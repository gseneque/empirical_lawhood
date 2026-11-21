# SPDX-License-Identifier: MPL-2.0
"""Independent numerical and contract controls for generic joint response methods."""
from fractions import Fraction
import math

import numpy as np
import pytest
from scipy.integrate import quad
from scipy.linalg import expm, solve_discrete_lyapunov

from empirical_lawhood.methods import joint_response as method


def hermitian_case(n=17, p=3, seed=20261116):
    rng = np.random.default_rng(seed)
    q, _ = np.linalg.qr(rng.normal(size=(n, n))+1j*rng.normal(size=(n, n)))
    a = (q*np.linspace(-2., 5., n))@q.conj().T
    v = rng.normal(size=(n, p))+1j*rng.normal(size=(n, p))
    return a, v


@pytest.mark.numerical(oracle='Direct dense complex resolvent solves and exact dual residual identity')
def test_complex_joint_krylov_residual_and_reused_prefixes():
    a, v = hermitian_case()
    calls = []

    def action(x):
        calls.append(x.shape[1])
        return a@x

    all_prefix = method.acquire_block_krylov(action, v, 5)
    assert sum(calls) == all_prefix.action_count == 15
    assert all_prefix.block_sizes == (3, 3, 3, 3, 3)
    assert all_prefix.orthogonality_error < 2e-14
    z = .3+.7j
    r = np.linalg.inv(z*np.eye(len(a))-a)
    for m in (1, 2, 4, 5):
        prefix = all_prefix.prefix(m)
        result = method.galerkin_response(prefix, v, z)
        actual = v.conj().T@r@v
        identity = result.dual_residual.conj().T@r@result.primal_residual
        np.testing.assert_allclose(actual-result.estimate, identity, atol=5e-13)
        assert np.linalg.norm(actual-result.estimate, 2) <= result.bound+1e-12
        assert np.all(np.abs(actual-result.estimate) <= result.entrywise_bounds+1e-12)
    assert len(calls) == 5
    assert np.shares_memory(all_prefix.prefix(2).basis, all_prefix.basis)
    assert np.shares_memory(all_prefix.prefix(2).actions, all_prefix.actions)
    with pytest.raises(ValueError):
        all_prefix.basis[0, 0] = 10
    with pytest.raises(ValueError):
        all_prefix.basis.flags.writeable = True


@pytest.mark.numerical(oracle='Diagonal finite cyclic subspace closes exactly with dependent physical ports')
def test_rank_deflation_preserves_physical_scale_and_full_closure():
    a = np.diag([1., 2., 3., 4.])
    v = np.array([[1., 2., 0.], [0., 0., 0.], [1., 2., 1.], [0., 0., 0.]])
    prefix = method.acquire_block_krylov(a, v, 20)
    assert prefix.action_count == 2
    assert prefix.invariant
    assert prefix.block_sizes == (2,)
    np.testing.assert_allclose(prefix.basis@prefix.seed_factor, v, atol=2e-15)
    actual = v.T@np.linalg.solve((.4+.3j)*np.eye(4)-a, v)
    result = method.galerkin_response(prefix, v, .4+.3j)
    np.testing.assert_allclose(actual, result.estimate, atol=2e-14)
    assert result.bound < 1e-25


@pytest.mark.numerical(oracle='Direct native solve with an explicitly bounded perturbed operator')
def test_operator_error_propagates_computed_correction_uncertainty():
    a, v = hermitian_case(12, 2)
    perturbation = .02*np.eye(12)
    approximate = a+perturbation
    prefix = method.acquire_block_krylov(approximate, v, 4, operator_error_bound=.02)
    z = .5+.3j
    result = method.galerkin_response(prefix, v, z)
    actual = v.conj().T@np.linalg.solve(z*np.eye(12)-a, v)
    assert np.linalg.norm(actual-result.estimate, 2) <= result.bound


