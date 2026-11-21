# SPDX-License-Identifier: MPL-2.0
"""Reconstruct finite-slab flux from original equilibrium and unbiased shots."""

from dataclasses import dataclass
from fractions import Fraction
import math

from empirical_lawhood.domains.matrix.input_contracts import MAXIMUM_MATRIX_ARRAY_BYTES
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.equilibrium_reweighting_read import RetainedEquilibriumTrace
from empirical_lawhood.domains.rubisco.rubisco_response.equilibrium_reweighting_science import basin_membership
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_bias_assessment import independent_reference_bias_coordinates
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_trajectory_operation import ReferenceTrajectoryResult, capability_for
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_trajectory_read import read_reference_trajectory
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_trajectory_selection import read_phase_space
from empirical_lawhood.domains.rubisco.rubisco_response.physical_rate_science import status
from empirical_lawhood.domains.rubisco.rubisco_response.reactive_flux_preparation import prepare_reactive_flux, validate_reactive_flux_preparation, signed_coordinate
from empirical_lawhood.domains.rubisco.rubisco_response.reactive_flux_records import ReactiveFluxRule
from empirical_lawhood.domains.rubisco.rubisco_response.reactive_flux_science import reduce_flux, assess_flux_controls, joint_flux_resampling
from empirical_lawhood.domains.rubisco.rubisco_response.retained_native_outputs import recheck_original_native_outputs


@dataclass(frozen=True, slots=True)
class RetainedReactiveFluxShot:
    """One prepared shot, including an explicit unlaunched or absent result.

    A missing result supplies no claim about whether native entry occurred.
    The original native-subwork reader retains receipt and cost authority.
    """
    shot_id: str
    config: object | None = None
    representation: object | None = None
    phase_bytes: bytes | None = None
    original_result: ReferenceTrajectoryResult | None = None
    native_subwork: object | None = None


def validate_reactive_flux_inputs(selection, sources):
    exact(selection,ReactiveFluxRule)
    n = len(selection.equilibrium.traces)
    if (type(sources) is not tuple or len(sources)<n
            or any(type(s) is not RetainedEquilibriumTrace for s in sources[:n])
            or any(type(s) is not RetainedReactiveFluxShot for s in sources[n:])):
        raise TypeError('flux inputs require all original equilibrium traces followed by all prepared shot carriers')
    capacity = validate_reactive_flux_preparation(selection,sources[:n])
    shots = sources[n:]
    ids = tuple(s.shot_id for s in shots)
    if ids != tuple(sorted(set(ids))):
        raise ValueError('flux carriers repeat or reorder a prepared shot')
    for source in shots:
        validate_stable_id(source.shot_id)
        if source.config is None:
            if any(v is not None for v in (source.representation,source.phase_bytes,source.original_result,source.native_subwork)):
                raise ValueError('an unlaunched flux carrier cannot substitute detached original operands')
            continue
        capability_for(source.config)
        read_phase_space(source.config.selection,source.representation,source.phase_bytes)
        if source.original_result is not None:
            exact(source.original_result,ReferenceTrajectoryResult)
    # Bound the worst complete population before any original-result read.
    # The estimate includes every original sample, both signs, all physical
    # steps, metadata and joint draws, even when no carrier has been supplied.
    ensembles = {e.ensemble_id:e for e in selection.equilibrium.ensembles}
    projected,workspace,maximum_shots = 0,0,0
    for trace,source in zip(selection.equilibrium.traces,sources[:n],strict=True):
        samples = source.config.selection.settings.expected_samples
        dimension = len(ensembles[trace.ensemble_id].coordinate_window.cv_kinds)
        count = samples*2*selection.momentum_pairs_per_configuration
        maximum_shots += count*len(selection.dynamics)
        for dynamics in selection.dynamics:
            projected += count*(dynamics.steps+1)*dimension*8
            workspace += count*(16384+(dynamics.steps+1)*dimension*64
                +len(selection.surfaces)*(len(selection.plateau_times_seconds)+1)*128)
    columns = len(selection.surfaces)*len(selection.dynamics)*4+len(selection.equilibrium.contrasts)
    projected += selection.equilibrium.criteria.bootstrap_replicates*columns*9
    workspace += selection.equilibrium.criteria.bootstrap_replicates*columns*1024
    projected += capacity['equilibrium']['projected_array_bytes']
    workspace += capacity['worst_case_preparation_bytes']+capacity['equilibrium']['estimated_workspace_bytes']
    members = 6*n+5*len(ensembles)+3
    if (workspace > selection.maximum_analysis_bytes or projected > MAXIMUM_MATRIX_ARRAY_BYTES or members>256
            or len(shots)>maximum_shots):
        raise ValueError('complete flux trajectory and uncertainty census exceeds its selected bounded analysis allocation')
    return dict(preparation=capacity,estimated_workspace_bytes=workspace,projected_array_bytes=projected,
        maximum_assigned_shots=maximum_shots,selected_workspace_bytes=selection.maximum_analysis_bytes)


