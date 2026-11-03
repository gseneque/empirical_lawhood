# SPDX-License-Identifier: MPL-2.0
"""Actual custody/relay/consumer route with an exposed solver; no molecular work."""

from dataclasses import fields, replace
from io import BytesIO
import json
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.battery_refined_inquiry import lossless_evidence_stream as stream
from empirical_lawhood.adapters.methods.battery_refined_inquiry import lossless_segment_consumer as consumer
from empirical_lawhood.adapters.methods.battery_refined_inquiry import lossless_segment_native as storage
from empirical_lawhood.adapters.methods.battery_refined_inquiry import lossless_segment_records as records
from empirical_lawhood.adapters.methods.battery_refined_inquiry import lossless_segment_runner as runner
from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_evidence as evidence
from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_fidelity as local
from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_native as native
from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_science as science
from empirical_lawhood.adapters.methods.battery_segmented_inquiry import evidence_stream as old
from empirical_lawhood.adapters.methods.battery_segmented_inquiry import operation_bindings as bindings
from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.runtime.artifacts import ArtifactLineageParent, ArtifactProfile, ArtifactStreamWriteRequest
from tests.test_battery_segmented_native import custody as custody_fixture, exposed_backend, acquire
from tests.test_battery_refined_inquiry import selected as selected_fixture
from tests.test_battery_segmented_fidelity import _operand, _receipt, prepared as prepared_fixture
from tests.test_battery_lossless_segment_records import encoded_original

custody, selected = custody_fixture, selected_fixture
prepared = prepared_fixture


class Emitter:
    def __init__(self):
        self.lines = []
    def write(self, output, line):
        assert output == "segments"
        self.lines.append(line)


def original_stream(custody, result):
    relay = tuple(runner.relay_segments(custody.store, custody.definition, result.inspection, result.trace, result.protocol))
    emitter = Emitter()
    header = old.SegmentStreamHeader(science.identity(result.trace, "trace_id"), science.identity(result.protocol, "protocol_id"), len(result.trace.segments))
    sequence = stream.emit_header(emitter, "segments", header)
    for frame in relay:
        sequence = stream.emit_frame(emitter, "segments", frame.metadata, frame.raw_lines(), sequence)
    return relay, emitter.lines


