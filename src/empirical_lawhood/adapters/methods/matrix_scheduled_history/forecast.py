# SPDX-License-Identifier: MPL-2.0
"""Scheduled-source pooled point forecasts, separate from every P contract.

This module fits no model and infers no exchangeability or source eligibility.
It consumes actual frozen operands and reuses the original numerical point and
split-rank equations. Calibration-bank point forecasts have no calibrated bound.
"""

from dataclasses import dataclass
from decimal import Decimal, localcontext
from hashlib import sha256
from typing import ClassVar

import numpy as np

from empirical_lawhood.adapters.methods.matrix_factor_response.response_error_joint_v2 import points, split_rank
from empirical_lawhood.adapters.methods.matrix_factor_response.response_error_prediction import FEATURES, MatrixResponseErrorModel, MatrixResponseErrorPredictionSpec, _validate_model
from empirical_lawhood.adapters.methods.matrix_factor_response.response_frontier import MatrixResponseFrontierProtocol
from empirical_lawhood.adapters.methods.matrix_factor_response.response_population_statistics import HORIZONS, STRATA
from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole
from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRoot
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history import MatrixParameterCoordinate
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, require_sorted_unique_ids, require_sorted_unique_strings, validate_decimal, validate_sha256, validate_stable_id
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteResult
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling

from .records import NAMESPACE, ScheduledAllocation, ScheduledCausalPrefix, ScheduledPrefixPolicy, ScheduledReservation, ScheduledSource, _publication, identity, physical_key

CALIBRATION_POINT = 'CALIBRATION_POINT_FORECAST_UNCALIBRATED'
DEVELOPMENT_POINT = 'EXPOSED_DEVELOPMENT_POINT_FORECAST_NOMINATION'
CALIBRATED_QUERY = 'FROZEN_POOLED_CALIBRATED_QUERY'
FAMILY_MAP = dict(zip(('matrix-history.joint-increasing-coupling', 'matrix-history.joint-decreasing-coupling',
    'matrix-history.x-first-increasing-coupling', 'matrix-history.y-first-increasing-coupling'), STRATA, strict=True))


def require_reserved_fit_input(spec, reservation, *, allocation_port, reservation_port, roles_port):
    """Read authentic prior scheduled publications before training inputs.

    The caller opens these original publications through its authenticated
    artifact plane. This join establishes ordering at the fitting entry, not
    the truth of an exposure audit or scientific qualification of a source.
    """
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from empirical_lawhood.runtime.execution import WorkerInputPort
    from empirical_lawhood.adapters.methods.matrix_factor_response.response_error_prediction import MatrixResponseDevelopmentRoles

    if type(spec) is not MatrixResponseErrorPredictionSpec or type(reservation) is not ScheduledReservation:
        raise ValueError('scheduled fit requires its actual training specification and prior reservation')
    spec.__post_init__()
    reservation.__post_init__()
    reservation.allocation.__post_init__()
    if spec.future_regime_reservation != identity(reservation):
        raise ValueError('scheduled fit substitutes its complete prior reservation')
    published = reservation.publication
    if (type(allocation_port) is not WorkerInputPort
            or allocation_port.artifact_id != published.logical.logical_artifact_id
            or allocation_port.materialization_id != published.materialization.materialization_id
            or allocation_port.payload_schema != ScheduledAllocation.SCHEMA
            or allocation_port.media_type != 'application/json'
            or allocation_port.size_bytes != published.materialization.size_bytes
            or allocation_port.outcome_access is not OutcomeAccess.OUTCOME_BLIND
            or allocation_port.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE):
        raise ValueError('scheduled fit lacks its actual prior allocation publication')

    def consume(port, reference, record, record_type):
        if (type(port) is not WorkerInputPort or port.artifact_id != reference.artifact_id
                or port.payload_schema != reference.payload_schema or port.media_type != reference.media_type
                or port.size_bytes != reference.size_bytes
                or port.outcome_access is not OutcomeAccess.OUTCOME_BLIND
                or port.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE):
            raise ValueError('scheduled fit substitutes a prior reservation or role publication')
        raw = port.read()
        if (len(raw) != port.size_bytes or sha256(raw).hexdigest() != reference.sha256
                or reference.sha256 != record.fingerprint()
                or decode_canonical_bytes(raw, record_type, maximum_bytes=None) != record):
            raise ValueError('scheduled fit changes complete original reservation or role bytes')

    raw = allocation_port.read()
    if (len(raw) != allocation_port.size_bytes
            or sha256(raw).hexdigest() != published.logical.content_sha256
            or sha256(raw).hexdigest() != published.materialization.physical_sha256
            or decode_canonical_bytes(raw, ScheduledAllocation, maximum_bytes=None) != reservation.allocation):
        raise ValueError('scheduled fit changes complete original allocation bytes')
    consume(reservation_port, spec.future_reservation_publication, reservation, ScheduledReservation)
    consume(roles_port, spec.roles_publication, spec.roles, MatrixResponseDevelopmentRoles)
    exposed_groups = {group for _, group, _, _, _ in spec.roles.rows}
    if exposed_groups & set(reservation.allocation.independent_group_ids):
        raise ValueError('scheduled fit leaks exposed training groups into reserved future roles')
    coordinates = {ObjectIdentity.from_record(c.coordinate_id, c): c for c in reservation.allocation.coordinates}
    withheld = {physical_key(coordinates[row.coordinate]) for row in reservation.allocation.roots
                if row.root.role is MatrixProgrammeRole.WITHHELD_TRANSFER}
    if len(withheld) != 2:
        raise ValueError('scheduled fit requires two distinct previously reserved whole E6 regimes')


