# SPDX-License-Identifier: MPL-2.0
"""Complete early-reference findings, distinct from biological or simulator success."""

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_prediction.paired_supply import PairedJointValue
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_inquiry_policy import RobustInquirySpecification, WorkBoundInquiryState
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_ids, require_sorted_unique_strings, validate_nonempty, validate_stable_id
from empirical_lawhood.storage.contracts.artifacts import CanonicalTaskReceipt
from empirical_lawhood.domains.rubisco.rubisco_response.biological_support import PredictiveSupportAssessment, selection_from_study
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact, identities
from empirical_lawhood.domains.rubisco.rubisco_response.reference_supply import ReferenceCostCensus, ReferenceKineticAssessment, profile_reference_costs
from empirical_lawhood.domains.rubisco.rubisco_response.requirements import scientific_scope
from empirical_lawhood.domains.rubisco.rubisco_response.study import RubiscoResponseStudy
from empirical_lawhood.domains.rubisco.rubisco_response.study_science import ResponseAssessment, ResponsePredictions, assess_response_study, exact_log_bounds

COMPONENTS = (
    "joint-kinetic-prediction", "numerical-and-chemical-validity", "predictive-validity-and-applicability",
    "approximation-fidelity", "prospective-recognition-and-service", "computational-benefit",
    "reusable-implementation", "scientific-delivery",
)


