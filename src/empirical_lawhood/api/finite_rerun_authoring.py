# SPDX-License-Identifier: MPL-2.0
"""Current P10 authoring over existing scientific builders and custody stores.

Compilation and provider proof never execute a task or create an authority.
Calibration parents are current authenticated publications, not the old
development-only parent-import route. Fixed nomination bytes remain provenance.
"""
from empirical_lawhood.storage.artifact_sidecars import read_artifact_sidecar

from collections import Counter
from dataclasses import dataclass, fields, replace
from datetime import UTC, datetime
from hashlib import sha256
import json
from pathlib import Path

from empirical_lawhood.domains.matrix.finite_response_law.authoring.consumer_input import build_consumer_authoring
from empirical_lawhood.adapters.composition.finite_response_law.consumer_ports import FiniteResponseLawRuntimeContext, load_control_runtime
from empirical_lawhood.domains.matrix.finite_response_law.authoring.exposure import native_seed_collisions, native_seed_ids
from empirical_lawhood.domains.matrix.finite_response_law.authoring.method_authoring import method_resource_envelope
from empirical_lawhood.domains.matrix.finite_response_law.authoring.resources import native_resource_envelope
from empirical_lawhood.domains.matrix.finite_response_law.authoring.rerun_input import FiniteResponseLawCurrentAllocation, FiniteResponseLawCurrentExposure, FiniteResponseLawCurrentParent, FiniteResponseLawCurrentPublication, FiniteResponseLawCurrentResultInput, FiniteResponseLawRerunInput, original_development_exposure, public_rerun_sample_exposure
from empirical_lawhood.domains.matrix.response_geometry_prospective.authoring.design import ResponseGeometryAssayCandidateContextProvider
from empirical_lawhood.domains.matrix.finite_response_law.assigned_native_records import FiniteResponseLawAssignedCalibrationNativeEvaluation, FiniteResponseLawAssignedEvaluationNativeCompletion
from empirical_lawhood.domains.matrix.finite_response_law.method_records import FiniteResponseLawAssignedQualificationReport
from empirical_lawhood.domains.matrix.finite_response_law.nominated_package import CurrentNominationOperand
from empirical_lawhood.api.authoring_handoff import create_authoring_api, preflight_authoring_output_directory, resolve_authoring_directory, write_exclusive_record
from empirical_lawhood.api.authoring_output import report_incomplete_output
from empirical_lawhood.api.finite_operands import current_nomination_operand_import
from empirical_lawhood.api.results import CompileCandidateRequest
from empirical_lawhood.storage.artifacts import ExternalArtifactPlane
from empirical_lawhood.storage.artifact_validation import ArtifactIdentityConflict
from empirical_lawhood.storage.bounded_io import BoundedFileIOError, file_matches_bytes, read_bounded_bytes
from empirical_lawhood.storage.canonical_record_read import read_verified_canonical_record
from empirical_lawhood.storage.candidate_payloads import ExternalCandidatePayloadPlane
from empirical_lawhood.storage.candidate_sources import ExternalContentAddressedInputResolver, ExternalCandidateInputPublisher
from empirical_lawhood.api.recursive_prospective_authoring import _capture_prospective_source, _publish_source_provenance
from empirical_lawhood.storage.study_issue import GitStudySourceClosureInspector
from empirical_lawhood.storage.source_closure import capture_clean_target_closure
from empirical_lawhood.api.authoring_handoff import authenticate_selected_authoring_source, require_authoring_source_kind_layout
from empirical_lawhood.storage.study_issue import ExternalIssuedStudyPublisher, ExternalStudyOperationAuthorityStore, PROGRAMME_EXECUTION_GRANTEE_ID, PROGRAMME_ISSUE_GRANTEE_ID, PROGRAMME_REVEAL_GRANTEE_ID
from empirical_lawhood.storage.task_receipts import ExternalTaskReceiptStore
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.identity.references import ArtifactIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.design.study_issue import SourceClosureKind, StudyAuthorityKind, require_study_authority
from empirical_lawhood.storage.contracts.artifacts import ArtifactLineageParent, ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.execution.compiler import compile_preissue_run_plan, lower_run_plan
from empirical_lawhood.execution.executable_bindings import ExecutablePlatformPort, LayeredCampaignRuntimeProviderResolver
from empirical_lawhood.execution.execution_envelope import ExecutionResourceEnvelopeSpec
from empirical_lawhood.execution.operator_profile import OperatorStorageProfile
from empirical_lawhood.execution.providers import CampaignRuntimeProviderRegistry
from empirical_lawhood.execution.plans import CandidateExecutionPlan, ExecutionPlan, RunPlan
from empirical_lawhood.execution.study_issue import project_standard_study_extensions

def _read_record(directory: Path, filename: str, record_type):
    limit = None
    return decode_canonical_bytes(read_bounded_bytes(directory / filename, maximum_bytes=limit), record_type, maximum_bytes=limit)


def _assert_expected_record(directory: Path, filename: str, expected: CanonicalRecord, refusal: str) -> None:
    # The current source/parent/compiler independently constructed and validated
    # expected. Exact canonical bytes preserve strict decode + equality without
    # constructing the same typed graph a second time. Each actual file remains
    # bounded, no-follow and stable, with no successful-read cache.
    try:
        matches = file_matches_bytes(directory / filename, expected.canonical_bytes(), maximum_bytes=None)
    except BoundedFileIOError as error:
        raise ValueError(refusal) from error
    if not matches:
        raise ValueError(refusal)


def _load_current_issued(publication, plane, *, expected_run=None, expected_candidate=None):
    """Replay the existing issue publication, with no historical/development alias."""
    from empirical_lawhood.execution.study_issue import IssuedExecutableStudyManifest
    store = ExternalStudyOperationAuthorityStore(plane)
    issued = ExternalIssuedStudyPublisher(artifact_plane=plane, authority_store=store, grantee_id=PROGRAMME_ISSUE_GRANTEE_ID).load_executable_study(publication.issued_study.object_id).manifest
    if type(issued) is not IssuedExecutableStudyManifest or ObjectIdentity.from_record(issued.issue_id, issued) != publication.issued_study or issued.base.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE:
        raise PermissionError('FINITE_CURRENT_ACTUAL_PROSPECTIVE_ISSUE_REQUIRED')
    run_id = publication.run_id
    if expected_run is not None and run_id != expected_run or expected_candidate is not None and ObjectIdentity.from_record(issued.candidate.candidate_id, issued.candidate) != expected_candidate:
        raise PermissionError('FINITE_CURRENT_ISSUED_CANDIDATE_OR_RUN_MISMATCH')
    return issued, run_id


def _authenticate_current_publication(publication, plane, *, expected_run=None, expected_candidate=None, include_controls=False):
    """Replay the actual current issue and both exact grants before outcome bytes."""
    issued, run_id = _load_current_issued(publication, plane, expected_run=expected_run, expected_candidate=expected_candidate)
    _require_current_grants(publication, plane)
    controls = _authenticate_current_run_controls(publication, issued, plane)
    return (issued, run_id, controls) if include_controls else (issued, run_id)


def _require_current_grants(publication, plane):
    store = ExternalStudyOperationAuthorityStore(plane)
    execution = store.load(publication.execution_authority.object_id)
    reveal = store.load(publication.reveal_authority.object_id)
    if ObjectIdentity.from_record(execution.authority_id, execution) != publication.execution_authority or ObjectIdentity.from_record(reveal.authority_id, reveal) != publication.reveal_authority:
        raise PermissionError('FINITE_CURRENT_PARENT_AUTHORITY_IDENTITY_MISMATCH')
    now = datetime.now(UTC).isoformat().replace('+00:00', 'Z')
    require_study_authority(execution, kind=StudyAuthorityKind.EXPERIMENT_EXECUTION, subject=publication.issued_study, prerequisite_authority=execution.prerequisite_authority, grantee_id=PROGRAMME_EXECUTION_GRANTEE_ID, at_utc=now)
    require_study_authority(reveal, kind=StudyAuthorityKind.OUTCOME_REVEAL, subject=publication.issued_study, prerequisite_authority=publication.execution_authority, grantee_id=PROGRAMME_REVEAL_GRANTEE_ID, at_utc=now)


def _published_current_control(plane, run_id, name, record_type, maximum_bytes):
    from empirical_lawhood.storage.contracts.artifacts import most_restrictive_outcome_access
    relative = f'runs/{run_id}/plans/{name}.json'
    try:
        manifest = plane.read_manifest(relative, maximum_bytes=plane.custody_limits.manifest_bytes)
    except ArtifactIdentityConflict as error:
        raise ValueError('FINITE_CURRENT_RUN_EXACT_PUBLISHED_CONTROL_REQUIRED') from error
    material, logical = manifest.materialization, manifest.logical
    parents = logical.lineage_parents
    if (manifest.publication is None or material.relative_path != relative
            or material.storage_root_id != plane.root.contract.storage_root_id
            or material.compression != 'none' or material.partition_selector is not None
            or (maximum_bytes is not None and material.size_bytes > maximum_bytes)
            or plane.custody_limits.exceeds('in_memory_payload_bytes', material.size_bytes)
            or logical.logical_artifact_id != f'{name}.{run_id}' or logical.payload_schema != record_type.SCHEMA
            or logical.profile is not ArtifactProfile.CANONICAL_JSON or logical.media_type != 'application/json'
            or manifest.publication.publication_scope.publication_scope_id != f'campaign-plans.{run_id}'
            or manifest.publication.publication_scope.relative_root != f'runs/{run_id}/plans'
            or not parents or logical.visibility_ceiling not in (VisibilityCeiling.PROSPECTIVE, VisibilityCeiling.OUTCOME_VISIBLE)
            or logical.visibility_ceiling is not VisibilityCeiling.most_restrictive(*(p.visibility_ceiling for p in parents))
            or logical.outcome_access is not most_restrictive_outcome_access(*(p.outcome_access for p in parents))):
        raise ValueError('FINITE_CURRENT_RUN_EXACT_PUBLISHED_CONTROL_REQUIRED')
    try:
        return read_verified_canonical_record(plane, manifest, record_type, maximum_bytes=material.size_bytes), parents
    except ArtifactIdentityConflict as error:
        raise ValueError('FINITE_CURRENT_RUN_CONTROL_BYTE_IDENTITY_MISMATCH') from error


