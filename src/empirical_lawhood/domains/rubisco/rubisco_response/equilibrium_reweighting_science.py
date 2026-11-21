# SPDX-License-Identifier: MPL-2.0
"""Complete-window MBAR, retained correlation diagnostics and joint block draws.

The reference energy is a common per-configuration gauge within each exact
operator/temperature ensemble. It is retained separately from every window's
bias. Counts remain actual sample counts; correlation changes the uncertainty
calculation, not those counts. No dynamical rate or physical admission follows.
"""

from fractions import Fraction
import math

from empirical_lawhood.domains.rubisco.rubisco_insilico_free_energy.science import reweighting
from empirical_lawhood.domains.rubisco.rubisco_response.transition_state_rates import AVOGADRO_MOL, BOLTZMANN_J_K


def thermal_energy(temperature):
    return float(Fraction(BOLTZMANN_J_K)*Fraction(AVOGADRO_MOL)*Fraction(temperature)/1000)


def cross_window_biases(windows, coordinates):
    """Evaluate all selected harmonic biases from independent scalar coordinates."""
    import numpy as np
    q = np.asarray(coordinates, dtype='<f8')
    if q.ndim != 2 or not np.isfinite(q).all():
        raise ValueError('cross-window coordinates must be a complete finite sample matrix')
    values = np.zeros((len(windows), len(q)), dtype='<f8')
    for index, window in enumerate(windows):
        if window is None:
            continue
        if len(window.cv_kinds) != q.shape[1]:
            raise ValueError('cross-window potential changes the selected coordinate census')
        with np.errstate(over='raise', invalid='raise'):
            displacement = q-np.asarray([float(c) for c in window.centers])
            for axis, kind in enumerate(window.cv_kinds):
                if kind == 'IMPROPER_DIHEDRAL':
                    displacement[:, axis] = np.arctan2(np.sin(displacement[:, axis]), np.cos(displacement[:, axis]))
            values[index] = np.sum(.5*np.asarray([float(k) for k in window.force_constants])*displacement**2, axis=1)
    if not np.isfinite(values).all():
        raise ValueError('cross-window bias energy is not finite')
    return values


def basin_membership(ensemble, coordinates):
    import numpy as np
    q = np.asarray(coordinates, dtype='<f8')
    return np.asarray([np.all((q >= np.asarray([float(x) for x in b.lower]))
        & (q < np.asarray([float(x) for x in b.upper])), axis=1) for b in ensemble.basins], dtype='|b1')


def statistical_inefficiency(values):
    """FFT autocovariance with an initial positive, monotone paired sequence.

    This finite-series diagnostic does not prove stationarity or mixing.
    Constant observations and an unresolved positive tail remain explicit.
    The biased lag normalization includes the finite-series (1-lag/N) factor.
    """
    import numpy as np
    x = np.asarray(values, dtype='<f8')
    if x.ndim != 1 or not np.isfinite(x).all():
        raise ValueError('correlation diagnostic requires one complete finite series')
    n = len(x)
    if n < 4:
        return dict(samples=n, inefficiency=None, effective_samples=None, resolved=False, reason='TOO_FEW_SAMPLES')
    centered = x-float(np.mean(x))
    scale = float(np.max(abs(centered)))
    if scale == 0:
        return dict(samples=n, inefficiency=None, effective_samples=None, resolved=False, reason='ZERO_VARIANCE')
    # Rescale before squaring so large, finite energies do not overflow.
    centered /= scale
    size = 1 << (2*n-1).bit_length()
    transformed = np.fft.rfft(centered, n=size)
    covariance = np.fft.irfft(transformed*transformed.conjugate(), n=size)[:n]
    correlation = covariance/covariance[0]
    pairs, previous, resolved = [], math.inf, False
    for lag in range(0, n-1, 2):
        pair = float(correlation[lag]+correlation[lag+1])
        if pair <= 0:
            resolved = True
            break
        previous = min(previous, pair)
        pairs.append(previous)
    g = max(1., -1.+2.*math.fsum(pairs))
    return dict(samples=n, inefficiency=g, effective_samples=n/g, resolved=resolved,
        retained_lag_pairs=len(pairs), reason=None if resolved else 'POSITIVE_TAIL_NOT_RESOLVED')


