# SPDX-License-Identifier: MPL-2.0
"""One-sided source tier/current assessment and separate terminal endpoints.

All original calls and tier returns survive. Differential continuation is a
falsifier; algebraic/current and derivative jumps are measured separately.
Native-knot quadrature is a numerical check, never a continuous-time enclosure.
An endpoint comparison supplies no absent post-terminal full-state trajectory.
"""

from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
from typing import ClassVar

from empirical_lawhood.adapters.methods.battery_thermal_inquiry.contracts import INTEGRAL_TOLERANCE, TIER_EVENT, TIER_TEMPERATURE
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id

from . import forecast_state_control as state
from . import forecast_state_orchestration as orchestration
from . import forecast_step_control as step
from . import lossless_segment_consumer as consumer
from . import preparation_contracts as preparation
from . import representable_clock as clock
from . import segmented_contracts as contracts
from . import segmented_fidelity_stream as paired
from . import segmented_qualification as qualification
from . import segmented_science as science

D = Decimal
SCOPE = "COMPLETE_NATIVE_KNOT_AND_ONE_SIDED_SOURCE_TIER_CONTROL;NO_CONTINUOUS_TIME_ENDPOINT_OR_MODEL_ADMISSION"
ENDPOINT_SCOPE = "ACTUAL_TERMINAL_ENDPOINT_COMPARISON_ONLY;NO_ABSENT_GLOBAL_SUFFIX_SUPPLIED"


def _fraction(value):
    return value.numerator, value.denominator


def _bits(value):
    return Fraction.from_float(float.fromhex(value))


def _optional_fraction(value):
    if value is not None:
        paired._require_fraction(value)


def _status(adverse, missing):
    return A.FALSIFIED if adverse else A.UNEVALUABLE if missing else A.SATISFIED, tuple(sorted(adverse | missing))


def _weights(control):
    budget = control.native_policy.comparison_budget
    return budget.rtol, budget.atol


def _metric(control, left, right, rows):
    class Budget:
        comparison_rtol, comparison_atol = _weights(control)
    return clock._metric(left, right, rows, Budget())


def _physical(block, bits):
    return Fraction(block.reference) + Fraction(block.scale) * _bits(bits)


def _source_inputs(config, regime):
    # Independent literal source contract; do not invoke native controller code.
    return {"Inquiry active charging magnitude [A]": {"binary64": float(D("1.455") if regime == "LOW" else D("3.395")).hex()},
        "Inquiry tier threshold [K]": {"binary64": float(TIER_TEMPERATURE + config.localization_epsilon_k / (D(1) if regime == "LOW" else D(2))).hex()},
        "Inquiry tier direction": {"binary64": float(-1 if regime == "LOW" else 1).hex()}}


