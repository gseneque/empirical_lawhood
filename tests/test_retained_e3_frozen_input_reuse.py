# SPDX-License-Identifier: MPL-2.0
"""Real NPZ publication and replay; exposed software arrays grant no authority."""
from dataclasses import replace
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.api.execution import CampaignExecutionService, _provider_input_location
from empirical_lawhood.api.retained_e3_control_repair import reuse_frozen_provider_input
from empirical_lawhood.infrastructure import artifact_validation
from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict
from empirical_lawhood.infrastructure.matrix_array_io import encode_matrix_arrays
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactStreamWriteRequest
from empirical_lawhood.runtime.plans import ExternalInputSpec
from empirical_lawhood.runtime.providers import ExternalInputPayload
from tests.test_matrix_array_worker_delivery import _plane


def _snapshot(root):
    return {p.relative_to(root): (p.read_bytes(), p.stat().st_mtime_ns)
        for p in root.rglob('*') if p.is_file() and not p.name.endswith('.lock')}


@pytest.mark.parametrize('damage', ('none', 'source', 'labels', 'stored', 'revoked', 'mid-read-revocation'))
def test_frozen_npz_reuses_actual_producing_stamp_and_refuses_changed_custody(tmp_path, monkeypatch, damage):
    writer = _plane(tmp_path / 'selected')
    raw, _ = encode_matrix_arrays({'exposed': np.arange(6, dtype='<f8').reshape(2, 3)})
    run = 'run.disclosed.retained-input'
    def payload():
        return ExternalInputPayload.from_bytes(logical_artifact_id='input.disclosed.retained-array',
            payload_schema=MATRIX_ARRAY_SCHEMA, profile=ArtifactProfile.MATRIX_ARRAY_NPZ,
            media_type='application/x-npz', payload=raw,
            visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY,
            outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE, parent_visibility_ceilings=(),
            lineage_parents=())
    service = SimpleNamespace(artifact_plane=writer)
    original, = CampaignExecutionService._persist_provider_inputs(service, run, (payload(),), minimum_free_bytes=0)
    descriptor = artifact_validation._distribution_implementation_descriptor
    monkeypatch.setattr(artifact_validation, '_distribution_implementation_descriptor',
        lambda name: {**descriptor(name), 'record_sha256': 'a' * 64})
    artifact_validation._profile_implementation_sha256.cache_clear()
    writer.validators = type(writer.validators)(binary_codecs=writer.validators.binary_codecs)
    assert writer.validators.generic_validation(profile=original.logical.profile,
        payload_schema=MATRIX_ARRAY_SCHEMA) != original.logical.generic_validation
    with pytest.raises(ArtifactIdentityConflict, match='sidecar differs'):
        CampaignExecutionService._persist_provider_inputs(service, run, (payload(),), minimum_free_bytes=0)
    value = payload()
    relative, scope, home = _provider_input_location(writer, run, value.logical_artifact_id)
    request = ArtifactStreamWriteRequest(logical_artifact_id=value.logical_artifact_id,
        relative_path=relative, payload_schema=value.payload_schema, profile=value.profile,
        media_type=value.media_type, publication_scope_id=scope, publication_scope_relative_root=home,
        chunks=value.chunks(), maximum_bytes=value.maximum_bytes, maximum_chunk_bytes=value.maximum_chunk_bytes,
        visibility_ceiling=value.visibility_ceiling, parent_visibility_ceilings=value.parent_visibility_ceilings,
        outcome_access=value.outcome_access, expected_size_bytes=value.size_bytes,
        expected_physical_sha256=value.source_sha256, logical_content_sha256=value.source_sha256)
    spec = ExternalInputSpec('external.disclosed.retained-array', value.logical_artifact_id,
        value.source_sha256, value.payload_schema, value.media_type, value.size_bytes,
        value.visibility_ceiling, value.outcome_access, None)
    if damage == 'source':
        request = replace(request, chunks=(bytes([raw[0] ^ 1]) + raw[1:],))
    elif damage == 'labels':
        spec = replace(spec, expected_outcome_access=OutcomeAccess.OUTCOME_BLIND)
    elif damage == 'stored':
        writer.root.resolve(relative, for_write=True).write_bytes(bytes([raw[0] ^ 1]) + raw[1:])
    calls = 0
    def access():
        nonlocal calls
        calls += 1
        if damage == 'revoked' or damage == 'mid-read-revocation' and calls >= 4:
            raise PermissionError('disclosed current access revoked')
    before = _snapshot(tmp_path)
    try:
        if damage == 'none':
            reused = reuse_frozen_provider_input(writer=writer, run_id=run, spec=spec,
                request=request, require_access=access)
            assert reused.logical == original.logical and reused.materialization == original.materialization
            assert calls >= 4
        else:
            with pytest.raises((PermissionError, ArtifactIdentityConflict)):
                reuse_frozen_provider_input(writer=writer, run_id=run, spec=spec,
                    request=request, require_access=access)
        assert _snapshot(tmp_path) == before
    finally:
        value.close()
        artifact_validation._profile_implementation_sha256.cache_clear()


def test_retained_control_scope_is_the_access_owner_without_a_generic_adapter(tmp_path):
    """Actual supplier/custody types with a disclosed non-scientific grant stub."""
    from empirical_lawhood.api.configured_e3_retained_runtime import (
        RetainedE3ExecutionScope, retained_e3_input_access_guard,
    )
    from empirical_lawhood.api.domain_composition.matrix_configured_protected_response.runtime import ProtectedE3RuntimeInputSupplier
    from empirical_lawhood.runtime.executable_bindings import ExecutablePlatformPort
    from empirical_lawhood.runtime.recursive_provider import RecursiveOperationInputPort
    writer = _plane(tmp_path / 'owner')
    run = 'run.disclosed.retained-access'
    calls = 0
    revoked = False
    def require_access():
        nonlocal calls
        calls += 1
        if revoked:
            raise PermissionError('disclosed retained-original grant revoked')
    scope = object.__new__(RetainedE3ExecutionScope)
    scope.writer = writer
    scope.selection = SimpleNamespace(retention=SimpleNamespace(continued_run_id=run))
    scope._active = SimpleNamespace(require_access=require_access)
    supplier = ProtectedE3RuntimeInputSupplier(SimpleNamespace(), writer=writer, root=None,
        fit_config=None, qualifications=(), selection=scope.selection, retained_e3_scope=scope)
    assert supplier.custody._original_input_accesses == ()
    ports = tuple(ExecutablePlatformPort('port.disclosed.' + str(i), RecursiveOperationInputPort(supplier))
        for i in range(2))
    service = SimpleNamespace(artifact_plane=writer, executable_platform_ports=ports)
    guard = retained_e3_input_access_guard(service, run)
    guard()
    assert calls == 2  # Duplicate installed ports still select one actual owner.
    revoked = True
    with pytest.raises(PermissionError, match='grant revoked'):
        guard()
    revoked = False
    with pytest.raises(PermissionError, match='substitutes'):
        retained_e3_input_access_guard(service, run + '.foreign')
    scope._active = None
    with pytest.raises(PermissionError, match='active original custody'):
        guard()
    service.executable_platform_ports = ()
    with pytest.raises(PermissionError, match='one actual retained control owner'):
        retained_e3_input_access_guard(service, run)
