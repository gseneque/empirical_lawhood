# SPDX-License-Identifier: MPL-2.0
"""Exposed independent controls; source-derived preparation is not qualification."""

from dataclasses import replace
from decimal import Decimal as D
import math
import json
import struct

import pytest

from empirical_lawhood.adapters.methods.battery_refined_inquiry import contracts as c, science as selected_science
from empirical_lawhood.adapters.methods.battery_refined_inquiry import preparation_contracts as pc
from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_contracts as sc, segmented_science as ss
from empirical_lawhood.adapters.methods.battery_refined_inquiry import source_derived_preparation as derived
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest, CanonicalTaskReceipt
from tests.test_battery_initial_preparation import _prepared_fixture
from tests.test_battery_refined_inquiry import selected as exposed_selection
from tests.runtime_platform.test_native_subwork import _plane


@pytest.fixture
def prepared():
    source, policy = exposed_selection.__wrapped__()
    native = next(row for row in selected_science.configurations(source, policy, "use") if row.component_view == "oregan-spme" and row.recipe == "chamber-35c")
    supplier = derived.supply_source_roots(c.identity(source), "ORegan2022")
    config = sc.SegmentedNativeConfig("config.segmented.exposed", native, supplier, derived.assess_source_roots(supplier),
        sc.SegmentedMethodProtocol("method.segmented.exposed.60s", D(60)))
    _, old = _prepared_fixture()
    protocol = replace(old["protocol"], configuration=ss.identity(config, "config_id"), source=c.identity(source))
    protocol_id = ss.identity(protocol, "protocol_id")
    layout = replace(old["layout"], protocol=protocol_id)
    layout_id = ss.identity(layout, "layout_id")
    names = tuple(sorted(("assigned_negative_concentration", "assigned_positive_concentration", "pre_soc_negative_concentration", "pre_soc_positive_concentration")))
    assignment = sc.ActualSourceAssignment("assignment.exposed", ss.identity(config, "config_id"), protocol_id,
        ss.identity(supplier, "preparation_id"), supplier.assigned_negative_concentration, supplier.assigned_positive_concentration,
        supplier.pre_soc_negative_concentration, supplier.pre_soc_positive_concentration,
        tuple((name, float(getattr(supplier, name)).hex()) for name in names))
    requested = replace(old["requested_initial"], protocol=protocol_id, layout=layout_id)
    actual = replace(old["actual_initial"], protocol=protocol_id, layout=layout_id)
    return config, protocol, assignment, layout, requested, actual


def _state_changed(state, index, delta):
    values = tuple(value + delta if i == index else value for i, value in enumerate(state.scaled_values))
    return replace(state, scaled_values=values, binary64_hex=tuple(float(value).hex() for value in values))


def test_derived_source_assessment_requires_actual_complete_preparation(prepared):
    assessment = ss.assess_derived_preparation(*prepared)
    assert assessment.disposition is A.SATISFIED and assessment.checked_differential_components == 173
    assert not assessment.physical_qualification and "OLD_UNKNOWN_RETAINED" in assessment.historical_completion
    assert decode_canonical_bytes(assessment.canonical_bytes(), type(assessment), maximum_bytes=None) == assessment
    assert prepared[0].preparation.observation_kind == "DERIVED_SOURCE_MATHEMATICS"


@pytest.mark.parametrize("index", (0, 1, 2, 81, 172))
def test_nonzero_origins_wrong_temperature_and_any_particle_component_falsify(prepared, index):
    changed = (*prepared[:-1], _state_changed(prepared[-1], index, D(".001")))
    assessment = ss.assess_derived_preparation(*changed)
    assert assessment.disposition is A.FALSIFIED
    assert "pointwise-full-derived-initial-state-disagrees" in assessment.reason_codes


def test_radial_average_compensation_cannot_hide_wrong_full_preparation(prepared):
    actual = _state_changed(_state_changed(prepared[-1], 2, D(".001")), 3, D("-.001"))
    assert sum(actual.scaled_values[2:42]) == sum(prepared[-1].scaled_values[2:42])
    assert ss.assess_derived_preparation(*prepared[:-1], actual).disposition is A.FALSIFIED


