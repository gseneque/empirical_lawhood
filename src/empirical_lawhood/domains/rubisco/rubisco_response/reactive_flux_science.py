# SPDX-License-Identifier: MPL-2.0
"""Finite-slab flux-side estimates over complete, retained shooting populations.

All momentum members of a configuration remain nested observations. The same
original circular-block draws carry their complete shot statistics through
every surface and physical step. No velocity, negative flux or failed draw is
clipped, and no physical rate follows from the conditional numerical checks.
"""

from fractions import Fraction
import math

from empirical_lawhood.domains.rubisco.rubisco_response.equilibrium_reweighting_science import basin_membership, fit_ensemble, thermal_energy
from empirical_lawhood.domains.rubisco.rubisco_response.physical_rate_science import status
from empirical_lawhood.domains.rubisco.rubisco_response.transition_state_rates import BOLTZMANN_J_K, PLANCK_J_S


def _exceeds(value, limit):
    return Fraction(value) > Fraction(limit)


def reduce_flux(*, surface, ensemble, dynamics, criteria, plateau_times, coordinates, weights,
        sample_keys, geometry, observations, momentum_pairs):
    """Reduce an explicitly weighted configuration-and-momentum population.

    We approximate delta(s) by 1/(2h) on [-h,h). The correlation is
    <1_slab qdot(0) 1_{s(t)>0}>/(2h P_A), including both momentum signs.
    Its finite-slab t=0 value is zero for antithetic Maxwell momenta. A
    positive-flux normalization is computed analytically from natural masses.
    The prespecified intermediate-time plateau, width and coordinate controls
    determine whether this approximation is numerically supported.
    """
    import numpy as np
    q, w = np.asarray(coordinates, dtype='<f8'), np.asarray(weights, dtype='<f8')
    if (q.ndim != 2 or w.shape != (len(q),) or len(sample_keys) != len(q)
            or not np.isfinite(q).all() or not np.isfinite(w).all() or np.any(w < 0)
            or abs(math.fsum(w)-1) > 1e-10):
        raise ValueError('flux reduction requires the complete normalized original configuration measure')
    basins = {b.basin_id:i for i,b in enumerate(ensemble.basins)}
    membership = basin_membership(ensemble, q)
    probability_a = math.fsum(w[membership[basins[surface.reactant_basin_id]]])
    selected = tuple(i for i,value in enumerate(q[:,surface.coordinate_axis])
        if -Fraction(surface.half_width) <= Fraction(float(value))-Fraction(surface.center) < Fraction(surface.half_width))
    mass = math.fsum(w[i] for i in selected)
    weight_squares = math.fsum(w[i]**2 for i in selected)
    ess = mass**2/weight_squares if weight_squares else 0.
    findings, missing = [], []
    if len(selected) < criteria.minimum_slab_configurations:
        findings.append('SLAB_CONFIGURATION_COUNT_BELOW_SELECTION')
    if Fraction(ess) < Fraction(criteria.minimum_slab_weight_ess):
        findings.append('SLAB_WEIGHT_ESS_BELOW_SELECTION')
    if not probability_a or not mass:
        missing.append('UNOBSERVED_REACTANT_OR_DIVIDING_SLAB')
    complete, mu, signed, observed_positive, uncommitted, committor = True, [], [], [], [], []
    derivative_status, initial_correlation, arithmetic_errors = [], [], []
    for index in selected:
        key = sample_keys[index]
        g = geometry.get((surface.surface_id,*key))
        row = observations.get((surface.surface_id,dynamics.settings_id,*key))
        if g is None:
            complete = False
            missing.append('DIVIDING_GEOMETRY_UNAVAILABLE')
            continue
        derivative_status.append(g['derivative_assessment']['selected_bias_geometry_criteria'])
        mu.append((index,g['analytic_positive_speed_per_second']))
        if row is None or not row['complete']:
            complete = False
            continue
        velocities = tuple(row['initial_coordinate_velocities_per_second'])
        sides = np.asarray(row['product_side'], dtype='|b1')
        hits = tuple(row['first_stable_basin'])
        if (len(velocities) != 2*momentum_pairs or len(hits) != len(velocities)
                or sides.shape != (len(velocities),len(plateau_times)+1)
                or not all(math.isfinite(v) for v in velocities)
                or any(h not in ('REACTANT','PRODUCT',None) for h in hits)):
            raise ValueError('flux observation changes its complete finite momentum, time or commitment census')
        if any(velocities[i] != -velocities[i+1] for i in range(0,len(velocities),2)):
            raise ValueError('flux observation changes its original antithetic phase law')
        count = len(velocities)
        # fsum is independent of the vectorized summation used by the
        # projection control. Retain their discrepancy against its selection.
        values = tuple(math.fsum(v*int(side) for v,side in zip(velocities,sides[:,j],strict=True))/count
            for j in range(sides.shape[1]))
        alternate = np.asarray(velocities)@sides.astype('<f8')/count
        scale = max(g['analytic_positive_speed_per_second'],*(abs(v) for v in values))
        arithmetic_errors.append(float(np.max(abs(alternate-np.asarray(values))))/scale)
        initial_correlation.append(values[0])
        signed.append((index,values[1:]))
        observed_positive.append((index,math.fsum(max(v,0.) for v in velocities)/count))
        uncommitted.append((index,sum(h is None for h in hits)/count))
        committor.append((index,sum(h=='PRODUCT' for h in hits)/count))
    if len(mu) != len(selected):
        complete = False
    if not complete:
        missing.append('COMPLETE_SELECTED_SHOOTING_POPULATION_UNAVAILABLE')
    geometry_status = status(*derivative_status) if len(derivative_status)==len(selected) and selected else 'UNEVALUABLE'
    if geometry_status == 'FALSIFIED':
        findings.append('DIVIDING_COORDINATE_GEOMETRY_FALSIFIED')
    elif geometry_status != 'SATISFIED':
        missing.append('DIVIDING_COORDINATE_GEOMETRY_NOT_SUPPORTED')
    width = float(2*Fraction(surface.half_width))
    analytic_numerator = math.fsum(w[i]*v for i,v in mu) if len(mu)==len(selected) and mass else None
    speed = analytic_numerator/mass if analytic_numerator is not None else None
    prefactor = speed/width if speed is not None else None
    thermal = thermal_energy(ensemble.temperature_kelvin)
    barrier = -thermal*math.log(mass/probability_a) if mass and probability_a else None
    tst_rate = analytic_numerator/(width*probability_a) if analytic_numerator is not None and probability_a else None
    dimensionless_prefactor = (prefactor*float(Fraction(PLANCK_J_S)/(Fraction(BOLTZMANN_J_K)*Fraction(ensemble.temperature_kelvin)))
        if prefactor is not None else None)
    values, kappas, mean, kappa, positive_error, noncommit, rms, variation = None,None,None,None,None,None,None,None
    if complete and selected and analytic_numerator and probability_a:
        numerators = tuple(math.fsum(w[i]*v[j] for i,v in signed) for j in range(len(plateau_times)))
        values = tuple(v/(width*probability_a) for v in numerators)
        kappas = tuple(v/analytic_numerator for v in numerators)
        mean = math.fsum(values)/len(values)
        kappa = math.fsum(kappas)/len(kappas)
        positive_error = abs(math.fsum(w[i]*v for i,v in observed_positive)/analytic_numerator-1)
        noncommit = math.fsum(w[i]*v for i,v in uncommitted)/mass
        rms = math.sqrt(math.fsum(w[i]*(v-.5)**2 for i,v in committor)/mass)
        variation = (max(values)-min(values))/abs(mean) if mean else None
        if any(v != 0 for v in initial_correlation):
            findings.append('FINITE_SLAB_ZERO_TIME_ANTITHETIC_FLUX_NOT_ZERO')
        if any(v <= 0 or v > 1 for v in kappas):
            findings.append('PLATEAU_TRANSMISSION_OUTSIDE_POSITIVE_UNIT_INTERVAL')
        if variation is None or _exceeds(variation,criteria.maximum_plateau_relative_range):
            findings.append('SELECTED_INTERMEDIATE_TIMES_HAVE_NO_RESOLVED_PLATEAU')
        for value,limit,reason in (
                (positive_error,criteria.maximum_positive_flux_relative_error,'SAMPLED_POSITIVE_FLUX_DIFFERS_FROM_MAXWELL_MEASURE'),
                (noncommit,criteria.maximum_uncommitted_probability,'UNCOMMITTED_SHOOTING_PROBABILITY_EXCEEDS_SELECTION'),
                (rms,criteria.maximum_committor_rms_deviation,'DIVIDING_CONFIGURATION_COMMITTOR_SPREAD_EXCEEDS_SELECTION'),
                (max(arithmetic_errors,default=0.),criteria.maximum_arithmetic_relative_error,'INDEPENDENT_FLUX_SUMS_DISAGREE')):
            if _exceeds(value,limit):
                findings.append(reason)
    return dict(surface_id=surface.surface_id,dynamics_id=dynamics.settings_id,
        equilibrium_configurations=len(q),slab_configurations=len(selected),slab_weight_ess=ess,
        reactant_probability=probability_a,slab_probability=mass,slab_full_width=str(2*Fraction(surface.half_width)),
        coordinate_unit=ensemble.coordinate_convention.center_units[surface.coordinate_axis],
        finite_slab_barrier_kj_mol=barrier,analytic_positive_coordinate_speed_per_second=speed,
        positive_flux_prefactor_per_second=prefactor,eyring_dimensionless_prefactor=dimensionless_prefactor,
        transition_state_rate_per_second=tst_rate,plateau_times_seconds=tuple(str(t) for t in plateau_times),
        flux_side_rates_per_second=values,transmission_curve=kappas,plateau_rate_per_second=mean,
        plateau_transmission_coefficient=kappa,plateau_relative_range=variation,
        positive_flux_relative_error=positive_error,uncommitted_probability=noncommit,committor_rms_deviation=rms,
        maximum_arithmetic_relative_error=max(arithmetic_errors,default=None),
        complete_selected_shooting_population=complete,geometry_assessment=geometry_status,
        selected_flux_criteria='FALSIFIED' if findings else 'UNEVALUABLE' if missing else 'SATISFIED',
        findings=tuple(sorted(set(findings))),missing=tuple(sorted(set(missing))),
        finite_slab_zero_time_convention='ANTITHETIC_SIGNED_CORRELATION_ZERO_NOT_TRANSMISSION_ONE',
        physical_rate_admission='UNEVALUABLE')


