# SPDX-License-Identifier: MPL-2.0
"""Exposed actual scientific request guards; no battery native acquisition."""
from dataclasses import replace
from decimal import Decimal as D
import json
from types import SimpleNamespace as N

import pytest

from empirical_lawhood.adapters.methods.battery_observation_inquiry import precision_assessment as consumer
from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_science as science
from empirical_lawhood.adapters.methods.battery_segmented_inquiry import evidence_stream as stream
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from tests.test_battery_precision_control import control as control_fixture, witness
from tests.test_battery_segmented_science import prepared as prepared_fixture, _segment_fixture

control = control_fixture
prepared = prepared_fixture


@pytest.fixture
def selected(control, prepared, tmp_path):
    config, protocol, layout, summary, receipt, records = _segment_fixture(prepared, tmp_path)
    assignment, _, _ = witness(control)
    assignment = replace(assignment, native_configuration=science.identity(config, "config_id"))
    primitive = json.loads(records["request"].primitive_json)
    primitive["solver"] = json.loads(assignment.actual_solver_json)
    request = replace(records["request"], primitive_json=canonical_json_bytes(primitive).decode())
    return N(control=control, assignment=assignment, config=config, layout=layout,
        summary=summary, request=request, full_state=records["full_state"])


def assess(selected, **changed):
    arguments = dict(control=selected.control, assignment=selected.assignment, config=selected.config,
        layout=selected.layout, summary=selected.summary, request=selected.request,
        full_state=selected.full_state, previous_terminal=None)
    arguments.update(changed)
    return consumer._policy_request_reasons(science._request_reasons, **arguments)


def test_declared_native_tolerance_is_distinct_from_unchanged_comparison_weights(selected):
    old = science._request_reasons(selected.config, selected.layout, selected.summary,
        selected.request, selected.full_state, None)
    assert old == {"actual-native-solver-type-or-tolerances-disagree"}
    assert assess(selected) == set()
    assert (selected.config.rtol, selected.config.atol) == (D("1e-7"), D("1e-8"))


@pytest.mark.parametrize("damage", ("rtol", "atol", "dt_max", "calc_ic", "type"))
def test_any_actual_solver_option_or_type_substitution_refuses(selected, damage):
    primitive = json.loads(selected.request.primitive_json)
    solver = primitive["solver"]
    if damage in ("rtol", "atol"):
        solver[damage] = {"binary64": float(1e-7 if damage == "rtol" else 1e-8).hex()}
    elif damage == "type":
        solver[damage] = "EXPOSED_WRONG_SOLVER"
    else:
        solver["options"][damage] = False if damage == "calc_ic" else {"binary64": float(2).hex()}
    request = replace(selected.request, primitive_json=canonical_json_bytes(primitive).decode())
    with pytest.raises(ValueError, match="actual complete solver options"):
        assess(selected, request=request)


@pytest.mark.parametrize("damage", ("requested_start", "current", "source", "save"))
def test_unchanged_scientific_primitive_guards_still_falsify(selected, damage):
    primitive = json.loads(selected.request.primitive_json)
    if damage == "requested_start":
        primitive[damage] = {"binary64": float(5).hex()}
    elif damage == "current":
        primitive["inputs"]["Inquiry active charging magnitude [A]"] = {"binary64": float(3.395).hex()}
    elif damage == "source":
        primitive["model_expression_sha256"] = "f" * 64
        assert primitive["model_expression_sha256"] != selected.layout.model_expression_sha256
    else:
        primitive["save"] = True
    request = replace(selected.request, primitive_json=canonical_json_bytes(primitive).decode())
    assert "actual-native-request-changes-scientific-primitive-operands" in assess(selected, request=request)


def test_actual_returned_scalar_input_guard_still_falsifies(selected):
    full = replace(selected.full_state, returned_inputs_json="[]\n")
    assert assess(selected, full_state=full) == {"actual-native-returned-inputs-disagree-with-frozen-regime"}


@pytest.mark.parametrize("damage", ("missing-control", "missing-assignment", "wrong-config", "wrong-control"))
def test_missing_or_wrong_policy_assignment_refuses(selected, damage):
    changed = dict(control=None) if damage == "missing-control" else dict(assignment=None) if damage == "missing-assignment" else dict(
        control=replace(selected.control, control_id=selected.control.control_id + ".wrong")) if damage == "wrong-control" else dict(
        assignment=replace(selected.assignment, native_configuration=replace(selected.assignment.native_configuration, object_fingerprint="0" * 64)))
    with pytest.raises(ValueError):
        assess(selected, **changed)


def test_missing_complete_original_refuses_without_hook_mutation():
    original_guard, original_reader = science._request_reasons, stream.read_frames
    with pytest.raises(ValueError, match="complete original"):
        with consumer.precision_consumer_scope(None):
            pytest.fail("missing original reached PURE consumer scope")
    assert science._request_reasons is original_guard and stream.read_frames is original_reader


def test_original_guard_and_reader_restore_on_adverse_exit(selected, monkeypatch):
    monkeypatch.setattr(consumer, "_require_original", lambda original: {selected.assignment.native_configuration: selected.assignment})
    original = N(control=selected.control, actual_assignments=(selected.assignment,))
    original_guard, original_reader = science._request_reasons, stream.read_frames
    with pytest.raises(RuntimeError, match="exposed adverse exit"):
        with consumer.precision_consumer_scope(original):
            assert science._request_reasons(selected.config, selected.layout, selected.summary,
                selected.request, selected.full_state, None) == set()
            raise RuntimeError("exposed adverse exit")
    assert science._request_reasons is original_guard and stream.read_frames is original_reader
