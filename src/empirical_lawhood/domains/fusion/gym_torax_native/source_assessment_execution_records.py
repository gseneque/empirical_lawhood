"""Reusable scientific contracts and calculations; native effects are owned by the adapter."""

from __future__ import annotations
from dataclasses import dataclass
from enum import StrEnum
from typing import ClassVar
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_ids, require_sorted_unique_strings, validate_stable_id
from empirical_lawhood.domains.fusion.gym_torax_native.field_metadata_contracts import GymToraxFieldMetadataNativeEpisode
from empirical_lawhood.domains.fusion.gym_torax_native.source_assessment_protocol import GymToraxSourceAssessmentCell, GymToraxSourceAssessmentFreeze, GymToraxNativeMetadataCanaryFreeze

class GymToraxOperationalDisposition(StrEnum):
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"

class GymToraxSourceAssessmentTerminalAcquisitionDisposition(StrEnum):
    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"

@dataclass(frozen=True, slots=True)
class GymToraxNativeCanaryRunReceipt(CanonicalRecord):
    SCHEMA: ClassVar[str] = (
        'empirical-lawhood/simulators/gym-torax-native/gym-torax-native-canary-run-receipt'
    )

    receipt_id: str
    freeze: ObjectIdentity
    request: ObjectIdentity
    episode: ObjectIdentity | None
    metadata_canary: ObjectIdentity | None
    source_qualification: ObjectIdentity | None
    disposition: GymToraxOperationalDisposition
    reason_codes: tuple[str, ...]
    source_reset_attempted: bool
    scientific_values_decoded: bool
    outcome_access: OutcomeAccess
    visibility_ceiling: VisibilityCeiling
    evidence_ceiling: EvidenceCeiling
    grants_source_assessment_freeze_authority: bool
    grants_source_assessment_execution_authority: bool

    def __post_init__(self) -> None:
        validate_stable_id(self.receipt_id, field_name="receipt_id")
        if self.freeze.object_schema != GymToraxNativeMetadataCanaryFreeze.SCHEMA:
            raise ValueError("canary run receipt binds another freeze schema")
        if (
            self.request.object_schema
            != 'empirical-lawhood/simulators/gym-torax-native/gym-torax-field-metadata-episode-request'
        ):
            raise ValueError("canary run receipt binds another request schema")
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes")
        complete = all(
            value is not None
            for value in (self.episode, self.metadata_canary, self.source_qualification)
        )
        if self.disposition is GymToraxOperationalDisposition.SUCCEEDED:
            if not complete or self.reason_codes or not self.source_reset_attempted:
                raise ValueError(
                    "successful canary run requires its complete passing closure"
                )
        elif not self.reason_codes:
            raise ValueError("failed canary run requires typed reasons")
        presence_count = sum(
            value is not None
            for value in (self.episode, self.metadata_canary, self.source_qualification)
        )
        if presence_count not in {0, 3}:
            raise ValueError(
                "canary run receipt cannot retain a partial artifact closure"
            )
        if self.scientific_values_decoded:
            raise ValueError("metadata canary cannot decode scientific values")
        if self.outcome_access is not OutcomeAccess.OUTCOME_BLIND:
            raise ValueError("metadata canary run must remain outcome-blind")
        if self.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE:
            raise ValueError("metadata canary run must remain prospective")
        if self.evidence_ceiling is not EvidenceCeiling.NON_PROMOTABLE:
            raise ValueError("metadata canary run cannot promote science")
        if self.grants_source_assessment_freeze_authority or self.grants_source_assessment_execution_authority:
            raise ValueError("metadata canary run receipt cannot grant authority")

