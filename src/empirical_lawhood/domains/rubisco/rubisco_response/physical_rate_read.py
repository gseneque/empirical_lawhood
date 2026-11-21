# SPDX-License-Identifier: MPL-2.0
"""Reconstruct conditional rates from every authenticated original path."""

from decimal import Decimal, localcontext
from fractions import Fraction
import math

from empirical_lawhood.domains.matrix.input_contracts import MAXIMUM_MATRIX_ARRAY_BYTES
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.physical_first_passage_read import validate_first_passage_inputs, read_first_passages
from empirical_lawhood.domains.rubisco.rubisco_response.physical_first_passage_records import FirstPassageSelection
from empirical_lawhood.domains.rubisco.rubisco_response.physical_first_passage_science import fraction
from empirical_lawhood.domains.rubisco.rubisco_response.physical_path_protocol import physical_settings
from empirical_lawhood.domains.rubisco.rubisco_response.physical_gas_concentration import validate_periodic_gas_concentration
from empirical_lawhood.domains.rubisco.rubisco_response.physical_rate_records import PhysicalRateSelection, initial_passages
from empirical_lawhood.domains.rubisco.rubisco_response.physical_rate_science import RateObservation, assess_case, joint_rate_resampling, status
from empirical_lawhood.domains.rubisco.rubisco_response.retained_native_outputs import recheck_original_native_outputs
from empirical_lawhood.domains.rubisco.rubisco_response.weighted_path_population import validate_weighted_path_campaign_inputs, read_weighted_path_campaign


