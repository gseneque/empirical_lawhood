# SPDX-License-Identifier: MPL-2.0
"""Read the exact published operands a programme operation actually consumes.

The complete scientific join belongs to preparation and new child compilation.
Opening an existing programme does not reconstruct unused historical phases.
Every consumed operand still has its original publication, byte and type checks.
"""
from contextlib import contextmanager
from dataclasses import dataclass, field

from .matrix_programme_inputs import (
    _input_record_scope, _programme_input_custody, _record_identity,
)


@dataclass(frozen=True)
class RecordedMatrixProgrammeInputs:
    commitments: object
    _read: object = field(repr=False)

    @property
    def scientific_design(self):
        from empirical_lawhood.adapters.methods.matrix_researcher_programme.scientific_design import MatrixProgrammeScientificDesign
        return self._read(self.commitments.scientific_design, MatrixProgrammeScientificDesign)

    @property
    def producing_provenance(self):
        from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
        return self._read(self.commitments.producing_provenance, NumericalProducingProvenance)

    @property
    def exposure_census(self):
        from empirical_lawhood.adapters.methods.matrix_factor_response.eligibility import MatrixFactorExposureCensus
        return self._read(self.commitments.exposure_census, MatrixFactorExposureCensus)

    @property
    def exposure_audit(self):
        from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import ScheduledExposureAudit
        return self._read(self.commitments.exposure_audit, ScheduledExposureAudit)

    @property
    def scalar_definitions(self):
        from empirical_lawhood.adapters.methods.matrix_parameter_factor.records import MatrixParameterScalarDefinition
        return tuple(self._read(row, MatrixParameterScalarDefinition) for row in self.commitments.scalar_definitions)

    @property
    def availability(self):
        from empirical_lawhood.kernel.time import AvailabilitySpec
        return self._read(self.commitments.availability, AvailabilitySpec)

    @property
    def e6_policy(self):
        from empirical_lawhood.adapters.methods.matrix_experimental_programme.e6_transport_records import MatrixE6EmpiricalTransportPolicy
        return self._read(self.commitments.e6_policy, MatrixE6EmpiricalTransportPolicy)

    def phase(self, role):
        from empirical_lawhood.adapters.methods.matrix_factor_confirmation.records import E1AllocationReservation
        from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledReservation, ScheduledSpecification
        from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_selection import ScheduledResponseSelection
        from empirical_lawhood.adapters.methods.matrix_researcher_programme.input_records import ResolvedMatrixProgrammePhaseInputs
        row = self.commitments.phase(role)
        return ResolvedMatrixProgrammePhaseInputs(role,
            self._read(row.reservation, E1AllocationReservation if role == 'e1' else ScheduledReservation),
            None if row.native_specification is None else self._read(row.native_specification, ScheduledSpecification),
            None if row.responses is None else self._read(row.responses, ScheduledResponseSelection))

    @property
    def phases(self):
        return tuple(self.phase(row.role) for row in self.commitments.phases)


@contextmanager
def recorded_programme_inputs(*, writer, commitment, maximum_source_bytes):
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.known_inputs import (
        MatrixProgrammeInputCommitments, MatrixProgrammePublishedInput,
    )
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import authenticate_publication
    from empirical_lawhood.kernel.decoding import decimal_context_key
    from .publication_metadata import read_published_canonical_record

    if type(commitment) is not MatrixProgrammePublishedInput or type(maximum_source_bytes) is not int or maximum_source_bytes < 1:
        raise TypeError('recorded programme inputs require exact published handles and a positive source budget')
    with _input_record_scope(maximum_source_bytes) as shared, _programme_input_custody(writer) as active:
        charged, memo, consumed, live = {}, {}, 0, True

        def read(selected, kind):
            nonlocal consumed
            if not live:
                raise PermissionError('recorded programme operands escaped their authenticated operation')
            selected.__post_init__()
            selected.require_kind(kind)
            path = selected.publication.materialization.relative_path
            if path in charged and charged[path] != selected.publication:
                raise PermissionError('recorded programme aliases different publications')
            if path not in charged:
                consumed += selected.publication.materialization.size_bytes
                if consumed > maximum_source_bytes:
                    raise ValueError('recorded programme operands exceed their source budget')
                charged[path] = selected.publication
            # Permission is not memoized. These inputs are published metadata;
            # protected scientific operands keep their separate access owners.
            key = selected, kind, decimal_context_key()
            value = memo.get(key)
            if value is None:
                size = selected.publication.materialization.size_bytes
                value = read_published_canonical_record(active, selected.publication, kind, maximum_bytes=size)
                selected.require_record(value, _record_identity(value, selected.record))
                retained = key in shared['records']
                if value._is_cacheable() and (retained or shared['bytes'] + size <= shared['maximum_bytes']):
                    shared['records'][key] = value
                    if not retained:
                        shared['bytes'] += size
            else:
                authenticate_publication(active, selected.publication)
            memo[key] = value
            return value

        result = RecordedMatrixProgrammeInputs(read(commitment, MatrixProgrammeInputCommitments), read)
        try:
            yield result
        finally:
            live = False
            from .publication_metadata import checkpoint_input_publications
            checkpoint_input_publications(active, tuple(charged.values()))
