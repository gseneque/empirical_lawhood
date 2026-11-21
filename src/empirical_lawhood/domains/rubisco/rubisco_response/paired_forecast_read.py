# SPDX-License-Identifier: MPL-2.0
"""Independently reread original suppliers before joining paired endpoints."""

from decimal import Decimal
from fractions import Fraction
import math

from empirical_lawhood.domains.rubisco.rubisco_response.electronic_ensemble_records import ElectronicEnsembleRule
from empirical_lawhood.domains.rubisco.rubisco_response.electronic_ensemble_read import validate_electronic_ensemble_inputs, read_electronic_ensembles
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.paired_forecast_records import PairedForecastSelection
from empirical_lawhood.domains.rubisco.rubisco_response.paired_forecast_science import reduce_forecast_pair
from empirical_lawhood.domains.rubisco.rubisco_response.physical_first_passage_science import fraction, rational
from empirical_lawhood.domains.rubisco.rubisco_response.physical_rate_network_read import validate_physical_supplier_inputs, read_physical_suppliers
from empirical_lawhood.domains.rubisco.rubisco_response.physical_rate_network_records import PhysicalSupplierSelection
from empirical_lawhood.domains.rubisco.rubisco_response.physical_rate_records import initial_passages
from empirical_lawhood.domains.rubisco.rubisco_response.physical_rate_science import status
from empirical_lawhood.domains.rubisco.rubisco_response.reactive_flux_records import ReactiveFluxRule
from empirical_lawhood.domains.rubisco.rubisco_response.reactive_flux_read import validate_reactive_flux_inputs, read_reactive_flux
from empirical_lawhood.domains.rubisco.rubisco_response.retained_native_outputs import recheck_original_native_outputs, scoped_original_reference


READERS = {
    ReactiveFluxRule:(validate_reactive_flux_inputs,read_reactive_flux),
    ElectronicEnsembleRule:(validate_electronic_ensemble_inputs,read_electronic_ensembles),
    PhysicalSupplierSelection:(validate_physical_supplier_inputs,read_physical_suppliers),
}


def _replicates(selection):
    return (selection.rates.bootstrap_replicates if type(selection) is PhysicalSupplierSelection
        else selection.equilibrium.criteria.bootstrap_replicates)


def _population(selection, sources, ensemble_id):
    if type(selection) is PhysicalSupplierSelection:
        original = initial_passages(selection.rates.passages)
        ensemble = next(e for e in original.ensembles if e.ensemble_id == ensemble_id)
        ids = {p.path_id for p in original.paths if p.ensemble_id == ensemble_id}
        selected = tuple(s for s in sources if s.path_id in ids)
    else:
        ensemble = next(e for e in selection.equilibrium.ensembles if e.ensemble_id == ensemble_id)
        ids = {t.trace_id for t in selection.equilibrium.traces if t.ensemble_id == ensemble_id}
        selected = tuple(s for s in sources[:len(selection.equilibrium.traces)] if s.trace_id in ids)
    if not selected or len({s.representation.material.identity for s in selected}) != 1:
        raise ValueError('forecast supplier changes or loses its complete material population')
    return selected[0].representation.material.identity, ensemble.temperature_kelvin


