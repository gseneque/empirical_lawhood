# SPDX-License-Identifier: MPL-2.0
"""Bounded analytical controls; no molecular acquisition or qualification."""

import math

import numpy as np
import pytest
from scipy.integrate import dblquad, quad
from scipy.linalg import expm

from empirical_lawhood.methods import retained_gaussian_response as method


def samples(reference, energy, receiver, *, order=64):
    rule = method.gaussian_quadrature(reference, order=order, maximum_points=100_000)
    return method.RetainedSamples(rule, energy(rule.points), receiver(rule.points))


@pytest.fixture(scope="module")
def quartic():
    reduction = method.reduce_dense_reference([[2., -1.], [-1., 2.]], [0., 0.], np.eye(2), beta=1.)
    rule = method.gaussian_quadrature(reduction.reference, order=96, maximum_points=96**2)
    wt = method.RetainedSamples(rule, np.zeros(len(rule.points)), rule.points[:, 0])
    mutant = method.RetainedSamples(rule, rule.points[:, 1]**4, rule.points[:, 0])
    return wt, mutant


@pytest.mark.numerical(oracle='Adaptive double integration of the original two-dimensional quartic energy without reduction')
def test_pasted_quartic_against_original_two_dimensional_partition_functions(quartic):
    wt, mutant = (method.restrained_series(arm, [0., .5, 1.], 1.) for arm in quartic)
    # This reference integrates the original physical energy, without the reducer,
    # Gaussian quadrature, projected covariance or completed-square calculation.
    def partition(center, modified):
        value, error = dblquad(
            lambda y, x: math.exp(-(x*x-x*y+y*y+modified*y**4+.5*(x-center)**2)),
            -np.inf, np.inf, lambda x: -np.inf, lambda x: np.inf,
            epsabs=2e-11, epsrel=2e-11)
        assert error < 3e-11
        return value

    direct = [-math.log(partition(1., arm)/partition(0., arm)) for arm in (0., 1.)]
    paired = method.paired_response(wt, mutant)
    assert direct[0] == pytest.approx(.3, abs=5e-11)
    assert direct[1] == pytest.approx(.3195967797645805, abs=5e-11)
    assert paired.endpoint == pytest.approx(direct[1]-direct[0], abs=1e-10)
    assert paired.endpoint == pytest.approx(.0195967797645805, abs=1e-12)
    assert [math.exp(mutant.integrals[i].log_partition-wt.integrals[i].log_partition)
            for i in (0, 2)] == pytest.approx([.7336298427304475, .7193930138890902], abs=1e-12)
    assert paired.finite_grid == pytest.approx(.01960151001746379, abs=1e-12)
    assert abs(paired.finite_grid-paired.endpoint) > 4e-6
    assert np.all(paired.paired_mean_forces[1:] > 0)
    assert paired.endpoint_residual_error is None and paired.finite_grid_residual_error is None


@pytest.mark.numerical(oracle='Hand-derived Schur complement and direct full-matrix inverse')
def test_actual_environment_elimination_lift_native_potential_and_one_action_enlargement():
    k = np.array([[4., -1., 0., 0.], [-1., 3., -1., 0.],
                  [0., -1., 3., -1.], [0., 0., -1., 2.]])
    origin = np.array([.2, -.1, .3, .4])
    s = np.eye(4)[:, :2]
    calls = []

    def inverse(v):
        calls.append(v.copy())
        return np.linalg.solve(k, v)

    reduced = method.reduce_reference(origin, s, inverse, beta=2.)
    # Elimination of the last two coordinates gives precision [[4,-1],[-1,13/5]].
    np.testing.assert_allclose(reduced.reference.compliance, np.array([[13., 5.], [5., 20.]])/47, atol=1e-15)
    assert len(calls) == 2
    point = np.array([.6, -.2])
    lifted = reduced.lift(point)
    np.testing.assert_allclose(s.T@lifted, point, atol=1e-15)
    np.testing.assert_allclose((k@(lifted-origin))[2:], 0., atol=1e-15)

    def native(x):
        delta = x-origin
        return .5*delta@k@delta+x[0]**4+math.sin(x[1])

    assert reduced.lifted_potential(native)(point) == pytest.approx(point[0]**4+math.sin(point[1]), abs=1e-15)
    for w in ([0., 0., .5, -.2], [0., 0., -1., .3]):
        assert reduced.residual(lifted+w, native, lambda v: k@v) == pytest.approx(0., abs=1e-14)
    changed = lambda x: native(x)+.3*x[2]**4
    assert abs(reduced.residual(lifted+[0., 0., .5, -.2], changed, lambda v: k@v)) > .01
    enlarged = method.enlarge_reduction(reduced, np.eye(4)[:, 2], inverse)
    assert len(calls) == 3
    np.testing.assert_array_equal(enlarged.inverse_actions[:, :2], reduced.inverse_actions)
    np.testing.assert_allclose(enlarged.reference.compliance, np.linalg.inv(k)[:3, :3], atol=1e-15)
    with pytest.raises(ValueError, match="independent"):
        method.enlarge_reduction(reduced, s[:, 0], inverse)
    assert len(calls) == 3


