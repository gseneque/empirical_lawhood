"""Frozen information-separated successor records for historical E1.

Adapted from icf-yolo aa9346547560abcb6500f2e97b53b96f456d9be3,
adapters/methods/rubisco_historical_v1/records.py. Original canonical bytes,
receipts and scientific outcomes keep their historical identities.

SPDX-License-Identifier: MPL-2.0
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, localcontext
from enum import StrEnum
from typing import ClassVar

from empirical_lawhood.adapters.physical.rubisco_kinetics.records import (
    HistoricalFeatureSliceV1, HistoricalTrainingSliceV1, ReportedEndpointsV1,
    ReportedSubstitutionV1,
)
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord, require_sorted_unique_ids, require_sorted_unique_strings,
    validate_decimal, validate_stable_id,
)

PREFIX = "rubisco-historical-e1"
CLAIM_SCOPE = "EXPOSED_REPORTED_TABLE_CONTRAST_DIAGNOSTIC_ONLY"
CALIBRATION_STATUS = "NO_INDEPENDENT_CALIBRATION_UNITS_NO_INTERVALS"
BIOLOGICAL_GATE = "UNEVALUABLE_NO_INDEPENDENT_CALIBRATION_OR_VALIDATED_CONSTRUCTS"


def numerical_context(precision: int = 28) -> Context:
    """A complete context, unaffected by caller precision or trap settings."""
    return Context(prec=precision, Emin=-999999, Emax=999999)


class BaselineV1(StrEnum):
    PARENT = "PARENT_NO_CHANGE"
    NEAREST = "NEAREST_SUBSTITUTION"
    RIDGE = "RIDGE_RESIDUE_DELTA"


def _typed_roster(values: tuple, record_type: type, attribute: str, *, maximum: int) -> None:
    if not isinstance(values, tuple) or not 1 <= len(values) <= maximum:
        raise ValueError("historical record needs a bounded immutable complete roster")
    if any(not isinstance(value, record_type) for value in values):
        raise ValueError("historical roster contains an untyped information role")
    require_sorted_unique_ids(values, attribute=attribute, field_name=attribute)


@dataclass(frozen=True, slots=True)
class HistoricalFoldV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/historical/fold"
    fold_id: str
    training_sample_ids: tuple[str, ...]
    target_sample_ids: tuple[str, ...]
    parent_anchor_sample_id: str

    def __post_init__(self) -> None:
        validate_stable_id(self.fold_id, field_name="fold_id")
        validate_stable_id(self.parent_anchor_sample_id, field_name="parent_anchor_sample_id")
        for name in ("training_sample_ids", "target_sample_ids"):
            values = getattr(self, name)
            require_sorted_unique_strings(values, field_name=name, allow_empty=False)
            if len(values) > 128:
                raise ValueError("historical sample roster exceeds its bound")
            for sample in values:
                validate_stable_id(sample, field_name="sample_id")
        if (self.parent_anchor_sample_id not in self.training_sample_ids
            or set(self.training_sample_ids) & set(self.target_sample_ids)):
            raise ValueError("held-out targets cannot enter their own training roster")


@dataclass(frozen=True, slots=True)
class HistoricalScienceV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/historical/science"
    science_id: str
    source: ObjectIdentity
    folds: tuple[HistoricalFoldV1, ...]
    substitutions: tuple[ReportedSubstitutionV1, ...]
    ridge_penalty: Decimal = Decimal(1)
    turnover_relative_tolerance: Decimal = Decimal("0.10")
    specificity_relative_tolerance: Decimal = Decimal("0.03")
    claim_scope: str = CLAIM_SCOPE

    def __post_init__(self) -> None:
        validate_stable_id(self.science_id, field_name="science_id")
        if not isinstance(self.source, ObjectIdentity):
            raise ValueError("historical science needs an exact source identity")
        _typed_roster(self.folds, HistoricalFoldV1, "fold_id", maximum=5)
        _typed_roster(self.substitutions, ReportedSubstitutionV1, "sample_id", maximum=128)
        if (self.ridge_penalty != Decimal(1) or not isinstance(self.ridge_penalty, Decimal)
            or self.turnover_relative_tolerance != Decimal("0.10")
            or not isinstance(self.turnover_relative_tolerance, Decimal)
            or self.specificity_relative_tolerance != Decimal("0.03")
            or not isinstance(self.specificity_relative_tolerance, Decimal)
            or self.claim_scope != CLAIM_SCOPE):
            raise ValueError("historical E1 changes its fixed estimator, point gates or claim ceiling")
        by_id = {sample.sample_id: sample for sample in self.substitutions}
        required = {sample for fold in self.folds for sample in (*fold.training_sample_ids, *fold.target_sample_ids)}
        if required != set(by_id):
            raise ValueError("historical design must retain exactly its declared feature roster")
        targets = tuple(sample for fold in self.folds for sample in fold.target_sample_ids)
        if len(set(targets)) != len(targets):
            raise ValueError("repeated targets do not create additional table contrasts")
        if any(by_id[fold.parent_anchor_sample_id].substitution != "WT" for fold in self.folds):
            raise ValueError("historical folds need their WT parent in training")


@dataclass(frozen=True, slots=True)
class HistoricalFittedModelV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/historical/fitted-model"
    model_id: str
    science: ObjectIdentity
    training: HistoricalTrainingSliceV1
    parent: ReportedEndpointsV1
    ridge_coefficients: tuple[tuple[Decimal, Decimal], ...]
    calibration_status: str = CALIBRATION_STATUS

    def __post_init__(self) -> None:
        validate_stable_id(self.model_id, field_name="model_id")
        if not isinstance(self.science, ObjectIdentity) or self.science.object_schema != HistoricalScienceV1.SCHEMA:
            raise ValueError("historical model changes its exact scientific design")
        if (not isinstance(self.training, HistoricalTrainingSliceV1)
            or not isinstance(self.parent, ReportedEndpointsV1) or self.parent not in self.training.endpoints
            or not isinstance(self.ridge_coefficients, tuple) or len(self.ridge_coefficients) != 20):
            raise ValueError("historical model changes parent, training role or fixed feature dimension")
        parent_feature = next(f for f in self.training.features if f.sample_id == self.parent.sample_id)
        if parent_feature.substitution != "WT":
            raise ValueError("historical model's measured parent must be WT")
        for pair in self.ridge_coefficients:
            if not isinstance(pair, tuple) or len(pair) != 2:
                raise ValueError("ridge model needs two endpoint coefficients per feature")
            for coefficient in pair:
                validate_decimal(coefficient, field_name="coefficient")
        if self.calibration_status != CALIBRATION_STATUS:
            raise ValueError("historical model cannot manufacture interval calibration")


@dataclass(frozen=True, slots=True)
class HistoricalForecastV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/historical/forecast"
    forecast_id: str
    method: BaselineV1
    endpoints: ReportedEndpointsV1
    model: ObjectIdentity
    target_features: ObjectIdentity

    def __post_init__(self) -> None:
        validate_stable_id(self.forecast_id, field_name="forecast_id")
        if not isinstance(self.method, BaselineV1) or not isinstance(self.endpoints, ReportedEndpointsV1):
            raise ValueError("historical forecast requires a declared method and paired endpoints")
        if (not isinstance(self.model, ObjectIdentity)
            or self.model.object_schema != HistoricalFittedModelV1.SCHEMA
            or not isinstance(self.target_features, ObjectIdentity)
            or self.target_features.object_schema != HistoricalFeatureSliceV1.SCHEMA):
            raise ValueError("historical forecast changes model or feature information roles")


@dataclass(frozen=True, slots=True)
class HistoricalFoldForecastsV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/historical/fold-forecasts"
    fold_id: str
    forecasts: tuple[HistoricalForecastV1, ...]

    def __post_init__(self) -> None:
        validate_stable_id(self.fold_id, field_name="fold_id")
        _typed_roster(self.forecasts, HistoricalForecastV1, "forecast_id", maximum=384)
        if len({f.model for f in self.forecasts}) != 1 or len({f.target_features for f in self.forecasts}) != 1:
            raise ValueError("fold forecasts must share their exact model and target-feature slice")


@dataclass(frozen=True, slots=True)
class HistoricalForecastCommitmentV1(CanonicalRecord):
    """All-fold forecast closure supplied before the evaluation label port."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/historical/global-forecast-commitment"
    commitment_id: str
    science: ObjectIdentity
    fold_forecasts: tuple[HistoricalFoldForecastsV1, ...]
    prior_biological_exposure: str = "EXPOSED_HISTORICAL_TABLE"
    barrier_semantics: str = "ALL_REQUIRED_SOFTWARE_FORECASTS_BEFORE_EVALUATION_LABEL_ACCESS"

    def __post_init__(self) -> None:
        validate_stable_id(self.commitment_id, field_name="commitment_id")
        if not isinstance(self.science, ObjectIdentity) or self.science.object_schema != HistoricalScienceV1.SCHEMA:
            raise ValueError("forecast commitment changes scientific design identity")
        _typed_roster(self.fold_forecasts, HistoricalFoldForecastsV1, "fold_id", maximum=5)
        if (self.prior_biological_exposure != "EXPOSED_HISTORICAL_TABLE"
            or self.barrier_semantics != "ALL_REQUIRED_SOFTWARE_FORECASTS_BEFORE_EVALUATION_LABEL_ACCESS"):
            raise ValueError("software forecast commitment cannot erase biological exposure")


