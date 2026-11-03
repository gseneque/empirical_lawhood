# SPDX-License-Identifier: MPL-2.0
"""Operational input locators preserve custody without a run-wide flat directory."""

import hashlib
import stat
from dataclasses import dataclass, replace
from pathlib import Path
from types import SimpleNamespace
from typing import ClassVar

import pytest

from empirical_lawhood.api.execution import (
    CampaignCapabilityError,
    CampaignExecutionService,
    CampaignValidationError,
    _provider_input_location,
)
from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict, ArtifactPlaneError
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.runtime.artifacts import (
    ArtifactLineageParent,
    ArtifactProfile,
    ArtifactStreamWriteRequest,
)
from empirical_lawhood.runtime.plans import ExternalInputSpec
from empirical_lawhood.runtime.providers import ExternalInputPayload
from tests.runtime_platform.test_execution_scheduler import _plane

RUN = 'run.input-layout'
LOGICAL = 'input.layout.example'
PAYLOAD = b'exposed layout control'
SCHEMA = 'empirical-lawhood/testing/input-layout'


def _payload(logical=LOGICAL, payload=PAYLOAD, *, parents=()):
    return ExternalInputPayload.from_bytes(
        logical_artifact_id=logical, payload_schema=SCHEMA,
        profile=ArtifactProfile.TEXT_PARAMETERS, media_type='text/plain', payload=payload,
        visibility_ceiling=VisibilityCeiling.PROSPECTIVE, outcome_access=OutcomeAccess.OUTCOME_BLIND,
        parent_visibility_ceilings=tuple(parent.visibility_ceiling for parent in parents),
        lineage_parents=parents,
    )


def _persist(plane, value=None):
    return CampaignExecutionService._persist_provider_inputs(
        SimpleNamespace(artifact_plane=plane), RUN, (value or _payload(),), minimum_free_bytes=0,
    )[0]


def _legacy(plane, value=None):
    value = value or _payload()
    try:
        return plane.write_stream(ArtifactStreamWriteRequest(
            logical_artifact_id=value.logical_artifact_id,
            relative_path=f'runs/{RUN}/inputs/{value.logical_artifact_id}.bin',
            publication_scope_id=f'campaign-inputs.{RUN}',
            publication_scope_relative_root=f'runs/{RUN}/inputs',
            payload_schema=value.payload_schema, profile=value.profile, media_type=value.media_type,
            chunks=value.chunks(), maximum_bytes=value.maximum_bytes,
            maximum_chunk_bytes=value.maximum_chunk_bytes, expected_size_bytes=value.size_bytes,
            expected_physical_sha256=value.source_sha256, visibility_ceiling=value.visibility_ceiling,
            parent_visibility_ceilings=value.parent_visibility_ceilings, outcome_access=value.outcome_access,
            lineage_parents=value.lineage_parents,
        ))
    finally:
        value.close()


def _primary(path):
    return {p.relative_to(path): (p.read_bytes(), p.stat().st_mtime_ns)
            for p in path.rglob('*') if p.is_file() and not p.name.endswith('.lock')}


def test_fresh_layout_and_replay_use_bounded_paths_and_exact_materialization(tmp_path):
    plane = _plane(tmp_path)
    token = hashlib.sha256(LOGICAL.encode()).hexdigest()
    expected = f'runs/{RUN}/inputs/{token[:2]}/{token}.bin'
    assert _provider_input_location(plane, RUN, LOGICAL) == (
        expected, f'campaign-inputs.{RUN}.{token[:2]}', f'runs/{RUN}/inputs/{token[:2]}')
    first = _persist(plane)
    assert first.materialization.relative_path == expected
    assert first.logical.logical_artifact_id == LOGICAL
    assert (tmp_path / expected).read_bytes() == PAYLOAD
    before = _primary(tmp_path)
    assert _persist(plane) == first
    assert _primary(tmp_path) == before
    assert not (tmp_path / f'runs/{RUN}/inputs/{LOGICAL}.bin').exists()
    assert all(str(path).startswith(f'runs/{RUN}/inputs/{token[:2]}/') for path in before)


def test_complete_legacy_pair_replays_original_canonical_bytes_and_materialization(tmp_path):
    plane = _plane(tmp_path)
    original = _legacy(plane)
    before = _primary(tmp_path)
    loaded = _persist(plane)
    assert loaded.logical == original.logical and loaded.materialization == original.materialization
    assert _primary(tmp_path) == before
    assert _provider_input_location(plane, RUN, LOGICAL) == (
        f'runs/{RUN}/inputs/{LOGICAL}.bin', f'campaign-inputs.{RUN}', f'runs/{RUN}/inputs')


