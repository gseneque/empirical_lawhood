# SPDX-License-Identifier: MPL-2.0
"""Exposed path-accounting and original-custody controls, not enzyme evidence."""

from dataclasses import replace
from decimal import Decimal as D, localcontext
from fractions import Fraction as F
import json

import pytest

from empirical_lawhood.domains.rubisco.rubisco_response import physical_first_passage_records as records
from empirical_lawhood.domains.rubisco.rubisco_response import physical_first_passage_science as science
from empirical_lawhood.domains.rubisco.rubisco_response import physical_first_passage_read as retained
from empirical_lawhood.domains.rubisco.rubisco_response import weighted_path_resampling as resampling
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_dynamics import ReferenceDynamicsSettings
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.storage.artifacts import ArtifactIdentityConflict
from tests import test_rubisco_periodic_trajectory as acquisition
from tests.test_rubisco_equilibrium_reweighting import ensemble as coordinate_fixture, pin


def ensemble():
    coordinate = coordinate_fixture()
    events = (records.PassageEvent('event.product', records.PassageRegion('region.product', (D('.5'),),(D('1.5'),)),
        'PRODUCTIVE', 1, pin('definition.product')),
        records.PassageEvent('event.reverse', records.PassageRegion('region.reverse',(D('-2'),),(D('-1'),)),
        'REVERSE', 0, pin('definition.reverse')))
    return records.PassageEnsemble('ensemble.exposed.passage', coordinate.prototype, coordinate.coordinate_window,
        coordinate.coordinate_convention, records.PassageRegion('region.entry',(D('-.5'),),(D('.5'),)),
        events, pin('entry.exposed'), None, None)


def selection(*, item=None, configs=None, weights=(F(1),)):
    item = item or ensemble()
    configs = configs or tuple(pin('config.path.'+str(i), acquisition.owner.ReferenceTrajectoryConfig.SCHEMA) for i in range(len(weights)))
    paths = tuple(records.FirstPassagePath('path.'+str(i), item.ensemble_id, config, 'run.one', 'preparation.one',
        'site.one', 'history.one', records.PathWeight.from_fraction(weight)) for i,(config,weight) in enumerate(zip(configs,weights,strict=True)))
    return records.FirstPassageSelection('selection.exposed.first-passage',(item,),paths,pin('dependence.exposed'),
        ('Exposed software trajectories, without physical ensemble or biological admission.',),2**30)


def observe(values, *, item=None):
    settings = ReferenceDynamicsSettings('settings.exposed.passage',D('5e-16'),len(values)-1)
    observer = science.PassageObserver(ensemble=item or ensemble(),settings=settings)
    for step,value in enumerate(values):
        observer.consume(step=step,physical_time_seconds=str(settings.time_at_step(step)),coordinates=(value,))
    return observer.finish()


def test_recrossings_dwell_confirmation_and_exact_native_clock_are_preserved():
    result = observe((0.,1.,0.,1.,1.,0.))
    event = result['first_event']
    assert result['event_visits']['event.product'] == 2
    assert result['event_departures']['event.product'] == 2
    assert event['entrance_step'] == 3 and event['confirmation_step'] == 4
    assert science.fraction(event['entrance_time_upper_seconds']) == F('1.5e-15')
    assert science.fraction(event['event_time_upper_seconds']) == F('2e-15')
    assert result['physical_rate_admission'] == 'UNEVALUABLE'


def test_decimal_region_boundaries_do_not_round_into_a_positive_event():
    region = records.PassageRegion('region.exact',(D('.50000000000000000000001'),),(D(1),))
    assert not science.contains(region,(.5,))
    with pytest.raises(ValueError,match='overlapping'):
        replace(ensemble(), entry_region=records.PassageRegion('region.entry',(D(0),),(D(1),)))


