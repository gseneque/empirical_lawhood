# SPDX-License-Identifier: MPL-2.0
"""Derive the full continued E3 graph from authenticated original custody."""
from dataclasses import fields, replace
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from time import monotonic

from empirical_lawhood.adapters.methods.matrix_factor_response import configured_protected_preparation as preparation_owner
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_composition import operation_declarations
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_lowering import lower_protected_matrix_response_error
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_retained_bindings import retained_input_id
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_retained_preparation import ConfiguredE3ContinuedPreparationSelection, ConfiguredE3UnfinishedPreparationSelection, ConfiguredE3ClosedPreparationSelection
from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_NPZ_CODEC
from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.infrastructure.matrix_array_io import NPZMemberSelection, decode_matrix_arrays
from empirical_lawhood.infrastructure.provider_input_custody import provider_input_location
from empirical_lawhood.infrastructure.publication_metadata import authenticate_published_materialization
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputBinding, ExperimentFileInputSelection, ExperimentInputBinding
from empirical_lawhood.planning.formal_gaps import FormalGapEvidenceWorld
from empirical_lawhood.runtime.artifacts import ArtifactLineageParent, ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave

from .derived_array_access import derive_matrix_array_access
from .derived_metadata_access import _semantic_access, derive_canonical_metadata_access


def _original_input(*, original, retained_files, external, original_run_id):
    """Read each retained product under its actual producer's semantic registry."""
    producer, owner = None, original
    original.require_access()
    kept = retained_files.get(external.logical_artifact_id)
    if kept is not None:
        producer, logical, physical = kept
        owner = original.product_source(producer)
        owner.require_access()
        receipt = owner.receipts[producer]
        if (logical not in receipt.output_logical_artifacts
                or physical not in receipt.output_materializations):
            raise PermissionError('retained E3 input changes its actual producing receipt')
        manifest = owner.writer.read_manifest(physical.relative_path)
        if (manifest.logical, manifest.materialization) != (logical, physical):
            raise PermissionError('retained E3 input changes its original completed output')
    else:
        relative, _, _ = provider_input_location(owner.writer, original_run_id, external.logical_artifact_id)
        manifest = owner.writer.read_manifest(relative)
        logical, physical = manifest.logical, manifest.materialization
    owner.writer.verify_manifest(manifest)
    if ((logical.content_sha256, physical.physical_sha256, physical.size_bytes, logical.payload_schema,
            logical.media_type, logical.outcome_access, logical.visibility_ceiling) !=
            (external.expected_content_sha256, external.expected_content_sha256, external.maximum_size_bytes,
                external.payload_schema, external.media_type, external.outcome_access, external.visibility_ceiling)):
        raise PermissionError('retained E3 copies require exact original bytes, size, schema and access')
    raw = read_bounded_bytes(owner.writer.root.resolve(physical.relative_path, for_write=False),
        maximum_bytes=physical.size_bytes)
    if len(raw) != physical.size_bytes or sha256(raw).hexdigest() != physical.physical_sha256:
        raise PermissionError('retained E3 original input changed before its copy')
    owner.require_access()
    original.require_access()
    return producer, owner, manifest, raw


