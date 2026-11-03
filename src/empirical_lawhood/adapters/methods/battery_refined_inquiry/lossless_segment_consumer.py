# SPDX-License-Identifier: MPL-2.0
"""Independent new-physical-schema segment integrity and unchanged arithmetic.

Raw/full historical-format identities are decoded subject witnesses only.
Actual native receipts retain their new storage schemas. The scientific
checks below reuse original request, endpoint, convergence and receiver logic;
complete missing/adverse outcomes retain their actual denominators.
"""

from contextlib import contextmanager
from decimal import Decimal
from fractions import Fraction
import math

from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.adapters.methods.battery_segmented_inquiry import evidence_stream as old
from . import lossless_evidence_stream as stream
from . import preparation_contracts as pc
from . import preparation_science as ps
from . import segmented_contracts as sc
from . import segmented_evidence as se
from . import segmented_fidelity as local
from . import segmented_fidelity_stream as paired
from . import segmented_qualification as qualification
from . import segmented_science as ss

D = Decimal


def _raw_counts(raw):
    if raw is None:
        return 0, 0, 0
    return sum(row.size_bytes for row in raw.arrays), len(raw.arrays), sum(math.prod(row.shape) for row in raw.arrays if row.role == "all_ys")


def assess_operand(operand):
    """Actual physical census first; every decoded state/derivative thereafter."""
    if type(operand) is not local.FullStateOperand or type(operand.frame) is not stream.LosslessSegmentFrame:
        raise ValueError("lossless segment assessment requires a complete decoded authentic frame")
    frame = operand.frame
    frame.__post_init__()
    config, protocol, layout, summary = operand.configuration, operand.protocol, operand.layout, operand.summary
    if type(config) is not sc.SegmentedNativeConfig or type(protocol) is not pc.PreparationProtocol or type(summary) is not sc.SegmentSummary:
        raise ValueError("lossless assessment substitutes actual scientific configuration/protocol/summary")
    for row in (config, protocol, summary):
        row.__post_init__()
    if (protocol.configuration != ss.identity(config, "config_id") or protocol.source != config.preparation.source
            or protocol.parameter_source != config.preparation.parameter_source
            or protocol.model_family != ("DFN" if "dfn" in config.model_view else "SPMe")
            or (protocol.electrode_points, protocol.particle_points) != (config.numerical_view.electrode_points, config.numerical_view.particle_points)
            or protocol.initial_temperature_k != config.initial_temperature_k
            or not set(ps.PREPARATION_SOURCE_MEMBERS).issubset(protocol.source_members)):
        raise ValueError("lossless assessment changes actual source, physics, mesh, temperature or pins")
    if layout is not None and (type(layout) is not pc.ProcessedInitialStateLayout
            or not layout.observed_from_built_model or ps._layout_reasons(protocol, layout)):
        raise ValueError("lossless assessment changes complete actual layout or scaling")
    ss.authenticate_request_custody(summary, frame.request, frame.definition, frame.native_receipt, frame.request_receipt)
    states = tuple(getattr(frame, name) for name in ("requested_initial", "actual_initial", "initial_derivative", "actual_terminal", "terminal_derivative"))
    if (summary.configuration != ss.identity(config, "config_id") or summary.protocol != ss.identity(protocol, "protocol_id")
            or summary.request != frame.request.identity or summary.returned != ss.identity(frame.returned, "return_id")
            or frame.request.configuration != summary.configuration or frame.request.protocol != summary.protocol
            or frame.request.ordinal != summary.segment_index or frame.request.kind != "charging"):
        raise ValueError("lossless assessment changes exact summary and entered primitive lineage")
    for field, row in zip(("requested_initial", "actual_initial", "initial_derivative", "actual_terminal", "terminal_derivative"), states, strict=True):
        if ((row is None) != (getattr(summary, field) is None)
                or row is not None and ss.identity(row, "observation_id") != getattr(summary, field)):
            raise ValueError("lossless assessment substitutes an actual boundary identity or absence")
    raw, full = frame.raw_return, frame.full_state
    if ((raw is None) != (summary.raw_return is None) or raw is not None and raw.decoded_subject != summary.raw_return
            or (full is None) != (summary.full_state is None) or full is not None and full.index.decoded_subject != summary.full_state):
        raise ValueError("lossless assessment changes exact decoded scientific subject identities")
    raw_bytes, raw_arrays, raw_states = _raw_counts(raw)
    count = 0 if full is None else sum(len(block.state_binary64) for block in full.blocks)
    knots = 0 if full is None else sum(len(block.clock_binary64) for block in full.blocks)
    derivatives = 0 if full is None else sum(len(block.derivative_binary64 or ()) for block in full.blocks)
    if summary.disposition == "TECHNICAL_FAILURE":
        if frame.native_receipt.operational_status is OperationalStatus.SUCCEEDED:
            raise ValueError("lossless adverse segment changes its actual completed failure receipt")
        reasons = {"actual-segment-technical-failure"}
        if full is None:
            reasons.add("actual-full-native-payload-unavailable")
        if frame.returned.disposition == "RETURNED" and raw is None:
            reasons.add("actual-returned-raw-array-custody-unavailable")
        if any(row is None for row in states):
            reasons.add("complete-requested-and-returned-boundary-denominator-unavailable")
        return ss.SegmentAssessment("assessment." + summary.summary_id, ss.identity(summary, "summary_id"), summary.native_receipt,
            A.UNEVALUABLE, tuple(sorted(reasons)), count, knots, derivatives, 0,
            retained_raw_bytes=raw_bytes, retained_raw_arrays=raw_arrays, retained_raw_state_elements=raw_states)
    if layout is None or full is None or raw is None or any(row is None for row in states):
        raise ValueError("lossless returned segment omits complete actual layout/raw/state/boundaries")
    protocol_id, layout_id = ss.identity(protocol, "protocol_id"), ss.identity(layout, "layout_id")
    if (layout.protocol != protocol_id or full.protocol != protocol_id or full.layout != layout_id
            or full.request != frame.request.identity or full.returned != summary.returned or full.raw_return != summary.raw_return
            or any(row.protocol != protocol_id or row.layout != layout_id for row in states)
            or tuple(row.role for row in states) != ("requested-initial", "actual-initial", "initial-derivative", "actual-terminal", "terminal-derivative")):
        raise ValueError("lossless assessment changes actual layout/state/source roles")
    requested_initial, actual_initial, initial_derivative, actual_terminal, terminal_derivative = states
    adverse, missing = set(), set()
    # Independent raw/full equivalence was exhausted by the decoder, including
    # every dtype/shape/order/finite component and exact canonical subject SHA.
    # Original request and all remaining numerical guards are reused exactly.
    adverse.update(ss._request_reasons(config, layout, summary, frame.request, full, operand.previous_terminal))
    if summary.disposition != "RETURNED" or frame.returned.disposition != "RETURNED" or frame.native_receipt.operational_status is not OperationalStatus.SUCCEEDED:
        missing.add("actual-native-segment-successful-return-unavailable")
    expected_horizon = min(config.method.maximum_segment_horizon_s, config.method.maximum_model_clock_s - summary.requested_start_clock_s)
    if summary.requested_horizon_s != expected_horizon:
        adverse.add("segment-request-changed-prospective-scientific-horizon")
    clocks = tuple(D(str(float.fromhex(value))) for block in full.blocks for value in block.clock_binary64)
    if clocks != summary.native_times_s or full.actual_termination != summary.termination:
        adverse.add("complete-native-clock-or-termination-denominator-disagrees")
    if not clocks or clocks[-1] > config.method.maximum_model_clock_s:
        adverse.add("native-segment-exceeds-global-scientific-clock")
    endpoint = D(str(float(summary.requested_start_clock_s) + float(summary.requested_horizon_s)))
    if summary.termination == "final time" and (not clocks or clocks[-1] != endpoint):
        adverse.add("final-time-return-misses-exact-source-binary64-endpoint")
    if any(block.state_rows != layout.differential_count + layout.algebraic_count for block in full.blocks):
        adverse.add("complete-native-state-row-denominator-disagrees")
    if any(digest != layout.model_expression_sha256 for digest in full.returned_model_expression_sha256):
        adverse.add("actual-returned-native-model-differs-from-observed-layout")
    for state, block, terminal, derivative in ((actual_initial, full.blocks[0], False, False),
            (actual_terminal, full.blocks[-1], True, False), (initial_derivative, full.blocks[0], False, True),
            (terminal_derivative, full.blocks[-1], True, True)):
        bits = ss._endpoint_bits(block, terminal, derivative)
        if bits is None:
            if state.kind is not pc.ObservationKind.UNAVAILABLE:
                adverse.add("absent-native-derivative-was-invented")
        elif (state.kind is not pc.ObservationKind.OBSERVED or state.binary64_hex != bits
                or state.model_clock_s != D(str(float.fromhex(block.clock_binary64[-1 if terminal else 0])))):
            adverse.add("native-full-array-boundary-or-derivative-bits-disagree")
    continuity_count = 0
    if requested_initial.kind is not pc.ObservationKind.OBSERVED:
        missing.add("actual-requested-full-initial-state-unobserved")
    elif requested_initial.model_clock_s not in (summary.requested_start_clock_s,
            D(str(math.nextafter(float(summary.requested_start_clock_s), math.inf)))):
        adverse.add("requested-full-state-global-clock-disagrees")
    previous_terminal = operand.previous_terminal
    if previous_terminal is not None:
        previous_terminal.__post_init__()
        if (previous_terminal.kind is not pc.ObservationKind.OBSERVED or previous_terminal.role != "actual-terminal"
                or previous_terminal.layout != layout_id or previous_terminal.protocol != protocol_id):
            raise ValueError("lossless continuity substitutes previous complete terminal state")
        if previous_terminal.model_clock_s != summary.requested_start_clock_s or requested_initial.binary64_hex != previous_terminal.binary64_hex:
            adverse.add("derived-continuation-changes-complete-terminal-state-or-clock")
        if len(actual_initial.scaled_values) != layout.differential_count + layout.algebraic_count:
            adverse.add("actual-reinitialized-full-state-denominator-omitted")
        else:
            continuity_count = layout.differential_count
            if any(not ps._close(left, right, config.atol, config.rtol) for left, right in zip(
                    previous_terminal.scaled_values[:layout.differential_count], actual_initial.scaled_values[:layout.differential_count], strict=True)):
                adverse.add("native-consistent-initialization-changes-differential-continuation")
    elif summary.segment_index != 1:
        missing.add("previous-complete-terminal-state-unavailable")
    return ss.SegmentAssessment("assessment." + summary.summary_id, ss.identity(summary, "summary_id"), summary.native_receipt,
        A.FALSIFIED if adverse else A.UNEVALUABLE if missing else A.SATISFIED, tuple(sorted(adverse | missing)), count, knots,
        derivatives, continuity_count, retained_raw_bytes=raw_bytes, retained_raw_arrays=raw_arrays, retained_raw_state_elements=raw_states)