def _operand_definition(operand, supplier, sources, parameter):
    selection = supplier.selection
    kind, key, member = operand.kind, operand.observable_id, operand.member_id
    unit = 's^-1'
    populations = []
    if kind == 'FLUX_RATE' and type(selection) is ReactiveFluxRule:
        surface = next((s for s in selection.surfaces if s.surface_id == key),None)
        if surface is None:
            raise ValueError('forecast flux observable is outside the selected surface census')
        populations.append(_population(selection,sources,surface.ensemble_id))
    elif kind == 'ELECTRONIC_RATE' and type(selection) is ElectronicEnsembleRule:
        pair = next((p for p in selection.pairs if p.pair_id == key),None)
        if pair is None:
            raise ValueError('forecast electronic observable is outside the selected pair census')
        populations.append(_population(selection,sources,pair.ensemble_id))
    elif kind in {'PASSAGE_RATE','PROCESSING_RATE','BULK_CAPTURE'} and type(selection) is PhysicalSupplierSelection:
        original = initial_passages(selection.rates.passages)
        if kind == 'PASSAGE_RATE':
            ensemble = next((e for e in original.ensembles if e.ensemble_id == key),None)
            event = next((e for e in ensemble.events if e.event_id == member),None) if ensemble else None
            if event is None:
                raise ValueError('forecast passage observable changes its selected competing event')
            populations.append(_population(selection,sources,key))
            if event.role == 'ASSOCIATION':
                if ensemble.dissolved_gas_uM is None or ensemble.concentration_source is None:
                    raise ValueError('forecast bulk capture lacks its original dissolved concentration')
                unit = 'uM^-1 s^-1'
            if parameter in {'b','d_c','d_o'} and event.role != 'REVERSE':
                raise ValueError('forecast reversal must use the original reverse event')
        else:
            if kind == 'BULK_CAPTURE':
                reduction = next((r for r in selection.encounter_reductions if r.reduction_id == key),None)
                if reduction is None:
                    raise ValueError('forecast capture changes its selected encounter elimination')
                network_id = reduction.network_id
                unit = 'uM^-1 s^-1'
                populations.append(_population(selection,sources,reduction.association.ensemble_id))
            else:
                network_id = key
            network = next((n for n in selection.networks if n.network_id == network_id),None)
            if network is None:
                raise ValueError('forecast processing changes its complete selected network')
            expected = ('CARBON' if parameter in {'c','r_c','d_c'} else 'OXYGEN')
            if not network.role.startswith(expected):
                raise ValueError('forecast substitutes carbon and oxygen network meanings')
            if kind == 'PROCESSING_RATE':
                if not network.role.endswith('PROCESSING'):
                    raise ValueError('forecast processing must include product release and substrate-ready return')
                outcome = 'REVERSE_RETURN' if parameter in {'d_c','d_o'} else 'PRODUCTIVE_RETURN'
                if member != outcome:
                    raise ValueError('forecast changes a productive versus reverse processing outcome')
            populations.extend(_population(selection,sources,s.outgoing_ensemble_id)
                for s in network.states if s.terminal_outcome is None)
    else:
        raise ValueError('forecast rate kind is incompatible with its original supplier')
    expected_unit = 'uM^-1 s^-1' if parameter in {'c','o'} else 's^-1'
    if unit != expected_unit:
        raise ValueError('forecast changes physical seconds or counts bulk access twice')
    if parameter in {'r_c','r_o'} and kind != 'PROCESSING_RATE':
        raise ValueError('forecast processing needs the complete release/return network')
    return populations


def validate_paired_forecast_inputs(selection, sources):
    exact(selection,PairedForecastSelection)
    if type(sources) is not tuple:
        raise TypeError('forecast requires one immutable complete original carrier census')
    used = {i for s in selection.suppliers for i in s.source_indices}
    if used != set(range(len(sources))):
        raise ValueError('forecast carrier census omits or adds original inputs')
    configs = [s.config.identity for s in sources if s.config is not None]
    if len(configs) != len(set(configs)):
        raise ValueError('shared original configurations must use one carrier and one original cost')
    counts = {_replicates(s.selection) for s in selection.suppliers}
    if len(counts)>1:
        raise ValueError('forecast joint draws must preserve the complete common replicate denominator')
    n = next(iter(counts),0)
    needed = max(1,n)*len(selection.cases)*65536+len(selection.suppliers)*65536
    if needed > selection.maximum_analysis_bytes:
        raise ValueError('forecast exceeds its selected complete joint analysis allocation')
    suppliers, stocks, capacities, streams = {},{},{},{}
    # Validate all structural joins before opening any original result.
    for supplier in selection.suppliers:
        selected = tuple(sources[i] for i in supplier.source_indices)
        suppliers[supplier.supplier_id] = supplier,selected
        capacities[supplier.supplier_id] = READERS[type(supplier.selection)][0](supplier.selection,selected)
        for i in supplier.source_indices:
            if stocks.setdefault(i,supplier.dependence_set_id) != supplier.dependence_set_id:
                raise ValueError('a shared original cannot be relabelled as independent supplier evidence')
            config = sources[i].config
            if config is not None:
                settings = config.selection.settings
                if hasattr(settings,'random_seed'):
                    stream = (settings.random_generator,settings.random_seed)
                    if streams.setdefault(stream,supplier.dependence_set_id) != supplier.dependence_set_id:
                        raise ValueError('shared original random streams cannot become independent forecast suppliers')
    for case in selection.cases:
        for pair in case.rates:
            for operand,material in ((pair.wild_type,case.case.parent),(pair.mutant,case.case.mutant)):
                if operand is None:
                    continue
                supplier,selected = suppliers[operand.supplier_id]
                populations = _operand_definition(operand,supplier,selected,pair.parameter)
                if any(identity != material.identity or temp is not None and temp != case.context.temperature_k
                        for identity,temp in populations):
                    raise ValueError('forecast substitutes its actual paired material or selected temperature')
    return dict(joint_replicates=n,estimated_joint_workspace_bytes=needed,
        selected_joint_workspace_bytes=selection.maximum_analysis_bytes,supplier_capacity=capacities)


