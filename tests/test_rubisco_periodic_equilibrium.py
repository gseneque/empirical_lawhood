# SPDX-License-Identifier: MPL-2.0
"""Exposed Langevin mechanics, harmonic invariant moments and original-prefix controls."""

from copy import deepcopy
from dataclasses import replace
from decimal import Decimal as D, localcontext
from fractions import Fraction
from functools import partial
import math
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.domains.rubisco.rubisco_insilico_free_energy.contracts import UmbrellaWindow
from empirical_lawhood.adapters.rubisco.rubisco_response.fixed_coordinate_mm import COULOMB_KJ_NM_PER_MOL_E2
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_bias import ReferenceBiasConvention, evaluate_reference_umbrella_bias
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_dynamics import ReferenceDynamicsSettings
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_equilibrium import ReferenceEquilibriumSettings, propagate_reference_equilibrium
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_equilibrium_assessment import ReferenceEquilibriumCriteria, assess_reference_equilibrium_frames
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_native import GRADIENT_UNIT
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.identity.provenance import ObjectIdentity

BOHR = .52917721092
HARTREE = COULOMB_KJ_NM_PER_MOL_E2/(BOHR/10)
R = .00831446261815324


class Harmonic:
    def __init__(self, center, stiffness=4000.):
        self.center, self.stiffness = np.array(center, dtype=float), stiffness
        self.calls = []

    def evaluate(self, xyz):
        self.calls.append(xyz.copy())
        delta = (xyz-self.center)/10
        return dict(energy_hartree=float(.5*np.sum(self.stiffness*delta**2)/HARTREE),
            gradient_hartree_per_bohr=np.asarray(self.stiffness*delta*(BOHR/10)/HARTREE),
            bohr_angstrom=BOHR, hartree_kj_mol=HARTREE, gradient_unit=GRADIENT_UNIT)


def selection(*, steps=12, biased=False):
    settings = ReferenceEquilibriumSettings('equilibrium.exposed',
        ReferenceDynamicsSettings('dynamics.exposed', D('5e-16'), steps), D('298.15'), D(2), 91823,
        'NUMPY_PCG64DXSM_STANDARD_NORMAL_FLOAT64', min(3, steps-1), 1 if steps<4 else 2, None, None)
    xyz = np.array(((.1, .2, .3), (1.4, -.1, .2), (.3, 1.4, -.7)))
    bias = None
    if biased:
        window = UmbrellaWindow('window.thermal.exposed', 'model.thermal.exposed', 'REACTANT',
            (('a','b'),), ('DISTANCE',), (D('1.2'),), (D(30),), 2, 6, 2, 123, D('.01'))
        convention = ReferenceBiasConvention('bias.thermal.exposed', ObjectIdentity.from_record(window.window_id,window),
            ('ANGSTROM',), ('KJ_PER_MOL_PER_ANGSTROM_SQUARED',), 'DISTANCE_12_MINUS_DISTANCE_23',
            'SIGNED_ORDERED_TORSION_SHORTEST_ANGULAR_RESTRAINT', 'ORTHORHOMBIC_MINIMUM_IMAGE_EACH_CONSECUTIVE_BOND')
        settings = replace(settings, bias_window=convention.window, bias_convention=convention.identity)
        evaluate = partial(evaluate_reference_umbrella_bias, window=window, convention=convention,
            physical_model_id=window.model_id, physical_atom_ids=('a','b','c'), cell_vectors_angstrom=np.eye(3)*20)
        bias = lambda positions: evaluate(coordinates_angstrom=positions)
    return dict(operator=Harmonic(xyz*.9), bias=bias, initial_angstrom=xyz,
        initial_velocity_nm_per_ps=np.linspace(-.2,.3,9).reshape((3,3)),
        physical_masses_dalton=np.array((1.008,12.011,15.999)), settings=settings)


