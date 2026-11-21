# SPDX-License-Identifier: MPL-2.0
"""Native and independent mathematical controls for the consolidated series."""
from copy import deepcopy

import numpy as np
import pytest

from empirical_lawhood.domains.matrix.classical_series import science as s


def small_config(**updates):
    values=dict(ramp_ticks=4,handoff_tick=4,history_ticks=8,horizon_ticks=4,pulse_ticks=1,
        refresh_tick=2,observation_stride=2,persistence_ticks=2,survival_ticks=2,panels=1,
        actions=['GENERIC','TRACE'],calibration_alpha='0.5',numerical_tolerance='1')
    values.update(updates)
    return s.normalise_config(values)


@pytest.fixture(scope='module')
def tiny_acquisition():
    c=small_config()
    return c,s.acquire_native_root(c,7)


@pytest.mark.conformance
def test_scientific_defaults_preserve_full_physical_model_and_original_decimals():
    c=s.normalise_config({})
    assert c['target_x']=='0.6666666666666666666666666667'
    assert c['target_y']=='7.333333333333333333333333334'
    assert (c['handoff_tick'],c['history_ticks'],c['occurrence_deadline'],c['horizon_ticks'])==(256,1152,1024,128)
    for changes in ({'bogus':1},{'timestep':.001},{'actions':['TRACE','TRACE']},
                    {'joint_rank':12},{'occurrence_deadline':1100}):
        with pytest.raises((ValueError,TypeError)):
            s.normalise_config(changes)


@pytest.mark.conformance
def test_native_complete_census_and_before_future_seal(tiny_acquisition):
    c,a=tiny_acquisition
    assert a['status']=='COMPLETED' and a['independent_units']==1
    case=a['cases'][0]
    assert len(case['origin_states'][0])==192
    assert np.asarray(case['origin_hessians']).shape==(2,96,96)
    assert np.asarray(case['panels'][0]['native_response']).shape==(2,2,5,48)
    assert case['pre_response_commitment']['cutoff_tick']==4
    assert case['pre_response_commitment']['causal_prefix_sha256']==case['causal_prefix_sha256']
    assert case['io48'][0]['status'] in ('COMPLETED','UNAVAILABLE')
    assert s.validate_acquisition(c,a)==c


@pytest.mark.conformance
def test_acquisition_phase_selection_changes_reanalysis_but_not_native_identity(tiny_acquisition):
    c,a=tiny_acquisition
    later=dict(c,phases=['e1'])
    assert s.acquisition_config_fingerprint(c)==s.acquisition_config_fingerprint(later)
    read=s.analyse_native_root(later,a)
    assert set(read['stages'])=={'e1'}
    assert read['actual_native_work_avoided']==0
    changed=dict(c,amplitude='0.02')
    with pytest.raises(ValueError,match='authored scientific'):
        s.analyse_native_root(changed,a)


@pytest.mark.conformance
def test_transfer_entry_requires_both_distinct_authored_temperatures(tiny_acquisition, monkeypatch):
    """Isolate entry accounting; forecast rows are disclosed contract fixtures."""
    c,a=tiny_acquisition
    selected=dict(c,phases=['e6'])
    def forecast(temperatures):
        return {'coordinates':[{'coordinate':{'id':str(i),'temperature':t,
            'friction':'1','cross_coupling':'1'}} for i,t in enumerate(temperatures)]}
    monkeypatch.setattr(s,'_frozen_forecast',lambda *args:forecast(['1.125','1.125']))
    result=s.analyse_native_root(selected,a)['stages']['e6']
    assert result['status']=='NOT_ESTABLISHED'
    assert result['reason']=='REQUIRES_BOTH_T1.125_AND_T3.25_AND_FROZEN_CALIBRATION'
    monkeypatch.setattr(s,'_frozen_forecast',lambda *args:forecast(['1.125','3.25']))
    assert s.analyse_native_root(selected,a)['stages']['e6']['status']=='EMPIRICAL_FROZEN_TRANSFER'


@pytest.mark.conformance
def test_changed_original_operands_or_commitments_refuse(tiny_acquisition):
    c,a=tiny_acquisition
    for changed in ('force','prefix','commitment','census'):
        altered=deepcopy(a)
        if changed=='force':
            altered['forces'][0][0]+=.001
        elif changed=='prefix':
            altered['cases'][0]['origin_hessians'][0][0][0]+=.001
        elif changed=='commitment':
            altered['cases'][0]['pre_response_commitment']['seed']=8
        else:
            altered['cases']=[]
        with pytest.raises(ValueError):
            s.analyse_native_root(c,altered)


