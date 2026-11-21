# SPDX-License-Identifier: MPL-2.0
"""Full-study conditional products and independent retained-result readout."""

from dataclasses import dataclass
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR, localcontext
from typing import ClassVar

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition, AssessmentPhase, RequirementSupplyAssessment
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_strings, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.paired_prediction import PairedPrediction
from empirical_lawhood.domains.rubisco.rubisco_response.prediction_assessment import PairedPredictionAssessment, assess_paired_prediction
from empirical_lawhood.domains.rubisco.rubisco_response.requirements import PHASES, RubiscoRequirementGraph, response_requirement_graph, validate_connection_assessment_census
from empirical_lawhood.domains.rubisco.rubisco_response.study import RubiscoResponseStudy


@dataclass(frozen=True, slots=True)
class ResponsePredictions(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/study-predictions"
    prediction_id: str
    study: ObjectIdentity
    predictions: tuple[PairedPrediction, ...]

    def __post_init__(self):
        validate_stable_id(self.prediction_id)
        exact(self.study, ObjectIdentity)
        if self.study.object_schema != RubiscoResponseStudy.SCHEMA or self.study.object_version != RubiscoResponseStudy.VERSION:
            raise ValueError("study predictions change the complete selected source")
        if type(self.predictions) is not tuple:
            raise TypeError("study predictions require an immutable paired-case census")
        for prediction in self.predictions:
            exact(prediction, PairedPrediction)
        ids = tuple(row.support.case.object_id for row in self.predictions)
        require_sorted_unique_strings(ids, field_name="case_ids")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.prediction_id, self)


