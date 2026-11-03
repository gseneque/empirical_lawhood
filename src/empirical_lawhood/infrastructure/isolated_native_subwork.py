# SPDX-License-Identifier: MPL-2.0
"""An isolated selected engine delegates progress to the existing coordinator.

This POSIX inherited-descriptor bridge runs inside the admitted worker and
inherits its resource placement. No stores, creator tokens or root paths move
to the selected engine. Full native outputs use the existing bounded output
frames; complete metadata records retain their selected census.
"""

from dataclasses import dataclass, replace
from decimal import Decimal
from hashlib import sha256
import importlib
import importlib.util
import json
from multiprocessing import Pipe
from multiprocessing.connection import Connection
import os
from pathlib import Path
import re
import resource
import stat
import subprocess
import sys
import time

from empirical_lawhood.infrastructure.native_subwork_ipc import (
    NativeSubworkReply, NativeSubworkRequest, PipeNativeSubworkProgress,
)
from empirical_lawhood.infrastructure.bounded_io import _open_regular, _regular_chunks, _stable_descriptor
from empirical_lawhood.infrastructure.artifact_stream_primitives import (
    _anonymous_input_descriptor, _PreopenedBoundedReader, _seal_anonymous_input,
)
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.isolated_native_subwork import IsolatedNativeEntryReturn, IsolatedNativeEntrySelection, IsolatedNativeInvocation, IsolatedNativeProcessStart
from empirical_lawhood.runtime.native_effects import NativeEffectContact, NativeEntryRefused
from empirical_lawhood.runtime.native_subwork import (
    NativeSubworkInputError, NativeSubworkObservationPublicationError, native_call_utc_now,
)


