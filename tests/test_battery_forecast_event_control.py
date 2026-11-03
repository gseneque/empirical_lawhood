# SPDX-License-Identifier: MPL-2.0
"""Exposed one-sided/current/terminal controls with exact custody; no solver."""

from dataclasses import replace
from decimal import Decimal as D
from fractions import Fraction
import json
import struct

import pytest

from empirical_lawhood.adapters.methods.battery_refined_inquiry import forecast_event_control as event
from empirical_lawhood.adapters.methods.battery_refined_inquiry import forecast_state_orchestration as orchestration
from empirical_lawhood.adapters.methods.battery_refined_inquiry import forecast_step_control as step
from empirical_lawhood.adapters.methods.battery_refined_inquiry import lossless_evidence_stream as stream
from empirical_lawhood.adapters.methods.battery_refined_inquiry import lossless_segment_records as lossless
from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_contracts as contracts
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.kernel.status import OperationalStatus
from tests.test_battery_forecast_clock_control import lossless_call, multiple_call_observation
from tests.test_battery_forecast_state_control import selected as selected_fixture
from tests.test_battery_forecast_step_control import failed_assignment_evidence, witness
from tests.test_battery_lossless_segment_integration import Emitter, encoded_original, selected_preparation
from tests.test_battery_forecast_state_orchestration import port, failed_observation
from tests.test_battery_segmented_fidelity import _receipt, prepared as prepared_fixture
from tests.test_battery_segmented_fidelity_stream import _stream


