# SPDX-License-Identifier: MPL-2.0
"""Public source continuation after completed E1/E2 and before any TRAIN entry.

The original programme remains immutable. A separate programme retains original
E1/E2 locators and source-adjusted future inputs, without acquiring new evidence.
"""
from contextlib import contextmanager
from dataclasses import dataclass, replace
from pathlib import Path
from time import monotonic

from empirical_lawhood.adapters.methods.matrix_researcher_programme import source_continuation as domain
from empirical_lawhood.adapters.methods.matrix_researcher_programme.frontier import PHASES
from empirical_lawhood.adapters.methods.matrix_researcher_programme.known_inputs import MatrixProgrammePublishedInput
from empirical_lawhood.adapters.methods.matrix_researcher_programme.selection import (
    CONTINUED_PROTOCOL_ID, MatrixContinuedProgrammeSpecification, MatrixResearchProgrammeSpecification,
)
from empirical_lawhood.api.matrix_researcher_programme_lineage import read_published_record
from empirical_lawhood.infrastructure.matrix_programme_inputs import authenticated_programme_inputs
from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.infrastructure.source_closure import require_admitted_target_source_current
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes, canonical_json_document_bytes
from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputSelection
from empirical_lawhood.runtime.experiment_preparation import ExperimentInputDerivationResult


def _pin(document):
    raw = canonical_json_document_bytes(document)
    return decode_canonical_bytes(raw, ObjectIdentity, maximum_bytes=len(raw))


def _predecessor(service, specification, *, allow_completed=False):
    from .matrix_researcher_programme import MatrixResearchProgrammeService, PLAN_FILENAME
    from .selected_e4_bank_recipe import _publication_from_manifest
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.selection import MatrixResearchProgrammePlan
    selection = specification.predecessor
    writer = service.artifact_writer
    plan = read_published_record(writer, selection.publication.materialization.relative_path,
        MatrixResearchProgrammePlan, selection.publication.materialization.size_bytes)
    selection.require_record(plan, plan.identity)
    actual = writer.read_manifest(selection.publication.materialization.relative_path)
    if _publication_from_manifest(writer, actual) != replace(selection.publication, created=False):
        raise PermissionError('source continuation substitutes its exact original programme publication')
    if type(plan.specification) not in ((MatrixResearchProgrammeSpecification, MatrixContinuedProgrammeSpecification)
            if allow_completed else (MatrixResearchProgrammeSpecification,)):
        raise PermissionError('source continuation requires an original programme, not a continued source period')
    directory = writer.root.resolve(plan.specification.directory, for_write=False)
    if writer.root.resolve(selection.publication.materialization.relative_path, for_write=False) != directory / PLAN_FILENAME:
        raise PermissionError('source continuation substitutes the original programme home')
    domain.require_separate_home(plan.specification.directory, specification.directory)
    if not allow_completed and ((directory / domain.CONTINUATION_FILENAME).exists()
            or (directory / domain.CONTINUATION_FILENAME).is_symlink()):
        raise PermissionError('source continuation requires an original programme, not a chain of source periods')
    owner = service._composite_programme(directory=directory)
    if type(owner) is not MatrixResearchProgrammeService or owner._plan(directory) != plan:
        raise PermissionError('source continuation requires the original ordinary Matrix programme descriptor')
    return owner, plan


def _require_future_namespaces_absent(context, run_id=None):
    """Recheck actual future paths, including uncommitted and dangling entries."""
    if set(context.bindings) != {'e1', 'e2', 'train'} or context.pending_bindings:
        raise PermissionError('source continuation requires exactly authored E1/E2/TRAIN and no later phase binding')
    for phase in PHASES[3:]:
        paths = (context.child_directory(phase), context.metadata_directory(phase))
        if hasattr(context, 'directory'):
            paths += (context.directory / 'bindings' / (phase + '.json'),
                context.directory / 'bindings' / (phase + '.json.manifest.json'))
        for directory in paths:
            if directory.exists() or directory.is_symlink():
                raise PermissionError('source continuation refuses an original dependent phase namespace: ' + phase)
    if run_id is not None:
        path = context.writer.root.resolve('runs/' + run_id, for_write=False)
        if path.exists() or path.is_symlink():
            raise PermissionError('source continuation refuses any original TRAIN execution custody, including uncertain entry')