def _authenticate_current_run_controls(publication, issued, plane):
    """Replay the current approved package and its exact scientific/runtime plans.

    Protected readout consumes actual published controls. Reconstruction reuses
    the scientific preissue compiler and the package's exact approved identities;
    it grants no authorization and does not replace approval-service execution.
    """
    from empirical_lawhood.api.models import ExperimentPackage
    from empirical_lawhood.api.execution import CampaignExecutionService
    package, package_parents = _published_current_control(plane, publication.run_id, 'campaign-package', ExperimentPackage, None)
    run, run_parents = _published_current_control(plane, publication.run_id, 'run-plan', RunPlan, None)
    execution, execution_parents = _published_current_control(plane, publication.run_id, 'execution-plan', ExecutionPlan, None)
    if package.issued_study != issued or package.run_plan_id != publication.run_id or ObjectIdentity.from_record(package.execution_authority.authority_id, package.execution_authority) != publication.execution_authority or execution.source_plan != ObjectIdentity.from_record(run.run_plan_id, run) or execution.execution_plan_id != package.execution_plan_id:
        raise ValueError('FINITE_CURRENT_RUN_ISSUED_PACKAGE_OR_PLAN_JOIN_MISMATCH')
    expected_controls = CampaignExecutionService._plan_control_records(package, run, execution)
    if (package_parents, run_parents, execution_parents) != tuple(parents for _, _, parents in expected_controls):
        raise ValueError('FINITE_CURRENT_RUN_CONTROL_LINEAGE_MISMATCH')
    candidate = issued.candidate
    projected = compile_preissue_run_plan(run_plan_id=publication.run_id, candidate_record=candidate.base_candidate.base_candidate, candidate=ObjectIdentity.from_record(candidate.candidate_id, candidate), registry=package.registry, implementation_commit=issued.source_closure.implementation_commit, issued_extension_set=issued.issued_extensions, resource_envelope=package.execution_resource_envelope_spec, jit_census=package.predevelopment_jit_signature_census, jit_manifest=package.jit_graph_signature_manifest, model_set=package.model_set)
    values = {item.name: getattr(projected, item.name) for item in fields(projected)}
    values.update(experiment=ObjectIdentity.from_record(package.experiment.experiment_id, package.experiment), authorization=ObjectIdentity.from_record(package.scientific_approval.authorization_id, package.scientific_approval))
    expected = RunPlan(**values, issued_extension_set=ObjectIdentity.from_record(issued.issued_extensions.issued_extension_set_id, issued.issued_extensions), execution_resource_envelope_spec=ObjectIdentity.from_record(package.execution_resource_envelope_spec.envelope_spec_id, package.execution_resource_envelope_spec), predevelopment_jit_signature_census=None if package.predevelopment_jit_signature_census is None else ObjectIdentity.from_record(package.predevelopment_jit_signature_census.census_id, package.predevelopment_jit_signature_census), jit_graph_signature_manifest=None if package.jit_graph_signature_manifest is None else ObjectIdentity.from_record(package.jit_graph_signature_manifest.manifest_id, package.jit_graph_signature_manifest))
    if run != expected or execution != lower_run_plan(expected, package.registry):
        raise ValueError('FINITE_CURRENT_RUN_EXACT_APPROVED_PROJECTION_REPLAY_MISMATCH')
    return package, run, execution


def _issued_member_bytes(plane, member):
    raw = read_bounded_bytes(plane.root.resolve(member.relative_path, for_write=False), maximum_bytes=member.size_bytes)
    if len(raw) != member.size_bytes or sha256(raw).hexdigest() != member.physical_sha256:
        raise ValueError('FINITE_CURRENT_ISSUED_SOURCE_MEMBER_BYTES_MISMATCH')
    return raw


def _require_issued_source(issued, source, plane, *, nomination=None, expected_config=None):
    from empirical_lawhood.domains.matrix.finite_response_law.control_records import FiniteResponseLawControlConfig
    from empirical_lawhood.domains.matrix.finite_response_law.method_records import FiniteResponseLawAssignedCalibrationMethodConfig
    from empirical_lawhood.domains.matrix.finite_response_law.completion.contracts import FiniteResponseLawAssignedCalibrationRetainedConfig
    candidates = []
    matched_config = expected_config is None
    for member in issued.members:
        if member.payload_schema == type(source).SCHEMA:
            candidates.append(decode_canonical_bytes(_issued_member_bytes(plane, member), type(source), maximum_bytes=None))
        elif member.payload_schema == FiniteResponseLawAssignedCalibrationRetainedConfig.SCHEMA:
            config = decode_canonical_bytes(_issued_member_bytes(plane, member), FiniteResponseLawAssignedCalibrationRetainedConfig, maximum_bytes=None)
            original = FiniteResponseLawCurrentPublication(config.retained_run_id, config.retained_study,
                config.retained_execution, config.retained_reveal)
            native_issue, _ = _load_current_issued(original, plane)
            _require_current_grants(original, plane)
            native_members = tuple(m for m in native_issue.members if m.payload_schema == type(source).SCHEMA)
            if (native_issue.source_closure.implementation_commit != config.retained_implementation_commit
                    or len(native_members) != 1 or _issued_member_bytes(plane, native_members[0]) != config.native_source.canonical_bytes()):
                raise ValueError('FINITE_RETAINED_CALIBRATION_ORIGINAL_SOURCE_MISMATCH')
            candidates.append(config.native_source)
        elif member.payload_schema == FiniteResponseLawAssignedCalibrationMethodConfig.SCHEMA:
            config = decode_canonical_bytes(_issued_member_bytes(plane, member), FiniteResponseLawAssignedCalibrationMethodConfig, maximum_bytes=None)
            candidates.append(config.native_source)
            if nomination is not None and (config.development_report, config.coefficients, config.development_manifest) != nomination.current_artifacts:
                raise ValueError('FINITE_CURRENT_PARENT_CHANGED_FIXED_NOMINATION')
        elif member.payload_schema == FiniteResponseLawControlConfig.SCHEMA:
            config = decode_canonical_bytes(_issued_member_bytes(plane, member), FiniteResponseLawControlConfig, maximum_bytes=None)
            candidates.append(config.source)
            matched_config = matched_config or config == expected_config
    if not candidates or any(candidate != source for candidate in candidates) or not matched_config:
        raise ValueError('FINITE_CURRENT_ISSUED_SOURCE_BINDING_REQUIRED')


def _exact_current_receipt(plane, issued, run_id, task_id, receipt_id):
    receipt = ExternalTaskReceiptStore(plane).read_by_receipt_id(run_id, task_id, receipt_id)
    steps = {step.step_id: step for step in issued.candidate.base_candidate.base_candidate.protocol.steps}
    if receipt is None or receipt.operational_status is not OperationalStatus.SUCCEEDED or receipt.run_id != run_id or receipt.task_id != task_id or receipt.receipt_id != receipt_id or receipt.implementation_commit != issued.source_closure.implementation_commit or task_id not in steps:
        raise ValueError('FINITE_CURRENT_PARENT_SUCCESSFUL_EXACT_ISSUED_RECEIPT_REQUIRED')
    step = steps[task_id]
    expected = {f'artifact.{run_id}.{task_id}.{output.output_id}': output for output in step.outputs}
    if {artifact.logical_artifact_id for artifact in receipt.output_logical_artifacts} != set(expected) or {value.logical_artifact_id for value in receipt.output_materializations} != set(expected):
        raise ValueError('FINITE_CURRENT_RECEIPT_COMPLETE_ISSUED_TASK_OUTPUTS_REQUIRED')
    physical = {value.logical_artifact_id: value for value in receipt.output_materializations}
    if sum(value.size_bytes for value in receipt.output_materializations) > step.resource_budget.output_bytes:
        raise ValueError('FINITE_CURRENT_RECEIPT_ISSUED_OUTPUT_BYTE_BUDGET_EXCEEDED')
    for logical in receipt.output_logical_artifacts:
        output = expected[logical.logical_artifact_id]
        materialization = physical[logical.logical_artifact_id]
        if (logical.payload_schema, logical.profile, logical.media_type) != (output.payload_schema, output.profile, output.media_type) or materialization.relative_path != f'runs/{run_id}/outputs/{task_id}/{output.output_id}{output.filename_suffix}' or materialization.size_bytes > step.resource_budget.output_bytes or materialization.compression != 'none' or materialization.partition_selector is not None:
            raise ValueError('FINITE_CURRENT_RECEIPT_ISSUED_OUTPUT_CONTRACT_MISMATCH')
    return receipt


def _verify_current_task_manifests(plane, manifests, published_tasks):
    """Verify complete receipted sibling batches using the independently authenticated producer."""
    typed_ids = {m.logical.logical_artifact_id for m in manifests if m.logical.semantic_validation is not None}
    if typed_ids and plane.accepts_issued_output_semantics():
        from empirical_lawhood.api.current_result_custody import retained_task_output_registrations
        from empirical_lawhood.execution.linked_campaigns import LinkedCampaignStageEnvelope
        from empirical_lawhood.domains.matrix.finite_response_law.assigned_native_records import FiniteResponseLawAssignedCalibrationViewObservation
        from empirical_lawhood.storage.contracts.artifacts import ArtifactSemanticValidationRegistry
        codecs = {kind.SCHEMA: kind for kind in (*_current_result_types().values(), LinkedCampaignStageEnvelope, FiniteResponseLawAssignedCalibrationViewObservation)}
        registrations = tuple(registration for package, task in published_tasks
            if any(output.logical_artifact_id in typed_ids for output in task.outputs)
            for registration in retained_task_output_registrations(package, task, codecs))
        plane = plane.with_semantic_validation_registry(ArtifactSemanticValidationRegistry.from_registrations(
            registry_id='finite-response-law.retained-result-semantics', registrations=registrations))
    plane.verify_manifests(manifests)


