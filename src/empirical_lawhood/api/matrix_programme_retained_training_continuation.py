# SPDX-License-Identifier: MPL-2.0
"""Supported source handoff retaining completed E1/E2/TRAIN without acquisition."""
from contextlib import contextmanager
from dataclasses import dataclass, replace
from pathlib import Path
from time import monotonic

from empirical_lawhood.adapters.methods.matrix_researcher_programme import retained_training_continuation as domain
from empirical_lawhood.adapters.methods.matrix_researcher_programme import source_continuation as source_domain
from empirical_lawhood.adapters.methods.matrix_researcher_programme.frontier import PHASES
from empirical_lawhood.adapters.methods.matrix_researcher_programme.known_inputs import MatrixProgrammePublishedInput
from empirical_lawhood.adapters.methods.matrix_researcher_programme.selection import (
    CONTINUED_PROTOCOL_ID, MatrixContinuedProgrammeSpecification, MatrixResearchProgrammePlan,
)
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
from empirical_lawhood.runtime.native_training_export import NativeTrainingExportAdoptionSelection
from .matrix_researcher_programme_lineage import read_published_record
from .matrix_programme_source_continuation import _pin


def _predecessor(service, specification):
    from .matrix_researcher_programme import MatrixResearchProgrammeService, PLAN_FILENAME
    from .selected_e4_bank_recipe import _publication_from_manifest
    selected, writer = specification.predecessor, service.artifact_writer
    plan = read_published_record(writer, selected.publication.materialization.relative_path,
        MatrixResearchProgrammePlan, selected.publication.materialization.size_bytes)
    selected.require_record(plan, plan.identity)
    if _publication_from_manifest(writer, writer.read_manifest(selected.publication.materialization.relative_path)) != replace(
            selected.publication, created=False):
        raise PermissionError('retained TRAIN continuation changes its exact predecessor publication')
    if (type(plan.specification) is MatrixContinuedProgrammeSpecification
            and plan.specification.continuation_request.object_schema == domain.MatrixProgrammeRetainedTrainingContinuationSpecification.SCHEMA):
        raise PermissionError('retained TRAIN continuation cannot chain a previous retained TRAIN handoff')
    directory = writer.root.resolve(plan.specification.directory, for_write=False)
    if writer.root.resolve(selected.publication.materialization.relative_path, for_write=False) != directory / PLAN_FILENAME:
        raise PermissionError('retained TRAIN continuation changes its original programme home')
    source_domain.require_separate_home(plan.specification.directory, specification.directory)
    owner = service._composite_programme(directory=directory)
    if type(owner) is not MatrixResearchProgrammeService or owner._plan(directory) != plan:
        raise PermissionError('retained TRAIN continuation requires the actual ordinary programme descriptor')
    return owner, plan


def _require_future_unentered(context):
    """Failed metadata is retained; an authored later child is not reusable here."""
    if set(context.bindings) != set(domain.RETAINED_PHASES) or context.pending_bindings:
        raise PermissionError('retained TRAIN continuation requires exactly completed E1/E2/TRAIN bindings')
    for phase in PHASES[3:]:
        paths = (context.child_directory(phase), context.directory / 'bindings' / (phase + '.json'),
            context.directory / 'bindings' / (phase + '.json.manifest.json'))
        for path in paths:
            if path.exists() or path.is_symlink():
                raise PermissionError('retained TRAIN continuation refuses any authored later child or binding: ' + phase)


@dataclass(frozen=True)
class _CompletedCustody:
    context: object
    terminals: tuple
    reports: dict
    require_current: object


