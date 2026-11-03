# SPDX-License-Identifier: MPL-2.0
"""Public custody repair with disclosed software effects, never native science.

The fixture interrupts real scheduler bookkeeping after a canonical receipt has
been committed. Its native contact/subwork records describe an inline disclosed
callback and literal bytes, not acquisition, qualification or live-run evidence.
"""

from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from time import time

import pytest
from sqlalchemy import delete, select, update

from empirical_lawhood.api import recursive_authoring
from empirical_lawhood.api.results import CampaignStatusRequest, ResumeCampaignRequest, RunCampaignRequest
from empirical_lawhood.infrastructure.execution import DirectTaskExecutor, InjectedSchedulerCrash, LocalScheduler
from empirical_lawhood.infrastructure.execution_resource_envelopes import ExternalExecutionResourceEnvelopeStore
from empirical_lawhood.infrastructure.native_subwork import ExternalNativeSubworkStore
from empirical_lawhood.infrastructure.recovery import ExternalRunRecoveryStore
from empirical_lawhood.infrastructure.sql import SQLiteOperationalRepository, create_catalog_engine, upgrade_catalog
from empirical_lawhood.infrastructure.sql.schema import lease, run_event, task_attempt, workflow_run
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
from empirical_lawhood.runtime.execution_envelope import (
    ExecutionResourceEnvelopeState, ProgressHeartbeat, ProgressLivenessContract,
    RunExecutionResourceEnvelopeMachine,
)
from empirical_lawhood.runtime.prepared_native_invocation import PreparedNativeWork
from empirical_lawhood.runtime.recovery import TaskRecoveryEvent
from empirical_lawhood.runtime.execution import TaskBlockReason
from empirical_lawhood.kernel.provenance import ObjectIdentity
from tests.execution_support import ENFORCING_TEST_EXECUTOR_CAPABILITY
from tests.runtime_platform import test_recursive_prospective_workflow as fixtures
from tests.test_issued_worker_preparation import _binding
from tests.test_reconcile_failed_history import _census, _seed_native_subwork


