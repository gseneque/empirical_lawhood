# SPDX-License-Identifier: MPL-2.0
"""Public selective recovery after a failed PURE retained-model adoption.

The controller may change; the scientific worker, task plan and successful
receipts may not. Every transition is derived under the exclusive run claim.
"""
from datetime import UTC, datetime

from empirical_lawhood.adapters.methods.matrix_factor_response.configured_retained_execution import require_numerical_source_continuity
from empirical_lawhood.infrastructure.execution import DurableExecutionResourceEnvelopeCoordinator
from empirical_lawhood.infrastructure.execution_resource_envelopes import ExternalExecutionResourceEnvelopeStore
from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
from empirical_lawhood.infrastructure.recovery import ExternalRunRecoveryStore
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest, most_restrictive_outcome_access
from empirical_lawhood.runtime.execution_envelope import ExecutionResourceEnvelopeState, RunExecutionResourceEnvelopeMachine
from empirical_lawhood.runtime.retained_e3_repair import RetainedE3RepairContinuation, RetainedE3RepairContinuationV2, RetainedE3ContinuedRepairRecoveryIndex, RetainedE3RepairRecoveryIndex

from .configured_e3_retained_custody import _resources
from .configured_e3_retained_runtime import retained_e3_execution_scope
from .current_result_custody import require_current_result_reveal_authority
from .recursive_authoring import implementation_binding
from .retained_e3_control_repair import _controller_admission, _pin, _read_record, _require_repair_catalog, observe_frozen_repair_worker, observe_frozen_worker_package_root, repair_relative_path


def repair_continuation_relative_path(predecessor):
    return (repair_relative_path(predecessor.run_id).rsplit('/', 1)[0]
        + '/continuations/' + predecessor.fingerprint() + '.json')


def selected_controller(writer, index):
    if type(index) is RetainedE3ContinuedRepairRecoveryIndex:
        return index.repair_continuation.controller
    admission = _controller_admission(writer, index)
    return index.repair.controller if admission is None else admission.controller


def read_repair_continuation(*, writer, plan, predecessor):
    proof = _read_record(writer, repair_continuation_relative_path(predecessor), RetainedE3RepairContinuation,
        record_versions=(RetainedE3RepairContinuationV2,))
    if proof is None:
        return predecessor
    index = RetainedE3ContinuedRepairRecoveryIndex.derive(plan, predecessor, proof)
    recovery = ExternalRunRecoveryStore(writer)
    terminal = recovery.read_terminal(predecessor)
    candidate, = predecessor.task(proof.failed_task_id).attempts
    failure = recovery.read_event(predecessor, candidate.event_relative_path)
    if (terminal is None or terminal.operational_status != 'FAILED'
            or _pin(terminal, 'terminal_event_id') != proof.previous_terminal
            or terminal.failed_task_ids != (proof.failed_task_id,)
            or terminal.completed_task_ids != tuple(key for key, _ in index.completed_receipts)
            or terminal.blocked_task_ids != index.unstarted_task_ids
            or failure is None or _pin(failure, 'event_id') != proof.previous_failure
            or failure.failure is None
            or failure.failure.failure_class.value not in (
                ('RETRY_EXHAUSTION',) if type(proof) is RetainedE3RepairContinuation
                else ('RETRY_EXHAUSTION', 'PROVIDER_RUNNER_DEFECT'))
            or selected_controller(writer, predecessor) != proof.previous_controller
            or any(writer.read_manifest(row.materialization.relative_path) != row
                for row in proof.failed_output_manifests)):
        raise PermissionError('repair continuation loses its failed wave, copied outputs or controller history')
    for task_id, receipt in index.completed_receipts:
        rows = tuple(row for row in terminal.attempts
            if row.task_id == task_id and row.disposition.value == 'SUCCEEDED')
        if len(rows) != 1 or (rows[0].receipt_id, rows[0].receipt_sha256) != (
                receipt.object_id, receipt.object_fingerprint):
            raise PermissionError('repair continuation substitutes a preceding successful receipt')
    require_numerical_source_continuity(predecessor.repair.worker, proof.controller)
    return index


