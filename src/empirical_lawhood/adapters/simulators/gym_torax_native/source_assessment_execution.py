"""Native acquisition, external-format translation and custody integration."""

from __future__ import annotations
from collections.abc import Callable, Sequence
from pathlib import Path
import re
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.design.study_issue import StudyAuthorityKind, StudyOperationAuthority, require_study_authority
from empirical_lawhood.storage.contracts.artifacts import ArtifactLineageParent
from empirical_lawhood.domains.fusion.gym_torax_native.field_metadata_contracts import GymToraxFieldMetadataNativeEpisode
from empirical_lawhood.domains.fusion.gym_torax_native.extraction_manifest import GymToraxBoundedExtractionManifest
from empirical_lawhood.domains.fusion.gym_torax_native.field_metadata import GymToraxFieldMetadataManifest
from empirical_lawhood.domains.fusion.gym_torax_native.metadata_barrier import GymToraxNativeMetadataCanaryDisposition, adjudicate_gym_torax_native_metadata_canary
from empirical_lawhood.domains.fusion.gym_torax_native.source_assessment_protocol import GymToraxSourceAssessmentCell, GymToraxSourceAssessmentFreeze, GymToraxNativeMetadataCanaryFreeze
from empirical_lawhood.adapters.simulators.gym_torax_native.runtime import GymToraxEnvironmentFactory, GymToraxRuntimeInspector, acquire_gym_torax_episode, inspect_gym_torax_runtime
from empirical_lawhood.domains.fusion.gym_torax_native.native_episode import GymToraxOutputBoundError, GymToraxRuntimePreflightError
from empirical_lawhood.domains.fusion.gym_torax_native.source_qualification import GymToraxNativeSourceQualificationDisposition, GymToraxNativeSourceQualificationReceipt, qualify_gym_torax_native_source
from empirical_lawhood.domains.fusion.gym_torax_native.source_assessment_execution_records import (
    GymToraxNativeCanaryRunReceipt as _science_GymToraxNativeCanaryRunReceipt,
    GymToraxOperationalDisposition as _science_GymToraxOperationalDisposition,
    GymToraxSourceAssessmentCellAcquisitionReceipt as _science_GymToraxSourceAssessmentCellAcquisitionReceipt,
    GymToraxSourceAssessmentTerminalAcquisitionDisposition as _science_GymToraxSourceAssessmentTerminalAcquisitionDisposition,
    GymToraxSourceAssessmentTerminalAcquisitionReceipt as _science_GymToraxSourceAssessmentTerminalAcquisitionReceipt,
)

from empirical_lawhood.execution.gym_torax_custody import (
    GymToraxArtifactPublicationItem as _science_GymToraxArtifactPublicationItem,
    GymToraxBoundedArtifactStore as _science_GymToraxBoundedArtifactStore,
)

_GYM_TORAX_EXECUTION_GRANTEE_ID = "operator.execution-service"

class GymToraxSourceAssessmentIncompleteError(RuntimeError):
    "The frozen source assessment roster lacks at least one terminal cell receipt."

    def __init__(self, missing_cell_ids: Sequence[str]) -> None:
        self.missing_cell_ids = tuple(sorted(set(missing_cell_ids)))
        super().__init__(f"GYM_TORAX_SOURCE_ASSESSMENT_CELL_RECEIPTS_MISSING:{len(self.missing_cell_ids)}")

GymToraxFieldMetadataEpisodeAcquirer = Callable[[object], GymToraxFieldMetadataNativeEpisode]

def _record_identity(identifier: str, record: CanonicalRecord) -> ObjectIdentity:
    return ObjectIdentity.from_record(identifier, record)

def _lineage_parent(
    identity: ObjectIdentity,
    outcome_access: OutcomeAccess,
) -> ArtifactLineageParent:
    return ArtifactLineageParent(
        identity=identity,
        visibility_ceiling=VisibilityCeiling.PROSPECTIVE,
        outcome_access=outcome_access,
    )

def _freeze_logical_id(run_id: str) -> str:
    return f"artifact.{run_id}.freeze"