def test_censored_paths_preserve_probability_and_leave_mean_exit_and_rates_unidentified():
    selected = selection(weights=(F(1,4),F(3,4)))
    first = dict(observe((0.,1.,1.,0.,0.)),path_disposition='OBSERVED_EVENT',original_cost={'wall_seconds':'7'})
    second = dict(observe((0.,0.,0.,0.,0.)),path_disposition='HORIZON_CENSORED',original_cost={'wall_seconds':None})
    report = science.summarize_first_passages(selection=selected,path_reports={'path.0':first,'path.1':second})
    run = report['ensembles'][selected.ensembles[0].ensemble_id]['runs']['run.one']
    assert science.fraction(run['observed_event_weight']['event.product']) == F(1,4)
    assert science.fraction(run['horizon_censored_weight']) == F(3,4)
    dt = F('5e-16')
    assert tuple(map(science.fraction,run['restricted_mean_first_passage_bounds_seconds'])) == (F(13,4)*dt,F(7,2)*dt)
    assert tuple(map(science.fraction,run['eventual_event_probability_bounds']['event.reverse'])) == (0,F(3,4))
    assert run['complete_mean_first_passage_bounds_seconds'] is None and run['memoryless_rates_per_second'] is None
    assert run['costs'][1]['original_cost']['wall_seconds'] is None


def test_computational_failure_is_not_silently_independent_censoring():
    selected = selection()
    row = dict(observe((0.,0.,0.)),path_disposition='COMPUTATIONAL_TRUNCATION',original_cost=None)
    row['selected_horizon_seconds'] = science.rational(F('2e-15'))
    result = science.summarize_first_passages(selection=selected,path_reports={'path.0':row})
    run = result['ensembles'][selected.ensembles[0].ensemble_id]['runs']['run.one']
    assert tuple(map(science.fraction,run['event_probability_by_horizon_bounds']['event.product'])) == (0,1)
    assert tuple(map(science.fraction,run['restricted_mean_first_passage_bounds_seconds'])) == (F('1e-15'),F('2e-15'))


def state(name, weight, *, disposition='ACTIVE', bin_id='bin.a', run_id='run.one'):
    return records.WeightedPathState(name,'ensemble.one',run_id,bin_id,records.PathWeight.from_fraction(weight),
        pin('phase.'+name),(pin('history.'+name),),64,disposition)


def resampling_selection(**changes):
    return replace(records.WeightedResamplingSelection('resampling.exposed',('bin.a','bin.b'),(3,2),91232,1024),**changes)


def test_exact_weighted_resampling_keeps_failed_paths_and_entire_parent_histories():
    paths = (state('path.a',F(1,6)),state('path.b',F(1,3)),state('path.c',F(1,2),disposition='FAILED',bin_id='bin.b'))
    with localcontext() as ctx:
        ctx.prec = 2
        result = resampling.resample_weighted_paths(selection=resampling_selection(),paths=paths)
    assert result.retained_terminal_paths == (paths[2],)
    assert len(result.offspring) == 3
    assert sum((p.weight.fraction for p in result.resulting_paths),F()) == 1
    assert all(p.path.weight.fraction == F(1,6) and p.path.physical_step == 64 for p in result.offspring)
    assert resampling.assess_weighted_resampling(result)['independent_units_added'] == 0
    decoded = decode_canonical_bytes(result.canonical_bytes(),resampling.WeightedResamplingEvidence,maximum_bytes=2**20)
    assert decoded == result
    altered = replace(result,offspring=(replace(result.offspring[0],path=replace(result.offspring[0].path,history=(pin('history.altered'),))),*result.offspring[1:]))
    with pytest.raises(ValueError,match='history'):
        resampling.assess_weighted_resampling(altered)


