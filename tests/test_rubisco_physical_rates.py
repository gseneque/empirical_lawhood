# SPDX-License-Identifier: MPL-2.0
"""Known first-exit laws, adversarial alternatives and original-custody controls.

Every distribution below is exposed software evidence, not an enzyme sample.
"""

from dataclasses import replace
from decimal import Decimal as D, localcontext
from fractions import Fraction as F
import math

import numpy as np
import pytest

from empirical_lawhood.domains.rubisco.rubisco_response import physical_rate_records as records
from empirical_lawhood.domains.rubisco.rubisco_response import physical_rate_science as science
from empirical_lawhood.domains.rubisco.rubisco_response import physical_rate_read as retained
from empirical_lawhood.domains.rubisco.rubisco_response.physical_first_passage_records import FirstPassagePath, PathWeight
from empirical_lawhood.domains.rubisco.rubisco_response.physical_first_passage_read import RetainedFirstPassagePath
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.storage.artifacts import ArtifactIdentityConflict
from tests import test_rubisco_physical_first_passage as passage


def criteria(**changes):
    return replace(records.PhysicalRateCriteria('criteria.exposed.rates',2,D('1e-8'),D('1e-8'),
        D('.01'),D('.02'),D('.02'),D('1e-12')),**changes)


def geometric(q, *, horizon=12, histories=('history.a','history.b'), prefix='path', events=('event.product','event.reverse'), proportions=(F(2,3),F(1,3))):
    """Exact CTMC observations: P(T in ((k-1)dt,kdt]) = S(k-1)-S(k)."""
    rows = []
    for history in histories:
        for step in range(1,horizon+1):
            for event,proportion in zip(events,proportions,strict=True):
                weight = ((1-q)**(step-1)-(1-q)**step)*proportion/len(histories)
                if weight:
                    rows.append(science.RateObservation(f'{prefix}.{history}.{event}.{step}',history,weight,step,event,True))
        rows.append(science.RateObservation(f'{prefix}.{history}.censored',history,(1-q)**horizon/len(histories),horizon,None,True))
    assert sum((r.weight for r in rows),F()) == 1
    return tuple(rows)