def _positive(value):
    if value is None:
        return None
    value = fraction(value) if type(value) is dict else Fraction(Decimal(value)) if type(value) is str else Fraction(value)
    return value if value > 0 else None


def _exp(value):
    try:
        return _positive(math.exp(value)) if value is not None else None
    except OverflowError:
        return None


def _observable(operand, supplier, report, replicate=None):
    selection = supplier.selection
    key,member,kind = operand.observable_id,operand.member_id,operand.kind
    if kind == 'FLUX_RATE':
        row = report['cases'][key]
        value = row['dynamics'][selection.primary_dynamics_id]['plateau_rate_per_second']
        if replicate is not None:
            column = dict(surface_id=key,dynamics_id=selection.primary_dynamics_id,quantity='log_plateau_rate_per_second')
            index = report['joint_uncertainty']['columns'].index(column)
            value = _exp(report['joint_uncertainty']['joint_values'][replicate][index])
        return _positive(value),row['conditional_flux_assessment']
    if kind == 'ELECTRONIC_RATE':
        row = report['pairs'][key]
        value = row['primary_rate_per_second']
        if replicate is not None:
            index = report['joint']['columns'].index('log-rate.'+key+'.per-second')
            value = _exp(report['joint']['joint_values'][replicate][index])
        assessment = status(row['selected_golden_rule_criteria'],report['joint']['status'],
            report['equilibrium']['statistics']['selected_numerical_sampling_criteria'])
        return _positive(value),assessment
    if kind == 'PASSAGE_RATE':
        original = report['original_rate_analysis']
        row = original['cases'][key]
        value = row['fit']['cause_rates_per_second'][member]
        if replicate is not None:
            index = original['joint_uncertainty']['columns'].index((key,member))
            value = original['joint_uncertainty']['resampled_decimal_rates_per_second'][replicate][index]
        value = _positive(value)
        ensemble = next(e for e in initial_passages(selection.rates.passages).ensembles if e.ensemble_id == key)
        event = next(e for e in ensemble.events if e.event_id == member)
        if event.role == 'ASSOCIATION' and value is not None:
            value /= Fraction(ensemble.dissolved_gas_uM)
        return value,row['conditional_rate_assessment']
    if kind == 'PROCESSING_RATE':
        row = report['networks'][key]
        value = row.get('moment_quotients_per_second',{}).get(member)
        assessment = row['conditional_memoryless_reduction']
        column = (key,'moment_quotient_per_second.'+member)
    else:
        row = report['encounter_reductions'][key]
        value,assessment = row['coefficient_per_uM_second'],row['status']
        column = (key,'coefficient_per_uM_second')
    if replicate is not None:
        index = report['joint_network_realizations']['columns'].index(column)
        value = report['joint_network_realizations']['exact_rational_realizations'][replicate][index]
    return _positive(value),assessment


