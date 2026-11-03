# SPDX-License-Identifier: MPL-2.0
"""Frozen matched DEV relations and retained E4 error-curve prediction.

The original physical feature equation, sealed causal descriptors and shared
ridge solver remain their existing owners. Nothing here acquires observations,
changes the original accounts or grants scientific standing.
"""
from dataclasses import dataclass, replace
from decimal import Decimal, DecimalException, localcontext
from typing import ClassVar
from fractions import Fraction

from empirical_lawhood.adapters.methods.matrix_factor_response.configured_secondary_readout import (
    E4_HEADLINE_TOLERANCE, E4_OBSERVATION_HORIZONS, E4_PRIMARY_TIMESTEP,
)
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, canonical_value, validate_stable_id
from empirical_lawhood.runtime.experimental_statistics import (
    StandardizedRidgeParameters, fit_standardized_ridge, predict_standardized_ridge,
)
from .programme_selection import FEATURES, physical_grid_features
from empirical_lawhood.adapters.methods.matrix_factor_response.matched_response_prediction import (
    SHARED_FEATURES, STRUCTURAL_FEATURES as MATCHED_STRUCTURAL_FEATURES, DRIFT_FEATURES,
    validate_matched_features, postprocess_log_points, matched_calibration_score,
    matched_duration_error_count, matched_model_calibration,
    MatchedCoverage, matched_coverage_values,
    original_error_points,
)
from empirical_lawhood.adapters.methods.matrix_factor_response.matched_response_fitting import (
    MatchedEstimatorModel, MatchedCurveEstimatorModel, MatchedTrainingRow, fit_matched_models, forecast_matched_models,
)
from empirical_lawhood.adapters.methods.matrix_factor_response.curve_contract import MECHANISM_FEATURES, CURVE_RELATION_LOSS_RULE
from empirical_lawhood.adapters.methods.matrix_factor_response.curve_prediction import MatchedCurveDecision, curve_decision
from empirical_lawhood.adapters.simulators.six_matrix_response.history_preparation import FOUR_FAMILY_PREPARATION_IDS
from empirical_lawhood.kernel.serialization import validate_decimal

STRUCTURAL_FEATURES = ('associative-leakage', 'factor-fit-angle', 'lie-leakage', 'trailing-angle')
VIEWS = ('PRIMARY', 'FINE')
ENDPOINTS = len(VIEWS) * len(E4_OBSERVATION_HORIZONS)
ARMS = ('PHYSICAL', 'PHYSICAL_PLUS_STRUCTURE')

RELATION_FAMILY_CODING = tuple(zip(('family-de-anneal', 'family-x-first', 'family-y-first'),
    FOUR_FAMILY_PREPARATION_IDS[1:], strict=True))
RELATION_PHYSICAL_FEATURES = tuple(sorted(('x-temperature', 'x-friction', 'x-coupling',
    'pair.temperature-friction', 'pair.temperature-coupling', 'pair.friction-coupling', 'q-aggregate',
    *(name for name, _ in RELATION_FAMILY_CODING))))
_REPLACED_CONTEXT = ('bath-temperature', 'friction', 'cross-gamma', *(name for name, _ in RELATION_FAMILY_CODING))
RELATION_BASE_FEATURES = tuple(sorted((*(name for name in SHARED_FEATURES if name not in _REPLACED_CONTEXT),
    *RELATION_PHYSICAL_FEATURES)))
RELATION_METHOD_FEATURES = (
    ('BR', tuple(sorted((*RELATION_BASE_FEATURES, *DRIFT_FEATURES)))),
    ('PHYSICAL', RELATION_PHYSICAL_FEATURES), ('RAW_DEV_MEDIAN', ()), ('RELATION_BASE', RELATION_BASE_FEATURES),
    ('SR', tuple(sorted((*RELATION_BASE_FEATURES, *MATCHED_STRUCTURAL_FEATURES)))),
)
RELATION_METHODS = tuple(method for method, _ in RELATION_METHOD_FEATURES)
RELATION_SCORE_RULE = 'WHOLE_GROUP_MAX_POSITIVE_PAIRED_LOG_RESIDUAL_NINE_COORDINATES_FACTOR58'


@dataclass(frozen=True, slots=True)
class E4MatchedRelationTarget(CanonicalRecord):
    """The predeclared paired dense FACTOR target, independent of outcomes."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-selected-e4/matched-relation-target'
    target_id: str
    criterion: ObjectIdentity
    horizon_ticks: tuple[int, ...] = E4_OBSERVATION_HORIZONS
    numerical_views: tuple[str, ...] = VIEWS
    definition: str = 'CUMULATIVE_LOG1P_NORMALIZED_FACTOR_ERROR_PAIRED58'

    def __post_init__(self):
        from empirical_lawhood.adapters.methods.matrix_factor_response.response_frontier import MatrixResponseFrontierProtocol
        validate_stable_id(self.target_id)
        if (type(self.criterion) is not ObjectIdentity or self.criterion.object_schema != MatrixResponseFrontierProtocol.SCHEMA
                or self.criterion.object_version != MatrixResponseFrontierProtocol.VERSION
                or self.horizon_ticks != E4_OBSERVATION_HORIZONS or self.numerical_views != VIEWS
                or self.definition != 'CUMULATIVE_LOG1P_NORMALIZED_FACTOR_ERROR_PAIRED58'):
            raise ValueError('matched relation target changes its original criterion or paired dense FACTOR grid')
        self.criterion.__post_init__()

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.target_id, self)


@dataclass(frozen=True, slots=True)
class E4MatchedRelationSelection(CanonicalRecord):
    """Pre-outcome physical extension and matched relation estimator contract."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-selected-e4/matched-relation-selection'
    record_id: str
    nominal_temperature: Decimal
    nominal_friction: Decimal
    nominal_coupling: Decimal
    reference_family: str = FOUR_FAMILY_PREPARATION_IDS[0]
    feature_rule: str = 'LOG2_PHYSICAL_RATIOS_MAIN_PAIRS_MEAN_SQUARES_THREE_FIXED_FAMILY_INDICATORS'
    target: str = 'LOG1P_CUMULATIVE_FACTOR_ERROR_PRIMARY29_FINE29'
    minimum_complete_groups: int = 12
    minimum_complete_per_family: int = 2
    minimum_family_per_fold: int = 1
    fold_count: int = 2
    maximum_fit_calls_per_arm: int = 5
    penalties: tuple[Decimal, ...] = (Decimal(1), Decimal(10))
    target_discrepancy_tolerance: Decimal = Decimal('.0001')
    loss: str = 'MEAN_NINE_COORDINATE_PAIRED_K_ERROR_DIVIDED_BY_29'
    missing_policy: str = 'COMMON_COMPLETE_WHOLE_GROUPS_ASSIGNED_FAILURES_RETAINED_NO_REDRAW'

    def __post_init__(self):
        validate_stable_id(self.record_id)
        for value in (self.nominal_temperature, self.nominal_friction, self.nominal_coupling):
            validate_decimal(value, field_name='declared positive nominal physical value', minimum=Decimal(0))
            if value <= 0:
                raise ValueError('relation physical ratios require strictly positive nominal values')
        if (self.reference_family != FOUR_FAMILY_PREPARATION_IDS[0]
                or self.feature_rule != 'LOG2_PHYSICAL_RATIOS_MAIN_PAIRS_MEAN_SQUARES_THREE_FIXED_FAMILY_INDICATORS'
                or self.target != 'LOG1P_CUMULATIVE_FACTOR_ERROR_PRIMARY29_FINE29'
                or any(type(value) is not int for value in (self.minimum_complete_groups, self.minimum_complete_per_family,
                    self.minimum_family_per_fold, self.fold_count, self.maximum_fit_calls_per_arm))
                or (self.minimum_complete_groups, self.minimum_complete_per_family, self.minimum_family_per_fold,
                    self.fold_count, self.maximum_fit_calls_per_arm) != (12, 2, 1, 2, 5)
                or self.penalties != (Decimal(1), Decimal(10)) or any(type(value) is not Decimal for value in self.penalties)
                or type(self.target_discrepancy_tolerance) is not Decimal or self.target_discrepancy_tolerance != Decimal('.0001')
                or self.loss not in ('MEAN_NINE_COORDINATE_PAIRED_K_ERROR_DIVIDED_BY_29', CURVE_RELATION_LOSS_RULE)
                or self.missing_policy != 'COMMON_COMPLETE_WHOLE_GROUPS_ASSIGNED_FAILURES_RETAINED_NO_REDRAW'):
            raise ValueError('matched relation changes its declared transforms, common-group fit or paired target')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)

    @property
    def is_curve_primary(self):
        return self.loss == CURVE_RELATION_LOSS_RULE


