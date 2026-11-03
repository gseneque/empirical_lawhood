# SPDX-License-Identifier: MPL-2.0
"""Derive and authenticate a PURE output-budget repair from primary custody."""
from hashlib import sha256

from empirical_lawhood.infrastructure.recovery import ExternalRunRecoveryStore
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes, validate_stable_id
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.runtime.development_output_repair import DevelopmentOutputBudgetRepair, DevelopmentOutputRepairRecoveryIndex
from empirical_lawhood.runtime.recovery import DevelopmentRunRecoveryIndex

from .retained_e3_control_repair import _read_record, observe_frozen_repair_worker, observe_frozen_worker_package_root


def repair_relative_path(run_id):
    validate_stable_id(run_id)
    return f'runs/{run_id}/repairs/development-output-budget/repair.json'


def _pin(value, field):
    return ObjectIdentity.from_record(getattr(value, field), value)


def _require_scientific_source(worker, controller):
    """All domain and kernel bytes, plus the lock, remain the original bytes."""
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_retained_execution import require_numerical_source_continuity
    require_numerical_source_continuity(worker, controller)
    for prefix in ('adapters/', 'kernel/'):
        old = {key: value for key, value in worker.package_sources if key.startswith(prefix)}
        new = {key: value for key, value in controller.package_sources if key.startswith(prefix)}
        if not old or old != new:
            raise PermissionError('development output repair changes original scientific source: ' + prefix)


def _original_census(*, writer, plan, predecessor, require_absent):
    """No replacement roster: derive all sets from the complete old terminal."""
    from .recursive_operations import operation_catalog
    from empirical_lawhood.runtime.recovery import TaskRecoveryDisposition
    from empirical_lawhood.runtime.execution import OperationalFailureClass

    if type(predecessor) is not DevelopmentRunRecoveryIndex:
        raise PermissionError('development output repair accepts only an original development wave')
    predecessor.validate_plan(plan)
    recovery = ExternalRunRecoveryStore(writer)
    if recovery.read_index(predecessor.index_relative_path, expected_schema=predecessor.SCHEMA) != predecessor:
        raise PermissionError('development output repair changes its original frozen index')
    terminal = recovery.read_terminal(predecessor)
    if terminal is None or terminal.operational_status != 'BLOCKED' or terminal.failed_task_ids:
        raise PermissionError('development output repair requires a settled resource-blocked terminal')
    store = ExternalTaskReceiptStore(writer)
    closure = recovery._reconcile_terminal(index=predecessor, plan=plan, terminal=terminal,
        repository=None, receipt_store=store, existing={}, candidate_count=sum(len(row.attempts) for row in predecessor.tasks),
        require_complete_events=True)
    receipts = {row.task_id: row for row in closure.recovered_receipts}
    if tuple(sorted(receipts)) != terminal.completed_task_ids:
        raise PermissionError('development output repair loses the complete original receipt census')
    registrations, registry, _ = operation_catalog()
    if registry.fingerprint() != plan.registry_sha256:
        raise PermissionError('development output repair changes the original capability registry')
    by_key = {(row.selection.capability_key, row.selection.capability_version): row for row in registrations}
    def registration(task):
        return by_key[task.capability.capability_key, task.capability.capability_version]
    if any((task.capability.capability_key, task.capability.capability_version) not in by_key for task in plan.tasks):
        raise PermissionError('development output repair cannot identify an original capability')
    if any(registration(task).native_effect and task.task_id not in receipts for task in plan.tasks):
        raise PermissionError('development output repair requires every original native task to have completed')
    from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
    contacts = ExternalNativeEffectContactStore(plane=writer, execution_plan=_pin(plan, 'execution_plan_id'),
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE)
    refused, unstarted = [], []
    for task in plan.tasks:
        if task.task_id in receipts:
            continue
        if contacts.read(predecessor.run_id, task.task_id) is not None:
            raise PermissionError('development output repair refuses prior contact for pending PURE work')
        binding = predecessor.task(task.task_id)
        if task.maximum_attempts != 1:
            raise PermissionError('development output repair admits one attempt for each pending PURE calculation')
        candidate, = binding.attempts
        event = recovery.read_event(predecessor, candidate.event_relative_path)
        if event is not None:
            if (event.disposition is not TaskRecoveryDisposition.BLOCKED or event.failure is None
                    or event.failure.failure_class is not OperationalFailureClass.RESOURCE_REFUSAL
                    or event.failure.sanitized_exception_type != 'ResourceAdmissionError'):
                raise PermissionError('development output repair refuses non-resource or uncertain attempts')
            refused.append((task.task_id, _pin(event, 'event_id')))
        else:
            event = recovery.read_event(predecessor, binding.nonattempt_event_relative_path)
            if (event is None or event.disposition is not TaskRecoveryDisposition.NOT_ATTEMPTED
                    or event.reason_codes != ('dependency-blocked',)):
                raise PermissionError('development output repair requires authentic unstarted dependency blocks')
            unstarted.append(task.task_id)
        if require_absent:
            for output in task.outputs:
                for relative in (output.relative_path, output.relative_path + '.manifest.json'):
                    path = writer.root.resolve(relative, for_write=False)
                    if path.exists() or path.is_symlink():
                        raise PermissionError('development output repair refuses unreceipted original output')
    if not refused or set(terminal.blocked_task_ids) != {*dict(refused), *unstarted}:
        raise PermissionError('development output repair changes the complete original blocked denominator')
    completed = tuple(sorted((key, _pin(value, 'receipt_id')) for key, value in receipts.items()))
    return terminal, tuple(sorted(refused)), completed, tuple(sorted(unstarted))


