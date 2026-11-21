# SPDX-License-Identifier: MPL-2.0
"""Independent finite-population and retained-custody controls, not enzyme evidence."""

from dataclasses import replace
from decimal import Decimal as D, localcontext
import math
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.domains.rubisco.rubisco_response import reactive_flux_records as records
from empirical_lawhood.domains.rubisco.rubisco_response import reactive_flux_preparation as preparation
from empirical_lawhood.domains.rubisco.rubisco_response import reactive_flux_science as science
from empirical_lawhood.domains.rubisco.rubisco_response import reactive_flux_read as retained
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_dynamics import ReferenceDynamicsSettings
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_dynamics_assessment import ReferenceTrajectoryCriteria
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_bias_assessment import ReferenceBiasGeometryCriteria
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.storage.artifacts import ArtifactIdentityConflict
from tests import test_rubisco_equilibrium_reweighting as equilibrium
from tests import test_rubisco_periodic_trajectory as trajectory


fixture = equilibrium.fixture


def limits(**changes):
    return replace(records.ReactiveFluxCriteria('criteria.exposed.flux',2,D(1),D('.2'),D('.2'),D('.1'),D('.1'),D('.01'),D('1e-12')),**changes)


def geometry_criteria(ensemble):
    n = len(ensemble.coordinate_window.cv_kinds)
    return ReferenceBiasGeometryCriteria('criteria.exposed.flux-geometry',ensemble.coordinate_convention.identity,
        D('1e-5'),(D('1e-10'),)*n,(D('1e-7'),)*n,(D('1e-7'),)*n,D('1e-9'),D('1e-6'),D('1e-6'))


def surface_for(ensemble,**changes):
    return replace(records.ReactiveFluxSurface('surface.exposed.flux',ensemble.ensemble_id,0,D(1),D('.1'),1,
        'basin.left','basin.right',equilibrium.pin('quantity.exposed.flux'),equilibrium.pin('states.exposed.flux'),
        geometry_criteria(ensemble)),**changes)


def finite_case():
    ensemble = equilibrium.ensemble(basins=(equilibrium.records.EquilibriumBasin('basin.left',(D(0),),(D('.5'),)),
        equilibrium.records.EquilibriumBasin('basin.right',(D('1.5'),),(D(2),))))
    surface = surface_for(ensemble)
    dynamics = ReferenceDynamicsSettings('dynamics.exposed.flux',D('5e-16'),3)
    times = (D('5e-16'),D('1e-15'),D('1.5e-15'))
    q = np.array([[.2],[.8],[.96],[1.04],[1.2],[1.8]])
    weights = np.array([.15,.2,.1,.15,.2,.2])
    keys = tuple(('trace.exposed',i+1) for i in range(len(q)))
    geometries,observations = {},{}
    for i in (2,3):
        key = keys[i]
        geometries[(surface.surface_id,*key)] = dict(analytic_positive_speed_per_second=2e14,
            derivative_assessment=dict(selected_bias_geometry_criteria='SATISFIED'))
        velocity = np.array([-4e14,4e14])
        x = q[i,0]+velocity[:,None]*np.array([0.,5e-16,1e-15,1.5e-15])[None,:]
        observations[(surface.surface_id,dynamics.settings_id,*key)] = dict(complete=True,
            initial_coordinate_velocities_per_second=tuple(velocity),product_side=x>1,
            first_stable_basin=tuple('REACTANT' if v<.5 else 'PRODUCT' if v>=1.5 else None for v in x[:,-1]))
    return dict(surface=surface,ensemble=ensemble,dynamics=dynamics,criteria=limits(),plateau_times=times,
        coordinates=q,weights=weights,sample_keys=keys,geometry=geometries,observations=observations,momentum_pairs=1)


