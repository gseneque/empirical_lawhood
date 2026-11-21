# SPDX-License-Identifier: MPL-2.0
"""Repair exhausted PURE scratch refusals while preserving every original attempt."""
from hashlib import sha256

from empirical_lawhood.api.development_controller_repair import _contacts
from empirical_lawhood.api.development_output_repair import _pin
from empirical_lawhood.api.retained_e3_control_repair import _read_record, observe_frozen_repair_worker, observe_frozen_worker_package_root
from empirical_lawhood.execution.development_scratch_repair import DevelopmentScratchRepair, DevelopmentScratchRepairRecoveryIndex
from empirical_lawhood.execution.execution import OperationalFailureClass
from empirical_lawhood.execution.recovery import DevelopmentRunRecoveryIndex, TaskRecoveryDisposition
from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.records.serialization import canonical_json_bytes, validate_stable_id
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.storage.recovery import ExternalRunRecoveryStore
from empirical_lawhood.storage.task_receipts import ExternalTaskReceiptStore


def repair_relative_path(run_id):
    validate_stable_id(run_id)
    return f'runs/{run_id}/repairs/development-scratch/repair.json'


def require_scientific_source(worker, controller):
    """Only operational controller packages may change; all science stays exact."""
    if (worker.observed_git_head == controller.observed_git_head
            or worker.dependency_lock_sha256 != controller.dependency_lock_sha256):
        raise PermissionError('scratch repair requires a distinct controller with the original dependency lock')
    operational = ('api/', 'cli/', 'execution/', 'storage/')
    original = tuple(row for row in worker.package_sources if not row[0].startswith(operational))
    current = tuple(row for row in controller.package_sources if not row[0].startswith(operational))
    if not original or original != current:
        raise PermissionError('scratch repair changes original scientific source, registration or package resources')


def _empty_scratch(writer, relative):
    path = writer.root.resolve(relative, for_write=False)
    if path.is_symlink() or not path.is_dir() or any(path.iterdir()):
        raise PermissionError('scratch repair requires the retained empty original attempt directory')


def _original_census(*, writer, plan, predecessor, require_absent):
    from empirical_lawhood.api.recursive_execution import _custody_control_pins
    from empirical_lawhood.api.recursive_operations import operation_catalog
    from empirical_lawhood.storage.sql import create_catalog_engine, upgrade_catalog, SQLiteOperationalRepository

    if type(predecessor) is not DevelopmentRunRecoveryIndex:
        raise PermissionError('scratch repair requires the unreplaced original development wave')
    predecessor.validate_plan(plan)
    controls = _custody_control_pins(writer, predecessor)
    recovery = ExternalRunRecoveryStore(writer)
    engine = create_catalog_engine('sqlite+pysqlite:///:memory:')
    try:
        upgrade_catalog(engine)
        closure = recovery.reconcile(predecessor, plan, SQLiteOperationalRepository(engine),
            ExternalTaskReceiptStore(writer), repair_missing_events=False)
    finally:
        engine.dispose()
    terminal = recovery.read_terminal(predecessor)
    if terminal is None or terminal.operational_status != 'BLOCKED' or terminal.failed_task_ids:
        raise PermissionError('scratch repair requires a settled original BLOCKED terminal')
    receipts = {row.task_id: row for row in closure.recovered_receipts}
    registrations, registry, _ = operation_catalog()
    if registry.fingerprint() != plan.registry_sha256:
        raise PermissionError('scratch repair changes the original capability registry')
    declarations = {(row.selection.capability_key, row.selection.capability_version): row for row in registrations}
    contacts = _contacts(writer, plan)
    refused, pending, scratch = [], [], []
    try:
        for task in plan.tasks:
            declaration = declarations[task.capability.capability_key, task.capability.capability_version]
            # This transition is intentionally limited to an entirely PURE graph.
            # A simulator's computation is not an external native-effect contract.
            if declaration.native_effect or contacts.read(predecessor.run_id, task.task_id) is not None:
                raise PermissionError('scratch repair refuses native effects or native contacts')
            if task.task_id in receipts:
                continue
            binding = predecessor.task(task.task_id)
            if binding.maximum_attempts != 1:
                raise PermissionError('scratch repair requires one original attempt per pending calculation')
            candidate, = binding.attempts
            event = recovery.read_event(predecessor, candidate.event_relative_path)
            nonattempt = recovery.read_event(predecessor, binding.nonattempt_event_relative_path)
            if event is not None:
                if (nonattempt is not None or event.disposition is not TaskRecoveryDisposition.BLOCKED
                        or event.reason_codes != ('resource-computability-unavailable',)
                        or event.failure is None or event.failure.failure_class is not OperationalFailureClass.RESOURCE_REFUSAL
                        or event.failure.sanitized_exception_type not in ('ResourceAdmissionError', 'TaskScratchIdentityConflict')):
                    raise PermissionError('scratch repair refuses a different original failure')
                relative = f'scratch/task-execution/{predecessor.run_id}/{candidate.attempt_id}'
                _empty_scratch(writer, relative)
                refused.append((task.task_id, _pin(event, 'event_id')))
                scratch.append((task.task_id, relative))
            else:
                if (nonattempt is None or nonattempt.disposition is not TaskRecoveryDisposition.NOT_ATTEMPTED
                        or nonattempt.reason_codes != ('dependency-blocked',)):
                    raise PermissionError('scratch repair requires the exact unstarted dependent census')
                pending.append(task.task_id)
            if require_absent:
                for output in task.outputs:
                    for relative in (output.relative_path, output.relative_path + '.manifest.json'):
                        path = writer.root.resolve(relative, for_write=False)
                        if path.exists() or path.is_symlink():
                            raise PermissionError('scratch repair refuses unreceipted original output')
        if (not receipts or not refused or set(terminal.completed_task_ids) != set(receipts)
                or set(terminal.blocked_task_ids) != {*dict(refused), *pending}):
            raise PermissionError('scratch repair loses the original complete outcome census')
        return dict(original_terminal=_pin(terminal, 'terminal_event_id'), original_controls=controls,
            completed_receipts=tuple(sorted((key, _pin(row, 'receipt_id')) for key, row in receipts.items())),
            refused_tasks=tuple(sorted(refused)), pending_task_ids=tuple(sorted(pending)),
            refused_scratch_paths=tuple(sorted(scratch)))
    finally:
        if _custody_control_pins(writer, predecessor) != controls:
            raise PermissionError('scratch repair changed original controls during inspection')
        for _, relative in scratch:
            _empty_scratch(writer, relative)


