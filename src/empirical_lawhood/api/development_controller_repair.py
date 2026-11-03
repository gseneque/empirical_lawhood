# SPDX-License-Identifier: MPL-2.0
"""Preserve entered DEV custody while replacing only its operational controller."""

from hashlib import sha256

from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
from empirical_lawhood.infrastructure.recovery import ExternalRunRecoveryStore
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes, validate_stable_id
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.development_controller_repair import (
    DevelopmentControllerRepair, DevelopmentControllerRepairRecoveryIndex,
)
from empirical_lawhood.runtime.execution import OperationalFailureClass
from empirical_lawhood.runtime.native_effects import NativeEffectContact
from empirical_lawhood.runtime.recovery import DevelopmentRunRecoveryIndex, TaskRecoveryDisposition

from .development_output_repair import _pin
from .retained_e3_control_repair import _read_record, observe_frozen_repair_worker, observe_frozen_worker_package_root


def repair_relative_path(run_id):
    validate_stable_id(run_id)
    return f'runs/{run_id}/repairs/development-controller/repair.json'


def require_scientific_source(worker, controller):
    """Frozen science and registry; programme continuation metadata may change."""
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_retained_execution import require_numerical_source_continuity
    require_numerical_source_continuity(worker, controller)
    metadata = frozenset(('adapters/methods/matrix_researcher_programme/source_continuation.py',
        'adapters/methods/matrix_researcher_programme/extension_bundle.py'))
    for prefix in ('adapters/', 'kernel/'):
        old = {key: value for key, value in worker.package_sources if key.startswith(prefix) and key not in metadata}
        new = {key: value for key, value in controller.package_sources if key.startswith(prefix) and key not in metadata}
        if not old or old != new:
            raise PermissionError('development controller repair changes original scientific source: ' + prefix)


def _contacts(writer, plan):
    return ExternalNativeEffectContactStore(plane=writer, execution_plan=_pin(plan, 'execution_plan_id'),
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE)


