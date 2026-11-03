# SPDX-License-Identifier: MPL-2.0
"""Disclosed repair controls; literal receipts grant no scientific authority."""
from dataclasses import fields, replace
from decimal import Decimal
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response.configured_retained_execution import source_binding
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_lowering import operation_class
from empirical_lawhood.infrastructure.execution_resource_envelopes import ExternalExecutionResourceEnvelopeStore
from empirical_lawhood.infrastructure.recovery import decode_run_recovery_index, decode_run_recovery_terminal_event
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.execution import OperationalFailureClass
from empirical_lawhood.runtime.execution_envelope import ProgressHeartbeat, ProgressLivenessContract, RunExecutionResourceEnvelopeMachine as Machine, reconstruct_execution_resource_envelope
from empirical_lawhood.runtime.prepared_native_invocation import PreparedWorkerEnvironment
from empirical_lawhood.runtime.recovery import OperationalFailureDiagnostic, RecoveryTerminalAttempt, RecoveryTerminalDisposition, RunRecoveryIndex, RunRecoveryTerminalEvent, TaskRecoveryDisposition, TaskRecoveryEvent
from empirical_lawhood.runtime.retained_e3_repair import RetainedE3ControlRepair, RetainedE3RepairRecoveryIndex, RetainedE3RepairTerminalEvent, RetainedE3RepairContinuation, RetainedE3RepairContinuationV2, RetainedE3ContinuedRepairRecoveryIndex
from tests.recovery_support import case as recovery_case  # noqa: F401
from tests.test_matrix_e3_retained_continuation import continuation_case, public_case  # noqa: F401
from tests.runtime_platform.test_execution_scheduler import _plane


def pin(record, name):
    return ObjectIdentity.from_record(getattr(record, name), record)


@pytest.fixture
def repair_case(continuation_case, recovery_case):  # noqa: F811
    source = continuation_case
    rows = [next(value for value in source.retained if operation_class(value) == phase)
        for phase in ('numerical', 'fit', 'model-freeze')]
    completed, failed, blocked = (row.original_task for row in rows)
    failed = replace(failed, capability=replace(failed.capability,
        capability_key='matrix-e3-configured-protected.retained-fit'))
    tasks = tuple(sorted((completed, failed, blocked), key=lambda row: row.task_id))
    cells = tuple(replace(recovery_case.envelope.spec.task_cells[0], cell_id='cell.' + task.task_id,
        task_id=task.task_id, maximum_attempts=1) for task in tasks)
    spec = replace(recovery_case.envelope.spec, task_cells=cells)
    plan = replace(recovery_case.plan, execution_plan_id='execution.' + source.retention.original_run_id,
        source_plan=replace(recovery_case.plan.source_plan, object_id=source.retention.original_run_id),
        implementation_commit=source.retention.original_source.observed_git_head, tasks=tasks,
        execution_resource_envelope_spec=pin(spec, 'envelope_spec_id'))
    index = RunRecoveryIndex.from_execution_plan(plan, run_id=plan.source_plan.object_id,
        wave_id='wave.disclosed.original', authority_identities=(spec.issued_study_extensions,))
    receipt = rows[0].original_receipt
    candidate, = index.task(failed.task_id).attempts
    failure = TaskRecoveryEvent('failure.disclosed', pin(index, 'recovery_index_id'), index.run_id,
        failed.task_id, candidate.attempt_id, 1, TaskRecoveryDisposition.FAILED,
        None, None, None, None, (), ('retry-exhaustion',), OperationalFailureDiagnostic.create(
            OperationalFailureClass.RETRY_EXHAUSTION, sanitized_exception_type='PermissionError',
            sanitized_message='Disclosed pre-worker lane failure'))
    terminal = RunRecoveryTerminalEvent('terminal.disclosed', pin(index, 'recovery_index_id'), index.run_id,
        'FAILED', tuple(sorted((RecoveryTerminalAttempt(receipt.attempt_id, completed.task_id, 1,
            RecoveryTerminalDisposition.SUCCEEDED, None, receipt.receipt_id, receipt.fingerprint()),
            RecoveryTerminalAttempt(candidate.attempt_id, failed.task_id, 1,
                RecoveryTerminalDisposition.FAILED, 'retry-exhaustion', None, None)),
            key=lambda row: (row.task_id, row.ordinal))), (completed.task_id,), (failed.task_id,), ())
    envelope = Machine.initial(envelope_id='run-resource-envelope.' + index.run_id,
        spec=spec, execution_plan=pin(plan, 'execution_plan_id'))
    for task, attempt in ((completed, receipt.attempt_id), (failed, candidate.attempt_id)):
        common = dict(cell_id=spec.cell_for_task(task.task_id).cell_id, occurred_at_utc='2026-10-16T00:00:00Z')
        envelope = Machine.reserve(envelope, event_id=task.task_id + '.reserve', attempt_id=attempt, **common)
        envelope = Machine.launch(envelope, event_id=task.task_id + '.launch', attempt_id=attempt, **common)
        if task is completed:
            envelope = Machine.observe_receipt(envelope, event_id=task.task_id + '.receipt',
                attempt_id=attempt, receipt=pin(receipt, 'receipt_id'), valid_receipt=True, scientific_terminal=False, **common)
            envelope = Machine.publish(envelope, event_id=task.task_id + '.publish',
                artifact=pin(receipt, 'receipt_id'), **common)
            envelope = Machine.terminal(envelope, event_id=task.task_id + '.terminal', **common)
        else:
            envelope = Machine.observe_operational_failure(envelope, event_id=task.task_id + '.failure',
                attempt_id=attempt, reason_code='RETRY_EXHAUSTION', **common)
    repair = RetainedE3ControlRepair('repair.disclosed', 'a' * 64, pin(plan, 'execution_plan_id'),
        pin(index, 'recovery_index_id'), pin(terminal, 'terminal_event_id'), pin(envelope, 'envelope_id'),
        failed.task_id, pin(failure, 'event_id'), source.retention.original_reveal_authority,
        ((completed.task_id, pin(receipt, 'receipt_id')),), (blocked.task_id,),
        source_binding(source.retention.response_provenance), source.retention.original_source,
        PreparedWorkerEnvironment('/disclosed/worker/bin/python', 'a' * 64, '/disclosed/worker', ()),
        '/disclosed/worker-source')
    return SimpleNamespace(plan=plan, index=index, repair=repair, envelope=envelope, terminal=terminal,
        receipt=receipt, failed=failed, blocked=blocked, completed=completed)