@pytest.fixture
def late_history(tmp_path, monkeypatch, request):
    original_catalog = getattr(request, "param", None) == "original-catalog"
    original = fixtures.prospective_fixture

    def single_attempt(**options):
        compiled, authoring, context = original(**options)
        draft = replace(compiled.draft, operations=tuple(replace(row, maximum_attempts=1)
            for row in compiled.draft.operations))
        return replace(compiled, draft=draft), authoring, context

    monkeypatch.setattr(fixtures, "prospective_fixture", single_attempt)
    parts = list(fixtures._public_issued_handoff_fixture(tmp_path, monkeypatch))
    package = parts[5]
    resources = package.execution_resource_envelope_spec
    cells = tuple(replace(row, physical_execution_cost=1, retry_token_cost=1,
        native_simulator_launch=True, progress_liveness=ProgressLivenessContract(
            "liveness.software.late-prepare", ProgressHeartbeat.SCHEMA,
            "disclosed-software-operation", Decimal(30), True, True))
        if row.task_id == "prepare" else row for row in resources.task_cells)
    resources = replace(resources, task_cells=cells, allowlisted_resource_stop_reason_codes=(),
        child_token_limits=tuple(replace(row, physical_execution_token_limit=sum(
            cell.physical_execution_cost for cell in cells if cell.child_id == row.child_id))
            for row in resources.child_token_limits))
    package = replace(package, execution_resource_envelope_spec=resources)
    parts[5] = package
    control = fixtures._run_public_handoff(tmp_path, issued_parts=tuple(parts), prepare_only=True)
    service, plane = control.service, parts[3]
    original_engine_factory = service.engine_factory
    monkeypatch.setattr(service, "_check_identity", lambda *_args, **_options: None)
    monkeypatch.setattr(recursive_authoring, "implementation_binding", lambda _root: _binding(package.implementation_commit))
    resolve = service._resolve_campaign_provider

    def prepare_native(*, runner, context, expected_parent):
        cell = resources.cell_for_task(context.task_id)
        return PreparedNativeWork(expected_parent, (cell.physical_independent_unit_id,),
            ("disclosed.software.late-prepare",))

    class NativeProvider:
        def __init__(self, delegate):
            self.delegate = delegate

        def __getattr__(self, name):
            return getattr(self.delegate, name)

        def worker_preparations(self, registry, execution_plan=None):
            keys = {task.capability.capability_key for task in execution_plan.tasks if task.task_id == "prepare"}
            return tuple(replace(row, native_effect=True, native_work_preparer=prepare_native)
                if row.selection.capability_key in keys else row
                for row in self.delegate.worker_preparations(registry, execution_plan))

        def runners(self, registry, source_records=()):
            runners = self.delegate.runners(registry, source_records)
            keys = {step.capability_key for step in package.protocol.steps if step.step_id == "prepare"}
            for runner in runners:
                if runner.manifest.capability_key in keys:
                    runner.execute_with_progress = lambda context, progress, selected=runner: selected.execute(context)
            return runners

    def provider(*arguments, **options):
        resolved = resolve(*arguments, **options)
        return replace(resolved, provider=NativeProvider(resolved.provider))

    monkeypatch.setattr(service, "_resolve_campaign_provider", provider)
    selected = _seed_native_subwork(monkeypatch)

    class InlineExecutor:
        enforcement_capability = ENFORCING_TEST_EXECUTOR_CAPABILITY

        def __init__(self):
            self.calls = []

        def execute_deadline_free(self, runner, context, *, prepared_contract=None, native_entry=None, **_options):
            self.calls.append((context.task_id, context.attempt_id))
            if native_entry is not None:
                native_entry()
            if context.task_id == "develop-a":
                raise OSError("disclosed pre-terminal PURE failure")
            if prepared_contract is not None:
                context = replace(context, prepared_invocation=prepared_contract)
            return DirectTaskExecutor().execute(runner, context, timeout_seconds=60)

    executor = InlineExecutor()
    service.executor = executor
    record = ExternalRunRecoveryStore.record_receipt
    finalize = LocalScheduler._finalize_envelope_receipt
    stop = LocalScheduler._stop_failed_envelope_task
    complete = SQLiteOperationalRepository.complete_attempt

    def omit_catalog_completion(self, attempt_id):
        # Disclosed interruption after this exact accepted receipt, before its
        # original SQL row finishes. No state is rewound or new attempt made.
        if original_catalog and ("prepare", attempt_id) in executor.calls:
            return
        return complete(self, attempt_id)

    def omit_event(self, index, receipt):
        if receipt.task_id != "prepare":
            return record(self, index, receipt)

    def omit_resource_completion(self, task_id, *arguments, **options):
        if task_id != "prepare":
            return finalize(self, task_id, *arguments, **options)

    def interrupt(self, task_id, **options):
        if task_id != "develop-a":
            return stop(self, task_id, **options)
        candidate = self.recovery_index.task("develop-b").attempts[0]
        self.execution_resource_envelope_coordinator.reserve(
            envelope_id=self.execution_resource_envelope_id,
            event_id="software.reserved-without-launch", occurred_at_utc=self.execution_envelope_event_clock.now_utc(),
            cell_id=resources.cell_for_task("develop-b").cell_id, attempt_id=candidate.attempt_id)
        raise InjectedSchedulerCrash("disclosed interruption with late receipt and reservation")

    with monkeypatch.context() as interruption:
        interruption.setattr(ExternalRunRecoveryStore, "record_receipt", omit_event)
        interruption.setattr(LocalScheduler, "_finalize_envelope_receipt", omit_resource_completion)
        interruption.setattr(LocalScheduler, "_stop_failed_envelope_task", interrupt)
        if original_catalog:
            interruption.setattr(SQLiteOperationalRepository, "complete_attempt", omit_catalog_completion)
        result = control.api.run_campaign(RunCampaignRequest(control.package_path, confirmed=True,
            reveal_authority_id=control.reveal.authority_id))
    assert not result.succeeded
    plan, index, store = service._load_status_index(package.run_plan_id)
    assert store.read_terminal(index) is None
    receipts = ExternalTaskReceiptStore(plane)
    candidate = index.task("prepare").attempts[0]
    receipt = receipts.read(index.run_id, "prepare", candidate.attempt_id)
    assert receipt is not None and store.read_event(index, candidate.event_relative_path) is None
    journal = ExternalExecutionResourceEnvelopeStore(plane.root)
    envelope = journal.load("run-resource-envelope." + index.run_id)
    assert envelope.cell(resources.cell_for_task("prepare").cell_id).state is ExecutionResourceEnvelopeState.LAUNCHED
    assert envelope.cell(resources.cell_for_task("develop-b").cell_id).state is ExecutionResourceEnvelopeState.RESERVED, (
        result.reason_codes, result.errors)
    assert [task for task, _ in executor.calls] == ["prepare", "develop-a"]
    private_catalog = tmp_path / "private-reconciled.sqlite3"

    def engine_factory():
        engine = create_catalog_engine("sqlite+pysqlite:///" + str(private_catalog))
        upgrade_catalog(engine)
        return engine

    if original_catalog:
        # Real SQLite metadata setup represents elapsed lease time; it does not
        # alter the authentic RUNNING row, receipt, attempt ID or resource state.
        engine = original_engine_factory()
        try:
            with engine.begin() as connection:
                selected_pk = connection.execute(select(task_attempt.c.pk).where(
                    task_attempt.c.attempt_id == candidate.attempt_id)).scalar_one()
                connection.execute(update(lease).where(lease.c.task_attempt_pk == selected_pk)
                    .values(expires_epoch_seconds=1))
        finally:
            engine.dispose()
        service.engine_factory = original_engine_factory
    else:
        service.engine_factory = engine_factory

    def forbidden(*_args, **_kwargs):
        pytest.fail("custody reconciliation entered compilation, provider, scheduler or worker")

    monkeypatch.setattr(control.api, "_compile_package", forbidden)
    monkeypatch.setattr(control.api, "_conditional_execution_records", forbidden)
    monkeypatch.setattr(service, "execute", forbidden)
    monkeypatch.setattr(service, "_resolve_campaign_provider", forbidden)
    monkeypatch.setattr(LocalScheduler, "__init__", forbidden)
    request = ResumeCampaignRequest(index.run_id, confirmed=True, reconcile_only=True,
        reveal_authority_id=control.reveal.authority_id)
    return SimpleNamespace(control=control, plane=plane, root=plane.root.contract.canonical_path,
        plan=plan, index=index, store=store, resources=resources, receipt=receipt,
        candidate=candidate, journal=journal, envelope=envelope, executor=executor,
        private_catalog=private_catalog, request=request, native=selected,
        original_engine_factory=original_engine_factory)


