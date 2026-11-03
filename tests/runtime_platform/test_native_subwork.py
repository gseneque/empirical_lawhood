# SPDX-License-Identifier: MPL-2.0
"""Independent exposed crash/replay probes; no native solver or scientific authority."""

from dataclasses import dataclass, replace
from decimal import Decimal
from hashlib import sha256
import shutil
import subprocess
import sys
from typing import ClassVar

import pytest

from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane, GuardedExternalRoot
from empirical_lawhood.infrastructure.artifact_validation import ArtifactIdentityConflict
from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
from empirical_lawhood.infrastructure.native_subwork import ExternalNativeSubworkStore
from empirical_lawhood.infrastructure.native_subwork_ipc import (
    NativeSubworkPipeService, NativeSubworkRequest, PipeNativeSubworkProgress,
)
from empirical_lawhood.infrastructure.execution import LocalProcessExecutor, TaskProcessError
from empirical_lawhood.adapters.methods.native_subwork_conformance import ExposedDerivedOperand, ExposedNativeSubworkRunner
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.recursive_inquiry import InquiryCost
from empirical_lawhood.kernel.serialization import CanonicalRecord, canonical_json_bytes
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest, ExternalRootContract, ReceiptCheck
from empirical_lawhood.runtime.capabilities import CapabilityConfigRef
from empirical_lawhood.runtime.execution import RunnerResult, TaskContext, WorkerInputBinding, WorkerInputKind, WorkerIsolationProfile
from empirical_lawhood.runtime.native_effects import NativeEffectContact
from empirical_lawhood.runtime.native_subwork import (
    NativeSubworkDefinition, NativeSubworkOutput, NativeSubworkPartialOutput, NativeSubworkRoster,
    NativeSubworkState, NativeSubworkUncertainContact,
)
from empirical_lawhood.runtime.operator_profile import OperatorStorageProfile


