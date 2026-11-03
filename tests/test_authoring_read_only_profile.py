# SPDX-License-Identifier: MPL-2.0
"""Read selection controls; actual retained custody is the held acceptance."""
from dataclasses import replace
from pathlib import Path

import pytest

from empirical_lawhood.api.authoring_handoff import resolve_authoring_directory
from empirical_lawhood.runtime.artifacts import ExternalRootContract
from empirical_lawhood.runtime.operator_profile import OperatorStorageAccessMode, OperatorStorageProfile, resolve_external_root_contract

ROOT = Path(__file__).resolve().parents[1]


def test_original_reader_selection_preserves_every_physical_policy_field():
    reader = ExternalRootContract("retained.original-id", "Current operational reader only",
        "/media/release-original/evidence/selected", "/media/release-original",
        OperatorStorageProfile.SCHEMA, 1024, "/dev/original", "original-volume", ("vfat",))
    replica = OperatorStorageProfile("release.replica", "external-filesystem", "1.0.0",
        "/media/release-replica/new-run", "/media/release-replica", "artifacts", "scratch",
        OperatorStorageAccessMode.READ_WRITE, "/dev/replica", "replica-volume", ("ext4",),
        "strict-mount-contained-no-symlink", 2048, (), 1, False)
    original = Path(reader.canonical_path)
    selected = replace(replica, profile_id=replica.profile_id + ".reader",
        external_root_locator=str(original.parent), artifact_namespace=original.name,
        scientific_scratch_namespace="unused-read-only-source-scratch",
        access_mode=OperatorStorageAccessMode.READ_ONLY,
        required_mount_path=reader.required_mount_path, minimum_free_bytes=reader.minimum_free_bytes,
        expected_mount_source=reader.expected_mount_source,
        expected_volume_identity=reader.expected_volume_identity,
        allowed_filesystem_types=reader.allowed_filesystem_types)
    assert selected.access_mode is OperatorStorageAccessMode.READ_ONLY
    assert selected.maximum_parallel_tasks == 1
    assert resolve_external_root_contract(selected, repo_root=ROOT, home_root=Path.home(),
        for_write=False, selected_contract=reader) == reader
    with pytest.raises(PermissionError, match="read/write"):
        resolve_external_root_contract(selected, repo_root=ROOT, home_root=Path.home())
    with pytest.raises(ValueError, match="physical policy"):
        resolve_external_root_contract(selected, repo_root=ROOT, home_root=Path.home(),
            for_write=False, selected_contract=replace(reader, minimum_free_bytes=reader.minimum_free_bytes + 1))
    assert replica.access_mode is OperatorStorageAccessMode.READ_WRITE


def test_directory_read_resolution_forwards_exact_mode_and_keeps_containment(tmp_path, monkeypatch):
    from empirical_lawhood.api import authoring_handoff as owner

    observed = []
    contract = ExternalRootContract("reader.control", "Read resolution control", str(tmp_path),
        str(tmp_path), OperatorStorageProfile.SCHEMA, 1, None, None, ())
    def select(profile, **kwargs):
        observed.append((profile, kwargs["for_write"]))
        return contract
    monkeypatch.setattr(owner, "resolve_external_root_contract", select)
    profile = object()
    assert resolve_authoring_directory(tmp_path, repo_root=ROOT, storage_profile=profile,
        escape_message="outside", for_write=False) == (tmp_path.resolve(), contract)
    assert observed == [(profile, False)]
    resolve_authoring_directory(tmp_path, repo_root=ROOT, storage_profile=profile, escape_message="outside")
    assert observed[-1] == (profile, True)
    for value in (0, 1, None, "false"):
        with pytest.raises(TypeError, match="exact bool"):
            resolve_authoring_directory(tmp_path, repo_root=ROOT, storage_profile=profile,
                escape_message="outside", for_write=value)
    monkeypatch.setattr(owner, "resolve_external_root_contract", lambda *a, **kw: replace(contract, canonical_path=str(tmp_path / "other")))
    with pytest.raises(ValueError, match="outside"):
        resolve_authoring_directory(tmp_path, repo_root=ROOT, storage_profile=profile, escape_message="outside", for_write=False)