@dataclass(frozen=True, slots=True)
class HistoricalPointErrorV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/historical/point-error"
    forecast: HistoricalForecastV1
    observed: ReportedEndpointsV1
    turnover_relative_error: Decimal
    specificity_relative_error: Decimal
    turnover_log_contrast_error: Decimal
    specificity_log_contrast_error: Decimal
    jointly_within_point_tolerance: bool

    def __post_init__(self) -> None:
        if not isinstance(self.forecast, HistoricalForecastV1) or not isinstance(self.observed, ReportedEndpointsV1):
            raise ValueError("point error changes forecast or evaluation-label type")
        if self.forecast.endpoints.sample_id != self.observed.sample_id:
            raise ValueError("forecast and observed sample differ")
        for name in ("turnover_relative_error", "specificity_relative_error"):
            validate_decimal(getattr(self, name), field_name=name, minimum=Decimal(0))
        for name in ("turnover_log_contrast_error", "specificity_log_contrast_error"):
            validate_decimal(getattr(self, name), field_name=name)
        with localcontext(numerical_context()):
            ratios = (self.forecast.endpoints.turnover_s_inv / self.observed.turnover_s_inv,
                      self.forecast.endpoints.specificity_dimensionless / self.observed.specificity_dimensionless)
            expected = (abs(ratios[0] - 1), abs(ratios[1] - 1), ratios[0].ln(), ratios[1].ln())
            actual = (self.turnover_relative_error, self.specificity_relative_error,
                      self.turnover_log_contrast_error, self.specificity_log_contrast_error)
            if actual != expected or self.jointly_within_point_tolerance is not (
                    expected[0] <= Decimal("0.10") and expected[1] <= Decimal("0.03")):
                raise ValueError("point-error fields disagree with exact forecast/label operands")


