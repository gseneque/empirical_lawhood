"""Fixed parent, nearest and residue-delta ridge point diagnostics.

Fit consumes training endpoints only; predict consumes target features only;
evaluation first validates the complete global software commitment, then reads
the evaluation labels. Previously exposed biological outcomes remain exposed.

SPDX-License-Identifier: MPL-2.0
"""

from __future__ import annotations

from decimal import Decimal, localcontext

from empirical_lawhood.adapters.physical.rubisco_kinetics.records import (
    HistoricalFeatureSliceV1, HistoricalLabelSliceV1, HistoricalTrainingSliceV1,
    ReportedEndpointsV1,
)
from empirical_lawhood.adapters.physical.rubisco_kinetics.rr2018 import (
    Rr2018NativeAuditV1, SOURCE_SHA256, selected_features,
)
from empirical_lawhood.kernel.provenance import ObjectIdentity

from .records import (
    BaselineV1, HistoricalEvaluationV1, HistoricalFittedModelV1,
    HistoricalFoldForecastsV1, HistoricalFoldV1, HistoricalForecastCommitmentV1,
    HistoricalForecastV1, HistoricalPointErrorV1, HistoricalScienceV1, PREFIX,
    RankOneFeasibilityV1, ScalarPassIntervalV1, numerical_context,
)


def rr2018_science(audit: Rr2018NativeAuditV1) -> HistoricalScienceV1:
    """Select exact original RR2018 source and the frozen two-fold diagnostic.

    This selection checks the source-record identity, not a receipt or source
    acquisition. Its caller must authenticate those original source bytes.
    """
    if not isinstance(audit, Rr2018NativeAuditV1) or audit.source_sha256 != SOURCE_SHA256:
        raise ValueError("historical E1 requires its exact retained RR2018 article digest")
    return HistoricalScienceV1(f"{PREFIX}.rr2018.science", ObjectIdentity.from_record(audit.audit_id, audit),
                               (HistoricalFoldV1("site100", ("d206e", "wt"), ("m100t",), "wt"),
                                HistoricalFoldV1("site206", ("m100t", "wt"), ("d206e",), "wt")),
                               selected_features(audit))


def _fold(science: HistoricalScienceV1, fold_id: str) -> HistoricalFoldV1:
    if not isinstance(science, HistoricalScienceV1):
        raise ValueError("historical operation requires its typed scientific design")
    selected = tuple(fold for fold in science.folds if fold.fold_id == fold_id)
    if len(selected) != 1:
        raise ValueError("historical operation changes the frozen fold roster")
    return selected[0]


def _validate_training(science: HistoricalScienceV1, training: HistoricalTrainingSliceV1) -> HistoricalFoldV1:
    if not isinstance(training, HistoricalTrainingSliceV1):
        raise ValueError("fit requires a training role, without target labels or target features")
    fold = _fold(science, training.fold_id)
    if tuple(f.sample_id for f in training.features) != fold.training_sample_ids:
        raise ValueError("fit changes the frozen training roster")
    expected = tuple(s for s in science.substitutions if s.sample_id in fold.training_sample_ids)
    if training.features != expected or training.source != science.source:
        raise ValueError("fit changes source or predeclared training features")
    return fold


def fit(science: HistoricalScienceV1, training: HistoricalTrainingSliceV1) -> HistoricalFittedModelV1:
    """Fixed twenty-coordinate ridge, penalty one, no fitted intercept."""
    import numpy as np

    fold = _validate_training(science, training)
    parent = next(e for e in training.endpoints if e.sample_id == fold.parent_anchor_sample_id)
    x = np.asarray([f.vector() for f in training.features], dtype=np.float64)
    with localcontext(numerical_context()):
        ratios = np.asarray([(float(e.turnover_s_inv / parent.turnover_s_inv),
                              float(e.specificity_dimensionless / parent.specificity_dimensionless))
                             for e in training.endpoints], dtype=np.float64)
    if not np.isfinite(ratios).all() or (ratios <= 0).any():
        raise ValueError("training endpoints exceed the declared finite float64 fit")
    y = np.log(ratios)
    coefficients = np.linalg.solve(x.T @ x + float(science.ridge_penalty) * np.eye(20), x.T @ y)
    if not np.isfinite(coefficients).all():
        raise ValueError("nonfinite fixed ridge fit")
    return HistoricalFittedModelV1(f"{science.science_id}.{fold.fold_id}.model",
                                   ObjectIdentity.from_record(science.science_id, science), training, parent,
                                   tuple((Decimal(str(a)), Decimal(str(b))) for a, b in coefficients))


