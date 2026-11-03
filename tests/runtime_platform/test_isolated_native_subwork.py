# SPDX-License-Identifier: MPL-2.0
"""Selected second interpreter shares actual progress; no domain native imports."""

from dataclasses import replace
from contextlib import contextmanager
from decimal import Decimal
from hashlib import sha256
import importlib.machinery
import json
import os
from pathlib import Path
import py_compile
import signal
import struct
import subprocess
import sys
import tracemalloc

import pytest

from empirical_lawhood.adapters.methods.isolated_native_conformance import ExposedIsolatedNativeRunner, exposed_metadata_definition
from empirical_lawhood.infrastructure.execution import LocalProcessExecutor, TaskProcessError
from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
from empirical_lawhood.infrastructure.native_subwork import ExternalNativeSubworkStore
from empirical_lawhood.infrastructure.native_subwork_ipc import NativeSubworkPipeService, NativeSubworkRequest, PipeNativeSubworkProgress
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.recursive_inquiry import InquiryCost
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.isolated_native_subwork import IsolatedNativeEntryReturn, IsolatedNativeEntrySelection
from empirical_lawhood.runtime.isolated_native_subwork import IsolatedNativeProcessStart
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.native_subwork import NativeSubworkOutput, NativeSubworkRoster, NativeSubworkState, NativeSubworkUncertainContact
from empirical_lawhood.runtime.prepared_native_invocation import PreparedNativeWork, PreparedWorkerEnvironment
from tests.runtime_platform.test_native_subwork import _process_context, _selected
from tests.runtime_platform.test_worker_preflight import _case


def fixture_case(tmp_path, phase):
    store, first, inputs = _selected(tmp_path, freeze=False)
    definitions = (first, replace(first, subwork_id="forecast.three"), replace(first, subwork_id="forecast.two"))
    root = tmp_path / "selected-child"
    root.mkdir()
    payload = "{\"outcome\":\"UNEVALUABLE\"}\n" * 100_000
    invocation = root / "invocation.json"
    invocation.write_text(json.dumps({"definitions": [row.canonical_bytes().decode() for row in definitions],
        "phase": phase, "payload": payload}))
    context = _process_context(store, first, inputs)
    return store, definitions, context, root, invocation, payload.encode()


