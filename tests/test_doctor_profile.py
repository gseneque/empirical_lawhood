# SPDX-License-Identifier: MPL-2.0
"""Actual CLI diagnostics honor profiles without creating an execution plane."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from rich.text import Text
from typer.testing import CliRunner

from empirical_lawhood.cli.app import app
from empirical_lawhood.execution.operator_profile import OperatorStorageAccessMode, OperatorStorageProfile


@pytest.mark.parametrize("arguments", (("doctor", "--route", "reactor"), ("capability", "list", "--limit", "5")))
def test_cold_diagnostics_and_discovery_use_only_their_declarations(tmp_path, arguments):
    from empirical_lawhood.execution.generated_extension_bundles import GENERATED_EXTENSION_BUNDLE_AGGREGATE

    code = """
import sys
class ForbidExecutableImports:
    def find_spec(self, name, path=None, target=None):
        if name in {"h5py", "scipy", "empirical_lawhood.api.composition",
                    "empirical_lawhood.adapters.composition.generated_executable_bindings"}:
            raise AssertionError("doctor imported " + name)
        return None
sys.meta_path.insert(0, ForbidExecutableImports())
from empirical_lawhood.cli.entry import main
main()
"""
    result = subprocess.run([sys.executable, "-c", code, *arguments, "--format", "json"],
                            cwd=tmp_path, capture_output=True, text=True, check=True, timeout=120)
    payload = json.loads(result.stdout)["payload"]
    if arguments[0] == "capability":
        page = payload["value"]
        assert page["returned_count"] == len(page["registrations"]) == len(page["execution_availability"]) == 5
        return
    catalog = GENERATED_EXTENSION_BUNDLE_AGGREGATE.candidate_capability_catalog
    assert payload["capability_count"] == len(catalog.registrations)
    assert payload["repository_root"] == "" and payload["capability_registry_fingerprint"] is None
    assert payload["optional_dependencies"]


def _profile(root: Path) -> OperatorStorageProfile:
    # /dev/shm supplies an isolated, real Linux mount for software diagnostics.
    # These empty temporary directories contain no scientific run or authority.
    return OperatorStorageProfile(
        profile_id="test-doctor-storage",
        backend_key="external-filesystem",
        backend_version="1.0.0",
        external_root_locator=str(root),
        required_mount_path="/dev/shm",
        artifact_namespace="artifacts",
        scientific_scratch_namespace="scratch",
        access_mode=OperatorStorageAccessMode.READ_WRITE,
        expected_mount_source=None,
        expected_volume_identity=None,
        allowed_filesystem_types=("tmpfs",),
        containment_policy_key="strict-mount-contained-no-symlink",
        minimum_free_bytes=1,
        read_only_mirror_ids=(),
        maximum_parallel_tasks=1,
        authority_granted=False,
    )


def _invoke(tmp_path: Path, raw: bytes | None):
    project = tmp_path / "project"
    project.mkdir(exist_ok=True)
    if not (project / ".git").exists():
        subprocess.run(["git", "init", "--quiet", str(project)], check=True)
    args = ["--project-root", str(project)]
    if raw is not None:
        profile = tmp_path / "profile.json"
        profile.write_bytes(raw)
        args += ["--operator-profile", str(profile)]
    result = CliRunner().invoke(app, [*args, "doctor", "--format", "json"])
    assert sorted(p.name for p in project.iterdir()) == [".git"], "doctor wrote local state"
    return result


@pytest.mark.parametrize("force_color", (False, True))
def test_no_profile_is_portable_and_malformed_profile_is_not_ignored(tmp_path: Path, monkeypatch, force_color) -> None:
    if force_color:
        monkeypatch.setenv("FORCE_COLOR", "1")
        monkeypatch.delenv("NO_COLOR", raising=False)
    else:
        monkeypatch.delenv("FORCE_COLOR", raising=False)
        monkeypatch.setenv("NO_COLOR", "1")
    result = _invoke(tmp_path, None)
    assert result.exit_code == 0, result.output
    assert "OPERATOR_STORAGE_UNCONFIGURED" in json.loads(result.stdout)["reason_codes"]
    malformed = _invoke(tmp_path, b'{"not":"an operator storage profile"}')
    assert malformed.exit_code == 2, malformed.output
    assert "operator-profile" in Text.from_ansi(malformed.output).plain


@pytest.mark.parametrize("read_only", (False, True))
def test_valid_profile_reports_real_mount_and_honors_access_mode(
    tmp_path: Path, read_only: bool
) -> None:
    with TemporaryDirectory(prefix="empirical-lawhood-doctor-", dir="/dev/shm") as directory:
        root = Path(directory)
        (root / "artifacts").mkdir()
        profile = _profile(root)
        if read_only:
            profile = replace(profile, access_mode=OperatorStorageAccessMode.READ_ONLY)
        before = sorted(root.rglob("*"))
        result = _invoke(tmp_path, profile.canonical_bytes())
        assert result.exit_code == 0, result.output
        document = json.loads(result.stdout)
        payload = document["payload"]
        assert payload["external_root"] == str(root / "artifacts")
        assert payload["mount_active"] is True
        assert payload["storage_read_ready"] is True
        assert payload["storage_write_ready"] is not read_only
        assert ("OPERATOR_STORAGE_READ_ONLY" in document["reason_codes"]) is read_only
        assert "OPERATOR_STORAGE_UNCONFIGURED" not in document["reason_codes"]
        assert sorted(root.rglob("*")) == before


@pytest.mark.parametrize("failure", ("filesystem", "space", "missing", "mount", "permission"))
def test_profile_unavailability_is_diagnosed_without_initialization(
    tmp_path: Path, failure: str
) -> None:
    with TemporaryDirectory(prefix="empirical-lawhood-doctor-", dir="/dev/shm") as directory:
        root = Path(directory)
        profile = _profile(root)
        if failure != "missing":
            (root / "artifacts").mkdir()
        if failure == "filesystem":
            profile = replace(profile, allowed_filesystem_types=("unavailable-filesystem",))
            expected = "EXTERNAL_FILESYSTEM_NOT_ALLOWED"
        elif failure == "space":
            profile = replace(profile, minimum_free_bytes=2**60)
            expected = "EXTERNAL_FREE_SPACE_BELOW_FLOOR"
        elif failure == "mount":
            profile = replace(profile, required_mount_path=str(root))
            expected = "EXTERNAL_MOUNT_INACTIVE"
        elif failure == "permission":
            (root / "artifacts").chmod(0o500)
            expected = "EXTERNAL_STORAGE_NOT_WRITABLE"
        else:
            expected = "EXTERNAL_STORAGE_ABSENT"
        before = sorted(root.rglob("*"))
        result = _invoke(tmp_path, profile.canonical_bytes())
        assert result.exit_code == 0, result.output
        document = json.loads(result.stdout)
        assert expected in document["reason_codes"]
        assert document["payload"]["storage_write_ready"] is False
        assert sorted(root.rglob("*")) == before


def test_profile_containment_is_checked_before_mount_inspection(tmp_path: Path) -> None:
    profile = replace(_profile(tmp_path / 'project'), required_mount_path=str(tmp_path))
    result = _invoke(tmp_path, profile.canonical_bytes())
    assert result.exit_code == 2
    assert "forbidden local root" in result.output


def test_explicit_local_policy_admits_selected_home_child_but_preserves_exclusions(tmp_path):
    from empirical_lawhood.execution.operator_profile import resolve_external_root_contract
    home, temporary = tmp_path / 'home', tmp_path / 'temporary'
    project = home / 'checkout'
    for path in (home, temporary, project): path.mkdir(exist_ok=True)
    selected = home / 'selected-study'
    profile = replace(_profile(selected), containment_policy_key='explicit-local-contained-no-symlink',
        required_mount_path='/', allowed_filesystem_types=())
    resolve = lambda value: resolve_external_root_contract(value, repo_root=project,
        home_root=home, temporary_root=temporary)
    assert resolve(profile).canonical_path == str(selected / 'artifacts')
    for excluded in (home, project, project / 'artifacts', temporary / 'study'):
        with pytest.raises(ValueError, match='forbidden local root'):
            resolve(replace(profile, external_root_locator=str(excluded)))
    with pytest.raises(ValueError, match='filesystem root'):
        replace(profile, external_root_locator='/')
    strict = replace(profile, containment_policy_key='strict-mount-contained-no-symlink',
        required_mount_path=str(home))
    with pytest.raises(ValueError, match='forbidden local root'): resolve(strict)
    alias = home / 'alias'
    alias.symlink_to(project, target_is_directory=True)
    with pytest.raises(ValueError, match='forbidden local root'):
        resolve(replace(profile, external_root_locator=str(alias)))
