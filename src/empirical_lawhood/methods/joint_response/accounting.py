# SPDX-License-Identifier: MPL-2.0
"""Signed endpoint and discrete propagation accounting, independent of substrate."""
from __future__ import annotations

from dataclasses import dataclass
import math
import numpy as np
from scipy.linalg import expm

from ._validation import array, hermitian, immutable, integer, norm, scalar, square_map


@dataclass(frozen=True)
class ContrastAccount:
    endpoint_energy: float
    signed_alignment: float
    contrast_energy: float
    identity_residual: float
    low_energy: float
    high_energy: float


def signed_contrast_account(low_error, high_error):
    """S=||e_H||²+||e_L||², A=2 Re<e_H,e_L>, D=||e_H-e_L||².

    Callers preserve their original actuator normalizations, common receiver,
    independent units and numerical masks before this arithmetic. This method
    creates no acceptance threshold and interprets no cells as independent trials.
    """
    low, high = np.asarray(low_error), np.asarray(high_error)
    if low.shape != high.shape or not low.size:
        raise ValueError('endpoint errors need identical nonempty shapes')
    low = array(low.reshape(-1), 'low endpoint error', ndim=1)
    high = array(high.reshape(-1), 'high endpoint error', ndim=1)
    le = math.fsum(float(abs(x)**2) for x in low)
    he = math.fsum(float(abs(x)**2) for x in high)
    alignment = 2*math.fsum(float((x.conjugate()*y).real) for x, y in zip(high, low, strict=True))
    contrast = math.fsum(float(abs(x-y)**2) for x, y in zip(high, low, strict=True))
    energy = math.fsum((le, he))
    return ContrastAccount(energy, alignment, contrast,
        math.fsum((contrast, -energy, alignment)), le, he)


@dataclass(frozen=True, eq=False)
class PropagationAccount:
    inherited: np.ndarray
    generated: np.ndarray
    direct: np.ndarray
    full_final: np.ndarray
    reduced_final: np.ndarray
    defect: np.ndarray
    reconstruction_error: float


def propagation_accounting(full_step, reduced_step, lift, full_initial, reduced_initial, steps):
    """Exact discrete telescoping with O(state size) retained working memory.

    d_N = M^N d_0 + sum M^(N-1-j)(ML-LR)z_j. Initial states are
    columns or vectors. R is supplied as the *actual* reduced step: for BAOAB,
    compose after Hessian projection rather than substituting L*ML. This
    arithmetic makes no normality/stability assumption and accepts zero steps.
    """
    m, r = square_map(full_step, 'full step'), square_map(reduced_step, 'reduced step')
    l = array(lift, 'lift')
    f0, z0 = np.asarray(full_initial), np.asarray(reduced_initial)
    if f0.ndim != z0.ndim or f0.ndim not in (1, 2):
        raise ValueError('full and reduced states must be matching vectors or column blocks')
    f = array(f0, 'full initial', ndim=f0.ndim).copy()
    z = array(z0, 'reduced initial', ndim=z0.ndim).copy()
    if (l.shape != (len(m), len(r)) or f.shape[0] != len(m) or z.shape[0] != len(r)
            or f.shape[1:] != z.shape[1:]):
        raise ValueError('state, lift and propagation dimensions differ')
    count = integer(steps, 'steps')
    defect = m@l-l@r
    inherited, generated = f-l@z, np.zeros_like(f-l@z)
    maximum = 0.
    for _ in range(count):
        inherited = m@inherited
        generated = m@generated+defect@z
        f, z = m@f, r@z
        if not all(np.isfinite(v).all() for v in (inherited, generated, f, z)):
            raise ArithmeticError('propagation accounting became nonfinite')
        maximum = max(maximum, float(np.max(np.abs(inherited+generated-(f-l@z)))))
    direct = f-l@z
    return PropagationAccount(*(immutable(v) for v in (inherited, generated, direct, f, z, defect)), maximum)


def ordered_propagator(generators, durations):
    """Exact matrix exponentials for a piecewise constant -i A(t) generator.

    Changes are multiplied in chronological order. Supplied generators may be
    general square matrices; no unitary error bound is inferred for non-Hermitian
    ones. This does not acquire a future generator or preparation.
    """
    aa = tuple(square_map(a, 'generator') for a in generators)
    times = tuple(scalar(t, 'duration', nonnegative=True) for t in durations)
    if not aa or len(aa) != len(times) or any(a.shape != aa[0].shape for a in aa):
        raise ValueError('piecewise generators and durations must form a matching nonempty sequence')
    result = np.eye(len(aa[0]), dtype=complex)
    for a, t in zip(aa, times, strict=True):
        result = expm(-1j*t*a)@result
    return result


def unitary_projection_bound(basis, native_actions, reduced_generator, receiver, inputs, time,
                             *, operator_error_bound=0.):
    """Finite-horizon Duhamel bound for Q exp(-itT) Q*B with Hermitian T.

    Native A must be self-adjoint. The caller supplies its acquired AQ and the
    uniform operator discrepancy. An initial projection mismatch remains explicit.
    The constant defect-norm integral is conservative but requires no quadrature.
    """
    q, aq = array(basis, 'basis'), array(native_actions, 'native actions')
    t = hermitian(reduced_generator, 'reduced generator')
    c, b = array(receiver, 'receiver'), array(inputs, 'inputs')
    horizon = scalar(time, 'time', nonnegative=True)
    delta = scalar(operator_error_bound, 'operator error bound', nonnegative=True)
    if (aq.shape != q.shape or t.shape != (q.shape[1], q.shape[1])
            or c.shape[0] != q.shape[0] or b.shape[0] != q.shape[0]):
        raise ValueError('finite-horizon operator, basis and port dimensions differ')
    if norm(q.conj().T@q-np.eye(q.shape[1])) > 1e-10:
        raise ValueError('finite-horizon projection requires an orthonormal basis')
    coefficients = q.conj().T@b
    mismatch = norm(b-q@coefficients)
    defect = norm(aq-q@t)+delta*norm(q)
    return norm(c)*(mismatch+horizon*defect*norm(coefficients))