@pytest.mark.numerical(oracle='Explicit six-point weighted ballistic population, thermal constants and -RT log(5/3) barrier')
def test_finite_ballistic_flux_and_positive_prefactor_have_independent_population_oracle():
    case = finite_case()
    row = science.reduce_flux(**case)
    assert row['selected_flux_criteria']=='SATISFIED'
    assert row['slab_probability']==pytest.approx(.25)
    assert row['reactant_probability']==pytest.approx(.15)
    assert row['positive_flux_prefactor_per_second']==pytest.approx(1e15)
    assert row['transition_state_rate_per_second']==pytest.approx(.25/.15*1e15)
    assert row['flux_side_rates_per_second']==pytest.approx((.25/.15*1e15,)*3)
    assert row['transmission_curve']==pytest.approx((1.,1.,1.))
    assert row['committor_rms_deviation']==row['uncommitted_probability']==0
    rt = 8.31446261815324e-3*298.15
    assert row['finite_slab_barrier_kj_mol']==pytest.approx(-rt*math.log(5/3))
    assert row['eyring_dimensionless_prefactor']==pytest.approx(1e15*6.62607015e-34/(1.380649e-23*298.15))
    assert row['physical_rate_admission']=='UNEVALUABLE'


@pytest.mark.numerical(oracle='Analytic harmonic trajectories with transmission values 1, 0, -1')
def test_harmonic_recrossing_retains_negative_flux_and_refuses_a_plateau():
    case = finite_case()
    omega = math.pi/(1e-15)
    for (_,_,trace,ordinal),row in case['observations'].items():
        x0 = case['coordinates'][ordinal-1,0]-1
        times = np.array([0.,5e-16,1e-15,1.5e-15])
        v = np.asarray(row['initial_coordinate_velocities_per_second'])
        x = x0*np.cos(omega*times)[None,:]+v[:,None]/omega*np.sin(omega*times)[None,:]
        row['product_side'] = x>0
    row = science.reduce_flux(**case)
    assert row['transmission_curve']==pytest.approx((1.,0.,-1.))
    assert row['plateau_rate_per_second']==0
    assert row['selected_flux_criteria']=='FALSIFIED'
    assert 'SELECTED_INTERMEDIATE_TIMES_HAVE_NO_RESOLVED_PLATEAU' in row['findings']
    assert 'PLATEAU_TRANSMISSION_OUTSIDE_POSITIVE_UNIT_INTERVAL' in row['findings']


def test_missing_shot_and_zero_reactant_mass_never_become_zero_rates():
    case = finite_case()
    next(iter(case['observations'].values()))['complete'] = False
    row = science.reduce_flux(**case)
    assert row['plateau_rate_per_second'] is None
    assert row['transition_state_rate_per_second'] is not None
    assert row['slab_probability']==.25 and row['slab_configurations']==2
    assert 'COMPLETE_SELECTED_SHOOTING_POPULATION_UNAVAILABLE' in row['missing']
    case = finite_case()
    case['weights'] = np.array([0.,.35,.1,.15,.2,.2])
    row = science.reduce_flux(**case)
    assert row['reactant_probability']==0 and row['plateau_rate_per_second'] is None
    assert row['transition_state_rate_per_second'] is None


def test_antithetic_sign_and_complete_probability_measure_are_required():
    case = finite_case()
    next(iter(case['observations'].values()))['initial_coordinate_velocities_per_second'] = (2e12,2e12)
    with pytest.raises(ValueError,match='antithetic'):
        science.reduce_flux(**case)
    case = finite_case()
    case['weights'] *= .9
    with pytest.raises(ValueError,match='normalized'):
        science.reduce_flux(**case)


def test_exact_decimal_positive_flux_threshold_is_not_rounded_to_pass():
    case = finite_case()
    for row in case['observations'].values():
        row['initial_coordinate_velocities_per_second'] = (-2e14,2e14)
    case['criteria'] = limits(maximum_positive_flux_relative_error=D('.4999999999999999999999999999'))
    with localcontext() as ctx:
        ctx.prec=6
        row = science.reduce_flux(**case)
    assert row['positive_flux_relative_error']==.5
    assert 'SAMPLED_POSITIVE_FLUX_DIFFERS_FROM_MAXWELL_MEASURE' in row['findings']


