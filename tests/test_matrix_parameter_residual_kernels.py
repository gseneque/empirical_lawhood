"""Literal array controls for shared residuals; no acquisition or qualification."""

from decimal import Decimal
from hashlib import sha256
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_parameter_history import chunked_science, independent
from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_history
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history_segments import segment_intervals
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from tests.test_matrix_parameter_native import REGIMES, coordinate


def _literal_history(family):
    """Complete, deliberately imperfect phase/noise rows, without a marcher."""
    c = coordinate(REGIMES[1], family=family, dt=Decimal('.001'))
    initial = parameter_history.initial_parameter_state(c)
    direction = np.zeros((2, 3, 4, 4), dtype='<c16')
    direction[0, 0, 0, 0] = .125
    direction[1, 2, 1, 2], direction[1, 2, 2, 1] = .0625j, -.0625j
    arrays = {}
    for prefix, refinement in (('primary', 1), ('fine', 2)):
        steps = refinement * c.total_ticks
        arrays[prefix + '_positions'] = np.asarray([
            initial.positions + (step / refinement) * direction for step in range(steps + 1)
        ], dtype='<c16')
        arrays[prefix + '_momenta'] = np.asarray([
            initial.momenta + (step / (2 * refinement)) * direction for step in range(steps + 1)
        ], dtype='<c16')
        arrays[prefix + '_alpha_tilde'] = np.asarray([
            c.couplings(step, refinement=refinement) for step in range(steps + 1)
        ], dtype='<f8')
        arrays[prefix + '_ticks'] = np.arange(steps + 1, dtype='<i8')
        arrays[prefix + '_innovations'] = np.asarray([
            ((step % 3) - 1) * direction for step in range(steps)
        ], dtype='<c16')
    arrays['bridge_innovations'] = np.asarray([
        (step % 2 + .5) * direction for step in range(c.total_ticks)
    ], dtype='<c16')
    return c, arrays


def _segment(c, arrays, start, stop):
    science = {name: arrays[name][begin:end].copy()
               for name, (begin, end) in segment_intervals(c, start, stop).items()}
    terminal = {
        'terminal_' + prefix + '_' + component: arrays[prefix + '_' + component][refinement * stop].copy()
        for prefix, refinement in (('primary', 1), ('fine', 2))
        for component in ('positions', 'momenta')
    }
    segment = SimpleNamespace(checkpoint=SimpleNamespace(start=start, stop=stop))
    return segment, science, terminal


# Exact residual bytes retained from both pre-consolidation owners on this
# literal exposed corpus. These are regression controls, not scientific data.
_ORIGINAL_RESIDUAL_DIGESTS = {
    0: '3600054425d1c9df2a49182e476f2282594b778a8818fa849393a32b7776685c',
    1: 'fde8a75f347e20dfda44b2c08c21edced0c5dfcfd2fd1df2bd3ab1bb8dbddba1',
    2: 'c7effbc9bcaa7c98a3719291bc278e51a11ff9bdc2765f35ce47a6fbe3b78a77',
    3: 'd6f89f435e94069601af685c5ab14685080fbfb2df48167caf15e08ae7fd02a6',
}
_ORIGINAL_CONTROL_DIGESTS = {
    0: '1fb6022e8cf7633fd6c9357e630eee77a97bdf65e4393e2c0cade9825a10e31e',
    1: '7cb70033bae50769d80a54f6fd61451dc1db3be6768b41b50d08d172c7b1ef45',
    2: 'fd848dc92819de74e46f1b73c6e71378e4f0cb73a63f201fb8b56c904bef970d',
    3: '8ba737b96b88705f3cf13362d3ff0c34104d61b2f4bb7daad313c08d8b5df91c',
}


