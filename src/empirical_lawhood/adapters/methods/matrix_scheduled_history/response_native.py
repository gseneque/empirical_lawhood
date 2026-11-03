# SPDX-License-Identifier: MPL-2.0
"""Scheduled pulse instrument and independently expressed received-path checks.

This instrument selects no streams, opens no contact and fits no model. Its
registered caller must authenticate original source, cutoff states, fixed
instrument, pre-future seals and actual innovations before invoking Native.
The cold checker imports no native force/gradient/marcher, RNG or eigensolve.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

import numpy as np

from empirical_lawhood.adapters.methods.matrix_parameter_history.independent import _reference_step
from empirical_lawhood.adapters.simulators.six_matrix_response.model import SixMatrixState
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history import MatrixParameterCoordinate
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_decimal, validate_stable_id


@dataclass(frozen=True, slots=True)
class ScheduledResponseTransitionControl(CanonicalRecord):
    """Complete received branch residuals; never an old history-control relabel."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-history/response-transition-control'
    control_id: str
    method: str
    error: Decimal
    tolerance: Decimal
    disposition: str
    denominator_steps: int
    denominator_real_coordinates: int
    measured_errors: tuple[Decimal, ...]
    failed_steps: tuple[int, ...]

    def __post_init__(self):
        validate_stable_id(self.control_id)
        for v in (self.error, self.tolerance, *self.measured_errors):
            validate_decimal(v, field_name='actual complete scheduled response residual/tolerance', minimum=Decimal(0))
        failed = tuple(i for i, v in enumerate(self.measured_errors, start=1) if v > self.tolerance)
        if (self.method != 'SCHEDULED_PULSE_FULL192_LITERAL_TRACE_WORD_BAOAB_BOTH_KICKS'
                or self.tolerance <= 0 or type(self.denominator_steps) is not int or self.denominator_steps < 1
                or self.denominator_real_coordinates != 192 or len(self.measured_errors) != self.denominator_steps
                or self.error != max(self.measured_errors) or self.failed_steps != failed
                or self.disposition != ('VIOLATED' if failed else 'SATISFIED')):
            raise ValueError('scheduled response control thins full192 residuals or substitutes numerical verdict')


def _geometry(coordinate, refinement, start, noise, direction, pulse_steps, amplitude):
    if (type(coordinate) is not MatrixParameterCoordinate or refinement not in (1, 2) or type(refinement) is not int
            or type(start) is not int or start < 0 or start % refinement or type(pulse_steps) is not int
            or not isinstance(noise, np.ndarray) or noise.dtype.str != '<c16'
            or noise.ndim != 5 or noise.shape[1:] != (2, 3, 4, 4) or not len(noise)
            or len(noise) % refinement
            or not 1 <= pulse_steps <= len(noise) or pulse_steps % refinement
            or start+len(noise) > refinement*coordinate.total_ticks
            or not np.isfinite(noise).all() or not np.isfinite(amplitude)
            or not isinstance(direction, np.ndarray) or direction.shape != (2, 3, 4, 4)
            or direction.dtype.str != '<c16' or not np.isfinite(direction).all()
            or np.linalg.norm(direction-direction.conj().swapaxes(-1, -2)) > 1e-12
            or np.linalg.norm(noise-noise.conj().swapaxes(-1, -2)) > 1e-12):
        raise ValueError('scheduled response changes full Hermitian innovations/force or absolute paired clock/menu')


