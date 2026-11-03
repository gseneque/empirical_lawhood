# SPDX-License-Identifier: MPL-2.0
"""Additive E1 records, separate from every exposed historical factor record.

An eligible allocation and its published selections are prospective operands.
They do not issue a study, qualify a source, authorize contact or reveal data.
The ordinary prospective compiler and execution services own those boundaries.
"""

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
from math import prod
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_factor_lifetime.records import (
    FactorEventSpec, FactorLifetime, FactorObservation, ScalarClosureSpec,
)
from empirical_lawhood.adapters.methods.matrix_factor_response.eligibility import MatrixFactorExposureCensus
from empirical_lawhood.adapters.methods.matrix_history_analysis.records import HISTORY_PURPOSES, MatrixHistorySeed
from empirical_lawhood.adapters.methods.matrix_parameter_factor.records import (
    MatrixParameterFactorControl, MatrixParameterFactorNumericalDesign,
    MatrixParameterScalarDefinition,
    expected_members as factor_members,
)
from empirical_lawhood.adapters.methods.matrix_parameter_history.records import (
    METHODS, MatrixParameterHistoryControl, MatrixParameterNativeHistory,
    MatrixParameterNumericalDesign, coordinate_identity, expected_members,
)
from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole, MatrixProgrammeRoot
from empirical_lawhood.adapters.simulators.six_matrix_response.history_preparation import FOUR_FAMILY_PREPARATION_IDS
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history import MatrixParameterCoordinate
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA, MAXIMUM_MATRIX_ARRAY_BYTES, MatrixArrayMember
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord, require_sorted_unique_ids, require_sorted_unique_strings,
    validate_decimal, validate_stable_id,
)
from empirical_lawhood.kernel.status import OperationalStatus, ScientificStatus
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteResult, CanonicalTaskReceipt
from empirical_lawhood.runtime.native_effects import NativeEffectContact

VIEWS = ('PRIMARY', 'FINE')
ENDPOINTS = ('MOVING', 'ORIGIN_FIXED', 'BOTH')


def identity(record):
    for name in ('source_id', 'allocation_id', 'reservation_id', 'specification_id',
                 'selection_id', 'criterion_id', 'spec_id', 'operand_id', 'history_id',
                 'assessment_id', 'product_id', 'population_id', 'result_id', 'config_id', 'design_id', 'definition_id', 'commitment_id'):
        if hasattr(record, name):
            return ObjectIdentity.from_record(getattr(record, name), record)
    raise ValueError('E1 record has no named identity')


