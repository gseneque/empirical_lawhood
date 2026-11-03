# SPDX-License-Identifier: MPL-2.0
"""Owned public intent-to-plan transition, reusing the existing E4 lifecycle.

Only exact current metadata is published. Actual original producers, source
gates and authority are replayed first; native work remains a later issued act.
"""
from dataclasses import dataclass, replace
from hashlib import sha256
from pathlib import Path
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_declarative as domain
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_records as native
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_preparation as existing
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_programme as p, selected_e4_methods as science
from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_NPZ_CODEC
from empirical_lawhood.api.derived_array_access import derive_matrix_array_access, validate_derived_matrix_array_access
from empirical_lawhood.api.authoring_handoff import preflight_authoring_output_directory
from empirical_lawhood.api.derived_metadata_access import (
    derive_canonical_metadata_access, validate_derived_metadata_access,
)
from .matrix_sampling_runtime import _original_product
from .matrix_source_runtime import authenticate_matrix_source_qualification
from .recursive_qualified_parents import MAX_PARENT_BYTES, _output_payload
from .selected_e4_native_runtime import development_products, validate_original_calibration_phase
from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.infrastructure.publication_metadata import authenticate_published_materialization
from empirical_lawhood.infrastructure.source_closure import (
    capture_admitted_target_source, require_admitted_target_source_current,
)
from empirical_lawhood.infrastructure.source_origin import require_selected_implementation
from empirical_lawhood.infrastructure.task_receipts import encode_artifact_manifest
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, inherited_visibility
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, canonical_json_bytes, validate_stable_id
from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputSelection, ExperimentInputBinding
from empirical_lawhood.runtime.artifacts import ArtifactManifest, ArtifactProfile, ArtifactWriteRequest, ArtifactWriteResult, derived_outcome_access
from empirical_lawhood.runtime.experiment_preparation import ExperimentInputDerivationResult


