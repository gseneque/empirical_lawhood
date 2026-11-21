# SPDX-License-Identifier: MPL-2.0
"""Joint self-adjoint response and finite acquisition bounds.

The convention is R(z)=(zI-A)^-1. Mechanical stiffness eigenvalues are squared
frequencies. Native underdamped Langevin step maps are not self-adjoint by
assertion. Dense input checks Hermiticity; callable actions require the supplier's
self-adjoint operator contract. Returned bounds are mathematical error bounds
on the supplied operator, numerically evaluated in binary64, not interval-arithmetic
certificates of physical model adequacy or statistical coverage.
"""
from __future__ import annotations

from dataclasses import dataclass
import cmath
import math
import numpy as np

from ._validation import array, hermitian, immutable, integer, norm, scalar, spectral_point


@dataclass(frozen=True, eq=False)
class KrylovPrefix:
    """Reusable acquired actions; truncating a prefix never reacquires the operator."""
    basis: np.ndarray
    actions: np.ndarray
    projected: np.ndarray
    seed_factor: np.ndarray
    block_sizes: tuple[int, ...]
    action_count: int
    discarded_norm: float
    seed_residual_norm: float
    orthogonality_error: float
    operator_error_bound: float
    invariant: bool

    def prefix(self, blocks):
        count = integer(blocks, 'prefix blocks', minimum=1)
        if count > len(self.block_sizes):
            raise ValueError('prefix requests unacquired blocks')
        dimension = sum(self.block_sizes[:count])
        q, aq = self.basis[:, :dimension], self.actions[:, :dimension]
        t = q.conj().T@aq
        return KrylovPrefix(q, aq, immutable((t+t.conj().T)/2),
            self.seed_factor, self.block_sizes[:count], dimension, self.discarded_norm,
            self.seed_residual_norm, norm(q.conj().T@q-np.eye(dimension)),
            self.operator_error_bound, self.invariant and count == len(self.block_sizes))


def acquire_block_krylov(operator, seeds, blocks, *, rank_tolerance=1e-12,
                         operator_error_bound=0.):
    """Acquire a twice-reorthogonalized, rank-deflated joint Krylov prefix.

    ``operator`` is a Hermitian dense matrix or a callable accepting a column
    block and returning its native actions. The caller owns self-adjointness and
    the uniform action error bound for a callable; projected symmetry is only a
    consistency check. Numerical rank deflation is retained in ``discarded_norm``;
    the later residual calculation uses all acquired AQ, including that defect.
    Physical seed amplitudes remain in ``seed_factor`` and explicit ports.
    """
    v = array(seeds, 'physical seeds')
    blocks = integer(blocks, 'blocks', minimum=1)
    tolerance = scalar(rank_tolerance, 'rank tolerance', nonnegative=True)
    action_error = scalar(operator_error_bound, 'operator error bound', nonnegative=True)
    if callable(operator):
        action = operator
    else:
        a = hermitian(operator, 'operator')
        if a.shape[0] != v.shape[0]:
            raise ValueError('operator and physical seeds have different dimensions')
        action = lambda q: a@q
    u, singular, vh = np.linalg.svd(v, full_matrices=False)
    cutoff = tolerance*singular[0] if singular.size else 0.
    rank = int(np.count_nonzero(singular > cutoff))
    if rank == 0:
        raise ValueError('physical seed block has no retained direction')
    q = u[:, :rank]
    seed_factor = singular[:rank, None]*vh[:rank]
    seed_residual = norm(v-q@seed_factor)
    qs, aqs, sizes, discarded = [], [], [], 0.
    invariant = False
    for block in range(blocks):
        aq = array(action(q), 'native operator action')
        if aq.shape != q.shape:
            raise ValueError('native action changes the physical block shape')
        qs.append(q)
        aqs.append(aq)
        sizes.append(q.shape[1])
        whole = np.column_stack(qs)
        w = aq.copy()
        for _ in range(2):
            w -= whole@(whole.conj().T@w)
        u, singular, _ = np.linalg.svd(w, full_matrices=False)
        cutoff = tolerance*max(norm(aq), np.finfo(float).tiny)
        rank = min(int(np.count_nonzero(singular > cutoff)), v.shape[0]-whole.shape[1])
        if rank < len(singular):
            discarded = max(discarded, float(singular[rank]))
        if rank == 0:
            invariant = norm(w) <= 512*np.finfo(float).eps*max(norm(aq), np.finfo(float).tiny)
            break
        if block+1 < blocks:
            q = u[:, :rank]
    q, aq = np.column_stack(qs), np.column_stack(aqs)
    t = q.conj().T@aq
    # The action contract allows a declared operator error, but not arbitrary
    # unexplained non-Hermiticity in the acquired projection.
    symmetry_error = norm(t-t.conj().T)
    allowed = 1024*np.finfo(float).eps*max(norm(aq), 1.)+2*action_error
    if symmetry_error > allowed:
        raise ValueError('acquired actions violate the declared self-adjoint operator contract')
    return KrylovPrefix(immutable(q), immutable(aq), immutable((t+t.conj().T)/2),
        immutable(seed_factor), tuple(sizes), q.shape[1], discarded, seed_residual,
        norm(q.conj().T@q-np.eye(q.shape[1])), action_error, invariant)


