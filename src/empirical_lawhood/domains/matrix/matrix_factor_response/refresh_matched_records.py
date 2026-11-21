# SPDX-License-Identifier: MPL-2.0
"""Separate bindings for the three commissioned retained-evidence analyses."""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.domains.matrix.input_contracts import MATRIX_ARRAY_SCHEMA, MAXIMUM_MATRIX_ARRAY_BYTES, MatrixArrayMember
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.identity.references import ArtifactIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_sha256, validate_stable_id

from empirical_lawhood.domains.matrix.matrix_factor_response.refresh_records import MatrixRefreshCaseSource, MatrixRefreshProtocol


MATCHED_PROTOCOL_ID = 'matrix.sci01.matched-accounting.v1'
ANALYSES = ('MATCHED_CELL_REVERSAL_CENSUS', 'SIGNED_ERROR_ALIGNMENT', 'POST_CHECKPOINT_REPRESENTATION')


@dataclass(frozen=True, slots=True)
class MatrixMatchedProtocol(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-sci01/matched-protocol'
    VERSION: ClassVar[str] = '1.0.0'
    original_protocol: MatrixRefreshProtocol
    calculation_completion: ObjectIdentity
    assessment_completion: ObjectIdentity
    public_specification_sha256: str
    protocol_id: str = MATCHED_PROTOCOL_ID
    analyses: tuple[str, ...] = ANALYSES
    evidence_role: str = 'EXPOSED_DEVELOPMENT_NONPROMOTABLE'
    endpoint_sign: str = 'PREDICTED_MINUS_NATIVE'
    representation_sign: str = 'FULL_MINUS_LIFTED_REDUCED'

    def __post_init__(self):
        validate_sha256(self.public_specification_sha256)
        if (type(self.original_protocol) is not MatrixRefreshProtocol
                or any(type(p) is not ObjectIdentity or p.object_schema != 'empirical-lawhood/runtime/retained-analysis-completion'
                       for p in (self.calculation_completion, self.assessment_completion))
                or self.protocol_id != MATCHED_PROTOCOL_ID or self.analyses != ANALYSES
                or self.evidence_role != 'EXPOSED_DEVELOPMENT_NONPROMOTABLE'
                or self.endpoint_sign != 'PREDICTED_MINUS_NATIVE'
                or self.representation_sign != 'FULL_MINUS_LIFTED_REDUCED'):
            raise ValueError('Matched SCI01 changes its exact three analyses, source bindings or signs')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.protocol_id, self)


@dataclass(frozen=True, slots=True)
class MatrixMatchedArrays(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-sci01/matched-arrays'
    VERSION: ClassVar[str] = '1.0.0'
    operand_id: str
    protocol: ObjectIdentity
    original_case: MatrixRefreshCaseSource
    source_arrays: ObjectIdentity
    array_artifact: ArtifactIdentity
    members: tuple[MatrixArrayMember, ...]

    def __post_init__(self):
        validate_stable_id(self.operand_id)
        names = tuple(row.name for row in self.members)
        if (self.protocol.object_schema != MatrixMatchedProtocol.SCHEMA
                or type(self.original_case) is not MatrixRefreshCaseSource
                or self.original_case.original_availability != 'FINITE'
                or self.source_arrays.object_schema != 'empirical-lawhood/matrix-sci01/retained-arrays'
                or not 0 < len(names) <= 256 or names != tuple(sorted(set(names)))
                or any(type(row) is not MatrixArrayMember or not row.finite_required for row in self.members)
                or sum(row.size_bytes for row in self.members) > MAXIMUM_MATRIX_ARRAY_BYTES
                or self.array_artifact.payload_schema != MATRIX_ARRAY_SCHEMA
                or self.array_artifact.media_type != 'application/x-npz'
                or not 0 < self.array_artifact.size_bytes <= MAXIMUM_MATRIX_ARRAY_BYTES):
            raise ValueError('Matched SCI01 loses its bounded arrays or original-case binding')