def test_actual_new_physical_receipts_and_complete_ordinary_consumer(custody, monkeypatch, tmp_path):
    _, _, effects = exposed_backend(custody, monkeypatch)
    old_capture, old_outputs = native.observe_raw_return, native.segment_outputs
    with storage.native_storage_scope():
        result = acquire(custody)
    assert native.observe_raw_return is old_capture and native.segment_outputs is old_outputs
    assert result.trace.disposition == "TARGET_REACHED", result.trace.error_message
    assert result.trace.backend_solve_calls == len(effects) == 3
    frames, lines = original_stream(custody, result)
    assert len(frames) == 3
    for frame, summary in zip(frames, result.trace.segments, strict=True):
        raw_output = tuple(row for row in frame.metadata.native_receipt.output_logical_artifacts if row.payload_schema == records.RawSegmentStreamLine.SCHEMA)
        assert len(raw_output) == 1 and raw_output[0].content_sha256 == frame.metadata.raw_physical_sha256
        assert frame.metadata.raw_index.decoded_subject == summary.raw_return
        assert frame.metadata.full_index.decoded_subject == summary.full_state
        assert not any(row.payload_schema in {native.RawReturnedSegment.SCHEMA, native.FullStateSegment.SCHEMA}
            for row in frame.metadata.native_receipt.output_logical_artifacts)
        assert frame.metadata.full_index.raw_index == records.identity(frame.metadata.raw_index, "index_id")
    # The real existing JSONL_CHUNKS owner must accept the entire new ordinary
    # artifact and publish its actual physical byte/hash identity.
    request = ArtifactStreamWriteRequest("ordinary.exposed-lossless", "ordinary/segments.jsonl", stream.LosslessEvidenceLine.SCHEMA,
        ArtifactProfile.JSONL_CHUNKS, "application/x-ndjson", "exposed.lossless", "ordinary", iter(lines),
        maximum_bytes=sum(map(len, lines)), maximum_chunk_bytes=max(map(len, lines)),
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, parent_visibility_ceilings=(), outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE)
    written = custody.plane.write_stream(request)
    raw_path = custody.plane.root.resolve(written.materialization.relative_path, for_write=False)
    manifest = decode_artifact_manifest(raw_path.with_name(raw_path.name + ".manifest.json").read_bytes())
    assert manifest.logical.payload_schema == stream.LosslessEvidenceLine.SCHEMA and manifest.materialization.size_bytes == sum(map(len, lines))
    payload = raw_path.read_bytes()
    port = SimpleNamespace(size_bytes=len(payload), read=BytesIO(payload).read)
    decoded = iter(stream.read_frames(port, temporary_file=stream.selected_temporary_files(tmp_path)))
    assert next(decoded).segment_count == 3
    previous = None
    for frame, summary in zip(decoded, result.trace.segments, strict=True):
        assessment = consumer.assess_operand(local.FullStateOperand(custody.config, result.protocol, result.layout, summary, frame, previous))
        assert assessment.disposition is A.FALSIFIED
        assert assessment.reason_codes == ("actual-native-solver-type-or-tolerances-disagree",)
        assert assessment.full_state_components == assessment.retained_derivative_components == 174 * 3
        assert assessment.retained_raw_bytes == (3 + 2 * 174 * 3) * 8
        assert all(sum(map(len, block.state_binary64.cached.values())) <= 2 * records.codec.CHUNK_BYTES for block in frame.full_state.blocks)
        previous = frame.actual_terminal
    assert all(handle.closed for handle in frame.handles)
    recovered = acquire(custody)
    assert recovered.recovered and len(effects) == 3
    original = bindings.FORECAST_OUTPUTS
    with runner.contract_scope():
        assert bindings.operation_inputs("assess")[1][1] is stream.LosslessEvidenceLine
        assert bindings.operation_outputs("forecast")[1][1] is stream.LosslessEvidenceLine
    assert bindings.FORECAST_OUTPUTS is original


@pytest.mark.parametrize("case", ("malformed", "nonfinite", "solver-failure", "derivative-absent", "derivative-empty"))
def test_adverse_raw_and_complete_denominators_survive_used_route(custody, monkeypatch, tmp_path, case):
    kwargs = {"malformed": {"malformed": True}, "nonfinite": {"bad_bits": 0x7ff8000000000042},
        "solver-failure": {"fail_at": 1}, "derivative-absent": {"derivatives": "none"}, "derivative-empty": {"derivatives": "empty"}}[case]
    _, _, effects = exposed_backend(custody, monkeypatch, **kwargs)
    with storage.native_storage_scope():
        result = acquire(custody)
    _, lines = original_stream(custody, result)
    decoded = iter(stream.read_frames(SimpleNamespace(size_bytes=sum(map(len, lines)), read=BytesIO(b"".join(lines)).read),
        temporary_file=stream.selected_temporary_files(tmp_path)))
    assert next(decoded).segment_count == len(result.trace.segments) == len(effects)
    previous = None
    for frame, summary in zip(decoded, result.trace.segments, strict=True):
        checked = consumer.assess_operand(local.FullStateOperand(custody.config, result.protocol, result.layout, summary, frame, previous))
        if case in {"malformed", "nonfinite", "solver-failure"}:
            assert checked.disposition is A.UNEVALUABLE and checked.full_state_components == 0
            assert len(effects) == 1 and result.trace.disposition == "TECHNICAL_FAILURE"
            if case == "solver-failure":
                assert frame.raw_return is None and checked.retained_raw_bytes == 0
            else:
                assert frame.raw_return is not None and checked.retained_raw_bytes > 0
        else:
            assert checked.disposition is A.FALSIFIED and checked.retained_derivative_components == 0
            assert checked.reason_codes == ("actual-native-solver-type-or-tolerances-disagree",)
            assert frame.raw_return.block_counts[2] == (None if case == "derivative-absent" else 0)
        previous = frame.actual_terminal


