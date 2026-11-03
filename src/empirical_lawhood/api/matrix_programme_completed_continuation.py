# SPDX-License-Identifier: MPL-2.0
"""Source continuation at completed E3 or E4 DEV through ordinary owners."""
from contextlib import ExitStack, contextmanager
from dataclasses import replace

from empirical_lawhood.adapters.methods.matrix_researcher_programme import source_continuation as domain
from empirical_lawhood.adapters.methods.matrix_researcher_programme.frontier import PHASES
from empirical_lawhood.runtime.retained_e3_repair import RetainedE3RepairRecoveryIndex
from empirical_lawhood.runtime.operational_configuration import scientific_reconstruction_enabled
from empirical_lawhood.runtime.progress import report_progress

from .matrix_researcher_programme_lineage import read_published_record, retained_run_binding
from .matrix_programme_source_continuation import (
    _OriginalExecutionCustody, _pin, _pin_original_selection, _predecessor,
)


def require_numerical_continuity(original, current):
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_retained_execution import (
        require_numerical_source_continuity, source_binding,
    )
    require_numerical_source_continuity(source_binding(original), source_binding(current))


def read_source_continuation(writer, relative, maximum_bytes):
    manifest = writer.read_manifest(relative)
    kinds = {kind.SCHEMA: kind for kind in (
        domain.MatrixProgrammeSourceContinuation, domain.MatrixProgrammeCompletedSourceContinuation,
        domain.MatrixProgrammeUnenteredE4SourceContinuation, domain.MatrixProgrammeCompletedE4SourceContinuation,
        domain.MatrixProgrammeCompletedE4OutputContinuation)}
    try:
        kind = kinds[manifest.logical.payload_schema]
    except KeyError as error:
        raise PermissionError('programme source continuation has an unsupported custody contract') from error
    return read_published_record(writer, relative, kind, maximum_bytes)


def require_unentered_successors(context, *, retained_metadata=None, unentered_e4=None,
        completed_phases=domain.COMPLETED_PHASES):
    if completed_phases not in (domain.COMPLETED_PHASES, domain.COMPLETED_E4_PHASES):
        raise PermissionError('source continuation has an unsupported completed frontier')
    if completed_phases == domain.COMPLETED_E4_PHASES and (retained_metadata is not None or unentered_e4 is not None):
        raise PermissionError('completed E4 cannot also be selected as unentered')
    phases = set(completed_phases) | ({'e4.development'} if unentered_e4 is not None else set())
    if set(context.bindings) != phases or context.pending_bindings:
        raise PermissionError('completed source continuation requires exactly its selected completed phase bindings')
    for phase in PHASES[len(completed_phases):]:
        for path in (context.child_directory(phase), context.metadata_directory(phase),
                context.directory / 'bindings' / (phase + '.json'),
                context.directory / 'bindings' / (phase + '.json.manifest.json'),
                context.directory / 'runs' / (phase + '.main.json')):
            if path.exists() or path.is_symlink():
                if (phase == 'e4.development' and unentered_e4 is not None
                        and path != context.directory / 'runs' / (phase + '.main.json')):
                    continue
                if (phase == 'e4.development' and path == context.metadata_directory(phase)
                        and callable(retained_metadata)):
                    continue
                raise PermissionError('source continuation refuses an entered or authored successor: ' + phase)
    if retained_metadata is not None:
        retained_metadata()
    if unentered_e4 is not None:
        unentered_e4.require_current()


def completed_e4_terminals(report):
    """Require both actual completion censuses, including the PURE structure."""
    structure = report.get('structure')
    for phase, selected in (('E4 development', report), ('E4 structure', structure)):
        if (not isinstance(selected, dict) or selected.get('read_scope') != 'EXECUTION_RECORDS'
                or selected.get('execution_complete') is not True
                or selected.get('operational_terminal') != 'AUTHENTICATED'):
            raise PermissionError('source continuation requires complete original ' + phase + ' custody')
    return _pin(report['terminal']), _pin(structure['terminal'])


@contextmanager
def recorded_completed_e4_custody(owner, context, record):
    """Hold both exact execution censuses through a recorded handoff's use."""
    from .recursive_execution import _custody_control_pins
    controls = []
    report = owner._read_phase(context, 'e4.development', execution_only=True,
        observe_controls=lambda index, pins: controls.append((index, pins)))
    if completed_e4_terminals(report) != (dict(record.predecessor_terminals)['e4.development'],
            record.completed_e4_structure_terminal):
        raise PermissionError('recorded continuation changes original E4 acquisition or structural custody')
    if len(controls) != 2:
        raise PermissionError('recorded E4 continuation requires both original execution control censuses')

    def require_current():
        require_unentered_successors(context, completed_phases=record.RETAINED_PHASES)
        for index, pins in controls:
            if _custody_control_pins(context.writer, index) != pins:
                raise PermissionError('recorded continuation changes original E4 execution controls during use')

    require_current()
    try:
        yield report
    finally:
        require_current()


