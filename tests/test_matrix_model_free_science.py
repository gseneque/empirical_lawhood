# SPDX-License-Identifier: MPL-2.0
"""Small independent physical and complete-module controls, not a campaign."""
from copy import deepcopy
import math
import numpy as np
import pytest

from empirical_lawhood.domains.matrix.model_free import native, science


def tiny_settings():
    return science.normalise_settings({
        'native': {'history_ticks': 8, 'handoff_tick': 8, 'ramp_ticks': 4,
            'horizon_ticks': 4, 'observation_stride': 2, 'pulse_ticks': 1,
            'refresh_tick': 2, 'persistence_ticks': 2, 'survival_ticks': 2,
            'preparation_arms': ['baseline', 'joint-increasing'], 'actions': ['TRACE'],
            'coordinates': [{'id': 'nominal', 'temperature': '1', 'friction': '1', 'cross_coupling': '1'}]},
        'formation': {'fixed_tick': 8, 'trigger_deadline': 8, 'trailing_ticks': 2, 'observation_stride': 2},
        'memory': {'burnin_ticks': 0, 'record_ticks': 16, 'record_length_ladder': [16],
            'lags': [1, 2], 'checkpoint_ticks': [0, 8, 16], 'reset_horizon_ticks': 2,
            'observation_dimensions': [1, 2], 'history_orders': [1]},
        'response': {'handoffs': ['fixed'], 'action_budgets': [2], 'equal_ranks': [2],
            'methods': ['INPUT', 'JOINT'], 'refinements': [1, 2], 'refresh_schedules': [[], [2]],
            'dense_oracle_seed_modulus': 64},
        'population': {'frame_size': 4, 'audit_size': 2, 'mode': 'sparse'},
        'equilibrium': {'centers': ['-0.2', '-0.1', '0', '0.1', '0.2'], 'burnin_ticks': 0,
            'sample_ticks': 4, 'reference_ticks': 8, 'stride': 1, 'importance_samples': 8},
        'events': {'horizon_ticks': 4, 'replicas': 2},
    })


def test_checkpoint_exact_roundtrip_and_mutation_refusal():
    settings = tiny_settings()
    coord, state = native.target_state(settings['native'], settings['native']['coordinates'][0])
    saved = native.checkpoint(state)
    restored = native.restore(saved)
    np.testing.assert_array_equal(state.positions, restored.positions)
    damaged = deepcopy(saved)
    damaged['positions'][0] += 1
    with pytest.raises(ValueError, match='digest'):
        native.restore(damaged)


def test_strict_settings_preserve_memory_and_physical_clocks():
    with pytest.raises(ValueError, match='Unknown'):
        science.normalise_settings({'unannounced': True})
    with pytest.raises(ValueError, match='Probability'):
        science.normalise_settings({'formation': {'probability_gain_margin': '2'}})
    with pytest.raises(ValueError, match='acquisition ladder'):
        science.normalise_settings({'memory': {'record_ticks': 100}})


@pytest.mark.numerical(oracle='Exact native state plus causal prefix; no future access')
def test_formation_saves_actual_fixed_state_and_retains_nonentry():
    settings = tiny_settings()
    acquired = science.acquire_root(settings, 1, 'M1')
    assert len(acquired['cases']) == 2
    for case in acquired['cases']:
        assert case['status'] == 'COMPLETED'
        fixed = case['checkpoints']['fixed']
        assert fixed['tick'] == 8
        assert native.restore(fixed['state']).step_index == 8
    readout = science.analyse_root(settings, acquired)
    result = science.synthesise_roots(settings, [readout])
    assert result['modules']['M1']['assigned_roots'] == 1
    assert result['modules']['M1']['assigned_cases'] == 2


@pytest.mark.numerical(oracle='Native six-matrix BAOAB finite-age stream with exact declared anchor counts')
def test_memory_native_observation_and_analysis():
    settings = tiny_settings()
    settings['memory']['protocol_age_ticks'] = [8]
    acquired = science.acquire_root(settings, 1, 'M2')
    case = acquired['cases'][0]
    assert len(case['observables']) == 17
    assert case['stationarity_established'] is False
    analysis = science.analyse_root(settings, acquired)
    for obs in analysis['cases'][0]['observations']:
        assert obs['counts']['lags']['1']['attempted_anchors'] == (1 if '-age-' in obs['observation_id'] else 15)
    assert all(control['full_state_clone_max_abs_difference'] == 0 for control in case['momentum_reset_controls'])
    output = science.synthesise_roots(settings, [analysis])
    assert output['modules']['M2']['memory']