@contextmanager
def _completed_custody(owner, context):
    """Original inherited reads remain live; authenticate the remaining census."""
    from .recursive_execution import _custody_control_pins
    from empirical_lawhood.runtime.experiment_programme import MAX_PROGRAMME_DESCRIPTOR_BYTES, PROGRAMME_DESCRIPTOR_FILENAME
    with context.writer.read_context() as writer:
        service = replace(context.service, artifact_writer=writer)
        current = replace(context, service=service)
        scoped_owner = type(owner)(service=service, descriptor=owner.descriptor)
        descriptor = owner.descriptor.canonical_bytes()
        controls, reports, terminals = [], {}, []

        def require_current():
            if not active:
                raise PermissionError('retained TRAIN execution custody escaped its bounded lifetime')
            if scoped_owner._plan(current.directory) != current.plan:
                raise PermissionError('retained TRAIN continuation changes its original programme plan')
            if read_bounded_bytes(current.directory / PROGRAMME_DESCRIPTOR_FILENAME,
                    maximum_bytes=MAX_PROGRAMME_DESCRIPTOR_BYTES) != descriptor:
                raise PermissionError('retained TRAIN continuation changes its original programme descriptor')
            _require_future_unentered(current)
            for index, pins in controls:
                if _custody_control_pins(writer, index) != pins:
                    raise PermissionError('retained TRAIN continuation changes original execution controls')
            writer.require_verification_snapshot()

        active = True
        try:
            require_current()
            for phase in domain.RETAINED_PHASES:
                from empirical_lawhood.adapters.methods.matrix_researcher_programme.selection import MatrixProgrammePhaseBinding
                origin = current.phase_origins.get(phase, current)
                relative = (origin.directory / 'bindings' / (phase + '.json')).relative_to(
                    writer.root.contract.canonical_path).as_posix()
                if read_published_record(writer, relative, MatrixProgrammePhaseBinding, 64 * 1024**2) != current.binding(phase):
                    raise PermissionError('retained TRAIN continuation changes an original phase binding publication')
                current.bound_specification(current.binding(phase))
                report = current.retained_execution_reports.get(phase)
                if report is None:
                    observed = len(controls)
                    report = scoped_owner._read_phase(current, phase, execution_only=True,
                        observe_controls=lambda index, pins: controls.append((index, pins)))
                    if len(controls) != observed + 1:
                        raise PermissionError('retained TRAIN continuation lacks original execution control custody')
                if (report.get('read_scope') != 'EXECUTION_RECORDS' or report.get('execution_complete') is not True
                        or report.get('operational_terminal') != 'AUTHENTICATED'):
                    raise PermissionError('retained TRAIN continuation requires complete original execution: ' + phase)
                terminals.append((phase, _pin(report['terminal'])))
                reports[phase] = report
            require_current()
            yield _CompletedCustody(current, tuple(terminals), reports, require_current)
        finally:
            try:
                require_current()
            finally:
                active = False


def _training_source(context, specification, provenance):
    """Derive the untrusted adoption locator from original authored publications."""
    from .native_training_banks import _read_instance
    from .recursive_authoring import load_authored_wave
    from .recursive_execution import _retained_plans
    from .selected_e4_bank_recipe import _publication_from_manifest
    packet, draft, source, payloads = load_authored_wave(directory=context.child_directory('train'),
        artifact_writer=context.writer, lazy_payloads=True)
    run, plan, _ = _retained_plans(payloads, draft)
    candidate, request, _ = _read_instance(payloads)
    locator = context.native_training_locator()
    if request.input_commitments != context.plan.specification.input_commitments:
        raise PermissionError('retained TRAIN changes its actual original input commitment publication')
    directory = context.metadata_directory('train') / 'bank-export'
    publications = tuple(_publication_from_manifest(context.writer, context.writer.read_manifest(
        (directory / (name + '.json')).relative_to(context.writer.root.contract.canonical_path).as_posix()))
        for name in ('allocation', 'features', 'outcomes'))
    adoption = NativeTrainingExportAdoptionSelection('adoption.' + specification.fingerprint(),
        locator.authored_directory, run.run_plan_id, ObjectIdentity.from_record(packet.packet_id, packet),
        ObjectIdentity.from_record(plan.execution_plan_id, plan), source, candidate.identity, request.identity,
        'export.' + context.namespace + '.train', publications)
    return domain.MatrixRetainedTrainingSource('retained-training.' + specification.fingerprint(),
        specification.predecessor, context.plan.specification.input_commitments, locator, adoption,
        provenance.identity, specification.identity)