def relation_method_features(selection):
    selection.__post_init__()
    return tuple((method, tuple(sorted((*names, *MECHANISM_FEATURES)))
        if selection.is_curve_primary and method not in ('PHYSICAL', 'RAW_DEV_MEDIAN') else names)
        for method, names in RELATION_METHOD_FEATURES)


def relation_physical_features(selection, factor_values, family_id):
    """A single case's declared controls, including off-grid E5/E6 values."""
    if type(selection) is not E4MatchedRelationSelection:
        raise TypeError('relation features require the original frozen physical extension')
    selection.__post_init__()
    if (type(factor_values) is not tuple or len(factor_values) != 3
            or family_id not in FOUR_FAMILY_PREPARATION_IDS):
        raise ValueError('relation features change their physical or four-family census')
    for value in factor_values:
        validate_decimal(value, field_name='declared physical value', minimum=Decimal(0))
        if value <= 0:
            raise ValueError('relation log ratios require positive physical controls')
    with localcontext() as context:
        context.prec = 60
        nominal = (selection.nominal_temperature, selection.nominal_friction, selection.nominal_coupling)
        x = tuple((value / center).ln() / Decimal(2).ln() for value, center in zip(factor_values, nominal, strict=True))
        values = dict(zip(('x-temperature', 'x-friction', 'x-coupling'), x, strict=True))
        values.update(zip(('pair.temperature-friction', 'pair.temperature-coupling', 'pair.friction-coupling'),
            (x[0] * x[1], x[0] * x[2], x[1] * x[2]), strict=True))
        values['q-aggregate'] = sum(value * value for value in x) / 3
    values.update((name, Decimal(family_id == family)) for name, family in RELATION_FAMILY_CODING)
    return tuple(sorted(values.items()))


def relation_feature_values(selection, causal_values, disposition, *, factor_values, family_id):
    """Replace duplicated physical/family inputs once; retain shared d_lin."""
    validate_matched_features(causal_values, disposition, curve_primary=selection.is_curve_primary)
    physical = relation_physical_features(selection, factor_values, family_id)
    if disposition != 'AVAILABLE':
        return ()
    values = dict(causal_values)
    if (tuple(values[name] for name in ('bath-temperature', 'friction', 'cross-gamma')) != factor_values
            or any(values[name] != value for name, value in physical if name.startswith('family-'))):
        raise ValueError('relation predictors substitute their actual single-case physical controls or family')
    return tuple(sorted((*(row for row in causal_values if row[0] not in _REPLACED_CONTEXT), *physical)))


