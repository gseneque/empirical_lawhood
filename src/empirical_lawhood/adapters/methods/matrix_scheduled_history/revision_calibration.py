# SPDX-License-Identifier: MPL-2.0
"""Separate whole-group calibration of the frozen E4 revision and baseline.

These pure scientific joins do not authenticate publication, source eligibility,
sampling assumptions or authority. The owning lifecycle must freeze the declared
models and forecasts before dependent outcomes and authenticate those records.
Historical scheduled calibration and development selection records stay exact.
"""

from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.kernel.time import CausalPhase, InformationCutoff
from empirical_lawhood.runtime.experimental_statistics import predict_standardized_ridge, split_upper_calibration

from .programme_records import ScheduledProgramme
from .records import ScheduledSource
from .programme_selection import (
    ScheduledRevisionFittedModel, ScheduledRevisionFrozenPackage, ScheduledRevisionNomination,
    ScheduledRevisionTarget,
    _exact_decimal, require_revision_for_future_phase, revision_case_features, validate_programme_paired_data,
)

SCORE_RULE = "WHOLE_GROUP_MAX_POSITIVE_PAIRED_LOG_RESIDUAL_NINE_COORDINATES_ALL30"


def _identity(record, field):
    return ObjectIdentity.from_record(getattr(record, field), record)


def _pin(value, schema, version="1.0.0"):
    if type(value) is not ObjectIdentity or value.object_schema != schema or value.object_version != version:
        raise ValueError("revision calibration substitutes an exact scientific input type")