@pytest.mark.numerical(oracle='Maxwell-Boltzmann component variance RT/m over 60000 fixed-seed coordinates per mass; 2 percent tolerance')
def test_cartesian_maxwell_draw_has_natural_mass_variance_and_no_speed_projection():
    masses = np.concatenate((np.full(20000,1.),np.full(20000,4.)))
    values,record = preparation.momentum_draw(coordinates_sha256='3'*64,masses=masses,
        temperature=D('300.000'),seed=18912,pair=0)
    thermal = 8.31446261815324e-3*300
    assert np.var(values[:20000])==pytest.approx(thermal,rel=.02)
    assert np.var(values[20000:])==pytest.approx(thermal/4,rel=.02)
    assert np.linalg.norm(np.sum(masses[:,None]*values,axis=0))>1
    repeated,again = preparation.momentum_draw(coordinates_sha256='3'*64,masses=masses,
        temperature=D('300'),seed=18912,pair=0)
    assert np.array_equal(repeated,values) and again==record


def paired_flux_case():
    case = finite_case()
    first,second = (replace(case['ensemble'],ensemble_id='ensemble.'+k) for k in ('a','b'))
    traces = tuple(equilibrium.records.ReweightingTrace('trace.'+k,e.ensemble_id,
        equilibrium.pin('config.'+k,equilibrium.acquisition.owner.ReferenceEquilibriumConfig.SCHEMA),'group.paired',8,None)
        for k,e in zip(('a','b'),(first,second),strict=True))
    selected = equilibrium.records.EquilibriumReweightingSelection('selection.exposed.flux-joint',(first,second),traces,
        (equilibrium.contrast('contrast.a',(first,1)),equilibrium.contrast('contrast.b',(second,1)),
            equilibrium.contrast('contrast.paired',(first,-1),(second,1))),equilibrium.criteria(),
        equilibrium.pin('dependence.exposed.flux'),('Exposed jointly sampled finite configurations and deterministic shots.',))
    surfaces = tuple(surface_for(e,surface_id='surface.'+k) for k,e in zip(('a','b'),(first,second),strict=True))
    coarse = case['dynamics']
    fine = ReferenceDynamicsSettings('dynamics.exposed.refined',D('2.5e-16'),6)
    rule = records.ReactiveFluxRule('rule.exposed.paired-flux',selected,surfaces,(coarse,fine),coarse.settings_id,
        ReferenceTrajectoryCriteria('criteria.exposed.flux-mechanics',D('1e-12'),D('1e-12'),D('1e-8'),None),
        case['plateau_times'],1,18,limits(),(),'COLD',2**29,2**30,('Exposed paired numerical controls only.',))
    rng = np.random.Generator(np.random.PCG64DXSM(87029))
    q = rng.choice(case['coordinates'][:,0],size=(256,1))
    tables = {t.trace_id:dict(coordinates=q,reference_energy_kj_mol=q[:,0]**2) for t in traces}
    statistics,fits = equilibrium.science.joint_block_analysis(selection=selected,tables=tables,windows={t.trace_id:None for t in traces})
    projected,geometry,observations,point = {},{},{},{}
    for trace,surface,ensemble in zip(traces,surfaces,(first,second),strict=True):
        projected[trace.trace_id+'.coordinates'] = q
        projected[trace.trace_id+'.all_window_bias_potentials_kj_mol'] = np.zeros((1,len(q)))
        keys = tuple((trace.trace_id,i+1) for i in range(len(q)))
        for i,value in enumerate(q[:,0]):
            if abs(value-1)>.1:
                continue
            geometry[(surface.surface_id,*keys[i])] = dict(analytic_positive_speed_per_second=2e14,
                derivative_assessment=dict(selected_bias_geometry_criteria='SATISFIED'))
            for dynamics in rule.dynamics:
                x = value+np.asarray([-4e14,4e14])[:,None]*np.array([0.,5e-16,1e-15,1.5e-15])[None,:]
                observations[(surface.surface_id,dynamics.settings_id,*keys[i])] = dict(complete=True,
                    initial_coordinate_velocities_per_second=(-4e14,4e14),product_side=x>1,first_stable_basin=('REACTANT','PRODUCT'))
        for dynamics in rule.dynamics:
            point[(surface.surface_id,dynamics.settings_id)] = science.reduce_flux(surface=surface,ensemble=ensemble,dynamics=dynamics,
                criteria=rule.criteria,plateau_times=rule.plateau_times_seconds,coordinates=q,
                weights=fits[ensemble.ensemble_id]['target_weights'],sample_keys=keys,geometry=geometry,
                observations=observations,momentum_pairs=1)
    return rule,dict(equilibrium_report=dict(statistics=statistics),equilibrium_arrays=projected,geometry=geometry),observations,point


