# SPDX-License-Identifier: MPL-2.0
"""Independent native-force, recorded-transition and estimator reconstruction."""
import json
import numpy as np
from scipy.stats import t

from empirical_lawhood.domains.matrix.six_matrix_response.gradients import SixMatrixParameters, analytic_gradient_terms
from empirical_lawhood.domains.matrix.six_matrix_response.shooting import hermitian_basis
from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02_science import Computation, measurements
from empirical_lawhood.domains.matrix.matrix_equilibrium_bridge import science
from empirical_lawhood.domains.matrix.matrix_equilibrium_bridge.physics import paired_series, trapezoid_weights


def correlation_diagnostic(values):
    """Initial positive adjacent-lag sums; the tail flag is only a diagnostic."""
    x = np.asarray(values, dtype=float)-np.mean(values)
    n = len(x)
    variance = x@x/n
    if variance <= 0: return np.array([-1., -1., 0.])
    rho = np.array([x[:-lag]@x[lag:]/(n-lag)/variance for lag in range(1, n//2+1)])
    total, stopped = 0., False
    for i in range(0, len(rho)-1, 2):
        pair = rho[i]+rho[i+1]
        if pair <= 0:
            stopped = True
            break
        total += pair
    tau = max(1., 1+2*total)
    return np.array([tau, n/tau, float(stopped and n >= 20*tau)])


def scalar_force_checks(design, positions, gradients, centers):
    basis = hermitian_basis(4)
    maximum = 0.
    scale = float(design.alpha_y)**2/36
    for view in range(2):
        for prep in range(2):
            for arm, c in enumerate(design.couplings):
                parameters = SixMatrixParameters(2, .5, .5, float(c), float(design.alpha_x), float(design.alpha_y))
                for node, center in enumerate(centers):
                    for q, actual in zip(positions[view, prep, arm, node], gradients[view, prep, arm, node], strict=True):
                        matrix = np.einsum('sjk,kab->sjab', q.reshape(2, 3, 16), basis)
                        expected = analytic_gradient_terms(matrix, parameters).total
                        radius = np.dot(q[48:], q[48:])/(12*scale)
                        expected[1] += float(design.stiffness)*(radius-center)*matrix[1]/(6*scale)
                        projected = np.einsum('kab,sjab->sjk', basis.conj(), expected).real.reshape(96)
                        maximum = max(maximum, float(np.max(abs(projected-actual)))/(1+float(np.max(abs(projected)))))
    return maximum


def observables(design, positions, gradients, centers):
    x, y = positions[..., :48], positions[..., 48:]
    gx, gy = gradients[..., :48], gradients[..., 48:]
    scale = float(design.alpha_y)**2/36
    xi, chi = np.sum(y*y, axis=-1)/(12*scale), np.sum(x*x, axis=-1)/12
    s = np.asarray(centers)[None, None, None, :, None]
    t0 = float(design.temperature)
    cy = t0*8/scale-np.sum(y*gy, axis=-1)/(6*scale)
    cx = t0*8-np.sum(x*gx, axis=-1)/6
    return np.stack((float(design.stiffness)*(s-xi), cy,
        (xi-s)*cy+t0*xi/(3*scale), chi*cy, (xi-s)*cx), axis=-1)


def transition_check(design, values):
    h = float(design.timestep); rho = np.exp(-float(design.friction)*h)
    sigma = np.sqrt(float(design.temperature)*(1-rho*rho))
    q0, p0, g0, q1, p1, g1, noise = np.moveaxis(values, 1, 0)
    pb = p0-h*g0/2
    po = rho*pb+sigma*noise
    wanted_q = q0+h*(pb+po)/2
    wanted_p = po-h*g1/2
    return max(float(np.max(abs(wanted_q-q1))), float(np.max(abs(wanted_p-p1))))


def assess(config, values):
    d, bank = config.design, config.root.bank
    mult = d.reference_multiplier if bank == 'REFERENCE' else 1
    centers = np.asarray(d.grid(bank), dtype=float)
    count = d.production_steps*mult//d.sample_stride
    shape = (2, 2, 2, len(centers), count, 96)
    total_steps = (d.burn_steps+d.production_steps)*mult
    if (values['positions'].shape != shape or values['gradients'].shape != shape
            or values['observables'].shape != (*shape[:-1], 5)
            or values['kinetic_temperature'].shape != shape[:-1]
            or values['warmup_radial'].shape != (2, 2, 2, len(centers), d.burn_steps*mult//d.sample_stride)
            or values['witnesses'].shape != (total_steps//1024, 7, 2, 2, len(centers), 96)
            or not np.array_equal(values['witness_ticks'], np.arange(1024, total_steps+1, 1024))
            or not np.array_equal(values['centers'], centers)
            or not np.array_equal(values['sample_ticks'], np.arange(d.burn_steps*mult+d.sample_stride,
                (d.burn_steps+d.production_steps)*mult+1, d.sample_stride))):
        raise ValueError('SCI02-D retained samples change their exact complete clocks or census')
    if not all(np.isfinite(v).all() for v in values.values()): raise ValueError('nonfinite retained SCI02-D array')
    random = json.loads(values['random_custody'].astype('u1').tobytes())
    if random['bit_generator'] != 'PCG64DXSM' or random['numpy'] != '2.4.6': raise ValueError('SCI02-D random implementation drift')
    if random['stream_identities'] != [p.to_document() for p in config.root.streams]:
        raise ValueError('SCI02-D native recorder changes its committed original stream identities')
    if (random['coarse_draw_shape'] != [total_steps, 2, 1, len(centers), 96]
            or random['bridge_draw_shape'] != random['coarse_draw_shape']
            or set(random['before']) != {'INITIAL_MOMENTUM', 'COARSE_INNOVATION', 'FINE_BRIDGE'}
            or set(random['after']) != set(random['before'])):
        raise ValueError('SCI02-D recorder changes original noise counts or state census')
    gradient_residual = scalar_force_checks(d, values['positions'], values['gradients'], centers)
    observation = observables(d, values['positions'], values['gradients'], centers)
    observable_residual = float(np.max(abs(observation-values['observables'])))/(1+float(np.max(abs(observation))))
    transition_residual = transition_check(d, values['witnesses'])
    series = paired_series(observation, centers)
    coef = science.coefficient_array(config.fitted)
    fractions = np.ones(3) if config.fitted is None else np.array(config.fitted.sampling_fractions, dtype=float)
    estimates, prefix, counts = science.estimates(series, coef, fractions)
    widths = np.empty((2, 3)); doubled = np.empty((2, 3))
    correlation = np.empty((2, 2, 3, 2, 3))
    node_covariance = np.empty((2, 2, 3, 2*len(centers), 2*len(centers)))
    for view in range(2):
        for method in range(3):
            n = counts[method]
            corrected = series[view, ..., 0]-series[view, ..., 1:]@coef[method]
            z = corrected[:, :n].mean(axis=0)
            for prep in range(2):
                correlation[view, prep, method, 0] = correlation_diagnostic(corrected[prep])
                correlation[view, prep, method, 1] = correlation_diagnostic(corrected[prep, :n])
                # Preserve all arm/node covariances before the signed integral.
                nodes = observation[view, prep, ..., 0]-observation[view, prep, ..., 1:]@coef[method]
                blocked = nodes.reshape(2*len(centers), -1, d.block_samples).mean(axis=-1)
                node_covariance[view, prep, method] = np.cov(blocked, ddof=1)
            for length, dest in ((d.block_samples, widths), (2*d.block_samples, doubled)):
                b = z.reshape(-1, length).mean(axis=1)
                dest[view, method] = (t.ppf(.975, len(b)-1)*np.std(b, ddof=1)/np.sqrt(len(b)) if len(b)>1 else -1.)
    five = series if bank != 'REFERENCE' else paired_series(observation[:, :, :, ::2], centers[::2])
    five_estimates, _, _ = science.estimates(five, coef, np.ones(3))
    reason = []
    if gradient_residual > 1e-10: reason.append('NATIVE_FORCE_RECONSTRUCTION_FAILED')
    if observable_residual > 1e-10: reason.append('CONTROL_RECEIVER_RECONSTRUCTION_FAILED')
    if transition_residual > 1e-10: reason.append('RECORDED_BAOAB_RECONSTRUCTION_FAILED')
    halves = np.stack((series[..., :count//2, :].mean(axis=-2), series[..., count//2:, :].mean(axis=-2)))
    chronological = halves[..., 0, None]-np.einsum('...k,mk->...m', halves[..., 1:], coef)
    weights = trapezoid_weights(centers)
    signed_weights = np.r_[-weights, weights]
    paired_block_variance = np.einsum('i,vpmij,j->vpm', signed_weights, node_covariance, signed_weights)
    out = {'series': series, 'node_means': observation.mean(axis=-2), 'estimates': estimates, 'prefix_estimates': prefix,
        'prefix_half_widths': widths, 'doubled_block_half_widths': doubled, 'prefix_sample_counts': counts,
        'five_node_estimates': five_estimates, 'half_estimates': halves, 'chronological_half_estimates': chronological,
        'correlation_diagnostics': correlation, 'arm_node_block_covariances': node_covariance, 'paired_block_variance': paired_block_variance,
        'kinetic_means': values['kinetic_temperature'].mean(axis=-1),
        'warmup_half_means': np.stack((values['warmup_radial'][..., :values['warmup_radial'].shape[-1]//2].mean(axis=-1),
            values['warmup_radial'][..., values['warmup_radial'].shape[-1]//2:].mean(axis=-1))),
        'reconstruction_residuals': np.array([gradient_residual, observable_residual, transition_residual])}
    return Computation(out, 'AVAILABLE' if not reason else 'PARTIAL', tuple(sorted(reason)), measurements=measurements({
        'assessment.gradient_relative_residual': gradient_residual, 'assessment.observable_relative_residual': observable_residual,
        'assessment.transition_absolute_residual': transition_residual, 'assessment.all_sampled_forces_checked': np.prod(shape[:-1]),
        'assessment.reference_production_frames': count, 'assessment.numerical_pass': int(not reason),
        'assessment.equilibrium_admitted': 0}))
