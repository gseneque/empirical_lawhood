# SPDX-License-Identifier: MPL-2.0
"""Complete functional preparation/transfer calculations over original scores.

No fitting, calibration, trajectory production or scientific authority is
performed. Original scheduled independent response scores remain the numerical
owner. Supported-use and sampling references make these calculations conditional;
they are not assessed by converting an identity or label into a warrant.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from fractions import Fraction
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_scheduled_history.forecast import CALIBRATED_QUERY
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import identity as original_identity
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.runtime.experimental_statistics import AssignedBinomialInference
from empirical_lawhood.adapters.methods.matrix_factor_response.curve_prediction import MatchedCurveDecision
from empirical_lawhood.adapters.methods.matrix_factor_response.matched_response_prediction import matched_primary_inference

from .paired_adequacy import MatrixPairedAdequacy
from .records import (
    STANDING, MatrixFrozenConsumerPackage, MatrixFunctionalCriterion, MatrixLaterExperimentSpecification, MatrixProgrammeEvidence,
    MatrixProgrammeRoster, identity,
)


@dataclass(frozen=True, slots=True)
class MatrixFunctionalCaseResult(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/functional-case-result"
    VERSION: ClassVar[str] = "2.0.0"
    case_id: str
    unit_id: str
    arm_id: str
    disposition: str
    actual_error: Decimal | None
    error_point: Decimal | None
    error_upper: Decimal | None
    functional_reliable: bool
    conditional_admission: bool
    covered: bool | None
    false_admission: bool
    preparation_effort: Decimal | None
    reasons: tuple[str, ...]
    absolute_forecast_log_error: Decimal | None = None
    absolute_comparator_log_error: Decimal | None = None
    source_support: str = "UNESTABLISHED"
    response_adequacy: bool | None = None
    response_adequacy_meaning: str = "NOT_SELECTED"
    duration_error_counts: tuple[tuple[str, int | None], ...] = ()

    def __post_init__(self):
        for value in (self.case_id, self.unit_id, self.arm_id):
            validate_stable_id(value)
        if (self.disposition not in ("FINITE", "UNEVALUABLE", "NONUSE", "MISSING")
                or any(type(value) is not bool for value in (self.functional_reliable, self.conditional_admission, self.false_admission))
                or self.covered is not None and type(self.covered) is not bool
                or self.reasons != tuple(sorted(set(self.reasons)))
                or self.false_admission and not self.conditional_admission
                or self.disposition != "FINITE" and (self.actual_error is not None or self.functional_reliable)):
            raise ValueError("functional result changes a complete original adverse/nonuse disposition")
        if (self.response_adequacy is not None and type(self.response_adequacy) is not bool
                or self.response_adequacy_meaning not in ("NOT_SELECTED", "SAMPLED_FACTOR_RESPONSE_ADEQUACY_THROUGH64_NOT_EXTERNAL_TASK")
                or self.response_adequacy_meaning == "NOT_SELECTED" and self.response_adequacy is not None
                or self.response_adequacy_meaning != "NOT_SELECTED" and self.functional_reliable != (self.response_adequacy is True)):
            raise ValueError("functional result confuses sampled response adequacy, unknowns or an external task")
        if self.duration_error_counts:
            from empirical_lawhood.adapters.methods.matrix_scheduled_history.e4_structural_prediction import RELATION_METHODS
            if (type(self.duration_error_counts) is not tuple
                    or tuple(method for method, _ in self.duration_error_counts) != RELATION_METHODS
                    or any(value is not None and (type(value) is not int or not 0 <= value <= 58)
                        for _, value in self.duration_error_counts)
                    or self.response_adequacy_meaning == "NOT_SELECTED"):
                raise ValueError("prepared duration comparison changes its frozen account menu or exact K denominator")


@dataclass(frozen=True, slots=True)
class MatrixPreparationNomination(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/preparation-nomination"
    VERSION: ClassVar[str] = "2.0.0"
    result_id: str
    specification: ObjectIdentity
    package: ObjectIdentity
    roster: ObjectIdentity
    evidence: ObjectIdentity
    development_unit_ids: tuple[str, ...]
    candidate_results: tuple[tuple[str, int, int, Decimal | None], ...]
    recoverable_unit_ids: tuple[str, ...]
    selected_arm_id: str | None
    selected_recipe: ObjectIdentity | None
    hold_recipe: ObjectIdentity
    functional_criterion: MatrixFunctionalCriterion
    tie_policy: str
    disposition: str
    cases: tuple[MatrixFunctionalCaseResult, ...]
    standing: str = STANDING
    paired_adequacy: tuple[tuple[str, MatrixPairedAdequacy], ...] = ()

    def __post_init__(self):
        validate_stable_id(self.result_id)
        if (self.disposition not in ("NOMINATED", "NONDISCRIMINATING_OPPORTUNITY", "UNEVALUABLE_OPPORTUNITY")
                or (self.selected_arm_id is None) != (self.selected_recipe is None)
                or (self.selected_arm_id is not None) != (self.disposition == "NOMINATED")
                or self.standing != STANDING
                or self.development_unit_ids != tuple(sorted(set(self.development_unit_ids)))
                or self.recoverable_unit_ids != tuple(sorted(set(self.recoverable_unit_ids)))
                or not set(self.recoverable_unit_ids) <= set(self.development_unit_ids)):
            raise ValueError("preparation nomination changes its bounded opportunity or original development census")
        if type(self.functional_criterion) is not MatrixFunctionalCriterion:
            raise TypeError("preparation nomination requires its exact frozen endpoint")
        self.functional_criterion.__post_init__()
        if self.functional_criterion.is_matched:
            from .functional_outcome_reduction import _matched_nomination_values

            arms = tuple(sorted({row.arm_id for row in self.cases}))
            prepared = tuple(row[0] for row in self.candidate_results)
            baseline = tuple(arm for arm in arms if arm not in prepared)
            if len(baseline) != 1 or len(arms) != 3 or len(prepared) != 2:
                raise ValueError("matched nomination omits the original ramp or an assigned alternative")
            expected = _matched_nomination_values(self.development_unit_ids, arms, baseline[0], self.cases)
            if ((self.candidate_results, self.recoverable_unit_ids, self.selected_arm_id, self.disposition, self.paired_adequacy) != expected
                    or self.tie_policy != "MINIMUM_TOTAL_EFFORT_THEN_LEXICAL"):
                raise ValueError("matched nomination changes actual rescues, worst-case net gain or the frozen tie rule")
        elif self.paired_adequacy:
            raise ValueError("original nomination cannot claim the amended paired criterion")

    @property
    def identity(self):
        return identity(self)


@dataclass(frozen=True, slots=True)
class MatrixFunctionalComparison(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/functional-comparison"
    VERSION: ClassVar[str] = "2.0.0"
    comparison_id: str
    assigned_group_ids: tuple[str, ...]
    successes: int
    usable_groups: int
    conditionally_admitted_groups: int
    false_admissions: int
    covered_groups: int
    bounded_groups: int
    missing_group_ids: tuple[str, ...]
    p_value_numerator: int
    p_value_denominator: int
    criterion_met_conditionally: bool
    total_preparation_effort: Decimal | None
    transfer_regime_id: str | None = None
    transfer_domain_claim: str | None = None
    paired_adequacy: MatrixPairedAdequacy | None = None
    duration_inference: AssignedBinomialInference | None = None

    def __post_init__(self):
        validate_stable_id(self.comparison_id)
        n = len(self.assigned_group_ids)
        if (not n or self.assigned_group_ids != tuple(sorted(set(self.assigned_group_ids)))
                or any(type(value) is not int or not 0 <= value <= n for value in (
                    self.successes, self.usable_groups, self.conditionally_admitted_groups,
                    self.false_admissions, self.covered_groups, self.bounded_groups))
                or not set(self.missing_group_ids) <= set(self.assigned_group_ids)
                or type(self.p_value_numerator) is not int or type(self.p_value_denominator) is not int
                or not 0 <= self.p_value_numerator <= self.p_value_denominator or self.p_value_denominator < 1
                or type(self.criterion_met_conditionally) is not bool):
            raise ValueError("functional comparison drops assigned groups or changes exact conditional probability")
        if self.paired_adequacy is not None:
            paired = self.paired_adequacy
            if type(paired) is not MatrixPairedAdequacy:
                raise TypeError("paired comparison requires its complete original adequacy table")
            paired.__post_init__()
            if (self.comparison_id != "e5.preparation" or paired.group_ids != self.assigned_group_ids
                    or self.successes != paired.conservative.gains or self.usable_groups != paired.observed.unit_count
                    or self.missing_group_ids != paired.unknown_group_ids
                    or Fraction(self.p_value_numerator, self.p_value_denominator) != paired.conservative.tail_probability
                    or self.criterion_met_conditionally != paired.criterion_met):
                raise ValueError("paired comparison changes the all-assigned test or practical-benefit decision")
        if self.duration_inference is not None:
            inference = self.duration_inference
            if type(inference) is not AssignedBinomialInference:
                raise TypeError("transfer comparison requires its complete assigned duration-win inference")
            inference.__post_init__()
            if (self.paired_adequacy is not None or self.comparison_id not in ("e6.nearby", "e6.shifted")
                    or self.assigned_group_ids != inference.unit_ids or n != 64
                    or (inference.null_numerator, inference.null_denominator, inference.alpha_numerator, inference.alpha_denominator) != (1, 2, 1, 160)
                    or self.successes != inference.successes or self.usable_groups != n - inference.unknowns
                    or self.missing_group_ids != tuple(group for group, event in zip(inference.unit_ids, inference.events, strict=True) if event is None)
                    or (self.p_value_numerator, self.p_value_denominator) != (inference.tail_numerator, inference.tail_denominator)
                    or self.criterion_met_conditionally != inference.criterion_met):
                raise ValueError("transfer comparison changes SR/BR duration inference or the full64 denominator")


@dataclass(frozen=True, slots=True)
class MatrixCurveFunctionalComparison(MatrixFunctionalComparison):
    """Prospective E6 curve comparison; the original duration result stays separate."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-experimental-programme/curve-functional-comparison'
    VERSION: ClassVar[str] = '1.0.0'
    curve_decisions: tuple[MatchedCurveDecision, ...] = field(kw_only=True)
    curve_inference: AssignedBinomialInference = field(kw_only=True)

    def __post_init__(self):
        MatrixFunctionalComparison.__post_init__(self)
        if (self.duration_inference is not None or self.paired_adequacy is not None
                or self.comparison_id not in ('e6.nearby', 'e6.shifted') or len(self.assigned_group_ids) != 64
                or type(self.curve_decisions) is not tuple
                or any(type(row) is not MatchedCurveDecision or row.structural_method != 'SR' or row.coordinate_count != 1
                    for row in self.curve_decisions)
                or tuple(row.unit_id for row in self.curve_decisions) != self.assigned_group_ids):
            raise ValueError('curve transport comparison changes its frozen SR/BR claim or complete64 denominator')
        for row in self.curve_decisions:
            row.__post_init__()
        inference = matched_primary_inference(self.curve_decisions)
        if (self.curve_inference != inference or self.successes != inference.successes
                or self.usable_groups != 64 - inference.unknowns
                or self.missing_group_ids != tuple(row.unit_id for row in self.curve_decisions if not row.usable)
                or (self.p_value_numerator, self.p_value_denominator) != (inference.tail_numerator, inference.tail_denominator)
                or self.criterion_met_conditionally != inference.criterion_met):
            raise ValueError('curve transport comparison alters its inclusive margin or assigned unknown events')


