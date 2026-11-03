# SPDX-License-Identifier: MPL-2.0
"""Per-root v2 identities binding a separately authenticated shared allocation."""

from dataclasses import dataclass
from hashlib import sha256
from math import prod
from typing import ClassVar

from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history import MatrixParameterCoordinate
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_ou_domain import validate_parameter_ou_domain
from empirical_lawhood.kernel.matrix_inputs import MAXIMUM_MATRIX_ARRAY_BYTES, MATRIX_ARRAY_SCHEMA, MatrixArrayMember
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, canonical_json_bytes, require_sorted_unique_ids, validate_sha256, validate_stable_id
from empirical_lawhood.runtime.artifacts import ArtifactProfile

from .records import (
    EXPOSED, METHODS, MatrixParameterAllocation, MatrixParameterHistoryControl,
    MatrixParameterNativeHistory, MatrixParameterNumericalDesign, MatrixParameterRoot,
    coordinate_identity, expected_members,
)


def identity(record):
    for name in ('source_id', 'config_id', 'allocation_id', 'history_id', 'assessment_id', 'operand_id', 'design_id'):
        if hasattr(record, name):
            return ObjectIdentity.from_record(getattr(record, name), record)
    raise ValueError('compact parameter record has no declared identity')


@dataclass(frozen=True, slots=True)
class MatrixParameterCompactSource(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-history/compact-source'
    VERSION: ClassVar[str] = '2.0.0'
    source_id: str
    allocation: ObjectIdentity
    coordinate: ObjectIdentity
    root: MatrixParameterRoot
    provenance: ObjectIdentity
    numerical_design: MatrixParameterNumericalDesign
    allocation_scope_sha256: str
    requested_roots: int
    requested_groups: int
    numerical_view_ids: tuple[str, str]
    exposure: str = EXPOSED

    def __post_init__(self):
        validate_stable_id(self.source_id)
        validate_sha256(self.allocation_scope_sha256)
        if (self.allocation.object_schema != MatrixParameterAllocation.SCHEMA
                or self.coordinate.object_schema != MatrixParameterCoordinate.SCHEMA
                or self.coordinate != self.root.coordinate
                or self.provenance.object_schema != NumericalProducingProvenance.SCHEMA
                or type(self.numerical_design) is not MatrixParameterNumericalDesign or self.exposure != EXPOSED
                or type(self.requested_roots) is not int or self.requested_roots < 1
                or type(self.requested_groups) is not int or not 1 <= self.requested_groups <= self.requested_roots
                or len(self.numerical_view_ids) != 2 or self.numerical_view_ids != tuple(sorted(set(self.numerical_view_ids)))):
            raise ValueError('compact source changes shared allocation/root/coordinate/provenance')

    @property
    def root_id(self):
        return self.root.root.root_id


@dataclass(frozen=True, slots=True)
class BoundParameterCompactSource:
    """Authenticated in-memory numerical view; never a legacy source record."""
    source: MatrixParameterCompactSource
    allocation: MatrixParameterAllocation
    coordinate: MatrixParameterCoordinate
    provenance: NumericalProducingProvenance

    @property
    def root(self):
        return self.source.root

    @property
    def root_id(self):
        return self.source.root_id

    @property
    def numerical_design(self):
        return self.source.numerical_design


def bind_source(source, allocation, coordinate, provenance, *, new_entry=False):
    if (type(source) is not MatrixParameterCompactSource or type(allocation) is not MatrixParameterAllocation
            or type(coordinate) is not MatrixParameterCoordinate or type(provenance) is not NumericalProducingProvenance
            or source.allocation != identity(allocation) or source.coordinate != coordinate_identity(coordinate)
            or source.provenance != provenance.identity or source.root not in allocation.roots
            or coordinate not in allocation.coordinates or source.root.root.clock_id != coordinate.clock_id
            or source.allocation_scope_sha256 != sha256(canonical_json_bytes(allocation.roots)).hexdigest()
            or source.requested_roots != len(allocation.roots)
            or source.requested_groups != len({r.root.independent_group_id for r in allocation.roots})
            or source.numerical_view_ids != tuple(sorted((coordinate.primary_view.view_id, coordinate.fine_view.view_id)))
            or coordinate.primary_view.rng_algorithm not in ('numpy.pcg64dxsm','numpy-pcg64dxsm')):
        raise ValueError('compact source substitutes authenticated shared allocation/root/coordinate/provenance')
    size = sum(prod(shape) * {'<c16': 16, '<f8': 8, '<i8': 8}[dtype]
               for dtype, shape in expected_members(coordinate).values())
    if size + 11 * 10000 > MAXIMUM_MATRIX_ARRAY_BYTES:
        raise ValueError('compact v2 complete history needs separately selected chunked transport')
    if new_entry:
        validate_parameter_ou_domain(coordinate)
    return BoundParameterCompactSource(source, allocation, coordinate, provenance)


def compact_sources(allocation, provenance, numerical_design, *, namespace):
    validate_stable_id(namespace)
    coordinates = {coordinate_identity(c): c for c in allocation.coordinates}
    scope = sha256(canonical_json_bytes(allocation.roots)).hexdigest()
    groups = len({r.root.independent_group_id for r in allocation.roots})
    selected_allocation, selected_provenance = identity(allocation), provenance.identity
    return tuple(MatrixParameterCompactSource(namespace + '.' + r.root.root_id, selected_allocation,
        r.coordinate, r, selected_provenance, numerical_design, scope, len(allocation.roots), groups,
        tuple(sorted((coordinates[r.coordinate].primary_view.view_id, coordinates[r.coordinate].fine_view.view_id))))
        for r in allocation.roots)


@dataclass(frozen=True, slots=True)
class MatrixParameterCompactArrays(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-history/compact-arrays'
    VERSION: ClassVar[str] = '2.0.0'
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
        validate_stable_id(self.operand_id)
        validate_stable_id(self.root_id)
        require_sorted_unique_ids(self.members, attribute='name', field_name='compact history members')
        require_sorted_unique_ids(self.producers, attribute='object_id', field_name='compact history producers')
        if (self.source.object_schema != MatrixParameterCompactSource.SCHEMA
                or self.allocation.object_schema != MatrixParameterAllocation.SCHEMA
                or self.coordinate.object_schema != MatrixParameterCoordinate.SCHEMA or self.exposure != EXPOSED
                or self.array_artifact.payload_schema != MATRIX_ARRAY_SCHEMA or self.array_artifact.media_type != 'application/x-npz'
                or not self.members or not self.producers or sum(m.size_bytes for m in self.members) > MAXIMUM_MATRIX_ARRAY_BYTES):
            raise ValueError('compact history arrays change source or complete supported transport')

    def validate_source(self, bound):
        s = bound.source
        if (self.source != identity(s) or self.allocation != s.allocation or self.coordinate != s.coordinate
                or self.root_id != s.root_id or {m.name: (m.dtype, m.shape) for m in self.members} != expected_members(bound.coordinate)
                or self.producers != tuple(sorted((identity(s), s.coordinate), key=lambda p: p.object_id))):
            raise ValueError('compact array joins change actual source/shared allocation/complete members')


@dataclass(frozen=True, slots=True)
class MatrixParameterCompactHistory(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-history/compact-product'
    VERSION: ClassVar[str] = '2.0.0'
    history_id: str
    source: ObjectIdentity
    coordinate: ObjectIdentity
    root_id: str
    independent_group_id: str
    clock_id: str
    arrays: MatrixParameterCompactArrays
    native: MatrixParameterNativeHistory
    primary_steps: int
    fine_steps: int
    exposure: str = EXPOSED

    def __post_init__(self):
        for value in (self.history_id,self.root_id,self.independent_group_id,self.clock_id):
            validate_stable_id(value)
        if (self.source.object_schema != MatrixParameterCompactSource.SCHEMA
                or self.coordinate.object_schema != MatrixParameterCoordinate.SCHEMA
                or type(self.arrays) is not MatrixParameterCompactArrays or type(self.native) is not MatrixParameterNativeHistory
                or type(self.primary_steps) is not int or self.primary_steps < 1
                or self.fine_steps != 2*self.primary_steps or self.exposure != EXPOSED):
            raise ValueError('compact history changes complete source/native/paired-step census')

    def validate_source(self, bound):
        s = bound.source
        self.arrays.validate_source(bound)
        if (self.source != identity(s) or self.coordinate != s.coordinate or self.root_id != s.root_id
                or self.independent_group_id != s.root.root.independent_group_id
                or self.clock_id != bound.coordinate.clock_id
                or (self.primary_steps, self.fine_steps) != (bound.coordinate.total_ticks, 2 * bound.coordinate.total_ticks)
                or self.exposure != EXPOSED or self.native.definition.code_sources_sha256 != bound.provenance.code_sources_sha256
                or self.native.definition.dependency_lock_sha256 != bound.provenance.dependency_lock_sha256
                or self.native.definition.operation_id != 'matrix-parameter-native.compact-paired-history-v2'
                or set(self.native.definition.sources) != {identity(s),s.allocation,s.coordinate,s.provenance}
                or self.native.definition.streams != tuple(sorted((s.root.stream_identity(t) for t in s.root.streams), key=lambda t: t.object_id))):
            raise ValueError('compact history substitutes exact native source/clock/group/stream result')
        consumed = tuple(sorted((s.root.stream_identity(t) for t in s.root.streams
            if t.purpose.startswith('preparation') or bound.coordinate.autonomous_ticks),key=lambda t:t.object_id))
        native_arrays = tuple(a for a in self.native.receipt.output_logical_artifacts if a.payload_schema == MATRIX_ARRAY_SCHEMA)
        artifact = self.arrays.array_artifact
        if (self.native.completion.consumed_streams != consumed or len(native_arrays) != 1
                or native_arrays[0].profile is not ArtifactProfile.MATRIX_ARRAY_NPZ
                or native_arrays[0].media_type != artifact.media_type or native_arrays[0].content_sha256 != artifact.sha256):
            raise ValueError('compact history changes actual consumed streams or native array receipt')
        physical = tuple(p for p in self.native.receipt.output_materializations if p.logical_artifact_id == native_arrays[0].logical_artifact_id)
        if len(physical) != 1 or (physical[0].physical_sha256,physical[0].size_bytes) != (artifact.sha256,artifact.size_bytes):
            raise ValueError('compact history changes exact original native physical custody')


@dataclass(frozen=True, slots=True)
class MatrixParameterCompactAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-history/compact-assessment'
    VERSION: ClassVar[str] = '2.0.0'
    assessment_id: str
    source: ObjectIdentity
    history: ObjectIdentity
    numerical_design: ObjectIdentity
    controls: tuple[MatrixParameterHistoryControl, ...]
    numerical_pass: bool
    standing: str = 'FINITE_DT_EQUATION_CONFORMANCE_NO_FUNCTIONAL_NUMERICAL_ADEQUACY'

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        if (self.source.object_schema != MatrixParameterCompactSource.SCHEMA
                or self.history.object_schema != MatrixParameterCompactHistory.SCHEMA
                or self.numerical_design.object_schema != MatrixParameterNumericalDesign.SCHEMA
                or type(self.numerical_pass) is not bool or tuple(c.control_id for c in self.controls) != METHODS
                or self.numerical_pass != all(c.disposition == 'SATISFIED' for c in self.controls)
                or self.standing != 'FINITE_DT_EQUATION_CONFORMANCE_NO_FUNCTIONAL_NUMERICAL_ADEQUACY'):
            raise ValueError('compact history assessment loses controls or implies functional adequacy')
