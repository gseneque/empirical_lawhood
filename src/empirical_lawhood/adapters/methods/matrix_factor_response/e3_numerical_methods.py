# SPDX-License-Identifier: MPL-2.0
"""Original E3 numerical bodies shared after owning source/custody guards.

These helpers receive already checked observations. They establish no source
eligibility, chronology, IID/exchangeability, qualification or authority.
Canonical records and their scientific validators remain with their callers.
"""

from decimal import Decimal, localcontext

from empirical_lawhood.runtime.experimental_statistics import (
    fit_standardized_ridge, predict_standardized_ridge, raw_median,
)

from .response_error_prediction import FEATURE_BLOCKS


def log_error(value):
    with localcontext() as context:
        context.prec = 50
        return (Decimal(1) + value).ln()


def original_units(log_value):
    with localcontext() as context:
        context.prec = 50
        return log_value.exp() - Decimal(1)


def outcome_reasons(specification, outcome):
    reasons = []
    if outcome.numerical_disposition != "SATISFIED":
        reasons.append("NUMERICAL_" + outcome.numerical_disposition)
    primary, fine = outcome.view("primary"), outcome.view("fine")
    for left, right, left_tag, right_tag in zip(primary.errors, fine.errors, primary.dispositions, fine.dispositions, strict=True):
        if left is None or right is None:
            reasons.extend(tag for tag in (left_tag, right_tag) if tag != "FINITE")
        elif abs(left-right) > specification.measurement.target_discrepancy_tolerance:
            reasons.append("TARGET_VIEW_DISCREPANCY")
    return tuple(sorted(set(reasons)))


def fit_estimator_values(specification, roots, fs, ys):
    """TRAIN PRIMARY labels, original masks/standardization and raw median."""
    available = tuple(root for root in roots if fs[root].disposition == "AVAILABLE")
    models = []
    for selection in specification.methods:
        names = tuple(sorted(name for block in selection.feature_blocks for name in FEATURE_BLOCKS[block]))
        feature_rows = tuple(tuple(dict(fs[root].values)[name] for name in names) for root in available)
        parameters, constants, counts = [], [], []
        for index in range(15):
            raw = tuple(ys[root].view("primary").errors[index] if not outcome_reasons(specification, ys[root]) else None
                for root in (roots if selection.method_key == "RAW_TRAIN_MEDIAN" else available))
            if selection.method_key == "RAW_TRAIN_MEDIAN":
                finite = tuple(value for value in raw if value is not None)
                constants.append(raw_median(finite) if finite else None)
                parameters.append(None)
                counts.append(len(finite))
            else:
                labels = tuple(log_error(value) if value is not None else None for value in raw)
                parameter = fit_standardized_ridge(feature_rows, labels, penalty=selection.ridge_lambda,
                    penalize_intercept=selection.penalize_intercept) if feature_rows else None
                parameters.append(parameter)
                constants.append(None)
                counts.append(0 if parameter is None else parameter.fitted_rows)
        models.append((selection.method_key, names, tuple(parameters), tuple(constants), roots, tuple(counts)))
    return tuple(models)


def forecast_point_values(models, feature):
    """Original zero clip and within-description cumulative maxima."""
    from .matched_response_fitting import MatchedEstimatorModel, MatchedCurveEstimatorModel, forecast_matched_models
    if models and type(models[0]) in (MatchedEstimatorModel, MatchedCurveEstimatorModel):
        return forecast_matched_models(models, feature)
    points = []
    for model in models:
        raw = []
        for index in range(15):
            if feature.disposition != "AVAILABLE":
                value = None
            elif model.method_key == "RAW_TRAIN_MEDIAN":
                value = None if model.raw_constants[index] is None else log_error(model.raw_constants[index])
            else:
                parameter = model.ridge_parameters[index]
                value = None if parameter is None else predict_standardized_ridge(parameter,
                    tuple(dict(feature.values)[name] for name in model.feature_names))
            raw.append(value)
        cumulative = []
        for start in range(0, 15, 3):
            prior, missing = Decimal(0), False
            for value in raw[start:start+3]:
                missing = missing or value is None
                if missing:
                    cumulative.append(None)
                else:
                    prior = max(prior, value)
                    cumulative.append(prior)
        points.append((model.method_key, tuple(cumulative)))
    return tuple(points)


