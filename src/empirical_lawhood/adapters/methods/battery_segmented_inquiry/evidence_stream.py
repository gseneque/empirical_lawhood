# SPDX-License-Identifier: MPL-2.0
"""Declared, sequential original segment evidence through authenticated relay.

JSONL records contain bounded transport pieces. They impose no total record or
scientific array ceiling. The consumer retains one complete segment at a time.
"""

from collections import Counter
from dataclasses import dataclass
from hashlib import sha256
import json
from typing import ClassVar

from empirical_lawhood.adapters.methods.battery_refined_inquiry import preparation_contracts as pc
from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_native as native
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, canonical_json_bytes
from empirical_lawhood.runtime.artifacts import CanonicalTaskReceipt
from empirical_lawhood.runtime.native_subwork import NativeSubworkDefinition

MEDIA = "application/x-ndjson"
CHUNK_BYTES = 128 * 1024


@dataclass(frozen=True, slots=True)
class SegmentEvidenceFrame(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented-inquiry/segment-evidence-frame"
    segment_index: int
    definition: NativeSubworkDefinition
    request_receipt: CanonicalTaskReceipt
    native_receipt: CanonicalTaskReceipt
    request: native.SegmentRequest
    returned: native.SegmentReturn
    next_request: native.SegmentRequest
    raw_return: native.RawReturnedSegment | None
    full_state: native.FullStateSegment | None
    requested_initial: pc.StateObservation | None
    actual_initial: pc.StateObservation | None
    initial_derivative: pc.StateObservation | None
    actual_terminal: pc.StateObservation | None
    terminal_derivative: pc.StateObservation | None

    def __post_init__(self):
        if type(self.segment_index) is not int or self.segment_index < 1 or self.request.ordinal != self.segment_index:
            raise ValueError("segment frame changes its actual ordered call ordinal")
        if self.returned.request != self.request.identity:
            raise ValueError("segment frame substitutes its original request/return join")
        optional = ((self.raw_return, native.RawReturnedSegment), (self.full_state, native.FullStateSegment),
            *((getattr(self, name), pc.StateObservation) for name in ("requested_initial", "actual_initial",
                "initial_derivative", "actual_terminal", "terminal_derivative")))
        if any(record is not None and type(record) is not record_type for record, record_type in optional):
            raise ValueError("segment frame changes an actual optional output type")
        schemas = {record_type.SCHEMA for _, record_type in optional}
        actual = Counter((row.payload_schema, row.content_sha256) for row in self.native_receipt.output_logical_artifacts
            if row.payload_schema in schemas)
        present = Counter((record.SCHEMA, record.fingerprint()) for record, _ in optional if record is not None)
        if actual != present:
            raise ValueError("segment frame hides or substitutes a materialized optional output from its actual receipt census")
        if (self.next_request.configuration != self.request.configuration or self.next_request.protocol != self.request.protocol
                or sum(row.payload_schema == self.next_request.SCHEMA and row.content_sha256 == self.next_request.fingerprint()
                    for row in self.native_receipt.output_logical_artifacts) != 1):
            raise ValueError("segment frame omits its actual successor or end-of-chain declaration")
        matched = tuple(row for row in self.request_receipt.output_logical_artifacts
            if row.payload_schema == self.request.SCHEMA and row.content_sha256 == self.request.fingerprint())
        if len(matched) != 1:
            raise ValueError("segment request loses its actual producing carrier receipt")
        materializations = tuple(row for row in self.request_receipt.output_materializations
            if row.logical_artifact_id == matched[0].logical_artifact_id)
        if (len(materializations) != 1 or materializations[0].materialization_id not in self.definition.input_materialization_ids
                or self.definition.configuration != self.request.identity
                or not set(self.definition.input_materialization_ids).issubset(self.native_receipt.input_materialization_ids)
                or any(sum(parent.identity == self.definition.identity for parent in row.lineage_parents) != 1
                    for row in self.native_receipt.output_logical_artifacts)):
            raise ValueError("segment request loses its exact frozen definition/input/returned-output custody")

    @property
    def records(self):
        return {name: getattr(self, name) for name in ("request", "returned", "raw_return", "full_state",
            "requested_initial", "actual_initial", "initial_derivative", "actual_terminal", "terminal_derivative")}


@dataclass(frozen=True, slots=True)
class SegmentStreamHeader(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented-inquiry/segment-stream-header"
    trace: ObjectIdentity
    protocol: ObjectIdentity
    segment_count: int

    def __post_init__(self):
        if (self.trace.object_schema != native.SegmentedTrace.SCHEMA or self.protocol.object_schema != pc.PreparationProtocol.SCHEMA
                or type(self.segment_count) is not int or self.segment_count < 0):
            raise ValueError("segment stream header changes its original complete forecast census")


@dataclass(frozen=True, slots=True)
class SegmentStreamChunk(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented-inquiry/segment-evidence-stream"
    sequence: int
    frame_index: int
    frame_schema: str
    size_bytes: int
    sha256: str
    offset: int
    payload_hex: str

    def canonical_bytes(self):
        # JSONL_CHUNKS requires contiguous sequence at the top level.
        return canonical_json_bytes({"schema": self.SCHEMA, "sequence": self.sequence, "version": self.VERSION,
            "value": {name: getattr(self, name) for name in ("frame_index", "frame_schema", "size_bytes", "sha256", "offset", "payload_hex")}})


def emit_record(emitter, output_id, record):
    """Retain exact canonical record bytes across bounded ordinary writes."""
    raw = record.canonical_bytes()
    for offset in range(0, len(raw), CHUNK_BYTES):
        emitter.write(output_id, raw[offset:offset + CHUNK_BYTES])


def emit_frame(emitter, output_id, record, frame_index, sequence):
    raw = record.canonical_bytes()
    digest = sha256(raw).hexdigest()
    for offset in range(0, len(raw), CHUNK_BYTES):
        chunk = SegmentStreamChunk(sequence, frame_index, record.SCHEMA, len(raw), digest,
            offset, raw[offset:offset + CHUNK_BYTES].hex())
        emitter.write(output_id, chunk.canonical_bytes())
        sequence += 1
    return sequence


def read_frames(port):
    """Read arbitrary transport boundaries with exact complete frame joins."""
    buffer = bytearray()
    frame = bytearray()
    sequence, index, descriptor = 0, 0, None
    count = 0
    while True:
        chunk = port.read(CHUNK_BYTES)
        if not chunk:
            break
        count += len(chunk)
        scan_from = len(buffer)
        buffer.extend(chunk)
        while True:
            newline = buffer.find(b"\n", scan_from)
            if newline < 0:
                break
            line = buffer[:newline]
            buffer = buffer[newline + 1:]
            scan_from = 0
            value = json.loads(line)
            if (canonical_json_bytes(value) != line + b"\n" or set(value) != {"schema", "sequence", "version", "value"}
                    or value["schema"] != SegmentStreamChunk.SCHEMA or value["version"] != SegmentStreamChunk.VERSION
                    or type(value["sequence"]) is not int or value["sequence"] != sequence):
                raise ValueError("segment stream changes canonical bytes or contiguous transport census")
            row = value["value"]
            if set(row) != {"frame_index", "frame_schema", "size_bytes", "sha256", "offset", "payload_hex"}:
                raise ValueError("segment stream substitutes its exact frame envelope")
            current = (row["frame_schema"], row["size_bytes"], row["sha256"])
            if (type(row["frame_index"]) is not int or row["frame_index"] != index
                    or type(row["offset"]) is not int or row["offset"] != len(frame)
                    or type(row["size_bytes"]) is not int or row["size_bytes"] <= 0
                    or descriptor is not None and descriptor != current):
                raise ValueError("segment stream omits, reorders or substitutes complete frame bytes")
            descriptor = current
            payload = bytes.fromhex(row["payload_hex"])
            if not payload or len(payload) > CHUNK_BYTES or payload.hex() != row["payload_hex"]:
                raise ValueError("segment stream changes its selected transport chunk representation")
            frame.extend(payload)
            sequence += 1
            if len(frame) > row["size_bytes"]:
                raise ValueError("segment stream exceeds its exact original frame denominator")
            if len(frame) == row["size_bytes"]:
                if sha256(frame).hexdigest() != row["sha256"]:
                    raise ValueError("segment stream changes original complete frame digest")
                record_type = SegmentStreamHeader if index == 0 else SegmentEvidenceFrame
                if row["frame_schema"] != record_type.SCHEMA:
                    raise ValueError("segment stream changes its declared header/segment type")
                record = decode_canonical_bytes(bytes(frame), record_type, maximum_bytes=None)
                if record.canonical_bytes() != frame or index and record.segment_index != index:
                    raise ValueError("segment stream changes its exact canonical original record")
                frame = bytearray()
                descriptor = None
                index += 1
                yield record
                del record
    if buffer or frame or count != port.size_bytes or index == 0:
        raise ValueError("segment stream omits a complete header, frame, or final LF")


def _manifest(inspection, output_id):
    # These are coordinator-returned logical identities, never storage paths.
    suffix = ".output." + output_id
    matches = tuple(row for row in inspection.outputs if row.logical.logical_artifact_id.endswith(suffix))
    if len(matches) > 1:
        raise ValueError("completed native inspection substitutes a unique actual output")
    return matches[0] if matches else None


def completed_record(progress, definition, inspection, name, record_type, *, optional=False):
    manifest = _manifest(inspection, name)
    if manifest is None:
        if optional:
            return None
        raise ValueError("completed native receipt omits a required original output")
    if manifest.logical.payload_schema != record_type.SCHEMA:
        raise ValueError("completed native output changes its declared original type")
    raw = b"".join(progress.iter_completed_output(definition, name, maximum_chunk_bytes=CHUNK_BYTES))
    record = decode_canonical_bytes(raw, record_type, maximum_bytes=None)
    if record.canonical_bytes() != raw or record.fingerprint() != manifest.logical.content_sha256:
        raise ValueError("completed native output substitutes original canonical bytes")
    return record


def relay_segments(progress, definition, inspection, trace, protocol):
    """Reconstruct exact frozen child definitions from actual carrier manifests.

    Recovered completion uses original products and receipts, with no native
    effect. A partial/unknown child cannot yield a completed stream frame.
    """
    preparation = native.completed_preparation_checkpoint(progress, definition)
    previous = inspection if preparation is None else preparation
    context = () if preparation is None else tuple(row.materialization.materialization_id for row in preparation.outputs)
    for summary in trace.segments:
        name = "native.request.first" if summary.segment_index == 1 else "native.request.next"
        request = completed_record(progress, previous.definition, previous, name, native.SegmentRequest)
        if request.identity != summary.request:
            raise ValueError("original segment request differs from complete trace summary")
        request_manifest = _manifest(previous, name)
        additional = [request_manifest.materialization.materialization_id]
        if summary.segment_index != 1:
            terminal = _manifest(previous, "actual-terminal")
            if terminal is None:
                raise ValueError("actual successor lost its previous full terminal materialization")
            additional.append(terminal.materialization.materialization_id)
        child = progress.resolve_completed_definition(summary.native_definition)
        if (child.identity != summary.native_definition or child.parent_contact != definition.parent_contact
                or child.subwork_id != definition.subwork_id + ".segment." + str(summary.segment_index)
                or child.operation_id != "battery.segmented-native.segment" or child.configuration != request.identity
                or child.input_materialization_ids != tuple(sorted(set((*definition.input_materialization_ids, *context, *additional))))
                or child.outputs != native.segment_outputs() or child.sources != definition.sources
                or child.streams != definition.streams or child.code_sources_sha256 != definition.code_sources_sha256
                or child.dependency_lock_sha256 != definition.dependency_lock_sha256
                or child.roster_id != "conditional.battery.segment." + str(summary.segment_index)):
            raise ValueError("segment stream changes the exact original frozen native definition")
        current = progress.recover(child)
        if current is None or current.receipt is None or ObjectIdentity.from_record(current.receipt.receipt_id, current.receipt) != summary.native_receipt:
            raise ValueError("segment stream lacks its exact actual completed native receipt")
        records = {"returned": completed_record(progress, child, current, "native.return", native.SegmentReturn),
            "next_request": completed_record(progress, child, current, "native.request.next", native.SegmentRequest)}
        for name, record_type in (("raw_return", native.RawReturnedSegment), ("full_state", native.FullStateSegment),
                *((name, pc.StateObservation) for name in ("requested_initial", "actual_initial", "initial_derivative", "actual_terminal", "terminal_derivative"))):
            records[name] = completed_record(progress, child, current, name.replace("_", "-"), record_type, optional=True)
        yield SegmentEvidenceFrame(summary.segment_index, child, previous.receipt, current.receipt, request, **records)
        del records
        previous = current