def derive_repair_continuation(*, service, run_id, repair_id, owner_instruction_sha256, reveal_authority_id):
    """Derive the only new attempt and every first execution from actual custody.

    The caller holds the exclusive current run claim and original-control scope.
    No terminal, failed event, output, receipt or resource journal is replaced.
    """
    package = service._load_package(run_id)
    plan, predecessor, recovery = service._load_status_index(run_id, package=package)
    if type(predecessor) not in (RetainedE3RepairRecoveryIndex, RetainedE3ContinuedRepairRecoveryIndex):
        raise PermissionError('repair continuation requires an authenticated retained-adoption repair')
    original_repair = predecessor.repair
    if owner_instruction_sha256 != original_repair.owner_instruction_sha256:
        raise PermissionError('repair continuation changes its exact retained owner instruction')
    terminal = recovery.read_terminal(predecessor)
    if terminal is None or terminal.operational_status != 'FAILED' or len(terminal.failed_task_ids) != 1:
        raise PermissionError('repair continuation requires one known failed PURE adoption')
    failed, = terminal.failed_task_ids
    now = datetime.now(UTC).isoformat().replace('+00:00', 'Z')
    service._validate_campaign_authorization(package)
    service._validate_issued_execution_authority(package, at_utc=now)
    original_scope = retained_e3_execution_scope(service, run_id)

    def refresh(_manifest=None):
        original_scope.require_access()
        require_current_result_reveal_authority(writer=service.artifact_plane, package=package,
            reveal_authority_id=reveal_authority_id)

    refresh()
    closure = recovery._reconcile_terminal(index=predecessor, plan=plan, terminal=terminal,
        repository=None, receipt_store=ExternalTaskReceiptStore(service.artifact_plane),
        existing={}, candidate_count=len(plan.tasks))
    receipts = {row.task_id: row for row in closure.recovered_receipts}
    unstarted = tuple(sorted({row.task_id for row in plan.tasks} - {*receipts, failed}))
    if unstarted != terminal.blocked_task_ids:
        raise PermissionError('repair continuation changes the actual blocked denominator')
    if not {row.task_id for row in package.execution_resource_envelope_spec.task_cells
            if row.native_simulator_launch} <= set(unstarted):
        raise PermissionError('repair continuation requires every future native response to remain unexecuted')
    envelope = _resources(recovery, package, plan, predecessor, receipts, terminal)
    task, = (row for row in plan.tasks if row.task_id == failed)
    candidate, = predecessor.task(failed).attempts
    failure = recovery.read_event(predecessor, candidate.event_relative_path)
    if (task.capability.capability_key not in (
                'matrix-e3-configured-protected.retained-fit',
                'matrix-e3-configured-protected.retained-model-freeze',
                'matrix-e3-configured-protected.retained-forecast')
            or task.maximum_attempts != 1 or failure is None or failure.failure is None
            or failure.failure.failure_class.value not in ('RETRY_EXHAUSTION', 'PROVIDER_RUNNER_DEFECT')
            or ExternalTaskReceiptStore(service.artifact_plane).read(run_id, failed, candidate.attempt_id) is not None):
        raise PermissionError('repair continuation requires a known failed PURE adoption without a receipt')
    provider = service._resolve_campaign_provider(package, authorization_replayed=True).provider
    preparations = service._worker_preparation_contracts(provider=provider, package=package, execution_plan=plan)
    semantic_plane = service._semantic_artifact_plane(plan, provider.output_semantic_contracts(package.registry, plan))
    declaration, = (row for row in preparations if row.selection.capability_key == task.capability.capability_key)
    failed_cell = package.execution_resource_envelope_spec.cell_for_task(failed)
    if declaration.native_effect or failed_cell.native_simulator_launch or failed_cell.physical_execution_cost:
        raise PermissionError('repair continuation refuses native or effectful failed work')
    config = original_scope.retained_task_config(failed)
    expected = {}
    for output in config.original_task.outputs:
        physical, = (row for row in config.original_receipt.output_materializations
            if row.logical_artifact_id == output.logical_artifact_id)
        expected[output.output_id] = physical.size_bytes, physical.physical_sha256
    manifests = []
    for output in task.outputs:
        refresh()
        paths = (output.relative_path, output.relative_path + '.manifest.json')
        if not any(service.artifact_plane.root.resolve(path, for_write=False).exists() for path in paths):
            continue
        manifest = service.artifact_plane.read_manifest(output.relative_path)
        logical, physical = manifest.logical, manifest.materialization
        if ((logical.logical_artifact_id, logical.payload_schema, logical.profile, logical.media_type,
                logical.visibility_ceiling, logical.outcome_access, physical.relative_path, physical.storage_root_id,
                physical.size_bytes, physical.physical_sha256) != (
                output.logical_artifact_id, output.payload_schema, output.profile, output.media_type,
                output.visibility_ceiling, output.outcome_access, output.relative_path, service.artifact_plane.root.contract.storage_root_id,
                *expected[output.output_id])):
            raise PermissionError('repair continuation changes the exact already-copied original model bytes')
        semantic_plane.verify_manifest_members(manifest,
            validate_members=lambda _members: None, before_member=refresh)
        refresh()
        manifests.append(manifest)
    pending = {failed, *unstarted}
    for row in plan.tasks:
        if row.task_id not in pending:
            continue
        spec = package.execution_resource_envelope_spec.cell_for_task(row.task_id)
        state = envelope.cell(spec.cell_id)
        if row.task_id != failed:
            if state.state is not ExecutionResourceEnvelopeState.ISSUED or state.attempt_ids:
                raise PermissionError('repair continuation refuses entered or uncertain pending work')
            if any(service.artifact_plane.root.resolve(path, for_write=False).exists()
                    for output in row.outputs for path in (output.relative_path, output.relative_path + '.manifest.json')):
                raise PermissionError('repair continuation refuses unreceipted pending output')
        contacts = ExternalNativeEffectContactStore(plane=service.artifact_plane, execution_plan=_pin(plan, 'execution_plan_id'),
            visibility_ceiling=VisibilityCeiling.most_restrictive(*(output.visibility_ceiling for output in row.outputs)),
            outcome_access=most_restrictive_outcome_access(row.capability.requested_outcome_access,
                *(output.outcome_access for output in row.outputs)))
        if contacts.read(run_id, row.task_id) is not None:
            raise PermissionError('repair continuation refuses every prior native contact')
    previous_controller = selected_controller(service.artifact_plane, predecessor)
    worker, environment = observe_frozen_repair_worker(interpreter=original_repair.worker_environment.interpreter_path,
        source_root=original_repair.worker_source_root)
    package_root = observe_frozen_worker_package_root(environment)
    controller = implementation_binding(service.repo_root)
    if (worker != original_repair.worker or environment != original_repair.worker_environment
            or controller.observed_git_head == previous_controller.observed_git_head):
        raise PermissionError('repair continuation substitutes the frozen worker or lacks a repaired installation')
    require_numerical_source_continuity(worker, controller)
    proof = RetainedE3RepairContinuationV2(repair_id, owner_instruction_sha256, original_repair.identity,
        _pin(predecessor, 'recovery_index_id'), _pin(terminal, 'terminal_event_id'), _pin(failure, 'event_id'),
        _pin(envelope, 'envelope_id'), previous_controller, failed,
        tuple(sorted(manifests, key=lambda row: row.materialization.relative_path)), controller, package_root,
        tuple(sorted((key, _pin(receipt, 'receipt_id')) for key, receipt in receipts.items())), unstarted)
    index = RetainedE3ContinuedRepairRecoveryIndex.derive(plan, predecessor, proof)
    _require_repair_catalog(service, index)
    RunExecutionResourceEnvelopeMachine.repair_pure_task(envelope,
        event_id='resource-repair.' + proof.repair_id, occurred_at_utc=now,
        cell_id=package.execution_resource_envelope_spec.cell_for_task(failed).cell_id, repair=proof.identity)
    refresh()
    return proof, index


