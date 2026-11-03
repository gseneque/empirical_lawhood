# SPDX-License-Identifier: MPL-2.0
"""Public selected preparation derivation; original custody stays parent-only."""
from dataclasses import replace
from functools import partial
from pathlib import Path

from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_declarative_preparation as domain
from empirical_lawhood.infrastructure.source_origin import require_selected_implementation
from empirical_lawhood.infrastructure.source_closure import (
    capture_admitted_target_source, require_admitted_target_source_current,
)
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess
from empirical_lawhood.kernel.serialization import canonical_json_document_bytes
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest


def selected_produced_input_parents(writer, *, originals, development=(),read_access=None):
    """Authenticate only exact original custody metadata; never grant access."""
    from empirical_lawhood.api.selected_prepared_access import original_input_parents
    originals=tuple(sorted(originals,key=lambda value:value.record.object_id))
    development=tuple(sorted(development,key=lambda value:value.record.object_id))
    locators=tuple(('original.'+str(index),value) for index,value in enumerate(originals))+tuple(
        ('development.'+str(index),value) for index,value in enumerate(development))
    return original_input_parents(artifact_writer=writer,locators=locators,read_access=read_access)


def require_produced_input_parents(writer, request, *,read_access=None):
    """Independently join the canonical declaration to genuine current parents."""
    if request.revision is None:
        originals = request.original_e3_products
        if request.original_e3_nomination is not None and (request.original_e3_source is None
                or request.original_e3_source.development_nomination is None):
            raise ValueError('selected CONF requires its genuine original DEV nomination locator')
        development = (() if request.original_e3_nomination is None else
            (request.original_e3_source.development_nomination,))
    else:
        evidence = request.revision_evidence
        if evidence is None:
            raise ValueError('selected revision requires its actual original producer evidence')
        originals = (evidence.downstream_nomination, evidence.calibration)
        development = (evidence.revision_fit, evidence.revision_freeze,
            *((evidence.preparation_nomination,) if evidence.preparation_nomination is not None else ()))
    actual = selected_produced_input_parents(writer, originals=originals, development=development,**({} if read_access is None else {"read_access":read_access}))
    if actual != request.produced_input_parents:
        raise PermissionError('selected request changes its exact actual produced-input access/visibility/lineage census')


def require_evidence_produced_input_parents(writer, parents, evidence, *,read_access=None):
    """Fresh actual producer comparison at ordinary worker/source boundaries."""
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_original_commitments import (
        MatrixRevisionEntryEvidenceV2, MatrixSelectedEntryEvidenceV3, MatrixSelectedOpportunityEvidenceV2)
    if type(evidence) is MatrixRevisionEntryEvidenceV2:
        originals = (evidence.downstream_nomination, evidence.calibration)
        development = (evidence.revision_fit, evidence.revision_freeze,
            *((evidence.preparation_nomination,) if evidence.preparation_nomination is not None else ()))
    elif type(evidence) in (MatrixSelectedEntryEvidenceV3, MatrixSelectedOpportunityEvidenceV2):
        originals = evidence.upstream_products
        development = (() if type(evidence) is MatrixSelectedOpportunityEvidenceV2
            or evidence.development_nomination is None else (evidence.development_nomination,))
    else:
        raise TypeError('current produced-parent census requires its actual committed original evidence')
    if selected_produced_input_parents(writer, originals=originals, development=development,**({} if read_access is None else {"read_access":read_access})) != parents:
        raise PermissionError('selected worker changes the exact actual produced-parent access/visibility census')