def test_joint_original_block_draws_keep_paired_material_and_step_covariance():
    rule,prepared,observations,point = paired_flux_case()
    report,arrays = science.joint_flux_resampling(rule=rule,prepared=prepared,observations=observations,point=point)
    assert report['status']=='SATISFIED' and report['failed_replicates']==()
    columns = report['columns']
    rate_columns = [i for i,c in enumerate(columns) if c['quantity']=='log_plateau_rate_per_second']
    draws = arrays['reactive-flux.joint_values']
    assert all(np.array_equal(draws[:,rate_columns[0]],draws[:,i]) for i in rate_columns)
    assert np.var(draws[:,rate_columns[0]])>0
    covariance = np.asarray(report['covariance'])
    assert covariance[rate_columns[0],rate_columns[0]]==covariance[rate_columns[0],rate_columns[-1]]
    assert np.all(draws[:,-1]==0) and report['retained_replicates']==32
    assert report['simultaneous_intervals'] is not None
    # Losing one actual momentum population keeps the full 32 draws and
    # blocks joint intervals; it cannot become an IID successful-shot subset.
    for key,row in observations.items():
        if key[0]=='surface.a':
            row['complete']=False
    failed,_ = science.joint_flux_resampling(rule=rule,prepared=prepared,observations=observations,point=point)
    assert len(failed['failed_replicates'])==32 and failed['simultaneous_intervals'] is None


def test_geometry_falsification_and_control_disagreement_remain_negative():
    case = finite_case()
    next(iter(case['geometry'].values()))['derivative_assessment']['selected_bias_geometry_criteria']='FALSIFIED'
    row = science.reduce_flux(**case)
    assert row['selected_flux_criteria']=='FALSIFIED' and 'DIVIDING_COORDINATE_GEOMETRY_FALSIFIED' in row['findings']
    rule,_,_,point = paired_flux_case()
    key = (rule.surfaces[0].surface_id,rule.dynamics[1].settings_id)
    point[key] = dict(point[key],plateau_rate_per_second=point[key]['plateau_rate_per_second']*2)
    _,steps = science.assess_flux_controls(rule,point)
    assert steps[rule.surfaces[0].surface_id]['status']=='FALSIFIED'


def rule_for(selected):
    ensemble = selected.ensembles[0]
    dimension = len(ensemble.coordinate_window.cv_kinds)
    basins = (equilibrium.records.EquilibriumBasin('basin.left',(D(-100),)*dimension,(D(1),)+(D(100),)*(dimension-1)),
        equilibrium.records.EquilibriumBasin('basin.right',(D(2),)+(D(-100),)*(dimension-1),(D(100),)*dimension))
    ensemble = replace(ensemble,basins=basins)
    selected = replace(selected,ensembles=(ensemble,))
    surface = surface_for(ensemble,center=D('1.6'),half_width=D('.2'))
    coarse = ReferenceDynamicsSettings('dynamics.coarse.flux',D('5e-16'),6)
    fine = ReferenceDynamicsSettings('dynamics.fine.flux',D('2.5e-16'),12)
    mechanics = ReferenceTrajectoryCriteria('criteria.exposed.flux-mechanics',D('1e-12'),D('1e-12'),D('1e-8'),None)
    return records.ReactiveFluxRule('rule.exposed.flux',selected,(surface,),(coarse,fine),coarse.settings_id,mechanics,
        (D('1e-15'),D('2e-15'),D('3e-15')),1,19287,limits(),(),'COLD',2**29,2**30,
        ('Exposed finite-slab transport controls, not enzyme rate or equilibrium evidence.',))


