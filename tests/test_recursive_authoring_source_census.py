# SPDX-License-Identifier: MPL-2.0
"""Exact original publication census, using disclosed software source metadata.

Real artifact batches and body I/O are exercised. The counter guard is explicitly
software-only: it creates no E3 product, reveal, qualification or native receipt.
"""
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_PYTHON_SOURCE_CODEC
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_bindings as operations
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e3_e4_experiment import SelectedE3E4OperationalSelection
from empirical_lawhood.api import recursive_authoring as owner
from empirical_lawhood.infrastructure import artifacts
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.experiment_preparation import ExperimentCensus, ExperimentPreparation
from tests.test_experiment_selected_input_bootstrap import Model
from tests.test_rubisco_gas_contrast import _real_plane


class DisclosedCurrentScope:
    parents = ()

    def __init__(self):
        self.calls = 0
        self.revoked = False
        self.member_calls = []

    def require_current(self):
        self.calls += 1
        if self.revoked:
            raise PermissionError('disclosed original read expired')

    def record_parents(self, record):
        return ()

    def require_member(self, manifest):
        # A permissive software double deliberately cannot authorize unknown
        # siblings: the shared exact source census must reject them itself.
        self.member_calls.append(manifest)
        self.require_current()


@pytest.fixture
def batch(tmp_path):
    plane = _real_plane(tmp_path / 'source-root')
    plane.validators = artifacts.ArtifactProfileValidatorRegistry(binary_codecs=(MATRIX_PYTHON_SOURCE_CODEC,))
    root = Path(plane.root.contract.canonical_path)
    codec = MATRIX_PYTHON_SOURCE_CODEC
    raw = b'values = (2, 3, 5)\n'
    canonical = Model('campaign.disclosed.source-census', (7, 11))
    budget = ResourceBudget(1, 1024**2, 0, 60, 1024**2, 1024**2)
    resources = SelectedE3E4OperationalSelection('resources.disclosed.source-census',
        tuple((phase, budget) for phase in sorted(operations.PHASES)))
    records = (('campaign', canonical), ('resources', resources))
    writes = [ArtifactWriteRequest('instrument.disclosed.source-census', 'original/instrument.py',
        codec.payload_schema, codec.profile, codec.media_type, 'publication.disclosed.source-census',
        'original', raw, VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND)]
    writes.extend(ArtifactWriteRequest(record.record_id, 'original/'+key+'.json', record.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, 'application/json', 'publication.disclosed.source-census',
        'original', record.canonical_bytes(), VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND)
        for key, record in records)
    pubs = plane.write_batch(tuple(writes))
    # Same generic author seam: the original canonical body is held in memory,
    # but its binding is a plain scratch copy without any original sidecar.
    scratch = root / 'scratch-canonical'
    scratch.mkdir()
    copied = scratch / 'unrelated-copy-name.json'
    copied.write_bytes(canonical.canonical_bytes())
    external = RecursiveExternalInput('instrument', writes[0].logical_artifact_id, codec.payload_schema,
        codec.media_type, len(raw), OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE,
        sha256(raw).hexdigest(), 'SOURCE')
    selected_record = RecursiveExternalInput('campaign', canonical.record_id, canonical.SCHEMA,
        'application/json', len(canonical.canonical_bytes()), OutcomeAccess.OUTCOME_BLIND,
        VisibilityCeiling.PROSPECTIVE, canonical.fingerprint(), 'SOURCE')
    return SimpleNamespace(plane=plane, root=root, codec=codec, original=pubs[0], publications=pubs,
        records=records, external=(selected_record, external),
        bindings={'campaign': copied, 'instrument': root/'original/instrument.py'}, scope=DisclosedCurrentScope())


def guard(case, *, records=None):
    return owner._published_source_manifest_preflight(selected_inputs=case.external, bindings=case.bindings,
        artifact_writer=case.plane, storage_codecs=(MATRIX_PYTHON_SOURCE_CODEC,),
        source_records=tuple(value for _, value in case.records) if records is None else records,
        original_input_access=case.scope, check_access=case.scope.require_current)