def selected(groups, *, dt=D('.5'), item=None, controls=(), replicas=32):
    item = item or passage.ensemble()
    paths, bindings = [], []
    for index, rows in enumerate(groups):
        run = 'run.'+str(index)
        for j,row in enumerate(rows):
            path_id = f'path.{index:03d}.{j:03d}'
            paths.append(FirstPassagePath(path_id,item.ensemble_id,passage.pin('config.'+path_id,passage.acquisition.owner.ReferenceTrajectoryConfig.SCHEMA),
                run,'preparation.one','site.one',row.entry_history_id,PathWeight.from_fraction(row.weight)))
        bindings.append(records.PhysicalRateRunGroup('group.'+str(index),(records.PhysicalRateRunBinding(item.ensemble_id,(run,)),)))
    original = replace(passage.selection(item=item),paths=tuple(paths))
    horizon = max(r.last_step for rows in groups for r in rows)
    history_ids = tuple(sorted({r.entry_history_id for rows in groups for r in rows}))
    case = records.PhysicalRateCase(item.ensemble_id,(dt*(horizon//2),dt*horizon),history_ids,passage.pin('quantity.exposed.exit'))
    return records.PhysicalRateSelection('selection.exposed.rates',original,(case,),tuple(bindings),controls,criteria(),replicas,23,
        D('.9'),2**30,('Exposed distributions with declared paired whole-run groups; no physical admission.',))


def assess(groups, *, rule=None, dt=D('.5')):
    rule = rule or selected(groups,dt=dt)
    return science.assess_case(case=rule.cases[0],ensemble=rule.passages.ensembles[0],groups=groups,
        dt=F(dt),horizon_steps=max(r.last_step for rows in groups for r in rows),criteria=rule.criteria)


@pytest.mark.numerical(oracle='Exact geometric survival and competing-exit exponential hazard -log(0.75)/dt')
def test_exact_competing_exponential_population_with_horizon_censoring():
    groups = (geometric(F(1,4)),geometric(F(1,4),prefix='other'))
    result = assess(groups)
    expected = -math.log(.75)/.5
    assert float(result['fit']['exit_rate_per_second']) == pytest.approx(expected,rel=1e-14)
    assert float(result['fit']['cause_rates_per_second']['event.product']) == pytest.approx(expected*2/3,rel=1e-14)
    assert float(result['fit']['cause_rates_per_second']['event.reverse']) == pytest.approx(expected/3,rel=1e-14)
    assert result['reduction_assessment'] == 'SATISFIED'
    assert result['numerical_assessment']['maximum_dimensionless_equation_error'] < 1e-14
    assert result['empirical_cumulative_probability_check']['maximum_absolute_error'] < 1e-14
    # No reciprocal restricted mean: the unobserved exponential tail is an
    # explicit model extrapolation, and its fitted mean differs from the grid.
    assert float(result['fit']['extrapolated_exponential_mean_seconds']) == pytest.approx(1/expected)
    assert 1/expected != .5/.25


@pytest.mark.numerical(oracle='Exact rational rare-event population and asymptotic hazard at probability 1e-100')
def test_exact_weight_arithmetic_is_independent_of_callers_decimal_context():
    groups = (geometric(F(1,4)),geometric(F(1,4),prefix='second'))
    baseline = assess(groups)
    with localcontext() as ctx:
        ctx.prec = 3
        actual = assess(groups)
    assert actual == baseline
    rare = (science.RateObservation('path.rare','history.one',F(1,10**100),1,'event.product',True),
        science.RateObservation('path.survives','history.one',1-F(1,10**100),2,None,True))
    fit = science.fit_hazards(samples=tuple((row,row.weight) for row in rare),event_ids=('event.product',),dt=F(1))
    assert float(fit['exit_rate_per_second']) == pytest.approx(5e-101,rel=1e-14,abs=0)


def test_absent_reverse_event_is_unidentified_and_does_not_become_irreversibility():
    groups = (geometric(F(1,4),proportions=(F(1),F(0))),)*2
    result = assess(groups)
    assert result['fit']['cause_rates_per_second']['event.reverse'] is None
    assert result['fit']['eventual_cause_probabilities']['event.reverse'] is None
    assert result['reduction_assessment'] == 'UNEVALUABLE'
    assert result['missing_cause_rates'] == ('event.reverse',)


@pytest.mark.parametrize('failure',('missing','mechanics','future-continuation'))
def test_computational_loss_is_not_a_noninformative_censor(failure):
    rows = list(geometric(F(1,4)))
    rows[-1] = replace(rows[-1],path_id='path.'+failure,complete=False)
    result = assess((tuple(rows),tuple(rows)))
    assert result['fit']['exit_rate_per_second'] is None
    assert result['fit']['reason'] == 'COMPUTATIONAL_OR_UNASSESSED_WEIGHT'
    assert result['fit']['invalid_path_ids'] == ('path.'+failure,)*2
    assert result['reduction_assessment'] == 'UNEVALUABLE'


def test_unresolved_substates_falsify_history_and_dwell_checks():
    fast = geometric(F(1,2),histories=('history.fast',))
    slow = geometric(F(1,20),histories=('history.slow',))
    mixture = tuple(replace(r,weight=r.weight/2) for r in (*fast,*slow))
    result = assess((mixture,mixture))
    assert result['entry_history_check']['status'] == 'FALSIFIED'
    assert result['dwell_time_check']['status'] == 'FALSIFIED'
    assert result['reduction_assessment'] == 'FALSIFIED'


def test_one_entry_history_does_not_supply_a_history_invariance_check():
    groups = (geometric(F(1,4),histories=('history.one',)),)*2
    result = assess(groups)
    assert result['entry_history_check']['status'] == 'UNEVALUABLE'
    assert result['reduction_assessment'] == 'UNEVALUABLE'


def test_fixed_delay_is_detected_without_relabeling_residence_time_as_exponential():
    original = geometric(F(1,4),horizon=8)
    delayed = tuple(replace(r,last_step=r.last_step+4) for r in original)
    result = assess((delayed,delayed))
    assert result['empirical_cumulative_probability_check']['status'] == 'FALSIFIED'
    assert result['dwell_time_check']['status'] == 'FALSIFIED'


def test_independent_rate_equations_reject_a_changed_fitted_rate():
    groups = (geometric(F(1,4)),)*2
    result = assess(groups)
    fit = dict(result['fit'],exit_rate_per_second='0.1')
    assessment = science.assess_hazard_arithmetic(samples=science.selected_samples(groups,(1,1)),
        event_ids=('event.product','event.reverse'),dt=F('.5'),fit=fit,tolerance=D('1e-12'))
    assert assessment['status'] == 'FALSIFIED'


def test_whole_run_bootstrap_retains_covariance_and_all_draws():
    groups = tuple(geometric(q,prefix='group.'+str(i)) for i,q in enumerate((F(1,5),F(1,4),F(1,3))))
    rule = selected(groups)
    key = rule.cases[0].ensemble_id
    point = assess(groups,rule=rule)
    report,arrays = science.joint_rate_resampling(selection=rule,ensembles=rule.passages.ensembles,
        datasets={key:groups},clocks={key:(F('.5'),12)},reports={key:point})
    assert report['complete_replicates']==32 and not report['unidentifiable_replicates']
    assert arrays['rate.group-draws'].shape == (32,3)
    rates = arrays['rate.resampled-rates-per-second']
    assert np.allclose(rates[:,0]/rates[:,1],2)
    covariance = np.asarray(report['joint_log_rate_covariance'])
    assert covariance[0,1] == pytest.approx(covariance[0,0],rel=1e-14)
    assert report['independent_units_added']==0
    assert report['simultaneous_log_radius']>0
    assert not arrays['rate.group-draws'].flags.writeable


def test_unidentified_bootstrap_draws_are_retained_and_not_conditioned_away():
    observed = geometric(F(1,4))
    unknown = geometric(F(0))
    groups = (observed,unknown)
    rule = selected(groups)
    key = rule.cases[0].ensemble_id
    report,arrays = science.joint_rate_resampling(selection=rule,ensembles=rule.passages.ensembles,
        datasets={key:groups},clocks={key:(F('.5'),12)},reports={key:assess(groups,rule=rule)})
    assert report['unidentifiable_replicates'] and report['complete_replicates']<32
    assert report['conditional_simultaneous_intervals'] is None
    assert arrays['rate.resampled-rate-observed'].shape == (32,2)


def test_selected_contract_keeps_every_run_history_and_failed_case():
    groups = (geometric(F(1,4)),)*2
    rule = selected(groups)
    assert decode_canonical_bytes(rule.canonical_bytes(),records.PhysicalRateSelection,maximum_bytes=2**20) == rule
    with pytest.raises(ValueError,match='repeats or omits'):
        replace(rule,run_groups=rule.run_groups[:1])
    with pytest.raises(ValueError,match='entry-history'):
        replace(rule,cases=(replace(rule.cases[0],entry_history_ids=('history.a',)),))
    with pytest.raises(ValueError,match='drops an original ensemble'):
        replace(rule,cases=(replace(rule.cases[0],ensemble_id='ensemble.wrong'),))


@pytest.mark.parametrize('factor,expected',((2,'SATISFIED'),(3,'FALSIFIED')))
def test_dissolved_concentration_is_divided_once_and_nonlinearity_is_retained(factor,expected):
    first = replace(passage.ensemble(),ensemble_id='ensemble.a',dissolved_gas_uM=D(1),concentration_source=passage.pin('concentration.a'))
    first = replace(first,events=(replace(first.events[0],role='ASSOCIATION',residence_steps=0),))
    second = replace(first,ensemble_id='ensemble.b',dissolved_gas_uM=D(2),concentration_source=passage.pin('concentration.b'))
    groups = (geometric(F(1,4),events=('event.product',),proportions=(F(1),)),)*2
    faster = (geometric(1-(1-F(1,4))**factor,events=('event.product',),proportions=(F(1),)),)*2
    a,b = selected(groups,item=first),selected(faster,item=second)
    control = records.PhysicalRateControl('control.gas','DISSOLVED_CONCENTRATION',('ensemble.a','ensemble.b'),passage.pin('gas.mapping'),D('.01'))
    # The pure numerical control uses already assessed case reports. Original
    # physical correspondence remains a separate requirement in the reader.
    rule = type('Selection',(),{'controls':(control,)})()
    reports = {'ensemble.a':assess(groups,rule=a),'ensemble.b':assess(faster,rule=b)}
    report = retained.assess_controls(rule,(first,second),reports)['control.gas']
    assert report['status']==expected
    assert report['normalization']=='ASSOCIATION_RATE_DIVIDED_ONCE_BY_FREE_DISSOLVED_uM'


fixture = passage.fixture


def native_rule(original,source):
    settings = source.config.selection.settings
    dt,horizon = settings.step_seconds,settings.steps
    case = records.PhysicalRateCase(original.ensembles[0].ensemble_id,(dt,dt*horizon),('history.one',),passage.pin('quantity.native.exposed'))
    group = records.PhysicalRateRunGroup('group.one',(records.PhysicalRateRunBinding(case.ensemble_id,('run.one',)),))
    return records.PhysicalRateSelection('selection.native.exposed.rate',original,(case,),(group,),(),criteria(),8,17,D('.9'),2**25,
        ('Single exposed ballistic software control. It supplies no physical or statistical admission.',))


def test_original_path_rate_export_reconstructs_without_new_native_calls(fixture,monkeypatch):
    from empirical_lawhood.api import numerical_provenance, recursive_authoring
    from empirical_lawhood.api.domain_composition.rubisco_response import physical_rates as public
    from tests.test_recursive_public_service import _plane
    original,source,_,observed = passage.run_original(fixture,monkeypatch)
    rule = native_rule(original,source)
    plane = _plane(fixture.tmp_path/'rate-custody')
    monkeypatch.setattr(recursive_authoring,'implementation_binding',lambda _:fixture.config.implementation)
    monkeypatch.setattr(numerical_provenance,'capture_numerical_provenance',lambda **k:fixture.config.provenance)
    before = len(observed)
    exported = public.export_physical_rates(selection=rule,sources=(source,),project_root=fixture.tmp_path,
        artifact_writer=plane,output_relative_path='selected/rates')
    read = public.read_physical_rate_export(directory_relative_path='selected/rates',sources=(source,),artifact_writer=plane)
    assert len(observed)==before and read['report']==exported['report']
    row = read['report']['cases'][rule.cases[0].ensemble_id]
    assert row['fit']['cause_rates_per_second']['event.product'] is not None
    assert row['conditional_rate_assessment']=='UNEVALUABLE'
    assert row['required_control_assessments']=={'INTEGRATION_STEP':'UNEVALUABLE'}
    original_row = read['report']['original_passage_analysis']['path_census']['path.0']
    assert original_row['original_cost']==source.original_result.completion.cost.to_document()
    target = plane.root.resolve('selected/rates/readout.json',for_write=False)
    target.write_bytes(target.read_bytes()+b' ')
    with pytest.raises(ArtifactIdentityConflict):
        public.read_physical_rate_export(directory_relative_path='selected/rates',sources=(source,),artifact_writer=plane)


def test_rate_capacity_and_complete_census_refuse_before_original_read(fixture):
    config,phase,original = passage.native_selection(fixture)
    source = RetainedFirstPassagePath('path.0',config,fixture.model,phase,None,None)
    rule = native_rule(original,source)
    with pytest.raises(ValueError,match='allocation'):
        retained.read_physical_rates(selection=replace(rule,maximum_analysis_bytes=1),sources=(source,),assessor_source=fixture.model.material.sources[0])
    with pytest.raises(ValueError,match='omit'):
        retained.read_physical_rates(selection=rule,sources=(),assessor_source=fixture.model.material.sources[0])
    wrong = replace(rule,cases=(replace(rule.cases[0],observation_times_seconds=(D('.123456'),D('.234567'))),))
    with pytest.raises(ValueError,match='exact original grid'):
        retained.validate_physical_rate_inputs(wrong,(source,))


def test_mutation_during_rate_analysis_is_caught_at_final_original_check(fixture,monkeypatch):
    original,source,_,_=passage.run_original(fixture,monkeypatch)
    rule = native_rule(original,source)
    draw = retained.joint_rate_resampling
    stream = source.native_subwork.iter_completed_output
    def changed(definition,output_id,**kwargs):
        first = True
        for block in stream(definition,output_id,**kwargs):
            if first and output_id=='files.raw' and block:
                block=bytes((block[0]^1,))+block[1:]
                first=False
            yield block
    def after(**kwargs):
        result=draw(**kwargs)
        monkeypatch.setattr(source.native_subwork,'iter_completed_output',changed)
        return result
    monkeypatch.setattr(retained,'joint_rate_resampling',after)
    with pytest.raises(ValueError,match='changed|digest|corrupt|original'):
        retained.read_physical_rates(selection=rule,sources=(source,),assessor_source=fixture.model.material.sources[0])


@pytest.mark.parametrize('missing',(False,True))
def test_weighted_descendants_keep_the_full_clock_cost_census_and_missing_weight(fixture,monkeypatch,missing):
    from tests import test_rubisco_weighted_path_continuation as weighted
    original,source,_,observed=weighted.root(fixture,monkeypatch)
    item=original.ensembles[0]
    event=replace(item.events[0],region=replace(item.events[0].region,lower=(D('2.4'),)),residence_steps=3)
    original=replace(original,ensembles=(replace(item,entry_region=replace(item.entry_region,upper=(D('2.4'),)),events=(event,)),))
    continuation,sampler=weighted.rule_for(original,source)
    continuation=replace(continuation,target_physical_steps=8)
    campaign=weighted.population.WeightedPathCampaign('campaign.rate.exposed',continuation,())
    first=weighted.population.read_weighted_path_campaign(selection=campaign,sources=(source,),assessor_source=fixture.model.material.sources[0])
    resampled=weighted.resampling.resample_weighted_paths(selection=sampler,paths=first['paths'])
    prepared=weighted.continuation.prepare_weighted_continuation(rule=continuation,resampling=resampled,
        histories=first['histories'],assessor_source=fixture.model.material.sources[0])
    children=[]
    for i,child in enumerate(prepared['prepared'].children):
        if missing and i==0:
            config=replace(source.config,config_id='config.absent.rate-child',selection=child.selection)
            children.append(RetainedFirstPassagePath(child.path_id,config,source.representation,prepared['phase_bytes'][child.path_id],None,None))
        else:
            children.append(weighted.execute_child(fixture,source,prepared,child))
    campaign=replace(campaign,continuations=(prepared['prepared'],))
    rule=native_rule(original,source)
    rule=replace(rule,passages=campaign,cases=(replace(rule.cases[0],observation_times_seconds=(D('2e-15'),D('4e-15'))),))
    before=len(observed)
    report,_=retained.read_physical_rates(selection=rule,sources=tuple(sorted((source,*children),key=lambda s:s.path_id)),
        assessor_source=fixture.model.material.sources[0])
    assert len(observed)==before
    assert len(report['original_passage_analysis']['original_cost_census'])==3
    case=report['cases'][rule.cases[0].ensemble_id]
    assert case['declared_whole_run_groups']==1
    if missing:
        assert case['fit']['exit_rate_per_second'] is None
        assert case['fit']['reason']=='COMPUTATIONAL_OR_UNASSESSED_WEIGHT'
    else:
        # Both children confirm the event at cumulative step six, not child
        # step two. They remain one original run with exact total weight one.
        assert float(case['fit']['exit_rate_per_second'])==pytest.approx(-math.log(F(5,6))/5e-16,rel=1e-14)
        assert science.rational(1)==case['fit']['assigned_weight']
        assert case['conditional_rate_assessment']=='UNEVALUABLE'


def step_control(fixture):
    config,phase,original=passage.native_selection(fixture)
    first=replace(original.ensembles[0],ensemble_id='ensemble.a')
    second=replace(first,ensemble_id='ensemble.b',events=tuple(replace(e,residence_steps=e.residence_steps*2) for e in first.events))
    fine=replace(config,config_id='config.refined',selection=replace(config.selection,
        settings=replace(config.selection.settings,step_seconds=D('2.5e-16'),steps=8)))
    paths=tuple(replace(original.paths[0],path_id='path.'+suffix,ensemble_id=item.ensemble_id,configuration=cfg.identity)
        for suffix,item,cfg in (('a',first,config),('b',second,fine)))
    original=replace(original,ensembles=(first,second),paths=paths)
    cases=tuple(records.PhysicalRateCase(e.ensemble_id,(D('1e-15'),D('2e-15')),('history.one',),passage.pin('quantity.step')) for e in (first,second))
    group=records.PhysicalRateRunGroup('group.one',tuple(records.PhysicalRateRunBinding(e.ensemble_id,('run.one',)) for e in (first,second)))
    control=records.PhysicalRateControl('control.step','INTEGRATION_STEP',('ensemble.a','ensemble.b'),passage.pin('step.comparison'),D('.01'))
    selected=records.PhysicalRateSelection('selection.step.control',original,cases,(group,),(control,),criteria(),8,17,D('.9'),2**27,
        ('Exposed source/control joins; no physical dynamics or ensemble admission.',))
    sources=(RetainedFirstPassagePath('path.a',config,fixture.model,phase,None,None),
        RetainedFirstPassagePath('path.b',fine,fixture.model,phase,None,None))
    return selected,sources


def test_actual_step_control_preserves_operator_entry_distribution_and_physical_horizon(fixture):
    rule,sources=step_control(fixture)
    capacity=retained.validate_physical_rate_inputs(rule,sources)
    assert capacity['clocks']=={'ensemble.a':(F('5e-16'),4),'ensemble.b':(F('2.5e-16'),8)}
    different=replace(rule.passages.ensembles[1],entry_distribution_source=passage.pin('entry.different'))
    with pytest.raises(ValueError,match='operator or entry ensemble'):
        retained.validate_physical_rate_inputs(replace(rule,passages=replace(rule.passages,ensembles=(rule.passages.ensembles[0],different))),sources)
    bath=replace(rule.controls[0],kind='BATH_FRICTION')
    with pytest.raises(ValueError,match='integration step|stochastic dynamics'):
        retained.validate_physical_rate_inputs(replace(rule,controls=(bath,)),sources)
    changed_duration=replace(rule.passages.ensembles[1],events=rule.passages.ensembles[0].events)
    with pytest.raises(ValueError,match='physical event'):
        retained.validate_physical_rate_inputs(replace(rule,passages=replace(rule.passages,
            ensembles=(rule.passages.ensembles[0],changed_duration))),sources)


def gas_prototype(fixture):
    from empirical_lawhood.domains.rubisco.rubisco_response.catalytic_path_selection import CatalyticProteinRegion
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import prepare_periodic_probe_selection
    model=fixture.model
    site=model.sites[0]
    residues={r.residue_id:r for r in model.residues}
    chain=residues[site.catalytic_residue_id].chain_id
    protein=tuple(r for r in model.residues if r.chain_id==chain)
    qm=tuple(i for i,a in enumerate(model.atoms) if residues[a.residue_id].chain_id==chain
        or i in (*site.magnesium_atom_indices,*site.ligand_atom_indices,*site.gas_atom_indices))
    charge=sum(model.atoms[i].atomic_number for i in qm)%2
    path=replace(fixture.selection.path,reactive_site_id=site.site_id,qm_atom_indices=qm,
        mm_atom_indices=tuple(i for i in range(len(model.atoms)) if i not in set(qm)),
        protein_regions=tuple(CatalyticProteinRegion(r.residue_id,'COMPLETE_RESIDUE') for r in protein),
        gas='CO2',gas_atom_indices=site.gas_atom_indices,qm_formal_charge=charge)
    return prepare_periodic_probe_selection(representation=model,path=path,cell=fixture.selection.cell,
        electronic=fixture.selection.electronic,molecular=fixture.selection.molecular,engine=fixture.selection.engine)


def test_periodic_gas_concentration_keeps_exact_si_volume_and_every_molecule(fixture):
    from empirical_lawhood.domains.rubisco.rubisco_response import physical_gas_concentration as gas
    from empirical_lawhood.domains.rubisco.rubisco_insilico_mechanism.contracts import Exact
    prototype=gas_prototype(fixture)
    molecules=tuple(r.residue_id for r in fixture.model.residues if r.role=='GAS')
    selected=gas.prepare_periodic_gas_concentration(prototype=prototype,representation=fixture.model,gas='CO2',
        free_gas_residue_ids=molecules,bound_gas_residue_ids=(),free_bound_assignment_source=passage.pin('free.bound.exposed'))
    assert selected.cell_volume_angstrom_cubed.fraction==8000
    assert selected.particle_concentration_uM.fraction==F(10**33,602214076000000000000000*8000)
    gas.validate_periodic_gas_concentration(selected,prototype,fixture.model)
    with localcontext() as ctx:
        ctx.prec=3
        assert selected.decimal_uM==gas.prepare_periodic_gas_concentration(prototype=prototype,representation=fixture.model,gas='CO2',
            free_gas_residue_ids=molecules,bound_gas_residue_ids=(),free_bound_assignment_source=passage.pin('free.bound.exposed')).decimal_uM
    with pytest.raises(ValueError,match='exact particle'):
        replace(selected,particle_concentration_uM=Exact.of(F(1)))
    with pytest.raises(ValueError,match='omits or invents'):
        gas.prepare_periodic_gas_concentration(prototype=prototype,representation=fixture.model,gas='CO2',
            free_gas_residue_ids=('residue.invented',),bound_gas_residue_ids=(),free_bound_assignment_source=passage.pin('free.bound.exposed'))
    assert decode_canonical_bytes(selected.canonical_bytes(),gas.PeriodicGasConcentration,maximum_bytes=2**20)==selected