def original(fixture,monkeypatch,*,failure=None):
    config,phase,observed,custody,result = equilibrium.run_original(fixture,monkeypatch,failure=failure)
    rule = rule_for(equilibrium.original_selection(fixture,config))
    source = equilibrium.retained.RetainedEquilibriumTrace('trace.original',config,fixture.model,phase,result,custody.store)
    return rule,source,observed


def prepare(fixture,rule,source):
    return preparation.prepare_reactive_flux(rule=rule,sources=(source,),assessor_source=fixture.model.material.sources[0])


def execute_shots(fixture,monkeypatch,prepared,*,failure=None):
    observed = trajectory.stub_native(fixture,monkeypatch,failure=failure)
    carriers = []
    for index,shot in enumerate(prepared['prepared'].shots):
        child = SimpleNamespace(**vars(fixture))
        child.tmp_path = fixture.tmp_path/('shot-'+str(index))
        child.tmp_path.mkdir()
        child.workdir = child.tmp_path/'native'
        child.config = replace(fixture.config,config_id='config.exposed.flux-probe.'+str(index),work_directory=str(child.workdir))
        config = trajectory.owner.config_kind(accelerated=False)('config.exposed.flux-shot.'+str(index),child.config,shot.selection)
        raw = prepared['phase_bytes'][shot.shot_id]
        custody = trajectory.custody(child,config,raw)
        returned = trajectory.owner.operation_declaration().runner_factory().execute_with_native_subwork(custody.context,custody.store)
        result = decode_canonical_bytes(returned.outputs[0].payload,trajectory.owner.ReferenceTrajectoryResult,
            maximum_bytes=trajectory.owner.MAX_RETURN)
        carriers.append(retained.RetainedReactiveFluxShot(shot.shot_id,config,fixture.model,raw,result,custody.store))
    return tuple(carriers),observed


def test_original_frames_prepare_all_thermal_signs_and_steps_with_mass_metric(fixture,monkeypatch):
    rule,source,observed = original(fixture,monkeypatch)
    before = len(observed)
    result = prepare(fixture,rule,source)
    assert len(observed)==before
    assert result['prepared'].complete_equilibrium_census and len(result['prepared'].shots)==8
    assert decode_canonical_bytes(result['prepared'].canonical_bytes(),records.PreparedReactiveFlux,maximum_bytes=2**24)==result['prepared']
    masses = preparation.physical_masses(fixture.model)
    atoms = rule.equilibrium.ensembles[0].coordinate_window.cv_atom_ids[0]
    rows = [next(i for i,a in enumerate(fixture.model.atoms) if a.atom_id==key) for key in atoms]
    expected = math.sqrt((8.31446261815324e-3*298.15)*(1/masses[rows[0]]+1/masses[rows[1]])/(2*math.pi))*1e13
    assert all(g['analytic_positive_speed_per_second']==pytest.approx(expected,rel=1e-14) for g in result['geometry'].values())
    grouped = {}
    for shot in result['prepared'].shots:
        x,v,_ = trajectory.selected.read_phase_space(shot.selection,fixture.model,result['phase_bytes'][shot.shot_id])
        key = (shot.phase_source.sample_ordinal,shot.phase_source.momentum_sign)
        if key in grouped:
            assert np.array_equal(grouped[key],v)
        grouped[key]=v
    assert all(np.array_equal(grouped[(i,-1)],-grouped[(i,1)]) for i in (1,2))


def test_rule_rejects_disguised_controls_and_noncommon_physical_clocks(fixture,monkeypatch):
    rule,_,_ = original(fixture,monkeypatch)
    with pytest.raises(ValueError,match='common horizon'):
        replace(rule,dynamics=(rule.dynamics[0],replace(rule.dynamics[1],steps=11)))
    with pytest.raises(ValueError,match='every original'):
        replace(rule,plateau_times_seconds=(D('1.1e-15'),D('2e-15'),D('3e-15')))
    other = replace(rule.surfaces[0],surface_id='surface.exposed.other')
    control = records.ReactiveFluxControl('control.width','SLAB_WIDTH',(rule.surfaces[0].surface_id,other.surface_id),
        equilibrium.pin('correspondence.exposed'),D('.1'))
    with pytest.raises(ValueError,match='vary only'):
        replace(rule,surfaces=(*rule.surfaces,other),controls=(control,))
    with pytest.raises(ValueError,match='two-cut'):
        replace(rule,surfaces=(replace(rule.surfaces[0],coordinate_axis=2),))


