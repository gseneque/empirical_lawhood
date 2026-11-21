# SPDX-License-Identifier: MPL-2.0
"""Conditional classical golden-rule reductions with complete gap measures.

The finite energy slab approximates delta(E_acceptor-E_donor). Neither a
converged determinant nor a single spin component supplies a complete physical
spin-transfer rate. Bandwidth, support, weak-coupling and memory checks remain
separate from chemical and ensemble validity.
"""

from fractions import Fraction
import math

from empirical_lawhood.domains.rubisco.rubisco_response.equilibrium_reweighting_science import statistical_inefficiency, fit_ensemble
from empirical_lawhood.domains.rubisco.rubisco_response.transition_state_rates import AVOGADRO_MOL, PLANCK_J_S


def hbar_native_hartree_seconds(hartree_kj_mol):
    if not math.isfinite(hartree_kj_mol) or hartree_kj_mol <= 0:
        raise ValueError('electronic rates require the original positive molecular energy conversion')
    return float(Fraction(PLANCK_J_S)*Fraction(AVOGADRO_MOL)/Fraction(hartree_kj_mol)/1000)/(2*math.pi)


def reduce_electronic_pair(*, pair, weights, gaps, coupling_squared, gap_speeds,
        point_supported, trace_counts, sample_intervals_seconds, hartree_kj_mol,
        unbiased_gap_dynamics=False):
    """Keep every assigned configuration, including unavailable vertical points."""
    import numpy as np
    from empirical_lawhood.methods.electronic_structure.surface_crossing import landau_zener_probability
    w, gaps, h2, speed = (np.asarray(v, dtype='<f8') for v in (weights,gaps,coupling_squared,gap_speeds))
    supported = np.asarray(point_supported, dtype='|b1')
    if (w.ndim != 1 or any(v.shape != w.shape for v in (gaps,h2,speed,supported))
            or sum(trace_counts) != len(w) or len(sample_intervals_seconds) != len(trace_counts)
            or not np.isfinite(w).all() or np.any(w < 0) or abs(math.fsum(w)-1) > 1e-10
            or any(n <= 0 for n in trace_counts)
            or any(not math.isfinite(t) or t <= 0 for t in sample_intervals_seconds)):
        raise ValueError('electronic reduction changes its complete weighted population or original physical clocks')
    if type(unbiased_gap_dynamics) is not bool:
        raise TypeError('electronic memory assessment requires an explicit original dynamics interpretation')
    hbar = hbar_native_hartree_seconds(hartree_kj_mol)
    complete = bool(supported.all() and np.isfinite(gaps).all() and np.isfinite(h2).all()
        and np.isfinite(speed).all() and np.all(h2 >= 0))
    rows, findings, missing = [], [], []
    if not complete:
        missing.append('COMPLETE_SUPPORTED_ELECTRONIC_POINT_POPULATION_UNAVAILABLE')
    memory, offset = [], 0
    for count, interval in zip(trace_counts,sample_intervals_seconds,strict=True):
        values = gaps[offset:offset+count]
        measured = statistical_inefficiency(values) if complete else dict(resolved=False,reason='INCOMPLETE_ORIGINAL_POINTS')
        memory.append(dict(original_samples=count, sample_interval_seconds=interval, correlation=measured,
            correlation_time_seconds=(.5*interval*measured['inefficiency']) if measured['resolved'] else None))
        offset += count
    correlation_time = max((m['correlation_time_seconds'] for m in memory),default=None) if all(
        m['correlation_time_seconds'] is not None for m in memory) else None
    if correlation_time is None:
        missing.append('ORIGINAL_ENERGY_GAP_CORRELATION_TIME_UNRESOLVED')
    if not unbiased_gap_dynamics:
        missing.append('BIASED_SAMPLING_TIME_CANNOT_SUPPLY_PHYSICAL_GAP_MEMORY')
    for width in pair.gap_half_widths_hartree:
        selected = np.isfinite(gaps) & (gaps >= -float(width)) & (gaps < float(width))
        mass = math.fsum(w[selected])
        squares = math.fsum(w[selected]**2)
        ess = mass*mass/squares if squares else 0.
        issues = []
        if int(selected.sum()) < pair.minimum_crossing_configurations:
            issues.append('CROSSING_CONFIGURATION_COUNT_BELOW_SELECTION')
        if Fraction(ess) < Fraction(pair.minimum_crossing_weight_ess):
            issues.append('CROSSING_WEIGHT_ESS_BELOW_SELECTION')
        rate, maximum_probability, product = None, None, None
        if complete and mass:
            rate = (2*math.pi/hbar)*math.fsum(w[selected]*h2[selected])/(2*float(width))
            probabilities = []
            for coupling, derivative in zip(h2[selected],speed[selected],strict=True):
                gamma = coupling/(hbar*abs(derivative)) if derivative else math.inf if coupling else 0.
                probabilities.append(landau_zener_probability(gamma))
            maximum_probability = max(probabilities)
            if Fraction(maximum_probability) > Fraction(pair.maximum_landau_zener_probability):
                issues.append('GOLDEN_RULE_WEAK_TRANSITION_CRITERION_FALSIFIED')
            if correlation_time is not None and unbiased_gap_dynamics:
                product = rate*correlation_time
                if Fraction(product) > Fraction(pair.maximum_rate_memory_product):
                    issues.append('GOLDEN_RULE_MEMORY_SEPARATION_FALSIFIED')
        if not mass:
            missing.append('UNOBSERVED_ENERGY_GAP_CROSSING_SLAB')
        rows.append(dict(half_width_hartree=str(width), configurations=int(selected.sum()),
            crossing_probability=mass, crossing_weight_ess=ess, finite_slab_rate_per_second=rate,
            maximum_landau_zener_probability=maximum_probability, rate_memory_product=product,
            findings=tuple(issues)))
        findings.extend(issues)
    rates = [r['finite_slab_rate_per_second'] for r in rows]
    variation = max(math.log(r) for r in rates)-min(math.log(r) for r in rates) if all(
        r is not None and r > 0 for r in rates) else None
    if variation is None:
        missing.append('POSITIVE_COMPLETE_BANDWIDTH_RATES_UNAVAILABLE')
    elif Fraction(variation) > Fraction(pair.maximum_bandwidth_log_rate_range):
        findings.append('ENERGY_DELTA_BANDWIDTH_CONTROL_FALSIFIED')
    primary = rows[pair.gap_half_widths_hartree.index(pair.primary_gap_half_width_hartree)]
    return dict(pair_id=pair.pair_id, assigned_configurations=len(w), supported_configurations=int(supported.sum()),
        complete_population=complete, bandwidths=tuple(rows), original_gap_correlations=tuple(memory),
        maximum_gap_correlation_time_seconds=correlation_time, absolute_bandwidth_log_rate_range=variation,
        gap_memory_scope='DECLARED_UNBIASED_LANGEVIN_NUCLEAR_BATH' if unbiased_gap_dynamics else 'SAMPLING_CORRELATION_ONLY',
        primary_rate_per_second=primary['finite_slab_rate_per_second'],
        hbar_native_hartree_seconds=hbar, original_hartree_kj_mol=hartree_kj_mol,
        selected_golden_rule_criteria='FALSIFIED' if findings else 'UNEVALUABLE' if missing else 'SATISFIED',
        findings=tuple(sorted(set(findings))), missing=tuple(sorted(set(missing))),
        spin_channel_scope=pair.coupling, physical_spin_admission='UNEVALUABLE', physical_rate_admission='UNEVALUABLE')


