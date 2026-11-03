# SPDX-License-Identifier: MPL-2.0
"""Common whole-group, paired58 ridge fitting after owning custody checks.

This numerical owner has no acquisition, source selection or authority effects.
Every fit uses only its fitting groups, including its centring and scaling.
"""
from dataclasses import dataclass, field
from decimal import Decimal, localcontext
from fractions import Fraction
from typing import ClassVar

import numpy as np

from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_decimal, validate_stable_id
from empirical_lawhood.runtime.experimental_statistics import raw_median
from .matched_response_prediction import matched_duration_error_count, postprocess_log_points
from .curve_contract import MECHANISM_FEATURES
from .curve_prediction import curve_loss, group_curve_loss
from .curve_duration import CurveDurationDiagnostic, duration_diagnostic

PENALTIES = (Decimal(1), Decimal(10))
SOLVER = 'FLOAT64_WEIGHTED_CENTERED_THIN_SVD_RANK_EPS_MAX_SHAPE_NO_INTERCEPT_PENALTY'


class MatchedNumericalError(ValueError):
    """A declared numerical operation failed after contract validation."""


def _ids(values):
    if type(values) is not tuple or not values or values != tuple(sorted(set(values))):
        raise ValueError('matched fit requires an exact sorted whole-group census')
    for value in values:
        validate_stable_id(value)


def _decimals(values, *, length, nonnegative=False):
    if type(values) is not tuple or len(values) != length:
        raise ValueError('matched fit changes its declared numerical dimension')
    for value in values:
        validate_decimal(value, field_name='matched numerical value', minimum=Decimal(0) if nonnegative else None)


def _decimal(value):
    if not np.isfinite(value):
        raise MatchedNumericalError('matched ridge arithmetic is numerically unavailable')
    return Decimal(repr(float(value)))