@pytest.mark.parametrize("coupling", [0., .4])
@pytest.mark.numerical(oracle='Closed-form conditional Gaussian quadratic partition function')
def test_conditional_modification_and_zero_cross_port_response(coupling):
    ref = method.GaussianReference([.1, -.2], [[1., coupling], [coupling, 1.2]], 1.7)
    energies = []
    for observed in (-.8, .1, 1.):
        conditional = method.conditional_reference(ref, (0,), [observed])
        cloud = samples(conditional, lambda z: .35*z[:, 0]**2, lambda z: z[:, 0])
        actual = method.evaluate_boltzmann(cloud).free_energy
        mean = -.2+coupling*(observed-.1)
        compliance = 1.2-coupling**2
        expected = math.log1p(.7*compliance)/(2*1.7)+.35*mean**2/(1+.7*compliance)
        assert actual == pytest.approx(expected, abs=2e-13)
        energies.append(actual)
    if coupling == 0:
        assert np.ptp(energies) < 1e-14
    else:
        assert np.ptp(energies) > .01


def test_nonlinear_coupling_removes_the_zero_cross_port_conclusion():
    ref = method.GaussianReference([0., 0.], np.eye(2), 1.)
    cloud = samples(ref, lambda z: .3*z[:, 0]**2*z[:, 1]**2, lambda z: z[:, 0]**2)
    before = method.evaluate_boltzmann(cloud)
    after = method.evaluate_boltzmann(cloud, extra_energy=.5*cloud.quadrature.points[:, 1]**4)
    assert after.mean-before.mean > .01


@pytest.mark.numerical(oracle='Closed-form Gaussian determinant and completed-square normalization')
def test_quadratic_update_keeps_determinants_constants_and_nonunit_beta():
    ref = method.GaussianReference([.3, -.2], [[1.5, .2], [.2, .9]], 1.7)
    direction = np.array([.6, -.4])
    center, k, offset = .8, 2.3, -.1
    update = method.linear_restraint_update(ref, direction, center, k, offset=offset)
    mean = float(direction@ref.mean+offset)
    compliance = float(direction@ref.compliance@direction)
    expected_log = -.5*math.log1p(k*compliance)-ref.beta*k*(mean-center)**2/(2*(1+k*compliance))
    assert update.log_normalization == pytest.approx(expected_log, abs=1e-14)
    cloud = samples(update.updated, lambda z: np.zeros(len(z)), lambda z: z@direction+offset)
    result = method.evaluate_boltzmann(cloud, normalization=update)
    assert result.log_partition == pytest.approx(expected_log, abs=1e-14)
    assert result.mean == pytest.approx((mean+k*compliance*center)/(1+k*compliance), abs=1e-14)
    shifted = method.quadratic_update(ref, k*np.outer(direction, direction), k*(center-offset)*direction,
                                     constant=.5*k*(center-offset)**2+7.)
    assert shifted.log_normalization == pytest.approx(update.log_normalization-7*ref.beta, abs=1e-14)
    with pytest.raises(ValueError, match="different Gaussian"):
        method.evaluate_boltzmann(samples(ref, lambda z: np.zeros(len(z)), lambda z: z[:, 0]), normalization=update)


