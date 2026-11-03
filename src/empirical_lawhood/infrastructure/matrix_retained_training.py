# SPDX-License-Identifier: MPL-2.0
"""Bounded authentication of the explicit completed-TRAIN source handoff."""
from contextlib import ExitStack, contextmanager
from contextvars import ContextVar

from empirical_lawhood.adapters.methods.matrix_researcher_programme.retained_training_continuation import (
    retained_source_files, retained_source_types, validate_retained_inputs,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import authenticate_publication
from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.kernel.decoding import decode_canonical_bytes

_reading_original = ContextVar('matrix_retained_training_original', default=False)


def read_retained_training_source(writer, commitments):
    rows = retained_source_files(commitments)
    if len(rows) != 1:
        raise PermissionError('continued inputs require exactly one original retained TRAIN source file')
    artifact, publication = rows[0]
    authenticate_publication(writer, publication)
    raw = read_bounded_bytes(writer.root.resolve(publication.materialization.relative_path, for_write=False),
        maximum_bytes=artifact.size_bytes)
    kind, = (kind for kind in retained_source_types() if kind.SCHEMA == artifact.payload_schema)
    value = decode_canonical_bytes(raw, kind, maximum_bytes=artifact.size_bytes)
    if value.canonical_bytes() != raw or value.artifact != artifact:
        raise PermissionError('retained TRAIN source changes its exact original canonical bytes')
    return value


@contextmanager
def authenticated_retained_training_source(*, writer, inputs, maximum_source_bytes):
    """Hold the original source-only proof through each dependent consumer."""
    from empirical_lawhood.infrastructure.matrix_programme_inputs import authenticated_programme_inputs
    if _reading_original.get():
        raise PermissionError('retained TRAIN source cannot chain or recurse through another retained TRAIN source')
    retained = read_retained_training_source(writer, inputs.commitments)
    with ExitStack() as lifetime:
        token = _reading_original.set(True)
        try:
            original = lifetime.enter_context(authenticated_programme_inputs(writer=writer,
                commitment=retained.input_commitments, maximum_source_bytes=maximum_source_bytes))
        finally:
            _reading_original.reset(token)
        validate_retained_inputs(original, inputs, retained)
        yield retained, original
