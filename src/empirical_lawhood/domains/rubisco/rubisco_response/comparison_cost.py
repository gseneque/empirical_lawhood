# SPDX-License-Identifier: MPL-2.0
"""Three exact cost accounts over complete original inquiry attempt censuses.

Physical events are deduplicated by the shared inquiry contract. Full common
charges remain in both comparison arms. Unknown classifications or measurements
cannot manufacture a saving. Amortization is an explicit repeat scenario, not
an observation of future cost.
"""

from dataclasses import dataclass
from decimal import localcontext
from fractions import Fraction
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_insilico_mechanism.contracts import Exact
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_inquiry import AcquisitionEvent, InquiryAttempt, InquiryCost, summarize_cost
from empirical_lawhood.science.inquiry.recursive_inquiry_policy import InquiryAttemptWorkBinding, WorkBoundInquiryState
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_ids, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.comparison_preparation import COST_ARMS, ResponseComparisonDesign
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact

FIELDS = ("cpu_seconds", "wall_seconds", "retained_bytes")
UNMEASURED = ("campaign-elapsed-wall-seconds", "gpu-seconds", "native-call-count", "peak-memory-bytes")
UNKNOWN = InquiryCost(None, None, None)


def _sum(events):
    values = tuple(value for event in events for name in FIELDS if (value := getattr(event.cost, name)) is not None)
    digits = max((max(1, value.adjusted() + 1) for value in values), default=1)
    places = max((max(0, -value.as_tuple().exponent) for value in values), default=0)
    with localcontext() as context:
        context.prec = digits + places + len(str(len(events))) + 2
        return summarize_cost(events)


def _events(values):
    if type(values) is not tuple:
        raise ValueError("comparison costs require immutable original events")
    require_sorted_unique_ids(values, attribute="event_id", field_name="cost_events")
    for row in values:
        exact(row, AcquisitionEvent)
        exact(row.cost, InquiryCost)


def _merge_states(states):
    if type(states) is not tuple:
        raise ValueError("comparison costs need their complete original source states")
    require_sorted_unique_ids(states, attribute="state_id", field_name="states")
    attempts, events, bindings = {}, {}, {}
    for state in states:
        exact(state, WorkBoundInquiryState)
        for actual, target, field in ((state.operational_census, attempts, "attempt_id"),
                (state.cost_events, events, "event_id"), (state.attempt_work_bindings, bindings, "attempt_id")):
            for row in actual:
                key = getattr(row, field)
                if key in target and target[key] != row:
                    raise ValueError("comparison histories conflict on an original attempt, work binding or cost event")
                target[key] = row
    attempt_rows = tuple(attempts[key] for key in sorted(attempts))
    event_rows = tuple(events[key] for key in sorted(events))
    binding_rows = tuple(bindings[key] for key in sorted(bindings))
    _events(event_rows)
    if {row.attempt_id: row.receipt for row in event_rows} != {row.attempt_id: row.receipt for row in attempt_rows}:
        raise ValueError("comparison cost census loses an original failed or unknown attempt")
    # Enforce the shared one-physical-event-per-attempt rule before any projection.
    _sum(event_rows)
    return attempt_rows, event_rows, binding_rows