@pytest.mark.numerical(oracle='Dense singular-Hermitian finite operator update and direct inverse')
def test_finite_singular_update_and_static_sign():
    a, v = hermitian_case(12, 5)
    c, b, u = v[:, :2], v[:, 2:3], v[:, 3:]
    d = np.array([[.3, .3j], [-.3j, .3]])
    assert abs(np.linalg.det(d)) < 1e-15
    z = .5+.6j
    r = np.linalg.inv(z*np.eye(12)-a)
    actual = c.conj().T@np.linalg.solve(z*np.eye(12)-a-u@d@u.conj().T, b)
    estimate = method.finite_update_response(c.conj().T@r@b, c.conj().T@r@u,
        u.conj().T@r@u, u.conj().T@r@b, d)
    np.testing.assert_allclose(estimate, actual, atol=3e-13)
    k = a+4*np.eye(12)
    ki = np.linalg.inv(k)
    static = method.finite_static_update(c.conj().T@ki@b, c.conj().T@ki@u,
        u.conj().T@ki@u, u.conj().T@ki@b, d)
    np.testing.assert_allclose(static, c.conj().T@np.linalg.solve(k+u@d@u.conj().T, b), atol=1e-13)
    omitted = .01*np.eye(12)
    changed = c.conj().T@np.linalg.solve(z*np.eye(12)-a-u@d@u.conj().T-omitted, b)
    assert np.linalg.norm(changed-actual, 2) <= method.omitted_update_bound(c, b, .01, z)


@pytest.mark.numerical(oracle='One dense block-Hermitian solve with unequal block ranks and explicit auxiliary tail')
def test_rectangular_schur_elimination_and_auxiliary_tail():
    a0 = np.array([[2., .1], [.1, 3.]])
    a1 = np.array([[4.]])
    b = np.array([[.2], [.3]])
    tail = np.array([[5., .2], [.2, 6.]])
    coupling = np.array([[.1, .3]])
    head = np.block([[a0, b], [b.T, a1]])
    joint_coupling = np.vstack((np.zeros((2, 2)), coupling))
    whole = np.block([[head, joint_coupling], [joint_coupling.T, tail]])
    z = 1.+.5j
    self_energy = method.finite_auxiliary_self_energy(tail, coupling, z)
    result = method.schur_head((a0, a1), (b,), z, terminal_self_energy=self_energy)
    actual = np.linalg.inv(z*np.eye(5)-whole)[:2, :2]
    np.testing.assert_allclose(result, actual, atol=1e-15)
    assert np.linalg.eigvalsh(-(result-result.conj().T)/(2j))[0] >= 0


@pytest.mark.numerical(oracle='Long finite-chain backward recursion independently approximates the known constant infinite tail')
def test_constant_tail_and_matrix_periodic_contraction():
    z = .4+.03j
    actual = 0j
    for _ in range(4096):
        actual = 1/(z-.4-.85**2*actual)
    np.testing.assert_allclose(method.constant_scalar_tail(z, .4, .85), actual, atol=1e-13)
    assert method.constant_scalar_tail(2.+.5j, .4, 0.) == pytest.approx(1/(1.6+.5j), rel=1e-15)
    for huge in (1e12+1j, -1e12+1j, 1e200+1e199j):
        assert method.constant_scalar_tail(huge, 0., 1.) == pytest.approx(1/huge, rel=1e-15)
    diagonals = (np.diag([1., 2.]), np.diag([3., 4.]))
    bonds = (np.diag([.1, .2]), np.diag([.3, .1]))
    periodic = method.periodic_block_tail(diagonals, bonds, .5+1j)
    assert periodic.converged and periodic.error_bound < 1e-12
    exact = np.zeros((2, 2), dtype=complex)
    for j in reversed(range(400)):
        a, b = diagonals[j % 2], bonds[j % 2]
        exact = np.linalg.inv((.5+1j)*np.eye(2)-a-b@exact@b.T)
    assert np.linalg.norm(periodic.responses[0]-exact, 2) <= periodic.error_bound+1e-15
    unconstrained = method.periodic_block_tail(([[0.]],), ([[1.]],), .03j, maximum_iterations=10)
    assert unconstrained.error_bound is None


@pytest.mark.numerical(oracle='Resolvents for two actual tail completions under a common known Jacobi head')
def test_computable_tail_error_propagation_encloses_difference():
    z = .2+.7j
    a = [np.array([[.3]]), np.array([[.7]])]
    b = [np.array([[.2]]), np.array([[.4]])]
    true_tail = np.array([[1/(z-2)]])
    proposed = np.array([[1/(z-4)]])
    approximate_heads = []
    true, guessed = true_tail, proposed
    for aa, bb in reversed(tuple(zip(a, b, strict=True))):
        true = np.linalg.inv(z*np.eye(1)-aa-bb@true@bb.T)
        guessed = np.linalg.inv(z*np.eye(1)-aa-bb@guessed@bb.T)
        approximate_heads.insert(0, guessed)
    bound = method.tail_error_bound(approximate_heads, b, z)
    assert np.linalg.norm(true-guessed, 2) <= bound


