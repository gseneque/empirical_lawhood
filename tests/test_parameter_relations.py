# SPDX-License-Identifier: MPL-2.0
"""Optional learned relation controls with independently known generating law."""
from copy import deepcopy
import math
import numpy as np
import pytest

from empirical_lawhood.methods.parameter_relations import fit_parameter_relations,predict_parameter_relations


def data():
    parameters=[(0.,0.,0.),(-.5,0.,0.),(.5,0.,0.),(0.,-.5,0.),(0.,.5,0.),
                (0.,0.,-.5),(0.,0.,.5),(-.5,-.5,0.),(.5,.5,0.)]
    rows=[]
    for root in range(17):
        rng=np.random.default_rng(root)
        for i,p in enumerate(parameters):
            z=float(rng.uniform(-.1,.1))
            features={'baseline':[1.,*p],'structure':[1.,*p,z]}
            y=math.expm1(.3+.2*p[0]-.1*p[1]+.15*p[2]+.05*z)
            rows.append({'root_id':root,'coordinate_id':str(i),'parameters':list(p),'features':features,'target':y})
    return rows,tuple(range(12)),tuple(range(12,17)),[str(i) for i in range(9)]


@pytest.mark.numerical(oracle='Known log-linear physical-parameter relation with independent structural covariate')
def test_grouped_parameter_fit_identifies_relation_and_seals_calibration():
    rows,train,cal,ids=data()
    package=fit_parameter_relations(rows,training_roots=train,calibration_roots=cal,coordinate_ids=ids,alpha=.2)
    assert package['status']=='FROZEN'
    assert package['parameter_design_rank']==4
    assert len(package['fold_assignments'])==len(train)
    assert len({r['root_id'] for r in package['fold_assignments']})==len(train)
    assert len(package['models']['baseline']['candidate_evaluations'])==len(package['models']['structure']['candidate_evaluations'])
    assert package['models']['structure']['selected_group_validation_score']<package['models']['baseline']['selected_group_validation_score']
    p=[.2,-.1,.15]; z=.03
    forecast=predict_parameter_relations(package,root_id=30,coordinate_id='held',parameters=p,
        features={'baseline':[1.,*p],'structure':[1.,*p,z]},tolerance=1.)
    target=math.expm1(.3+.2*p[0]-.1*p[1]+.15*p[2]+.05*z)
    assert forecast['structure']['point']==pytest.approx(target,abs=1e-7)
    assert forecast['structure']['transfer_coordinate']
    assert not forecast['structure']['coverage_inherited']
    assert all(len(m['calibration_scores'])==len(cal) for m in package['models'].values())


def test_missing_calibration_stays_in_complete_root_quantile():
    rows,train,cal,ids=data()
    rows=[r for r in rows if not (r['root_id']==cal[0] and r['coordinate_id']=='0')]
    package=fit_parameter_relations(rows,training_roots=train,calibration_roots=cal,coordinate_ids=ids,alpha=.05)
    assert package['models']['structure']['calibration_scores'][0]['score'] is None
    assert package['models']['structure']['calibration_radius'] is None


def test_identifiability_and_role_boundaries_refuse_false_relations():
    rows,train,cal,ids=data()
    narrow=[{**r,'parameters':[0.,0.,0.]} for r in rows]
    result=fit_parameter_relations(narrow,training_roots=train,calibration_roots=cal,coordinate_ids=ids,alpha=.2)
    assert result['status']=='FIT_UNAVAILABLE'
    assert result['reason']=='DECLARED_PARAMETER_EFFECTS_NOT_IDENTIFIABLE'
    package=fit_parameter_relations(rows,training_roots=train,calibration_roots=cal,coordinate_ids=ids,alpha=.2)
    with pytest.raises(ValueError,match='CONF'):
        predict_parameter_relations(package,root_id=train[0],coordinate_id='0',parameters=[0.,0.,0.],features={},tolerance=1.)
    with pytest.raises(ValueError,match='substitutes'):
        predict_parameter_relations(package,root_id=99,coordinate_id='0',parameters=[1.,0.,0.],features={},tolerance=1.)
    changed=deepcopy(package); changed['models']['structure']['coefficients'][0]+=1
    with pytest.raises(ValueError,match='bytes'):
        predict_parameter_relations(changed,root_id=99,coordinate_id='held',parameters=[0.,0.,0.],features={},tolerance=1.)


def test_relation_is_wired_into_classical_frozen_lifecycle():
    from empirical_lawhood.domains.matrix.classical_series import science as s
    rows,train,cal,ids=data()
    coordinate_rows=[]
    for coord in ids:
        p=next(r['parameters'] for r in rows if r['coordinate_id']==coord)
        coordinate_rows.append({'id':coord,'temperature':str(math.exp(p[0])),
            'friction':str(math.exp(p[1])),'cross_coupling':str(math.exp(p[2]))})
    c=s.normalise_config({'phases':['e4','e6'],'coordinates':coordinate_rows,
        'relation_training_coordinates':ids,'relation_response_method':'FACTOR','calibration_alpha':'.2'})
    summaries={}
    for root in (*train,*cal):
        cases=[]
        for row in [r for r in rows if r['root_id']==root]:
            coordinate=next(x for x in coordinate_rows if x['id']==row['coordinate_id'])
            cases.append({'arm':'baseline','coordinate':coordinate,'status':'COMPLETED',
                'numerical_policy_pass':True,'features':row['features'],
                'method_scores':{'FACTOR':[{'frozen':{'maximum':row['target']}}]}})
        summaries[root]=cases
    package=s._fit_parameter_relation(c,summaries,train,cal)
    assert package['status']=='FROZEN'
    assert package['receiver_loss_method']=='FACTOR'
    assert package['historical_reproduction'] is False
    assert package['package_sha256']==s._fingerprint({k:v for k,v in package.items() if k!='package_sha256'})


