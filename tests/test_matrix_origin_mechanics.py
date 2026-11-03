# SPDX-License-Identifier: MPL-2.0
"""Analytic and literal controls for the amended origin response construction."""

from dataclasses import replace
from decimal import Decimal
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response import origin_mechanics as owner
from empirical_lawhood.adapters.methods.matrix_factor_response import science
from empirical_lawhood.adapters.simulators.six_matrix_response.shooting import hermitian_basis


POLICY = owner.MatrixIO48Construction('matrix.io48.exposed-control')


def literal_step(q, p, hessian, force, dt, decay):
    # Native kick/drift/OU/drift/kick equations, independent of block formulas.
    p = p + dt / 2 * (force - hessian @ q)
    q = q + dt / 2 * p
    p = decay * p
    q = q + dt / 2 * p
    p = p + dt / 2 * (force - hessian @ q)
    return np.concatenate((q, p))


@pytest.mark.parametrize('dt,decay', ((.001, .999), (.0005, .9995), (.1, 1.)))
def test_discrete_map_matches_both_kicks_and_native_unit_kinetic_mass(dt, decay):
    h = np.asarray([[2., .3], [.3, -1.]])
    forces = np.asarray([[.01, -.03], [.02, .04]])
    a, b = owner.discrete_baoab_maps(h, forces, timestep=dt, decay=decay)
    for index in range(4):
        state = np.eye(4)[index]
        np.testing.assert_allclose(a @ state, literal_step(state[:2], state[2:], h,
            np.zeros(2), dt, decay), atol=1e-15, rtol=1e-14)
    for index in range(2):
        np.testing.assert_allclose(b[:, index], literal_step(np.zeros(2), np.zeros(2), h,
            forces[:, index], dt, decay), atol=1e-15, rtol=1e-14)
    # Free undamped unit force delivers dt momentum and dt**2/2 position.
    _, free_b = owner.discrete_baoab_maps(np.zeros((1, 1)), np.ones((1, 1)), timestep=dt, decay=1.)
    np.testing.assert_allclose(free_b[:, 0], (dt * dt / 2, dt), rtol=1e-15)


def test_harmonic_pulse_response_has_second_order_error_against_independent_exponential():
    from scipy.linalg import expm
    stiffness, gamma, force = 9., .6, .01
    generator = np.asarray([[0., 1.], [-stiffness, -gamma]])
    forced = np.zeros((3, 3))
    forced[:2, :2] = generator
    forced[1, 2] = force
    exact = expm(.112 * generator) @ (expm(.016 * forced) @ np.asarray([0., 0., 1.]))[:2]
    errors = []
    for dt, steps, pulse in ((.001, 128, 16), (.0005, 256, 32)):
        transition, inputs = owner.discrete_baoab_maps(np.asarray([[stiffness]]), np.asarray([[force]]),
            timestep=dt, decay=np.exp(-gamma*dt))
        actual = owner.pulse_responses(transition, inputs, np.eye(2), pulse_steps=(pulse,),
            horizons=(steps,), output_units=np.ones(2))[0, 0]
        errors.append(np.linalg.norm(actual-exact))
        np.testing.assert_allclose(actual, exact, rtol=3e-6, atol=1e-12)
    assert 3.9 < errors[0] / errors[1] < 4.1


@pytest.mark.parametrize('steps', (1, 2, 128, 256))
def test_gramians_and_post_step_impulse_include_both_endpoints(steps):
    a = np.asarray([[1.01, .02], [0., .98]])  # Finite-horizon unstable control.
    b, c = np.asarray([[.3], [.4]]), np.asarray([[.5, -.2]])
    wc, wo = owner.finite_horizon_gramians(a, b, c, steps)
    reach = np.column_stack([np.linalg.matrix_power(a, k) @ b for k in range(steps)])
    observe = np.vstack([c @ np.linalg.matrix_power(a, k) for k in range(steps)])
    np.testing.assert_allclose(wc, reach @ reach.T, rtol=2e-13, atol=1e-13)
    np.testing.assert_allclose(wo, observe.T @ observe, rtol=2e-13, atol=1e-13)
    predictions = owner.pulse_responses(a, b, c, pulse_steps=(1,),
        horizons=tuple(range(1, steps + 1)), output_units=np.ones(1))
    expected = np.asarray([(c @ np.linalg.matrix_power(a, k) @ b).item() for k in range(steps)])
    np.testing.assert_allclose(predictions[0, :, 0], expected, rtol=2e-13, atol=1e-14)
    assert predictions[0, 0, 0] == pytest.approx((c @ b).item())