@dataclass(frozen=True, slots=True)
class E4MatchedRelationFit(CanonicalRecord):
    """The fixed DEV fit; no CONF result selects or substitutes an account."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-selected-e4/matched-relation-fit'
    record_id: str
    selection: E4MatchedRelationSelection
    development: ObjectIdentity
    original_cases: tuple[ObjectIdentity, ...]
    models: tuple[MatchedEstimatorModel | MatchedCurveEstimatorModel, ...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if type(self.selection) is not E4MatchedRelationSelection or type(self.development) is not ObjectIdentity:
            raise TypeError('relation fit requires the exact declared mathematics and original DEV')
        self.selection.__post_init__()
        self.development.__post_init__()
        if (type(self.models) is not tuple or tuple(model.method_key for model in self.models) != RELATION_METHODS
                or any(type(model) is not (MatchedCurveEstimatorModel if self.selection.is_curve_primary else MatchedEstimatorModel)
                    for model in self.models)
                or type(self.original_cases) is not tuple or len(set(self.original_cases)) != len(self.original_cases)
                or len(self.original_cases) != 9 * len(self.models[0].training_unit_ids)):
            raise ValueError('relation fit drops its original nine-coordinate evidence or matched account menu')
        for value in self.original_cases:
            if type(value) is not ObjectIdentity:
                raise TypeError('relation fitting requires exact original case references')
            value.__post_init__()
        for model, (_, features) in zip(self.models, relation_method_features(self.selection), strict=True):
            model.__post_init__()
            if (model.feature_names != features or any(denominator != 9 for attempt in model.fit_attempts
                    if attempt.diagnostics is not None for _, _, denominator in attempt.diagnostics.row_groups)):
                raise ValueError('relation fit changes matched feature masks or equal within-group weights')
        if len({(model.training_unit_ids, model.folds, model.complete_group_ids, model.exclusions,
                tuple(reason for reason in model.prerequisite_reasons if reason != 'NUMERICALLY_UNEVALUABLE'))
                for model in self.models}) != 1:
            raise ValueError('relation accounts change the common complete whole-group set or folds')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)


def relation_target_reasons(errors, *, tolerance=Decimal('.0001')):
    """Numerical pairing remains a prerequisite, with no fabricated failure."""
    return (('PAIRED_TARGET_DISCREPANCY',) if any(left is not None and right is not None
        and abs(Fraction(left) - Fraction(right)) > Fraction(tolerance) for left, right in zip(errors[:29], errors[29:], strict=True)) else ())


def fit_relation_values(selection, development, rows, original_cases, *, assigned_groups, folds, record_id):
    """Owning callers authenticate case projections before this values-only fit."""
    selection.__post_init__()
    rows = tuple(replace(row, reasons=tuple(sorted(set((*row.reasons,
        *relation_target_reasons(row.errors, tolerance=selection.target_discrepancy_tolerance)))))) for row in rows)
    if set(row.family_id for row in rows) != set(FOUR_FAMILY_PREPARATION_IDS):
        raise ValueError('relation DEV must retain all four preassigned preparation families')
    models = fit_matched_models(rows, assigned_groups=assigned_groups, folds=folds,
        method_features=relation_method_features(selection), coordinates_per_group=9,
        minimum_complete_groups=selection.minimum_complete_groups, minimum_per_fold=4,
        minimum_per_family=selection.minimum_complete_per_family, minimum_family_per_fold=selection.minimum_family_per_fold,
        curve_primary=selection.is_curve_primary)
    return E4MatchedRelationFit(record_id, selection, development, original_cases, models)


def validate_relation_geometry(selection, programme):
    """The fixed nine-coordinate DEV geometry and nominal physical scales."""
    from .selected_e3_e4_records import SelectedE3E4DevelopmentProgramme
    if type(programme) is not SelectedE3E4DevelopmentProgramme or type(selection) is not E4MatchedRelationSelection:
        raise TypeError('matched relation fitting needs the original DEV and frozen physical selection')
    programme.__post_init__()
    selection.__post_init__()
    nominal = selection.nominal_temperature, selection.nominal_friction, selection.nominal_coupling
    if (tuple(factor.factor_id for factor in programme.factors) != ('temperature', 'friction', 'coupling')
            or tuple(factor.center for factor in programme.factors) != nominal
            or any(factor.scale != 'LOG' or factor.low * 2 != factor.center or factor.high != factor.center * 2
                for factor in programme.factors)):
        raise ValueError('matched relation changes its frozen log2 corner/center geometry')


def fit_relation(selection, programme, records, *, fold_slots, record_id):
    """Fit from the complete authenticated original DEV case projections."""
    validate_relation_geometry(selection, programme)
    by_root = {row.root_id: row for row in records}
    if (len(by_root) != len(records) or set(by_root) != {case.root_id for case in programme.cases}
            or any(type(row) is not E4StructuralPredictionCase for row in records)):
        raise ValueError('matched relation fitting changes the complete original assigned case census')
    rows, originals = [], []
    for case in programme.cases:
        row = by_root[case.root_id]
        row.__post_init__()
        if ((row.source, row.group_id, row.coordinate) != (case.source, case.independent_group_id, case.coordinate)
                or row.target_contract != 'MATCHED_FACTOR58'):
            raise ValueError('matched relation fitting substitutes source, group, coordinate or target')
        features = relation_feature_values(selection, row.matched_feature_values, row.feature_disposition,
            factor_values=case.factor_values, family_id=case.family_id)
        reasons = () if row.complete else tuple(sorted({
            *(() if row.feature_disposition == 'AVAILABLE' else ('CAUSAL_FEATURE_' + row.feature_disposition,)),
            *(() if all(row.cumulative_complete) else ('INCOMPLETE_PAIRED_TARGET',)),
            *(() if row.response_disposition in ('FINITE', 'PARTIAL') else ('RESPONSE_' + row.response_disposition,)),
        }))
        errors = tuple(value if complete else None for value, complete in
            zip(row.cumulative_errors, row.cumulative_complete, strict=True))
        rows.append(MatchedTrainingRow(row.root_id, row.group_id, case.family_id, features, errors, reasons))
        originals.append(row.original_case)
    folds = bind_group_fold_slots(programme, fold_slots, selection.fold_count)
    return fit_relation_values(selection, programme.identity, tuple(rows), tuple(originals),
        assigned_groups=programme.group_ids, folds=tuple((row.unit_id, row.fold) for row in folds), record_id=record_id)


def relation_point_values(fit, causal_values, disposition, *, factor_values, family_id):
    from types import SimpleNamespace
    fit.__post_init__()
    features = relation_feature_values(fit.selection, causal_values, disposition,
        factor_values=factor_values, family_id=family_id)
    return forecast_matched_models(fit.models, SimpleNamespace(values=features, disposition=disposition))


@dataclass(frozen=True, slots=True)
class E4RelationScoringCase(CanonicalRecord):
    """An authenticated case projection; coordinates never become IID units."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-selected-e4/relation-scoring-case'
    root_id: str
    group_id: str
    original_forecast: ObjectIdentity | None
    original_outcome: ObjectIdentity | None
    log_points: tuple[tuple[str, tuple[Decimal | None, ...]], ...]
    errors: tuple[Decimal | None, ...]
    reasons: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.root_id)
        validate_stable_id(self.group_id)
        if (tuple(method for method, _ in self.log_points) != RELATION_METHODS
                or self.reasons != tuple(sorted(set(self.reasons))) or len(self.errors) != 58):
            raise ValueError('relation scoring changes its complete declared case or paired58 target')
        for _, points in self.log_points:
            if postprocess_log_points(points) != points:
                raise ValueError('relation scoring substitutes an unprocessed prediction')
        for value in self.errors:
            if value is not None:
                validate_decimal(value, field_name='relation actual cumulative error', minimum=Decimal(0))
        for start in (0, 29):
            previous, missing = Decimal(0), False
            for value in self.errors[start:start + 29]:
                if value is None:
                    missing = True
                elif missing or value < previous:
                    raise ValueError('relation scoring changes cumulative target missingness or order')
                else:
                    previous = value
        for value in (self.original_forecast, self.original_outcome):
            if value is not None:
                if type(value) is not ObjectIdentity:
                    raise TypeError('relation scoring requires original scientific product references')
                value.__post_init__()
        if self.original_forecast is None and any(value is not None for _, points in self.log_points for value in points):
            raise ValueError('relation scoring invents an unsealed point prediction')
        if self.original_outcome is None and any(value is not None for value in self.errors):
            raise ValueError('relation scoring invents an unobserved native target')


def _relation_scoring_groups(cases, assigned_groups):
    if (type(assigned_groups) is not tuple or not assigned_groups
            or assigned_groups != tuple(sorted(set(assigned_groups)))
            or type(cases) is not tuple or any(type(row) is not E4RelationScoringCase for row in cases)
            or len({row.root_id for row in cases}) != len(cases)
            or {row.group_id for row in cases} != set(assigned_groups)):
        raise ValueError('relation scores require the complete assigned group and coordinate census')
    grouped = {group: tuple(row for row in cases if row.group_id == group) for group in assigned_groups}
    if any(len(rows) != 9 for rows in grouped.values()):
        raise ValueError('relation scoring retains all nine coordinates per assigned group')
    for row in cases:
        row.__post_init__()
    return grouped


