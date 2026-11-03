# SPDX-License-Identifier: MPL-2.0
"""Actual guarded Matrix source identity transform under the existing dataset grant.

This owner writes no numerical observations and mints no task/issue receipt.
Its verification record records the actual committed-byte comparison performed
here and is replayed before the finite-dt scientific source gates are accepted.
"""
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import PurePosixPath

from empirical_lawhood.adapters.methods.matrix_finite_dt_source_pipeline import (
    MatrixFiniteDtPendingSourceRows, MatrixFiniteDtSourceValidationRule, MatrixFiniteDtSourceVerification,
)
from empirical_lawhood.adapters.methods.matrix_prepared_source_pipeline import (
    MatrixPreparedPendingSourceRows, MatrixPreparedSourceValidationRule, MatrixPreparedSourceVerification,
)
from empirical_lawhood.adapters.methods.matrix_finite_dt_source_records import BLIND, PROSPECTIVE
from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import authenticate_publication
from empirical_lawhood.adapters.methods.matrix_source_evidence import MatrixSourcePipelineConfig
from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.kernel.authority import AuthorityAction
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import validate_relative_locator, validate_stable_id
from empirical_lawhood.planning.dataset_authority import replay_dataset_operation_authorization
from empirical_lawhood.planning.source_pipelines import SourcePipelineArtifactProfile, SourcePipelineEdgeAccounting
from empirical_lawhood.runtime.artifacts import ArtifactLineageParent, ArtifactProfile, ArtifactWriteRequest, ArtifactWriteResult
from empirical_lawhood.runtime.source_pipelines import (SourcePipelineExecutionEvidence, SourcePipelineValidatorEvidence,
    compile_source_pipeline, plan_source_pipeline_resume)
from empirical_lawhood.runtime.sources import SourceResult, validate_source_result


@dataclass(frozen=True, slots=True)
class MatrixFiniteDtSourceMaterialization:
    config: MatrixSourcePipelineConfig
    rows: MatrixFiniteDtPendingSourceRows | MatrixPreparedPendingSourceRows
    source_publication: ArtifactWriteResult
    output_publication: ArtifactWriteResult
    verification: MatrixFiniteDtSourceVerification | MatrixPreparedSourceVerification
    verification_publication: ArtifactWriteResult


@dataclass(frozen=True, slots=True)
class MatrixFiniteDtDatasetClock:
    """Actual application clock, never a request-supplied timestamp."""
    clock_id: str

    def __post_init__(self):
        validate_stable_id(self.clock_id)

    def now_utc(self):
        return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _read_rows(writer, publication, rows):
    authenticate_publication(writer, publication, rows)
    if (publication.logical.profile is not ArtifactProfile.CANONICAL_JSON
            or publication.logical.outcome_access is not BLIND
            or publication.logical.visibility_ceiling is not PROSPECTIVE
            or publication.logical.media_type != "application/json"):
        raise PermissionError("finite-dt pending source metadata substitutes raw numerical/evaluation evidence")
    raw = read_bounded_bytes(writer.root.resolve(publication.materialization.relative_path, for_write=False),
        maximum_bytes=publication.materialization.size_bytes)
    if (len(raw) != publication.materialization.size_bytes or raw != rows.canonical_bytes()
            or decode_canonical_bytes(raw, type(rows), maximum_bytes=len(raw)) != rows):
        raise PermissionError("finite-dt source changes its exact complete typed pending-source bytes")
    manifest = writer.read_manifest(publication.materialization.relative_path)
    writer.verify_manifest(manifest)
    return raw, manifest


def _require_profile(profile, rows, rule, source, *, writer):
    if (profile.source_schema != rows.SCHEMA or profile.output_schema != rows.SCHEMA
            or profile.source_media_type != "application/json" or profile.output_media_type != "application/json"
            or profile.output_artifact_profile is not SourcePipelineArtifactProfile.CANONICAL_JSON
            or profile.output_filename_suffix != ".json"
            or profile.output_relative_locator == profile.source_relative_locator
            or profile.source_config != rule.identity
            or profile.outcome_access is not BLIND or profile.visibility_ceiling is not PROSPECTIVE
            or profile.operator_storage_root_id != writer.root.contract.storage_root_id
            or profile.source_relative_locator != source.materialization.relative_path
            or profile.expected_source_sha256 != rows.fingerprint()
            or profile.expected_source_size_bytes != len(rows.canonical_bytes())
            or profile.source_materialization != ObjectIdentity.from_record(source.materialization.materialization_id, source.materialization)
            or len(profile.transform_edges) != 1 or profile.semantic_validators != (rule.identity,)
            or profile.transform_edges[0].semantic_validator != rule.identity
            or profile.transform_edges[0].config != rule.identity
            or profile.maximum_row_count != len(rows.rows)
            or profile.maximum_physical_unit_count != len({value.group_id for value in rows.rows})):
        raise PermissionError("finite-dt source profile changes its one actual complete identity transform")
    edge, = profile.transform_edges
    if (edge.input_coordinates != edge.output_coordinates or edge.domain_schema != rows.SCHEMA
            or edge.codomain_schema != rows.SCHEMA or not edge.physical_unit_roster_preserved
            or not edge.invalid_rows_retained or any(getattr(edge, field).value != "PRESERVED"
                for field in ("native_unit_semantics", "frame_semantics", "clock_semantics", "row_semantics"))):
        raise PermissionError("finite-dt source profile changes native coordinates, pending states or whole-unit semantics")


