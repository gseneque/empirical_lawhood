# SPDX-License-Identifier: MPL-2.0
"""Bounded census recovery without workers or scientific products."""
from types import SimpleNamespace

import pytest

from empirical_lawhood.infrastructure.recursive_custody import _operational_census
from empirical_lawhood.runtime.recovery import OperationalFailureDiagnostic
from empirical_lawhood.runtime.execution import OperationalFailureClass


class Event:
    def __init__(self, status, reason, failure=None, ordinal=None):
        self.task_id = "task.one"
        self.attempt_id = f"attempt.{ordinal}" if ordinal is not None else None
        self.attempt_ordinal = ordinal
        self.disposition = SimpleNamespace(value=status)
        self.reason_codes = (reason,)
        self.failure = failure

    def to_document(self):
        return {"disposition": self.disposition.value, "reason_codes": self.reason_codes,
                "failure": self.failure.to_document() if self.failure else None}


def _fixture():
    candidates = tuple(SimpleNamespace(attempt_id=f"attempt.{n}", ordinal=n, event_relative_path=f"events/{n}") for n in (1, 2))
    binding = SimpleNamespace(task_id="task.one", attempts=candidates, nonattempt_event_relative_path="events/nonattempt")
    index = SimpleNamespace(tasks=(binding,), run_id="run.one")
    rows = tuple(SimpleNamespace(task_id="task.one", attempt_id=f"attempt.{n}", ordinal=n,
        disposition=SimpleNamespace(value="FAILED"), reason_code="failure.temporary", receipt_id=None,
        receipt_sha256=None) for n in (1, 2))
    failure_class = next(value for value in OperationalFailureClass if value.retryable)
    failure = OperationalFailureDiagnostic.create(failure_class, sanitized_exception_type="RuntimeError", sanitized_message="temporary")
    events = {f"events/{n}": Event("FAILED", "failure.temporary", failure, ordinal=n) for n in (1, 2)}
    recovery = SimpleNamespace(read_event=lambda _, path: events.get(path))
    store = SimpleNamespace(plane=object(), read=lambda *args: None)
    plan = SimpleNamespace(tasks=(SimpleNamespace(task_id="task.one"),))
    terminal = SimpleNamespace(attempts=rows)
    return recovery, store, plan, index, terminal, events


def test_failed_retries_preserve_full_attempt_census_diagnostics_and_unknown_actuals():
    recovery, store, plan, index, terminal, _ = _fixture()
    rows, events, receipts = _operational_census(recovery=recovery, store=store, plan=plan, index=index, terminal=terminal)
    assert len(rows) == len(events) == 2
    assert receipts == {}
    assert rows[0]["recovery_event"]["failure"]["value"]["scientific_evidence"] is False
    assert all(row["actual_cpu_seconds"] is None and row["actual_wall_seconds"] is None and row["actual_peak_rss_bytes"] is None for row in rows)


@pytest.mark.parametrize("tamper", ["missing_event", "omitted_attempt", "wrong_reason", "unknown_attempt"])
def test_incomplete_or_substituted_attempt_closure_refuses(tamper):
    recovery, store, plan, index, terminal, events = _fixture()
    if tamper == "missing_event":
        del events["events/1"]
    elif tamper == "omitted_attempt":
        terminal.attempts = terminal.attempts[1:]
    elif tamper == "wrong_reason":
        events["events/1"].reason_codes = ("changed.reason",)
    else:
        terminal.attempts[0].attempt_id = "unknown.attempt"
    with pytest.raises(ValueError):
        _operational_census(recovery=recovery, store=store, plan=plan, index=index, terminal=terminal)


def test_failed_attempt_then_success_keeps_failure_while_latest_can_succeed(monkeypatch):
    from empirical_lawhood.infrastructure import recursive_custody
    from empirical_lawhood.runtime.recovery import TaskRecoveryEvent

    recovery, store, plan, index, terminal, events = _fixture()
    receipt = SimpleNamespace(receipt_id="receipt.success", fingerprint=lambda: "a"*64)
    terminal.attempts[1].disposition.value = "SUCCEEDED"
    terminal.attempts[1].reason_code = None
    terminal.attempts[1].receipt_id = receipt.receipt_id
    terminal.attempts[1].receipt_sha256 = receipt.fingerprint()
    success = Event("SUCCEEDED", "unused", ordinal=2)
    events["events/2"] = success
    store.read = lambda run, task, attempt: receipt if attempt == "attempt.2" else None
    monkeypatch.setattr(TaskRecoveryEvent, "from_receipt", lambda *args: success)
    monkeypatch.setattr(recursive_custody.ExternalRunRecoveryStore, "_validate_receipt_static", lambda *args: None)
    rows, _, receipts = _operational_census(recovery=recovery, store=store, plan=plan, index=index, terminal=terminal)
    assert [row["operational_status"] for row in rows] == ["FAILED", "SUCCEEDED"]
    assert tuple(receipts) == ("attempt.2",)
    assert rows[0]["recovery_event"]["failure"]