def derive_development_scratch_repair(*, writer, plan, predecessor, original_source, controller,
        owner_instruction_sha256, worker_interpreter, worker_source_root):
    """The caller holds the original execution lock and current input access."""
    worker, environment = observe_frozen_repair_worker(interpreter=worker_interpreter, source_root=worker_source_root)
    if worker != original_source:
        raise PermissionError('scratch repair substitutes the original worker source')
    require_scientific_source(worker, controller)
    package_root = observe_frozen_worker_package_root(environment, source_root=worker_source_root)
    census = _original_census(writer=writer, plan=plan, predecessor=predecessor, require_absent=True)
    token = sha256(canonical_json_bytes((predecessor.fingerprint(), controller,
        owner_instruction_sha256, environment, str(worker_source_root), package_root))).hexdigest()
    proof = DevelopmentScratchRepair('repair.development-scratch.' + token[:24], owner_instruction_sha256,
        _pin(plan, 'execution_plan_id'), _pin(predecessor, 'recovery_index_id'), **census,
        controller=controller, worker=worker, worker_environment=environment,
        worker_source_root=str(worker_source_root), worker_package_root=package_root)
    return proof, DevelopmentScratchRepairRecoveryIndex.derive(plan, predecessor, proof)


def select_development_scratch_repair(*, writer, plan, predecessor):
    proof = _read_record(writer, repair_relative_path(predecessor.run_id), DevelopmentScratchRepair)
    if proof is None:
        return predecessor
    index = DevelopmentScratchRepairRecoveryIndex.derive(plan, predecessor, proof)
    census = _original_census(writer=writer, plan=plan, predecessor=predecessor, require_absent=False)
    if any(getattr(proof, key) != value for key, value in census.items()):
        raise PermissionError('scratch repair changes original attempts, scratch or successful receipts')
    require_scientific_source(proof.worker, proof.controller)
    if ExternalRunRecoveryStore(writer).read_index(index.index_relative_path, expected_schema=index.SCHEMA) != index:
        raise PermissionError('scratch repair loses its separately derived attempt index')
    return index


