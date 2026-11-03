# SPDX-License-Identifier: MPL-2.0
"""Separate candidate source identities for scheduled protected histories.

These records neither qualify exposed evidence nor grant authority. A selected
source requires original publications and ordinary platform qualification,
issue and execution. Historical E1, P and parameter records remain unchanged.
"""

from empirical_lawhood.kernel.decoding import validate_record_fields
from dataclasses import dataclass
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_factor_confirmation.records import E1FactorRule
from empirical_lawhood.adapters.methods.matrix_factor_response.eligibility import MatrixFactorExposureCensus
from empirical_lawhood.adapters.methods.matrix_factor_lifetime.records import FactorLifetime, FactorObservation
from empirical_lawhood.adapters.methods.matrix_history_analysis.records import HISTORY_PURPOSES, MatrixHistorySeed
from empirical_lawhood.adapters.methods.matrix_parameter_factor.records import MatrixParameterFactorControl, MatrixParameterFactorNumericalDesign
from empirical_lawhood.adapters.methods.matrix_parameter_history.records import (
    METHODS, MatrixParameterHistoryControl, MatrixParameterNumericalDesign, coordinate_identity,
)
from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole, MatrixProgrammeRoot
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history import MatrixParameterCoordinate
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history_segments import ParameterGeneratorState
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA, MAXIMUM_MATRIX_ARRAY_BYTES, MatrixArrayMember
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, require_sorted_unique_ids, require_sorted_unique_strings, validate_stable_id
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteResult, CanonicalTaskReceipt
from empirical_lawhood.runtime.native_effects import NativeEffectContact
from empirical_lawhood.runtime.native_subwork import NativeSubworkCompletion, NativeSubworkDefinition

NAMESPACE = 'matrix-scheduled-history'
CANDIDATE = 'ELIGIBLE_UNENTERED_CANDIDATE'
ROLES = tuple(MatrixProgrammeRole)


def identity(record):
    if not isinstance(record, CanonicalRecord):
        from .source_index import ResolvedScheduledSource
        if type(record) is ResolvedScheduledSource:
            return record.reference.identity
        from .selected_native_source import BoundSelectedNativeSource
        if type(record) is BoundSelectedNativeSource:
            return record.reference.identity
    for name in ('source_id', 'allocation_id', 'reservation_id', 'selection_id', 'specification_id',
                 'scope_id', 'policy_id', 'history_id', 'operand_id', 'checkpoint_id', 'assessment_id',
                 'prefix_id', 'product_id', 'config_id', 'design_id', 'spec_id', 'audit_id',
                 'commitment_id', 'calibration_id', 'feature_id', 'seal_id', 'record_id', 'score_id',
                 'response_id', 'forecast_id', 'criterion_id', 'relation_id'):
        if hasattr(record, name):
            return ObjectIdentity.from_record(getattr(record, name), record)
    raise ValueError('scheduled matrix record lacks its declared identity')


def physical_key(c):
    """Complete preparation regime; labels and numerical dt create no regime."""
    return (c.member.mass_x, c.member.mass_y, c.member.cross_coupling_gamma, c.member.beta_rule,
        c.primary_view.friction_gamma, c.primary_view.bath_temperature, c.family_id, c.target_x, c.target_y,
        c.decreasing_start, c.ramp_ticks*c.primary_view.timestep, c.autonomous_ticks*c.primary_view.timestep,
        c.initial_state_rule_id, c.preparation_rule_id)


def matched_key(c):
    """Same starts, schedule and absolute paired clocks across E4 coordinates."""
    return (c.member.mass_x, c.member.mass_y, c.member.beta_rule, c.family_id, c.target_x, c.target_y,
        c.decreasing_start, c.ramp_ticks, c.autonomous_ticks, c.observation_ticks,
        c.initial_state_rule_id, c.preparation_rule_id, c.primary_view.timestep, c.fine_view.timestep,
        c.primary_view.time_unit, c.primary_view.precision, c.primary_view.integrator,
        c.primary_view.rng_algorithm, c.primary_view.rng_version, c.primary_view.stream_derivation_rule_id)