@pytest.mark.numerical(oracle='Actual shared-noise finite native chord and independent h/2 BAOAB view')
def test_response_composition_and_sparse_audit_are_native():
    settings = tiny_settings()
    # A loose declared allowance supplies a positive exact-identity reuse
    # control; its numerical value remains the original native residual bound.
    settings['response']['certificate_tolerance'] = '1000000'
    m1 = science.acquire_root(settings, 1, 'M1')
    m3 = science.acquire_root(settings, 1, 'M3', prerequisite_payloads={'M1': m1})
    assert all(case['status'] == 'COMPLETED' for case in m3['cases'])
    for case in m3['cases']:
        assert case['futures'][0]['force_evaluations'] > 0
        assert case['certificates'][0]['action_count'] <= 2
    analysis = science.analyse_root(settings, m3)
    assert analysis['cases'][0]['numerical_difference'] is not None
    m4 = science.acquire_root(settings, 1, 'M4', prerequisite_payloads={'M3': m3})
    assert m4['new_native_actions'] > 0
    for source, reused in zip(m3['cases'], m4['cases'], strict=True):
        identity = reused['transfer_modes']['zero_new_action_reuse']
        assert identity['operator_identity_verified'] is True
        assert identity['new_native_column_actions'] == 0
        assert [value['status'] for value in identity['suppliers']] == [value['status'] for value in source['certificates']]
        assert identity['status'] == ('CERTIFIED' if all(value['status'] == 'CERTIFIED' for value in source['certificates']) else 'UNRESOLVED')
        assert identity['status'] == 'CERTIFIED'
    sampling = {'audit_selected': True, 'inclusion_probability': '0.5', 'frame_id': 'frame-test', 'frame_size': 4, 'audit_size': 2}
    m5 = science.acquire_root(settings, 1, 'M5', prerequisite_payloads={'M1': m1}, sampling=sampling)
    assert all(case['native_calls_acquired'] == 2 for case in m5['cases'])
    unselected = science.acquire_root(settings, 1, 'M5', prerequisite_payloads={'M1': m1}, sampling={**sampling, 'audit_selected': False})
    assert all(case['native_calls_acquired'] == 0 and case['native_value'] is None for case in unselected['cases'])
    assert m5['auxiliary_freeze_sha256'] == unselected['auxiliary_freeze_sha256']
    with pytest.raises(ValueError, match='no hidden reacquisition'):
        science.acquire_root(settings, 1, 'M3')


@pytest.mark.numerical(oracle='Native complete potential restrained BAOAB; all finite-age samples retained')
def test_equilibrium_and_events_preserve_scope():
    settings = tiny_settings()
    acquired = science.acquire_root(settings, 1, 'M6')
    case = acquired['cases'][0]
    assert case['status'] == 'COMPLETED'
    assert len(case['center_records']) == 5
    assert len(case['importance']) == 5
    assert case['finite_step_measure_bias_bound'] is None
    assert case['canonical_preparation_qualified'] is False
    readout = science.analyse_root(settings, acquired)
    assert 'samples' not in readout['cases'][0]['center_records'][0]
    event = science.acquire_root(settings, 1, 'M7')
    assert len(event['cases'][0]['events']) == 2
    result = science.synthesise_roots(settings, [science.analyse_root(settings, event)])
    assert result['modules']['M7']['first_passage']


@pytest.mark.numerical(oracle='Constant mean force integrates exactly to force times center span')
def test_equilibrium_synthesis_integrates_mean_force_with_physical_sign():
    settings = tiny_settings()
    readout = science.analyse_root(settings, science.acquire_root(settings, 1, 'M6'))
    for row in readout['cases'][0]['center_records']:
        for name in ('mean', 'controlled_mean', 'reference_mean'):
            row[name] = float(row['center']) + 0.3
    result = science.synthesise_roots(settings, [readout])['modules']['M6']['equilibrium'][0]
    expected = -float(settings['equilibrium']['stiffness']) * 0.3 * 0.4
    for name in ('finite_grid', 'coarse_grid', 'fixed_control', 'longer_shared_path_reference'):
        assert result[name]['mean'] == pytest.approx(expected)


