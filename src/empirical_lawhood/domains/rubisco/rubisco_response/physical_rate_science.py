# SPDX-License-Identifier: MPL-2.0
"""Conditional competing-hazard estimates with whole-run uncertainty.

For grid probability q and step dt, lambda = -log(1-q)/dt. The weighted
estimating criterion uses all competing exits and intact horizon censoring.
It is not an independent-particle likelihood for weighted descendants.
"""

from dataclasses import dataclass
from decimal import Decimal, localcontext
from fractions import Fraction
import math

from empirical_lawhood.domains.rubisco.rubisco_response.physical_first_passage_science import rational


@dataclass(frozen=True, slots=True)
class RateObservation:
    path_id: str
    entry_history_id: str
    weight: Fraction
    last_step: int
    event_id: str | None
    complete: bool


def _decimal(value):
    value = Fraction(value)
    return Decimal(value.numerator)/Decimal(value.denominator)


def status(*values):
    return 'FALSIFIED' if 'FALSIFIED' in values else 'UNEVALUABLE' if 'UNEVALUABLE' in values else 'SATISFIED'


def selected_samples(groups, counts):
    denominator = sum(counts)
    return tuple((row, row.weight*Fraction(count, denominator))
        for count, group in zip(counts, groups, strict=True) if count for row in group)


def fit_hazards(*, samples, event_ids, dt, left=0, right=None, history=None):
    """Retain the exact weighted score operands; never infer a missing cause zero."""
    chosen = tuple((row, weight) for row, weight in samples if history is None or row.entry_history_id == history)
    assigned = sum((w for _, w in chosen), Fraction())
    invalid = tuple(row.path_id for row, _ in chosen if not row.complete)
    risk = sum((w for row, w in chosen if row.last_step > left), Fraction())
    exposure = sum((w*max(0, min(row.last_step, right if right is not None else row.last_step)-left)
        for row, w in chosen), Fraction())
    deaths = {event:sum((w for row, w in chosen if row.event_id == event
        and left < row.last_step and (right is None or row.last_step <= right)), Fraction()) for event in event_ids}
    total = sum(deaths.values(), Fraction())
    result = dict(assigned_weight=rational(assigned), at_risk_weight=rational(risk),
        weighted_at_risk_steps=rational(exposure), event_weights={k:rational(v) for k,v in deaths.items()},
        event_probability_per_grid_step=None, exit_rate_per_second=None,
        cause_rates_per_second=dict.fromkeys(event_ids), eventual_cause_probabilities=dict.fromkeys(event_ids),
        extrapolated_exponential_mean_seconds=None, invalid_path_ids=invalid, reason=None)
    if invalid or not assigned or not exposure or not 0 < total < exposure:
        result['reason'] = ('COMPUTATIONAL_OR_UNASSESSED_WEIGHT' if invalid else 'NO_SELECTED_HISTORY_WEIGHT' if not assigned
            else 'NO_AT_RISK_TIME' if not exposure else 'NO_OBSERVED_EXIT' if total == 0 else 'UNRESOLVED_SUBSTEP_EXIT_RATE')
        return result
    q = total/exposure
    with localcontext() as ctx:
        # Exact WE weights can put q very close to zero or one. Resolve the
        # rational subtraction before the logarithm rather than rounding q.
        ctx.prec = 80+len(str(q.denominator))
        rate = -(Decimal(1)-_decimal(q)).ln()/_decimal(dt)
        if not math.isfinite(float(rate)) or float(rate) <= 0:
            result['reason'] = 'RATE_OUTSIDE_FINITE_ANALYSIS_REPRESENTATION'
            return result
        result.update(event_probability_per_grid_step=rational(q), exit_rate_per_second=str(rate),
            extrapolated_exponential_mean_seconds=str(1/rate))
        for event, value in deaths.items():
            if value:
                result['cause_rates_per_second'][event] = str(rate*_decimal(value/total))
                result['eventual_cause_probabilities'][event] = rational(value/total)
    return result


def _support(fit, criteria):
    from empirical_lawhood.domains.rubisco.rubisco_response.physical_first_passage_science import fraction
    assigned = fraction(fit['assigned_weight'])
    return bool(assigned and not fit['invalid_path_ids'] and fit['exit_rate_per_second'] is not None
        and fraction(fit['at_risk_weight'])/assigned >= Fraction(criteria.minimum_at_risk_probability)
        and all(fraction(v)/assigned >= Fraction(criteria.minimum_event_probability) for v in fit['event_weights'].values()))


def _log_changes(reference, comparison):
    changes = {}
    with localcontext() as ctx:
        ctx.prec = 80
        for key, value in reference['cause_rates_per_second'].items():
            other = comparison['cause_rates_per_second'][key]
            changes[key] = float(abs(Decimal(other).ln()-Decimal(value).ln())) if value is not None and other is not None else None
    return changes


