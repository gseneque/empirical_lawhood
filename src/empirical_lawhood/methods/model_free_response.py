# SPDX-License-Identifier: MPL-2.0
"""Fit-free response and equilibrium calculations with explicit evidence scopes.

Numerical bounds concern the supplied self-adjoint operator. They do not certify
finite native dynamics, canonical sampling, or physical model adequacy. The
caller owns actual force/receiver identities and every action acquisition.
"""
from __future__ import annotations

import math
from statistics import NormalDist

import numpy as np

from .joint_response import residual_response
from .retained_gaussian_response import HarmonicBath, trapezoid_weights


def _real(value, name, *, positive=False, nonnegative=False):
    if isinstance(value, (bool, np.bool_)) or np.iscomplexobj(value):
        raise ValueError(f'{name} must be real')
    value = float(value)
    if not math.isfinite(value) or positive and value <= 0 or nonnegative and value < 0:
        raise ValueError(f'{name} is outside its finite domain')
    return value


def _array(value, name, *, ndim=None, real=False):
    raw = np.asarray(value)
    if raw.dtype.kind not in 'iufc' or real and np.iscomplexobj(raw):
        raise ValueError(f'{name} must contain numerical values')
    value = np.asarray(raw, dtype=float if real else complex)
    if not value.size or ndim is not None and value.ndim != ndim or not np.isfinite(value).all():
        raise ValueError(f'{name} needs nonempty finite values and its declared dimensions')
    return value


def measured_rank(matrix, *, relative_tolerance=1e-12):
    """Numerical rank of actual values, separately from construction width."""
    a = _array(matrix, 'matrix', ndim=2)
    tol = _real(relative_tolerance, 'rank tolerance', nonnegative=True)
    singular = np.linalg.svd(a, compute_uv=False)
    threshold = tol * float(singular[0])
    return {'rank': int(np.sum(singular > threshold)), 'width': int(a.shape[1]),
            'singular_values': singular.tolist(), 'relative_tolerance': tol,
            'absolute_threshold': threshold}