def authenticate_finite_current_parent(parent: FiniteResponseLawCurrentParent, plane: ExternalArtifactPlane, *, nomination=None) -> dict[str, bytes]:
    """Resolve actual grants before protected bytes, then replay full publication custody."""
    publications = {}
    primary_runs = {run for run, _, _ in parent.receipt_bindings} - {publication.run_id for publication in parent.additional_publications}
    if len(primary_runs) != 1:
        raise ValueError('FINITE_CURRENT_PARENT_ONE_PRIMARY_OPERATIVE_RUN_REQUIRED')
    primary = FiniteResponseLawCurrentPublication(next(iter(primary_runs)), parent.issued_study, parent.execution_authority, parent.reveal_authority)
    for publication in (primary, *parent.additional_publications):
        issued, run_id, (package, _, execution) = _authenticate_current_publication(publication, plane, expected_run=publication.run_id, include_controls=True)
        _require_issued_source(issued, parent.native_source, plane, nomination=nomination)
        if run_id in publications:
            raise ValueError('FINITE_CURRENT_PARENT_AMBIGUOUS_RUN_PUBLICATION')
        publications[run_id] = (issued, package, execution)
    if set(publications) != {run for run, _, _ in parent.receipt_bindings}:
        raise ValueError('FINITE_CURRENT_PARENT_COMPLETE_RUN_AUTHORITY_CENSUS_REQUIRED')
    original_units, original_seeds = original_development_exposure()
    sample_units, sample_seeds = public_rerun_sample_exposure()
    if {root.physical_unit_id for root in parent.native_source.roots} & set((*original_units, *sample_units)) or native_seed_collisions(native_seed_ids(parent.native_source), tuple(sorted(set((*original_seeds, *sample_seeds))))):
        raise ValueError('FINITE_CURRENT_PARENT_EXPOSED_NATIVE_ALLOCATION_CANNOT_QUALIFY')
    receipts, published_tasks = [], []
    for run_id, task_id, receipt_id in parent.receipt_bindings:
        issued, package, execution = publications[run_id]
        receipt = _exact_current_receipt(plane, issued, run_id, task_id, receipt_id)
        published_tasks.append((package, _require_receipt_execution_join(receipt, execution)))
        matching = tuple(m for m in parent.manifests if m.materialization in receipt.output_materializations)
        if {m.materialization for m in matching} != set(receipt.output_materializations) or {m.logical for m in matching} != set(receipt.output_logical_artifacts):
            raise ValueError('FINITE_CURRENT_PARENT_COMPLETE_RECEIPT_PUBLICATION_REQUIRED')
        receipts.append(receipt)
    if {m.materialization for m in parent.manifests} != {m for r in receipts for m in r.output_materializations}:
        raise ValueError('FINITE_CURRENT_PARENT_UNRECEIPTED_OUTPUT')
    # Verification reads protected physical operands. Exact successful receipts,
    # authorized task/output metadata and the full sibling census precede it.
    _verify_current_task_manifests(plane, parent.manifests, published_tasks)
    result = {}
    for manifest in parent.manifests:
        logical = manifest.logical
        path = plane.root.resolve(manifest.materialization.relative_path, for_write=False)
        if logical.logical_artifact_id in result or manifest.publication is None or manifest.materialization.compression != 'none' or manifest.materialization.partition_selector is not None:
            raise ValueError('FINITE_CURRENT_PARENT_EXACT_AUTHORIZED_MATERIALIZATION_REQUIRED')
        raw = read_bounded_bytes(path, maximum_bytes=manifest.materialization.size_bytes)
        if len(raw) != manifest.materialization.size_bytes or sha256(raw).hexdigest() != manifest.materialization.physical_sha256 or logical.content_sha256 != manifest.materialization.physical_sha256:
            raise ValueError('FINITE_CURRENT_PARENT_OPERAND_BYTE_IDENTITY_MISMATCH')
        result[logical.logical_artifact_id] = raw
    for receipt in receipts:
        result[receipt.receipt_id] = receipt.canonical_bytes()
    from empirical_lawhood.domains.matrix.finite_response_law.method_records import FiniteResponseLawAssignedCalibrationMethodConfig
    for issued, _, _ in publications.values():
        for member in issued.members:
            if member.payload_schema == FiniteResponseLawAssignedCalibrationMethodConfig.SCHEMA:
                raw = _issued_member_bytes(plane, member)
                method = decode_canonical_bytes(raw, FiniteResponseLawAssignedCalibrationMethodConfig, maximum_bytes=None)
                if method.config_id in result:
                    raise ValueError('FINITE_CURRENT_PARENT_AMBIGUOUS_ISSUED_METHOD_CONFIG')
                result[method.config_id] = raw
    return result


def _validate_parent(packet, parent, plane):
    if packet.stage == 'calibration':
        if parent is not None:
            raise ValueError('FINITE_RERUN_NATIVE_CALIBRATION_HAS_NO_PARENT')
        return {}
    if parent is None:
        raise ValueError('FINITE_RERUN_CURRENT_PUBLISHED_PARENT_REQUIRED')
    data = authenticate_finite_current_parent(parent, plane, nomination=packet.nomination)
    return _validate_parent_operands(packet, parent, data)


def _validate_parent_operands(packet, parent, data):
    """Join operands authenticated for this exact local parent and nomination."""
    selected = packet.method.inputs if packet.method is not None else packet.control.inputs
    fixed = set(packet.nomination.current_artifacts)
    for artifact in selected:
        if artifact in fixed:
            continue
        raw = data.get(artifact.artifact_id)
        if raw is None or len(raw) != artifact.size_bytes or sha256(raw).hexdigest() != artifact.sha256:
            raise ValueError('FINITE_RERUN_EXACT_CURRENT_PARENT_OPERAND_REQUIRED')
    primary = packet.method.native_evaluation if packet.method is not None else packet.control.qualification
    if primary.sha256 != packet.primary_parent_sha256:
        raise ValueError('FINITE_RERUN_PRIMARY_PARENT_MISMATCH')
    if packet.method is not None:
        from empirical_lawhood.domains.matrix.finite_response_law.calibration_operands import authenticated_evaluation
        from empirical_lawhood.storage.contracts.artifacts import CanonicalTaskReceipt
        native = authenticated_evaluation(data[primary.artifact_id], primary, decode_canonical_bytes(data[packet.method.native_receipt.artifact_id], CanonicalTaskReceipt, maximum_bytes=None), expected_receipt=packet.method.expected_native_receipt, source=packet.source)
        if native.config.projection.native_spec != packet.source or parent.native_source != packet.source:
            raise ValueError('FINITE_RERUN_CALIBRATION_NATIVE_SOURCE_MISMATCH')
    else:
        from empirical_lawhood.domains.matrix.finite_response_law.control_inputs import authenticated_control_inputs
        qualification, native = authenticated_control_inputs(packet.control, {artifact.artifact_id: data[artifact.artifact_id] for artifact in packet.control.inputs})
        if native.config.projection.native_spec != parent.native_source:
            raise ValueError('FINITE_RERUN_QUALIFICATION_NATIVE_CUSTODY_MISMATCH')
        from empirical_lawhood.domains.matrix.finite_response_law.method_records import FiniteResponseLawAssignedCalibrationMethodConfig
        raw = data.get(qualification.config.object_id)
        if raw is None:
            raise ValueError('FINITE_RERUN_QUALIFICATION_ISSUED_METHOD_CONFIG_REQUIRED')
        method = decode_canonical_bytes(raw, FiniteResponseLawAssignedCalibrationMethodConfig, maximum_bytes=None)
        if ObjectIdentity.from_record(method.config_id, method) != qualification.config or method.native_source != parent.native_source or method.native_evaluation != packet.control.calibration_native or method.native_receipt != packet.control.calibration_native_receipt or method.expected_native_receipt != packet.control.expected_calibration_native_receipt or (method.development_report, method.coefficients, method.development_manifest) != packet.nomination.current_artifacts:
            raise ValueError('FINITE_RERUN_QUALIFICATION_FIXED_NOMINATION_OR_ISSUED_SOURCE_MISMATCH')
        if set(root.physical_unit_id for root in parent.native_source.roots) & set(packet.allocation.physical_unit_ids) or native_seed_collisions(native_seed_ids(packet.source), native_seed_ids(parent.native_source)):
            raise ValueError('FINITE_RERUN_CALIBRATION_EVALUATION_ALLOCATION_COLLISION')
    return data


def _bundle(packet, exposure, implementation_sha256, completion=None, retention=None):
    original_units, original_seeds = original_development_exposure()
    if not set(original_units) <= set(exposure.excluded_unit_ids) or not set(original_seeds) <= set(exposure.excluded_seed_ids):
        raise ValueError('FINITE_RERUN_CURRENT_CENSUS_OMITS_ORIGINAL_DEVELOPMENT')
    if retention is not None:
        from empirical_lawhood.domains.matrix.finite_response_law.authoring.authoring import build_native_authoring
        if (not set(packet.original_prior_unit_ids) <= set(exposure.excluded_unit_ids)
                or not set(packet.original_prior_seed_ids) <= set(exposure.excluded_seed_ids)):
            raise ValueError("Locked evaluation requires the complete prior exposure")
        return build_native_authoring(source=packet.source, control=packet.control, retention=retention,
            original_design_exposure=(packet.original_prior_unit_ids, packet.original_prior_seed_ids),
            exposure=ObjectIdentity.from_record(exposure.census_id, exposure),
            exposed_unit_ids=exposure.excluded_unit_ids, exposed_seed_ids=exposure.excluded_seed_ids,
            new_seed_ids=(), implementation_sha256=implementation_sha256)
    if completion is not None:
        from empirical_lawhood.domains.matrix.finite_response_law.authoring.completion_authoring import build_completion_authoring
        if (packet.source != completion.native_source
                or not set((*packet.original_prior_unit_ids, *packet.allocation.physical_unit_ids)) <= set(exposure.excluded_unit_ids)
                or not set((*packet.original_prior_seed_ids, *native_seed_ids(packet.source))) <= set(exposure.excluded_seed_ids)):
            raise ValueError('FINITE_RETAINED_CALIBRATION_COMPLETE_CURRENT_EXPOSURE_REQUIRED')
        return build_completion_authoring(config=completion, implementation_sha256=implementation_sha256,
            exposure=ObjectIdentity.from_record(exposure.census_id, exposure),
            exposed_unit_ids=packet.original_prior_unit_ids, exposed_seed_ids=packet.original_prior_seed_ids)
    return build_consumer_authoring(packet, implementation_sha256=implementation_sha256,
        exposure=ObjectIdentity.from_record(exposure.census_id, exposure),
        current_units=exposure.excluded_unit_ids, current_seeds=exposure.excluded_seed_ids)


def _packet_run_names(packet: FiniteResponseLawRerunInput) -> tuple[str, ...]:
    suffix = packet.fingerprint()[:32]
    # Preserve previously issued names when they fit. Long native step IDs can use
    # the same 128-bit packet commitment without a descriptive prefix.
    return f"{packet.config_id}.run-{suffix}", f"finite.run-{suffix}", suffix


