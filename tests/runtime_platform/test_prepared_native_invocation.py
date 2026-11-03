# SPDX-License-Identifier: MPL-2.0
"""Prepared operands reach actual guarded BEGIN/IPC, never qualification."""

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import shutil

import pytest

from empirical_lawhood.adapters.methods.native_subwork_conformance import ExposedNativeSubworkRunner
from empirical_lawhood.adapters.methods import isolated_native_conformance
from empirical_lawhood.adapters.methods.isolated_native_conformance import ExposedIsolatedNativeRunner
from empirical_lawhood.infrastructure.execution import LocalProcessExecutor, TaskProcessError
from empirical_lawhood.infrastructure.native_subwork_inputs import (
    NativeSubworkInputError, validate_native_subwork_inputs,
)
from empirical_lawhood.infrastructure.native_subwork_ipc import (
    NativeSubworkPipeService, NativeSubworkRequest, PipeNativeSubworkProgress,
)
from empirical_lawhood.infrastructure.prepared_native_invocation import (
    NativeInputPublication, prepare_native_invocation, validate_prepared_native_invocation,
)
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.runtime.native_effects import NativeEffectContact
from empirical_lawhood.runtime.native_subwork import NativeSubworkOutput, NativeSubworkRoster, NativeSubworkState
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.isolated_native_subwork import (
    IsolatedNativeEntryReturn, IsolatedNativeEntrySelection, IsolatedNativeProcessStart,
)
from tests.runtime_platform.test_native_subwork import ExposedInput, _plane, _store, _process_context


VISIBILITY = VisibilityCeiling.DEVELOPMENT_ONLY
ACCESS = OutcomeAccess.DEVELOPMENT_VISIBLE


def test_one_shot_publications_return_complete_committed_inputs(tmp_path):
    plane = _plane(tmp_path / "custody")
    records = (ExposedInput("source.one", "exposed"), ExposedInput("source.two", "exposed"))
    publications = (NativeInputPublication(record.selected_id, record) for record in records)
    bundle = prepare_native_invocation(plane, publications=publications,
        visibility=VISIBILITY, access=ACCESS)
    try:
        assert tuple(row.identity for row in bundle.inputs) == tuple(
            ObjectIdentity.from_record(record.selected_id, record) for record in records)
        for selected, record in zip(bundle.inputs, records, strict=True):
            plane.verify_manifest(selected.manifest)
            assert selected.port.read() == record.canonical_bytes()
    finally:
        bundle.close()


def prepared(tmp_path):
    plane = _plane(tmp_path / "custody")
    config = ExposedInput("config.selected", "293.150")
    source = ExposedInput("source.selected", "FALSIFIED")
    stream = ExposedInput("stream.selected", "unchanged-driver")
    package_sources = (("src/exposed_fixture.py", "4" * 64),)
    provenance = NumericalProducingProvenance(
        '{"python":"exposed","numpy":"exposed","scipy":"exposed","system":"Linux","machine":"exposed","threadpools":[]}',
        "5" * 64, package_sources, sha256(canonical_json_bytes(package_sources)).hexdigest(), "3" * 40, False)
    bundle = prepare_native_invocation(plane, visibility=VISIBILITY, access=ACCESS,
        publications=(NativeInputPublication(config.selected_id, config),
            NativeInputPublication(source.selected_id, source, "transport.source-alias"),
            NativeInputPublication(stream.selected_id, stream),
            NativeInputPublication(provenance.identity.object_id, provenance)))
    parent = NativeEffectContact("synthetic.run", "native.parent", "synthetic.run.native.parent.attempt-001",
        ObjectIdentity("plan.selected", "empirical-lawhood/runtime/development-execution-plan", "1.0.0", "1" * 64),
        ObjectIdentity("native.parent", "empirical-lawhood/runtime/execution-task", "1.0.0", "2" * 64),
        provenance.observed_git_head, bundle.input_materialization_ids, ())
    definition = bundle.definition(subwork_id="forecast.one", operation_id="exposed.forecast",
        parent_contact=parent, configuration=ObjectIdentity.from_record(config.selected_id, config),
        sources=(ObjectIdentity.from_record(source.selected_id, source),), provenance=provenance,
        streams=(ObjectIdentity.from_record(stream.selected_id, stream),),
        outputs=(NativeSubworkOutput("result.output.native",
            "empirical-lawhood/source/checksummed-uninterpreted-public-bytes",
            ArtifactProfile.RAW_SOURCE_BYTES, "text/plain"),))
    return plane, bundle, definition


