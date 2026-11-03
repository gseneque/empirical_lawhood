# SPDX-License-Identifier: MPL-2.0
"""Explicit comparison weights and provenance controls; no scientific acquisition."""
from dataclasses import replace
from decimal import Decimal as D
from fractions import Fraction as F
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace as N

import pytest

from empirical_lawhood.adapters.methods.battery_refined_inquiry import forecast_state_control as state
from empirical_lawhood.adapters.methods.battery_refined_inquiry import forecast_step_control as step
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from tests.test_battery_forecast_step_control import selected as selected_fixture
from tests.test_battery_forecast_step_control import failed_assignment_evidence, config as config_fixture


@pytest.fixture
def selected():
    original, roster, policy = selected_fixture.__wrapped__()
    control = state.ForecastStateControl('control.exposed-fixed-budget', policy,
        sha256(Path(state.local.__file__).read_bytes()).hexdigest(), sha256(Path(state.paired.__file__).read_bytes()).hexdigest())
    return original, roster, control


def test_known_zero_call_failure_absence_is_usable_only_as_adverse_metadata(selected, tmp_path):
    original, roster, control = selected
    selected_step = original, roster, control.native_policy
    config = config_fixture.__wrapped__(selected_step)
    metadata = failed_assignment_evidence(selected_step, config, tmp_path)
    evidence = N(native_receipt=metadata.original_native_receipt,
        trace=N(config=config, disposition='TECHNICAL_FAILURE', segments=(), backend_solve_calls=0))
    assert state.require_forecast_assignment(control, roster, metadata, evidence) is None
    for changed in (N(config=config, disposition='TARGET_REACHED', segments=(), backend_solve_calls=0),
            N(config=config, disposition='TECHNICAL_FAILURE', segments=(N(),), backend_solve_calls=1)):
        with pytest.raises(ValueError, match='absent forecast assignment'):
            state.require_forecast_assignment(control, roster, metadata, N(native_receipt=metadata.original_native_receipt, trace=changed))


def test_new_protocol_states_fixed_weights_and_original_protocol_bytes_unchanged(selected):
    control = selected[2]
    old = control.algorithm_control
    historical = old.canonical_bytes()
    state.require_algorithm_sources(control)
    assert 'SEPARATELY_DECLARED_FIXED' in control.comparison_weights
    assert 'COMMON_SELECTED_NATIVE_ATOL' in old.state_weights
    assert old.canonical_bytes() == historical
    assert decode_canonical_bytes(control.canonical_bytes(), type(control), maximum_bytes=None) == control


def test_exact_independent_arithmetic_confirms_fixed_budget_differs_from_native_solver(selected):
    _, roster, control = selected
    config = roster.configurations[0]
    left, right = (D(0), D(0)), (D('1e-9'), D('1e-9'))
    native = state.local._residual(left, right, config.atol, config.rtol)
    expected = state.local._residual(left, right, D('1e-8'), D('1e-7'))
    assert native[2] is A.FALSIFIED and expected[2] is A.SATISFIED
    original_algorithm = state.local._residual
    with state._fixed_arithmetic(control, config):
        actual = state.local._residual(left, right, config.atol, config.rtol)
    assert actual == expected and state.local._residual is original_algorithm
    ratio = F(D('1e-9')) / (F(D('1e-8')) + F(D('1e-7')) * F(D('1e-9')))
    assert F(actual[0]) <= ratio <= F(actual[1])


@pytest.mark.parametrize('damage', ('rtol', 'atol'))
def test_undeclared_weight_request_refuses_and_restores_algorithm(selected, damage):
    config = selected[1].configurations[0]
    atol, rtol = (D('1e-8'), config.rtol) if damage == 'atol' else (config.atol, D('1e-7'))
    original_algorithm = state.local._residual
    with pytest.raises(ValueError, match='undeclared native weights'):
        with state._fixed_arithmetic(selected[2], config):
            state.local._residual((F(0), F(0)), (F(1), F(1)), atol, rtol)
    assert state.local._residual is original_algorithm


@pytest.mark.parametrize('field', ('interval_algorithm_source_sha256', 'stream_algorithm_source_sha256'))
def test_wrong_algorithm_source_refuses_before_hooks(selected, field):
    control = replace(selected[2], **{field: 'a' * 64})
    original_algorithm, original_interval = state.local._residual, state.local.assess_interval
    with pytest.raises(ValueError, match='algorithm source'):
        state.require_algorithm_sources(control)
    assert state.local._residual is original_algorithm and state.local.assess_interval is original_interval


def test_wrong_native_policy_refuses_before_any_scientific_assessment(selected):
    control = selected[2]
    operand = N(configuration=N(native=N(policy=step.identity(selected[0], 'roster_id'))))
    with pytest.raises(ValueError, match='selected native policy'):
        state.assess_interval(control, operand, operand)


def test_missing_actual_complete_assignment_refuses_before_stream_consumption(selected):
    control, roster = selected[2], selected[1]
    with pytest.raises(ValueError, match='both complete actual'):
        state.assess_streams(control, roster, None, None, ())
    with pytest.raises(ValueError, match='actual completed assignment'):
        state.require_forecast_assignment(control, roster, None, None)