def test_absorbed_and_fixed_reference_paths_agree_for_finite_quartic(quartic):
    ref = quartic[0].quadrature.reference
    fixed = method.restrained_series(quartic[1], [0., .5, 1.], 1.)
    absorbed = method.absorbed_linear_restraint_series(
        ref, lambda z: z[1]**4, [1., 0.], [0., .5, 1.], 1., order=80, maximum_points=6400)
    np.testing.assert_allclose([v.log_partition for v in absorbed.integrals],
                               [v.log_partition for v in fixed.integrals], atol=2e-12, rtol=0)
    np.testing.assert_allclose(absorbed.mean_forces, fixed.mean_forces, atol=2e-12, rtol=0)


def test_fixed_reference_reuses_energy_evaluations_across_centers_and_strengths():
    ref = method.GaussianReference([.2], [[.7]], 1.4)
    rule = method.gaussian_quadrature(ref, order=32, maximum_points=32)
    observed = []

    def energy(z):
        observed.append(tuple(z))
        return .2*z[0]**4

    cloud = method.sample_potential(rule, energy, lambda z: z[0]+.1*z[0]**2)
    for k in (.5, 1., 3.):
        series = method.restrained_series(cloud, [-1., -.3, .2, 1.], k)
        assert len(series.integrals) == 4
    assert len(observed) == 32


def test_finite_composition_and_covariance_derivatives_are_not_linearized():
    ref = method.GaussianReference([.2], [[.8]], 1.3)
    cloud = samples(ref, lambda z: .1*z[:, 0]**4, lambda z: z[:, 0]+.2*z[:, 0]**2)
    x = cloud.quadrature.points[:, 0]
    modifications = np.column_stack((x*x, x))
    lam = np.array([.3, -.2])
    current = method.evaluate_boltzmann(cloud, extra_energy=modifications@lam)
    derivatives = current.parameter_response(modifications)
    step = 2e-4
    for i in range(2):
        direction = np.eye(2)[i]*step
        before = method.evaluate_boltzmann(cloud, extra_energy=modifications@(lam-direction))
        after = method.evaluate_boltzmann(cloud, extra_energy=modifications@(lam+direction))
        assert (after.free_energy-before.free_energy)/(2*step) == pytest.approx(
            derivatives.free_energy_gradient[i], abs=2e-8)
        assert (after.mean-before.mean)/(2*step) == pytest.approx(derivatives.receiver_gradient[i], abs=2e-8)
        numerical_column = (after.parameter_response(modifications).free_energy_gradient
                            -before.parameter_response(modifications).free_energy_gradient)/(2*step)
        np.testing.assert_allclose(numerical_column, derivatives.free_energy_hessian[:, i], atol=6e-8, rtol=0)
    base = method.evaluate_boltzmann(cloud).free_energy
    separate = sum(method.evaluate_boltzmann(cloud, extra_energy=modifications[:, i]*lam[i]).free_energy-base
                   for i in range(2))
    assert abs(current.free_energy-base-separate) > 1e-3
    combined = method.compose_potentials(lambda z: .1*z[0]**4, lambda z: .3*z[0]**2, lambda z: -.2*z[0])
    assert combined(np.array([.6])) == pytest.approx(.1*.6**4+.3*.6**2-.2*.6)


def test_energy_constants_cancel_from_moments_and_paired_contrasts(quartic):
    original = [method.restrained_series(arm, [0., .5, 1.], 1.) for arm in quartic]
    shifted = []
    for arm, constant in zip(quartic, (500., -300.), strict=True):
        changed = method.RetainedSamples(arm.quadrature, arm.energies+constant, arm.receiver)
        shifted.append(method.restrained_series(changed, [0., .5, 1.], 1.))
    before, after = method.paired_response(*original), method.paired_response(*shifted)
    assert after.endpoint == pytest.approx(before.endpoint, abs=2e-12)
    assert after.finite_grid == pytest.approx(before.finite_grid, abs=2e-12)
    np.testing.assert_allclose(shifted[0].means, original[0].means, atol=2e-12, rtol=0)