def predict(science: HistoricalScienceV1, model: HistoricalFittedModelV1,
            features: HistoricalFeatureSliceV1) -> tuple[HistoricalForecastV1, ...]:
    """Frozen model plus predeclared target substitutions, never labels."""
    if not isinstance(model, HistoricalFittedModelV1) or not isinstance(features, HistoricalFeatureSliceV1):
        raise ValueError("prediction needs fitted-model and target-feature roles, never target labels")
    fold = _fold(science, features.fold_id)
    model_fold = _validate_training(science, model.training)
    if model_fold != fold:
        raise ValueError("prediction changes its model fold")
    expected_parent = next(e for e in model.training.endpoints if e.sample_id == fold.parent_anchor_sample_id)
    if (model_fold != fold or model.science != ObjectIdentity.from_record(science.science_id, science)
        or model.parent != expected_parent or model.model_id != f"{science.science_id}.{fold.fold_id}.model"
        or features.source != science.source
        or features.features != tuple(s for s in science.substitutions if s.sample_id in fold.target_sample_ids)
        or tuple(s.sample_id for s in features.features) != fold.target_sample_ids):
        raise ValueError("prediction changes its model, source or predeclared target features")
    parent = model.parent
    model_identity = ObjectIdentity.from_record(model.model_id, model)
    feature_identity = ObjectIdentity.from_record(features.slice_id, features)
    results = []
    with localcontext(numerical_context()):
        for target in features.features:
            vector = target.vector()
            distances = tuple(sum((a - b) ** 2 for a, b in zip(vector, row.vector(), strict=True))
                              for row in model.training.features)
            nearest = tuple(e for e, distance in zip(model.training.endpoints, distances, strict=True)
                            if distance == min(distances))
            # Retain every exact tie. Geometric means match the log-ratio
            # estimand; neither training order nor a first-match ID wins.
            nearest_values = tuple(
                (sum(((getattr(e, name) / getattr(parent, name)).ln() for e in nearest), Decimal(0))
                 / len(nearest)).exp() * getattr(parent, name)
                for name in ("turnover_s_inv", "specificity_dimensionless"))
            ridge_values = tuple(sum((v * coefficient[j] for v, coefficient in zip(
                vector, model.ridge_coefficients, strict=True)), Decimal(0)).exp() * anchor
                for j, anchor in enumerate((parent.turnover_s_inv, parent.specificity_dimensionless)))
            predictions = ((BaselineV1.PARENT, (parent.turnover_s_inv, parent.specificity_dimensionless)),
                           (BaselineV1.NEAREST, nearest_values), (BaselineV1.RIDGE, ridge_values))
            for method, (turnover, specificity) in predictions:
                results.append(HistoricalForecastV1(
                    f"forecast.{fold.fold_id}.{target.sample_id}.{method.value.lower()}", method,
                    ReportedEndpointsV1(target.sample_id, turnover, specificity), model_identity, feature_identity))
    return tuple(sorted(results, key=lambda forecast: forecast.forecast_id))


def commit_forecasts(science: HistoricalScienceV1,
                     fold_forecasts: tuple[HistoricalFoldForecastsV1, ...]) -> HistoricalForecastCommitmentV1:
    """Validate all folds/methods before opening any evaluation label object."""
    if (not isinstance(science, HistoricalScienceV1) or not isinstance(fold_forecasts, tuple)
        or any(not isinstance(f, HistoricalFoldForecastsV1) for f in fold_forecasts)
        or tuple(f.fold_id for f in fold_forecasts) != tuple(f.fold_id for f in science.folds)):
        raise ValueError("global forecast barrier requires the complete frozen fold census")
    for fold, bundle in zip(science.folds, fold_forecasts, strict=True):
        expected = {(sample, method) for sample in fold.target_sample_ids for method in BaselineV1}
        pairs = {(f.endpoints.sample_id, f.method) for f in bundle.forecasts}
        if pairs != expected or len(bundle.forecasts) != len(expected):
            raise ValueError("global forecast barrier loses a required baseline forecast")
        if any(f.model.object_id != f"{science.science_id}.{fold.fold_id}.model"
               or f.forecast_id != f"forecast.{fold.fold_id}.{f.endpoints.sample_id}.{f.method.value.lower()}"
               for f in bundle.forecasts):
            raise ValueError("global forecast barrier changes a model/forecast identity")
    return HistoricalForecastCommitmentV1(f"{science.science_id}.global-commit",
                                           ObjectIdentity.from_record(science.science_id, science), fold_forecasts)