@dataclass(frozen=True, slots=True)
class MatrixFunctionalAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/functional-assessment"
    result_id: str
    specification: ObjectIdentity
    package: ObjectIdentity
    roster: ObjectIdentity
    evidence: ObjectIdentity
    nomination: ObjectIdentity | None
    comparisons: tuple[MatrixFunctionalComparison | MatrixCurveFunctionalComparison, ...]
    cases: tuple[MatrixFunctionalCaseResult, ...]
    unused_family_slots: tuple[str, ...]
    assumptions: str = "SOURCE_SUPPORT_SAMPLING_RESERVATION_CHRONOLOGY_NOT_AUTHENTICATED_BY_THIS_CALCULATION"
    qualification: str = "NOT_ESTABLISHED"
    standing: str = STANDING

    def __post_init__(self):
        validate_stable_id(self.result_id)
        if (self.qualification != "NOT_ESTABLISHED" or self.standing != STANDING
                or self.assumptions != "SOURCE_SUPPORT_SAMPLING_RESERVATION_CHRONOLOGY_NOT_AUTHENTICATED_BY_THIS_CALCULATION"):
            raise ValueError("functional assessment promotes conditional arithmetic into qualification")


def source_allocation(specification, roster):
    """Derive units from original allocation members; views/arms remain nested."""
    from .source_selection_metadata import _source_allocation

    return _source_allocation(phase=specification.phase, selection_sha256=specification.fingerprint(), roster=roster)