def test_public_late_native_receipt_closes_once_and_reservation_stays_pending(late_history):
    case = late_history
    before = _census(case.plane.root.verify(for_write=False))
    calls = tuple(case.executor.calls)
    result = case.control.api.resume_campaign(case.request)
    assert result.succeeded, (result.reason_codes, result.errors)
    summary = result.payload
    assert summary.operational_status == "FAILED" and summary.assigned_task_count == 5
    assert summary.completed_task_ids == ("prepare",) and summary.failed_task_ids == ("develop-a",)
    assert set(summary.pending_task_ids) == {"develop-b", "freeze", "evaluate"}
    assert summary.closure_only and summary.worker_entries == 0
    assert case.store.read_event(case.index, case.candidate.event_relative_path) == TaskRecoveryEvent.from_receipt(case.index, case.receipt)
    updated = case.journal.load(case.envelope.envelope_id)
    assert updated.events[:len(case.envelope.events)] == case.envelope.events
    assert len(updated.events) == len(case.envelope.events) + 3
    reserved_id = case.resources.cell_for_task("develop-b").cell_id
    assert updated.cell(reserved_id) == case.envelope.cell(reserved_id)
    assert updated.child_token_states == case.envelope.child_token_states
    binding = case.index.task("develop-b")
    assert case.store.read_event(case.index, binding.attempts[0].event_relative_path) is None
    assert case.store.read_event(case.index, binding.nonattempt_event_relative_path) is None
    after = _census(case.plane.root.verify(for_write=False))
    journal_paths = {case.journal._relative_path(case.envelope.envelope_id, suffix) for suffix in ("head", "journal")}
    assert all(after[path] == value for path, value in before.items() if path not in journal_paths)
    case.private_catalog.unlink()
    repeated = case.control.api.resume_campaign(case.request)
    assert repeated.succeeded and repeated.payload == summary
    assert _census(case.plane.root.verify(for_write=False)) == after
    assert tuple(case.executor.calls) == calls


@pytest.mark.parametrize("target", ("product", "native-completion", "event", "launched-without-receipt"))
def test_bad_late_custody_refuses_before_any_repair(late_history, target):
    case = late_history
    if target == "product":
        case.plane.root.resolve(case.receipt.output_materializations[0].relative_path, for_write=False).write_bytes(b"changed")
    elif target == "native-completion":
        store, _, definition = case.native[0]
        path = case.plane.root.resolve(store._root(definition) + "/completion.json", for_write=False)
        path.unlink()
    elif target == "event":
        event = replace(TaskRecoveryEvent.from_receipt(case.index, case.receipt), receipt_sha256="9" * 64)
        case.store.append_event(case.index, event, receipt=case.receipt)
    else:
        candidate = case.index.task("develop-b").attempts[0]
        updated = RunExecutionResourceEnvelopeMachine.launch(case.envelope,
            event_id="software.unproven-launch", occurred_at_utc=case.envelope.events[-1].occurred_at_utc,
            cell_id=case.resources.cell_for_task("develop-b").cell_id, attempt_id=candidate.attempt_id)
        case.journal.compare_and_append(expected=case.envelope, updated=updated)
    before = _census(case.plane.root.verify(for_write=False))
    result = case.control.api.resume_campaign(case.request)
    assert not result.succeeded
    assert case.store.read_terminal(case.index) is None
    assert _census(case.plane.root.verify(for_write=False)) == before
    assert [task for task, _ in case.executor.calls] == ["prepare", "develop-a"]


@pytest.mark.parametrize("mutation", ("output", "namespace", "resource"))
def test_final_preflight_detects_late_mutation_before_repairs(late_history, monkeypatch, mutation):
    case = late_history
    inspect = ExternalNativeSubworkStore.inspect
    calls = {}
    changed = []

    def mutate(self, definition):
        result = inspect(self, definition)
        calls[definition.subwork_id] = calls.get(definition.subwork_id, 0) + 1
        if not changed and calls[definition.subwork_id] == 2:
            if mutation == "output":
                case.plane.root.resolve(case.receipt.output_materializations[0].relative_path, for_write=False).write_bytes(b"late change")
            elif mutation == "namespace":
                path = case.plane.root.resolve(f"runs/{case.index.run_id}/native-subwork/software.orphan", for_write=True)
                path.mkdir()
            else:
                candidate = case.index.task("freeze").attempts[0]
                updated = RunExecutionResourceEnvelopeMachine.reserve(case.envelope,
                    event_id="software.late-reservation", occurred_at_utc=case.envelope.events[-1].occurred_at_utc,
                    cell_id=case.resources.cell_for_task("freeze").cell_id, attempt_id=candidate.attempt_id)
                case.journal.compare_and_append(expected=case.envelope, updated=updated)
            changed.append(_census(case.plane.root.verify(for_write=False)))
        return result

    monkeypatch.setattr(ExternalNativeSubworkStore, "inspect", mutate)
    result = case.control.api.resume_campaign(case.request)
    assert changed and not result.succeeded
    assert case.store.read_terminal(case.index) is None
    assert case.store.read_event(case.index, case.candidate.event_relative_path) is None
    assert _census(case.plane.root.verify(for_write=False)) == changed[0]


def test_custom_physical_verifier_is_refused_instead_of_lost_in_scope(late_history, monkeypatch):
    case = late_history
    calls = []

    def deny(materialization):
        calls.append(materialization)
        raise AssertionError("custom verifier must never be silently replaced")

    monkeypatch.setattr(case.plane, "verify", deny)
    before = _census(case.plane.root.verify(for_write=False))
    result = case.control.api.resume_campaign(case.request)
    assert not result.succeeded
    assert not calls  # Explicit stock-policy refusal precedes the new scope.
    assert any("stock custody hooks" in error.message for error in result.errors)
    assert case.store.read_terminal(case.index) is None
    assert _census(case.plane.root.verify(for_write=False)) == before


