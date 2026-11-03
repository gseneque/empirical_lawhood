# SPDX-License-Identifier: MPL-2.0
"""Compact report successor retaining complete streamed per-step controls."""

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_array_chunks import ChunkedMatrixArrays, FRAMED_ARRAY_SCHEMA, FRAMED_ARRAY_MEDIA, framed_size
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_decimal, validate_stable_id

from .records import METHODS, MatrixParameterAllocation, MatrixParameterNumericalDesign
from .chunked_records import MatrixParameterChunkedSource, MatrixParameterChunkedHistory


@dataclass(frozen=True, slots=True)
class MatrixParameterChunkControlSummary(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-history/chunk-control-summary'
    control_id: str
    error: Decimal
    tolerance: Decimal
    disposition: str
    denominator_steps: int
    denominator_real_coordinates: int
    violation_count: int
    worst_step: int

    def __post_init__(self):
        for value in (self.error,self.tolerance):
            validate_decimal(value,field_name='complete control summary',minimum=Decimal(0))
        if (self.control_id not in METHODS or type(self.denominator_steps) is not int or self.denominator_steps < 1
                or self.denominator_real_coordinates not in (96,192) or type(self.violation_count) is not int
                or not 0 <= self.violation_count <= self.denominator_steps or type(self.worst_step) is not int
                or not 1 <= self.worst_step <= self.denominator_steps
                or self.disposition != ('VIOLATED' if self.violation_count else 'SATISFIED')
                or bool(self.violation_count) != (self.error > self.tolerance)):
            raise ValueError('compact control summary changes complete count/max/negative outcome')


@dataclass(frozen=True, slots=True)
class MatrixParameterChunkedAssessmentReport(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-history/chunked-assessment-summary'
    assessment_id: str
    source: ObjectIdentity
    history: ObjectIdentity
    numerical_design: ObjectIdentity
    allocation: ObjectIdentity
    controls: tuple[MatrixParameterChunkControlSummary, ...]
    control_arrays: ChunkedMatrixArrays
    control_container: ArtifactIdentity
    numerical_pass: bool
    standing: str = 'FINITE_DT_EQUATION_CONFORMANCE_NO_FUNCTIONAL_NUMERICAL_ADEQUACY'

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        expected = tuple(sorted((c.control_id,'<f8',(c.denominator_steps,),True) for c in self.controls))
        if (self.source.object_schema != MatrixParameterChunkedSource.SCHEMA
                or self.history.object_schema != MatrixParameterChunkedHistory.SCHEMA
                or self.numerical_design.object_schema != MatrixParameterNumericalDesign.SCHEMA
                or self.allocation.object_schema != MatrixParameterAllocation.SCHEMA
                or type(self.numerical_pass) is not bool or tuple(c.control_id for c in self.controls) != METHODS
                or self.numerical_pass != all(c.disposition == 'SATISFIED' for c in self.controls)
                or self.standing != 'FINITE_DT_EQUATION_CONFORMANCE_NO_FUNCTIONAL_NUMERICAL_ADEQUACY'
                or self.control_arrays.source != self.source or self.control_arrays.allocation != self.allocation
                or self.control_arrays.producers != tuple(sorted((self.history,self.numerical_design),key=lambda i:i.object_id))
                or tuple((m.name,m.dtype,m.shape,m.finite_required) for m in self.control_arrays.members) != expected
                or (self.control_container.payload_schema,self.control_container.media_type,self.control_container.size_bytes) !=
                    (FRAMED_ARRAY_SCHEMA,FRAMED_ARRAY_MEDIA,framed_size(self.control_arrays))):
            raise ValueError('compact report loses complete controls or implies functional adequacy')