def original_e3_package(writer, request, codecs, *,read_access=None):
    """Read four actual issued products under their original current grants."""
    from empirical_lawhood.api.matrix_selected_e3_family import selected_e3_product_family
    from ...matrix_sampling_runtime import _original_products
    from empirical_lawhood.api.matrix_selected_producer_scope import validate_selected_e3_original_product
    from ...matrix_selected_runtime import reconstruct_selected_package
    from ...recursive_qualified_parents import MAX_PARENT_BYTES

    public = request.original_e3
    if public is None: raise ValueError("select the exact original public E3 package")
    family = selected_e3_product_family(public.specification)
    expected = {domain.pin(value) for value in (public.models, public.model_freeze, public.calibrated_freeze)}
    expected.add(public.calibration)
    if (len(expected) != 4 or tuple(value.record.object_id for value in request.original_e3_products)
            != tuple(sorted(value.object_id for value in expected))
            or {value.record for value in request.original_e3_products} != expected):
        raise ValueError("selected E3 derivation needs all four exact actual original producers")
    originals = {domain.pin(value): value for value in (public.models, public.model_freeze, public.calibrated_freeze)}
    calibration = None
    from empirical_lawhood.api.selected_prepared_access import _selected
    selected_originals=_selected(request.original_e3_products,read_access)
    payloads = _original_products(writer, tuple((value, value.record) for value in selected_originals),
        codecs, scope_validator=partial(validate_selected_e3_original_product, frozen=public, assay=request.assay))
    for product, raw in zip(selected_originals, payloads, strict=True):
        if product.record == public.calibration:
            calibration = decode_canonical_bytes(raw, family.calibration_type, maximum_bytes=MAX_PARENT_BYTES)
            if domain.pin(calibration) != public.calibration or raw != calibration.canonical_bytes():
                raise PermissionError("selected E3 derivation changes actual original calibration bytes")
        elif raw != originals[product.record].canonical_bytes():
            raise PermissionError("selected E3 derivation changes actual original frozen product bytes")
    return reconstruct_selected_package(public, calibration)