def test_classical_training_calibration_and_pre_future_relation_commitment(monkeypatch):
    """Synthetic canonical summaries exercise the actual fitted lifecycle owner."""
    from empirical_lawhood.domains.matrix.classical_series import science as s
    rows,train,cal,ids=data()
    coordinates=[]
    for coord in ids:
        p=next(r['parameters'] for r in rows if r['coordinate_id']==coord)
        coordinates.append({'id':coord,'temperature':str(math.exp(p[0])),
            'friction':str(math.exp(p[1])),'cross_coupling':str(math.exp(p[2]))})
    c=s.normalise_config({'phases':['e4','e6'],'coordinates':coordinates,
        'relation_training_coordinates':ids,'relation_response_method':'FACTOR','calibration_alpha':'.2'})
    summaries={}
    for root in (*train,*cal):
        cases=[]
        for row in [r for r in rows if r['root_id']==root]:
            coordinate=next(x for x in coordinates if x['id']==row['coordinate_id'])
            cases.append({'arm':'baseline','coordinate':coordinate,'status':'COMPLETED',
                'numerical_policy_pass':True,'features':row['features'],
                'method_scores':{method:[{'frozen':{'maximum':row['target']}}]
                    for method in ('FACTOR','INPUT_KRYLOV','JOINT_KRYLOV')}})
        summaries[str(root)]={'schema':'classical-series-summary.v1','seed':root,
            'config_sha256':s.acquisition_config_fingerprint(c),'case_summaries':cases,
            'preparation_contrast_losses':{'baseline':None},'capstone_cases':[]}
    package=s.calibrate_native_roots({**c,'training_seeds':list(train),'calibration_seeds':list(cal)},summaries)
    assert package['parameter_relation']['status']=='FROZEN'
    monkeypatch.setattr(s,'_features',lambda case:case['features'])
    cases=deepcopy(summaries['0']['case_summaries'])
    for case in cases:
        case['causal_prefix_sha256']='a'*64
        case['pre_response_commitment']=s._precommit(c,99,case,package)
        assert 'parameter_relation_forecasts' in case['pre_response_commitment']
        assert case['pre_response_commitment']['cutoff_tick']==c['handoff_tick']
    acquired={'seed':99,'cases':cases}
    result=s._parameter_relation_readout(c,acquired,cases,package)
    assert result['status']=='FROZEN_RELATION_EVALUATED'
    assert result['refits_on_confirmation']==0
    assert len(result['coordinates'])==len(coordinates)
    assert not result['coverage_transported_to_new_coordinates']
    cases[0]['pre_response_commitment']['parameter_relation_forecasts']['structure']['point']+=1
    with pytest.raises(ValueError,match='before-future'):
        s._parameter_relation_readout(c,acquired,cases,package)


def test_authored_l9_frame_identifies_effects_and_records_constant_feature_removal():
    """The authored physical frame must not fail because zero leakages repeat an intercept."""
    import json
    from pathlib import Path
    design=json.loads(Path('programmes/foundations/emergent-structure/workflows/model-free/relation-benchmark.json').read_text())
    settings=design['settings']; ids=settings['relation_training_coordinates']
    coordinates=[c for c in settings['coordinates'] if c['id'] in ids]
    parameters=[[math.log(float(c[k])) for k in ('temperature','friction','cross_coupling')] for c in coordinates]
    assert np.linalg.matrix_rank([[1.,*p] for p in parameters])==4
    assert np.linalg.matrix_rank([[1.,*p,p[0]*p[1],p[0]*p[2],p[1]*p[2]] for p in parameters])==7
    rows=[]
    for root in range(10):
        for coordinate,p in zip(coordinates,parameters,strict=True):
            # Fixed Hessian norm and exact zero/constant structure are admissible
            # controls, not a justification for manufacturing descriptor variation.
            base=[1.,2.,*p]
            rows.append({'root_id':root,'coordinate_id':coordinate['id'],'parameters':p,
                'features':{'baseline':base,'structure':base+[0.,0.,.5]},
                'target':math.expm1(.3+.1*p[0]-.2*p[1]+.05*p[2])})
    package=fit_parameter_relations(rows,training_roots=range(6),calibration_roots=range(6,10),coordinate_ids=ids,alpha=.2)
    assert package['status']=='FROZEN'
    for kind,expected in [('baseline',{1}),('structure',{1,5,6,7})]:
        model=package['models'][kind]
        dropped={r['index'] for r in model['dropped_features']}
        assert expected<=dropped
        assert all(r['reason']=='CONSTANT_ON_TRAIN' for r in model['dropped_features'])
        assert model['rank']==len(model['active_feature_indices'])
        assert model['rank']<model['feature_count']
        assert all(r['status']=='EVALUABLE' for r in model['candidate_evaluations'])