@pytest.mark.parametrize("case", ("native-raw-sha", "native-size", "old-receipt", "hidden-full", "missing-frame-end", "wrong-sequence", "extra-frame"))
def test_used_consumer_refuses_physical_custody_or_complete_transport_forgery(custody, monkeypatch, tmp_path, case):
    exposed_backend(custody, monkeypatch)
    with storage.native_storage_scope():
        result = acquire(custody)
    frames, lines = original_stream(custody, result)
    metadata = frames[0].metadata
    if case in {"native-raw-sha", "native-size", "old-receipt", "hidden-full"}:
        changes = {"native-raw-sha": {"raw_physical_sha256": "e" * 64}, "native-size": {"raw_size_bytes": metadata.raw_size_bytes + 1},
            "old-receipt": {"native_receipt": metadata.request_receipt}, "hidden-full": {"full_index": None}}[case]
        with pytest.raises(ValueError):
            replace(metadata, **changes)
        return
    if case == "missing-frame-end":
        lines.pop()
    elif case == "extra-frame":
        lines.append(lines[-1])
    else:
        row = json.loads(lines[1])
        row["sequence"] += 1
        lines[1] = stream.LosslessEvidenceLine(row["sequence"], **row["value"]).canonical_bytes()
    with pytest.raises(ValueError):
        list(stream.read_frames(SimpleNamespace(size_bytes=sum(map(len, lines)), read=BytesIO(b"".join(lines)).read),
            temporary_file=stream.selected_temporary_files(tmp_path)))


def test_custody_failure_cannot_become_known_solver_failure(custody, monkeypatch):
    _, _, effects = exposed_backend(custody, monkeypatch)
    original = custody.store.publish_output
    def failure(entry, name, *args, **kwargs):
        if name == "raw-return":
            raise RuntimeError("exposed physical custody refusal")
        return original(entry, name, *args, **kwargs)
    monkeypatch.setattr(custody.store, "publish_output", failure)
    with storage.native_storage_scope(), pytest.raises(native._CustodyFailure):
        acquire(custody)
    assert len(effects) == 1
    assert custody.store.inspect(effects[0][0]).state.value == "UNKNOWN_COMPLETION"


def test_complete_pure_consumer_uses_actual_new_schema_and_receiver_census(custody, monkeypatch, tmp_path):
    exposed_backend(custody, monkeypatch)
    with storage.native_storage_scope():
        result = acquire(custody)
    original_evidence = evidence.evidence_from_result(custody.config, result)
    _, lines = original_stream(custody, result)
    summary = consumer.assess_trace(custody.config, original_evidence,
        SimpleNamespace(size_bytes=sum(map(len, lines)), read=BytesIO(b"".join(lines)).read),
        temporary_file=stream.selected_temporary_files(tmp_path))
    assert summary.charging_segment_calls == len(summary.segment_assessments) == len(result.trace.segments) == 3
    assert sum(row.full_state_components for row in summary.segment_assessments) == 174 * 3 * 3
    assert summary.trace == science.identity(result.trace, "trace_id")
    # This artificial exposed charging receiver is not qualification evidence.
    assert summary.disposition is A.UNEVALUABLE
    assert "independent-native-preparation-or-segment-integrity-unadmitted" in summary.reason_codes


