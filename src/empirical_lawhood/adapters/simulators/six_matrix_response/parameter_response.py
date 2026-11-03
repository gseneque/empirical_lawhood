"""Parameter-consistent constant-coupling response with supplied innovations.

This instrument has no stream selection, source access or custody effects.
The caller must authenticate the retained origin and expressly select the new
autonomous assay clock before invoking it. Potential coefficients remain
distinct from the native unit kinetic mass.
"""

import numpy as np

from .contracts import MatrixIntegratorKind, SixMatrixResponseModelFamilyMember, SixMatrixResponseNumericalView
from .model import SixMatrixState, hermiticity_residual
from .parameter_derivatives import matrix, scheduled_force_step
from .simulation import BAOABGradientCache

IMPLEMENTATION_ID = 'six-matrix-q2.parameter-constant-response.v1'


def validate_future_view(coordinate, view):
    """Keep original PRIMARY physical conditions and declare the new RNG view."""
    primary = coordinate.primary_view
    if (type(view) is not SixMatrixResponseNumericalView
            or view.integrator is not MatrixIntegratorKind.BAOAB_UNDERDAMPED_LANGEVIN
            or view.rng_algorithm != 'PCG64' or view.rng_version != '1.0.0'
            or any(getattr(view, name) != getattr(primary, name) for name in (
                'timestep', 'friction_gamma', 'bath_temperature', 'time_unit', 'precision', 'integrator'))):
        raise ValueError('parameter response substitutes its PRIMARY physical future view')


def native_constant_response_branch(state, *, member, numerical_view, direction,
                                    amplitude, pulse_steps, innovations,
                                    alpha_tilde_x=None, alpha_tilde_y=None):
    """Both physical kicks and complete state/noise/coupling/clock history.

The supplied innovation panel is consumed exactly once in its given order.
Couplings are exact retained binary64 values; a normative target is not silently
substituted. New states may extend beyond the original historical source's end
only under the caller's separately authenticated autonomous continuation rule.
"""
    if (type(state) is not SixMatrixState or state.q != 2 or not state.finite
            or type(state.step_index) is not int
            or type(member) is not SixMatrixResponseModelFamilyMember
            or type(numerical_view) is not SixMatrixResponseNumericalView
            or numerical_view.integrator is not MatrixIntegratorKind.BAOAB_UNDERDAMPED_LANGEVIN):
        raise ValueError('parameter response requires exact typed finite q=2 native operands')
    direction = matrix(direction, 'constant response direction')
    innovations = np.asarray(innovations)
    if (innovations.ndim != 5 or innovations.shape[1:] != (2, 3, 4, 4)
            or innovations.dtype.str != '<c16' or not len(innovations)
            or not np.isfinite(innovations).all() or hermiticity_residual(innovations) > 1e-12
            or type(pulse_steps) is not int or not 1 <= pulse_steps <= len(innovations)
            or not np.isfinite(amplitude)):
        raise ValueError('parameter response requires its full pulse and Hermitian innovation horizon')
    selected = (state.alpha_tilde_x if alpha_tilde_x is None else float(alpha_tilde_x),
                state.alpha_tilde_y if alpha_tilde_y is None else float(alpha_tilde_y))
    if (not np.isfinite(selected).all()
            or tuple(float(x).hex() for x in selected) !=
               (float(state.alpha_tilde_x).hex(), float(state.alpha_tilde_y).hex())):
        raise ValueError('parameter response changes exact retained constant coupling realization')
    start = state.step_index
    positions, momenta = [state.positions.copy()], [state.momenta.copy()]
    gradient_cache = BAOABGradientCache()
    for tick, noise in enumerate(innovations):
        state = scheduled_force_step(state, direction=direction,
            amplitude=amplitude if tick < pulse_steps else 0., member=member,
            numerical_view=numerical_view, next_alpha_tilde_x=selected[0],
            next_alpha_tilde_y=selected[1], standardized_noise=noise, gradient_cache=gradient_cache)
        positions.append(state.positions.copy())
        momenta.append(state.momenta.copy())
    count = len(innovations) + 1
    return {
        'positions': np.asarray(positions, dtype='<c16'),
        'momenta': np.asarray(momenta, dtype='<c16'),
        'noise': np.asarray(innovations, dtype='<c16').copy(),
        'alpha_tilde': np.broadcast_to(np.asarray(selected, dtype='<f8'), (count, 2)).copy(),
        'ticks': np.arange(start, start + count, dtype='<i8'),
    }
