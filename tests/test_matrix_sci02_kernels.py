# SPDX-License-Identifier: MPL-2.0
"""Supplied-array controls; these checks are not SCI02 acquisition evidence."""
from dataclasses import replace
from decimal import Decimal as D
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.domains.matrix.matrix_experimental_programme.preparation_intervals import propagate_interval
from empirical_lawhood.domains.matrix.matrix_factor_response.refresh_science import continue_response, continue_response_window
from empirical_lawhood.domains.matrix.matrix_factor_response.refresh_read import affine_response_window
from empirical_lawhood.domains.matrix.six_matrix_response.contracts import BetaCouplingRule, MatrixIntegratorKind, MatrixPrecision, SixMatrixResponseModelFamilyMember, SixMatrixResponseNumericalView
from empirical_lawhood.domains.matrix.six_matrix_response.model import SixMatrixState


def interval_operands():
    member = SixMatrixResponseModelFamilyMember('test.member', D('.5'), D('.5'), D(1), BetaCouplingRule.PUBLISHED_DETERMINISTIC)
    primary = SixMatrixResponseNumericalView('test.primary', MatrixIntegratorKind.BAOAB_UNDERDAMPED_LANGEVIN,
        D('.001'), 'dimensionless-langevin-time', D(1), D(1), MatrixPrecision.COMPLEX128,
        'numpy.pcg64dxsm', '1.0.0', 'test.stream', 512)
    fine = replace(primary, view_id='test.fine', timestep=D('.0005'))
    source = SimpleNamespace(member=member, primary_view=primary, fine_view=fine, total_ticks=256,
        recipe=SimpleNamespace(half_tick_couplings=tuple((D(1) + D(i) / 1000, D(2)) for i in range(513))))
    q = np.zeros((2, 3, 4, 4), dtype='<c16')
    q[..., 0, 0] = .02
    state = SixMatrixState(2, q, q.copy() / 10, 0, 1., 2.)
    coarse = np.broadcast_to(q, (256, *q.shape)).copy()
    bridge = coarse * .3
    return source, state, coarse, bridge


def test_split_at64_preserves_distinct_states_clocks_and_all_original_bytes():
    source, initial, coarse, bridge = interval_operands()
    whole = propagate_interval(source, initial, initial, end_tick=256,
        coarse_innovations=coarse, bridge_innovations=bridge)
    first = propagate_interval(source, initial, initial, end_tick=64,
        coarse_innovations=coarse[:64], bridge_innovations=bridge[:64])
    starts = []
    for name in ('primary', 'fine'):
        starts.append(SixMatrixState(2, first[name + '_positions'][-1], first[name + '_momenta'][-1],
            int(first[name + '_ticks'][-1]), *first[name + '_alpha_tilde'][-1]))
    assert not np.array_equal(starts[0].momenta, starts[1].momenta)
    second = propagate_interval(source, *starts, end_tick=256,
        coarse_innovations=coarse[64:], bridge_innovations=bridge[64:])
    for key, expected in whole.items():
        joined = np.concatenate((first[key], second[key] if key.endswith('innovations') else second[key][1:]))
        np.testing.assert_array_equal(joined, expected)
    with pytest.raises(ValueError, match='clock|window'):
        propagate_interval(source, starts[0], starts[0], end_tick=256,
            coarse_innovations=coarse[64:], bridge_innovations=bridge[64:])


@pytest.mark.parametrize('dt', (D('.001'), D('.0005')))
@pytest.mark.parametrize('refresh', (False, True))
def test_h64_preserves_old_prefix_and_independent_affine_equations(dt, refresh):
    h0 = np.array([[1., .3], [.3, 7.]])
    h32 = np.array([[4., -.2], [-.2, 2.]]) if refresh else h0
    force = np.array([[.01, .02, .03, -.02], [.03, -.01, .01, .01]])
    basis = np.eye(2)
    kwargs = dict(timestep=dt, friction=D(1), primary_horizon=64, pulse_ticks=16, refresh_tick=32)
    actual = continue_response_window(h0, basis, force, refresh_operator=h32 if refresh else None, **kwargs)
    expected = affine_response_window(h0, h32, basis, force, **kwargs)
    mult = 1 if dt == D('.001') else 2
    old = continue_response(h0, basis, force, timestep=dt, friction=D(1), native_horizon=128 * mult,
        refresh_operator=h32 if refresh else None)
    np.testing.assert_array_equal(actual, old[:, :64 * mult + 1])
    np.testing.assert_allclose(actual, expected, rtol=2e-14, atol=1e-18)
    frozen = continue_response_window(h0, basis, force, **kwargs)
    np.testing.assert_array_equal(actual[:, :32 * mult + 1], frozen[:, :32 * mult + 1])
    with pytest.raises(ValueError, match='SCI01'):
        continue_response(h0, basis, force, timestep=dt, friction=D(1), native_horizon=64 * mult)
