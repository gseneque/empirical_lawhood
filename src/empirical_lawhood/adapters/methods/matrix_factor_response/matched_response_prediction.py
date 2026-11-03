# SPDX-License-Identifier: MPL-2.0
"""Shared matched FACTOR-curve prediction for the nominal and relation accounts.

Only received causal values and declared training/calibration banks enter this
owner. Source custody, pre-future receipt order and protected access remain with
the ordinary acquisition, feature, fitting and reader boundaries.
"""

from dataclasses import dataclass
from decimal import Decimal, DecimalException, localcontext
from fractions import Fraction
from typing import ClassVar

import numpy as np

from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_decimal, validate_stable_id
from empirical_lawhood.runtime.experimental_statistics import assigned_binomial_inference, binomial_probability_interval, split_upper_calibration
from .response_error_prediction import FEATURE_BLOCKS, FEATURES
from .curve_contract import MECHANISM_FEATURES
from .response_scoring import (
    DENSE_RESPONSE_HORIZONS, MatrixSampledResponseDuration, origin_response_discrepancy,
    paired_adequacy, sampled_pass_count_bounds,
)


DRIFT_FEATURES = ('momentum-x-drift', 'momentum-y-drift', 'position-x-drift', 'position-y-drift')
SHARED_FEATURES = tuple(sorted((*FEATURE_BLOCKS['CONTEXT'], *FEATURE_BLOCKS['NORM_RADIUS'],
    *FEATURE_BLOCKS['SPECTRAL'], 'd_lin')))
STRUCTURAL_FEATURES = FEATURE_BLOCKS['FACTOR']
MATCHED_FEATURES = tuple(sorted((*FEATURES, *DRIFT_FEATURES, 'd_lin')))
CURVE_SHARED_FEATURES = tuple(sorted((*SHARED_FEATURES, *MECHANISM_FEATURES)))
CURVE_MATCHED_FEATURES = tuple(sorted((*MATCHED_FEATURES, *MECHANISM_FEATURES)))
MATCHED_FEATURE_BLOCKS = {**FEATURE_BLOCKS, 'LINEAR_DEFECT': ('d_lin',), 'NORM_DRIFT': DRIFT_FEATURES,
    'PAST_HESSIAN': MECHANISM_FEATURES}
MATCHED_METHODS = ('B0', 'RAW_TRAIN_MEDIAN', 'S0', 'SHARED_BASE')
MATCHED_TARGET_COUNT = 58


def validate_matched_features(values, disposition, *, curve_primary=None):
    if curve_primary is not None and type(curve_primary) is not bool:
        raise TypeError('matched feature validation requires its declared scientific selection')
    menus = ((MATCHED_FEATURES, CURVE_MATCHED_FEATURES) if curve_primary is None else
        (CURVE_MATCHED_FEATURES,) if curve_primary else (MATCHED_FEATURES,))
    if (type(values) is not tuple or
            (tuple(name for name, _ in values) not in menus if disposition == 'AVAILABLE' else bool(values))):
        raise ValueError('matched causal features lose their common complete descriptor and drift census')
    for name, value in values:
        validate_decimal(value, field_name='matched causal feature',
            minimum=None if name in DRIFT_FEATURES else Decimal(0))