@pytest.mark.numerical(oracle='Dense complex resolvent and exact diagonal spectral support')
def test_chebyshev_query_bound_with_joint_moment_uncertainty():
    a, v = hermitian_case(15, 2)
    # Deliberately outward support: direct supplied bounds include all eigenvalues.
    support = (-2.0001, 5.0001)
    mm = method.chebyshev_moments(a, v, 20, support)
    z = .2+1.8j
    result = method.chebyshev_response(mm, z, support)
    actual = v.conj().T@np.linalg.solve(z*np.eye(15)-a, v)
    assert np.linalg.norm(actual-result.estimate, 2) <= result.bound
    errors = np.full(len(mm), 1e-5)
    perturbed = [m+1e-5*np.eye(2) for m in mm]
    uncertain = method.chebyshev_response(perturbed, z, support, moment_error_bounds=errors)
    assert uncertain.acquisition_bound > 0
    assert np.linalg.norm(actual-uncertain.estimate, 2) <= uncertain.bound
    lower = method.chebyshev_response(mm, z.conjugate(), support)
    np.testing.assert_allclose(lower.estimate, result.estimate.conj().T, atol=1e-14)


@pytest.mark.numerical(oracle='Direct matrix exponentials of the full and reduced Hermitian evolution')
def test_finite_horizon_bound_and_time_ordering():
    a, b = hermitian_case(9, 2)
    c = b[:, ::-1]
    prefix = method.acquire_block_krylov(a, b, 2)
    time = .6
    q = prefix.basis
    prediction = c.conj().T@q@expm(-1j*time*prefix.projected)@q.conj().T@b
    actual = c.conj().T@expm(-1j*time*a)@b
    bound = method.unitary_projection_bound(q, prefix.actions, prefix.projected, c, b, time)
    assert np.linalg.norm(actual-prediction, 2) <= bound
    a0 = np.array([[0., 1.], [1., 0.]])
    a1 = np.diag([1., -1.])
    ordered = method.ordered_propagator((a0, a1), (.3, .5))
    np.testing.assert_allclose(ordered, expm(-.5j*a1)@expm(-.3j*a0), atol=1e-15)
    assert np.linalg.norm(ordered-expm(-1j*(.3*a0+.5*a1))) > .1


@pytest.mark.numerical(oracle='Matrix-power telescoping sum formed independently of the recursive endpoint accounting')
def test_propagation_accounting_preserves_generated_and_inherited_terms():
    m = np.array([[.9, .2, 0.], [0., .8, .3], [.1, 0., .7]])
    r = np.array([[.92, .1], [.1, .85]])
    lift = np.array([[1., 0.], [0., 1.], [.1, .2]])
    full = np.array([1., -.3, .4])
    reduced = np.array([.8, -.2])
    n = 17
    result = method.propagation_accounting(m, r, lift, full, reduced, n)
    inherited = np.linalg.matrix_power(m, n)@(full-lift@reduced)
    generated = sum((np.linalg.matrix_power(m, n-1-j)@(m@lift-lift@r)@
                     np.linalg.matrix_power(r, j)@reduced for j in range(n)), np.zeros(3))
    np.testing.assert_allclose(result.inherited, inherited, atol=1e-14)
    np.testing.assert_allclose(result.generated, generated, atol=1e-14)
    assert result.reconstruction_error < 1e-14
    zero = method.propagation_accounting(m, r, lift, full, reduced, 0)
    np.testing.assert_array_equal(zero.generated, np.zeros(3))


@pytest.mark.numerical(oracle='Explicit signed endpoint vectors demonstrate endpoint improvement with contrast deterioration')
def test_signed_contrast_reversal_and_complex_vectors():
    before = method.signed_contrast_account([10., 1.], [10., 2.])
    after = method.signed_contrast_account([1., 1.], [-1., 1.])
    assert after.low_energy < before.low_energy
    assert after.high_energy < before.high_energy
    assert after.contrast_energy > before.contrast_energy
    assert after.endpoint_energy < before.endpoint_energy
    assert before.signed_alignment-after.signed_alignment > before.endpoint_energy-after.endpoint_energy
    for account in (before, after, method.signed_contrast_account([1+2j, 3], [-1j, 2-1j])):
        assert abs(account.identity_residual) < 1e-13


