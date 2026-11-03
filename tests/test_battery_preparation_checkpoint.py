# SPDX-License-Identifier: MPL-2.0
"""Exposed coordinator-loss controls through actual compact custody owners.

The backend is the existing declared fake battery model, not PyBaMM execution
or scientific qualification. Real process death tests original receipt recovery.
"""
from dataclasses import replace
import multiprocessing
import signal
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.battery_refined_inquiry import forecast_step_control as step
from empirical_lawhood.adapters.methods.battery_refined_inquiry import lossless_segment_native as storage
from empirical_lawhood.adapters.methods.battery_refined_inquiry import lossless_segment_records as records
from empirical_lawhood.adapters.methods.battery_refined_inquiry import preparation_contracts as pc
from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_native as native
from empirical_lawhood.adapters.methods.battery_segmented_inquiry import evidence_stream as stream
from empirical_lawhood.runtime.native_subwork import NativeSubworkOutput, NativeSubworkState, NativeSubworkUncertainContact
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.kernel.status import OperationalStatus
from tests.test_battery_forecast_step_control import config as step_config_fixture, selected as step_selected_fixture, witness
from tests.test_battery_segmented_native import custody as custody_fixture, exposed_backend, acquire
from tests.test_battery_refined_inquiry import selected as native_selected_fixture

custody = custody_fixture
selected = native_selected_fixture
controlled_selected = step_selected_fixture


@pytest.fixture
def controlled_config(controlled_selected):
    return step_config_fixture.__wrapped__(controlled_selected)


def checkpoint_records(custody, inspection):
    return {name: stream.completed_record(custody.store, inspection.definition, inspection, name, kind)
        for name, kind in (("protocol", pc.PreparationProtocol), ("source-assignment", native.ActualSourceAssignment),
            ("layout", pc.ProcessedInitialStateLayout), ("native.request.first", native.SegmentRequest))}


@pytest.mark.parametrize("stop_before_call", (1, 2))
def test_actual_process_death_retains_context_before_first_call_and_closed_prefix(custody, monkeypatch, tmp_path, stop_before_call):
    if "fork" not in multiprocessing.get_all_start_methods():
        pytest.skip("This operational process-death control requires POSIX fork")
    context = multiprocessing.get_context("fork")
    parent, child = context.Pipe()

    def execute_exposed():
        parent.close()
        _, solver, effects = exposed_backend(custody, monkeypatch)
        original_step = solver.step

        def stop_at_selected_call(*args, **kwargs):
            if len(effects) + 1 == stop_before_call:
                preparation = native.completed_preparation_checkpoint(custody.store, custody.definition)
                assert preparation.receipt is not None
                assert preparation.completion.operational_status is OperationalStatus.SUCCEEDED
                child.send({"checkpoint": preparation.definition.identity,
                    "completed_calls": len(effects), "exposed_backend_only": True})
                child.recv()  # Parent kills this process instead of allowing the pending fake call.
                raise AssertionError("Stopped fake call unexpectedly resumed")
            return original_step(*args, **kwargs)

        solver.step = stop_at_selected_call
        with storage.native_storage_scope():
            acquire(custody)

    process = context.Process(target=execute_exposed)
    process.start()
    child.close()
    try:
        assert parent.poll(30), "Exposed child never reached selected custody checkpoint"
        reached = parent.recv()
        assert reached["completed_calls"] == stop_before_call - 1 and reached["exposed_backend_only"] is True
        process.kill()
        process.join(10)
        assert not process.is_alive() and process.exitcode == -signal.SIGKILL
    finally:
        if process.is_alive():
            process.kill()
            process.join(10)
        parent.close()
    # Removal of the creating launch grants no new effect authority. Original
    # completed subwork receipts remain readable through the existing owner.
    custody.store.parent_contacts.retire_live_creator(custody.store.parent_contact)
    checkpoint = native.completed_preparation_checkpoint(custody.store, custody.definition)
    assert checkpoint.definition.identity == reached["checkpoint"]
    actual = checkpoint_records(custody, checkpoint)
    assert actual["protocol"] == custody.protocol
    assert actual["source-assignment"].configuration == custody.definition.configuration
    assert actual["layout"].observed_from_built_model
    assert actual["native.request.first"].ordinal == 1
    assert {row.output_id for row in checkpoint.definition.outputs} == set(actual)
    assert not {"actual-initial", "requested-initial", "initial-derivative", "actual-terminal", "terminal-derivative"} & set(actual)
    assert custody.store.inspect(custody.definition).state is NativeSubworkState.UNKNOWN_COMPLETION
    definitions = tuple(row for roster in custody.store.iter_rosters(custody.store.parent_contact)
        for row in custody.store.iter_roster_definitions(roster.parent_contact, roster.roster_id)
        if row.operation_id == "battery.segmented-native.segment")
    assert len(definitions) == stop_before_call
    states = tuple(custody.store.inspect(row).state for row in sorted(definitions, key=lambda row: row.subwork_id))
    assert states == (NativeSubworkState.COMPLETED,) * (stop_before_call - 1) + (NativeSubworkState.UNKNOWN_COMPLETION,)
    context_ids = {row.materialization.materialization_id for row in checkpoint.outputs}
    first = next(row for row in definitions if row.subwork_id.endswith(".segment.1"))
    assert context_ids.issubset(first.input_materialization_ids)
    if stop_before_call == 2:
        completed = custody.store.recover(first)
        request = actual["native.request.first"]
        assert first.configuration == request.identity
        full = stream.completed_record(custody.store, first, completed, "full-state", records.FullSegmentIndex)
        sources = custody.store.iter_completed_output(first, "raw-return", maximum_chunk_bytes=records.codec.CHUNK_BYTES)
        from empirical_lawhood.adapters.methods.battery_refined_inquiry.lossless_evidence_stream import bounded_lines, selected_temporary_files
        raw, decoded_sources, handles = records.decode_raw_segment(bounded_lines(sources), selected_temporary_files(tmp_path))
        try:
            view = records.DecodedFullSegment(full, raw, decoded_sources)
            assert view.layout == native._identity(actual["layout"], "layout_id")
            assert view.request == request.identity and len(view.blocks) == 1
            assert len(view.blocks[0].state_binary64) == 174 * 3
            assert len(view.blocks[0].derivative_binary64) == 174 * 3
        finally:
            for handle in handles:
                handle.close()
    # UNKNOWN parents and pending contacts cannot be replayed, even though
    # their independently completed context/earlier arrays are recoverable.
    with pytest.raises(NativeSubworkUncertainContact):
        acquire(custody)