def test_large_common_energy_zero_cannot_erase_a_finite_restraint():
    ref = method.GaussianReference([.2], [[.7]], 1.4)
    original = samples(ref, lambda z: np.zeros(len(z)), lambda z: z[:, 0])
    shifted = method.RetainedSamples(original.quadrature, np.full(len(original.energies), 1e20), original.receiver)
    first = method.restrained_series(original, [-.3, .8], 1.)
    second = method.restrained_series(shifted, [-.3, .8], 1.)
    np.testing.assert_array_equal(first.mean_forces, second.mean_forces)
    assert first.endpoint_difference == second.endpoint_difference
    assert first.endpoint_difference != 0.
    result = method.paired_response(first, second)
    assert result.finite_grid == result.endpoint == 0.


def test_nonlinear_receiver_force_derivatives_and_trapezoid_remainder():
    ref = method.GaussianReference([.2], [[1.]], 1.7)
    cloud = samples(ref, lambda z: .05*z[:, 0]**4, lambda z: z[:, 0]+.2*z[:, 0]**2, order=96)
    step = 1e-4
    series = method.restrained_series(cloud, [.4-step, .4, .4+step], 1.4)
    first, second = series.mean_force_derivatives
    forces = series.mean_forces
    assert (forces[2]-forces[0])/(2*step) == pytest.approx(first[1], abs=1e-7)
    assert (forces[2]-2*forces[1]+forces[0])/step**2 == pytest.approx(second[1], abs=2e-7)
    # Independent f(s)=s^3 has f''=6s and integral 1/4 over [0,1].
    centers = np.array([0., .3, 1.])
    error = abs(method.trapezoid_weights(centers)@centers**3-.25)
    assert error <= method.trapezoid_error_bound(centers, 6*centers[1:])


@pytest.mark.parametrize("application", ["endpoint", "finite-grid", "both"])
def test_distinct_eq24_and_eq25_residual_applications_cover_bounded_omissions(quartic, application):
    centers = [0., .5, 1.]
    weights = np.array([-.25, 1., .5])  # Signed weights require absolute values in the bound.
    original, changed = [], []
    envelopes = (method.ResidualEnvelope(-.05, .05), method.ResidualEnvelope(-.07, .07))
    for arm, amplitude, function in zip(quartic, (.05, .07), (np.sin, np.cos), strict=True):
        original.append(method.restrained_series(arm, centers, 1.))
        remainder = amplitude*function(arm.quadrature.points[:, 1])
        altered = method.RetainedSamples(arm.quadrature, arm.energies+remainder, arm.receiver)
        changed.append(method.restrained_series(altered, centers, 1.))
    before = method.paired_response(*original, weights=weights, residual_application=application, residuals=envelopes)
    after = method.paired_response(*changed, weights=weights)
    if application in ("endpoint", "both"):
        assert before.endpoint_residual_error == pytest.approx(.24)
        assert abs(after.endpoint-before.endpoint) <= before.endpoint_residual_error
    else:
        assert before.endpoint_residual_error is None
    if application in ("finite-grid", "both"):
        expected = sum(abs(w)*math.sqrt(v.variance)*math.sinh(env.oscillation/2)
                       for arm, env in zip(original, envelopes, strict=True)
                       for w, v in zip(weights, arm.integrals, strict=True))
        assert before.finite_grid_residual_error == pytest.approx(expected)
        assert abs(after.finite_grid-before.finite_grid) <= before.finite_grid_residual_error
        assert before.residual_variance_source == "QUADRATURE_ESTIMATES_NOT_CERTIFIED_VARIANCE_BOUNDS"
        for old, new, env in zip(original, changed, envelopes, strict=True):
            for left, right in zip(old.integrals, new.integrals, strict=True):
                assert abs(left.mean-right.mean) <= method.receiver_residual_error(left.variance, env, beta=old.beta)
    else:
        assert before.finite_grid_residual_error is None


