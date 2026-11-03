# SPDX-License-Identifier: MPL-2.0
"""Scheduled response operands, separate from every constant-alpha P record."""

from empirical_lawhood.kernel.decoding import validate_record_fields
from dataclasses import dataclass, fields
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_factor_response.records import ACTION_ROLES, PREDICTORS, SIGNS, MatrixFactorAction, MatrixFactorResponseModel
from empirical_lawhood.adapters.methods.matrix_factor_response.origin_mechanics import MatrixOriginResponseModel, model_predictors
from empirical_lawhood.adapters.methods.matrix_factor_response.response_scoring import (
    DENSE_RESPONSE_HORIZONS, RESPONSE_PRIMARY_TIMESTEP, RESPONSE_FINE_TIMESTEP,
    MatrixDenseResponseCell, MatrixDenseResponseDiagnostics,
)
from empirical_lawhood.adapters.methods.matrix_history_analysis.records import HISTORY_PURPOSES, MatrixHistorySeed
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA, MAXIMUM_MATRIX_ARRAY_BYTES, MatrixArrayMember
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, require_sorted_unique_ids, validate_decimal, validate_stable_id
from decimal import Decimal

from .forecast import ScheduledPublicSource
from .records import ScheduledCausalPrefix, ScheduledNativeEvidence
from .response_native import ScheduledResponseTransitionControl


def physical_forecast_implementation():
    """The installed zero-fit method, independent of any caller's model label."""
    from .response_bindings import response_manifest
    method = response_manifest('physical-forecast')
    return ObjectIdentity.from_record(method.capability_key, method)