def _terminal_logical_id(run_id: str) -> str:
    return f"artifact.{run_id}.run-receipt"

def _episode_logical_id(episode_id: str) -> str:
    return f"artifact.{episode_id}"

def _cell_receipt_logical_id(cell_id: str) -> str:
    return f"artifact.receipt.{cell_id}"

def _episode_path(root: str, episode_id: str) -> str:
    return f"{root}/episodes/{episode_id}.json"

def _cell_receipt_path(root: str, cell_id: str) -> str:
    return f"{root}/receipts/{cell_id}.json"

def _require_custody_authority(
    *,
    freeze: CanonicalRecord,
    freeze_id: str,
    relative_root: str,
    authority: StudyOperationAuthority,
    store: _science_GymToraxBoundedArtifactStore,
    at_utc: str,
) -> None:
    require_study_authority(
        authority,
        kind=StudyAuthorityKind.CUSTODY_PUBLICATION,
        subject=_record_identity(freeze_id, freeze),
        prerequisite_authority=None,
        grantee_id=_GYM_TORAX_EXECUTION_GRANTEE_ID,
        storage_root_id=store.storage_root_id,
        relative_root=relative_root,
        at_utc=at_utc,
    )

def _require_execution_authorities(
    *,
    freeze: GymToraxNativeMetadataCanaryFreeze | GymToraxSourceAssessmentFreeze,
    source_authority: StudyOperationAuthority,
    execution_authority: StudyOperationAuthority,
    at_utc: str,
) -> None:
    subject = _record_identity(freeze.freeze_id, freeze)
    require_study_authority(
        source_authority,
        kind=StudyAuthorityKind.SOURCE_ACQUISITION,
        subject=subject,
        prerequisite_authority=None,
        grantee_id=_GYM_TORAX_EXECUTION_GRANTEE_ID,
        at_utc=at_utc,
    )
    require_study_authority(
        execution_authority,
        kind=StudyAuthorityKind.EXPERIMENT_EXECUTION,
        subject=subject,
        prerequisite_authority=freeze.scientific_approval,
        grantee_id=_GYM_TORAX_EXECUTION_GRANTEE_ID,
        at_utc=at_utc,
    )
    if execution_authority.allows_actuation:
        raise PermissionError(
            "Gym-TORAX simulator execution authority cannot permit actuation"
        )
    expected_access = (
        freeze.request.outcome_access
        if isinstance(freeze, GymToraxNativeMetadataCanaryFreeze)
        else OutcomeAccess.EVALUATION_SEALED
    )
    if execution_authority.outcome_access is not expected_access:
        raise PermissionError("Gym-TORAX execution authority changes outcome access")
    if source_authority.authority_id not in freeze.required_operation_authority_ids:
        raise PermissionError("Gym-TORAX source authority ID is outside the freeze")
    if execution_authority.authority_id not in freeze.required_operation_authority_ids:
        raise PermissionError("Gym-TORAX execution authority ID is outside the freeze")

def _publish_freeze(
    *,
    freeze: GymToraxNativeMetadataCanaryFreeze | GymToraxSourceAssessmentFreeze,
    custody_authority: StudyOperationAuthority,
    store: _science_GymToraxBoundedArtifactStore,
    at_utc: str,
) -> ObjectIdentity:
    _require_custody_authority(
        freeze=freeze,
        freeze_id=freeze.freeze_id,
        relative_root=freeze.relative_root,
        authority=custody_authority,
        store=store,
        at_utc=at_utc,
    )
    if custody_authority.authority_id not in freeze.required_operation_authority_ids:
        raise PermissionError("Gym-TORAX custody authority ID is outside the freeze")
    logical_id = _freeze_logical_id(freeze.run_id)
    return store.publish_atomic(
        publication_scope_id=f"publication.{freeze.run_id}",
        publication_scope_relative_root=freeze.relative_root,
        implementation_sha256=freeze.implementation_source_closure.implementation_sha256,
        items=(
            _science_GymToraxArtifactPublicationItem(
                logical_artifact_id=logical_id,
                relative_path=f"{freeze.relative_root}/freeze.json",
                record=freeze,
                visibility_ceiling=VisibilityCeiling.PROSPECTIVE,
                outcome_access=OutcomeAccess.OUTCOME_BLIND,
                lineage_parents=(
                    _lineage_parent(
                        freeze.prospective_protocol_parent,
                        OutcomeAccess.OUTCOME_BLIND,
                    ),
                ),
            ),
        ),
    )[0]

