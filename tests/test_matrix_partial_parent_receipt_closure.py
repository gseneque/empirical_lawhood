# SPDX-License-Identifier: MPL-2.0
"""Shared receipt-closure controls on the disclosed five-task reference issue.

The source/approval doubles belong only to this software fixture. These checks
produce no Matrix qualification, real human act or native acquisition.
"""
from dataclasses import replace
from pathlib import Path

import pytest

from empirical_lawhood.api.recursive_qualified_parents import _collect_receipt_closure
from empirical_lawhood.infrastructure.recovery import ExternalRunRecoveryStore
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
from tests.runtime_platform.test_recursive_prospective_workflow import _public_issued_handoff_fixture, _run_public_handoff


def test_complete_and_partial_parent_read_share_exact_actual_input_lineage_and_task_census(tmp_path, monkeypatch):
    parts = _public_issued_handoff_fixture(tmp_path, monkeypatch)
    fixture = _run_public_handoff(tmp_path, issued_parts=parts)
    arguments = (fixture.package, fixture.execution_plan, fixture.plane, fixture.reveal,
        tuple(row.capability_key for row in fixture.package.registry.capabilities))
    complete = _collect_receipt_closure(*arguments)
    partial = _collect_receipt_closure(*arguments, allow_partial=True)
    assert complete.by_task == partial.by_task and len(complete.by_task) == 5
    assert all(row.lineage_parents for receipt in complete.by_task.values()
        for row in receipt.output_logical_artifacts)

    read_terminal = ExternalRunRecoveryStore.read_terminal
    original = complete.by_task["evaluate"]
    altered = replace(original, output_logical_artifacts=tuple(replace(row, lineage_parents=())
        for row in original.output_logical_artifacts))
    read_receipt = ExternalTaskReceiptStore.read_by_receipt_id
    read_manifest = fixture.plane.read_manifest
    changed = {row.logical_artifact_id: row for row in altered.output_logical_artifacts}
    def resealed_terminal(store, index):
        value = read_terminal(store, index)
        return replace(value, attempts=tuple(replace(row, receipt_sha256=altered.fingerprint())
            if row.receipt_id == original.receipt_id else row for row in value.attempts))
    def resealed_receipt(store, run_id, task_id, receipt_id):
        return altered if receipt_id == original.receipt_id else read_receipt(store, run_id, task_id, receipt_id)
    def resealed_manifest(relative, **kwargs):
        value = read_manifest(relative, **kwargs)
        logical = changed.get(value.logical.logical_artifact_id)
        return value if logical is None else replace(value, logical=logical)
    # A changed receipted lineage must also agree with publication membership
    # and the exact consumed inputs. Preserve every immutable fixture byte.
    with monkeypatch.context() as patch:
        patch.setattr(ExternalRunRecoveryStore, "read_terminal", resealed_terminal)
        patch.setattr(ExternalTaskReceiptStore, "read_by_receipt_id", resealed_receipt)
        patch.setattr(fixture.plane, "read_manifest", resealed_manifest)
        with pytest.raises((ValueError, PermissionError), match="publication|scientific input lineage"):
            _collect_receipt_closure(*arguments)

    def incomplete(store, index):
        value = read_terminal(store, index)
        omitted = value.completed_task_ids[-1]
        # Canonically valid smaller terminal; the immutable original execution
        # index still assigns five tasks and supplies the authoritative census.
        return replace(value, attempts=tuple(row for row in value.attempts if row.task_id != omitted),
            completed_task_ids=tuple(task for task in value.completed_task_ids if task != omitted))
    monkeypatch.setattr(ExternalRunRecoveryStore, "read_terminal", incomplete)
    with pytest.raises(ValueError, match="omits a retained attempt"):
        _collect_receipt_closure(*arguments, allow_partial=True)