@pytest.mark.numerical(oracle='Independent adaptive canonical quadrature of two quartic potentials at each original grid node')
def test_exact_finite_grid_anchor_variance_bridge_is_not_continuum_endpoint():
    def stats(alpha, linear, s):
        def kernel(x):
            return math.exp(-(.5*x*x+alpha*x**4+linear*x+.5*(x-s)**2))
        moments = [quad(lambda x: x**j*kernel(x), -np.inf, np.inf, epsabs=2e-11, epsrel=2e-11)[0] for j in (0, 1, 2)]
        return moments[1]/moments[0], moments[2]/moments[0]-(moments[1]/moments[0])**2, -math.log(moments[0])
    centers = [-.4, -.1, .2, .7]
    weights = [.15, .30, .40, .25]
    wt = [stats(.05, 0., s) for s in centers]
    mutant = [stats(.2, .1, s) for s in centers]
    direct = method.finite_grid_from_means(centers, weights, [m[0] for m in mutant], [w[0] for w in wt], stiffness=1.)
    bridge = method.finite_grid_mean_bridge(centers, weights, mutant[0][0]-wt[0][0],
        lambda s: stats(.2, .1, s)[1]-stats(.05, 0., s)[1], beta=1., stiffness=1.)
    assert direct == pytest.approx(.0532037905239821, abs=3e-12)
    assert bridge.value == pytest.approx(direct, abs=3e-12)
    assert bridge.total_error_bound is None
    assert bridge.interval_weights == pytest.approx([.95, .65, .25])
    continuum = mutant[-1][2]-mutant[0][2]-wt[-1][2]+wt[0][2]
    assert abs(direct-continuum) > 1e-5
    kj_to_j = method.finite_grid_mean_bridge(centers, weights, mutant[0][0]-wt[0][0],
        lambda s: stats(.2, .1, s)[1]-stats(.05, 0., s)[1], beta=1., stiffness=1., energy_scale=1000)
    assert kj_to_j.value == pytest.approx(1000*direct, abs=3e-9)


@pytest.mark.numerical(oracle='Analytic polynomial variance transport with arbitrary signed finite-grid weights')
def test_mean_bridge_bound_and_signed_weights():
    centers = [-1., 0., 2.]
    weights = [1., -3., .5]
    # Delta mu(s) = anchor + beta*k*integral_(s_a)^s u^2 du.
    beta, k, anchor = 1.3, .7, -.2
    expected = -k*sum(w*(anchor+beta*k*(s**3+1)/3) for s, w in zip(centers, weights, strict=True))
    bridge = method.finite_grid_mean_bridge(centers, weights, anchor, lambda s:s*s,
        beta=beta, stiffness=k, anchor_error_bound=.01, variance_error_bound=.02,
        integration_error_bound=1e-12)
    assert bridge.value == pytest.approx(expected, abs=1e-14)
    assert bridge.upstream_error_bound == pytest.approx(k*1.5*.01+beta*k*k*(2.5*1+.5*2)*.02)
    assert bridge.total_error_bound == pytest.approx(bridge.upstream_error_bound+1e-12)


@pytest.mark.numerical(oracle='Direct finite-support partition function under changed harmonic restraint')
def test_finite_center_tilt_and_physical_remainder_limits():
    x = np.array([-1., .2, 1.3])
    energy = .3*x**4
    beta, k, a, b = 1.7, 2.1, -.4, .7
    logs = -beta*(energy+.5*k*(x-a)**2)
    result = method.finite_center_tilt(x, logs, a, b, beta=beta, stiffness=k)
    weights = np.exp(-beta*(energy+.5*k*(x-b)**2))
    weights /= sum(weights)
    mean = float(weights@x)
    assert result.mean == pytest.approx(mean)
    assert result.variance == pytest.approx(weights@(x-mean)**2)
    exact_log_ratio = math.log(sum(np.exp(-beta*(energy+.5*k*(x-b)**2)))/sum(np.exp(logs)))
    assert result.log_normalization == pytest.approx(exact_log_ratio)
    bounds = method.physical_remainder_bounds(.3, 0., 0., beta=1.)
    assert bounds.variance_lower == pytest.approx(.3)
    assert bounds.variance_upper == pytest.approx(.3)
    assert bounds.mean_error_bound == 0


