# SPDX-License-Identifier: MPL-2.0
"""Current E3 response contracts over supplied original numerical operands.

These joins establish consistency, never numerical support, source eligibility
or authority. The owning API authenticates the complete selection and original
publications once. A local native consumer receives its already bound source;
the physical forecaster receives only seedless public operands.
"""

from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledSource
from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ResolvedScheduledSource
from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_factor_response.records import PREDICTORS
from empirical_lawhood.adapters.methods.matrix_parameter_history.records import coordinate_identity
from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole
from empirical_lawhood.adapters.methods.matrix_scheduled_history.compact_records import compact_identity
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import (
    ScheduledNativeEvidence, identity as scheduled_identity,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import (
    ScheduledResponseArrays, ScheduledResponsePanel, ScheduledResponseProtocol, branch_census,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_selection import ScheduledResponseSelection
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling, inherited_visibility
from empirical_lawhood.kernel.experimental_design import UnitAllocation
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA, MatrixArrayMember
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, require_sorted_unique_strings, validate_decimal, validate_sha256, validate_stable_id
from empirical_lawhood.planning.study_authoring import MaterializationQualificationReceipt
from empirical_lawhood.runtime.artifacts import ArtifactMaterialization, ArtifactProfile, ArtifactWriteResult, CanonicalTaskReceipt, LogicalArtifactIdentity, derived_outcome_access
from empirical_lawhood.runtime.native_subwork import NativeSubworkCompletion, NativeSubworkDefinition, NativeSubworkOutput

from .experiment_specification import MatrixResponseErrorSpecification
from .protected_experiment_methods import (
    ProtectedE3Calibration, ProtectedE3Forecast, ProtectedE3FrozenProducts, ProtectedE3ModelSet,
)
from .protected_prefix_records import ProtectedE3CausalPrefix, ProtectedE3PrefixHistory
from .protected_protocol import ProtectedE3ProtocolProjection
from .protected_source_records import (
    NAMESPACE, ProtectedE3NativeSourceManifest, ProtectedE3ResponseSelection, _reference, _selected, identity,
)
from .response_frontier import MatrixResponseActionScale, MatrixResponseFrontierProtocol

NUMERICAL_FIELDS = ("hessian_difference_step", "generic_gap_minimum", "spectral_gap_minimum", "radial_norm_minimum",
    "complement_gram_minimum", "native_reference_tolerance", "hessian_reference_tolerance", "weak_response_minimum",
    "receiver_gram_tolerance")
POSITIVE_NUMERICAL_FIELDS = ("hessian_difference_step", "complement_gram_minimum", "native_reference_tolerance",
    "hessian_reference_tolerance", "receiver_gram_tolerance")


def _exact(record, kind):
    if type(record) is not kind:
        raise TypeError("protected E3 response requires exact current or original record types")
    record.__post_init__()


def _object(record):
    from .records import MatrixFactorResponseModel
    from .origin_mechanics import MatrixOriginResponseModel
    for kind, name in ((ScheduledResponseProtocol, "protocol_id"), (ScheduledResponsePanel, "panel_id"),
            (MatrixFactorResponseModel, "model_id"), (MatrixOriginResponseModel, 'model_id')):
        if type(record) is kind:
            return ObjectIdentity.from_record(getattr(record, name), record)
    return scheduled_identity(record)


def _profile_id(protocol):
    return "numerics." + NAMESPACE + "." + protocol.public_source.root.root_id


def _lookup(rows, target, key=lambda row: row[0]):
    """Resolve one member of an already validated canonical sorted census."""
    left, right = 0, len(rows)
    while left < right:
        middle = (left + right) // 2
        value = key(rows[middle])
        if value < target:
            left = middle + 1
        elif value > target:
            right = middle
        else:
            return rows[middle]
    return None


def _profile_provenance(protocol, provenance, publication, qualification):
    _exact(protocol, ScheduledResponseProtocol)
    if type(provenance) not in (ScheduledResponseProtocol, ProtectedE3ResponseSelection, ScheduledResponseSelection):
        raise TypeError("protected E3 numerical provenance requires an actual protocol or selection container")
    # The complete container is authenticated once by its owning API. Do not
    # rerun its full allocation/selection validator inside each local consumer.
    reference = _object(protocol)
    if type(provenance) is ScheduledResponseProtocol:
        bound = provenance == protocol
    elif type(provenance) is ProtectedE3ResponseSelection:
        bound = _lookup(provenance.root_protocols, protocol.public_source.root.root_id) == (protocol.public_source.root.root_id, reference)
    else:
        bound = _lookup(provenance.protocols, protocol.public_source.root.root_id,
            key=lambda row: row.public_source.root.root_id) == protocol
    if not bound:
        raise ValueError("protected E3 numerical provenance substitutes the exact original protocol member")
    if type(publication) is not ArtifactWriteResult:
        raise TypeError("protected E3 numerical provenance requires its actual container publication")
    _publication_metadata(publication)
    _exact(qualification, MaterializationQualificationReceipt)
    digest, size = provenance.fingerprint(), len(provenance.canonical_bytes())
    logical, physical = publication.logical, publication.materialization
    expected = ObjectIdentity(logical.logical_artifact_id, provenance.SCHEMA, provenance.VERSION, digest)
    if ((logical.payload_schema, logical.profile, logical.media_type, logical.content_sha256,
            physical.physical_sha256, physical.size_bytes, physical.logical_artifact_id) !=
            (provenance.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", digest, digest, size, logical.logical_artifact_id)
            or qualification.materialization != expected or qualification.content_sha256 != digest
            or (qualification.outcome_access, qualification.visibility_ceiling) !=
               (logical.outcome_access, logical.visibility_ceiling)):
        raise ValueError("protected E3 numerical provenance changes original container publication or qualification metadata")
    return _object(provenance)


def _publication_metadata(publication):
    _exact(publication, ArtifactWriteResult)
    for value, kind in ((publication.logical, LogicalArtifactIdentity), (publication.materialization, ArtifactMaterialization),
            (publication.manifest_materialization, ArtifactMaterialization)):
        _exact(value, kind)


@dataclass(frozen=True, slots=True)
class ProtectedE3ResponseNumericalProfile(CanonicalRecord):
    """Exact original values and provenance; no numerical adequacy judgment."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/protected-response-numerical-profile"
    record_id: str
    original_protocol: ObjectIdentity
    provenance_container: ObjectIdentity
    provenance_publication: ArtifactWriteResult
    qualification: ObjectIdentity
    hessian_difference_step: Decimal
    generic_gap_minimum: Decimal
    spectral_gap_minimum: Decimal
    radial_norm_minimum: Decimal
    complement_gram_minimum: Decimal
    native_reference_tolerance: Decimal
    hessian_reference_tolerance: Decimal
    weak_response_minimum: Decimal
    receiver_gram_tolerance: Decimal

    def __post_init__(self):
        validate_stable_id(self.record_id)
        _reference(self.original_protocol, ScheduledResponseProtocol)
        _reference(self.qualification, MaterializationQualificationReceipt)
        if (type(self.provenance_container) is not ObjectIdentity
                or (self.provenance_container.object_schema, self.provenance_container.object_version) not in {
                    (kind.SCHEMA, kind.VERSION) for kind in (ScheduledResponseProtocol, ProtectedE3ResponseSelection, ScheduledResponseSelection)}
                or type(self.provenance_publication) is not ArtifactWriteResult):
            raise ValueError("protected E3 numerical profile changes its actual provenance container")
        self.provenance_container.__post_init__()
        p = self.provenance_publication
        _publication_metadata(p)
        if (p.logical.payload_schema != self.provenance_container.object_schema
                or p.logical.profile is not ArtifactProfile.CANONICAL_JSON or p.logical.media_type != "application/json"
                or p.logical.content_sha256 != self.provenance_container.object_fingerprint
                or p.materialization.physical_sha256 != self.provenance_container.object_fingerprint
                or p.materialization.logical_artifact_id != p.logical.logical_artifact_id):
            raise ValueError("protected E3 numerical profile substitutes its original container bytes")
        for name in NUMERICAL_FIELDS:
            validate_decimal(getattr(self, name), field_name=name, minimum=Decimal(0))
            if name in POSITIVE_NUMERICAL_FIELDS and getattr(self, name) == 0:
                raise ValueError("protected E3 numerical profile changes an explicit positive original reference")

    def validate_protocol(self, protocol):
        self.__post_init__()
        _exact(protocol, ScheduledResponseProtocol)
        if (self.record_id != _profile_id(protocol) or self.original_protocol != _object(protocol)
                or any(getattr(self, name) != getattr(protocol, name) for name in NUMERICAL_FIELDS)):
            raise ValueError("protected E3 numerical profile differs from its exact original protocol values")

    def validate_original(self, protocol, *, provenance, publication, qualification):
        self.validate_protocol(protocol)
        container = _profile_provenance(protocol, provenance, publication, qualification)
        if (self.provenance_container != container or self.provenance_publication != publication
                or self.qualification != ObjectIdentity.from_record(qualification.receipt_id, qualification)):
            raise ValueError("protected E3 numerical profile substitutes original publication/qualification references")


def project_protected_e3_response_numerics(protocol: ScheduledResponseProtocol, *,
        provenance: ScheduledResponseProtocol | ProtectedE3ResponseSelection | ScheduledResponseSelection,
        publication: ArtifactWriteResult, qualification: MaterializationQualificationReceipt) -> ProtectedE3ResponseNumericalProfile:
    """Project supplied original values, preserving the container's access."""
    container = _profile_provenance(protocol, provenance, publication, qualification)
    return ProtectedE3ResponseNumericalProfile(_profile_id(protocol), _object(protocol), container, publication,
        ObjectIdentity.from_record(qualification.receipt_id, qualification), *(getattr(protocol, name) for name in NUMERICAL_FIELDS))


def _selected_protocol(specification, protocol, numerical_profile, projection, mathematical_protocol):
    """One local join; full candidate/population authentication stays upstream."""
    _selected(specification)
    for record, kind in ((protocol, ScheduledResponseProtocol), (numerical_profile, ProtectedE3ResponseNumericalProfile),
            (projection, ProtectedE3ProtocolProjection), (mathematical_protocol, MatrixResponseFrontierProtocol)):
        _exact(record, kind)
    numerical_profile.validate_protocol(protocol)
    public, measurement = protocol.public_source, specification.measurement
    scales = tuple(sorted((MatrixResponseActionScale(a.role, a.amplitude, a.force_norm, a.pulse_steps)
        for a in protocol.actions), key=lambda row: row.role))
    if (projection.specification != specification.identity or projection.candidate_sha256 != specification.protocol_sha256
            or projection.mathematical_protocol != mathematical_protocol.identity or protocol.criterion != mathematical_protocol.identity
            or projection.prefix_policy != _object(public.policy) or projection.prefix_rule != public.policy.factor_rule.identity
            or coordinate_identity(public.coordinate) != projection.nominal
            or public.root.role not in (MatrixProgrammeRole.CALIBRATION, MatrixProgrammeRole.CONFIRMATION)
            or public.policy.cutoff_tick != measurement.origin_tick or public.policy.origin_sector != "Y"
            or public.coordinate.primary_view.timestep != measurement.primary_timestep
            or public.coordinate.fine_view.timestep != measurement.fine_timestep
            or mathematical_protocol.primary_timestep != measurement.primary_timestep
            or protocol.horizon_steps != mathematical_protocol.horizon_steps or protocol.horizon_steps != measurement.horizons
            or protocol.receiver_count != measurement.receiver_count or protocol.receiver_gram_tolerance != mathematical_protocol.receiver_gram_tolerance
            or scales != mathematical_protocol.action_scales):
        raise ValueError("protected E3 response changes the original selected protocol, profile, physical source or action metric")


@dataclass(frozen=True, slots=True)
class ProtectedE3PhysicalForecastConfig(CanonicalRecord):
    """Only public references; never a manifest, history, model fit or stream."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/protected-physical-forecast-config"
    config_id: str
    root_id: str
    specification: ObjectIdentity
    protocol: ObjectIdentity
    numerical_profile: ObjectIdentity

    def __post_init__(self):
        validate_stable_id(self.root_id)
        for ref, kind in ((self.specification, MatrixResponseErrorSpecification), (self.protocol, ScheduledResponseProtocol),
                (self.numerical_profile, ProtectedE3ResponseNumericalProfile)):
            _reference(ref, kind)
        if self.config_id != "config." + NAMESPACE + "." + self.root_id + ".physical-forecast":
            raise ValueError("protected E3 physical config changes its exact current public task")


def _response_arrays(arrays, source, role, producers):
    _exact(arrays, ScheduledResponseArrays)
    for member in arrays.members:
        _exact(member, MatrixArrayMember)
    if (arrays.source != source or arrays.role != role
            or arrays.producers != tuple(sorted(producers, key=lambda row: row.object_id))):
        raise ValueError("protected E3 response arrays substitute exact source, phase or producers")


def validate_physical_information_scope(numerical_profile, *, outcome_access, visibility_ceiling):
    """Retain original numerical provenance while keeping future inputs absent.

    The worker supplies its actual compiled output lane. Numerical parameters
    from an exposed original container cannot become blind by projection.
    """
    _exact(numerical_profile, ProtectedE3ResponseNumericalProfile)
    if (outcome_access, visibility_ceiling) not in (
            (OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE),
            (OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY)):
        raise ValueError("protected E3 physical forecast changes its permitted information scope")
    parent = numerical_profile.provenance_publication.logical
    if (derived_outcome_access(outcome_access, parent.outcome_access) is not outcome_access
            or not visibility_ceiling.is_at_least_as_restrictive_as(
                inherited_visibility((parent.visibility_ceiling,), outcome_access))):
        raise ValueError("protected E3 physical forecast lowers original numerical provenance information scope")


def _physical_members(protocol, disposition, *, members=None):
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_forecast import frozen_member_layout
    return frozen_member_layout(protocol, disposition, members=members)



@dataclass(frozen=True, slots=True)
class ProtectedE3PhysicalForecast(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/protected-physical-forecast"
    forecast_id: str
    configuration: ObjectIdentity
    source: ObjectIdentity
    causal_prefix: ObjectIdentity
    protocol: ObjectIdentity
    numerical_profile: ObjectIdentity
    mechanical_model: ObjectIdentity
    frame_sha256: str | None
    arrays: ScheduledResponseArrays
    disposition: str
    dispositions: tuple[tuple[str, str, str, str | None], ...]

    def __post_init__(self):
        from .records import MatrixFactorResponseModel
        validate_stable_id(self.forecast_id)
        for ref, kind in ((self.configuration, ProtectedE3PhysicalForecastConfig), (self.source, ScheduledSource),
                (self.causal_prefix, ProtectedE3CausalPrefix), (self.protocol, ScheduledResponseProtocol),
                (self.numerical_profile, ProtectedE3ResponseNumericalProfile), (self.mechanical_model, MatrixFactorResponseModel)):
            _reference(ref, kind)
        if self.frame_sha256 is not None:
            validate_sha256(self.frame_sha256)
        _response_arrays(self.arrays, self.source, "FORECAST", (self.source, self.causal_prefix, self.protocol, self.numerical_profile))
        if (self.disposition not in ("AVAILABLE", "NO_ORIGIN", "UNEVALUABLE", "INSTRUMENT_UNRESOLVED")
                or type(self.dispositions) is not tuple
                or tuple((view, predictor) for view, predictor, _, _ in self.dispositions) != tuple(
                    (view, predictor) for view in ("PRIMARY", "FINE") for predictor in PREDICTORS)
                or any(status not in ("AVAILABLE", "UNRESOLVED") or (status == "AVAILABLE") != (reason is None)
                    for _, _, status, reason in self.dispositions)
                or self.disposition != "AVAILABLE" and any(status != "UNRESOLVED" for _, _, status, _ in self.dispositions)):
            raise ValueError("protected E3 physical forecast drops complete paired predictions or original nonuse")

    def validate_public_inputs(self, config, *, specification, protocol, numerical_profile, causal,
            mathematical_protocol, projection):
        self.__post_init__()
        _exact(config, ProtectedE3PhysicalForecastConfig)
        _exact(causal, ProtectedE3CausalPrefix)
        _selected_protocol(specification, protocol, numerical_profile, projection, mathematical_protocol)
        validate_physical_information_scope(numerical_profile, outcome_access=self.arrays.outcome_access,
            visibility_ceiling=self.arrays.visibility_ceiling)
        public = protocol.public_source
        if (config.root_id != public.root.root_id or config.specification != specification.identity
                or config.protocol != _object(protocol) or config.numerical_profile != identity(numerical_profile)
                or self.configuration != _object(config) or self.source != public.source
                or self.causal_prefix != identity(causal) or self.protocol != config.protocol or self.numerical_profile != config.numerical_profile
                or self.mechanical_model != _object(protocol.mechanical_model)
                or causal.source != public.source or causal.root != public.root or causal.policy != _object(public.policy)
                or causal.cutoff_tick != public.policy.cutoff_tick or self.frame_sha256 != causal.frame_sha256
                or causal.disposition != "AVAILABLE" and self.disposition != causal.disposition
                or causal.disposition == "AVAILABLE" and self.disposition not in ("AVAILABLE", "INSTRUMENT_UNRESOLVED")
                or {m.name: (m.dtype, m.shape) for m in self.arrays.members} != _physical_members(protocol, self.disposition)):
            raise ValueError("protected E3 physical forecast substitutes current public source, frame, protocol or complete witnesses")
        statuses = {(view.lower() + "_" + predictor.lower()): status for view, predictor, status, _ in self.dispositions}
        if any(member.finite_required != (statuses.get(member.name, "AVAILABLE") == "AVAILABLE") for member in self.arrays.members):
            raise ValueError("protected E3 physical forecast changes retained finite/unresolved member meaning")


@dataclass(frozen=True, slots=True)
class ProtectedE3ResponseConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/protected-response-config"
    VERSION: ClassVar[str] = '2.0.0'
    config_id: str
    operation: str
    specification: ObjectIdentity
    source_manifest: ObjectIdentity
    source: ScheduledSource
    response_selection: ObjectIdentity
    protocol: ObjectIdentity
    numerical_profile: ObjectIdentity

    def __post_init__(self):
        for ref, kind in ((self.specification, MatrixResponseErrorSpecification), (self.source_manifest, ProtectedE3NativeSourceManifest),
                (self.response_selection, ProtectedE3ResponseSelection), (self.protocol, ScheduledResponseProtocol),
                (self.numerical_profile, ProtectedE3ResponseNumericalProfile)):
            _reference(ref, kind)
        _exact(self.source, ScheduledSource)
        if (self.operation not in ("responses", "response-score")
                or self.source.root.root.role not in (MatrixProgrammeRole.CALIBRATION, MatrixProgrammeRole.CONFIRMATION)
                or self.config_id != "config." + NAMESPACE + "." + self.source.root_id + "." + self.operation):
            raise ValueError("protected E3 response config changes current phase/root or acquires reserved transfer")


def _bound_source(source, config, manifest, selection, protocol):
    """Match original source fields without hashing or walking its full roster."""
    if type(source) is not ResolvedScheduledSource or type(manifest) is not ProtectedE3NativeSourceManifest or type(selection) is not ProtectedE3ResponseSelection:
        raise TypeError("protected E3 response needs its already bound exact source and shared original records")
    descriptor, public = config.source, protocol.public_source
    if (config.source_manifest != identity(manifest) or config.response_selection != identity(selection)
            or selection.source_manifest != config.source_manifest or selection.specification != config.specification
            or source.source_id != descriptor.identity.object_id or source.root_id != descriptor.root_id
            or _object(source.reservation) != descriptor.reservation
            or _object(source.specification) != descriptor.specification or source.provenance.identity != descriptor.provenance
            or descriptor.allocation != _object(manifest.reservation.allocation)
            or descriptor.reservation != _object(manifest.reservation)
            or descriptor.specification != _object(manifest.native_specification)
            or descriptor.selection != _object(manifest.native_specification.selection)
            or public.source != descriptor.identity or public.root != descriptor.root.root
            or coordinate_identity(public.coordinate) != descriptor.coordinate or public.allocation != descriptor.allocation
            or public.reservation != descriptor.reservation
            or _lookup(selection.root_protocols, source.root_id) != (source.root_id, _object(protocol))
            or config.protocol != _object(protocol)):
        raise ValueError("protected E3 response changes its actual bound root/shared-source/protocol references")
    policy = dict(source.specification.selection.coordinate_policies).get(descriptor.coordinate)
    if policy != _object(public.policy):
        raise ValueError("protected E3 response changes its actual bound one-coordinate prefix policy")


def _panels(config, selection, protocol, panels):
    if type(panels) is not tuple or len(panels) != 2:
        raise ValueError("protected E3 response requires both original group-owned noise panels")
    for panel in panels:
        _exact(panel, ScheduledResponsePanel)
    group = config.source.root.root.independent_group_id
    refs = tuple(_object(panel) for panel in panels)
    if (tuple(sorted(p.role for p in panels)) != ("COMMON_NOISE_PANEL", "INDEPENDENT_FUTURE")
            or any(p.independent_group_id != group for p in panels)
            or refs != tuple(sorted(refs, key=lambda row: row.object_id))
            or _lookup(selection.group_panels, group) != (group, refs)
            or any(p.role == "COMMON_NOISE_PANEL" and p.streams != config.source.root.streams for p in panels)
            or protocol.public_source.root.independent_group_id != group):
        raise ValueError("protected E3 response substitutes exact selected panel records or original common streams")


def _error_forecast(specification, allocation, models, frozen, calibration, model_freeze, causal, protocol, error, descriptor):
    if type(allocation) is not UnitAllocation:
        raise TypeError("protected E3 response requires its authenticated original role allocation")
    for record, kind in ((models, ProtectedE3ModelSet), (frozen, ProtectedE3FrozenProducts), (error, ProtectedE3Forecast)):
        _exact(record, kind)
    # The complete allocation was validated once upstream. Reuse its one-unit
    # lookup and resolve one role without rebuilding or walking its roster.
    unit = allocation.unit(error.feature.unit_id)
    assignment = _lookup(allocation.roles, error.feature.unit_id, key=lambda row: row.unit_id)
    role = "calibration" if descriptor.root.root.role is MatrixProgrammeRole.CALIBRATION else "evaluation"
    if (error.specification != specification.identity or error.allocation != allocation.identity
            or models.specification != specification.identity or models.allocation != allocation.identity
            or frozen.specification != specification.identity or frozen.allocation != allocation.identity
            or error.models != identity(models) or error.frozen_products != identity(frozen)
            or frozen.models != identity(models) or frozen.reservation_join != models.reservation_join
            or error.role != role or unit is None or unit.exposed or assignment is None or assignment.role != role
            or error.feature.unit_id != descriptor.root.root.independent_group_id
            or error.feature.public_source != protocol.public_source or error.feature.source_manifest != descriptor.allocation
            or error.feature.prefix != identity(causal) or error.feature.frame_sha256 != causal.frame_sha256
            or error.feature.evidence != tuple(sorted((identity(causal), causal.numerical, causal.witness,
                causal.frame_assessment), key=lambda row: row.object_id))
            or error.feature.cutoff != specification.measurement.origin_tick * specification.measurement.primary_timestep
            or unit.source_id != descriptor.allocation.object_id or descriptor.allocation not in allocation.sources
            or descriptor.reservation not in allocation.sources):
        raise ValueError("protected E3 response substitutes actual source/role/current feature/fitted freeze")
    if role == "calibration":
        if calibration is not None or model_freeze is not None or frozen.calibration is not None or frozen.model_freeze is not None:
            raise ValueError("protected E3 CAL response cannot use calibrated products or outcomes")
    else:
        _exact(calibration, ProtectedE3Calibration)
        _exact(model_freeze, ProtectedE3FrozenProducts)
        if (frozen.calibration != identity(calibration) or frozen.model_freeze != identity(model_freeze)
                or calibration.model_freeze != identity(model_freeze)
                or model_freeze.specification != specification.identity or model_freeze.allocation != allocation.identity
                or model_freeze.models != identity(models) or model_freeze.reservation_join != models.reservation_join
                or model_freeze.calibration is not None or model_freeze.model_freeze is not None
                or calibration.specification != specification.identity or calibration.allocation != allocation.identity
                or calibration.models != identity(models) or error.radius != calibration.radius):
            raise ValueError("protected E3 CONF response changes its actual separately frozen calibration")


def protected_e3_response_native_contract(native_config, *, source, manifest, specification, selection, protocol,
        numerical_profile, panels, history, causal, physical, error):
    """Exact direct-input metadata only; the existing lifecycle owns effects."""
    _exact(native_config, ProtectedE3ResponseConfig)
    _selected(specification)
    for record, kind in ((protocol, ScheduledResponseProtocol), (numerical_profile, ProtectedE3ResponseNumericalProfile),
            (history, ProtectedE3PrefixHistory), (causal, ProtectedE3CausalPrefix),
            (physical, ProtectedE3PhysicalForecast), (error, ProtectedE3Forecast)):
        _exact(record, kind)
    if native_config.operation != "responses":
        raise ValueError("protected E3 native response requires the actual acquisition config")
    _bound_source(source, native_config, manifest, selection, protocol)
    _panels(native_config, selection, protocol, panels)
    numerical_profile.validate_protocol(protocol)
    if (native_config.specification != specification.identity or native_config.numerical_profile != identity(numerical_profile)
            or history.source != native_config.source.identity or causal.history != identity(history)
            or causal.source != history.source or physical.source != history.source or physical.causal_prefix != identity(causal)
            or physical.protocol != _object(protocol) or physical.numerical_profile != identity(numerical_profile)
            or error.feature.public_source != protocol.public_source or error.feature.prefix != identity(causal)):
        raise ValueError("protected E3 native metadata substitutes its actual current response operands")
    streams = tuple(sorted((*(native_config.source.root.stream_identity(s) for s in native_config.source.root.streams),
        *(p.stream_identity(s) for p in panels if p.role == "INDEPENDENT_FUTURE" for s in p.streams)), key=lambda row: row.object_id))
    sources = tuple(sorted((compact_identity(native_config.source), identity(manifest), specification.identity,
        coordinate_identity(protocol.public_source.coordinate), source.provenance.identity, identity(selection), _object(protocol),
        identity(numerical_profile), *(_object(p) for p in panels), identity(history), _object(history.checkpoint),
        identity(causal), _object(physical), identity(error)), key=lambda row: row.object_id))
    return (native_config.source.identity, _object(native_config), NAMESPACE + "." + source.root_id + ".responses",
        NAMESPACE + ".scheduled-paired-pulse-responses.v1", sources, streams,
        (NativeSubworkOutput("arrays", MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ, "application/x-npz"),))


@dataclass(frozen=True, slots=True)
class ProtectedE3NativeResponse(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/protected-native-responses"
    response_id: str
    configuration: ObjectIdentity
    source: ObjectIdentity
    history: ObjectIdentity
    causal_prefix: ObjectIdentity
    physical_forecast: ObjectIdentity
    error_forecast: ObjectIdentity
    protocol: ObjectIdentity
    numerical_profile: ObjectIdentity
    response_selection: ObjectIdentity
    arrays: ScheduledResponseArrays
    branch_ids: tuple[str, ...]
    native: tuple[ScheduledNativeEvidence, ...]
    disposition: str
    reason_codes: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.response_id)
        require_sorted_unique_strings(self.reason_codes, field_name="protected E3 response reasons")
        for ref, kind in ((self.configuration, ProtectedE3ResponseConfig), (self.source, ScheduledSource),
                (self.history, ProtectedE3PrefixHistory), (self.causal_prefix, ProtectedE3CausalPrefix),
                (self.physical_forecast, ProtectedE3PhysicalForecast), (self.error_forecast, ProtectedE3Forecast),
                (self.protocol, ScheduledResponseProtocol), (self.numerical_profile, ProtectedE3ResponseNumericalProfile),
                (self.response_selection, ProtectedE3ResponseSelection)):
            _reference(ref, kind)
        _response_arrays(self.arrays, self.source, "RESPONSES", (self.source, self.response_selection, self.physical_forecast, self.error_forecast, self.numerical_profile))
        if (self.arrays.outcome_access is not OutcomeAccess.EVALUATION_SEALED
                or self.arrays.visibility_ceiling not in (VisibilityCeiling.PROSPECTIVE, VisibilityCeiling.DEVELOPMENT_ONLY)
                or type(self.branch_ids) is not tuple or len(self.branch_ids) != 48 or self.branch_ids != tuple(sorted(set(self.branch_ids)))
                or type(self.native) is not tuple or len(self.native) > 1
                or self.disposition not in ("COMPLETED", "NO_ORIGIN", "UNEVALUABLE", "INSTRUMENT_UNRESOLVED")
                or (self.disposition == "COMPLETED") != bool(self.native)
                or bool(self.reason_codes) != (self.disposition != "COMPLETED")):
            raise ValueError("protected E3 response changes complete protected native or nonuse census")
        for event in self.native:
            _exact(event, ScheduledNativeEvidence)
            for value, kind in ((event.definition, NativeSubworkDefinition), (event.completion, NativeSubworkCompletion), (event.receipt, CanonicalTaskReceipt)):
                _exact(value, kind)

    def validate_source(self, native_config, *, source, specification, manifest, selection, protocol, numerical_profile,
            panels, history, causal, physical_config, physical, error, allocation, models, frozen, calibration, model_freeze,
            mathematical_protocol, projection):
        """Local consistency after authentic original source/prefix binding."""
        self.__post_init__()
        _exact(native_config, ProtectedE3ResponseConfig)
        if native_config.operation != "responses":
            raise ValueError("protected E3 native response requires its actual acquisition config")
        _exact(history, ProtectedE3PrefixHistory)
        _exact(causal, ProtectedE3CausalPrefix)
        _exact(physical, ProtectedE3PhysicalForecast)
        _selected_protocol(specification, protocol, numerical_profile, projection, mathematical_protocol)
        _bound_source(source, native_config, manifest, selection, protocol)
        _panels(native_config, selection, protocol, panels)
        physical.validate_public_inputs(physical_config, specification=specification, protocol=protocol,
            numerical_profile=numerical_profile, causal=causal, mathematical_protocol=mathematical_protocol, projection=projection)
        _error_forecast(specification, allocation, models, frozen, calibration, model_freeze, causal, protocol, error, native_config.source)
        if (native_config.specification != specification.identity or native_config.numerical_profile != identity(numerical_profile)
                or self.configuration != _object(native_config) or self.source != native_config.source.identity
                or self.history != identity(history) or history.source != self.source or causal.history != self.history
                or self.causal_prefix != identity(causal) or self.physical_forecast != _object(physical)
                or self.error_forecast != identity(error) or self.protocol != _object(protocol)
                or self.numerical_profile != identity(numerical_profile) or self.response_selection != identity(selection)
                or self.branch_ids != tuple(row[0] for row in branch_census(protocol, panels))):
            raise ValueError("protected E3 response substitutes complete original current source/forecast/profile joins")
        if not self.native:
            expected = "NO_ORIGIN" if causal.disposition == "NO_ORIGIN" else (
                "INSTRUMENT_UNRESOLVED" if physical.disposition == "INSTRUMENT_UNRESOLVED" else "UNEVALUABLE")
            if (causal.disposition == physical.disposition == "AVAILABLE" or self.disposition != expected
                    or {m.name: (m.dtype, m.shape) for m in self.arrays.members} != {"unentered_branches": ("<i8", (48,))}):
                raise ValueError("protected E3 response hides available work or changes original complete nonuse slots")
            return source
        if causal.disposition != "AVAILABLE" or physical.disposition != "AVAILABLE":
            raise ValueError("protected E3 response invents native work after original origin/instrument nonuse")
        names = {"noise." + panel.panel_id + "." + name for panel in panels for name in ("primary", "fine", "bridge")}
        names.update("branch." + branch + "." + name for branch in self.branch_ids
            for name in ("positions", "momenta", "innovations", "ticks", "alpha_tilde"))
        if {member.name for member in self.arrays.members} != names or any(not member.finite_required for member in self.arrays.members):
            raise ValueError("protected E3 response drops complete branch/noise members or permits nonfinite native paths")
        # Native custody and independent cold-array checks remain distinct from
        # the complete-unit metadata relation established by this record.
        _validate_current_native(self, native_config, source=source, manifest=manifest, specification=specification,
            selection=selection, protocol=protocol, numerical_profile=numerical_profile, panels=panels, history=history,
            causal=causal, physical=physical, error=error)
        return source


def _validate_current_native(response, config, **operands):
    from .protected_native_custody import validate_current_native
    return validate_current_native(response, config, native_contract=protected_e3_response_native_contract, **operands)