def publish_gym_torax_native_canary_freeze(
    *,
    freeze: GymToraxNativeMetadataCanaryFreeze,
    custody_authority: StudyOperationAuthority,
    store: _science_GymToraxBoundedArtifactStore,
    at_utc: str,
) -> ObjectIdentity:
    return _publish_freeze(
        freeze=freeze,
        custody_authority=custody_authority,
        store=store,
        at_utc=at_utc,
    )

def publish_gym_torax_q_freeze(
    *,
    freeze: GymToraxSourceAssessmentFreeze,
    custody_authority: StudyOperationAuthority,
    store: _science_GymToraxBoundedArtifactStore,
    at_utc: str,
) -> ObjectIdentity:
    return _publish_freeze(
        freeze=freeze,
        custody_authority=custody_authority,
        store=store,
        at_utc=at_utc,
    )

def _require_persisted_freeze(
    store: _science_GymToraxBoundedArtifactStore,
    freeze: GymToraxNativeMetadataCanaryFreeze | GymToraxSourceAssessmentFreeze,
) -> None:
    observed = store.load_optional(
        logical_artifact_id=_freeze_logical_id(freeze.run_id),
        relative_path=f"{freeze.relative_root}/freeze.json",
        record_type=type(freeze),
        maximum_bytes=32 * 1024**2,
    )
    if observed != freeze:
        raise RuntimeError("GYM_TORAX_FREEZE_NOT_PERSISTED_EXACTLY")

def _technical_reason(error: Exception) -> tuple[str, ...]:
    if isinstance(error, GymToraxRuntimePreflightError):
        return tuple(f"NATIVE_SOURCE_ASSESSMENT_{value}" for value in error.reason_codes)
    if isinstance(error, GymToraxOutputBoundError):
        return ("NATIVE_SOURCE_ASSESSMENT_OUTPUT_BOUND_EXCEEDED",)
    token = re.sub(r"[^A-Z0-9]+", "_", type(error).__name__.upper()).strip("_")
    return (f"NATIVE_SOURCE_ASSESSMENT_TECHNICAL_{token or 'ERROR'}",)