@pytest.mark.numerical(oracle='Full block Toeplitz covariance assembled from an exactly stationary vector AR(1) model')
def test_finite_record_uncertainty_preserves_cross_port_signs_and_unequal_lengths():
    transition = np.array([[.7, .2], [0., .5]])
    innovation = np.array([[1., .3], [.3, .6]])
    stationary = solve_discrete_lyapunov(transition, innovation)
    n = 9
    gamma = np.array([np.linalg.matrix_power(transition, lag)@stationary for lag in range(n)])
    toeplitz = np.block([[gamma[i-j] if i>=j else gamma[j-i].T for j in range(n)] for i in range(n)])
    weights = np.array([1.2, -.8])
    exact_weights = np.tile(weights/n, n)
    expected = exact_weights@toeplitz@exact_weights
    assert method.finite_record_variance(gamma, weights, n) == pytest.approx(expected, abs=1e-14)
    filters = np.zeros((n, 2))
    filters[:, 0] = 1.2/n
    filters[:5, 1] = -.8/5
    assert method.finite_filter_variance(gamma, filters) == pytest.approx(filters.ravel()@toeplitz@filters.ravel(), abs=1e-14)
    assert abs(expected-method.finite_record_variance(gamma*np.eye(2)[None], weights, n)) > .01
    angles = np.array([0., 2*np.pi, .1, 2.])
    independent = np.abs(np.mean(np.exp(1j*np.arange(n)[:, None]*angles[None]), axis=0))**2
    np.testing.assert_allclose(method.finite_record_window(angles, n), independent, atol=2e-15)


@pytest.mark.numerical(oracle='Explicit positive matrix-valued atomic measure, including complex joint residues and a boundary atom')
def test_rational_moment_constraints_and_index_ranges():
    nodes = np.array([-.9, -.7, 0., .5, .8])
    rng = np.random.default_rng(7)
    v = rng.normal(size=(5, 2))+1j*rng.normal(size=(5, 2))
    z = .25+.4j
    mm = [v.conj().T@((nodes**j)[:,None]*v) for j in range(5)]
    nn = [v.conj().T@((nodes**j/abs(z-nodes)**2)[:,None]*v) for j in range(7)]
    constraints = method.rational_moment_constraints(mm, nn, z, order=3,
        bands=((-1., -.5), (0., 0.), (.4, 1.)))
    assert np.linalg.eigvalsh(constraints.hankel)[0] > -1e-12
    assert all(np.linalg.eigvalsh(localizer)[0] > -1e-12 for localizer in constraints.localizers)
    assert all(np.linalg.norm(residual) < 1e-13 for residual in constraints.equation_residuals)
    actual = v.conj().T@((1/(z-nodes))[:,None]*v)
    np.testing.assert_allclose(constraints.response, actual, atol=1e-13)
    reconstructed = method.rational_moments_from_seed(mm, nn[0], nn[1], z)
    np.testing.assert_allclose(reconstructed, nn, atol=1e-13)
    with pytest.raises(ValueError, match='unavailable'):
        method.moment_hankel(nn, 4)


@pytest.mark.numerical(oracle='Analytic scalar Weyl disk plus exact rational polynomial coefficient matching')
def test_verified_dual_envelope_certifies_bounds_and_charges_bad_coefficients():
    # For z=i and unit mass, 0 <= -Im R <= 1. The upper certificate
    # D(lambda)*1-1=lambda² has factor [0,1]. No optimization is trusted.
    exact = method.verify_dual_envelope([[[1.]]], [[[1.]]], [[-1j]], 1j, [[0., 1.]])
    assert exact.value == 1.
    assert exact.polynomial_allowance == 0
    assert Fraction(exact.exact_bound_numerator, exact.exact_bound_denominator) == 1
    broken = method.verify_dual_envelope([[[1.]]], [[[.1]]], [[-1j]], 1j, [[0., 1.]])
    assert broken.value >= 1.
    assert broken.polynomial_allowance > 0
    uncertain = method.verify_dual_envelope([[[1.]]], [[[1.]]], [[-1j]], 1j, [[0., 1.]], moment_error_bounds=[.02])
    assert uncertain.value >= 1.02
    lower = method.verify_dual_envelope([[[1.]]], [[[-1.]]], [[1j]], 1j, [[0., 1.]], direction='lower')
    assert lower.value == -1.


