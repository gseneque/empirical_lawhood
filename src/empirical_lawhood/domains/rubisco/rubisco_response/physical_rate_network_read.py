# SPDX-License-Identifier: MPL-2.0
"""Join original physical rates to complete processing and encounter networks."""

from decimal import Decimal
from fractions import Fraction
import math

from empirical_lawhood.domains.matrix.input_contracts import MAXIMUM_MATRIX_ARRAY_BYTES
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.physical_first_passage_science import rational
from empirical_lawhood.domains.rubisco.rubisco_response.physical_rate_records import initial_passages
from empirical_lawhood.domains.rubisco.rubisco_response.physical_rate_read import validate_physical_rate_inputs, read_physical_rates
from empirical_lawhood.domains.rubisco.rubisco_response.physical_rate_science import status
from empirical_lawhood.domains.rubisco.rubisco_response.physical_rate_network_records import PhysicalSupplierSelection, PhysicalRateOperand
from empirical_lawhood.domains.rubisco.rubisco_response.physical_rate_network_science import network_moments, summarize_network, assess_encounter_elimination
from empirical_lawhood.domains.rubisco.rubisco_response.retained_native_outputs import recheck_original_native_outputs


def validate_physical_supplier_inputs(selection, sources):
    exact(selection,PhysicalSupplierSelection)
    capacity = validate_physical_rate_inputs(selection.rates,sources)
    ensembles = {e.ensemble_id:e for e in initial_passages(selection.rates.passages).ensembles}
    for network in selection.networks:
        states = {s.state_id:s for s in network.states}
        expected = set()
        for state in network.states:
            if state.terminal_outcome is not None:
                continue
            ensemble = ensembles.get(state.outgoing_ensemble_id)
            if ensemble is None or state.entry_distribution_source != ensemble.entry_distribution_source:
                raise ValueError('physical network changes the complete original entry distribution or state-rate ensemble')
            expected.update(PhysicalRateOperand(ensemble.ensemble_id,e.event_id) for e in ensemble.events)
        if {e.rate for e in network.edges} != expected:
            raise ValueError('physical network drops or duplicates a selected competing exit, including OTHER outcomes')
        for edge in network.edges:
            ensemble = ensembles[edge.rate.ensemble_id]
            event = next(e for e in ensemble.events if e.event_id==edge.rate.event_id)
            before,after = states[edge.source_state_id],states[edge.target_state_id]
            if event.physical_definition != after.definition:
                raise ValueError('physical network substitutes the actual target-state event definition')
            expected_roles = {'PRODUCTIVE_RETURN':{'SUBSTRATE_READY','RELEASE'},'REVERSE_RETURN':{'REVERSE'},
                'COMMITTED':{'PRODUCTIVE'},'ESCAPED':{'DISSOCIATION','REVERSE'},'OTHER':{'OTHER'}}
            if event.role=='ASSOCIATION' or after.terminal_outcome is not None and event.role not in expected_roles[after.terminal_outcome]:
                raise ValueError('physical network changes product, reverse, encounter or substrate-ready event meaning')
            release = (before.released_3pga,before.released_2phosphoglycolate)!=(after.released_3pga,after.released_2phosphoglycolate)
            if release and event.role not in {'RELEASE','SUBSTRATE_READY'} or event.role=='RELEASE' and not release:
                raise ValueError('physical network product release lacks its corresponding original event and product census')
    for reduction in selection.encounter_reductions:
        ensemble = ensembles.get(reduction.association.ensemble_id)
        if ensemble is None or ensemble.dissolved_gas_uM is None:
            raise ValueError('encounter reduction requires its original sourced free dissolved concentration')
        events = tuple(e for e in ensemble.events if e.event_id==reduction.association.event_id)
        if len(events)!=1 or events[0].role!='ASSOCIATION':
            raise ValueError('encounter reduction must use a bulk-to-encounter association event, not bulk-to-product capture')
    # Exact rational elimination and independent ball matrix exponentials use
    # bounded selected state, query, coefficient and replicate populations.
    edge_digits = 512+sum(len(str(p.weight.denominator)) for p in initial_passages(selection.rates.passages).paths)
    states = sum(len(n.states)**3 for n in selection.networks)
    curves = sum(len(n.observation_times_seconds)*len(n.states)**2 for n in selection.networks)
    curves += sum(len(r.mean_time_multipliers)*len(r.dissolved_concentration_queries_uM)
        *len(next(n for n in selection.networks if n.network_id==r.network_id).states)**2 for r in selection.encounter_reductions)
    columns = sum(2+2*len({s.terminal_outcome for s in n.states if s.terminal_outcome is not None}) for n in selection.networks)+len(selection.encounter_reductions)
    projection = selection.rates.bootstrap_replicates*columns*16
    workspace = states*edge_digits*16+curves*edge_digits*16+projection*4+selection.rates.bootstrap_replicates*columns*edge_digits*8
    if workspace>selection.maximum_network_analysis_bytes or projection>MAXIMUM_MATRIX_ARRAY_BYTES:
        raise ValueError('complete physical network analysis exceeds its selected finite workspace allocation')
    return dict(rate_capacity=capacity,projected_network_array_bytes=projection,estimated_network_workspace_bytes=workspace)


