"""Native acquisition, external-format translation and custody integration."""

from __future__ import annotations
from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.design.study_issue import StudyAuthorityKind, StudyOperationAuthority, require_study_authority
from empirical_lawhood.storage.contracts.artifacts import ArtifactManifest
from empirical_lawhood.storage.contracts.artifacts import ArtifactLineageParent
from empirical_lawhood.domains.fusion.gym_torax_native.selected_parent_execution_records import GymToraxSelectedParentTerminalAcquisitionDisposition, GymToraxSelectedParentTerminalAcquisitionReceipt
from empirical_lawhood.domains.fusion.gym_torax_native.selected_parent_protocol import GymToraxSelectedParentFreeze
from empirical_lawhood.execution.gym_torax_custody import GymToraxArtifactPublicationItem, GymToraxBoundedArtifactStore

from empirical_lawhood.domains.fusion.gym_torax_native.selected_parent_science import (
    GYM_TORAX_MATCHED_EVALUATION_SCIENCE_EVALUATION_LOGICAL_ID as _science_GYM_TORAX_MATCHED_EVALUATION_SCIENCE_EVALUATION_LOGICAL_ID,
    GYM_TORAX_MATCHED_EVALUATION_SCIENCE_FREEZE_LOGICAL_ID as _science_GYM_TORAX_MATCHED_EVALUATION_SCIENCE_FREEZE_LOGICAL_ID,
    GymToraxSelectedParentScienceEvaluationBundle as _science_GymToraxSelectedParentScienceEvaluationBundle,
    GymToraxSelectedParentScienceFreeze as _science_GymToraxSelectedParentScienceFreeze,
    _episode_logical_id,
    _episode_object_identity,
    _identity,
)

def publish_gym_torax_response_experiment_science_freeze(
    *,
    science_freeze: _science_GymToraxSelectedParentScienceFreeze,
    acquisition_freeze: GymToraxSelectedParentFreeze,
    acquisition_terminal: GymToraxSelectedParentTerminalAcquisitionReceipt,
    episode_manifests: tuple[ArtifactManifest, ...],
    custody_authority: StudyOperationAuthority,
    store: GymToraxBoundedArtifactStore,
    at_utc: str,
) -> ObjectIdentity:
    """Publish the topology-only science freeze without revealing episode bytes."""

    if (
        acquisition_terminal.freeze
        != _identity(acquisition_freeze.freeze_id, acquisition_freeze)
        or acquisition_terminal.disposition
        is not GymToraxSelectedParentTerminalAcquisitionDisposition.COMPLETE
        or acquisition_terminal.completed_episode_count != 576
        or acquisition_terminal.failed_cell_count
    ):
        raise ValueError(
            "Gym-TORAX science freeze requires complete terminal acquisition accounting"
        )
    require_study_authority(
        custody_authority,
        kind=StudyAuthorityKind.CUSTODY_PUBLICATION,
        subject=_identity(acquisition_freeze.freeze_id, acquisition_freeze),
        prerequisite_authority=None,
        grantee_id="operator.execution-service",
        storage_root_id=store.storage_root_id,
        relative_root=acquisition_freeze.relative_root,
        at_utc=at_utc,
    )
    manifests = {
        value.logical.logical_artifact_id: value for value in episode_manifests
    }
    expected = {
        _episode_logical_id(value)
        for value in science_freeze.expected_primary_episode_ids
    }
    if set(manifests) != expected:
        raise ValueError(
            "Gym-TORAX science freeze publication changes its 144 sidecar roster"
        )
    parents = [
        ArtifactLineageParent(
            identity=science_freeze.prospective_protocol_parent,
            visibility_ceiling=VisibilityCeiling.PROSPECTIVE,
            outcome_access=OutcomeAccess.OUTCOME_BLIND,
        ),
        ArtifactLineageParent(
            identity=science_freeze.source_campaign_roster,
            visibility_ceiling=VisibilityCeiling.PROSPECTIVE,
            outcome_access=OutcomeAccess.OUTCOME_BLIND,
        ),
        ArtifactLineageParent(
            identity=science_freeze.source_qualification,
            visibility_ceiling=VisibilityCeiling.PROSPECTIVE,
            outcome_access=OutcomeAccess.OUTCOME_BLIND,
        ),
    ]
    parents.extend(
        ArtifactLineageParent(
            identity=_episode_object_identity(
                manifests[_episode_logical_id(episode_id)], episode_id
            ),
            visibility_ceiling=VisibilityCeiling.PROSPECTIVE,
            outcome_access=OutcomeAccess.EVALUATION_SEALED,
        )
        for episode_id in science_freeze.expected_primary_episode_ids
    )
    return store.publish_atomic(
        publication_scope_id='publication.tokamak-control.matched-evaluation-science',
        publication_scope_relative_root=acquisition_freeze.relative_root,
        implementation_sha256=(
            science_freeze.implementation_source_closure.implementation_sha256
        ),
        items=(
            GymToraxArtifactPublicationItem(
                logical_artifact_id=_science_GYM_TORAX_MATCHED_EVALUATION_SCIENCE_FREEZE_LOGICAL_ID,
                relative_path=f"{science_freeze.relative_root}/science-freeze.json",
                record=science_freeze,
                visibility_ceiling=VisibilityCeiling.PROSPECTIVE,
                outcome_access=OutcomeAccess.EVALUATION_SEALED,
                lineage_parents=tuple(
                    sorted(parents, key=lambda value: value.identity.object_id)
                ),
            ),
        ),
    )[0]

