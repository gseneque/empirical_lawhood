"""Independent finite-difference potential and complete phase-space reference kernels."""

import numpy as np


def potential(position, design):
    """Literal q=2 potential independently reduced from its published sums."""
    total = 0j
    for z, alpha_tilde, mass in ((position[0], design.alpha_x, design.member.mass_x),
                                (position[1], design.alpha_y, design.member.mass_y)):
        alpha = float(alpha_tilde)/2
        mu = 2*(3*float(mass)-1)/9
        beta = -alpha**2*mu
        radius = sum(matrix@matrix for matrix in z)
        commutators = sum(np.trace((a@b-b@a)@(a@b-b@a)) for a in z for b in z)
        total += 4*(-commutators/4 + 2j*alpha*np.trace(z[0]@(z[1]@z[2]-z[2]@z[1]))
                    + beta*np.trace(radius) + float(mass)*np.trace(radius@radius))
    total += -2*float(design.member.cross_coupling_gamma)*sum(
        np.trace((a@b-b@a)@(a@b-b@a)) for a in position[0] for b in position[1])
    if abs(total.imag) > 1e-8*max(1, abs(total.real)):
        raise ValueError('independent matrix potential is not real')
    return float(total.real)



def native_basis():
    result = []
    for sector in range(2):
        for component in range(3):
            for row in range(4):
                direction = np.zeros((2, 3, 4, 4), dtype='<c16')
                direction[sector, component, row, row] = 1
                result.append(direction)
            for imaginary in (False, True):
                for row in range(4):
                    for column in range(row+1, 4):
                        direction = np.zeros((2, 3, 4, 4), dtype='<c16')
                        value = (1j if imaginary else 1)/np.sqrt(2)
                        direction[sector, component, row, column] = value
                        direction[sector, component, column, row] = value.conjugate()
                        result.append(direction)
    return np.asarray(result)



def potential_gradient(position, design):
    epsilon = float(design.potential_difference_step)
    basis = native_basis()
    coefficients = [(potential(position+epsilon*v, design)-potential(position-epsilon*v, design))/(2*epsilon) for v in basis]
    return np.einsum('k,ksjab->sjab', coefficients, basis)



def potential_hessian(position, design):
    epsilon = float(design.hessian_difference_step)
    basis = native_basis()
    hessian = np.empty((96, 96))
    for i, left in enumerate(basis):
        for j in range(i+1):
            right = basis[j]
            value = (potential(position+epsilon*(left+right), design)
                     -potential(position+epsilon*(left-right), design)
                     -potential(position+epsilon*(-left+right), design)
                     +potential(position-epsilon*(left+right), design))/(4*epsilon**2)
            hessian[i,j] = hessian[j,i] = value
    return hessian



def noise_panel(stream, steps):
    rng = np.random.Generator(np.random.PCG64(stream.seed))
    values = np.zeros((steps, 2, 3, 4, 4), dtype='<c16')
    for tick in values:
        for sector in tick:
            for matrix in sector:
                matrix[np.diag_indices(4)] = rng.normal(size=4)
                real, imaginary = rng.normal(size=6), rng.normal(size=6)
                index = 0
                for row in range(4):
                    for column in range(row+1, 4):
                        value = (real[index]+1j*imaginary[index])/np.sqrt(2)
                        matrix[row,column], matrix[column,row] = value, value.conjugate()
                        index += 1
    return values



def reference_branch(design, origin_arrays, force, amplitude, pulse_steps, noise):
    x, p = origin_arrays['positions'][-1].copy(), origin_arrays['momenta'][-1].copy()
    xs, ps = [x.copy()], [p.copy()]
    dt = float(design.view.timestep)
    decay = np.exp(-float(design.view.friction_gamma)*dt)
    scale = np.sqrt(float(design.view.bath_temperature)*(1-decay**2))
    def hermitian(value):
        return (value+value.swapaxes(-1,-2).conj())/2
    for index, innovation in enumerate(noise):
        kick = dt/2*amplitude*force if index < pulse_steps else np.zeros_like(force)
        p = hermitian(p+kick-dt/2*potential_gradient(x, design))
        x = hermitian(x+dt/2*p)
        p = hermitian(decay*p+scale*innovation)
        x = hermitian(x+dt/2*p)
        p = hermitian(p-dt/2*potential_gradient(x, design)+kick)
        xs.append(x.copy()); ps.append(p.copy())
    return {'positions':np.asarray(xs), 'momenta':np.asarray(ps)}
