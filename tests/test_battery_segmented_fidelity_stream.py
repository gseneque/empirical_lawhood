# SPDX-License-Identifier: MPL-2.0
"""Exposed complete paired-stream controls with real artifact joins, no solve."""

from dataclasses import replace
from decimal import Decimal as D
from fractions import Fraction
import io
import json
import math
import struct
import subprocess
import sys
from types import SimpleNamespace as N

import pytest

from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_evidence as se
from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_fidelity as local, segmented_fidelity_stream as paired
from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_native as native, segmented_science as ss
from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_contracts as sc
from empirical_lawhood.adapters.methods.battery_segmented_inquiry import evidence_stream as es
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.kernel.status import OperationalStatus
from tests.test_battery_segmented_fidelity import _operand, _receipt, prepared as prepared_fixture
from tests.test_battery_segmented_native import custody as native_custody, selected as selected_fixture, exposed_backend, acquire

prepared = prepared_fixture
selected = selected_fixture


class _Emitter:
    def __init__(self):
        self.payload = bytearray()

    def write(self, name, payload):
        self.payload.extend(payload)


class _Port:
    def __init__(self, payload):
        self.port, self.size_bytes = io.BytesIO(payload), len(payload)

    def read(self, size=-1):
        return self.port.read(min(size, 917))


