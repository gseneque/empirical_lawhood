# SPDX-License-Identifier: MPL-2.0
"""Derive ordinary native E2 inputs from authenticated whole-programme C.

This operation publishes metadata and copies the original template bytes. It
does not allocate streams, decode outcome arrays, acquire native histories,
issue a study or establish scientific qualification or permission.
"""
from dataclasses import replace
from hashlib import sha256
from pathlib import Path

from empirical_lawhood.adapters.methods.matrix_factor_response import native_utility_acquisition as acquisition
from empirical_lawhood.adapters.methods.matrix_factor_response import native_utility_records as utility
from empirical_lawhood.adapters.methods.matrix_researcher_programme import e2_assembly as domain
from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import exposure_support
from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex
from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.infrastructure.matrix_programme_inputs import authenticated_programme_inputs
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.planning.experiment_inputs import (
    ExperimentFileInputBinding, ExperimentFileInputSelection, ExperimentInputBinding,
)
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.experiment_preparation import ExperimentInputDerivationResult


def _current_request(*, request, resolved):
    """Project only actual E2 originals; ordinary E2 owns graph construction."""
    original, design, phase = resolved.commitments, resolved.scientific_design.e2, resolved.phase('e2')
    namespace = original.namespace + '.e2'
    count = len(phase.reservation.allocation.roots)
    resources = utility.NativeUtilityResources('resources.' + namespace,
        tuple((name, request.resources.for_operation(name)) for name in utility.ALL_PHASES),
        request.resources.maximum_parallel_tasks)
    aggregate = ResourceBudget.aggregate(tuple(resources.for_operation(name) for name in utility.ALL_PHASES
        for _ in range(1 if name in ('entry', 'terminal') else count)))
    if not request.campaign.budget.contains(aggregate):
        raise ValueError('programme E2 campaign does not contain every actual selected task budget')
    scalar = design.scalar_definition
    scalar_pin = ObjectIdentity.from_record(scalar.definition_id, scalar)
    scalar_publication, = (value.publication for value in original.scalar_definitions if value.record == scalar_pin)
    manifest = utility.NativeUtilitySourceManifest('manifest.' + namespace, phase.reservation,
        phase.native_specification, (resolved.producing_provenance,), resolved.exposure_audit,
        original.exposure_audit.publication, original.phase('e2').reservation.publication, scalar, scalar_publication)
    index = ScheduledSourceIndex.from_shared(reservation=manifest.reservation,
        specification=manifest.native_specification, provenances=manifest.provenances)
    sources = tuple(sorted((index.reference(source_id=protocol.public_source.source.object_id,
        root_id=protocol.public_source.root.root_id, provenance=resolved.producing_provenance.identity)
        for protocol in phase.responses.protocols), key=lambda value: value.root_id))
    index.require_roster(sources, expected_root_ids=index.root_ids)
    specification = utility.NativeUtilitySpecification('experiment.' + namespace,
        tuple(value.root_id for value in sources), design.mathematical_protocol.identity, design.criterion)
    request_id = 'request.' + namespace
    evidence = {value.object_id: value for value in request.campaign.evidence_state}
    for pin in (resolved.commitments.identity, resolved.scientific_design.identity):
        if evidence.setdefault(pin.object_id, pin) != pin:
            raise ValueError('programme E2 campaign substitutes an original programme input identity')
    campaign = replace(request.campaign, objective=acquisition.QUESTION, system_ids=(request_id,),
        world_ids=(acquisition.WORLD,), target_claim_ids=('claim.study.' + specification.specification_id,),
        evidence_state=tuple(evidence[name] for name in sorted(evidence)))
    target_request = utility.NativeUtilityRequest(request_id, manifest, sources,
        tuple(sorted(phase.responses.protocols, key=lambda value: value.protocol_id)),
        tuple(sorted((panel for _, panels in phase.responses.panels for panel in panels), key=lambda value: value.panel_id)),
        design.mathematical_protocol, phase.responses.template_publications,
        exposure_support(resolved.exposure_audit), campaign, resources)
    utility.validate_request(specification, target_request)
    return specification, target_request


