# SPDX-License-Identifier: MPL-2.0
"""Public source transition retaining an entered E3 before any future response."""
from contextlib import contextmanager
from dataclasses import fields, replace
from pathlib import Path
from time import monotonic

from empirical_lawhood.adapters.methods.matrix_researcher_programme import retained_e3_continuation as domain
from empirical_lawhood.adapters.methods.matrix_researcher_programme import e3_closeout as closeout_domain
from empirical_lawhood.adapters.methods.matrix_researcher_programme import retained_training_continuation as training_domain
from empirical_lawhood.adapters.methods.matrix_researcher_programme import source_continuation as source_domain
from empirical_lawhood.adapters.methods.matrix_researcher_programme.frontier import PHASES
from empirical_lawhood.adapters.methods.matrix_researcher_programme.known_inputs import MatrixProgrammePublishedInput
from empirical_lawhood.adapters.methods.matrix_researcher_programme.selection import CONTINUED_PROTOCOL_ID, MatrixContinuedProgrammeSpecification, MatrixResearchProgrammePlan
from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.infrastructure.matrix_programme_inputs import authenticated_programme_inputs
from empirical_lawhood.infrastructure.matrix_retained_training import read_retained_training_source
from empirical_lawhood.infrastructure.source_closure import require_admitted_target_source_current
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputSelection
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.experiment_preparation import ExperimentInputDerivationResult

from .configured_e3_retained_custody import read_original_partial_e3
from .matrix_researcher_programme_lineage import read_published_record, retained_run_binding


def _predecessor(service, request):
    from .matrix_researcher_programme import MatrixResearchProgrammeService, PLAN_FILENAME
    from .selected_e4_bank_recipe import _publication_from_manifest
    writer, selected = service.artifact_writer, request.predecessor
    plan = read_published_record(writer, selected.publication.materialization.relative_path,
        MatrixResearchProgrammePlan, selected.publication.materialization.size_bytes)
    selected.require_record(plan, plan.identity)
    if _publication_from_manifest(writer, writer.read_manifest(selected.publication.materialization.relative_path)) != replace(
            selected.publication, created=False):
        raise PermissionError('retained E3 continuation changes its actual predecessor publication')
    if (type(plan.specification) is not MatrixContinuedProgrammeSpecification
            or plan.specification.continuation_request.object_schema not in (
                training_domain.MatrixProgrammeRetainedTrainingContinuationSpecification.SCHEMA,
                domain.MatrixProgrammeRetainedE3ContinuationSpecification.SCHEMA)):
        raise PermissionError('retained E3 requires its actual retained-TRAIN or stopped retained-E3 programme')
    directory = writer.root.resolve(plan.specification.directory, for_write=False)
    if writer.root.resolve(selected.publication.materialization.relative_path, for_write=False) != directory / PLAN_FILENAME:
        raise PermissionError('retained E3 continuation changes its actual original programme home')
    source_domain.require_separate_home(plan.specification.directory, request.directory)
    owner = service._composite_programme(directory=directory)
    if type(owner) is not MatrixResearchProgrammeService or owner._plan(directory) != plan:
        raise PermissionError('retained E3 continuation requires its actual original programme descriptor')
    return owner, plan


def _require_original_frontier(context):
    if set(context.bindings) != {'e1', 'e2', 'train', 'e3'} or context.pending_bindings:
        raise PermissionError('retained E3 requires its original E1/E2/TRAIN and entered E3 bindings')
    for phase in PHASES[4:]:
        for path in (context.child_directory(phase), context.directory / 'bindings' / (phase + '.json'),
                context.directory / 'bindings' / (phase + '.json.manifest.json'),
                context.directory / 'runs' / (phase + '.main.json')):
            if path.exists() or path.is_symlink():
                raise PermissionError('retained E3 continuation refuses an authored later phase: ' + phase)


