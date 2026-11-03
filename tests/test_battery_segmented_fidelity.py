# SPDX-License-Identifier: MPL-2.0
"""Independent exposed full-state comparisons; no native battery acquisition."""

from dataclasses import replace
from decimal import Decimal as D, localcontext
from fractions import Fraction
import json
import struct
import subprocess
import sys

import pytest

from empirical_lawhood.adapters.methods.battery_refined_inquiry import preparation_contracts as pc
from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_contracts as sc, segmented_fidelity as sf
from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_native as native, segmented_science as ss
from empirical_lawhood.adapters.methods.battery_segmented_inquiry.evidence_stream import SegmentEvidenceFrame
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactLineageParent, ArtifactProfile, ArtifactWriteRequest, CanonicalTaskReceipt
from empirical_lawhood.runtime.native_effects import NativeEffectContact
from empirical_lawhood.runtime.native_subwork import NativeSubworkDefinition
from tests.runtime_platform.test_native_subwork import _plane
from tests.test_battery_segmented_science import _segment_fixture, prepared as prepared_fixture

prepared = prepared_fixture


def _receipt(path, records, *, inputs=(), definition=None):
    path.mkdir(parents=True)
    plane = _plane(path)
    lineage = () if definition is None else (ArtifactLineageParent(definition.identity, VisibilityCeiling.DEVELOPMENT_ONLY, OutcomeAccess.DEVELOPMENT_VISIBLE),)
    outputs = tuple(plane.write(ArtifactWriteRequest(f"output.{index:03d}", f"outputs/{index:03d}.json", record.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, "application/json", "task.exposed", "outputs", record.canonical_bytes(),
        VisibilityCeiling.DEVELOPMENT_ONLY, tuple(parent.visibility_ceiling for parent in lineage), OutcomeAccess.DEVELOPMENT_VISIBLE, lineage_parents=lineage))
        for index, record in enumerate(records))
    return CanonicalTaskReceipt("receipt.exposed." + path.name, "run.exposed", "task.exposed", "attempt-001", "0" * 40, inputs,
        tuple(row.materialization for row in outputs), tuple(row.logical for row in outputs), (), OperationalStatus.SUCCEEDED, ())