def publish_development_scratch_repair(*, writer, repair, index):
    if type(index) is not DevelopmentScratchRepairRecoveryIndex or index.repair != repair:
        raise PermissionError('scratch repair changes its derived attempt index')
    ExternalRunRecoveryStore(writer).freeze(index)
    relative = repair_relative_path(index.run_id)
    writer.write(ArtifactWriteRequest(repair.repair_id, relative, repair.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, 'application/json', 'development-scratch-repair.' + index.run_id,
        relative.rsplit('/', 1)[0], repair.canonical_bytes(), VisibilityCeiling.DEVELOPMENT_ONLY,
        (), OutcomeAccess.DEVELOPMENT_VISIBLE))


def authenticate_controller(*, index, source, controller):
    if type(index) is not DevelopmentScratchRepairRecoveryIndex:
        raise TypeError('scratch repair requires its typed recovery index')
    proof = index.repair
    if (source, controller) != (proof.worker, proof.controller):
        raise PermissionError('scratch repair changes the selected controller or original worker')
    require_scientific_source(source, controller)
    worker, environment = observe_frozen_repair_worker(interpreter=proof.worker_environment.interpreter_path,
        source_root=proof.worker_source_root)
    root = observe_frozen_worker_package_root(environment, source_root=proof.worker_source_root)
    if (worker, environment, root) != (proof.worker, proof.worker_environment, proof.worker_package_root):
        raise PermissionError('scratch repair changes the live original worker installation')
    return root


def repair_report(index):
    proof = index.repair
    return {'operational_scratch_repair': {
        'repair': proof.identity.to_document(), 'original_terminal': proof.original_terminal.to_document(),
        'retained_successful_receipts': len(proof.completed_receipts),
        'retained_refused_attempts': len(proof.refused_tasks),
        'additional_pure_attempts': len(proof.refused_tasks),
        'previously_unstarted_tasks': len(proof.pending_task_ids),
        'original_scratch_preserved': True, 'scientific_task_and_resource_changes': False,
        'native_effect_authority': 'NONE'}}


def recover_development_scratch(*, service, directory, run_id, owner_instruction_sha256,
        worker_interpreter, worker_source_root, maximum_parallel_tasks, read_access=None):
    from empirical_lawhood.api.recursive_authoring import implementation_binding, load_authored_wave
    from empirical_lawhood.api.recursive_execution import _retained_plans, run_recursive_wave
    from empirical_lawhood.storage.run_source_admission import _capture_source
    from empirical_lawhood.storage.source_closure import require_admitted_target_source_current

    writer = service.artifact_writer
    _, draft, source, payloads = load_authored_wave(directory=directory, artifact_writer=writer,
        lazy_payloads=True, require_initial_experiment=True, read_access=read_access)
    run, plan, index = _retained_plans(payloads, draft)
    if run.run_plan_id != run_id:
        raise PermissionError('scratch repair changes its selected original run')
    admission = _capture_source(service.project_root)
    controller = implementation_binding(service.project_root, _admitted_source=admission)
    access = getattr(payloads, 'original_input_access', None)
    with _contacts(writer, plan).execution_lock(run_id):
        try:
            if access is not None:
                access.require_current()
            if type(index) is DevelopmentScratchRepairRecoveryIndex:
                proof = index.repair
                if (proof.owner_instruction_sha256, proof.worker_environment.interpreter_path, proof.worker_source_root) != (
                        owner_instruction_sha256, str(worker_interpreter), str(worker_source_root)):
                    raise PermissionError('existing scratch repair cannot receive another selection or attempt')
                authenticate_controller(index=index, source=source, controller=controller)
            else:
                proof, index = derive_development_scratch_repair(writer=writer, plan=plan, predecessor=index,
                    original_source=source, controller=controller, owner_instruction_sha256=owner_instruction_sha256,
                    worker_interpreter=worker_interpreter, worker_source_root=worker_source_root)
                require_admitted_target_source_current(service.project_root, admission)
                if access is not None:
                    access.require_current()
                publish_development_scratch_repair(writer=writer, repair=proof, index=index)
        finally:
            require_admitted_target_source_current(service.project_root, admission)
            if access is not None:
                access.require_current()
    return run_recursive_wave(directory=directory, project_root=service.project_root,
        artifact_writer=writer, maximum_parallel_tasks=maximum_parallel_tasks,
        require_initial_experiment=True, read_access=read_access)