@pytest.mark.parametrize("point", ("resource-append", "final-native-inspection"))
def test_new_reserved_candidate_event_during_effects_cannot_enter_terminal(late_history, monkeypatch, point):
    case = late_history
    append = ExternalExecutionResourceEnvelopeStore.compare_and_append
    changed = []

    def insert_event():
        if not changed:
            failed = case.index.task("develop-a").attempts[0]
            failure = case.store.read_event(case.index, failed.event_relative_path).failure
            reserved = case.index.task("develop-b").attempts[0]
            case.store.record_failure(case.index, task_id="develop-b", attempt_id=reserved.attempt_id,
                reason_code="retry-exhaustion", failure=failure)
            changed.append(_census(case.plane.root.verify(for_write=False)))

    if point == "resource-append":
        def insert(self, *, expected, updated):
            append(self, expected=expected, updated=updated)
            insert_event()

        monkeypatch.setattr(ExternalExecutionResourceEnvelopeStore, "compare_and_append", insert)
    else:
        inspect = ExternalNativeSubworkStore.inspect

        def insert_at_final_native(self, definition):
            result = inspect(self, definition)
            if case.store.read_event(case.index, case.candidate.event_relative_path) is not None:
                insert_event()
            return result

        monkeypatch.setattr(ExternalNativeSubworkStore, "inspect", insert_at_final_native)
    result = case.control.api.resume_campaign(case.request)
    assert changed and not result.succeeded
    assert case.store.read_terminal(case.index) is None
    if point == "resource-append":
        assert case.store.read_event(case.index, case.candidate.event_relative_path) is None
    else:
        assert case.store.read_event(case.index, case.candidate.event_relative_path) == TaskRecoveryEvent.from_receipt(
            case.index, case.receipt)
    # Resource transitions already fsynced are truthful partial custody; the
    # unexpected attempt must never be normalized into a terminal history.
    current = case.journal.load(case.envelope.envelope_id)
    assert current.events[:len(case.envelope.events)] == case.envelope.events
    assert current.cell(case.resources.cell_for_task("develop-b").cell_id) == case.envelope.cell(
        case.resources.cell_for_task("develop-b").cell_id)


def test_partial_resource_commit_retries_only_existing_custody_transitions(late_history, monkeypatch):
    case = late_history
    append = ExternalExecutionResourceEnvelopeStore.compare_and_append

    def interrupted(self, *, expected, updated):
        append(self, expected=expected, updated=updated)
        raise OSError("disclosed interruption after one durable resource event")

    with monkeypatch.context() as transient:
        transient.setattr(ExternalExecutionResourceEnvelopeStore, "compare_and_append", interrupted)
        failed = case.control.api.resume_campaign(case.request)
    assert not failed.succeeded and case.store.read_terminal(case.index) is None
    partial = case.journal.load(case.envelope.envelope_id)
    assert len(partial.events) == len(case.envelope.events) + 1
    assert partial.cell(case.resources.cell_for_task("prepare").cell_id).state is ExecutionResourceEnvelopeState.RECOVERY_PUBLICATION
    completed = case.control.api.resume_campaign(case.request)
    assert completed.succeeded, (completed.reason_codes, completed.errors)
    final = case.journal.load(case.envelope.envelope_id)
    assert final.events[:len(partial.events)] == partial.events
    assert len(final.events) == len(case.envelope.events) + 3
    assert final.child_token_states == case.envelope.child_token_states
    assert [task for task, _ in case.executor.calls] == ["prepare", "develop-a"]


def test_final_terminal_mutation_refuses_without_rolling_back_committed_custody(late_history, monkeypatch):
    case = late_history
    record = ExternalRunRecoveryStore.record_terminal

    def corrupt_after_publication(self, *arguments, **options):
        record(self, *arguments, **options)
        case.plane.root.resolve(case.receipt.output_materializations[0].relative_path,
            for_write=False).write_bytes(b"disclosed post-publication mutation")

    monkeypatch.setattr(ExternalRunRecoveryStore, "record_terminal", corrupt_after_publication)
    result = case.control.api.resume_campaign(case.request)
    assert not result.succeeded
    assert case.store.read_terminal(case.index).operational_status == "FAILED"
    assert case.store.read_event(case.index, case.candidate.event_relative_path) == TaskRecoveryEvent.from_receipt(
        case.index, case.receipt)
    assert [task for task, _ in case.executor.calls] == ["prepare", "develop-a"]


# The original catalog is intentional here. The earlier controls use an empty
# private projection and therefore cannot expose late real RUNNING row refusal.
def _original_sql_snapshot(case):
    engine = case.original_engine_factory()
    try:
        with engine.connect() as connection:
            run_pk = connection.execute(select(workflow_run.c.pk).where(
                workflow_run.c.run_id == case.index.run_id)).scalar_one()
            attempts = tuple(dict(row) for row in connection.execute(select(task_attempt)
                .where(task_attempt.c.workflow_run_pk == run_pk).order_by(task_attempt.c.pk)).mappings())
            leases = tuple(dict(row) for row in connection.execute(select(lease)
                .join(task_attempt, lease.c.task_attempt_pk == task_attempt.c.pk)
                .where(task_attempt.c.workflow_run_pk == run_pk).order_by(lease.c.pk)).mappings())
            events = tuple(dict(row) for row in connection.execute(select(run_event)
                .where(run_event.c.workflow_run_pk == run_pk).order_by(run_event.c.sequence)).mappings())
            return attempts, leases, events
    finally:
        engine.dispose()


def _change_original_lease(case, **changes):
    engine = case.original_engine_factory()
    try:
        with engine.begin() as connection:
            pk = connection.execute(select(task_attempt.c.pk).where(
                task_attempt.c.attempt_id == case.candidate.attempt_id)).scalar_one()
            statement = (update(lease).where(lease.c.task_attempt_pk == pk).values(**changes)
                if changes else delete(lease).where(lease.c.task_attempt_pk == pk))
            connection.execute(statement)
    finally:
        engine.dispose()


