# SPDX-License-Identifier: MPL-2.0
"""Independent small controls for fit-free response and equilibrium suppliers."""
import numpy as np
import pytest
from scipy.integrate import quad

from empirical_lawhood.methods.model_free_response import (
    incremental_receiver_certificate, measured_rank, signed_error_account,
    signed_propagation_account, couple_ou_normals, canonical_linear_control,
    equilibrium_grid_estimate, native_response_error_budget,
    retained_residual_assessment, harmonic_bath_trajectories,
)
from empirical_lawhood.methods.retained_gaussian_response import HarmonicBath


@pytest.mark.numerical(oracle='independent dense Hermitian resolvent solve')
def test_incremental_certificate_counts_native_columns_and_contains_dense_oracle():
    rng=np.random.default_rng(9021)
    m=rng.normal(size=(9,9)); a=(m+m.T)/2
    b=rng.normal(size=(9,1)); c=rng.normal(size=(9,1))
    calls=[]
    def action(q):
        calls.append(q.shape[1]); return a@q
    result=incremental_receiver_certificate(action,b,c,.3+2j,tolerance=1e-9,max_actions=9)
    exact=c.T@np.linalg.solve((.3+2j)*np.eye(9)-a,b)
    estimate=np.asarray(result['estimate_real'])+1j*np.asarray(result['estimate_imag'])
    assert np.linalg.norm(exact-estimate)<=result['residual_bound']+2e-12
    assert sum(calls)==result['action_count']<=9
    assert result['status']=='CERTIFIED'
    assert not result['native_finite_response_certified']


@pytest.mark.numerical(oracle='diagonal invariant eigenspace and exact rank')
def test_incremental_early_stopping_and_actual_rank():
    diagonal=np.arange(1.,9.)
    b=np.eye(8)[:,:1]
    result=incremental_receiver_certificate(lambda q:diagonal[:,None]*q,b,b,1j,tolerance=1e-12,max_actions=8)
    assert result['action_count']==1
    assert result['status']=='CERTIFIED'
    rank=measured_rank(np.diag([1.,1e-14,0.]),relative_tolerance=1e-12)
    assert rank['rank']==1 and rank['width']==3


def test_uncertified_finite_native_remainder_stays_unresolved():
    result=native_response_error_budget(numerical=0.,step=None,amplitude=.1,
        operator_history=0.,reduction=.01,tolerance=.2)
    assert result['status']=='UNRESOLVED'
    assert result['missing_operands']==['step']
    with pytest.raises(ValueError):
        incremental_receiver_certificate(lambda q:q,np.ones((2,1)),np.ones((2,1)),1.,tolerance=.1,max_actions=2)


@pytest.mark.numerical(oracle='explicit signed cancellation and cross-term arithmetic')
def test_signed_accounting_preserves_vectors():
    r=signed_error_account([0.,0.],[1.,2.],[0.,0.],[3.,-1.])
    assert r['contrast_error']==[2.,-3.]
    assert r['contrast_energy']==13.
    assert r['cross_term']==-2.
    assert r['identity_residual']==0.
    p=signed_propagation_account([1.,2.],[-1.,-2.])
    assert p['total_energy']==0.
    assert p['cross_term']==-10.


@pytest.mark.numerical(oracle='exact composition of two OU Gaussian updates')
def test_ou_coupling_matches_two_half_steps():
    z=np.asarray([[.3,-.2],[1.2,.8],[-.5,.2],[.3,-1.]])
    a=.7
    coarse=couple_ou_normals(z,a)
    fine=np.sqrt(1-a*a)*(a*z[::2]+z[1::2])
    assert np.allclose(np.sqrt(1-a**4)*coarse,fine,atol=1e-15)
    with pytest.raises(ValueError): couple_ou_normals(z[:3],a)


@pytest.mark.numerical(oracle='analytic Gaussian constant control and independent quartic quadrature')
def test_fixed_canonical_control_has_native_mean_without_fitting():
    k=np.asarray([[2.,.2],[.2,3.]])
    x=np.asarray([[-1.,3.],[2.,2.],[4.,-2.]])
    origin=np.asarray([.3,-.2]); a=np.asarray([1.,-2.])
    y=canonical_linear_control(x,(x-origin)@k,a,k)
    assert np.allclose(y,origin@a,atol=2e-15)
    beta=1.3
    potential=lambda v:.5*1.7*(v-.8)**2+.35*v**4
    density=lambda v:np.exp(-beta*potential(v))
    grad=lambda v:1.7*(v-.8)+1.4*v**3
    norm=quad(density,-8,8,epsabs=1e-12)[0]
    mean=quad(lambda v:v*density(v),-8,8,epsabs=1e-12)[0]/norm
    controlled=quad(lambda v:(v-grad(v)/4)*density(v),-8,8,epsabs=1e-12)[0]/norm
    assert abs(mean-controlled)<1e-11


@pytest.mark.numerical(oracle='direct paired root contrast variance with cross-center cancellation')
def test_equilibrium_uses_full_paired_covariance():
    means=np.asarray([[[1.,2.,3.],[2.,3.,4.]], [[4.,3.,2.],[5.,4.,3.]], [[0.,2.,5.],[1.,3.,6.]]])
    r=equilibrium_grid_estimate(means,[0.,1.,2.])
    assert r['mean']==2.
    assert r['variance_of_mean']==0.
    assert np.asarray(r['full_mean_covariance']).shape==(6,6)
    assert r['continuous_quadrature_bound'] is None
    assert not r['canonical_measure_qualified']


