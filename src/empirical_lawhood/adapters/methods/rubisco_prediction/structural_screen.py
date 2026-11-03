# SPDX-License-Identifier: MPL-2.0
"""Finite, exposed structural-proxy screen; no registered execution is asserted.

Only explicit numerical calls import NumPy. Source-owned witnesses admit the
nine scores. Each numerical fitter receives training responses and label-free
queries; published responses used in other folds remain exposed to the caller.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, localcontext
from hashlib import sha256
from itertools import combinations
from typing import ClassVar

from empirical_lawhood.adapters.physical.rubisco_kinetics.mcdonald2026 import PlantContextV1
from empirical_lawhood.adapters.physical.rubisco_kinetics.plant_structural_scores import (
    S1_SHA256, PlantStructuralScoreRowV1,
)
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord, validate_decimal, validate_stable_id,
)

from . import records as source_roles

PROTOCOL_SHA256 = "79abe9a72cd30103ec813965df34a011e54a890e25f86eb0324a9087d71ed59d"
PREFIX = "rubisco-plant-structural-screen.v1"
ALPHAS = (Decimal("0.1"), Decimal(1), Decimal(10))
FAMILIES = ("if-conservation", "if-only", "conservation-only")
METHODS = ("parent", "training-mean", *FAMILIES)
ENDPOINTS = source_roles.ENDPOINTS
EDITS = source_roles.FOCAL_EDITS
SITES = source_roles.SITES
DIAGNOSTIC_STATUS = "UNEVALUABLE_NO_EXACT_DEPOSITED_STRUCTURAL_SCORE"


def _number(value: Decimal) -> None:
    validate_decimal(value, field_name="structural_screen_number")


def _typed(values, record_type, count: int | None = None) -> None:
    if (type(values) is not tuple or (count is not None and len(values) != count)
            or not values or any(type(v) is not record_type for v in values)):
        raise ValueError("structural screen requires its immutable typed census")
    for value in values:
        value.__post_init__()


def case_id(edit: str) -> str:
    if edit not in EDITS:
        raise ValueError("structural screen changes its nine focal edits")
    return PREFIX + "." + edit.lower()


@dataclass(frozen=True, slots=True)
class RidgeQueryV1(CanonicalRecord):
    """A numerical query contains no response field or native label record."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/structural-screen/ridge-query"
    case_id: str
    site: int
    features: tuple[Decimal, ...]

    def __post_init__(self) -> None:
        validate_stable_id(self.case_id)
        if (type(self.site) is not int or self.site <= 0 or type(self.features) is not tuple
                or len(self.features) not in (1, 2)):
            raise ValueError("ridge query needs one or two features and one site")
        for value in self.features:
            _number(value)


@dataclass(frozen=True, slots=True)
class RidgeTrainingPointV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/structural-screen/ridge-training-point"
    query: RidgeQueryV1
    response: Decimal

    def __post_init__(self) -> None:
        if type(self.query) is not RidgeQueryV1:
            raise ValueError("ridge training requires a typed feature query")
        self.query.__post_init__()
        _number(self.response)