def validate_physical_rate_inputs(selection, sources):
    exact(selection, PhysicalRateSelection)
    initial = initial_passages(selection.passages)
    if type(selection.passages) is FirstPassageSelection:
        validate_first_passage_inputs(selection.passages, sources)
    else:
        validate_weighted_path_campaign_inputs(selection.passages, sources)
    by_id = {s.path_id:s for s in sources}
    clocks, prototypes, representations = {}, {}, {}
    for path in initial.paths:
        config = by_id[path.path_id].config
        dynamics = physical_settings(config)
        steps = dynamics.steps if type(selection.passages) is FirstPassageSelection else selection.passages.initial_rule.target_physical_steps
        clocks[path.ensemble_id] = Fraction(dynamics.step_seconds), steps
        prototypes[path.ensemble_id] = config.original.selection
        representations[path.ensemble_id] = by_id[path.path_id].representation
    for case in selection.cases:
        dt, steps = clocks[case.ensemble_id]
        grid = tuple(Fraction(t)/dt for t in case.observation_times_seconds)
        if any(t.denominator != 1 for t in grid) or grid[-1] != steps:
            raise ValueError('physical rate dwell boundaries must use exact original grid points through the complete horizon')
    ensembles = {e.ensemble_id:e for e in initial.ensembles}
    cases = {c.ensemble_id:c for c in selection.cases}
    concentrations = {c.identity:c for c in selection.gas_concentrations}
    for ensemble in initial.ensembles:
        selected = concentrations.get(ensemble.concentration_source)
        if selected is not None:
            validate_periodic_gas_concentration(selected,prototypes[ensemble.ensemble_id],representations[ensemble.ensemble_id])
            if ensemble.dissolved_gas_uM != selected.decimal_uM:
                raise ValueError('physical rate substitutes the exact selected periodic particle concentration')
    for control in selection.controls:
        selected = tuple(ensembles[key] for key in control.ensemble_ids)
        first = selected[0]
        for other in selected[1:]:
            def event_definition(ensemble):
                dt=clocks[ensemble.ensemble_id][0]
                return tuple((e.event_id,e.region,e.role,e.physical_definition,e.residence_steps*dt) for e in ensemble.events)
            if (event_definition(other) != event_definition(first) or other.entry_region != first.entry_region
                    or other.coordinate_window.cv_kinds != first.coordinate_window.cv_kinds
                    or other.coordinate_convention.center_units != first.coordinate_convention.center_units
                    or other.dynamics_model != first.dynamics_model or other.temperature_kelvin != first.temperature_kelvin):
                raise ValueError('physical rate control changes its physical event, coordinate, bath or temperature meaning')
            if (cases[other.ensemble_id].observation_times_seconds != cases[first.ensemble_id].observation_times_seconds
                    or cases[other.ensemble_id].entry_history_ids != cases[first.ensemble_id].entry_history_ids):
                raise ValueError('physical rate control changes its selected dwell-time or entry-history census')
            if control.kind != 'DISSOLVED_CONCENTRATION' and (
                    other.prototype != first.prototype or other.coordinate_window != first.coordinate_window
                    or other.coordinate_convention != first.coordinate_convention
                    or other.entry_distribution_source != first.entry_distribution_source
                    or other.dissolved_gas_uM != first.dissolved_gas_uM or other.concentration_source != first.concentration_source):
                raise ValueError('step or bath control changes its original reference operator or entry ensemble')
            if control.kind != 'BATH_FRICTION' and other.friction_per_picosecond != first.friction_per_picosecond:
                raise ValueError('physical rate control changes an unselected bath friction')
            if control.kind != 'INTEGRATION_STEP' and clocks[other.ensemble_id][0] != clocks[first.ensemble_id][0]:
                raise ValueError('physical rate control changes an unselected integration step')
        if len({dt*n for dt,n in (clocks[e.ensemble_id] for e in selected)}) != 1:
            raise ValueError('physical rate control changes its prospective physical observation horizon')
        if control.kind == 'INTEGRATION_STEP':
            values = {clocks[e.ensemble_id][0] for e in selected}
        elif control.kind == 'BATH_FRICTION':
            if any(e.dynamics_model != 'DECLARED_UNBIASED_LANGEVIN' for e in selected):
                raise ValueError('bath control requires actual declared unbiased stochastic dynamics')
            values = {e.friction_per_picosecond for e in selected}
        else:
            if any(e.dissolved_gas_uM is None for e in selected) or not any(e.role == 'ASSOCIATION' for e in first.events):
                raise ValueError('concentration scaling requires actual sourced dissolved gas and an association event')
            values = {e.dissolved_gas_uM for e in selected}
            base = prototypes[first.ensemble_id]
            for other in selected[1:]:
                candidate = prototypes[other.ensemble_id]
                if (candidate.electronic != base.electronic or candidate.molecular != base.molecular
                        or candidate.engine != base.engine or any(getattr(candidate.path,name) != getattr(base.path,name)
                            for name in ('gas','qm_formal_charge','spin_multiplicity','electronic_approximation',
                                'oxygenation_assumption','embedding_method','complement_hamiltonian','environment_mode'))):
                    raise ValueError('gas concentration control changes its numerical or electronic model')
        if len(values) != len(selected):
            raise ValueError('physical rate control repeats a condition instead of varying its selected operand')
    columns = sum(len(e.events) for e in initial.ensembles)
    projection = selection.bootstrap_replicates*(8*len(selection.run_groups)+16*columns)
    weights = [p.weight for p in initial.paths]
    if type(selection.passages) is not FirstPassageSelection:
        weights.extend(p.weight for wave in selection.passages.continuations for p in wave.resampling.resulting_paths)
    decimal_extent = 512+sum(len(str(p.denominator)) for p in weights)
    workspace = (projection*4+selection.bootstrap_replicates*columns*decimal_extent*4
        +len(sources)*16384+sum(len(c.observation_times_seconds)*columns*8192 for c in selection.cases))
    if workspace > selection.maximum_analysis_bytes or projection > MAXIMUM_MATRIX_ARRAY_BYTES:
        raise ValueError('physical rate whole-group resampling exceeds its selected finite analysis allocation')
    return dict(clocks=clocks, prototypes=prototypes, projected_array_bytes=projection, estimated_workspace_bytes=workspace)


