# SPDX-License-Identifier: MPL-2.0
"""Durable raw custody and selected launcher; no eager molecular imports."""

from dataclasses import dataclass, replace
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
import resource
import time
import traceback
import zlib

from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.recursive_inquiry import InquiryCost
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ReceiptCheck
from empirical_lawhood.runtime.isolated_native_subwork import IsolatedNativeEntryReturn, IsolatedNativeEntrySelection, IsolatedNativeProcessStart
from empirical_lawhood.runtime.native_subwork import NativeSubworkRoster, NativeSubworkState

from . import contracts as historical
from .durable_contracts import DurableNativeCallOperand, DurableNativeReturnWitness, DurableRawFileCensus, DurableUnitReturn
from .durable_roster import census, freeze, json_output, raw_output

CHUNK_BYTES = 1024 * 1024
RAW_MAGIC = b"EL-RUBISCO-NATIVE-FILES-1\n"


def file_chunks(path, *, expected=None, maximum_chunk_bytes=CHUNK_BYTES):
    """Use infrastructure-owned stable descriptors, bounded reads and exact SHA."""
    from empirical_lawhood.infrastructure.bounded_io import _open_regular, _regular_chunks, _stable_descriptor
    if type(maximum_chunk_bytes) is not int or not 0 < maximum_chunk_bytes <= CHUNK_BYTES:
        raise ValueError("raw native file read needs a bounded exact integer chunk size")
    descriptor, before = _open_regular(Path(path), maximum_bytes=None)
    digest = sha256()
    with _stable_descriptor(descriptor, before, operation="durable native raw publication"):
        for chunk in _regular_chunks(descriptor, before, maximum_bytes=before.st_size,
                chunk_bytes=maximum_chunk_bytes, opened_size_bound=True, operation="stream"):
            digest.update(chunk)
            yield chunk
        if expected is not None and (before.st_size != expected.byte_count
                or digest.hexdigest() != expected.sha256):
            raise ValueError("native file differs from complete selected byte census")


def directory_census(directory, root):
    rows = []
    # No symlink, FIFO, device or nested directory is silently omitted.
    for path in sorted(Path(directory).iterdir()):
        digest = sha256()
        size = 0
        for block in file_chunks(path):
            size += len(block)
            digest.update(block)
        rows.append(historical.FileEvidence(path.relative_to(root).as_posix(), size, digest.hexdigest()))
    return DurableRawFileCensus(tuple(rows))


def raw_archive_chunks(directory, root, selected_census, *, maximum_chunk_bytes=CHUNK_BYTES):
    """Lossless framed files; headers are typed and all original bytes survive."""
    header = selected_census.canonical_bytes()
    prefix = RAW_MAGIC + len(header).to_bytes(8, "big") + header
    for offset in range(0, len(prefix), maximum_chunk_bytes):
        yield prefix[offset:offset + maximum_chunk_bytes]
    for row in selected_census.files:
        yield from file_chunks(Path(root) / row.relative_path, expected=row,
                               maximum_chunk_bytes=maximum_chunk_bytes)
    if directory_census(directory, root) != selected_census:
        raise ValueError("native directory changed during complete raw publication")


def compressed_archive_chunks(directory, root, selected_census):
    compressor = zlib.compressobj(wbits=31)
    for chunk in raw_archive_chunks(directory, root, selected_census):
        compressed = compressor.compress(chunk)
        for offset in range(0, len(compressed), CHUNK_BYTES):
            yield compressed[offset:offset + CHUNK_BYTES]
    ending = compressor.flush()
    for offset in range(0, len(ending), CHUNK_BYTES):
        yield ending[offset:offset + CHUNK_BYTES]


def uncompressed_archive_chunks(chunks):
    decompressor = zlib.decompressobj(wbits=31)
    for chunk in chunks:
        pending = chunk
        while pending:
            returned = decompressor.decompress(pending, CHUNK_BYTES)
            pending = decompressor.unconsumed_tail
            if decompressor.unused_data:
                raise ValueError("raw native gzip appends undeclared bytes/members")
            if returned:
                yield returned
    while True:
        returned = decompressor.decompress(b"", CHUNK_BYTES)
        if not returned:
            break
        yield returned
    if not decompressor.eof or decompressor.unused_data:
        raise ValueError("raw native gzip omits complete original bytes/trailer")