def authenticate_inputs(writer, specification, selected, codecs, *, project_root, execution):
    """Replay original custody once; only bounded summaries leave that owner."""
    request, bank = selected.request, selected.bank
    from .selected_prepared_access import selected_e4_original_input_access
    actual_parents=selected_e4_original_input_access(artifact_writer=writer,upstream_products=request.upstream_products,
        calibration_product=request.calibration_product,
        development=(request.development_nomination,request.development_freeze)).parents
    if actual_parents!=request.produced_input_parents:
        raise PermissionError("declarative E4 substitutes its exact actual produced-input parent census")
    programme = domain.validate_request(specification, request, bank, selected.calibration_bank)
    from .matrix_full_factor_secondary import authenticate_e4_secondary_target
    if authenticate_e4_secondary_target(writer=writer, selection=selected.secondary_readout, bank=bank) != request.structure.secondary_target:
        raise PermissionError('declarative E4 replaces the original frozen target')
    if request.bank_publication is None or request.source is None:
        raise ValueError("declarative E4 lacks actual bank publication and independent source qualification")
    authenticate_published_materialization(writer, request.bank_publication)
    raw_bank = read_bounded_bytes(writer.root.resolve(request.bank_publication.materialization.relative_path,
        for_write=False), maximum_bytes=len(bank.canonical_bytes()))
    if raw_bank != bank.canonical_bytes():
        raise PermissionError("declarative E4 substitutes exact original bank publication")
    summary_id = "original-summary." + request.record_id
    if specification.bank_recipe is not None:
        from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_bank_recipe import validate_selected_e4_recipe_bank
        from .selected_e4_bank_recipe import authenticate_selected_e4_bank_recipe_inputs
        inputs = selected.bank_recipe_inputs
        if (inputs is None or inputs.original_products != request.upstream_products
                or inputs.original_public_package != bank.forecast_design.package):
            raise PermissionError("declarative E4 recipe and current entry must bind the same actual original producer census")
        validate_selected_e4_recipe_bank(inputs, bank, bank.phase)
        summary = authenticate_selected_e4_bank_recipe_inputs(inputs=inputs, project_root=project_root,
            artifact_writer=writer, execution=execution, summary_record_id=summary_id)
    else:
        from .matrix_selected_e3_e4_runtime import authenticate_selected_e3_public_package
        summary = authenticate_selected_e3_public_package(writer=writer, public=bank.forecast_design.package,
            upstream_products=request.upstream_products, codecs=codecs, summary_record_id=summary_id,
            response_criterion=bank.forecast_design.criterion_record,
            prefix_policies=bank.specification.selection.prefix_policies,
            downstream_coordinates=bank.reservation.allocation.coordinates)
    if type(summary) is not p.SelectedE4OriginalCalibrationSummary:
        raise TypeError("original custody owner must return only its exact bounded calibration summary")
    scope = None
    (development, nomination), (frozen_development, frozen) = development_products(writer,
        ((request.development_nomination, 'revision-fit'), (request.development_freeze, 'revision-freeze')),
        codecs, _secondary_readout=selected.secondary_readout)
    if development != frozen_development:
        raise PermissionError("declarative E4 combines different actual DEV selection/freeze populations")
    p.validate_phase_separation(development, programme)
    revision = p.SelectedE4RevisionExport.from_products(development, nomination, frozen, record_id="revision." + request.record_id)
    public_calibration = None
    if programme.mode == "E4_CONFIRMATION" and revision.models is not None:
        if request.calibration_product is None:
            raise ValueError("triggered E4 CONF needs the actual separate issued CAL producer and reveal")
        projected = []
        def validate_original(**kwargs):
            payload = _output_payload(kwargs["writer"], kwargs["receipt"], kwargs["logical"], MAX_PARENT_BYTES)
            actual = decode_canonical_bytes(payload, science.SelectedE4Calibration, maximum_bytes=MAX_PARENT_BYTES)
            if actual.canonical_bytes() != payload or actual.identity != request.calibration_product.record:
                raise PermissionError("declarative E4 CAL original changes exact canonical bytes")
            current = p.SelectedE4PublicCalibration.from_calibration(actual, record_id="public-calibration." + request.record_id)
            validate_original_calibration_phase(expected_public=current, confirmation=programme, **kwargs)
            projected.append(current)
        _original_product(writer, request.calibration_product, request.calibration_product.record, codecs,
            scope, scope_validator=validate_original)
        if len(projected) != 1:
            raise PermissionError("declarative E4 calibration must have one actual authenticated producer")
        public_calibration, = projected
        declared_cal = p.SelectedE4PhaseProgramme.from_bank(selected.calibration_bank, programme_id=request.calibration_programme_id)
        if public_calibration.specification.calibration_programme != declared_cal.identity:
            raise PermissionError("declarative E4 CONF substitutes the separately declared original CAL population")
    elif request.calibration_product is not None:
        raise ValueError("untriggered or CAL phase cannot gain a fictitious E4 calibration producer")
    evidence = native.SelectedE4ProtectedEvidence("evidence." + request.record_id, programme.identity,
        request.upstream_products, request.development_nomination, request.development_freeze, request.source,
        request.calibration_product, request.produced_input_parents)
    native.validate_evidence(evidence, programme, bank, revision.decision, revision.models, public_calibration)
    source = request.source
    authenticate_matrix_source_qualification(writer=writer, specification=source.specification, result=source.result,
        pipeline=source.pipeline, executions=source.executions, publications=source.publications, codecs=codecs, read_scope=scope)

    # Preserve original selection/reservation/audit/assay and template custody.
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import authenticate_publication
    for record, publication in ((bank.reservation.allocation, bank.reservation.publication),
            (bank.specification.selection, bank.specification.publication), (bank.audit, bank.audit_publication),
            (bank.response_selection, bank.response_selection_publication),
            (bank.forecast_design.criterion_record, bank.forecast_design.criterion_publication)):
        authenticate_publication(writer, publication, record)
    for publication in (*bank.audit.prior_corpus, *bank.response_selection.template_publications):
        authenticate_published_materialization(writer, publication)
    return evidence, revision, summary, public_calibration


def _write(writer, relative, logical_id, record, *, access=OutcomeAccess.OUTCOME_BLIND,lineage_parents=()):
    access=derived_outcome_access(access,*(value.outcome_access for value in lineage_parents))
    ceilings=tuple(value.visibility_ceiling for value in lineage_parents)
    return writer.write(ArtifactWriteRequest(logical_id, relative, record.SCHEMA, ArtifactProfile.CANONICAL_JSON,
        "application/json", "e4-declarative-inputs", str(Path(relative).parent), record.canonical_bytes(),
        inherited_visibility(ceilings,access), ceilings, access,lineage_parents=lineage_parents))