def _unentered_future_packet(context):
    from .recursive_authoring import load_authored_wave
    from .recursive_execution import _retained_plans
    _require_future_namespaces_absent(context)
    _, specification = context.bound_specification(context.binding('train'))
    packet, draft, _, payloads = load_authored_wave(directory=context.child_directory('train'),
        artifact_writer=context.writer, lazy_payloads=True)
    if payloads.get('experiment-specification.json') != specification.canonical_bytes():
        raise PermissionError('source continuation changes the original unentered TRAIN specification')
    run, _, _ = _retained_plans(payloads, draft)
    _require_future_namespaces_absent(context, run.run_plan_id)
    return ObjectIdentity.from_record(packet.packet_id, packet), run.run_plan_id


def _unentered_future(context):
    """No original future execution, binding, derived input or partial namespace."""
    return _unentered_future_packet(context)[0]


def _original_executions(owner, context, *, observe_controls=None, reports=None):
    terminals = []
    for phase in domain.RETAINED_PHASES:
        report = owner._read_phase(context, phase, execution_only=True, observe_controls=observe_controls)
        if (report.get('read_scope') != 'EXECUTION_RECORDS' or report.get('execution_complete') is not True
                or report.get('operational_terminal') != 'AUTHENTICATED'):
            raise PermissionError('source continuation requires the complete original execution census: ' + phase)
        terminals.append((phase, _pin(report['terminal'])))
        if reports is not None:
            reports[phase] = report
    return tuple(terminals)


@dataclass(frozen=True)
class _OriginalExecutionCustody:
    context: object
    terminals: tuple
    training_packet: ObjectIdentity
    reports: dict
    require_current: object
    phases: tuple = domain.RETAINED_PHASES
    unentered_e4: object = None
    completed_e4_structure_terminal: ObjectIdentity | None = None


def _pin_original_selection(owner, context):
    """Keep the original plan, descriptor and bindings in the same byte guard."""
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.selection import MatrixProgrammePhaseBinding
    from empirical_lawhood.runtime.experiment_programme import (
        MAX_PROGRAMME_DESCRIPTOR_BYTES, PROGRAMME_DESCRIPTOR_FILENAME,
    )
    if owner._plan(context.directory) != context.plan:
        raise PermissionError('source continuation changes its original programme plan')
    writer = context.writer
    descriptor_relative = (context.directory / PROGRAMME_DESCRIPTOR_FILENAME).relative_to(
        writer.root.contract.canonical_path).as_posix()
    descriptor = owner.descriptor.canonical_bytes()
    for phase, expected in context.bindings.items():
        origin = getattr(context, 'phase_origins', {}).get(phase, context)
        relative = (origin.directory / 'bindings' / (phase + '.json')).relative_to(
            writer.root.contract.canonical_path).as_posix()
        if read_published_record(writer, relative, MatrixProgrammePhaseBinding, 64 * 1024**2) != expected:
            raise PermissionError('source continuation changes an original phase binding')

    def require_descriptor():
        path = writer.root.resolve(descriptor_relative, for_write=False)
        if read_bounded_bytes(path, maximum_bytes=MAX_PROGRAMME_DESCRIPTOR_BYTES) != descriptor:
            raise PermissionError('source continuation changes its original programme descriptor')

    require_descriptor()
    return require_descriptor


@contextmanager
def _original_custody(owner, context):
    """Borrow one decoded census while its real controls and absences stay guarded.

    The ordinary readers still authenticate every original receipt and event.
    Their complete control pins, observed publication snapshots and input-access
    callbacks are checked again before publication and before this scope closes.
    No report or permission survives as a cache for another operation.
    """
    from .recursive_execution import _custody_control_pins
    with context.writer.read_context() as writer, writer.verification_dependencies() as dependencies:
        service = replace(context.service, artifact_writer=writer)
        scoped_owner = type(owner)(service=service, descriptor=owner.descriptor)
        current = replace(context, service=service)
        require_selection = _pin_original_selection(scoped_owner, current)
        controls, reports = [], {}
        packet, run_id = _unentered_future_packet(current)
        terminals = _original_executions(scoped_owner, current,
            observe_controls=lambda index, pins: controls.append((index, pins)), reports=reports)
        if len(controls) != len(domain.RETAINED_PHASES):
            raise PermissionError('source continuation lacks the complete original execution control census')
        active = True

        def require_current():
            if not active:
                raise PermissionError('source continuation execution observation escaped its current custody scope')
            require_selection()
            _require_future_namespaces_absent(current, run_id)
            for index, pins in controls:
                if _custody_control_pins(writer, index) != pins:
                    raise PermissionError('original E1/E2 execution custody changed during the continued operation')
            dependencies.require_current()

        try:
            require_current()
            yield _OriginalExecutionCustody(current, terminals, packet, reports, require_current)
        finally:
            try:
                require_current()
            finally:
                active = False