def execute_gym_torax_native_metadata_canary(
    *,
    freeze: GymToraxNativeMetadataCanaryFreeze,
    extraction_manifest: GymToraxBoundedExtractionManifest,
    field_metadata_manifest: GymToraxFieldMetadataManifest,
    source_authority: StudyOperationAuthority,
    execution_authority: StudyOperationAuthority,
    custody_authority: StudyOperationAuthority,
    store: _science_GymToraxBoundedArtifactStore,
    repository_root: Path,
    at_utc: str,
    environment_factory: GymToraxEnvironmentFactory | None = None,
    runtime_inspector: GymToraxRuntimeInspector = inspect_gym_torax_runtime,
) -> _science_GymToraxNativeCanaryRunReceipt:
    "Execute or recover the one real metadata canary, never scientific source assessment."

    _require_execution_authorities(
        freeze=freeze,
        source_authority=source_authority,
        execution_authority=execution_authority,
        at_utc=at_utc,
    )
    _require_custody_authority(
        freeze=freeze,
        freeze_id=freeze.freeze_id,
        relative_root=freeze.relative_root,
        authority=custody_authority,
        store=store,
        at_utc=at_utc,
    )
    if custody_authority.authority_id not in freeze.required_operation_authority_ids:
        raise PermissionError("Gym-TORAX canary custody authority ID is outside the freeze")
    _require_persisted_freeze(store, freeze)
    terminal_id = _terminal_logical_id(freeze.run_id)
    terminal_path = f"{freeze.relative_root}/run-receipt.json"
    recovered = store.load_optional(
        logical_artifact_id=terminal_id,
        relative_path=terminal_path,
        record_type=_science_GymToraxNativeCanaryRunReceipt,
        maximum_bytes=2 * 1024**2,
    )
    if recovered is not None:
        if recovered.freeze != _record_identity(freeze.freeze_id, freeze):
            raise RuntimeError("GYM_TORAX_CANARY_RECOVERY_FREEZE_DIVERGENCE")
        return recovered

    freeze_identity = _record_identity(freeze.freeze_id, freeze)
    request_identity = _record_identity(freeze.request.request_id, freeze.request)
    items: list[_science_GymToraxArtifactPublicationItem] = []
    source_reset_attempted = False

    def observe_source_reset() -> None:
        nonlocal source_reset_attempted
        source_reset_attempted = True

    try:
        episode = acquire_gym_torax_episode(
            freeze.request,
            extraction_manifest=extraction_manifest,
            field_metadata_manifest=field_metadata_manifest,
            repository_root=repository_root,
            environment_factory=environment_factory,
            runtime_inspector=runtime_inspector,
            source_reset_observer=observe_source_reset,
        )
        episode_identity = _record_identity(episode.episode_id, episode)
        canary = adjudicate_gym_torax_native_metadata_canary(
            episode=episode,
            field_metadata_manifest=field_metadata_manifest,
        )
        qualification = qualify_gym_torax_native_source(
            episode=episode,
            canary=canary,
            extraction_manifest=extraction_manifest,
            field_metadata_manifest=field_metadata_manifest,
        )
        passed = (
            canary.disposition is GymToraxNativeMetadataCanaryDisposition.PASS
            and qualification.disposition
            is GymToraxNativeSourceQualificationDisposition.QUALIFIED
        )
        reasons = (
            ()
            if passed
            else tuple(sorted({*canary.reason_codes, *qualification.reason_codes}))
        )
        terminal = _science_GymToraxNativeCanaryRunReceipt(
            receipt_id=f"receipt.{freeze.run_id.removeprefix('run.')}.terminal",
            freeze=freeze_identity,
            request=request_identity,
            episode=episode_identity,
            metadata_canary=_record_identity(canary.receipt_id, canary),
            source_qualification=_record_identity(
                qualification.receipt_id, qualification
            ),
            disposition=(
                _science_GymToraxOperationalDisposition.SUCCEEDED
                if passed
                else _science_GymToraxOperationalDisposition.FAILED
            ),
            reason_codes=reasons,
            source_reset_attempted=episode.source_reset_attempted,
            scientific_values_decoded=False,
            outcome_access=OutcomeAccess.OUTCOME_BLIND,
            visibility_ceiling=VisibilityCeiling.PROSPECTIVE,
            evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
            grants_source_assessment_freeze_authority=False,
            grants_source_assessment_execution_authority=False,
        )
        for logical_id, path, record, parents in (
            (
                _episode_logical_id(episode.episode_id),
                _episode_path(freeze.relative_root, episode.episode_id),
                episode,
                (freeze_identity,),
            ),
            (
                f"artifact.{canary.receipt_id}",
                f"{freeze.relative_root}/metadata-canary-receipt.json",
                canary,
                tuple(
                    sorted(
                        (freeze_identity, episode_identity),
                        key=lambda value: value.object_id,
                    )
                ),
            ),
            (
                f"artifact.{qualification.receipt_id}",
                f"{freeze.relative_root}/source-qualification.json",
                qualification,
                (
                    _record_identity(canary.receipt_id, canary),
                    episode_identity,
                    freeze_identity,
                ),
            ),
        ):
            items.append(
                _science_GymToraxArtifactPublicationItem(
                    logical_artifact_id=logical_id,
                    relative_path=path,
                    record=record,
                    visibility_ceiling=VisibilityCeiling.PROSPECTIVE,
                    outcome_access=OutcomeAccess.OUTCOME_BLIND,
                    lineage_parents=tuple(
                        sorted(
                            (
                                _lineage_parent(value, OutcomeAccess.OUTCOME_BLIND)
                                for value in parents
                            ),
                            key=lambda value: value.identity.object_id,
                        )
                    ),
                )
            )
    except Exception as error:
        terminal = _science_GymToraxNativeCanaryRunReceipt(
            receipt_id=f"receipt.{freeze.run_id.removeprefix('run.')}.terminal",
            freeze=freeze_identity,
            request=request_identity,
            episode=None,
            metadata_canary=None,
            source_qualification=None,
            disposition=_science_GymToraxOperationalDisposition.FAILED,
            reason_codes=_technical_reason(error),
            source_reset_attempted=source_reset_attempted,
            scientific_values_decoded=False,
            outcome_access=OutcomeAccess.OUTCOME_BLIND,
            visibility_ceiling=VisibilityCeiling.PROSPECTIVE,
            evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
            grants_source_assessment_freeze_authority=False,
            grants_source_assessment_execution_authority=False,
        )
    items.append(
        _science_GymToraxArtifactPublicationItem(
            logical_artifact_id=terminal_id,
            relative_path=terminal_path,
            record=terminal,
            visibility_ceiling=VisibilityCeiling.PROSPECTIVE,
            outcome_access=OutcomeAccess.OUTCOME_BLIND,
            lineage_parents=(
                _lineage_parent(freeze_identity, OutcomeAccess.OUTCOME_BLIND),
            ),
        )
    )
    store.publish_atomic(
        publication_scope_id=f"publication.{freeze.run_id}",
        publication_scope_relative_root=freeze.relative_root,
        implementation_sha256=freeze.implementation_source_closure.implementation_sha256,
        items=tuple(sorted(items, key=lambda value: value.logical_artifact_id)),
    )
    return terminal

