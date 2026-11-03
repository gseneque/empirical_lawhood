# SPDX-License-Identifier: MPL-2.0
"""A bounded conventional, position-blind paired-composition rejection pilot.

These numerical records do not admit native biology. Callers bind exact sources,
protein recipes and exposed response roles separately. NumPy is imported only
inside numerical fitting. Through-origin fits preserve the no-edit anchor.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, localcontext
from typing import ClassVar

from empirical_lawhood.kernel.serialization import (
    CanonicalRecord, validate_decimal, validate_sha256, validate_stable_id,
)

METHODS = ("split-ridge", "pooled-ridge", "anchored-rbf")
ALPHAS = (Decimal("0.1"), Decimal(1), Decimal(10))
GAMMAS = (Decimal("0.1"), Decimal(1), Decimal(10))
AMINO_ACIDS = "ARNDCQEGHILKMFPSTWYV"
FEATURE_NAMES = ("lsu-volume-index", "lsu-hydropathy", "lsu-charge-convention",
                 "ssu-volume-index", "ssu-hydropathy", "ssu-charge-convention")
NUMERICAL_CONTEXT = Context(prec=50)


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext(NUMERICAL_CONTEXT):
        return sum(values, Decimal(0)) / len(values)


def _mae(predictions: tuple[Decimal, ...], points: tuple[PairedTrainingPointV1, ...]) -> Decimal:
    with localcontext(NUMERICAL_CONTEXT):
        return _mean(tuple(abs(pred - point.response) for pred, point in zip(predictions, points, strict=True)))


def _numbers(values: tuple[Decimal, ...], length: int | None = None) -> None:
    if type(values) is not tuple or (length is not None and len(values) != length):
        raise ValueError("paired response requires its immutable numeric dimensions")
    for value in values:
        validate_decimal(value, field_name="paired_response_number")


def _typed(values, kind) -> None:
    if type(values) is not tuple or not values or any(type(v) is not kind for v in values):
        raise ValueError("paired response requires immutable typed rows")
    for value in values:
        value.__post_init__()


@dataclass(frozen=True, slots=True)
class CompositionDescriptorsV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/paired-response/descriptors"
    source_sha256: str
    volume_index: tuple[Decimal, ...]
    hydropathy: tuple[Decimal, ...]
    amino_acids: str = AMINO_ACIDS
    volume_accession: str = "GRAR740103"
    hydropathy_accession: str = "KYTJ820101"
    charge_convention: str = "KR_PLUS_ONE_DE_MINUS_ONE_OTHER_ZERO_INCLUDING_H"

    def __post_init__(self) -> None:
        validate_sha256(self.source_sha256)
        _numbers(self.volume_index, 20)
        _numbers(self.hydropathy, 20)
        if (self.amino_acids != AMINO_ACIDS or self.volume_accession != "GRAR740103"
                or self.hydropathy_accession != "KYTJ820101"
                or self.charge_convention != "KR_PLUS_ONE_DE_MINUS_ONE_OTHER_ZERO_INCLUDING_H"):
            raise ValueError("paired descriptors change their native identities or charge convention")


def composition_delta(parent: str, variant: str, table: CompositionDescriptorsV1) -> tuple[Decimal, ...]:
    """Total per-chain composition deltas; no alignment, site or contact claim."""
    if type(table) is not CompositionDescriptorsV1:
        raise ValueError("composition requires its typed descriptor table")
    table.__post_init__()
    if any(type(s) is not str or not 1 <= len(s) <= 1024 or set(s) - set(AMINO_ACIDS)
           for s in (parent, variant)):
        raise ValueError("composition requires bounded standard-amino-acid protein strings")
    # Counts give exact positional invariance and cancellation, including
    # unequal-length recipes; this is not a structural alignment operation.
    counts = tuple(variant.count(aa) - parent.count(aa) for aa in AMINO_ACIDS)
    charge = tuple(Decimal(1 if aa in "KR" else -1 if aa in "DE" else 0) for aa in AMINO_ACIDS)
    with localcontext(NUMERICAL_CONTEXT):
        return tuple(sum((Decimal(n) * value for n, value in zip(counts, descriptor, strict=True)), Decimal(0))
                     for descriptor in (table.volume_index, table.hydropathy, charge))


@dataclass(frozen=True, slots=True)
class PairedFeatureQueryV1(CanonicalRecord):
    """Label-free six channels in FEATURE_NAMES order."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/paired-response/query"
    case_id: str
    group_id: str
    features: tuple[Decimal, ...]

    def __post_init__(self) -> None:
        validate_stable_id(self.case_id)
        validate_stable_id(self.group_id)
        _numbers(self.features, 6)