def expected_declaration_publication(writer, directory, declaration):
    """Deterministic future metadata; not evidence that publication occurred."""
    relative = (directory / "native-declaration.json").relative_to(writer.root.contract.canonical_path).as_posix()
    parents=declaration.produced_input_parents
    access=derived_outcome_access(OutcomeAccess.OUTCOME_BLIND,*(value.outcome_access for value in parents))
    ceilings=tuple(value.visibility_ceiling for value in parents)
    request = ArtifactWriteRequest(declaration.identity.object_id, relative, declaration.SCHEMA, ArtifactProfile.CANONICAL_JSON,
        "application/json", declaration.identity.object_id, str(Path(relative).parent), declaration.canonical_bytes(),
        inherited_visibility(ceilings,access), ceilings, access,lineage_parents=parents)
    logical, physical, _, _ = writer._prepare(request)
    prepared = writer._preflight_publication((request,))
    raw = encode_artifact_manifest(logical, physical, prepared.publication)
    sidecar = writer._manifest_materialization(logical_artifact_id=request.logical_artifact_id,
        relative_path=relative + ".manifest.json", payload=raw)
    return ArtifactWriteResult(logical, physical, sidecar, True)


def _wave_operands(plan, publication):
    for wave in plan.declaration.programme.waves:
        specification = existing.component_specification(plan, wave.wave_id)
        resolved = existing.ResolvedSelectedE4ComponentInputs(plan,wave.wave_id,publication,None)
        yield existing.component_source_operands(specification,resolved)


def materialize_plan_access(writer, plan, publication, metadata_relative):
    if plan.declaration.bank_phase == "CALIBRATION" and plan.declaration.models is None:
        return plan, ()
    profile = plan.evidence.source.pipeline.pipeline_config.profile
    publications, configs, qualifications = [], {}, {}
    arrays_by_identity = {(value.logical.logical_artifact_id, value.logical.content_sha256): value
        for value in plan.bank.response_selection.template_publications}
    from empirical_lawhood.api.derived_array_access import (
        DerivedInputAccess, derive_matrix_input_access_batch, supports_derived_input_access_batch,
    )
    from empirical_lawhood.infrastructure.publication_metadata import checkpoint_publication_access
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_produced_inputs import produced_record_parents,produced_access
    canonical = {}
    def retain_access(config, qualification):
        if config.source_id in configs and configs[config.source_id] != config:
            raise ValueError("shared E4 source configuration changes exact payload/access across waves")
        configs[config.source_id] = config
        if qualification.receipt_id in qualifications and qualifications[qualification.receipt_id] != qualification:
            raise ValueError("derived E4 qualification aliases distinct local semantic scopes")
        qualifications[qualification.receipt_id] = qualification
    for draft, records, arrays in _wave_operands(plan, publication):
        pending = []
        batch_access = supports_derived_input_access_batch(writer, len(draft.external_inputs))
        if batch_access:
            checkpoint_publication_access(writer)
        records, arrays = dict(records), dict(arrays)
        for external in draft.external_inputs:
            if external.input_id in records:
                record = records[external.input_id]
                parents=produced_record_parents(record,plan.evidence.produced_input_parents)
                if parents and (external.outcome_access,external.visibility_ceiling)!=produced_access(
                        declared_access=external.outcome_access,declared_visibility=external.visibility_ceiling,parents=parents):
                    raise PermissionError("selected E4 native provider input lacks actual original-parent custody projection")
                key = (external.logical_artifact_id, record.fingerprint(), external.outcome_access, external.visibility_ceiling)
                stored = canonical.get(key)
                if stored is None:
                    filename = sha256(canonical_json_bytes(key)).hexdigest() + ".json"
                    stored = _write(writer, metadata_relative + "/operands/" + filename,
                        external.logical_artifact_id, record, access=external.outcome_access,lineage_parents=parents)
                    canonical[key] = stored
                    publications.append(stored)
                if batch_access:
                    pending.append(DerivedInputAccess(stored, record, external))
                    continue
                config, qualification = derive_canonical_metadata_access(writer=writer, publication=stored, record=record,
                    external=external, root=draft.prospective_draft, source_profile=profile)
            elif external.input_id in arrays:
                artifact = arrays[external.input_id]
                stored = arrays_by_identity.get((artifact.artifact_id, artifact.sha256))
                if stored is None:
                    raise ValueError("derived E4 wave lacks exact original template publication")
                if stored.logical.logical_artifact_id != external.logical_artifact_id:
                    raw = read_bounded_bytes(writer.root.resolve(stored.materialization.relative_path, for_write=False),
                        maximum_bytes=artifact.size_bytes)
                    if (len(raw), sha256(raw).hexdigest()) != (artifact.size_bytes, artifact.sha256):
                        raise PermissionError("derived template copy changes actual original bytes")
                    filename = sha256(canonical_json_bytes((external.logical_artifact_id, artifact.sha256))).hexdigest() + ".npz"
                    stored = writer.write(ArtifactWriteRequest(external.logical_artifact_id, metadata_relative + "/operands/" + filename,
                        external.payload_schema, MATRIX_NPZ_CODEC.profile, external.media_type, "e4-derived-templates",
                        metadata_relative + "/operands", raw, external.visibility_ceiling, (), external.outcome_access,
                        semantic_validation=stored.logical.semantic_validation))
                    publications.append(stored)
                templates = tuple(value.templates for value in plan.bank.response_selection.protocols
                    if (value.templates.array_artifact.sha256, value.templates.array_artifact.payload_schema,
                        value.templates.array_artifact.size_bytes) == (artifact.sha256, artifact.payload_schema, artifact.size_bytes))
                if not templates or any(value.members != templates[0].members for value in templates):
                    raise ValueError("derived templates lose one exact original typed member/shape contract")
                if batch_access:
                    pending.append(DerivedInputAccess(stored, templates[0], external))
                    continue
                config, qualification = derive_matrix_array_access(writer=writer, publication=stored, arrays=templates[0],
                    external=external, root=draft.prospective_draft, source_profile=profile)
            else:
                raise ValueError("derived E4 wave omits an actual current canonical or storage operand")
            retain_access(config, qualification)
        if pending:
            for config, qualification in derive_matrix_input_access_batch(writer=writer, inputs=tuple(pending),
                    root=draft.prospective_draft, source_profile=profile):
                retain_access(config, qualification)
    return domain.with_access(plan, tuple(configs.values()), tuple(qualifications.values())), tuple(publications)