@dataclass(frozen=True, slots=True)
class ScheduledRevisionCalibrationSpecification(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-scheduled-programme/revision-calibration-specification"
    specification_id: str
    development_programme: ObjectIdentity
    calibration_programme: ObjectIdentity
    nomination: ObjectIdentity
    frozen_models: ObjectIdentity
    alpha: Decimal
    score_rule: str

    def __post_init__(self):
        validate_stable_id(self.specification_id)
        for value in (self.development_programme, self.calibration_programme):
            _pin(value, ScheduledProgramme.SCHEMA, ScheduledProgramme.VERSION)
        _pin(self.nomination, ScheduledRevisionNomination.SCHEMA)
        _pin(self.frozen_models, ScheduledRevisionFrozenPackage.SCHEMA)
        if (type(self.alpha) is not Decimal or not self.alpha.is_finite() or not 0 < self.alpha < 1
                or self.score_rule != SCORE_RULE or self.development_programme == self.calibration_programme):
            raise ValueError("revision calibration needs an explicit whole-group rule and separate population")

    @property
    def identity(self):
        return _identity(self, "specification_id")


@dataclass(frozen=True, slots=True)
class ScheduledRevisionForecastSeal(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-scheduled-programme/revision-forecast-seal"
    record_id: str
    programme: ObjectIdentity
    case_id: str
    independent_group_id: str
    source: ObjectIdentity
    coordinate: ObjectIdentity
    cutoff: InformationCutoff
    frozen_models: ObjectIdentity
    revision_model: ObjectIdentity
    baseline_model: ObjectIdentity
    target: ObjectIdentity
    revision_predictions: tuple[Decimal, ...]
    baseline_predictions: tuple[Decimal, ...]

    def __post_init__(self):
        self._validate_operands(programme_schema=ScheduledProgramme.SCHEMA, programme_version=ScheduledProgramme.VERSION,
            source_schema=ScheduledSource.SCHEMA, source_version=ScheduledSource.VERSION,
            frozen_schema=ScheduledRevisionFrozenPackage.SCHEMA)

    def _validate_operands(self, *, programme_schema, programme_version, source_schema, source_version, frozen_schema):
        for value in (self.record_id, self.case_id, self.independent_group_id):
            validate_stable_id(value)
        _pin(self.programme, programme_schema, programme_version)
        _pin(self.frozen_models, frozen_schema)
        for value in (self.revision_model, self.baseline_model):
            _pin(value, ScheduledRevisionFittedModel.SCHEMA)
        _pin(self.source, source_schema, source_version)
        _pin(self.coordinate, "empirical-lawhood/simulators/six-matrix-response/parameter-coordinate")
        _pin(self.target, ScheduledRevisionTarget.SCHEMA)
        if (type(self.cutoff) is not InformationCutoff or self.cutoff.phase is not CausalPhase.PRE_ACTION
                or self.cutoff.cutoff_id != "cutoff." + self.case_id):
            raise TypeError("revision forecasts retain their original physical pre-action cutoff")
        self.cutoff.__post_init__()
        for values in (self.revision_predictions, self.baseline_predictions):
            if (type(values) is not tuple or len(values) != 30
                    or any(type(value) is not Decimal or not value.is_finite() for value in values)):
                raise ValueError("revision forecast omits its paired thirty-endpoint model output")

    @property
    def identity(self):
        return _identity(self, "record_id")


def validate_revision_phase(development, nomination, frozen, programme, *, phase):
    if (type(development) is not ScheduledProgramme or type(programme) is not ScheduledProgramme
            or type(nomination) is not ScheduledRevisionNomination or type(frozen) is not ScheduledRevisionFrozenPackage
            or programme.mode != {"CALIBRATION": "E4_REVISION_CALIBRATION", "CONFIRMATION": "E4_CONFIRMATION"}.get(phase)):
        raise ValueError("revision use requires its actual separate calibration or confirmation phase")
    development.__post_init__()
    programme.__post_init__()
    if (nomination.trigger_disposition != "TRIGGERED" or nomination.revision_model is None
            or nomination.baseline_model is None):
        raise ValueError("an untriggered revision leaves calibration and revision use unentered")
    for model in (nomination.revision_model, nomination.baseline_model):
        # Replay the exact original joint freeze for both selected models.
        design = nomination.specification
        if model is nomination.revision_model:
            require_revision_for_future_phase(development, nomination, frozen, phase=phase,
                model=model, target=design.target.identity, criterion=design.target.criterion,
                features=design.revision_design.features)
        else:
            from empirical_lawhood.runtime.experimental_selection import require_frozen_selection_for_phase
            allocation = design.validate_programme(development)
            require_frozen_selection_for_phase(design.baseline_design, allocation, nomination.baseline_selection,
                frozen.baseline, phase=phase, fitted_model=model.identity, target=design.target.identity,
                criterion=design.target.criterion, features=design.baseline_design.features)
    if (programme.reservation != development.reservation or programme.criterion != development.criterion
            or programme.specification != development.specification or programme.factors != development.factors
            or set(programme.group_ids) & set(development.group_ids)
            or {case.root_id for case in programme.cases} & {case.root_id for case in development.cases}
            or {case.source for case in programme.cases} & {case.source for case in development.cases}
            or {case.streams_sha256 for case in programme.cases} & {case.streams_sha256 for case in development.cases}):
        raise ValueError("revision phase changes its scientific scope or reuses development evidence")


def forecast_revision_case(development, nomination, frozen, programme, case, *, record_id):
    phase = "CALIBRATION" if programme.mode == "E4_REVISION_CALIBRATION" else "CONFIRMATION"
    validate_revision_phase(development, nomination, frozen, programme, phase=phase)
    return _forecast_revision_case(nomination, programme, case, record_id=record_id,
        pins=_forecast_pins(nomination, frozen, programme))


def forecast_revision_cases(development, nomination, frozen, programme, *, record_prefix):
    """Validate the owning phase once before constructing its complete census."""
    phase = "CALIBRATION" if programme.mode == "E4_REVISION_CALIBRATION" else "CONFIRMATION"
    validate_revision_phase(development, nomination, frozen, programme, phase=phase)
    pins = _forecast_pins(nomination, frozen, programme)
    return tuple(_forecast_revision_case(nomination, programme, case,
        record_id=record_prefix + "." + case.root_id, pins=pins) for case in programme.cases)


def _forecast_pins(nomination, frozen, programme):
    return (programme.identity, frozen.identity, nomination.revision_model.identity,
        nomination.baseline_model.identity, nomination.specification.target.identity)


def _forecast_revision_case(nomination, programme, case, *, record_id, pins):
    features = revision_case_features(programme, case)
    predictions = []
    for model in (nomination.revision_model, nomination.baseline_model):
        values = tuple(features[key] for key in model.tuning.feature_names)
        predictions.append(tuple(predict_standardized_ridge(parameters, values) for parameters in model.parameters))
    programme_pin, frozen_pin, revision_pin, baseline_pin, target_pin = pins
    return ScheduledRevisionForecastSeal(record_id, programme_pin, case.root_id, case.independent_group_id,
        case.source, case.coordinate, case.information_cutoff, frozen_pin, revision_pin, baseline_pin, target_pin, *predictions)


@dataclass(frozen=True, slots=True)
class ScheduledRevisionCalibration(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-scheduled-programme/revision-calibration"
    record_id: str
    specification: ScheduledRevisionCalibrationSpecification
    target: ObjectIdentity
    revision_model: ScheduledRevisionFittedModel
    baseline_model: ScheduledRevisionFittedModel
    group_ids: tuple[str, ...]
    revision_scores: tuple[tuple[str, Decimal | None], ...]
    baseline_scores: tuple[tuple[str, Decimal | None], ...]
    rank: int
    # None is the canonical unbounded result, including a missing-score rank.
    # Non-finite Decimal values cannot enter immutable canonical records.
    revision_radius: Decimal | None
    baseline_radius: Decimal | None
    data: ObjectIdentity
    forecasts: tuple[ObjectIdentity, ...]

    def __post_init__(self):
        from .programme_selection import ScheduledRevisionDataBank
        self._validate_operands(specification_type=ScheduledRevisionCalibrationSpecification,
            data_schema=ScheduledRevisionDataBank.SCHEMA, forecast_schema=ScheduledRevisionForecastSeal.SCHEMA, group_count=64)

    def _validate_operands(self, *, specification_type, data_schema, forecast_schema, group_count,
            data_version='1.0.0', forecast_version='1.0.0'):
        validate_stable_id(self.record_id)
        if (type(self.specification) is not specification_type
                or type(self.revision_model) is not ScheduledRevisionFittedModel
                or type(self.baseline_model) is not ScheduledRevisionFittedModel
                or type(self.group_ids) is not tuple or len(self.group_ids) != group_count
                or self.group_ids != tuple(sorted(set(self.group_ids)))
                or type(self.revision_scores) is not tuple or type(self.baseline_scores) is not tuple
                or any(type(row) is not tuple or len(row) != 2 for row in (*self.revision_scores, *self.baseline_scores))
                or tuple(key for key, _ in self.revision_scores) != self.group_ids
                or tuple(key for key, _ in self.baseline_scores) != self.group_ids
                or type(self.rank) is not int or type(self.forecasts) is not tuple
                or len(self.forecasts) != 9 * len(self.group_ids)
                or len(set(self.forecasts)) != len(self.forecasts)):
            raise ValueError("revision calibration must retain all sixty-four independent groups and paired models")
        for group in self.group_ids:
            validate_stable_id(group)
        _pin(self.data, data_schema, data_version)
        _pin(self.target, ScheduledRevisionTarget.SCHEMA)
        for forecast in self.forecasts:
            _pin(forecast, forecast_schema, forecast_version)
        self.specification.__post_init__()
        self.revision_model.__post_init__()
        self.baseline_model.__post_init__()
        if (self.revision_model.training_groups != self.baseline_model.training_groups
                or set(self.group_ids).intersection(self.revision_model.training_groups)):
            raise ValueError("revision calibration cannot reuse fitted groups or substitute the paired training census")
        for scores, radius in ((self.revision_scores, self.revision_radius), (self.baseline_scores, self.baseline_radius)):
            expected = split_upper_calibration(tuple(value for _, value in scores), self.specification.alpha)
            expected_radius = expected.radius if expected.radius.is_finite() else None
            if ((radius is not None and (type(radius) is not Decimal or not radius.is_finite()))
                    or self.rank != expected.rank or radius != expected_radius):
                raise ValueError("revision calibration changes its complete score rank or bound")

    @property
    def identity(self):
        return _identity(self, "record_id")


def calibrate_revision(specification, development, nomination, frozen, programme, reduction, data, forecasts, *, record_id):
    """Reduce one maximum residual per whole group; missing remains infinite.

    The rule covers all nine declared coordinates and both fifteen-endpoint
    views on one future matched group, conditional on applicable exchangeability.
    It supplies no per-state, transfer or preparation-selected coverage warrant.
    """
    validate_revision_phase(development, nomination, frozen, programme, phase="CALIBRATION")
    if (type(specification) is not ScheduledRevisionCalibrationSpecification
            or (specification.development_programme, specification.calibration_programme,
                specification.nomination, specification.frozen_models) !=
            (development.identity, programme.identity, nomination.identity, frozen.identity)):
        raise ValueError("revision calibration substitutes its frozen model or assigned populations")
    specification.__post_init__()
    if specification.alpha != Decimal(1) - programme.confidence:
        raise ValueError("revision calibration changes its declared global confidence")
    if type(forecasts) is not tuple or tuple(seal.case_id for seal in forecasts) != tuple(case.root_id for case in programme.cases):
        raise ValueError("revision calibration omits or reorders a pre-outcome forecast")
    targets, missing = validate_programme_paired_data(programme, reduction, data, nomination.specification.target,
        mode="E4_REVISION_CALIBRATION", missing_record_policy="ALLOW_ABSENT_DECLARED_ROWS")
    pins = _forecast_pins(nomination, frozen, programme)
    for case, seal in zip(programme.cases, forecasts, strict=True):
        if (type(seal) is not ScheduledRevisionForecastSeal or seal != _forecast_revision_case(
                nomination, programme, case, record_id=seal.record_id, pins=pins)):
            raise ValueError("revision calibration changes a frozen pre-outcome prediction")
    return calibration_from_targets(specification, nomination.specification.target.identity, nomination.revision_model, nomination.baseline_model, programme, data, forecasts, targets, missing,
        record_id=record_id, record_type=ScheduledRevisionCalibration)


def calibration_from_targets(specification, target, revision_model, baseline_model, programme, data, forecasts, targets, missing, *, record_id, record_type):
    """Shared original max-positive paired residual equation after exact phase joins."""
    scores = ({group: Decimal(0) for group in programme.group_ids}, {group: Decimal(0) for group in programme.group_ids})
    for case, seal in zip(programme.cases, forecasts, strict=True):
        for by_group, points in zip(scores, (seal.revision_predictions, seal.baseline_predictions), strict=True):
            if case.independent_group_id in missing:
                by_group[case.independent_group_id] = None
            elif by_group[case.independent_group_id] is not None:
                by_group[case.independent_group_id] = max(by_group[case.independent_group_id],
                    *(_exact_decimal(max(Fraction(0), Fraction(actual) - Fraction(point)))
                      for actual, point in zip(targets[case.root_id], points, strict=True)))
    pairs = tuple(tuple((group, values[group]) for group in programme.group_ids) for values in scores)
    ranks = tuple(split_upper_calibration(tuple(value for _, value in values), specification.alpha) for values in pairs)
    return record_type(record_id, specification, target,
        revision_model, baseline_model, programme.group_ids, *pairs,
        ranks[0].rank, *(rank.radius if rank.radius.is_finite() else None for rank in ranks),
        data.identity, tuple(seal.identity for seal in forecasts))
