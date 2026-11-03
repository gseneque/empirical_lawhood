# SPDX-License-Identifier: MPL-2.0
"""Authenticate an unchanged tested candidate for separate postcommit artifacts."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess

if __package__:
    from .release_check import portable_test_environment_policy, retained_test_options
else:
    from release_check import portable_test_environment_policy, retained_test_options


SCHEMA = "empirical-lawhood/release/precommit-portable-evidence"
REQUIRED_CHECKS = frozenset({"environment", "coverage-configuration", "tests", "critical-coverage",
                             "critical-coverage-json", "critical-coverage-inventory"})


RELEASE_INPUT_ROOTS = ("src/empirical_lawhood/", "scripts/", "tests/", "docs/", "configs/", "programmes/",
                       "experiments/",  # Original source selections retain their historical input scope.
                       "paper/", "assets/")
RELEASE_INPUT_FILES = frozenset({"pyproject.toml", "uv.lock", ".coveragerc", ".gitignore",
                               "README.md", "CONTRIBUTING.md", "LICENSE"})
_MAX_SELECTED_SOURCE_BYTES = 256 * 1024**2


def _selected_entries(root: Path, revision: str | None = None):
    command = (["git", "ls-files", "--stage", "-z"] if revision is None else
               ["git", "ls-tree", "-r", "-z", "--full-tree", revision])
    result = {}
    for entry in subprocess.check_output(command, cwd=root).split(b"\0"):
        if not entry:
            continue
        metadata, name = entry.split(b"\t", 1)
        fields = metadata.decode().split()
        mode, object_id = (fields[0], fields[1]) if revision is None else (fields[0], fields[2])
        if ((revision is None and fields[2] != "0") or mode not in {"100644", "100755"}
                or len(object_id) != 40 or any(value not in "0123456789abcdef" for value in object_id)):
            raise ValueError("Release source refuses unresolved or non-file selected entries")
        path = name.decode()
        if path in result or Path(path).is_absolute() or ".." in Path(path).parts:
            raise ValueError("Release source requires unique contained tracked paths")
        result[path] = (mode, object_id)
    return result


def release_input_paths(root: Path, *, revision: str | None = None) -> tuple[str, ...]:
    """Select code, tests, maintained guides, copied inputs and build controls."""
    from empirical_lawhood.infrastructure.source_policy import (
        MAINTAINED_ROOT_MARKDOWN, is_work_plan_path,
    )

    entries = _selected_entries(root, revision)
    unclassified = sorted(name for name in entries if "/" not in name and name.endswith(".md")
                          and name not in MAINTAINED_ROOT_MARKDOWN and not is_work_plan_path(name))
    if unclassified:
        raise ValueError(f"Release root Markdown requires a documentation or work-plan classification: {unclassified}")
    return tuple(sorted(name for name in entries if not is_work_plan_path(name)
                        and (name in RELEASE_INPUT_FILES or name.startswith(RELEASE_INPUT_ROOTS)
                             or name.startswith("LICENSES/") or name.endswith(".md"))))


def candidate_inventory(root: Path, *, selected_paths: tuple[str, ...] | None = None,
                        revision: str | None = None, verify_selected: bool = False) -> list[dict[str, object]]:
    """Describe the selected index's actual loaded bytes and executable modes."""
    entries = _selected_entries(root, revision)
    names = tuple(sorted(entries)) if selected_paths is None else selected_paths
    if (type(names) is not tuple or names != tuple(sorted(set(names)))
            or any(name not in entries for name in names)):
        raise ValueError("Release source selection is not an exact tracked path census")
    from empirical_lawhood.infrastructure.repository_identity import _descriptor_identity, _open_relative_read_only
    result = []
    selected_bytes = 0
    for path in names:
        mode, object_id = entries[path]
        descriptor = _open_relative_read_only(str(root), path)
        try:
            before = os.fstat(descriptor)
            permissions = stat.S_IMODE(before.st_mode)
            if (not stat.S_ISREG(before.st_mode) or permissions & ~0o777
                    or (not permissions & stat.S_IXUSR if mode == "100755" else permissions & 0o111)):
                raise ValueError(f"Loaded candidate executable mode differs: {path}")
            selected_bytes += before.st_size
            if selected_bytes > _MAX_SELECTED_SOURCE_BYTES:
                raise ValueError("Release selected source exceeds its bounded complete census")
            chunks = []
            remaining = before.st_size
            while remaining:
                chunk = os.read(descriptor, min(remaining, 1024 * 1024))
                if not chunk:
                    raise ValueError(f"Loaded candidate was truncated during authentication: {path}")
                chunks.append(chunk)
                remaining -= len(chunk)
            payload = b"".join(chunks)
            if os.read(descriptor, 1) or _descriptor_identity(os.fstat(descriptor)) != _descriptor_identity(before):
                raise ValueError(f"Loaded candidate changed during authentication: {path}")
        finally:
            os.close(descriptor)
        blob = hashlib.sha1(f"blob {len(payload)}\0".encode() + payload).hexdigest()
        if verify_selected and blob != object_id:
            raise ValueError(f"Loaded release input differs from its selected Git blob: {path}")
        result.append({"path": path, "mode": mode, "size_bytes": len(payload),
                       "sha256": hashlib.sha256(payload).hexdigest()})
    return sorted(result, key=lambda row: row["path"])


