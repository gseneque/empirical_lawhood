"""Independent exposed software controls; no real E4 source or acquisition."""

from dataclasses import replace
from decimal import Decimal as D
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_derivatives as derivatives
from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_history as history
from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_response, simulation
from empirical_lawhood.adapters.simulators.six_matrix_response.contracts import (
    BetaCouplingRule, MatrixIntegratorKind, MatrixPrecision,
    SixMatrixResponseModelFamilyMember, SixMatrixResponseNumericalView,
)
from empirical_lawhood.adapters.simulators.six_matrix_response.gradients import (
    SixMatrixParameters, analytic_gradient_terms, coupling_derivative_density, reference_action_terms,
)
from empirical_lawhood.adapters.simulators.six_matrix_response.history_source import (
    advance_history_pair, history_native_parameters, initial_history_state,
)
from empirical_lawhood.adapters.simulators.six_matrix_response.model import SixMatrixState, hermitian_part
from empirical_lawhood.adapters.simulators.six_matrix_response.preparation_differential import (
    NativeStateDifferential, preparation_force_step,
)
from empirical_lawhood.adapters.simulators.six_matrix_response.response_hessian import _hessian_image
from empirical_lawhood.adapters.simulators.six_matrix_response.shooting import hermitian_basis
from empirical_lawhood.adapters.simulators.six_matrix_response.simulation import BAOABGradientCache, hermitian_noise
from empirical_lawhood.kernel.decoding import decode_canonical_bytes


REGIMES = (('.2','.3','.4','.25'),('.5','1','1','1'),('.9','2.2','1.8','2.4'))


def coordinate(regime, *, family=0, dt=D('.002')):
    mass,cross,friction,bath = map(D,regime)
    member = SixMatrixResponseModelFamilyMember('test.e4.member',mass,mass,cross,BetaCouplingRule.PUBLISHED_DETERMINISTIC)
    views = tuple(SixMatrixResponseNumericalView('test.e4.view.'+str(i),MatrixIntegratorKind.BAOAB_UNDERDAMPED_LANGEVIN,
        dt/i,'dimensionless-langevin-time',friction,bath,MatrixPrecision.COMPLEX128,
        'numpy.pcg64dxsm','1.0.0','test.e4.numeric-stream',8*i) for i in (1,2))
    return history.MatrixParameterCoordinate('test.e4.coordinate',2,member,*views,'test.e4.physical-clock',
        history.FOUR_FAMILY_PREPARATION_IDS[family],D('2.1'),D('4.4'),D(8),4,4,(0,2,4,6,8),
        history.INITIAL_RULE_ID,history.PREPARATION_RULE_ID)


def corpus(seed=802):
    rng = np.random.Generator(np.random.PCG64(seed))
    draw = lambda: hermitian_noise(rng=rng,q=2)
    state = SixMatrixState(2,.2*draw(),.1*draw(),3,.45,.8)
    direction = draw();direction /= np.linalg.norm(direction)
    return rng,state,direction,draw(),NativeStateDifferential(draw(),draw())


@pytest.mark.parametrize('regime',REGIMES)
@pytest.mark.parametrize('amplitude',(-.2,0.,.2))
def test_constant_response_cache_preserves_every_step_and_gradient_count(regime, amplitude, monkeypatch):
    c = coordinate(regime)
    rng,state,direction,_,_ = corpus()
    noise = np.asarray([hermitian_noise(rng=rng,q=2) for _ in range(8)],dtype='<c16')
    gradient = simulation.analytic_gradient_terms
    evaluations = []
    def counted(*args, **kwargs):
        evaluations.append(None)
        return gradient(*args, **kwargs)
    monkeypatch.setattr(simulation,'analytic_gradient_terms',counted)
    expected_positions,expected_momenta = [state.positions.copy()],[state.momenta.copy()]
    reference = state
    for tick,innovation in enumerate(noise):
        reference = derivatives.scheduled_force_step(reference,direction=direction,
            amplitude=amplitude if tick < 3 else 0.,member=c.member,numerical_view=c.primary_view,
            next_alpha_tilde_x=state.alpha_tilde_x,next_alpha_tilde_y=state.alpha_tilde_y,
            standardized_noise=innovation)
        expected_positions.append(reference.positions.copy());expected_momenta.append(reference.momenta.copy())
    assert len(evaluations) == 2*len(noise)
    evaluations.clear()
    actual = parameter_response.native_constant_response_branch(state,member=c.member,
        numerical_view=c.primary_view,direction=direction,amplitude=amplitude,pulse_steps=3,innovations=noise)
    assert len(evaluations) == len(noise)+1
    assert actual['positions'].tobytes() == np.asarray(expected_positions,dtype='<c16').tobytes()
    assert actual['momenta'].tobytes() == np.asarray(expected_momenta,dtype='<c16').tobytes()
    assert actual['noise'].tobytes() == noise.tobytes()