def assess_hazard_arithmetic(*, samples, event_ids, dt, fit, tolerance):
    """Check the rate by survival-area integration and the transition equations.

    The survival-area calculation uses sorted event/end boundaries. It does
    not use the fitter's weighted-duration sum or its logarithm calculation.
    """
    if fit['exit_rate_per_second'] is None:
        return dict(status='UNEVALUABLE', reason=fit['reason'])
    from empirical_lawhood.domains.rubisco.rubisco_response.physical_first_passage_science import fraction
    boundaries = sorted({0, *(r.last_step for r, _ in samples)})
    area = Fraction()
    for left, right in zip(boundaries[:-1], boundaries[1:], strict=True):
        survivors = sum((w for row, w in samples if row.last_step > left), Fraction())
        area += (right-left)*survivors
    observed = {event:sum((w for row, w in samples if row.event_id == event), Fraction()) for event in event_ids}
    if area != fraction(fit['weighted_at_risk_steps']) or any(observed[k] != fraction(fit['event_weights'][k]) for k in event_ids):
        raise ValueError('physical rate changes its independently integrated risk or competing-event denominator')
    rate = float(fit['exit_rate_per_second'])
    q = float(sum(observed.values(), Fraction())/area)
    error = abs(-math.expm1(-rate*float(dt))-q)
    causes = fit['cause_rates_per_second']
    numerical_sum = math.fsum(float(v) for v in causes.values() if v is not None)
    error = max(error, abs(numerical_sum/rate-1))
    total = sum(observed.values(), Fraction())
    for event, value in causes.items():
        if value is not None:
            error = max(error, abs(float(value)/rate-float(observed[event]/total)))
        elif observed[event]:
            raise ValueError('physical rate discards an observed competing exit')
    return dict(status='SATISFIED' if error <= float(tolerance) else 'FALSIFIED',
        maximum_dimensionless_equation_error=error, independently_integrated_risk_steps=rational(area),
        scope='SURVIVAL_AREA_AND_COMPETING_TRANSITION_IDENTITIES_NOT_PHYSICAL_MODEL_VALIDATION')


def assess_case(*, case, ensemble, groups, dt, horizon_steps, criteria):
    samples = selected_samples(groups, (1,)*len(groups))
    event_ids = tuple(e.event_id for e in ensemble.events)
    fitted = fit_hazards(samples=samples, event_ids=event_ids, dt=dt)
    supported = _support(fitted, criteria) and len(groups) >= criteria.minimum_run_groups
    arithmetic = assess_hazard_arithmetic(samples=samples, event_ids=event_ids, dt=dt,
        fit=fitted, tolerance=criteria.maximum_arithmetic_error)
    grids = tuple(int(Fraction(t)/dt) for t in case.observation_times_seconds)
    curves, residual = [], None
    if fitted['exit_rate_per_second'] is not None:
        rate = float(fitted['exit_rate_per_second'])
        residual = 0.
        for step in grids:
            survival = sum((w for row,w in samples if row.last_step > step or row.event_id is None), Fraction())
            expected_survival = math.exp(-rate*float(dt*step))
            observed = {event:sum((w for row,w in samples if row.event_id == event and row.last_step <= step), Fraction()) for event in event_ids}
            expected = {event:(float(value)/rate*(1-expected_survival) if value is not None else None)
                for event,value in fitted['cause_rates_per_second'].items()}
            residual = max(residual, abs(float(survival)-expected_survival),
                *(abs(float(observed[event])-value) for event,value in expected.items() if value is not None))
            curves.append(dict(physical_step=step, physical_time_seconds=rational(dt*step),
                survival=rational(survival), expected_survival=expected_survival,
                cumulative_event_probability={k:rational(v) for k,v in observed.items()}, expected_cumulative_event_probability=expected))
    curve_status = ('UNEVALUABLE' if not supported else
        'SATISFIED' if residual <= float(criteria.maximum_cumulative_probability_error) else 'FALSIFIED')
    dwell = []
    for left,right in zip((0,*grids[:-1]), grids, strict=True):
        local = fit_hazards(samples=samples, event_ids=event_ids, dt=dt, left=left, right=right)
        changes = _log_changes(fitted, local)
        result = ('UNEVALUABLE' if not supported or not _support(local, criteria) or any(v is None for v in changes.values())
            else 'SATISFIED' if max(changes.values()) <= float(criteria.maximum_dwell_log_rate_change) else 'FALSIFIED')
        dwell.append(dict(left_step=left, right_step=right, fit=local, absolute_log_rate_change=changes, status=result))
    histories = {}
    for history in case.entry_history_ids:
        local = fit_hazards(samples=samples, event_ids=event_ids, dt=dt, history=history)
        changes = _log_changes(fitted, local)
        result = ('UNEVALUABLE' if not supported or not _support(local, criteria) or any(v is None for v in changes.values())
            else 'SATISFIED' if max(changes.values()) <= float(criteria.maximum_history_log_rate_change) else 'FALSIFIED')
        histories[history] = dict(fit=local, absolute_log_rate_change=changes, status=result)
    history_status = 'UNEVALUABLE' if len(histories)<2 else status(*(r['status'] for r in histories.values()))
    dwell_status = status(*(r['status'] for r in dwell))
    return dict(fit=fitted, numerical_assessment=arithmetic,
        empirical_cumulative_probability_check=dict(status=curve_status, maximum_absolute_error=residual, curves=curves),
        dwell_time_check=dict(status=dwell_status, intervals=dwell),
        entry_history_check=dict(status=history_status, histories=histories),
        reduction_assessment=status(arithmetic['status'], curve_status, dwell_status, history_status),
        integration_step_seconds=rational(dt), horizon_steps=horizon_steps, declared_whole_run_groups=len(groups),
        cause_roles={e.event_id:e.role for e in ensemble.events},
        missing_cause_rates=tuple(k for k,v in fitted['cause_rates_per_second'].items() if v is None),
        conditional_estimator='EXACT_WEIGHTED_GRID_ESTIMATING_EQUATIONS_WITH_CONSTANT_COMPETING_HAZARDS',
        uncertainty_interpretation='DECLARED_WHOLE_RUN_GROUPS_NOT_DESCENDANT_OR_SITE_INDEPENDENCE')


