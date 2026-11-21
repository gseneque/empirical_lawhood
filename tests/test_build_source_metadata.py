# SPDX-License-Identifier: MPL-2.0
"""Build identity from a literal committed fixture and Git-free source export."""

from hashlib import sha256
import io
import json
from pathlib import Path
import subprocess
import tarfile
import tomllib
from types import SimpleNamespace
import zipfile

import pytest
import yaml

from scripts import build_source_metadata as owner

ROOT = Path(__file__).resolve().parents[1]


def test_deposit_and_software_citation_match_the_selected_distribution_version():
    distribution = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    citation = yaml.safe_load((ROOT / "CITATION.cff").read_bytes())
    deposit = json.loads((ROOT / ".zenodo.json").read_bytes())
    assert citation["version"] == deposit["version"] == distribution
    for related in deposit["related_identifiers"]:
        if related["relation"] == "isIdenticalTo" and "/tree/v" in related["identifier"]:
            assert related["identifier"].rsplit("/tree/v", 1)[1] == distribution


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
        "src/empirical_lawhood/package_data/operand.txt": b"literal mathematical operand\n",
        "scripts/entry.py": b"# literal entry fixture\n", "uv.lock": b"version = 1\n",
        "pyproject.toml": b"[project]\nname = 'empirical-lawhood'\nversion = '0.0.test'\n",
        "docs/public.md": b"# Public fixture instructions\n"}
    # These are the build owner's explicit executable policy/process inputs,
    # copied as implementation fixtures; no scientific records are borrowed.
    for relative in (
        "src/empirical_lawhood/storage/source_policy.py",
        "src/empirical_lawhood/execution/local/bounded_process.py",
    ):
        payloads[relative] = (ROOT / relative).read_bytes()
    for name in ("build_source_metadata.py", "hatch_metadata.py"):
        payloads["scripts/" + name] = (ROOT / "scripts" / name).read_bytes()
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


def test_documentation_hook_retains_the_exact_commit_through_git_free_sdist(build_case, tmp_path, monkeypatch):
    from scripts.hatch_metadata import CustomMetadataHook

    raw = owner.build_source_metadata(build_case.root)
    commit = json.loads(raw)["implementation_commit"]
    metadata = {}
    CustomMetadataHook(str(build_case.root), {}).update(metadata)
    assert metadata["urls"]["Documentation"] == f"{owner.PROJECT_REPOSITORY}/blob/{commit}/README.md"
    source = export_source(build_case, tmp_path / "source-export")
    write(source / owner.SOURCE_METADATA_FILENAME, raw)
    def forbidden(*args, **kwargs):
        pytest.fail("Git-free metadata hook attempted a process")
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    rebuilt = {}
    CustomMetadataHook(str(source), {}).update(rebuilt)
    assert rebuilt == metadata


@pytest.mark.parametrize("artifact", ("wheel", "sdist"))
@pytest.mark.parametrize("defect", (None, "main", "wrong-commit", "missing", "duplicate", "oversized"))
def test_artifact_gate_checks_actual_documentation_metadata(tmp_path, artifact, defect):
    from scripts.release_check import verify_artifact_documentation

    commit = "e" * 40
    url = f"{owner.PROJECT_REPOSITORY}/blob/{commit}/README.md"
    header = f"Project-URL: Documentation, {url}\n"
    good = ("Metadata-Version: 2.4\nName: empirical-lawhood\n" + header + "\n").encode()
    altered = good
    if defect == "main":
        altered = good.replace(commit.encode(), b"main")
    elif defect == "wrong-commit":
        altered = good.replace(commit.encode(), b"f" * 40)
    elif defect == "missing":
        altered = good.replace(header.encode(), b"")
    elif defect == "duplicate":
        altered = good.replace(header.encode(), (header + header).encode())
    elif defect == "oversized":
        altered = good + b"x" * (128 * 1024)
    wheel = tmp_path / "selected.whl"
    sdist = tmp_path / "selected.tar.gz"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("empirical_lawhood-0.3.0.dist-info/METADATA", altered if artifact == "wheel" else good)
    with tarfile.open(sdist, "w:gz") as archive:
        raw = altered if artifact == "sdist" else good
        info = tarfile.TarInfo("empirical_lawhood-0.3.0/PKG-INFO")
        info.size = len(raw)
        archive.addfile(info, io.BytesIO(raw))
    if defect:
        with pytest.raises((ValueError, RuntimeError), match="metadata|documentation"):
            verify_artifact_documentation(wheel, sdist, implementation_commit=commit)
    else:
        assert verify_artifact_documentation(wheel, sdist, implementation_commit=commit) == {
            "implementation_commit": commit, "wheel": url, "sdist": url}


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


@pytest.mark.parametrize("name", ("src/empirical_lawhood/untracked.py", "src/empirical_lawhood/package_data/new.txt", "scripts/untracked.py"))
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