def test_resampling_has_the_weighted_distribution_without_relabelled_independent_runs():
    paths = (state('path.a',F(1,5)),state('path.b',F(4,5)))
    selected = resampling_selection(offspring_per_occupied_bin=(4000,2))
    result = resampling.resample_weighted_paths(selection=selected,paths=paths)
    count = sum(row.parent_path_id=='path.a' for row in result.offspring)
    assert count/4000 == pytest.approx(.2,abs=.02)
    assert len({row.path.run_id for row in result.offspring}) == 1
    assert resampling.assess_weighted_resampling(result)['probability_conservation'] == 'EXACT'


@pytest.mark.parametrize('change',('weight','clock','draw','denominator','missing-child'))
def test_resampling_rejects_broken_census_weights_clocks_and_random_evidence(change):
    result = resampling.resample_weighted_paths(selection=resampling_selection(),paths=(state('path.a',F(1)),))
    row = result.offspring[0]
    if change=='weight':row=replace(row,path=replace(row.path,weight=records.PathWeight(1,2)))
    elif change=='clock':row=replace(row,path=replace(row.path,physical_step=65))
    elif change=='draw':row=replace(row,random_words=(row.random_words[0]^1,*row.random_words[1:]))
    elif change=='denominator':row=replace(row,selection_denominator=row.selection_denominator+1)
    changed = replace(result,offspring=result.offspring[:-1] if change=='missing-child' else (row,*result.offspring[1:]))
    with pytest.raises(ValueError):resampling.assess_weighted_resampling(changed)


fixture = acquisition.fixture


def native_selection(fixture, *, event=True):
    config, phase = acquisition.trajectory(fixture)
    xyz, velocity, _ = acquisition.selected.read_phase_space(config.selection,fixture.model,phase)
    xyz[0],xyz[1] = (0.,0.,0.),(1.,0.,0.)
    velocity[:] = 0
    velocity[1,0] = 100
    trajectory, phase = acquisition.selected.prepare_reference_trajectory(prototype=fixture.selection,representation=fixture.model,
        phase_source=pin('phase.exposed.designed'),initial_angstrom=xyz,initial_velocity_nm_per_ps=velocity,
        settings=replace(config.selection.settings,steps=4),criteria=replace(config.selection.criteria,maximum_energy_drift_kj_mol=D('1e-4')),
        density_guess_policy='COLD')
    config = replace(config,selection=trajectory)
    item = ensemble()
    window = replace(item.coordinate_window,model_id=fixture.model.representation_id,
        cv_atom_ids=((fixture.model.atoms[0].atom_id,fixture.model.atoms[1].atom_id),))
    convention = replace(item.coordinate_convention,window=ObjectIdentity.from_record(window.window_id,window))
    boundary = D('1.4') if event else D('10')
    event = replace(item.events[0],region=records.PassageRegion('region.product',(boundary,),(D(20),)))
    item = replace(item,prototype=fixture.selection.identity,coordinate_window=window,coordinate_convention=convention,
        entry_region=records.PassageRegion('region.entry',(D(0),),(boundary,)),events=(event,))
    return config,phase,selection(item=item,configs=(config.identity,))


def run_original(fixture,monkeypatch,*,failure=None,event=True):
    config,phase,selected = native_selection(fixture,event=event)
    observed = acquisition.stub_native(fixture,monkeypatch,failure=failure)
    custody = acquisition.custody(fixture,config,phase)
    returned = acquisition.owner.operation_declaration().runner_factory().execute_with_native_subwork(custody.context,custody.store)
    original = decode_canonical_bytes(returned.outputs[0].payload,acquisition.owner.ReferenceTrajectoryResult,maximum_bytes=acquisition.owner.MAX_RETURN)
    source = retained.RetainedFirstPassagePath('path.0',config,fixture.model,phase,original,custody.store)
    return selected,source,custody,observed