@pytest.mark.numerical(oracle='Direct complex two-port atomic response checked against exact-rational SOS dual envelope')
def test_complex_dual_envelope_with_localizer_and_rounding_allowance():
    nodes = np.array([-.8, .2, .7])
    ports = np.array([[1., .2j], [.3, .5], [.2j, -.4]])
    mass = ports.conj().T@ports
    # Enforce exact binary64 Hermiticity, as supplied empirical moments must have.
    mass = (mass+mass.conj().T)/2
    target = np.array([[0., 1.+.3j], [.2j, 0.]])
    result = method.verify_dual_envelope([mass], [2*np.eye(2)], target, .2+.7j,
        np.zeros((1, 4)), localizer_factors=(np.zeros((1, 2)),))
    response = ports.conj().T@((1/(.2+.7j-nodes))[:, None]*ports)
    objective = np.trace(target.conj().T@response).real
    assert objective <= result.value
    assert result.coefficient_residual_bound > 0


@pytest.mark.conformance
@pytest.mark.parametrize('operation', [
    lambda: method.acquire_block_krylov([[1., 2.], [0., 1.]], np.eye(2), 1),
    lambda: method.acquire_block_krylov(np.eye(2), np.zeros((2, 1)), 1),
    lambda: method.acquire_block_krylov(np.eye(2), np.eye(2), True),
    lambda: method.acquire_block_krylov(np.eye(2), np.eye(2), 1).prefix(2),
    lambda: method.constant_scalar_tail(1., 0., 1.),
    lambda: method.mechanical_admittance([[-1.]], [[1.]], 1.),
    lambda: method.finite_grid_mean_bridge([0., 0.], [1., 1.], 0., lambda s:0., beta=1., stiffness=1.),
    lambda: method.finite_grid_mean_bridge([0., 1.], [1., 1.], 0., lambda s:0., beta=1., stiffness=1., anchor_error_bound=.1),
    lambda: method.finite_record_variance([[[1.]]], [1.], 2),
    lambda: method.finite_record_variance([[[1.]], [[-2.]]], [1.], 2),
    lambda: method.rational_moment_constraints([[[1.]]], [[[1.]], [[1.]], [[1.]]], 1j, order=2),
    lambda: method.chebyshev_moments(np.diag([1.,2.]), [[1.],[1.]], 2, (1.1, 2.)),
    lambda: method.physical_remainder_bounds(1., 1., 1e5, beta=1.),
])
def test_invalid_scientific_or_numerical_contract_refuses(operation):
    with pytest.raises((ValueError, TypeError)):
        operation()


@pytest.mark.numerical(oracle='Central finite differences of an independently implemented nonlinear restrained potential')
def test_complete_nonlinear_restraint_jet_and_center_change():
    point = np.array([.4, -.3])
    # xi=x*y + .3*x^2 has an indefinite, full-rank Hessian.
    xi = point[0]*point[1]+.3*point[0]**2
    gradient = np.array([point[1]+.6*point[0], point[0]])
    hessian = np.array([[.6, 1.], [1., 0.]])
    center, stiffness = .8, 2.7
    jet = method.harmonic_restraint_jet(xi, gradient, hessian, center, stiffness)
    def energy(x, s):
        return .5*stiffness*(x[0]*x[1]+.3*x[0]**2-s)**2
    step = 2e-4
    finite_gradient = [(energy(point+step*e, center)-energy(point-step*e, center))/(2*step) for e in np.eye(2)]
    finite_hessian = np.array([[(energy(point+step*e+step*f, center)-energy(point+step*e-step*f, center)
                               -energy(point-step*e+step*f, center)+energy(point-step*e-step*f, center))/(4*step**2)
                              for f in np.eye(2)] for e in np.eye(2)])
    assert jet.energy == pytest.approx(energy(point, center))
    np.testing.assert_allclose(jet.gradient, finite_gradient, atol=2e-8)
    np.testing.assert_allclose(jet.hessian, finite_hessian, atol=5e-7)
    changed = method.harmonic_restraint_jet(xi, gradient, hessian, center+.7, stiffness)
    np.testing.assert_allclose(changed.hessian-jet.hessian, .7*jet.center_hessian_derivative, atol=1e-15)
    assert np.linalg.matrix_rank(changed.hessian-jet.hessian) == 2
    np.testing.assert_allclose(-changed.gradient+jet.gradient, .7*jet.center_force_port, atol=1e-15)