def _stream(prepared, path, *, horizon=60, segments=1, changed_state=None, derivatives=True, last_end=None):
    original = _operand(prepared, path / "prototype", horizon=horizon,
        changed_state=changed_state, derivatives=derivatives)
    config, protocol, layout = original.configuration, original.protocol, original.layout
    protocol_id = ss.identity(protocol, "protocol_id")
    records, requests, previous = [], [], None
    for index in range(1, segments + 1):
        start, requested_end = float((index - 1) * horizon), float(index * horizon)
        end = float(last_end) if last_end is not None and index == segments else requested_end
        termination = "final time" if last_end is None or index != segments else "event: " + native.TARGET_EVENT
        shifted = start if start == 0 else math.nextafter(start, math.inf)
        def observe(name, clock):
            state = getattr(original.frame, name)
            return replace(state, observation_id=state.observation_id + ".s" + str(index),
                model_clock_s=D(str(clock)) if state.model_clock_s is not None else None)
        states = {name: observe(name, shifted if "initial" in name else end) for name in
            ("requested_initial", "actual_initial", "initial_derivative", "actual_terminal", "terminal_derivative")}
        document = json.loads(original.frame.request.primitive_json)
        document.update(requested_start={"binary64": start.hex()}, source_computed_end={"binary64": requested_end.hex()},
            previous_terminal=None if previous is None else ss._primitive_identity(previous, "observation_id"),
            continuation_metadata="NONE" if previous is None else config.method.continuation_method)
        request = replace(original.frame.request, request_id=original.frame.request.request_id + ".s" + str(index),
            ordinal=index, primitive_json=canonical_json_bytes(document).decode())
        returned = replace(original.frame.returned, return_id=original.frame.returned.return_id + ".s" + str(index), request=request.identity)
        raw = original.frame.raw_return
        clock_array = replace(raw.clock_blocks[0], bytes_hex=struct.pack("<dd", shifted, end).hex())
        raw = replace(raw, raw_id=raw.raw_id + ".s" + str(index), request=request.identity,
            returned=ss.identity(returned, "return_id"), clock_blocks=(clock_array,))
        full = original.frame.full_state
        full = replace(full, segment_id=full.segment_id + ".s" + str(index), request=request.identity,
            returned=ss.identity(returned, "return_id"), raw_return=ss.identity(raw, "raw_id"),
            blocks=(replace(full.blocks[0], clock_binary64=(shifted.hex(), end.hex())),), actual_termination=termination)
        records.append(dict(returned=returned, raw_return=raw, full_state=full, **states))
        requests.append(request)
        previous = states["actual_terminal"]
    frames, summaries = [], []
    carrier = _receipt(path / "first-carrier", (requests[0],))
    for index, (request, current) in enumerate(zip(requests, records, strict=True), 1):
        matched = next(row for row in carrier.output_logical_artifacts if row.content_sha256 == request.fingerprint())
        materialized = next(row for row in carrier.output_materializations if row.logical_artifact_id == matched.logical_artifact_id)
        definition = replace(original.frame.definition, subwork_id=original.frame.definition.subwork_id + ".s" + str(index),
            configuration=request.identity, input_materialization_ids=(materialized.materialization_id,))
        successor = requests[index] if index < segments else replace(request, request_id=request.request_id + ".end", kind="end-of-chain",
            primitive_json=canonical_json_bytes({"actual_segment_calls": segments}).decode())
        receipt = _receipt(path / ("returned-" + str(index)), (*current.values(), successor),
            inputs=definition.input_materialization_ids, definition=definition)
        clocks = tuple(D(str(float.fromhex(value))) for value in current["full_state"].blocks[0].clock_binary64)
        summary = replace(original.summary, summary_id=original.summary.summary_id + ".s" + str(index), segment_index=index,
            requested_start_clock_s=D((index - 1) * horizon), native_times_s=clocks,
            termination=current["full_state"].actual_termination,
            request=request.identity, returned=ss.identity(current["returned"], "return_id"),
            native_receipt=ss.identity(receipt, "receipt_id"), native_definition=definition.identity,
            raw_return=ss.identity(current["raw_return"], "raw_id"), full_state=ss.identity(current["full_state"], "segment_id"),
            **{name: ss.identity(current[name], "observation_id") for name in
                ("requested_initial", "actual_initial", "initial_derivative", "actual_terminal", "terminal_derivative")})
        frames.append(es.SegmentEvidenceFrame(index, definition, carrier, receipt, request, current["returned"], successor,
            *(current[name] for name in ("raw_return", "full_state", "requested_initial", "actual_initial",
                "initial_derivative", "actual_terminal", "terminal_derivative"))))
        summaries.append(summary)
        carrier = receipt
    assignment = replace(prepared[2], assignment_id="assignment.stream." + str(horizon),
        configuration=ss.identity(config, "config_id"), protocol=protocol_id)
    delivery = native.BatteryInquiryDelivery(native.CONTROL_RULE, D("4.2"), D("4.2"), config.chamber_temperature_k,
        config.chamber_temperature_k, D(0), None, "exposed control", "exposed control", "exposed I", "exposed V", "exposed chamber", None, None, None)
    trace = sc.SegmentedTrace("trace." + config.config_id, config, "a" * 64, "SERVICE_TERMINATED", summaries[-1].termination, None, None,
        delivery, (D(0), D(str(end))), *(tuple((D(0), D(0))) for _ in range(5)),
        ("CC", "CC"), ("LOW", "LOW"), (native.TARGET_EVENT, native.TIER_EVENT), ("exposed target", "exposed tier"),
        tuple(summaries), (), 1, segments, D(2 * segments), D(segments), 4096)
    main_records = (trace, protocol, assignment, layout, frames[0].requested_initial, frames[0].actual_initial,
        frames[0].initial_derivative, frames[-1].actual_terminal, frames[-1].terminal_derivative)
    main = _receipt(path / "main", main_records)
    evidence = se.SegmentedNativeEvidence("evidence.stream." + str(horizon), *main_records, native_receipt=main)
    return evidence, tuple(frames)


def _port(evidence, frames, *, header=None):
    emitter = _Emitter()
    header = header or es.SegmentStreamHeader(ss.identity(evidence.trace, "trace_id"),
        ss.identity(evidence.protocol, "protocol_id"), len(evidence.trace.segments))
    sequence = es.emit_frame(emitter, "segments", header, 0, 0)
    for index, frame in enumerate(frames, 1):
        sequence = es.emit_frame(emitter, "segments", frame, index, sequence)
    return _Port(bytes(emitter.payload))


def _compare(left, right, *, left_frames=None, right_frames=None):
    a, frames_a = left
    b, frames_b = right
    return paired.assess_streams(local.FullStateControlProtocol("control.exposed.stream"),
        paired.FullStateStreamOperand(a, _port(a, frames_a if left_frames is None else left_frames)),
        paired.FullStateStreamOperand(b, _port(b, frames_b if right_frames is None else right_frames)))


