# SPDX-License-Identifier: MPL-2.0
"""Exact competing-exit and slow-release counterexamples; no enzyme evidence."""

from dataclasses import replace
from decimal import Decimal as D, localcontext
from fractions import Fraction as F

import numpy as np
import pytest

from empirical_lawhood.domains.rubisco.rubisco_response import physical_rate_network_records as records
from empirical_lawhood.domains.rubisco.rubisco_response import physical_rate_network_science as science
from empirical_lawhood.domains.rubisco.rubisco_response import physical_rate_network_read as retained
from empirical_lawhood.domains.rubisco.rubisco_response.physical_first_passage_records import PathWeight
from empirical_lawhood.domains.rubisco.rubisco_response.physical_first_passage_science import fraction
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.storage.artifacts import ArtifactIdentityConflict
from tests import test_rubisco_physical_rates as rates
from tests import test_rubisco_physical_first_passage as passage


def network(*, encounter=False, release=False, other=False, ensemble_id='ensemble.exposed.passage'):
    productive = 'COMMITTED' if encounter else 'PRODUCTIVE_RETURN'
    reverse = 'ESCAPED' if encounter else 'REVERSE_RETURN'
    states = [records.PhysicalNetworkState('state.a',passage.pin('definition.a'),ensemble_id,passage.pin('entry.exposed'),None,0,0,False),
        records.PhysicalNetworkState('state.product',passage.pin('definition.product'),None,None,productive,0 if encounter else 2,0,not encounter),
        records.PhysicalNetworkState('state.reverse',passage.pin('definition.reverse'),None,None,reverse,0,0,False)]
    edges = [records.PhysicalNetworkEdge('edge.product','state.a','state.release' if release else 'state.product',
                records.PhysicalRateOperand(ensemble_id,'event.product')),
        records.PhysicalNetworkEdge('edge.reverse','state.a','state.reverse',records.PhysicalRateOperand(ensemble_id,'event.reverse'))]
    if release:
        states.append(records.PhysicalNetworkState('state.release',passage.pin('definition.release'),
            'ensemble.release',passage.pin('entry.release'),None,0,0,False))
        edges.append(records.PhysicalNetworkEdge('edge.release','state.release','state.product',
            records.PhysicalRateOperand('ensemble.release','event.release')))
    if other:
        states.append(records.PhysicalNetworkState('state.other',passage.pin('definition.other'),None,None,'OTHER',0,0,False))
        edges.append(records.PhysicalNetworkEdge('edge.other','state.a','state.other',records.PhysicalRateOperand(ensemble_id,'event.other')))
    return records.PhysicalRateNetwork('network.exposed','CARBON_ENCOUNTER' if encounter else 'CARBON_PROCESSING',
        tuple(sorted(states,key=lambda s:s.state_id)),tuple(sorted(edges,key=lambda e:e.edge_id)),
        (records.PhysicalNetworkEntry('state.a',PathWeight(1,1)),),(D('.1'),D('.5'),D(2)),
        D('.01'),D('.01'),D('.01'),D('1e-10'),192,passage.pin('chemical.correspondence'))


def constants(selected, *, product=F(3),reverse=F(1),release=F(2),other=F(1)):
    values = {'event.product':product,'event.reverse':reverse,'event.release':release,'event.other':other}
    return {edge.rate:values[edge.rate.event_id] for edge in selected.edges}


@pytest.mark.numerical(oracle='Exact competing exponential mean 1/4, second moment 1/8, fate probabilities 3/4 and 1/4')
def test_exact_exponential_network_has_complete_competing_fates_and_independent_enclosure():
    selected = network()
    moments = science.network_moments(selected,constants(selected))
    assert moments['mean']==F(1,4) and moments['second_moment']==F(1,8)
    assert moments['probabilities']=={'PRODUCTIVE_RETURN':F(3,4),'REVERSE_RETURN':F(1,4)}
    assert moments['moment_quotients']=={'PRODUCTIVE_RETURN':F(3),'REVERSE_RETURN':F(1)}
    report = science.summarize_network(selected,moments,input_assessments=('SATISFIED',))
    assert report['conditional_memoryless_reduction']=='SATISFIED'
    assert report['dynamics']['numerical_assessment']=='SATISFIED'
    for row in report['dynamics']['curves']:
        assert all(F(upper)<=F('1e-10') for _,upper in row['absolute_numerical_error_enclosures'])