def _inherited_terminals(context):
    from .matrix_programme_source_continuation import _pin
    rows = []
    for phase in training_domain.RETAINED_PHASES:
        report = context.retained_execution_reports.get(phase)
        if (report is None or report.get('read_scope') != 'EXECUTION_RECORDS'
                or report.get('execution_complete') is not True or report.get('operational_terminal') != 'AUTHENTICATED'):
            raise PermissionError('retained E3 loses its live original E1/E2/TRAIN execution custody')
        rows.append((phase, _pin(report['terminal'])))
    return tuple(rows)


def _training_source(original, request, provenance):
    if type(original) not in (training_domain.MatrixRetainedTrainingSource, domain.MatrixE3RetainedTrainingSource):
        raise PermissionError('retained E3 requires its exact original retained TRAIN source')
    kind = (closeout_domain.MatrixE3ClosedTrainingSource if type(request) is closeout_domain.MatrixProgrammeE3CloseoutSpecification
        else domain.MatrixE3RetainedTrainingSource)
    return kind(**{
        field.name: getattr(original, field.name) for field in fields(original)
        if field.name not in ('record_id', 'target_provenance', 'continuation_request')},
        record_id='retained-training.e3.' + request.fingerprint(),
        target_provenance=provenance.identity, continuation_request=request.identity)


@contextmanager
def _original_partial(context, request):
    _require_original_frontier(context)
    run = retained_run_binding(context, 'e3')
    if run is None or run.run_id == request.continued_e3_run_id:
        raise PermissionError('retained E3 requires the exact original entered run and a distinct continuation')
    context.bound_specification(context.binding('e3'))
    relative = context.child_directory('e3').relative_to(context.writer.root.contract.canonical_path).as_posix()
    from .configured_e3_unfinished_custody import read_unfinished_e3
    reader = (read_unfinished_e3 if context.plan.specification.continuation_request.object_schema ==
        domain.MatrixProgrammeRetainedE3ContinuationSpecification.SCHEMA else read_original_partial_e3)
    if type(request) is closeout_domain.MatrixProgrammeE3CloseoutSpecification:
        from .configured_e3_closeout_custody import read_closed_e3
        reader = read_closed_e3
    with reader(artifact_writer=context.writer, directory=relative, run_id=run.run_id,
            reveal_authority_id=request.original_reveal_authority_id) as partial:
        if (run.package != ObjectIdentity.from_record(partial.package.package_id, partial.package)
                or run.specification != partial.specification.identity
                or context.binding('e3').specification.identity != partial.specification.identity):
            raise PermissionError('retained E3 changes its original programme run or scientific specification')
        yield run, partial
        _require_original_frontier(context)
        if retained_run_binding(context, 'e3') != run:
            raise PermissionError('retained E3 original run locator changed during its read')
        partial.require_access()