def _read_shot(shot, source, prepared, ensemble, surfaces, rule, assessor_source):
    import numpy as np
    seed = shot.phase_source
    original = prepared['selected_frames'][(seed.trace_id,seed.sample_ordinal)]['source']
    projection,observed = [],{}
    for surface in surfaces:
        observed[surface.surface_id] = dict(initial_coordinate_velocity_per_second=None,
            product_side=[],first_stable_basin=None,first_stable_step=None)
    selected_steps = (0,*(int(Fraction(t)/Fraction(shot.selection.settings.step_seconds)) for t in rule.plateau_times_seconds))
    representation = original.representation
    cell = np.diag([float(v) for v in original.config.original.selection.cell.lengths_angstrom])
    args = dict(window=ensemble.coordinate_window,convention=ensemble.coordinate_convention,
        physical_model_id=representation.representation_id,physical_atom_ids=tuple(a.atom_id for a in representation.atoms),
        cell_vectors_angstrom=cell)
    basins = {b.basin_id:i for i,b in enumerate(ensemble.basins)}

    def consume(frame):
        if frame['step'] != len(projection):
            raise ValueError('flux shot changes its complete original physical clock')
        q = independent_reference_bias_coordinates(**args,coordinates_angstrom=frame['coordinates_angstrom'])
        projection.append(tuple(q))
        membership = basin_membership(ensemble,np.asarray([q]))[:,0]
        for surface in surfaces:
            row = observed[surface.surface_id]
            if frame['step']==0:
                g = prepared['geometry'][(surface.surface_id,seed.trace_id,seed.sample_ordinal)]
                row['initial_coordinate_velocity_per_second'] = float(np.sum(
                    g['derivatives']*frame['velocities_nm_per_ps'][list(g['atom_rows'])]))*1e13
                if tuple(q) != prepared['selected_frames'][(seed.trace_id,seed.sample_ordinal)]['coordinates']:
                    raise ValueError('flux shot changes its original equilibrium coordinate projection')
            if frame['step'] in selected_steps:
                row['product_side'].append(signed_coordinate(surface,q)>0)
            if row['first_stable_basin'] is None:
                if membership[basins[surface.reactant_basin_id]]:
                    row['first_stable_basin'] = 'REACTANT'
                elif membership[basins[surface.product_basin_id]]:
                    row['first_stable_basin'] = 'PRODUCT'
                if row['first_stable_basin'] is not None:
                    row['first_stable_step'] = frame['step']

    report,reasons = None,[]
    if source.config is not None:
        if (source.config.selection != shot.selection or source.config.original.selection != original.config.original.selection
                or source.representation != representation or source.phase_bytes != prepared['phase_bytes'][shot.shot_id]):
            raise ValueError('flux shot substitutes its exact prepared phase, original reference operator or physical clock')
    if source.original_result is None:
        reasons.append('ORIGINAL_SHOT_RESULT_NOT_SUPPLIED')
    else:
        report = read_reference_trajectory(config=source.config,representation=source.representation,
            phase_bytes=source.phase_bytes,original_result=source.original_result,native_subwork=source.native_subwork,
            assessor_source=assessor_source,frame_consumer=consume)
        if report['native_error'] is not None:
            reasons.append('ORIGINAL_SHOT_NATIVE_FAILURE')
        if report['assessment_error'] is not None or report['assessment'] is None:
            reasons.append('ORIGINAL_SHOT_MECHANICS_UNAVAILABLE')
        elif report['assessment']['selected_trace_criteria'] != 'SATISFIED':
            reasons.append('ORIGINAL_SHOT_MECHANICS_'+report['assessment']['selected_trace_criteria'])
        if report['gpu_assessment_error'] is not None:
            reasons.append('ORIGINAL_SHOT_GPU_OBSERVATIONS_UNAVAILABLE')
    if len(projection) != shot.selection.settings.steps+1:
        reasons.append('COMPLETE_SHOT_HORIZON_UNAVAILABLE')
    if any(len(r['product_side'])!=len(selected_steps) or r['initial_coordinate_velocity_per_second'] is None
            or not math.isfinite(r['initial_coordinate_velocity_per_second']) for r in observed.values()):
        reasons.append('COMPLETE_SHOT_FLUX_PROJECTION_UNAVAILABLE')
    numerical_status = 'FALSIFIED' if report and report['assessment'] and report['assessment']['selected_trace_criteria']=='FALSIFIED' else (
        'SATISFIED' if not reasons else 'UNEVALUABLE')
    return dict(prepared_shot=shot.to_document(),trajectory_assessment=numerical_status,disposition='ORIGINAL_FAILED' if report and report['native_error'] else
        'ORIGINAL_RETURNED' if report else 'NOT_SUPPLIED',eligible_for_complete_flux=not reasons,reasons=tuple(reasons),
        original_trace=report,original_completion=source.original_result.completion.to_document() if source.original_result else None,
        retained_projected_frames=len(projection),coordinate_dimension=len(ensemble.coordinate_window.cv_kinds),
        surfaces=observed),np.asarray(projection,dtype='<f8').reshape((-1,len(ensemble.coordinate_window.cv_kinds)))