@dataclass(frozen=True, eq=False)
class ResidualResponse:
    estimate: np.ndarray
    raw_estimate: np.ndarray
    bound: float
    entrywise_bounds: np.ndarray
    primal_residual: np.ndarray
    dual_residual: np.ndarray
    primal_trial: np.ndarray
    dual_trial: np.ndarray


def residual_response(receiver, inputs, primal_trial, dual_trial, primal_action,
                      dual_action, z, *, operator_error_bound=0., inverse_norm_bound=None):
    """Dual correction and exact residual identity using supplied native actions.

    For self-adjoint A, E_B=B-(zI-A)X and E_C=C-(conj(z)I-A)Y.
    Returns C*X+Y*E_B and ||E_C||||E_B||/|Im z|. With approximate
    actions the uniform action error is propagated both through residual norms
    and the computed correction. ``inverse_norm_bound`` may tighten the default
    only when independently justified by the supplier.
    """
    z = spectral_point(z)
    c, b, x, y, ax, ay = [array(value, name) for value, name in (
        (receiver, 'receiver'), (inputs, 'inputs'), (primal_trial, 'primal trial'),
        (dual_trial, 'dual trial'), (primal_action, 'primal action'), (dual_action, 'dual action'))]
    if x.shape != b.shape or y.shape != c.shape or ax.shape != x.shape or ay.shape != y.shape or b.shape[0] != c.shape[0]:
        raise ValueError('response trial/action/port shapes do not match')
    inverse = 1/abs(z.imag) if inverse_norm_bound is None else scalar(inverse_norm_bound, 'inverse norm bound', positive=True)
    return inverse_residual_response(c, b, x, y, z*x-ax, z.conjugate()*y-ay,
        inverse_norm_bound=inverse, operator_error_bound=operator_error_bound)



def galerkin_response(prefix, ports, z, *, inputs=None):
    """Joint or cross response from a prefix; no new operator actions."""
    if not isinstance(prefix, KrylovPrefix):
        raise TypeError('prefix must be an acquired KrylovPrefix')
    z = spectral_point(z)
    c = array(ports, 'ports')
    b = c if inputs is None else array(inputs, 'inputs')
    q, aq, t = prefix.basis, prefix.actions, prefix.projected
    if c.shape[0] != q.shape[0] or b.shape[0] != q.shape[0]:
        raise ValueError('ports and prefix have different physical dimensions')
    identity = np.eye(t.shape[0])
    xs = np.linalg.solve(z*identity-t, q.conj().T@b)
    ys = np.linalg.solve(z.conjugate()*identity-t, q.conj().T@c)
    return residual_response(c, b, q@xs, q@ys, aq@xs, aq@ys, z,
        operator_error_bound=prefix.operator_error_bound)