def _seed_dependency_projection(case, *, mode="valid"):
    # Use actual existing producers, with no fake retryable nonattempt event.
    # The disclosed five-task graph has a real failed develop-a -> freeze ->
    # evaluate chain. These producer calls represent its original metadata pass.
    assert "develop-a" in case.index.task("freeze").dependency_task_ids
    assert "freeze" in case.index.task("evaluate").dependency_task_ids
    engine = case.original_engine_factory()
    try:
        repository = SQLiteOperationalRepository(engine)
        if mode != "orphan":
            if mode != "missing-durable":
                case.store.record_not_attempted(case.index, task_id="freeze", reason=TaskBlockReason.DEPENDENCY_FAILED)
            repository.block_task(case.index.run_id, "freeze", TaskBlockReason.DEPENDENCY_FAILED)
        reason = TaskBlockReason.DEPENDENCY_FAILED if mode == "wrong-priority" else TaskBlockReason.DEPENDENCY_BLOCKED
        repository.block_task(case.index.run_id, "evaluate", reason)
    finally:
        engine.dispose()
    assert case.store.read_event(case.index, case.index.task("evaluate").nonattempt_event_relative_path) is None




@pytest.mark.parametrize("late_history", ("original-catalog",), indirect=True)
@pytest.mark.parametrize("with_blocks", (False, True), ids=("late-row", "transitive-blocks"))
def test_public_original_catalog_closes_same_row_and_replays_all_consumers(late_history, with_blocks):
    case = late_history
    if with_blocks:
        _seed_dependency_projection(case)
    before_sql = _original_sql_snapshot(case)
    before_primary = _census(case.plane.root.verify(for_write=False))
    before_calls = tuple(case.executor.calls)
    old_row, = (row for row in before_sql[0] if row["attempt_id"] == case.candidate.attempt_id)
    assert old_row["state"] == "RUNNING" and old_row["reason_code"] is None
    old_lease, = (row for row in before_sql[1] if row["task_attempt_pk"] == old_row["pk"])
    assert old_lease["lease_id"] == "lease." + case.candidate.attempt_id
    assert old_lease["expires_epoch_seconds"] == 1

    result = case.control.api.resume_campaign(case.request)
    assert result.succeeded, (result.reason_codes, result.errors)
    assert result.reason_codes == ("FAILED_HISTORY_RECONCILED_WITHOUT_EXECUTION",)
    assert result.payload.closure_only and result.payload.worker_entries == 0
    assert result.payload.operational_status == "FAILED"
    assert result.payload.assigned_task_count == 5
    terminal = case.store.read_terminal(case.index)
    assert terminal.completed_task_ids == ("prepare",)
    assert terminal.failed_task_ids == ("develop-a",)
    assert terminal.blocked_task_ids == (("evaluate", "freeze") if with_blocks else ())
    assert "develop-b" in result.payload.pending_task_ids
    after_sql = _original_sql_snapshot(case)
    new_row, = (row for row in after_sql[0] if row["attempt_id"] == case.candidate.attempt_id)
    assert new_row == dict(old_row, state="SUCCEEDED")
    assert tuple(row["pk"] for row in after_sql[0]) == tuple(row["pk"] for row in before_sql[0])
    assert after_sql[1] == tuple(row for row in before_sql[1] if row["pk"] != old_lease["pk"])
    assert after_sql[2][:len(before_sql[2])] == before_sql[2]
    assert [row["event_kind"] for row in after_sql[2][len(before_sql[2]):]] == ["TASK_ATTEMPT_SUCCEEDED", "RUN_FAILED"]
    assert case.store.read_event(case.index, case.candidate.event_relative_path) == TaskRecoveryEvent.from_receipt(case.index, case.receipt)
    envelope = case.journal.load(case.envelope.envelope_id)
    assert envelope.events[:len(case.envelope.events)] == case.envelope.events
    assert len(envelope.events) == len(case.envelope.events) + 3
    reserved_id = case.resources.cell_for_task("develop-b").cell_id
    assert envelope.cell(reserved_id) == case.envelope.cell(reserved_id)
    assert envelope.child_token_states == case.envelope.child_token_states
    after_primary = _census(case.plane.root.verify(for_write=False))
    journal_paths = {case.journal._relative_path(case.envelope.envelope_id, suffix) for suffix in ("head", "journal")}
    assert all(after_primary[path] == value for path, value in before_primary.items() if path not in journal_paths)

    status = case.control.api.campaign_status(CampaignStatusRequest(case.index.run_id))
    assert status.succeeded, (status.reason_codes, status.errors)
    assert status.payload.operational_status == "FAILED"
    assert case.store.read_terminal(case.index) == terminal
    assert case.store.read_event(case.index,
        case.index.task("evaluate").nonattempt_event_relative_path) is None
    assert case.journal.load(case.envelope.envelope_id).cell(reserved_id) == case.envelope.cell(reserved_id)
    repeated = case.control.api.resume_campaign(case.request)
    assert repeated.succeeded and repeated.payload == result.payload
    again_sql = _original_sql_snapshot(case)
    assert again_sql[:2] == after_sql[:2]
    assert sum(row["event_kind"] == "TASK_ATTEMPT_SUCCEEDED" for row in again_sql[2]) == sum(
        row["event_kind"] == "TASK_ATTEMPT_SUCCEEDED" for row in after_sql[2])
    assert sum(row["event_kind"] == "TASK_ATTEMPT_STARTED" for row in again_sql[2]) == sum(
        row["event_kind"] == "TASK_ATTEMPT_STARTED" for row in before_sql[2])
    assert _census(case.plane.root.verify(for_write=False)) == after_primary
    assert tuple(case.executor.calls) == before_calls