def test_balanced_full_rank_limit_and_cold_witnesses_without_solvers(monkeypatch):
    a = np.asarray([[1.01, .03], [.01, .97]])
    b, c = np.asarray([[.3], [.4]]), np.asarray([[.5, -.2]])
    result = owner.balance_io48(a, b, c, 128, POLICY)
    assert (result.reachable_rank, result.observable_rank, result.balanced_rank, result.effective_rank) == (2, 2, 2, 2)
    expected = owner.pulse_responses(a, b, c, pulse_steps=(16,), horizons=(16, 32, 128), output_units=np.ones(1))
    actual = owner.pulse_responses(result.transition, result.inputs, result.outputs,
        pulse_steps=(16,), horizons=(16, 32, 128), output_units=np.ones(1))
    np.testing.assert_allclose(actual, expected, rtol=1e-11, atol=1e-12)
    monkeypatch.setattr(np.linalg, 'eigh', lambda *a, **k: pytest.fail('cold reader reran eigensolve'))
    monkeypatch.setattr(np.linalg, 'svd', lambda *a, **k: pytest.fail('cold reader reran SVD'))
    replay = owner.balance_io48(a, b, c, 128, POLICY, retained=result.witnesses)
    assert all(np.array_equal(value, replay.witnesses[key]) for key, value in result.witnesses.items())
    assert replay.projection_condition_bound == result.projection_condition_bound


@pytest.mark.parametrize('damage', ('gramian_c', 'gramian_o', 'controllability_vectors',
    'observability_values', 'hankel_left', 'hankel_values', 'lift', 'reduced_inputs'))
def test_cold_reduction_refuses_changed_numerical_witnesses(damage):
    a, b, c = np.diag([.98, .95]), np.eye(2), np.eye(2)
    result = owner.balance_io48(a, b, c, 128, POLICY)
    changed = {key: value.copy() for key, value in result.witnesses.items()}
    changed[damage].flat[0] += .01
    with pytest.raises(ValueError, match='IO48'):
        owner.balance_io48(a, b, c, 128, POLICY, retained=changed)


def test_large_finite_witnesses_cannot_bypass_residuals_through_norm_overflow():
    a, b, c = np.zeros((1, 1)), np.asarray([[1e100]]), np.asarray([[1e100]])
    result = owner.balance_io48(a, b, c, 1, POLICY)
    owner.balance_io48(a, b, c, 1, POLICY, retained=result.witnesses)
    changed = {key: value.copy() for key, value in result.witnesses.items()}
    changed['gramian_c'] *= 2
    with pytest.raises(ValueError, match='independent numerical reproof'):
        owner.balance_io48(a, b, c, 1, POLICY, retained=changed)


@pytest.mark.parametrize('reachable,observable,rank', ((True, True, 1), (False, True, 0), (True, False, 0)))
def test_lower_rank_and_zero_rank_are_explicit_without_fallback(reachable, observable, rank):
    a = np.diag([1.01, .9, .8])
    b = np.asarray([[float(reachable)], [0.], [0.]])
    c = np.asarray([[float(observable), 0., 0.]])
    result = owner.balance_io48(a, b, c, 128, POLICY)
    assert result.effective_rank == rank
    predictions = owner.pulse_responses(result.transition, result.inputs, result.outputs,
        pulse_steps=(16,), horizons=(16, 128), output_units=np.ones(1))
    expected = owner.pulse_responses(a, b, c, pulse_steps=(16,), horizons=(16, 128), output_units=np.ones(1))
    np.testing.assert_allclose(predictions, expected, rtol=1e-12, atol=1e-12)
    owner.balance_io48(a, b, c, 128, POLICY, retained=result.witnesses)