def publish_record(progress, entry, output_id, record):
    raw = record.canonical_bytes()
    return progress.publish_output(entry, output_id,
        (raw[offset:offset + CHUNK_BYTES] for offset in range(0, len(raw), CHUNK_BYTES)),
        maximum_bytes=len(raw), expected_size_bytes=len(raw),
        expected_physical_sha256=sha256(raw).hexdigest())


def publish_directory(progress, entry, directory, root):
    selected = directory_census(directory, root)
    expected = sha256()
    size = 0
    for block in compressed_archive_chunks(directory, root, selected):
        size += len(block)
        expected.update(block)
    raw = progress.publish_output(entry, "files.raw", compressed_archive_chunks(directory, root, selected),
        maximum_bytes=size, maximum_chunk_bytes=CHUNK_BYTES, expected_size_bytes=size,
        expected_physical_sha256=expected.hexdigest())
    typed = publish_record(progress, entry, "files.census", selected)
    return selected, (raw, typed)


class _ChunkReader:
    def __init__(self, chunks):
        self.chunks = iter(chunks)
        self.buffer = b""

    def take(self, count):
        while len(self.buffer) < count:
            try:
                self.buffer += next(self.chunks)
            except StopIteration as error:
                raise ValueError("completed raw native file archive is truncated") from error
        result, self.buffer = self.buffer[:count], self.buffer[count:]
        return result

    def finish(self):
        if self.buffer or next(self.chunks, None) is not None:
            raise ValueError("raw native archive appends undeclared file bytes")


def copy_completed_geometry(progress, definition, directory):
    """Copy exact original completed geometry, never invoke its producer again."""
    from empirical_lawhood.infrastructure.bounded_io import MAX_CONTROL_PLANE_JSON_BYTES
    inspection = progress.recover(definition)
    if inspection is None or inspection.completion.operational_status is not OperationalStatus.SUCCEEDED:
        raise ValueError("model requires actual completed successful geometry custody")
    chunks = progress.iter_completed_output(definition, "files.raw", maximum_chunk_bytes=CHUNK_BYTES)
    reader = _ChunkReader(uncompressed_archive_chunks(chunks))
    try:
        if reader.take(len(RAW_MAGIC)) != RAW_MAGIC:
            raise ValueError("geometry recovery substitutes its raw file contract")
        header_size = int.from_bytes(reader.take(8), "big")
        # Metadata has its existing finite control envelope; raw files have no total ceiling.
        if not 0 < header_size <= MAX_CONTROL_PLANE_JSON_BYTES:
            raise ValueError("geometry recovery changes finite file-census envelope")
        raw = reader.take(header_size)
        selected = decode_canonical_bytes(raw, DurableRawFileCensus, maximum_bytes=header_size)
        typed_raw = b"".join(progress.iter_completed_output(definition, "files.census"))
        if raw != typed_raw:
            raise ValueError("geometry raw/header disagrees with exact completed typed census")
        for row in selected.files:
            path = Path(row.relative_path)
            if path.parts != (definition.subwork_id, path.name):
                raise ValueError("geometry recovery changes its actual unit path scope")
            digest = sha256()
            with (Path(directory) / path.name).open("xb") as stream:
                remaining = row.byte_count
                while remaining:
                    block = reader.take(min(remaining, CHUNK_BYTES))
                    stream.write(block)
                    digest.update(block)
                    remaining -= len(block)
            if digest.hexdigest() != row.sha256:
                raise ValueError("completed geometry differs from full original file bytes")
        reader.finish()
    finally:
        close = getattr(chunks, "close", None)
        if close is not None:
            close()
    return ObjectIdentity.from_record(inspection.receipt.receipt_id, inspection.receipt)