def matched_causal_feature_values(protocol, *, prefix_disposition, prefix_frame_sha256, traces,
        causal_arrays, diagnostics, frozen_arrays, feature_window_ticks=32, feature_cadence_ticks=16,
        curve_primary=False):
    """Shared PRIMARY origin defect and signed raw-norm slopes, never futures.

    The caller binds the original mechanical forecast and its exact array port
    before delivery. Its FINE defect is retained separately as a diagnostic.
    """
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.forecast import causal_feature_values
    from .origin_mechanics import MatrixOriginResponseModel
    if (type(curve_primary) is not bool or type(protocol.mechanical_model) is not MatrixOriginResponseModel
            or protocol.horizon_steps != DENSE_RESPONSE_HORIZONS):
        raise ValueError('matched features require the exact amended pre-future mechanical assay')
    public = protocol.public_source
    disposition, values = causal_feature_values(public.coordinate, public.policy,
        prefix_disposition=prefix_disposition, prefix_frame_sha256=prefix_frame_sha256, traces=traces,
        causal_arrays=causal_arrays, diagnostics=diagnostics, feature_window_ticks=feature_window_ticks,
        feature_cadence_ticks=feature_cadence_ticks)
    if disposition != 'AVAILABLE':
        return disposition, (), None
    primary, fine = origin_response_discrepancy(protocol, frozen_arrays)
    defects = tuple(curve.cumulative_sampled_errors(numerical_usable=True)[-1] for curve in (primary, fine))
    with localcontext() as context:
        context.prec = 60
        fine_defect = None if defects[1] is None else (Decimal(1) + defects[1]).ln()
        if defects[0] is None:
            return 'UNAVAILABLE', (), fine_defect
        result = dict(values)
        result['d_lin'] = (Decimal(1) + defects[0]).ln()
        tick = public.policy.cutoff_tick
        first = max(0, tick - feature_window_ticks)
        elapsed = public.coordinate.primary_view.timestep * (tick - first)
        for member, label in (('positions', 'position'), ('momenta', 'momentum')):
            states = causal_arrays['primary_' + member]
            for index, sector in enumerate(('x', 'y')):
                before, after = (float(np.linalg.norm(states[time, index])) for time in (first, tick))
                if not np.isfinite((before, after)).all() or elapsed <= 0:
                    return 'UNAVAILABLE', (), fine_defect
                result[label + '-' + sector + '-drift'] = (Decimal(repr(after)) - Decimal(repr(before))) / elapsed
    if curve_primary:
        from .causal_hessian import causal_hessian_features
        primary = causal_hessian_features(protocol, causal_arrays, frozen_arrays, include_fine=False)[0]
        if primary.reasons:
            return 'UNAVAILABLE', (), fine_defect
        result.update(primary.values)
    values = tuple(sorted(result.items()))
    validate_matched_features(values, 'AVAILABLE', curve_primary=curve_primary)
    return 'AVAILABLE', values, fine_defect