@dataclass(frozen=True, slots=True)
class ReportEndpointRow(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/report-endpoint-row"
    case_id: str
    scenario_id: str
    original_state: str
    point_id: str | None
    retained_value: PairedJointValue | None
    numerical_assessment: A
    paired_log_bounds: tuple[tuple[Decimal, Decimal], tuple[Decimal, Decimal]] | None
    reason_codes: tuple[str, ...]

    def __post_init__(self):
        for name in (self.case_id, self.scenario_id):
            validate_stable_id(name)
        if self.point_id is not None:
            validate_stable_id(self.point_id)
        if self.original_state not in {"AVAILABLE", "FAILED", "UNKNOWN"} or type(self.numerical_assessment) is not A:
            raise ValueError("endpoint row changes its original scenario or numerical state")
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes")
        if self.retained_value is None:
            if self.paired_log_bounds is not None or not self.reason_codes:
                raise ValueError("missing endpoints need typed reasons without invented logs")
        else:
            exact(self.retained_value, PairedJointValue)
            if self.retained_value.value_id != self.point_id or self.paired_log_bounds != tuple(
                    exact_log_bounds(value) for value in (self.retained_value.turnover_ratio, self.retained_value.specificity_ratio)):
                raise ValueError("report loses exact original point or paired log-ratio bounds")


def endpoint_rows(study, predictions, assessment):
    """Use the expected census; absent/failed alternatives each retain a row."""
    actual = {row.support.case.object_id: row for row in predictions.predictions}
    checked = {row.supply.object_id: row for row in assessment.cases}
    rows = []
    for supply in study.supplies:
        prediction = actual.get(supply.case.case_id)
        result = checked.get(supply.supply_id)
        state = A.UNEVALUABLE if result is None else result.disposition
        retained = {} if prediction is None else {row.scenario_id: row for row in prediction.support.scenarios}
        for scenario in supply.scenarios:
            output = retained.get(scenario.scenario_id)
            values = {} if output is None or output.region is None else {row.value_id: row for row in output.region.values}
            for point_id in tuple(point.point_id for point in scenario.points) or (None,):
                value = values.get(point_id)
                reasons = []
                if value is None:
                    reasons.append("MISSING_RETAINED_ENDPOINT" if scenario.original_state == "AVAILABLE"
                                   else "ORIGINAL_SCENARIO_" + scenario.original_state)
                if state is not A.SATISFIED:
                    reasons.append("NUMERICAL_OUTPUT_NOT_ACCEPTED")
                logs = None if value is None else tuple(exact_log_bounds(value) for value in
                    (value.turnover_ratio, value.specificity_ratio))
                rows.append(ReportEndpointRow(supply.case.case_id, scenario.scenario_id, scenario.original_state,
                    point_id, value, state, logs, tuple(sorted(reasons))))
    return tuple(rows)


@dataclass(frozen=True, slots=True)
class CandidateActionFinding(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/candidate-action-finding"
    conditional_action: str
    biological_action: str
    forecast_scope: str
    remaining_requirement_ids: tuple[str, ...]

    def __post_init__(self):
        if self.conditional_action not in {"ADVANCE", "DEPRIORITIZE", "REFINE", "HOLD"} or self.biological_action != "HOLD":
            raise ValueError("conditional candidate action cannot establish biological readiness")
        if self.forecast_scope not in {"ASSESSED_CONDITIONAL_RATE_SUPPORT", "UNRESOLVED_CONDITIONAL_RATE_SUPPORT"}:
            raise ValueError("early reference report cannot invent a validated native forecast")
        require_sorted_unique_strings(self.remaining_requirement_ids, field_name="remaining_requirement_ids", allow_empty=False)


@dataclass(frozen=True, slots=True)
class MilestoneComponentFinding(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/milestone-component-finding"
    component: str
    frozen_criterion: str
    criterion_source: ObjectIdentity
    disposition: A
    evidence: tuple[ObjectIdentity, ...]
    remaining_requirement_ids: tuple[str, ...]

    def __post_init__(self):
        if self.component not in COMPONENTS or type(self.disposition) is not A:
            raise ValueError("milestone component changes its scientific requirement or disposition")
        validate_nonempty(self.frozen_criterion, field_name="frozen_criterion")
        exact(self.criterion_source, ObjectIdentity)
        identities(self.evidence, allow_empty=True)
        require_sorted_unique_strings(self.remaining_requirement_ids, field_name="remaining_requirement_ids")
        if self.disposition is A.SATISFIED and (self.remaining_requirement_ids or not self.evidence):
            raise ValueError("satisfied milestone component requires evidence and no unresolved premise")
        if self.disposition is not A.SATISFIED and not self.remaining_requirement_ids:
            raise ValueError("unsatisfied milestone component loses its remaining requirement")


@dataclass(frozen=True, slots=True)
class CombinedMilestoneAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/combined-milestone-assessment"
    acceptance: ObjectIdentity
    components: tuple[MilestoneComponentFinding, ...]
    status: str

    def __post_init__(self):
        exact(self.acceptance, ObjectIdentity)
        if type(self.components) is not tuple or tuple(row.component for row in self.components) != COMPONENTS:
            raise ValueError("combined milestone must retain every scientific acceptance component")
        for row in self.components:
            exact(row, MilestoneComponentFinding)
            if row.criterion_source != self.acceptance:
                raise ValueError("milestone component changes its frozen acceptance source")
        expected = "COMPLETE" if all(row.disposition is A.SATISFIED for row in self.components) else "OPEN"
        if self.status != expected:
            raise ValueError("combined milestone closes before every scientific requirement is satisfied")


def _decimal_pair(values):
    return "[" + ", ".join(str(value) for value in values) + "]"


def _milestone(study, assessment, references, biology):
    acceptance = study.acceptance
    prefix = "requirement." + study.study_id + "."
    math_valid = assessment.complete_case_census and all(row.disposition is A.SATISFIED for row in assessment.cases)
    reference_ids = tuple(sorted((row.identity for row in references), key=lambda row: row.object_id))
    conditional = ObjectIdentity.from_record(assessment.assessment_id, assessment)
    biological = ObjectIdentity.from_record(biology.assessment_id, biology)
    numerical_requirements = tuple(sorted(set(key for row in references for key in row.unresolved_requirement_ids)))
    descriptions = (
        ("Independent absolute WT/mutant endpoints and paired response; both gas branches supplied or bounded.",
         A.UNEVALUABLE if math_valid else A.FALSIFIED, (conditional,), (prefix + "validated-prediction",)),
        ("Admitted preparation, forces, chemistry, integration, sampling, clocks and kinetic closure.",
         A.UNEVALUABLE if math_valid else A.FALSIFIED, reference_ids, numerical_requirements or (prefix + "physical-reference-validity",)),
        ("Independent joint predictive error and coverage; separate Gp applicability and discrepancy assessment.",
         A.UNEVALUABLE, (biological,), biology.remaining_requirement_ids),
        ("Absolute log tolerances " + _decimal_pair(acceptance.absolute_log_endpoint_tolerances)
         + "; paired log tolerances " + _decimal_pair(acceptance.paired_log_endpoint_tolerances) + "; complete frozen denominator.",
         A.NOT_ATTEMPTED, (), (prefix + "approximation-fidelity",)),
        ("Committed prospective decisions; useful service >= " + str(acceptance.minimum_useful_service)
         + "; false admission <= " + str(acceptance.maximum_false_admission) + "; " + acceptance.checkpoint_rule,
         A.NOT_ATTEMPTED, (), (prefix + "prospective-policy",)),
        ("Inclusive " + acceptance.cost_metric + " in " + acceptance.cost_unit + "; reference and conventional comparator; reuse count "
         + str(acceptance.planned_reuse_count) + "; admitted improvement criterion required.",
         A.NOT_ATTEMPTED, (), tuple(sorted((acceptance.matrix_handoff_requirement_id, prefix + "prospective-cost")))),
        ("Selected Gp, matched donor and controls use the same admitted installed operations and data bindings.",
         A.UNEVALUABLE, (study.cases.identity,), (prefix + "same-interface-scientific-reuse",)),
        ("Full scientific report, exact outputs, every adverse/unknown attempt, costs and no-acquisition recovery evidence.",
         A.UNEVALUABLE, (conditional,), (prefix + "complete-scientific-delivery",)),
    )
    components = tuple(MilestoneComponentFinding(name, description, acceptance.identity, state, evidence, tuple(sorted(pending)))
        for name, (description, state, evidence, pending) in zip(COMPONENTS, descriptions, strict=True))
    return CombinedMilestoneAssessment(acceptance.identity, components, "OPEN")


def _action(assessment, biology, milestone):
    pending = set(assessment.remaining_requirement_ids) | set(biology.remaining_requirement_ids)
    pending.update(key for row in milestone.components for key in row.remaining_requirement_ids)
    scope = "UNRESOLVED_CONDITIONAL_RATE_SUPPORT" if assessment.conditional_candidate_action == "HOLD" else "ASSESSED_CONDITIONAL_RATE_SUPPORT"
    return CandidateActionFinding(assessment.conditional_candidate_action, biology.biological_candidate_action,
                                  scope, tuple(sorted(pending)))


@dataclass(frozen=True, slots=True)
class ReferenceFindingReport(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/reference-finding-report"
    report_id: str
    study: RubiscoResponseStudy
    predictions: ResponsePredictions
    conditional_assessment: ResponseAssessment
    references: tuple[ReferenceKineticAssessment, ...]
    biological_support: PredictiveSupportAssessment
    producing_receipts: tuple[CanonicalTaskReceipt, ...]
    inquiry_specification: RobustInquirySpecification | None
    work_state: WorkBoundInquiryState | None
    cost_census: ReferenceCostCensus | None
    endpoints: tuple[ReportEndpointRow, ...]
    action: CandidateActionFinding
    milestone: CombinedMilestoneAssessment
    permitted_refinement_id: str | None = None
    new_native_calls: int = 0
    independent_biological_units: int = 0

    def __post_init__(self):
        validate_stable_id(self.report_id)
        exact(self.study, RubiscoResponseStudy)
        exact(self.predictions, ResponsePredictions)
        exact(self.conditional_assessment, ResponseAssessment)
        expected = assess_response_study(self.study, self.predictions,
            assessment_id=self.conditional_assessment.assessment_id, permitted_refinement_id=self.permitted_refinement_id)
        if self.conditional_assessment != expected:
            raise ValueError("report substitutes the independent nomination or joint candidate assessment")
        exact(self.biological_support, PredictiveSupportAssessment)
        if self.biological_support.selection != selection_from_study(self.study):
            raise ValueError("report changes frozen biological requirements, constructs or anchor uses")
        actual = {row.support.case.object_id: row for row in self.predictions.predictions}
        expected_ids = tuple(row.case.case_id for row in self.study.supplies if row.case.case_id in actual)
        if type(self.references) is not tuple or tuple(row.supply.case.case_id for row in self.references) != expected_ids:
            raise ValueError("report loses a retained case's independent reference analysis")
        for reference in self.references:
            exact(reference, ReferenceKineticAssessment)
            supply = next(row for row in self.study.supplies if row.case.case_id == reference.supply.case.case_id)
            prediction = actual[supply.case.case_id]
            if reference.supply != supply or reference.retained_prediction != ObjectIdentity.from_record(prediction.prediction_id, prediction):
                raise ValueError("report reference changes its retained source or prediction")
        if type(self.producing_receipts) is not tuple:
            raise ValueError("report needs an immutable original receipt census")
        require_sorted_unique_ids(self.producing_receipts, attribute="receipt_id", field_name="receipts")
        for receipt in self.producing_receipts:
            exact(receipt, CanonicalTaskReceipt)
        if len({self.work_state is None, self.cost_census is None, self.inquiry_specification is None}) != 1:
            raise ValueError("report must bind its scientific question, original work and its complete cost census together")
        if self.work_state is not None:
            exact(self.inquiry_specification, RobustInquirySpecification)
            exact(self.work_state, WorkBoundInquiryState)
            if (self.inquiry_specification.target.scope != scientific_scope(self.study)
                    or self.work_state.information_cutoff.clock_id != self.inquiry_specification.target.scope.clock_id
                    or self.work_state.specification != ObjectIdentity.from_record(
                        self.inquiry_specification.specification_id, self.inquiry_specification)):
                raise ValueError("report borrows work/cost from another scientific question")
            exact(self.cost_census, ReferenceCostCensus)
            if self.cost_census != profile_reference_costs(self.work_state, census_id=self.cost_census.census_id):
                raise ValueError("report omits failed/unknown work or substitutes actual measured costs")
            if not {ObjectIdentity.from_record(row.receipt_id, row) for row in self.producing_receipts}.issubset({
                    row.receipt for row in self.work_state.operational_census}):
                raise ValueError("report substitutes an original producing receipt outside its complete attempt census")
        elif self.producing_receipts:
            raise ValueError("original receipt census requires its complete work-bound context")
        if self.endpoints != endpoint_rows(self.study, self.predictions, expected):
            raise ValueError("report drops a selected missing, failed or retained endpoint row")
        expected_milestone = _milestone(self.study, expected, self.references, self.biological_support)
        if self.milestone != expected_milestone or self.action != _action(expected, self.biological_support, expected_milestone):
            raise ValueError("report confuses candidate action, prediction validity or combined milestone")
        if (type(self.new_native_calls) is not int or self.new_native_calls != 0
                or type(self.independent_biological_units) is not int or self.independent_biological_units != 0):
            raise ValueError("retained reporting cannot create native calls or biological units")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.report_id, self)


def build_reference_finding_report(study, predictions, biology, *, report_id,
        references=None, producing_receipts=(), inquiry_specification=None, work_state=None, permitted_refinement_id=None):
    """Independently recheck original outputs, then assemble all scientific gaps."""
    from empirical_lawhood.domains.rubisco.rubisco_response.reference_supply import assess_reference_supply
    exact(study, RubiscoResponseStudy)
    exact(predictions, ResponsePredictions)
    exact(biology, PredictiveSupportAssessment)
    assessment = assess_response_study(study, predictions, assessment_id=report_id + ".conditional",
                                      permitted_refinement_id=permitted_refinement_id)
    if references is None:
        actual = {row.support.case.object_id: row for row in predictions.predictions}
        references = tuple(assess_reference_supply(supply, actual[supply.case.case_id], decision,
            assessment_id=report_id + ".reference." + supply.case.case_id)
            for supply, decision in zip(study.supplies, study.decisions, strict=True) if supply.case.case_id in actual)
    costs = None if work_state is None else profile_reference_costs(work_state, census_id=report_id + ".costs")
    milestone = _milestone(study, assessment, references, biology)
    return ReferenceFindingReport(report_id, study, predictions, assessment, references, biology,
        producing_receipts, inquiry_specification, work_state, costs, endpoint_rows(study, predictions, assessment),
        _action(assessment, biology, milestone), milestone, permitted_refinement_id)
