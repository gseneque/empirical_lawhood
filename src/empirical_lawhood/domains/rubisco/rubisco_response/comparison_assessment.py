# SPDX-License-Identifier: MPL-2.0
"""Independent retained comparison with full assignments and original decisions.

The supported input reports remain exposed conditional kinetics. This consumer
can diagnose arithmetic error, complete service counts and recorded expense.
It cannot turn those reports into native reference validity or prospective
qualification. Original read cutoffs are not acquisition timestamps.
"""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_insilico_mechanism.contracts import Exact
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_inquiry import InquiryAttemptStatus
from empirical_lawhood.science.inquiry.recursive_inquiry_policy import WorkBoundInquiryState
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_strings, validate_stable_id
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.domains.rubisco.rubisco_response.comparison_cost import ComparisonCostAssessment, assess_comparison_costs
from empirical_lawhood.domains.rubisco.rubisco_response.comparison_decisions import RetainedPolicyDecision
from empirical_lawhood.domains.rubisco.rubisco_response.comparison_preparation import ARMS, ResponseComparisonDesign
from empirical_lawhood.domains.rubisco.rubisco_response.finding_report import ReferenceFindingReport
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.policy_service import PolicyUnitAudit, _service_values
from empirical_lawhood.domains.rubisco.rubisco_response.reduction_error import STAGES, JointErrorDecomposition, JointErrorStage, assess_joint_error_decomposition
from empirical_lawhood.domains.rubisco.rubisco_response.requirements import response_requirement_graph


