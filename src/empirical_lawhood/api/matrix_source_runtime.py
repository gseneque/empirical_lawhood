# SPDX-License-Identifier: MPL-2.0
"""Original Matrix source qualification through existing custody and owners.

Scientific consumer scope is checked by each domain. This owner authenticates
the real pipeline, qualified/recovered output and every original independent
gate, then replays the existing noncompensating scientific-source service.
"""

import json
from dataclasses import replace
from functools import partial
from hashlib import sha256

from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import authenticate_publication
from empirical_lawhood.adapters.methods.matrix_source_evidence import MatrixSourcePipelineEvidence, reference, source_declarations
from .recursive_qualified_parents import _authenticate_prior_execution
from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_document_bytes
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.planning.metatheory import MetatheoryApplicability
from empirical_lawhood.planning.scientific_source_qualification import ScientificSourceGateEvidence, ScientificSourceQualificationResult, ScientificSourceQualificationSpec
from empirical_lawhood.planning.source_pipelines import SourcePipelineQualificationReceipt
from empirical_lawhood.planning.study_authoring import StudyDraft
from empirical_lawhood.runtime.recursive_qualified_parents import RecursivePriorExecutionBinding
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteResult
from empirical_lawhood.runtime.source_pipelines import plan_source_pipeline_resume


def _genuine_context(package, execution_plan, units):
    draft = package.issued_study.candidate.authoring_package.base.draft
    if (type(draft) is not StudyDraft or draft.evaluation_unit_ids != units
            or draft.system is None or draft.system.world.kind is not WorldKind.NUMERICAL_SIMULATOR
            or any(getattr(value, "fixture_scope_id", None) is not None
                or getattr(value, "plumbing_only", False) for value in (package, execution_plan, draft))):
        raise PermissionError("Matrix source qualification requires actual numerical scientific scope, not fixture or source-free plumbing")


def _owner_scope(*, parent_evidence, binding, package, execution_plan, writer):
    config, product, declaration, units = parent_evidence
    _genuine_context(package, execution_plan, units)
    tasks = tuple(value for value in execution_plan.tasks if value.task_id == binding.task_id)
    if len(tasks) != 1:
        raise PermissionError("Matrix source owner lacks its one original scientific producer")
    task, = tasks
    manifest = declaration.manifest()
    identifier = "receipt_id" if type(product) is SourcePipelineQualificationReceipt else "result_id"
    if (binding.record != reference(product, identifier) or binding.record_id_field != identifier
            or task.capability.capability_key != manifest.capability_key
            or task.capability.capability_version != manifest.capability_version
            or task.capability_implementation_sha256 != manifest.implementation_sha256
            or (task.capability.config.config_id, task.capability.config.config_schema, task.capability.config.content_sha256)
                != (config.config_id, config.SCHEMA, config.fingerprint())
            or task.dependency_task_ids or len(task.external_inputs) != 1):
        raise PermissionError("Matrix source owner substitutes its actual installed method, original configuration or input census")
    external, = task.external_inputs
    if (external.logical_artifact_id != task.capability.config.artifact_id
            or external.expected_payload_schema != config.SCHEMA
            or external.expected_content_sha256 != config.fingerprint()
            or external.expected_size_bytes not in (None,len(config.canonical_bytes()))
            or external.expected_media_type not in (None,"application/json")
            or external.expected_outcome_access not in (None,OutcomeAccess.OUTCOME_BLIND)
            or external.expected_visibility_ceiling not in (None,VisibilityCeiling.PROSPECTIVE)):
        raise PermissionError("Matrix source owner substitutes its one actual complete original configuration input")
    # Issued lowering retains exact schema/digest but may omit these optional
    # static fields. Authenticate the actual input with the complete bounded
    # blind/prospective contract, rather than infer its lane from omissions.
    from .matrix_selected_runtime import _published_input
    strict=replace(external,expected_size_bytes=len(config.canonical_bytes()),expected_media_type="application/json",
        expected_outcome_access=OutcomeAccess.OUTCOME_BLIND,expected_visibility_ceiling=VisibilityCeiling.PROSPECTIVE)
    if _published_input(writer,binding.run_id,strict,type(config)) != config:
        raise PermissionError("Matrix source owner changes its actual original canonical configuration")