def test_repair_derivation_reuses_original_receipts_and_only_retries_failed_pure_adoption(repair_case):
    case = repair_case
    before = case.index.canonical_bytes(), case.plan.canonical_bytes(), case.terminal.canonical_bytes()
    index = RetainedE3RepairRecoveryIndex.derive(case.plan, case.index, case.repair)
    index.validate_plan(case.plan)
    assert decode_run_recovery_index(index.canonical_bytes()) == index
    assert decode_canonical_bytes(case.repair.canonical_bytes(), RetainedE3ControlRepair, maximum_bytes=None) == case.repair
    assert index.task(case.completed.task_id) == case.index.task(case.completed.task_id)
    assert TaskRecoveryEvent.from_receipt(index, case.receipt) == TaskRecoveryEvent.from_receipt(case.index, case.receipt)
    assert index.task(case.blocked.task_id).attempts[0].attempt_id != case.index.task(case.blocked.task_id).attempts[0].attempt_id
    assert index.task(case.blocked.task_id).attempts[0].ordinal == 1
    assert index.task(case.failed.task_id).attempts[0].attempt_id != case.index.task(case.failed.task_id).attempts[0].attempt_id
    assert all(row.maximum_attempts == 1 and len(row.attempts) == 1 for row in index.tasks)
    assert index.implementation_commit == case.receipt.implementation_commit == case.repair.worker.observed_git_head
    assert before == (case.index.canonical_bytes(), case.plan.canonical_bytes(), case.terminal.canonical_bytes())
    summary = RetainedE3RepairTerminalEvent(**{field.name: getattr(case.terminal, field.name)
        for field in fields(RunRecoveryTerminalEvent) if field.name != 'recovery_index'},
        recovery_index=pin(index, 'recovery_index_id'))
    assert decode_run_recovery_terminal_event(summary.canonical_bytes()) == summary