def finite_update_response(response_cb, response_cu, response_uu, response_ub, update):
    """Exact C*R1B for A1=A0+UDU*, including singular/indefinite D.

    All four joint blocks must refer to the same z, physical ports, operator and
    preparation. The arithmetic cannot establish those scientific identities.
    No inverse of D is used. Conditioning of the small solve remains observable.
    """
    cb, cu, uu, ub = [array(v, n) for v, n in (
        (response_cb, 'response CB'), (response_cu, 'response CU'),
        (response_uu, 'response UU'), (response_ub, 'response UB'))]
    d = hermitian(update, 'finite update')
    r = d.shape[0]
    if uu.shape != (r, r) or cu.shape != (cb.shape[0], r) or ub.shape != (r, cb.shape[1]):
        raise ValueError('joint response blocks and finite update dimensions differ')
    return cb+cu@np.linalg.solve(np.eye(r)-d@uu, d@ub)


def finite_static_update(response_cb, response_cu, response_uu, response_ub, update):
    """Exact static K^-1 update; caller must establish updated positive stiffness."""
    return -finite_update_response(-np.asarray(response_cb), -np.asarray(response_cu),
        -np.asarray(response_uu), -np.asarray(response_ub), update)


def omitted_update_bound(receiver, inputs, omitted_operator_norm, z):
    """Hermitian omitted update E: ||C*(Rtrue-Rlowrank)B|| <= ||C||||B||||E||/eta^2."""
    z = spectral_point(z)
    return norm(array(receiver, 'receiver'))*norm(array(inputs, 'inputs'))*scalar(
        omitted_operator_norm, 'omitted operator norm', nonnegative=True)/z.imag**2


def finite_auxiliary_self_energy(tail, coupling, z):
    """Exact W(zI-T)^-1W* for a supplied finite Hermitian tail."""
    t, w, z = hermitian(tail, 'tail'), array(coupling, 'coupling'), spectral_point(z)
    if w.shape[1] != t.shape[0]:
        raise ValueError('tail and coupling dimensions differ')
    return w@np.linalg.solve(z*np.eye(len(t))-t, w.conj().T)


def schur_head(diagonals, upper_couplings, z, *, terminal_self_energy=None):
    """Exact backward Schur recursion with rectangular deflated block couplings."""
    z = spectral_point(z)
    aa = tuple(hermitian(a, 'Jacobi diagonal') for a in diagonals)
    bb = tuple(array(b, 'upper coupling') for b in upper_couplings)
    if not aa or len(bb) != len(aa)-1:
        raise ValueError('a Jacobi chain needs one fewer coupling than diagonal blocks')
    for i, b in enumerate(bb):
        if b.shape != (aa[i].shape[0], aa[i+1].shape[0]):
            raise ValueError('Jacobi upper coupling has the wrong orientation or shape')
    sigma = np.zeros_like(aa[-1], dtype=complex) if terminal_self_energy is None else array(terminal_self_energy, 'terminal self energy')
    if sigma.shape != aa[-1].shape:
        raise ValueError('terminal self energy has the wrong shape')
    f = np.linalg.solve(z*np.eye(len(aa[-1]))-aa[-1]-sigma, np.eye(len(aa[-1])))
    for a, b in reversed(tuple(zip(aa[:-1], bb, strict=True))):
        f = np.linalg.solve(z*np.eye(len(a))-a-b@f@b.conj().T, np.eye(len(a)))
    return f


