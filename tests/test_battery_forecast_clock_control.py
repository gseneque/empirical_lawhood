# SPDX-License-Identifier: MPL-2.0
"""Actual source20 assignment/array clock controls; no native acquisition."""

from dataclasses import replace
from decimal import Decimal as D
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path

import pytest

from empirical_lawhood.adapters.methods.battery_refined_inquiry import forecast_clock_control as clock
from empirical_lawhood.adapters.methods.battery_refined_inquiry import forecast_step_control as step
from empirical_lawhood.adapters.methods.battery_refined_inquiry import forecast_state_orchestration as orchestration
from empirical_lawhood.adapters.methods.battery_refined_inquiry import lossless_evidence_stream as stream
from empirical_lawhood.adapters.methods.battery_refined_inquiry import lossless_segment_records as lossless
from empirical_lawhood.adapters.methods.battery_refined_inquiry import lossless_segment_native as storage
from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_fidelity_stream as paired
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactLineageParent, ArtifactProfile, ArtifactStreamWriteRequest
from tests.runtime_platform.test_native_subwork import _plane
from tests.test_battery_forecast_state_execution import original_pairs as original_pairs_fixture
from tests.test_battery_forecast_state_orchestration import failed_observation, port
from tests.test_battery_forecast_state_control import selected as selected_fixture
from tests.test_battery_forecast_step_control import config as config_fixture, failed_assignment_evidence, witness
from tests.test_battery_lossless_segment_integration import Emitter, encoded_original, selected_preparation
from tests.test_battery_segmented_fidelity import _receipt, prepared as prepared_fixture
from tests.test_battery_segmented_fidelity_stream import _stream

original_pairs = original_pairs_fixture


def lossless_call(original, directory, temporary_file):
    """Preserve the actual selected ordinal through original-to-lossless fixtures."""
    index, full, sources = encoded_original(original.frame.raw_return, original.frame.full_state)
    definition = replace(original.frame.definition, outputs=storage.segment_outputs())
    states = tuple(getattr(original.frame, name) for name in
        ("requested_initial", "actual_initial", "initial_derivative", "actual_terminal", "terminal_derivative"))
    receipt = _receipt(directory, (original.frame.returned, full, *states, original.frame.next_request),
        inputs=definition.input_materialization_ids, definition=definition)
    plane = _plane(directory)
    lines = tuple(lossless.encode_raw_segment(index, sources))
    parent = ArtifactLineageParent(definition.identity, VisibilityCeiling.DEVELOPMENT_ONLY, OutcomeAccess.DEVELOPMENT_VISIBLE)
    written = plane.write_stream(ArtifactStreamWriteRequest("output.raw", "outputs/raw.jsonl", lossless.RawSegmentStreamLine.SCHEMA,
        ArtifactProfile.JSONL_CHUNKS, "application/x-ndjson", "task.exposed", "outputs", iter(lines),
        maximum_bytes=sum(map(len, lines)), maximum_chunk_bytes=max(map(len, lines)),
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, parent_visibility_ceilings=(parent.visibility_ceiling,),
        outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE, lineage_parents=(parent,)))
    receipt = replace(receipt,
        output_materializations=tuple(sorted((*receipt.output_materializations, written.materialization), key=lambda row: row.materialization_id)),
        output_logical_artifacts=tuple(sorted((*receipt.output_logical_artifacts, written.logical), key=lambda row: row.logical_artifact_id)))
    summary = replace(original.summary, native_definition=definition.identity, native_receipt=step.identity(receipt, "receipt_id"))
    metadata = stream.LosslessSegmentMetadata(summary.segment_index, definition, original.frame.request_receipt, receipt,
        original.frame.request, original.frame.returned, original.frame.next_request, index,
        written.logical.content_sha256, written.materialization.size_bytes, full, *states)
    return replace(original, summary=summary, frame=stream.decoded_frame(metadata, iter(lines), temporary_file))