def materialize_finite_dt_source(*, writer, programme, bank, rows, rule, source_publication,
        profile, source_manifest, capability_registry, dataset_registry, dataset_operation_request,
        policy, authorization, issuer_registration, decision_clock, verification_relative_path, record_id):
    """Run the sole implemented identity transform after genuine dataset authorization.

    Profiles, resource bounds, clock, issuer and exact storage scopes are actual
    caller selections. No signer, authority registration or budget is invented.
    """
    validate_stable_id(record_id)
    validate_relative_locator(verification_relative_path)
    if type(decision_clock) is not MatrixFiniteDtDatasetClock:
        raise PermissionError("finite-dt source requires its actual application decision clock")
    control = dataset_operation_request.control_write_scope
    if (control.storage_root.object_id != writer.root.contract.storage_root_id
            or not (verification_relative_path == control.relative_prefix
                or verification_relative_path.startswith(control.relative_prefix + "/"))):
        raise PermissionError("finite-dt source verification lies outside the actual granted control scope")
    from empirical_lawhood.api.matrix_finite_dt_dataset_metadata import select_rows_owner
    rows_owner = select_rows_owner(type(rows))
    rows_owner.validate_source_rows(programme, bank, rows, rule)
    _require_profile(profile, rows, rule, source_publication, writer=writer)
    if (source_manifest != rows_owner.source_capability(profile.resource_ceiling)
            or capability_registry.resolve(profile.transform_edges[0].selection.capability_key,
                profile.transform_edges[0].selection.capability_version) != rows_owner.transform_capability(profile.transform_edges[0].resource_budget)):
        raise PermissionError("finite-dt source substitutes its actual implemented source/identity-transform owners")
    compilation = compile_source_pipeline(profile, source_manifest=source_manifest,
        capability_registry=capability_registry, dataset_registry=dataset_registry,
        dataset_operation_request=dataset_operation_request)
    replay_dataset_operation_authorization(policy=policy, request=dataset_operation_request,
        authorization=authorization, issuer_registration=issuer_registration,
        manifest=profile.dataset_transformation_manifest, required_action=AuthorityAction.DATASET_TRANSFORMATION,
        implementation_commit=dataset_operation_request.implementation_commit, clock=decision_clock)
    # Resolve selected paths and recheck actual authority before publication.
    writer.root.resolve(profile.output_relative_locator, for_write=True)
    writer.root.resolve(verification_relative_path, for_write=True)
    from empirical_lawhood.api.matrix_finite_dt_dataset_metadata import (
        authenticate_dataset_contract, inspect_pending_source)
    authenticate_dataset_contract(writer=writer, profile=profile, registry=dataset_registry,
        capabilities=capability_registry, request=dataset_operation_request, rows=rows, rule=rule,
        source_publication=source_publication)
    raw, source_sidecar = inspect_pending_source(writer=writer, programme=programme, bank=bank,
        rows=rows, rule=rule, publication=source_publication, registration=dataset_registry.inspectors[0])
    source = SourceResult(compilation.source_request.request_id, profile.source_id, rows.SCHEMA,
        source_publication.materialization, sha256(raw).hexdigest(), len(raw), "verified")
    validate_source_result(source_manifest, compilation.source_request, source)
    parent = ArtifactLineageParent(ObjectIdentity.from_record(source_sidecar.logical.logical_artifact_id, source_sidecar), PROSPECTIVE, BLIND)
    relative_root = str(PurePosixPath(profile.output_relative_locator).parent)
    output_request = ArtifactWriteRequest("source-output." + record_id, profile.output_relative_locator,
        rows.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", "source-output." + record_id,
        relative_root, raw, PROSPECTIVE, (PROSPECTIVE,), BLIND, lineage_parents=(parent,))
    writer.preflight_write(output_request)
    output = writer.write(output_request)
    observed, output_sidecar = _read_rows(writer, output, rows)
    if observed != raw:
        raise PermissionError("finite-dt identity transform changed canonical source bytes")
    verification_kind = (MatrixFiniteDtSourceVerification if type(rows) is MatrixFiniteDtPendingSourceRows
        else MatrixPreparedSourceVerification)
    verification = verification_kind("verification." + record_id, rule.identity,
        ObjectIdentity.from_record(source_sidecar.logical.logical_artifact_id, source_sidecar),
        ObjectIdentity.from_record(output_sidecar.logical.logical_artifact_id, output_sidecar), rows.identity,
        len(rows.rows), len(programme.group_ids))
    verification_publication = writer.write(ArtifactWriteRequest(verification.record_id, verification_relative_path,
        verification.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", verification.record_id,
        str(PurePosixPath(verification_relative_path).parent), verification.canonical_bytes(), PROSPECTIVE, (), BLIND))
    edge, = profile.transform_edges
    roster = sha256(("\n".join(programme.group_ids) + "\n").encode()).hexdigest()
    accounting = SourcePipelineEdgeAccounting(edge.edge_id, profile.source_materialization, verification.output_manifest,
        len(rows.rows), len(rows.rows), 0, 0, len(programme.group_ids), roster, roster, 0,
        edge.input_coordinates, edge.output_coordinates)
    evidence = SourcePipelineExecutionEvidence("execution." + record_id, policy, authorization, issuer_registration,
        source, (accounting,), output_sidecar,
        (SourcePipelineValidatorEvidence(rule.identity, verification.identity, True),), verification.identity)
    config = MatrixSourcePipelineConfig("config." + record_id, profile, source_manifest, capability_registry,
        dataset_registry, dataset_operation_request, evidence, decision_clock.clock_id, decision_clock.now_utc())
    # Existing independent owners replay the complete grant, registered schema,
    # transform, row accounting, actual atomic publication and recovery contract.
    receipt = config.assess()
    plan_source_pipeline_resume(profile, receipt, output_sidecar, artifact_writer=writer, catalog_projection_current=True)
    return MatrixFiniteDtSourceMaterialization(config, rows, source_publication, output, verification, verification_publication)