def _schedule(supplier, report, arrays):
    selection = supplier.selection
    if type(selection) is PhysicalSupplierSelection:
        return dict(kind='WHOLE_RUN_GROUPS',groups=tuple(g.group_id for g in selection.rates.run_groups),
            draws=arrays['rate.group-draws'].tolist())
    original = report['original_equilibrium_analysis'] if type(selection) is ReactiveFluxRule else report['equilibrium']
    bootstrap = original['statistics']['bootstrap']
    return dict(kind='CIRCULAR_CONFIGURATION_BLOCKS',
        groups={k:{name:v[name] for name in ('samples','block_samples')} for k,v in bootstrap['groups'].items()},
        draws=bootstrap['block_starts'])


def _failed_draws(supplier, report):
    if type(supplier.selection) is PhysicalSupplierSelection:
        rows = (*report['original_rate_analysis']['joint_uncertainty']['unidentifiable_replicates'],
            *report['joint_network_realizations']['incomplete_replicates'])
    else:
        rows = report['joint_uncertainty' if type(supplier.selection) is ReactiveFluxRule else 'joint']['failed_replicates']
    return {r['replicate'] for r in rows}


def _original_costs(sources):
    """Charge each original carrier once; missing costs remain unknown."""
    census = []
    for index, source in enumerate(sources):
        result = source.original_result
        census.append(dict(source_index=index,
            original=None if result is None else scoped_original_reference(source).to_document(),
            completion=None if result is None else result.completion.to_document(),
            absence='NOT_SUPPLIED_NOT_PROVEN_NONENTRY' if result is None else None))
    totals, known, unknown = {}, {}, {}
    for field in ('cpu_seconds', 'wall_seconds', 'retained_bytes'):
        values = [None if s.original_result is None else getattr(s.original_result.completion.cost, field) for s in sources]
        totals[field] = None if any(v is None for v in values) else rational(sum(map(Fraction, values), Fraction()))
        known[field] = rational(sum((Fraction(v) for v in values if v is not None), Fraction()))
        unknown[field] = sum(v is None for v in values)
    return dict(carriers=tuple(census), total=totals, known_subtotal=known, unknown_carriers=unknown,
        interpretation='SUM_OF_ORIGINAL_TASK_COSTS_NOT_ELAPSED_MAKESPAN_OR_ADDITIONAL_ANALYSIS_COST')


