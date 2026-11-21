# SPDX-License-Identifier: MPL-2.0
"""Make changed-test execution choices explicit without widening every CI run."""

from __future__ import annotations

import ast
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
import subprocess


def _require_shared_fixture(root: Path, name: str, original: str, base: str) -> None:
    """An explicit helper can require the full suite, never erase test bodies."""
    sources = [("current", (root / name).read_bytes())]
    previous = subprocess.run(["git", "show", f"{base}:{original}"], cwd=root,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if previous.returncode == 0:
        sources.append(("previous", previous.stdout))
    for label, payload in sources:
        tree = ast.parse(payload)
        nodes = tuple(ast.walk(tree))
        if any(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
               and (node.name.startswith("test_") or node.name.startswith("Test")) for node in nodes):
            raise ValueError(f"{name}: {label} test bodies cannot be relabelled as shared fixtures")
        fixtures = []
        for node in nodes:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for decorator in node.decorator_list:
                marker = decorator.func if isinstance(decorator, ast.Call) else decorator
                if (isinstance(marker, ast.Attribute) and marker.attr == "fixture"
                        and isinstance(marker.value, ast.Name) and marker.value.id == "pytest"):
                    fixtures.append(node.name)
        if not fixtures:
            raise ValueError(f"{name}: {label} shared-fixture module must declare pytest fixtures")


def changed_test_files(root: Path, base: str) -> tuple[str, list[dict]]:
    resolved = subprocess.check_output(
        ["git", "rev-parse", "--verify", "--end-of-options", base + "^{commit}"], cwd=root, text=True,
    ).strip()
    rows = iter(subprocess.check_output(
        ["git", "diff", "--name-status", "-z", "--find-renames", resolved, "HEAD", "--", "tests"], cwd=root,
    ).decode().rstrip("\0").split("\0"))
    changes = []
    for status in rows:
        if not status:
            continue
        original = next(rows)
        name = next(rows) if status.startswith(("R", "C")) else original
        path = PurePosixPath(name)
        if path.suffix != ".py" or not (path.name.startswith("test_") or path.name == "conftest.py"):
            continue
        changes.append({"status": status, "path": name,
                        "original_path": original if original != name else None})
    return resolved, changes


def _profile_evidence(root, paths, required_nodeids):
    """Authenticate existing complete-portable or selected-partition evidence."""
    if not paths:
        return [], sorted(required_nodeids)
    if __package__:
        from .release_portable_evidence import (
            SCHEMA, _bound_member, authenticate_portable_evidence, candidate_inventory, release_input_paths,
        )
    else:
        from release_portable_evidence import (
            SCHEMA, _bound_member, authenticate_portable_evidence, candidate_inventory, release_input_paths,
        )
    covered, receipts = set(), []
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    for path in paths:
        path = Path(path).resolve(strict=True)
        if path.stat().st_size > 16 * 1024**2:
            raise ValueError("changed-test evidence exceeds its bounded manifest size")
        payload = path.read_bytes()
        record = json.loads(payload)
        if record.get("schema") == SCHEMA:
            authenticate_portable_evidence(path, root)
            covered.update(required_nodeids)
        else:
            if (record.get("schema") != "empirical-lawhood/release/check-manifest"
                    or record.get("status") != "PASSED" or record.get("profile") not in ("ci", "integration", "scale")
                    or record.get("source", {}).get("commit") != head):
                raise ValueError("changed-test evidence is not a passing exact-source partition packet")
            selected_paths = tuple(record["source"]["selected_paths"])
            if (selected_paths != release_input_paths(root, revision="HEAD")
                    or candidate_inventory(root, selected_paths=selected_paths, revision=head, verify_selected=True)
                    != record["source"]["selected_inventory"]):
                raise ValueError("changed-test evidence differs from the current complete source selection")
            tests = [row for row in record["checks"] if row["name"] == "tests"]
            if len(tests) != 1 or tests[0]["exit_code"] != 0 or tests[0]["disposition"] != "PASSED":
                raise ValueError("changed-test evidence lacks a completed passing test invocation")
            check = tests[0]
            command = check["command"]
            if ("--fail-on-skip" not in command or "--collect-only" in command or "-k" in command
                    or "--test-profile" not in command or command[command.index("--test-profile") + 1] != record["profile"]):
                raise ValueError("changed-test evidence changes its required execution selector")
            _bound_member(path.parent, {"path": check["log"], "size_bytes": check["size_bytes"], "sha256": check["sha256"]})
            census = json.loads(_bound_member(path.parent, record["test_selection"]).read_bytes())
            if census["profile"] != record["profile"]:
                raise ValueError("changed-test evidence changes its profile census")
            execution = json.loads(_bound_member(path.parent, record["test_execution"]).read_bytes())
            nodes = set(census["selected_nodeids"])
            if (execution["collection_only"] or execution["exit_code"] != 0
                    or execution["executed"] != len(nodes) or execution["passed"] != len(nodes)
                    or execution["failed"] or execution["skipped"] or execution["collection_failures"]
                    or execution["changed_test_drift"] or set(execution["cases"]) != nodes
                    or any(not row["executed"] or row["failed"] or row["skipped"] for row in execution["cases"].values())):
                raise ValueError("changed-test evidence does not establish every selected test body's execution")
            covered.update(census["selected_nodeids"])
        receipts.append({"path": str(path), "sha256": sha256(payload).hexdigest()})
    missing = sorted(set(required_nodeids) - covered)
    return receipts, missing


def changed_test_selection(root, base, items, eligible_nodeids, profile_for, ci_files, *,
                           evidence_paths=(), audit=True):
    """Return bounded extra cases and a complete changed-module disposition census."""
    root = Path(root)
    resolved, changes = changed_test_files(root, base)
    path = root / "scripts/test_change_decisions.json"
    document = json.loads(path.read_bytes())
    if document.get("schema") != "empirical-lawhood/tests/change-decisions-v1":
        raise ValueError("changed-test declarations have an unsupported schema")
    decisions = document["modules"]
    if not audit:
        bounded = set()
        for row in changes:
            name = row["path"]
            if row["status"] == "D":
                row["disposition"] = "DELETED"
                continue
            profile = profile_for(name)
            row["profile"] = profile
            if name in ci_files or (profile != "scale" and decisions.get(name, {}).get("policy") == "bounded"):
                bounded.add(name)
                row["sha256"] = sha256((root / name).read_bytes()).hexdigest()
                row["disposition"] = "EXECUTE_BOUNDED"
            else:
                row["disposition"] = "SEPARATE_PROFILE"
        extra = {node for node in eligible_nodeids if node.split("::", 1)[0] in bounded}
        return extra, {"base_commit": resolved, "changes": changes, "errors": [],
            "scope": "Routine bounded CI. Other profiles can be executed independently."}
    by_module = {}
    for nodeid, markers in items:
        by_module.setdefault(nodeid.split("::", 1)[0], []).append((nodeid, markers))
    eligible = set(eligible_nodeids)
    extras, need_evidence, failures = set(), set(), []
    for row in changes:
        name = row["path"]
        if row["status"] == "D":
            row.update(disposition="DELETED", collected_cases=0)
            continue
        source = root / name
        checksum = sha256(source.read_bytes()).hexdigest()
        row["sha256"] = checksum
        if name in ci_files:
            decision = decisions.get(name, {"profile": "ci", "policy": "bounded", "sha256": checksum,
                                           "reason": "Required bounded CI module", "exclusions": {}})
        else:
            decision = decisions.get(name)
        if decision is None or decision.get("sha256") != checksum:
            row["disposition"] = "MISSING_OR_STALE_DECISION"
            failures.append(f"{name}: explicit current-byte test profile decision required")
            continue
        profile = profile_for(name)
        if (decision.get("profile") != profile or decision.get("policy") not in ("bounded", "profile")
                or not decision.get("reason") or type(decision.get("exclusions")) is not dict
                or decision.get("role", "test-module") not in ("test-module", "shared-fixture")):
            failures.append(f"{name}: invalid profile, execution policy or exclusion declaration")
            continue
        if profile == "scale" and decision["policy"] == "bounded":
            failures.append(f"{name}: scale cases require their explicit profile evidence")
            continue
        row.update(profile=profile, policy=decision["policy"], reason=decision["reason"])
        cases = by_module.get(name, [])
        row["collected_cases"] = len(cases)
        row["eligible_cases"] = sum(node in eligible for node, _ in cases)
        row["excluded_cases"] = []
        if decision.get("role") == "shared-fixture":
            if decision["policy"] != "profile" or cases:
                failures.append(f"{name}: shared fixtures require profile evidence and no collected test bodies")
                continue
            try:
                _require_shared_fixture(root, name, row.get("original_path") or name, resolved)
            except (SyntaxError, ValueError) as error:
                failures.append(str(error))
                continue
        for node, markers in cases:
            for marker in sorted(set(markers) & {"native", "held"}):
                exclusion = decision["exclusions"].get(marker)
                if (type(exclusion) is not dict or not exclusion.get("reason")
                        or not exclusion.get("required_acceptance")):
                    failures.append(f"{node}: {marker} exclusion needs a reason and remaining acceptance")
                row["excluded_cases"].append({"nodeid": node, "marker": marker,
                                               "disposition": "UNVERIFIED", "requirement": exclusion})
        selected = {node for node, _ in cases if node in eligible}
        if not cases:
            # Conftest changes can affect every fixture and marker; a complete
            # portable packet is required, never an empty passing selection.
            if (PurePosixPath(name).name == "conftest.py" or decision.get("role") == "shared-fixture") and decision["policy"] == "profile":
                need_evidence.update(eligible)
                row["disposition"] = "REQUIRES_PROFILE_EVIDENCE"
                row["role"] = decision.get("role", "conftest")
            else:
                failures.append(f"{name}: changed test module collected no test bodies")
            continue
        if decision["policy"] == "bounded":
            extras.update(selected)
            row["disposition"] = "EXECUTE_BOUNDED" if selected else "ONLY_EXPLICIT_UNVERIFIED_EXCLUSIONS"
        else:
            need_evidence.update(selected)
            row["disposition"] = "REQUIRES_PROFILE_EVIDENCE" if selected else "ONLY_EXPLICIT_UNVERIFIED_EXCLUSIONS"
    receipts, missing = _profile_evidence(root, evidence_paths, need_evidence) if need_evidence or evidence_paths else ([], [])
    if missing:
        failures.append(f"{len(missing)} changed portable cases require exact-source passing profile evidence")
    for row in changes:
        if row.get("disposition") == "REQUIRES_PROFILE_EVIDENCE" and not missing:
            row["disposition"] = "ACCEPTED_PROFILE_EVIDENCE"
    return extras, {"base_commit": resolved, "changes": changes, "evidence": receipts,
                    "missing_evidence_nodeids": missing, "errors": failures,
                    "scope": "Execution decisions and software evidence; explicit native/held exclusions remain unverified."}