def test_missing_actual_state_is_unevaluable_even_with_favourable_mathematical_roots(prepared):
    actual = replace(prepared[-1], kind=pc.ObservationKind.UNAVAILABLE, scaled_values=(), binary64_hex=(), model_clock_s=None)
    result = ss.assess_derived_preparation(*prepared[:-1], actual)
    assert result.disposition is A.UNEVALUABLE and result.checked_differential_components == 0


def test_wrong_actual_binary64_assignment_falsifies_without_manufacturing_soh(prepared):
    assignment = prepared[2]
    value = assignment.assigned_positive_concentration + 1
    changed = replace(assignment, assigned_positive_concentration=value,
        binary64_operands=tuple((name, float(value if name == "assigned_positive_concentration" else getattr(assignment, name)).hex()) for name, _ in assignment.binary64_operands))
    result = ss.assess_derived_preparation(prepared[0], prepared[1], changed, *prepared[3:])
    assert result.disposition is A.FALSIFIED
    assert "actual-parameter-assignment-differs-from-assessed-derived-operands" in result.reason_codes


@pytest.mark.parametrize("field, value", (("receiver_spacing_s", D(2)), ("maximum_model_clock_s", D(3600)),
    ("maximum_segment_horizon_s", D(59)), ("fidelity", "QUALIFIED"), ("historical_completion", "COMPLETED")))
def test_changed_method_cannot_thin_or_grant_unassessed_scientific_results(prepared, field, value):
    with pytest.raises(ValueError):
        replace(prepared[0].method, **{field: value})


def test_method_change_is_a_scientific_operand_and_wrong_stock_join_refuses(prepared):
    config = prepared[0]
    half = replace(config, method=replace(config.method, maximum_segment_horizon_s=D(30)))
    assert half.fingerprint() != config.fingerprint() and half.native == config.native
    wrong = derived.supply_source_roots(c.identity(config.source), "Chen2020")
    with pytest.raises(ValueError, match="source/stock join"):
        replace(config, preparation=wrong, preparation_assessment=derived.assess_source_roots(wrong))


def test_exact_source_ulp_clocks_are_preserved_in_compact_summary(prepared):
    config, protocol = prepared[:2]
    def marker(name, schema):
        return ObjectIdentity(name, schema, "1.0.0", "1" * 64)
    start, horizon = D("120.00000000000003"), D(60)
    first = D(str(math.nextafter(float(start), math.inf)))
    last = D(str(float(start) + float(horizon)))
    states = tuple(marker("state." + name, pc.StateObservation.SCHEMA) for name in ("requested", "initial", "di", "terminal", "dt"))
    summary = sc.SegmentSummary("summary.exposed", ss.identity(config, "config_id"), ss.identity(protocol, "protocol_id"), 3, "LOW", start, horizon,
        marker("request.exposed", "empirical-lawhood/battery-segmented/native-request"),
        marker("return.exposed", "empirical-lawhood/battery-segmented/native-return"),
        marker("receipt.exposed", "empirical-lawhood/runtime/canonical-task-receipt"), "RETURNED", "final time", None, None,
        D(1), D(2), 4096, (first, last), (D(-1), D(4), D(293), D(0)), (D(-1), D(4), D(293), D("-.1")),
        marker("payload.exposed", "empirical-lawhood/battery-segmented/full-state-segment"), *states,
        marker("definition.exposed", "empirical-lawhood/runtime/native-subwork-definition"),
        raw_return=marker("raw.exposed", "empirical-lawhood/battery-segmented/raw-returned-segment"))
    assert summary.requested_start_clock_s == start and summary.native_times_s == (first, last)
    with pytest.raises(ValueError, match="native clocks"):
        replace(summary, native_times_s=(D(str(math.nextafter(float(first), math.inf))), last))