def _datasets(selection, paths, path_reports, clocks):
    datasets = {}
    for case in selection.cases:
        dt, steps = clocks[case.ensemble_id]
        selected = tuple(p for p in paths if p.ensemble_id == case.ensemble_id)
        groups = []
        for group in selection.run_groups:
            binding = next(b for b in group.bindings if b.ensemble_id == case.ensemble_id)
            rows = []
            for run in binding.run_ids:
                members = tuple(p for p in selected if p.run_id == run)
                if sum((p.weight.fraction for p in members),Fraction()) != 1:
                    raise ValueError('physical rate changes an original run total through descendant selection')
                for path in members:
                    row = path_reports[path.path_id]
                    valid = row['path_disposition'] in {'OBSERVED_EVENT','HORIZON_CENSORED'}
                    event = row['first_event'] if row['path_disposition'] == 'OBSERVED_EVENT' else None
                    if event is not None:
                        last = event['confirmation_step']
                        if (type(last) is not int or not 1 <= last <= steps
                                or fraction(event['confirmation_time_seconds']) != dt*last
                                or fraction(event['event_time_upper_seconds']) != dt*last):
                            raise ValueError('physical rate changes the original confirmed event clock')
                    else:
                        last = steps
                    if (row['ensemble_id'] != case.ensemble_id or row['run_id'] != run
                            or row['entry_history_id'] not in case.entry_history_ids
                            or fraction(row['selected_horizon_seconds']) != dt*steps
                            or row['path_disposition'] == 'HORIZON_CENSORED' and fraction(row['observed_time_seconds']) != dt*steps):
                        raise ValueError('physical rate changes an original path, history or censoring horizon')
                    rows.append(RateObservation(path.path_id,row['entry_history_id'],path.weight.fraction/len(binding.run_ids),
                        last,event['event_id'] if event else None,valid))
            groups.append(tuple(rows))
        datasets[case.ensemble_id] = tuple(groups)
    return datasets


def assess_controls(selection, ensembles, reports):
    indexed = {e.ensemble_id:e for e in ensembles}
    controls = {}
    for selected in selection.controls:
        values = {}
        for ensemble_id in selected.ensemble_ids:
            ensemble = indexed[ensemble_id]
            rates = reports[ensemble_id]['fit']['cause_rates_per_second']
            with localcontext() as ctx:
                ctx.prec = 80
                values[ensemble_id] = {event.event_id:(str(Decimal(rates[event.event_id])/ensemble.dissolved_gas_uM)
                    if selected.kind == 'DISSOLVED_CONCENTRATION' and event.role == 'ASSOCIATION' else rates[event.event_id])
                    if rates[event.event_id] is not None else None for event in ensemble.events}
        changes = {}
        for event in indexed[selected.ensemble_ids[0]].events:
            rows = tuple(v[event.event_id] for v in values.values())
            changes[event.event_id] = (max(math.log(float(v)) for v in rows)-min(math.log(float(v)) for v in rows)
                if all(v is not None and 0 < float(v) < math.inf for v in rows) else None)
        supported = all(reports[key]['reduction_assessment'] == 'SATISFIED' for key in selected.ensemble_ids)
        result = ('UNEVALUABLE' if not supported or any(v is None for v in changes.values()) else
            'SATISFIED' if max(changes.values()) <= float(selected.maximum_log_rate_change) else 'FALSIFIED')
        controls[selected.control_id] = dict(kind=selected.kind, status=result, ensemble_ids=selected.ensemble_ids,
            comparison_basis=selected.comparison_basis.to_document(), compared_rates=values, absolute_log_rate_range=changes,
            normalization='ASSOCIATION_RATE_DIVIDED_ONCE_BY_FREE_DISSOLVED_uM' if selected.kind == 'DISSOLVED_CONCENTRATION' else 'NONE',
            scope='OBSERVED_SELECTED_CONDITIONS_WITHOUT_ZERO_CONCENTRATION_OR_MODEL_EXTRAPOLATION')
    return controls


