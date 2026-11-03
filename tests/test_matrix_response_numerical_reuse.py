# SPDX-License-Identifier: MPL-2.0
# ruff: noqa: F811
"""Supplied-array numerical reuse; no scientific/native custody acceptance.

Scheduled score physical/response identities are two explicit metadata seams.
All source/history/causal guards,48 independent transition controls and240
loss cells remain real. Original-body parity is retained separately on EL.
"""
from collections import Counter
from dataclasses import replace
from decimal import Decimal, localcontext
from hashlib import sha256
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_experimental_programme import prepared_forecast, prepared_response_science as prepared
from empirical_lawhood.adapters.methods.matrix_factor_response import science as linear
from empirical_lawhood.adapters.methods.matrix_scheduled_history import records, response_forecast, response_records, response_science
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_native import native_scheduled_branch
from empirical_lawhood.adapters.simulators.six_matrix_response.model import SixMatrixState
from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays, encode_matrix_arrays
from empirical_lawhood.kernel.provenance import ObjectIdentity
from tests.test_matrix_prepared_response_method import case as prepared_case  # noqa: F401
from tests.test_matrix_prepared_forecast import case as prepared_forecast_case  # noqa: F401
from tests.test_matrix_scheduled_response_forecast import case as scheduled_forecast_case  # noqa: F401
from tests.test_matrix_e3_response_records import case as scheduled_metadata  # noqa: F401


@pytest.fixture(autouse=True)
def _forbid_effects_and_rng(monkeypatch):
    from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
    from empirical_lawhood.infrastructure.native_subwork import ExternalNativeSubworkStore
    from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_history, parameter_history_segments, parameter_source
    def refused(*_args, **_kwargs):
        pytest.fail("numerical-only control entered native custody, acquisition or RNG")
    for cls, name in ((ExternalNativeEffectContactStore, "begin"), (ExternalNativeSubworkStore, "begin"),
            (ExternalNativeSubworkStore, "contact")):
        monkeypatch.setattr(cls, name, refused)
    for module, name in ((parameter_history_segments, "acquire_parameter_segment"),
            (parameter_source, "acquire_parameter_history"), (parameter_history, "advance_parameter_pair")):
        monkeypatch.setattr(module, name, refused)
    for name in ("Generator", "PCG64DXSM", "default_rng"):
        monkeypatch.setattr(np.random, name, refused)


def _flags(context):
    return {signal.__name__: state for signal, state in context.flags.items()}


def _evaluate(call, precision):
    with localcontext() as context:
        context.prec = precision
        context.clear_flags()
        value = call()
        return value, _flags(context)


def _prepared_operands(case, damage):
    args = list(case[:-1])
    arrays = prepared.propagate_prepared_responses(*case)
    if damage == "adverse":
        key = next(name for name in arrays if name.startswith("branch.fine.") and ".plus.momenta" in name)
        arrays[key] = arrays[key].copy()
        arrays[key][1, 0, 0, 0, 0] += .01
    elif damage == "missing":
        arrays.pop(next(name for name in arrays if name.startswith("branch.") and name.endswith(".positions")))
    elif damage == "nonfinite":
        frozen = {name: value.copy() for name, value in decode_matrix_arrays(args[7], args[6]).items()}
        frozen["primary_full_coupled"][0, 0, 0] = np.nan
        raw, members = encode_matrix_arrays(frozen, nonfinite_members=("primary_full_coupled",))
        args[6] = replace(args[6], array_artifact=replace(args[6].array_artifact,
            sha256=sha256(raw).hexdigest(), size_bytes=len(raw)), members=members)
        args[7] = raw
    return tuple(args), arrays