@pytest.mark.numerical(oracle='Equal finite sums of sinusoidal ramp deviations over a complete cycle')
def test_matched_exposure_is_actual_schedule_not_relabeling():
    settings = tiny_settings()
    settings['formation']['exposure_matched_recipes'] = ['x-first-exposure-matched', 'y-first-exposure-matched']
    acquired = science.acquire_root(settings, 1, 'M1')
    rows = {case['recipe']: case for case in acquired['cases']}
    for name in settings['formation']['exposure_matched_recipes']:
        np.testing.assert_allclose(rows[name]['coupling_exposure'], rows['joint-increasing']['coupling_exposure'], rtol=1e-14, atol=1e-15)
        assert rows[name]['initial_presence'] is False
    assert acquired['assigned_case_count'] == 4


def test_unsampled_whole_root_does_not_contact_native_future(monkeypatch):
    settings = tiny_settings()
    m1 = science.acquire_root(settings, 1, 'M1')
    def forbidden(*args, **kwargs):
        raise AssertionError('unsampled root contacted native future')
    monkeypatch.setattr(native, 'paired_response', forbidden)
    sampling = {'audit_selected': False, 'inclusion_probability': '0.5', 'frame_id': 'frame-test', 'frame_size': 4, 'audit_size': 2}
    acquired = science.acquire_root(settings, 1, 'M5', prerequisite_payloads={'M1': m1}, sampling=sampling)
    assert acquired['native_audit_root_omitted'] is True


@pytest.mark.parametrize('failed_refinement', (1, 2))
def test_failed_population_audit_counts_only_attempted_and_completed_futures(monkeypatch, failed_refinement):
    settings = tiny_settings()
    m1 = science.acquire_root(settings, 1, 'M1')
    original, calls = native.paired_response, []

    def fail_selected_view(*args, **kwargs):
        calls.append(kwargs['refinement'])
        if kwargs['refinement'] == failed_refinement:
            raise FloatingPointError('declared audit failure')
        return original(*args, **kwargs)

    monkeypatch.setattr(native, 'paired_response', fail_selected_view)
    sampling = {'audit_selected': True, 'inclusion_probability': '0.5',
        'frame_id': 'frame-test', 'frame_size': 4, 'audit_size': 2}
    acquired = science.acquire_root(settings, 1, 'M5', prerequisite_payloads={'M1': m1}, sampling=sampling)
    assert calls == list(range(1, failed_refinement + 1)) * 2
    for case in acquired['cases']:
        assert case['status'] == 'UNAVAILABLE' and case['native_value'] is None
        assert case['native_calls_attempted'] == failed_refinement
        assert case['native_calls_acquired'] == failed_refinement - 1
        assert case['native_force_evaluations'] == (15 if failed_refinement == 2 else 0)
        assert case['tangent_hessian_actions'] == (8 if failed_refinement == 2 else 0)
    assert acquired['work_accounting']['counts_are_lower_bounds'] is True


@pytest.mark.parametrize('error_type', (FloatingPointError, OverflowError))
def test_event_observed_before_later_failure_retains_event_and_incomplete_work(monkeypatch, error_type):
    from dataclasses import replace

    settings = tiny_settings()
    c, config = settings['native'], settings['events']
    forces, _ = native.physical_chart(c, config['receiver_seed'])
    displacement = native.native_position_lift(2 * float(config['upper_target']) * forces[:, 0])

    def enter_then_fail(state, *args, **kwargs):
        if state.step_index:
            raise error_type('failure after observed event')
        return replace(state, positions=state.positions + displacement, step_index=1)

    monkeypatch.setattr(native, 'step', enter_then_fail)
    acquired = science.acquire_root(settings, 1, 'M7')
    case, = acquired['cases']
    assert case['status'] == 'COMPLETED'
    assert len(case['events']) == config['replicas']
    for event in case['events']:
        assert event['status'] == 'event' and event['event'] == 'target'
        assert event['event_time'] == event['observed_until'] == float(c['timestep'])
        assert event['failure'] == 'failure after observed event'
    assert acquired['work_accounting']['counts_are_lower_bounds'] is True