@dataclass(frozen=True, slots=True)
class HistoricalEvaluationV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/historical/evaluation"
    evaluation_id: str
    commitment: ObjectIdentity
    errors: tuple[HistoricalPointErrorV1, ...]
    paired_table_contrasts: int
    all_methods_identical: bool
    independent_biological_units: int = 0
    joint_coverage: Decimal | None = None
    interval_width: Decimal | None = None
    biological_gate: str = BIOLOGICAL_GATE

    def __post_init__(self) -> None:
        validate_stable_id(self.evaluation_id, field_name="evaluation_id")
        if (not isinstance(self.commitment, ObjectIdentity)
            or self.commitment.object_schema != HistoricalForecastCommitmentV1.SCHEMA):
            raise ValueError("historical evaluation requires its global forecast commitment")
        if (not isinstance(self.errors, tuple) or not 1 <= len(self.errors) <= 1920
            or any(not isinstance(e, HistoricalPointErrorV1) for e in self.errors)
            or type(self.paired_table_contrasts) is not int
            or self.paired_table_contrasts * len(BaselineV1) != len(self.errors)
            or type(self.independent_biological_units) is not int or self.independent_biological_units != 0
            or self.joint_coverage is not None or self.interval_width is not None
            or self.biological_gate != BIOLOGICAL_GATE):
            raise ValueError("point diagnostics cannot establish biological replication or coverage")
        by_sample = {}
        for error in self.errors:
            by_sample.setdefault(error.observed.sample_id, []).append(error)
        if len(by_sample) != self.paired_table_contrasts or any(
                len(group) != len(BaselineV1) or {e.forecast.method for e in group} != set(BaselineV1)
                or len({e.observed for e in group}) != 1 for group in by_sample.values()):
            raise ValueError("historical evaluation loses its complete method/contrast denominator")
        identical = all(len({(e.forecast.endpoints.turnover_s_inv,
                              e.forecast.endpoints.specificity_dimensionless) for e in group}) == 1
                        for group in by_sample.values())
        if self.all_methods_identical is not identical:
            raise ValueError("historical model agreement differs from complete forecasts")