def multiple_call_observation(prepared, selected, directory, temporary_file, *, horizon, segments, derivatives=True):
    """Expose new authentic receipts for every call and actual selected request."""
    original, frames = _stream(prepared, directory / "old", horizon=horizon, segments=segments, derivatives=derivatives)
    config = original.trace.config
    assignment = replace(witness(selected[2].native_policy, config)[2], assignment_id="assignment.exposed.clock." + str(horizon))
    requests = []
    for frame in frames:
        document = json.loads(frame.request.primitive_json)
        document["solver"] = json.loads(assignment.actual_solver_json)
        requests.append(replace(frame.request, primitive_json=canonical_json_bytes(document).decode()))
    summaries, converted = [], []
    carrier = _receipt(directory / "first-request", (requests[0],))
    for index, (frame, request, summary) in enumerate(zip(frames, requests, original.trace.segments, strict=True)):
        returned = replace(frame.returned, request=request.identity)
        raw = replace(frame.raw_return, request=request.identity, returned=step.identity(returned, "return_id"))
        full = replace(frame.full_state, request=request.identity, returned=step.identity(returned, "return_id"),
            raw_return=step.identity(raw, "raw_id"))
        matched = next(row for row in carrier.output_logical_artifacts if row.content_sha256 == request.fingerprint())
        materialized = next(row for row in carrier.output_materializations if row.logical_artifact_id == matched.logical_artifact_id)
        definition = replace(frame.definition, configuration=request.identity, input_materialization_ids=(materialized.materialization_id,),
            sources=tuple(sorted(assignment.control.sources, key=lambda row: row.object_id)))
        successor = requests[index + 1] if index + 1 < segments else frame.next_request
        states = tuple(getattr(frame, name) for name in
            ("requested_initial", "actual_initial", "initial_derivative", "actual_terminal", "terminal_derivative"))
        receipt = _receipt(directory / ("matched-" + str(index)), (returned, raw, full, *states, successor),
            inputs=definition.input_materialization_ids, definition=definition)
        summary = replace(summary, request=request.identity, returned=step.identity(returned, "return_id"),
            raw_return=step.identity(raw, "raw_id"), full_state=step.identity(full, "segment_id"),
            native_definition=definition.identity, native_receipt=step.identity(receipt, "receipt_id"))
        old = clock.consumer.old.SegmentEvidenceFrame(index + 1, definition, carrier, receipt, request, returned,
            successor, raw, full, *states)
        operand = clock.state.local.FullStateOperand(config, original.protocol, original.layout, summary, old)
        current = lossless_call(operand, directory / ("lossless-" + str(index)), temporary_file)
        converted.append((current.frame.metadata, raw, full))
        carrier = current.frame.native_receipt
        summaries.append(current.summary)
        current.frame.close()
    trace = replace(original.trace, segments=tuple(summaries))
    template = failed_assignment_evidence((selected[0], selected[1], selected[2].native_policy), config, directory / "template")
    completion = replace(template.original_native_completion, operational_status=OperationalStatus.SUCCEEDED,
        output_ids=("forecast-step-assignment", "forecast-step-policy"), omitted_output_ids=(), reason_codes=())
    records = (trace, original.protocol, original.source_assignment, original.layout, original.requested_initial,
        original.actual_initial, original.initial_derivative, original.actual_terminal, original.terminal_derivative)
    receipt = _receipt(directory / "assigned-main", (*records, selected[2].native_policy, assignment, completion),
        inputs=template.original_native_definition.input_materialization_ids, definition=template.original_native_definition)
    evidence = replace(original, trace=trace, native_receipt=receipt)
    metadata = step.ForecastStepEvidence("evidence.assigned.clock." + str(horizon), selected[2].native_policy,
        assignment, template.original_native_definition, completion, receipt)
    emitter = Emitter()
    sequence = stream.emit_header(emitter, "segments", clock.consumer.old.SegmentStreamHeader(
        step.identity(trace, "trace_id"), step.identity(original.protocol, "protocol_id"), segments))
    for frame, raw, full in converted:
        index, _, sources = encoded_original(raw, full)
        sequence = stream.emit_frame(emitter, "segments", frame,
            lossless.encode_raw_segment(index, sources), sequence)
    payload = b"".join(emitter.lines)
    summary = clock.consumer.assess_trace(config, evidence, port(payload), temporary_file=temporary_file)
    return orchestration.ForecastObservation(evidence, metadata, summary), payload