def selected_environment_sha256(environment):
    if type(environment) is not dict or any(type(k) is not str or type(v) is not str for k, v in environment.items()):
        raise ValueError("isolated native entry requires its exact string environment")
    return sha256(json.dumps(environment, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()


def materialize_isolated_invocation(path, chunks, *, expected_size_bytes, expected_sha256):
    """Retain exact operational invocation bytes at the explicitly selected path.

    Existing identical metadata can be checked again without native replay.
    Different bytes, links and partial metadata are refused rather than replaced.
    """
    from empirical_lawhood.kernel.serialization import validate_sha256
    validate_sha256(expected_sha256)
    target = Path(path)
    if (not target.is_absolute() or ".." in target.parts
            or type(expected_size_bytes) is not int or expected_size_bytes < 0):
        raise ValueError("isolated invocation requires its explicit complete operational destination")
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.parent.resolve() != target.parent:
        raise ValueError("isolated invocation destination substitutes a parent directory link")
    try:
        descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    except FileExistsError:
        descriptor, before = _open_regular(target, maximum_bytes=expected_size_bytes)
        digest, size = sha256(), 0
        with _stable_descriptor(descriptor, before, operation="selected invocation metadata reuse"):
            for chunk in _regular_chunks(descriptor, before, maximum_bytes=expected_size_bytes,
                    chunk_bytes=1024 * 1024, opened_size_bound=True, operation="selected invocation metadata reuse"):
                size += len(chunk)
                digest.update(chunk)
        if (size, digest.hexdigest()) != (expected_size_bytes, expected_sha256):
            raise ValueError("isolated invocation refuses different or partial retained metadata")
        return
    digest, size = sha256(), 0
    with os.fdopen(descriptor, "wb") as output:
        for chunk in chunks:
            if type(chunk) is not bytes or len(chunk) > 1024 * 1024:
                raise ValueError("isolated invocation requires bounded immutable byte frames")
            size += len(chunk)
            if size > expected_size_bytes:
                raise ValueError("isolated invocation exceeds its selected complete bytes")
            digest.update(chunk)
            output.write(chunk)
        if (size, digest.hexdigest()) != (expected_size_bytes, expected_sha256):
            raise ValueError("isolated invocation changes its selected complete bytes")
        output.flush()
        os.fsync(output.fileno())


def _file_sha256(path, *, allow_symlink=False):
    selected = Path(path).resolve() if allow_symlink else Path(path)
    descriptor, before = _open_regular(selected, maximum_bytes=None)
    digest = sha256()
    with _stable_descriptor(descriptor, before, operation="isolated selected file hashing"):
        for chunk in _regular_chunks(descriptor, before, maximum_bytes=before.st_size,
                chunk_bytes=1024 * 1024, opened_size_bound=True, operation="isolated selected file hashing"):
            digest.update(chunk)
    return digest.hexdigest()


def _verify_selection(selection, environment):
    if type(selection) is not IsolatedNativeEntrySelection:
        raise TypeError("isolated native entry requires its immutable selected contract")
    selection.__post_init__()
    for path, expected, allow_symlink in ((selection.interpreter_path, selection.interpreter_sha256, True),
                           (selection.entry_source_path, selection.entry_source_sha256, False),
                           (selection.invocation_path, selection.invocation_sha256, False)):
        if _file_sha256(path, allow_symlink=allow_symlink) != expected:
            raise ValueError("isolated native selected interpreter/source/invocation changed")
    if selected_environment_sha256(environment) != selection.environment_sha256:
        raise ValueError("isolated native selected environment changed")


@dataclass(frozen=True, slots=True)
class _Handshake:
    selection: ObjectIdentity
    parent: NativeEffectContact
    actual_interpreter_sha256: str
    actual_entry_source_sha256: str
    actual_invocation_sha256: str
    actual_environment_sha256: str


def _launch_selected_entry(selection, child, *, environment, cwd, stdout, stderr):
    """The existing selected interpreter transport, shared with diagnostic Stop."""
    return subprocess.Popen([selection.interpreter_path, "-c",
        "from empirical_lawhood.infrastructure.isolated_native_subwork import _main\n_main()",
        "--selected-native-entry-fd", str(child.fileno())], cwd=cwd, env=environment,
        stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
        pass_fds=(child.fileno(),))


def _receive_prepared_ready(connection, selection, prepared_contract):
    """Require the actual selected child, then its complete no-effect readiness."""
    from empirical_lawhood.runtime.prepared_native_invocation import WorkerPreflightResult

    limit = prepared_contract.resource_budget.wall_time_seconds
    if limit is not None and not connection.poll(float(limit)):
        raise TimeoutError("isolated selected child did not report readiness within its task budget")
    value = connection.recv()
    handshaken = False
    if type(value) is _Handshake:
        expected = _Handshake(selection.identity, prepared_contract.expected_parent_contact,
            selection.interpreter_sha256, selection.entry_source_sha256,
            selection.invocation_sha256, selection.environment_sha256)
        if value != expected:
            raise ValueError("isolated selected child changes its actual selection or full anticipated parent")
        handshaken = True
        value = connection.recv()
    if type(value) is not WorkerPreflightResult or value.invocation != prepared_contract.identity:
        raise ValueError("isolated selected child changes its exact prepared readiness binding")
    if value.ready:
        if not handshaken:
            raise ValueError("isolated selected child readiness lacks its actual selected handshake")
        if (value.environment != prepared_contract.environment or value.native_work != prepared_contract.native_work
                or (value.producing_provenance.package_sources, value.producing_provenance.code_sources_sha256,
                    value.producing_provenance.dependency_lock_sha256, value.producing_provenance.observed_git_head)
                != (prepared_contract.implementation.package_sources, prepared_contract.implementation.code_sources_sha256,
                    prepared_contract.implementation.dependency_lock_sha256, prepared_contract.implementation.observed_git_head)):
            raise ValueError("isolated selected child changes its complete prepared source, environment or native work")
    return value


def preflight_isolated_native_entry(selection, *, prepared_contract, entry_preflight,
                                   environment, cwd, stdout, stderr, provenance_requirements=(),
                                   prefix_selected=True):
    """Exercise the actual selected child and Stop, without progress or contact.

    Outer input descriptors remain authenticated lineage. The child separately
    checks the sealed invocation and installed domain's complete embedded joins.
    No native progress port, local process witness or completion is available.
    """
    from empirical_lawhood.infrastructure.execution import _WorkerProceed
    from empirical_lawhood.runtime.prepared_native_invocation import PreparedInvocationContract

    if type(prepared_contract) is not PreparedInvocationContract:
        raise TypeError("isolated readiness requires the exact original prepared task contract")
    if type(prefix_selected) is not bool:
        raise ValueError("isolated prefix observation requires its explicit diagnostic disposition")
    selection.__post_init__()
    coordinator, child = Pipe(duplex=True)
    process = None
    try:
        process = _launch_selected_entry(selection, child, environment=environment,
            cwd=cwd, stdout=stdout, stderr=stderr)
        child.close()
        coordinator.send((selection, prepared_contract.expected_parent_contact,
            prepared_contract, entry_preflight, tuple(provenance_requirements), prefix_selected))
        result = _receive_prepared_ready(coordinator, selection, prepared_contract)
        coordinator.send(_WorkerProceed(prepared_contract.identity, False))
        process.wait()
        return result
    finally:
        coordinator.close()
        child.close()
        if process is not None and process.poll() is None:
            process.kill()
            process.wait()


def prepare_isolated_native_work(selection, *, prepared_contract, entry_preflight,
                                environment, cwd, stdout, stderr, provenance_requirements=()):
    """Retain mechanical observed environment selection in the existing work.

    Returned diagnostics are operational evidence. Only the sole unselected
    prefix mismatch may be adopted; actual execution always repeats a bound gate.
    """
    from empirical_lawhood.infrastructure.execution import WorkerPreflightError
    from empirical_lawhood.runtime.prepared_native_invocation import PreparedWorkerEnvironment

    work = prepared_contract.native_work
    if work is None:
        raise ValueError("isolated preparation requires its original typed initial native work")
    if work.isolated_selection is not None:
        if (work.isolated_selection != selection
                or work.isolated_environment.selected_environment != tuple(sorted(environment.items()))):
            raise ValueError("isolated preparation changes its frozen selection/full environment")
        selected_contract = replace(prepared_contract, environment=work.isolated_environment,
            native_work=replace(work, isolated_diagnostics=()))
        ready = preflight_isolated_native_entry(selection, prepared_contract=selected_contract,
            entry_preflight=entry_preflight, environment=environment, cwd=cwd, stdout=stdout,
            stderr=stderr, provenance_requirements=provenance_requirements)
        if not ready.ready:
            raise WorkerPreflightError(ready)
        return work, (ready,)
    initial_environment = PreparedWorkerEnvironment(selection.interpreter_path, selection.interpreter_sha256,
        prepared_contract.environment.prefix, tuple(sorted(environment.items())))
    initial_contract = replace(prepared_contract, environment=initial_environment)
    observed = preflight_isolated_native_entry(selection, prepared_contract=initial_contract,
        entry_preflight=entry_preflight, environment=environment, cwd=cwd, stdout=stdout,
        stderr=stderr, provenance_requirements=provenance_requirements, prefix_selected=False)
    if tuple(row.operand_id for row in observed.mismatches) != ("worker.prefix",):
        raise WorkerPreflightError(observed)
    selected = replace(work, isolated_selection=selection, isolated_environment=observed.environment)
    selected_contract = replace(prepared_contract, native_work=selected, environment=observed.environment)
    ready = preflight_isolated_native_entry(selection, prepared_contract=selected_contract,
        entry_preflight=entry_preflight, environment=environment, cwd=cwd, stdout=stdout,
        stderr=stderr, provenance_requirements=provenance_requirements)
    if not ready.ready:
        raise WorkerPreflightError(ready)
    return replace(selected, isolated_diagnostics=(observed, ready)), (observed, ready)


def _seal_invocation(selection):
    """One stable source read, full bounded copy/hash, then kernel immutability."""
    copied = _anonymous_input_descriptor()
    try:
        descriptor, before = _open_regular(Path(selection.invocation_path), maximum_bytes=None)
        digest = sha256()
        with _stable_descriptor(descriptor, before, operation="selected invocation copy"):
            for chunk in _regular_chunks(descriptor, before, maximum_bytes=before.st_size,
                    chunk_bytes=1024 * 1024, opened_size_bound=True, operation="selected invocation copy"):
                digest.update(chunk)
                offset = 0
                while offset < len(chunk):
                    written = os.write(copied, memoryview(chunk)[offset:])
                    if written <= 0:
                        raise OSError("selected invocation copy made no progress")
                    offset += written
        if digest.hexdigest() != selection.invocation_sha256:
            raise ValueError("selected invocation changed before its immutable snapshot")
        os.lseek(copied, 0, os.SEEK_SET)
        _seal_anonymous_input(copied)
        return IsolatedNativeInvocation(selection.identity, before.st_size, digest.hexdigest(),
            _PreopenedBoundedReader(copied, maximum_bytes=before.st_size))
    except BaseException:
        os.close(copied)
        raise


def _local_process_witness_directory(cwd):
    """Only the caller's selected working directory receives operational facts."""
    root = Path(cwd).resolve(strict=True)
    descriptor = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        if not stat.S_ISDIR(os.fstat(descriptor).st_mode):
            raise ValueError("isolated native local witness requires its selected working directory")
        for name in ("isolated-native-process-start.json", "isolated-native-process-return.json"):
            try:
                os.stat(name, dir_fd=descriptor, follow_symlinks=False)
            except FileNotFoundError:
                continue
            raise FileExistsError("isolated native local witness refuses previous observations or replay")
        return root, descriptor
    except BaseException:
        os.close(descriptor)
        raise


def _process_identity_before_acknowledgement(pid):
    raw = Path(f"/proc/{pid}/stat").read_text()
    fields = raw[raw.rfind(")") + 2:].split()
    return dict(pid=pid, start_time_ticks=int(fields[19]), parent_pid=int(fields[1]),
        process_group_id=int(fields[2]), session_id=int(fields[3]),
        pid_namespace=os.readlink(f"/proc/{pid}/ns/pid"),
        mount_namespace=os.readlink(f"/proc/{pid}/ns/mnt"))


def _retain_local_process_witness(directory, name, record, *, root, process_identity, lifecycle_entry, owner_source):
    """Fsync exact typed observations before IPC; confer no unit completion."""
    value = dict(schema="empirical-lawhood/infrastructure/isolated-native-local-process-witness.v1",
        record_schema=record.SCHEMA, canonical_record=record.canonical_bytes().decode(),
        lifecycle_definition_identity=lifecycle_entry.definition.identity.canonical_bytes().decode(),
        process_identity=process_identity, process_identity_known=process_identity is not None,
        selected_working_directory=str(root), owner_source=owner_source,
        observed_time_ns=time.time_ns(), scientific_receipt=False, nested_completion_inferred=False,
        replay_authority=False)
    raw = (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode()
    descriptor = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=directory)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    os.fsync(directory)


def run_isolated_native_entry(selection, native_subwork, *, lifecycle_entry, start_output_id, return_output_id,
                              environment, cwd, stdout, stderr, prepared_contract=None,
                              entry_preflight=None, provenance_requirements=()):
    """Bridge one selected child; never infer nested completion or replay it.

The domain entry receives `(native_subwork, immutable_invocation_port)`. It must freeze
its own complete scientific operands and acknowledge contact before effects.
    The caller freezes and begins a lifecycle entry with a declared process-start
    port. A complete prepared contract gates contact on actual selected-child
    readiness. Legacy calls retain their original contact-before-launch behavior.
    The actual process locator is published before
    acknowledging the child. The caller retains complete stdout/stderr through its selected streams and
publishes them before scientific return guards. A known child return cannot
complete a contacted nested unit lacking its own exact receipt.
    Local operational start/return witnesses in the selected working directory
    survive a lost coordinator pipe. They retain the existing typed records and
    actual PID/start join; they neither complete a unit nor grant replay.
"""
    if type(native_subwork) is not PipeNativeSubworkProgress:
        raise TypeError("isolated native entry requires the actual admitted worker progress port")
    if os.name != "posix" or not sys.platform.startswith("linux"):
        raise ValueError("selected isolated native profile requires Linux inherited descriptors and sealed invocation")
    _verify_selection(selection, environment)
    parent = native_subwork.parent_contact
    if prepared_contract is not None:
        from empirical_lawhood.runtime.prepared_native_invocation import PreparedInvocationContract
        if type(prepared_contract) is not PreparedInvocationContract or parent != prepared_contract.expected_parent_contact:
            raise ValueError("isolated native entry changes its full prepared actual parent")
        selected = prepared_contract.native_work
        if selected is not None and selected.isolated_selection is not None:
            if selected.isolated_selection != selection:
                raise ValueError("isolated native entry changes its frozen selected child")
            prepared_contract = replace(prepared_contract, environment=selected.isolated_environment)
    outputs = {row.output_id: row for row in lifecycle_entry.definition.outputs}
    expected = ((start_output_id, IsolatedNativeProcessStart), (return_output_id, IsolatedNativeEntryReturn))
    if (lifecycle_entry.definition.parent_contact != parent
            or lifecycle_entry.definition.configuration != selection.identity
            or len({row[0] for row in expected}) != 2
            or any(output_id not in outputs or outputs[output_id].payload_schema != record.SCHEMA
                or outputs[output_id].profile is not ArtifactProfile.CANONICAL_JSON
                or outputs[output_id].media_type != "application/json" for output_id, record in expected)):
        raise ValueError("isolated native lifecycle changes its frozen selection, actual parent or start/return ports")
    owner_source = dict(path=str(Path(__file__).resolve()), sha256=_file_sha256(__file__))
    witness_root = witness_directory = None
    if prepared_contract is None:
        witness_root, witness_directory = _local_process_witness_directory(cwd)
    coordinator, child = Pipe(duplex=True)
    started = time.perf_counter()
    start_cpu = time.process_time()
    before_children = resource.getrusage(resource.RUSAGE_CHILDREN)
    process = None
    process_identity = None
    handshake_completed = False
    requests = 0
    bridge_error = None
    phase = "contact"
    lifecycle_contacted = False
    call_entered = False
    returned_at_utc = None
    try:
        if prepared_contract is None:
            lifecycle_contacted = True
            native_subwork.contact(lifecycle_entry)
        phase = "process-start" if prepared_contract is None else "prepared-readiness"
        process = _launch_selected_entry(selection, child, environment=environment,
            cwd=cwd, stdout=stdout, stderr=stderr)
        child.close()
        if prepared_contract is not None:
            from empirical_lawhood.infrastructure.execution import _WorkerProceed, WorkerPreflightError
            coordinator.send((selection, parent, prepared_contract, entry_preflight, tuple(provenance_requirements)))
            readiness = _receive_prepared_ready(coordinator, selection, prepared_contract)
            if not readiness.ready:
                coordinator.send(_WorkerProceed(prepared_contract.identity, False))
                process.wait()
                raise WorkerPreflightError(readiness)
            handshake_completed = True
            witness_root, witness_directory = _local_process_witness_directory(cwd)
            phase = "contact"
            lifecycle_contacted = True
            native_subwork.contact(lifecycle_entry)
        phase = "process-start-publication"
        namespace_path = Path("/proc/self/ns/pid")
        started_record = IsolatedNativeProcessStart(selection.identity, parent, process.pid, os.getpid(),
            os.getpgid(process.pid), os.readlink(namespace_path) if namespace_path.is_symlink() else None)
        process_identity = _process_identity_before_acknowledgement(process.pid)
        _retain_local_process_witness(witness_directory, "isolated-native-process-start.json", started_record,
            root=witness_root, process_identity=process_identity, lifecycle_entry=lifecycle_entry, owner_source=owner_source)
        phase = "process-start-publication"
        raw_start = started_record.canonical_bytes()
        native_subwork.publish_output(lifecycle_entry, start_output_id, iter((raw_start,)),
            maximum_bytes=len(raw_start), expected_size_bytes=len(raw_start),
            expected_physical_sha256=sha256(raw_start).hexdigest())
        phase = "handshake"
        if prepared_contract is None:
            coordinator.send((selection, parent))
            try:
                handshake = coordinator.recv()
            except EOFError as error:
                raise ValueError("isolated native child closed before its selected entry handshake") from error
            expected = _Handshake(selection.identity, parent, selection.interpreter_sha256,
                selection.entry_source_sha256, selection.invocation_sha256, selection.environment_sha256)
            if type(handshake) is not _Handshake or handshake != expected:
                raise ValueError("isolated native child substitutes its selected entry or active parent")
            handshake_completed = True
            coordinator.send(True)
        else:
            try:
                native_subwork.call_entry(lifecycle_entry, at_utc=native_call_utc_now())
            except NativeEntryRefused:
                raise
            except Exception as error:
                raise NativeSubworkObservationPublicationError(
                    "isolated native call entry observation publication was not acknowledged") from error
            call_entered = True
            coordinator.send(_WorkerProceed(prepared_contract.identity, True))
        if handshake_completed:
            phase = "progress-bridge"
            while True:
                try:
                    request = coordinator.recv()
                except EOFError:
                    break
                if (type(request) is not NativeSubworkRequest or type(request.sequence) is not int
                        or request.sequence != requests + 1 or type(request.operation) is not str
                        or type(request.arguments) is not tuple):
                    raise ValueError("isolated native progress request is out of sequence")
                requests += 1
                try:
                    value = native_subwork._call(request.operation, *request.arguments)
                except Exception as error:  # noqa: BLE001 - exact coordinator refusal crosses its existing narrow protocol
                    reply = NativeSubworkReply(request.sequence, error_type=type(error).__name__,
                        error_message=str(error)[:512],
                        input_mismatches=error.mismatches if type(error) is NativeSubworkInputError else ())
                else:
                    reply = NativeSubworkReply(request.sequence, value)
                coordinator.send(reply)
        phase = "process-return"
        returncode = process.wait()
        returned_at_utc = native_call_utc_now()
    except BaseException as error:
        bridge_error = error
        if process is not None:
            if process.poll() is None:
                # Reap only this owned direct child. Its known return does not
                # resolve any contacted nested unit or authorize replay.
                process.kill()
            returncode = process.wait()
            returned_at_utc = native_call_utc_now()
    finally:
        coordinator.close()
        child.close()
    if process is None or not lifecycle_contacted:
        if witness_directory is not None:
            os.close(witness_directory)
        assert bridge_error is not None
        bridge_error.isolated_native_phase = phase
        raise bridge_error
    if call_entered:
        try:
            native_subwork.call_return(lifecycle_entry, at_utc=returned_at_utc,
                return_code=returncode)
        except Exception as error:
            if witness_directory is not None:
                os.close(witness_directory)
            raise NativeSubworkObservationPublicationError(
                "isolated native raw process return observation publication was not acknowledged") from error
    after_children = resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu = time.process_time() - start_cpu + after_children.ru_utime + after_children.ru_stime - before_children.ru_utime - before_children.ru_stime
    returned = IsolatedNativeEntryReturn(selection.identity, returncode, handshake_completed, requests,
        Decimal(str(time.perf_counter() - started)), Decimal(str(cpu)))
    raw_return = returned.canonical_bytes()
    try:
        return_phase = "process-return-local-retention"
        _retain_local_process_witness(witness_directory, "isolated-native-process-return.json", returned,
            root=witness_root, process_identity=process_identity, lifecycle_entry=lifecycle_entry, owner_source=owner_source)
        return_phase = "process-return-publication"
        native_subwork.publish_output(lifecycle_entry, return_output_id, iter((raw_return,)),
            maximum_bytes=len(raw_return), expected_size_bytes=len(raw_return),
            expected_physical_sha256=sha256(raw_return).hexdigest())
    except BaseException as error:
        # These observations are available to a controlled diagnostic consumer
        # even when its publication path failed. They confer no completion.
        error.isolated_native_phase = return_phase
        error.isolated_native_entry_return = returned
        error.isolated_native_bridge_error = bridge_error
        raise
    finally:
        os.close(witness_directory)
    if bridge_error is not None:
        bridge_error.isolated_native_phase = phase
        bridge_error.isolated_native_entry_return = returned
        raise bridge_error
    return returned


def _load_selected_module(selection):
    spec = importlib.util.find_spec(selection.entry_module)
    if spec is None or spec.origin is None or Path(spec.origin).resolve() != Path(selection.entry_source_path).resolve():
        raise ValueError("isolated native child resolves another entry source")
    source_snapshot = Path(spec.origin).read_bytes()
    if sha256(source_snapshot).hexdigest() != selection.entry_source_sha256:
        raise ValueError("isolated native source changed before entry")
    # Execute authenticated source rather than a timestamp-valid stale .pyc.
    module = importlib.util.module_from_spec(spec)
    sys.modules[selection.entry_module] = module
    exec(compile(source_snapshot, spec.origin, "exec", dont_inherit=True), module.__dict__)
    parent_module, _, child_name = selection.entry_module.rpartition(".")
    if parent_module:
        setattr(sys.modules[parent_module], child_name, module)
    return module


def _prepared_selected_child(connection, selection, parent, contract, entry_preflight, requirements,
                             prefix_selected=True):
    """The actual specialist child reports readiness before progress exists."""
    from empirical_lawhood.infrastructure.execution import _WorkerProceed
    from empirical_lawhood.infrastructure.numerical_provenance import observe_prepared_worker
    from empirical_lawhood.runtime.prepared_native_invocation import (
        PreparedInvocationContract, PreparedNativeWork, WorkerPreflightMismatch, WorkerPreflightResult,
    )

    if type(contract) is not PreparedInvocationContract:
        raise TypeError("selected child requires its exact original prepared contract")
    mismatches = []
    invocation = sealed_invocation = module = native_work = None

    def check(operand_id, callback):
        try:
            return callback()
        except Exception as error:  # noqa: BLE001 - collect independent selected prerequisites
            mismatches.append(WorkerPreflightMismatch(operand_id, str(error) or type(error).__name__))
            return None

    def validate_scope():
        contract.require_complete()
        if (not contract.native_effect or parent != contract.expected_parent_contact
                or (contract.environment.interpreter_path, contract.environment.interpreter_sha256)
                    != (selection.interpreter_path, selection.interpreter_sha256)
                or contract.environment.selected_environment != tuple(sorted(os.environ.items()))):
            raise ValueError("specialist changes its full original task/parent or selected interpreter/environment scope")
        if contract.native_work is None:
            raise ValueError("specialist lacks its exact selected typed native work")
        if contract.native_work.isolated_selection is not None and (
                contract.native_work.isolated_selection != selection
                or contract.native_work.isolated_environment != contract.environment):
            raise ValueError("specialist changes its frozen selected child/environment pair")

    check("specialist.scope", validate_scope)
    check("specialist.selection", lambda: _verify_selection(selection, dict(os.environ)))
    def validate_interpreter():
        if _file_sha256(sys.executable, allow_symlink=True) != selection.interpreter_sha256:
            raise ValueError("isolated selected child uses another actual interpreter")
    check("specialist.interpreter", validate_interpreter)
    try:
        invocation = sealed_invocation = check("specialist.invocation", lambda: _seal_invocation(selection))
        if invocation is not None:
            invocation = check("specialist.binding", lambda: replace(invocation, prepared_invocation=contract))
        module = check("specialist.entry", lambda: _load_selected_module(selection))
        if type(entry_preflight) is not str or re.fullmatch(r"[A-Za-z_]\w*", entry_preflight) is None:
            mismatches.append(WorkerPreflightMismatch("specialist.preparer",
                "SOFTWARE: installed PURE specialist preparation hook is unavailable"))
        elif module is not None and invocation is not None:
            def prepare():
                callback = getattr(module, entry_preflight, None)
                if not callable(callback):
                    raise ValueError("SOFTWARE: installed PURE specialist preparation hook is unavailable")
                cursor = invocation.cursor()
                try:
                    selected = callback(invocation=cursor, expected_parent=parent, prepared_contract=contract)
                finally:
                    cursor.close()
                if type(selected) is not PreparedNativeWork:
                    raise ValueError("specialist preparer must return its exact typed native work")
                selected.__post_init__()
                if selected != contract.native_work or selected.expected_parent != contract.expected_parent_contact:
                    raise ValueError("specialist changes the complete selected native definition/operand census")
                return selected
            native_work = check("specialist.work", prepare)
        provenance, environment, observed = observe_prepared_worker(contract, requirements, prefix_selected=prefix_selected)
        mismatches.extend(observed)
        result = WorkerPreflightResult(contract.identity, provenance, environment,
            tuple(sorted(set(mismatches), key=lambda row: (row.operand_id, row.reason))), native_work)
        if not any(row.operand_id in {"specialist.selection", "specialist.interpreter",
                "specialist.invocation", "specialist.entry", "specialist.binding"} for row in mismatches):
            connection.send(_Handshake(selection.identity, parent,
                _file_sha256(sys.executable, allow_symlink=True),
                _file_sha256(selection.entry_source_path), invocation.content_sha256,
                selected_environment_sha256(dict(os.environ))))
        connection.send(result)
        acknowledgement = connection.recv()
        if (type(acknowledgement) is not _WorkerProceed or acknowledgement.invocation != contract.identity):
            raise ValueError("specialist lacks its exact prepared acknowledgement")
        if not acknowledgement.proceed:
            return
        if not result.ready or not prefix_selected:
            raise ValueError("specialist cannot execute a refused prepared invocation")
        progress = PipeNativeSubworkProgress(connection)
        if progress.parent_contact != parent:
            raise ValueError("specialist changes its full actual entered parent")
        if _file_sha256(selection.entry_source_path) != selection.entry_source_sha256:
            raise ValueError("specialist source changed before acknowledged entry")
        getattr(module, selection.entry_function)(progress, invocation)
    finally:
        if sealed_invocation is not None:
            sealed_invocation.close()


def _selected_child(fd):
    connection = Connection(fd)
    invocation = None
    try:
        operands = connection.recv()
        if type(operands) is tuple and len(operands) in (5, 6):
            _prepared_selected_child(connection, *operands)
            return
        selection, parent = operands
        if type(parent) is not NativeEffectContact:
            raise ValueError("isolated native child requires its actual entered parent")
        _verify_selection(selection, dict(os.environ))
        if _file_sha256(sys.executable, allow_symlink=True) != selection.interpreter_sha256:
            raise ValueError("isolated native child uses another actual interpreter")
        spec = importlib.util.find_spec(selection.entry_module)
        if spec is None or spec.origin is None or Path(spec.origin).resolve() != Path(selection.entry_source_path).resolve():
            raise ValueError("isolated native child resolves another entry source")
        invocation = _seal_invocation(selection)
        connection.send(_Handshake(selection.identity, parent, _file_sha256(sys.executable, allow_symlink=True),
            _file_sha256(spec.origin), invocation.content_sha256, selected_environment_sha256(dict(os.environ))))
        if connection.recv() is not True:
            raise ValueError("isolated native child lacks its parent entry acknowledgement")
        progress = PipeNativeSubworkProgress(connection)
        if progress.parent_contact != parent:
            raise ValueError("isolated native child substitutes its active parent")
        module = _load_selected_module(selection)
        getattr(module, selection.entry_function)(progress, invocation)
    finally:
        if invocation is not None:
            invocation.close()
        connection.close()


def _main():
    if len(sys.argv) != 3 or sys.argv[1] != "--selected-native-entry-fd":
        raise SystemExit("explicit selected isolated-native descriptor required")
    _selected_child(int(sys.argv[2]))


if __name__ == "__main__":
    _main()