@dataclass(frozen=True, slots=True)
class GymToraxSourceAssessmentCellAcquisitionReceipt(CanonicalRecord):
    SCHEMA: ClassVar[str] = (
        'empirical-lawhood/simulators/gym-torax-native/gym-torax-source-assessment-cell-acquisition-receipt'
    )

    receipt_id: str
    freeze: ObjectIdentity
    cell: ObjectIdentity
    request: ObjectIdentity
    expected_episode_id: str
    episode: ObjectIdentity | None
    disposition: GymToraxOperationalDisposition
    reason_codes: tuple[str, ...]
    attempt_count: int
    automatic_retry_performed: bool
    source_reset_attempted: bool
    scientific_values_decoded: bool
    outcome_access: OutcomeAccess
    visibility_ceiling: VisibilityCeiling
    evidence_ceiling: EvidenceCeiling

    def __post_init__(self) -> None:
        validate_stable_id(self.receipt_id, field_name="receipt_id")
        validate_stable_id(self.expected_episode_id, field_name="expected_episode_id")
        if self.freeze.object_schema != GymToraxSourceAssessmentFreeze.SCHEMA:
            raise ValueError("source assessment cell receipt binds another freeze schema")
        if self.cell.object_schema != GymToraxSourceAssessmentCell.SCHEMA:
            raise ValueError("source assessment cell receipt binds another cell schema")
        if (
            self.request.object_schema
            != 'empirical-lawhood/simulators/gym-torax-native/gym-torax-field-metadata-episode-request'
        ):
            raise ValueError("source assessment cell receipt binds another request schema")
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes")
        if self.attempt_count != 1 or self.automatic_retry_performed:
            raise ValueError(
                "bounded source assessment permits exactly one attempt and no automatic retry"
            )
        if self.disposition is GymToraxOperationalDisposition.SUCCEEDED:
            if self.episode is None or self.reason_codes:
                raise ValueError("successful source assessment acquisition requires one exact episode")
            if (
                self.episode.object_schema != GymToraxFieldMetadataNativeEpisode.SCHEMA
                or self.episode.object_id != self.expected_episode_id
            ):
                raise ValueError("source assessment cell receipt episode identity differs")
        elif self.episode is not None or not self.reason_codes:
            raise ValueError("failed source assessment acquisition cannot claim an episode")
        if self.scientific_values_decoded:
            raise ValueError("source assessment acquisition receipt cannot decode scientific values")
        if self.outcome_access is not OutcomeAccess.EVALUATION_SEALED:
            raise ValueError("source assessment acquisition receipt must remain evaluation-sealed")
        if self.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE:
            raise ValueError("source assessment acquisition receipt must remain prospectively sealed")
        if self.evidence_ceiling is not EvidenceCeiling.NON_PROMOTABLE:
            raise ValueError("source assessment acquisition receipt cannot promote science")

@dataclass(frozen=True, slots=True)
class GymToraxSourceAssessmentTerminalAcquisitionReceipt(CanonicalRecord):
    SCHEMA: ClassVar[str] = (
        'empirical-lawhood/simulators/gym-torax-native/gym-torax-source-assessment-terminal-acquisition-receipt'
    )

    receipt_id: str
    freeze: ObjectIdentity
    cell_receipts: tuple[ObjectIdentity, ...]
    episodes: tuple[ObjectIdentity, ...]
    accounted_cell_count: int
    completed_episode_count: int
    failed_cell_count: int
    disposition: GymToraxSourceAssessmentTerminalAcquisitionDisposition
    reason_codes: tuple[str, ...]
    scientific_values_decoded: bool
    outcome_access: OutcomeAccess
    visibility_ceiling: VisibilityCeiling
    evidence_ceiling: EvidenceCeiling

    def __post_init__(self) -> None:
        validate_stable_id(self.receipt_id, field_name="receipt_id")
        if self.freeze.object_schema != GymToraxSourceAssessmentFreeze.SCHEMA:
            raise ValueError("source assessment terminal receipt binds another freeze schema")
        require_sorted_unique_ids(
            self.cell_receipts,
            attribute="object_id",
            field_name="cell_receipts",
        )
        require_sorted_unique_ids(
            self.episodes, attribute="object_id", field_name="episodes"
        )
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes")
        if self.accounted_cell_count != 96 or len(self.cell_receipts) != 96:
            raise ValueError("source assessment terminal acquisition requires all 96 cell receipts")
        if self.completed_episode_count != len(self.episodes):
            raise ValueError(
                "source assessment terminal completed count differs from episode identities"
            )
        if self.completed_episode_count + self.failed_cell_count != 96:
            raise ValueError("source assessment terminal counts do not cover the frozen roster")
        if self.disposition is GymToraxSourceAssessmentTerminalAcquisitionDisposition.COMPLETE:
            if (
                self.completed_episode_count != 96
                or self.failed_cell_count
                or self.reason_codes
            ):
                raise ValueError("complete source assessment terminal requires all 96 episodes")
        elif self.failed_cell_count <= 0 or not self.reason_codes:
            raise ValueError("incomplete source assessment terminal requires exact failed cells")
        if self.scientific_values_decoded:
            raise ValueError("source assessment terminal acquisition cannot decode scientific values")
        if self.outcome_access is not OutcomeAccess.EVALUATION_SEALED:
            raise ValueError("source assessment terminal acquisition must remain sealed")
        if self.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE:
            raise ValueError("source assessment terminal acquisition must remain prospective")
        if self.evidence_ceiling is not EvidenceCeiling.NON_PROMOTABLE:
            raise ValueError("source assessment terminal acquisition cannot promote science")
