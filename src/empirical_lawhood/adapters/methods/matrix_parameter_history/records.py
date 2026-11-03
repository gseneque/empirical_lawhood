"""Parameter-history identities, complete root/stream and retained array joins.

These new development records do not widen any historical allocation, protocol,
protected factor source or scientific authority contract.
"""

from dataclasses import dataclass
from decimal import Decimal
from math import prod
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_history_analysis.records import HISTORY_PURPOSES, MatrixHistorySeed
from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole, MatrixProgrammeRoot
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history import MatrixParameterCoordinate
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA, MAXIMUM_MATRIX_ARRAY_BYTES, MatrixArrayMember
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord, require_sorted_unique_ids, validate_decimal, validate_stable_id,
)
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactProfile, CanonicalTaskReceipt
from empirical_lawhood.runtime.native_subwork import NativeSubworkCompletion, NativeSubworkDefinition, require_native_completion_receipt

EXPOSED = 'EXPOSED_DEVELOPMENT_NONPROMOTABLE'
METHODS = ('control.primary-trajectory', 'control.fine-trajectory', 'control.ou-innovation-reconstruction', 'control.ou-bath-impulse')


def identity(record):
    for name in ('allocation_id', 'source_id', 'design_id', 'operand_id', 'history_id', 'assessment_id', 'config_id'):
        if hasattr(record, name):
            return ObjectIdentity.from_record(getattr(record, name), record)
    raise ValueError('parameter history record has no declared identity')


def coordinate_identity(coordinate):
    return ObjectIdentity.from_record(coordinate.coordinate_id, coordinate)


def expected_members(coordinate):
    n = coordinate.total_ticks
    result = {}
    for view, count in (('primary', n + 1), ('fine', 2*n + 1)):
        for component in ('positions', 'momenta'):
            result[view+'_'+component] = ('<c16', (count, 2, 3, 4, 4))
        result[view+'_alpha_tilde'] = ('<f8', (count, 2))
        result[view+'_ticks'] = ('<i8', (count,))
    for name, count in (('primary_innovations', n), ('fine_innovations', 2*n), ('bridge_innovations', n)):
        result[name] = ('<c16', (count, 2, 3, 4, 4))
    return dict(sorted(result.items()))