def authenticate_finite_dt_source_materialization(*, writer, programme, bank, rows, rule, pipeline,
        source_publication, output_publication, verification, verification_publication):
    """Replay actual source/validator/recovery facts without writes or re-acquisition."""
    from empirical_lawhood.api.matrix_finite_dt_dataset_metadata import select_rows_owner
    rows_owner = select_rows_owner(type(rows))
    rows_owner.validate_source_rows(programme, bank, rows, rule)
    config, receipt = pipeline.pipeline_config, pipeline.receipt
    _require_profile(config.profile, rows, rule, source_publication, writer=writer)
    from empirical_lawhood.api.matrix_finite_dt_dataset_metadata import (
        authenticate_dataset_contract, inspect_pending_source)
    authenticate_dataset_contract(writer=writer, profile=config.profile, registry=config.dataset_registry,
        capabilities=config.capability_registry, request=config.dataset_operation_request, rows=rows, rule=rule,
        source_publication=source_publication)
    before, source = inspect_pending_source(writer=writer, programme=programme, bank=bank,
        rows=rows, rule=rule, publication=source_publication, registration=config.dataset_registry.inspectors[0])
    after, output = _read_rows(writer, output_publication, rows)
    verification_kind = (MatrixFiniteDtSourceVerification if type(rows) is MatrixFiniteDtPendingSourceRows
        else MatrixPreparedSourceVerification)
    expected = verification_kind(verification.record_id, rule.identity,
        ObjectIdentity.from_record(source.logical.logical_artifact_id, source),
        ObjectIdentity.from_record(output.logical.logical_artifact_id, output), rows.identity,
        len(rows.rows), len(programme.group_ids))
    if (config.source_manifest != rows_owner.source_capability(config.profile.resource_ceiling)
            or config.capability_registry.resolve(config.profile.transform_edges[0].selection.capability_key,
                config.profile.transform_edges[0].selection.capability_version) != rows_owner.transform_capability(config.profile.transform_edges[0].resource_budget)
            or before != after or verification != expected or config.execution_evidence.output_manifest != output
            or config.execution_evidence.recovery != verification.identity
            or config.execution_evidence.validator_evidence !=
                (SourcePipelineValidatorEvidence(rule.identity, verification.identity, True),)
            or config.execution_evidence.source_result.materialization != source.materialization
            or config.assess() != receipt):
        raise PermissionError("finite-dt source substitutes actual transform, verification or complete native-source accounting")
    authenticate_publication(writer, verification_publication, verification)
    plan_source_pipeline_resume(config.profile, receipt, output, artifact_writer=writer, catalog_projection_current=True)