@pytest.mark.numerical(oracle='Independent conditional sum Exp(5) plus Bernoulli(4/5) times Exp(2), yielding moments 3/5 and 16/25')
def test_product_release_wait_is_part_of_complete_processing_and_can_falsify_exponential_reduction():
    selected = network(release=True)
    moments = science.network_moments(selected,constants(selected,product=F(4),reverse=F(1),release=F(2)))
    # Independent conditional sum: Exp(5) then, with probability 4/5,
    # Exp(2). The productive chemical rate 4 is not the return rate 4/3.
    assert moments['mean']==F(1,5)+F(4,5)*F(1,2)==F(3,5)
    assert moments['second_moment']==F(2,25)+2*F(1,5)*F(4,5)*F(1,2)+F(4,5)*F(2,4)==F(16,25)
    assert moments['moment_quotients']['PRODUCTIVE_RETURN']==F(4,3)
    report = science.summarize_network(selected,moments,input_assessments=('SATISFIED',))
    assert report['squared_cv_assessment']=='FALSIFIED'
    assert report['conditional_memoryless_reduction']=='FALSIFIED'
    assert report['dynamics']['constant_hazard_assessment']=='FALSIFIED'
    slow = science.network_moments(selected,constants(selected,product=F(4),reverse=F(1),release=F(1,100)))
    assert slow['moment_quotients']['PRODUCTIVE_RETURN']<F(1,100)


def test_other_exit_stays_in_total_mean_and_blocks_two_outcome_reduction():
    selected = network(other=True)
    moments = science.network_moments(selected,constants(selected))
    assert moments['probabilities']['OTHER']==F(1,5)
    assert moments['probabilities']['PRODUCTIVE_RETURN']==F(3,5)
    report = science.summarize_network(selected,moments,input_assessments=('SATISFIED',))
    assert report['complete_outcome_reduction']=='UNEVALUABLE'
    assert report['conditional_memoryless_reduction']=='UNEVALUABLE'


def test_terminal_product_count_and_substrate_ready_return_are_required():
    selected = network()
    for change in ({'released_3pga':1},{'substrate_ready':False}):
        states = tuple(replace(s,**change) if s.terminal_outcome=='PRODUCTIVE_RETURN' else s for s in selected.states)
        with pytest.raises(ValueError,match='complete product release'):
            replace(selected,states=states)
    # Carbon product stoichiometry cannot become oxygen processing by a label.
    with pytest.raises(ValueError,match='complete product release'):
        replace(selected,role='OXYGEN_PROCESSING')
    with pytest.raises(ValueError,match='both productive'):
        replace(selected,states=tuple(s for s in selected.states if s.state_id!='state.reverse'),
            edges=tuple(e for e in selected.edges if e.target_state_id!='state.reverse'))


def test_closed_nonabsorbing_class_and_hidden_recapture_are_refused():
    selected = network(release=True)
    a = next(s for s in selected.states if s.state_id=='state.a')
    release = next(s for s in selected.states if s.state_id=='state.release')
    loop = records.PhysicalNetworkEdge('edge.loop','state.release','state.a',records.PhysicalRateOperand(release.outgoing_ensemble_id,'event.loop'))
    # A terminal state made unreachable is not silently dropped.
    with pytest.raises(ValueError,match='entry denominator'):
        replace(selected,edges=tuple(sorted((selected.edges[0],selected.edges[-1],loop),key=lambda e:e.edge_id)))
    released = tuple(replace(s,released_3pga=1) if s.state_id==release.state_id else s for s in selected.states)
    with pytest.raises(ValueError,match='recapture'):
        replace(selected,states=released,edges=tuple(sorted((*selected.edges,loop),key=lambda e:e.edge_id)))
    assert a.released_3pga==0


def test_reachable_closed_cycle_cannot_acquire_a_finite_exit_time():
    selected=network()
    first=records.PhysicalNetworkState('state.dead.a',passage.pin('definition.dead.a'),'ensemble.dead.a',passage.pin('entry.dead.a'),None,0,0,False)
    second=replace(first,state_id='state.dead.b',definition=passage.pin('definition.dead.b'),outgoing_ensemble_id='ensemble.dead.b')
    edges=(records.PhysicalNetworkEdge('edge.dead.entry','state.a',first.state_id,records.PhysicalRateOperand('ensemble.exposed.passage','event.trap')),
        records.PhysicalNetworkEdge('edge.dead.forward',first.state_id,second.state_id,records.PhysicalRateOperand('ensemble.dead.a','event.forward')),
        records.PhysicalNetworkEdge('edge.dead.return',second.state_id,first.state_id,records.PhysicalRateOperand('ensemble.dead.b','event.return')))
    with pytest.raises(ValueError,match='nonabsorbing closed class'):
        replace(selected,states=tuple(sorted((*selected.states,first,second),key=lambda s:s.state_id)),
            edges=tuple(sorted((*selected.edges,*edges),key=lambda e:e.edge_id)))