def select_development_output_repair(*, writer, plan, predecessor):
    """Read the additive repair without changing any original publication."""
    from .native_continuation_execution import select_native_continuation
    continued = select_native_continuation(writer=writer, plan=plan, predecessor=predecessor)
    if continued is not predecessor:
        return continued
    repair = _read_record(writer, repair_relative_path(predecessor.run_id), DevelopmentOutputBudgetRepair)
    if repair is None:
        from .development_controller_repair import select_development_controller_repair
        return select_development_controller_repair(writer=writer, plan=plan, predecessor=predecessor)
    from .development_controller_repair import repair_relative_path as controller_path
    if writer.root.resolve(controller_path(predecessor.run_id), for_write=False).exists():
        raise PermissionError('development repair cannot select two replacement controllers')
    index = DevelopmentOutputRepairRecoveryIndex.derive(plan, predecessor, repair)
    terminal, refused, completed, unstarted = _original_census(writer=writer, plan=plan,
        predecessor=predecessor, require_absent=False)
    if (repair.original_terminal != _pin(terminal, 'terminal_event_id')
            or repair.refused_tasks != refused or repair.completed_receipts != completed
            or repair.unstarted_task_ids != unstarted):
        raise PermissionError('development output repair substitutes original outcomes or receipt identities')
    _require_scientific_source(repair.worker, repair.controller)
    if ExternalRunRecoveryStore(writer).read_index(index.index_relative_path, expected_schema=index.SCHEMA) != index:
        raise PermissionError('development output repair loses its separately derived recovery wave')
    return index


def derive_development_output_repair(*, writer, plan, predecessor, original_source, controller,
        owner_instruction_sha256, output_bytes, worker_interpreter, worker_source_root):
    """Caller holds the actual run lock and current original-input read scope."""
    terminal, refused, completed, unstarted = _original_census(writer=writer, plan=plan,
        predecessor=predecessor, require_absent=True)
    worker, environment = observe_frozen_repair_worker(interpreter=worker_interpreter, source_root=worker_source_root)
    if worker != original_source:
        raise PermissionError('development output repair substitutes the original frozen worker installation')
    _require_scientific_source(worker, controller)
    token = sha256(canonical_json_bytes((predecessor.fingerprint(), controller, owner_instruction_sha256, output_bytes))).hexdigest()
    repair = DevelopmentOutputBudgetRepair('repair.development-output.' + token[:24], owner_instruction_sha256,
        _pin(plan, 'execution_plan_id'), _pin(predecessor, 'recovery_index_id'), _pin(terminal, 'terminal_event_id'),
        refused, completed, unstarted, output_bytes, controller, worker, environment, str(worker_source_root))
    from .recursive_operations import operation_catalog
    registrations, _, _ = operation_catalog()
    ceilings = {(row.selection.capability_key, row.selection.capability_version): row.resource_ceiling for row in registrations}
    for task_id, _ in refused:
        task = repair.task(plan.task(task_id))
        if not ceilings[task.capability.capability_key, task.capability.capability_version].contains(task.capability.requested_resources):
            raise PermissionError('development output repair exceeds the original capability resource ceiling')
    index = DevelopmentOutputRepairRecoveryIndex.derive(plan, predecessor, repair)
    return repair, index


def publish_development_output_repair(*, writer, repair, index):
    if type(index) is not DevelopmentOutputRepairRecoveryIndex or index.repair != repair:
        raise PermissionError('development output repair changes its derived recovery index')
    ExternalRunRecoveryStore(writer).freeze(index)
    relative = repair_relative_path(index.run_id)
    writer.write(ArtifactWriteRequest(repair.repair_id, relative, repair.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, 'application/json', 'development-output-repair.' + index.run_id,
        relative.rsplit('/', 1)[0], repair.canonical_bytes(), VisibilityCeiling.DEVELOPMENT_ONLY,
        (), OutcomeAccess.DEVELOPMENT_VISIBLE))


