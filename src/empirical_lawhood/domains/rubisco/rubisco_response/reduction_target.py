# SPDX-License-Identifier: MPL-2.0
"""Retain the exact missing target selection instead of choosing a convenient matrix."""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_strings, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.finding_report import ReferenceFindingReport
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.rate_suppliers import RateSupplierSemantics
from empirical_lawhood.domains.rubisco.rubisco_response.reference_supply import ReferenceSensitivity


@dataclass(frozen=True, slots=True)
class ReductionTargetCandidate(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/reduction-target-candidate"
    case_id: str
    scenario_id: str
    parameter: str
    original_scenario_state: str
    supplier: RateSupplierSemantics | None
    local_sensitivity: ReferenceSensitivity | None
    local_meaning: str
    missing_requirement_ids: tuple[str, ...]

    def __post_init__(self):
        for value in (self.case_id, self.scenario_id, self.parameter):
            validate_stable_id(value)
        if self.original_scenario_state not in {"AVAILABLE", "FAILED", "UNKNOWN"}:
            raise ValueError("target candidate loses its original scenario state")
        if self.supplier is not None:
            exact(self.supplier, RateSupplierSemantics)
            if self.supplier.parameter != self.parameter:
                raise ValueError("target candidate changes the original rate supplier")
        if self.local_sensitivity is not None:
            exact(self.local_sensitivity, ReferenceSensitivity)
            if self.local_sensitivity.parameter != self.parameter:
                raise ValueError("target candidate changes its independently assessed sensitivity")
        expected = ("UNKNOWN" if self.local_sensitivity is None or self.local_sensitivity.maximum_absolute_derivatives is None
            else "LOCAL_SENSITIVITY_PRESENT_NOT_GLOBAL_PRIORITY" if any(value.fraction for value in self.local_sensitivity.maximum_absolute_derivatives)
            else "LOCALLY_ZERO_NOT_GLOBAL_EXCLUSION")
        if self.local_meaning != expected:
            raise ValueError("local sensitivity cannot be relabelled as global target justification")
        require_sorted_unique_strings(self.missing_requirement_ids, field_name="missing_requirement_ids", allow_empty=False)


def _candidates(report):
    references = {row.supply.case.case_id: row for row in report.references}
    result = []
    for supply in report.study.supplies:
        reference = references.get(supply.case.case_id)
        sensitivities = {} if reference is None else {row.parameter: row for row in reference.sensitivities}
        censuses = {} if reference is None else {row.ledger.identity: row for row in reference.supplier_censuses}
        for scenario in supply.scenarios:
            census = censuses.get(scenario.ledger.identity)
            for index, binding in enumerate(scenario.ledger.bindings):
                supplier = None if census is None else census.semantics[index]
                sensitivity = sensitivities.get(binding.parameter) if scenario.original_state == "AVAILABLE" else None
                meaning = ("UNKNOWN" if sensitivity is None or sensitivity.maximum_absolute_derivatives is None
                    else "LOCAL_SENSITIVITY_PRESENT_NOT_GLOBAL_PRIORITY" if any(value.fraction for value in sensitivity.maximum_absolute_derivatives)
                    else "LOCALLY_ZERO_NOT_GLOBAL_EXCLUSION")
                prefix = "requirement." + scenario.ledger.ledger_id + "." + binding.parameter
                pending = {prefix + ".actual-supplier-cost-or-consequential-uncertainty",
                    prefix + ".joint-receiver-error-connection", prefix + ".supplier-physical-applicability",
                    *binding.unresolved_requirement_ids}
                if reference is None:
                    pending.add("requirement." + supply.supply_id + ".independent-reference-analysis")
                else:
                    pending.update(reference.unresolved_requirement_ids)
                result.append(ReductionTargetCandidate(supply.case.case_id, scenario.scenario_id, binding.parameter,
                    scenario.original_state, supplier, sensitivity, meaning, tuple(sorted(pending))))
    return tuple(result)


@dataclass(frozen=True, slots=True)
class ReductionTargetAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/reduction-target-assessment"
    assessment_id: str
    reference_report: ReferenceFindingReport
    candidates: tuple[ReductionTargetCandidate, ...]
    remaining_requirement_ids: tuple[str, ...]
    selected_target: ObjectIdentity | None = None
    disposition: str = "HOLD_NO_JUSTIFIED_PRODUCTION_SUPPLIER"
    allowed_work: str = "TARGET_INDEPENDENT_CONTRACTS_AND_EXPOSED_ANALYTIC_CONTROLS_ONLY"

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        exact(self.reference_report, ReferenceFindingReport)
        if self.candidates != _candidates(self.reference_report):
            raise ValueError("target assessment drops zero, failed, unknown or consequential supplier candidates")
        expected = tuple(sorted({key for row in self.candidates for key in row.missing_requirement_ids}
            | {self.reference_report.study.acceptance.matrix_handoff_requirement_id}))
        if self.remaining_requirement_ids != expected:
            raise ValueError("target selection drops an exact source, cost, sensitivity or transfer prerequisite")
        # This retained-reference type explicitly has no admitted physical rate
        # supplier and no measured molecular-supplier profile. New evidence must
        # receive its own scientific assessment, not flip a field on this record.
        if (self.selected_target is not None or self.disposition != "HOLD_NO_JUSTIFIED_PRODUCTION_SUPPLIER"
                or self.allowed_work != "TARGET_INDEPENDENT_CONTRACTS_AND_EXPOSED_ANALYTIC_CONTROLS_ONLY"):
            raise ValueError("conditional reference analysis cannot justify a production approximation target")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.assessment_id, self)


def assess_reduction_target(report, *, assessment_id):
    exact(report, ReferenceFindingReport)
    candidates = _candidates(report)
    pending = tuple(sorted({key for row in candidates for key in row.missing_requirement_ids}
        | {report.study.acceptance.matrix_handoff_requirement_id}))
    return ReductionTargetAssessment(assessment_id, report, candidates, pending)