def _packet_run_id(packet: FiniteResponseLawRerunInput, steps=()) -> str:
    from empirical_lawhood.execution.recovery import task_receipt_relative_path
    from empirical_lawhood.science.records.serialization import validate_relative_locator

    for name in _packet_run_names(packet):
        try:
            for step in steps:
                attempt = f"{name}.{step.step_id}.attempt-{step.maximum_attempts:03d}"
                relative = task_receipt_relative_path(name, step.step_id, attempt)
                validate_relative_locator(f"{relative}.manifest.json")
        except ValueError:
            continue
        return name
    raise ValueError("Finite-response task receipt exceeds the portable path limit with the compact run name")


def _project_bundle(bundle, packet, closure, report, completion=None):
    candidate = report.candidate
    base = candidate.base_candidate.base_candidate
    extensions, _, _ = project_standard_study_extensions(candidate=candidate, extension_payload_bytes=tuple(record.canonical_bytes() for record in bundle.payloads), decoder_registrations=bundle.decoder_registrations, extension_materializations=report.extension_materializations)
    extension_identity = ObjectIdentity.from_record(extensions.issued_extension_set_id, extensions)
    if completion is None:
        resources = method_resource_envelope(base.protocol, extension_identity) if packet.method is not None else native_resource_envelope(bundle, base.protocol, extension_identity)
        run_id = _packet_run_id(packet, base.protocol.steps)
    else:
        resources = method_resource_envelope(base.protocol, extension_identity, prefix=completion.study_prefix,
            task_ids=(completion.freeze_task_id, completion.aggregate_task_id, completion.adjudicate_task_id))
        run_id = f'calibration-completion.{candidate.fingerprint()[:32]}'
    projected = compile_preissue_run_plan(run_plan_id=run_id, candidate_record=base, candidate=ObjectIdentity.from_record(candidate.candidate_id, candidate), registry=bundle.standard_context.base.registry, implementation_commit=closure.implementation_commit, issued_extension_set=extensions, resource_envelope=resources, jit_census=None, jit_manifest=None, model_set=None if packet.control is None else packet.control.primary_model_set)
    execution = lower_run_plan(projected, bundle.standard_context.base.registry)
    return candidate, resources, projected, execution