@pytest.mark.parametrize("failed_output", ("layout", "source-assignment", "native.request.first"))
def test_interrupted_context_publication_never_calls_first_solver_or_invents_completion(custody, monkeypatch, failed_output):
    _, _, effects = exposed_backend(custody, monkeypatch)
    original = custody.store.publish_output

    def fail_selected_context(entry, name, *args, **kwargs):
        if entry.definition.operation_id == "battery.segmented-native.preparation" and name == failed_output:
            raise OSError("Declared exposed checkpoint publication refusal")
        return original(entry, name, *args, **kwargs)

    monkeypatch.setattr(custody.store, "publish_output", fail_selected_context)
    with pytest.raises(native._CustodyFailure, match="checkpoint custody failed"):
        acquire(custody)
    assert effects == []
    definition = native.build_preparation_checkpoint_definition(custody.definition)
    assert custody.store.inspect(definition).state is NativeSubworkState.UNKNOWN_COMPLETION
    with pytest.raises(NativeSubworkUncertainContact):
        native.completed_preparation_checkpoint(custody.store, custody.definition)
    with pytest.raises(NativeSubworkUncertainContact):
        acquire(custody)


def test_controlled_context_exposes_only_original_published_actual_solver_records(controlled_selected, controlled_config, monkeypatch):
    published = []
    original = SimpleNamespace(begin=lambda definition, inputs: SimpleNamespace(definition=definition), contact=lambda entry: None)
    monkeypatch.setattr(step.passive, "_publish", lambda progress, entry, name, record:
        published.append((name, record.canonical_bytes())) or SimpleNamespace(materialization=SimpleNamespace(size_bytes=len(record.canonical_bytes()))))
    progress = step._ControlledProgress(original, controlled_selected[2])
    entry = progress.begin(SimpleNamespace(operation_id="battery.segmented-native.forecast"))
    progress.contact(entry)
    with pytest.raises(ValueError, match="lacks its solver assignment"):
        progress.preparation_records()
    assignment = witness(controlled_selected[2], controlled_config)[2]
    progress.publish_extra("forecast-step-assignment", assignment)
    actual = progress.preparation_records()
    assert tuple((name, record.canonical_bytes()) for name, record in actual) == tuple(sorted(published))
    assert dict(actual)["forecast-step-assignment"] is assignment
    assert dict(actual)["forecast-step-policy"] is controlled_selected[2]