@dataclass(frozen=True, slots=True)
class ScheduledPublicSource(CanonicalRecord):
    """Exact predictor view. It contains no stream seeds or generator states."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-history/public-source'
    source: ObjectIdentity
    root: MatrixProgrammeRoot
    coordinate: MatrixParameterCoordinate
    policy: ScheduledPrefixPolicy
    allocation: ObjectIdentity
    reservation: ObjectIdentity

    def __post_init__(self):
        if ((self.source.object_schema,self.source.object_version) != (ScheduledSource.SCHEMA,ScheduledSource.VERSION) or type(self.root) is not MatrixProgrammeRoot
                or type(self.coordinate) is not MatrixParameterCoordinate or type(self.policy) is not ScheduledPrefixPolicy
                or self.root.coordinate_id != self.coordinate.coordinate_id or self.root.clock_id != self.coordinate.clock_id
                or not 0 < self.policy.cutoff_tick < self.coordinate.total_ticks):
            raise ValueError('scheduled predictor changes its exact public source/clock/cutoff')

    @classmethod
    def from_source(cls, source):
        from .source_index import ResolvedScheduledSource
        from .selected_native_source import BoundSelectedNativeSource
        from .selected_e3_e4_records import SelectedE3E4NativeSource,SelectedE3E4NativeSourceReference
        from .selected_e4_native_records import SelectedE4ProtectedNativeSource,SelectedE4ProtectedNativeSourceReference
        if type(source) not in (ResolvedScheduledSource,BoundSelectedNativeSource,
                SelectedE3E4NativeSource,SelectedE3E4NativeSourceReference,
                SelectedE4ProtectedNativeSource,SelectedE4ProtectedNativeSourceReference):
            raise TypeError('scheduled predictor requires an explicit current resolved scientific source')
        source.__post_init__()
        reference=source.reference
        return cls(reference.identity,source.root.root,source.coordinate,source.policy,
            reference.allocation,reference.reservation)

    def validate_source(self, source):
        if self != type(self).from_source(source):
            raise ValueError('scheduled predictor public descriptor differs from original native source')


@dataclass(frozen=True, slots=True)
class ScheduledCalibrationCase(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-history/calibration-case'
    root_id: str
    independent_group_id: str
    source: ObjectIdentity
    coordinate: ObjectIdentity
    cutoff: Decimal
    score: ObjectIdentity
    point_forecast: ObjectIdentity
    score_receipt_id: str
    forecast_receipt_id: str
    score_materialization_id: str
    forecast_materialization_id: str
    disposition: str
    cumulative_log_errors: tuple[Decimal | None, ...]
    log_error_points: tuple[Decimal | None, ...]

    def __post_init__(self):
        for name in ('root_id', 'independent_group_id', 'score_receipt_id', 'forecast_receipt_id',
                'score_materialization_id', 'forecast_materialization_id'):
            validate_stable_id(getattr(self, name))
        validate_decimal(self.cutoff, field_name='actual calibration cutoff', minimum=Decimal(0))
        if ((self.source.object_schema,self.source.object_version) != (ScheduledSource.SCHEMA,ScheduledSource.VERSION) or self.coordinate.object_schema != MatrixParameterCoordinate.SCHEMA
                or self.score.object_schema != 'empirical-lawhood/matrix-scheduled-history/response-score'
                or self.point_forecast.object_schema != 'empirical-lawhood/matrix-scheduled-history/forecast-seal'
                or len(self.cumulative_log_errors) != 15 or len(self.log_error_points) != 15
                or self.disposition not in ('FINITE', 'PARTIAL', 'NO_ORIGIN', 'UNEVALUABLE', 'NATIVE_CROSSCHECK_FAILED', 'INSTRUMENT_UNRESOLVED')):
            raise ValueError('scheduled calibration case changes original full15 assessment/forecast custody scope')
        if self.disposition not in ('FINITE', 'PARTIAL') and any(v is not None for v in self.cumulative_log_errors):
            raise ValueError('scheduled calibration relabels unavailable/failed numerical source as finite response support')
        for menu in (self.cumulative_log_errors, self.log_error_points):
            for i, value in enumerate(menu):
                if value is not None:
                    validate_decimal(value, field_name='actual nonnegative log response endpoint', minimum=Decimal(0))
                    if i % 3 and (menu[i-1] is None or value < menu[i-1]):
                        raise ValueError('scheduled calibration hides earlier unresolved/larger response endpoint')


@dataclass(frozen=True, slots=True)
class ScheduledCalibration(CanonicalRecord):
    """Actual completed whole-group scores; None retains nonuse/infinite bound."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-history/calibration'
    calibration_id: str
    reservation: ObjectIdentity
    model: ObjectIdentity
    criterion: ObjectIdentity
    allocation: ObjectIdentity
    qualification_criterion: ObjectIdentity
    independent_unit_id: str
    family_ids: tuple[str, ...]
    cases: tuple[ScheduledCalibrationCase, ...]
    group_ids: tuple[str, ...]
    scores: tuple[tuple[str, Decimal | None, tuple[str, ...]], ...]
    original_assessments: tuple[ObjectIdentity, ...]
    outcome_sha256: str

    def __post_init__(self):
        validate_stable_id(self.calibration_id); validate_stable_id(self.independent_unit_id); validate_sha256(self.outcome_sha256)
        require_sorted_unique_strings(self.group_ids, field_name='group_ids', allow_empty=False)
        require_sorted_unique_strings(self.family_ids, field_name='family_ids', allow_empty=False)
        require_sorted_unique_ids(self.original_assessments, attribute='object_id', field_name='original_assessments')
        if (self.model.object_schema != MatrixResponseErrorModel.SCHEMA or self.criterion.object_schema != MatrixResponseFrontierProtocol.SCHEMA
                or self.allocation.object_schema != 'empirical-lawhood/matrix-scheduled-history/allocation'
                or self.qualification_criterion.object_schema != 'empirical-lawhood/matrix-scheduled-history/calibration-criterion'
                or tuple(g for g, _, _ in self.scores) != self.group_ids or not self.original_assessments
                or tuple(c.root_id for c in self.cases) != tuple(sorted({c.root_id for c in self.cases}))
                or tuple(sorted({c.independent_group_id for c in self.cases})) != self.group_ids
                or self.original_assessments != tuple(sorted((c.score for c in self.cases), key=lambda o: o.object_id))):
            raise ValueError('scheduled calibration omits actual complete whole-group assessment ancestry')
        for _, value, reasons in self.scores:
            require_sorted_unique_strings(reasons, field_name='score reasons', allow_empty=False)
            if value is not None:
                validate_decimal(value, field_name='whole-group maximum log-error residual', minimum=Decimal(0))
        from .calibration import reduce_cases
        if self.scores != reduce_cases(self.cases) or self.outcome_sha256 != _case_digest(self.cases):
            raise ValueError('scheduled calibration changes original complete whole-group residual reduction')


