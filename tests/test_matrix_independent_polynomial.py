# SPDX-License-Identifier: MPL-2.0
"""Exact comparison to the unchanged literal trace expansion, not tolerance."""

from decimal import Decimal
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_parameter_history import independent as original
from empirical_lawhood.adapters.methods.matrix_parameter_history import independent_polynomial as compiled
from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_source
from tests.test_matrix_parameter_history import source
from tests.test_matrix_parameter_native import REGIMES, coordinate


def literal_gradient(position, member, couplings):
    """The pre-optimization occurrence loop over the independent polynomial."""
    matrices = original._position(position).reshape(6,4,4)
    result = np.zeros_like(matrices)
    for coefficient, word in original._trace_words(member,couplings):
        for occurrence, destination in enumerate(word):
            remaining = word[occurrence + 1:] + word[:occurrence]
            result[destination] += coefficient * original._word_product(matrices,remaining)
    return original._hermitian(result).reshape(2,3,4,4)


@pytest.mark.parametrize('masses,cross', (((.2,.3),.4), ((.5,1.),1.), ((.9,2.2),1.8)))
def test_compiled_gradient_is_bit_identical_across_states_and_zero_couplings(masses,cross):
    rng = np.random.default_rng(6211703)
    member = SimpleNamespace(mass_x=masses[0],mass_y=masses[1],cross_coupling_gamma=cross)
    for index in range(32):
        raw = (rng.normal(size=(2,3,4,4)) + 1j*rng.normal(size=(2,3,4,4))) * (1e-6,1.,1e4)[index%3]
        state = (raw + raw.swapaxes(-1,-2).conj())/2
        couplings = ((0.,0.),(0.,2.1),(4.8,0.),(4.8,2.1))[index%4]
        for layout in (state,np.asfortranarray(state),state[:,::-1]):
            expected = literal_gradient(layout,member,couplings)
            assert original.potential_gradient(layout,member,couplings).tobytes() == expected.tobytes()


@pytest.mark.parametrize('regime', REGIMES)
def test_all_paired_control_decimals_and_denominators_are_exact(regime,monkeypatch):
    streams = source(regime).root.streams
    for family in range(4):
        selected = coordinate(regime,family=family,dt=Decimal('.001'))
        values = parameter_source.acquire_parameter_history(selected,streams)
        actual = original.assess_arrays(selected,values,trajectory_tolerance=Decimal('1e-8'),
            bridge_tolerance=Decimal('1e-11'))
        with monkeypatch.context() as old:
            old.setattr(original,'potential_gradient',literal_gradient)
            expected = original.assess_arrays(selected,values,trajectory_tolerance=Decimal('1e-8'),
                bridge_tolerance=Decimal('1e-11'))
        assert actual == expected
        assert tuple(row['denominator_steps'] for row in actual) == (8,16,8,8)


def test_word_topology_is_bounded_and_built_once_for_repeated_gradients(monkeypatch):
    compiled._plan.cache_clear()
    calls = []
    literal = original._trace_words
    def counted(*args):
        calls.append(1)
        return literal(*args)
    monkeypatch.setattr(original,'_trace_words',counted)
    member = SimpleNamespace(mass_x=.7,mass_y=1.3,cross_coupling_gamma=.2)
    state = np.zeros((2,3,4,4),dtype=np.complex128)
    for index in range(32):
        original.potential_gradient(state,member,(index/10,index/20))
    assert calls == [1] and compiled._plan.cache_info().maxsize == 32
    for couplings in ((-1.,0.),(float('nan'),0.)):
        with pytest.raises(ValueError,match='positive physical domain'):
            original.potential_gradient(state,member,couplings)
