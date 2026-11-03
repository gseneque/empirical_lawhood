# SPDX-License-Identifier: MPL-2.0
"""Complete paired segment-stream census with explicit unassessed clock spans.

Two monotone cursors retain an active original segment and its preceding full
terminal vector per operand. All interval products are compact. No extrapolated
state, phase alignment or gap closure is supplied by this numerical control.
"""

from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord, canonical_json_bytes, require_sorted_unique_strings, validate_stable_id,
)
from . import segmented_contracts as sc
from . import segmented_evidence as se
from . import segmented_fidelity as local
from . import segmented_science as ss

D = Decimal


def _fraction(value):
    return (value.numerator, value.denominator)


def _require_fraction(value):
    if (type(value) is not tuple or len(value) != 2 or any(type(n) is not int for n in value)
            or value[0] < 0 or value[1] <= 0 or _fraction(Fraction(*value)) != value):
        raise ValueError("stream coverage changes an exact nonnegative rational clock")


@dataclass(frozen=True, slots=True)
class StreamCoverageIssue(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/full-state-stream-coverage-issue"
    issue_id: str
    side: str
    code: str
    exact_start: tuple[int, int] | None
    exact_end: tuple[int, int] | None
    segment_indices: tuple[int, ...]

    def __post_init__(self):
        validate_stable_id(self.issue_id)
        validate_stable_id(self.code)
        if self.side not in {"LEFT", "RIGHT", "BOTH"} or any(type(n) is not int or n < 1 for n in self.segment_indices):
            raise ValueError("stream coverage loses its original operand/call census")
        if (self.exact_start is None) != (self.exact_end is None):
            raise ValueError("stream coverage invents one unavailable interval boundary")
        if self.exact_start is not None:
            _require_fraction(self.exact_start)
            _require_fraction(self.exact_end)
            if Fraction(*self.exact_end) < Fraction(*self.exact_start):
                raise ValueError("stream coverage reverses an actual global-clock interval")


@dataclass(frozen=True, slots=True)
class FullStateStreamAssessment(CanonicalRecord):
    """Complete returned-call comparison, separate from a forecast supplier.

    Interval boundary queries may repeat across neighbouring overlap products;
    the comparison counts are their explicit sum, not an invented unique grid.
    All original segment and knot denominators remain separately retained.
    """
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/full-state-stream-assessment"
    assessment_id: str
    control: ObjectIdentity
    left_evidence: ObjectIdentity
    right_evidence: ObjectIdentity
    left_trace: ObjectIdentity
    right_trace: ObjectIdentity
    left_configuration: ObjectIdentity
    right_configuration: ObjectIdentity
    preparations: tuple[ss.DerivedPreparationAssessment | ss.UnavailableDerivedPreparationAssessment, ...]
    declared_segment_counts: tuple[int, int]
    segment_assessments: tuple[tuple[ss.SegmentAssessment, ...], tuple[ss.SegmentAssessment, ...]]
    original_retained_native_knots: tuple[int, int]
    actual_terminal_clocks: tuple[tuple[int, int] | None, tuple[int, int] | None]
    declared_transition_counts: tuple[int, int]
    intervals: tuple[local.FullStateIntervalAssessment, ...]
    coverage_issues: tuple[StreamCoverageIssue, ...]
    interval_queries_including_repeated_boundaries: int
    compared_rhs_components: int
    compared_algebraic_components: int
    compared_derivative_components: int
    disposition: A
    reason_codes: tuple[str, ...]
    scope: str = "COMPLETE_ORIGINAL_STREAM_CENSUS;NOT_A_LATER_USE_SUPPLIER"
    interpolation_error_certified: bool = False
    whole_time_certified: bool = False
    physical_qualification: bool = False
    historical_completion: str = "NOT_ASSESSED;OLD_UNKNOWN_RETAINED"
    fresh_physical_units: int = 0

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes")
        for identity, schema in ((self.control, local.FullStateControlProtocol.SCHEMA),
                *((row, se.SegmentedNativeEvidence.SCHEMA) for row in (self.left_evidence, self.right_evidence)),
                *((row, sc.SegmentedTrace.SCHEMA) for row in (self.left_trace, self.right_trace)),
                *((row, sc.SegmentedNativeConfig.SCHEMA) for row in (self.left_configuration, self.right_configuration))):
            if type(identity) is not ObjectIdentity or identity.object_schema != schema:
                raise ValueError("stream assessment substitutes its original scientific operands")
        if (len(self.preparations) != 2 or any(type(row) not in
                {ss.DerivedPreparationAssessment, ss.UnavailableDerivedPreparationAssessment} for row in self.preparations)
                or tuple(row.configuration for row in self.preparations) != (self.left_configuration, self.right_configuration)):
            raise ValueError("stream assessment changes independently assessed actual preparation")
        for counts in (self.declared_segment_counts, self.original_retained_native_knots, self.declared_transition_counts):
            if type(counts) is not tuple or len(counts) != 2 or any(type(n) is not int or n < 0 for n in counts):
                raise ValueError("stream assessment changes its complete original denominator")
        if type(self.segment_assessments) is not tuple or len(self.segment_assessments) != 2:
            raise ValueError("stream assessment loses an original operand")
        for side, expected, knots in zip(self.segment_assessments, self.declared_segment_counts,
                self.original_retained_native_knots, strict=True):
            if (type(side) is not tuple or len(side) != expected or any(type(row) is not ss.SegmentAssessment for row in side)
                    or knots != sum(row.retained_native_knots for row in side)
                    or len({row.summary for row in side}) != len(side)):
                raise ValueError("stream assessment omits, duplicates or relabels original returned calls")
        if type(self.actual_terminal_clocks) is not tuple or len(self.actual_terminal_clocks) != 2:
            raise ValueError("stream assessment loses actual terminal clock operands")
        for value in self.actual_terminal_clocks:
            if value is not None:
                _require_fraction(value)
        if any(type(row) is not local.FullStateIntervalAssessment for row in self.intervals):
            raise ValueError("stream assessment substitutes independent full-state interval products")
        for interval in self.intervals:
            interval.__post_init__()
            if (interval.control != self.control or interval.left_configuration != self.left_configuration
                    or interval.right_configuration != self.right_configuration
                    or interval.left_segment_assessment not in self.segment_assessments[0]
                    or interval.right_segment_assessment not in self.segment_assessments[1]):
                raise ValueError("stream interval changes its independently recomputed original call joins")
        if any(type(row) is not StreamCoverageIssue for row in self.coverage_issues):
            raise ValueError("stream assessment substitutes its exact uncovered-span census")
        for issue in self.coverage_issues:
            issue.__post_init__()
        if len({row.issue_id for row in self.coverage_issues}) != len(self.coverage_issues):
            raise ValueError("stream assessment repeats a coverage issue identity")
        fields = ("interval_queries_including_repeated_boundaries", "compared_rhs_components",
                  "compared_algebraic_components", "compared_derivative_components")
        operands = ("query_count", "checked_rhs_components", "checked_algebraic_components", "checked_derivative_components")
        if any(type(getattr(self, name)) is not int or getattr(self, name) != sum(getattr(row, operand) for row in self.intervals)
               for name, operand in zip(fields, operands, strict=True)):
            raise ValueError("stream assessment changes complete interval comparison counts")
        if (type(self.disposition) is not A or self.scope != "COMPLETE_ORIGINAL_STREAM_CENSUS;NOT_A_LATER_USE_SUPPLIER"
                or self.historical_completion != "NOT_ASSESSED;OLD_UNKNOWN_RETAINED"
                or type(self.fresh_physical_units) is not int or self.fresh_physical_units != 0
                or any(type(getattr(self, name)) is not bool or getattr(self, name) for name in
                       ("interpolation_error_certified", "whole_time_certified", "physical_qualification"))
                or self.disposition is not A.SATISFIED and not self.reason_codes):
            raise ValueError("stream comparison invents scientific supply, fresh units or old completion")
        products = (*self.preparations, *self.segment_assessments[0], *self.segment_assessments[1], *self.intervals)
        if self.disposition is A.SATISFIED and (self.reason_codes or self.coverage_issues or not self.intervals
                or not all(self.declared_segment_counts) or self.actual_terminal_clocks[0] is None
                or self.actual_terminal_clocks[0] != self.actual_terminal_clocks[1]
                or any(self.declared_transition_counts) or any(row.disposition is not A.SATISFIED for row in products)):
            raise ValueError("satisfied stream comparison omits actual preparation, coverage, events or adverse products")
        if self.disposition is A.SATISFIED:
            covered = Fraction(0)
            for interval in self.intervals:
                start, end = Fraction(*interval.exact_interval_start), Fraction(*interval.exact_interval_end)
                if start > covered or end < covered:
                    raise ValueError("satisfied stream comparison omits an exact global-clock interval")
                covered = end
            if (covered != Fraction(*self.actual_terminal_clocks[0]) or any(
                    set(side) != {getattr(interval, name) for interval in self.intervals}
                    for side, name in zip(self.segment_assessments, ("left_segment_assessment", "right_segment_assessment"), strict=True))):
                raise ValueError("satisfied stream comparison omits a terminal suffix or independently assessed call")


@dataclass(frozen=True, slots=True)
class FullStateStreamOperand:
    evidence: se.SegmentedNativeEvidence
    port: object


class _Cursor:
    def __init__(self, operand, side, issues):
        from empirical_lawhood.adapters.methods.battery_segmented_inquiry import evidence_stream as stream
        if type(operand) is not FullStateStreamOperand or type(operand.evidence) is not se.SegmentedNativeEvidence:
            raise ValueError("paired control requires original typed scientific evidence and declared streams")
        self.evidence, self.side, self.issues = operand.evidence, side, issues
        self.evidence.__post_init__()
        self.trace = self.evidence.trace
        self.preparation = se.assess_preparation_evidence(self.trace.config, self.evidence)
        self.frames = iter(stream.read_frames(operand.port))
        header = next(self.frames)
        if (type(header) is not stream.SegmentStreamHeader or header.trace != ss.identity(self.trace, "trace_id")
                or header.protocol != ss.identity(self.evidence.protocol, "protocol_id")
                or header.segment_count != len(self.trace.segments)):
            raise ValueError("paired stream substitutes original header, protocol or complete returned-call census")
        self.index, self.previous_terminal, self.previous_end, self.previous_receipt = 0, None, None, None
        self.frame, self.operand, self.start, self.end, self.position = None, None, None, None, None
        self.assessments = []
        self.terminal = None
        self.advance()

    def issue(self, code, start=None, end=None, indices=()):
        self.issues.append(StreamCoverageIssue("coverage." + self.side.lower() + "." + str(len(self.issues)),
            self.side, code, None if start is None else _fraction(start), None if end is None else _fraction(end), indices))

    def advance(self):
        from empirical_lawhood.adapters.methods.battery_segmented_inquiry import evidence_stream as stream
        if self.frame is not None:
            self.previous_terminal = self.frame.actual_terminal
            self.previous_receipt = ss.identity(self.frame.native_receipt, "receipt_id")
            self.previous_end = self.end
            self.frame, self.operand = None, None
        if self.index == len(self.trace.segments):
            if next(self.frames, None) is not None:
                raise ValueError("paired stream adds undeclared original calls")
            self.start, self.end, self.position = None, None, None
            return
        try:
            frame = next(self.frames)
        except StopIteration as error:
            raise ValueError("paired stream omits an original returned call") from error
        summary = self.trace.segments[self.index]
        if (type(frame) is not stream.SegmentEvidenceFrame or frame.segment_index != self.index + 1
                or frame.definition.identity != summary.native_definition):
            raise ValueError("paired stream substitutes an actual call ordinal or stored native definition")
        if self.previous_receipt is not None and ss.identity(frame.request_receipt, "receipt_id") != self.previous_receipt:
            raise ValueError("paired stream breaks the original successor request-carrier receipt chain")
        successor = frame.next_request
        if self.index + 1 == len(self.trace.segments):
            if (successor.kind != "end-of-chain" or successor.ordinal != summary.segment_index
                    or successor.primitive_json != canonical_json_bytes({"actual_segment_calls": len(self.trace.segments)}).decode()):
                raise ValueError("paired stream hides unclosed successor work or changes complete call census")
        elif (successor.kind != "charging" or successor.ordinal != summary.segment_index + 1
                or successor.identity != self.trace.segments[self.index + 1].request):
            raise ValueError("paired stream changes original frozen successor request operands")
        operand = local.FullStateOperand(self.trace.config, self.evidence.protocol, self.evidence.layout,
            summary, frame, self.previous_terminal)
        assessment = local._assess_operand(operand)
        self.assessments.append(assessment)
        self.index += 1
        self.frame, self.operand = frame, operand
        if frame.full_state is None:
            self.start, self.end, self.position, self.terminal = None, None, None, None
            self.issue("actual-full-state-clock-domain-unavailable", indices=(summary.segment_index,))
            return
        clocks = local._clocks(frame.full_state)
        self.start, self.end = clocks[0], clocks[-1]
        self.position, self.terminal = self.start, self.end
        if self.index == 1 and self.start != 0:
            self.issue("original-global-clock-prefix-uncovered", Fraction(0), self.start, (summary.segment_index,))
        elif self.previous_end is not None:
            if self.start < self.previous_end:
                raise ValueError("paired stream overlaps or reverses actual segment clock domains")
            if self.start > self.previous_end:
                self.issue("original-open-global-clock-gap-source-nextafter-not-interpolated",
                    self.previous_end, self.start, (summary.segment_index - 1, summary.segment_index))


def assess_streams(control, left, right):
    """Consume both complete original streams without accumulating arrays.

    A complete adverse or uncertain result is useful. No favourable subset of
    overlaps can cover an omitted interval, event, suffix or returned call.
    """
    if type(control) is not local.FullStateControlProtocol:
        raise ValueError("paired stream comparison requires an explicit prospective full-state protocol")
    control.__post_init__()
    if type(left) is not FullStateStreamOperand or type(right) is not FullStateStreamOperand:
        raise ValueError("paired stream comparison requires original typed operands")
    a, b = left.evidence.trace.config, right.evidence.trace.config
    if (a.native != b.native or a.preparation != b.preparation or a.preparation_assessment != b.preparation_assessment
            or (a.method.maximum_segment_horizon_s, b.method.maximum_segment_horizon_s) not in ((D(60), D(30)), (D(30), D(15)))):
        raise ValueError("paired stream comparison changes isolated native/root/half-segment operands")
    issues, intervals = [], []
    cursors = (_Cursor(left, "LEFT", issues), _Cursor(right, "RIGHT", issues))
    first, second = cursors
    while first.frame is not None or second.frame is not None:
        if first.frame is None or second.frame is None:
            cursor = second if first.frame is None else first
            if cursor.start is not None:
                cursor.issue("unpaired-actual-terminal-suffix", cursor.position, cursor.end, (cursor.index,))
            cursor.advance()
            continue
        if first.start is None or second.start is None:
            if first.start is None:
                first.advance()
            if second.start is None:
                second.advance()
            continue
        start, end = max(first.position, second.position), min(first.end, second.end)
        if end < start:
            cursor = first if first.end < second.position else second
            cursor.issue("unpaired-actual-global-clock-span", cursor.position, cursor.end, (cursor.index,))
            cursor.advance()
            continue
        for cursor in cursors:
            if cursor.position < start:
                cursor.issue("unpaired-actual-global-clock-span", cursor.position, start, (cursor.index,))
        intervals.append(local.assess_interval(control, first.operand, second.operand, start_s=start, end_s=end))
        first.position = second.position = end
        if first.end == end:
            first.advance()
        if second.end == end:
            second.advance()
    traces = tuple(cursor.trace for cursor in cursors)
    if first.terminal != second.terminal:
        available = tuple(value for value in (first.terminal, second.terminal) if value is not None)
        issues.append(StreamCoverageIssue("coverage.both." + str(len(issues)), "BOTH", "actual-terminal-clocks-differ",
            None if len(available) != 2 else _fraction(min(available)), None if len(available) != 2 else _fraction(max(available)), ()))
    if (traces[0].disposition, traces[0].termination) != (traces[1].disposition, traces[1].termination):
        issues.append(StreamCoverageIssue("coverage.both." + str(len(issues)), "BOTH", "actual-terminal-outcome-or-event-differs", None, None, ()))
    if traces[0].transitions or traces[1].transitions:
        issues.append(StreamCoverageIssue("coverage.both." + str(len(issues)), "BOTH", "one-sided-hybrid-event-control-unqualified", None, None, ()))
        if len(traces[0].transitions) != len(traces[1].transitions):
            issues.append(StreamCoverageIssue("coverage.both." + str(len(issues)), "BOTH", "actual-hybrid-event-denominators-differ", None, None, ()))
        for before, after in zip(traces[0].transitions, traces[1].transitions):
            if before.root_clock_s != after.root_clock_s:
                start, end = sorted((Fraction(before.root_clock_s), Fraction(after.root_clock_s)))
                issues.append(StreamCoverageIssue("coverage.both." + str(len(issues)), "BOTH", "actual-hybrid-root-clocks-differ",
                    _fraction(start), _fraction(end), (before.preceding_segment, after.preceding_segment)))
    products = (*(cursor.preparation for cursor in cursors), *(row for cursor in cursors for row in cursor.assessments), *intervals)
    reasons = {issue.code for issue in issues}
    reasons.update(reason for product in products if product.disposition is not A.SATISFIED for reason in product.reason_codes)
    if not intervals:
        reasons.add("no-complete-actual-overlap-interval-assessed")
    return FullStateStreamAssessment("assessment.full-state-stream." + a.config_id + "." + b.config_id,
        ss.identity(control, "control_id"), *(ss.identity(operand.evidence, "evidence_id") for operand in (left, right)),
        *(ss.identity(trace, "trace_id") for trace in traces), ss.identity(a, "config_id"), ss.identity(b, "config_id"),
        tuple(cursor.preparation for cursor in cursors), tuple(len(trace.segments) for trace in traces),
        tuple(tuple(cursor.assessments) for cursor in cursors), tuple(sum(row.retained_native_knots for row in cursor.assessments) for cursor in cursors),
        tuple(None if cursor.terminal is None else _fraction(cursor.terminal) for cursor in cursors), tuple(len(trace.transitions) for trace in traces),
        tuple(intervals), tuple(issues), *(sum(getattr(row, name) for row in intervals) for name in
            ("query_count", "checked_rhs_components", "checked_algebraic_components", "checked_derivative_components")),
        A.FALSIFIED if any(product.disposition is A.FALSIFIED for product in products) else A.UNEVALUABLE if reasons else A.SATISFIED,
        tuple(sorted(reasons)))