def _unavailable(surface,dynamics,reason):
    return dict(surface_id=surface.surface_id,dynamics_id=dynamics.settings_id,
        finite_slab_barrier_kj_mol=None,positive_flux_prefactor_per_second=None,
        plateau_transmission_coefficient=None,plateau_rate_per_second=None,
        selected_flux_criteria='UNEVALUABLE',missing=(reason,),findings=(),physical_rate_admission='UNEVALUABLE')


def read_reactive_flux(*, selection, sources, assessor_source):
    import numpy as np
    capacity = validate_reactive_flux_inputs(selection,sources)
    exact(assessor_source,ObjectIdentity)
    n = len(selection.equilibrium.traces)
    prepared = prepare_reactive_flux(rule=selection,sources=sources[:n],assessor_source=assessor_source)
    expected = prepared['prepared'].shots
    if tuple(s.shot_id for s in sources[n:]) != tuple(s.shot_id for s in expected):
        raise ValueError('flux source carriers omit, add or reorder an actual derived shot; retain explicit absent-result carriers')
    ensembles = {e.ensemble_id:e for e in selection.equilibrium.ensembles}
    trace_ensembles = {t.trace_id:t.ensemble_id for t in selection.equilibrium.traces}
    surfaces = {s.surface_id:s for s in selection.surfaces}
    census,blocks,offset,observation_members = {},[],0,{}
    for shot,source in zip(expected,sources[n:],strict=True):
        seed = shot.phase_source
        ensemble = ensembles[trace_ensembles[seed.trace_id]]
        row,projection = _read_shot(shot,source,prepared,ensemble,tuple(surfaces[s] for s in shot.surface_ids),selection,assessor_source)
        row['coordinate_array_offset'] = offset
        offset += projection.size
        blocks.append(projection.ravel())
        census[shot.shot_id] = row
        for surface_id in shot.surface_ids:
            key = (surface_id,shot.selection.settings.settings_id,seed.trace_id,seed.sample_ordinal)
            observation_members.setdefault(key,[]).append((seed.momentum_pair,seed.momentum_sign,row,row['surfaces'][surface_id]))
    observations = {}
    for key,members in observation_members.items():
        members.sort(key=lambda row:(row[0],row[1]))
        if tuple((p,s) for p,s,_,_ in members) != tuple((p,s) for p in range(selection.momentum_pairs_per_configuration) for s in (-1,1)):
            raise ValueError('flux reduction loses the original complete antithetic phase census')
        observations[key] = dict(complete=all(row['eligible_for_complete_flux'] for _,_,row,_ in members),
            initial_coordinate_velocities_per_second=tuple(v['initial_coordinate_velocity_per_second'] for _,_,_,v in members),
            product_side=tuple(v['product_side'] for _,_,_,v in members),
            first_stable_basin=tuple(v['first_stable_basin'] for _,_,_,v in members))
    arrays = prepared['equilibrium_arrays']
    arrays['reactive-flux.projected_coordinates'] = np.concatenate(blocks) if blocks else np.empty(0,dtype='<f8')
    estimates = {}
    statistics = prepared['equilibrium_report']['statistics']
    for ensemble in selection.equilibrium.ensembles:
        traces = tuple(t for t in selection.equilibrium.traces if t.ensemble_id==ensemble.ensemble_id)
        q = np.concatenate([arrays[t.trace_id+'.coordinates'] for t in traces])
        keys = tuple((t.trace_id,i+1) for t in traces for i in range(len(arrays[t.trace_id+'.coordinates'])))
        for surface in selection.surfaces:
            if surface.ensemble_id != ensemble.ensemble_id:
                continue
            for dynamics in selection.dynamics:
                key = (surface.surface_id,dynamics.settings_id)
                if not prepared['prepared'].complete_equilibrium_census or not statistics['ensembles'][ensemble.ensemble_id]['available']:
                    estimates[key] = _unavailable(surface,dynamics,'COMPLETE_ORIGINAL_EQUILIBRIUM_MEASURE_UNAVAILABLE')
                else:
                    estimates[key] = reduce_flux(surface=surface,ensemble=ensemble,dynamics=dynamics,criteria=selection.criteria,
                        plateau_times=selection.plateau_times_seconds,coordinates=q,weights=arrays[ensemble.ensemble_id+'.target_weights'],
                        sample_keys=keys,geometry=prepared['geometry'],observations=observations,momentum_pairs=selection.momentum_pairs_per_configuration)
    controls,step = assess_flux_controls(selection,estimates)
    joint,resampling_arrays = joint_flux_resampling(rule=selection,prepared=prepared,observations=observations,point=estimates)
    arrays.update(resampling_arrays)
    cases = {}
    for surface in selection.surfaces:
        required = {}
        for kind in ('SLAB_WIDTH','ALTERNATIVE_COORDINATE'):
            rows = tuple(c['status'] for c in controls.values() if c['kind']==kind and surface.surface_id in c['surface_ids'])
            required[kind] = status(*rows) if rows else 'UNEVALUABLE'
        rows = {d.settings_id:estimates[(surface.surface_id,d.settings_id)] for d in selection.dynamics}
        selected_shot_status = tuple(r['trajectory_assessment'] for r in census.values() if surface.surface_id in r['surfaces'])
        shot_status = status(*selected_shot_status) if selected_shot_status else 'UNEVALUABLE'
        cases[surface.surface_id] = dict(dynamics=rows,step_control=step[surface.surface_id],required_controls=required,
            original_shooting_assessment=shot_status,
            conditional_flux_assessment=status(statistics['selected_numerical_sampling_criteria'],joint['status'],
                shot_status,step[surface.surface_id]['status'],*required.values(),*(r['selected_flux_criteria'] for r in rows.values())),
            physical_rate_admission='UNEVALUABLE',remaining_physical_requirements=(
                'EQUILIBRIUM_ENSEMBLE_AND_UNSEEN_SLOW_MODES','REFERENCE_FORCE_AND_CHEMICAL_MODEL_ACCURACY',
                'STABLE_STATE_AND_REACTION_COORDINATE_MEANING','CLASSICAL_UNCONSTRAINED_NUCLEAR_DYNAMICS',
                'FINITE_SLAB_LIMIT_AND_KINETIC_TIME_SCALE_SEPARATION','MOMENTUM_TAIL_AND_CONFIGURATION_SAMPLING_COVERAGE'))
    for value in arrays.values():
        value.setflags(write=False)
    recheck_original_native_outputs(sources,description='reactive-flux analysis')
    geometry_census = tuple(dict(surface_id=key[0],trace_id=key[1],sample_ordinal=key[2],
        **{name:value for name,value in row.items() if name not in {'derivatives','atom_rows'}},
        atom_rows=tuple(int(i) for i in row['atom_rows']),cartesian_derivatives=row['derivatives'].tolist())
        for key,row in sorted(prepared['geometry'].items()))
    return dict(selection=selection.identity.to_document(),assessor_source=assessor_source.to_document(),
        preparation=prepared['prepared'].to_document(),original_equilibrium_analysis=prepared['equilibrium_report'],
        assigned_shots=len(expected),supplied_results=sum(s.original_result is not None for s in sources[n:]),
        complete_shots=sum(r['eligible_for_complete_flux'] for r in census.values()),shot_census=census,
        dividing_configuration_census=geometry_census,
        cases=cases,controls=controls,joint_uncertainty=joint,capacity=capacity,
        original_cost_scope='EACH_ORIGINAL_COMPLETION_ONCE_IN_THE_SOURCE_CENSUS_NO_COST_REPLAY',
        assumptions=selection.assumptions,evidence_scope=selection.scope,physical_rate_admission='UNEVALUABLE',
        new_native_calls=0,new_reference_evaluations=0),arrays