def incremental_receiver_certificate(action, inputs, receivers, z, *, tolerance,
                                     max_actions, seed_basis=None,
                                     rank_tolerance=1e-12, operator_error_bound=0.):
    """Acquire a joint Galerkin prefix without repeated or hidden dense actions.

    Each column submitted to ``action`` counts as one action. Stopping tests use
    the dual-corrected residual identity and 1/abs(Im(z)). Callable actions must
    satisfy an externally qualified self-adjoint operator contract. Projected
    symmetry is a consistency check only. ``operator_error_bound`` is a uniform
    operator-norm bound, not an arbitrary per-observation confidence interval.
    """
    if not callable(action):
        raise TypeError('native action must be callable')
    b, c = _array(inputs, 'inputs', ndim=2), _array(receivers, 'receivers', ndim=2)
    if b.shape[0] != c.shape[0]:
        raise ValueError('ports need the same physical dimension')
    if type(max_actions) is not int or max_actions < 1:
        raise ValueError('max_actions must be a positive integer')
    tol = _real(tolerance, 'receiver tolerance', nonnegative=True)
    rt = _real(rank_tolerance, 'rank tolerance', nonnegative=True)
    error = _real(operator_error_bound, 'operator error', nonnegative=True)
    z = complex(z)
    if not np.isfinite(z) or z.imag == 0:
        raise ValueError('resolvent requires a finite off-real spectral point')
    seeds = np.column_stack((b, c)) if seed_basis is None else _array(seed_basis, 'seeds', ndim=2)
    if seeds.shape[0] != b.shape[0]:
        raise ValueError('seeds have a different physical dimension')
    u, s, _ = np.linalg.svd(seeds, full_matrices=False)
    seed_rank = int(np.sum(s > rt * (s[0] if s.size else 0)))
    if seed_rank == 0:
        raise ValueError('seed block has no nonzero direction')
    pending = u[:, :seed_rank]
    q = np.empty((b.shape[0], 0), dtype=complex)
    aq = q.copy()
    history = []
    result = None
    count = 0
    reason = 'ACTION_BUDGET_EXHAUSTED'
    while count < min(max_actions, len(b)) and pending.shape[1]:
        pending = pending[:, :min(max_actions - count, len(b) - count)]
        new_actions = _array(action(pending), 'native actions', ndim=2)
        if new_actions.shape != pending.shape:
            raise ValueError('native actions changed column shape')
        q = np.column_stack((q, pending))
        aq = np.column_stack((aq, new_actions))
        count += pending.shape[1]
        projected = q.conj().T @ aq
        asymmetry = np.linalg.norm(projected - projected.conj().T, 2)
        if asymmetry > 1024*np.finfo(float).eps*max(np.linalg.norm(aq, 2), 1.) + 2*error:
            raise ValueError('actions contradict the self-adjoint operator contract')
        projected = (projected + projected.conj().T)/2
        eye = np.eye(len(projected))
        xs = np.linalg.solve(z*eye - projected, q.conj().T @ b)
        ys = np.linalg.solve(z.conjugate()*eye - projected, q.conj().T @ c)
        result = residual_response(c, b, q@xs, q@ys, aq@xs, aq@ys, z,
                                   operator_error_bound=error)
        history.append({'action_count': count, 'rank': q.shape[1],
                        'residual_bound': float(result.bound)})
        if result.bound <= tol:
            reason = 'RECEIVER_ALLOWANCE_MET'
            break
        residual = new_actions.copy()
        for _ in range(2):
            residual -= q @ (q.conj().T @ residual)
        u, s, _ = np.linalg.svd(residual, full_matrices=False)
        rank = min(int(np.sum(s > rt*max(np.linalg.norm(new_actions, 2), np.finfo(float).tiny))),
                   len(b)-q.shape[1])
        pending = u[:, :rank]
        if rank == 0:
            reason = 'ACQUIRED_SPACE_EXHAUSTED_WITH_REMAINDER'
    assert result is not None
    return {'status': 'CERTIFIED' if result.bound <= tol else 'UNRESOLVED', 'reason': reason,
            'target_scope': 'HERMITIAN_RESOLVENT', 'supplier_class': 'deterministic certificate',
            'estimate_real': result.estimate.real.tolist(), 'estimate_imag': result.estimate.imag.tolist(),
            'residual_bound': float(result.bound), 'entrywise_bounds': result.entrywise_bounds.tolist(),
            'action_count': count, 'rank': q.shape[1], 'seed_rank': seed_rank,
            'input_defect': float(np.linalg.norm(b-q@(q.conj().T@b), 2)),
            'receiver_defect': float(np.linalg.norm(c-q@(q.conj().T@c), 2)),
            'orthogonality_error': float(np.linalg.norm(q.conj().T@q-np.eye(q.shape[1]), 2)),
            'action_prefix': history, 'operator_error_bound': error,
            'retained_basis':q.real.tolist() if not np.any(q.imag) else None,
            'projected_operator':projected.real.tolist() if not np.any(projected.imag) else None,
            'retained_basis_real':q.real.tolist(),'retained_basis_imag':q.imag.tolist(),
            'projected_operator_real':projected.real.tolist(),'projected_operator_imag':projected.imag.tolist(),
            'native_finite_response_certified': False,
            'premises': ['qualified self-adjoint native action', 'uniform operator error bound',
                         'fixed physical ports and off-real frequency'],
            'numerical_scope': 'binary64 evaluation of mathematical residual bound, not interval arithmetic'}


def native_response_error_budget(*, numerical, step, amplitude, operator_history,
                                 reduction, sampling=0., tolerance, future_path_used=False):
    """Compose independently supplied nonnegative bounds; missing terms refuse.

    No term is estimated here. Supplying zero asserts that term is exactly zero
    under the caller's declared contract. A future-path bound is retrospective.
    """
    fields = {'numerical': numerical, 'step': step, 'amplitude': amplitude,
              'operator_history': operator_history, 'reduction': reduction, 'sampling': sampling}
    tol = _real(tolerance, 'tolerance', nonnegative=True)
    missing = sorted(k for k, v in fields.items() if v is None)
    bounds = {k: None if v is None else _real(v, k, nonnegative=True) for k, v in fields.items()}
    total = None if missing else math.fsum(bounds.values())
    return {'status': 'UNRESOLVED' if total is None else ('CERTIFIED' if total <= tol else 'NOT_ADMITTED'),
            'target_scope': 'NATIVE_FINITE_RESPONSE', 'terms': bounds, 'total_bound': total,
            'tolerance': tol, 'missing_operands': missing,
            'information_schedule': 'RETROSPECTIVE' if future_path_used else 'BEFORE_CHALLENGE'}