@dataclass(frozen=True, slots=True)
class PairedTrainingPointV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/paired-response/training-point"
    query: PairedFeatureQueryV1
    response: Decimal

    def __post_init__(self) -> None:
        if type(self.query) is not PairedFeatureQueryV1:
            raise ValueError("paired training requires a label-free query")
        self.query.__post_init__()
        validate_decimal(self.response, field_name="paired_response")


@dataclass(frozen=True, slots=True)
class PairedFitV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/paired-response/fit"
    method: str
    training_queries: tuple[PairedFeatureQueryV1, ...]
    query_rows: tuple[PairedFeatureQueryV1, ...]
    alpha: Decimal
    gamma: Decimal | None
    row_weights: tuple[Decimal, ...]
    feature_scales: tuple[Decimal, ...]
    inactive_columns: tuple[bool, ...]
    coefficients: tuple[Decimal, ...]
    predictions: tuple[Decimal, ...]

    def __post_init__(self) -> None:
        _typed(self.training_queries, PairedFeatureQueryV1)
        _typed(self.query_rows, PairedFeatureQueryV1)
        _hyperparameters(self.method, self.alpha, self.gamma)
        dimension = 3 if self.method == "pooled-ridge" else 6
        _numbers(self.row_weights, len(self.training_queries))
        _numbers(self.feature_scales, dimension)
        _numbers(self.predictions, len(self.query_rows))
        _numbers(self.coefficients, len(self.training_queries) if self.method == "anchored-rbf" else dimension)
        with localcontext(NUMERICAL_CONTEXT):
            weight_error = abs(sum(self.row_weights) - 1)
        if (type(self.inactive_columns) is not tuple or len(self.inactive_columns) != dimension
                or any(type(v) is not bool for v in self.inactive_columns)
                or any(v <= 0 for v in (*self.row_weights, *self.feature_scales))
                or weight_error > Decimal("1e-14")):
            raise ValueError("paired fit changes positive normalized weights/scales or inactive columns")
        _separate(self.training_queries, self.query_rows)


def _hyperparameters(method: str, alpha: Decimal, gamma: Decimal | None) -> None:
    validate_decimal(alpha, field_name="paired_alpha")
    if method not in METHODS or alpha not in ALPHAS:
        raise ValueError("paired fitter changes its frozen method or alpha grid")
    if method == "anchored-rbf":
        validate_decimal(gamma, field_name="paired_gamma")
        if gamma not in GAMMAS:
            raise ValueError("paired kernel changes its frozen gamma grid")
    elif gamma is not None:
        raise ValueError("linear paired fitter has no kernel gamma")


def _separate(training: tuple[PairedFeatureQueryV1, ...], queries: tuple[PairedFeatureQueryV1, ...]) -> None:
    all_rows = (*training, *queries)
    if (len({q.case_id for q in all_rows}) != len(all_rows)
            or {q.group_id for q in training} & {q.group_id for q in queries}):
        raise ValueError("paired fitter refuses duplicate cases or held-group overlap")


def group_weights(queries: tuple[PairedFeatureQueryV1, ...]) -> tuple[Decimal, ...]:
    _typed(queries, PairedFeatureQueryV1)
    groups = set(q.group_id for q in queries)
    with localcontext(NUMERICAL_CONTEXT):
        return tuple(Decimal(1) / (len(groups) * sum(q.group_id == p.group_id for p in queries)) for q in queries)


