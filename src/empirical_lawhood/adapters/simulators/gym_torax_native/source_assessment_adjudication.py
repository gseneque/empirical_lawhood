"""Native acquisition, external-format translation and custody integration."""

from __future__ import annotations
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.design.study_issue import StudyAuthorityKind, StudyOperationAuthority, require_study_authority
from empirical_lawhood.storage.contracts.artifacts import ArtifactLineageParent
from empirical_lawhood.domains.fusion.gym_torax_native.field_metadata_contracts import GymToraxFieldMetadataNativeEpisode
from empirical_lawhood.execution.gym_torax_custody import GymToraxArtifactPublicationItem, GymToraxBoundedArtifactStore
from empirical_lawhood.domains.fusion.gym_torax_native.source_assessment_execution_records import GymToraxSourceAssessmentTerminalAcquisitionDisposition, GymToraxSourceAssessmentTerminalAcquisitionReceipt
from empirical_lawhood.domains.fusion.gym_torax_native.source_assessment_protocol import GymToraxSourceAssessmentCell, GymToraxSourceAssessmentFreeze

from empirical_lawhood.domains.fusion.gym_torax_native.source_assessment_adjudication import (
    GymToraxSourceAssessmentAdjudicationDisposition as _science_GymToraxSourceAssessmentAdjudicationDisposition,
    GymToraxSourceAssessmentAdjudicationReceipt as _science_GymToraxSourceAssessmentAdjudicationReceipt,
    GymToraxSourceAssessmentBranchSelectionDisposition as _science_GymToraxSourceAssessmentBranchSelectionDisposition,
    GymToraxSourceAssessmentBranchSelectionReceipt as _science_GymToraxSourceAssessmentBranchSelectionReceipt,
    _classify,
    _ordinary_episode_ready,
)


GYM_TORAX_SOURCE_ASSESSMENT_ADJUDICATION_RECEIPT_ID = 'result.tokamak-control.source-assessment.g2'

GYM_TORAX_SOURCE_ASSESSMENT_BRANCH_SELECTION_RECEIPT_ID = 'selection.tokamak-control.source-assessment'






_EXECUTION_GRANTEE_ID = "operator.execution-service"

_EVALUATOR_GRANTEE_ID = "operator.evaluator-service"

def _identity(identifier: str, record: CanonicalRecord) -> ObjectIdentity:
    return ObjectIdentity.from_record(identifier, record)

def _parent(
    identity: ObjectIdentity,
    *,
    visibility: VisibilityCeiling,
    access: OutcomeAccess,
) -> ArtifactLineageParent:
    return ArtifactLineageParent(
        identity=identity,
        visibility_ceiling=visibility,
        outcome_access=access,
    )

def _terminal_logical_id(freeze: GymToraxSourceAssessmentFreeze) -> str:
    return f"artifact.{freeze.run_id}.run-receipt"

def _episode_logical_id(episode_id: str) -> str:
    return f"artifact.{episode_id}"

def _episode_path(freeze: GymToraxSourceAssessmentFreeze, episode_id: str) -> str:
    return f"{freeze.relative_root}/episodes/{episode_id}.json"

def _adjudication_logical_id() -> str:
    return f'artifact.{GYM_TORAX_SOURCE_ASSESSMENT_ADJUDICATION_RECEIPT_ID}'

def _selection_logical_id() -> str:
    return f'artifact.{GYM_TORAX_SOURCE_ASSESSMENT_BRANCH_SELECTION_RECEIPT_ID}'

