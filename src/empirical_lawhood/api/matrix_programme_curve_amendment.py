# SPDX-License-Identifier: MPL-2.0
"""Prospective scientific amendment with original E1/E2 custody and no entry."""
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
from time import monotonic

from empirical_lawhood.adapters.methods.matrix_researcher_programme import curve_amendment as domain
from empirical_lawhood.adapters.methods.matrix_researcher_programme.curve_amendment_design import amend_curve_design
from empirical_lawhood.adapters.methods.matrix_researcher_programme.known_inputs import (
    MatrixProgrammePublishedInput,
)
from empirical_lawhood.adapters.methods.matrix_researcher_programme.selection import (
    AMENDED_PROTOCOL_ID, MatrixCurveAmendedProgrammeSpecification,
)
from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.infrastructure.matrix_programme_inputs import authenticated_programme_inputs
from empirical_lawhood.infrastructure.source_closure import require_admitted_target_source_current
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputSelection
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.experiment_preparation import ExperimentInputDerivationResult
from .matrix_amendment_evidence import evidence_snapshots, publish_evidence, read_evidence, validate_evidence
from .matrix_amendment_withdrawals import withdrawn_custody
from .matrix_programme_source_continuation import _original_custody, _predecessor


@contextmanager
def amended_context(owner, context, record):
    if record.target_plan != context.plan:
        raise PermissionError('curve amendment changes its exact selected target programme')
    original_owner, original_plan = _predecessor(context.service, record.specification)
    if ((original_plan.workers, original_plan.environment_id, original_plan.specification.operations) != (
            context.plan.workers, context.plan.environment_id, context.plan.specification.operations)
            or original_plan.source_snapshot == context.plan.source_snapshot):
        raise PermissionError('curve amendment changes operations or lacks its actual revised source')
    with original_owner._read_context(original_plan, operation=context.operation) as original:
        domain.validate_amended_inputs(original.inputs, context.inputs)
        bindings = tuple((phase, original.binding(phase).identity) for phase in domain.RETAINED_PHASES)
        if (bindings != record.predecessor_bindings
                or domain.amendment_exposure(original.inputs, original.bindings) != record.exposure):
            raise PermissionError('curve amendment changes the complete original exposure and phase binding census')
        read_evidence(context.writer, record, original.inputs.producing_provenance)
        with _original_custody(original_owner, original) as retained, withdrawn_custody(
                context.service, record.specification, original_plan, bindings, retained) as (withdrawn, require_withdrawn):
            if (retained.terminals != record.predecessor_terminals
                    or retained.training_packet != record.unentered_training_packet
                    or withdrawn != record.withdrawn_training_packets):
                raise PermissionError('curve amendment changes original execution or superseded TRAIN nonentry custody')
            if any(phase in context.bindings for phase in domain.RETAINED_PHASES):
                raise PermissionError('curve amendment cannot author replacement E1/E2 bindings')
            context.phase_origins.update((phase, retained.context) for phase in domain.RETAINED_PHASES)
            context.bindings.update((phase, original.binding(phase)) for phase in domain.RETAINED_PHASES)
            context.retained_execution_reports.update(retained.reports)
            context.amendment_records.append(record)
            yield
            require_withdrawn()


def _publish_inputs(original, provenance, publish, *, record_id):
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.input_records import validate_programme_input_records
    design = amend_curve_design(original.scientific_design, record_id='design.' + record_id)
    design_publication = publish('scientific-design', design)
    provenance_publication = publish('producing-provenance', provenance, identity=provenance.identity)
    phases, handles = [], []
    for phase in original.phases:
        handle = original.commitments.phase(phase.role)
        if phase.responses is not None:
            assay = design.e2.assay if phase.role == 'e2' else design.training_assay
            responses = domain.rebound_responses(phase, provenance, assay)
            handle = replace(handle, responses=publish(phase.role + '.responses', responses))
            phase = replace(phase, responses=responses)
        phases.append(phase)
        handles.append(handle)
    policy = domain.amended_e6_policy(original, tuple(phases), design)
    commitments = replace(original.commitments, record_id=record_id, scientific_design=design_publication,
        producing_provenance=provenance_publication, phases=tuple(handles), e6_policy=publish('e6-policy', policy))
    resolved = replace(original, commitments=commitments, scientific_design=design, producing_provenance=provenance,
        phases=tuple(phases), e6_policy=policy)
    validate_programme_input_records(resolved)
    domain.validate_amended_inputs(original, resolved)
    return publish('commitments', commitments)