@contextmanager
def continued_context(owner, context, record):
    if record.target_plan != context.plan:
        raise PermissionError('retained TRAIN continuation changes its selected target programme')
    original_owner, original_plan = _predecessor(context.service, record.specification)
    if ((original_plan.workers, original_plan.environment_id, original_plan.specification.operations) != (
            context.plan.workers, context.plan.environment_id, context.plan.specification.operations)
            or original_plan.source_snapshot == context.plan.source_snapshot):
        raise PermissionError('retained TRAIN continuation changes operations or lacks a source transition')
    with original_owner._read_context(original_plan, operation=context.operation) as original:
        domain.validate_retained_inputs(original.inputs, context.inputs, record.retained_training)
        if read_retained_training_source(context.writer, context.commitments) != record.retained_training:
            raise PermissionError('retained TRAIN continuation changes its required input source lineage')
        if tuple((phase, original.binding(phase).identity) for phase in domain.RETAINED_PHASES) != record.predecessor_bindings:
            raise PermissionError('retained TRAIN continuation changes original phase bindings')
        with _completed_custody(original_owner, original) as retained:
            if (retained.terminals != record.predecessor_terminals
                    or _training_source(retained.context, record.specification,
                        context.inputs.producing_provenance) != record.retained_training):
                raise PermissionError('retained TRAIN continuation changes original terminals or bank locators')
            if any(phase in context.bindings for phase in domain.RETAINED_PHASES):
                raise PermissionError('retained TRAIN continuation cannot author replacement original bindings')
            context.phase_origins.update((phase, retained.context.phase_origins.get(phase, retained.context))
                for phase in domain.RETAINED_PHASES)
            context.bindings.update((phase, original.binding(phase)) for phase in domain.RETAINED_PHASES)
            context.retained_execution_reports.update(retained.reports)
            context.continuation_records.extend(original.continuation_records)
            context.amendment_records.extend(original.amendment_records)
            context.continuation_records.append(record)
            yield


@contextmanager
def authenticated_e3_continuation(*, project_root, artifact_writer, selected, execution):
    """Open the published handoff through its ordinary programme owner."""
    from .experiment_programme import ExperimentProgrammeService
    from .selected_e4_bank_recipe import _publication_from_manifest
    if type(selected) is not MatrixProgrammePublishedInput:
        raise TypeError('continued E3 requires its exact published retained TRAIN handoff')
    selected.require_kind(domain.MatrixProgrammeRetainedTrainingContinuation)
    record = read_published_record(artifact_writer, selected.publication.materialization.relative_path,
        domain.MatrixProgrammeRetainedTrainingContinuation, selected.publication.materialization.size_bytes)
    selected.require_record(record, record.identity)
    if _publication_from_manifest(artifact_writer, artifact_writer.read_manifest(
            selected.publication.materialization.relative_path)) != replace(selected.publication, created=False):
        raise PermissionError('continued E3 changes its original handoff publication')
    service = ExperimentProgrammeService(Path(project_root).resolve(strict=True), artifact_writer)
    directory = artifact_writer.root.resolve(record.target_plan.specification.directory, for_write=False)
    if artifact_writer.root.resolve(selected.publication.materialization.relative_path,
            for_write=False) != directory / domain.CONTINUATION_FILENAME:
        raise PermissionError('continued E3 changes its required handoff home')
    owner = service._composite_programme(directory=directory)
    if owner._plan(directory) != record.target_plan:
        raise PermissionError('continued E3 changes its actual authored target programme')
    with owner._context(record.target_plan) as context:
        if context.execution != execution or record not in context.continuation_records:
            raise PermissionError('continued E3 changes its selected source/environment or retained TRAIN lineage')
        yield context


