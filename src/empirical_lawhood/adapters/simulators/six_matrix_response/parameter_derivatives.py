"""Additive q=2 derivatives and scheduled force maps for parameter studies.

Potential coefficients M are not kinetic masses. The native kinetic convention
is unit mass. These pure instruments own no RNG, source access or qualification;
realized-path tangents and secants remain evaluator-only operands.
"""

from dataclasses import replace

import numpy as np

from .gradients import SixMatrixParameters, commutator
from .model import SixMatrixState, hermitian_part, hermiticity_residual
from .preparation_differential import NativeStateDifferential
from .simulation import baoab_step_with_hermitian_noise

IMPLEMENTATION_ID = 'six-matrix-q2.parameter-native-derivatives.v1'


def matrix(value, name):
    value = np.asarray(value)
    if (value.shape != (2, 3, 4, 4) or value.dtype != np.dtype('complex128')
            or not np.isfinite(value).all() or hermiticity_residual(value) > 1e-12):
        raise ValueError(f'parameter {name} requires full finite q=2 Hermitian complex128 geometry')
    return value


def parameters(state, member):
    if type(state) is not SixMatrixState or state.q != 2 or not state.finite:
        raise ValueError('parameter native map requires a finite q=2 state')
    return SixMatrixParameters(2, float(member.mass_x), float(member.mass_y),
        float(member.cross_coupling_gamma), state.alpha_tilde_x, state.alpha_tilde_y)


def hessian_image(positions, perturbation, selected):
    """Full96 position image, retaining n, beta, 2*M and cross-coupling."""
    z_all, v_all = matrix(positions, 'positions'), matrix(perturbation, 'perturbation')
    if (type(selected) is not SixMatrixParameters or selected.q != 2
            or not np.isfinite((selected.mass_x,selected.mass_y,selected.gamma,
                selected.alpha_tilde_x,selected.alpha_tilde_y)).all()):
        raise ValueError('parameter Hessian requires exact finite q=2 potential parameters')
    output = np.zeros_like(z_all)
    for sector, alpha, beta, mass in ((0,selected.alpha_x,selected.beta_x,selected.mass_x),
            (1,selected.alpha_y,selected.beta_y,selected.mass_y)):
        z,v = z_all[sector],v_all[sector]
        other,w = z_all[1-sector],v_all[1-sector]
        radius = np.sum(z@z,axis=0)
        delta_radius = np.sum(v@z+z@v,axis=0)
        for a in range(3):
            b,c = ((1,2),(2,0),(0,1))[a]
            result = 2*beta*v[a] + 2j*alpha*(commutator(v[b],z[c])+commutator(z[b],v[c]))
            result += 2*mass*(delta_radius@z[a]+z[a]@delta_radius+radius@v[a]+v[a]@radius)
            for b in range(3):
                result += commutator(v[b],commutator(z[b],z[a]))
                result += commutator(z[b],commutator(v[b],z[a]))
                result += commutator(z[b],commutator(z[b],v[a]))
                result += selected.gamma*(commutator(w[b],commutator(other[b],z[a]))
                    +commutator(other[b],commutator(w[b],z[a]))
                    +commutator(other[b],commutator(other[b],v[a])))
            output[sector,a] = selected.n*result
    return hermitian_part(output)


def coupling_gradient_image(positions, selected, scaled_coupling_derivative):
    """d(grad S)/d(alpha_tilde), including the mass-dependent beta derivative."""
    positions = matrix(positions, 'coupling positions')
    rates = np.asarray(scaled_coupling_derivative)
    if rates.shape != (2,) or not np.isfinite(rates).all() or selected.q != 2:
        raise ValueError('parameter coupling differential requires two finite scaled-coupling rates')
    output = np.zeros_like(positions)
    for sector,mass,alpha_tilde in ((0,selected.mass_x,selected.alpha_tilde_x),
            (1,selected.mass_y,selected.alpha_tilde_y)):
        beta_rate = -2*alpha_tilde*selected.mu(mass)/selected.q**2
        for a in range(3):
            b,c = ((1,2),(2,0),(0,1))[a]
            output[sector,a] = selected.n*rates[sector]*(2*beta_rate*positions[sector,a]
                +2j/selected.q*commutator(positions[sector,b],positions[sector,c]))
    return hermitian_part(output)


