# SPDX-License-Identifier: MPL-2.0
"""Selected pure dependencies never replace complete final or effect custody."""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from threading import Barrier
import sys

import pytest

from empirical_lawhood.infrastructure import artifacts
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.operational_configuration import ArtifactVerificationMode
from tests.runtime_platform.test_artifact_verification_scope import _publication
from tests.test_reduced_artifact_verification import _mask_changed_stat


def _additional(plane, count):
    rows = plane.write_compact_batch(tuple(ArtifactWriteRequest(
        'exposed.prior.' + str(index), 'prior/' + str(index) + '.json', ObjectIdentity.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, 'application/json', 'exposed.prior', 'prior',
        ObjectIdentity('exposed.prior.' + str(index), ObjectIdentity.SCHEMA, '1.0.0', 'b' * 64).canonical_bytes(),
        VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE) for index in range(count)))
    return tuple(plane.read_manifest(row.materialization.relative_path) for row in rows)


@contextmanager
def _paths():
    paths = Counter()
    code = artifacts.ExternalArtifactPlane._require_verification_snapshot_paths.__code__
    def observe(frame, event, arg):
        if event == 'call' and frame.f_code is code:
            paths.update(frame.f_locals['snapshots'].keys())
    prior = sys.getprofile()
    sys.setprofile(observe)
    try:
        yield paths
    finally:
        sys.setprofile(prior)


@pytest.mark.parametrize('history', (4, 32))
def test_checkpoint_work_names_only_complete_actual_dependencies(tmp_path, history, record_property):
    plane, selected = _publication(tmp_path, 3)
    prior = _additional(plane, history)
    with plane.read_context() as reading:
        reading.verify_manifests(prior)
        with reading.verification_dependencies() as checkpoint:
            reading.verify_manifest(selected[0])
            with _paths() as paths:
                for _ in range(3):
                    checkpoint.require_current()
            assert len(paths) == 7 and set(paths.values()) == {3}
            assert not any('/prior/' in str(path) for path in paths)
            record_property('history_members', history)
            record_property('checkpoint_paths', len(paths))
            # A cached complete census must contribute the same actual siblings.
            with reading.verification_dependencies() as cached:
                reading.verify_manifest(selected[0])
                cached.require_current()
                assert cached.paths == checkpoint.paths
        with pytest.raises(artifacts.ArtifactIdentityConflict, match='escaped'):
            checkpoint.require_current()


@pytest.mark.parametrize('damage', ('sibling', 'sidecar', 'marker', 'revoked', 'ancestor'))
def test_dependency_checkpoint_refuses_before_consumer(tmp_path, damage):
    plane, selected = _publication(tmp_path, 3)
    allowed, consumed = True, False
    def access(manifest):
        if not allowed:
            raise PermissionError('selected input access revoked')
    with pytest.raises((ValueError, RuntimeError, PermissionError)):
        with plane.read_context(before_member=access) as reading:
            with reading.verification_dependencies() as checkpoint:
                reading.verify_manifest(selected[0])
                if damage == 'revoked':
                    allowed = False
                elif damage == 'ancestor':
                    parent = plane.root.resolve(selected[0].materialization.relative_path, for_write=False).parent
                    original = parent.with_name('original')
                    parent.rename(original)
                    parent.symlink_to(original, target_is_directory=True)
                else:
                    relative = (selected[-1].materialization.relative_path if damage == 'sibling'
                        else selected[0].materialization.relative_path + '.manifest.json' if damage == 'sidecar'
                        else selected[0].publication.commit_marker_relative_path)
                    path = plane.root.resolve(relative, for_write=False)
                    raw = path.read_bytes()
                    path.write_bytes(b'[' + raw[1:])
                checkpoint.require_current()
                consumed = True
    assert not consumed