@dataclass(frozen=True, slots=True)
class ExposedInput(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/tests/native-subwork-input"
    selected_id: str
    value: str


def _plane(path, *, binary_codecs=()):
    path.mkdir(exist_ok=True)
    path = path.resolve(strict=True)
    mount = next(candidate for candidate in (path, *path.parents) if candidate.is_mount())
    from empirical_lawhood.infrastructure.artifact_validation import ArtifactProfileValidatorRegistry
    return ExternalArtifactPlane(GuardedExternalRoot(ExternalRootContract(
        "synthetic.subwork", "exposed conformance only", str(path), str(mount),
        OperatorStorageProfile.SCHEMA, 0, None, None, (),
    )), validators=ArtifactProfileValidatorRegistry(binary_codecs=binary_codecs))


def _store(plane, parent, inputs=(), *, prepared_invocation=None):
    contacts = ExternalNativeEffectContactStore(plane=plane, execution_plan=parent.execution_plan,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE)
    return ExternalNativeSubworkStore(plane=plane, parent_contacts=contacts, parent_contact=parent,
        parent_inputs=inputs, prepared_invocation=prepared_invocation)


def _selected(tmp_path, *, freeze=True, extra_outputs=()):
    plane = _plane(tmp_path / "custody")
    records = (ExposedInput("config.selected", "293.15"), ExposedInput("source.selected", "fixed-science"),
        ExposedInput("stream.selected", "retained-driver"))
    package_sources = (("src/exposed_fixture.py", "4" * 64),)
    provenance = NumericalProducingProvenance(
        '{"python":"exposed","numpy":"exposed","scipy":"exposed","system":"Linux","machine":"exposed","threadpools":[]}',
        "5" * 64, package_sources, sha256(canonical_json_bytes(package_sources)).hexdigest(), "3" * 40, False)
    manifests = []
    for record_id, record in (*((record.selected_id, record) for record in records),
            (provenance.identity.object_id, provenance)):
        result = plane.write(ArtifactWriteRequest(
            record_id, "inputs/" + record_id + ".json", record.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, "application/json", "selected.inputs", "inputs",
            record.canonical_bytes(), VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE,
        ))
        from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest
        manifests.append(decode_artifact_manifest(plane.root.resolve(
            result.materialization.relative_path + ".manifest.json", for_write=False).read_bytes()))
    parent = NativeEffectContact("synthetic.run", "native.parent", "synthetic.run.native.parent.attempt-001",
        ObjectIdentity("plan.selected", "empirical-lawhood/runtime/development-execution-plan", "1.0.0", "1" * 64),
        ObjectIdentity("native.parent", "empirical-lawhood/runtime/execution-task", "1.0.0", "2" * 64),
        "3" * 40, tuple(sorted(m.materialization.materialization_id for m in manifests)), ())
    store = _store(plane, parent, tuple(manifests))
    store.parent_contacts.begin(parent)
    definition = NativeSubworkDefinition("forecast.one", "exposed.forecast", parent,
        ObjectIdentity.from_record(records[0].selected_id, records[0]),
        tuple(sorted((ObjectIdentity.from_record(records[1].selected_id, records[1]), provenance.identity),
            key=lambda row: row.object_id)), provenance.code_sources_sha256, provenance.dependency_lock_sha256,
        parent.input_materialization_ids, (ObjectIdentity.from_record(records[2].selected_id, records[2]),),
        tuple(sorted((NativeSubworkOutput("result.output.native", "empirical-lawhood/source/checksummed-uninterpreted-public-bytes",
            ArtifactProfile.RAW_SOURCE_BYTES, "text/plain"), *extra_outputs), key=lambda row: row.output_id)))
    definitions = (definition, replace(definition, subwork_id="forecast.three"),
        replace(definition, subwork_id="forecast.two"))
    if freeze:
        store.freeze_roster(NativeSubworkRoster("selected.native-subwork", parent,
            tuple(row.identity for row in definitions)), definitions=definitions)
    return store, definition, tuple(manifests)


@pytest.fixture
def selected(tmp_path):
    return _selected(tmp_path)


def _publish(store, entry, payload):
    return store.publish_output(entry, "result.output.native", iter((payload[:2], payload[2:])),
        maximum_bytes=max(len(payload), 1), maximum_chunk_bytes=max(len(payload), 1),
        expected_size_bytes=len(payload), expected_physical_sha256=sha256(payload).hexdigest())


def _complete(store, entry, *, failed=False, unknown_stream=False):
    return store.complete(entry, operational_status=OperationalStatus.FAILED if failed else OperationalStatus.SUCCEEDED,
        cost=InquiryCost(None, Decimal("2.500"), None), cost_scope="one native call; contained in parent window",
        consumed_streams=() if unknown_stream else entry.definition.streams,
        unknown_streams=entry.definition.streams if unknown_stream else (),
        reason_codes=("exposed-native-error",) if failed else ())


@pytest.mark.parametrize("scientific_outcome", [b"SATISFIED", b"FALSIFIED", b"UNEVALUABLE"])
def test_complete_positive_negative_and_unevaluable_recover_without_callback(selected, scientific_outcome):
    store, definition, inputs = selected
    entry = store.begin(definition, inputs)
    store.contact(entry)
    manifest = _publish(store, entry, scientific_outcome)
    completed = _complete(store, entry)
    fresh = ExternalNativeSubworkStore(plane=ExternalArtifactPlane(store.plane.root), parent_contacts=store.parent_contacts)
    recovered = fresh.recover(definition)
    assert recovered == completed
    assert recovered.completion.operational_status is OperationalStatus.SUCCEEDED
    assert recovered.completion.cost.cpu_seconds is None
    assert recovered.completion.cost.retained_bytes is None
    assert recovered.outputs == (manifest,)
    assert fresh.plane.root.resolve(manifest.materialization.relative_path, for_write=False).read_bytes() == scientific_outcome
    with pytest.raises(ValueError, match="already completed"):
        fresh.begin(definition, inputs)
    with pytest.raises(ValueError, match="completed"):
        store.contact(entry)


def test_begin_only_crash_is_distinct_from_contact_and_only_contact_creator_enters(selected):
    store, definition, inputs = selected
    abandoned = store.begin(definition, inputs)
    fresh = _store(ExternalArtifactPlane(store.plane.root), definition.parent_contact)
    assert fresh.inspect(definition).state is NativeSubworkState.BEGUN
    assert fresh.recover(definition) is None
    with pytest.raises(NativeSubworkUncertainContact, match="no live creating launch"):
        fresh.begin(definition, inputs)
    fresh = ExternalNativeSubworkStore(plane=fresh.plane, parent_contacts=store.parent_contacts)
    replacement = fresh.begin(definition, inputs)
    fresh.contact(replacement)
    with pytest.raises(NativeSubworkUncertainContact, match="only creating publisher"):
        store.contact(abandoned)
    with pytest.raises(ValueError, match="another creator"):
        store.complete(replacement, operational_status=OperationalStatus.SUCCEEDED,
            cost=InquiryCost(None, None, None), cost_scope="unknown")


def test_crash_after_contact_preserves_partial_output_and_refuses_replay(selected):
    store, definition, inputs = selected
    entry = store.begin(definition, inputs)
    store.contact(entry)
    partial = _publish(store, entry, b"exact completed native prefix")
    fresh = _store(ExternalArtifactPlane(store.plane.root), definition.parent_contact)
    inspected = fresh.inspect(definition)
    assert inspected.state is NativeSubworkState.UNKNOWN_COMPLETION
    assert inspected.outputs == (partial,) and inspected.receipt is None
    for action in (lambda: fresh.recover(definition), lambda: fresh.begin(definition, inputs)):
        with pytest.raises(NativeSubworkUncertainContact, match="no automatic retry"):
            action()


def test_known_native_error_reuses_complete_denominator_and_unknown_costs(selected):
    store, definition, inputs = selected
    entry = store.begin(definition, inputs)
    store.contact(entry)
    completed = _complete(store, entry, failed=True, unknown_stream=True)
    assert completed.state is NativeSubworkState.COMPLETED
    assert completed.receipt.operational_status is OperationalStatus.FAILED
    assert completed.completion.omitted_output_ids == ("result.output.native",)
    assert completed.completion.unknown_streams == definition.streams
    assert _store(ExternalArtifactPlane(store.plane.root), definition.parent_contact).recover(definition) == completed


def test_missing_output_or_stream_census_cannot_be_completed(selected):
    store, definition, inputs = selected
    entry = store.begin(definition, inputs)
    store.contact(entry)
    with pytest.raises(ValueError, match="omits outputs"):
        _complete(store, entry)
    _publish(store, entry, b"negative")
    with pytest.raises(ValueError, match="stream denominator"):
        store.complete(entry, operational_status=OperationalStatus.SUCCEEDED,
            cost=InquiryCost(None, None, None), cost_scope="unknown")


@pytest.mark.parametrize("field,value", [
    ("operation_id", "other.operation"), ("code_sources_sha256", "6" * 64),
    ("dependency_lock_sha256", "7" * 64), ("streams", ()), ("sources", ()), ("outputs", ()),
])
def test_substituted_selected_contract_cannot_reuse_slot(selected, field, value):
    store, definition, inputs = selected
    store.begin(definition, inputs)
    with pytest.raises(ValueError, match="substitutes source"):
        store.inspect(replace(definition, **{field: value}))


def test_missing_actual_parent_and_input_materialization_refuse_before_contact(selected):
    store, definition, inputs = selected
    with pytest.raises(ValueError, match="input materialization census"):
        store.begin(definition, inputs[:2])
    wrong_parent = replace(definition.parent_contact, attempt_id="other.attempt")
    with pytest.raises(ValueError, match="entered parent"):
        store.begin(replace(definition, parent_contact=wrong_parent), inputs)
    assert store.inspect(definition).state is NativeSubworkState.NOT_ENTERED


@pytest.mark.parametrize("failed", [False, True])
def test_receipt_publication_crash_finalizes_known_return_without_creator(selected, monkeypatch, failed):
    store, definition, inputs = selected
    entry = store.begin(definition, inputs)
    store.contact(entry)
    _publish(store, entry, b"completed calculation")
    commit = store.receipts.commit
    def interrupted(*args, **kwargs):
        raise RuntimeError("exposed crash before receipt publication")
    monkeypatch.setattr(store.receipts, "commit", interrupted)
    with pytest.raises(RuntimeError, match="before receipt"):
        _complete(store, entry, failed=failed)
    fresh = _store(ExternalArtifactPlane(store.plane.root), definition.parent_contact)
    inspected = fresh.inspect(definition)
    assert inspected.completion is not None and inspected.receipt is None
    assert inspected.state is NativeSubworkState.UNKNOWN_COMPLETION
    assert inspected.native_return_status is (OperationalStatus.FAILED if failed else OperationalStatus.SUCCEEDED)
    assert not inspected.has_uncertain_contact
    assert not fresh.parent_contacts.is_live_creator(definition.parent_contact)
    recovered = fresh.recover(definition)
    assert recovered.state is NativeSubworkState.COMPLETED
    assert recovered.completion == inspected.completion
    assert recovered.outputs == inspected.outputs
    assert recovered.completion.operational_status is (OperationalStatus.FAILED if failed else OperationalStatus.SUCCEEDED)
    assert fresh.recover(definition) == recovered
    with pytest.raises(ValueError, match="already completed"):
        fresh.begin(definition, inputs)
    # The original creator derives exactly the same receipt, without new work.
    monkeypatch.setattr(store.receipts, "commit", commit)
    assert _complete(store, entry, failed=failed) == recovered


def _known_unreceipted_return(selected, monkeypatch):
    store, definition, inputs = selected
    entry = store.begin(definition, inputs)
    store.contact(entry)
    _publish(store, entry, b"FALSIFIED")
    with monkeypatch.context() as interrupted:
        def no_receipt(*args, **kwargs):
            raise RuntimeError("exposed interruption before receipt")
        interrupted.setattr(store.receipts, "commit", no_receipt)
        with pytest.raises(RuntimeError, match="before receipt"):
            _complete(store, entry)
    return store, definition, inputs


@pytest.mark.parametrize("interrupt_publication", [False, True])
def test_new_process_finalizes_known_return_and_owned_receipt_publication(selected, monkeypatch, interrupt_publication):
    store, definition, _ = _known_unreceipted_return(selected, monkeypatch)
    script = """
from pathlib import Path
import os
import sys
from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.runtime.native_subwork import NativeSubworkDefinition
from tests.runtime_platform.test_native_subwork import _plane, _store
raw = bytes.fromhex(sys.argv[2])
definition = decode_canonical_bytes(raw, NativeSubworkDefinition, maximum_bytes=len(raw))
store = _store(_plane(Path(sys.argv[1])), definition.parent_contact)
assert not store.parent_contacts.is_live_creator(definition.parent_contact)
def no_entry(*args, **kwargs):
    raise AssertionError('finalization entered native work')
store.begin = store.contact = no_entry
if sys.argv[3] == 'interrupt':
    move = ExternalArtifactPlane._move_file_once
    def interrupted(source, destination):
        move(source, destination)
        if '/receipts/' in str(destination) and str(destination).endswith('.json') and not str(destination).endswith('.manifest.json'):
            os._exit(77)
    ExternalArtifactPlane._move_file_once = staticmethod(interrupted)
result = store.recover(definition)
assert result.state.value == 'COMPLETED'
sys.stdout.buffer.write(result.receipt.canonical_bytes())
"""
    command = [sys.executable, "-c", script, store.plane.root.contract.canonical_path,
        definition.canonical_bytes().hex(), "interrupt" if interrupt_publication else "recover"]
    if interrupt_publication:
        interrupted = subprocess.run(command, capture_output=True, check=False)
        assert interrupted.returncode == 77, interrupted.stderr.decode()
        with pytest.raises(ArtifactIdentityConflict, match="partial"):
            store.inspect(definition)
        command[-1] = "recover"
    recovered = subprocess.run(command, capture_output=True, check=False)
    assert recovered.returncode == 0, recovered.stderr.decode()
    result = store.inspect(definition)
    assert result.state is NativeSubworkState.COMPLETED
    assert result.receipt.canonical_bytes() == recovered.stdout
    assert b"".join(store.iter_completed_output(definition, "result.output.native")) == b"FALSIFIED"


def test_concurrent_finalizers_publish_the_same_receipt_without_entry(selected, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    store, definition, _ = _known_unreceipted_return(selected, monkeypatch)
    ready = Barrier(2)
    def recover():
        reader = _store(ExternalArtifactPlane(store.plane.root), definition.parent_contact)
        ready.wait()
        return reader.recover(definition)
    with ThreadPoolExecutor(max_workers=2) as workers:
        results = tuple(workers.map(lambda _: recover(), range(2)))
    assert results[0] == results[1] == store.inspect(definition)
    assert results[0].state is NativeSubworkState.COMPLETED


@pytest.mark.parametrize("changed", ["output", "completion", "contact", "access"])
def test_finalization_refuses_changed_or_missing_completion_custody(selected, monkeypatch, changed):
    store, definition, _ = _known_unreceipted_return(selected, monkeypatch)
    before = store.inspect(definition)
    if changed != "access":
        relative = (before.outputs[0].materialization.relative_path if changed == "output"
            else store._root(definition) + "/" + changed + ".json")
        path = store.plane.root.resolve(relative, for_write=False)
        if changed == "output":
            path.write_bytes(b"corrupted")
        else:
            path.unlink()
    reader = _store(ExternalArtifactPlane(store.plane.root), definition.parent_contact)
    if changed == "access":
        reader.parent_contacts.outcome_access = OutcomeAccess.EVALUATION_SEALED
    with pytest.raises((ValueError, ArtifactIdentityConflict)):
        reader.recover(definition)
    assert reader.receipts.read(*reader._receipt_locator(definition)) is None


def test_partial_wave_portable_recovery_uses_exact_completed_and_uncertain_slots(selected, tmp_path):
    store, first, inputs = selected
    second = replace(first, subwork_id="forecast.two")
    third = replace(first, subwork_id="forecast.three")
    complete = store.begin(first, inputs)
    store.contact(complete)
    _publish(store, complete, b"negative first forecast")
    _complete(store, complete)
    interrupted = store.begin(second, inputs)
    store.contact(interrupted)
    target = tmp_path / "relocated"
    shutil.copytree(store.plane.root.contract.canonical_path, target)
    relocated = _store(_plane(target), first.parent_contact)
    progress = list(relocated.iter_inspections(iter((first, second, third))))
    assert [row.state for row in progress] == [NativeSubworkState.COMPLETED,
        NativeSubworkState.UNKNOWN_COMPLETION, NativeSubworkState.NOT_ENTERED]
    assert relocated.recover(first).receipt == store.recover(first).receipt
    with pytest.raises(NativeSubworkUncertainContact):
        relocated.recover(second)


def test_streamed_output_tamper_refuses_complete_recovery(selected):
    store, definition, inputs = selected
    entry = store.begin(definition, inputs)
    store.contact(entry)
    manifest = _publish(store, entry, b"immutable array bytes")
    _complete(store, entry)
    path = store.plane.root.resolve(manifest.materialization.relative_path, for_write=True)
    path.write_bytes(b"corrupted array bytes")
    with pytest.raises(ArtifactIdentityConflict, match="bytes differ|changed during its verification scope"):
        _store(ExternalArtifactPlane(store.plane.root), definition.parent_contact).recover(definition)


def test_persisted_or_retired_parent_cannot_enter_unstarted_child(selected):
    store, definition, inputs = selected
    reader = _store(ExternalArtifactPlane(store.plane.root), definition.parent_contact)
    with pytest.raises(NativeSubworkUncertainContact, match="no live creating launch"):
        reader.begin(definition, inputs)
    entry = store.begin(definition, inputs)
    store.parent_contacts.retire_live_creator(definition.parent_contact)
    with pytest.raises(NativeSubworkUncertainContact, match="no live creating launch"):
        store.contact(entry)
    assert reader.inspect(definition).state is NativeSubworkState.BEGUN


def _context(definition, inputs):
    parent = definition.parent_contact
    bindings = tuple(sorted((WorkerInputBinding(
        artifact_id=m.logical.logical_artifact_id, materialization_id=m.materialization.materialization_id,
        kind=WorkerInputKind.EXTERNAL, payload_schema=m.logical.payload_schema,
        media_type=m.logical.media_type,
        size_bytes=m.materialization.size_bytes, visibility_ceiling=m.logical.visibility_ceiling,
        outcome_access=m.logical.outcome_access,
    ) for m in inputs), key=lambda value: value.artifact_id))
    # Actual ports are constructed by the existing guarded owner, never by the fixture engine.
    return parent, bindings


def _process_context(store, definition, inputs):
    parent, bindings = _context(definition, inputs)
    by_id = {m.logical.logical_artifact_id: m for m in inputs}
    ports = tuple(store.plane.open(by_id[binding.artifact_id], binding=binding,
        maximum_bytes=by_id[binding.artifact_id].materialization.size_bytes) for binding in bindings)
    return TaskContext(parent.run_id, parent.task_id, parent.attempt_id,
        CapabilityConfigRef("config.selected", definition.configuration.object_schema, "6" * 64,
            definition.configuration.object_fingerprint, "config.selected"), bindings, ports, (), (),
        OutcomeAccess.DEVELOPMENT_VISIBLE, ResourceBudget(1, None, 0, None, None, None),
        WorkerIsolationProfile.TRUSTED_LOCAL)


@pytest.mark.parametrize("deadline_free", [False, True])
def test_installed_spawned_adapter_retains_exact_positive_negative_unevaluable(selected, deadline_free):
    store, first, inputs = selected
    definitions = (first, replace(first, subwork_id="forecast.two"), replace(first, subwork_id="forecast.three"))
    outcomes = (b"SATISFIED", b"FALSIFIED", b"UNEVALUABLE")
    context = _process_context(store, first, inputs)
    executor = LocalProcessExecutor(scratch_root=store.plane.root)
    try:
        runner = ExposedNativeSubworkRunner(definitions, outcomes)
        if deadline_free:
            result = executor.execute_deadline_free(runner, context, progress_contract=None,
                progress_callback=lambda _: None, native_subwork=store)
        else:
            result = executor.execute(runner, context, timeout_seconds=None, native_subwork=store)
    finally:
        for port in context.input_ports:
            port.close()
    assert result.checks[0].passed
    reader = _store(ExternalArtifactPlane(store.plane.root), first.parent_contact)
    for definition, outcome in zip(definitions, outcomes, strict=True):
        recovered = reader.recover(definition)
        assert recovered.completion.operational_status is OperationalStatus.SUCCEEDED
        assert recovered.outputs[0].logical.content_sha256 == sha256(outcome).hexdigest()
        assert recovered.completion.peak_rss_bytes > 0
        assert recovered.completion.cost.cpu_seconds >= 0


@pytest.mark.parametrize("failure_point,expected", [
    ("before-contact", NativeSubworkState.BEGUN),
    ("after-contact", NativeSubworkState.UNKNOWN_COMPLETION),
    ("during-output", NativeSubworkState.UNKNOWN_COMPLETION),
    ("before-first-output-chunk", NativeSubworkState.UNKNOWN_COMPLETION),
])
def test_spawned_adapter_process_loss_retains_exact_entry_boundary(selected, failure_point, expected):
    store, definition, inputs = selected
    context = _process_context(store, definition, inputs)
    try:
        with pytest.raises(TaskProcessError, match="exited without a typed result"):
            LocalProcessExecutor(scratch_root=store.plane.root).execute(
                ExposedNativeSubworkRunner((definition,), (b"negative",), failure_point),
                context, timeout_seconds=None, native_subwork=store)
    finally:
        for port in context.input_ports:
            port.close()
        store.parent_contacts.retire_live_creator(definition.parent_contact)
    reader = _store(ExternalArtifactPlane(store.plane.root), definition.parent_contact)
    assert reader.inspect(definition).state is expected
    assert reader.inspect(definition).outputs == ()
    if failure_point == "during-output":
        partial = reader.inspect(definition)
        assert partial.partial_output_records[0].received_size_bytes == 2
        assert partial.partial_output_records[0].received_physical_sha256 == sha256(b"ne").hexdigest()
        assert partial.partial_outputs[0].logical.profile is ArtifactProfile.NATIVE_SUBWORK_PREFIX
        assert partial.partial_output_records[0].reason_codes == ("native-output-transport-interrupted",)
    if failure_point == "before-first-output-chunk":
        partial = reader.inspect(definition)
        assert partial.partial_output_records[0].received_size_bytes == 0
        assert partial.partial_output_records[0].received_physical_sha256 == sha256(b"").hexdigest()
        assert partial.partial_outputs[0].materialization.size_bytes == 0
    with pytest.raises(NativeSubworkUncertainContact):
        reader.begin(definition, inputs)


def test_spawned_adapter_partial_wave_retains_full_selected_denominator(selected):
    store, first, inputs = selected
    second = replace(first, subwork_id="forecast.two")
    context = _process_context(store, first, inputs)
    try:
        with pytest.raises(TaskProcessError):
            LocalProcessExecutor(scratch_root=store.plane.root).execute(
                ExposedNativeSubworkRunner((first, second), (b"FALSIFIED", b"UNEVALUABLE"), "after-first"),
                context, timeout_seconds=None, native_subwork=store)
    finally:
        for port in context.input_ports:
            port.close()
        store.parent_contacts.retire_live_creator(first.parent_contact)
    reader = _store(ExternalArtifactPlane(store.plane.root), first.parent_contact)
    assert reader.recover(first).completion.output_ids == ("result.output.native",)
    assert reader.inspect(second).state is NativeSubworkState.UNKNOWN_COMPLETION
    assert [state for _, state in reader.iter_roster_states(first.parent_contact)] == [
        NativeSubworkState.COMPLETED, NativeSubworkState.NOT_ENTERED, NativeSubworkState.UNKNOWN_COMPLETION]


def test_spawned_adapter_caught_memory_error_has_failed_receipt_not_unknown_or_positive(selected):
    store, definition, inputs = selected
    context = _process_context(store, definition, inputs)
    try:
        LocalProcessExecutor(scratch_root=store.plane.root).execute(
            ExposedNativeSubworkRunner((definition,), (b"unused",), "memory-error"),
            context, timeout_seconds=None, native_subwork=store)
    finally:
        for port in context.input_ports:
            port.close()
        store.parent_contacts.retire_live_creator(definition.parent_contact)
    completed = _store(ExternalArtifactPlane(store.plane.root), definition.parent_contact).recover(definition)
    assert completed.receipt.operational_status is OperationalStatus.FAILED
    assert completed.completion.omitted_output_ids == ("result.output.native",)
    assert completed.completion.unknown_streams == definition.streams
    assert completed.completion.reason_codes == ("exposed-native-memory-error",)
    assert completed.completion.cost.retained_bytes is None


def test_conditional_roster_requires_live_entered_parent_and_preserves_initial_denominator(selected):
    store, definition, inputs = selected
    conditional = replace(definition, subwork_id="forecast.one.initializer",
        operation_id="exposed.initializer", roster_id="conditional.initializer")
    roster = NativeSubworkRoster(conditional.roster_id, definition.parent_contact,
        (conditional.identity,), definition.identity)
    with pytest.raises(ValueError, match="another creator"):
        store.freeze_roster(roster, definitions=(conditional,))
    main = store.begin(definition, inputs)
    with pytest.raises(ValueError, match="precedes creating native contact"):
        store.freeze_roster(roster, main, definitions=(conditional,))
    store.contact(main)
    store.freeze_roster(roster, main, definitions=(conditional,))
    segment = store.begin(conditional, inputs)
    store.contact(segment)
    _publish(store, segment, b"UNEVALUABLE")
    _complete(store, segment)
    reader = _store(ExternalArtifactPlane(store.plane.root), definition.parent_contact)
    assert reader.inspect(definition).state is NativeSubworkState.UNKNOWN_COMPLETION
    assert reader.recover(conditional).completion.operational_status is OperationalStatus.SUCCEEDED
    assert {row.roster_id for row in reader.iter_rosters(definition.parent_contact)} == {
        "selected.native-subwork", conditional.roster_id}
    assert len(list(reader.iter_roster_states(definition.parent_contact))) == 3


def test_spawned_adapter_completed_conditional_segment_survives_parent_forecast_death(selected):
    store, definition, inputs = selected
    context = _process_context(store, definition, inputs)
    try:
        with pytest.raises(TaskProcessError):
            LocalProcessExecutor(scratch_root=store.plane.root).execute(
                ExposedNativeSubworkRunner((definition,), (b"unused",), "after-conditional"),
                context, timeout_seconds=None, native_subwork=store)
    finally:
        for port in context.input_ports:
            port.close()
        store.parent_contacts.retire_live_creator(definition.parent_contact)
    reader = _store(ExternalArtifactPlane(store.plane.root), definition.parent_contact)
    conditional = replace(definition, subwork_id=definition.subwork_id + ".segment.one",
        operation_id="exposed.conditional-segment", roster_id="conditional.segment.one")
    assert reader.inspect(definition).state is NativeSubworkState.UNKNOWN_COMPLETION
    assert reader.recover(conditional).outputs[0].logical.content_sha256 == sha256(b"FALSIFIED").hexdigest()
    assert [state for _, state in reader.iter_roster_states(definition.parent_contact)] == [
        NativeSubworkState.UNKNOWN_COMPLETION, NativeSubworkState.NOT_ENTERED, NativeSubworkState.NOT_ENTERED]
    assert [state for _, state in reader.iter_roster_states(definition.parent_contact, conditional.roster_id)] == [
        NativeSubworkState.COMPLETED]


def test_full_frozen_operands_of_unentered_units_survive_relocation(selected, tmp_path):
    store, first, _ = selected
    expected = (first, replace(first, subwork_id="forecast.three"), replace(first, subwork_id="forecast.two"))
    target = tmp_path / "relocated"
    shutil.copytree(store.plane.root.contract.canonical_path, target)
    reader = _store(_plane(target), first.parent_contact)
    assert tuple(reader.iter_roster_definitions(first.parent_contact)) == expected
    assert [state for _, state in reader.iter_roster_states(first.parent_contact)] == [NativeSubworkState.NOT_ENTERED] * 3


def test_initial_roster_cannot_omit_full_definition_operands(tmp_path):
    store, first, inputs = _selected(tmp_path, freeze=False)
    second = replace(first, subwork_id="forecast.two")
    roster = NativeSubworkRoster("selected.native-subwork", first.parent_contact, (first.identity, second.identity))
    with pytest.raises(ValueError, match="complete selected definitions"):
        store.freeze_roster(roster, definitions=(first,))
    assert store.inspect(first).state is NativeSubworkState.NOT_ENTERED
    with pytest.raises(ValueError, match="frozen selected denominator"):
        store.begin(first, inputs)
    with pytest.raises(ValueError, match="one complete initial"):
        NativeSubworkRoster("additional.initial-units", first.parent_contact, (first.identity,))


def test_installed_spawned_adapter_freezes_complete_operands_before_entry(tmp_path):
    store, first, inputs = _selected(tmp_path, freeze=False)
    full = (first, replace(first, subwork_id="forecast.three"), replace(first, subwork_id="forecast.two"))
    context = _process_context(store, first, inputs)
    try:
        with pytest.raises(TaskProcessError):
            LocalProcessExecutor(scratch_root=store.plane.root).execute(
                ExposedNativeSubworkRunner((first,), (b"unused",), "before-contact", full),
                context, timeout_seconds=None, native_subwork=store)
    finally:
        for port in context.input_ports:
            port.close()
    reader = _store(ExternalArtifactPlane(store.plane.root), first.parent_contact)
    assert tuple(reader.iter_roster_definitions(first.parent_contact)) == full
    assert [state for _, state in reader.iter_roster_states(first.parent_contact)] == [
        NativeSubworkState.BEGUN, NativeSubworkState.NOT_ENTERED, NativeSubworkState.NOT_ENTERED]
    assert not store.parent_contacts.is_live_creator(first.parent_contact)


def test_conditional_child_cannot_enter_after_its_live_parent_completes(selected):
    store, first, inputs = selected
    parent_entry = store.begin(first, inputs)
    store.contact(parent_entry)
    child = replace(first, subwork_id="forecast.one.segment", roster_id="conditional.segment")
    store.freeze_roster(NativeSubworkRoster(child.roster_id, first.parent_contact, (child.identity,), first.identity),
        parent_entry, definitions=(child,))
    _publish(store, parent_entry, b"negative")
    _complete(store, parent_entry)
    with pytest.raises(ValueError, match="completed"):
        store.begin(child, inputs)
    assert store.inspect(child).state is NativeSubworkState.NOT_ENTERED


@pytest.mark.parametrize("field,value", [("code_sources_sha256", "a" * 64), ("dependency_lock_sha256", "b" * 64)])
def test_frozen_digest_labels_cannot_replace_authenticated_producing_bytes(selected, field, value):
    store, first, inputs = selected
    parent_entry = store.begin(first, inputs)
    store.contact(parent_entry)
    child = replace(first, subwork_id="forecast.one.wrong-source", roster_id="conditional.wrong-source", **{field: value})
    store.freeze_roster(NativeSubworkRoster(child.roster_id, first.parent_contact, (child.identity,), first.identity),
        parent_entry, definitions=(child,))
    with pytest.raises(ValueError, match="actual producing source or dependency lock"):
        store.begin(child, inputs)
    assert store.inspect(child).state is NativeSubworkState.NOT_ENTERED


@pytest.mark.parametrize("role", ["configuration", "source", "stream"])
def test_selected_canonical_identity_cannot_mislabel_record_revision(selected, role):
    store, first, inputs = selected
    parent_entry = store.begin(first, inputs)
    store.contact(parent_entry)
    changes = {"subwork_id": "forecast.one.wrong-revision", "roster_id": "conditional.wrong-revision"}
    if role == "configuration":
        changes["configuration"] = replace(first.configuration, object_version="2.0.0")
    elif role == "source":
        changes["sources"] = tuple(replace(row, object_version="2.0.0")
            if row.object_schema == ExposedInput.SCHEMA else row for row in first.sources)
    else:
        changes["streams"] = (replace(first.streams[0], object_version="2.0.0"),)
    child = replace(first, **changes)
    store.freeze_roster(NativeSubworkRoster(child.roster_id, first.parent_contact, (child.identity,), first.identity),
        parent_entry, definitions=(child,))
    with pytest.raises(ValueError, match="record version"):
        store.begin(child, inputs)
    assert store.inspect(child).state is NativeSubworkState.NOT_ENTERED


@pytest.mark.parametrize("missing", ["begin", "contact"])
def test_missing_earlier_records_cannot_hide_actual_contact_or_completed_output(selected, missing):
    store, first, inputs = selected
    entry = store.begin(first, inputs)
    store.contact(entry)
    _publish(store, entry, b"completed negative output")
    for suffix in (".json", ".json.manifest.json"):
        store.plane.root.resolve(store._root(first) + "/" + missing + suffix, for_write=True).unlink()
    with pytest.raises(NativeSubworkUncertainContact, match="earlier progress|without earlier"):
        store.inspect(first)


@pytest.mark.parametrize("missing", ["begin", "contact"])
def test_retained_partial_metadata_cannot_hide_contact_when_its_prefix_is_lost(selected, missing):
    store, first, inputs = selected
    entry = store.begin(first, inputs)
    store.contact(entry)
    record = NativeSubworkPartialOutput(first.identity, store._contact_identity(entry),
        "result.output.native", 9, 9, sha256(b"FALSIFIED").hexdigest(), 2, sha256(b"FA").hexdigest(),
        ("exposed-native-output-aborted",))
    store.retain_partial_output(entry, record, iter((b"FA",)))
    shutil.rmtree(store.plane.root.resolve(store._root(first) + "/partial-outputs", for_write=True))
    for suffix in (".json", ".json.manifest.json"):
        store.plane.root.resolve(store._root(first) + "/" + missing + suffix, for_write=True).unlink()
    with pytest.raises(NativeSubworkUncertainContact, match="earlier progress"):
        store.inspect(first)


@pytest.mark.parametrize("failure_point,prefix_bytes", [
    ("memory-error-during-output", b"FA"), ("memory-error-before-first-output-chunk", b""),
])
def test_caught_output_memory_error_retains_prefix_with_failed_receipt_and_portable_recovery(selected, tmp_path,
        failure_point, prefix_bytes):
    store, first, inputs = selected
    context = _process_context(store, first, inputs)
    try:
        LocalProcessExecutor(scratch_root=store.plane.root).execute(
            ExposedNativeSubworkRunner((first,), (b"FALSIFIED",), failure_point),
            context, timeout_seconds=None, native_subwork=store)
    finally:
        for port in context.input_ports:
            port.close()
    target = tmp_path / "relocated"
    shutil.copytree(store.plane.root.contract.canonical_path, target)
    reader = _store(_plane(target), first.parent_contact)
    recovered = reader.recover(first)
    assert recovered.state is NativeSubworkState.COMPLETED
    assert recovered.completion.operational_status is OperationalStatus.FAILED
    assert recovered.outputs == ()
    assert recovered.completion.omitted_output_ids == ("result.output.native",)
    assert recovered.completion.unknown_streams == first.streams
    assert recovered.completion.cost.retained_bytes is None
    record = recovered.partial_output_records[0]
    assert (record.received_size_bytes, record.received_physical_sha256) == (
        len(prefix_bytes), sha256(prefix_bytes).hexdigest())
    assert record.expected_size_bytes == 9
    assert record.reason_codes == ("native-output-generator-aborted",)
    prefix = recovered.partial_outputs[0]
    assert reader.plane.root.resolve(prefix.materialization.relative_path, for_write=False).read_bytes() == prefix_bytes
    assert prefix.logical in recovered.receipt.output_logical_artifacts
    assert len(recovered.receipt.output_logical_artifacts) == 3  # prefix, partial metadata, completion
    reader.plane.root.resolve(prefix.materialization.relative_path, for_write=True).write_bytes(b"XX")
    with pytest.raises(ArtifactIdentityConflict):
        reader.recover(first)


def test_spawned_conditional_child_uses_frozen_operand_from_its_actual_live_parent(tmp_path):
    extra = (NativeSubworkOutput("derived.configuration", ExposedDerivedOperand.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, "application/json"),)
    store, first, inputs = _selected(tmp_path, extra_outputs=extra)
    context = _process_context(store, first, inputs)
    try:
        LocalProcessExecutor(scratch_root=store.plane.root).execute(
            ExposedNativeSubworkRunner((first,), (b"FALSIFIED",), "derived-conditional"),
            context, timeout_seconds=None, native_subwork=store)
    finally:
        for port in context.input_ports:
            port.close()
    reader = _store(ExternalArtifactPlane(store.plane.root), first.parent_contact)
    child = next(reader.iter_roster_definitions(first.parent_contact, "conditional.derived-segment"))
    derived = ExposedDerivedOperand("exposed.derived-configuration", first.parent_contact.task_id,
        sha256(b"FALSIFIED").hexdigest())
    assert child.configuration == derived.identity
    assert len(child.input_materialization_ids) == len(first.input_materialization_ids) + 1
    parent = reader.recover(first)
    operand_manifest = next(row for row in parent.outputs if row.logical.payload_schema == derived.SCHEMA)
    assert operand_manifest.materialization.materialization_id in child.input_materialization_ids
    assert reader.recover(child).outputs[0].logical.content_sha256 == sha256(b"UNEVALUABLE").hexdigest()
    assert reader.read_roster(first.parent_contact, child.roster_id).parent_subwork == first.identity


@pytest.mark.parametrize("state", ["not-entered", "contacted", "completed"])
@pytest.mark.parametrize("loss", ["absent", "empty"])
def test_lost_full_selected_directory_never_becomes_new_work_with_live_creator(selected, state, loss):
    store, first, inputs = selected
    definitions = tuple(store.iter_roster_definitions(first.parent_contact))
    roster = store.read_roster(first.parent_contact)
    roster_path = store.plane.root.resolve(store._roster_path(first.parent_contact, roster.roster_id), for_write=False)
    original_roster_bytes = roster_path.read_bytes()
    if state != "not-entered":
        entry = store.begin(first, inputs)
        store.contact(entry)
        if state == "completed":
            _publish(store, entry, b"FALSIFIED")
            receipt = _complete(store, entry).receipt
    directory = store.plane.root.resolve(store._root(first), for_write=True)
    shutil.rmtree(directory)
    if loss == "empty":
        directory.mkdir()
    if state == "completed":
        assert store.receipts.read(*store._receipt_locator(first)) == receipt
    calls = []

    def attempt():
        new_entry = store.begin(first, inputs)
        store.contact(new_entry)
        calls.append("native effect would have entered")

    for action in (
        lambda: store.inspect(first), lambda: store.recover(first),
        lambda: list(store.iter_roster_states(first.parent_contact)),
        lambda: list(store.iter_roster_definitions(first.parent_contact)),
        attempt, lambda: store.freeze_roster(roster, definitions=definitions),
    ):
        with pytest.raises(ValueError, match="definition|operands"):
            action()
    assert store.parent_contacts.is_live_creator(first.parent_contact)
    assert calls == []
    assert roster_path.read_bytes() == original_roster_bytes
    assert not (directory / "definition.json").exists()


def test_surviving_completion_receipt_refuses_even_when_definition_and_roster_directories_are_lost(selected):
    store, first, inputs = selected
    definitions = tuple(store.iter_roster_definitions(first.parent_contact))
    roster = store.read_roster(first.parent_contact)
    entry = store.begin(first, inputs)
    store.contact(entry)
    _publish(store, entry, b"FALSIFIED")
    receipt = _complete(store, entry).receipt
    shutil.rmtree(store.plane.root.resolve(store._root(first), for_write=True))
    shutil.rmtree(store.plane.root.resolve(store._roster_root(first.parent_contact), for_write=True))
    assert store.receipts.read(*store._receipt_locator(first)) == receipt
    for action in (lambda: store.inspect(first), lambda: store.recover(first),
            lambda: store.begin(first, inputs), lambda: store.freeze_roster(roster, definitions=definitions)):
        with pytest.raises(NativeSubworkUncertainContact, match="receipt without earlier"):
            action()
    for action in (lambda: list(store.iter_roster_states(first.parent_contact)),
            lambda: list(store.iter_roster_definitions(first.parent_contact))):
        with pytest.raises(ValueError, match="retained selected full denominator"):
            action()
    assert store.read_roster(first.parent_contact) is None


def test_unselected_work_is_not_entered_and_cannot_begin(selected):
    store, first, inputs = selected
    unselected = replace(first, subwork_id="forecast.unselected")
    assert store.inspect(unselected).state is NativeSubworkState.NOT_ENTERED
    assert store.recover(unselected) is None
    with pytest.raises(ValueError, match="outside its frozen"):
        store.begin(unselected, inputs)
    assert not store.plane.root.resolve(store._root(unselected), for_write=False).exists()


@pytest.mark.parametrize("state", ["not-entered", "contacted", "completed"])
def test_actual_spawned_adapter_refuses_lost_selected_directory_before_replay(selected, state):
    store, first, inputs = selected
    if state != "not-entered":
        entry = store.begin(first, inputs)
        store.contact(entry)
        if state == "completed":
            _publish(store, entry, b"FALSIFIED")
            _complete(store, entry)
    directory = store.plane.root.resolve(store._root(first), for_write=True)
    shutil.rmtree(directory)
    context = _process_context(store, first, inputs)
    try:
        with pytest.raises(TaskProcessError, match="typed failure") as failure:
            LocalProcessExecutor(scratch_root=store.plane.root).execute(
                ExposedNativeSubworkRunner((first,), (b"must not replay",)), context,
                timeout_seconds=None, native_subwork=store)
        assert failure.value.sanitized_exception_type == "NativeSubworkUncertainContact"
    finally:
        for port in context.input_ports:
            port.close()
    assert not (directory / "definition.json").exists()
    assert not (directory / "contact.json").exists()


@dataclass(frozen=True, slots=True)
class _ChunkAllowanceRunner:
    definition: NativeSubworkDefinition
    chunks: tuple[bytes, ...]
    maximum_bytes: int
    maximum_chunk_bytes: int | None = None

    def execute_with_native_subwork(self, context, native_subwork, progress=None):
        entry = native_subwork.begin(self.definition)
        native_subwork.contact(entry)
        options = {} if self.maximum_chunk_bytes is None else {"maximum_chunk_bytes": self.maximum_chunk_bytes}
        try:
            native_subwork.publish_output(entry, "result.output.native", self.chunks,
                maximum_bytes=self.maximum_bytes, **options)
        except ValueError:
            native_subwork.complete(entry, operational_status=OperationalStatus.FAILED,
                cost=InquiryCost(None, None, None), cost_scope="exposed invalid output contract",
                unknown_streams=self.definition.streams, reason_codes=("exposed-invalid-output",))
        else:
            native_subwork.complete(entry, operational_status=OperationalStatus.SUCCEEDED,
                cost=InquiryCost(None, None, Decimal(sum(map(len, self.chunks)))),
                cost_scope="exposed complete output bytes", consumed_streams=self.definition.streams)
        return RunnerResult((), (ReceiptCheck("exposed-chunk-allowance-return-retained", True, ()),))


@pytest.mark.parametrize("payload", [b"F", b"FALSIFIED", b"x" * 100])
@pytest.mark.parametrize("route", ["direct", "spawned"])
def test_tiny_whole_output_accepts_default_source_chunk_allowance(selected, payload, route):
    store, first, inputs = selected
    if route == "direct":
        entry = store.begin(first, inputs)
        store.contact(entry)
        store.publish_output(entry, "result.output.native", (payload,), maximum_bytes=len(payload),
            expected_size_bytes=len(payload), expected_physical_sha256=sha256(payload).hexdigest())
        _complete(store, entry)
    else:
        context = _process_context(store, first, inputs)
        try:
            LocalProcessExecutor(scratch_root=store.plane.root).execute(
                _ChunkAllowanceRunner(first, (payload,), len(payload)), context,
                timeout_seconds=None, native_subwork=store)
        finally:
            for port in context.input_ports:
                port.close()
    recovered = store.recover(first)
    assert recovered.completion.operational_status is OperationalStatus.SUCCEEDED
    manifest = recovered.outputs[0]
    assert manifest.materialization.size_bytes == len(payload)
    assert manifest.logical.content_sha256 == sha256(payload).hexdigest()
    assert store.plane.root.resolve(manifest.materialization.relative_path, for_write=False).read_bytes() == payload


@pytest.mark.parametrize("route", ["direct", "spawned"])
def test_transport_rechunking_does_not_relax_original_source_chunk_allowance(selected, route):
    store, first, inputs = selected
    if route == "direct":
        entry = store.begin(first, inputs)
        store.contact(entry)
        with pytest.raises(ValueError, match="immutable chunk contract"):
            store.publish_output(entry, "result.output.native", (b"xxxxx",),
                maximum_bytes=100, maximum_chunk_bytes=4)
        assert store.inspect(first).outputs == ()
    else:
        context = _process_context(store, first, inputs)
        try:
            LocalProcessExecutor(scratch_root=store.plane.root).execute(
                _ChunkAllowanceRunner(first, (b"FA", b"xxxxx"), 100, 4), context,
                timeout_seconds=None, native_subwork=store)
        finally:
            for port in context.input_ports:
                port.close()
        recovered = store.recover(first)
        assert recovered.completion.operational_status is OperationalStatus.FAILED
        assert recovered.outputs == ()
        assert recovered.partial_output_records[0].received_size_bytes == 2


@pytest.mark.parametrize("parameters", [
    {"maximum_bytes": True}, {"maximum_bytes": 0}, {"maximum_bytes": -1}, {"maximum_bytes": 1.5},
    {"maximum_chunk_bytes": True}, {"maximum_chunk_bytes": 0}, {"maximum_chunk_bytes": -1},
    {"expected_size_bytes": True, "expected_physical_sha256": "0" * 64},
    {"expected_size_bytes": -1, "expected_physical_sha256": "0" * 64},
])
@pytest.mark.parametrize("route", ["direct", "pipe"])
def test_invalid_output_integer_parameters_refuse_without_consuming_source(selected, parameters, route, tmp_path):
    store, first, inputs = selected
    context = None
    progress = store
    if route == "pipe":
        context = _process_context(store, first, inputs)
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
    entry = progress.begin(first)
    progress.contact(entry)
    consumed = []

    def chunks():
        consumed.append(True)
        yield b"F"

    try:
        with pytest.raises(ValueError, match="allowance"):
            progress.publish_output(entry, "result.output.native", chunks(), **{"maximum_bytes": 100, **parameters})
        if route == "pipe":
            options = {"maximum_bytes": 100, "maximum_chunk_bytes": 100,
                "expected_size_bytes": None, "expected_physical_sha256": None, **parameters}
            with pytest.raises(ValueError, match="allowance"):
                service._dispatch("output-open", (entry.handle, "result.output.native",
                    options["maximum_bytes"], options["maximum_chunk_bytes"],
                    options["expected_size_bytes"], options["expected_physical_sha256"]))
            assert service._stages == {}
    finally:
        if context is not None:
            for port in context.input_ports:
                port.close()
    assert consumed == []
    assert store.inspect(first).outputs == ()
