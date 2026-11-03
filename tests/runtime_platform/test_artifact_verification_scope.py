# SPDX-License-Identifier: MPL-2.0
"""Actual stable custody reads, independent of scientific grants or native work."""

import json

import pytest

from empirical_lawhood.infrastructure.artifacts import (
    ExternalArtifactPlane, GuardedExternalRoot,
)
from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import (
    ArtifactProfile, ArtifactWriteRequest, ExternalRootContract,
)


def _publication(tmp_path, count=4):
    root = tmp_path / 'custody'
    root.mkdir()
    mount = next(parent for parent in root.parents if parent.is_mount())
    plane = ExternalArtifactPlane(GuardedExternalRoot(ExternalRootContract(
        'exposed.scope-custody', 'Software custody verification, no scientific qualification',
        str(root), str(mount), 'empirical-lawhood/testing/read-scope', 1)))
    requests = tuple(ArtifactWriteRequest(
        'exposed.member.' + str(index), 'outputs/member-' + str(index) + '.json', ObjectIdentity.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, 'application/json', 'exposed.complete-batch', 'outputs',
        ObjectIdentity('exposed.subject.' + str(index), ObjectIdentity.SCHEMA, '1.0.0', 'a' * 64).canonical_bytes(),
        VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE,
    ) for index in range(count))
    results = plane.write_batch(requests)
    manifests = tuple(decode_artifact_manifest(plane.root.resolve(
        row.manifest_materialization.relative_path, for_write=False).read_bytes()) for row in results)
    return plane, manifests


@pytest.mark.parametrize('members', (4, 32))
def test_multiple_consumers_verify_each_complete_publication_once(tmp_path, monkeypatch, members):
    plane, manifests = _publication(tmp_path, members)
    calls = []
    original = ExternalArtifactPlane._verify_manifest_snapshot

    def observed(self, manifest, **kwargs):
        calls.append(manifest.logical.logical_artifact_id)
        return original(self, manifest, **kwargs)

    monkeypatch.setattr(ExternalArtifactPlane, '_verify_manifest_snapshot', observed)
    for _ in range(3):
        plane.verify_manifests(manifests)
    baseline = len(calls)
    calls.clear()
    with plane.verification_scope() as scoped:
        for _ in range(3):
            scoped.verify_manifests(manifests)
    assert baseline == 3 * members
    assert len(calls) == members
    assert set(calls) == {row.logical.logical_artifact_id for row in manifests}
    (tmp_path / 'complete-read-scaling.json').write_text(json.dumps({
        'members': members, 'consumers': 3, 'full_member_verifications_before': baseline,
        'full_member_verifications_with_scope': len(calls), 'complete_members_retained': True,
        'claim': 'Actual physical/semantic checks through three retained consumers; no authority or science inferred',
    }, sort_keys=True) + '\n')
    # The next operation must verify afresh, rather than inherit a cache.
    calls.clear()
    plane.verify_manifests(manifests)
    assert len(calls) == members


@pytest.mark.parametrize("guard", ("scope", "member-consumer"))
def test_four_parent_threads_extend_real_snapshot_without_losing_final_mutation_guard(tmp_path, monkeypatch, guard):
    """Force the actual live-roster interleaving; all members are real bytes."""
    from concurrent.futures import ThreadPoolExecutor
    from pathlib import Path
    import sys
    from threading import Barrier, Event, Lock, get_ident
    from empirical_lawhood.infrastructure import artifacts as owner
    from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict

    plane, first = _publication(tmp_path, 1)
    requests = tuple(ArtifactWriteRequest(
        "exposed.concurrent." + str(index), "additional/member-" + str(index) + ".json", ObjectIdentity.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, "application/json", "exposed.additional-batch", "additional",
        ObjectIdentity("exposed.concurrent-subject." + str(index), ObjectIdentity.SCHEMA, "1.0.0", "b" * 64).canonical_bytes(),
        VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE) for index in range(3))
    publications = plane.write_batch(requests)
    additional = tuple(plane.read_manifest(value.materialization.relative_path) for value in publications)
    ready, entered, registered = Barrier(4), Event(), Event()
    guard_thread, completed, mutex = [], [], Lock()
    original_stat = owner.os.stat
    expected_caller = "_require_verification_snapshot_paths"
    initial_path = plane.root.resolve(first[0].materialization.relative_path + ".manifest.json", for_write=False)

    def interleaved_stat(path, *args, **kwargs):
        if (guard_thread and get_ident() == guard_thread[0] and Path(path) == initial_path
                and sys._getframe(1).f_code.co_name == expected_caller and not entered.is_set()):
            entered.set()
            assert registered.wait(15), "parallel member verification did not finish"
        return original_stat(path, *args, **kwargs)

    # The final guard must also reject mutation of a member first encountered
    # by another parent while the initial roster was being traversed.
    with pytest.raises(ArtifactIdentityConflict, match="changed"):
        with plane.verification_scope() as scoped:
            scoped.read_manifest(first[0].materialization.relative_path)
            monkeypatch.setattr(owner.os, "stat", interleaved_stat)
            def verify_initial():
                guard_thread.append(get_ident())
                ready.wait(timeout=15)
                if guard == "scope":
                    scoped.require_verification_snapshot()
                else:
                    scoped._verify_manifests(first, {}, snapshots=scoped._read_verification.snapshots)
            def verify_additional(manifest):
                ready.wait(timeout=15)
                assert entered.wait(15), "initial snapshot traversal did not start"
                scoped.verify_manifest(manifest)
                with mutex:
                    completed.append(manifest.logical.logical_artifact_id)
                    if len(completed) == 3:
                        registered.set()
            with ThreadPoolExecutor(max_workers=4) as pool:
                futures = [pool.submit(verify_initial), *(pool.submit(verify_additional, value) for value in additional)]
                for future in futures:
                    future.result(timeout=30)
            assert len(completed) == 3
            scoped.require_verification_snapshot()
            changed = plane.root.resolve(additional[0].materialization.relative_path, for_write=False)
            changed.write_bytes(changed.read_bytes() + b" ")