def test_existing_gradient_cache_invalidates_in_place_position_and_exact_coupling_changes(monkeypatch):
    _,state,_,_,_ = corpus()
    positions = state.positions.copy()
    selected = derivatives.parameters(state,coordinate(REGIMES[0]).member)
    gradient = simulation.analytic_gradient_terms
    evaluations = []
    def counted(*args, **kwargs):
        evaluations.append(None)
        return gradient(*args, **kwargs)
    monkeypatch.setattr(simulation,'analytic_gradient_terms',counted)
    cache = BAOABGradientCache()
    original = cache.evaluate(positions,selected).tobytes()
    assert original == gradient(positions,selected).total.tobytes()
    assert cache.evaluate(positions.copy(),selected).tobytes() == original
    assert len(evaluations) == 1
    positions[0,0,0,0] += .03125
    changed = cache.evaluate(positions,selected)
    assert changed.tobytes() == gradient(positions,selected).total.tobytes()
    assert len(evaluations) == 2
    for name in ('alpha_tilde_x','alpha_tilde_y'):
        selected = replace(selected,**{name:np.nextafter(getattr(selected,name),np.inf)})
        changed = cache.evaluate(positions,selected)
        assert changed.tobytes() == gradient(positions,selected).total.tobytes()
    assert len(evaluations) == 4


@pytest.mark.parametrize('regime',REGIMES)
def test_potential_gradient_hessian_beta_and_cross_coefficients_independently(regime):
    c = coordinate(regime)
    _,state,_,_,delta = corpus()
    p = derivatives.parameters(state,c.member)
    gradient = analytic_gradient_terms(state.positions,p).total
    # Independently transcribed potential sums, full96 real-HS position basis.
    for sector in range(2):
        for component in range(3):
            for basis in hermitian_basis(4):
                direction = np.zeros_like(state.positions);direction[sector,component] = basis
                eps = 1e-6
                difference = (reference_action_terms(state.positions+eps*direction,p).total
                    -reference_action_terms(state.positions-eps*direction,p).total)/(2*eps)
                assert difference == pytest.approx(np.vdot(direction,gradient).real,abs=1e-8,rel=1e-7)
    image = derivatives.hessian_image(state.positions,delta.positions,p)
    for eps in (1e-4,1e-5,1e-6):
        difference = (analytic_gradient_terms(state.positions+eps*delta.positions,p).total
            -analytic_gradient_terms(state.positions-eps*delta.positions,p).total)/(2*eps)
        np.testing.assert_allclose(image,difference,atol=2e-5 if eps==1e-4 else 3e-7,rtol=2e-7)
    # The beta map changes sign across M=1/3 and must be differentiated too.
    for sector in (0,1):
        rates = np.eye(2)[sector]
        image = derivatives.coupling_gradient_image(state.positions,p,rates)
        changes = {'alpha_tilde_x':eps*rates[0],'alpha_tilde_y':eps*rates[1]}
        left = replace(p,**{k:getattr(p,k)-v for k,v in changes.items()})
        right = replace(p,**{k:getattr(p,k)+v for k,v in changes.items()})
        difference = (analytic_gradient_terms(state.positions,right).total-analytic_gradient_terms(state.positions,left).total)/(2*eps)
        np.testing.assert_allclose(image,difference,atol=2e-9,rtol=2e-8)
        potential_difference = (reference_action_terms(state.positions,right).total-reference_action_terms(state.positions,left).total)/(2*eps*p.n)
        assert potential_difference == pytest.approx(coupling_derivative_density(state.positions,p)[sector],abs=1e-9)


