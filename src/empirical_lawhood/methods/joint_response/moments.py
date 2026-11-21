# SPDX-License-Identifier: MPL-2.0
"""Rational-moment outer constraints and independently verified dual envelopes.

No SDP optimizer is embedded. The finite constraint matrices can be passed to a
chosen solver; a primal optimum or solver status is never returned as a certified
outer bound. The dual verifier below uses exact rational arithmetic on the given
binary64 coefficients, PSD Gram *factors*, and an explicit remainder allowance.
It can verify externally optimized certificates without trusting their solver.
The Chebyshev route in ``spectral`` supplies an executable solver-free enclosure.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math
import numpy as np

from ._validation import array, hermitian, immutable, integer, scalar, spectral_point


def rational_moments_from_seed(original_moments, n0, n1, z):
    """N_(k+2)=M_k+2 Re(z) N_(k+1)-|z|²N_k, retaining physical joint mass."""
    mm = tuple(hermitian(m, 'original moment') for m in original_moments)
    nn = [hermitian(n0, 'N0'), hermitian(n1, 'N1')]
    z = spectral_point(z, upper=True)
    if not mm or any(m.shape != nn[0].shape for m in (*mm, nn[1])):
        raise ValueError('rational and original moments need one common square shape')
    for m in mm:
        nn.append(m+2*z.real*nn[-1]-abs(z)**2*nn[-2])
    return tuple(immutable(n) for n in nn)


def rational_resolvent(n0, n1, z):
    """R(z)=conj(z)N0-N1, with the anti-Herglotz sign convention."""
    a, b, z = hermitian(n0, 'N0'), hermitian(n1, 'N1'), spectral_point(z, upper=True)
    if a.shape != b.shape:
        raise ValueError('rational moments have different port dimensions')
    return z.conjugate()*a-b


def moment_hankel(weighted_moments, order):
    nn = tuple(hermitian(n, 'weighted moment') for n in weighted_moments)
    d = integer(order, 'Hankel order')
    if len(nn) < 2*d+1 or any(n.shape != nn[0].shape for n in nn):
        raise ValueError('Hankel matrix references unavailable or inconsistent moments')
    return np.block([[nn[i+j] for j in range(d+1)] for i in range(d+1)])


def moment_localizer(weighted_moments, polynomial, order):
    """[sum g_k N_(i+j+k)] for a caller-justified support polynomial g>=0."""
    nn = tuple(hermitian(n, 'weighted moment') for n in weighted_moments)
    g = array(polynomial, 'support polynomial', ndim=1, real=True)
    d = integer(order, 'localizer order')
    if len(nn) < 2*d+len(g) or any(n.shape != nn[0].shape for n in nn):
        raise ValueError('localizer references unavailable or inconsistent moments')
    return np.block([[sum((coefficient*nn[i+j+k] for k, coefficient in enumerate(g)),
                               np.zeros_like(nn[0])) for j in range(d+1)] for i in range(d+1)])


def support_polynomials(bands):
    """Outer-interval and forbidden-gap polynomials; isolated atoms may be bands [a,a]."""
    bands = tuple(tuple(scalar(x, 'spectral endpoint') for x in band) for band in bands)
    if not bands or any(len(b) != 2 or b[1] < b[0] for b in bands):
        raise ValueError('support needs nonempty ordered closed bands')
    if any(left[1] >= right[0] for left, right in zip(bands[:-1], bands[1:], strict=True)):
        raise ValueError('allowed bands must be strictly separated')
    a, b = bands[0][0], bands[-1][1]
    output = [(-a*b, a+b, -1.)]
    for left, right in zip(bands[:-1], bands[1:], strict=True):
        a, b = left[1], right[0]
        output.append((a*b, -(a+b), 1.))
    return tuple(output)


@dataclass(frozen=True, eq=False)
class RationalConstraints:
    hankel: np.ndarray
    localizers: tuple[np.ndarray, ...]
    mass_lower: np.ndarray
    mass_upper: np.ndarray
    response: np.ndarray
    equation_residuals: tuple[np.ndarray, ...]


def rational_moment_constraints(original_moments, weighted_moments, z, *, order, bands=None):
    """Evaluate the finite SDP's necessary PSD/equality constraints at supplied N.

    Numerical feasibility here is a diagnostic only. Extra feasible truncated
    sequences can widen a mathematically valid outer bound; no representing
    measure is asserted. Uncertain acquired moments belong in explicit SDP
    matrix inequalities, not an ignored equation residual.
    """
    mm = tuple(hermitian(m, 'original moment') for m in original_moments)
    nn = tuple(hermitian(n, 'weighted moment') for n in weighted_moments)
    z, d = spectral_point(z, upper=True), integer(order, 'relaxation order', minimum=1)
    if not mm or 2*d < len(mm)+1 or len(nn) < max(2*d+1, len(mm)+2) or any(n.shape != mm[0].shape for n in (*mm, *nn)):
        raise ValueError('rational constraint order exceeds the supplied moment sequence')
    equations = tuple(immutable(nn[k+2]-2*z.real*nn[k+1]+abs(z)**2*nn[k]-m)
                      for k, m in enumerate(mm))
    localizers = () if bands is None else tuple(immutable(moment_localizer(nn, g, d-1)) for g in support_polynomials(bands))
    return RationalConstraints(immutable(moment_hankel(nn, d)), localizers, nn[0],
        immutable(mm[0]/z.imag**2-nn[0]), immutable(rational_resolvent(nn[0], nn[1], z)), equations)


# Exact rational complex matrices are represented by real/imaginary object arrays.
# Every supplied binary64 value has an exact rational representation.
def _fractions(value):
    aa = np.asarray(value, dtype=complex)
    real = np.empty(aa.shape, dtype=object)
    imag = np.empty(aa.shape, dtype=object)
    for index in np.ndindex(aa.shape):
        real[index] = Fraction.from_float(float(aa[index].real))
        imag[index] = Fraction.from_float(float(aa[index].imag))
    return real, imag


def _zero(shape):
    return np.full(shape, Fraction(0), dtype=object), np.full(shape, Fraction(0), dtype=object)


def _add(left, right, factor=Fraction(1)):
    return left[0]+factor*right[0], left[1]+factor*right[1]


def _multiply(left, right):
    return left[0]@right[0]-left[1]@right[1], left[0]@right[1]+left[1]@right[0]


def _adjoint(value):
    return value[0].T, -value[1].T


def _hermitian_exact(value):
    return _add(value, _adjoint(value), Fraction(1))[0]/2, _add(value, _adjoint(value), Fraction(1))[1]/2


def _matrix_row_bound(value):
    # For Hermitian residuals, max absolute row sum bounds the operator norm.
    return max(sum((abs(a)+abs(b) for a, b in zip(rr, ii, strict=True)), Fraction(0))
               for rr, ii in zip(value[0], value[1], strict=True))


def _entry_sum(value):
    # Sum of entry magnitudes bounds nuclear norm (decompose into rank-one entries).
    return sum((abs(a)+abs(b) for a, b in zip(value[0].flat, value[1].flat, strict=True)), Fraction(0))


def _outward(value, upper):
    result = float(value)
    if not math.isfinite(result):
        raise ValueError('dual bound exceeds finite binary64 output range')
    exact = Fraction.from_float(result)
    if (upper and exact < value) or (not upper and exact > value):
        result = math.nextafter(result, math.inf if upper else -math.inf)
    return result


@dataclass(frozen=True)
class VerifiedDualBound:
    value: float
    direction: str
    moment_allowance: float
    polynomial_allowance: float
    coefficient_residual_bound: float
    exact_bound_numerator: int
    exact_bound_denominator: int
    verification: str = 'exact-rational binary64 inputs; PSD Gram factors; outward rounded result'


def verify_dual_envelope(original_moments, coefficients, target, z, gram_factor, *,
                         bands=((-1., 1.),), localizer_factors=(), direction='upper',
                         moment_error_bounds=None):
    """Verify an explicit rational-moment dual bound without trusting an optimizer.

    Y(lambda)=sum coefficients[k] lambda^k. The target is Re tr(W*R).
    ``gram_factor`` is F with columns grouped by polynomial power, so the Gram
    polynomial is Z*F*F Z and is PSD by construction. ``localizer_factors`` has
    either no items or one F per support polynomial returned by
    :func:`support_polynomials`. Factors may be rectangular and complex.

    For an upper bound, verify D_z Y-P_W = SOS + residual; for a lower bound,
    P_W-D_z Y = SOS + residual. All coefficient products, objective traces and
    mismatch allowances are exact rationals of the supplied finite binary64
    values. Every Gram factor is PSD without numerical eigenvalue tests. A
    coefficient mismatch delta(lambda) is conservatively charged using
    sup||delta|| tr(M0)/eta² on the declared compact support, including uncertainty
    in M0. This is often looser than an optimized certified solver but is a real
    checkable outer bound, not a feasible primal objective.
    """
    def exact_hermitian(value, name):
        result = array(value, name)
        if result.shape[0] != result.shape[1] or not np.array_equal(result, result.conj().T):
            raise ValueError(f'{name} must be exactly Hermitian as supplied to the rational verifier')
        return result

    mm = tuple(exact_hermitian(m, 'original moment') for m in original_moments)
    yy = tuple(exact_hermitian(y, 'dual coefficient') for y in coefficients)
    w, z = array(target, 'target'), spectral_point(z, upper=True)
    if not yy or len(mm) < len(yy) or w.shape != yy[0].shape or any(m.shape != w.shape for m in (*mm, *yy)):
        raise ValueError('dual coefficients, target and acquired moments must have matching dimensions')
    if direction not in ('upper', 'lower'):
        raise ValueError('dual direction must be upper or lower')
    polynomials = support_polynomials(bands)
    factors = (array(gram_factor, 'Gram factor'),)+tuple(array(f, 'localizer Gram factor') for f in localizer_factors)
    if len(localizer_factors) not in (0, len(polynomials)):
        raise ValueError('localizer factors must cover each declared support polynomial or none')
    p = len(w)
    if any(f.shape[1] % p for f in factors):
        raise ValueError('Gram-factor columns must group complete physical-port blocks')
    eps = np.zeros(len(yy)) if moment_error_bounds is None else array(moment_error_bounds, 'moment error bounds', ndim=1, real=True)
    if eps.shape != (len(yy),) or np.any(eps < 0):
        raise ValueError('one nonnegative simultaneous error bound per acquired dual moment is required')
    # Symmetrization is exact and leaves the required exactly-Hermitian inputs unchanged.
    yexact = tuple(_hermitian_exact(_fractions(y)) for y in yy)
    mexact = tuple(_hermitian_exact(_fractions(m)) for m in mm[:len(yy)])
    wexact = _fractions(w)
    zr, zi = Fraction.from_float(z.real), Fraction.from_float(z.imag)
    denominator = (zr*zr+zi*zi, -2*zr, Fraction(1))
    degree = max(len(yy)+1, max(2*(f.shape[1]//p-1)+(0 if j == 0 else 2) for j, f in enumerate(factors)))
    residual = [_zero((p, p)) for _ in range(degree+1)]
    sign = Fraction(1 if direction == 'upper' else -1)
    for k, y in enumerate(yexact):
        for j, d in enumerate(denominator):
            residual[k+j] = _add(residual[k+j], y, sign*d)
    # P_W=Herm(W* (conj(z)-lambda)).
    wz = (wexact[0].T*zr-wexact[1].T*zi,
          -wexact[0].T*zi-wexact[1].T*zr)
    p0 = _hermitian_exact(wz)
    p1 = _hermitian_exact((-wexact[0].T, wexact[1].T))
    residual[0], residual[1] = _add(residual[0], p0, -sign), _add(residual[1], p1, -sign)
    multipliers = ((Fraction(1),),)+tuple(tuple(Fraction.from_float(float(x)) for x in g) for g in polynomials[:len(localizer_factors)])
    # Reconstruct support multipliers exactly from their endpoints, not rounded products.
    if localizer_factors:
        rational_bands = tuple(tuple(Fraction.from_float(float(x)) for x in b) for b in bands)
        a, b = rational_bands[0][0], rational_bands[-1][1]
        exact_support = [(-a*b, a+b, Fraction(-1))]
        for left, right in zip(rational_bands[:-1], rational_bands[1:], strict=True):
            a, b = left[1], right[0]
            exact_support.append((a*b, -(a+b), Fraction(1)))
        multipliers = ((Fraction(1),),)+tuple(exact_support)
    for factor, multiplier in zip(factors, multipliers, strict=True):
        fe = _fractions(factor)
        count = factor.shape[1]//p
        blocks = [(fe[0][:, j*p:(j+1)*p], fe[1][:, j*p:(j+1)*p]) for j in range(count)]
        for i, left in enumerate(blocks):
            for j, right in enumerate(blocks):
                product = _multiply(_adjoint(left), right)
                for k, g in enumerate(multiplier):
                    residual[i+j+k] = _add(residual[i+j+k], product, -g)
    radius = max(abs(Fraction.from_float(float(x))) for band in bands for x in band)
    mismatch = sum((_matrix_row_bound(coefficient)*radius**k for k, coefficient in enumerate(residual)), Fraction(0))
    objective = Fraction(0)
    allowance = Fraction(0)
    for y, m, error in zip(yexact, mexact, eps, strict=True):
        product = _multiply(y, m)
        objective += sum(product[0].diagonal(), Fraction(0))
        allowance += Fraction.from_float(float(error))*_entry_sum(y)
    mass = sum(mexact[0][0].diagonal(), Fraction(0))+p*Fraction.from_float(float(eps[0]))
    if mass < 0:
        raise ValueError('zeroth moment trace bound must be nonnegative')
    polynomial_allowance = mismatch*mass/(zi*zi)
    value = objective+sign*(allowance+polynomial_allowance)
    return VerifiedDualBound(_outward(value, direction == 'upper'), direction,
        _outward(allowance, True), _outward(polynomial_allowance, True), _outward(mismatch, True),
        value.numerator, value.denominator)