def test_complete_native_census_and_exact_unpaired_suffix_are_retained(prepared, tmp_path):
    left = _stream(prepared, tmp_path / "left")
    right = _stream(prepared, tmp_path / "right", horizon=30)
    result = _compare(left, right)
    assert result.declared_segment_counts == (1, 1) and result.original_retained_native_knots == (2, 2)
    assert result.disposition is A.UNEVALUABLE and result.intervals[0].disposition is A.SATISFIED
    assert result.interval_queries_including_repeated_boundaries == 31
    assert result.compared_rhs_components == 173 * 31 and result.compared_algebraic_components == 31
    assert result.compared_derivative_components == 174 * 31
    suffix = next(row for row in result.coverage_issues if row.code == "unpaired-actual-terminal-suffix")
    assert suffix.exact_start == (30, 1) and suffix.exact_end == (60, 1)
    assert decode_canonical_bytes(result.canonical_bytes(), type(result), maximum_bytes=None) == result
    assert not result.whole_time_certified and not result.physical_qualification
    with pytest.raises(ValueError, match="omits actual preparation"):
        replace(result, disposition=A.SATISFIED, reason_codes=())


def test_complete_matching_observed_streams_only_admit_declared_numerical_scope(prepared, tmp_path):
    left = _stream(prepared, tmp_path / "left", last_end=30)
    right = _stream(prepared, tmp_path / "right", horizon=30, last_end=30)
    result = _compare(left, right)
    assert result.disposition is A.SATISFIED and result.actual_terminal_clocks == ((30, 1), (30, 1))
    assert result.coverage_issues == () and result.declared_segment_counts == (1, 1)
    assert not result.whole_time_certified and not result.interpolation_error_certified
    assert "NOT_A_LATER_USE_SUPPLIER" in result.scope and not result.physical_qualification
    assert decode_canonical_bytes(result.canonical_bytes(), type(result), maximum_bytes=None) == result


def test_source_nextafter_open_gap_is_exact_and_never_filled_by_favourable_overlaps(prepared, tmp_path):
    left = _stream(prepared, tmp_path / "left")
    right = _stream(prepared, tmp_path / "right", horizon=30, segments=2)
    result = _compare(left, right)
    assert result.declared_segment_counts == (1, 2) and result.original_retained_native_knots == (2, 4)
    assert all(row.disposition is A.SATISFIED for row in result.intervals)
    assert result.disposition is A.UNEVALUABLE and result.actual_terminal_clocks == ((60, 1), (60, 1))
    gap = next(row for row in result.coverage_issues if row.code.startswith("original-open-global-clock-gap"))
    assert gap.exact_start == (30, 1)
    assert Fraction(*gap.exact_end) == Fraction.from_float(math.nextafter(30., math.inf))
    with pytest.raises(ValueError, match="exact global-clock"):
        replace(result, disposition=A.SATISFIED, coverage_issues=(), reason_codes=())
    raw = result.canonical_bytes()
    assert b"state_binary64" not in raw and b"bytes_hex" not in raw


def test_complete_adverse_component_counts_survive_multiple_intervals_and_later_calls(prepared, tmp_path):
    left = _stream(prepared, tmp_path / "left", segments=2)
    right = _stream(prepared, tmp_path / "right", horizon=30, segments=4, changed_state=(173, .001))
    result = _compare(left, right)
    assert result.declared_segment_counts == (2, 4) and result.original_retained_native_knots == (4, 8)
    assert result.disposition is A.FALSIFIED and all(row.disposition is A.FALSIFIED for row in result.intervals)
    assert result.compared_derivative_components == result.compared_rhs_components + result.compared_algebraic_components
    assert len(result.segment_assessments[0]) == 2 and len(result.segment_assessments[1]) == 4


def test_missing_derivatives_remain_unevaluable_in_complete_stream_control(prepared, tmp_path):
    left = _stream(prepared, tmp_path / "left", derivatives=False)
    right = _stream(prepared, tmp_path / "right", horizon=30, segments=2, derivatives=False)
    result = _compare(left, right)
    assert result.disposition is A.UNEVALUABLE and result.declared_segment_counts == (1, 2)
    assert result.compared_derivative_components == 0 and result.original_retained_native_knots == (2, 4)