def validate_sources(specification, roster, package):
    if (type(specification) is not MatrixLaterExperimentSpecification or type(roster) is not MatrixProgrammeRoster
            or type(package) is not MatrixFrozenConsumerPackage):
        raise TypeError("later Matrix assessment requires its exact typed selection, original roster and frozen package")
    for value in (specification, roster, package):
        value.__post_init__()
    from .source_selection_metadata import _validate_source_metadata

    return _validate_source_metadata(phase=specification.phase, roster_reference=specification.roster,
        package_reference=specification.package, expected_groups=specification.expected_groups, arm_ids=specification.arm_ids,
        transfer_regime_ids=specification.transfer_regime_ids, selection_sha256=specification.fingerprint(), roster=roster, package=package)

def _case_result(specification, package, case, observed):
    criterion = specification.criterion
    forecast = None if observed is None else observed.forecast
    score = None if observed is None else observed.score
    reasons = []
    if observed is None or score is None or forecast is None:
        return MatrixFunctionalCaseResult(case.case_id, case.unit_id, case.arm_id, "MISSING", None, None, None,
            False, False, None, False, case.preparation_effort, ("MISSING_ORIGINAL_FORECAST_OR_SCORE",))
    public = case.public_source
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.forecast import FAMILY_MAP
    if public.policy.cutoff_tick + criterion.horizon_tick > public.coordinate.total_ticks:
        raise ValueError("functional endpoint exceeds its complete original physical source horizon")
    if (score.source != public.source or score.root_id != public.root.root_id or score.independent_group_id != case.unit_id
            or forecast.source != public.source or score.error_forecast != original_identity(forecast)
            or score.causal_prefix != forecast.prefix or score.role != public.root.role.value
            or forecast.feature.independent_group_id != case.unit_id
            or forecast.feature.root_id != public.root.root_id or forecast.model != package.component("model")
            or forecast.criterion != package.component("criterion") or score.criterion != package.component("criterion")
            or forecast.calibration != package.component("calibration") or forecast.scope != CALIBRATED_QUERY):
        raise ValueError("later assessment substitutes its original causal forecast, selected model/criterion or source")
    if forecast.feature.clock_id != public.root.clock_id or forecast.feature.family_id != FAMILY_MAP[public.coordinate.family_id]:
        raise ValueError("later assessment changes original source clock or preparation family")
    _validate_original_score(score)
    if forecast.feature.cutoff != public.coordinate.physical_time(public.policy.cutoff_tick):
        raise ValueError("later assessment changes observation-assisted pre-future handoff cutoff")
    applicability = []
    if observed.source_support != "SUPPORTED":
        applicability.append("SOURCE_SUPPORT_" + observed.source_support)
    if not case.native_assessments or not observed.supplier_assessments:
        applicability.append("MISSING_INDEPENDENT_SOURCE_OR_SUPPLIER_ASSESSMENT")
    if not score.numerical_pass or score.disposition != "FINITE" or forecast.feature.disposition != "AVAILABLE":
        reasons.extend(("ORIGINAL_SCORE_" + score.disposition, "ORIGINAL_FEATURE_" + forecast.feature.disposition))
    cells = tuple(row for row in score.cells if row.predictor == criterion.predictor and row.horizon_tick <= criterion.horizon_tick)
    views = {view: tuple(row for row in cells if row.view == view) for view in ("PRIMARY", "FINE")}
    expected = 2 * 4 * ((16, 64, 128).index(criterion.horizon_tick) + 1)
    if (any(len(rows) != expected for rows in views.values())
            or {row.key[1:] for row in views["PRIMARY"]} != {row.key[1:] for row in views["FINE"]}):
        raise ValueError("functional endpoint omits a paired view, action, panel or preceding horizon")
    panels = {row.panel_id for row in cells}
    actions = {row.action_id for row in cells}
    horizons = (16, 64, 128)[:(16, 64, 128).index(criterion.horizon_tick) + 1]
    if len(panels) != 2 or len(actions) != 4 or {row.key[1:] for row in views["PRIMARY"]} != {
            (panel, action, criterion.predictor, horizon) for panel in panels for action in actions for horizon in horizons}:
        raise ValueError("functional endpoint replaces the complete original counterfactual menu")
    losses = []
    for view in ("PRIMARY", "FINE"):
        rows = views[view]
        values = tuple(row.normalized_error for row in rows)
        if any(value is None for value in values):
            reasons.append("MISSING_NATIVE_RESPONSE")
        else:
            losses.append(max(values))
    for left, right in zip(sorted(views["PRIMARY"], key=lambda row: row.key[1:]),
            sorted(views["FINE"], key=lambda row: row.key[1:]), strict=True):
        if (left.normalized_error is not None and right.normalized_error is not None
                and abs(Fraction(left.normalized_error)-Fraction(right.normalized_error)) > Fraction(criterion.paired_view_discrepancy_maximum)):
            reasons.append("PAIRED_VIEW_DISCREPANCY")
    index = ("FACTOR", "FULL_COUPLED", "GENERIC_SLOW", "NORM_RADIUS", "SPECTRA").index(criterion.predictor) * 3 + (16, 64, 128).index(criterion.horizon_tick)
    point, upper = forecast.log_error_points[index], forecast.log_error_uppers[index]
    if point is None:
        reasons.append("MISSING_PRE_FUTURE_PREDICTION")
    if reasons:
        return MatrixFunctionalCaseResult(case.case_id, case.unit_id, case.arm_id,
            "NONUSE" if score.disposition == "NO_ORIGIN" else "UNEVALUABLE", None, point, upper,
            False, False, None, False, case.preparation_effort, tuple(sorted(set(reasons))))
    actual = max(losses)
    # Monotonic log1p comparison uses high precision and retains an unbounded
    # None upper as unbounded; no transfer-dependent recalibration occurs.
    from decimal import localcontext
    with localcontext() as context:
        context.prec = 80
        actual_log = (1 + actual).ln()
        threshold_log = (1 + criterion.normalized_error_maximum).ln()
    comparator = observed.comparator_forecast
    if comparator is None:
        comparator_error = None
        applicability.append("MISSING_ORIGINAL_SAME_INFORMATION_COMPARATOR")
    else:
        if (comparator.feature != forecast.feature or comparator.source != forecast.source or comparator.prefix != forecast.prefix
                or comparator.model != package.component("comparator") or comparator.criterion != forecast.criterion
                or comparator.calibration != package.component("comparator-calibration") or comparator.scope != CALIBRATED_QUERY):
            raise ValueError("later assessment changes the frozen same-information comparator or its cutoff")
        with localcontext() as context:
            context.prec = 80
            comparator_error = None if comparator.log_error_points[index] is None else abs(actual_log - comparator.log_error_points[index])
    admitted = upper is not None and upper <= threshold_log and observed.source_support == "SUPPORTED" and bool(case.native_assessments) and bool(observed.supplier_assessments)
    reliable = actual <= criterion.normalized_error_maximum
    with localcontext() as context:
        context.prec = 80
        forecast_error = abs(actual_log - point)
    return MatrixFunctionalCaseResult(case.case_id, case.unit_id, case.arm_id, "FINITE", actual, point, upper,
        reliable, admitted, None if upper is None else actual_log <= upper, admitted and not reliable,
        case.preparation_effort, tuple(sorted((*applicability,
            "FINITE_ORIGINAL_RESPONSE" if upper is not None else "UNBOUNDED_FROZEN_FORECAST"))),
        forecast_error, comparator_error, observed.source_support)


