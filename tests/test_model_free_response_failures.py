# SPDX-License-Identifier: MPL-2.0
"""Numerical-failure custody controls; exposed small native fixtures only."""
from copy import deepcopy

import pytest

from empirical_lawhood.domains.matrix.model_free import native, science
from tests.test_matrix_model_free_science import tiny_settings


def prepared_response():
    settings = tiny_settings()
    settings['response']['port_controls'] = False
    m1 = science.acquire_root(settings, 31, 'M1')
    return settings, m1


def test_response_keeps_completed_futures_and_counts_failing_future_once(monkeypatch):
    settings, m1 = prepared_response()
    original = native.paired_response

    def fail_refinement(*args, **kwargs):
        if kwargs['refinement'] == 2:
            raise native.NativeResponseFailure(FloatingPointError('late refinement failure'), {
                'native_force_evaluations': 7, 'native_hessian_actions': 3,
                'native_energy_evaluations': 2, 'counts_are_lower_bounds': True})
        return original(*args, **kwargs)

    monkeypatch.setattr(native, 'paired_response', fail_refinement)
    acquired = science.acquire_root(settings, 31, 'M3', prerequisite_payloads={'M1': m1})
    assert acquired['assigned_case_count'] == len(acquired['cases']) == 2
    for case in acquired['cases']:
        assert case['status'] == 'UNAVAILABLE'
        assert case['completed_scientific_prefix']['native_futures'] == 2
        assert case['completed_scientific_prefix']['failure_stage'] == 'NATIVE_FUTURES'
        assert len(case['futures']) == 2 and case['certificates']
        assert case['actual_force_evaluations'] == sum(row['force_evaluations'] for row in case['futures'])
    assert acquired['work_accounting']['native_force_evaluations'] == sum(case['actual_force_evaluations'] for case in acquired['cases'])+14
    assert acquired['work_accounting']['native_hessian_actions'] == sum(case['actual_hessian_actions'] for case in acquired['cases'])+6
    assert acquired['work_accounting']['counts_are_lower_bounds']
    readout = science.analyse_root(settings, acquired)
    assert all('futures' not in case and len(case['completed_native_futures']) == 2 for case in readout['cases'])


def test_response_keeps_completed_models_and_inflight_action_ledger(monkeypatch):
    settings, m1 = prepared_response()
    original = science._reduced_propagation
    failed_actions = []

    def fail_later_model(*args, **kwargs):
        result = original(*args, **kwargs)
        if args[7]:  # The explicit refresh schedule follows origin-only.
            failed_actions.append(result['hessian_actions'])
            raise FloatingPointError('late model reduction failure')
        return result

    monkeypatch.setattr(science, '_reduced_propagation', fail_later_model)
    acquired = science.acquire_root(settings, 31, 'M3', prerequisite_payloads={'M1': m1})
    assert len(failed_actions) == len(acquired['cases']) == 2
    for case, completed_inflight in zip(acquired['cases'], failed_actions):
        assert case['status'] == 'UNAVAILABLE'
        assert case['completed_scientific_prefix']['failure_stage'] == 'REDUCED_MODELS'
        assert len(case['linear_models']) == 1 and len(case['futures']) == 4
        assert case['model_action_attempts'] == sum(row['hessian_actions'] for row in case['linear_models'])+completed_inflight
        assert case['actual_hessian_actions'] >= case['model_action_attempts']


def test_transfer_retains_completed_destination_probe_and_partial_columns(monkeypatch):
    settings, m1 = prepared_response()
    m3 = science.acquire_root(settings, 31, 'M3', prerequisite_payloads={'M1': m1})
    original = native.action_at

    def fail_second_block(*args, **kwargs):
        action = original(*args, **kwargs)
        blocks = 0

        def selected(columns):
            nonlocal blocks
            blocks += 1
            try:
                if blocks == 2:
                    action(columns[:, :1])
                    raise FloatingPointError('failure after a completed destination column')
                return action(columns)
            finally:
                selected.real_hessian_evaluations = action.real_hessian_evaluations
                selected.real_hessian_attempts = action.real_hessian_attempts

        selected.real_hessian_evaluations = selected.real_hessian_attempts = 0
        return selected

    monkeypatch.setattr(native, 'action_at', fail_second_block)
    result = science.acquire_root(settings, 31, 'M4', prerequisite_payloads={'M3': m3})
    for case in result['cases']:
        assert case['status'] == 'UNAVAILABLE' and case['completed_destination_probes'] == 1
        assert case['transfer_modes']['residual_probe_reuse']['status'] == 'PARTIAL'
        assert case['new_native_actions'] == case['native_action_attempts'] == 3
    assert result['new_native_actions'] == result['work_accounting']['native_hessian_actions'] == 6
    assert result['work_accounting']['counts_are_lower_bounds']
    changed = deepcopy(m3)
    changed['cases'][0]['origin']['positions'][0] += 1
    with pytest.raises(ValueError, match='digest'):
        science.acquire_root(settings, 31, 'M4', prerequisite_payloads={'M3': changed})


