# SPDX-License-Identifier: MPL-2.0
"""Original sampling custody over the shared bounded native framing mechanics."""

from dataclasses import dataclass, replace
from typing import ClassVar

from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_contracts import (
    DurableNativeCallOperand, DurableRawFileCensus)
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_roster import json_output, raw_output
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_stream import (
    DurableUnitEvidence, DurableUnitStreamChunk, FrameWriter, PortableCallCustody, iter_verified_frames, unit_evidence)
from empirical_lawhood.infrastructure.bounded_io import MAX_CONTROL_PLANE_JSON_BYTES
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.isolated_native_subwork import (
    IsolatedNativeEntryReturn, IsolatedNativeEntrySelection, IsolatedNativeProcessStart)
from empirical_lawhood.runtime.native_subwork import NativeSubworkDefinition, NativeSubworkState, NativeSubworkUncertainContact
from empirical_lawhood.runtime.recursive_storage_codecs import RecursiveStorageCodec

from .control_contracts import ChemicalForceCensus, ChemicalForceReturn
from .nve_contracts import NVEControlCensus, NVEControlReturn

MEDIA = "application/x-ndjson"


@dataclass(frozen=True, slots=True)
class SamplingUnitStreamChunk(DurableUnitStreamChunk):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-sampling/unit-stream"


def validate_sampling_stream(source, request, *, size):
    from empirical_lawhood.infrastructure.artifact_validation import validate_jsonl_stream
    return validate_jsonl_stream(source, request, size=size, record_version=SamplingUnitStreamChunk.VERSION)


SAMPLING_STORAGE_CODECS = (RecursiveStorageCodec("rubisco.sampling.unit-stream", SamplingUnitStreamChunk.SCHEMA,
    SamplingUnitStreamChunk.VERSION, ArtifactProfile.JSONL_CHUNKS, MEDIA, ".jsonl", validate_sampling_stream),)


def launcher_definition(metadata, selection, outputs):
    """The original launcher joins its exact selection and metadata receipts."""
    operations = {"rubisco.chemical-force.metadata": ("control.chemical-force.launch", "rubisco.chemical-force.launch",
        "conditional.rubisco-chemical-force.launch"), "rubisco.nve-control.metadata": (
        "control.nve.launch", "rubisco.nve-control.launch", "conditional.rubisco-nve-control.launch")}
    if metadata.operation_id not in operations or type(selection) is not IsolatedNativeEntrySelection:
        raise ValueError("sampling launcher changes its original metadata/selection type")
    manifests = dict(outputs)
    if set(manifests) - {"files.census", "files.raw", "process.selection", "control.census"}:
        raise ValueError("sampling launcher changes its original metadata output census")
    required = ("process.selection", "files.census", "files.raw")
    if not set(required).issubset(manifests):
        raise ValueError("sampling launcher omits its original selection/full invocation receipts")
    subwork_id, operation_id, roster_id = operations[metadata.operation_id]
    return replace(metadata, subwork_id=subwork_id, operation_id=operation_id,
        configuration=selection.identity, roster_id=roster_id,
        input_materialization_ids=tuple(sorted((*metadata.input_materialization_ids,
            *(manifests[name].materialization.materialization_id for name in required)))),
        outputs=(json_output("files.census", DurableRawFileCensus), raw_output("files.raw"),
            json_output("process.return", IsolatedNativeEntryReturn), json_output("process.start", IsolatedNativeProcessStart)))


