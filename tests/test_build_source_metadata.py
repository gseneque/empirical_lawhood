# SPDX-License-Identifier: MPL-2.0
"""Build identity from a literal committed fixture and Git-free source export."""

from hashlib import sha256
import io
import json
from pathlib import Path
import subprocess
import tarfile
from types import SimpleNamespace

import pytest

from scripts import build_source_metadata as owner

ROOT = Path(__file__).resolve().parents[1]


def git(root, *arguments):
    return subprocess.check_output(["git", *arguments], cwd=root, stderr=subprocess.PIPE)


def write(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


@pytest.fixture
def build_case(tmp_path):
    root = tmp_path / "literal-build-source"
    payloads = {"src/empirical_lawhood/__init__.py": b"# literal package fixture\n",
        "src/empirical_lawhood/operation.py": b"VALUE = 42\n",
        "src/empirical_lawhood/resources/operand.txt": b"literal mathematical operand\n",
        "scripts/entry.py": b"# literal entry fixture\n", "uv.lock": b"version = 1\n",
        "pyproject.toml": b"[project]\nname = 'empirical-lawhood'\nversion = '0.0.test'\n",
        "docs/public.md": b"# Public fixture instructions\n"}
    # These are the build owner's explicit executable policy/process inputs,
    # copied as implementation fixtures; no scientific records are borrowed.
    for name in ("source_policy.py", "bounded_process.py"):
        relative = "src/empirical_lawhood/infrastructure/" + name
        payloads[relative] = (ROOT / relative).read_bytes()
    for name, raw in payloads.items():
        write(root / name, raw)
    git(root, "init", "--template=")
    git(root, "add", ".")
    git(root, "-c", "user.name=Software fixture", "-c", "user.email=fixture@example.invalid",
        "commit", "-m", "literal source for build controls")
    return SimpleNamespace(root=root, payloads=payloads)


def export_source(case, target):
    archive = git(case.root, "archive", "HEAD")
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as packet:
        for member in packet:
            if member.isdir():
                continue
            assert member.isfile() and ".." not in Path(member.name).parts
            raw = packet.extractfile(member).read()
            write(target / member.name, raw)
    return target


def test_build_metadata_binds_exact_complete_commit_archive_tree_and_members(build_case):
    case = build_case
    raw = owner.build_source_metadata(case.root)
    value = json.loads(raw)
    assert owner.encode(value) == raw
    assert value["implementation_commit"] == git(case.root, "rev-parse", "HEAD").decode().strip()
    assert value["implementation_sha256"] == sha256(git(case.root, "archive", "HEAD")).hexdigest()
    assert value["source_tree_sha256"] == sha256(git(case.root, "ls-tree", "-r", "-z", "--full-tree", "HEAD")).hexdigest()
    assert value["tracked_files"] == [{"relative_path": name, "mode": "100644", "size_bytes": len(payload),
        "sha256": sha256(payload).hexdigest()} for name, payload in sorted(case.payloads.items())]


def test_source_distribution_rebuild_retains_identical_metadata_without_git(build_case, tmp_path, monkeypatch):
    case = build_case
    expected = owner.build_source_metadata(case.root)
    source = export_source(case, tmp_path / "ordinary-source-distribution")
    write(source / owner.SOURCE_METADATA_FILENAME, expected)

    def forbidden(*args, **kwargs):
        pytest.fail("source distribution rebuild attempted a process or Git")

    monkeypatch.setattr(subprocess, "Popen", forbidden)
    assert owner.build_source_metadata(source) == expected


@pytest.mark.parametrize("name", ("src/empirical_lawhood/operation.py", "scripts/entry.py", "uv.lock", "pyproject.toml"))
@pytest.mark.parametrize("route", ("checkout", "sdist"))
def test_execution_and_build_inputs_must_match_the_committed_identity(build_case, tmp_path, name, route):
    case = build_case
    if route == "sdist":
        raw = owner.build_source_metadata(case.root)
        selected = export_source(case, tmp_path / "source-export")
        write(selected / owner.SOURCE_METADATA_FILENAME, raw)
    else:
        selected = case.root
    (selected / name).write_bytes(b"foreign execution or build operand\n")
    with pytest.raises((ValueError, PermissionError)):
        owner.build_source_metadata(selected)


@pytest.mark.parametrize("name", ("src/empirical_lawhood/untracked.py", "src/empirical_lawhood/resources/new.txt", "scripts/untracked.py"))
@pytest.mark.parametrize("route", ("checkout", "sdist"))
def test_complete_source_census_refuses_extra_executable_and_package_resources(build_case, tmp_path, name, route):
    case = build_case
    if route == "sdist":
        raw = owner.build_source_metadata(case.root)
        selected = export_source(case, tmp_path / "source-export")
        write(selected / owner.SOURCE_METADATA_FILENAME, raw)
    else:
        selected = case.root
    write(selected / name, b"extra undeclared member\n")
    with pytest.raises((ValueError, PermissionError)):
        owner.build_source_metadata(selected)


@pytest.mark.parametrize("defect", ("commit", "archive", "tree", "escaping", "duplicate", "empty", "encoding", "removed-member"))
def test_malformed_or_forged_retained_metadata_cannot_describe_a_source_distribution(build_case, tmp_path, defect):
    case = build_case
    raw = owner.build_source_metadata(case.root)
    selected = export_source(case, tmp_path / "source-export")
    value = json.loads(raw)
    if defect == "commit":
        value["implementation_commit"] = "HEAD"
    elif defect == "archive":
        value["implementation_sha256"] = "not-a-digest"
    elif defect == "tree":
        value["source_tree_sha256"] = "not-a-digest"
    elif defect == "escaping":
        value["tracked_files"][0]["relative_path"] = "../outside.py"
    elif defect == "duplicate":
        value["tracked_files"].append(value["tracked_files"][-1])
    elif defect == "empty":
        value["tracked_files"] = []
    elif defect == "removed-member":
        value["tracked_files"] = [row for row in value["tracked_files"]
            if row["relative_path"] != "src/empirical_lawhood/operation.py"]
    raw = owner.encode(value)
    write(selected / owner.SOURCE_METADATA_FILENAME, raw.rstrip(b"\n") if defect == "encoding" else raw)
    with pytest.raises((ValueError, PermissionError)):
        owner.build_source_metadata(selected)


def test_retained_metadata_cannot_override_a_checkout_commit(build_case):
    case = build_case
    raw = owner.build_source_metadata(case.root)
    value = json.loads(raw)
    value["implementation_commit"] = "f" * 40
    write(case.root / owner.SOURCE_METADATA_FILENAME, owner.encode(value))
    with pytest.raises((ValueError, PermissionError)):
        owner.build_source_metadata(case.root)


@pytest.mark.parametrize("defect", ("symlink", "missing", "executable", "group-executable"))
def test_source_distribution_requires_exact_regular_member_mode_and_kind(build_case, tmp_path, defect):
    case = build_case
    raw = owner.build_source_metadata(case.root)
    source = export_source(case, tmp_path / "source-export")
    write(source / owner.SOURCE_METADATA_FILENAME, raw)
    member = source / "src/empirical_lawhood/operation.py"
    if defect == "symlink":
        foreign = tmp_path / "borrowed.py"
        member.rename(foreign)
        member.symlink_to(foreign)
    elif defect == "missing":
        member.unlink()
    elif defect == "executable":
        member.chmod(0o755)
    else:
        member.chmod(0o654)
    with pytest.raises((ValueError, PermissionError, OSError)):
        owner.build_source_metadata(source)