@pytest.mark.parametrize('layout', ('legacy', 'sharded'))
@pytest.mark.parametrize('member', ('matching-payload', 'conflicting-payload', 'invalid-sidecar'))
def test_partial_existing_pair_uses_established_writer_recovery_without_relocation(tmp_path, layout, member):
    plane = _plane(tmp_path)
    relative = (f'runs/{RUN}/inputs/{LOGICAL}.bin' if layout == 'legacy'
                else _provider_input_location(plane, RUN, LOGICAL)[0])
    path = tmp_path / (relative + '.manifest.json' if member == 'invalid-sidecar' else relative)
    path.parent.mkdir(parents=True)
    path.write_bytes(PAYLOAD if member == 'matching-payload' else b'conflicting original bytes')
    original = path.read_bytes(), path.stat().st_mtime_ns
    if member == 'matching-payload':
        result = _persist(plane)
        assert result.materialization.relative_path == relative
        assert (tmp_path / (relative + '.manifest.json')).is_file()
    else:
        with pytest.raises(ArtifactPlaneError):
            _persist(plane)
    assert (path.read_bytes(), path.stat().st_mtime_ns) == original
    if member != 'matching-payload':
        other = tmp_path / (relative if member == 'invalid-sidecar' else relative + '.manifest.json')
        assert not other.exists()
    if layout == 'legacy':
        token = hashlib.sha256(LOGICAL.encode()).hexdigest()
        assert not (tmp_path / f'runs/{RUN}/inputs/{token[:2]}/{token}.bin').exists()


@pytest.mark.parametrize('layout', ('legacy', 'sharded'))
def test_existing_conflicting_payload_refuses_and_preserves_original_pair(tmp_path, layout):
    plane = _plane(tmp_path)
    (_legacy if layout == 'legacy' else _persist)(plane)
    before = _primary(tmp_path)
    with pytest.raises(ArtifactIdentityConflict):
        _persist(plane, _payload(payload=b'changed exposed control'))
    assert _primary(tmp_path) == before


def test_both_layouts_are_ambiguous_even_when_scientific_bytes_match(tmp_path):
    plane = _plane(tmp_path)
    _persist(plane)
    _legacy(plane)
    before = _primary(tmp_path)
    with pytest.raises(ArtifactIdentityConflict, match='ambiguous legacy and sharded'):
        _persist(plane)
    assert _primary(tmp_path) == before


@pytest.mark.parametrize('member', ('legacy-payload', 'legacy-sidecar', 'sharded-payload', 'sharded-sidecar', 'parent'))
def test_nonregular_entries_do_not_fall_through_to_fresh_storage(tmp_path, member):
    plane = _plane(tmp_path)
    fresh = _provider_input_location(plane, RUN, LOGICAL)[0]
    relative = {'legacy-payload': f'runs/{RUN}/inputs/{LOGICAL}.bin',
                'legacy-sidecar': f'runs/{RUN}/inputs/{LOGICAL}.bin.manifest.json',
                'sharded-payload': fresh, 'sharded-sidecar': fresh + '.manifest.json',
                'parent': f'runs/{RUN}/inputs'}[member]
    path = tmp_path / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    if member == 'parent':
        path.write_bytes(b'not a directory')
    else:
        path.mkdir()
    with pytest.raises((ArtifactPlaneError, NotADirectoryError)):
        _persist(plane)


@pytest.mark.parametrize('entry', ('payload', 'sidecar', 'sharded-payload', 'sharded-sidecar', 'parent'))
def test_dangling_symlink_metadata_is_refused_even_when_exists_is_false(tmp_path, monkeypatch, entry):
    # VFAT cannot create symlinks. Inject only lstat metadata for an absent entry;
    # the real guarded root and all remaining custody code remain in use.
    plane = _plane(tmp_path)
    directory = tmp_path / f'runs/{RUN}/inputs'
    directory.mkdir(parents=True)
    fresh = tmp_path / _provider_input_location(plane, RUN, LOGICAL)[0]
    selected = {'payload': directory / f'{LOGICAL}.bin',
                'sidecar': directory / f'{LOGICAL}.bin.manifest.json',
                'sharded-payload': fresh, 'sharded-sidecar': Path(str(fresh) + '.manifest.json'),
                'parent': directory / hashlib.sha256(LOGICAL.encode()).hexdigest()[:2]}[entry]
    if entry.startswith('sharded-'):
        selected.parent.mkdir()
    original = Path.lstat

    def observed(path):
        if path == selected:
            return SimpleNamespace(st_mode=stat.S_IFLNK | 0o777)
        return original(path)

    monkeypatch.setattr(Path, 'lstat', observed)
    assert not selected.exists()
    with pytest.raises(ArtifactPlaneError, match='symlink'):
        _persist(plane)