def _connected(overlap, minimum):
    n = len(overlap)
    reached, pending = {0}, [0]
    while pending:
        i = pending.pop()
        for j in range(n):
            if j not in reached and Fraction(float(min(overlap[i][j], overlap[j][i]))) >= Fraction(minimum):
                reached.add(j)
                pending.append(j)
    return len(reached) == n


def fit_ensemble(*, ensemble, biases_kj_mol, coordinates, counts, criteria):
    """Reuse the MBAR owner and independently check its estimating equations."""
    import numpy as np
    from scipy.special import logsumexp
    counts = tuple(counts)
    if not counts or any(type(n) is not int or n <= 0 for n in counts):
        return dict(available=False, reason='MISSING_SELECTED_WINDOW_SAMPLES', counts=counts), {}
    thermal = thermal_energy(ensemble.temperature_kelvin)
    biases = np.asarray(biases_kj_mol, dtype='<f8')
    if biases.shape != (len(counts), sum(counts)):
        raise ValueError('free-energy fit changes its complete window/sample denominator')
    reduced = biases/thermal
    fitted = reweighting(reduced, counts, tolerance=criteria.solver_tolerance,
        maximum_iterations=criteria.solver_maximum_iterations)
    f = np.asarray(fitted.free_energies_reduced)
    denominator = logsumexp(np.log(np.asarray(counts))[:, None]+f[:, None]-reduced, axis=0)
    # This independently evaluates the original MBAR equations without the
    # producer's normalized-weight repair or its self-consistency iteration.
    log_weights = f[:, None]-reduced-denominator
    normalization_error = float(np.max(abs(logsumexp(log_weights, axis=1))))
    partition_error = float(np.max(abs(logsumexp(np.log(np.asarray(counts))[:, None]+log_weights, axis=0))))
    checked_weights = np.exp(log_weights-logsumexp(log_weights, axis=1)[:, None])
    recorded_weights = np.asarray(fitted.normalized_weights, dtype='<f8')
    if recorded_weights.shape != reduced.shape or not np.isfinite(recorded_weights).all():
        raise ValueError('MBAR return changes its complete finite weight matrix')
    weight_error = float(np.max(abs(recorded_weights-checked_weights)))
    checked_overlap = (checked_weights@checked_weights.T)*np.asarray(counts)[None, :]
    overlap_error = float(np.max(abs(np.asarray(fitted.overlap)-checked_overlap)))
    checked_ess = 1./np.sum(checked_weights**2, axis=1)
    ess_error = float(np.max(abs(np.asarray(fitted.effective_samples)-checked_ess)/np.maximum(1., checked_ess)))
    residual = max(normalization_error, partition_error, weight_error, overlap_error, ess_error)
    target_log_weights = -denominator-logsumexp(-denominator)
    target_weights = np.exp(target_log_weights)
    membership = basin_membership(ensemble, coordinates)
    probabilities = membership@target_weights
    overlap = checked_overlap
    target_ess = 1./float(target_weights@target_weights)
    window_ess = tuple(float(v) for v in checked_ess)
    numerical_ok = fitted.converged and Fraction(residual) <= 2*Fraction(criteria.solver_tolerance)
    failures = []
    if not numerical_ok:
        failures.append('MBAR_ESTIMATING_EQUATIONS_NOT_RESOLVED')
    if not _connected(overlap, criteria.minimum_overlap):
        failures.append('OVERLAP_GRAPH_DISCONNECTED_AT_SELECTED_THRESHOLD')
    if Fraction(min(window_ess)) < Fraction(criteria.minimum_window_weight_ess):
        failures.append('WINDOW_WEIGHT_ESS_BELOW_SELECTION')
    if Fraction(target_ess) < Fraction(criteria.minimum_target_weight_ess):
        failures.append('TARGET_WEIGHT_ESS_BELOW_SELECTION')
    unavailable = [b.basin_id for b, p in zip(ensemble.basins, probabilities, strict=True) if p <= 0]
    result = dict(available=numerical_ok, reason=None if numerical_ok else failures[0], counts=counts,
        iterations=fitted.iterations, converged=fitted.converged,
        maximum_log_equation_residual=max(normalization_error, partition_error), maximum_mbar_residual=residual,
        maximum_weight_disagreement=weight_error, maximum_overlap_disagreement=overlap_error,
        maximum_relative_weight_ess_disagreement=ess_error,
        window_free_energies_reduced=tuple(float(x) for x in f), window_weight_effective_samples=window_ess,
        target_weight_effective_samples=target_ess, overlap=overlap.tolist(),
        overlap_connected=_connected(overlap, criteria.minimum_overlap),
        probabilities={b.basin_id:float(p) for b,p in zip(ensemble.basins, probabilities, strict=True)},
        basin_free_energies_kj_mol={b.basin_id: -thermal*math.log(p) if p > 0 else None
            for b,p in zip(ensemble.basins, probabilities, strict=True)},
        outside_selected_basins_probability=float(target_weights[~np.any(membership, axis=0)].sum()),
        unavailable_basins=unavailable, selected_criteria_failures=failures,
        reference_energy_gauge='COMMON_EXACT_OPERATOR_AND_TEMPERATURE_PER_SAMPLE',
        physical_rate_admission='UNEVALUABLE')
    arrays = dict(reduced_bias_potentials=reduced, target_weights=target_weights,
        window_weights=checked_weights, basin_membership=membership)
    return result, arrays