def signed_error_account(reference_a, approximate_a, reference_b, approximate_b):
    """Signed paired receiver errors and the exact contrast-energy cross term."""
    values = [_array(x, 'signed receiver', real=True) for x in
              (reference_a, approximate_a, reference_b, approximate_b)]
    if any(x.shape != values[0].shape for x in values):
        raise ValueError('paired receiver arrays must match')
    ea, eb = values[1]-values[0], values[3]-values[2]
    contrast = eb-ea
    cross = float(np.vdot(ea, eb).real)
    energy_a, energy_b = float(np.vdot(ea, ea).real), float(np.vdot(eb, eb).real)
    energy = float(np.vdot(contrast, contrast).real)
    return {'error_a': ea.tolist(), 'error_b': eb.tolist(), 'contrast_error': contrast.tolist(),
            'energy_a': energy_a, 'energy_b': energy_b, 'signed_alignment': cross,
            'cross_term': -2*cross, 'contrast_energy': energy,
            'identity_residual': abs(energy-(energy_a+energy_b-2*cross))}


def signed_propagation_account(inherited, generated):
    a, b = _array(inherited, 'inherited', real=True), _array(generated, 'generated', real=True)
    if a.shape != b.shape:
        raise ValueError('signed propagation components must match')
    cross = 2*float(np.vdot(a, b).real)
    return {'inherited_vector': a.tolist(), 'generated_vector': b.tolist(),
            'total_vector': (a+b).tolist(), 'inherited_energy': float(np.vdot(a, a).real),
            'generated_energy': float(np.vdot(b, b).real), 'cross_term': cross,
            'total_energy': float(np.vdot(a+b, a+b).real)}


def couple_ou_normals(fine_normals, decay):
    """Exact two-half-step OU coupling: Zc=(a*Z1+Z2)/sqrt(1+a*a).

    ``decay`` is the damping factor of ONE fine half-step. The leading axis
    contains an even number of successive fine normals. Physical force pulses
    must separately retain their original times.
    """
    normals = _array(fine_normals, 'fine OU normals', real=True)
    a = _real(decay, 'fine-step damping', nonnegative=True)
    if a > 1 or normals.shape[0] % 2:
        raise ValueError('OU coupling requires 0<=decay<=1 and paired fine steps')
    return (a*normals[0::2]+normals[1::2])/math.sqrt(1+a*a)


def canonical_linear_control(positions, gradients, receiver, reference_precision):
    """Fixed Stein control using the actual COMPLETE native restrained gradient.

    Valid expectation identity requires Cartesian canonical measure, integrable
    score, and vanishing boundary terms. This calculation does not prove those
    premises or the sampler's invariant measure. No fitted coefficient is used.
    """
    x, g = _array(positions, 'positions', real=True), _array(gradients, 'native gradients', real=True)
    a = _array(receiver, 'linear receiver', ndim=1, real=True)
    k = _array(reference_precision, 'reference precision', ndim=2, real=True)
    if x.shape != g.shape or x.shape[-1] != len(a) or k.shape != (len(a), len(a)):
        raise ValueError('canonical control dimensions differ')
    if not np.allclose(k, k.T, rtol=0, atol=1e-12):
        raise ValueError('reference precision must be symmetric')
    np.linalg.cholesky(k)
    return x@a-g@np.linalg.solve(k, a)