@pytest.mark.parametrize("damage", ("missing", "extra", "wrong-header", "wrong-end"))
def test_complete_stream_census_refuses_missing_added_or_unclosed_native_calls(prepared, tmp_path, damage):
    left = _stream(prepared, tmp_path / "left")
    right = _stream(prepared, tmp_path / "right", horizon=30, segments=2)
    evidence, frames = right
    if damage == "missing":
        with pytest.raises(ValueError, match="omits an original"):
            _compare(left, right, right_frames=frames[:1])
    elif damage == "extra":
        with pytest.raises(ValueError):
            _compare(left, right, right_frames=(*frames, frames[-1]))
    elif damage == "wrong-header":
        header = es.SegmentStreamHeader(ss.identity(evidence.trace, "trace_id"), ss.identity(evidence.protocol, "protocol_id"), 1)
        with pytest.raises(ValueError, match="header"):
            paired.assess_streams(local.FullStateControlProtocol("control.exposed.header"),
                paired.FullStateStreamOperand(left[0], _port(*left)), paired.FullStateStreamOperand(evidence, _port(evidence, frames, header=header)))
    else:
        end = replace(frames[-1].next_request, primitive_json='{"actual_segment_calls":1}\n')
        records = (*tuple(value for name, value in frames[-1].records.items() if name != "request" and value is not None), end)
        receipt = _receipt(tmp_path / "forged-count", records, inputs=frames[-1].definition.input_materialization_ids,
            definition=frames[-1].definition)
        frame = replace(frames[-1], native_receipt=receipt, next_request=end)
        summary = replace(evidence.trace.segments[-1], native_receipt=ss.identity(receipt, "receipt_id"))
        trace = replace(evidence.trace, segments=(*evidence.trace.segments[:-1], summary))
        main_records = (trace, evidence.protocol, evidence.source_assignment, evidence.layout,
            evidence.requested_initial, evidence.actual_initial, evidence.initial_derivative, evidence.actual_terminal, evidence.terminal_derivative)
        main = _receipt(tmp_path / "forged-main", main_records)
        evidence = replace(evidence, trace=trace, native_receipt=main)
        with pytest.raises(ValueError, match="complete call census"):
            _compare(left, (evidence, (frames[0], frame)))


def test_comparison_counts_and_scientific_scope_cannot_be_relabelled(prepared, tmp_path):
    result = _compare(_stream(prepared, tmp_path / "left"), _stream(prepared, tmp_path / "right", horizon=30))
    for damage in ({"declared_segment_counts": (1, 0)}, {"compared_rhs_components": 1},
            {"original_retained_native_knots": (1, 2)}, {"physical_qualification": True}, {"fresh_physical_units": 1}):
        with pytest.raises(ValueError):
            replace(result, **damage)


def test_actual_known_failure_keeps_available_raw_denominator_and_missing_clock_domain(prepared, tmp_path):
    left, right = _stream(prepared, tmp_path / "left"), _stream(prepared, tmp_path / "right", horizon=30)
    evidence, frames = left
    frame = frames[0]
    receipt = _receipt(tmp_path / "failure-return", (frame.returned, frame.raw_return, frame.next_request),
        inputs=frame.definition.input_materialization_ids, definition=frame.definition)
    receipt = replace(receipt, operational_status=OperationalStatus.FAILED, reason_codes=("exposed-scientific-extraction-failed",))
    summary = replace(evidence.trace.segments[0], disposition="TECHNICAL_FAILURE", error_type="ExposedExtractionError", error_message="exposed missing interpretation",
        native_receipt=ss.identity(receipt, "receipt_id"), native_times_s=(), start_receivers=(), end_receivers=(),
        full_state=None, requested_initial=None, actual_initial=None, initial_derivative=None, actual_terminal=None, terminal_derivative=None)
    frame = replace(frame, native_receipt=receipt, full_state=None, requested_initial=None, actual_initial=None,
        initial_derivative=None, actual_terminal=None, terminal_derivative=None)
    trace = replace(evidence.trace, disposition="TECHNICAL_FAILURE", error_type=summary.error_type, error_message=summary.error_message, segments=(summary,))
    main = _receipt(tmp_path / "failure-main", (trace, evidence.protocol, evidence.source_assignment, evidence.layout))
    evidence = replace(evidence, trace=trace, native_receipt=main, requested_initial=None, actual_initial=None,
        initial_derivative=None, actual_terminal=None, terminal_derivative=None)
    result = _compare((evidence, (frame,)), right)
    assert result.disposition is A.UNEVALUABLE and result.declared_segment_counts == (1, 1)
    assert result.original_retained_native_knots == (0, 2) and result.actual_terminal_clocks[0] is None
    assert result.segment_assessments[0][0].retained_raw_state_elements == 348
    assert result.segment_assessments[0][0].retained_raw_bytes > 0
    assert "actual-full-state-clock-domain-unavailable" in result.reason_codes