@dataclass(frozen=True, slots=True)
class ScheduledResponseArrays(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-history/response-arrays'
    operand_id: str
    role: str
    source: ObjectIdentity
    array_artifact: ArtifactIdentity
    members: tuple[MatrixArrayMember, ...]
    producers: tuple[ObjectIdentity, ...]
    outcome_access: OutcomeAccess
    visibility_ceiling: VisibilityCeiling

    def __post_init__(self):
        validate_stable_id(self.operand_id)
        require_sorted_unique_ids(self.members, attribute='name', field_name='response members')
        require_sorted_unique_ids(self.producers, attribute='object_id', field_name='response producers')
        if (self.role not in ('TEMPLATES', 'FORECAST', 'RESPONSES') or not 0 < len(self.members) <= 256 or not self.producers
                or self.array_artifact.payload_schema != MATRIX_ARRAY_SCHEMA or self.array_artifact.media_type != 'application/x-npz'
                or not 0 < self.array_artifact.size_bytes <= MAXIMUM_MATRIX_ARRAY_BYTES
                or sum(m.size_bytes for m in self.members) > MAXIMUM_MATRIX_ARRAY_BYTES
                or self.role == 'TEMPLATES' and (self.outcome_access, self.visibility_ceiling) != (OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE)
                or self.role == 'FORECAST' and (self.outcome_access, self.visibility_ceiling) not in
                   ((OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE),
                    (OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY))
                or self.role == 'RESPONSES' and (self.outcome_access, self.visibility_ceiling) not in
                   ((OutcomeAccess.EVALUATION_SEALED, VisibilityCeiling.PROSPECTIVE),
                    (OutcomeAccess.EVALUATION_SEALED, VisibilityCeiling.DEVELOPMENT_ONLY),
                    (OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY))):
            raise ValueError('scheduled response array changes complete bounded/information scope')


def _validate_assay(value, artifact, members):
    """The same complete scientific instrument before and after source binding."""
    if (type(value.criterion) is not ObjectIdentity or type(value.mechanical_model) not in (MatrixFactorResponseModel, MatrixOriginResponseModel)
            or type(value.actions) is not tuple or any(type(action) is not MatrixFactorAction for action in value.actions)
            or type(artifact) is not ArtifactIdentity or type(members) is not tuple
            or any(type(member) is not MatrixArrayMember for member in members)):
        raise TypeError('scheduled response requires exact mathematical and coefficient records')
    validate_record_fields(value.criterion); validate_record_fields(value.mechanical_model); validate_record_fields(artifact)
    if type(value.mechanical_model) is MatrixOriginResponseModel and (
            value.horizon_steps != DENSE_RESPONSE_HORIZONS or value.receiver_count != 48
            or any(action.pulse_steps != 16 or action.amplitude != Decimal('0.01') for action in value.actions)):
        raise ValueError('amended origin response requires all29 horizons, HS48 and the fixed nominal pulse')
    require_sorted_unique_ids(value.actions, attribute='action_id', field_name='response actions')
    require_sorted_unique_ids(members, attribute='name', field_name='response members')
    for member in members:
        validate_record_fields(member)
    for action in value.actions:
        validate_record_fields(action)
    if (value.mechanical_model.implementation != physical_forecast_implementation()
            or tuple(sorted(a.role for a in value.actions)) != ACTION_ROLES
            or len({a.force_norm for a in value.actions}) != 1
            or type(value.horizon_steps) is not tuple
            or value.horizon_steps != tuple(sorted(set(value.horizon_steps))) or not value.horizon_steps
            or any(type(h) is not int or h < 1 for h in value.horizon_steps)
            or any(a.pulse_steps > value.horizon_steps[-1] for a in value.actions)
            or type(value.receiver_count) is not int or not 1 <= value.receiver_count <= 48
            or value.origin_rule != 'PRESERVED_DISTINCT_PRIMARY_FINE_CUTOFF_STATES_ORIGIN_FIXED_PRIMARY_Y_FRAME'):
        raise ValueError('scheduled response changes actual source/cutoff/duration/force/menu/receiver/origin scope')
    for name in ('hessian_difference_step', 'native_reference_tolerance', 'hessian_reference_tolerance', 'complement_gram_minimum', 'receiver_gram_tolerance'):
        validate_decimal(getattr(value, name), field_name=name, minimum=Decimal(0))
        if getattr(value, name) <= 0:
            raise ValueError('scheduled response requires explicit positive numerical references')
    for name in ('generic_gap_minimum', 'spectral_gap_minimum', 'radial_norm_minimum', 'weak_response_minimum'):
        validate_decimal(getattr(value, name), field_name=name, minimum=Decimal(0))
    expected = {'generic_basis': ('<c16', (3, 4, 4)), 'force_coefficients': ('<f8', (2, 3, 3)),
        'trace_coefficients': ('<f8', (2, 3)), 'receiver_coefficients': ('<f8', (value.receiver_count, 2, 2, 3, 4))}
    if ({m.name: (m.dtype, m.shape) for m in members} != expected or any(not m.finite_required for m in members)
            or artifact.payload_schema != MATRIX_ARRAY_SCHEMA or artifact.media_type != 'application/x-npz'
            or not 0 < artifact.size_bytes <= MAXIMUM_MATRIX_ARRAY_BYTES
            or sum(m.size_bytes for m in members) > MAXIMUM_MATRIX_ARRAY_BYTES):
        raise ValueError('scheduled response substitutes complete declared instrument coefficients')


@dataclass(frozen=True, slots=True)
class ScheduledResponseAssay(CanonicalRecord):
    """Complete source-independent instrument, including exact coefficient bytes."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-history/response-assay'
    assay_id: str
    criterion: ObjectIdentity
    mechanical_model: MatrixFactorResponseModel | MatrixOriginResponseModel
    actions: tuple[MatrixFactorAction, ...]
    horizon_steps: tuple[int, ...]
    receiver_count: int
    array_artifact: ArtifactIdentity
    members: tuple[MatrixArrayMember, ...]
    hessian_difference_step: Decimal
    generic_gap_minimum: Decimal
    spectral_gap_minimum: Decimal
    radial_norm_minimum: Decimal
    complement_gram_minimum: Decimal
    native_reference_tolerance: Decimal
    hessian_reference_tolerance: Decimal
    weak_response_minimum: Decimal
    receiver_gram_tolerance: Decimal
    origin_rule: str

    def __post_init__(self):
        validate_stable_id(self.assay_id)
        _validate_assay(self, self.array_artifact, self.members)

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.assay_id, self)

    def bind(self, source, *, protocol_id):
        """Bind only the newly reserved source; retain the existing output contract."""
        from .records import identity
        pin = identity(source)
        templates = ScheduledResponseArrays('templates.'+source.root_id, 'TEMPLATES', pin,
            self.array_artifact, self.members, (pin,), OutcomeAccess.OUTCOME_BLIND,
            VisibilityCeiling.PROSPECTIVE)
        values = {field.name: getattr(self, field.name) for field in fields(ScheduledResponseProtocol)
            if field.name not in ('protocol_id', 'public_source', 'templates')}
        return ScheduledResponseProtocol(protocol_id=protocol_id, public_source=ScheduledPublicSource.from_source(source),
            templates=templates, **values)


@dataclass(frozen=True, slots=True)
class ScheduledResponseProtocol(CanonicalRecord):
    """All selected physical/numerical parameters; no current future seeds."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-history/response-protocol'
    protocol_id: str
    public_source: ScheduledPublicSource
    criterion: ObjectIdentity
    mechanical_model: MatrixFactorResponseModel | MatrixOriginResponseModel
    actions: tuple[MatrixFactorAction, ...]
    horizon_steps: tuple[int, ...]
    receiver_count: int
    templates: ScheduledResponseArrays
    hessian_difference_step: Decimal
    generic_gap_minimum: Decimal
    spectral_gap_minimum: Decimal
    radial_norm_minimum: Decimal
    complement_gram_minimum: Decimal
    native_reference_tolerance: Decimal
    hessian_reference_tolerance: Decimal
    weak_response_minimum: Decimal
    receiver_gram_tolerance: Decimal
    origin_rule: str

    def __post_init__(self):
        validate_stable_id(self.protocol_id)
        if type(self.templates) is not ScheduledResponseArrays:
            raise TypeError('scheduled response requires exact bound template arrays')
        _validate_assay(self, self.templates.array_artifact, self.templates.members)
        if type(self.mechanical_model) is MatrixOriginResponseModel and (
                self.public_source.coordinate.primary_view.timestep != RESPONSE_PRIMARY_TIMESTEP
                or self.public_source.coordinate.fine_view.timestep != RESPONSE_FINE_TIMESTEP):
            raise ValueError('amended origin response changes its paired physical clock')
        if (type(self.public_source) is not ScheduledPublicSource
                or self.public_source.policy.cutoff_tick+self.horizon_steps[-1] > self.public_source.coordinate.total_ticks
                or self.templates.role != 'TEMPLATES' or self.templates.source != self.public_source.source
                or self.public_source.policy.origin_sector != 'Y'):
            raise ValueError('scheduled response changes actual source/cutoff/duration/force/menu/receiver/origin scope')

    def validate_error_design(self, design):
        criterion = design.criterion_record
        if (self.criterion != design.criterion or self.horizon_steps != criterion.horizon_steps
                or self.receiver_count != 48 or self.receiver_gram_tolerance != criterion.receiver_gram_tolerance
                or self.public_source.allocation != design.allocation
                or criterion.factor_rule != self.public_source.policy.factor_rule.identity
                or criterion.primary_timestep != self.public_source.coordinate.primary_view.timestep
                or tuple(sorted((a.role, a.amplitude, a.force_norm, a.pulse_steps) for a in self.actions)) !=
                   tuple(sorted((a.role, a.amplitude, a.force_norm, a.pulse_steps) for a in criterion.action_scales))):
            raise ValueError('scheduled response differs from exact frozen error target/menu/physical clock')


@dataclass(frozen=True, slots=True)
class ScheduledResponsePanel(CanonicalRecord):
    """Explicit group-owned future purpose scope, never another independent unit."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-history/response-panel'
    panel_id: str
    independent_group_id: str
    role: str
    stream_mode: str
    streams: tuple[MatrixHistorySeed, ...]

    def __post_init__(self):
        validate_stable_id(self.panel_id); validate_stable_id(self.independent_group_id)
        if (self.role not in ('COMMON_NOISE_PANEL', 'INDEPENDENT_FUTURE')
                or self.stream_mode not in ('ORIGINAL_COMPLETED_PREFIX_GENERATOR_STATES', 'FRESH_DECLARED_FUTURE_START_AT_CUTOFF')
                or (self.stream_mode == 'ORIGINAL_COMPLETED_PREFIX_GENERATOR_STATES') != (self.role == 'COMMON_NOISE_PANEL')
                or tuple(s.purpose for s in self.streams) != HISTORY_PURPOSES
                or any(type(s) is not MatrixHistorySeed for s in self.streams)
                or len({s.effective_seed for s in self.streams}) != 4):
            raise ValueError('scheduled response panel changes exact group/four-purpose future construction')

    def stream_identity(self, stream):
        if stream not in self.streams:
            raise ValueError('scheduled future stream is outside its original group/panel')
        return ObjectIdentity.from_record('future-stream.'+self.independent_group_id+'.'+self.panel_id+'.'+stream.purpose, stream)


@dataclass(frozen=True, slots=True)
class ScheduledResponseForecast(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-history/response-forecast'
    forecast_id: str
    source: ObjectIdentity
    causal_prefix: ObjectIdentity
    protocol: ObjectIdentity
    mechanical_model: ObjectIdentity
    frame_sha256: str | None
    arrays: ScheduledResponseArrays
    disposition: str
    dispositions: tuple[tuple[str, str, str, str | None], ...]

    def __post_init__(self):
        validate_stable_id(self.forecast_id)
        expected = tuple((v, p) for v in ('PRIMARY', 'FINE') for p in model_predictors(self.mechanical_model))
        if (self.causal_prefix.object_schema != ScheduledCausalPrefix.SCHEMA
                or self.protocol.object_schema != ScheduledResponseProtocol.SCHEMA or self.arrays.role != 'FORECAST'
                or self.arrays.source != self.source or tuple((v, p) for v, p, _, _ in self.dispositions) != expected
                or self.disposition not in ('AVAILABLE', 'NO_ORIGIN', 'UNEVALUABLE', 'INSTRUMENT_UNRESOLVED')
                or any(s not in ('AVAILABLE', 'UNRESOLVED') or (s == 'AVAILABLE') != (reason is None)
                    for _, _, s, reason in self.dispositions)):
            raise ValueError('scheduled forecast thins full paired predictor/menu or manufactures availability')


@dataclass(frozen=True, slots=True)
class ScheduledResponseNative(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-history/native-responses'
    response_id: str
    source: ObjectIdentity
    causal_prefix: ObjectIdentity
    physical_forecast: ObjectIdentity
    error_forecast: ObjectIdentity
    protocol: ObjectIdentity
    arrays: ScheduledResponseArrays
    branch_ids: tuple[str, ...]
    native: tuple[ScheduledNativeEvidence, ...]
    disposition: str
    reason_codes: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.response_id)
        if (self.arrays.source != self.source or self.arrays.role != 'RESPONSES'
                or self.branch_ids != tuple(sorted(set(self.branch_ids)))
                or self.disposition not in ('COMPLETED', 'NO_ORIGIN', 'UNEVALUABLE', 'INSTRUMENT_UNRESOLVED')
                or (self.disposition == 'COMPLETED') != bool(self.native)
                or self.native and len(self.native) != 1
                or any(type(n) is not ScheduledNativeEvidence for n in self.native)):
            raise ValueError('scheduled response changes actual branch/native/nonuse census')

    def validate_source(self, source, selection, history, causal, physical, error, *, native_context=None):
        from .records import identity
        from .source_index import ScheduledNativeSourceContext
        protocol, panels = selection.validate_source(source)
        if (self.source != identity(source) or self.causal_prefix != identity(causal)
                or self.physical_forecast != ObjectIdentity.from_record(physical.forecast_id, physical)
                or self.error_forecast != identity(error) or self.protocol != ObjectIdentity.from_record(protocol.protocol_id, protocol)
                or self.branch_ids != tuple(row[0] for row in branch_census(protocol, panels))
                or self.arrays.outcome_access is not (OutcomeAccess.DEVELOPMENT_VISIBLE if source.evidence_role == 'EXPOSED_DEVELOPMENT_NONPROMOTABLE' else OutcomeAccess.EVALUATION_SEALED)):
            raise ValueError('scheduled response substitutes complete original source/seals/menu/access')
        if not self.native:
            if causal.disposition == 'AVAILABLE' and physical.disposition == 'AVAILABLE':
                raise ValueError('scheduled response hides a requested available native collection')
            return
        role = 'responses-development' if source.evidence_role == 'EXPOSED_DEVELOPMENT_NONPROMOTABLE' else 'responses'
        if type(native_context) is not ScheduledNativeSourceContext or native_context.source != source:
            raise ValueError('scheduled pulse requires its actual authenticated native configuration context')
        configuration, parent_task, operation, shared_sources = native_context.contract(role)
        validate_response_native_evidence(self, source, selection.identity, history, causal, physical, error,
            configuration=configuration, parent_task=parent_task, operation=operation, shared_sources=shared_sources, panels=panels, protocol=protocol)


def validate_native_response_nonentry(response, causal, physical, protocol, panels):
    """One exact unavailable relation for the two distinct current native families."""
    from hashlib import sha256
    from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_records as train
    from empirical_lawhood.adapters.methods.matrix_factor_response import native_utility_records as utility
    if type(response) is utility.NativeUtilityResponse:
        causal_kind, physical_kind, label = utility.NativeUtilityCausalPrefix, utility.NativeUtilityPhysicalForecast, "native E2"
    elif type(response) is train.NativeTrainingResponse:
        causal_kind, physical_kind, label = train.NativeTrainingCausalPrefix, train.NativeTrainingPhysicalForecast, "native TRAIN"
    else:
        raise TypeError("native response nonentry requires an exact TRAIN or E2 response")
    if (type(causal) is not causal_kind or type(physical) is not physical_kind
            or type(protocol) is not ScheduledResponseProtocol or type(panels) is not tuple
            or any(type(panel) is not ScheduledResponsePanel for panel in panels)):
        raise TypeError(label + " response nonentry requires its exact actual operand records")
    validate_record_fields(response)
    expected = ("NO_ORIGIN" if causal.disposition == "NO_ORIGIN" else
        "INSTRUMENT_UNRESOLVED" if physical.disposition == "INSTRUMENT_UNRESOLVED" else "UNEVALUABLE")
    branches = tuple(row[0] for row in branch_census(protocol, panels))
    expected_hash = sha256(b"".join(value.to_bytes(8, "little", signed=True) for value in range(len(branches)))).hexdigest()
    pin = lambda value: ObjectIdentity.from_record(value.prefix_id if type(value) is causal_kind else
        value.forecast_id if type(value) is physical_kind else value.protocol_id, value)
    if (response.native or causal.disposition == physical.disposition == "AVAILABLE"
            or response.disposition != expected
            or response.reason_codes != ("complete-paired-branch-slots-not-entered-" + expected.lower(),)
            or (response.source, response.causal_prefix, response.physical_forecast, response.protocol) !=
                (protocol.public_source.source, pin(causal), pin(physical), pin(protocol))
            or (causal.source, physical.source, physical.causal_prefix, physical.protocol) !=
                (response.source, response.source, pin(causal), pin(protocol))
            or response.branch_ids != branches or len(response.arrays.members) != 1
            or (response.arrays.members[0].name, response.arrays.members[0].dtype, response.arrays.members[0].shape,
                response.arrays.members[0].sha256, response.arrays.members[0].finite_required) !=
                ("unentered_branches", "<i8", (len(branches),), expected_hash, True)):
        raise ValueError(label + " response nonentry changes unavailable operands, reason or exact complete branch markers")
    return response


def response_consumed_streams(source, protocol, streams):
    """Actual phase use within the complete reserved response stream roster."""
    protocol.public_source.validate_source(source)
    start = source.policy.cutoff_tick
    stop = start + protocol.horizon_steps[-1]
    ramp = source.coordinate.ramp_ticks
    return tuple(row for row in streams
        if row.object_id.endswith(('preparation-coarse-driver', 'preparation-fine-bridge')) and start < ramp
        or row.object_id.endswith(('autonomous-coarse-driver', 'autonomous-fine-bridge')) and stop > max(start, ramp))


def validate_response_native_evidence(self, source, selection, history, causal, physical, error, *,
        configuration, parent_task, operation, shared_sources, panels, protocol, native_sources=None):
    """Original nested receipt/array census with explicit owner-derived scope."""
    from hashlib import sha256
    from .records import identity
    event = self.native[0]
    d, completion, receipt = event.definition, event.completion, event.receipt
    streams = tuple(sorted((*tuple(source.root.stream_identity(s) for s in source.root.streams),
        *(p.stream_identity(s) for p in panels if p.role == 'INDEPENDENT_FUTURE' for s in p.streams)), key=lambda o: o.object_id))
    consumed = response_consumed_streams(source, protocol, streams)
    if (self.protocol != ObjectIdentity.from_record(protocol.protocol_id, protocol)
            or completion.consumed_streams != consumed
            or completion.unconsumed_streams != tuple(row for row in streams if row not in consumed)):
        raise ValueError('scheduled response changes its actual physical phase stream consumption')
    from empirical_lawhood.runtime.native_subwork import require_native_completion_receipt
    require_native_completion_receipt(completion, receipt, outcome_access=self.arrays.outcome_access,
        visibility_ceiling=self.arrays.visibility_ceiling)
    task = 'native-subwork.'+sha256((d.parent_contact.task_id+':'+d.subwork_id).encode()).hexdigest()
    attempt = d.parent_contact.run_id+'.'+task+'.attempt-001'
    expected_ids = {task+'.output.arrays', task+'.completion'}
    if (d.subwork_id != 'responses.'+source.root_id or d.operation_id != operation
            or d.configuration != configuration
            or d.parent_contact.task_id != parent_task
            or d.parent_contact.run_id != history.native.definition.parent_contact.run_id
            or d.parent_contact.implementation_commit != source.provenance.observed_git_head
            or d.code_sources_sha256 != source.provenance.code_sources_sha256 or d.dependency_lock_sha256 != source.provenance.dependency_lock_sha256
            or d.streams != streams or receipt.receipt_id != 'receipt.'+attempt
            or (receipt.run_id, receipt.task_id, receipt.attempt_id) != (d.parent_contact.run_id, task, attempt)
            or {a.logical_artifact_id for a in receipt.output_logical_artifacts} != expected_ids
            or {a.logical_artifact_id for a in receipt.output_materializations} != expected_ids
            or len(receipt.output_logical_artifacts) != 2 or len(receipt.output_materializations) != 2
            or completion.operational_status.value != 'SUCCEEDED'):
        raise ValueError('scheduled response loses exact original single48-branch native collection custody')
    expected_sources = tuple(sorted((*shared_sources, identity(history), identity(history.checkpoint), identity(causal), identity(error),
        ObjectIdentity.from_record(physical.forecast_id, physical), selection), key=lambda o: o.object_id))
    if native_sources is not None:
        if not operation.endswith(".direct-operands.v2"):
            raise ValueError("historical response cannot override its exact original native sources")
        expected_sources = tuple(sorted(native_sources, key=lambda row: row.object_id))
    if d.sources != expected_sources or completion.output_ids != ('arrays',) or completion.unknown_streams:
        raise ValueError('scheduled response replaces exact completed original sources/output/stream census')
    logical = next(a for a in receipt.output_logical_artifacts if a.logical_artifact_id == task+'.output.arrays')
    physical_array = next(a for a in receipt.output_materializations if a.logical_artifact_id == logical.logical_artifact_id)
    saved = self.arrays.array_artifact
    if (logical.payload_schema != saved.payload_schema or logical.media_type != saved.media_type or logical.content_sha256 != saved.sha256
            or physical_array.physical_sha256 != saved.sha256 or physical_array.size_bytes != saved.size_bytes
            or logical.outcome_access != self.arrays.outcome_access or logical.visibility_ceiling != self.arrays.visibility_ceiling):
        raise ValueError('scheduled ordinary response archive differs from original nested native bytes')


def branch_census(protocol, panels):
    if tuple(sorted(p.role for p in panels)) != ('COMMON_NOISE_PANEL', 'INDEPENDENT_FUTURE'):
        raise ValueError('scheduled response omits exact common/independent panel roles')
    return tuple(sorted((v.lower()+'.'+p.panel_id+'.'+a.action_id+'.'+sign.lower(), v, p, a, sign)
        for v in ('PRIMARY', 'FINE') for p in panels for a in protocol.actions for sign in SIGNS))


@dataclass(frozen=True, slots=True)
class ScheduledResponseLossCell(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-history/response-loss-cell'
    view: str
    panel_id: str
    action_id: str
    predictor: str
    horizon_tick: int
    actual_odd_responses: tuple[Decimal, ...] | None
    signed_errors: tuple[Decimal, ...] | None
    absolute_errors: tuple[Decimal, ...] | None
    relative_errors: tuple[Decimal | None, ...] | None
    normalized_error: Decimal | None

    def __post_init__(self):
        if (self.view not in ('PRIMARY', 'FINE') or self.predictor not in PREDICTORS
                or type(self.horizon_tick) is not int or self.horizon_tick < 1
                or self.actual_odd_responses is None and self.signed_errors is not None
                or (self.signed_errors is None) != (self.absolute_errors is None)
                or (self.signed_errors is None) != (self.relative_errors is None)
                or self.signed_errors is not None and (not self.signed_errors
                    or len(self.signed_errors) != len(self.absolute_errors) or len(self.signed_errors) != len(self.relative_errors)
                    or self.absolute_errors != tuple(abs(v) for v in self.signed_errors))):
            raise ValueError('scheduled loss cell changes exact paired view/receiver/task or missingness')
        for value in self.signed_errors or ():
            validate_decimal(value, field_name='actual signed response error')
        for value in self.actual_odd_responses or ():
            validate_decimal(value, field_name='actual signed native odd response')
        for value in (*(() if self.absolute_errors is None else self.absolute_errors),
                *(v for v in self.relative_errors or () if v is not None),
                *((self.normalized_error,) if self.normalized_error is not None else ())):
            validate_decimal(value, field_name='actual nonnegative response error', minimum=Decimal(0))

    @property
    def key(self):
        return self.view, self.panel_id, self.action_id, self.predictor, self.horizon_tick


@dataclass(frozen=True, slots=True)
class ScheduledResponseScore(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-history/response-score'
    VERSION: ClassVar[str] = '2.0.0'
    score_id: str
    source: ObjectIdentity
    causal_prefix: ObjectIdentity
    error_forecast: ObjectIdentity
    physical_forecast: ObjectIdentity
    responses: ObjectIdentity
    root_id: str
    independent_group_id: str
    role: str
    criterion: ObjectIdentity
    controls: tuple[ScheduledResponseTransitionControl, ...]
    numerical_pass: bool
    disposition: str
    cells: tuple[ScheduledResponseLossCell | MatrixDenseResponseCell, ...]
    cumulative_log_errors: tuple[Decimal | None, ...]
    reason_codes: tuple[str, ...]
    dense: MatrixDenseResponseDiagnostics | None = None

    def __post_init__(self):
        validate_response_score(self)


def validate_response_score(value):
    """One numerical score contract for scheduled, TRAIN and utility custody."""
    validate_stable_id(value.score_id); validate_stable_id(value.root_id); validate_stable_id(value.independent_group_id)
    amended = value.dense is not None
    if amended:
        if type(value.dense) is not MatrixDenseResponseDiagnostics:
            raise TypeError('amended score requires its exact complete dense diagnostics')
        validate_record_fields(value.dense)
        value.dense.validate_cells(value.cells)
        if value.dense.numerical_usable != value.numerical_pass or value.cumulative_log_errors != value.dense.factor_log_targets:
            raise ValueError('amended score changes numerical use or its exact58 FACTOR targets')
        if len(value.controls) not in (0, 48) or value.numerical_pass and len(value.controls) != 48:
            raise ValueError('amended score loses complete native branch controls')
    elif any(type(cell) is not ScheduledResponseLossCell for cell in value.cells):
        raise ValueError('closed five-method score substitutes an unbound amended measurement')
    if (len(value.cumulative_log_errors) != (58 if amended else 15) or type(value.numerical_pass) is not bool
            or value.disposition not in ('FINITE', 'PARTIAL', 'NO_ORIGIN', 'UNEVALUABLE', 'NATIVE_CROSSCHECK_FAILED', 'INSTRUMENT_UNRESOLVED')
            or value.disposition in ('FINITE', 'PARTIAL') and (not value.numerical_pass or not value.controls)
            or value.disposition == 'FINITE' and any(v is None for v in value.cumulative_log_errors)
            or value.numerical_pass and any(c.disposition != 'SATISFIED' for c in value.controls)
            or tuple(c.key for c in value.cells) != tuple(sorted({c.key for c in value.cells}))):
        raise ValueError('response score invents finite nonuse errors or drops its complete target contract')
    for error in value.cumulative_log_errors:
        if error is not None:
            validate_decimal(error, field_name='actual cumulative normalized log response error', minimum=Decimal(0))


def has_response_measurements(score):
    """Known native values, including numerically unusable retained diagnostics."""
    if score.dense is not None:
        return any(value is not None for curve in score.dense.amplitudes for value in curve.position_norms)
    return any(cell.actual_odd_responses is not None or cell.normalized_error is not None for cell in score.cells)



def _e4_original_forecast(physical):
    """Closed current E4 families; the base E3 forecast is not an E4 seal."""
    from .selected_e3_e4_records import SelectedE3E4MechanicalForecast
    from .selected_e4_native_records import SelectedE4ProtectedMechanicalForecast
    if type(physical) not in (SelectedE3E4MechanicalForecast, SelectedE4ProtectedMechanicalForecast):
        raise TypeError('dense E4 requires its exact actual DEV or protected mechanical forecast')
    validate_record_fields(physical)
    return ObjectIdentity.from_record(physical.forecast_id, physical)


@dataclass(frozen=True, slots=True)
class ScheduledE4DenseMechanicalForecast(CanonicalRecord):
    """Prediction-only supplementary archive, sealed with the original before futures."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-history/e4-dense-mechanical-forecast'
    VERSION: ClassVar[str] = "2.0.0"
    forecast_id: str
    source: ObjectIdentity
    causal_prefix: ObjectIdentity
    protocol: ObjectIdentity
    original_physical_forecast: ObjectIdentity
    secondary_target: ObjectIdentity
    secondary_selection: ObjectIdentity
    cutoff_tick: int
    arrays: ScheduledResponseArrays
    disposition: str
    dispositions: tuple[tuple[str, str, str, str | None], ...]

    def __post_init__(self):
        from empirical_lawhood.adapters.methods.matrix_factor_response.configured_secondary_readout import (
            E4_OBSERVATION_HORIZONS, MatrixE4SecondaryTarget, MatrixE4SecondaryReadoutSelection,
        )
        validate_stable_id(self.forecast_id)
        for value, kind in ((self.protocol, ScheduledResponseProtocol),
                (self.secondary_target, MatrixE4SecondaryTarget), (self.secondary_selection, MatrixE4SecondaryReadoutSelection)):
            if type(value) is not ObjectIdentity or (value.object_schema, value.object_version) != (kind.SCHEMA, kind.VERSION):
                raise TypeError('dense E4 forecast changes an exact protocol or target reference')
            validate_record_fields(value)
        from empirical_lawhood.adapters.methods.matrix_factor_response.origin_mechanics import ORIGIN_RESPONSE_PREDICTORS
        predictors = tuple(p for view, p, _, _ in self.dispositions if view == "PRIMARY")
        if predictors not in (PREDICTORS, ORIGIN_RESPONSE_PREDICTORS):
            raise ValueError("dense E4 forecast changes its complete original mechanical method menu")
        expected = {view + '_' + predictor.lower() for view in ('primary', 'fine') for predictor in predictors}
        members = {} if type(self.arrays) is not ScheduledResponseArrays else {m.name: m for m in self.arrays.members}
        if (type(self.cutoff_tick) is not int or self.cutoff_tick < 0 or type(self.arrays) is not ScheduledResponseArrays
                or self.arrays.role != 'FORECAST' or self.arrays.source != self.source or set(members) != expected
                or any(m.dtype != '<f8' or m.shape != (4, len(E4_OBSERVATION_HORIZONS), 48) for m in members.values())
                or self.disposition not in ('AVAILABLE', 'NO_ORIGIN', 'UNEVALUABLE', 'INSTRUMENT_UNRESOLVED')
                or tuple((v, p) for v, p, _, _ in self.dispositions) !=
                    tuple((v, p) for v in ('PRIMARY', 'FINE') for p in predictors)
                or any(state not in ('AVAILABLE', 'UNRESOLVED') or (state == 'AVAILABLE') != (reason is None)
                    for _, _, state, reason in self.dispositions)):
            raise ValueError('dense E4 forecast drops its exact prediction-only paired29grid or manufactures availability')
        validate_record_fields(self.arrays)

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.forecast_id, self)

    def validate_original(self, protocol, target, secondary, physical):
        from empirical_lawhood.adapters.methods.matrix_factor_response.configured_secondary_readout import MatrixE4SecondaryReadoutSelection
        if type(secondary) is not MatrixE4SecondaryReadoutSelection:
            raise TypeError('dense E4 forecast requires its actual frozen target publication selection')
        secondary.validate_target(target)
        target.validate_protocol(protocol)
        self.__post_init__()
        physical_pin = _e4_original_forecast(physical)
        if (self.original_physical_forecast != physical_pin or self.source != protocol.public_source.source
                or physical.source != self.source or self.causal_prefix != physical.causal_prefix
                or self.protocol != physical.protocol or self.protocol != ObjectIdentity.from_record(protocol.protocol_id, protocol)
                or physical.mechanical_model != ObjectIdentity.from_record(protocol.mechanical_model.model_id, protocol.mechanical_model)
                or self.secondary_target != target.identity or self.secondary_selection != secondary.identity
                or self.cutoff_tick != protocol.public_source.policy.cutoff_tick
                or (self.disposition, self.dispositions) != (physical.disposition, physical.dispositions)
                or (self.arrays.outcome_access, self.arrays.visibility_ceiling) !=
                    (physical.arrays.outcome_access, physical.arrays.visibility_ceiling)
                or self.arrays.producers != tuple(sorted((self.source, self.causal_prefix, physical_pin,
                    target.identity, secondary.identity), key=lambda value: value.object_id))
                or self.arrays.array_artifact == physical.arrays.array_artifact):
            raise ValueError('dense E4 forecast substitutes its original source/cutoff/seal/target or reuses the3point artifact')