def _require_evaluation_authorities(
    *,
    freeze: GymToraxSourceAssessmentFreeze,
    terminal: GymToraxSourceAssessmentTerminalAcquisitionReceipt,
    execution_authority: StudyOperationAuthority,
    reveal_authority: StudyOperationAuthority,
    custody_authority: StudyOperationAuthority,
    store: GymToraxBoundedArtifactStore,
    at_utc: str,
) -> None:
    freeze_identity = _identity(freeze.freeze_id, freeze)
    require_study_authority(
        execution_authority,
        kind=StudyAuthorityKind.EXPERIMENT_EXECUTION,
        subject=freeze_identity,
        prerequisite_authority=freeze.scientific_approval,
        grantee_id=_EXECUTION_GRANTEE_ID,
        at_utc=at_utc,
    )
    execution_identity = _identity(
        execution_authority.authority_id, execution_authority
    )
    require_study_authority(
        reveal_authority,
        kind=StudyAuthorityKind.OUTCOME_REVEAL,
        subject=_identity(terminal.receipt_id, terminal),
        prerequisite_authority=execution_identity,
        grantee_id=_EVALUATOR_GRANTEE_ID,
        at_utc=at_utc,
    )
    require_study_authority(
        custody_authority,
        kind=StudyAuthorityKind.CUSTODY_PUBLICATION,
        subject=freeze_identity,
        prerequisite_authority=None,
        grantee_id=_EXECUTION_GRANTEE_ID,
        storage_root_id=store.storage_root_id,
        relative_root=freeze.relative_root,
        at_utc=at_utc,
    )
    required = set(freeze.required_operation_authority_ids)
    if {
        execution_authority.authority_id,
        reveal_authority.authority_id,
        custody_authority.authority_id,
    } - required:
        raise PermissionError("source assessment evaluation authority ID is outside the freeze")
    if execution_authority.allows_actuation or reveal_authority.allows_actuation:
        raise PermissionError("Gym-TORAX simulator evaluation cannot permit actuation")

def _require_episode_lineage(
    *,
    freeze: GymToraxSourceAssessmentFreeze,
    cell: GymToraxSourceAssessmentCell,
    episode: GymToraxFieldMetadataNativeEpisode,
) -> None:
    request = cell.request
    if (
        episode.episode_id != cell.episode_id
        or episode.request != _identity(request.request_id, request)
        or episode.preparation
        != _identity(request.preparation.preparation_id, request.preparation)
        or episode.numerical_member
        != _identity(request.numerical_member.member_id, request.numerical_member)
        or episode.action_word
        != _identity(request.schedule.action_word.word_id, request.schedule.action_word)
        or episode.extraction_manifest != freeze.extraction_manifest
        or episode.field_metadata_manifest != freeze.field_metadata_manifest
        or episode.outcome_access is not OutcomeAccess.EVALUATION_SEALED
        or episode.evidence_ceiling is not EvidenceCeiling.NON_PROMOTABLE
    ):
        raise ValueError("source assessment episode lineage differs from the frozen cell")