@pytest.mark.parametrize("late_history", ("original-catalog",), indirect=True)
@pytest.mark.parametrize("damage", ("live-lease", "zero-expiry", "negative-expiry", "fractional-expiry",
    "missing-lease", "substituted-lease", "missing-receipt", "unknown-native"))
def test_original_running_late_receipt_requires_complete_expired_custody(late_history, damage):
    case = late_history
    if damage == "live-lease":
        _change_original_lease(case, expires_epoch_seconds=int(time()) + 3600)
    elif damage in {"zero-expiry", "negative-expiry", "fractional-expiry"}:
        _change_original_lease(case, expires_epoch_seconds={
            "zero-expiry": 0, "negative-expiry": -1, "fractional-expiry": 0.5}[damage])
    elif damage == "missing-lease":
        _change_original_lease(case)
    elif damage == "substituted-lease":
        _change_original_lease(case, lease_id="lease.software.substituted")
    elif damage == "missing-receipt":
        case.plane.root.resolve(case.candidate.receipt_relative_path, for_write=False).unlink()
    else:
        store, _, definition = case.native[0]
        case.plane.root.resolve(store._root(definition) + "/completion.json", for_write=False).unlink()
    before_sql = _original_sql_snapshot(case)
    before = _census(case.plane.root.verify(for_write=False))
    result = case.control.api.resume_campaign(case.request)
    assert not result.succeeded
    assert _original_sql_snapshot(case) == before_sql
    assert case.store.read_terminal(case.index) is None
    assert case.store.read_event(case.index, case.candidate.event_relative_path) is None
    assert case.journal.load(case.envelope.envelope_id) == case.envelope
    assert _census(case.plane.root.verify(for_write=False)) == before


@pytest.mark.parametrize("late_history", ("original-catalog",), indirect=True)
@pytest.mark.parametrize("mode", ("orphan", "wrong-priority", "missing-durable"))
def test_catalog_only_dependency_blocks_require_actual_direct_causes(late_history, mode):
    case = late_history
    _seed_dependency_projection(case, mode=mode)
    before_sql = _original_sql_snapshot(case)
    before = _census(case.plane.root.verify(for_write=False))
    result = case.control.api.resume_campaign(case.request)
    assert not result.succeeded
    assert _original_sql_snapshot(case) == before_sql
    assert case.store.read_terminal(case.index) is None
    assert case.store.read_event(case.index, case.candidate.event_relative_path) is None
    assert case.journal.load(case.envelope.envelope_id) == case.envelope
    assert _census(case.plane.root.verify(for_write=False)) == before


@pytest.mark.parametrize("late_history", ("original-catalog",), indirect=True)
@pytest.mark.parametrize("mutation", ("renewed-lease", "new-catalog-block"))
@pytest.mark.parametrize("point", ("final-preflight", "after-first-resource-append"))
def test_catalog_changes_cannot_enter_closeout_terminal(late_history, monkeypatch, mutation, point):
    case = late_history
    changed = []
    before_primary = _census(case.plane.root.verify(for_write=False))

    def mutate():
        if changed:
            return
        if mutation == "renewed-lease":
            _change_original_lease(case, expires_epoch_seconds=int(time()) + 3600)
        else:
            engine = case.original_engine_factory()
            try:
                SQLiteOperationalRepository(engine).block_task(case.index.run_id, "evaluate", TaskBlockReason.DEPENDENCY_BLOCKED)
            finally:
                engine.dispose()
        changed.append(_original_sql_snapshot(case))

    if point == "final-preflight":
        inspect = ExternalNativeSubworkStore.inspect
        count = {}
        def inject(self, definition):
            result = inspect(self, definition)
            count[definition.subwork_id] = count.get(definition.subwork_id, 0) + 1
            if count[definition.subwork_id] == 2:
                mutate()
            return result
        monkeypatch.setattr(ExternalNativeSubworkStore, "inspect", inject)
    else:
        append = ExternalExecutionResourceEnvelopeStore.compare_and_append
        def inject(self, *, expected, updated):
            append(self, expected=expected, updated=updated)
            mutate()
        monkeypatch.setattr(ExternalExecutionResourceEnvelopeStore, "compare_and_append", inject)
    result = case.control.api.resume_campaign(case.request)
    assert changed and not result.succeeded
    assert _original_sql_snapshot(case) == changed[0]
    assert case.store.read_terminal(case.index) is None
    assert case.store.read_event(case.index, case.candidate.event_relative_path) is None
    current = case.journal.load(case.envelope.envelope_id)
    assert current.events[:len(case.envelope.events)] == case.envelope.events
    if point == "final-preflight":
        assert current == case.envelope
        assert _census(case.plane.root.verify(for_write=False)) == before_primary
    else:
        assert len(current.events) == len(case.envelope.events) + 1
        assert current.cell(case.resources.cell_for_task("develop-b").cell_id) == case.envelope.cell(
            case.resources.cell_for_task("develop-b").cell_id)


@pytest.mark.parametrize("late_history", ("original-catalog",), indirect=True)
def test_supplied_receipt_reader_is_copied_into_owned_scope_without_losing_hooks(late_history):
    case = late_history
    observed = []

    class DisclosedReceiptReader(ExternalTaskReceiptStore):
        def read(self, run_id, task_id, attempt_id):
            observed.append((self, self.plane, self.minimum_free_bytes))
            self.plane.require_verification_snapshot()
            return super().read(run_id, task_id, attempt_id)

    reader = DisclosedReceiptReader(case.plane, minimum_free_bytes=947)
    engine = case.original_engine_factory()
    try:
        terminal = case.store.reconcile_failed_history(plan=case.plan, index=case.index,
            receipt_store=reader, repository=SQLiteOperationalRepository(engine),
            resource_spec=case.resources)
    finally:
        engine.dispose()
    assert terminal.operational_status == "FAILED"
    assert terminal.completed_task_ids == ("prepare",)
    assert observed and all(type(row[0]) is DisclosedReceiptReader for row in observed)
    assert all(row[0] is not reader and row[1] is not case.plane and row[2] == 947 for row in observed)
    assert reader.plane is case.plane and reader.minimum_free_bytes == 947
    assert case.journal.load(case.envelope.envelope_id).cell(
        case.resources.cell_for_task("develop-b").cell_id).state is ExecutionResourceEnvelopeState.RESERVED


