# SPDX-License-Identifier: MPL-2.0
"""Supported, single PURE-adoption repair with an unchanged scientific worker.

This controller transition leaves the issued package, original FAILED terminal,
attempt budgets, scientific configurations and worker installation untouched.
Use a separate selected catalog projection and an additional resource journal.
"""
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
import os

from empirical_lawhood.adapters.methods.matrix_factor_response.configured_retained_execution import require_numerical_source_continuity
from empirical_lawhood.infrastructure.bounded_process import run_bounded_command
from empirical_lawhood.infrastructure.execution import DurableExecutionResourceEnvelopeCoordinator, LocalProcessExecutor
from empirical_lawhood.infrastructure.execution_resource_envelopes import ExternalExecutionResourceEnvelopeStore
from empirical_lawhood.infrastructure.recovery import ExternalRunRecoveryStore
from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest, most_restrictive_outcome_access
from empirical_lawhood.runtime.execution_envelope import ExecutionResourceEnvelopeState, RunExecutionResourceEnvelopeMachine
from empirical_lawhood.runtime.prepared_native_invocation import PreparedWorkerEnvironment
from empirical_lawhood.runtime.recursive_handoff import RecursiveImplementationBinding
from empirical_lawhood.runtime.recovery import RunRecoveryIndex
from empirical_lawhood.runtime.retained_e3_repair import RetainedE3ControlRepair, RetainedE3RepairRecoveryIndex, RetainedE3ControllerAdmission, RetainedE3ControllerInputReuseAdmission, RetainedE3ControllerRetainedScopeAdmission, RetainedE3ContinuedRepairRecoveryIndex

from .configured_e3_retained_custody import _resources
from .current_result_custody import require_current_result_reveal_authority
from .recursive_authoring import implementation_binding


def _pin(value, name):
    return ObjectIdentity.from_record(getattr(value, name), value)


def repair_relative_path(run_id):
    from empirical_lawhood.kernel.serialization import validate_stable_id
    validate_stable_id(run_id)
    return f'runs/{run_id}/repairs/retained-e3-control-lane/repair.json'


def _read_record(writer, relative, kind, *, record_versions=()):
    raw = ExternalRunRecoveryStore(writer)._read_payload(relative, expected_schema=kind.SCHEMA,
        maximum_bytes=writer.custody_limits.recovery_index_bytes)
    if raw is None:
        return None
    if record_versions:
        from json import loads
        version = loads(raw).get('version')
        choices = (kind, *record_versions)
        selected = tuple(row for row in choices if row.SCHEMA == kind.SCHEMA and row.VERSION == version)
        if len(selected) != 1:
            raise PermissionError('retained E3 repair control has an unsupported record revision')
        kind, = selected
    value = decode_canonical_bytes(raw, kind, maximum_bytes=len(raw))
    if value.canonical_bytes() != raw:
        raise PermissionError('retained E3 repair control changes its canonical bytes')
    return value


def read_retained_e3_control_repair(*, writer, plan, predecessor):
    """Authenticate the additive control and its immutable original failure."""
    repair = _read_record(writer, repair_relative_path(predecessor.run_id), RetainedE3ControlRepair)
    if repair is None:
        return None
    index = RetainedE3RepairRecoveryIndex.derive(plan, predecessor, repair)
    recovery = ExternalRunRecoveryStore(writer)
    terminal = recovery.read_terminal(predecessor)
    if (recovery.read_index(predecessor.index_relative_path, expected_schema=predecessor.SCHEMA) != predecessor
            or terminal is None or _pin(terminal, 'terminal_event_id') != repair.original_terminal
            or terminal.operational_status != 'FAILED' or terminal.failed_task_ids != (repair.failed_task_id,)
            or terminal.completed_task_ids != tuple(key for key, _ in repair.completed_receipts)
            or terminal.blocked_task_ids != repair.unstarted_task_ids):
        raise PermissionError('retained E3 repair loses its exact original failed terminal')
    candidate, = predecessor.task(repair.failed_task_id).attempts
    event = recovery.read_event(predecessor, candidate.event_relative_path)
    if event is None or _pin(event, 'event_id') != repair.original_failure:
        raise PermissionError('retained E3 repair substitutes its original failed attempt')
    return index