@dataclass(frozen=True, slots=True)
class ScalarPassIntervalV1(CanonicalRecord):
    """Finite, all-real, empty or numerically unresolved scalar set."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/historical/scalar-pass-interval"
    state: str
    lower: Decimal | None
    upper: Decimal | None

    def __post_init__(self) -> None:
        if self.state not in ("FINITE", "ALL_REAL", "EMPTY", "UNRESOLVED"):
            raise ValueError("unknown scalar interval state")
        if self.state == "FINITE":
            validate_decimal(self.lower, field_name="scalar_lower")
            validate_decimal(self.upper, field_name="scalar_upper")
            if self.lower > self.upper:
                raise ValueError("finite scalar interval is reversed")
        elif self.lower is not None or self.upper is not None:
            raise ValueError("unbounded or empty scalar sets have no finite bounds")


@dataclass(frozen=True, slots=True)
class RankOneFeasibilityV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/historical/rank-one-feasibility"
    parent: ReportedEndpointsV1
    training_mutant: ReportedEndpointsV1
    target: ReportedEndpointsV1
    training_log_contrasts: tuple[Decimal, Decimal]
    turnover_scalar_interval: ScalarPassIntervalV1
    specificity_scalar_interval: ScalarPassIntervalV1
    disposition: str
    reason_codes: tuple[str, ...]
    numerical_precision_digits: int = 50
    claim_scope: str = "ONE_NONZERO_TRAINING_RESPONSE_SHARED_LINEAR_MAP_ONLY"

    def __post_init__(self) -> None:
        if any(not isinstance(e, ReportedEndpointsV1) for e in (self.parent, self.training_mutant, self.target)):
            raise ValueError("rank-one diagnostic needs explicit endpoint operands")
        if len({e.sample_id for e in (self.parent, self.training_mutant, self.target)}) != 3:
            raise ValueError("rank-one diagnostic needs distinct parent, training and target identities")
        if not isinstance(self.training_log_contrasts, tuple) or len(self.training_log_contrasts) != 2:
            raise ValueError("rank-one diagnostic needs both response directions")
        for value in self.training_log_contrasts:
            validate_decimal(value, field_name="training_log_contrast")
        if (not isinstance(self.turnover_scalar_interval, ScalarPassIntervalV1)
            or not isinstance(self.specificity_scalar_interval, ScalarPassIntervalV1)
            or self.disposition not in ("INCOMPATIBLE", "ATTAINABLE", "UNRESOLVED_NUMERICAL_BOUNDARY")
            or type(self.numerical_precision_digits) is not int or self.numerical_precision_digits != 50
            or self.claim_scope != "ONE_NONZERO_TRAINING_RESPONSE_SHARED_LINEAR_MAP_ONLY"):
            raise ValueError("rank-one diagnostic extends beyond its specified shared linear design")
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes", allow_empty=False)
