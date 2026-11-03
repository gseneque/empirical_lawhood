# SPDX-License-Identifier: MPL-2.0
"""Exact retained Gram compatibility against the original vdot loop."""

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_parameter_factor import independent


def literal_operator(triplet):
    commutators = [[z@b-b@z for b in independent.BASIS] for z in triplet]
    value = np.empty((15,15),dtype='<f8')
    for i in range(15):
        for j in range(15):
            value[i,j] = sum(float(np.vdot(row[i],row[j]).real) for row in commutators)
    return (value+value.T)/2


@pytest.mark.parametrize('scale', (1e-6,1.,1e4))
def test_vecdot_gram_preserves_every_float_bit(scale):
    rng = np.random.default_rng(6211703)
    for _ in range(32):
        values = (rng.normal(size=(3,4,4)) + 1j*rng.normal(size=(3,4,4))) * scale
        triplet = (values + values.swapaxes(-1,-2).conj())/2
        for layout in (triplet,np.asfortranarray(triplet),triplet[::-1]):
            assert independent.raw_operator(layout).tobytes() == literal_operator(layout).tobytes()
    for special in ([],np.zeros((3,4,4),dtype='<c16'),np.array([np.eye(4)]*3)):
        assert independent.raw_operator(special).tobytes() == literal_operator(special).tobytes()