@pytest.mark.numerical(oracle='Complete authored four-root SRS frame; whole paired recipes share one inclusion indicator')
def test_whole_root_population_keeps_census_and_paired_contrast():
    settings = tiny_settings()
    readouts = []
    for seed in (1, 2, 3, 4):
        m1 = science.acquire_root(settings, seed, 'M1')
        sampling = {'audit_selected': seed in (1, 3), 'inclusion_probability': '0.5', 'frame_id': 'frame-test', 'frame_size': 4, 'audit_size': 2}
        acquired = science.acquire_root(settings, seed, 'M5', prerequisite_payloads={'M1': m1}, sampling=sampling)
        readouts.append(science.analyse_root(settings, acquired))
    outcome = science.synthesise_roots(settings, readouts)['modules']['M5']
    assert outcome['unit'] == 'WHOLE_PAIRED_INDEPENDENT_ROOT'
    assert all(row['actual_native_root_audits_omitted'] == 2 for row in outcome['finite_population'])
    assert outcome['paired_finite_population_contrasts']
    assert science.synthesise_roots(settings, readouts[:-1])['modules']['M5']['finite_population']['status'] == 'UNRESOLVED'


def test_missing_native_root_not_selected_out_of_memory_equilibrium_or_events():
    settings = tiny_settings()
    for module in ('M2', 'M6', 'M7'):
        acquired = science.acquire_root(settings, 1, module)
        acquired['cases'][0] = {**acquired['cases'][0], 'status': 'UNAVAILABLE', 'reason': 'CONTROL_FAILURE'}
        acquired['status'] = 'PARTIAL'
        readout = science.analyse_root(settings, acquired)
        outcome = science.synthesise_roots(settings, [readout])['modules'][module]
        assert outcome['unavailable_cases'] == 1
        if module == 'M2':
            assert outcome['memory'][0]['assessment']['status'] == 'UNRESOLVED'
        elif module == 'M6':
            assert outcome['equilibrium'][0]['status'] == 'UNRESOLVED'
        else:
            assert outcome['first_passage'][0]['assessment']['unresolved_weight_fraction'] > 0


def _declared_response_readout(settings, seed, *, unavailable=False):
    """Known root outcomes for independent reporting-equation controls."""
    cases = []
    for recipe in settings['native']['preparation_arms']:
        case = {'coordinate': settings['native']['coordinates'][0], 'recipe': recipe,
            'handoff': 'fixed', 'status': 'UNAVAILABLE' if unavailable else 'COMPLETED'}
        if not unavailable:
            case.update(handoff_present=True, survival=[{'present': True}], native_endpoint=[[0.] * 48],
                models=[{'method': method, 'requested_rank': 2, 'schedule_ticks': [],
                    'adequate': recipe != 'baseline', 'maximum_receiver_error': 1. if recipe == 'baseline' else 0.,
                    'predicted_endpoint': [[0.] * 48]} for method in settings['response']['methods']],
                selectors=[{'method': method, 'rank': 2, 'selected_suffix_score': 0.,
                    'withheld_suffix_scores': {'origin-only': float(seed % 2), '2': float(1 - seed % 2)}}
                    for method in settings['response']['methods']])
        cases.append(case)
    return {'schema': 'matrix-model-free-analysis.v1', 'module': 'M3', 'seed': seed,
        'settings_sha256': science.settings_fingerprint(settings), 'status': 'PARTIAL' if unavailable else 'COMPLETED',
        'cases': cases, 'assigned_case_count': len(cases), 'acquisition_seconds': 0.,
        'work_accounting': {'native_force_evaluations': 0, 'native_hessian_actions': 0,
            'native_energy_evaluations': 0, 'wall_seconds': 0., 'counts_are_lower_bounds': unavailable}}


def test_response_gain_interval_uses_paired_range_and_entire_declared_family():
    settings = tiny_settings()
    roots = [_declared_response_readout(settings, seed) for seed in range(100)]
    result = science.synthesise_roots(settings, roots)['modules']['M3']
    family = 4  # one coordinate/handoff/rank, two recipes, two methods
    module_alpha = float(settings['alpha']) * float(settings['inference']['module_alpha_weights']['M3'])
    expected_halfwidth = math.sqrt(2 * math.log(2 * family / module_alpha) / 100)
    for row in result['preparation_service']:
        expected_mean = 0. if row['recipe'] == 'baseline' else 1.
        assert row['net_adequacy_probability_gain'] == expected_mean
        assert row['gain_interval'] == pytest.approx([max(-1., expected_mean - expected_halfwidth), min(1., expected_mean + expected_halfwidth)])
        assert row['gain_uncertainty']['family_size'] == family
        assert row['gain_uncertainty']['assigned_roots'] == 100