def _case_digest(cases):
    from hashlib import sha256
    from empirical_lawhood.kernel.serialization import canonical_json_bytes
    return sha256(canonical_json_bytes(cases)).hexdigest()


@dataclass(frozen=True, slots=True)
class ScheduledForecastDesign(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-history/forecast-design'
    design_id: str
    allocation: ObjectIdentity
    model_record: MatrixResponseErrorModel
    model_publication: ArtifactWriteResult
    training_record: MatrixResponseErrorPredictionSpec
    training_publication: ArtifactWriteResult
    criterion_record: MatrixResponseFrontierProtocol
    criterion_publication: ArtifactWriteResult
    source_scopes: tuple[tuple[str, str], ...]
    # Actual scores are delivered only through a sealed qualified-parent port.
    # Neither this blind design nor the predictor config embeds score values.
    calibration: ObjectIdentity | None
    calibration_publication: ArtifactWriteResult | None
    calibration_reservation: ObjectIdentity | None
    population_alpha: Decimal
    calibration_group_ids: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.design_id)
        require_sorted_unique_strings(self.calibration_group_ids, field_name='calibration_group_ids', allow_empty=False)
        if (type(self.model_record) is not MatrixResponseErrorModel or type(self.training_record) is not MatrixResponseErrorPredictionSpec
                or type(self.criterion_record) is not MatrixResponseFrontierProtocol
                or self.model_record.spec != self.training_record.identity
                or any(getattr(self.criterion_record, name) != getattr(self.training_record.population.policy.protocol, name)
                    for name in ('primary_timestep', 'horizon_steps', 'action_scales', 'receiver_gram_tolerance',
                                 'panel_roles', 'estimand', 'metric', 'aggregation'))
                or self.criterion_record.horizon_steps != HORIZONS
                or self.source_scopes != tuple(sorted(self.source_scopes))
                or len({root for root, _ in self.source_scopes}) != len(self.source_scopes)
                or any(scope not in (CALIBRATION_POINT, DEVELOPMENT_POINT, CALIBRATED_QUERY) for _, scope in self.source_scopes)
                or (self.calibration is None) != (self.calibration_publication is None)
                or (self.calibration is None) != (self.calibration_reservation is None)):
            raise ValueError('scheduled forecast design substitutes actual frozen model/training/criterion/scopes')
        validate_decimal(self.population_alpha, field_name='explicit pooled population alpha')
        if not 0 < self.population_alpha < 1:
            raise ValueError('scheduled pooled alpha must be explicitly in (0,1)')
        for record, publication in ((self.model_record, self.model_publication), (self.training_record, self.training_publication),
                (self.criterion_record, self.criterion_publication)):
            _publication(publication, record)
        _validate_model(self.training_record, self.model_record)
        if self.calibration is not None:
            p = self.calibration_publication
            if (self.calibration.object_schema != ScheduledCalibration.SCHEMA
                    or p.logical.payload_schema != ScheduledCalibration.SCHEMA
                    or p.logical.content_sha256 != self.calibration.object_fingerprint
                    or p.logical.profile is not ArtifactProfile.CANONICAL_JSON or p.logical.media_type != 'application/json'
                    or p.logical.outcome_access is not OutcomeAccess.EVALUATION_SEALED
                    or p.logical.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE
                    or p.materialization.physical_sha256 != self.calibration.object_fingerprint
                    or p.logical.logical_artifact_id != p.materialization.logical_artifact_id or p.materialization.size_bytes < 1):
                raise ValueError('scheduled calibration reference changes original sealed publication scope or identity')
        elif any(scope == CALIBRATED_QUERY for _, scope in self.source_scopes):
            raise ValueError('calibrated query requires original completed calibration package')

    @property
    def model(self):
        return ObjectIdentity.from_record(self.model_record.record_id, self.model_record)

    @property
    def training_spec(self):
        return self.training_record.identity

    @property
    def criterion(self):
        return self.criterion_record.identity

    def validate_source(self, source):
        scope = self.validate_public_source(ScheduledPublicSource.from_source(source))
        expected = tuple(sorted({r.root.independent_group_id for r in source.allocation.roots if r.root.role is MatrixProgrammeRole.CALIBRATION}))
        if self.calibration_group_ids != expected:
            raise ValueError('scheduled forecast drops actual requested calibration groups')
        return scope

    def validate_public_source(self, public):
        """Join the pre-fit reservation to the exact current public source."""
        if (self.allocation != public.allocation
                or self.training_record.future_regime_reservation != public.reservation
                or self.model_record.reservation != public.reservation):
            raise ValueError('scheduled forecast changes complete allocation or original pre-fit reservation')
        scope = dict(self.source_scopes).get(public.root.root_id)
        role = public.root.role
        if (scope is None or role is MatrixProgrammeRole.CALIBRATION and scope != CALIBRATION_POINT
                or role in (MatrixProgrammeRole.CONFIRMATION, MatrixProgrammeRole.WITHHELD_TRANSFER) and scope != CALIBRATED_QUERY
                or role is MatrixProgrammeRole.DEVELOPMENT and scope != DEVELOPMENT_POINT):
            raise ValueError('scheduled forecast changes explicit calibration/development/query role')
        if (self.criterion_record.factor_rule != public.policy.factor_rule.identity
                or self.criterion_record.primary_timestep != public.coordinate.primary_view.timestep
                or public.policy.origin_sector != 'Y'):
            raise ValueError('scheduled query differs from actual frozen feature/factor/physical clock criterion')
        if self.calibration is not None and self.calibration_reservation != public.reservation:
            raise ValueError('scheduled calibration substitutes prior complete reservation')
        return scope