def derive_authenticated_selection(specification, request, *, writer, project_root,read_access=None,
        _admitted_source=None):
    """Authenticate all selected scientific original operands before publication."""
    from empirical_lawhood.api.recursive_operations import operation_catalog
    from empirical_lawhood.api.matrix_selected_revision_runtime import authenticate_revision_source_custody, revision_original_operands
    from ...matrix_selected_runtime import _authenticate_entry
    from ...matrix_selected_opportunity_runtime import (
        reconstruct_opportunity_programme, authenticate_selected_development_nomination,
    )
    if type(request) not in domain.committed_request_types():
        domain.require_original_commitments(None)
    require_produced_input_parents(writer, request,read_access=read_access)
    sources = domain.derive_sources(specification, request)
    root = Path(project_root).resolve(strict=True)
    require_selected_implementation(root)
    if _admitted_source is None:
        admitted = capture_admitted_target_source(root)
    else:
        admitted = _admitted_source
        require_admitted_target_source_current(root, admitted)
    rows = domain.source_arms(specification, sources)
    if any(value.provenance.observed_git_head != admitted.implementation_commit for _, value in rows):
        raise ValueError("selected preparation needs actual current producing provenance; old source labels cannot be relabelled")
    codecs = operation_catalog()[2]
    if specification.account == "REVISION":
        programme, evidence = domain.make_programme(specification, request)
        used = revision_original_operands(writer, programme, evidence, codecs,current_access=read_access)
        programme, evidence = domain.make_programme(specification, request, excluded_groups=used)
        if programme.excluded_group_ids != used:
            raise PermissionError("selected revision changes its authenticated complete prior group census")
        domain.validate_evidence(programme, evidence)
        authenticate_revision_source_custody(writer, programme, evidence, codecs)
    else:
        package = original_e3_package(writer, request, codecs,read_access=read_access)
        nomination = None
        if specification.phase == "E5_CONFIRMATION":
            from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_entry_v2 import MatrixSelectedEntryEvidenceV2
            original = request.original_e3_source
            if (type(original) not in (MatrixSelectedEntryEvidenceV2, domain.MatrixSelectedEntryEvidenceV3)
                    or original.development_nomination is None or request.original_e3_nomination is None):
                raise ValueError("selected confirmation needs its actual separate DEV nomination and current source custody")
            selected = request.original_e3_nomination
            nomination = authenticate_selected_development_nomination(writer, original.development_nomination,
                package=package, criterion=specification.criterion, nomination_pin=selected.original_nomination,read_access=read_access)
            from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_public import MatrixSelectedNominationSelection
            if MatrixSelectedNominationSelection.from_nomination(nomination[0]) != selected:
                raise PermissionError("selected CONF declaration changes its actual original DEV recipe/criterion")
        programme, evidence = domain.make_programme(specification, request, e3_package=package, nomination=nomination)
        if specification.phase == "E5_OPPORTUNITY":
            domain.validate_evidence(programme, evidence)
            if (evidence.upstream_products != request.original_e3_products
                    or programme.point_design.package != request.original_e3):
                raise PermissionError("opportunity changes the exact already authenticated original producer census")
            reconstructed = reconstruct_opportunity_programme(programme, package.calibration)
            if reconstructed.point_design.package != package:
                raise PermissionError("opportunity changes the exact already authenticated original scientific package")
        else:
            _authenticate_entry(writer, programme, evidence, codecs,
                source_scan_bytes=dict(request.phase_resources.phase_budgets)["entry"].source_scan_bytes,
                transport_policy=getattr(request, "transport_policy", None),current_access=read_access)
    from ...matrix_prepared_original_commitments import authenticate_prepared_original_commitments
    if specification.account == "REVISION" or specification.phase == "E5_OPPORTUNITY":
        authenticate_prepared_original_commitments(writer=writer, programme=programme, evidence=evidence,
            source_scan_bytes=dict(request.phase_resources.phase_budgets)["entry" if specification.account == "REVISION" else "design"].source_scan_bytes,
            **({} if read_access is None else {"current_access":read_access}))
    extra = {}
    kind = domain.SelectedPreparedDerivedSelectionV4
    if type(request) is domain.SelectedPreparedDerivationRequestV3:
        from empirical_lawhood.adapters.methods.matrix_experimental_programme.e6_transport_science import project_e6_frozen_calibration
        if specification.account != "ORIGINAL_E3" or specification.phase != "E6_TRANSFER":
            raise ValueError("the transport policy belongs only to expanded original-E3 E6")
        extra["transport_calibration"] = project_e6_frozen_calibration(request.transport_policy, package,
            record_id="calibration-projection." + request.transport_policy.fingerprint() + "." + package.fingerprint())
        kind = domain.SelectedPreparedDerivedSelectionV5
    selection = kind("selection.selected-declarative." + specification.fingerprint()
        + "." + request.fingerprint(), specification.identity, request, programme, evidence, **extra)
    domain.validate_selection(specification, selection)
    require_admitted_target_source_current(root, admitted)
    return selection


