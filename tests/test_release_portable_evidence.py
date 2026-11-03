# SPDX-License-Identifier: MPL-2.0
"""Reject mismatched source/evidence before an artifact-only release gate."""

import hashlib
import json
import shutil

import pytest

from scripts import release_portable_evidence as evidence


@pytest.fixture
def packet(tmp_path, monkeypatch):
    root = tmp_path / "source"
    root.mkdir()
    (root / "uv.lock").write_bytes(b"actual locked dependencies")
    (root / ".coveragerc").write_bytes(b"selected owner config")
    inventory = [{"path": "uv.lock", "mode": "100644", "size_bytes": 26, "sha256": "1"*64}]
    monkeypatch.setattr(evidence, "candidate_inventory", lambda selected: inventory)
    monkeypatch.setattr(evidence.subprocess, "check_output", lambda *a, **k: "abc123\n")
    log = tmp_path / "bound.log"
    log.write_bytes(b"completed check output\n")
    binding = {"path": log.name, "size_bytes": log.stat().st_size,
               "sha256": hashlib.sha256(log.read_bytes()).hexdigest()}
    checks = [{"name": name, "exit_code": 0, "disposition": "PASSED", "log": log.name,
               "size_bytes": binding["size_bytes"], "sha256": binding["sha256"],
               "command": ["uv", "run", "--no-sync", "python", "-m", "coverage", "run", "-m", "pytest",
                           "-q", "-ra", "--fail-on-skip", *evidence.retained_test_options(tmp_path),
                           "tests", "-m", "not native and not held"]}
              for name in sorted(evidence.REQUIRED_CHECKS)]
    inventory_file = tmp_path / "candidate-inventory.json"
    inventory_file.write_text(json.dumps(inventory))
    inventory_binding = {"path": inventory_file.name, "size_bytes": inventory_file.stat().st_size,
                         "sha256": hashlib.sha256(inventory_file.read_bytes()).hexdigest()}
    record = {"schema": evidence.SCHEMA, "status": "PASSED", "full_suite_invocations": 1,
              "candidate_tree": "abc123", "inventory_before_sha256": evidence.inventory_digest(inventory),
              "inventory_after_sha256": evidence.inventory_digest(inventory),
              "uv_lock_sha256": hashlib.sha256((root / "uv.lock").read_bytes()).hexdigest(),
              "test_environment_policy": evidence.portable_test_environment_policy(tmp_path, root),
              "checks": checks, "coverage": binding, "candidate_inventory": inventory_binding}
    path = tmp_path / "precommit.json"
    def write():
        path.write_text(json.dumps(record))
        return path
    return root, record, write, log


def test_exact_tree_join_authenticates_existing_bytes_without_test_execution(packet):
    root, record, write, _ = packet
    assert evidence.authenticate_portable_evidence(write(), root) == record


def test_explicit_selected_scope_reauthenticates_committed_blobs_and_refuses_scope_drift(packet, monkeypatch):
    root, record, write, _ = packet
    record["selected_paths"] = ["uv.lock"]
    monkeypatch.setattr(evidence, "release_input_paths", lambda selected, **kwargs: ("uv.lock",))
    original = evidence.candidate_inventory
    calls = []

    def selected_inventory(selected, **kwargs):
        calls.append(kwargs)
        return original(selected)

    monkeypatch.setattr(evidence, "candidate_inventory", selected_inventory)
    assert evidence.authenticate_portable_evidence(write(), root) == record
    assert calls == [{"selected_paths": ("uv.lock",), "revision": "HEAD", "verify_selected": True}]
    record["selected_paths"] = []
    with pytest.raises(ValueError, match="complete release input selection"):
        evidence.authenticate_portable_evidence(write(), root)


@pytest.mark.parametrize("field,value", [("candidate_tree", "other"), ("status", "FAILED"),
    ("inventory_after_sha256", "0"*64), ("uv_lock_sha256", "0"*64), ("full_suite_invocations", 2)])
def test_rejects_source_change_failure_or_duplicate_suite(packet, field, value):
    root, record, write, _ = packet
    record[field] = value
    with pytest.raises(ValueError):
        evidence.authenticate_portable_evidence(write(), root)


def test_bound_log_mutation_invalidates_precommit_pass(packet):
    root, _, write, log = packet
    path = write()
    log.write_bytes(b"altered check output!!\n")
    with pytest.raises(ValueError):
        evidence.authenticate_portable_evidence(path, root)


def test_incomplete_selection_or_check_owners_are_not_a_full_portable_pass(packet):
    root, record, write, _ = packet
    record["checks"] = [item for item in record["checks"] if item["name"] != "critical-coverage-inventory"]
    with pytest.raises(ValueError, match="owners"):
        evidence.authenticate_portable_evidence(write(), root)