def test_supplied_variance_bounds_and_constant_residuals_are_explicit(quartic):
    arms = [method.restrained_series(arm, [0., 1.], 1.) for arm in quartic]
    envelopes = (method.ResidualEnvelope(7., 7.), method.ResidualEnvelope(-3., -3.))
    result = method.paired_response(*arms, residual_application="both", residuals=envelopes,
                                    receiver_variance_bounds=(np.ones(2), np.ones(2)))
    assert result.endpoint_residual_error == result.finite_grid_residual_error == 0
    assert result.residual_variance_source == "SUPPLIED_VARIANCE_BOUNDS_REQUIRING_EXTERNAL_JUSTIFICATION"
    assert method.endpoint_residual_error(method.ResidualEnvelope(100., 101.), method.ResidualEnvelope(-7., -5.)) == 3.
    assert math.isinf(method.receiver_residual_error(1., method.ResidualEnvelope(-1000., 1000.), beta=1.))
    assert method.receiver_residual_error(0., method.ResidualEnvelope(-1000., 1000.), beta=1.) == 0.
    with pytest.raises(ValueError, match="explicitly"):
        method.paired_response(*arms, residuals=envelopes)
    with pytest.raises(ValueError, match="both WT"):
        method.paired_response(*arms, residual_application="endpoint")
    with pytest.raises(ValueError, match="finite-grid error only"):
        method.paired_response(*arms, residual_application="endpoint", residuals=envelopes,
                               receiver_variance_bounds=(np.ones(2), np.ones(2)))


@pytest.mark.numerical(oracle='Independent full linear solve and residual quadratic-form identity')
def test_galerkin_identity_and_declared_lower_bound_against_full_solve():
    rng = np.random.default_rng(429)
    a = rng.normal(size=(6, 6))
    k = a.T@a+2*np.eye(6)  # The global lower bound 2 follows from construction.
    s = rng.normal(size=(6, 2))
    q = np.linalg.qr(rng.normal(size=(6, 4)))[0]
    approximation = method.galerkin_compliance(s, q, lambda v: k@v, lower_eigenvalue_bound=2.)
    actual = s.T@np.linalg.solve(k, s)
    error = approximation.residual.T@np.linalg.solve(k, approximation.residual)
    np.testing.assert_allclose(actual-approximation.lower, error, atol=1e-14, rtol=0)
    assert np.linalg.eigvalsh(actual-approximation.lower)[0] > 0
    assert np.linalg.eigvalsh(approximation.upper-actual)[0] > 0
    with pytest.raises(ValueError, match="orthonormal"):
        method.galerkin_compliance(s, 2*q, lambda v: k@v, lower_eigenvalue_bound=2.)
    singular = method.galerkin_compliance(np.eye(2), np.eye(2)[:, :1], lambda v: v, lower_eigenvalue_bound=1.)
    with pytest.raises(ValueError, match="positive definite"):
        method.GaussianReference([0., 0.], singular.lower, 1.)


@pytest.mark.numerical(oracle='Adaptive scalar integration of a nonlinear double-well Gaussian expectation')
def test_covariance_enclosure_with_nonlinear_integral_and_fixed_mean():
    beta, mean = 1.3, .4
    references = [method.GaussianReference([mean], [[g]], beta) for g in (.7, 1.1, 1.6)]

    def log_integral(g):
        variance = g/beta
        value, _ = quad(lambda x: math.exp(-beta*.4*(x*x-1)**2-(x-mean)**2/(2*variance))
                       /math.sqrt(2*math.pi*variance), -np.inf, np.inf, epsabs=1e-12, epsrel=1e-12)
        return math.log(value)

    logs = list(map(log_integral, (.7, 1.1, 1.6)))
    lo, hi = method.covariance_log_integral_bounds(references[0], references[2],
                                                 log_lower_integral_bound=logs[0]-1e-11,
                                                 log_upper_integral_bound=logs[2]+1e-11)
    assert lo < logs[1] < hi
    assert lo == pytest.approx(logs[0]-1e-11+.5*math.log(.7/1.6))
    different_mean = method.GaussianReference([mean+.1], [[1.6]], beta)
    with pytest.raises(ValueError, match="same mean"):
        method.covariance_log_integral_bounds(references[0], different_mean,
                                             log_lower_integral_bound=logs[0], log_upper_integral_bound=logs[2])
    with pytest.raises(ValueError, match="not ordered"):
        method.covariance_log_integral_bounds(references[2], references[0],
                                             log_lower_integral_bound=logs[2], log_upper_integral_bound=logs[0])


