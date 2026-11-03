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
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledAllocation, ScheduledReservation, ScheduledSource, identity as scheduled_identity
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import (
    ScheduledResponseLossCell, ScheduledResponsePanel, ScheduledResponseProtocol, ScheduledResponseScore, branch_census,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_selection import ScheduledResponseSelection
from empirical_lawhood.kernel.experimental_design import UnitAllocation
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, canonical_json_bytes, validate_decimal, validate_sha256, validate_stable_id
from empirical_lawhood.runtime.experimental_statistics import binomial_upper_tail, split_upper_calibration

from . import e3_numerical_methods as numerical
from . import experiment_methods as exposed
from .experiment_specification import MatrixResponseErrorSpecification
from .protected_experiment_inputs import ProtectedE3PreFitJoin, ProtectedE3SourceInputs, project_protected_e3_allocation
from .protected_prefix_records import ProtectedE3CausalPrefix, ProtectedE3FrameAssessment, ProtectedE3NumericalAssessment, ProtectedE3PrefixWitness
from .response_error_prediction import FEATURES


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
    if specification.evidence_scope != "PROSPECTIVE_REQUIRED" or specification.calibration_target_view != "MAX_PAIRED_VIEWS":
        raise ValueError("source-bound E3 changes selected paired-view science")


def _selected(specification, allocation):
    _selected_specification(specification)
    if type(allocation) is not UnitAllocation:
        raise TypeError("source-bound E3 needs its exact selected allocation")
    allocation.__post_init__()


@dataclass(frozen=True, slots=True)
class ProtectedE3CausalFeature(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/protected-causal-feature"
    VERSION: ClassVar[str] = "2.0.0"
    record_id: str
    source_manifest: ObjectIdentity
    public_source: ScheduledPublicSource
    prefix: ObjectIdentity
    frame_sha256: str | None
    disposition: str
    values: tuple[tuple[str, Decimal], ...]
    evidence: tuple[ObjectIdentity, ...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (type(self.public_source) is not ScheduledPublicSource or type(self.evidence) is not tuple
                or len(self.evidence) != 4 or any(type(row) is not ObjectIdentity for row in self.evidence)):
            raise TypeError("source-bound E3 feature requires exact seedless public source and four current products")
        self.public_source.__post_init__()
        _reference(self.source_manifest, ScheduledAllocation)
        _reference(self.public_source.source, ScheduledSource)
        _reference(self.public_source.reservation, ScheduledReservation)
        _reference(self.prefix, ProtectedE3CausalPrefix)
        kinds = (ProtectedE3CausalPrefix, ProtectedE3NumericalAssessment, ProtectedE3PrefixWitness, ProtectedE3FrameAssessment)
        expected = {(kind.SCHEMA, kind.VERSION) for kind in kinds}
        if (self.source_manifest != self.public_source.allocation
                or tuple(row.object_id for row in self.evidence) != tuple(sorted({row.object_id for row in self.evidence}))
                or {(row.object_schema, row.object_version) for row in self.evidence} != expected
                or self.prefix not in self.evidence):
            raise ValueError("source-bound E3 feature changes original allocation or complete current evidence")
        if (self.disposition not in ("AVAILABLE", "NO_CAUSAL_ORIGIN", "UNAVAILABLE", "REFUSED")
                or type(self.values) is not tuple
                or (tuple(name for name, _ in self.values) != FEATURES if self.disposition == "AVAILABLE" else bool(self.values))
                or self.disposition == "AVAILABLE" and (self.frame_sha256 is None or dict(self.values)["cutoff"] != self.cutoff)):
            raise ValueError("source-bound E3 feature changes original values, frame, cutoff or nonuse")
        if self.frame_sha256 is not None:
            validate_sha256(self.frame_sha256)
        for _, value in self.values:
            validate_decimal(value, field_name="source-bound causal feature", minimum=Decimal(0))
        for row in self.evidence:
            row.__post_init__()

    @property
    def unit_id(self):
        return self.public_source.root.independent_group_id

    @property
    def native_source(self):
        return self.public_source.source

    @property
    def origin(self):
        return self.prefix

    @property
    def clock_id(self):
        return self.public_source.root.clock_id

    @property
    def cutoff(self):
        return self.public_source.coordinate.physical_time(self.public_source.policy.cutoff_tick)


@dataclass(frozen=True, slots=True)
class ProtectedE3ModelSet(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/protected-model-set"
    record_id: str
    specification: ObjectIdentity
    allocation: ObjectIdentity
    reservation_join: ObjectIdentity
    training_features: ObjectIdentity
    training_outcomes: ObjectIdentity
    models: tuple[exposed.MatrixE3EstimatorModel, ...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        for value, kind in ((self.specification, MatrixResponseErrorSpecification), (self.allocation, UnitAllocation),
                (self.reservation_join, ProtectedE3PreFitJoin), (self.training_features, exposed.MatrixE3FeatureBank),
                (self.training_outcomes, exposed.MatrixE3OutcomeBank)):
            _reference(value, kind)
        if type(self.models) is not tuple or tuple(row.method_key for row in self.models) != exposed.METHODS:
            raise ValueError("source-bound E3 fitted product changes the exact three estimators")
        for row in self.models:
            if type(row) is not exposed.MatrixE3EstimatorModel:
                raise TypeError("source-bound E3 uses original neutral estimator values")
            row.__post_init__()


@dataclass(frozen=True, slots=True)
class ProtectedE3FrozenProducts(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/protected-frozen-products"
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
                (self.models, ProtectedE3ModelSet), (self.reservation_join, ProtectedE3PreFitJoin)):
            _reference(value, kind)
        if (self.calibration is None) != (self.model_freeze is None):
            raise ValueError("source-bound E3 calibrated freeze requires its actual prior fitted freeze")
        if self.calibration is not None:
            _reference(self.calibration, ProtectedE3Calibration)
            _reference(self.model_freeze, ProtectedE3FrozenProducts)


@dataclass(frozen=True, slots=True)
class ProtectedE3Forecast(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/protected-forecast"
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

    def __post_init__(self):
        validate_stable_id(self.record_id)
        for value, kind in ((self.specification, MatrixResponseErrorSpecification), (self.allocation, UnitAllocation),
                (self.models, ProtectedE3ModelSet), (self.frozen_products, ProtectedE3FrozenProducts)):
            _reference(value, kind)
        if (type(self.feature) is not ProtectedE3CausalFeature or self.role not in ("calibration", "evaluation")
                or tuple(row[0] for row in self.log_points) != exposed.METHODS
                or self.radius_kind != ("UNCALIBRATED" if self.role == "calibration" else "INFINITE" if self.radius is None else "FINITE")
                or self.role == "calibration" and self.radius is not None):
            raise ValueError("source-bound E3 forecast changes its fitted method, causal input or calibration scope")
        self.feature.__post_init__()
        for _, values in self.log_points:
            exposed._values(values, count=15, nonnegative=True)
            if self.feature.disposition != "AVAILABLE" and any(value is not None for value in values):
                raise ValueError("source-bound E3 cannot predict without an original causal feature")
            for index, value in enumerate(values):
                if index % 3 and value is not None and (values[index-1] is None or value < values[index-1]):
                    raise ValueError("source-bound E3 drops cumulative-horizon missingness or maxima")
        if self.radius is not None:
            validate_decimal(self.radius, field_name="calibrated radius", minimum=Decimal(0))


@dataclass(frozen=True, slots=True)
class ProtectedE3PairedOutcome(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/protected-paired-outcome"
    record_id: str
    feature: ProtectedE3CausalFeature
    forecast: ObjectIdentity
    original_score: ObjectIdentity
    original_cells_sha256: str
    protocol: ObjectIdentity
    panels: tuple[ObjectIdentity, ...]
    views: tuple[exposed.MatrixE3ViewOutcome, ...]
    numerical_disposition: str

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if type(self.feature) is not ProtectedE3CausalFeature:
            raise TypeError("source-bound paired outcome needs its actual original feature")
        self.feature.__post_init__()
        _reference(self.forecast, ProtectedE3Forecast)
        _reference(self.original_score, ScheduledResponseScore)
        _reference(self.protocol, ScheduledResponseProtocol)
        validate_sha256(self.original_cells_sha256)
        if (tuple(row.view_id for row in self.views) != ("fine", "primary")
                or any(type(row) is not exposed.MatrixE3ViewOutcome for row in self.views)
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
class ProtectedE3Calibration(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/protected-calibration"
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

    def __post_init__(self):
        validate_stable_id(self.record_id)
        for value, kind in ((self.specification, MatrixResponseErrorSpecification), (self.allocation, UnitAllocation),
                (self.models, ProtectedE3ModelSet), (self.model_freeze, ProtectedE3FrozenProducts)):
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
            _reference(value, ProtectedE3Forecast)
        for value in self.outcomes:
            _reference(value, ProtectedE3PairedOutcome)
        if self.radius is not None:
            validate_decimal(self.radius, field_name="calibration radius", minimum=Decimal(0))


@dataclass(frozen=True, slots=True)
class ProtectedE3Assessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/protected-assessment"
    record_id: str
    specification: ObjectIdentity
    allocation: ObjectIdentity
    calibrated_freeze: ObjectIdentity
    forecasts: tuple[ObjectIdentity, ...]
    outcomes: tuple[ObjectIdentity, ...]
    decisions: tuple[exposed.MatrixE3RootDecision, ...]
    successes: int
    usable_units: int
    binomial_tail_numerator: int
    binomial_tail_denominator: int
    criterion_met: bool
    coverage: tuple[tuple[str, bool, tuple[Decimal | None, ...]], ...]
    coverage_bound_kinds: tuple[tuple[str, str], ...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        for value, kind in ((self.specification, MatrixResponseErrorSpecification), (self.allocation, UnitAllocation),
                (self.calibrated_freeze, ProtectedE3FrozenProducts)):
            _reference(value, kind)
        units = tuple(row.unit_id for row in self.decisions)
        if (not units or units != tuple(sorted(set(units))) or self.successes != sum(row.success for row in self.decisions)
                or self.usable_units != sum(row.usable for row in self.decisions)
                or len(self.forecasts) != len(units) or len(self.outcomes) != len(units)
                or tuple(row[0] for row in self.coverage) != units or tuple(row[0] for row in self.coverage_bound_kinds) != units
                or self.binomial_tail_denominator < 1 or not 0 <= self.binomial_tail_numerator <= self.binomial_tail_denominator
                or type(self.criterion_met) is not bool):
            raise ValueError("source-bound E3 assessment drops the original complete whole-root criterion")
        for row in self.decisions:
            if type(row) is not exposed.MatrixE3RootDecision:
                raise TypeError("source-bound E3 assessment requires original neutral whole-root decisions")
            row.__post_init__()
        for value in self.forecasts:
            _reference(value, ProtectedE3Forecast)
        for value in self.outcomes:
            _reference(value, ProtectedE3PairedOutcome)
        for (_, covered, values), (_, kind) in zip(self.coverage, self.coverage_bound_kinds, strict=True):
            if type(covered) is not bool or kind not in ("FINITE", "INFINITE", "UNAVAILABLE"):
                raise ValueError("source-bound E3 assessment changes coverage availability")
            exposed._values(values, count=15, nonnegative=True)
            if kind == "INFINITE" and any(value is not None for value in values):
                raise ValueError("source-bound E3 assessment invents finite unavailable coverage")


def fit_protected_e3_models(inputs, joined, features, outcomes, *, record_id):
    if type(inputs) is not ProtectedE3SourceInputs or type(joined) is not ProtectedE3PreFitJoin:
        raise TypeError("source-bound E3 fit requires its actual original sources and pre-fit publication join")
    allocation = project_protected_e3_allocation(inputs)
    joined.__post_init__()
    if (joined.specification != inputs.specification.identity or joined.allocation != allocation.identity
            or joined.training_allocation != inputs.training_allocation.identity
            or joined.original_allocation != scheduled_identity(inputs.reservation.allocation)
            or joined.reservation != scheduled_identity(inputs.reservation)
            or joined.native_specification != scheduled_identity(inputs.native_specification)):
        raise ValueError("source-bound E3 fit changes its actual original reservation/source joins")
    for bank, kind in ((features, exposed.MatrixE3FeatureBank), (outcomes, exposed.MatrixE3OutcomeBank)):
        if type(bank) is not kind:
            raise TypeError("source-bound E3 TRAIN retains its exact original exposed bank types")
        bank.__post_init__()
        if (bank.allocation != inputs.training_allocation.identity or bank.role != "train"
                or tuple(row.unit_id for row in bank.rows) != inputs.training_allocation.unit_ids()):
            raise ValueError("source-bound E3 fit drops or relabels an original TRAIN bank denominator")
        for row in bank.rows:
            exposed._validate_row(inputs.specification, inputs.training_allocation, row)
    fs, ys = {row.unit_id: row for row in features.rows}, {row.unit_id: row for row in outcomes.rows}
    for unit in allocation.unit_ids("train"):
        exposed.validate_pair(fs[unit], ys[unit])
    models = tuple(exposed.MatrixE3EstimatorModel(*values) for values in
        numerical.fit_estimator_values(inputs.specification, allocation.unit_ids("train"), fs, ys))
    return ProtectedE3ModelSet(record_id, inputs.specification.identity, allocation.identity, joined.identity,
        exposed.identity(features), exposed.identity(outcomes), models)


def freeze_protected_e3(specification, allocation, models, *, record_id, model_freeze=None, calibration=None):
    _selected(specification, allocation)
    if type(models) is not ProtectedE3ModelSet or (models.specification, models.allocation) != (specification.identity, allocation.identity):
        raise ValueError("source-bound E3 freeze substitutes the selected fitted product")
    models.__post_init__()
    if (model_freeze is None) != (calibration is None):
        raise ValueError("source-bound E3 calibrated freeze requires its original model freeze and actual calibration")
    if calibration is not None and (type(calibration) is not ProtectedE3Calibration or type(model_freeze) is not ProtectedE3FrozenProducts
            or calibration.model_freeze != identity(model_freeze) or model_freeze.calibration is not None
            or model_freeze.models != identity(models) or calibration.models != identity(models)
            or model_freeze.specification != specification.identity or model_freeze.allocation != allocation.identity
            or calibration.specification != specification.identity or calibration.allocation != allocation.identity
            or model_freeze.reservation_join != models.reservation_join):
        raise ValueError("source-bound E3 calibrated freeze refits or changes original model/score/source lineage")
    return ProtectedE3FrozenProducts(record_id, specification.identity, allocation.identity, identity(models), models.reservation_join,
        None if calibration is None else identity(calibration), None if model_freeze is None else identity(model_freeze))


def forecast_protected_e3(specification, allocation, models, frozen, feature, *, role, record_id, calibration=None):
    _selected(specification, allocation)
    if (type(models) is not ProtectedE3ModelSet or type(frozen) is not ProtectedE3FrozenProducts
            or type(feature) is not ProtectedE3CausalFeature or role not in ("calibration", "evaluation")):
        raise TypeError("source-bound E3 forecast needs its actual fitted/frozen/causal typed inputs")
    for row in (models, frozen, feature):
        row.__post_init__()
    unit = allocation.unit(feature.unit_id)
    native_role = MatrixProgrammeRole.CALIBRATION if role == "calibration" else MatrixProgrammeRole.CONFIRMATION
    if (models.specification != specification.identity or models.allocation != allocation.identity
            or frozen.specification != specification.identity or frozen.allocation != allocation.identity
            or frozen.models != identity(models) or frozen.reservation_join != models.reservation_join
            or feature.unit_id not in allocation.unit_ids(role) or unit is None or unit.exposed
            or feature.source_manifest.object_id != unit.source_id or feature.source_manifest not in allocation.sources
            or feature.public_source.reservation not in allocation.sources
            or feature.public_source.root.role is not native_role
            or feature.cutoff != specification.measurement.origin_tick * specification.measurement.primary_timestep):
        raise ValueError("source-bound E3 forecast changes actual frozen fit, original source or allocated causal role")
    if role == "calibration":
        if frozen.calibration is not None or calibration is not None:
            raise ValueError("source-bound E3 CAL point forecast cannot use calibration outcomes")
        radius = None
    else:
        if (type(calibration) is not ProtectedE3Calibration or frozen.calibration != identity(calibration)
                or calibration.models != identity(models) or calibration.specification != specification.identity
                or calibration.allocation != allocation.identity):
            raise ValueError("source-bound E3 CONF requires the exact separately frozen calibration")
        radius = calibration.radius
    return ProtectedE3Forecast(record_id, specification.identity, allocation.identity, identity(models), identity(frozen),
        feature, role, numerical.forecast_point_values(models.models, feature), radius,
        "UNCALIBRATED" if role == "calibration" else "INFINITE" if radius is None else "FINITE")


def project_protected_e3_outcome(specification, source, selection, forecast, score, *, record_id):
    """Derive BOTH all15 targets from the original complete independent cells."""
    _selected_specification(specification)
    if (type(source) is not ResolvedScheduledSource or type(selection) is not ScheduledResponseSelection
            or type(forecast) is not ProtectedE3Forecast or type(score) is not ScheduledResponseScore):
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


def project_paired_response_cells(specification, source, protocol, panels, forecast, score, *, record_id):
    """Original complete-cell/receiver reduction after owning source guards.

    This helper confers no source, forecast, custody or numerical qualification.
    """
    protocol_id = ObjectIdentity.from_record(protocol.protocol_id, protocol)
    expected = {(view, panel.panel_id, action.action_id, predictor, horizon)
        for view in ("PRIMARY", "FINE") for panel in panels for action in protocol.actions
        for predictor in specification.measurement.descriptions for horizon in protocol.horizon_steps}
    if {cell.key for cell in score.cells} != expected or len(score.cells) != len(expected):
        raise ValueError("source-bound E3 target projection drops original complete paired cell denominators")
    for cell in score.cells:
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
        for description, horizon in exposed.ENDPOINTS:
            cells = tuple(cell for cell in score.cells if cell.view == view.upper() and cell.predictor == description and cell.horizon_tick <= horizon)
            missing = any(cell.normalized_error is None for cell in cells)
            finite = score.numerical_pass and score.disposition in ("FINITE", "PARTIAL") and not missing
            values.append(max(cell.normalized_error for cell in cells) if finite else None)
            tags.append("FINITE" if finite else "NUMERICAL_FAILURE" if not score.numerical_pass else "UNAVAILABLE")
        views.append(exposed.MatrixE3ViewOutcome(view, tuple(values), tuple(tags)))
    return ProtectedE3PairedOutcome(record_id, forecast.feature, identity(forecast), scheduled_identity(score),
        sha256(canonical_json_bytes(score.cells)).hexdigest(), protocol_id,
        tuple(ObjectIdentity.from_record(panel.panel_id, panel) for panel in panels), tuple(views),
        "SATISFIED" if score.numerical_pass and score.disposition in ("FINITE", "PARTIAL") else "VIOLATED" if score.disposition == "NATIVE_CROSSCHECK_FAILED" else "UNEVALUABLE")


def _paired_inputs(specification, allocation, frozen, forecasts, outcomes, role):
    _selected(specification, allocation)
    if (type(frozen) is not ProtectedE3FrozenProducts or type(forecasts) is not tuple or type(outcomes) is not tuple
            or any(type(row) is not ProtectedE3Forecast for row in forecasts)
            or any(type(row) is not ProtectedE3PairedOutcome for row in outcomes)):
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
    return expected, fs, ys


def calibrate_protected_e3(specification, allocation, models, frozen, forecasts, outcomes, *, record_id):
    expected, fs, ys = _paired_inputs(specification, allocation, frozen, forecasts, outcomes, "calibration")
    if (type(models) is not ProtectedE3ModelSet or frozen.models != identity(models) or frozen.calibration is not None
            or models.specification != specification.identity or models.allocation != allocation.identity
            or models.reservation_join != frozen.reservation_join):
        raise ValueError("source-bound E3 CAL replaces its pre-calibration fitted freeze")
    scores = []
    for unit in expected:
        f, y = fs[unit], ys[unit]
        reasons = list(numerical.outcome_reasons(specification, y))
        if f.feature.disposition != "AVAILABLE":
            reasons.append(f.feature.disposition)
        score, tags = numerical.calibration_score(specification, f.log_points, y, reasons)
        scores.append((unit, score, tags))
    ranked = split_upper_calibration(tuple(row[1] for row in scores), specification.calibration_alpha)
    return ProtectedE3Calibration(record_id, specification.identity, allocation.identity, identity(models), identity(frozen),
        tuple(scores), ranked.rank, None if ranked.radius.is_infinite() else ranked.radius,
        tuple(identity(fs[unit]) for unit in expected), tuple(identity(ys[unit]) for unit in expected))


def assess_protected_e3(specification, allocation, frozen, forecasts, outcomes, *, record_id):
    expected, fs, ys = _paired_inputs(specification, allocation, frozen, forecasts, outcomes, "evaluation")
    if frozen.calibration is None:
        raise ValueError("source-bound E3 CONF lacks its exact calibrated freeze")
    decisions, coverage, kinds = [], [], []
    primary = exposed.ENDPOINTS.index((specification.measurement.primary_description, specification.measurement.primary_horizon))
    for unit in expected:
        f, y = fs[unit], ys[unit]
        reasons = list(numerical.outcome_reasons(specification, y))
        if f.feature.disposition != "AVAILABLE":
            reasons.append(f.feature.disposition)
        points = dict(f.log_points)
        usable, success, comparisons, tags = numerical.paired_root_decision(specification, points, y, primary, reasons)
        decisions.append(exposed.MatrixE3RootDecision(unit, usable, success, comparisons, tags))
        covered, slacks, kind = numerical.coverage_values(points, y, f.radius_kind, f.radius, usable)
        coverage.append((unit, covered, slacks))
        kinds.append((unit, kind))
    successes, usable_units = sum(row.success for row in decisions), sum(row.usable for row in decisions)
    tail = binomial_upper_tail(len(expected), successes, specification.assessment.null_probability)
    return ProtectedE3Assessment(record_id, specification.identity, allocation.identity, identity(frozen),
        tuple(identity(fs[unit]) for unit in expected), tuple(identity(ys[unit]) for unit in expected), tuple(decisions),
        successes, usable_units, tail.numerator, tail.denominator,
        tail <= specification.assessment.alpha and usable_units >= specification.assessment.minimum_usable_units,
        tuple(coverage), tuple(kinds))
