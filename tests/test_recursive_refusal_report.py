# SPDX-License-Identifier: MPL-2.0
"""Public refusal retains genuine PURE receipts and no invented scientific result.

The custom PURE executors disclose prerequisite refusal and ordinary failure.
All authoring, scheduling, terminal custody and reads use the public owners.
No native worker, scientific authority or qualification is exercised.
"""
from pathlib import Path
from threading import Barrier, Event

import pytest

from empirical_lawhood.adapters.methods.rubisco_historical.recursive_translation import historical_recursive_draft
from empirical_lawhood.api import numerical_provenance as provenance_owner
from empirical_lawhood.api import recursive_authoring as author
from empirical_lawhood.api import recursive_execution as execution
from empirical_lawhood.api import experiment_scientific_read
from empirical_lawhood.infrastructure import execution as scheduler_owner
from empirical_lawhood.infrastructure.execution import DirectTaskExecutor, ExecutionResourceCapacity, WorkerPreflightError
from empirical_lawhood.runtime.prepared_native_invocation import PreparedInvocationContract, WorkerPreflightMismatch, WorkerPreflightResult
from tests.test_recursive_public_service import _plane
from tests.test_rubisco_historical_recursive import _inputs

ROOT = Path(__file__).resolve().parents[1]


def _authored_case(tmp_path, monkeypatch):
    plane = _plane(tmp_path / "selected")
    model, slices = _inputs()
    bindings = []
    for record in slices:
        path = tmp_path / (record.slice_id + ".json")
        path.write_bytes(record.canonical_bytes())
        bindings.append(("external." + record.slice_id, path))
    directory = Path(plane.root.contract.canonical_path) / "authored"
    source = author.implementation_binding(ROOT)
    provenance = provenance_owner.capture_numerical_provenance(project_root=ROOT)
    monkeypatch.setattr(author, "implementation_binding", lambda root, **_kwargs: source)
    monkeypatch.setattr(execution, "implementation_binding", lambda root, **_kwargs: source)
    monkeypatch.setattr(provenance_owner, "capture_numerical_provenance", lambda **kwargs: provenance)
    draft = historical_recursive_draft(model, slices)
    author.author_recursive_wave(draft=draft, project_root=ROOT, artifact_writer=plane,
        output_dir=directory, input_bindings=tuple(bindings))
    return plane, directory, draft


def _refusal(contract):
    assert type(contract) is PreparedInvocationContract and not contract.native_effect
    return WorkerPreflightError(WorkerPreflightResult(contract.identity, None, None,
        (WorkerPreflightMismatch("disclosed.prerequisite", "disclosed software refusal"),)))


@pytest.mark.parametrize("completed_before_refusal", (0, 1))
def test_public_run_returns_authenticated_refusal_without_scientific_completion(
        tmp_path, monkeypatch, completed_before_refusal):
    plane, directory, _draft = _authored_case(tmp_path, monkeypatch)
    entered = []

    class RefusingExecutor(DirectTaskExecutor):
        """Disclosed PURE executor; no process/resource enforcement is claimed."""
        def __init__(self, *, scratch_root):
            assert scratch_root is plane.root

        def execute(self, runner, context, *, timeout_seconds, **prepared_controls):
            entered.append(context.task_id)
            if len(entered) > completed_before_refusal:
                raise _refusal(prepared_controls["prepared_contract"])
            return super().execute(runner, context, timeout_seconds=timeout_seconds)

    def forbidden_completion(**_kwargs):
        pytest.fail("refused execution attempted scientific completion")

    monkeypatch.setattr(scheduler_owner, "LocalProcessExecutor", RefusingExecutor)
    monkeypatch.setattr(experiment_scientific_read, "complete_prepared_development_science", forbidden_completion)
    report = execution.run_recursive_wave(directory=directory, project_root=ROOT,
        artifact_writer=plane, terminal_product_format="references")
    assert report["status"] == "PARTIAL" and report["operational_terminal"] == "ABSENT"
    assert report["terminal_product_format"] == "compact"
    assert report["scientific_completion"] == "NOT_ASSESSED_BY_COMPACT_CUSTODY"
    assert report["qualification"] == "NOT_ESTABLISHED" and "scientific_result" not in report
    assert report["native_contact"] == "none" and report["new_native_contact_count"] == 0
    assert report["task_count"] == len(report["task_census"]) == 6
    assert len(entered) == completed_before_refusal + 1
    rows = {row["task_id"]: row for row in report["task_census"]}
    assert rows[entered[-1]]["operational_status"] == "BLOCKED"
    for task_id in entered[:-1]:
        assert rows[task_id]["operational_status"] == "SUCCEEDED"
    missing = set(rows) - set(entered)
    assert len(missing) == 6 - len(entered)
    assert all(rows[task_id] == {"task_id": task_id,
        "operational_status": "NO_COMPLETION_RECEIPT", "reason_code": "ENTRY_OR_PROCESS_STATE_NOT_INFERRED"}
        for task_id in missing)
    assert {row["task_id"] for row in report["operational_census"]} == set(entered)
    assert {row["task_id"] for row in report["retained_product_index"]} == set(entered[:-1])

    # Strict scientific/full reads retain the complete assigned-census guard.
    with pytest.raises(ValueError, match="lacks its complete operational terminal"):
        execution.read_recursive_wave(directory=directory, artifact_writer=plane)
    before = {path.relative_to(plane.root.contract.canonical_path).as_posix(): path.read_bytes()
        for path in Path(plane.root.contract.canonical_path).rglob("*") if path.is_file()}
    partial = execution.read_recursive_wave(directory=directory, artifact_writer=plane,
        terminal_product_format="compact", allow_partial=True)
    assert partial == report
    assert before == {path.relative_to(plane.root.contract.canonical_path).as_posix(): path.read_bytes()
        for path in Path(plane.root.contract.canonical_path).rglob("*") if path.is_file()}


