# SPDX-License-Identifier: MPL-2.0
"""Derive native TRAIN inputs from authenticated original programme inputs C.

This operation allocates no groups or streams and observes no new availability.
It produces metadata, without native work or scientific authority.
"""
from dataclasses import replace
from hashlib import sha256
from pathlib import Path

from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_acquisition as acquisition
from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_records as native
from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_assembly import validate_request
from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_publications import validate_request_programme_inputs
from empirical_lawhood.adapters.methods.matrix_factor_response.protected_source_records import ProtectedE3NativeSourceManifest
from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as scheduled
from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import exposure_support
from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex
from empirical_lawhood.api.matrix_numerical_provenance import capture_matrix_provenance
from empirical_lawhood.api.selected_e4_bank_recipe import _current_selection, _metadata_record_size, _publication_from_manifest
from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.infrastructure.matrix_programme_inputs import authenticate_programme_inputs
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputBinding, ExperimentFileInputSelection, ExperimentInputBinding
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest


_FUTURE_ROLES = (("CALIBRATION", "e3.calibration"), ("EVALUATION", "e3.confirmation"),
    ("TRANSFER_NEARBY", "e6.nearby"), ("TRANSFER_SHIFTED", "e6.shifted"))


def assemble_native_training_inputs(*, assembly_specification, request, request_path, project_root, artifact_writer,
        metadata_directory, output_selection_path, execution):
    validate_request(assembly_specification, request)
    root, implementation = _current_selection(project_root=project_root, artifact_writer=artifact_writer, execution=execution)
    destination = Path(metadata_directory)
    plane = Path(artifact_writer.root.contract.canonical_path)
    if (not destination.is_absolute() or destination != destination.resolve(strict=False)
            or destination == plane or not destination.is_relative_to(plane) or destination.is_relative_to(root)
            or Path(output_selection_path) != destination / 'inputs/sources.json'):
        raise ValueError('native assembly requires its exact guarded metadata and <metadata>/inputs/sources.json target')
    if execution.workers != request.resources.maximum_parallel_tasks:
        raise ValueError('native assembly changes the selected native worker resources')
    budget = request.resources.for_operation('entry')
    for field in ('memory_bytes', 'source_scan_bytes', 'output_bytes'):
        if type(getattr(budget, field)) is not int or getattr(budget, field) < 1:
            raise ValueError('native metadata assembly requires a finite positive entry ' + field)
    prefix = destination.relative_to(plane).as_posix()
    artifact_writer.root.resolve(prefix + '/inputs/sources.json', for_write=True)
    # The copied request path has already been bounded/authenticated by the
    # ordinary input loader. Original input bodies come only from C's custody.
    if request_path is None:
        raise ValueError('native assembly requires its actual copied request path')
    with artifact_writer.verification_scope() as writer:
        resolved = authenticate_programme_inputs(writer=writer, commitment=assembly_specification.input_commitments,
            maximum_source_bytes=budget.source_scan_bytes)
        design = resolved.scientific_design
        if assembly_specification.candidate != design.e3.identity:
            raise ValueError('native assembly changes the actual original candidate pinned by C')
        provenance = capture_matrix_provenance(project_root=root)
        if (provenance != resolved.producing_provenance
                or provenance.observed_git_head != implementation.implementation_commit):
            raise ValueError('native assembly changes C\'s actual selected numerical/source provenance')
        return _assemble_current_inputs(assembly_specification=assembly_specification, assembly_request=request,
            resolved=resolved, writer=writer, destination=destination, prefix=prefix, project_root=root, budget=budget)