def constant_scalar_tail(z, diagonal, coupling):
    """Physical semi-infinite scalar branch; cancellation-safe quadratic roots."""
    z = spectral_point(z, upper=True)
    a, b = scalar(diagonal, 'diagonal'), scalar(coupling, 'coupling', nonnegative=True)
    # Scale before subtracting/squaring, so finite huge queries do not overflow
    # and evaluating the unphysical reciprocal root cannot cause division by zero.
    scale = max(abs(z.real), abs(z.imag), abs(a), b)
    w = z/scale-a/scale
    if b == 0:
        result = (1/scale)/w
        if not np.isfinite(result):
            raise ArithmeticError('scalar tail response exceeds finite binary64 range')
        return result
    root = cmath.sqrt(w*w-4*(b/scale)**2)
    # The upper-half-plane physical square-root branch has positive imaginary part.
    if root.imag < 0:
        root = -root
    result = (2/scale)/(w+root)
    if not np.isfinite(result) or result.imag > 0:
        raise ArithmeticError('could not resolve the physical scalar tail branch')
    # An imaginary part may underflow to -0.0 for an otherwise finite asymptotic query.
    return result



@dataclass(frozen=True, eq=False)
class PeriodicTail:
    responses: tuple[np.ndarray, ...]
    iterations: int
    residual_norm: float
    error_bound: float | None
    converged: bool


def periodic_block_tail(diagonals, outgoing_couplings, z, *, tolerance=1e-12, maximum_iterations=10000):
    """Physical fixed-point iteration for a declared periodic block tail.

    Coupling j maps block j+1 into j, with cyclic indexing. A rigorous contraction
    rate is available only when max||B_j||^2/eta^2 < 1; otherwise convergence is a
    numerical result and ``error_bound`` is None. No unmeasured periodicity is inferred.
    """
    aa = tuple(hermitian(a, 'periodic diagonal') for a in diagonals)
    bb = tuple(array(b, 'periodic outgoing coupling') for b in outgoing_couplings)
    z = spectral_point(z, upper=True)
    tol = scalar(tolerance, 'tolerance', positive=True)
    maximum = integer(maximum_iterations, 'maximum iterations', minimum=1)
    if not aa or len(aa) != len(bb):
        raise ValueError('periodic tail needs one outgoing coupling per block')
    for j, b in enumerate(bb):
        if b.shape != (len(aa[j]), len(aa[(j+1)%len(aa)])):
            raise ValueError('periodic coupling has the wrong orientation')
    fs = tuple(np.linalg.solve(z*np.eye(len(a))-a, np.eye(len(a))) for a in aa)
    contraction = max(norm(b)**2 for b in bb)/z.imag**2
    difference = math.inf
    for iteration in range(1, maximum+1):
        new = tuple(np.linalg.solve(z*np.eye(len(a))-a-b@fs[(j+1)%len(aa)]@b.conj().T,
                     np.eye(len(a))) for j, (a, b) in enumerate(zip(aa, bb, strict=True)))
        difference = max(norm(g-f) for f, g in zip(fs, new, strict=True))
        fs = new
        stopping_tolerance = tol*(1-contraction) if contraction < 1 else tol
        if difference <= stopping_tolerance:
            break
    residual = max(norm(np.linalg.inv(f)-(z*np.eye(len(a))-a-b@fs[(j+1)%len(aa)]@b.conj().T))
                   for j, (a, b, f) in enumerate(zip(aa, bb, fs, strict=True)))
    bound = difference*contraction/(1-contraction) if contraction < 1 else None
    converged = (bound <= tol) if bound is not None else difference <= tol
    return PeriodicTail(tuple(immutable(f) for f in fs), iteration, residual, bound, converged)


def tail_error_bound(approximate_heads, upper_couplings, z, *, tail_error=None):
    """Propagate a valid normalized-tail error through known head resolvents."""
    z = spectral_point(z, upper=True)
    ff = tuple(array(f, 'approximate head') for f in approximate_heads)
    bb = tuple(array(b, 'coupling') for b in upper_couplings)
    if len(ff) != len(bb):
        raise ValueError('one approximate head is required per outward coupling')
    error = 2/z.imag if tail_error is None else scalar(tail_error, 'tail error', nonnegative=True)
    for f, b in reversed(tuple(zip(ff, bb, strict=True))):
        if f.shape != (b.shape[0], b.shape[0]):
            raise ValueError('tail error propagation has inconsistent block dimensions')
        left, right = norm(f@b), norm(b.conj().T@f)
        candidates = [2/z.imag, norm(b)*right*error/z.imag, left*norm(b)*error/z.imag]
        denominator = 1-error*norm(b.conj().T@f@b)
        if denominator > 0:
            candidates.append(left*right*error/denominator)
        error = min(candidates)
    return float(error)


