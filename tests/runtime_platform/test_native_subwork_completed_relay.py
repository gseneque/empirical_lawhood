# SPDX-License-Identifier: MPL-2.0
"""Receipt-authenticated completed-output relay; no scientific native effects."""

from dataclasses import replace
from contextlib import ExitStack
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
import shutil
import tracemalloc

import pytest

from empirical_lawhood.adapters.methods.native_subwork_conformance import ExposedNativeSubworkRelayRunner
from empirical_lawhood.infrastructure.artifact_validation import ArtifactIdentityConflict
from empirical_lawhood.infrastructure.artifacts import STREAM_CHUNK_BYTES
from empirical_lawhood.infrastructure.bounded_io import BoundedFileIOError
from empirical_lawhood.infrastructure.execution import LocalProcessExecutor, ResourceAdmissionError, TaskProcessError
from empirical_lawhood.infrastructure.native_subwork import ExternalNativeSubworkStore
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
from empirical_lawhood.infrastructure.native_subwork_ipc import (
    NativeSubworkPipeService, NativeSubworkRequest, PipeNativeSubworkProgress,
)
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.execution import StreamedTaskOutput, WorkerOutputPort
from empirical_lawhood.runtime.execution_envelope import ProgressHeartbeat, ProgressLivenessContract
from empirical_lawhood.runtime.native_subwork import NativeSubworkState, NativeSubworkUncertainContact
from tests.runtime_platform.test_native_subwork import (
    _complete, _known_unreceipted_return, _plane, _process_context, _publish, _selected, _store,
)


@pytest.fixture
def selected(tmp_path):
    return _selected(tmp_path)


def test_completed_prepared_process_relay_preserves_call_facts_without_new_entry(tmp_path):
    from tests.runtime_platform.test_isolated_native_subwork import prepared_bridge_case
    with prepared_bridge_case(tmp_path, 0) as (store, definition, context, contract, returned, _progress, _service), ExitStack() as scopes:
        retained = store.recover(definition)
        paths = tuple(store.plane.root.resolve(store._root(definition), for_write=False).rglob("*"))
        before = {str(path): path.read_bytes() for path in paths if path.is_file()}
        def forbidden(*args, **kwargs):
            raise AssertionError("completed relay requested acquisition, a grant or mutation")
        scoped_plane = scopes.enter_context(store.plane.verification_scope())
        reader = ExternalNativeSubworkStore(plane=scoped_plane, parent_contacts=store.parent_contacts,
            parent_contact=store.parent_contact, parent_inputs=store.parent_inputs,
            completed_only=True, before_contact=forbidden)
        relay = NativeSubworkPipeService(reader, context, tmp_path, completed_work=contract.native_work)
        class Connection:
            def send(self, message):
                if type(message) is NativeSubworkRequest:
                    relay.handle(message, self)
                else:
                    self.reply = message
            def recv(self):
                return self.reply
        port = PipeNativeSubworkProgress(Connection())
        try:
            for output in ("process.start", "process.return"):
                raw = b"".join(port.iter_completed_output(definition, output, maximum_chunk_bytes=7))
                assert raw == b"".join(store.iter_completed_output(definition, output))
                if output == "process.return":
                    assert raw == returned.canonical_bytes()
            assert port.recover(definition) == retained
            assert retained.call_entry.invocation == contract.identity
            assert retained.call_return.return_code == 0
            assert relay._readers == {}
            after = {str(path): path.read_bytes() for path in paths if path.is_file()}
            assert after == before
        finally:
            relay.close()


def pipe(store, definition, inputs, tmp_path):
    context = _process_context(store, definition, inputs)
    service = NativeSubworkPipeService(store, context, tmp_path)
    class Connection:
        def send(self, message):
            if type(message) is NativeSubworkRequest:
                service.handle(message, self)
            else:
                self.reply = message
        def recv(self):
            return self.reply
    return PipeNativeSubworkProgress(Connection()), service, context


