# SPDX-License-Identifier: MPL-2.0
"""Tiny exposed scheduled-pulse equation controls, never a scientific bank."""

from dataclasses import replace
from decimal import Decimal as D

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history import response_native as response
from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_derivatives, parameter_source
from empirical_lawhood.adapters.simulators.six_matrix_response.model import SixMatrixState
from tests.test_matrix_factor_confirmation_eligibility import provenance as provenance
from tests.test_matrix_factor_confirmation_eligibility import stock as stock
from tests.test_matrix_scheduled_history import scheduled as scheduled


def blocked(*args, **kwargs):
    raise AssertionError('independent received-path control entered Native/producer/RNG/eigen')


def branches(scheduled):
    source = scheduled[1][0]
    c = source.coordinate
    full = parameter_source.acquire_parameter_history(c, source.root.streams)
    direction = np.zeros((2, 3, 4, 4), dtype='<c16')
    direction[0, 0] = np.eye(4)/2
    direction[1, 1] = np.diag((1, -1, 1, -1))/2
    direction /= np.linalg.norm(direction)
    result = []
    for view, refinement in (('primary', 1), ('fine', 2)):
        start, count = 2*refinement, 3*refinement
        state = SixMatrixState(2, full[view+'_positions'][start], full[view+'_momenta'][start], start,
            *c.couplings(start, refinement=refinement))
        for sign in (0, -1, 1):
            amplitude = sign*.01
            noise = full[view+'_innovations'][start:start+count].copy()
            actual = response.native_scheduled_branch(state, coordinate=c, refinement=refinement, direction=direction,
                amplitude=amplitude, pulse_steps=2*refinement, innovations=noise)
            result.append((c, state, refinement, direction, amplitude, actual))
    return result


def test_scheduled_pulse_both_views_signs_hold_and_pulse_end_reprove_without_producers(scheduled, monkeypatch):
    actual = branches(scheduled)
    monkeypatch.setattr(response, 'native_scheduled_branch', blocked)
    monkeypatch.setattr(parameter_derivatives, 'scheduled_force_step', blocked)
    monkeypatch.setattr(parameter_source, 'acquire_parameter_history', blocked)
    monkeypatch.setattr(np.random, 'Generator', blocked)
    monkeypatch.setattr(np.random, 'PCG64DXSM', blocked)
    monkeypatch.setattr(np.linalg, 'eigh', blocked)
    monkeypatch.setattr(np.linalg, 'eigvalsh', blocked)
    for c, state, refinement, direction, amplitude, arrays in actual:
        assert not np.array_equal(arrays['alpha_tilde'][0], arrays['alpha_tilde'][-1])
        control = response.assess_scheduled_branch(c, arrays, refinement=refinement, initial_positions=state.positions,
            initial_momenta=state.momenta, start_tick=state.step_index, direction=direction, amplitude=amplitude,
            pulse_steps=2*refinement, tolerance=D('1e-9'), control_id='control.software.pulse.'+str(refinement)+'.'+str(int(100*amplitude)))
        assert control.disposition == 'SATISFIED'
        assert control.denominator_steps == 3*refinement and control.denominator_real_coordinates == 192
        assert len(control.measured_errors) == 3*refinement
    for primary, fine in ((actual[i], actual[i+3]) for i in range(3)):
        assert primary[1].step_index*2 == fine[1].step_index
        assert not np.array_equal(primary[1].positions, fine[1].positions)


@pytest.mark.parametrize('defect', ('clock', 'schedule', 'start', 'halfview', 'pulse-force', 'phase'))
def test_scheduled_response_received_array_or_force_falsifiers(scheduled, defect, monkeypatch):
    c, state, refinement, direction, amplitude, original = branches(scheduled)[-1]
    arrays = {n: a.copy() for n, a in original.items()}
    if defect == 'clock':
        arrays['ticks'][1] += 1
    elif defect == 'schedule':
        arrays['alpha_tilde'][2, 0] += .125
    elif defect == 'start':
        state = replace(state, positions=state.positions+.125*np.eye(4)[None, None])
    elif defect == 'halfview':
        arrays['positions'] = arrays['positions'][::2]
    elif defect == 'pulse-force':
        amplitude = -amplitude
    else:
        arrays['momenta'][2, 1, 0, 0, 0] += .125
    monkeypatch.setattr(np.random, 'Generator', blocked)
    monkeypatch.setattr(parameter_derivatives, 'scheduled_force_step', blocked)
    try:
        control = response.assess_scheduled_branch(c, arrays, refinement=refinement, initial_positions=state.positions,
            initial_momenta=state.momenta, start_tick=state.step_index, direction=direction, amplitude=amplitude,
            pulse_steps=2*refinement, tolerance=D('1e-9'), control_id='control.software.changed')
    except ValueError:
        assert defect in ('clock', 'schedule', 'start', 'halfview')
    else:
        assert control.disposition == 'VIOLATED' and control.failed_steps