def test_distinct_original_request_publisher_cannot_replace_actual_successor_chain(prepared, tmp_path):
    left = _stream(prepared, tmp_path / "left")
    evidence, frames = _stream(prepared, tmp_path / "right", horizon=30, segments=2)
    last = frames[-1]
    copied = _receipt(tmp_path / "copied-request", (last.request,))
    definition = replace(last.definition, input_materialization_ids=(copied.output_materializations[0].materialization_id,))
    records = (*tuple(value for name, value in last.records.items() if name != "request" and value is not None), last.next_request)
    receipt = _receipt(tmp_path / "copied-actual-return", records, inputs=definition.input_materialization_ids, definition=definition)
    frame = replace(last, definition=definition, request_receipt=copied, native_receipt=receipt)
    summary = replace(evidence.trace.segments[-1], native_definition=definition.identity, native_receipt=ss.identity(receipt, "receipt_id"))
    trace = replace(evidence.trace, segments=(evidence.trace.segments[0], summary))
    main_records = (trace, evidence.protocol, evidence.source_assignment, evidence.layout, evidence.requested_initial,
        evidence.actual_initial, evidence.initial_derivative, evidence.actual_terminal, evidence.terminal_derivative)
    main = _receipt(tmp_path / "copied-main", main_records)
    evidence = replace(evidence, trace=trace, native_receipt=main)
    with pytest.raises(ValueError, match="successor request-carrier receipt chain"):
        _compare(left, (evidence, (frames[0], frame)))


def test_actual_hybrid_and_terminal_clocks_are_not_phase_aligned(selected, tmp_path, monkeypatch):
    operands = []
    for horizon in (60, 30):
        (tmp_path / str(horizon)).mkdir()
        custody = native_custody.__wrapped__(tmp_path / str(horizon), selected, N(param=D(horizon)))
        exposed_backend(custody, monkeypatch)
        result = acquire(custody)
        evidence = se.evidence_from_result(custody.config, result)
        frames = tuple(es.relay_segments(custody.store, custody.definition, result.inspection, result.trace, result.protocol))
        operands.append((evidence, frames))
    result = _compare(*operands)
    assert result.declared_segment_counts == (3, 3) and result.declared_transition_counts == (1, 1)
    assert result.disposition is not A.SATISFIED
    issues = {row.code: row for row in result.coverage_issues}
    assert "one-sided-hybrid-event-control-unqualified" in issues
    assert "actual-terminal-clocks-differ" in issues
    roots = issues["actual-hybrid-root-clocks-differ"]
    assert roots.exact_start == (181, 4) and roots.exact_end == (361, 4)
    assert any("actual-hybrid-regimes-differ" in row.reason_codes[0] or any("actual-hybrid-regimes-differ" in reason for reason in row.reason_codes)
        for row in result.intervals if row.reason_codes)


def test_complete_stream_control_import_stays_outside_native_and_numeric_engines():
    result = subprocess.run((sys.executable, "-c", "import sys; import empirical_lawhood.adapters.methods.battery_refined_inquiry.segmented_fidelity_stream; assert 'pybamm' not in sys.modules; assert 'numpy' not in sys.modules"),
        capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
