# SPDX-License-Identifier: MPL-2.0
"""Disposable exact-byte custody replicas confer no scientific authority."""

from dataclasses import replace
from hashlib import sha256
import json

import pytest

from empirical_lawhood.infrastructure import artifact_replication as owner
from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane, GuardedExternalRoot
from tests.test_artifact_publication_admission import _plane, _requests


@pytest.fixture
def case(tmp_path):
    source = _plane(tmp_path / "original")
    published = source.write_batch(_requests(2))
    manifests = tuple(source.read_manifest(item.materialization.relative_path) for item in published)
    target = _plane(tmp_path / "replica")
    control = source.root.resolve("additional-control.json", for_write=True)
    control.write_bytes(b'{"disclosed":"control"}\n')
    extra = owner.ReplicaFile("additional-control.json", control.stat().st_size, sha256(control.read_bytes()).hexdigest())
    return source, target, manifests, extra, tmp_path / "replica-receipt.json"


def copy(case, **changes):
    source, target, manifests, extra, receipt = case
    operands = dict(publications=(manifests[0],), supplemental_files=(extra,),
                    receipt_path=receipt, maximum_bytes=10 * 1024**2, maximum_files=100)
    operands.update(changes)
    return owner.replicate_artifact_publications(source, target.root, **operands)


@pytest.mark.parametrize("compact", [False, True])
def test_replica_preserves_complete_publication_and_original_control_bytes(case, monkeypatch, compact):
    source, target, manifests, extra, receipt_path = case
    if compact:
        from empirical_lawhood.infrastructure.artifact_sidecars import encode_artifact_manifest_reference

        for manifest in manifests:
            path = source.root.resolve(manifest.materialization.relative_path + ".manifest.json", for_write=False)
            path.write_bytes(encode_artifact_manifest_reference(manifest.logical, manifest.materialization, manifest.publication))
    unselected = source.root.resolve("unselected-bank.bin", for_write=True)
    unselected.write_bytes(b"not part of the selected publication closure\n")
    original_resolve = source.root.resolve
    original_verify = source.root.verify
    before = {path: (path.stat().st_mtime_ns, path.stat().st_size, sha256(path.read_bytes()).hexdigest())
              for path in source.root.verify(for_write=False).rglob("*") if path.is_file()}

    def read_resolve(relative, **kwargs):
        assert kwargs["for_write"] is False, "replication attempted to mutate the original root"
        return original_resolve(relative, **kwargs)

    def read_verify(**kwargs):
        assert kwargs["for_write"] is False
        return original_verify(**kwargs)

    monkeypatch.setattr(source.root, "resolve", read_resolve)
    monkeypatch.setattr(source.root, "verify", read_verify)
    receipt = copy(case)
    assert receipt.receipt_path == receipt_path
    record = json.loads(receipt_path.read_bytes())
    assert record["status"] == "COMPLETE" and record["execution_authority"] == "NONE"
    assert record["source_contract"] != record["target_contract"]
    assert source.root.contract.storage_root_id == target.root.contract.storage_root_id
    assert len(receipt.files) == 6
    assert extra in receipt.files
    assert not target.root.resolve(unselected.name, for_write=False).exists()
    for member in receipt.files:
        assert original_resolve(member.relative_path, for_write=False).read_bytes() == target.root.resolve(member.relative_path, for_write=False).read_bytes()
    for manifest in manifests:
        assert target.read_manifest(manifest.materialization.relative_path) == manifest
        target.verify_manifest(manifest)
    assert before == {path: (path.stat().st_mtime_ns, path.stat().st_size, sha256(path.read_bytes()).hexdigest())
                      for path in original_verify(for_write=False).rglob("*") if path.is_file()}


@pytest.mark.parametrize("changes", [{"maximum_files": 1}, {"maximum_bytes": 1}])
def test_replica_bounds_refuse_before_copy(case, changes):
    with pytest.raises(ValueError, match="explicit file or byte bound"):
        copy(case, **changes)
    assert not tuple(case[1].root.verify(for_write=False).iterdir())
    assert not case[4].exists()


@pytest.mark.parametrize("defect", ["namespace", "nonempty", "inside-receipt", "missing-marker", "wrong-sibling"])
def test_replica_refuses_identity_or_incomplete_publication_before_copy(case, defect):
    source, target, manifests, _, receipt = case
    if defect == "namespace":
        changed = replace(target.root.contract, storage_root_id="another.namespace")
        target = ExternalArtifactPlane(GuardedExternalRoot(changed))
        case = source, target, *case[2:]
    elif defect == "nonempty":
        target.root.resolve("occupied", for_write=True).write_bytes(b"existing")
    elif defect == "inside-receipt":
        receipt = target.root.resolve("replica-receipt.json", for_write=False)
    elif defect == "missing-marker":
        source.root.resolve(manifests[0].publication.commit_marker_relative_path, for_write=False).unlink()
    else:
        source.root.resolve(manifests[1].materialization.relative_path + ".manifest.json", for_write=False).write_bytes(b"{}")
    with pytest.raises((ValueError, RuntimeError, OSError)):
        copy(case, receipt_path=receipt)
    assert not receipt.exists()


