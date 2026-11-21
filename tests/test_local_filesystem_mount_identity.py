# SPDX-License-Identifier: MPL-2.0
"""Disclosed mount facts exercise storage identity; no scientific authority."""

import json
from types import SimpleNamespace

import pytest

from empirical_lawhood.storage import artifacts as owner
from empirical_lawhood.storage.contracts.artifacts import ExternalRootContract


@pytest.mark.parametrize("copies", (1, 2, 3))
@pytest.mark.parametrize("conflict", (None, "source", "uuid", "fstype", "target"))
def test_repeated_mount_identity_accepts_only_unanimous_facts(tmp_path, monkeypatch, copies, conflict):
    mount = tmp_path / "mount"
    root = mount / "artifacts"
    root.mkdir(parents=True)
    fact = {"source": "/dev/disclosed-test", "uuid": "disclosed-volume",
            "fstype": "ext4", "target": str(mount)}
    facts = [dict(fact) for _ in range(copies)]
    if conflict is not None:
        facts[-1][conflict] = "foreign-identity"
    calls = []

    def observe(argv, **bounds):
        calls.append((argv, bounds))
        return SimpleNamespace(returncode=0, stdout=json.dumps({"filesystems": facts}).encode())

    monkeypatch.setattr(owner, "run_bounded_command", observe)
    monkeypatch.setattr(owner.os.path, "ismount", lambda path: path == mount)
    contract = ExternalRootContract("test.volume", "test volume", str(root), str(mount), "empirical-lawhood/test/volume", 0,
        expected_mount_source=fact["source"], expected_volume_identity=fact["uuid"],
        allowed_filesystem_types=("ext4",))
    guard = owner.GuardedExternalRoot(contract)
    if conflict is None:
        assert guard.verify(for_write=True) == root
        assert guard.diagnostic().write_ready
    else:
        with pytest.raises(owner.ExternalRootUnavailable):
            guard.verify(for_write=True)
        assert not guard.diagnostic().read_ready
    assert calls and all(bounds["timeout_seconds"] == 5 for _, bounds in calls)
    assert not tuple(root.iterdir())


def test_missing_mount_facts_refuse_storage(tmp_path, monkeypatch):
    monkeypatch.setattr(owner, "run_bounded_command", lambda *args, **kwargs:
        SimpleNamespace(returncode=0, stdout=b'{"filesystems": []}'))
    monkeypatch.setattr(owner.os.path, "ismount", lambda path: True)
    contract = ExternalRootContract("test.volume", "test volume", str(tmp_path), str(tmp_path), "empirical-lawhood/test/volume", 0)
    guard = owner.GuardedExternalRoot(contract)
    with pytest.raises(owner.ExternalRootUnavailable, match="not active"):
        guard.verify(for_write=False)
