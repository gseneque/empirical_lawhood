# SPDX-License-Identifier: MPL-2.0
"""Bounded paired history segments with exact four-stream continuation.

No effects occur at import. The scientific adapter must authenticate its source
and preceding completed checkpoint and retain a native contact before calling
this producer. No unknown or failed segment can be restarted here.
"""

from dataclasses import dataclass
from typing import ClassVar

import numpy as np

from empirical_lawhood.adapters.methods.matrix_history_analysis.records import HISTORY_PURPOSES, MatrixHistorySeed
from empirical_lawhood.kernel.matrix_inputs import MAXIMUM_MATRIX_ARRAY_BYTES
from empirical_lawhood.kernel.serialization import CanonicalRecord

from .model import SixMatrixState
from .parameter_history import MatrixParameterCoordinate, advance_parameter_pair, initial_parameter_state, split_parameter_innovations
from .parameter_ou_domain import validate_parameter_ou_domain
from .simulation import BAOABGradientCache, hermitian_noise

METHOD = 'Q2_ORIGINAL_BAOAB_PCG64DXSM_EXACT_SEGMENT_CONTINUATION_V1'
OPERATION_ID = 'matrix-parameter-history.segment-original-baoab-pcg64dxsm.v1'


@dataclass(frozen=True, slots=True)
class ParameterGeneratorState(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-segments/generator-state'
    purpose: str
    effective_seed: int
    state: int
    increment: int
    has_uint32: int
    uinteger: int
    completed_noise_matrices: int
    generator: str = 'numpy-pcg64dxsm'

    def __post_init__(self):
        if (self.purpose not in HISTORY_PURPOSES or self.generator != 'numpy-pcg64dxsm'
                or any(type(v) is not int for v in (self.effective_seed,self.state,self.increment,self.has_uint32,self.uinteger,self.completed_noise_matrices))
                or not 0 <= self.effective_seed < 2**128 or not 0 <= self.state < 2**128
                or not 0 < self.increment < 2**128 or self.increment % 2 != 1
                or self.has_uint32 not in (0,1) or not 0 <= self.uinteger < 2**32 or self.completed_noise_matrices < 0):
            raise ValueError('parameter segment changes exact PCG64DXSM purpose/state/cursor')

    def numpy_state(self):
        return {'bit_generator':'PCG64DXSM','state':{'state':self.state,'inc':self.increment},
                'has_uint32':self.has_uint32,'uinteger':self.uinteger}


@dataclass(frozen=True, slots=True)
class ParameterSegmentValues:
    start: int
    stop: int
    arrays: dict
    terminal_arrays: dict
    generators: tuple[ParameterGeneratorState, ...]


def segment_intervals(coordinate,start,stop):
    """Owned science rows; each initial/terminal row occurs exactly once."""
    if type(start) is not int or type(stop) is not int or not 0 <= start < stop <= coordinate.total_ticks:
        raise ValueError('parameter segment changes complete coarse-clock bounds')
    terminal = int(stop == coordinate.total_ticks)
    result = {}
    for prefix,multiplier in (('primary',1),('fine',2)):
        for component in ('positions','momenta','alpha_tilde','ticks'):
            result[prefix+'_'+component] = multiplier*start,multiplier*stop+terminal
        result[prefix+'_innovations'] = multiplier*start,multiplier*stop
    result['bridge_innovations'] = start,stop
    return dict(sorted(result.items()))


def validate_segment_entry(coordinate,streams,start,stop,*,terminal=None,generator_states=None):
    if (type(coordinate) is not MatrixParameterCoordinate or tuple(s.purpose for s in streams) != HISTORY_PURPOSES
            or any(type(s) is not MatrixHistorySeed for s in streams)
            or len({s.effective_seed for s in streams}) != len(HISTORY_PURPOSES)
            or coordinate.primary_view.rng_algorithm not in ('numpy.pcg64dxsm','numpy-pcg64dxsm')):
        raise ValueError('parameter segment changes actual coordinate or four historical purpose streams')
    validate_parameter_ou_domain(coordinate)
    intervals = segment_intervals(coordinate,start,stop)
    span, final = stop-start,int(stop == coordinate.total_ticks)
    decoded_bytes = (3*span+2*final)*2*96*16+(3*span+2*final)*24+4*span*96*16
    if decoded_bytes+11*10000 > MAXIMUM_MATRIX_ARRAY_BYTES:
        raise ValueError('selected parameter segment must fit an unchanged physical NPZ leaf')
    if start == 0:
        if terminal is not None or generator_states is not None:
            raise ValueError('initial segment cannot substitute a previous checkpoint')
    else:
        expected = {'primary_positions','primary_momenta','fine_positions','fine_momenta'}
        if not isinstance(terminal,dict) or set(terminal) != expected or generator_states is None:
            raise ValueError('continuation requires completed exact phase and generator checkpoint')
        for value in terminal.values():
            if value.dtype.str != '<c16' or value.shape != (2,3,4,4) or not np.isfinite(value).all():
                raise ValueError('parameter checkpoint loses complete finite q=2 phase space')
        if (tuple(s.purpose for s in generator_states) != HISTORY_PURPOSES
                or any(type(s) is not ParameterGeneratorState for s in generator_states)
                or any(s.effective_seed != stream.effective_seed for s,stream in zip(generator_states,streams,strict=True))
                or any(s.completed_noise_matrices != (min(start,coordinate.ramp_ticks) if s.purpose.startswith('preparation')
                    else max(0,start-coordinate.ramp_ticks)) for s in generator_states)):
            raise ValueError('parameter checkpoint substitutes exact stream state or complete draw cursor')
    return intervals


def acquire_parameter_segment(coordinate,streams,start,stop,*,terminal=None,generator_states=None,progress=None):
    """Bounded science after BEGIN; progress counts completed native integrations."""
    intervals = validate_segment_entry(coordinate,streams,start,stop,terminal=terminal,generator_states=generator_states)
    arrays = {}
    for name,(begin,end) in intervals.items():
        shape = (end-begin,2,3,4,4) if name.endswith(('positions','momenta','innovations')) else (end-begin,2) if name.endswith('alpha_tilde') else (end-begin,)
        dtype = '<c16' if name.endswith(('positions','momenta','innovations')) else '<f8' if name.endswith('alpha_tilde') else '<i8'
        arrays[name] = np.full(shape,np.nan,dtype=dtype) if dtype != '<i8' else np.arange(begin,end,dtype=dtype)
    generators = {s.purpose:np.random.Generator(np.random.PCG64DXSM(s.effective_seed)) for s in streams}
    if generator_states is not None:
        for saved in generator_states:
            generators[saved.purpose].bit_generator.state = saved.numpy_state()
        primary = SixMatrixState(2,terminal['primary_positions'],terminal['primary_momenta'],start,*coordinate.couplings(start))
        fine = SixMatrixState(2,terminal['fine_positions'],terminal['fine_momenta'],2*start,*coordinate.couplings(2*start,refinement=2))
    else:
        primary = fine = initial_parameter_state(coordinate)
    caches = BAOABGradientCache(),BAOABGradientCache()
    def store(prefix,state):
        begin,end = intervals[prefix+'_positions']
        if begin <= state.step_index < end:
            index = state.step_index-begin
            arrays[prefix+'_positions'][index] = state.positions
            arrays[prefix+'_momenta'][index] = state.momenta
            arrays[prefix+'_alpha_tilde'][index] = state.alpha_tilde_x,state.alpha_tilde_y
    store('primary',primary);store('fine',fine)
    for tick in range(start+1,stop+1):
        stage = 'preparation' if tick <= coordinate.ramp_ticks else 'autonomous'
        coarse = hermitian_noise(rng=generators[stage+'-coarse-driver'],q=2)
        bridge = hermitian_noise(rng=generators[stage+'-fine-bridge'],q=2)
        halves = split_parameter_innovations(coordinate,coarse,bridge)
        index = tick-start-1
        arrays['primary_innovations'][index] = coarse
        arrays['bridge_innovations'][index] = bridge
        arrays['fine_innovations'][2*index:2*index+2] = halves
        primary,first,fine = advance_parameter_pair(primary,fine,coordinate=coordinate,coarse_step=tick,
            coarse_noise=coarse,bridge_noise=bridge,primary_cache=caches[0],fine_cache=caches[1])
        if not primary.finite or not first.finite or not fine.finite:
            raise FloatingPointError('parameter segment became numerically invalid')
        store('primary',primary);store('fine',first);store('fine',fine)
        if progress is not None:
            progress(3*(tick-start))
    saved = []
    for stream in streams:
        state = generators[stream.purpose].bit_generator.state
        count = min(stop,coordinate.ramp_ticks) if stream.purpose.startswith('preparation') else max(0,stop-coordinate.ramp_ticks)
        saved.append(ParameterGeneratorState(stream.purpose,stream.effective_seed,state['state']['state'],state['state']['inc'],
            state['has_uint32'],state['uinteger'],count))
    terminal_arrays = {'primary_positions':primary.positions,'primary_momenta':primary.momenta,
                       'fine_positions':fine.positions,'fine_momenta':fine.momenta}
    return ParameterSegmentValues(start,stop,arrays,terminal_arrays,tuple(saved))