@pytest.mark.parametrize("route", ["direct", "pipe"])
@pytest.mark.parametrize("payload,failed", [(b"SATISFIED", False), (b"FALSIFIED", False), (b"UNEVALUABLE", True)])
def test_exact_completed_bytes_include_negative_and_failed(selected, route, payload, failed, tmp_path, monkeypatch):
    store, definition, inputs = selected
    entry = store.begin(definition, inputs)
    store.contact(entry)
    _publish(store, entry, payload)
    before = _complete(store, entry, failed=failed)
    context = service = None
    reader = store
    if route == "pipe":
        reader, service, context = pipe(store, definition, inputs, tmp_path)
    def no_native(*args, **kwargs):
        raise AssertionError("receipt-only relay entered native work")
    monkeypatch.setattr(store, "contact", no_native)
    monkeypatch.setattr(ExternalNativeSubworkStore, "recover", no_native)
    monkeypatch.setattr(ExternalTaskReceiptStore, "commit", no_native)
    try:
        chunks = list(reader.iter_completed_output(definition, definition.outputs[0].output_id,
            maximum_chunk_bytes=2))
        assert all(0 < len(chunk) <= 2 for chunk in chunks)
        assert b"".join(chunks) == payload
        assert reader.resolve_completed_definition(definition.identity) == definition
        assert store.inspect(definition) == before
        if service is not None:
            assert service._readers == {}
    finally:
        if context is not None:
            for port in context.input_ports:
                port.close()
            service.close()


@pytest.mark.parametrize("route", ["direct", "pipe"])
def test_known_unreceipted_return_is_read_only_and_requires_explicit_recovery(selected, route, tmp_path, monkeypatch):
    store, definition, inputs = _known_unreceipted_return(selected, monkeypatch)
    context = service = None
    reader = store
    if route == "pipe":
        reader, service, context = pipe(store, definition, inputs, tmp_path)
    root = Path(store.plane.root.contract.canonical_path)
    before = {str(path): sha256(path.read_bytes()).hexdigest() for path in root.rglob("*") if path.is_file()}
    def forbidden(*args, **kwargs):
        pytest.fail("completed-output read attempted recovery or receipt publication")
    monkeypatch.setattr(ExternalNativeSubworkStore, "recover", forbidden)
    monkeypatch.setattr(ExternalTaskReceiptStore, "commit", forbidden)
    try:
        with pytest.raises(ValueError, match="complete subwork receipt"):
            reader.resolve_completed_definition(definition.identity)
        with pytest.raises(ValueError, match="complete subwork receipt"):
            list(reader.iter_completed_output(definition, definition.outputs[0].output_id))
        assert store.inspect(definition).state is NativeSubworkState.UNKNOWN_COMPLETION
        assert store.inspect(definition).native_return_status is not None
        assert {str(path): sha256(path.read_bytes()).hexdigest() for path in root.rglob("*") if path.is_file()} == before
    finally:
        if context is not None:
            for port in context.input_ports:
                port.close()
            service.close()


@pytest.mark.parametrize("phase", ["unentered", "begun", "contacted", "published", "omitted"])
def test_incomplete_or_omitted_output_never_supplies_a_complete_product(selected, phase):
    store, definition, inputs = selected
    if phase != "unentered":
        entry = store.begin(definition, inputs)
        if phase != "begun":
            store.contact(entry)
            if phase == "published":
                _publish(store, entry, b"returned but not completed")
            if phase == "omitted":
                _complete(store, entry, failed=True)
    with pytest.raises((ValueError, NativeSubworkUncertainContact)):
        list(store.iter_completed_output(definition, definition.outputs[0].output_id))
    with pytest.raises(ValueError, match="declared"):
        list(store.iter_completed_output(definition, "other.output"))
    if phase != "omitted":
        with pytest.raises((ValueError, NativeSubworkUncertainContact)):
            store.resolve_completed_definition(definition.identity)