def acquire(selected, **callbacks):
    frames, noises, events = [], [], []
    result = propagate_reference_equilibrium(**selected, capture=callbacks.get('capture', frames.append),
        capture_noise=callbacks.get('capture_noise', noises.append), observe=callbacks.get('observe', events.append))
    return result, frames, noises, events


def assess(frames, selected, criteria=True):
    return assess_reference_equilibrium_frames(frames, **{name:selected[name] for name in
        ('initial_angstrom','initial_velocity_nm_per_ps','physical_masses_dalton','settings')},
        criteria=ReferenceEquilibriumCriteria('criteria.exposed',D('1e-12'),D('1e-10'),D('1e-10')) if criteria else None)


def test_explicit_settings_canonical_exact_clock_thermal_constant_and_sample_schedule():
    selected = selection()
    settings = selected['settings']
    assert decode_canonical_bytes(settings.canonical_bytes(),ReferenceEquilibriumSettings,maximum_bytes=8192)==settings
    criteria = ReferenceEquilibriumCriteria('criteria.exposed',D('1e-12'),D('1e-10'),D('1e-10'))
    assert decode_canonical_bytes(criteria.canonical_bytes(),ReferenceEquilibriumCriteria,maximum_bytes=4096)==criteria
    with localcontext() as context:
        context.prec = 3
        assert settings.thermal_energy_kj_mol == float(Fraction(D('.00831446261815324'))*Fraction(D('298.15')))
        assert str(settings.dynamics.time_at_step(11))=='5.5E-15'
    assert [i for i in range(13) if settings.sample_ordinal(i) is not None] == [5,7,9,11]
    assert settings.expected_samples == 4


@pytest.mark.parametrize('biased', [False,True])
def test_complete_trace_original_components_noise_and_independent_recurrence(biased):
    selected = selection(biased=biased)
    originals = [selected[key].copy() for key in ('initial_angstrom','initial_velocity_nm_per_ps','physical_masses_dalton')]
    result,frames,noises,events = acquire(selected)
    assert len(selected['operator'].calls)==len(frames)==13 and len(noises)==12
    assert [frame['sample_ordinal'] for frame in frames if frame['sample_ordinal'] is not None]==[1,2,3,4]
    assert result[2]['captured_sample_frames']==result[2]['selected_sample_frames']==4
    for frame,noise in zip(frames[1:],noises,strict=True):
        np.testing.assert_array_equal(frame['noise_standard_normal'],noise['standard_normal'])
        assert noise['step']==frame['step'] and noise['numpy_version']==np.__version__
    assert all(events.index(e)<next(i for i,x in enumerate(events) if x['event']=='equilibrium-evaluation-entry' and x['step']==e['step'])
        for e in events if e['event']=='equilibrium-noise-return')
    before = len(selected['operator'].calls)
    report = assess(iter(frames), selected)
    assert len(selected['operator'].calls)==before and report['new_operator_evaluations']==report['new_bias_evaluations']==0
    assert report['selected_trace_criteria']=='SATISFIED' and report['findings']==()
    assert report['retained_frames']==13 and report['retained_noise_draws']==12 and report['retained_sample_frames']==4
    assert report['equilibrium_admission']==report['physical_rate_admission']==report['step_convergence']=='UNEVALUABLE'
    assert result[2]['physical_rate_clock']=='NOT_SUPPLIED_BY_EQUILIBRIUM_SAMPLER'
    for name,original in zip(('initial_angstrom','initial_velocity_nm_per_ps','physical_masses_dalton'),originals,strict=True):
        np.testing.assert_array_equal(selected[name],original)