def plan_current_metadata(specification, selection, *, relative, files):
    """Validate every typed input and derive access coordinates before effects."""
    from hashlib import sha256
    from empirical_lawhood.api.derived_metadata_access import _semantic_access
    from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_NPZ_CODEC
    from empirical_lawhood.api.derived_array_access import validate_matrix_array_input_bytes
    from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_produced_inputs import produced_history_parents
    if specification.phase == "E5_OPPORTUNITY":
        return selection, ()
    lowered = domain.lower(specification, selection)
    root = domain.project_root(specification, selection)
    profile = selection.evidence.pipeline.pipeline_config.profile
    records = dict(lowered.input_records)
    arrays = {value.initial.array_artifact: value.initial for _, value in domain.source_arms(specification, selection.programme.sources)}
    arrays[selection.programme.assay.template_artifact] = selection.programme.assay
    request = selection.request
    qualifications, configs, planned = {}, {}, []
    required = {value.input_id for value in lowered.draft.external_inputs
        if not produced_history_parents(value, records.get(value.input_id), request.produced_input_parents)}
    if (len({value.source_id for value in request.qualifications}) != len(request.qualifications)
            or len({value.source_id for value in request.source_configs}) != len(request.source_configs)
            or ({value.source_id for value in request.qualifications} | {value.source_id for value in request.source_configs}) - required):
        raise ValueError("selected existing access includes undeclared foreign source IDs")
    for external in lowered.draft.external_inputs:
        record = records.get(external.input_id)
        if record is None:
            artifact = dict(lowered.input_artifacts)[external.input_id]
            original, handle = arrays.get(artifact), files.get(artifact)
            if original is None or handle is None or handle.identity != artifact:
                raise ValueError("selected array access lacks actual original typed source/template and bytes")
            raw = read_bounded_bytes(handle.path, maximum_bytes=artifact.size_bytes)
            validate_matrix_array_input_bytes(raw=raw, arrays=original, external=external)
            suffix = sha256((external.logical_artifact_id + artifact.sha256).encode()).hexdigest()
            relative_path, profile_kind = relative + "/arrays/" + suffix + ".npz", ArtifactProfile.MATRIX_ARRAY_NPZ
        else:
            if (record.SCHEMA, record.fingerprint(), len(record.canonical_bytes())) != (
                    external.payload_schema, external.expected_content_sha256, external.maximum_size_bytes):
                raise PermissionError("typed derivation changes its exact generated canonical input")
            raw, original = record.canonical_bytes(), record
            relative_path, profile_kind = relative + "/metadata/" + external.expected_content_sha256 + ".json", ArtifactProfile.CANONICAL_JSON
        parents = produced_history_parents(external, record, selection.request.produced_input_parents)
        publication_request = ArtifactWriteRequest(external.logical_artifact_id, relative_path,
            external.payload_schema, profile_kind, external.media_type, "selected-input." + external.expected_content_sha256,
            str(Path(relative_path).parent), raw, external.visibility_ceiling,
            tuple(value.visibility_ceiling for value in parents), external.outcome_access, lineage_parents=parents)
        publication_request.__post_init__()
        if not parents:
            config, qualification = _semantic_access(external=external, root=root, source_profile=profile,
                version=MATRIX_NPZ_CODEC.record_version if record is None else record.VERSION)
            configs[external.input_id], qualifications[external.input_id] = config, qualification
        planned.append((external, original, publication_request))
    selected = replace(request, source_configs=tuple(sorted(configs.values(), key=lambda value: value.fingerprint())),
        qualifications=tuple(sorted(qualifications.values(), key=lambda value: value.receipt_id)))
    result = replace(selection, request=selected,
        record_id="selection.selected-declarative." + specification.fingerprint() + "." + selected.fingerprint())
    domain.validate_selection(specification, result)
    return result, tuple(planned)


def _authenticate_produced_history_publication(*, writer, publication, record, external, parents,
        root, source_profile, require_current=None):
    """Authenticate retained exact bytes and ancestry without source qualification."""
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_produced_inputs import produced_history_parents
    from empirical_lawhood.api.derived_metadata_access import (
        _require_canonical_metadata_binding, _read_canonical_metadata_binding,
    )
    from empirical_lawhood.infrastructure.publication_metadata import authenticate_published_materialization
    selected = produced_history_parents(external, record, parents)
    if not selected:
        raise ValueError("retained publication lacks its exact produced HISTORY ancestry")
    _require_canonical_metadata_binding(publication=publication, record=record, external=external,
        root=root, source_profile=source_profile)
    if publication.logical.lineage_parents != selected:
        raise PermissionError("retained HISTORY publication changes its exact produced-parent census")
    if require_current is not None:
        require_current()
    authenticate_published_materialization(writer, publication)
    if require_current is not None:
        require_current()
    _read_canonical_metadata_binding(writer=writer, publication=publication, record=record, external=external)
    if require_current is not None:
        require_current()