def test_empty_raw_publication_refusal_cannot_be_relabelled_as_a_completed_product(selected):
    store, definition, inputs = selected
    entry = store.begin(definition, inputs); store.contact(entry)
    with pytest.raises(ArtifactIdentityConflict, match="uninterpreted contract"):
        _publish(store, entry, b"")
    with pytest.raises(NativeSubworkUncertainContact):
        list(store.iter_completed_output(definition, definition.outputs[0].output_id))


@pytest.mark.parametrize("bound", [True, 0, -1, 1.5])
def test_invalid_read_allowance_refuses_before_custody(selected, bound):
    store, definition, _ = selected
    with pytest.raises(ValueError, match="positive integer"):
        list(store.iter_completed_output(definition, definition.outputs[0].output_id,
            maximum_chunk_bytes=bound))
    assert store.inspect(definition).state is NativeSubworkState.NOT_ENTERED


def test_corruption_and_midstream_mutation_refuse_complete_delivery(selected):
    store, definition, inputs = selected
    entry = store.begin(definition, inputs); store.contact(entry)
    manifest = _publish(store, entry, b"0123456789")
    _complete(store, entry)
    path = store.plane.root.resolve(manifest.materialization.relative_path, for_write=False)
    iterator = store.iter_completed_output(definition, definition.outputs[0].output_id, maximum_chunk_bytes=2)
    assert next(iterator) == b"01"
    path.write_bytes(b"01234567XX")
    with pytest.raises((BoundedFileIOError, ArtifactIdentityConflict)):
        list(iterator)
    with pytest.raises((ValueError, BoundedFileIOError, ArtifactIdentityConflict)):
        list(store.iter_completed_output(definition, definition.outputs[0].output_id))


@pytest.mark.parametrize("member", ["completion", "receipt", "parent-contact"])
def test_whole_output_read_keeps_primary_custody_guarded_until_delivery_ends(selected, member):
    store, definition, inputs = selected
    entry = store.begin(definition, inputs)
    store.contact(entry)
    _publish(store, entry, b"0123456789")
    _complete(store, entry)
    if member == "receipt":
        run, task, attempt = store._receipt_locator(definition)
        relative = f"runs/{run}/receipts/{task}/{attempt}.json"
    elif member == "parent-contact":
        relative = store.parent_contacts._path(definition.parent_contact.run_id, definition.parent_contact.task_id)
    else:
        relative = store._root(definition) + "/completion.json"
    iterator = store.iter_completed_output(definition, definition.outputs[0].output_id, maximum_chunk_bytes=2)
    assert next(iterator) == b"01"
    path = store.plane.root.resolve(relative, for_write=False)
    raw = path.read_bytes()
    path.write_bytes(raw[:-1] + (b" " if raw[-1:] != b" " else b"\n"))
    with pytest.raises((ArtifactIdentityConflict, BoundedFileIOError)):
        list(iterator)


def test_relocated_primary_receipt_reads_without_live_creator(selected, tmp_path):
    store, definition, inputs = selected
    entry = store.begin(definition, inputs); store.contact(entry)
    _publish(store, entry, b"exact retained independent-assessment operand")
    _complete(store, entry)
    target = tmp_path / "relocated"
    shutil.copytree(store.plane.root.contract.canonical_path, target)
    reader = _store(_plane(target), definition.parent_contact)
    assert b"".join(reader.iter_completed_output(definition, definition.outputs[0].output_id)) == b"exact retained independent-assessment operand"
    with pytest.raises(ValueError, match="substitutes"):
        list(reader.iter_completed_output(replace(definition, code_sources_sha256="f" * 64), definition.outputs[0].output_id))
    with pytest.raises(ValueError, match="substitutes"):
        reader.resolve_completed_definition(replace(definition.identity, object_fingerprint="f" * 64))
    foreign_parent = replace(definition.parent_contact, run_id="other.run", attempt_id="other.run.native.parent.attempt-001")
    foreign_reader = _store(reader.plane, foreign_parent)
    foreign_reader.parent_contacts.begin(foreign_parent)
    with pytest.raises(ValueError):
        foreign_reader.resolve_completed_definition(definition.identity)