def tier_observation(prepared, selected, directory, temporary_file, *, damage=None, kind="tier"):
    """Entire declared toy event denominator, using fresh exposed custody only."""
    original, originals = _stream(prepared, directory / "old", horizon=30, segments=3 if kind == "cycle" else 2)
    config, layout = original.trace.config, original.layout
    assignment = replace(witness(selected[2].native_policy, config)[2], assignment_id="assignment.exposed.tier-control")
    roles = {row.role: row for row in layout.blocks}
    threshold = event.TIER_TEMPERATURE + config.localization_epsilon_k
    states = []
    for index, frame in enumerate(originals):
        regimes = "LOW" if index == 0 or kind == "constant" or kind == "cycle" and index == 2 else "HIGH"
        start = list(frame.actual_initial.binary64_hex)
        end = list(frame.actual_terminal.binary64_hex)
        for row, before, after in ((roles["temperature"], config.initial_temperature_k if index == 0 or kind == "constant" else threshold,
                config.initial_temperature_k if kind == "constant" else threshold if index == 0 else threshold + D(".01")),
                (roles["current"], D("-.5") if kind == "constant" or index else D(0), D("-.5") if kind == "constant" or index else D(0)),
                (roles["discharge-capacity"], -D(".5") * D(index * 30) / D(3600) if kind == "constant" and index else D(0),
                    -D(".5") * D((index + 1) * 30) / D(3600) if kind == "constant" else D(0) if index == 0 else -D(".5") * D(30) / D(3600))):
            start[row.start] = float((before - row.reference) / row.scale).hex()
            end[row.start] = float((after - row.reference) / row.scale).hex()
        if kind == "cycle" and index:
            row = roles["temperature"]
            before = threshold if index == 1 else event.TIER_TEMPERATURE + config.localization_epsilon_k / D(2)
            after = event.TIER_TEMPERATURE + config.localization_epsilon_k / (D(2) if index == 1 else D("1.5"))
            start[row.start] = float((before - row.reference) / row.scale).hex()
            end[row.start] = float((after - row.reference) / row.scale).hex()
            row = roles["discharge-capacity"]
            for bits, value in ((start, -D(".5") * D((index - 1) * 30) / D(3600) if index > 1 else D(0)),
                    (end, -D(".5") * D(index * 30) / D(3600))):
                bits[row.start] = float((value - row.reference) / row.scale).hex()
        if index and damage == "differential":
            start[2] = float(float.fromhex(start[2]) + .01).hex()
        if not index and damage == "root":
            row = roles["temperature"]
            end[row.start] = float((threshold + D(".01") - row.reference) / row.scale).hex()
        derivative = [float(0).hex()] * (layout.differential_count + layout.algebraic_count)
        if index:
            derivative[-1] = float(.25).hex()
        requested = start if not index else list(states[index - 1]["actual_terminal"].binary64_hex)
        values = {}
        for name, bits in (("requested_initial", requested), ("actual_initial", start), ("actual_terminal", end),
                ("initial_derivative", derivative), ("terminal_derivative", derivative)):
            original_state = getattr(frame, name)
            values[name] = replace(original_state, scaled_values=tuple(D(str(float.fromhex(value))) for value in bits), binary64_hex=tuple(bits))
        if damage == "requested" and index:
            bits = list(values["requested_initial"].binary64_hex)
            bits[2] = float(float.fromhex(bits[2]) + .01).hex()
            values["requested_initial"] = replace(values["requested_initial"],
                scaled_values=tuple(D(str(float.fromhex(value))) for value in bits), binary64_hex=tuple(bits))
        states.append(dict(regime=regimes, start=tuple(start), end=tuple(end), derivative=tuple(derivative), **values))
    requests = []
    for index, frame in enumerate(originals):
        document = json.loads(frame.request.primitive_json)
        document.update(regime=states[index]["regime"], inputs=event._source_inputs(config, states[index]["regime"]),
            solver=json.loads(assignment.actual_solver_json),
            previous_terminal=None if not index else event.science._primitive_identity(states[index - 1]["actual_terminal"], "observation_id"))
        if not index and damage in ("threshold", "direction"):
            key = "Inquiry tier threshold [K]" if damage == "threshold" else "Inquiry tier direction"
            document["inputs"][key] = {"binary64": float(threshold + D(".01") if damage == "threshold" else 1).hex()}
        requests.append(replace(frame.request, primitive_json=canonical_json_bytes(document).decode()))
    carrier = _receipt(directory / "first-request", (requests[0],))
    converted, summaries = [], []
    for index, (frame, request, old_summary, data) in enumerate(zip(originals, requests, original.trace.segments, states, strict=True)):
        returned = replace(frame.returned, request=request.identity)
        state_bits = tuple(value for pair in zip(data["start"], data["end"], strict=True) for value in pair)
        derivatives = tuple(value for value in data["derivative"] for _ in range(2))
        def array(bits):
            return replace(frame.raw_return.state_blocks[0], bytes_hex=b"".join(struct.pack("<d", float.fromhex(value)) for value in bits).hex())
        raw = replace(frame.raw_return, request=request.identity, returned=step.identity(returned, "return_id"),
            state_blocks=(array(state_bits),), derivative_blocks=(array(derivatives),))
        termination = "event: " + event.TIER_EVENT if (not index and kind != "constant"
            or kind == "cycle" and index == 1) else "final time"
        full = replace(frame.full_state, request=request.identity, returned=step.identity(returned, "return_id"),
            raw_return=step.identity(raw, "raw_id"),
            blocks=(replace(frame.full_state.blocks[0], state_binary64=state_bits, derivative_binary64=derivatives),),
            returned_inputs_json=canonical_json_bytes((event._source_inputs(config, data["regime"]),)).decode(), actual_termination=termination)
        logical = next(row for row in carrier.output_logical_artifacts if row.content_sha256 == request.fingerprint())
        materialized = next(row for row in carrier.output_materializations if row.logical_artifact_id == logical.logical_artifact_id)
        definition = replace(frame.definition, configuration=request.identity, input_materialization_ids=(materialized.materialization_id,),
            sources=tuple(sorted(assignment.control.sources, key=lambda row: row.object_id)))
        successor = (replace(request, request_id=request.request_id + ".end.exposed-uncertain", kind="end-of-chain",
            primitive_json=canonical_json_bytes({"actual_segment_calls": 1}).decode()) if kind == "unfinished" else
            requests[index + 1] if index + 1 < len(requests) else frame.next_request)
        observed = tuple(data[name] for name in ("requested_initial", "actual_initial", "initial_derivative", "actual_terminal", "terminal_derivative"))
        receipt = _receipt(directory / ("matched-" + str(index)), (returned, raw, full, *observed, successor),
            inputs=definition.input_materialization_ids, definition=definition)
        def receivers(bits):
            physical = {role: D(str(float(event._physical(row, bits[row.start])))) for role, row in roles.items()
                if role in ("current", "temperature", "discharge-capacity")}
            return physical["current"], D("4.2"), physical["temperature"], physical["discharge-capacity"]
        summary = replace(old_summary, regime=data["regime"], termination=termination,
            start_receivers=receivers(data["start"]), end_receivers=receivers(data["end"]), request=request.identity,
            returned=step.identity(returned, "return_id"), raw_return=step.identity(raw, "raw_id"), full_state=step.identity(full, "segment_id"),
            native_definition=definition.identity, native_receipt=step.identity(receipt, "receipt_id"),
            **{name: step.identity(data[name], "observation_id") for name in
                ("requested_initial", "actual_initial", "initial_derivative", "actual_terminal", "terminal_derivative")})
        original_frame = event.consumer.old.SegmentEvidenceFrame(index + 1, definition, carrier, receipt, request,
            returned, successor, raw, full, *observed)
        operand = event.state.local.FullStateOperand(config, original.protocol, layout, summary, original_frame)
        current = lossless_call(operand, directory / ("lossless-" + str(index)), temporary_file)
        converted.append((current.frame.metadata, raw, full))
        carrier = current.frame.native_receipt
        summaries.append(current.summary)
        current.frame.close()
        if kind == "unfinished":
            break
    transitions = () if kind in ("constant", "unfinished") else (contracts.SegmentTransition("transition.exposed.tier", 1, 1, 2, "LOW", "HIGH", D(30), threshold,
        config.localization_epsilon_k, summaries[0].actual_terminal, summaries[1].requested_initial, summaries[1].actual_initial,
        summaries[0].end_receivers, summaries[1].start_receivers),)
    if kind == "cycle":
        transitions += (contracts.SegmentTransition("transition.exposed.cooling", 2, 2, 3, "HIGH", "LOW", D(60),
            event.TIER_TEMPERATURE + config.localization_epsilon_k / D(2), config.localization_epsilon_k,
            summaries[1].actual_terminal, summaries[2].requested_initial, summaries[2].actual_initial,
            summaries[1].end_receivers, summaries[2].start_receivers),)
    trace = replace(original.trace, segments=tuple(summaries), transitions=transitions,
        backend_solve_calls=len(summaries))
    if kind == "unfinished":
        trace = replace(trace, disposition="TECHNICAL_FAILURE", error_type="ExposedPostTierStop", error_message="One known tier return; successor not entered.",
            termination="ExposedPostTierStop", times_s=(D(0), D(30)))
    template = failed_assignment_evidence((selected[0], selected[1], selected[2].native_policy), config, directory / "template")
    completion = replace(template.original_native_completion, operational_status=OperationalStatus.SUCCEEDED,
        output_ids=("forecast-step-assignment", "forecast-step-policy"), omitted_output_ids=(), reason_codes=())
    if kind == "unfinished":
        completion = replace(completion, operational_status=OperationalStatus.FAILED, reason_codes=("exposed-post-tier-stop",))
    last = len(summaries) - 1
    records = (trace, original.protocol, original.source_assignment, layout, states[0]["requested_initial"], states[0]["actual_initial"],
        states[0]["initial_derivative"], states[last]["actual_terminal"], states[last]["terminal_derivative"])
    receipt = _receipt(directory / "assigned-main", (*records, selected[2].native_policy, assignment, completion),
        inputs=template.original_native_definition.input_materialization_ids, definition=template.original_native_definition)
    if kind == "unfinished":
        receipt = replace(receipt, operational_status=OperationalStatus.FAILED, reason_codes=completion.reason_codes)
    evidence = replace(original, **dict(zip(("trace", "protocol", "source_assignment", "layout", "requested_initial", "actual_initial",
        "initial_derivative", "actual_terminal", "terminal_derivative"), records, strict=True)), native_receipt=receipt)
    metadata = step.ForecastStepEvidence("evidence.assigned.exposed.tier", selected[2].native_policy,
        assignment, template.original_native_definition, completion, receipt)
    emitter = Emitter()
    sequence = stream.emit_header(emitter, "segments", event.consumer.old.SegmentStreamHeader(
        step.identity(trace, "trace_id"), step.identity(original.protocol, "protocol_id"), len(summaries)))
    for frame, raw, full in converted:
        index, _, sources = encoded_original(raw, full)
        sequence = stream.emit_frame(emitter, "segments", frame, lossless.encode_raw_segment(index, sources), sequence)
    payload = b"".join(emitter.lines)
    summary = event.consumer.assess_trace(config, evidence, port(payload), temporary_file=temporary_file)
    return orchestration.ForecastObservation(evidence, metadata, summary), payload