def _original_census(*, writer, plan, predecessor, output_bytes, require_absent, repair_index=None):
    from .recursive_execution import _custody_control_pins
    from .recursive_operations import operation_catalog
    from empirical_lawhood.infrastructure.sql import create_catalog_engine, upgrade_catalog, SQLiteOperationalRepository

    if type(predecessor) is not DevelopmentRunRecoveryIndex:
        raise PermissionError('development controller repair requires the original development index')
    predecessor.validate_plan(plan)
    recovery, store = ExternalRunRecoveryStore(writer), ExternalTaskReceiptStore(writer)
    engine = create_catalog_engine('sqlite+pysqlite:///:memory:')
    try:
        upgrade_catalog(engine)
        closure = recovery.reconcile(predecessor, plan, SQLiteOperationalRepository(engine), store,
            repair_missing_events=require_absent)
    finally:
        engine.dispose()
    receipts = {row.task_id: row for row in closure.recovered_receipts}
    registrations, registry, _ = operation_catalog()
    if registry.fingerprint() != plan.registry_sha256:
        raise PermissionError('development controller repair changes the original capability registry')
    by_key = {(row.selection.capability_key, row.selection.capability_version): row for row in registrations}
    def registration(task):
        try:
            return by_key[task.capability.capability_key, task.capability.capability_version]
        except KeyError as error:
            raise PermissionError('development controller repair loses an original capability') from error
    contacts = _contacts(writer, plan)
    refused, pending, native_pins, uncontacted = [], [], [], []
    for task in plan.tasks:
        native = registration(task).native_effect
        contact = contacts.read(predecessor.run_id, task.task_id)
        receipt = receipts.get(task.task_id)
        if receipt is not None:
            if native:
                try:
                    dependency_ids = tuple(sorted(receipts[key].receipt_id for key in task.dependency_task_ids))
                except KeyError as error:
                    raise PermissionError('completed native work loses an original dependency receipt') from error
                expected = NativeEffectContact(predecessor.run_id, task.task_id, receipt.attempt_id,
                    _pin(plan, 'execution_plan_id'), _pin(task, 'task_id'), plan.implementation_commit,
                    receipt.input_materialization_ids, dependency_ids)
                if contact != expected:
                    raise PermissionError('development controller repair changes a completed native contact')
                native_pins.append((task.task_id, ObjectIdentity.from_record(task.task_id, contact)))
            elif contact is not None:
                raise PermissionError('PURE original work cannot have a native contact')
            continue
        if contact is not None:
            # A later read may encounter this repair's first native contact.
            # The immutable original contact path cannot be relabelled.
            if (require_absent or not native or repair_index is None
                    or contact.attempt_id not in {row.attempt_id for row in repair_index.task(task.task_id).attempts}
                    or contact.execution_plan != _pin(plan, 'execution_plan_id')
                    or contact.execution_task != _pin(task, 'task_id')
                    or contact.implementation_commit != plan.implementation_commit):
                raise PermissionError('development controller repair refuses an uncertain or original pending native contact')
        binding = predecessor.task(task.task_id)
        if binding.maximum_attempts != 1:
            raise PermissionError('development controller repair requires one original attempt per pending task')
        candidate, = binding.attempts
        event = recovery.read_event(predecessor, candidate.event_relative_path)
        nonattempt = recovery.read_event(predecessor, binding.nonattempt_event_relative_path)
        if event is not None:
            if (native or nonattempt is not None or event.disposition is not TaskRecoveryDisposition.BLOCKED
                    or event.failure is None or event.failure.failure_class is not OperationalFailureClass.RESOURCE_REFUSAL
                    or event.failure.sanitized_exception_type != 'ResourceAdmissionError'):
                raise PermissionError('development controller repair refuses non-resource or native failed attempts')
            refused.append((task.task_id, _pin(event, 'event_id')))
        else:
            if nonattempt is not None and (nonattempt.disposition is not TaskRecoveryDisposition.NOT_ATTEMPTED
                    or nonattempt.reason_codes != ('dependency-blocked',)):
                raise PermissionError('development controller repair refuses an unrelated original task block')
            pending.append(task.task_id)
            if native:
                uncontacted.append(task.task_id)
        if require_absent:
            for output in task.outputs:
                for relative in (output.relative_path, output.relative_path + '.manifest.json'):
                    path = writer.root.resolve(relative, for_write=False)
                    if path.exists() or path.is_symlink():
                        raise PermissionError('development controller repair refuses unreceipted original output')
    if not receipts or not refused:
        raise PermissionError('development controller repair requires retained success and an actual PURE output refusal')
    refused_keys = {(plan.task(key).capability.capability_key, plan.task(key).capability.capability_version)
        for key, _ in refused}
    for key, _ in refused:
        budget = plan.task(key).capability.requested_resources
        if budget.output_bytes is None or budget.output_bytes >= output_bytes:
            raise PermissionError('development controller repair must increase the refused PURE output allowance')
    output_tasks = tuple(task.task_id for task in plan.tasks if task.task_id not in receipts and
        (task.capability.capability_key, task.capability.capability_version) in refused_keys and
        task.capability.requested_resources.output_bytes is not None and
        task.capability.requested_resources.output_bytes < output_bytes)
    for task_id in output_tasks:
        task = plan.task(task_id)
        declared = registration(task)
        budget = task.capability.requested_resources
        from dataclasses import replace
        if (declared.native_effect or budget.output_bytes is None or budget.output_bytes >= output_bytes
                or not declared.resource_ceiling.contains(replace(budget, output_bytes=output_bytes))):
            raise PermissionError('development controller repair changes a native budget or exceeds its original PURE ceiling')
    terminal = recovery.read_terminal(predecessor)
    if terminal is not None and (terminal.operational_status != 'BLOCKED' or terminal.failed_task_ids):
        raise PermissionError('development controller repair refuses an incompatible original terminal')
    return dict(original_terminal=None if terminal is None else _pin(terminal, 'terminal_event_id'),
        original_controls=_custody_control_pins(writer, predecessor),
        completed_receipts=tuple(sorted((key, _pin(value, 'receipt_id')) for key, value in receipts.items())),
        completed_native_contacts=tuple(sorted(native_pins)), refused_tasks=tuple(sorted(refused)),
        pending_task_ids=tuple(sorted(pending)), uncontacted_native_task_ids=tuple(sorted(uncontacted)),
        output_task_ids=tuple(sorted(output_tasks)))


def derive_development_controller_repair(*, writer, plan, predecessor, original_source, controller,
        owner_instruction_sha256, output_bytes, worker_interpreter, worker_source_root):
    """Derive the complete census under the original exclusive run lock."""
    worker, environment = observe_frozen_repair_worker(interpreter=worker_interpreter, source_root=worker_source_root)
    if worker != original_source:
        raise PermissionError('development controller repair substitutes the original worker installation')
    require_scientific_source(worker, controller)
    census = _original_census(writer=writer, plan=plan, predecessor=predecessor,
        output_bytes=output_bytes, require_absent=True)
    token = sha256(canonical_json_bytes((predecessor.fingerprint(), controller, owner_instruction_sha256, output_bytes))).hexdigest()
    proof = DevelopmentControllerRepair('repair.development-controller.' + token[:24], owner_instruction_sha256,
        _pin(plan, 'execution_plan_id'), _pin(predecessor, 'recovery_index_id'), **census,
        output_bytes=output_bytes, controller=controller, worker=worker,
        worker_environment=environment, worker_source_root=str(worker_source_root))
    index = DevelopmentControllerRepairRecoveryIndex.derive(plan, predecessor, proof)
    return proof, index


def select_development_controller_repair(*, writer, plan, predecessor):
    proof = _read_record(writer, repair_relative_path(predecessor.run_id), DevelopmentControllerRepair)
    if proof is None:
        return predecessor
    require_scientific_source(proof.worker, proof.controller)
    index = DevelopmentControllerRepairRecoveryIndex.derive(plan, predecessor, proof)
    census = _original_census(writer=writer, plan=plan, predecessor=predecessor,
        output_bytes=proof.output_bytes, require_absent=False, repair_index=index)
    if any(getattr(proof, key) != value for key, value in census.items()):
        raise PermissionError('development controller repair changes its complete original custody census')
    if ExternalRunRecoveryStore(writer).read_index(index.index_relative_path, expected_schema=index.SCHEMA) != index:
        raise PermissionError('development controller repair changes its separately derived recovery index')
    return index