def test_coordinator_refuses_store_bound_to_another_live_parent(selected, tmp_path):
    store, definition, inputs = selected
    context = _process_context(store, definition, inputs)
    foreign_parent = replace(definition.parent_contact, run_id="other.run",
        attempt_id="other.run.native.parent.attempt-001")
    foreign_store = ExternalNativeSubworkStore(plane=store.plane,
        parent_contacts=store.parent_contacts, parent_contact=foreign_parent,
        parent_inputs=inputs)
    foreign_store.parent_contacts.begin(foreign_parent)
    try:
        with pytest.raises(ValueError, match="store differs from its active parent"):
            NativeSubworkPipeService(foreign_store, context, tmp_path)
        assert store.inspect(definition).state is NativeSubworkState.NOT_ENTERED
    finally:
        for port in context.input_ports:
            port.close()


def test_partial_consumption_closes_pipe_reader_and_preserves_completion(selected, tmp_path):
    store, definition, inputs = selected
    entry = store.begin(definition, inputs); store.contact(entry)
    _publish(store, entry, b"0123456789"); before = _complete(store, entry)
    progress, service, context = pipe(store, definition, inputs, tmp_path)
    iterator = progress.iter_completed_output(definition, definition.outputs[0].output_id, maximum_chunk_bytes=2)
    try:
        assert next(iterator) == b"01" and len(service._readers) == 1
        iterator.close()
        assert service._readers == {} and store.recover(definition) == before
    finally:
        service.close()
        for port in context.input_ports:
            port.close()


@pytest.mark.parametrize("deadline_free,with_progress", [(False, False), (True, False), (True, True)])
def test_installed_native_progress_composes_ordinary_streams_without_buffered_result(selected, deadline_free, with_progress):
    store, first, inputs = selected
    definitions = (first, replace(first, subwork_id="forecast.three"), replace(first, subwork_id="forecast.two"))
    payload = b'{"outcome":"UNEVALUABLE"}\n' * 100_000
    context = replace(_process_context(store, first, inputs), output_ports=(WorkerOutputPort(
        "ordinary.receivers", "empirical-lawhood/tests/exposed-native-relay", ArtifactProfile.JSONL_CHUNKS,
        "application/x-ndjson"),))
    runner = ExposedNativeSubworkRelayRunner(definitions, payload, "ordinary.receivers")
    executor = LocalProcessExecutor(scratch_root=store.plane.root)
    counters = []
    try:
        if deadline_free:
            contract = ProgressLivenessContract("exposed.relay.progress", ProgressHeartbeat.SCHEMA,
                "exposed.relay.complete-byte-census", Decimal("10"), True, True) if with_progress else None
            result = executor.execute_deadline_free(runner, context, progress_contract=contract,
                progress_callback=counters.append, native_subwork=store)
        else:
            result = executor.execute(runner, context, timeout_seconds=None, native_subwork=store)
        assert len(result.outputs) == 1 and type(result.outputs[0]) is StreamedTaskOutput
        output = result.outputs[0]
        assert output.physical_sha256 == sha256(payload).hexdigest() and output.size_bytes == len(payload)
        assert b"".join(output.source.chunks(STREAM_CHUNK_BYTES)) == payload
        assert result.checks[0].passed
        assert counters == ([Decimal(1)] if with_progress else [])
        output.source.close()
        assert store.recover(first).outputs[0].materialization.physical_sha256 == sha256(payload).hexdigest()
        assert store.inspect(definitions[1]).state is NativeSubworkState.NOT_ENTERED
    finally:
        for port in context.input_ports:
            port.close()