def mechanical_admittance(stiffness, ports, laplace_frequency):
    """Force-to-velocity s V*(s^2 I+K)^-1 V; checks the whole K is nonnegative."""
    k, v = hermitian(stiffness, 'stiffness'), array(ports, 'ports')
    s = complex(laplace_frequency)
    if not np.isfinite(s) or s.real <= 0 or v.shape[0] != len(k):
        raise ValueError('admittance requires Re(s)>0 and matching physical ports')
    if np.linalg.eigvalsh(k)[0] < 0:
        raise ValueError('mechanical passivity requires nonnegative complete stiffness')
    return s*(v.conj().T@np.linalg.solve(s*s*np.eye(len(k))+k, v))


@dataclass(frozen=True, eq=False)
class PolynomialResponse:
    estimate: np.ndarray
    truncation_bound: float
    acquisition_bound: float
    degree: int
    convergence_ratio: float

    @property
    def bound(self):
        return self.truncation_bound+self.acquisition_bound


def chebyshev_response(moments, z, spectral_interval, *, moment_error_bounds=None, seed_norm_squared=None):
    """Explicit finite response bound from acquired V*T_n(A_scaled)V moments.

    ``spectral_interval`` must enclose the native spectrum, not just Ritz values.
    Error bounds must hold simultaneously for the supplied moments. The seed norm
    bound defaults to ||M0|| only for exact M0, otherwise includes its error.
    """
    mm = tuple(hermitian(m, 'Chebyshev moment') for m in moments)
    if not mm or any(m.shape != mm[0].shape for m in mm):
        raise ValueError('Chebyshev moments need a common nonempty square shape')
    a, b = (scalar(x, 'spectral interval endpoint') for x in spectral_interval)
    if b <= a:
        raise ValueError('spectral interval must be nondegenerate and ordered')
    z = spectral_point(z)
    h, c = (b-a)/2, (a+b)/2
    zz = (z-c)/h
    ss = cmath.sqrt(zz*zz-1)
    # Compute the small root without subtractive cancellation at large |z|.
    if abs(zz+ss) < abs(zz-ss):
        ss = -ss
    r = 1/(zz+ss)
    if abs(r) >= 1:
        raise ArithmeticError('could not select the convergent Chebyshev branch')
    errors = np.zeros(len(mm)) if moment_error_bounds is None else array(moment_error_bounds, 'moment error bounds', ndim=1, real=True)
    if errors.shape != (len(mm),) or np.any(errors < 0):
        raise ValueError('one nonnegative simultaneous error bound per moment is required')
    mass = norm(mm[0])+errors[0] if seed_norm_squared is None else scalar(seed_norm_squared, 'seed norm squared', nonnegative=True)
    if mass < norm(mm[0])-errors[0]:
        raise ValueError('seed norm bound contradicts the supplied zeroth moment')
    coeff = np.array([1]+[2*r**j for j in range(1, len(mm))], dtype=complex)/(h*ss)
    estimate = sum((f*m for f, m in zip(coeff, mm, strict=True)), np.zeros_like(mm[0], dtype=complex))
    bound = 2*mass/(h*abs(ss))*abs(r)**len(mm)/(1-abs(r))
    uncertainty = float(np.dot(np.abs(coeff), errors))
    return PolynomialResponse(immutable(estimate), float(bound), uncertainty, len(mm)-1, abs(r))