def _validate_original_score(score):
    """Check the original score's complete endpoint/cumulative projection.

    Literal native transitions remain independently owned by the original
    assessor. This check never manufactures a missing numerical assessment.
    """
    from decimal import localcontext
    from empirical_lawhood.adapters.methods.matrix_factor_response.records import PREDICTORS

    if score.dense is not None:
        from empirical_lawhood.adapters.methods.matrix_factor_response.response_scoring import MatrixDenseResponseDiagnostics
        if type(score.dense) is not MatrixDenseResponseDiagnostics:
            raise TypeError("original dense score requires its exact complete diagnostics")
        score.__post_init__()
        score.dense.validate_cells(score.cells)
        if (score.cumulative_log_errors != score.dense.factor_log_targets
                or score.numerical_pass != score.dense.numerical_usable):
            raise ValueError("original dense score changes its complete paired58 FACTOR targets")
        return
    panels = {row.panel_id for row in score.cells}
    actions = {row.action_id for row in score.cells}
    if len(panels) != 2 or len(actions) != 4 or {row.key for row in score.cells} != {
            (view, panel, action, predictor, horizon) for view in ("PRIMARY", "FINE") for panel in panels
            for action in actions for predictor in PREDICTORS for horizon in (16, 64, 128)}:
        raise ValueError("original response score omits its complete view/panel/action/15-output census")
    if score.numerical_pass and (len(score.controls) != 48 or len({row.control_id for row in score.controls}) != 48):
        raise ValueError("original response score thins its complete48 native branch controls")
    cumulative = []
    for predictor in PREDICTORS:
        for horizon in (16, 64, 128):
            values = tuple(row.normalized_error for row in score.cells
                if row.view == "PRIMARY" and row.predictor == predictor and row.horizon_tick <= horizon)
            with localcontext() as context:
                context.prec = 50
                cumulative.append(None if not score.numerical_pass or any(value is None for value in values)
                    else (Decimal(1) + max(values)).ln())
    if tuple(cumulative) != score.cumulative_log_errors:
        raise ValueError("original response score changes its exact complete cumulative projection")