@dataclass(frozen=True, slots=True)
class ScheduledE4DenseResponseCell(CanonicalRecord):
    """Lean instantaneous errors at PRIMARY steps in both matched physical views."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-history/e4-dense-response-cell'
    view: str
    panel_id: str
    action_id: str
    predictor: str
    horizon_tick: int
    position_error_norm: Decimal | None
    momentum_error_norm: Decimal | None
    normalized_error: Decimal | None

    def __post_init__(self):
        from empirical_lawhood.adapters.methods.matrix_factor_response.configured_secondary_readout import E4_OBSERVATION_HORIZONS
        validate_stable_id(self.panel_id)
        validate_stable_id(self.action_id)
        values = self.position_error_norm, self.momentum_error_norm, self.normalized_error
        if (self.view not in ('PRIMARY', 'FINE') or self.predictor not in PREDICTORS
                or type(self.horizon_tick) is not int or self.horizon_tick not in E4_OBSERVATION_HORIZONS
                or len({value is None for value in values}) != 1):
            raise ValueError('dense E4 cell changes its complete scientific key or unresolved norm tuple')
        for value in values:
            if value is not None:
                validate_decimal(value, field_name='instantaneous dense E4 error norm', minimum=Decimal(0))

    @property
    def key(self):
        return self.view, self.panel_id, self.action_id, self.predictor, self.horizon_tick


@dataclass(frozen=True, slots=True)
class ScheduledE4DenseResponseScore(CanonicalRecord):
    """Supplementary cells pinned to original ALL15 and exact received archives."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-history/e4-dense-response-score'
    VERSION: ClassVar[str] = "2.0.0"
    score_id: str
    original_score: ObjectIdentity
    dense_forecast: ObjectIdentity
    forecast_archive: ArtifactIdentity
    responses: ObjectIdentity
    response_archive: ArtifactIdentity
    secondary_target: ObjectIdentity
    secondary_selection: ObjectIdentity
    source: ObjectIdentity
    causal_prefix: ObjectIdentity
    protocol: ObjectIdentity
    cutoff_tick: int
    root_id: str
    independent_group_id: str
    role: str
    numerical_pass: bool
    disposition: str
    reason_codes: tuple[str, ...]
    cells: tuple[ScheduledE4DenseResponseCell | MatrixDenseResponseCell, ...]

    def __post_init__(self):
        from empirical_lawhood.adapters.methods.matrix_factor_response.configured_secondary_readout import (
            MatrixE4SecondaryTarget, MatrixE4SecondaryReadoutSelection,
        )
        for name in ('score_id', 'root_id', 'independent_group_id'):
            validate_stable_id(getattr(self, name))
        for value, kind in ((self.original_score, ScheduledResponseScore), (self.dense_forecast, ScheduledE4DenseMechanicalForecast),
                (self.secondary_target, MatrixE4SecondaryTarget), (self.secondary_selection, MatrixE4SecondaryReadoutSelection),
                (self.protocol, ScheduledResponseProtocol)):
            if type(value) is not ObjectIdentity or (value.object_schema, value.object_version) != (kind.SCHEMA, kind.VERSION):
                raise TypeError('dense E4 score changes an exact original or supplementary reference')
            validate_record_fields(value)
        matched = bool(self.cells) and type(self.cells[0]) is MatrixDenseResponseCell
        cell_type = MatrixDenseResponseCell if matched else ScheduledE4DenseResponseCell
        if (type(self.cutoff_tick) is not int or self.cutoff_tick < 0 or type(self.numerical_pass) is not bool
                or self.disposition not in ('FINITE', 'PARTIAL', 'NO_ORIGIN', 'UNEVALUABLE', 'NATIVE_CROSSCHECK_FAILED', 'INSTRUMENT_UNRESOLVED')
                or self.disposition in ('FINITE', 'PARTIAL') and not self.numerical_pass
                or type(self.cells) is not tuple or len(self.cells) != (3248 if matched else 2320)
                or any(type(cell) is not cell_type for cell in self.cells)
                or tuple(cell.key for cell in self.cells) != tuple(sorted({cell.key for cell in self.cells}))):
            raise ValueError('dense E4 score changes original nonuse/numerical state or duplicates its complete cell keys')
        for archive in (self.forecast_archive, self.response_archive):
            if type(archive) is not ArtifactIdentity or archive.payload_schema != MATRIX_ARRAY_SCHEMA or archive.media_type != 'application/x-npz':
                raise TypeError('dense E4 score requires its exact actual forecast/response archives')
            validate_record_fields(archive)
        for cell in self.cells:
            validate_record_fields(cell)

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.score_id, self)

    def validate_original(self, protocol, panels, target, secondary, score):
        from decimal import localcontext
        from empirical_lawhood.adapters.methods.matrix_factor_response.configured_secondary_readout import MatrixE4SecondaryReadoutSelection
        if type(score) is not ScheduledResponseScore or type(secondary) is not MatrixE4SecondaryReadoutSelection:
            raise TypeError('dense E4 score requires its exact original ALL15 score and target publication selection')
        validate_record_fields(score)
        secondary.validate_target(target)
        target.validate_protocol(protocol)
        self.__post_init__()
        branch_census(protocol, panels)
        expected = {(view, panel.panel_id, action.action_id, predictor, horizon)
            for view in ('PRIMARY', 'FINE') for panel in panels for action in protocol.actions
            for predictor in model_predictors(protocol.mechanical_model) for horizon in target.observation_horizons}
        if (len(panels) != 2 or len(protocol.actions) != 4 or len(self.cells) != len(expected)
                or {cell.key for cell in self.cells} != expected
                or self.original_score != ObjectIdentity.from_record(score.score_id, score)
                or (self.source, self.causal_prefix, self.responses, self.root_id, self.independent_group_id,
                    self.role, self.numerical_pass, self.disposition, self.reason_codes) !=
                    (score.source, score.causal_prefix, score.responses, score.root_id, score.independent_group_id,
                    score.role, score.numerical_pass, score.disposition, score.reason_codes)
                or score.criterion != protocol.criterion or self.source != protocol.public_source.source
                or self.protocol != ObjectIdentity.from_record(protocol.protocol_id, protocol)
                or self.cutoff_tick != protocol.public_source.policy.cutoff_tick
                or self.secondary_target != target.identity or self.secondary_selection != secondary.identity):
            raise ValueError('dense E4 score substitutes its complete original score/source/cutoff/target or scientific cell census')
        if score.dense is not None:
            from empirical_lawhood.adapters.methods.matrix_factor_response.response_scoring import validate_dense_score_units
            if self.cells != score.cells:
                raise ValueError('matched E4 projection changes its complete original dense cells')
            validate_dense_score_units(protocol, score)
            return
        original = {cell.key: cell for cell in score.cells}
        sampled = {cell.key: cell for cell in self.cells if cell.horizon_tick in protocol.horizon_steps}
        if set(original) != set(sampled):
            raise ValueError('dense E4 score loses the original3sample instantaneous cells')
        for key, old in original.items():
            dense = sampled[key]
            with localcontext() as context:
                context.prec = 60
                norms = ((None, None) if old.normalized_error is None else
                    (sum(value * value for value in old.signed_errors[:24]).sqrt(),
                     sum(value * value for value in old.signed_errors[24:]).sqrt()))
            if (dense.position_error_norm, dense.momentum_error_norm, dense.normalized_error) != (*norms, old.normalized_error):
                raise ValueError('dense E4 score changes original3sample error norms or normalized values')
        with localcontext() as context:
            context.prec = 60
            scales = {}
            for action in protocol.actions:
                for horizon in target.observation_horizons:
                    duration = target.primary_timestep * horizon
                    pulse = target.primary_timestep * min(action.pulse_steps, horizon)
                    impulse = action.amplitude * action.force_norm * pulse
                    scales[action.action_id, horizon] = impulse * (duration - pulse / 2), impulse
            for cell in self.cells:
                if cell.normalized_error is not None:
                    qscale, pscale = scales[cell.action_id, cell.horizon_tick]
                    if cell.normalized_error != max(cell.position_error_norm / qscale, cell.momentum_error_norm / pscale):
                        raise ValueError('dense E4 score changes its declared nominal-actuator normalization')