def validate_access(plan, expected_publication):
    if plan.declaration.bank_phase == "CALIBRATION" and plan.declaration.models is None:
        if plan.preparation.qualifications or plan.preparation.source_configs:
            raise ValueError("unentered CAL cannot gain native input admissions")
        return
    profile = plan.evidence.source.pipeline.pipeline_config.profile
    configs = {value.source_id: value for value in plan.preparation.source_configs}
    used_receipts, used_sources = set(), set()
    for draft, records, arrays in _wave_operands(plan, expected_publication):
        records, arrays = dict(records), dict(arrays)
        versions = {external.logical_artifact_id: records[external.input_id].VERSION
            if external.input_id in records else MATRIX_NPZ_CODEC.record_version for external in draft.external_inputs}
        selected = existing.select_component_qualifications(draft, plan.preparation.qualifications, versions, profile.observation_operator)
        for external, qualification in ((value, next(row for row in selected if row.source_id == value.input_id))
                for value in draft.external_inputs):
            config = configs.get(external.input_id)
            if external.input_id in records:
                validate_derived_metadata_access(external=external, root=draft.prospective_draft, source_profile=profile,
                    version=versions[external.logical_artifact_id], config=config, qualification=qualification)
            else:
                artifact = arrays[external.input_id]
                templates = tuple(value.templates for value in plan.bank.response_selection.protocols
                    if (value.templates.array_artifact.sha256, value.templates.array_artifact.payload_schema,
                        value.templates.array_artifact.size_bytes) == (artifact.sha256, artifact.payload_schema, artifact.size_bytes))
                if not templates or any(value.members != templates[0].members for value in templates):
                    raise ValueError("derived templates change exact original typed member/shape contract")
                validate_derived_matrix_array_access(arrays=templates[0], external=external, root=draft.prospective_draft,
                    source_profile=profile, config=config, qualification=qualification)
            used_sources.add(external.input_id)
            used_receipts.add(qualification.receipt_id)
    if used_sources != set(configs) or used_receipts != {value.receipt_id for value in plan.preparation.qualifications}:
        raise ValueError("derived E4 source access adds undeclared payloads or semantic receipt variants")


