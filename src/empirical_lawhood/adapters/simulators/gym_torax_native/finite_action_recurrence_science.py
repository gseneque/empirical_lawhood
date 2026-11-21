"""Native acquisition, external-format translation and custody integration."""

from __future__ import annotations
from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.design.study_issue import StudyAuthorityKind, StudyOperationAuthority, require_study_authority
from empirical_lawhood.storage.contracts.artifacts import ArtifactLineageParent
from empirical_lawhood.domains.fusion.gym_torax_native.finite_action_recurrence_execution_records import GymToraxFiniteActionRecurrenceStageAcquisitionReceipt
from empirical_lawhood.domains.fusion.gym_torax_native.finite_action_recurrence_protocol import GymToraxFiniteActionRecurrenceProspectiveFreeze
from empirical_lawhood.execution.gym_torax_custody import GymToraxArtifactPublicationItem, GymToraxBoundedArtifactStore

from empirical_lawhood.domains.fusion.gym_torax_native.finite_action_recurrence_science import (
    GymToraxFiniteActionRecurrenceQualificationBundle as _science_GymToraxFiniteActionRecurrenceQualificationBundle,
    GymToraxFiniteActionRecurrenceRecurrenceEvaluationBundle as _science_GymToraxFiniteActionRecurrenceRecurrenceEvaluationBundle,
    _identity,
)

def _require_hfr_custody(
    *,
    freeze: GymToraxFiniteActionRecurrenceProspectiveFreeze,
    authority: StudyOperationAuthority,
    store: GymToraxBoundedArtifactStore,
    at_utc: str,
) -> None:
    require_study_authority(
        authority,
        kind=StudyAuthorityKind.CUSTODY_PUBLICATION,
        subject=_identity(freeze.freeze_id, freeze),
        prerequisite_authority=None,
        grantee_id="operator.execution-service",
        storage_root_id=store.storage_root_id,
        relative_root=freeze.relative_root,
        at_utc=at_utc,
    )

def publish_gym_torax_finite_action_recurrence_qualification(
    *,
    freeze: GymToraxFiniteActionRecurrenceProspectiveFreeze,
    bundle: _science_GymToraxFiniteActionRecurrenceQualificationBundle,
    stage_terminal: GymToraxFiniteActionRecurrenceStageAcquisitionReceipt,
    custody_authority: StudyOperationAuthority,
    store: GymToraxBoundedArtifactStore,
    at_utc: str,
) -> ObjectIdentity:
    _require_hfr_custody(
        freeze=freeze,
        authority=custody_authority,
        store=store,
        at_utc=at_utc,
    )
    if bundle.freeze != _identity(freeze.freeze_id, freeze):
        raise ValueError("Finite-action recurrence qualification publication changes its freeze")
    parents = tuple(
        sorted(
            (
                ArtifactLineageParent(
                    identity=_identity(freeze.freeze_id, freeze),
                    visibility_ceiling=VisibilityCeiling.OUTCOME_VISIBLE,
                    outcome_access=OutcomeAccess.EVALUATION_REVEALED,
                ),
                ArtifactLineageParent(
                    identity=_identity(stage_terminal.receipt_id, stage_terminal),
                    visibility_ceiling=VisibilityCeiling.OUTCOME_VISIBLE,
                    outcome_access=OutcomeAccess.EVALUATION_REVEALED,
                ),
                ArtifactLineageParent(
                    identity=bundle.law_qualification_result,
                    visibility_ceiling=VisibilityCeiling.PROSPECTIVE,
                    outcome_access=OutcomeAccess.EVALUATOR_REVEAL,
                ),
            ),
            key=lambda value: value.identity.object_id,
        )
    )
    return store.publish_atomic(
        publication_scope_id='publication.tokamak-control.finite-action-qualification',
        publication_scope_relative_root=freeze.relative_root,
        implementation_sha256=freeze.implementation_source_closure.implementation_sha256,
        items=(
            GymToraxArtifactPublicationItem(
                logical_artifact_id='artifact.qualification-bundle.tokamak-control.finite-action-recurrence',
                relative_path=f"{freeze.relative_root}/science/qualification-bundle.json",
                record=bundle,
                visibility_ceiling=VisibilityCeiling.OUTCOME_VISIBLE,
                outcome_access=OutcomeAccess.EVALUATOR_REVEAL,
                lineage_parents=parents,
            ),
        ),
    )[0]

def publish_gym_torax_finite_action_recurrence_recurrence(
    *,
    freeze: GymToraxFiniteActionRecurrenceProspectiveFreeze,
    bundle: _science_GymToraxFiniteActionRecurrenceRecurrenceEvaluationBundle,
    custody_authority: StudyOperationAuthority,
    store: GymToraxBoundedArtifactStore,
    at_utc: str,
) -> ObjectIdentity:
    _require_hfr_custody(
        freeze=freeze,
        authority=custody_authority,
        store=store,
        at_utc=at_utc,
    )
    if bundle.freeze != _identity(freeze.freeze_id, freeze):
        raise ValueError("Finite-action recurrence publication changes its freeze")
    parents = tuple(
        sorted(
            (
                ArtifactLineageParent(
                    identity=bundle.qualification,
                    visibility_ceiling=VisibilityCeiling.OUTCOME_VISIBLE,
                    outcome_access=OutcomeAccess.EVALUATOR_REVEAL,
                ),
                ArtifactLineageParent(
                    identity=bundle.terminal_acquisition,
                    visibility_ceiling=VisibilityCeiling.OUTCOME_VISIBLE,
                    outcome_access=OutcomeAccess.EVALUATION_REVEALED,
                ),
            ),
            key=lambda value: value.identity.object_id,
        )
    )
    return store.publish_atomic(
        publication_scope_id='publication.tokamak-control.finite-action-recurrence',
        publication_scope_relative_root=freeze.relative_root,
        implementation_sha256=freeze.implementation_source_closure.implementation_sha256,
        items=(
            GymToraxArtifactPublicationItem(
                logical_artifact_id='artifact.evaluation-bundle.tokamak-control.finite-action-recurrence',
                relative_path=(
                    f"{freeze.relative_root}/science/recurrence-evaluation-bundle.json"
                ),
                record=bundle,
                visibility_ceiling=VisibilityCeiling.OUTCOME_VISIBLE,
                outcome_access=OutcomeAccess.EVALUATOR_REVEAL,
                lineage_parents=parents,
            ),
        ),
    )[0]