def test_memory_retains_observation_prefix_and_failed_energy_attempt(monkeypatch):
    settings = tiny_settings()
    original = native.optimized_action_terms
    attempts = 0

    def fail_third_energy(*args, **kwargs):
        nonlocal attempts
        attempts += 1
        if attempts == 3:
            raise FloatingPointError('failure after an acquired force observation')
        return original(*args, **kwargs)

    monkeypatch.setattr(native, 'optimized_action_terms', fail_third_energy)
    result = science.acquire_root(settings, 31, 'M2')
    case = result['cases'][0]
    assert result['status'] == 'PARTIAL' and case['status'] == 'UNAVAILABLE'
    assert len(case['observables']) == len(case['energies']) == 2
    assert len(case['checkpoints']) == 1 and case['momentum_reset_controls'] == []
    assert case['incomplete_observation']['age_tick'] == 2
    assert case['incomplete_observation']['energy_available'] is False
    assert case['completed_scientific_prefix']['completed_record_ticks'] == 2
    counts = case['partial_native_accounting']
    assert counts['native_force_evaluations'] == counts['native_force_attempts'] == 6
    assert counts['native_energy_evaluations'] == 2 and counts['native_energy_attempts'] == 3
    assert result['work_accounting']['native_force_evaluations'] == 6
    assert result['work_accounting']['native_energy_evaluations'] == 2
    readout = science.analyse_root(settings, result)
    assert readout['cases'][0]['status'] == 'UNAVAILABLE'
    assert 'observations' not in readout['cases'][0]
    assert not {'observables', 'energies', 'checkpoints', 'momentum_reset_controls', 'incomplete_observation'} & set(readout['cases'][0])
    prefix = readout['cases'][0]['partial_native_record']
    assert prefix['observations'] == prefix['energies'] == 2 and prefix['checkpoints'] == 1
    assert prefix['incomplete_observation_present'] is True
    assert prefix['raw_prefix_owner'] == 'IMMUTABLE_ORIGINAL_ACQUISITION; NOT_REPLAYED_OR_RECOUNTED_HERE'


def test_memory_retains_completed_reset_and_inflight_branch_cost(monkeypatch):
    settings = tiny_settings()
    original = native.guard
    calls = 0

    def fail_second_reset(*args, **kwargs):
        nonlocal calls
        calls += 1
        # Sixteen main-path steps; six steps in the first three-path reset;
        # then two first-tick branches in the second reset.
        if calls == 24:
            raise FloatingPointError('failure after a completed reset-branch force')
        return original(*args, **kwargs)

    monkeypatch.setattr(native, 'guard', fail_second_reset)
    result = science.acquire_root(settings, 31, 'M2')
    case = result['cases'][0]
    assert case['status'] == 'UNAVAILABLE'
    assert len(case['observables']) == len(case['energies']) == 17
    assert len(case['checkpoints']) == 3
    controls = case['momentum_reset_controls']
    assert len(controls) == 2 and controls[0]['status'] == 'COMPLETED'
    assert controls[0]['full_state_clone_max_abs_difference'] == 0
    assert controls[1]['status'] == 'PARTIAL' and controls[1]['completed_ticks_by_path'] == [1, 0, 0]
    assert case['completed_scientific_prefix']['completed_reset_controls'] == 1
    counts = case['partial_native_accounting']
    assert counts['native_force_evaluations'] == counts['native_force_attempts'] == 47
    assert result['work_accounting']['native_force_evaluations'] == 47
    assert result['work_accounting']['native_energy_evaluations'] == 17
    assert result['work_accounting']['counts_are_lower_bounds'] is True