def joint_rate_resampling(*, selection, ensembles, datasets, clocks, reports):
    """Use the same retained whole-group draws for every paired rate and control."""
    import numpy as np
    group_count = len(selection.run_groups)
    rng = np.random.Generator(np.random.PCG64DXSM(selection.bootstrap_seed))
    draws = rng.integers(0, group_count, size=(selection.bootstrap_replicates, group_count), dtype=np.int64)
    columns = tuple((e.ensemble_id,event.event_id) for e in ensembles for event in e.events)
    values = np.zeros((len(draws), len(columns)), dtype='<f8')
    valid = np.zeros(values.shape, dtype='<i8')
    failures, decimal_rows = [], []
    for draw_index, draw in enumerate(draws):
        counts = np.bincount(draw, minlength=group_count)
        column = 0
        reasons = {}
        exact_values = []
        for ensemble in ensembles:
            samples = selected_samples(datasets[ensemble.ensemble_id], tuple(map(int, counts)))
            fit = fit_hazards(samples=samples, event_ids=tuple(e.event_id for e in ensemble.events), dt=clocks[ensemble.ensemble_id][0])
            for event,value in fit['cause_rates_per_second'].items():
                exact_values.append(value)
                if value is not None and math.isfinite(float(value)) and float(value)>0:
                    values[draw_index,column],valid[draw_index,column] = float(value),1
                else:
                    reasons[ensemble.ensemble_id+'/'+event] = fit['reason'] or 'UNOBSERVED_COMPETING_CAUSE'
                column += 1
        decimal_rows.append(tuple(exact_values))
        if reasons:
            failures.append(dict(replicate=draw_index, unresolved=reasons))
    point = [reports[e]['fit']['cause_rates_per_second'][event] for e,event in columns]
    radius, intervals, covariance = None, None, None
    enough = group_count >= selection.criteria.minimum_run_groups
    if enough and not failures and all(v is not None and 0 < float(v) < math.inf for v in point):
        logs = np.log(values)
        center = np.asarray([math.log(float(v)) for v in point])
        deviations = np.max(np.abs(logs-center), axis=1)
        radius = float(np.quantile(deviations, float(selection.central_resampling_mass), method='higher'))
        intervals = []
        with localcontext() as ctx:
            ctx.prec = 80
            factor = Decimal.from_float(radius).exp()
            for (ensemble,event),value in zip(columns,point,strict=True):
                intervals.append(dict(ensemble_id=ensemble,event_id=event,
                    lower_per_second=str(Decimal(value)/factor), upper_per_second=str(Decimal(value)*factor)))
        covariance = np.atleast_2d(np.cov(logs,rowvar=False,ddof=1)).tolist()
    report = dict(columns=columns, resampling_generator='NUMPY_PCG64DXSM', numpy_version=np.__version__,
        seed=selection.bootstrap_seed, assigned_replicates=len(draws), unidentifiable_replicates=failures,
        complete_replicates=len(draws)-len(failures), central_resampling_mass=str(selection.central_resampling_mass),
        simultaneous_log_radius=radius, conditional_simultaneous_intervals=intervals,
        joint_log_rate_covariance=covariance,
        status='SATISFIED' if intervals is not None else 'UNEVALUABLE',
        resampled_decimal_rates_per_second=tuple(decimal_rows),
        scope='CONDITIONAL_EMPIRICAL_RUN_BOOTSTRAP_NOT_CALIBRATED_COVERAGE_OR_PHYSICAL_MODEL_ERROR',
        independent_units_added=0, all_replicates_retained=True)
    arrays = {'rate.group-draws':draws.astype('<i8'), 'rate.resampled-rates-per-second':values, 'rate.resampled-rate-observed':valid}
    for array in arrays.values():
        array.setflags(write=False)
    return report, arrays