@pytest.mark.parametrize("defect", ["wrong-extra-hash", "source-change", "destination-change"])
def test_copy_drift_retains_partial_replica_without_complete_receipt(case, monkeypatch, defect):
    source, target, manifests, extra, receipt = case
    options = {}
    if defect == "wrong-extra-hash":
        options["supplemental_files"] = (replace(extra, sha256="0" * 64),)
    else:
        original = owner.copy_bounded_file
        changed = False

        def copying(source_path, destination, **kwargs):
            nonlocal changed
            result = original(source_path, destination, **kwargs)
            if not changed:
                changed = True
                if defect == "destination-change":
                    destination.write_bytes(b"changed")
                else:
                    selected = source.root.resolve(manifests[0].materialization.relative_path, for_write=False)
                    selected.write_bytes(b"changed")
            return result

        monkeypatch.setattr(owner, "copy_bounded_file", copying)
    with pytest.raises((ValueError, RuntimeError)):
        copy(case, **options)
    assert tuple(target.root.verify(for_write=False).iterdir())
    assert not receipt.exists()


def test_current_access_is_refreshed_during_copy_before_complete_receipt(case, monkeypatch):
    original = owner.copy_bounded_file
    revoked = False

    def require_current():
        if revoked:
            raise PermissionError('original copy access revoked')

    def copying(*args, **kwargs):
        nonlocal revoked
        result = original(*args, **kwargs)
        revoked = True
        return result

    monkeypatch.setattr(owner, 'copy_bounded_file', copying)
    with pytest.raises(PermissionError, match='access revoked'):
        copy(case, require_current=require_current)
    assert tuple(case[1].root.verify(for_write=False).iterdir())
    assert not case[4].exists()


@pytest.mark.parametrize('mid_file', (False, True))
def test_resume_reuses_complete_files_and_restarts_only_unpublished_partial(case, monkeypatch, mid_file):
    original = owner.copy_bounded_file
    calls = []
    def interrupted(source, destination, **kwargs):
        calls.append(source.name)
        if len(calls) == 3:
            if mid_file:
                destination.write_bytes(b'interrupted partial bytes')
            raise InterruptedError('disclosed copy interruption')
        return original(source, destination, **kwargs)
    monkeypatch.setattr(owner, 'copy_bounded_file', interrupted)
    with pytest.raises(InterruptedError):
        copy(case, resume=True)
    assert not case[4].exists()
    assert case[4].with_name(case[4].name + '.progress.json').exists()
    completed = {path: path.stat().st_ino for path in case[1].root.verify(for_write=False).rglob('*')
        if path.is_file() and not path.name.endswith('.partial')}
    assert len(completed) == 2
    calls.clear()
    def resumed(source, destination, **kwargs):
        calls.append(source.name)
        return original(source, destination, **kwargs)
    monkeypatch.setattr(owner, 'copy_bounded_file', resumed)
    result = copy(case, resume=True)
    assert len(calls) == len(result.files) - 2
    assert all(path.stat().st_ino == inode for path, inode in completed.items())
    assert not tuple(case[1].root.verify(for_write=False).rglob('*.partial'))
    calls.clear()
    repeated = copy(case, resume=True)
    assert repeated == result and not calls


@pytest.mark.parametrize('damage', ('target', 'source', 'extra', 'plan', 'access'))
def test_resume_refuses_changed_custody_without_complete_receipt(case, monkeypatch, damage):
    original = owner.copy_bounded_file
    calls = []
    def interrupted(*args, **kwargs):
        if calls:
            raise InterruptedError('disclosed interruption')
        calls.append(1)
        return original(*args, **kwargs)
    monkeypatch.setattr(owner, 'copy_bounded_file', interrupted)
    with pytest.raises(InterruptedError):
        copy(case, resume=True)
    monkeypatch.setattr(owner, 'copy_bounded_file', original)
    target = case[1].root.verify(for_write=False)
    options = {}
    if damage == 'target':
        next(path for path in target.rglob('*') if path.is_file()).write_bytes(b'changed')
    elif damage == 'source':
        case[0].root.resolve(case[3].relative_path, for_write=False).write_bytes(b'changed')
    elif damage == 'extra':
        (target / 'unexpected').write_bytes(b'foreign')
    elif damage == 'plan':
        options['maximum_files'] = 101
    else:
        def revoked():
            raise PermissionError('disclosed revoked access')
        options['require_current'] = revoked
    with pytest.raises((ValueError, RuntimeError, PermissionError)):
        copy(case, resume=True, **options)
    assert not case[4].exists()


@pytest.mark.parametrize('damage', ('original', 'destination', 'extra'))
def test_complete_receipt_follows_the_final_source_and_destination_guard(case, damage):
    def changed():
        root = case[0].root if damage == 'original' else case[1].root
        name = 'unexpected' if damage == 'extra' else case[3].relative_path
        root.resolve(name, for_write=True).write_bytes(b'changed after larger custody guard')
    with pytest.raises((ValueError, RuntimeError)):
        copy(case, resume=True, before_complete=changed)
    assert not case[4].exists()