def test_public_failed_terminal_keeps_incomplete_assigned_census_read_only(tmp_path, monkeypatch):
    plane, directory, draft = _authored_case(tmp_path, monkeypatch)
    first_wave = tuple(sorted(operation.node_id for operation in draft.operations
        if operation.node_id.endswith(".fit")))
    assert len(first_wave) == 2
    ready, refusal_observed = Barrier(2), Event()
    entered, drained = [], []
    stop_dispatch = scheduler_owner.LocalScheduler._stop_refused_worker_dispatch

    def observe_refusal(scheduler, error):
        # Observe the unchanged owner's stop; do not inject scheduler state.
        stop_dispatch(scheduler, error)
        if isinstance(error, WorkerPreflightError):
            refusal_observed.set()

    monkeypatch.setattr(scheduler_owner.LocalScheduler, "_stop_refused_worker_dispatch", observe_refusal)

    class MixedFailureExecutor(DirectTaskExecutor):
        """Two admitted PURE attempts fail; no isolated worker is simulated."""
        def __init__(self, *, scratch_root):
            assert scratch_root is plane.root

        def execute(self, runner, context, *, timeout_seconds, **prepared_controls):
            assert context.task_id in first_wave
            contract = prepared_controls["prepared_contract"]
            assert type(contract) is PreparedInvocationContract and not contract.native_effect
            assert contract.execution_task_record.task_id == context.task_id
            entered.append(context.task_id)
            ready.wait(timeout=20)
            try:
                if context.task_id == first_wave[0]:
                    raise _refusal(contract)
                assert refusal_observed.wait(timeout=20)
                # Explicit software failure at the ordinary PURE runner seam.
                # Neither a scientific product nor completion receipt is made.
                raise ValueError("disclosed PURE runner failure")
            finally:
                drained.append(context.task_id)

    def forbidden_completion(**_kwargs):
        pytest.fail("failed execution attempted scientific completion")

    monkeypatch.setattr(scheduler_owner, "LocalProcessExecutor", MixedFailureExecutor)
    monkeypatch.setattr(experiment_scientific_read, "complete_prepared_development_science", forbidden_completion)
    # Both existing independent fits retain their declared 1-core/1-GiB budget.
    capacity = ExecutionResourceCapacity(2, 4 * 1024**3, 0, False, False, False)
    report = execution.run_recursive_wave(directory=directory, project_root=ROOT,
        artifact_writer=plane, terminal_product_format="references",
        maximum_parallel_tasks=2, parallel_resource_capacity=capacity)
    assert set(entered) == set(drained) == set(first_wave) and len(entered) == len(drained) == 2
    assert report["status"] == "FAILED" and report["operational_terminal"] == "AUTHENTICATED"
    assert report["terminal_product_format"] == "compact"
    assert report["scientific_completion"] == "NOT_ASSESSED_BY_COMPACT_CUSTODY"
    assert report["qualification"] == "NOT_ESTABLISHED" and "scientific_result" not in report
    assert report["native_contact"] == "none" and report["new_native_contact_count"] == 0
    assert report["task_count"] == len(report["task_census"]) == 6
    rows = {row["task_id"]: row for row in report["task_census"]}
    assert rows[first_wave[0]]["operational_status"] == "BLOCKED"
    assert rows[first_wave[1]]["operational_status"] == "FAILED"
    missing = set(rows) - set(first_wave)
    assert len(missing) == 4
    assert all(rows[task_id] == {"task_id": task_id,
        "operational_status": "NO_COMPLETION_RECEIPT", "reason_code": "ENTRY_OR_PROCESS_STATE_NOT_INFERRED"}
        for task_id in missing)
    census = {row["task_id"]: row for row in report["operational_census"]}
    assert set(census) == set(first_wave)
    assert census[first_wave[0]]["operational_status"] == "BLOCKED"
    assert census[first_wave[1]]["operational_status"] == "FAILED"
    assert all(row["receipt_id"] is None and row["receipt_sha256"] is None
        and row["recovery_event_status"] == "AUTHENTICATED" for row in census.values())
    assert report["retained_product_index"] == () and report["terminal_products"] == {}

    with pytest.raises(ValueError, match="omits a task in its assigned census"):
        execution.read_recursive_wave(directory=directory, artifact_writer=plane)
    before = {path.relative_to(plane.root.contract.canonical_path).as_posix(): path.read_bytes()
        for path in Path(plane.root.contract.canonical_path).rglob("*") if path.is_file()}
    partial = execution.read_recursive_wave(directory=directory, artifact_writer=plane,
        terminal_product_format="compact", allow_partial=True)
    assert partial == report
    assert before == {path.relative_to(plane.root.contract.canonical_path).as_posix(): path.read_bytes()
        for path in Path(plane.root.contract.canonical_path).rglob("*") if path.is_file()}