def test_free_particle_exact_ou_transition_mass_dependence_and_heat():
    selected = selection(steps=1)
    selected['operator'].stiffness=0.
    result,frames,noises,_ = acquire(selected)
    settings = selected['settings']
    h = float(settings.dynamics.step_seconds)*1e12
    c = math.exp(-float(settings.friction_per_picosecond)*h)
    eta = np.sqrt((1-c*c)*R*float(settings.temperature_kelvin)/selected['physical_masses_dalton'])[:,None]*noises[0]['standard_normal']
    expected_v = c*selected['initial_velocity_nm_per_ps']+eta
    expected_x = selected['initial_angstrom']+5*h*(selected['initial_velocity_nm_per_ps']+expected_v)
    np.testing.assert_allclose(result[1],expected_v,atol=1e-14,rtol=1e-13)
    np.testing.assert_allclose(result[0],expected_x,atol=1e-14,rtol=1e-13)
    heat = .5*np.sum(selected['physical_masses_dalton'][:,None]*(expected_v**2-selected['initial_velocity_nm_per_ps']**2))
    assert frames[1]['thermostat_heat_kj_mol']==pytest.approx(heat,abs=1e-13)


def test_harmonic_invariant_covariance_with_exact_gaussian_second_moment_quadrature(monkeypatch):
    # Six sigma points integrate Gaussian quadratic moments exactly. This is
    # an exposed quadrature control, not a random ensemble or seed-provenance test.
    selected = selection(steps=1)
    mass,stiffness = 2.,1e6
    h = selected['settings'].dynamics.step_picoseconds
    thermal = R*float(selected['settings'].temperature_kelvin)
    var_x = thermal/stiffness
    var_v = thermal/mass*(1-h*h*stiffness/(4*mass))
    xyz,velocity,noise = (np.zeros((6,3)) for _ in range(3))
    xyz[:2,0] = np.array((1,-1))*math.sqrt(3*var_x)*10
    velocity[2:4,0] = np.array((1,-1))*math.sqrt(3*var_v)
    noise[4:,0] = np.array((1,-1))*math.sqrt(3)
    selected.update(operator=Harmonic(np.zeros_like(xyz),stiffness),initial_angstrom=xyz,
        initial_velocity_nm_per_ps=velocity,physical_masses_dalton=np.full(6,mass))
    class Quadrature:
        def __init__(self, generator):self.bit_generator=SimpleNamespace(state={'exposed_quadrature':True})
        def standard_normal(self, *, size, dtype):
            assert size==noise.shape and dtype==np.float64
            return noise.copy()
    monkeypatch.setattr(np.random,'Generator',Quadrature)
    result,_,_,_ = acquire(selected)
    x,v = result[0][:,0]/10,result[1][:,0]
    assert np.mean(x)==pytest.approx(0,abs=1e-17) and np.mean(v)==pytest.approx(0,abs=1e-15)
    assert np.mean(x*x)==pytest.approx(var_x,rel=1e-14)
    assert np.mean(v*v)==pytest.approx(var_v,rel=1e-14)
    assert np.mean(x*v)==pytest.approx(0,abs=1e-17)


def test_reproducible_real_normal_stream_and_component_census():
    selected = selection(steps=1)
    n = 10000
    selected.update(operator=Harmonic(np.zeros((n,3)),0.),initial_angstrom=np.zeros((n,3)),
        initial_velocity_nm_per_ps=np.zeros((n,3)),physical_masses_dalton=np.ones(n))
    first,_,noises,_ = acquire(selected)
    second,_,again,_ = acquire(selected)
    np.testing.assert_array_equal(first[0],second[0]);np.testing.assert_array_equal(first[1],second[1])
    np.testing.assert_array_equal(noises[0]['standard_normal'],again[0]['standard_normal'])
    z = noises[0]['standard_normal']
    assert z.shape==(n,3) and len(set(z.flatten()))==z.size
    assert abs(np.mean(z))<.04 and abs(np.mean(z*z)-1)<.06
    selected['settings']=replace(selected['settings'],random_seed=91824)
    _,_,different,_ = acquire(selected)
    assert not np.array_equal(z,different[0]['standard_normal'])


