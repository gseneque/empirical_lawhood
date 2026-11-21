# SPDX-License-Identifier: MPL-2.0
"""Physical port derivatives and finite restraint changes on declared coordinates."""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np

from ._validation import array, hermitian, immutable, integer, scalar, spectral_point


@dataclass(frozen=True, eq=False)
class RestraintJet:
    energy: float
    gradient: np.ndarray
    hessian: np.ndarray
    center_force_port: np.ndarray
    center_hessian_derivative: np.ndarray


def harmonic_restraint_jet(receiver_value, receiver_gradient, receiver_hessian, center, stiffness):
    """Value, force-input port and complete Cartesian derivatives of k(xi-s)^2/2.

    The receiver is real and twice differentiable in the supplied fixed coordinate
    measure. The second Hessian term k(xi-s) H_xi is retained. Moving s by delta
    changes the restraint force by +k delta grad(xi) and the Hessian by
    -k delta H_xi at a fixed configuration; this change is not generally rank one.
    Periodic-image switches or coincident distance-receiver atoms violate the
    differentiability contract and must be handled by the domain supplier.
    """
    xi, s, k = scalar(receiver_value, 'receiver'), scalar(center, 'restraint center'), scalar(stiffness, 'restraint stiffness', positive=True)
    g = array(receiver_gradient, 'receiver gradient', ndim=1, real=True)
    h = array(receiver_hessian, 'receiver Hessian', real=True)
    h = hermitian(h, 'receiver Hessian')
    if h.shape != (len(g), len(g)):
        raise ValueError('receiver gradient and Hessian dimensions differ')
    delta = xi-s
    return RestraintJet(.5*k*delta*delta, immutable(k*delta*g),
        immutable(k*(np.outer(g, g)+delta*h)), immutable(k*g), immutable(-k*h))


@dataclass(frozen=True, eq=False)
class ResponseDerivative:
    derivative: np.ndarray
    receiver_term: np.ndarray
    operator_term: np.ndarray
    input_term: np.ndarray


def resolvent_directional_derivative(operator, receiver, inputs, z, operator_derivative, *,
                                     receiver_derivative=None, input_derivative=None):
    """All three terms of d(C*R B): dC*RB + C*R(dA)RB + C*R dB.

    Dense finite-dimensional evaluation is an algebraic control and a reusable
    method; it makes no cheap-native-action claim. A physically justified
    finite-rank derivative can instead reuse acquired joint response blocks.
    """
    a, da = hermitian(operator, 'operator'), hermitian(operator_derivative, 'operator derivative')
    c, b, z = array(receiver, 'receiver'), array(inputs, 'inputs'), spectral_point(z)
    dc = np.zeros_like(c) if receiver_derivative is None else array(receiver_derivative, 'receiver derivative')
    db = np.zeros_like(b) if input_derivative is None else array(input_derivative, 'input derivative')
    if da.shape != a.shape or c.shape[0] != len(a) or b.shape[0] != len(a) or dc.shape != c.shape or db.shape != b.shape:
        raise ValueError('operator and moving physical-port derivative shapes differ')
    shifted = z*np.eye(len(a))-a
    rb = np.linalg.solve(shifted, b)
    receiver_term = dc.conj().T@rb
    operator_term = c.conj().T@np.linalg.solve(shifted, da@rb)
    input_term = c.conj().T@np.linalg.solve(shifted, db)
    return ResponseDerivative(*(immutable(term) for term in
        (receiver_term+operator_term+input_term, receiver_term, operator_term, input_term)))


def resolvent_mixed_derivative(operator, first_derivative, second_derivative, mixed_derivative, z):
    """d_theta d_lambda R preserving both noncommuting orders and d_theta,lambda A."""
    a = hermitian(operator, 'operator')
    aa = tuple(hermitian(value, name) for value, name in (
        (first_derivative, 'first derivative'), (second_derivative, 'second derivative'),
        (mixed_derivative, 'mixed derivative')))
    if any(value.shape != a.shape for value in aa):
        raise ValueError('all derivative operators need the same physical dimension')
    z = spectral_point(z)
    r = np.linalg.solve(z*np.eye(len(a))-a, np.eye(len(a)))
    first, second, mixed = aa
    return r@second@r@first@r+r@first@r@second@r+r@mixed@r


def recombine_ports(response, coefficients):
    """R_(VT)=T*R_V T with no new native action; physical availability stays separate."""
    r, t = array(response, 'joint response'), array(coefficients, 'port recombination')
    if r.shape[0] != r.shape[1] or t.shape[0] != r.shape[0]:
        raise ValueError('joint response and port recombination dimensions differ')
    return t.conj().T@r@t


@dataclass(frozen=True, eq=False)
class InputVisibility:
    moment_map: np.ndarray
    singular_values: np.ndarray
    rank: int
    null_directions: np.ndarray
    action_count: int


def input_visibility(operator, receiver, available_inputs, depth, *, rank_tolerance=1e-12):
    """Moment map C* A^j B on a *declared* finite space of available inputs.

    Numerical rank applies only to this acquired depth and threshold. A null
    direction here may remain dynamically visible at a later depth; it is not a
    certificate of invisibility over all frequencies or nonlinear interventions.
    """
    a, c, b = hermitian(operator, 'operator'), array(receiver, 'receiver'), array(available_inputs, 'available inputs')
    m = integer(depth, 'depth', minimum=1)
    tolerance = scalar(rank_tolerance, 'rank tolerance', nonnegative=True)
    if c.shape[0] != len(a) or b.shape[0] != len(a):
        raise ValueError('input visibility operator and ports differ in dimension')
    columns, state = [], b
    for j in range(m):
        columns.append(c.conj().T@state)
        if j+1 < m:
            state = a@state
    observation = np.vstack(columns)
    _, singular, vh = np.linalg.svd(observation, full_matrices=True)
    cutoff = tolerance*singular[0] if len(singular) else 0.
    rank = int(np.count_nonzero(singular > cutoff))
    return InputVisibility(immutable(observation), immutable(singular), rank,
        immutable(vh[rank:].conj().T), (m-1)*b.shape[1])