def inventory_digest(inventory) -> str:
    return hashlib.sha256(json.dumps(inventory, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _bound_member(root: Path, binding: dict) -> Path:
    name = binding["path"]
    relative = Path(name)
    if relative.is_absolute() or ".." in relative.parts or not relative.parts:
        raise ValueError("Portable evidence member must be a contained relative file")
    path = root / relative
    if any(part.is_symlink() for part in (path, *path.parents)):
        raise ValueError("Portable evidence refuses symlink members")
    if not path.is_file() or path.stat().st_size != binding["size_bytes"]:
        raise ValueError("Portable evidence member size differs")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    if digest.hexdigest() != binding["sha256"]:
        raise ValueError("Portable evidence member checksum differs")
    return path


def authenticate_portable_evidence(path: Path, root: Path) -> dict:
    """Verify evidence bytes and exact final-tree join; never execute tests."""
    if path.is_symlink() or path.stat().st_size > 16 * 1024**2:
        raise ValueError("Portable evidence requires a bounded ordinary file")
    record = json.loads(path.read_bytes())
    if record["schema"] != SCHEMA or record["status"] != "PASSED" or record["full_suite_invocations"] != 1:
        raise ValueError("Portable evidence is not one completed passing precommit suite")
    tree = subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], cwd=root, text=True).strip()
    if record["candidate_tree"] != tree:
        raise ValueError("Final commit tree differs from the tested candidate")
    if "selected_paths" in record:
        selected_paths = tuple(record["selected_paths"])
        if selected_paths != release_input_paths(root, revision="HEAD"):
            raise ValueError("Portable evidence changes the complete release input selection")
        current = inventory_digest(candidate_inventory(root, selected_paths=selected_paths,
                                                      revision="HEAD", verify_selected=True))
    else:
        current = inventory_digest(candidate_inventory(root))
    if current != record["inventory_before_sha256"] or current != record["inventory_after_sha256"]:
        raise ValueError("Candidate loaded bytes changed before or after its suite")
    if record["uv_lock_sha256"] != hashlib.sha256((root / "uv.lock").read_bytes()).hexdigest():
        raise ValueError("Portable evidence dependency lock differs")
    policy = record.get("test_environment_policy")
    if type(policy) is not dict or type(policy.get("basetemp")) is not str:
        raise ValueError("Portable evidence lacks the current all-retention test/coverage environment")
    basetemp = Path(policy["basetemp"])
    if (not basetemp.is_absolute() or ".." in basetemp.parts
            or str(basetemp) != policy["basetemp"] or basetemp.name != "test-artifacts"):
        raise ValueError("Portable evidence requires the original ordinary absolute fixture destination")
    # The artifact gate copies evidence into a new packet, without relocating
    # original test bodies or rewriting their recorded command/destination.
    candidate_packet = basetemp.parent
    if (type(policy.get("tmp_path_retention_count")) is not int
            or policy != portable_test_environment_policy(candidate_packet, root)):
        raise ValueError("Portable evidence does not bind the current all-retention test/coverage environment")
    checks = record["checks"]
    if len({item["name"] for item in checks}) != len(checks) or not REQUIRED_CHECKS <= {item["name"] for item in checks}:
        raise ValueError("Portable evidence is missing required check owners")
    for item in checks:
        if item["exit_code"] != 0 or item["disposition"] != "PASSED":
            raise ValueError("Portable evidence contains a failed or incomplete check")
        _bound_member(path.parent, {"path": item["log"], "size_bytes": item["size_bytes"], "sha256": item["sha256"]})
    suite = next(item for item in checks if item["name"] == "tests")
    command = suite["command"]
    expected_command = ["uv", "run", "--no-sync", "python", "-m", "coverage", "run", "-m", "pytest",
                        "-q", "-ra", "--fail-on-skip", *retained_test_options(candidate_packet),
                        "tests", "-m", "not native and not held"]
    if command != expected_command:
        raise ValueError("Portable evidence does not cover the exact supported required-skip selector")
    _bound_member(path.parent, record["coverage"])
    selected_inventory = _bound_member(path.parent, record["candidate_inventory"])
    if inventory_digest(json.loads(selected_inventory.read_bytes())) != current:
        raise ValueError("Retained candidate inventory does not describe the tested source bytes")
    return record