def _rates(report):
    return {PhysicalRateOperand(key,event):(Fraction(Decimal(value)) if value is not None else None)
        for key,row in report['cases'].items() for event,value in row['fit']['cause_rates_per_second'].items()}


def _missing(network, rates):
    return tuple(edge.edge_id for edge in network.edges if rates.get(edge.rate) is None)


def _network_values(moments):
    return {'mean_exit_seconds':moments['mean'],'second_exit_moment_seconds_squared':moments['second_moment'],
        **{'probability.'+key:value for key,value in moments['probabilities'].items()},
        **{'moment_quotient_per_second.'+key:value for key,value in moments['moment_quotients'].items()}}


def resample_networks(selection, rate_report, ensembles):
    """Carry every exact joint rate realization through the full network.

    The network and entry-law hypotheses stay fixed. This conditional parameter
    resampling is not a new test of every hypothesis in each resample.
    """
    import numpy as np
    rate_columns = tuple(PhysicalRateOperand(*key) for key in rate_report['joint_uncertainty']['columns'])
    draws = rate_report['joint_uncertainty']['resampled_decimal_rates_per_second']
    columns = []
    for network in selection.networks:
        outcomes = sorted({s.terminal_outcome for s in network.states if s.terminal_outcome is not None})
        columns.extend((network.network_id,key) for key in ('mean_exit_seconds','second_exit_moment_seconds_squared',
            *('probability.'+key for key in outcomes),*('moment_quotient_per_second.'+key for key in outcomes)))
    columns.extend((r.reduction_id,'coefficient_per_uM_second') for r in selection.encounter_reductions)
    values = np.zeros((len(draws),len(columns)),dtype='<f8')
    valid = np.zeros(values.shape,dtype='<i8')
    retained,failures = [],[]
    by_ensemble = {e.ensemble_id:e for e in ensembles}
    for draw_index,draw in enumerate(draws):
        rates = {key:(Fraction(Decimal(value)) if value is not None else None) for key,value in zip(rate_columns,draw,strict=True)}
        moments, exact_values, missing = {},{},{}
        for network in selection.networks:
            absent = _missing(network,rates)
            if absent:
                missing[network.network_id] = absent
            else:
                computed = network_moments(network,rates)
                moments[network.network_id] = computed
                exact_values.update({(network.network_id,key):value for key,value in _network_values(computed).items()})
        for reduction in selection.encounter_reductions:
            network = moments.get(reduction.network_id)
            association = rates.get(reduction.association)
            if network is None or association is None or 'OTHER' in network['outcomes']:
                missing[reduction.reduction_id] = ('INCOMPLETE_ENCOUNTER_OR_ASSOCIATION',)
            else:
                concentration = Fraction(by_ensemble[reduction.association.ensemble_id].dissolved_gas_uM)
                exact_values[reduction.reduction_id,'coefficient_per_uM_second'] = association/concentration*network['probabilities']['COMMITTED']
        row = []
        for column,key in enumerate(columns):
            value = exact_values.get(key)
            row.append(rational(value) if value is not None else None)
            if value is not None:
                try:
                    floating = float(value)
                except OverflowError:
                    floating = math.inf
                if math.isfinite(floating) and (floating!=0 or value==0):
                    values[draw_index,column],valid[draw_index,column] = floating,1
                else:
                    missing[key[0]+'/'+key[1]] = ('OUTSIDE_BINARY64_PROJECTION',)
        retained.append(tuple(row))
        if missing:
            failures.append(dict(replicate=draw_index,unresolved=missing))
    for array in (values,valid):
        array.setflags(write=False)
    return dict(columns=tuple(columns),exact_rational_realizations=tuple(retained),assigned_replicates=len(draws),
        incomplete_replicates=failures,all_replicates_retained=True,
        conditioning='FIXED_ENTERED_NETWORK_AND_ENTRY_LAWS_NOT_REASSESSED_MODEL_HYPOTHESES',
        covariance_basis='SAME_COMPLETE_GROUP_DRAWS_AS_ORIGINAL_JOINT_RATE_ANALYSIS'),{
            'supplier.resampled-network-quantities':values,'supplier.resampled-network-quantity-observed':valid}