@pytest.fixture(scope="module")
def selected_operands(tmp_path_factory):
    selected = selected_fixture.__wrapped__()
    prepared = selected_preparation(prepared_fixture.__wrapped__(), (selected[0], selected[1], selected[2].native_policy))
    directory = tmp_path_factory.mktemp("forecast-event-controls")
    temporary_file = stream.selected_temporary_files(directory)
    observations = []
    for label, damage in (("tier", None), ("differential", "differential"), ("requested", "requested"),
            ("constant", None), ("unfinished", None), ("threshold", "threshold"), ("direction", "direction"), ("root", "root"), ("cycle", None)):
        observed, payload = tier_observation(prepared, selected, directory / label, temporary_file, damage=damage,
            kind=label if label in ("constant", "unfinished", "cycle") else "tier")
        result = event.assess_events(selected[2], selected[1], observed, port(payload), temporary_file=temporary_file)
        observations.append((label, observed, payload, result))
    left, left_payload = multiple_call_observation(prepared, selected, directory / "constant60", temporary_file, horizon=60, segments=1)
    right, right_payload = multiple_call_observation(prepared, selected, directory / "constant30", temporary_file, horizon=30, segments=1)
    pair = orchestration.assess_pair(selected[2], selected[1], left, right,
        port(left_payload), port(right_payload), temporary_file=temporary_file)
    constant = tuple(event.assess_events(selected[2], selected[1], observed, port(payload), temporary_file=temporary_file)
        for observed, payload in ((left, left_payload), (right, right_payload)))
    terminal = event.assess_terminals(selected[2], pair, *constant)
    return selected, observations, constant, terminal, temporary_file


