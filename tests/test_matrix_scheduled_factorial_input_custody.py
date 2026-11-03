# SPDX-License-Identifier: MPL-2.0
"""The factorial input reader reuses exact legacy or sharded custody metadata."""

from dataclasses import replace
from hashlib import sha256

import pytest

from empirical_lawhood.api.matrix_scheduled_factorial_runtime import _original_external
from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict, ArtifactPlaneError
from empirical_lawhood.infrastructure.provider_input_custody import provider_input_location
from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactLineageParent, ArtifactStreamWriteRequest
from empirical_lawhood.runtime.plans import ExternalInputSpec
from tests.runtime_platform.test_execution_scheduler import _plane
from tests.test_execution_input_layout import LOGICAL, PAYLOAD, RUN, SCHEMA, _legacy, _payload, _persist


def _spec(**changes):
    return replace(ExternalInputSpec(
        input_id='input.factorial-custody', logical_artifact_id=LOGICAL,
        expected_content_sha256=sha256(PAYLOAD).hexdigest(), expected_payload_schema=SCHEMA,
        expected_media_type='text/plain', expected_size_bytes=len(PAYLOAD),
        expected_visibility_ceiling=VisibilityCeiling.PROSPECTIVE,
        expected_outcome_access=OutcomeAccess.OUTCOME_BLIND, identity_scope_sha256=None,
    ), **changes)


def _snapshot(directory):
    return {path.relative_to(directory).as_posix(): (path.read_bytes(), path.stat().st_mtime_ns)
            for path in directory.rglob('*') if path.is_file()}


def _publish(plane, layout, value=None):
    return (_legacy if layout == 'legacy' else _persist)(plane, value)


def _sidecar(directory, result):
    return directory / (result.materialization.relative_path + '.manifest.json')


@pytest.mark.parametrize('layout', ('legacy', 'sharded'))
def test_original_external_joins_exact_custody_and_preserves_all_original_bytes(tmp_path, layout):
    plane = _plane(tmp_path)
    written = _publish(plane, layout)
    before = _snapshot(tmp_path)
    result = _original_external(plane, RUN, _spec())
    assert (result.logical, result.materialization) == (written.logical, written.materialization)
    assert result.canonical_bytes() == _sidecar(tmp_path, written).read_bytes()
    assert _snapshot(tmp_path) == before


def test_absent_input_refuses_without_creating_any_files(tmp_path):
    plane = _plane(tmp_path)
    before = _snapshot(tmp_path)
    with pytest.raises((FileNotFoundError, ArtifactPlaneError)):
        _original_external(plane, RUN, _spec())
    assert _snapshot(tmp_path) == before


@pytest.mark.parametrize('layout', ('legacy', 'sharded'))
def test_payload_only_partial_refuses_missing_metadata_without_relocation(tmp_path, layout):
    plane = _plane(tmp_path)
    written = _publish(plane, layout)
    _sidecar(tmp_path, written).unlink()
    before = _snapshot(tmp_path)
    with pytest.raises((FileNotFoundError, ArtifactPlaneError)):
        _original_external(plane, RUN, _spec())
    assert _snapshot(tmp_path) == before


@pytest.mark.parametrize('layout', ('legacy', 'sharded'))
def test_sidecar_only_keeps_metadata_boundary_and_full_custody_still_refuses(tmp_path, layout):
    # This reader intentionally authenticates publication metadata without
    # payload access. Its existing downstream full-custody gate owns the bytes.
    plane = _plane(tmp_path)
    written = _publish(plane, layout)
    (tmp_path / written.materialization.relative_path).unlink()
    before = _snapshot(tmp_path)
    result = _original_external(plane, RUN, _spec())
    assert (result.logical, result.materialization) == (written.logical, written.materialization)
    assert _snapshot(tmp_path) == before
    with pytest.raises((FileNotFoundError, ArtifactPlaneError)):
        plane.verify_manifest(result)
    assert _snapshot(tmp_path) == before


def test_both_complete_layouts_refuse_even_when_payloads_match(tmp_path):
    plane = _plane(tmp_path)
    _publish(plane, 'legacy')
    # The normal persistence owner reuses legacy custody. Publish the second
    # exact pair independently to exercise an actually ambiguous retained root.
    token = sha256(LOGICAL.encode()).hexdigest()
    value = _payload()
    try:
        plane.write_stream(ArtifactStreamWriteRequest(
            logical_artifact_id=value.logical_artifact_id,
            relative_path=f'runs/{RUN}/inputs/{token[:2]}/{token}.bin',
            publication_scope_id=f'campaign-inputs.{RUN}.{token[:2]}',
            publication_scope_relative_root=f'runs/{RUN}/inputs/{token[:2]}',
            payload_schema=value.payload_schema, profile=value.profile, media_type=value.media_type,
            chunks=value.chunks(), maximum_bytes=value.maximum_bytes,
            maximum_chunk_bytes=value.maximum_chunk_bytes, expected_size_bytes=value.size_bytes,
            expected_physical_sha256=value.source_sha256, visibility_ceiling=value.visibility_ceiling,
            parent_visibility_ceilings=value.parent_visibility_ceilings, outcome_access=value.outcome_access,
            lineage_parents=value.lineage_parents,
        ))
    finally:
        value.close()
    before = _snapshot(tmp_path)
    with pytest.raises(ArtifactIdentityConflict, match='ambiguous legacy and sharded'):
        _original_external(plane, RUN, _spec())
    assert _snapshot(tmp_path) == before


