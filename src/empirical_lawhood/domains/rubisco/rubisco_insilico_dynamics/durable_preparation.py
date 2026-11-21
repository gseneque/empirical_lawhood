# SPDX-License-Identifier: MPL-2.0
"""Durable raw custody and selected launcher; no eager molecular imports."""
from importlib.resources import files as _native_files
from contextlib import closing

from dataclasses import dataclass, replace
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
import resource
import time
import traceback
import zlib

from empirical_lawhood.science.inquiry.recursive_inquiry import InquiryCost
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.storage.contracts.artifacts import ReceiptCheck
from empirical_lawhood.execution.isolated_native_subwork import IsolatedNativeEntryReturn, IsolatedNativeEntrySelection, IsolatedNativeProcessStart
from empirical_lawhood.execution.native_subwork import NativeSubworkRoster, NativeSubworkState
from empirical_lawhood.execution.progress import progress_step

from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics import contracts as historical
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.durable_contracts import DurableNativeCallOperand, DurableNativeReturnWitness, DurableRawFileCensus, DurableUnitReturn
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.durable_roster import census, freeze, json_output, raw_output

CHUNK_BYTES = 1024 * 1024
RAW_MAGIC = b"EL-RUBISCO-NATIVE-FILES-1\n"


def file_chunks(path, *, expected=None, maximum_chunk_bytes=CHUNK_BYTES):
    """Use infrastructure-owned stable descriptors, bounded reads and exact SHA."""
    from empirical_lawhood.storage.bounded_io import _open_regular, _regular_chunks, _stable_descriptor
    if type(maximum_chunk_bytes) is not int or not 0 < maximum_chunk_bytes <= CHUNK_BYTES:
        raise ValueError("raw native file read needs a bounded exact integer chunk size")
    descriptor, before = _open_regular(Path(path), maximum_bytes=None)
    # The caller owns hashing when it only needs a bounded byte stream.
    # A selected expected census requires this independent exact-byte check.
    digest = sha256() if expected is not None else None
    with _stable_descriptor(descriptor, before, operation="durable native raw publication"), progress_step(
            "native.file-read", total=before.st_size, unit="bytes", detail=Path(path).name) as step:
        for chunk in _regular_chunks(descriptor, before, maximum_bytes=before.st_size,
                chunk_bytes=maximum_chunk_bytes, opened_size_bound=True, operation="stream"):
            if digest is not None:
                digest.update(chunk)
            step.advance(len(chunk))
            yield chunk
        if expected is not None and (before.st_size != expected.byte_count
                or digest.hexdigest() != expected.sha256):
            raise ValueError("native file differs from complete selected byte census")


def directory_census(directory, root):
    rows = []
    # No symlink, FIFO, device or nested directory is silently omitted.
    paths = sorted(Path(directory).iterdir())
    with progress_step("native.directory-census", total=len(paths), unit="files",
                       detail=Path(directory).name) as step:
        for path in paths:
            digest = sha256()
            size = 0
            for block in file_chunks(path):
                size += len(block)
                digest.update(block)
            rows.append(historical.FileEvidence(path.relative_to(root).as_posix(), size, digest.hexdigest()))
            step.advance()
    return DurableRawFileCensus(tuple(rows))


def raw_archive_chunks(root, selected_census, *, maximum_chunk_bytes=CHUNK_BYTES):
    """Frame exact selected files; the publication owner closes the directory.

    Each selected body is independently checked against its census while read.
    This codec does not establish a current complete directory population.
    """
    header = selected_census.canonical_bytes()
    prefix = RAW_MAGIC + len(header).to_bytes(8, "big") + header
    for offset in range(0, len(prefix), maximum_chunk_bytes):
        yield prefix[offset:offset + maximum_chunk_bytes]
    for row in selected_census.files:
        yield from file_chunks(Path(root) / row.relative_path, expected=row,
                               maximum_chunk_bytes=maximum_chunk_bytes)


def compressed_archive_chunks(root, selected_census):
    compressor = zlib.compressobj(wbits=31, memLevel=8)
    raw_size = len(RAW_MAGIC) + 8 + len(selected_census.canonical_bytes()) + sum(
        row.byte_count for row in selected_census.files)
    with progress_step("native.archive-compression", total=raw_size, unit="bytes") as step, closing(
            raw_archive_chunks(root, selected_census)) as source:
        for chunk in source:
            compressed = compressor.compress(chunk)
            step.advance(len(chunk))
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


