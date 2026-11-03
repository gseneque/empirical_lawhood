# SPDX-License-Identifier: MPL-2.0
"""Distinct compact E1 contracts; old E1 schemas, bytes and meanings stay closed.

The shared manifest retains the actual allocation/exposure and producing source
once. Per-root records pin that manifest and carry only one root's operands.
These records create no qualification, issue, execution or reveal permission.
"""
from dataclasses import dataclass, fields
from fractions import Fraction
from hashlib import sha256
from math import prod
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_factor_lifetime.records import FactorLifetime, FactorObservation
from empirical_lawhood.adapters.methods.matrix_parameter_factor.records import MatrixParameterFactorControl, MatrixParameterFactorNumericalDesign, MatrixParameterScalarDefinition, expected_members as factor_members
from empirical_lawhood.adapters.methods.matrix_parameter_history.records import METHODS, MatrixParameterHistoryControl, MatrixParameterNativeHistory, MatrixParameterNumericalDesign, coordinate_identity, expected_members
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history import MatrixParameterCoordinate
from empirical_lawhood.adapters.simulators.six_matrix_response.history_preparation import FOUR_FAMILY_PREPARATION_IDS
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA, MAXIMUM_MATRIX_ARRAY_BYTES, MatrixArrayMember
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, canonical_json_bytes, require_sorted_unique_ids, require_sorted_unique_strings, validate_sha256, validate_stable_id
from empirical_lawhood.kernel.status import OperationalStatus, ScientificStatus
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteResult, CanonicalTaskReceipt
from empirical_lawhood.runtime.native_effects import NativeEffectContact
from empirical_lawhood.runtime.native_subwork import require_native_completion_receipt
from empirical_lawhood.runtime.execution import TaskBlockKind, TaskBlockReason
from empirical_lawhood.runtime.plans import ExecutionPlan
from empirical_lawhood.runtime.recovery import (
    RecoveryTerminalAttempt, RecoveryTerminalDisposition, RunRecoveryIndex,
    RunRecoveryTerminalEvent, TaskRecoveryDisposition, TaskRecoveryEvent,
)
from .records import E1AllocationReservation, E1FactorRule, E1HistoryAllocation, E1HistoryRoot, E1RiskRow, VIEWS, ENDPOINTS, _publication
from .occurrence import E1OccurrenceCell, E1RootOccurrence, occurrence_cells

NAMESPACE='matrix-factor-confirmation-compact'
PHASES=('history','numerical','measure','check')


def identity(record):
    for name in ('source_id','record_id','allocation_id','reservation_id','specification_id','selection_id','criterion_id','spec_id','operand_id','history_id','assessment_id','product_id','population_id','result_id','config_id','design_id','definition_id'):
        if hasattr(record,name):return ObjectIdentity.from_record(getattr(record,name),record)
    raise ValueError('compact E1 record has no actual named identity')


class _Identity:
    __slots__=()
    @property
    def identity(self):return identity(self)


def exact_pin(value,kind):
    if type(value) is not ObjectIdentity or (value.object_schema,value.object_version)!=(kind.SCHEMA,kind.VERSION):
        raise ValueError('compact E1 substitutes an original typed record edition')
    value.__post_init__()


def validate_e1_criterion_choices(value):
    """Validate the same mathematical choices before or after allocation."""
    for name in ('criterion_id', 'system_id', 'world_id', 'independent_unit_id'):
        validate_stable_id(getattr(value, name))
    exact_pin(value.factor_rule, E1FactorRule)
    if type(value.relation) is not ObjectIdentity:
        raise TypeError('E1 criterion requires its exact scientific relation')
    value.relation.__post_init__()
    if (type(value.family_requirements) is not tuple
            or any(type(row) is not E1FamilySize for row in value.family_requirements)):
        raise TypeError('E1 occurrence map requires exact family sizes without probability gates')
    for row in value.family_requirements:
        row.__post_init__()
    require_sorted_unique_ids(value.family_requirements, attribute='family_id', field_name='family_requirements')
    if (value.factor_rule.object_schema != E1FactorRule.SCHEMA
            or {f.family_id for f in value.family_requirements} != set(FOUR_FAMILY_PREPARATION_IDS)
            or value.views != VIEWS or value.survival_endpoints != ENDPOINTS
            or value.occurrence_estimand != 'INITIAL_PRESENCE_OR_FIRST_CAUSAL_ADMISSION'
            or type(value.occurrence_end_tick) is not int or value.occurrence_end_tick < 1
            or type(value.survival_duration_ticks) is not int or value.survival_duration_ticks < 1
            or value.uncertainty != 'TWO_SIDED_EXACT_BINOMIAL_FEASIBLE_COMPLETION_ENVELOPE'
            or value.multiplicity != 'EIGHT_PRIMARY_Y_CELLS_DIAGNOSTIC_MARGINAL_95_PERCENT'):
        raise ValueError('E1 criterion omits explicit complete family/estimand/endpoint/uncertainty selections')
    if (type(value.alpha_numerator) is not int or type(value.alpha_denominator) is not int
            or (value.alpha_numerator, value.alpha_denominator) != (1, 160)
            or type(value.survival_origin_end_tick) is not int
            or value.survival_origin_end_tick != value.occurrence_end_tick):
        raise ValueError('compact E1 requires exact rational primary alpha and explicit survival-origin scope')


