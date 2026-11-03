# SPDX-License-Identifier: MPL-2.0
"""Explicit returned binary64 clock-domain coverage, retaining real open gaps.

This separate PURE control never edits the original paired assessment. It checks
all original calls, full one-sided state/derivative continuity and source-nextafter
adjacency. Continuous-time uncertainty, events and later admission remain separate.
"""
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
import json
import math
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_sha256, validate_stable_id
from . import segmented_fidelity as local
from . import segmented_fidelity_stream as paired
from . import segmented_science as science

D = Decimal
SCOPE = "RETURNED_BINARY64_CLOCK_DOMAIN_ONLY;ORIGINAL_REAL_OPEN_GAPS_RETAINED;NO_WHOLE_TIME_OR_PHYSICAL_CERTIFICATE;NOT_A_LATER_USE_SUPPLIER"
GAP_CODES = {"original-open-global-clock-gap-source-nextafter-not-interpolated", "unpaired-actual-global-clock-span"}


def _fraction(value):
    return value.numerator, value.denominator


def _binary64(value):
    result = float(value)
    if not math.isfinite(result) or Fraction.from_float(result) != value:
        raise ValueError("clock coverage changes an exact finite binary64 operand")
    return result


def _adjacent(start, end):
    a, b = _binary64(start), _binary64(end)
    return math.nextafter(a, math.inf) == b