@pytest.mark.parametrize('repair_kind', (RetainedE3ControlRepair, RetainedE3RepairContinuation, RetainedE3RepairContinuationV2))
@pytest.mark.parametrize('damage', ('native', 'launched', 'reserved', 'unknown', 'success', 'second-repair'))
def test_pure_repair_never_repeats_completed_or_uncertain_native_work(repair_case, damage, repair_kind):
    case = repair_case
    envelope = case.envelope
    cell_id = envelope.spec.cell_for_task(case.failed.task_id).cell_id
    if damage == 'native':
        progress = ProgressLivenessContract('progress.disclosed', ProgressHeartbeat.SCHEMA,
            'work.disclosed', Decimal('1'), True, True)
        envelope = replace(envelope, spec=replace(envelope.spec, task_cells=tuple(
            replace(row, native_simulator_launch=True, physical_execution_cost=1, retry_token_cost=1,
                physical_independent_unit_id='unit.disclosed', preparation_unit_id='preparation.disclosed',
                progress_liveness=progress) if row.cell_id == cell_id else row
            for row in envelope.spec.task_cells), child_token_limits=tuple(
                replace(row, physical_execution_token_limit=1) for row in envelope.spec.child_token_limits)))
    elif damage == 'success':
        cell_id = envelope.spec.cell_for_task(case.completed.task_id).cell_id
    elif damage == 'second-repair':
        envelope = Machine.repair_pure_task(envelope, event_id='repair.first', occurred_at_utc='2026-10-16T00:00:00Z',
            cell_id=cell_id, repair=case.repair.identity)
    else:
        from empirical_lawhood.runtime.execution_envelope import ExecutionResourceEnvelopeState
        state = {'launched': ExecutionResourceEnvelopeState.LAUNCHED, 'reserved': ExecutionResourceEnvelopeState.RESERVED,
            'unknown': ExecutionResourceEnvelopeState.UNKNOWN_COMPLETION}[damage]
        envelope = replace(envelope, cells=tuple(replace(row, state=state) if row.cell_id == cell_id else row
            for row in envelope.cells))
    with pytest.raises(ValueError, match='completed, native, uncertain or repeated'):
        Machine.repair_pure_task(envelope, event_id='repair.refused', occurred_at_utc='2026-10-16T00:00:00Z',
            cell_id=cell_id, repair=replace(case.repair.identity,
                object_schema=repair_kind.SCHEMA, object_version=repair_kind.VERSION))


def test_additional_repair_journal_keeps_original_prefix_and_frozen_limits(repair_case, tmp_path):
    case = repair_case
    plane = _plane(tmp_path)
    original = ExternalExecutionResourceEnvelopeStore(plane.root, artifact_plane=plane,
        state_root_relative_path='original-journal')
    original.create(case.envelope, jit_graph_signature_manifest=None)
    before = original.load(case.envelope.envelope_id)
    index = RetainedE3RepairRecoveryIndex.derive(case.plan, case.index, case.repair)
    branch = ExternalExecutionResourceEnvelopeStore(plane.root, artifact_plane=plane,
        state_root_relative_path=index.resource_envelope_event_root_relative_path)
    branch.create(before, jit_graph_signature_manifest=None)
    updated = Machine.repair_pure_task(before, event_id='repair.accepted', occurred_at_utc='2026-10-16T00:00:00Z',
        cell_id=before.spec.cell_for_task(case.failed.task_id).cell_id, repair=case.repair.identity)
    branch.compare_and_append(expected=before, updated=updated)
    assert original.load(before.envelope_id).canonical_bytes() == before.canonical_bytes()
    assert branch.load(before.envelope_id) == updated
    assert updated.events[:-1] == before.events and updated.spec == before.spec
    assert reconstruct_execution_resource_envelope(envelope_id=before.envelope_id, spec=before.spec,
        execution_plan=before.execution_plan, events=updated.events, jit_graph_signature_manifest=None) == updated