def publish_current_metadata(specification, selection, *, writer, planned, require_current=None):
    """Actual verified publication must establish every planned ACCESS record."""
    from empirical_lawhood.api.derived_metadata_access import derive_canonical_metadata_access
    from empirical_lawhood.api.derived_array_access import derive_matrix_array_access
    root = None if specification.phase == "E5_OPPORTUNITY" else domain.project_root(specification, selection)
    profile = None if root is None else selection.evidence.pipeline.pipeline_config.profile
    expected_configs = {value.source_id: value for value in selection.request.source_configs}
    expected_qualifications = {value.source_id: value for value in selection.request.qualifications}
    from empirical_lawhood.api.derived_array_access import (
        DerivedInputAccess, derive_matrix_input_access_batch, supports_derived_input_access_batch,
    )
    from empirical_lawhood.infrastructure.publication_metadata import checkpoint_publication_access
    publications = []
    batch_access = supports_derived_input_access_batch(writer, len(planned))
    pending = []
    if batch_access and planned:
        checkpoint_publication_access(writer)
    for external, original, request in planned:
        if require_current is not None:
            require_current()
        publication = writer.write(request)
        if external.scientific_role == "HISTORY":
            _authenticate_produced_history_publication(writer=writer, publication=publication, record=original,
                external=external, parents=selection.request.produced_input_parents,
                root=root, source_profile=profile, require_current=require_current)
            publications.append(publication)
            continue
        if batch_access:
            pending.append(DerivedInputAccess(publication, original, external))
            publications.append(publication)
            continue
        if request.profile is ArtifactProfile.MATRIX_ARRAY_NPZ:
            config, qualification = derive_matrix_array_access(writer=writer, publication=publication,
                arrays=original, external=external, root=root, source_profile=profile)
        else:
            config, qualification = derive_canonical_metadata_access(writer=writer, publication=publication,
                record=original, external=external, root=root, source_profile=profile)
        if (config, qualification) != (expected_configs[external.input_id], expected_qualifications[external.input_id]):
            raise PermissionError("actual typed publication changes its planned exact ordinary access")
        publications.append(publication)
    if pending:
        observed = derive_matrix_input_access_batch(writer=writer, inputs=tuple(pending), root=root, source_profile=profile)
        for item, (config, qualification) in zip(pending, observed, strict=True):
            if (config, qualification) != (expected_configs[item.external.input_id], expected_qualifications[item.external.input_id]):
                raise PermissionError("actual typed publication changes its planned exact ordinary access")
    return tuple(publications)


def validate_current_metadata(specification, selection):
    """Cold contextual validation; actual issue/publication guards still apply."""
    from empirical_lawhood.api.derived_metadata_access import validate_derived_metadata_access
    from empirical_lawhood.api.derived_array_access import validate_derived_matrix_array_access
    if specification.phase == "E5_OPPORTUNITY": return
    lowered = domain.lower(specification, selection)
    root = domain.project_root(specification, selection)
    profile = selection.evidence.pipeline.pipeline_config.profile
    records = dict(lowered.input_records)
    configs = {value.source_id: value for value in selection.request.source_configs}
    qualifications = {value.source_id: value for value in selection.request.qualifications}
    arrays = {value.initial.array_artifact: value.initial for _, value in domain.source_arms(specification, selection.programme.sources)}
    arrays[selection.programme.assay.template_artifact] = selection.programme.assay
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_produced_inputs import produced_history_parents
    source_ids = {value.input_id for value in lowered.draft.external_inputs if value.scientific_role != "HISTORY"}
    if set(configs) != source_ids or set(qualifications) != source_ids:
        raise PermissionError("selected ordinary access roster differs from exact physical SOURCE inputs")
    for external in lowered.draft.external_inputs:
        record = records.get(external.input_id)
        if produced_history_parents(external, record, selection.request.produced_input_parents):
            continue
        if record is None:
            artifact = dict(lowered.input_artifacts)[external.input_id]
            if external.input_id not in configs or external.input_id not in qualifications:
                raise PermissionError("selected array input lacks current exact ordinary access")
            validate_derived_matrix_array_access(arrays=arrays[artifact], external=external, root=root,
                source_profile=profile, config=configs[external.input_id], qualification=qualifications[external.input_id])
            continue
        if external.input_id not in configs or external.input_id not in qualifications:
            raise PermissionError("selected canonical metadata lacks its current exact access proof")
        validate_derived_metadata_access(external=external, root=root, source_profile=profile,
            version=record.VERSION, config=configs[external.input_id], qualification=qualifications[external.input_id])


