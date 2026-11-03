# SPDX-License-Identifier: MPL-2.0
"""Repair a failed ordinary E4 PURE child without repeating native acquisition.

The original child must contain only failed measurements and their unstarted
dependants. A new ordinary author derives every task and input from the exact
original preparation. Original attempts, sources and terminals remain intact.
"""
from hashlib import sha256
from pathlib import Path

from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.development_structure_repair import DevelopmentStructureRepair
from empirical_lawhood.runtime.recovery import DevelopmentRunRecoveryIndex, TaskRecoveryDisposition


def _pin(value, field):
    return ObjectIdentity.from_record(getattr(value, field), value)


def _relative(writer, directory):
    from .selected_e4_structure import _directory
    return (_directory(writer, directory) / 'repair.json').relative_to(writer.root.contract.canonical_path).as_posix()


def _read_selection(writer, directory):
    from .retained_e3_control_repair import _read_record
    return _read_record(writer, _relative(writer, directory), DevelopmentStructureRepair)


def require_structural_source(original, replacement):
    """Keep all numerical owners and the kernel; permit the label correction."""
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_retained_execution import require_numerical_source_continuity
    require_numerical_source_continuity(original, replacement)
    metadata = frozenset((
        'adapters/methods/matrix_scheduled_history/full_factor_records.py',
        'adapters/methods/matrix_researcher_programme/source_continuation.py',
        'adapters/methods/matrix_researcher_programme/extension_bundle.py',
        'adapters/methods/matrix_researcher_programme/selection.py',
        'adapters/methods/matrix_researcher_programme/completed_source.py',
    ))
    for prefix in ('adapters/', 'kernel/'):
        before = {key: value for key, value in original.package_sources if key.startswith(prefix) and key not in metadata}
        after = {key: value for key, value in replacement.package_sources if key.startswith(prefix) and key not in metadata}
        if not before or before != after:
            raise PermissionError('structural repair changes original numerical or kernel source: ' + prefix)


