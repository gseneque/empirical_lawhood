# SPDX-License-Identifier: MPL-2.0
"""Complete retained metadata is bounded by its authenticated actual extent."""

from dataclasses import dataclass
from typing import ClassVar

import pytest

from empirical_lawhood.execution.progress import progress_reporting
from empirical_lawhood.execution.retained_native_records import decode_completed_record
from empirical_lawhood.science.records.serialization import CanonicalRecord


@dataclass(frozen=True)
class Metadata(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/test/retained-native-metadata"
    payload: str

    def __post_init__(self):
        if type(self.payload) is not str:
            raise ValueError("metadata payload must be text")


class CompletedPort:
    def __init__(self, chunks):
        self.chunks, self.closed = chunks, False

    def iter_completed_output(self, definition, output_id):
        assert definition == "original.definition" and output_id == "metadata"
        try:
            yield from self.chunks
        finally:
            self.closed = True


def test_actual_complete_metadata_crosses_former_32_mib_ceiling_with_exact_bytes():
    record = Metadata("x" * (32 * 1024**2 + 1))
    raw = record.canonical_bytes()
    port = CompletedPort(raw[start:start+1024**2] for start in range(0, len(raw), 1024**2))
    decoded, received = decode_completed_record(port, "original.definition", "metadata", Metadata)
    assert decoded == record and received == raw
    assert port.closed


@pytest.mark.parametrize("chunks", [(b"{}\n",), (bytearray(b"{}\n"),), (b"not canonical",)])
def test_bad_retained_metadata_refuses_and_closes_original_reader(chunks):
    port = CompletedPort(chunks)
    with pytest.raises((ValueError, TypeError)):
        decode_completed_record(port, "original.definition", "metadata", Metadata)
    assert port.closed


def test_retained_metadata_progress_reports_actual_bytes_without_changing_record():
    raw = Metadata("selected exact metadata").canonical_bytes()
    events = []
    class Reporter:
        def update(self, **event):
            events.append(event)
    port = CompletedPort((raw[:7], raw[7:]))
    with progress_reporting(Reporter()):
        decoded, received = decode_completed_record(port, "original.definition", "metadata", Metadata)
    assert decoded.payload == "selected exact metadata" and received == raw and port.closed
    reads = [event for event in events if event["phase"] == "native.retained-record-read"]
    assert [event["done"] for event in reads] == [0, 7, len(raw)]
    assert all(event["total"] is None and event["unit"] == "bytes" for event in reads)
    assert events[-1]["phase"] == "native.retained-record-decode"
    assert events[-1]["done"] == events[-1]["total"] == len(raw)