def flux_vector(rule, estimates, equilibrium_contrasts):
    columns, values = [], []
    for surface in rule.surfaces:
        for dynamics in rule.dynamics:
            row = estimates[(surface.surface_id,dynamics.settings_id)]
            for field,log in (('finite_slab_barrier_kj_mol',False),('positive_flux_prefactor_per_second',True),
                    ('plateau_transmission_coefficient',True),('plateau_rate_per_second',True)):
                columns.append(dict(surface_id=surface.surface_id,dynamics_id=dynamics.settings_id,
                    quantity=('log_' if log else '')+field))
                value = row[field]
                values.append(math.log(value) if log and value is not None and value > 0 else None if log else value)
    for contrast,value in zip(rule.equilibrium.contrasts,equilibrium_contrasts,strict=True):
        columns.append(dict(contrast_id=contrast.contrast_id,quantity='free_energy_contrast_kj_mol'))
        values.append(value)
    return tuple(columns),tuple(values)


def assess_flux_controls(rule, estimates):
    controls = {}
    for control in rule.controls:
        rows = tuple(estimates[(s,rule.primary_dynamics_id)] for s in control.surface_ids)
        rates = tuple(r['plateau_rate_per_second'] for r in rows)
        change = max(math.log(v) for v in rates)-min(math.log(v) for v in rates) if all(v is not None and v>0 for v in rates) else None
        result = ('UNEVALUABLE' if change is None else
            'FALSIFIED' if _exceeds(change,control.maximum_log_rate_change) else status(*(r['selected_flux_criteria'] for r in rows)))
        controls[control.control_id] = dict(kind=control.kind,surface_ids=control.surface_ids,
            correspondence=control.correspondence.to_document(),absolute_log_rate_range=change,status=result)
    step = {}
    for surface in rule.surfaces:
        rows = tuple(estimates[(surface.surface_id,d.settings_id)] for d in rule.dynamics)
        rates = tuple(r['plateau_rate_per_second'] for r in rows)
        change = max(math.log(v) for v in rates)-min(math.log(v) for v in rates) if all(v is not None and v>0 for v in rates) else None
        result = ('UNEVALUABLE' if change is None else
            'FALSIFIED' if _exceeds(change,rule.criteria.maximum_step_log_rate_change) else status(*(r['selected_flux_criteria'] for r in rows)))
        step[surface.surface_id] = dict(absolute_log_rate_range=change,status=result)
    return controls,step