def test_available_inputs_validate_before_ordinary_contact_then_reach_real_spawned_begin(tmp_path):
    plane, bundle, definition = prepared(tmp_path)
    definitions = tuple(replace(definition, subwork_id=value)
        for value in ("forecast.one", "forecast.three", "forecast.two"))
    try:
        validate_prepared_native_invocation(plane, bundle, definitions, visibility=VISIBILITY, access=ACCESS)
        # No parent contact exists during preparation. It is still owned by custody.
        store = _store(plane, definition.parent_contact, bundle.manifests)
        assert store.parent_contacts.read("synthetic.run", "native.parent") is None
        store.parent_contacts.begin(definition.parent_contact)
        store.freeze_roster(NativeSubworkRoster("selected.native-subwork", definition.parent_contact,
            tuple(value.identity for value in definitions)), definitions=definitions)
        context = _process_context(store, definition, bundle.manifests)
        for port in context.input_ports:
            port.close()
        # Compose context from the same joined ports, not a separately assembled census.
        ports = bundle.open_many(bundle.verified_inputs, bindings=bundle.input_bindings, maximum_bytes=None)
        assert all(left is right for left, right in zip(ports, bundle.input_ports, strict=True))
        context = replace(context, input_bindings=bundle.input_bindings, input_ports=ports)
        LocalProcessExecutor(scratch_root=plane.root).execute(
            ExposedNativeSubworkRunner(definitions, (b"SATISFIED", b"FALSIFIED", b"UNEVALUABLE")),
            context, timeout_seconds=None, native_subwork=store)
        assert [store.recover(value).state for value in definitions] == [NativeSubworkState.COMPLETED] * 3
        assert [b"".join(store.iter_completed_output(value, "result.output.native"))
            for value in definitions] == [b"SATISFIED", b"FALSIFIED", b"UNEVALUABLE"]
        source = next(value for value in bundle.inputs if value.identity.object_id == "source.selected")
        assert source.port.artifact_id == "transport.source-alias"
        assert source.identity.object_id == "source.selected"
    finally:
        bundle.close()


def test_complete_mismatch_census_is_identical_at_preparation_and_actual_begin(tmp_path):
    plane, bundle, definition = prepared(tmp_path)
    broken = replace(definition, configuration=replace(definition.configuration, object_fingerprint="9" * 64),
        sources=tuple(replace(value, object_fingerprint="8" * 64)
            if value.object_id == "source.selected" else value for value in definition.sources),
        streams=tuple(replace(value, object_version="2.0.0") for value in definition.streams),
        code_sources_sha256="7" * 64, dependency_lock_sha256="6" * 64)
    try:
        with pytest.raises(NativeSubworkInputError) as early:
            validate_prepared_native_invocation(plane, bundle, (broken,), visibility=VISIBILITY, access=ACCESS)
        assert {row.operand_id for row in early.value.mismatches} == {
            "config.selected", "source.selected", "stream.selected", "numerical.producing-provenance"}
        store = _store(plane, broken.parent_contact, bundle.manifests)
        assert store.parent_contacts.read("synthetic.run", "native.parent") is None
        store.parent_contacts.begin(broken.parent_contact)
        with pytest.raises(NativeSubworkInputError) as entered:
            store.begin(broken, bundle.manifests)
        assert entered.value.mismatches == early.value.mismatches
        assert store.inspect(broken).state is NativeSubworkState.NOT_ENTERED
    finally:
        bundle.close()