@dataclass(frozen=True, slots=True)
class ScheduledForecastConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-history/forecast-config'
    config_id: str
    public_source: ScheduledPublicSource
    design: ScheduledForecastDesign

    def __post_init__(self):
        if (type(self.public_source) is not ScheduledPublicSource or type(self.design) is not ScheduledForecastDesign
                or self.config_id != 'config.'+NAMESPACE+'.'+self.public_source.root.root_id+'.'+
                   ('forecast-calibrated' if type(self) is ScheduledCalibratedForecastConfig else 'forecast')
                or self.design.allocation != self.public_source.allocation
                or self.public_source.root.root_id not in dict(self.design.source_scopes)
                or self.design.criterion_record.factor_rule != self.public_source.policy.factor_rule.identity
                or self.design.criterion_record.primary_timestep != self.public_source.coordinate.primary_view.timestep):
            raise ValueError('scheduled forecast configuration substitutes actual public source/model/criterion')
        scope = self.design.validate_public_source(self.public_source)
        if ((type(self) is ScheduledCalibratedForecastConfig) != (scope == CALIBRATED_QUERY)
                or self.public_source.root.role in (MatrixProgrammeRole.CONFIRMATION, MatrixProgrammeRole.WITHHELD_TRANSFER)
                   and scope != CALIBRATED_QUERY
                or self.public_source.root.role is MatrixProgrammeRole.DEVELOPMENT and scope != DEVELOPMENT_POINT):
            raise ValueError('scheduled forecast config changes actual blind-point versus sealed-query access')

    @property
    def root_id(self):
        return self.public_source.root.root_id


