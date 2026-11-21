# SPDX-License-Identifier: MPL-2.0
"""Small PURE controls separating output allowances from actual storage."""

from dataclasses import replace
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from typer.testing import CliRunner

from empirical_lawhood.cli.app import app
from empirical_lawhood.storage.artifacts import ExternalRootUnavailable, FilesystemState, GuardedExternalRoot
from empirical_lawhood.storage.contracts.artifacts import ExternalRootContract
from empirical_lawhood.execution.output_reservations import output_reservation_operation
from tests.runtime_platform.test_recursive_compiler import compile_fixture


def test_advisory_reservations_preserve_exact_plan_and_task_limits():
    plan = compile_fixture().execution_plan
    original = plan.canonical_bytes()
    assert plan.minimum_free_bytes == 0
    with pytest.raises(RuntimeError, match="retained failure"):
        with output_reservation_operation() as record:
            assert plan.minimum_free_bytes == 0
            assert plan.canonical_bytes() == original
            assert [task.capability.requested_resources.output_bytes for task in plan.tasks] == [10_000, 10_000]
            assert record["plans"][plan.execution_plan_id] == {
                "task_count": 2, "declared_output_bytes": 20_000, "effective_plan_floor_bytes": 0}
            assert record['policy'] == 'ADVISORY_RESERVATIONS'
            raise RuntimeError("retained failure")
    assert plan.minimum_free_bytes == 0
    assert plan.canonical_bytes() == original


def test_storage_keeps_actual_mount_write_and_profile_floor_checks(tmp_path):
    plan = compile_fixture().execution_plan
    contract = ExternalRootContract("storage.control", "PURE storage control", str(tmp_path),
        str(tmp_path), "empirical-lawhood/testing/storage-mount", 1_000, None, None, ("ext4",))
    state = FilesystemState(canonical_root=str(tmp_path), active_mount=True, writable=True,
        free_bytes=1_500, path_is_symlink=False, mount_source="/dev/control", filesystem_type="ext4")
    inspector = SimpleNamespace(inspect=lambda _: state)
    root = GuardedExternalRoot(contract, inspector)
    assert root.verify(for_write=True, operation_minimum_free_bytes=plan.minimum_free_bytes) == tmp_path
    with output_reservation_operation():
        assert root.verify(for_write=True, operation_minimum_free_bytes=plan.minimum_free_bytes) == tmp_path
        state = replace(state, free_bytes=999)
        with pytest.raises(ExternalRootUnavailable, match="free-space floor"):
            root.verify(for_write=True)
        state = replace(state, free_bytes=30_000, active_mount=False)
        with pytest.raises(ExternalRootUnavailable, match="not active"):
            root.verify(for_write=True, operation_minimum_free_bytes=plan.minimum_free_bytes)
        state = replace(state, active_mount=True, writable=False)
        with pytest.raises(ExternalRootUnavailable, match="writ"):
            root.verify(for_write=True, operation_minimum_free_bytes=plan.minimum_free_bytes)


def test_cli_reports_advisory_reservations_without_overcommit_selection(tmp_path, monkeypatch):
    from empirical_lawhood.adapters.simulators.rc_ladder_response import native_quickstart
    plan = compile_fixture().execution_plan
    calls = []
    def compute(_):
        calls.append(plan.minimum_free_bytes)
        return {"control": "PURE", "new_native_contacts": 0}
    monkeypatch.setattr(native_quickstart, "check_native_model", compute)
    model = Path(__file__).resolve().parents[1] / "programmes/foundations/measurement-and-response/workflows/rc-ladder-response/model.json"
    command = [
        "campaign", "rc-ladder-native-check", "--config", str(model)]
    unretained = CliRunner().invoke(app, command)
    assert unretained.exit_code == 0 and calls == [0], unretained.output
    result = CliRunner().invoke(app, [*command, "--output-dir", str(tmp_path / "attempt")])
    assert result.exit_code == 0, result.output
    assert calls == [0, 0]
    record = json.loads((tmp_path / "attempt/invocation.json").read_bytes())["output_reservations"]
    assert "allow_overcommit" not in record
    assert record['storage_admission'] == 'OPERATOR_FLOOR_AND_ACTUAL_WRITES'
    assert record["plans"][plan.execution_plan_id]["declared_output_bytes"] == 20_000
    assert record["plans"][plan.execution_plan_id]["effective_plan_floor_bytes"] == 0
    assert plan.minimum_free_bytes == 0


def test_removed_overcommit_flag_refuses_before_command_entry():
    result = CliRunner().invoke(app, ["--allow-output-reservation-overcommit", "workflow", "list"])
    assert result.exit_code == 2
    assert "No such option" in result.stderr
    assert "--allow-output-reservation-overcommit" in result.stderr


def test_removed_overcommit_argument_is_not_accepted():
    with pytest.raises(TypeError, match="allow_overcommit"):
        with output_reservation_operation(allow_overcommit=True):
            pytest.fail("removed compatibility argument entered its operation")