@pytest.mark.parametrize('event',(False,True))
def test_original_native_trajectory_supplies_actual_physical_passage_or_censoring(fixture,monkeypatch,event):
    selected,source,_,observed = run_original(fixture,monkeypatch,event=event)
    before = len(observed)
    report,arrays = retained.read_first_passages(selection=selected,sources=(source,),assessor_source=fixture.model.material.sources[0])
    path = report['path_census']['path.0']
    assert path['path_disposition'] == ('OBSERVED_EVENT' if event else 'HORIZON_CENSORED')
    assert path['original_cost'] == source.original_result.completion.cost.to_document()
    assert arrays['path.0.physical_steps'].tolist() == [0,1,2,3,4]
    assert arrays['path.0.coordinates'].shape == (5,1)
    assert len(observed)==before and report['new_reference_evaluations']==0
    if event:assert path['first_event']['confirmation_step']==2


def test_failed_original_and_missing_result_keep_every_assigned_weight(fixture,monkeypatch):
    selected,source,_,observed = run_original(fixture,monkeypatch,failure='native')
    before=len(observed)
    report,_=retained.read_first_passages(selection=selected,sources=(source,),assessor_source=fixture.model.material.sources[0])
    assert report['path_census']['path.0']['path_disposition']=='COMPUTATIONAL_TRUNCATION'
    missing=replace(source,original_result=None,native_subwork=None)
    absent,arrays=retained.read_first_passages(selection=selected,sources=(missing,),assessor_source=fixture.model.material.sources[0])
    assert absent['assigned_paths']==1 and absent['supplied_results']==0
    assert absent['path_census']['path.0']['path_disposition']=='MISSING_ORIGINAL'
    assert arrays['path.0.coordinates'].shape==(0,1)
    assert len(observed)==before


def test_complete_first_passage_export_reconstructs_without_force_reentry(fixture,monkeypatch):
    from empirical_lawhood.api import numerical_provenance, recursive_authoring
    from empirical_lawhood.api.domain_composition.rubisco_response import physical_first_passage as public
    from tests.test_recursive_public_service import _plane
    selected,source,_,observed=run_original(fixture,monkeypatch)
    plane=_plane(fixture.tmp_path/'analysis-custody')
    monkeypatch.setattr(recursive_authoring,'implementation_binding',lambda _:fixture.config.implementation)
    monkeypatch.setattr(numerical_provenance,'capture_numerical_provenance',lambda **k:fixture.config.provenance)
    before=len(observed)
    exported=public.export_first_passages(selection=selected,sources=(source,),project_root=fixture.tmp_path,
        artifact_writer=plane,output_relative_path='selected/first-passage')
    reread=public.read_first_passage_export(directory_relative_path='selected/first-passage',sources=(source,),artifact_writer=plane)
    assert reread['report']==exported['report'] and len(observed)==before
    target=plane.root.resolve('selected/first-passage/report.txt',for_write=False)
    target.write_bytes(target.read_bytes()+b'changed\n')
    with pytest.raises(ArtifactIdentityConflict):
        public.read_first_passage_export(directory_relative_path='selected/first-passage',sources=(source,),artifact_writer=plane)


def test_projection_allocation_and_omitted_carriers_refuse_before_original_contact(fixture):
    config,phase,selected=native_selection(fixture)
    source=retained.RetainedFirstPassagePath('path.0',config,fixture.model,phase,None,None)
    with pytest.raises(ValueError,match='allocation'):
        retained.validate_first_passage_inputs(replace(selected,maximum_projection_bytes=1),(source,))
    with pytest.raises(ValueError,match='omit'):
        retained.validate_first_passage_inputs(selected,())


def test_original_mutation_during_path_reduction_refuses_the_return(fixture,monkeypatch):
    selected,source,_,_=run_original(fixture,monkeypatch)
    summarize=retained.summarize_first_passages
    stream=source.native_subwork.iter_completed_output
    def changed(definition,output_id,**kwargs):
        first=True
        for block in stream(definition,output_id,**kwargs):
            if first and output_id=='files.raw' and block:
                block=bytes((block[0]^1,))+block[1:]
                first=False
            yield block
    def during(**kwargs):
        value=summarize(**kwargs)
        monkeypatch.setattr(source.native_subwork,'iter_completed_output',changed)
        return value
    monkeypatch.setattr(retained,'summarize_first_passages',during)
    with pytest.raises(ValueError,match='original output changed before return'):
        retained.read_first_passages(selection=selected,sources=(source,),assessor_source=fixture.model.material.sources[0])


