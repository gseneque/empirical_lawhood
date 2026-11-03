# SPDX-License-Identifier: MPL-2.0
"""Current C role projections over real metadata; no scientific acquisition.

The C publisher authenticates actual disclosed inputs. The local guard spy is
only publication ordering instrumentation, never a real reveal authorization.
"""
from dataclasses import fields
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import matrix_programme_prepared_phases as owner
from empirical_lawhood.api.matrix_programme_projection import MatrixProgrammeProjectionContext
from empirical_lawhood.adapters.methods.matrix_researcher_programme.prepared_operations import MatrixProgrammePreparedOperations
from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import authenticate_publication
from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex
from tests.test_matrix_programme_allocations import census, _publisher_case, _forbid_acquisition  # noqa: F401
from tests.test_matrix_programme_scientific_design import scientific_design  # noqa: F401


@pytest.fixture
def actual_inputs(tmp_path, scientific_design, census, monkeypatch):  # noqa: F811
    from empirical_lawhood.api.matrix_programme_allocations import publish_matrix_programme_allocations
    writer, kwargs = _publisher_case(tmp_path, scientific_design, census)
    _forbid_acquisition(monkeypatch)
    published = publish_matrix_programme_allocations(**kwargs)
    root = Path(writer.root.contract.canonical_path)
    operations = SimpleNamespace(metadata_budget=kwargs['metadata_budget'])
    context = SimpleNamespace(writer=writer, inputs=published.resolved, commitments=published.resolved.commitments,
        namespace=published.resolved.commitments.namespace, plan=SimpleNamespace(specification=SimpleNamespace(
            input_commitments=published.commitment, operations=operations)),
        metadata_directory=lambda phase: root / 'prepared' / phase)
    context.publish_record = lambda *args, **options: MatrixProgrammeProjectionContext.publish_record(context, *args, **options)
    guards = []
    original = SimpleNamespace(require_current=lambda: guards.append('current'))
    return context, original, guards


def _selected_roots(context, role):
    phase = context.inputs.phase(role)
    selected = {value.public_source.root.root_id for value in phase.responses.protocols}
    return tuple(value for value in phase.reservation.allocation.roots if value.root.root_id in selected)


@pytest.mark.parametrize('role', ('e5.development', 'e5.confirmation'))
def test_current_role_view_keeps_every_assigned_root_and_the_immutable_shared_parent(actual_inputs, role, monkeypatch):
    context, original, guards = actual_inputs
    write_guards = []
    original_write = type(context.writer).write
    def observe_write(writer, request):
        if writer is context.writer:
            write_guards.append(len(guards))
        return original_write(writer, request)
    monkeypatch.setattr(type(context.writer), 'write', observe_write)
    before = context.commitments.canonical_bytes()
    parent = context.inputs.phase(role).reservation
    parent_bytes = parent.canonical_bytes()
    expected = _selected_roots(context, role)
    opposite = 'e5.confirmation' if role == 'e5.development' else 'e5.development'
    other = _selected_roots(context, opposite)
    assert parent == context.inputs.phase(opposite).reservation
    projected = owner._role_sources(context, 'projection.' + role, role, original=original)
    assert projected.reservation.allocation.roots == expected
    assert len(projected.descriptors) == len(expected) == dict(context.inputs.scientific_design.phase_group_counts)[role]
    assert projected.reservation.allocation != parent.allocation
    assert parent.canonical_bytes() == parent_bytes and context.commitments.canonical_bytes() == before
    assert {value.root.independent_group_id for value in projected.reservation.allocation.roots}.isdisjoint(
        value.root.independent_group_id for value in other)
    index = projected.source_index()
    public = {value.public_source.root.root_id: value.public_source for value in context.inputs.phase(role).responses.protocols}
    for reference in projected.descriptors:
        source = index.resolve(reference)
        source_public = public[reference.root_id]
        assert (source.root.root, source.coordinate, source.policy, source.provenance, source.source_id) == (
            next(value.root for value in expected if value.root.root_id == reference.root_id),
            source_public.coordinate, source_public.policy, context.inputs.producing_provenance, source_public.source.object_id)
        projected.audit.validate_source(source)
    assert write_guards and write_guards[0] > 0
    assert all(after > before for before, after in zip(write_guards, write_guards[1:]))
    assert len(guards) > write_guards[-1]
    authenticate_publication(context.writer, projected.audit_publication, projected.audit)


