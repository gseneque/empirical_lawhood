# SPDX-License-Identifier: MPL-2.0
"""Original-supplier joins and exposed independent kinetic falsifiers."""

from dataclasses import replace
from decimal import Decimal as D
from fractions import Fraction as F

import numpy as np
import pytest

from empirical_lawhood.domains.rubisco.rubisco_prediction.kinetic_model import PARAMETER_ORDER, DissolvedGasQuery, FourStateRates, solve_four_state
from empirical_lawhood.domains.rubisco.rubisco_response.disclosed_examples import disclosed_supply
from empirical_lawhood.domains.rubisco.rubisco_response.paired_forecast_science import reduce_forecast_pair
from empirical_lawhood.domains.rubisco.rubisco_response.physical_first_passage_science import fraction
from empirical_lawhood.api.domain_composition.rubisco_response import paired_forecast as public
from empirical_lawhood.storage.artifacts import ArtifactIdentityConflict
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from tests import test_rubisco_electronic_ensembles as electronic
from tests.test_recursive_public_service import _plane

fixture = electronic.fixture


def empty_case(supply=None):
    supply = supply or disclosed_supply()
    return public.ForecastCase('case.forecast.exposed',supply.case,supply.context,
        tuple(public.ForecastRatePair(p,None,None) for p in PARAMETER_ORDER),supply.case.sources[0])


def prepared_empty():
    case = empty_case()
    return public.prepare_paired_forecast(suppliers=(),cases=(case,),dependence_source=case.closure_model,
        maximum_analysis_bytes=2**20,assumptions=('Disclosed software inputs, no scientific evidence.',),sources=())


@pytest.mark.parametrize('factor,processing', [(F(2),F(3)),(F(1),F(1)),(F(1,2),F(3)),(F(1,2),F(3,4))])
def test_complete_reversible_solver_lies_inside_waiting_enclosure_without_independent_marginals(factor,processing):
    case = empty_case()
    wt = FourStateRates(*(D(n) for n in (2,3,5,7,11,13,17,19)))
    mutant = replace(wt,a=D(2)*D(factor.numerator)/D(factor.denominator),
        b=D(37),r_c=D(17)*D(processing.numerator)/D(processing.denominator),c=D(23),d_c=D(29),o=D(31),r_o=D(41))
    result = reduce_forecast_pair(case,dict(wild_type=wt.fractions,mutant=mutant.fractions),
        realization_id='exposed.point',source=case.closure_model,dependence_group_id='group.exposed')
    endpoints = tuple(solve_four_state(r,DissolvedGasQuery(D(20),D(250)),result_id='result.'+str(i)).intrinsic
        for i,r in enumerate((wt,mutant)))
    actual = endpoints[1].kcat_c.fraction/endpoints[0].kcat_c.fraction
    low,high = map(fraction,result['turnover_ratio_bounds'])
    assert low <= actual <= high
    assert fraction(result['specificity_ratio']) == endpoints[1].specificity.fraction/endpoints[0].specificity.fraction
    assert (low,high)==tuple(sorted((factor,processing)))
    assert result['missing_operands']==()


def test_strict_owner_boundary_and_missing_reversal_remain_distinct():
    case = empty_case()
    rates = dict(wild_type={p:F(1) for p in PARAMETER_ORDER},mutant={p:F(1) for p in PARAMETER_ORDER})
    def read():
        return reduce_forecast_pair(case,rates,realization_id='exposed.boundary',source=case.closure_model,
            dependence_group_id='group.exposed')
    assert read()['owner_criteria']=='FALSIFIED'  # exactly one is not a turnover increase
    rates['mutant']['a']=rates['mutant']['r_c']=F(10000000000000000001,10000000000000000000)
    rates['mutant']['d_c']=rates['mutant']['r_c']
    assert read()['owner_criteria']=='SATISFIED'
    rates['wild_type']['b']=None
    row=read()
    assert row['endpoint'] is not None and row['missing_operands']==(('wild_type','b'),)
    rates['mutant']['d_o']=None
    assert read()['endpoint'] is None