@dataclass(frozen=True, slots=True)
class NominationFinding(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/nomination-finding"
    nominated_prediction: ObjectIdentity
    case_id: str
    joint_direction: str
    nominated_magnitude: str

    def __post_init__(self):
        exact(self.nominated_prediction, ObjectIdentity)
        validate_stable_id(self.case_id)
        kinds = {"CONDITIONAL_SUPPORT", "CONDITIONAL_CONTRADICTION", "MIXED", "UNEVALUABLE"}
        if self.joint_direction not in kinds or self.nominated_magnitude not in kinds | {"NOT_NOMINATED"}:
            raise ValueError("nominated prediction findings must remain separate from the candidate criterion")


@dataclass(frozen=True, slots=True)
class ResponseAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/study-assessment"
    assessment_id: str
    study: ObjectIdentity
    predictions: ObjectIdentity
    graph: RubiscoRequirementGraph
    complete_case_census: bool
    cases: tuple[PairedPredictionAssessment, ...]
    nomination_findings: tuple[NominationFinding, ...]
    connection_assessments: tuple[RequirementSupplyAssessment, ...]
    conditional_candidate_action: str
    remaining_requirement_ids: tuple[str, ...]
    combined_milestone: str = "OPEN"
    biological_predictive_calibration: str = "NOT_ESTABLISHED"
    independent_biological_units: int = 0

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        for record, kind in ((self.study, RubiscoResponseStudy), (self.predictions, ResponsePredictions)):
            exact(record, ObjectIdentity)
            if record.object_schema != kind.SCHEMA or record.object_version != kind.VERSION:
                raise ValueError("study assessment substitutes its retained exact source")
        exact(self.graph, RubiscoRequirementGraph)
        if self.graph.study != self.study or type(self.complete_case_census) is not bool:
            raise ValueError("study assessment changes its complete source census")
        if type(self.cases) is not tuple or type(self.nomination_findings) is not tuple:
            raise TypeError("study readout must retain immutable case and nomination findings")
        for row in self.cases:
            exact(row, PairedPredictionAssessment)
        for row in self.nomination_findings:
            exact(row, NominationFinding)
        validate_connection_assessment_census(self.graph, self.connection_assessments)
        if self.conditional_candidate_action not in {"ADVANCE", "DEPRIORITIZE", "REFINE", "HOLD"}:
            raise ValueError("unknown conditional candidate action")
        require_sorted_unique_strings(self.remaining_requirement_ids, field_name="remaining_requirement_ids", allow_empty=False)
        if self.graph.root_requirement_id not in self.remaining_requirement_ids:
            raise ValueError("conditional response cannot close the combined scientific milestone")
        if (self.combined_milestone != "OPEN" or self.biological_predictive_calibration != "NOT_ESTABLISHED"
                or type(self.independent_biological_units) is not int or self.independent_biological_units != 0):
            raise ValueError("conditional study readout cannot establish biological or computational benefit")


def predict_response_study(study, *, prediction_id):
    from empirical_lawhood.domains.rubisco.rubisco_response.paired_prediction import predict_paired_rates

    exact(study, RubiscoResponseStudy)
    predictions = tuple(predict_paired_rates(supply,
        prediction_id=prediction_id + "." + supply.case.case_id) for supply in study.supplies)
    return ResponsePredictions(prediction_id, study.identity, predictions)


def exact_log_bounds(ratio):
    """Bound an exact positive rational log using directed division and ulps."""
    if ratio == 1:
        return Decimal(0), Decimal(0)
    with localcontext() as context:
        context.prec = 50
        context.rounding = ROUND_FLOOR
        lower = Decimal(ratio.numerator) / Decimal(ratio.denominator)
        context.rounding = ROUND_CEILING
        upper = Decimal(ratio.numerator) / Decimal(ratio.denominator)
        # Decimal.ln is correctly rounded to nearest; adjacent representable
        # values enclose each result even at the last-place rounding boundary.
        return lower.ln().next_minus(), upper.ln().next_plus()


def _nomination_finding(nominated, supplied, assessed):
    magnitude = "NOT_NOMINATED" if nominated.nominated_turnover_log_ratio_interval is None else "UNEVALUABLE"
    available = (assessed.disposition is AssessmentDisposition.SATISFIED
        and assessed.decision is not None and not assessed.decision.unresolved_requirement_ids
        and all(row.region is not None and row.region.values for row in supplied.support.scenarios))
    directions, magnitudes = [], []
    if available:
        for scenario in supplied.support.scenarios:
            for point in scenario.region.values:
                carbon, specificity = point.turnover_ratio, point.specificity_ratio
                direction = {"INCREASE": carbon > 1, "DECREASE": carbon < 1, "UNCHANGED": carbon == 1,
                             "UNSPECIFIED": None}[nominated.turnover_direction]
                other = {"PRESERVE_OR_INCREASE": specificity >= 1, "INCREASE": specificity > 1,
                         "DECREASE": specificity < 1, "UNSPECIFIED": None}[nominated.specificity_direction]
                directions.append(None if direction is None or other is None else direction and other)
                if nominated.nominated_turnover_log_ratio_interval is not None:
                    lower, upper = exact_log_bounds(carbon)
                    start, stop = nominated.nominated_turnover_log_ratio_interval
                    magnitudes.append(True if lower >= start and upper <= stop else
                                      False if upper < start or lower > stop else None)
    def finding(values):
        if not values or any(value is None for value in values):
            return "UNEVALUABLE"
        if all(values):
            return "CONDITIONAL_SUPPORT"
        return "CONDITIONAL_CONTRADICTION" if not any(values) else "MIXED"
    if magnitudes:
        magnitude = finding(magnitudes)
    return NominationFinding(ObjectIdentity.from_record(nominated.prediction_id, nominated),
                             nominated.case.object_id, finding(directions), magnitude)


def assess_response_study(study, predictions, *, assessment_id, permitted_refinement_id=None):
    """Assess the complete retained product; no producer, native entry or retry."""
    exact(study, RubiscoResponseStudy)
    exact(predictions, ResponsePredictions)
    if permitted_refinement_id is not None and permitted_refinement_id not in study.acceptance.permitted_refinement_ids:
        raise ValueError("refinement is outside the frozen finite menu")
    graph = response_requirement_graph(study)
    by_case = {row.support.case.object_id: row for row in predictions.predictions}
    expected = tuple(supply.case.case_id for supply in study.supplies)
    complete = predictions.study == study.identity and tuple(by_case) == expected
    assessed = []
    nominations = []
    actions = []
    for supply, decision in zip(study.supplies, study.decisions, strict=True):
        prediction = by_case.get(supply.case.case_id)
        if prediction is None:
            continue
        result = assess_paired_prediction(supply, prediction, decision,
            assessment_id=assessment_id + "." + supply.case.case_id,
            permitted_refinement_id=permitted_refinement_id)
        assessed.append(result)
        if supply.case.case_role == "CANDIDATE":
            actions.append(result.conditional_action)
            nomination = next(row for row in study.nominated_predictions if row.case == supply.case.identity)
            nominations.append(_nomination_finding(nomination, prediction, result))
    valid = complete and all(row.disposition is AssessmentDisposition.SATISFIED for row in assessed)
    if not valid or "HOLD" in actions:
        action = "HOLD"
    elif set(actions) == {"ADVANCE"}:
        action = "ADVANCE"
    elif set(actions) == {"DEPRIORITIZE"}:
        action = "DEPRIORITIZE"
    else:
        action = "REFINE" if permitted_refinement_id is not None else "HOLD"
    connection = graph.connections[0]
    requirement = next(row for row in graph.requirements if row.requirement_id == connection.requirement_id)
    evidence = tuple(sorted((study.identity, predictions.identity, graph.identity,
        *(ObjectIdentity.from_record(row.assessment_id, row) for row in assessed)), key=lambda row: row.object_id))
    phases = []
    for phase in PHASES:
        passed = True if phase is AssessmentPhase.PROCEDURE else (
            complete if phase is AssessmentPhase.INSTANCE else valid)
        phases.append(RequirementSupplyAssessment(assessment_id + ".connection." + phase.value.lower(),
            ObjectIdentity.from_record(requirement.requirement_id, requirement),
            ObjectIdentity.from_record(connection.connection_id, connection), phase,
            AssessmentDisposition.SATISFIED if passed else AssessmentDisposition.FALSIFIED,
            study.study_id, evidence, () if passed else ("CONDITIONAL_CONNECTION_FAILED",)))
    remaining = tuple(row.requirement_id for row in graph.requirements
                      if not valid or row.requirement_id != graph.conditional_requirement_id)
    return ResponseAssessment(assessment_id, study.identity, predictions.identity, graph, complete,
        tuple(assessed), tuple(nominations), tuple(phases), action, remaining)
