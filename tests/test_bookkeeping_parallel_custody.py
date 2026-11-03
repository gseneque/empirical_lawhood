# SPDX-License-Identifier: MPL-2.0
"""Real multicore format checks; exposed software fixtures, no native work."""
import io
import os
import subprocess
import sys
from types import SimpleNamespace
from threading import Event, Lock

import pytest

from empirical_lawhood.infrastructure import artifact_validation as formats
from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict, ExternalArtifactPlane
from empirical_lawhood.infrastructure.parallel_verification import CanonicalValidationPool
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactSemanticValidationRegistry, ArtifactWriteRequest
from tests.runtime_platform.test_artifact_verification_scope import _publication


def test_json_format_worker_does_not_import_array_and_model_stacks():
    subprocess.run([sys.executable, '-c', '''
import io
import sys
from types import SimpleNamespace
from empirical_lawhood.infrastructure import artifact_validation as formats
raw = b'{"schema":"empirical-lawhood/testing/light-format","value":1}\\n'
request = SimpleNamespace(payload_schema='empirical-lawhood/testing/light-format', semantic_validation=None)
assert formats._inspect_canonical_json_file(io.BytesIO(raw), request, size=len(raw)).schema == request.payload_schema
assert not {'numpy', 'h5py', 'onnx', 'pyarrow', 'safetensors'}.intersection(sys.modules)
import numpy as np
array = np.arange(6, dtype=np.float64).reshape(2, 3)
assert np.array_equal(formats.validate_numpy_no_pickle(formats.numpy_no_pickle_bytes(array)), array)
'''], check=True, timeout=30)


@pytest.mark.parametrize('batch', (False, True))
def test_verification_refills_a_free_slot_before_the_oldest_read_finishes(batch):
    from empirical_lawhood.infrastructure.parallel_verification import ParallelValidationBatch, verify_in_parallel

    first_started, third_started = Event(), Event()
    lock = Lock()
    active, peak, finished = 0, 0, []
    def check(value):
        nonlocal active, peak
        with lock:
            active += 1
            peak = max(peak, active)
        try:
            if value == 0:
                first_started.set()
                assert third_started.wait(5), 'completed second read did not release its slot'
            elif value == 1:
                assert first_started.wait(5)
            else:
                third_started.set()
            finished.append(value)
        finally:
            with lock:
                active -= 1
    if batch:
        with ParallelValidationBatch(check, workers=2) as pending:
            for value in range(3):
                pending.submit(value)
    else:
        verify_in_parallel(check, range(3), workers=2)
    assert sorted(finished) == [0, 1, 2]
    assert active == 0 and peak == 2


@pytest.mark.parametrize('mode', ('reduced', 'strict'))
def test_actual_publication_format_checks_use_processes_and_controller_access(tmp_path, mode):
    original, _ = _publication(tmp_path, 1)
    plane = ExternalArtifactPlane(original.root, maximum_parallel_verifications=2, artifact_verification=mode)
    schema = 'empirical-lawhood/testing/parallel-bookkeeping'
    raw = canonical_json_bytes({'schema': schema, 'value': tuple(range(75000)), 'version': '1.0.0'})
    requests = tuple(ArtifactWriteRequest('parallel.member.' + str(index), f'parallel/{index}.json',
        schema, ArtifactProfile.CANONICAL_JSON, 'application/json', 'parallel.batch', 'parallel', raw,
        VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE) for index in range(4))
    results = plane.write_batch(requests)
    manifests = tuple(plane.read_manifest(row.materialization.relative_path) for row in results)
    access_pids = []
    def access(_manifest):
        access_pids.append(os.getpid())
    with plane.read_context() as reading:
        reading.verify_manifests(manifests, before_member=access)
        pool = reading._read_verification.canonical_pool
        assert pool is not None
        assert 1 < len(pool.worker_pids) <= 2
        assert os.getpid() not in pool.worker_pids
        assert pool.validated_files == len(manifests)
        for manifest in manifests:
            header = reading.verified_canonical_header(manifest)
            assert header == formats.CanonicalJsonHeader(('schema', 'value', 'version'), schema, '1.0.0')
        # Reduced scopes share format facts within this invocation. Strict
        # scopes repeat them. Both retain separate current access and final
        # byte censuses, and share the finite CPU pool without early shutdown.
        for _ in range(2):
            with reading.verification_scope() as nested, nested.read_context() as child:
                assert child._read_verification is not reading._read_verification
                assert child._read_verification.canonical_pool is pool
                child.verify_manifests(manifests, before_member=access)
            assert child._read_verification.canonical_pool is None
        assert pool.validated_files == (3 if mode == 'strict' else 1) * len(manifests)
        assert 1 < len(pool.worker_pids) <= 2
    assert access_pids and set(access_pids) == {os.getpid()}
    assert reading._read_verification.canonical_pool is None
    with (tmp_path / 'unneeded').open('wb+') as handle, pytest.raises(RuntimeError, match='ended'):
        pool.validate(handle, None, None)
    with pytest.raises(ArtifactIdentityConflict, match='ended'):
        reading.require_verification_context()


def test_changed_semantic_registry_reuses_format_only_and_refreshes_access(tmp_path):
    plane, manifests = _publication(tmp_path, 4)
    code = formats.ArtifactProfileValidatorRegistry.validate_file.__code__
    calls = []
    def observe(frame, event, _arg):
        if event == 'call' and frame.f_code is code:
            calls.append(frame.f_locals['path'])
    previous = sys.getprofile()
    live = True
    def access(_manifest):
        if not live:
            raise PermissionError('revoked exposed access')
    sys.setprofile(observe)
    try:
        with plane.read_context() as reading:
            reading.verify_manifests(manifests, before_member=access)
            other = reading.with_semantic_validation_registry(ArtifactSemanticValidationRegistry('other.registry', ()))
            other.verify_manifests(manifests, before_member=access)
            assert len(calls) == len(manifests)
            live = False
            with pytest.raises(PermissionError, match='revoked'):
                other.verify_manifests(manifests, before_member=access)
            live = True
    finally:
        sys.setprofile(previous)