class DurableCallLedger:
    """Actual conditional calls publish raw returns before downstream guards."""

    def __init__(self, progress, plan, root, unit_entry, directory):
        self.progress, self.plan, self.root = progress, plan, Path(root)
        self.unit_entry, self.directory = unit_entry, Path(directory)
        self.calls, self.call_definitions, self.stack = [], [], []
        self.model_id = unit_entry.definition.subwork_id
        self.counter = 0
        self.current_parent = None
        self.request_projector = None
        self.returned_projector = None

    def call(self, role, request, function, *, realization=None, files=()):
        self.counter += 1
        call_id = self.model_id + ".call." + str(self.counter).zfill(6)
        parent_entry = self.stack[-1] if self.stack else self.unit_entry
        if self.request_projector is not None:
            request = {**request, **self.request_projector(role)}
        request_census = directory_census(self.directory, self.root)
        # Explicit caller operands must actually be present, never unbound summaries.
        if any(row not in request_census.files for row in files):
            raise ValueError("native request references absent/substituted complete file operands")
        operand = DurableNativeCallOperand(call_id, self.plan.identity,
            self.unit_entry.definition.identity,
            parent_entry.definition.identity if self.stack else None, role,
            json.dumps(request, sort_keys=True, separators=(",", ":")), request_census.files)
        base = self.unit_entry.definition
        carrier = replace(base, subwork_id=call_id + ".operand", operation_id="rubisco.durable-preparation.call-operand",
            roster_id=call_id + ".operand-roster", outputs=(json_output("call.operand", DurableNativeCallOperand),
                json_output("files.census", DurableRawFileCensus), raw_output("files.raw")))
        self.progress.freeze_roster(NativeSubworkRoster(carrier.roster_id, self.progress.parent_contact,
            (carrier.identity,), parent_subwork=parent_entry.definition.identity),
            parent_entry=parent_entry, definitions=(carrier,))
        carrier_entry = self.progress.begin(carrier)
        self.progress.contact(carrier_entry)
        operand_manifest = publish_record(self.progress, carrier_entry, "call.operand", operand)
        _, file_manifests = publish_directory(self.progress, carrier_entry, self.directory, self.root)
        definition = replace(base, subwork_id=call_id, operation_id="rubisco.durable-preparation.native-call",
            configuration=operand.identity, roster_id=call_id + ".roster",
            input_materialization_ids=tuple(sorted((*base.input_materialization_ids,
                operand_manifest.materialization.materialization_id,
                *(row.materialization.materialization_id for row in file_manifests)))),
            outputs=(json_output("call.return", historical.NativeCall),
                json_output("call.witness", DurableNativeReturnWitness),
                json_output("files.census", DurableRawFileCensus), raw_output("files.raw")))
        self.progress.freeze_roster(NativeSubworkRoster(definition.roster_id, self.progress.parent_contact,
            (definition.identity,), parent_subwork=carrier.identity), parent_entry=carrier_entry,
            definitions=(definition,))
        entry = self.progress.begin(definition)
        self.progress.contact(entry)
        self.call_definitions.append(definition)
        self.stack.append(entry)
        old_parent = self.current_parent
        self.current_parent = call_id
        wall, cpu = time.perf_counter(), time.process_time()
        child_before = resource.getrusage(resource.RUSAGE_CHILDREN)
        result, realized, error, returned = None, {}, None, False
        try:
            result = function()
            returned = True
        except Exception:
            error = traceback.format_exc()
        publish_record(self.progress, entry, "call.witness", DurableNativeReturnWitness(
            definition.identity, returned, type(result).__name__ if returned else None, error))
        if returned:
            try:
                realized = realization(result) if realization is not None else {"return_type": type(result).__name__}
                if self.returned_projector is not None:
                    realized = {**realized, **self.returned_projector(role, result)}
            except Exception:
                error = traceback.format_exc()
                realized = {"native_returned": True, "return_type": type(result).__name__,
                            "extraction_error_text": error}
        # Signals/lost children leave contact UNKNOWN. Only known return/errors complete.
        child_after = resource.getrusage(resource.RUSAGE_CHILDREN)
        wall_cost = Decimal(str(time.perf_counter() - wall))
        cpu_cost = Decimal(str(time.process_time() - cpu + child_after.ru_utime + child_after.ru_stime
                              - child_before.ru_utime - child_before.ru_stime))
        selected, _ = publish_directory(self.progress, entry, self.directory, self.root)
        row = historical.NativeCall(call_id, old_parent, self.model_id, role,
            operand.requested_json, json.dumps(realized, sort_keys=True, separators=(",", ":")),
            wall_cost, cpu_cost, "TECHNICAL_FAILURE" if error else "COMPLETED", error, selected.files)
        publish_record(self.progress, entry, "call.return", row)
        self.progress.complete(entry, operational_status=OperationalStatus.FAILED if error else OperationalStatus.SUCCEEDED,
            cost=InquiryCost(cpu_cost, wall_cost, None),
            cost_scope="Actual native call inclusive window; nested calls are contained, never sum twice; RSS unknown",
            reason_codes=(("known-native-return-extraction-error",) if returned else ("known-native-call-error",)) if error else ())
        self.progress.complete(carrier_entry, operational_status=OperationalStatus.SUCCEEDED,
            cost=InquiryCost(None, None, None), cost_scope="Actual operand publication; cost unmeasured, not free")
        self.calls.append(row)
        self.stack.pop()
        self.current_parent = old_parent
        if error is not None:
            raise RuntimeError("known native preparation call failed; original raw return/error retained\n" + error)
        return result