@contextmanager
def continued_context(owner, context, record):
    if record.target_plan != context.plan:
        raise PermissionError('retained E3 continuation changes its exact target programme')
    original_owner, original_plan = _predecessor(context.service, record.specification)
    if ((original_plan.workers, original_plan.environment_id, original_plan.specification.operations) != (
            context.plan.workers, context.plan.environment_id, context.plan.specification.operations)
            or original_plan.source_snapshot == context.plan.source_snapshot):
        raise PermissionError('retained E3 continuation changes operations or lacks a separate source')
    with original_owner._read_context(original_plan) as original, _original_partial(original, record.specification) as (run, partial):
        old_training = read_retained_training_source(original.writer, original.commitments)
        retained_training = _training_source(old_training, record.specification, context.inputs.producing_provenance)
        retention, tasks = partial.continuation(record_id=record.retained_e3.record_id,
            continued_run_id=record.specification.continued_e3_run_id, response_provenance=context.inputs.producing_provenance)
        if type(record) is domain.MatrixProgrammeUnfinishedE3Continuation:
            if partial.unfinished(record_id=record.unfinished.record_id, retention=retention) != record.unfinished:
                raise PermissionError('unfinished E3 changes its actual predecessor receipts or remaining work')
        if type(record) is closeout_domain.MatrixProgrammeClosedE3Continuation:
            if partial.closeout(record_id=record.closeout.record_id, retention=retention) != record.closeout:
                raise PermissionError('CAL closeout changes original contacts, resource history or remaining work')
        if (retention != record.retained_e3 or old_training != record.predecessor_training
                or retained_training != record.retained_training
                or read_retained_training_source(context.writer, context.commitments) != retained_training
                or record.predecessor_e3_binding != original.binding('e3').identity
                or record.predecessor_e3_run != run.identity
                or record.predecessor_terminals != _inherited_terminals(original)
                or record.predecessor_bindings != tuple((phase, original.binding(phase).identity) for phase in training_domain.RETAINED_PHASES)):
            raise PermissionError('retained E3 continuation changes original receipts, run, models or inherited phases')
        domain.validate_retained_e3_inputs(original.inputs, context.inputs, old_training, retained_training)
        if any(phase in context.bindings for phase in training_domain.RETAINED_PHASES):
            raise PermissionError('retained E3 continuation cannot replace original E1/E2/TRAIN bindings')
        context.phase_origins.update((phase, original.phase_origins.get(phase, original)) for phase in training_domain.RETAINED_PHASES)
        context.bindings.update((phase, original.binding(phase)) for phase in training_domain.RETAINED_PHASES)
        context.retained_execution_reports.update(original.retained_execution_reports)
        context.continuation_records.extend(original.continuation_records)
        context.amendment_records.extend(original.amendment_records)
        context.continuation_records.append(record)
        context.retained_e3.append((record, partial, tasks))
        yield
        partial.require_access()


def _publish_inputs(original, provenance, old_training, retained, support, publish, *, record_id):
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.input_records import validate_programme_input_records
    phases, handles = [], []
    for phase in original.phases:
        handle = original.commitments.phase(phase.role)
        if phase.responses is not None:
            assay = original.scientific_design.e2.assay if phase.role == 'e2' else original.scientific_design.training_assay
            responses = source_domain.rebound_responses(phase, provenance, assay)
            handle = replace(handle, responses=publish(phase.role + '.responses', responses))
            phase = replace(phase, responses=responses)
        phases.append(phase)
        handles.append(handle)
    policy = source_domain.rebound_e6_policy(original, tuple(phases))
    removed = training_domain.retained_source_files(original.commitments)
    commitments = replace(original.commitments, record_id=record_id,
        producing_provenance=publish('producing-provenance', provenance, identity=provenance.identity),
        phases=tuple(handles), e6_policy=publish('e6-policy', policy),
        support_files=tuple(sorted((*tuple(row for row in original.commitments.support_files if row not in removed),
            (retained.artifact, support)), key=lambda row: row[0].artifact_id)))
    resolved = replace(original, commitments=commitments, producing_provenance=provenance, phases=tuple(phases), e6_policy=policy)
    validate_programme_input_records(resolved)
    domain.validate_retained_e3_inputs(original, resolved, old_training, retained)
    return publish('commitments', commitments)