@pytest.mark.parametrize('family', range(4))
def test_dense_and_segmented_controls_preserve_exact_residuals_and_denominators(family, monkeypatch):
    def prohibited(*args, **kwargs):
        pytest.fail('literal residual controls cannot acquire, march or draw noise')

    monkeypatch.setattr(parameter_history, 'advance_parameter_pair', prohibited)
    monkeypatch.setattr(np.random, 'Generator', prohibited)
    c, arrays = _literal_history(family)
    tolerances = (Decimal('.1'), Decimal('.01'))
    dense = independent.assess_arrays(c, arrays, trajectory_tolerance=tolerances[0],
                                     bridge_tolerance=tolerances[1])
    rows = [[] for _ in dense]
    previous = None
    for start, stop in ((0, 3), (3, 6), (6, 8)):
        segment, science, terminal = _segment(c, arrays, start, stop)
        actual = chunked_science._segment_controls(SimpleNamespace(coordinate=c), segment,
                                                   science, terminal, previous)
        for retained, values in zip(rows, actual, strict=True):
            retained.extend(values)
        previous = terminal
    for control, values in zip(dense, rows, strict=True):
        assert independent._control(control['control_id'], control['method'], values,
                                    control['tolerance'], control['denominator_real_coordinates']) == control
    assert tuple(control['denominator_steps'] for control in dense) == (8, 16, 8, 8)
    assert tuple(control['denominator_real_coordinates'] for control in dense) == (192, 192, 192, 96)
    digest = sha256(b''.join(np.asarray(row, dtype='<f8').tobytes() for row in rows)).hexdigest()
    assert digest == _ORIGINAL_RESIDUAL_DIGESTS[family]
    assert sha256(canonical_json_bytes(dense)).hexdigest() == _ORIGINAL_CONTROL_DIGESTS[family]


def test_reference_trajectory_residual_has_full_phase_norm_and_terminal_fallback():
    c, _ = _literal_history(0)
    zeros = np.zeros((1, 2, 3, 4, 4), dtype='<c16')
    terminal_position, terminal_momentum = zeros[0].copy(), zeros[0].copy()
    terminal_position[0, 0, 0, 0] = 3
    terminal_momentum[1, 2, 3, 3] = 4
    alpha = np.zeros((1, 2), dtype='<f8')
    assert independent._trajectory_errors(zeros, zeros, zeros, c.member, c.primary_view,
        alpha, alpha, terminal=(terminal_position, terminal_momentum)) == [5.]
    phase = np.concatenate((zeros, terminal_position[None]))
    momentum = np.concatenate((zeros, terminal_momentum[None]))
    assert independent._trajectory_errors(phase, momentum, zeros, c.member, c.primary_view,
                                          alpha, alpha) == [5.]


def test_ou_residual_uses_complete_two_half_innovations_and_bath_scale():
    view = SimpleNamespace(timestep=Decimal('1'), friction_gamma=Decimal('0'),
                           bath_temperature=Decimal('2'))
    coarse = np.zeros((1, 2, 3, 4, 4), dtype='<c16')
    fine = np.zeros((2, 2, 3, 4, 4), dtype='<c16')
    fine[0, 0, 0, 0, 0] = 3
    fine[1, 1, 2, 3, 3] = 4
    assert independent._ou_errors(view, coarse, fine, coarse) == ([5.], [0.])
    # Half decay underflows to zero here: the bath impulse retains the second
    # half's norm, scaled by sqrt(T)=2, while reconstruction still uses both.
    view = SimpleNamespace(timestep=Decimal('1'), friction_gamma=Decimal('2000'),
                           bath_temperature=Decimal('4'))
    assert independent._ou_errors(view, coarse, fine, coarse) == ([5.], [8.])


@pytest.mark.parametrize(('defect', 'message'), (
    ('missing-member', 'omits full original scientific members'),
    ('wrong-tick', 'exact physical tick denominator'),
    ('wrong-coupling', 'actual native coupling schedule'),
    ('wrong-previous-phase', 'exact previous terminal/initial phase'),
    ('wrong-final-endpoint', 'complete science endpoint'),
))
def test_segment_source_guards_remain_before_residual_release(defect, message):
    c, arrays = _literal_history(0)
    start, stop = (6, 8) if defect == 'wrong-final-endpoint' else (3, 6)
    segment, science, terminal = _segment(c, arrays, start, stop)
    previous = _segment(c, arrays, 0, start)[2]
    if defect == 'missing-member':
        del science['bridge_innovations']
    elif defect == 'wrong-tick':
        science['primary_ticks'][0] += 1
    elif defect == 'wrong-coupling':
        science['fine_alpha_tilde'][0, 0] += .25
    elif defect == 'wrong-previous-phase':
        previous['terminal_primary_positions'][0, 0, 0, 0] += .25
    else:
        terminal['terminal_fine_positions'][0, 0, 0, 0] += .25
    with pytest.raises(ValueError, match=message):
        chunked_science._segment_controls(SimpleNamespace(coordinate=c), segment,
                                         science, terminal, previous)