def validate_evidence(specification, roster, package, evidence):
    allocation, design = validate_sources(specification, roster, package)
    if (type(evidence) is not MatrixProgrammeEvidence or evidence.identity != specification.evidence
            or evidence.roster != roster.identity or evidence.package != package.identity):
        raise ValueError("later assessment changes its selected original evidence bank")
    evidence.__post_init__()
    observations = {row.case_id: row for row in evidence.rows}
    if set(observations) - {case.case_id for case in roster.cases}:
        raise ValueError("later assessment adds unassigned source cases")
    results = tuple(_case_result(specification, package, case, observations.get(case.case_id)) for case in roster.cases)
    return allocation, design, results


def nominate_preparation(specification, roster, package, evidence, *, result_id):
    if specification.phase != "E5_OPPORTUNITY":
        raise ValueError("recipe nomination may consume only the declared development opportunity population")
    allocation, _, cases = validate_evidence(specification, roster, package, evidence)
    from .functional_outcome_reduction import _nominate_functional_cases

    return _nominate_functional_cases(result_id=result_id, specification_identity=specification.identity,
        package_identity=package.identity, roster_identity=roster.identity, evidence_identity=evidence.identity,
        group_ids=allocation.unit_ids(), arm_ids=specification.arm_ids, hold_arm_id=specification.hold_arm_id,
        criterion=specification.criterion, minimum_recoverable_groups=specification.minimum_recoverable_groups,
        tie_policy=specification.tie_policy,
        recipes=tuple((arm, next(case.recipe for case in roster.cases if case.arm_id == arm)) for arm in specification.arm_ids), cases=cases)


