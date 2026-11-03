# SPDX-License-Identifier: MPL-2.0
"""Portable exact preparation returns, with bounded raw transport memory.

Every completed selected unit supplies its original definition, completion,
receipt, manifests and all returned bytes. UNKNOWN units supply no invented
return. This is custody evidence, not an independent preparation assessment.
"""

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import ClassVar

from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, canonical_json_bytes
from empirical_lawhood.runtime.artifacts import ArtifactManifest, ArtifactProfile, CanonicalTaskReceipt
from empirical_lawhood.runtime.native_subwork import NativeSubworkCompletion, NativeSubworkDefinition, NativeSubworkState
from empirical_lawhood.runtime.recursive_storage_codecs import RecursiveStorageCodec

from .durable_contracts import DurableNativeCallOperand, DurablePreparationCensus, DurableRawFileCensus, DurableUnitReturn
from .durable_roster import completed_call_custody, definitions as selected_definitions, json_output, raw_output
from .durable_lifecycle import completed_launcher, launcher_definition

MEDIA = "application/x-ndjson"
CHUNK_BYTES = 128 * 1024


def validate_unit_stream(source, request, *, size):
    """Bounded physical JSONL checks; independent scientific custody stays below."""
    from empirical_lawhood.infrastructure.artifact_validation import validate_jsonl_stream
    return validate_jsonl_stream(source, request, size=size, record_version=DurableUnitStreamChunk.VERSION)


DURABLE_UNIT_STREAM_CODEC = RecursiveStorageCodec(
    "rubisco.preparation.unit-stream", "empirical-lawhood/rubisco-insilico-dynamics/durable-unit-stream",
    "1.0.0", ArtifactProfile.JSONL_CHUNKS, MEDIA, ".jsonl", validate_unit_stream)
DURABLE_STORAGE_CODECS = (DURABLE_UNIT_STREAM_CODEC,)


