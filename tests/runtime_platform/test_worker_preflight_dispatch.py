# SPDX-License-Identifier: MPL-2.0
"""A refused prerequisite stops dispatch without losing admitted custody."""
from dataclasses import replace
import hashlib
import threading

import pytest

from empirical_lawhood.infrastructure.execution import (
    DirectTaskExecutor, ExecutionResourceCapacity, WorkerPreflightError, operational_failure_diagnostic,
)
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.infrastructure.recovery import RunRecoveryError
from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest
from empirical_lawhood.runtime.execution import TaskAttemptDisposition
from empirical_lawhood.runtime.prepared_native_invocation import (
    PreparedInvocationContract, WorkerPreflightMismatch, WorkerPreflightResult,
)
from tests.runtime_platform.test_execution_scheduler import _runtime
from tests.runtime_platform.conftest import protocol_fixture as protocol_fixture


class RefusingFirstWorker:
    """Synthetic dispatch refusal; no worker, native work or scientific output."""

    def __init__(self, first_wave):
        self.first_wave = first_wave
        self.ready = threading.Barrier(len(first_wave))
        self.refusal = None

    def execute(self, runner, context, *, timeout_seconds):
        if context.task_id in self.first_wave:
            self.ready.wait(timeout=20)
        if context.task_id == self.first_wave[0]:
            self.refusal = WorkerPreflightResult(
                ObjectIdentity("prepared." + context.attempt_id, PreparedInvocationContract.SCHEMA,
                    PreparedInvocationContract.VERSION, "a" * 64), None, None,
                (WorkerPreflightMismatch("disclosed.missing-input", "PRIVATE-CHILD-MESSAGE"),),
            )
            raise WorkerPreflightError(self.refusal)
        return DirectTaskExecutor().execute(runner, context, timeout_seconds=timeout_seconds)


@pytest.mark.parametrize("workers", (1, 4))
def test_preflight_refusal_stops_new_dispatch_and_drains_receipts(
    tmp_path, protocol_fixture, caplog, workers,
):
    template = next(task for task in protocol_fixture.execution_plan.tasks if task.task_id == "prepare")
    run_id = protocol_fixture.run_plan.run_plan_id
    tasks = tuple(replace(template, task_id="preflight-refusal." + str(index).zfill(4),
        maximum_attempts=1, dependency_task_ids=(), resource_lock_ids=(),
        outputs=tuple(replace(output, output_id=output.output_id + "." + str(index),
            logical_artifact_id=output.logical_artifact_id + "." + str(index),
            relative_path=f"runs/{run_id}/outputs/preflight-refusal.{index}/{output.output_id}.json")
            for output in template.outputs)) for index in range(24))
    plan = replace(protocol_fixture.execution_plan, tasks=tasks)
    fixture = replace(protocol_fixture, execution_plan=plan)
    first_wave = tuple(task.task_id for task in tasks[:workers])
    executor = RefusingFirstWorker(first_wave)
    scheduler, repository, plane, receipts, _runners = _runtime(
        tmp_path, fixture, executor=executor, maximum_parallel_tasks=workers,
        parallel_resource_capacity=(ExecutionResourceCapacity(workers, 4_000_000, 0, True, True, False)
            if workers > 1 else None),
    )
    try:
        result = scheduler.execute(run_id, plan)
        assert result.status is OperationalStatus.BLOCKED
        assert result.blocked_task_ids == first_wave[:1]
        assert result.completed_task_ids == first_wave[1:]
        attempts = repository.attempts(run_id)
        assert {attempt.task_id for attempt in attempts} == set(first_wave)
        assert all(attempt.disposition is not TaskAttemptDisposition.RUNNING for attempt in attempts)
        assert len(result.receipts) == workers - 1
        for receipt in result.receipts:
            assert receipts.read(run_id, receipt.task_id, receipt.attempt_id) == receipt
        assert "disclosed.missing-input" in caplog.text
        assert "PRIVATE-CHILD-MESSAGE" not in caplog.text
        assert "diagnostic_sha256=" in caplog.text
        failure = operational_failure_diagnostic(WorkerPreflightError(executor.refusal))
        assert failure.sanitized_message == (
            "worker preflight refused the prepared invocation; inspect its guarded diagnostic")
        assert "PRIVATE-CHILD-MESSAGE" not in failure.canonical_bytes().decode()
        refused_attempt, = (value for value in attempts if value.task_id == first_wave[0])
        token = hashlib.sha256(refused_attempt.attempt_id.encode()).hexdigest()
        relative = f"runs/{run_id}/recovery/{scheduler.recovery_index.wave_id}/preflight/{token}.json"
        raw = scheduler.recovery_store._read_payload(relative,
            expected_schema=WorkerPreflightResult.SCHEMA,
            maximum_bytes=plane.custody_limits.recovery_event_bytes)
        assert raw == executor.refusal.canonical_bytes()
        assert decode_canonical_bytes(raw, WorkerPreflightResult,
            maximum_bytes=plane.custody_limits.recovery_event_bytes) == executor.refusal
        manifest = decode_artifact_manifest(plane.root.resolve(relative + ".manifest.json",
            for_write=False).read_bytes())
        assert manifest.logical.content_sha256 == executor.refusal.fingerprint()
        assert manifest.logical.outcome_access == template.capability.requested_outcome_access
        assert manifest.logical.lineage_parents[0].identity == ObjectIdentity.from_record(
            scheduler.recovery_index.recovery_index_id, scheduler.recovery_index)
        # Guarded diagnostics cannot be attributed to a different attempt or
        # grow beyond the operator-selected existing recovery allocation.
        with pytest.raises(RunRecoveryError, match="actual refused attempt"):
            scheduler.recovery_store.record_worker_preflight(scheduler.recovery_index,
                task_id=first_wave[-1], attempt_id=refused_attempt.attempt_id + ".other",
                result=executor.refusal, visibility_ceiling=manifest.logical.visibility_ceiling,
                outcome_access=manifest.logical.outcome_access)
        plane.custody_limits = replace(plane.custody_limits, recovery_event_bytes=len(raw) - 1)
        with pytest.raises(RunRecoveryError, match="selected recovery allowance"):
            scheduler.recovery_store.record_worker_preflight(scheduler.recovery_index,
                task_id=first_wave[0], attempt_id=refused_attempt.attempt_id,
                result=executor.refusal, visibility_ceiling=manifest.logical.visibility_ceiling,
                outcome_access=manifest.logical.outcome_access)
        # The remaining assigned tasks stay unentered; no fake refusal or
        # completion records are manufactured for the rest of the population.
        assert not {task.task_id for task in tasks[workers:]} & {attempt.task_id for attempt in attempts}
    finally:
        repository.engine.dispose()
