# SPDX-License-Identifier: MPL-2.0
"""Actual new-schema native custody and a lossless ordinary battery stream.

One compressed raw population is relayed from its authentic native receipt.
The independent reader exhausts that population before yielding a scientific
frame. Temporary binary files hold at most active segments; vectors are lazy.
"""

import base64
from collections import Counter
from contextlib import ExitStack
from dataclasses import dataclass
from hashlib import sha256
import json
from tempfile import TemporaryFile
from typing import ClassVar
import zlib

from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.serialization import CanonicalRecord, canonical_json_bytes, validate_sha256
from empirical_lawhood.runtime.artifacts import CanonicalTaskReceipt
from empirical_lawhood.runtime.native_subwork import NativeSubworkDefinition
from empirical_lawhood.adapters.methods.battery_segmented_inquiry import evidence_stream as old
from . import lossless_segment_arrays as codec
from . import lossless_segment_records as records
from . import lossless_segment_native as storage
from . import preparation_contracts as pc
from . import segmented_native as native


@dataclass(frozen=True, slots=True)
class LosslessSegmentMetadata(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/lossless-segment-evidence-metadata"
    segment_index: int
    definition: NativeSubworkDefinition
    request_receipt: CanonicalTaskReceipt
    native_receipt: CanonicalTaskReceipt
    request: native.SegmentRequest
    returned: native.SegmentReturn
    next_request: native.SegmentRequest
    raw_index: records.RawSegmentIndex | None
    raw_physical_sha256: str | None
    raw_size_bytes: int | None
    full_index: records.FullSegmentIndex | None
    requested_initial: pc.StateObservation | None
    actual_initial: pc.StateObservation | None
    initial_derivative: pc.StateObservation | None
    actual_terminal: pc.StateObservation | None
    terminal_derivative: pc.StateObservation | None

    def __post_init__(self):
        if (type(self.segment_index) is not int or self.segment_index < 1 or self.request.ordinal != self.segment_index
                or self.returned.request != self.request.identity or self.definition.configuration != self.request.identity):
            raise ValueError("lossless frame changes its authentic request/return/definition ordinal")
        optional = ((self.full_index, records.FullSegmentIndex), *((getattr(self, name), pc.StateObservation) for name in
            ("requested_initial", "actual_initial", "initial_derivative", "actual_terminal", "terminal_derivative")))
        if any(row is not None and type(row) is not kind for row, kind in optional):
            raise ValueError("lossless frame substitutes authentic optional output types")
        schemas = {kind.SCHEMA for _, kind in optional} | {records.RawSegmentStreamLine.SCHEMA, native.SegmentReturn.SCHEMA}
        actual = Counter((row.payload_schema, row.content_sha256) for row in self.native_receipt.output_logical_artifacts
            if row.payload_schema in schemas)
        present = Counter((row.SCHEMA, row.fingerprint()) for row, _ in optional if row is not None)
        present[(self.returned.SCHEMA, self.returned.fingerprint())] += 1
        if self.raw_index is not None:
            if type(self.raw_index) is not records.RawSegmentIndex or type(self.raw_size_bytes) is not int or self.raw_size_bytes < 1:
                raise ValueError("lossless frame changes its complete raw physical population")
            self.raw_index.__post_init__()
            validate_sha256(self.raw_physical_sha256)
            present[(records.RawSegmentStreamLine.SCHEMA, self.raw_physical_sha256)] += 1
            outputs = tuple(row for row in self.native_receipt.output_logical_artifacts
                if row.payload_schema == records.RawSegmentStreamLine.SCHEMA and row.content_sha256 == self.raw_physical_sha256)
            if len(outputs) != 1:
                raise ValueError("lossless raw population lacks its actual physical native receipt")
            materials = tuple(row for row in self.native_receipt.output_materializations if row.logical_artifact_id == outputs[0].logical_artifact_id)
            if len(materials) != 1 or materials[0].size_bytes != self.raw_size_bytes or materials[0].physical_sha256 != self.raw_physical_sha256:
                raise ValueError("lossless raw population changes exact physical byte/hash receipt joins")
            if (self.raw_index.request != self.request.identity or self.raw_index.returned != records.identity(self.returned, "return_id")
                    or self.raw_index.protocol != self.request.protocol):
                raise ValueError("lossless raw index changes actual scientific source lineage")
        elif self.raw_physical_sha256 is not None or self.raw_size_bytes is not None or self.full_index is not None:
            raise ValueError("lossless frame invents raw bytes or an interpretation after absent raw custody")
        if actual != present:
            raise ValueError("lossless frame hides or substitutes an actual new-schema native output")
        if self.full_index is not None and (self.full_index.raw_index != records.identity(self.raw_index, "index_id")
                or self.full_index.decoded_raw_subject != self.raw_index.decoded_subject):
            raise ValueError("lossless full output substitutes its exact raw index/decoded subject")
        if (self.next_request.configuration != self.request.configuration or self.next_request.protocol != self.request.protocol
                or sum(row.payload_schema == self.next_request.SCHEMA and row.content_sha256 == self.next_request.fingerprint()
                    for row in self.native_receipt.output_logical_artifacts) != 1):
            raise ValueError("lossless frame omits authentic successor or complete end-of-chain")
        matches = tuple(row for row in self.request_receipt.output_logical_artifacts
            if row.payload_schema == self.request.SCHEMA and row.content_sha256 == self.request.fingerprint())
        materials = tuple(row for row in self.request_receipt.output_materializations
            if len(matches) == 1 and row.logical_artifact_id == matches[0].logical_artifact_id)
        if (len(matches) != 1 or len(materials) != 1 or materials[0].materialization_id not in self.definition.input_materialization_ids
                or not set(self.definition.input_materialization_ids).issubset(self.native_receipt.input_materialization_ids)
                or any(sum(parent.identity == self.definition.identity for parent in row.lineage_parents) != 1
                    for row in self.native_receipt.output_logical_artifacts)):
            raise ValueError("lossless frame loses actual request publisher, inputs or native output lineage")
        if self.definition.outputs != storage.segment_outputs():
            raise ValueError("lossless frame substitutes complete declared physical native output schemas")


class LosslessSegmentFrame:
    """Complete verified physical custody plus bounded decoded numerical views."""
    def __init__(self, metadata, sources, handles=(), raw_lines=None, *, temporary_file=None, transforms=None):
        from .dataset_bridge import bridge_lossless_inputs
        metadata.__post_init__()
        self.metadata, self.sources, self.handles, self.raw_lines = metadata, sources, handles, raw_lines
        self.raw_return = metadata.raw_index
        self.full_state = None
        self._lifetime, self._closed = ExitStack(), False
        try:
            self.dataset = bridge_lossless_inputs(metadata, sources, transforms=transforms,
                maximum_slice_bytes=codec.CHUNK_BYTES)
            self.dataset_reader = self._lifetime.enter_context(
                self.dataset.reader.verified_session(block_size_bytes=codec.CHUNK_BYTES))
            if metadata.full_index is not None:
                self.full_state = records.DecodedFullSegment(metadata.full_index, metadata.raw_index, sources,
                    temporary_file=temporary_file, dataset_reader=self.dataset_reader)
        except BaseException:
            import sys
            self._lifetime.__exit__(*sys.exc_info())
            raise
        self.verified_raw = metadata.raw_index is None or sources is not None

    def __getattr__(self, name):
        return getattr(self.metadata, name)

    def __post_init__(self):
        self.metadata.__post_init__()
        if self._closed or not self.verified_raw:
            raise ValueError("lossless scientific frame has not exhausted authentic raw bytes")

    def close(self):
        if self._closed:
            return
        self._closed = True
        try:
            # No report or next frame may escape before the final current-byte
            # seal, including members never visited by the numerical reducer.
            self._lifetime.close()
        finally:
            for handle in self.handles:
                handle.close()
            if self.full_state is not None:
                for handle in self.full_state.scratch_handles:
                    handle.close()


def bounded_lines(chunks):
    buffer = bytearray()
    for chunk in chunks:
        if type(chunk) is not bytes or len(chunk) > 3 * codec.CHUNK_BYTES:
            raise ValueError("lossless raw source changes bounded physical read chunks")
        buffer.extend(chunk)
        while True:
            end = buffer.find(b"\n")
            if end < 0:
                break
            line = bytes(buffer[:end + 1])
            del buffer[:end + 1]
            if len(line) > 3 * codec.CHUNK_BYTES:
                raise ValueError("lossless raw source exceeds bounded transport line")
            yield line
        if len(buffer) > 3 * codec.CHUNK_BYTES:
            raise ValueError("lossless raw source exceeds bounded partial line")
    if buffer:
        raise ValueError("lossless raw source omits its final newline")


def _verified_raw_lines(lines, metadata):
    size, digest = 0, sha256()
    for line in lines:
        size += len(line)
        digest.update(line)
        yield line
    if size != metadata.raw_size_bytes or digest.hexdigest() != metadata.raw_physical_sha256:
        raise ValueError("lossless raw source differs from actual native physical receipt bytes")


def decoded_frame(metadata, lines, temporary_file):
    from .dataset_bridge import lossless_dataset_manifest
    metadata.__post_init__()
    if metadata.raw_index is None:
        if next(iter(lines), None) is not None:
            raise ValueError("lossless frame invents absent raw outputs")
        return LosslessSegmentFrame(metadata, {})
    transforms = {}
    raw, sources, handles = records.decode_raw_segment(iter(_verified_raw_lines(lines, metadata)), temporary_file,
        clock_major_working=metadata.full_index is not None, dataset_manifest=lossless_dataset_manifest(metadata),
        transform_witnesses=transforms)
    try:
        if raw != metadata.raw_index:
            raise ValueError("lossless raw bytes substitute metadata index/scientific source")
        if set(transforms) != set(sources):
            # A non-FD source cannot acquire a physical proof by its label.
            # All members instead use the same complete logical block lease.
            for witness in transforms.values():
                witness.close()
            transforms.clear()
            selected_transforms = None
        else:
            selected_transforms = transforms
        return LosslessSegmentFrame(metadata, sources, handles, temporary_file=temporary_file,
            transforms=selected_transforms)
    except BaseException:
        for witness in transforms.values():
            witness.close()
        for handle in handles:
            handle.close()
        raise


@dataclass(frozen=True, slots=True)
class LosslessEvidenceLine(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/lossless-evidence-stream"
    sequence: int
    frame_index: int
    kind: str
    payload: str | None
    complete_sha256: str | None
    complete_bytes: int | None

    def __post_init__(self):
        if (type(self.sequence) is not int or self.sequence < 0 or type(self.frame_index) is not int or self.frame_index < 0
                or self.kind not in {"HEADER", "METADATA", "METADATA_END", "RAW", "FRAME_END"}
                or self.kind in {"HEADER", "METADATA", "RAW"} and (type(self.payload) is not str or self.complete_bytes is not None or self.complete_sha256 is not None)
                or self.kind == "METADATA_END" and (self.payload is not None or type(self.complete_bytes) is not int or self.complete_bytes < 1)
                or self.kind == "FRAME_END" and (self.payload is not None or self.complete_bytes is not None or self.complete_sha256 is not None)):
            raise ValueError("lossless evidence stream changes bounded type or complete framing")
        if self.kind == "METADATA_END":
            validate_sha256(self.complete_sha256)

    def canonical_bytes(self):
        return canonical_json_bytes({"schema": self.SCHEMA, "version": self.VERSION, "sequence": self.sequence,
            "value": {name: getattr(self, name) for name in ("frame_index", "kind", "payload", "complete_sha256", "complete_bytes")}})


def _line(sequence, frame_index, kind, payload=None, digest=None, size=None):
    return LosslessEvidenceLine(sequence, frame_index, kind, payload, digest, size).canonical_bytes()


def emit_header(emitter, output_id, header):
    emitter.write(output_id, _line(0, 0, "HEADER", header.canonical_bytes().decode()))
    return 1


def emit_frame(emitter, output_id, metadata, raw_lines, sequence):
    metadata.__post_init__()
    payload = metadata.canonical_bytes()
    index = metadata.segment_index
    for offset in range(0, len(payload), codec.CHUNK_BYTES):
        compressor = zlib.compressobj(level=6, wbits=31)
        raw = payload[offset:offset + codec.CHUNK_BYTES]
        encoded = compressor.compress(raw) + compressor.flush()
        emitter.write(output_id, _line(sequence, index, "METADATA", base64.b64encode(encoded).decode()))
        sequence += 1
    emitter.write(output_id, _line(sequence, index, "METADATA_END", digest=sha256(payload).hexdigest(), size=len(payload)))
    sequence += 1
    if metadata.raw_index is not None:
        for line in _verified_raw_lines(raw_lines, metadata):
            emitter.write(output_id, _line(sequence, index, "RAW", line.decode()))
            sequence += 1
    elif next(iter(raw_lines), None) is not None:
        raise ValueError("lossless relay invents absent raw outputs")
    emitter.write(output_id, _line(sequence, index, "FRAME_END"))
    return sequence + 1


def _decode_line(line, sequence):
    from empirical_lawhood.kernel.decoding import decode_canonical_record
    document = json.loads(line)
    row = decode_canonical_record({"schema": document.get("schema"), "version": document.get("version"),
        "value": {"sequence": document.get("sequence"), **document.get("value", {})}}, LosslessEvidenceLine)
    if row.sequence != sequence or row.canonical_bytes() != line:
        raise ValueError("lossless evidence changes exact contiguous canonical bytes")
    return row


def read_frames(port, *, temporary_file):
    """Complete used consumer; the caller explicitly chooses scratch custody."""
    def chunks():
        size = 0
        while chunk := port.read(codec.CHUNK_BYTES):
            size += len(chunk)
            yield chunk
        if size != port.size_bytes:
            raise ValueError("lossless evidence omits actual ordinary materialization bytes")
    lines = iter(bounded_lines(chunks()))
    sequence = 0
    def take():
        nonlocal sequence
        try:
            row = _decode_line(next(lines), sequence)
        except StopIteration as error:
            raise ValueError("lossless evidence omits its complete frame/footer denominator") from error
        sequence += 1
        return row
    first = take()
    if first.kind != "HEADER" or first.frame_index != 0:
        raise ValueError("lossless evidence lacks original complete forecast header")
    header = decode_canonical_bytes(first.payload.encode(), old.SegmentStreamHeader, maximum_bytes=None)
    if header.canonical_bytes().decode() != first.payload:
        raise ValueError("lossless evidence changes exact original scientific header")
    yield header
    for index in range(1, header.segment_count + 1):
        payload = bytearray()
        while True:
            row = take()
            if row.frame_index != index:
                raise ValueError("lossless evidence omits or reorders an actual call")
            if row.kind == "METADATA_END":
                if len(payload) != row.complete_bytes or sha256(payload).hexdigest() != row.complete_sha256:
                    raise ValueError("lossless metadata omits complete original custody bytes")
                break
            if row.kind != "METADATA":
                raise ValueError("lossless evidence changes exact metadata/raw order")
            encoded = base64.b64decode(row.payload, validate=True)
            decoder = zlib.decompressobj(wbits=31)
            raw = decoder.decompress(encoded, codec.CHUNK_BYTES + 1)
            if len(raw) > codec.CHUNK_BYTES or not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
                raise ValueError("lossless metadata changes bounded gzip bytes or adds trailing members")
            payload.extend(raw)
        metadata = decode_canonical_bytes(bytes(payload), LosslessSegmentMetadata, maximum_bytes=None)
        if metadata.canonical_bytes() != payload or metadata.segment_index != index:
            raise ValueError("lossless evidence substitutes original canonical metadata")
        del payload
        def raw_lines():
            while True:
                row = take()
                if row.frame_index != index:
                    raise ValueError("lossless evidence substitutes raw segment ordinal")
                if row.kind == "FRAME_END":
                    return
                if row.kind != "RAW":
                    raise ValueError("lossless evidence changes selected raw population or omits final frame")
                yield row.payload.encode()
        frame = decoded_frame(metadata, raw_lines(), temporary_file)
        try:
            yield frame
        finally:
            frame.close()
        del frame, metadata
    if next(lines, None) is not None:
        raise ValueError("lossless evidence adds undeclared scientific calls")


def selected_temporary_files(directory):
    """Explicit selected scratch path; no implicit cwd/system storage choice."""
    return lambda: TemporaryFile(dir=directory, buffering=0)