def publish_directory(progress, entry, directory, root, *, selected_census):
    """Publish an already selected population and close its current originals."""
    if type(selected_census) is not DurableRawFileCensus:
        raise TypeError("raw native publication requires its typed selected file census")
    directory, root = Path(directory), Path(root)
    if (not root.is_absolute() or not directory.is_absolute()
            or root.resolve(strict=True) != root or directory.resolve(strict=True) != directory
            or not root.is_dir() or not directory.is_dir() or not directory.is_relative_to(root)):
        raise ValueError("raw native publication requires an ordinary directory within its selected root")
    selected = selected_census
    selected_parent = directory.relative_to(root).parts
    for row in selected.files:
        relative = PurePosixPath(row.relative_path)
        if (relative.is_absolute() or '..' in relative.parts or str(relative) != row.relative_path
                or relative.parts[:-1] != selected_parent):
            raise ValueError("raw native census selects a file outside its selected directory")
    # This derived deflate bound is a property of the selected exact input,
    # not a fixed workflow ceiling. The artifact plane owns the only staging
    # descriptor, actual size/hash, available-space policy and atomic commit.
    raw_size = len(RAW_MAGIC) + 8 + len(selected.canonical_bytes()) + sum(row.byte_count for row in selected.files)
    archive_bound = raw_size + (raw_size >> 12) + (raw_size >> 14) + (raw_size >> 25) + 25
    population_closed = False

    def selected_chunks():
        nonlocal population_closed
        yield from compressed_archive_chunks(root, selected)
        # Close after every compressed byte has reached the owned staging
        # writer, before successful publication. Failure cannot publish census.
        if directory_census(directory, root) != selected:
            raise ValueError("native directory changed before publication closing check")
        population_closed = True

    with closing(selected_chunks()) as chunks:
        raw = progress.publish_output(entry, "files.raw", chunks,
            maximum_bytes=archive_bound, maximum_chunk_bytes=min(CHUNK_BYTES, archive_bound))
        if not population_closed:
            raise ValueError("native archive publisher did not consume the complete selected population")
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
    from empirical_lawhood.execution.retained_native_records import decode_completed_record
    inspection = progress.recover(definition)
    if inspection is None or inspection.completion.operational_status is not OperationalStatus.SUCCEEDED:
        raise ValueError("model requires actual completed successful geometry custody")
    selected, typed_raw = decode_completed_record(progress, definition, "files.census", DurableRawFileCensus)
    chunks = progress.iter_completed_output(definition, "files.raw", maximum_chunk_bytes=CHUNK_BYTES)
    reader = _ChunkReader(uncompressed_archive_chunks(chunks))
    try:
        if reader.take(len(RAW_MAGIC)) != RAW_MAGIC:
            raise ValueError("geometry recovery substitutes its raw file contract")
        header_size = int.from_bytes(reader.take(8), "big")
        # The receipted typed census supplies the exact expected header length.
        # A hostile/inconsistent 64-bit length cannot cause a speculative read.
        if header_size != len(typed_raw):
            raise ValueError("geometry raw/header disagrees with exact completed typed census")
        for offset in range(0, header_size, CHUNK_BYTES):
            if reader.take(min(CHUNK_BYTES, header_size-offset)) != typed_raw[offset:offset+CHUNK_BYTES]:
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
        with progress_step("native.durable-call", total=3, unit="phases", detail=role) as call_step:
            operand_started, operand_cpu_started = time.perf_counter(), time.process_time()
            operand_children = resource.getrusage(resource.RUSAGE_CHILDREN)
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
            _, file_manifests = publish_directory(self.progress, carrier_entry, self.directory, self.root, selected_census=request_census)
            operand_children_done = resource.getrusage(resource.RUSAGE_CHILDREN)
            operand_cost = InquiryCost(
                Decimal(str(time.process_time() - operand_cpu_started + operand_children_done.ru_utime
                            + operand_children_done.ru_stime - operand_children.ru_utime - operand_children.ru_stime)),
                Decimal(str(time.perf_counter() - operand_started)), None)
            call_step.advance()
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
                with progress_step("native.engine-call", detail=role):
                    result = function()
                returned = True
            except Exception:
                error = traceback.format_exc()
            call_step.advance()
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
            selected, _ = publish_directory(self.progress, entry, self.directory, self.root, selected_census=directory_census(self.directory, self.root))
            row = historical.NativeCall(call_id, old_parent, self.model_id, role,
                operand.requested_json, json.dumps(realized, sort_keys=True, separators=(",", ":")),
                wall_cost, cpu_cost, "TECHNICAL_FAILURE" if error else "COMPLETED", error, selected.files)
            publish_record(self.progress, entry, "call.return", row)
            self.progress.complete(entry, operational_status=OperationalStatus.FAILED if error else OperationalStatus.SUCCEEDED,
                cost=InquiryCost(cpu_cost, wall_cost, None),
                cost_scope="Actual native call inclusive window; nested calls are contained, never sum twice; RSS unknown",
                reason_codes=(("known-native-return-extraction-error",) if returned else ("known-native-call-error",)) if error else ())
            self.progress.complete(carrier_entry, operational_status=OperationalStatus.SUCCEEDED,
                cost=operand_cost, cost_scope="Actual request census and operand publication inclusive window; nested cost is not additive")
            call_step.advance()
            self.calls.append(row)
            self.stack.pop()
            self.current_parent = old_parent
            if error is not None:
                raise RuntimeError("known native preparation call failed; original raw return/error retained\n" + error)
            return result

def complete_unit(progress, plan, entry, root, directory, ledger, *, succeeded, error=None,
                  geometry=None, geometry_receipt=None):
    selected, _ = publish_directory(progress, entry, directory, root, selected_census=directory_census(directory, root))
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
        path = Path(str(_native_files("empirical_lawhood.adapters.rubisco.rubisco_insilico_dynamics").joinpath("durable_native_entry.py")))
        module = "empirical_lawhood.adapters.rubisco.rubisco_insilico_dynamics.durable_native_entry"
        return module, "selected_child", path, "src/" + module.replace(".", "/") + ".py"

    def execute_streaming_with_native_subwork(self, context, native_subwork, emitter, progress=None):
        from empirical_lawhood.execution.local.isolated_native_subwork import run_isolated_native_entry, selected_environment_sha256
        from empirical_lawhood.storage.numerical_provenance import numerical_observer_environment
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
        _, invocation_manifests = publish_directory(native_subwork, metadata_entry, metadata_directory, root, selected_census=directory_census(metadata_directory, root))
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
        publish_directory(native_subwork, launcher, logs, root, selected_census=directory_census(logs, root))
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