def continued_e3_future(context, *, assembly_request, training_request, scientific_protocol, candidate, export_adoption):
    """Rebind only authenticated original future inputs to the admitted source."""
    retained = read_retained_training_source(context.writer, context.commitments)
    if (assembly_request.native_training_locator != retained.training_locator
            or training_request.input_commitments != retained.input_commitments
            or training_request.identity != retained.export_adoption.request
            or export_adoption != retained.export_adoption
            or candidate != context.design.e3 or scientific_protocol != context.design.training_protocol):
        raise PermissionError('continued E3 substitutes original TRAIN or changes its frozen scientific design')
    manifest = replace(training_request.future_manifest,
        record_id=training_request.future_manifest.record_id + '.source.' + retained.fingerprint(),
        provenances=(context.inputs.producing_provenance,))
    roles = (('CALIBRATION', 'e3.calibration'), ('EVALUATION', 'e3.confirmation'),
        ('TRANSFER_NEARBY', 'e6.nearby'), ('TRANSFER_SHIFTED', 'e6.shifted'))
    responses = {role: context.inputs.phase(phase).responses for role, phase in roles}
    return manifest, responses, retained


def _publish_inputs(original, provenance, retained, support, publish, *, record_id):
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.input_records import validate_programme_input_records
    provenance_publication = publish('producing-provenance', provenance, identity=provenance.identity)
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
    commitments = replace(original.commitments, record_id=record_id, producing_provenance=provenance_publication,
        phases=tuple(handles), e6_policy=publish('e6-policy', policy),
        support_files=tuple(sorted((*original.commitments.support_files, (retained.artifact, support)),
            key=lambda row: row[0].artifact_id)))
    resolved = replace(original, commitments=commitments, producing_provenance=provenance,
        phases=tuple(phases), e6_policy=policy)
    validate_programme_input_records(resolved)
    domain.validate_retained_inputs(original, resolved, retained)
    return publish('commitments', commitments)