def _original_controls(*, writer, directory, read_access=None):
    from .experiment_execution_read import load_development_execution_controls, read_execution_records
    from .recursive_execution import _custody_control_pins
    from .recursive_operations import operation_catalog
    from .selected_e4_structure import _directory
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import full_factor_bindings as owner
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.full_factor_preparation import ScheduledFullFactorDevelopmentSpecification
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e3_e4_experiment import SelectedE3E4ExperimentSpecification
    from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
    from empirical_lawhood.infrastructure.recovery import ExternalRunRecoveryStore
    from empirical_lawhood.runtime.execution import OperationalFailureClass

    child = _directory(writer, directory) / 'analysis'
    acquisition = load_development_execution_controls(directory=directory, artifact_writer=writer, read_access=read_access)
    structural = load_development_execution_controls(directory=child, artifact_writer=writer, read_access=read_access)
    for values, kind in ((acquisition, SelectedE3E4ExperimentSpecification),
            (structural, ScheduledFullFactorDevelopmentSpecification)):
        packet = values[0]
        members = tuple(row for row in packet.members if row.filename == 'experiment-specification.json')
        if len(members) != 1 or (members[0].identity.object_schema, members[0].identity.object_version) != (kind.SCHEMA, kind.VERSION):
            raise PermissionError('structural repair requires the original ordinary E4 development companions')
    reports, controls = [], []
    for values in (acquisition, structural):
        _, _, plan, index, _, access = values
        if access is not None:
            access.require_current()
        observed = []
        reports.append(read_execution_records(writer=writer, plan=plan, index=index,
            observe_controls=lambda selected, pins: observed.append(pins)))
        pins, = observed
        controls.append(pins)
    first, second = reports
    if not first['execution_complete'] or first['operational_terminal'] != 'AUTHENTICATED':
        raise PermissionError('structural repair requires complete original native acquisition')
    packet, run, plan, index, source, access = structural
    if type(index) is not DevelopmentRunRecoveryIndex or second['status'] != 'FAILED':
        raise PermissionError('structural repair requires one settled original failed PURE child')
    registrations, registry, _ = operation_catalog()
    declarations = {row.selection.capability_key: row for row in registrations}
    if plan.registry_sha256 != registry.fingerprint():
        raise PermissionError('structural repair changes the original capability registry')
    keys = {owner.key(False, phase) for phase in owner.PHASES}
    if {task.capability.capability_key for task in plan.tasks} != keys or any(
            declarations[task.capability.capability_key].native_effect or task.maximum_attempts != 1 for task in plan.tasks):
        raise PermissionError('structural repair requires the exact single-attempt PURE full-factor graph')
    recovery = ExternalRunRecoveryStore(writer)
    terminal = recovery.read_terminal(index)
    measures = tuple(task.task_id for task in plan.tasks if task.capability.capability_key == owner.key(False, 'measure'))
    unstarted = tuple(task.task_id for task in plan.tasks if task.task_id not in measures)
    if (terminal is None or terminal.completed_task_ids or terminal.failed_task_ids != measures
            or terminal.blocked_task_ids != unstarted):
        raise PermissionError('structural repair cannot discard successful or differently failed original work')
    contacts = ExternalNativeEffectContactStore(plane=writer, execution_plan=_pin(plan, 'execution_plan_id'),
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE)
    for task in plan.tasks:
        binding = index.task(task.task_id)
        candidate, = binding.attempts
        event = recovery.read_event(index, candidate.event_relative_path)
        if task.task_id in measures:
            if (event is None or event.disposition is not TaskRecoveryDisposition.FAILED or event.failure is None
                    or event.failure.failure_class is not OperationalFailureClass.RETRY_EXHAUSTION
                    or event.failure.sanitized_exception_type != 'ValueError'):
                raise PermissionError('structural repair changes a known original measurement failure')
        else:
            nonattempt = recovery.read_event(index, binding.nonattempt_event_relative_path)
            if (event is not None or nonattempt is None or nonattempt.disposition is not TaskRecoveryDisposition.NOT_ATTEMPTED
                    or nonattempt.reason_codes not in (('dependency-failed',), ('dependency-blocked',))):
                raise PermissionError('structural repair requires actual unstarted dependency failures')
        if contacts.read(index.run_id, task.task_id) is not None:
            raise PermissionError('structural repair refuses prior native contact in its PURE child')
        for output in task.outputs:
            for relative in (output.relative_path, output.relative_path + '.manifest.json'):
                path = writer.root.resolve(relative, for_write=False)
                if path.exists() or path.is_symlink():
                    raise PermissionError('structural repair refuses unreceipted original output')

    def current():
        for values, pins in zip((acquisition, structural), controls, strict=True):
            if values[-1] is not None:
                values[-1].require_current()
            if _custody_control_pins(writer, values[3]) != pins:
                raise PermissionError('structural repair changed original execution custody during use')

    current()
    return acquisition, structural, reports, controls, current


def _selection(writer, directory, original, *, instruction_sha256, replacement):
    from empirical_lawhood.kernel.decoding import decode_canonical_record
    acquisition, structural, reports, controls, _ = original
    require_structural_source(structural[4], replacement)
    return DevelopmentStructureRepair(Path(directory).relative_to(writer.root.contract.canonical_path).as_posix(),
        instruction_sha256, _pin(acquisition[0], 'packet_id'),
        decode_canonical_record(reports[0]['terminal'], ObjectIdentity), sha256(canonical_json_bytes(controls[0])).hexdigest(),
        _pin(structural[0], 'packet_id'), decode_canonical_record(reports[1]['terminal'], ObjectIdentity),
        sha256(canonical_json_bytes(controls[1])).hexdigest(), structural[4], replacement)


