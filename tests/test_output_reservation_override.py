# SPDX-License-Identifier: MPL-2.0
"""Small PURE controls separating output allowances from actual storage."""

from dataclasses import replace
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from typer.testing import CliRunner

from empirical_lawhood.cli.app import app
from empirical_lawhood.infrastructure.artifacts import (
    ExternalRootUnavailable, FilesystemState, GuardedExternalRoot,
)
from empirical_lawhood.runtime.artifacts import ExternalRootContract
from empirical_lawhood.runtime.output_reservations import output_reservation_operation
from tests.runtime_platform.test_recursive_compiler import compile_fixture


@pytest.mark.parametrize('legacy_option', (False, True))
def test_advisory_reservations_preserve_exact_plan_and_task_limits(legacy_option):
    plan = compile_fixture().execution_plan
    original = plan.canonical_bytes()
    assert plan.minimum_free_bytes == 0
    with pytest.raises(RuntimeError, match="retained failure"):
        with output_reservation_operation(allow_overcommit=legacy_option) as record:
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
    with output_reservation_operation(allow_overcommit=True):
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


@pytest.mark.parametrize('legacy_option', (False, True))
def test_cli_default_and_legacy_option_report_advisory_reservations(tmp_path, monkeypatch, legacy_option):
    from empirical_lawhood.adapters.simulators.rc_ladder_response import native_quickstart
    plan = compile_fixture().execution_plan
    calls = []
    def compute(_):
        calls.append(plan.minimum_free_bytes)
        return {"control": "PURE", "new_native_contacts": 0}
    monkeypatch.setattr(native_quickstart, "check_native_model", compute)
    model = Path(__file__).resolve().parents[1] / "programmes/foundations/measurement-and-response/workflows/rc-ladder-response/model.json"
    command = (["--allow-output-reservation-overcommit"] if legacy_option else []) + [
        "campaign", "rc-ladder-native-check", "--config", str(model)]
    unretained = CliRunner().invoke(app, command)
    assert unretained.exit_code == 0 and calls == [0], unretained.output
    result = CliRunner().invoke(app, [*command, "--output-dir", str(tmp_path / "attempt")])
    assert result.exit_code == 0, result.output
    assert calls == [0, 0]
    record = json.loads((tmp_path / "attempt/invocation.json").read_bytes())["output_reservations"]
    assert record["allow_overcommit"] is legacy_option
    assert record['storage_admission'] == 'OPERATOR_FLOOR_AND_ACTUAL_WRITES'
    assert record["plans"][plan.execution_plan_id]["declared_output_bytes"] == 20_000
    assert record["plans"][plan.execution_plan_id]["effective_plan_floor_bytes"] == 0
    assert plan.minimum_free_bytes == 0