@dataclass(frozen=True, slots=True)
class MatchedResponseViewOutcome(CanonicalRecord):
    """One actual view's complete 29 cumulative FACTOR errors."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-experiment/matched-factor-view-outcome'
    view_id: str
    errors: tuple[Decimal | None, ...]
    dispositions: tuple[str, ...]

    def __post_init__(self):
        from .experiment_methods import OUTCOME_DISPOSITIONS
        if (self.view_id not in ('primary', 'fine') or type(self.errors) is not tuple or len(self.errors) != 29
                or type(self.dispositions) is not tuple or len(self.dispositions) != 29):
            raise ValueError('matched outcome changes its complete29 FACTOR target order')
        for index, (value, disposition) in enumerate(zip(self.errors, self.dispositions, strict=True)):
            if disposition not in OUTCOME_DISPOSITIONS or (value is not None) != (disposition == 'FINITE'):
                raise ValueError('matched outcome invents a finite unresolved target')
            if value is not None:
                validate_decimal(value, field_name='matched cumulative FACTOR error', minimum=Decimal(0))
                if index and (self.errors[index - 1] is None or value < self.errors[index - 1]):
                    raise ValueError('matched outcome drops preceding missingness or cumulative error')


def postprocess_log_points(values):
    """The same nonnegative cumulative curve is used for tuning and calibration."""
    if type(values) is not tuple or len(values) != MATCHED_TARGET_COUNT:
        raise ValueError('matched prediction requires PRIMARY29 followed by FINE29')
    result = []
    for start in (0, 29):
        previous, missing = Decimal(0), False
        for value in values[start:start + 29]:
            if value is not None:
                validate_decimal(value, field_name='matched raw log prediction')
            missing = missing or value is None
            if missing:
                result.append(None)
            else:
                previous = max(previous, value)
                result.append(previous)
    return tuple(result)


def original_error_points(log_points):
    points = postprocess_log_points(log_points)
    with localcontext() as context:
        context.prec = 60
        return tuple(None if point is None else point.exp() - 1 for point in points)


def matched_duration_loss(log_points, observed_errors):
    count = matched_duration_error_count(log_points, observed_errors)
    with localcontext() as context:
        context.prec = 60
        return None if count is None else Decimal(count) / 58


def matched_duration_error_count(log_points, observed_errors):
    if type(observed_errors) is not tuple or len(observed_errors) != MATCHED_TARGET_COUNT:
        raise ValueError('matched duration loss requires both complete sampled-view target rosters')
    predictions = postprocess_log_points(log_points)
    with localcontext() as context:
        context.prec = 60
        log_tolerance = Decimal('1.01').ln()
    # The monotone log-domain comparison avoids overflow and a rounded
    # exp(log(1.01))-1 changing the inclusive adequacy boundary.
    predicted_bounds = tuple(sampled_pass_count_bounds(tuple(None if value is None else value <= log_tolerance
        for value in predictions[start:start + 29])) for start in (0, 29))
    predicted_counts = tuple(lower if lower == upper else None for lower, upper in predicted_bounds)
    observed = tuple(MatrixSampledResponseDuration(observed_errors[start:start + 29], Decimal('.01'), True,
        tuple(value is not None for value in observed_errors[start:start + 29])) for start in (0, 29))
    if any(value is None for value in (*predicted_counts, *(row.count for row in observed))):
        return None
    # Recover an exact integer from the two finite initial pass counts; no
    # rounded decimal comparison decides CV ties or the primary win margin.
    return sum(abs(left - right.count) for left, right in zip(predicted_counts, observed, strict=True))


def matched_calibration_score(log_points, observed_errors):
    """One maximum-positive residual over both29 postprocessed curves."""
    points = postprocess_log_points(log_points)
    if type(observed_errors) is not tuple or len(observed_errors) != MATCHED_TARGET_COUNT:
        raise ValueError('matched calibration drops its complete58 target census')
    if any(value is None for value in (*points, *observed_errors)):
        return None
    with localcontext() as context:
        context.prec = 60
        for value in observed_errors:
            validate_decimal(value, field_name='matched calibration target', minimum=Decimal(0))
        return max(Decimal(0), *((Decimal(1) + observed).ln() - point
            for point, observed in zip(points, observed_errors, strict=True)))


def paired_factor_targets(outcome):
    """The declared target order is PRIMARY29 followed by FINE29."""
    return tuple(value for view in ('primary', 'fine') for value in outcome.view(view).errors)


@dataclass(frozen=True, slots=True)
class MatchedRootDecision(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-experiment/matched-root-decision'
    unit_id: str
    usable: bool
    success: bool
    # Each integer is abs(Kp-predictedKp) + abs(Kf-predictedKf), over 58.
    duration_error_counts: tuple[tuple[str, int | None], ...]
    reasons: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.unit_id)
        values = dict(self.duration_error_counts)
        if (tuple(values) != MATCHED_METHODS or type(self.usable) is not bool or type(self.success) is not bool
                or any(value is not None and (type(value) is not int or not 0 <= value <= 58) for value in values.values())
                or self.usable and any(values[method] is None for method in ('S0', 'B0'))
                or self.success != (self.usable and values['B0'] - values['S0'] >= 2)
                or not self.reasons or self.reasons != tuple(sorted(set(self.reasons)))):
            raise ValueError('matched root decision changes the paired K denominator or exact one-of29 win margin')

    @property
    def improvement_count(self):
        values = dict(self.duration_error_counts)
        return None if not self.usable else values['B0'] - values['S0']


def matched_root_decision(unit_id, points, outcome, reasons):
    targets = paired_factor_targets(outcome)
    losses = tuple((method, matched_duration_error_count(points[method], targets)) for method in MATCHED_METHODS)
    reasons = set(reasons)
    if any(dict(losses)[method] is None for method in ('S0', 'B0')):
        reasons.add('MISSING_PAIRED_DURATION_PREDICTION_OR_TARGET')
    usable = not reasons
    success = usable and dict(losses)['B0'] - dict(losses)['S0'] >= 2
    if usable:
        reasons.add('PAIRED_DURATION_SUCCESS' if success else 'PAIRED_DURATION_MARGIN_NOT_MET')
    return MatchedRootDecision(unit_id, usable, success, losses, tuple(sorted(reasons)))


def matched_primary_inference(decisions):
    return assigned_binomial_inference(tuple(row.unit_id for row in decisions),
        tuple(row.success if row.usable else None for row in decisions),
        null_probability=Fraction(1, 2), alpha=Fraction(1, 160))


@dataclass(frozen=True, slots=True)
class MatchedModelCalibration(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-experiment/matched-model-calibration'
    method_key: str
    scores: tuple[tuple[str, Decimal | None, tuple[str, ...]], ...]
    rank: int
    radius: Decimal | None

    def __post_init__(self):
        if (self.method_key not in ('S0', 'B0', 'SR', 'BR') or not self.scores
                or tuple(row[0] for row in self.scores) != tuple(sorted({row[0] for row in self.scores}))):
            raise ValueError('matched calibration changes its model or complete assigned whole-group roster')
        for unit, score, reasons in self.scores:
            validate_stable_id(unit)
            if score is not None:
                validate_decimal(score, field_name='whole-group paired calibration score', minimum=Decimal(0))
            if not reasons or reasons != tuple(sorted(set(reasons))):
                raise ValueError('matched calibration drops its explicit finite or infinite reasons')
        ranked = split_upper_calibration(tuple(score for _, score, _ in self.scores), Decimal('.05'))
        if (type(self.rank) is not int or self.rank != ranked.rank
                or self.radius != (None if ranked.radius.is_infinite() else ranked.radius)):
            raise ValueError('matched calibration changes its complete-rank95 radius')


def matched_model_calibration(method, scores):
    ranked = split_upper_calibration(tuple(row[1] for row in scores), Decimal('.05'))
    return MatchedModelCalibration(method, scores, ranked.rank, None if ranked.radius.is_infinite() else ranked.radius)


@dataclass(frozen=True, slots=True)
class MatchedForecastPolicy(CanonicalRecord):
    """Pre-future bound and both-view admission at every sampled horizon."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-experiment/matched-forecast-policy'
    method_key: str
    bound_kind: str
    upper_errors: tuple[Decimal | None, ...]
    admissions: tuple[bool | None, ...]

    def __post_init__(self):
        if (self.method_key not in ('S0', 'B0', 'SR', 'BR')
                or self.bound_kind not in ('UNCALIBRATED', 'FINITE', 'INFINITE', 'UNAVAILABLE')
                or type(self.upper_errors) is not tuple or len(self.upper_errors) != 58
                or type(self.admissions) is not tuple or len(self.admissions) != 29):
            raise ValueError('matched forecast policy changes its complete paired58 bound/admission census')
        finite = self.bound_kind == 'FINITE'
        for value in self.upper_errors:
            if (value is not None) != finite:
                raise ValueError('matched policy invents a finite upper bound')
            if value is not None:
                validate_decimal(value, field_name='matched upper error', minimum=Decimal(0))
        expected = (tuple(max(self.upper_errors[index], self.upper_errors[index + 29]) <= Decimal('.01') for index in range(29))
            if finite else (False,) * 29 if self.bound_kind == 'INFINITE' else (None,) * 29)
        if self.admissions != expected or any(value is not None and type(value) is not bool for value in self.admissions):
            raise ValueError('matched policy changes its fixed both-view adequacy admission rule')
        if finite and any(self.upper_errors[start + index] < self.upper_errors[start + index - 1]
                for start in (0, 29) for index in range(1, 29)):
            raise ValueError('matched policy drops cumulative upper-curve maxima')