def _require_replacement(writer, selection, original):
    """A new compiler owns the plan; all original scientific members stay exact."""
    from .recursive_authoring import load_authored_wave
    from .recursive_execution import _retained_plans
    child = writer.root.resolve(selection.child_relative_path, for_write=False)
    if not (child / 'authored-wave.json').exists() and not (child / 'authored-wave.json').is_symlink():
        return child
    packet, draft, source, payloads = load_authored_wave(directory=child, artifact_writer=writer, lazy_payloads=True)
    run, plan, _ = _retained_plans(payloads, draft)
    old_packet, old_run, old_plan, _, _, _ = original[1]
    if (source != selection.replacement_source or packet.draft != old_packet.draft
            or plan.registry_sha256 != old_plan.registry_sha256 or run.run_plan_id == old_run.run_plan_id):
        raise PermissionError('structural repair changes its selected source or complete scientific graph')
    # Only the implementation and the two compiler-produced execution plans
    # depend on the repaired source. Every other canonical member and FILE
    # must retain its exact original schema, version, size and digest.
    from empirical_lawhood.infrastructure.recursive_control_read import CONTROL_VIEWS
    excluded = {'implementation.json', 'run-plan.json', 'execution-plan.json', 'graph-preservation.json', *CONTROL_VIEWS.values()}
    old_members = tuple(member for member in old_packet.members if member.filename not in excluded)
    new_members = tuple(member for member in packet.members if member.filename not in excluded)
    if old_members != new_members:
        raise PermissionError('structural repair changes original scientific inputs or companion bytes')
    return child


def selected_structure_directory(*, writer, directory):
    """Resolve an authenticated additive selection inside the caller's read scope."""
    from .selected_e4_structure import _directory
    selected = _read_selection(writer, directory)
    if selected is None:
        return _directory(writer, directory) / 'analysis', None, lambda: None
    original = _original_controls(writer=writer, directory=directory)
    if selected != _selection(writer, directory, original,
            instruction_sha256=selected.owner_instruction_sha256, replacement=selected.replacement_source):
        raise PermissionError('structural repair changes its original complete custody binding')
    child = _require_replacement(writer, selected, original)
    def current():
        original[-1]()
        if _read_selection(writer, directory) != selected:
            raise PermissionError('structural repair selection changed during read')
    current()
    return child, selected, current