def test_capture_mutation_cannot_change_continued_force_bias_or_noise():
    selected = selection(biased=True)
    expected,_,_,_ = acquire(selected)
    def corrupt(frame):
        for key,value in frame.items():
            if isinstance(value,np.ndarray):value[:]=123
        frame['settings'].clear();frame['bias_window'].clear();frame['bias_convention'].clear()
    def corrupt_noise(row):
        row['standard_normal'][:]=321;row['state_before'].clear();row['state_after'].clear()
    actual,_,_,_ = acquire(selected,capture=corrupt,capture_noise=corrupt_noise)
    np.testing.assert_array_equal(actual[0],expected[0]);np.testing.assert_array_equal(actual[1],expected[1])


def test_reference_failure_retains_draw_before_contact_and_never_retries():
    selected = selection()
    operator = selected['operator']
    base = operator.evaluate
    calls = 0
    def failure(xyz):
        nonlocal calls
        calls+=1
        if calls==2:raise RuntimeError('exposed failure')
        return base(xyz)
    operator.evaluate=failure
    frames,noises,events = [],[],[]
    with pytest.raises(RuntimeError,match='exposed failure'):
        propagate_reference_equilibrium(**selected,capture=frames.append,capture_noise=noises.append,observe=events.append)
    assert calls==2 and len(frames)==len(noises)==1
    error=events[-1]
    assert error['operator_invocations']==2 and error['operator_returns']==error['completed_evaluations']==1
    assert error['retained_noise_draws']==error['noise_draws']==1 and error['captured_frames']==1
    assert assess(frames,selected)['selected_trace_criteria']=='UNEVALUABLE'


@pytest.mark.parametrize('which', ['noise','frame'])
def test_capture_failure_counts_exact_completed_work_without_retry(which):
    selected = selection()
    events=[]
    def fail(row):
        if row.get('step')==1:raise OSError('exposed capture failure')
    with pytest.raises(OSError,match='capture failure'):
        propagate_reference_equilibrium(**selected,observe=events.append,
            capture_noise=fail if which=='noise' else lambda row:None,
            capture=fail if which=='frame' else lambda row:None)
    error=events[-1]
    assert error['noise_draws']==1 and error['captured_frames']==1
    assert error['completed_evaluations']==(1 if which=='noise' else 2)
    assert error['operator_invocations']==error['completed_evaluations']
    assert error['retained_noise_draws']==(0 if which=='noise' else 1)


@pytest.mark.parametrize('change', [
    {'temperature_kelvin':D(0)},{'temperature_kelvin':D('NaN')},{'temperature_kelvin':D('1e-400')},
    {'friction_per_picosecond':D(0)},{'friction_per_picosecond':D('1e-20')},
    {'random_seed':True},{'random_seed':-1},{'random_seed':2**128},{'random_generator':'DEFAULT_RNG'},
    {'discard_initial_steps':12},{'discard_initial_steps':-1},{'sample_interval_steps':0},{'sample_interval_steps':100},
])
def test_undeclared_or_unrepresentable_sampling_settings_refused(change):
    with pytest.raises((TypeError,ValueError)):
        replace(selection()['settings'],**change)


@pytest.mark.parametrize('field,value', [
    ('initial_angstrom',np.zeros((2,3))),('initial_velocity_nm_per_ps',np.zeros((3,2))),
    ('physical_masses_dalton',np.array((0.,1.,1.))),('physical_masses_dalton',np.array((1.,float('nan'),1.))),
    ('initial_angstrom',np.zeros((3,3))+1j),('initial_velocity_nm_per_ps',np.full((3,3),float('inf'))),
    ('initial_velocity_nm_per_ps',np.full((3,3),1e308)),
])
def test_invalid_phase_space_refuses_before_reference_entry(field,value):
    selected=selection();selected[field]=value
    with pytest.raises((ValueError,FloatingPointError)):
        acquire(selected)
    assert not selected['operator'].calls