def equilibrium_grid_estimate(root_center_means, centers, *, weights=None, reference=None,
                              alpha=.05, deterministic_allowance=None):
    """Finite-grid mean from independent complete roots, retaining paired covariance.

    Input shape is root x center, or root x arm x center. Two arms produce arm1-
    arm0. Each root's mean must already average its complete declared time record;
    using all times within each root preserves arbitrary within-record covariance
    in the across-root covariance. This does NOT establish equilibration or give
    a continuous-integral quadrature bound. The reported normal interval is an
    approximation, not distribution-free coverage.
    """
    values = _array(root_center_means, 'root center means', real=True)
    ss = _array(centers, 'centers', ndim=1, real=True)
    if len(ss) < 2 or np.any(np.diff(ss) <= 0) or values.ndim not in (2, 3) or values.shape[-1] != len(ss):
        raise ValueError('root means require a strictly increasing matching center grid')
    alpha = _real(alpha, 'alpha', positive=True)
    if alpha >= 1:
        raise ValueError('alpha must be below one')
    ww = trapezoid_weights(ss) if weights is None else _array(weights, 'weights', ndim=1, real=True)
    if ww.shape != ss.shape:
        raise ValueError('weights must match centers')
    if values.ndim == 3 and values.shape[1] != 2:
        raise ValueError('paired grid requires exactly two arms in declared order')
    contrasts = values if values.ndim == 2 else values[:, 1, :]-values[:, 0, :]
    root_targets = contrasts@ww
    mean = float(np.mean(root_targets))
    covariance = None if len(values) < 2 else np.atleast_2d(np.cov(values.reshape(len(values), -1), rowvar=False, ddof=1))/len(values)
    variance = None if len(values) < 2 else float(np.var(root_targets, ddof=1)/len(values))
    allowance = None if deterministic_allowance is None else _real(deterministic_allowance, 'deterministic allowance', nonnegative=True)
    halfwidth = None if variance is None else NormalDist().inv_cdf(1-alpha/2)*math.sqrt(max(0., variance))
    ref = None if reference is None else _real(reference, 'reference')
    return {'status': 'ESTIMATED' if variance is not None else 'UNRESOLVED',
            'target_scope': 'FINITE_GRID_ROOT_POPULATION_MEAN', 'mean': mean,
            'root_targets': root_targets.tolist(), 'independent_roots': len(values),
            'center_means': np.mean(contrasts, axis=0).tolist(), 'weights': np.asarray(ww).tolist(),
            'full_mean_covariance': None if covariance is None else covariance.tolist(),
            'variance_of_mean': variance, 'normal_approximation_halfwidth': halfwidth,
            'interval': None if halfwidth is None else [mean-halfwidth, mean+halfwidth],
            'deterministic_allowance': allowance,
            'total_normal_approximation_halfwidth': None if halfwidth is None or allowance is None else halfwidth+allowance,
            'absolute_reference_error': None if ref is None else abs(mean-ref),
            'canonical_measure_qualified': False, 'continuous_quadrature_bound': None,
            'uncertainty_scope': 'approximate independent-root normal interval; within-root dependence retained'}


def equilibrium_importance_endpoint(root_log_normalizations, centers, inverse_temperatures, *, alpha=.05):
    """Endpoint free energies from complete Gaussian-reference importance data.

    Center-independent reference and momentum normalizations cancel within
    each arm. The log of a finite Monte Carlo average is biased. Across-root
    covariance quantifies the finite estimator's variability only; it supplies
    neither a tail/overlap bound nor the missing finite-sample bias allowance.
    """
    logs = _array(root_log_normalizations, 'root log normalizations', real=True)
    beta = np.asarray(inverse_temperatures, dtype=float)
    if logs.ndim == 2:
        if beta.ndim != 0 or not np.isfinite(beta) or beta <= 0:
            raise ValueError('one importance arm requires its positive inverse temperature')
        energies = -logs / beta
    elif logs.ndim == 3 and logs.shape[1] == 2:
        if beta.shape != (2,) or not np.isfinite(beta).all() or np.any(beta <= 0):
            raise ValueError('paired importance arms require their own positive inverse temperatures')
        energies = -logs / beta[None, :, None]
    else:
        raise ValueError('importance endpoints require root x center or root x two arms x center')
    weights = np.zeros(logs.shape[-1])
    weights[0], weights[-1] = -1., 1.
    result = equilibrium_grid_estimate(energies, centers, weights=weights, alpha=alpha)
    result.update(target_scope='FINITE_SAMPLE_LOG_IMPORTANCE_ENDPOINT_ESTIMATOR',
        normalization_scope='CONFIGURATIONAL_REFERENCE_AND_MOMENTA_CANCEL_WITHIN_EACH_FIXED_TEMPERATURE_ARM',
        finite_sample_log_bias_bound=None, overlap_and_tail_bound=None,
        exact_free_energy_certified=False,
        uncertainty_scope='approximate independent-root normal interval for the finite log-importance estimator; not coverage for the exact free energy')
    return result