def _operand(prepared, path, *, horizon=60, changed_state=None, changed_derivative=None, derivatives=True, extra_knot=None):
    path.mkdir(parents=True)
    config, protocol, layout, summary, _, records = _segment_fixture(prepared, path / "original")
    config = replace(config, config_id="config.exposed.full-state." + str(horizon),
        method=sc.SegmentedMethodProtocol("method.exposed.full-state." + str(horizon), D(horizon)))
    protocol = replace(protocol, protocol_id="protocol.exposed.full-state." + str(horizon), configuration=ss.identity(config, "config_id"))
    protocol_id = ss.identity(protocol, "protocol_id")
    layout = replace(layout, protocol=protocol_id)
    layout_id = ss.identity(layout, "layout_id")
    states = records["actual_initial"].binary64_hex
    if changed_state is not None:
        at, delta = changed_state
        states = tuple(float(float.fromhex(value) + delta).hex() if i == at else value for i, value in enumerate(states))
    clocks = (0., float(horizon)) if extra_knot is None else (0., float(extra_knot), float(horizon))
    dy = tuple(float(changed_derivative[1] if changed_derivative is not None and i == changed_derivative[0] else 0).hex()
        for i in range(len(states)))
    def observe(role, clock, bits):
        old = records[role]
        if bits is None:
            return replace(old, protocol=protocol_id, layout=layout_id, kind=pc.ObservationKind.UNAVAILABLE,
                model_clock_s=None, scaled_values=(), binary64_hex=())
        return replace(old, protocol=protocol_id, layout=layout_id, kind=pc.ObservationKind.OBSERVED,
            model_clock_s=D(str(clock)), scaled_values=tuple(D(str(float.fromhex(value))) for value in bits), binary64_hex=bits,
            producing_evidence=(ObjectIdentity("native.exposed-return", native.SegmentReturn.SCHEMA, "1.0.0", "a" * 64),))
    records.update(requested_initial=observe("requested_initial", 0., states), actual_initial=observe("actual_initial", 0., states),
        actual_terminal=observe("actual_terminal", float(horizon), states),
        initial_derivative=observe("initial_derivative", 0., dy if derivatives else None),
        terminal_derivative=observe("terminal_derivative", float(horizon), dy if derivatives else None))
    document = json.loads(records["request"].primitive_json)
    document.update(duration={"binary64": float(horizon).hex()}, source_computed_end={"binary64": float(horizon).hex()},
        method=ss._primitive_identity(config.method, "method_id"))
    request = replace(records["request"], request_id="request.exposed.full-state." + str(horizon), configuration=ss.identity(config, "config_id"),
        protocol=protocol_id, primitive_json=json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n")
    returned = replace(records["returned"], return_id="return.exposed.full-state." + str(horizon), request=request.identity)
    def raw(shape, bits):
        return native.RawReturnedArray("<f8", shape, 8, b"".join(struct.pack("<d", float.fromhex(value)) for value in bits).hex())
    values = tuple(value for value in states for _ in clocks)
    derivative_values = tuple(value for value in dy for _ in clocks) if derivatives else None
    raw_return = native.RawReturnedSegment("raw.exposed.full-state." + str(horizon), protocol_id, request.identity,
        ss.identity(returned, "return_id"), ("all_ts", "all_yps", "all_ys"),
        (raw((len(clocks),), tuple(value.hex() for value in clocks)),), (raw((len(states), len(clocks)), values),),
        None if derivative_values is None else (raw((len(states), len(clocks)), derivative_values),))
    full = native.FullStateSegment("full.exposed.full-state." + str(horizon), protocol_id, layout_id, request.identity,
        ss.identity(returned, "return_id"), ss.identity(raw_return, "raw_id"),
        (native.FullStateBlock(tuple(value.hex() for value in clocks), len(states), values, derivative_values),),
        (layout.model_expression_sha256,), records["full_state"].returned_inputs_json, "final time")
    records.update(request=request, returned=returned, raw_return=raw_return, full_state=full)
    carrier = _receipt(path / "carrier", (request,))
    inputs = (carrier.output_materializations[0].materialization_id,)
    parent = NativeEffectContact("run.exposed", "task.exposed", "effect.exposed",
        ObjectIdentity("plan.exposed", "empirical-lawhood/runtime/development-execution-plan", "1.0.0", "a" * 64),
        ObjectIdentity("task.exposed", "empirical-lawhood/runtime/execution-task", "1.0.0", "b" * 64), "0" * 40, inputs, ())
    definition = NativeSubworkDefinition("segment.exposed." + str(horizon), "battery.segmented-native.segment", parent, request.identity,
        (), "c" * 64, "d" * 64, inputs, (), native.segment_outputs())
    next_request = replace(request, request_id=request.request_id + ".end", kind="end-of-chain", primitive_json='{"end_of_chain":true}\n')
    receipt = _receipt(path / "returned", (*tuple(value for name, value in records.items() if name != "request"), next_request),
        inputs=inputs, definition=definition)
    summary = replace(summary, summary_id="summary.exposed.full-state." + str(horizon), configuration=ss.identity(config, "config_id"),
        protocol=protocol_id, requested_horizon_s=D(horizon), request=request.identity, returned=ss.identity(returned, "return_id"),
        native_receipt=ss.identity(receipt, "receipt_id"), native_definition=definition.identity,
        native_times_s=tuple(D(str(clock)) for clock in clocks), full_state=ss.identity(full, "segment_id"), raw_return=ss.identity(raw_return, "raw_id"),
        **{name: ss.identity(records[name], "observation_id") for name in ("requested_initial", "actual_initial", "initial_derivative", "actual_terminal", "terminal_derivative")})
    frame = SegmentEvidenceFrame(1, definition, carrier, receipt, request, returned, next_request, raw_return, full,
        *(records[name] for name in ("requested_initial", "actual_initial", "initial_derivative", "actual_terminal", "terminal_derivative")))
    return sf.FullStateOperand(config, protocol, layout, summary, frame)


def test_complete_union_grid_compares_all_rhs_algebraic_and_derivative_rows(prepared, tmp_path):
    left = _operand(prepared, tmp_path / "left", extra_knot=7.5)
    right = _operand(prepared, tmp_path / "right", horizon=30, extra_knot=12.25)
    result = sf.assess_interval(sf.FullStateControlProtocol("control.exposed.complete"), left, right)
    assert result.disposition is A.SATISFIED, result.reason_codes
    assert result.query_count == 33 and result.integer_seconds_in_interval == 31
    assert result.original_native_knots_in_interval == (2, 3)
    assert result.checked_rhs_components == 173 * 33 and result.checked_algebraic_components == 33
    assert result.checked_derivative_components == 174 * 33
    assert result.derived_state_components > 0 and result.derived_derivative_components == result.derived_state_components
    assert result.maximum_scaled_state_residual_upper < D("1e-65")
    assert decode_canonical_bytes(result.canonical_bytes(), type(result), maximum_bytes=None) == result
    assert not result.whole_time_certified and not result.physical_qualification
    for damaged in ({"maximum_scaled_state_residual_upper": D(2)},
            {"maximum_scaled_derivative_residual_lower": None, "maximum_scaled_derivative_residual_upper": None}):
        with pytest.raises(ValueError, match="omits independently"):
            replace(result, **damaged)
    for damaged in ({"derived_state_components": result.checked_derivative_components + 1},
            {"uncertain_derivative_components": result.checked_derivative_components + 1}):
        with pytest.raises(ValueError, match="component denominator"):
            replace(result, **damaged)


@pytest.mark.parametrize("component", (0, 1, 2, 81, 172, 173))
def test_any_full_state_component_falsifies_and_complete_adverse_denominator_survives(prepared, tmp_path, component):
    left = _operand(prepared, tmp_path / "left")
    right = _operand(prepared, tmp_path / "right", horizon=30, changed_state=(component, .001))
    result = sf.assess_interval(sf.FullStateControlProtocol("control.exposed.adverse"), left, right)
    assert result.disposition is A.FALSIFIED
    assert "componentwise-full-state-convergence-budget-missed" in result.reason_codes
    assert result.checked_rhs_components + result.checked_algebraic_components == result.checked_derivative_components == 174 * 31


def test_returned_derivative_disagreement_is_a_distinct_complete_control(prepared, tmp_path):
    left = _operand(prepared, tmp_path / "left")
    right = _operand(prepared, tmp_path / "right", horizon=30, changed_derivative=(173, .001))
    result = sf.assess_interval(sf.FullStateControlProtocol("control.exposed.derivative"), left, right)
    assert result.disposition is A.FALSIFIED
    assert "componentwise-returned-derivative-convergence-budget-missed" in result.reason_codes
    assert result.checked_derivative_components == 174 * 31


def test_missing_returned_derivatives_do_not_supply_interpolated_convergence(prepared, tmp_path):
    left = _operand(prepared, tmp_path / "left", derivatives=False)
    right = _operand(prepared, tmp_path / "right", horizon=30, derivatives=False)
    result = sf.assess_interval(sf.FullStateControlProtocol("control.exposed.missing"), left, right)
    assert result.disposition is A.UNEVALUABLE
    assert "native-derivative-or-covered-interpolation-block-unavailable" in result.reason_codes
    assert result.query_count == 31 and result.checked_derivative_components == 0
    assert result.checked_rhs_components + result.checked_algebraic_components == 174
    assert result.derived_state_components == 0


def test_original_custody_substitution_refuses_before_numerical_comparison(prepared, tmp_path):
    left = _operand(prepared, tmp_path / "left")
    right = _operand(prepared, tmp_path / "right", horizon=30)
    with pytest.raises(ValueError, match="actual definition"):
        sf.assess_interval(sf.FullStateControlProtocol("control.exposed.custody"), left,
            replace(right, summary=replace(right.summary, native_definition=left.summary.native_definition)))
    with pytest.raises(ValueError, match="materialized"):
        sf.assess_interval(sf.FullStateControlProtocol("control.exposed.custody"), left,
            replace(right, frame=replace(right.frame, raw_return=None)))


def test_extrapolation_and_changed_native_operands_are_not_convergence_controls(prepared, tmp_path):
    left = _operand(prepared, tmp_path / "left")
    right = _operand(prepared, tmp_path / "right", horizon=30)
    control = sf.FullStateControlProtocol("control.exposed.refusal")
    with pytest.raises(ValueError, match="extrapolate"):
        sf.assess_interval(control, left, right, end_s=D(31))
    with pytest.raises(ValueError):
        replace(control, receiver_spacing_s=D(2))
    with pytest.raises(ValueError):
        replace(control, receiver_spacing_s=True)
    result = sf.assess_interval(control, left, right, start_s=D(10), end_s=D(20))
    assert result.disposition is A.SATISFIED and result.query_count == 11
    assert "LOCAL_OVERLAP_CONTROL" in result.scope
    with pytest.raises(ValueError):
        replace(result, checked_rhs_components=0, checked_algebraic_components=0, checked_derivative_components=0)
    with pytest.raises(ValueError, match="physics, mesh"):
        sf.assess_interval(control, left, replace(right, protocol=replace(right.protocol, particle_points=41)))


def test_selected_exact_rational_boundaries_survive_outward_projection(prepared, tmp_path):
    left = _operand(prepared, tmp_path / "left")
    right = _operand(prepared, tmp_path / "right", horizon=30)
    result = sf.assess_interval(sf.FullStateControlProtocol("control.exposed.rational"), left, right,
        start_s=Fraction(1, 3), end_s=Fraction(2, 3))
    assert result.exact_interval_start == (1, 3) and result.exact_interval_end == (2, 3)
    assert result.query_count == 2 and result.disposition is A.SATISFIED
    with pytest.raises(ValueError, match="exact rational"):
        replace(result, exact_interval_start=(1, 4))


def test_control_import_does_not_load_native_battery_or_numeric_engine():
    result = subprocess.run((sys.executable, "-c", "import sys; import empirical_lawhood.adapters.methods.battery_refined_inquiry.segmented_fidelity; assert 'pybamm' not in sys.modules; assert 'numpy' not in sys.modules"),
        capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr


def test_exact_native_and_derived_hermite_values_enclose_independent_rational_math():
    values = tuple(float(value).hex() for value in (1, 5, -2, 2))
    derivatives = tuple(float(value).hex() for value in (2, 2, 2, 2))
    block = native.FullStateBlock((float(0).hex(), float(2).hex()), 2, values, derivatives)
    class Payload:
        blocks = (block,)
    for clock in (Fraction(0), Fraction(1, 3), Fraction(1), Fraction(2)):
        for at, (state, derivative, interpolated) in enumerate(sf._snapshot(Payload(), clock)):
            exact = Fraction(1 if at == 0 else -2) + 2 * clock
            with localcontext() as context:
                context.prec = 160
                independent = D(exact.numerator) / D(exact.denominator)
                assert state[0] <= independent <= state[1]
                assert derivative[0] <= 2 <= derivative[1]
            assert interpolated == (clock not in (Fraction(0), Fraction(2)))


def test_outward_arithmetic_uncertainty_is_retained_instead_of_rounded_admission():
    with localcontext() as context:
        context.prec = 160
        left = D("1e-8") - D("1e-70"), D("1e-8") + D("1e-70")
    low, high, status = sf._residual(left, (D(0), D(0)), D("1e-8"), D("1e-80"))
    assert low <= 1 <= high and status is A.UNEVALUABLE