def test_transverse_taylor_bound_is_only_a_tube_bound():
    # R(w)=.2*w+.3*w^2 has force mismatch .2 and curvature mismatch .6.
    envelope = method.transverse_residual_envelope(.2, .6, .5)
    values = .2*np.linspace(-.5, .5, 21)+.3*np.linspace(-.5, .5, 21)**2
    assert np.min(values) >= envelope.lower and np.max(values) <= envelope.upper
    assert envelope.upper == pytest.approx(.175)
    assert .2*2+.3*2**2 > envelope.upper  # No tail or full-domain claim follows.


def test_distance_difference_keeps_shared_hydrogen_covariance_and_nonlinear_geometry():
    # Nine Cartesian coordinates for C,H,O; six retained relative-vector entries.
    s = np.zeros((9, 6))
    s[:3, :3] = np.eye(3)
    s[3:6, :3] = s[3:6, 3:] = -np.eye(3)
    s[6:, 3:] = np.eye(3)
    origin = np.array([-1.2, .2, 0., 0., 0., 0., .8, .1, 0.])
    reduced = method.reduce_dense_reference(np.eye(9), origin, s, beta=20.)
    np.testing.assert_array_equal(reduced.reference.compliance[:3, 3:], np.eye(3))
    receiver = lambda z: np.linalg.norm(z[:3])-np.linalg.norm(z[3:6])
    literal = np.linalg.norm(origin[:3]-origin[3:6])-np.linalg.norm(origin[6:]-origin[3:6])
    assert receiver(reduced.reference.mean) == pytest.approx(literal)
    shifted = origin+np.tile([3., -4., .7], 3)
    assert receiver(s.T@shifted) == pytest.approx(literal)
    ref = reduced.reference
    cloud = method.sample_potential(method.gaussian_quadrature(ref, order=3, maximum_points=729),
                                    lambda z: .1*(z[:3]@z[3:6])**2, receiver)
    series = method.restrained_series(cloud, [-.5, .5], 2.)
    # Different retained dimensions are permitted. An independent added coordinate
    # contributes a center-independent partition factor, which must cancel.
    enlarged_g = np.zeros((7, 7))
    enlarged_g[:6, :6], enlarged_g[6, 6] = ref.compliance, 1.
    other_ref = method.GaussianReference(np.r_[ref.mean, 0.], enlarged_g, ref.beta)
    other_cloud = method.sample_potential(method.gaussian_quadrature(other_ref, order=3, maximum_points=2187),
        lambda z: .1*(z[:3]@z[3:6])**2+.2*z[6]**2, receiver)
    paired = method.paired_response(series, method.restrained_series(other_cloud, [-.5, .5], 2.))
    assert paired.endpoint == pytest.approx(0., abs=1e-14)
    assert paired.finite_grid == pytest.approx(0., abs=1e-14)