def test_missing_and_failed_equilibrium_keep_no_successful_subset_roster(fixture,monkeypatch):
    rule,source,observed = original(fixture,monkeypatch,failure='native')
    before = len(observed)
    result = prepare(fixture,rule,source)
    assert not result['prepared'].complete_equilibrium_census and result['prepared'].shots==()
    report,_ = retained.read_reactive_flux(selection=rule,sources=(source,),assessor_source=fixture.model.material.sources[0])
    assert report['assigned_shots']==0 and report['original_equilibrium_analysis']['supplied_results']==1
    assert report['original_equilibrium_analysis']['trace_census']['trace.original']['original_completion']==source.original_result.completion.to_document()
    assert len(report['joint_uncertainty']['failed_replicates'])==rule.equilibrium.criteria.bootstrap_replicates
    assert len(observed)==before


def test_analysis_allocation_refuses_before_any_original_recovery(fixture,monkeypatch):
    rule,source,_ = original(fixture,monkeypatch)
    class Refuse:
        def recover(self,*a,**k):
            pytest.fail('allocation inspected original custody')
    with pytest.raises(ValueError,match='bounded analysis allocation'):
        retained.read_reactive_flux(selection=replace(rule,maximum_analysis_bytes=1),sources=(replace(source,native_subwork=Refuse()),),
            assessor_source=fixture.model.material.sources[0])


def test_complete_original_shots_keep_physical_failures_and_no_native_replay(fixture,monkeypatch):
    rule,source,_ = original(fixture,monkeypatch)
    prepared = prepare(fixture,rule,source)
    carriers,observed = execute_shots(fixture,monkeypatch,prepared)
    before = len(observed)
    report,arrays = retained.read_reactive_flux(selection=rule,sources=(source,*carriers),assessor_source=fixture.model.material.sources[0])
    assert report['assigned_shots']==report['supplied_results']==report['complete_shots']==8
    assert len(observed)==before and report['new_native_calls']==0
    assert report['physical_rate_admission']=='UNEVALUABLE'
    expected = {s.shot_id:s.selection.settings.steps+1 for s in prepared['prepared'].shots}
    assert all(r['retained_projected_frames']==expected[key] for key,r in report['shot_census'].items())
    assert arrays['reactive-flux.projected_coordinates'].size==4*(7+13)*3
    assert all(r['conditional_flux_assessment']!='SATISFIED' for r in report['cases'].values())
    with pytest.raises(ValueError,match='derived shot'):
        retained.read_reactive_flux(selection=rule,sources=(source,*carriers[:-1]),assessor_source=fixture.model.material.sources[0])


def test_absent_or_failed_shot_keeps_complete_assignment_and_original_cost(fixture,monkeypatch):
    rule,source,_ = original(fixture,monkeypatch)
    prepared = prepare(fixture,rule,source)
    carriers,observed = execute_shots(fixture,monkeypatch,prepared,failure='native')
    carriers = (retained.RetainedReactiveFluxShot(carriers[0].shot_id),*carriers[1:])
    before = len(observed)
    report,_ = retained.read_reactive_flux(selection=rule,sources=(source,*carriers),assessor_source=fixture.model.material.sources[0])
    assert report['assigned_shots']==8 and report['supplied_results']==7 and report['complete_shots']==0
    assert report['shot_census'][carriers[0].shot_id]['disposition']=='NOT_SUPPLIED'
    assert all(report['shot_census'][s.shot_id]['original_completion']==s.original_result.completion.to_document() for s in carriers[1:])
    assert len(observed)==before


