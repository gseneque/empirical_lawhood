# SPDX-License-Identifier: MPL-2.0
"""Complete descriptive policy service censuses, with unresolved truth retained.

These records consume explicitly selected audit operands. They do not establish
receipt authenticity, reference validity, causal commitment or a population
confidence bound. The integrated comparison reader owns those joins separately.
"""

from dataclasses import dataclass
from fractions import Fraction
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_insilico_mechanism.contracts import Exact
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.policy_indicator import OUTPUTS, exact_vector
from empirical_lawhood.domains.rubisco.rubisco_response.study import RubiscoResponseStudy


@dataclass(frozen=True, slots=True)
class PolicyAuditObservation(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/policy-audit-observation"
    case: ObjectIdentity
    decision: ObjectIdentity | None
    action: str
    reduced_state: str
    reference_state: str
    reference_assessment: ObjectIdentity | None
    normalized_absolute_error_bounds: tuple[tuple[Exact, Exact], ...] | None

    def __post_init__(self):
        exact(self.case, ObjectIdentity)
        if self.decision is not None:
            exact(self.decision, ObjectIdentity)
        if self.action not in {"REDUCED", "REFERENCE", "REFINE", "HOLD", "UNKNOWN"}:
            raise ValueError("audit loses its original policy action")
        if self.action != "UNKNOWN" and self.decision is None:
            raise ValueError("a known policy action requires its original decision identity")
        if self.reduced_state not in {"AVAILABLE", "FAILED", "UNKNOWN", "NOT_ENTERED"} or self.reference_state not in {
                "ASSESSED_VALID", "FAILED", "UNKNOWN", "NOT_ENTERED"}:
            raise ValueError("audit must retain failed, unknown and unentered reduced/reference outcomes")
        if self.reference_assessment is not None:
            exact(self.reference_assessment, ObjectIdentity)
        if self.reference_state == "ASSESSED_VALID" and self.reference_assessment is None:
            raise ValueError("valid reference claim needs its original independent assessment")
        bounds = self.normalized_absolute_error_bounds
        if bounds is not None:
            if self.reference_state != "ASSESSED_VALID" or self.reduced_state != "AVAILABLE":
                raise ValueError("unknown or failed operands cannot acquire a measured error")
            if type(bounds) is not tuple or len(bounds) != len(OUTPUTS):
                raise ValueError("audit must retain both absolute arms and paired errors")
            for pair in bounds:
                exact_vector(pair, 2, nonnegative=True)
                if pair[0].fraction > pair[1].fraction:
                    raise ValueError("audit error enclosure is reversed")

    @property
    def joint_error(self):
        if self.normalized_absolute_error_bounds is None:
            return "UNRESOLVED"
        if any(pair[0].fraction > 1 for pair in self.normalized_absolute_error_bounds):
            return "FAILED"
        return "WITHIN" if all(pair[1].fraction <= 1 for pair in self.normalized_absolute_error_bounds) else "UNRESOLVED"


@dataclass(frozen=True, slots=True)
class PolicyUnitAudit(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/policy-unit-audit"
    unit_id: str
    case_ids: tuple[str, ...]
    useful_service: tuple[int, int]
    admitted: tuple[int, int]
    false_admission: tuple[int, int]
    fallback: tuple[int, int]
    reference_complete: bool

    def __post_init__(self):
        validate_stable_id(self.unit_id)
        if not self.case_ids or self.case_ids != tuple(sorted(set(self.case_ids))):
            raise ValueError("unit audit drops its exact nested case census")
        for pair in (self.useful_service, self.admitted, self.false_admission, self.fallback):
            if type(pair) is not tuple or len(pair) != 2 or any(type(value) is not int for value in pair) or not 0 <= pair[0] <= pair[1] <= 1:
                raise ValueError("unit-level known/possible event bounds are invalid")
        if type(self.reference_complete) is not bool:
            raise ValueError("reference audit coverage must be explicit")


def _units(study, observations):
    actual = {row.case.object_id: row for row in observations}
    result = []
    for unit in study.allocation.units:
        cases = tuple(case.case_id for case in study.cases.cases if case.case_id in unit.numerical_view_ids)
        rows = tuple(actual[key] for key in cases)
        lower = int(all(row.action == "REDUCED" and row.joint_error == "WITHIN" for row in rows))
        upper = int(all(row.action in {"REDUCED", "UNKNOWN"} and row.joint_error != "FAILED"
            and row.reduced_state not in {"FAILED", "NOT_ENTERED"} for row in rows))
        admitted = (int(any(row.action == "REDUCED" for row in rows)), int(any(row.action in {"REDUCED", "UNKNOWN"} for row in rows)))
        false = (int(any(row.action == "REDUCED" and row.joint_error == "FAILED" for row in rows)),
                 int(any(row.action in {"REDUCED", "UNKNOWN"} and row.joint_error != "WITHIN" for row in rows)))
        fallback = (int(any(row.action == "REFERENCE" for row in rows)), int(any(row.action in {"REFERENCE", "UNKNOWN"} for row in rows)))
        result.append(PolicyUnitAudit(unit.unit_id, cases, (lower, upper), admitted, false, fallback,
            all(row.reference_state == "ASSESSED_VALID" for row in rows)))
    return tuple(result)


def _rate(bounds, denominator):
    return tuple(Exact.of(Fraction(value, denominator)) for value in bounds)


def _verdict(bounds, criterion, *, minimum):
    if bounds is None:
        return A.UNEVALUABLE
    low, high = (row.fraction for row in bounds)
    if minimum:
        return A.SATISFIED if low >= criterion else A.FALSIFIED if high < criterion else A.UNEVALUABLE
    return A.SATISFIED if high <= criterion else A.FALSIFIED if low > criterion else A.UNEVALUABLE


def _service_values(study, observations, denominator):
    units = _units(study, observations)
    count = len(units)
    summed = {name: tuple(sum(getattr(row, name)[i] for row in units) for i in (0, 1))
              for name in ("useful_service", "admitted", "false_admission", "fallback")}
    service = _rate(summed["useful_service"], count)
    assigned_false = _rate(summed["false_admission"], count)
    admitted = summed["admitted"]
    conditional_false = None if admitted[1] == 0 else (
        Exact.of(Fraction(summed["false_admission"][0], admitted[1])),
        Exact.of(1 if admitted[0] == 0 else min(Fraction(1), Fraction(summed["false_admission"][1], admitted[0]))))
    chosen = assigned_false if denominator == "ALL_ASSIGNED_UNITS" else conditional_false
    return (units, service, assigned_false, conditional_false, _rate(summed["fallback"], count),
        _verdict(service, Fraction(study.acceptance.minimum_useful_service), minimum=True),
        _verdict(chosen, Fraction(study.acceptance.maximum_false_admission), minimum=False),
        A.SATISFIED if all(row.reference_complete for row in units) else A.UNEVALUABLE)


@dataclass(frozen=True, slots=True)
class PolicyServiceAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/policy-service-assessment"
    assessment_id: str
    study: RubiscoResponseStudy
    observations: tuple[PolicyAuditObservation, ...]
    false_admission_denominator: str
    units: tuple[PolicyUnitAudit, ...]
    useful_service_bounds: tuple[Exact, Exact]
    false_admission_assigned_bounds: tuple[Exact, Exact]
    false_admission_conditional_bounds: tuple[Exact, Exact] | None
    fallback_bounds: tuple[Exact, Exact]
    useful_service_disposition: A
    false_admission_disposition: A
    reference_coverage_disposition: A
    claim_scope: str = "DESCRIPTIVE_COMPLETE_EXPOSURE_GROUP_CENSUS_NOT_POPULATION_COVERAGE_OR_AUTHENTICATION"
    new_independent_biological_units: int = 0

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        exact(self.study, RubiscoResponseStudy)
        if type(self.observations) is not tuple or tuple(row.case for row in self.observations) != tuple(row.identity for row in self.study.cases.cases):
            raise ValueError("policy audit must retain every selected case, including refusal and missing truth")
        for row in self.observations:
            exact(row, PolicyAuditObservation)
        if self.false_admission_denominator not in {"ALL_ASSIGNED_UNITS", "ADMITTED_UNITS"}:
            raise ValueError("false-admission criterion needs its explicitly frozen denominator")
        actual = (self.units, self.useful_service_bounds, self.false_admission_assigned_bounds,
            self.false_admission_conditional_bounds, self.fallback_bounds, self.useful_service_disposition,
            self.false_admission_disposition, self.reference_coverage_disposition)
        if actual != _service_values(self.study, self.observations, self.false_admission_denominator):
            raise ValueError("service audit changes the full denominator, nested dependence or unknown-reference bounds")
        if (self.claim_scope != "DESCRIPTIVE_COMPLETE_EXPOSURE_GROUP_CENSUS_NOT_POPULATION_COVERAGE_OR_AUTHENTICATION"
                or type(self.new_independent_biological_units) is not int or self.new_independent_biological_units != 0):
            raise ValueError("descriptive policy counts cannot establish causal authentication, confidence or fresh biology")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.assessment_id, self)


def assess_policy_service(study, observations, *, false_admission_denominator, assessment_id):
    exact(study, RubiscoResponseStudy)
    if type(observations) is not tuple or tuple(row.case for row in observations) != tuple(row.identity for row in study.cases.cases):
        raise ValueError("policy audit must retain every selected case, including refusal and missing truth")
    for row in observations:
        exact(row, PolicyAuditObservation)
    return PolicyServiceAssessment(assessment_id, study, observations, false_admission_denominator,
        *_service_values(study, observations, false_admission_denominator))