@contextmanager
def continued_context(owner, context, record):
    """Keep original input custody active while observing inherited E1/E2."""
    if isinstance(record, domain.MatrixProgrammeCompletedSourceContinuation):
        from .matrix_programme_completed_continuation import continued_context as completed_context
        with completed_context(owner, context, record):
            yield
        return
    if record.target_plan != context.plan:
        raise PermissionError('source continuation changes its exact target programme plan')
    original_owner, original_plan = _predecessor(context.service, record.specification)
    if (original_plan.workers != context.plan.workers or original_plan.environment_id != context.plan.environment_id
            or original_plan.specification.operations != context.plan.specification.operations
            or original_plan.source_snapshot == context.plan.source_snapshot):
        raise PermissionError('source continuation changes operations or lacks an actual source handoff')
    # Operation authorities still match each exact retained child candidate.
    # No old plan, binding, package or authority record is rewritten.
    with original_owner._read_context(original_plan, operation=context.operation) as original:
        domain.validate_continued_inputs(original.inputs, context.inputs)
        if tuple((phase, original.binding(phase).identity) for phase in domain.RETAINED_PHASES) != record.predecessor_bindings:
            raise PermissionError('source continuation changes its original E1/E2 bindings')
        with _original_custody(original_owner, original) as retained:
            if retained.terminals != record.predecessor_terminals:
                raise PermissionError('source continuation changes its original E1/E2 execution terminals')
            if retained.training_packet != record.unentered_training_packet:
                raise PermissionError('source continuation changes its original unentered TRAIN packet')
            if any(phase in context.bindings for phase in domain.RETAINED_PHASES):
                raise PermissionError('source continuation cannot author replacement E1/E2 bindings')
            context.phase_origins.update((phase, retained.context) for phase in domain.RETAINED_PHASES)
            context.bindings.update((phase, original.binding(phase)) for phase in domain.RETAINED_PHASES)
            context.retained_execution_reports.update(retained.reports)
            context.continuation_records.append(record)
            yield


def _publish_inputs(original, provenance, publish, *, record_id, completed_source=None):
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.input_records import validate_programme_input_records
    provenance_publication = publish('producing-provenance', provenance, identity=provenance.identity)
    phases, handles = [], []
    for phase in original.phases:
        handle = original.commitments.phase(phase.role)
        if phase.responses is not None:
            assay = original.scientific_design.e2.assay if phase.role == 'e2' else original.scientific_design.training_assay
            responses = domain.rebound_responses(phase, provenance, assay)
            handle = replace(handle, responses=publish(phase.role + '.responses', responses))
            phase = replace(phase, responses=responses)
        phases.append(phase)
        handles.append(handle)
    policy = domain.rebound_e6_policy(original, tuple(phases))
    policy_publication = publish('e6-policy', policy)
    support = original.commitments.support_files
    if completed_source is not None:
        source_publication = publish('completed-e3-input-source', completed_source).publication
        support = tuple(sorted((*support, (completed_source.artifact, source_publication)), key=lambda row: row[0].artifact_id))
    commitments = replace(original.commitments, record_id=record_id, producing_provenance=provenance_publication,
        phases=tuple(handles), e6_policy=policy_publication, support_files=support)
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.input_records import ResolvedMatrixProgrammeInputs
    resolved = ResolvedMatrixProgrammeInputs(commitments, original.scientific_design,
        original.exposure_census, original.exposure_audit, provenance, original.scalar_definitions,
        tuple(phases), original.availability, policy)
    validate_programme_input_records(resolved)
    if completed_source is None:
        domain.validate_continued_inputs(original, resolved)
    else:
        from empirical_lawhood.adapters.methods.matrix_researcher_programme.completed_source import validate_completed_inputs
        validate_completed_inputs(original, resolved, completed_source)
    return publish('commitments', commitments)


@contextmanager
def _current_source_publications(root, admitted):
    """Guard one closed metadata publication group with actual source bytes.

    This owns no execution or outcome authority. Individual writes keep their
    ordinary immutable custody and resource checks. A changed source refuses
    the whole derivation, including after a partial publication or exception.
    """
    require_admitted_target_source_current(root, admitted)
    try:
        yield
    finally:
        require_admitted_target_source_current(root, admitted)