def test_actual_ipc_retains_complete_input_mismatch_census_beyond_short_error_message(tmp_path):
    plane, bundle, definition = prepared(tmp_path)
    broken = replace(definition, configuration=replace(definition.configuration, object_fingerprint="9" * 64),
        sources=tuple(replace(value, object_fingerprint="8" * 64)
            if value.object_id == "source.selected" else value for value in definition.sources),
        streams=tuple(sorted((*tuple(replace(value, object_version="2.0.0") for value in definition.streams),
            replace(definition.streams[0], object_id="stream.selected.second-missing-independent-operand",
                object_fingerprint="a" * 64)), key=lambda value: value.object_id)),
        code_sources_sha256="7" * 64, dependency_lock_sha256="6" * 64)
    store = _store(plane, definition.parent_contact, bundle.manifests)
    store.parent_contacts.begin(definition.parent_contact)
    context = _process_context(store, definition, bundle.manifests)
    service = NativeSubworkPipeService(store, context, tmp_path)
    class Connection:
        def send(self, value):
            if type(value) is NativeSubworkRequest:
                service.handle(value, self)
            else:
                self.reply = value
        def recv(self):
            return self.reply
    connection = Connection()
    progress = PipeNativeSubworkProgress(connection)
    try:
        with pytest.raises(NativeSubworkInputError) as expected:
            validate_prepared_native_invocation(plane, bundle, (broken,), visibility=VISIBILITY, access=ACCESS)
        assert len(str(expected.value)) > 512
        with pytest.raises(NativeSubworkInputError) as received:
            progress.begin(broken)
        assert connection.reply.error_message == str(expected.value)[:512]
        assert received.value.mismatches == expected.value.mismatches
        assert len(received.value.mismatches) == 6
        assert store.inspect(broken).state is NativeSubworkState.NOT_ENTERED
    finally:
        service.close()
        for port in context.input_ports:
            port.close()
        bundle.close()


