# SPDX-License-Identifier: MPL-2.0
"""Independent Gaussian normalization and finite-root moment controls."""
from itertools import product
import json

import numpy as np
import pytest

from empirical_lawhood.methods.model_free_response import equilibrium_importance_endpoint, equilibrium_variance_transport


@pytest.mark.numerical(oracle='Closed-form one-dimensional restrained harmonic partition functions with different inverse temperatures')
def test_importance_endpoint_preserves_normalization_sign_and_arm_temperatures():
    centers = np.array([-.2, -.1, 0., .1, .2])
    stiffness = 1.7
    arms = [(2., .3, .7), (3., -.4, 1.2)]
    logs, expected = [], []
    for precision, mean, beta in arms:
        effective = precision * stiffness / (precision + stiffness)
        logs.append(.5 * np.log(2 * np.pi / (beta * (precision + stiffness)))
            - .5 * beta * effective * (centers - mean) ** 2)
        expected.append(.5 * effective * ((centers[-1] - mean) ** 2 - (centers[0] - mean) ** 2))
    # An arbitrary reference normalization for each arm/root cancels exactly.
    roots = np.array([[logs[0] + shift, logs[1] - 2 * shift] for shift in (-1., 0., 3.)])
    result = equilibrium_importance_endpoint(roots, centers, [.7, 1.2])
    assert result['mean'] == pytest.approx(expected[1] - expected[0], abs=1e-14)
    assert result['variance_of_mean'] < 1e-28
    assert result['finite_sample_log_bias_bound'] is None
    assert result['overlap_and_tail_bound'] is None
    assert result['exact_free_energy_certified'] is False
    single = equilibrium_importance_endpoint(roots[:, 0], centers, .7)
    assert single['mean'] == pytest.approx(expected[0], abs=1e-14)


@pytest.mark.numerical(oracle='Exact enumeration of all eight independent three-root sign draws; temporal replicas within each root are perfectly correlated')
def test_cross_root_moments_remove_temporal_variance_bias_without_iid_time_assumption():
    centers = np.array([0., .5, 1.])
    estimates, moment_estimates = [], []
    for signs in product((-1., 1.), repeat=3):
        # Every finite record is constant in time, so its ddof=1 variance is
        # zero. Independent roots still have variances one and four.
        means = np.array([[centers + sign, 4 * centers + 2 * sign] for sign in signs])
        result = equilibrium_variance_transport(means, means ** 2, centers, [1., 1.], stiffness=1.)
        estimates.append(result['mean'])
        moment_estimates.append(result['variance_estimates_by_arm_and_center'])
        assert result['canonical_measure_qualified'] is False
        assert result['continuous_variance_interpolation_error_bound'] is None
        assert len(result['jackknife_leave_one_root_estimates']) == 3
    np.testing.assert_allclose(np.mean(moment_estimates, axis=0), [[1., 1., 1.], [4., 4., 4.]], atol=1e-14)
    # The mean contrast is 3s and its negative integral is -3/2.
    assert np.mean(estimates) == pytest.approx(-1.5, abs=1e-14)


@pytest.mark.numerical(oracle='Identical full root records in both arms cancel mean-anchor and variance terms including jackknife covariance')
def test_identical_variance_transport_arms_cancel_before_uncertainty():
    centers = [0., .5, 1.]
    one = np.array([[1., 2., 3.], [2., 4., 6.], [3., 1., 7.], [2., 0., 1.]])
    means = np.stack((one, one), axis=1)
    second = means ** 2 + 2.
    result = equilibrium_variance_transport(means, second, centers, [2., 2.], stiffness=1.5)
    assert result['mean'] == result['anchor_term'] == result['variance_term'] == 0.
    assert result['jackknife_variance_of_estimator'] == 0.
    assert result['interval'] == [0., 0.]
    assert np.asarray(result['full_mean_and_second_moment_covariance']).shape == (12, 12)
    json.dumps(result, allow_nan=False)


@pytest.mark.numerical(oracle='Analytic linear variance contrast v_B-v_A=s gives mean contrast s^2/2: three-center trapezoidal target is -3/16, continuous endpoint is -1/6')
def test_linear_variance_transport_preserves_the_finite_grid_target():
    centers = np.array([0., .5, 1.])
    means = np.array([[centers, centers + .5 * centers ** 2]] * 3)
    variances = np.array([[np.ones(3), 1. + centers]] * 3)
    result = equilibrium_variance_transport(means, means ** 2 + variances,
        centers, [1., 1.], stiffness=1.)
    assert result['mean'] == pytest.approx(-3 / 16, abs=1e-14)
    assert result['mean'] != pytest.approx(-1 / 6)
    assert result['target_scope'].startswith('FINITE_GRID_')
    assert result['continuous_variance_interpolation_error_bound'] is None


def test_variance_transport_preserves_insufficient_roots_and_rejects_false_moments():
    means = np.ones((1, 2, 3))
    result = equilibrium_variance_transport(means, means ** 2, [0., .5, 1.], [1., 1.], stiffness=1.)
    assert result['status'] == 'UNRESOLVED'
    assert result['mean'] is None
    with pytest.raises(ValueError, match='second moment'):
        equilibrium_variance_transport(np.repeat(means, 2, axis=0), np.zeros((2, 2, 3)),
            [0., .5, 1.], [1., 1.], stiffness=1.)
    with pytest.raises(ValueError, match='inverse temperatures'):
        equilibrium_importance_endpoint(np.zeros((3, 2, 3)), [0., .5, 1.], 1.)