def test_checkpoint_definition_preserves_source_streams_inputs_and_rejects_partial_control(custody):
    original = custody.definition
    checkpoint = native.build_preparation_checkpoint_definition(original)
    for field in ("parent_contact", "configuration", "sources", "code_sources_sha256", "dependency_lock_sha256", "input_materialization_ids", "streams"):
        assert getattr(checkpoint, field) == getattr(original, field)
    assert {row.output_id for row in checkpoint.outputs} == {"protocol", "source-assignment", "layout", "native.request.first"}
    single = NativeSubworkOutput("forecast-step-policy", step.ForecastStepPolicy.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json")
    changed = replace(original, outputs=tuple(sorted((*original.outputs, single), key=lambda row: row.output_id)))
    with pytest.raises(ValueError, match="declared forecast context"):
        native.build_preparation_checkpoint_definition(changed)
    with pytest.raises(ValueError, match="declared forecast context"):
        native.build_preparation_checkpoint_definition(replace(original, operation_id="battery.unregistered.context"))


@pytest.mark.parametrize("role", ("forecast-step-policy", "forecast-step-assignment", "step-assignment"))
def test_uncontrolled_observation_checkpoint_rejects_forecast_control_roles(custody, role):
    from empirical_lawhood.adapters.methods.battery_refined_inquiry import development_restart_control as development
    from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_observation_native as observation

    selected = replace(custody.definition, operation_id="battery.segmented-observation.initial-window",
        outputs=observation.observation_outputs())
    checkpoint = native.build_preparation_checkpoint_definition(selected)
    assert {row.output_id for row in checkpoint.outputs} == {"protocol", "source-assignment", "layout", "native.request.first"}
    unexpected = next(row for row in development.outputs() if row.output_id == role) if role == "step-assignment" else NativeSubworkOutput(
        role, step.ForecastStepPolicy.SCHEMA if role == "forecast-step-policy" else step.ActualForecastStepAssignment.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, "application/json")
    injected = replace(selected, outputs=tuple(sorted((*selected.outputs, unexpected), key=lambda row: row.output_id)))
    with pytest.raises(ValueError, match="declared forecast context"):
        native.build_preparation_checkpoint_definition(injected)


def test_first_solver_request_cannot_substitute_completed_checkpoint_bytes(custody, monkeypatch):
    _, _, effects = exposed_backend(custody, monkeypatch)
    original = native._SegmentChain.enter

    def changed_first(chain, primitive):
        assert chain.preparation.receipt is not None
        return original(chain, dict(primitive, duration=primitive["duration"] / 2))

    monkeypatch.setattr(native._SegmentChain, "enter", changed_first)
    result = acquire(custody)
    assert effects == [] and result.trace.disposition == "TECHNICAL_FAILURE"
    assert "substitutes its completed checkpoint request" in result.trace.error_message
    assert native.completed_preparation_checkpoint(custody.store, custody.definition).receipt is not None


def test_existing_development_control_has_explicit_actual_checkpoint_roles(custody):
    from empirical_lawhood.adapters.methods.battery_refined_inquiry import development_restart_control as development
    selected = replace(custody.definition, operation_id="battery.development.restart-control", outputs=development.outputs())
    checkpoint = native.build_preparation_checkpoint_definition(selected)
    assert {row.output_id for row in checkpoint.outputs} == {
        "protocol", "source-assignment", "layout", "native.request.first", "forecast-step-policy", "step-assignment"}
    assert checkpoint.configuration == selected.configuration
    assert checkpoint.sources == selected.sources and checkpoint.input_materialization_ids == selected.input_materialization_ids
    assert not {"control", "result", "actual-initial", "initial-derivative"} & {row.output_id for row in checkpoint.outputs}
    incomplete = replace(selected, outputs=tuple(row for row in selected.outputs if row.output_id != "forecast-step-policy"))
    with pytest.raises(ValueError, match="declared forecast context"):
        native.build_preparation_checkpoint_definition(incomplete)