def assess_trace(config, evidence, port, *, temporary_file):
    evidence.__post_init__()
    if evidence.trace.config != config:
        raise ValueError("lossless trace consumer changes actual selected native configuration")
    preparation = se.assess_preparation_evidence(config, evidence)
    frames = iter(stream.read_frames(port, temporary_file=temporary_file))
    try:
        header = next(frames)
        if (header.trace != ss.identity(evidence.trace, "trace_id") or header.protocol != ss.identity(evidence.protocol, "protocol_id")
                or header.segment_count != len(evidence.trace.segments)):
            raise ValueError("lossless trace consumer changes complete original header/call denominator")
        previous, assessments = None, []
        for summary in evidence.trace.segments:
            frame = next(frames)
            if frame.segment_index != summary.segment_index or frame.definition.identity != summary.native_definition:
                raise ValueError("lossless trace consumer changes actual native definition or call order")
            _successor(evidence.trace, summary.segment_index - 1, frame)
            assessments.append(assess_operand(local.FullStateOperand(config, evidence.protocol, evidence.layout, summary, frame, previous)))
            previous = frame.actual_terminal
        if next(frames, None) is not None:
            raise ValueError("lossless trace consumer adds undeclared native calls")
        return qualification.summarize_trace(evidence.trace, preparation, tuple(assessments))
    finally:
        frames.close()