def authenticate_repair_controller(*, index, source, controller):
    from empirical_lawhood.runtime.native_continuation_execution import DevelopmentNativeContinuationRecoveryIndex
    if type(index) is DevelopmentNativeContinuationRecoveryIndex:
        from .native_continuation_execution import authenticate_controller
        return authenticate_controller(index=index, source=source, controller=controller)
    from empirical_lawhood.runtime.development_controller_repair import DevelopmentControllerRepairRecoveryIndex
    if type(index) is DevelopmentControllerRepairRecoveryIndex:
        from .development_controller_repair import authenticate_controller
        return authenticate_controller(index=index, source=source, controller=controller)
    if type(index) is not DevelopmentOutputRepairRecoveryIndex:
        raise TypeError('development output repair requires its typed selected recovery index')
    repair = index.repair
    if (source, controller) != (repair.worker, repair.controller):
        raise PermissionError('development output repair changes the selected controller or original worker')
    _require_scientific_source(source, controller)
    worker, environment = observe_frozen_repair_worker(interpreter=repair.worker_environment.interpreter_path,
        source_root=repair.worker_source_root)
    if (worker, environment) != (repair.worker, repair.worker_environment):
        raise PermissionError('development output repair changes the live frozen worker environment')
    return observe_frozen_worker_package_root(environment)


def repair_report(index):
    from empirical_lawhood.runtime.native_continuation_execution import DevelopmentNativeContinuationRecoveryIndex
    if type(index) is DevelopmentNativeContinuationRecoveryIndex:
        from .native_continuation_execution import repair_report as continuation_report
        return continuation_report(index)
    from empirical_lawhood.runtime.development_controller_repair import DevelopmentControllerRepairRecoveryIndex
    if type(index) is DevelopmentControllerRepairRecoveryIndex:
        from .development_controller_repair import repair_report as controller_report
        return controller_report(index)
    if type(index) is not DevelopmentOutputRepairRecoveryIndex:
        return {}
    return {'operational_output_budget_repair': {
        'repair': index.repair.identity.to_document(),
        'original_terminal': index.repair.original_terminal.to_document(),
        'refused_calculations': len(index.repair.refused_tasks),
        'retained_successful_receipts': len(index.repair.completed_receipts),
        'output_bytes_per_repaired_calculation': index.repair.output_bytes,
        'native_acquisition_authority': 'NONE'}}


def recover_development_output_budget(*, service, directory, run_id, output_bytes,
        owner_instruction_sha256, worker_interpreter, worker_source_root,
        maximum_parallel_tasks, read_access=None):
    """Public recovery owner; preparation cannot overlap the original run."""
    from .recursive_authoring import implementation_binding, load_authored_wave
    from .recursive_execution import _retained_plans, run_recursive_wave
    from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
    from empirical_lawhood.infrastructure.run_source_admission import _capture_source
    from empirical_lawhood.infrastructure.source_closure import require_admitted_target_source_current

    writer = service.artifact_writer
    _, draft, source, payloads = load_authored_wave(directory=directory, artifact_writer=writer,
        lazy_payloads=True, require_initial_experiment=True, read_access=read_access)
    run, plan, index = _retained_plans(payloads, draft)
    if run.run_plan_id != run_id:
        raise PermissionError('development output repair changes its selected original run')
    admission = _capture_source(service.project_root)
    controller = implementation_binding(service.project_root, _admitted_source=admission)
    contacts = ExternalNativeEffectContactStore(plane=writer,
        execution_plan=_pin(plan, 'execution_plan_id'), visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY,
        outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE)
    access = getattr(payloads, 'original_input_access', None)
    with contacts.execution_lock(run_id):
        if access is not None:
            access.require_current()
        if type(index) is DevelopmentOutputRepairRecoveryIndex:
            proof = index.repair
            if (proof.output_bytes, proof.owner_instruction_sha256, proof.worker_environment.interpreter_path,
                    proof.worker_source_root) != (output_bytes, owner_instruction_sha256,
                    str(worker_interpreter), str(worker_source_root)):
                raise PermissionError('existing development output repair cannot receive another reservation or attempt')
            authenticate_repair_controller(index=index, source=source, controller=controller)
        else:
            proof, index = derive_development_output_repair(writer=writer, plan=plan, predecessor=index,
                original_source=source, controller=controller, owner_instruction_sha256=owner_instruction_sha256,
                output_bytes=output_bytes, worker_interpreter=worker_interpreter, worker_source_root=worker_source_root)
            require_admitted_target_source_current(service.project_root, admission)
            if access is not None:
                access.require_current()
            publish_development_output_repair(writer=writer, repair=proof, index=index)
        require_admitted_target_source_current(service.project_root, admission)
        if access is not None:
            access.require_current()
    return run_recursive_wave(directory=directory, project_root=service.project_root,
        artifact_writer=writer, maximum_parallel_tasks=maximum_parallel_tasks,
        require_initial_experiment=True, read_access=read_access)
