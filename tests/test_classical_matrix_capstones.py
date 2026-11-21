# SPDX-License-Identifier: MPL-2.0
"""Controls for two genuine capstone connections and their causal frozen packages."""
from copy import deepcopy

import numpy as np
import pytest

from empirical_lawhood.domains.matrix.classical_series import capstones as method


def configuration():
    return {'phases':['capstone-forecast','capstone-preparation'],
        'horizon_ticks':64,'handoff_tick':32,'pulse_ticks':16,'timestep':'0.001',
        'amplitude':'0.01','panels':2,'actions':['FACTOR','TRACE'],
        'response_tolerance':'0.1','numerical_tolerance':'0.01',
        'calibration_alpha':'0.2','ridge_penalty':'0.000001',
        'capstone_support_radius':'3','capstone_task_threshold':'0','capstone_horizon_tick':64,
        'coordinates':[{'id':'nominal','temperature':'1','friction':'1','cross_coupling':'1'}],
        'preparation_arms':['baseline','joint-increasing']}


def instrument():
    forces = np.eye(96)[:,:2]
    receivers = np.zeros((48,192))
    receivers[:24,:24] = np.eye(24)
    receivers[24:,96:120] = np.eye(24)
    return forces,receivers


def synthetic_acquisition(config, seed, initial, package=None):
    forces,receivers = instrument()
    coordinate = config['coordinates'][0]
    cases=[]
    for arm in config['preparation_arms']:
        z0 = np.zeros(24); z0[0]=initial
        z = z0.copy(); z[0] += 0 if arm=='baseline' else -.2
        # First commitment exists before native prepared state and assay values.
        first = method.capstone_preparation_commitment(config,seed,coordinate,arm,z0,forces,package)
        states=np.zeros((2,192)); states[:,:24]=z
        direct = method.capstone_response_commitment(config,seed,coordinate,arm,np.stack((z,z)),forces,package)
        case={'coordinate':deepcopy(coordinate),'arm':arm,'status':'COMPLETED',
            'preparation_initial_descriptor':z0.tolist(),'origin_states':states.tolist(),
            'capstone_preparation_commitment':first,'capstone_response_commitment':direct,'panels':[]}
        t=config['capstone_horizon_tick']*float(config['timestep'])
        pulse=min(t,config['pulse_ticks']*float(config['timestep']))
        sq=float(config['amplitude'])*pulse*(t-pulse/2)
        sp=float(config['amplitude'])*pulse
        y=[1.+.1*z[0],.5+.2*z[0]]
        for panel in range(config['panels']):
            response=np.zeros((2,2,config['horizon_ticks']+1,48))
            response[:,0,config['capstone_horizon_tick'],1]=sq*y[0]
            response[:,1,config['capstone_horizon_tick'],24]=sp*y[1]
            case['panels'].append({'panel':panel,'native_response':response.tolist()})
        cases.append(case)
    return {'seed':seed,'cases':cases,'forces':forces.tolist(),'receivers':receivers.tolist()}


def training_summaries(config):
    train=tuple(range(6)); cal=tuple(range(10,14))
    inputs={0:-1.,1:-.6,2:-.2,3:.2,4:.6,5:1.,10:-.7,11:-.3,12:.3,13:.7}
    summaries={}
    for seed in (*train,*cal):
        acquired=synthetic_acquisition(config,seed,inputs[seed])
        summaries[seed]={'capstone_cases':[method.capstone_case_summary(config,seed,case,
            acquired['receivers'],acquired['forces']) for case in acquired['cases']]}
    return summaries,train,cal


@pytest.fixture
def prepared():
    config=configuration()
    summaries,train,cal=training_summaries(config)
    package=method.freeze_capstones(config,summaries,train,cal)
    return config,summaries,train,cal,package


