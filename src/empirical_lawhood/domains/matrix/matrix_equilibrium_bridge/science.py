# SPDX-License-Identifier: MPL-2.0
"""Solvable controls, frozen response fit and complete finite-cohort reductions."""
from dataclasses import replace
from decimal import Decimal
import time

import numpy as np
from scipy.integrate import quad
from scipy.stats import t, beta as beta_distribution

from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02_science import Computation, measurements
from empirical_lawhood.domains.matrix.matrix_equilibrium_bridge.records import BridgeFit, METHODS


def with_cost(result, cpu, wall):
    return replace(result, measurements=tuple(sorted((*result.measurements,
        *measurements({'runtime.cpu_seconds': time.process_time()-cpu, 'runtime.wall_seconds': time.monotonic()-wall})))))


def controls():
    h = np.array([[3., .7], [.7, 2.]])
    k, s = 4., .4
    matrix = h+np.diag([k, 0.])
    mean = np.linalg.solve(matrix, [k*s, 0.])
    v = np.linalg.solve(matrix, [k, 0.])
    points = np.array([[0., 0.], [1., -.5], [-.7, 1.2], mean])
    grad = points@matrix.T-[k*s, 0.]
    corrected = k*(s-points[:, 0])+grad@v
    harmonic_error = float(np.max(abs(corrected-k*(s-mean[0]))))
    nodes = np.linspace(-1., 0., 9)
    means, partitions, quad_errors, zero_errors, grids = [], [], [], [], []
    from numpy.polynomial.legendre import leggauss
    for c in (.5, 2.):
        row, zs, errs, zeros = [], [], [], []
        for center in nodes:
            def weight(x): return np.exp(-2*(x*x-1)**2-.5*k*(x-center)**2)/np.sqrt(1+c*x*x)
            z, ez = quad(weight, -np.inf, np.inf, epsabs=1e-12, epsrel=1e-12)
            m, em = quad(lambda x: k*(center-x)*weight(x), -np.inf, np.inf, epsabs=1e-12, epsrel=1e-12)
            # After exact conditional Gaussian integration over y, E[-U_x|x].
            cv, ec = quad(lambda x: -(8*x*(x*x-1)+c*x/(1+c*x*x)+k*(x-center))*weight(x),
                -np.inf, np.inf, epsabs=1e-12, epsrel=1e-12)
            row.append(m/z); zs.append(z); errs.append((ez, em, ec)); zeros.append(cv/z)
        means.append(row); partitions.append(zs); quad_errors.append(errs); zero_errors.append(zeros)
        # Independent bounded tensor quadrature of the original 2-D force.
        values = []
        for order in (96, 160):
            x, wx = leggauss(order); y, wy = leggauss(order)
            x, wx, y, wy = 4*x, 4*wx, 12*y, 12*wy
            xx, yy = x[:, None], y[None, :]
            center = -.5
            density = np.exp(-2*(xx*xx-1)**2-.5*(1+c*xx*xx)*yy*yy-.5*k*(xx-center)**2)
            weights = wx[:, None]*wy[None, :]*density
            force = -(8*xx*(xx*xx-1)+c*xx*yy*yy+k*(xx-center))
            values.append([np.sum(weights*k*(center-xx))/np.sum(weights), np.sum(weights*force)/np.sum(weights)])
        grids.append(values)
    from empirical_lawhood.domains.matrix.matrix_equilibrium_bridge.physics import trapezoid_weights
    means, partitions = np.array(means), np.array(partitions)
    integral = float(trapezoid_weights(nodes)@(means[1]-means[0]))
    exact_restrained = float(-np.log(partitions[1, -1]/partitions[1, 0])+np.log(partitions[0, -1]/partitions[0, 0]))
    exact_pmf = .5*np.log(1.5/3.)
    zero = float(np.max(np.abs(zero_errors)))
    grid = np.array(grids)
    grid_error = float(np.max(abs(grid[:, -1, 0]-means[:, 4])))
    passed = harmonic_error < 1e-12 and zero < 1e-10 and grid_error < 1e-8 and np.max(abs(grid[:, -1, 1])) < 1e-8
    arrays = {'harmonic_corrected': corrected, 'centers': nodes, 'node_means': means, 'partitions': partitions,
        'quadrature_errors': np.array(quad_errors), 'zero_means': np.array(zero_errors), 'tensor_quadrature': grid,
        'connections': np.array([integral, exact_restrained, exact_pmf, exact_pmf-exact_restrained, exact_restrained-integral])}
    return Computation(arrays, 'AVAILABLE' if passed else 'UNAVAILABLE', () if passed else ('SOLVABLE_CONTROL_FAILURE',),
        measurements=measurements({'control.harmonic_residual': harmonic_error, 'control.zero_mean_residual': zero,
            'control.independent_quadrature_residual': grid_error, 'control.passed': int(passed)}))


