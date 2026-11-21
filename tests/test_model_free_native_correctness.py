# SPDX-License-Identifier: MPL-2.0
"""Independent native physical controls for the model-free matrix adapter."""

import numpy as np
import pytest

from empirical_lawhood.domains.matrix.classical_series import science as classical
from empirical_lawhood.domains.matrix.model_free import native
from empirical_lawhood.domains.matrix.six_matrix_response.gradients import analytic_gradient_terms, optimized_action_terms
from empirical_lawhood.domains.matrix.six_matrix_response.parameter_derivatives import parameters
from empirical_lawhood.domains.matrix.matrix_factor_response.science import native_position_coordinates, native_position_lift


def small_config():
    return classical.normalise_config({'ramp_ticks':4,'handoff_tick':4,'history_ticks':8,
        'horizon_ticks':4,'pulse_ticks':1,'refresh_tick':2,'observation_stride':1,
        'persistence_ticks':1,'survival_ticks':2,'amplitude':'0.001','panels':1})


@pytest.mark.numerical(oracle='central directional difference of complete native action plus harmonic restraint')
def test_complete_restrained_gradient_differentiates_actual_native_potential():
    c=small_config(); row=c['coordinates'][0]
    coord,state=native.target_state(c,row)
    random=np.random.default_rng(219)
    q=native_position_coordinates(state.positions)+.003*random.normal(size=96)
    direction=random.normal(size=96); direction/=np.linalg.norm(direction)
    receiver=random.normal(size=96); receiver/=np.linalg.norm(receiver)
    stiffness,center=1.7,.2
    selected=parameters(state,coord.member)
    def energy(point):
        return (optimized_action_terms(native_position_lift(point),selected).total
                +.5*stiffness*(receiver@point-center)**2)
    native_gradient=native_position_coordinates(analytic_gradient_terms(native_position_lift(q),selected).total)
    total_gradient=native_gradient+stiffness*(receiver@q-center)*receiver
    epsilon=1e-5
    difference=(energy(q+epsilon*direction)-energy(q-epsilon*direction))/(2*epsilon)
    assert difference==pytest.approx(total_gradient@direction,rel=2e-6,abs=2e-7)


@pytest.mark.numerical(oracle='existing unrestrained BAOAB update with identical state and innovation')
def test_zero_restraint_reproduces_native_baoab_map():
    c=small_config(); row=c['coordinates'][0]
    coord,state=native.target_state(c,row)
    random=native.rng(7,999)
    noise=native.hermitian_noise(rng=random,q=2)
    direction=np.eye(96)[0]
    actual=native.restrained_step(state,coord,noise,direction,.1,0.)
    expected=native.step(state,coord,noise)
    assert np.allclose(actual.positions,expected.positions,rtol=0,atol=2e-15)
    assert np.allclose(actual.momenta,expected.momenta,rtol=0,atol=2e-15)


@pytest.mark.numerical(oracle='central finite native force chord versus analytically differentiated BAOAB path')
def test_same_noise_native_chord_matches_infinitesimal_response_at_small_amplitude():
    c=small_config(); row=c['coordinates'][0]
    _,state=native.target_state(c,row)
    force,receiver=native.physical_chart(c,7)
    result=native.paired_response(c,row,state,force[:,:1],receiver,7,0)
    odd=np.asarray(result['odd_response']); tangent=np.asarray(result['native_tangent'])
    assert np.max(np.abs(odd-tangent))<2e-10
    assert np.max(np.abs(tangent))>1e-8
    assert result['scope']=='PAIRED_NATIVE_FINITE_CHORD_AND_REALIZED_PATH_TANGENT'


@pytest.mark.numerical(oracle='native gradient central difference versus physical Hessian action')
def test_native_hessian_action_has_physical_coordinate_units():
    c=small_config(); row=c['coordinates'][0]
    coord,state=native.target_state(c,row)
    q=native_position_coordinates(state.positions)
    vector=np.random.default_rng(72).normal(size=96); vector/=np.linalg.norm(vector)
    selected=parameters(state,coord.member)
    epsilon=1e-5
    gp=native_position_coordinates(analytic_gradient_terms(native_position_lift(q+epsilon*vector),selected).total)
    gm=native_position_coordinates(analytic_gradient_terms(native_position_lift(q-epsilon*vector),selected).total)
    expected=(gp-gm)/(2*epsilon)
    actual=native.action_at(state,coord.member)(vector)
    assert np.allclose(actual,expected,rtol=2e-7,atol=3e-7)