def derive_inputs(*, specification, source_selection_path, project_root, artifact_writer,
        metadata_directory, output_selection_path, execution, read_access=None):
    from .experiment_preparation import load_experiment_inputs, prepare_experiment
    from .experiment_programme import ExperimentProgrammeService
    from .matrix_numerical_provenance import capture_matrix_provenance
    from .matrix_programme_allocations import _require_memory
    from .matrix_researcher_programme import _publish
    from .selected_e4_bank_recipe import _current_selection, _metadata_record_size, _publication_from_manifest
    if type(specification) not in (domain.MatrixProgrammeRetainedE3ContinuationSpecification,
            closeout_domain.MatrixProgrammeE3CloseoutSpecification) or read_access is not None:
        raise TypeError('retained E3 continuation requires its exact ordinary source-transition specification')
    started = monotonic()
    original_bytes = read_bounded_bytes(Path(source_selection_path), maximum_bytes=4 * 1024**2)
    load_experiment_inputs(specification, Path(source_selection_path), artifact_writer=artifact_writer)
    root, admitted = _current_selection(project_root=project_root, artifact_writer=artifact_writer, execution=execution)
    service = ExperimentProgrammeService(root, artifact_writer)
    original_owner, original_plan = _predecessor(service, specification)
    if ((execution.workers, execution.environment_id) != (original_plan.workers, original_plan.environment_id)
            or execution.source_snapshot == original_plan.source_snapshot):
        raise PermissionError('retained E3 requires the selected original worker/environment capacity and a new source')
    directory = artifact_writer.root.resolve(specification.directory, for_write=True)
    if (Path(metadata_directory) != directory / 'continuation-inputs'
            or Path(output_selection_path) != Path(metadata_directory) / 'inputs/sources.json'):
        raise ValueError('retained E3 requires <new-home>/continuation-inputs and inputs/sources.json')
    provenance = capture_matrix_provenance(project_root=root, _admitted_source=admitted)
    budget = original_plan.specification.operations.metadata_budget
    publications, output_bytes = [], 0

    def admit(raw):
        nonlocal output_bytes
        _require_memory(budget.memory_bytes)
        output_bytes += len(raw)
        if (budget.wall_time_seconds is not None and monotonic() - started > budget.wall_time_seconds
                or output_bytes > budget.output_bytes or len(raw) > budget.memory_bytes):
            raise ValueError('retained E3 continuation exceeds its selected metadata budget')
        _metadata_record_size(artifact_writer, len(raw))
        if read_bounded_bytes(Path(source_selection_path), maximum_bytes=len(original_bytes)) != original_bytes:
            raise PermissionError('retained E3 continuation changes its copied selector')
        require_admitted_target_source_current(root, admitted)

    def publish_record(path, record):
        admit(record.canonical_bytes())
        return _publish(artifact_writer, path, record)

    def publish(key, record, *, identity=None):
        path = Path(metadata_directory) / 'publications' / (key + '.json')
        publish_record(path, record)
        relative = path.relative_to(artifact_writer.root.contract.canonical_path).as_posix()
        publication = _publication_from_manifest(artifact_writer, artifact_writer.read_manifest(relative))
        publications.append(publication)
        return MatrixProgrammePublishedInput(record.identity if identity is None else identity, publication)

    with original_owner._read_context(original_plan) as original, _original_partial(original, specification) as (run, partial):
        old_training = read_retained_training_source(original.writer, original.commitments)
        retained = _training_source(old_training, specification, provenance)
        retention, _ = partial.continuation(record_id='retained-e3.' + specification.fingerprint(),
            continued_run_id=specification.continued_e3_run_id, response_provenance=provenance)
        raw = retained.canonical_bytes()
        admit(raw)
        relative = (Path(metadata_directory) / 'publications/retained-training-source.json').relative_to(
            artifact_writer.root.contract.canonical_path).as_posix()
        support = artifact_writer.write(ArtifactWriteRequest(retained.record_id, relative, retained.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, 'application/json', retained.record_id, Path(relative).parent.as_posix(), raw,
            VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND))
        publications.append(support)
        commitment = _publish_inputs(original.inputs, provenance, old_training, retained, support, publish,
            record_id='commitments.retained-e3.' + specification.fingerprint())
        target = MatrixContinuedProgrammeSpecification('specification.retained-e3.' + specification.fingerprint(),
            specification.directory, commitment, original_plan.specification.operations, specification.predecessor, specification.identity)
        preparation = prepare_experiment(target, execution=execution)
        closed = type(specification) is closeout_domain.MatrixProgrammeE3CloseoutSpecification
        closeout = partial.closeout(record_id='closed-e3.' + specification.fingerprint(), retention=retention) if closed else None
        unfinished = (partial.unfinished(record_id='unfinished-e3.' + specification.fingerprint(), retention=retention)
            if not closed and type(old_training) is domain.MatrixE3RetainedTrainingSource else None)
        record_type = (domain.MatrixProgrammeRetainedE3Continuation if unfinished is None
            else domain.MatrixProgrammeUnfinishedE3Continuation)
        if closed:
            record_type = closeout_domain.MatrixProgrammeClosedE3Continuation
        boundary = closeout if closed else unfinished
        record = record_type('continuation.e3.' + specification.fingerprint(), specification,
            preparation.programme, tuple((phase, original.binding(phase).identity) for phase in training_domain.RETAINED_PHASES),
            _inherited_terminals(original), original.binding('e3').identity, run.identity, old_training, retained, retention,
            **({'closeout': closeout} if closed else {} if unfinished is None else {'unfinished': unfinished}))
        with authenticated_programme_inputs(writer=artifact_writer, commitment=commitment,
                maximum_source_bytes=budget.source_scan_bytes) as current:
            domain.validate_retained_e3_inputs(original.inputs, current, old_training, retained)
            partial.require_current()
            require_admitted_target_source_current(root, admitted)
            if capture_matrix_provenance(project_root=root, _admitted_source=admitted) != provenance:
                raise PermissionError('retained E3 target source changed before continuation publication')
            continuation_publication = publish_record(directory / domain.CONTINUATION_FILENAME, record)
            selector = ExperimentFileInputSelection('sources.' + target.fingerprint(), CONTINUED_PROTOCOL_ID, (), ())
            target_path = Path(metadata_directory) / 'inputs/specification.json'
            target_publication = publish_record(target_path, target)
            source_publication = publish_record(Path(output_selection_path), selector)
            requirements = canonical_json_bytes({'schema': 'empirical-lawhood/operational/experiment-input-requirements',
                'version': '1.0.0', 'value': {'specification': target.identity, 'source_continuation': record.identity,
                    'original_programme': original_plan.identity, 'retained_e3': retention.identity,
                    'original_terminal': retention.original_terminal,
                    'retained_completed_tasks': len(retention.completed_receipts) if boundary is None else len(boundary.completed_receipts),
                    'unfinished_execution': None if unfinished is None else unfinished.identity,
                    'closed_cal_execution': None if closeout is None else closeout.identity,
                    'selected_tasks': None if boundary is None else len(boundary.unfinished_task_ids),
                    'original_fitted_freeze': retention.model_freeze,
                    'future_native_contact_count': 0 if closeout is None else len(closeout.calibration_roots),
                    'excluded_uncertain_native_tasks': () if closeout is None else closeout.excluded_native_task_ids,
                    'native_contact': 'NONE', 'scientific_completion': 'DEFERRED_TO_FULL_READ',
                    'scientific_authority': 'NONE', 'freshness': 'NOT_INFERRED_FROM_SOURCE_CONTINUATION'}})
            relative = (Path(metadata_directory) / 'requirements.json').relative_to(artifact_writer.root.contract.canonical_path).as_posix()
            admit(requirements)
            requirement_publication = artifact_writer.write(ArtifactWriteRequest('requirements.' + record.fingerprint(), relative,
                'empirical-lawhood/operational/experiment-input-requirements', ArtifactProfile.CANONICAL_JSON,
                'application/json', record.record_id, Path(relative).parent.as_posix(), requirements,
                VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND))
            # The owning partial-read context checks all custody on exit.
            # Keep the explicit full guard above before publication begins.
            require_admitted_target_source_current(root, admitted)
    return ExperimentInputDerivationResult(specification.identity, selector, Path(output_selection_path), preparation,
        (*publications, continuation_publication, target_publication, source_publication, requirement_publication),
        requirement_publication, target, target_path)