def evaluate(science: HistoricalScienceV1, commitment: HistoricalForecastCommitmentV1,
             labels_by_fold: tuple[HistoricalLabelSliceV1, ...]) -> HistoricalEvaluationV1:
    """Complete fixed point errors, after the global software forecast barrier.

    The caller's platform owns temporal receipt/label-port ordering. This pure
    function enforces complete input closure and exposes no label to fitting.
    """
    # Deliberately validate the global closure before touching labels_by_fold:
    # no labels iteration, attribute read or source inspection precedes this.
    if (not isinstance(commitment, HistoricalForecastCommitmentV1)
        or commit_forecasts(science, commitment.fold_forecasts) != commitment):
        raise ValueError("evaluation needs its exact complete global forecast commitment")
    if (not isinstance(labels_by_fold, tuple)
        or any(not isinstance(label, HistoricalLabelSliceV1) for label in labels_by_fold)
        or tuple(label.fold_id for label in labels_by_fold) != tuple(f.fold_id for f in science.folds)):
        raise ValueError("evaluation requires the complete frozen evaluation-label census")
    errors = []
    with localcontext(numerical_context()):
        for fold, forecasts, labels in zip(science.folds, commitment.fold_forecasts, labels_by_fold, strict=True):
            if (labels.source != science.source
                or tuple(e.sample_id for e in labels.endpoints) != fold.target_sample_ids):
                raise ValueError("evaluation changes the native label source or roster")
            by_id = {e.sample_id: e for e in labels.endpoints}
            for forecast in forecasts.forecasts:
                observed = by_id[forecast.endpoints.sample_id]
                turnover_ratio = forecast.endpoints.turnover_s_inv / observed.turnover_s_inv
                specificity_ratio = forecast.endpoints.specificity_dimensionless / observed.specificity_dimensionless
                turnover_error, specificity_error = abs(turnover_ratio - 1), abs(specificity_ratio - 1)
                errors.append(HistoricalPointErrorV1(forecast, observed, turnover_error, specificity_error,
                    turnover_ratio.ln(), specificity_ratio.ln(),
                    turnover_error <= science.turnover_relative_tolerance
                    and specificity_error <= science.specificity_relative_tolerance))
    values = tuple(errors)
    by_sample = {}
    for error in values:
        by_sample.setdefault(error.observed.sample_id, set()).add(
            (error.forecast.endpoints.turnover_s_inv, error.forecast.endpoints.specificity_dimensionless))
    return HistoricalEvaluationV1(f"{science.science_id}.evaluate",
                                  ObjectIdentity.from_record(commitment.commitment_id, commitment), values,
                                  sum(len(f.target_sample_ids) for f in science.folds),
                                  all(len(group) == 1 for group in by_sample.values()))


def _pass_interval(parent: Decimal, training: Decimal, target: Decimal,
                   tolerance: Decimal) -> tuple[Decimal, ScalarPassIntervalV1]:
    direction = (training / parent).ln()
    lower_value, upper_value = target * (1 - tolerance), target * (1 + tolerance)
    if training == parent:
        return direction, ScalarPassIntervalV1("ALL_REAL" if lower_value <= parent <= upper_value else "EMPTY",
                                               None, None)
    if direction == 0:
        return direction, ScalarPassIntervalV1("UNRESOLVED", None, None)
    bounds = sorted(((lower_value / parent).ln() / direction, (upper_value / parent).ln() / direction))
    return direction, ScalarPassIntervalV1("FINITE", bounds[0], bounds[1])


