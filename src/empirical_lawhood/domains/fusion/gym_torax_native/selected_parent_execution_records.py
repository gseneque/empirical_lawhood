"""Reusable scientific contracts and calculations; native effects are owned by the adapter."""

from __future__ import annotations
from dataclasses import dataclass
from enum import StrEnum
from typing import ClassVar
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_ids, require_sorted_unique_strings, validate_stable_id
from empirical_lawhood.domains.fusion.gym_torax_native.field_metadata_contracts import GymToraxFieldMetadataEpisodeRequest, GymToraxFieldMetadataNativeEpisode
from empirical_lawhood.domains.fusion.gym_torax_native.selected_parent_protocol import GymToraxSelectedParentCell, GymToraxSelectedParentFreeze
from empirical_lawhood.domains.fusion.gym_torax_native.source_assessment_execution_records import GymToraxOperationalDisposition

class GymToraxSelectedParentTerminalAcquisitionDisposition(StrEnum):
    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"

@dataclass(frozen=True, slots=True)
class GymToraxSelectedParentCellAcquisitionReceipt(CanonicalRecord):
    "One immutable acquisition attempt for one frozen response qualification cell."

    SCHEMA: ClassVar[str] = (
        'empirical-lawhood/simulators/gym-torax-native/gym-torax-selected-parent-cell-acquisition-receipt'
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
        if self.freeze.object_schema != GymToraxSelectedParentFreeze.SCHEMA:
            raise ValueError("Response qualification cell receipt binds another freeze schema")
        if self.cell.object_schema != GymToraxSelectedParentCell.SCHEMA:
            raise ValueError("Response qualification cell receipt binds another cell schema")
        if self.request.object_schema != GymToraxFieldMetadataEpisodeRequest.SCHEMA:
            raise ValueError("Response qualification cell receipt binds another request schema")
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes")
        if self.attempt_count != 1 or self.automatic_retry_performed:
            raise ValueError(
                "Response qualification permits exactly one attempt and no automatic retry"
            )
        if self.disposition is GymToraxOperationalDisposition.SUCCEEDED:
            if self.episode is None or self.reason_codes:
                raise ValueError(
                    "successful response qualification acquisition requires one exact episode"
                )
            if (
                self.episode.object_schema != GymToraxFieldMetadataNativeEpisode.SCHEMA
                or self.episode.object_id != self.expected_episode_id
            ):
                raise ValueError("Response qualification receipt episode identity differs")
        elif self.episode is not None or not self.reason_codes:
            raise ValueError("failed response qualification acquisition cannot claim an episode")
        if self.scientific_values_decoded:
            raise ValueError("Response qualification acquisition cannot decode scientific values")
        if (
            self.outcome_access is not OutcomeAccess.EVALUATION_REVEALED
            or self.visibility_ceiling is not VisibilityCeiling.OUTCOME_VISIBLE
            or self.evidence_ceiling is not EvidenceCeiling.MEASUREMENT
        ):
            raise ValueError("Response qualification receipt changes its selected-parent evidence lane")

@dataclass(frozen=True, slots=True)
class GymToraxSelectedParentTerminalAcquisitionReceipt(CanonicalRecord):
    """Exact terminal accounting for all 576 selected-parent cells."""

    SCHEMA: ClassVar[str] = (
        'empirical-lawhood/simulators/gym-torax-native/gym-torax-selected-parent-terminal-acquisition-receipt'
    )

    receipt_id: str
    freeze: ObjectIdentity
    cell_receipts: tuple[ObjectIdentity, ...]
    episodes: tuple[ObjectIdentity, ...]
    accounted_cell_count: int
    completed_episode_count: int
    failed_cell_count: int
    disposition: GymToraxSelectedParentTerminalAcquisitionDisposition
    reason_codes: tuple[str, ...]
    scientific_values_decoded: bool
    outcome_access: OutcomeAccess
    visibility_ceiling: VisibilityCeiling
    evidence_ceiling: EvidenceCeiling

    def __post_init__(self) -> None:
        validate_stable_id(self.receipt_id, field_name="receipt_id")
        if self.freeze.object_schema != GymToraxSelectedParentFreeze.SCHEMA:
            raise ValueError("Response qualification terminal binds another freeze schema")
        require_sorted_unique_ids(
            self.cell_receipts,
            attribute="object_id",
            field_name="cell_receipts",
        )
        require_sorted_unique_ids(
            self.episodes, attribute="object_id", field_name="episodes"
        )
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes")
        if self.accounted_cell_count != 576 or len(self.cell_receipts) != 576:
            raise ValueError("Response qualification terminal requires all 576 cell receipts")
        if self.completed_episode_count != len(self.episodes):
            raise ValueError("Response qualification completed count differs from episode identities")
        if self.completed_episode_count + self.failed_cell_count != 576:
            raise ValueError("Response qualification terminal counts do not cover the frozen roster")
        if self.disposition is GymToraxSelectedParentTerminalAcquisitionDisposition.COMPLETE:
            if (
                self.completed_episode_count != 576
                or self.failed_cell_count
                or self.reason_codes
            ):
                raise ValueError("complete response qualification terminal requires all episodes")
        elif self.failed_cell_count <= 0 or not self.reason_codes:
            raise ValueError("incomplete response qualification terminal requires exact failed cells")
        if self.scientific_values_decoded:
            raise ValueError("Response qualification terminal cannot decode scientific values")
        if (
            self.outcome_access is not OutcomeAccess.EVALUATION_REVEALED
            or self.visibility_ceiling is not VisibilityCeiling.OUTCOME_VISIBLE
            or self.evidence_ceiling is not EvidenceCeiling.MEASUREMENT
        ):
            raise ValueError(
                "Response qualification terminal changes its selected-parent evidence lane"
            )