@contextmanager
def original_completed_custody(owner, context):
    """Authenticate completed phases and keep their original grants live."""
    from .matrix_researcher_programme import _phase_complete
    from .recursive_execution import _custody_control_pins
    from .matrix_programme_retained_bank_metadata import retained_e4_bank_metadata
    from empirical_lawhood.kernel.provenance import ObjectIdentity

    if context.service.storage_profile is None:
        raise ValueError('completed source continuation requires the selected operator profile')
    with context.writer.read_context() as writer, writer.verification_dependencies() as dependencies, ExitStack() as lifetime:
        service = replace(context.service, artifact_writer=writer)
        scoped_owner = type(owner)(service=service, descriptor=owner.descriptor)
        current = replace(context, service=service)
        require_selection = _pin_original_selection(scoped_owner, current)
        controls, reports, terminals = [], {}, []
        phases, e4_report, structure_terminal = domain.COMPLETED_PHASES, None, None
        if 'e4.development' in current.bindings:
            observed = scoped_owner._read_phase(current, 'e4.development', execution_only=True,
                observe_controls=lambda index, pins: controls.append((index, pins)))
            if observed.get('execution_complete') is True:
                _, structure_terminal = completed_e4_terminals(observed)
                e4_report, phases = observed, domain.COMPLETED_E4_PHASES
        from .matrix_programme_unentered_e4 import unentered_e4_custody
        unentered = None if e4_report is not None else lifetime.enter_context(unentered_e4_custody(current))
        metadata_guard = (None if unentered is not None or e4_report is not None
            else lifetime.enter_context(retained_e4_bank_metadata(current)))
        require_unentered_successors(current, retained_metadata=metadata_guard, unentered_e4=unentered,
            completed_phases=phases)
        for phase in phases:
            report_progress(phase='matrix.continuation.authenticate.' + phase)
            if phase == 'e4.development':
                report = e4_report
                terminal, _ = completed_e4_terminals(report)
            elif phase != 'e3' or not scientific_reconstruction_enabled():
                report = scoped_owner._read_phase(current, phase, execution_only=True,
                    observe_controls=lambda index, pins: controls.append((index, pins)))
                if (report.get('read_scope') != 'EXECUTION_RECORDS'
                        or report.get('execution_complete') is not True
                        or report.get('operational_terminal') != 'AUTHENTICATED'):
                    raise PermissionError('source continuation requires complete original execution: ' + phase)
                terminal = _pin(report['terminal'])
            else:
                report = scoped_owner._read_phase(current, phase)
                if not _phase_complete(phase, report):
                    raise PermissionError('source continuation requires completed E3 custody and its full scientific read')
                selected, api, authority, package, run, selected_plan = current.authority(phase)
                plan, index, recovery = api._execution_service._load_status_index(run.run_plan_id, package=package)
                event = recovery.read_terminal(index)
                if (event is None or event.operational_status != 'SUCCEEDED'
                        or set(event.completed_task_ids) != {task.task_id for task in plan.tasks}
                        or event.failed_task_ids or event.blocked_task_ids):
                    raise PermissionError('source continuation requires every frozen E3 task receipt')
                if isinstance(index, RetainedE3RepairRecoveryIndex):
                    index.validate_plan(plan)
                controls.append((index, _custody_control_pins(writer, index)))
                terminal = ObjectIdentity.from_record(event.terminal_event_id, event)
                # The terminal and control pins complete this independent
                # execution join. Original scientific custody stays live below.
                del selected, api, authority, package, run, selected_plan, plan, recovery, event
            reports[phase] = report
            terminals.append((phase, terminal))
        run = retained_run_binding(current.phase_origins.get('e3', current), 'e3')
        active = True

        def require_current():
            if not active:
                raise PermissionError('completed source custody escaped its read lifetime')
            require_selection()
            require_unentered_successors(current, retained_metadata=metadata_guard, unentered_e4=unentered,
                completed_phases=phases)
            if retained_run_binding(current.phase_origins.get('e3', current), 'e3') != run:
                raise PermissionError('completed source continuation changes its original E3 run')
            for index, pins in controls:
                if _custody_control_pins(writer, index) != pins:
                    raise PermissionError('completed source continuation changes original execution custody')
            # The full scientific reader owns current reveal and model/array
            # access. Its live scope must outlast every downstream publication.
            if scientific_reconstruction_enabled():
                if not current._e3_products:
                    raise PermissionError('completed source continuation lost its original scientific read scope')
                for _, products in current._e3_products:
                    products.require_current()
            else:
                from .retained_e3_evidence import current_e3_evidence
                evidence = current_e3_evidence(writer)
                if evidence is not None:
                    evidence.require_access()
            dependencies.require_current()

        try:
            require_current()
            yield _OriginalExecutionCustody(current, tuple(terminals), None, reports,
                require_current, phases, unentered, structure_terminal)
        finally:
            try:
                require_current()
            finally:
                active = False


