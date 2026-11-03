# SPDX-License-Identifier: MPL-2.0
"""The candidate owner launches one complete suite and retains its evidence."""

import json
from pathlib import Path
from types import SimpleNamespace
import sys

import pytest

from scripts import release_candidate_check as gate


@pytest.mark.parametrize("suite_exit", [0, 1, None])
def test_candidate_gate_invokes_suite_once_and_preserves_precommit_attribution(tmp_path, monkeypatch, suite_exit):
    root = tmp_path / "source"
    root.mkdir()
    (root / "uv.lock").write_bytes(b"locked fixture")
    (root / ".coveragerc").write_bytes(b"selected owner config")
    monkeypatch.setenv("PYTEST_ADDOPTS", "--collect-only")
    monkeypatch.setenv("COVERAGE_RCFILE", "/unselected/config")
    for name in gate.THREAD_ENVIRONMENT:
        monkeypatch.setenv(name, "23")
    packet = tmp_path / "evidence"
    monkeypatch.setattr(gate, "ROOT", root)
    monkeypatch.setattr(gate, "candidate_inventory", lambda r, **kwargs: [{"path": "uv.lock", "mode": "100644", "sha256": "1"*64, "size_bytes": 14}])
    monkeypatch.setattr(gate, "release_input_paths", lambda r: ("uv.lock",))
    monkeypatch.setattr(gate, "release_source_disclosure", lambda *args: {"observed_checkout_clean": False})
    def output(command, **kwargs):
        if "--others" in command:
            return b""
        return "tree-or-parent-fixture\n"
    monkeypatch.setattr(gate.subprocess, "check_output", output)
    commands = []
    def process(command, **kwargs):
        commands.append(command)
        if "pytest" in command:
            assert "PYTEST_ADDOPTS" not in kwargs["env"]
            assert kwargs["env"]["COVERAGE_RCFILE"] == str(root / ".coveragerc")
            assert all(kwargs["env"][name] == "1" for name in gate.THREAD_ENVIRONMENT)
            assert kwargs["env"]["TMPDIR"] == str(packet / "temporary-files")
            running = json.loads((packet / "precommit-portable-evidence.json").read_bytes())
            assert running["status"] == "RUNNING" and running["full_suite_invocations"] == 1
            assert running["checks"][-1]["command"] == command
            assert running["checks"][-1]["disposition"] == "RUNNING"
            assert running["checks"][-1]["exit_code"] is None
        stream = kwargs.get("stdout")
        if stream is not None:
            stream.write(b"actual mocked boundary output\n")
        if "pytest" in command and suite_exit is None:
            raise KeyboardInterrupt("interrupted boundary")
        if "json" in command and "coverage" in command:
            Path(command[-1]).write_text('{"files": {}}')
        return SimpleNamespace(returncode=suite_exit if "pytest" in command else 0)
    monkeypatch.setattr(gate.subprocess, "run", process)
    monkeypatch.setattr(sys, "argv", ["release_candidate_check.py", "--output-dir", str(packet)])
    if suite_exit is None:
        with pytest.raises(KeyboardInterrupt, match="interrupted boundary"):
            gate.main()
    elif suite_exit:
        with pytest.raises(RuntimeError, match="tests failed"):
            gate.main()
    else:
        gate.main()
    suites = [command for command in commands if "pytest" in command]
    assert len(suites) == 1
    assert suites[0][-3:] == ["tests", "-m", "not native and not held"]
    assert "--fail-on-skip" in suites[0]
    assert "tmp_path_retention_policy=all" in suites[0]
    assert suites[0][suites[0].index("--basetemp") + 1] == str(packet / "test-artifacts")
    retained = json.loads((packet / "precommit-portable-evidence.json").read_bytes())
    assert retained["status"] == ("INTERRUPTED" if suite_exit is None else "FAILED" if suite_exit else "PASSED")
    assert retained["full_suite_invocations"] == 1
    assert retained["test_environment_policy"] == gate.portable_test_environment_policy(packet, root)
    expected_command = ["uv", "run", "--no-sync", "python", "-m", "coverage", "run", "-m", "pytest",
                        "-q", "-ra", "--fail-on-skip", *gate.retained_test_options(packet),
                        "tests", "-m", "not native and not held"]
    assert suites[0] == expected_command
    assert "not a clean-commit" in retained["attribution"]
    check = next(item for item in retained["checks"] if item["name"] == "tests")
    assert check["exit_code"] == suite_exit and (packet / check["log"]).read_bytes() == b"actual mocked boundary output\n"
    if suite_exit != 0:
        assert retained["coverage"] is None
        assert retained["checks"][-2]["name"] == "coverage-configuration"
        assert all(item["disposition"] == "PASSED" for item in retained["checks"][:-1])
    if suite_exit is None:
        assert check["disposition"] == "INTERRUPTED"
        assert retained["failure_type"] == "KeyboardInterrupt"


@pytest.mark.parametrize("generator", ("integration_examples", "matrix_experiment_examples"))
def test_stale_shipped_examples_stop_before_the_full_suite(tmp_path, monkeypatch, generator):
    root = tmp_path / "source"
    root.mkdir()
    (root / "uv.lock").write_bytes(b"locked fixture")
    (root / ".coveragerc").write_bytes(b"selected owner config")
    packet = tmp_path / "evidence"
    monkeypatch.setattr(gate, "ROOT", root)
    inventory = [{"path": "uv.lock", "mode": "100644", "sha256": "1" * 64, "size_bytes": 14}]
    monkeypatch.setattr(gate, "candidate_inventory", lambda r, **kwargs: inventory)
    monkeypatch.setattr(gate, "release_input_paths", lambda r: ("uv.lock",))
    monkeypatch.setattr(gate, "release_source_disclosure", lambda *args: {"observed_checkout_clean": False})
    monkeypatch.setattr(gate.subprocess, "check_output", lambda command, **kwargs:
                        b"" if "--others" in command else "unchanged-candidate\n")
    commands = []

    def process(command, **kwargs):
        commands.append(command)
        stale = f"scripts/generate_{generator}.py" in command
        if stream := kwargs.get("stdout"):
            stream.write(b"historical examples differ\n" if stale else b"checked\n")
        return SimpleNamespace(returncode=1 if stale else 0)

    monkeypatch.setattr(gate.subprocess, "run", process)
    monkeypatch.setattr(sys, "argv", ["release_candidate_check.py", "--output-dir", str(packet)])
    with pytest.raises(RuntimeError, match=f"generated-{generator} failed"):
        gate.main()
    assert not any("pytest" in command for command in commands)
    retained = json.loads((packet / "precommit-portable-evidence.json").read_bytes())
    assert retained["status"] == "FAILED" and retained["full_suite_invocations"] == 0
    assert retained["coverage"] is None
    failed = retained["checks"][-1]
    assert failed["name"] == f"generated-{generator}" and failed["disposition"] == "FAILED"
    assert failed["exit_code"] == 1
    assert (packet / failed["log"]).read_bytes() == b"historical examples differ\n"
    assert (root / "uv.lock").read_bytes() == b"locked fixture"
