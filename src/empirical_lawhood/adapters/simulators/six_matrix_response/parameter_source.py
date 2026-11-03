"""Complete parameter-consistent histories for an explicitly selected root.

The caller owns source qualification and the guarded native contact. This new
wrapper retains every integration state and innovation; it does not change the
historical fixed history producer or acquire any data at import time.
"""

import numpy as np

from empirical_lawhood.adapters.methods.matrix_history_analysis.records import HISTORY_PURPOSES, MatrixHistorySeed
from empirical_lawhood.kernel.matrix_inputs import MAXIMUM_MATRIX_ARRAY_BYTES

from .parameter_history import MatrixParameterCoordinate, advance_parameter_pair, initial_parameter_state, split_parameter_innovations
from .simulation import BAOABGradientCache, hermitian_noise

IMPLEMENTATION_ID = 'six-matrix-q2.parameter-complete-pcg64dxsm-history.v1'


def acquire_parameter_history(coordinate, streams, *, progress=None):
    """One complete paired trajectory, only after the caller's native BEGIN.

    Numerical failure raises and cannot furnish a completed scientific operand.
    The guarded caller retains its known failed receipt/unknown consumed streams;
    an interrupted contact must never be automatically repeated.
    """
    if (type(coordinate) is not MatrixParameterCoordinate
            or tuple(s.purpose for s in streams) != HISTORY_PURPOSES
            or any(type(s) is not MatrixHistorySeed for s in streams)
            or len({s.effective_seed for s in streams}) != len(HISTORY_PURPOSES)
            or coordinate.primary_view.rng_algorithm not in ('numpy.pcg64dxsm','numpy-pcg64dxsm')):
        raise ValueError('parameter acquisition changes actual coordinate or four-purpose PCG64DXSM source')
    n = coordinate.total_ticks
    decoded_bytes = (3*n+2)*2*96*16 + (3*n+2)*24 + 4*n*96*16
    if decoded_bytes + 11*10000 > MAXIMUM_MATRIX_ARRAY_BYTES:
        raise ValueError('parameter scientific duration needs an explicit chunked transport successor')
    arrays = {}
    for view, count in (('primary',n+1),('fine',2*n+1)):
        for component in ('positions','momenta'):
            arrays[view+'_'+component] = np.full((count,2,3,4,4),np.nan,dtype='<c16')
        arrays[view+'_alpha_tilde'] = np.full((count,2),np.nan,dtype='<f8')
        arrays[view+'_ticks'] = np.arange(count,dtype='<i8')
    for name, count in (('primary_innovations',n),('fine_innovations',2*n),('bridge_innovations',n)):
        arrays[name] = np.full((count,2,3,4,4),np.nan,dtype='<c16')
    generators = {s.purpose:np.random.Generator(np.random.PCG64DXSM(s.effective_seed)) for s in streams}
    caches = BAOABGradientCache(),BAOABGradientCache()
    primary = fine = initial_parameter_state(coordinate)
    def store(view,state):
        for name in ('positions','momenta'):
            arrays[view+'_'+name][state.step_index] = getattr(state,name)
        arrays[view+'_alpha_tilde'][state.step_index] = state.alpha_tilde_x,state.alpha_tilde_y
    store('primary',primary)
    store('fine',fine)
    for tick in range(1,n+1):
        stage = 'preparation' if tick <= coordinate.ramp_ticks else 'autonomous'
        coarse = hermitian_noise(rng=generators[stage+'-coarse-driver'],q=2)
        bridge = hermitian_noise(rng=generators[stage+'-fine-bridge'],q=2)
        halves = split_parameter_innovations(coordinate,coarse,bridge)
        arrays['primary_innovations'][tick-1] = coarse
        arrays['bridge_innovations'][tick-1] = bridge
        arrays['fine_innovations'][2*tick-2:2*tick] = halves
        primary,first,fine = advance_parameter_pair(primary,fine,coordinate=coordinate,coarse_step=tick,
            coarse_noise=coarse,bridge_noise=bridge,primary_cache=caches[0],fine_cache=caches[1])
        if not primary.finite or not first.finite or not fine.finite:
            raise FloatingPointError('parameter native history became numerically invalid')
        store('primary',primary)
        store('fine',first)
        store('fine',fine)
        if progress is not None:
            progress(tick,2*tick)
    return arrays