def _publication(publication, record):
    if (type(publication) is not ArtifactWriteResult or publication.logical.payload_schema != record.SCHEMA
            or publication.logical.profile is not ArtifactProfile.CANONICAL_JSON
            or publication.logical.media_type != 'application/json'
            or publication.logical.content_sha256 != record.fingerprint()
            or publication.materialization.physical_sha256 != record.fingerprint()
            or publication.materialization.size_bytes != record.canonical_size_bytes()
            or publication.logical.logical_artifact_id != publication.materialization.logical_artifact_id
            or publication.logical.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE
            or publication.logical.outcome_access is not OutcomeAccess.OUTCOME_BLIND):
        raise ValueError('scheduled source requires exact original blind prospective publication')


@dataclass(frozen=True, slots=True)
class ScheduledRoot(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-history/root'
    root: MatrixProgrammeRoot
    coordinate: ObjectIdentity
    streams: tuple[MatrixHistorySeed, ...]

    def __post_init__(self):
        if (type(self.root) is not MatrixProgrammeRoot or self.root.role not in ROLES
                or self.coordinate.object_schema != MatrixParameterCoordinate.SCHEMA
                or self.coordinate.object_id != self.root.coordinate_id
                or tuple(s.purpose for s in self.streams) != HISTORY_PURPOSES
                or any(type(s) is not MatrixHistorySeed for s in self.streams)
                or len({s.effective_seed for s in self.streams}) != len(HISTORY_PURPOSES)):
            raise ValueError('scheduled root changes protected role, coordinate or four purposes')

    def stream_identity(self, stream):
        if stream not in self.streams:
            raise ValueError('scheduled stream is outside its exact root')
        # A matched coordinate is a case of one group, not a fresh stream unit.
        return ObjectIdentity.from_record('stream.'+self.root.independent_group_id+'.'+stream.purpose, stream)


@dataclass(frozen=True, slots=True)
class ScheduledMatchedScope(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-history/matched-scope'
    scope_id: str
    role: MatrixProgrammeRole
    independent_group_ids: tuple[str, ...]
    coordinates: tuple[ObjectIdentity, ...]
    construction: str

    def __post_init__(self):
        validate_stable_id(self.scope_id)
        require_sorted_unique_strings(self.independent_group_ids, field_name='independent_group_ids', allow_empty=False)
        require_sorted_unique_ids(self.coordinates, attribute='object_id', field_name='coordinates')
        if (self.role not in ROLES or not self.coordinates
                or any(c.object_schema != MatrixParameterCoordinate.SCHEMA for c in self.coordinates)
                or self.construction != 'COMMON_DECLARED_INITIAL_STATE_AND_FOUR_PURPOSE_PCG64DXSM_NOISE_COORDINATE_SPECIFIC_OU'):
            raise ValueError('matched source needs complete explicit role/coordinate/initial/noise scope')


@dataclass(frozen=True, slots=True)
class ScheduledExposure(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-history/exposure'
    scope_id: str
    census: MatrixFactorExposureCensus
    prior_scheduled_coordinates: tuple[MatrixParameterCoordinate, ...]
    scheduled_audit: ArtifactIdentity

    def __post_init__(self):
        validate_stable_id(self.scope_id)
        require_sorted_unique_ids(self.prior_scheduled_coordinates, attribute='coordinate_id', field_name='prior_scheduled_coordinates')
        if type(self.census) is not MatrixFactorExposureCensus or type(self.scheduled_audit) is not ArtifactIdentity:
            raise ValueError('scheduled exposure requires original full stream/group and schedule audit operands')


def _validate_allocation_members(coordinates, roots, matched_scopes, *, census, prior_scheduled_coordinates):
    """Shared pure membership checks before publication and at canonical construction."""
    require_sorted_unique_ids(coordinates, attribute='coordinate_id', field_name='coordinates')
    require_sorted_unique_ids(matched_scopes, attribute='scope_id', field_name='matched_scopes')
    root_ids = tuple(r.root.root_id for r in roots)
    if (not coordinates or not roots or root_ids != tuple(sorted(set(root_ids)))
            or any(type(r) is not ScheduledRoot for r in roots)):
        raise ValueError('scheduled allocation omits complete candidate roots/source exposure')
    coordinates_by_pin = {coordinate_identity(c): c for c in coordinates}
    consumed_seeds = set(census.effective_seed_exclusions)
    exposed_groups = set(census.exposed_independent_groups)
    roots_by_group = {}
    names, used, roles, stream_owners, regimes, cells = {}, set(), {}, {}, {}, set()
    physical_roles = {}
    for c in coordinates:
        if c.primary_view.rng_algorithm not in ('numpy.pcg64dxsm', 'numpy-pcg64dxsm'):
            raise ValueError('scheduled history requires declared PCG64DXSM paired views')
        for name, record in ((c.member.member_id, c.member), (c.primary_view.view_id, c.primary_view), (c.fine_view.view_id, c.fine_view)):
            if names.setdefault(name, record) != record:
                raise ValueError('scheduled allocation aliases different member/view bytes')
    for row in roots:
        root = row.root
        roots_by_group.setdefault(root.independent_group_id, []).append(row)
        if row.coordinate not in coordinates_by_pin or root.clock_id != coordinates_by_pin[row.coordinate].clock_id:
            raise ValueError('scheduled allocation substitutes exact coordinate or physical clock')
        c, cell = coordinates_by_pin[row.coordinate], (root.independent_group_id, row.coordinate)
        if cell in cells or roles.setdefault(root.independent_group_id, root.role) is not root.role:
            raise ValueError('scheduled matched group duplicates a case or crosses roles')
        cells.add(cell); used.add(row.coordinate)
        if root.independent_group_id in exposed_groups:
            raise ValueError('exposed group cannot enter protected calibration/evaluation/transfer')
        key = physical_key(c)
        if regimes.setdefault(root.regime_id, key) != key:
            raise ValueError('scheduled regime label mixes full preparation physics')
        physical_roles.setdefault(key, set()).add(root.role)
        for stream in row.streams:
            owner = (root.independent_group_id, stream.purpose)
            if stream.effective_seed in consumed_seeds or stream_owners.setdefault(stream.effective_seed, owner) != owner:
                raise ValueError('scheduled effective stream is exposed or shared across group/purpose')
    if used != set(coordinates_by_pin):
        raise ValueError('scheduled allocation omits a selected coordinate')
    scope_groups = set()
    for scope in matched_scopes:
        if type(scope) is not ScheduledMatchedScope or not set(scope.coordinates) <= set(coordinates_by_pin):
            raise ValueError('matched scope substitutes selected complete coordinates')
        if len({matched_key(coordinates_by_pin[c]) for c in scope.coordinates}) != 1:
            raise ValueError('matched coordinates change initial state, schedule or absolute physical clocks')
        scope_coordinates = set(scope.coordinates)
        for group in scope.independent_group_ids:
            rows = roots_by_group.get(group, ())
            if (group in scope_groups or not rows or {r.coordinate for r in rows} != scope_coordinates
                    or any(r.root.role is not scope.role or r.streams != rows[0].streams for r in rows)):
                raise ValueError('matched group omits coordinates or changes role/common four streams')
            scope_groups.add(group)
    if scope_groups != set(roles):
        raise ValueError('scheduled allocation omits whole-group matched scopes')
    prior = {physical_key(c) for c in prior_scheduled_coordinates}
    prior.update(value.key for value in census.scheduled_physical_exclusions)
    old_constant = {r.key for r in census.constant_physical_exclusions}
    for key, role_set in physical_roles.items():
        if MatrixProgrammeRole.WITHHELD_TRANSFER in role_set:
            constant = (key[0], key[1], key[2], key[3], key[5], key[4], key[7], key[8])
            if len(role_set) != 1 or key in prior or constant in old_constant:
                raise ValueError('withheld source overlaps upstream or actually exposed physical preparation regime')


@dataclass(frozen=True, slots=True)
class ScheduledAllocation(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-history/allocation'
    allocation_id: str
    coordinates: tuple[MatrixParameterCoordinate, ...]
    roots: tuple[ScheduledRoot, ...]
    matched_scopes: tuple[ScheduledMatchedScope, ...]
    exposure: ScheduledExposure
    evidence_role: str = CANDIDATE

    def __post_init__(self):
        validate_stable_id(self.allocation_id)
        if type(self.exposure) is not ScheduledExposure or self.evidence_role != CANDIDATE:
            raise ValueError('scheduled allocation omits complete candidate roots/source exposure')
        _validate_allocation_members(self.coordinates, self.roots, self.matched_scopes,
            census=self.exposure.census, prior_scheduled_coordinates=self.exposure.prior_scheduled_coordinates)

    @property
    def independent_group_ids(self):
        return tuple(sorted({r.root.independent_group_id for r in self.roots}))


@dataclass(frozen=True, slots=True)
class ScheduledReservation(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-history/reservation'
    reservation_id: str
    allocation: ScheduledAllocation
    publication: ArtifactWriteResult

    def __post_init__(self):
        validate_stable_id(self.reservation_id)
        if type(self.allocation) is not ScheduledAllocation:
            raise ValueError('scheduled reservation cannot relabel historical allocation')
        _publication(self.publication, self.allocation)


@dataclass(frozen=True, slots=True)
class ScheduledPrefixPolicy(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-history/prefix-policy'
    policy_id: str
    cutoff_tick: int
    factor_rule: E1FactorRule
    factor_numerical_design: MatrixParameterFactorNumericalDesign
    origin_sector: str
    origin_policy: str

    def __post_init__(self):
        validate_stable_id(self.policy_id)
        if (type(self.cutoff_tick) is not int or self.cutoff_tick < 1 or type(self.factor_rule) is not E1FactorRule
                or type(self.factor_numerical_design) is not MatrixParameterFactorNumericalDesign
                or self.factor_rule.lattice[-1] != self.cutoff_tick or self.origin_sector not in self.factor_rule.sectors
                or self.origin_policy != 'FIXED_DECLARED_CUTOFF_CAUSALLY_ADMITTED_PRIMARY_FRAME'):
            raise ValueError('scheduled causal prefix requires exact frozen cutoff/admission/frame policy')


@dataclass(frozen=True, slots=True)
class ScheduledSelection(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-history/selection'
    selection_id: str
    reservation: ObjectIdentity
    numerical_design: MatrixParameterNumericalDesign
    prefix_policies: tuple[ScheduledPrefixPolicy, ...]
    coordinate_policies: tuple[tuple[ObjectIdentity, ObjectIdentity], ...]

    def __post_init__(self):
        validate_stable_id(self.selection_id)
        require_sorted_unique_ids(self.prefix_policies, attribute='policy_id', field_name='prefix_policies')
        if (self.reservation.object_schema != ScheduledReservation.SCHEMA or type(self.numerical_design) is not MatrixParameterNumericalDesign
                or not self.prefix_policies or not self.coordinate_policies
                or tuple(c.object_id for c, _ in self.coordinate_policies) != tuple(sorted({c.object_id for c, _ in self.coordinate_policies}))
                or any(c.object_schema != MatrixParameterCoordinate.SCHEMA or p not in {identity(p) for p in self.prefix_policies} for c, p in self.coordinate_policies)
                or {p for _, p in self.coordinate_policies} != {identity(p) for p in self.prefix_policies}):
            raise ValueError('scheduled selection omits exact caller-selected coordinate/prefix/numerical closure')


@dataclass(frozen=True, slots=True)
class ScheduledSpecification(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-history/specification'
    specification_id: str
    selection: ScheduledSelection
    publication: ArtifactWriteResult

    def __post_init__(self):
        validate_stable_id(self.specification_id)
        if type(self.selection) is not ScheduledSelection:
            raise ValueError('scheduled freeze cannot accept historical scientific selections')
        _publication(self.publication, self.selection)


@dataclass(frozen=True, slots=True)
class ScheduledSource(CanonicalRecord):
    """One root's scientific identity, referring to shared immutable parents."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-history/source'
    VERSION: ClassVar[str] = '2.0.0'
    source_id: str
    root: ScheduledRoot
    allocation: ObjectIdentity
    reservation: ObjectIdentity
    specification: ObjectIdentity
    selection: ObjectIdentity
    provenance: ObjectIdentity

    def __post_init__(self):
        validate_stable_id(self.source_id)
        if type(self.root) is not ScheduledRoot:
            raise TypeError('scheduled source requires its exact local assigned root and streams')
        validate_record_fields(self.root)
        for reference, kind in ((self.allocation, ScheduledAllocation), (self.reservation, ScheduledReservation),
                (self.specification, ScheduledSpecification), (self.selection, ScheduledSelection),
                (self.provenance, NumericalProducingProvenance)):
            if (type(reference) is not ObjectIdentity or
                    (reference.object_schema, reference.object_version) != (kind.SCHEMA, kind.VERSION)):
                raise ValueError('scheduled source changes an exact current shared scientific parent')
            validate_record_fields(reference)

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.source_id, self)

    @property
    def root_id(self):
        return self.root.root.root_id

    @property
    def coordinate(self):
        return self.root.coordinate


@dataclass(frozen=True, slots=True)
class ScheduledConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-history/config'
    VERSION: ClassVar[str] = '2.0.0'
    config_id: str
    operation: str
    source: ScheduledSource
    commitment_config: ObjectIdentity

    def __post_init__(self):
        from .commitment import ScheduledCommitmentConfig
        if (type(self.source) is not ScheduledSource or self.operation not in
                ('prefix', 'continue', 'continue-development', 'numerical', 'measure', 'check', 'project',
                 'full-numerical', 'full-numerical-development')
                or self.config_id != 'config.'+NAMESPACE+'.'+self.source.root_id+'.'+self.operation
                or type(self.commitment_config) is not ObjectIdentity
                or (self.commitment_config.object_schema, self.commitment_config.object_version) !=
                    (ScheduledCommitmentConfig.SCHEMA, ScheduledCommitmentConfig.VERSION)):
            raise ValueError('scheduled native configuration changes exact source/phase')
        validate_record_fields(self.source)
        validate_record_fields(self.commitment_config)


@dataclass(frozen=True, slots=True)
class ScheduledArrays(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-history/arrays'
    operand_id: str
    source: ObjectIdentity
    role: str
    array_artifact: ArtifactIdentity
    members: tuple[MatrixArrayMember, ...]
    producers: tuple[ObjectIdentity, ...]
    outcome_access: OutcomeAccess
    visibility_ceiling: VisibilityCeiling

    def __post_init__(self):
        validate_stable_id(self.operand_id)
        require_sorted_unique_ids(self.members, attribute='name', field_name='members')
        require_sorted_unique_ids(self.producers, attribute='object_id', field_name='producers')
        if (self.source.object_schema != ScheduledSource.SCHEMA or self.role not in ('PREFIX', 'FULL_HISTORY', 'PREFIX_DIAGNOSTICS', 'CAUSAL_STATE')
                or not self.members or not self.producers or self.array_artifact.payload_schema != MATRIX_ARRAY_SCHEMA
                or self.array_artifact.media_type != 'application/x-npz' or not 0 < self.array_artifact.size_bytes <= MAXIMUM_MATRIX_ARRAY_BYTES
                or self.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE
                or self.outcome_access is not (OutcomeAccess.EVALUATION_SEALED if self.role == 'FULL_HISTORY' else OutcomeAccess.OUTCOME_BLIND)):
            raise ValueError('scheduled arrays change bounded original causal/protected scope')


@dataclass(frozen=True, slots=True)
class ScheduledCheckpoint(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-history/checkpoint'
    checkpoint_id: str
    source: ObjectIdentity
    coordinate: ObjectIdentity
    cutoff_tick: int
    prefix_arrays: ArtifactIdentity
    generators: tuple[ParameterGeneratorState, ...]

    def __post_init__(self):
        validate_stable_id(self.checkpoint_id)
        if (self.source.object_schema != ScheduledSource.SCHEMA or self.coordinate.object_schema != MatrixParameterCoordinate.SCHEMA
                or type(self.cutoff_tick) is not int or self.cutoff_tick < 1
                or self.prefix_arrays.payload_schema != MATRIX_ARRAY_SCHEMA
                or tuple(s.purpose for s in self.generators) != HISTORY_PURPOSES
                or any(type(s) is not ParameterGeneratorState for s in self.generators)):
            raise ValueError('scheduled checkpoint changes exact four-stream causal boundary')

    def validate_source(self, source, arrays):
        tick, c = source.policy.cutoff_tick, source.coordinate
        if (self.source != identity(source) or self.coordinate != coordinate_identity(c) or self.cutoff_tick != tick
                or (self.prefix_arrays.payload_schema, self.prefix_arrays.media_type, self.prefix_arrays.sha256, self.prefix_arrays.size_bytes) !=
                   (arrays.array_artifact.payload_schema, arrays.array_artifact.media_type, arrays.array_artifact.sha256, arrays.array_artifact.size_bytes)
                or any(s.effective_seed != r.effective_seed or s.completed_noise_matrices !=
                       (min(tick, c.ramp_ticks) if s.purpose.startswith('preparation') else max(0, tick-c.ramp_ticks))
                       for s, r in zip(self.generators, source.root.streams, strict=True))):
            raise ValueError('scheduled checkpoint substitutes original source/streams/draw cursors')


@dataclass(frozen=True, slots=True)
class ScheduledNativeEvidence(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-history/native-evidence'
    definition: NativeSubworkDefinition
    completion: NativeSubworkCompletion
    receipt: CanonicalTaskReceipt

    def __post_init__(self):
        from empirical_lawhood.runtime.native_subwork import require_native_completion_receipt
        require_native_completion_receipt(self.completion, self.receipt)
        if (self.completion.definition != self.definition.identity
                or self.completion.operational_status is not OperationalStatus.SUCCEEDED
                or self.receipt.operational_status is not OperationalStatus.SUCCEEDED
                or self.completion.omitted_output_ids or self.completion.unknown_streams
                or self.completion.output_ids != tuple(o.output_id for o in self.definition.outputs)
                or set((*self.completion.consumed_streams, *self.completion.unconsumed_streams)) != set(self.definition.streams)
                or self.receipt.implementation_commit != self.definition.parent_contact.implementation_commit
                or not set(self.definition.input_materialization_ids) <= set(self.receipt.input_materialization_ids)):
            raise ValueError('scheduled source requires actual known complete native receipt')


def _validate_prefix_native_evidence(history, source, *, configuration, parent_task, operation, native_sources,
        output_access=OutcomeAccess.OUTCOME_BLIND, output_visibility=VisibilityCeiling.PROSPECTIVE):
    """Original native checks, with expectations derived by typed source owners."""
    from empirical_lawhood.runtime.native_subwork import require_native_completion_receipt
    require_native_completion_receipt(history.native.completion, history.native.receipt,
        outcome_access=output_access, visibility_ceiling=output_visibility)
    d, tick = history.native.definition, source.policy.cutoff_tick
    streams = tuple(sorted((source.root.stream_identity(s) for s in source.root.streams), key=lambda x: x.object_id))
    consumed = tuple(sorted((source.root.stream_identity(s) for s in source.root.streams if
        s.purpose.startswith('preparation') or tick > source.coordinate.ramp_ticks), key=lambda x: x.object_id))
    task = 'native-subwork.'+sha256((d.parent_contact.task_id+':'+d.subwork_id).encode()).hexdigest()
    if (history.source != identity(source) or d.configuration != configuration
            or d.operation_id != operation or d.subwork_id != 'prefix.'+source.root_id
            or d.parent_contact.task_id != parent_task
            or d.parent_contact.implementation_commit != source.provenance.observed_git_head
            or d.streams != streams or history.native.completion.consumed_streams != consumed
            or d.code_sources_sha256 != source.provenance.code_sources_sha256
            or d.dependency_lock_sha256 != source.provenance.dependency_lock_sha256
            or set(d.sources) != native_sources
            or tuple(o.output_id for o in d.outputs) != ('arrays', 'checkpoint')
            or (history.native.receipt.run_id, history.native.receipt.task_id, history.native.receipt.attempt_id) !=
               (d.parent_contact.run_id, task, d.parent_contact.run_id+'.'+task+'.attempt-001')):
        raise ValueError('scheduled prefix substitutes original native phase/source/clock/stream closure')
    expected_outputs = (('arrays', MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ, 'application/x-npz'),
        ('checkpoint', ScheduledCheckpoint.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json'))
    if tuple((o.output_id, o.payload_schema, o.profile, o.media_type) for o in d.outputs) != expected_outputs:
        raise ValueError('scheduled prefix changes original nested output contract')
    for name, schema, profile, media in expected_outputs:
        logical_id = task+'.output.'+name
        logical = tuple(a for a in history.native.receipt.output_logical_artifacts if a.logical_artifact_id == logical_id)
        physical = tuple(p for p in history.native.receipt.output_materializations if p.logical_artifact_id == logical_id)
        digest, size = ((history.arrays.array_artifact.sha256, history.arrays.array_artifact.size_bytes) if name == 'arrays'
            else (history.checkpoint.fingerprint(), len(history.checkpoint.canonical_bytes())))
        if (len(logical) != 1 or len(physical) != 1
                or (logical[0].payload_schema, logical[0].profile, logical[0].media_type, logical[0].content_sha256) != (schema, profile, media, digest)
                or logical[0].outcome_access is not output_access
                or logical[0].visibility_ceiling is not output_visibility
                or (physical[0].physical_sha256, physical[0].size_bytes) != (digest, size)
                or name == 'arrays' and history.checkpoint.prefix_arrays.artifact_id != logical_id):
            raise ValueError('scheduled prefix changes original physical native arrays/checkpoint custody')


@dataclass(frozen=True, slots=True)
class ScheduledPrefixHistory(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-history/prefix-history'
    history_id: str
    source: ObjectIdentity
    arrays: ScheduledArrays
    checkpoint: ScheduledCheckpoint
    native: ScheduledNativeEvidence

    def __post_init__(self):
        validate_stable_id(self.history_id)
        if (type(self.arrays) is not ScheduledArrays or self.arrays.role != 'PREFIX' or self.source != self.arrays.source
                or type(self.checkpoint) is not ScheduledCheckpoint or self.checkpoint.source != self.source
                or type(self.native) is not ScheduledNativeEvidence):
            raise ValueError('scheduled prefix cannot accept sealed full history or exposed source')

    def validate_source(self, source, *, native_context=None):
        self.checkpoint.validate_source(source, self.arrays)
        from .source_index import ScheduledNativeSourceContext
        if type(native_context) is not ScheduledNativeSourceContext or native_context.source != source:
            raise ValueError('scheduled prefix requires its actual current native configuration and shared context')
        configuration, parent_task, operation, native_sources = native_context.contract('prefix')
        _validate_prefix_native_evidence(self, source, configuration=configuration, parent_task=parent_task,
            operation=operation, native_sources=set(native_sources))


@dataclass(frozen=True, slots=True)
class ScheduledNumericalAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-history/numerical-assessment'
    assessment_id: str
    source: ObjectIdentity
    history: ObjectIdentity
    numerical_design: ObjectIdentity
    controls: tuple[MatrixParameterHistoryControl, ...]
    numerical_pass: bool

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        if (self.source.object_schema != ScheduledSource.SCHEMA or self.history.object_schema != ScheduledPrefixHistory.SCHEMA
                or tuple(c.control_id for c in self.controls) != METHODS or type(self.numerical_pass) is not bool
                or self.numerical_pass != all(c.disposition == 'SATISFIED' for c in self.controls)):
            raise ValueError('scheduled prefix assessment loses exact independent numerical controls')


@dataclass(frozen=True, slots=True)
class ScheduledPrefixTrace(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-history/prefix-trace'
    rule: ObjectIdentity
    view: str
    sector: str
    observations: tuple[FactorObservation, ...]
    moving_lifetime: FactorLifetime
    origin_fixed_lifetime: FactorLifetime

    def __post_init__(self):
        if (self.rule.object_schema != E1FactorRule.SCHEMA or self.view not in ('PRIMARY', 'FINE') or self.sector not in ('X', 'Y') or not self.observations
                or tuple(o.tick for o in self.observations) != tuple(sorted({o.tick for o in self.observations}))):
            raise ValueError('scheduled prefix trace changes complete causal view/sector/lattice')


@dataclass(frozen=True, slots=True)
class ScheduledPrefixWitness(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-history/prefix-witness'
    product_id: str
    source: ObjectIdentity
    history: ObjectIdentity
    numerical: ObjectIdentity
    policy: ObjectIdentity
    traces: tuple[ScheduledPrefixTrace, ...]
    arrays: ScheduledArrays

    def __post_init__(self):
        validate_stable_id(self.product_id)
        if (self.source.object_schema != ScheduledSource.SCHEMA or self.history.object_schema != ScheduledPrefixHistory.SCHEMA
                or self.numerical.object_schema != ScheduledNumericalAssessment.SCHEMA
                or self.policy.object_schema != ScheduledPrefixPolicy.SCHEMA
                or type(self.arrays) is not ScheduledArrays or self.arrays.role != 'PREFIX_DIAGNOSTICS'
                or self.arrays.source != self.source or not self.traces):
            raise ValueError('scheduled prefix witness cannot accept full-history E1 diagnostics')


@dataclass(frozen=True, slots=True)
class ScheduledFrameAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-history/frame-assessment'
    assessment_id: str
    source: ObjectIdentity
    witness: ObjectIdentity
    numerical_design: ObjectIdentity
    controls: tuple[MatrixParameterFactorControl, ...]
    numerical_pass: bool

    def __post_init__(self):
        from empirical_lawhood.adapters.methods.matrix_parameter_factor.records import METHODS as FACTOR_METHODS
        validate_stable_id(self.assessment_id)
        if (self.source.object_schema != ScheduledSource.SCHEMA or self.witness.object_schema != ScheduledPrefixWitness.SCHEMA
                or tuple(c.method for c in self.controls) != FACTOR_METHODS or type(self.numerical_pass) is not bool
                or self.numerical_pass != all(c.disposition in ('SATISFIED', 'NOT_APPLICABLE') for c in self.controls)):
            raise ValueError('scheduled frame assessment loses complete independent eigenpair controls')


@dataclass(frozen=True, slots=True)
class ScheduledCausalPrefix(CanonicalRecord):
    """Predictor delivery: causal phase/frame only, never checkpoint/RNG state."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-history/causal-prefix'
    prefix_id: str
    source: ObjectIdentity
    history: ObjectIdentity
    numerical: ObjectIdentity
    witness: ObjectIdentity
    frame_assessment: ObjectIdentity
    policy: ObjectIdentity
    root: MatrixProgrammeRoot
    cutoff_tick: int
    frame_sha256: str | None
    disposition: str
    reason: str | None
    arrays: ScheduledArrays

    def __post_init__(self):
        from empirical_lawhood.kernel.serialization import validate_sha256
        validate_stable_id(self.prefix_id)
        if self.frame_sha256 is not None:
            validate_sha256(self.frame_sha256)
        if (self.source.object_schema != ScheduledSource.SCHEMA or self.history.object_schema != ScheduledPrefixHistory.SCHEMA
                or self.numerical.object_schema != ScheduledNumericalAssessment.SCHEMA
                or self.witness.object_schema != ScheduledPrefixWitness.SCHEMA
                or self.frame_assessment.object_schema != ScheduledFrameAssessment.SCHEMA
                or self.policy.object_schema != ScheduledPrefixPolicy.SCHEMA
                or type(self.root) is not MatrixProgrammeRoot or self.root.role not in ROLES
                or type(self.cutoff_tick) is not int or self.cutoff_tick < 1
                or self.disposition not in ('AVAILABLE', 'NO_ORIGIN', 'UNEVALUABLE')
                or (self.disposition == 'AVAILABLE') != (self.frame_sha256 is not None and self.reason is None)
                or self.disposition != 'AVAILABLE' and self.reason is None
                or type(self.arrays) is not ScheduledArrays or self.arrays.role != 'CAUSAL_STATE' or self.arrays.source != self.source):
            raise ValueError('causal delivery changes exact cutoff/role or manufactures available frame')


@dataclass(frozen=True, slots=True)
class ScheduledUnavailable(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-history/unavailable'
    source: ObjectIdentity
    receipt: CanonicalTaskReceipt | None
    contact: NativeEffectContact | None

    def __post_init__(self):
        if (self.source.object_schema != ScheduledSource.SCHEMA or self.receipt is None and self.contact is None
                or self.receipt is not None and self.receipt.operational_status not in
                   (OperationalStatus.FAILED, OperationalStatus.BLOCKED, OperationalStatus.SKIPPED, OperationalStatus.INVALIDATED)
                or self.contact is not None and type(self.contact) is not NativeEffectContact
                or self.receipt is not None and self.contact is not None and
                   (self.receipt.run_id, self.receipt.task_id, self.receipt.attempt_id, self.receipt.implementation_commit) !=
                   (self.contact.run_id, self.contact.task_id, self.contact.attempt_id, self.contact.implementation_commit)):
            raise ValueError('scheduled unavailable row requires original known refusal or unknown contact')


@dataclass(frozen=True, slots=True)
class ScheduledDisposition(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-history/disposition'
    source: ObjectIdentity
    root: MatrixProgrammeRoot
    prefix: ScheduledCausalPrefix | None
    unavailable: ScheduledUnavailable | None

    def __post_init__(self):
        if (self.source.object_schema != ScheduledSource.SCHEMA or type(self.root) is not MatrixProgrammeRoot
                or (self.prefix is None) == (self.unavailable is None)
                or self.prefix is not None and (self.prefix.source != self.source or self.prefix.root != self.root)
                or self.unavailable is not None and self.unavailable.source != self.source):
            raise ValueError('scheduled disposition omits exact complete source/root/evidence')

    @property
    def availability(self):
        return self.prefix.disposition if self.prefix is not None else 'UNKNOWN_CONTACT' if self.unavailable.receipt is None else 'UNAVAILABLE'