def _original_byte_count(commitment, resolved):
    """Count unique original materializations retained by this operation."""
    originals = [commitment.publication, *(value.publication for value in resolved.commitments.publications())]
    for phase in resolved.phases:
        originals.append(phase.reservation.publication)
        if phase.native_specification is not None:
            originals.append(phase.native_specification.publication)
        if phase.responses is not None:
            originals.extend(phase.responses.template_publications)
    originals.extend(resolved.exposure_audit.prior_corpus)
    originals.extend(value for _, value in resolved.commitments.support_files)
    paths = {}
    for value in originals:
        path = value.materialization.relative_path
        if paths.setdefault(path, value) != value:
            raise ValueError('programme E2 aliases different original materializations')
    return sum(value.materialization.size_bytes for value in paths.values())


def assemble_programme_e2(*, specification, request, project_root, artifact_writer,
        metadata_directory, output_selection_path, execution, read_access=None):
    """Publish existing native-utility inputs while C remains authenticated."""
    from empirical_lawhood.api.experiment_preparation import load_experiment_inputs, prepare_experiment
    from empirical_lawhood.api.matrix_numerical_provenance import capture_matrix_provenance
    from empirical_lawhood.api.selected_e4_bank_recipe import _current_selection, _metadata_record_size
    from empirical_lawhood.infrastructure.source_closure import require_admitted_target_source_current

    domain.validate_request(specification, request)
    root, implementation = _current_selection(project_root=project_root, artifact_writer=artifact_writer, execution=execution)
    destination = Path(metadata_directory)
    plane = Path(artifact_writer.root.contract.canonical_path).resolve(strict=True)
    output = Path(output_selection_path)
    if (not destination.is_absolute() or destination != destination.resolve(strict=False)
            or destination == plane or not destination.is_relative_to(plane) or destination.is_relative_to(root)
            or output != destination / 'inputs/sources.json'):
        raise ValueError('programme E2 requires guarded metadata and its exact <metadata>/inputs/sources.json target')
    if execution.workers != request.resources.maximum_parallel_tasks:
        raise ValueError('programme E2 assembly changes the selected native worker resources')
    budget = request.resources.for_operation('entry')
    for field in ('memory_bytes', 'source_scan_bytes', 'output_bytes'):
        if type(getattr(budget, field)) is not int or getattr(budget, field) < 1:
            raise ValueError('programme E2 metadata requires a finite positive entry ' + field)
    prefix = destination.relative_to(plane).as_posix()
    artifact_writer.root.resolve(prefix + '/inputs/sources.json', for_write=True)
    with authenticated_programme_inputs(writer=artifact_writer, commitment=specification.input_commitments,
            maximum_source_bytes=budget.source_scan_bytes) as resolved:
        provenance = capture_matrix_provenance(project_root=root, _admitted_source=implementation)
        if (provenance != resolved.producing_provenance
                or provenance.observed_git_head != implementation.implementation_commit):
            raise ValueError('programme E2 changes C\'s actual selected numerical/source provenance')
        target, selected = _current_request(request=request, resolved=resolved)
        original_bytes = _original_byte_count(specification.input_commitments, resolved)
        namespace = resolved.commitments.namespace + '.e2'
        artifact = resolved.scientific_design.e2.assay.array_artifact
        template_publication, = (value for value in selected.template_publications
            if value.logical.logical_artifact_id == artifact.artifact_id)
        template_raw = read_bounded_bytes(artifact_writer.root.resolve(
            template_publication.materialization.relative_path, for_write=False), maximum_bytes=artifact.size_bytes)
        if (len(template_raw), sha256(template_raw).hexdigest()) != (artifact.size_bytes, artifact.sha256):
            raise ValueError('programme E2 actual original template bytes changed')
        template_name = artifact.sha256 + '.npz'
        selector = ExperimentFileInputSelection('inputs.' + namespace, acquisition.PROTOCOL_ID,
            (ExperimentInputBinding('request', selected.identity, 'request.json', len(selected.canonical_bytes())),),
            (ExperimentFileInputBinding(artifact.artifact_id, artifact, '1.0.0', template_name, artifact.size_bytes),))
        writes = []

        def canonical(name, record):
            writes.append(ArtifactWriteRequest(namespace + '.copied.' + sha256(name.encode()).hexdigest(),
                prefix + '/inputs/' + name + '.json', record.SCHEMA, ArtifactProfile.CANONICAL_JSON,
                'application/json', namespace, prefix, record.canonical_bytes(),
                VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND))

        canonical('native-utility-specification', target)
        canonical('request', selected)
        canonical('sources', selector)
        writes.append(ArtifactWriteRequest(artifact.artifact_id, prefix + '/inputs/' + template_name,
            artifact.payload_schema, ArtifactProfile.MATRIX_ARRAY_NPZ, artifact.media_type, namespace, prefix,
            template_raw, VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND))
        output_bytes = sum(len(value.payload) for value in writes)
        if output_bytes > budget.output_bytes or original_bytes + output_bytes > budget.memory_bytes:
            raise ValueError('programme E2 original and copied metadata exceed selected materialized-byte limits')
        for value in writes:
            if value.profile is ArtifactProfile.CANONICAL_JSON:
                _metadata_record_size(artifact_writer, len(value.payload))
        require_admitted_target_source_current(root, implementation)
        if capture_matrix_provenance(project_root=root, _admitted_source=implementation) != provenance:
            raise ValueError('programme E2 source changed before first dependent metadata publication')
        publications = [artifact_writer.write(value) for value in writes]
        reopened = load_experiment_inputs(target, output, artifact_writer=artifact_writer, read_access=read_access)
        prepared = prepare_experiment(target, scientific_inputs=reopened.scientific_inputs,
            method_inputs=reopened.method_inputs, execution=execution)
        payload = canonical_json_bytes({'schema': 'empirical-lawhood/operational/experiment-input-requirements',
            'version': '1.0.0', 'value': {'specification': specification.identity, 'target_specification': target.identity,
                'input_commitments': specification.input_commitments.record, 'scientific_design': resolved.scientific_design.identity,
                'root_count': len(target.root_ids), 'source_selection': selector, 'native_contact': 'NONE',
                'scientific_authority': 'NONE', 'qualification': 'NOT_ESTABLISHED',
                'original_materialized_bytes': original_bytes, 'copied_input_bytes': output_bytes,
                'dependencies': tuple((value.code, value.kind.value, value.detail) for value in prepared.dependencies)}})
        if (output_bytes + len(payload) > budget.output_bytes
                or original_bytes + output_bytes + len(payload) > budget.memory_bytes):
            raise ValueError('programme E2 requirements exceed selected materialized-byte limits')
        _metadata_record_size(artifact_writer, len(payload))
        requirements = artifact_writer.write(ArtifactWriteRequest('requirements.' + namespace,
            prefix + '/requirements.json', 'empirical-lawhood/operational/experiment-input-requirements',
            ArtifactProfile.CANONICAL_JSON, 'application/json', namespace, prefix, payload,
            VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND))
        publications.append(requirements)
        require_admitted_target_source_current(root, implementation)
        if capture_matrix_provenance(project_root=root, _admitted_source=implementation) != provenance:
            raise ValueError('programme E2 source changed during dependent metadata publication')
        return ExperimentInputDerivationResult(specification.identity, selector, output, prepared,
            tuple(publications), requirements, target, destination / 'inputs/native-utility-specification.json')


def derive_inputs(*, specification, source_selection_path, project_root, artifact_writer,
        metadata_directory, output_selection_path, execution, read_access=None):
    """Ordinary public derive hook; native execution remains with E2."""
    from empirical_lawhood.api.experiment_preparation import load_experiment_inputs
    request = load_experiment_inputs(specification, source_selection_path, artifact_writer=artifact_writer, read_access=read_access).method_inputs
    if request is None:
        raise ValueError('programme E2 derivation requires its exact C-only assembly request')
    return assemble_programme_e2(specification=specification, request=request, project_root=project_root,
        artifact_writer=artifact_writer, metadata_directory=metadata_directory,
        output_selection_path=output_selection_path, execution=execution, read_access=read_access)
