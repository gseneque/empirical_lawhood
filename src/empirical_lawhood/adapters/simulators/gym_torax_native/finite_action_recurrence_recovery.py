"""Native acquisition, external-format translation and custody integration."""

from __future__ import annotations
from collections.abc import Callable
import hashlib
from pathlib import Path
import re
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.design.study_issue import StudyAuthorityKind, StudyOperationAuthority
from empirical_lawhood.domains.fusion.gym_torax_native.field_metadata_contracts import GymToraxFieldMetadataEpisodeRequest, GymToraxFieldMetadataNativeEpisode
from empirical_lawhood.domains.fusion.gym_torax_native.extraction_manifest import GymToraxBoundedExtractionManifest
from empirical_lawhood.domains.fusion.gym_torax_native.field_metadata import GymToraxFieldMetadataManifest
from empirical_lawhood.execution.gym_torax_custody import GymToraxArtifactPublicationItem, GymToraxBoundedArtifactStore
from empirical_lawhood.domains.fusion.gym_torax_native.source_assessment_execution_records import GymToraxOperationalDisposition
from empirical_lawhood.adapters.simulators.gym_torax_native.runtime import GymToraxEnvironmentFactory, GymToraxRuntimeInspector, acquire_gym_torax_episode, inspect_gym_torax_runtime
from empirical_lawhood.domains.fusion.gym_torax_native.source_qualification import GymToraxNativeSourceQualificationReceipt

from empirical_lawhood.domains.fusion.gym_torax_native.finite_action_recurrence_recovery import (
    GYM_TORAX_FINITE_ACTION_RECURRENCE_RECOVERY_RELATIVE_ROOT as _science_GYM_TORAX_FINITE_ACTION_RECURRENCE_RECOVERY_RELATIVE_ROOT,
    GYM_TORAX_FINITE_ACTION_RECURRENCE_RECOVERY_RUN_ID as _science_GYM_TORAX_FINITE_ACTION_RECURRENCE_RECOVERY_RUN_ID,
    GymToraxFiniteActionRecurrenceRecoveryCellReceipt as _science_GymToraxFiniteActionRecurrenceRecoveryCellReceipt,
    GymToraxFiniteActionRecurrenceRecoveryFreeze as _science_GymToraxFiniteActionRecurrenceRecoveryFreeze,
    GymToraxFiniteActionRecurrenceRecoveryTerminalDisposition as _science_GymToraxFiniteActionRecurrenceRecoveryTerminalDisposition,
    GymToraxFiniteActionRecurrenceRecoveryTerminalReceipt as _science_GymToraxFiniteActionRecurrenceRecoveryTerminalReceipt,
    _identity,
    _is_complete_valid,
    _parent,
    _require_authority,
    materialize_gym_torax_finite_action_recurrence_recovery_request as _science_materialize_gym_torax_finite_action_recurrence_recovery_request,
)

def publish_gym_torax_finite_action_recurrence_recovery_freeze(
    *,
    freeze: _science_GymToraxFiniteActionRecurrenceRecoveryFreeze,
    custody_authority: StudyOperationAuthority,
    store: GymToraxBoundedArtifactStore,
    at_utc: str,
) -> ObjectIdentity:
    _require_authority(
        freeze=freeze,
        authority=custody_authority,
        kind=StudyAuthorityKind.CUSTODY_PUBLICATION,
        at_utc=at_utc,
        store=store,
    )
    parents = tuple(
        sorted(
            (
                _parent(freeze.parent_freeze, OutcomeAccess.EVALUATION_REVEALED),
                _parent(freeze.parent_qualification, OutcomeAccess.EVALUATOR_REVEAL),
                _parent(freeze.parent_terminal, OutcomeAccess.EVALUATION_REVEALED),
                _parent(freeze.extraction_manifest, OutcomeAccess.OUTCOME_BLIND),
            ),
            key=lambda value: value.identity.object_id,
        )
    )
    return store.publish_atomic(
        publication_scope_id=f"publication.{freeze.run_id}",
        publication_scope_relative_root=freeze.relative_root,
        implementation_sha256=freeze.implementation_source_closure.implementation_sha256,
        items=(
            GymToraxArtifactPublicationItem(
                logical_artifact_id=f"artifact.{freeze.run_id}.freeze",
                relative_path=f"{freeze.relative_root}/freeze.json",
                record=freeze,
                visibility_ceiling=VisibilityCeiling.OUTCOME_VISIBLE,
                outcome_access=OutcomeAccess.EVALUATION_REVEALED,
                lineage_parents=parents,
            ),
        ),
    )[0]