@pytest.mark.parametrize('receipt_path_failure,later_adoption_failure', ((False, False), (True, False), (False, True)))
def test_real_scheduler_reuses_success_and_executes_only_repair_and_unstarted_dependencies(
        repair_case, tmp_path, monkeypatch, receipt_path_failure, later_adoption_failure):
    """Actual exposed executions/publications, rather than hypothetical receipts."""
    from copy import copy
    from empirical_lawhood.api.retained_e3_control_repair import repair_resource_coordinator
    from empirical_lawhood.api.current_task_custody import CurrentIssuedTaskCustody
    from empirical_lawhood.infrastructure.execution import DirectTaskExecutor, DurableExecutionResourceEnvelopeCoordinator, ExecutionResourceCapacity
    from empirical_lawhood.infrastructure.recovery import ExternalRunRecoveryStore
    from empirical_lawhood.infrastructure.sql import SQLiteOperationalRepository, create_catalog_engine, upgrade_catalog
    from empirical_lawhood.kernel.status import OperationalStatus
    from empirical_lawhood.runtime.execution import RunnerRegistry
    from empirical_lawhood.runtime.plans import BarrierKind, ScientificInputRole, ScientificInputSpec
    from tests.runtime_platform.test_execution_scheduler import DeterministicRunner
    from tests.runtime_platform.test_multicore_envelope_admission import _selected_plan, _scheduler
    from tests.runtime_platform.conftest import build_protocol_fixture

    protocol_fixture = build_protocol_fixture()
    plan, spec = _selected_plan(protocol_fixture, workers=1, aggregate_slots=1)
    done, failed, *pending = plan.tasks
    failed = replace(failed, capability=replace(failed.capability,
        capability_key='matrix-e3-configured-protected.retained-fit'))
    tasks = [done, failed]
    parent = failed
    for task in pending:
        if later_adoption_failure and task is pending[0]:
            task = replace(task, capability=replace(task.capability,
                capability_key='matrix-e3-configured-protected.retained-model-freeze'))
        output = parent.outputs[0]
        edge = ScientificInputSpec('edge.' + task.task_id, 'parent', ScientificInputRole.SOURCE,
            parent.task_id, output.output_id, None, output.logical_artifact_id, output.logical_artifact_id,
            output.payload_schema, output.media_type, parent.capability.requested_resources.output_bytes,
            output.outcome_access, output.visibility_ceiling, BarrierKind.NONE)
        task = replace(task, dependency_task_ids=(parent.task_id,), scientific_inputs=(edge,))
        tasks.append(task)
        parent = task
    plan = replace(plan, tasks=tuple(tasks))
    pending = tasks[2:]
    scheduler, repository, _, _ = _scheduler(tmp_path, protocol_fixture, plan, spec, workers=1,
        capacity=ExecutionResourceCapacity(1, spec.aggregate_memory_ceiling_bytes, 0, True, True, False),
        executor=DirectTaskExecutor())
    plane = scheduler.artifact_writer
    store = ExternalExecutionResourceEnvelopeStore(plane.root, artifact_plane=plane)
    coordinator = DurableExecutionResourceEnvelopeCoordinator(store)
    envelope_id = 'run-resource-envelope.' + plan.source_plan.object_id
    coordinator.ensure_initialized(envelope_id=envelope_id, spec=spec,
        execution_plan=pin(plan, 'execution_plan_id'), jit_graph_signature_manifest=None)
    scheduler.execution_resource_envelope_coordinator = coordinator
    scheduler.execution_resource_envelope_id = envelope_id
    manifest = next(row for row in protocol_fixture.registry.capabilities
        if row.capability_key == done.capability.capability_key)
    fit_manifest = replace(manifest, capability_key=failed.capability.capability_key)
    first_done, first_failed = DeterministicRunner(manifest), DeterministicRunner(fit_manifest, failures=1)
    scheduler.runner_registry = RunnerRegistry((first_failed, first_done), registry_sha256=plan.registry_sha256)
    if later_adoption_failure:
        freeze_manifest = replace(manifest, capability_key=pending[0].capability.capability_key)
        scheduler.runner_registry = RunnerRegistry(tuple(sorted((first_failed, first_done,
            DeterministicRunner(freeze_manifest)), key=lambda runner: runner.manifest.capability_key)),
            registry_sha256=plan.registry_sha256)
    first = scheduler.execute(plan.source_plan.object_id, plan)
    assert first.status is OperationalStatus.FAILED and first.completed_task_ids == (done.task_id,)
    terminal = scheduler.recovery_store.read_terminal(scheduler.recovery_index)
    original_terminal_bytes = terminal.canonical_bytes()
    original_envelope = coordinator.current(envelope_id)
    receipt, = first.receipts
    candidate, = scheduler.recovery_index.task(failed.task_id).attempts
    failure = scheduler.recovery_store.read_event(scheduler.recovery_index, candidate.event_relative_path)
    premise = repair_case.repair
    repair = replace(premise, execution_plan=pin(plan, 'execution_plan_id'),
        original_index=pin(scheduler.recovery_index, 'recovery_index_id'),
        original_terminal=pin(terminal, 'terminal_event_id'), original_resource_envelope=pin(original_envelope, 'envelope_id'),
        failed_task_id=failed.task_id, original_failure=pin(failure, 'event_id'),
        completed_receipts=((done.task_id, pin(receipt, 'receipt_id')),),
        unstarted_task_ids=tuple(task.task_id for task in pending),
        worker=replace(premise.worker, observed_git_head=plan.implementation_commit))
    if receipt_path_failure:
        # Match the failed production attempt length. Exercise the real file
        # publication path, not a mocked receipt-store exception.
        size = 217 - len(candidate.attempt_id) - 1
        repair = replace(repair, repair_id='repair.' + 'r' * (size - len('repair.')))
    index = RetainedE3RepairRecoveryIndex.derive(plan, scheduler.recovery_index, repair)
    scheduler.recovery_store.freeze(index)
    second = copy(scheduler)
    engine = create_catalog_engine('sqlite+pysqlite:///:memory:')
    upgrade_catalog(engine)
    second.operational_repository = SQLiteOperationalRepository(engine)
    second.recovery_index = index
    second.recovery_store = ExternalRunRecoveryStore(plane)
    second.execution_resource_envelope_coordinator = repair_resource_coordinator(writer=plane,
        package=SimpleNamespace(execution_resource_envelope_spec=spec, jit_graph_signature_manifest=None),
        plan=plan, index=index)
    again_done, again_fit = DeterministicRunner(manifest), DeterministicRunner(fit_manifest)
    second.runner_registry = RunnerRegistry((again_fit, again_done), registry_sha256=plan.registry_sha256)
    if later_adoption_failure:
        freeze_manifest = replace(manifest, capability_key=pending[0].capability.capability_key)
        freeze_runner = DeterministicRunner(freeze_manifest, failures=1)
        second.runner_registry = RunnerRegistry(tuple(sorted((again_fit, again_done, freeze_runner),
            key=lambda runner: runner.manifest.capability_key)), registry_sha256=plan.registry_sha256)
    final_engine = None
    ordinary_receipts = second.receipt_store
    try:
        with monkeypatch.context() as old_staging:
            if receipt_path_failure:
                old_staging.setattr(plane, '_staging_path',
                    lambda path, token, suffix: path.with_name(f'.{path.name}.{token}.{suffix}'))
            result = second.execute(plan.source_plan.object_id, plan)
        if receipt_path_failure:
            assert result.status is OperationalStatus.FAILED
            assert result.completed_task_ids == (done.task_id,)
            assert len(again_fit.contexts) == 1 and not again_done.contexts
            first_repair_terminal = second.recovery_store.read_terminal(index)
            first_repair_terminal_bytes = first_repair_terminal.canonical_bytes()
            failed_candidate, = index.task(failed.task_id).attempts
            first_repair_failure = second.recovery_store.read_event(index, failed_candidate.event_relative_path)
            assert first_repair_failure.failure.sanitized_exception_type == 'OSError'
            first_repair_resources = second.execution_resource_envelope_coordinator.current(envelope_id)
            proof = RetainedE3RepairContinuation('repair.disclosed.continuation', repair.owner_instruction_sha256,
                repair.identity, pin(index, 'recovery_index_id'), pin(first_repair_terminal, 'terminal_event_id'),
                pin(first_repair_failure, 'event_id'), pin(first_repair_resources, 'envelope_id'),
                replace(repair_case.repair.controller, observed_git_head='c' * 40), failed.task_id,
                tuple(sorted((plane.read_manifest(output.relative_path) for output in failed.outputs),
                    key=lambda row: row.materialization.relative_path)), repair_case.repair.controller,
                '/disclosed/worker/site-packages')
            third_index = RetainedE3ContinuedRepairRecoveryIndex.derive(plan, index, proof)
            third_index.validate_plan(plan)
            assert decode_run_recovery_index(third_index.canonical_bytes()) == third_index
            assert third_index.task(done.task_id) == scheduler.recovery_index.task(done.task_id)
            assert third_index.event_owner(done.task_id) == scheduler.recovery_index
            assert all(binding.maximum_attempts == 1 and len(binding.attempts) == 1
                for binding in third_index.tasks)
            for binding in third_index.tasks:
                if binding.task_id == done.task_id:
                    continue
                candidate, = binding.attempts
                assert candidate.ordinal == 1
                assert len(candidate.attempt_id) < 100
                leaf = candidate.receipt_relative_path.rsplit('/', 1)[1]
                assert len(leaf.encode()) < 255
            second.recovery_store.freeze(third_index)
            third = copy(second)
            final_engine = create_catalog_engine('sqlite+pysqlite:///:memory:')
            upgrade_catalog(final_engine)
            third.operational_repository = SQLiteOperationalRepository(final_engine)
            third.recovery_index = third_index
            third.receipt_store = ordinary_receipts
            third.execution_resource_envelope_coordinator = repair_resource_coordinator(writer=plane,
                package=SimpleNamespace(execution_resource_envelope_spec=spec, jit_graph_signature_manifest=None),
                plan=plan, index=third_index)
            restored = third.execution_resource_envelope_coordinator.current(envelope_id)
            assert restored.events[:-1] == first_repair_resources.events and restored.spec == spec
            again_done, again_fit = DeterministicRunner(manifest), DeterministicRunner(fit_manifest)
            third.runner_registry = RunnerRegistry((again_fit, again_done), registry_sha256=plan.registry_sha256)
            result = third.execute(plan.source_plan.object_id, plan)
            assert second.recovery_store.read_terminal(index).canonical_bytes() == first_repair_terminal_bytes
            assert second.execution_resource_envelope_coordinator.current(envelope_id) == first_repair_resources
            assert decode_run_recovery_terminal_event(third.recovery_store.read_terminal(third_index).canonical_bytes()) == third.recovery_store.read_terminal(third_index)
            second = third
        if later_adoption_failure:
            assert result.status is OperationalStatus.FAILED
            assert set(result.completed_task_ids) == {done.task_id, failed.task_id}
            assert result.failed_task_ids == (pending[0].task_id,)
            previous_terminal = second.recovery_store.read_terminal(index)
            previous_bytes = previous_terminal.canonical_bytes()
            resources = second.execution_resource_envelope_coordinator.current(envelope_id)
            failed_candidate, = index.task(pending[0].task_id).attempts
            failure = second.recovery_store.read_event(index, failed_candidate.event_relative_path)
            proof = RetainedE3RepairContinuationV2('repair.disclosed.progress', repair.owner_instruction_sha256,
                repair.identity, pin(index, 'recovery_index_id'), pin(previous_terminal, 'terminal_event_id'),
                pin(failure, 'event_id'), pin(resources, 'envelope_id'),
                repair.controller, pending[0].task_id,
                (), replace(repair.controller, observed_git_head='c' * 40), '/disclosed/worker/site-packages',
                tuple(sorted((row.task_id, pin(row, 'receipt_id')) for row in result.receipts)),
                tuple(row.task_id for row in pending[1:]))
            progress = RetainedE3ContinuedRepairRecoveryIndex.derive(plan, index, proof)
            assert decode_run_recovery_index(progress.canonical_bytes()) == progress
            assert progress.task(failed.task_id) == index.task(failed.task_id)
            assert progress.event_owner(failed.task_id) == index
            assert progress.event_owner(done.task_id) == scheduler.recovery_index
            with pytest.raises(ValueError, match='drops or substitutes'):
                RetainedE3ContinuedRepairRecoveryIndex.derive(plan, index, replace(proof,
                    completed_receipts=tuple(row for row in proof.completed_receipts if row[0] != done.task_id),
                    unstarted_task_ids=tuple(sorted((*proof.unstarted_task_ids, done.task_id)))))
            from empirical_lawhood.api import retained_e3_repair_continuation as owner
            with monkeypatch.context() as publication:
                publication.setattr(owner, 'implementation_binding', lambda root: proof.controller)
                owner.publish_repair_continuation(service=SimpleNamespace(artifact_plane=plane, repo_root=None),
                    proof=proof, index=progress)
            assert owner.read_repair_continuation(writer=plane, plan=plan, predecessor=index) == progress
            third = copy(second)
            final_engine = create_catalog_engine('sqlite+pysqlite:///:memory:')
            upgrade_catalog(final_engine)
            third.operational_repository = SQLiteOperationalRepository(final_engine)
            third.recovery_index = progress
            third.execution_resource_envelope_coordinator = repair_resource_coordinator(writer=plane,
                package=SimpleNamespace(execution_resource_envelope_spec=spec, jit_graph_signature_manifest=None),
                plan=plan, index=progress)
            restored = third.execution_resource_envelope_coordinator.current(envelope_id)
            assert restored.events[:-1] == resources.events and restored.spec == spec
            again_done, again_fit = DeterministicRunner(manifest), DeterministicRunner(fit_manifest)
            freeze_runner = DeterministicRunner(freeze_manifest)
            third.runner_registry = RunnerRegistry(tuple(sorted((again_done, again_fit, freeze_runner),
                key=lambda runner: runner.manifest.capability_key)), registry_sha256=plan.registry_sha256)
            result = third.execute(plan.source_plan.object_id, plan)
            assert not again_fit.contexts
            assert [row.task_id for row in freeze_runner.contexts] == [pending[0].task_id]
            assert second.recovery_store.read_terminal(index).canonical_bytes() == previous_bytes
            assert second.execution_resource_envelope_coordinator.current(envelope_id) == resources
            second = third
        assert result.status is OperationalStatus.SUCCEEDED
        assert [row.task_id for row in again_fit.contexts] == ([] if later_adoption_failure else [failed.task_id])
        assert [row.task_id for row in again_done.contexts] == [row.task_id for row in pending[later_adoption_failure:]]
        for actual in result.receipts:
            assert second.receipt_store.read_by_receipt_id(actual.run_id, actual.task_id, actual.receipt_id) == actual
            assert second.receipt_store.read_by_receipt_id(actual.run_id, 'foreign.task', actual.receipt_id) is None
        # Exercise the parent's real dependency-reader path with the contexts
        # produced by the scheduler, including compact continuation receipts.
        custody = CurrentIssuedTaskCustody(writer=plane)
        # The exposed scheduler fixture uses its own static input layout.
        # Select those actual publications; receipt lookup stays unmodified.
        from empirical_lawhood.api import current_task_custody
        monkeypatch.setattr(current_task_custody, 'provider_input_location',
            lambda writer, run_id, logical: (
                second.external_input_resolver.resolve((logical,))[0].materialization.relative_path, None, None))
        contexts = again_done.contexts + (freeze_runner.contexts if later_adoption_failure else [])
        for context in contexts:
            task = next(row for row in plan.tasks if row.task_id == context.task_id)
            dependencies, _ = custody.task_inputs(context, task)
            assert set(dependencies) == set(task.dependency_task_ids)
        assert next(row for row in result.receipts if row.task_id == done.task_id) == receipt
        assert scheduler.recovery_store.read_terminal(scheduler.recovery_index).canonical_bytes() == original_terminal_bytes
        assert coordinator.current(envelope_id) == original_envelope
        assert scheduler.execute(plan.source_plan.object_id, plan).status is OperationalStatus.FAILED
        count = len(again_done.contexts), len(again_fit.contexts)
        assert second.execute(plan.source_plan.object_id, plan) == result
        assert (len(again_done.contexts), len(again_fit.contexts)) == count
    finally:
        if final_engine is not None:
            final_engine.dispose()
        engine.dispose()
        repository.engine.dispose()


def test_worker_observation_preserves_printed_canonical_line_endings(repair_case, monkeypatch):
    from empirical_lawhood.api import retained_e3_control_repair as owner
    expected = repair_case.repair.worker, repair_case.repair.worker_environment
    # Each canonical record already ends in LF; print adds another LF.
    stdout = b''.join(record.canonical_bytes() + b'\n' for record in expected)
    monkeypatch.setattr(owner, 'run_bounded_command', lambda *args, **kwargs:
        SimpleNamespace(returncode=0, stdout=stdout))
    assert owner.observe_frozen_repair_worker(interpreter='/disclosed/python',
        source_root='/disclosed/source') == expected