def _derive_inputs(*, specification, source_selection_path, project_root, artifact_writer,
        metadata_directory, output_selection_path, execution, read_access=None):
    """The existing generic command publishes new current metadata, no authority."""
    from ...experiment_preparation import _protocol, load_experiment_inputs, prepare_experiment
    from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
    from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputSelection, ExperimentInputBinding
    from empirical_lawhood.runtime.experiment_preparation import ExperimentInputDerivationResult

    source, output, metadata = Path(source_selection_path), Path(output_selection_path), Path(metadata_directory)
    root = Path(project_root).resolve(strict=True)
    require_selected_implementation(root)
    source_before = capture_admitted_target_source(root)
    plane = Path(artifact_writer.root.contract.canonical_path).resolve(strict=True)
    if (not all(value.is_absolute() for value in (source, output, metadata))
            or source.parent != output.parent or source == output
            or any(value.is_symlink() for path in (source, output, metadata) for value in (path, *path.parents))
            or any(path == root or root in path.parents for path in (output, metadata))):
        raise ValueError("select fresh canonical external metadata/selector paths under the selected guarded input root")
    try:
        output_relative = output.relative_to(plane).as_posix()
        metadata_relative = metadata.relative_to(plane).as_posix()
        metadata_under_inputs = metadata.relative_to(source.parent)
    except ValueError as error:
        raise ValueError("derived selector and metadata must remain within the actual selected guarded input root") from error
    if any(path != path.resolve(strict=False) for path in (source, output, metadata)):
        raise ValueError("selected input derivation requires exact canonical paths")
    artifact_writer.root.resolve(output_relative, for_write=True)
    original_raw = read_bounded_bytes(source, maximum_bytes=_protocol(specification).maximum_config_bytes)
    original = decode_canonical_bytes(original_raw,
        ExperimentFileInputSelection, maximum_bytes=_protocol(specification).maximum_config_bytes)
    if original.protocol_id != _protocol(specification).protocol_id or tuple(value.key for value in original.bindings if not value.key.startswith(("original.","development."))) != ("request",):
        raise ValueError("selected derivation requires exactly its explicit request source role")
    inputs = load_experiment_inputs(specification, source, artifact_writer=artifact_writer, read_access=read_access)
    request = inputs.method_inputs.request
    selected_request = request
    def require_current():
        require_produced_input_parents(artifact_writer, selected_request,read_access=read_access)
        artifact_writer.require_verification_snapshot()
    # Typed science, unsupported recipes/source changes and all actual producer/
    # source grants are checked before any metadata write.
    selection = derive_authenticated_selection(specification, request, writer=artifact_writer, project_root=root,
        read_access=read_access, _admitted_source=source_before)
    # Every knowable original-science refusal above precedes new publication.
    lowered = domain.lower(specification, selection)
    by_artifact = {}
    for value in original.files:
        if by_artifact.setdefault(value.identity, value) != value:
            raise ValueError("selected input files alias differing paths/bounds for one artifact")
    files = []
    for key, artifact in lowered.input_artifacts:
        selected = by_artifact.get(artifact)
        if selected is None:
            raise ValueError("selected derivation lacks actual original file bytes: " + key)
        files.append(replace(selected, key=key))
    if set(by_artifact) != {value for _, value in lowered.input_artifacts}:
        raise ValueError("selected file census contains undeclared initial/template bytes")
    selection, planned = plan_current_metadata(specification, selection,
        relative=metadata_relative, files={value.identity: value for _, value in inputs.method_inputs.files})
    lowered = domain.lower(specification, selection)
    digest = selection.fingerprint()
    target = metadata_relative + "/selection." + digest + ".json"
    artifact_writer.root.resolve(target, for_write=True)
    selected_file = (metadata_under_inputs / ("selection." + digest + ".json")).as_posix()
    derived = ExperimentFileInputSelection("sources.selected-declarative." + digest, original.protocol_id,
        tuple(sorted((ExperimentInputBinding("selection", selection.identity, selected_file, len(selection.canonical_bytes())),
            *(value for value in original.bindings if value.key.startswith(("original.","development.")))),key=lambda value:value.key)),
        tuple(sorted(files, key=lambda value: value.key)))
    bound_files = {key: value for key, value in inputs.method_inputs.files}
    by_identity = {value.identity: value for value in bound_files.values()}
    prepared_inputs = domain.bind_inputs(specification, {"selection": selection,**dict(domain.original_locator_records(selected_request))},
        files={key: by_identity[artifact] for key, artifact in lowered.input_artifacts})
    preparation = prepare_experiment(specification, scientific_inputs=prepared_inputs.scientific_inputs,
        method_inputs=prepared_inputs.method_inputs, execution=execution)
    # A selected ordinary source proof cannot be borrowed onto these new config
    # digests. Complete missing rows remain the actual preparation result.
    requirements = canonical_json_document_bytes({"schema": "empirical-lawhood/operational/experiment-input-requirements",
        "version": "1.0.0", "value": {"specification": specification.identity.to_document(),
            "dependencies": [{"code": value.code, "kind": value.kind.value, "detail": value.detail,
                "source_key": value.source_key} for value in preparation.dependencies],
            "scientific_authority": "NONE", "native_contact": "NONE"}})
    def publication_request(identifier, relative, schema, raw, *, produced=False):
        from empirical_lawhood.runtime.artifacts import derived_outcome_access
        from empirical_lawhood.kernel.evidence import inherited_visibility
        parents = selected_request.produced_input_parents if produced else ()
        access = derived_outcome_access(OutcomeAccess.DEVELOPMENT_VISIBLE if produced else OutcomeAccess.OUTCOME_BLIND,
            *(value.outcome_access for value in parents))
        ceilings = tuple(value.visibility_ceiling for value in parents)
        return ArtifactWriteRequest(identifier, relative, schema, ArtifactProfile.CANONICAL_JSON,
            "application/json", identifier, str(Path(relative).parent), raw, inherited_visibility(ceilings, access),
            ceilings, access, lineage_parents=parents)
    index = canonical_json_document_bytes({"schema": "empirical-lawhood/operational/derived-metadata-index",
        "version": "1.0.0", "value": {"specification": specification.identity.to_document(),
            "publications": [{"logical_artifact_id": value.logical_artifact_id, "relative_path": value.relative_path,
                "payload_schema": value.payload_schema, "sha256": external.expected_content_sha256,
                "size_bytes": external.maximum_size_bytes} for external, _, value in planned],
            "scientific_authority": "NONE"}})
    requests = (
        publication_request("metadata-index.selected-declarative." + digest, metadata_relative + "/metadata-index." + digest + ".json",
            "empirical-lawhood/operational/derived-metadata-index", index),
        publication_request(selection.record_id, target, selection.SCHEMA, selection.canonical_bytes(),produced=True),
        publication_request("requirements.selected-declarative." + digest, metadata_relative + "/requirements." + digest + ".json",
            "empirical-lawhood/operational/experiment-input-requirements", requirements),
        publication_request(derived.selection_id, output_relative, derived.SCHEMA, derived.canonical_bytes()))
    # All knowable paths, serialization and custody bounds precede first effect.
    # Exact committed publications replay through the owning immutable writer.
    all_requests = (*tuple(value for _, _, value in planned), *requests)
    destinations = tuple(path for value in all_requests for path in (value.relative_path, value.relative_path + ".manifest.json"))
    if len(destinations) != len(set(destinations)):
        raise ValueError("selected derivation destinations overlap before publication")
    for request in all_requests:
        artifact_writer.preflight_write(request)
    if read_bounded_bytes(source, maximum_bytes=len(original_raw)) != original_raw:
        raise ValueError("original selected input selector changed before current publication")
    publish_current_metadata(specification, selection, writer=artifact_writer, planned=planned, require_current=require_current)
    # Navigable selector is last; requirements must already be durable.
    published = []
    for value in requests:
        require_current()
        published.append(artifact_writer.write(value))
    index_publication, selected_publication, requirement_publication, selector_publication = published
    loaded = load_experiment_inputs(specification, output, artifact_writer=artifact_writer, read_access=read_access)
    retained = prepare_experiment(specification, scientific_inputs=loaded.scientific_inputs,
        method_inputs=loaded.method_inputs, execution=execution)
    if retained != preparation:
        raise PermissionError("cold selected derivation changes exact current preparation")
    require_admitted_target_source_current(root, source_before)
    require_current()
    return ExperimentInputDerivationResult(specification.identity, derived, output, retained,
        (index_publication, selected_publication, selector_publication, requirement_publication), requirement_publication)


