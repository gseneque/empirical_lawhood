# SPDX-License-Identifier: MPL-2.0
"""Source-bound E3 methods over complete exposed causal and paired-view banks.

The arithmetic methods reuse the shared experimental-statistics owner. Native
feature equations and independent numerical assessments remain with their
existing Matrix owners. These exposed products provide no fresh qualification.
"""

from dataclasses import dataclass, replace
from decimal import Decimal
from typing import ClassVar

from empirical_lawhood.kernel.experimental_design import UnitAllocation
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord, require_sorted_unique_ids, validate_decimal, validate_sha256, validate_stable_id,
)
from empirical_lawhood.planning.campaigns import CampaignSpec
from empirical_lawhood.runtime.experimental_statistics import (
    StandardizedRidgeParameters, binomial_upper_tail, split_upper_calibration,
)

from .experiment_specification import DESCRIPTIONS, HORIZONS, MatrixResponseErrorSpecification
from .response_error_prediction import FEATURES, FEATURE_BLOCKS as FEATURE_BLOCKS
from . import e3_numerical_methods as numerical

_log = numerical.log_error
_original_units = numerical.original_units


STANDING = "EXPOSED_CONFORMANCE_NONPROMOTABLE"
ENDPOINTS = tuple((description, horizon) for description in DESCRIPTIONS for horizon in HORIZONS)
METHODS = ("ALL_ORIGIN_RIDGE", "RAW_TRAIN_MEDIAN", "SPECTRAL_RIDGE")
FEATURE_DISPOSITIONS = ("AVAILABLE", "NO_CAUSAL_ORIGIN", "UNAVAILABLE", "REFUSED", "UNSUPPORTED")
OUTCOME_DISPOSITIONS = ("FINITE", "NO_CAUSAL_ORIGIN", "UNKNOWN_CONTACT", "NUMERICAL_FAILURE", "UNAVAILABLE", "REFUSED")


def identity(record):
    return ObjectIdentity.from_record(record.record_id, record)


def _identity(value, schema=None):
    if type(value) is not ObjectIdentity or schema is not None and value.object_schema != schema:
        raise ValueError("Matrix experiment substitutes an immutable scientific reference")


def _values(values, *, count, nonnegative=False):
    if type(values) is not tuple or len(values) != count:
        raise ValueError("Matrix experiment thins its complete endpoint/feature scope")
    for value in values:
        if value is not None:
            validate_decimal(value, field_name="Matrix experiment value", minimum=Decimal(0) if nonnegative else None)


def _bank_projection_references(bank):
    if (bank.original_bank is None) != (bank.original_allocation is None):
        raise ValueError("selected bank must retain both original bank and source allocation references")
    if bank.original_bank is not None:
        _identity(bank.original_bank, bank.SCHEMA)
        _identity(bank.original_allocation, UnitAllocation.SCHEMA)


