# SPDX-License-Identifier: MPL-2.0
"""Concurrent real byte guards, with serialized current-access callbacks."""
from contextvars import ContextVar
from threading import Barrier, Lock, get_ident
import time

import pytest

from empirical_lawhood.infrastructure import artifacts
from empirical_lawhood.runtime.artifacts import ArtifactSemanticValidationRegistry
from tests.runtime_platform.test_execution_scheduler import _plane


def _snapshots(tmp_path):
    original = _plane(tmp_path)
    plane = artifacts.ExternalArtifactPlane(original.root, original.validators,
        maximum_parallel_verifications=4)
    snapshots = {}
    for index in range(4):
        path = plane.root.resolve(f'checks/member-{index}', for_write=True)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(bytes([index]) * 512 * 1024)
        plane._track_verification_snapshot(path, snapshots, maximum_bytes=512 * 1024)
    return plane, snapshots


def test_parallel_hashing_overlaps_with_bounded_workers_and_live_serialized_access(tmp_path, monkeypatch):
    plane, snapshots = _snapshots(tmp_path)
    original = artifacts.bounded_file_sha256
    ready, lock = Barrier(4), Lock()
    workers, counts = set(), {'active': 0, 'peak': 0}
    selection = ContextVar('disclosed-live-access', default=None)
    token = selection.set('current')

    def access(_manifest):
        assert selection.get() == 'current'
        with lock:
            counts['active'] += 1
            counts['peak'] = max(counts['peak'], counts['active'])
        time.sleep(0.005)
        # Reentrant access verification must not create a nested waiting pool.
        plane._require_verification_snapshot_paths({}, reason='nested')
        with lock:
            counts['active'] -= 1

    def digest(path, **kwargs):
        with lock:
            workers.add(get_ident())
        ready.wait(timeout=5)
        return original(path, **kwargs)

    monkeypatch.setattr(artifacts, 'bounded_file_sha256', digest)
    try:
        plane._require_verification_snapshot_paths(snapshots, reason='changed',
            member_preflights={path: [(None, access)] for path in snapshots})
    finally:
        selection.reset(token)
    assert len(workers) == 4 and counts['peak'] == 1


@pytest.mark.parametrize('damage', ('bytes', 'revoked-access'))
def test_parallel_guard_refuses_changed_bytes_and_current_access(tmp_path, monkeypatch, damage):
    plane, snapshots = _snapshots(tmp_path)
    original = artifacts.bounded_file_sha256
    selected = next(iter(snapshots))
    reads = []

    def digest(path, **kwargs):
        reads.append(path)
        if damage == 'bytes' and path == selected:
            # Change bytes after the outer stat check, keeping the same length.
            path.write_bytes(b'X' * 512 * 1024)
        return original(path, **kwargs)

    def access(_manifest):
        raise PermissionError('disclosed grant revoked')

    monkeypatch.setattr(artifacts, 'bounded_file_sha256', digest)
    if damage == 'bytes':
        with pytest.raises(artifacts.ArtifactIdentityConflict, match='changed'):
            plane._require_verification_snapshot_paths(snapshots, reason='changed')
        assert selected in reads
    else:
        with pytest.raises(PermissionError, match='grant revoked'):
            plane._require_verification_snapshot_paths(snapshots, reason='changed',
                member_preflights={path: [(None, access)] for path in snapshots})
        assert not reads


def test_scoped_and_semantic_views_preserve_selected_bookkeeping_bound(tmp_path):
    plane, _ = _snapshots(tmp_path)
    registry = ArtifactSemanticValidationRegistry('disclosed.registry', ())
    with plane.verification_scope() as view:
        derived = view.with_semantic_validation_registry(registry)
        assert derived.maximum_parallel_verifications == view.maximum_parallel_verifications == 4
        assert derived._verification_preflight_lock is view._verification_preflight_lock


def test_parallel_snapshot_scans_only_its_selected_callback_rows(tmp_path):
    """Count registry visits, not elapsed time, over actual bounded file reads."""
    plane, snapshots = _snapshots(tmp_path)
    visits = []
    calls = []

    class ObservedRows(dict):
        def values(self):
            for path, rows in super().items():
                visits.append(path)
                yield rows

        def get(self, path, default=None):
            visits.append(path)
            return super().get(path, default)

    def access(manifest):
        calls.append(manifest)

    rows = ObservedRows({path: [(path, access)] for path in snapshots})
    plane._require_verification_snapshot_paths(snapshots, reason='changed', member_preflights=rows)
    assert set(calls) == set(snapshots) and len(calls) == len(snapshots)
    # One outer scope, one selected worker scope, one pre-body lookup per path.
    assert len(visits) <= 3 * len(snapshots)