def test_actual_two_process_hops_preserve_complete_input_refusal_before_native_effect(tmp_path):
    plane, bundle, definition = prepared(tmp_path)
    source = next(value for value in definition.sources if value.object_id == "source.selected")
    broken = replace(definition,
        configuration=replace(definition.configuration, object_fingerprint="9" * 64),
        sources=tuple(sorted((*(replace(value, object_fingerprint="8" * 64)
            if value.object_id == source.object_id else value for value in definition.sources),
            replace(source, object_id="source.selected.second-missing-independent-operand",
                object_fingerprint="a" * 64)),
            key=lambda value: value.object_id)),
        streams=tuple(sorted((replace(definition.streams[0], object_version="2.0.0"),
            *(replace(definition.streams[0],
                object_id=f"stream.selected.{name}-missing-independent-operand",
                object_fingerprint=digest * 64)
                for name, digest in (("second", "b"), ("third", "c")))),
                key=lambda value: value.object_id)),
        code_sources_sha256="7" * 64, dependency_lock_sha256="6" * 64)
    root = tmp_path / "isolated-refusal"
    root.mkdir()
    entry = root / "selected_input_refusal.py"
    entry.write_text(
        "import json, os\n"
        "from pathlib import Path\n"
        "from empirical_lawhood.kernel.decoding import decode_canonical_bytes\n"
        "from empirical_lawhood.runtime.native_subwork import NativeSubworkDefinition\n"
        "def exposed_child(progress, invocation):\n"
        "    data = json.loads(invocation.read())\n"
        "    raw = data['definitions'][1].encode()\n"
        "    definition = decode_canonical_bytes(raw, NativeSubworkDefinition, maximum_bytes=len(raw))\n"
        "    try:\n"
        "        selected = progress.begin(definition)\n"
        "    except Exception as error:\n"
        "        Path('received-refusal.json').write_text(json.dumps({\n"
        "            'pid': os.getpid(), 'type': type(error).__name__, 'message': str(error),\n"
        "            'mismatches': [[row.operand_id, row.reason]\n"
        "                for row in getattr(error, 'mismatches', ())]}))\n"
        "        return\n"
        "    progress.contact(selected)\n"
        "    Path('native-effect-entered').write_text('unexpected scientific native entry')\n"
    )
    invocation = root / "invocation.json"
    # The valid carrier only supports authenticated process start/return. The
    # selected scientific definition reaches the real coordinator's validator.
    carrier = replace(definition, subwork_id="carrier.control")
    invocation.write_text(json.dumps({"definitions": [row.canonical_bytes().decode()
        for row in (carrier, broken)]}))
    context = None
    try:
        with pytest.raises(NativeSubworkInputError) as expected:
            validate_native_subwork_inputs(plane, broken, bundle.manifests,
                visibility=VISIBILITY, access=ACCESS)
        assert len(expected.value.mismatches) == 8 and len(str(expected.value)) > 512
        store = _store(plane, definition.parent_contact, bundle.manifests)
        store.parent_contacts.begin(definition.parent_contact)
        context = _process_context(store, definition, bundle.manifests)
        result = LocalProcessExecutor(scratch_root=plane.root).execute(
            ExposedIsolatedNativeRunner(str(invocation), str(root), selected_entry_source=str(entry)),
            context, timeout_seconds=None, native_subwork=store)
        assert result.checks[0].passed
        refused = json.loads((root / "received-refusal.json").read_bytes())
        assert refused["type"] == "NativeSubworkInputError"
        assert refused["mismatches"] == [[row.operand_id, row.reason]
            for row in expected.value.mismatches]
        assert refused["message"] == str(expected.value)
        assert len(refused["message"]) > 512
        assert not (root / "native-effect-entered").exists()
        assert store.inspect(broken).state is NativeSubworkState.NOT_ENTERED
        assert store.inspect(carrier).state is NativeSubworkState.NOT_ENTERED
        lifecycle, = store.iter_roster_definitions(definition.parent_contact, "conditional.isolated.engine")
        raw_start = b"".join(store.iter_completed_output(lifecycle, "process.start"))
        started = decode_canonical_bytes(raw_start, IsolatedNativeProcessStart, maximum_bytes=len(raw_start))
        raw_return = b"".join(store.iter_completed_output(lifecycle, "process.return"))
        returned = decode_canonical_bytes(raw_return, IsolatedNativeEntryReturn, maximum_bytes=len(raw_return))
        assert refused["pid"] == started.child_pid and started.child_pid != started.creator_pid
        assert started.selection == returned.selection
        assert returned.handshake_completed and returned.returncode == 0
    finally:
        if context is not None:
            for port in context.input_ports:
                port.close()
        bundle.close()


@pytest.mark.parametrize("field", ["identity", "port"])
def test_prepared_handle_refuses_detached_identity_or_port(tmp_path, field):
    _, bundle, _ = prepared(tmp_path)
    first, second = bundle.inputs[:2]
    try:
        with pytest.raises(ValueError, match="source identity|worker port"):
            replace(first, **{field: second.identity if field == "identity" else second.port})
    finally:
        bundle.close()


def test_record_revision_substitution_refuses_during_preparation_before_contact(tmp_path):
    plane, bundle, _ = prepared(tmp_path)
    selected = bundle.inputs[0]
    try:
        with pytest.raises(ValueError, match="record version"):
            prepare_native_invocation(plane, existing_inputs=((
                replace(selected.identity, object_version="2.0.0"), selected.manifest),),
                visibility=VISIBILITY, access=ACCESS)
        assert not (tmp_path / "custody" / "runs").exists()
    finally:
        bundle.close()