@pytest.mark.numerical(oracle='Independent central finite differences of dense resolvent with simultaneously moving operator and ports')
def test_differential_response_includes_moving_receiver_and_input():
    a, v = hermitian_case(7, 4)
    c, b = v[:, :2], v[:, 2:]
    da = np.diag(np.linspace(-.2, .3, 7))
    dc, db = .1*b, -.2*c
    z = .3+.8j
    result = method.resolvent_directional_derivative(a, c, b, z, da,
        receiver_derivative=dc, input_derivative=db)
    def query(t):
        return (c+t*dc).conj().T@np.linalg.solve(z*np.eye(7)-a-t*da, b+t*db)
    delta = 1e-5
    finite = (query(delta)-query(-delta))/(2*delta)
    np.testing.assert_allclose(result.derivative, finite, atol=2e-9)
    assert np.linalg.norm(result.receiver_term) > .1
    assert np.linalg.norm(result.input_term) > .1
    a1, a2 = da, .2*np.ones((7, 7))
    cross = .01*np.eye(7)
    mixed = method.resolvent_mixed_derivative(a, a1, a2, cross, z)
    def rq(t, s):
        return np.linalg.inv(z*np.eye(7)-a-t*a1-s*a2-t*s*cross)
    delta = 1e-4
    finite_mixed = (rq(delta, delta)-rq(delta, -delta)-rq(-delta, delta)+rq(-delta, -delta))/(4*delta**2)
    np.testing.assert_allclose(mixed, finite_mixed, atol=5e-8)


@pytest.mark.numerical(oracle='Exact two-mode cancellation has zero static response but nonzero dynamic response')
def test_physical_input_visibility_and_port_recombination():
    a = np.diag([1., 2.])
    c = np.ones((2, 1))
    b = np.array([[1., 0.], [-1., 1.]])
    shallow = method.input_visibility(a, c, b, 1)
    deeper = method.input_visibility(a, c, b, 2)
    assert shallow.rank == 1 and deeper.rank == 2
    np.testing.assert_allclose(shallow.moment_map@shallow.null_directions, 0., atol=1e-15)
    ports = np.column_stack((c, b))
    transform = np.array([[1., .5], [.3, -.2], [.1, .6]])
    z = .5+.2j
    response = ports.T@np.linalg.solve(z*np.eye(2)-a, ports)
    actual = (ports@transform).T@np.linalg.solve(z*np.eye(2)-a, ports@transform)
    np.testing.assert_allclose(method.recombine_ports(response, transform), actual, atol=1e-14)


@pytest.mark.numerical(oracle='Dense resolvent checks the complete no-SDP Chebyshev acquisition and explicit unresolved budget path')
def test_complete_chebyshev_acquisition_plans_finite_degree_and_reports_budget():
    a = np.diag(np.linspace(-1., 1., 17))
    v = np.column_stack((np.ones(17), np.linspace(-.5, .5, 17)))
    result = method.acquire_chebyshev_response(a, v, .3+1j, (-1., 1.), tolerance=1e-7)
    actual = v.T@np.linalg.solve((.3+1j)*np.eye(17)-a, v)
    assert result.tolerance_met and result.response.bound <= 1e-7
    assert np.linalg.norm(actual-result.response.estimate, 2) <= result.response.bound+1e-13
    assert result.action_count == 2*result.acquired_degree
    limited = method.acquire_chebyshev_response(a, v, .3+1j, (-1., 1.), tolerance=1e-7, maximum_degree=1)
    assert not limited.tolerance_met and limited.acquired_degree == 1
    assert limited.requested_degree > limited.acquired_degree


