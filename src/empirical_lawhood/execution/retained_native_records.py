# SPDX-License-Identifier: MPL-2.0
"""Typed metadata from the complete-output port, with observed byte accounting.

The port owns receipt, current access and closing custody checks. This owner
consumes and closes it, then strictly decodes the actual received population.
Metadata must fit the selected process memory; no unrelated fixed byte ceiling
is substituted for an operator resource policy or a scientific requirement.
"""

from io import BytesIO
from typing import TypeVar

from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.execution.progress import progress_step


Record = TypeVar("Record", bound=CanonicalRecord)


def decode_completed_record(progress, definition, output_id: str,
                            record_type: type[Record]) -> tuple[Record, bytes]:
    """Read one receipted original record and return its exact canonical bytes."""
    chunks = progress.iter_completed_output(definition, output_id)
    try:
        with BytesIO() as buffer, progress_step(
                "native.retained-record-read", unit="bytes", detail=output_id) as step:
            for chunk in chunks:
                if type(chunk) is not bytes:
                    raise TypeError("completed native record chunks must be exact bytes")
                buffer.write(chunk)
                step.advance(len(chunk))
            raw = buffer.getvalue()
    finally:
        close = getattr(chunks, "close", None)
        if close is not None:
            close()
    with progress_step("native.retained-record-decode", total=len(raw), unit="bytes",
                       detail=output_id) as step:
        record = decode_canonical_bytes(raw, record_type, maximum_bytes=len(raw))
        step.advance(len(raw))
    return record, raw
