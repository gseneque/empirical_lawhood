# SPDX-License-Identifier: MPL-2.0
"""Live bounded input custody for a source change after completed E3."""
from contextlib import ExitStack, contextmanager
from contextvars import ContextVar

from empirical_lawhood.adapters.methods.matrix_researcher_programme.completed_source import (
    MatrixCompletedE3InputSource, completed_source_files, validate_completed_inputs,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import authenticate_publication
from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.kernel.decoding import decode_canonical_bytes

_reading_original = ContextVar('matrix_completed_e3_original', default=False)


def read_completed_source(writer, commitments):
    rows = completed_source_files(commitments)
    if len(rows) != 1:
        raise PermissionError('completed E3 inputs require exactly one original source file')
    artifact, publication = rows[0]
    authenticate_publication(writer, publication)
    raw = read_bounded_bytes(writer.root.resolve(publication.materialization.relative_path, for_write=False),
        maximum_bytes=artifact.size_bytes)
    source = decode_canonical_bytes(raw, MatrixCompletedE3InputSource, maximum_bytes=artifact.size_bytes)
    if source.artifact != artifact or source.canonical_bytes() != raw:
        raise PermissionError('completed E3 source changes its exact canonical bytes')
    return source


def original_e3_commitment(writer, inputs, commitment):
    """Return the exact published input handle, never a body-only substitute."""
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    commitment.require_record(inputs.commitments,
        ObjectIdentity.from_record(inputs.commitments.record_id, inputs.commitments))
    if completed_source_files(inputs.commitments):
        return read_completed_source(writer, inputs.commitments).predecessor_inputs
    return commitment


@contextmanager
def original_e3_programme_inputs(*, writer, inputs, maximum_source_bytes):
    """Resolve original E3 inputs without relabeling their TRAIN or model source."""
    if not completed_source_files(inputs.commitments):
        yield inputs
        return
    if _reading_original.get():
        raise PermissionError('completed E3 input source cannot chain or recurse')
    from empirical_lawhood.infrastructure.matrix_programme_inputs import authenticated_programme_inputs
    source = read_completed_source(writer, inputs.commitments)
    remaining = maximum_source_bytes - source.artifact.size_bytes
    if remaining <= 0:
        raise ValueError('completed E3 original inputs exceed the selected source byte budget')
    with ExitStack() as lifetime:
        token = _reading_original.set(True)
        try:
            original = lifetime.enter_context(authenticated_programme_inputs(writer=writer,
                commitment=source.predecessor_inputs, maximum_source_bytes=remaining))
        finally:
            _reading_original.reset(token)
        validate_completed_inputs(original, inputs, source)
        yield original