@dataclass(frozen=True, slots=True)
class RepresentableClockPolicy(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/representable-clock-policy"
    policy_id: str
    original_control: ObjectIdentity
    selected_step_source_sha256: str
    comparison_rtol: Decimal = D("1e-7")
    comparison_atol: Decimal = D("1e-8")
    clock_domain: str = "FINITE_BINARY64_GLOBAL_CLOCK;NO_INTERIOR_OPERAND_BETWEEN_ADJACENT_VALUES"
    scope: str = SCOPE

    def __post_init__(self):
        validate_stable_id(self.policy_id)
        validate_sha256(self.selected_step_source_sha256)
        if (type(self.original_control) is not ObjectIdentity or self.original_control.object_schema != local.FullStateControlProtocol.SCHEMA
                or (self.comparison_rtol, self.comparison_atol) != (D("1e-7"), D("1e-8"))
                or self.clock_domain != "FINITE_BINARY64_GLOBAL_CLOCK;NO_INTERIOR_OPERAND_BETWEEN_ADJACENT_VALUES" or self.scope != SCOPE):
            raise ValueError("representable clock policy loses original control, unchanged gates or explicit scope")


@dataclass(frozen=True, slots=True)
class BoundaryMetric(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/full-boundary-metric"
    checked_components: int
    failed_components: tuple[int, ...]
    maximum_row: int
    maximum_exact_normalized_difference: tuple[int, int]

    def __post_init__(self):
        if (type(self.checked_components) is not int or self.checked_components < 1
                or type(self.failed_components) is not tuple or tuple(sorted(set(self.failed_components))) != self.failed_components
                or any(type(row) is not int or not 0 <= row < self.checked_components for row in self.failed_components)
                or type(self.maximum_row) is not int or not 0 <= self.maximum_row < self.checked_components):
            raise ValueError("boundary metric thins, duplicates or relabels complete native rows")
        paired._require_fraction(self.maximum_exact_normalized_difference)
        maximum = Fraction(*self.maximum_exact_normalized_difference)
        if bool(self.failed_components) != (maximum > 1) or self.failed_components and self.maximum_row not in self.failed_components:
            raise ValueError("boundary metric bypasses the unchanged complete-row precision gate")


def _metric(left, right, rows, policy):
    if len(left) != rows or len(right) != rows:
        raise ValueError("clock coverage omits actual full state or returned derivative rows")
    ratios = []
    for a, b in zip(left, right, strict=True):
        a, b = Fraction.from_float(float.fromhex(a)), Fraction.from_float(float.fromhex(b))
        ratios.append(abs(a - b) / (Fraction(policy.comparison_atol) + Fraction(policy.comparison_rtol) * max(abs(a), abs(b))))
    maximum = max(range(rows), key=ratios.__getitem__)
    return BoundaryMetric(rows, tuple(i for i, value in enumerate(ratios) if value > 1), maximum, _fraction(ratios[maximum]))


@dataclass(frozen=True, slots=True)
class ClockCall(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/representable-clock-call"
    summary: ObjectIdentity
    full_state: ObjectIdentity
    request: ObjectIdentity
    exact_start: tuple[int, int]
    exact_end: tuple[int, int]
    state_rows: int

    def __post_init__(self):
        paired._require_fraction(self.exact_start)
        paired._require_fraction(self.exact_end)
        _binary64(Fraction(*self.exact_start))
        _binary64(Fraction(*self.exact_end))
        if (Fraction(*self.exact_start) > Fraction(*self.exact_end) or type(self.state_rows) is not int or self.state_rows < 1
                or tuple(row.object_schema for row in (self.summary, self.full_state, self.request)) != (
                    "empirical-lawhood/battery-segmented/segment-summary", "empirical-lawhood/battery-segmented/full-state-segment", "empirical-lawhood/battery-segmented/native-request")):
            raise ValueError("clock call substitutes original full-state/call operands")


@dataclass(frozen=True, slots=True)
class ClockBoundary(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/representable-clock-boundary"
    side: str
    next_segment: int
    exact_start: tuple[int, int]
    exact_end: tuple[int, int]
    original_requested_initial: ObjectIdentity
    original_previous_terminal: ObjectIdentity
    original_actual_initial: ObjectIdentity
    original_previous_derivative: ObjectIdentity
    original_initial_derivative: ObjectIdentity
    requested_full_state_unchanged: bool
    actual_model_and_scalar_regime_unchanged: bool
    state_continuity: BoundaryMetric
    returned_derivative_continuity: BoundaryMetric

    def __post_init__(self):
        paired._require_fraction(self.exact_start)
        paired._require_fraction(self.exact_end)
        if (self.side not in {"LEFT", "RIGHT"} or type(self.next_segment) is not int or self.next_segment < 2
                or any(type(row) is not ObjectIdentity or row.object_schema != "empirical-lawhood/battery-preparation/state-observation" for row in (
                    self.original_requested_initial, self.original_previous_terminal, self.original_actual_initial,
                    self.original_previous_derivative, self.original_initial_derivative))
                or any(type(row) is not bool for row in (self.requested_full_state_unchanged, self.actual_model_and_scalar_regime_unchanged))
                or type(self.state_continuity) is not BoundaryMetric or type(self.returned_derivative_continuity) is not BoundaryMetric):
            raise ValueError("clock boundary loses original one-sided full state/derivative operands")
        self.state_continuity.__post_init__()
        self.returned_derivative_continuity.__post_init__()


def _reasons(original, calls, boundaries):
    adverse, missing = set(), set()
    products = (*original.preparations, *original.segment_assessments[0], *original.segment_assessments[1], *original.intervals)
    if any(row.disposition is A.FALSIFIED for row in products):
        adverse.add("original-covered-preparation-segment-or-interval-falsified")
    if not original.intervals or any(row.disposition is A.UNEVALUABLE for row in products):
        missing.add("original-covered-preparation-segment-or-interval-unresolved")
    if any(original.declared_transition_counts):
        missing.add("independent-regime-change-event-control-unassessed")
    if original.actual_terminal_clocks[0] is None or original.actual_terminal_clocks[0] != original.actual_terminal_clocks[1]:
        missing.add("actual-terminal-suffix-or-clock-alignment-unresolved")
    if any(not side or Fraction(*side[0].exact_start) != 0 for side in calls):
        missing.add("original-global-clock-prefix-uncovered")
    for boundary in boundaries:
        if not _adjacent(Fraction(*boundary.exact_start), Fraction(*boundary.exact_end)):
            missing.add("actual-restart-gap-has-representable-interior-operand")
        if not boundary.requested_full_state_unchanged:
            adverse.add("actual-request-substitutes-previous-complete-terminal-state")
        if not boundary.actual_model_and_scalar_regime_unchanged:
            missing.add("actual-model-or-regime-change-unassessed")
        if boundary.state_continuity.failed_components or boundary.returned_derivative_continuity.failed_components:
            adverse.add("full-one-sided-state-or-returned-derivative-continuity-falsified")
    domains = {(row.exact_start, row.exact_end) for row in boundaries}
    for issue in original.coverage_issues:
        if issue.code not in GAP_CODES or (issue.exact_start, issue.exact_end) not in domains:
            missing.add("original-uncovered-span-has-no-exact-source-adjacent-boundary")
    covered = Fraction(0)
    for interval in original.intervals:
        start, end = Fraction(*interval.exact_interval_start), Fraction(*interval.exact_interval_end)
        if end < covered or start < covered or start > covered and not _adjacent(covered, start):
            missing.add("original-interval-union-omits-representable-global-clock-domain")
        covered = end
    if original.actual_terminal_clocks[0] is None or covered != Fraction(*original.actual_terminal_clocks[0]):
        missing.add("original-interval-union-omits-terminal-suffix")
    return A.FALSIFIED if adverse else A.UNEVALUABLE if missing else A.SATISFIED, tuple(sorted(adverse | missing))


@dataclass(frozen=True, slots=True)
class RepresentableClockAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/representable-clock-assessment"
    assessment_id: str
    policy: RepresentableClockPolicy
    original_pair: paired.FullStateStreamAssessment
    complete_call_censuses: tuple[tuple[ClockCall, ...], ...]
    boundaries: tuple[ClockBoundary, ...]
    disposition: A
    reason_codes: tuple[str, ...]
    scope: str = SCOPE
    real_open_gaps_retain_original_disposition: bool = True
    whole_time_certified: bool = False
    physical_qualification: bool = False
    later_use_admission: bool = False

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        self.policy.__post_init__()
        self.original_pair.__post_init__()
        if (self.policy.original_control != self.original_pair.control or type(self.complete_call_censuses) is not tuple
                or len(self.complete_call_censuses) != 2 or any(type(side) is not tuple for side in self.complete_call_censuses)
                or tuple(len(side) for side in self.complete_call_censuses) != self.original_pair.declared_segment_counts
                or tuple(tuple(row.summary for row in side) for side in self.complete_call_censuses) != tuple(
                    tuple(row.summary for row in side) for side in self.original_pair.segment_assessments)
                or type(self.boundaries) is not tuple or tuple((row.side, row.next_segment) for row in self.boundaries) != tuple(
                    (side, i) for side, rows in zip(("LEFT", "RIGHT"), self.complete_call_censuses, strict=True) for i in range(2, len(rows) + 1))
                or self.scope != SCOPE or self.real_open_gaps_retain_original_disposition is not True
                or any(type(row) is not bool or row for row in (self.whole_time_certified, self.physical_qualification, self.later_use_admission))):
            raise ValueError("representable coverage loses complete original calls/boundaries or invents broader admission")
        for side, terminal in zip(self.complete_call_censuses, self.original_pair.actual_terminal_clocks, strict=True):
            for row in side:
                row.__post_init__()
            if side and side[-1].exact_end != terminal:
                raise ValueError("representable coverage substitutes the actual original terminal clock")
        for boundary in self.boundaries:
            boundary.__post_init__()
            side = self.complete_call_censuses[0 if boundary.side == "LEFT" else 1]
            previous, following = side[boundary.next_segment - 2:boundary.next_segment]
            if (boundary.exact_start != previous.exact_end or boundary.exact_end != following.exact_start
                    or boundary.state_continuity.checked_components != previous.state_rows
                    or boundary.returned_derivative_continuity.checked_components != previous.state_rows
                    or following.state_rows != previous.state_rows):
                raise ValueError("representable boundary changes original clock/row denominator")
        if (self.disposition, self.reason_codes) != _reasons(self.original_pair, self.complete_call_censuses, self.boundaries):
            raise ValueError("representable coverage bypasses independent interval/boundary/event/suffix controls")


def assess_representable_clock(policy, original_pair, left, right):
    """Reconsume original custody/arrays in bounded memory; never fill a gap."""
    policy.__post_init__()
    original_pair.__post_init__()
    if policy.original_control != original_pair.control:
        raise ValueError("representable coverage substitutes original comparison protocol")
    calls, boundaries = [], []
    for side_index, (side, operand, expected) in enumerate(zip(("LEFT", "RIGHT"), (left, right),
            (original_pair.left_evidence, original_pair.right_evidence), strict=True)):
        if science.identity(operand.evidence, "evidence_id") != expected:
            raise ValueError("representable coverage substitutes complete original evidence")
        cursor = paired._Cursor(operand, side, [])
        if (dict(cursor.trace.config.source.source_members).get("solvers/base_solver.py") != policy.selected_step_source_sha256
                or (cursor.trace.config.rtol, cursor.trace.config.atol) != (policy.comparison_rtol, policy.comparison_atol)):
            raise ValueError("representable coverage substitutes actual selected step source or original weights")
        side_calls, previous = [], None
        while cursor.frame is not None:
            frame = cursor.frame
            if cursor.start is None or frame.initial_derivative is None or frame.terminal_derivative is None:
                raise ValueError("representable coverage lacks actual full clock/state/derivative operands")
            rows = cursor.evidence.layout.differential_count + cursor.evidence.layout.algebraic_count
            side_calls.append(ClockCall(science.identity(cursor.operand.summary, "summary_id"),
                science.identity(frame.full_state, "segment_id"), frame.request.identity, _fraction(cursor.start), _fraction(cursor.end), rows))
            if previous is not None:
                prior_frame, prior_end = previous
                prior_inputs, inputs = json.loads(prior_frame.request.primitive_json)["inputs"], json.loads(frame.request.primitive_json)["inputs"]
                same_regime = (prior_inputs == inputs and prior_frame.full_state.returned_model_expression_sha256 == frame.full_state.returned_model_expression_sha256)
                boundaries.append(ClockBoundary(side, cursor.index, _fraction(prior_end), _fraction(cursor.start),
                    *(science.identity(row, "observation_id") for row in (frame.requested_initial, prior_frame.actual_terminal,
                        frame.actual_initial, prior_frame.terminal_derivative, frame.initial_derivative)),
                    frame.requested_initial.binary64_hex == prior_frame.actual_terminal.binary64_hex, same_regime,
                    _metric(prior_frame.actual_terminal.binary64_hex, frame.actual_initial.binary64_hex, rows, policy),
                    _metric(prior_frame.terminal_derivative.binary64_hex, frame.initial_derivative.binary64_hex, rows, policy)))
            previous = frame, cursor.end
            cursor.advance()
        if tuple(cursor.assessments) != original_pair.segment_assessments[side_index]:
            raise ValueError("representable coverage substitutes independently assessed original native calls")
        calls.append(tuple(side_calls))
    disposition, reasons = _reasons(original_pair, tuple(calls), tuple(boundaries))
    return RepresentableClockAssessment("assessment.binary64." + original_pair.assessment_id, policy, original_pair,
        tuple(calls), tuple(boundaries), disposition, reasons)