def derive_inputs(*, specification, source_selection_path, project_root, artifact_writer,
        metadata_directory, output_selection_path, execution, read_access=None):
    from .experiment_preparation import load_experiment_inputs, prepare_experiment
    from .experiment_programme import ExperimentProgrammeService
    from .matrix_numerical_provenance import capture_matrix_provenance
    from .matrix_programme_allocations import _require_memory
    from .matrix_researcher_programme import _publish
    from .selected_e4_bank_recipe import _current_selection, _metadata_record_size, _publication_from_manifest
    if type(specification) is not domain.MatrixProgrammeRetainedTrainingContinuationSpecification or read_access is not None:
        raise TypeError('retained TRAIN continuation requires its exact ordinary metadata specification')
    started = monotonic()
    source_bytes = read_bounded_bytes(Path(source_selection_path), maximum_bytes=4 * 1024**2)
    load_experiment_inputs(specification, Path(source_selection_path), artifact_writer=artifact_writer)
    root, admitted = _current_selection(project_root=project_root, artifact_writer=artifact_writer, execution=execution)
    service = ExperimentProgrammeService(root, artifact_writer)
    original_owner, original_plan = _predecessor(service, specification)
    if ((execution.workers, execution.environment_id) != (original_plan.workers, original_plan.environment_id)
            or execution.source_snapshot == original_plan.source_snapshot):
        raise PermissionError('retained TRAIN continuation preserves workers/environment and requires a new source')
    directory = artifact_writer.root.resolve(specification.directory, for_write=True)
    if (Path(metadata_directory) != directory / 'continuation-inputs'
            or Path(output_selection_path) != Path(metadata_directory) / 'inputs/sources.json'):
        raise ValueError('retained TRAIN continuation requires <new-home>/continuation-inputs and inputs/sources.json')
    budget = original_plan.specification.operations.metadata_budget
    provenance = capture_matrix_provenance(project_root=root, _admitted_source=admitted)
    publications, output_bytes = [], 0

    def admit_output(raw):
        nonlocal output_bytes
        _require_memory(budget.memory_bytes)
        if budget.wall_time_seconds is not None and monotonic() - started > budget.wall_time_seconds:
            raise ValueError('retained TRAIN continuation exceeds its selected metadata wall budget')
        output_bytes += len(raw)
        if output_bytes > budget.output_bytes or len(raw) > budget.memory_bytes:
            raise ValueError('retained TRAIN continuation exceeds its selected metadata byte budget')
        _metadata_record_size(artifact_writer, len(raw))
        if read_bounded_bytes(Path(source_selection_path), maximum_bytes=len(source_bytes)) != source_bytes:
            raise PermissionError('retained TRAIN continuation changes its copied selector')
        require_admitted_target_source_current(root, admitted)

    def publish_record(path, record):
        admit_output(record.canonical_bytes())
        return _publish(artifact_writer, path, record)

    def publish(key, record, *, identity=None):
        path = Path(metadata_directory) / 'publications' / (key + '.json')
        publish_record(path, record)
        relative = path.relative_to(artifact_writer.root.contract.canonical_path).as_posix()
        publication = _publication_from_manifest(artifact_writer, artifact_writer.read_manifest(relative))
        publications.append(publication)
        return MatrixProgrammePublishedInput(record.identity if identity is None else identity, publication)

    with original_owner._read_context(original_plan) as original, _completed_custody(original_owner, original) as retained:
        original = retained.context
        lineage = _training_source(original, specification, provenance)
        raw = lineage.canonical_bytes()
        admit_output(raw)
        relative = (Path(metadata_directory) / 'publications/retained-training-source.json').relative_to(
            artifact_writer.root.contract.canonical_path).as_posix()
        support = artifact_writer.write(ArtifactWriteRequest(lineage.record_id, relative, lineage.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, 'application/json', lineage.record_id,
            Path(relative).parent.as_posix(), raw, VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND))
        publications.append(support)
        commitment = _publish_inputs(original.inputs, provenance, lineage, support, publish,
            record_id='commitments.retained-training.' + specification.fingerprint())
        target = MatrixContinuedProgrammeSpecification('specification.retained-training.' + specification.fingerprint(),
            specification.directory, commitment, original_plan.specification.operations,
            specification.predecessor, specification.identity)
        preparation = prepare_experiment(target, execution=execution)
        record = domain.MatrixProgrammeRetainedTrainingContinuation('continuation.' + specification.fingerprint(),
            specification, preparation.programme,
            tuple((phase, original.binding(phase).identity) for phase in domain.RETAINED_PHASES), retained.terminals, lineage)
        with authenticated_programme_inputs(writer=artifact_writer, commitment=commitment,
                maximum_source_bytes=budget.source_scan_bytes) as current:
            domain.validate_retained_inputs(original.inputs, current, lineage)
            retained.require_current()
            require_admitted_target_source_current(root, admitted)
            if capture_matrix_provenance(project_root=root, _admitted_source=admitted) != provenance:
                raise PermissionError('current source changed before retained TRAIN continuation publication')
            continuation_publication = publish_record(directory / domain.CONTINUATION_FILENAME, record)
            selector = ExperimentFileInputSelection('sources.' + target.fingerprint(), CONTINUED_PROTOCOL_ID, (), ())
            target_path = Path(metadata_directory) / 'inputs/specification.json'
            target_publication = publish_record(target_path, target)
            source_publication = publish_record(Path(output_selection_path), selector)
            requirements = canonical_json_bytes({'schema': 'empirical-lawhood/operational/experiment-input-requirements',
                'version': '1.0.0', 'value': {'specification': target.identity, 'source_continuation': record.identity,
                    'original_programme': original_plan.identity, 'original_input_commitments': lineage.input_commitments.record,
                    'continued_input_commitments': commitment.record, 'scientific_design': original.design.identity,
                    'retained_execution_phases': domain.RETAINED_PHASES, 'retained_training': lineage.identity,
                    'bank_validation': 'DEFERRED_TO_RECEIPT_BOUND_ADOPTION', 'native_contact': 'NONE',
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
        (*publications, continuation_publication, target_publication, source_publication, requirement_publication),
        requirement_publication, target, target_path)