def test_sampled_residual_extrema_do_not_become_global_bounds():
    r=retained_residual_assessment(beta=1.,residual_lower=-.1,residual_upper=.1,envelope_scope='sampled')
    assert r['status']=='UNRESOLVED'
    r=retained_residual_assessment(beta=1.,residual_lower=-.1,residual_upper=.1,envelope_scope='global',reduced_variance=1.)
    assert r['log_partition_correction_bounds']==[-.1,.1]
    assert r['receiver_mean_error_bound']==pytest.approx(np.sinh(.1))


@pytest.mark.numerical(oracle='analytic coupled harmonic normal modes and exact energy conservation')
def test_bath_ensemble_preserves_energy_and_distinguishes_static_dynamic():
    one=HarmonicBath([[2.]],[[1.]],[[1.]])
    two=HarmonicBath([[2.]],[[2.]],[[4.]])
    assert np.array_equal(one.effective_stiffness,two.effective_stiffness)
    r=harmonic_bath_trajectories(one,beta=1.3,times=[0.,.1,.8,2.],samples=12,seed=11,
        preparation='conditional',retained_position=[.2],retained_velocity=[-.4])
    x,p=r['positions'],r['momenta']; k=np.asarray([[2.,1.],[1.,1.]])
    energy=.5*np.einsum('rti,ij,rtj->rt',x,k,x)+.5*np.sum(p*p,axis=-1)
    assert np.max(np.abs(energy-energy[:,:1]))<1e-12
    assert np.allclose(x[:,0,0],.2) and np.allclose(p[:,0,0],-.4)
    assert not np.allclose(one.memory(1.),two.memory(1.))
    assert not r['irreversible_mixing_established']


def test_capstone_features_and_fitted_response_are_exactly_force_odd():
    from empirical_lawhood.domains.matrix.classical_series.capstones import _response_features,_fit,_predict
    coord={'temperature':'1','friction':'1','cross_coupling':'1'}
    z=np.arange(24.)/24; force=np.arange(96.)/96
    x=_response_features(z,coord,force)
    opposite=_response_features(z,coord,-force)
    assert np.array_equal(opposite,-x)
    model=_fit([x,2*x],[1.,2.],1e-6,odd=True)
    assert np.allclose(_predict(model,x),-_predict(model,opposite),atol=0)
    assert np.array_equal(_predict(model,np.zeros_like(x)),[0.])


def test_io48_large_horizon_is_explicit_nonuse_before_dense_work():
    from empirical_lawhood.domains.matrix.classical_series.science import _io_origin
    result=_io_origin({'horizon_ticks':129},{},None,None,None,1)
    assert result['status']=='UNAVAILABLE'
    assert result['requested_steps']==258


def test_e5_nomination_uses_probability_units_and_attainable_headroom():
    from empirical_lawhood.domains.matrix.classical_series import science as s
    config=s.normalise_config({'phases':['e5'],'preparation_arms':['baseline','joint-increasing'],
        'coordinates':[{'id':'low','temperature':'1','friction':'1','cross_coupling':'.5'},
                       {'id':'high','temperature':'1','friction':'1','cross_coupling':'2'}]})
    values={}
    for seed,base,arm in [(1,.05,.02),(2,.05,.02),(3,.2,.05),(4,.2,.15),(5,.1,.1),(6,.1,.1)]:
        values[str(seed)]={'schema':'classical-series-summary.v1','seed':seed,
            'config_sha256':s.acquisition_config_fingerprint(config),'case_summaries':[],
            'preparation_contrast_losses':{'baseline':base,'joint-increasing':arm}}
    result=s.calibrate_native_roots({**config,'training_seeds':[1,2,3,4],'calibration_seeds':[5,6]},values)
    assert result['nominee']=='joint-increasing'
    assert result['training_arm_delivery_rates']=={'baseline':.5,'joint-increasing':.75}
    assert result['preparation_probability_headroom']==.5
    assert result['preparation_minimum_gain_units']=='NET_ADEQUACY_PROBABILITY'
    # Mean loss improvement is .065 < .1; the gain is .25 probability, so it enters.
    assert result['training_arm_losses']['baseline']-result['training_arm_losses']['joint-increasing']<.1


def test_occurrence_only_reanalysis_skips_all_response_models(monkeypatch):
    from empirical_lawhood.domains.matrix.classical_series import science as s
    monkeypatch.setattr(s,'validate_acquisition',lambda *args:None)
    monkeypatch.setattr(s,'_base_analysis',lambda *args,**kwargs:pytest.fail('unselected mechanics ran'))
    acquired={'seed':7,'cases':[],'assigned_cases':0,'native_seconds':0.}
    result=s.analyse_native_root({'phases':['e1']},acquired)
    assert list(result['stages'])==['e1']


def test_causal_selector_is_invariant_to_withheld_suffix_and_refuses_empty_future():
    from empirical_lawhood.methods.model_free_response import select_causal_response
    truth=np.zeros((1,7,2)); truth[:,1:]=1.
    first=truth.copy(); first[:,1:4]=.9; first[:,4:]=500.
    second=truth.copy(); second[:,1:4]=.5; second[:,4:]=1.
    result=select_causal_response(truth,{'first':first,'second':second},cutoff_tick=3,target_tick=6)
    assert result['selected']=='first'
    assert result['suffix_values_used'] is False
    truth[:,4:]=np.nan; first[:,4:]=-1e99; second[:,4:]=np.inf
    repeated=select_causal_response(truth,{'first':first,'second':second},cutoff_tick=3,target_tick=6)
    assert repeated==result
    assert select_causal_response(truth,{'first':first},cutoff_tick=6,target_tick=6)['status']=='UNRESOLVED'