def test_process_decoder_keeps_strict_newline_and_bounded_token_contract(tmp_path):
    schema = 'empirical-lawhood/testing/parallel-bookkeeping'
    raw = canonical_json_bytes({'schema': schema, 'value': 'x', 'version': '1.0.0'})
    path = tmp_path / 'invalid.json'
    path.write_bytes(raw[:-1])
    pool = CanonicalValidationPool(2)
    try:
        with path.open('rb') as handle, pytest.raises(ArtifactIdentityConflict, match='newline'):
            pool.validate(handle, SimpleNamespace(payload_schema=schema, semantic_validation=None), None)
    finally:
        pool.close()


def test_fast_tokens_keep_complete_header_shape_and_noncanonical_refusals():
    schema = 'empirical-lawhood/testing/parallel-bookkeeping'
    request = SimpleNamespace(payload_schema=schema, semantic_validation=None)
    raw = canonical_json_bytes({'schema': schema, 'value': None, 'version': '2.0.0'})
    assert formats._CanonicalJsonFileInspector(io.BytesIO(raw), request).validate() == (
        formats.CanonicalJsonHeader(('schema', 'value', 'version'), schema, '2.0.0'))
    for invalid in (raw.replace(b'"value":', b'"value" :'), raw.replace(b'null', b'"\\/"'), raw + b'\n'):
        with pytest.raises(ArtifactIdentityConflict):
            formats._CanonicalJsonFileInspector(io.BytesIO(invalid), request).validate()


@pytest.mark.parametrize('file_read', (False, True))
def test_memory_and_file_codecs_keep_identical_canonical_byte_refusals(file_read):
    schema = 'empirical-lawhood/testing/parallel-bookkeeping'
    raw = canonical_json_bytes({'schema': schema, 'value': {'decimal': '0.00100'}, 'version': '2.0.0'})

    def validate(payload):
        request = ArtifactWriteRequest('canonical.control', 'canonical/control.json', schema,
            ArtifactProfile.CANONICAL_JSON, 'application/json', 'canonical', 'canonical', payload,
            VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE)
        if file_read:
            return formats._inspect_canonical_json_file(io.BytesIO(payload), request, size=len(payload))
        return formats.ArtifactProfileValidatorRegistry().validate(request)

    validate(raw)
    for invalid in (raw[:-1], raw + b'\n', raw.replace(b'"value":', b'"value" :'),
            raw.replace(b'"value":', b'"value":null,"value":'),
            raw.replace(b'"0.00100"', b'"\\u0030.00100"')):
        with pytest.raises(ArtifactIdentityConflict):
            validate(invalid)


@pytest.mark.parametrize('workers', (1, 8))
def test_normal_controller_state_selects_shared_read_and_publication_batches(tmp_path, workers):
    from empirical_lawhood.api.integration_artifact_profiles import INTEGRATION_ARTIFACT_PROFILE_VALIDATORS
    from empirical_lawhood.api.recursive_execution import _read_only_custody_policy
    from empirical_lawhood.infrastructure.publication_metadata import supports_closed_publication_access
    from empirical_lawhood.infrastructure.recursive_custody import _can_batch_compact_output_custody
    from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore

    original, _ = _publication(tmp_path, 1)
    plane = ExternalArtifactPlane(original.root, INTEGRATION_ARTIFACT_PROFILE_VALIDATORS,
        maximum_parallel_verifications=workers)
    assert _read_only_custody_policy(plane) is not None
    assert supports_closed_publication_access(plane)
    with plane.read_context() as reading:
        policy = _read_only_custody_policy(reading)
        assert policy is not None
        assert supports_closed_publication_access(reading)
        assert _can_batch_compact_output_custody(plane=reading, store=ExternalTaskReceiptStore(reading),
            decode_products=False, output_count=4, policy=policy)
        reading.custom_read_policy = object()
        assert _read_only_custody_policy(reading) is None
        assert not supports_closed_publication_access(reading)
        assert not _can_batch_compact_output_custody(plane=reading, store=ExternalTaskReceiptStore(reading),
            decode_products=False, output_count=4, policy=policy)
        del reading.custom_read_policy


def test_factory_lookup_uses_the_closed_index_without_scanning_the_population():
    from empirical_lawhood.adapters.composition.generated_executable_bindings import EXECUTABLE_CAPABILITY_PROVIDER_FACTORY_REGISTRY
    from empirical_lawhood.runtime.executable_bindings import ExecutableCapabilityProviderFactoryRegistry

    original = EXECUTABLE_CAPABILITY_PROVIDER_FACTORY_REGISTRY
    visits = []
    class ObservedFactory:
        def __init__(self, value):
            self.value = value
        @property
        def binding(self):
            visits.append(1)
            return self.value.binding
        def __getattr__(self, name):
            return getattr(self.value, name)
    factories = tuple(ObservedFactory(original.factory(key)) for key in original.binding_ids)
    registry = ExecutableCapabilityProviderFactoryRegistry(aggregate=original.aggregate, factories=factories)
    visits.clear()
    assert tuple(registry.factory(key) for key in registry.binding_ids) == factories
    assert visits == []
    with pytest.raises(KeyError):
        registry.factory('absent.exposed.factory')
    assert registry.fingerprint == original.fingerprint