def _validate_recovered_cell(
    *,
    freeze: GymToraxSourceAssessmentFreeze,
    cell: GymToraxSourceAssessmentCell,
    receipt: _science_GymToraxSourceAssessmentCellAcquisitionReceipt,
    episode: GymToraxFieldMetadataNativeEpisode | None,
) -> None:
    if (
        receipt.freeze != _record_identity(freeze.freeze_id, freeze)
        or receipt.cell != _record_identity(cell.cell_id, cell)
        or receipt.request != _record_identity(cell.request.request_id, cell.request)
        or receipt.expected_episode_id != cell.episode_id
    ):
        raise RuntimeError("GYM_TORAX_SOURCE_ASSESSMENT_RECOVERY_LINEAGE_DIVERGENCE")
    if receipt.disposition is _science_GymToraxOperationalDisposition.SUCCEEDED:
        if episode is None or receipt.episode != _record_identity(
            episode.episode_id, episode
        ):
            raise RuntimeError("GYM_TORAX_SOURCE_ASSESSMENT_RECOVERY_EPISODE_DIVERGENCE")
        if episode.request != receipt.request or episode.episode_id != cell.episode_id:
            raise RuntimeError("GYM_TORAX_SOURCE_ASSESSMENT_RECOVERY_REQUEST_DIVERGENCE")
    elif episode is not None:
        raise RuntimeError("GYM_TORAX_SOURCE_ASSESSMENT_FAILED_RECEIPT_HAS_EPISODE")

