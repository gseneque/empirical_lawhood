# SPDX-License-Identifier: MPL-2.0
"""Source-only input lineage after the completed E3 boundary."""
from dataclasses import dataclass, replace
from typing import ClassVar

from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from .known_inputs import MatrixProgrammeInputCommitments, MatrixProgrammePublishedInput
from .source_continuation import (
    MatrixProgrammeSourceContinuationSpecification, MatrixProgrammeOutputContinuationSpecification,
    validate_continued_inputs,
)


@dataclass(frozen=True, slots=True)
class MatrixCompletedE3InputSource(CanonicalRecord):
    """Keep original E3/TRAIN input provenance separate from future production.

    This source proof carries no execution, reveal or completion authority.
    The programme owner separately authenticates the completed phase frontier.
    """
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-programme/completed-e3-input-source'
    record_id: str
    continuation_request: ObjectIdentity
    predecessor_inputs: MatrixProgrammePublishedInput
    original_provenance: ObjectIdentity
    target_provenance: ObjectIdentity

    def __post_init__(self):
        validate_stable_id(self.record_id)
        for value, kinds in ((self.continuation_request, (MatrixProgrammeSourceContinuationSpecification,
                MatrixProgrammeOutputContinuationSpecification)),
                (self.original_provenance, (NumericalProducingProvenance,)),
                (self.target_provenance, (NumericalProducingProvenance,))):
            if type(value) is not ObjectIdentity or (value.object_schema, value.object_version) not in {
                    (kind.SCHEMA, kind.VERSION) for kind in kinds}:
                raise TypeError('completed E3 source requires exact source and continuation identities')
            value.__post_init__()
        if type(self.predecessor_inputs) is not MatrixProgrammePublishedInput:
            raise TypeError('completed E3 source requires its original input publication')
        self.predecessor_inputs.__post_init__()
        self.predecessor_inputs.require_kind(MatrixProgrammeInputCommitments)
        if self.original_provenance == self.target_provenance:
            raise ValueError('completed E3 source requires a separate future producing source')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)

    @property
    def artifact(self):
        return ArtifactIdentity(self.record_id, 'completed-e3-input-source', self.SCHEMA,
            self.fingerprint(), 'application/json', len(self.canonical_bytes()))


def completed_source_files(commitments):
    return tuple(row for row in commitments.support_files if row[0].payload_schema == MatrixCompletedE3InputSource.SCHEMA)


def validate_completed_inputs(original, continued, source):
    """Allow only the explicit source handoff beside unchanged original support."""
    if type(source) is not MatrixCompletedE3InputSource:
        raise TypeError('completed E3 inputs require the exact typed original source')
    source.__post_init__()
    source.predecessor_inputs.require_record(original.commitments,
        ObjectIdentity.from_record(original.commitments.record_id, original.commitments))
    rows = completed_source_files(continued.commitments)
    if (completed_source_files(original.commitments) or len(rows) != 1 or rows[0][0] != source.artifact
            or source.original_provenance != original.producing_provenance.identity
            or source.target_provenance != continued.producing_provenance.identity):
        raise PermissionError('completed E3 inputs change their original or future source lineage')
    reduced = replace(continued, commitments=replace(continued.commitments,
        support_files=tuple(row for row in continued.commitments.support_files if row != rows[0])))
    validate_continued_inputs(original, reduced)
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_retained_execution import (
        require_numerical_source_continuity, source_binding,
    )
    require_numerical_source_continuity(source_binding(original.producing_provenance),
        source_binding(continued.producing_provenance))