def test_response_selectors_keep_entirely_missing_groups_and_refuse_partial_wins():
    settings = tiny_settings()
    missing = _declared_response_readout(settings, 3, unavailable=True)
    absent = science.synthesise_roots(settings, [missing])['modules']['M3']['selector_comparisons']
    assert len(absent) == 4
    assert all(row['status'] == 'UNRESOLVED' and row['missing_roots'] == 1 for row in absent)
    roots = [_declared_response_readout(settings, 1), _declared_response_readout(settings, 2), missing]
    partial = science.synthesise_roots(settings, roots)['modules']['M3']['selector_comparisons']
    assert all(row['mean_selected_suffix_error'] < row['best_fixed_exposed_mean'] for row in partial)
    assert all(row['status'] == 'UNRESOLVED' and row['evaluable_roots'] == 2
        and row['assigned_roots'] == 3 and not row['selected_beats_every_fixed_mean'] for row in partial)


def test_memory_segments_are_frozen_and_retained_analysis_is_exact():
    settings = tiny_settings()
    settings['memory']['protocol_age_ticks'] = [8]
    acquired = science.acquire_root(settings, 7, 'M2')
    direct = science.analyse_root(settings, acquired)
    retained = science.analyse_root(settings, acquired, retained_settings=settings)
    # Timing is not part of the scientific per-case target.
    assert direct['cases'] == retained['cases']
    segments = direct['cases'][0]['stationarity']
    assert segments['segment_boundaries_samples'] == [0, 6, 12, 17]
    assert segments['transition_policy'] == 'within_segment'
    counts = segments['segment_observations'][0]['counts']
    assert [row['sample_count'] for row in counts['segments']] == [6, 6, 5]
    assert [row['transitions']['1']['boundary_crossing_pairs_excluded'] for row in counts['segments']] == [0, 1, 1]
    output = science.synthesise_roots(settings, [direct])['modules']['M2']
    assert len(output['segment_drift']) == 2
    assert output['memory_error_allocation']['history_fraction'] == .5
    for row in output['segment_drift']:
        assert row['assessment']['independent_roots'] == 1
        assert row['assessment']['stationarity_established'] is False
    with pytest.raises(ValueError, match='segment'):
        science.normalise_settings({**settings, 'memory': {**settings['memory'], 'segment_boundaries_samples': [0, 5, 18]}})


def test_retained_memory_segment_changes_are_exposed_and_not_new_acquisition():
    from empirical_lawhood.domains.matrix.model_free.retained_analysis import validate_reanalysis_settings

    original = tiny_settings()
    changed = deepcopy(original)
    changed['memory']['segment_boundaries_samples'] = [0, 5, 10, 17]
    assert validate_reanalysis_settings(original, changed, {'M2'}) is True
    acquired = science.acquire_root(original, 8, 'M2')
    analysis = science.analyse_root(changed, acquired, retained_settings=original)
    result = science.synthesise_roots(changed, [analysis])['modules']['M2']
    assert result['analysis_menu_scope'] == 'EXPOSED_POST_HOC'
    assert all(row['assessment']['status'] == 'EXPLORATORY_POST_HOC' for row in result['segment_drift'])


@pytest.mark.numerical(oracle='Actual four-root reveal-all census contains every fine native endpoint while a fixed SRS subaudit is held unchanged')
def test_reveal_all_benchmark_reports_direct_baseline_and_counterfactual_savings():
    settings = tiny_settings()
    settings['population']['mode'] = 'reveal_all'
    readouts = []
    for seed in (1, 2, 3, 4):
        m1 = science.acquire_root(settings, seed, 'M1')
        sampling = {'audit_selected': seed in (1, 3), 'inclusion_probability': '0.5',
            'frame_id': 'reveal-all-frame', 'frame_size': 4, 'audit_size': 2}
        acquired = science.acquire_root(settings, seed, 'M5', prerequisite_payloads={'M1': m1}, sampling=sampling)
        assert all(case['native_calls_attempted'] == case['native_calls_acquired'] == 2 for case in acquired['cases'])
        assert acquired['native_audit_root_omitted'] is False
        readouts.append(science.analyse_root(settings, acquired))
    result = science.synthesise_roots(settings, readouts)['modules']['M5']
    assert result['acquisition_mode'] == 'reveal_all'
    for row in result['finite_population']:
        comparison = row['estimator_comparison']
        assert comparison['full_frame_benchmark']['status'] == 'ENUMERATED'
        assert comparison['full_frame_benchmark']['actual_native_calls_omitted'] == 0
        assert comparison['full_frame_benchmark']['counterfactual_calls_omitted'] == 2
        assert row['actual_native_root_audits_omitted'] == 0
        assert row['native_future_calls_attempted'] == 8
        assert comparison['full_frame_benchmark']['full_frame_mean'] == pytest.approx(row['full_frame_mean'])
    assert result['paired_finite_population_contrasts'][0]['estimator_comparison']['full_frame_benchmark']['status'] == 'ENUMERATED'