def run_gym_torax_q(
    *,
    freeze: GymToraxSourceAssessmentFreeze,
    source_qualification: GymToraxNativeSourceQualificationReceipt,
    extraction_manifest: GymToraxBoundedExtractionManifest,
    field_metadata_manifest: GymToraxFieldMetadataManifest,
    source_authority: StudyOperationAuthority,
    execution_authority: StudyOperationAuthority,
    custody_authority: StudyOperationAuthority,
    store: _science_GymToraxBoundedArtifactStore,
    repository_root: Path,
    at_utc: str,
    environment_factory: GymToraxEnvironmentFactory | None = None,
    runtime_inspector: GymToraxRuntimeInspector = inspect_gym_torax_runtime,
    episode_acquirer: Callable[[GymToraxSourceAssessmentCell], GymToraxFieldMetadataNativeEpisode]
    | None = None,
) -> tuple[_science_GymToraxSourceAssessmentCellAcquisitionReceipt, ...]:
    """Execute or exactly recover every frozen cell, sequentially and sealed."""

    if freeze.maximum_concurrency != 1:
        raise ValueError("bounded source assessment runner only supports frozen concurrency one")
    if freeze.source_qualification != _record_identity(
        source_qualification.receipt_id,
        source_qualification,
    ):
        raise ValueError("source assessment runner source qualification differs from its freeze")
    if (
        source_qualification.disposition
        is not GymToraxNativeSourceQualificationDisposition.QUALIFIED
    ):
        raise ValueError("source assessment runner requires a qualified source")
    _require_execution_authorities(
        freeze=freeze,
        source_authority=source_authority,
        execution_authority=execution_authority,
        at_utc=at_utc,
    )
    _require_custody_authority(
        freeze=freeze,
        freeze_id=freeze.freeze_id,
        relative_root=freeze.relative_root,
        authority=custody_authority,
        store=store,
        at_utc=at_utc,
    )
    if custody_authority.authority_id not in freeze.required_operation_authority_ids:
        raise PermissionError("Gym-TORAX source assessment custody authority ID is outside the freeze")
    _require_persisted_freeze(store, freeze)
    freeze_identity = _record_identity(freeze.freeze_id, freeze)
    receipts: list[_science_GymToraxSourceAssessmentCellAcquisitionReceipt] = []
    for cell in freeze.cells:
        receipt_id = _cell_receipt_logical_id(cell.cell_id)
        receipt_path = _cell_receipt_path(freeze.relative_root, cell.cell_id)
        episode_id = _episode_logical_id(cell.episode_id)
        episode_path = _episode_path(freeze.relative_root, cell.episode_id)
        recovered_receipt = store.load_optional(
            logical_artifact_id=receipt_id,
            relative_path=receipt_path,
            record_type=_science_GymToraxSourceAssessmentCellAcquisitionReceipt,
            maximum_bytes=2 * 1024**2,
        )
        recovered_episode = store.load_optional(
            logical_artifact_id=episode_id,
            relative_path=episode_path,
            record_type=GymToraxFieldMetadataNativeEpisode,
            maximum_bytes=cell.request.maximum_output_bytes,
        )
        if recovered_receipt is not None:
            _validate_recovered_cell(
                freeze=freeze,
                cell=cell,
                receipt=recovered_receipt,
                episode=recovered_episode,
            )
            receipts.append(recovered_receipt)
            continue
        if recovered_episode is not None:
            raise RuntimeError("GYM_TORAX_SOURCE_ASSESSMENT_ORPHAN_EPISODE_WITHOUT_RECEIPT")
        items: tuple[_science_GymToraxArtifactPublicationItem, ...]
        source_reset_attempted = False

        def observe_source_reset() -> None:
            nonlocal source_reset_attempted
            source_reset_attempted = True

        try:
            episode = (
                episode_acquirer(cell)
                if episode_acquirer is not None
                else acquire_gym_torax_episode(
                    cell.request,
                    extraction_manifest=extraction_manifest,
                    field_metadata_manifest=field_metadata_manifest,
                    repository_root=repository_root,
                    environment_factory=environment_factory,
                    runtime_inspector=runtime_inspector,
                    source_reset_observer=observe_source_reset,
                )
            )
            episode_identity = _record_identity(episode.episode_id, episode)
            receipt = _science_GymToraxSourceAssessmentCellAcquisitionReceipt(
                receipt_id=f"receipt.{cell.cell_id.removeprefix('cell.')}",
                freeze=freeze_identity,
                cell=_record_identity(cell.cell_id, cell),
                request=_record_identity(cell.request.request_id, cell.request),
                expected_episode_id=cell.episode_id,
                episode=episode_identity,
                disposition=_science_GymToraxOperationalDisposition.SUCCEEDED,
                reason_codes=(),
                attempt_count=1,
                automatic_retry_performed=False,
                source_reset_attempted=episode.source_reset_attempted,
                scientific_values_decoded=False,
                outcome_access=OutcomeAccess.EVALUATION_SEALED,
                visibility_ceiling=VisibilityCeiling.PROSPECTIVE,
                evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
            )
            _validate_recovered_cell(
                freeze=freeze,
                cell=cell,
                receipt=receipt,
                episode=episode,
            )
            items = (
                _science_GymToraxArtifactPublicationItem(
                    logical_artifact_id=episode_id,
                    relative_path=episode_path,
                    record=episode,
                    visibility_ceiling=VisibilityCeiling.PROSPECTIVE,
                    outcome_access=OutcomeAccess.EVALUATION_SEALED,
                    lineage_parents=(
                        _lineage_parent(freeze_identity, OutcomeAccess.OUTCOME_BLIND),
                    ),
                ),
                _science_GymToraxArtifactPublicationItem(
                    logical_artifact_id=receipt_id,
                    relative_path=receipt_path,
                    record=receipt,
                    visibility_ceiling=VisibilityCeiling.PROSPECTIVE,
                    outcome_access=OutcomeAccess.EVALUATION_SEALED,
                    lineage_parents=tuple(
                        sorted(
                            (
                                _lineage_parent(
                                    episode_identity,
                                    OutcomeAccess.EVALUATION_SEALED,
                                ),
                                _lineage_parent(
                                    freeze_identity,
                                    OutcomeAccess.OUTCOME_BLIND,
                                ),
                            ),
                            key=lambda value: value.identity.object_id,
                        )
                    ),
                ),
            )
        except Exception as error:
            receipt = _science_GymToraxSourceAssessmentCellAcquisitionReceipt(
                receipt_id=f"receipt.{cell.cell_id.removeprefix('cell.')}",
                freeze=freeze_identity,
                cell=_record_identity(cell.cell_id, cell),
                request=_record_identity(cell.request.request_id, cell.request),
                expected_episode_id=cell.episode_id,
                episode=None,
                disposition=_science_GymToraxOperationalDisposition.FAILED,
                reason_codes=_technical_reason(error),
                attempt_count=1,
                automatic_retry_performed=False,
                source_reset_attempted=source_reset_attempted,
                scientific_values_decoded=False,
                outcome_access=OutcomeAccess.EVALUATION_SEALED,
                visibility_ceiling=VisibilityCeiling.PROSPECTIVE,
                evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
            )
            items = (
                _science_GymToraxArtifactPublicationItem(
                    logical_artifact_id=receipt_id,
                    relative_path=receipt_path,
                    record=receipt,
                    visibility_ceiling=VisibilityCeiling.PROSPECTIVE,
                    outcome_access=OutcomeAccess.EVALUATION_SEALED,
                    lineage_parents=(
                        _lineage_parent(freeze_identity, OutcomeAccess.OUTCOME_BLIND),
                    ),
                ),
            )
        store.publish_atomic(
            publication_scope_id=f"publication.{freeze.run_id}",
            publication_scope_relative_root=freeze.relative_root,
            implementation_sha256=freeze.implementation_source_closure.implementation_sha256,
            items=tuple(sorted(items, key=lambda value: value.logical_artifact_id)),
        )
        receipts.append(receipt)
    return tuple(sorted(receipts, key=lambda value: value.cell.object_id))