@dataclass(frozen=True, slots=True)
class MatchedTrainingRow:
    """Received values only; callers retain and authenticate original records."""
    row_id: str
    group_id: str
    family_id: str
    features: tuple[tuple[str, Decimal], ...]
    errors: tuple[Decimal | None, ...]
    reasons: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class MatchedRidgeDiagnostics(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-experiment/matched-ridge-diagnostics'
    fitting_groups: tuple[str, ...]
    # Equal group mass 1 and equal coordinate mass within each whole group.
    row_groups: tuple[tuple[str, str, int], ...]
    penalty: Decimal
    means: tuple[Decimal, ...]
    scales: tuple[Decimal, ...]
    zero_variance_mask: tuple[bool, ...]
    design_rank: int
    coefficient_norms: tuple[Decimal, ...]
    effective_degrees_of_freedom: Decimal
    solver: str = SOLVER

    def __post_init__(self):
        _ids(self.fitting_groups)
        p = len(self.means)
        if (not p or not self.row_groups or self.solver != SOLVER or self.penalty not in PENALTIES
                or type(self.penalty) is not Decimal
                or tuple(row[0] for row in self.row_groups) != tuple(sorted({row[0] for row in self.row_groups}))
                or tuple(sorted({row[1] for row in self.row_groups})) != self.fitting_groups
                or type(self.zero_variance_mask) is not tuple or len(self.zero_variance_mask) != p
                or any(type(value) is not bool for value in self.zero_variance_mask)
                or type(self.design_rank) is not int or not 1 <= self.design_rank <= min(p + 1, len(self.row_groups))):
            raise ValueError('matched ridge diagnostics change the fit, weight, rank or solver contract')
        counts = {group: sum(row[1] == group for row in self.row_groups) for group in self.fitting_groups}
        for row, group, denominator in self.row_groups:
            validate_stable_id(row)
            if type(denominator) is not int or denominator != counts[group]:
                raise ValueError('matched fit fails equal whole-group and within-group weighting')
        _decimals(self.means, length=p)
        _decimals(self.scales, length=p, nonnegative=True)
        _decimals(self.coefficient_norms, length=58, nonnegative=True)
        validate_decimal(self.effective_degrees_of_freedom, field_name='ridge effective degrees of freedom', minimum=Decimal(1))
        if (any(scale <= 0 or constant and scale != 1 for scale, constant in zip(self.scales, self.zero_variance_mask, strict=True))
                or self.effective_degrees_of_freedom > p + 1):
            raise ValueError('matched ridge scale or effective degrees of freedom is invalid')


@dataclass(frozen=True, slots=True)
class MatchedRidgeParameters(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-experiment/matched-ridge-parameters'
    diagnostics: MatchedRidgeDiagnostics
    intercepts: tuple[Decimal, ...]
    # One 58-target row per standardized predictor; intercept is separate.
    coefficients: tuple[tuple[Decimal, ...], ...]

    def __post_init__(self):
        if type(self.diagnostics) is not MatchedRidgeDiagnostics:
            raise TypeError('matched parameters lack their exact fit diagnostics')
        self.diagnostics.__post_init__()
        _decimals(self.intercepts, length=58)
        if type(self.coefficients) is not tuple or len(self.coefficients) != len(self.diagnostics.means):
            raise ValueError('matched coefficients change their fixed feature order')
        for row in self.coefficients:
            _decimals(row, length=58)


@dataclass(frozen=True, slots=True)
class MatchedCrossValidationFit(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-experiment/matched-cross-validation-fit'
    held_out_fold: int
    diagnostics: MatchedRidgeDiagnostics
    # Exact sums of the two K errors across a group's coordinates, over 58*m.
    group_losses: tuple[tuple[str, int, int], ...]

    def __post_init__(self):
        if type(self.held_out_fold) is not int or self.held_out_fold not in (0, 1):
            raise ValueError('matched cross validation changes its frozen two-fold assignment')
        self.diagnostics.__post_init__()
        _ids(tuple(group for group, _, _ in self.group_losses))
        for group, numerator, denominator in self.group_losses:
            if (group in self.diagnostics.fitting_groups or type(numerator) is not int or type(denominator) is not int
                    or denominator < 58 or denominator % 58 or not 0 <= numerator <= denominator):
                raise ValueError('matched validation loss crosses a fitting group or changes its K denominator')


@dataclass(frozen=True, slots=True)
class MatchedCurveCrossValidationFit(CanonicalRecord):
    """New selection claim; exact group averages of precision-60 root RMS losses."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-experiment/matched-curve-cross-validation-fit'
    held_out_fold: int
    diagnostics: MatchedRidgeDiagnostics
    group_losses: tuple[tuple[str, int, int], ...]
    coordinate_losses: tuple[tuple[str, tuple[Decimal, ...]], ...]
    duration_error_counts: tuple[tuple[str, int, int], ...]
    duration_diagnostic: CurveDurationDiagnostic

    def __post_init__(self):
        if (type(self.held_out_fold) is not int or self.held_out_fold not in (0, 1)
                or type(self.diagnostics) is not MatchedRidgeDiagnostics):
            raise ValueError('curve cross validation changes its two folds or original ridge fit')
        self.diagnostics.__post_init__()
        if type(self.duration_diagnostic) is not CurveDurationDiagnostic:
            raise TypeError('curve validation requires its separately retained unselected K diagnostics')
        self.duration_diagnostic.__post_init__()
        groups = tuple(group for group, _, _ in self.group_losses)
        _ids(groups)
        if (tuple(group for group, _ in self.coordinate_losses) != groups
                or tuple(group for group, _, _ in self.duration_error_counts) != groups):
            raise ValueError('curve validation drops a coordinate or a secondary K result')
        for (group, numerator, denominator), (_, losses), (_, count, k_denominator) in zip(
                self.group_losses, self.coordinate_losses, self.duration_error_counts, strict=True):
            exact = group_curve_loss(losses)
            if (group in self.diagnostics.fitting_groups or exact is None
                    or type(numerator) is not int or type(denominator) is not int
                    or (numerator, denominator) != (exact.numerator, exact.denominator)
                    or type(count) is not int or type(k_denominator) is not int
                    or k_denominator != 58 * len(losses) or not 0 <= count <= k_denominator):
                raise ValueError('curve validation changes equal-coordinate loss or uses a fitting group')
        if (tuple(sorted({row[1] for row in self.duration_diagnostic.fitting_targets})) != self.diagnostics.fitting_groups
                or tuple(sorted({row[1] for row in self.duration_diagnostic.held_out_targets})) != groups
                or self.duration_diagnostic.group_errors(held_out=True, median=False)
                    != tuple((group, Fraction(n, d)) for group, n, d in self.duration_error_counts)):
            raise ValueError('curve validation substitutes its fitting-only median or diagnostic K predictions')


@dataclass(frozen=True, slots=True)
class MatchedFitAttempt(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-experiment/matched-fit-attempt'
    penalty: Decimal
    held_out_fold: int | None
    disposition: str
    diagnostics: MatchedRidgeDiagnostics | None

    def __post_init__(self):
        if (type(self.penalty) is not Decimal or self.penalty not in PENALTIES
                or self.held_out_fold is not None and (type(self.held_out_fold) is not int or self.held_out_fold not in (0, 1))
                or self.disposition not in ('FITTED', 'NUMERICALLY_UNEVALUABLE')
                or self.disposition == 'FITTED' and self.diagnostics is None):
            raise ValueError('matched fit attempt changes its frozen budget or numerical disposition')
        if self.diagnostics is not None:
            self.diagnostics.__post_init__()
            if self.diagnostics.penalty != self.penalty:
                raise ValueError('matched fit attempt changes its actual penalty')


@dataclass(frozen=True, slots=True)
class MatchedEstimatorModel(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-experiment/matched-estimator-model'
    CURVE_PRIMARY: ClassVar[bool] = False
    method_key: str
    feature_names: tuple[str, ...]
    training_unit_ids: tuple[str, ...]
    folds: tuple[tuple[str, int], ...]
    complete_group_ids: tuple[str, ...]
    exclusions: tuple[tuple[str, tuple[str, ...]], ...]
    prerequisite_reasons: tuple[str, ...]
    parameters: MatchedRidgeParameters | None
    cross_validation: tuple[MatchedCrossValidationFit, ...]
    raw_constants: tuple[Decimal | None, ...]
    fit_attempts: tuple[MatchedFitAttempt, ...] = ()

    def __post_init__(self):
        from .matched_response_prediction import MATCHED_METHODS, SHARED_FEATURES, STRUCTURAL_FEATURES, DRIFT_FEATURES
        if self.method_key not in (*MATCHED_METHODS, 'SR', 'BR', 'PHYSICAL', 'RELATION_BASE', 'RAW_DEV_MEDIAN'):
            raise ValueError('matched model changes its declared account')
        _ids(self.training_unit_ids)
        if (tuple(group for group, _ in self.folds) != self.training_unit_ids
                or any(type(fold) is not int or fold not in (0, 1) for _, fold in self.folds)
                or self.complete_group_ids != tuple(sorted(set(self.complete_group_ids)))
                or tuple(group for group, _ in self.exclusions) != tuple(sorted(set(self.training_unit_ids) - set(self.complete_group_ids)))
                or self.prerequisite_reasons != tuple(sorted(set(self.prerequisite_reasons)))
                or any(not reasons or reasons != tuple(sorted(set(reasons))) for _, reasons in self.exclusions)):
            raise ValueError('matched model drops assigned failures or changes its pre-outcome folds')
        if self.method_key in ('RAW_TRAIN_MEDIAN', 'RAW_DEV_MEDIAN'):
            if self.feature_names or self.parameters is not None or self.cross_validation or self.fit_attempts or len(self.raw_constants) != 58:
                raise ValueError('raw TRAIN median substitutes a feature fit')
            for value in self.raw_constants:
                if value is not None:
                    validate_decimal(value, field_name='raw TRAIN median', minimum=Decimal(0))
            if any((value is None) != (not self.complete_group_ids) for value in self.raw_constants):
                raise ValueError('raw TRAIN median drops its common complete training set')
            return
        _ids(self.feature_names)
        if self.method_key in ('S0', 'B0', 'SHARED_BASE'):
            expected = tuple(sorted((*SHARED_FEATURES,
                *(MECHANISM_FEATURES if self.CURVE_PRIMARY else ()),
                *(STRUCTURAL_FEATURES if self.method_key == 'S0' else DRIFT_FEATURES if self.method_key == 'B0' else ()))))
            if self.feature_names != expected:
                raise ValueError('matched account substitutes its declared common base or four-feature addition')
        if (self.raw_constants or bool(self.prerequisite_reasons) != (self.parameters is None)
                or type(self.fit_attempts) is not tuple or len(self.fit_attempts) > 5):
            raise ValueError('matched fitted account hides a training prerequisite or substitutes raw constants')
        attempted = tuple((row.penalty, row.held_out_fold) for row in self.fit_attempts)
        declared = tuple((penalty, fold) for penalty in PENALTIES for fold in (0, 1))
        if attempted[:4] != declared[:len(attempted[:4])]:
            raise ValueError('matched attempts add an undeclared fitting search or change fold order')
        for row in self.fit_attempts:
            row.__post_init__()
        successful_cv = tuple(row for row in self.fit_attempts if row.held_out_fold is not None and row.disposition == 'FITTED')
        if (tuple(row.diagnostics for row in successful_cv) != tuple(row.diagnostics for row in self.cross_validation)
                or any(row.disposition != 'FITTED' for row in self.fit_attempts[:-1])):
            raise ValueError('matched fitting hides a failed attempt or retries a numerical failure')
        for row in self.cross_validation:
            if type(row) is not (MatchedCurveCrossValidationFit if self.CURVE_PRIMARY else MatchedCrossValidationFit):
                raise TypeError('matched fit substitutes a validation loss from a different scientific claim')
            row.__post_init__()
            held = tuple(group for group, fold in self.folds if fold == row.held_out_fold and group in self.complete_group_ids)
            fitted = tuple(group for group in self.complete_group_ids if group not in held)
            if (tuple(group for group, _, _ in row.group_losses) != held or row.diagnostics.fitting_groups != fitted
                    or len(row.diagnostics.means) != len(self.feature_names)):
                raise ValueError('matched validation substitutes a group, fold or feature mask')
        if len(self.fit_attempts) == 5 and (self.fit_attempts[-1].held_out_fold is not None
                or self.fit_attempts[-1].penalty != selected_penalty(self.cross_validation)):
            raise ValueError('matched final fitting attempt changes its selected penalty or complete refit')
        if self.parameters is None:
            failed = self.fit_attempts and self.fit_attempts[-1].disposition == 'NUMERICALLY_UNEVALUABLE'
            if bool(failed) != ('NUMERICALLY_UNEVALUABLE' in self.prerequisite_reasons) or self.fit_attempts and not failed:
                raise ValueError('matched unavailable model loses its actual failed fitting attempt')
            return
        self.parameters.__post_init__()
        if (len(self.fit_attempts) != 5 or self.fit_attempts[-1].held_out_fold is not None
                or self.fit_attempts[-1].disposition != 'FITTED'
                or self.fit_attempts[-1].diagnostics != self.parameters.diagnostics
                or self.parameters.diagnostics.fitting_groups != self.complete_group_ids
                or len(self.parameters.diagnostics.means) != len(self.feature_names)
                or tuple((row.diagnostics.penalty, row.held_out_fold) for row in self.cross_validation)
                    != tuple((penalty, fold) for penalty in PENALTIES for fold in (0, 1))):
            raise ValueError('matched fitting exceeds five58 bundles or changes the common fitting set')
        if self.parameters.diagnostics.penalty != selected_penalty(self.cross_validation):
            raise ValueError('matched refit ignores its declared whole-group loss or the lower-penalty tie rule')

    @property
    def identity(self):
        from empirical_lawhood.kernel.provenance import ObjectIdentity
        return ObjectIdentity.from_record('matched-estimator.' + self.method_key.lower().replace('_', '-'), self)

    @property
    def finite_counts(self):
        # Kept as a report projection: all58 targets use one complete set.
        return (len(self.complete_group_ids) if self.parameters is not None or self.method_key in ('RAW_TRAIN_MEDIAN', 'RAW_DEV_MEDIAN') else 0,) * 58


@dataclass(frozen=True, slots=True)
class MatchedCurveEstimatorModel(MatchedEstimatorModel):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-experiment/matched-curve-estimator-model'
    CURVE_PRIMARY: ClassVar[bool] = True
    cross_validation: tuple[MatchedCurveCrossValidationFit, ...]
    duration_diagnostic: CurveDurationDiagnostic = field(kw_only=True)

    def __post_init__(self):
        MatchedEstimatorModel.__post_init__(self)
        if type(self.duration_diagnostic) is not CurveDurationDiagnostic:
            raise TypeError('curve model requires its TRAIN-only median and secondary duration diagnostics')
        self.duration_diagnostic.__post_init__()
        if (self.duration_diagnostic.held_out_targets
                or tuple(sorted({row[1] for row in self.duration_diagnostic.fitting_targets})) != self.complete_group_ids):
            raise ValueError('curve model duration diagnostic changes its original complete TRAIN groups')


def require_matched_model_reference(value):
    """Accept only an explicitly identified old-K or prospective-curve model."""
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    if (type(value) is not ObjectIdentity or (value.object_schema, value.object_version) not in
            tuple((kind.SCHEMA, kind.VERSION) for kind in (MatchedEstimatorModel, MatchedCurveEstimatorModel))):
        raise ValueError('matched forecast loses its exact old-K or prospective-curve model identity')
    value.__post_init__()


def _diagnostic_points(rows, parameters, names, constants=()):
    """Diagnostic prediction failures cannot change the primary fitted model."""
    result = {}
    for row in rows:
        try:
            if constants:
                with localcontext() as context:
                    context.prec = 60
                    points = postprocess_log_points(tuple((Decimal(1) + value).ln() for value in constants))
            else:
                points = None if parameters is None else predict_bundle(parameters, row.features, names)
        except (MatchedNumericalError, ArithmeticError):
            points = None
        result[row.row_id] = points
    return result


def selected_penalty(fits):
    def loss(penalty):
        losses = tuple(Fraction(n, d) for fit in fits if fit.diagnostics.penalty == penalty
            for _, n, d in fit.group_losses)
        return sum(losses, Fraction(0)) / len(losses)
    return min(PENALTIES, key=lambda penalty: (loss(penalty), penalty))


def fit_ridge_bundle(rows, feature_names, penalty):
    """One float64 SVD for all58 targets; weights sum to the group count."""
    if not rows or not feature_names or penalty not in PENALTIES:
        raise ValueError('matched ridge requires a nonempty complete fitting partition')
    groups = tuple(sorted({row.group_id for row in rows}))
    counts = {group: sum(row.group_id == group for row in rows) for group in groups}
    x = np.asarray([[float(dict(row.features)[name]) for name in feature_names] for row in rows], dtype=np.float64)
    with localcontext() as context:
        context.prec = 60
        y = np.asarray([[float((Decimal(1) + value).ln()) for value in row.errors] for row in rows], dtype=np.float64)
    weights = np.asarray([1 / counts[row.group_id] for row in rows], dtype=np.float64)
    if y.shape != (len(rows), 58):
        raise ValueError('matched fit changes its complete paired58 target dimensions')
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        raise MatchedNumericalError('matched fit has unrepresentable causal values or targets')
    means = np.average(x, axis=0, weights=weights)
    constant = np.ptp(x, axis=0) == 0
    means[constant] = x[0, constant]
    centered = x - means
    scales = np.sqrt(np.average(centered * centered, axis=0, weights=weights))
    scales[constant] = 1
    if not np.isfinite(scales).all() or np.any(scales <= 0):
        raise MatchedNumericalError('matched fold-local scaling is numerically unavailable')
    standardized = centered / scales
    intercepts = np.average(y, axis=0, weights=weights)
    design = np.sqrt(weights)[:, None] * standardized
    targets = np.sqrt(weights)[:, None] * (y - intercepts)
    try:
        left, singular, right = np.linalg.svd(design, full_matrices=False)
    except np.linalg.LinAlgError as error:
        raise MatchedNumericalError('matched ridge SVD is numerically unavailable') from error
    squared = singular * singular
    coefficients = right.T @ ((singular / (squared + float(penalty)))[:, None] * (left.T @ targets))
    rank_cutoff = np.finfo(np.float64).eps * max(design.shape) * singular[0]
    rank = 1 + int(np.count_nonzero(singular > rank_cutoff))
    diagnostics = MatchedRidgeDiagnostics(groups,
        tuple(sorted((row.row_id, row.group_id, counts[row.group_id]) for row in rows)), penalty,
        tuple(map(_decimal, means)), tuple(map(_decimal, scales)), tuple(map(bool, constant)),
        rank, tuple(map(_decimal, np.linalg.norm(coefficients, axis=0))),
        _decimal(1 + np.sum(squared / (squared + float(penalty)))))
    return MatchedRidgeParameters(diagnostics, tuple(map(_decimal, intercepts)),
        tuple(tuple(map(_decimal, row)) for row in coefficients))


def predict_bundle(parameters, feature_values, feature_names):
    values = dict(feature_values)
    x = np.asarray([float(values[name]) for name in feature_names], dtype=np.float64)
    if not np.isfinite(x).all():
        raise MatchedNumericalError('matched prediction has unrepresentable causal values')
    p = parameters.diagnostics
    standardized = (x - np.asarray(p.means, dtype=np.float64)) / np.asarray(p.scales, dtype=np.float64)
    predicted = np.asarray(parameters.intercepts, dtype=np.float64) + standardized @ np.asarray(parameters.coefficients, dtype=np.float64)
    return postprocess_log_points(tuple(map(_decimal, predicted)))


def fit_matched_models(rows, *, assigned_groups, folds, method_features, coordinates_per_group=1,
        minimum_complete_groups=48, minimum_per_fold=24, minimum_per_family=0, minimum_family_per_fold=0,
        curve_primary=False):
    """Fit every declared arm on one common complete group set, without redraws."""
    _ids(assigned_groups)
    if type(curve_primary) is not bool:
        raise TypeError('matched fitting requires an explicit old-duration or prospective-curve selection')
    if tuple(group for group, _ in folds) != assigned_groups or any(type(fold) is not int or fold not in (0, 1) for _, fold in folds):
        raise ValueError('matched fit needs its complete pre-outcome group/fold assignment')
    if (len({row.row_id for row in rows}) != len(rows) or tuple(sorted({row.group_id for row in rows})) != assigned_groups
            or coordinates_per_group not in (1, 9)):
        raise ValueError('matched fit cannot add, duplicate or omit assigned whole groups')
    required = {name for _, names in method_features for name in names}
    exclusions, complete = [], []
    families = {}
    for group in assigned_groups:
        members = tuple(row for row in rows if row.group_id == group)
        if len(members) != coordinates_per_group or len({row.family_id for row in members}) != 1:
            raise ValueError('matched fit loses the complete within-group coordinate or family census')
        families[group] = members[0].family_id
        reasons = set(reason for row in members for reason in row.reasons)
        for row in members:
            if (tuple(name for name, _ in row.features) != tuple(sorted({name for name, _ in row.features}))
                    or not required.issubset(dict(row.features))):
                reasons.add('MISSING_CAUSAL_FEATURE')
            if any(type(value) is not Decimal or not value.is_finite() for _, value in row.features):
                reasons.add('NONFINITE_CAUSAL_FEATURE')
            if len(row.errors) != 58:
                raise ValueError('matched fit thins its paired58 target census')
            if any(value is None or type(value) is not Decimal or not value.is_finite() or value < 0 for value in row.errors):
                reasons.add('MISSING_OR_UNUSABLE_TARGET')
        if reasons:
            exclusions.append((group, tuple(sorted(reasons))))
        else:
            complete.append(group)
    complete = tuple(complete)
    prerequisite = []
    if len(complete) < minimum_complete_groups:
        prerequisite.append('INSUFFICIENT_COMMON_COMPLETE_GROUPS')
    for fold in (0, 1):
        members = tuple(group for group, slot in folds if slot == fold and group in complete)
        if len(members) < minimum_per_fold:
            prerequisite.append('INSUFFICIENT_COMMON_COMPLETE_FOLD_' + str(fold))
        if any(sum(families[group] == family for group in members) < minimum_family_per_fold for family in set(families.values())):
            prerequisite.append('INSUFFICIENT_FAMILY_SUPPORT_FOLD_' + str(fold))
    if any(sum(families[group] == family for group in complete) < minimum_per_family for family in set(families.values())):
        prerequisite.append('INSUFFICIENT_COMMON_COMPLETE_FAMILY_SUPPORT')
    retained = tuple(sorted((row for row in rows if row.group_id in complete), key=lambda row: row.row_id))
    models = []
    for method, names in method_features:
        parameters, fits, constants, attempts = None, [], (), []
        reasons = list(prerequisite)
        if method in ('RAW_TRAIN_MEDIAN', 'RAW_DEV_MEDIAN'):
            constants = tuple(raw_median(tuple(row.errors[index] for row in retained)) if retained else None for index in range(58))
        elif not prerequisite:
            try:
                for penalty, fold in tuple((penalty, fold) for penalty in PENALTIES for fold in (0, 1)):
                    parameter = None
                    held = tuple(group for group, slot in folds if slot == fold and group in complete)
                    training = tuple(row for row in retained if row.group_id not in held)
                    parameter = fit_ridge_bundle(training, names, penalty)
                    losses, coordinate_losses, duration_counts, held_predictions = [], [], [], {}
                    for group in held:
                        members = tuple(row for row in retained if row.group_id == group)
                        predictions = tuple(predict_bundle(parameter, row.features, names) for row in members)
                        held_predictions.update((row.row_id, points) for row, points in zip(members, predictions, strict=True))
                        errors = tuple(matched_duration_error_count(points, row.errors)
                            for points, row in zip(predictions, members, strict=True))
                        if any(value is None for value in errors):
                            raise ValueError('complete matched validation has an unavailable K prediction')
                        duration_counts.append((group, sum(errors), 58 * len(members)))
                        if curve_primary:
                            rms = tuple(curve_loss(points, row.errors) for points, row in zip(predictions, members, strict=True))
                            loss = group_curve_loss(rms)
                            if loss is None:
                                raise ValueError('complete matched validation has an unavailable curve prediction')
                            coordinate_losses.append((group, rms))
                            losses.append((group, loss.numerator, loss.denominator))
                        else:
                            losses.append(duration_counts[-1])
                    fits.append(MatchedCurveCrossValidationFit(fold, parameter.diagnostics, tuple(losses),
                        tuple(coordinate_losses), tuple(duration_counts), duration_diagnostic(training,
                            tuple(row for row in retained if row.group_id in held),
                            fitting_points=_diagnostic_points(training, parameter, names), held_out_points=held_predictions)) if curve_primary else
                        MatchedCrossValidationFit(fold, parameter.diagnostics, tuple(losses)))
                    attempts.append(MatchedFitAttempt(penalty, fold, 'FITTED', parameter.diagnostics))
                penalty, fold, parameter = selected_penalty(fits), None, None
                parameters = fit_ridge_bundle(retained, names, penalty)
                attempts.append(MatchedFitAttempt(penalty, None, 'FITTED', parameters.diagnostics))
            except (MatchedNumericalError, ArithmeticError):
                attempts.append(MatchedFitAttempt(penalty, fold, 'NUMERICALLY_UNEVALUABLE',
                    None if parameter is None else parameter.diagnostics))
                reasons.append('NUMERICALLY_UNEVALUABLE')
        model_type = MatchedCurveEstimatorModel if curve_primary else MatchedEstimatorModel
        diagnostics = ({'duration_diagnostic': duration_diagnostic(retained, (),
            fitting_points=_diagnostic_points(retained, parameters, names, constants), held_out_points={})} if curve_primary else {})
        models.append(model_type(method, names, assigned_groups, folds, complete, tuple(exclusions),
            tuple(sorted(reasons)), parameters, tuple(fits), constants, tuple(attempts), **diagnostics))
    return tuple(models)


def forecast_matched_models(models, feature):
    points = []
    for model in models:
        if feature.disposition != 'AVAILABLE':
            values = (None,) * 58
        elif model.method_key in ('RAW_TRAIN_MEDIAN', 'RAW_DEV_MEDIAN'):
            with localcontext() as context:
                context.prec = 60
                values = postprocess_log_points(tuple(None if value is None else (Decimal(1) + value).ln() for value in model.raw_constants))
        elif model.parameters is None:
            values = (None,) * 58
        else:
            try:
                values = predict_bundle(model.parameters, feature.values, model.feature_names)
            except (MatchedNumericalError, ArithmeticError):
                values = (None,) * 58
        points.append((model.method_key, values))
    return tuple(points)
