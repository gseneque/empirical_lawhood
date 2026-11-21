# SPDX-License-Identifier: MPL-2.0
"""Real parallel checks stay live through retained parent guards and close."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
from contextvars import copy_context

import pytest

from empirical_lawhood.api import recursive_contributions as contributions
from empirical_lawhood.api import recursive_execution as execution
from empirical_lawhood.api.integration_artifact_profiles import INTEGRATION_ARTIFACT_PROFILE_VALIDATORS
from empirical_lawhood.api.recursive_inquiry_read import inquiry_authoring_read, inquiry_projection_read
from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.records.serialization import canonical_json_bytes
from empirical_lawhood.storage.artifacts import ArtifactIdentityConflict, ExternalArtifactPlane
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.storage.parallel_verification import canonical_validation_scope
from tests.runtime_platform.test_artifact_verification_scope import _publication
from tests.test_recursive_projection_lifetime import _stock_plane
from tests.test_recursive_report_projection import wave as wave  # noqa: F401


def _parallel_publication(tmp_path):
    original, _ = _publication(tmp_path, 1)
    plane = ExternalArtifactPlane(original.root, INTEGRATION_ARTIFACT_PROFILE_VALIDATORS,
        maximum_parallel_verifications=2)
    schema = 'empirical-lawhood/testing/retained-parallel-read'
    raw = canonical_json_bytes(dict(schema=schema, value='x' * 600_000, version='1.0.0'))
    requests = tuple(ArtifactWriteRequest('exposed.parallel.' + str(index), f'parallel/{index}.json',
        schema, ArtifactProfile.CANONICAL_JSON, 'application/json', 'exposed.parallel', 'parallel', raw,
        VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE) for index in range(2))
    results = plane.write_batch(requests)
    return plane, tuple(plane.read_manifest(result.materialization.relative_path) for result in results)


def _retain_parent(plane, manifests, final):
    """Keep a real independent parent reader in the owning ancestry lifetime."""
    ancestry = contributions._current_contribution_reads()
    assert ancestry is not None
    parent = ancestry.lifetime.enter_context(plane.read_context())
    parent.verify_manifests(manifests)
    pool = parent._read_verification.canonical_pool
    assert pool.validated_files == len(manifests)
    assert pool.worker_pids
    # A late parent consumer still needs the same finite CPU capacity. Its
    # artifact scope performs the complete original final mutation guard next.
    ancestry.lifetime.callback(lambda: final.append(pool.project_ordered(abs, (-3,))))
    return parent, pool


@pytest.mark.parametrize('scope', (inquiry_authoring_read, inquiry_projection_read))
@pytest.mark.parametrize('consumer_failure', (False, True))
def test_retained_parent_finishes_before_main_read_pool_closes(tmp_path, scope, consumer_failure):
    plane, manifests = _parallel_publication(tmp_path)
    final = []
    expected = pytest.raises(LookupError, match='consumer refusal') if consumer_failure else nullcontext()
    with expected:
        with scope(plane):
            parent, pool = _retain_parent(plane, manifests, final)
            if consumer_failure:
                raise LookupError('consumer refusal')
    assert final == [(3,)]
    with pytest.raises(ArtifactIdentityConflict, match='ended'):
        parent.require_active_verification_scope()
    with pytest.raises(RuntimeError, match='ended'):
        pool.project_ordered(abs, (-4,))
    # The next complete byte check must not inherit a closed executor.
    with plane.read_context() as fresh:
        fresh.verify_manifests(manifests)
        assert fresh._read_verification.canonical_pool is not pool
        assert fresh._read_verification.canonical_pool.validated_files == len(manifests)


@pytest.mark.parametrize('consumer_failure', (False, True))
def test_retained_parent_still_refuses_final_byte_mutation(tmp_path, consumer_failure):
    plane, manifests = _parallel_publication(tmp_path)
    final = []
    with pytest.raises(ArtifactIdentityConflict):
        with inquiry_authoring_read(plane):
            parent, _ = _retain_parent(plane, manifests, final)
            path = plane.root.resolve(manifests[0].materialization.relative_path, for_write=False)
            raw = path.read_bytes()
            path.write_bytes(raw.replace(b'xxx', b'yxx', 1))
            if consumer_failure:
                raise LookupError('consumer refusal')
    assert final == [(3,)]
    with pytest.raises(ArtifactIdentityConflict, match='ended'):
        parent.require_active_verification_scope()


def test_recursive_wave_keeps_retained_parent_guards_inside_its_pool(wave, tmp_path):
    parent_plane, manifests = _parallel_publication(tmp_path)
    plane = _stock_plane(wave.plane)
    final, pools = [], []
    def consume(**_roots):
        _, pool = _retain_parent(parent_plane, manifests, final)
        pools.append(pool)
    result, _ = execution._read_recursive_wave_with_retained_roots(directory=wave.directory,
        artifact_writer=plane, include_products=True, _validate_authored=consume)
    assert result[0]['status'] == 'SUCCEEDED' and final == [(3,)] and len(pools) == 1
    with canonical_validation_scope(2) as fresh:
        assert fresh is not pools[0]
        assert fresh.project_ordered(abs, (-4,)) == (4,)


def test_copied_context_after_close_gets_a_fresh_cpu_pool():
    with canonical_validation_scope(2) as original:
        copied = copy_context()
        assert original.project_ordered(abs, (-1,)) == (1,)
    def fresh():
        with canonical_validation_scope(2) as current:
            assert current is not original
            assert current.project_ordered(abs, (-2,)) == (2,)
    copied.run(fresh)
    with pytest.raises(RuntimeError, match='ended'):
        with canonical_validation_scope(2, shared_pool=original):
            pytest.fail('explicit closed pool was accepted')


def test_copied_thread_gets_fresh_capacity_unless_explicitly_borrowed():
    with canonical_validation_scope(2) as original:
        def independent():
            with canonical_validation_scope(1) as current:
                assert current is not original
                assert current.project_ordered(abs, (-1,)) == (1,)
            with canonical_validation_scope(2, shared_pool=original) as borrowed:
                with canonical_validation_scope(1) as nested:
                    assert nested is borrowed is original
                    assert nested.project_ordered(abs, (-2,)) == (2,)
        with ThreadPoolExecutor(max_workers=1) as threads:
            threads.submit(copy_context().run, independent).result()
        assert original.project_ordered(abs, (-3,)) == (3,)