def test_nonattempt_dependency_block_retains_event_without_receipt_or_product():
    recovery, store, plan, index, terminal, events = _fixture()
    events.clear()
    events["events/nonattempt"] = Event("NOT_ATTEMPTED", "dependency.failed")
    row = terminal.attempts[0]
    row.attempt_id = "run.one.task.one.block-001"
    row.disposition.value = "BLOCKED"
    row.reason_code = "dependency.failed"
    terminal.attempts = (row,)
    rows, recovered, receipts = _operational_census(recovery=recovery, store=store, plan=plan, index=index, terminal=terminal)
    assert rows[0]["operational_status"] == "BLOCKED"
    assert rows[0]["recovery_event"]["disposition"] == "NOT_ATTEMPTED"
    assert tuple(recovered) == ("run.one.task.one.block-001",)
    assert receipts == {}


def test_typed_terminal_failure_ordinal_swap_refuses():
    from dataclasses import replace
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    from empirical_lawhood.runtime.recovery import (
        DevelopmentRunRecoveryIndex, DevelopmentRunRecoveryTerminalEvent, RecoveryAttemptCandidate,
        RecoveryTerminalAttempt, RecoveryTerminalDisposition, TaskRecoveryDisposition, TaskRecoveryEvent,
    )

    recovery, store, plan, index, _, _ = _fixture()
    identity = ObjectIdentity("index.one", DevelopmentRunRecoveryIndex.SCHEMA, "1.0.0", "a"*64)
    index.tasks[0].attempts = tuple(RecoveryAttemptCandidate(f"attempt.{n}", n, f"receipts/{n}", f"events/{n}",
        "empirical-lawhood/runtime/canonical-task-receipt", TaskRecoveryEvent.SCHEMA) for n in (1, 2))
    diagnostic = OperationalFailureDiagnostic.create(next(value for value in OperationalFailureClass if value.retryable),
        sanitized_exception_type="RuntimeError", sanitized_message="temporary")
    events = {f"events/{n}": TaskRecoveryEvent(f"event.{n}", identity, "run.one", "task.one", f"attempt.{n}", n,
        TaskRecoveryDisposition.FAILED, None, None, None, None, (), ("failure.temporary",), diagnostic) for n in (1, 2)}
    recovery.read_event = lambda _, path: events.get(path)
    rows = tuple(RecoveryTerminalAttempt(f"attempt.{n}", "task.one", n, RecoveryTerminalDisposition.FAILED,
        "failure.temporary", None, None) for n in (1, 2))
    terminal = DevelopmentRunRecoveryTerminalEvent("terminal.one", identity, "run.one", "FAILED", rows, (), ("task.one",), ())
    assert len(_operational_census(recovery=recovery, store=store, plan=plan, index=index, terminal=terminal)[0]) == 2
    # Remains a canonical, contiguous terminal, but assigns each exact attempt
    # the other's order. This previously changed which outcome was latest.
    swapped = replace(terminal, attempts=(replace(rows[1], ordinal=1), replace(rows[0], ordinal=2)))
    with pytest.raises(ValueError, match="identity or ordinal"):
        _operational_census(recovery=recovery, store=store, plan=plan, index=index, terminal=swapped)
    events["events/1"] = replace(events["events/1"], attempt_ordinal=2)
    with pytest.raises(ValueError, match="identity or ordinal"):
        _operational_census(recovery=recovery, store=store, plan=plan, index=index, terminal=terminal)


def _retryable_block_fixture():
    recovery, store, plan, index, terminal, events = _fixture()
    del events["events/2"]
    candidate = terminal.attempts[0]
    candidate.ordinal = 3
    blocks = tuple(SimpleNamespace(task_id="task.one", attempt_id=f"run.one.task.one.block-{n:03d}",
        ordinal=n, disposition=SimpleNamespace(value="BLOCKED"), reason_code="resource-lock-unavailable",
        receipt_id=None, receipt_sha256=None) for n in (1, 2))
    terminal.attempts = (*blocks, candidate)
    return recovery, store, plan, index, terminal, events


def test_terminal_primary_retryable_blocks_do_not_consume_executable_candidates():
    recovery, store, plan, index, terminal, _ = _retryable_block_fixture()
    rows, events, receipts = _operational_census(
        recovery=recovery, store=store, plan=plan, index=index, terminal=terminal)
    assert [row["ordinal"] for row in rows] == [1, 2, 3]
    assert [row["recovery_event_status"] for row in rows] == [
        "MISSING_TERMINAL_PRIMARY_NONATTEMPT", "MISSING_TERMINAL_PRIMARY_NONATTEMPT", "AUTHENTICATED"]
    assert all(row["recovery_event"] is None for row in rows[:2])
    assert rows[-1]["recovery_event"]["disposition"] == "FAILED"
    assert tuple(events) == ("attempt.1",)
    assert receipts == {}


