"""Reusable scientific contracts and calculations; native effects are owned by the adapter."""

from __future__ import annotations
from dataclasses import dataclass
from enum import StrEnum
from typing import ClassVar
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_ids, require_sorted_unique_strings, validate_stable_id
from empirical_lawhood.domains.fusion.gym_torax_native.field_metadata_contracts import GymToraxFieldMetadataEpisodeRequest, GymToraxFieldMetadataNativeEpisode
from empirical_lawhood.domains.fusion.gym_torax_native.finite_action_recurrence_protocol import GymToraxFiniteActionRecurrenceCellStage, GymToraxFiniteActionRecurrenceCell, GymToraxFiniteActionRecurrenceProspectiveFreeze
from empirical_lawhood.domains.fusion.gym_torax_native.source_assessment_execution_records import GymToraxOperationalDisposition

class GymToraxFiniteActionRecurrenceTerminalAcquisitionDisposition(StrEnum):
    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"

@dataclass(frozen=True, slots=True)
class GymToraxFiniteActionRecurrenceCellAcquisitionReceipt(CanonicalRecord):
    "One immutable acquisition attempt for one frozen finite-action recurrence cell."

    SCHEMA: ClassVar[str] = (
        'empirical-lawhood/simulators/gym-torax-native/gym-torax-finite-action-recurrence-cell-acquisition-receipt'
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
        if self.freeze.object_schema != GymToraxFiniteActionRecurrenceProspectiveFreeze.SCHEMA:
            raise ValueError("Finite-action recurrence cell receipt binds another freeze schema")
        if self.cell.object_schema != GymToraxFiniteActionRecurrenceCell.SCHEMA:
            raise ValueError("Finite-action recurrence cell receipt binds another cell schema")
        if self.request.object_schema != GymToraxFieldMetadataEpisodeRequest.SCHEMA:
            raise ValueError("Finite-action recurrence cell receipt binds another request schema")
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes")
        if self.attempt_count != 1 or self.automatic_retry_performed:
            raise ValueError("Finite-action recurrence permits exactly one attempt and no automatic retry")
        if self.disposition is GymToraxOperationalDisposition.SUCCEEDED:
            if self.episode is None or self.reason_codes:
                raise ValueError(
                    "successful finite-action recurrence acquisition requires one exact episode"
                )
            if (
                self.episode.object_schema != GymToraxFieldMetadataNativeEpisode.SCHEMA
                or self.episode.object_id != self.expected_episode_id
            ):
                raise ValueError("Finite-action recurrence receipt episode identity differs")
        elif self.episode is not None or not self.reason_codes:
            raise ValueError("failed finite-action recurrence acquisition cannot claim an episode")
        if self.scientific_values_decoded:
            raise ValueError("Finite-action recurrence acquisition cannot decode scientific values")
        if (
            self.outcome_access is not OutcomeAccess.EVALUATION_REVEALED
            or self.visibility_ceiling is not VisibilityCeiling.OUTCOME_VISIBLE
            or self.evidence_ceiling is not EvidenceCeiling.MEASUREMENT
        ):
            raise ValueError("Finite-action recurrence receipt changes its selected-parent evidence lane")

@dataclass(frozen=True, slots=True)
class GymToraxFiniteActionRecurrenceTerminalAcquisitionReceipt(CanonicalRecord):
    """Exact terminal accounting for all 98 selected-parent cells."""

    SCHEMA: ClassVar[str] = (
        'empirical-lawhood/simulators/gym-torax-native/gym-torax-finite-action-recurrence-terminal-acquisition-receipt'
    )

    receipt_id: str
    freeze: ObjectIdentity
    cell_receipts: tuple[ObjectIdentity, ...]
    episodes: tuple[ObjectIdentity, ...]
    accounted_cell_count: int
    completed_episode_count: int
    failed_cell_count: int
    disposition: GymToraxFiniteActionRecurrenceTerminalAcquisitionDisposition
    reason_codes: tuple[str, ...]
    scientific_values_decoded: bool
    outcome_access: OutcomeAccess
    visibility_ceiling: VisibilityCeiling
    evidence_ceiling: EvidenceCeiling

    def __post_init__(self) -> None:
        validate_stable_id(self.receipt_id, field_name="receipt_id")
        if self.freeze.object_schema != GymToraxFiniteActionRecurrenceProspectiveFreeze.SCHEMA:
            raise ValueError("Finite-action recurrence terminal binds another freeze schema")
        require_sorted_unique_ids(
            self.cell_receipts,
            attribute="object_id",
            field_name="cell_receipts",
        )
        require_sorted_unique_ids(
            self.episodes, attribute="object_id", field_name="episodes"
        )
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes")
        if self.accounted_cell_count != 98 or len(self.cell_receipts) != 98:
            raise ValueError("Finite-action recurrence terminal requires all 98 cell receipts")
        if self.completed_episode_count != len(self.episodes):
            raise ValueError("Finite-action recurrence completed count differs from episode identities")
        if self.completed_episode_count + self.failed_cell_count != 98:
            raise ValueError("Finite-action recurrence terminal counts do not cover the frozen roster")
        if self.disposition is GymToraxFiniteActionRecurrenceTerminalAcquisitionDisposition.COMPLETE:
            if (
                self.completed_episode_count != 98
                or self.failed_cell_count
                or self.reason_codes
            ):
                raise ValueError("complete finite-action recurrence terminal requires all episodes")
        elif self.failed_cell_count <= 0 or not self.reason_codes:
            raise ValueError("incomplete finite-action recurrence terminal requires exact failed cells")
        if self.scientific_values_decoded:
            raise ValueError("Finite-action recurrence terminal cannot decode scientific values")
        if (
            self.outcome_access is not OutcomeAccess.EVALUATION_REVEALED
            or self.visibility_ceiling is not VisibilityCeiling.OUTCOME_VISIBLE
            or self.evidence_ceiling is not EvidenceCeiling.MEASUREMENT
        ):
            raise ValueError("Finite-action recurrence terminal changes its selected-parent evidence lane")

@dataclass(frozen=True, slots=True)
class GymToraxFiniteActionRecurrenceStageAcquisitionReceipt(CanonicalRecord):
    "Exact outcome-sealed terminal for one explicitly selected finite-action recurrence stage set."

    SCHEMA: ClassVar[str] = (
        'empirical-lawhood/simulators/gym-torax-native/gym-torax-finite-action-recurrence-stage-acquisition-receipt'
    )

    receipt_id: str
    freeze: ObjectIdentity
    stages: tuple[GymToraxFiniteActionRecurrenceCellStage, ...]
    cell_receipts: tuple[ObjectIdentity, ...]
    episodes: tuple[ObjectIdentity, ...]
    expected_cell_count: int
    completed_episode_count: int
    failed_cell_count: int
    disposition: GymToraxFiniteActionRecurrenceTerminalAcquisitionDisposition
    reason_codes: tuple[str, ...]
    scientific_values_decoded: bool
    outcome_access: OutcomeAccess
    visibility_ceiling: VisibilityCeiling
    evidence_ceiling: EvidenceCeiling

    def __post_init__(self) -> None:
        validate_stable_id(self.receipt_id, field_name="receipt_id")
        if self.freeze.object_schema != GymToraxFiniteActionRecurrenceProspectiveFreeze.SCHEMA:
            raise ValueError("Finite-action recurrence stage terminal binds another freeze")
        if (
            not self.stages
            or tuple(sorted(set(self.stages), key=lambda value: value.value))
            != self.stages
        ):
            raise ValueError("Finite-action recurrence stage terminal requires unique sorted stages")
        require_sorted_unique_ids(
            self.cell_receipts, attribute="object_id", field_name="cell_receipts"
        )
        require_sorted_unique_ids(
            self.episodes, attribute="object_id", field_name="episodes"
        )
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes")
        if self.expected_cell_count != len(self.cell_receipts):
            raise ValueError("Finite-action recurrence stage terminal omits an expected cell receipt")
        if self.completed_episode_count != len(self.episodes):
            raise ValueError(
                "Finite-action recurrence stage completed count differs from episode identities"
            )
        if (
            self.completed_episode_count + self.failed_cell_count
            != self.expected_cell_count
        ):
            raise ValueError("Finite-action recurrence stage terminal counts do not cover its roster")
        if self.disposition is GymToraxFiniteActionRecurrenceTerminalAcquisitionDisposition.COMPLETE:
            if self.failed_cell_count or self.reason_codes:
                raise ValueError("complete finite-action recurrence stage terminal cannot carry failures")
        elif self.failed_cell_count <= 0 or not self.reason_codes:
            raise ValueError("incomplete finite-action recurrence stage terminal requires exact failures")
        if self.scientific_values_decoded:
            raise ValueError("Finite-action recurrence stage acquisition cannot decode scientific values")
        if (
            self.outcome_access is not OutcomeAccess.EVALUATION_REVEALED
            or self.visibility_ceiling is not VisibilityCeiling.OUTCOME_VISIBLE
            or self.evidence_ceiling is not EvidenceCeiling.MEASUREMENT
        ):
            raise ValueError("Finite-action recurrence stage terminal changes its evidence lane")