def test_missing_required_skip_policy_refuses_reuse(packet):
    root, record, write, _ = packet
    next(item for item in record["checks"] if item["name"] == "tests")["command"].remove("--fail-on-skip")
    with pytest.raises(ValueError, match="selector"):
        evidence.authenticate_portable_evidence(write(), root)


def test_evidence_path_escape_refuses_file_access(packet):
    root, record, write, _ = packet
    record["coverage"]["path"] = "../outside.log"
    with pytest.raises(ValueError, match="contained"):
        evidence.authenticate_portable_evidence(write(), root)


@pytest.mark.parametrize("extra", [["--collect-only"], ["-k", "favourable"], ["--deselect", "tests/test_bad.py"], ["--ignore", "tests/test_bad.py"], ["tests/test_good.py::test_one"]])
def test_filtered_or_collect_only_command_is_not_full_suite_evidence(packet, extra):
    root, record, write, _ = packet
    next(item for item in record["checks"] if item["name"] == "tests")["command"].extend(extra)
    with pytest.raises(ValueError, match="exact supported"):
        evidence.authenticate_portable_evidence(write(), root)


def test_unbound_or_filtered_environment_refuses_full_suite_reuse(packet):
    root, record, write, _ = packet
    record["test_environment_policy"]["pytest_addopts"] = "--collect-only"
    with pytest.raises(ValueError, match="environment"):
        evidence.authenticate_portable_evidence(write(), root)


def test_copied_evidence_keeps_original_fixture_destination_without_reexecution(packet, tmp_path):
    root, record, write, _ = packet
    original = write()
    copied = tmp_path / "artifact-packet" / "precommit-portable"
    copied.mkdir(parents=True)
    for member in {original.name, *(row["log"] for row in record["checks"]),
                   record["coverage"]["path"], record["candidate_inventory"]["path"]}:
        shutil.copyfile(original.parent / member, copied / member)
    assert not (tmp_path / "test-artifacts").exists()
    assert evidence.authenticate_portable_evidence(copied / original.name, root) == record
    assert record["test_environment_policy"]["basetemp"] == str(tmp_path / "test-artifacts")
    assert not (copied / "test-artifacts").exists()


@pytest.mark.parametrize("field,value", [
    ("tmp_path_retention_policy", "failed"), ("tmp_path_retention_count", 2),
    ("tmp_path_retention_count", True), ("coverage_rcfile_sha256", "0" * 64),
])
def test_changed_retention_or_coverage_policy_refuses_current_reuse(packet, field, value):
    root, record, write, _ = packet
    record["test_environment_policy"][field] = value
    with pytest.raises(ValueError, match="environment"):
        evidence.authenticate_portable_evidence(write(), root)


def test_legacy_retention_packet_remains_ineligible_without_relabeling(packet):
    root, record, write, _ = packet
    policy = record["test_environment_policy"]
    record["test_environment_policy"] = {
        "pytest_addopts": policy["pytest_addopts"],
        "coverage_rcfile_sha256": policy["coverage_rcfile_sha256"],
    }
    with pytest.raises(ValueError, match="current all-retention"):
        evidence.authenticate_portable_evidence(write(), root)


@pytest.mark.parametrize("destination", ["relative/test-artifacts", "/packet/../test-artifacts",
                                         "/packet/disposable", "/packet/./test-artifacts"])
def test_noncanonical_fixture_destination_refuses_before_evidence_access(packet, destination):
    root, record, write, _ = packet
    record["test_environment_policy"]["basetemp"] = destination
    with pytest.raises(ValueError, match="fixture destination"):
        evidence.authenticate_portable_evidence(write(), root)


@pytest.mark.parametrize("option,replacement", [
    ("--basetemp", "/other/test-artifacts"),
    ("cache_dir=", "cache_dir=/other/pytest-cache"),
    ("tmp_path_retention_policy=all", "tmp_path_retention_policy=failed"),
    ("tmp_path_retention_count=1", "tmp_path_retention_count=2"),
])
def test_command_cannot_change_bound_fixture_retention_or_paths(packet, option, replacement):
    root, record, write, _ = packet
    command = next(row for row in record["checks"] if row["name"] == "tests")["command"]
    if option == "--basetemp":
        command[command.index(option) + 1] = replacement
    else:
        index = next(index for index, argument in enumerate(command) if argument.startswith(option))
        command[index] = replacement
    with pytest.raises(ValueError, match="exact supported"):
        evidence.authenticate_portable_evidence(write(), root)


def test_current_coverage_owner_change_invalidates_reuse(packet):
    root, _, write, _ = packet
    path = write()
    (root / ".coveragerc").write_bytes(b"different owner config")
    with pytest.raises(ValueError, match="environment"):
        evidence.authenticate_portable_evidence(path, root)