def publish_repair_continuation(*, service, proof, index):
    if index.repair_continuation != proof or implementation_binding(service.repo_root) != proof.controller:
        raise PermissionError('repair continuation changes its selected derived controller')
    relative = repair_continuation_relative_path(index.predecessor)
    service.artifact_plane.write(ArtifactWriteRequest(proof.repair_id, relative, proof.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, 'application/json', 'retained-e3-repair-continuation.' + index.run_id,
        relative.rsplit('/', 1)[0], proof.canonical_bytes(), VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND))
    ExternalRunRecoveryStore(service.artifact_plane).freeze(index)


def continuation_resource_coordinator(*, writer, package, index):
    proof = index.repair_continuation
    original = ExternalRunRecoveryStore(writer).reconstruct_execution_resource_envelope(index=index.predecessor,
        envelope_id='run-resource-envelope.' + index.run_id, spec=package.execution_resource_envelope_spec,
        execution_plan=index.execution_plan, jit_graph_signature_manifest=package.jit_graph_signature_manifest)
    if _pin(original, 'envelope_id') != proof.previous_resource_envelope:
        raise PermissionError('repair continuation changes its complete failed-repair resource history')
    store = ExternalExecutionResourceEnvelopeStore(writer.root, artifact_plane=writer,
        state_root_relative_path=index.resource_envelope_event_root_relative_path)
    coordinator = DurableExecutionResourceEnvelopeCoordinator(store)
    current = coordinator.ensure_checkpoint(original, jit_graph_signature_manifest=package.jit_graph_signature_manifest)
    event_id = 'resource-repair.' + proof.repair_id
    existing = tuple(row for row in current.events if row.event_id == event_id)
    if not existing:
        if current != original:
            raise PermissionError('repair continuation resource journal changed before its single PURE repair')
        updated = RunExecutionResourceEnvelopeMachine.repair_pure_task(current, event_id=event_id,
            occurred_at_utc=datetime.now(UTC).isoformat().replace('+00:00', 'Z'),
            cell_id=package.execution_resource_envelope_spec.cell_for_task(proof.failed_task_id).cell_id,
            repair=proof.identity)
        store.compare_and_append(expected=current, updated=updated)
    elif len(existing) != 1 or existing[0].recovery_proof != proof.identity:
        raise PermissionError('repair continuation resource journal substitutes its repair')
    return coordinator