def blocks(series, length):
    n = series.shape[-2]
    if n % length: raise ValueError('SCI02-D keeps every selected sample in its block denominator')
    return series.reshape((*series.shape[:-2], n//length, length, series.shape[-1])).mean(axis=-2)


def coefficient_array(fitted):
    return np.zeros((3, 4)) if fitted is None else np.array(fitted.coefficients, dtype=float)


def estimates(series, coefficients, fractions):
    full, prefix, available = [], [], []
    for beta, fraction in zip(coefficients, fractions, strict=True):
        corrected = series[..., 0]-series[..., 1:]@beta
        count = int(round(corrected.shape[-1]*fraction))
        full.append(corrected.mean(axis=-1)); prefix.append(corrected[..., :count].mean(axis=-1))
        available.append(count)
    return np.stack(full, axis=-1), np.stack(prefix, axis=-1), np.array(available, dtype='<i8')


def fit(config, parents, arrays):
    selected = sorted((p for p in parents.values() if p.config.phase == 'assess'), key=lambda p: p.config.root.ordinal)
    if len(selected) != 16 or tuple(p.config.root.ordinal for p in selected) != tuple(range(16)):
        raise ValueError('SCI02-D fit must retain all sixteen original development bundles')
    covariance = np.zeros((5, 5)); degrees = 0
    for product in selected:
        series = arrays[product.config.node_id]['series'][0]
        blocked = blocks(series, config.design.block_samples)
        centered = blocked-blocked.mean(axis=-2, keepdims=True)
        covariance += np.einsum('pbi,pbj->ij', centered, centered)
        degrees += 2*(blocked.shape[-2]-1)
    covariance /= degrees
    coefficients = np.zeros((3, 4))
    if covariance[1, 1] > 0: coefficients[1, 0] = covariance[0, 1]/covariance[1, 1]
    ridge = float(config.design.ridge_fraction)*max(np.max(np.diag(covariance)[1:]), np.finfo(float).tiny)
    coefficients[2] = np.linalg.solve(covariance[1:, 1:]+ridge*np.eye(4), covariance[1:, 0])
    contrast = np.column_stack((np.ones(3), -coefficients))
    variances = np.einsum('mi,ij,mj->m', contrast, covariance, contrast)
    variance_available = covariance[0, 0] > 0
    ratios = variances/covariance[0, 0] if variance_available else np.ones(3)
    fractions = tuple(next((Decimal(str(f)) for f in (.25, .5, 1.) if f >= r), Decimal(1)) for r in ratios)
    fitted = BridgeFit('fit.'+config.node_id, config.design.identity, tuple(p.identity for p in selected),
        tuple(tuple(Decimal(repr(float(v))) for v in row) for row in coefficients), fractions)
    reasons = [] if all(p.disposition == 'AVAILABLE' for p in parents.values()) else ['DEVELOPMENT_NUMERICAL_ASSESSMENT_FAILED']
    if not variance_available: reasons.append('DEVELOPMENT_NATIVE_VARIANCE_UNAVAILABLE')
    reasons = tuple(sorted(reasons))
    result = Computation({'covariance': covariance, 'coefficients': coefficients, 'variance_ratios': ratios,
        'sampling_fractions': np.array(fractions, dtype=float), 'ridge': np.array([ridge]), 'covariance_degrees': np.array([degrees], dtype='<i8')},
        'AVAILABLE' if not reasons else 'PARTIAL', reasons, measurements=measurements({
            'fit.training_roots': 16, 'fit.structure_variance_ratio': ratios[2], 'fit.coordinate_variance_ratio': ratios[1],
            'fit.ridge': ridge, 'fit.variance_ratio_available': int(variance_available), 'fit.complete_numerical_controls': int(not reasons)}))
    return result, fitted


def mean_interval(values):
    x = np.asarray(values)
    n = len(x)
    mean = np.mean(x, axis=0)
    half = t.ppf(.975, n-1)*np.std(x, axis=0, ddof=1)/np.sqrt(n)
    return mean, half


def confirm(config, parents, arrays):
    held = sorted((p for p in parents.values() if p.config.root.bank == 'CONFIRMATION'), key=lambda p:p.config.root.ordinal)
    reference = sorted((p for p in parents.values() if p.config.root.bank == 'REFERENCE'), key=lambda p:p.config.root.ordinal)
    if len(held) != 64 or len(reference) != 8: raise ValueError('SCI02-D confirmation loses its full original banks')
    h = [arrays[p.config.node_id] for p in held]; r = [arrays[p.config.node_id] for p in reference]
    # Reference uncertainty and all numerical/preparation views remain explicit.
    reference_five = np.array([a['five_node_estimates'][..., 0] for a in r])
    reference_nine = np.array([a['estimates'][..., 0] for a in r])
    ref_mean, ref_half = mean_interval(reference_five.mean(axis=2))
    nine_mean, nine_half = mean_interval(reference_nine.mean(axis=2))
    target = ref_mean[1]
    estimates_full = np.array([a['estimates'].mean(axis=1) for a in h])
    prefix = np.array([a['prefix_estimates'].mean(axis=1) for a in h])
    widths = np.array([a['prefix_half_widths'] for a in h])
    errors = prefix[:, 0]-target
    full_errors = estimates_full[:, 0]-target
    bias, bias_half = mean_interval(errors)
    view_gap = prefix[:, 0]-prefix[:, 1]
    view_mean, view_half = mean_interval(view_gap)
    prep_gap = np.array([a['prefix_estimates'][0, 0]-a['prefix_estimates'][0, 1] for a in h])
    prep_mean, prep_half = mean_interval(prep_gap)
    chronological_gap = np.array([(a['chronological_half_estimates'][0]-a['chronological_half_estimates'][1]).mean(axis=1) for a in h])
    chronological_mean, chronological_half = mean_interval(chronological_gap)
    correlations = np.array([a['correlation_diagnostics'] for a in h])
    doubled_widths = np.array([a['doubled_block_half_widths'] for a in h])
    quad_mean, quad_half = mean_interval((reference_nine-reference_five).mean(axis=2))
    native_variance = np.var(estimates_full[:, 0, 0], ddof=1)
    variance_ratio = np.var(estimates_full[:, 0], axis=0, ddof=1)/native_variance if native_variance > 0 else np.ones(3)
    cover = np.sum(abs(errors) <= widths[:, 0], axis=0)
    conservative_cover = np.sum(abs(errors)+ref_half[1] <= widths[:, 0], axis=0)
    numerical = abs(view_mean)+view_half <= float(config.design.numerical_allowance)
    preparation = abs(prep_mean)+prep_half <= float(config.design.preparation_allowance)
    quadrature = abs(quad_mean[1])+quad_half[1] <= float(config.design.quadrature_allowance)
    sampling_budget = float(config.design.target_error-config.design.numerical_allowance-config.design.quadrature_allowance-config.design.preparation_allowance)
    _, delivered_mean_half = mean_interval(prefix[:, 0])
    precision = delivered_mean_half <= sampling_budget
    accurate = abs(bias)+bias_half+ref_half[1] <= float(config.design.target_error)
    precision_counts = np.sum((widths[:, 0] >= 0) & (widths[:, 0] <= sampling_budget), axis=0)
    point_error_counts = np.sum(abs(errors)+ref_half[1] <= float(config.design.target_error), axis=0)
    reasons = ['MOLECULAR_SUPPLIERS_NOT_ESTABLISHED', 'EQUILIBRIUM_STATE_COVERAGE_NOT_ESTABLISHED',
        'OPERATIONAL_SAVING_RECONSTRUCTED_NOT_DEPLOYED']
    if native_variance <= 0: reasons.append('CONFIRMATION_NATIVE_VARIANCE_UNAVAILABLE')
    if not quadrature: reasons.append('QUADRATURE_ALLOWANCE_UNRESOLVED_OR_EXCEEDED')
    if not np.all(numerical): reasons.append('NUMERICAL_ALLOWANCE_UNRESOLVED_OR_EXCEEDED')
    if not np.all(preparation): reasons.append('PREPARATION_ALLOWANCE_UNRESOLVED_OR_EXCEEDED')
    if not np.all(precision): reasons.append('SAMPLING_PRECISION_UNRESOLVED')
    if not np.all(accurate): reasons.append('PAIRED_TARGET_ACCURACY_UNRESOLVED')
    if not np.all(correlations[..., 2]): reasons.append('CORRELATION_TAIL_DIAGNOSTIC_UNRESOLVED')
    if any(p.disposition != 'AVAILABLE' for p in parents.values()): reasons.append('NATIVE_NUMERICAL_ASSESSMENT_FAILED')
    coverage_bounds = np.array([[0. if n == 0 else beta_distribution.ppf(.025, n, 65-n),
        1. if n == 64 else beta_distribution.ppf(.975, n+1, 64-n)] for n in cover])
    out = {'reference_five': reference_five, 'reference_nine': reference_nine,
        'reference_mean_half': np.stack((ref_mean, ref_half)), 'reference_nine_mean_half': np.stack((nine_mean, nine_half)),
        'estimates': estimates_full, 'prefix_estimates': prefix, 'prefix_half_widths': widths, 'signed_errors': errors,
        'full_signed_errors': full_errors, 'bias_half': np.stack((bias, bias_half)),
        'view_mean_half': np.stack((view_mean, view_half)), 'preparation_mean_half': np.stack((prep_mean, prep_half)),
        'chronological_mean_half': np.stack((chronological_mean, chronological_half)),
        'correlation_diagnostics': correlations, 'doubled_block_half_widths': doubled_widths,
        'quadrature_mean_half': np.stack((quad_mean, quad_half)), 'variance_ratios': variance_ratio,
        'coverage_counts': cover.astype('<i8'), 'coverage_binomial_intervals': coverage_bounds,
        'conservative_coverage_counts': conservative_cover.astype('<i8'),
        'individual_sampling_precision_counts': precision_counts.astype('<i8'),
        'reference_adjusted_point_error_counts': point_error_counts.astype('<i8'),
        'diagnostic_passes': np.stack((numerical, preparation, precision, accurate)).astype('|b1')}
    measured = {'confirmation.complete_roots': 64, 'reference.complete_roots': 8, 'reference.fine_mean': target,
        'reference.fine_half_width': ref_half[1], 'reference.quadrature_difference': quad_mean[1],
        'reference.quadrature_half_width': quad_half[1], 'molecular.eligible': 0, 'qualification.established': 0,
        'equilibrium.admitted': 0, 'saving.actual_avoided_reference_calls': 0}
    for j, method in enumerate(METHODS):
        measured.update({method+'.prefix_bias': bias[j], method+'.prefix_rmse': np.sqrt(np.mean(errors[:, j]**2)),
            method+'.full_rmse': np.sqrt(np.mean(full_errors[:, j]**2)), method+'.full_variance_ratio': variance_ratio[j],
            method+'.coverage_count': cover[j], method+'.mean_sampling_half_width': delivered_mean_half[j],
            method+'.individual_sampling_precision_count': precision_counts[j], method+'.reference_adjusted_point_error_count': point_error_counts[j],
            method+'.numerical_diagnostic_pass': int(numerical[j]), method+'.preparation_diagnostic_pass': int(preparation[j])})
    return Computation(out, 'PARTIAL', tuple(sorted(reasons)), measurements=measurements(measured))