def evaluate_gym_torax_q(
    *,
    freeze: GymToraxSourceAssessmentFreeze,
    terminal: GymToraxSourceAssessmentTerminalAcquisitionReceipt,
    execution_authority: StudyOperationAuthority,
    reveal_authority: StudyOperationAuthority,
    custody_authority: StudyOperationAuthority,
    store: GymToraxBoundedArtifactStore,
    at_utc: str,
) -> _science_GymToraxSourceAssessmentAdjudicationReceipt:
    "Reveal and classify exact source assessment status, without numerical array access."

    if (
        terminal.freeze != _identity(freeze.freeze_id, freeze)
        or terminal.disposition is not GymToraxSourceAssessmentTerminalAcquisitionDisposition.COMPLETE
    ):
        raise ValueError(
            "source assessment evaluation requires the exact complete terminal acquisition"
        )
    persisted_terminal = store.load_optional(
        logical_artifact_id=_terminal_logical_id(freeze),
        relative_path=f"{freeze.relative_root}/run-receipt.json",
        record_type=GymToraxSourceAssessmentTerminalAcquisitionReceipt,
        maximum_bytes=4 * 1024**2,
    )
    if persisted_terminal != terminal:
        raise ValueError("source assessment terminal acquisition is not persisted exactly")
    _require_evaluation_authorities(
        freeze=freeze,
        terminal=terminal,
        execution_authority=execution_authority,
        reveal_authority=reveal_authority,
        custody_authority=custody_authority,
        store=store,
        at_utc=at_utc,
    )
    result_path = f"{freeze.relative_root}/adjudication/source-assessment-result.json"
    recovered = store.load_optional(
        logical_artifact_id=_adjudication_logical_id(),
        relative_path=result_path,
        record_type=_science_GymToraxSourceAssessmentAdjudicationReceipt,
        maximum_bytes=4 * 1024**2,
    )
    if recovered is not None:
        if recovered.terminal_acquisition != _identity(terminal.receipt_id, terminal):
            raise ValueError(
                "recovered source assessment adjudication changes its terminal acquisition"
            )
        return recovered

    episodes: list[GymToraxFieldMetadataNativeEpisode] = []
    for cell in freeze.cells:
        episode = store.load_optional(
            logical_artifact_id=_episode_logical_id(cell.episode_id),
            relative_path=_episode_path(freeze, cell.episode_id),
            record_type=GymToraxFieldMetadataNativeEpisode,
            maximum_bytes=cell.request.maximum_output_bytes,
        )
        if episode is None:
            raise ValueError("complete source assessment terminal lacks an exact episode")
        _require_episode_lineage(freeze=freeze, cell=cell, episode=episode)
        episodes.append(episode)
    episode_tuple = tuple(episodes)
    episode_identities = tuple(
        sorted(
            (_identity(value.episode_id, value) for value in episode_tuple),
            key=lambda value: value.object_id,
        )
    )
    if episode_identities != terminal.episodes:
        raise ValueError("source assessment episode roster differs from terminal acquisition")
    ordinary_ready = all(
        _ordinary_episode_ready(cell, episode)
        for cell, episode in zip(freeze.cells, episode_tuple, strict=True)
    )
    disposition, g2_reason, reasons = _classify(
        episode_tuple,
        ordinary_ready=ordinary_ready,
    )
    result = _science_GymToraxSourceAssessmentAdjudicationReceipt(
        receipt_id=GYM_TORAX_SOURCE_ASSESSMENT_ADJUDICATION_RECEIPT_ID,
        freeze=_identity(freeze.freeze_id, freeze),
        terminal_acquisition=_identity(terminal.receipt_id, terminal),
        reveal_authority=_identity(reveal_authority.authority_id, reveal_authority),
        episode_ids=episode_identities,
        physical_independent_unit_count=len(
            {value.physical_unit_instance_id for value in freeze.cells}
        ),
        numerical_member_count=len(
            {value.request.numerical_member.member_id for value in freeze.cells}
        ),
        action_word_count=len(
            {value.request.schedule.action_word.word_id for value in freeze.cells}
        ),
        ordinary_readiness_passed=ordinary_ready,
        disposition=disposition,
        g2_reason_code=g2_reason,
        reason_codes=reasons,
        scientific_arrays_materialized=False,
        outcome_access=OutcomeAccess.EVALUATION_REVEALED,
        visibility_ceiling=VisibilityCeiling.OUTCOME_VISIBLE,
        evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
    )
    store.publish_atomic(
        publication_scope_id=f"publication.{freeze.run_id}.adjudication",
        publication_scope_relative_root=freeze.relative_root,
        implementation_sha256=freeze.implementation_source_closure.implementation_sha256,
        items=(
            GymToraxArtifactPublicationItem(
                logical_artifact_id=_adjudication_logical_id(),
                relative_path=result_path,
                record=result,
                visibility_ceiling=VisibilityCeiling.OUTCOME_VISIBLE,
                outcome_access=OutcomeAccess.EVALUATION_REVEALED,
                lineage_parents=tuple(
                    sorted(
                        (
                            _parent(
                                _identity(terminal.receipt_id, terminal),
                                visibility=VisibilityCeiling.PROSPECTIVE,
                                access=OutcomeAccess.EVALUATION_SEALED,
                            ),
                            _parent(
                                _identity(
                                    reveal_authority.authority_id, reveal_authority
                                ),
                                visibility=VisibilityCeiling.PROSPECTIVE,
                                access=OutcomeAccess.EVALUATOR_REVEAL,
                            ),
                        ),
                        key=lambda value: value.identity.object_id,
                    )
                ),
            ),
        ),
    )
    return result

