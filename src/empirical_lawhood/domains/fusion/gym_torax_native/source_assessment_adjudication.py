"""Reusable scientific contracts and calculations; native effects are owned by the adapter."""

from __future__ import annotations
from dataclasses import dataclass
from enum import StrEnum
from typing import ClassVar
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_ids, require_sorted_unique_strings, validate_stable_id
from empirical_lawhood.design.study_issue import StudyOperationAuthority
from empirical_lawhood.domains.fusion.gym_torax_native.diagnostic_contracts import GYM_TORAX_HORIZON_REQUESTS, GymToraxDeliveryDisposition, GymToraxNumericalDisposition, GymToraxObservationDisposition, GymToraxSourceDisposition
from empirical_lawhood.domains.fusion.gym_torax_native.field_metadata_contracts import GymToraxFieldMetadataNativeEpisode
from empirical_lawhood.domains.fusion.gym_torax_native.source_assessment_execution_records import GymToraxSourceAssessmentTerminalAcquisitionReceipt
from empirical_lawhood.domains.fusion.gym_torax_native.source_assessment_protocol import GymToraxSourceAssessmentCell, GymToraxSourceAssessmentFreeze, GYM_TORAX_FINITE_ACTION_RECURRENCE_BRANCH_ID, GYM_TORAX_PRIMARY_BRANCH_ID


CONTROLLED_IO_OPERATOR_API_UNAVAILABLE = "CONTROLLED_IO_OPERATOR_API_UNAVAILABLE"


CONTROLLED_IO_DERIVATIVE_SURFACE_UNAVAILABLE = (
    "CONTROLLED_IO_DERIVATIVE_SURFACE_UNAVAILABLE"
)


CONTROLLED_IO_EXCLUDED_SOURCE_REPEATABILITY_EVIDENCE_MISSING = (
    "CONTROLLED_IO_EXCLUDED_SOURCE_REPEATABILITY_EVIDENCE_MISSING"
)


CONTROLLED_IO_EXCLUDED_OPERATOR_SOURCE_DISPOSITION_INCONSISTENT = (
    "CONTROLLED_IO_EXCLUDED_OPERATOR_SOURCE_DISPOSITION_INCONSISTENT"
)


GYM_TORAX_SOURCE_ASSESSMENT_ORDINARY_READINESS_FAILED = "GYM_TORAX_SOURCE_ASSESSMENT_ORDINARY_READINESS_FAILED"




class GymToraxSourceAssessmentAdjudicationDisposition(StrEnum):
    SUPPORTED = "SUPPORTED"
    NOT_SUPPORTED = "NOT_SUPPORTED"
    UNEVALUABLE = "UNEVALUABLE"
    ORDINARY_FAILURE = "ORDINARY_FAILURE"

class GymToraxSourceAssessmentBranchSelectionDisposition(StrEnum):
    PRIMARY_SELECTED = "PRIMARY_SELECTED"
    FINITE_ACTION_RECURRENCE_SELECTED = "FINITE_ACTION_RECURRENCE_SELECTED"
    NO_SELECTION = "NO_SELECTION"