def test_blocked_parent_keeps_unreached_tasks_and_refuses_hidden_attempts(tmp_path, monkeypatch):
    """A real scheduler terminal can stop before reaching the complete graph."""
    from hashlib import sha256
    from empirical_lawhood.api.results import RunCampaignRequest
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    from empirical_lawhood.runtime.recovery import RecoveryTerminalAttempt, RecoveryTerminalDisposition, RunRecoveryTerminalEvent
    from tests.test_recursive_refusal_report import _refusal

    parts = _public_issued_handoff_fixture(tmp_path, monkeypatch)
    control = _run_public_handoff(tmp_path, issued_parts=parts, prepare_only=True)
    executor = type(control.executor)
    execute = executor.execute_deadline_free
    entered = []

    def stop_after_one(self, runner, context, **kwargs):
        entered.append(context.task_id)
        if len(entered) > 1:
            raise _refusal(kwargs['prepared_contract'])
        return execute(self, runner, context, **kwargs)

    monkeypatch.setattr(executor, 'execute_deadline_free', stop_after_one)
    result = control.api.run_campaign(RunCampaignRequest(control.package_path, confirmed=True,
        reveal_authority_id=control.reveal.authority_id))
    assert not result.succeeded
    plane = control.service.artifact_plane
    root = Path(plane.root.contract.canonical_path)
    plan = control.service._load_status_execution_plan(control.package.run_plan_id)
    arguments = (control.package, plan, plane, control.reveal,
        tuple(row.capability_key for row in control.package.registry.capabilities))
    stopped = _collect_receipt_closure(*arguments, allow_partial=True)
    recovery = ExternalRunRecoveryStore(plane)
    assert recovery.read_terminal(stopped.recovery_index) is None
    # The reference issue permits another retry, so the service correctly keeps
    # its terminal open. Supply a disclosed terminal-selection double over the
    # actual reached journal rows; all index/event/receipt checks stay real.
    attempts = tuple(RecoveryTerminalAttempt(row.attempt_id, row.task_id, row.ordinal,
        RecoveryTerminalDisposition(row.disposition.value), row.reason_code, row.receipt_id, row.receipt_sha256)
        for row in sorted(stopped.operational_summaries.values(), key=lambda row: (row.task_id, row.ordinal)))
    terminal_selection = RunRecoveryTerminalEvent('terminal.disclosed-partial-parent',
        ObjectIdentity.from_record(stopped.recovery_index.recovery_index_id, stopped.recovery_index),
        control.package.run_plan_id, 'BLOCKED', attempts, tuple(sorted(stopped.by_task)), (),
        tuple(sorted(row.task_id for row in attempts if row.disposition.value == 'BLOCKED')))
    def selected_terminal(store, index):
        assert store.plane.root is plane.root and index == stopped.recovery_index
        return terminal_selection
    monkeypatch.setattr(ExternalRunRecoveryStore, 'read_terminal', selected_terminal)
    before = {path.relative_to(root).as_posix(): sha256(path.read_bytes()).hexdigest()
        for path in root.rglob('*') if path.is_file()}
    closure = _collect_receipt_closure(*arguments, allow_partial=True)
    terminal = ExternalRunRecoveryStore(plane).read_terminal(closure.recovery_index)
    assert terminal.operational_status == 'BLOCKED'
    assert set(closure.by_task) == {entered[0]} and len(entered) == 2
    assert {row.task_id for row in terminal.attempts} == set(entered)
    assert set(entered) < {task.task_id for task in plan.tasks}
    with pytest.raises(PermissionError, match='complete successful retained parent execution'):
        _collect_receipt_closure(*arguments)
    assert before == {path.relative_to(root).as_posix(): sha256(path.read_bytes()).hexdigest()
        for path in root.rglob('*') if path.is_file()}

    actual_terminal = ExternalRunRecoveryStore.read_terminal
    def hide_completed_attempt(store, index):
        current = actual_terminal(store, index)
        return replace(current, completed_task_ids=(),
            attempts=tuple(row for row in current.attempts if row.task_id != entered[0]))
    monkeypatch.setattr(ExternalRunRecoveryStore, 'read_terminal', hide_completed_attempt)
    with pytest.raises(ValueError, match='omits a retained attempt'):
        _collect_receipt_closure(*arguments, allow_partial=True)