def publish_development_controller_repair(*, writer, repair, index):
    from .recursive_execution import _custody_control_pins
    if type(index) is not DevelopmentControllerRepairRecoveryIndex or index.repair != repair:
        raise PermissionError('development controller repair changes its derived index')
    if _custody_control_pins(writer, index.predecessor) != repair.original_controls:
        raise PermissionError('original development custody changed before repair publication')
    ExternalRunRecoveryStore(writer).freeze(index)
    relative = repair_relative_path(index.run_id)
    writer.write(ArtifactWriteRequest(repair.repair_id, relative, repair.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, 'application/json', 'development-controller-repair.' + index.run_id,
        relative.rsplit('/', 1)[0], repair.canonical_bytes(), VisibilityCeiling.DEVELOPMENT_ONLY,
        (), OutcomeAccess.DEVELOPMENT_VISIBLE))


def authenticate_controller(*, index, source, controller):
    if type(index) is not DevelopmentControllerRepairRecoveryIndex:
        raise TypeError('development controller repair requires its typed recovery index')
    proof = index.repair
    if (source, controller) != (proof.worker, proof.controller):
        raise PermissionError('development controller repair changes its selected controller or original worker')
    require_scientific_source(source, controller)
    worker, environment = observe_frozen_repair_worker(interpreter=proof.worker_environment.interpreter_path,
        source_root=proof.worker_source_root)
    if (worker, environment) != (proof.worker, proof.worker_environment):
        raise PermissionError('development controller repair changes its live original worker environment')
    return observe_frozen_worker_package_root(environment)


def repair_report(index):
    proof = index.repair
    return {'operational_controller_repair': {
        'repair': proof.identity.to_document(),
        'original_terminal': None if proof.original_terminal is None else proof.original_terminal.to_document(),
        'retained_successful_receipts': len(proof.completed_receipts),
        'retained_native_contacts': len(proof.completed_native_contacts),
        'refused_pure_calculations': len(proof.refused_tasks),
        'pending_original_tasks': len(proof.pending_task_ids),
        'uncontacted_original_native_tasks': len(proof.uncontacted_native_task_ids),
        'output_allowance_task_count': len(proof.output_task_ids), 'output_bytes': proof.output_bytes,
        'native_acquisition_scope': 'ORIGINAL_UNCONTACTED_TASKS_ONLY'}}


def recover_development_controller(*, service, directory, run_id, output_bytes,
        owner_instruction_sha256, worker_interpreter, worker_source_root,
        maximum_parallel_tasks, read_access=None):
    from .recursive_authoring import implementation_binding, load_authored_wave
    from .recursive_execution import _retained_plans, run_recursive_wave
    from empirical_lawhood.infrastructure.run_source_admission import _capture_source
    from empirical_lawhood.infrastructure.source_closure import require_admitted_target_source_current

    writer = service.artifact_writer
    _, draft, source, payloads = load_authored_wave(directory=directory, artifact_writer=writer,
        lazy_payloads=True, require_initial_experiment=True, read_access=read_access)
    run, plan, index = _retained_plans(payloads, draft)
    if run.run_plan_id != run_id:
        raise PermissionError('development controller repair changes its selected original run')
    admission = _capture_source(service.project_root)
    controller = implementation_binding(service.project_root, _admitted_source=admission)
    access = getattr(payloads, 'original_input_access', None)
    with _contacts(writer, plan).execution_lock(run_id):
        if access is not None:
            access.require_current()
        if type(index) is DevelopmentControllerRepairRecoveryIndex:
            proof = index.repair
            if (proof.output_bytes, proof.owner_instruction_sha256, proof.worker_environment.interpreter_path,
                    proof.worker_source_root) != (output_bytes, owner_instruction_sha256,
                    str(worker_interpreter), str(worker_source_root)):
                raise PermissionError('existing development controller repair cannot receive another selection or attempt')
            authenticate_controller(index=index, source=source, controller=controller)
        else:
            proof, index = derive_development_controller_repair(writer=writer, plan=plan, predecessor=index,
                original_source=source, controller=controller, owner_instruction_sha256=owner_instruction_sha256,
                output_bytes=output_bytes, worker_interpreter=worker_interpreter, worker_source_root=worker_source_root)
            require_admitted_target_source_current(service.project_root, admission)
            if access is not None:
                access.require_current()
            publish_development_controller_repair(writer=writer, repair=proof, index=index)
        require_admitted_target_source_current(service.project_root, admission)
        if access is not None:
            access.require_current()
    return run_recursive_wave(directory=directory, project_root=service.project_root,
        artifact_writer=writer, maximum_parallel_tasks=maximum_parallel_tasks,
        require_initial_experiment=True, read_access=read_access)