def derive_inputs(*, specification, source_selection_path, project_root, artifact_writer,
        metadata_directory, output_selection_path, execution, read_access=None):
    """Keep original custody and fresh actual parent access through return."""
    with artifact_writer.verification_scope() as writer:
        return _derive_inputs(specification=specification, source_selection_path=source_selection_path,
            project_root=project_root, artifact_writer=writer, metadata_directory=metadata_directory,
            output_selection_path=output_selection_path, execution=execution, read_access=read_access)


def prepare_authoring(preparation, *, project_root, artifact_writer, output_dir,read_access=None,original_input_access=None):
    """Bind only the actual candidate resources; preserve all scientific inputs."""
    from empirical_lawhood.api.authoring_handoff import preflight_authoring_output_directory
    from ...prospective_experiment import preview_prepared_prospective_experiment_candidate
    from empirical_lawhood.runtime.experiment_resources import bind_execution_resources
    from empirical_lawhood.runtime.experiment_preparation import DependencyKind
    selection, = (value for _, value in preparation.design_records if type(value) in domain.derived_selection_types())
    if preparation.specification_record.phase == "E5_OPPORTUNITY":
        expected = derive_authenticated_selection(preparation.specification_record, selection.request,
            writer=artifact_writer, project_root=project_root,read_access=read_access)
        if expected != selection:
            raise PermissionError("selected original source custody changed after derivation")
        return preparation
    unresolved = tuple(value for value in preparation.dependencies if value.kind is not DependencyKind.SOFTWARE or value.code != domain.RESOURCE_BINDING)
    if unresolved:
        raise ValueError("selected authoring retains exact source/entry prerequisites: " + ";".join(value.code for value in unresolved))
    # Authenticate actual original/qualification custody again at the authoring
    # boundary; the public derivation publications never confer authority.
    expected = derive_authenticated_selection(preparation.specification_record, selection.request,
        writer=artifact_writer, project_root=project_root,read_access=read_access)
    if expected != selection: raise PermissionError("selected original source custody changed after derivation")
    validate_current_metadata(preparation.specification_record, selection)
    lowered, design, resources = domain.prospective_design(preparation.specification_record, selection)
    if lowered.draft != preparation.draft: raise ValueError("selected authoring changes its derived complete graph")
    preflight_authoring_output_directory(directory=Path(output_dir), repo_root=Path(project_root), artifact_writer=artifact_writer)
    preview = preview_prepared_prospective_experiment_candidate(preparation=preparation, design_inputs=design,
        source_configs=selection.request.source_configs, project_root=project_root, artifact_writer=artifact_writer,
        read_access=read_access,original_input_access=original_input_access)
    return replace(preparation, dependencies=(), prospective_spec=design.bind_resources(bind_execution_resources(resources,
        issued_extensions=preview.issued_extensions)), source_configs=selection.request.source_configs, prospective_candidate_preview=preview)
