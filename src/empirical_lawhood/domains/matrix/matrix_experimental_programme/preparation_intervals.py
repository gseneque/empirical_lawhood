# SPDX-License-Identifier: MPL-2.0
"""Supplied-noise preparation intervals with distinct paired states and clocks.

This module owns no RNG, source selection, native contact or persistence. The
registered caller supplies its admitted states, complete schedule and noise.
"""

import numpy as np

from empirical_lawhood.domains.matrix.six_matrix_response.model import SixMatrixState
from empirical_lawhood.domains.matrix.six_matrix_response.parameter_history import split_parameter_innovations
from empirical_lawhood.domains.matrix.six_matrix_response.simulation import BAOABGradientCache, baoab_step_with_hermitian_noise


def advance_preparation_pair(primary, fine, *, source, step, coarse, bridge,
                             primary_cache=None, fine_cache=None):
    """One original primary step and its two original fine half steps."""
    if (type(primary) is not SixMatrixState or type(fine) is not SixMatrixState
            or type(step) is not int or not 1 <= step <= source.total_ticks
            or primary.step_index != step - 1 or fine.step_index != 2 * (step - 1)):
        raise ValueError('preparation interval loses its distinct paired absolute clocks')
    for state, index in ((primary, 2 * (step - 1)), (fine, 2 * (step - 1))):
        if (state.alpha_tilde_x, state.alpha_tilde_y) != tuple(map(float, source.recipe.half_tick_couplings[index])):
            raise ValueError('preparation interval changes its actual starting couplings')
    halves = split_parameter_innovations(source, coarse, bridge)
    alpha = tuple(map(float, source.recipe.half_tick_couplings[2 * step]))
    primary = baoab_step_with_hermitian_noise(primary, member=source.member, numerical_view=source.primary_view,
        next_alpha_tilde_x=alpha[0], next_alpha_tilde_y=alpha[1], standardized_noise=coarse, gradient_cache=primary_cache)
    states = []
    for half, noise in enumerate(halves, start=1):
        alpha = tuple(map(float, source.recipe.half_tick_couplings[2 * step - 2 + half]))
        fine = baoab_step_with_hermitian_noise(fine, member=source.member, numerical_view=source.fine_view,
            next_alpha_tilde_x=alpha[0], next_alpha_tilde_y=alpha[1], standardized_noise=noise, gradient_cache=fine_cache)
        if not fine.finite:
            raise FloatingPointError('prepared fine native trajectory became nonfinite')
        states.append(fine)
    if not primary.finite:
        raise FloatingPointError('prepared primary native trajectory became nonfinite')
    return primary, states[0], fine, halves


def propagate_interval(source, primary, fine, *, end_tick, coarse_innovations, bridge_innovations, on_step=None):
    """Continue an interval without restarting either state or stream position.

    Arrays use absolute clocks, retain the start and every fine half step, and
    contain only this interval's innovations. The caller owns stream slicing.
    """
    from empirical_lawhood.domains.matrix.matrix_experimental_programme.preparation_science import _noise
    start = primary.step_index
    if (type(end_tick) is not int or not 0 <= start < end_tick <= source.total_ticks
            or fine.step_index != 2 * start):
        raise ValueError('preparation interval changes the selected absolute window')
    count = end_tick - start
    _noise(coarse_innovations, count)
    _noise(bridge_innovations, count)
    arrays = {'primary_innovations': coarse_innovations.copy(), 'bridge_innovations': bridge_innovations.copy(),
        'fine_innovations': np.empty((2 * count, 2, 3, 4, 4), dtype='<c16')}
    for prefix, mult, state in (('primary', 1, primary), ('fine', 2, fine)):
        ticks = np.arange(mult * start, mult * end_tick + 1, dtype='<i8')
        arrays[prefix + '_ticks'] = ticks
        arrays[prefix + '_alpha_tilde'] = np.asarray(source.recipe.half_tick_couplings[2 * start:2 * end_tick + 1:2 // mult], dtype='<f8')
        for name in ('positions', 'momenta'):
            arrays[prefix + '_' + name] = np.empty((len(ticks), 2, 3, 4, 4), dtype='<c16')
            arrays[prefix + '_' + name][0] = getattr(state, name)
    pc, fc = BAOABGradientCache(), BAOABGradientCache()
    for offset in range(count):
        primary, middle, fine, halves = advance_preparation_pair(primary, fine, source=source,
            step=start + offset + 1, coarse=coarse_innovations[offset], bridge=bridge_innovations[offset],
            primary_cache=pc, fine_cache=fc)
        arrays['fine_innovations'][2 * offset:2 * offset + 2] = halves
        for name in ('positions', 'momenta'):
            arrays['primary_' + name][offset + 1] = getattr(primary, name)
            arrays['fine_' + name][2 * offset + 1] = getattr(middle, name)
            arrays['fine_' + name][2 * offset + 2] = getattr(fine, name)
        if on_step is not None:
            on_step(3 * (offset + 1))
    return arrays