def test_prepared_phase_substitution_refuses_before_result_contact(fixture,monkeypatch):
    rule,source,_ = original(fixture,monkeypatch)
    prepared = prepare(fixture,rule,source)
    carriers = tuple(retained.RetainedReactiveFluxShot(s.shot_id) for s in prepared['prepared'].shots)
    first = prepared['prepared'].shots[0]
    settings = replace(first.selection.settings,step_seconds=D('1.25e-16'),steps=24)
    config = trajectory.owner.config_kind(accelerated=False)('config.exposed.changed-flux-clock',fixture.config,
        replace(first.selection,settings=settings))
    changed = retained.RetainedReactiveFluxShot(first.shot_id,config,fixture.model,prepared['phase_bytes'][first.shot_id])
    with pytest.raises(ValueError,match='exact prepared'):
        retained.read_reactive_flux(selection=rule,sources=(source,changed,*carriers[1:]),assessor_source=fixture.model.material.sources[0])


def test_closed_export_reconstructs_originals_and_refuses_changed_sibling(fixture,monkeypatch):
    from empirical_lawhood.api import numerical_provenance, recursive_authoring
    from empirical_lawhood.api.domain_composition.rubisco_response import reactive_flux as public
    from tests.test_recursive_public_service import _plane
    rule,source,_ = original(fixture,monkeypatch)
    prepared = prepare(fixture,rule,source)
    carriers = tuple(retained.RetainedReactiveFluxShot(s.shot_id) for s in prepared['prepared'].shots)
    sources = (source,*carriers)
    plane = _plane(fixture.tmp_path/'flux-export')
    monkeypatch.setattr(recursive_authoring,'implementation_binding',lambda _:fixture.config.implementation)
    monkeypatch.setattr(numerical_provenance,'capture_numerical_provenance',lambda **k:fixture.config.provenance)
    result = public.export_reactive_flux(selection=rule,sources=sources,project_root=fixture.tmp_path,
        artifact_writer=plane,output_relative_path='selected/flux')
    assert set(result['paths'])==set(public.MEMBERS)
    reread = public.read_reactive_flux_export(directory_relative_path='selected/flux',sources=sources,artifact_writer=plane)
    assert reread['report']==result['report'] and reread['evidence']==result['evidence']
    target = plane.root.resolve('selected/flux/report.txt',for_write=False)
    target.write_bytes(target.read_bytes()+b'altered\n')
    with pytest.raises(ArtifactIdentityConflict):
        public.read_reactive_flux_export(directory_relative_path='selected/flux',sources=sources,artifact_writer=plane)


def test_original_byte_change_during_joint_analysis_refuses_final_return(fixture,monkeypatch):
    rule,source,_ = original(fixture,monkeypatch)
    prepared = prepare(fixture,rule,source)
    carriers = tuple(retained.RetainedReactiveFluxShot(s.shot_id) for s in prepared['prepared'].shots)
    analyze = retained.joint_flux_resampling
    stream = source.native_subwork.iter_completed_output
    def changed(definition,output_id,**kwargs):
        first = True
        for block in stream(definition,output_id,**kwargs):
            if output_id=='files.raw' and first and block:
                block=bytes((block[0]^1,))+block[1:]
                first=False
            yield block
    def during(**kwargs):
        result=analyze(**kwargs)
        monkeypatch.setattr(source.native_subwork,'iter_completed_output',changed)
        return result
    monkeypatch.setattr(retained,'joint_flux_resampling',during)
    with pytest.raises(ValueError,match='original output changed before return'):
        retained.read_reactive_flux(selection=rule,sources=(source,*carriers),assessor_source=fixture.model.material.sources[0])