@pytest.mark.parametrize("late_history", ("original-catalog",), indirect=True)
def test_receipt_store_from_another_plane_refuses_before_any_effect(late_history):
    from copy import copy
    from empirical_lawhood.infrastructure.recovery import RunRecoveryError

    case = late_history
    before = _census(Path(case.root))
    sql_before = _original_sql_snapshot(case)
    engine = case.original_engine_factory()
    try:
        with pytest.raises(RunRecoveryError, match="receipt store.*exact artifact plane"):
            case.store.reconcile_failed_history(plan=case.plan, index=case.index,
                receipt_store=ExternalTaskReceiptStore(copy(case.plane)),
                repository=SQLiteOperationalRepository(engine), resource_spec=case.resources)
    finally:
        engine.dispose()
    assert _census(Path(case.root)) == before
    assert _original_sql_snapshot(case) == sql_before
    assert case.journal.load(case.envelope.envelope_id) == case.envelope
    assert case.store.read_terminal(case.index) is None


@pytest.mark.parametrize("late_history", ("original-catalog",), indirect=True)
def test_valid_receipt_substitution_after_read_refuses_before_first_effect(late_history, monkeypatch):
    from empirical_lawhood.runtime.artifacts import ReceiptCheck

    case = late_history
    body = ExternalTaskReceiptStore._read_body
    append = ExternalExecutionResourceEnvelopeStore.compare_and_append
    changed = []
    appends = []
    sql_before = _original_sql_snapshot(case)
    replacement = replace(case.receipt, checks=tuple(sorted(
        (*case.receipt.checks, ReceiptCheck("software-valid-receipt-substitution", True, ())),
        key=lambda row: row.check_id)))
    assert replacement.fingerprint() != case.receipt.fingerprint()
    assert (replacement.input_materialization_ids, replacement.output_logical_artifacts,
        replacement.output_materializations, replacement.operational_status) == (
        case.receipt.input_materialization_ids, case.receipt.output_logical_artifacts,
        case.receipt.output_materializations, case.receipt.operational_status)
    ExternalRunRecoveryStore._validate_receipt_static(case.index,
        next(row for row in case.plan.tasks if row.task_id == "prepare"), case.candidate, replacement)

    def substitute(self, run_id, task_id, attempt_id, path, manifest):
        result = body(self, run_id, task_id, attempt_id, path, manifest)
        if result == case.receipt and not changed:
            # Disclosed hostile filesystem substitution, not supported overwrite:
            # move A away, then let the real writer construct a fully valid B
            # body/sidecar/commit. No scientific output or frozen contract changes.
            changed.append(None)
            backup = Path(case.root).parent / (Path(case.root).name + ".receipt-a-backup")
            backup.mkdir()
            original_path = case.plane.root.resolve(case.candidate.receipt_relative_path, for_write=False)
            original_meta = case.plane.root.resolve(case.candidate.receipt_relative_path + ".manifest.json", for_write=False)
            original_path.rename(backup / "receipt-a.json")
            original_meta.rename(backup / "receipt-a.json.manifest.json")
            writer = ExternalTaskReceiptStore(case.plane)
            writer.commit(replacement, visibility_ceiling=manifest.logical.visibility_ceiling,
                outcome_access=manifest.logical.outcome_access)
            assert writer.read(run_id, task_id, attempt_id) == replacement
            changed[0] = _census(Path(case.root))
        return result

    def observe_append(self, *, expected, updated):
        appends.append((expected, updated))
        return append(self, expected=expected, updated=updated)

    monkeypatch.setattr(ExternalTaskReceiptStore, "_read_body", substitute)
    monkeypatch.setattr(ExternalExecutionResourceEnvelopeStore, "compare_and_append", observe_append)
    result = case.control.api.resume_campaign(case.request)
    assert changed and changed[0] is not None
    assert not result.succeeded
    assert not appends
    assert _census(Path(case.root)) == changed[0]
    assert _original_sql_snapshot(case) == sql_before
    assert case.journal.load(case.envelope.envelope_id) == case.envelope
    assert case.store.read_event(case.index, case.candidate.event_relative_path) is None
    assert case.store.read_terminal(case.index) is None


@pytest.mark.parametrize("custom_reconstruct", (False, True))
def test_failed_history_resource_journal_reuses_only_owned_stock_reader(late_history, monkeypatch, custom_reconstruct):
    from empirical_lawhood.infrastructure import execution_resource_envelopes as resource_module

    case = late_history
    decoded_origins = []
    decoder = resource_module.decode_canonical_bytes
    def count_origin(payload, kind, **options):
        if kind in (resource_module._JournalOrigin, resource_module._JournalCheckpoint):
            decoded_origins.append(kind)
        return decoder(payload, kind, **options)
    monkeypatch.setattr(resource_module, "decode_canonical_bytes", count_origin)
    reconstruct_calls = []
    if custom_reconstruct:
        reconstruct = ExternalRunRecoveryStore.reconstruct_execution_resource_envelope
        def traced(self, **options):
            reconstruct_calls.append(options["envelope_id"])
            return reconstruct(self, **options)
        monkeypatch.setattr(ExternalRunRecoveryStore, "reconstruct_execution_resource_envelope", traced)
    result = case.control.api.resume_campaign(case.request)
    assert result.succeeded, (result.reason_codes, result.errors)
    # The selected owned path authenticates one origin and reuses actual
    # head/stamp checks for all three reads and the existing append sequence.
    # A customized reconstruct hook keeps all three calls. Its reader reuses
    # the identical decoded prefix while still authenticating current bytes.
    assert len(decoded_origins) == (3 if custom_reconstruct else 1)
    assert reconstruct_calls == ([case.envelope.envelope_id] * 3 if custom_reconstruct else [])
    assert result.payload.worker_entries == 0


