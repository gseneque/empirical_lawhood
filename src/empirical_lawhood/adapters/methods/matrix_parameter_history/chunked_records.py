# SPDX-License-Identifier: MPL-2.0
"""Explicit segmented source and custody successors; closed v1/v2 stay intact."""

from dataclasses import dataclass
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_array_chunks import ChunkedMatrixArrays, MatrixArrayChunk
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history import MatrixParameterCoordinate
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history_segments import METHOD, OPERATION_ID, ParameterGeneratorState, segment_intervals
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_ou_domain import validate_parameter_ou_domain
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, canonical_json_bytes, validate_stable_id
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import CanonicalTaskReceipt
from empirical_lawhood.runtime.native_subwork import NativeSubworkCompletion, NativeSubworkDefinition

from .compact_records import MatrixParameterCompactSource
from .records import EXPOSED, METHODS, MatrixParameterAllocation, MatrixParameterHistoryControl, coordinate_identity, expected_members


def identity(record):
    for name in ('source_id','config_id','history_id','assessment_id','checkpoint_id','carrier_id','operand_id'):
        if hasattr(record,name):
            return ObjectIdentity.from_record(getattr(record,name),record)
    from .compact_records import identity as shared_identity
    return shared_identity(record)


@dataclass(frozen=True, slots=True)
class MatrixParameterChunkedSource(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-history/chunked-source'
    VERSION: ClassVar[str] = '3.0.0'
    source_id: str
    compact: MatrixParameterCompactSource
    segment_steps: int
    method: str = METHOD
    exposure: str = EXPOSED

    def __post_init__(self):
        validate_stable_id(self.source_id)
        if (type(self.compact) is not MatrixParameterCompactSource or type(self.segment_steps) is not int or self.segment_steps < 1
                or self.method != METHOD or self.exposure != EXPOSED):
            raise ValueError('chunked parameter source changes versioned complete scientific source')

    @property
    def root_id(self):
        return self.compact.root_id

    @property
    def root(self):
        return self.compact.root

    @property
    def allocation(self):
        return self.compact.allocation

    @property
    def coordinate(self):
        return self.compact.coordinate

    @property
    def provenance(self):
        return self.compact.provenance

    @property
    def numerical_design(self):
        return self.compact.numerical_design

    @property
    def allocation_scope_sha256(self):
        return self.compact.allocation_scope_sha256

    @property
    def requested_roots(self):
        return self.compact.requested_roots

    @property
    def requested_groups(self):
        return self.compact.requested_groups

    @property
    def numerical_view_ids(self):
        return self.compact.numerical_view_ids


@dataclass(frozen=True, slots=True)
class BoundChunkedParameterSource:
    source: MatrixParameterChunkedSource
    allocation: MatrixParameterAllocation
    coordinate: MatrixParameterCoordinate
    provenance: NumericalProducingProvenance

    @property
    def root_id(self):
        return self.source.root_id

    @property
    def root(self):
        return self.source.compact.root

    @property
    def numerical_design(self):
        return self.source.compact.numerical_design


def bind_source(source,allocation,coordinate,provenance,*,new_entry=False):
    if type(source) is not MatrixParameterChunkedSource:
        raise ValueError('chunked source requires its explicit new edition')
    s = source.compact
    if (type(allocation) is not MatrixParameterAllocation or type(coordinate) is not MatrixParameterCoordinate
            or type(provenance) is not NumericalProducingProvenance or s.allocation != identity(allocation)
            or s.coordinate != coordinate_identity(coordinate) or s.provenance != provenance.identity
            or s.root not in allocation.roots or coordinate not in allocation.coordinates
            or s.root.root.clock_id != coordinate.clock_id
            or s.allocation_scope_sha256 != sha256(canonical_json_bytes(allocation.roots)).hexdigest()
            or s.requested_roots != len(allocation.roots)
            or s.requested_groups != len({r.root.independent_group_id for r in allocation.roots})
            or s.numerical_view_ids != tuple(sorted((coordinate.primary_view.view_id,coordinate.fine_view.view_id)))
            or coordinate.primary_view.rng_algorithm not in ('numpy.pcg64dxsm','numpy-pcg64dxsm')):
        raise ValueError('chunked source substitutes authenticated complete allocation/coordinate/provenance')
    # Working-memory segment size is separate from the scientific duration.
    span = min(source.segment_steps,coordinate.total_ticks)
    leaf_bytes = (3*span+2)*2*96*16+(3*span+2)*24+4*span*96*16
    from empirical_lawhood.kernel.matrix_inputs import MAXIMUM_MATRIX_ARRAY_BYTES
    if leaf_bytes+11*10000 > MAXIMUM_MATRIX_ARRAY_BYTES:
        raise ValueError('chunked source selected working segment exceeds unchanged physical NPZ leaf')
    if new_entry:
        validate_parameter_ou_domain(coordinate)
    return BoundChunkedParameterSource(source,allocation,coordinate,provenance)


def segment_plan(bound):
    n,span = bound.coordinate.total_ticks,bound.source.segment_steps
    return tuple((start,min(start+span,n)) for start in range(0,n,span))


@dataclass(frozen=True, slots=True)
class MatrixParameterSegmentCheckpoint(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-history/segment-checkpoint'
    checkpoint_id: str
    source: ObjectIdentity
    coordinate: ObjectIdentity
    start: int
    stop: int
    science_arrays: MatrixArrayChunk
    terminal_arrays: MatrixArrayChunk
    generators: tuple[ParameterGeneratorState, ...]
    definition: ObjectIdentity
    previous: ObjectIdentity | None
    method: str = METHOD

    def __post_init__(self):
        validate_stable_id(self.checkpoint_id)
        if (self.source.object_schema != MatrixParameterChunkedSource.SCHEMA or self.coordinate.object_schema != MatrixParameterCoordinate.SCHEMA
                or type(self.start) is not int or type(self.stop) is not int or not 0 <= self.start < self.stop
                or type(self.science_arrays) is not MatrixArrayChunk or type(self.terminal_arrays) is not MatrixArrayChunk or self.definition.object_schema != NativeSubworkDefinition.SCHEMA
                or self.method != METHOD or (self.previous is None) != (self.start == 0)
                or self.previous is not None and self.previous.object_schema != self.SCHEMA):
            raise ValueError('parameter checkpoint loses exact phase/clock/previous native continuation')

    def validate_source(self,bound):
        s,c = bound.source,bound.coordinate
        producers = tuple(sorted((identity(s),coordinate_identity(c)),key=lambda i:i.object_id))
        if (self.source != identity(s) or self.coordinate != coordinate_identity(c) or (self.start,self.stop) not in segment_plan(bound)
                or self.terminal_arrays.producers != producers
                or tuple((m.name,m.dtype,m.shape) for m in self.terminal_arrays.members) != tuple((name,'<c16',(2,3,4,4))
                    for name in ('terminal_fine_momenta','terminal_fine_positions','terminal_primary_momenta','terminal_primary_positions'))
                or tuple(g.purpose for g in self.generators) != tuple(t.purpose for t in bound.root.streams)
                or any(g.effective_seed != t.effective_seed for g,t in zip(self.generators,bound.root.streams,strict=True))
                or any(g.completed_noise_matrices != (min(self.stop,c.ramp_ticks) if g.purpose.startswith('preparation') else max(0,self.stop-c.ramp_ticks)) for g in self.generators)):
            raise ValueError('parameter checkpoint changes complete source/stream cursor/terminal phase')


def _receipt_array(receipt,artifact):
    logical = tuple(a for a in receipt.output_logical_artifacts if a.logical_artifact_id == artifact.artifact_id)
    physical = tuple(a for a in receipt.output_materializations if a.logical_artifact_id == artifact.artifact_id)
    if (len(logical) != 1 or len(physical) != 1 or logical[0].payload_schema != artifact.payload_schema
            or logical[0].media_type != artifact.media_type or logical[0].content_sha256 != artifact.sha256
            or (physical[0].physical_sha256,physical[0].size_bytes) != (artifact.sha256,artifact.size_bytes)):
        raise ValueError('parameter segment substitutes actual original Native receipt bytes')


def _check_native_receipt(definition,completion,receipt):
    key = sha256((definition.parent_contact.task_id+':'+definition.subwork_id).encode()).hexdigest()
    task = 'native-subwork.'+key
    attempt = definition.parent_contact.run_id+'.'+task+'.attempt-001'
    if (receipt.run_id,receipt.task_id,receipt.attempt_id,receipt.receipt_id) != (definition.parent_contact.run_id,task,attempt,'receipt.'+attempt):
        raise ValueError('parameter native receipt changes exact run/task/attempt parent')
    if receipt.implementation_commit != definition.parent_contact.implementation_commit:
        raise ValueError('parameter native receipt changes producing commit')
    outputs = tuple(a for a in receipt.output_logical_artifacts if a.payload_schema == NativeSubworkCompletion.SCHEMA)
    physical = tuple(p for p in receipt.output_materializations if outputs and p.logical_artifact_id == outputs[0].logical_artifact_id)
    if (len(outputs) != 1 or outputs[0].content_sha256 != completion.fingerprint()
            or len(physical) != 1 or (physical[0].physical_sha256,physical[0].size_bytes) != (completion.fingerprint(),len(completion.canonical_bytes()))):
        raise ValueError('parameter native receipt changes canonical completion bytes')


@dataclass(frozen=True, slots=True)
class CompletedParameterSegment(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-history/completed-segment'
    arrays: MatrixArrayChunk
    checkpoint: MatrixParameterSegmentCheckpoint
    definition: NativeSubworkDefinition
    completion: NativeSubworkCompletion
    receipt: CanonicalTaskReceipt

    def __post_init__(self):
        _check_native_receipt(self.definition,self.completion,self.receipt)
        if (self.checkpoint.science_arrays != self.arrays or self.checkpoint.definition != self.definition.identity or self.completion.definition != self.definition.identity
                or self.completion.operational_status is not OperationalStatus.SUCCEEDED or self.receipt.operational_status is not OperationalStatus.SUCCEEDED
                or self.completion.output_ids != ('arrays','checkpoint','terminal') or self.completion.omitted_output_ids
                or self.completion.unknown_streams or set((*self.completion.consumed_streams,*self.completion.unconsumed_streams)) != set(self.definition.streams)
                or self.receipt.implementation_commit != self.definition.parent_contact.implementation_commit
                or not set(self.definition.input_materialization_ids) <= set(self.receipt.input_materialization_ids)):
            raise ValueError('parameter segment requires completed exact native custody')
        _receipt_array(self.receipt,self.arrays.array_artifact)
        _receipt_array(self.receipt,self.checkpoint.terminal_arrays.array_artifact)
        checkpoint = tuple(a for a in self.receipt.output_logical_artifacts if a.payload_schema == self.checkpoint.SCHEMA)
        physical = tuple(p for p in self.receipt.output_materializations if checkpoint and p.logical_artifact_id == checkpoint[0].logical_artifact_id)
        if (len(checkpoint) != 1 or checkpoint[0].content_sha256 != self.checkpoint.fingerprint()
                or len(physical) != 1 or (physical[0].physical_sha256,physical[0].size_bytes) !=
                    (self.checkpoint.fingerprint(),len(self.checkpoint.canonical_bytes()))):
            raise ValueError('parameter segment substitutes actual canonical checkpoint publication')

    def validate_source(self,bound,previous):
        self.checkpoint.validate_source(bound)
        c,s = bound.coordinate,bound.source
        if self.checkpoint.previous != (None if previous is None else identity(previous.checkpoint)):
            raise ValueError('parameter segment changes actual previous completed checkpoint')
        expected = segment_intervals(c,self.checkpoint.start,self.checkpoint.stop)
        expected_sources = {identity(s),s.allocation,s.coordinate,s.provenance}
        if previous is not None:
            expected_sources.add(identity(previous.checkpoint))
        if ({i.name:(i.start,i.stop) for i in self.arrays.intervals} != expected
                or self.arrays.producers != tuple(sorted((identity(s),coordinate_identity(c)),key=lambda i:i.object_id))
                or set(self.definition.sources) != expected_sources or self.definition.operation_id != OPERATION_ID
                or self.definition.code_sources_sha256 != bound.provenance.code_sources_sha256
                or self.definition.dependency_lock_sha256 != bound.provenance.dependency_lock_sha256
                or self.definition.streams != tuple(sorted((bound.root.stream_identity(t) for t in bound.root.streams),key=lambda i:i.object_id))):
            raise ValueError('parameter segment changes full owned science/physical source/streams')
        consumed = tuple(sorted((bound.root.stream_identity(t) for t in bound.root.streams
            if (t.purpose.startswith('preparation') and self.checkpoint.start < c.ramp_ticks)
            or (t.purpose.startswith('autonomous') and self.checkpoint.stop > c.ramp_ticks)),key=lambda i:i.object_id))
        if self.completion.consumed_streams != consumed:
            raise ValueError('parameter segment changes actual consumed stream census')


@dataclass(frozen=True, slots=True)
class MatrixParameterHistoryCarrier(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-history/carrier-completion'
    carrier_id: str
    source: ObjectIdentity
    segment_definitions: tuple[ObjectIdentity, ...]
    completed_primary_steps: int
    completed_fine_steps: int


@dataclass(frozen=True, slots=True)
class CompletedParameterCarrier(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-history/completed-carrier'
    record: MatrixParameterHistoryCarrier
    definition: NativeSubworkDefinition
    completion: NativeSubworkCompletion
    receipt: CanonicalTaskReceipt

    def __post_init__(self):
        _check_native_receipt(self.definition,self.completion,self.receipt)
        if (self.completion.definition != self.definition.identity or self.completion.operational_status is not OperationalStatus.SUCCEEDED
                or self.receipt.operational_status is not OperationalStatus.SUCCEEDED
                or self.completion.output_ids != ('completion',) or self.completion.omitted_output_ids
                or self.completion.consumed_streams or self.completion.unknown_streams
                or self.completion.unconsumed_streams != self.definition.streams):
            raise ValueError('parameter history carrier is not completed no-draw custody')
        logical = tuple(a for a in self.receipt.output_logical_artifacts if a.payload_schema == self.record.SCHEMA)
        physical = tuple(a for a in self.receipt.output_materializations if logical and a.logical_artifact_id == logical[0].logical_artifact_id)
        if (len(logical) != 1 or logical[0].content_sha256 != self.record.fingerprint()
                or len(physical) != 1 or (physical[0].physical_sha256,physical[0].size_bytes) != (self.record.fingerprint(),len(self.record.canonical_bytes()))):
            raise ValueError('parameter carrier completion changes exact retained summary bytes')


@dataclass(frozen=True, slots=True)
class MatrixParameterChunkedHistory(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-history/chunked-product'
    history_id: str
    source: ObjectIdentity
    root_id: str
    independent_group_id: str
    clock_id: str
    arrays: ChunkedMatrixArrays
    container: ArtifactIdentity
    segments: tuple[CompletedParameterSegment, ...]
    carrier: CompletedParameterCarrier

    def validate_source(self,bound):
        s,c = bound.source,bound.coordinate
        if (self.source != identity(s) or self.root_id != bound.root_id or self.independent_group_id != bound.root.root.independent_group_id
                or self.clock_id != c.clock_id or self.arrays.source != identity(s) or self.arrays.allocation != s.compact.allocation
                or tuple((m.name,m.dtype,m.shape) for m in self.arrays.members) != tuple((name,dtype,shape) for name,(dtype,shape) in chunked_members(bound).items())
                or tuple((v.checkpoint.start,v.checkpoint.stop) for v in self.segments) != segment_plan(bound)
                or self.arrays.chunks != tuple(chunk for v in self.segments for chunk in (v.arrays,v.checkpoint.terminal_arrays))
                or self.carrier.record.source != identity(s) or self.carrier.record.segment_definitions != tuple(v.definition.identity for v in self.segments)
                or (self.carrier.record.completed_primary_steps,self.carrier.record.completed_fine_steps) != (c.total_ticks,2*c.total_ticks)
                or set(self.carrier.definition.sources) != {identity(s),s.allocation,s.coordinate,s.provenance}
                or self.carrier.definition.operation_id != 'matrix-parameter-history.no-rng-carrier-v1'
                or any(v.definition.parent_contact != self.carrier.definition.parent_contact for v in self.segments)):
            raise ValueError('chunked history drops complete scientific root/group/clock/segment denominator')
        previous = None
        for segment in self.segments:
            segment.validate_source(bound,previous);previous = segment


def chunked_members(bound):
    members = expected_members(bound.coordinate)
    for name in ('terminal_fine_momenta','terminal_fine_positions','terminal_primary_momenta','terminal_primary_positions'):
        members[name] = '<c16',(2*len(segment_plan(bound)),3,4,4)
    return dict(sorted(members.items()))


@dataclass(frozen=True, slots=True)
class MatrixParameterChunkedAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-history/chunked-assessment'
    assessment_id: str
    source: ObjectIdentity
    history: ObjectIdentity
    numerical_design: ObjectIdentity
    controls: tuple[MatrixParameterHistoryControl, ...]
    numerical_pass: bool
    standing: str = 'FINITE_DT_EQUATION_CONFORMANCE_NO_FUNCTIONAL_NUMERICAL_ADEQUACY'

    def __post_init__(self):
        if (type(self.numerical_pass) is not bool or tuple(c.control_id for c in self.controls) != METHODS
                or self.numerical_pass != all(c.disposition == 'SATISFIED' for c in self.controls)
                or self.standing != 'FINITE_DT_EQUATION_CONFORMANCE_NO_FUNCTIONAL_NUMERICAL_ADEQUACY'):
            raise ValueError('chunked assessment changes control denominator or implies functional adequacy')
