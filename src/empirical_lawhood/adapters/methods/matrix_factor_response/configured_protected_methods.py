# SPDX-License-Identifier: MPL-2.0
"""Source-bound E3 calculations over actual original scheduled observations.

These distinct records retain fit/freeze/forecast and original cell ancestry.
They confer no source qualification, IID/exchangeability, issue or authority.
Owning API custody and independent source assessment remain required.
"""

from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ResolvedScheduledSource
from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole
from empirical_lawhood.adapters.methods.matrix_scheduled_history.forecast import ScheduledPublicSource
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import identity as scheduled_identity
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import (
    ScheduledResponseLossCell, ScheduledResponsePanel, ScheduledResponseProtocol, ScheduledResponseScore, branch_census,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_selection import ScheduledResponseSelection
from empirical_lawhood.kernel.experimental_design import UnitAllocation
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, canonical_json_bytes, validate_decimal, validate_sha256, validate_stable_id
from empirical_lawhood.runtime.experimental_statistics import AssignedBinomialInference, binomial_upper_tail, split_upper_calibration

from empirical_lawhood.adapters.methods.matrix_parameter_history.records import coordinate_identity
from . import e3_numerical_methods as numerical
from . import experiment_methods as exposed
from .native_training_records import native_training_bank_types, validate_native_training_banks
from . import matched_response_prediction as matched
from .matched_response_prediction import MatchedResponseViewOutcome
from .matched_response_fitting import MatchedEstimatorModel, MatchedCurveEstimatorModel
from .curve_prediction import MatchedCurveDecision, curve_root_decision
from .configured_protected_specification import ConfiguredProtectedE3Specification as MatrixResponseErrorSpecification
from .configured_protected_inputs import ConfiguredProtectedE3PreFitJoin, ConfiguredProtectedE3SourceInputs, project_protected_e3_allocation


def identity(record):
    return ObjectIdentity.from_record(record.record_id, record)


def _reference(value, kind):
    if type(value) is not ObjectIdentity or (value.object_schema, value.object_version) != (kind.SCHEMA, kind.VERSION):
        raise ValueError("source-bound E3 calculation substitutes an exact original type or revision")
    value.__post_init__()


def _selected_specification(specification):
    if type(specification) is not MatrixResponseErrorSpecification:
        raise TypeError("source-bound E3 needs its exact selected specification")
    specification.__post_init__()
    if specification.evidence_scope != "PROSPECTIVE_REQUIRED" or specification.calibration_target_view not in ("PRIMARY", "MAX_PAIRED_VIEWS"):
        raise ValueError("source-bound E3 changes selected paired-view science")


def _selected(specification, allocation):
    _selected_specification(specification)
    if type(allocation) is not UnitAllocation:
        raise TypeError("source-bound E3 needs its exact selected allocation")
    allocation.__post_init__()


from .configured_protected_feature_records import ConfiguredProtectedE3CausalFeature as ProtectedE3CausalFeature


def training_bank_types(feature_schema, outcome_schema):
    """Require the sole acquired-native TRAIN bank pair before body delivery."""
    kinds = native_training_bank_types()
    if (feature_schema, outcome_schema) != tuple(kind.SCHEMA for kind in kinds):
        raise ValueError("configured protected E3 requires the exact native TRAIN bank pair")
    return kinds


def _training_bank_references(features, outcomes):
    if type(features) is not ObjectIdentity or type(outcomes) is not ObjectIdentity:
        raise TypeError("configured E3 fitted product needs exact TRAIN bank identities")
    kinds = training_bank_types(features.object_schema, outcomes.object_schema)
    for reference, kind in zip((features, outcomes), kinds, strict=True):
        _reference(reference, kind)


@dataclass(frozen=True, slots=True)
class ConfiguredProtectedE3ModelSet(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/configured-protected-model-set"
    VERSION: ClassVar[str] = '2.0.0'
    record_id: str
    specification: ObjectIdentity
    allocation: ObjectIdentity
    reservation_join: ObjectIdentity
    training_features: ObjectIdentity
    training_outcomes: ObjectIdentity
    models: tuple[exposed.MatrixE3EstimatorModel | MatchedEstimatorModel | MatchedCurveEstimatorModel, ...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        for value, kind in ((self.specification, MatrixResponseErrorSpecification), (self.allocation, UnitAllocation),
                (self.reservation_join, ConfiguredProtectedE3PreFitJoin)):
            _reference(value, kind)
        _training_bank_references(self.training_features, self.training_outcomes)
        amended = bool(self.models) and type(self.models[0]) in (MatchedEstimatorModel, MatchedCurveEstimatorModel)
        model_type = type(self.models[0]) if amended else exposed.MatrixE3EstimatorModel
        if type(self.models) is not tuple or tuple(row.method_key for row in self.models) != (matched.MATCHED_METHODS if amended else exposed.METHODS):
            raise ValueError("source-bound E3 fitted product changes the exact selected estimator menu")
        for row in self.models:
            if type(row) is not model_type:
                raise TypeError("source-bound E3 substitutes its selected neutral estimator type")
            row.__post_init__()
        if amended and len({(row.training_unit_ids, row.folds, row.complete_group_ids, row.exclusions,
                tuple(reason for reason in row.prerequisite_reasons if reason != 'NUMERICALLY_UNEVALUABLE'))
                for row in self.models}) != 1:
            raise ValueError('matched E3 methods do not share the same complete roots and frozen folds')


@dataclass(frozen=True, slots=True)
class ConfiguredProtectedE3FrozenProducts(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/configured-protected-frozen-products"
    VERSION: ClassVar[str] = '2.0.0'
    record_id: str
    specification: ObjectIdentity
    allocation: ObjectIdentity
    models: ObjectIdentity
    reservation_join: ObjectIdentity
    calibration: ObjectIdentity | None
    model_freeze: ObjectIdentity | None

    def __post_init__(self):
        validate_stable_id(self.record_id)
        for value, kind in ((self.specification, MatrixResponseErrorSpecification), (self.allocation, UnitAllocation),
                (self.models, ConfiguredProtectedE3ModelSet), (self.reservation_join, ConfiguredProtectedE3PreFitJoin)):
            _reference(value, kind)
        if (self.calibration is None) != (self.model_freeze is None):
            raise ValueError("source-bound E3 calibrated freeze requires its actual prior fitted freeze")
        if self.calibration is not None:
            _reference(self.calibration, ConfiguredProtectedE3Calibration)
            _reference(self.model_freeze, ConfiguredProtectedE3FrozenProducts)


@dataclass(frozen=True, slots=True)
class ConfiguredProtectedE3Forecast(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/configured-protected-forecast"
    VERSION: ClassVar[str] = '2.0.0'
    record_id: str
    specification: ObjectIdentity
    allocation: ObjectIdentity
    models: ObjectIdentity
    frozen_products: ObjectIdentity
    feature: ProtectedE3CausalFeature
    role: str
    log_points: tuple[tuple[str, tuple[Decimal | None, ...]], ...]
    radius: Decimal | None
    radius_kind: str
    model_radii: tuple[tuple[str, Decimal | None], ...] = ()
    policies: tuple[matched.MatchedForecastPolicy, ...] = ()
    admission_owner: str | None = None

    def __post_init__(self):
        validate_stable_id(self.record_id)
        for value, kind in ((self.specification, MatrixResponseErrorSpecification), (self.allocation, UnitAllocation),
                (self.models, ConfiguredProtectedE3ModelSet), (self.frozen_products, ConfiguredProtectedE3FrozenProducts)):
            _reference(value, kind)
        amended = self.admission_owner == 'S0'
        if (type(self.feature) is not ProtectedE3CausalFeature or self.role not in ("calibration", "evaluation")
                or tuple(row[0] for row in self.log_points) != (matched.MATCHED_METHODS if amended else exposed.METHODS)
                or self.radius_kind != ("UNCALIBRATED" if self.role == "calibration" else "INFINITE" if self.radius is None else "FINITE")
                or self.role == "calibration" and self.radius is not None
                or amended != (self.feature.physical_forecast is not None)):
            raise ValueError("source-bound E3 forecast changes its fitted method, causal input or calibration scope")
        self.feature.__post_init__()
        for _, values in self.log_points:
            exposed._values(values, count=58 if amended else 15, nonnegative=True)
            if self.feature.disposition != "AVAILABLE" and any(value is not None for value in values):
                raise ValueError("source-bound E3 cannot predict without an original causal feature")
            for index, value in enumerate(values):
                if index % (29 if amended else 3) and value is not None and (values[index-1] is None or value < values[index-1]):
                    raise ValueError("source-bound E3 drops cumulative-horizon missingness or maxima")
        if self.radius is not None:
            validate_decimal(self.radius, field_name="calibrated radius", minimum=Decimal(0))
        if amended:
            if (tuple(method for method, _ in self.model_radii) != ('B0', 'S0')
                    or dict(self.model_radii)['S0'] != self.radius
                    or self.role == 'calibration' and any(radius is not None for _, radius in self.model_radii)):
                raise ValueError('matched forecast changes its separate radii or fixed S0 admission owner')
            for _, radius in self.model_radii:
                if radius is not None:
                    validate_decimal(radius, field_name='per-model calibrated radius', minimum=Decimal(0))
            expected = tuple(matched.matched_forecast_policy(method, dict(self.log_points)[method], radius,
                calibrated=self.role == 'evaluation') for method, radius in self.model_radii)
            if self.policies != expected:
                raise ValueError('matched forecast does not seal its original point/upper curves and separate admission policies')
        elif self.model_radii or self.policies or self.admission_owner is not None:
            raise ValueError('paired15 forecast substitutes a matched policy')


@dataclass(frozen=True, slots=True)
class ConfiguredProtectedE3PairedOutcome(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/configured-protected-paired-outcome"
    VERSION: ClassVar[str] = '2.0.0'
    record_id: str
    feature: ProtectedE3CausalFeature
    forecast: ObjectIdentity
    original_score: ObjectIdentity
    original_cells_sha256: str
    protocol: ObjectIdentity
    panels: tuple[ObjectIdentity, ...]
    views: tuple[exposed.MatrixE3ViewOutcome | MatchedResponseViewOutcome, ...]
    numerical_disposition: str

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if type(self.feature) is not ProtectedE3CausalFeature:
            raise TypeError("source-bound paired outcome needs its actual original feature")
        self.feature.__post_init__()
        _reference(self.forecast, ConfiguredProtectedE3Forecast)
        _reference(self.original_score, ScheduledResponseScore)
        _reference(self.protocol, ScheduledResponseProtocol)
        validate_sha256(self.original_cells_sha256)
        if (tuple(row.view_id for row in self.views) != ("fine", "primary")
                or len({type(row) for row in self.views}) != 1
                or any(type(row) not in (exposed.MatrixE3ViewOutcome, MatchedResponseViewOutcome) for row in self.views)
                or self.numerical_disposition not in ("SATISFIED", "VIOLATED", "UNEVALUABLE")
                or len(self.panels) != 2 or len(set(self.panels)) != 2):
            raise ValueError("source-bound E3 paired outcome drops original paired views or independent panels")
        for row in self.views:
            row.__post_init__()
        for row in self.panels:
            _reference(row, ScheduledResponsePanel)

    @property
    def unit_id(self):
        return self.feature.unit_id

    def view(self, view_id):
        return next(row for row in self.views if row.view_id == view_id)


@dataclass(frozen=True, slots=True)
class ConfiguredProtectedE3Calibration(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/configured-protected-calibration"
    VERSION: ClassVar[str] = '2.0.0'
    record_id: str
    specification: ObjectIdentity
    allocation: ObjectIdentity
    models: ObjectIdentity
    model_freeze: ObjectIdentity
    scores: tuple[tuple[str, Decimal | None, tuple[str, ...]], ...]
    rank: int
    radius: Decimal | None
    forecasts: tuple[ObjectIdentity, ...]
    outcomes: tuple[ObjectIdentity, ...]
    model_calibrations: tuple[matched.MatchedModelCalibration, ...] = ()

    def __post_init__(self):
        validate_stable_id(self.record_id)
        for value, kind in ((self.specification, MatrixResponseErrorSpecification), (self.allocation, UnitAllocation),
                (self.models, ConfiguredProtectedE3ModelSet), (self.model_freeze, ConfiguredProtectedE3FrozenProducts)):
            _reference(value, kind)
        if (not self.scores or tuple(row[0] for row in self.scores) != tuple(sorted({row[0] for row in self.scores}))
                or len(self.forecasts) != len(self.scores) or len(self.outcomes) != len(self.scores)
                or type(self.rank) is not int or self.rank < 1):
            raise ValueError("source-bound E3 calibration drops complete whole roots or original sealed ancestry")
        for unit, score, reasons in self.scores:
            validate_stable_id(unit)
            if score is not None:
                validate_decimal(score, field_name="calibration score", minimum=Decimal(0))
            if not reasons or reasons != tuple(sorted(set(reasons))):
                raise ValueError("source-bound E3 calibration loses finite/nonuse reasons")
        for value in self.forecasts:
            _reference(value, ConfiguredProtectedE3Forecast)
        for value in self.outcomes:
            _reference(value, ConfiguredProtectedE3PairedOutcome)
        if self.radius is not None:
            validate_decimal(self.radius, field_name="calibration radius", minimum=Decimal(0))
        if self.model_calibrations:
            if tuple(row.method_key for row in self.model_calibrations) != ('B0', 'S0'):
                raise ValueError('matched calibration must retain each fixed account separately')
            for row in self.model_calibrations:
                row.__post_init__()
                if tuple(item[0] for item in row.scores) != tuple(item[0] for item in self.scores):
                    raise ValueError('matched calibrations change the common assigned CAL roster')
            owner = self.model_calibrations[1]
            if (self.scores, self.rank, self.radius) != (owner.scores, owner.rank, owner.radius):
                raise ValueError('matched calibration changes its fixed S0 primary policy')


@dataclass(frozen=True, slots=True)
class ConfiguredProtectedE3Assessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/configured-protected-assessment"
    VERSION: ClassVar[str] = '2.0.0'
    record_id: str
    specification: ObjectIdentity
    allocation: ObjectIdentity
    calibrated_freeze: ObjectIdentity
    forecasts: tuple[ObjectIdentity, ...]
    outcomes: tuple[ObjectIdentity, ...]
    decisions: tuple[exposed.MatrixE3RootDecision | matched.MatchedRootDecision | MatchedCurveDecision, ...]
    successes: int
    usable_units: int
    binomial_tail_numerator: int
    binomial_tail_denominator: int
    criterion_met: bool
    coverage: tuple[tuple[str, bool, tuple[Decimal | None, ...]], ...]
    coverage_bound_kinds: tuple[tuple[str, str], ...]
    model_coverage: tuple[matched.MatchedCoverage, ...] = ()
    amended_inference: AssignedBinomialInference | None = None

    def __post_init__(self):
        validate_stable_id(self.record_id)
        for value, kind in ((self.specification, MatrixResponseErrorSpecification), (self.allocation, UnitAllocation),
                (self.calibrated_freeze, ConfiguredProtectedE3FrozenProducts)):
            _reference(value, kind)
        units = tuple(row.unit_id for row in self.decisions)
        if (not units or units != tuple(sorted(set(units))) or self.successes != sum(row.success for row in self.decisions)
                or self.usable_units != sum(row.usable for row in self.decisions)
                or len(self.forecasts) != len(units) or len(self.outcomes) != len(units)
                or tuple(row[0] for row in self.coverage) != units or tuple(row[0] for row in self.coverage_bound_kinds) != units
                or self.binomial_tail_denominator < 1 or not 0 <= self.binomial_tail_numerator <= self.binomial_tail_denominator
                or type(self.criterion_met) is not bool):
            raise ValueError("source-bound E3 assessment drops the original complete whole-root criterion")
        amended = self.amended_inference is not None
        decision_type = (MatchedCurveDecision if amended and type(self.decisions[0]) is MatchedCurveDecision else
            matched.MatchedRootDecision if amended else exposed.MatrixE3RootDecision)
        for row in self.decisions:
            if type(row) is not decision_type or decision_type is MatchedCurveDecision and row.structural_method != 'S0':
                raise TypeError("source-bound E3 assessment requires its selected whole-root decisions")
            row.__post_init__()
        for value in self.forecasts:
            _reference(value, ConfiguredProtectedE3Forecast)
        for value in self.outcomes:
            _reference(value, ConfiguredProtectedE3PairedOutcome)
        for (_, covered, values), (_, kind) in zip(self.coverage, self.coverage_bound_kinds, strict=True):
            if type(covered) is not bool or kind not in ("FINITE", "INFINITE", "UNAVAILABLE"):
                raise ValueError("source-bound E3 assessment changes coverage availability")
            exposed._values(values, count=58 if amended else 15, nonnegative=True)
            if kind == "INFINITE" and any(value is not None for value in values):
                raise ValueError("source-bound E3 assessment invents finite unavailable coverage")
        if amended:
            if self.amended_inference != matched.matched_primary_inference(self.decisions):
                raise ValueError('matched assessment changes its exact assigned-roster test or unknown-event envelope')
            if tuple((row.unit_id, row.method_key) for row in self.model_coverage) != tuple((unit, method) for unit in units for method in ('B0', 'S0')):
                raise ValueError('matched assessment drops a separate model coverage or admission policy')
            for row in self.model_coverage:
                row.__post_init__()
            owner = tuple(row for row in self.model_coverage if row.method_key == 'S0')
            if (self.coverage != tuple((row.unit_id, row.covered is True, row.original_unit_slacks) for row in owner)
                    or self.coverage_bound_kinds != tuple((row.unit_id, row.bound_kind) for row in owner)):
                raise ValueError('matched assessment changes its fixed S0 coverage projection')
        elif self.model_coverage:
            raise ValueError('paired15 assessment substitutes matched coverage')


def fit_protected_e3_models(inputs, joined, features, outcomes, *, record_id):
    if type(inputs) is not ConfiguredProtectedE3SourceInputs or type(joined) is not ConfiguredProtectedE3PreFitJoin:
        raise TypeError("source-bound E3 fit requires its actual original sources and pre-fit publication join")
    allocation = project_protected_e3_allocation(inputs)
    joined.__post_init__()
    if (joined.specification != inputs.specification.identity or joined.allocation != allocation.identity
            or joined.training_allocation != inputs.training_allocation.identity
            or joined.original_allocation != scheduled_identity(inputs.reservation.allocation)
            or joined.reservation != scheduled_identity(inputs.reservation)
            or joined.native_specification != scheduled_identity(inputs.native_specification)):
        raise ValueError("source-bound E3 fit changes its actual original reservation/source joins")
    kinds = training_bank_types(getattr(type(features), "SCHEMA", None), getattr(type(outcomes), "SCHEMA", None))
    if (type(features), type(outcomes)) != kinds:
        raise TypeError("configured E3 TRAIN requires its exact selected bank types")
    validate_native_training_banks(inputs.specification, inputs.training_allocation, features, outcomes)
    fs, ys = {row.unit_id: row for row in features.rows}, {row.unit_id: row for row in outcomes.rows}
    source_by_unit = {unit: source for unit, source, _ in inputs.training_coordinates.assignments}
    if any(feature.native_source != source_by_unit[feature.unit_id] for feature in features.rows):
        raise ValueError("configured E3 TRAIN banks substitute declared original source identities")
    for unit in allocation.unit_ids("train"):
        exposed.validate_pair(fs[unit], ys[unit])
    models = (numerical.fit_matched_estimator_values(inputs.specification, allocation.unit_ids('train'), fs, ys)
        if inputs.specification.measurement.is_matched else tuple(exposed.MatrixE3EstimatorModel(*values) for values in
            numerical.fit_estimator_values(inputs.specification, allocation.unit_ids("train"), fs, ys)))
    return ConfiguredProtectedE3ModelSet(record_id, inputs.specification.identity, allocation.identity, joined.identity,
        exposed.identity(features), exposed.identity(outcomes), models)


def freeze_protected_e3(specification, allocation, models, *, record_id, model_freeze=None, calibration=None):
    _selected(specification, allocation)
    if type(models) is not ConfiguredProtectedE3ModelSet or (models.specification, models.allocation) != (specification.identity, allocation.identity):
        raise ValueError("source-bound E3 freeze substitutes the selected fitted product")
    models.__post_init__()
    if (specification.measurement.is_matched != (type(models.models[0]) in (MatchedEstimatorModel, MatchedCurveEstimatorModel))
            or specification.is_curve_primary != (type(models.models[0]) is MatchedCurveEstimatorModel)):
        raise ValueError('source-bound E3 freeze substitutes the selected matched target/feature contract')
    if (model_freeze is None) != (calibration is None):
        raise ValueError("source-bound E3 calibrated freeze requires its original model freeze and actual calibration")
    if calibration is not None and (type(calibration) is not ConfiguredProtectedE3Calibration or type(model_freeze) is not ConfiguredProtectedE3FrozenProducts
            or calibration.model_freeze != identity(model_freeze) or model_freeze.calibration is not None
            or model_freeze.models != identity(models) or calibration.models != identity(models)
            or model_freeze.specification != specification.identity or model_freeze.allocation != allocation.identity
            or calibration.specification != specification.identity or calibration.allocation != allocation.identity
            or model_freeze.reservation_join != models.reservation_join):
        raise ValueError("source-bound E3 calibrated freeze refits or changes original model/score/source lineage")
    return ConfiguredProtectedE3FrozenProducts(record_id, specification.identity, allocation.identity, identity(models), models.reservation_join,
        None if calibration is None else identity(calibration), None if model_freeze is None else identity(model_freeze))


def forecast_protected_e3(specification, allocation, models, frozen, feature, *, role, record_id, calibration=None):
    _selected(specification, allocation)
    if (type(models) is not ConfiguredProtectedE3ModelSet or type(frozen) is not ConfiguredProtectedE3FrozenProducts
            or type(feature) is not ProtectedE3CausalFeature or role not in ("calibration", "evaluation")):
        raise TypeError("source-bound E3 forecast needs its actual fitted/frozen/causal typed inputs")
    for row in (models, frozen, feature):
        row.__post_init__()
    if (specification.measurement.is_matched != (type(models.models[0]) in (MatchedEstimatorModel, MatchedCurveEstimatorModel))
            or specification.is_curve_primary != (type(models.models[0]) is MatchedCurveEstimatorModel)
            or specification.measurement.is_matched != (feature.physical_forecast is not None)):
        raise ValueError('source-bound E3 forecast substitutes its selected model or causal mechanical parent')
    if specification.measurement.is_matched:
        matched.validate_matched_features(feature.values, feature.disposition, curve_primary=specification.is_curve_primary)
    unit = allocation.unit(feature.unit_id)
    native_role = MatrixProgrammeRole.CALIBRATION if role == "calibration" else MatrixProgrammeRole.CONFIRMATION
    if (models.specification != specification.identity or models.allocation != allocation.identity
            or frozen.specification != specification.identity or frozen.allocation != allocation.identity
            or frozen.models != identity(models) or frozen.reservation_join != models.reservation_join
            or feature.unit_id not in allocation.unit_ids(role) or unit is None or unit.exposed
            or feature.source_manifest.object_id != unit.source_id or feature.source_manifest not in allocation.sources
            or feature.public_source.reservation not in allocation.sources
            or feature.public_source.root.role is not native_role
            or coordinate_identity(feature.public_source.coordinate) != dict(specification.role_coordinates)[role.upper()]
            or feature.cutoff != specification.measurement.origin_tick * specification.measurement.primary_timestep):
        raise ValueError("source-bound E3 forecast changes actual frozen fit, original source or allocated causal role")
    if role == "calibration":
        if frozen.calibration is not None or calibration is not None:
            raise ValueError("source-bound E3 CAL point forecast cannot use calibration outcomes")
        radius = None
    else:
        if (type(calibration) is not ConfiguredProtectedE3Calibration or frozen.calibration != identity(calibration)
                or calibration.models != identity(models) or calibration.specification != specification.identity
                or calibration.allocation != allocation.identity):
            raise ValueError("source-bound E3 CONF requires the exact separately frozen calibration")
        radius = calibration.radius
    points = numerical.forecast_point_values(models.models, feature)
    radii, policies = (), ()
    if specification.measurement.is_matched:
        if role == 'evaluation' and not calibration.model_calibrations:
            raise ValueError('matched E3 confirmation requires both separately calibrated model bounds')
        radii = (tuple((row.method_key, row.radius) for row in calibration.model_calibrations)
            if role == 'evaluation' else (('B0', None), ('S0', None)))
        policies = tuple(matched.matched_forecast_policy(method, dict(points)[method], value,
            calibrated=role == 'evaluation') for method, value in radii)
    return ConfiguredProtectedE3Forecast(record_id, specification.identity, allocation.identity, identity(models), identity(frozen),
        feature, role, points, radius,
        "UNCALIBRATED" if role == "calibration" else "INFINITE" if radius is None else "FINITE",
        radii, policies, 'S0' if specification.measurement.is_matched else None)


def project_protected_e3_outcome(specification, source, selection, forecast, score, *, record_id):
    """Derive BOTH all15 targets from the original complete independent cells."""
    _selected_specification(specification)
    if (type(source) is not ResolvedScheduledSource or type(selection) is not ScheduledResponseSelection
            or type(forecast) is not ConfiguredProtectedE3Forecast or type(score) is not ScheduledResponseScore):
        raise TypeError("source-bound E3 target projection needs actual original scheduled source/selection/forecast/score")
    for value in (source, selection, forecast, score):
        value.__post_init__()
    selection.validate_allocation(source.allocation)
    protocol, panels = selection.validate_source(source)
    protocol_id = ObjectIdentity.from_record(protocol.protocol_id, protocol)  # noqa: F841 - preserve original pre-guard evaluation
    if (forecast.specification != specification.identity or forecast.feature.public_source != ScheduledPublicSource.from_source(source)
            or score.source != scheduled_identity(source) or score.causal_prefix != forecast.feature.origin
            or score.error_forecast != identity(forecast) or score.criterion != protocol.criterion
            or (score.root_id, score.independent_group_id, score.role) != (source.root_id, forecast.feature.unit_id, source.root.root.role.value)
            or protocol.horizon_steps != specification.measurement.horizons or protocol.receiver_count != specification.measurement.receiver_count
            or tuple(sorted(action.role for action in protocol.actions)) != specification.measurement.actions
            or any(action.amplitude != specification.measurement.action_amplitude
                or action.pulse_steps != specification.measurement.pulse_ticks
                # Original candidate-design02 action_scales use unit HS norm.
                or action.force_norm != Decimal(1) for action in protocol.actions)):
        raise ValueError("source-bound E3 target projection changes actual original source/seal/menu/cutoff")
    return project_paired_response_cells(specification, source, protocol, panels, forecast, score, record_id=record_id)


def paired_response_view_values(specification, source, protocol, panels, score):
    """Original complete paired target reduction without a learned forecast."""
    matched = specification.measurement.is_matched
    if matched != (score.dense is not None):
        raise ValueError('source-bound E3 target projection substitutes the selected paired target contract')
    expected = {(view, panel.panel_id, action.action_id, predictor, horizon)
        for view in ("PRIMARY", "FINE") for panel in panels for action in protocol.actions
        for predictor in specification.measurement.descriptions for horizon in protocol.horizon_steps}
    if {cell.key for cell in score.cells} != expected or len(score.cells) != len(expected):
        raise ValueError("source-bound E3 target projection drops original complete paired cell denominators")
    if matched:
        from .response_scoring import validate_dense_score_units
        validate_dense_score_units(protocol, score)
    for cell in (() if matched else score.cells):
        if type(cell) is not ScheduledResponseLossCell:
            raise TypeError("source-bound E3 target projection needs original exact receiver cells")
        cell.__post_init__()
        vectors = (cell.actual_odd_responses, cell.signed_errors, cell.absolute_errors, cell.relative_errors)
        if (any(values is not None and (type(values) is not tuple or len(values) != protocol.receiver_count) for values in vectors)
                or cell.normalized_error is not None and any(values is None for values in vectors)):
            raise ValueError("source-bound E3 target projection thins original full receiver denominators")
    branches = branch_census(protocol, panels)
    if score.disposition in ("FINITE", "PARTIAL"):
        expected_controls = {"control.scheduled." + source.root_id + "." + branch: (1 if view == "PRIMARY" else 2) * protocol.horizon_steps[-1]
            for branch, view, *_ in branches}
        if (len(score.controls) != len(branches) or {row.control_id for row in score.controls} != set(expected_controls)
                or any(row.denominator_steps != expected_controls[row.control_id] or row.denominator_real_coordinates != 192
                    or row.tolerance != protocol.native_reference_tolerance for row in score.controls)):
            raise ValueError("source-bound E3 target projection thins actual full192 paired native controls")
    views = []
    for view in ("fine", "primary"):
        values, tags = [], []
        endpoints = tuple(('FACTOR', horizon) for horizon in specification.measurement.horizons) if matched else exposed.ENDPOINTS
        for description, horizon in endpoints:
            cells = tuple(cell for cell in score.cells if cell.view == view.upper() and cell.predictor == description and cell.horizon_tick <= horizon)
            missing = any(cell.normalized_error is None for cell in cells)
            finite = score.numerical_pass and score.disposition in ("FINITE", "PARTIAL") and not missing
            values.append(max(cell.normalized_error for cell in cells) if finite else None)
            tags.append("FINITE" if finite else "NUMERICAL_FAILURE" if not score.numerical_pass else "UNAVAILABLE")
        views.append((MatchedResponseViewOutcome if matched else exposed.MatrixE3ViewOutcome)(view, tuple(values), tuple(tags)))
    numerical_disposition = ("SATISFIED" if score.numerical_pass and score.disposition in ("FINITE", "PARTIAL") else
        "VIOLATED" if score.disposition == "NATIVE_CROSSCHECK_FAILED" else "UNEVALUABLE")
    return tuple(views), numerical_disposition


def project_paired_response_cells(specification, source, protocol, panels, forecast, score, *, record_id):
    """Original complete-cell/receiver reduction after owning source guards.

    This helper confers no source, forecast, custody or numerical qualification.
    """
    views, numerical_disposition = paired_response_view_values(specification, source, protocol, panels, score)
    protocol_id = ObjectIdentity.from_record(protocol.protocol_id, protocol)
    return ConfiguredProtectedE3PairedOutcome(record_id, forecast.feature, identity(forecast), scheduled_identity(score),
        sha256(canonical_json_bytes(score.cells)).hexdigest(), protocol_id,
        tuple(ObjectIdentity.from_record(panel.panel_id, panel) for panel in panels), views, numerical_disposition)


def _paired_inputs(specification, allocation, frozen, forecasts, outcomes, role):
    _selected(specification, allocation)
    if (type(frozen) is not ConfiguredProtectedE3FrozenProducts or type(forecasts) is not tuple or type(outcomes) is not tuple
            or any(type(row) is not ConfiguredProtectedE3Forecast for row in forecasts)
            or any(type(row) is not ConfiguredProtectedE3PairedOutcome for row in outcomes)):
        raise TypeError("source-bound E3 reduction requires original typed frozen/forecast/paired products")
    expected = allocation.unit_ids(role)
    fs, ys = {row.feature.unit_id: row for row in forecasts}, {row.unit_id: row for row in outcomes}
    if (len(fs) != len(forecasts) or len(ys) != len(outcomes) or tuple(sorted(fs)) != expected or tuple(sorted(ys)) != expected
            or frozen.specification != specification.identity or frozen.allocation != allocation.identity):
        raise ValueError("source-bound E3 reduction drops complete assigned whole roots or changes frozen source")
    for unit in expected:
        f, y = fs[unit], ys[unit]
        allocated = allocation.unit(unit)
        native_role = MatrixProgrammeRole.CALIBRATION if role == "calibration" else MatrixProgrammeRole.CONFIRMATION
        if (f.role != role or f.frozen_products != identity(frozen) or f.models != frozen.models or f.specification != specification.identity
                or f.allocation != allocation.identity or y.forecast != identity(f) or y.feature != f.feature
                or allocated is None or allocated.exposed or f.feature.source_manifest.object_id != allocated.source_id
                or f.feature.source_manifest not in allocation.sources or f.feature.public_source.reservation not in allocation.sources
                or f.feature.public_source.root.role is not native_role
                or f.feature.cutoff != specification.measurement.origin_tick * specification.measurement.primary_timestep):
            raise ValueError("source-bound E3 reduction substitutes a future-informed or foreign actual forecast")
        f.__post_init__()
        y.__post_init__()
        if (specification.measurement.is_matched != (f.admission_owner == 'S0')
                or specification.measurement.is_matched != (type(y.views[0]) is MatchedResponseViewOutcome)):
            raise ValueError('source-bound E3 reduction changes its selected paired target/policy contract')
    return expected, fs, ys


def calibrate_protected_e3(specification, allocation, models, frozen, forecasts, outcomes, *, record_id):
    expected, fs, ys = _paired_inputs(specification, allocation, frozen, forecasts, outcomes, "calibration")
    if (type(models) is not ConfiguredProtectedE3ModelSet or frozen.models != identity(models) or frozen.calibration is not None
            or models.specification != specification.identity or models.allocation != allocation.identity
            or models.reservation_join != frozen.reservation_join):
        raise ValueError("source-bound E3 CAL replaces its pre-calibration fitted freeze")
    scores = []
    model_scores = {method: [] for method in ('B0', 'S0')}
    for unit in expected:
        f, y = fs[unit], ys[unit]
        reasons = list(numerical.outcome_reasons(specification, y))
        if f.feature.disposition != "AVAILABLE":
            reasons.append(f.feature.disposition)
        if specification.measurement.is_matched:
            for method in ('B0', 'S0'):
                value, tags = numerical.matched_calibration_value(dict(f.log_points)[method], y, reasons)
                model_scores[method].append((unit, value, tags))
        else:
            score, tags = numerical.calibration_score(specification, f.log_points, y, reasons)
            scores.append((unit, score, tags))
    calibrations = (tuple(matched.matched_model_calibration(method, tuple(model_scores[method])) for method in ('B0', 'S0'))
        if specification.measurement.is_matched else ())
    if calibrations:
        scores = list(calibrations[1].scores)
    ranked = split_upper_calibration(tuple(row[1] for row in scores), specification.calibration_alpha)
    return ConfiguredProtectedE3Calibration(record_id, specification.identity, allocation.identity, identity(models), identity(frozen),
        tuple(scores), ranked.rank, None if ranked.radius.is_infinite() else ranked.radius,
        tuple(identity(fs[unit]) for unit in expected), tuple(identity(ys[unit]) for unit in expected), calibrations)


def assess_protected_e3(specification, allocation, frozen, forecasts, outcomes, *, record_id):
    expected, fs, ys = _paired_inputs(specification, allocation, frozen, forecasts, outcomes, "evaluation")
    if frozen.calibration is None:
        raise ValueError("source-bound E3 CONF lacks its exact calibrated freeze")
    decisions, coverage, kinds, model_coverage = [], [], [], []
    primary = (None if specification.measurement.is_matched else
        exposed.ENDPOINTS.index((specification.measurement.primary_description, specification.measurement.primary_horizon)))
    for unit in expected:
        f, y = fs[unit], ys[unit]
        reasons = list(numerical.outcome_reasons(specification, y))
        if f.feature.disposition != "AVAILABLE":
            reasons.append(f.feature.disposition)
        points = dict(f.log_points)
        if specification.measurement.is_matched:
            decision = (curve_root_decision if specification.is_curve_primary else matched.matched_root_decision)(unit, points, y, reasons)
            decisions.append(decision)
            for policy in f.policies:
                value = matched.matched_coverage(unit, policy.method_key, points[policy.method_key], policy, y,
                    not reasons and all(point is not None for point in points[policy.method_key]))
                model_coverage.append(value)
                if policy.method_key == 'S0':
                    coverage.append((unit, value.covered is True, value.original_unit_slacks))
                    kinds.append((unit, value.bound_kind))
        else:
            usable, success, comparisons, tags = numerical.paired_root_decision(specification, points, y, primary, reasons)
            decisions.append(exposed.MatrixE3RootDecision(unit, usable, success, comparisons, tags))
            covered, slacks, kind = numerical.coverage_values(points, y, f.radius_kind, f.radius, usable)
            coverage.append((unit, covered, slacks))
            kinds.append((unit, kind))
    successes, usable_units = sum(row.success for row in decisions), sum(row.usable for row in decisions)
    tail = binomial_upper_tail(len(expected), successes, specification.assessment.null_probability)
    return ConfiguredProtectedE3Assessment(record_id, specification.identity, allocation.identity, identity(frozen),
        tuple(identity(fs[unit]) for unit in expected), tuple(identity(ys[unit]) for unit in expected), tuple(decisions),
        successes, usable_units, tail.numerator, tail.denominator,
        tail <= specification.assessment.alpha and usable_units >= specification.assessment.minimum_usable_units,
        tuple(coverage), tuple(kinds), tuple(model_coverage),
        matched.matched_primary_inference(tuple(decisions)) if specification.measurement.is_matched else None)
