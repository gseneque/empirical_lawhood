# SPDX-License-Identifier: MPL-2.0
"""Independent work identities and actual native split-boundary controls."""
from dataclasses import replace

import numpy as np
import pytest

from empirical_lawhood.methods.protocol_work import ProtocolWorkAccount
from empirical_lawhood.domains.matrix.model_free import native, science
from empirical_lawhood.domains.matrix.six_matrix_response.gradients import reference_action_terms
from empirical_lawhood.domains.matrix.six_matrix_response.parameter_derivatives import parameters
from tests.test_matrix_model_free_science import tiny_settings


@pytest.mark.numerical(oracle='W = (k_final-k_initial) q^2/2 for fixed-position quadratic parameter jumps')
def test_quadratic_protocol_work_is_signed_and_telescopes_at_fixed_position():
    ledger = ProtocolWorkAccount('joule', 'fixed-position-jump')
    def energy(q, k):
        return .5 * k * q ** 2
    ledger.record_jump(energy, 3., 2., 5.)
    ledger.record_jump(energy, 3., 5., 1.)
    assert ledger.signed_work == pytest.approx(-4.5)
    assert ledger.absolute_jump_work == pytest.approx(31.5)
    assert ledger.completed_jumps == 2
    assert ledger.potential_evaluations_completed == 4


def test_work_failure_keeps_completed_prefix_and_attempted_evaluations():
    ledger = ProtocolWorkAccount('joule', 'fixed-position-jump')
    ledger.record_jump(lambda q, k: q * k, 2., 1., 3.)
    def failed(q, k):
        if k == 7:
            raise FloatingPointError('unavailable potential')
        return q * k
    with pytest.raises(FloatingPointError):
        ledger.record_jump(failed, 2., 3., 7.)
    assert ledger.signed_work == 4
    assert ledger.potential_evaluations_attempted == 4
    assert ledger.potential_evaluations_completed == 3
    assert ledger.summary(complete=False)['complete'] is False


@pytest.mark.numerical(oracle='Independent reference native action evaluated at actual post-AOA position and old/new full Hamiltonian coefficients')
def test_native_work_uses_actual_parameter_update_position_and_preserves_trajectory():
    settings = tiny_settings()
    c, row = settings['native'], settings['native']['coordinates'][0]
    coord, state = native.target_state(c, row)
    state = replace(state, momenta=2. * native.hermitian_noise(rng=native.rng(41, 9), q=2))
    noise = native.hermitian_noise(rng=native.rng(42, 9), q=2)
    targets = (state.alpha_tilde_x * .8, state.alpha_tilde_y * .7)
    ledger = native.protocol_work_account()
    advanced = native.step(state, coord, noise, couplings=targets, protocol_work=ledger)
    ordinary = native.step(state, coord, noise, couplings=targets)
    np.testing.assert_array_equal(advanced.positions, ordinary.positions)
    np.testing.assert_array_equal(advanced.momenta, ordinary.momenta)
    previous, current = parameters(state, coord.member), parameters(advanced, coord.member)
    expected = reference_action_terms(advanced.positions, current).total - reference_action_terms(advanced.positions, previous).total
    incorrect_incoming = reference_action_terms(state.positions, current).total - reference_action_terms(state.positions, previous).total
    assert ledger.signed_work == pytest.approx(expected, abs=2e-12)
    assert abs(expected - incorrect_incoming) > 1e-5
    assert ledger.completed_jumps == 1


@pytest.mark.numerical(oracle='A constant Hamiltonian parameter has identically zero parameter work')
def test_constant_parameters_have_zero_work_and_no_extra_potential_calls():
    settings = tiny_settings()
    c, row = settings['native'], settings['native']['coordinates'][0]
    coord, state = native.target_state(c, row)
    ledger = native.protocol_work_account()
    native.step(state, coord, native.hermitian_noise(rng=native.rng(5, 10), q=2), protocol_work=ledger)
    assert ledger.signed_work == ledger.potential_evaluations_attempted == 0


def test_failed_preparation_retains_protocol_prefix_and_exact_force_counter(monkeypatch):
    settings = tiny_settings()
    ordinary = native.guard
    def fail_after_two(state, config):
        ordinary(state, config)
        if state.step_index == 2:
            raise FloatingPointError('two completed steps then refusal')
    monkeypatch.setattr(native, 'guard', fail_after_two)
    result = science.acquire_root(settings, 15, 'M1')
    assert result['status'] == 'PARTIAL'
    assert result['work_accounting']['counts_are_lower_bounds']
    for case in result['cases']:
        assert case['status'] == 'UNAVAILABLE'
        assert case['preparation_completed_ticks'] == 2
        assert case['preparation_force_evaluations'] == 3
        assert case['protocol_work']['complete'] is False
        assert case['protocol_work']['potential_evaluations_completed'] == 4
        assert set(case['checkpoints']) == {'fixed', 'triggered'}
    assert result['work_accounting']['native_force_evaluations'] == 6
    assert result['work_accounting']['native_energy_evaluations'] == 8


def test_service_failure_retains_handoff_work_and_completed_force_calls(monkeypatch):
    settings = tiny_settings()
    c, row = settings['native'], settings['native']['coordinates'][0]
    _, origin = native.target_state(c, row)
    origin = replace(origin, alpha_tilde_x=0., alpha_tilde_y=0.)
    forces, receivers = native.physical_chart(c, 7)
    ordinary, calls = native.guard, 0
    def refuse(state, config):
        nonlocal calls
        ordinary(state, config)
        calls += 1
        if calls == 4:
            raise FloatingPointError('future interrupted after first common step')
    monkeypatch.setattr(native, 'guard', refuse)
    with pytest.raises(native.NativeResponseFailure) as caught:
        native.paired_response(c, row, origin, forces[:, :1], receivers, 7, 0)
    partial = caught.value.partial_accounting
    assert partial['native_force_evaluations'] == 7
    assert partial['native_energy_evaluations'] == 6
    assert len(partial['protocol_handoff_work']) == 3
    assert all(row['completed_parameter_jumps'] == 1 for row in partial['protocol_handoff_work'])


def test_hessian_block_failure_retains_completed_columns(monkeypatch):
    settings = tiny_settings()
    coord, state = native.target_state(settings['native'], settings['native']['coordinates'][0])
    action = native.action_at(state, coord.member)
    ordinary, calls = native.hessian_image, 0
    def image(*args):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise FloatingPointError('second column failed')
        return ordinary(*args)
    monkeypatch.setattr(native, 'hessian_image', image)
    with pytest.raises(FloatingPointError):
        action(np.eye(96)[:, :3])
    assert action.real_hessian_evaluations == 1 and action.real_hessian_attempts == 2