@pytest.mark.conformance
def test_callable_error_envelope_requires_integration_enclosure_and_quad_warning_refuses():
    estimate = method.finite_grid_mean_bridge([0., 1.], [.5, .5], 0., lambda s:s,
        beta=1., stiffness=1., anchor_error_bound=.01, variance_error_bound=lambda s:.02*s)
    assert estimate.upstream_error_bound is None
    assert estimate.upstream_error_estimate > 0
    assert estimate.total_error_bound is None
    bounded = method.finite_grid_mean_bridge([0., 1.], [.5, .5], 0., lambda s:s,
        beta=1., stiffness=1., anchor_error_bound=.01, variance_error_bound=lambda s:.02*s,
        integration_error_bound=1e-12)
    assert bounded.total_error_bound >= bounded.upstream_error_estimate
    with pytest.raises(ArithmeticError, match='did not converge'):
        method.finite_grid_mean_bridge([0., 1.], [.5, .5], 0., lambda s:math.sin(100000*s),
            beta=1., stiffness=1., quadrature_limit=1)


@pytest.mark.numerical(oracle='Exact inverse of a strongly nonnormal triangular matrix with an explicit singular-value bound')
def test_generic_inverse_residual_needs_actual_nonnormal_inverse_bound():
    z = np.array([[1., 20., 0.], [0., 1., 20.], [0., 0., 1.]])
    b, c = np.ones((3, 1)), np.array([[1.], [0.], [-1.]])
    x, y = np.array([[.1], [.2], [.3]]), np.array([[.2], [-.3], [.1]])
    norm_inverse = 1/np.linalg.svd(z, compute_uv=False)[-1]
    result = method.inverse_residual_response(c, b, x, y, z@x, z.T@y,
        inverse_norm_bound=norm_inverse)
    actual = c.T@np.linalg.solve(z, b)
    identity = result.dual_residual.T@np.linalg.solve(z, result.primal_residual)
    np.testing.assert_allclose(actual-result.estimate, identity, atol=1e-12)
    assert np.linalg.norm(actual-result.estimate, 2) <= result.bound
    assert norm_inverse > 100


@pytest.mark.numerical(oracle='Direct positive stiffness inverse with independently known diagonal lower spectral gap')
def test_static_joint_response_uses_true_gap_and_refuses_indefinite_reference():
    k = np.diag(np.linspace(.5, 4., 11))
    ports = np.column_stack((np.ones(11), np.linspace(-1., 1., 11)))
    prefix = method.acquire_block_krylov(k, ports, 3)
    result = method.static_galerkin_response(prefix, ports, lower_eigenvalue_bound=.5)
    actual = ports.T@np.linalg.solve(k, ports)
    assert np.linalg.norm(actual-result.estimate, 2) <= result.bound+1e-13
    with pytest.raises(ValueError, match='contradicts'):
        method.static_galerkin_response(prefix, ports, lower_eigenvalue_bound=100.)
    indefinite = method.acquire_block_krylov(np.diag([-1., 2.]), np.eye(2), 1)
    with pytest.raises(ValueError, match='positive'):
        method.static_galerkin_response(indefinite, np.eye(2), lower_eigenvalue_bound=.1)


@pytest.mark.numerical(oracle='Exact finite weighted canonical measures with a known global potential-oscillation bound')
def test_physical_remainder_bound_with_nonlinear_receiver_and_changed_measure():
    points = np.linspace(-2., 2., 21)
    reference = np.exp(-points**2/2)
    reference /= reference.sum()
    linear = points+.3
    nonlinear = linear+.1*points**2
    beta = 1.4
    remainder = .3*np.sin(points)
    actual = reference*np.exp(-beta*remainder)
    actual /= actual.sum()
    linear_mean = reference@linear
    v0 = reference@(linear-linear_mean)**2
    d0 = math.sqrt(reference@(nonlinear-linear)**2)
    mean = actual@nonlinear
    variance = actual@(nonlinear-mean)**2
    bounds = method.physical_remainder_bounds(v0, d0, np.ptp(remainder), beta=beta)
    assert bounds.variance_lower <= variance <= bounds.variance_upper
    assert abs(mean-linear_mean) <= bounds.mean_error_bound


@pytest.mark.conformance
def test_exact_dual_verifier_refuses_silent_hermitian_repair():
    with pytest.raises(ValueError, match='exactly Hermitian'):
        method.verify_dual_envelope([[[1., 1e-17], [0., 1.]]], [np.eye(2)],
            np.eye(2), 1j, np.zeros((1, 4)))