def test_existing_factory_contract_supplies_the_same_prepared_ports_and_refuses_substitution(tmp_path):
    _, bundle, _ = prepared(tmp_path)
    try:
        ports = bundle.open_many(bundle.verified_inputs, bindings=bundle.input_bindings, maximum_bytes=None)
        assert all(left is right for left, right in zip(ports, bundle.input_ports, strict=True))
        assert bundle.open(bundle.verified_inputs[0], maximum_bytes=None) is ports[0]
        with pytest.raises(ValueError, match="source-scan budget"):
            bundle.open_many(bundle.verified_inputs, bindings=bundle.input_bindings, maximum_bytes=1)
        with pytest.raises(ValueError, match="worker binding"):
            bundle.open_many(bundle.verified_inputs, bindings=(
                replace(bundle.input_bindings[0], artifact_id="substituted.source"), *bundle.input_bindings[1:]),
                maximum_bytes=None)
        with pytest.raises(ValueError, match="complete input census"):
            bundle.open_many(bundle.verified_inputs[:-1], bindings=bundle.input_bindings[:-1], maximum_bytes=None)
    finally:
        bundle.close()
    with pytest.raises(ValueError, match="closed"):
        bundle.open_many(bundle.verified_inputs, bindings=bundle.input_bindings, maximum_bytes=None)


def test_zero_length_prepared_read_preserves_bytes_and_closed_port_refusal(tmp_path):
    _, bundle, _ = prepared(tmp_path)
    port = bundle.input_ports[0]
    try:
        assert port.read(0) == port.read(0) == b""
        assert port.bytes_read == 0
        first = port.read(1)
        assert len(first) == 1
        assert port.read(0) == b"" and port.bytes_read == 1
        remaining = port.read()
        assert sha256(first + remaining).hexdigest() == bundle.inputs[0].manifest.materialization.physical_sha256
        with pytest.raises(ValueError, match="consumed"):
            bundle.open_many(bundle.verified_inputs, bindings=bundle.input_bindings, maximum_bytes=None)
    finally:
        bundle.close()
    with pytest.raises(ValueError, match="closed"):
        port.read(0)


def test_invalid_transport_id_and_mutable_serialization_refuse_before_publication(tmp_path):
    plane = _plane(tmp_path / "custody")
    with pytest.raises(ValueError):
        NativeInputPublication("source.selected", ExposedInput("source.selected", "old"), "invalid/alias")
    with pytest.raises(ValueError, match="unsupported canonical value type: list"):
        NativeInputPublication("source.selected", ExposedInput("source.selected", ["mutable"]))
    assert not (Path(plane.root.contract.canonical_path) / "inputs").exists()


def test_available_input_census_catches_all_missing_operands(tmp_path):
    plane, bundle, definition = prepared(tmp_path)
    try:
        with pytest.raises(NativeSubworkInputError) as refused:
            validate_native_subwork_inputs(plane, definition, (), visibility=VISIBILITY, access=ACCESS)
        assert {row.operand_id for row in refused.value.mismatches}.issuperset({
            "config.selected", "source.selected", "stream.selected", "numerical.producing-provenance",
            *bundle.input_materialization_ids})
        assert not (tmp_path / "custody" / "runs").exists()
    finally:
        bundle.close()


def test_historical_and_selected_record_ids_keep_distinct_authenticated_transport_bindings(tmp_path):
    plane = _plane(tmp_path / "custody")
    historical = ExposedInput("roster.battery-durable-inquiry.qualification", "original48")
    selected = replace(historical, value="selected54-with-six-aliases")
    bundle = prepare_native_invocation(plane, visibility=VISIBILITY, access=ACCESS, publications=(
        NativeInputPublication(historical.selected_id, historical),
        NativeInputPublication(selected.selected_id, selected, "selected.roster.battery-durable-inquiry.qualification")))
    try:
        assert len(bundle.inputs) == 2
        old, new = bundle.inputs
        assert old.identity.object_id == new.identity.object_id
        assert old.identity.object_fingerprint != new.identity.object_fingerprint
        assert old.port.artifact_id != new.port.artifact_id
        assert old.port.materialization_id != new.port.materialization_id
        assert old.port.read() == historical.canonical_bytes()
        assert new.port.read() == selected.canonical_bytes()
    finally:
        bundle.close()


