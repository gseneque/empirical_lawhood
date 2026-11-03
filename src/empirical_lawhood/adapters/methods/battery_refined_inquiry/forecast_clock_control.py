# SPDX-License-Identifier: MPL-2.0
"""Actual-assignment clock coverage with the separately fixed source20 budget.

Legacy clock policies and outcomes are unchanged. Every original returned call
is retained, including unavailable clock/vector operands. Exact binary64
coverage cannot establish continuous time, hybrid event validity or admission.
"""

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_sha256, validate_stable_id

from . import forecast_state_control as state
from . import forecast_state_orchestration as orchestration
from . import forecast_step_control as step
from . import lossless_segment_consumer as consumer
from . import representable_clock as clock
from . import segmented_fidelity_stream as paired
from . import segmented_qualification as qualification
from . import segmented_science as science

SCOPE = "SOURCE20_FIXED_BUDGET_FINITE_BINARY64_CLOCK_ONLY;ORIGINAL_GAPS_EVENTS_SUFFIXES_RETAINED;NO_CONTINUOUS_TIME_OR_ADMISSION"
DOMAIN = "FINITE_BINARY64_GLOBAL_CLOCK;NO_INTERIOR_OPERAND_BETWEEN_ADJACENT_VALUES"
MISSING = "actual-full-clock-or-complete-one-sided-vectors-unavailable"