def _comparison(specification, comparison_id, groups, successes, rows):
    from .functional_outcome_reduction import _functional_comparison

    return _functional_comparison(specification.criterion, comparison_id, groups, successes, rows)


def _effort_sum(values):
    """Preserve exact declared Decimal effort independently of caller precision."""
    from decimal import localcontext

    exact = sum((Fraction(value) for value in values), Fraction(0))
    numerator, denominator = Decimal(exact.numerator), Decimal(exact.denominator)
    with localcontext() as context:
        context.prec = len(numerator.as_tuple().digits) + 4 * len(denominator.as_tuple().digits) + 10
        return numerator / denominator


def assess_later_programme(specification, roster, package, evidence, *, result_id, nomination=None):
    from .selection_metadata import validate_phase_metadata

    allocation, _, cases = validate_evidence(specification, roster, package, evidence)
    if specification.phase == "E5_OPPORTUNITY":
        raise ValueError("development opportunity requires recipe nomination, not confirmation")
    from .functional_outcome_reduction import _confirmation_comparisons, _transfer_comparisons

    prepared = validate_phase_metadata(specification, roster, package, allocation, nomination)
    if specification.phase == "E5_CONFIRMATION":
        comparisons = _confirmation_comparisons(specification.criterion, allocation.unit_ids(), prepared,
            specification.hold_arm_id, cases)
    else:
        regime_groups = tuple((regime, tuple(sorted({case.unit_id for case in roster.cases
            if case.public_source.root.regime_id == regime}))) for regime in specification.transfer_regime_ids)
        comparisons = _transfer_comparisons(specification.criterion, regime_groups,
            specification.transfer_domain_claims, specification.hold_arm_id, cases)
    used = {row.comparison_id for row in comparisons}
    return MatrixFunctionalAssessment(result_id, specification.identity, package.identity, roster.identity, evidence.identity,
        None if nomination is None else nomination.identity, comparisons, cases,
        tuple(slot for slot in specification.criterion.family_slots if slot not in used))