@dataclass(frozen=True, slots=True)
class E1FamilySize(CanonicalRecord):
    """Assigned population size; no minimum-risk or probability-above-half gate."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-confirmation/occurrence-family-size'
    family_id: str
    requested_roots: int

    def __post_init__(self):
        if (self.family_id not in FOUR_FAMILY_PREPARATION_IDS
                or type(self.requested_roots) is not int or self.requested_roots < 1):
            raise ValueError('E1 family size requires a complete positive assigned denominator')


@dataclass(frozen=True, slots=True)
class E1CompactCriterionChoices(_Identity, CanonicalRecord):
    """Prospective mathematics, without a placeholder allocation or authority."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-confirmation/compact-criterion-choices'
    VERSION: ClassVar[str] = '2.0.0'
    criterion_id: str
    factor_rule: ObjectIdentity
    system_id: str
    world_id: str
    relation: ObjectIdentity
    independent_unit_id: str
    family_requirements: tuple[E1FamilySize, ...]
    views: tuple[str, ...]
    survival_endpoints: tuple[str, ...]
    occurrence_estimand: str
    occurrence_end_tick: int
    survival_duration_ticks: int
    alpha_numerator: int
    alpha_denominator: int
    survival_origin_end_tick: int
    uncertainty: str
    multiplicity: str

    def __post_init__(self):
        validate_e1_criterion_choices(self)

    def bind_allocation(self, allocation, rule):
        if type(allocation) is not E1HistoryAllocation or type(rule) is not E1FactorRule:
            raise TypeError('E1 criterion binds only the actual current allocation and factor rule')
        allocation.__post_init__()
        rule.__post_init__()
        criterion = E1CompactCriterion(allocation=identity(allocation),
            **{field.name: getattr(self, field.name) for field in fields(self)})
        criterion.validate_allocation(allocation, rule)
        return criterion