@dataclass(frozen=True, slots=True)
class SelectedE4DerivedMetadataIndex(CanonicalRecord):
    """Complete retained publication census; no outcome data or authority."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/operational/selected-e4-derived-metadata-index"
    record_id: str
    specification: ObjectIdentity
    request: ObjectIdentity
    plan: ObjectIdentity | None
    members: tuple[ArtifactManifest, ...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (type(self.members) is not tuple or any(type(value) is not ArtifactManifest for value in self.members)
                or tuple(value.materialization.relative_path for value in self.members) !=
                    tuple(sorted({value.materialization.relative_path for value in self.members}))
                or len(self.canonical_bytes()) > 64 * 1024**2):
            raise ValueError("E4 derived metadata index needs its complete unique bounded original publication census")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)


def _result(*, specification, selector, selected, plan, writer, metadata_relative, metadata_to_inputs,
        destination, selector_relative, execution, publications, retained_members=(), before_publish=None, read_access=None):
    from .experiment_preparation import load_experiment_inputs, prepare_experiment
    parents=selected.request.produced_input_parents
    access=derived_outcome_access(OutcomeAccess.OUTCOME_BLIND,*(value.outcome_access for value in parents))
    ceilings=tuple(value.visibility_ceiling for value in parents)
    visibility=inherited_visibility(ceilings,access)
    current = {"request": selected.request, "bank": selected.bank}
    if selected.calibration_bank is not None:
        current["calibration_bank"] = selected.calibration_bank
    if selected.secondary_readout is not None:
        current['secondary_readout'] = selected.secondary_readout
    if plan is not None:
        current["plan"] = plan
    bindings = {value.key: value for value in selector.bindings if value.key not in {"request", "bank", "calibration_bank", "plan", "secondary_readout"}}
    requests = []
    for role, record in current.items():
        filename = role + ".json"
        identity, payload = record.identity, record.canonical_bytes()
        requests.append(ArtifactWriteRequest(identity.object_id, metadata_relative + "/" + filename, record.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, "application/json", "e4-declarative-inputs", metadata_relative, payload,
            visibility, ceilings, access,lineage_parents=parents))
        bindings[role] = ExperimentInputBinding(role, identity, (metadata_to_inputs / filename).as_posix(), len(payload))
    requests.append(ArtifactWriteRequest(specification.identity.object_id, metadata_relative + "/specification.json",
        specification.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", "e4-declarative-inputs",
        metadata_relative, specification.canonical_bytes(), visibility, ceilings, access,lineage_parents=parents))
    bound = ExperimentFileInputSelection(selector.selection_id + ".derived." + selected.request.fingerprint(),
        domain.PROTOCOL_ID, tuple(bindings[key] for key in sorted(bindings)), selector.files)
    selected_records = dict(current)
    if selected.bank_recipe_inputs is not None:
        selected_records["bank-recipe-inputs"] = selected.bank_recipe_inputs
    rebound = domain.bind_inputs(specification, selected_records)
    preparation = prepare_experiment(specification, scientific_inputs=rebound.scientific_inputs,
        method_inputs=rebound.method_inputs, execution=execution)
    document = {"schema": "empirical-lawhood/operational/experiment-input-requirements", "version": "1.0.0",
        "value": {"specification": specification.identity.to_document(), "request": selected.request.identity.to_document(),
            "source_selection": ObjectIdentity.from_record(bound.selection_id, bound).to_document(),
            "generated_plan": None if plan is None else plan.identity.to_document(),
            "authority": "NONE", "native_contact": "NONE",
            "dependencies": tuple({"code": value.code, "kind": value.kind.value, "detail": value.detail,
                "source_key": value.source_key} for value in preparation.dependencies),
            "assessment_limitations": tuple({"code": value.code, "kind": value.kind.value, "detail": value.detail,
                "source_key": value.source_key} for value in preparation.assessment_limitations)}}
    payload = canonical_json_bytes(document)
    manifests = {value.materialization.relative_path: value for value in retained_members}
    for publication in publications:
        value = authenticate_published_materialization(writer, publication)
        previous = manifests.get(value.materialization.relative_path)
        if previous is not None and previous != value:
            raise ValueError("E4 metadata index aliases distinct actual materializations")
        manifests[value.materialization.relative_path] = value
    preflights = []
    for request in requests:
        logical, physical, _, _ = writer._prepare(request)
        prepared = writer._preflight_publication((request,))
        manifest = ArtifactManifest(logical, physical, prepared.publication)
        previous = manifests.get(request.relative_path)
        if previous is not None and previous != manifest:
            raise ValueError("E4 retained metadata index changes a planned immutable member")
        manifests[request.relative_path] = manifest
        preflights.append(prepared)
    index = SelectedE4DerivedMetadataIndex("metadata-index." + selected.request.record_id, specification.identity,
        selected.request.identity, None if plan is None else plan.identity, tuple(manifests[key] for key in sorted(manifests)))
    requirements_request = ArtifactWriteRequest("e4-requirements." + sha256(payload).hexdigest(),
        metadata_relative + "/requirements.json", document["schema"], ArtifactProfile.CANONICAL_JSON, "application/json",
        "e4-declarative-inputs", metadata_relative, payload, visibility, ceilings, access,lineage_parents=parents)
    index_request = ArtifactWriteRequest(index.identity.object_id, metadata_relative + "/index.json", index.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, "application/json", "e4-declarative-inputs", metadata_relative,
        index.canonical_bytes(), visibility, ceilings, access,lineage_parents=parents)
    selector_request = ArtifactWriteRequest(bound.selection_id, selector_relative, bound.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, "application/json", "e4-declarative-inputs", str(Path(selector_relative).parent),
        bound.canonical_bytes(), visibility, ceilings, access,lineage_parents=parents)
    complete_requests = (*requests, requirements_request, index_request, selector_request)
    for request in complete_requests[len(requests):]:
        writer._prepare(request)
        preflights.append(writer._preflight_publication((request,)))
    # All knowable cold preparation, bytes and immutable paths precede writes.
    if before_publish is not None:
        before_publish()
    replayed = []
    for request, preflight in zip(complete_requests, preflights, strict=True):
        replay = writer._replay_committed_publication((request,), preflight)
        if replay is None and any(writer.root.resolve(relative, for_write=True).exists()
                for relative in (request.relative_path, request.relative_path + ".manifest.json")):
            raise ValueError("E4 metadata has an orphan or foreign publication, not an exact committed prefix")
        replayed.append(None if replay is None else replay[0])
    results = tuple(old if old is not None else writer.write(request)
        for request, old in zip(complete_requests, replayed, strict=True))
    specification_publication = results[len(requests) - 1]
    requirements, index_publication, selector_publication = results[-3:]
    reopened = load_experiment_inputs(specification, destination, artifact_writer=writer, read_access=read_access)
    actual_preparation = prepare_experiment(specification, scientific_inputs=reopened.scientific_inputs,
        method_inputs=reopened.method_inputs, execution=execution)
    if actual_preparation != preparation:
        raise ValueError("actual cold public E4 preparation differs from its precomputed source/scientific projection")
    return ExperimentInputDerivationResult(specification.identity, bound, destination, preparation,
        (specification_publication, index_publication, requirements, selector_publication), requirements)


def _retained_selected(*, writer, specification, original, destination, metadata, selector_relative, read_access=None):
    """Authenticate a complete former projection; preserve original created flags."""
    from .experiment_preparation import load_experiment_inputs
    selector_raw = read_bounded_bytes(destination, maximum_bytes=64 * 1024**2)
    selector = decode_canonical_bytes(selector_raw, ExperimentFileInputSelection, maximum_bytes=len(selector_raw))
    if selector.canonical_bytes() != selector_raw or selector.protocol_id != domain.PROTOCOL_ID:
        raise ValueError("retained E4 source selector changes its exact protocol or canonical bytes")
    stored = load_experiment_inputs(specification, destination, artifact_writer=writer, read_access=read_access).method_inputs
    if type(stored) is not domain.SelectedE4DeclarativeInputs:
        raise TypeError("retained E4 selector changes its exact input owner")
    derived_fields = ("programme_id", "bank_publication", "calibration_programme_id")
    if any(getattr(original.request, name) is not None and getattr(original.request, name) != getattr(stored.request, name)
            for name in derived_fields):
        raise ValueError("retained E4 derivation changes an explicitly selected original programme or bank publication")
    if specification.bank_recipe is None and any(getattr(original.request, name) != getattr(stored.request, name)
            for name in derived_fields):
        raise ValueError("an exact-bank retry cannot replace caller-selected source or programme fields")
    expected = replace(stored.request, programme_id=original.request.programme_id,
        bank_publication=original.request.bank_publication,
        calibration_programme_id=original.request.calibration_programme_id)
    if (expected != original.request or stored.bank_recipe_inputs != original.bank_recipe_inputs
            or stored.secondary_readout != original.secondary_readout
            or (original.bank is not None and stored.bank != original.bank)
            or (original.calibration_bank is not None and stored.calibration_bank != original.calibration_bank)):
        raise ValueError("retained E4 derivation differs from copied scientific or operational intent")
    raw = read_bounded_bytes(metadata / "index.json", maximum_bytes=64 * 1024**2)
    index = decode_canonical_bytes(raw, SelectedE4DerivedMetadataIndex, maximum_bytes=len(raw))
    if (index.canonical_bytes() != raw or index.specification != specification.identity
            or index.request != stored.request.identity
            or index.plan != (None if stored.plan is None else stored.plan.identity)):
        raise ValueError("retained E4 index differs from the exact original projection")
    for relative, record, payload in ((selector_relative, selector, selector_raw),
            ((metadata / "index.json").relative_to(Path(writer.root.contract.canonical_path)).as_posix(), index, raw)):
        manifest = writer.read_manifest(relative)
        writer.verify_manifest(manifest)
        record_id = record.selection_id if type(record) is ExperimentFileInputSelection else record.identity.object_id
        if (manifest.logical.logical_artifact_id, manifest.logical.payload_schema,
                manifest.logical.content_sha256, manifest.materialization.size_bytes) != (
                    record_id, record.SCHEMA, record.fingerprint(), len(payload)):
            raise ValueError("retained E4 metadata index has a different actual publication")
    for manifest in index.members:
        writer.verify_manifest(manifest)
    # Parent custody, original source and complete cold access are replayed
    # afresh below. A retained index creates no admission or authority.
    return replace(stored, plan=None), index.members


def derive_inputs(*, specification, source_selection_path, project_root, artifact_writer,
        metadata_directory, output_selection_path, execution, read_access=None):
    from .experiment_preparation import load_experiment_inputs, _protocol
    from empirical_lawhood.api.recursive_operations import operation_catalog
    source, destination, metadata = map(Path, (source_selection_path, output_selection_path, metadata_directory))
    if (not all(value.is_absolute() for value in (source, destination, metadata))
            or source.parent != destination.parent or source == destination
            or any(path.is_symlink() for value in (source, destination, metadata) for path in (value, *value.parents))):
        raise ValueError("E4 derivation requires explicit unlinked output/metadata under the selected input root")
    root = Path(project_root).resolve(strict=True)
    require_selected_implementation(root)
    admitted = capture_admitted_target_source(root)
    plane = Path(artifact_writer.root.contract.canonical_path).resolve(strict=True)
    metadata_relative = metadata.relative_to(plane).as_posix()
    selector_relative = destination.relative_to(plane).as_posix()
    metadata_to_inputs = metadata.relative_to(source.parent)
    artifact_writer.root.resolve(selector_relative, for_write=True)
    original_raw = read_bounded_bytes(source, maximum_bytes=_protocol(specification).maximum_config_bytes)
    selector = decode_canonical_bytes(original_raw, ExperimentFileInputSelection, maximum_bytes=len(original_raw))
    selected = load_experiment_inputs(specification, source, artifact_writer=artifact_writer, read_access=read_access).method_inputs
    if type(selected) is not domain.SelectedE4DeclarativeInputs or selected.plan is not None:
        raise ValueError("E4 derive-inputs requires copied intent, not an already generated plan")
    retained_members = ()
    if destination.exists():
        selected, retained_members = _retained_selected(writer=artifact_writer, specification=specification, original=selected,
            destination=destination, metadata=metadata, selector_relative=selector_relative, read_access=read_access)
    if execution.workers != selected.request.resources.controls.maximum_parallel_tasks:
        raise ValueError("copied E4 resource profile and explicit execution workers differ")
    directory = artifact_writer.root.resolve(selected.request.programme_directory, for_write=True)
    preflight_authoring_output_directory(directory=directory, repo_root=root, artifact_writer=artifact_writer)
    def require_stable():
        if read_bounded_bytes(source, maximum_bytes=len(original_raw)) != original_raw:
            raise ValueError("copied E4 source selection changed during derivation")
        require_admitted_target_source_current(root, admitted)
    publications = ()
    if selected.bank is None:
        require_stable()
        from .selected_e4_bank_recipe import publish_selected_e4_bank_recipe
        result = publish_selected_e4_bank_recipe(inputs=selected.bank_recipe_inputs, project_root=root,
            artifact_writer=artifact_writer, metadata_directory=metadata / "bank", execution=execution,
            _admitted_source=admitted)
        banks, programmes, stored = dict(result.banks), dict(result.programmes), dict(result.publications)
        phase = specification.population_phase
        request = replace(selected.request, programme_id=programmes[phase].programme_id,
            bank_publication=stored[phase + ".bank"],
            calibration_programme_id=programmes["CALIBRATION"].programme_id if phase == "CONFIRMATION" else None)
        selected = replace(selected, request=request, bank=banks[phase],
            calibration_bank=banks["CALIBRATION"] if phase == "CONFIRMATION" else None)
        publications = tuple(value for _, value in result.publications)
    else:
        domain.validate_request(specification, selected.request, selected.bank, selected.calibration_bank)
    if any(value.observed_git_head != admitted.implementation_commit for value in selected.bank.provenances):
        raise ValueError("new E4 native preparation requires fresh actual current provenance; old source cannot be relabelled")
    source_evidence = selected.request.source
    if (source_evidence is None or source_evidence.specification.source_identity != selected.bank.identity
            or selected.request.bank_publication is None or selected.secondary_readout is None):
        # Newly derived source membership never inherits old qualification.
        # Return actual new records and exact missing gates, without fitting,
        # authoring components, issue, reveal or native acquisition.
        plan = None
    else:
        evidence, revision, summary, calibration = authenticate_inputs(artifact_writer, specification, selected,
            operation_catalog()[2], project_root=root, execution=execution)
        plan = domain.assemble_plan(specification, selected, evidence=evidence, revision=revision, summary=summary, calibration=calibration)
        expected = expected_declaration_publication(artifact_writer, directory, plan.declaration)
        require_stable()
        plan, current_publications = materialize_plan_access(artifact_writer, plan, expected, metadata_relative)
        publications = (*publications, *current_publications)
        domain.validate_plan(specification, replace(selected, plan=plan))
        validate_access(plan, expected)
    require_stable()
    return _result(specification=specification, selector=selector, selected=selected, plan=plan, writer=artifact_writer,
        metadata_relative=metadata_relative, metadata_to_inputs=metadata_to_inputs, destination=destination,
        selector_relative=selector_relative, execution=execution, publications=publications, retained_members=retained_members, before_publish=require_stable, read_access=read_access)


class SelectedE4DeclarativeProgrammeService:
    """One authoring adaptation; retained execution uses the original service."""
    def __init__(self, *, service, descriptor=None):
        self.service = service
        if descriptor is not None:
            raise ValueError("declarative E4 has no separate retained execution lifecycle")

    def author(self, *, preparation, output_dir):
        from empirical_lawhood.api.recursive_operations import operation_catalog
        from empirical_lawhood.api.selected_e4_programme_service import SelectedE4ProgrammeService
        specification = preparation.specification_record
        requests = tuple(value for _, value in preparation.design_records if type(value) is domain.SelectedE4DeclarativeRequest)
        if type(specification) is not domain.SelectedE4DeclarativeSpecification or len(requests) != 1:
            raise TypeError("declarative E4 author loses original copied intent")
        request, = requests
        expected_directory = self.service.artifact_writer.root.resolve(request.programme_directory, for_write=True)
        if Path(output_dir) != expected_directory:
            raise ValueError("E4 authoring directory differs from the exact selected future declaration location")
        plan = preparation.programme
        if type(plan) is not existing.SelectedE4ProtectedProgrammePlan or preparation.dependencies:
            raise ValueError("declarative E4 author requires its complete prepared plan and no missing dependencies")
        bundles = tuple(value for _, value in preparation.design_records if type(value) is domain.SelectedE4BankRecipeSourceInputs)
        selected = domain.SelectedE4DeclarativeInputs(request, plan.bank, None, plan, bundles[0] if len(bundles) == 1 else None)
        if plan.declaration.bank_phase == "CONFIRMATION":
            # The separate CAL bank is a scientific source operand, retained
            # by the copied request binding in preparation design records.
            banks = tuple(value for _, value in preparation.design_records if type(value) is p.SelectedE4PhaseBank)
            if len(banks) != 1:
                raise ValueError("declarative CONF loses actual declared CAL bank")
            selected = replace(selected, calibration_bank=banks[0])
        domain.validate_plan(specification, selected)
        expected = expected_declaration_publication(self.service.artifact_writer, expected_directory, plan.declaration)
        validate_access(plan, expected)
        evidence, revision, summary, calibration = authenticate_inputs(self.service.artifact_writer, specification, selected,
            operation_catalog()[2], project_root=self.service.project_root, execution=preparation.execution)
        if (evidence, revision, summary, calibration) != (
                plan.evidence, plan.tail.revision, plan.declaration.original_summary, plan.declaration.calibration):
            raise PermissionError("E4 author changes actual original producer results after derivation")
        component = replace(preparation, specification=plan.specification.identity, specification_record=plan.specification)
        return SelectedE4ProgrammeService(service=self.service).author(preparation=component, output_dir=output_dir)

    def run(self, **kwargs):
        raise ValueError("use the existing retained E4 programme descriptor returned by author")

    def read(self, **kwargs):
        raise ValueError("use the existing retained E4 programme descriptor returned by author")

    def recover(self, **kwargs):
        raise ValueError("use the existing retained E4 programme descriptor returned by author")


def programme_service_factory(*, service, descriptor=None):
    return SelectedE4DeclarativeProgrammeService(service=service, descriptor=descriptor)