@pytest.mark.parametrize("tamper", (
    "foreign_task", "unindexed_task", "foreign_run", "arbitrary_id", "wrong_block_number", "noncontiguous_ordinal",
    "duplicate_attempt", "nonblocked_state", "unknown_reason", "durable_without_event",
    "receipt_id", "receipt_hash", "off_index_receipt", "candidate_ordinal", "event_ordinal",
))
def test_terminal_primary_nonattempt_substitutions_refuse(tamper):
    recovery, store, plan, index, terminal, events = _retryable_block_fixture()
    row = terminal.attempts[0]
    if tamper == "foreign_task":
        row.task_id = "task.foreign"
    elif tamper == "unindexed_task":
        row.task_id = "task.unindexed"
        row.attempt_id = "run.one.task.unindexed.block-001"
        plan.tasks = (*plan.tasks, SimpleNamespace(task_id=row.task_id))
    elif tamper == "foreign_run":
        row.attempt_id = "run.foreign.task.one.block-001"
    elif tamper == "arbitrary_id":
        row.attempt_id = "arbitrary.nonattempt"
    elif tamper == "wrong_block_number":
        row.attempt_id = "run.one.task.one.block-009"
    elif tamper == "noncontiguous_ordinal":
        row.ordinal = 4
        row.attempt_id = "run.one.task.one.block-004"
    elif tamper == "duplicate_attempt":
        terminal.attempts[1].attempt_id = row.attempt_id
    elif tamper == "nonblocked_state":
        row.disposition.value = "FAILED"
    elif tamper == "unknown_reason":
        row.reason_code = "invented-retryable-reason"
    elif tamper == "durable_without_event":
        row.reason_code = "dependency-failed"
    elif tamper == "receipt_id":
        row.receipt_id = "receipt.foreign"
    elif tamper == "receipt_hash":
        row.receipt_sha256 = "a" * 64
    elif tamper == "off_index_receipt":
        store.read = lambda run, task, attempt: object() if attempt == row.attempt_id else None
    elif tamper == "candidate_ordinal":
        terminal.attempts[-1].ordinal = 1
    else:
        events["events/1"].attempt_ordinal = 3
    with pytest.raises(ValueError):
        _operational_census(recovery=recovery, store=store, plan=plan, index=index, terminal=terminal)


def test_stock_resource_block_resume_terminal_census_is_read_only(tmp_path, monkeypatch):
    """Actual platform custody with deterministic software runners, no Native."""
    from hashlib import sha256
    from tests.runtime_platform.conftest import build_protocol_fixture
    from tests.runtime_platform.test_execution_scheduler import _runtime
    from empirical_lawhood.infrastructure.execution import LocalScheduler, ResourceLockManager
    from empirical_lawhood.kernel.status import OperationalStatus

    protocol = build_protocol_fixture()
    locks = ResourceLockManager()
    locks.reserve_for_test("reference-simulator")
    scheduler, repository, plane, store, runners = _runtime(tmp_path, protocol, lock_manager=locks)
    run_id = protocol.run_plan.run_plan_id
    try:
        assert scheduler.execute(run_id, protocol.execution_plan).status is OperationalStatus.BLOCKED
        assert scheduler.execute(run_id, protocol.execution_plan).status is OperationalStatus.BLOCKED
        locks.release(("reference-simulator",))
        assert scheduler.execute(run_id, protocol.execution_plan).status is OperationalStatus.SUCCEEDED
        terminal = scheduler.recovery_store.read_terminal(scheduler.recovery_index)
        assert terminal is not None
        before = {str(p.relative_to(tmp_path)): sha256(p.read_bytes()).hexdigest()
                  for p in tmp_path.rglob("*") if p.is_file()}
        calls = tuple(len(runner.contexts) for runner in runners)

        def blocked(*args, **kwargs):
            raise AssertionError("cold operational census entered a worker")

        monkeypatch.setattr(LocalScheduler, "execute", blocked)
        rows, events, receipts = _operational_census(recovery=scheduler.recovery_store, store=store,
            plan=protocol.execution_plan, index=scheduler.recovery_index, terminal=terminal)
        history = [row for row in rows if row["task_id"] == "prepare"]
        assert [row["ordinal"] for row in history] == [1, 2, 3]
        assert [row["operational_status"] for row in history] == ["BLOCKED", "BLOCKED", "SUCCEEDED"]
        assert all(row["recovery_event"] is None for row in history[:2])
        assert history[-1]["recovery_event"]["value"]["attempt_ordinal"] == 1
        assert len(receipts) == len(protocol.execution_plan.tasks)
        assert all(event is not None for event in events.values())
        assert calls == tuple(len(runner.contexts) for runner in runners)
        assert before == {str(p.relative_to(tmp_path)): sha256(p.read_bytes()).hexdigest()
                          for p in tmp_path.rglob("*") if p.is_file()}
    finally:
        repository.engine.dispose()