def test_unmeasured_full_census_roundtrips_and_exports_without_any_native_entry(fixture,monkeypatch):
    selection = prepared_empty()
    assert decode_canonical_bytes(selection.canonical_bytes(),public.PairedForecastSelection,maximum_bytes=2**20)==selection
    source=selection.dependence_source
    report,arrays=public.read_paired_forecast(selection=selection,sources=(),assessor_source=source)
    row=report['cases'][selection.cases[0].case_id]
    assert len(row['missing_operands'])==16 and row['owner_criteria']=='UNEVALUABLE'
    assert report['joint']['assigned_replicates']==0 and report['joint']['log_covariance'] is None
    assert report['joint']['point_criteria'] == 'UNEVALUABLE'
    assert sum(report['joint']['criterion_counts'].values()) == 0
    assert arrays['forecast.joint-endpoints'].shape==(0,3)
    from empirical_lawhood.api import numerical_provenance, recursive_authoring
    root=fixture.tmp_path/'export'
    writer=_plane(root)
    monkeypatch.setattr(recursive_authoring,'implementation_binding',lambda _:fixture.config.implementation)
    monkeypatch.setattr(numerical_provenance,'capture_numerical_provenance',lambda **k:fixture.config.provenance)
    project=fixture.tmp_path
    exported=public.export_paired_forecast(selection=selection,sources=(),project_root=project,
        artifact_writer=writer,output_relative_path='paired')
    reread=public.read_paired_forecast_export(directory_relative_path='paired',sources=(),artifact_writer=writer)
    assert reread['report']==exported['report'] and reread['new_native_calls']==0
    path=root/'paired'/'report.txt'
    path.write_bytes(path.read_bytes()+b'changed\n')
    with pytest.raises(ArtifactIdentityConflict):
        public.read_paired_forecast_export(directory_relative_path='paired',sources=(),artifact_writer=writer)


def electronic_forecast(fixture,monkeypatch,*,failed_point=False):
    from empirical_lawhood.domains.rubisco.rubisco_response.materials import paired_case
    from empirical_lawhood.domains.rubisco.rubisco_response.contexts import RubiscoAssayContext
    from empirical_lawhood.api.domain_composition.rubisco_response.electronic_ensembles import RetainedEquilibriumTrace
    config,phase,rule=electronic.observed_configuration(fixture)
    fixture.electronic_config=config
    observed,_=electronic.instrument_electronic_operator(fixture,monkeypatch,failed_point=failed_point)
    custody=electronic.acquisition.custody(fixture,config,phase)
    runner=electronic.acquisition.owner.operation_declaration(accelerated=True,observed=True).runner_factory()
    returned=runner.execute_with_native_subwork(custody.context,custody.store)
    result=electronic.acquisition.decode_canonical_bytes(returned.outputs[0].payload,
        electronic.acquisition.owner.ReferenceEquilibriumResult,maximum_bytes=electronic.acquisition.owner.MAX_RETURN)
    carrier=RetainedEquilibriumTrace('trace.original',config,fixture.model,phase,result,custody.store)
    material=fixture.model.material
    pin=material.sources[0]
    case=paired_case(case_id='case.exposed.no-change',parent=material,mutant=material,case_role='NO_CHANGE',
        exposure_group='exposure.exposed',sources=(pin,))
    context=RubiscoAssayContext('context.exposed',config.selection.settings.temperature_kelvin,(D(8),D(8)),'Selected control pH',fixture.model.chemistry,
        'Exposed initial-rate control',(pin,),'NEW_SELECTION')
    supplier=public.ForecastSupplier('supplier.electronic',rule,(0,),'dependence.exposed')
    operand=public.ForecastOperand(supplier.supplier_id,'ELECTRONIC_RATE',rule.pairs[0].pair_id,None,pin)
    selected_case=public.ForecastCase('case.exposed',case,context,
        tuple(public.ForecastRatePair(p,operand if p=='a' else None,operand if p=='a' else None) for p in PARAMETER_ORDER),pin)
    chosen=public.prepare_paired_forecast(suppliers=(supplier,),cases=(selected_case,),dependence_source=pin,
        maximum_analysis_bytes=2**24,assumptions=('Exposed electronic integration; absent chemical suppliers remain missing.',),sources=(carrier,))
    return chosen,(carrier,),observed


@pytest.mark.parametrize('failed_point',(False,True))
def test_original_electronic_join_retains_draw_failures_and_never_replays(fixture,monkeypatch,failed_point):
    chosen,sources,observed=electronic_forecast(fixture,monkeypatch,failed_point=failed_point)
    before=list(observed)
    report,arrays=public.read_paired_forecast(selection=chosen,sources=sources,assessor_source=chosen.dependence_source)
    assert list(observed)==before
    assert report['original_carriers']==report['original_results']==1
    assert len(report['original_native_receipts'])==1
    assert report['joint']['retained_replicates']==chosen.suppliers[0].selection.equilibrium.criteria.bootstrap_replicates
    assert len(report['joint']['failed_replicates'])==report['joint']['assigned_replicates']
    assert not arrays['forecast.joint-observed'].any()
    assert all(np.isfinite(a).all() for a in arrays.values())
    assert report['cases']['case.exposed']['owner_criteria']=='UNEVALUABLE'
    changed=replace(chosen,cases=(replace(chosen.cases[0],context=replace(chosen.cases[0].context,
        temperature_k=chosen.cases[0].context.temperature_k+D(1))),))
    with pytest.raises(ValueError,match='temperature'):
        public.validate_paired_forecast_inputs(changed,sources)