@pytest.mark.numerical(oracle='A unit normalized error in every one of 24 receiver components has Euclidean block norm sqrt(24), not unit RMS')
def test_original_block_l2_scoring_is_preserved():
    scales=np.asarray([[2.,3.]])
    error=np.zeros((1,2,48)); error[0,1,:24]=2.; error[0,1,24:]=3.
    score,_=s._score(error,scales)
    assert score['maximum']==pytest.approx(np.sqrt(24.))
    assert score['curve_rms']==pytest.approx(1.)


@pytest.mark.conformance
def test_missing_structural_feature_remains_missing_and_exact_zero_is_preserved(tiny_acquisition):
    c,a=tiny_acquisition
    case=deepcopy(a['cases'][0]); case['handoff_tick']=c['handoff_tick']
    at=next(x for x in case['factor_observations'] if x['tick']==c['handoff_tick'])['primary']['Y']
    at['associative_leakage']=0.; at['lie_leakage']=0.
    assert s._features(case)['structure'][5:7]==[0.,0.]
    at['associative_leakage']=None
    assert s._features(case)['structure'] is None
    assert s._features(case)['baseline'] is not None


@pytest.mark.numerical(oracle='Known exact Gaussian quartic partition-function contrast and harmonic cos(t)/cos(2t) memory functions')
def test_both_derivations_are_exercised_without_equilibrium_claim(tiny_acquisition):
    c,a=tiny_acquisition
    report=s.analyse_native_root(dict(c,phases=['derivations']),a)['stages']['derivations']
    assert report['resolvent_enclosure_contains_oracle']
    assert report['finite_tail_dense_oracle_error']<1e-10
    assert report['finite_operator_update_error']<1e-10
    static=report['static_dynamic_separation']
    assert static['static_equal']
    assert static['memory_at_one_first']==pytest.approx(np.cos(1.))
    assert static['memory_at_one_second']==pytest.approx(np.cos(2.))
    nonlinear=report['retained_gaussian_elimination']
    assert nonlinear['quartic_controls'][-1]['endpoint']==pytest.approx(.0195967797645805,abs=1e-12)
    assert nonlinear['quartic_controls'][-1]['finite_grid']==pytest.approx(.0196015100174638,abs=1e-12)
    assert nonlinear['actual_hidden_coordinate_elimination']['compliance_schur_error']<1e-14
    assert not nonlinear['native_matrix_equilibrium_or_free_energy_claim']
    assert not report['canonical_mean_bridge']['canonical_native_matrix_claim']
    assert report['actual_native_work_avoided']==0


@pytest.mark.conformance
def test_frozen_training_calibration_confirmation_and_small_cal_vacuity(tiny_acquisition):
    c,a=tiny_acquisition
    cal=s.acquire_native_root(c,8)
    summary=s.summarise_native_root(c,a)
    frozen=s.calibrate_native_roots(dict(c,training_seeds=[7],calibration_seeds=[8]),
        {'root7':summary,'root8':s.summarise_native_root(c,cal)})
    assert frozen['training_seeds']==[7] and frozen['calibration_seeds']==[8]
    assert frozen['models']['baseline']['calibration_assigned']==1
    with pytest.raises(ValueError,match='separation'):
        s.acquire_native_root(c,7,calibration=frozen)
    fresh=s.acquire_native_root(c,9,calibration=frozen)
    report=s.analyse_native_root(c,fresh,calibration=frozen)
    assert report['stages']['e3']['status']=='FROZEN_RULE_EVALUATED'
    assert fresh['freeze_sha256']==frozen['freeze_sha256']
    assert fresh['cases'][0]['pre_response_commitment']['forecasts']
    with pytest.raises(ValueError,match='did not consume'):
        s.analyse_native_root(c,s.acquire_native_root(c,10),calibration=frozen)
    # Under alpha .05 and one CAL root, ceil(2*.95)>1 is vacuous, not a borrowed guarantee.
    c2=dict(c,calibration_alpha='0.05')
    missing=s.calibrate_native_roots(dict(c2,training_seeds=[1],calibration_seeds=[2]),{})
    assert missing['models']['baseline']['status']=='FIT_UNAVAILABLE'
    assert missing['nominee'] is None


@pytest.mark.conformance
def test_unentered_original_successors_remain_explicit_without_supplier(tiny_acquisition):
    c,a=tiny_acquisition
    report=s.analyse_native_root(c,a)
    assert report['stages']['e5']['status']=='NOT_ENTERED'
    assert report['stages']['e6']['status']=='NOT_ESTABLISHED'
    assert report['stages']['e4']['historical_e4_qualification']=='UNCHANGED_NOT_ESTABLISHED'
    assert report['stages']['sci02']['native_force_calls_avoided']==0