def selected_repair_index(*, writer, plan, predecessor):
    index = read_retained_e3_control_repair(writer=writer, plan=plan, predecessor=predecessor)
    if index is not None and ExternalRunRecoveryStore(writer).read_index(
            index.index_relative_path, expected_schema=index.SCHEMA) != index:
        raise PermissionError('retained E3 repair changes its derived additional wave')
    if index is None:
        return predecessor
    from .retained_e3_repair_continuation import read_repair_continuation
    while True:
        selected = read_repair_continuation(writer=writer, plan=plan, predecessor=index)
        if selected is index:
            return index
        if ExternalRunRecoveryStore(writer).read_index(
                selected.index_relative_path, expected_schema=selected.SCHEMA) != selected:
            raise PermissionError('retained E3 continuation changes its derived wave')
        index = selected


def observe_frozen_repair_worker(*, interpreter, source_root):
    """Observe the selected installed worker without touching scientific inputs."""
    program = (
        'from pathlib import Path; import sys; from dataclasses import replace; '
        'from empirical_lawhood.api.recursive_authoring import implementation_binding; '
        'from empirical_lawhood.infrastructure.numerical_provenance import '
        'observe_worker_environment, selected_worker_environment; '
        'print(implementation_binding(Path(sys.argv[1])).canonical_bytes().decode()); '
        'print(replace(observe_worker_environment(), '
        'selected_environment=selected_worker_environment()).canonical_bytes().decode())')
    result = run_bounded_command([str(interpreter), '-I', '-B', '-c', program, str(source_root)],
        environment=os.environ, timeout_seconds=60, maximum_stdout_bytes=4 * 1024 * 1024,
        maximum_stderr_bytes=64 * 1024)
    if result.returncode != 0:
        raise PermissionError('retained E3 repair cannot authenticate its frozen installed worker')
    rows = tuple(row for row in result.stdout.splitlines(keepends=True) if row.strip())
    if len(rows) != 2:
        raise PermissionError('retained E3 worker observation is not the exact bounded pair')
    return (decode_canonical_bytes(rows[0], RecursiveImplementationBinding, maximum_bytes=len(rows[0])),
        decode_canonical_bytes(rows[1], PreparedWorkerEnvironment, maximum_bytes=len(rows[1])))


def observe_frozen_worker_package_root(environment):
    program = ('from pathlib import Path; from empirical_lawhood.infrastructure import execution; '
        'print(Path(execution.__file__).resolve().parents[2])')
    result = run_bounded_command([environment.interpreter_path, '-I', '-B', '-c', program],
        environment=os.environ, timeout_seconds=60, maximum_stdout_bytes=16 * 1024,
        maximum_stderr_bytes=64 * 1024)
    rows = result.stdout.decode('utf-8').splitlines()
    if result.returncode != 0 or len(rows) != 1:
        raise PermissionError('retained E3 cannot observe its frozen worker package location')
    root = Path(rows[0])
    if not root.is_absolute() or root != root.resolve(strict=True) or not root.is_relative_to(environment.prefix):
        raise PermissionError('retained E3 worker package leaves its selected interpreter prefix')
    return str(root)


def reuse_frozen_provider_input(*, writer, run_id, spec, request, require_access=None):
    """Read an existing frozen input, preserving its actual producing stamp.

    An installed NumPy RECORD can differ despite an unchanged dependency lock.
    That affects a new publication's validation provenance, not the original
    input's bytes. Authenticate the frozen metadata, run the current format
    validator and compare every incoming source chunk under the publication's
    before/after snapshot. No new input or validation stamp is published.
    """
    from .current_task_custody import _require_provider_input_manifest
    from empirical_lawhood.runtime.artifacts import ArtifactStreamWriteRequest
    if type(request) is not ArtifactStreamWriteRequest or not callable(require_access):
        raise TypeError('retained E3 input reuse requires its exact stream and current access guard')
    request.__post_init__()

    def refresh(_manifest=None):
        require_access()

    refresh()
    manifest = writer.read_manifest(request.relative_path)
    _require_provider_input_manifest(writer, run_id, spec, manifest,
        authenticated_size_bytes=request.expected_size_bytes)
    logical, physical = manifest.logical, manifest.materialization
    if ((logical.profile, logical.parent_visibility_ceilings, logical.lineage_parents,
            logical.content_sha256, physical.physical_sha256, logical.semantic_validation) !=
            (request.profile, request.parent_visibility_ceilings, request.lineage_parents,
                request.logical_content_sha256 or request.expected_physical_sha256,
                request.expected_physical_sha256, request.semantic_validation)):
        raise PermissionError('retained E3 input reuse changes its original payload or lineage')

    def consume(members):
        if members.get(request.relative_path) != manifest:
            raise PermissionError('retained E3 input reuse substitutes its committed member')
        refresh()
        writer._require_replayed_stream(request, physical,
            writer.root.resolve(physical.relative_path, for_write=False))
        refresh()
        return manifest

    return writer.verify_manifest_members(manifest, validate_members=consume, before_member=refresh)