def publish_finite_dt_source_metadata(*, writer, scope, materialization, output_directory):
    """Publish only otherwise-nested expectation metadata, once and atomically.

    Task configurations and the large shared bank/operands already have actual
    provider-input publications and are not copied again by this helper.
    These expectation/publication descriptors create no scientific receipt.
    """
    from pathlib import Path
    if type(materialization) is not MatrixFiniteDtSourceMaterialization:
        raise TypeError("finite-dt source metadata requires its actual typed source materialization")
    scope.__post_init__()
    config = materialization.config
    if scope.profile != config.profile or scope.pipeline_receipt != config.assess():
        raise PermissionError("finite-dt metadata substitutes its actual qualified source pipeline")
    writer.verify_manifest(config.execution_evidence.output_manifest)
    publication = config.execution_evidence.output_manifest.publication
    if publication is None:
        raise PermissionError("finite-dt metadata omits actual atomic source publication")
    target = Path(output_directory)
    if not target.is_absolute() or target != target.resolve(strict=False):
        raise ValueError("finite-dt metadata needs an explicit canonical absolute destination")
    try:
        relative = target.relative_to(writer.root.contract.canonical_path).as_posix()
    except ValueError as error:
        raise ValueError("finite-dt metadata must use its selected guarded artifact plane") from error
    if relative in ("", "."):
        raise ValueError("finite-dt metadata needs a separate selected output directory")
    from empirical_lawhood.api.matrix_finite_dt_dataset_metadata import select_rows_owner
    records = select_rows_owner(type(materialization.rows)).metadata_records_for(scope, config)
    writes, pins = [], []
    for reference, record in records:
        locator = relative + "/" + reference.object_id + ".json"
        writer.root.resolve(locator, for_write=True)
        pins.append(reference)
        writes.append(ArtifactWriteRequest(reference.object_id, locator, record.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, "application/json", "metadata." + scope.record_id,
            relative, record.canonical_bytes(), PROSPECTIVE, (), BLIND))
    publications = writer.write_batch(tuple(writes))
    return tuple(sorted(zip(pins, publications, strict=True), key=lambda value: value[0].object_id))



def authenticate_installed_finite_dt_source_materialization(*, writer, programme, bank, pipeline, verification_publication):
    """Replay installed transform semantics at direct SDK/consumer boundaries.

    Same-schema validator bytes and a passing boolean cannot replace this
    comparison of actual committed source/output bytes and complete typed rows.
    No publication, task receipt, source acquisition or authority is created.
    """
    from empirical_lawhood.api.selected_e4_bank_recipe import _publication_from_manifest
    from empirical_lawhood.adapters.methods import matrix_prepared_source_records as prepared_records
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_programme import SelectedE4PhaseBank
    if type(bank) is prepared_records.MatrixPreparedSourceBank:
        row_kind = MatrixPreparedPendingSourceRows
        rule_kind = MatrixPreparedSourceValidationRule
        verification_kind = MatrixPreparedSourceVerification
    elif type(bank) is SelectedE4PhaseBank:
        row_kind = MatrixFiniteDtPendingSourceRows
        rule_kind = MatrixFiniteDtSourceValidationRule
        verification_kind = MatrixFiniteDtSourceVerification
    else:
        raise TypeError('source replay requires an exact installed bank family')
    config = pipeline.pipeline_config
    source_manifest = writer.read_manifest(config.execution_evidence.source_result.materialization.relative_path)
    if source_manifest.materialization != config.execution_evidence.source_result.materialization:
        raise PermissionError("finite-dt source replaces actual original source materialization")
    source_publication = _publication_from_manifest(writer, source_manifest)
    raw = read_bounded_bytes(writer.root.resolve(source_publication.materialization.relative_path, for_write=False),
        maximum_bytes=source_publication.materialization.size_bytes)
    rows = decode_canonical_bytes(raw, row_kind, maximum_bytes=len(raw))
    if raw != rows.canonical_bytes():
        raise PermissionError("finite-dt source changes its complete original canonical source rows")
    rule = rule_kind(config.profile.source_config.object_id, programme.identity, bank.identity, rows.identity)
    if config.profile.source_config != rule.identity:
        raise PermissionError("finite-dt source substitutes an arbitrary or altered semantic validation rule")
    authenticate_publication(writer, verification_publication)
    raw = read_bounded_bytes(writer.root.resolve(verification_publication.materialization.relative_path, for_write=False),
        maximum_bytes=verification_publication.materialization.size_bytes)
    verification = decode_canonical_bytes(raw, verification_kind, maximum_bytes=len(raw))
    if (raw != verification.canonical_bytes() or verification.identity != config.execution_evidence.recovery
            or pipeline.receipt.validator_receipts != (verification.identity,)):
        raise PermissionError("finite-dt source substitutes its actual complete original validation/recovery observation")
    output_publication = _publication_from_manifest(writer, config.execution_evidence.output_manifest)
    authenticate_finite_dt_source_materialization(writer=writer, programme=programme, bank=bank, rows=rows, rule=rule,
        pipeline=pipeline, source_publication=source_publication, output_publication=output_publication,
        verification=verification, verification_publication=verification_publication)
