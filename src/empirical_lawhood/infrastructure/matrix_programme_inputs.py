# SPDX-License-Identifier: MPL-2.0
"""Bounded ordinary custody for the programme's original known inputs."""
from contextlib import contextmanager
from contextvars import ContextVar
from empirical_lawhood.adapters.methods.matrix_factor_confirmation.records import E1AllocationReservation
from empirical_lawhood.adapters.methods.matrix_factor_response.eligibility import MatrixFactorExposureCensus
from empirical_lawhood.adapters.methods.matrix_parameter_factor.records import MatrixParameterScalarDefinition
from empirical_lawhood.adapters.methods.matrix_experimental_programme.e6_transport_records import MatrixE6EmpiricalTransportPolicy
from empirical_lawhood.adapters.methods.matrix_researcher_programme.known_inputs import MatrixProgrammeInputCommitments, MatrixProgrammePublishedInput
from empirical_lawhood.adapters.methods.matrix_researcher_programme.input_records import (
    ResolvedMatrixProgrammeInputs, ResolvedMatrixProgrammePhaseInputs, validate_programme_input_records,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as scheduled
from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import ScheduledExposureAudit, authenticate_publication
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_selection import ScheduledResponseSelection
from empirical_lawhood.infrastructure.publication_metadata import read_published_canonical_record
from empirical_lawhood.kernel.decoding import decimal_context_key
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.time import AvailabilitySpec

_input_records = ContextVar('matrix_programme_input_records', default=None)


@contextmanager
def _programme_input_custody(writer):
    """Borrow stock bounded facts with complete current byte and access guards."""
    from empirical_lawhood.infrastructure.publication_metadata import supports_closed_publication_access
    if not supports_closed_publication_access(writer):
        with writer.verification_scope() as active:
            yield active
        return
    with writer.read_context() as active:
        yield active


@contextmanager
def _input_record_scope(maximum_bytes):
    """Bound pure decoding reuse to nested calls inside one live input read.

    Every caller still authenticates its own complete publication census and
    source budget. This memo contains no file or access acceptance decision.
    """
    previous = _input_records.get()
    if previous is not None:
        yield previous
        return
    memo = {'records': {}, 'validated': {}, 'bytes': 0, 'maximum_bytes': maximum_bytes}
    token = _input_records.set(memo)
    try:
        from empirical_lawhood.adapters.methods.matrix_researcher_programme.source_continuation import source_rebinding_scope
        from empirical_lawhood.kernel.decoded_record_store import decoded_record_scope
        with decoded_record_scope(), source_rebinding_scope(maximum_bytes):
            yield memo
    finally:
        _input_records.reset(token)


def _record_identity(record, reference):
    if type(record) is AvailabilitySpec:
        return ObjectIdentity.from_record(reference.object_id, record)
    if type(record) is MatrixFactorExposureCensus:
        return ObjectIdentity.from_record(record.census_id, record)
    if type(record) is MatrixParameterScalarDefinition:
        return ObjectIdentity.from_record(record.definition_id, record)
    if type(record) is NumericalProducingProvenance:
        return record.identity
    return scheduled.identity(record)



@contextmanager
def authenticated_programme_inputs(*, writer, commitment, maximum_source_bytes):
    """Read each actual original once, then independently join the whole census.

    The budget is the caller's selected boundary resource limit. All source,
    execution and outcome-access authorities remain at their ordinary owners.
    """
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.scientific_design import MatrixProgrammeScientificDesign
    if type(commitment) is not MatrixProgrammePublishedInput:
        raise TypeError("programme input authentication requires the actual original commitment publication")
    commitment.__post_init__()
    commitment.require_kind(MatrixProgrammeInputCommitments)
    if type(maximum_source_bytes) is not int or maximum_source_bytes < 1:
        raise ValueError("programme input authentication requires an explicit positive source byte budget")
    with _input_record_scope(maximum_source_bytes) as shared, _programme_input_custody(writer) as active:
        memo, charged, consumed = {}, {}, 0
        decimal_context = decimal_context_key()

        def charge(publication):
            nonlocal consumed
            path = publication.materialization.relative_path
            if path in charged:
                if charged[path] != publication:
                    raise PermissionError("programme inputs alias different publications through one physical path")
                return
            charged[path] = publication
            consumed += publication.materialization.size_bytes
            if consumed > maximum_source_bytes:
                raise ValueError("complete programme input reads exceed the selected source byte budget")

        def read(selected, kind):
            selected.__post_init__()
            selected.require_kind(kind)
            key = selected.record
            if key in memo:
                previous, record = memo[key]
                if previous != selected or type(record) is not kind:
                    raise PermissionError("programme input repeats an original with different custody or type")
                return record
            charge(selected.publication)
            shared_key = selected, kind, decimal_context
            size = selected.publication.materialization.size_bytes
            record = read_published_canonical_record(active, selected.publication, kind, maximum_bytes=size)
            selected.require_record(record, _record_identity(record, selected.record))
            retained = shared_key in shared['records']
            if record._is_cacheable() and (retained or shared['bytes'] + size <= shared['maximum_bytes']):
                shared['records'][shared_key] = record
                if not retained:
                    shared['bytes'] += size
            memo[key] = selected, record
            return record

        original = read(commitment, MatrixProgrammeInputCommitments)
        design = read(original.scientific_design, MatrixProgrammeScientificDesign)
        census = read(original.exposure_census, MatrixFactorExposureCensus)
        audit = read(original.exposure_audit, ScheduledExposureAudit)
        provenance = read(original.producing_provenance, NumericalProducingProvenance)
        scalars = tuple(read(selected, MatrixParameterScalarDefinition) for selected in original.scalar_definitions)
        phases = []
        for selected in original.phases:
            reservation = read(selected.reservation,
                E1AllocationReservation if selected.role == "e1" else scheduled.ScheduledReservation)
            native = None if selected.native_specification is None else read(selected.native_specification, scheduled.ScheduledSpecification)
            responses = None if selected.responses is None else read(selected.responses, ScheduledResponseSelection)
            phases.append(ResolvedMatrixProgrammePhaseInputs(selected.role, reservation, native, responses))
        availability = read(original.availability, AvailabilitySpec)
        policy = read(original.e6_policy, MatrixE6EmpiricalTransportPolicy)
        result = ResolvedMatrixProgrammeInputs(original, design, census, audit, provenance, scalars,
            tuple(phases), availability, policy)
        # Reuse only a pure join over the identical immutable decoded objects.
        # Publication/body checks above and the complete child checks below are
        # fresh even when this nested caller uses the same scientific operands.
        operands = tuple(record for _, record in memo.values())
        validated_key = commitment, decimal_context
        prior = shared['validated'].get(validated_key)
        if prior is None or len(prior) != len(operands) or any(a is not b for a, b in zip(prior, operands, strict=True)):
            validate_programme_input_records(result)
            cached_ids = {id(record) for record in shared['records'].values()}
            if all(id(record) in cached_ids for record in operands):
                shared['validated'][validated_key] = operands
        # Child reservation/selection and template publications retain their
        # normal manifest/commit-marker authentication. Deduplicate only here.
        child_publications = {}
        def child(publication):
            path = publication.materialization.relative_path
            if child_publications.setdefault(path, publication) != publication:
                raise PermissionError("programme input aliases different actual child publications")
        for phase in result.phases:
            child(phase.reservation.publication)
            if phase.native_specification is not None:
                child(phase.native_specification.publication)
            if phase.responses is not None:
                for publication in phase.responses.template_publications:
                    child(publication)
        for publication in result.exposure_audit.prior_corpus:
            child(publication)
        for _, publication in original.support_files:
            child(publication)
        for publication in child_publications.values():
            charge(publication)
            authenticate_publication(active, publication)

        @contextmanager
        def checked_inputs():
            from .publication_metadata import checkpoint_input_publications

            # Input checks cover their complete atomic publications. The
            # surrounding read/publication owners retain the full union.
            publications = tuple(charged.values())
            checkpoint_input_publications(active, publications)
            try:
                yield result
            finally:
                checkpoint_input_publications(active, publications)

        from empirical_lawhood.adapters.methods.matrix_researcher_programme.retained_training_continuation import retained_source_files
        from empirical_lawhood.adapters.methods.matrix_researcher_programme.completed_source import completed_source_files
        if completed_source_files(original):
            from empirical_lawhood.infrastructure.matrix_completed_source import original_e3_programme_inputs
            if consumed >= maximum_source_bytes:
                raise ValueError('completed E3 original inputs exceed the selected source byte budget')
            with original_e3_programme_inputs(writer=active, inputs=result,
                    maximum_source_bytes=maximum_source_bytes - consumed), checked_inputs():
                yield result
        elif retained_source_files(original):
            from empirical_lawhood.infrastructure.matrix_retained_training import authenticated_retained_training_source
            if consumed >= maximum_source_bytes:
                raise ValueError('retained TRAIN original inputs exceed the selected source byte budget')
            with authenticated_retained_training_source(writer=active, inputs=result,
                    maximum_source_bytes=maximum_source_bytes - consumed), checked_inputs():
                yield result
        else:
            with checked_inputs():
                yield result


def authenticate_programme_inputs(*, writer, commitment, maximum_source_bytes):
    """Authenticate one bounded read, with its final guard before returning.

    Assemblers that publish dependent metadata use authenticated_programme_inputs
    to keep the same immutable input snapshots alive through their final return.
    """
    with authenticated_programme_inputs(writer=writer, commitment=commitment,
            maximum_source_bytes=maximum_source_bytes) as result:
        return result