@pytest.mark.parametrize('failure', (False, True))
def test_outer_union_still_refuses_unselected_late_bytes_on_success_or_failure(tmp_path, monkeypatch, failure):
    plane, selected = _publication(tmp_path, 2)
    prior = _additional(plane, 2)
    plane.artifact_verification = ArtifactVerificationMode.REDUCED
    with pytest.raises(artifacts.ArtifactIdentityConflict, match='changed'):
        with plane.read_context() as reading:
            reading.verify_manifest(prior[0])
            with reading.verification_dependencies():
                reading.verify_manifest(selected[0])
            path = plane.root.resolve(prior[0].materialization.relative_path, for_write=False)
            _mask_changed_stat(monkeypatch, path)
            raw = path.read_bytes()
            path.write_bytes(b'[' + raw[1:])
            if failure:
                raise LookupError('consumer refused')


def test_force_full_checkpoint_refuses_same_stat_changed_bytes(tmp_path, monkeypatch):
    plane, selected = _publication(tmp_path, 2)
    plane.artifact_verification = ArtifactVerificationMode.REDUCED
    with pytest.raises(artifacts.ArtifactIdentityConflict, match='changed'):
        with plane.read_context() as reading, reading.verification_dependencies() as checkpoint:
            reading.verify_manifest(selected[0])
            path = plane.root.resolve(selected[-1].materialization.relative_path, for_write=False)
            _mask_changed_stat(monkeypatch, path)
            raw = path.read_bytes()
            path.write_bytes(b'[' + raw[1:])
            checkpoint.require_current(force_full=True)


def test_changed_read_policy_refuses_an_existing_dependency_checkpoint(tmp_path):
    plane, selected = _publication(tmp_path, 2)
    with pytest.raises(artifacts.ArtifactIdentityConflict, match='policy'):
        with plane.read_context() as reading, reading.verification_dependencies() as checkpoint:
            reading.verify_manifest(selected[0])
            reading.custody_limits = artifacts.ArtifactCustodyLimits(publication_members=4)
            checkpoint.require_current()


def test_metadata_selection_does_not_open_or_claim_bodies(tmp_path):
    plane, selected = _publication(tmp_path, 2)
    path = plane.root.resolve(selected[0].materialization.relative_path, for_write=False)
    path.unlink()  # Metadata access has no body-access authority.
    with plane.read_context() as reading:
        with reading.verification_dependencies() as checkpoint:
            reading.read_manifest(selected[0].materialization.relative_path)
            checkpoint.require_current()
            assert path not in checkpoint.paths
            assert checkpoint.paths


def test_concurrent_and_nested_consumers_keep_precise_dependency_sets(tmp_path):
    plane, first = _publication(tmp_path, 2)
    second = _additional(plane, 3)
    ready = Barrier(2)
    with plane.read_context() as reading:
        reading.verify_manifests((first[0], second[0]))
        def consume(manifest):
            with reading.verification_dependencies() as checkpoint:
                ready.wait(timeout=10)
                with reading.verification_dependencies() as nested:
                    reading.verify_manifest(manifest)
                    nested.require_current()
                ready.wait(timeout=10)
                checkpoint.require_current()
                return frozenset(checkpoint.paths)
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = tuple(pool.map(consume, (first[0], second[0])))
        assert tuple(map(len, results)) == (5, 7)
        assert not results[0] & results[1]


@pytest.mark.parametrize('policy', ('inspector', 'scope'))
def test_custom_policy_keeps_full_history_checkpoint(tmp_path, policy):
    plane, selected = _publication(tmp_path, 2)
    prior = _additional(plane, 2)
    if policy == 'inspector':
        class Inspector(artifacts.LocalFilesystemInspector):
            pass
        plane.root.inspector = Inspector()
    scope = plane.verification_scope if policy == 'scope' else plane.read_context
    consumed = False
    with pytest.raises(artifacts.ArtifactIdentityConflict):
        with scope() as reading:
            reading.verify_manifest(prior[0])
            with reading.verification_dependencies() as checkpoint:
                reading.verify_manifest(selected[0])
                plane.root.resolve(prior[0].materialization.relative_path, for_write=False).write_bytes(b'{}\n')
                checkpoint.require_current()
                consumed = True
    assert not consumed