@pytest.mark.numerical(oracle='Signed error identity D=S-A and discrete variation-of-constants decomposition on independently acquired two-endpoint native operands')
def test_matched_endpoint_contrasts_keep_nested_cells_and_exact_accounting():
    c=small_config(phases=['e4','sci01'],coordinates=[
        {'id':'low','temperature':'1','friction':'1','cross_coupling':'0.5'},
        {'id':'high','temperature':'1','friction':'1','cross_coupling':'2'}])
    report=s.analyse_native_root(c,s.acquire_native_root(c,11))
    cells=report['stages']['e4']['cells']
    assert cells and report['census']['independent_units']==1
    assert all(row['identity_residual']<1e-10 for row in cells if 'identity_residual' in row)
    terms=report['stages']['sci01']['inherited_generated']
    assert terms and max(row['reconstruction_error'] for row in terms)<1e-12


@pytest.mark.conformance
def test_native_commitment_precedes_each_assay_future(monkeypatch):
    calls=[]
    commit=s._precommit; response=s._response_acquisition
    def first(*args,**kwargs):
        calls.append('commit'); return commit(*args,**kwargs)
    def second(*args,**kwargs):
        assert calls[-1]=='commit'
        calls.append('native'); return response(*args,**kwargs)
    monkeypatch.setattr(s,'_precommit',first)
    monkeypatch.setattr(s,'_response_acquisition',second)
    s.acquire_native_root(small_config(),12)
    assert calls==['commit','native']


@pytest.mark.conformance
def test_native_force_call_accounting_matches_actual_cache_misses(monkeypatch):
    from empirical_lawhood.domains.matrix.six_matrix_response import simulation
    original=simulation.analytic_gradient_terms
    calls=[]
    def observed(*args,**kwargs):
        calls.append(1)
        return original(*args,**kwargs)
    monkeypatch.setattr(simulation,'analytic_gradient_terms',observed)
    acquired=s.acquire_native_root(small_config(phases=['e1']),13)
    assert sum(case['native_force_evaluations'] for case in acquired['cases'])==len(calls)


@pytest.mark.conformance
def test_capstone_forecasts_precede_preparation_noise_and_use_distinct_connection(monkeypatch):
    from empirical_lawhood.domains.matrix.classical_series import capstones
    calls=[]
    commit=capstones.capstone_preparation_commitment
    rng=s._rng
    def first(*args,**kwargs):
        calls.append('before-preparation')
        return commit(*args,**kwargs)
    def second(seed,purpose,panel=0):
        if purpose in (10,11):
            assert calls and calls[0]=='before-preparation'
        return rng(seed,purpose,panel)
    monkeypatch.setattr(capstones,'capstone_preparation_commitment',first)
    monkeypatch.setattr(s,'_rng',second)
    c=small_config()
    acquired=s.acquire_native_root(c,14)
    read=s.analyse_native_root(c,acquired)
    assert read['stages']['capstone-forecast']['scientific_connection']=='FORECAST_PREPARED_DESCRIPTION_SUPPLIES_FIXED_F_INPUT'
    assert read['stages']['capstone-preparation']['same_response_coefficients_support_and_calibration']
    assert read['stages']['capstone-forecast']['census']['assigned_task_requests']==2


@pytest.mark.conformance
def test_method_nonuse_does_not_mutate_retained_original_acquisition(monkeypatch):
    import json
    monkeypatch.setattr(s,'_io_origin',lambda *args,**kwargs:
        {'status':'UNAVAILABLE','reason':'HANKEL_CAP_CUTOFF_UNRESOLVED','witnesses':{}})
    c=small_config(phases=['e2'])
    acquired=s.acquire_native_root(c,15)
    original=json.dumps(acquired,sort_keys=True)
    read=s.analyse_native_root(c,acquired)
    assert read['stages']['e2']['cases'][0]['method_nonuse'][0]['IO48']=='HANKEL_CAP_CUTOFF_UNRESOLVED'
    assert json.dumps(acquired,sort_keys=True)==original
    assert s.validate_acquisition(c,acquired)==c


@pytest.mark.conformance
def test_failed_native_work_counts_remain_explicit_lower_bounds(monkeypatch):
    def failed(*args,**kwargs):
        raise FloatingPointError('declared native numerical failure after attempted work')
    monkeypatch.setattr(s,'_history',failed)
    c=small_config(phases=['sci02'])
    acquisition=s.acquire_native_root(c,16)
    assert acquisition['status']=='PARTIAL'
    work=acquisition['work_accounting']
    assert work['counts_are_lower_bounds'] is True
    assert work['cost_status']=='PARTIAL_FAILED_ATTEMPTS_REQUIRE_RECEIPTS'
    assert work['unavailable_case_counts']==1
    assert work['all_attempted_case_wall_seconds_included'] is True
    read=s.analyse_native_root(c,acquisition)
    assert read['stages']['sci02']['counts_are_lower_bounds'] is True
    assert read['stages']['sci02']['cost_status']=='PARTIAL_FAILED_ATTEMPTS_REQUIRE_RECEIPTS'