def _successor(trace, index, frame):
    summary, successor = trace.segments[index], frame.next_request
    if index + 1 == len(trace.segments):
        if (successor.kind != "end-of-chain" or successor.ordinal != summary.segment_index
                or successor.primitive_json != canonical_json_bytes({"actual_segment_calls": len(trace.segments)}).decode()):
            raise ValueError("lossless frame hides unclosed successor work or changes complete call census")
    elif (successor.kind != "charging" or successor.ordinal != summary.segment_index + 1 or successor.identity != trace.segments[index + 1].request):
        raise ValueError("lossless frame changes original frozen successor request operands")


@contextmanager
def numerical_consumer_scope(*, temporary_file, assignments):
    """Use actual new receipts/views with the original complete interval algorithm.

    The new cursor only changes physical loading and its matching independent
    custody guard. Original interval arithmetic, query grids and gap/event/
    suffix outcomes remain unchanged. Every request consumes its actual full
    solver assignment before any comparison.
    """
    import json
    from . import forecast_step_control as step
    if type(assignments) is not tuple or any(type(row) is not step.ActualForecastStepAssignment for row in assignments):
        raise ValueError("lossless numerical consumer changes actual assignment denominator")
    for row in assignments:
        row.__post_init__()
    selected = {row.native_configuration: row for row in assignments}
    if len(selected) != len(assignments):
        raise ValueError("lossless numerical consumer changes actual assignment denominator")
    old_cursor, old_assess = paired._Cursor, local._assess_operand
    opened_readers = []

    class Cursor(old_cursor):
        def __init__(self, operand, side, issues):
            if type(operand) is not paired.FullStateStreamOperand or type(operand.evidence) is not se.SegmentedNativeEvidence:
                raise ValueError("lossless paired consumer changes actual scientific operand types")
            self.evidence, self.side, self.issues = operand.evidence, side, issues
            self.evidence.__post_init__()
            self.trace = self.evidence.trace
            self.preparation = se.assess_preparation_evidence(self.trace.config, self.evidence)
            self.frames = iter(stream.read_frames(operand.port, temporary_file=temporary_file))
            opened_readers.append(self.frames)
            header = next(self.frames)
            if (type(header) is not old.SegmentStreamHeader or header.trace != ss.identity(self.trace, "trace_id")
                    or header.protocol != ss.identity(self.evidence.protocol, "protocol_id") or header.segment_count != len(self.trace.segments)):
                raise ValueError("lossless paired stream changes original header/protocol/call census")
            self.index, self.previous_terminal, self.previous_end, self.previous_receipt = 0, None, None, None
            self.frame = self.operand = self.start = self.end = self.position = None
            self.assessments, self.terminal = [], None
            self.advance()

        def advance(self):
            if self.frame is not None:
                self.previous_terminal = self.frame.actual_terminal
                self.previous_receipt = ss.identity(self.frame.native_receipt, "receipt_id")
                self.previous_end = self.end
                self.frame = self.operand = None
            if self.index == len(self.trace.segments):
                if next(self.frames, None) is not None:
                    raise ValueError("lossless paired stream adds undeclared original calls")
                self.start = self.end = self.position = None
                return
            try:
                frame = next(self.frames)
            except StopIteration as error:
                raise ValueError("lossless paired stream omits an actual original call") from error
            summary = self.trace.segments[self.index]
            if type(frame) is not stream.LosslessSegmentFrame or frame.segment_index != self.index + 1 or frame.definition.identity != summary.native_definition:
                raise ValueError("lossless paired stream substitutes actual call/definition ordinal")
            if self.previous_receipt is not None and ss.identity(frame.request_receipt, "receipt_id") != self.previous_receipt:
                raise ValueError("lossless paired stream breaks actual request-carrier receipt chain")
            _successor(self.trace, self.index, frame)
            assignment = selected.get(frame.request.configuration)
            if (assignment is None or assignment.numerical_view != self.trace.config.native.numerical_view
                    or json.loads(frame.request.primitive_json)["solver"] != json.loads(assignment.actual_solver_json)
                    or not set(assignment.control.sources).issubset(frame.definition.sources)):
                raise ValueError("lossless actual request substitutes explicit native policy or full solver assignment")
            operand = local.FullStateOperand(self.trace.config, self.evidence.protocol, self.evidence.layout, summary, frame, self.previous_terminal)
            self.assessments.append(assess_operand(operand))
            self.index += 1
            self.frame, self.operand = frame, operand
            if frame.full_state is None:
                self.start = self.end = self.position = self.terminal = None
                self.issue("actual-full-state-clock-domain-unavailable", indices=(summary.segment_index,))
                return
            clocks = local._clocks(frame.full_state)
            self.start, self.end = clocks[0], clocks[-1]
            self.position, self.terminal = self.start, self.end
            if self.index == 1 and self.start != 0:
                self.issue("original-global-clock-prefix-uncovered", Fraction(0), self.start, (summary.segment_index,))
            elif self.previous_end is not None:
                if self.start < self.previous_end:
                    raise ValueError("lossless paired stream overlaps/reverses actual segment clocks")
                if self.start > self.previous_end:
                    self.issue("original-open-global-clock-gap-source-nextafter-not-interpolated", self.previous_end, self.start, (summary.segment_index - 1, summary.segment_index))

    paired._Cursor, local._assess_operand = Cursor, assess_operand
    try:
        yield
    finally:
        paired._Cursor, local._assess_operand = old_cursor, old_assess
        for reader in opened_readers:
            reader.close()
