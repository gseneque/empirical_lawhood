"""Exposed segment equations and exact stream continuity; no qualification."""

from dataclasses import replace
from decimal import Decimal

import numpy as np
import pytest

from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history_segments import acquire_parameter_segment, segment_intervals, validate_segment_entry
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_source import acquire_parameter_history
from empirical_lawhood.adapters.methods.matrix_parameter_history.chunked_records import MatrixParameterChunkedSource, bind_source, segment_plan
from tests.test_matrix_parameter_compact_history import selected


def test_three_segments_preserve_every_original_state_noise_and_generator_cursor():
    sources,a,p = selected()
    c,streams = a.coordinates[0],a.roots[0].streams
    expected = acquire_parameter_history(c,streams)
    pieces = {name:[] for name in expected}
    terminal,states = None,None
    for start,stop in ((0,3),(3,6),(6,8)):
        values = acquire_parameter_segment(c,streams,start,stop,terminal=terminal,generator_states=states)
        for name,array in values.arrays.items():
            begin,end = segment_intervals(c,start,stop)[name]
            assert np.array_equal(array,expected[name][begin:end])
            pieces[name].append(array)
        terminal,states = values.terminal_arrays,values.generators
    for name,arrays in pieces.items():
        assert np.array_equal(np.concatenate(arrays),expected[name])
    assert tuple(g.completed_noise_matrices for g in states) == (4,4,4,4)


@pytest.mark.parametrize('defect',('missing-terminal','missing-stream-state','wrong-cursor','wrong-seed','wrong-phase-shape'))
def test_continuation_refuses_before_generators_or_draws(defect,monkeypatch):
    _,a,_ = selected();c,streams = a.coordinates[0],a.roots[0].streams
    values = acquire_parameter_segment(c,streams,0,3)
    terminal,states = dict(values.terminal_arrays),values.generators
    if defect == 'missing-terminal':
        terminal = None
    elif defect == 'missing-stream-state':
        states = None
    elif defect == 'wrong-cursor':
        states = (replace(states[0],completed_noise_matrices=9),*states[1:])
    elif defect == 'wrong-seed':
        states = (replace(states[0],effective_seed=states[0].effective_seed+1),*states[1:])
    else:
        terminal['fine_positions'] = terminal['fine_positions'][0]
    def blocked(*args,**kwargs):
        pytest.fail('invalid continuation cannot instantiate or consume streams')
    monkeypatch.setattr(np.random,'Generator',blocked)
    with pytest.raises(ValueError):
        acquire_parameter_segment(c,streams,3,6,terminal=terminal,generator_states=states)


def test_unsupported_numerical_domain_refuses_before_generators(monkeypatch):
    _,a,_ = selected();c = a.coordinates[0]
    c = replace(c,primary_view=replace(c.primary_view,friction_gamma=Decimal('1e-18')),
        fine_view=replace(c.fine_view,friction_gamma=Decimal('1e-18')))
    def blocked(*args,**kwargs):
        pytest.fail('unsupported domain cannot instantiate streams')
    monkeypatch.setattr(np.random,'Generator',blocked)
    with pytest.raises(ValueError,match='unsupported numerical OU domain'):
        validate_segment_entry(c,a.roots[0].streams,0,3)


def test_source_duration_beyond4341_is_preserved_not_capped():
    from empirical_lawhood.adapters.methods.matrix_parameter_history.compact_records import compact_sources
    from empirical_lawhood.adapters.methods.matrix_parameter_history.records import coordinate_identity
    sources,a,p = selected();c = replace(a.coordinates[0],autonomous_ticks=4996,observation_ticks=(0,5000))
    root = replace(a.roots[0],coordinate=coordinate_identity(c))
    a = replace(a,coordinates=(c,),roots=(root,))
    compact = compact_sources(a,p,sources[0].numerical_design,namespace='source.long')[0]
    s = MatrixParameterChunkedSource('source.chunked.long',compact,128)
    bound = bind_source(s,a,c,p,new_entry=True)
    plan = segment_plan(bound)
    assert plan[0] == (0,128) and plan[-1] == (4992,5000)
    assert sum(stop-start for start,stop in plan) == 5000
    with pytest.raises(ValueError,match='physical NPZ'):
        bind_source(replace(s,segment_steps=5000),a,c,p)