def select_gym_torax_q_branch(
    *,
    freeze: GymToraxSourceAssessmentFreeze,
    adjudication: _science_GymToraxSourceAssessmentAdjudicationReceipt,
    custody_authority: StudyOperationAuthority,
    store: GymToraxBoundedArtifactStore,
    at_utc: str,
) -> _science_GymToraxSourceAssessmentBranchSelectionReceipt:
    "Apply only the branch rule frozen before source assessment; never issue a parent."

    if adjudication.freeze != _identity(freeze.freeze_id, freeze):
        raise ValueError("branch selection adjudication binds another freeze")
    persisted = store.load_optional(
        logical_artifact_id=_adjudication_logical_id(),
        relative_path=f"{freeze.relative_root}/adjudication/source-assessment-result.json",
        record_type=_science_GymToraxSourceAssessmentAdjudicationReceipt,
        maximum_bytes=4 * 1024**2,
    )
    if persisted != adjudication:
        raise ValueError("branch selection requires the exact persisted source assessment adjudication")
    require_study_authority(
        custody_authority,
        kind=StudyAuthorityKind.CUSTODY_PUBLICATION,
        subject=_identity(freeze.freeze_id, freeze),
        prerequisite_authority=None,
        grantee_id=_EXECUTION_GRANTEE_ID,
        storage_root_id=store.storage_root_id,
        relative_root=freeze.relative_root,
        at_utc=at_utc,
    )
    if custody_authority.authority_id not in freeze.required_operation_authority_ids:
        raise PermissionError(
            "branch-selection custody authority is outside the freeze"
        )
    selection_path = f"{freeze.relative_root}/adjudication/branch-selection.json"
    recovered = store.load_optional(
        logical_artifact_id=_selection_logical_id(),
        relative_path=selection_path,
        record_type=_science_GymToraxSourceAssessmentBranchSelectionReceipt,
        maximum_bytes=2 * 1024**2,
    )
    if recovered is not None:
        if recovered.adjudication != _identity(adjudication.receipt_id, adjudication):
            raise ValueError("recovered branch selection changes its source assessment adjudication")
        return recovered

    if adjudication.disposition is _science_GymToraxSourceAssessmentAdjudicationDisposition.SUPPORTED:
        branch_disposition = _science_GymToraxSourceAssessmentBranchSelectionDisposition.PRIMARY_SELECTED
        selected_branch_id = freeze.branch_rule.primary_branch_id
        controlling_reason = None
        hfr_evidence: tuple[ObjectIdentity, ...] = ()
    elif (
        adjudication.disposition is _science_GymToraxSourceAssessmentAdjudicationDisposition.NOT_SUPPORTED
        and adjudication.g2_reason_code
        in freeze.branch_rule.alternate_reason_code_precedence
    ):
        branch_disposition = _science_GymToraxSourceAssessmentBranchSelectionDisposition.FINITE_ACTION_RECURRENCE_SELECTED
        selected_branch_id = freeze.branch_rule.alternate_branch_id
        controlling_reason = adjudication.g2_reason_code
        hfr_evidence = freeze.branch_rule.hfr_contract_evidence
    else:
        branch_disposition = _science_GymToraxSourceAssessmentBranchSelectionDisposition.NO_SELECTION
        selected_branch_id = None
        controlling_reason = None
        hfr_evidence = ()
    selection = _science_GymToraxSourceAssessmentBranchSelectionReceipt(
        receipt_id=GYM_TORAX_SOURCE_ASSESSMENT_BRANCH_SELECTION_RECEIPT_ID,
        freeze=_identity(freeze.freeze_id, freeze),
        adjudication=_identity(adjudication.receipt_id, adjudication),
        branch_rule=_identity(freeze.branch_rule.rule_id, freeze.branch_rule),
        disposition=branch_disposition,
        selected_branch_id=selected_branch_id,
        selected_parent_episode_count=576 if selected_branch_id else 0,
        controlling_reason_code=controlling_reason,
        hfr_contract_evidence=hfr_evidence,
        parent_issue_started=False,
        outcome_access=OutcomeAccess.EVALUATION_REVEALED,
        visibility_ceiling=VisibilityCeiling.OUTCOME_VISIBLE,
        evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
    )
    store.publish_atomic(
        publication_scope_id=f"publication.{freeze.run_id}.selection",
        publication_scope_relative_root=freeze.relative_root,
        implementation_sha256=freeze.implementation_source_closure.implementation_sha256,
        items=(
            GymToraxArtifactPublicationItem(
                logical_artifact_id=_selection_logical_id(),
                relative_path=selection_path,
                record=selection,
                visibility_ceiling=VisibilityCeiling.OUTCOME_VISIBLE,
                outcome_access=OutcomeAccess.EVALUATION_REVEALED,
                lineage_parents=tuple(
                    sorted(
                        (
                            _parent(
                                _identity(adjudication.receipt_id, adjudication),
                                visibility=VisibilityCeiling.OUTCOME_VISIBLE,
                                access=OutcomeAccess.EVALUATION_REVEALED,
                            ),
                            _parent(
                                _identity(freeze.freeze_id, freeze),
                                visibility=VisibilityCeiling.PROSPECTIVE,
                                access=OutcomeAccess.OUTCOME_BLIND,
                            ),
                        ),
                        key=lambda value: value.identity.object_id,
                    )
                ),
            ),
        ),
    )
    return selection