@dataclass(frozen=True, slots=True)
class MatrixParameterRoot(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-history/root'
    root: MatrixProgrammeRoot
    coordinate: ObjectIdentity
    streams: tuple[MatrixHistorySeed, ...]

    def __post_init__(self):
        if (type(self.root) is not MatrixProgrammeRoot or self.root.role is not MatrixProgrammeRole.DEVELOPMENT
                or self.coordinate.object_schema != MatrixParameterCoordinate.SCHEMA
                or self.coordinate.object_id != self.root.coordinate_id
                or tuple(s.purpose for s in self.streams) != HISTORY_PURPOSES
                or any(type(s) is not MatrixHistorySeed for s in self.streams)
                or len({s.effective_seed for s in self.streams}) != len(HISTORY_PURPOSES)):
            raise ValueError('parameter root changes development coordinate or complete four-purpose streams')

    def stream_identity(self, stream):
        if stream not in self.streams:
            raise ValueError('parameter stream is outside its actual root')
        return ObjectIdentity.from_record('stream.'+self.root.root_id+'.'+stream.purpose, stream)


@dataclass(frozen=True, slots=True)
class MatrixParameterAllocation(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-history/allocation'
    allocation_id: str
    coordinates: tuple[MatrixParameterCoordinate, ...]
    roots: tuple[MatrixParameterRoot, ...]
    prior_effective_seeds: tuple[int, ...]
    exposure: str = EXPOSED

    def __post_init__(self):
        validate_stable_id(self.allocation_id)
        require_sorted_unique_ids(self.coordinates, attribute='coordinate_id', field_name='coordinates')
        ids = tuple(r.root.root_id for r in self.roots)
        if (not self.coordinates or not self.roots or ids != tuple(sorted(set(ids)))
                or self.exposure != EXPOSED
                or self.prior_effective_seeds != tuple(sorted(set(self.prior_effective_seeds)))
                or any(type(s) is not int or not 0 <= s < 2**128 for s in self.prior_effective_seeds)):
            raise ValueError('parameter allocation loses complete roots, prior exposure or development standing')
        coordinates = {coordinate_identity(c): c for c in self.coordinates}
        record_names = {}
        for c in self.coordinates:
            for key,record in ((c.member.member_id,c.member),(c.primary_view.view_id,c.primary_view),(c.fine_view.view_id,c.fine_view)):
                if record_names.setdefault(key,record) != record:
                    raise ValueError('parameter allocation aliases a member/view ID across different scientific operands')
        used = set()
        owners = {}
        physical_regimes = {}
        for row in self.roots:
            if type(row) is not MatrixParameterRoot or row.coordinate not in coordinates:
                raise ValueError('parameter allocation substitutes a coordinate/root identity')
            c = coordinates[row.coordinate]
            if row.root.clock_id != c.clock_id:
                raise ValueError('parameter root changes its coordinate physical clock')
            used.add(row.coordinate)
            # IDs and dt/refinement cannot invent a physical regime. Schedule
            # and duration remain exact coordinate operands, not seed labels.
            physical = (c.member.mass_x, c.member.mass_y, c.member.cross_coupling_gamma, c.member.beta_rule,
                c.primary_view.friction_gamma, c.primary_view.bath_temperature, c.family_id,
                c.target_x, c.target_y, c.decreasing_start, c.ramp_ticks*c.primary_view.timestep,
                c.autonomous_ticks*c.primary_view.timestep, c.initial_state_rule_id, c.preparation_rule_id)
            if physical_regimes.setdefault(row.root.regime_id, physical) != physical:
                raise ValueError('parameter regime label mixes different physical coordinates')
            for s in row.streams:
                if s.effective_seed in self.prior_effective_seeds:
                    raise ValueError('parameter allocation reuses an explicitly exposed numeric stream')
                key = s.effective_seed
                owner = (row.root.independent_group_id, s.purpose)
                if owners.setdefault(key, owner) != owner:
                    raise ValueError('independent parameter groups or purposes collide in consumed128bits')
        if used != set(coordinates):
            raise ValueError('parameter allocation omits a requested coordinate')


@dataclass(frozen=True, slots=True)
class MatrixParameterNumericalDesign(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-history/numerical-design'
    design_id: str
    trajectory_tolerance: Decimal
    bridge_tolerance: Decimal
    error_norm: str = 'FULL_REAL_HERMITIAN_HS_L2'
    method: str = 'LITERAL_TRACE_WORD_GRADIENT_BAOAB_AND_WEIGHTED_OU_V1'
    standing: str = 'FINITE_DT_EMPIRICAL_EQUATION_CROSSCHECK_NO_CONTINUUM_BOUND'

    def __post_init__(self):
        validate_stable_id(self.design_id)
        for name in ('trajectory_tolerance', 'bridge_tolerance'):
            validate_decimal(getattr(self, name), field_name=name, minimum=Decimal(0))
            if getattr(self,name) == 0:
                raise ValueError('parameter independent tolerances must be explicitly positive')
        if (self.error_norm != 'FULL_REAL_HERMITIAN_HS_L2'
                or self.method != 'LITERAL_TRACE_WORD_GRADIENT_BAOAB_AND_WEIGHTED_OU_V1'
                or self.standing != 'FINITE_DT_EMPIRICAL_EQUATION_CROSSCHECK_NO_CONTINUUM_BOUND'):
            raise ValueError('parameter design confuses independent equations with numerical qualification')


@dataclass(frozen=True, slots=True)
class MatrixParameterHistorySource(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-history/source'
    source_id: str
    allocation: MatrixParameterAllocation
    root_id: str
    provenance: NumericalProducingProvenance
    numerical_design: MatrixParameterNumericalDesign

    def __post_init__(self):
        validate_stable_id(self.source_id)
        if (type(self.allocation) is not MatrixParameterAllocation or type(self.provenance) is not NumericalProducingProvenance
                or type(self.numerical_design) is not MatrixParameterNumericalDesign
                or self.root_id not in {r.root.root_id for r in self.allocation.roots}):
            raise ValueError('parameter source omits exact allocation/root/provenance/design')
        if self.coordinate.primary_view.rng_algorithm not in ('numpy.pcg64dxsm', 'numpy-pcg64dxsm'):
            raise ValueError('parameter source supports only explicitly selected PCG64DXSM history streams')
        # Scientific duration is unrestricted; this initial complete package
        # must fit the unchanged bounded transport, before any RNG/contact.
        size = sum(prod(shape)*({'<c16':16,'<f8':8,'<i8':8}[dtype])
                   for dtype, shape in expected_members(self.coordinate).values())
        if size + 11*10000 > MAXIMUM_MATRIX_ARRAY_BYTES:
            raise ValueError('declared parameter history needs an explicit chunked successor before effects')

    @property
    def root(self):
        return next(r for r in self.allocation.roots if r.root.root_id == self.root_id)

    @property
    def coordinate(self):
        return next(c for c in self.allocation.coordinates if coordinate_identity(c) == self.root.coordinate)


@dataclass(frozen=True, slots=True)
class MatrixParameterHistoryArrays(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-history/arrays'
    operand_id: str
    source: ObjectIdentity
    allocation: ObjectIdentity
    coordinate: ObjectIdentity
    root_id: str
    array_artifact: ArtifactIdentity
    members: tuple[MatrixArrayMember, ...]
    producers: tuple[ObjectIdentity, ...]
    exposure: str = EXPOSED

    def __post_init__(self):
        for name in ('operand_id', 'root_id'):
            validate_stable_id(getattr(self, name))
        require_sorted_unique_ids(self.members, attribute='name', field_name='members')
        require_sorted_unique_ids(self.producers, attribute='object_id', field_name='producers')
        if (self.source.object_schema != MatrixParameterHistorySource.SCHEMA
                or self.allocation.object_schema != MatrixParameterAllocation.SCHEMA
                or self.coordinate.object_schema != MatrixParameterCoordinate.SCHEMA
                or not self.members or not self.producers or self.exposure != EXPOSED
                or any(not m.finite_required for m in self.members)
                or sum(m.size_bytes for m in self.members) > MAXIMUM_MATRIX_ARRAY_BYTES
                or self.array_artifact.payload_schema != MATRIX_ARRAY_SCHEMA
                or self.array_artifact.media_type != 'application/x-npz'
                or not 0 < self.array_artifact.size_bytes <= MAXIMUM_MATRIX_ARRAY_BYTES):
            raise ValueError('parameter arrays substitute complete bounded source/member/exposure')

    def validate_source(self, source):
        if (self.source != identity(source) or self.allocation != identity(source.allocation)
                or self.coordinate != coordinate_identity(source.coordinate) or self.root_id != source.root_id
                or self.producers != tuple(sorted((identity(source), coordinate_identity(source.coordinate)), key=lambda x:x.object_id))
                or {m.name:(m.dtype,m.shape) for m in self.members} != expected_members(source.coordinate)):
            raise ValueError('parameter arrays change exact source/root/coordinate/complete clocks')


@dataclass(frozen=True, slots=True)
class MatrixParameterNativeHistory(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-history/native-history'
    definition: NativeSubworkDefinition
    completion: NativeSubworkCompletion
    receipt: CanonicalTaskReceipt

    def __post_init__(self):
        require_native_completion_receipt(self.completion, self.receipt)
        if (self.completion.definition != self.definition.identity
                or self.completion.operational_status is not OperationalStatus.SUCCEEDED
                or self.receipt.operational_status is not OperationalStatus.SUCCEEDED
                or self.completion.output_ids != ('arrays',) or self.completion.omitted_output_ids
                or set((*self.completion.consumed_streams,*self.completion.unconsumed_streams)) != set(self.definition.streams)
                or self.completion.unknown_streams
                or self.receipt.implementation_commit != self.definition.parent_contact.implementation_commit
                or not set(self.definition.input_materialization_ids) <= set(self.receipt.input_materialization_ids)):
            raise ValueError('parameter history requires known native completion and original exact receipt')


@dataclass(frozen=True, slots=True)
class MatrixParameterHistoryProduct(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-history/product'
    history_id: str
    source: ObjectIdentity
    coordinate: ObjectIdentity
    root_id: str
    independent_group_id: str
    clock_id: str
    arrays: MatrixParameterHistoryArrays
    native: MatrixParameterNativeHistory
    completed_primary_steps: int
    completed_fine_steps: int

    def __post_init__(self):
        for name in ('history_id','root_id','independent_group_id','clock_id'):
            validate_stable_id(getattr(self,name))
        if (self.source != self.arrays.source or self.coordinate != self.arrays.coordinate or self.root_id != self.arrays.root_id
                or type(self.completed_primary_steps) is not int or self.completed_primary_steps < 1
                or self.completed_fine_steps != 2*self.completed_primary_steps):
            raise ValueError('parameter product changes complete native paired clock/source')

    def validate_source(self, source):
        self.arrays.validate_source(source)
        selected = source.root.root
        definitions = self.native.definition
        consumed = tuple(sorted((source.root.stream_identity(s) for s in source.root.streams
            if s.purpose.startswith('preparation') or source.coordinate.autonomous_ticks), key=lambda x:x.object_id))
        if (self.source != identity(source) or self.coordinate != coordinate_identity(source.coordinate)
                or self.root_id != selected.root_id or self.independent_group_id != selected.independent_group_id
                or self.clock_id != selected.clock_id or self.completed_primary_steps != source.coordinate.total_ticks
                or self.native.completion.consumed_streams != consumed
                or definitions.streams != tuple(sorted((source.root.stream_identity(s) for s in source.root.streams), key=lambda x:x.object_id))
                or definitions.code_sources_sha256 != source.provenance.code_sources_sha256
                or definitions.dependency_lock_sha256 != source.provenance.dependency_lock_sha256
                or set(definitions.sources) != {identity(source),identity(source.allocation),coordinate_identity(source.coordinate),source.provenance.identity}):
            raise ValueError('parameter product substitutes native source/stream/provenance/group lineage')
        native_arrays = tuple(a for a in self.native.receipt.output_logical_artifacts if a.payload_schema == MATRIX_ARRAY_SCHEMA)
        artifact = self.arrays.array_artifact
        if (len(native_arrays) != 1 or native_arrays[0].profile is not ArtifactProfile.MATRIX_ARRAY_NPZ
                or native_arrays[0].media_type != artifact.media_type or native_arrays[0].content_sha256 != artifact.sha256):
            raise ValueError('parameter product substitutes the actual receipted native array bytes')
        physical = next(p for p in self.native.receipt.output_materializations if p.logical_artifact_id == native_arrays[0].logical_artifact_id)
        if physical.physical_sha256 != artifact.sha256 or physical.size_bytes != artifact.size_bytes:
            raise ValueError('parameter product changes original native physical array custody')


@dataclass(frozen=True, slots=True)
class MatrixParameterHistoryControl(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-history/control'
    control_id: str
    method: str
    error: Decimal
    tolerance: Decimal
    disposition: str
    denominator_steps: int
    denominator_real_coordinates: int
    measured_errors: tuple[Decimal, ...]
    failed_steps: tuple[int, ...]

    def __post_init__(self):
        validate_stable_id(self.control_id)
        for value in (self.error,self.tolerance,*self.measured_errors):
            validate_decimal(value,field_name='complete control error/tolerance',minimum=Decimal(0))
        if (self.control_id not in METHODS or self.denominator_real_coordinates not in (96,192)
                or type(self.denominator_steps) is not int or self.denominator_steps < 1
                or len(self.measured_errors) != self.denominator_steps or self.error != max(self.measured_errors)
                or self.failed_steps != tuple(i+1 for i,e in enumerate(self.measured_errors) if e > self.tolerance)
                or self.disposition != ('VIOLATED' if self.failed_steps else 'SATISFIED')):
            raise ValueError('parameter control drops a denominator or changes independent verdict')
        method = dict(zip(METHODS,('PRIMARY_FULL192_TRACE_POLYNOMIAL_BAOAB_ALL_STEPS',
            'FINE_FULL192_TRACE_POLYNOMIAL_BAOAB_ALL_STEPS','WEIGHTED_OU_FULL192_ORIGINAL_COARSE_AND_BRIDGE_ALL_STEPS',
            'WEIGHTED_OU_FULL96_BATH_SCALED_COMPOSED_IMPULSE_ALL_STEPS'),strict=True))[self.control_id]
        if self.method != method:
            raise ValueError('parameter control substitutes its independently expressed numerical method')


@dataclass(frozen=True, slots=True)
class MatrixParameterHistoryAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-history/assessment'
    assessment_id: str
    source: ObjectIdentity
    history: ObjectIdentity
    numerical_design: ObjectIdentity
    controls: tuple[MatrixParameterHistoryControl, ...]
    numerical_pass: bool
    standing: str = 'FINITE_DT_EMPIRICAL_EQUATION_CROSSCHECK_NO_CONTINUUM_BOUND'

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        if (tuple(c.control_id for c in self.controls) != METHODS or type(self.numerical_pass) is not bool
                or self.numerical_pass != all(c.disposition == 'SATISFIED' for c in self.controls)
                or self.standing != 'FINITE_DT_EMPIRICAL_EQUATION_CROSSCHECK_NO_CONTINUUM_BOUND'):
            raise ValueError('parameter assessment fabricates numerical or scientific standing')
