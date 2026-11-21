# SPDX-License-Identifier: MPL-2.0
"""Canonical restraint transport and finite stationary-estimator uncertainty.

These operations preserve the caller's energy units. ``energy_scale=1000``
converts kJ/mol to J/mol exactly once; dimensionless controls use 1. A frozen
initialized trajectory supplies neither a canonical mean anchor nor stationarity.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import warnings
import numpy as np
from scipy.integrate import IntegrationWarning, quad
from scipy.special import logsumexp

from ._validation import array, hermitian, integer, norm, scalar


def _grid(centers, weights):
    centers = array(centers, 'centers', ndim=1, real=True)
    weights = array(weights, 'weights', ndim=1, real=True)
    if weights.shape != centers.shape or np.any(np.diff(centers) <= 0):
        raise ValueError('centers must strictly increase and have one real weight each')
    return centers, weights


@dataclass(frozen=True)
class MeanBridge:
    value: float
    anchor_term: float
    variance_term: float
    quadrature_error_estimate: float
    upstream_error_bound: float | None
    total_error_bound: float | None
    interval_weights: tuple[float, ...]
    interval_integrals: tuple[float, ...]
    upstream_error_estimate: float | None


def finite_grid_mean_bridge(centers, weights, anchor_difference, variance_difference, *, beta,
                            stiffness, energy_scale=1., anchor_error_bound=None,
                            variance_error_bound=None, integration_error_bound=None,
                            quadrature_tolerance=1e-10, quadrature_limit=200):
    """Exact finite-grid target as signed anchor plus weighted variance integrals.

    Anchor is mu_M(s_first)-mu_W(s_first); the callable supplies v_M(s)-v_W(s).
    Arbitrary real weights are preserved. SciPy quadrature errors are labelled
    estimates; a deterministic ``total_error_bound`` is returned only when
    upstream and integral enclosures have actually been supplied. A scalar
    ``variance_error_bound`` denotes a uniform envelope. A callable denotes a
    pointwise envelope and its integration still needs the supplied integration
    allowance. With a callable envelope, ``upstream_error_estimate`` is retained
    and ``upstream_error_bound`` remains None; only the supplied integration
    enclosure permits a complete target bound. Quadrature convergence warnings
    raise ArithmeticError. The integration allowance is in the output target's units and
    covers all numerical integrations, including that of the error envelope.
    """
    ss, ww = _grid(centers, weights)
    anchor = scalar(anchor_difference, 'anchor difference')
    beta = scalar(beta, 'beta', positive=True)
    k = scalar(stiffness, 'stiffness', positive=True)
    scale = scalar(energy_scale, 'energy scale', positive=True)
    tolerance = scalar(quadrature_tolerance, 'quadrature tolerance', positive=True)
    limit = integer(quadrature_limit, 'quadrature limit', minimum=1)

    def integrate(function, left, right):
        try:
            with warnings.catch_warnings():
                warnings.simplefilter('error', IntegrationWarning)
                value, error = quad(function, float(left), float(right),
                    epsabs=tolerance, epsrel=tolerance, limit=limit)
        except IntegrationWarning as exc:
            raise ArithmeticError('variance transport quadrature did not converge') from exc
        return scalar(value, 'quadrature value'), scalar(error, 'quadrature error estimate', nonnegative=True)
    if not callable(variance_difference):
        raise TypeError('variance difference must supply the center-dependent variance contrast')
    if (anchor_error_bound is None) != (variance_error_bound is None):
        raise ValueError('a target bound needs both anchor and variance error bounds')
    anchor_term = -scale*k*float(np.sum(ww))*anchor
    interval_weights, integrals = [], []
    variance_term, estimate, envelope_integral = 0., 0., 0.
    if anchor_error_bound is not None:
        anchor_error_bound = scalar(anchor_error_bound, 'anchor error bound', nonnegative=True)
        if not callable(variance_error_bound):
            variance_error_bound = scalar(variance_error_bound, 'variance error bound', nonnegative=True)
    for i, (left, right) in enumerate(zip(ss[:-1], ss[1:], strict=True)):
        weight = float(np.sum(ww[i+1:]))
        value, error = integrate(lambda s: scalar(variance_difference(s), 'variance contrast'), left, right)
        interval_weights.append(weight)
        integrals.append(value)
        variance_term -= scale*beta*k*k*weight*value
        estimate += scale*beta*k*k*abs(weight)*error
        if variance_error_bound is not None:
            if callable(variance_error_bound):
                envelope, error_estimate = integrate(lambda s: scalar(variance_error_bound(s),
                    'variance error envelope', nonnegative=True), left, right)
                estimate += scale*beta*k*k*abs(weight)*error_estimate
            else:
                envelope = (right-left)*variance_error_bound
            envelope_integral += abs(weight)*envelope
    upstream = None if anchor_error_bound is None else (scale*k*abs(float(np.sum(ww)))*anchor_error_bound
                    +scale*beta*k*k*envelope_integral)
    total = None
    if integration_error_bound is not None:
        if upstream is None:
            raise ValueError('integration error alone is not a complete target error bound')
        total = upstream+scalar(integration_error_bound, 'integration error bound', nonnegative=True)
    return MeanBridge(float(anchor_term+variance_term), float(anchor_term), float(variance_term),
        float(estimate), None if upstream is None or callable(variance_error_bound) else float(upstream),
        None if total is None else float(total), tuple(interval_weights), tuple(integrals),
        None if upstream is None else float(upstream))


def finite_grid_from_means(centers, weights, mutant_means, wildtype_means, *, stiffness, energy_scale=1.):
    """Direct original finite-grid Q, preserving the signed paired means."""
    centers, weights = _grid(centers, weights)
    m, w = array(mutant_means, 'mutant means', ndim=1, real=True), array(wildtype_means, 'wildtype means', ndim=1, real=True)
    if m.shape != centers.shape or w.shape != centers.shape:
        raise ValueError('mean arrays must match the declared finite grid')
    return -scalar(energy_scale, 'energy scale', positive=True)*scalar(stiffness, 'stiffness', positive=True)*float(weights@(m-w))


@dataclass(frozen=True)
class TiltedMoments:
    log_normalization: float
    mean: float
    variance: float
    third_cumulant: float
    effective_sample_size: float


def finite_center_tilt(receiver_values, log_weights, anchor_center, center, *, beta, stiffness):
    """Exact exponential tilt of a *supplied finite weighted measure*.

    If the weights approximate a native ensemble, this output remains an
    estimate. Effective sample size diagnoses weight concentration; it does not
    certify overlap, canonical preparation, or tail coverage.
    """
    xi = array(receiver_values, 'receiver values', ndim=1, real=True)
    logs = array(log_weights, 'log weights', ndim=1, real=True)
    if logs.shape != xi.shape:
        raise ValueError('receiver values and log weights must match')
    a, s = scalar(anchor_center, 'anchor center'), scalar(center, 'center')
    beta, k = scalar(beta, 'beta', positive=True), scalar(stiffness, 'stiffness', positive=True)
    normalized = logs-logsumexp(logs)
    shifted = normalized+beta*k*(s-a)*xi
    log_mgf = float(logsumexp(shifted))
    probabilities = np.exp(shifted-log_mgf)
    mean = float(probabilities@xi)
    centered = xi-mean
    return TiltedMoments(log_mgf-beta*k*(s*s-a*a)/2, mean,
        float(probabilities@centered**2), float(probabilities@centered**3),
        float(1/np.sum(probabilities**2)))


@dataclass(frozen=True)
class PhysicalRemainder:
    variance_lower: float
    variance_upper: float
    variance_error_bound: float
    mean_error_bound: float


def physical_remainder_bounds(reference_variance, receiver_rms_error, potential_oscillation, *, beta):
    """Density-ratio bounds under an actual global restrained-potential oscillation.

    A local Taylor remainder without normalization and outside-region moment
    control does not satisfy this contract. The reference variance must belong
    to the actual declared reference measure (not an unjustified Gaussian).
    """
    v = scalar(reference_variance, 'reference variance', nonnegative=True)
    d = scalar(receiver_rms_error, 'reference receiver RMS error', nonnegative=True)
    rho = scalar(beta, 'beta', positive=True)*scalar(potential_oscillation, 'potential oscillation', nonnegative=True)
    try:
        growth = math.exp(rho/2)
        upper = (growth*(math.sqrt(v)+d))**2
        lower = max(0., math.sqrt(v)/growth-growth*d)**2
        mean = math.expm1(rho)*math.sqrt(v)+growth*d
    except OverflowError as exc:
        raise ValueError('physical remainder bound overflows; no finite numerical enclosure') from exc
    if not all(math.isfinite(x) for x in (lower, upper, mean)):
        raise ValueError('physical remainder bound is nonfinite')
    return PhysicalRemainder(lower, upper, max(v-lower, upper-v), mean)


def finite_record_covariance(covariance_lags, record_length):
    """Exact covariance of a stationary vector record mean from known lags.

    Gamma(l)=E[h_(n+l) h_n^T]. All lags through N-1 are required; unavailable
    cross blocks cannot be filled with zeros except by a justified independence
    construction. This checks the resulting mean covariance, not stationarity.
    """
    gg = array(covariance_lags, 'covariance lags', ndim=3, real=True)
    n = integer(record_length, 'record length', minimum=1)
    if gg.shape[1] != gg.shape[2] or len(gg) < n:
        raise ValueError('need square joint covariance lags through record length minus one')
    g0 = hermitian(gg[0], 'zero-lag covariance')
    if np.linalg.eigvalsh(g0)[0] < -512*np.finfo(float).eps*max(norm(g0), 1.):
        raise ValueError('zero-lag covariance must be positive semidefinite')
    result = g0/n
    for lag in range(1, n):
        result += (n-lag)/(n*n)*(gg[lag]+gg[lag].T)
    tolerance = 512*np.finfo(float).eps*max(norm(g0), 1.)
    if np.linalg.eigvalsh(result)[0] < -tolerance:
        raise ValueError('supplied covariance lags imply a negative mean variance')
    return result


def finite_record_variance(covariance_lags, weights, record_length):
    """Signed whole-estimator variance, including measured paired cross-covariance."""
    covariance = finite_record_covariance(covariance_lags, record_length)
    weights = array(weights, 'signed target weights', ndim=1, real=True)
    if weights.shape != (len(covariance),):
        raise ValueError('signed weights and covariance dimension differ')
    value = float(weights@covariance@weights)
    # Only an arithmetic negative is rounded after the covariance PSD check.
    return max(0., value)


def finite_filter_variance(covariance_lags, filters):
    """Stationary joint estimator covariance with separate finite filters per port.

    ``filters[t,j]`` is the actual coefficient on h[t,j], including sample-length
    and target weights. Zero entries encode unused samples. This preserves
    unequal record lengths and declared sampling at one common base cadence.
    """
    gg = array(covariance_lags, 'covariance lags', ndim=3, real=True)
    ff = array(filters, 'component filters', real=True)
    if gg.shape[1:] != (ff.shape[1], ff.shape[1]) or len(gg) < len(ff):
        raise ValueError('joint covariance lags and component filters do not match')
    g0 = hermitian(gg[0], 'zero-lag covariance')
    if np.linalg.eigvalsh(g0)[0] < -512*np.finfo(float).eps*max(norm(g0), 1.):
        raise ValueError('zero-lag covariance must be positive semidefinite')
    value = math.fsum(float(row@g0@row) for row in ff)
    for lag in range(1, len(ff)):
        value += 2*math.fsum(float(later@gg[lag]@earlier)
                            for earlier, later in zip(ff[:-lag], ff[lag:], strict=True))
    if value < -512*np.finfo(float).eps*max(1., norm(g0)*norm(ff)**2):
        raise ValueError('supplied covariance lags imply a negative filter variance')
    return max(0., float(value))


def finite_record_window(theta, record_length):
    """w_N(theta)=|mean exp(i n theta)|², with the removable zero handled."""
    angles = np.asarray(theta, dtype=float)
    if not np.isfinite(angles).all():
        raise ValueError('frequencies must be finite')
    n = integer(record_length, 'record length', minimum=1)
    # Periodic reduction makes sinc stable near every multiple of 2*pi.
    reduced = (angles+np.pi)%(2*np.pi)-np.pi
    return (np.sinc(n*reduced/(2*np.pi))/np.sinc(reduced/(2*np.pi)))**2