def test_network_moments_never_fill_a_missing_reverse_edge_with_zero():
    selected = network()
    with pytest.raises(ValueError,match='missing rates are not zeros'):
        science.network_moments(selected,constants(selected,reverse=F(0)))


def encounter_selection(network_id, concentrations):
    return records.PhysicalEncounterReduction('reduction.encounter',network_id,
        records.PhysicalRateOperand('ensemble.bulk','event.arrival'),tuple(map(D,concentrations)),
        (D('.2'),D(1),D(3)),D('.01'),passage.pin('bulk.encounter.correspondence'))


@pytest.mark.parametrize('concentrations,expected',((('.01','.02'),'SATISFIED'),(('1','10'),'FALSIFIED')))
@pytest.mark.numerical(oracle='Exact rational capture mean 3/c+1/2 and elimination error c/6')
def test_encounter_elimination_tests_residence_and_full_capture_law(concentrations,expected):
    selected = network(encounter=True)
    moments = science.network_moments(selected,constants(selected,product=F(2),reverse=F(4)))
    reduced = encounter_selection(selected.network_id,concentrations)
    report = science.assess_encounter_elimination(selection=reduced,network=selected,moments=moments,
        association_coefficient=F(1),input_assessment='SATISFIED')
    assert fraction(report['coefficient_per_uM_second'])==F(1,3)
    assert report['status']==expected
    for row in report['queries']:
        concentration=F(row['dissolved_concentration_uM'])
        assert fraction(row['exact_mean_capture_seconds'])==3/concentration+F(1,2)
        assert fraction(row['elimination_relative_error'])==concentration/6
        assert row['capture_distribution_check']['numerical_assessment']=='SATISFIED'


def test_scipy_propagation_tampering_fails_the_independent_arb_check(monkeypatch):
    from scipy import linalg
    selected = network()
    moments = science.network_moments(selected,constants(selected))
    original = linalg.expm
    monkeypatch.setattr(linalg,'expm',lambda matrix:original(matrix)+np.eye(len(matrix))*.01)
    report = science.assess_network_dynamics(selected,moments)
    assert report['numerical_assessment']=='FALSIFIED'
    assert report['constant_hazard_assessment']=='SATISFIED'


def test_network_enclosures_preserve_decimal_context_and_global_arb_precision():
    from flint import ctx
    selected = network()
    moments = science.network_moments(selected,constants(selected))
    before = ctx.prec
    baseline = science.summarize_network(selected,moments,input_assessments=('SATISFIED',))
    with localcontext() as decimal_context:
        decimal_context.prec=3
        actual=science.summarize_network(selected,moments,input_assessments=('SATISFIED',))
    assert actual==baseline and ctx.prec==before


def test_joint_network_resampling_consumes_exact_decimal_rates_and_preserves_each_draw():
    groups=tuple(rates.geometric(q,prefix='group.'+str(i)) for i,q in enumerate((F(1,5),F(1,4),F(1,3))))
    rule=rates.selected(groups)
    key=rule.cases[0].ensemble_id
    point=rates.assess(groups,rule=rule)
    joint,_=rates.science.joint_rate_resampling(selection=rule,ensembles=rule.passages.ensembles,
        datasets={key:groups},clocks={key:(F('.5'),12)},reports={key:point})
    selected=records.PhysicalSupplierSelection('selection.joint.network',rule,(network(),),(),2**28)
    report,arrays=retained.resample_networks(selected,{'joint_uncertainty':joint},rule.passages.ensembles)
    assert not report['incomplete_replicates']
    assert len(report['exact_rational_realizations'])==len(joint['resampled_decimal_rates_per_second'])==32
    columns={name:i for i,(_,name) in enumerate(report['columns'])}
    for original,projected in zip(joint['resampled_decimal_rates_per_second'],report['exact_rational_realizations'],strict=True):
        forward,reverse=map(lambda value:F(D(value)),original)
        assert fraction(projected[columns['mean_exit_seconds']])==1/(forward+reverse)
        assert fraction(projected[columns['probability.PRODUCTIVE_RETURN']])==forward/(forward+reverse)
        assert fraction(projected[columns['moment_quotient_per_second.PRODUCTIVE_RETURN']])==forward
    assert np.all(arrays['supplier.resampled-network-quantity-observed']==1)


