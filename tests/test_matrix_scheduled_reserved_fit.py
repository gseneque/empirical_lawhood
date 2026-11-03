# SPDX-License-Identifier: MPL-2.0
"""Original publication joins precede exposed fitting; no scientific authority."""

from dataclasses import replace
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response import response_error_prediction as prediction
from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole as Role
from empirical_lawhood.adapters.methods.matrix_scheduled_history import records
from empirical_lawhood.kernel.evidence import VisibilityCeiling
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.runtime.execution import VerifiedArtifactInput, WorkerInputBinding, WorkerInputKind, WorkerInputPort
from tests.test_matrix_factor_confirmation_eligibility import publish
from tests.test_matrix_factor_confirmation_eligibility import provenance as provenance
from tests.test_matrix_factor_confirmation_eligibility import stock as stock
from tests.test_matrix_factor_response import Reader
from tests.test_matrix_response_error_prediction import inputs, spec as spec
from tests.test_matrix_scheduled_history import scheduled as scheduled


def artifact(publication):
    return ArtifactIdentity(publication.logical.logical_artifact_id, 'exposed-original-publication',
        publication.logical.payload_schema, publication.logical.content_sha256,
        publication.logical.media_type, publication.materialization.size_bytes)


@pytest.fixture
def case(scheduled, spec):
    plane, sources = scheduled
    reservation = sources[0].reservation
    roles = publish(plane, spec.roles, 'exposed.fit.roles')
    reserved = publish(plane, reservation, 'exposed.fit.reservation')
    spec = replace(spec, future_regime_reservation=records.identity(reservation),
        future_reservation_publication=artifact(reserved), roles_publication=artifact(roles))
    return SimpleNamespace(plane=plane, reservation=reservation, spec=spec, roles=roles, reserved=reserved)


def ports(case):
    result = {}
    for name, publication in (('allocation_port', case.reservation.publication),
            ('reservation_port', case.reserved), ('roles_port', case.roles)):
        raw = case.plane.root.resolve(publication.materialization.relative_path, for_write=False).read_bytes()
        result[name] = WorkerInputPort(WorkerInputBinding.from_verified(
            VerifiedArtifactInput(publication.logical, publication.materialization), kind=WorkerInputKind.EXTERNAL), Reader(raw))
    return result


def test_original_full_reserve_and_roles_are_read_before_training_and_fit(case):
    selected = ports(case)
    features, labels = inputs(case.spec, role='TRAIN')
    expected = prediction.fit_error_model(case.spec, features, labels, method='ALL_ORIGIN', record_id='exposed.fit.model')
    loaded = []

    def load():
        assert all(port.bytes_read == port.size_bytes for port in selected.values())
        loaded.append(True)
        return features, labels

    actual = prediction.fit_scheduled_error_model(case.spec, case.reservation, **selected,
        load_training_inputs=load, method='ALL_ORIGIN', record_id='exposed.fit.model')
    assert actual == expected and loaded == [True]
    assert actual.reservation == records.identity(case.reservation)
    assert len(actual.training_root_ids) == 128


@pytest.mark.parametrize('damage', ('foreign-reservation', 'allocation-materialization',
    'allocation-bytes', 'allocation-decimal-spelling', 'reservation-decimal-spelling',
    'role-bytes', 'missing-role-port', 'exposed-role-port'))