@pytest.mark.parametrize('regime',REGIMES)
def test_scheduled_both_sector_native_tangent_and_finite_secant(regime):
    c = coordinate(regime)
    _,state,direction,noise,delta = corpus()
    amplitude = .17
    current_rates,next_rates = np.array((.2,-.1)),np.array((.3,-.25))
    def step(s,a,next_values):
        return derivatives.scheduled_force_step(s,direction=direction,amplitude=a,member=c.member,
            numerical_view=c.primary_view,next_alpha_tilde_x=next_values[0],next_alpha_tilde_y=next_values[1],standardized_noise=noise)
    next_values = np.array((.7,1.1))
    advanced = step(state,amplitude,next_values)
    tangent = derivatives.tangent_step(state,advanced,delta,direction=direction,force_derivative=.4,
        member=c.member,numerical_view=c.primary_view,current_coupling_derivative=current_rates,next_coupling_derivative=next_rates)
    for eps in (1e-4,1e-5,1e-6):
        signed = []
        for sign in (-1,1):
            perturbed = replace(state,positions=state.positions+sign*eps*delta.positions,
                momenta=state.momenta+sign*eps*delta.momenta,alpha_tilde_x=state.alpha_tilde_x+sign*eps*current_rates[0],
                alpha_tilde_y=state.alpha_tilde_y+sign*eps*current_rates[1])
            signed.append(step(perturbed,amplitude+sign*eps*.4,next_values+sign*eps*next_rates))
        for n in ('positions','momenta'):
            difference = (getattr(signed[1],n)-getattr(signed[0],n))/(2*eps)
            np.testing.assert_allclose(getattr(tangent,n),difference,atol=1e-7,rtol=1e-7)
    # Finite chord uses shared schedule and same noise; no observed future is a forecast.
    eps = .025
    left = replace(state,positions=state.positions-eps*delta.positions,momenta=state.momenta-eps*delta.momenta)
    right = replace(state,positions=state.positions+eps*delta.positions,momenta=state.momenta+eps*delta.momenta)
    lnext,rnext = step(left,amplitude-eps*.4,next_values),step(right,amplitude+eps*.4,next_values)
    reconstructed = derivatives.secant_step(left,right,lnext,rnext,delta,direction=direction,
        normalized_force=.4,member=c.member,numerical_view=c.primary_view)
    for n in ('positions','momenta'):
        np.testing.assert_allclose(getattr(reconstructed,n),(getattr(rnext,n)-getattr(lnext,n))/(2*eps),atol=1e-13,rtol=1e-12)


@pytest.mark.parametrize('regime',REGIMES)
def test_actual_scheduled_force_map_against_independent_potential_fd_baoab(regime):
    c=coordinate(regime)
    _,state,direction,noise,_=corpus()
    dt,eta,temp=map(float,(c.primary_view.timestep,c.primary_view.friction_gamma,c.primary_view.bath_temperature))
    def gradient(position,p):
        out=np.zeros_like(position)
        for sector in (0,1):
            for component in range(3):
                for basis in hermitian_basis(4):
                    v=np.zeros_like(position);v[sector,component]=basis
                    eps=1e-6
                    value=(reference_action_terms(position+eps*v,p).total-reference_action_terms(position-eps*v,p).total)/(2*eps)
                    out+=value*v
        return out
    # Unit kinetic mass; potential M appears only inside the potential derivative.
    momentum=state.momenta+.5*dt*.17*direction-.5*dt*gradient(state.positions,derivatives.parameters(state,c.member))
    position=state.positions+.5*dt*momentum
    a=np.exp(-eta*dt)
    momentum=a*momentum+np.sqrt(temp*(1-a*a))*noise
    position=position+.5*dt*momentum
    next_p=SixMatrixParameters(2,float(c.member.mass_x),float(c.member.mass_y),float(c.member.cross_coupling_gamma),.7,1.1)
    momentum=momentum-.5*dt*gradient(position,next_p)+.5*dt*.17*direction
    actual=derivatives.scheduled_force_step(state,direction=direction,amplitude=.17,member=c.member,numerical_view=c.primary_view,
        next_alpha_tilde_x=.7,next_alpha_tilde_y=1.1,standardized_noise=noise)
    np.testing.assert_allclose(actual.positions,position,atol=1e-12,rtol=1e-11)
    np.testing.assert_allclose(actual.momenta,momentum,atol=1e-10,rtol=1e-9)