@dataclass(frozen=True, slots=True)
class E1CompactCriterion(_Identity,CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-confirmation/compact-criterion'
    VERSION: ClassVar[str] = '2.0.0'
    criterion_id: str
    allocation: ObjectIdentity
    factor_rule: ObjectIdentity
    system_id: str
    world_id: str
    relation: ObjectIdentity
    independent_unit_id: str
    family_requirements: tuple[E1FamilySize, ...]
    views: tuple[str, ...]
    survival_endpoints: tuple[str, ...]
    occurrence_estimand: str
    occurrence_end_tick: int
    survival_duration_ticks: int
    alpha_numerator: int
    alpha_denominator: int
    survival_origin_end_tick: int
    uncertainty: str
    multiplicity: str

    def __post_init__(self):
        exact_pin(self.allocation, E1HistoryAllocation)
        validate_e1_criterion_choices(self)

    def validate_allocation(self, allocation, rule):
        counts = {f.family_id: sum(c.family_id == f.family_id for r in allocation.roots
                  for c in allocation.coordinates if r.coordinate == coordinate_identity(c)) for f in self.family_requirements}
        stride = rule.lattice[1]-rule.lattice[0]
        if (self.allocation != identity(allocation) or self.factor_rule != identity(rule)
                or any(counts[f.family_id] != f.requested_roots for f in self.family_requirements)
                or rule.risk_start_tick != 0 or rule.sectors != ('X', 'Y')
                or self.occurrence_end_tick not in rule.lattice
                or self.occurrence_end_tick + self.survival_duration_ticks > rule.lattice[-1]
                or self.survival_duration_ticks % stride
                or any(c.primary_view.timestep != rule.primary_dt or c.observation_ticks != rule.lattice
                       for c in allocation.coordinates)):
            raise ValueError('E1 frozen criterion changes requested roots, scheduled clocks, causal risk or duration')

    @property
    def primary_alpha(self):return Fraction(self.alpha_numerator,self.alpha_denominator)

    def cell_alpha(self,rule):
        if self.factor_rule != identity(rule) or rule.sectors != ('X', 'Y') or rule.risk_start_tick != 0:
            raise ValueError('E1 primary interval allocation changes its selected rule')
        return self.primary_alpha / 8


@dataclass(frozen=True,slots=True)
class E1CompactScientificSelection(_Identity,CanonicalRecord):
    SCHEMA:ClassVar[str]='empirical-lawhood/matrix-factor-confirmation/compact-scientific-selection'
    selection_id:str
    reservation:ObjectIdentity
    factor_rule:E1FactorRule
    criterion:E1CompactCriterion
    numerical_design:MatrixParameterNumericalDesign
    factor_numerical_design:MatrixParameterFactorNumericalDesign

    def __post_init__(self):
        validate_stable_id(self.selection_id);exact_pin(self.reservation,E1AllocationReservation)
        for value,kind in ((self.factor_rule,E1FactorRule),(self.criterion,E1CompactCriterion),(self.numerical_design,MatrixParameterNumericalDesign),(self.factor_numerical_design,MatrixParameterFactorNumericalDesign)):
            if type(value) is not kind:raise TypeError('compact E1 selection requires original exact mathematical owners')
            value.__post_init__()
        if self.criterion.factor_rule!=identity(self.factor_rule):raise ValueError('compact E1 criterion changes its exact selected factor rule')


@dataclass(frozen=True,slots=True)
class E1CompactFrozenSpecification(_Identity,CanonicalRecord):
    SCHEMA:ClassVar[str]='empirical-lawhood/matrix-factor-confirmation/compact-frozen-specification'
    specification_id:str
    selection:E1CompactScientificSelection
    publication:ArtifactWriteResult

    def __post_init__(self):
        validate_stable_id(self.specification_id)
        if type(self.selection) is not E1CompactScientificSelection:raise TypeError('compact E1 freeze requires its distinct exact selection')
        self.selection.__post_init__();_publication(self.publication,self.selection)


@dataclass(frozen=True,slots=True)
class E1CompactManifest(_Identity,CanonicalRecord):
    SCHEMA:ClassVar[str]='empirical-lawhood/matrix-factor-confirmation/compact-manifest'
    record_id:str
    reservation:E1AllocationReservation
    specification:E1CompactFrozenSpecification
    provenance:NumericalProducingProvenance
    scalar_definition:MatrixParameterScalarDefinition
    scalar_publication:ArtifactWriteResult

    def __post_init__(self):
        validate_stable_id(self.record_id)
        for value,kind in ((self.reservation,E1AllocationReservation),(self.specification,E1CompactFrozenSpecification),(self.provenance,NumericalProducingProvenance),(self.scalar_definition,MatrixParameterScalarDefinition)):
            if type(value) is not kind:raise TypeError('compact E1 manifest keeps actual allocation/science/provenance/scalar owners')
            value.__post_init__()
        selection=self.specification.selection
        if selection.reservation!=identity(self.reservation):raise ValueError('compact E1 manifest substitutes the original actual reservation')
        selection.criterion.validate_allocation(self.reservation.allocation,selection.factor_rule)
        _publication(self.scalar_publication,self.scalar_definition)
        owner=selection.factor_rule.scalar_closure.normalization_owner
        publication=self.scalar_publication
        if (owner.artifact_id,owner.payload_schema,owner.sha256,owner.media_type,owner.size_bytes)!=(publication.logical.logical_artifact_id,self.scalar_definition.SCHEMA,self.scalar_definition.fingerprint(),'application/json',len(self.scalar_definition.canonical_bytes())):
            raise ValueError('compact E1 changes original scalar0.30 comparison custody')


@dataclass(frozen=True,slots=True)
class E1CompactSource(_Identity,CanonicalRecord):
    SCHEMA:ClassVar[str]='empirical-lawhood/matrix-factor-confirmation/compact-source'
    VERSION:ClassVar[str]='2.0.0'
    source_id:str
    manifest:ObjectIdentity
    root:E1HistoryRoot
    coordinate:MatrixParameterCoordinate
    rule:E1FactorRule
    criterion:ObjectIdentity
    numerical_design:MatrixParameterNumericalDesign
    factor_numerical_design:MatrixParameterFactorNumericalDesign
    provenance:ObjectIdentity
    implementation_commit:str
    code_sources_sha256:str
    dependency_lock_sha256:str

    def __post_init__(self):
        validate_stable_id(self.source_id);exact_pin(self.manifest,E1CompactManifest);exact_pin(self.criterion,E1CompactCriterion);exact_pin(self.provenance,NumericalProducingProvenance)
        for value,kind in ((self.root,E1HistoryRoot),(self.coordinate,MatrixParameterCoordinate),(self.rule,E1FactorRule),(self.numerical_design,MatrixParameterNumericalDesign),(self.factor_numerical_design,MatrixParameterFactorNumericalDesign)):
            if type(value) is not kind:raise TypeError('compact E1 source requires exact single-root mathematical operands')
            value.__post_init__()
        if (self.root.coordinate!=coordinate_identity(self.coordinate) or self.root.root.clock_id!=self.coordinate.clock_id
                or self.coordinate.observation_ticks!=self.rule.lattice or self.coordinate.primary_view.timestep!=self.rule.primary_dt
                or self.rule.risk_start_tick != 0 or self.rule.sectors != ('X', 'Y') or len(self.implementation_commit)!=40
                or any(c not in '0123456789abcdef' for c in self.implementation_commit)):
            raise ValueError('compact E1 changes its actual root, paired clock or producing revision')
        validate_sha256(self.code_sources_sha256);validate_sha256(self.dependency_lock_sha256)
        size=sum(prod(shape)*({'<c16':16,'<f8':8,'<i8':8}[dtype]) for dtype,shape in expected_members(self.coordinate).values())
        if size+11*10000>MAXIMUM_MATRIX_ARRAY_BYTES:raise ValueError('compact E1 complete native history exceeds bounded array transport')

    @property
    def root_id(self):return self.root.root.root_id


def sources_for_manifest(manifest):
    """Validate/hash complete immutable context once; no whole-bank per-root join."""
    if type(manifest) is not E1CompactManifest:raise TypeError('compact E1 requires its actual shared manifest')
    manifest.__post_init__()
    allocation=manifest.reservation.allocation;selection=manifest.specification.selection;p=manifest.provenance
    pin=identity(manifest);criterion=identity(selection.criterion);coordinates={coordinate_identity(c):c for c in allocation.coordinates}
    provenance=p.identity
    return tuple(E1CompactSource('source.'+row.root.root_id,pin,row,coordinates[row.coordinate],selection.factor_rule,criterion,
        selection.numerical_design,selection.factor_numerical_design,provenance,p.observed_git_head,p.code_sources_sha256,p.dependency_lock_sha256) for row in allocation.roots)


@dataclass(frozen=True,slots=True)
class E1CompactOperationConfig(_Identity,CanonicalRecord):
    SCHEMA:ClassVar[str]='empirical-lawhood/matrix-factor-confirmation/compact-operation-config'
    config_id:str
    operation:str
    source:E1CompactSource

    def __post_init__(self):
        validate_stable_id(self.config_id)
        if type(self.source) is not E1CompactSource or self.operation not in PHASES or self.config_id!='config.'+NAMESPACE+'.'+self.source.root_id+'.'+self.operation:
            raise ValueError('compact E1 config substitutes exact root/phase')
        self.source.__post_init__()


@dataclass(frozen=True,slots=True)
class E1CompactCommitment(_Identity,CanonicalRecord):
    SCHEMA:ClassVar[str]='empirical-lawhood/matrix-factor-confirmation/compact-commitment'
    record_id:str
    manifest:ObjectIdentity
    allocation:ObjectIdentity
    scientific_selection:ObjectIdentity
    criterion:ObjectIdentity
    root_count:int
    source_roster_sha256:str

    def __post_init__(self):
        validate_stable_id(self.record_id)
        for value,kind in ((self.manifest,E1CompactManifest),(self.allocation,E1HistoryAllocation),(self.scientific_selection,E1CompactScientificSelection),(self.criterion,E1CompactCriterion)):exact_pin(value,kind)
        if type(self.root_count) is not int or self.root_count<1:raise ValueError('compact E1 commitment drops its complete assigned census')
        validate_sha256(self.source_roster_sha256)


def commitment_for(manifest,sources):
    expected=sources_for_manifest(manifest)
    if tuple(sources)!=expected:raise ValueError('compact E1 commitment changes selected root/source correspondence')
    roster=tuple(identity(source) for source in sources)
    return E1CompactCommitment('commitment.'+manifest.record_id,sources[0].manifest,identity(manifest.reservation.allocation),identity(manifest.specification.selection),identity(manifest.specification.selection.criterion),len(sources),sha256(canonical_json_bytes(roster)).hexdigest())


NATIVE_HISTORY_OPERATION_V1 = 'matrix-e1-compact.full-paired-history'
NATIVE_HISTORY_OPERATION = 'matrix-e1-compact.full-paired-history.direct-operands.v2'


def native_history_sources(source, operation_id):
    """Keep historical rosters exact; current work binds its direct carriers.

    The shared prior commitment authenticates the complete manifest separately
    before native entry. Its manifest pin is already inside the compact source.
    """
    values = (identity(source), coordinate_identity(source.coordinate), source.provenance)
    if operation_id == NATIVE_HISTORY_OPERATION_V1:
        values = (*values, source.manifest)
    elif operation_id != NATIVE_HISTORY_OPERATION:
        raise ValueError('E1 history changes its declared native operation revision')
    return tuple(sorted(values, key=lambda value: value.object_id))

@dataclass(frozen=True, slots=True)
class E1CompactArrays(_Identity,CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-confirmation/compact-arrays'
    operand_id: str
    source: ObjectIdentity
    role: str
    array_artifact: ArtifactIdentity
    members: tuple[MatrixArrayMember, ...]
    producers: tuple[ObjectIdentity, ...]
    outcome_access: OutcomeAccess
    visibility_ceiling: VisibilityCeiling

    def __post_init__(self):
        exact_pin(self.source,E1CompactSource)
        validate_stable_id(self.operand_id)
        require_sorted_unique_ids(self.members, attribute='name', field_name='members')
        require_sorted_unique_ids(self.producers, attribute='object_id', field_name='producers')
        if (self.source.object_schema != E1CompactSource.SCHEMA or self.role not in ('NATIVE_HISTORY', 'FACTOR_DIAGNOSTICS')
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
class E1CompactNativeHistory(_Identity,CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-confirmation/compact-native-history'
    history_id: str
    source: ObjectIdentity
    coordinate: ObjectIdentity
    root_id: str
    independent_group_id: str
    clock_id: str
    arrays: E1CompactArrays
    native: MatrixParameterNativeHistory
    completed_primary_steps: int
    completed_fine_steps: int

    def __post_init__(self):
        exact_pin(self.source,E1CompactSource);exact_pin(self.coordinate,MatrixParameterCoordinate)
        for name in ('history_id', 'root_id', 'independent_group_id', 'clock_id'):
            validate_stable_id(getattr(self, name))
        if (type(self.arrays) is not E1CompactArrays or self.arrays.role != 'NATIVE_HISTORY'
                or self.source != self.arrays.source or self.source.object_schema != E1CompactSource.SCHEMA
                or type(self.native) is not MatrixParameterNativeHistory
                or type(self.completed_primary_steps) is not int or self.completed_primary_steps < 1
                or self.completed_fine_steps != 2*self.completed_primary_steps):
            raise ValueError('E1 history substitutes protected source or paired full native history')

    def validate_source(self, source):
        E1OperationConfig = E1CompactOperationConfig
        self.arrays.validate_source(source)
        require_native_completion_receipt(self.native.completion, self.native.receipt,
            outcome_access=OutcomeAccess.EVALUATION_SEALED, visibility_ceiling=VisibilityCeiling.PROSPECTIVE)
        root, definition = source.root.root, self.native.definition
        streams = tuple(sorted((source.root.stream_identity(s) for s in source.root.streams), key=lambda x: x.object_id))
        native_task = 'native-subwork.'+sha256((definition.parent_contact.task_id+':'+definition.subwork_id).encode()).hexdigest()
        native_attempt = definition.parent_contact.run_id+'.'+native_task+'.attempt-001'
        consumed = tuple(sorted((source.root.stream_identity(s) for s in source.root.streams
            if s.purpose.startswith('preparation') or source.coordinate.autonomous_ticks), key=lambda x: x.object_id))
        if (self.source != identity(source) or self.coordinate != coordinate_identity(source.coordinate)
                or (self.root_id, self.independent_group_id, self.clock_id) != (root.root_id, root.independent_group_id, root.clock_id)
                or self.completed_primary_steps != source.coordinate.total_ticks or definition.streams != streams
                or definition.subwork_id != 'paired-history.'+source.root_id
                or definition.configuration != identity(E1OperationConfig('config.'+NAMESPACE+'.'+source.root_id+'.history', 'history', source))
                or definition.parent_contact.task_id != NAMESPACE+'.'+source.root_id+'.history'
                or definition.parent_contact.implementation_commit != source.implementation_commit
                or (self.native.receipt.run_id, self.native.receipt.task_id, self.native.receipt.attempt_id) !=
                   (definition.parent_contact.run_id, native_task, native_attempt)
                or self.native.completion.consumed_streams != consumed
                or definition.code_sources_sha256 != source.code_sources_sha256
                or definition.dependency_lock_sha256 != source.dependency_lock_sha256
                or definition.sources != native_history_sources(source, definition.operation_id)):
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
class E1CompactNumericalAssessment(_Identity,CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-confirmation/compact-numerical-assessment'
    assessment_id: str
    source: ObjectIdentity
    history: ObjectIdentity
    numerical_design: ObjectIdentity
    controls: tuple[MatrixParameterHistoryControl, ...]
    numerical_pass: bool

    def __post_init__(self):
        exact_pin(self.source,E1CompactSource);exact_pin(self.history,E1CompactNativeHistory);exact_pin(self.numerical_design,MatrixParameterNumericalDesign)
        validate_stable_id(self.assessment_id)
        if (self.source.object_schema != E1CompactSource.SCHEMA or self.history.object_schema != E1CompactNativeHistory.SCHEMA
                or tuple(c.control_id for c in self.controls) != METHODS or type(self.numerical_pass) is not bool
                or self.numerical_pass != all(c.disposition == 'SATISFIED' for c in self.controls)):
            raise ValueError('E1 independent numerical assessment loses complete exact controls')


@dataclass(frozen=True, slots=True)
class E1CompactFactorRootRole(_Identity,CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-confirmation/compact-factor-root-role'
    root_id: str
    independent_unit_id: str
    family_id: str
    source: ObjectIdentity
    native_arrays: ArtifactIdentity
    native_result: ObjectIdentity

    def __post_init__(self):
        exact_pin(self.source,E1CompactSource);exact_pin(self.native_result,E1CompactNativeHistory)
        for name in ('root_id', 'independent_unit_id'):
            validate_stable_id(getattr(self, name))
        if (self.family_id not in FOUR_FAMILY_PREPARATION_IDS or self.source.object_schema != E1CompactSource.SCHEMA
                or self.native_result.object_schema != E1CompactNativeHistory.SCHEMA):
            raise ValueError('E1 factor root cannot accept historical exposed source/history roles')


@dataclass(frozen=True, slots=True)
class E1CompactFactorTrace(_Identity,CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-confirmation/compact-factor-trace'
    VERSION: ClassVar[str] = '2.0.0'
    root: E1CompactFactorRootRole
    rule: ObjectIdentity
    view: str
    sector: str
    observations: tuple[FactorObservation, ...]
    moving_lifetime: FactorLifetime
    origin_fixed_lifetime: FactorLifetime
    diagnostics: ArtifactIdentity
    diagnostic_members: tuple[MatrixArrayMember, ...]

    def __post_init__(self):
        exact_pin(self.rule,E1FactorRule)
        if (type(self.root) is not E1CompactFactorRootRole or self.rule.object_schema != E1FactorRule.SCHEMA
                or self.view not in VIEWS or self.sector not in ('X', 'Y')
                or not self.observations or tuple(o.tick for o in self.observations) != tuple(sorted({o.tick for o in self.observations}))
                or not self.diagnostic_members):
            raise ValueError('E1 trace substitutes distinct root/rule/full ordered observations')


@dataclass(frozen=True, slots=True)
class E1CompactFactorProduct(_Identity,CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-confirmation/compact-factor-product'
    VERSION: ClassVar[str] = '2.0.0'
    product_id: str
    source: ObjectIdentity
    history: ObjectIdentity
    numerical_assessment: ObjectIdentity
    history_numerical_pass: bool
    traces: tuple[E1CompactFactorTrace, ...]
    arrays: E1CompactArrays

    def __post_init__(self):
        exact_pin(self.source,E1CompactSource);exact_pin(self.history,E1CompactNativeHistory);exact_pin(self.numerical_assessment,E1CompactNumericalAssessment)
        validate_stable_id(self.product_id)
        if (self.source.object_schema != E1CompactSource.SCHEMA or self.history.object_schema != E1CompactNativeHistory.SCHEMA
                or self.numerical_assessment.object_schema != E1CompactNumericalAssessment.SCHEMA
                or type(self.history_numerical_pass) is not bool or type(self.arrays) is not E1CompactArrays
                or self.arrays.role != 'FACTOR_DIAGNOSTICS' or self.arrays.source != self.source
                or not self.traces or any(type(t) is not E1CompactFactorTrace for t in self.traces)):
            raise ValueError('E1 factor product cannot promote exposed factor products')


@dataclass(frozen=True, slots=True)
class E1CompactFactorAssessment(_Identity,CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-confirmation/compact-factor-assessment'
    assessment_id: str
    source: ObjectIdentity
    product: ObjectIdentity
    numerical_design: ObjectIdentity
    controls: tuple[MatrixParameterFactorControl, ...]
    numerical_pass: bool

    def __post_init__(self):
        exact_pin(self.source,E1CompactSource);exact_pin(self.product,E1CompactFactorProduct);exact_pin(self.numerical_design,MatrixParameterFactorNumericalDesign)
        from empirical_lawhood.adapters.methods.matrix_parameter_factor.records import METHODS as FACTOR_METHODS
        validate_stable_id(self.assessment_id)
        if (self.source.object_schema != E1CompactSource.SCHEMA or self.product.object_schema != E1CompactFactorProduct.SCHEMA
                or tuple(c.method for c in self.controls) != FACTOR_METHODS or type(self.numerical_pass) is not bool
                or self.numerical_pass != all(c.disposition in ('SATISFIED', 'NOT_APPLICABLE') for c in self.controls)):
            raise ValueError('E1 factor assessment loses full independently checked witness controls')


@dataclass(frozen=True, slots=True)
class E1CompactUnavailableRoot(_Identity,CanonicalRecord):
    """Retained non-success receipt; never an invented factor assessment.

    The custody caller authenticates original receipts and contacts and supplies
    the complete operational census. A contact with no completion receipt is
    explicit UNKNOWN_CONTACT with no replay; an entirely absent contact needs
    the platform's absence census and cannot be asserted by this value record.
    """
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-confirmation/compact-unavailable-root'
    source: ObjectIdentity
    receipt: CanonicalTaskReceipt | None = None
    contact: NativeEffectContact | None = None

    def __post_init__(self):
        exact_pin(self.source,E1CompactSource)
        if (self.source.object_schema != E1CompactSource.SCHEMA or self.receipt is None and self.contact is None
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
class E1CompactClosedRoot(CanonicalRecord):
    """Actual closed task gaps, separate from a failed receipt or an assessment."""

    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-confirmation/compact-closed-root'
    source: ObjectIdentity
    implementation_commit: str
    terminal_attempts: tuple[RecoveryTerminalAttempt, ...]
    recovery_events: tuple[TaskRecoveryEvent, ...]
    contact: NativeEffectContact | None

    def __post_init__(self):
        exact_pin(self.source, E1CompactSource)
        if (type(self.implementation_commit) is not str or len(self.implementation_commit) != 40
                or any(value not in '0123456789abcdef' for value in self.implementation_commit)):
            raise ValueError('closed E1 root requires the exact producing commit')
        if (type(self.terminal_attempts) is not tuple or not self.terminal_attempts
                or any(type(row) is not RecoveryTerminalAttempt for row in self.terminal_attempts)
                or type(self.recovery_events) is not tuple
                or any(type(row) is not TaskRecoveryEvent for row in self.recovery_events)
                or self.contact is not None and type(self.contact) is not NativeEffectContact):
            raise TypeError('closed E1 root requires original terminal/event/contact records')
        require_sorted_unique_ids(self.terminal_attempts, attribute='task_id', field_name='closed E1 tasks')
        require_sorted_unique_ids(self.recovery_events, attribute='task_id', field_name='closed E1 events')
        events = {row.task_id: row for row in self.recovery_events}
        if not set(events).issubset(row.task_id for row in self.terminal_attempts):
            raise ValueError('closed E1 root changes its original event census')
        for summary in self.terminal_attempts:
            summary.__post_init__()
            if (summary.disposition not in (RecoveryTerminalDisposition.FAILED, RecoveryTerminalDisposition.BLOCKED)
                    or summary.receipt_id is not None or summary.receipt_sha256 is not None):
                raise ValueError('closed E1 root cannot invent successful completion')
            event = events.get(summary.task_id)
            if event is None:
                # The common recovery owner permits terminal-only retryable
                # blocks. Do not invent a durable event for those observations.
                if (summary.disposition is not RecoveryTerminalDisposition.BLOCKED
                        or TaskBlockReason(summary.reason_code).kind is not TaskBlockKind.RETRYABLE):
                    raise ValueError('closed E1 root loses its required original recovery event')
                continue
            event.__post_init__()
            if event.reason_codes != (summary.reason_code,) or event.receipt_id is not None:
                raise ValueError('closed E1 root substitutes its actual operational reason')
            if event.disposition is TaskRecoveryDisposition.NOT_ATTEMPTED:
                if summary.disposition is not RecoveryTerminalDisposition.BLOCKED:
                    raise ValueError('closed E1 nonattempt cannot become an entered failure')
            elif (event.attempt_id != summary.attempt_id
                    or event.disposition.value != summary.disposition.value):
                raise ValueError('closed E1 root substitutes its actual entered attempt')
        if self.contact is not None:
            self.contact.__post_init__()
            matches = tuple(row for row in self.terminal_attempts if row.task_id == self.contact.task_id)
            if (len(matches) != 1 or matches[0].attempt_id != self.contact.attempt_id
                    or self.contact.implementation_commit != self.implementation_commit
                    or (event := events.get(self.contact.task_id)) is None
                    or event.run_id != self.contact.run_id or event.attempt_id != self.contact.attempt_id):
                raise ValueError('closed E1 root substitutes its original native contact')
        elif any(row.reason_code == 'unknown-completion' for row in self.terminal_attempts):
            raise ValueError('closed E1 unknown completion requires its actual native contact')

    @property
    def availability(self):
        return ('UNKNOWN_CONTACT' if any(row.reason_code == 'unknown-completion'
            for row in self.terminal_attempts) else 'UNAVAILABLE')


@dataclass(frozen=True,slots=True)
class E1CompactPopulationResult(_Identity,CanonicalRecord):
    SCHEMA:ClassVar[str]='empirical-lawhood/matrix-factor-confirmation/compact-population-result'
    VERSION:ClassVar[str]='2.0.0'
    result_id:str
    manifest:ObjectIdentity
    allocation:ObjectIdentity
    criterion:ObjectIdentity
    root_ids:tuple[str,...]
    sources:tuple[ObjectIdentity,...]
    products:tuple[ObjectIdentity,...]
    assessments:tuple[ObjectIdentity,...]
    unavailable:tuple[E1CompactUnavailableRoot,...]
    events:tuple[E1RootOccurrence,...]
    findings:tuple[E1OccurrenceCell,...]
    risk_rows:tuple[E1RiskRow,...]
    primary_alpha_numerator:int
    primary_alpha_denominator:int
    cell_alpha_numerator:int
    cell_alpha_denominator:int
    scientific_status:ScientificStatus
    reason_codes:tuple[str,...]

    def __post_init__(self):
        self._validate_population(E1CompactUnavailableRoot)

    def _validate_population(self, unavailable_type):
        validate_stable_id(self.result_id);require_sorted_unique_strings(self.root_ids,field_name='root_ids',allow_empty=False);require_sorted_unique_strings(self.reason_codes,field_name='reason_codes',allow_empty=False)
        for value,kind in ((self.manifest,E1CompactManifest),(self.allocation,E1HistoryAllocation),(self.criterion,E1CompactCriterion)):exact_pin(value,kind)
        if (len(self.sources)!=len(self.root_ids) or len(set(self.sources))!=len(self.sources)
                or len(self.products)+len(self.unavailable)!=len(self.root_ids) or len(self.assessments)!=len(self.products)
                or len(set(self.products))!=len(self.products) or len(set(self.assessments))!=len(self.assessments)
                or type(self.scientific_status) is not ScientificStatus
                or self.scientific_status not in (ScientificStatus.PARTIAL, ScientificStatus.UNEVALUABLE)):
            raise ValueError('compact E1 population result loses complete assigned roots or estimation-only status')
        for values,kind in ((self.sources,E1CompactSource),(self.products,E1CompactFactorProduct),(self.assessments,E1CompactFactorAssessment)):
            for value in values:exact_pin(value,kind)
        for values,kind in ((self.unavailable,unavailable_type),(self.events,E1RootOccurrence),(self.findings,E1OccurrenceCell),(self.risk_rows,E1RiskRow)):
            if type(values) is not tuple or any(type(value) is not kind for value in values):raise TypeError('compact E1 result substitutes exact records')
        for n,d in ((self.primary_alpha_numerator,self.primary_alpha_denominator),(self.cell_alpha_numerator,self.cell_alpha_denominator)):
            if type(n) is not int or type(d) is not int or not 0<n<d:raise ValueError('compact E1 result changes exact selected alpha')
        if ((self.primary_alpha_numerator, self.primary_alpha_denominator) != (1, 160)
                or (self.cell_alpha_numerator, self.cell_alpha_denominator) != (1, 1280)
                or tuple(event.key for event in self.events) != tuple((root, view, sector)
                    for root in self.root_ids for view in VIEWS for sector in ('X', 'Y'))
                or any(event.source != self.sources[self.root_ids.index(event.root_id)] for event in self.events)):
            raise ValueError('compact E1 map changes its eight-cell alpha or complete assigned root events')
        counts = {family: sum(event.family_id == family and event.view == 'PRIMARY' and event.sector == 'Y'
            for event in self.events) for family in FOUR_FAMILY_PREPARATION_IDS}
        if self.findings != occurrence_cells(self.events, family_counts=counts):
            raise ValueError('compact E1 intervals differ from their complete categorical evidence')
        expected_status = ScientificStatus.PARTIAL if any(event.numerical_usable for event in self.events) else ScientificStatus.UNEVALUABLE
        if self.scientific_status is not expected_status or 'e1-estimation-map-no-binary-claim' not in self.reason_codes:
            raise ValueError('compact E1 occurrence estimates cannot become a universal support claim')


@dataclass(frozen=True, slots=True)
class E1CompactClosedPopulationResult(E1CompactPopulationResult):
    """Read-derived whole population; no completed scientific adjudication."""

    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-confirmation/compact-closed-population-result'
    VERSION: ClassVar[str] = '1.0.0'
    unavailable: tuple[E1CompactClosedRoot, ...]
    run_id: str
    execution_plan: ObjectIdentity
    recovery_index: ObjectIdentity
    operational_terminal: ObjectIdentity
    operational_status: str
    implementation_commit: str

    def __post_init__(self):
        self._validate_population(E1CompactClosedRoot)
        validate_stable_id(self.run_id)
        if (type(self.implementation_commit) is not str or len(self.implementation_commit) != 40
                or any(value not in '0123456789abcdef' for value in self.implementation_commit)):
            raise ValueError('closed E1 projection requires the exact producing commit')
        for value, kind in ((self.execution_plan, ExecutionPlan), (self.recovery_index, RunRecoveryIndex),
                (self.operational_terminal, RunRecoveryTerminalEvent)):
            exact_pin(value, kind)
        if self.operational_status not in ('FAILED', 'BLOCKED'):
            raise ValueError('closed E1 projection requires an actual unsuccessful operational terminal')
        for row in self.unavailable:
            row.__post_init__()
            if row.implementation_commit != self.implementation_commit:
                raise ValueError('closed E1 projection changes its producing implementation')
            if any((event.run_id, event.recovery_index) != (self.run_id, self.recovery_index)
                    for event in row.recovery_events):
                raise ValueError('closed E1 projection substitutes a different run or recovery index')
            if row.contact is not None and (row.contact.run_id, row.contact.execution_plan) != (
                    self.run_id, self.execution_plan):
                raise ValueError('closed E1 projection substitutes a different native execution')