@pytest.mark.parametrize("phase", ["success", "after-completion"])
def test_prepared_selected_worker_publication_and_independent_relocated_recovery(tmp_path, phase):
    plane, bundle, first = prepared(tmp_path)
    definitions = tuple(replace(first, subwork_id=value)
        for value in ("forecast.one", "forecast.three", "forecast.two"))
    root = tmp_path / "frozen-child"
    root.mkdir()
    package = Path(isolated_native_conformance.__file__).resolve().parents[2]
    selected_import_root = package.parent

    def source_census():
        return tuple((str(path.relative_to(selected_import_root)), sha256(path.read_bytes()).hexdigest())
            for path in sorted(package.rglob("*"))
            if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc")

    original_source = source_census()
    entry = Path(isolated_native_conformance.__file__).resolve()
    payload = '{"outcome":"FALSIFIED"}\n' * 100_000
    invocation = root / "invocation.json"
    invocation.write_text(json.dumps({"definitions": [row.canonical_bytes().decode() for row in definitions],
        "phase": phase, "payload": payload}))
    try:
        validate_prepared_native_invocation(plane, bundle, definitions, visibility=VISIBILITY, access=ACCESS)
        store = _store(plane, first.parent_contact, bundle.manifests)
        store.parent_contacts.begin(first.parent_contact)
        context = _process_context(store, first, bundle.manifests)
        for port in context.input_ports:
            port.close()
        context = replace(context, input_bindings=bundle.input_bindings, input_ports=bundle.input_ports)
        runner = ExposedIsolatedNativeRunner(str(invocation), str(root), selected_entry_source=str(entry),
            selected_import_root=str(selected_import_root))
        if phase == "after-completion":
            with pytest.raises(TaskProcessError):
                LocalProcessExecutor(scratch_root=plane.root).execute(runner, context,
                    timeout_seconds=None, native_subwork=store)
        else:
            LocalProcessExecutor(scratch_root=plane.root).execute(runner, context,
                timeout_seconds=None, native_subwork=store)
        raw_return = (root / "child-return.json").read_bytes()
        returned = decode_canonical_bytes(raw_return, IsolatedNativeEntryReturn,
            maximum_bytes=len(raw_return))
        assert returned.handshake_completed
        assert returned.returncode == (95 if phase == "after-completion" else 0)
        metadata = isolated_native_conformance.exposed_metadata_definition(first)
        raw_selection = b"".join(store.iter_completed_output(metadata, "process.selection"))
        selection = decode_canonical_bytes(raw_selection, IsolatedNativeEntrySelection,
            maximum_bytes=len(raw_selection))
        assert selection.entry_source_sha256 == sha256(entry.read_bytes()).hexdigest()
        assert selection.invocation_sha256 == sha256(invocation.read_bytes()).hexdigest()
        assert source_census() == original_source
        destination = tmp_path / "relocated"
        shutil.copytree(plane.root.contract.canonical_path, destination)
        reader = _store(_plane(destination), first.parent_contact)
        before = reader.recover(first)
        contact_files = tuple(sorted(destination.rglob("contact")))
        count, pending = 0, b""
        for chunk in reader.iter_completed_output(first, first.outputs[0].output_id,
                maximum_chunk_bytes=65536):
            lines = (pending + chunk).split(b"\n")
            pending = lines.pop()
            for line in lines:
                assert json.loads(line) == {"outcome": "FALSIFIED"}
                count += 1
        assert count == 100_000 and pending == b""
        assert before.outputs[0].logical.content_sha256 == sha256(payload.encode()).hexdigest()
        assert reader.recover(first) == before
        assert tuple(sorted(destination.rglob("contact"))) == contact_files
        assert [reader.inspect(row).state for row in definitions] == [
            NativeSubworkState.COMPLETED, NativeSubworkState.NOT_ENTERED, NativeSubworkState.NOT_ENTERED]
        with pytest.raises(ValueError, match="already completed"):
            reader.begin(first, bundle.manifests)
    finally:
        bundle.close()