def _scheduled_operands(case, prepared_case, monkeypatch, damage):
    """Seedless received-equation fixture, not a native completion or forecast.

    Real retained legacy prefix records provide source and ancestry identities.
    Two SimpleNamespace records supply only the caller-owned numerical metadata
    seam. No receipt, native event, issue, grant or qualification is fabricated.
    """
    source, history, causal = case.source, case.old_history, case.old_causal
    protocol = replace(case.protocol, actions=tuple(replace(action, amplitude=Decimal(".01"),
        pulse_steps=1, force_norm=Decimal(1)) for action in case.protocol.actions), horizon_steps=(1, 2, 3))
    prefix = decode_matrix_arrays(case.native_raw, history.arrays)
    received = decode_matrix_arrays(prepared_case[7], prepared_case[6])
    frozen = {name: value.copy() for name, value in received.items()}
    panels = case.panels
    arrays = {}
    for panel in panels:
        for label, count in (("primary", 3), ("fine", 6), ("bridge", 3)):
            arrays["noise." + panel.panel_id + "." + label] = np.zeros((count, 2, 3, 4, 4), dtype="<c16")
    for branch, view, panel, action, sign in response_records.branch_census(protocol, panels):
        label, mult = view.lower(), 1 if view == "PRIMARY" else 2
        start = mult * source.policy.cutoff_tick
        state = SixMatrixState(2, prefix[label + "_positions"][-1], prefix[label + "_momenta"][-1],
            start, *source.coordinate.couplings(start, refinement=mult))
        values = native_scheduled_branch(state, coordinate=source.coordinate, refinement=mult,
            direction=frozen["forces"][protocol.actions.index(action)],
            amplitude=0 if sign == "HOLD" else float(action.amplitude) * (1 if sign == "PLUS" else -1),
            pulse_steps=mult * action.pulse_steps, innovations=arrays["noise." + panel.panel_id + "." + label])
        arrays.update({"branch." + branch + "." + name: value for name, value in values.items()})
    error = records.identity(case.error)
    physical = SimpleNamespace(forecast_id="forecast.exposed.reuse-metadata", source=records.identity(source),
        causal_prefix=records.identity(causal), protocol=ObjectIdentity.from_record(protocol.protocol_id, protocol),
        mechanical_model=ObjectIdentity.from_record(protocol.mechanical_model.model_id, protocol.mechanical_model), disposition="AVAILABLE")
    physical_id = ObjectIdentity(physical.forecast_id, response_records.ScheduledResponseForecast.SCHEMA, "1.0.0", "1" * 64)
    responses = SimpleNamespace(response_id="responses.exposed.reuse-metadata", source=records.identity(source),
        causal_prefix=records.identity(causal), physical_forecast=physical_id, error_forecast=error,
        protocol=physical.protocol, branch_ids=tuple(row[0] for row in response_records.branch_census(protocol, panels)), disposition="COMPLETED")
    responses_id = ObjectIdentity(responses.response_id, response_records.ScheduledResponseNative.SCHEMA, "1.0.0", "2" * 64)
    actual_pin = ObjectIdentity.from_record
    def pin(name, value):
        if value is physical:
            return physical_id
        if value is responses:
            return responses_id
        return actual_pin(name, value)
    monkeypatch.setattr(ObjectIdentity, "from_record", staticmethod(pin))
    if damage == "adverse":
        key = next(name for name in arrays if name.startswith("branch.fine.") and ".plus.momenta" in name)
        arrays[key] = arrays[key].copy()
        arrays[key][1, 0, 0, 0, 0] += .01
    elif damage == "missing":
        arrays.pop(next(name for name in arrays if name.startswith("branch.") and name.endswith(".positions")))
    elif damage == "nonfinite":
        frozen["primary_full_coupled"][0, 0, 0] = np.nan
    elif damage == "nonuse":
        responses.disposition = physical.disposition = "UNEVALUABLE"
        arrays = {"unentered_branches": np.arange(48, dtype="<i8")}
    return (source, causal, history, prefix, physical, frozen, protocol, panels, responses, arrays), error


def _projection_counter(monkeypatch):
    original, counts = np.einsum, Counter()
    def observed(subscripts, *args, **kwargs):
        if subscripts == "rpsjab,psjab->r":
            counts["truths"] += 1
        return original(subscripts, *args, **kwargs)
    monkeypatch.setattr(np, "einsum", observed)
    return counts


def _assert_cells(value, *, projections, negative=False, nonfinite=False, nonuse=False):
    assert len(value.cells) == 240 and len(value.cumulative_log_errors) == 15
    assert len(value.controls) == (0 if nonuse else 48)
    if nonuse:
        assert projections == 0 and not value.numerical_pass
        assert all(cell.actual_odd_responses is None for cell in value.cells)
        assert value.cumulative_log_errors == (None,) * 15
    else:
        assert projections == 48
        truths = {}
        for cell in value.cells:
            key = cell.view, cell.panel_id, cell.action_id, cell.horizon_tick
            assert truths.setdefault(key, cell.actual_odd_responses) == cell.actual_odd_responses
        assert len(truths) == 48
        assert value.numerical_pass is not negative
        if negative:
            assert value.cumulative_log_errors == (None,) * 15
        elif nonfinite:
            assert value.disposition == "PARTIAL" and any(point is None for point in value.cumulative_log_errors)
        else:
            assert value.disposition == "FINITE" and all(point is not None for point in value.cumulative_log_errors)