def fit_matched_estimator_values(specification, roots, fs, ys):
    """The protected caller has already authenticated the complete TRAIN bank."""
    from .matched_response_fitting import MatchedTrainingRow, fit_matched_models
    from .matched_response_prediction import MATCHED_FEATURE_BLOCKS, paired_factor_targets, validate_matched_features
    rows = []
    for unit in roots:
        feature, outcome = fs[unit], ys[unit]
        validate_matched_features(feature.values, feature.disposition, curve_primary=specification.is_curve_primary)
        reasons = set(outcome_reasons(specification, outcome))
        if feature.disposition != 'AVAILABLE':
            reasons.add(feature.disposition)
        rows.append(MatchedTrainingRow(unit, unit, 'NOMINAL', feature.values,
            paired_factor_targets(outcome), tuple(sorted(reasons))))
    return fit_matched_models(tuple(rows), assigned_groups=roots,
        folds=tuple((unit, index % 2) for index, unit in enumerate(roots)),
        method_features=tuple((selection.method_key,
            tuple(sorted(name for block in selection.feature_blocks for name in MATCHED_FEATURE_BLOCKS[block])))
            for selection in specification.methods), curve_primary=specification.is_curve_primary)


def calibration_score(specification, log_points, outcome, reasons):
    """Selected paired-view endpoint max followed by one complete max15 score."""
    reasons = list(reasons)
    primary, fine = outcome.view("primary"), outcome.view("fine")
    residuals = []
    for index, point in enumerate(dict(log_points)["SPECTRAL_RIDGE"]):
        labels = (primary.errors[index],) if specification.calibration_target_view == "PRIMARY" else (primary.errors[index], fine.errors[index])
        if point is None or any(label is None for label in labels):
            reasons.append("MISSING_POINT_OR_TARGET")
        else:
            with localcontext() as context:
                context.prec = 50
                residuals.append(max(Decimal(0), log_error(max(labels)) - point))
    return None if reasons else max(residuals), tuple(sorted(set(reasons))) if reasons else ("FINITE_WHOLE_UNIT_MAX15",)


def matched_calibration_value(points, outcome, reasons):
    from .matched_response_prediction import matched_calibration_score, paired_factor_targets
    value = matched_calibration_score(points, paired_factor_targets(outcome))
    reasons = set(reasons)
    if value is None:
        reasons.add('MISSING_POINT_OR_TARGET')
    return (None, tuple(sorted(reasons))) if reasons else (value, ('FINITE_WHOLE_UNIT_MAX58',))


def paired_root_decision(specification, point_menu, outcome, primary_index, reasons):
    reasons = list(reasons)
    comparisons = []
    for baseline in ("ALL_ORIGIN_RIDGE", "RAW_TRAIN_MEDIAN"):
        for view_id in ("fine", "primary"):
            target = outcome.view(view_id).errors[primary_index]
            candidate, control = point_menu["SPECTRAL_RIDGE"][primary_index], point_menu[baseline][primary_index]
            improvement = None
            if target is None or candidate is None or control is None:
                reasons.append("MISSING_PAIRED_COMPARISON")
            else:
                with localcontext() as context:
                    context.prec = 50
                    improvement = abs(target-original_units(control)) - abs(target-original_units(candidate))
            comparisons.append((baseline, view_id, improvement))
    usable = not reasons
    success = usable and all(value is not None and value > specification.assessment.improvement_margin for _, _, value in comparisons)
    if usable and not success:
        reasons.append("STRICT_PAIRED_MARGIN_NOT_MET")
    return usable, success, tuple(comparisons), tuple(sorted(set(reasons))) if reasons else ("PAIRED_SUCCESS",)


def coverage_values(point_menu, outcome, radius_kind, radius, usable):
    slacks, covered, available = [], usable, True
    for index, point in enumerate(point_menu["SPECTRAL_RIDGE"]):
        labels = tuple(view.errors[index] for view in outcome.views)
        if point is None or any(value is None for value in labels):
            slacks.append(None)
            covered = False
            available = False
        elif radius_kind == "INFINITE":
            slacks.append(None)
        else:
            with localcontext() as context:
                context.prec = 50
                upper = original_units(point+radius)
                slacks.append(upper-original_units(point))
                covered = covered and max(labels) <= upper
    return covered, tuple(slacks), radius_kind if available else "UNAVAILABLE"