def calibrate_relation_values(cases, *, assigned_groups):
    """Separate BR/SR maxima over all522 targets; missing groups score infinity."""
    grouped = _relation_scoring_groups(cases, assigned_groups)
    calibrations = []
    for method in ('BR', 'SR'):
        scores = []
        for group, rows in grouped.items():
            reasons = {reason for row in rows for reason in (*row.reasons, *relation_target_reasons(row.errors))}
            residuals = tuple(matched_calibration_score(dict(row.log_points)[method], row.errors) for row in rows)
            if any(value is None for value in residuals):
                reasons.add('MISSING_POINT_OR_TARGET')
            scores.append((group, None if reasons else max(residuals),
                tuple(sorted(reasons)) if reasons else ('FINITE_WHOLE_GROUP_MAX522',)))
        calibrations.append(matched_model_calibration(method, tuple(scores)))
    return tuple(calibrations)


@dataclass(frozen=True, slots=True)
class E4RelationGroupDecision(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-selected-e4/relation-group-decision'
    group_id: str
    root_ids: tuple[str, ...]
    duration_error_counts: tuple[tuple[str, int | None], ...]
    usable: bool
    success: bool
    reasons: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.group_id)
        values = dict(self.duration_error_counts)
        if (type(self.root_ids) is not tuple or len(self.root_ids) != 9 or self.root_ids != tuple(sorted(set(self.root_ids)))
                or tuple(values) != RELATION_METHODS or type(self.usable) is not bool or type(self.success) is not bool
                or any(value is not None and (type(value) is not int or not 0 <= value <= 522) for value in values.values())
                or self.usable and any(values[method] is None for method in ('BR', 'SR'))
                or self.success != (self.usable and values['BR'] - values['SR'] >= 18)
                or not self.reasons or self.reasons != tuple(sorted(set(self.reasons)))):
            raise ValueError('relation decision changes its nine-coordinate loss, assigned unit or exact1/29 margin')


def relation_group_decisions(cases, *, assigned_groups, curve_primary=False):
    if type(curve_primary) is not bool:
        raise TypeError('relation comparison requires its explicit old-duration or prospective-curve claim')
    grouped = _relation_scoring_groups(cases, assigned_groups)
    decisions = []
    for group, rows in grouped.items():
        losses = []
        reasons = {reason for row in rows for reason in (*row.reasons, *relation_target_reasons(row.errors))}
        if curve_primary:
            rows = tuple(sorted(rows, key=lambda row: row.root_id))
            decisions.append(curve_decision(group, tuple(dict(row.log_points) for row in rows),
                tuple(row.errors for row in rows), reasons, structural_method='SR',
                coordinate_ids=tuple(row.root_id for row in rows)))
            continue
        for method in RELATION_METHODS:
            values = tuple(matched_duration_error_count(dict(row.log_points)[method], row.errors) for row in rows)
            losses.append((method, None if any(value is None for value in values) else sum(values)))
        if any(dict(losses)[method] is None for method in ('BR', 'SR')):
            reasons.add('MISSING_PAIRED_DURATION_PREDICTION_OR_TARGET')
        usable = not reasons
        success = usable and dict(losses)['BR'] - dict(losses)['SR'] >= 18
        if usable:
            reasons.add('PAIRED_GROUP_DURATION_SUCCESS' if success else 'PAIRED_GROUP_DURATION_MARGIN_NOT_MET')
        decisions.append(E4RelationGroupDecision(group, tuple(sorted(row.root_id for row in rows)), tuple(losses),
            usable, success, tuple(sorted(reasons))))
    return tuple(decisions)


def relation_primary_inference(decisions):
    from fractions import Fraction
    from empirical_lawhood.runtime.experimental_statistics import assigned_binomial_inference
    return assigned_binomial_inference(tuple(row.group_id for row in decisions),
        tuple(row.success if row.usable else None for row in decisions),
        null_probability=Fraction(1, 2), alpha=Fraction(1, 160))