def _controller_admission_path(run_id):
    return repair_relative_path(run_id).rsplit('/', 1)[0] + '/controller-admission.json'


def _input_reuse_admission_path(run_id):
    return repair_relative_path(run_id).rsplit('/', 1)[0] + '/controller-input-reuse-admission.json'


def _retained_scope_admission_path(run_id):
    return repair_relative_path(run_id).rsplit('/', 1)[0] + '/controller-retained-scope-admission.json'


def _controller_admission(writer, index):
    admission = _read_record(writer, _controller_admission_path(index.run_id), RetainedE3ControllerAdmission)
    correction = _read_record(writer, _input_reuse_admission_path(index.run_id), RetainedE3ControllerInputReuseAdmission)
    scope_correction = _read_record(writer, _retained_scope_admission_path(index.run_id), RetainedE3ControllerRetainedScopeAdmission)
    for selected in (admission, correction, scope_correction):
        if selected is None:
            continue
        if (selected.repair != index.repair.identity
                or selected.recovery_index != _pin(index, 'recovery_index_id')
                or selected.owner_instruction_sha256 != index.repair.owner_instruction_sha256):
            raise PermissionError('retained E3 controller admission changes the frozen additional wave')
        require_numerical_source_continuity(index.repair.controller, selected.controller)
    if correction is not None:
        if (admission is None or correction.previous_controller_admission != admission.identity
                or correction.worker_package_root != admission.worker_package_root):
            raise PermissionError('retained E3 input reuse loses its original controller admission')
        require_numerical_source_continuity(admission.controller, correction.controller)
        admission = correction
    if scope_correction is not None:
        if (correction is None or scope_correction.previous_controller_admission != correction.identity
                or scope_correction.worker_package_root != correction.worker_package_root):
            raise PermissionError('retained E3 scope correction loses its input-reuse controller admission')
        require_numerical_source_continuity(correction.controller, scope_correction.controller)
        admission = scope_correction
    return admission