@dataclass(frozen=True, slots=True)
class RidgeFitV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/structural-screen/ridge-fit"
    training_queries: tuple[RidgeQueryV1, ...]
    query_rows: tuple[RidgeQueryV1, ...]
    alpha: Decimal
    row_weights: tuple[Decimal, ...]
    feature_means: tuple[Decimal, ...]
    feature_scales: tuple[Decimal, ...]
    constant_columns: tuple[bool, ...]
    intercept: Decimal
    coefficients: tuple[Decimal, ...]
    predictions: tuple[Decimal, ...]

    def __post_init__(self) -> None:
        _number(self.alpha)
        _typed(self.training_queries, RidgeQueryV1)
        _typed(self.query_rows, RidgeQueryV1)
        dimension = len(self.training_queries[0].features)
        if (self.alpha not in ALPHAS
                or any(len(q.features) != dimension for q in (*self.training_queries, *self.query_rows))
                or len(self.row_weights) != len(self.training_queries)
                or len(self.predictions) != len(self.query_rows)
                or any(len(v) != dimension for v in (self.feature_means, self.feature_scales,
                                                      self.constant_columns, self.coefficients))
                or any(type(v) is not bool for v in self.constant_columns)
                or set(q.site for q in self.training_queries) & set(q.site for q in self.query_rows)
                or len({q.case_id for q in (*self.training_queries, *self.query_rows)})
                != len(self.training_queries) + len(self.query_rows)):
            raise ValueError("ridge fit changes its dimensions, census or held-site boundary")
        for value in (*self.row_weights, *self.feature_means, *self.feature_scales,
                      self.intercept, *self.coefficients, *self.predictions):
            _number(value)
        if any(w <= 0 for w in self.row_weights) or any(s <= 0 for s in self.feature_scales):
            raise ValueError("ridge fit requires positive weights/scales")


def fit_ridge(training: tuple[RidgeTrainingPointV1, ...], queries: tuple[RidgeQueryV1, ...],
              alpha: Decimal) -> RidgeFitV1:
    """Fit only these training rows; held responses are not an accepted argument."""
    _typed(training, RidgeTrainingPointV1)
    _typed(queries, RidgeQueryV1)
    _number(alpha)
    if alpha not in ALPHAS:
        raise ValueError("ridge alpha changes its frozen grid")
    training_queries = tuple(row.query for row in training)
    sites = tuple(sorted({q.site for q in training_queries}))
    if set(sites) & {q.site for q in queries}:
        raise ValueError("ridge fitter refuses a held-site label overlap")
    dimension = len(training_queries[0].features)
    if any(len(q.features) != dimension for q in (*training_queries, *queries)):
        raise ValueError("ridge feature dimensions differ")
    import numpy as np

    x = np.asarray([[float(v) for v in q.features] for q in training_queries], dtype=np.float64)
    query_x = np.asarray([[float(v) for v in q.features] for q in queries], dtype=np.float64)
    y = np.asarray([float(row.response) for row in training], dtype=np.float64)
    weights = np.asarray([1 / (len(sites) * sum(q.site == row.query.site for q in training_queries))
                          for row in training], dtype=np.float64)
    means = weights @ x
    constant = np.asarray([all(q.features[j] == training_queries[0].features[j]
                              for q in training_queries) for j in range(dimension)], dtype=bool)
    scales = np.sqrt(weights @ ((x - means) ** 2))
    scales[constant] = 1.0
    z, query_z = (x - means) / scales, (query_x - means) / scales
    z[:, constant], query_z[:, constant] = 0.0, 0.0
    design = np.column_stack((np.ones(len(training)), z))
    matrix = design.T @ (weights[:, None] * design)
    matrix[1:, 1:] += float(alpha) * np.eye(dimension)
    try:
        solution = np.linalg.solve(matrix, design.T @ (weights * y))
    except np.linalg.LinAlgError as error:
        raise ValueError("structural ridge refuses a singular solve") from error
    if not np.isfinite(solution).all():
        raise ValueError("structural ridge refuses a nonfinite solve")
    if all(row.response == training[0].response for row in training):
        # NumPy still solves the same declared objective. Normalize its exact
        # constant-response identity (intercept=y, slopes=0), so floating
        # summation cannot masquerade as feature-driven discrimination. This
        # identity uses equality of all native Decimals, not a tolerance/gate.
        solution = np.asarray([float(training[0].response), *([0.0] * dimension)])
    predicted = solution[0] + query_z @ solution[1:]
    if (not all(np.isfinite(a).all() for a in (x, query_x, y, weights, means, scales, solution, predicted))
            or (scales <= 0).any()):
        raise ValueError("structural ridge refuses nonfinite numeric operands/results")
    decimal = lambda value: Decimal(str(float(value)))
    return RidgeFitV1(training_queries, queries, alpha, tuple(map(decimal, weights)),
                      tuple(map(decimal, means)), tuple(map(decimal, scales)), tuple(map(bool, constant)),
                      decimal(solution[0]), tuple(map(decimal, solution[1:])), tuple(map(decimal, predicted)))