def equilibrium_variance_transport(root_means, root_second_moments, centers, inverse_temperatures, *, stiffness, alpha=.05):
    """Anchored variance transport using independent-root moment products.

    Each row contains two arms and their complete declared time-record moments.
    E[X^2] minus the cross-root U-statistic for E[X]^2 is unbiased for the
    variance of the declared root/time mixture, even with arbitrary within-root
    dependence. It represents canonical variance only under a qualified
    canonical-measure premise. Negative finite-sample estimates are retained.
    Delete-one-root jackknife uncertainty is approximate and keeps all arms,
    centers, mean anchors and second moments together.

    The target is the selected finite-grid sum of mean differences. Its
    interval weights are the discrete tails sum_{j>i} w_j, constant within
    each interval. Integrating the piecewise-linear variance there is exact
    for that represented finite-grid target. A continuous endpoint integral
    instead has a continuously varying tail kernel and is a different target.
    """
    means = _array(root_means, 'root means', real=True)
    second = _array(root_second_moments, 'root second moments', real=True)
    ss = _array(centers, 'centers', ndim=1, real=True)
    beta = _array(inverse_temperatures, 'inverse temperatures', ndim=1, real=True)
    k = _real(stiffness, 'restraint stiffness', positive=True)
    alpha = _real(alpha, 'alpha', positive=True)
    if alpha >= 1 or means.ndim != 3 or means.shape[1:] != (2, len(ss)) or second.shape != means.shape:
        raise ValueError('variance transport needs complete root x two arms x center moments and alpha below one')
    if beta.shape != (2,) or np.any(beta <= 0) or len(ss) < 2 or np.any(np.diff(ss) <= 0):
        raise ValueError('variance transport requires two inverse temperatures and an ordered center grid')
    scale = np.maximum(1., np.maximum(np.abs(second), means * means))
    if np.any(second - means * means < -64 * np.finfo(float).eps * scale):
        raise ValueError('a root second moment cannot be below its squared record mean')
    n = len(means)
    if n < 2:
        return {'status': 'UNRESOLVED', 'reason': 'TWO_INDEPENDENT_ROOTS_REQUIRED_FOR_MOMENT_PRODUCT',
                'independent_roots': n, 'mean': None, 'canonical_measure_qualified': False}
    weights = trapezoid_weights(ss)
    interval_weights = np.array([weights[j + 1:].sum() for j in range(len(ss) - 1)])

    def calculate(mean_sum, mean_square_sum, second_sum, count):
        average = mean_sum / count
        cross_root_square = (count * average * average - mean_square_sum / count) / (count - 1)
        variances = second_sum / count - cross_root_square
        variance_contrast = beta[1] * variances[1] - beta[0] * variances[0]
        intervals = .5 * (variance_contrast[:-1] + variance_contrast[1:]) * np.diff(ss)
        anchor = -k * weights.sum() * (average[1, 0] - average[0, 0])
        transported = -k * k * float(interval_weights @ intervals)
        return float(anchor + transported), variances, float(anchor), transported

    mean_sum, mean_square_sum, second_sum = means.sum(axis=0), (means * means).sum(axis=0), second.sum(axis=0)
    value, variances, anchor, transported = calculate(mean_sum, mean_square_sum, second_sum, n)
    # Sufficient sums make the complete-root jackknife linear in root count;
    # do not rebuild an N-1 population for each deletion.
    leave_one = None if n < 3 else [calculate(mean_sum - means[j], mean_square_sum - means[j] ** 2,
        second_sum - second[j], n - 1)[0] for j in range(n)]
    variance = None if leave_one is None else float((n - 1) / n * np.sum((np.asarray(leave_one) - np.mean(leave_one)) ** 2))
    halfwidth = None if variance is None else NormalDist().inv_cdf(1 - alpha / 2) * math.sqrt(max(0., variance))
    joint = np.concatenate((means.reshape(n, -1), second.reshape(n, -1)), axis=1)
    return {'status': 'ESTIMATED', 'independent_roots': n, 'mean': value,
        'anchor_term': anchor, 'variance_term': transported,
        'variance_estimates_by_arm_and_center': variances.tolist(),
        'negative_variance_estimate_cells': np.argwhere(variances < 0).tolist(),
        'full_mean_and_second_moment_covariance': (np.cov(joint, rowvar=False, ddof=1) / n).tolist(),
        'moment_covariance_order': 'all root means arm-major/center-minor, then all root second moments in the same order',
        'jackknife_leave_one_root_estimates': leave_one, 'jackknife_variance_of_estimator': variance,
        'normal_approximation_halfwidth': halfwidth,
        'interval': None if halfwidth is None else [value - halfwidth, value + halfwidth],
        'moment_estimator': 'INDEPENDENT_ROOT_CROSS_PRODUCT_U_STATISTIC',
        'unbiased_moment_scope': 'identically distributed independent roots and the same fixed time-record weights; arbitrary dependence within root',
        'target_scope': 'FINITE_GRID_ANCHORED_TRANSPORT_WITH_PIECEWISE_LINEAR_VARIANCE_INTERPOLATION',
        'continuous_variance_interpolation_error_bound': None, 'finite_step_measure_bias_bound': None,
        'canonical_measure_qualified': False,
        'uncertainty_scope': 'approximate delete-one-complete-root jackknife; no canonical, overlap, tail or interpolation certificate'}