@dataclass(frozen=True, slots=True)
class MatrixE3CausalFeature(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/causal-feature"
    record_id: str
    unit_id: str
    source_manifest: ObjectIdentity
    native_source: ObjectIdentity
    origin: ObjectIdentity
    clock_id: str
    cutoff: Decimal
    frame_sha256: str
    disposition: str
    values: tuple[tuple[str, Decimal], ...]
    evidence: tuple[ObjectIdentity, ...]
    standing: str = STANDING

    def __post_init__(self):
        for value in (self.record_id, self.unit_id, self.clock_id):
            validate_stable_id(value)
        for value in (self.source_manifest, self.native_source, self.origin):
            _identity(value)
        validate_sha256(self.frame_sha256)
        validate_decimal(self.cutoff, field_name="causal cutoff", minimum=Decimal(0))
        require_sorted_unique_ids(self.evidence, attribute="object_id", field_name="causal feature evidence")
        if (self.disposition not in FEATURE_DISPOSITIONS or not self.evidence or self.standing != STANDING
                or (tuple(name for name, _ in self.values) != FEATURES if self.disposition == "AVAILABLE" else bool(self.values))):
            raise ValueError("causal feature substitutes full origin information, evidence or disposition")
        for _, value in self.values:
            validate_decimal(value, field_name="causal feature", minimum=Decimal(0))
        if self.disposition == "AVAILABLE" and dict(self.values)["cutoff"] != self.cutoff:
            raise ValueError("causal feature changes its actual information cutoff")


@dataclass(frozen=True, slots=True)
class MatrixE3FeatureBank(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/feature-bank"
    record_id: str
    allocation: ObjectIdentity
    role: str
    rows: tuple[MatrixE3CausalFeature, ...]
    standing: str = STANDING
    original_bank: ObjectIdentity | None = None
    original_allocation: ObjectIdentity | None = None

    def __post_init__(self):
        validate_stable_id(self.record_id)
        _identity(self.allocation, UnitAllocation.SCHEMA)
        if self.role not in ("train", "calibration", "evaluation") or self.standing != STANDING:
            raise ValueError("feature bank changes its whole-unit role or exposed standing")
        require_sorted_unique_ids(self.rows, attribute="unit_id", field_name="complete feature bank")
        if not self.rows or any(type(row) is not MatrixE3CausalFeature for row in self.rows):
            raise ValueError("feature bank requires typed complete causal observations")
        _bank_projection_references(self)


@dataclass(frozen=True, slots=True)
class MatrixE3ViewOutcome(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/view-outcome"
    view_id: str
    errors: tuple[Decimal | None, ...]
    dispositions: tuple[str, ...]

    def __post_init__(self):
        _values(self.errors, count=15, nonnegative=True)
        if self.view_id not in ("fine", "primary") or len(self.dispositions) != 15:
            raise ValueError("paired outcome changes its fixed view or all15 endpoint denominator")
        for index, (value, disposition) in enumerate(zip(self.errors, self.dispositions, strict=True)):
            if disposition not in OUTCOME_DISPOSITIONS or (value is not None) != (disposition == "FINITE"):
                raise ValueError("paired outcome manufactures a finite nonuse/unknown observation")
            if index % 3 and value is not None and (self.errors[index-1] is None or value < self.errors[index-1]):
                raise ValueError("paired outcome changes cumulative horizon accounting")


@dataclass(frozen=True, slots=True)
class MatrixE3PairedOutcome(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/paired-outcome"
    record_id: str
    unit_id: str
    source_manifest: ObjectIdentity
    native_source: ObjectIdentity
    origin: ObjectIdentity
    clock_id: str
    cutoff: Decimal
    frame_sha256: str
    views: tuple[MatrixE3ViewOutcome, ...]
    numerical_disposition: str
    evidence: tuple[ObjectIdentity, ...]
    standing: str = STANDING

    def __post_init__(self):
        for value in (self.record_id, self.unit_id, self.clock_id):
            validate_stable_id(value)
        for value in (self.source_manifest, self.native_source, self.origin):
            _identity(value)
        validate_sha256(self.frame_sha256)
        validate_decimal(self.cutoff, field_name="paired response cutoff", minimum=Decimal(0))
        require_sorted_unique_ids(self.evidence, attribute="object_id", field_name="paired outcome evidence")
        if (tuple(view.view_id for view in self.views) != ("fine", "primary")
                or any(type(view) is not MatrixE3ViewOutcome for view in self.views)
                or self.numerical_disposition not in ("SATISFIED", "VIOLATED", "UNEVALUABLE")
                or not self.evidence or self.standing != STANDING):
            raise ValueError("paired outcome loses views, original numerical disposition or evidence")

    def view(self, view_id):
        return next(view for view in self.views if view.view_id == view_id)


@dataclass(frozen=True, slots=True)
class MatrixE3OutcomeBank(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/outcome-bank"
    record_id: str
    allocation: ObjectIdentity
    role: str
    rows: tuple[MatrixE3PairedOutcome, ...]
    standing: str = STANDING
    original_bank: ObjectIdentity | None = None
    original_allocation: ObjectIdentity | None = None

    def __post_init__(self):
        validate_stable_id(self.record_id)
        _identity(self.allocation, UnitAllocation.SCHEMA)
        if self.role not in ("train", "calibration", "evaluation") or self.standing != STANDING:
            raise ValueError("outcome bank changes its whole-unit role or exposed standing")
        require_sorted_unique_ids(self.rows, attribute="unit_id", field_name="complete outcome bank")
        if not self.rows or any(type(row) is not MatrixE3PairedOutcome for row in self.rows):
            raise ValueError("outcome bank requires complete typed paired observations")
        _bank_projection_references(self)


@dataclass(frozen=True, slots=True)
class MatrixE3MethodInputs:
    campaign: CampaignSpec | None
    features: tuple[MatrixE3FeatureBank, ...]
    outcomes: tuple[MatrixE3OutcomeBank, ...]

    def __post_init__(self):
        if self.campaign is not None and type(self.campaign) is not CampaignSpec:
            raise TypeError("Matrix method inputs require the selected scientific campaign")
        for rows, kind in ((self.features, MatrixE3FeatureBank), (self.outcomes, MatrixE3OutcomeBank)):
            if type(rows) is not tuple or any(type(row) is not kind for row in rows) or len({row.role for row in rows}) != len(rows):
                raise ValueError("Matrix method inputs duplicate or substitute source banks")


def _validate_row(specification, allocation, row):
    unit = allocation.unit(row.unit_id)
    if (unit is None or not unit.exposed or row.source_manifest not in allocation.sources
            or row.source_manifest.object_id != unit.source_id
            or row.cutoff != specification.measurement.origin_tick * specification.measurement.primary_timestep):
        raise ValueError("Matrix source row substitutes actual source, exposed unit or physical cutoff")
    if type(row) is MatrixE3CausalFeature and row.disposition == "AVAILABLE":
        values = dict(row.values)
        families = {
            "family-de-anneal": "matrix-history.joint-decreasing-coupling",
            "family-x-first": "matrix-history.x-first-increasing-coupling",
            "family-y-first": "matrix-history.y-first-increasing-coupling",
        }
        if any(values[name] != Decimal(unit.family_id == family) for name, family in families.items()):
            raise ValueError("causal feature substitutes its actual preparation family")


def validate_bank(specification, allocation, bank):
    specification.__post_init__()
    allocation.__post_init__()
    bank.__post_init__()
    if specification.evidence_scope != "EXPOSED_CONFORMANCE":
        raise ValueError("exposed method banks cannot enter a protected scientific workflow")
    if bank.allocation != allocation.identity or tuple(row.unit_id for row in bank.rows) != allocation.unit_ids(bank.role):
        raise ValueError("Matrix source bank drops, duplicates or crosses complete allocated whole-unit roles")
    for row in bank.rows:
        _validate_row(specification, allocation, row)


def project_source_bank(specification, allocation, source_allocation, bank):
    """Authenticate complete original membership before deriving selected rows."""
    source_allocation.__post_init__()
    bank.__post_init__()
    if bank.allocation == allocation.identity:
        validate_bank(specification, allocation, bank)
        if bank.original_allocation is not None and bank.original_allocation != source_allocation.identity:
            raise ValueError("selected bank substitutes its original source allocation")
        return bank
    if bank.allocation != source_allocation.identity or bank.original_bank is not None:
        raise ValueError("original source bank lacks its exact supplied source allocation binding")
    if tuple(row.unit_id for row in bank.rows) != tuple(unit.unit_id for unit in source_allocation.units):
        raise ValueError("original source bank drops, duplicates or adds complete source roster members")
    for row in bank.rows:
        _validate_row(specification, source_allocation, row)
    selected = set(allocation.unit_ids(bank.role))
    rows = tuple(row for row in bank.rows if row.unit_id in selected)
    if tuple(row.unit_id for row in rows) != allocation.unit_ids(bank.role):
        raise ValueError("selected bank cannot bind every originally selected whole unit")
    return replace(bank, record_id="bank.matrix-e3." + specification.fingerprint() + "." + bank.fingerprint(),
        allocation=allocation.identity, rows=rows, original_bank=identity(bank), original_allocation=source_allocation.identity)


def project_method_inputs(specification, allocation, scientific_inputs, method_inputs):
    """Pure projection of authenticated original banks, preserving missing inputs."""
    def project(bank):
        selection = specification.population(bank.role.upper())
        original_allocation = scientific_inputs.get(selection.source_key)
        if type(original_allocation) is not UnitAllocation:
            raise ValueError("source bank lacks its actual original source allocation")
        return project_source_bank(specification, allocation, original_allocation, bank)
    return replace(method_inputs, features=tuple(project(bank) for bank in method_inputs.features),
        outcomes=tuple(project(bank) for bank in method_inputs.outcomes))


def validate_pair(feature, outcome):
    if any(getattr(feature, name) != getattr(outcome, name) for name in (
            "unit_id", "source_manifest", "native_source", "origin", "clock_id", "cutoff", "frame_sha256")):
        raise ValueError("Matrix paired response changes its PRIMARY causal source/origin/clock/frame")


def outcome_usable(specification, outcome):
    return numerical.outcome_reasons(specification, outcome)


@dataclass(frozen=True, slots=True)
class MatrixE3EstimatorModel(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/estimator-model"
    method_key: str
    feature_names: tuple[str, ...]
    ridge_parameters: tuple[StandardizedRidgeParameters | None, ...]
    raw_constants: tuple[Decimal | None, ...]
    training_unit_ids: tuple[str, ...]
    finite_counts: tuple[int, ...]

    def __post_init__(self):
        if (self.method_key not in METHODS or len(self.ridge_parameters) != 15 or len(self.raw_constants) != 15
                or len(self.finite_counts) != 15 or not self.training_unit_ids
                or self.training_unit_ids != tuple(sorted(set(self.training_unit_ids)))
                or any(type(count) is not int or not 0 <= count <= len(self.training_unit_ids) for count in self.finite_counts)):
            raise ValueError("fitted estimator changes its complete training/endpoint denominator")
        if self.method_key == "RAW_TRAIN_MEDIAN":
            if self.feature_names or any(parameter is not None for parameter in self.ridge_parameters):
                raise ValueError("raw TRAIN median cannot substitute a feature regression")
            _values(self.raw_constants, count=15, nonnegative=True)
            if any((value is None) != (count == 0) for value, count in zip(self.raw_constants, self.finite_counts, strict=True)):
                raise ValueError("raw TRAIN median loses missing training targets")
        else:
            if any(value is not None for value in self.raw_constants) or not self.feature_names:
                raise ValueError("ridge estimator substitutes raw constant targets")
            for parameter, count in zip(self.ridge_parameters, self.finite_counts, strict=True):
                if parameter is None:
                    if count:
                        raise ValueError("ridge estimator omits fitted coefficients")
                elif type(parameter) is not StandardizedRidgeParameters or parameter.fitted_rows != count or len(parameter.means) != len(self.feature_names):
                    raise ValueError("ridge parameters differ from the finite training or feature census")


@dataclass(frozen=True, slots=True)
class MatrixE3ModelSet(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/model-set"
    record_id: str
    specification: ObjectIdentity
    allocation: ObjectIdentity
    training_features: ObjectIdentity
    training_outcomes: ObjectIdentity
    models: tuple[MatrixE3EstimatorModel, ...]
    standing: str = STANDING

    def __post_init__(self):
        validate_stable_id(self.record_id)
        for reference, schema in ((self.specification, MatrixResponseErrorSpecification.SCHEMA), (self.allocation, UnitAllocation.SCHEMA),
                (self.training_features, MatrixE3FeatureBank.SCHEMA), (self.training_outcomes, MatrixE3OutcomeBank.SCHEMA)):
            _identity(reference, schema)
        if tuple(model.method_key for model in self.models) != METHODS or self.standing != STANDING:
            raise ValueError("model set changes selected predictor/baselines or exposed standing")


def fit_models(specification, allocation, features, outcomes, *, record_id):
    validate_bank(specification, allocation, features)
    validate_bank(specification, allocation, outcomes)
    if features.role != "train" or outcomes.role != "train":
        raise ValueError("model fitting receives only assigned TRAIN observations")
    fs, ys = {row.unit_id: row for row in features.rows}, {row.unit_id: row for row in outcomes.rows}
    roots = allocation.unit_ids("train")
    for root in roots:
        validate_pair(fs[root], ys[root])
    models = tuple(MatrixE3EstimatorModel(*values)
        for values in numerical.fit_estimator_values(specification, roots, fs, ys))
    return MatrixE3ModelSet(record_id, specification.identity, allocation.identity, identity(features), identity(outcomes), models)


@dataclass(frozen=True, slots=True)
class MatrixE3FrozenProducts(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/frozen-products"
    record_id: str
    specification: ObjectIdentity
    allocation: ObjectIdentity
    models: ObjectIdentity
    calibration: ObjectIdentity | None
    model_freeze: ObjectIdentity | None
    standing: str = STANDING

    def __post_init__(self):
        validate_stable_id(self.record_id)
        _identity(self.specification, MatrixResponseErrorSpecification.SCHEMA)
        _identity(self.allocation, UnitAllocation.SCHEMA)
        _identity(self.models, MatrixE3ModelSet.SCHEMA)
        if (self.calibration is None) != (self.model_freeze is None) or self.standing != STANDING:
            raise ValueError("frozen products lose fitted-before-calibration ordering")
        if self.calibration is not None:
            _identity(self.calibration, MatrixE3Calibration.SCHEMA)
            _identity(self.model_freeze, self.SCHEMA)


@dataclass(frozen=True, slots=True)
class MatrixE3Forecast(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/forecast"
    record_id: str
    specification: ObjectIdentity
    allocation: ObjectIdentity
    frozen_products: ObjectIdentity
    feature: MatrixE3CausalFeature
    role: str
    log_points: tuple[tuple[str, tuple[Decimal | None, ...]], ...]
    radius: Decimal | None
    radius_kind: str = "UNCALIBRATED"
    standing: str = STANDING

    def __post_init__(self):
        validate_stable_id(self.record_id)
        _identity(self.specification, MatrixResponseErrorSpecification.SCHEMA)
        _identity(self.allocation, UnitAllocation.SCHEMA)
        _identity(self.frozen_products, MatrixE3FrozenProducts.SCHEMA)
        if (self.role not in ("calibration", "evaluation") or tuple(method for method, _ in self.log_points) != METHODS
                or self.standing != STANDING or self.role == "calibration" and self.radius is not None):
            raise ValueError("forecast substitutes selected methods, role or calibrated scope")
        expected_kind = "UNCALIBRATED" if self.role == "calibration" else "INFINITE" if self.radius is None else "FINITE"
        if self.radius_kind != expected_kind:
            raise ValueError("forecast relabels an infinite or uncalibrated bound")
        for _, values in self.log_points:
            _values(values, count=15, nonnegative=True)
            if self.feature.disposition != "AVAILABLE" and any(value is not None for value in values):
                raise ValueError("forecast manufactures predictions without a causal origin")
            for index, value in enumerate(values):
                if index % 3 and value is not None and (values[index-1] is None or value < values[index-1]):
                    raise ValueError("forecast drops earlier nonuse or cumulative horizon maxima")
        if self.radius is not None:
            validate_decimal(self.radius, field_name="finite calibrated log radius", minimum=Decimal(0))


def forecast(specification, allocation, models, frozen, feature, *, role, record_id, calibration=None):
    if (models.specification != specification.identity or models.allocation != allocation.identity
            or frozen.specification != specification.identity or frozen.allocation != allocation.identity
            or frozen.models != identity(models) or feature.unit_id not in allocation.unit_ids(role)):
        raise ValueError("forecast substitutes frozen fit, source or exact allocated role")
    _validate_row(specification, allocation, feature)
    if role == "calibration":
        if frozen.calibration is not None or calibration is not None:
            raise ValueError("calibration point forecast cannot use calibration outcomes")
        radius = None
    else:
        if (calibration is None or frozen.calibration != identity(calibration)
                or calibration.models != identity(models) or calibration.specification != specification.identity
                or calibration.allocation != allocation.identity):
            raise ValueError("evaluation requires the separately frozen calibrated products")
        radius = calibration.radius
    points = numerical.forecast_point_values(models.models, feature)
    return MatrixE3Forecast(record_id, specification.identity, allocation.identity, identity(frozen), feature, role, tuple(points), radius,
        "UNCALIBRATED" if role == "calibration" else "INFINITE" if radius is None else "FINITE")


@dataclass(frozen=True, slots=True)
class MatrixE3ObservedOutcome(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/observed-outcome"
    record_id: str
    forecast: ObjectIdentity
    outcome: MatrixE3PairedOutcome
    standing: str = STANDING

    def __post_init__(self):
        validate_stable_id(self.record_id)
        _identity(self.forecast, MatrixE3Forecast.SCHEMA)
        if type(self.outcome) is not MatrixE3PairedOutcome or self.standing != STANDING:
            raise ValueError("outcome release changes its exposed paired source")


def observe(forecast_record, outcome, *, record_id):
    validate_pair(forecast_record.feature, outcome)
    return MatrixE3ObservedOutcome(record_id, identity(forecast_record), outcome)


@dataclass(frozen=True, slots=True)
class MatrixE3Calibration(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/calibration"
    record_id: str
    specification: ObjectIdentity
    allocation: ObjectIdentity
    models: ObjectIdentity
    model_freeze: ObjectIdentity
    target_view: str
    scores: tuple[tuple[str, Decimal | None, tuple[str, ...]], ...]
    rank: int
    radius: Decimal | None
    forecasts: tuple[ObjectIdentity, ...]
    outcomes: tuple[ObjectIdentity, ...]
    radius_kind: str = "FINITE"
    standing: str = STANDING

    def __post_init__(self):
        validate_stable_id(self.record_id)
        for value, schema in ((self.specification, MatrixResponseErrorSpecification.SCHEMA), (self.allocation, UnitAllocation.SCHEMA),
                (self.models, MatrixE3ModelSet.SCHEMA), (self.model_freeze, MatrixE3FrozenProducts.SCHEMA)):
            _identity(value, schema)
        if (self.target_view not in ("PRIMARY", "MAX_PAIRED_VIEWS") or not self.scores
                or tuple(row[0] for row in self.scores) != tuple(sorted({row[0] for row in self.scores}))
                or len(self.forecasts) != len(self.scores) or len(self.outcomes) != len(self.scores)
                or type(self.rank) is not int or self.rank < 1 or self.standing != STANDING):
            raise ValueError("calibration changes complete unit scores, selected view or frozen ancestry")
        if self.radius_kind != ("INFINITE" if self.radius is None else "FINITE"):
            raise ValueError("calibration relabels its infinite order statistic")
        for _, score, reasons in self.scores:
            if score is not None:
                validate_decimal(score, field_name="whole-unit calibration score", minimum=Decimal(0))
            if not reasons or reasons != tuple(sorted(set(reasons))):
                raise ValueError("calibration drops explicit finite/nonuse score reasons")
        if self.radius is not None:
            validate_decimal(self.radius, field_name="calibrated radius", minimum=Decimal(0))


def calibrate(specification, allocation, models, frozen, forecasts, outcomes, *, record_id):
    if specification.calibration_target_view is None:
        raise ValueError("calibration target view remains an unresolved scientific selection")
    expected = allocation.unit_ids("calibration")
    fs = {row.feature.unit_id: row for row in forecasts}
    ys = {row.outcome.unit_id: row for row in outcomes}
    if (len(fs) != len(forecasts) or len(ys) != len(outcomes) or tuple(sorted(fs)) != expected or tuple(sorted(ys)) != expected
            or frozen.models != identity(models) or frozen.calibration is not None):
        raise ValueError("calibration loses the full assigned unit or pre-calibration model freeze")
    scores = []
    for unit in expected:
        f, observed = fs[unit], ys[unit]
        if (f.role != "calibration" or f.specification != specification.identity or f.allocation != allocation.identity
                or f.frozen_products != identity(frozen) or observed.forecast != identity(f)):
            raise ValueError("calibration substitutes a future-informed or foreign forecast")
        validate_pair(f.feature, observed.outcome)
        reasons = list(outcome_usable(specification, observed.outcome))
        if f.feature.disposition != "AVAILABLE":
            reasons.append(f.feature.disposition)
        score, tags = numerical.calibration_score(specification, f.log_points, observed.outcome, reasons)
        scores.append((unit, score, tags))
    ranked = split_upper_calibration(tuple(row[1] for row in scores), specification.calibration_alpha)
    radius = None if ranked.radius.is_infinite() else ranked.radius
    return MatrixE3Calibration(record_id, specification.identity, allocation.identity, identity(models), identity(frozen),
        specification.calibration_target_view, tuple(scores), ranked.rank, radius,
        tuple(identity(fs[unit]) for unit in expected), tuple(identity(ys[unit]) for unit in expected),
        "INFINITE" if radius is None else "FINITE")


def freeze(specification, allocation, models, *, record_id, model_freeze=None, calibration=None):
    if models.specification != specification.identity or models.allocation != allocation.identity:
        raise ValueError("freeze substitutes the selected fitted model set")
    if (model_freeze is None) != (calibration is None):
        raise ValueError("calibrated freeze needs its actual prior model freeze and calibration")
    if calibration is not None and (calibration.model_freeze != identity(model_freeze)
            or model_freeze.models != identity(models) or model_freeze.calibration is not None
            or calibration.models != identity(models) or calibration.specification != specification.identity
            or calibration.allocation != allocation.identity):
        raise ValueError("calibrated freeze refits or replaces its original model/score lineage")
    return MatrixE3FrozenProducts(record_id, specification.identity, allocation.identity, identity(models),
        None if calibration is None else identity(calibration), None if model_freeze is None else identity(model_freeze))


@dataclass(frozen=True, slots=True)
class MatrixE3RootDecision(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/root-decision"
    unit_id: str
    usable: bool
    success: bool
    comparisons: tuple[tuple[str, str, Decimal | None], ...]
    reasons: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.unit_id)
        if (type(self.usable) is not bool or type(self.success) is not bool or self.success and not self.usable
                or tuple((method, view) for method, view, _ in self.comparisons) !=
                    tuple((method, view) for method in ("ALL_ORIGIN_RIDGE", "RAW_TRAIN_MEDIAN") for view in ("fine", "primary"))
                or not self.reasons or self.reasons != tuple(sorted(set(self.reasons)))):
            raise ValueError("root decision changes both-baseline/both-view or nonuse census")
        for _, _, value in self.comparisons:
            if value is not None:
                validate_decimal(value, field_name="paired absolute-error improvement")


@dataclass(frozen=True, slots=True)
class MatrixE3Assessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/assessment"
    record_id: str
    specification: ObjectIdentity
    allocation: ObjectIdentity
    calibrated_freeze: ObjectIdentity
    decisions: tuple[MatrixE3RootDecision, ...]
    successes: int
    usable_units: int
    binomial_tail_numerator: int
    binomial_tail_denominator: int
    criterion_met: bool
    coverage: tuple[tuple[str, bool, tuple[Decimal | None, ...]], ...]
    coverage_bound_kinds: tuple[tuple[str, str], ...]
    standing: str = STANDING
    qualification: str = "NOT_ESTABLISHED"

    def __post_init__(self):
        validate_stable_id(self.record_id)
        _identity(self.specification, MatrixResponseErrorSpecification.SCHEMA)
        _identity(self.allocation, UnitAllocation.SCHEMA)
        _identity(self.calibrated_freeze, MatrixE3FrozenProducts.SCHEMA)
        if (not self.decisions or tuple(row.unit_id for row in self.decisions) != tuple(sorted({row.unit_id for row in self.decisions}))
                or self.successes != sum(row.success for row in self.decisions)
                or self.usable_units != sum(row.usable for row in self.decisions)
                or type(self.criterion_met) is not bool or self.binomial_tail_denominator < 1
                or not 0 <= self.binomial_tail_numerator <= self.binomial_tail_denominator
                or tuple(row[0] for row in self.coverage) != tuple(row.unit_id for row in self.decisions)
                or tuple(row[0] for row in self.coverage_bound_kinds) != tuple(row.unit_id for row in self.decisions)
                or any(kind not in ("FINITE", "INFINITE", "UNAVAILABLE") for _, kind in self.coverage_bound_kinds)
                or self.standing != STANDING or self.qualification != "NOT_ESTABLISHED"):
            raise ValueError("assessment changes complete decisions, arithmetic or exposed scientific standing")
        for _, covered, slacks in self.coverage:
            if type(covered) is not bool:
                raise ValueError("coverage requires an explicit whole-root disposition")
            _values(slacks, count=15, nonnegative=True)


def evaluate(specification, allocation, frozen, forecasts, outcomes, *, record_id):
    expected = allocation.unit_ids("evaluation")
    fs = {row.feature.unit_id: row for row in forecasts}
    ys = {row.outcome.unit_id: row for row in outcomes}
    if (len(fs) != len(forecasts) or len(ys) != len(outcomes) or tuple(sorted(fs)) != expected or tuple(sorted(ys)) != expected
            or frozen.calibration is None):
        raise ValueError("evaluation drops assigned roots or lacks the calibrated freeze")
    decisions, coverage, bound_kinds = [], [], []
    primary_index = ENDPOINTS.index((specification.measurement.primary_description, specification.measurement.primary_horizon))
    for unit in expected:
        f, observed = fs[unit], ys[unit]
        if (f.role != "evaluation" or f.frozen_products != identity(frozen) or observed.forecast != identity(f)
                or f.specification != specification.identity or f.allocation != allocation.identity):
            raise ValueError("evaluation replaces its pre-future forecast or frozen experiment")
        validate_pair(f.feature, observed.outcome)
        reasons = list(outcome_usable(specification, observed.outcome))
        if f.feature.disposition != "AVAILABLE":
            reasons.append(f.feature.disposition)
        point_menu = dict(f.log_points)
        usable, success, comparisons, tags = numerical.paired_root_decision(
            specification, point_menu, observed.outcome, primary_index, reasons)
        decisions.append(MatrixE3RootDecision(unit, usable, success, comparisons, tags))
        covered, slacks, kind = numerical.coverage_values(point_menu, observed.outcome, f.radius_kind, f.radius, usable)
        coverage.append((unit, covered, slacks))
        bound_kinds.append((unit, kind))
    successes = sum(row.success for row in decisions)
    usable_units = sum(row.usable for row in decisions)
    tail = binomial_upper_tail(len(expected), successes, specification.assessment.null_probability)
    criterion_met = tail <= specification.assessment.alpha and usable_units >= specification.assessment.minimum_usable_units
    return MatrixE3Assessment(record_id, specification.identity, allocation.identity, identity(frozen), tuple(decisions),
        successes, usable_units, tail.numerator, tail.denominator, criterion_met, tuple(coverage), tuple(bound_kinds))
