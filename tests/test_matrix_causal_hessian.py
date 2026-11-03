# SPDX-License-Identifier: MPL-2.0
"""Exposed algebraic controls; independent maps and rotations, no native tasks."""
from decimal import Decimal as D
from types import SimpleNamespace as NS

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response.causal_hessian import (
    current_eigenspace_split, origin_trend_first_variation, causal_hessian_features,
)
from empirical_lawhood.adapters.methods.matrix_factor_response.response_scoring import DENSE_RESPONSE_HORIZONS


def test_transitive_signed_clusters_and_degenerate_basis_invariance():
    h = np.diag([-.3, 0., .75e-10, 1.5e-10, .3])
    difference = np.arange(25, dtype=float).reshape(5, 5)
    difference += difference.T
    block, mix, clusters = current_eigenspace_split(h, difference)
    assert clusters == ((0, 1), (1, 4), (4, 5))
    expected = np.zeros((5, 5))
    expected[0, 0], expected[4, 4] = difference[0, 0], difference[4, 4]
    expected[1:4, 1:4] = difference[1:4, 1:4]
    np.testing.assert_array_equal(block, expected)
    np.testing.assert_array_equal(block + mix, difference)
    h = np.diag([0., 0., 0., 2., 3.])
    angle = .61
    rotation = np.eye(5)
    rotation[:2, :2] = [[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]]
    original = current_eigenspace_split(h, difference)
    rotated = current_eigenspace_split(h, difference, eigensystem=(np.diag(h).copy(), rotation))
    np.testing.assert_allclose(rotated[0], original[0], rtol=0, atol=2e-14)
    np.testing.assert_allclose(rotated[1], original[1], rtol=0, atol=2e-14)
    assert rotated[2] == original[2]


def time_varying_map(h, d, force, receiver, dt, decay, pulse, steps, eta):
    # Independently compose the affine full-step map with distinct first/last H.
    n = len(h)
    state = np.zeros((2 * n, force.shape[1]))
    eye = np.eye(n)
    half, drift = dt / 2, dt / 2 * (1 + decay)
    out = []
    for tick in range(1, steps + 1):
        first, last = h + eta * (tick - 1) * dt * d, h + eta * tick * dt * d
        qq, qp = eye - drift * half * first, drift * eye
        a = np.block([[qq, qp], [-half * (decay * first + last @ qq), decay * eye - half * last @ qp]])
        bq = drift * half * force
        b = np.concatenate((bq, drift * force - half * last @ bq))
        state = a @ state + (b if tick <= pulse else 0)
        out.append((receiver @ state).T)
    return np.transpose(out, (1, 0, 2))


def test_kick_variation_matches_independent_affine_derivative_including_final_input_kick():
    h = np.array([[1., .2], [.2, 3.]])
    d = np.array([[.3, -.8], [-.8, .1]])
    forces = np.array([[.01, 0.], [0., .02]])
    receiver = np.eye(4)
    dt, decay, eta = .001, np.exp(-.001), .001
    actual = origin_trend_first_variation(h, d, forces, receiver, timestep=dt, decay=decay,
        pulse_steps=16, horizons=tuple(range(1, 129)))
    expected = (time_varying_map(h, d, forces, receiver, dt, decay, 16, 128, eta)
        - time_varying_map(h, d, forces, receiver, dt, decay, 16, 128, -eta)) / (2 * eta)
    np.testing.assert_allclose(actual, expected, rtol=2e-6, atol=3e-16)
    np.testing.assert_array_equal(actual[:, 0, :2], 0.)
    bq = dt * dt / 4 * (1 + decay) * forces
    np.testing.assert_allclose(actual[:, 0, 2:], (-dt / 2 * dt * d @ bq).T, rtol=2e-15, atol=0.)
    fine = origin_trend_first_variation(h, d, forces, receiver, timestep=dt / 2, decay=np.exp(-dt / 2),
        pulse_steps=32, horizons=tuple(2 * h for h in DENSE_RESPONSE_HORIZONS))
    coarse = actual[:, np.asarray(DENSE_RESPONSE_HORIZONS) - 1]
    np.testing.assert_allclose(fine, coarse, rtol=.003, atol=1e-13)


def causal_case():
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_forecast import _hessian
    from empirical_lawhood.adapters.methods.matrix_factor_response.science import native_position_lift
    coordinate = NS(primary_view=NS(timestep=D('.001'), friction_gamma=D(1)),
        fine_view=NS(timestep=D('.0005'), friction_gamma=D(1)),
        member=NS(mass_x=D('.1'), mass_y=D('.2'), cross_coupling_gamma=D('.2')))
    protocol = NS(public_source=NS(coordinate=coordinate, policy=NS(cutoff_tick=256)),
        horizon_steps=DENSE_RESPONSE_HORIZONS, receiver_count=48,
        actions=tuple(NS(amplitude=D('.01'), force_norm=D(1), pulse_steps=16) for _ in range(4)))
    position = native_position_lift(np.linspace(-.1, .2, 96))
    alpha = np.array([1., 2.])
    hessian = _hessian(protocol, position, alpha)
    values, vectors = np.linalg.eigh(hessian)
    lifts = np.asarray([native_position_lift(row) for row in np.eye(96)])
    receivers = np.zeros((48, 2, 2, 3, 4, 4), dtype='<c16')
    receivers[:24, 0] = lifts[:24]
    receivers[24:, 1] = lifts[:24]
    causal, frozen = {}, {'forces': lifts[:4], 'receivers': receivers}
    for view, multiplier in (('primary', 1), ('fine', 2)):
        causal[view + '_ticks'] = np.arange(256 * multiplier + 1, dtype='<i8')
        causal[view + '_positions'] = np.broadcast_to(position, (256 * multiplier + 1, *position.shape)).copy()
        causal[view + '_positions'][224 * multiplier] = position * .99
        causal[view + '_alpha_tilde'] = np.broadcast_to(alpha, (256 * multiplier + 1, 2)).copy()
        frozen.update({view + '_hessian': hessian, view + '_hessian_spectrum': values, view + '_hessian_eigenvectors': vectors})
    return protocol, causal, frozen


def test_past_window_uses_handoff_parameters_and_refuses_future_or_replacement_window():
    protocol, causal, frozen = causal_case()
    result = causal_hessian_features(protocol, causal, frozen)
    assert all(not row.reasons for row in result)
    causal['primary_alpha_tilde'][224] = [90., -90.]
    assert causal_hessian_features(protocol, causal, frozen) == result
    causal['primary_ticks'][224] = 223  # an invalid clock is not an alternative window
    with pytest.raises(ValueError, match='clocks'):
        causal_hessian_features(protocol, causal, frozen)
    for name in tuple(causal):
        if name.startswith('primary_'):
            causal[name] = np.delete(causal[name], 224, axis=0)
    missing = causal_hessian_features(protocol, causal, frozen)
    assert missing[0].reasons == ('MISSING_FIXED_032_PAST_OBSERVATION',) and missing[1] == result[1]
    with pytest.raises(ValueError, match='future'):
        causal_hessian_features(protocol, {**causal, 'future_hold': object()}, frozen)


def test_nonfinite_past_operator_is_missing_without_a_replacement_window(monkeypatch):
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import response_forecast
    protocol, causal, frozen = causal_case()
    monkeypatch.setattr(response_forecast, '_hessian', lambda *args: np.full((96, 96), np.inf))
    result = causal_hessian_features(protocol, causal, frozen)
    assert tuple(row.reasons for row in result) == (('NONFINITE_PAST_HESSIAN_DIFFERENCE',),) * 2