@pytest.mark.parametrize("precision", (28, 80))
@pytest.mark.parametrize("damage", ("finite", "adverse", "nonfinite", "missing"))
def test_prepared_truth_projection_keeps_all_cells_and_context(prepared_case, monkeypatch, precision, damage):
    args, arrays = _prepared_operands(prepared_case, damage)
    before = {name: value.tobytes() for name, value in arrays.items()}
    count = _projection_counter(monkeypatch)
    call = lambda: prepared.assess_prepared_responses(*args, arrays, record_id="readout.exposed.reuse")
    if damage == "missing":
        with pytest.raises(ValueError, match="complete48"):
            _evaluate(call, precision)
        assert count["truths"] == 0
    else:
        value, flags = _evaluate(call, precision)
        _assert_cells(value, projections=count["truths"], negative=damage == "adverse", nonfinite=damage == "nonfinite")
        assert not flags["InvalidOperation"]
    assert before == {name: value.tobytes() for name, value in arrays.items()}


@pytest.mark.parametrize("precision", (28, 80))
@pytest.mark.parametrize("damage", ("finite", "adverse", "nonfinite", "missing", "nonuse"))
def test_scheduled_truth_projection_keeps_real_full_branch_math_and_metadata_seam(
        scheduled_metadata, prepared_case, monkeypatch, precision, damage):
    args, error = _scheduled_operands(scheduled_metadata, prepared_case, monkeypatch, damage)
    count = _projection_counter(monkeypatch)
    call = lambda: response_science.assess_paired_response_arrays(*args,
        error_forecast=error, score_id="score.exposed.reuse")
    if damage == "missing":
        with pytest.raises(ValueError, match="complete branch"):
            _evaluate(call, precision)
        assert count["truths"] == 0
    else:
        value, flags = _evaluate(call, precision)
        _assert_cells(value, projections=count["truths"], negative=damage == "adverse",
            nonfinite=damage == "nonfinite", nonuse=damage == "nonuse")
        assert not flags["InvalidOperation"]


class _CountingModes(np.ndarray):
    def __new__(cls, values, hessian, counts):
        result = np.asarray(values).view(cls)
        result._hessian, result._counts = hessian, counts
        return result
    def __array_finalize__(self, other):
        self._hessian = getattr(other, "_hessian", None)
        self._counts = getattr(other, "_counts", None)
    def __matmul__(self, other):
        if other is self._hessian:
            self._counts["reductions"] += 1
        return super().__matmul__(other)


def _linear_operands(case):
    source, _, _, _, protocol, _, forecast, raw, _ = case
    frozen = decode_matrix_arrays(raw, forecast)
    design = SimpleNamespace(view=source.primary_view, horizon_steps=protocol.horizon_steps)
    hessian = np.diag(np.linspace(.25, 1.25, 96)).astype("<f8")
    return design, np.eye(96, dtype="<f8"), hessian, frozen["forces"], frozen["receivers"], protocol.actions


@pytest.mark.parametrize("precision", (28, 80))
def test_reduced_operator_reuses_one_exact_matrix_product_and_keeps_distinct_forces(prepared_case, precision):
    d, values, hessian, forces, receivers, actions = _linear_operands(prepared_case)
    expected_counts, counts = Counter(), Counter()
    expected_modes = _CountingModes(values, hessian, expected_counts)
    modes = _CountingModes(values, hessian, counts)
    expected, expected_flags = _evaluate(lambda: np.asarray([linear._linear_response(d, expected_modes, hessian,
        force, receivers, action) for force, action in zip(forces, actions, strict=True)]), precision)
    actual, flags = _evaluate(lambda: np.asarray(linear._linear_responses(d, modes, hessian, forces, receivers, actions)), precision)
    assert actual.dtype == expected.dtype and actual.shape == expected.shape and actual.tobytes() == expected.tobytes()
    assert flags == expected_flags and expected_counts["reductions"] == 4 and counts["reductions"] == 1
    changed = forces.copy()
    observed = next(index for index, action in enumerate(actions) if action.role == "TRACE")
    changed[observed] *= 2
    fresh, _ = _evaluate(lambda: np.asarray(linear._linear_responses(d, modes, hessian, changed, receivers, actions)), precision)
    assert counts["reductions"] == 2 and not np.array_equal(fresh[observed], actual[observed])
    others = tuple(index for index in range(len(actions)) if index != observed)
    assert np.array_equal(fresh[list(others)], actual[list(others)])
    changed_hessian = hessian.copy()
    changed_hessian[0, 0] += .25
    fresh_modes = _CountingModes(values, changed_hessian, counts)
    changed_result, _ = _evaluate(lambda: np.asarray(linear._linear_responses(d, fresh_modes,
        changed_hessian, forces, receivers, actions)), precision)
    changed_expected = np.asarray([linear._linear_response(d, values, changed_hessian, force, receivers, action)
        for force, action in zip(forces, actions, strict=True)])
    assert counts["reductions"] == 3 and changed_result.tobytes() == changed_expected.tobytes()
    assert not np.array_equal(changed_result, actual)