@dataclass(frozen=True, slots=True)
class GymToraxSourceAssessmentAdjudicationReceipt(CanonicalRecord):
    SCHEMA: ClassVar[str] = (
        'empirical-lawhood/simulators/gym-torax-native/gym-torax-source-assessment-adjudication-receipt'
    )

    receipt_id: str
    freeze: ObjectIdentity
    terminal_acquisition: ObjectIdentity
    reveal_authority: ObjectIdentity
    episode_ids: tuple[ObjectIdentity, ...]
    physical_independent_unit_count: int
    numerical_member_count: int
    action_word_count: int
    ordinary_readiness_passed: bool
    disposition: GymToraxSourceAssessmentAdjudicationDisposition
    g2_reason_code: str | None
    reason_codes: tuple[str, ...]
    scientific_arrays_materialized: bool
    outcome_access: OutcomeAccess
    visibility_ceiling: VisibilityCeiling
    evidence_ceiling: EvidenceCeiling

    def __post_init__(self) -> None:
        validate_stable_id(self.receipt_id, field_name="receipt_id")
        if self.freeze.object_schema != GymToraxSourceAssessmentFreeze.SCHEMA:
            raise ValueError("source assessment adjudication binds another freeze schema")
        if (
            self.terminal_acquisition.object_schema
            != GymToraxSourceAssessmentTerminalAcquisitionReceipt.SCHEMA
        ):
            raise ValueError("source assessment adjudication binds another terminal schema")
        if self.reveal_authority.object_schema != StudyOperationAuthority.SCHEMA:
            raise ValueError("source assessment adjudication lacks typed reveal authority")
        require_sorted_unique_ids(
            self.episode_ids,
            attribute="object_id",
            field_name="episode_ids",
        )
        if len(self.episode_ids) != 96:
            raise ValueError("source assessment adjudication requires exactly 96 episodes")
        if (
            self.physical_independent_unit_count != 12
            or self.numerical_member_count != 2
            or self.action_word_count != 4
        ):
            raise ValueError("source assessment adjudication changes the frozen nested design")
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes")
        if self.disposition is GymToraxSourceAssessmentAdjudicationDisposition.SUPPORTED:
            if (
                not self.ordinary_readiness_passed
                or self.g2_reason_code
                or self.reason_codes
            ):
                raise ValueError(
                    "supported source assessment requires complete ordinary and controlled-I/O feasibility evidence"
                )
        elif self.disposition is GymToraxSourceAssessmentAdjudicationDisposition.NOT_SUPPORTED:
            if (
                not self.ordinary_readiness_passed
                or self.g2_reason_code is None
                or self.reason_codes != (self.g2_reason_code,)
            ):
                raise ValueError("not-supported source assessment requires one closed controlled-I/O feasibility obstruction")
        elif self.disposition is GymToraxSourceAssessmentAdjudicationDisposition.ORDINARY_FAILURE:
            if self.ordinary_readiness_passed or self.g2_reason_code is not None:
                raise ValueError("ordinary source assessment failure cannot claim a controlled-I/O feasibility result")
        elif not self.ordinary_readiness_passed or self.g2_reason_code is not None:
            raise ValueError(
                "unevaluable controlled-I/O feasibility requires ordinary readiness and no obstruction"
            )
        if (
            self.disposition is not GymToraxSourceAssessmentAdjudicationDisposition.SUPPORTED
            and not self.reason_codes
        ):
            raise ValueError("non-supported source assessment adjudication requires exact reasons")
        if self.scientific_arrays_materialized:
            raise ValueError(
                "bounded source assessment adjudication cannot materialize scientific arrays"
            )
        if (
            self.outcome_access is not OutcomeAccess.EVALUATION_REVEALED
            or self.visibility_ceiling is not VisibilityCeiling.OUTCOME_VISIBLE
            or self.evidence_ceiling is not EvidenceCeiling.NON_PROMOTABLE
        ):
            raise ValueError("source assessment adjudication changes its nonpromotable reveal boundary")

@dataclass(frozen=True, slots=True)
class GymToraxSourceAssessmentBranchSelectionReceipt(CanonicalRecord):
    SCHEMA: ClassVar[str] = (
        'empirical-lawhood/simulators/gym-torax-native/gym-torax-source-assessment-branch-selection-receipt'
    )

    receipt_id: str
    freeze: ObjectIdentity
    adjudication: ObjectIdentity
    branch_rule: ObjectIdentity
    disposition: GymToraxSourceAssessmentBranchSelectionDisposition
    selected_branch_id: str | None
    selected_parent_episode_count: int
    controlling_reason_code: str | None
    hfr_contract_evidence: tuple[ObjectIdentity, ...]
    parent_issue_started: bool
    outcome_access: OutcomeAccess
    visibility_ceiling: VisibilityCeiling
    evidence_ceiling: EvidenceCeiling

    def __post_init__(self) -> None:
        validate_stable_id(self.receipt_id, field_name="receipt_id")
        if self.freeze.object_schema != GymToraxSourceAssessmentFreeze.SCHEMA:
            raise ValueError("branch selection binds another source assessment freeze")
        if self.adjudication.object_schema != GymToraxSourceAssessmentAdjudicationReceipt.SCHEMA:
            raise ValueError("branch selection binds another source assessment adjudication")
        require_sorted_unique_ids(
            self.hfr_contract_evidence,
            attribute="object_id",
            field_name="hfr_contract_evidence",
        )
        if self.disposition is GymToraxSourceAssessmentBranchSelectionDisposition.PRIMARY_SELECTED:
            if (
                self.selected_branch_id != GYM_TORAX_PRIMARY_BRANCH_ID
                or self.controlling_reason_code is not None
                or self.hfr_contract_evidence
            ):
                raise ValueError("PRIMARY selection changes its frozen rule")
        elif self.disposition is GymToraxSourceAssessmentBranchSelectionDisposition.FINITE_ACTION_RECURRENCE_SELECTED:
            if (
                self.selected_branch_id != GYM_TORAX_FINITE_ACTION_RECURRENCE_BRANCH_ID
                or self.controlling_reason_code is None
                or not self.hfr_contract_evidence
            ):
                raise ValueError(
                    "finite-action recurrence selection lacks its obstruction and static closure"
                )
        elif (
            self.selected_branch_id is not None
            or self.controlling_reason_code is not None
            or self.hfr_contract_evidence
        ):
            raise ValueError("no-selection receipt cannot imply a branch")
        if self.selected_parent_episode_count != (
            576 if self.selected_branch_id else 0
        ):
            raise ValueError("branch selection changes the conditional parent roster")
        if self.parent_issue_started:
            raise ValueError("branch receipt cannot claim parent issue")
        if (
            self.outcome_access is not OutcomeAccess.EVALUATION_REVEALED
            or self.visibility_ceiling is not VisibilityCeiling.OUTCOME_VISIBLE
            or self.evidence_ceiling is not EvidenceCeiling.NON_PROMOTABLE
        ):
            raise ValueError("branch receipt lowers its revealed outcome ceiling")