def complete_unit(progress, plan, entry, root, directory, ledger, *, succeeded, error=None,
                  geometry=None, geometry_receipt=None):
    selected, _ = publish_directory(progress, entry, directory, root)
    returned = DurableUnitReturn(entry.definition.subwork_id, plan.identity,
        geometry, geometry_receipt, True, succeeded,
        () if succeeded else ("known-preparation-error-or-missing-prerequisite",), selected.files,
        tuple(sorted((row.identity for row in ledger.call_definitions), key=lambda row: row.object_id)), error)
    publish_record(progress, entry, "unit.return", returned)
    return progress.complete(entry, operational_status=OperationalStatus.SUCCEEDED if succeeded else OperationalStatus.FAILED,
        cost=InquiryCost(None, None, None),
        cost_scope="Complete unit return; inclusive launcher cost separately measured, per-unit RSS/CPU/wall unknown",
        reason_codes=returned.reason_codes)


@dataclass(frozen=True, slots=True)
class DurablePreparationRunner:
    """Fresh-only selected composition; completed products use receipt-only recovery.

    A previous working directory is refused. This runner never resumes an old
    uncertain process; recover_unit remains available without launching a child.
    Public provider registration and physical preparation assessment are separate.
    """
    plan: object
    invocation_path: str
    selected_definitions: tuple
    environment: tuple[tuple[str, str], ...]
    output_ids: tuple[tuple[str, str], ...]
    census_output_id: str = "preparation.census"

    def execute(self, context):
        raise ValueError("durable preparation requires actual native progress and ordinary streaming")

    def _entry_target(self):
        path = Path(__file__).with_name("durable_native_entry.py")
        module = "empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_native_entry"
        return module, "selected_child", path, "src/" + module.replace(".", "/") + ".py"

    def execute_streaming_with_native_subwork(self, context, native_subwork, emitter, progress=None):
        from empirical_lawhood.infrastructure.isolated_native_subwork import run_isolated_native_entry, selected_environment_sha256
        from empirical_lawhood.infrastructure.numerical_provenance import numerical_observer_environment
        plan = self.plan
        selected = self.selected_definitions
        if (str(Path(plan.workdir)) != plan.workdir or native_subwork.parent_contact.task_id != context.task_id
                or any(row.parent_contact != native_subwork.parent_contact or row.configuration != plan.identity
                       for row in selected)):
            raise ValueError("durable preparation runner substitutes actual parent/plan")
        attempted = tuple(sorted((*plan.attempted_geometry_ids, *plan.attempted_model_ids)))
        if (tuple(unit_id for unit_id, _ in self.output_ids) != attempted
                or len(set(name for _, name in self.output_ids)) != len(self.output_ids)
                or self.census_output_id in {name for _, name in self.output_ids}):
            raise ValueError("durable preparation runner changes exact selected ordinary output ports")
        freeze(native_subwork, selected)
        root = Path(plan.workdir)
        root.mkdir(parents=True, exist_ok=False)
        environment = numerical_observer_environment(dict(self.environment))
        if environment.get("PYTHONDONTWRITEBYTECODE") != "1":
            raise ValueError("selected molecular child must disable bytecode writes")
        entry_module, entry_function, entry_source, entry_relative = self._entry_target()
        source_hash = sha256(entry_source.read_bytes()).hexdigest()
        if dict(plan.code_sources).get(entry_relative,
                dict(plan.code_sources).get(entry_relative.removeprefix("src/empirical_lawhood/"))) != source_hash:
            raise ValueError("selected molecular entry differs from the actual plan code-source binding")
        # Retain exact full invocation bytes before deriving the launcher. The
        # bridge then seals this authenticated copy before acknowledging entry.
        metadata_directory = root / "metadata"
        metadata_directory.mkdir()
        invocation = metadata_directory / "invocation.json"
        digest = sha256()
        with invocation.open("xb") as output:
            for chunk in file_chunks(Path(self.invocation_path)):
                output.write(chunk)
                digest.update(chunk)
        selection = IsolatedNativeEntrySelection("rubisco.durable-preparation.entry", plan.interpreter_path,
            plan.interpreter_sha256, entry_module, entry_function,
            str(entry_source), source_hash, str(invocation), digest.hexdigest(),
            selected_environment_sha256(environment))
        if context.prepared_invocation is not None:
            frozen = context.prepared_invocation.native_work
            if (frozen is None or frozen.isolated_selection is None or frozen.definitions != selected
                    or frozen.isolated_selection.invocation_path != self.invocation_path
                    or frozen.isolated_selection.invocation_sha256 != digest.hexdigest()):
                raise ValueError("durable preparation changes its original frozen specialist invocation/roster")
            selection = frozen.isolated_selection
        metadata = next(row for row in selected if row.subwork_id == "preparation.metadata")
        metadata_entry = native_subwork.begin(metadata)
        native_subwork.contact(metadata_entry)
        manifest = publish_record(native_subwork, metadata_entry, "process.selection", selection)
        _, invocation_manifests = publish_directory(native_subwork, metadata_entry, metadata_directory, root)
        lifecycle = replace(metadata, subwork_id="preparation.launch", operation_id="rubisco.durable-preparation.launch",
            configuration=selection.identity, roster_id="conditional.rubisco-preparation.launch",
            input_materialization_ids=tuple(sorted((*metadata.input_materialization_ids,
                manifest.materialization.materialization_id,
                *(row.materialization.materialization_id for row in invocation_manifests)))),
            outputs=(json_output("files.census", DurableRawFileCensus), raw_output("files.raw"),
                json_output("process.return", IsolatedNativeEntryReturn), json_output("process.start", IsolatedNativeProcessStart)))
        native_subwork.freeze_roster(NativeSubworkRoster(lifecycle.roster_id, native_subwork.parent_contact,
            (lifecycle.identity,), parent_subwork=metadata.identity), parent_entry=metadata_entry, definitions=(lifecycle,))
        launcher = native_subwork.begin(lifecycle)
        logs = root / "launcher"
        logs.mkdir()
        with (logs / "stdout.log").open("xb") as stdout, (logs / "stderr.log").open("xb") as stderr:
            returned = run_isolated_native_entry(selection, native_subwork, lifecycle_entry=launcher,
                start_output_id="process.start", return_output_id="process.return", environment=environment,
                cwd=root, stdout=stdout, stderr=stderr, prepared_contract=context.prepared_invocation,
                entry_preflight="preflight_selected_child")
        publish_directory(native_subwork, launcher, logs, root)
        native_subwork.complete(launcher, operational_status=OperationalStatus.SUCCEEDED if returned.returncode == 0 else OperationalStatus.FAILED,
            cost=InquiryCost(returned.inclusive_cpu_seconds, returned.wall_seconds, None),
            cost_scope="Actual isolated child+relay inclusive window; nested native calls contained, RSS unknown",
            reason_codes=() if returned.returncode == 0 else ("known-molecular-child-adverse-return",))
        retained_census = census(native_subwork, plan, selected)
        publish_record(native_subwork, metadata_entry, "preparation.census", retained_census)
        native_subwork.complete(metadata_entry, operational_status=OperationalStatus.SUCCEEDED,
            cost=InquiryCost(None, None, None), cost_scope="Selected launcher metadata and complete denominator; cost unmeasured")
        raw_census = retained_census.canonical_bytes()
        for offset in range(0, len(raw_census), CHUNK_BYTES):
            emitter.write(self.census_output_id, raw_census[offset:offset + CHUNK_BYTES])
        for unit_id, output_id in self.output_ids:
            definition = next(row for row in selected if row.subwork_id == unit_id)
            if native_subwork.inspect(definition).state is NativeSubworkState.COMPLETED:
                for chunk in native_subwork.iter_completed_output(definition, "files.raw", maximum_chunk_bytes=CHUNK_BYTES):
                    emitter.write(output_id, chunk)
        if not returned.handshake_completed or returned.returncode != 0:
            raise RuntimeError("selected molecular child adverse return; original launcher and unit census retained")
        return (ReceiptCheck("rubisco-durable-preparation-custody", True, ()),)