def signed_contrasts(selection, results):
    values = []
    for contrast in selection.contrasts:
        terms = []
        for term in contrast.terms:
            result = results[term.ensemble_id]
            value = result.get('basin_free_energies_kj_mol', {}).get(term.basin_id) if result['available'] else None
            if value is None:
                break
            terms.append(float(term.coefficient)*value)
        values.append(math.fsum(terms) if len(terms) == len(contrast.terms) else None)
    return tuple(values)


def joint_block_analysis(*, selection, tables, windows):
    """Fit every selected ensemble and retain each coupled circular-block draw.

    A table contains one trace's original scalar sample projection. The caller
    authenticates its native receipts and exact acquisition configuration.
    Every selected trace remains in its original denominator, including empty
    or failed members. Different declared groups are resampled independently;
    members of one group share every start index and block boundary.
    """
    import numpy as np
    criteria = selection.criteria
    point, point_arrays, groups, trace_ranges, raw = {}, {}, {}, {}, {}
    incomplete_groups = set()
    findings, missing = [], []
    for ensemble in selection.ensembles:
        traces = tuple(t for t in selection.traces if t.ensemble_id == ensemble.ensemble_id)
        counts = tuple(len(tables[t.trace_id]['coordinates']) for t in traces)
        dimension = len(ensemble.coordinate_window.cv_kinds)
        coordinates = np.concatenate([tables[t.trace_id]['coordinates'] for t in traces], axis=0).reshape((-1, dimension))
        biases = cross_window_biases(tuple(windows[t.trace_id] for t in traces), coordinates)
        raw[ensemble.ensemble_id] = (ensemble, traces, coordinates, biases, counts)
        result, arrays = fit_ensemble(ensemble=ensemble, biases_kj_mol=biases, coordinates=coordinates,
            counts=counts, criteria=criteria)
        point[ensemble.ensemble_id], point_arrays[ensemble.ensemble_id] = result, dict(arrays, bias_potentials_kj_mol=biases)
        findings.extend((ensemble.ensemble_id, reason) for reason in result.get('selected_criteria_failures', ()))
        if not result['available'] or result.get('unavailable_basins'):
            missing.append((ensemble.ensemble_id, result.get('reason') or 'UNOBSERVED_SELECTED_BASIN'))
        offset = 0
        for trace, count in zip(traces, counts, strict=True):
            trace_ranges[trace.trace_id] = (offset, offset+count)
            offset += count

    point_contrasts = signed_contrasts(selection, point)
    correlations = {}
    for trace in selection.traces:
        ensemble, _, _, _, _ = raw[trace.ensemble_id]
        table = tables[trace.trace_id]
        n = len(table['coordinates'])
        group = groups.setdefault(trace.resampling_group_id, dict(samples=n, block_samples=trace.block_samples, trace_ids=[], trace_samples={}))
        if group['samples'] != n or group['block_samples'] != trace.block_samples:
            incomplete_groups.add(trace.resampling_group_id)
        if n == 0:
            incomplete_groups.add(trace.resampling_group_id)
        group['trace_ids'].append(trace.trace_id)
        group['trace_samples'][trace.trace_id] = n
        observables = [('reference-energy-kj-mol', table['reference_energy_kj_mol'])]
        for i, kind in enumerate(ensemble.coordinate_window.cv_kinds):
            values = table['coordinates'][:, i]
            if kind == 'IMPROPER_DIHEDRAL':
                observables.extend(((f'cv-{i}-sin', np.sin(values)), (f'cv-{i}-cos', np.cos(values))))
            else:
                observables.append((f'cv-{i}', values))
        membership = basin_membership(ensemble, table['coordinates'])
        for basin, indicator in zip(ensemble.basins, membership, strict=True):
            observables.append(('basin-'+basin.basin_id, indicator.astype('<f8')))
        result_arrays = point_arrays[trace.ensemble_id]
        if 'target_weights' in result_arrays:
            begin, end = trace_ranges[trace.trace_id]
            weights = result_arrays['target_weights'][begin:end]
            for basin, indicator in zip(ensemble.basins, membership, strict=True):
                p = point[trace.ensemble_id]['probabilities'][basin.basin_id]
                observables.append(('weighted-basin-'+basin.basin_id, weights*(indicator-p)))
        measured = {name:statistical_inefficiency(values) for name, values in observables}
        estimable = [v for v in measured.values() if v['inefficiency'] is not None]
        maximum = max((v['inefficiency'] for v in estimable), default=None)
        full_blocks = n//trace.block_samples
        if n == 0:
            missing.append((trace.trace_id, 'SELECTED_TRACE_SAMPLES_UNAVAILABLE'))
        elif full_blocks < criteria.minimum_blocks:
            findings.append((trace.trace_id, 'TOO_FEW_SELECTED_CORRELATION_BLOCKS'))
        if maximum is None or any(not v['resolved'] for v in estimable):
            missing.append((trace.trace_id, 'CORRELATION_TAIL_NOT_RESOLVED'))
        if maximum is not None and trace.block_samples < Fraction(criteria.block_inefficiency_multiplier)*Fraction(maximum):
            findings.append((trace.trace_id, 'BLOCK_SHORTER_THAN_SELECTED_INEFFICIENCY_MULTIPLE'))
        correlations[trace.trace_id] = dict(observables=measured, maximum_inefficiency=maximum,
            estimated_effective_samples=n/maximum if maximum is not None else None,
            selected_block_samples=trace.block_samples, complete_blocks=full_blocks,
            remainder_samples=n%trace.block_samples, equilibrium_admission='UNEVALUABLE')

    # Compare both complete half-windows. Neither half is silently selected as
    # an improved production prefix, and an absent basin remains unresolved.
    halves = []
    for half in (0, 1):
        fitted = {}
        for name, (ensemble, traces, coordinates, biases, _) in raw.items():
            selected, counts = [], []
            for trace in traces:
                begin, end = trace_ranges[trace.trace_id]
                mid = begin+(end-begin)//2
                indices = list(range(begin, mid)) if half == 0 else list(range(mid, end))
                selected.extend(indices)
                counts.append(len(indices))
            fitted[name], _ = fit_ensemble(ensemble=ensemble, biases_kj_mol=biases[:, selected],
                coordinates=coordinates[selected], counts=tuple(counts), criteria=criteria)
        halves.append(dict(ensembles=fitted, contrasts_kj_mol=signed_contrasts(selection, fitted)))
    split = []
    for contrast, first, second in zip(selection.contrasts, halves[0]['contrasts_kj_mol'], halves[1]['contrasts_kj_mol'], strict=True):
        difference = abs(first-second) if first is not None and second is not None else None
        split.append(difference)
        if difference is None:
            missing.append((contrast.contrast_id, 'SPLIT_CONTRAST_UNAVAILABLE'))
        elif Fraction(difference) > Fraction(criteria.maximum_split_contrast_kj_mol):
            findings.append((contrast.contrast_id, 'SPLIT_CONTRAST_DISAGREEMENT_EXCEEDS_SELECTION'))

    rng = np.random.Generator(np.random.PCG64DXSM(criteria.bootstrap_seed))
    replicates, failed, starts = [], [], {key:[] for key in sorted(groups)}
    for replicate in range(criteria.bootstrap_replicates):
        if incomplete_groups:
            values = (None,)*len(selection.contrasts)
            replicates.append(values)
            failed.append(dict(replicate=replicate, findings=tuple((g, 'INCOMPLETE_DEPENDENCE_GROUP')
                for g in sorted(incomplete_groups)), contrasts_kj_mol=values))
            for name in starts:
                starts[name].append(None)
            continue
        indices_by_group = {}
        for name, group in sorted(groups.items()):
            n, length = group['samples'], group['block_samples']
            draw = rng.integers(n, size=(n+length-1)//length, dtype=np.int64) if n else np.empty(0, dtype=np.int64)
            starts[name].append(draw.tolist())
            indices_by_group[name] = ((draw[:, None]+np.arange(length)) % n).ravel()[:n] if n else np.empty(0, dtype=np.int64)
        fitted, issues = {}, []
        for name, (ensemble, traces, coordinates, biases, counts) in raw.items():
            indices = np.concatenate([indices_by_group[t.resampling_group_id]+trace_ranges[t.trace_id][0] for t in traces])
            fitted[name], _ = fit_ensemble(ensemble=ensemble, biases_kj_mol=biases[:, indices],
                coordinates=coordinates[indices], counts=counts, criteria=criteria)
            if not fitted[name]['available'] or fitted[name].get('unavailable_basins'):
                issues.append((name, fitted[name].get('reason') or 'UNOBSERVED_SELECTED_BASIN'))
            if fitted[name].get('overlap_connected') is False:
                issues.append((name, 'RESAMPLED_OVERLAP_DISCONNECTED'))
        values = signed_contrasts(selection, fitted)
        replicates.append(values)
        if issues or any(value is None for value in values):
            failed.append(dict(replicate=replicate, findings=issues, contrasts_kj_mol=values))
    covariance, half_width, intervals = None, None, None
    rank = math.ceil(Fraction(criteria.simultaneous_coverage)*(criteria.bootstrap_replicates+1))
    if failed or any(value is None for value in point_contrasts):
        missing.append(('joint-bootstrap', 'INCOMPLETE_JOINT_REPLICATE_CENSUS'))
    elif rank > criteria.bootstrap_replicates:
        missing.append(('joint-bootstrap', 'TOO_FEW_REPLICATES_FOR_SELECTED_QUANTILE'))
    else:
        draws = np.asarray(replicates, dtype='<f8')
        covariance = np.atleast_2d(np.cov(draws, rowvar=False, ddof=1)).tolist()
        deviations = np.max(abs(draws-np.asarray(point_contrasts)), axis=1)
        half_width = float(np.sort(deviations)[rank-1])
        intervals = tuple((value-half_width, value+half_width) for value in point_contrasts)
    status = 'FALSIFIED' if findings else 'UNEVALUABLE' if missing else 'SATISFIED'
    return dict(selected_numerical_sampling_criteria=status, ensembles=point,
        contrast_ids=tuple(c.contrast_id for c in selection.contrasts), contrasts_kj_mol=point_contrasts,
        correlation=correlations, split_halves=halves, split_contrast_disagreement_kj_mol=tuple(split),
        findings=tuple(sorted(set(findings))), missing=tuple(sorted(set(missing))),
        bootstrap=dict(method='COUPLED_CIRCULAR_BLOCKS_FIXED_LENGTH_COMPLETE_COUNTS', generator='NUMPY_PCG64DXSM',
            numpy_version=np.__version__, seed=criteria.bootstrap_seed, groups=groups, block_starts=starts,
            requested_replicates=criteria.bootstrap_replicates, retained_replicates=len(replicates),
            failed_replicates=failed, joint_contrasts_kj_mol=tuple(replicates), covariance_kj_mol_squared=covariance,
            simultaneous_coverage=str(criteria.simultaneous_coverage), simultaneous_quantile_rank=rank,
            simultaneous_max_error_kj_mol=half_width,
            simultaneous_intervals_kj_mol=intervals, interpretation='CONDITIONAL_BLOCK_BOOTSTRAP_ESTIMATE_NOT_GUARANTEED_COVERAGE'),
        equilibrium_admission='UNEVALUABLE', chemical_model_admission='UNEVALUABLE',
        physical_rate_admission='UNEVALUABLE', biological_admission='UNEVALUABLE'), point_arrays