def _segment_fixture(prepared, tmp_path, *, index=1, start=D(0), previous=None):
    from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_native as native
    config, protocol, _, layout, requested, initial = prepared
    first = start if start == 0 else D(str(math.nextafter(float(start), math.inf)))
    last = D(str(float(start) + 60.0))
    base = initial if previous is None else previous
    requested = replace(requested, observation_id=f"request-state.exposed.{index}", model_clock_s=first,
        scaled_values=base.scaled_values, binary64_hex=base.binary64_hex)
    initial = replace(initial, observation_id=f"initial.exposed.{index}", model_clock_s=first,
        scaled_values=base.scaled_values, binary64_hex=base.binary64_hex)
    terminal = replace(_state_changed(initial, 0, D("-.01")), observation_id=f"terminal.exposed.{index}", role="actual-terminal", model_clock_s=last)
    def absent(role):
        return pc.StateObservation(f"absent.exposed.{index}." + role, ss.identity(protocol, "protocol_id"), ss.identity(layout, "layout_id"), role,
            pc.ObservationKind.UNAVAILABLE, None, (), (), ())
    di, dt = absent("initial-derivative"), absent("terminal-derivative")
    bit = lambda value: {"binary64": float(value).hex()}
    inputs = {"Inquiry active charging magnitude [A]": bit(D("1.455")), "Inquiry tier threshold [K]": bit(D("298.15") + config.localization_epsilon_k),
        "Inquiry tier direction": bit(-1)}
    def primitive_id(record, name):
        bound = ss.identity(record, name)
        return {"id": bound.object_id, "schema": bound.object_schema, "version": bound.object_version, "fingerprint": bound.object_fingerprint}
    document = {"regime": "LOW", "requested_start": bit(start), "duration": bit(60), "source_computed_end": bit(last),
        "inputs": inputs, "solver": {"type": "IDAKLUSolver", "rtol": bit(config.rtol), "atol": bit(config.atol)},
        "model_expression_sha256": layout.model_expression_sha256, "initial_conditions_sha256": layout.initial_conditions_sha256,
        "method": primitive_id(config.method, "method_id"), "previous_terminal": None if previous is None else primitive_id(previous, "observation_id"),
        "continuation_metadata": "NONE" if previous is None else config.method.continuation_method,
        "save": False, "initial_soc_argument": None}
    request = native.SegmentRequest(f"request.exposed.{index}", ss.identity(config, "config_id"), ss.identity(protocol, "protocol_id"), index,
        "charging", json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n")
    returned = native.SegmentReturn(f"return.exposed.{index}", request.identity, "RETURNED", None, None, '{"backend_returned":true}\n')
    row_major = tuple(value for pair in zip(initial.binary64_hex, terminal.binary64_hex, strict=True) for value in pair)
    def raw_array(shape, values):
        return native.RawReturnedArray("<f8", shape, 8, b"".join(struct.pack("<d", float.fromhex(value)) for value in values).hex())
    raw = native.RawReturnedSegment(f"raw.exposed.{index}", ss.identity(protocol, "protocol_id"), request.identity,
        ss.identity(returned, "return_id"), ("all_ts", "all_yps", "all_ys"),
        (raw_array((2,), (float(first).hex(), float(last).hex())),),
        (raw_array((len(initial.scaled_values), 2), row_major),), None)
    full = native.FullStateSegment(f"full.exposed.{index}", ss.identity(protocol, "protocol_id"), ss.identity(layout, "layout_id"),
        request.identity, ss.identity(returned, "return_id"), ss.identity(raw, "raw_id"),
        (native.FullStateBlock((float(first).hex(), float(last).hex()), len(initial.scaled_values), row_major, None),),
        (layout.model_expression_sha256,),
        json.dumps([inputs], sort_keys=True, separators=(",", ":")) + "\n", "final time")
    records = dict(request=request, returned=returned, full_state=full, requested_initial=requested, actual_initial=initial,
        initial_derivative=di, actual_terminal=terminal, terminal_derivative=dt, raw_return=raw)
    receipt = _receipt(tmp_path, tuple(records.values())[1:])
    summary = sc.SegmentSummary(f"summary.exposed.{index}", ss.identity(config, "config_id"), ss.identity(protocol, "protocol_id"), index, "LOW",
        start, D(60), request.identity, ss.identity(returned, "return_id"), ss.identity(receipt, "receipt_id"), "RETURNED", "final time", None, None,
        D(1), D(2), 4096, (first, last), (D(-1), D(4), D(293), D(0)), (D(-1), D(4), D(293), D("-.01")),
        ss.identity(full, "segment_id"), *(ss.identity(row, "observation_id") for row in (requested, initial, di, terminal, dt)),
        ObjectIdentity(f"definition.exposed.{index}", "empirical-lawhood/runtime/native-subwork-definition", "1.0.0", "a" * 64),
        raw_return=ss.identity(raw, "raw_id"))
    return config, protocol, layout, summary, receipt, records


def _receipt(tmp_path, records):
    plane = _plane(tmp_path)
    outputs = tuple(plane.write(ArtifactWriteRequest(f"output.{index:03d}", f"outputs/{index:03d}.json", record.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, "application/json", "task.exposed", "outputs", record.canonical_bytes(),
        VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE)) for index, record in enumerate(records))
    return CanonicalTaskReceipt("receipt.exposed", "run.exposed", "task.exposed", "attempt-001", "0" * 40, (),
        tuple(row.materialization for row in outputs), tuple(row.logical for row in outputs), (), OperationalStatus.SUCCEEDED, ())


def test_full_segment_derivative_absence_and_all_state_rows_are_independently_retained(prepared, tmp_path):
    *args, records = _segment_fixture(prepared, tmp_path)
    assessment = ss.assess_segment(*args, **records)
    assert assessment.disposition is A.SATISFIED
    assert assessment.full_state_components == 348 and assessment.retained_native_knots == 2
    assert assessment.retained_derivative_components == 0 and "NO_ACCURACY" in assessment.derivative_claim


def test_payload_receipt_substitution_refuses_before_any_scientific_admission(prepared, tmp_path):
    *args, records = _segment_fixture(prepared, tmp_path)
    records["actual_terminal"] = _state_changed(records["actual_terminal"], 2, D(".01"))
    with pytest.raises(ValueError, match="receipt payload"):
        ss.assess_segment(*args, **records)


def test_missing_native_knot_in_summary_is_a_known_falsifier(prepared, tmp_path):
    config, protocol, layout, summary, receipt, records = _segment_fixture(prepared, tmp_path)
    summary = replace(summary, native_times_s=summary.native_times_s[:1])
    result = ss.assess_segment(config, protocol, layout, summary, receipt, **records)
    assert result.disposition is A.FALSIFIED
    assert "complete-native-clock-or-termination-denominator-disagrees" in result.reason_codes


def test_continuation_retains_exact_full_state_and_source_clock_shift(prepared, tmp_path):
    *_, first_records = _segment_fixture(prepared, tmp_path / "first")
    previous = first_records["actual_terminal"]
    config, protocol, layout, summary, receipt, records = _segment_fixture(prepared, tmp_path / "second", index=2, start=D(60), previous=previous)
    result = ss.assess_segment(config, protocol, layout, summary, receipt, **records, previous_terminal=previous)
    assert result.disposition is A.SATISFIED and result.differential_continuity_components == 173
    assert records["requested_initial"].binary64_hex == previous.binary64_hex
    assert records["actual_initial"].model_clock_s == D(str(math.nextafter(60.0, math.inf)))
    wrong_previous = _state_changed(previous, 173, D(".01"))
    result = ss.assess_segment(config, protocol, layout, summary, receipt, **records, previous_terminal=wrong_previous)
    assert result.disposition is A.FALSIFIED
    assert "derived-continuation-changes-complete-terminal-state-or-clock" in result.reason_codes


def test_known_native_return_with_failed_extraction_never_becomes_sampling_integrity(prepared, tmp_path):
    config, protocol, layout, summary, _, records = _segment_fixture(prepared, tmp_path / "original")
    receipt = replace(_receipt(tmp_path / "failed", (records["returned"],)), operational_status=OperationalStatus.FAILED,
        reason_codes=("full-state-extraction-failed",))
    summary = replace(summary, native_receipt=ss.identity(receipt, "receipt_id"), disposition="TECHNICAL_FAILURE",
        error_type="ValueError", error_message="missing actual full state", native_times_s=(), start_receivers=(), end_receivers=(),
        full_state=None, raw_return=None, requested_initial=None, actual_initial=None, initial_derivative=None, actual_terminal=None, terminal_derivative=None)
    values = {"request": records["request"], "returned": records["returned"], **dict.fromkeys(
        ("full_state", "raw_return", "requested_initial", "actual_initial", "initial_derivative", "actual_terminal", "terminal_derivative"))}
    result = ss.assess_segment(config, protocol, layout, summary, receipt, **values)
    assert records["returned"].disposition == "RETURNED" and result.disposition is A.UNEVALUABLE
    assert "actual-full-native-payload-unavailable" in result.reason_codes
    assert result.retained_native_knots == result.full_state_components == 0


def test_actual_input_arrays_retain_exact_bits_and_wrong_regime_is_independently_rejected(prepared, tmp_path):
    config, protocol, layout, summary, _, records = _segment_fixture(prepared, tmp_path / "original")
    document = json.loads(records["full_state"].returned_inputs_json)
    arrays = [{name: {"shape": [1], "binary64": [value["binary64"]]} for name, value in row.items()} for row in document]
    full = replace(records["full_state"], returned_inputs_json=json.dumps(arrays, sort_keys=True, separators=(",", ":")) + "\n")
    records["full_state"] = full
    receipt = _receipt(tmp_path / "array-inputs", tuple(records.values())[1:])
    summary = replace(summary, native_receipt=ss.identity(receipt, "receipt_id"), full_state=ss.identity(full, "segment_id"))
    assert ss.assess_segment(config, protocol, layout, summary, receipt, **records).disposition is A.SATISFIED
    arrays[0]["Inquiry tier direction"]["binary64"] = [float(1).hex()]
    full = replace(full, returned_inputs_json=json.dumps(arrays, sort_keys=True, separators=(",", ":")) + "\n")
    records["full_state"] = full
    receipt = _receipt(tmp_path / "wrong-inputs", tuple(records.values())[1:])
    summary = replace(summary, native_receipt=ss.identity(receipt, "receipt_id"), full_state=ss.identity(full, "segment_id"))
    result = ss.assess_segment(config, protocol, layout, summary, receipt, **records)
    assert result.disposition is A.FALSIFIED and "actual-native-returned-inputs-disagree-with-frozen-regime" in result.reason_codes


def test_raw_bytes_are_independently_interpreted_even_when_both_payloads_are_receipted(prepared, tmp_path):
    config, protocol, layout, summary, _, records = _segment_fixture(prepared, tmp_path / "original")
    raw = records["raw_return"]
    array = raw.state_blocks[0]
    original = bytes.fromhex(array.bytes_hex)
    changed = replace(array, bytes_hex=(struct.pack("<d", 19.0) + original[8:]).hex())
    raw = replace(raw, state_blocks=(changed,))
    full = replace(records["full_state"], raw_return=ss.identity(raw, "raw_id"))
    records.update(raw_return=raw, full_state=full)
    receipt = _receipt(tmp_path / "both-actual", tuple(records.values())[1:])
    summary = replace(summary, native_receipt=ss.identity(receipt, "receipt_id"), full_state=ss.identity(full, "segment_id"), raw_return=ss.identity(raw, "raw_id"))
    result = ss.assess_segment(config, protocol, layout, summary, receipt, **records)
    assert result.disposition is A.FALSIFIED
    assert "raw-native-bits-shape-or-dtype-do-not-match-typed-interpretation" in result.reason_codes
    assert result.retained_raw_state_elements == result.full_state_components == 348


@pytest.mark.parametrize("first_bits", (0x7FF8000000001234, 0x7FF0000000000000, 0xFFF0000000000000))
def test_known_nonfinite_raw_return_keeps_exact_bytes_and_adverse_counts(prepared, tmp_path, first_bits):
    config, protocol, layout, summary, _, records = _segment_fixture(prepared, tmp_path / "original")
    raw = records["raw_return"]
    array = raw.state_blocks[0]
    original = bytes.fromhex(array.bytes_hex)
    changed = replace(array, bytes_hex=(struct.pack("<Q", first_bits) + original[8:]).hex())
    raw = replace(raw, state_blocks=(changed,))
    receipt = replace(_receipt(tmp_path / "failed", (records["returned"], raw)), operational_status=OperationalStatus.FAILED,
        reason_codes=("native-nonfinite-array",))
    summary = replace(summary, native_receipt=ss.identity(receipt, "receipt_id"), disposition="TECHNICAL_FAILURE",
        error_type="ValueError", error_message="nonfinite returned array", native_times_s=(), start_receivers=(), end_receivers=(),
        full_state=None, raw_return=ss.identity(raw, "raw_id"), requested_initial=None, actual_initial=None,
        initial_derivative=None, actual_terminal=None, terminal_derivative=None)
    values = {"request": records["request"], "returned": records["returned"], "raw_return": raw, **dict.fromkeys(
        ("full_state", "requested_initial", "actual_initial", "initial_derivative", "actual_terminal", "terminal_derivative"))}
    result = ss.assess_segment(config, protocol, layout, summary, receipt, **values)
    assert result.disposition is A.UNEVALUABLE and result.full_state_components == 0
    assert result.retained_raw_state_elements == 348 and result.retained_raw_bytes == 2800 and result.retained_raw_arrays == 2
    assert bytes.fromhex(raw.state_blocks[0].bytes_hex)[:8] == struct.pack("<Q", first_bits)
    assert "actual-returned-raw-array-custody-unavailable" not in result.reason_codes


def test_actual_request_publisher_definition_and_receipt_input_join_is_required(prepared, tmp_path):
    from tests.runtime_platform.test_native_subwork import _selected
    config, protocol, layout, summary, receipt, records = _segment_fixture(prepared, tmp_path / "segment")
    (tmp_path / "selected").mkdir()
    _, base, _ = _selected(tmp_path / "selected")
    publisher = _receipt(tmp_path / "publisher", (records["request"],))
    request_materialization = publisher.output_materializations[0].materialization_id
    definition = replace(base, operation_id="battery.segmented-native.segment", configuration=records["request"].identity,
        input_materialization_ids=tuple(sorted((*base.input_materialization_ids, request_materialization))))
    receipt = replace(receipt, input_materialization_ids=tuple(sorted((*definition.input_materialization_ids, "control.actual-definition"))))
    summary = replace(summary, native_definition=definition.identity, native_receipt=ss.identity(receipt, "receipt_id"))
    ss.authenticate_request_custody(summary, records["request"], definition, receipt, publisher)
    wrong_publisher = _receipt(tmp_path / "different-publisher", (records["request"],))
    wrong_publisher = replace(wrong_publisher, output_materializations=(replace(wrong_publisher.output_materializations[0],
        materialization_id="material.foreign.actual-request"),))
    with pytest.raises(ValueError, match="custody disagrees"):
        ss.authenticate_request_custody(summary, records["request"], definition, receipt, wrong_publisher)
    missing = replace(receipt, input_materialization_ids=tuple(name for name in receipt.input_materialization_ids if name != request_materialization))
    with pytest.raises(ValueError, match="custody disagrees"):
        ss.authenticate_request_custody(summary, records["request"], definition, missing, publisher)
    with pytest.raises(ValueError, match="custody disagrees"):
        ss.authenticate_request_custody(summary, records["request"], replace(definition, subwork_id="segment.foreign"), receipt, publisher)