def test_authoring_uses_returned_shots_and_receipted_exact_preparation(fixture,monkeypatch):
    from empirical_lawhood.api import numerical_provenance, recursive_authoring
    from empirical_lawhood.api.domain_composition.rubisco_response import reactive_flux as public
    from tests.runtime_platform.test_native_subwork import _plane
    rule,source,observed = original(fixture,monkeypatch)
    prepared = prepare(fixture,rule,source)
    plane = _plane(fixture.tmp_path/'flux-authoring',binary_codecs=(trajectory.owner.PHASE_CODEC,))
    project = fixture.tmp_path/'project'
    project.mkdir()
    monkeypatch.setattr(recursive_authoring,'implementation_binding',lambda _:fixture.config.implementation)
    monkeypatch.setattr(numerical_provenance,'capture_numerical_provenance',lambda **k:fixture.config.provenance)
    authored = []
    def author(**kwargs):
        authored.append(kwargs)
        for _,path in kwargs['input_bindings']:
            manifest = plane.read_manifest(path.relative_to(Path(plane.root.contract.canonical_path)).as_posix())
            plane.verify_manifest(manifest)
            assert len(manifest.logical.lineage_parents)==2
        return dict(scope='EXPOSED_SHARED_AUTHOR_CONTROL')
    monkeypatch.setattr(recursive_authoring,'author_recursive_wave',author)
    before = len(observed)
    returned = public.author_reactive_flux(prepared=prepared['prepared'],sources=(source,),raw_sources=(fixture.sources,),
        project_root=project,work_directory=fixture.tmp_path/'flux-native',artifact_writer=plane,
        output_dir=Path(plane.root.contract.canonical_path)/'selected')
    assert len(authored)==8 and set(returned['shots'])=={s.shot_id for s in prepared['prepared'].shots}
    assert len(observed)==before
    reread = public.read_reactive_flux_preparation(relative_path='selected/preparation.json',sources=(source,),artifact_writer=plane,maximum_bytes=2**24)
    assert reread['prepared']==prepared['prepared']


def test_flux_preparation_authors_actual_shared_graphs_and_exports_complete_returned_population(fixture, monkeypatch):
    from empirical_lawhood.api import numerical_provenance, recursive_authoring
    from empirical_lawhood.api.domain_composition.rubisco_response import reactive_flux as public
    from tests.runtime_platform.test_native_subwork import _plane
    rule, source, observed = original(fixture, monkeypatch)
    prepared = prepare(fixture, rule, source)
    plane = _plane(fixture.tmp_path/'integrated-flux', binary_codecs=(trajectory.owner.PHASE_CODEC,))
    monkeypatch.setattr(recursive_authoring, 'implementation_binding', lambda *a, **k: fixture.config.implementation)
    monkeypatch.setattr(numerical_provenance, 'capture_numerical_provenance', lambda **k: fixture.config.provenance)
    destination = Path(plane.root.contract.canonical_path)/'authored'
    project = fixture.tmp_path/'project'
    project.mkdir()
    before = len(observed)
    authored = public.author_reactive_flux(prepared=prepared['prepared'], sources=(source,), raw_sources=(fixture.sources,),
        project_root=project, work_directory=fixture.tmp_path/'integrated-native', artifact_writer=plane,
        output_dir=destination)
    assert len(observed) == before and authored['new_native_calls'] == 0
    assert len(authored['shots']) == len(prepared['prepared'].shots) == 8
    for shot in prepared['prepared'].shots:
        returned = authored['shots'][shot.shot_id]
        packet, draft, _, _ = recursive_authoring.load_authored_wave(
            directory=Path(returned['authoring_dir']), artifact_writer=plane)
        assert packet.draft.object_fingerprint == draft.fingerprint()
        assert returned['task_count'] == 1 and returned['native_contact'] == 'none'
        config = decode_canonical_bytes(draft.operations[0].config_payload.encode(),
            trajectory.owner.config_kind(accelerated=False), maximum_bytes=2**24)
        assert config.selection == shot.selection
    # Native bodies are explicitly exposed analytical mechanics. The complete
    # native-subwork stores, readers and publication remain the real owners.
    carriers, forces = execute_shots(fixture, monkeypatch, prepared)
    before = len(forces)
    sources = (source, *carriers)
    exported = public.export_reactive_flux(selection=rule, sources=sources, project_root=fixture.tmp_path,
        artifact_writer=plane, output_relative_path='analysis')
    reread = public.read_reactive_flux_export(directory_relative_path='analysis', sources=sources, artifact_writer=plane)
    assert reread['report'] == exported['report'] and len(forces) == before
    assert reread['report']['complete_shots'] == 8
    assert all(row['conditional_flux_assessment'] != 'SATISFIED' for row in reread['report']['cases'].values())