@dataclass(frozen=True, slots=True)
class ForecastCurrentCall(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/forecast-current-call"
    summary: ObjectIdentity
    request: ObjectIdentity
    original_integrity: science.SegmentAssessment
    exact_start: tuple[int, int] | None
    exact_end: tuple[int, int] | None
    native_knots: int
    integrated_charge_ah: tuple[int, int] | None
    capacity_charge_ah: tuple[int, int] | None
    source_inputs_match: bool
    native_temperature_regime_match: bool | None

    def __post_init__(self):
        if (type(self.summary) is not ObjectIdentity or self.summary.object_schema != contracts.SegmentSummary.SCHEMA
                or type(self.request) is not ObjectIdentity or self.request.object_schema != "empirical-lawhood/battery-segmented/native-request"
                or type(self.original_integrity) is not science.SegmentAssessment or self.original_integrity.summary != self.summary
                or type(self.native_knots) is not int or self.native_knots < 0 or type(self.source_inputs_match) is not bool
                or self.native_temperature_regime_match is not None and type(self.native_temperature_regime_match) is not bool):
            raise ValueError("event/current call loses its complete original integrity or source assignment")
        self.original_integrity.__post_init__()
        for value in (self.exact_start, self.exact_end, self.integrated_charge_ah, self.capacity_charge_ah):
            _optional_fraction(value)
        if ((self.exact_start is None) != (self.exact_end is None)
                or (self.integrated_charge_ah is None) != (self.capacity_charge_ah is None)
                or self.integrated_charge_ah is not None and (self.native_knots < 1 or self.exact_start is None)
                or self.exact_start is not None and Fraction(*self.exact_start) > Fraction(*self.exact_end)
                or self.native_knots != self.original_integrity.retained_native_knots):
            raise ValueError("event/current call changes its actual complete native knot denominator")


@dataclass(frozen=True, slots=True)
class ForecastTierAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/forecast-tier-assessment"
    preceding_segment: int
    original_transition: contracts.SegmentTransition | None
    root_source_and_direction_match: bool | None
    complete_requested_state_unchanged: bool | None
    differential_continuity: clock.BoundaryMetric | None
    algebraic_jump: clock.BoundaryMetric | None
    returned_derivative_jump: clock.BoundaryMetric | None
    disposition: A
    reason_codes: tuple[str, ...]

    def __post_init__(self):
        if (type(self.preceding_segment) is not int or self.preceding_segment < 1
                or self.original_transition is not None and (type(self.original_transition) is not contracts.SegmentTransition
                    or self.original_transition.preceding_segment != self.preceding_segment)
                or any(value is not None and type(value) is not bool for value in
                    (self.root_source_and_direction_match, self.complete_requested_state_unchanged))
                or any(value is not None and type(value) is not clock.BoundaryMetric for value in
                    (self.differential_continuity, self.algebraic_jump, self.returned_derivative_jump))):
            raise ValueError("one-sided tier assessment changes actual event or complete component operands")
        for value in (self.differential_continuity, self.algebraic_jump, self.returned_derivative_jump):
            if value is not None:
                value.__post_init__()
        if self.original_transition is not None:
            self.original_transition.__post_init__()
        adverse, missing = set(), set()
        if any(value is None for value in (self.original_transition, self.root_source_and_direction_match,
                self.complete_requested_state_unchanged, self.differential_continuity, self.algebraic_jump, self.returned_derivative_jump)):
            missing.add("complete-one-sided-tier-restart-unavailable")
        if self.root_source_and_direction_match is False:
            adverse.add("actual-source-tier-threshold-direction-or-regime-disagrees")
        if self.complete_requested_state_unchanged is False:
            adverse.add("tier-request-substitutes-complete-previous-terminal")
        if self.differential_continuity is not None and self.differential_continuity.failed_components:
            adverse.add("tier-differential-state-continuation-falsified")
        # Algebraic/current and derivative jump metrics stay in the record;
        # their presence does not make a discontinuity a continuity failure.
        if type(self.disposition) is not A or (self.disposition, self.reason_codes) != _status(adverse, missing):
            raise ValueError("tier assessment bypasses one-sided negatives or missing native operands")


def _event_reasons(calls, events, declared_tier_returns):
    adverse, missing = set(), set()
    if any(row.original_integrity.disposition is A.FALSIFIED for row in calls):
        adverse.add("independent-original-segment-integrity-falsified")
    if not calls or any(row.original_integrity.disposition is A.UNEVALUABLE for row in calls):
        missing.add("complete-original-segment-integrity-unresolved")
    if any(not row.source_inputs_match for row in calls):
        adverse.add("actual-source-input-assignment-disagrees")
    if any(row.native_temperature_regime_match is False for row in calls):
        adverse.add("actual-native-temperature-regime-or-unrecorded-tier-disagrees")
    if any(row.native_temperature_regime_match is None for row in calls):
        missing.add("complete-native-temperature-regime-operands-unavailable")
    if any(row.integrated_charge_ah is None for row in calls) or not calls:
        missing.add("complete-native-current-capacity-operands-unavailable")
    else:
        integral = sum((Fraction(*row.integrated_charge_ah) for row in calls), Fraction(0))
        capacity = sum((Fraction(*row.capacity_charge_ah) for row in calls), Fraction(0))
        if abs(integral - capacity) > Fraction(INTEGRAL_TOLERANCE):
            missing.add("independent-native-knot-current-capacity-disagreement")
    if tuple(row.preceding_segment for row in events) != declared_tier_returns:
        raise ValueError("event assessment omits, duplicates or reorders actual tier returns")
    if any(row.disposition is A.FALSIFIED for row in events):
        adverse.add("independent-one-sided-tier-falsified")
    if any(row.disposition is A.UNEVALUABLE for row in events):
        missing.add("complete-one-sided-tier-assessment-unresolved")
    return _status(adverse, missing)


@dataclass(frozen=True, slots=True)
class ForecastEventAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/forecast-event-assessment"
    assessment_id: str
    scientific_control: state.ForecastStateControl
    evidence: ObjectIdentity
    assignment: ObjectIdentity
    original_trace: contracts.SegmentedTrace
    original_summary: qualification.SegmentedTraceSummary
    actual_layout: preparation.ProcessedInitialStateLayout | None
    complete_calls: tuple[ForecastCurrentCall, ...]
    declared_tier_returns: tuple[int, ...]
    complete_tier_assessments: tuple[ForecastTierAssessment, ...]
    boundary_algorithm_source_sha256: str
    disposition: A
    reason_codes: tuple[str, ...]
    scope: str = SCOPE
    quadrature_scope: str = "EXACT_RATIONAL_TRAPEZOIDS_ON_ALL_RETURNED_NATIVE_CLOCKS;REAL_RESTART_GAPS_UNFILLED;NO_CONTINUOUS_ERROR_BOUND"
    model_admission: bool = False

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        if (type(self.scientific_control) is not state.ForecastStateControl or type(self.original_trace) is not contracts.SegmentedTrace
                or type(self.original_summary) is not qualification.SegmentedTraceSummary
                or type(self.evidence) is not ObjectIdentity or self.evidence.object_schema != "empirical-lawhood/battery-segmented/native-evidence"
                or type(self.assignment) is not ObjectIdentity or self.assignment.object_schema != step.ForecastStepEvidence.SCHEMA
                or self.actual_layout is not None and type(self.actual_layout) is not preparation.ProcessedInitialStateLayout
                or type(self.complete_calls) is not tuple or any(type(row) is not ForecastCurrentCall for row in self.complete_calls)
                or type(self.complete_tier_assessments) is not tuple or any(type(row) is not ForecastTierAssessment for row in self.complete_tier_assessments)
                or self.scope != SCOPE or self.model_admission is not False
                or self.quadrature_scope != "EXACT_RATIONAL_TRAPEZOIDS_ON_ALL_RETURNED_NATIVE_CLOCKS;REAL_RESTART_GAPS_UNFILLED;NO_CONTINUOUS_ERROR_BOUND"):
            raise ValueError("event/current assessment changes source20 operands or invents broader admission")
        self.scientific_control.__post_init__()
        self.original_trace.__post_init__()
        self.original_summary.__post_init__()
        if self.actual_layout is not None:
            self.actual_layout.__post_init__()
        from empirical_lawhood.kernel.serialization import validate_sha256
        validate_sha256(self.boundary_algorithm_source_sha256)
        if (tuple(row.summary for row in self.complete_calls) != tuple(step.identity(row, "summary_id") for row in self.original_trace.segments)
                or tuple(row.request for row in self.complete_calls) != tuple(row.request for row in self.original_trace.segments)
                or self.declared_tier_returns != tuple(row.segment_index for row in self.original_trace.segments if TIER_EVENT in row.termination)):
            raise ValueError("event/current assessment changes the complete original call or tier denominator")
        for row in (*self.complete_calls, *self.complete_tier_assessments):
            row.__post_init__()
        if (self.original_summary.trace != step.identity(self.original_trace, "trace_id")
                or self.original_summary.configuration != self.original_trace.config
                or tuple(row.original_integrity for row in self.complete_calls) != self.original_summary.segment_assessments
                or self.original_summary != qualification.summarize_trace(
                    self.original_trace, self.original_summary.preparation, self.original_summary.segment_assessments)):
            raise ValueError("event/current assessment substitutes its independently recomputed original preparation or receiver summary")
        for row in self.complete_calls:
            if (row.original_integrity.full_state_components and (self.actual_layout is None
                    or row.original_integrity.full_state_components != row.native_knots * (
                        self.actual_layout.differential_count + self.actual_layout.algebraic_count))):
                raise ValueError("event/current assessment thins independently consumed full native layout rows")
        if tuple(row.original_transition for row in self.complete_tier_assessments if row.original_transition is not None) != self.original_trace.transitions:
            raise ValueError("event/current assessment substitutes declared original transition records")
        for row in self.complete_tier_assessments:
            if row.differential_continuity is not None and row.algebraic_jump is not None and row.returned_derivative_jump is not None:
                if row.differential_continuity.checked_components + row.algebraic_jump.checked_components != row.returned_derivative_jump.checked_components:
                    raise ValueError("tier continuity/jump assessment thins its complete component denominator")
                if (self.actual_layout is None or row.differential_continuity.checked_components != self.actual_layout.differential_count
                        or row.algebraic_jump.checked_components != self.actual_layout.algebraic_count):
                    raise ValueError("tier continuity/jump assessment substitutes actual differential/algebraic roles")
        if type(self.disposition) is not A or (self.disposition, self.reason_codes) != _event_reasons(
                self.complete_calls, self.complete_tier_assessments, self.declared_tier_returns):
            raise ValueError("event/current assessment bypasses complete independent negatives or uncertainty")


def _native_integral(frame, layout):
    roles = {row.role: row for row in layout.blocks}
    current, capacity = roles.get("current"), roles.get("discharge-capacity")
    if any(row is None or row.stop != row.start + 1 for row in (current, capacity)) or frame.full_state is None:
        return None, None
    integral, first_capacity, last_capacity, prior_block_end = Fraction(0), None, None, None
    for block in frame.full_state.blocks:
        width = len(block.clock_binary64)
        if not width or prior_block_end is not None and _bits(block.clock_binary64[0]) != prior_block_end:
            # There is no authentic current population between separated
            # returned blocks; do not invent its quadrature or charge change.
            return None, None
        previous = None
        for column, bit in enumerate(block.clock_binary64):
            t = _bits(bit)
            i = _physical(current, block.state_binary64[current.start * width + column])
            q = _physical(capacity, block.state_binary64[capacity.start * width + column])
            if first_capacity is None:
                first_capacity = q
            last_capacity = q
            if previous is not None:
                before, old_i = previous
                integral -= (old_i + i) * (t - before) / 7200
            previous = t, i
        prior_block_end = t
    return (None, None) if first_capacity is None else (_fraction(integral), _fraction(first_capacity - last_capacity))


def _temperature_regime(frame, layout, config, regime):
    row = next((value for value in layout.blocks if value.role == "temperature"), None)
    if row is None or row.stop != row.start + 1 or frame.full_state is None:
        return None
    threshold = Fraction(TIER_TEMPERATURE + config.localization_epsilon_k / (D(1) if regime == "LOW" else D(2)))
    allowance = Fraction(config.localization_epsilon_k) / 1000000
    for block in frame.full_state.blocks:
        width = len(block.clock_binary64)
        for column in range(width):
            temperature = _physical(row, block.state_binary64[row.start * width + column])
            if regime == "LOW" and temperature > threshold + allowance or regime == "HIGH" and temperature < threshold - allowance:
                return False
    return True


def _root_match(config, summary, frame, layout):
    block = next((row for row in layout.blocks if row.role == "temperature"), None)
    if block is None or block.stop != block.start + 1 or frame.full_state is None or frame.actual_terminal is None:
        return None
    last = frame.full_state.blocks[-1]
    width = len(last.clock_binary64)
    if width < 2:
        return None
    before = _physical(block, last.state_binary64[block.start * width + width - 2])
    terminal = _physical(block, last.state_binary64[block.start * width + width - 1])
    threshold = Fraction(TIER_TEMPERATURE + config.localization_epsilon_k / (D(1) if summary.regime == "LOW" else D(2)))
    tolerance = Fraction(config.localization_epsilon_k) / 1000000
    direction = before <= threshold + tolerance and terminal >= before if summary.regime == "LOW" else before >= threshold - tolerance and terminal <= before
    return abs(terminal - threshold) <= tolerance and direction


def assess_events(control, selected, observation, port, *, temporary_file):
    """Consume one authentic complete lossless stream, holding one active frame."""
    state.require_algorithm_sources(control)
    orchestration._require_observation(control, selected, observation)
    observed = observation.evidence
    assignments = () if observation.assignment.assignment is None else (observation.assignment.assignment,)
    calls, events, pending = [], [], None
    transitions = {row.preceding_segment: row for row in observed.trace.transitions}
    with consumer.numerical_consumer_scope(temporary_file=temporary_file, assignments=assignments):
        cursor = paired._Cursor(paired.FullStateStreamOperand(observed, port), "LEFT", [])
        while cursor.frame is not None:
            frame, summary = cursor.frame, cursor.operand.summary
            source_match = json.loads(frame.request.primitive_json).get("inputs") == _source_inputs(cursor.trace.config, summary.regime)
            integral, capacity = (None, None) if cursor.evidence.layout is None else _native_integral(frame, cursor.evidence.layout)
            regime_match = None if cursor.evidence.layout is None else _temperature_regime(
                frame, cursor.evidence.layout, cursor.trace.config, summary.regime)
            calls.append(ForecastCurrentCall(step.identity(summary, "summary_id"), frame.request.identity, cursor.assessments[-1],
                None if cursor.start is None else _fraction(cursor.start), None if cursor.end is None else _fraction(cursor.end),
                cursor.assessments[-1].retained_native_knots, integral, capacity, source_match, regime_match))
            if pending is not None:
                ordinal, terminal, derivative, root_match = pending
                transition = transitions.get(ordinal)
                vectors = terminal, derivative, frame.requested_initial, frame.actual_initial, frame.initial_derivative
                complete = cursor.evidence.layout is not None and all(row is not None and len(row.binary64_hex) == (
                    cursor.evidence.layout.differential_count + cursor.evidence.layout.algebraic_count) for row in vectors)
                differential = algebraic = returned_derivative = requested = None
                if complete:
                    count = cursor.evidence.layout.differential_count
                    rows = count + cursor.evidence.layout.algebraic_count
                    requested = terminal.binary64_hex == frame.requested_initial.binary64_hex
                    differential = _metric(control, terminal.binary64_hex[:count], frame.actual_initial.binary64_hex[:count], count)
                    algebraic = _metric(control, terminal.binary64_hex[count:], frame.actual_initial.binary64_hex[count:], rows - count)
                    returned_derivative = _metric(control, derivative.binary64_hex, frame.initial_derivative.binary64_hex, rows)
                root_source = root_match
                if root_source is not None:
                    root_source = bool(root_source and source_match and transition is not None
                        and summary.regime == transition.to_regime and transition.localization_epsilon_k == cursor.trace.config.localization_epsilon_k
                        and transition.root_threshold_k == TIER_TEMPERATURE + cursor.trace.config.localization_epsilon_k / (
                            D(1) if transition.from_regime == "LOW" else D(2)))
                adverse, missing = set(), set()
                if any(value is None for value in (transition, root_source, requested, differential, algebraic, returned_derivative)):
                    missing.add("complete-one-sided-tier-restart-unavailable")
                if root_source is False:
                    adverse.add("actual-source-tier-threshold-direction-or-regime-disagrees")
                if requested is False:
                    adverse.add("tier-request-substitutes-complete-previous-terminal")
                if differential is not None and differential.failed_components:
                    adverse.add("tier-differential-state-continuation-falsified")
                disposition, reasons = _status(adverse, missing)
                events.append(ForecastTierAssessment(ordinal, transition, root_source, requested,
                    differential, algebraic, returned_derivative, disposition, reasons))
                pending = None
            if TIER_EVENT in summary.termination:
                root = None if cursor.evidence.layout is None else _root_match(cursor.trace.config, summary, frame, cursor.evidence.layout)
                pending = summary.segment_index, frame.actual_terminal, frame.terminal_derivative, root
            cursor.advance()
        if (tuple(cursor.assessments) != observation.summary.segment_assessments
                or observation.summary != qualification.summarize_trace(cursor.trace, cursor.preparation, tuple(cursor.assessments))):
            raise ValueError("event/current assessment disagrees with independently reconsumed complete original summary")
    if pending is not None:
        ordinal = pending[0]
        events.append(ForecastTierAssessment(ordinal, transitions.get(ordinal), None, None, None, None, None,
            A.UNEVALUABLE, ("complete-one-sided-tier-restart-unavailable",)))
    declared = tuple(row.segment_index for row in observed.trace.segments if TIER_EVENT in row.termination)
    disposition, reasons = _event_reasons(tuple(calls), tuple(events), declared)
    return ForecastEventAssessment("assessment.events." + observed.evidence_id, control,
        step.identity(observed, "evidence_id"), step.identity(observation.assignment, "evidence_id"), observed.trace, observation.summary, observed.layout,
        tuple(calls), declared, tuple(events), sha256(Path(clock.__file__).read_bytes()).hexdigest(), disposition, reasons)


@dataclass(frozen=True, slots=True)
class ForecastTerminalAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/forecast-terminal-assessment"
    assessment_id: str
    scientific_control: state.ForecastStateControl
    original_pair: state.ForecastStateStream
    events: tuple[ForecastEventAssessment, ForecastEventAssessment]
    terminal_clock_difference_s: tuple[int, int] | None
    voltage_difference_v: Decimal | None
    temperature_difference_k: Decimal | None
    unpaired_actual_suffix: tuple[tuple[int, int], tuple[int, int]] | None
    disposition: A
    reason_codes: tuple[str, ...]
    scope: str = ENDPOINT_SCOPE
    whole_global_state_coverage: A = A.UNEVALUABLE
    model_admission: bool = False

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        if (type(self.scientific_control) is not state.ForecastStateControl or type(self.original_pair) is not state.ForecastStateStream
                or self.original_pair.scientific_control != self.scientific_control or type(self.events) is not tuple
                or len(self.events) != 2 or any(type(row) is not ForecastEventAssessment for row in self.events)
                or tuple(row.evidence for row in self.events) != (self.original_pair.left_evidence, self.original_pair.right_evidence)
                or any(row.scientific_control != self.scientific_control for row in self.events)
                or self.scope != ENDPOINT_SCOPE or self.whole_global_state_coverage is not A.UNEVALUABLE or self.model_admission is not False):
            raise ValueError("terminal endpoint product substitutes original evidence or supplies an absent full-state suffix")
        self.original_pair.__post_init__()
        for event in self.events:
            event.__post_init__()
        expected = _terminal_operands(self.events)
        if (self.terminal_clock_difference_s, self.voltage_difference_v, self.temperature_difference_k,
                self.unpaired_actual_suffix, self.disposition, self.reason_codes) != expected:
            raise ValueError("terminal endpoint assessment bypasses original outcomes or unchanged1s/1mV/0.01K gates")


def _terminal_operands(events):
    a, b = (row.original_trace for row in events)
    clocks = tuple(None if not row.complete_calls or row.complete_calls[-1].exact_end is None
        else Fraction(*row.complete_calls[-1].exact_end) for row in events)
    difference = None if any(value is None for value in clocks) else abs(clocks[0] - clocks[1])
    suffix = None if difference in (None, 0) else tuple(_fraction(value) for value in sorted(clocks))
    voltage = None if not a.voltage_v or not b.voltage_v else abs(a.voltage_v[-1] - b.voltage_v[-1])
    temperature = None if not a.mean_temperature_k or not b.mean_temperature_k else abs(a.mean_temperature_k[-1] - b.mean_temperature_k[-1])
    adverse, missing = set(), set()
    if any(row.disposition is A.FALSIFIED for row in events):
        adverse.add("independent-source-tier-current-control-falsified")
    if any(row.disposition is A.UNEVALUABLE for row in events):
        missing.add("independent-source-tier-current-control-unresolved")
    if any(row.original_summary.receiver_check.disposition is A.FALSIFIED for row in events):
        adverse.add("independent-original-terminal-receiver-integrity-falsified")
    if any(row.original_summary.receiver_check.disposition is A.UNEVALUABLE for row in events):
        missing.add("independent-original-terminal-receiver-integrity-unresolved")
    if any(row.disposition == "TECHNICAL_FAILURE" for row in (a, b)):
        missing.add("actual-terminal-technical-failure")
    elif a.disposition != b.disposition or a.termination != b.termination:
        adverse.add("actual-terminal-outcome-or-event-disagrees")
    if difference is None or voltage is None or temperature is None:
        missing.add("complete-actual-terminal-receivers-unavailable")
    else:
        if difference > 1:
            missing.add("reference-terminal-clock-precision-unresolved")
        if voltage > D(".001"):
            missing.add("reference-voltage-precision-unresolved")
        if temperature > D(".01"):
            missing.add("reference-temperature-precision-unresolved")
    disposition, reasons = _status(adverse, missing)
    return None if difference is None else _fraction(difference), voltage, temperature, suffix, disposition, reasons


def assess_terminals(control, original_pair, left_event, right_event):
    """Compare actual endpoints separately; never extrapolate the shorter trace."""
    state.require_algorithm_sources(control)
    events = left_event, right_event
    values = _terminal_operands(events)
    return ForecastTerminalAssessment("assessment.terminals." + original_pair.assessment_id, control,
        original_pair, events, *values)