@dataclass(frozen=True, slots=True)
class ScheduledCalibratedForecastConfig(ScheduledForecastConfig):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-history/calibrated-forecast-config'


@dataclass(frozen=True, slots=True)
class ScheduledForecastFeature(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-history/forecast-feature'
    feature_id: str
    source: ObjectIdentity
    prefix: ObjectIdentity
    root_id: str
    independent_group_id: str
    family_id: str
    clock_id: str
    cutoff: Decimal
    frame_sha256: str | None
    disposition: str
    values: tuple[tuple[str, Decimal], ...]

    def __post_init__(self):
        validate_stable_id(self.feature_id)
        if ((self.source.object_schema,self.source.object_version) != (ScheduledSource.SCHEMA,ScheduledSource.VERSION) or self.prefix.object_schema != ScheduledCausalPrefix.SCHEMA
                or self.family_id not in STRATA or self.disposition not in ('AVAILABLE', 'NO_CAUSAL_ORIGIN', 'UNAVAILABLE', 'REFUSED')
                or (tuple(n for n, _ in self.values) != FEATURES if self.disposition == 'AVAILABLE' else bool(self.values))):
            raise ValueError('scheduled feature changes exact causal source/feature or nonuse scope')
        if self.frame_sha256 is not None:
            validate_sha256(self.frame_sha256)
        for _, value in self.values:
            validate_decimal(value, field_name='causal feature', minimum=Decimal(0))


@dataclass(frozen=True, slots=True)
class ScheduledForecastSeal(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-history/forecast-seal'
    seal_id: str
    source: ObjectIdentity
    prefix: ObjectIdentity
    design: ObjectIdentity
    model: ObjectIdentity
    criterion: ObjectIdentity
    calibration: ObjectIdentity | None
    scope: str
    feature: ScheduledForecastFeature
    raw_log_error_points: tuple[Decimal | None, ...]
    log_error_points: tuple[Decimal | None, ...]
    log_error_uppers: tuple[Decimal | None, ...]
    radius: Decimal | None

    def __post_init__(self):
        validate_stable_id(self.seal_id)
        if (self.source != self.feature.source or self.prefix != self.feature.prefix
                or self.design.object_schema != ScheduledForecastDesign.SCHEMA
                or self.scope not in (CALIBRATION_POINT, DEVELOPMENT_POINT, CALIBRATED_QUERY)
                or any(len(v) != 15 for v in (self.raw_log_error_points, self.log_error_points, self.log_error_uppers))
                or self.scope != CALIBRATED_QUERY and (self.calibration is not None or self.radius is not None or any(v is not None for v in self.log_error_uppers))):
            raise ValueError('scheduled seal invents a calibration bound or changes exact actual forecast scope')
        expected = []
        for start in range(0, 15, 3):
            prior, missing = Decimal(0), False
            for value in self.raw_log_error_points[start:start+3]:
                missing = missing or value is None
                if missing:
                    expected.append(None)
                else:
                    prior = max(prior, value); expected.append(prior)
        if (self.log_error_points != tuple(expected)
                or any(u != (None if self.radius is None or p is None else p+self.radius)
                       for p, u in zip(self.log_error_points, self.log_error_uppers, strict=True))
                or self.feature.disposition != 'AVAILABLE' and any(v is not None for v in (*self.raw_log_error_points, *self.log_error_points, *self.log_error_uppers))):
            raise ValueError('scheduled seal reverses cumulative horizons or manufactures finite nonuse predictions')


def forecast(design, source, prefix, feature, *, seal_id):
    scope = design.validate_source(source)
    return forecast_public(design, ScheduledPublicSource.from_source(source), prefix, feature, seal_id=seal_id, scope=scope)


def forecast_public(design, public, prefix, feature, *, seal_id, scope=None, calibration_record=None):
    """Calculate from public physical operands and opaque current-source IDs."""
    declared_scope = design.validate_public_source(public)
    if scope is not None and scope != declared_scope:
        raise ValueError('scheduled forecast changes the original declared role/scope')
    scope = declared_scope
    if (public.allocation != design.allocation or public.policy.factor_rule.identity != design.criterion_record.factor_rule
            or public.coordinate.primary_view.timestep != design.criterion_record.primary_timestep
            or prefix.source != public.source or feature.source != public.source or feature.prefix != identity(prefix)
            or prefix.root != public.root
            or (feature.root_id, feature.independent_group_id, feature.clock_id) !=
               (public.root.root_id, public.root.independent_group_id, public.root.clock_id)
            or feature.family_id != FAMILY_MAP[public.coordinate.family_id]
            or prefix.cutoff_tick != public.policy.cutoff_tick
            or feature.cutoff != public.coordinate.physical_time(public.policy.cutoff_tick)
            or feature.disposition == 'AVAILABLE' and prefix.disposition != 'AVAILABLE'
            or feature.frame_sha256 != prefix.frame_sha256):
        raise ValueError('scheduled forecast substitutes actual causal root/group/clock/frame/cutoff')
    raw, point = points(design, design.model_record, feature)
    radius, calibration = None, None
    if scope == CALIBRATED_QUERY:
        c = calibration_record
        if (type(c) is not ScheduledCalibration or identity(c) != design.calibration or c.reservation != public.reservation
                or c.allocation != public.allocation
                or c.model != design.model or c.criterion != design.criterion or c.group_ids != design.calibration_group_ids):
            raise ValueError('scheduled calibrated prediction lacks actual original sealed complete score package')
        values = tuple(row[1] for row in c.scores)
        rank = split_rank(len(values), design.population_alpha)
        ordered = tuple(sorted(v for v in values if v is not None))+(None,)*sum(v is None for v in values)
        radius = None if rank > len(values) else ordered[rank-1]
        calibration = ObjectIdentity.from_record(c.calibration_id, c)
    upper = tuple(None if radius is None or value is None else value+radius for value in point)
    return ScheduledForecastSeal(seal_id, public.source, identity(prefix), ObjectIdentity.from_record(design.design_id, design),
        design.model, design.criterion, calibration, scope, feature, raw, point, upper, radius)


def causal_feature(design, source, prefix, witness, causal_arrays, diagnostics, *, feature_id):
    """Actual declared pre-cutoff features; no producer, spectrum or future."""
    design.validate_source(source)
    return causal_feature_from_prefix(source, prefix, witness, causal_arrays, diagnostics,
        feature_id=feature_id, feature_window_ticks=design.training_record.feature_window_ticks,
        feature_cadence_ticks=design.training_record.feature_cadence_ticks)


def causal_feature_from_prefix(source, prefix, witness, causal_arrays, diagnostics, *, feature_id,
                              feature_window_ticks, feature_cadence_ticks):
    """Original causal feature equations with an explicit observation window.

    The caller authenticates the source and supplied prefix operands. This
    numerical consumer requires no historical forecast design, model or seal.
    """
    if (type(feature_window_ticks) is not int or feature_window_ticks <= 0
            or type(feature_cadence_ticks) is not int or feature_cadence_ticks <= 0):
        raise ValueError('causal feature window and cadence require positive exact integers')
    if (prefix.source != identity(source) or prefix.policy != identity(source.policy) or prefix.root != source.root.root
            or prefix.cutoff_tick != source.policy.cutoff_tick or witness.source != identity(source)
            or witness.history != prefix.history or witness.numerical != prefix.numerical):
        raise ValueError('scheduled feature substitutes actual prefix/source/witness/clock boundary')
    disposition, values = causal_feature_values(source.coordinate, source.policy,
        prefix_disposition=prefix.disposition, prefix_frame_sha256=prefix.frame_sha256,
        traces=witness.traces, causal_arrays=causal_arrays, diagnostics=diagnostics,
        feature_window_ticks=feature_window_ticks, feature_cadence_ticks=feature_cadence_ticks)
    return ScheduledForecastFeature(feature_id, identity(source), identity(prefix), source.root_id,
        source.root.root.independent_group_id, FAMILY_MAP[source.coordinate.family_id], source.coordinate.clock_id,
        source.coordinate.physical_time(source.policy.cutoff_tick), prefix.frame_sha256, disposition, values)


def causal_feature_values(coordinate, policy, *, prefix_disposition, prefix_frame_sha256, traces,
                          causal_arrays, diagnostics, feature_window_ticks, feature_cadence_ticks):
    """Original causal feature values from seedless physical prefix operands.

    Source custody and prefix/witness identity remain with the caller. The
    original numerical checks, native coupling bits and nonuse meanings apply.
    """
    if (type(feature_window_ticks) is not int or feature_window_ticks <= 0
            or type(feature_cadence_ticks) is not int or feature_cadence_ticks <= 0):
        raise ValueError('causal feature window and cadence require positive exact integers')
    disposition = 'NO_CAUSAL_ORIGIN' if prefix_disposition == 'NO_ORIGIN' else 'UNAVAILABLE'
    values = ()
    if prefix_disposition == 'AVAILABLE':
        try:
            c, tick = coordinate, policy.cutoff_tick
            if c.member.mass_x != c.member.mass_y:
                raise ValueError('existing frozen feature grammar has one potential mass')
            window, cadence = feature_window_ticks, feature_cadence_ticks
            selected = tuple(range(max(0, tick-window), tick+1, cadence))
            if len(selected) < 2 or selected[-1] != tick:
                raise ValueError('scheduled feature omits original frozen window/cadence')
            trace = next(t for t in traces if (t.view, t.sector) == ('PRIMARY', 'Y'))
            observed = {o.tick: o for o in trace.observations}
            samples = tuple(observed[t] for t in selected)
            if any(o.status != 'AVAILABLE' or o.identifiable is not True or o.alignment_ambiguous for o in samples):
                raise ValueError('scheduled feature has unavailable/unidentified causal observations')
            last = samples[-1]
            angles = tuple(o.adjacent_angle_degrees for o in samples[1:])
            if any(type(a) is not Decimal or not a.is_finite() or a < 0 for a in angles):
                raise ValueError('scheduled feature lacks actual within-window continuity diagnostics')
            spectrum = diagnostics['primary_y_spectrum'][-1]
            if (not np.isfinite(spectrum).all() or spectrum.shape != (15,)
                    or not np.array_equal(causal_arrays['primary_ticks'], np.arange(tick+1, dtype='<i8'))
                    or not np.array_equal(causal_arrays['fine_ticks'], np.arange(2*tick+1, dtype='<i8'))):
                raise ValueError('scheduled feature substitutes exact primary/fine clock or spectrum')
            frame = causal_arrays['frame']
            from hashlib import sha256
            if sha256(frame.tobytes()).hexdigest() != prefix_frame_sha256:
                raise ValueError('scheduled feature substitutes actual admitted frame')
            # Actual native coupling bits, independently joined to the schedule.
            alpha = causal_arrays['primary_alpha_tilde'][-1]
            if not np.array_equal(alpha, np.asarray(c.couplings(tick), dtype='<f8')):
                raise ValueError('scheduled feature substitutes targets for realized cutoff couplings')
            context = {'alpha-x': Decimal(repr(float(alpha[0]))), 'alpha-y': Decimal(repr(float(alpha[1]))),
                'bath-temperature': c.primary_view.bath_temperature, 'friction': c.primary_view.friction_gamma,
                'cross-gamma': c.member.cross_coupling_gamma, 'potential-m': c.member.mass_x,
                'cutoff': c.physical_time(tick),
                **{'family-'+f.rsplit('.', 1)[1]: Decimal(FAMILY_MAP[c.family_id] == f) for f in STRATA[1:]},
                'largest-y-rate': Decimal(repr(float(spectrum[-1]))),
                'third-fourth-y-gap': Decimal(repr(float(spectrum[3]-spectrum[2]))),
                'associative-leakage': last.associative_leakage, 'lie-leakage': last.lie_leakage,
                'factor-fit-angle': last.factor_fit_angle_degrees,
                'trailing-angle': max(angles)}
            with localcontext() as ctx:
                ctx.prec = 50
                context['slow-y-mean'] = sum(Decimal(repr(float(v))) for v in spectrum[:3])/3
                for name, label in (('positions', 'position'), ('momenta', 'momentum')):
                    state = causal_arrays['primary_'+name][-1]
                    for sector, index in (('x', 0), ('y', 1)):
                        context[label+'-'+sector+'-norm'] = (Decimal(1)+Decimal(repr(float(np.linalg.norm(state[index]))))).ln()
            for value in context.values():
                validate_decimal(value, field_name='actual nonnegative causal feature', minimum=Decimal(0))
            values, disposition = tuple(sorted(context.items())), 'AVAILABLE'
        except (ValueError, TypeError, KeyError, StopIteration):
            disposition = 'REFUSED'
    return disposition, values
