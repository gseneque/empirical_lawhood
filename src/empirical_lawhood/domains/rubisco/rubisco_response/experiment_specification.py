# SPDX-License-Identifier: MPL-2.0
"""Editable candidate criteria over separately retained immutable source inputs."""

from dataclasses import dataclass, replace
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_prediction.paired_supply import PairedDecisionRegion
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_strings, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.acceptance import ResponseAcceptance
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.study import QUESTION, RubiscoResponseStudy

PROTOCOL_ID = "rubisco-response-experiment-v1"


@dataclass(frozen=True, slots=True)
class RubiscoResponseExperimentSpecification(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/experiment-specification"
    specification_id: str
    study: ObjectIdentity
    expected_case_ids: tuple[str, ...]
    expected_scenarios: tuple[tuple[str, tuple[str, ...]], ...]
    expected_analytical_unit_ids: tuple[str, ...]
    decisions: tuple[PairedDecisionRegion, ...]
    acceptance: ResponseAcceptance
    permitted_refinement_id: str | None = None
    evidence_scope: str = "EXPOSED_CONDITIONAL"
    question: str = QUESTION

    def __post_init__(self):
        validate_stable_id(self.specification_id)
        exact(self.study, ObjectIdentity)
        if self.study.object_schema != RubiscoResponseStudy.SCHEMA or self.study.object_version != RubiscoResponseStudy.VERSION:
            raise ValueError("experiment selection changes the exact original study")
        require_sorted_unique_strings(self.expected_case_ids, field_name="expected_case_ids", allow_empty=False)
        require_sorted_unique_strings(self.expected_analytical_unit_ids, field_name="expected_analytical_unit_ids", allow_empty=False)
        if (type(self.expected_scenarios) is not tuple
                or tuple(key for key, _ in self.expected_scenarios) != self.expected_case_ids):
            raise ValueError("experiment selection must retain each case's complete scenario census")
        for _, scenarios in self.expected_scenarios:
            require_sorted_unique_strings(scenarios, field_name="scenario_ids", allow_empty=False)
        if type(self.decisions) is not tuple or tuple(row.case.object_id for row in self.decisions) != self.expected_case_ids:
            raise ValueError("experiment selection must retain every paired candidate criterion")
        for row in self.decisions:
            exact(row, PairedDecisionRegion)
        exact(self.acceptance, ResponseAcceptance)
        if self.permitted_refinement_id is not None and self.permitted_refinement_id not in self.acceptance.permitted_refinement_ids:
            raise ValueError("selected refinement is outside the frozen finite menu")
        if self.evidence_scope not in {"EXPOSED_CONDITIONAL", "PROSPECTIVE_REQUIRED"} or self.question != QUESTION:
            raise ValueError("experiment selection changes its evidence lane or combined scientific question")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.specification_id, self)


def validate_unchanged_sources(original, selected):
    """Allow explicit criterion edits; preserve evidence, units and prior use."""
    exact(original, RubiscoResponseStudy)
    exact(selected, RubiscoResponseStudy)
    if any(getattr(original, name) != getattr(selected, name)
           for name in ("cases", "supplies", "nominated_predictions", "allocation", "question",
                        "independent_biological_units", "biological_predictive_calibration")):
        raise ValueError("response selection changes immutable paired evidence, exposure or original nomination")
    left, right = original.acceptance, selected.acceptance
    if (left.predictive_evidence_requirement_ids != right.predictive_evidence_requirement_ids
            or left.gp_applicability_requirement_id != right.gp_applicability_requirement_id
            or left.matrix_handoff_requirement_id != right.matrix_handoff_requirement_id
            or not set(left.criterion_admission_requirement_ids).issubset(right.criterion_admission_requirement_ids)):
        raise ValueError("criterion edit drops an original scientific admission or validation requirement")


def select_response_study(specification, original):
    exact(specification, RubiscoResponseExperimentSpecification)
    exact(original, RubiscoResponseStudy)
    if original.identity != specification.study:
        raise ValueError("response experiment substitutes its original source study bytes")
    if (tuple(case.case_id for case in original.cases.cases) != specification.expected_case_ids
            or tuple((supply.case.case_id, supply.expected_scenario_ids) for supply in original.supplies)
            != specification.expected_scenarios
            or original.allocation.unit_ids() != specification.expected_analytical_unit_ids):
        raise ValueError("response experiment changes the complete original case or scenario denominator")
    selected = replace(original, study_id="study.rubisco-response." + specification.fingerprint(),
        decisions=specification.decisions, acceptance=specification.acceptance,
        evidence_scope=specification.evidence_scope)
    validate_unchanged_sources(original, selected)
    return selected


def response_experiment_specification(study, *, specification_id="specification.rubisco-response.exposed",
                                      decisions=None, acceptance=None, evidence_scope="EXPOSED_CONDITIONAL"):
    exact(study, RubiscoResponseStudy)
    return RubiscoResponseExperimentSpecification(specification_id, study.identity,
        tuple(case.case_id for case in study.cases.cases),
        tuple((supply.case.case_id, supply.expected_scenario_ids) for supply in study.supplies),
        study.allocation.unit_ids(), study.decisions if decisions is None else decisions, study.acceptance if acceptance is None else acceptance,
        evidence_scope=evidence_scope)