def test_external_resource_reconstruction_reuses_identical_decoded_prefix(late_history, monkeypatch):
    from empirical_lawhood.infrastructure import execution_resource_envelopes as resource_module

    case = late_history
    decoded_origins = []
    decoder = resource_module.decode_canonical_bytes
    def count_origin(payload, kind, **options):
        if kind in (resource_module._JournalOrigin, resource_module._JournalCheckpoint):
            decoded_origins.append(kind)
        return decoder(payload, kind, **options)
    monkeypatch.setattr(resource_module, "decode_canonical_bytes", count_origin)
    for _ in range(2):
        assert case.store.reconstruct_execution_resource_envelope(index=case.index,
            envelope_id=case.envelope.envelope_id, spec=case.resources,
            execution_plan=ObjectIdentity.from_record(case.plan.execution_plan_id, case.plan),
            jit_graph_signature_manifest=case.control.package.jit_graph_signature_manifest) == case.envelope
    assert len(decoded_origins) == 1


@pytest.mark.parametrize("damaged_member", ("json", "head"))
def test_owned_resource_prefix_refuses_physical_member_drift_before_effects(late_history, monkeypatch, damaged_member):
    case = late_history
    inspect = ExternalNativeSubworkStore.inspect
    calls = {}; changed = []
    def inject(self, definition):
        result = inspect(self, definition)
        calls[definition.subwork_id] = calls.get(definition.subwork_id, 0) + 1
        if calls[definition.subwork_id] == 2 and not changed:
            path = case.journal._path(case.envelope.envelope_id, damaged_member)
            path.write_bytes(path.read_bytes() + b" ")
            changed.append(_census(case.plane.root.verify(for_write=False)))
        return result
    monkeypatch.setattr(ExternalNativeSubworkStore, "inspect", inject)
    result = case.control.api.resume_campaign(case.request)
    assert changed and not result.succeeded
    assert case.store.read_terminal(case.index) is None
    assert case.store.read_event(case.index, case.candidate.event_relative_path) is None
    assert _census(case.plane.root.verify(for_write=False)) == changed[0]


def test_owned_resource_prefix_observes_new_committed_journal_suffix(late_history, monkeypatch):
    from empirical_lawhood.runtime.execution_envelope import RunExecutionResourceEnvelopeMachine

    case = late_history
    inspect = ExternalNativeSubworkStore.inspect
    calls = {}; changed = []
    def inject(self, definition):
        result = inspect(self, definition)
        calls[definition.subwork_id] = calls.get(definition.subwork_id, 0) + 1
        if calls[definition.subwork_id] == 2 and not changed:
            current = case.journal.load(case.envelope.envelope_id)
            cell = current.cell(case.resources.cell_for_task("prepare").cell_id)
            assert cell.last_progress_counter is not None
            heartbeat = ProgressHeartbeat("heartbeat.disclosed.external-resource-change", "prepare",
                case.candidate.attempt_id, cell_id_work_unit(case), cell.last_progress_counter + Decimal(1))
            updated = RunExecutionResourceEnvelopeMachine.heartbeat(current,
                event_id="resource-event.disclosed.external-resource-change",
                occurred_at_utc=current.events[-1].occurred_at_utc,
                cell_id=cell.cell_id, heartbeat=heartbeat)
            case.journal.compare_and_append(expected=current, updated=updated)
            changed.append((updated, _census(case.plane.root.verify(for_write=False))))
        return result
    def cell_id_work_unit(case):
        return case.resources.cell_for_task("prepare").progress_liveness.work_unit_id
    monkeypatch.setattr(ExternalNativeSubworkStore, "inspect", inject)
    result = case.control.api.resume_campaign(case.request)
    assert changed and not result.succeeded
    assert case.store.read_terminal(case.index) is None
    assert case.store.read_event(case.index, case.candidate.event_relative_path) is None
    assert case.journal.load(case.envelope.envelope_id) == changed[0][0]
    assert _census(case.plane.root.verify(for_write=False)) == changed[0][1]


def test_owned_resource_reader_cannot_outlive_failed_history_scope(late_history, monkeypatch):
    from empirical_lawhood.infrastructure.recovery import RunRecoveryError

    case = late_history
    captured = []
    locked = ExternalRunRecoveryStore._reconcile_failed_history_locked
    def retain(self, **options):
        captured.append(self)
        return locked(self, **options)
    monkeypatch.setattr(ExternalRunRecoveryStore, "_reconcile_failed_history_locked", retain)
    result = case.control.api.resume_campaign(case.request)
    assert result.succeeded, (result.reason_codes, result.errors)
    owned, = captured
    assert owned._failed_history_resource_journal is not None
    with pytest.raises(RunRecoveryError, match="active verification lifetime"):
        owned.reconstruct_execution_resource_envelope(index=case.index,
            envelope_id=case.envelope.envelope_id, spec=case.resources,
            execution_plan=ObjectIdentity.from_record(case.plan.execution_plan_id, case.plan),
            jit_graph_signature_manifest=case.control.package.jit_graph_signature_manifest)