fixture = passage.fixture


def native_supplier(original,source):
    item = original.ensembles[0]
    productive = replace(item.events[0],role='SUBSTRATE_READY')
    reverse = passage.ensemble().events[1]
    item = replace(item,events=(productive,reverse))
    original = replace(original,ensembles=(item,))
    rule = rates.native_rule(original,source)
    graph = network(ensemble_id=item.ensemble_id)
    # Exact event definitions are already bound by the first-passage rule.
    graph = replace(graph,states=tuple(replace(s,entry_distribution_source=item.entry_distribution_source)
        if s.terminal_outcome is None else s for s in graph.states))
    return records.PhysicalSupplierSelection('selection.native.supplier',rule,(graph,),(),2**28)


def test_original_supplier_export_preserves_missing_reverse_and_every_cost(fixture,monkeypatch):
    from empirical_lawhood.api import numerical_provenance, recursive_authoring
    from empirical_lawhood.api.domain_composition.rubisco_response import physical_suppliers as public
    from tests.test_recursive_public_service import _plane
    original,source,_,observed = passage.run_original(fixture,monkeypatch)
    rule = native_supplier(original,source)
    plane = _plane(fixture.tmp_path/'supplier-custody')
    monkeypatch.setattr(recursive_authoring,'implementation_binding',lambda _:fixture.config.implementation)
    monkeypatch.setattr(numerical_provenance,'capture_numerical_provenance',lambda **k:fixture.config.provenance)
    before=len(observed)
    export=public.export_physical_suppliers(selection=rule,sources=(source,),project_root=fixture.tmp_path,
        artifact_writer=plane,output_relative_path='selected/supplier')
    reread=public.read_physical_supplier_export(directory_relative_path='selected/supplier',sources=(source,),artifact_writer=plane)
    assert len(observed)==before and export['report']==reread['report']
    graph=reread['report']['networks']['network.exposed']
    assert graph['missing_edges']==['edge.reverse']
    assert graph['conditional_memoryless_reduction']=='UNEVALUABLE'
    assert len(reread['report']['joint_network_realizations']['incomplete_replicates'])==8
    assert decode_canonical_bytes(rule.canonical_bytes(),records.PhysicalSupplierSelection,maximum_bytes=2**26)==rule
    target=plane.root.resolve('selected/supplier/report.txt',for_write=False)
    target.write_bytes(target.read_bytes()+b'changed')
    with pytest.raises(ArtifactIdentityConflict):
        public.read_physical_supplier_export(directory_relative_path='selected/supplier',sources=(source,),artifact_writer=plane)


def test_actual_network_binding_rejects_chemical_product_as_complete_return(fixture):
    config,phase,original=passage.native_selection(fixture)
    source=rates.RetainedFirstPassagePath('path.0',config,fixture.model,phase,None,None)
    rule=native_supplier(original,source)
    retained.validate_physical_supplier_inputs(rule,(source,))
    item=rule.rates.passages.ensembles[0]
    changed=replace(item,events=(replace(item.events[0],role='PRODUCTIVE'),item.events[1]))
    wrong=replace(rule,rates=replace(rule.rates,passages=replace(rule.rates.passages,ensembles=(changed,))))
    with pytest.raises(ValueError,match='event meaning'):
        retained.validate_physical_supplier_inputs(wrong,(source,))
    states=tuple(replace(s,definition=passage.pin('definition.invented')) if s.terminal_outcome=='REVERSE_RETURN' else s for s in rule.networks[0].states)
    with pytest.raises(ValueError,match='target-state event definition'):
        retained.validate_physical_supplier_inputs(replace(rule,networks=(replace(rule.networks[0],states=states),)),(source,))
    with pytest.raises(ValueError,match='workspace allocation'):
        retained.validate_physical_supplier_inputs(replace(rule,maximum_network_analysis_bytes=1),(source,))