def _load_freeze(store: GymToraxBoundedArtifactStore) -> _science_GymToraxFiniteActionRecurrenceRecoveryFreeze:
    value = store.load_optional(
        logical_artifact_id=f'artifact.{_science_GYM_TORAX_FINITE_ACTION_RECURRENCE_RECOVERY_RUN_ID}.freeze',
        relative_path=f'{_science_GYM_TORAX_FINITE_ACTION_RECURRENCE_RECOVERY_RELATIVE_ROOT}/freeze.json',
        record_type=_science_GymToraxFiniteActionRecurrenceRecoveryFreeze,
        maximum_bytes=32 * 1024**2,
    )
    if value is None:
        raise RuntimeError("GYM_TORAX_FINITE_ACTION_RECURRENCE_RECOVERY_FREEZE_NOT_PUBLISHED")
    return value

def _technical_reason(error: Exception) -> tuple[tuple[str, ...], str]:
    token = (
        re.sub(r"[^A-Z0-9]+", "_", type(error).__name__.upper()).strip("_") or "ERROR"
    )
    detail = f"{type(error).__name__}:{str(error)[:1024]}"
    return (f"FINITE_ACTION_RECURRENCE_RECOVERY_TECHNICAL_{token}",), hashlib.sha256(
        detail.encode()
    ).hexdigest()