def test_long_logical_identity_uses_bounded_leaf_without_changing_identity(tmp_path):
    logical = 'input.' + 'a' * 300
    result = _persist(_plane(tmp_path), _payload(logical))
    assert result.logical.logical_artifact_id == logical
    assert len(Path(result.materialization.relative_path).name) == 68


@pytest.mark.parametrize('changed', ('logical', 'materialization-logical', 'path'))
def test_writer_returned_identity_and_locator_are_joined_before_acceptance(tmp_path, changed):
    class WrongWriter:
        root = _plane(tmp_path).root

        def write_stream(self, request):
            return SimpleNamespace(
                logical=SimpleNamespace(logical_artifact_id='other' if changed == 'logical' else LOGICAL),
                materialization=SimpleNamespace(
                    logical_artifact_id='other' if changed == 'materialization-logical' else LOGICAL,
                    relative_path='other.bin' if changed == 'path' else request.relative_path,
                    size_bytes=len(PAYLOAD), physical_sha256=hashlib.sha256(PAYLOAD).hexdigest()))

    with pytest.raises(CampaignCapabilityError, match='identity changed'):
        _persist(WrongWriter())


@dataclass(frozen=True, slots=True)
class _Context(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/testing/input-layout-context'
    plan_id: str = RUN
    snapshot_id: str = 'snapshot.layout'
    wave_input_id: str = 'wave.layout'
    selections: tuple = ()
    proposals: tuple = ()
    visibility_ceiling: VisibilityCeiling = VisibilityCeiling.PROSPECTIVE
    outcome_access: OutcomeAccess = OutcomeAccess.OUTCOME_BLIND
    plan: object = None


@pytest.mark.parametrize('layout', ('legacy', 'sharded'))
def test_exploration_reader_reuses_recorded_materialization_and_retains_tamper_refusal(tmp_path, layout):
    plane = _plane(tmp_path)
    plan = _Context()
    package = SimpleNamespace(exploration_plan=plan, snapshot=replace(plan, snapshot_id='other.snapshot'),
                              wave_input=replace(plan, plan=plan))
    specification = ExternalInputSpec(
        input_id='input.layout', logical_artifact_id=LOGICAL,
        expected_content_sha256=hashlib.sha256(PAYLOAD).hexdigest(),
        expected_payload_schema=SCHEMA, expected_media_type='text/plain',
        expected_size_bytes=len(PAYLOAD), expected_visibility_ceiling=VisibilityCeiling.PROSPECTIVE,
        expected_outcome_access=OutcomeAccess.OUTCOME_BLIND, identity_scope_sha256=None)
    parent = ArtifactLineageParent(identity=ObjectIdentity.from_record(specification.input_id, specification),
                                  visibility_ceiling=VisibilityCeiling.PROSPECTIVE,
                                  outcome_access=OutcomeAccess.OUTCOME_BLIND)
    original = (_legacy if layout == 'legacy' else _persist)(plane, _payload(parents=(parent,)))
    execution_plan = SimpleNamespace(tasks=(SimpleNamespace(external_inputs=(specification,)),))
    service = SimpleNamespace(artifact_plane=plane)
    reader = CampaignExecutionService._verified_exploration_external_inputs
    before = _primary(tmp_path)
    assert reader(service, package, execution_plan) == {LOGICAL: original.materialization.materialization_id}
    assert _primary(tmp_path) == before
    (tmp_path / original.materialization.relative_path).write_bytes(b'tampered control')
    with pytest.raises(CampaignValidationError, match='custody is invalid'):
        reader(service, package, execution_plan)


def test_3478_long_logical_ids_have_bounded_per_bucket_physical_layout():
    # Names only: no acquisition, scientific payloads or native execution.
    buckets = {}
    for index in range(3478):
        logical = f'input.long-exposed-layout-control.{index:04d}.' + 'a' * 160
        token = hashlib.sha256(logical.encode()).hexdigest()
        buckets.setdefault(token[:2], []).append(token)
    assert sum(map(len, buckets.values())) == 3478
    assert len(buckets) == 256 and max(map(len, buckets.values())) <= 32
    # Conservative LFN + short-entry allocation for payload, sidecar, pair lock
    # and their one-live-publication staged files, plus directory entries.
    slots_per_input = sum(1 + (length + 12) // 13 for length in (68, 82, 44, 120, 134))
    assert max(map(len, buckets.values())) * slots_per_input + 16 < 65536