def test_ordinary_stream_loss_keeps_completed_nested_output_without_native_replay(selected):
    store, first, inputs = selected
    definitions = (first, replace(first, subwork_id="forecast.three"), replace(first, subwork_id="forecast.two"))
    context = replace(_process_context(store, first, inputs), output_ports=(WorkerOutputPort(
        "ordinary.receivers", "empirical-lawhood/tests/exposed-native-relay", ArtifactProfile.JSONL_CHUNKS,
        "application/x-ndjson"),))
    payload = b'{"outcome":"FALSIFIED"}\n' * 100_000
    try:
        with pytest.raises(TaskProcessError):
            LocalProcessExecutor(scratch_root=store.plane.root).execute(
                ExposedNativeSubworkRelayRunner(definitions, payload, "ordinary.receivers", True),
                context, timeout_seconds=None, native_subwork=store)
        assert b"".join(store.iter_completed_output(first, first.outputs[0].output_id)) == payload
        with pytest.raises(ValueError, match="completed"):
            store.begin(first, inputs)
    finally:
        for port in context.input_ports:
            port.close()


def test_exposed_relay_working_buffers_do_not_grow_with_total_output(selected):
    store, definition, inputs = selected
    payload = b"x" * (6 * STREAM_CHUNK_BYTES + 7)
    entry = store.begin(definition, inputs); store.contact(entry)
    _publish(store, entry, payload); _complete(store, entry)
    tracemalloc.start()
    try:
        retained = sum(len(chunk) for chunk in store.iter_completed_output(definition, definition.outputs[0].output_id))
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert retained == len(payload) and peak < 6 * STREAM_CHUNK_BYTES


@pytest.mark.parametrize("copies,accepted", [(1, False), (2, True)])
def test_finite_parent_allowance_counts_both_retained_native_and_ordinary_copies(selected, copies, accepted):
    store, first, inputs = selected
    definitions = (first, replace(first, subwork_id="forecast.three"), replace(first, subwork_id="forecast.two"))
    payload = b'{"outcome":"UNEVALUABLE"}\n' * 10_000
    base = _process_context(store, first, inputs)
    context = replace(base, resource_budget=replace(base.resource_budget, output_bytes=copies * len(payload)),
        output_ports=(WorkerOutputPort("ordinary.receivers", "empirical-lawhood/tests/exposed-native-relay",
            ArtifactProfile.JSONL_CHUNKS, "application/x-ndjson"),))
    executor = LocalProcessExecutor(scratch_root=store.plane.root)
    runner = ExposedNativeSubworkRelayRunner(definitions, payload, "ordinary.receivers")
    try:
        if accepted:
            result = executor.execute(runner, context, timeout_seconds=None, native_subwork=store)
            assert result.outputs[0].size_bytes == len(payload)
            result.outputs[0].source.close()
        else:
            with pytest.raises(ResourceAdmissionError, match="combined native and ordinary"):
                executor.execute(runner, context, timeout_seconds=None, native_subwork=store)
        assert b"".join(store.iter_completed_output(first, first.outputs[0].output_id)) == payload
    finally:
        for port in context.input_ports:
            port.close()


def test_ordinary_bytes_also_reduce_a_later_nested_publication_allowance(selected, tmp_path):
    store, definition, inputs = selected
    base = _process_context(store, definition, inputs)
    context = replace(base, resource_budget=replace(base.resource_budget, output_bytes=10))
    service = NativeSubworkPipeService(store, context, tmp_path)
    try:
        assert service.account_ordinary_output_bytes(6)
        entry = service._dispatch("begin", (definition, None))
        service._dispatch("contact", (entry,))
        service._dispatch("output-open", (entry, definition.outputs[0].output_id, 9, 9, None, None))
        with pytest.raises(ValueError, match="parent output allowance"):
            service._dispatch("output-chunk", (entry, definition.outputs[0].output_id, b"FALSIFIED"))
        assert service.output_bytes == 0 and service.ordinary_output_bytes == 6
    finally:
        service.close()
        for port in context.input_ports:
            port.close()