@contextmanager
def prepared_bridge_case(tmp_path, return_code):
    """One actual prepared launcher, with its own task, inputs and source census.

    The selected child only returns a disclosed process code. This exercises
    real source/preflight/IPC custody, without a scientific native engine.
    """
    from empirical_lawhood.infrastructure import isolated_native_subwork as bridge
    plane, bundle, _runner, context, contract, parent = _case(tmp_path, actual=True, native=True)
    root = tmp_path / "prepared-selected-child"
    root.mkdir()
    source = root / "prepared_transport_entry.py"
    source.write_text('''import json
import sys

def preflight_selected_child(*, invocation, expected_parent, prepared_contract):
    data = json.loads(invocation.read())
    if (set(data) != {"return_code"} or type(data["return_code"]) is not int
            or expected_parent != prepared_contract.expected_parent_contact):
        raise ValueError("disclosed child substitutes its original invocation or parent")
    return prepared_contract.native_work

def selected_child(progress, invocation):
    data = json.loads(invocation.read())
    if progress.parent_contact != invocation.prepared_invocation.expected_parent_contact:
        raise ValueError("disclosed child substitutes its actual coordinator parent")
    if data["return_code"]:
        sys.exit(data["return_code"])
''')
    invocation = root / "invocation.json"
    invocation.write_text(json.dumps({"return_code": return_code}, sort_keys=True))
    environment = dict(contract.environment.selected_environment)
    environment.update(PYTHONPATH=os.pathsep.join((str(Path(__file__).resolve().parents[2] / "src"), str(root))),
        PYTHONDONTWRITEBYTECODE="1")
    selected_environment = PreparedWorkerEnvironment(contract.environment.interpreter_path,
        contract.environment.interpreter_sha256, contract.environment.prefix, tuple(sorted(environment.items())))
    selection = IsolatedNativeEntrySelection("exposed.prepared.entry", selected_environment.interpreter_path,
        selected_environment.interpreter_sha256, source.stem, "selected_child", str(source),
        sha256(source.read_bytes()).hexdigest(), str(invocation), sha256(invocation.read_bytes()).hexdigest(),
        bridge.selected_environment_sha256(environment))
    metadata = replace(contract.native_definitions[0], subwork_id="engine.metadata", streams=(),
        operation_id="exposed.prepared.metadata", outputs=(NativeSubworkOutput("process.selection",
            IsolatedNativeEntrySelection.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json"),))
    roster = NativeSubworkRoster("selected.native-subwork", parent, (metadata.identity,))
    contract = replace(contract, environment=selected_environment,
        native_work=PreparedNativeWork(parent, ("exposed.launcher",), ("exposed.process",),
            (metadata,), (roster,), selection, selected_environment))
    contract.require_complete()
    context = replace(context, prepared_invocation=contract)
    contacts = ExternalNativeEffectContactStore(plane=plane, execution_plan=parent.execution_plan,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE)
    contacts.begin(parent)
    store = ExternalNativeSubworkStore(plane=plane, parent_contacts=contacts, parent_contact=parent,
        parent_inputs=bundle.manifests, prepared_invocation=contract)
    store.freeze_roster(roster, definitions=(metadata,))
    service = NativeSubworkPipeService(store, context, tmp_path)
    class Connection:
        def send(self, message):
            if type(message) is NativeSubworkRequest:
                service.handle(message, self)
            else:
                self.reply = message
        def recv(self):
            return self.reply
    progress = PipeNativeSubworkProgress(Connection())
    metadata_entry = progress.begin(metadata)
    progress.contact(metadata_entry)
    raw_selection = selection.canonical_bytes()
    selection_manifest = progress.publish_output(metadata_entry, "process.selection", (raw_selection,),
        maximum_bytes=len(raw_selection), expected_size_bytes=len(raw_selection),
        expected_physical_sha256=sha256(raw_selection).hexdigest())
    definition = replace(metadata, subwork_id="engine.launch", operation_id="exposed.prepared.launch",
        configuration=selection.identity, roster_id="conditional.prepared.launch",
        input_materialization_ids=tuple(sorted((*metadata.input_materialization_ids,
            selection_manifest.materialization.materialization_id))),
        outputs=(NativeSubworkOutput("process.return", IsolatedNativeEntryReturn.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, "application/json"),
            NativeSubworkOutput("process.start", IsolatedNativeProcessStart.SCHEMA,
                ArtifactProfile.CANONICAL_JSON, "application/json")))
    progress.freeze_roster(NativeSubworkRoster(definition.roster_id, parent, (definition.identity,), metadata.identity),
        parent_entry=metadata_entry, definitions=(definition,))
    entry = progress.begin(definition)
    try:
        with (root / "stdout.log").open("xb") as stdout, (root / "stderr.log").open("xb") as stderr:
            returned = bridge.run_isolated_native_entry(selection, progress, lifecycle_entry=entry,
                start_output_id="process.start", return_output_id="process.return", environment=environment,
                cwd=root, stdout=stdout, stderr=stderr, prepared_contract=contract,
                entry_preflight="preflight_selected_child")
        progress.complete(entry,
            operational_status=OperationalStatus.SUCCEEDED if return_code == 0 else OperationalStatus.FAILED,
            cost=InquiryCost(returned.inclusive_cpu_seconds, returned.wall_seconds, Decimal(0)),
            cost_scope="Actual disclosed prepared process and relay; no scientific native acquisition",
            reason_codes=() if return_code == 0 else ("disclosed-process-adverse-return",))
        progress.complete(metadata_entry, operational_status=OperationalStatus.SUCCEEDED,
            cost=InquiryCost(None, None, None), cost_scope="Derived selection metadata; nested process window separate")
        yield store, definition, context, contract, returned, progress, service
    finally:
        service.close()
        bundle.close()


@pytest.mark.parametrize("return_code", (0, 17))
def test_actual_prepared_process_retains_invocation_bound_entry_and_raw_return(tmp_path, return_code):
    from tests.runtime_platform.test_native_subwork import _store
    with prepared_bridge_case(tmp_path, return_code) as (store, definition, _context, contract, returned, _progress, _service):
        retained = store.inspect(definition)
        assert returned.handshake_completed and returned.returncode == return_code
        assert retained.call_entry.invocation == contract.identity
        assert retained.call_return.error_type is None and retained.call_return.return_code == return_code
        assert retained.call_entry.entered_at_utc.endswith("Z") and retained.call_return.returned_at_utc.endswith("Z")
        assert retained.completion.operational_status is (
            OperationalStatus.SUCCEEDED if return_code == 0 else OperationalStatus.FAILED)
        fresh = _store(store.plane, store.parent_contact, store.parent_inputs)
        assert fresh.recover(definition) == retained
        raw = b"".join(fresh.iter_completed_output(definition, "process.return"))
        assert decode_canonical_bytes(raw, IsolatedNativeEntryReturn, maximum_bytes=len(raw)) == returned


@pytest.mark.parametrize("phase,state,returncode", [
    ("success", NativeSubworkState.COMPLETED, 0),
    ("before-begin", NativeSubworkState.NOT_ENTERED, 91),
    ("before-contact", NativeSubworkState.BEGUN, 92),
    ("after-contact", NativeSubworkState.UNKNOWN_COMPLETION, 93),
    ("after-publication", NativeSubworkState.UNKNOWN_COMPLETION, 94),
    ("after-completion", NativeSubworkState.COMPLETED, 95),
])
def test_actual_selected_interpreter_retains_nested_states_without_replay(tmp_path, phase, state, returncode):
    store, definitions, context, root, invocation, payload = fixture_case(tmp_path, phase)
    executor = LocalProcessExecutor(scratch_root=store.plane.root)
    runner = ExposedIsolatedNativeRunner(str(invocation), str(root))
    try:
        if returncode:
            with pytest.raises(TaskProcessError) as failure:
                executor.execute(runner, context, timeout_seconds=None, native_subwork=store)
            assert failure.value.sanitized_exception_type == "RuntimeError"
        else:
            result = executor.execute(runner, context, timeout_seconds=None, native_subwork=store)
            assert result.checks[0].passed
    finally:
        for port in context.input_ports:
            port.close()
    raw = (root / "child-return.json").read_bytes()
    returned = decode_canonical_bytes(raw, IsolatedNativeEntryReturn, maximum_bytes=len(raw))
    assert returned.handshake_completed and returned.returncode == returncode
    assert returned.progress_requests >= 3
    assert returned.peak_rss_bytes is None
    local_start = json.loads((root / "isolated-native-process-start.json").read_bytes())
    local_return = json.loads((root / "isolated-native-process-return.json").read_bytes())
    assert local_return["canonical_record"].encode() == raw
    assert local_return["process_identity"] == local_start["process_identity"]
    assert local_return["process_identity_known"]
    assert local_start["process_identity"]["start_time_ticks"] > 0
    assert not local_return["scientific_receipt"] and not local_return["nested_completion_inferred"]
    assert not local_return["replay_authority"]
    lifecycle, = store.iter_roster_definitions(definitions[0].parent_contact, "conditional.isolated.engine")
    assert lifecycle.subwork_id == "engine.launch"
    lifecycle_inspection = store.recover(lifecycle)
    assert lifecycle_inspection.completion is not None
    assert lifecycle_inspection.call_entry is None and lifecycle_inspection.call_return is None
    raw_start = b"".join(store.iter_completed_output(lifecycle, "process.start"))
    started = decode_canonical_bytes(raw_start, IsolatedNativeProcessStart, maximum_bytes=len(raw_start))
    assert started.parent_contact == definitions[0].parent_contact
    assert started.selection == returned.selection
    assert started.child_pid != started.creator_pid and started.process_group_id == started.creator_pid
    assert b"".join(store.iter_completed_output(lifecycle, "process.return")) == raw
    metadata = exposed_metadata_definition(definitions[0])
    raw_selection = b"".join(store.iter_completed_output(metadata, "process.selection"))
    selection = decode_canonical_bytes(raw_selection, IsolatedNativeEntrySelection, maximum_bytes=len(raw_selection))
    assert selection.identity == returned.selection
    assert lifecycle.configuration == selection.identity
    assert store.read_roster(definitions[0].parent_contact, lifecycle.roster_id).parent_subwork == metadata.identity
    assert store.inspect(definitions[0]).state is state
    assert all(store.inspect(row).state is NativeSubworkState.NOT_ENTERED for row in definitions[1:])
    if state is NativeSubworkState.COMPLETED:
        before = store.recover(definitions[0])
        assert b"".join(store.iter_completed_output(definitions[0], definitions[0].outputs[0].output_id)) == payload
        assert before.outputs[0].logical.content_sha256 == sha256(payload).hexdigest()
        assert store.recover(definitions[0]) == before
    elif state is NativeSubworkState.UNKNOWN_COMPLETION:
        with pytest.raises(NativeSubworkUncertainContact):
            store.recover(definitions[0])


@pytest.mark.parametrize("wrong", ["interpreter_sha256", "entry_source_sha256", "invocation_sha256", "environment_sha256", "lifecycle_selection"])
def test_selected_byte_or_environment_substitution_refuses_before_child_entry(tmp_path, wrong):
    store, definitions, context, root, invocation, _ = fixture_case(tmp_path, "success")
    try:
        with pytest.raises(TaskProcessError) as failure:
            LocalProcessExecutor(scratch_root=store.plane.root).execute(
                ExposedIsolatedNativeRunner(str(invocation), str(root), wrong), context,
                timeout_seconds=None, native_subwork=store)
        assert failure.value.sanitized_exception_type == "ValueError"
    finally:
        for port in context.input_ports:
            port.close()
    assert not (root / "child-return.json").exists()
    assert all(store.inspect(row).state is NativeSubworkState.NOT_ENTERED for row in definitions)
    assert (root / "child.stdout").read_bytes() == b""
    assert (root / "child.stderr").read_bytes() == b""
    lifecycle, = store.iter_roster_definitions(definitions[0].parent_contact, "conditional.isolated.engine")
    assert store.inspect(lifecycle).state is NativeSubworkState.BEGUN


def test_selected_source_executes_authenticated_bytes_despite_valid_stale_bytecode(tmp_path):
    store, definitions, context, root, invocation, _ = fixture_case(tmp_path, "success")
    source = root / "selected_exposed_entry.py"
    old_source = ('from pathlib import Path\nMARKER = "stale"\n'
        'def exposed_child(progress, invocation):\n'
        '    Path("selected-source-marker").write_text(MARKER)\n')
    source.write_text(old_source)
    original = source.stat()
    cache = Path(py_compile.compile(str(source), doraise=True))
    source.write_text(old_source.replace('"stale"', '"fresh"'))
    os.utime(source, ns=(original.st_atime_ns, original.st_mtime_ns))
    # This is a real timestamp/size-valid stale cache that normal loading accepts.
    assert struct.unpack("<II", cache.read_bytes()[8:16]) == (int(source.stat().st_mtime), source.stat().st_size)
    loader = importlib.machinery.SourceFileLoader(source.stem, str(source))
    assert "stale" in loader.get_code(source.stem).co_consts
    try:
        result = LocalProcessExecutor(scratch_root=store.plane.root).execute(
            ExposedIsolatedNativeRunner(str(invocation), str(root), selected_entry_source=str(source)), context,
            timeout_seconds=None, native_subwork=store)
        assert result.checks[0].passed
    finally:
        for port in context.input_ports:
            port.close()
    assert (root / "selected-source-marker").read_text() == "fresh"
    metadata = exposed_metadata_definition(definitions[0])
    raw = b"".join(store.iter_completed_output(metadata, "process.selection"))
    selected = decode_canonical_bytes(raw, IsolatedNativeEntrySelection, maximum_bytes=len(raw))
    assert selected.entry_source_sha256 == sha256(source.read_bytes()).hexdigest()
    assert all(store.inspect(row).state is NativeSubworkState.NOT_ENTERED for row in definitions)


@pytest.mark.parametrize("fault", ["none-handshake", "boolean-sequence", "bootstrap-exit"])
@pytest.mark.parametrize("return_publication_fails", [False, True])
def test_malformed_actual_child_is_refused_and_reaped_even_when_it_ignores_term(tmp_path, monkeypatch, fault, return_publication_fails):
    from empirical_lawhood.adapters.methods.isolated_native_conformance import _freeze_initial
    from empirical_lawhood.infrastructure import isolated_native_subwork as bridge
    from empirical_lawhood.infrastructure.native_subwork_ipc import NativeSubworkPipeService, NativeSubworkRequest, PipeNativeSubworkProgress
    store, definitions, context, root, invocation, _ = fixture_case(tmp_path, "success")
    service = NativeSubworkPipeService(store, context, tmp_path)
    class Connection:
        def send(self, message):
            if type(message) is NativeSubworkRequest:
                service.handle(message, self)
            else:
                self.reply = message
        def recv(self):
            return self.reply
    progress = PipeNativeSubworkProgress(Connection())
    environment = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[2] / "src"), PYTHONDONTWRITEBYTECODE="1")
    entry_source = Path(bridge.__file__).resolve()
    selected = IsolatedNativeEntrySelection("exposed.malformed.entry", sys.executable,
        sha256(Path(sys.executable).read_bytes()).hexdigest(), bridge.__name__, "_main", str(entry_source),
        sha256(entry_source.read_bytes()).hexdigest(), str(invocation), sha256(invocation.read_bytes()).hexdigest(),
        bridge.selected_environment_sha256(environment))
    metadata = _freeze_initial(progress, definitions)
    metadata_entry = progress.begin(metadata)
    progress.contact(metadata_entry)
    raw = selected.canonical_bytes()
    manifest = progress.publish_output(metadata_entry, "process.selection", iter((raw,)), maximum_bytes=len(raw),
        expected_size_bytes=len(raw), expected_physical_sha256=sha256(raw).hexdigest())
    lifecycle = replace(metadata, subwork_id="engine.launch", operation_id="exposed.isolated.launch",
        configuration=selected.identity, input_materialization_ids=tuple(sorted((*metadata.input_materialization_ids,
            manifest.materialization.materialization_id))), roster_id="conditional.isolated.engine",
        outputs=(NativeSubworkOutput("process.return", IsolatedNativeEntryReturn.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json"),
            NativeSubworkOutput("process.start", IsolatedNativeProcessStart.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json")))
    progress.freeze_roster(NativeSubworkRoster(lifecycle.roster_id, definitions[0].parent_contact,
        (lifecycle.identity,), parent_subwork=metadata.identity), parent_entry=metadata_entry, definitions=(lifecycle,))
    lifecycle_entry = progress.begin(lifecycle)
    if return_publication_fails:
        real_publish = progress.publish_output
        def refuse_return_publication(entry, output_id, chunks, **kwargs):
            if output_id == "process.return":
                raise OSError("controlled return publication failure")
            return real_publish(entry, output_id, chunks, **kwargs)
        monkeypatch.setattr(progress, "publish_output", refuse_return_publication)
    real_popen = subprocess.Popen
    children = []
    # The controlled real child uses the exact inherited FD, then deliberately
    # violates this narrow protocol and waits forever while ignoring SIGTERM.
    script = '''import os, signal, sys
from multiprocessing.connection import Connection
from empirical_lawhood.infrastructure.isolated_native_subwork import _Handshake
from empirical_lawhood.infrastructure.native_subwork_ipc import NativeSubworkRequest
signal.signal(signal.SIGTERM, signal.SIG_IGN)
connection = Connection(int(sys.argv[1]))
selection, parent = connection.recv()
if sys.argv[2] == "bootstrap-exit":
    os._exit(17)
elif sys.argv[2] == "none-handshake":
    connection.send(None)
else:
    connection.send(_Handshake(selection.identity, parent, selection.interpreter_sha256,
        selection.entry_source_sha256, selection.invocation_sha256, selection.environment_sha256))
    connection.recv()
    connection.send(NativeSubworkRequest(True, "parent-contact", ()))
while True:
    signal.pause()
'''
    def malformed_child(command, **kwargs):
        child = real_popen([command[0], "-c", script, command[-1], fault], **kwargs)
        children.append(child)
        return child
    monkeypatch.setattr(bridge.subprocess, "Popen", malformed_child)
    try:
        with (root / "child.stdout").open("xb") as stdout, (root / "child.stderr").open("xb") as stderr:
            with pytest.raises(OSError if return_publication_fails else ValueError,
                    match="controlled return publication failure|substitutes|sequence|handshake") as failure:
                bridge.run_isolated_native_entry(selected, progress, lifecycle_entry=lifecycle_entry,
                    start_output_id="process.start", return_output_id="process.return", environment=environment,
                    cwd=root, stdout=stdout, stderr=stderr)
        expected_code = 17 if fault == "bootstrap-exit" else -9
        assert len(children) == 1 and children[0].returncode == expected_code
        inspection = store.inspect(lifecycle)
        assert inspection.state is NativeSubworkState.UNKNOWN_COMPLETION
        assert len(inspection.outputs) == (1 if return_publication_fails else 2)
        if return_publication_fails:
            returned = failure.value.isolated_native_entry_return
            assert isinstance(failure.value.isolated_native_bridge_error, ValueError)
            assert failure.value.isolated_native_phase == "process-return-publication"
        else:
            returned_manifest = next(row for row in inspection.outputs
                if row.logical.payload_schema == IsolatedNativeEntryReturn.SCHEMA)
            raw = store.plane.root.resolve(returned_manifest.materialization.relative_path, for_write=False).read_bytes()
            returned = decode_canonical_bytes(raw, IsolatedNativeEntryReturn, maximum_bytes=len(raw))
            assert failure.value.isolated_native_phase == ("progress-bridge" if fault == "boolean-sequence" else "handshake")
        assert returned.returncode == expected_code
        local_return = json.loads((root / "isolated-native-process-return.json").read_bytes())
        assert local_return["canonical_record"] == returned.canonical_bytes().decode()
        assert returned.handshake_completed is (fault == "boolean-sequence")
        assert returned.progress_requests == 0
        assert failure.value.isolated_native_entry_return == returned
        assert all(store.inspect(row).state is NativeSubworkState.NOT_ENTERED for row in definitions)
    finally:
        for child in children:
            if child.poll() is None:
                child.kill()
                child.wait()
        service.close()
        for port in context.input_ports:
            port.close()


def _run_exposed_loss_coordinator(tmp_path):
    """Separate disposable coordinator; the selected software child kills it."""
    store, _, context, root, invocation, _ = fixture_case(tmp_path, "success")
    source = root / "selected_software_loss.py"
    source.write_text('''import json, os, signal
from pathlib import Path
def identity(pid):
    raw = Path(f"/proc/{pid}/stat").read_text()
    fields = raw[raw.rfind(")") + 2:].split()
    return dict(pid=pid, start_time_ticks=int(fields[19]))
def exposed_child(progress, invocation):
    data = json.loads(invocation.read())
    progress.parent_contact
    coordinator = identity(data["coordinator"]["pid"])
    if coordinator != data["coordinator"]:
        raise ValueError("Exposed coordinator locator changed")
    marker = dict(coordinator=coordinator, child=identity(os.getpid()),
        worker=identity(os.getppid()), software_only=True, scientific_contacts=0)
    with Path("software-controller-loss.json").open("x") as stream:
        json.dump(marker, stream, sort_keys=True)
        stream.flush()
        os.fsync(stream.fileno())
    os.kill(coordinator["pid"], signal.SIGKILL)
    os.write(1, b"known software child stdout\\n")
    os.write(2, b"known software child stderr\\n")
    os._exit(47)
''')
    fields = Path(f"/proc/{os.getpid()}/stat").read_text().rsplit(")", 1)[1].split()
    data = json.loads(invocation.read_bytes())
    data["coordinator"] = dict(pid=os.getpid(), start_time_ticks=int(fields[19]))
    invocation.write_text(json.dumps(data))
    LocalProcessExecutor(scratch_root=store.plane.root).execute(
        ExposedIsolatedNativeRunner(str(invocation), str(root), selected_entry_source=str(source)),
        context, timeout_seconds=None, native_subwork=store)


def _host_exposed_loss_coordinator(tmp_path):
    """A software-only subreaper retains the disposable worker's actual return."""
    import ctypes
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(36, 1, 0, 0, 0) != 0:
        raise OSError(ctypes.get_errno(), "exposed loss host could not retain owned processes")
    command = [sys.executable, "-c",
        "from pathlib import Path; from tests.runtime_platform.test_isolated_native_subwork import "
        "_run_exposed_loss_coordinator; import sys; _run_exposed_loss_coordinator(Path(sys.argv[1]))", str(tmp_path)]
    coordinator = subprocess.Popen(command)
    code = coordinator.wait()
    adopted = []
    while True:
        try:
            pid, status = os.waitpid(-1, 0)
        except ChildProcessError:
            break
        adopted.append(dict(pid=pid, returncode=os.waitstatus_to_exitcode(status)))
    (tmp_path / "software-host-terminal.json").write_text(json.dumps(dict(
        coordinator_pid=coordinator.pid, coordinator_returncode=code,
        adopted_process_returns=adopted, scientific_contacts=0, native_replay=False), sort_keys=True))


def test_actual_coordinator_loss_retains_known_owned_child_return_before_broken_ipc(tmp_path):
    environment = dict(os.environ, PYTHONPATH=os.pathsep.join((
        str(Path(__file__).resolve().parents[2] / "src"), str(Path(__file__).resolve().parents[2]))),
        PYTHONDONTWRITEBYTECODE="1")
    command = [sys.executable, "-c",
        "from pathlib import Path; from tests.runtime_platform.test_isolated_native_subwork import "
        "_host_exposed_loss_coordinator; import sys; _host_exposed_loss_coordinator(Path(sys.argv[1]))", str(tmp_path)]
    host = subprocess.Popen(command, env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        start_new_session=True)
    try:
        stdout, stderr = host.communicate(timeout=30)
        assert host.returncode == 0, (stdout, stderr)
    finally:
        if host.poll() is None:
            os.killpg(host.pid, signal.SIGKILL)
            host.wait()
    root = tmp_path / "selected-child"
    start = json.loads((root / "isolated-native-process-start.json").read_bytes())
    returned = json.loads((root / "isolated-native-process-return.json").read_bytes())
    marker = json.loads((root / "software-controller-loss.json").read_bytes())
    terminal = json.loads((tmp_path / "software-host-terminal.json").read_bytes())
    raw = returned["canonical_record"].encode()
    typed = decode_canonical_bytes(raw, IsolatedNativeEntryReturn, maximum_bytes=len(raw))
    assert typed.returncode == 47 and typed.handshake_completed
    assert returned["record_schema"] == IsolatedNativeEntryReturn.SCHEMA
    assert returned["process_identity"] == start["process_identity"]
    assert {key: returned["process_identity"][key] for key in ("pid", "start_time_ticks")} == marker["child"]
    assert returned["process_identity"]["parent_pid"] == marker["worker"]["pid"]
    assert returned["owner_source"]["sha256"] == sha256(Path(returned["owner_source"]["path"]).read_bytes()).hexdigest()
    assert terminal["coordinator_pid"] == marker["coordinator"]["pid"]
    assert terminal["coordinator_returncode"] == -9
    assert next(row for row in terminal["adopted_process_returns"] if row["pid"] == marker["worker"]["pid"])["returncode"] == 1
    assert b"BrokenPipeError" in stderr
    assert (root / "child.stdout").read_bytes() == b"known software child stdout\n"
    assert (root / "child.stderr").read_bytes() == b"known software child stderr\n"
    assert not returned["scientific_receipt"] and not returned["nested_completion_inferred"]
    assert not returned["replay_authority"]
    assert not (root / "child-return.json").exists()


@pytest.mark.parametrize("occupied", ["isolated-native-process-start.json", "isolated-native-process-return.json"])
def test_previous_local_process_witness_refuses_before_launch_or_contact(tmp_path, occupied):
    store, definitions, context, root, invocation, _ = fixture_case(tmp_path, "success")
    (root / occupied).write_bytes(b"retained original unknown observation")
    try:
        with pytest.raises(TaskProcessError) as failure:
            LocalProcessExecutor(scratch_root=store.plane.root).execute(
                ExposedIsolatedNativeRunner(str(invocation), str(root)), context,
                timeout_seconds=None, native_subwork=store)
        assert failure.value.sanitized_exception_type == "FileExistsError"
        assert (root / occupied).read_bytes() == b"retained original unknown observation"
        assert all(store.inspect(row).state is NativeSubworkState.NOT_ENTERED for row in definitions)
        lifecycle, = store.iter_roster_definitions(definitions[0].parent_contact, "conditional.isolated.engine")
        assert store.inspect(lifecycle).state is NativeSubworkState.BEGUN
        assert (root / "child.stdout").read_bytes() == (root / "child.stderr").read_bytes() == b""
    finally:
        for port in context.input_ports:
            port.close()


def test_changed_original_invocation_after_handshake_cannot_substitute_selected_operands(tmp_path):
    store, definitions, context, root, invocation, payload = fixture_case(tmp_path, "success")
    original = invocation.read_bytes()
    try:
        result = LocalProcessExecutor(scratch_root=store.plane.root).execute(
            ExposedIsolatedNativeRunner(str(invocation), str(root), replace_invocation_after_handshake=True),
            context, timeout_seconds=None, native_subwork=store)
        assert result.checks[0].passed
    finally:
        for port in context.input_ports:
            port.close()
    assert invocation.read_bytes() == b'{"substituted":true}'
    metadata = exposed_metadata_definition(definitions[0])
    raw = b"".join(store.iter_completed_output(metadata, "process.selection"))
    selection = decode_canonical_bytes(raw, IsolatedNativeEntrySelection, maximum_bytes=len(raw))
    assert selection.invocation_sha256 == sha256(original).hexdigest()
    assert b"".join(store.iter_completed_output(definitions[0], definitions[0].outputs[0].output_id)) == payload


@pytest.mark.parametrize("field", ["entry_source_path", "invocation_path"])
def test_nonregular_selected_file_refuses_before_launch_or_contact(tmp_path, field):
    from empirical_lawhood.infrastructure import isolated_native_subwork as bridge
    from empirical_lawhood.infrastructure.bounded_io import BoundedFileIOError
    from tests.runtime_platform.test_native_subwork_completed_relay import pipe
    store, definitions, _, root, invocation, _ = fixture_case(tmp_path, "success")
    progress, service, context = pipe(store, definitions[0], store.parent_inputs, tmp_path)
    environment = dict(os.environ)
    source = Path(bridge.__file__).resolve()
    selected = IsolatedNativeEntrySelection("exposed.fifo.entry", sys.executable,
        sha256(Path(sys.executable).read_bytes()).hexdigest(), bridge.__name__, "_main", str(source),
        sha256(source.read_bytes()).hexdigest(), str(invocation), sha256(invocation.read_bytes()).hexdigest(),
        bridge.selected_environment_sha256(environment))
    fifo = root / "selected.fifo"
    os.mkfifo(fifo)
    selected = replace(selected, **{field: str(fifo)})
    try:
        with (root / "child.stdout").open("xb") as stdout, (root / "child.stderr").open("xb") as stderr:
            with pytest.raises(BoundedFileIOError, match="regular file"):
                bridge.run_isolated_native_entry(selected, progress, lifecycle_entry=None,
                    start_output_id="process.start", return_output_id="process.return", environment=environment,
                    cwd=root, stdout=stdout, stderr=stderr)
        assert all(store.inspect(row).state is NativeSubworkState.NOT_ENTERED for row in definitions)
        assert (root / "child.stdout").read_bytes() == (root / "child.stderr").read_bytes() == b""
    finally:
        service.close()
        for port in context.input_ports:
            port.close()


def test_complete_invocation_snapshot_is_sealed_with_bounded_copy_memory(tmp_path):
    import fcntl
    from empirical_lawhood.infrastructure import isolated_native_subwork as bridge
    source = Path(bridge.__file__).resolve()
    invocation = tmp_path / "all-selected-operands"
    block = b"complete operand denominator\n" * 32768
    digest = sha256()
    with invocation.open("xb") as stream:
        for _ in range(12):
            stream.write(block)
            digest.update(block)
    selected = IsolatedNativeEntrySelection("exposed.large.entry", sys.executable,
        sha256(Path(sys.executable).read_bytes()).hexdigest(), bridge.__name__, "_main", str(source),
        sha256(source.read_bytes()).hexdigest(), str(invocation), digest.hexdigest(),
        bridge.selected_environment_sha256(dict(os.environ)))
    tracemalloc.start()
    try:
        operand = bridge._seal_invocation(selected)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    try:
        descriptor = operand._reader._binary_handle().fileno()
        assert fcntl.fcntl(descriptor, 1034) & 0xF == 0xF  # Linux F_GET_SEALS, complete four-seal census.
        with pytest.raises(PermissionError):
            os.write(descriptor, b"substitute")
        invocation.write_bytes(b"changed original path")
        recovered = sha256()
        count = 0
        for chunk in operand.iter_chunks(maximum_chunk_bytes=65536):
            assert len(chunk) <= 65536
            count += len(chunk)
            recovered.update(chunk)
        assert count == operand.bytes_read == operand.size_bytes == 12 * len(block)
        assert recovered.hexdigest() == operand.content_sha256 == digest.hexdigest()
        assert peak < 4 * 1024 * 1024 < operand.size_bytes
        with pytest.raises(ValueError, match="integer read size"):
            operand.read(True)
    finally:
        operand.close()