@dataclass(frozen=True, slots=True)
class E4RelationGroupCoverage(CanonicalRecord):
    """Nine case readouts with one whole-group coverage denominator."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-selected-e4/relation-group-coverage'
    group_id: str
    method_key: str
    cases: tuple[MatchedCoverage, ...]
    bound_kind: str
    covered: bool | None

    def __post_init__(self):
        validate_stable_id(self.group_id)
        if (self.method_key not in ('BR', 'SR') or type(self.cases) is not tuple or len(self.cases) != 9
                or any(type(row) is not MatchedCoverage or row.method_key != self.method_key for row in self.cases)
                or tuple(row.unit_id for row in self.cases) != tuple(sorted({row.unit_id for row in self.cases}))):
            raise ValueError('relation coverage changes the original nine-coordinate model census')
        for row in self.cases:
            row.__post_init__()
        kinds = {row.bound_kind for row in self.cases}
        if {'FINITE', 'INFINITE'} <= kinds:
            raise ValueError('relation group substitutes different original radii between matched coordinates')
        expected_kind = 'UNAVAILABLE' if 'UNAVAILABLE' in kinds else next(iter(kinds))
        expected_covered = None if expected_kind == 'UNAVAILABLE' else all(row.covered for row in self.cases)
        if self.bound_kind != expected_kind or self.covered is not expected_covered:
            raise ValueError('relation coverage changes complete-group availability or its all-coordinate event')


def relation_group_coverage(cases, forecasts, *, assigned_groups):
    grouped = _relation_scoring_groups(cases, assigned_groups)
    seals = {seal.case_id: seal for seal in forecasts}
    if len(seals) != len(forecasts) or set(seals) - {row.root_id for row in cases}:
        raise ValueError('relation coverage changes its actual original forecast census')
    result = []
    for group, rows in grouped.items():
        for method in ('BR', 'SR'):
            coverage = []
            for row in sorted(rows, key=lambda value: value.root_id):
                seal = seals.get(row.root_id)
                if seal is None:
                    value = MatchedCoverage(row.root_id, method, 'UNAVAILABLE', None, (None,) * 58)
                else:
                    seal.__post_init__()
                    if seal.identity != row.original_forecast or seal.relation_points != row.log_points:
                        raise ValueError('relation coverage substitutes an actual consumed point/upper-curve seal')
                    policy = next(value for value in seal.policies if value.method_key == method)
                    value = matched_coverage_values(row.root_id, method, dict(row.log_points)[method], policy,
                        row.errors, not row.reasons and not relation_target_reasons(row.errors))
                coverage.append(value)
            kinds = {row.bound_kind for row in coverage}
            kind = 'UNAVAILABLE' if 'UNAVAILABLE' in kinds else next(iter(kinds))
            result.append(E4RelationGroupCoverage(group, method, tuple(coverage), kind,
                None if kind == 'UNAVAILABLE' else all(row.covered for row in coverage)))
    return tuple(result)


def relation_loss_readout(cases, decisions):
    """Assigned-group descriptive K/error losses; no extra significance tests."""
    from empirical_lawhood.adapters.methods.matrix_factor_response.matched_response_prediction import complete_group_loss_summary as summary
    groups = tuple(row.group_id for row in decisions)
    grouped = _relation_scoring_groups(cases, groups)
    curve_primary = bool(decisions) and type(decisions[0]) is MatchedCurveDecision
    if decisions != relation_group_decisions(cases, assigned_groups=groups, curve_primary=curve_primary):
        raise ValueError('relation loss report substitutes its complete original scoring decisions')

    error_losses = []
    for decision in decisions:
        values, reasons = [], []
        for method in RELATION_METHODS:
            loss = None
            if decision.usable:
                try:
                    pairs = tuple((target, point) for row in grouped[decision.group_id]
                        for target, point in zip(row.errors, original_error_points(dict(row.log_points)[method]), strict=True))
                    if all(point is not None for _, point in pairs):
                        loss = sum((abs(Fraction(target) - Fraction(point)) for target, point in pairs), Fraction(0)) / 522
                except DecimalException:
                    reasons.append((method, 'UNREPRESENTABLE_ORIGINAL_UNIT_PREDICTION'))
            values.append((method, loss))
        error_losses.append((decision.group_id, tuple(values), tuple(reasons)))
    improvement = tuple(Fraction(dict(row.duration_error_counts)['BR'] - dict(row.duration_error_counts)['SR'], 522)
        if row.usable else None for row in decisions)
    return {'scope': 'OBSERVED_COMMON_GROUPS_DESCRIPTIVE_NO_POPULATION_MEAN_OR_CAUSAL_MEDIATION_CLAIM',
        'assigned_group_ids': groups, 'unknown_group_ids': tuple(row.group_id for row in decisions if not row.usable),
        'BR_minus_SR_duration_loss': summary(improvement),
        'absolute_duration_loss': tuple((method, summary(tuple(Fraction(dict(row.duration_error_counts)[method], 522)
            if row.usable and dict(row.duration_error_counts)[method] is not None else None for row in decisions)))
            for method in RELATION_METHODS),
        'mean_absolute_original_error_paired522': tuple((method, summary(tuple(dict(values)[method]
            for _, values, _ in error_losses))) for method in RELATION_METHODS),
        'BR_minus_SR_mean_absolute_error': summary(tuple(dict(values)['BR'] - dict(values)['SR']
            if dict(values)['BR'] is not None and dict(values)['SR'] is not None else None for _, values, _ in error_losses)),
        'original_unit_projection_failures': tuple((group, reasons) for group, _, reasons in error_losses if reasons),
        **({'curve_primary': _curve_loss_readout(decisions)} if curve_primary else {})}


def _curve_loss_readout(decisions):
    from empirical_lawhood.adapters.methods.matrix_factor_response.curve_prediction import curve_loss_summary
    return curve_loss_summary(decisions)


@dataclass(frozen=True, slots=True)
class E4StructuralPredictionSelection(CanonicalRecord):
    """One explicitly selected analysis; no estimator or target search."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-selected-e4/structural-prediction-selection'
    record_id: str
    physical_features: tuple[str, ...]
    structural_features: tuple[str, ...]
    descriptor_rule: str
    target: str
    penalties: tuple[Decimal, ...]
    fold_count: int
    maximum_fit_calls_per_arm: int
    loss: str
    missing_policy: str
    prediction_transform: str

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (self.physical_features != FEATURES or self.structural_features != STRUCTURAL_FEATURES
                or self.descriptor_rule != 'SEALED_PRIMARY_Y_ORIGINAL_PRE_CUTOFF_WINDOW_AND_CADENCE'
                or self.target != 'LOG1P_CUMULATIVE_FACTOR_ERROR_29_HORIZONS_EACH_PAIRED_VIEW'
                or type(self.penalties) is not tuple or any(type(value) is not Decimal for value in self.penalties)
                or self.penalties != (Decimal(1), Decimal(10))
                or type(self.fold_count) is not int or self.fold_count != 2
                or type(self.maximum_fit_calls_per_arm) is not int or self.maximum_fit_calls_per_arm != 5
                or self.loss != 'MEAN_WHOLE_GROUP_MSE_NINE_COORDINATES_PAIRED58_LOG_ENDPOINTS'
                or self.missing_policy != 'COMMON_COMPLETE_WHOLE_GROUPS_EXPLICIT_NO_POPULATION_INFERENCE'
                or self.prediction_transform != 'NONNEGATIVE_CUMULATIVE_MAXIMUM_WITHIN_EACH_VIEW'):
            raise ValueError('E4 structural prediction changes the frozen descriptors, target, folds, fit budget or loss')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)


def selected_structural_prediction(record_id):
    """Spell the owner-selected comparison in ordinary public input examples."""
    return E4StructuralPredictionSelection(record_id, FEATURES, STRUCTURAL_FEATURES,
        'SEALED_PRIMARY_Y_ORIGINAL_PRE_CUTOFF_WINDOW_AND_CADENCE',
        'LOG1P_CUMULATIVE_FACTOR_ERROR_29_HORIZONS_EACH_PAIRED_VIEW', (Decimal(1), Decimal(10)), 2, 5,
        'MEAN_WHOLE_GROUP_MSE_NINE_COORDINATES_PAIRED58_LOG_ENDPOINTS',
        'COMMON_COMPLETE_WHOLE_GROUPS_EXPLICIT_NO_POPULATION_INFERENCE',
        'NONNEGATIVE_CUMULATIVE_MAXIMUM_WITHIN_EACH_VIEW')