def fit_response(training: tuple[PairedTrainingPointV1, ...], queries: tuple[PairedFeatureQueryV1, ...],
                 method: str, alpha: Decimal, gamma: Decimal | None = None) -> PairedFitV1:
    """Training-only scales and response values, with exact no-edit anchoring."""
    _typed(training, PairedTrainingPointV1)
    _typed(queries, PairedFeatureQueryV1)
    _hyperparameters(method, alpha, gamma)
    training_queries = tuple(p.query for p in training)
    _separate(training_queries, queries)
    if len(training) > 128 or len(queries) > 128:
        raise ValueError("paired pilot exceeds its bounded numerical row census")
    import numpy as np

    def matrix(rows):
        x = np.asarray([[float(v) for v in q.features] for q in rows], dtype=np.float64)
        return x[:, :3] + x[:, 3:] if method == "pooled-ridge" else x

    x, query_x = matrix(training_queries), matrix(queries)
    y = np.asarray([float(p.response) for p in training], dtype=np.float64)
    weights = np.asarray(list(map(float, group_weights(training_queries))), dtype=np.float64)
    if not all(np.isfinite(v).all() for v in (x, query_x, y, weights)):
        raise ValueError("paired fitter refuses nonfinite float64 operands")
    with np.errstate(over="raise", invalid="raise", divide="raise", under="ignore"):
        try:
            inactive = np.all(x == 0, axis=0)
            scales = np.sqrt(weights @ (x * x))
            scales[inactive] = 1.0
            z, query_z = x / scales, query_x / scales
            # No training variation from the zero parent anchor means no
            # learned response for that channel, including in kernel distance.
            z[:, inactive], query_z[:, inactive] = 0.0, 0.0
            if method == "anchored-rbf":
                def kernel(a, b):
                    aa, bb = np.sum(a * a, axis=1), np.sum(b * b, axis=1)
                    distance = np.sum((a[:, None, :] - b[None, :, :]) ** 2, axis=2)
                    return (np.exp(-float(gamma) * distance) - np.exp(-float(gamma) * aa[:, None])
                            - np.exp(-float(gamma) * bb[None, :]) + 1)
                k = kernel(z, z)
                root_w = np.sqrt(weights)
                solution = root_w * np.linalg.solve(root_w[:, None] * k * root_w[None, :]
                    + float(alpha) * np.eye(len(training)), root_w * y)
                predictions = kernel(query_z, z) @ solution
            else:
                solution = np.linalg.solve(z.T @ (weights[:, None] * z)
                    + float(alpha) * np.eye(x.shape[1]), z.T @ (weights * y))
                predictions = query_z @ solution
        except (FloatingPointError, np.linalg.LinAlgError) as error:
            raise ValueError("paired fitter refuses overflow or a singular solve") from error
    if not all(np.isfinite(v).all() for v in (scales, z, query_z, solution, predictions)) or (scales <= 0).any():
        raise ValueError("paired fitter refuses nonfinite operands or solve results")
    # k0(0,z) and a linear zero feature vector are exactly zero. Normalize the
    # declared identity so cancellation roundoff cannot produce a fake edit.
    predictions[np.all(query_z == 0, axis=1)] = 0.0
    decimal = lambda value: Decimal(str(float(value)))
    return PairedFitV1(method, training_queries, queries, alpha, gamma, tuple(map(decimal, weights)),
        tuple(map(decimal, scales)), tuple(map(bool, inactive)), tuple(map(decimal, solution)),
        tuple(map(decimal, predictions)))