def test_genuine_two_call_tier_preserves_complete_state_and_expected_jumps(selected_operands):
    result = selected_operands[1][0][3]
    assert result.disposition is A.SATISFIED, result.reason_codes
    assert len(result.complete_calls) == 2 and result.declared_tier_returns == (1,)
    tier, = result.complete_tier_assessments
    assert tier.disposition is A.SATISFIED
    assert tier.differential_continuity.checked_components == 173 and not tier.differential_continuity.failed_components
    assert tier.algebraic_jump.checked_components == 1 and tier.algebraic_jump.failed_components == (0,)
    assert tier.returned_derivative_jump.checked_components == 174 and tier.returned_derivative_jump.failed_components == (173,)
    assert tier.complete_requested_state_unchanged and tier.root_source_and_direction_match
    assert all(row.source_inputs_match and row.native_knots == 2 for row in result.complete_calls)
    assert sum(Fraction(*row.integrated_charge_ah) for row in result.complete_calls) > 0
    assert decode_canonical_bytes(result.canonical_bytes(), type(result), maximum_bytes=None) == result
    assert not result.model_admission


@pytest.mark.parametrize("label", ("differential", "requested", "threshold", "direction", "root"))
def test_actual_full_continuation_damage_is_falsified_with_all_calls(selected_operands, label):
    result = next(row[3] for row in selected_operands[1] if row[0] == label)
    assert result.disposition is A.FALSIFIED and len(result.complete_calls) == 2
    if label not in ("threshold", "direction"):
        assert result.complete_tier_assessments[0].disposition is A.FALSIFIED


def test_genuine_last_tier_return_without_successor_stays_unevaluable(selected_operands):
    result = next(row[3] for row in selected_operands[1] if row[0] == "unfinished")
    assert result.disposition is A.UNEVALUABLE and len(result.complete_calls) == 1
    assert result.declared_tier_returns == (1,)
    tier, = result.complete_tier_assessments
    assert tier.disposition is A.UNEVALUABLE and tier.original_transition is None
    assert tier.differential_continuity is tier.algebraic_jump is tier.returned_derivative_jump is None