def test_dimension_cap_degenerate_cutoff_and_nonfinite_gramian_nonuse():
    a, c = np.zeros((50, 50)), np.eye(50)
    result = owner.balance_io48(a, np.diag(np.linspace(1., 2., 50)), c, 1, POLICY)
    assert result.balanced_rank == 50 and result.effective_rank == 48
    with pytest.raises(owner.IO48Unresolved, match='HANKEL_CAP_CUTOFF_UNRESOLVED'):
        owner.balance_io48(a, np.eye(50), c, 1, POLICY)
    with pytest.raises(owner.IO48Unresolved, match='NONFINITE_FINITE_HORIZON_GRAMIANS'):
        owner.balance_io48(np.asarray([[1e20]]), np.ones((1, 1)), np.ones((1, 1)), 128, POLICY)


def test_projection_condition_policy_refuses_numerically_unusable_similarity():
    # Reachable and observable lines are almost orthogonal. Their cross value
    # is above the absolute threshold, but the oblique projector is unusable.
    a = np.zeros((2, 2))
    b, c = np.asarray([[1.], [0.]]), np.asarray([[1e-9, 1.]])
    with pytest.raises(owner.IO48Unresolved, match='BALANCED_PROJECTION_ILL_CONDITIONED'):
        owner.balance_io48(a, b, c, 1, POLICY)
    with pytest.raises(ValueError, match='frozen'):
        replace(POLICY, projection_condition_limit=Decimal('1e10'))


@pytest.mark.parametrize('failure', ('cutoff', 'conditioning', 'nonfinite'))
def test_cold_reproof_of_partial_failure_witnesses_never_selects_fallback(failure, monkeypatch):
    if failure == 'cutoff':
        a, b, c, steps = np.zeros((50, 50)), np.eye(50), np.eye(50), 1
    elif failure == 'conditioning':
        a, b, c, steps = np.zeros((2, 2)), np.asarray([[1.], [0.]]), np.asarray([[1e-9, 1.]]), 1
    else:
        a, b, c, steps = np.asarray([[1e20]]), np.ones((1, 1)), np.ones((1, 1)), 128
    with pytest.raises(owner.IO48Unresolved) as original:
        owner.balance_io48(a, b, c, steps, POLICY)
    monkeypatch.setattr(np.linalg, 'eigh', lambda *a, **k: pytest.fail('cold failure reran eigensolve'))
    monkeypatch.setattr(np.linalg, 'svd', lambda *a, **k: pytest.fail('cold failure reran SVD'))
    with pytest.raises(owner.IO48Unresolved) as replay:
        owner.balance_io48(a, b, c, steps, POLICY, retained=original.value.witnesses,
            declared_failure=original.value.reason)
    assert replay.value.reason == original.value.reason
    with pytest.raises(ValueError):
        owner.balance_io48(a, b, c, steps, POLICY, retained=original.value.witnesses)


@pytest.mark.parametrize('which', ('eigh-first', 'eigh-second', 'svd'))
def test_solver_failure_retains_reported_nonuse_and_only_verifies_preceding_stages(which, monkeypatch):
    a, b, c = np.diag([.9, .8]), np.eye(2), np.eye(2)
    calls, original_eigh = [], np.linalg.eigh
    def failure(*args, **kwargs):
        calls.append(None)
        if which == 'eigh-second' and len(calls) == 1:
            return original_eigh(*args, **kwargs)
        raise np.linalg.LinAlgError('exposed solver-failure control')
    monkeypatch.setattr(np.linalg, 'svd' if which == 'svd' else 'eigh', failure)
    with pytest.raises(owner.IO48Unresolved) as original:
        owner.balance_io48(a, b, c, 128, POLICY)
    monkeypatch.setattr(np.linalg, 'eigh', lambda *a, **k: pytest.fail('retried failed eigensolver'))
    monkeypatch.setattr(np.linalg, 'svd', lambda *a, **k: pytest.fail('retried failed SVD'))
    with pytest.raises(owner.IO48Unresolved) as replay:
        owner.balance_io48(a, b, c, 128, POLICY, retained=original.value.witnesses,
            declared_failure=original.value.reason)
    assert replay.value.reason == original.value.reason
    damaged = {name: value.copy() for name, value in original.value.witnesses.items()}
    damaged['gramian_c'][0, 0] += 1
    with pytest.raises(ValueError, match='reproof'):
        owner.balance_io48(a, b, c, 128, POLICY, retained=damaged, declared_failure=original.value.reason)


