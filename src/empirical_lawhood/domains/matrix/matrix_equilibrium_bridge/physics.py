# SPDX-License-Identifier: MPL-2.0
"""Restrained six-matrix force and symmetry-preserving equilibrium controls.

The historical scalar source remains unchanged. The retained assessor compares
this batch implementation with that source and with literal potential stencils.
"""
import numpy as np

from empirical_lawhood.domains.matrix.six_matrix_response.shooting import hermitian_basis


def hermitian(value): return .5 * (value + value.swapaxes(-1, -2).conj())
def commutator(a, b): return a @ b - b @ a


def coordinates(value):
    return np.einsum('kab,...sjab->...sjk', hermitian_basis(4).conj(), value).real.reshape((*value.shape[:-4], 96))


def lift(value):
    return np.einsum('...sjk,kab->...sjab', np.asarray(value).reshape((*value.shape[:-1], 2, 3, 16)), hermitian_basis(4))


def radial_scale(design): return float(design.alpha_y)**2 / 36


def receiver(design, q):
    y = q[..., 1, :, :, :]
    return np.sum(abs(y)**2, axis=(-3, -2, -1)) / (12 * radial_scale(design))


def native_gradient(design, q, coupling):
    """Batch the same nine native terms, retaining all 96 physical coordinates."""
    alpha = np.array((float(design.alpha_x)/2, float(design.alpha_y)/2))
    beta = -alpha**2 / 9
    grad = np.empty_like(q)
    for sector in (0, 1):
        z, other = q[..., sector, :, :, :], q[..., 1-sector, :, :, :]
        radius = np.sum(z @ z, axis=-3)
        # (input component, response component) summations.
        left, right = z[..., :, None, :, :], z[..., None, :, :, :]
        nested = np.sum(commutator(left, commutator(left, right)), axis=-4)
        other_left = other[..., :, None, :, :]
        cross = np.sum(commutator(other_left, commutator(other_left, right)), axis=-4)
        cubic = np.stack((commutator(z[..., 1, :, :], z[..., 2, :, :]),
            commutator(z[..., 2, :, :], z[..., 0, :, :]), commutator(z[..., 0, :, :], z[..., 1, :, :])), axis=-3)
        grad[..., sector, :, :, :] = 4 * (nested + 2j * alpha[sector] * cubic + 2 * beta[sector] * z
            + radius[..., None, :, :] @ z + z @ radius[..., None, :, :]
            + np.asarray(coupling)[..., None, None, None] * cross)
    return hermitian(grad)


def gradient(design, q, coupling, center):
    grad = native_gradient(design, q, coupling)
    xi = receiver(design, q)
    grad[..., 1, :, :, :] += (float(design.stiffness) * (xi-center) / (6*radial_scale(design)))[..., None, None, None] * q[..., 1, :, :, :]
    return grad


def fields(design, q, grad, center):
    """Return G and four exact canonical zero-mean Stein observables.

    v0=grad(xi); v1=(xi-s)grad(xi); v2=chi grad(xi);
    v3=(xi-s)grad(chi), chi=||X||^2/12. Polynomial fields have
    vanishing surface terms under this confining quartic native potential.
    """
    xi = receiver(design, q)
    x, y = q[..., 0, :, :, :], q[..., 1, :, :, :]
    chi = np.sum(abs(x)**2, axis=(-3, -2, -1))/12
    gx = np.sum((x.conj()*grad[..., 0, :, :, :]).real, axis=(-3, -2, -1))/6
    gy = np.sum((y.conj()*grad[..., 1, :, :, :]).real, axis=(-3, -2, -1))/(6*radial_scale(design))
    div_y, div_x = 8/radial_scale(design), 8.
    norm_y = xi/(3*radial_scale(design))
    c0 = float(design.temperature)*div_y-gy
    c1 = (xi-center)*c0+float(design.temperature)*norm_y
    c2 = chi*c0
    c3 = (xi-center)*(float(design.temperature)*div_x-gx)
    return np.stack((float(design.stiffness)*(center-xi), c0, c1, c2, c3), axis=-1)


def step(design, q, p, grad, noise, dt, coupling, center):
    """Ordered BAOAB with one new conservative force and supplied HS noise."""
    p = hermitian(p-.5*dt*grad)
    q = hermitian(q+.5*dt*p)
    rho = np.exp(-float(design.friction)*dt)
    p = hermitian(rho*p+np.sqrt(float(design.temperature)*(1-rho*rho))*noise)
    q = hermitian(q+.5*dt*p)
    grad = gradient(design, q, coupling, center)
    p = hermitian(p-.5*dt*grad)
    return q, p, grad


def initial_positions(design, node_count):
    sigma = np.array([[[0, 1], [1, 0]], [[0, -1j], [1j, 0]], [[1, 0], [0, -1]]], dtype='<c16')/2
    q = np.zeros((2, 2, node_count, 2, 3, 4, 4), dtype='<c16')
    for a in range(3):
        q[1, :, :, 0, a] = float(design.alpha_x)/3*np.kron(sigma[a], np.eye(2))
        q[1, :, :, 1, a] = float(design.alpha_y)/3*np.kron(np.eye(2), sigma[a])
    return q


def trapezoid_weights(centers):
    x = np.asarray(centers, dtype=float)
    if x.ndim != 1 or len(x) < 2 or np.any(np.diff(x) <= 0): raise ValueError('ordered complete center grid required')
    return np.r_[x[1]-x[0], x[2:]-x[:-2], x[-1]-x[-2]]/2


def paired_series(values, centers):
    # values: view, preparation, arm, node, sample, observable.
    weights = trapezoid_weights(centers)
    return np.einsum('n,vpntc->vptc', weights, values[:, :, 1]-values[:, :, 0])