@pytest.mark.numerical(oracle='Known affine prepared-state and scalar response relationships on a deterministic fixture')
def test_frozen_forecast_supplies_actual_prepared_descriptor_to_fixed_coefficients(prepared):
    config,summaries,train,cal,package=prepared
    assert package['fixed_response_package']['training_usable_roots']==len(train)
    assert package['fixed_response_package']['calibration_radius'] < 1e-6
    assert package['composition_calibration']['descriptor_radius'] < 1e-6
    acquired=synthetic_acquisition(config,20,.25,package)
    # The odd homogeneous response regularizes the force coefficient as well
    # as its descriptor dependence. In this orthogonal affine fixture its
    # constant shrinkage is lambda/(n+lambda); include both fit contributions.
    response_fit_allowance=2*float(config['ridge_penalty'])/len(train)
    for case in acquired['cases']:
        commitment=case['capstone_preparation_commitment']
        expected=.25+(0 if case['arm']=='baseline' else -.2)
        assert commitment['predicted_prepared_descriptor'][0]==pytest.approx(expected,abs=1e-7)
        assert commitment['cutoff_tick']==0
        assert commitment['tasks'][0]['point']==pytest.approx(1.+.1*expected,abs=response_fit_allowance)
        assert commitment['tasks'][1]['point']==pytest.approx(.5+.2*expected,abs=response_fit_allowance)
        assert all(t['admitted'] for t in commitment['tasks'])
    before=deepcopy(package)
    outcome=method.assess_capstones(config,acquired,package)
    assert package==before
    assert outcome['forecast']['scientific_connection']=='FORECAST_PREPARED_DESCRIPTION_SUPPLIES_FIXED_F_INPUT'
    assert outcome['forecast']['prepared_state_observed_to_make_forecast'] is False
    assert outcome['forecast']['census']['assigned_task_requests']==4
    assert outcome['forecast']['census']['delivered_requests']==4
    assert outcome['forecast']['census']['false_admissions']==0
    assert outcome['forecast']['coefficient_refits_on_confirmation']==0


@pytest.mark.conformance
def test_preparation_changes_input_with_entire_package_unchanged(prepared):
    config,_,_,_,package=prepared
    acquired=synthetic_acquisition(config,20,.25,package)
    direct=[case['capstone_response_commitment'] for case in acquired['cases']]
    assert direct[0]['fixed_response_package_sha256']==direct[1]['fixed_response_package_sha256']
    assert direct[0]['prepared_descriptors']!=direct[1]['prepared_descriptors']
    assert direct[0]['tasks'][0]['point']!=direct[1]['tasks'][0]['point']
    assert direct[0]['tasks'][0]['radius']==direct[1]['tasks'][0]['radius']
    result=method.assess_capstones(config,acquired,package)['preparation']
    assert result['same_response_coefficients_support_and_calibration'] is True
    # Baseline already delivers every development request. Forcing an arm
    # with no useful service gain was the audited nomination defect.
    assert result['nominee'] is None
    assert package['design_feasibility']['development_positive_control']
    assert result['comparisons'][0]['same_complete_package']
    assert result['census']['delivered_requests']==4
    assert result['historical_result_claim'] is False


@pytest.mark.conformance
def test_before_preparation_and_before_future_commitments_are_enforced(prepared):
    config,_,_,_,package=prepared
    acquired=synthetic_acquisition(config,20,.25,package)
    changed=deepcopy(acquired)
    changed['cases'][0]['capstone_preparation_commitment']['predicted_prepared_descriptor'][0]+=1
    with pytest.raises(ValueError,match='before-preparation'):
        method.assess_capstones(config,changed,package)
    changed=deepcopy(acquired)
    changed['cases'][0]['capstone_response_commitment']['tasks'][0]['admitted']=False
    with pytest.raises(ValueError,match='before-assay'):
        method.assess_capstones(config,changed,package)
    changed=deepcopy(acquired)
    del changed['cases'][0]['capstone_preparation_commitment']
    with pytest.raises(ValueError,match='before-preparation'):
        method.assess_capstones(config,changed,package)