def read_physical_suppliers(*, selection, sources, assessor_source):
    capacity = validate_physical_supplier_inputs(selection,sources)
    report,arrays = read_physical_rates(selection=selection.rates,sources=sources,assessor_source=assessor_source)
    rates = _rates(report)
    networks,moments = {},{}
    for network in selection.networks:
        missing = _missing(network,rates)
        if missing:
            networks[network.network_id] = dict(role=network.role,missing_edges=missing,
                conditional_memoryless_reduction='UNEVALUABLE',reason='MISSING_OR_UNOBSERVED_ORIGINAL_RATE',
                physical_model_admission='UNEVALUABLE')
        else:
            moments[network.network_id] = network_moments(network,rates)
            checks = tuple(report['cases'][e.rate.ensemble_id]['conditional_rate_assessment'] for e in network.edges)
            networks[network.network_id] = summarize_network(network,moments[network.network_id],input_assessments=checks)
    ensembles = initial_passages(selection.rates.passages).ensembles
    indexed = {e.ensemble_id:e for e in ensembles}
    encounters = {}
    for reduction in selection.encounter_reductions:
        current = moments.get(reduction.network_id)
        association = rates.get(reduction.association)
        if current is None or association is None:
            encounters[reduction.reduction_id] = dict(status='UNEVALUABLE',reason='INCOMPLETE_ENCOUNTER_OR_ASSOCIATION',
                coefficient_per_uM_second=None)
            continue
        network = next(n for n in selection.networks if n.network_id==reduction.network_id)
        checks = tuple(report['cases'][edge.rate.ensemble_id]['conditional_rate_assessment'] for edge in network.edges)
        check = status(report['cases'][reduction.association.ensemble_id]['conditional_rate_assessment'],*checks)
        encounters[reduction.reduction_id] = assess_encounter_elimination(selection=reduction,network=network,moments=current,
            association_coefficient=association/Fraction(indexed[reduction.association.ensemble_id].dissolved_gas_uM),input_assessment=check)
    resampling,network_arrays = resample_networks(selection,report,ensembles)
    arrays.update(network_arrays)
    recheck_original_native_outputs(sources,description='physical supplier network assessment')
    return dict(selection=selection.identity.to_document(),assessor_source=assessor_source.to_document(),
        original_rate_analysis=report,networks=networks,encounter_reductions=encounters,joint_network_realizations=resampling,
        capacity={k:v for k,v in capacity.items() if k!='rate_capacity'},
        new_native_calls=0,new_reference_evaluations=0,evidence_scope=selection.scope,
        remaining_requirements=('CHEMICAL_STATE_AND_ENTRY_CORRESPONDENCE','PHYSICAL_RATE_MODEL_AND_BATH_APPLICABILITY',
            'PAIRED_RATE_SUPPORT_AND_ENDPOINT_CLOSURE','BIOLOGICAL_APPLICABILITY')),arrays