@pytest.mark.parametrize("sizes", ((0, 0), (3, 4), (4, 3)))
def test_reduced_operator_retains_empty_and_strict_zip_length_behavior(prepared_case, sizes):
    d, modes, hessian, forces, receivers, actions = _linear_operands(prepared_case)
    force_count, action_count = sizes
    if sizes == (0, 0):
        assert linear._linear_responses(d, modes, hessian, forces[:0], receivers, actions[:0]) == []
    else:
        with pytest.raises(ValueError, match=r"zip\(\) argument"):
            linear._linear_responses(d, modes, hessian, forces[:force_count], receivers, actions[:action_count])


def test_reduced_operator_preserves_first_action_error_before_later_zip_length(prepared_case, monkeypatch):
    d, modes, hessian, forces, receivers, actions = _linear_operands(prepared_case)
    sentinel = RuntimeError("literal first force failure")
    order = []
    def first_force(_value):
        order.append("force-math")
        raise sentinel
    def selected():
        order.append("force-yield")
        yield forces[0]
        order.append("later-force")
    monkeypatch.setattr(linear, "native_position_coordinates", first_force)
    with pytest.raises(RuntimeError) as caught:
        linear._linear_responses(d, modes, hessian, selected(), receivers, actions)
    assert caught.value is sentinel and order == ["force-yield", "force-math"]


@pytest.mark.parametrize("which", ("prepared", "scheduled"))
def test_real_forecasts_keep_full_cold_reproof_and_array_bytes(
        which, prepared_forecast_case, scheduled_forecast_case, monkeypatch):
    if which == "prepared":
        raw, forecast = prepared_forecast.forecast(*prepared_forecast_case, artifact_id="array.exposed.operator-reuse")
        values = decode_matrix_arrays(raw, forecast.arrays)
        monkeypatch.setattr(response_forecast, "_hessian", lambda *_: pytest.fail("cold entry produced Hessian"))
        monkeypatch.setattr(np.linalg, "eigh", lambda *_: pytest.fail("cold entry produced eigenvectors"))
        observed_raw, observed = prepared_forecast.forecast(*prepared_forecast_case,
            artifact_id=forecast.arrays.array_artifact.artifact_id, retained=values, raw=raw)
    else:
        c = scheduled_forecast_case
        raw, forecast, values = c.raw, c.result, c.retained
        monkeypatch.setattr(response_forecast, "_hessian", lambda *_: pytest.fail("cold entry produced Hessian"))
        monkeypatch.setattr(np.linalg, "eigh", lambda *_: pytest.fail("cold entry produced eigenvectors"))
        observed_raw, observed = response_forecast.forecast(c.protocol, c.causal, c.arrays, c.templates,
            artifact_id=forecast.arrays.array_artifact.artifact_id, retained=values, raw=raw)
    assert observed_raw == raw and observed == forecast and observed.canonical_bytes() == forecast.canonical_bytes()


def test_truth_cache_is_local_to_each_received_array_invocation(prepared_case, monkeypatch):
    args, arrays = _prepared_operands(prepared_case, "finite")
    count = _projection_counter(monkeypatch)
    first = prepared.assess_prepared_responses(*args, arrays, record_id="readout.exposed.freshness")
    key = next(name for name in arrays if name.startswith("branch.fine.") and ".plus.momenta" in name)
    arrays[key] = arrays[key].copy()
    arrays[key][2 * args[4].horizon_steps[0], 0, 0, 0, 0] += .01
    second = prepared.assess_prepared_responses(*args, arrays, record_id="readout.exposed.freshness")
    assert count["truths"] == 96 and first.canonical_bytes() != second.canonical_bytes()
    assert first.numerical_pass and not second.numerical_pass
    assert any(a.actual_odd_responses != b.actual_odd_responses for a, b in zip(first.cells, second.cells, strict=True))
