# SPDX-License-Identifier: MPL-2.0
"""Actual contributor collection/execution refuses silent changed-test omissions."""

from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from scripts import test_change_policy, test_profiles, test_purposes


def git(root, *args):
    return subprocess.check_output(["git", *args], cwd=root, stderr=subprocess.PIPE, text=True).strip()


def commit(root):
    git(root, "add", ".")
    git(root, "-c", "user.name=Software fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "software fixture")
    return git(root, "rev-parse", "HEAD")


@pytest.fixture
def contributor(tmp_path):
    root = tmp_path / "contributor"
    root.mkdir()
    (root / "tests").mkdir()
    (root / "scripts").mkdir()
    (root / "scripts/test_change_decisions.json").write_text(json.dumps({
        "schema": "empirical-lawhood/tests/change-decisions-v1", "modules": {}}))
    (root / "profile_fixture.py").write_bytes(Path(test_profiles.__file__).read_bytes())
    (root / "test_change_policy.py").write_bytes(Path(test_change_policy.__file__).read_bytes())
    (root / "scripts/test_purposes.py").write_bytes(Path(test_purposes.__file__).read_bytes())
    (root / "required_fixture.py").write_bytes((Path(__file__).parent / "conftest.py").read_bytes())
    (root / "conftest.py").write_text(
        "import profile_fixture\nprofile_fixture.CI_FILES = frozenset({'tests/test_core.py'})\n"
        "profile_fixture.CI_REQUIRED_CASES = frozenset({'tests/test_core.py::test_core'})\n"
        "profile_fixture.SCALE_FILES = frozenset()\n")
    (root / "tests/test_core.py").write_text("def test_core(): pass\n")
    git(root, "init", "--template=")
    return root, commit(root)


def declare(root, name, *, policy="bounded", exclusions=None, role=None):
    path = root / "scripts/test_change_decisions.json"
    document = json.loads(path.read_text())
    document["modules"][name] = {"profile": "integration", "policy": policy,
        "sha256": sha256((root / name).read_bytes()).hexdigest(), "reason": "Bounded changed adapter control",
        "exclusions": exclusions or {}}
    if role is not None:
        document["modules"][name]["role"] = role
    path.write_text(json.dumps(document))


def run(root, base, packet, *, comparison="--changed-tests-base"):
    command = [sys.executable, "-B", "-m", "pytest", "-q", "-p", "profile_fixture", "-p", "required_fixture",
               "--fail-on-skip", "-p", "no:cacheprovider",
               "tests", "-m", "not native and not held", "--test-profile", "ci", comparison, base,
               "--test-selection-output", str(packet / "selection.json"),
               "--test-execution-output", str(packet / "execution.json")]
    packet.mkdir()
    result = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=30,
                            env=dict(os.environ, PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", PYTEST_ADDOPTS=""))
    return result, json.loads((packet / "selection.json").read_text()), json.loads((packet / "execution.json").read_text())


def test_routine_ci_executes_changed_bounded_bytes_without_a_review_receipt(contributor, tmp_path):
    root, base = contributor
    adapter = root / "tests/test_adapter.py"
    adapter.write_text("def test_adapter(): pass\n")
    declare(root, "tests/test_adapter.py")
    adapter.write_text("def test_adapter(): assert False, 'changed bounded body ran'\n")
    (root / "tests/test_integration.py").write_text("def test_long_workflow(): pass\n")
    (root / "tests/conftest.py").write_text("import pytest\n")
    commit(root)
    result, selection, execution = run(root, base, tmp_path / "routine", comparison="--bounded-changes-since")
    assert result.returncode == 1 and "changed bounded body ran" in result.stdout
    assert selection["changed_tests"]["errors"] == []
    assert set(selection["selected_nodeids"]) == {"tests/test_core.py::test_core", "tests/test_adapter.py::test_adapter"}
    assert execution["executed"] == 2 and execution["failed"] == 1 and execution["changed_test_drift"] == []
    assert {row["path"] for row in selection["changed_tests"]["changes"]
            if row["disposition"] == "SEPARATE_PROFILE"} == {"tests/conftest.py", "tests/test_integration.py"}


def test_failing_new_bounded_adapter_test_blocks_actual_contributor_acceptance(contributor, tmp_path):
    root, base = contributor
    (root / "tests/test_adapter.py").write_text("def test_new_adapter(): assert False, 'actual new test body'\n")
    declare(root, "tests/test_adapter.py")
    commit(root)
    result, selection, execution = run(root, base, tmp_path / "packet")
    assert result.returncode == 1 and "actual new test body" in result.stdout
    assert "tests/test_adapter.py::test_new_adapter" in selection["selected_nodeids"]
    assert execution["collected"] == execution["selected"] == execution["executed"] == 2
    assert execution["failed"] == 1 and execution["passed"] == 1


@pytest.mark.parametrize("defect", ("missing", "stale", "empty", "unexplained-native"))
def test_added_or_changed_modules_cannot_silently_escape_execution(contributor, tmp_path, defect):
    root, base = contributor
    module = root / "tests/test_adapter.py"
    module.write_text("def test_new_adapter(): pass\n")
    if defect != "missing":
        declare(root, "tests/test_adapter.py")
    if defect == "stale":
        module.write_text("import pytest\n@pytest.mark.native\ndef test_new_adapter(): pass\n")
    elif defect == "empty":
        module.write_text("VALUE = 1\n")
        declare(root, "tests/test_adapter.py")
    elif defect == "unexplained-native":
        module.write_text("import pytest\n@pytest.mark.native\ndef test_new_adapter(): pass\n")
        declare(root, "tests/test_adapter.py")
    commit(root)
    result, selection, execution = run(root, base, tmp_path / "packet")
    assert result.returncode != 0 and selection["changed_tests"]["errors"]
    assert execution["executed"] == 0


def test_explicit_native_exclusion_remains_unverified_and_renames_are_reported(contributor, tmp_path):
    root, base = contributor
    old = root / "tests/test_adapter.py"
    old.write_text("import pytest\ndef test_portable(): pass\n@pytest.mark.native\ndef test_native(): raise AssertionError('no contact')\n")
    commit(root)
    base = git(root, "rev-parse", "HEAD")
    old.rename(root / "tests/test_renamed_adapter.py")
    declare(root, "tests/test_renamed_adapter.py", exclusions={"native": {
        "reason": "Requires the separately installed native fixture",
        "required_acceptance": "Selected native profile with genuine prerequisites"}})
    commit(root)
    result, selection, execution = run(root, base, tmp_path / "packet")
    assert result.returncode == 0, result.stdout + result.stderr
    row, = selection["changed_tests"]["changes"]
    assert row["original_path"] == "tests/test_adapter.py" and row["status"].startswith("R")
    assert row["excluded_cases"][0]["disposition"] == "UNVERIFIED"
    assert execution["collected"] == 3 and execution["executed"] == 2 and execution["deselected"] == 1
    assert execution["skipped"] == 0


def test_empty_change_selection_is_explicit_and_existing_ci_still_executes(contributor, tmp_path):
    root, base = contributor
    result, selection, execution = run(root, base, tmp_path / "packet")
    assert result.returncode == 0, result.stdout + result.stderr
    assert selection["changed_tests"]["changes"] == []
    assert execution["executed"] == execution["passed"] == 1


def test_larger_changed_check_requires_passing_exact_source_profile_evidence(contributor, tmp_path):
    root, base = contributor
    (root / "tests/test_adapter.py").write_text("def test_large(): raise AssertionError('do not launch in CI')\n")
    declare(root, "tests/test_adapter.py", policy="profile")
    commit(root)
    result, selection, execution = run(root, base, tmp_path / "packet")
    assert result.returncode != 0 and execution["executed"] == 0
    assert selection["changed_tests"]["missing_evidence_nodeids"] == ["tests/test_adapter.py::test_large"]


def test_unavailable_selected_prerequisite_is_a_failed_check_not_a_passing_skip(contributor, tmp_path):
    root, base = contributor
    (root / "tests/test_adapter.py").write_text("import pytest\ndef test_missing_input(): pytest.skip('required input absent')\n")
    declare(root, "tests/test_adapter.py")
    commit(root)
    result, _, execution = run(root, base, tmp_path / "packet")
    assert result.returncode != 0 and "Required release-profile check skipped" in result.stdout
    assert execution["skipped"] == execution["failed"] == 1
    assert execution["passed"] == 1


def test_explicit_shared_fixture_requires_all_portable_bodies_not_empty_success(contributor, tmp_path):
    root, _ = contributor
    path = root / "tests/test_shared_fixture.py"
    path.write_text("import pytest\n@pytest.fixture\ndef value(): return 1\n")
    base = commit(root)
    path.write_text("import pytest\n@pytest.fixture\ndef value(): return 2\n")
    declare(root, "tests/test_shared_fixture.py", policy="profile", role="shared-fixture")
    commit(root)
    result, selection, execution = run(root, base, tmp_path / "packet")
    assert result.returncode != 0 and execution["executed"] == 0
    changed = selection["changed_tests"]
    assert changed["missing_evidence_nodeids"] == ["tests/test_core.py::test_core"]
    assert changed["changes"][0]["disposition"] == "REQUIRES_PROFILE_EVIDENCE"
    assert not any("collected no test bodies" in error for error in changed["errors"])


@pytest.mark.parametrize("defect", ("removed-test", "bounded-helper", "empty-helper"))
def test_shared_fixture_role_cannot_hide_removed_tests_or_bypass_profile(contributor, tmp_path, defect):
    root, _ = contributor
    path = root / "tests/test_shared_fixture.py"
    fixture = "import pytest\n@pytest.fixture\ndef value(): return 1\n"
    path.write_text("def test_original(): pass\n" if defect == "removed-test" else fixture)
    base = commit(root)
    path.write_text("VALUE = 1\n" if defect == "empty-helper" else fixture + "CHANGED = True\n")
    declare(root, "tests/test_shared_fixture.py", policy="bounded" if defect == "bounded-helper" else "profile", role="shared-fixture")
    commit(root)
    result, selection, execution = run(root, base, tmp_path / "packet")
    assert result.returncode != 0 and execution["executed"] == 0
    errors = "; ".join(selection["changed_tests"]["errors"])
    expected = {"removed-test": "test bodies cannot be relabelled", "bounded-helper": "require profile evidence", "empty-helper": "must declare pytest fixtures"}
    assert expected[defect] in errors


@pytest.mark.parametrize("defect", (None, "foreign-source", "collection-only", "changed-log"))
def test_reused_partition_evidence_requires_exact_source_and_actual_test_bodies(contributor, tmp_path, defect):
    from scripts.release_portable_evidence import candidate_inventory, release_input_paths

    root, base = contributor
    (root / "tests/test_adapter.py").write_text("def test_new_adapter(): pass\n")
    declare(root, "tests/test_adapter.py")
    head = commit(root)
    packet = tmp_path / "packet"
    result, _, execution = run(root, base, packet)
    assert result.returncode == 0, result.stdout + result.stderr
    log = packet / "tests.log"
    log.write_text(result.stdout + result.stderr)
    if defect == "collection-only":
        execution["collection_only"] = True
        (packet / "execution.json").write_text(json.dumps(execution))

    def member(name):
        raw = (packet / name).read_bytes()
        return {"path": name, "size_bytes": len(raw), "sha256": sha256(raw).hexdigest()}

    selected = release_input_paths(root, revision="HEAD")
    log_member = member("tests.log")
    manifest = {"schema": "empirical-lawhood/release/check-manifest", "status": "PASSED", "profile": "ci",
        "source": {"commit": "0" * 40 if defect == "foreign-source" else head,
                   "selected_paths": list(selected), "selected_inventory": candidate_inventory(root, selected_paths=selected, revision=head, verify_selected=True)},
        "checks": [{"name": "tests", "exit_code": 0, "disposition": "PASSED", "command": result.args,
                    "log": log_member["path"], "size_bytes": log_member["size_bytes"], "sha256": log_member["sha256"]}],
        "test_selection": member("selection.json"), "test_execution": member("execution.json")}
    path = packet / "release-manifest.json"
    path.write_text(json.dumps(manifest))
    if defect == "changed-log":
        log.write_text("replacement log\n")
    if defect is None:
        receipts, missing = test_change_policy._profile_evidence(root, [path], {"tests/test_adapter.py::test_new_adapter"})
        assert len(receipts) == 1 and missing == []
    else:
        with pytest.raises(ValueError):
            test_change_policy._profile_evidence(root, [path], {"tests/test_adapter.py::test_new_adapter"})