@dataclass(frozen=True, slots=True)
class ExactComparisonCost(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/exact-comparison-cost"
    cpu_seconds: Exact | None
    wall_seconds: Exact | None
    retained_bytes: Exact | None

    def __post_init__(self):
        for name in FIELDS:
            value = getattr(self, name)
            if value is not None:
                exact(value, Exact)
                if value.fraction < 0:
                    raise ValueError("exact cost account cannot be negative")


def _amortized(setup, use, audit, count, *, per_use):
    result = []
    for name in FIELDS:
        operands = tuple(getattr(value, name) for value in (setup, use, audit))
        if any(value is None for value in operands):
            result.append(None)
        else:
            first, repeated, verification = (Fraction(value) for value in operands)
            total = first + count * (repeated + verification)
            result.append(Exact.of(total / count if per_use else total))
    return ExactComparisonCost(*result)


@dataclass(frozen=True, slots=True)
class ComparisonArmCost(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/comparison-arm-cost"
    arm: str
    setup_events: tuple[AcquisitionEvent, ...]
    use_events: tuple[AcquisitionEvent, ...]
    audit_events: tuple[AcquisitionEvent, ...]
    complete_classification: bool
    planned_reuse_count: int
    setup: InquiryCost
    incremental_use: InquiryCost
    equivalent_audit: InquiryCost
    frozen_policy_use: InquiryCost
    amortized_total: ExactComparisonCost
    amortized_per_use: ExactComparisonCost

    def __post_init__(self):
        if self.arm not in COST_ARMS or type(self.complete_classification) is not bool:
            raise ValueError("cost arm needs its actual complete classification state")
        if type(self.planned_reuse_count) is not int or self.planned_reuse_count < 1:
            raise ValueError("amortization needs its frozen positive reuse denominator")
        for values in (self.setup_events, self.use_events, self.audit_events):
            _events(values)
        events = (*self.setup_events, *self.use_events, *self.audit_events)
        if len({row.event_id for row in events}) != len(events):
            raise ValueError("one physical event cannot be charged twice inside one comparison arm")
        expected = _arm_totals(self.setup_events, self.use_events, self.audit_events,
            self.complete_classification, self.planned_reuse_count)
        for value in (self.setup, self.incremental_use, self.equivalent_audit, self.frozen_policy_use):
            exact(value, InquiryCost)
        for value in (self.amortized_total, self.amortized_per_use):
            exact(value, ExactComparisonCost)
        if (self.setup, self.incremental_use, self.equivalent_audit, self.frozen_policy_use,
                self.amortized_total, self.amortized_per_use) != expected:
            raise ValueError("comparison arm drops setup, failed use, equal audit or exact amortization")


def _arm_totals(setup_events, use_events, audit_events, complete, count):
    setup, use, audit = tuple(_sum(events) if complete else UNKNOWN for events in (setup_events, use_events, audit_events))
    frozen_use = _sum((*use_events, *audit_events)) if complete else UNKNOWN
    return setup, use, audit, frozen_use, _amortized(setup, use, audit, count, per_use=False), _amortized(setup, use, audit, count, per_use=True)


def _cost_values(design, states):
    attempts, events, bindings = _merge_states(states)
    allocation = {row.work: row for row in design.cost_work}
    by_attempt = {row.attempt_id: row.work for row in bindings}
    unclassified = tuple(row.attempt_id for row in attempts if by_attempt[row.attempt_id] not in allocation)
    missing = tuple(sorted(row.work.fingerprint() for row in design.cost_work if row.work not in by_attempt.values()))
    complete = bool(states) and bool(allocation) and not unclassified and not missing
    arms = []
    for arm in COST_ARMS:
        assigned = {phase: tuple(row for row in events if (selection := allocation.get(by_attempt[row.attempt_id])) is not None
            and selection.phase == phase and arm in selection.charged_arms) for phase in ("SETUP", "USE", "AUDIT")}
        # A missing comparison arm cannot gain a measured zero-cost performance.
        arm_complete = complete and bool(assigned["USE"])
        groups = assigned["SETUP"], assigned["USE"], assigned["AUDIT"]
        arms.append(ComparisonArmCost(arm, *groups, arm_complete, design.study.acceptance.planned_reuse_count,
            *_arm_totals(*groups, arm_complete, design.study.acceptance.planned_reuse_count)))
    return attempts, events, bindings, unclassified, missing, _sum(events) if states else UNKNOWN, tuple(arms)


def _metric(design):
    selected = design.study.acceptance
    return {("complete_cpu_time", "s"): "cpu_seconds", ("complete_wall_time", "s"): "wall_seconds",
        ("retained_storage", "bytes"): "retained_bytes"}.get((selected.cost_metric, selected.cost_unit))


def _cost_comparison(design, arms):
    field = _metric(design)
    if field is None:
        return A.UNEVALUABLE, None, "UNSUPPORTED_SELECTED_METRIC"
    conventional, reduced = arms
    costs = tuple(getattr(row.amortized_total, field) for row in arms)
    if any(value is None for value in costs):
        return A.UNEVALUABLE, None, "UNKNOWN_OR_INCOMPLETE_MEASUREMENT"
    disposition = A.SATISFIED if costs[1].fraction < costs[0].fraction else A.FALSIFIED
    setup_delta = Fraction(getattr(reduced.setup, field)) - Fraction(getattr(conventional.setup, field))
    repeated_saving = Fraction(getattr(conventional.frozen_policy_use, field)) - Fraction(getattr(reduced.frozen_policy_use, field))
    if repeated_saving > 0:
        # Strict savings: equality at an integer count is not a break-even win.
        count = max(1, setup_delta // repeated_saving + 1)
        return disposition, count, "CONDITIONAL_SUSTAINED_BREAK_EVEN_UNDER_EXPLICIT_REPEATED_COSTS"
    if repeated_saving == 0 and setup_delta < 0:
        return disposition, 1, "CONDITIONAL_SUSTAINED_BREAK_EVEN_UNDER_EXPLICIT_REPEATED_COSTS"
    return disposition, None, "NO_SUSTAINED_BREAK_EVEN_UNDER_EXPLICIT_REPEATED_COSTS"


@dataclass(frozen=True, slots=True)
class ComparisonCostAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/comparison-cost-assessment"
    assessment_id: str
    design: ResponseComparisonDesign
    states: tuple[WorkBoundInquiryState, ...]
    attempts: tuple[InquiryAttempt, ...]
    events: tuple[AcquisitionEvent, ...]
    work_bindings: tuple[InquiryAttemptWorkBinding, ...]
    unclassified_attempt_ids: tuple[str, ...]
    missing_work_fingerprints: tuple[str, ...]
    complete_campaign: InquiryCost
    arms: tuple[ComparisonArmCost, ...]
    conditional_cost_criterion: A
    break_even_reuse_count: int | None
    break_even_interpretation: str
    unmeasured_metric_ids: tuple[str, ...] = UNMEASURED
    interpretation: str = "COMPLETE_SELECTED_RETAINED_CENSUS_AND_EXPLICIT_REUSE_SCENARIO_NOT_SIMULATOR_SPEEDUP"

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        exact(self.design, ResponseComparisonDesign)
        expected = _cost_values(self.design, self.states)
        actual = (self.attempts, self.events, self.work_bindings, self.unclassified_attempt_ids,
            self.missing_work_fingerprints, self.complete_campaign, self.arms)
        if actual != expected:
            raise ValueError("comparison cost assessment changes an original attempt, unknown cost or full shared charge")
        for row in self.arms:
            exact(row, ComparisonArmCost)
        if (self.conditional_cost_criterion, self.break_even_reuse_count, self.break_even_interpretation) != _cost_comparison(self.design, self.arms):
            raise ValueError("comparison changes its declared metric, reuse denominator or strict break-even calculation")
        if self.break_even_reuse_count is not None and type(self.break_even_reuse_count) is not int:
            raise ValueError("break-even count must be an exact integer")
        if (self.unmeasured_metric_ids != UNMEASURED
                or self.interpretation != "COMPLETE_SELECTED_RETAINED_CENSUS_AND_EXPLICIT_REUSE_SCENARIO_NOT_SIMULATOR_SPEEDUP"):
            raise ValueError("retained task expenses cannot invent unmeasured resources or whole-simulator acceleration")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.assessment_id, self)


def assess_comparison_costs(design, states, *, assessment_id):
    exact(design, ResponseComparisonDesign)
    values = _cost_values(design, states)
    return ComparisonCostAssessment(assessment_id, design, states, *values, *_cost_comparison(design, values[-1]))