def test_forged_failure_or_thinned_success_is_refused():
    a, b, c = np.diag([.9, .8]), np.eye(2), np.eye(2)
    result = owner.balance_io48(a, b, c, 128, POLICY)
    partial = {name: value for name, value in result.witnesses.items()
        if name not in ('lift', 'restrict', 'reduced_transition', 'reduced_inputs', 'reduced_outputs')}
    with pytest.raises(ValueError, match='witness census'):
        owner.balance_io48(a, b, c, 128, POLICY, retained=partial)
    with pytest.raises(ValueError, match='witness|contradicted'):
        owner.balance_io48(a, b, c, 128, POLICY, retained=partial, declared_failure='HANKEL_CAP_CUTOFF_UNRESOLVED')


def test_feedback_blocks_are_projector_invariant_and_keep_memory_endpoints():
    a = np.asarray([[.9, .1, .3], [.2, .8, -.1], [.4, .2, 1.01]])
    basis = np.eye(3)[:, :2]
    p, q = basis @ basis.T, np.diag([0., 0., 1.])
    escaped, returned, curve = owner.factor_feedback_norms(a, basis, 128)
    assert escaped == pytest.approx(np.linalg.norm(q @ a @ p))
    assert returned == pytest.approx(np.linalg.norm(p @ a @ q))
    expected = [np.linalg.norm(p @ a @ q @ np.linalg.matrix_power(q @ a @ q, k) @ q @ a @ p) for k in range(128)]
    np.testing.assert_allclose(curve, expected, rtol=1e-13)
    rotated = basis @ np.asarray([[.6, -.8], [.8, .6]])
    other = owner.factor_feedback_norms(a, rotated, 128)
    np.testing.assert_allclose(other[:2], (escaped, returned), rtol=1e-13)
    np.testing.assert_allclose(other[2], curve, rtol=1e-13)


@pytest.mark.parametrize('multiplier', (1, 2))
def test_native_scaled_map_reproduces_origin_full_response_with_trace(multiplier):
    dt = Decimal('0.001') / multiplier
    view = SimpleNamespace(timestep=dt, friction_gamma=Decimal('1'))
    d = SimpleNamespace(view=view, horizon_steps=tuple(multiplier * h for h in range(16, 129, 4)))
    actions = tuple(SimpleNamespace(amplitude=Decimal('.01'), force_norm=Decimal(1), pulse_steps=16 * multiplier) for _ in range(4))
    axes = hermitian_basis(4)
    forces = np.zeros((4, 2, 3, 4, 4), dtype='<c16')
    forces[:, 0, 0] = axes[:4]
    receivers = np.zeros((48, 2, 2, 3, 4, 4), dtype='<c16')
    for phase in range(2):
        for index in range(24):
            sector, matrix, axis = index // 12, index // 4 % 3, index % 4
            receivers[24 * phase + index, phase, sector, matrix] = axes[axis]
    hessian = np.diag(np.linspace(-1., 2., 96))
    a, b, c, state_units, output_units = science.origin_io_system(d, hessian, forces, receivers, actions)
    np.testing.assert_allclose(state_units[:96], .01 * .016 * (.128 - .016 / 2))
    np.testing.assert_allclose(state_units[96:], .01 * .016)
    actual = owner.pulse_responses(a, b, c, pulse_steps=tuple(a.pulse_steps for a in actions),
        horizons=d.horizon_steps, output_units=output_units)
    expected = np.asarray(science._linear_responses(d, np.eye(96), hessian, forces, receivers, actions))
    np.testing.assert_allclose(actual, expected, rtol=1e-12, atol=1e-17)
    assert np.linalg.norm(actual) > 0  # Neither zero-response nor amplitude-divided.
    reduced = owner.balance_io48(a, b, c, 128 * multiplier, POLICY)
    owner.balance_io48(a, b, c, 128 * multiplier, POLICY, retained=reduced.witnesses)