def retained_residual_assessment(*, beta, residual_lower=None, residual_upper=None,
                                 reduced_variance=None, envelope_scope='sampled',
                                 tail_log_integral_bound=None):
    """Qualify a retained Gaussian residual without promoting sample maxima.

    The global log partition correction lies in [-beta*upper,-beta*lower].
    The receiver mean bound uses sqrt(var)*sinh(beta*oscillation/2), matching
    the existing residual theorem. A local tube requires a separate tail inquiry;
    this function intentionally does not convert an unspecified tail into zero.
    """
    from .retained_gaussian_response import ResidualEnvelope, receiver_residual_error
    beta = _real(beta, 'beta', positive=True)
    if envelope_scope not in ('sampled', 'local_tube', 'global'):
        raise ValueError('unknown residual envelope scope')
    if residual_lower is None or residual_upper is None:
        return {'status': 'UNRESOLVED', 'reason': 'MISSING_RESIDUAL_ENVELOPE'}
    lo, hi = _real(residual_lower, 'residual lower'), _real(residual_upper, 'residual upper')
    if hi < lo:
        raise ValueError('residual envelope endpoints reversed')
    if envelope_scope != 'global':
        return {'status': 'UNRESOLVED', 'reason': 'SAMPLED_EXTREMA_ARE_NOT_GLOBAL' if envelope_scope == 'sampled' else 'GLOBAL_TAIL_COMPOSITION_REQUIRED',
                'local_envelope': [lo, hi], 'tail_log_integral_bound': tail_log_integral_bound}
    envelope = ResidualEnvelope(lo, hi)
    bound = None if reduced_variance is None else float(receiver_residual_error(reduced_variance, envelope, beta=beta))
    if bound is not None and not math.isfinite(bound):
        return {'status':'UNRESOLVED','reason':'RECEIVER_BOUND_EXCEEDS_FINITE_NUMERICAL_RANGE',
                'log_partition_correction_bounds':[-beta*hi,-beta*lo],'receiver_mean_error_bound':None}
    return {'status': 'BOUNDED', 'scope': 'DECLARED_GLOBAL_RESIDUAL_ENVELOPE',
            'log_partition_correction_bounds': [-beta*hi, -beta*lo],
            'free_energy_correction_bounds': [lo, hi], 'receiver_mean_error_bound': bound,
            'premise': 'global residual envelope supplied independently; normalization retained'}