@dataclass(frozen=True, slots=True)
class ForecastClockPolicy(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/forecast-clock-policy"
    policy_id: str
    scientific_control: state.ForecastStateControl
    clock_algorithm_source_sha256: str
    selected_step_source_sha256: str
    clock_domain: str = DOMAIN
    scope: str = SCOPE

    def __post_init__(self):
        validate_stable_id(self.policy_id)
        validate_sha256(self.clock_algorithm_source_sha256)
        validate_sha256(self.selected_step_source_sha256)
        if type(self.scientific_control) is not state.ForecastStateControl or self.clock_domain != DOMAIN or self.scope != SCOPE:
            raise ValueError("forecast clock policy changes actual scientific control or finite-domain scope")
        self.scientific_control.__post_init__()

    @property
    def comparison_rtol(self):
        return self.scientific_control.native_policy.comparison_budget.rtol

    @property
    def comparison_atol(self):
        return self.scientific_control.native_policy.comparison_budget.atol


def require_sources(policy):
    if type(policy) is not ForecastClockPolicy:
        raise ValueError("forecast clock control needs its actual typed prospective policy")
    policy.__post_init__()
    state.require_algorithm_sources(policy.scientific_control)
    if sha256(Path(clock.__file__).read_bytes()).hexdigest() != policy.clock_algorithm_source_sha256:
        raise ValueError("forecast clock changes its authenticated exact coverage/boundary algorithm")


@dataclass(frozen=True, slots=True)
class ForecastClockCall(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/forecast-clock-call"
    summary: ObjectIdentity
    request: ObjectIdentity
    full_state: ObjectIdentity | None
    returned_clock: clock.ClockCall | None
    reason_codes: tuple[str, ...]

    def __post_init__(self):
        if (type(self.summary) is not ObjectIdentity or self.summary.object_schema != "empirical-lawhood/battery-segmented/segment-summary"
                or type(self.request) is not ObjectIdentity or self.request.object_schema != "empirical-lawhood/battery-segmented/native-request"
                or self.full_state is not None and (type(self.full_state) is not ObjectIdentity
                    or self.full_state.object_schema != "empirical-lawhood/battery-segmented/full-state-segment")
                or self.returned_clock is not None and type(self.returned_clock) is not clock.ClockCall
                or self.reason_codes not in ((), (MISSING,))
                or self.returned_clock is None and self.reason_codes != (MISSING,)):
            raise ValueError("forecast clock call loses a complete original or its unavailable outcome")
        if self.returned_clock is not None:
            self.returned_clock.__post_init__()
            if (self.returned_clock.summary, self.returned_clock.request, self.returned_clock.full_state) != (
                    self.summary, self.request, self.full_state):
                raise ValueError("forecast clock call substitutes its original clock/state/request operands")


def _reasons(original, calls, boundaries):
    available = tuple(tuple(row.returned_clock for row in side if row.returned_clock is not None) for side in calls)
    _, legacy_reasons = clock._reasons(original, available, boundaries)
    reasons = set(legacy_reasons)
    # A changed algebraic constraint/current law can legitimately change
    # algebraic states and returned derivatives. Retain every measured jump;
    # only the independent one-sided event control can assess that boundary.
    # Constant-regime full-row continuity remains the unchanged falsifier.
    continuity = "full-one-sided-state-or-returned-derivative-continuity-falsified"
    if not any(row.actual_model_and_scalar_regime_unchanged and (
            row.state_continuity.failed_components or row.returned_derivative_continuity.failed_components) for row in boundaries):
        reasons.discard(continuity)
    missing = {reason for side in calls for row in side for reason in row.reason_codes}
    expected = tuple((side, i) for side, rows in zip(("LEFT", "RIGHT"), calls, strict=True) for i in range(2, len(rows) + 1))
    if tuple((row.side, row.next_segment) for row in boundaries) != expected:
        missing.add("original-one-sided-boundary-census-unavailable")
    reasons.update(missing)
    adverse = reasons.intersection({continuity, "original-covered-preparation-segment-or-interval-falsified",
        "actual-request-substitutes-previous-complete-terminal-state"})
    return A.FALSIFIED if adverse else A.UNEVALUABLE if reasons else A.SATISFIED, tuple(sorted(reasons))


@dataclass(frozen=True, slots=True)
class ForecastClockAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/forecast-clock-assessment"
    assessment_id: str
    policy: ForecastClockPolicy
    original_pair: state.ForecastStateStream
    complete_call_censuses: tuple[tuple[ForecastClockCall, ...], tuple[ForecastClockCall, ...]]
    boundaries: tuple[clock.ClockBoundary, ...]
    disposition: A
    reason_codes: tuple[str, ...]
    scope: str = SCOPE
    real_open_gaps_retain_original_disposition: bool = True
    whole_time_certified: bool = False
    physical_qualification: bool = False
    later_use_admission: bool = False

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        if type(self.policy) is not ForecastClockPolicy or type(self.original_pair) is not state.ForecastStateStream:
            raise ValueError("forecast clock assessment substitutes its complete actual source20 operands")
        self.policy.__post_init__()
        self.original_pair.__post_init__()
        if (self.policy.scientific_control != self.original_pair.scientific_control
                or type(self.complete_call_censuses) is not tuple or len(self.complete_call_censuses) != 2
                or any(type(side) is not tuple for side in self.complete_call_censuses)
                or tuple(map(len, self.complete_call_censuses)) != self.original_pair.declared_segment_counts
                or self.scope != SCOPE or self.real_open_gaps_retain_original_disposition is not True
                or any(type(value) is not bool or value for value in
                       (self.whole_time_certified, self.physical_qualification, self.later_use_admission))):
            raise ValueError("forecast clock assessment omits complete calls or invents broader admission")
        for side, products, terminal in zip(self.complete_call_censuses, self.original_pair.segment_assessments,
                self.original_pair.actual_terminal_clocks, strict=True):
            if tuple(row.summary for row in side) != tuple(row.summary for row in products):
                raise ValueError("forecast clock substitutes an independently assessed original returned call")
            for row, product in zip(side, products, strict=True):
                if type(row) is not ForecastClockCall:
                    raise ValueError("forecast clock changes an original call outcome type")
                row.__post_init__()
                if (row.returned_clock is not None and product.full_state_components
                        and row.returned_clock.state_rows * product.retained_native_knots != product.full_state_components):
                    raise ValueError("forecast clock thins its independently consumed native state row denominator")
            if side and side[-1].returned_clock is not None and side[-1].returned_clock.exact_end != terminal:
                raise ValueError("forecast clock substitutes the original actual terminal clock")
        if type(self.boundaries) is not tuple or any(type(row) is not clock.ClockBoundary for row in self.boundaries):
            raise ValueError("forecast clock substitutes the complete original one-sided boundaries")
        keys = tuple((row.side, row.next_segment) for row in self.boundaries)
        expected = tuple((side, i) for side, rows in zip(("LEFT", "RIGHT"), self.complete_call_censuses, strict=True)
            for i in range(2, len(rows) + 1))
        if len(set(keys)) != len(keys) or tuple(key for key in expected if key in keys) != keys:
            raise ValueError("forecast clock adds, duplicates or reorders actual restart boundaries")
        for boundary in self.boundaries:
            boundary.__post_init__()
            previous, following = self.complete_call_censuses[0 if boundary.side == "LEFT" else 1][boundary.next_segment - 2:boundary.next_segment]
            a, b = previous.returned_clock, following.returned_clock
            if (a is None or b is None or boundary.exact_start != a.exact_end or boundary.exact_end != b.exact_start
                    or boundary.state_continuity.checked_components != a.state_rows
                    or boundary.returned_derivative_continuity.checked_components != a.state_rows or a.state_rows != b.state_rows):
                raise ValueError("forecast clock boundary thins original clocks or full component denominators")
        if type(self.disposition) is not A or (self.disposition, self.reason_codes) != _reasons(
                self.original_pair, self.complete_call_censuses, self.boundaries):
            raise ValueError("forecast clock bypasses original negative, uncertain, event or suffix outcomes")


def assess_clock(policy, selected, original_pair, left, right, left_port, right_port, *, temporary_file):
    """Reconsume complete lossless originals; retain unavailable calls and gaps."""
    require_sources(policy)
    if type(original_pair) is not state.ForecastStateStream or original_pair.scientific_control != policy.scientific_control:
        raise ValueError("forecast clock substitutes its original fixed-budget full-state product")
    original_pair.__post_init__()
    for observed, expected, assigned in zip((left, right), (original_pair.left_evidence, original_pair.right_evidence),
            original_pair.actual_assignment_evidence, strict=True):
        orchestration._require_observation(policy.scientific_control, selected, observed)
        if step.identity(observed.evidence, "evidence_id") != expected or step.identity(observed.assignment, "evidence_id") != assigned:
            raise ValueError("forecast clock substitutes original evidence or actual solver assignment identity")
        if dict(observed.evidence.trace.config.source.source_members).get("solvers/base_solver.py") != policy.selected_step_source_sha256:
            raise ValueError("forecast clock substitutes the actual selected step source")
    assignments = tuple(row.assignment.assignment for row in (left, right) if row.assignment.assignment is not None)
    calls, boundaries = [], []
    with consumer.numerical_consumer_scope(temporary_file=temporary_file, assignments=assignments):
        for side_index, (side, observed, port) in enumerate(zip(("LEFT", "RIGHT"), (left, right), (left_port, right_port), strict=True)):
            cursor = paired._Cursor(paired.FullStateStreamOperand(observed.evidence, port), side, [])
            side_calls, previous = [], None
            while cursor.frame is not None:
                frame = cursor.frame
                returned = None if cursor.start is None else clock.ClockCall(science.identity(cursor.operand.summary, "summary_id"),
                    science.identity(frame.full_state, "segment_id"), frame.request.identity, clock._fraction(cursor.start), clock._fraction(cursor.end),
                    cursor.evidence.layout.differential_count + cursor.evidence.layout.algebraic_count)
                complete = returned is not None and all(value is not None and len(value.binary64_hex) == returned.state_rows
                    for value in (frame.requested_initial, frame.actual_initial, frame.actual_terminal,
                        frame.initial_derivative, frame.terminal_derivative))
                side_calls.append(ForecastClockCall(science.identity(cursor.operand.summary, "summary_id"), frame.request.identity,
                    None if frame.full_state is None else science.identity(frame.full_state, "segment_id"), returned,
                    () if returned is not None and complete else (MISSING,)))
                inputs = json.loads(frame.request.primitive_json)["inputs"]
                model = None if frame.full_state is None else frame.full_state.returned_model_expression_sha256
                if previous is not None and returned is not None and complete:
                    terminal, derivative, prior_end, prior_inputs, prior_model = previous
                    boundaries.append(clock.ClockBoundary(side, cursor.index, clock._fraction(prior_end), clock._fraction(cursor.start),
                        *(science.identity(value, "observation_id") for value in (frame.requested_initial, terminal, frame.actual_initial,
                            derivative, frame.initial_derivative)), frame.requested_initial.binary64_hex == terminal.binary64_hex,
                        prior_inputs == inputs and prior_model == model,
                        clock._metric(terminal.binary64_hex, frame.actual_initial.binary64_hex, returned.state_rows, policy),
                        clock._metric(derivative.binary64_hex, frame.initial_derivative.binary64_hex, returned.state_rows, policy)))
                previous = (frame.actual_terminal, frame.terminal_derivative, cursor.end, inputs, model) if returned is not None and complete else None
                cursor.advance()
            if (tuple(cursor.assessments) != original_pair.segment_assessments[side_index]
                    or cursor.preparation != original_pair.preparations[side_index]
                    or observed.summary != qualification.summarize_trace(cursor.trace, cursor.preparation, tuple(cursor.assessments))):
                raise ValueError("forecast clock disagrees with independently reconsumed preparation/call/summary products")
            calls.append(tuple(side_calls))
    disposition, reasons = _reasons(original_pair, tuple(calls), tuple(boundaries))
    return ForecastClockAssessment("assessment.forecast-clock." + original_pair.assessment_id, policy, original_pair,
        tuple(calls), tuple(boundaries), disposition, reasons)