def test_conf_excludes_actual_dev_role_without_excluding_its_own_original_reserve(actual_inputs):
    context, original, _ = actual_inputs
    projected = owner._role_sources(context, 'projection.confirmation', 'e5.confirmation', original=original)
    dev, conf = _selected_roots(context, 'e5.development'), _selected_roots(context, 'e5.confirmation')
    excluded = set(projected.audit.census.effective_seed_exclusions)
    assert {stream.effective_seed for root in dev for stream in root.streams} <= excluded
    assert {stream.effective_seed for _, panels in context.inputs.phase('e5.development').responses.panels
        for panel in panels for stream in panel.streams} <= excluded
    assert not ({stream.effective_seed for root in conf for stream in root.streams} & excluded)
    assert {root.root.independent_group_id for root in dev} <= set(projected.audit.census.exposed_independent_groups)
    assert not ({root.root.independent_group_id for root in conf} & set(projected.audit.census.exposed_independent_groups))
    assert set(context.inputs.exposure_census.effective_seed_exclusions) <= excluded
    assert projected.audit.census.mandatory_floor == context.inputs.exposure_census.mandatory_floor
    # The actual C selection remains the custody parent of this conservative
    # declaration projection; a reserved row is never reported as a contact.
    facts = (context.metadata_directory('projection.confirmation') / 'current-exclusions/facts.json').read_text()
    assert 'NOT_A_CONTACT_OR_MEASURED_EXPOSURE_CENSUS' in facts
    assert 'NOT_MEASURED_PHYSICAL_EVIDENCE' in facts
    assert context.plan.specification.input_commitments.record.object_fingerprint in facts


def test_original_two_regime_e6_reservation_and_streams_are_never_rewritten(actual_inputs):
    context, _, _ = actual_inputs
    root = Path(context.writer.root.contract.canonical_path)
    before = tuple(sorted(path.relative_to(root).as_posix() for path in root.rglob('*') if path.is_file()))
    selected = owner._transfer_sources(context)
    near, shifted = context.inputs.phase('e6.nearby'), context.inputs.phase('e6.shifted')
    assert selected.reservation == near.reservation == shifted.reservation
    assert selected.specification == near.native_specification == shifted.native_specification
    assert selected.audit == context.inputs.exposure_audit
    assert selected.audit_publication == context.commitments.exposure_audit.publication
    expected = tuple(sorted((*_selected_roots(context, 'e6.nearby'), *_selected_roots(context, 'e6.shifted')),
        key=lambda value: value.root.root_id))
    index = ScheduledSourceIndex.from_shared(reservation=selected.reservation, specification=selected.specification,
        provenances=selected.provenances)
    assert tuple(index.resolve(value).root for value in selected.descriptors) == expected
    assert tuple(sorted(path.relative_to(root).as_posix() for path in root.rglob('*') if path.is_file())) == before


def test_prepared_operations_have_no_hidden_science_nominee_or_source_qualification_defaults():
    assert tuple(field.name for field in fields(MatrixProgrammePreparedOperations)) == (
        'record_id', 'campaign', 'cutoff', 'operator_id', 'maximum_source_bytes',
        'opportunity_resources', 'protected_resources')
    assert owner.PHASES == ('e5.initialize-development', 'e5.development', 'e5.initialize-confirmation',
        'e5.source', 'e5.confirmation', 'e6.initialize', 'e6.source', 'e6')


def test_guard_refusal_precedes_first_current_exclusion_publication(actual_inputs):
    context, original, _ = actual_inputs
    root = Path(context.writer.root.contract.canonical_path)
    before = tuple(sorted(path.relative_to(root).as_posix() for path in root.rglob('*') if path.is_file()))
    def refused():
        raise PermissionError('actual-current-access-refused')
    original.require_current = refused
    with pytest.raises(PermissionError, match='actual-current-access-refused'):
        owner._role_sources(context, 'projection.refused', 'e5.development', original=original)
    assert tuple(sorted(path.relative_to(root).as_posix() for path in root.rglob('*') if path.is_file())) == before


def test_projection_refuses_unsupported_phase_before_reading_originals():
    with pytest.raises(ValueError, match='unsupported current prepared'):
        owner.project_prepared_phase(SimpleNamespace(), 'e5.unknown')