def new_operand(original, directory, temporary_file):
    """Exposed new primary receipts, never a relabelled scientific original."""
    index, full, sources = encoded_original(original.frame.raw_return, original.frame.full_state)
    definition = replace(original.frame.definition, outputs=storage.segment_outputs())
    successor = original.frame.next_request
    state_rows = tuple(getattr(original.frame, name) for name in
        ("requested_initial", "actual_initial", "initial_derivative", "actual_terminal", "terminal_derivative"))
    receipt = _receipt(directory, (original.frame.returned, full, *state_rows, successor),
        inputs=definition.input_materialization_ids, definition=definition)
    from tests.runtime_platform.test_native_subwork import _plane
    plane = _plane(directory)
    lines = tuple(records.encode_raw_segment(index, sources))
    parent = ArtifactLineageParent(definition.identity, VisibilityCeiling.DEVELOPMENT_ONLY, OutcomeAccess.DEVELOPMENT_VISIBLE)
    result = plane.write_stream(ArtifactStreamWriteRequest("output.raw", "outputs/raw.jsonl", records.RawSegmentStreamLine.SCHEMA,
        ArtifactProfile.JSONL_CHUNKS, "application/x-ndjson", "task.exposed", "outputs", iter(lines),
        maximum_bytes=sum(map(len, lines)), maximum_chunk_bytes=max(map(len, lines)),
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, parent_visibility_ceilings=(parent.visibility_ceiling,),
        outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE, lineage_parents=(parent,)))
    receipt = replace(receipt, output_materializations=tuple(sorted((*receipt.output_materializations, result.materialization), key=lambda row: row.materialization_id)),
        output_logical_artifacts=tuple(sorted((*receipt.output_logical_artifacts, result.logical), key=lambda row: row.logical_artifact_id)))
    summary = replace(original.summary, native_definition=definition.identity, native_receipt=records.identity(receipt, "receipt_id"))
    metadata = stream.LosslessSegmentMetadata(1, definition, original.frame.request_receipt, receipt, original.frame.request,
        original.frame.returned, successor, index, result.logical.content_sha256, result.materialization.size_bytes, full, *state_rows)
    frame = stream.decoded_frame(metadata, iter(lines), temporary_file)
    return replace(original, summary=summary, frame=frame)


@pytest.mark.parametrize("component,delta,derivative", ((None, 0., False), (0, .001, False), (81, .001, False), (173, .001, True)))
def test_unchanged_full_interval_math_uses_complete_new_custody_and_lazy_rows(prepared, tmp_path, component, delta, derivative):
    left = _operand(prepared, tmp_path / "left-original", extra_knot=7.5)
    changes = {} if component is None else {"changed_derivative" if derivative else "changed_state": (component, delta)}
    right = _operand(prepared, tmp_path / "right-original", horizon=30, extra_knot=12.25, **changes)
    control = local.FullStateControlProtocol("control.exposed-lossless")
    baseline = local.assess_interval(control, left, right)
    selected_temp = stream.selected_temporary_files(tmp_path)
    a, b = new_operand(left, tmp_path / "left-new", selected_temp), new_operand(right, tmp_path / "right-new", selected_temp)
    old_cursor, old_guard = consumer.paired._Cursor, local._assess_operand
    try:
        with consumer.numerical_consumer_scope(temporary_file=selected_temp, assignments=()):
            actual = local.assess_interval(control, a, b)
        assert consumer.paired._Cursor is old_cursor and local._assess_operand is old_guard
        assert actual.disposition is baseline.disposition and actual.reason_codes == baseline.reason_codes
        assert actual.query_count == baseline.query_count == 33
        assert actual.checked_rhs_components == baseline.checked_rhs_components == 173 * 33
        assert actual.checked_algebraic_components == baseline.checked_algebraic_components == 33
        assert actual.checked_derivative_components == baseline.checked_derivative_components == 174 * 33
        for field in ("maximum_scaled_state_residual_lower", "maximum_scaled_state_residual_upper",
                "maximum_scaled_derivative_residual_lower", "maximum_scaled_derivative_residual_upper", "query_grid_sha256"):
            assert getattr(actual, field) == getattr(baseline, field)
        assert actual.left_receipt != baseline.left_receipt and actual.right_receipt != baseline.right_receipt
    finally:
        a.frame.close()
        b.frame.close()