def chebyshev_moments(operator, ports, degree, spectral_interval):
    """Acquire one action per polynomial degree, preserving joint cross moments."""
    v = array(ports, 'physical ports')
    degree = integer(degree, 'degree')
    a, b = (scalar(x, 'spectral interval endpoint') for x in spectral_interval)
    if b <= a:
        raise ValueError('spectral interval must be ordered')
    if callable(operator):
        action = operator
    else:
        aa = hermitian(operator, 'operator')
        if aa.shape != (len(v), len(v)):
            raise ValueError('operator and port dimensions differ')
        eigenvalues = np.linalg.eigvalsh(aa)
        if eigenvalues[0] < a or eigenvalues[-1] > b:
            raise ValueError('declared spectral interval does not contain the dense operator')
        action = lambda q: aa@q
    previous, current = np.zeros_like(v), v.copy()
    moments = []
    for j in range(degree+1):
        moments.append(immutable((v.conj().T@current+current.conj().T@v)/2))
        if j < degree:
            raw = array(action(current), 'Chebyshev operator action')
            if raw.shape != current.shape:
                raise ValueError('operator action changes the physical block shape')
            scaled = (raw-(a+b)/2*current)/((b-a)/2)
            following = scaled if j == 0 else 2*scaled-previous
            previous, current = current, following
    return tuple(moments)


def chebyshev_required_degree(z, spectral_interval, tolerance, *, seed_norm_squared):
    """Finite sufficient degree for the closed-form resolvent truncation bound.

    This is a planning calculation, not an acquisition. Operator/moment uncertainty
    is additional. The returned degree can be large when the query is close to
    the spectrum; no arbitrary degree cap or implicit regularization is imposed.
    """
    z = spectral_point(z)
    a, b = (scalar(x, 'spectral endpoint') for x in spectral_interval)
    tol = scalar(tolerance, 'target tolerance', positive=True)
    mass = scalar(seed_norm_squared, 'seed norm squared', nonnegative=True)
    if b <= a:
        raise ValueError('spectral interval must be nondegenerate')
    if mass == 0:
        return 0
    h, c = (b-a)/2, (a+b)/2
    zz = (z-c)/h
    ss = cmath.sqrt(zz*zz-1)
    if abs(zz+ss) < abs(zz-ss):
        ss = -ss
    r = abs(1/(zz+ss))
    if not math.isfinite(r) or not 0 <= r < 1 or not np.isfinite(ss):
        raise ArithmeticError('Chebyshev query cannot be resolved in binary64 arithmetic')
    if r == 0:
        return 0
    logarithmic_factor = math.log(2)+math.log(mass)-math.log(h)-math.log(abs(ss))-math.log1p(-r)
    degree = max(0, math.ceil((math.log(tol)-logarithmic_factor)/math.log(r))-1)
    # Guard a floating logarithmic boundary; this does not spend native actions.
    while logarithmic_factor+(degree+1)*math.log(r) > math.log(tol):
        degree += 1
    return degree


@dataclass(frozen=True, eq=False)
class AcquiredPolynomialResponse:
    response: PolynomialResponse
    requested_degree: int
    acquired_degree: int
    action_count: int
    tolerance_met: bool
    moments: tuple[np.ndarray, ...]


def acquire_chebyshev_response(operator, ports, z, spectral_interval, *, tolerance, maximum_degree=None):
    """Complete solver-free acquisition-to-enclosure route for a fixed exact operator.

    The spectral support is a supplied scientific contract (checked for dense A).
    Native action and floating arithmetic errors are not silently certified as
    zero physical errors: the returned radius is the exact-operator polynomial
    truncation bound evaluated numerically. For approximate/uncertain moments,
    use ``chebyshev_response(..., moment_error_bounds=...)``. A user-selected
    maximum degree returns an explicit unresolved bound instead of pretending
    its accuracy was met.
    """
    v = array(ports, 'ports')
    requested = chebyshev_required_degree(z, spectral_interval, tolerance, seed_norm_squared=norm(v)**2)
    chosen = requested if maximum_degree is None else min(requested, integer(maximum_degree, 'maximum degree'))
    moments = chebyshev_moments(operator, v, chosen, spectral_interval)
    result = chebyshev_response(moments, z, spectral_interval, seed_norm_squared=norm(v)**2)
    return AcquiredPolynomialResponse(result, requested, chosen, chosen*v.shape[1], result.bound <= tolerance, moments)