def native_scheduled_branch(state, *, coordinate, refinement, direction, amplitude, pulse_steps, innovations, on_step=None):
    """Advance real source couplings; both physical kicks use the fixed force."""
    from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_derivatives import scheduled_force_step
    from empirical_lawhood.adapters.simulators.six_matrix_response.simulation import BAOABGradientCache
    if type(state) is not SixMatrixState or state.q != 2 or not state.finite:
        raise ValueError('scheduled response requires its exact complete native cutoff state')
    _geometry(coordinate, refinement, state.step_index, innovations, direction, pulse_steps, amplitude)
    start = state.step_index
    if (float(state.alpha_tilde_x).hex(), float(state.alpha_tilde_y).hex()) != tuple(
            float(a).hex() for a in coordinate.couplings(start, refinement=refinement)):
        raise ValueError('scheduled response changes realized source-specific cutoff coupling bits')
    view = coordinate.primary_view if refinement == 1 else coordinate.fine_view
    positions, momenta, cache = [state.positions.copy()], [state.momenta.copy()], BAOABGradientCache()
    for j, noise in enumerate(innovations):
        alpha = coordinate.couplings(start+j+1, refinement=refinement)
        state = scheduled_force_step(state, direction=direction, amplitude=amplitude if j < pulse_steps else 0.,
            member=coordinate.member, numerical_view=view, next_alpha_tilde_x=float(alpha[0]), next_alpha_tilde_y=float(alpha[1]),
            standardized_noise=noise, gradient_cache=cache)
        positions.append(state.positions.copy()); momenta.append(state.momenta.copy())
        if on_step is not None:
            on_step(j + 1)
    ticks = np.arange(start, start+len(innovations)+1, dtype='<i8')
    return {'positions': np.asarray(positions, dtype='<c16'), 'momenta': np.asarray(momenta, dtype='<c16'),
        'innovations': innovations.copy(), 'ticks': ticks,
        'alpha_tilde': np.asarray([coordinate.couplings(int(t), refinement=refinement) for t in ticks], dtype='<f8')}


def assess_scheduled_branch(coordinate, arrays, *, refinement, initial_positions, initial_momenta,
        start_tick, direction, amplitude, pulse_steps, tolerance, control_id):
    """Every received full192 transition, using literal trace-polynomial math."""
    if type(tolerance) is not Decimal or not tolerance.is_finite() or tolerance <= 0:
        raise ValueError('scheduled response requires explicit positive independent numerical tolerance')
    if set(arrays) != {'positions', 'momenta', 'innovations', 'ticks', 'alpha_tilde'}:
        raise ValueError('scheduled response thins exact state/noise/schedule/clock census')
    noise = arrays['innovations']
    _geometry(coordinate, refinement, start_tick, noise, direction, pulse_steps, amplitude)
    n = len(noise)
    expected = {'positions': ('<c16', (n+1, 2, 3, 4, 4)), 'momenta': ('<c16', (n+1, 2, 3, 4, 4)),
        'innovations': ('<c16', (n, 2, 3, 4, 4)), 'ticks': ('<i8', (n+1,)), 'alpha_tilde': ('<f8', (n+1, 2))}
    if any(a.dtype.str != expected[k][0] or a.shape != expected[k][1] or not np.isfinite(a).all() for k, a in arrays.items()):
        raise ValueError('scheduled response substitutes complete finite native member geometry')
    if any(np.linalg.norm(arrays[n]-arrays[n].conj().swapaxes(-1, -2)) > 1e-12 for n in ('positions', 'momenta')):
        raise ValueError('scheduled response loses original full Hermitian phase space')
    ticks = np.arange(start_tick, start_tick+n+1, dtype='<i8')
    if (not np.array_equal(arrays['ticks'], ticks)
            or not np.array_equal(arrays['alpha_tilde'], np.asarray([coordinate.couplings(int(t), refinement=refinement) for t in ticks], dtype='<f8'))
            or not np.array_equal(arrays['positions'][0], initial_positions)
            or not np.array_equal(arrays['momenta'][0], initial_momenta)):
        raise ValueError('scheduled response changes original view-specific start, realized schedule or absolute clock')
    view = coordinate.primary_view if refinement == 1 else coordinate.fine_view
    errors = []
    for j in range(n):
        force = amplitude*direction if j < pulse_steps else np.zeros_like(direction)
        kick = .5*float(view.timestep)*force
        x, p = _reference_step(arrays['positions'][j], arrays['momenta'][j]+kick, noise[j], coordinate.member, view,
            arrays['alpha_tilde'][j], arrays['alpha_tilde'][j+1])
        p += kick
        error = Decimal(repr(float(np.linalg.norm(np.stack((arrays['positions'][j+1]-x, arrays['momenta'][j+1]-p))))))
        if not error.is_finite():
            raise ValueError('scheduled independent response has nonfinite received residual')
        errors.append(error)
    failed = tuple(i for i, e in enumerate(errors, start=1) if e > tolerance)
    return ScheduledResponseTransitionControl(control_id=control_id, method='SCHEDULED_PULSE_FULL192_LITERAL_TRACE_WORD_BAOAB_BOTH_KICKS',
        error=max(errors), tolerance=tolerance, disposition='VIOLATED' if failed else 'SATISFIED',
        measured_errors=tuple(errors), failed_steps=failed, denominator_steps=n, denominator_real_coordinates=192)