@pytest.mark.conformance
def test_missing_calibration_roots_stay_in_quantile_and_full_denominator(prepared):
    config,summaries,train,cal,_=prepared
    missing=deepcopy(summaries)
    del missing[cal[0]]
    package=method.freeze_capstones(config,missing,train,cal)
    fixed=package['fixed_response_package']
    assert len(fixed['calibration_scores'])==len(cal)
    assert fixed['calibration_scores'][0]['score'] is None
    assert fixed['calibration_radius'] is None
    assert package['composition_calibration']['descriptor_radius'] is None
    acquired=synthetic_acquisition(config,20,.25,package)
    result=method.assess_capstones(config,acquired,package)
    for stage in result.values():
        assert stage['census']['assigned_task_requests']==4
        assert stage['census']['declined_requests']==4
        assert stage['census']['delivered_requests']==0


@pytest.mark.conformance
def test_unavailable_confirmation_future_is_not_removed_or_false_success(prepared):
    config,_,_,_,package=prepared
    acquired=synthetic_acquisition(config,20,.25,package)
    acquired['cases'][1]['status']='UNAVAILABLE'
    acquired['cases'][1]['reason']='DECLARED_NATIVE_FAILURE_AFTER_COMMITMENT'
    acquired['cases'][1]['panels']=[]
    result=method.assess_capstones(config,acquired,package)
    for stage in result.values():
        assert stage['census']['assigned_task_requests']==4
        assert stage['census']['unavailable_future_requests']==2
        assert stage['census']['unresolved_admitted_requests']==2
        assert stage['census']['false_admissions']==0
        assert stage['census']['delivered_requests']==2


@pytest.mark.conformance
def test_numerical_failure_is_retained_and_support_does_not_recalibrate(prepared):
    config,_,_,_,package=prepared
    acquired=synthetic_acquisition(config,20,20.,package)
    outcome=method.assess_capstones(config,acquired,package)
    assert outcome['preparation']['census']['admitted_requests']==0
    assert outcome['forecast']['census']['admitted_requests']==0
    assert all(not task['supported'] for row in outcome['preparation']['cases'] for task in row['tasks'])
    acquired=synthetic_acquisition(config,20,.25,package)
    acquired['cases'][0]['panels'][0]['native_response'][1][0][64][1]+=1.
    outcome=method.assess_capstones(config,acquired,package)
    assert outcome['forecast']['census']['unresolved_admitted_requests']==2


@pytest.mark.conformance
def test_cannot_refit_support_or_move_confirmatory_roots_into_training(prepared):
    config,_,train,_,package=prepared
    acquired=synthetic_acquisition(config,20,.25,package)
    mutated=deepcopy(package)
    mutated['fixed_response_package']['support']['radius']=1000
    with pytest.raises(ValueError,match='package has changed'):
        method.assess_capstones(config,acquired,mutated)
    with pytest.raises(ValueError,match='TRAIN or CAL'):
        method.capstone_preparation_commitment(config,train[0],config['coordinates'][0],'baseline',np.zeros(24),instrument()[0],package)
    changed=deepcopy(config); changed['response_tolerance']='1'
    with pytest.raises(ValueError,match='package has changed'):
        method.assess_capstones(changed,acquired,package)


@pytest.mark.conformance
def test_root_and_case_census_is_not_silently_reduced(prepared):
    config,summaries,train,cal,package=prepared
    contaminated=deepcopy(summaries); contaminated[100]=deepcopy(summaries[train[0]])
    with pytest.raises(ValueError,match='CONF outcomes'):
        method.freeze_capstones(config,contaminated,train,cal)
    duplicated=deepcopy(summaries)
    duplicated[train[0]]['capstone_cases'].append(deepcopy(duplicated[train[0]]['capstone_cases'][0]))
    with pytest.raises(ValueError,match='duplicates'):
        method.freeze_capstones(config,duplicated,train,cal)
    acquired=synthetic_acquisition(config,20,.25,package)
    acquired['cases'].pop()
    with pytest.raises(ValueError,match='complete assigned case census'):
        method.assess_capstones(config,acquired,package)


@pytest.mark.conformance
def test_posthoc_phase_selection_does_not_change_frozen_science(prepared):
    config,_,_,_,package=prepared
    acquired=synthetic_acquisition(config,20,.25,package)
    changed=deepcopy(config); changed['phases']=['capstone-forecast']
    result=method.assess_capstones(changed,acquired,package)
    assert result['forecast']['census']['delivered_requests']==4