def _ordinary_episode_ready(
    cell: GymToraxSourceAssessmentCell,
    episode: GymToraxFieldMetadataNativeEpisode,
) -> bool:
    expected_clocks = tuple(range(GYM_TORAX_HORIZON_REQUESTS + 1))
    if (
        not episode.source_reset_attempted
        or episode.state_clocks != expected_clocks
        or episode.missing_required_state_clocks
        or episode.last_valid_state_clock != GYM_TORAX_HORIZON_REQUESTS
        or episode.source_disposition is not GymToraxSourceDisposition.AVAILABLE
        or episode.delivery_disposition is not GymToraxDeliveryDisposition.COMPLETE
        or episode.numerical_disposition is not GymToraxNumericalDisposition.VALID
        or episode.observation_disposition
        is not GymToraxObservationDisposition.COMPLETE
        or episode.termination
        or episode.truncation
        or len(episode.deliveries) != GYM_TORAX_HORIZON_REQUESTS
        or not episode.blocks
        or any(value.nonfinite_value_count for value in episode.blocks)
    ):
        return False
    by_clock = {value.request_clock: value for value in episode.deliveries}
    if len(by_clock) != GYM_TORAX_HORIZON_REQUESTS:
        return False
    for row in cell.request.schedule.rows:
        delivery = by_clock.get(row.request_clock)
        if (
            delivery is None
            or delivery.receiver_clock != row.request_clock + 1
            or delivery.occurrence_id != row.controlled_occurrence_id
            or delivery.disposition is not GymToraxDeliveryDisposition.COMPLETE
            or delivery.requested != row.action
            or delivery.accepted != row.action
            or delivery.applied != row.action
            or delivery.realized is None
        ):
            return False
    return True

def _classify(
    episodes: tuple[GymToraxFieldMetadataNativeEpisode, ...],
    *,
    ordinary_ready: bool,
) -> tuple[GymToraxSourceAssessmentAdjudicationDisposition, str | None, tuple[str, ...]]:
    if not ordinary_ready:
        return (
            GymToraxSourceAssessmentAdjudicationDisposition.ORDINARY_FAILURE,
            None,
            (GYM_TORAX_SOURCE_ASSESSMENT_ORDINARY_READINESS_FAILED,),
        )
    dispositions = {value.operator_source.disposition for value in episodes}
    if dispositions == {GymToraxSourceDisposition.OPERATOR_API_UNAVAILABLE}:
        return (
            GymToraxSourceAssessmentAdjudicationDisposition.NOT_SUPPORTED,
            CONTROLLED_IO_OPERATOR_API_UNAVAILABLE,
            (CONTROLLED_IO_OPERATOR_API_UNAVAILABLE,),
        )
    if dispositions == {GymToraxSourceDisposition.SOURCE_UNAVAILABLE}:
        return (
            GymToraxSourceAssessmentAdjudicationDisposition.NOT_SUPPORTED,
            CONTROLLED_IO_DERIVATIVE_SURFACE_UNAVAILABLE,
            (CONTROLLED_IO_DERIVATIVE_SURFACE_UNAVAILABLE,),
        )
    if dispositions == {GymToraxSourceDisposition.AVAILABLE}:
        return (
            GymToraxSourceAssessmentAdjudicationDisposition.UNEVALUABLE,
            None,
            (CONTROLLED_IO_EXCLUDED_SOURCE_REPEATABILITY_EVIDENCE_MISSING,),
        )
    return (
        GymToraxSourceAssessmentAdjudicationDisposition.UNEVALUABLE,
        None,
        (CONTROLLED_IO_EXCLUDED_OPERATOR_SOURCE_DISPOSITION_INCONSISTENT,),
    )