@pytest.fixture(scope="module")
def restarted_pair(tmp_path_factory):
    selected = selected_fixture.__wrapped__()
    prepared = selected_preparation(prepared_fixture.__wrapped__(), (selected[0], selected[1], selected[2].native_policy))
    directory = tmp_path_factory.mktemp("forecast-clock-restarts")
    temporary_file = stream.selected_temporary_files(directory)
    left, left_payload = multiple_call_observation(prepared, selected, directory / "left", temporary_file, horizon=60, segments=1)
    right, right_payload = multiple_call_observation(prepared, selected, directory / "right", temporary_file, horizon=30, segments=2)
    pair = orchestration.assess_pair(selected[2], selected[1], left, right,
        port(left_payload), port(right_payload), temporary_file=temporary_file)
    policy = clock.ForecastClockPolicy("policy.exposed.source20-restarts", selected[2],
        sha256(Path(clock.clock.__file__).read_bytes()).hexdigest(),
        dict(left.evidence.trace.config.source.source_members)["solvers/base_solver.py"])
    result = clock.assess_clock(policy, selected[1], pair, left, right,
        port(left_payload), port(right_payload), temporary_file=temporary_file)
    return result


def test_genuine_source20_restarts_keep_original_real_gaps_and_exact174_boundary(restarted_pair):
    result = restarted_pair
    assert result.original_pair.disposition is A.UNEVALUABLE and len(result.original_pair.coverage_issues) == 2
    assert result.disposition is A.SATISFIED and result.reason_codes == ()
    assert tuple(map(len, result.complete_call_censuses)) == (1, 2)
    boundary, = result.boundaries
    assert boundary.requested_full_state_unchanged and boundary.actual_model_and_scalar_regime_unchanged
    assert boundary.state_continuity.checked_components == boundary.returned_derivative_continuity.checked_components == 174
    assert boundary.exact_start == (30, 1)
    assert clock.clock._adjacent(Fraction(*boundary.exact_start), Fraction(*boundary.exact_end))
    assert decode_canonical_bytes(result.canonical_bytes(), type(result), maximum_bytes=None) == result


@pytest.mark.parametrize("damage", ("missing-boundary", "state-row", "derivative-row", "regime", "changed-regime-jump", "request"))
def test_genuine_complete_boundary_countercases_preserve_negative_or_uncertain(restarted_pair, damage):
    result = restarted_pair
    boundary, = result.boundaries
    boundaries = result.boundaries
    if damage == "missing-boundary":
        boundaries = ()
    elif damage in ("state-row", "derivative-row", "changed-regime-jump"):
        left = (float(0).hex(),) * 174
        metric = clock.clock._metric(left, tuple(float(1e-3 if i == 173 else 0).hex() for i in range(174)), 174, result.policy)
        boundary = replace(boundary, **{("state_continuity" if damage == "state-row" else "returned_derivative_continuity"): metric})
        if damage == "changed-regime-jump":
            boundary = replace(boundary, actual_model_and_scalar_regime_unchanged=False, state_continuity=metric)
        boundaries = (boundary,)
    else:
        boundaries = (replace(boundary, **{("actual_model_and_scalar_regime_unchanged" if damage == "regime"
            else "requested_full_state_unchanged"): False}),)
    with pytest.raises(ValueError):
        replace(result, boundaries=boundaries)
    disposition, reasons = clock._reasons(result.original_pair, result.complete_call_censuses, boundaries)
    changed = replace(result, boundaries=boundaries, disposition=disposition, reason_codes=reasons)
    assert changed.disposition is (A.UNEVALUABLE if damage in ("missing-boundary", "regime", "changed-regime-jump") else A.FALSIFIED)
    if damage == "changed-regime-jump":
        assert changed.boundaries[0].state_continuity.failed_components == (173,)
        assert changed.boundaries[0].returned_derivative_continuity.failed_components == (173,)
        assert "actual-model-or-regime-change-unassessed" in changed.reason_codes