@pytest.mark.numerical(oracle='Full Hamiltonian matrix exponential and independently integrated memory convolution')
def test_equal_equilibrium_geometry_has_distinct_history_and_correct_preparation_force():
    baths = [method.HarmonicBath([[2.]], [[b]], [[kq]]) for b, kq in ((1., 1.), (2., 4.))]
    final_positions = []
    for bath, frequency in zip(baths, (1., 2.), strict=True):
        assert bath.effective_stiffness[0, 0] == pytest.approx(1.)
        assert bath.memory(.7)[0, 0] == pytest.approx(math.cos(frequency*.7))
        b, kq = bath.coupling[0, 0], bath.bath_stiffness[0, 0]
        full_k = np.array([[2., b], [b, kq]])
        operator = np.block([[np.zeros((2, 2)), np.eye(2)], [-full_k, np.zeros((2, 2))]])
        initial = np.array([1., -b/kq+.2, -.1, .3])
        t = .7
        state = expm(operator*t)@initial
        memory, _ = quad(lambda tau: math.cos(frequency*(t-tau))*(expm(operator*tau)@initial)[2],
                         0., t, epsabs=1e-12)
        acceleration = -(full_k@state[:2])[0]
        noise = bath.initial_force(t, initial[:1], initial[1:2], initial[3:4])[0]
        assert acceleration+state[0]+memory-noise == pytest.approx(0., abs=1e-12)
        p = .8+.3j
        expected = p*p+2-b*b/(p*p+kq)
        assert bath.dynamic_stiffness(p)[0, 0] == pytest.approx(expected)
        left = np.array([-b*math.cos(frequency*t), -b*math.sin(frequency*t)/frequency])
        right = np.array([-b*math.cos(frequency*.2), -b*math.sin(frequency*.2)/frequency])
        covariance = left@np.diag([1/(1.7*kq), 1/1.7])@right
        assert bath.thermal_force_covariance(t, .2, beta=1.7)[0, 0] == pytest.approx(covariance)
        final_positions.append(state[0])
    assert abs(final_positions[0]-final_positions[1]) > .01


@pytest.mark.parametrize("stiffness", [[[1., 0.], [0., 0.]], [[1., 2.], [2., 1.]],
                                     [[1., .1], [.2, 1.]], [[1., np.nan], [np.nan, 1.]]])
def test_invalid_positive_references_refuse(stiffness):
    with pytest.raises(ValueError):
        method.reduce_dense_reference(stiffness, [0., 0.], np.eye(2), beta=1.)


@pytest.mark.parametrize("beta", [0., -1., math.inf, math.nan, True, 1j])
def test_invalid_temperature_refuses(beta):
    with pytest.raises(ValueError):
        method.GaussianReference([0.], [[1.]], beta)


def test_rank_and_point_budget_refuse_before_operator_or_quadrature_contact(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("must refuse before contact")

    with pytest.raises(ValueError, match="independent"):
        method.reduce_reference([0., 0.], [[1., 1.], [0., 0.]], forbidden, beta=1.)
    monkeypatch.setattr(method, "roots_hermitenorm", forbidden)
    with pytest.raises(ValueError, match="before allocation"):
        method.gaussian_quadrature(method.GaussianReference(np.zeros(6), np.eye(6), 1.),
                                   order=10, maximum_points=999_999)


def test_failed_energy_missing_nodes_and_changed_target_refuse(quartic):
    rule = quartic[0].quadrature
    with pytest.raises(ValueError, match="finite real"):
        method.sample_potential(rule, lambda z: math.nan, lambda z: z[0])
    with pytest.raises(ValueError, match="every quadrature"):
        method.RetainedSamples(rule, np.zeros(len(rule.points)-1), rule.points[:, 0])
    for centers in ([1., 0.], [0., 0.]):
        with pytest.raises(ValueError, match="strictly increasing"):
            method.restrained_series(quartic[0], centers, 1.)
    wt = method.restrained_series(quartic[0], [0., 1.], 1.)
    other = method.restrained_series(quartic[1], [0., 1.], 2.)
    with pytest.raises(ValueError, match="share centers"):
        method.paired_response(wt, other)
    with pytest.raises(ValueError, match="updated precision"):
        method.quadratic_update(rule.reference, -100*np.eye(2), np.zeros(2))
    with pytest.raises(ValueError, match="reversed"):
        method.ResidualEnvelope(1., 0.)


def test_arrays_cannot_be_mutated_through_original_or_returned_operands():
    mean, g = np.array([.2]), np.array([[1.]])
    ref = method.GaussianReference(mean, g, 1.)
    mean[0], g[0, 0] = 9., 9.
    assert ref.mean[0] == .2 and ref.compliance[0, 0] == 1.
    with pytest.raises(ValueError):
        ref.mean.setflags(write=True)