def test_identical_deterministic_phases_cannot_be_counted_as_separate_runs(fixture):
    config,phase,selected=native_selection(fixture)
    other=replace(config,config_id='config.exposed.other')
    selected=replace(selected,paths=(selected.paths[0],replace(selected.paths[0],path_id='path.1',run_id='run.two',configuration=other.identity)))
    sources=(retained.RetainedFirstPassagePath('path.0',config,fixture.model,phase,None,None),
        retained.RetainedFirstPassagePath('path.1',other,fixture.model,phase,None,None))
    with pytest.raises(ValueError,match='identical deterministic'):
        retained.validate_first_passage_inputs(selected,sources)


def test_all_missing_paths_can_be_exported_without_inventing_zero_events(fixture,monkeypatch):
    from empirical_lawhood.api import numerical_provenance, recursive_authoring
    from empirical_lawhood.api.domain_composition.rubisco_response import physical_first_passage as public
    from tests.test_recursive_public_service import _plane
    config,phase,selected=native_selection(fixture)
    source=retained.RetainedFirstPassagePath('path.0',config,fixture.model,phase,None,None)
    plane=_plane(fixture.tmp_path/'missing-custody')
    monkeypatch.setattr(recursive_authoring,'implementation_binding',lambda _:fixture.config.implementation)
    monkeypatch.setattr(numerical_provenance,'capture_numerical_provenance',lambda **k:fixture.config.provenance)
    exported=public.export_first_passages(selection=selected,sources=(source,),project_root=fixture.tmp_path,
        artifact_writer=plane,output_relative_path='selected/missing-paths')
    reread=public.read_first_passage_export(directory_relative_path='selected/missing-paths',sources=(source,),artifact_writer=plane)
    assert reread['report']==exported['report']
    run=reread['report']['statistics']['ensembles'][selected.ensembles[0].ensemble_id]['runs']['run.one']
    assert tuple(map(science.fraction,run['event_probability_by_horizon_bounds']['event.product']))==(0,1)


def stochastic_selection(fixture, *, event=True):
    from tests import test_rubisco_periodic_equilibrium_acquisition as equilibrium
    base,phase,selected=native_selection(fixture,event=event)
    original,_=equilibrium.trajectory(fixture)
    xyz,velocity,_=acquisition.selected.read_phase_space(base.selection,fixture.model,phase)
    settings=replace(original.selection.settings,dynamics=base.selection.settings,discard_initial_steps=0,
        sample_interval_steps=1,bias_window=None,bias_convention=None)
    sampling,phase=equilibrium.selected.prepare_reference_equilibrium(prototype=fixture.selection,representation=fixture.model,
        phase_source=base.selection.phase_source,initial_angstrom=xyz,initial_velocity_nm_per_ps=velocity,
        settings=settings,criteria=original.selection.criteria,density_guess_policy='COLD',window=None,convention=None)
    config=replace(original,selection=sampling)
    item=replace(selected.ensembles[0],dynamics_model='DECLARED_UNBIASED_LANGEVIN',
        temperature_kelvin=settings.temperature_kelvin,friction_per_picosecond=settings.friction_per_picosecond)
    selected=replace(selected,ensembles=(item,),paths=(replace(selected.paths[0],configuration=config.identity),))
    return config,phase,selected