def observe_bodies(case, monkeypatch, callback):
    paths = {case.root / publication.materialization.relative_path for publication in case.publications}
    opening = artifacts.os.open
    def observed(path, *args, **kwargs):
        if isinstance(path, (str, Path)) and Path(path) in paths:
            callback(Path(path))
        return opening(path, *args, **kwargs)
    monkeypatch.setattr(artifacts.os, 'open', observed)
    return paths


def test_original_batch_authenticates_scratch_canonical_and_operational_siblings_before_hash(batch, monkeypatch):
    case = batch
    assert not case.bindings['campaign'].with_name(case.bindings['campaign'].name+'.manifest.json').exists()
    before = guard(case)
    observed = []
    last = case.scope.calls
    def opened(path):
        nonlocal last
        assert case.scope.calls > last
        last = case.scope.calls
        observed.append(path)
    paths = observe_bodies(case, monkeypatch, opened)
    manifest = case.plane.read_manifest(case.original.materialization.relative_path)
    case.plane.verify_manifest(manifest, before_member=before)
    assert set(observed) == paths
    assert not case.scope.member_calls


@pytest.mark.parametrize('damage', ('missing-resource', 'substituted-resource'))
def test_unheld_or_changed_operational_sibling_refuses_before_any_batch_body(batch, monkeypatch, damage):
    case = batch
    canonical, resource = (record for _, record in case.records)
    records = (canonical,) if damage == 'missing-resource' else (canonical,
        replace(resource, record_id=resource.record_id+'.foreign'))
    observe_bodies(case, monkeypatch, lambda path: pytest.fail('unowned original batch body opened'))
    with pytest.raises(PermissionError, match='outside its exact selected source census'):
        guard(case, records=records)
    assert not case.scope.member_calls


def test_foreign_same_parent_member_cannot_use_record_type_blind_label_or_owning_guard(batch, monkeypatch):
    case = batch
    before = guard(case)
    alien = Model('campaign.disclosed.alien-same-parents', (13, 17))
    published = case.plane.write(ArtifactWriteRequest(alien.record_id, 'alien/foreign.json', alien.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, 'application/json', 'publication.disclosed.alien', 'alien',
        alien.canonical_bytes(), VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND))
    manifest = case.plane.read_manifest(published.materialization.relative_path)
    # Exact same record class, intrinsic pair and empty parent census confer no
    # membership in the selected original batch or independently held records.
    with pytest.raises(PermissionError, match='outside its exact selected source census'):
        before(manifest)
    assert not case.scope.member_calls


def test_original_expiry_after_metadata_preflight_refuses_before_first_batch_hash(batch, monkeypatch):
    case = batch
    before = guard(case)
    manifest = case.plane.read_manifest(case.original.materialization.relative_path)
    case.scope.revoked = True
    observe_bodies(case, monkeypatch, lambda path: pytest.fail('expired original batch body opened'))
    with pytest.raises(PermissionError, match='disclosed original read expired'):
        case.plane.verify_manifest(manifest, before_member=before)


@pytest.mark.parametrize('damage', ('list', 'duplicate', 'reordered'))
def test_source_census_is_immutable_exact_keyed_metadata_separate_from_scientific_design(batch, damage):
    records = batch.records
    if damage == 'list':
        records = list(records)
    elif damage == 'duplicate':
        records = (records[0], records[0])
    else:
        records = tuple(reversed(records))
    pin = ObjectIdentity.from_record(batch.records[0][1].record_id, batch.records[0][1])
    census = ExperimentCensus((), (), (), (), 0)
    actual = ExperimentPreparation(pin, census, (), authoring_source_records=batch.records)
    assert actual.authoring_source_records == batch.records and actual.design_records == ()
    with pytest.raises(ValueError, match='source custody'):
        ExperimentPreparation(pin, census, (), authoring_source_records=records)


def test_composite_preparation_cannot_carry_component_source_custody(batch):
    record = batch.records[0][1]
    pin = ObjectIdentity.from_record(record.record_id, record)
    with pytest.raises(ValueError, match="Composite preparation"):
        ExperimentPreparation(pin, ExperimentCensus((), (), (), (), 0), (),
            programme=record, authoring_source_records=batch.records)