def repair_development_structure(*, service, directory, owner_instruction_sha256, maximum_parallel_tasks, read_access=None):
    from .recursive_authoring import implementation_binding, load_authored_wave
    from .selected_e3_access import original_e3_authority_read_context
    from .selected_e4_structure import (
        _acquisition, _complete_structure, _development_inputs, _directory, _retained_structure_preparation,
        _structural_companion, structural_measurement,
    )
    from .experiment_scientific_read import _development_runtime_context
    from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
    from empirical_lawhood.infrastructure.numerical_provenance import observe_worker_environment
    from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection

    writer = service.artifact_writer
    directory = Path(directory)
    # Locate the real original run for its existing cross-process lock. The
    # complete census is read again while this lock is owned.
    from .experiment_execution_read import load_development_execution_controls
    with original_e3_authority_read_context(writer), writer.read_context() as reading:
        original_child = _directory(reading, directory) / 'analysis'
        _, run, plan, _, _, _ = load_development_execution_controls(directory=original_child, artifact_writer=reading)
    contacts = ExternalNativeEffectContactStore(plane=writer, execution_plan=_pin(plan, 'execution_plan_id'),
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE)
    with contacts.execution_lock(run.run_plan_id), original_e3_authority_read_context(writer):
        replacement = implementation_binding(service.project_root)
        with writer.read_context() as reading:
            original = _original_controls(writer=reading, directory=directory, read_access=read_access)
            selected = _selection(reading, directory, original, instruction_sha256=owner_instruction_sha256, replacement=replacement)
            retained = _read_selection(reading, directory)
            if retained is not None and retained != selected:
                raise PermissionError('structural repair cannot replace its selected source or instruction')
            _, draft, _, payloads = load_authored_wave(directory=directory, artifact_writer=reading, lazy_payloads=True, read_access=read_access)
            binding = _development_runtime_context(payloads=payloads, draft=draft, callback_name='complete_development_result')
            if binding is None:
                raise PermissionError('structural repair lacks its ordinary original completion owner')
            _, specification, instance = binding
            inputs = _development_inputs(specification, instance, payloads)
            _, _, _, child_payloads = load_authored_wave(directory=original_child, artifact_writer=reading, lazy_payloads=True)
            from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_bindings as original_workers
            from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
            entry_id = original_workers.global_node(inputs.programme, 'entry')
            original_index = original[0][3]
            store = ExternalTaskReceiptStore(reading)
            entry_receipts = tuple(receipt for candidate in original_index.task(entry_id).attempts
                if (receipt := store.read(original_index.run_id, entry_id, candidate.attempt_id)) is not None)
            if len(entry_receipts) != 1:
                raise PermissionError('structural repair lacks its exact successful acquisition entry receipt')
            acquisition = _acquisition(directory=directory, writer=reading, programme=inputs.programme,
                report=original[2][0], products={'receipts':{entry_id:entry_receipts[0]}}, plan=original[0][2])
            arguments = dict(programme=inputs.programme, bank=inputs.bank, choices=specification.structure,
                secondary_readout=inputs.secondary_readout, resources=specification.structural_resources,
                campaign=inputs.campaign, original=acquisition, declaration=None, current_access=None,
                measurement=structural_measurement(programme=inputs.programme, bank=inputs.bank, choices=specification.structure))
            _structural_companion(payloads=child_payloads, **arguments)
            child = _require_replacement(reading, selected, original)
            prepared = None
            if not (child / 'authored-wave.json').exists():
                execution = ExecutionSelection(workers=maximum_parallel_tasks,
                    environment_id='environment.' + observe_worker_environment().fingerprint(),
                    source_snapshot=ObjectIdentity.from_record('recursive-member.implementation', replacement),
                    output_root=writer.root.contract.canonical_path)
                prepared = _retained_structure_preparation(directory=_directory(reading, directory) / 'inputs',
                    writer=reading, execution=execution, **arguments)
                if prepared.draft.fingerprint() != original[1][0].draft.object_fingerprint:
                    raise PermissionError('structural repair preparation changes the original full graph')
            original[-1]()
        if retained is None:
            relative = _relative(writer, directory)
            writer.write(ArtifactWriteRequest(selected.repair_id, relative, selected.SCHEMA,
                ArtifactProfile.CANONICAL_JSON, 'application/json', selected.repair_id,
                relative.rsplit('/', 1)[0], selected.canonical_bytes(), VisibilityCeiling.DEVELOPMENT_ONLY,
                (), OutcomeAccess.DEVELOPMENT_VISIBLE))
        if prepared is not None:
            service.author(preparation=prepared, output_dir=child)
        with writer.read_context() as reading:
            observed, proof, current = selected_structure_directory(writer=reading, directory=directory)
            if observed != child or proof != selected:
                raise PermissionError('structural repair changes its actual authored replacement')
            current()
        report = service.run(directory=child, maximum_parallel_tasks=maximum_parallel_tasks)
        result = _complete_structure(report)
        with writer.read_context() as reading:
            observed, proof, current = selected_structure_directory(writer=reading, directory=directory)
            if observed != child or proof != selected:
                raise PermissionError('structural repair changes its retained selection on return')
            current()
        if implementation_binding(service.project_root) != replacement:
            raise PermissionError('structural repair source changed during execution')
        return {**report, 'structural_repair': selected.to_document(), 'original_failed_structure_retained': True,
            'new_native_contact_count': 0, 'additional_independent_observations': 0,
            'scientific_result': result, 'structural_authoring_dir': str(child)}