@pytest.mark.parametrize('regime',REGIMES)
def test_paired_ou_and_parameter_clock_with_actual_friction_and_bath(regime):
    c = coordinate(regime)
    rng = np.random.Generator(np.random.PCG64(71))
    coarse,bridge = (hermitian_noise(rng=rng,q=2) for _ in range(2))
    first,second = history.split_parameter_innovations(c,coarse,bridge)
    a = np.exp(-float(c.primary_view.friction_gamma)*float(c.primary_view.timestep)/2)
    np.testing.assert_allclose(a*first+second,np.sqrt(1+a*a)*coarse,atol=1e-14,rtol=1e-14)
    np.testing.assert_allclose(np.linalg.norm(first)**2+np.linalg.norm(second)**2,
        np.linalg.norm(coarse)**2+np.linalg.norm(bridge)**2,atol=1e-12)
    p = hermitian_noise(rng=rng,q=2)
    t = float(c.primary_view.bath_temperature)
    twice = a*(a*p+np.sqrt(t*(1-a*a))*first)+np.sqrt(t*(1-a*a))*second
    once = a*a*p+np.sqrt(t*(1-a**4))*coarse
    np.testing.assert_allclose(twice,once,atol=1e-13,rtol=1e-13)
    primary=fine=history.initial_parameter_state(c)
    for tick in range(1,c.total_ticks+1):
        primary,half,fine = history.advance_parameter_pair(primary,fine,coordinate=c,coarse_step=tick,
            coarse_noise=coarse,bridge_noise=bridge)
        assert c.physical_time(primary.step_index)==c.physical_time(fine.step_index,refinement=2)
        assert (half.alpha_tilde_x,half.alpha_tilde_y)==c.couplings(half.step_index,refinement=2)
        assert (primary.alpha_tilde_x,primary.alpha_tilde_y)==c.couplings(primary.step_index)


def test_native_hermitian_noise_has_identity_real_hs_covariance_including_trace():
    # Every independent normal coefficient is probed separately. The resulting
    # orthogonal map proves Gaussian covariance without a Monte Carlo tolerance.
    class Coefficients:
        def __init__(self, values):
            self.values, self.offset = values, 0
        def normal(self, *, size):
            values = self.values[self.offset:self.offset+size]
            self.offset += size
            return values

    basis = hermitian_basis(4)
    columns = []
    for values in np.eye(96):
        supplied = Coefficients(values)
        native = hermitian_noise(rng=supplied, q=2)
        assert supplied.offset == 96
        columns.append(np.einsum('kab,sjab->sjk', basis.conj(), native).real.reshape(96))
    transform = np.asarray(columns).T
    np.testing.assert_allclose(transform @ transform.T, np.eye(96), atol=5e-16, rtol=0)
    trace_coefficients = np.asarray([np.trace(hermitian_noise(rng=Coefficients(values), q=2),
        axis1=-2, axis2=-1).real.reshape(6)/2 for values in np.eye(96)]).T
    np.testing.assert_allclose(trace_coefficients @ trace_coefficients.T, np.eye(6), atol=1e-15, rtol=0)