def _retained_array_access(*, original, producer, writer, publication, external, root, observation_operator):
    """Validate the original complete array contract under its explicit copy alias."""
    original.require_access()
    arrays = original.array_descriptors[producer]
    artifact = arrays.array_artifact
    logical, physical = publication.logical, publication.materialization
    receipt = original.receipts[producer]
    source, = (row for row in receipt.output_logical_artifacts if row.profile is MATRIX_NPZ_CODEC.profile)
    imported = hasattr(original.selection, 'retention')
    if (external.logical_artifact_id != (source.logical_artifact_id if imported else retained_input_id(source))
            or (logical.logical_artifact_id, logical.profile, logical.payload_schema, logical.media_type,
                logical.content_sha256, physical.physical_sha256, physical.size_bytes, logical.outcome_access, logical.visibility_ceiling) !=
                (external.logical_artifact_id, MATRIX_NPZ_CODEC.profile, artifact.payload_schema, artifact.media_type,
                    artifact.sha256, artifact.sha256, artifact.size_bytes, external.outcome_access, external.visibility_ceiling)
            or (source.outcome_access, source.visibility_ceiling) != (external.outcome_access, external.visibility_ceiling)):
        raise PermissionError('retained E3 array access substitutes its actual original archive or disclosure scope')
    arrays.__post_init__()
    authenticate_published_materialization(writer, publication)
    raw = read_bounded_bytes(writer.root.resolve(physical.relative_path, for_write=False), maximum_bytes=artifact.size_bytes)
    request = ArtifactWriteRequest(external.logical_artifact_id, physical.relative_path, external.payload_schema,
        MATRIX_NPZ_CODEC.profile, external.media_type, 'retained-e3.array-access', Path(physical.relative_path).parent.as_posix(),
        raw, external.visibility_ceiling, (), external.outcome_access)
    MATRIX_NPZ_CODEC.validate_stream(BytesIO(raw), request, size=len(raw))
    decode_matrix_arrays(raw, NPZMemberSelection(artifact, arrays.members))
    original.require_access()
    return _semantic_access(external=external, root=root, observation_operator=observation_operator,
        version=MATRIX_NPZ_CODEC.record_version)