def read_physical_rates(*, selection, sources, assessor_source):
    capacity = validate_physical_rate_inputs(selection, sources)
    exact(assessor_source, ObjectIdentity)
    initial = initial_passages(selection.passages)
    if type(selection.passages) is FirstPassageSelection:
        original, arrays = read_first_passages(selection=selection.passages,sources=sources,assessor_source=assessor_source)
        paths = initial.paths
    else:
        campaign = read_weighted_path_campaign(selection=selection.passages,sources=sources,assessor_source=assessor_source)
        original, arrays, paths = campaign['report'],campaign['arrays'],campaign['paths']
    datasets = _datasets(selection,paths,original['path_census'],capacity['clocks'])
    cases = {}
    for case, ensemble in zip(selection.cases,initial.ensembles,strict=True):
        dt, horizon = capacity['clocks'][case.ensemble_id]
        cases[case.ensemble_id] = assess_case(case=case,ensemble=ensemble,groups=datasets[case.ensemble_id],
            dt=dt,horizon_steps=horizon,criteria=selection.criteria)
    controls = assess_controls(selection,initial.ensembles,cases)
    joint, resampling_arrays = joint_rate_resampling(selection=selection,ensembles=initial.ensembles,
        datasets=datasets,clocks=capacity['clocks'],reports=cases)
    arrays.update(resampling_arrays)
    for ensemble in initial.ensembles:
        row = cases[ensemble.ensemble_id]
        required = ['INTEGRATION_STEP']
        if ensemble.dynamics_model != 'NVE':
            required.append('BATH_FRICTION')
        if any(event.role == 'ASSOCIATION' for event in ensemble.events):
            required.append('DISSOLVED_CONCENTRATION')
        assessment = {}
        for kind in required:
            matched = tuple(c['status'] for c in controls.values() if c['kind']==kind and ensemble.ensemble_id in c['ensemble_ids'])
            assessment[kind] = status(*matched) if matched else 'UNEVALUABLE'
        if ensemble.dissolved_gas_uM is not None or 'DISSOLVED_CONCENTRATION' in required:
            assessment['CONCENTRATION_CENSUS'] = ('SATISFIED'
                if ensemble.concentration_source in {c.identity for c in selection.gas_concentrations} else 'UNEVALUABLE')
        row['concentration_census'] = next((c.to_document() for c in selection.gas_concentrations if c.identity==ensemble.concentration_source),None)
        row['required_control_assessments'] = assessment
        row['conditional_rate_assessment'] = status(row['reduction_assessment'],joint['status'],*assessment.values())
        row['physical_model_admission'] = 'UNEVALUABLE'
        row['remaining_physical_requirements'] = (
            'ENTRY_DISTRIBUTION_AND_HISTORY_REPRESENTATIVENESS','EVENT_AND_STATE_CHEMICAL_MEANING',
            'REFERENCE_OPERATOR_AND_NUMERICAL_ERROR','RUN_GROUP_INDEPENDENCE_AND_SAMPLING_COVERAGE',
            *(() if ensemble.dynamics_model=='NVE' else ('BATH_TRANSPORT_APPLICABILITY',)),
            *(() if 'DISSOLVED_CONCENTRATION' not in required else ('BULK_RESERVOIR_FINITE_SIZE_AND_DILUTE_LIMIT',)))
    recheck_original_native_outputs(sources,description='physical rate assessment')
    return dict(selection=selection.identity.to_document(),assessor_source=assessor_source.to_document(),
        original_passage_analysis=original,cases=cases,controls=controls,joint_uncertainty=joint,
        capacity={k:v for k,v in capacity.items() if k not in {'clocks','prototypes'}},
        assumptions=selection.assumptions,evidence_scope=selection.scope,
        new_native_calls=0,new_reference_evaluations=0,biological_predictive_validity='UNEVALUABLE'),arrays