def selected_preparation(prepared, selected):
    """A prospectively selected exposed scalar recipe, with original toy state."""
    from empirical_lawhood.adapters.methods.battery_refined_inquiry import contracts as c
    from empirical_lawhood.adapters.methods.battery_refined_inquiry import forecast_step_control as step
    from empirical_lawhood.adapters.methods.battery_refined_inquiry import source_derived_preparation as roots
    chosen = next(row for row in selected[1].configurations
        if row.component_view == prepared[0].native.component_view and row.recipe == prepared[0].native.recipe)
    root = roots.supply_source_roots(c.identity(selected[1].source), 'ORegan2022')
    config = replace(prepared[0], native=chosen, preparation=root, preparation_assessment=roots.assess_source_roots(root))
    protocol = replace(prepared[1], configuration=step.identity(config, 'config_id'), source=c.identity(selected[1].source), initial_temperature_k=config.initial_temperature_k)
    protocol_id = step.identity(protocol, 'protocol_id')
    layout = replace(prepared[3], protocol=protocol_id)
    layout_id = step.identity(layout, 'layout_id')
    assignment = replace(prepared[2], configuration=step.identity(config, 'config_id'), protocol=protocol_id,
        supplied_preparation=step.identity(root, 'preparation_id'))
    temperature = next(block for block in layout.blocks if block.role == 'temperature')
    observed = []
    for row in prepared[4:]:
        values = tuple(config.initial_temperature_k / temperature.scale if i == temperature.start else value
            for i, value in enumerate(row.scaled_values))
        observed.append(replace(row, protocol=protocol_id, layout=layout_id, scaled_values=values,
            binary64_hex=tuple(float(value).hex() for value in values)))
    return config, protocol, assignment, layout, *observed


def selected_stream(prepared, selected, directory, temporary_file, *, horizon, changed_state=None):
    """Entire exposed original/new receipt closure; no solver or native contact."""
    from tests.test_battery_segmented_fidelity_stream import _stream
    from tests.test_battery_forecast_step_control import witness
    from empirical_lawhood.kernel.serialization import canonical_json_bytes
    original_evidence, frames = _stream(prepared, directory / 'old', horizon=horizon, changed_state=changed_state)
    frame, config = frames[0], original_evidence.trace.config
    assignment = replace(witness(selected[2], config)[2], assignment_id='assignment.exposed.' + str(horizon))
    request_document = json.loads(frame.request.primitive_json)
    request_document['solver'] = json.loads(assignment.actual_solver_json)
    request = replace(frame.request, primitive_json=canonical_json_bytes(request_document).decode())
    returned = replace(frame.returned, request=request.identity)
    raw = replace(frame.raw_return, request=request.identity, returned=science.identity(returned, 'return_id'))
    full = replace(frame.full_state, request=request.identity, returned=science.identity(returned, 'return_id'),
        raw_return=science.identity(raw, 'raw_id'))
    carrier = _receipt(directory / 'request', (request,))
    definition = replace(frame.definition, configuration=request.identity,
        input_materialization_ids=tuple(row.materialization_id for row in carrier.output_materializations), sources=tuple(sorted(assignment.control.sources, key=lambda row: row.object_id)))
    values = (returned, raw, full, frame.requested_initial, frame.actual_initial, frame.initial_derivative,
        frame.actual_terminal, frame.terminal_derivative, frame.next_request)
    receipt = _receipt(directory / 'old-matched', values, inputs=definition.input_materialization_ids, definition=definition)
    summary = replace(original_evidence.trace.segments[0], request=request.identity, returned=science.identity(returned, 'return_id'),
        native_definition=definition.identity, native_receipt=science.identity(receipt, 'receipt_id'),
        raw_return=science.identity(raw, 'raw_id'), full_state=science.identity(full, 'segment_id'))
    old_frame = old.SegmentEvidenceFrame(1, definition, carrier, receipt, request, returned, frame.next_request,
        raw, full, frame.requested_initial, frame.actual_initial, frame.initial_derivative, frame.actual_terminal, frame.terminal_derivative)
    converted = new_operand(local.FullStateOperand(config, original_evidence.protocol, original_evidence.layout, summary, old_frame),
        directory / 'new', temporary_file)
    metadata = converted.frame.metadata
    converted.frame.close()
    trace = replace(original_evidence.trace, segments=(converted.summary,))
    main_records = (trace, original_evidence.protocol, original_evidence.source_assignment, original_evidence.layout,
        original_evidence.requested_initial, original_evidence.actual_initial, original_evidence.initial_derivative,
        original_evidence.actual_terminal, original_evidence.terminal_derivative)
    main_receipt = _receipt(directory / 'main-new', main_records)
    actual_evidence = evidence.SegmentedNativeEvidence(original_evidence.evidence_id, *main_records, native_receipt=main_receipt)
    index, _, sources = encoded_original(raw, full)
    emitter = Emitter()
    sequence = stream.emit_header(emitter, 'segments', old.SegmentStreamHeader(science.identity(trace, 'trace_id'),
        science.identity(actual_evidence.protocol, 'protocol_id'), 1))
    stream.emit_frame(emitter, 'segments', metadata, records.encode_raw_segment(index, sources), sequence)
    payload = b''.join(emitter.lines)
    return consumer.paired.FullStateStreamOperand(actual_evidence, SimpleNamespace(size_bytes=len(payload), read=BytesIO(payload).read)), assignment