def derive_inputs(*, specification, source_selection_path, project_root, artifact_writer,
        metadata_directory, output_selection_path, execution, read_access=None, _service=None):
    """Publish a source-only handoff; author and execute through ordinary owners."""
    from .experiment_preparation import load_experiment_inputs, prepare_experiment
    from .experiment_programme import ExperimentProgrammeService
    from .matrix_numerical_provenance import capture_matrix_provenance
    from .matrix_programme_allocations import _require_memory
    from .matrix_researcher_programme import _publish
    from .selected_e4_bank_recipe import _current_selection, _metadata_record_size, _publication_from_manifest
    from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest

    if type(specification) not in (domain.MatrixProgrammeSourceContinuationSpecification,
            domain.MatrixProgrammeOutputContinuationSpecification) or read_access is not None:
        raise TypeError('source continuation requires its exact ordinary metadata specification')
    started = monotonic()
    source_bytes = read_bounded_bytes(Path(source_selection_path), maximum_bytes=4 * 1024**2)
    load_experiment_inputs(specification, Path(source_selection_path), artifact_writer=artifact_writer)
    root, admitted = _current_selection(project_root=project_root, artifact_writer=artifact_writer, execution=execution)
    service = _service or ExperimentProgrammeService(root, artifact_writer)
    original_owner, original_plan = _predecessor(service, specification, allow_completed=True)
    if (execution.workers != original_plan.workers or execution.environment_id != original_plan.environment_id
            or execution.source_snapshot == original_plan.source_snapshot):
        raise PermissionError('source continuation preserves workers/environment and requires a new selected source')
    directory = artifact_writer.root.resolve(specification.directory, for_write=True)
    if (Path(metadata_directory) != directory / 'continuation-inputs'
            or Path(output_selection_path) != Path(metadata_directory) / 'inputs/sources.json'):
        raise ValueError('source continuation requires <new-home>/continuation-inputs and its inputs/sources.json selector')
    # No current reader or author has permission to overwrite the original.
    budget = original_plan.specification.operations.metadata_budget
    provenance = capture_matrix_provenance(project_root=root, _admitted_source=admitted)
    publications, output_bytes = [], 0

    def admit_output(raw):
        nonlocal output_bytes
        _require_memory(budget.memory_bytes)
        if budget.wall_time_seconds is not None and monotonic() - started > budget.wall_time_seconds:
            raise ValueError('source continuation exceeds its original finite metadata wall budget')
        output_bytes += len(raw)
        if output_bytes > budget.output_bytes or len(raw) > budget.memory_bytes:
            raise ValueError('source continuation exceeds its original finite metadata budget')
        _metadata_record_size(artifact_writer, len(raw))
        if read_bounded_bytes(Path(source_selection_path), maximum_bytes=len(source_bytes)) != source_bytes:
            raise PermissionError('source continuation changes its copied input selector during derivation')

    def publish_record(path, record):
        admit_output(record.canonical_bytes())
        return _publish(artifact_writer, path, record)

    def publish(key, record, *, identity=None):
        path = Path(metadata_directory) / 'publications' / (key + '.json')
        publish_record(path, record)
        relative = path.relative_to(artifact_writer.root.contract.canonical_path).as_posix()
        publication = _publication_from_manifest(artifact_writer, artifact_writer.read_manifest(relative))
        publications.append(publication)
        pin = record.identity if identity is None else identity
        return MatrixProgrammePublishedInput(pin, publication)

    from contextlib import ExitStack
    from .matrix_programme_completed_continuation import original_completed_custody, require_numerical_continuity
    with original_owner._read_context(original_plan) as original, ExitStack() as lifetime:
        completed = 'e3' in original.bindings
        if completed:
            require_numerical_continuity(original.inputs.producing_provenance, provenance)
        custody = original_completed_custody if completed else _original_custody
        retained = lifetime.enter_context(custody(original_owner, original))
        operations = domain.continued_operations(original_plan.specification.operations, specification,
            completed_phases=retained.phases)
        original = retained.context
        training_packet = retained.training_packet
        terminals = retained.terminals
        before_bindings = tuple((phase, original.binding(phase).identity) for phase in retained.phases)
        if original.inputs.producing_provenance == provenance:
            raise PermissionError('source continuation requires changed actual numerical/source provenance')
        completed_source = None
        original_inputs = original.inputs
        original_commitment = original.plan.specification.input_commitments
        if completed:
            from empirical_lawhood.adapters.methods.matrix_researcher_programme.completed_source import MatrixCompletedE3InputSource
            from empirical_lawhood.infrastructure.matrix_completed_source import original_e3_commitment
            original_commitment = original_e3_commitment(artifact_writer, original.inputs, original_commitment)
            if original_commitment != original.plan.specification.input_commitments:
                from empirical_lawhood.infrastructure.matrix_recorded_inputs import recorded_programme_inputs
                original_inputs = lifetime.enter_context(recorded_programme_inputs(writer=artifact_writer,
                    commitment=original_commitment, maximum_source_bytes=budget.source_scan_bytes))
            completed_source = MatrixCompletedE3InputSource('source.completed-e3.' + specification.fingerprint(),
                specification.identity, original_commitment,
                original_inputs.producing_provenance.identity, provenance.identity)
        # The finite group has one source admission before its first write and
        # a full final guard. Rehashing the whole installation for each metadata
        # record adds no new execution boundary. The continuation seal below
        # still has its separate current-source and original-custody checks.
        lifetime.enter_context(_current_source_publications(root, admitted))
        commitment = _publish_inputs(original_inputs, provenance, publish,
            record_id='commitments.continuation.' + specification.fingerprint(), completed_source=completed_source)
        target = MatrixContinuedProgrammeSpecification('specification.continuation.' + specification.fingerprint(),
            specification.directory, commitment, operations,
            specification.predecessor, specification.identity)
        preparation = prepare_experiment(target, execution=execution)
        kind = domain.MatrixProgrammeCompletedSourceContinuation if completed else domain.MatrixProgrammeSourceContinuation
        extra = (training_packet,) if not completed else ()
        if retained.unentered_e4 is not None:
            kind = domain.MatrixProgrammeUnenteredE4SourceContinuation
            extra = retained.unentered_e4.fields
        elif retained.completed_e4_structure_terminal is not None:
            kind = (domain.MatrixProgrammeCompletedE4OutputContinuation
                if type(specification) is domain.MatrixProgrammeOutputContinuationSpecification
                else domain.MatrixProgrammeCompletedE4SourceContinuation)
            extra = (retained.completed_e4_structure_terminal,)
        record = kind('continuation.' + specification.fingerprint(), specification,
            preparation.programme, before_bindings, terminals, *extra)
        with authenticated_programme_inputs(writer=artifact_writer, commitment=commitment,
                maximum_source_bytes=budget.source_scan_bytes) as current:
            if completed_source is None:
                domain.validate_continued_inputs(original.inputs, current)
            else:
                from empirical_lawhood.adapters.methods.matrix_researcher_programme.completed_source import validate_completed_inputs
                validate_completed_inputs(original_inputs, current, completed_source)
            retained.require_current()
            require_admitted_target_source_current(root, admitted)
            if capture_matrix_provenance(project_root=root, _admitted_source=admitted) != provenance:
                raise PermissionError('current source changed before source-continuation publication')
            continuation_publication = publish_record(directory / domain.CONTINUATION_FILENAME, record)
            selector = ExperimentFileInputSelection('sources.' + target.fingerprint(),
                CONTINUED_PROTOCOL_ID, (), ())
            target_path = Path(metadata_directory) / 'inputs/specification.json'
            target_publication = publish_record(target_path, target)
            source_publication = publish_record(Path(output_selection_path), selector)
            requirements = canonical_json_bytes({'schema': 'empirical-lawhood/operational/experiment-input-requirements',
                'version': '1.0.0', 'value': {'specification': target.identity, 'source_continuation': record.identity,
                    'original_programme': original_plan.identity, 'original_input_commitments': original_plan.specification.input_commitments.record,
                    'continued_input_commitments': commitment.record, 'scientific_design': original.inputs.scientific_design.identity,
                    'retained_execution_phases': retained.phases, 'native_contact': 'NONE',
                    'new_native_contact_count': 0, 'scientific_completion': 'DEFERRED_TO_FULL_READ',
                    'scientific_authority': 'NONE', 'freshness': 'NOT_INFERRED_FROM_SOURCE_CONTINUATION'}})
            relative = (Path(metadata_directory) / 'requirements.json').relative_to(
                artifact_writer.root.contract.canonical_path).as_posix()
            admit_output(requirements)
            requirement_publication = artifact_writer.write(ArtifactWriteRequest('requirements.' + record.fingerprint(),
                relative, 'empirical-lawhood/operational/experiment-input-requirements', ArtifactProfile.CANONICAL_JSON,
                'application/json', record.record_id, Path(relative).parent.as_posix(), requirements,
                VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND))
            require_admitted_target_source_current(root, admitted)
        retained.require_current()
    return ExperimentInputDerivationResult(specification.identity, selector, Path(output_selection_path), preparation,
        (*publications, continuation_publication, target_publication, source_publication, requirement_publication), requirement_publication,
        target, target_path)