@dataclass(frozen=True, slots=True)
class StructuralOuterFoldV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/structural-screen/outer-fold"
    family: str
    endpoint: str
    held_site: int
    inner_fits: tuple[RidgeFitV1, ...]
    alpha_scores: tuple[Decimal, ...]
    selected_alpha: Decimal
    outer_fit: RidgeFitV1

    def __post_init__(self) -> None:
        _typed(self.inner_fits, RidgeFitV1, 15)
        if (self.family not in FAMILIES or self.endpoint not in ENDPOINTS or self.held_site not in SITES
                or type(self.outer_fit) is not RidgeFitV1 or len(self.alpha_scores) != 3):
            raise ValueError("structural fold changes its frozen family/endpoint/tuning census")
        self.outer_fit.__post_init__()
        training_sites = tuple(site for site in SITES if site != self.held_site)
        for index, fit in enumerate(self.inner_fits):
            inner_site = training_sites[index % 5]
            if (fit.alpha != ALPHAS[index // 5]
                    or {q.site for q in fit.query_rows} != {inner_site}
                    or {q.site for q in fit.training_queries} != set(training_sites) - {inner_site}):
                raise ValueError("structural inner fold leaks an outer/inner held site")
        if ({q.site for q in self.outer_fit.query_rows} != {self.held_site}
                or {q.site for q in self.outer_fit.training_queries} != set(training_sites)
                or self.outer_fit.alpha != self.selected_alpha):
            raise ValueError("structural outer fold changes its held-site separation")
        for value in self.alpha_scores:
            _number(value)
            if value < 0:
                raise ValueError("structural alpha error cannot be negative")
        selected = min(range(3), key=lambda i: (self.alpha_scores[i], -ALPHAS[i]))
        if self.selected_alpha != ALPHAS[selected]:
            raise ValueError("structural fold changes alpha selection or its larger-alpha tie rule")


def _crossfit_family(queries: tuple[RidgeQueryV1, ...], responses: tuple[Decimal, ...],
                     family: str, endpoint: str) -> tuple[StructuralOuterFoldV1, ...]:
    """Finite software core; callers admit native sources before using it."""
    _typed(queries, RidgeQueryV1, 9)
    if (tuple(q.case_id for q in queries) != tuple(case_id(edit) for edit in EDITS)
            or tuple(q.site for q in queries) != tuple(int(edit[1:-1]) for edit in EDITS)
            or len(responses) != 9 or family not in FAMILIES or endpoint not in ENDPOINTS):
        raise ValueError("structural crossfit changes its full nine-case/site roster")
    for value in responses:
        _number(value)
    response_map = dict(zip((q.case_id for q in queries), responses, strict=True))
    folds = []
    with localcontext(source_roles.NUMERICAL_CONTEXT):
        for held_site in SITES:
            outer_training = tuple(q for q in queries if q.site != held_site)
            outer_queries = tuple(q for q in queries if q.site == held_site)
            training_sites = tuple(site for site in SITES if site != held_site)
            inner_fits, scores = [], []
            for alpha in ALPHAS:
                site_errors = []
                for inner_site in training_sites:
                    train = tuple(RidgeTrainingPointV1(q, response_map[q.case_id])
                                  for q in outer_training if q.site != inner_site)
                    held = tuple(q for q in outer_training if q.site == inner_site)
                    fitted = fit_ridge(train, held, alpha)
                    inner_fits.append(fitted)
                    site_errors.append(source_roles.mean(tuple(abs(pred - response_map[q.case_id])
                                            for q, pred in zip(held, fitted.predictions, strict=True))))
                scores.append(source_roles.mean(tuple(site_errors)))
            best = min(range(3), key=lambda i: (scores[i], -ALPHAS[i]))
            outer = fit_ridge(tuple(RidgeTrainingPointV1(q, response_map[q.case_id]) for q in outer_training),
                              outer_queries, ALPHAS[best])
            folds.append(StructuralOuterFoldV1(family, endpoint, held_site, tuple(inner_fits),
                                               tuple(scores), ALPHAS[best], outer))
    return tuple(folds)


@dataclass(frozen=True, slots=True)
class StructuralForecastPointV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/structural-screen/forecast-point"
    edit: str
    method: str
    endpoint: str
    parent_value: Decimal
    predicted_log_contrast: Decimal
    predicted_value: Decimal

    def __post_init__(self) -> None:
        if self.edit not in EDITS or self.method not in METHODS or self.endpoint not in ENDPOINTS:
            raise ValueError("structural forecast changes its focal/method/endpoint role")
        for value in (self.parent_value, self.predicted_log_contrast, self.predicted_value):
            _number(value)
        if self.parent_value <= 0 or self.predicted_value <= 0:
            raise ValueError("structural forecast refuses nonpositive means")
        with localcontext(source_roles.NUMERICAL_CONTEXT):
            expected = self.parent_value * self.predicted_log_contrast.exp()
        if self.predicted_value != expected:
            raise ValueError("structural forecast changes raw recovery from log contrast")


@dataclass(frozen=True, slots=True)
class StructuralForecastsV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/structural-screen/forecasts"
    source_scores: tuple[PlantStructuralScoreRowV1, ...]
    source_panel: ObjectIdentity
    native_parent: ObjectIdentity
    native_labels: tuple[ObjectIdentity, ...]
    protocol_sha256: str
    folds: tuple[StructuralOuterFoldV1, ...]
    points: tuple[StructuralForecastPointV1, ...]
    diagnostic_status: str = DIAGNOSTIC_STATUS
    exposure: str = "DEVELOPMENT_VISIBLE_NON_PROMOTABLE"

    def __post_init__(self) -> None:
        _typed(self.source_scores, PlantStructuralScoreRowV1, 9)
        _typed(self.folds, StructuralOuterFoldV1, 36)
        _typed(self.points, StructuralForecastPointV1, 90)
        if (tuple(row.edit for row in self.source_scores) != EDITS
                or self.source_panel != source_roles.plant_identity()
                or self.native_parent != source_roles.context_identity(None)
                or self.native_labels != tuple(source_roles.context_identity(edit) for edit in source_roles.EDITS)
                or self.protocol_sha256 != PROTOCOL_SHA256
                or self.diagnostic_status != DIAGNOSTIC_STATUS or self.exposure != "DEVELOPMENT_VISIBLE_NON_PROMOTABLE"
                or tuple((f.family, f.endpoint, f.held_site) for f in self.folds)
                != tuple((family, endpoint, site) for family in FAMILIES for endpoint in ENDPOINTS for site in SITES)
                or tuple((p.edit, p.method, p.endpoint) for p in self.points)
                != tuple((edit, method, endpoint) for edit in EDITS for method in METHODS for endpoint in ENDPOINTS)):
            raise ValueError("structural forecasts change native/protocol identities or their complete census")
        expected_queries = {family: _family_queries(self.source_scores, family) for family in FAMILIES}
        for fold in self.folds:
            queries = expected_queries[fold.family]
            outer_training = tuple(q for q in queries if q.site != fold.held_site)
            outer_held = tuple(q for q in queries if q.site == fold.held_site)
            if (fold.outer_fit.training_queries != outer_training or fold.outer_fit.query_rows != outer_held):
                raise ValueError("structural outer queries change the native feature/case roster")
            for fit in fold.inner_fits:
                inner_site = fit.query_rows[0].site
                inner_training = tuple(q for q in outer_training if q.site != inner_site)
                inner_held = tuple(q for q in outer_training if q.site == inner_site)
                if fit.training_queries != inner_training or fit.query_rows != inner_held:
                    raise ValueError("structural inner queries change the native feature/case roster")
        fitted = {(q.case_id, f.family, f.endpoint): value for f in self.folds
                  for q, value in zip(f.outer_fit.query_rows, f.outer_fit.predictions, strict=True)}
        for point in self.points:
            if ((point.method == "parent" and point.predicted_log_contrast != 0)
                    or (point.method in FAMILIES and point.predicted_log_contrast
                        != fitted[case_id(point.edit), point.method, point.endpoint])):
                raise ValueError("structural forecasts differ from their held-site fitted values")


def _family_queries(rows: tuple[PlantStructuralScoreRowV1, ...], family: str) -> tuple[RidgeQueryV1, ...]:
    with localcontext(source_roles.NUMERICAL_CONTEXT):
        return tuple(RidgeQueryV1(case_id(row.edit), row.site,
                     (row.inverse_folding_log_likelihood, row.land_plant_conservation_percent / 100)
                     if family == "if-conservation" else (row.inverse_folding_log_likelihood,)
                     if family == "if-only" else (row.land_plant_conservation_percent / 100,)) for row in rows)


def _admit_contexts(parent: PlantContextV1, labels: tuple[PlantContextV1, ...]) -> None:
    source_roles._context(parent, None)
    _typed(labels, PlantContextV1, 10)
    if tuple(label.protein_recipe.edit for label in labels) != source_roles.EDITS:
        raise ValueError("structural labels change the complete focal/diagnostic census")
    for label, edit in zip(labels, source_roles.EDITS, strict=True):
        source_roles._context(label, edit)


def crossfit_structural_scores(score_rows: tuple[PlantStructuralScoreRowV1, ...],
                              parent: PlantContextV1, labels: tuple[PlantContextV1, ...],
                              *, protocol_payload: bytes) -> StructuralForecastsV1:
    """Construct all forecasts before a separate exposed metric evaluation."""
    if type(protocol_payload) is not bytes or sha256(protocol_payload).hexdigest() != PROTOCOL_SHA256:
        raise ValueError("structural screen requires the exact frozen protocol bytes")
    _typed(score_rows, PlantStructuralScoreRowV1, 9)
    if tuple(row.edit for row in score_rows) != EDITS or any(row.source_sha256 != S1_SHA256 for row in score_rows):
        raise ValueError("structural screen changes its exact score source/roster")
    _admit_contexts(parent, labels)
    with localcontext(source_roles.NUMERICAL_CONTEXT):
        responses = {endpoint: tuple((label.quantity(endpoint).mean / parent.quantity(endpoint).mean).ln()
                                    for label in labels[:9]) for endpoint in ENDPOINTS}
        folds = []
        for family in FAMILIES:
            queries = _family_queries(score_rows, family)
            for endpoint in ENDPOINTS:
                folds.extend(_crossfit_family(queries, responses[endpoint], family, endpoint))
        predicted = {(q.case_id, f.family, f.endpoint): value for f in folds
                     for q, value in zip(f.outer_fit.query_rows, f.outer_fit.predictions, strict=True)}
        points = []
        for edit in EDITS:
            site = int(edit[1:-1])
            train_indices = tuple(i for i, candidate in enumerate(EDITS) if int(candidate[1:-1]) != site)
            for method in METHODS:
                for endpoint in ENDPOINTS:
                    if method == "parent":
                        contrast = Decimal(0)
                    elif method == "training-mean":
                        contrast = source_roles.mean(tuple(source_roles.mean(tuple(responses[endpoint][i]
                                        for i in train_indices if int(EDITS[i][1:-1]) == group))
                                        for group in SITES if group != site))
                    else:
                        contrast = predicted[case_id(edit), method, endpoint]
                    parent_value = parent.quantity(endpoint).mean
                    points.append(StructuralForecastPointV1(edit, method, endpoint, parent_value,
                                                             contrast, parent_value * contrast.exp()))
    return StructuralForecastsV1(score_rows, source_roles.plant_identity(), source_roles.context_identity(None),
                                tuple(source_roles.context_identity(edit) for edit in source_roles.EDITS),
                                PROTOCOL_SHA256, tuple(folds), tuple(points))


@dataclass(frozen=True, slots=True)
class StructuralPointErrorV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/structural-screen/point-error"
    forecast: StructuralForecastPointV1
    observed_value: Decimal
    observed_log_contrast: Decimal
    absolute_error: Decimal
    absolute_log_error: Decimal
    predicted_sign: int
    observed_sign: int

    def __post_init__(self) -> None:
        if type(self.forecast) is not StructuralForecastPointV1:
            raise ValueError("structural error needs one typed forecast")
        self.forecast.__post_init__()
        for value in (self.observed_value, self.observed_log_contrast, self.absolute_error, self.absolute_log_error):
            _number(value)
        with localcontext(source_roles.NUMERICAL_CONTEXT):
            contrast = (self.observed_value / self.forecast.parent_value).ln() if self.observed_value > 0 else None
            if (self.observed_log_contrast != contrast
                    or self.absolute_error != abs(self.forecast.predicted_value - self.observed_value)
                    or self.absolute_log_error != abs(self.forecast.predicted_log_contrast - contrast)
                    or type(self.predicted_sign) is not int or type(self.observed_sign) is not int
                    or self.predicted_sign != _sign(self.forecast.predicted_log_contrast)
                    or self.observed_sign != _sign(contrast)):
                raise ValueError("structural error changes observed contrast/error/sign arithmetic")


@dataclass(frozen=True, slots=True)
class StructuralErrorSummaryV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/structural-screen/error-summary"
    method: str
    endpoint: str
    weighting: str
    member_ids: tuple[str, ...]
    mean_absolute_log_error: Decimal
    root_mean_squared_log_error: Decimal
    mean_absolute_error: Decimal
    mean_absolute_deviation_from_training_mean: Decimal

    def __post_init__(self) -> None:
        if (self.method not in METHODS or self.endpoint not in ENDPOINTS
                or self.weighting not in ("NINE_ROWS", "SIX_SITES")
                or self.member_ids != (EDITS if self.weighting == "NINE_ROWS" else tuple(str(site) for site in SITES))):
            raise ValueError("structural summary changes its full row/site denominator")
        for value in (self.mean_absolute_log_error, self.root_mean_squared_log_error,
                      self.mean_absolute_error, self.mean_absolute_deviation_from_training_mean):
            _number(value)
            if value < 0:
                raise ValueError("structural summary cannot contain negative errors")


@dataclass(frozen=True, slots=True)
class StructuralPairOrderV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/structural-screen/pair-order"
    left_edit: str
    right_edit: str
    method: str
    endpoint: str
    predicted_order: int
    observed_order: int

    def __post_init__(self) -> None:
        if (self.left_edit not in EDITS or self.right_edit not in EDITS
                or EDITS.index(self.left_edit) >= EDITS.index(self.right_edit)
                or int(self.left_edit[1:-1]) != int(self.right_edit[1:-1])
                or self.method not in METHODS or self.endpoint not in ENDPOINTS
                or any(type(v) is not int or v not in (-1, 0, 1) for v in (self.predicted_order, self.observed_order))):
            raise ValueError("structural pair changes its same-site order/domain")


@dataclass(frozen=True, slots=True)
class StructuralEvaluationV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/structural-screen/evaluation"
    forecasts: ObjectIdentity
    points: tuple[StructuralPointErrorV1, ...]
    summaries: tuple[StructuralErrorSummaryV1, ...]
    pair_orders: tuple[StructuralPairOrderV1, ...]
    primary_endpoint_passes: tuple[bool, bool]
    primary_has_same_site_discrimination: tuple[bool, bool]
    diagnostic_status: str = DIAGNOSTIC_STATUS
    exposure: str = "DEVELOPMENT_VISIBLE_NON_PROMOTABLE"

    def __post_init__(self) -> None:
        _typed(self.points, StructuralPointErrorV1, 90)
        _typed(self.summaries, StructuralErrorSummaryV1, 20)
        _typed(self.pair_orders, StructuralPairOrderV1, 40)
        if (type(self.forecasts) is not ObjectIdentity
                or (self.forecasts.object_id, self.forecasts.object_schema, self.forecasts.object_version)
                != (PREFIX + ".forecasts", StructuralForecastsV1.SCHEMA, StructuralForecastsV1.VERSION)
                or self.diagnostic_status != DIAGNOSTIC_STATUS or self.exposure != "DEVELOPMENT_VISIBLE_NON_PROMOTABLE"
                or tuple((e.forecast.edit, e.forecast.method, e.forecast.endpoint) for e in self.points)
                != tuple((edit, method, endpoint) for edit in EDITS for method in METHODS for endpoint in ENDPOINTS)
                or tuple((s.method, s.endpoint, s.weighting) for s in self.summaries)
                != tuple((method, endpoint, weighting) for method in METHODS for endpoint in ENDPOINTS
                         for weighting in ("NINE_ROWS", "SIX_SITES"))):
            raise ValueError("structural evaluation changes its complete census/source role")
        expected_pairs = tuple((left, right, method, endpoint) for method in METHODS for endpoint in ENDPOINTS
                               for site in SITES for left, right in combinations(
                                   tuple(edit for edit in EDITS if int(edit[1:-1]) == site), 2))
        if tuple((p.left_edit, p.right_edit, p.method, p.endpoint) for p in self.pair_orders) != expected_pairs:
            raise ValueError("structural evaluation changes its four same-site comparison denominator")
        error_map = {(e.forecast.edit, e.forecast.method, e.forecast.endpoint): e for e in self.points}
        with localcontext(source_roles.NUMERICAL_CONTEXT):
            for summary in self.summaries:
                selected = tuple(error_map[edit, summary.method, summary.endpoint] for edit in EDITS)
                values = _summary_metrics(selected, error_map, summary.weighting, summary.endpoint)
                if values != (summary.mean_absolute_log_error, summary.root_mean_squared_log_error,
                              summary.mean_absolute_error, summary.mean_absolute_deviation_from_training_mean):
                    raise ValueError("structural evaluation changes summary arithmetic")
            for pair in self.pair_orders:
                left = error_map[pair.left_edit, pair.method, pair.endpoint]
                right = error_map[pair.right_edit, pair.method, pair.endpoint]
                if (pair.predicted_order != _sign(left.forecast.predicted_log_contrast - right.forecast.predicted_log_contrast)
                        or pair.observed_order != _sign(left.observed_log_contrast - right.observed_log_contrast)):
                    raise ValueError("structural evaluation changes observed/predicted pair arithmetic")
        summaries = {(s.method, s.endpoint, s.weighting): s for s in self.summaries}
        passes = tuple(all(summaries["if-conservation", e, "SIX_SITES"].mean_absolute_log_error
                            < summaries[b, e, "SIX_SITES"].mean_absolute_log_error
                            for b in ("parent", "training-mean")) for e in ENDPOINTS)
        discrimination = tuple(any(p.predicted_order != 0 for p in self.pair_orders
                                  if p.method == "if-conservation" and p.endpoint == e) for e in ENDPOINTS)
        if (type(self.primary_endpoint_passes) is not tuple or type(self.primary_has_same_site_discrimination) is not tuple
                or any(type(v) is not bool for v in (*self.primary_endpoint_passes, *self.primary_has_same_site_discrimination))
                or self.primary_endpoint_passes != passes
                or self.primary_has_same_site_discrimination != discrimination):
            raise ValueError("structural evaluation changes its two-endpoint baseline/discrimination disposition")


def _sign(value: Decimal) -> int:
    return (value > 0) - (value < 0)


def _summary_metrics(selected, error_map, weighting, endpoint):
    groups = (selected,) if weighting == "NINE_ROWS" else tuple(
        tuple(e for e in selected if int(e.forecast.edit[1:-1]) == site) for site in SITES)
    metric = lambda values: source_roles.mean(tuple(source_roles.mean(tuple(values(e) for e in group))
                                                    for group in groups))
    return (metric(lambda e: e.absolute_log_error), metric(lambda e: e.absolute_log_error ** 2).sqrt(),
            metric(lambda e: e.absolute_error), metric(lambda e: abs(e.forecast.predicted_log_contrast
                - error_map[e.forecast.edit, "training-mean", endpoint].forecast.predicted_log_contrast)))


def evaluate_structural_screen(forecasts: StructuralForecastsV1, parent: PlantContextV1,
                               labels: tuple[PlantContextV1, ...]) -> StructuralEvaluationV1:
    """Evaluate the complete committed census without fitting or selecting again."""
    if type(forecasts) is not StructuralForecastsV1:
        raise ValueError("structural evaluation requires typed complete forecasts")
    forecasts.__post_init__()
    _admit_contexts(parent, labels)
    label_map = {label.protein_recipe.edit: label for label in labels[:9]}
    errors, summaries, orders = [], [], []
    with localcontext(source_roles.NUMERICAL_CONTEXT):
        for point in forecasts.points:
            observed = label_map[point.edit].quantity(point.endpoint).mean
            if point.parent_value != parent.quantity(point.endpoint).mean:
                raise ValueError("structural evaluation changes its measured-parent anchor")
            log_response = (observed / point.parent_value).ln()
            errors.append(StructuralPointErrorV1(point, observed, log_response,
                          abs(point.predicted_value - observed), abs(point.predicted_log_contrast - log_response),
                          _sign(point.predicted_log_contrast), _sign(log_response)))
        error_map = {(e.forecast.edit, e.forecast.method, e.forecast.endpoint): e for e in errors}
        for method in METHODS:
            for endpoint in ENDPOINTS:
                selected = tuple(error_map[edit, method, endpoint] for edit in EDITS)
                for weighting in ("NINE_ROWS", "SIX_SITES"):
                    log_mae, log_rmse, raw_mae, deviation = _summary_metrics(selected, error_map, weighting, endpoint)
                    members = EDITS if weighting == "NINE_ROWS" else tuple(str(site) for site in SITES)
                    summaries.append(StructuralErrorSummaryV1(method, endpoint, weighting, members,
                                                               log_mae, log_rmse, raw_mae, deviation))
                for site in SITES:
                    site_edits = tuple(edit for edit in EDITS if int(edit[1:-1]) == site)
                    for left, right in combinations(site_edits, 2):
                        a, b = error_map[left, method, endpoint], error_map[right, method, endpoint]
                        orders.append(StructuralPairOrderV1(left, right, method, endpoint,
                            _sign(a.forecast.predicted_log_contrast - b.forecast.predicted_log_contrast),
                            _sign(a.observed_log_contrast - b.observed_log_contrast)))
    summary_map = {(s.method, s.endpoint, s.weighting): s for s in summaries}
    passes = tuple(all(summary_map["if-conservation", e, "SIX_SITES"].mean_absolute_log_error
                        < summary_map[baseline, e, "SIX_SITES"].mean_absolute_log_error
                        for baseline in ("parent", "training-mean")) for e in ENDPOINTS)
    discrimination = tuple(any(p.predicted_order != 0 for p in orders
                            if p.method == "if-conservation" and p.endpoint == endpoint) for endpoint in ENDPOINTS)
    return StructuralEvaluationV1(ObjectIdentity.from_record(PREFIX + ".forecasts", forecasts), tuple(errors),
                                  tuple(summaries), tuple(orders), passes, discrimination)
