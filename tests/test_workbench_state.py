# SPDX-License-Identifier: MPL-2.0
"""Operational selections: bounded mutation, contention and current storage."""

from dataclasses import replace
from hashlib import sha256
from types import SimpleNamespace

import pytest

from empirical_lawhood.storage.artifacts import ExternalRootUnavailable, FilesystemState, GuardedExternalRoot
from empirical_lawhood.storage.workbench_state import MAX_STATE_BYTES, WorkbenchStateConflict, WorkbenchStateStore
from empirical_lawhood.storage.contracts.artifacts import ExternalRootContract


@pytest.fixture
def selected(tmp_path):
    root = tmp_path / "scratch"
    root.mkdir()
    contract = ExternalRootContract("software.ui.scratch", "Operational fixture", str(root), str(root),
        "empirical-lawhood/testing/ui-state", 1, allowed_filesystem_types=("ext4",))
    state = SimpleNamespace(value=FilesystemState(str(root), True, True, 10**9, False, None, None, "ext4"))

    class Inspector:
        def inspect(self, selected_contract):
            assert selected_contract == contract
            return state.value

    guard = GuardedExternalRoot(contract, Inspector())
    return WorkbenchStateStore(guard, root / "selection" / "collection.json", writable=True), state


def test_absent_read_creates_no_directory_or_lock(selected):
    store, _ = selected
    assert store.read() is None
    assert not store.path.parent.exists()


def test_compare_and_replace_preserves_concurrent_selection(selected):
    store, _ = selected
    first = b'{"entries":["first"]}\n'
    digest = store.replace(first, expected_sha256=None)
    assert digest == sha256(first).hexdigest() and store.read() == first
    second = b'{"entries":["first","second"]}\n'
    store.replace(second, expected_sha256=digest)
    with pytest.raises(WorkbenchStateConflict):
        store.replace(b'{"entries":["lost update"]}\n', expected_sha256=digest)
    assert store.read() == second
    assert not list(store.path.parent.glob("*.pending"))


def test_readonly_and_lost_mount_refuse_without_changing_bytes(selected):
    store, state = selected
    original = b'{"selected":true}\n'
    store.replace(original, expected_sha256=None)
    readonly = WorkbenchStateStore(store.root, store.path, writable=False)
    assert readonly.read() == original
    with pytest.raises(PermissionError):
        readonly.replace(b"{}", expected_sha256=sha256(original).hexdigest())
    state.value = replace(state.value, active_mount=False)
    with pytest.raises(ExternalRootUnavailable):
        store.read()
    with pytest.raises(ExternalRootUnavailable):
        store.replace(b"{}", expected_sha256=sha256(original).hexdigest())
    assert store.path.read_bytes() == original


def test_symlink_and_byte_bounds_refuse_without_target_mutation(selected, tmp_path):
    store, _ = selected
    outside = tmp_path / "unchanged.json"
    outside.write_bytes(b"{}")
    store.path.parent.mkdir()
    store.path.symlink_to(outside)
    with pytest.raises(ExternalRootUnavailable):
        store.read()
    with pytest.raises(ExternalRootUnavailable):
        store.replace(b"null", expected_sha256=None)
    assert outside.read_bytes() == b"{}"
    with pytest.raises(ValueError, match="byte bound"):
        store.replace(b" " * (MAX_STATE_BYTES + 1), expected_sha256=None)