def joint_flux_resampling(*, rule, prepared, observations, point):
    """Refit all windows on the existing paired block indices, with all shots.

    A block carries each original configuration's entire antithetic population.
    There is no IID resampling of sites, signs or descendant trajectories.
    This is a conditional empirical block estimate, not guaranteed coverage
    of unresolved equilibrium modes or unseen momentum-tail behaviour.
    """
    import numpy as np
    selection = rule.equilibrium
    original = prepared['equilibrium_report']['statistics']
    bootstrap = original['bootstrap']
    projected = prepared['equilibrium_arrays']
    raw = {}
    for ensemble in selection.ensembles:
        traces = tuple(t for t in selection.traces if t.ensemble_id==ensemble.ensemble_id)
        counts = tuple(len(projected[t.trace_id+'.coordinates']) for t in traces)
        q = np.concatenate([projected[t.trace_id+'.coordinates'] for t in traces])
        biases = np.concatenate([projected[t.trace_id+'.all_window_bias_potentials_kj_mol'] for t in traces],axis=1)
        keys = tuple((t.trace_id,i+1) for t,n in zip(traces,counts,strict=True) for i in range(n))
        raw[ensemble.ensemble_id] = (ensemble,traces,counts,q,biases,keys)
    columns,point_values = flux_vector(rule,point,original['contrasts_kj_mol'])
    replicates,failed = [], []
    original_failed = {r['replicate']:r for r in bootstrap['failed_replicates']}
    for replicate in range(bootstrap['requested_replicates']):
        sampled,issues = {}, []
        if replicate in original_failed:
            issues.append(('original-equilibrium','ORIGINAL_JOINT_REPLICATE_UNAVAILABLE'))
        for ensemble,traces,counts,q,biases,keys in raw.values():
            indices,offset = [],0
            for trace,count in zip(traces,counts,strict=True):
                starts = bootstrap['block_starts'][trace.resampling_group_id][replicate]
                if starts is None or count==0:
                    indices = None
                    break
                selected = ((np.asarray(starts,dtype='<i8')[:,None]+np.arange(trace.block_samples)) % count).ravel()[:count]
                indices.extend((selected+offset).tolist())
                offset += count
            if indices is None:
                issues.append((ensemble.ensemble_id,'ORIGINAL_BLOCK_DRAW_UNAVAILABLE'))
                continue
            indices = np.asarray(indices,dtype='<i8')
            fitted,arrays = fit_ensemble(ensemble=ensemble,biases_kj_mol=biases[:,indices],
                coordinates=q[indices],counts=counts,criteria=selection.criteria)
            if not fitted['available'] or not fitted.get('overlap_connected'):
                issues.append((ensemble.ensemble_id,'RESAMPLED_MBAR_NOT_SUPPORTED'))
                continue
            for surface in rule.surfaces:
                if surface.ensemble_id != ensemble.ensemble_id:
                    continue
                for dynamics in rule.dynamics:
                    sampled[(surface.surface_id,dynamics.settings_id)] = reduce_flux(surface=surface,ensemble=ensemble,
                        dynamics=dynamics,criteria=rule.criteria,plateau_times=rule.plateau_times_seconds,
                        coordinates=q[indices],weights=arrays['target_weights'],sample_keys=tuple(keys[i] for i in indices),
                        geometry=prepared['geometry'],observations=observations,momentum_pairs=rule.momentum_pairs_per_configuration)
        if len(sampled)==len(point):
            _,values = flux_vector(rule,sampled,bootstrap['joint_contrasts_kj_mol'][replicate])
        else:
            values = (None,)*len(columns)
        if any(v is None or not math.isfinite(v) for v in values):
            issues.append(('joint-flux','INCOMPLETE_OR_NONPOSITIVE_JOINT_FLUX_VECTOR'))
        replicates.append(values)
        if issues:
            failed.append(dict(replicate=replicate,findings=tuple(issues),values=values))
    rank = math.ceil(Fraction(selection.criteria.simultaneous_coverage)*(len(replicates)+1))
    covariance,intervals = None,None
    available = not failed and all(v is not None and math.isfinite(v) for v in point_values) and rank<=len(replicates)
    if available:
        draws = np.asarray(replicates,dtype='<f8')
        covariance = np.atleast_2d(np.cov(draws,rowvar=False,ddof=1)).tolist()
        # Columns have different units. Use marginal empirical SD scales for
        # a simultaneous maximum; deterministic columns keep exact zero width.
        scale = np.std(draws,axis=0,ddof=1)
        deviation = abs(draws-np.asarray(point_values))
        unresolved = (scale==0)&np.any(deviation!=0,axis=0)
        if np.any(unresolved):
            available = False
            covariance = None
        else:
            normalized = deviation/np.where(scale>0,scale,1)
            quantile = float(np.sort(np.max(normalized,axis=1))[rank-1])
            intervals = tuple((v-quantile*s,v+quantile*s) for v,s in zip(point_values,scale,strict=True))
    return dict(status='SATISFIED' if available else 'UNEVALUABLE',columns=columns,point_values=point_values,
        joint_values=tuple(replicates),requested_replicates=bootstrap['requested_replicates'],retained_replicates=len(replicates),
        failed_replicates=tuple(failed),covariance=covariance,simultaneous_intervals=intervals,
        simultaneous_coverage=bootstrap['simultaneous_coverage'],simultaneous_quantile_rank=rank,
        resampling_source='ORIGINAL_EQUILIBRIUM_COUPLED_CIRCULAR_BLOCK_STARTS',
        nested_unit='ONE_CONFIGURATION_WITH_ALL_ORIGINAL_MOMENTUM_PAIRS_AND_PHYSICAL_STEPS',
        interpretation='CONDITIONAL_EMPIRICAL_BLOCK_VARIATION_NOT_GUARANTEED_COVERAGE'),{
            'reactive-flux.joint_values':np.asarray([[0. if v is None else v for v in row] for row in replicates],dtype='<f8'),
            'reactive-flux.joint_available':np.asarray([[v is not None for v in row] for row in replicates],dtype='|b1')}
