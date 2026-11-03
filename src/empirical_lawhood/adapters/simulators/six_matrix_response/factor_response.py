"""Both-sector native force instrument; original preparation wrapper is unchanged."""

from dataclasses import replace

import numpy as np

from .model import SixMatrixState, hermitian_part, hermiticity_residual
from .simulation import BAOABGradientCache, baoab_step_with_hermitian_noise


def factor_response_force_step(state, *, amplitude, direction, member, numerical_view,
                               standardized_noise, gradient_cache=None):
    """Two declared X/Y half kicks around one full coupled BAOAB step.

    Direction is a complete physical force, not a projection of the native
    state. The caller owns its source/frame, amplitude, clock and native roster.
    This map owns no stream selection, fitting, custody or scientific verdict.
    """
    direction = np.asarray(direction)
    if (type(state) is not SixMatrixState or state.q != 2 or not state.finite
            or direction.shape != (2, 3, 4, 4) or direction.dtype != np.dtype('complex128')
            or not np.isfinite(direction).all() or hermiticity_residual(direction) > 1e-12
            or not np.isfinite(amplitude)):
        raise ValueError('factor response requires a complete finite q=2 state and both-sector force')
    dt = float(numerical_view.timestep)
    kick = .5 * dt * amplitude * direction
    incoming = state if amplitude == 0 else replace(state, momenta=hermitian_part(state.momenta + kick))
    advanced = baoab_step_with_hermitian_noise(incoming, member=member, numerical_view=numerical_view,
        next_alpha_tilde_x=state.alpha_tilde_x, next_alpha_tilde_y=state.alpha_tilde_y,
        standardized_noise=standardized_noise, gradient_cache=gradient_cache)
    return advanced if amplitude == 0 else replace(advanced, momenta=hermitian_part(advanced.momenta + kick))


def native_factor_response_branch(state, *, direction, amplitude, pulse_steps,
                                  member, numerical_view, innovations):
    """Complete native branch supplied with an already selected innovation panel."""
    innovations = np.asarray(innovations)
    if (innovations.ndim != 5 or innovations.shape[1:] != (2, 3, 4, 4)
            or innovations.dtype != np.dtype('complex128') or not len(innovations)
            or not np.isfinite(innovations).all() or hermiticity_residual(innovations) > 1e-12
            or type(pulse_steps) is not int or not 1 <= pulse_steps <= len(innovations)):
        raise ValueError('factor response requires the complete declared pulse and innovation horizon')
    positions, momenta = [state.positions.copy()], [state.momenta.copy()]
    gradient_cache = BAOABGradientCache()
    for tick, noise in enumerate(innovations):
        state = factor_response_force_step(state, amplitude=amplitude if tick < pulse_steps else 0.,
            direction=direction, member=member, numerical_view=numerical_view, standardized_noise=noise,
            gradient_cache=gradient_cache)
        positions.append(state.positions.copy())
        momenta.append(state.momenta.copy())
    return {'positions': np.asarray(positions, dtype='<c16'), 'momenta': np.asarray(momenta, dtype='<c16'),
            'noise': np.asarray(innovations, dtype='<c16').copy()}