def _assemble_current_inputs(*, assembly_specification, assembly_request, resolved, writer, destination, prefix,
        project_root, budget):
    namespace = assembly_specification.namespace
    original, design = resolved.commitments, resolved.scientific_design
    scalar = design.training_protocol.scalar_definition
    scalar_pin = ObjectIdentity.from_record(scalar.definition_id, scalar)
    scalar_publication, = (value.publication for value in original.scalar_definitions if value.record == scalar_pin)
    manifests = {}
    for name, role in (('train', 'train'), ('future', 'e3.calibration')):
        phase = resolved.phase(role)
        manifests[name] = ProtectedE3NativeSourceManifest('manifest.' + namespace + '.' + name,
            phase.reservation, phase.native_specification, (resolved.producing_provenance,), resolved.exposure_audit,
            original.exposure_audit.publication, original.phase(role).reservation.publication, scalar, scalar_publication)
    training, future = manifests['train'], manifests['future']
    train_responses = resolved.phase('train').responses
    index = ScheduledSourceIndex.from_shared(reservation=training.reservation,
        specification=training.native_specification, provenances=training.provenances)
    sources = tuple(index.reference(source_id='source.' + row.root.root_id, root_id=row.root.root_id,
        provenance=resolved.producing_provenance.identity) for row in training.reservation.allocation.roots)
    specification = native.NativeTrainingAcquisitionSpecification('experiment.' + namespace + '.native-train',
        design.e3.measurement, tuple(value.root_id for value in sources), scheduled.identity(future.reservation), design.e3.identity)
    original_publications = (assembly_specification.input_commitments, original.availability, original.e6_policy,
        *(original.phase(role).responses for _, role in _FUTURE_ROLES))
    evidence = tuple(sorted((value.record for value in original_publications), key=lambda value: value.object_id))
    support = list(exposure_support(resolved.exposure_audit))
    for value in original_publications:
        publication = value.publication
        support.append((ArtifactIdentity(publication.logical.logical_artifact_id, 'pretrain-programme-input',
            value.record.object_schema, value.record.object_fingerprint, 'application/json',
            publication.materialization.size_bytes), publication))
    support = tuple(sorted(support, key=lambda row: row[0].artifact_id))
    request_id = 'request.' + namespace + '.native-train'
    campaign = replace(assembly_request.campaign, evidence_state=evidence, objective=acquisition.QUESTION,
        system_ids=(request_id,), world_ids=(acquisition.WORLD,),
        target_claim_ids=('claim.study.' + specification.specification_id,),
        budget=ResourceBudget.aggregate(tuple(assembly_request.resources.for_operation(operation)
            for operation in native.ALL_PHASES for _ in range(1 if operation in ('entry', 'terminal') else len(sources)))))
    request = native.NativeTrainingAcquisitionRequest(request_id, training, future, design.e3, sources,
        train_responses.protocols, tuple(sorted((panel for _, values in train_responses.panels for panel in values),
            key=lambda value: value.panel_id)), design.training_protocol.mathematical_protocol,
        train_responses.template_publications, support, campaign, assembly_request.resources, assembly_specification.input_commitments)
    native.validate_request(specification, request)
    # The whole original C closure was authenticated above. This exact join
    # reuses those operation-local bodies rather than reading that closure again.
    validate_request_programme_inputs(request, resolved)
    if capture_matrix_provenance(project_root=project_root) != resolved.producing_provenance:
        raise ValueError('native assembly actual source changed before first metadata publication')
    members = destination / 'inputs'
    array_artifact = design.training_assay.array_artifact
    template_publication, = (value for value in request.template_publications
        if value.logical.logical_artifact_id == array_artifact.artifact_id)
    template_raw = read_bounded_bytes(writer.root.resolve(template_publication.materialization.relative_path, for_write=False),
        maximum_bytes=array_artifact.size_bytes)
    if (len(template_raw), sha256(template_raw).hexdigest()) != (array_artifact.size_bytes, array_artifact.sha256):
        raise ValueError('native assembly actual original template bytes changed')
    template_file = members / (array_artifact.sha256 + '.npz')
    binding = ExperimentInputBinding('request', request.identity, 'request.json', len(request.canonical_bytes()))
    copied = ExperimentFileInputSelection('sources.' + namespace + '.native-train', acquisition.PROTOCOL_ID,
        (binding,), (ExperimentFileInputBinding(array_artifact.artifact_id, array_artifact, '1.0.0',
            template_file.name, array_artifact.size_bytes),))
    writes = []

    def canonical(path, record):
        writes.append(ArtifactWriteRequest(namespace + '.copied.' + sha256(path.encode()).hexdigest(),
            prefix + '/' + path, record.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', namespace, prefix,
            record.canonical_bytes(), VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND))

    canonical('inputs/native-training-specification.json', specification)
    canonical('inputs/request.json', request)
    canonical('inputs/sources.json', copied)
    canonical('publications/train-unit-allocation.json', native.training_allocation(specification, request))
    canonical('inputs/candidate.json', design.e3)
    canonical('inputs/input-commitments-publication.json', assembly_specification.input_commitments)
    canonical('inputs/future-manifest.json', future)
    canonical('inputs/future-availability.json', resolved.availability)
    canonical('inputs/future-availability-publication.json', original.availability.publication)
    canonical('inputs/e6-transport-policy.json', resolved.e6_policy)
    canonical('inputs/e6-transport-policy-publication.json', original.e6_policy.publication)
    for phase in ('development', 'calibration', 'confirmation'):
        canonical('inputs/e4-design-' + phase + '.json', getattr(design, 'e4_' + phase))
    for role, slot in _FUTURE_ROLES:
        canonical('inputs/future-responses-' + role.lower() + '.json', resolved.phase(slot).responses)
        canonical('inputs/future-responses-' + role.lower() + '-publication.json', original.phase(slot).responses.publication)
    for artifact, publication in support:
        canonical('inputs/support-publication-' + artifact.sha256 + '.json', publication)
    writes.append(ArtifactWriteRequest(array_artifact.artifact_id, template_file.relative_to(writer.root.contract.canonical_path).as_posix(),
        array_artifact.payload_schema, ArtifactProfile.MATRIX_ARRAY_NPZ, array_artifact.media_type, namespace, prefix,
        template_raw, VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND))
    # These two derived wrappers preserve C's actual original reservation and
    # selection handles. They never create replacement source/panel custody.
    for name, manifest in manifests.items():
        canonical('publications/' + name + '.manifest.record.json', manifest)
    manifest_write = next(value for value in writes if value.relative_path == prefix + '/publications/future.manifest.record.json')
    # Its actual publication handle is available only after its ordinary write.
    total = sum(len(value.payload) for value in writes)
    if total > budget.output_bytes or total + len(template_raw) > budget.memory_bytes:
        raise ValueError('native assembly metadata exceeds selected actual output or materialized-byte limits')
    for value in writes:
        _metadata_record_size(writer, len(value.payload))
    publications = []
    for value in writes:
        writer.write(value)
        publications.append(_publication_from_manifest(writer, writer.read_manifest(value.relative_path)))
    training_write = next(value for value in writes if value.relative_path == prefix + '/publications/train-unit-allocation.json')
    handles = (('inputs/future-manifest-publication.json', manifest_write),
        ('inputs/train-unit-allocation-publication.json', training_write))
    final_writes = []
    for path, original_write in handles:
        publication = publications[writes.index(original_write)]
        final_writes.append(ArtifactWriteRequest(namespace + '.copied.' + sha256(path.encode()).hexdigest(), prefix + '/' + path,
            publication.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', namespace, prefix,
            publication.canonical_bytes(), VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND))
    final_bytes = sum(len(value.payload) for value in final_writes)
    if total + final_bytes > budget.output_bytes or total + len(template_raw) + final_bytes > budget.memory_bytes:
        raise ValueError('native assembly metadata exceeds selected output or materialized-byte limits')
    for final in final_writes:
        _metadata_record_size(writer, len(final.payload))
        writer.write(final)
        publications.append(_publication_from_manifest(writer, writer.read_manifest(final.relative_path)))
    if capture_matrix_provenance(project_root=project_root) != resolved.producing_provenance:
        raise ValueError('native assembly actual source changed during metadata publication')
    return specification, request, copied, members / 'native-training-specification.json', tuple(publications)
