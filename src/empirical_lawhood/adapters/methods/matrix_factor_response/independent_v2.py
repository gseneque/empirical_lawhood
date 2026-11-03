# SPDX-License-Identifier: MPL-2.0
"""Independent trace-word and finite-difference numerical reference kernels."""

from functools import lru_cache
import numpy as np
from . import independent as v1


STATE_SHAPE = (2, 3, 4, 4)



IMPLEMENTATION_ID = "matrix-factor-response.independent-trace-word-v2"



@lru_cache(maxsize=1)
def native_basis():
    """One immutable complete HS96 basis; callers cannot enable writes."""
    original = v1.native_basis()
    return np.frombuffer(original.tobytes(), dtype="<c16").reshape(original.shape)



def _position(value):
    value = np.asarray(value)
    if (value.shape != STATE_SHAPE or value.dtype != np.dtype("<c16")
            or not np.isfinite(value).all()
            or np.linalg.norm(value-value.conj().swapaxes(-1, -2)) > 1e-12):
        raise ValueError("v2 independent reference needs full finite Hermitian q=2 geometry")
    return value



def _trace_words(member, alpha_tilde):
    """Literal trace-polynomial expansion, independently differentiated below."""
    masses = float(member.mass_x), float(member.mass_y)
    cross = float(member.cross_coupling_gamma)
    couplings = np.asarray(alpha_tilde, dtype="<f8")
    if (couplings.shape != (2,) or not np.isfinite(couplings).all() or np.min(couplings) < 0
            or not np.isfinite((*masses, cross)).all() or min(*masses, cross) <= 0):
        raise ValueError("v2 independent reference changes positive physical parameters")
    words = {}

    def add(coefficient, word):
        key = min(word[i:]+word[:i] for i in range(len(word)))
        words[key] = words.get(key, 0j)+coefficient

    def square(coefficient, a, b):
        for sign, word in ((1, (a,b,a,b)), (-1, (a,b,b,a)), (-1, (b,a,a,b)), (1, (b,a,b,a))):
            add(sign*coefficient, word)

    epsilon = ((1,(0,1,2)), (1,(1,2,0)), (1,(2,0,1)),
               (-1,(0,2,1)), (-1,(2,1,0)), (-1,(1,0,2)))
    for sector, mass in enumerate(masses):
        offset, alpha = 3*sector, float(couplings[sector])/2
        beta = -alpha**2*(2*(3*mass-1)/9)
        for a in range(3):
            add(4*beta, (offset+a, offset+a))
            for b in range(3):
                square(-1, offset+a, offset+b)
                add(4*mass, (offset+a, offset+a, offset+b, offset+b))
        for sign, indices in epsilon:
            add(4*2j*alpha*sign/3, tuple(offset+i for i in indices))
    for a in range(3):
        for b in range(3):
            square(-2*cross, a, 3+b)
    return tuple((coefficient, word) for word, coefficient in sorted(words.items()) if coefficient != 0)



class TraceWordGradient:
    """Assessment-local coefficient cache; no growing global parameter cache."""

    def __init__(self, member, alpha_tilde):
        self.terms = tuple((coefficient, destination, word[i+1:]+word[:i])
            for coefficient, word in _trace_words(member, alpha_tilde) for i, destination in enumerate(word))

    def __call__(self, position):
        matrices = _position(position).reshape(6, 4, 4)
        gradient = np.zeros_like(matrices)
        products = {}
        for coefficient, destination, word in self.terms:
            if word not in products:
                product = matrices[word[0]]
                for index in word[1:]:
                    product = product@matrices[index]
                products[word] = product
            gradient[destination] += coefficient*products[word]
        result = (gradient+gradient.conj().swapaxes(-1, -2))/2
        if not np.isfinite(result).all():
            raise FloatingPointError("v2 independent gradient is not finite")
        return result.reshape(STATE_SHAPE)



def potential_gradient(position, member, alpha_tilde):
    """Public parameter-consistent primitive for later explicitly bound SI02."""
    return TraceWordGradient(member, alpha_tilde)(position)



def potential_gradient_fd(position, design):
    """Full96 central-difference falsifier against the separate literal potential."""
    epsilon = float(design.potential_difference_step)
    coefficients = [(v1.potential(position+epsilon*b, design)-v1.potential(position-epsilon*b, design))/(2*epsilon)
                    for b in native_basis()]
    return np.einsum("k,ksjab->sjab", coefficients, native_basis())



def potential_hessian(position, design):
    """Unchanged literal second-difference formula with the cached HS basis."""
    basis, epsilon = native_basis(), float(design.hessian_difference_step)
    result = np.empty((96, 96))
    for i, left in enumerate(basis):
        for j in range(i+1):
            right = basis[j]
            value = (v1.potential(position+epsilon*(left+right), design)
                     -v1.potential(position+epsilon*(left-right), design)
                     -v1.potential(position+epsilon*(-left+right), design)
                     +v1.potential(position-epsilon*(left+right), design))/(4*epsilon**2)
            result[i,j] = result[j,i] = value
    return result



def _reference_branch(view, positions, momenta, force, amplitude, pulse_steps, noise, gradient):
    x, p, force = _position(positions).copy(), _position(momenta).copy(), _position(force)
    noise = np.asarray(noise)
    dt, eta, bath = float(view.timestep), float(view.friction_gamma), float(view.bath_temperature)
    if (not np.isfinite((dt,eta,bath,amplitude)).all() or min(dt,eta,bath) <= 0
            or type(pulse_steps) is not int or pulse_steps < 1
            or noise.dtype != np.dtype("<c16") or noise.ndim != 5 or noise.shape[1:] != STATE_SHAPE
            or not np.isfinite(noise).all()
            or np.linalg.norm(noise-noise.conj().swapaxes(-1,-2)) > 1e-12):
        raise ValueError("v2 independent reference changes physical clock/noise/action geometry")
    decay = np.exp(-eta*dt)
    if decay == 1:
        raise ValueError("positive-friction OU decay is not representable at this clock")
    scale = np.sqrt(bath*(1-decay**2))
    hermitian = lambda a:(a+a.conj().swapaxes(-1,-2))/2
    xs, ps, incoming_gradient = [x.copy()], [p.copy()], gradient(x)
    for tick, innovation in enumerate(noise):
        kick = dt/2*amplitude*force if tick < pulse_steps else np.zeros_like(force)
        p = hermitian(p+kick-dt/2*incoming_gradient)
        x = hermitian(x+dt/2*p)
        p = hermitian(decay*p+scale*innovation)
        x = hermitian(x+dt/2*p)
        outgoing_gradient = gradient(x)
        p = hermitian(p-dt/2*outgoing_gradient+kick)
        xs.append(x.copy()); ps.append(p.copy())
        incoming_gradient = outgoing_gradient
    return {"positions":np.asarray(xs), "momenta":np.asarray(ps)}



def reference_branch_parameters(*, member, alpha_tilde, view, positions, momenta,
                                force, amplitude, pulse_steps, noise):
    return _reference_branch(view,positions,momenta,force,amplitude,pulse_steps,noise,
                             TraceWordGradient(member,alpha_tilde))



def reference_branch(design, origin_arrays, force, amplitude, pulse_steps, noise):
    return reference_branch_parameters(member=design.member, alpha_tilde=(design.alpha_x,design.alpha_y),
        view=design.view, positions=origin_arrays["positions"][-1], momenta=origin_arrays["momenta"][-1],
        force=force, amplitude=amplitude, pulse_steps=pulse_steps, noise=noise)