@pytest.mark.numerical(oracle='Identical M1 checkpoint states under common root/replica Brownian streams produce identical M7 paths')
def test_native_entry_histories_pair_before_root_uncertainty_and_keep_nonentry():
    settings = tiny_settings()
    settings['events']['require_admitted_entry'] = False
    m1 = science.acquire_root(settings, 1, 'M1')
    m1['cases'][1]['checkpoints']['fixed']['state'] = deepcopy(m1['cases'][0]['checkpoints']['fixed']['state'])
    acquired = science.acquire_root(settings, 1, 'M7', prerequisite_payloads={'M1': m1})
    left, right = [case['events'] for case in acquired['cases']]
    for first, second in zip(left, right, strict=True):
        for field in ('event', 'event_time', 'observed_until', 'status'):
            assert first[field] == second[field]
    result = science.synthesise_roots(settings, [science.analyse_root(settings, acquired)])['modules']['M7']
    assert len(result['paired_history_contrasts']) == 2
    for row in result['paired_history_contrasts']:
        assert row['assessment']['independent_roots'] == 1
        assert row['assessment']['assigned_paired_paths'] == 2
        assert row['assessment']['commitment']['completion_bounds'] == [0., 0.]
        assert row['assessment']['restricted_mean']['completion_bounds'] == [0., 0.]
    acquired['cases'][1] = {**acquired['cases'][1], 'status': 'UNAVAILABLE', 'reason': 'DECLARED_NONENTRY'}
    acquired['status'] = 'PARTIAL'
    result = science.synthesise_roots(settings, [science.analyse_root(settings, acquired)])['modules']['M7']
    assert all(row['assessment']['status'] == 'UNRESOLVED' for row in result['paired_history_contrasts'])
    assert all(row['assessment']['assigned_paired_paths'] == 2 for row in result['paired_history_contrasts'])


@pytest.mark.parametrize('mutation', ('missing-replica', 'wrong-root', 'changed-weight', 'off-grid-time'))
def test_event_analysis_rejects_changed_paired_path_census(mutation):
    settings = tiny_settings()
    acquired = science.acquire_root(settings, 1, 'M7')
    events = acquired['cases'][0]['events']
    if mutation == 'missing-replica':
        events.pop()
    elif mutation == 'wrong-root':
        events[0]['root_id'] = 'different-root'
    elif mutation == 'off-grid-time':
        events[0]['observed_until'] = .5 * float(settings['native']['timestep'])
    else:
        events[0]['weight'] *= 2
    message = 'native tick grid' if mutation == 'off-grid-time' else 'paired replica/root/weight census'
    with pytest.raises(ValueError, match=message):
        science.analyse_root(settings, acquired)


def test_failed_auxiliary_freezes_zero_before_preserving_the_native_audit(monkeypatch):
    settings = tiny_settings()
    m1 = science.acquire_root(settings, 1, 'M1')
    original, calls = native.paired_response, []

    def failed_auxiliary(*args, **kwargs):
        assert not calls, 'all auxiliaries must freeze before any native future'
        raise np.linalg.LinAlgError('declared auxiliary failure')

    def recorded_future(*args, **kwargs):
        calls.append(kwargs['refinement'])
        return original(*args, **kwargs)

    monkeypatch.setattr(science, '_reduced_propagation', failed_auxiliary)
    monkeypatch.setattr(native, 'paired_response', recorded_future)
    sampling = {'audit_selected': True, 'inclusion_probability': '0.5',
        'frame_id': 'frame-test', 'frame_size': 4, 'audit_size': 2}
    acquired = science.acquire_root(settings, 1, 'M5', prerequisite_payloads={'M1': m1}, sampling=sampling)
    assert calls == [1, 2, 1, 2]
    for case in acquired['cases']:
        assert case['frame_member_defined'] is True
        assert case['auxiliary'] == 0.
        assert case['auxiliary_status'] == 'NUMERICAL_FAILURE_FROZEN_ZERO'
        assert case['auxiliary_hessian_actions'] > 0
        assert case['native_value'] is not None
        assert case['native_calls_acquired'] == 2
        assert case['attempted_work_count_is_lower_bound'] is True