@pytest.mark.parametrize('layout', ('legacy', 'sharded'))
def test_foreign_logical_identity_at_selected_location_refuses(tmp_path, layout):
    plane = _plane(tmp_path)
    relative = (f'runs/{RUN}/inputs/{LOGICAL}.bin' if layout == 'legacy'
                else provider_input_location(plane, RUN, LOGICAL)[0])
    value = _payload(logical='input.factorial-foreign')
    try:
        plane.write_stream(ArtifactStreamWriteRequest(
            logical_artifact_id=value.logical_artifact_id, relative_path=relative,
            publication_scope_id=f'factorial-input-foreign.{layout}',
            publication_scope_relative_root=relative.rsplit('/', 1)[0],
            payload_schema=value.payload_schema, profile=value.profile, media_type=value.media_type,
            chunks=value.chunks(), maximum_bytes=value.maximum_bytes,
            maximum_chunk_bytes=value.maximum_chunk_bytes, expected_size_bytes=value.size_bytes,
            expected_physical_sha256=value.source_sha256, visibility_ceiling=value.visibility_ceiling,
            parent_visibility_ceilings=value.parent_visibility_ceilings, outcome_access=value.outcome_access,
            lineage_parents=value.lineage_parents,
        ))
    finally:
        value.close()
    before = _snapshot(tmp_path)
    with pytest.raises(PermissionError, match='exact frozen external input metadata'):
        _original_external(plane, RUN, _spec())
    assert _snapshot(tmp_path) == before


@pytest.mark.parametrize(('field', 'value'), (
    ('expected_content_sha256', 'f' * 64),
    ('expected_payload_schema', 'empirical-lawhood/testing/foreign-factorial-input'),
    ('expected_media_type', 'application/octet-stream'),
    ('expected_size_bytes', len(PAYLOAD) + 1),
    ('expected_visibility_ceiling', VisibilityCeiling.DEVELOPMENT_ONLY),
    ('expected_outcome_access', OutcomeAccess.DEVELOPMENT_VISIBLE),
))
def test_frozen_metadata_predicates_still_refuse(tmp_path, field, value):
    plane = _plane(tmp_path)
    _publish(plane, 'sharded')
    before = _snapshot(tmp_path)
    with pytest.raises(PermissionError, match='exact frozen external input metadata'):
        _original_external(plane, RUN, _spec(**{field: value}))
    assert _snapshot(tmp_path) == before


@pytest.mark.parametrize('layout', ('legacy', 'sharded'))
@pytest.mark.parametrize('matching', (True, False))
def test_original_lineage_scope_is_joined_without_rewriting(tmp_path, layout, matching):
    plane = _plane(tmp_path)
    identity = ObjectIdentity('scope.factorial-input', 'empirical-lawhood/testing/factorial-input-scope',
                              '1.0.0', sha256(b'exposed original scope').hexdigest())
    parent = ArtifactLineageParent(identity, VisibilityCeiling.PROSPECTIVE, OutcomeAccess.OUTCOME_BLIND)
    written = _publish(plane, layout, _payload(parents=(parent,)))
    before = _snapshot(tmp_path)
    spec = _spec(identity_scope_sha256=identity.object_fingerprint if matching else 'e' * 64)
    if matching:
        assert _original_external(plane, RUN, spec).logical == written.logical
    else:
        with pytest.raises(PermissionError, match='exact frozen external input metadata'):
            _original_external(plane, RUN, spec)
    assert _snapshot(tmp_path) == before


@pytest.mark.parametrize('layout', ('legacy', 'sharded'))
@pytest.mark.parametrize('mutation', ('invalid-sidecar', 'missing-publication', 'invalid-marker', 'missing-marker'))
def test_existing_manifest_and_marker_refusals_preserve_retained_bytes(tmp_path, layout, mutation):
    plane = _plane(tmp_path)
    written = _publish(plane, layout)
    path = _sidecar(tmp_path, written)
    manifest = decode_artifact_manifest(path.read_bytes())
    if mutation == 'invalid-sidecar':
        path.write_bytes(b'not a canonical manifest')
    elif mutation == 'missing-publication':
        path.write_bytes(replace(manifest, publication=None).canonical_bytes())
    elif mutation == 'invalid-marker':
        (tmp_path / manifest.publication.commit_marker_relative_path).write_bytes(b'wrong marker')
    else:
        (tmp_path / manifest.publication.commit_marker_relative_path).unlink()
    before = _snapshot(tmp_path)
    with pytest.raises((ValueError, PermissionError, FileNotFoundError, ArtifactPlaneError)):
        _original_external(plane, RUN, _spec())
    assert _snapshot(tmp_path) == before