def finalize_gym_torax_q(
    *,
    freeze: GymToraxSourceAssessmentFreeze,
    custody_authority: StudyOperationAuthority,
    store: _science_GymToraxBoundedArtifactStore,
    at_utc: str,
) -> _science_GymToraxSourceAssessmentTerminalAcquisitionReceipt:
    """Publish the terminal roster receipt only after all 96 cells are accounted."""

    _require_custody_authority(
        freeze=freeze,
        freeze_id=freeze.freeze_id,
        relative_root=freeze.relative_root,
        authority=custody_authority,
        store=store,
        at_utc=at_utc,
    )
    if custody_authority.authority_id not in freeze.required_operation_authority_ids:
        raise PermissionError("Gym-TORAX source assessment custody authority ID is outside the freeze")
    _require_persisted_freeze(store, freeze)
    terminal_id = _terminal_logical_id(freeze.run_id)
    terminal_path = f"{freeze.relative_root}/run-receipt.json"
    recovered = store.load_optional(
        logical_artifact_id=terminal_id,
        relative_path=terminal_path,
        record_type=_science_GymToraxSourceAssessmentTerminalAcquisitionReceipt,
        maximum_bytes=4 * 1024**2,
    )
    if recovered is not None:
        if recovered.freeze != _record_identity(freeze.freeze_id, freeze):
            raise RuntimeError("GYM_TORAX_SOURCE_ASSESSMENT_TERMINAL_RECOVERY_FREEZE_DIVERGENCE")
        return recovered

    receipts: list[_science_GymToraxSourceAssessmentCellAcquisitionReceipt] = []
    episodes: list[ObjectIdentity] = []
    missing: list[str] = []
    for cell in freeze.cells:
        receipt = store.load_optional(
            logical_artifact_id=_cell_receipt_logical_id(cell.cell_id),
            relative_path=_cell_receipt_path(freeze.relative_root, cell.cell_id),
            record_type=_science_GymToraxSourceAssessmentCellAcquisitionReceipt,
            maximum_bytes=2 * 1024**2,
        )
        episode = store.load_optional(
            logical_artifact_id=_episode_logical_id(cell.episode_id),
            relative_path=_episode_path(freeze.relative_root, cell.episode_id),
            record_type=GymToraxFieldMetadataNativeEpisode,
            maximum_bytes=cell.request.maximum_output_bytes,
        )
        if receipt is None:
            missing.append(cell.cell_id)
            if episode is not None:
                raise RuntimeError("GYM_TORAX_SOURCE_ASSESSMENT_ORPHAN_EPISODE_WITHOUT_RECEIPT")
            continue
        _validate_recovered_cell(
            freeze=freeze, cell=cell, receipt=receipt, episode=episode
        )
        receipts.append(receipt)
        if episode is not None:
            episodes.append(_record_identity(episode.episode_id, episode))
    if missing:
        raise GymToraxSourceAssessmentIncompleteError(missing)
    failed_count = sum(
        value.disposition is _science_GymToraxOperationalDisposition.FAILED for value in receipts
    )
    terminal = _science_GymToraxSourceAssessmentTerminalAcquisitionReceipt(
        receipt_id=f"receipt.{freeze.run_id.removeprefix('run.')}.terminal-acquisition",
        freeze=_record_identity(freeze.freeze_id, freeze),
        cell_receipts=tuple(
            sorted(
                (_record_identity(value.receipt_id, value) for value in receipts),
                key=lambda value: value.object_id,
            )
        ),
        episodes=tuple(sorted(episodes, key=lambda value: value.object_id)),
        accounted_cell_count=len(receipts),
        completed_episode_count=len(episodes),
        failed_cell_count=failed_count,
        disposition=(
            _science_GymToraxSourceAssessmentTerminalAcquisitionDisposition.COMPLETE
            if failed_count == 0
            else _science_GymToraxSourceAssessmentTerminalAcquisitionDisposition.INCOMPLETE
        ),
        reason_codes=() if failed_count == 0 else ("GYM_TORAX_SOURCE_ASSESSMENT_TECHNICAL_CELL_FAILURE",),
        scientific_values_decoded=False,
        outcome_access=OutcomeAccess.EVALUATION_SEALED,
        visibility_ceiling=VisibilityCeiling.PROSPECTIVE,
        evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
    )
    store.publish_atomic(
        publication_scope_id=f"publication.{freeze.run_id}",
        publication_scope_relative_root=freeze.relative_root,
        implementation_sha256=freeze.implementation_source_closure.implementation_sha256,
        items=(
            _science_GymToraxArtifactPublicationItem(
                logical_artifact_id=terminal_id,
                relative_path=terminal_path,
                record=terminal,
                visibility_ceiling=VisibilityCeiling.PROSPECTIVE,
                outcome_access=OutcomeAccess.EVALUATION_SEALED,
                lineage_parents=tuple(
                    sorted(
                        (
                            _lineage_parent(
                                _record_identity(value.receipt_id, value),
                                OutcomeAccess.EVALUATION_SEALED,
                            )
                            for value in receipts
                        ),
                        key=lambda value: value.identity.object_id,
                    )
                ),
            ),
        ),
    )
    return terminal