@pytest.mark.parametrize("missing", ("all-calls", "returned-derivatives"))
def test_genuine_missing_operands_retain_complete_zero_or_three_call_denominator(tmp_path, missing):
    selected = selected_fixture.__wrapped__()
    prepared = selected_preparation(prepared_fixture.__wrapped__(), (selected[0], selected[1], selected[2].native_policy))
    temporary_file = stream.selected_temporary_files(tmp_path)
    if missing == "all-calls":
        config = config_fixture.__wrapped__((selected[0], selected[1], selected[2].native_policy))
        left, left_payload = failed_observation(selected, config, prepared[1], tmp_path / "left-failed")
        right_config = replace(config, config_id=config.config_id + ".half",
            method=replace(config.method, method_id=config.method.method_id + ".half", maximum_segment_horizon_s=D(30)))
        right, right_payload = failed_observation(selected, right_config, prepared[1], tmp_path / "right-failed")
    else:
        left, left_payload = multiple_call_observation(prepared, selected, tmp_path / "left", temporary_file,
            horizon=60, segments=1, derivatives=False)
        right, right_payload = multiple_call_observation(prepared, selected, tmp_path / "right", temporary_file,
            horizon=30, segments=2, derivatives=False)
    pair = orchestration.assess_pair(selected[2], selected[1], left, right,
        port(left_payload), port(right_payload), temporary_file=temporary_file)
    policy = clock.ForecastClockPolicy("policy.exposed.missing-clock-operand", selected[2],
        sha256(Path(clock.clock.__file__).read_bytes()).hexdigest(),
        dict(left.evidence.trace.config.source.source_members)["solvers/base_solver.py"])
    result = clock.assess_clock(policy, selected[1], pair, left, right,
        port(left_payload), port(right_payload), temporary_file=temporary_file)
    assert result.disposition is A.UNEVALUABLE
    assert tuple(map(len, result.complete_call_censuses)) == ((0, 0) if missing == "all-calls" else (1, 2))
    if missing == "returned-derivatives":
        assert all(row.returned_clock is not None and row.reason_codes == (clock.MISSING,)
            for side in result.complete_call_censuses for row in side)
        assert "original-one-sided-boundary-census-unavailable" in result.reason_codes and result.boundaries == ()
    assert decode_canonical_bytes(result.canonical_bytes(), type(result), maximum_bytes=None) == result


@pytest.fixture(scope="module")
def clock_pairs(original_pairs, tmp_path_factory):
    selected, originals = original_pairs
    temporary_file = stream.selected_temporary_files(tmp_path_factory.mktemp("forecast-clock-arrays"))
    policy = clock.ForecastClockPolicy("policy.exposed.source20-clock", selected[2],
        sha256(Path(clock.clock.__file__).read_bytes()).hexdigest(),
        dict(originals[0][1].evidence.trace.config.source.source_members)["solvers/base_solver.py"])
    rows = []
    for label, left, right, left_payload, right_payload in originals:
        original = orchestration.assess_pair(selected[2], selected[1], left, right,
            port(left_payload), port(right_payload), temporary_file=temporary_file)
        result = clock.assess_clock(policy, selected[1], original, left, right,
            port(left_payload), port(right_payload), temporary_file=temporary_file)
        rows.append((label, original, result, left, right, left_payload, right_payload))
    return selected, policy, tuple(rows), temporary_file


def test_actual_source20_fixed_budget_and_complete_arrays_retain_suffix_and_negatives(clock_pairs):
    _, policy, rows, _ = clock_pairs
    assert (policy.comparison_rtol, policy.comparison_atol) == (D("1e-7"), D("1e-8"))
    for label, original, result, left, right, *_ in rows:
        assert result.original_pair == original
        assert (left.assignment.assignment.numerical_view.rtol, right.assignment.assignment.numerical_view.atol) == (D("1e-9"), D("1e-10"))
        assert result.disposition is (A.UNEVALUABLE if label == "unchanged" else A.FALSIFIED)
        assert tuple(map(len, result.complete_call_censuses)) == (1, 1)
        assert all(row.returned_clock.state_rows == 174 for side in result.complete_call_censuses for row in side)
        assert "actual-terminal-suffix-or-clock-alignment-unresolved" in result.reason_codes
        assert result.real_open_gaps_retain_original_disposition
        assert not result.whole_time_certified and not result.physical_qualification and not result.later_use_admission
        assert decode_canonical_bytes(result.canonical_bytes(), type(result), maximum_bytes=None) == result