@pytest.mark.numerical(oracle='Three independent tiny native restrained roots with two physical temperature coordinates retain all suppliers and paired moments')
def test_equilibrium_synthesis_uses_importance_and_independent_root_variance_suppliers():
    settings = tiny_settings()
    settings['native']['coordinates'].append({'id': 'warm', 'temperature': '2', 'friction': '1', 'cross_coupling': '1'})
    readouts = [science.analyse_root(settings, science.acquire_root(settings, seed, 'M6')) for seed in (1, 2, 3)]
    result = science.synthesise_roots(settings, readouts)['modules']['M6']
    assert result['family_allocation']['families'] == 13
    assert result['family_allocation']['alpha_per_family'] * 13 == pytest.approx(result['inference_allocation']['module_alpha'])
    for row in result['equilibrium']:
        importance = row['native_residual_importance']
        assert importance['independent_roots'] == 3
        assert len(importance['root_targets']) == 3
        assert importance['exact_free_energy_certified'] is False
        assert importance['minimum_effective_sample_size'] > 0
        assert importance['maximum_normalized_weight'] <= 1
        assert np.asarray(row['complete_estimator_mean_covariance']).shape == (5, 5)
    paired, = result['paired_equilibrium']
    assert paired['signed_paired_importance_endpoint']['independent_roots'] == 3
    bridge = paired['independent_root_variance_transport']
    assert bridge['moment_estimator'] == 'INDEPENDENT_ROOT_CROSS_PRODUCT_U_STATISTIC'
    assert len(bridge['jackknife_leave_one_root_estimates']) == 3
    assert bridge['canonical_measure_qualified'] is False
    assert paired['anchored_variance_transport']['finite_record_correlation_bias_bound'] is None


@pytest.mark.parametrize('failed_phase', ['restrained_force', 'importance_energy'])
def test_equilibrium_numerical_failure_preserves_work_and_raw_prefix_without_qualification(monkeypatch, failed_phase):
    settings = tiny_settings()
    name = 'analytic_gradient_terms' if failed_phase == 'restrained_force' else 'optimized_action_terms'
    original = getattr(native, name)
    attempts = 0
    stop = 4 if failed_phase == 'restrained_force' else 2

    def injected_failure(*args, **kwargs):
        nonlocal attempts
        attempts += 1
        if attempts == stop:
            raise FloatingPointError('injected M6 native failure')
        return original(*args, **kwargs)

    monkeypatch.setattr(native, name, injected_failure)
    acquired = science.acquire_root(settings, 1, 'M6')
    case, = acquired['cases']
    assert acquired['status'] == 'PARTIAL'
    assert case['status'] == 'UNAVAILABLE'
    assert case['canonical_preparation_qualified'] is False
    costs = case['partial_native_accounting']
    if failed_phase == 'restrained_force':
        assert costs['native_force_evaluations_attempted'] == 4
        assert costs['native_force_evaluations'] == 3
        assert case['incomplete_center_record']['completed_ticks'] == 1
        assert len(case['incomplete_center_record']['samples']) == 1
        assert case['center_records'] == []
    else:
        assert len(case['center_records']) == len(settings['equilibrium']['centers'])
        assert costs['native_force_evaluations'] == sum(row['native_force_evaluations'] for row in case['center_records'])
        assert costs['native_energy_evaluations_attempted'] == 2
        assert costs['native_energy_evaluations'] == 1
        assert len(case['completed_importance_native_samples']) == 1
        assert case['importance'] == []
    for key in ('native_force_evaluations', 'native_energy_evaluations'):
        assert acquired['work_accounting'][key] == costs[key]
    readout = science.analyse_root(settings, acquired)
    compact, = readout['cases']
    assert compact['status'] == 'UNAVAILABLE'
    assert 'center_records' not in compact
    assert 'completed_importance_native_samples' not in compact
    result = science.synthesise_roots(settings, [readout])['modules']['M6']
    assert result['equilibrium'][0]['status'] == 'UNRESOLVED'
    assert result['equilibrium'][0]['missing_roots'] == [1]