def _gate_scope(*, parent_evidence, binding, package, execution_plan):
    spec, gate = parent_evidence
    _genuine_context(package, execution_plan, spec.physical_unit_ids)
    tasks = tuple(value for value in execution_plan.tasks if value.task_id == binding.task_id)
    if len(tasks) != 1:
        raise PermissionError("Matrix source gate lacks its one original independent producer")
    task, = tasks
    method = gate.method
    if (binding.record != reference(gate, "evidence_id") or binding.record_id_field != "evidence_id"
            or task.capability.capability_key != method.capability_key
            or task.capability.capability_version != method.capability_version
            or task.capability_implementation_sha256 != method.implementation_sha256
            or (task.capability.config.config_id, task.capability.config.config_schema, task.capability.config.content_sha256)
                != (method.config.object_id, method.config.object_schema, method.config.object_fingerprint)
            or task.capability.capability_key.startswith("executable-source-free-property-transport.")):
        raise PermissionError("Matrix source gate substitutes its actual independently installed scientific method")
    expected = {(value.object_schema, value.object_fingerprint) for value in (*gate.input_operands, method.config)}
    actual = {(value.expected_payload_schema, value.expected_content_sha256) for value in task.external_inputs}
    if (task.dependency_task_ids or actual != expected
            or len(task.external_inputs) != len(actual)):
        raise PermissionError("Matrix source gate changes its complete original fixed scientific operands")


def matrix_source_publication_references(specification, result, pipeline):
    """Exact retained canonical scientific operands expected by this owner."""
    config, receipt = pipeline.pipeline_config, pipeline.receipt
    values = (reference(specification, "spec_id"), config.identity, pipeline.qualification_config.identity,
        reference(pipeline.evidence_profile, "selection_id"), reference(config.profile, "profile_id"),
        specification.source_identity, specification.preparation,
        specification.observation_operator, specification.numerical_view, specification.causal_cutoff,
        receipt.publication, receipt.recovery, *receipt.validator_receipts,
        *(value for gate in result.gate_evidence for value in
            (*gate.input_operands, gate.method.config, gate.publication, gate.recovery, *gate.evidence_links)))
    refs = {}
    for value in values:
        if value is None:
            raise PermissionError("Matrix source qualification lacks original publication or recovery")
        if value == receipt.output_artifact:
            # This is the exact original output manifest, authenticated through
            # its existing binary-aware owner below; no second JSON publication
            # of a Parquet/array payload is required.
            continue
        if value.object_id in refs and refs[value.object_id] != value:
            raise PermissionError("Matrix source qualification aliases original immutable scientific operands")
        refs[value.object_id] = value
    return tuple(refs[key] for key in sorted(refs))


def retained_source_publications(*, writer, package, plan, selection, evidence, result):
    """Locate exact required handles; final independent qualification still replays.

    Explicit retained metadata needs no whole-plan input scan. Missing handles
    use only matching original external inputs, once per logical input.
    """
    from .selected_e4_bank_recipe import _publication_from_manifest
    from empirical_lawhood.infrastructure.provider_input_custody import provider_input_location

    expected = matrix_source_publication_references(evidence.qualification_config.specification, result, evidence)
    selected = dict(selection.metadata_publications)
    selected[selection.verification.identity] = selection.verification_publication
    missing = {(pin.object_schema, pin.object_fingerprint) for pin in expected if pin not in selected}
    candidates, visited = {}, set()
    for task in plan.tasks:
        if not missing:
            break
        for external in task.external_inputs:
            if external.logical_artifact_id in visited:
                continue
            key = external.expected_payload_schema, external.expected_content_sha256
            if None not in key and key not in missing:
                continue
            visited.add(external.logical_artifact_id)
            relative, _, _ = provider_input_location(writer, package.run_plan_id, external.logical_artifact_id)
            manifest = writer.read_manifest(relative)
            key = manifest.logical.payload_schema, manifest.logical.content_sha256
            if key not in missing:
                continue
            writer.verify_manifest(manifest)
            candidates[key] = _publication_from_manifest(writer, manifest)
            missing.remove(key)
    rows = []
    for pin in expected:
        publication = selected.get(pin, candidates.get((pin.object_schema, pin.object_fingerprint)))
        if publication is None:
            raise PermissionError("finite-dt source read omits an actual original required metadata publication")
        if (publication.logical.payload_schema, publication.logical.content_sha256,
                publication.materialization.physical_sha256) != (pin.object_schema, pin.object_fingerprint, pin.object_fingerprint):
            raise PermissionError("source read changes its exact retained metadata identity")
        rows.append((pin, publication))
    return tuple(rows)