def test_both_actual_source_directions_preserve_complete_one_sided_cycle(selected_operands):
    result = next(row[3] for row in selected_operands[1] if row[0] == "cycle")
    assert result.disposition is A.SATISFIED, result.reason_codes
    assert len(result.complete_calls) == 3 and result.declared_tier_returns == (1, 2)
    assert tuple(row.original_transition.to_regime for row in result.complete_tier_assessments) == ("HIGH", "LOW")
    assert all(row.root_source_and_direction_match and row.disposition is A.SATISFIED for row in result.complete_tier_assessments)
    assert all(row.differential_continuity.checked_components == 173 and not row.differential_continuity.failed_components
        for row in result.complete_tier_assessments)
    assert all(row.source_inputs_match and row.native_temperature_regime_match for row in result.complete_calls)


def test_complete_no_transition_and_actual_unequal_terminal_suffix_remain_separate(selected_operands):
    _, _, constant, terminal, _ = selected_operands
    assert all(row.disposition is A.UNEVALUABLE and not row.declared_tier_returns and not row.complete_tier_assessments for row in constant)
    assert all("independent-native-knot-current-capacity-disagreement" in row.reason_codes for row in constant)
    consistent = next(row[3] for row in selected_operands[1] if row[0] == "constant")
    assert consistent.disposition is A.SATISFIED and not consistent.declared_tier_returns and not consistent.complete_tier_assessments
    assert terminal.unpaired_actual_suffix == ((30, 1), (60, 1))
    assert terminal.terminal_clock_difference_s == (30, 1)
    assert terminal.disposition is A.FALSIFIED
    assert "independent-original-terminal-receiver-integrity-falsified" in terminal.reason_codes
    assert terminal.whole_global_state_coverage is A.UNEVALUABLE and not terminal.model_admission
    assert decode_canonical_bytes(terminal.canonical_bytes(), type(terminal), maximum_bytes=None) == terminal


@pytest.mark.parametrize("damage", ("calls", "events", "source", "threshold", "rows", "promote"))
def test_complete_event_call_source_threshold_and_negative_denominators_cannot_be_bypassed(selected_operands, damage):
    result = selected_operands[1][0][3]
    with pytest.raises(ValueError):
        if damage == "calls":
            replace(result, complete_calls=result.complete_calls[:-1])
        elif damage == "events":
            replace(result, complete_tier_assessments=())
        elif damage == "source":
            replace(result, complete_calls=(replace(result.complete_calls[0], source_inputs_match=False), result.complete_calls[1]))
        elif damage == "threshold":
            replace(result, complete_tier_assessments=(replace(result.complete_tier_assessments[0], root_source_and_direction_match=False),))
        elif damage == "rows":
            tier = result.complete_tier_assessments[0]
            replace(result, complete_tier_assessments=(replace(tier, differential_continuity=replace(tier.differential_continuity, checked_components=172)),))
        else:
            replace(result, model_admission=True)


def test_missing_terminal_suffix_cannot_be_hidden_by_favourable_endpoint_label(selected_operands):
    result = selected_operands[3]
    for change in (dict(unpaired_actual_suffix=None), dict(whole_global_state_coverage=A.SATISFIED),
            dict(disposition=A.SATISFIED, reason_codes=()), dict(model_admission=True)):
        with pytest.raises(ValueError):
            replace(result, **change)


def test_zero_call_native_failure_has_complete_uncertain_census(tmp_path):
    selected = selected_fixture.__wrapped__()
    prepared = selected_preparation(prepared_fixture.__wrapped__(), (selected[0], selected[1], selected[2].native_policy))
    observed, payload = failed_observation(selected, prepared[0], prepared[1], tmp_path / "failed")
    result = event.assess_events(selected[2], selected[1], observed, port(payload), temporary_file=lambda: None)
    assert result.disposition is A.UNEVALUABLE and result.complete_calls == result.complete_tier_assessments == ()
    assert decode_canonical_bytes(result.canonical_bytes(), type(result), maximum_bytes=None) == result