def derive_retained_e3_control_repair(*, service, run_id, repair_id, owner_instruction_sha256,
        worker_interpreter, worker_source_root, reveal_authority_id):
    """Derive the complete selection from actual primary custody, never a roster.

    This does not execute or publish. The existing grant is checked separately
    from the owner-requested PURE retry and installation selection.
    """
    package = service._load_package(run_id)
    plan, predecessor, recovery = service._load_status_index(run_id, package=package)
    if type(predecessor) is not RunRecoveryIndex:
        raise PermissionError('retained E3 repair cannot chain from another repair wave')
    terminal = recovery.read_terminal(predecessor)
    if terminal is None or terminal.operational_status != 'FAILED' or len(terminal.failed_task_ids) != 1:
        raise PermissionError('retained E3 repair needs exactly one immutable failed adoption')
    now = datetime.now(UTC).isoformat().replace('+00:00', 'Z')
    service._validate_campaign_authorization(package)
    service._validate_issued_execution_authority(package, at_utc=now)
    reveal = require_current_result_reveal_authority(writer=service.artifact_plane, package=package,
        reveal_authority_id=reveal_authority_id)
    closure = recovery._reconcile_terminal(index=predecessor, plan=plan, terminal=terminal,
        repository=None, receipt_store=ExternalTaskReceiptStore(service.artifact_plane),
        existing={}, candidate_count=len(plan.tasks))
    receipts = {row.task_id: row for row in closure.recovered_receipts}
    envelope = _resources(recovery, package, plan, predecessor, receipts, terminal)
    failed, = terminal.failed_task_ids
    task, = (row for row in plan.tasks if row.task_id == failed)
    cell = package.execution_resource_envelope_spec.cell_for_task(failed)
    preparations = service._worker_preparation_contracts(provider=service._resolve_campaign_provider(
        package, authorization_replayed=True).provider, package=package, execution_plan=plan)
    declaration, = (row for row in preparations if row.selection.capability_key == task.capability.capability_key)
    if declaration.native_effect or cell.native_simulator_launch or cell.physical_execution_cost:
        raise PermissionError('retained E3 repair refuses any native or uncertain failed work')
    unstarted = tuple(sorted({row.task_id for row in plan.tasks} - {*receipts, failed}))
    if unstarted != terminal.blocked_task_ids:
        raise PermissionError('retained E3 repair changes the original blocked denominator')
    if not {row.task_id for row in package.execution_resource_envelope_spec.task_cells
            if row.native_simulator_launch} <= set(unstarted):
        raise PermissionError('retained E3 repair requires every future native response to remain unexecuted')
    for pending in (row for row in plan.tasks if row.task_id in {*unstarted, failed}):
        state = envelope.cell(package.execution_resource_envelope_spec.cell_for_task(pending.task_id).cell_id)
        if pending.task_id != failed and (state.state is not ExecutionResourceEnvelopeState.ISSUED
                or state.attempt_ids or state.current_attempt_id is not None):
            raise PermissionError('retained E3 repair refuses entered or uncertain pending work')
        for output in pending.outputs:
            if any(service.artifact_plane.root.resolve(path, for_write=False).exists()
                    for path in (output.relative_path, output.relative_path + '.manifest.json')):
                raise PermissionError('retained E3 repair refuses unreceipted pending output')
        contacts = ExternalNativeEffectContactStore(plane=service.artifact_plane,
            execution_plan=_pin(plan, 'execution_plan_id'),
            visibility_ceiling=VisibilityCeiling.most_restrictive(*(row.visibility_ceiling for row in pending.outputs)),
            outcome_access=most_restrictive_outcome_access(pending.capability.requested_outcome_access,
                *(row.outcome_access for row in pending.outputs)))
        if contacts.read(run_id, pending.task_id) is not None:
            raise PermissionError('retained E3 repair refuses prior native contact')
    worker, environment = observe_frozen_repair_worker(interpreter=worker_interpreter, source_root=worker_source_root)
    controller = implementation_binding(service.repo_root)
    require_numerical_source_continuity(worker, controller)
    candidate, = predecessor.task(failed).attempts
    failure = recovery.read_event(predecessor, candidate.event_relative_path)
    if (failure is None or failure.failure is None
            or failure.failure.sanitized_exception_type != 'PermissionError'
            or failure.failure.failure_class.value != 'RETRY_EXHAUSTION'):
        raise PermissionError('retained E3 repair requires its known pre-worker custody failure')
    repair = RetainedE3ControlRepair(repair_id, owner_instruction_sha256,
        _pin(plan, 'execution_plan_id'), _pin(predecessor, 'recovery_index_id'),
        _pin(terminal, 'terminal_event_id'), _pin(envelope, 'envelope_id'), failed,
        _pin(failure, 'event_id'), _pin(reveal, 'authority_id'),
        tuple((key, _pin(receipts[key], 'receipt_id')) for key in sorted(receipts)),
        unstarted, controller, worker, environment, str(Path(worker_source_root).absolute()))
    index = RetainedE3RepairRecoveryIndex.derive(plan, predecessor, repair)
    _require_repair_catalog(service, index)
    RunExecutionResourceEnvelopeMachine.repair_pure_task(envelope,
        event_id='resource-repair.' + repair.repair_id, occurred_at_utc=now,
        cell_id=cell.cell_id, repair=repair.identity)
    return repair, index, envelope


def publish_retained_e3_control_repair(*, service, repair, index, original_envelope):
    """Publish additive custody, preserving all old publications and journals."""
    if index.repair != repair or _pin(original_envelope, 'envelope_id') != repair.original_resource_envelope:
        raise PermissionError('retained E3 repair publication changes its derived original history')
    fresh, fresh_index, fresh_envelope = derive_retained_e3_control_repair(service=service,
        run_id=index.run_id, repair_id=repair.repair_id,
        owner_instruction_sha256=repair.owner_instruction_sha256,
        worker_interpreter=repair.worker_environment.interpreter_path,
        worker_source_root=repair.worker_source_root,
        reveal_authority_id=repair.reveal_authority.object_id)
    if (fresh, fresh_index, fresh_envelope) != (repair, index, original_envelope):
        raise PermissionError('retained E3 repair changed between derivation and publication')
    writer = service.artifact_plane
    relative = repair_relative_path(index.run_id)
    writer.write(ArtifactWriteRequest(repair.repair_id, relative, repair.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, 'application/json', 'retained-e3-repair.' + index.run_id,
        relative.rsplit('/', 1)[0], repair.canonical_bytes(), VisibilityCeiling.PROSPECTIVE, (),
        OutcomeAccess.OUTCOME_BLIND))
    ExternalRunRecoveryStore(writer).freeze(index)
    return repair.identity


def _require_repair_catalog(service, index):
    from empirical_lawhood.infrastructure.sql import SQLiteOperationalRepository
    engine = service.engine_factory()
    try:
        repository = SQLiteOperationalRepository(engine)
        candidates = {row.attempt_id for task in index.tasks for row in task.attempts}
        if any(row.attempt_id not in candidates for row in repository.attempts(index.run_id)):
            raise PermissionError('retained E3 repair requires a separate selected catalog projection')
        service._require_no_live_run_lease(repository, index.run_id)
    finally:
        engine.dispose()