def authenticate_matrix_source_qualification(*, writer, specification, result, pipeline, executions,
                                            publications, codecs, read_scope, consumer_programme=None,
                                            prepared_source_custody=None, prepared_source_selection=None,
                                            prepared_source_current_access=None):
    """Authenticate and replay exact original source owners; return no token."""
    if (type(specification) is not ScientificSourceQualificationSpec or type(result) is not ScientificSourceQualificationResult
            or type(pipeline) is not MatrixSourcePipelineEvidence):
        raise TypeError("Matrix source admission requires its original typed scientific qualification and pipeline")
    for value in (specification, result, pipeline):
        value.__post_init__()
    spec, config, receipt, qualification = specification, pipeline.pipeline_config, pipeline.receipt, pipeline.qualification_config
    profile = config.profile
    if (spec.outcome_access is not OutcomeAccess.OUTCOME_BLIND or spec.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE
            or (profile.outcome_access, profile.visibility_ceiling) != (spec.outcome_access, spec.visibility_ceiling)
            or (receipt.outcome_access, receipt.visibility_ceiling) != (spec.outcome_access, spec.visibility_ceiling)
            or spec.source_pipeline_profile != reference(profile, "profile_id")
            or spec.source_pipeline_qualification != reference(receipt, "receipt_id")
            or spec.evidence_profile_selection != reference(pipeline.evidence_profile, "selection_id")
            or qualification.specification != spec or qualification.pipeline_receipt != receipt
            or qualification.gate_evidence != result.gate_evidence
            or spec.source_materialization != receipt.output_artifact
            or spec.observation_operator != profile.observation_operator
            or spec.numerical_view.object_id not in profile.numerical_view_ids
            or spec.causal_cutoff != profile.causal_cutoff
            or any(value.physical_unit_count != len(spec.physical_unit_ids) for value in receipt.edge_accounting)):
        raise PermissionError("Matrix source qualification substitutes its actual profile/source/materialization/observation/cutoff or complete units")
    owned = prepared_source_custody is not None or prepared_source_selection is not None
    from .prepared_source_replay import (
        authenticated_prepared_source_replay, is_prepared_source_result,
        partition_prepared_source_publications,
    )
    if is_prepared_source_result(result) and not owned:
        if consumer_programme is None:
            raise PermissionError("prepared source consumer replay requires its actual downstream programme")
        scientific, bootstrap = partition_prepared_source_publications(writer=writer, publications=publications)
        with authenticated_prepared_source_replay(writer=writer, executions=executions,
                bootstrap_publications=bootstrap, codecs=codecs,
                current_access=prepared_source_current_access) as original:
            from .matrix_prepared_source_runtime import _validate_consumer_programme
            from .matrix_prepared_source_experiment import pipeline_evidence
            _validate_consumer_programme(original.selection.bank, consumer_programme)
            actual_pipeline, actual_result = pipeline_evidence(original.selection)
            if (actual_pipeline != pipeline or actual_result != result
                    or actual_pipeline.qualification_config.specification != specification):
                raise PermissionError("prepared source consumer substitutes the actual original source selection")
            # The producer context is independent of the consuming campaign.
            # Only this checked source bank discharges the consumer join above.
            authenticate_matrix_source_qualification(writer=original.writer, specification=specification,
                result=result, pipeline=pipeline, executions=executions, publications=scientific,
                codecs=codecs, read_scope=original.read_scope, prepared_source_custody=original.custody,
                prepared_source_selection=original.selection)
            original.writer.require_verification_snapshot()
            original.original_input_access.require_current()
        return
    if owned:
        from .matrix_prepared_source_runtime import (
            _prepared_gate_product_context, validate_prepared_gate_product, validate_prepared_terminal_product)
        from .current_task_custody import CurrentIssuedTaskCustody
        if (type(prepared_source_custody) is not CurrentIssuedTaskCustody
                or prepared_source_custody._current_package_plan is None or consumer_programme is not None):
            raise PermissionError("prepared source owning replay requires its paired live original context")
        package, execution_plan = prepared_source_custody._current_package_plan
        access = _prepared_gate_product_context(selection=prepared_source_selection,
            product_custody=prepared_source_custody, read_scope=read_scope,
            package=package, execution_plan=execution_plan)
    expected = tuple(sorted((reference(receipt, "receipt_id"), reference(result, "result_id"),
        *(reference(value, "evidence_id") for value in result.gate_evidence)), key=lambda value: value.object_id))
    if (type(executions) is not tuple or any(type(value) is not RecursivePriorExecutionBinding for value in executions)
            or tuple(value.record for value in executions) != expected or len({value.object_id for value in expected}) != len(expected)):
        raise PermissionError("Matrix source qualification loses its complete original pipeline, qualification and gate producers")
    declarations = source_declarations()
    by_ref = {value.record: value for value in executions}
    codecs = {**codecs, SourcePipelineQualificationReceipt.SCHEMA: SourcePipelineQualificationReceipt,
        ScientificSourceQualificationResult.SCHEMA: ScientificSourceQualificationResult,
        ScientificSourceGateEvidence.SCHEMA: ScientificSourceGateEvidence}
    for selected_config, product, declaration, field in ((config, receipt, declarations[0], "receipt_id"),
            (qualification, result, declarations[1], "result_id")):
        authenticated = _authenticate_prior_execution(by_ref[reference(product, field)], writer, codecs,
            scope_validator=partial(_owner_scope,writer=writer), parent_evidence=(selected_config, product, declaration, spec.physical_unit_ids),
            read_scope=read_scope, required_outcome_access=OutcomeAccess.OUTCOME_BLIND,
            **({} if not owned else {"product_custody": prepared_source_custody,
                "product_validator": partial(validate_prepared_terminal_product, selection=prepared_source_selection,
                    config=selected_config, product=product, declaration=declaration)}))
        if authenticated.product.payload != product.canonical_bytes():
            raise PermissionError("Matrix source qualifier changes actual original result bytes")
    for gate in result.gate_evidence:
        authenticated = _authenticate_prior_execution(by_ref[reference(gate, "evidence_id")], writer, codecs,
            scope_validator=_gate_scope, parent_evidence=(spec, gate), read_scope=read_scope,
            required_outcome_access=OutcomeAccess.OUTCOME_BLIND,
            **({} if not owned else {"product_custody": prepared_source_custody,
                "product_validator": partial(validate_prepared_gate_product, selection=prepared_source_selection)}))
        if authenticated.product.payload != gate.canonical_bytes():
            raise PermissionError("Matrix source gate changes actual original independent result bytes")
    expected_refs = matrix_source_publication_references(spec, result, pipeline)
    if (type(publications) is not tuple or any(type(row) is not tuple or len(row) != 2 for row in publications)
            or tuple(value for value, _ in publications) != expected_refs):
        raise PermissionError("Matrix source qualification changes its complete original publication/recovery census")
    for pin, publication in publications:
        _authenticate_source_publication(writer, pin, publication, pipeline,
            **({} if not owned else {"require_current": access.require_current}))
    if any(gate.method.capability_key.startswith("matrix-source.finite-dt-instrument.") for gate in result.gate_evidence):
        from empirical_lawhood.api.matrix_finite_dt_source_runtime import authenticate_installed_source_prerequisite
        authenticate_installed_source_prerequisite(writer=writer, result=result, pipeline=pipeline,
            publications=publications, read_scope=read_scope)
    if any(gate.method.capability_key.startswith("matrix-source.prepared-finite-dt.") for gate in result.gate_evidence):
        if owned:
            from .matrix_prepared_source_runtime import authenticate_owning_prepared_source_prerequisite
            authenticate_owning_prepared_source_prerequisite(writer=writer, selection=prepared_source_selection,
                result=result, pipeline=pipeline, read_scope=read_scope, product_custody=prepared_source_custody)
        else:
            from .matrix_prepared_source_runtime import authenticate_installed_prepared_source_prerequisite
            authenticate_installed_prepared_source_prerequisite(writer=writer, result=result, pipeline=pipeline,
                publications=publications, read_scope=read_scope, consumer_programme=consumer_programme)
    if owned:
        access.require_current()
    _authenticate_pipeline_output(writer, pipeline)
    if owned:
        access.require_current()
    if config.assess() != receipt:
        raise PermissionError("Matrix source pipeline disagrees with existing source/authority/validator/accounting owner replay")
    plan_source_pipeline_resume(profile, receipt, config.execution_evidence.output_manifest,
        artifact_writer=writer, catalog_projection_current=True)
    if qualification.assess() != result:
        raise PermissionError("Matrix source result disagrees with complete original noncompensating scientific gate replay")
    required = tuple(gate for gate in spec.gates if gate.applicability is MetatheoryApplicability.REQUIRED)
    if len(required) != len(result.gate_evidence):
        raise PermissionError("Matrix source qualification omits an independently assessed required source gate")
    if owned:
        writer.require_verification_snapshot()
        access.require_current()