def rank_one_feasibility(parent: ReportedEndpointsV1, training_mutant: ReportedEndpointsV1,
                          target: ReportedEndpointsV1) -> RankOneFeasibilityV1:
    """Required scalar ranges when y_hat=alpha*y for one training contrast.

    With any feature dimension and common ridge penalty, WT has x=y=0 and
    the sole nonzero row gives B=x*y/(lambda+x*x). A target therefore changes
    only alpha, not the shared two-endpoint response direction. This checks
    that specified model; it says nothing about all predictors or all biology.
    Near-contact interval comparisons are retained as unresolved rather than
    claiming exact transcendental certification from rounded Decimal logs.
    """
    if any(not isinstance(e, ReportedEndpointsV1) for e in (parent, training_mutant, target)):
        raise ValueError("rank-one feasibility needs typed endpoint operands")
    with localcontext(numerical_context(50)):
        c_direction, c_interval = _pass_interval(parent.turnover_s_inv, training_mutant.turnover_s_inv,
                                                 target.turnover_s_inv, Decimal("0.10"))
        s_direction, s_interval = _pass_interval(parent.specificity_dimensionless,
                                                 training_mutant.specificity_dimensionless,
                                                 target.specificity_dimensionless, Decimal("0.03"))
        if "EMPTY" in (c_interval.state, s_interval.state):
            disposition, reason = "INCOMPATIBLE", "CONSTANT_ENDPOINT_OUTSIDE_POINT_GATE"
        elif "UNRESOLVED" in (c_interval.state, s_interval.state):
            disposition, reason = "UNRESOLVED_NUMERICAL_BOUNDARY", "TRAINING_LOG_DIRECTION_BELOW_DECIMAL_RESOLUTION"
        elif "ALL_REAL" in (c_interval.state, s_interval.state):
            disposition, reason = "ATTAINABLE", "ONE_OR_BOTH_ENDPOINTS_IMPOSE_NO_SCALAR_RESTRICTION"
        else:
            lower, upper = max(c_interval.lower, s_interval.lower), min(c_interval.upper, s_interval.upper)
            guard = max(abs(lower), abs(upper), Decimal(1)) * Decimal("1e-40")
            if lower > upper + guard:
                disposition, reason = "INCOMPATIBLE", "DISJOINT_REQUIRED_SCALAR_INTERVALS"
            elif upper > lower + guard:
                disposition, reason = "ATTAINABLE", "REQUIRED_SCALAR_INTERVALS_HAVE_INTERIOR_OVERLAP"
            else:
                disposition, reason = "UNRESOLVED_NUMERICAL_BOUNDARY", "ROUNDED_DECIMAL_LOGS_CANNOT_CERTIFY_BOUNDARY"
        reasons = [reason, "NO_GLOBAL_PREDICTOR_IMPOSSIBILITY_CLAIM"]
        # For retained M100T this is a second, exact rational sign argument:
        # both permissible predictions lie below WT, but training directions
        # have opposite signs. Thus one endpoint requires alpha<0, the other
        # alpha>0, independently of numerical logarithm rounding.
        # Enough precision for exact multiplication by each finite three-digit
        # rational, even if an input has more than fifty significant digits.
        with localcontext(numerical_context(max(50, len(target.turnover_s_inv.as_tuple().digits) + 3,
                                                   len(target.specificity_dimensionless.as_tuple().digits) + 3))):
            below_parent = (target.turnover_s_inv * Decimal("1.10") < parent.turnover_s_inv
                            and target.specificity_dimensionless * Decimal("1.03") < parent.specificity_dimensionless)
        opposite_training_signs = (
            training_mutant.turnover_s_inv > parent.turnover_s_inv
            and training_mutant.specificity_dimensionless < parent.specificity_dimensionless) or (
            training_mutant.turnover_s_inv < parent.turnover_s_inv
            and training_mutant.specificity_dimensionless > parent.specificity_dimensionless)
        if below_parent and opposite_training_signs:
            disposition = "INCOMPATIBLE"
            reasons.append("EXACT_OPPOSITE_REQUIRED_SCALAR_SIGNS")
        return RankOneFeasibilityV1(parent, training_mutant, target, (c_direction, s_direction),
                                     c_interval, s_interval, disposition, tuple(sorted(reasons)))