def repair_resource_coordinator(*, writer, package, plan, index):
    """Seed a separate replay-verified journal, then append the explicit repair."""
    if type(index) is RetainedE3ContinuedRepairRecoveryIndex:
        from .retained_e3_repair_continuation import continuation_resource_coordinator
        return continuation_resource_coordinator(writer=writer, package=package, index=index)
    recovery = ExternalRunRecoveryStore(writer)
    original = recovery.reconstruct_execution_resource_envelope(index=index.predecessor,
        envelope_id='run-resource-envelope.' + index.run_id,
        spec=package.execution_resource_envelope_spec, execution_plan=index.execution_plan,
        jit_graph_signature_manifest=package.jit_graph_signature_manifest)
    if _pin(original, 'envelope_id') != index.repair.original_resource_envelope:
        raise PermissionError('retained E3 repair changes its original resource history')
    store = ExternalExecutionResourceEnvelopeStore(writer.root, artifact_plane=writer,
        state_root_relative_path=index.resource_envelope_event_root_relative_path)
    coordinator = DurableExecutionResourceEnvelopeCoordinator(store)
    current = coordinator.ensure_checkpoint(original, jit_graph_signature_manifest=package.jit_graph_signature_manifest)
    event_id = 'resource-repair.' + index.repair.repair_id
    existing = tuple(row for row in current.events if row.event_id == event_id)
    if not existing:
        if current != original:
            raise PermissionError('retained E3 repair journal changed before its repair transition')
        updated = RunExecutionResourceEnvelopeMachine.repair_pure_task(current, event_id=event_id,
            occurred_at_utc=datetime.now(UTC).isoformat().replace('+00:00', 'Z'),
            cell_id=package.execution_resource_envelope_spec.cell_for_task(index.repair.failed_task_id).cell_id,
            repair=index.repair.identity)
        store.compare_and_append(expected=current, updated=updated)
    elif len(existing) != 1 or existing[0].recovery_proof != index.repair.identity:
        raise PermissionError('retained E3 repair journal substitutes its transition')
    return coordinator


@contextmanager
def retained_e3_control_repair(service, *, run_id, owner_instruction_sha256=None):
    """Bind a repaired controller and the separately frozen producing worker."""
    package = service._load_package(run_id)
    plan = service._load_status_execution_plan(run_id)
    predecessor = RunRecoveryIndex.from_execution_plan(plan, run_id=run_id,
        wave_id='wave.' + package.package_id, authority_identities=tuple(sorted((
            _pin(package.scientific_approval, 'authorization_id'),
            _pin(package.execution_authority, 'authority_id')), key=lambda row: row.object_id)))
    index = selected_repair_index(writer=service.artifact_plane, plan=plan, predecessor=predecessor)
    if type(index) not in (RetainedE3RepairRecoveryIndex, RetainedE3ContinuedRepairRecoveryIndex):
        raise PermissionError('retained E3 execution requires its explicitly published repair')
    repair = index.repair
    _require_repair_catalog(service, index)
    worker, environment = observe_frozen_repair_worker(interpreter=repair.worker_environment.interpreter_path,
        source_root=repair.worker_source_root)
    if worker != repair.worker or environment != repair.worker_environment:
        raise PermissionError('retained E3 repair installation changed before execution')
    controller = implementation_binding(service.repo_root)
    package_root = observe_frozen_worker_package_root(environment)
    admission = (index.repair_continuation if type(index) is RetainedE3ContinuedRepairRecoveryIndex
        else _controller_admission(service.artifact_plane, index))
    expected = repair.controller if admission is None else admission.controller
    if controller != expected or admission is not None and admission.worker_package_root != package_root:
        raise PermissionError('retained E3 controller changed; select an explicit repair through experiment-recover')
    previous = getattr(service, '_retained_e3_control_repair', None)
    if previous is not None:
        raise PermissionError('retained E3 repair cannot overlap another control transition')
    previous_executor = service.executor
    if type(previous_executor) is not LocalProcessExecutor:
        raise PermissionError('retained E3 frozen worker requires its supported local process executor')
    selected_executor = LocalProcessExecutor(scratch_root=previous_executor._scratch_root,
        worker_environment=environment, worker_package_root=package_root)
    service._retained_e3_control_repair = index
    service._retained_e3_controller_admission = admission
    service.executor = selected_executor
    try:
        yield index
    finally:
        service.executor = previous_executor
        service._retained_e3_controller_admission = None
        service._retained_e3_control_repair = previous