def _authenticate_pipeline_output(writer, pipeline):
    """Keep native payloads behind their existing schema/profile/storage owner."""
    config, receipt = pipeline.pipeline_config, pipeline.receipt
    manifest = config.execution_evidence.output_manifest
    if (receipt.output_artifact != ObjectIdentity.from_record(manifest.logical.logical_artifact_id, manifest)
            or receipt.output_content_sha256 != manifest.logical.content_sha256
            or manifest.logical.payload_schema != config.profile.output_schema
            or manifest.logical.media_type != config.profile.output_media_type
            or manifest.logical.profile.name != config.profile.output_artifact_profile.name):
        raise PermissionError("Matrix source pipeline substitutes its exact original native output contract")
    # SourcePipeline.qualify checks the exact profile/media/access/size contract
    # and terminal manifest identity. Existing guarded verification dispatches to
    # its registered artifact/dataset codec, without parsing native bytes as JSON.
    writer.verify(config.execution_evidence.source_result.materialization)
    writer.verify_manifest(manifest)


def _authenticate_source_publication(writer, pin, publication, pipeline, *, require_current=None):
    if type(pin) is not ObjectIdentity or type(publication) is not ArtifactWriteResult:
        raise TypeError("Matrix source qualification requires original typed publication descriptors")
    authenticate_publication(writer, publication)
    if require_current is not None and require_current() is not None:
        raise PermissionError("source original permission guard must return None or raise")
    raw = read_bounded_bytes(writer.root.resolve(publication.materialization.relative_path, for_write=False),
        maximum_bytes=publication.materialization.size_bytes)
    if (len(raw) != publication.materialization.size_bytes or sha256(raw).hexdigest() != pin.object_fingerprint
            or (pin.object_schema, pin.object_fingerprint) != (publication.logical.payload_schema, publication.logical.content_sha256)):
        raise PermissionError("Matrix source qualification substitutes original scientific publication bytes")
    if require_current is not None and require_current() is not None:
        raise PermissionError("source original permission guard must return None or raise")
    if publication.logical.profile is ArtifactProfile.CANONICAL_JSON:
        document = json.loads(raw)
        if (type(document) is not dict or (document.get("schema"), document.get("version"))
                != (pin.object_schema, pin.object_version) or canonical_json_document_bytes(document) != raw):
            raise PermissionError("Matrix source qualification substitutes original canonical scientific metadata")
    else:
        manifest = pipeline.pipeline_config.execution_evidence.output_manifest
        if publication.logical != manifest.logical or publication.materialization != manifest.materialization:
            raise PermissionError("Matrix source qualification substitutes the original registered native dataset")
        # The independently issued gate pins its exact native operand/version;
        # its registered output codec and full source profile own native bytes.
        _authenticate_pipeline_output(writer, pipeline)
