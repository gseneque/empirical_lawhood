"""Reusable scientific records, designs and calculations extracted from native binding.

Native acquisition and external-format effects belong to the corresponding adapter.
Original scientific schemas and numerical definitions are preserved.
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import StrEnum
from typing import ClassVar
from empirical_lawhood.science.evidence.evidence import OutcomeAccess
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_strings, validate_stable_id
from empirical_lawhood.domains.energy.grid2op.contracts import Grid2OpSourceBinding


class Grid2OpSourceQualificationDisposition(StrEnum):
    PASS = "PASS"
    SOURCE_IDENTITY_MISMATCH = "SOURCE_IDENTITY_MISMATCH"
    ACTION_SURFACE_INCOMPLETE = "ACTION_SURFACE_INCOMPLETE"
    RESET_OR_REALIZATION_INCOMPLETE = "RESET_OR_REALIZATION_INCOMPLETE"
    OPERATIONAL_UNEVALUABLE = "OPERATIONAL_UNEVALUABLE"


@dataclass(frozen=True, slots=True)
class Grid2OpSourceQualification(CanonicalRecord):
    """Excluded source readiness follow-up qualification; never a target evidence unit."""

    SCHEMA: ClassVar[str] = 'empirical-lawhood/simulators/grid2op-response/grid2-op-source-qualification'

    qualification_id: str
    target_source: ObjectIdentity
    qualification_source: ObjectIdentity
    qualification_native_chronic_id: str
    supported_action_kind_ids: tuple[str, ...]
    target_action_kind_ids: tuple[str, ...]
    hold_observed: bool
    exact_reset_observed: bool
    requested_accepted_applied_realized_distinct: bool
    realized_action_observable: bool
    backend_step_count: int
    backend_error_count: int
    excluded_from_target_evidence: bool
    target_evidence_unit_count: int
    disposition: Grid2OpSourceQualificationDisposition
    reason_codes: tuple[str, ...]
    outcome_access: OutcomeAccess

    def __post_init__(self) -> None:
        validate_stable_id(self.qualification_id, field_name="qualification_id")
        if (
            self.target_source.object_schema != Grid2OpSourceBinding.SCHEMA
            or self.qualification_source.object_schema != Grid2OpSourceBinding.SCHEMA
        ):
            raise ValueError("Grid2Op qualification source identity differs")
        require_sorted_unique_strings(
            self.supported_action_kind_ids,
            field_name="supported_action_kind_ids",
            allow_empty=False,
        )
        require_sorted_unique_strings(
            self.target_action_kind_ids,
            field_name="target_action_kind_ids",
            allow_empty=False,
        )
        if not set(self.target_action_kind_ids) <= set(self.supported_action_kind_ids):
            raise ValueError("Grid2Op target action chart exceeds the qualified source")
        if "hold" not in self.target_action_kind_ids:
            raise ValueError("Grid2Op target action chart lacks mandatory hold")
        if self.backend_step_count <= 0 or self.backend_error_count < 0:
            raise ValueError("Grid2Op qualification step accounting is invalid")
        if (
            not self.excluded_from_target_evidence
            or self.target_evidence_unit_count
            or self.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
        ):
            raise ValueError("Grid2Op source qualification crossed target evidence")
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes")
        passed = all(
            (
                self.hold_observed,
                self.exact_reset_observed,
                self.requested_accepted_applied_realized_distinct,
                self.realized_action_observable,
                self.backend_error_count == 0,
                not self.reason_codes,
            )
        )
        if passed != (self.disposition is Grid2OpSourceQualificationDisposition.PASS):
            raise ValueError("Grid2Op qualification disposition is not fact-derived")
        if self.disposition is not Grid2OpSourceQualificationDisposition.PASS and (
            not self.reason_codes or self.disposition.value not in self.reason_codes
        ):
            raise ValueError("stopped Grid2Op qualification lacks its controlling reason")