def derive_inputs(*, specification, source_selection_path, project_root, artifact_writer,
        metadata_directory, output_selection_path, execution, read_access=None):
    from .experiment_preparation import load_experiment_inputs, prepare_experiment
    from .experiment_programme import ExperimentProgrammeService
    from .matrix_numerical_provenance import capture_matrix_provenance
    from .matrix_programme_allocations import _require_memory
    from .matrix_researcher_programme import _publish
    from .selected_e4_bank_recipe import _current_selection, _metadata_record_size, _publication_from_manifest

    if type(specification) is not domain.MatrixProgrammeCurveAmendmentSpecification or read_access is not None:
        raise TypeError('curve amendment requires its exact ordinary metadata selection')
    started = monotonic()
    source_bytes = read_bounded_bytes(Path(source_selection_path), maximum_bytes=4 * 1024**2)
    load_experiment_inputs(specification, Path(source_selection_path), artifact_writer=artifact_writer)
    root, admitted = _current_selection(project_root=project_root, artifact_writer=artifact_writer, execution=execution)
    service = ExperimentProgrammeService(root, artifact_writer)
    original_owner, original_plan = _predecessor(service, specification)
    if ((execution.workers, execution.environment_id) != (original_plan.workers, original_plan.environment_id)
            or execution.source_snapshot == original_plan.source_snapshot):
        raise PermissionError('curve amendment preserves workers/environment and requires its newly frozen source')
    directory = artifact_writer.root.resolve(specification.directory, for_write=True)
    if (Path(metadata_directory) != directory / 'amendment-inputs'
            or Path(output_selection_path) != Path(metadata_directory) / 'inputs/sources.json'):
        raise ValueError('curve amendment requires <new-home>/amendment-inputs and its inputs/sources.json selector')
    budget = original_plan.specification.operations.metadata_budget
    provenance = capture_matrix_provenance(project_root=root, _admitted_source=admitted)
    snapshots = evidence_snapshots(specification)
    publications, output_bytes = [], 0

    def admit_output(raw):
        nonlocal output_bytes
        _require_memory(budget.memory_bytes)
        if budget.wall_time_seconds is not None and monotonic() - started > budget.wall_time_seconds:
            raise ValueError('curve amendment exceeds its original finite metadata wall budget')
        output_bytes += len(raw)
        if output_bytes > budget.output_bytes or len(raw) > budget.memory_bytes:
            raise ValueError('curve amendment exceeds its original finite metadata budget')
        _metadata_record_size(artifact_writer, len(raw))
        if read_bounded_bytes(Path(source_selection_path), maximum_bytes=len(source_bytes)) != source_bytes:
            raise PermissionError('curve amendment changes its copied selector during derivation')
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

    with original_owner._read_context(original_plan) as original, _original_custody(original_owner, original) as retained:
        original = retained.context
        bindings = tuple((phase, original.binding(phase).identity) for phase in domain.RETAINED_PHASES)
        exposure = domain.amendment_exposure(original.inputs, original.bindings)
        validate_evidence(specification, snapshots, exposure, original.inputs.producing_provenance)
        with withdrawn_custody(service, specification, original_plan, bindings, retained) as (withdrawn, require_withdrawn):
            evidence = publish_evidence(artifact_writer, specification, snapshots, metadata_directory,
                admit_output=admit_output)
            publications.extend(value.publication for value in evidence)
            commitment = _publish_inputs(original.inputs, provenance, publish,
                record_id='commitments.curve-amendment.' + specification.fingerprint())
            target = MatrixCurveAmendedProgrammeSpecification('specification.curve-amendment.' + specification.fingerprint(),
                specification.directory, commitment, original_plan.specification.operations,
                specification.predecessor, specification.identity)
            preparation = prepare_experiment(target, execution=execution)
            record = domain.MatrixProgrammeCurveAmendment('curve-amendment.' + specification.fingerprint(), specification,
                preparation.programme, exposure, bindings, retained.terminals, retained.training_packet, tuple(evidence), withdrawn)
            with authenticated_programme_inputs(writer=artifact_writer, commitment=commitment,
                    maximum_source_bytes=budget.source_scan_bytes) as current:
                domain.validate_amended_inputs(original.inputs, current)
                retained.require_current()
                require_withdrawn()
                if evidence_snapshots(specification) != snapshots:
                    raise PermissionError('exposed amendment evidence changed before publication')
                if capture_matrix_provenance(project_root=root, _admitted_source=admitted) != provenance:
                    raise PermissionError('current source changed before curve-amendment publication')
                amendment_publication = publish_record(directory / domain.AMENDMENT_FILENAME, record)
                selector = ExperimentFileInputSelection('sources.' + target.fingerprint(), AMENDED_PROTOCOL_ID, (), ())
                target_path = Path(metadata_directory) / 'inputs/specification.json'
                target_publication = publish_record(target_path, target)
                source_publication = publish_record(Path(output_selection_path), selector)
                requirements = canonical_json_bytes({'schema': 'empirical-lawhood/operational/experiment-input-requirements',
                    'version': '1.0.0', 'value': {'specification': target.identity, 'prospective_amendment': record.identity,
                        'amendment_rule': specification.rule, 'exposure_census': exposure,
                        'original_programme': original_plan.identity, 'original_input_commitments': original.inputs.commitments.identity,
                        'amended_input_commitments': commitment.record, 'scientific_design': current.scientific_design.identity,
                        'retained_execution_phases': domain.RETAINED_PHASES, 'native_contact': 'NONE',
                        'new_native_contact_count': 0, 'scientific_completion': 'DEFERRED_TO_FULL_READ',
                        'scientific_authority': 'NONE', 'exposed_analysis_standing': snapshots[0].standing}})
                relative = (Path(metadata_directory) / 'requirements.json').relative_to(artifact_writer.root.contract.canonical_path).as_posix()
                admit_output(requirements)
                requirement_publication = artifact_writer.write(ArtifactWriteRequest('requirements.' + record.fingerprint(),
                    relative, 'empirical-lawhood/operational/experiment-input-requirements', ArtifactProfile.CANONICAL_JSON,
                    'application/json', record.record_id, Path(relative).parent.as_posix(), requirements,
                    VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND))
                require_admitted_target_source_current(root, admitted)
            require_withdrawn()
        retained.require_current()
    return ExperimentInputDerivationResult(specification.identity, selector, Path(output_selection_path), preparation,
        (*publications, amendment_publication, target_publication, source_publication, requirement_publication), requirement_publication,
        target, target_path)