def author_finite_response_rerun(*, root: Path, packet: FiniteResponseLawRerunInput,
                               exposure: FiniteResponseLawCurrentExposure,
                               nomination_directory: Path, output_dir: Path,
                               artifact_writer: ExternalArtifactPlane,
                               parent: FiniteResponseLawCurrentParent | None = None,
                               retained_calibration: FiniteResponseLawCurrentPublication | None = None,
                               retained_evaluation: FiniteResponseLawCurrentPublication | None = None) -> dict[str, object]:
    """Compile the selected current act; source acquisition remains an issued later operation."""
    if retained_evaluation is not None and retained_evaluation.run_id in _packet_run_names(packet):
        packet = replace(packet, config_id=f"continued-{packet.fingerprint()[:16]}")
    output_dir = preflight_authoring_output_directory(directory=output_dir, repo_root=root,
        artifact_writer=artifact_writer, allow_existing_empty=True)
    captured = _capture_prospective_source(root, f'{packet.config_id}.source-closure', artifact_writer=artifact_writer)
    closure = captured.closure
    nomination = current_nomination_operand_import(nomination_directory / 'nomination.canonical.json', source_directory=nomination_directory)
    if nomination != packet.nomination:
        raise ValueError('FINITE_RERUN_AUTHENTICATED_FIXED_NOMINATION_MISMATCH')
    if packet.additional_parents:
        raise ValueError('FINITE_RERUN_CURRENT_PARENT_INVENTORY_REPLACES_DEVELOPMENT_IMPORT_LOCATORS')
    data = _validate_parent(packet, parent, artifact_writer)
    retention = None
    if retained_evaluation is not None:
        if retained_calibration is not None:
            raise ValueError("Select one original issued stage for continuation")
        from empirical_lawhood.api.finite_evaluation_continuation import retained_evaluation_operands
        retention = retained_evaluation_operands(packet, retained_evaluation, artifact_writer,
            publisher=ExternalCandidateInputPublisher(artifact_writer.root))
    completion = None
    if retained_calibration is not None:
        from empirical_lawhood.api.finite_calibration_completion import retained_calibration_operands
        completion, data = retained_calibration_operands(packet, retained_calibration, artifact_writer)
    if parent is not None:
        if not set(root.physical_unit_id for root in parent.native_source.roots) <= set(exposure.excluded_unit_ids) or not set(native_seed_ids(parent.native_source)) <= set(exposure.excluded_seed_ids):
            raise ValueError('FINITE_RERUN_CURRENT_CENSUS_OMITS_CALIBRATION_PARENT')
    bundle = _bundle(packet, exposure, closure.implementation_sha256, completion, retention)
    output_dir = preflight_authoring_output_directory(directory=output_dir, repo_root=root,
        artifact_writer=artifact_writer, allow_existing_empty=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    with report_incomplete_output(output_dir) as progress:
        save = lambda name, record: write_exclusive_record(output_dir, name, record)
        save('rerun-input.json', packet)
        save('exposure.json', exposure)
        if retained_calibration is not None:
            save('retained-calibration-publication.json', retained_calibration)
        if retained_evaluation is not None:
            save('retained-evaluation-publication.json', retained_evaluation)
        if parent is not None:
            save('current-parent.json', parent)
        # Bind the exact published nomination bytes into the existing current
        # content-addressed input store; historical manifests grant no authority.
        publisher = ExternalCandidateInputPublisher(artifact_writer.root)
        for filename, artifact in zip(('development-report.json', 'coefficients.transport.json', 'development-manifest.json'), nomination.current_artifacts, strict=True):
            raw = read_bounded_bytes(nomination_directory / filename, maximum_bytes=artifact.size_bytes)
            publisher.publish(raw, maximum_bytes=artifact.size_bytes)
        for raw in data.values():
            publisher.publish(raw, maximum_bytes=None)
        author = save('authoring.json', bundle.authoring)
        save('base-authoring.json', bundle.authoring.base)
        payloads = tuple(save(f'payload-{index:02d}.json', record) for index, record in enumerate(bundle.payloads))
        decoders = tuple(save(f'decoder-{index:02d}.json', record) for index, record in enumerate(bundle.decoder_registrations))
        progress.stage = 'candidate compilation'
        api = create_authoring_api(repo_root=root, candidate_context_provider=ResponseGeometryAssayCandidateContextProvider(bundle), candidate_capability_catalog=bundle.catalog)
        result = api.compile_candidate(CompileCandidateRequest(author, payloads, decoders))
        if not result.succeeded or result.payload is None or result.payload.report.candidate is None:
            raise RuntimeError(f'FINITE_RERUN_CANDIDATE_REFUSED: {result.reason_codes}; {result.errors}')
        report = result.payload.report
        candidate, resources, projected, lowered = _project_bundle(bundle, packet, closure, report, completion)
        run_id = projected.run_plan_id
        for name, record in (('candidate-report.json', report), ('candidate.json', candidate), ('base-candidate.json', candidate.base_candidate), ('source-closure.json', closure), ('resources.json', resources), ('preissue-run-plan.json', projected), ('preissue-execution-plan.json', lowered)):
            save(name, record)
        _publish_source_provenance(captured=captured, destination=output_dir, artifact_writer=artifact_writer)
        GitStudySourceClosureInspector(Path(root)).observe(closure)
    return {'stage': packet.stage if completion is None else 'calibration-completion', 'candidate_sha256': candidate.fingerprint(), 'run_id': run_id,
            'independent_units': packet.allocation.root_count, 'task_count': len(lowered.tasks),
            'output_count': sum(len(task.outputs) for task in lowered.tasks), 'authoring_dir': str(output_dir),
            'scientific_execution_performed': False, 'authority_created': False}


@dataclass(frozen=True)
class _UnissuedRuntime:
    """Proof-only missing-authority port: every effect/read explicitly refuses."""
    def __getattr__(self, name):
        def refuse(*args, **kwargs):
            raise PermissionError('FINITE_RERUN_PUBLISHED_RUNTIME_AUTHORITY_REQUIRED')
        return refuse


@dataclass(frozen=True)
class _CurrentCandidatePort:
    plane: ExternalArtifactPlane
    run_id: str
    parent: ArtifactLineageParent
    visibility: VisibilityCeiling

    def __reduce__(self):
        from empirical_lawhood.storage.candidate_payloads import candidate_worker_plane_factory

        return (_restore_current_candidate_port,
            (candidate_worker_plane_factory(self.plane), self.run_id, self.parent, self.visibility))

    def publish_candidate_payload(self, **kwargs):
        return ExternalCandidatePayloadPlane(self.plane, f'runs/{self.run_id}/candidate-models', f'{self.run_id}.candidate-models', self.visibility, OutcomeAccess.EVALUATION_SEALED, (self.parent,), self.plane.root.contract.minimum_free_bytes).publish_candidate_payload(**kwargs)

    def read_candidate_payload(self, receipt):
        path = self.plane.root.resolve(receipt.authoritative_relative_locator + '.manifest.json', for_write=False)
        manifest = read_artifact_sidecar(self.plane, (path).relative_to(self.plane.root.contract.canonical_path).as_posix(), maximum_bytes=None)
        self.plane.verify_manifest(manifest)
        if manifest.publication is None or ObjectIdentity.from_record(manifest.publication.publication_batch_id, manifest.publication) != receipt.publication_receipt or manifest.logical.content_sha256 != receipt.content_sha256 or ObjectIdentity.from_record(manifest.materialization.materialization_id, manifest.materialization) != receipt.recovery_identity:
            raise ValueError('FINITE_RERUN_CANDIDATE_PUBLICATION_RECEIPT_MISMATCH')
        return ExternalCandidatePayloadPlane(self.plane, 'runs', f'{self.run_id}.candidate-models', self.visibility, OutcomeAccess.EVALUATION_SEALED, (), self.plane.root.contract.minimum_free_bytes).read_candidate_payload(receipt)


def _restore_current_candidate_port(make_plane, run_id, parent, visibility):
    return _CurrentCandidatePort(make_plane(), run_id, parent, visibility)


@dataclass(frozen=True, slots=True)
class FiniteResponseLawApplicationHandoff:
    directory: Path
    packet: FiniteResponseLawRerunInput
    bundle: object
    projection: object
    resources: ExecutionResourceEnvelopeSpec
    platform_ports: tuple[ExecutablePlatformPort, ...]
    runtime_authority_bound: bool


def _require_runtime_packet(context, packet):
    if packet.control is None or packet.evidence_role != 'PROPOSED_UNRUN' or context.source_sha256 != packet.source.fingerprint() or context.run_id not in _packet_run_names(packet):
        raise ValueError('FINITE_RERUN_RUNTIME_PROPOSED_SOURCE_OR_RUN_MISMATCH')


def _authenticate_runtime_context(context, packet, projection, plane):
    _require_runtime_packet(context, packet)
    if context.run_id != projection.source_plan.object_id:
        raise ValueError('FINITE_RERUN_RUNTIME_PROPOSED_SOURCE_OR_RUN_MISMATCH')
    issued, _ = _load_current_issued(context, plane, expected_run=context.run_id, expected_candidate=projection.candidate)
    _require_issued_source(issued, packet.source, plane, expected_config=packet.control)
    store = ExternalStudyOperationAuthorityStore(plane)
    authority = store.load(context.authority.object_id)
    if ObjectIdentity.from_record(authority.authority_id, authority) != context.authority or context.grantee_id != PROGRAMME_EXECUTION_GRANTEE_ID:
        raise PermissionError('FINITE_RERUN_RUNTIME_AUTHORITY_IDENTITY_OR_GRANTEE_MISMATCH')
    now = datetime.now(UTC).isoformat().replace('+00:00', 'Z')
    require_study_authority(authority, kind=StudyAuthorityKind.EXPERIMENT_EXECUTION, subject=context.issued_study, prerequisite_authority=context.prerequisite_authority, grantee_id=PROGRAMME_EXECUTION_GRANTEE_ID, at_utc=now)
    if context.reveal_authority_id is not None:
        reveal = store.load(context.reveal_authority_id)
        require_study_authority(reveal, kind=StudyAuthorityKind.OUTCOME_REVEAL, subject=context.issued_study, prerequisite_authority=context.authority, grantee_id=PROGRAMME_REVEAL_GRANTEE_ID, at_utc=now)


def load_finite_response_rerun_handoff(*, directory: Path, root: Path, storage_profile: OperatorStorageProfile, artifact_writer: ExternalArtifactPlane) -> FiniteResponseLawApplicationHandoff:
    directory, _ = resolve_authoring_directory(directory, repo_root=root, storage_profile=storage_profile, escape_message='Finite rerun handoff is outside selected guarded storage')
    packet = _read_record(directory, 'rerun-input.json', FiniteResponseLawRerunInput)
    exposure = _read_record(directory, 'exposure.json', FiniteResponseLawCurrentExposure)
    from empirical_lawhood.design.study_issue import ImplementationSourceClosure
    closure = _read_record(directory, 'source-closure.json', ImplementationSourceClosure)
    require_authoring_source_kind_layout(directory=directory, closure=closure)
    if closure.kind is SourceClosureKind.CLEAN_GIT_COMMIT:
        observed = capture_clean_target_closure(root, closure.source_closure_id)
        if observed != closure:
            raise ValueError('FINITE_RERUN_ACTUAL_SOURCE_CLOSURE_CHANGED')
    else:
        authenticate_selected_authoring_source(directory=directory, project_root=root,
            artifact_writer=artifact_writer, closure=closure)
    parent = None if packet.stage == 'calibration' else _read_record(directory, 'current-parent.json', FiniteResponseLawCurrentParent)
    _validate_parent(packet, parent, artifact_writer)
    retention = None
    if (directory / 'retained-evaluation-publication.json').exists():
        if (directory / 'retained-calibration-publication.json').exists():
            raise ValueError("Conflicting retained stages in finite-response handoff")
        from empirical_lawhood.api.finite_evaluation_continuation import retained_evaluation_operands
        original = _read_record(directory, 'retained-evaluation-publication.json', FiniteResponseLawCurrentPublication)
        retention = retained_evaluation_operands(packet, original, artifact_writer)
    completion = None
    if (directory / 'retained-calibration-publication.json').exists():
        from empirical_lawhood.api.finite_calibration_completion import retained_calibration_operands
        original = _read_record(directory, 'retained-calibration-publication.json', FiniteResponseLawCurrentPublication)
        completion, _ = retained_calibration_operands(packet, original, artifact_writer)
    if parent is not None and (not {root.physical_unit_id for root in parent.native_source.roots} <= set(exposure.excluded_unit_ids) or not set(native_seed_ids(parent.native_source)) <= set(exposure.excluded_seed_ids)):
        raise ValueError('FINITE_RERUN_CURRENT_CENSUS_OMITS_CALIBRATION_PARENT')
    bundle = _bundle(packet, exposure, closure.implementation_sha256, completion, retention)
    _assert_expected_record(directory, 'authoring.json', bundle.authoring, 'FINITE_RERUN_RETAINED_AUTHORING_RECONSTRUCTION_MISMATCH')
    for filename, record in (('base-authoring.json', bundle.authoring.base), *((f'payload-{index:02d}.json', record) for index, record in enumerate(bundle.payloads)), *((f'decoder-{index:02d}.json', record) for index, record in enumerate(bundle.decoder_registrations))):
        _assert_expected_record(directory, filename, record, 'FINITE_RERUN_RETAINED_INPUT_OR_DECODER_CHANGED')
    api = create_authoring_api(repo_root=root, candidate_context_provider=ResponseGeometryAssayCandidateContextProvider(bundle), candidate_capability_catalog=bundle.catalog)
    result = api.compile_candidate(CompileCandidateRequest(directory / 'authoring.json', tuple(directory / f'payload-{index:02d}.json' for index in range(len(bundle.payloads))), tuple(directory / f'decoder-{index:02d}.json' for index in range(len(bundle.decoder_registrations)))))
    if not result.succeeded or result.payload is None or result.payload.report.candidate is None:
        raise ValueError('FINITE_RERUN_CURRENT_CANDIDATE_RECOMPILATION_REFUSED')
    report = result.payload.report
    candidate, resources, projected, projection = _project_bundle(bundle, packet, closure, report, completion)
    for filename, record in (('candidate-report.json', report), ('candidate.json', candidate), ('base-candidate.json', candidate.base_candidate), ('resources.json', resources), ('preissue-run-plan.json', projected), ('preissue-execution-plan.json', projection)):
        _assert_expected_record(directory, filename, record, 'FINITE_RERUN_EXACT_CURRENT_PROJECTION_RECONSTRUCTION_MISMATCH')
    from empirical_lawhood.domains.matrix.finite_response_law.method_provider import CANDIDATE_PAYLOAD_PORT, INPUT_RESOLVER_PORT
    ports = {
        CANDIDATE_PAYLOAD_PORT: _CurrentCandidatePort(artifact_writer, projection.source_plan.object_id, ArtifactLineageParent(ObjectIdentity.from_record(bundle.authoring.package_id, bundle.authoring), VisibilityCeiling.PROSPECTIVE if packet.evidence_role == 'PROPOSED_UNRUN' else VisibilityCeiling.DEVELOPMENT_ONLY, OutcomeAccess.OUTCOME_BLIND), VisibilityCeiling.PROSPECTIVE if packet.evidence_role == 'PROPOSED_UNRUN' else VisibilityCeiling.DEVELOPMENT_ONLY),
        INPUT_RESOLVER_PORT: ExternalContentAddressedInputResolver(artifact_writer.root),
    }
    bound = False
    if packet.control is not None:
        from empirical_lawhood.domains.matrix.finite_response_law.control_ports import CONTROL_RUNTIME_PORT, REVEAL_CONTROL_PORT, SEALED_CONTROL_PORT, SOURCE_CONTROL_PORT
        runtime = _UnissuedRuntime()
        if retention is not None:
            from empirical_lawhood.adapters.simulators.finite_response_law.evaluation_continuation.extension import IMPORT_RESOLVER_PORT, LOCK_IMPORT_CONTROL_PORT
            ports[IMPORT_RESOLVER_PORT] = ports[INPUT_RESOLVER_PORT]
        if (directory / 'runtime-context-reference.json').exists():
            identity = _read_record(directory, 'runtime-context-reference.json', ObjectIdentity)
            runtime = load_control_runtime(artifact_writer, identity, packet.source.fingerprint())
            context = _read_record(artifact_writer.root.resolve('operator/finite-response-law-contexts', for_write=False), f'{identity.object_id}.json', FiniteResponseLawRuntimeContext)
            _authenticate_runtime_context(context, packet, projection, artifact_writer)
            if retention is not None:
                from empirical_lawhood.domains.matrix.finite_response_law.runtime_ports import retain_evaluation_runtime
                runtime = retain_evaluation_runtime(runtime, retention)
            bound = True
        if retention is not None:
            ports[LOCK_IMPORT_CONTROL_PORT] = runtime
        ports.update({key: runtime for key in (CONTROL_RUNTIME_PORT, REVEAL_CONTROL_PORT, SEALED_CONTROL_PORT, SOURCE_CONTROL_PORT)})
    from empirical_lawhood.adapters.composition.generated_executable_bindings import EXECUTABLE_CAPABILITY_PROVIDER_FACTORY_REGISTRY
    selected = {(manifest.capability_key, manifest.capability_version) for manifest in bundle.standard_context.base.registry.capabilities}
    required_ports = {key for binding in EXECUTABLE_CAPABILITY_PROVIDER_FACTORY_REGISTRY.aggregate.bindings if (binding.capability_key, binding.capability_version) in selected for key in binding.required_platform_port_keys}
    if not required_ports <= ports.keys():
        raise ValueError('FINITE_RERUN_REQUIRED_PLATFORM_PORT_UNAVAILABLE')
    return FiniteResponseLawApplicationHandoff(directory, packet, bundle, projection, resources, tuple(ExecutablePlatformPort(key, ports[key]) for key in sorted(required_ports)), bound)


def prove_finite_response_rerun_handoff(handoff: FiniteResponseLawApplicationHandoff) -> dict[str, object]:
    from empirical_lawhood.adapters.composition.generated_executable_bindings import EXECUTABLE_CAPABILITY_PROVIDER_FACTORY_REGISTRY
    from empirical_lawhood.api.integration_proof import prove_provider_projection
    bundle = handoff.bundle
    registry = bundle.standard_context.base.registry
    resolver = LayeredCampaignRuntimeProviderResolver(precomposed=CampaignRuntimeProviderRegistry(()), factories=EXECUTABLE_CAPABILITY_PROVIDER_FACTORY_REGISTRY)
    provider = resolver.resolve(registry, decoded_records=tuple(sorted(bundle.payloads, key=lambda value: value.SCHEMA)), platform_ports=handoff.platform_ports)
    proof = prove_provider_projection(provider=provider, registry=registry, projection=handoff.projection,
        resources=handoff.resources, proof_id=f'{handoff.packet.config_id}.proof')
    from empirical_lawhood.domains.matrix.finite_response_law.completion.contracts import FiniteResponseLawAssignedCalibrationRetainedConfig
    stage = 'calibration-completion' if any(type(p) is FiniteResponseLawAssignedCalibrationRetainedConfig for p in bundle.payloads) else handoff.packet.stage
    return {'stage': stage, 'independent_units': handoff.packet.allocation.root_count,
        **proof, 'runtime_authority_bound': handoff.runtime_authority_bound}


def bind_finite_response_runtime(*, directory: Path, context: FiniteResponseLawRuntimeContext, artifact_writer: ExternalArtifactPlane) -> ObjectIdentity:
    """Publish an operator-supplied binding only after authentic current authority checks."""
    packet = _read_record(directory, 'rerun-input.json', FiniteResponseLawRerunInput)
    _require_runtime_packet(context, packet)
    projection = _read_record(directory, 'preissue-execution-plan.json', CandidateExecutionPlan)
    _authenticate_runtime_context(context, packet, projection, artifact_writer)
    identity = ObjectIdentity.from_record(context.context_id, context)
    relative = f'operator/finite-response-law-contexts/{context.context_id}.json'
    artifact_writer.write(ArtifactWriteRequest(logical_artifact_id=context.context_id, relative_path=relative, payload_schema=context.SCHEMA, profile=ArtifactProfile.CANONICAL_JSON, media_type='application/vnd.empirical-lawhood.canonical+json', publication_scope_id='operator.finite-response-law-contexts', publication_scope_relative_root='operator/finite-response-law-contexts', payload=context.canonical_bytes(), visibility_ceiling=VisibilityCeiling.PROSPECTIVE, parent_visibility_ceilings=(), outcome_access=OutcomeAccess.OUTCOME_BLIND, logical_content_sha256=context.fingerprint(), lineage_parents=(), minimum_free_bytes=artifact_writer.root.contract.minimum_free_bytes))
    load_control_runtime(artifact_writer, identity, packet.source.fingerprint())
    write_exclusive_record(directory, 'runtime-context-reference.json', identity)
    return identity


def read_finite_response_current_result(*, config: FiniteResponseLawCurrentResultInput, artifact_writer: ExternalArtifactPlane) -> CanonicalRecord:
    """Read one explicitly selected scientific result after actual authorized reveal.

    The complete successful task receipt and all sibling output manifests remain
    compulsory. This is a bounded reader, not qualification or execution.
    """
    from empirical_lawhood.execution.adjudication import ScientificAdjudicationRecord
    by_schema = {record.SCHEMA: record for record in _current_result_types().values()}
    selected = next(manifest for manifest in config.manifests if manifest.logical.logical_artifact_id == config.result_artifact_id)
    record_type = by_schema.get(selected.logical.payload_schema)
    if record_type is None:
        raise ValueError('FINITE_CURRENT_RESULT_UNSUPPORTED_SCIENTIFIC_SCHEMA')
    run_id, task_id, receipt_id = config.receipt_binding
    issued, _, (package, _, execution) = _authenticate_current_publication(config.publication, artifact_writer, expected_run=run_id, include_controls=True)
    receipt = _exact_current_receipt(artifact_writer, issued, run_id, task_id, receipt_id)
    task = _require_receipt_execution_join(receipt, execution)
    if set(receipt.output_materializations) != {manifest.materialization for manifest in config.manifests} or set(receipt.output_logical_artifacts) != {manifest.logical for manifest in config.manifests} or any(manifest.publication is None for manifest in config.manifests):
        raise ValueError('FINITE_CURRENT_RESULT_COMPLETE_RECEIPT_PUBLICATION_REQUIRED')
    _verify_current_task_manifests(artifact_writer, config.manifests, ((package, task),))
    raw = read_bounded_bytes(artifact_writer.root.resolve(selected.materialization.relative_path, for_write=False), maximum_bytes=selected.materialization.size_bytes)
    if len(raw) != selected.materialization.size_bytes or sha256(raw).hexdigest() != selected.materialization.physical_sha256 or selected.logical.content_sha256 != selected.materialization.physical_sha256:
        raise ValueError('FINITE_CURRENT_RESULT_BYTE_IDENTITY_MISMATCH')
    record = decode_canonical_bytes(raw, record_type, maximum_bytes=None)
    _require_current_result_binding(record, issued, task_id, artifact_writer)
    if isinstance(record, ScientificAdjudicationRecord):
        if record.run_id != run_id or record.adjudication_task_id != task_id or record.execution_plan != ObjectIdentity.from_record(execution.execution_plan_id, execution) or record.input_materialization_ids != receipt.input_materialization_ids or record.output_logical_artifact_ids != tuple(value.logical_artifact_id for value in receipt.output_logical_artifacts):
            raise ValueError('FINITE_CURRENT_RESULT_ADJUDICATION_RUN_PLAN_OR_CENSUS_MISMATCH')
        from empirical_lawhood.execution.adjudication import ScientificAdjudicationContext
        output = next(value for value in task.outputs if value.logical_artifact_id == selected.logical.logical_artifact_id)
        context = ScientificAdjudicationContext(ObjectIdentity.from_record(execution.execution_plan_id, execution), package.system.world.world_id, package.system.world.kind, ObjectIdentity.from_record(package.experiment.relation.relation_id, package.experiment.relation), package.experiment.independent_unit_id, tuple(ObjectIdentity.from_record(cutoff.cutoff_id, cutoff) for cutoff in package.experiment.information_cutoffs), output.visibility_ceiling, output.outcome_access)
        if not record.matches_context(context):
            raise ValueError('FINITE_CURRENT_RESULT_ACTUAL_TERMINAL_SCIENTIFIC_CONTEXT_MISMATCH')
        matched = set()
        for dependency in task.dependency_task_ids:
            candidates = tuple(value for value in record.required_receipt_ids if value.startswith(f'receipt.{run_id}.{dependency}.'))
            if len(candidates) != 1:
                raise ValueError('FINITE_CURRENT_RESULT_COMPLETE_TERMINAL_DEPENDENCY_RECEIPTS_REQUIRED')
            dependent = _exact_current_receipt(artifact_writer, issued, run_id, dependency, candidates[0])
            _require_receipt_execution_join(dependent, execution)
            matched.add(candidates[0])
        if matched != set(record.required_receipt_ids):
            raise ValueError('FINITE_CURRENT_RESULT_UNDECLARED_TERMINAL_DEPENDENCY_RECEIPT')
    _require_current_grants(config.publication, artifact_writer)
    return record


def _require_receipt_execution_join(receipt, execution):
    tasks = tuple(task for task in execution.tasks if task.task_id == receipt.task_id)
    if len(tasks) != 1 or receipt.run_id != execution.source_plan.object_id or receipt.implementation_commit != execution.implementation_commit:
        raise ValueError('FINITE_CURRENT_RECEIPT_ACTUAL_EXECUTION_PLAN_TASK_MISMATCH')
    task = tasks[0]
    expected = {output.logical_artifact_id: output for output in task.outputs}
    if set(expected) != {value.logical_artifact_id for value in receipt.output_logical_artifacts}:
        raise ValueError('FINITE_CURRENT_RECEIPT_ACTUAL_EXECUTION_OUTPUT_CENSUS_MISMATCH')
    physical = {value.logical_artifact_id: value for value in receipt.output_materializations}
    for logical in receipt.output_logical_artifacts:
        output = expected[logical.logical_artifact_id]
        if (logical.payload_schema, logical.profile, logical.media_type, logical.visibility_ceiling, logical.outcome_access, physical[logical.logical_artifact_id].relative_path) != (output.payload_schema, output.profile, output.media_type, output.visibility_ceiling, output.outcome_access, output.relative_path):
            raise ValueError('FINITE_CURRENT_RECEIPT_ACTUAL_EXECUTION_OUTPUT_CONTRACT_MISMATCH')
    return task


def _require_current_result_binding(record, issued, task_id, plane):
    """Bind decoded scientific content to the selected issued source and task."""
    from empirical_lawhood.domains.matrix.finite_response_law.control_closeout import FiniteResponseLawRootSealedControl
    from empirical_lawhood.domains.matrix.finite_response_law.control_records import FiniteResponseLawControlConfig
    from empirical_lawhood.domains.matrix.finite_response_law.control_reveal import FiniteResponseLawProspectiveRootEvaluation
    from empirical_lawhood.domains.matrix.finite_response_law.evaluation_readout import FiniteResponseLawRootInferenceOperands
    from empirical_lawhood.domains.matrix.finite_response_law.evaluation_results import FiniteResponseLawEvaluationCohort, FiniteResponseLawEvaluationRevealConfig
    from empirical_lawhood.domains.matrix.finite_response_law.method_records import FiniteResponseLawAssignedCalibrationMethodConfig
    from empirical_lawhood.domains.matrix.finite_response_law.assigned_contracts import FiniteResponseLawAssignedEvaluationConfig
    if type(record) in (FiniteResponseLawAssignedCalibrationNativeEvaluation, FiniteResponseLawAssignedEvaluationNativeCompletion):
        _require_issued_source(issued, record.config.projection.native_spec, plane)
        return
    if type(record) is FiniteResponseLawAssignedQualificationReport:
        methods = tuple(decode_canonical_bytes(_issued_member_bytes(plane, member), FiniteResponseLawAssignedCalibrationMethodConfig, maximum_bytes=None) for member in issued.members if member.payload_schema == FiniteResponseLawAssignedCalibrationMethodConfig.SCHEMA)
        if len(methods) != 1 or record.config != ObjectIdentity.from_record(methods[0].config_id, methods[0]):
            raise ValueError('FINITE_CURRENT_RESULT_ISSUED_QUALIFICATION_CONFIG_MISMATCH')
        return
    if type(record) not in (FiniteResponseLawRootSealedControl, FiniteResponseLawProspectiveRootEvaluation, FiniteResponseLawRootInferenceOperands, FiniteResponseLawEvaluationCohort):
        return
    controls = tuple(decode_canonical_bytes(_issued_member_bytes(plane, member), FiniteResponseLawControlConfig, maximum_bytes=None) for member in issued.members if member.payload_schema == FiniteResponseLawControlConfig.SCHEMA)
    if len(controls) != 1:
        raise ValueError('FINITE_CURRENT_RESULT_ONE_ISSUED_CONTROL_CONFIG_REQUIRED')
    control = controls[0]
    if type(control.source) is not FiniteResponseLawAssignedEvaluationConfig:
        raise ValueError('FINITE_CURRENT_RESULT_CURRENT_ASSIGNED_CONTROL_SOURCE_REQUIRED')
    roots = {root.stage_unit: root for root in control.source.roots}
    if type(record) is FiniteResponseLawRootSealedControl:
        forecast = record.join.lock.forecast
        if forecast.root.stage_unit not in roots or roots[forecast.root.stage_unit] != forecast.root or forecast.config != ObjectIdentity.from_record(control.config_id, control) or task_id != f'{forecast.root.stage_unit}.seal-control':
            raise ValueError('FINITE_CURRENT_RESULT_ISSUED_CLOSEOUT_ROOT_MISMATCH')
    elif type(record) is FiniteResponseLawProspectiveRootEvaluation:
        root_ids = {unit.root_id for unit in record.units}
        if len(root_ids) != 1 or not root_ids <= roots.keys() or task_id != f'{next(iter(root_ids))}.evaluate-use' or record.sealed.object_id != f'{next(iter(root_ids))}.sealed-control':
            raise ValueError('FINITE_CURRENT_RESULT_ISSUED_REVEAL_ROOT_MISMATCH')
    elif type(record) is FiniteResponseLawRootInferenceOperands:
        bootstrap = next(seed for purpose, index, seed in control.source.scientific_seeds if (purpose, index) == ('bootstrap', -1))
        if record.root_id not in roots or task_id != f'{record.root_id}.evaluate-use' or record.bootstrap_seed != bootstrap:
            raise ValueError('FINITE_CURRENT_RESULT_ISSUED_INFERENCE_ROOT_MISMATCH')
    else:
        reveal = FiniteResponseLawEvaluationRevealConfig(control)
        if record.config != ObjectIdentity.from_record(reveal.config_id, reveal) or record.qualification.object_fingerprint != control.qualification.sha256 or {operand.root_id for operand in record.operands} != roots.keys():
            raise ValueError('FINITE_CURRENT_RESULT_ISSUED_COHORT_CONFIG_MISMATCH')


def _current_result_types():
    from empirical_lawhood.domains.matrix.finite_response_law.control_closeout import FiniteResponseLawRootSealedControl
    from empirical_lawhood.domains.matrix.finite_response_law.control_reveal import FiniteResponseLawProspectiveRootEvaluation
    from empirical_lawhood.domains.matrix.finite_response_law.evaluation_readout import FiniteResponseLawRootInferenceOperands
    from empirical_lawhood.domains.matrix.finite_response_law.evaluation_results import FiniteResponseLawEvaluationCohort
    from empirical_lawhood.execution.adjudication import ScientificAdjudicationRecord
    return {
        'calibration-native': FiniteResponseLawAssignedCalibrationNativeEvaluation,
        'evaluation-native': FiniteResponseLawAssignedEvaluationNativeCompletion,
        'qualification': FiniteResponseLawAssignedQualificationReport,
        'closeout': FiniteResponseLawRootSealedControl,
        'root-reveal': FiniteResponseLawProspectiveRootEvaluation,
        'root-inference': FiniteResponseLawRootInferenceOperands,
        'cohort': FiniteResponseLawEvaluationCohort,
        'terminal': ScientificAdjudicationRecord,
    }


def finite_response_current_result_summary(*, config: FiniteResponseLawCurrentResultInput,
                                          record: CanonicalRecord) -> dict[str, object]:
    """Present an already authenticated result without embedding native arrays.

    This display helper creates no authority. Call the protected result reader
    first; the selected publication remains the complete scientific record.
    """
    kinds = {record_type: kind for kind, record_type in _current_result_types().items()}
    kind = kinds.get(type(record))
    if kind is None:
        raise ValueError('FINITE_CURRENT_RESULT_UNSUPPORTED_SCIENTIFIC_SCHEMA')
    selected = next(manifest for manifest in config.manifests if manifest.logical.logical_artifact_id == config.result_artifact_id)
    if record.SCHEMA != selected.logical.payload_schema or record.fingerprint() != selected.logical.content_sha256:
        raise ValueError('FINITE_CURRENT_RESULT_SUMMARY_PUBLICATION_MISMATCH')
    run_id, task_id, receipt_id = config.receipt_binding
    result = {'result_kind': kind, 'payload_schema': record.SCHEMA,
        'payload_sha256': selected.logical.content_sha256,
        'result_reference': {'result_input_id': config.config_id, 'run_id': run_id, 'task_id': task_id,
            'receipt_id': receipt_id, 'logical_artifact_id': config.result_artifact_id,
            'relative_path': selected.materialization.relative_path,
            'physical_sha256': selected.materialization.physical_sha256,
            'size_bytes': selected.materialization.size_bytes,
            'visibility_ceiling': selected.logical.visibility_ceiling.value,
            'outcome_access': selected.logical.outcome_access.value}}
    if kind in ('calibration-native', 'evaluation-native'):
        source = record.config.projection.native_spec
        counts = Counter(status for view in record.views for _, _, status in view.accounting)
        result.update(claim='declared native completion', scientific_status=record.scientific_status.value,
            reason_codes=record.reasons, independent_roots=len(source.roots),
            root_ids=tuple(root.stage_unit for root in source.roots), nested_numerical_views=len(record.views),
            assigned_native_cells=sum(len(view.accounting) for view in record.views),
            completed_native_updates=record.completed_native_updates,
            native_cell_dispositions={status: counts[status] for status in ('COMPLETE', 'NUMERICAL_FAILURE',
                'OBSERVATION_FAILURE', 'PREFIX_UNAVAILABLE', 'PORT_FRAME_UNRESOLVED', 'HANDOFF_UNAVAILABLE')},
            views=tuple({'root_id': view.root.stage_unit, 'refinement': view.refinement,
                'assigned_native_cells': len(view.accounting),
                'completed_native_updates': sum(updates for _, updates, _ in view.accounting),
                'cell_dispositions': dict(sorted(Counter(status for _, _, status in view.accounting).items())),
                'reason_codes': view.reasons} for view in record.views))
    elif kind == 'qualification':
        boundaries = record.calibration.boundaries
        result.update(independent_roots=len(boundaries[0].root_ids), root_ids=boundaries[0].root_ids,
            eligible_for_prospective_evaluation=record.eligible_for_prospective_evaluation,
            joint_opportunities=dict(record.calibration.joint_opportunities),
            boundaries=tuple({'boundary': boundary.boundary, 'assigned_root_count': len(boundary.root_ids),
                'finite_score_count': sum(score is not None for score in boundary.scores),
                'infinite_score_count': sum(score is None for score in boundary.scores),
                'order_index': boundary.order_index, 'q': None if boundary.q is None else {'decimal': str(boundary.q)},
                'score_reason_counts': dict(sorted(Counter(reason for reasons in boundary.score_reasons for reason in reasons).items())),
                'scientific_status': qualification.scientific_status.value,
                'qualification': ObjectIdentity.from_record(qualification.result_id, qualification).to_document()}
                for boundary, qualification in zip(boundaries, record.qualifications, strict=True)))
    elif kind == 'closeout':
        root = record.join.lock.forecast.root.stage_unit
        result.update(custody_state='SEALED_CLOSEOUT', independent_roots=1, root_ids=(root,),
            nested_numerical_views=len(record.views), assigned_consumer_count=len(record.bundles),
            consumer_censuses=tuple(bundle.census.to_document() for bundle in record.bundles),
            future_dispositions=dict(sorted(Counter(locator.disposition.value for bundle in record.bundles for locator in bundle.locators).items())))
    elif kind == 'root-reveal':
        result.update(independent_roots=len({unit.root_id for unit in record.units}),
            root_ids=tuple(sorted({unit.root_id for unit in record.units})),
            assigned_consumer_count=len(record.units), units=tuple(unit.to_document() for unit in record.units))
    elif kind == 'root-inference':
        # One root's closed scalar readout is small; retain every consumer and
        # boundary, including unavailable losses and numerical disagreement.
        result.update(independent_roots=1, root_ids=(record.root_id,), operands=record.to_document())
    elif kind == 'cohort':
        result.update(scientific_status=record.scientific_status.value, reason_codes=record.reasons,
            independent_roots=len(record.operands), root_ids=tuple(operand.root_id for operand in record.operands),
            assigned_consumer_count=len(record.generic.units),
            censuses=tuple(census.to_document() for census in record.generic.censuses),
            statistics=json.loads(record.statistics_json))
    else:
        result.update(evaluability=record.evaluability.value, scientific_status=record.scientific_status.value,
            admission_status=record.admission_status.value, reason_codes=record.reason_codes,
            independent_unit_id=record.independent_unit_id, execution_plan=record.execution_plan.to_document(),
            required_receipt_count=len(record.required_receipt_ids),
            input_materialization_count=len(record.input_materialization_ids),
            output_artifact_count=len(record.output_logical_artifact_ids))
    return result


def prepare_finite_response_allocation(*, stage: str, cohort_namespace: str,
                                      master_seed: int,
                                      evidence_role: str = 'PROPOSED_UNRUN') -> FiniteResponseLawCurrentAllocation:
    """Expand a declared numeric input to the fixed 32/64-root purpose census.

    The returned allocation is a proposal. Namespace, numeric novelty and role
    establish neither independence from prior exposure nor scientific authority.
    """
    from empirical_lawhood.domains.matrix.finite_response_law.authoring.assignment import proposed_scientific_seeds
    from empirical_lawhood.domains.matrix.finite_response_law.science import FiniteResponseLawScienceSpec
    return FiniteResponseLawCurrentAllocation(stage, cohort_namespace, FiniteResponseLawScienceSpec().plan_sha256, 32 if stage == 'calibration' else 64, evidence_role, proposed_scientific_seeds(stage, master_seed))


def current_publication_from_ids(run_id: str, issued_study_id: str, execution_authority_id: str,
                                 reveal_authority_id: str, *, artifact_writer: ExternalArtifactPlane
                                 ) -> FiniteResponseLawCurrentPublication:
    """Resolve a run selector from stored grant identities. Its consumer authenticates the issue and current access."""
    store = ExternalStudyOperationAuthorityStore(artifact_writer)
    execution, reveal = store.load(execution_authority_id), store.load(reveal_authority_id)
    execution_identity = ObjectIdentity.from_record(execution.authority_id, execution)
    if (execution.kind is not StudyAuthorityKind.EXPERIMENT_EXECUTION or reveal.kind is not StudyAuthorityKind.OUTCOME_REVEAL
            or execution.subject.object_id != issued_study_id or reveal.subject != execution.subject
            or reveal.prerequisite_authority != execution_identity):
        raise PermissionError('FINITE_CURRENT_PARENT_AUTHORITY_IDENTITY_MISMATCH')
    return FiniteResponseLawCurrentPublication(run_id, execution.subject, execution_identity,
        ObjectIdentity.from_record(reveal.authority_id, reveal))


def current_result_input_from_receipt(*, config_id: str, run_id: str,
                                    issued_study_id: str, execution_authority_id: str,
                                    reveal_authority_id: str, task_id: str,
                                    receipt_id: str, result_kind: str,
                                    artifact_writer: ExternalArtifactPlane) -> FiniteResponseLawCurrentResultInput:
    """Select an actual receipted result without manually supplying byte identities."""
    record_type = _current_result_types().get(result_kind)
    if record_type is None:
        raise ValueError('FINITE_CURRENT_RESULT_UNSUPPORTED_KIND')
    publication = current_publication_from_ids(run_id, issued_study_id, execution_authority_id,
        reveal_authority_id, artifact_writer=artifact_writer)
    issued, _ = _authenticate_current_publication(publication, artifact_writer, expected_run=run_id)
    receipt = _exact_current_receipt(artifact_writer, issued, run_id, task_id, receipt_id)
    manifests = tuple(sorted((read_artifact_sidecar(artifact_writer, (artifact_writer.root.resolve(value.relative_path + '.manifest.json', for_write=False)).relative_to(artifact_writer.root.contract.canonical_path).as_posix(), maximum_bytes=None) for value in receipt.output_materializations), key=lambda value: value.materialization.materialization_id))
    selected = tuple(value for value in manifests if value.logical.payload_schema == record_type.SCHEMA)
    if len(selected) != 1:
        raise ValueError('FINITE_CURRENT_RESULT_ONE_EXACT_KIND_REQUIRED')
    config = FiniteResponseLawCurrentResultInput(config_id, publication, manifests, (run_id, task_id, receipt_id), selected[0].logical.logical_artifact_id)
    read_finite_response_current_result(config=config, artifact_writer=artifact_writer)
    return config


def current_parent_from_results(*, parent_id: str,
                                native_result: FiniteResponseLawCurrentResultInput,
                                artifact_writer: ExternalArtifactPlane,
                                qualification_result: FiniteResponseLawCurrentResultInput | None = None) -> FiniteResponseLawCurrentParent:
    """Join authenticated current native and optional qualification publications."""
    native = read_finite_response_current_result(config=native_result, artifact_writer=artifact_writer)
    if type(native) is not FiniteResponseLawAssignedCalibrationNativeEvaluation:
        raise ValueError('FINITE_CURRENT_PARENT_NATIVE_RESULT_REQUIRED')
    results = (native_result,)
    if qualification_result is not None:
        qualification = read_finite_response_current_result(config=qualification_result, artifact_writer=artifact_writer)
        receipt = ExternalTaskReceiptStore(artifact_writer).read_by_receipt_id(*native_result.receipt_binding)
        if type(qualification) is not FiniteResponseLawAssignedQualificationReport or any(boundary.native_evaluation != ObjectIdentity.from_record(native.evaluation_id, native) or boundary.native_task_receipt != ObjectIdentity.from_record(receipt.receipt_id, receipt) for boundary in qualification.calibration.boundaries):
            raise ValueError('FINITE_CURRENT_PARENT_QUALIFICATION_NATIVE_JOIN_MISMATCH')
        results += (qualification_result,)
    manifests = {manifest.materialization.materialization_id: manifest for result in results for manifest in result.manifests}
    if len(manifests) != sum(len(result.manifests) for result in results):
        raise ValueError('FINITE_CURRENT_PARENT_DUPLICATE_OUTPUT_PUBLICATION')
    primary = native_result.publication
    additional = tuple(sorted({result.publication for result in results if result.publication != primary}, key=lambda value: value.issued_study.object_id))
    parent = FiniteResponseLawCurrentParent(parent_id, primary.issued_study, primary.execution_authority, primary.reveal_authority, native.config.projection.native_spec, tuple(manifests[key] for key in sorted(manifests)), tuple(sorted(result.receipt_binding for result in results)), additional_publications=additional)
    authenticate_finite_current_parent(parent, artifact_writer)
    return parent


def _parent_operand(parent, data, record_type, role):
    matches = tuple(value for value in parent.manifests if value.logical.payload_schema == record_type.SCHEMA)
    if len(matches) != 1:
        raise ValueError('FINITE_RERUN_ONE_EXACT_PARENT_OPERAND_REQUIRED')
    manifest = matches[0]
    raw = data[manifest.logical.logical_artifact_id]
    artifact = ArtifactIdentity(manifest.logical.logical_artifact_id, role, record_type.SCHEMA, sha256(raw).hexdigest(), manifest.logical.media_type, len(raw))
    from empirical_lawhood.storage.contracts.artifacts import CanonicalTaskReceipt
    receipts = tuple(decode_canonical_bytes(data[receipt_id], CanonicalTaskReceipt, maximum_bytes=None) for _, _, receipt_id in parent.receipt_bindings)
    matching = tuple(receipt for receipt in receipts if manifest.materialization in receipt.output_materializations)
    if len(matching) != 1:
        raise ValueError('FINITE_RERUN_ONE_EXACT_PARENT_RECEIPT_REQUIRED')
    receipt = matching[0]
    receipt_artifact = ArtifactIdentity(receipt.receipt_id, role, receipt.SCHEMA, receipt.fingerprint(), 'application/json', len(receipt.canonical_bytes()))
    return artifact, receipt_artifact, ObjectIdentity.from_record(receipt.receipt_id, receipt), decode_canonical_bytes(raw, record_type, maximum_bytes=None)


def prepare_finite_response_rerun(*, config_id: str, stage: str, allocation: FiniteResponseLawCurrentAllocation,
                                exposure: FiniteResponseLawCurrentExposure,
                                nomination: CurrentNominationOperand, nomination_directory: Path,
                                artifact_writer: ExternalArtifactPlane,
                                parent: FiniteResponseLawCurrentParent | None = None) -> FiniteResponseLawRerunInput:
    """Construct an editable current packet from authenticated scientific operands.

    This retains actual exposure and unchanged nomination. It creates no grant,
    qualification, eligibility or source completion.
    """
    actual = current_nomination_operand_import(nomination_directory / 'nomination.canonical.json', source_directory=nomination_directory)
    if actual != nomination:
        raise ValueError('FINITE_RERUN_AUTHENTICATED_FIXED_NOMINATION_MISMATCH')
    units, seeds = exposure.excluded_unit_ids, exposure.excluded_seed_ids
    method = control = None
    primary_sha = None
    if stage == 'calibration':
        if parent is not None:
            raise ValueError('FINITE_RERUN_NATIVE_CALIBRATION_HAS_NO_PARENT')
    elif stage in ('calibration-method', 'prospective-evaluation'):
        if parent is None:
            raise ValueError('FINITE_RERUN_CURRENT_PUBLISHED_PARENT_REQUIRED')
        data = authenticate_finite_current_parent(parent, artifact_writer, nomination=nomination)
        parent_units = {root.physical_unit_id for root in parent.native_source.roots}
        parent_seeds = set(native_seed_ids(parent.native_source))
        if not parent_units <= set(units) or not parent_seeds <= set(seeds):
            raise ValueError('FINITE_RERUN_CURRENT_CENSUS_OMITS_CALIBRATION_PARENT')
        native_artifact, native_receipt, expected_native, _ = _parent_operand(parent, data, FiniteResponseLawAssignedCalibrationNativeEvaluation, 'current-calibration-native')
        if stage == 'calibration-method':
            from empirical_lawhood.domains.matrix.finite_response_law.method_records import FiniteResponseLawAssignedCalibrationMethodConfig
            method = FiniteResponseLawAssignedCalibrationMethodConfig('finite-response-law.calibration.method-config', parent.native_source, native_artifact, native_receipt, expected_native, *nomination.current_artifacts)
            primary_sha = native_artifact.sha256
            # The nonacquiring method act replays its original pre-calibration
            # exclusion cut while the explicit current census retains the parent.
            units = tuple(sorted(set(units) - parent_units))
            seeds = tuple(sorted(set(seeds) - parent_seeds))
        else:
            from empirical_lawhood.domains.matrix.finite_response_law.authoring.design import qualification_system
            from empirical_lawhood.domains.matrix.finite_response_law.control_plan import qualified_model_set
            from empirical_lawhood.domains.matrix.finite_response_law.control_records import FiniteResponseLawControlConfig
            from empirical_lawhood.domains.matrix.finite_response_law.assigned_contracts import FiniteResponseLawAssignedEvaluationConfig
            from empirical_lawhood.adapters.simulators.finite_response_law.evaluation.discovery import SOURCE_CAPABILITY
            qualification, qualification_receipt, expected_qualification, report = _parent_operand(parent, data, FiniteResponseLawAssignedQualificationReport, 'current-calibration-qualification')
            if not report.eligible_for_prospective_evaluation:
                raise ValueError('FINITE_RERUN_GENUINE_PRIMARY_QUALIFICATION_REQUIRED')
            source = FiniteResponseLawAssignedEvaluationConfig('prospective-evaluation', parent.native_source.science, ObjectIdentity.from_record(SOURCE_CAPABILITY.capability_key, SOURCE_CAPABILITY), None, (), allocation.cohort_namespace, allocation.fingerprint(), allocation.scientific_seeds)
            models = qualified_model_set(report=report, boundary='composed', world_id=qualification_system(parent.native_source).world.world_id)
            control = FiniteResponseLawControlConfig(source, qualification, qualification_receipt, expected_qualification, native_artifact, native_receipt, expected_native, models)
            primary_sha = qualification.sha256
    packet = FiniteResponseLawRerunInput(config_id, stage, allocation, nomination, units, seeds, primary_sha, method, control)
    # Parent and fixed nomination were authenticated together above in this
    # same call. Retain every selected operand/source/allocation join, without
    # replaying their entire published package and plans twice.
    if parent is not None:
        _validate_parent_operands(packet, parent, data)
    if stage != 'calibration-method' and packet.evidence_role == 'PROPOSED_UNRUN' and (set(allocation.physical_unit_ids) & set(exposure.excluded_unit_ids) or native_seed_collisions(native_seed_ids(packet.source), exposure.excluded_seed_ids)):
        raise ValueError('FINITE_RERUN_PROPOSED_ALLOCATION_ALREADY_EXPOSED')
    return packet