def harmonic_bath_trajectories(bath, *, beta, times, samples, seed,
                              preparation='canonical', retained_position=None,
                              retained_velocity=None):
    """Exact unit-mass ensemble trajectories of the existing finite harmonic bath.

    The block energy uses [[Kzz,B],[B.T,Kqq]], consistent with HarmonicBath.
    Canonical initializes the FULL coupled equilibrium. Conditional initializes
    the hidden canonical distribution at a fixed retained position and velocity.
    Finite undamped ensemble dynamics supplies no irreversible mixing claim.
    """
    if not isinstance(bath, HarmonicBath):
        raise TypeError('bath must be HarmonicBath')
    beta = _real(beta, 'beta', positive=True)
    ts = _array(times, 'physical times', ndim=1, real=True)
    if np.any(ts < 0) or np.any(np.diff(ts) < 0) or type(samples) is not int or samples < 1:
        raise ValueError('times must be ordered/nonnegative and samples positive')
    if type(seed) is not int or seed < 0:
        raise ValueError('seed must be a nonnegative integer')
    kzz, coupling, kqq = bath.retained_stiffness, bath.coupling, bath.bath_stiffness
    nz, nq = len(kzz), len(kqq)
    stiffness = np.block([[kzz, coupling], [coupling.T, kqq]])
    eigen, modes = np.linalg.eigh(stiffness)
    if np.min(eigen) <= 0:
        raise ValueError('full canonical bath must be positive definite')
    rng = np.random.default_rng(seed)
    if preparation == 'canonical':
        if retained_position is not None or retained_velocity is not None:
            raise ValueError('full canonical preparation cannot fix retained state')
        x = rng.normal(size=(samples, nz+nq)) @ (modes/np.sqrt(beta*eigen)).T
        p = rng.normal(size=x.shape)/math.sqrt(beta)
    elif preparation == 'conditional':
        z = _array(retained_position, 'retained position', ndim=1, real=True)
        v = _array(retained_velocity, 'retained velocity', ndim=1, real=True)
        if z.shape != (nz,) or v.shape != (nz,):
            raise ValueError('conditional retained state has wrong dimension')
        mean = -np.linalg.solve(kqq, coupling.T@z)
        q = mean + rng.normal(size=(samples, nq))@np.linalg.cholesky(np.linalg.inv(beta*kqq)).T
        x = np.column_stack((np.broadcast_to(z, (samples, nz)), q))
        p = np.column_stack((np.broadcast_to(v, (samples, nz)), rng.normal(size=(samples, nq))/math.sqrt(beta)))
    else:
        raise ValueError('preparation must be canonical or conditional')
    omega = np.sqrt(eigen)
    xm, pm = x@modes, p@modes
    phases = ts[:, None]*omega
    pos = ((xm[:, None, :]*np.cos(phases)+pm[:, None, :]*np.sin(phases)/omega)@modes.T)
    mom = ((pm[:, None, :]*np.cos(phases)-xm[:, None, :]*np.sin(phases)*omega)@modes.T)
    return {'positions': pos, 'momenta': mom, 'retained_positions': pos[:, :, :nz],
            'retained_momenta': mom[:, :, :nz], 'initial_positions': x, 'initial_momenta': p,
            'memory_kernel': np.stack([bath.memory(float(t)) for t in ts]),
            'effective_stiffness': bath.effective_stiffness, 'preparation': preparation,
            'physical_time': ts, 'scope': 'EXACT_FINITE_UNDAMPED_HARMONIC_ENSEMBLE',
            'irreversible_mixing_established': False}