def test_changed_material_and_shared_original_as_independent_refuse_before_read(fixture,monkeypatch):
    chosen,sources,_=electronic_forecast(fixture,monkeypatch)
    supplier=chosen.suppliers[0]
    other=replace(supplier,supplier_id='supplier.second',dependence_set_id='dependence.false-independent')
    cases=chosen.cases[0]
    operand=replace(cases.rates[0].mutant,supplier_id=other.supplier_id)
    changed=replace(chosen,suppliers=(supplier,other),cases=(replace(cases,rates=(replace(cases.rates[0],mutant=operand),*cases.rates[1:])),))
    monkeypatch.setattr(sources[0].native_subwork,'recover',lambda *a,**k:pytest.fail('read before dependence refusal'))
    with pytest.raises(ValueError,match='shared original'):
        public.validate_paired_forecast_inputs(changed,sources)


def test_scf_gap_cannot_be_relabelled_bulk_oxygen_or_product_return(fixture,monkeypatch):
    chosen,sources,_=electronic_forecast(fixture,monkeypatch)
    case=chosen.cases[0]
    operand=case.rates[0].wild_type
    for parameter,match in (('o','bulk access'),('r_c','release/return')):
        changed=replace(chosen,cases=(replace(case,rates=tuple(
            replace(r,wild_type=operand,mutant=operand) if r.parameter==parameter else r for r in case.rates)),))
        with pytest.raises(ValueError,match=match):
            public.validate_paired_forecast_inputs(changed,sources)


def mixed_original_suppliers(fixture, monkeypatch):
    """One electronic/flux parent plus independent original processing work."""
    from types import SimpleNamespace
    from tests import test_rubisco_reactive_flux as flux
    from tests import test_rubisco_physical_rate_networks as networks
    from tests import test_rubisco_physical_first_passage as passage
    path_fixture = SimpleNamespace(**vars(fixture))
    path_fixture.tmp_path = fixture.tmp_path/'processing'
    path_fixture.tmp_path.mkdir()
    path_fixture.workdir = path_fixture.tmp_path/'native'
    path_fixture.config = replace(fixture.config, work_directory=str(path_fixture.workdir))
    chosen, sources, electronic_calls = electronic_forecast(fixture, monkeypatch)
    rule = flux.rule_for(chosen.suppliers[0].selection.equilibrium)
    prepared = flux.prepare(fixture, rule, sources[0])
    shots = tuple(flux.retained.RetainedReactiveFluxShot(s.shot_id) for s in prepared['prepared'].shots)
    original, path, _, processing_calls = passage.run_original(path_fixture, monkeypatch)
    processing = networks.native_supplier(original, path)
    processing = replace(processing, rates=replace(processing.rates,
        bootstrap_replicates=rule.equilibrium.criteria.bootstrap_replicates))
    sources = (*sources, *shots, path)
    pin = chosen.dependence_source
    suppliers = (chosen.suppliers[0], public.ForecastSupplier('supplier.flux', rule,
        tuple(range(1+len(shots))), chosen.suppliers[0].dependence_set_id),
        public.ForecastSupplier('supplier.processing', processing, (len(sources)-1,), 'dependence.processing'))
    formation = public.ForecastOperand('supplier.flux', 'FLUX_RATE', rule.surfaces[0].surface_id, None, pin)
    electronic_operand = chosen.cases[0].rates[0].wild_type
    processing_operand = public.ForecastOperand('supplier.processing', 'PROCESSING_RATE',
        processing.networks[0].network_id, 'PRODUCTIVE_RETURN', pin)
    operands = {'a':formation, 'd_o':electronic_operand, 'r_c':processing_operand}
    case = replace(chosen.cases[0], rates=tuple(public.ForecastRatePair(p, operands.get(p), operands.get(p))
        for p in PARAMETER_ORDER))
    selected = public.prepare_paired_forecast(suppliers=suppliers, cases=(case,), dependence_source=pin,
        maximum_analysis_bytes=2**26, assumptions=('Exposed shared configurations and independent processing population.',), sources=sources)
    return selected, sources, electronic_calls, processing_calls