@dataclass(frozen=True, slots=True)
class E1FactorRule(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-confirmation/factor-rule'
    spec_id: str
    sectors: tuple[str, ...]
    lattice: tuple[int, ...]
    primary_dt: Decimal
    risk_start_tick: int
    trailing_persistence_ticks: int
    associative_leakage_maximum: Decimal
    lie_leakage_maximum: Decimal
    factor_fit_angle_maximum_degrees: Decimal
    adjacent_angle_maximum_degrees: Decimal
    origin_angle_maximum_degrees: Decimal
    identifiability_relative_gap: Decimal
    identifiability_absolute_fourth: Decimal
    frame_alignment_minimum_overlap: Decimal
    scalar_closure: ScalarClosureSpec

    def __post_init__(self):
        # Reuse mathematical domain validation only. No historical source,
        # population or trace is accepted or relabelled by this new schema.
        if (type(self.scalar_closure) is not ScalarClosureSpec
                or self.scalar_closure.normalization_owner.payload_schema != MatrixParameterScalarDefinition.SCHEMA
                or self.scalar_closure.normalization_owner.media_type != 'application/json'):
            raise ValueError('E1 requires the separately retained original scalar 0.30 comparison')
        FactorEventSpec(**{name: getattr(self, name) for name in self.__dataclass_fields__ if name != 'SCHEMA'})

    @property
    def identity(self):
        return identity(self)


@dataclass(frozen=True, slots=True)
class E1HistoryRoot(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-confirmation/history-root'
    root: MatrixProgrammeRoot
    coordinate: ObjectIdentity
    streams: tuple[MatrixHistorySeed, ...]

    def __post_init__(self):
        if (type(self.root) is not MatrixProgrammeRoot or self.root.role is not MatrixProgrammeRole.CONFIRMATION
                or self.coordinate.object_schema != MatrixParameterCoordinate.SCHEMA
                or self.coordinate.object_id != self.root.coordinate_id
                or tuple(s.purpose for s in self.streams) != HISTORY_PURPOSES
                or any(type(s) is not MatrixHistorySeed for s in self.streams)
                or len({s.effective_seed for s in self.streams}) != len(HISTORY_PURPOSES)):
            raise ValueError('E1 requires fresh confirmation roles and all four native history streams')

    def stream_identity(self, stream):
        if stream not in self.streams:
            raise ValueError('E1 stream is outside its exact root')
        return ObjectIdentity.from_record('stream.'+self.root.root_id+'.'+stream.purpose, stream)


@dataclass(frozen=True, slots=True)
class E1HistoryAllocation(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-confirmation/history-allocation'
    allocation_id: str
    coordinates: tuple[MatrixParameterCoordinate, ...]
    roots: tuple[E1HistoryRoot, ...]
    exposure: MatrixFactorExposureCensus

    def __post_init__(self):
        validate_stable_id(self.allocation_id)
        require_sorted_unique_ids(self.coordinates, attribute='coordinate_id', field_name='coordinates')
        ids = tuple(r.root.root_id for r in self.roots)
        if (type(self.exposure) is not MatrixFactorExposureCensus or not ids or ids != tuple(sorted(set(ids)))
                or any(type(r) is not E1HistoryRoot for r in self.roots)
                or {c.family_id for c in self.coordinates} != set(FOUR_FAMILY_PREPARATION_IDS)
                or len(self.coordinates) != len(FOUR_FAMILY_PREPARATION_IDS)):
            raise ValueError('E1 allocation must retain exactly one coordinate per scheduled family and every root')
        coordinates = {coordinate_identity(c): c for c in self.coordinates}
        used, streams, cells = set(), set(), set()
        common = None
        for row in self.roots:
            if row.coordinate not in coordinates:
                raise ValueError('E1 root substitutes its full-history coordinate')
            c = coordinates[row.coordinate]
            if (row.root.clock_id != c.clock_id or row.root.independent_group_id in self.exposure.exposed_independent_groups
                    or c.primary_view.rng_algorithm not in ('numpy.pcg64dxsm', 'numpy-pcg64dxsm')):
                raise ValueError('E1 root reuses exposed groups or changes declared physical clock/generator')
            # Four schedules differ in preparation, with the same selected
            # physical member, bath, target, duration and matched view clocks.
            physical = (c.member, c.primary_view, c.fine_view, c.target_x, c.target_y,
                        c.decreasing_start, c.ramp_ticks, c.autonomous_ticks, c.observation_ticks,
                        c.initial_state_rule_id, c.preparation_rule_id)
            if common is None:
                common = physical
            elif physical != common:
                raise ValueError('E1 four-family comparison changes physical parameters or observation clocks')
            cell = (c.family_id, row.root.independent_group_id)
            if cell in cells:
                raise ValueError('E1 family duplicates an independent unit')
            cells.add(cell)
            used.add(row.coordinate)
            for stream in row.streams:
                if stream.effective_seed in streams or stream.effective_seed in self.exposure.effective_seed_exclusions:
                    raise ValueError('E1 consumed native streams collide with selected or exposed history')
                streams.add(stream.effective_seed)
        if used != set(coordinates):
            raise ValueError('E1 allocation omits a full scheduled family')


def _publication(publication, record):
    if (type(publication) is not ArtifactWriteResult
            or publication.logical.payload_schema != record.SCHEMA
            or publication.logical.profile is not ArtifactProfile.CANONICAL_JSON
            or publication.logical.content_sha256 != record.fingerprint()
            or publication.materialization.physical_sha256 != record.fingerprint()
            or publication.materialization.size_bytes != len(record.canonical_bytes())
            or publication.logical.outcome_access is not OutcomeAccess.OUTCOME_BLIND
            or publication.logical.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE):
        raise ValueError('E1 requires actual exact outcome-blind prospective publication custody')


@dataclass(frozen=True, slots=True)
class E1AllocationReservation(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-confirmation/allocation-reservation'
    reservation_id: str
    allocation: E1HistoryAllocation
    publication: ArtifactWriteResult

    def __post_init__(self):
        validate_stable_id(self.reservation_id)
        if type(self.allocation) is not E1HistoryAllocation:
            raise ValueError('E1 reservation cannot accept exposed allocations')
        _publication(self.publication, self.allocation)


@dataclass(frozen=True, slots=True)
class E1FamilyRequirement(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-confirmation/family-requirement'
    family_id: str
    requested_roots: int
    minimum_admitted_roots: int
    required_recurrence_probability: Decimal
    required_survival_probability: Decimal

    def __post_init__(self):
        if (self.family_id not in FOUR_FAMILY_PREPARATION_IDS or type(self.requested_roots) is not int
                or self.requested_roots < 1 or type(self.minimum_admitted_roots) is not int
                or not 1 <= self.minimum_admitted_roots <= self.requested_roots):
            raise ValueError('E1 family root and survival risk counts must be explicit positive integers')
        for name in ('required_recurrence_probability', 'required_survival_probability'):
            validate_decimal(getattr(self, name), field_name=name)
            if not 0 < getattr(self, name) <= 1:
                raise ValueError('E1 family probabilities must be explicitly in (0,1]')


@dataclass(frozen=True, slots=True)
class E1ConfirmationCriterion(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-confirmation/criterion'
    criterion_id: str
    allocation: ObjectIdentity
    factor_rule: ObjectIdentity
    system_id: str
    world_id: str
    relation: ObjectIdentity
    independent_unit_id: str
    family_requirements: tuple[E1FamilyRequirement, ...]
    views: tuple[str, ...]
    survival_endpoints: tuple[str, ...]
    recurrence_estimand: str
    recurrence_end_tick: int
    survival_duration_ticks: int
    confidence_level: Decimal
    uncertainty: str
    multiplicity: str

    def __post_init__(self):
        for name in ('criterion_id', 'system_id', 'world_id', 'independent_unit_id'):
            validate_stable_id(getattr(self, name))
        require_sorted_unique_ids(self.family_requirements, attribute='family_id', field_name='family_requirements')
        if (self.allocation.object_schema != E1HistoryAllocation.SCHEMA or self.factor_rule.object_schema != E1FactorRule.SCHEMA
                or {f.family_id for f in self.family_requirements} != set(FOUR_FAMILY_PREPARATION_IDS)
                or not self.views or self.views != tuple(v for v in VIEWS if v in self.views)
                or not self.survival_endpoints or self.survival_endpoints != tuple(v for v in ENDPOINTS if v in self.survival_endpoints)
                or self.recurrence_estimand not in ('EVER_CAUSALLY_ADMITTED_IN_RISK_WINDOW', 'OBSERVED_NEW_ADMISSION_AFTER_RISK_START')
                or type(self.recurrence_end_tick) is not int or self.recurrence_end_tick < 1
                or type(self.survival_duration_ticks) is not int or self.survival_duration_ticks < 1
                or self.uncertainty != 'EXACT_ONE_SIDED_BINOMIAL_LOWER_BOUND'
                or self.multiplicity not in ('BONFERRONI_FROZEN_FAMILY_VIEW_SECTOR_ENDPOINT_MENU', 'MARGINAL_CELL_NO_FULL_STUDY_CLAIM')):
            raise ValueError('E1 criterion omits explicit complete family/estimand/endpoint/uncertainty selections')
        validate_decimal(self.confidence_level, field_name='confidence_level')
        if not 0 < self.confidence_level < 1:
            raise ValueError('E1 confidence must be explicitly between zero and one')

    def validate_allocation(self, allocation, rule):
        counts = {f.family_id: sum(c.family_id == f.family_id for r in allocation.roots
                  for c in allocation.coordinates if r.coordinate == coordinate_identity(c)) for f in self.family_requirements}
        stride = rule.lattice[1]-rule.lattice[0]
        if (self.allocation != identity(allocation) or self.factor_rule != identity(rule)
                or any(counts[f.family_id] != f.requested_roots for f in self.family_requirements)
                or self.recurrence_end_tick not in rule.lattice or self.recurrence_end_tick < rule.risk_start_tick
                or self.survival_duration_ticks % stride or self.survival_duration_ticks > rule.lattice[-1]-rule.risk_start_tick
                or any(c.primary_view.timestep != rule.primary_dt or c.observation_ticks != rule.lattice
                       or rule.risk_start_tick < c.ramp_ticks for c in allocation.coordinates)):
            raise ValueError('E1 frozen criterion changes requested roots, scheduled clocks, causal risk or duration')


@dataclass(frozen=True, slots=True)
class E1ScientificSelection(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-confirmation/scientific-selection'
    selection_id: str
    reservation: ObjectIdentity
    factor_rule: E1FactorRule
    criterion: E1ConfirmationCriterion
    numerical_design: MatrixParameterNumericalDesign
    factor_numerical_design: MatrixParameterFactorNumericalDesign

    def __post_init__(self):
        validate_stable_id(self.selection_id)
        if (self.reservation.object_schema != E1AllocationReservation.SCHEMA or type(self.factor_rule) is not E1FactorRule
                or type(self.criterion) is not E1ConfirmationCriterion
                or type(self.numerical_design) is not MatrixParameterNumericalDesign
                or type(self.factor_numerical_design) is not MatrixParameterFactorNumericalDesign
                or self.criterion.factor_rule != identity(self.factor_rule)):
            raise ValueError('E1 selection substitutes its frozen mathematical protocols')


@dataclass(frozen=True, slots=True)
class E1FrozenSpecification(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-confirmation/frozen-specification'
    specification_id: str
    selection: E1ScientificSelection
    publication: ArtifactWriteResult

    def __post_init__(self):
        validate_stable_id(self.specification_id)
        if type(self.selection) is not E1ScientificSelection:
            raise ValueError('E1 freeze cannot accept exposed scientific selections')
        _publication(self.publication, self.selection)


@dataclass(frozen=True, slots=True)
class E1HistorySource(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-confirmation/history-source'
    source_id: str
    reservation: E1AllocationReservation
    specification: E1FrozenSpecification
    root_id: str
    provenance: NumericalProducingProvenance

    def __post_init__(self):
        validate_stable_id(self.source_id)
        validate_stable_id(self.root_id)
        if (type(self.reservation) is not E1AllocationReservation or type(self.specification) is not E1FrozenSpecification
                or type(self.provenance) is not NumericalProducingProvenance
                or self.specification.selection.reservation != identity(self.reservation)
                or self.root_id not in {r.root.root_id for r in self.allocation.roots}):
            raise ValueError('E1 source requires complete fresh allocation, prior selections and producing provenance')
        self.criterion.validate_allocation(self.allocation, self.rule)
        size = sum(prod(shape)*({'<c16': 16, '<f8': 8, '<i8': 8}[dtype])
                   for dtype, shape in expected_members(self.coordinate).values())
        if size+11*10000 > MAXIMUM_MATRIX_ARRAY_BYTES:
            raise ValueError('E1 complete history exceeds bounded transport before contact')

    @property
    def allocation(self):
        return self.reservation.allocation

    @property
    def root(self):
        return next(r for r in self.allocation.roots if r.root.root_id == self.root_id)

    @property
    def coordinate(self):
        return next(c for c in self.allocation.coordinates if coordinate_identity(c) == self.root.coordinate)

    @property
    def rule(self):
        return self.specification.selection.factor_rule

    @property
    def criterion(self):
        return self.specification.selection.criterion

    @property
    def numerical_design(self):
        return self.specification.selection.numerical_design


@dataclass(frozen=True, slots=True)
class E1Arrays(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-confirmation/arrays'
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
        if (self.source.object_schema != E1HistorySource.SCHEMA or self.role not in ('NATIVE_HISTORY', 'FACTOR_DIAGNOSTICS')
                or self.outcome_access is not OutcomeAccess.EVALUATION_SEALED
                or self.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE
                or not self.members or not self.producers or self.array_artifact.payload_schema != MATRIX_ARRAY_SCHEMA
                or self.array_artifact.media_type != 'application/x-npz'
                or not 0 < self.array_artifact.size_bytes <= MAXIMUM_MATRIX_ARRAY_BYTES
                or sum(m.size_bytes for m in self.members) > MAXIMUM_MATRIX_ARRAY_BYTES):
            raise ValueError('E1 arrays require their distinct exact protected source/role/member contract')

    def validate_source(self, source):
        expected = expected_members(source.coordinate) if self.role == 'NATIVE_HISTORY' else factor_members(source.rule)
        if self.source != identity(source) or {m.name: (m.dtype, m.shape) for m in self.members} != expected:
            raise ValueError('E1 arrays substitute source, all physical clocks or complete factor witnesses')
        if self.role == 'NATIVE_HISTORY' and (not all(m.finite_required for m in self.members)
                or self.producers != tuple(sorted((identity(source), coordinate_identity(source.coordinate)), key=lambda x: x.object_id))):
            raise ValueError('E1 native arrays lose complete finite source/coordinate provenance')


@dataclass(frozen=True, slots=True)
class E1NativeHistory(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-confirmation/native-history'
    history_id: str
    source: ObjectIdentity
    coordinate: ObjectIdentity
    root_id: str
    independent_group_id: str
    clock_id: str
    arrays: E1Arrays
    native: MatrixParameterNativeHistory
    completed_primary_steps: int
    completed_fine_steps: int

    def __post_init__(self):
        for name in ('history_id', 'root_id', 'independent_group_id', 'clock_id'):
            validate_stable_id(getattr(self, name))
        if (type(self.arrays) is not E1Arrays or self.arrays.role != 'NATIVE_HISTORY'
                or self.source != self.arrays.source or self.source.object_schema != E1HistorySource.SCHEMA
                or type(self.native) is not MatrixParameterNativeHistory
                or type(self.completed_primary_steps) is not int or self.completed_primary_steps < 1
                or self.completed_fine_steps != 2*self.completed_primary_steps):
            raise ValueError('E1 history substitutes protected source or paired full native history')

    def validate_source(self, source):
        from .operation_bindings import E1OperationConfig, NAMESPACE
        self.arrays.validate_source(source)
        root, definition = source.root.root, self.native.definition
        streams = tuple(sorted((source.root.stream_identity(s) for s in source.root.streams), key=lambda x: x.object_id))
        native_task = 'native-subwork.'+sha256((definition.parent_contact.task_id+':'+definition.subwork_id).encode()).hexdigest()
        native_attempt = definition.parent_contact.run_id+'.'+native_task+'.attempt-001'
        consumed = tuple(sorted((source.root.stream_identity(s) for s in source.root.streams
            if s.purpose.startswith('preparation') or source.coordinate.autonomous_ticks), key=lambda x: x.object_id))
        if (self.source != identity(source) or self.coordinate != coordinate_identity(source.coordinate)
                or (self.root_id, self.independent_group_id, self.clock_id) != (root.root_id, root.independent_group_id, root.clock_id)
                or self.completed_primary_steps != source.coordinate.total_ticks or definition.streams != streams
                or definition.operation_id != 'matrix-e1.full-paired-history'
                or definition.subwork_id != 'paired-history.'+source.root_id
                or definition.configuration != identity(E1OperationConfig('config.'+NAMESPACE+'.'+source.root_id+'.history', 'history', source))
                or definition.parent_contact.task_id != NAMESPACE+'.'+source.root_id+'.history'
                or definition.parent_contact.implementation_commit != source.provenance.observed_git_head
                or (self.native.receipt.run_id, self.native.receipt.task_id, self.native.receipt.attempt_id) !=
                   (definition.parent_contact.run_id, native_task, native_attempt)
                or self.native.completion.consumed_streams != consumed
                or definition.code_sources_sha256 != source.provenance.code_sources_sha256
                or definition.dependency_lock_sha256 != source.provenance.dependency_lock_sha256
                or set(definition.sources) != {identity(source), identity(source.allocation), coordinate_identity(source.coordinate), source.provenance.identity}):
            raise ValueError('E1 history changes native source/stream/provenance/full clock lineage')
        artifacts = tuple(a for a in self.native.receipt.output_logical_artifacts if a.payload_schema == MATRIX_ARRAY_SCHEMA)
        if (len(artifacts) != 1 or artifacts[0].profile is not ArtifactProfile.MATRIX_ARRAY_NPZ
                or artifacts[0].logical_artifact_id != native_task+'.output.arrays'
                or artifacts[0].content_sha256 != self.arrays.array_artifact.sha256
                or artifacts[0].outcome_access is not OutcomeAccess.EVALUATION_SEALED
                or artifacts[0].visibility_ceiling is not VisibilityCeiling.PROSPECTIVE):
            raise ValueError('E1 history lacks original protected native array receipt')
        physical = tuple(p for p in self.native.receipt.output_materializations if p.logical_artifact_id == artifacts[0].logical_artifact_id)
        if (len(physical) != 1 or physical[0].physical_sha256 != self.arrays.array_artifact.sha256
                or physical[0].size_bytes != self.arrays.array_artifact.size_bytes):
            raise ValueError('E1 history changes original physical array custody')


@dataclass(frozen=True, slots=True)
class E1NumericalAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-confirmation/numerical-assessment'
    assessment_id: str
    source: ObjectIdentity
    history: ObjectIdentity
    numerical_design: ObjectIdentity
    controls: tuple[MatrixParameterHistoryControl, ...]
    numerical_pass: bool

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        if (self.source.object_schema != E1HistorySource.SCHEMA or self.history.object_schema != E1NativeHistory.SCHEMA
                or tuple(c.control_id for c in self.controls) != METHODS or type(self.numerical_pass) is not bool
                or self.numerical_pass != all(c.disposition == 'SATISFIED' for c in self.controls)):
            raise ValueError('E1 independent numerical assessment loses complete exact controls')


@dataclass(frozen=True, slots=True)
class E1FactorRootRole(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-confirmation/factor-root-role'
    root_id: str
    independent_unit_id: str
    family_id: str
    source: ObjectIdentity
    native_arrays: ArtifactIdentity
    native_result: ObjectIdentity

    def __post_init__(self):
        for name in ('root_id', 'independent_unit_id'):
            validate_stable_id(getattr(self, name))
        if (self.family_id not in FOUR_FAMILY_PREPARATION_IDS or self.source.object_schema != E1HistorySource.SCHEMA
                or self.native_result.object_schema != E1NativeHistory.SCHEMA):
            raise ValueError('E1 factor root cannot accept historical exposed source/history roles')


@dataclass(frozen=True, slots=True)
class E1FactorTrace(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-confirmation/factor-trace'
    root: E1FactorRootRole
    rule: ObjectIdentity
    view: str
    sector: str
    observations: tuple[FactorObservation, ...]
    moving_lifetime: FactorLifetime
    origin_fixed_lifetime: FactorLifetime
    diagnostics: ArtifactIdentity
    diagnostic_members: tuple[MatrixArrayMember, ...]

    def __post_init__(self):
        if (type(self.root) is not E1FactorRootRole or self.rule.object_schema != E1FactorRule.SCHEMA
                or self.view not in VIEWS or self.sector not in ('X', 'Y')
                or not self.observations or tuple(o.tick for o in self.observations) != tuple(sorted({o.tick for o in self.observations}))
                or not self.diagnostic_members):
            raise ValueError('E1 trace substitutes distinct root/rule/full ordered observations')


@dataclass(frozen=True, slots=True)
class E1FactorProduct(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-confirmation/factor-product'
    product_id: str
    source: ObjectIdentity
    history: ObjectIdentity
    numerical_assessment: ObjectIdentity
    history_numerical_pass: bool
    traces: tuple[E1FactorTrace, ...]
    arrays: E1Arrays

    def __post_init__(self):
        validate_stable_id(self.product_id)
        if (self.source.object_schema != E1HistorySource.SCHEMA or self.history.object_schema != E1NativeHistory.SCHEMA
                or self.numerical_assessment.object_schema != E1NumericalAssessment.SCHEMA
                or type(self.history_numerical_pass) is not bool or type(self.arrays) is not E1Arrays
                or self.arrays.role != 'FACTOR_DIAGNOSTICS' or self.arrays.source != self.source
                or not self.traces or any(type(t) is not E1FactorTrace for t in self.traces)):
            raise ValueError('E1 factor product cannot promote exposed factor products')


@dataclass(frozen=True, slots=True)
class E1FactorAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-confirmation/factor-assessment'
    assessment_id: str
    source: ObjectIdentity
    product: ObjectIdentity
    numerical_design: ObjectIdentity
    controls: tuple[MatrixParameterFactorControl, ...]
    numerical_pass: bool

    def __post_init__(self):
        from empirical_lawhood.adapters.methods.matrix_parameter_factor.records import METHODS as FACTOR_METHODS
        validate_stable_id(self.assessment_id)
        if (self.source.object_schema != E1HistorySource.SCHEMA or self.product.object_schema != E1FactorProduct.SCHEMA
                or tuple(c.method for c in self.controls) != FACTOR_METHODS or type(self.numerical_pass) is not bool
                or self.numerical_pass != all(c.disposition in ('SATISFIED', 'NOT_APPLICABLE') for c in self.controls)):
            raise ValueError('E1 factor assessment loses full independently checked witness controls')


@dataclass(frozen=True, slots=True)
class E1UnavailableRoot(CanonicalRecord):
    """Retained non-success receipt; never an invented factor assessment.

    The custody caller authenticates original receipts and contacts and supplies
    the complete operational census. A contact with no completion receipt is
    explicit UNKNOWN_CONTACT with no replay; an entirely absent contact needs
    the platform's absence census and cannot be asserted by this value record.
    """
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-confirmation/unavailable-root'
    source: ObjectIdentity
    receipt: CanonicalTaskReceipt | None = None
    contact: NativeEffectContact | None = None

    def __post_init__(self):
        if (self.source.object_schema != E1HistorySource.SCHEMA or self.receipt is None and self.contact is None
                or self.receipt is not None and (type(self.receipt) is not CanonicalTaskReceipt
                    or self.receipt.operational_status not in (OperationalStatus.FAILED, OperationalStatus.BLOCKED,
                        OperationalStatus.SKIPPED, OperationalStatus.INVALIDATED))
                or self.contact is not None and type(self.contact) is not NativeEffectContact):
            raise ValueError('E1 unavailable root requires actual original non-success receipt or uncertain contact')
        if self.receipt is not None and self.contact is not None and (
                self.receipt.run_id, self.receipt.task_id, self.receipt.attempt_id, self.receipt.implementation_commit) != (
                self.contact.run_id, self.contact.task_id, self.contact.attempt_id, self.contact.implementation_commit):
            raise ValueError('E1 unavailable root substitutes its actual contacted attempt')

    @property
    def availability(self):
        return 'UNKNOWN_CONTACT' if self.receipt is None else 'UNAVAILABLE'


@dataclass(frozen=True, slots=True)
class E1RiskRow(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-confirmation/risk-row'
    family_id: str
    view: str
    sector: str
    tick: int
    requested_roots: int
    available_observations: int
    unidentifiable_observations: int
    unavailable_observations: int
    raw_admitted_observations: int
    causal_admitted_observations: int
    first_causal_admissions: int
    admitted_through_tick: int
    left_present_roots: int
    left_present_surviving: int
    left_present_exited: int
    left_present_unknown: int


@dataclass(frozen=True, slots=True)
class E1FamilyFinding(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-confirmation/family-finding'
    family_id: str
    view: str
    sector: str
    endpoint: str
    requested_roots: int
    independent_units: int
    admitted_roots: int
    left_present_roots: int
    observed_new_admissions: int
    never_admitted_roots: int
    unknown_admission_roots: int
    risk_roots: int
    successes: int
    failures: int
    censored_before_horizon: int
    unresolved_roots: int
    probability_lower: Decimal
    required_probability: Decimal
    evaluable: bool

    def __post_init__(self):
        if (self.family_id not in FOUR_FAMILY_PREPARATION_IDS or self.view not in VIEWS
                or self.sector not in ('X', 'Y') or self.endpoint not in ('RECURRENCE', *ENDPOINTS)
                or type(self.evaluable) is not bool):
            raise ValueError('E1 finding substitutes frozen family/view/sector/endpoint')
        for name in ('requested_roots', 'independent_units', 'admitted_roots', 'left_present_roots',
                     'observed_new_admissions', 'never_admitted_roots', 'unknown_admission_roots',
                     'risk_roots', 'successes', 'failures', 'censored_before_horizon', 'unresolved_roots'):
            if type(getattr(self, name)) is not int or not 0 <= getattr(self, name) <= self.requested_roots:
                raise ValueError('E1 finding loses complete integer denominators')
        if (self.requested_roots < 1 or self.independent_units != self.requested_roots
                or self.admitted_roots+self.never_admitted_roots+self.unknown_admission_roots != self.requested_roots
                or self.successes+self.failures+self.censored_before_horizon+self.unresolved_roots != self.risk_roots):
            raise ValueError('E1 finding thins full requested or actual risk denominator')
        for name in ('probability_lower', 'required_probability'):
            validate_decimal(getattr(self, name), field_name=name)
            if not 0 <= getattr(self, name) <= 1:
                raise ValueError('E1 finding probability is outside [0,1]')


@dataclass(frozen=True, slots=True)
class E1FactorPopulation(CanonicalRecord):
    """Complete prospective source census, including roots without products."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-confirmation/factor-population'
    population_id: str
    allocation: ObjectIdentity
    factor_rule: ObjectIdentity
    root_ids: tuple[str, ...]
    sources: tuple[ObjectIdentity, ...]

    def __post_init__(self):
        validate_stable_id(self.population_id)
        require_sorted_unique_strings(self.root_ids, field_name='root_ids', allow_empty=False)
        if (self.allocation.object_schema != E1HistoryAllocation.SCHEMA or self.factor_rule.object_schema != E1FactorRule.SCHEMA
                or len(self.sources) != len(self.root_ids) or len(set(self.sources)) != len(self.sources)
                or any(s.object_schema != E1HistorySource.SCHEMA for s in self.sources)):
            raise ValueError('E1 population cannot omit or promote protected/exposed source roles')

    def validate_sources(self, sources):
        if (tuple(s.root_id for s in sources) != self.root_ids
                or tuple(identity(s) for s in sources) != self.sources
                or self.root_ids != tuple(r.root.root_id for r in sources[0].allocation.roots)
                or any(identity(s.allocation) != self.allocation or identity(s.rule) != self.factor_rule for s in sources)):
            raise ValueError('E1 population substitutes frozen complete allocation/root/rule/source census')


@dataclass(frozen=True, slots=True)
class E1PopulationResult(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-confirmation/population-result'
    result_id: str
    population: E1FactorPopulation
    criterion: ObjectIdentity
    root_ids: tuple[str, ...]
    products: tuple[ObjectIdentity, ...]
    assessments: tuple[ObjectIdentity, ...]
    unavailable: tuple[E1UnavailableRoot, ...]
    findings: tuple[E1FamilyFinding, ...]
    risk_rows: tuple[E1RiskRow, ...]
    scientific_status: ScientificStatus
    reason_codes: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.result_id)
        require_sorted_unique_strings(self.root_ids, field_name='root_ids', allow_empty=False)
        require_sorted_unique_strings(self.reason_codes, field_name='reason_codes', allow_empty=False)
        if (type(self.population) is not E1FactorPopulation or self.root_ids != self.population.root_ids
                or self.criterion.object_schema != E1ConfirmationCriterion.SCHEMA
                or len(self.products)+len(self.unavailable) != len(self.root_ids)
                or len(self.assessments) != len(self.products)
                or type(self.scientific_status) is not ScientificStatus
                or self.scientific_status is ScientificStatus.SUPPORTED and (
                    self.unavailable or not self.findings or not all(f.evaluable and f.probability_lower >= f.required_probability for f in self.findings))):
            raise ValueError('E1 population result drops the exact complete requested root denominator')

    @property
    def allocation(self):
        return self.population.allocation
