"""SCF stopping controls; these do not qualify an enzyme or a force backend."""
from dataclasses import replace
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.rubisco.rubisco_response.periodic_qmmm import solve_selected_scf
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_force_contracts import PeriodicForceSettings
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from tests.rubisco_periodic_fixture import make_periodic_fixture


def test_unlimited_scf_selection_and_historical_bytes_round_trip():
    finite = make_periodic_fixture()[3]
    for value in (finite, replace(finite, maximum_scf_cycles=None)):
        assert decode_canonical_bytes(value.canonical_bytes(), PeriodicForceSettings, maximum_bytes=4096) == value
    for invalid in (0, -1, False, 2.5):
        with pytest.raises(ValueError, match='SCF iterations'):
            replace(finite, maximum_scf_cycles=invalid)


def test_unlimited_scf_retains_density_and_full_iteration_denominator():
    iterations, observations, calls = [], [], []
    density = object()
    solver = SimpleNamespace(callback=lambda state: iterations.append(state['cycle']),
        make_rdm1=lambda: density, cycles=0, converged=False)
    original_callback = solver.callback

    def kernel(**kwargs):
        calls.append((solver.max_cycle, kwargs))
        solver.cycles = solver.max_cycle if len(calls) < 3 else 7
        for i in range(solver.cycles):
            solver.callback(dict(cycle=i))
        solver.converged = len(calls) == 3
        return -12.5

    solver.kernel = kernel
    assert solve_selected_scf(solver, None, observe=observations.append, evaluation=4) == -12.5
    assert calls == [(50, {}), (100, {'dm0': density}), (200, {'dm0': density})]
    assert iterations == list(range(157))
    assert [r['cumulative_cycles'] for r in observations] == [50, 150, 157]
    assert [r['converged'] for r in observations] == [False, False, True]
    assert all(r['evaluation'] == 4 and r['count_ceiling'] is None for r in observations)
    assert solver.callback is original_callback


@pytest.mark.parametrize('energy,cycles', [(float('nan'), 50), (-1., 0), (-1., 51)])
def test_unlimited_scf_refuses_numerical_breakdown_and_restores_observer(energy, cycles):
    solver = SimpleNamespace(callback=lambda state: None, cycles=cycles, converged=False,
        kernel=lambda: energy)
    original = solver.callback
    rows = []
    with pytest.raises(ValueError, match='SCF continuation returned'):
        solve_selected_scf(solver, None, observe=rows.append, evaluation=1)
    assert len(rows) == 1
    assert solver.callback is original


def test_native_scf_failure_propagates_without_replay():
    calls = []
    solver = SimpleNamespace(callback=lambda state: None)
    original = solver.callback

    def kernel():
        calls.append(1)
        raise ArithmeticError('original numerical failure')

    solver.kernel = kernel
    with pytest.raises(ArithmeticError, match='original numerical failure'):
        solve_selected_scf(solver, None, observe=lambda row: None, evaluation=1)
    assert calls == [1] and solver.callback is original


def test_finite_historical_scf_selection_does_not_continue_a_failed_solution():
    calls = []
    solver = SimpleNamespace(kernel=lambda: calls.append(1) or -2., converged=False)
    assert solve_selected_scf(solver, 3, observe=lambda row: pytest.fail('unexpected extra chunk'), evaluation=1) == -2.
    assert solver.max_cycle == 3 and calls == [1] and not solver.converged


@pytest.mark.parametrize('maximum_cycles', [3, None])
def test_selected_initial_density_is_only_a_first_chunk_guess(maximum_cycles):
    initial, updated = object(), object()
    calls, observations = [], []
    solver = SimpleNamespace(callback=lambda state: None, make_rdm1=lambda: updated,
        cycles=0, converged=False)

    def kernel(**kwargs):
        calls.append(kwargs)
        solver.cycles = solver.max_cycle
        solver.converged = len(calls) == 2
        return -2.

    solver.kernel = kernel
    assert solve_selected_scf(solver, maximum_cycles, observe=observations.append,
        evaluation=1, initial_density=initial) == -2.
    assert calls[0] == {'dm0': initial}
    if maximum_cycles is None:
        assert calls == [{'dm0': initial}, {'dm0': updated}]
        assert [row['cumulative_cycles'] for row in observations] == [50, 150]
    else:
        assert len(calls) == 1 and not solver.converged