@pytest.mark.parametrize("damage", ("clock-source", "step-source", "state-source", "assignment", "evidence"))
def test_authenticated_sources_assignments_and_exact_originals_refuse_before_read(clock_pairs, damage):
    selected, policy, rows, temporary_file = clock_pairs
    _, original, _, left, right, *_ = rows[0]
    if damage == "clock-source":
        policy = replace(policy, clock_algorithm_source_sha256="f" * 64)
    elif damage == "step-source":
        policy = replace(policy, selected_step_source_sha256="f" * 64)
    elif damage == "state-source":
        policy = replace(policy, scientific_control=replace(policy.scientific_control, interval_algorithm_source_sha256="f" * 64))
    elif damage == "assignment":
        right = replace(right, assignment=replace(right.assignment, evidence_id="evidence.exposed.different-assignment"))
    else:
        right = replace(right, evidence=replace(right.evidence, evidence_id="evidence.exposed.different-original"))
    hooks = paired._Cursor, clock.state.local._assess_operand
    with pytest.raises(ValueError):
        clock.assess_clock(policy, selected[1], original, left, right, port(b""), port(b""), temporary_file=temporary_file)
    assert hooks == (paired._Cursor, clock.state.local._assess_operand)


@pytest.mark.parametrize("damage", ("omit-call", "clock-end", "row-count", "pass", "admission", "duplicate-boundary"))
def test_actual_call_census_and_adverse_outcome_cannot_be_thinned_or_relabelled(clock_pairs, damage):
    result = clock_pairs[2][0][2]
    with pytest.raises(ValueError):
        if damage == "omit-call":
            replace(result, complete_call_censuses=((), result.complete_call_censuses[1]))
        elif damage == "clock-end":
            original = result.complete_call_censuses[1][0]
            changed = replace(original, returned_clock=replace(original.returned_clock, exact_end=(31, 1)))
            replace(result, complete_call_censuses=(result.complete_call_censuses[0], (changed,)))
        elif damage == "row-count":
            original = result.complete_call_censuses[1][0]
            changed = replace(original, returned_clock=replace(original.returned_clock, state_rows=173))
            replace(result, complete_call_censuses=(result.complete_call_censuses[0], (changed,)))
        elif damage == "pass":
            replace(result, disposition=A.SATISFIED, reason_codes=())
        elif damage == "admission":
            replace(result, later_use_admission=True)
        else:
            replace(result, boundaries=(object(), object()))


def test_independent_literal_fraction_boundary_budget_preserves_all174_rows(clock_pairs):
    policy = clock_pairs[1]
    left = (float(0).hex(),) * 174
    right = tuple(float(1e-9 if i == 173 else 0).hex() for i in range(174))
    result = clock.clock._metric(left, right, 174, policy)
    expected = Fraction.from_float(1e-9) / (Fraction(D("1e-8")) + Fraction(D("1e-7")) * Fraction.from_float(1e-9))
    assert result.checked_components == 174 and result.maximum_row == 173
    assert Fraction(*result.maximum_exact_normalized_difference) == expected and not result.failed_components
    adverse = clock.clock._metric(left, tuple(float(1e-3 if i == 173 else 0).hex() for i in range(174)), 174, policy)
    assert adverse.failed_components == (173,)


def test_missing_actual_clock_call_retains_census_and_cannot_be_favourable(clock_pairs):
    result = clock_pairs[2][0][2]
    original = result.complete_call_censuses[1][0]
    missing = replace(original, returned_clock=None, full_state=None, reason_codes=(clock.MISSING,))
    calls = result.complete_call_censuses[0], (missing,)
    disposition, reasons = clock._reasons(result.original_pair, calls, result.boundaries)
    changed = replace(result, complete_call_censuses=calls, disposition=disposition, reason_codes=reasons)
    assert changed.disposition is A.UNEVALUABLE and clock.MISSING in changed.reason_codes
    assert tuple(map(len, changed.complete_call_censuses)) == (1, 1)
    with pytest.raises(ValueError):
        replace(changed, disposition=A.SATISFIED, reason_codes=())


def test_legacy_clock_contract_remains_exact_and_rejects_new_native_weight_relabelling(clock_pairs):
    _, policy, rows, _ = clock_pairs
    legacy = clock.clock.RepresentableClockPolicy("policy.exposed.legacy-unchanged",
        clock.step.identity(policy.scientific_control.algorithm_control, "control_id"), policy.selected_step_source_sha256)
    retained = legacy.canonical_bytes()
    assert decode_canonical_bytes(retained, type(legacy), maximum_bytes=None).canonical_bytes() == retained
    assert rows[0][2].original_pair == rows[0][1]
    with pytest.raises(ValueError):
        replace(legacy, comparison_rtol=D("1e-9"))