@dataclass(frozen=True, slots=True)
class RetainedComparisonArm(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/retained-comparison-arm"
    arm: str
    report: ReferenceFindingReport | None

    def __post_init__(self):
        if self.arm not in ARMS:
            raise ValueError("retained comparison changes its declared arm")
        if self.report is not None:
            exact(self.report, ReferenceFindingReport)


def _validate_inputs(design, arms, decisions):
    exact(design, ResponseComparisonDesign)
    if type(arms) is not tuple or tuple(row.arm for row in arms) != ARMS:
        raise ValueError("retained comparison requires all three arms, including missing results")
    for row in arms:
        exact(row, RetainedComparisonArm)
        if row.report is not None and row.report.study != design.study:
            raise ValueError("comparison report changes the exact frozen study, source, scenario or criterion")
    if type(decisions) is not tuple:
        raise ValueError("comparison decisions must retain immutable original history")
    expected_cases = {row.case.object_id: row for row in design.cases}
    keys = []
    histories = {key: [] for key in expected_cases}
    for row in decisions:
        exact(row, RetainedPolicyDecision)
        case_id = row.selection.case_id
        if case_id not in expected_cases or row.selection != expected_cases[case_id].policy:
            raise ValueError("comparison decision changes a case's exact frozen policy")
        previous = histories[case_id]
        if row.state.previous_decisions != tuple(sorted((value.identity for value in previous), key=lambda value: value.object_id)):
            raise ValueError("comparison drops, reorders or substitutes an original decision checkpoint")
        keys.append((case_id, len(previous)))
        previous.append(row)
    if keys != sorted(keys):
        raise ValueError("comparison decision histories must preserve case and checkpoint order")


def _prediction_receipts(report):
    if report is None:
        return ()
    return tuple(receipt for receipt in report.producing_receipts
        if any(logical.payload_schema == report.predictions.SCHEMA and logical.content_sha256 == report.predictions.fingerprint()
               and any(physical.logical_artifact_id == logical.logical_artifact_id
                   and physical.physical_sha256 == logical.content_sha256
                   and physical.size_bytes == len(report.predictions.canonical_bytes())
                   and physical.compression == "none" for physical in receipt.output_materializations)
               for logical in receipt.output_logical_artifacts))


def _method_gate(report, method):
    if report is None or method is None or report.work_state is None:
        return A.UNEVALUABLE
    # An assessment task or a label on a wrapper is not the producing method.
    receipts = _prediction_receipts(report)
    if not receipts:
        return A.UNEVALUABLE
    if any(row.operational_status is not OperationalStatus.SUCCEEDED for row in receipts):
        return A.FALSIFIED
    producers = {ObjectIdentity.from_record(row.receipt_id, row) for row in receipts}
    bindings = tuple(row for row in report.work_state.attempt_work_bindings if row.witness in producers)
    if len({row.witness for row in bindings}) != len(producers) or any(row.work is None for row in bindings):
        return A.UNEVALUABLE
    by_receipt = {ObjectIdentity.from_record(row.receipt_id, row): row for row in receipts}
    attempts = {row.attempt_id: row for row in report.work_state.operational_census}
    required = {report.study.cases.identity, report.study.allocation.identity, *(row.identity for row in report.study.supplies)}
    for binding in bindings:
        receipt = by_receipt[binding.witness]
        attempt = attempts[binding.attempt_id]
        operands = set(binding.work.scientific_operands)
        if (binding.attempt_id != receipt.attempt_id or binding.execution_task.object_id != receipt.task_id
                or attempt.status is not InquiryAttemptStatus.COMPLETED or report.predictions.identity not in attempt.products
                or binding.work.method != method or report.study.identity not in operands and not required <= operands):
            return A.FALSIFIED
    return A.SATISFIED


def _row_state(report, endpoint):
    if report is None or endpoint is None:
        return "UNKNOWN"
    if any(row.operational_status is not OperationalStatus.SUCCEEDED for row in _prediction_receipts(report)):
        return "FAILED"
    if endpoint.original_state != "AVAILABLE":
        return endpoint.original_state
    return "AVAILABLE" if endpoint.retained_value is not None else "UNKNOWN"


def _error_status(term):
    if term is None or term.normalized_absolute_error_bounds is None:
        return "UNRESOLVED"
    bounds = term.normalized_absolute_error_bounds
    if any(pair[0].fraction > 1 for pair in bounds):
        return "FAILED"
    return "WITHIN" if all(pair[1].fraction <= 1 for pair in bounds) else "UNRESOLVED"


@dataclass(frozen=True, slots=True)
class ComparisonPointFinding(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/comparison-point-finding"
    case: ObjectIdentity
    scenario_id: str
    point_id: str | None
    original_scenario_state: str
    original_arm_states: tuple[tuple[str, str], ...]
    method_gates: tuple[tuple[str, A], ...]
    arithmetic_gates: tuple[tuple[str, A], ...]
    error: JointErrorDecomposition | None
    reason_codes: tuple[str, ...]

    def __post_init__(self):
        exact(self.case, ObjectIdentity)
        validate_stable_id(self.scenario_id)
        if self.point_id is not None:
            validate_stable_id(self.point_id)
        if self.original_scenario_state not in {"AVAILABLE", "FAILED", "UNKNOWN"}:
            raise ValueError("comparison point loses the original source scenario state")
        for values in (self.original_arm_states, self.method_gates, self.arithmetic_gates):
            if type(values) is not tuple or tuple(key for key, _ in values) != ARMS:
                raise ValueError("comparison point drops an arm's original result or independent gate")
        if any(state not in {"AVAILABLE", "FAILED", "UNKNOWN"} for _, state in self.original_arm_states):
            raise ValueError("comparison point loses an actual failed or unknown return")
        if any(type(state) is not A for _, state in (*self.method_gates, *self.arithmetic_gates)):
            raise ValueError("comparison point gates require exact independent dispositions")
        if self.error is not None:
            exact(self.error, JointErrorDecomposition)
            if (self.error.parity.case, self.error.scenario_id, self.error.point_id) != (self.case, self.scenario_id, self.point_id):
                raise ValueError("comparison error substitutes a selected case, scenario or point")
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes")

    @property
    def reference_usable(self):
        return (self.original_arm_states[0][1] == "AVAILABLE" and self.method_gates[0][1] is A.SATISFIED
            and self.arithmetic_gates[0][1] is A.SATISFIED and self.error is not None)

    def joint_error(self, arm="reduced"):
        index = ARMS.index(arm)
        if arm == "reference" or not self.reference_usable or self.method_gates[index][1] is not A.SATISFIED:
            return "UNRESOLVED"
        return _error_status(self.error.total if arm == "reduced" else self.error.conventional_error)


def _point_findings(design, arms):
    reports = {row.arm: row.report for row in arms}
    endpoints = {arm: {} if report is None else {(row.case_id, row.scenario_id, row.point_id): row for row in report.endpoints}
                 for arm, report in reports.items()}
    plans = {row.case.object_id: row for row in design.cases}
    result = []
    for first in design.assignments[::3]:
        plan = plans[first.case.object_id]
        actual = {arm: endpoints[arm].get(first.point_key) for arm in ARMS}
        methods = (design.study.acceptance.reference_method, design.study.acceptance.conventional_baseline,
                   None if plan.parity is None else plan.parity.approximation_method)
        method_gates = tuple((arm, _method_gate(reports[arm], method)) for arm, method in zip(ARMS, methods, strict=True))
        arithmetic = tuple((arm, A.UNEVALUABLE if actual[arm] is None else actual[arm].numerical_assessment) for arm in ARMS)
        states = tuple((arm, _row_state(reports[arm], actual[arm])) for arm in ARMS)
        reasons = {"MISSING_RETAINED_" + arm.upper() for arm, state in states if state == "UNKNOWN"}
        reasons.update("UNASSESSED_OR_DIFFERENT_" + arm.upper() + "_METHOD" for arm, gate in method_gates if gate is not A.SATISFIED)
        if arithmetic[0][1] is not A.SATISFIED:
            reasons.add("REFERENCE_ARITHMETIC_NOT_ACCEPTED")
        error = None
        if plan.parity is None:
            reasons.add("SHARED_COMPARISON_OPERANDS_NOT_SELECTED")
        elif first.point_id is None:
            reasons.add("ORIGINAL_SCENARIO_HAS_NO_COMPLETE_JOINT_POINT")
        elif design.scale == "ANCHORED" and any(point is not None and point.retained_value is not None
                and point.retained_value.anchor_wild_type is None for point in actual.values()):
            reasons.add("MISSING_ORIGINAL_SHARED_WT_ANCHOR")
        else:
            def stage(role, arm, method):
                report, point = reports[arm], actual[arm]
                state = dict(states)[arm]
                sources = (design.identity,) if report is None else tuple(sorted({report.identity, report.predictions.identity,
                    *(ObjectIdentity.from_record(row.receipt_id, row) for row in report.producing_receipts)}, key=lambda row: row.object_id))
                return JointErrorStage(role, plan.parity.identity, method, state,
                    None if point is None else point.retained_value, sources, () if state == "AVAILABLE" else ("ORIGINAL_" + state,))
            reference = stage("REFERENCE", "reference", methods[0])
            approximation = stage("APPROXIMATION", "reduced", methods[2])
            conventional = stage("CONVENTIONAL", "conventional", methods[1])
            intermediate = tuple(JointErrorStage(role, plan.parity.identity, methods[2], "UNKNOWN", None,
                (design.identity,), ("MISSING_RETAINED_INTERMEDIATE",)) for role in STAGES[1:-1])
            # Each original value is preserved. A failed approximation equation
            # is not removed before measuring its discrepancy against good truth.
            error = assess_joint_error_decomposition(plan.parity, (reference, *intermediate, approximation), conventional,
                scenario_id=first.scenario_id, point_id=first.point_id, scale=design.scale,
                log_tolerances=design.log_tolerances, assessment_id="error." + first.identity.object_id)
        result.append(ComparisonPointFinding(first.case, first.scenario_id, first.point_id, first.original_scenario_state,
            states, method_gates, arithmetic, error, tuple(sorted(reasons))))
    return tuple(result)


def _causal_order(decisions, reference):
    if not decisions:
        return A.UNEVALUABLE, ("MISSING_ORIGINAL_POLICY_DECISION",)
    if reference is not None:
        truth = {reference.predictions.identity, reference.identity,
            *(ObjectIdentity.from_record(row.receipt_id, row) for row in reference.producing_receipts)}
        for decision in decisions:
            seen = {row.product for row in decision.state.stock} | {row.receipt for row in decision.state.operational_census}
            if truth & seen:
                return A.FALSIFIED, ("REFERENCE_ALREADY_IN_ORIGINAL_POLICY_INFORMATION",)
    # A post-outcome read cutoff records access, not the time of original native
    # acquisition. Only the future installed supplier's causal custody can add
    # that evidence. The current exposed report types cannot establish it.
    return A.UNEVALUABLE, ("ORIGINAL_PRE_REFERENCE_CAUSAL_CUSTODY_NOT_ESTABLISHED",)


@dataclass(frozen=True, slots=True)
class ComparisonCaseFinding(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/comparison-case-finding"
    case: ObjectIdentity
    decisions: tuple[RetainedPolicyDecision, ...]
    points: tuple[ComparisonPointFinding, ...]
    causal_order: A
    causal_reason_codes: tuple[str, ...]

    def __post_init__(self):
        exact(self.case, ObjectIdentity)
        if type(self.decisions) is not tuple or type(self.points) is not tuple or not self.points:
            raise ValueError("comparison case needs complete retained point and decision tuples")
        for row in self.decisions:
            exact(row, RetainedPolicyDecision)
            if row.selection.case_id != self.case.object_id:
                raise ValueError("comparison case borrows another original policy decision")
        for row in self.points:
            exact(row, ComparisonPointFinding)
            if row.case != self.case:
                raise ValueError("comparison case borrows another original joint error")
        if self.causal_order not in {A.UNEVALUABLE, A.FALSIFIED}:
            raise ValueError("exposed read cutoffs cannot establish original prospective causal custody")
        require_sorted_unique_strings(self.causal_reason_codes, field_name="causal_reasons", allow_empty=False)

    @property
    def action(self):
        return "UNKNOWN" if not self.decisions else self.decisions[-1].action

    @property
    def joint_error(self):
        findings = tuple(row.joint_error() for row in self.points)
        return "FAILED" if "FAILED" in findings else "WITHIN" if set(findings) == {"WITHIN"} else "UNRESOLVED"

    @property
    def reduced_state(self):
        states = tuple(dict(row.original_arm_states)["reduced"] for row in self.points)
        return "FAILED" if "FAILED" in states else "AVAILABLE" if set(states) == {"AVAILABLE"} else "UNKNOWN"

    @property
    def reference_state(self):
        if all(row.reference_usable for row in self.points):
            return "ASSESSED_VALID"
        return "FAILED" if any(dict(row.original_arm_states)["reference"] == "FAILED" for row in self.points) else "UNKNOWN"


def _case_findings(design, arms, decisions, points):
    reference = arms[0].report
    result = []
    for case in design.study.cases.cases:
        history = tuple(row for row in decisions if row.selection.case_id == case.case_id)
        result.append(ComparisonCaseFinding(case.identity, history, tuple(row for row in points if row.case == case.identity),
            *_causal_order(history, reference)))
    return tuple(result)


@dataclass(frozen=True, slots=True)
class ComparisonServiceAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/comparison-service-assessment"
    design: ResponseComparisonDesign
    observations: tuple[ComparisonCaseFinding, ...]
    units: tuple[PolicyUnitAudit, ...]
    useful_service_bounds: tuple[Exact, Exact]
    false_admission_assigned_bounds: tuple[Exact, Exact]
    false_admission_conditional_bounds: tuple[Exact, Exact] | None
    fallback_bounds: tuple[Exact, Exact]
    useful_service_disposition: A
    false_admission_disposition: A
    reference_coverage_disposition: A
    interpretation: str = "DESCRIPTIVE_EXPOSED_CONDITIONAL_AUDIT_NOT_PROSPECTIVE_OR_BIOLOGICAL_VALIDATION"

    def __post_init__(self):
        exact(self.design, ResponseComparisonDesign)
        if type(self.observations) is not tuple or tuple(row.case for row in self.observations) != tuple(case.identity for case in self.design.study.cases.cases):
            raise ValueError("comparison service drops an assigned case or refused unit")
        for row in self.observations:
            exact(row, ComparisonCaseFinding)
        actual = (self.units, self.useful_service_bounds, self.false_admission_assigned_bounds,
            self.false_admission_conditional_bounds, self.fallback_bounds, self.useful_service_disposition,
            self.false_admission_disposition, self.reference_coverage_disposition)
        if actual != _service_values(self.design.study, self.observations, self.design.false_admission_denominator):
            raise ValueError("comparison service changes original nested units, missing truth or known false admission")
        if self.interpretation != "DESCRIPTIVE_EXPOSED_CONDITIONAL_AUDIT_NOT_PROSPECTIVE_OR_BIOLOGICAL_VALIDATION":
            raise ValueError("finite descriptive service cannot become prospective validation or population coverage")


def _states(arms, decisions):
    values = [row.report.work_state for row in arms if row.report is not None and row.report.work_state is not None]
    values.extend(row.state for row in decisions)
    by_id = {}
    for row in values:
        exact(row, WorkBoundInquiryState)
        if row.state_id in by_id and by_id[row.state_id] != row:
            raise ValueError("comparison sources conflict on an original work-bound state")
        by_id[row.state_id] = row
    return tuple(by_id[key] for key in sorted(by_id))


def _fidelity(points, arm):
    statuses = tuple(row.joint_error(arm) for row in points)
    return A.FALSIFIED if "FAILED" in statuses else A.SATISFIED if set(statuses) == {"WITHIN"} else A.UNEVALUABLE


def _remaining(design, arms, decisions, points):
    pending = ({row.requirement_id for row in response_requirement_graph(design.study).requirements}
        if arms[0].report is None else set(arms[0].report.conditional_assessment.remaining_requirement_ids))
    pending.update("requirement." + design.design_id + "." + name for name in (
        "actual-native-reference-and-parity", "original-pre-reference-causal-custody", "prospective-complete-service",
        "complete-comparative-measurements", "accepted-native-output-binding"))
    for row in arms:
        if row.report is not None:
            pending.update(name for component in row.report.milestone.components for name in component.remaining_requirement_ids)
    for row in decisions:
        pending.update(row.decision.unresolved_target_requirement_ids)
    for row in points:
        if row.reason_codes:
            pending.add("requirement." + design.design_id + "." + row.case.object_id + "." + row.scenario_id + ".comparison-inputs")
    return tuple(sorted(pending))


@dataclass(frozen=True, slots=True)
class ResponseComparisonAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/comparison-assessment"
    assessment_id: str
    design: ResponseComparisonDesign
    arms: tuple[RetainedComparisonArm, ...]
    decisions: tuple[RetainedPolicyDecision, ...]
    points: tuple[ComparisonPointFinding, ...]
    cases: tuple[ComparisonCaseFinding, ...]
    service: ComparisonServiceAssessment
    costs: ComparisonCostAssessment
    reduced_conditional_fidelity: A
    conventional_conditional_fidelity: A
    remaining_requirement_ids: tuple[str, ...]
    prospective_qualification: A = A.UNEVALUABLE
    biological_validation: str = "NOT_ESTABLISHED"
    new_native_calls: int = 0

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        _validate_inputs(self.design, self.arms, self.decisions)
        points = _point_findings(self.design, self.arms)
        cases = _case_findings(self.design, self.arms, self.decisions, points)
        if self.points != points or self.cases != cases:
            raise ValueError("comparison substitutes original returns, error operands, methods or decision history")
        exact(self.service, ComparisonServiceAssessment)
        if self.service.design != self.design or self.service.observations != cases:
            raise ValueError("comparison borrows service counts from a different policy or error census")
        exact(self.costs, ComparisonCostAssessment)
        if self.costs.design != self.design or self.costs.states != _states(self.arms, self.decisions):
            raise ValueError("comparison drops original work or borrows another campaign's cost")
        if (self.reduced_conditional_fidelity, self.conventional_conditional_fidelity) != (_fidelity(points, "reduced"), _fidelity(points, "conventional")):
            raise ValueError("comparison changes conditional fidelity or treats unknown truth as success")
        if self.remaining_requirement_ids != _remaining(self.design, self.arms, self.decisions, points):
            raise ValueError("comparison drops an actual remaining scientific prerequisite")
        if (self.prospective_qualification is not A.UNEVALUABLE or self.biological_validation != "NOT_ESTABLISHED"
                or type(self.new_native_calls) is not int or self.new_native_calls != 0):
            raise ValueError("retained exposed comparison cannot manufacture prospective or biological qualification")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.assessment_id, self)


def assess_retained_comparison(design, arms, decisions=(), *, assessment_id):
    _validate_inputs(design, arms, decisions)
    points = _point_findings(design, arms)
    cases = _case_findings(design, arms, decisions, points)
    service = ComparisonServiceAssessment(design, cases, *_service_values(design.study, cases, design.false_admission_denominator))
    costs = assess_comparison_costs(design, _states(arms, decisions), assessment_id=assessment_id + ".costs")
    return ResponseComparisonAssessment(assessment_id, design, arms, decisions, points, cases, service, costs,
        _fidelity(points, "reduced"), _fidelity(points, "conventional"), _remaining(design, arms, decisions, points))