def run_gym_torax_finite_action_recurrence_recovery(
    *,
    freeze: _science_GymToraxFiniteActionRecurrenceRecoveryFreeze,
    source_qualification: GymToraxNativeSourceQualificationReceipt,
    extraction_manifest: GymToraxBoundedExtractionManifest,
    field_metadata_manifest: GymToraxFieldMetadataManifest,
    source_authority: StudyOperationAuthority,
    execution_authority: StudyOperationAuthority,
    custody_authority: StudyOperationAuthority,
    store: GymToraxBoundedArtifactStore,
    repository_root: Path,
    at_utc: str,
    environment_factory: GymToraxEnvironmentFactory | None = None,
    runtime_inspector: GymToraxRuntimeInspector = inspect_gym_torax_runtime,
    episode_acquirer: Callable[[GymToraxFieldMetadataEpisodeRequest], GymToraxFieldMetadataNativeEpisode]
    | None = None,
) -> tuple[_science_GymToraxFiniteActionRecurrenceRecoveryCellReceipt, ...]:
    if _load_freeze(store) != freeze:
        raise RuntimeError("GYM_TORAX_FINITE_ACTION_RECURRENCE_RECOVERY_FREEZE_DIVERGED")
    _require_authority(
        freeze=freeze,
        authority=source_authority,
        kind=StudyAuthorityKind.SOURCE_ACQUISITION,
        at_utc=at_utc,
    )
    _require_authority(
        freeze=freeze,
        authority=execution_authority,
        kind=StudyAuthorityKind.EXPERIMENT_EXECUTION,
        at_utc=at_utc,
        prerequisite=freeze.scientific_approval,
    )
    _require_authority(
        freeze=freeze,
        authority=custody_authority,
        kind=StudyAuthorityKind.CUSTODY_PUBLICATION,
        at_utc=at_utc,
        store=store,
    )
    if freeze.source_qualification != _identity(
        source_qualification.receipt_id, source_qualification
    ):
        raise ValueError("Finite-action recurrence recovery source qualification differs")
    receipts = []
    for cell in freeze.cells:
        request = _science_materialize_gym_torax_finite_action_recurrence_recovery_request(freeze, cell)
        request_path = f"{freeze.relative_root}/requests/{request.request_id}.json"
        episode_path = f"{freeze.relative_root}/episodes/{cell.episode_id}.json"
        receipt_path = f"{freeze.relative_root}/receipts/{cell.cell_id}.json"
        recovered_receipt = store.load_optional(
            logical_artifact_id=f"artifact.receipt.{cell.cell_id}",
            relative_path=receipt_path,
            record_type=_science_GymToraxFiniteActionRecurrenceRecoveryCellReceipt,
            maximum_bytes=2 * 1024**2,
        )
        if recovered_receipt is not None:
            receipts.append(recovered_receipt)
            continue
        recovered_request = store.load_optional(
            logical_artifact_id=f"artifact.{request.request_id}",
            relative_path=request_path,
            record_type=GymToraxFieldMetadataEpisodeRequest,
            maximum_bytes=2 * 1024**2,
        )
        if recovered_request is not None:
            raise RuntimeError("GYM_TORAX_FINITE_ACTION_RECURRENCE_RECOVERY_INTERRUPTED_REQUEST_NO_RETRY")
        store.publish_atomic(
            publication_scope_id=f"publication.{freeze.run_id}",
            publication_scope_relative_root=freeze.relative_root,
            implementation_sha256=freeze.implementation_source_closure.implementation_sha256,
            items=(
                GymToraxArtifactPublicationItem(
                    logical_artifact_id=f"artifact.{request.request_id}",
                    relative_path=request_path,
                    record=request,
                    visibility_ceiling=VisibilityCeiling.PROSPECTIVE,
                    outcome_access=OutcomeAccess.EVALUATION_SEALED,
                    # The visible declaration already binds this exact request
                    # hash. The fresh acquisition remains sealed from the old,
                    # revealed outcome lineage and is joined only at reveal.
                    lineage_parents=tuple(
                        sorted(
                            (
                                _parent(
                                    freeze.extraction_manifest,
                                    OutcomeAccess.OUTCOME_BLIND,
                                ),
                                _parent(
                                    freeze.field_metadata_manifest,
                                    OutcomeAccess.OUTCOME_BLIND,
                                ),
                                _parent(
                                    freeze.source_qualification,
                                    OutcomeAccess.OUTCOME_BLIND,
                                ),
                            ),
                            key=lambda value: value.identity.object_id,
                        )
                    ),
                ),
            ),
        )
        source_reset_attempted = False

        def observed_reset() -> None:
            nonlocal source_reset_attempted
            source_reset_attempted = True

        try:
            episode = (
                episode_acquirer(request)
                if episode_acquirer
                else acquire_gym_torax_episode(
                    request,
                    extraction_manifest=extraction_manifest,
                    field_metadata_manifest=field_metadata_manifest,
                    repository_root=repository_root,
                    environment_factory=environment_factory,
                    runtime_inspector=runtime_inspector,
                    source_reset_observer=observed_reset,
                )
            )
            if (
                episode.episode_id != cell.episode_id
                or episode.request != _identity(request.request_id, request)
                or episode.preparation
                != _identity(request.preparation.preparation_id, request.preparation)
            ):
                raise RuntimeError("GYM_TORAX_FINITE_ACTION_RECURRENCE_RECOVERY_EPISODE_LINEAGE_DIVERGED")
            store.publish_atomic(
                publication_scope_id=f"publication.{freeze.run_id}",
                publication_scope_relative_root=freeze.relative_root,
                implementation_sha256=freeze.implementation_source_closure.implementation_sha256,
                items=(
                    GymToraxArtifactPublicationItem(
                        logical_artifact_id=f"artifact.{cell.episode_id}",
                        relative_path=episode_path,
                        record=episode,
                        visibility_ceiling=VisibilityCeiling.PROSPECTIVE,
                        outcome_access=OutcomeAccess.EVALUATION_SEALED,
                        lineage_parents=(
                            _parent(
                                _identity(request.request_id, request),
                                OutcomeAccess.EVALUATION_SEALED,
                            ),
                        ),
                    ),
                ),
            )
            disposition = GymToraxOperationalDisposition.SUCCEEDED
            complete_valid = _is_complete_valid(episode)
            operational_reasons: tuple[str, ...] = ()
            episode_reasons = episode.reason_codes
            detail_sha = None
        except Exception as error:
            episode = None
            disposition = GymToraxOperationalDisposition.FAILED
            complete_valid = False
            operational_reasons, detail_sha = _technical_reason(error)
            episode_reasons = ()
        receipt = _science_GymToraxFiniteActionRecurrenceRecoveryCellReceipt(
            receipt_id=f"receipt.{cell.cell_id.removeprefix('cell.')}",
            freeze=_identity(freeze.freeze_id, freeze),
            cell=_identity(cell.cell_id, cell),
            request=_identity(request.request_id, request),
            episode=None if episode is None else _identity(episode.episode_id, episode),
            disposition=disposition,
            complete_valid_episode=complete_valid,
            operational_reason_codes=operational_reasons,
            episode_reason_codes=episode_reasons,
            technical_detail_sha256=detail_sha,
            attempt_count=1,
            automatic_retry_performed=False,
            source_reset_attempted=(
                source_reset_attempted
                if episode is None
                else episode.source_reset_attempted
            ),
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
                GymToraxArtifactPublicationItem(
                    logical_artifact_id=f"artifact.receipt.{cell.cell_id}",
                    relative_path=receipt_path,
                    record=receipt,
                    visibility_ceiling=VisibilityCeiling.PROSPECTIVE,
                    outcome_access=OutcomeAccess.EVALUATION_SEALED,
                    lineage_parents=tuple(
                        sorted(
                            (
                                _parent(
                                    _identity(request.request_id, request),
                                    OutcomeAccess.EVALUATION_SEALED,
                                ),
                                *(
                                    ()
                                    if episode is None
                                    else (
                                        _parent(
                                            _identity(episode.episode_id, episode),
                                            OutcomeAccess.EVALUATION_SEALED,
                                        ),
                                    )
                                ),
                            ),
                            key=lambda value: value.identity.object_id,
                        )
                    ),
                ),
            ),
        )
        receipts.append(receipt)
        if receipt.disposition is GymToraxOperationalDisposition.FAILED:
            break
    return tuple(sorted(receipts, key=lambda value: value.cell.object_id))