def read_paired_forecast(*, selection, sources, assessor_source):
    import numpy as np
    capacity = validate_paired_forecast_inputs(selection,sources)
    reports,schedules,sets = {},{},{}
    for supplier in selection.suppliers:
        selected = tuple(sources[i] for i in supplier.source_indices)
        report,arrays = READERS[type(supplier.selection)][1](
            selection=supplier.selection,sources=selected,assessor_source=assessor_source)
        reports[supplier.supplier_id] = report
        schedule = _schedule(supplier,report,arrays)
        schedules[supplier.supplier_id] = schedule
        if sets.setdefault(supplier.dependence_set_id,schedule) != schedule:
            raise ValueError('dependent suppliers must reuse exactly the same original resampling units and draws')
        del arrays
    suppliers = {s.supplier_id:s for s in selection.suppliers}
    failed_supplier_draws = {s.supplier_id:_failed_draws(s,reports[s.supplier_id]) for s in selection.suppliers}
    def evaluate(case,replicate):
        rates = dict(wild_type={},mutant={})
        census = {}
        for pair in case.rates:
            for arm,operand in (('wild_type',pair.wild_type),('mutant',pair.mutant)):
                value,assessment = (None,'UNEVALUABLE') if operand is None else _observable(
                    operand,suppliers[operand.supplier_id],reports[operand.supplier_id],replicate)
                if operand is not None and replicate in failed_supplier_draws[operand.supplier_id]:
                    value,assessment = None,'UNEVALUABLE'
                rates[arm][pair.parameter] = value
                census[arm+'.'+pair.parameter] = dict(value=rational(value) if value is not None else None,
                    assessment=assessment,source=operand.to_document() if operand else None)
        result = reduce_forecast_pair(case,rates,realization_id=case.case_id+('.point' if replicate is None else '.draw.'+str(replicate)),
            source=selection.identity,dependence_group_id='dependence.'+selection.selection_id)
        result['supplier_assessment'] = status(*(r['assessment'] for r in census.values()))
        # Keep endpoint arithmetic visible even when its supplier has failed.
        # A conditional forecast additionally requires the complete assessed
        # supplier census, including the reversal absent from limiting ratios.
        result['conditional_forecast_status'] = status(result['owner_criteria'], result['supplier_assessment'],
            'UNEVALUABLE' if result['missing_operands'] else 'SATISFIED')
        if replicate is None:
            result['rate_census'] = census
        return result
    points = {c.case_id:evaluate(c,None) for c in selection.cases}
    draws,failed = [],[]
    n = capacity['joint_replicates']
    projected = np.zeros((n,len(selection.cases)*3),dtype='<f8')
    observed = np.zeros(projected.shape,dtype='|b1')
    for replicate in range(n):
        current = {c.case_id:evaluate(c,replicate) for c in selection.cases}
        missing = ['supplier.'+s for s,failed in failed_supplier_draws.items() if replicate in failed]
        for i,case in enumerate(selection.cases):
            row = current[case.case_id]
            if row['endpoint'] is None:
                missing.append(case.case_id)
                continue
            values = (*row['turnover_ratio_bounds'],row['specificity_ratio'])
            for j,value in enumerate(values):
                try:
                    v = float(fraction(value))
                except OverflowError:
                    v = math.inf
                if math.isfinite(v) and v>0:
                    projected[replicate,3*i+j],observed[replicate,3*i+j] = v,True
                else:
                    missing.append(case.case_id+'.binary64-projection')
        draws.append(current)
        if missing:
            failed.append(dict(replicate=replicate,missing=tuple(sorted(set(missing)))))
    complete = n>=2 and not failed
    covariance = np.atleast_2d(np.cov(np.log(projected),rowvar=False,ddof=1)).tolist() if complete else None
    incomplete = {row['replicate'] for row in failed}
    joint_criteria = tuple(status(*(r['conditional_forecast_status'] for r in draw.values()),
        'UNEVALUABLE' if index in incomplete else 'SATISFIED') for index, draw in enumerate(draws))
    for value in (projected,observed):
        value.setflags(write=False)
    recheck_original_native_outputs(sources,description='paired supplier forecast')
    return dict(selection=selection.identity.to_document(),assessor_source=assessor_source.to_document(),
        cases=points,original_supplier_analyses=reports,original_draw_schedules=schedules,
        joint=dict(assigned_replicates=n,retained_replicates=len(draws),failed_replicates=failed,realizations=draws,
            point_criteria=status(*(r['conditional_forecast_status'] for r in points.values())),
            realization_criteria=joint_criteria,
            criterion_counts={value:joint_criteria.count(value) for value in ('SATISFIED','FALSIFIED','UNEVALUABLE')},
            columns=tuple(c.case_id+'.'+q for c in selection.cases for q in ('turnover-lower','turnover-upper','specificity')),
            log_covariance=covariance,independent_units_added=0,
            interpretation='CONDITIONAL_EMPIRICAL_JOINT_VARIATION_NO_COVERAGE_CLAIM',
            dependence='COMMON_ORIGINAL_DRAWS_WITHIN_SETS_EXPLICIT_CONDITIONAL_INDEPENDENCE_BETWEEN_SETS'),
        original_cost_scope='ONE_DEDUPLICATED_NATIVE_CARRIER_CENSUS_NESTED_REPORTS_ARE_REFERENCES_NOT_EXTRA_COST',
        original_costs=_original_costs(sources),
        original_carriers=len(sources),original_results=sum(s.original_result is not None for s in sources),
        original_native_receipts=tuple(s.original_result.receipt.to_document() for s in sources if s.original_result is not None),
        capacity={k:v for k,v in capacity.items() if k!='supplier_capacity'},
        assumptions=selection.assumptions,new_native_calls=0,new_reference_evaluations=0,
        physical_admission='UNEVALUABLE',biological_predictive_validity='UNEVALUABLE',
        evidence_scope=selection.interpretation),{'forecast.joint-endpoints':projected,'forecast.joint-observed':observed}