def project_retained_e3(context):
    """Use ordinary source access, candidate preparation and public authoring."""
    from empirical_lawhood.adapters.composition.experiment_authoring import formal_entry
    from empirical_lawhood.api.matrix_programme_allocations import _require_memory
    from empirical_lawhood.api.recursive_operations import operation_catalog
    from empirical_lawhood.planning.experiment_entry import validate_experiment_entry
    from empirical_lawhood.infrastructure.source_closure import require_admitted_target_source_current
    from .selected_e4_bank_recipe import _current_selection
    from .matrix_numerical_provenance import capture_matrix_provenance
    if len(context.retained_e3) != 1:
        raise PermissionError('retained E3 requires its one active original programme continuation')
    continuation, original, tasks = context.retained_e3[0]
    retention = continuation.retained_e3
    if continuation.target_plan != context.plan:
        raise PermissionError('retained E3 changes its target programme during projection')
    original.require_current()
    project, admitted = _current_selection(project_root=context.service.project_root,
        artifact_writer=context.writer, execution=context.execution)
    if capture_matrix_provenance(project_root=project, _admitted_source=admitted) != retention.response_provenance:
        raise PermissionError('retained E3 input projection changes its selected future response source')
    old = original.selection
    unfinished = getattr(continuation, 'unfinished', None)
    closeout = getattr(continuation, 'closeout', None)
    boundary = closeout if closeout is not None else unfinished
    selection_type = ConfiguredE3ContinuedPreparationSelection if unfinished is None else ConfiguredE3UnfinishedPreparationSelection
    if closeout is not None:
        selection_type = ConfiguredE3ClosedPreparationSelection
    selection = selection_type(**{
        field.name: getattr(old, field.name) for field in fields(old)
        if field.name not in ('selection_id', 'qualifications', 'source_configs', 'resource_selection', 'retention', 'retained_tasks', 'unfinished', 'closeout')},
        selection_id='selection.retained-e3.' + retention.fingerprint(),
        qualifications=(), source_configs=(), resource_selection=context.plan.specification.operations.e3.resources,
        retention=retention, retained_tasks=tasks,
        **({'closeout': closeout} if closeout is not None else {} if unfinished is None else {'unfinished': unfinished}))
    specification, allocation = original.specification, original.allocation
    lowered = lower_protected_matrix_response_error(specification, allocation, selection)
    declarations = {row.capability_key: row for row in operation_declarations()}
    codecs = {schema: kind for declaration in declarations.values() for schema, kind in declaration.record_codecs.items()}
    records, files = dict(lowered.input_records), dict(lowered.file_identities)
    retained_files = {}
    for config in tasks:
        physicals = {row.logical_artifact_id: row for row in config.original_receipt.output_materializations}
        for logical in config.original_receipt.output_logical_artifacts:
            retained_files[retained_input_id(logical)] = (config.original_task.task_id, logical, physicals[logical.logical_artifact_id])
    if boundary is not None:
        retained_files.update((row.logical.logical_artifact_id, (row.task_id, row.logical, row.materialization))
            for row in boundary.imported_outputs)
    missing_products = ({} if closeout is None else {row.record_id: row
        for row in original.missing_products(retention.response_provenance).values()})
    templates = {protocol.templates.array_artifact.artifact_id: protocol.templates for protocol in selection.protocols}
    writer = context.writer
    destination = context.metadata_directory('e3') / 'continued-inputs'
    relative_root = destination.relative_to(writer.root.contract.canonical_path).as_posix()
    started, written = monotonic(), 0
    budget = context.plan.specification.operations.metadata_budget
    publications, bindings, source_configs, qualifications, versions = [], [], [], [], {}
    operator = ObjectIdentity.from_record(specification.specification_id + '.measurement', specification.measurement)

    def write(path, raw, *, logical, schema, profile, media, access, visibility, parent=None):
        nonlocal written
        original.require_access()
        _require_memory(budget.memory_bytes)
        written += len(raw)
        if (len(raw) > budget.memory_bytes or written > budget.output_bytes
                or budget.wall_time_seconds is not None and monotonic() - started > budget.wall_time_seconds):
            raise ValueError('retained E3 input copies exceed their selected metadata budget')
        relative = path.relative_to(writer.root.contract.canonical_path).as_posix()
        lineage = (() if parent is None else (ArtifactLineageParent(ObjectIdentity.from_record(parent.logical_artifact_id, parent),
            parent.visibility_ceiling, parent.outcome_access),))
        publication = writer.write(ArtifactWriteRequest(logical, relative, schema, profile, media,
            'retained-e3.inputs.' + retention.fingerprint(), relative_root, raw,
            visibility, tuple(row.visibility_ceiling for row in lineage), access, lineage_parents=lineage))
        publications.append(publication)
        return publication

    for external in lowered.draft.external_inputs:
        producer, product_owner = None, original
        if external.logical_artifact_id in missing_products:
            record = missing_products[external.logical_artifact_id]
            raw, version, profile, parent = record.canonical_bytes(), record.VERSION, ArtifactProfile.CANONICAL_JSON, None
            if (len(raw), record.fingerprint()) != (external.maximum_size_bytes, external.expected_content_sha256):
                raise PermissionError('CAL closeout changes its authenticated missing-outcome assessment')
        elif external.input_id in records:
            record = records[external.input_id]
            raw, version, profile, parent = record.canonical_bytes(), record.VERSION, ArtifactProfile.CANONICAL_JSON, None
        else:
            producer, product_owner, manifest, raw = _original_input(original=original,
                retained_files=retained_files, external=external, original_run_id=retention.original_run_id)
            logical = manifest.logical
            profile, parent = logical.profile, logical
            if profile is ArtifactProfile.CANONICAL_JSON:
                kind = codecs[external.payload_schema]
                record = decode_canonical_bytes(raw, kind, maximum_bytes=len(raw))
                if record.canonical_bytes() != raw:
                    raise PermissionError('retained E3 canonical input changes its original bytes')
                version = record.VERSION
            else:
                record, version = None, MATRIX_NPZ_CODEC.record_version
        filename = sha256(external.logical_artifact_id.encode()).hexdigest() + ('.npz' if profile is ArtifactProfile.MATRIX_ARRAY_NPZ else '.json')
        publication = write(destination / filename, raw, logical=external.logical_artifact_id,
            schema=external.payload_schema, profile=profile, media=external.media_type,
            access=external.outcome_access, visibility=external.visibility_ceiling, parent=parent)
        if profile is ArtifactProfile.CANONICAL_JSON:
            config, qualification = derive_canonical_metadata_access(writer=writer, publication=publication,
                record=record, external=external, root=lowered.draft.prospective_draft, observation_operator=operator)
        elif producer is not None:
            config, qualification = _retained_array_access(original=product_owner, producer=producer, writer=writer,
                publication=publication, external=external, root=lowered.draft.prospective_draft, observation_operator=operator)
        else:
            config, qualification = derive_matrix_array_access(writer=writer, publication=publication,
                arrays=templates[external.logical_artifact_id], external=external,
                root=lowered.draft.prospective_draft, observation_operator=operator)
        versions[external.logical_artifact_id] = version
        source_configs.append(config)
        qualifications.append(qualification)
        if external.input_id in files:
            artifact = files[external.input_id]
            bindings.append(ExperimentFileInputBinding(artifact.artifact_id, artifact, version, filename, len(raw)))
    selection = replace(selection, source_configs=tuple(source_configs),
        qualifications=tuple(sorted(qualifications, key=lambda row: row.receipt_id)))
    draft = preparation_owner._source_projection(lowered.draft, selection, versions)
    registrations, registry, output_codecs = operation_catalog()
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_retained_execution import source_binding
    implementation = source_binding(retention.response_provenance)
    compiled = compile_recursive_wave(draft=draft, registrations=registrations, registry=registry,
        implementation_commit=implementation.observed_git_head, qualifications=selection.qualifications,
        known_design_inputs=draft.prospective_draft.design_inputs, output_codecs=output_codecs,
        implementation_sha256=implementation.fingerprint())
    if compiled.candidate_context is None or compiled.candidate_draft is None or compiled.candidate_report.candidate is None:
        raise ValueError('retained E3 candidate graph is invalid: ' + str(compiled.candidate_report))
    authoring, standard = formal_entry(compiled.candidate_draft, compiled.candidate_context, specification.identity,
        prefix=context.namespace + '.e3', minimum_units=specification.population('EVALUATION').expected_units,
        operand_description='Selected paired native response-error {domain} on the complete independently seeded physical-root roster',
        estimator='whole-root-exact-comparison', uncertainty='family-exact-uncertainty', ceiling=EvidenceCeiling.RESPONSE,
        evaluator=registry.resolve('matrix-e3-configured-protected.assess', '1.0.0'), input_schema=specification.SCHEMA,
        output_schema='empirical-lawhood/matrix-response-experiment/configured-protected-assessment',
        world=FormalGapEvidenceWorld.NUMERICAL_SIMULATOR, minimum_views=len(selection.root.system.numerical_views),
        evidence_unit_ids=allocation.unit_ids('evaluation'))
    selection = replace(selection, root=authoring.draft, entry_package=authoring.entry_package,
        formal_methods=standard.formal_methods, formal_source_inventories=standard.source_inventories)
    final = lower_protected_matrix_response_error(specification, allocation, selection)
    final_draft = preparation_owner._source_projection(final.draft, selection, versions)
    entry = replace(selection.entry_package, checklist=replace(selection.entry_package.checklist,
        draft=ObjectIdentity.from_record(final_draft.prospective_draft.draft_id, final_draft.prospective_draft)))
    validate_experiment_entry(final_draft.prospective_draft, entry, for_issue=False)
    selection = replace(selection, entry_package=entry)
    from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
    for filename, record, identity in (('specification.json', specification, specification.identity),
            ('protected-selection.json', selection, ObjectIdentity.from_record(selection.selection_id, selection))):
        write(destination / filename, record.canonical_bytes(), logical=identity.object_id, schema=record.SCHEMA,
            profile=ArtifactProfile.CANONICAL_JSON, media='application/json', access=OutcomeAccess.OUTCOME_BLIND,
            visibility=VisibilityCeiling.PROSPECTIVE)
    selector = ExperimentFileInputSelection('sources.retained-e3.' + retention.fingerprint(),
        'matrix.response-error.configured-protected-v2',
        (ExperimentInputBinding('protected-selection', ObjectIdentity.from_record(selection.selection_id, selection),
            'protected-selection.json', len(selection.canonical_bytes())),), tuple(sorted(bindings, key=lambda row: row.key)))
    write(destination / 'sources.json', selector.canonical_bytes(), logical=selector.selection_id, schema=selector.SCHEMA,
        profile=ArtifactProfile.CANONICAL_JSON, media='application/json', access=OutcomeAccess.OUTCOME_BLIND,
        visibility=VisibilityCeiling.PROSPECTIVE)
    original.require_current()
    require_admitted_target_source_current(project, admitted)
    return context.result('e3', specification, selector, destination / 'specification.json', destination / 'sources.json',
        tuple(publications), require_current=original.require_access)