@dataclass(frozen=True, slots=True)
class PairedSelectionV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/paired-response/selection"
    method: str
    groups: tuple[str, ...]
    inner_fits: tuple[PairedFitV1, ...]
    scores: tuple[Decimal, ...]
    selected_alpha: Decimal
    selected_gamma: Decimal | None
    final_fit: PairedFitV1

    def __post_init__(self) -> None:
        if type(self.final_fit) is not PairedFitV1:
            raise ValueError("paired selection requires its final typed fit")
        self.final_fit.__post_init__()
        _typed(self.inner_fits, PairedFitV1)
        grid = _grid(self.method)
        _numbers(self.scores, len(grid))
        if (type(self.groups) is not tuple or len(self.groups) < 2 or self.groups != tuple(sorted(set(self.groups)))
                or len(self.inner_fits) != len(grid) * len(self.groups)
                or any(score < 0 for score in self.scores)
                or self.final_fit.method != self.method):
            raise ValueError("paired tuning changes its groups, grid or error census")
        roster = self.final_fit.training_queries
        if set(self.groups) != {q.group_id for q in roster}:
            raise ValueError("paired tuning changes its full final-training group roster")
        for index, fitted in enumerate(self.inner_fits):
            alpha, gamma = grid[index // len(self.groups)]
            held = self.groups[index % len(self.groups)]
            if (fitted.method != self.method or (fitted.alpha, fitted.gamma) != (alpha, gamma)
                    or fitted.training_queries != tuple(q for q in roster if q.group_id != held)
                    or fitted.query_rows != tuple(q for q in roster if q.group_id == held)):
                raise ValueError("paired tuning changes its whole-group separation or source roster")
        best = _best(self.scores, grid)
        if (self.selected_alpha, self.selected_gamma) != grid[best] or (
                self.final_fit.alpha, self.final_fit.gamma) != grid[best]:
            raise ValueError("paired selection changes its lowest-error or conservative tie rule")


def _grid(method: str) -> tuple[tuple[Decimal, Decimal | None], ...]:
    if method not in METHODS:
        raise ValueError("paired tuning changes its frozen method")
    return tuple((alpha, gamma) for alpha in ALPHAS for gamma in GAMMAS) if method == "anchored-rbf" else tuple((a, None) for a in ALPHAS)


def _best(scores, grid):
    # Equal score: larger ridge penalty, then smaller kernel gamma.
    return min(range(len(grid)), key=lambda i: (scores[i], -grid[i][0], grid[i][1] or Decimal(0)))


def tune_response(training: tuple[PairedTrainingPointV1, ...], queries: tuple[PairedFeatureQueryV1, ...],
                  method: str) -> PairedSelectionV1:
    _typed(training, PairedTrainingPointV1)
    _typed(queries, PairedFeatureQueryV1)
    _separate(tuple(p.query for p in training), queries)
    groups = tuple(sorted({p.query.group_id for p in training}))
    if len(groups) < 2:
        raise ValueError("paired tuning requires at least two explicit held groups")
    grid, fits, scores = _grid(method), [], []
    for alpha, gamma in grid:
        errors = []
        for held in groups:
            train = tuple(p for p in training if p.query.group_id != held)
            held_rows = tuple(p for p in training if p.query.group_id == held)
            fitted = fit_response(train, tuple(p.query for p in held_rows), method, alpha, gamma)
            fits.append(fitted)
            errors.append(_mae(fitted.predictions, held_rows))
        scores.append(_mean(tuple(errors)))
    best = _best(scores, grid)
    alpha, gamma = grid[best]
    final = fit_response(training, queries, method, alpha, gamma)
    return PairedSelectionV1(method, groups, tuple(fits), tuple(scores), alpha, gamma, final)


@dataclass(frozen=True, slots=True)
class PairedFixedDiagnosticV1(CanonicalRecord):
    """Two-block error diagnostic without hyperparameter selection."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/paired-response/fixed-diagnostic"
    groups: tuple[str, ...]
    inner_fits: tuple[PairedFitV1, ...]
    held_mean_absolute_errors: tuple[Decimal, ...]
    final_fit: PairedFitV1

    def __post_init__(self) -> None:
        if type(self.final_fit) is not PairedFitV1:
            raise ValueError("paired fixed diagnostic requires its final typed fit")
        self.final_fit.__post_init__()
        _typed(self.inner_fits, PairedFitV1)
        _numbers(self.held_mean_absolute_errors, len(self.groups))
        if (type(self.groups) is not tuple or len(self.groups) < 2
                or self.groups != tuple(sorted(set(self.groups)))
                or len(self.inner_fits) != len(self.groups)
                or self.final_fit.method not in ("split-ridge", "pooled-ridge")
                or self.final_fit.alpha != Decimal(1) or self.final_fit.gamma is not None
                or any(error < 0 for error in self.held_mean_absolute_errors)):
            raise ValueError("paired fixed diagnostic changes the alpha1 model or group census")
        roster = self.final_fit.training_queries
        if set(self.groups) != {q.group_id for q in roster}:
            raise ValueError("paired fixed diagnostic changes the final group roster")
        for held, fit in zip(self.groups, self.inner_fits, strict=True):
            if (fit.method != self.final_fit.method or fit.alpha != Decimal(1) or fit.gamma is not None
                    or fit.training_queries != tuple(q for q in roster if q.group_id != held)
                    or fit.query_rows != tuple(q for q in roster if q.group_id == held)):
                raise ValueError("paired fixed diagnostic changes its whole-group source split")


def diagnose_fixed(training: tuple[PairedTrainingPointV1, ...], queries: tuple[PairedFeatureQueryV1, ...],
                   method: str) -> PairedFixedDiagnosticV1:
    _typed(training, PairedTrainingPointV1)
    _typed(queries, PairedFeatureQueryV1)
    groups = tuple(sorted({p.query.group_id for p in training}))
    if len(groups) < 2 or method not in ("split-ridge", "pooled-ridge"):
        raise ValueError("fixed paired diagnostic requires two groups and a linear method")
    fits, errors = [], []
    for held in groups:
        train = tuple(p for p in training if p.query.group_id != held)
        held_rows = tuple(p for p in training if p.query.group_id == held)
        fit = fit_response(train, tuple(p.query for p in held_rows), method, Decimal(1))
        fits.append(fit)
        errors.append(_mae(fit.predictions, held_rows))
    final = fit_response(training, queries, method, Decimal(1))
    return PairedFixedDiagnosticV1(groups, tuple(fits), tuple(errors), final)
