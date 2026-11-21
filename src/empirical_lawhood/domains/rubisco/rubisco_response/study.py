# SPDX-License-Identifier: MPL-2.0
"""Complete paired case census and exposed analytical unit allocation."""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_prediction.paired_supply import PairedDecisionRegion
from empirical_lawhood.science.experiments.experimental_design import IndependentUnit, UnitAllocation, UnitRoleAssignment
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.acceptance import NominatedPrediction, ResponseAcceptance
from empirical_lawhood.domains.rubisco.rubisco_response.materials import RubiscoCaseSet, exact
from empirical_lawhood.domains.rubisco.rubisco_response.rate_contracts import PairedRateSupply

QUESTION = ("For the complete selected paired-material and model-alternative census, "
    "does the conditional joint kinetic support meet the frozen turnover and specificity decision, "
    "and which requirements still separate that result from validated prediction and computational benefit?")


def exposed_source_allocation(cases, supplies):
    """One analytical unit per original exposure group; nested views stay nested."""
    exact(cases, RubiscoCaseSet)
    groups = sorted({case.exposure_group for case in cases.cases})
    by_case = {supply.case.case_id: supply for supply in supplies}
    def views(group):
        result = []
        for case in cases.cases:
            if case.exposure_group == group:
                result.append(case.case_id)
                for scenario in by_case[case.case_id].scenarios:
                    result.append(case.case_id + "." + scenario.scenario_id)
                    result.extend(case.case_id + "." + scenario.scenario_id + "." + point.point_id
                                  for point in scenario.points)
        return tuple(sorted(result))
    units = tuple(IndependentUnit("unit." + group, cases.selection_id, group, views(group), True)
                  for group in groups)
    return UnitAllocation("allocation." + cases.selection_id, (cases.identity,), units,
        tuple(UnitRoleAssignment(unit.unit_id, "development") for unit in units))


@dataclass(frozen=True, slots=True)
class RubiscoResponseStudy(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/study"
    study_id: str
    cases: RubiscoCaseSet
    supplies: tuple[PairedRateSupply, ...]
    decisions: tuple[PairedDecisionRegion, ...]
    nominated_predictions: tuple[NominatedPrediction, ...]
    acceptance: ResponseAcceptance
    allocation: UnitAllocation
    evidence_scope: str = "EXPOSED_CONDITIONAL"
    question: str = QUESTION
    independent_biological_units: int = 0
    biological_predictive_calibration: str = "NOT_ESTABLISHED"

    def __post_init__(self):
        validate_stable_id(self.study_id)
        exact(self.cases, RubiscoCaseSet)
        if type(self.supplies) is not tuple or len(self.supplies) > 32:
            raise ValueError("study must retain a bounded complete supply census")
        if tuple(supply.case for supply in self.supplies) != self.cases.cases:
            raise ValueError("study drops or substitutes a complete selected paired case")
        for supply in self.supplies:
            exact(supply, PairedRateSupply)
        if sum(len(scenario.points) for supply in self.supplies for scenario in supply.scenarios) > 256:
            raise ValueError("study exceeds its complete finite point capacity")
        if (type(self.decisions) is not tuple or len(self.decisions) != len(self.supplies)
                or any((decision.case, decision.context) != (supply.case.identity, supply.context.identity)
                       for supply, decision in zip(self.supplies, self.decisions, strict=True))):
            raise ValueError("study must retain the exact decision for every paired case and context")
        for decision in self.decisions:
            exact(decision, PairedDecisionRegion)
        candidates = tuple(case for case in self.cases.cases if case.case_role == "CANDIDATE")
        if (not candidates or type(self.nominated_predictions) is not tuple
                or tuple(row.case for row in self.nominated_predictions) != tuple(case.identity for case in candidates)):
            raise ValueError("study must retain each candidate prediction separately from decision thresholds")
        for row, case in zip(self.nominated_predictions, candidates, strict=True):
            exact(row, NominatedPrediction)
            if row.exposure_group != case.exposure_group:
                raise ValueError("nominated prediction changes its prior exposure group")
        exact(self.acceptance, ResponseAcceptance)
        if self.acceptance.uncertainty_interpretation != "FINITE_JOINT_SUPPORT":
            raise ValueError("finite rate points cannot claim an unconstructed continuous or probabilistic region")
        exact(self.allocation, UnitAllocation)
        if self.allocation != exposed_source_allocation(self.cases, self.supplies):
            raise ValueError("exposed cases cannot become independent calibration or held-out validation units")
        if (self.evidence_scope not in {"EXPOSED_CONDITIONAL", "PROSPECTIVE_REQUIRED"}
                or self.question != QUESTION or type(self.independent_biological_units) is not int
                or self.independent_biological_units != 0 or self.biological_predictive_calibration != "NOT_ESTABLISHED"):
            raise ValueError("this study cannot confer biological calibration or change its combined milestone")
        if self.evidence_scope == "EXPOSED_CONDITIONAL" and self.acceptance.maximum_native_acquisitions != 0:
            raise ValueError("exposed response work requires a zero native-acquisition ceiling")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.study_id, self)