def inverse_residual_response(receiver, inputs, primal_trial, dual_trial,
                              primal_operator_action, dual_adjoint_action, *,
                              inverse_norm_bound, operator_error_bound=0.):
    """Generic dual-residual identity for an invertible, possibly nonnormal Z.

    The supplied actions are ZX and Z*Y (not AX and AY). The supplier must
    establish ||Z^-1|| <= inverse_norm_bound independently. Eigenvalue stability
    or stationary observations alone do not establish such a bound for a
    nonnormal generator. This also handles Z=K for positive static compliance.
    """
    c, b, x, y, zx, zy = [array(value, name) for value, name in (
        (receiver, 'receiver'), (inputs, 'inputs'), (primal_trial, 'primal trial'),
        (dual_trial, 'dual trial'), (primal_operator_action, 'primal operator action'),
        (dual_adjoint_action, 'dual adjoint action'))]
    if x.shape != b.shape or y.shape != c.shape or zx.shape != x.shape or zy.shape != y.shape or b.shape[0] != c.shape[0]:
        raise ValueError('inverse-response trial/action/port shapes do not match')
    bound = scalar(inverse_norm_bound, 'inverse norm bound', positive=True)
    delta = scalar(operator_error_bound, 'operator error bound', nonnegative=True)
    eb, ec = b-zx, c-zy
    raw = c.conj().T@x
    estimate = raw+y.conj().T@eb
    result_bound = ((norm(ec)+delta*norm(y))*(norm(eb)+delta*norm(x))*bound
                    +delta*norm(y)*norm(x))
    cn = np.linalg.norm(ec, axis=0)+delta*np.linalg.norm(y, axis=0)
    bn = np.linalg.norm(eb, axis=0)+delta*np.linalg.norm(x, axis=0)
    entry_bounds = np.outer(cn, bn)*bound+delta*np.outer(np.linalg.norm(y, axis=0), np.linalg.norm(x, axis=0))
    return ResidualResponse(immutable(estimate), immutable(raw), float(result_bound), immutable(entry_bounds),
        immutable(eb), immutable(ec), immutable(x), immutable(y))


def static_galerkin_response(prefix, ports, *, lower_eigenvalue_bound, inputs=None):
    """Positive-static joint response using acquired KQ and an independently known gap.

    The lower bound concerns the complete native K, not the smallest projected
    Ritz value. An indefinite reference must not be silently shifted and presented
    as the same physical canonical system.
    """
    if not isinstance(prefix, KrylovPrefix):
        raise TypeError('prefix must be an acquired KrylovPrefix')
    gap = scalar(lower_eigenvalue_bound, 'native lower eigenvalue bound', positive=True)
    c = array(ports, 'ports')
    b = c if inputs is None else array(inputs, 'inputs')
    q, aq, t = prefix.basis, prefix.actions, prefix.projected
    if c.shape[0] != q.shape[0] or b.shape[0] != q.shape[0]:
        raise ValueError('static ports and prefix have different physical dimensions')
    if np.linalg.eigvalsh(t)[0] <= 0:
        raise ValueError('static response requires positive projected stiffness')
    rounding = 512*np.finfo(float).eps*max(norm(t), 1.)
    if gap > np.linalg.eigvalsh(t)[0]+prefix.operator_error_bound+rounding:
        raise ValueError('declared native lower gap contradicts an acquired Ritz value')
    xs = np.linalg.solve(t, q.conj().T@b)
    ys = np.linalg.solve(t, q.conj().T@c)
    return inverse_residual_response(c, b, q@xs, q@ys, aq@xs, aq@ys,
        inverse_norm_bound=1/gap, operator_error_bound=prefix.operator_error_bound)