@pytest.mark.parametrize('regime', REGIMES)
def test_actual_native_ou_conditional_moments_from_exact_symmetric_quadrature(regime):
    c = coordinate(regime)
    _, state, _, _, _ = corpus(293)
    dt, gamma, temperature = map(float, (c.primary_view.timestep, c.primary_view.friction_gamma, c.primary_view.bath_temperature))
    current = derivatives.parameters(state, c.member)
    before_ou = state.momenta - dt/2*analytic_gradient_terms(state.positions, current).total
    expected_mean = np.exp(-gamma*dt)*before_ou
    basis = hermitian_basis(4)
    innovations = []
    for sector in range(2):
        for component in range(3):
            for direction in basis:
                noise = np.zeros_like(state.positions)
                noise[sector, component] = np.sqrt(96)*direction
                innovations.extend((noise, -noise))
    residuals = []
    for noise in innovations:
        actual = simulation.baoab_step_with_hermitian_noise(state, member=c.member, numerical_view=c.primary_view,
            next_alpha_tilde_x=state.alpha_tilde_x, next_alpha_tilde_y=state.alpha_tilde_y, standardized_noise=noise)
        # Undo the final conservative kick to inspect the OU stage. Separate
        # finite-potential controls above test that native conservative force.
        after_ou = actual.momenta + dt/2*analytic_gradient_terms(actual.positions, current).total
        residuals.append(np.einsum('kab,sjab->sjk', basis.conj(), after_ou-expected_mean).real.reshape(96))
    residuals = np.asarray(residuals)
    np.testing.assert_allclose(residuals.mean(axis=0), 0, atol=1e-15, rtol=0)
    variance = temperature * (1-np.exp(-2*gamma*dt))
    np.testing.assert_allclose(residuals.T @ residuals / len(residuals), variance*np.eye(96), atol=2e-15, rtol=2e-13)
    assert np.exp(-2*gamma*dt)*temperature+variance == pytest.approx(temperature, rel=2e-15)


@pytest.mark.parametrize('family',range(4))
def test_historical_parameter_point_exact_paired_map_compatibility(family):
    member,views = history_native_parameters()
    c = history.MatrixParameterCoordinate('test.e4.legacy-coordinate',2,member,*views,'test.e4.legacy-clock',
        history.FOUR_FAMILY_PREPARATION_IDS[family],D(2)/3,D(22)/3,D(8),256,768,(0,256,1024),
        history.INITIAL_RULE_ID,history.PREPARATION_RULE_ID)
    root = SimpleNamespace(history_index=family*64,family_id=c.family_id)
    protocol = SimpleNamespace(ramp_ticks=256,target_x=c.target_x,target_y=c.target_y,decreasing_start=D(8))
    old_initial=initial_history_state(root);new_initial=history.initial_parameter_state(c)
    np.testing.assert_array_equal(old_initial.positions,new_initial.positions)
    np.testing.assert_array_equal(old_initial.momenta,new_initial.momenta)
    streams = {stage+'-'+role:np.random.Generator(np.random.PCG64DXSM(40+i))
        for i,(stage,role) in enumerate((s,r) for s in ('preparation','autonomous') for r in ('coarse-driver','fine-bridge'))}
    mirrors = {k:np.random.Generator(np.random.PCG64DXSM()) for k in streams}
    for k in streams:mirrors[k].bit_generator.state=streams[k].bit_generator.state
    for tick in (1,255,256,257):
        primary=replace(old_initial,step_index=tick-1,alpha_tilde_x=c.couplings(tick-1)[0],alpha_tilde_y=c.couplings(tick-1)[1])
        fine=replace(primary,step_index=2*(tick-1))
        stage='preparation' if tick<=256 else 'autonomous'
        coarse=hermitian_noise(rng=mirrors[stage+'-coarse-driver'],q=2)
        bridge=hermitian_noise(rng=mirrors[stage+'-fine-bridge'],q=2)
        old=advance_history_pair(primary,fine,root=root,coarse_step=tick,protocol=protocol,streams=streams,
            caches=(BAOABGradientCache(),BAOABGradientCache()),member=member,views=views)
        new=history.advance_parameter_pair(primary,fine,coordinate=c,coarse_step=tick,coarse_noise=coarse,bridge_noise=bridge)
        for left,right in zip(old,new,strict=True):
            np.testing.assert_array_equal(left.positions,right.positions)
            np.testing.assert_array_equal(left.momenta,right.momenta)
            assert left.step_index==right.step_index