def matched_forecast_policy(method, points, radius, *, calibrated):
    points = postprocess_log_points(points)
    kind = ('UNCALIBRATED' if not calibrated else 'UNAVAILABLE' if any(point is None for point in points)
        else 'INFINITE' if radius is None else 'FINITE')
    if kind == 'FINITE':
        try:
            with localcontext() as context:
                context.prec = 60
                upper = tuple((point + radius).exp() - 1 for point in points)
            admissions = tuple(max(upper[index], upper[index + 29]) <= Decimal('.01') for index in range(29))
        except DecimalException:
            kind = 'UNAVAILABLE'
    if kind != 'FINITE':
        upper, admissions = (None,) * 58, (False if kind == 'INFINITE' else None,) * 29
    return MatchedForecastPolicy(method, kind, upper, admissions)


@dataclass(frozen=True, slots=True)
class MatchedCoverage(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-experiment/matched-coverage'
    unit_id: str
    method_key: str
    bound_kind: str
    covered: bool | None
    original_unit_slacks: tuple[Decimal | None, ...]

    def __post_init__(self):
        validate_stable_id(self.unit_id)
        if (self.method_key not in ('S0', 'B0', 'SR', 'BR') or self.bound_kind not in ('FINITE', 'INFINITE', 'UNAVAILABLE')
                or (self.covered is None) != (self.bound_kind == 'UNAVAILABLE')
                or self.covered is not None and type(self.covered) is not bool
                or type(self.original_unit_slacks) is not tuple or len(self.original_unit_slacks) != 58):
            raise ValueError('matched coverage drops paired58 availability or its assigned model policy')
        for value in self.original_unit_slacks:
            if (value is not None) != (self.bound_kind == 'FINITE'):
                raise ValueError('matched coverage replaces a vacuous or unavailable bound with finite slack')
            if value is not None:
                validate_decimal(value, field_name='matched original-unit slack', minimum=Decimal(0))


def matched_coverage(unit, method, points, policy, outcome, usable):
    return matched_coverage_values(unit, method, points, policy, paired_factor_targets(outcome), usable)


def matched_coverage_values(unit, method, points, policy, targets, usable):
    """Apply the original sealed policy to authenticated paired raw targets."""
    if type(targets) is not tuple or len(targets) != 58 or type(usable) is not bool:
        raise ValueError('matched coverage requires all original paired58 targets and numerical usability')
    if type(policy) is not MatchedForecastPolicy or policy.method_key != method:
        raise TypeError('matched coverage requires its actual model-specific pre-future policy')
    policy.__post_init__()
    kind = policy.bound_kind if usable and all(value is not None for value in targets) else 'UNAVAILABLE'
    if kind == 'UNCALIBRATED':
        raise ValueError('matched confirmation coverage requires an actual calibrated policy')
    if kind == 'FINITE':
        raw = original_error_points(points)
        with localcontext() as context:
            context.prec = 60
            slacks = tuple(upper - point for upper, point in zip(policy.upper_errors, raw, strict=True))
        covered = all(target <= upper for target, upper in zip(targets, policy.upper_errors, strict=True))
    else:
        slacks, covered = (None,) * 58, True if kind == 'INFINITE' else None
    return MatchedCoverage(unit, method, kind, covered, slacks)


def matched_loss_readout(unit, point_menu, outcome, reasons, *, curve_primary=False):
    targets = paired_factor_targets(outcome)
    result = []
    for method in MATCHED_METHODS:
        try:
            points = original_error_points(point_menu[method])
            projection_reason = None
        except DecimalException:
            points, projection_reason = (None,) * 58, 'UNREPRESENTABLE_ORIGINAL_UNIT_PREDICTION'
        available = not reasons and all(value is not None for value in (*points, *targets))
        with localcontext() as context:
            context.prec = 60
            absolute = sum(abs(point - target) for point, target in zip(points, targets, strict=True)) / 58 if available else None
        result.append({'method': method, 'mean_absolute_error_paired58': absolute,
            'duration_error_count_over58': matched_duration_error_count(point_menu[method], targets) if not reasons else None})
        if curve_primary:
            from .curve_prediction import curve_loss
            result[-1]['normalized_root_curve_rms'] = curve_loss(point_menu[method], targets) if not reasons else None
        if projection_reason is not None:
            result[-1]['original_unit_projection_reason'] = projection_reason
    return {'unit_id': unit, 'methods': tuple(result), 'target_nonuse_reasons': reasons}


def complete_group_loss_summary(values):
    """Exact observed-group mean and inverse empirical 10/50/90% quantiles."""
    if type(values) is not tuple or any(value is not None and type(value) is not Fraction for value in values):
        raise TypeError('descriptive loss summaries require exact fractions and retained unknown groups')
    ordered = tuple(sorted(value for value in values if value is not None))
    def ratio(value):
        return value.numerator, value.denominator
    return {'observed_groups': len(ordered), 'unavailable_groups': len(values) - len(ordered),
        'mean_exact_ratio': ratio(sum(ordered, Fraction(0)) / len(ordered)) if ordered else None,
        'empirical_quantiles': tuple((numerator, denominator, ratio(ordered[max(0,
            (len(ordered) * numerator + denominator - 1) // denominator - 1)]) if ordered else None)
            for numerator, denominator in ((1, 10), (1, 2), (9, 10)))}


def matched_loss_summary(decisions):
    """Exact complete-case descriptive means and inverse empirical quantiles."""
    values = tuple(row.improvement_count for row in decisions if row.usable)
    def summary(counts):
        ordered = sorted(counts)
        return {'observed_units': len(ordered),
            'mean_numerator': sum(ordered) if ordered else None,
            'mean_denominator': 58 * len(ordered) if ordered else None,
            'empirical_quantiles': tuple((numerator, denominator,
                ordered[max(0, (len(ordered) * numerator + denominator - 1) // denominator - 1)] if ordered else None, 58)
                for numerator, denominator in ((1, 10), (1, 2), (9, 10)))}
    return {'scope': 'OBSERVED_COMMON_ROOTS_DESCRIPTIVE_NOT_POPULATION_MEAN_INFERENCE',
        'assigned_units': len(decisions), 'unknown_units': sum(not row.usable for row in decisions),
        'B0_minus_S0_duration_loss': summary(values),
        'absolute_duration_loss': tuple((method, summary(tuple(dict(row.duration_error_counts)[method]
            for row in decisions if row.usable and dict(row.duration_error_counts)[method] is not None))) for method in MATCHED_METHODS)}


def admission_risk(unit_ids, admissions, adequacy):
    """One fixed policy/query: unknown admitted targets count as failures in U95."""
    if (type(unit_ids) is not tuple or unit_ids != tuple(sorted(set(unit_ids))) or not unit_ids
            or type(admissions) is not tuple or type(adequacy) is not tuple
            or len(admissions) != len(unit_ids) or len(adequacy) != len(unit_ids)
            or any(value is not None and type(value) is not bool for value in (*admissions, *adequacy))):
        raise ValueError('admission risk requires the complete assigned whole-unit policy and outcome roster')
    admitted = tuple(unit for unit, decision in zip(unit_ids, admissions, strict=True) if decision is True)
    failed = tuple(unit for unit, decision, outcome in zip(unit_ids, admissions, adequacy, strict=True)
        if decision is True and outcome is False)
    unknown = tuple(unit for unit, decision, outcome in zip(unit_ids, admissions, adequacy, strict=True)
        if decision is True and outcome is None)
    assessed = len(admitted) - len(unknown)
    complete_interval = binomial_probability_interval(assessed, len(failed), tail_probability=Fraction(1, 40))
    bound = (binomial_probability_interval(len(admitted), len(failed) + len(unknown), tail_probability=Fraction(1, 20)).upper
        if admitted else None)
    return {'assigned_units': len(unit_ids), 'unit_ids': unit_ids, 'admitted_unit_ids': admitted,
        'refused_unit_ids': tuple(unit for unit, decision in zip(unit_ids, admissions, strict=True) if decision is False),
        'unknown_admission_unit_ids': tuple(unit for unit, decision in zip(unit_ids, admissions, strict=True) if decision is None),
        'known_admitted_failure_unit_ids': failed, 'unknown_admitted_outcome_unit_ids': unknown,
        'admitted_units': len(admitted), 'assessed_admitted_units': assessed, 'unresolved_admitted_units': len(unknown),
        'observed_admitted_failures': len(failed), 'observed_admitted_adequate': assessed - len(failed),
        'descriptive95_complete_case_failure_probability': complete_interval,
        'upper95_worst_case_failure_probability': bound,
        'bound_kind': 'UNDEFINED_NO_ADMISSIONS' if not admitted else 'CONDITIONAL_RISK_REQUIRES_SAMPLING_ASSUMPTION',
        'coverage_numerator': len(admitted), 'coverage_denominator': len(unit_ids)}


def matched_admission_risk(forecasts, outcomes):
    fs = {row.feature.unit_id: row for row in forecasts}
    ys = {row.unit_id: row for row in outcomes}
    units = tuple(sorted(fs))
    if not units or set(fs) != set(ys) or len(fs) != len(forecasts) or len(ys) != len(outcomes):
        raise ValueError('matched admission risk drops or duplicates assigned whole roots')
    durations = {}
    for unit in units:
        outcome = ys[unit]
        targets = tuple(outcome.view(view).errors for view in ('primary', 'fine'))
        usable = outcome.numerical_disposition == 'SATISFIED' and all(
            left is None or right is None or abs(left - right) <= Decimal('.0001')
            for left, right in zip(*targets, strict=True))
        durations[unit] = tuple(MatrixSampledResponseDuration(values, Decimal('.01'), usable,
            tuple(value is not None for value in values)) for values in targets)
    result = []
    for method in ('B0', 'S0'):
        for index, horizon in enumerate(DENSE_RESPONSE_HORIZONS):
            admissions = tuple(next(row for row in fs[unit].policies if row.method_key == method).admissions[index] for unit in units)
            adequacy = tuple(paired_adequacy(durations[unit], horizon_tick=horizon) for unit in units)
            result.append({'method': method, 'horizon_tick': horizon, 'tolerance': Decimal('.01'),
                **admission_risk(units, admissions, adequacy)})
    return tuple(result)