@dataclass(frozen=True, slots=True)
class E4StructuralPredictionCase(CanonicalRecord):
    """Small authenticated projection; unavailable values remain explicit."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-selected-e4/structural-prediction-case'
    VERSION: ClassVar[str] = "2.0.0"
    record_id: str
    original_case: ObjectIdentity
    source: ObjectIdentity
    root_id: str
    group_id: str
    coordinate: ObjectIdentity
    causal_account: ObjectIdentity | None
    causal_feature: ObjectIdentity | None
    feature_disposition: str
    feature_values: tuple[tuple[str, Decimal], ...]
    feature_window_ticks: int
    feature_cadence_ticks: int
    cutoff_tick: int
    response_disposition: str
    cumulative_errors: tuple[Decimal | None, ...]
    cumulative_complete: tuple[bool, ...]
    matched_feature_values: tuple[tuple[str, Decimal], ...] = ()
    physical_forecast: ObjectIdentity | None = None
    target_contract: str = "PAIRED15"

    def __post_init__(self):
        if self.target_contract not in ('PAIRED15', 'MATCHED_FACTOR58'):
            raise ValueError('E4 prediction case changes its original target contract')
        if self.target_contract == 'MATCHED_FACTOR58':
            validate_matched_features(self.matched_feature_values, self.feature_disposition)
            if (self.causal_account is None) != (self.physical_forecast is None):
                raise ValueError('matched E4 feature omits its original mechanical forecast')
            if self.physical_forecast is not None:
                self.physical_forecast.__post_init__()
        elif self.matched_feature_values or self.physical_forecast is not None:
            raise ValueError('closed E4 case invents amended matched features')
        for value in (self.record_id, self.root_id, self.group_id):
            validate_stable_id(value)
        for value in (self.original_case, self.source, self.coordinate):
            if type(value) is not ObjectIdentity:
                raise TypeError('structural prediction requires exact original identity references')
            value.__post_init__()
        if ((self.causal_account is None) != (self.causal_feature is None)
                or self.feature_disposition not in ('AVAILABLE', 'NO_CAUSAL_ORIGIN', 'UNAVAILABLE', 'REFUSED', 'UNOBSERVED')
                or (self.causal_account is None) != (self.feature_disposition == 'UNOBSERVED')
                or type(self.feature_values) is not tuple
                or (tuple(name for name, _ in self.feature_values) != STRUCTURAL_FEATURES
                    if self.feature_disposition == 'AVAILABLE' else bool(self.feature_values))
                or any(type(value) is not Decimal or not value.is_finite() or value < 0 for _, value in self.feature_values)
                or any(type(value) is not int or value <= 0 for value in
                    (self.feature_window_ticks, self.feature_cadence_ticks, self.cutoff_tick))
                or self.feature_cadence_ticks > self.feature_window_ticks
                or self.response_disposition not in ('FINITE', 'PARTIAL', 'NO_ORIGIN', 'UNEVALUABLE',
                    'NATIVE_CROSSCHECK_FAILED', 'INSTRUMENT_UNRESOLVED', 'UNKNOWN_CONTACT', 'UNAVAILABLE')
                or type(self.cumulative_errors) is not tuple or len(self.cumulative_errors) != ENDPOINTS
                or type(self.cumulative_complete) is not tuple or len(self.cumulative_complete) != ENDPOINTS
                or any(type(value) is not bool for value in self.cumulative_complete)
                or any(value is not None and (type(value) is not Decimal or not value.is_finite() or value < 0)
                    for value in self.cumulative_errors)
                or any(complete and value is None for complete, value in zip(self.cumulative_complete, self.cumulative_errors, strict=True))):
            raise ValueError('structural prediction drops its causal availability or complete paired dense target')
        for start in (0, len(E4_OBSERVATION_HORIZONS)):
            previous = None
            for value in self.cumulative_errors[start:start + len(E4_OBSERVATION_HORIZONS)]:
                if value is not None and previous is not None and value < previous:
                    raise ValueError('structural prediction reverses a cumulative observed error curve')
                if value is not None:
                    previous = value
        for value in (self.causal_account, self.causal_feature):
            if value is not None:
                if type(value) is not ObjectIdentity:
                    raise TypeError('structural prediction needs exact original sealed feature provenance')
                value.__post_init__()

    @property
    def complete(self):
        return (self.feature_disposition == 'AVAILABLE' and self.response_disposition in ('FINITE', 'PARTIAL')
            and all(self.cumulative_complete) and all(value is not None for value in self.cumulative_errors))


def prediction_case(bank, case, row, account):
    """Join the exact original pre-future account, never full-history features."""
    from .selected_e3_e4_records import SelectedE3E4AccountSeal
    from .selected_e4_native_records import SelectedE4ProtectedAccountSeal
    protocol = next(value for value in bank.response_selection.protocols
        if value.public_source.root.root_id == case.root_id)
    public = protocol.public_source
    measurement = bank.forecast_design.package.specification.measurement
    if ((account is None) != (case.forecast is None)
            or row.original_case != ObjectIdentity.from_record(case.root_id, case)
            or row.source != case.source or row.root_id != case.root_id or row.group_id != case.group_id
            or row.observation_horizons != E4_OBSERVATION_HORIZONS):
        raise PermissionError('structural prediction omits its actual original account or dense case')
    values, feature_pin, matched_values, physical_pin = (), None, (), None
    disposition = 'UNOBSERVED'
    if account is not None:
        if type(account) not in (SelectedE3E4AccountSeal, SelectedE4ProtectedAccountSeal):
            raise TypeError('structural prediction requires the actual original sealed account')
        account.__post_init__()
        feature = account.feature
        feature.__post_init__()
        if (account.identity != case.forecast or account.source != case.source
                or account.design != bank.forecast_design.identity or account.log_points != case.original_log_points
                or feature.source != public.source or feature.root_id != case.root_id
                or feature.independent_group_id != case.group_id
                or feature.clock_id != public.coordinate.clock_id
                or feature.cutoff != public.coordinate.physical_time(public.policy.cutoff_tick)
                or row.causal_prefix is not None and feature.prefix != row.causal_prefix):
            raise PermissionError('structural prediction substitutes original feature source, cutoff or seal')
        disposition = feature.disposition
        feature_pin = ObjectIdentity.from_record(feature.feature_id, feature)
        if getattr(measurement, "is_matched", False):
            matched_values, physical_pin = feature.values, feature.physical_forecast
            if physical_pin is None:
                raise PermissionError("matched E4 prediction omits the original mechanical feature dependency")
        if disposition == 'AVAILABLE':
            original = dict(feature.values)
            values = tuple((name, original[name]) for name in STRUCTURAL_FEATURES)
    indices = tuple((view * len(row.predictors) + row.predictors.index('FACTOR')) * len(E4_OBSERVATION_HORIZONS) + horizon
        for view in range(len(VIEWS)) for horizon in range(len(E4_OBSERVATION_HORIZONS)))
    return E4StructuralPredictionCase('structural-prediction.' + case.root_id, row.original_case, row.source,
        row.root_id, row.group_id, row.coordinate, None if account is None else account.identity,
        feature_pin, disposition, values, measurement.feature_window_ticks, measurement.feature_cadence_ticks,
        public.policy.cutoff_tick, row.disposition, tuple(row.errors[index] for index in indices),
        tuple(row.cumulative_complete[index] for index in indices), matched_values, physical_pin, case.target_contract)


def bind_group_fold_slots(programme, fold_slots, fold_count):
    """The same original whole-group assignment for revision and comparison."""
    from empirical_lawhood.kernel.experimental_selection import WholeUnitFold
    groups = {}
    for case in programme.cases:
        groups.setdefault(case.family_id, set()).add(case.independent_group_id)
    slots = {(family, ordinal): group for family, values in groups.items()
        for ordinal, group in enumerate(sorted(values))}
    if (len(fold_slots) != len(slots) or set(slots) != {(family, ordinal) for family, ordinal, _ in fold_slots}
            or {fold for _, _, fold in fold_slots} != set(range(fold_count))):
        raise ValueError('programme folds omit or add an original C whole group')
    return tuple(sorted((WholeUnitFold(slots[family, ordinal], fold)
        for family, ordinal, fold in fold_slots), key=lambda row: row.unit_id))


@dataclass(frozen=True, slots=True)
class E4StructuralPredictionModel(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-selected-e4/structural-prediction-model'
    record_id: str
    selection: ObjectIdentity
    development: ObjectIdentity
    arm: str
    feature_names: tuple[str, ...]
    penalty: Decimal
    training_groups: tuple[str, ...]
    parameters: tuple[StandardizedRidgeParameters, ...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        names = FEATURES if self.arm == 'PHYSICAL' else tuple(sorted((*FEATURES, *STRUCTURAL_FEATURES)))
        if (self.arm not in ARMS or self.feature_names != names
                or type(self.penalty) is not Decimal or self.penalty not in (Decimal(1), Decimal(10))
                or type(self.training_groups) is not tuple or not self.training_groups
                or self.training_groups != tuple(sorted(set(self.training_groups)))
                or type(self.parameters) is not tuple or len(self.parameters) != ENDPOINTS
                or any(type(row) is not StandardizedRidgeParameters or row.coefficients is None
                    or len(row.coefficients) != len(names) + 1 or row.training_rows != 9 * len(self.training_groups)
                    or row.fitted_rows != row.training_rows for row in self.parameters)):
            raise ValueError('structural model changes its exact paired bundle, physical arm or whole training groups')
        for value in (self.selection, self.development):
            if type(value) is not ObjectIdentity:
                raise TypeError('structural model lacks its frozen analysis or original DEV identity')
            value.__post_init__()
        for value in self.parameters:
            value.__post_init__()

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)


def _rows(programme, records):
    from .selected_e3_e4_records import SelectedE3E4DevelopmentProgramme
    from .selected_e4_programme import SelectedE4PhaseProgramme
    if type(programme) not in (SelectedE3E4DevelopmentProgramme, SelectedE4PhaseProgramme):
        raise TypeError('structural comparison requires the actual original DEV, CAL or CONF programme')
    programme.__post_init__()
    records = tuple(records)
    if any(type(row) is not E4StructuralPredictionCase for row in records):
        raise TypeError('structural comparison requires actual typed original case projections')
    by_root = {row.root_id: row for row in records}
    if len(by_root) != len(records) or set(by_root) != {case.root_id for case in programme.cases}:
        raise ValueError('structural comparison changes its complete assigned case denominator')
    groups, features, targets = {}, {}, {}
    for case in programme.cases:
        row = by_root[case.root_id]
        row.__post_init__()
        if row.source != case.source or row.group_id != case.independent_group_id or row.coordinate != case.coordinate:
            raise ValueError('structural comparison substitutes original source, independent group or coordinate')
        groups.setdefault(row.group_id, []).append(row)
        features[row.root_id] = {**physical_grid_features(programme.factors, case.factor_values), **dict(row.feature_values)}
        targets[row.root_id] = (tuple((Decimal(1) + value).ln() for value in row.cumulative_errors)
            if row.complete else None)
    if set(groups) != set(programme.group_ids) or any(len(rows) != 9 for rows in groups.values()):
        raise ValueError('structural comparison requires complete original nine-coordinate whole groups')
    complete = tuple(group for group in programme.group_ids if all(row.complete for row in groups[group]))
    return by_root, groups, features, targets, complete


def _fit(selection, programme, arm, penalty, groups, features, targets, suffix):
    names = FEATURES if arm == 'PHYSICAL' else tuple(sorted((*FEATURES, *STRUCTURAL_FEATURES)))
    cases = tuple(case for case in programme.cases if case.independent_group_id in groups)
    x = tuple(tuple(features[case.root_id][name] for name in names) for case in cases)
    parameters = tuple(fit_standardized_ridge(x, tuple(targets[case.root_id][index] for case in cases),
        penalty=penalty, penalize_intercept=False) for index in range(ENDPOINTS))
    return E4StructuralPredictionModel('model.structural.' + arm.lower().replace('_', '-') + '.' + suffix,
        selection.identity, programme.identity, arm, names, penalty, tuple(sorted(groups)), parameters)


def _predict(model, features):
    values = tuple(features[name] for name in model.feature_names)
    raw = tuple(predict_standardized_ridge(parameters, values) for parameters in model.parameters)
    result = []
    for view in range(len(VIEWS)):
        maximum = Decimal(0)
        for value in raw[view * len(E4_OBSERVATION_HORIZONS):(view + 1) * len(E4_OBSERVATION_HORIZONS)]:
            if value is None:
                raise ValueError('structural model has an unavailable fitted endpoint')
            maximum = max(maximum, value)
            result.append(maximum)
    return tuple(result)


def _group_loss(rows, model, features, targets):
    losses = []
    for row in rows:
        predicted = _predict(model, features[row.root_id])
        losses.extend((actual - point) ** 2 for actual, point in zip(targets[row.root_id], predicted, strict=True))
    return sum(losses, Decimal(0)) / len(losses)


def _tau(values):
    threshold = (Decimal(1) + E4_HEADLINE_TOLERANCE).ln()
    result = []
    for index, view in enumerate(VIEWS):
        curve = values[index * len(E4_OBSERVATION_HORIZONS):(index + 1) * len(E4_OBSERVATION_HORIZONS)]
        failure = next((horizon for horizon, value in zip(E4_OBSERVATION_HORIZONS, curve, strict=True)
            if value > threshold), None)
        result.append({'view': view, 'first_predicted_strict_exceedance': failure,
            'predicted_time': None if failure is None else failure * E4_PRIMARY_TIMESTEP,
            'last_predicted_pass': max((horizon for horizon, value in zip(E4_OBSERVATION_HORIZONS, curve, strict=True)
                if value <= threshold), default=None),
            'classification': 'MODEL_PREDICTED_NO_EXCEEDANCE_WITHIN_GRID' if failure is None
                else 'MODEL_PREDICTED_FAILURE_BY_FIRST_CHECK' if failure == E4_OBSERVATION_HORIZONS[0]
                else 'MODEL_PREDICTED_SAMPLED_CROSSING',
            'observed_event_or_continuous_time_bound': False})
    return tuple(result)


def _evaluation(programme, records, model, phase):
    by_root, groups, features, targets, complete = _rows(programme, records)
    predictions, losses = [], []
    for case in programme.cases:
        row = by_root[case.root_id]
        available = model.arm == 'PHYSICAL' or row.feature_disposition == 'AVAILABLE'
        disposition = 'PREDICTED' if available else 'STRUCTURAL_FEATURE_UNAVAILABLE'
        try:
            values = _predict(model, features[row.root_id]) if available else None
        except (ValueError, ArithmeticError):
            values, disposition = None, 'NUMERICALLY_UNEVALUABLE'
        predictions.append({'root_id': row.root_id, 'group_id': row.group_id,
            'causal_feature': row.causal_feature, 'feature_disposition': row.feature_disposition,
            'prediction_disposition': disposition,
            'prediction': values, 'tau_0_01': None if values is None else _tau(values)})
    by_prediction = {row['root_id']: row['prediction'] for row in predictions}
    for group in complete:
        values = tuple(by_prediction[row.root_id] for row in groups[group])
        if all(value is not None for value in values):
            errors = tuple((actual - point) ** 2 for row, predicted in zip(groups[group], values, strict=True)
                for actual, point in zip(targets[row.root_id], predicted, strict=True))
            losses.append({'group_id': group, 'mse': sum(errors, Decimal(0)) / len(errors)})
    return {'phase': phase, 'scope': 'IN_SAMPLE_DEV_FIT' if phase == 'DEVELOPMENT' else 'HELD_OUT_DESCRIPTIVE_REPLAY',
        'programme': programme.identity, 'assigned_groups': len(groups), 'complete_common_groups': complete,
        'excluded_groups': tuple(group for group in programme.group_ids if group not in complete),
        'numerically_unscored_complete_groups': tuple(group for group in complete
            if group not in {row['group_id'] for row in losses}),
        'group_losses': tuple(losses), 'mean_group_mse': None if not losses else
            sum((row['mse'] for row in losses), Decimal(0)) / len(losses), 'predictions': tuple(predictions),
        'population_inference': 'NOT_ESTABLISHED_FROM_COMPLETE_CASES',
        'new_before_outcome_prediction_seal': False}


def structural_prediction_comparison(selection, revision_choices, development, records, *, evaluation=()):
    """Five bundle fits per arm at most; all fitting operands are DEV only.

    Each bundle has 58 endpoint regressions. CAL/CONF labels never enter fitting,
    standardization, candidate selection or the final DEV refit.
    """
    selection.__post_init__()
    revision_choices.__post_init__()
    if development.mode != 'E4_DEVELOPMENT' or revision_choices.fold_count != selection.fold_count:
        raise ValueError('structural comparison changes the original frozen revision folds')
    records, evaluation = tuple(records), tuple(evaluation)
    seen_groups, seen_roots, seen_phases = set(development.group_ids), {case.root_id for case in development.cases}, set()
    modes = {'CALIBRATION': 'E4_REVISION_CALIBRATION', 'CONFIRMATION': 'E4_CONFIRMATION'}
    for phase, programme, values in evaluation:
        if (phase not in modes or phase in seen_phases or programme.mode != modes[phase]
                or programme.factors != development.factors or programme.forecast_design != development.forecast_design
                or seen_groups.intersection(programme.group_ids)
                or seen_roots.intersection(case.root_id for case in programme.cases)):
            raise ValueError('structural comparison reuses DEV groups or changes held-out original phase mathematics')
        _rows(programme, values)
        seen_phases.add(phase)
        seen_groups.update(programme.group_ids)
        seen_roots.update(case.root_id for case in programme.cases)
    folds = bind_group_fold_slots(development, revision_choices.fold_slots, selection.fold_count)
    with localcontext() as context:
        context.prec = 80
        by_root, groups, features, targets, complete = _rows(development, records)
        fold_by_group = {row.unit_id: row.fold for row in folds}
        arms = []
        for arm in ARMS:
            candidates, attempts = [], []
            for penalty in selection.penalties:
                scores = []
                for fold in range(selection.fold_count):
                    training = tuple(group for group in complete if fold_by_group[group] != fold)
                    heldout = tuple(group for group in complete if fold_by_group[group] == fold)
                    if not training or not heldout:
                        scores.append({'fold': fold, 'status': 'INCOMPLETE_FOLD', 'training_groups': training,
                            'heldout_groups': heldout, 'group_losses': ()})
                        continue
                    attempt = {'purpose': 'CROSS_VALIDATION', 'penalty': penalty, 'fold': fold,
                        'training_groups': training, 'heldout_groups': heldout}
                    attempts.append(attempt)
                    try:
                        model = _fit(selection, development, arm, penalty, training, features, targets,
                            str(penalty) + '.fold-' + str(fold))
                        losses = tuple({'group_id': group, 'mse': _group_loss(groups[group], model, features, targets)}
                            for group in heldout)
                        scores.append({**attempt, 'status': 'SCORED', 'model': model.identity, 'group_losses': losses})
                    except (ValueError, ArithmeticError):
                        scores.append({**attempt, 'status': 'NUMERICALLY_UNEVALUABLE', 'group_losses': ()})
                valid = all(row['status'] == 'SCORED' for row in scores)
                losses = tuple(loss for row in scores for loss in row['group_losses'])
                candidates.append({'penalty': penalty, 'folds': tuple(scores),
                    'mean_group_mse': sum((row['mse'] for row in losses), Decimal(0)) / len(losses) if valid else None})
            selectable = tuple(row for row in candidates if row['mean_group_mse'] is not None)
            chosen = min(selectable, key=lambda row: (row['mean_group_mse'], row['penalty'])) if selectable else None
            final = None
            if chosen is not None:
                attempts.append({'purpose': 'FINAL_DEV_REFIT', 'penalty': chosen['penalty'], 'training_groups': complete})
                try:
                    final = _fit(selection, development, arm, chosen['penalty'], complete, features, targets,
                        development.fingerprint() + '.final')
                except (ValueError, ArithmeticError):
                    pass
            if len(attempts) > selection.maximum_fit_calls_per_arm:
                raise ValueError('structural comparison exceeded its frozen fitting budget')
            arms.append({'arm': arm, 'status': 'FITTED' if final is not None else 'NOT_ESTABLISHED',
                'candidates': tuple(candidates), 'fit_attempts': tuple(attempts), 'fit_calls': len(attempts),
                'endpoint_regressions_per_bundle': ENDPOINTS, 'final_model': final,
                'evaluation': () if final is None else tuple(_evaluation(programme, values, final, phase)
                    for phase, programme, values in (('DEVELOPMENT', development, records), *evaluation))})
        return canonical_value({'selection': selection.identity, 'development': development.identity,
            'scope': 'FROZEN_DESCRIPTIVE_PHYSICAL_VERSUS_PHYSICAL_PLUS_STRUCTURE',
            'assigned_groups': len(groups), 'complete_common_groups': complete,
            'excluded_groups': tuple({'group_id': group,
                'incomplete_roots': tuple(row.root_id for row in groups[group] if not row.complete)}
                for group in development.group_ids if group not in complete),
            'folds': folds, 'arms': tuple(arms),
            'tuning_scores': 'SELECTION_CROSS_VALIDATION_NOT_INDEPENDENT_FINAL_ASSESSMENT',
            'population_inference': 'NOT_ESTABLISHED_FROM_COMPLETE_CASES',
            'primary_tests_and_original_models': 'UNCHANGED',
            'before_outcome_prediction_seal': 'NOT_CLAIMED_BY_DESCRIPTIVE_REPLAY'})