@pytest.mark.parametrize('mode', ['unit','gradient','nonfinite','complex','mutates'])
def test_bad_reference_returns_preserve_invocation_denominator(mode):
    selected=selection();base=selected['operator'].evaluate
    def changed(xyz):
        returned=base(xyz)
        if mode=='unit':returned['bohr_angstrom']=.5
        if mode=='gradient':returned['gradient_hartree_per_bohr']=np.zeros((2,3))
        if mode=='nonfinite':returned['energy_hartree']=float('nan')
        if mode=='complex':returned['gradient_hartree_per_bohr']=np.zeros((3,3))+1j
        if mode=='mutates':xyz[0,0]+=1
        return returned
    selected['operator'].evaluate=changed
    events=[]
    with pytest.raises(ValueError):acquire(selected,observe=events.append)
    assert len(selected['operator'].calls)==1
    assert events[-1]['operator_invocations']==events[-1]['operator_returns']==1
    assert events[-1]['completed_evaluations']==events[-1]['captured_frames']==0


@pytest.mark.parametrize('mode', ['identity','includes_reference','gradient','mutates'])
def test_bad_bias_refuses_before_expensive_reference_entry(mode):
    selected=selection(biased=True);base=selected['bias']
    def changed(xyz):
        returned=base(xyz)
        if mode=='identity':returned['window']={}
        if mode=='includes_reference':returned['reference_energy_included']=True
        if mode=='gradient':returned['gradient_kj_mol_per_angstrom']=np.zeros((2,3))
        if mode=='mutates':xyz[0,0]+=1
        return returned
    selected['bias']=changed
    events=[]
    with pytest.raises(ValueError):acquire(selected,observe=events.append)
    assert not selected['operator'].calls and events[-1]['operator_invocations']==0


@pytest.mark.parametrize('field', ['coordinates_angstrom','velocities_nm_per_ps','noise_standard_normal',
    'reference_gradient_hartree_per_bohr','bias_gradient_kj_mol_per_angstrom','thermostat_heat_kj_mol'])
def test_finite_original_trace_disagreement_is_falsified(field):
    selected=selection(biased=True)
    _,frames,_,_=acquire(selected)
    changed=deepcopy(frames)
    if field=='thermostat_heat_kj_mol':changed[3][field]+=.01
    else:changed[3][field][0,0]+=.01
    report=assess(changed,selected)
    assert report['selected_trace_criteria']=='FALSIFIED' and report['findings']
    assert report['new_operator_evaluations']==report['new_bias_evaluations']==0


@pytest.mark.parametrize('field,value', [('step',2),('evaluation',1),('noise_draw',True),
    ('sampling_time_seconds','0.123'),('sample_ordinal',True),('gradient_unit','kcal'),
    ('bias_window',{}),('noise_standard_normal',None),('reference_energy_hartree',float('inf')),
    ('coordinates_angstrom',np.zeros((3,3),dtype=np.float32))])
def test_structural_frame_substitutions_refused(field,value):
    selected=selection();_,frames,_,_=acquire(selected)
    changed=deepcopy(frames);changed[1][field]=value
    with pytest.raises(ValueError):assess(changed,selected)


def test_exact_time_equivalence_prefix_census_seed_binding_and_no_unselected_acceptance():
    selected=selection();_,frames,_,_=acquire(selected)
    frames[1]['sampling_time_seconds']='0.000000000000000500000'
    assert assess(frames,selected)['selected_trace_criteria']=='SATISFIED'
    prefix=assess(frames[:8],selected)
    assert prefix['selected_trace_criteria']=='UNEVALUABLE' and prefix['retained_frames']==8
    assert prefix['retained_sample_frames']==2 and prefix['retained_noise_draws']==7
    assert prefix['observed_sampling_time_seconds']=='3.5E-15'
    assert assess([],selected)['retained_frames']==0
    assert assess(frames,selected,criteria=False)['selected_trace_criteria']=='UNEVALUABLE'
    selected['settings']=replace(selected['settings'],random_seed=1)
    with pytest.raises(ValueError,match='census'):assess(frames,selected)