def test_default_force_and_hessian_compatibility_cache_and_unitary_covariance():
    _,state,direction,noise,delta=corpus()
    member,views=history_native_parameters()
    nominal=replace(state,alpha_tilde_x=2/3,alpha_tilde_y=22/3)
    full=np.zeros_like(direction);full[0]=direction[0]/np.linalg.norm(direction[0])
    old=preparation_force_step(nominal,amplitude=.2,mode=full[0],member=member,numerical_view=views[0],standardized_noise=noise)
    new=derivatives.scheduled_force_step(nominal,direction=full,amplitude=.2,member=member,numerical_view=views[0],
        next_alpha_tilde_x=nominal.alpha_tilde_x,next_alpha_tilde_y=nominal.alpha_tilde_y,standardized_noise=noise)
    np.testing.assert_array_equal(old.positions,new.positions);np.testing.assert_array_equal(old.momenta,new.momenta)
    p=derivatives.parameters(nominal,member)
    np.testing.assert_allclose(derivatives.hessian_image(nominal.positions,delta.positions,p),_hessian_image(nominal.positions,delta.positions),atol=1e-13,rtol=1e-13)
    cache=BAOABGradientCache()
    for regime in REGIMES:
        c=coordinate(regime)
        kwargs=dict(direction=direction,amplitude=.2,member=c.member,numerical_view=c.primary_view,
            next_alpha_tilde_x=.7,next_alpha_tilde_y=1.1,standardized_noise=noise)
        cached=derivatives.scheduled_force_step(state,gradient_cache=cache,**kwargs)
        uncached=derivatives.scheduled_force_step(state,**kwargs)
        np.testing.assert_array_equal(cached.positions,uncached.positions);np.testing.assert_array_equal(cached.momenta,uncached.momenta)
    rng=np.random.Generator(np.random.PCG64(49));unitary,_=np.linalg.qr(rng.normal(size=(4,4))+1j*rng.normal(size=(4,4)))
    transform=lambda v:hermitian_part(unitary@v@unitary.conj().T)
    image=derivatives.hessian_image(state.positions,delta.positions,derivatives.parameters(state,c.member))
    changed=derivatives.hessian_image(transform(state.positions),transform(delta.positions),derivatives.parameters(state,c.member))
    np.testing.assert_allclose(changed,transform(image),atol=1e-12,rtol=1e-12)


def test_coordinate_canonical_clock_domain_and_schedule_refusals():
    c=coordinate(REGIMES[0])
    assert decode_canonical_bytes(c.canonical_bytes(),history.MatrixParameterCoordinate,maximum_bytes=None)==c
    for changes in ({'q':3},{'initial_state_rule_id':'foreign.initial'}, {'observation_ticks':(0,4)},
            {'fine_view':replace(c.fine_view,bath_temperature=D(9))}, {'fine_view':replace(c.fine_view,timestep=D('.0007'))}):
        with pytest.raises(ValueError):replace(c,**changes)
    with pytest.raises(ValueError):replace(c.primary_view,friction_gamma=D(0))
    with pytest.raises(ValueError):replace(c.member,cross_coupling_gamma=D(0))
    with pytest.raises(ValueError):replace(c.primary_view,bath_temperature=D(0))
    initial=history.initial_parameter_state(c);noise=np.zeros_like(initial.positions)
    with pytest.raises(ValueError,match='clock'):
        history.advance_parameter_pair(replace(initial,alpha_tilde_x=.1),initial,coordinate=c,coarse_step=1,
            coarse_noise=noise,bridge_noise=noise)
    with pytest.raises(ValueError,match='geometry'):
        history.split_parameter_innovations(c,noise.real,noise)