@dataclass(frozen=True, slots=True)
class SamplingStreamHeader(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-sampling/stream-header"
    census: ChemicalForceCensus | NVEControlCensus
    definitions: tuple[NativeSubworkDefinition, ...]
    metadata: NativeSubworkDefinition
    metadata_state: NativeSubworkState
    launcher: NativeSubworkDefinition
    launcher_state: NativeSubworkState

    def __post_init__(self):
        chemical = type(self.census) is ChemicalForceCensus
        if not chemical and type(self.census) is not NVEControlCensus:
            raise ValueError("sampling stream substitutes its exact domain census type")
        self.census.__post_init__()
        prefix = "control.chemical-force" if chemical else "control.nve"
        operation = "rubisco.chemical-force" if chemical else "rubisco.nve-control"
        names = tuple(row.subwork_id for row in self.definitions)
        if (names != tuple(sorted(set(names))) or set(names) != {prefix + ".metadata", *(name for name, _ in self.census.states)}
                or self.metadata not in self.definitions or self.metadata.subwork_id != prefix + ".metadata"
                or self.metadata.operation_id != operation + ".metadata"
                or any(row.configuration != self.census.plan or row.parent_contact != self.metadata.parent_contact
                    for row in self.definitions)
                or self.launcher.subwork_id != prefix + ".launch" or self.launcher.operation_id != operation + ".launch"
                or self.launcher.parent_contact != self.metadata.parent_contact
                or type(self.metadata_state) is not NativeSubworkState or type(self.launcher_state) is not NativeSubworkState):
            raise ValueError("sampling stream changes its complete original unit/process/parent census")

    @property
    def completed_processes(self):
        return tuple(row for row, state in ((self.metadata, self.metadata_state), (self.launcher, self.launcher_state))
            if state is NativeSubworkState.COMPLETED)


@dataclass(frozen=True, slots=True)
class SamplingUnitEvidence(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-sampling/unit-evidence"
    custody: DurableUnitEvidence
    conditional_calls: tuple[PortableCallCustody, ...]

    def __post_init__(self):
        if type(self.custody) is not DurableUnitEvidence or self.custody.conditional_calls:
            raise ValueError("sampling stream substitutes original complete custody")
        self.custody.__post_init__()
        definition = self.custody.definition
        names = tuple(row.call.object_id for row in self.conditional_calls)
        if names != tuple(sorted(set(names))):
            raise ValueError("sampling stream changes original conditional call census")
        for row in self.conditional_calls:
            if row.call_state is NativeSubworkState.UNKNOWN_COMPLETION:
                if row.call_definition is not None or row.operand_definition is not None or row.operand_state is not None:
                    raise ValueError("sampling stream manufactures an unknown call return")
                continue
            carrier = replace(definition, subwork_id=row.call.object_id + ".operand",
                operation_id="rubisco.durable-preparation.call-operand", roster_id=row.call.object_id + ".operand-roster",
                outputs=(json_output("call.operand", DurableNativeCallOperand),
                    json_output("files.census", DurableRawFileCensus), raw_output("files.raw")))
            call = row.call_definition
            if (row.call_state is not NativeSubworkState.COMPLETED or call is None or call.identity != row.call
                    or call.operation_id != "rubisco.durable-preparation.native-call"
                    or call.parent_contact != definition.parent_contact or call.sources != definition.sources
                    or call.code_sources_sha256 != definition.code_sources_sha256
                    or call.dependency_lock_sha256 != definition.dependency_lock_sha256
                    or row.operand_definition != carrier or type(row.operand_state) is not NativeSubworkState):
                raise ValueError("sampling stream substitutes its original call/operand/producing-source relation")

    @property
    def completed_children(self):
        return tuple(definition for row in self.conditional_calls for definition, state in (
            (row.operand_definition, row.operand_state), (row.call_definition, row.call_state))
            if definition is not None and state is NativeSubworkState.COMPLETED)


def _completed_calls(progress, definition):
    record_type = {"rubisco.chemical-force.unit": ChemicalForceReturn,
        "rubisco.nve-control.unit": NVEControlReturn}.get(definition.operation_id)
    if record_type is None:
        return ()
    raw = bytearray()
    for block in progress.iter_completed_output(definition, "unit.return"):
        raw.extend(block)
        if len(raw) > MAX_CONTROL_PLANE_JSON_BYTES:
            raise ValueError("sampling unit return exceeds its original bounded control envelope")
    returned = decode_canonical_bytes(bytes(raw), record_type, maximum_bytes=len(raw))
    if returned.unit_id != definition.subwork_id or returned.plan != definition.configuration:
        raise ValueError("sampling stream changes its original unit return/plan")
    calls = []
    for identity in returned.native_calls:
        prefix = definition.subwork_id + ".call."
        if not identity.object_id.startswith(prefix) or not identity.object_id[len(prefix):].isdigit():
            raise ValueError("sampling stream replaces an original conditional call identity")
        try:
            call = progress.resolve_completed_definition(identity)
        except NativeSubworkUncertainContact:
            calls.append(PortableCallCustody(identity, NativeSubworkState.UNKNOWN_COMPLETION, None, None, None))
            continue
        carrier = replace(definition, subwork_id=identity.object_id + ".operand",
            operation_id="rubisco.durable-preparation.call-operand", roster_id=identity.object_id + ".operand-roster",
            outputs=(json_output("call.operand", DurableNativeCallOperand),
                json_output("files.census", DurableRawFileCensus), raw_output("files.raw")))
        observed = progress.inspect(carrier)
        if observed.state is NativeSubworkState.COMPLETED and progress.resolve_completed_definition(carrier.identity) != carrier:
            raise ValueError("sampling stream substitutes the original completed operand carrier")
        calls.append(PortableCallCustody(identity, NativeSubworkState.COMPLETED, call, carrier, observed.state))
    return tuple(calls)


def emit_units(emitter, output_id, progress, census, definitions, *, launcher):
    """Export complete receipted originals; preserve every adverse/unknown slot."""
    metadata_id = "control.chemical-force.metadata" if type(census) is ChemicalForceCensus else "control.nve.metadata"
    by_id = {row.subwork_id: row for row in definitions}
    metadata = by_id[metadata_id]
    header = SamplingStreamHeader(census, definitions, metadata, progress.inspect(metadata).state,
        launcher, progress.inspect(launcher).state)
    writer = FrameWriter(emitter, output_id, record_type=SamplingUnitStreamChunk)
    writer.record(header)
    units = tuple(by_id[name] for name, state in census.states if state is NativeSubworkState.COMPLETED)
    for definition in (*header.completed_processes, *units):
        evidence = SamplingUnitEvidence(unit_evidence(progress, definition), _completed_calls(progress, definition))
        writer.record(evidence)
        for name, manifest in evidence.custody.transport_outputs:
            writer.output(progress, definition, name, manifest)
        for child in evidence.completed_children:
            child_evidence = SamplingUnitEvidence(unit_evidence(progress, child), ())
            writer.record(child_evidence)
            for name, manifest in child_evidence.custody.transport_outputs:
                writer.output(progress, child, name, manifest)


def authenticate_units(port, plan, *, implementation, source_root, on_chunk=None):
    """Independently verify complete frames and original return/call denominators."""
    from . import control_roster, nve_roster
    header, expected, children = None, (), ()
    evidence, outputs, output_index = None, (), 0
    buffer = bytearray()
    mode = "header"
    for _, descriptor, block, done in iter_verified_frames(port, record_type=SamplingUnitStreamChunk):
        schema, size, _ = descriptor
        if mode in {"header", "evidence"}:
            record_type = SamplingStreamHeader if mode == "header" else SamplingUnitEvidence
            if schema != record_type.SCHEMA or size > MAX_CONTROL_PLANE_JSON_BYTES:
                raise ValueError("sampling stream changes its bounded typed control records")
            buffer.extend(block)
            if not done:
                continue
            value = decode_canonical_bytes(bytes(buffer), record_type, maximum_bytes=size)
            buffer.clear()
            if mode == "header":
                header = value
                roster = control_roster if type(header.census) is ChemicalForceCensus else nve_roster
                if (header.census.plan != plan.identity or header.definitions != roster.definitions(plan, header.metadata.parent_contact,
                        sources=header.metadata.sources, input_materialization_ids=header.metadata.input_materialization_ids,
                        implementation=implementation, source_root=source_root)):
                    raise ValueError("sampling stream substitutes the exact original plan/full roster/current implementation")
                by_id = {row.subwork_id: row for row in header.definitions}
                expected = (*header.completed_processes,
                    *(by_id[name] for name, state in header.census.states if state is NativeSubworkState.COMPLETED))
            else:
                evidence = value
                if children:
                    if evidence.custody.definition != children[0] or evidence.conditional_calls:
                        raise ValueError("sampling stream changes an original conditional custody child")
                    children = children[1:]
                else:
                    if not expected or evidence.custody.definition != expected[0]:
                        raise ValueError("sampling stream changes the complete completed process/unit census")
                    expected = expected[1:]
                    children = evidence.completed_children
                outputs, output_index = evidence.custody.transport_outputs, 0
            mode = "output" if outputs else "evidence"
        else:
            name, manifest = outputs[output_index]
            if descriptor != (manifest.logical.payload_schema, manifest.materialization.size_bytes, manifest.materialization.physical_sha256):
                raise ValueError("sampling stream substitutes exact receipted original bytes/schema/size")
            if on_chunk is not None:
                on_chunk(evidence.custody, name, block, done)
            if name == "process.selection":
                if size > MAX_CONTROL_PLANE_JSON_BYTES:
                    raise ValueError("sampling process selection exceeds its original finite control envelope")
                buffer.extend(block)
                if done:
                    selection = decode_canonical_bytes(bytes(buffer), IsolatedNativeEntrySelection, maximum_bytes=size)
                    buffer.clear()
                    if launcher_definition(evidence.custody.definition, selection, evidence.custody.outputs) != header.launcher:
                        raise ValueError("sampling stream loses original selection/launcher input/receipt joins")
            if name == "unit.return" and evidence.custody.definition.operation_id in {
                    "rubisco.chemical-force.unit", "rubisco.nve-control.unit"}:
                if size > MAX_CONTROL_PLANE_JSON_BYTES:
                    raise ValueError("sampling return exceeds its original finite control envelope")
                buffer.extend(block)
                if done:
                    record_type = ChemicalForceReturn if evidence.custody.definition.operation_id == "rubisco.chemical-force.unit" else NVEControlReturn
                    returned = decode_canonical_bytes(bytes(buffer), record_type, maximum_bytes=size)
                    buffer.clear()
                    if (returned.plan != plan.identity or returned.unit_id != evidence.custody.definition.subwork_id
                            or returned.native_calls != tuple(row.call for row in evidence.conditional_calls)):
                        raise ValueError("sampling stream hides the original complete conditional call denominator")
            if done:
                output_index += 1
                if output_index == len(outputs):
                    outputs = ()
                    mode = "evidence"
    if header is None or mode != "evidence" or expected or children or buffer:
        raise ValueError("sampling stream omits complete original custody or final output frames")
    return header.census
