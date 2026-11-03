# SPDX-License-Identifier: MPL-2.0
"""Bounded native progress over the executor's existing request/ack pipe.

Guarded roots, manifests and entry tokens remain in the coordinator. The worker
receives a progress port, with durable acknowledgement before each native call.
This transport carries no scheduler, database or repeat-effect authority.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from hashlib import sha256
from multiprocessing.connection import Connection
import os
from pathlib import Path
from typing import BinaryIO, TYPE_CHECKING

from empirical_lawhood.infrastructure.artifact_stream_primitives import (
    STREAM_CHUNK_BYTES, _output_chunk_bound, _output_chunks,
)

if TYPE_CHECKING:
    from empirical_lawhood.infrastructure.native_subwork import ExternalNativeSubworkStore
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_inquiry import InquiryCost
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactManifest
from empirical_lawhood.runtime.execution import TaskContext
from empirical_lawhood.runtime.native_effects import NativeEntryRefused
from empirical_lawhood.runtime.native_subwork import (
    NativeSubworkDefinition, NativeSubworkInspection, NativeSubworkPartialOutput, NativeSubworkRoster, NativeSubworkState,
    NativeSubworkUncertainContact, NativeSubworkInputError, NativeSubworkInputMismatch,
)
from empirical_lawhood.runtime.prepared_native_invocation import PreparedInvocationContract, PreparedNativeWork


@dataclass(frozen=True, slots=True)
class NativeSubworkRequest:
    sequence: int
    operation: str
    arguments: tuple


@dataclass(frozen=True, slots=True)
class NativeSubworkReply:
    sequence: int
    value: object = None
    error_type: str | None = None
    error_message: str | None = None
    input_mismatches: tuple[NativeSubworkInputMismatch, ...] = ()


@dataclass(frozen=True, slots=True)
class _PipeEntry:
    definition: NativeSubworkDefinition
    handle: int
    owner: object


class PipeNativeSubworkProgress:
    """Worker-side protocol proxy; no stores or filesystem paths are composed."""

    def __init__(self, connection: Connection):
        self._connection = connection
        self._sequence = 0
        self._owner = object()

    def _call(self, operation: str, *arguments):
        self._sequence += 1
        sequence = self._sequence
        self._connection.send(NativeSubworkRequest(sequence, operation, arguments))
        reply = self._connection.recv()
        if type(reply) is not NativeSubworkReply or reply.sequence != sequence:
            raise ValueError("native subwork progress acknowledgement is out of sequence")
        if reply.error_type is not None:
            if reply.error_type == "NativeEntryRefused":
                raise NativeEntryRefused(reply.error_message or "current native entry refused")
            if reply.error_type == "NativeSubworkInputError" and reply.input_mismatches:
                if any(type(row) is not NativeSubworkInputMismatch for row in reply.input_mismatches):
                    raise ValueError("native subwork acknowledgement substitutes its input mismatch census")
                raise NativeSubworkInputError(reply.input_mismatches)
            exception = NativeSubworkUncertainContact if reply.error_type == "NativeSubworkUncertainContact" else ValueError
            raise exception(reply.error_message or "native subwork coordinator refused progress")
        return reply.value

    def _handle(self, entry) -> int:
        if type(entry) is not _PipeEntry or entry.owner is not self._owner:
            raise ValueError("native subwork pipe entry belongs to another worker")
        return entry.handle

    @property
    def parent_contact(self):
        return self._call("parent-contact")

    def inspect(self, definition: NativeSubworkDefinition) -> NativeSubworkInspection:
        return self._call("inspect", definition)

    def freeze_roster(self, roster: NativeSubworkRoster, parent_entry: _PipeEntry | None = None, *,
                      definitions: tuple[NativeSubworkDefinition, ...]) -> None:
        self._call("freeze-roster", roster, None if parent_entry is None else self._handle(parent_entry), definitions)

    def iter_inspections(self, definitions: Iterable[NativeSubworkDefinition]) -> Iterator[NativeSubworkInspection]:
        for definition in definitions:
            yield self.inspect(definition)

    def recover(self, definition: NativeSubworkDefinition) -> NativeSubworkInspection | None:
        return self._call("recover", definition)

    def resolve_completed_definition(self, identity: ObjectIdentity) -> NativeSubworkDefinition:
        return self._call("resolve-completed-definition", identity)

    def iter_completed_output(self, definition: NativeSubworkDefinition, output_id: str, *,
                              maximum_chunk_bytes: int = STREAM_CHUNK_BYTES) -> Iterator[bytes]:
        if type(maximum_chunk_bytes) is not int or maximum_chunk_bytes <= 0:
            raise ValueError("completed native output requires a positive integer chunk allowance")
        handle = self._call("completed-output-open", definition, output_id, maximum_chunk_bytes)
        try:
            while True:
                chunk = self._call("completed-output-next", handle)
                if chunk is None:
                    break
                if type(chunk) is not bytes or not chunk or len(chunk) > min(maximum_chunk_bytes, STREAM_CHUNK_BYTES):
                    raise ValueError("completed native output relay changes its bounded byte frame")
                yield chunk
        finally:
            self._call("completed-output-close", handle)

    def begin(self, definition: NativeSubworkDefinition,
              inputs: tuple[ArtifactManifest, ...] | None = None) -> _PipeEntry:
        return _PipeEntry(definition, self._call("begin", definition, inputs), self._owner)

    def contact(self, entry: _PipeEntry) -> None:
        self._call("contact", self._handle(entry))

    def call_entry(self, entry: _PipeEntry, *, at_utc: str) -> None:
        self._call("call-entry", self._handle(entry), at_utc)

    def call_return(self, entry: _PipeEntry, *, at_utc: str, error_type: str | None = None,
                    return_code: int | None = None) -> None:
        self._call("call-return", self._handle(entry), at_utc, error_type, return_code)

    def publish_output(self, entry: _PipeEntry, output_id: str, chunks: Iterable[bytes], *,
                       maximum_bytes: int, maximum_chunk_bytes: int = STREAM_CHUNK_BYTES,
                       expected_size_bytes: int | None = None,
                       expected_physical_sha256: str | None = None) -> ArtifactManifest:
        handle = self._handle(entry)
        chunk_bound = _output_chunk_bound(maximum_bytes, maximum_chunk_bytes,
            expected_size_bytes, expected_physical_sha256)
        self._call("output-open", handle, output_id, maximum_bytes, chunk_bound,
            expected_size_bytes, expected_physical_sha256)
        try:
            for chunk in _output_chunks(chunks, maximum_chunk_bytes, chunk_bound):
                self._call("output-chunk", handle, output_id, chunk)
        except BaseException:
            self._call("output-abort", handle, output_id)
            raise
        return self._call("output-close", handle, output_id)

    def complete(self, entry: _PipeEntry, *, operational_status: OperationalStatus,
                 cost: InquiryCost, cost_scope: str, consumed_streams: tuple[ObjectIdentity, ...] = (),
                 unconsumed_streams: tuple[ObjectIdentity, ...] = (), unknown_streams: tuple[ObjectIdentity, ...] = (),
                 peak_rss_bytes: int | None = None, reason_codes: tuple[str, ...] = ()) -> NativeSubworkInspection:
        return self._call("complete", self._handle(entry), operational_status, cost, cost_scope,
            consumed_streams, unconsumed_streams, unknown_streams, peak_rss_bytes, reason_codes)


@dataclass(slots=True)
class _OutputStage:
    path: Path
    stream: BinaryIO
    maximum_bytes: int
    maximum_chunk_bytes: int
    expected_size_bytes: int | None
    expected_physical_sha256: str | None
    written: int = 0


class NativeSubworkPipeService:
    """Coordinator progress for a live parent, or read-only completed assembly."""

    def __init__(self, store: ExternalNativeSubworkStore, context: TaskContext, scratch: Path, *,
                 completed_work: PreparedNativeWork | None = None):
        from empirical_lawhood.infrastructure.native_subwork import ExternalNativeSubworkStore
        if type(store) is not ExternalNativeSubworkStore:
            raise TypeError("native subwork pipe requires the actual guarded progress owner")
        parent = store.parent_contacts.read(context.run_id, context.task_id)
        if (parent is None or parent.attempt_id != context.attempt_id
                or parent.input_materialization_ids != context.input_materialization_ids
                or parent.dependency_receipt_ids != context.dependency_receipt_ids):
            raise NativeSubworkUncertainContact("native subwork pipe lacks its live scheduler-approved parent")
        if store.parent_contact != parent:
            raise ValueError("native subwork pipe store differs from its active parent task")
        self._completed = None
        if completed_work is None:
            if store.completed_only or not store.parent_contacts.is_live_creator(parent):
                raise NativeSubworkUncertainContact("native subwork pipe lacks its live scheduler-approved parent")
        else:
            from empirical_lawhood.infrastructure.native_parent_finalization import _authenticate_native_parent_return
            contract = context.prepared_invocation
            if (type(completed_work) is not PreparedNativeWork or not store.completed_only
                    or type(contract) is not PreparedInvocationContract or contract.native_work != completed_work):
                raise ValueError("completed-only native pipe changes its exact prepared invocation")
            contract.require_complete()
            contract.validate_context(context)
            self._completed = _authenticate_native_parent_return(store=store, work=completed_work)
        self._selected_definitions = ({} if self._completed is None else
            {row.definition.identity: row.definition for row in self._completed.inspections})
        self.store, self.parent, self.scratch = store, parent, scratch
        self._sequence = 0
        self._entries: dict[int, object] = {}
        self._entry_inputs: dict[ObjectIdentity, tuple[ArtifactManifest, ...]] = {}
        self._stages: dict[tuple[int, str], _OutputStage] = {}
        self._readers: dict[int, Iterator[bytes]] = {}
        self._next_reader = 0
        self._aborted: set[tuple[int, str]] = set()
        self._available_inputs = {manifest.materialization.materialization_id: manifest for manifest in store.parent_inputs}
        if tuple(sorted(self._available_inputs)) != parent.input_materialization_ids:
            raise ValueError("native subwork pipe lacks its exact coordinator-held parent input manifests")
        bindings = {binding.materialization_id: binding for binding in context.input_bindings}
        for materialization_id, manifest in self._available_inputs.items():
            binding = bindings[materialization_id]
            if (binding.artifact_id, binding.payload_schema, binding.media_type, binding.size_bytes,
                    binding.visibility_ceiling, binding.outcome_access) != (
                    manifest.logical.logical_artifact_id, manifest.logical.payload_schema,
                    manifest.logical.media_type, manifest.materialization.size_bytes,
                    manifest.logical.visibility_ceiling, manifest.logical.outcome_access):
                raise ValueError("native subwork parent manifest differs from actual worker input")
        self._next_handle = 0
        self._output_budget = context.resource_budget.output_bytes
        self.output_bytes = 0
        self.ordinary_output_bytes = 0

    def account_ordinary_output_bytes(self, size: int) -> bool:
        """One parent allowance covers both retained native and ordinary copies."""
        if type(size) is not int or size < 0:
            raise ValueError("ordinary output accounting requires an actual nonnegative byte count")
        if self._output_budget is not None and self.output_bytes + self.ordinary_output_bytes + size > self._output_budget:
            return False
        self.ordinary_output_bytes += size
        return True

    def _definition(self, definition) -> None:
        if type(definition) is not NativeSubworkDefinition or definition.parent_contact != self.parent:
            raise ValueError("native subwork pipe substitutes its active parent task")
        if self._completed is not None and self._selected_definitions.get(definition.identity) != definition:
            raise ValueError("completed-only native pipe substitutes its exact selected definition census")

    def _entry(self, handle):
        if type(handle) is not int or handle not in self._entries:
            raise ValueError("native subwork pipe uses another creator's entry")
        return self._entries[handle]

    def handle(self, request: NativeSubworkRequest, connection: Connection) -> None:
        if type(request) is not NativeSubworkRequest or request.sequence != self._sequence + 1:
            raise ValueError("native subwork progress request is out of sequence")
        self._sequence = request.sequence
        try:
            value = self._dispatch(request.operation, request.arguments)
        except Exception as error:  # noqa: BLE001 - refusal crosses the narrow worker pipe
            connection.send(NativeSubworkReply(request.sequence, error_type=type(error).__name__,
                error_message=str(error)[:512],
                input_mismatches=error.mismatches if type(error) is NativeSubworkInputError else ()))
            if type(error) is NativeEntryRefused:
                raise
            return
        connection.send(NativeSubworkReply(request.sequence, value))

    def _dispatch(self, operation, arguments):
        if self._completed is not None:
            self.store.plane.require_verification_snapshot()
            if self.store.parent_contact != self.parent:
                raise ValueError("completed-only native pipe changes its exact parent")
            if operation not in {"parent-contact", "freeze-roster", "inspect", "recover",
                    "resolve-completed-definition", "completed-output-open", "completed-output-next",
                    "completed-output-close"}:
                raise NativeSubworkUncertainContact("completed-only native pipe prohibits acquisition and mutation")
        if operation == "parent-contact":
            if arguments:
                raise ValueError("native subwork parent inspection takes no arguments")
            return self.parent
        if operation == "freeze-roster":
            roster, handle, definitions = arguments
            if type(roster) is not NativeSubworkRoster or roster.parent_contact != self.parent:
                raise ValueError("native subwork pipe substitutes its selected roster parent")
            if self._completed is not None:
                expected = tuple(self._selected_definitions[identity] for identity in roster.subworks
                    if identity in self._selected_definitions)
                if (handle is not None or roster not in self._completed.rosters or definitions != expected
                        or self.store.read_roster(self.parent, roster.roster_id) != roster):
                    raise NativeSubworkUncertainContact("completed-only native pipe cannot create or change a frozen roster")
                return None
            self.store.freeze_roster(roster, None if handle is None else self._entry(handle),
                definitions=definitions)
            return None
        if operation in ("inspect", "recover"):
            (definition,) = arguments
            self._definition(definition)
            return getattr(self.store, operation)(definition)
        if operation == "resolve-completed-definition":
            (identity,) = arguments
            if self._completed is not None and identity not in self._selected_definitions:
                raise ValueError("completed-only native pipe definition is outside its exact selected census")
            definition = self.store.resolve_completed_definition(identity)
            self._definition(definition)
            return definition
        if operation == "completed-output-open":
            definition, output_id, chunk_bound = arguments
            self._definition(definition)
            if type(chunk_bound) is not int or chunk_bound <= 0:
                raise ValueError("completed native output requires a positive integer chunk allowance")
            self.store._completed_output_manifest(definition, output_id)
            reader = self.store.iter_completed_output(definition, output_id, maximum_chunk_bytes=chunk_bound)
            self._next_reader += 1
            self._readers[self._next_reader] = reader
            return self._next_reader
        if operation == "completed-output-next":
            (handle,) = arguments
            if type(handle) is not int or handle not in self._readers:
                raise ValueError("completed native output relay uses no active reader")
            reader = self._readers[handle]
            try:
                return next(reader)
            except StopIteration:
                self._readers.pop(handle)
                return None
            except BaseException:
                self._readers.pop(handle)
                reader.close()
                raise
        if operation == "completed-output-close":
            (handle,) = arguments
            if type(handle) is not int or not 0 < handle <= self._next_reader:
                raise ValueError("completed native output relay uses another reader")
            reader = self._readers.pop(handle, None)
            if reader is not None:
                reader.close()
            return None
        if operation == "begin":
            definition, inputs = arguments
            self._definition(definition)
            available_inputs = dict(self._available_inputs)
            selected_parent = self.store._conditional_parents.get(definition.roster_id)
            if selected_parent is not None:
                self.store._entry(selected_parent)
                # A conditional parent already admitted these exact manifests.
                # Keep them scoped to its descendants, without promoting live
                # sibling publications to the task-wide completed-input pool.
                available_inputs.update((manifest.materialization.materialization_id, manifest)
                    for manifest in self._entry_inputs.get(selected_parent.definition.identity, ()))
                available_inputs.update((manifest.materialization.materialization_id, manifest)
                    for manifest in selected_parent.outputs.values())
            if not set(definition.input_materialization_ids).issubset(available_inputs):
                raise ValueError("native subwork pipe input is outside its frozen parent or completed child census")
            selected_inputs = tuple(available_inputs[value] for value in definition.input_materialization_ids)
            if inputs is not None and tuple(sorted(inputs, key=lambda value: value.materialization.materialization_id)) != selected_inputs:
                raise ValueError("native subwork pipe substitutes its coordinator-held input manifests")
            entry = self.store.begin(definition, selected_inputs)
            self._next_handle += 1
            handle = self._next_handle
            self._entries[handle] = entry
            self._entry_inputs[definition.identity] = selected_inputs
            return handle
        if operation == "contact":
            (handle,) = arguments
            self.store.contact(self._entry(handle))
            return None
        if operation == "call-entry":
            handle, at_utc = arguments
            self.store.call_entry(self._entry(handle), at_utc=at_utc)
            return None
        if operation == "call-return":
            handle, at_utc, error_type, return_code = arguments
            self.store.call_return(self._entry(handle), at_utc=at_utc, error_type=error_type,
                return_code=return_code)
            return None
        if operation == "output-open":
            handle, output_id, maximum_bytes, chunk_bound, size, digest = arguments
            entry = self._entry(handle)
            self.store._entry(entry)
            if output_id not in {port.output_id for port in entry.definition.outputs}:
                raise ValueError("native subwork output is outside its frozen port census")
            if chunk_bound != _output_chunk_bound(maximum_bytes, chunk_bound, size, digest):
                raise ValueError("native subwork output changes its stream contract")
            key = (handle, output_id)
            if key in self._stages or key in self._aborted or output_id in entry.outputs:
                raise ValueError("native subwork output is already entered")
            token = sha256((str(handle) + ":" + output_id).encode()).hexdigest()
            path = self.scratch / (".native-subwork." + token + ".partial")
            stream = path.open("xb")
            self._stages[key] = _OutputStage(path, stream, maximum_bytes, chunk_bound, size, digest)
            return None
        if operation == "output-abort":
            handle, output_id = arguments
            self._retain_stage((handle, output_id), "native-output-generator-aborted")
            return None
        if operation == "output-chunk":
            handle, output_id, chunk = arguments
            stage = self._stages[(handle, output_id)]
            self.store._entry(self._entry(handle))
            if type(chunk) is not bytes or len(chunk) > stage.maximum_chunk_bytes:
                raise ValueError("native subwork output chunk exceeds its transport bound")
            if stage.written + len(chunk) > stage.maximum_bytes:
                raise ValueError("native subwork output exceeds its selected complete byte census")
            if self._output_budget is not None and self.output_bytes + self.ordinary_output_bytes + len(chunk) > self._output_budget:
                raise ValueError("native subwork output exceeds its selected parent output allowance")
            stage.stream.write(chunk)
            stage.written += len(chunk)
            self.output_bytes += len(chunk)
            return None
        if operation == "output-close":
            handle, output_id = arguments
            key = (handle, output_id)
            stage = self._stages[key]
            stage.stream.flush()
            os.fsync(stage.stream.fileno())
            stage.stream.close()
            try:
                def chunks():
                    with stage.path.open("rb") as stream:
                        while chunk := stream.read(stage.maximum_chunk_bytes):
                            yield chunk
                manifest = self.store.publish_output(self._entry(handle), output_id, chunks(),
                    maximum_bytes=stage.maximum_bytes, maximum_chunk_bytes=stage.maximum_chunk_bytes,
                    expected_size_bytes=stage.expected_size_bytes,
                    expected_physical_sha256=stage.expected_physical_sha256)
            except BaseException:
                self._retain_stage(key, "native-output-publication-refused")
                raise
            else:
                stage.path.unlink(missing_ok=True)
                self._stages.pop(key)
                return manifest
        if operation == "complete":
            handle, status, cost, scope, consumed, unconsumed, unknown, peak, reasons = arguments
            if any(key[0] == handle for key in self._stages):
                raise ValueError("native subwork completion precedes its exact output stream publication")
            entry = self._entry(handle)
            inspection = self.store.complete(entry, operational_status=status, cost=cost,
                cost_scope=scope, consumed_streams=consumed, unconsumed_streams=unconsumed,
                unknown_streams=unknown, peak_rss_bytes=peak, reason_codes=reasons)
            if inspection.state is NativeSubworkState.COMPLETED:
                self._available_inputs.update((manifest.materialization.materialization_id, manifest)
                    for manifest in inspection.outputs)
                self._entries.pop(handle)
                self._entry_inputs.pop(entry.definition.identity)
            return inspection
        raise ValueError("native subwork pipe operation is outside its progress protocol")

    def close(self) -> None:
        """Keep received prefixes on loss; incomplete scientific outputs stay unknown."""
        first_error = None
        try:
            for key in tuple(self._stages):
                try:
                    self._retain_stage(key, "native-output-transport-interrupted")
                except Exception as error:  # noqa: PERF203 - close every interrupted transport
                    if first_error is None:
                        first_error = error
                    self._stages[key].stream.close()
        finally:
            for reader in self._readers.values():
                reader.close()
            self._readers.clear()
            self._entries.clear()
            self._entry_inputs.clear()
            if self._completed is None:
                self.store.parent_contacts.retire_live_creator(self.parent)
        if first_error is not None:
            raise first_error

    def _retain_stage(self, key, reason):
        stage = self._stages[key]
        if not stage.stream.closed:
            stage.stream.flush()
            os.fsync(stage.stream.fileno())
            stage.stream.close()
        digest = sha256()
        with stage.path.open("rb") as stream:
            while chunk := stream.read(STREAM_CHUNK_BYTES):
                digest.update(chunk)
        entry = self._entry(key[0])
        record = NativeSubworkPartialOutput(entry.definition.identity, self.store._contact_identity(entry),
            key[1], stage.maximum_bytes, stage.expected_size_bytes, stage.expected_physical_sha256,
            stage.written, digest.hexdigest(), (reason,))
        def chunks():
            with stage.path.open("rb") as stream:
                while chunk := stream.read(STREAM_CHUNK_BYTES):
                    yield chunk
        self.store.retain_partial_output(entry, record, chunks())
        stage.path.unlink(missing_ok=True)
        self._stages.pop(key)
        self._aborted.add(key)