@contextmanager
def continued_context(owner, context, record):
    if record.target_plan != context.plan:
        raise PermissionError('completed source continuation changes its target programme')
    original_owner, original_plan = _predecessor(context.service, record.specification, allow_completed=True)
    operations = domain.continued_operations(original_plan.specification.operations, record.specification,
        completed_phases=record.RETAINED_PHASES)
    if ((original_plan.workers, original_plan.environment_id, operations) !=
            (context.plan.workers, context.plan.environment_id, context.plan.specification.operations)
            or original_plan.source_snapshot == context.plan.source_snapshot):
        raise PermissionError('completed source continuation changes operations or lacks a new source')
    with original_owner._read_context(original_plan, operation=context.operation) as original, ExitStack() as lifetime:
        require_numerical_continuity(original.inputs.producing_provenance, context.inputs.producing_provenance)
        from empirical_lawhood.adapters.methods.matrix_researcher_programme.completed_source import (
            MatrixCompletedE3InputSource, validate_completed_inputs,
        )
        from empirical_lawhood.infrastructure.matrix_completed_source import read_completed_source, original_e3_commitment, original_e3_programme_inputs
        source = read_completed_source(context.writer, context.commitments)
        selected = original_e3_commitment(context.writer, original.inputs, original.plan.specification.input_commitments)
        original_inputs = lifetime.enter_context(original_e3_programme_inputs(writer=context.writer,
            inputs=original.inputs, maximum_source_bytes=original.plan.specification.operations.metadata_budget.source_scan_bytes))
        expected = MatrixCompletedE3InputSource('source.completed-e3.' + record.specification.fingerprint(),
            record.specification.identity, selected,
            original_inputs.producing_provenance.identity, context.inputs.producing_provenance.identity)
        if source != expected:
            raise PermissionError('completed source continuation changes its exact original input source')
        validate_completed_inputs(original_inputs, context.inputs, source)
        phases = record.RETAINED_PHASES
        if tuple((phase, original.binding(phase).identity) for phase in phases) != record.predecessor_bindings:
            raise PermissionError('completed source continuation changes original phase bindings')
        with original_completed_custody(original_owner, original) as retained:
            if retained.phases != phases or retained.terminals != record.predecessor_terminals:
                raise PermissionError('completed source continuation changes original terminal custody')
            expected_e4 = (record.unentered_e4_binding, record.unentered_e4_packet, record.unentered_e4_plan,
                record.unentered_e4_run_id, record.unentered_e4_inputs_sha256) if type(record) is domain.MatrixProgrammeUnenteredE4SourceContinuation else None
            if (None if retained.unentered_e4 is None else retained.unentered_e4.fields) != expected_e4:
                raise PermissionError('completed source continuation changes its recorded unentered E4 custody')
            expected_structure = (record.completed_e4_structure_terminal
                if isinstance(record, domain.MatrixProgrammeCompletedE4SourceContinuation) else None)
            if retained.completed_e4_structure_terminal != expected_structure:
                raise PermissionError('completed source continuation changes its original E4 structural terminal')
            if any(phase in context.bindings for phase in phases):
                raise PermissionError('completed phases cannot be reauthored in a continued programme')
            context.phase_origins.update((phase, retained.context.phase_origins.get(phase, retained.context))
                for phase in phases)
            context.bindings.update((phase, original.binding(phase)) for phase in phases)
            context.retained_execution_reports.update(retained.reports)
            if context._e3_products:
                raise PermissionError('completed source continuation cannot substitute an active E3 reader')
            context._e3_products.extend(retained.context._e3_products)
            context.continuation_records.extend(original.continuation_records)
            context.amendment_records.extend(original.amendment_records)
            context.continuation_records.append(record)
            yield
            retained.require_current()