def select_causal_response(native_response, candidate_predictions, *, cutoff_tick, target_tick,
                           normalizers=None, block_width=None, minimum_signal=0.):
    """Freeze a response supplier using only an observed prefix of the same task.

    Candidate states/parameters must already be available at ``cutoff_tick``.
    Scores use ticks 1..cutoff; no terminal or withheld-suffix value is inspected,
    even for validity checks. This supplies a conditional prefix forecast, not an
    origin forecast. Domain execution owns the prefix acquisition and its cost.
    Arrays have action x time x receiver layout. Normalizers have nonzero-time
    x receiver layout and are fixed physical scales, never learned from suffixes.
    """
    if type(cutoff_tick) is not int or type(target_tick) is not int or cutoff_tick < 1 or target_tick <= cutoff_tick:
        return {'status': 'UNRESOLVED', 'reason': 'NO_NONEMPTY_PREFIX_AND_WITHHELD_SUFFIX',
                'selected': None, 'cutoff_tick': cutoff_tick, 'target_tick': target_tick}
    if not isinstance(candidate_predictions, dict) or not candidate_predictions or any(not isinstance(k, str) for k in candidate_predictions):
        raise ValueError('selector requires named declared candidate predictions')
    target = np.asarray(native_response)
    if target.ndim != 3 or target.shape[1] <= cutoff_tick:
        raise ValueError('native observation lacks the declared prefix')
    prefix = _array(target[:, 1:cutoff_tick+1, :], 'observed native prefix', ndim=3, real=True)
    width = prefix.shape[-1] if block_width is None else block_width
    if type(width) is not int or width < 1 or prefix.shape[-1] % width:
        raise ValueError('receiver block width must divide the receiver dimension')
    if normalizers is None:
        scale = np.ones(prefix.shape[1:])
    else:
        raw = np.asarray(normalizers)
        if raw.ndim != 2 or raw.shape[0] < cutoff_tick or raw.shape[1] != prefix.shape[-1]:
            raise ValueError('normalizers do not cover the selected prefix')
        scale = _array(raw[:cutoff_tick], 'prefix physical normalizers', ndim=2, real=True)
        if np.any(scale <= 0):
            raise ValueError('physical normalizers must be positive')
    signal = float(np.max(np.linalg.norm((prefix/scale).reshape(-1,width),axis=-1)))
    minimum = _real(minimum_signal, 'minimum prefix signal', nonnegative=True)
    if signal < minimum:
        return {'status':'UNRESOLVED','reason':'NO_USEFUL_PREFIX_SIGNAL','selected':None,
                'cutoff_tick':cutoff_tick,'target_tick':target_tick,'prefix_signal':signal}
    scores, unavailable = {}, {}
    for name, prediction in sorted(candidate_predictions.items()):
        prediction = np.asarray(prediction)
        if prediction.ndim != 3 or prediction.shape[0] != prefix.shape[0] or prediction.shape[-1] != prefix.shape[-1] or prediction.shape[1] <= cutoff_tick:
            unavailable[name] = 'MISSING_COMPLETE_PREFIX'
            continue
        selected = prediction[:,1:cutoff_tick+1,:]
        if np.iscomplexobj(selected) or not np.isfinite(selected).all():
            unavailable[name] = 'NONFINITE_PREFIX'
            continue
        delta=(selected-prefix)/scale
        scores[name]=float(np.max(np.linalg.norm(delta.reshape(-1,width),axis=-1)))
    chosen=min(scores,key=lambda key:(scores[key],key)) if scores else None
    return {'status':'SELECTED' if chosen is not None else 'UNRESOLVED',
            'reason':None if chosen is not None else 'NO_VALID_CANDIDATE_PREFIX',
            'selected':chosen,'prefix_scores':scores,'unavailable':unavailable,
            'cutoff_tick':cutoff_tick,'target_tick':target_tick,'prefix_signal':signal,
            'selection_rule':'MINIMUM_DECLARED_PREFIX_BLOCK_ERROR_THEN_LEXICAL_ID',
            'target_scope':'CONDITIONAL_FORECAST_ON_WITHHELD_SUFFIX_AFTER_CUTOFF',
            'suffix_values_used':False,'native_prefix_required':True}