def scheduled_force_step(state, *, direction, amplitude, member, numerical_view,
        next_alpha_tilde_x, next_alpha_tilde_y, standardized_noise, gradient_cache=None):
    """Both physical sectors, both force kicks and distinct scheduled gradients."""
    parameters(state,member)
    direction = matrix(direction, 'force direction')
    if not np.isfinite((amplitude,next_alpha_tilde_x,next_alpha_tilde_y)).all():
        raise ValueError('parameter force and next couplings must be finite')
    dt = float(numerical_view.timestep)
    kick = .5*dt*amplitude*direction
    incoming = state if amplitude == 0 else replace(state,momenta=hermitian_part(state.momenta+kick))
    advanced = baoab_step_with_hermitian_noise(incoming,member=member,numerical_view=numerical_view,
        next_alpha_tilde_x=next_alpha_tilde_x,next_alpha_tilde_y=next_alpha_tilde_y,
        standardized_noise=standardized_noise,gradient_cache=gradient_cache)
    return advanced if amplitude == 0 else replace(advanced,momenta=hermitian_part(advanced.momenta+kick))


def tangent_step(state, advanced, differential, *, direction, force_derivative, member,
        numerical_view, current_coupling_derivative=(0.,0.), next_coupling_derivative=(0.,0.)):
    """Same-innovation state/force/scheduled-coupling derivative of actual BAOAB.

    Member, friction, bath and dt are fixed in this derivative. Coupling rates
    are derivatives of the selected schedule, not a change to its native clock.
    """
    first,last = parameters(state,member),parameters(advanced,member)
    direction = matrix(direction, 'tangent force direction')
    if advanced.step_index != state.step_index+1 or not np.isfinite(force_derivative):
        raise ValueError('parameter tangent requires aligned consecutive native states')
    dt = float(numerical_view.timestep)
    kick = .5*dt*force_derivative*direction
    first_image = hessian_image(state.positions,differential.positions,first)
    first_image += coupling_gradient_image(state.positions,first,current_coupling_derivative)
    momentum = hermitian_part(differential.momenta+kick-.5*dt*first_image)
    position = hermitian_part(differential.positions+.5*dt*momentum)
    momentum = hermitian_part(np.exp(-float(numerical_view.friction_gamma)*dt)*momentum)
    position = hermitian_part(position+.5*dt*momentum)
    last_image = hessian_image(advanced.positions,position,last)
    last_image += coupling_gradient_image(advanced.positions,last,next_coupling_derivative)
    momentum = hermitian_part(momentum-.5*dt*last_image+kick)
    return NativeStateDifferential(position,momentum)


def secant_hessian_image(minus, plus, perturbation, selected):
    """Exact two-node integral for fixed-parameter quartic gradient differences."""
    minus,plus = matrix(minus,'secant minus'),matrix(plus,'secant plus')
    middle = (minus+plus)/2
    offset = (plus-minus)/(2*np.sqrt(3))
    return hermitian_part((hessian_image(middle-offset,perturbation,selected)
        +hessian_image(middle+offset,perturbation,selected))/2)


def secant_step(minus, plus, advanced_minus, advanced_plus, reconstructed, *, direction,
        normalized_force, member, numerical_view):
    """Actual finite signed chord at shared schedules/noise, evaluator-only."""
    first = parameters(minus,member)
    last = parameters(advanced_minus,member)
    if (parameters(plus,member) != first or parameters(advanced_plus,member) != last
            or minus.step_index != plus.step_index or advanced_minus.step_index != minus.step_index+1
            or advanced_plus.step_index != plus.step_index+1 or not np.isfinite(normalized_force)):
        raise ValueError('parameter secant requires shared schedules and consecutive signed states')
    direction = matrix(direction,'secant force direction')
    dt = float(numerical_view.timestep)
    kick = .5*dt*normalized_force*direction
    first_image = secant_hessian_image(minus.positions,plus.positions,reconstructed.positions,first)
    momentum = hermitian_part(reconstructed.momenta+kick-.5*dt*first_image)
    position = hermitian_part(reconstructed.positions+.5*dt*momentum)
    momentum = hermitian_part(np.exp(-float(numerical_view.friction_gamma)*dt)*momentum)
    position = hermitian_part(position+.5*dt*momentum)
    last_image = secant_hessian_image(advanced_minus.positions,advanced_plus.positions,position,last)
    momentum = hermitian_part(momentum-.5*dt*last_image+kick)
    return NativeStateDifferential(position,momentum)