def test_missing_or_substituted_originals_refuse_before_training_or_fitting(case, monkeypatch, damage):
    selected, spec = ports(case), case.spec
    if damage == 'foreign-reservation':
        foreign = replace(case.reservation, reservation_id='reservation.foreign.fit')
        spec = replace(spec, future_regime_reservation=records.identity(foreign),
            future_reservation_publication=replace(spec.future_reservation_publication, sha256=foreign.fingerprint()))
    elif damage == 'allocation-materialization':
        port = selected['allocation_port']
        selected['allocation_port'] = replace(port, binding=replace(port.binding, materialization_id='materialization.foreign.fit'))
    elif damage == 'allocation-bytes':
        raw = replace(case.reservation.allocation, allocation_id='allocation.foreign.fit').canonical_bytes()
        selected['allocation_port'] = replace(selected['allocation_port'], _reader=Reader(raw))
    elif damage in ('allocation-decimal-spelling', 'reservation-decimal-spelling'):
        name = 'allocation_port' if damage.startswith('allocation') else 'reservation_port'
        publication = case.reservation.publication if name == 'allocation_port' else case.reserved
        raw = case.plane.root.resolve(publication.materialization.relative_path, for_write=False).read_bytes()
        altered = raw.replace(b'"0.001"', b'".0010"', 1)
        assert altered != raw and len(altered) == len(raw)
        selected[name] = replace(selected[name], _reader=Reader(altered))
    elif damage == 'role-bytes':
        raw = replace(spec.roles, record_id='roles.foreign.fit').canonical_bytes()
        selected['roles_port'] = replace(selected['roles_port'], _reader=Reader(raw))
    elif damage == 'missing-role-port':
        selected['roles_port'] = None
    else:
        port = selected['roles_port']
        selected['roles_port'] = replace(port, binding=replace(port.binding, visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY))

    def forbidden(*args, **kwargs):
        raise AssertionError('refused publication reached training or fitting')

    monkeypatch.setattr(prediction, 'fit_error_model', forbidden)
    with pytest.raises(ValueError):
        prediction.fit_scheduled_error_model(spec, case.reservation, **selected,
            load_training_inputs=forbidden, method='ALL_ORIGIN', record_id='exposed.refused.model')


@pytest.mark.parametrize('damage', ('missing-transfer', 'exposed-group'))
def test_complete_reserve_refuses_absent_e6_or_exposed_training_group(case, monkeypatch, damage):
    allocation = case.reservation.allocation
    if damage == 'missing-transfer':
        roots = tuple(row for row in allocation.roots if row.root.role is not Role.WITHHELD_TRANSFER)
        coordinates = tuple(c for c in allocation.coordinates if records.coordinate_identity(c) in {row.coordinate for row in roots})
        scopes = tuple(scope for scope in allocation.matched_scopes if scope.role is not Role.WITHHELD_TRANSFER)
    else:
        exposed_group = next(group for _, group, _, role, _ in case.spec.roles.rows if role == 'TRAIN')
        old_group = next(row.root.independent_group_id for row in allocation.roots if row.root.role is Role.DEVELOPMENT)
        roots = tuple(replace(row, root=replace(row.root, independent_group_id=exposed_group))
            if row.root.independent_group_id == old_group else row for row in allocation.roots)
        coordinates = allocation.coordinates
        scopes = tuple(replace(scope, independent_group_ids=(exposed_group,))
            if old_group in scope.independent_group_ids else scope for scope in allocation.matched_scopes)
    allocation = replace(allocation, roots=roots, coordinates=coordinates, matched_scopes=scopes)
    reservation = replace(case.reservation, allocation=allocation,
        publication=publish(case.plane, allocation, 'exposed.changed.fit.allocation'))
    reserved = publish(case.plane, reservation, 'exposed.changed.fit.reservation')
    spec = replace(case.spec, future_regime_reservation=records.identity(reservation),
        future_reservation_publication=artifact(reserved))
    case = SimpleNamespace(plane=case.plane, reservation=reservation, spec=spec, roles=case.roles, reserved=reserved)

    def forbidden(*args, **kwargs):
        raise AssertionError('invalid whole reserve reached training or fitting')

    monkeypatch.setattr(prediction, 'fit_error_model', forbidden)
    with pytest.raises(ValueError, match='reserved whole E6|exposed training'):
        prediction.fit_scheduled_error_model(spec, reservation, **ports(case),
            load_training_inputs=forbidden, method='ALL_ORIGIN', record_id='exposed.refused.model')