def test_declared_unbiased_bath_retains_every_frame_noise_clock_and_transport_limit(fixture,monkeypatch):
    from tests import test_rubisco_periodic_equilibrium_acquisition as equilibrium
    config,phase,selected=stochastic_selection(fixture)
    observed=equilibrium.stub_native(fixture,monkeypatch)
    custody=equilibrium.custody(fixture,config,phase)
    returned=equilibrium.owner.operation_declaration().runner_factory().execute_with_native_subwork(custody.context,custody.store)
    original=decode_canonical_bytes(returned.outputs[0].payload,equilibrium.owner.ReferenceEquilibriumResult,maximum_bytes=equilibrium.owner.MAX_RETURN)
    source=retained.RetainedFirstPassagePath('path.0',config,fixture.model,phase,original,custody.store)
    before=len(observed)
    report,arrays=retained.read_first_passages(selection=selected,sources=(source,),assessor_source=fixture.model.material.sources[0])
    assert len(observed)==before
    assert report['path_census']['path.0']['original_trace_assessment']['native_error'] is None
    assert report['path_census']['path.0']['original_trace_assessment']['assessment_error'] is None
    assert arrays['path.0.physical_steps'].tolist()==[0,1,2,3,4]
    path=report['path_census']['path.0']
    assert path['path_disposition']=='OBSERVED_EVENT'
    assert path['bath_transport_dependence']=='UNEVALUABLE'
    assert path['original_trace_assessment']['assessment']['random_state_chain']=='COMPLETE_FRAME_DRAWS_REPRODUCED_FROM_SELECTED_SEED'


@pytest.mark.parametrize('change',('model','temperature','friction','discard','sample-interval'))
def test_stochastic_clock_needs_the_explicit_unbiased_bath_and_complete_schedule(fixture,change):
    config,phase,selected=stochastic_selection(fixture)
    item=selected.ensembles[0]
    if change=='model':item=replace(item,dynamics_model='NVE',temperature_kelvin=None,friction_per_picosecond=None)
    elif change=='temperature':item=replace(item,temperature_kelvin=item.temperature_kelvin+D(1))
    elif change=='friction':item=replace(item,friction_per_picosecond=item.friction_per_picosecond*D(2))
    else:
        settings=replace(config.selection.settings,**({'discard_initial_steps':1} if change=='discard' else {'sample_interval_steps':2}))
        config=replace(config,selection=replace(config.selection,settings=settings))
    selected=replace(selected,ensembles=(item,),paths=(replace(selected.paths[0],configuration=config.identity),))
    source=retained.RetainedFirstPassagePath('path.0',config,fixture.model,phase,None,None)
    with pytest.raises(ValueError,match='dynamical model|stochastic path'):
        retained.validate_first_passage_inputs(selected,(source,))


def test_full_noise_replay_refuses_an_unbound_initial_generator_state(fixture,monkeypatch):
    from tests import test_rubisco_periodic_equilibrium_acquisition as equilibrium
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_equilibrium_recorded import assess_recorded_equilibrium, selected_equilibrium_member
    config,phase,_=stochastic_selection(fixture)
    equilibrium.stub_native(fixture,monkeypatch)
    directory=fixture.tmp_path/'noise-control'
    equilibrium.run_body(fixture,config,phase,directory)
    def files():
        for path in sorted(directory.iterdir()):
            raw=path.read_bytes() if selected_equilibrium_member(path.name) else None
            if path.name=='evaluation.0000000000000002.noise-state.json':
                row=json.loads(raw)
                row['state_before']['state']['state']^=1
                raw=json.dumps(row).encode()
            yield path.name,raw
    # Continuity after the first state cannot, by itself, establish its seed.
    kwargs=dict(selection=config.selection,prototype=fixture.selection,representation=fixture.model,
        phase_bytes=phase,native_succeeded=True)
    assert assess_recorded_equilibrium(files=files(),**kwargs)['selected_trace_criteria']=='SATISFIED'
    with pytest.raises(ValueError,match='exact selected seed'):
        assess_recorded_equilibrium(files=files(),verify_random_stream=True,**kwargs)