def publish_gym_torax_response_experiment_science_evaluation(
    *,
    science_freeze: _science_GymToraxSelectedParentScienceFreeze,
    acquisition_freeze: GymToraxSelectedParentFreeze,
    bundle: _science_GymToraxSelectedParentScienceEvaluationBundle,
    episode_manifests: tuple[ArtifactManifest, ...],
    custody_authority: StudyOperationAuthority,
    store: GymToraxBoundedArtifactStore,
    at_utc: str,
) -> ObjectIdentity:
    """Publish the exact prospective evaluator bundle after generic finalization."""

    require_study_authority(
        custody_authority,
        kind=StudyAuthorityKind.CUSTODY_PUBLICATION,
        subject=_identity(acquisition_freeze.freeze_id, acquisition_freeze),
        prerequisite_authority=None,
        grantee_id="operator.execution-service",
        storage_root_id=store.storage_root_id,
        relative_root=acquisition_freeze.relative_root,
        at_utc=at_utc,
    )
    if bundle.science_freeze != _identity(science_freeze.freeze_id, science_freeze):
        raise ValueError("Gym-TORAX evaluation publication names another science freeze")
    manifests = {
        value.logical.logical_artifact_id: value for value in episode_manifests
    }
    if set(manifests) != {
        _episode_logical_id(value)
        for value in science_freeze.expected_primary_episode_ids
    }:
        raise ValueError("Gym-TORAX evaluation publication changes its 144 sidecar roster")
    parents = [
        ArtifactLineageParent(
            identity=_identity(science_freeze.freeze_id, science_freeze),
            visibility_ceiling=VisibilityCeiling.PROSPECTIVE,
            outcome_access=OutcomeAccess.EVALUATION_SEALED,
        )
    ]
    parents.extend(
        ArtifactLineageParent(
            identity=_episode_object_identity(
                manifests[_episode_logical_id(episode_id)], episode_id
            ),
            visibility_ceiling=VisibilityCeiling.PROSPECTIVE,
            outcome_access=OutcomeAccess.EVALUATION_SEALED,
        )
        for episode_id in science_freeze.expected_primary_episode_ids
    )
    return store.publish_atomic(
        publication_scope_id='publication.tokamak-control.matched-evaluation-evaluation',
        publication_scope_relative_root=acquisition_freeze.relative_root,
        implementation_sha256=(
            science_freeze.implementation_source_closure.implementation_sha256
        ),
        items=(
            GymToraxArtifactPublicationItem(
                logical_artifact_id=_science_GYM_TORAX_MATCHED_EVALUATION_SCIENCE_EVALUATION_LOGICAL_ID,
                relative_path=f"{science_freeze.relative_root}/evaluation-bundle.json",
                record=bundle,
                visibility_ceiling=VisibilityCeiling.PROSPECTIVE,
                outcome_access=OutcomeAccess.EVALUATOR_REVEAL,
                lineage_parents=tuple(
                    sorted(parents, key=lambda value: value.identity.object_id)
                ),
            ),
        ),
    )[0]