@pytest.mark.parametrize('damage', (None, 'missing-assignment', 'wrong-request-options', 'missing-policy-source', 'different-view'))
def test_actual_complete_paired_cursor_consumes_selected_assignment_and_preserves_suffix(prepared, tmp_path, damage):
    from tests.test_battery_forecast_step_control import selected as future_fixture
    selected = future_fixture.__wrapped__()
    prepared = selected_preparation(prepared, selected)
    temporary_file = stream.selected_temporary_files(tmp_path)
    left, left_assignment = selected_stream(prepared, selected, tmp_path / 'left-pair', temporary_file, horizon=60)
    right, right_assignment = selected_stream(prepared, selected, tmp_path / 'right-pair', temporary_file, horizon=30)
    assignments = (left_assignment, right_assignment)
    if damage == 'missing-assignment':
        assignments = (left_assignment,)
    elif damage == 'wrong-request-options':
        # A separately valid selected assignment does not authorize old dt_max.
        doc = json.loads(right_assignment.actual_solver_json)
        doc['options']['dt_max'] = {'binary64': 0.0.hex()}
        right_assignment = object.__new__(type(right_assignment))
        for field in fields(left_assignment):
            object.__setattr__(right_assignment, field.name, getattr(assignments[1], field.name))
        object.__setattr__(right_assignment, 'actual_solver_json', json.dumps(doc))
        assignments = left_assignment, right_assignment
    elif damage == 'missing-policy-source':
        assignments = (left_assignment, replace(right_assignment, control=replace(selected[2], policy_id='other.exposed-policy')))
    elif damage == 'different-view':
        different = next(row for row in selected[1].policy.views if row.view_id == 'chen-spme')
        assignments = (left_assignment, replace(right_assignment, numerical_view=different))
    old_cursor, old_guard = consumer.paired._Cursor, local._assess_operand
    if damage is not None:
        with pytest.raises(ValueError), consumer.numerical_consumer_scope(temporary_file=temporary_file, assignments=assignments):
            consumer.paired.assess_streams(local.FullStateControlProtocol('control.exposed.selected-pair'), left, right)
    else:
        with consumer.numerical_consumer_scope(temporary_file=temporary_file, assignments=assignments):
            result = consumer.paired.assess_streams(local.FullStateControlProtocol('control.exposed.selected-pair'), left, right)
        assert result.declared_segment_counts == (1, 1) and result.original_retained_native_knots == (2, 2)
        assert result.compared_rhs_components == 173 * 31 and result.compared_algebraic_components == 31
        assert result.compared_derivative_components == 174 * 31
        assert all(row.disposition is A.SATISFIED for rows in result.segment_assessments for row in rows)
        assert result.disposition is A.UNEVALUABLE
        assert {'unpaired-actual-terminal-suffix', 'actual-terminal-clocks-differ'}.issubset(result.reason_codes)
    assert consumer.paired._Cursor is old_cursor and local._assess_operand is old_guard