def finalize_gym_torax_finite_action_recurrence_recovery(
    *,
    freeze: _science_GymToraxFiniteActionRecurrenceRecoveryFreeze,
    custody_authority: StudyOperationAuthority,
    store: GymToraxBoundedArtifactStore,
    at_utc: str,
) -> _science_GymToraxFiniteActionRecurrenceRecoveryTerminalReceipt:
    _require_authority(
        freeze=freeze,
        authority=custody_authority,
        kind=StudyAuthorityKind.CUSTODY_PUBLICATION,
        at_utc=at_utc,
        store=store,
    )
    receipts = []
    episodes = []
    for cell in freeze.cells:
        receipt = store.load_optional(
            logical_artifact_id=f"artifact.receipt.{cell.cell_id}",
            relative_path=f"{freeze.relative_root}/receipts/{cell.cell_id}.json",
            record_type=_science_GymToraxFiniteActionRecurrenceRecoveryCellReceipt,
            maximum_bytes=2 * 1024**2,
        )
        if receipt is None:
            raise RuntimeError(f"GYM_TORAX_FINITE_ACTION_RECURRENCE_RECOVERY_RECEIPT_MISSING:{cell.cell_id}")
        receipts.append(receipt)
        if receipt.episode is not None:
            episodes.append(receipt.episode)
    partial = sum(
        value.disposition is GymToraxOperationalDisposition.SUCCEEDED
        and not value.complete_valid_episode
        for value in receipts
    )
    failed = sum(
        value.disposition is GymToraxOperationalDisposition.FAILED for value in receipts
    )
    valid = len(episodes) - partial
    terminal = _science_GymToraxFiniteActionRecurrenceRecoveryTerminalReceipt(
        receipt_id='receipt.tokamak-control.finite-action-recurrence-recovery.terminal',
        freeze=_identity(freeze.freeze_id, freeze),
        cell_receipts=tuple(
            sorted(
                (_identity(value.receipt_id, value) for value in receipts),
                key=lambda value: value.object_id,
            )
        ),
        episodes=tuple(sorted(episodes, key=lambda value: value.object_id)),
        accounted_cell_count=80,
        episode_count=len(episodes),
        complete_valid_episode_count=valid,
        partial_episode_count=partial,
        failed_cell_count=failed,
        disposition=(
            _science_GymToraxFiniteActionRecurrenceRecoveryTerminalDisposition.INCOMPLETE
            if failed
            else (
                _science_GymToraxFiniteActionRecurrenceRecoveryTerminalDisposition.COMPLETE_WITH_PARTIAL
                if partial
                else _science_GymToraxFiniteActionRecurrenceRecoveryTerminalDisposition.COMPLETE_VALID
            )
        ),
        reason_codes=tuple(
            sorted(
                ({"GYM_TORAX_FINITE_ACTION_RECURRENCE_RECOVERY_TECHNICAL_CELL_FAILURE"} if failed else set())
                | ({"GYM_TORAX_FINITE_ACTION_RECURRENCE_RECOVERY_PARTIAL_EPISODE_EVIDENCE"} if partial else set())
            )
        ),
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
            GymToraxArtifactPublicationItem(
                logical_artifact_id=f"artifact.{freeze.run_id}.run-receipt",
                relative_path=f"{freeze.relative_root}/run-receipt.json",
                record=terminal,
                visibility_ceiling=VisibilityCeiling.PROSPECTIVE,
                outcome_access=OutcomeAccess.EVALUATION_SEALED,
                lineage_parents=tuple(
                    _parent(value, OutcomeAccess.EVALUATION_SEALED)
                    for value in terminal.cell_receipts
                ),
            ),
        ),
    )
    return terminal