def joint_electronic_analysis(*, rule, equilibrium, projected, points, point_estimates, energy_conversions):
    """Replay original coupled block indices through MBAR and all pair rates.

    Each configuration retains all original state observations together. An
    unavailable original point invalidates the whole joint draw; resampling
    cannot turn a failed population into a successful subset.
    """
    import numpy as np
    selection = rule.equilibrium
    statistics = equilibrium['statistics']
    bootstrap = statistics['bootstrap']
    columns = tuple('free-energy.'+c.contrast_id+'.kj-mol' for c in selection.contrasts)+tuple(
        'log-rate.'+p.pair_id+'.per-second' for p in rule.pairs)
    def log_rate(value):
        return math.log(value) if value is not None and math.isfinite(value) and value > 0 else None
    point_values = tuple(statistics['contrasts_kj_mol'])+tuple(
        log_rate(point_estimates[p.pair_id]['primary_rate_per_second']) for p in rule.pairs)
    raw = {}
    for ensemble in selection.ensembles:
        traces = tuple(t for t in selection.traces if t.ensemble_id == ensemble.ensemble_id)
        counts = tuple(len(projected[t.trace_id+'.coordinates']) for t in traces)
        q = np.concatenate([projected[t.trace_id+'.coordinates'] for t in traces])
        biases = np.concatenate([projected[t.trace_id+'.all_window_bias_potentials_kj_mol'] for t in traces],axis=1)
        raw[ensemble.ensemble_id] = (ensemble,traces,counts,q,biases)
    failed_original = {r['replicate'] for r in bootstrap['failed_replicates']}
    draws,failed = [],[]
    for replicate in range(bootstrap['requested_replicates']):
        issues,rates = [],{}
        if replicate in failed_original:
            issues.append(('equilibrium','ORIGINAL_JOINT_REPLICATE_UNAVAILABLE'))
        for ensemble,traces,counts,q,biases in raw.values():
            indices,offset = [],0
            for trace,count in zip(traces,counts,strict=True):
                starts = bootstrap['block_starts'][trace.resampling_group_id][replicate]
                if starts is None or count == 0:
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
            w = arrays['target_weights']
            for pair in rule.pairs:
                if pair.ensemble_id != ensemble.ensemble_id:
                    continue
                data,supported = points[pair.pair_id]
                if len(data) != len(q) or not supported.all() or not np.isfinite(data).all():
                    issues.append((pair.pair_id,'COMPLETE_ORIGINAL_ELECTRONIC_POPULATION_UNAVAILABLE'))
                    continue
                slab = abs(data[indices,2]) < float(pair.primary_gap_half_width_hartree)
                # Match the half-open original interval at its negative edge.
                slab |= data[indices,2] == -float(pair.primary_gap_half_width_hartree)
                hbar = hbar_native_hartree_seconds(energy_conversions[pair.ensemble_id])
                rate = (2*math.pi/hbar)*math.fsum(w[slab]*data[indices,6][slab])/(2*float(pair.primary_gap_half_width_hartree))
                rates[pair.pair_id] = log_rate(rate)
        values = tuple(bootstrap['joint_contrasts_kj_mol'][replicate])+tuple(rates.get(p.pair_id) for p in rule.pairs)
        draws.append(values)
        if any(v is None or not math.isfinite(v) for v in values):
            issues.append(('joint-electronic','INCOMPLETE_JOINT_OBSERVABLE_VECTOR'))
        if issues:
            failed.append(dict(replicate=replicate,findings=tuple(issues),values=values))
    rank = math.ceil(Fraction(selection.criteria.simultaneous_coverage)*(len(draws)+1))
    covariance,intervals = None,None
    available = not failed and rank <= len(draws) and all(v is not None and math.isfinite(v) for v in point_values)
    if available:
        matrix = np.asarray(draws,dtype='<f8')
        scale = np.std(matrix,axis=0,ddof=1)
        deviation = abs(matrix-np.asarray(point_values))
        if np.any((scale==0)&np.any(deviation!=0,axis=0)):
            available = False
        else:
            covariance = np.atleast_2d(np.cov(matrix,rowvar=False,ddof=1)).tolist()
            quantile = float(np.sort(np.max(deviation/np.where(scale>0,scale,1),axis=1))[rank-1])
            intervals = tuple((v-quantile*s,v+quantile*s) for v,s in zip(point_values,scale,strict=True))
    return dict(status='SATISFIED' if available else 'UNEVALUABLE',columns=columns,point_values=point_values,
        joint_values=tuple(draws),requested_replicates=len(draws),retained_replicates=len(draws),
        failed_replicates=tuple(failed),covariance=covariance,simultaneous_intervals=intervals,
        simultaneous_coverage=bootstrap['simultaneous_coverage'],simultaneous_quantile_rank=rank,
        resampling_source='ORIGINAL_EQUILIBRIUM_COUPLED_CIRCULAR_BLOCK_STARTS',
        nested_unit='ONE_CONFIGURATION_WITH_ALL_ORIGINAL_CHARGE_SPIN_AND_COUPLING_OBSERVATIONS',
        interpretation='CONDITIONAL_EMPIRICAL_BLOCK_VARIATION_NOT_GUARANTEED_COVERAGE'), {
            'electronic.joint_values':np.asarray([[0. if v is None else v for v in row] for row in draws],dtype='<f8'),
            'electronic.joint_available':np.asarray([[v is not None for v in row] for row in draws],dtype='|b1')}