def test_authenticated_mixed_suppliers_export_shared_costs_missing_rates_and_joint_draws(fixture, monkeypatch):
    from empirical_lawhood.api import numerical_provenance, recursive_authoring
    selected, sources, electronic_calls, processing_calls = mixed_original_suppliers(fixture, monkeypatch)
    before = (len(electronic_calls), len(processing_calls))
    writer = _plane(fixture.tmp_path/'mixed-export')
    monkeypatch.setattr(recursive_authoring, 'implementation_binding', lambda _:fixture.config.implementation)
    monkeypatch.setattr(numerical_provenance, 'capture_numerical_provenance', lambda **k:fixture.config.provenance)
    exported = public.export_paired_forecast(selection=selected, sources=sources, project_root=fixture.tmp_path,
        artifact_writer=writer, output_relative_path='paired')
    reread = public.read_paired_forecast_export(directory_relative_path='paired', sources=sources, artifact_writer=writer)
    report = reread['report']
    assert report == exported['report'] and before == (len(electronic_calls), len(processing_calls))
    assert report['original_results'] == len(report['original_native_receipts']) == 2
    schedules = report['original_draw_schedules']
    assert schedules['supplier.electronic'] == schedules['supplier.flux']
    denominator = selected.suppliers[0].selection.equilibrium.criteria.bootstrap_replicates
    assert report['joint']['retained_replicates'] == report['joint']['assigned_replicates'] == denominator
    assert len(report['joint']['failed_replicates']) == denominator
    assert len(report['joint']['realization_criteria']) == sum(report['joint']['criterion_counts'].values()) == denominator
    assert report['joint']['criterion_counts']['SATISFIED'] == 0
    assert report['joint']['log_covariance'] is None
    row = report['cases'][selected.cases[0].case_id]
    assert row['owner_criteria'] == 'UNEVALUABLE' and row['conditional_forecast_status'] != 'SATISFIED'
    from empirical_lawhood.api.domain_composition.rubisco_response.pilot_programme import _gate_status
    assert _gate_status('PAIRED_FORECAST', report) != 'SATISFIED'
    kinds = {'supplier.electronic':'ELECTRONIC_ENSEMBLES', 'supplier.flux':'REACTIVE_FLUX',
        'supplier.processing':'PHYSICAL_SUPPLIERS'}
    assert set(report['original_supplier_analyses']) == set(kinds)
    for name, original in report['original_supplier_analyses'].items():
        assert _gate_status(kinds[name], original) in {'SATISFIED', 'FALSIFIED', 'UNEVALUABLE'}
    expected = sum(F(s.original_result.completion.cost.wall_seconds) for s in sources if s.original_result is not None)
    assert fraction(report['original_costs']['known_subtotal']['wall_seconds']) == expected
    assert report['original_costs']['unknown_carriers']['wall_seconds'] == len(sources)-2
    if len(sources) > 2:
        assert report['original_costs']['total']['wall_seconds'] is None
    target = writer.root.resolve('paired/arrays.npz', for_write=False)
    raw = target.read_bytes()
    target.write_bytes(raw[:-1]+bytes((raw[-1]^1,)))
    with pytest.raises(ArtifactIdentityConflict):
        public.read_paired_forecast_export(directory_relative_path='paired', sources=sources, artifact_writer=writer)


def test_mixed_supplier_common_draw_and_original_mutation_refusals(fixture, monkeypatch):
    from empirical_lawhood.domains.rubisco.rubisco_response import paired_forecast_read as reader
    selected, sources, _, _ = mixed_original_suppliers(fixture, monkeypatch)
    # The same original cannot be assigned a second independence label.
    suppliers = tuple(replace(s, dependence_set_id='dependence.false') if s.supplier_id == 'supplier.flux' else s
        for s in selected.suppliers)
    with pytest.raises(ValueError, match='shared original'):
        public.validate_paired_forecast_inputs(replace(selected, suppliers=suppliers), sources)
    original = reader.reduce_forecast_pair
    stream = sources[0].native_subwork.iter_completed_output
    def changed(definition, output_id, **kwargs):
        first = True
        for block in stream(definition, output_id, **kwargs):
            if first and block and output_id == 'files.raw':
                block = bytes((block[0]^1,))+block[1:]
                first = False
            yield block
    def reduce_then_change(*args, **kwargs):
        result = original(*args, **kwargs)
        monkeypatch.setattr(sources[0].native_subwork, 'iter_completed_output', changed)
        return result
    monkeypatch.setattr(reader, 'reduce_forecast_pair', reduce_then_change)
    with pytest.raises(ValueError, match='original output changed'):
        public.read_paired_forecast(selection=selected, sources=sources, assessor_source=selected.dependence_source)