@dataclass(frozen=True, slots=True)
class PortableCallCustody(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-dynamics/portable-call-custody"
    call: ObjectIdentity
    call_state: NativeSubworkState
    call_definition: NativeSubworkDefinition | None
    operand_definition: NativeSubworkDefinition | None
    operand_state: NativeSubworkState | None


@dataclass(frozen=True, slots=True)
class DurablePreparationStreamHeader(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-dynamics/durable-preparation-stream-header"
    census: DurablePreparationCensus
    metadata: NativeSubworkDefinition
    metadata_state: NativeSubworkState
    launcher: NativeSubworkDefinition | None
    launcher_state: NativeSubworkState | None

    def __post_init__(self):
        if (self.metadata.subwork_id != "preparation.metadata" or self.metadata.configuration != self.census.plan
                or self.metadata.operation_id != "rubisco.durable-preparation.metadata"
                or type(self.metadata_state) is not NativeSubworkState):
            raise ValueError("portable preparation changes original process metadata census")
        if self.launcher is not None and (self.launcher.subwork_id != "preparation.launch"
                or self.launcher.operation_id != "rubisco.durable-preparation.launch"
                or self.launcher.parent_contact != self.metadata.parent_contact
                or type(self.launcher_state) is not NativeSubworkState):
            raise ValueError("portable preparation substitutes original process lifecycle")
        if self.metadata_state is NativeSubworkState.COMPLETED and self.launcher is None:
            raise ValueError("portable preparation hides the original launcher declaration")
        if self.metadata_state is not NativeSubworkState.COMPLETED and self.launcher is not None:
            raise ValueError("portable preparation invents an unresolved launcher locator")
        if (self.launcher is None and self.launcher_state is not (
                NativeSubworkState.NOT_ENTERED if self.metadata_state is NativeSubworkState.NOT_ENTERED else None)):
            raise ValueError("portable preparation invents a known unresolved launcher state")

    @property
    def completed_processes(self):
        return tuple(definition for definition, state in ((self.metadata, self.metadata_state),
            (self.launcher, self.launcher_state)) if definition is not None and state is NativeSubworkState.COMPLETED)


@dataclass(frozen=True, slots=True)
class DurableUnitEvidence(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-dynamics/durable-unit-evidence"
    definition: NativeSubworkDefinition
    completion: NativeSubworkCompletion
    receipt: CanonicalTaskReceipt
    outputs: tuple[tuple[str, ArtifactManifest], ...]
    completion_manifest: ArtifactManifest
    conditional_calls: tuple[PortableCallCustody, ...] = ()

    def __post_init__(self):
        names = tuple(name for name, _ in self.outputs)
        declared = {row.output_id: row for row in self.definition.outputs}
        if (names != tuple(sorted(set(names))) or names != self.completion.output_ids
                or set(names) | set(self.completion.omitted_output_ids) != set(declared)
                or self.completion.definition != self.definition.identity
                or self.receipt.operational_status is not self.completion.operational_status
                or not set(self.definition.input_materialization_ids).issubset(self.receipt.input_materialization_ids)
                or len(self.receipt.input_materialization_ids) != len(self.definition.input_materialization_ids) + 3
                or self.receipt.run_id != self.definition.parent_contact.run_id
                or self.receipt.implementation_commit != self.definition.parent_contact.implementation_commit
                or len(self.receipt.output_logical_artifacts) != len(names) + 1):
            raise ValueError("unit stream changes original complete definition/receipt/output census")
        raw_completion = self.completion.canonical_bytes()
        control = self.completion_manifest
        if (control.logical.payload_schema != NativeSubworkCompletion.SCHEMA
                or control.logical.profile is not ArtifactProfile.CANONICAL_JSON
                or control.logical.content_sha256 != self.completion.fingerprint()
                or control.materialization.physical_sha256 != sha256(raw_completion).hexdigest()
                or control.materialization.size_bytes != len(raw_completion)):
            raise ValueError("unit stream substitutes original completion control witness")
        manifests = (*tuple(row for _, row in self.outputs), control)
        if (tuple(sorted((row.logical for row in manifests), key=lambda row: row.logical_artifact_id))
                != self.receipt.output_logical_artifacts
                or tuple(sorted((row.materialization for row in manifests), key=lambda row: row.materialization_id))
                != self.receipt.output_materializations):
            raise ValueError("unit stream substitutes original receipted materializations")
        for name, row in self.outputs:
            contract = declared[name]
            if (not row.logical.logical_artifact_id.endswith(".output." + name)
                    or row.logical.payload_schema != contract.payload_schema
                    or row.logical.profile is not contract.profile
                    or row.logical.media_type != contract.media_type
                    or sum(parent.identity == self.definition.identity for parent in row.logical.lineage_parents) != 1):
                raise ValueError("unit stream loses exact native output contract/lineage")
        if self.conditional_calls:
            ids = tuple(row.call.object_id for row in self.conditional_calls)
            if (self.definition.operation_id != "rubisco.durable-preparation.unit"
                    or ids != tuple(sorted(set(ids)))):
                raise ValueError("unit stream changes complete conditional call census")
            for row in self.conditional_calls:
                if row.call_state is NativeSubworkState.COMPLETED:
                    if (row.call_definition is None or row.call_definition.identity != row.call
                            or row.operand_definition is None or type(row.operand_state) is not NativeSubworkState):
                        raise ValueError("unit stream substitutes original completed call definition")
                    from dataclasses import replace
                    carrier = replace(self.definition, subwork_id=row.call.object_id + ".operand",
                        operation_id="rubisco.durable-preparation.call-operand", roster_id=row.call.object_id + ".operand-roster",
                        outputs=(json_output("call.operand", DurableNativeCallOperand),
                            json_output("files.census", DurableRawFileCensus), raw_output("files.raw")))
                    if (row.operand_definition != carrier or row.call_definition.parent_contact != self.definition.parent_contact
                            or row.call_definition.operation_id != "rubisco.durable-preparation.native-call"
                            or row.call_definition.sources != self.definition.sources
                            or row.call_definition.code_sources_sha256 != self.definition.code_sources_sha256
                            or row.call_definition.dependency_lock_sha256 != self.definition.dependency_lock_sha256):
                        raise ValueError("unit stream changes original conditional operand/call source join")
                elif (row.call_state is not NativeSubworkState.UNKNOWN_COMPLETION
                        or row.call_definition is not None or row.operand_definition is not None):
                    raise ValueError("unit stream manufactures unknown call completion")

    @property
    def completed_children(self):
        return tuple(definition for row in self.conditional_calls for definition, state in (
            (row.operand_definition, row.operand_state), (row.call_definition, row.call_state))
            if state is NativeSubworkState.COMPLETED and definition is not None)

    @property
    def transport_outputs(self):
        # Raw bytes come last, so the live producer can relay its exact chunks.
        return tuple(row for row in self.outputs if row[0] != "files.raw") + tuple(
            row for row in self.outputs if row[0] == "files.raw")


@dataclass(frozen=True, slots=True)
class DurableUnitStreamChunk(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-dynamics/durable-unit-stream"
    sequence: int
    frame_index: int
    frame_schema: str
    size_bytes: int
    sha256: str
    offset: int
    payload_hex: str

    def canonical_bytes(self):
        return canonical_json_bytes({"schema": self.SCHEMA, "sequence": self.sequence, "version": self.VERSION,
            "value": {name: getattr(self, name) for name in
                ("frame_index", "frame_schema", "size_bytes", "sha256", "offset", "payload_hex")}})


class FrameWriter:
    """One bounded chunk at a time; no ceiling on complete native output size."""

    def __init__(self, emitter, output_id, *, record_type=DurableUnitStreamChunk):
        if not isinstance(record_type, type) or not issubclass(record_type, DurableUnitStreamChunk):
            raise ValueError("native stream requires its code-owned exact framed record type")
        self.emitter, self.output_id = emitter, output_id
        self.record_type = record_type
        self.sequence, self.index, self.pending = 0, 0, None

    def start(self, schema, size, digest):
        if self.pending is not None:
            raise ValueError("unit stream has an unfinished prior frame")
        self.pending = (schema, size, digest, sha256(), 0)
        if size == 0:
            self.write(b"")

    def write(self, raw):
        if self.pending is None:
            raise ValueError("unit stream receives bytes outside a declared frame")
        schema, size, digest, actual, offset = self.pending
        if type(raw) is not bytes or (not raw and size != 0) or offset + len(raw) > size:
            raise ValueError("unit stream changes exact raw frame byte denominator")
        for start in range(0, max(1, len(raw)), CHUNK_BYTES):
            chunk = raw[start:start + CHUNK_BYTES]
            row = self.record_type(self.sequence, self.index, schema, size, digest, offset, chunk.hex())
            self.emitter.write(self.output_id, row.canonical_bytes())
            actual.update(chunk)
            offset += len(chunk)
            self.sequence += 1
        self.pending = (schema, size, digest, actual, offset)

    def finish(self):
        if self.pending is None:
            raise ValueError("unit stream omits its declared frame")
        _, size, digest, actual, count = self.pending
        if count != size or actual.hexdigest() != digest:
            raise ValueError("unit stream changes original full output bytes")
        self.pending = None
        self.index += 1

    def record(self, record):
        raw = record.canonical_bytes()
        self.start(record.SCHEMA, len(raw), sha256(raw).hexdigest())
        self.write(raw)
        self.finish()

    def output(self, progress, definition, name, manifest):
        physical = manifest.materialization
        self.start(manifest.logical.payload_schema, physical.size_bytes, physical.physical_sha256)
        if physical.size_bytes:
            for block in progress.iter_completed_output(definition, name, maximum_chunk_bytes=CHUNK_BYTES):
                self.write(block)
        self.finish()


def unit_evidence(progress, definition, *, include_calls=False):
    actual = progress.recover(definition)
    if actual is None or actual.state is not NativeSubworkState.COMPLETED:
        raise ValueError("unit stream requires actual completed original custody")
    outputs = []
    for name in actual.completion.output_ids:
        matches = tuple(row for row in actual.outputs if row.logical.logical_artifact_id.endswith(".output." + name))
        if len(matches) != 1:
            raise ValueError("unit stream omits unique actual output manifest")
        outputs.append((name, matches[0]))
    calls = tuple(PortableCallCustody(row.call, row.call_state, row.call_definition,
        row.operand_definition, row.operand_state) for row in completed_call_custody(progress, definition)) if include_calls else ()
    declared = {row.logical.logical_artifact_id for _, row in outputs}
    remaining = tuple(row for row in actual.receipt.output_logical_artifacts if row.logical_artifact_id not in declared)
    if len(remaining) != 1 or remaining[0].payload_schema != NativeSubworkCompletion.SCHEMA:
        raise ValueError("unit stream retains unsupported partial receipt outputs; full declared return unavailable")
    materializations = tuple(row for row in actual.receipt.output_materializations
        if row.logical_artifact_id == remaining[0].logical_artifact_id)
    if len(materializations) != 1:
        raise ValueError("unit stream loses its exact completion control materialization")
    completion_manifest = ArtifactManifest(remaining[0], materializations[0])
    return DurableUnitEvidence(definition, actual.completion, actual.receipt, tuple(outputs), completion_manifest, calls)


def emit_units(emitter, output_id, progress, census, definitions):
    """Receipt-only export; no native entry or producer reconstruction."""
    writer = FrameWriter(emitter, output_id)
    by_id = {row.subwork_id: row for row in definitions}
    metadata = by_id["preparation.metadata"]
    launcher, state = completed_launcher(progress, metadata)
    header = DurablePreparationStreamHeader(census, metadata, progress.inspect(metadata).state, launcher, state)
    writer.record(header)
    for process in header.completed_processes:
        evidence = unit_evidence(progress, process)
        writer.record(evidence)
        for name, manifest in evidence.transport_outputs:
            writer.output(progress, process, name, manifest)
    for unit, state in census.states:
        if state is not NativeSubworkState.COMPLETED:
            continue
        evidence = unit_evidence(progress, by_id[unit], include_calls=True)
        if evidence.definition.configuration != census.plan:
            raise ValueError("unit stream changes actual producing plan")
        writer.record(evidence)
        for name, manifest in evidence.transport_outputs:
            writer.output(progress, evidence.definition, name, manifest)
        for child in evidence.completed_children:
            child_evidence = unit_evidence(progress, child)
            writer.record(child_evidence)
            for name, manifest in child_evidence.transport_outputs:
                writer.output(progress, child, name, manifest)


def iter_verified_frames(port, *, record_type=DurableUnitStreamChunk):
    """Complete bounded frame verification with an explicit installed domain type."""
    if not isinstance(record_type, type) or not issubclass(record_type, DurableUnitStreamChunk):
        raise ValueError("native stream reader requires its code-owned exact framed record type")
    buffer = bytearray()
    total, sequence, index, descriptor, offset = 0, 0, 0, None, 0
    digest = sha256()
    while True:
        raw = port.read(CHUNK_BYTES)
        if not raw:
            break
        total += len(raw)
        buffer.extend(raw)
        while True:
            end = buffer.find(b"\n")
            if end < 0:
                # Maximum encoded piece is a working-memory contract only.
                if len(buffer) > 2 * CHUNK_BYTES + 4096:
                    raise ValueError("unit stream omits bounded transport record boundary")
                break
            line = bytes(buffer[:end])
            del buffer[:end + 1]
            value = json.loads(line)
            if (canonical_json_bytes(value) != line + b"\n"
                    or set(value) != {"schema", "version", "sequence", "value"}
                    or value["schema"] != record_type.SCHEMA
                    or value["version"] != record_type.VERSION
                    or type(value["sequence"]) is not int or value["sequence"] != sequence):
                raise ValueError("unit stream changes canonical contiguous transport census")
            row = value["value"]
            if set(row) != {"frame_index", "frame_schema", "size_bytes", "sha256", "offset", "payload_hex"}:
                raise ValueError("unit stream substitutes frame envelope")
            current = (row["frame_schema"], row["size_bytes"], row["sha256"])
            if (type(row["frame_index"]) is not int or row["frame_index"] != index
                    or type(row["offset"]) is not int or row["offset"] != offset
                    or type(row["size_bytes"]) is not int or row["size_bytes"] < 0
                    or descriptor is not None and current != descriptor):
                raise ValueError("unit stream reorders/substitutes full frame bytes")
            block = bytes.fromhex(row["payload_hex"])
            if (block.hex() != row["payload_hex"] or len(block) > CHUNK_BYTES
                    or not block and row["size_bytes"] != 0):
                raise ValueError("unit stream changes bounded lossless byte representation")
            descriptor = current
            digest.update(block)
            offset += len(block)
            sequence += 1
            if offset > row["size_bytes"]:
                raise ValueError("unit stream exceeds original frame byte denominator")
            done = offset == row["size_bytes"]
            if done and digest.hexdigest() != row["sha256"]:
                raise ValueError("unit stream changes full original frame digest")
            yield index, current, block, done
            if done:
                index += 1
                offset, descriptor, digest = 0, None, sha256()
    if buffer or descriptor is not None or total != port.size_bytes or index == 0:
        raise ValueError("unit stream omits complete frame/header/final LF")


def authenticate_units(port, plan, *, on_chunk=None, implementation=None, source_root=None):
    """Authenticate all unit bytes without retaining any raw scientific array.

An optional consumer callback receives (evidence, output_id, bytes, complete).
The callback must treat output as provisional until this function returns:
the later complete census can still fail. No custody paths are opened here.
"""
    from empirical_lawhood.infrastructure.bounded_io import MAX_CONTROL_PLANE_JSON_BYTES

    header, evidence, record, expected_units, cursor = None, None, bytearray(), (), 0
    children, unit_return, selection = (), bytearray(), bytearray()
    stream_header, processes, selected = None, (), {}
    outputs, output_index, mode = (), 0, "header"
    for _, descriptor, block, done in iter_verified_frames(port):
        schema, size, _ = descriptor
        if mode in {"header", "evidence"}:
            record_type = DurablePreparationStreamHeader if mode == "header" else DurableUnitEvidence
            if schema != record_type.SCHEMA or size > MAX_CONTROL_PLANE_JSON_BYTES:
                raise ValueError("unit stream changes compact declared control record")
            record.extend(block)
            if not done:
                continue
            decoded = decode_canonical_bytes(bytes(record), record_type, maximum_bytes=size)
            record.clear()
            if mode == "header":
                if decoded.census.plan != plan.identity:
                    raise ValueError("unit stream substitutes selected preparation plan")
                stream_header, header, processes = decoded, decoded.census, decoded.completed_processes
                full = selected_definitions(plan, decoded.metadata.parent_contact,
                    sources=decoded.metadata.sources, input_materialization_ids=decoded.metadata.input_materialization_ids,
                    implementation=implementation, source_root=source_root)
                selected = {row.subwork_id: row for row in full}
                if decoded.metadata != selected["preparation.metadata"]:
                    raise ValueError("unit stream changes exact producing parent/source/code/metadata definition")
                expected_units = tuple(unit for unit, state in header.states if state is NativeSubworkState.COMPLETED)
            else:
                evidence = decoded
                if processes:
                    if evidence.definition != processes[0] or evidence.conditional_calls:
                        raise ValueError("unit stream substitutes original operational process custody")
                    processes = processes[1:]
                elif children:
                    if evidence.definition != children[0] or evidence.conditional_calls:
                        raise ValueError("unit stream substitutes original conditional call/carrier")
                    children = children[1:]
                else:
                    if (cursor >= len(expected_units) or evidence.definition.subwork_id != expected_units[cursor]
                            or evidence.definition != selected.get(evidence.definition.subwork_id)):
                        raise ValueError("unit stream changes full completed unit census/plan")
                    cursor += 1
                    children = evidence.completed_children
                outputs, output_index = evidence.transport_outputs, 0
            mode = "output" if evidence is not None and outputs else "evidence"
        else:
            name, manifest = outputs[output_index]
            if descriptor != (manifest.logical.payload_schema, manifest.materialization.size_bytes,
                              manifest.materialization.physical_sha256):
                raise ValueError("unit stream changes original receipted output bytes/size/schema")
            if on_chunk is not None:
                on_chunk(evidence, name, block, done)
            if name == "process.selection":
                from empirical_lawhood.runtime.isolated_native_subwork import IsolatedNativeEntrySelection
                if size > MAX_CONTROL_PLANE_JSON_BYTES:
                    raise ValueError("process selection exceeds original finite control envelope")
                selection.extend(block)
                if done:
                    actual_selection = decode_canonical_bytes(bytes(selection), IsolatedNativeEntrySelection, maximum_bytes=size)
                    selection.clear()
                    if launcher_definition(evidence.definition, actual_selection, evidence.outputs) != stream_header.launcher:
                        raise ValueError("unit stream loses original selection/launcher input/receipt join")
            if name == "unit.return" and evidence.definition.operation_id == "rubisco.durable-preparation.unit":
                if size > MAX_CONTROL_PLANE_JSON_BYTES:
                    raise ValueError("unit return exceeds finite original control envelope")
                unit_return.extend(block)
                if done:
                    actual_return = decode_canonical_bytes(bytes(unit_return), DurableUnitReturn, maximum_bytes=size)
                    unit_return.clear()
                    if (actual_return.unit_id != evidence.definition.subwork_id or actual_return.plan != plan.identity
                            or actual_return.native_calls != tuple(row.call for row in evidence.conditional_calls)):
                        raise ValueError("unit stream hides original conditional call denominator")
            if done:
                output_index += 1
                if output_index == len(outputs):
                    mode, evidence, outputs = "evidence", None, ()
    if (header is None or mode != "evidence" or cursor != len(expected_units)
            or record or children or processes or unit_return or selection):
        raise ValueError("unit stream omits original complete unit/output denominator")
    return header
