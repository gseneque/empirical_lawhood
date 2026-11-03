# SPDX-License-Identifier: MPL-2.0
"""Exposed complete ordinary observation graph; no scientific acquisition."""

from dataclasses import replace
from hashlib import sha256
import io
import json
from types import SimpleNamespace as N

import pytest

from empirical_lawhood.adapters.methods.battery_observation_inquiry import contracts as ct, operation_bindings as ob, recursive_translation as rt
from empirical_lawhood.adapters.methods.battery_refined_inquiry import contracts as c, preparation_contracts as pc, preparation_science as ps
from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_native as base, segmented_observation_native as native, segmented_observation_contracts as oc
from empirical_lawhood.adapters.methods.battery_refined_inquiry.segmented_fidelity import FullStateControlProtocol
from empirical_lawhood.adapters.methods.battery_refined_inquiry.segmented_fidelity_stream import FullStateStreamAssessment
from empirical_lawhood.adapters.methods.battery_segmented_inquiry import evidence_stream as es
from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest
from empirical_lawhood.infrastructure.execution import LocalScheduler, ResourceAdmissionError
from empirical_lawhood.infrastructure.native_subwork_ipc import NativeSubworkPipeService, NativeSubworkRequest, PipeNativeSubworkProgress
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest, ExternalRootContract
from empirical_lawhood.runtime.capabilities import CapabilityRegistry
from empirical_lawhood.runtime.execution import DependencyReceiptBinding, WorkerInputBinding, WorkerInputKind, WorkerOutputPort
from empirical_lawhood.runtime.native_effects import NativeEffectContact
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
from tests.runtime_platform.test_native_subwork import _plane, _store
from tests.test_battery_durable_graph import stock as old_stock_fixture
from tests.test_battery_segmented_observation import observation as observation_fixture
from tests.test_battery_segmented_native import exposed_backend
from tests.test_battery_segmented_graph import Emitter


def make_stock(storage):
    old = old_stock_fixture.__wrapped__()
    observation = observation_fixture.__wrapped__()
    abi_payload, resource_payload = b'{"EXPOSED_ABI_GUARD_CONTROL":true}\n', b'{"EXPOSED_RESOURCE_CONTROL":true}\n'
    abi = ObjectIdentity("source.exposed-observation-abi", oc.RAW_SOURCE_SCHEMA, "1.0.0", sha256(abi_payload).hexdigest())
    source = ObjectIdentity("source.exposed-observation-resources", oc.RAW_SOURCE_SCHEMA, "1.0.0", sha256(resource_payload).hexdigest())
    resources = oc.ObservationResourceSnapshot("resources.exposed-observation", "2026-10-11T11:00:00+00:00",
        ct.identity(storage, "storage_root_id"), 1000000, 1000000, source)
    protocols = tuple(pc.PreparationProtocol("protocol.exposed-observation." + str(i), c.identity(config), c.identity(old.source),
        old.provenance.identity, config.preparation.parameter_source, "SPMe", config.numerical_view.electrode_points,
        config.numerical_view.particle_points, config.initial_temperature_k, ps.PREPARATION_SOURCE_MEMBERS)
        for i, config in enumerate(observation.configurations))
    declarations = tuple(oc.ObservationEntryDeclaration("entry.exposed-observation." + str(i), ct.identity(observation, "observation_id"),
        i, old.provenance, abi, resources) for i in range(3))
    control = FullStateControlProtocol("control.exposed-observation.full-state")
    draft = rt.observation_draft(observation, protocols, declarations, old.provenance, storage, control,
        parent=old.parent, selected_storage_contract=storage)
    configs = {operation.node_id: decode_canonical_bytes(operation.config_payload.encode(), ob.ObservationOperationConfig, maximum_bytes=None)
        for operation in draft.operations}
    return N(old=old, observation=observation, protocols=protocols, declarations=declarations, control=control, storage=storage,
        draft=draft, configs=configs, abi_payload=abi_payload, resource_payload=resource_payload)


@pytest.fixture(scope="module")
def stock():
    return make_stock(ExternalRootContract("storage.exposed-observation", "EXPOSED observation root", "/tmp/exposed-observation",
        "/tmp", "empirical-lawhood/development/exposed-root-contract", 0))


def compile_stock(stock, draft=None):
    registry = CapabilityRegistry("registry.exposed-observation", tuple(sorted(ob.operation_manifests(), key=lambda row: row.registry_id)))
    return compile_recursive_wave(draft=draft or stock.draft, registrations=ob.operation_registrations(), registry=registry,
        implementation_commit="1" * 40, output_codecs=ob.output_codecs())


def test_declarations_keep_canonical_input_types_separate_from_original_stream_codecs():
    from empirical_lawhood.runtime.artifacts import is_canonical_json_media_type
    from empirical_lawhood.runtime.recursive_storage_codecs import resolve_storage_codec

    for declaration in ob.operation_declarations():
        registration = declaration.registration()
        assert {record.SCHEMA for record in registration.input_record_types} == {
            port.payload_schema for port in registration.input_ports if is_canonical_json_media_type(port.media_type)}
        assert es.SegmentStreamChunk not in registration.input_record_types
        assert registration.storage_codecs == ob.OBSERVATION_STORAGE_CODECS
        assert dict(declaration.provider_factory().output_codecs) == ob.output_codecs()
        for port in registration.input_ports:
            if port.payload_schema == es.SegmentStreamChunk.SCHEMA:
                codec = resolve_storage_codec(registration.storage_codecs,
                    payload_schema=port.payload_schema, media_type=port.media_type)
                assert codec is not None and codec.profile is ArtifactProfile.JSONL_CHUNKS


def test_complete_three_native_three_assessor_two_pair_and_one_readout_graph(stock):
    compiled = compile_stock(stock)
    tasks = compiled.execution_plan.tasks
    assert len(tasks) == 9 and all(row.maximum_attempts == 1 for row in tasks)
    assert sum(".observe." in row.task_id for row in tasks) == sum(".assess." in row.task_id for row in tasks) == 3
    assert sum(".pair." in row.task_id for row in tasks) == 2
    slots = tuple(slot for config in stock.configs.values() if config.operation == "observe" for slot in ob.native_effect_slot_ids(config))
    assert len(slots) == len(set(slots)) == 3
    readout = next(row for row in tasks if row.task_id == ob.node_id("summarize"))
    assert len(readout.dependency_task_ids) == 5
    assert all(row.payload_schema != es.SegmentStreamChunk.SCHEMA for row in readout.scientific_inputs)
    assert stock.observation.original_entry_disposition.scientific_authority == "NONE"
    assert not stock.observation.full_forecast_completed
    for row in tasks:
        work = rt.scientific_work(stock.draft, row.task_id)
        assert work.scope == c.scope(stock.old.source)


@pytest.mark.parametrize("damage", ("missing-method", "pair-operand", "lost-stream", "history-role"))
def test_omitted_method_or_scientific_dependency_refuses(stock, damage):
    draft = stock.draft
    if damage == "missing-method":
        draft = replace(draft, selected_operation_ids=tuple(node for node in draft.selected_operation_ids if node != ob.node_id("observe", 2)))
    else:
        link = next(row for row in draft.links if row.consumer_input_id == ("left-window" if damage == "pair-operand" else "segments" if damage == "lost-stream" else "history"))
        changed = replace(link, producer_output_id="segments" if damage == "pair-operand" else "window") if damage != "history-role" else replace(link, scientific_role="SOURCE")
        draft = replace(draft, links=tuple(changed if row == link else row for row in draft.links))
    with pytest.raises(ValueError):
        compile_stock(stock, draft)


def test_selected_storage_and_entry_resource_join_are_explicit(stock):
    config = stock.configs[ob.node_id("summarize")]
    ob.require_selected_storage(config, stock.storage)
    with pytest.raises(ValueError, match="actually selected measured"):
        ob.require_selected_storage(config, replace(stock.storage, canonical_path="/tmp/foreign"))
    with pytest.raises(ValueError, match="root joins"):
        replace(config, storage=replace(stock.storage, storage_root_id="storage.foreign"))
    assert ob.primitive(config, 0) != ob.primitive(config, 1) != ob.primitive(config, 2)
    changed = replace(config.observation.configurations[0], config_id="config.changed-label")
    assert changed.native == config.observation.configurations[0].native


class Port:
    def __init__(self, artifact_id, record, kind, *, raw=None, media="application/json", schema=None):
        self.artifact_id, self.materialization_id, self.kind = artifact_id, "materialization." + artifact_id, kind
        self.raw = record.canonical_bytes() if raw is None else raw
        self.payload_schema, self.media_type = record.SCHEMA if schema is None else schema, media
        self.size_bytes, self.reader, self.closed = len(self.raw), io.BytesIO(self.raw), False
        self.visibility_ceiling, self.outcome_access = VisibilityCeiling.DEVELOPMENT_ONLY, OutcomeAccess.DEVELOPMENT_VISIBLE

    def read(self, size=-1):
        return self.reader.read(size)

    def close(self):
        self.closed = True
        self.reader.close()


def context_for(stock, config, outputs=None):
    node, run_id = ob.node_id(config.operation, config.index), "run.exposed-observation"
    external = rt.external_values(config)
    external[config.history_artifact_id] = stock.old.history
    sources, ports, by_name = rt.input_sources(config), [], {}
    for name, (kind, origin) in sources.items():
        dependency = kind == "DEPENDENCY"
        artifact = "artifact." + run_id + "." + origin if dependency else origin
        if dependency:
            raw = outputs[origin]
            record = next(record for selected_name, record in ob.operation_inputs(config.operation) if selected_name == name)
        elif name in {"abi-import-report", "resource-source"}:
            raw, record = stock.abi_payload if name == "abi-import-report" else stock.resource_payload, ob.RawSource
        else:
            record, raw = external[origin], None
        port = Port(artifact, record, WorkerInputKind.DEPENDENCY if dependency else WorkerInputKind.EXTERNAL,
            raw=raw, media=ob.media_for(name))
        ports.append(port)
        by_name[name] = port
    config_port = Port("config.external", config, WorkerInputKind.EXTERNAL)
    ports.append(config_port)
    producers = {origin.rsplit(".", 1)[0] for kind, origin in sources.values() if kind == "DEPENDENCY"}
    receipts = tuple(DependencyReceiptBinding("receipt." + producer, producer,
        tuple(sorted(by_name[name].materialization_id for name, (kind, origin) in sources.items()
            if kind == "DEPENDENCY" and origin.rsplit(".", 1)[0] == producer))) for producer in sorted(producers))
    runner = ob.ObservationRunner(config.operation)
    context = N(task_id=node, run_id=run_id, input_ports=tuple(ports), permissions=runner.manifest.permissions,
        resource_budget=ob.BUDGET, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE, dependency_receipts=receipts,
        input_materialization_ids=tuple(sorted(port.materialization_id for port in ports)),
        config=N(artifact_id=config_port.artifact_id, content_sha256=config.fingerprint(), config_id=config.config_id),
        output_ports=tuple(WorkerOutputPort(node + "." + name, record.SCHEMA,
            ArtifactProfile.JSONL_CHUNKS if name == "segments" else ArtifactProfile.CANONICAL_JSON, ob.media_for(name))
            for name, record in ob.operation_outputs(config.operation)))
    return runner, context


def native_progress(plane, context, provenance, tmp_path):
    manifests, bindings = [], []
    for port in context.input_ports:
        result = plane.write(ArtifactWriteRequest(port.artifact_id, "inputs/" + context.task_id + "/" + port.artifact_id + ".json", port.payload_schema,
            ArtifactProfile.RAW_SOURCE_BYTES if port.payload_schema == oc.RAW_SOURCE_SCHEMA else ArtifactProfile.CANONICAL_JSON,
            port.media_type, "exposed.observation.inputs", "inputs", port.raw, VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE))
        manifest = decode_artifact_manifest(plane.root.resolve(result.materialization.relative_path + ".manifest.json", for_write=False).read_bytes())
        port.materialization_id = manifest.materialization.materialization_id
        manifests.append(manifest)
        bindings.append(WorkerInputBinding(port.artifact_id, port.materialization_id, port.payload_schema, port.media_type,
            port.size_bytes, port.visibility_ceiling, port.outcome_access, port.kind))
    context.input_materialization_ids = tuple(sorted(port.materialization_id for port in context.input_ports))
    parent = NativeEffectContact(context.run_id, context.task_id, context.run_id + "." + context.task_id + ".attempt-001",
        ObjectIdentity("plan.exposed-observation", "empirical-lawhood/runtime/development-execution-plan", "1.0.0", "1" * 64),
        ObjectIdentity(context.task_id, "empirical-lawhood/runtime/execution-task", "1.0.0", "2" * 64),
        provenance.observed_git_head, context.input_materialization_ids, ())
    store = _store(plane, parent, tuple(sorted(manifests, key=lambda row: row.materialization.materialization_id)))
    store.parent_contacts.begin(parent)
    service_context = N(run_id=parent.run_id, task_id=parent.task_id, attempt_id=parent.attempt_id,
        input_materialization_ids=parent.input_materialization_ids, dependency_receipt_ids=(), input_bindings=tuple(bindings), resource_budget=context.resource_budget)
    service = NativeSubworkPipeService(store, service_context, tmp_path)
    class Connection:
        def send(self, message):
            if type(message) is NativeSubworkRequest:
                service.handle(message, self)
            else:
                self.reply = message

        def recv(self):
            return self.reply
    return store, service, PipeNativeSubworkProgress(Connection())


def test_original_native_three_windows_stream_to_separate_pure_assessment_and_complete_readout(tmp_path, monkeypatch):
    plane = _plane(tmp_path / "episode")
    planes = (plane, plane, plane)
    stock = make_stock(planes[0].root.contract)
    outputs, windows, effects = {}, [], []
    # These three real custody stores use exposed fake engine/source guards.
    # They are software controls and create no actual PyBaMM qualification.
    monkeypatch.setattr(native, "_validate_entry_sources", lambda *_: None)
    monkeypatch.setattr(native, "_validate_selected_source_inputs", lambda *_: None)
    for i, plane in enumerate(planes):
        config = stock.configs[ob.node_id("observe", i)]
        runner, context = context_for(stock, config)
        store, service, progress = native_progress(plane, context, stock.old.provenance, tmp_path)
        fake = N(config=stock.observation.configurations[i], protocol=stock.protocols[i], store=store)
        _, solver, calls = exposed_backend(fake, monkeypatch)
        definition = native.build_observation_definition(config.observation, config.index, config.protocols[config.index],
            config.provenance, progress, config.declarations[config.index], context.input_materialization_ids)
        original_step, checked_receipts = solver.step, []

        def checked_step(previous, built, horizon, *, inputs=None, save=True):
            checkpoint = base.completed_preparation_checkpoint(store, definition)
            assert checkpoint is not None and checkpoint.receipt is not None
            assert checkpoint.definition.configuration == definition.configuration
            assert checkpoint.definition.sources == definition.sources
            assert checkpoint.definition.input_materialization_ids == definition.input_materialization_ids
            segment = next(row for roster in store.iter_rosters(store.parent_contact)
                for row in store.iter_roster_definitions(roster.parent_contact, roster.roster_id)
                if row.subwork_id == definition.subwork_id + ".segment." + str(len(calls) + 1))
            assert {row.materialization.materialization_id for row in checkpoint.outputs}.issubset(segment.input_materialization_ids)
            if not calls:
                request = es.completed_record(store, checkpoint.definition, checkpoint, "native.request.first", base.SegmentRequest)
                assert segment.configuration == request.identity
                primitive = json.loads(request.primitive_json)
                assert primitive["inputs"] == base.passive._freeze(inputs)
                assert primitive["duration"] == base.passive._freeze(horizon)
                assert primitive["solver"] == base.passive._freeze(solver.to_config())
            checked_receipts.append(checkpoint.receipt.fingerprint())
            return original_step(previous, built, horizon, inputs=inputs, save=save)

        monkeypatch.setattr(solver, "step", checked_step)
        monkeypatch.setattr(native, "build_runtime", base.build_runtime)
        emitter = Emitter()
        try:
            checks = runner.execute_streaming_with_native_subwork(context, progress, emitter)
        finally:
            service.close()
        assert all(row.passed for row in checks) and all(port.closed for port in context.input_ports)
        assert len(checked_receipts) == len(calls) and len(set(checked_receipts)) == 1
        assert sum(row.subwork_id == definition.subwork_id + ".preparation"
            for roster in store.iter_rosters(store.parent_contact)
            for row in store.iter_roster_definitions(roster.parent_contact, roster.roster_id)) == 1
        outputs.update((key, bytes(value)) for key, value in emitter.outputs.items())
        window = decode_canonical_bytes(outputs[context.task_id + ".window"], ct.ObservedWindow, maximum_bytes=None)
        assert window.completion.cost.retained_bytes is not None and window.completion.peak_rss_bytes > 0
        windows.append(window)
        effects.append(len(calls))
        runner, context = context_for(stock, stock.configs[ob.node_id("assess", i)], outputs)
        result = runner.execute(context)
        outputs.update((row.output_id, row.payload) for row in result.outputs)
        assert all(port.closed for port in context.input_ports)
        assessment = decode_canonical_bytes(result.outputs[0].payload, ct.ObservationMethodAssessment, maximum_bytes=None)
        assert len(assessment.segments) == len(calls)
        with pytest.raises(ValueError):
            replace(assessment, full_forecast_completed=True)
        if i == 0:
            stream_id = ob.node_id("observe", i) + ".segments"
            raw = outputs[stream_id]
            with io.BytesIO(raw) as source:
                header, first = es.read_frames(N(read=source.read, size_bytes=len(raw)))
            publisher = first.request_receipt
            checkpoint = base.build_preparation_checkpoint_definition(definition)
            foreign_lineage = tuple(replace(logical, lineage_parents=tuple(
                replace(parent, identity=replace(parent.identity, object_fingerprint="d" * 64))
                    if parent.identity == checkpoint.identity else parent for parent in logical.lineage_parents))
                for logical in publisher.output_logical_artifacts)
            layout_id = next(row.logical_artifact_id for row in publisher.output_logical_artifacts
                if row.payload_schema == pc.ProcessedInitialStateLayout.SCHEMA)
            damaged_publishers = (
                (replace(publisher, output_logical_artifacts=foreign_lineage), "completed preparation publisher/context"),
                (replace(publisher, operational_status=OperationalStatus.FAILED, reason_codes=("exposed-failed-checkpoint",)),
                    "completed preparation publisher/context"),
                (replace(publisher, implementation_commit="e" * 40), "completed preparation publisher/context"),
                (replace(publisher, input_materialization_ids=tuple(row for row in publisher.input_materialization_ids
                    if row != checkpoint.input_materialization_ids[0])), "completed preparation publisher/context"),
                (replace(publisher,
                    output_logical_artifacts=tuple(row for row in publisher.output_logical_artifacts if row.logical_artifact_id != layout_id),
                    output_materializations=tuple(row for row in publisher.output_materializations if row.logical_artifact_id != layout_id)),
                    "assessed segment operand differs"),
            )
            for damaged_publisher, expected in damaged_publishers:
                emitter = Emitter()
                sequence = es.emit_frame(emitter, stream_id, header, 0, 0)
                es.emit_frame(emitter, stream_id, replace(first, request_receipt=damaged_publisher), 1, sequence)
                changed_outputs = dict(outputs, **{stream_id: bytes(emitter.outputs[stream_id])})
                runner, changed_context = context_for(stock, stock.configs[ob.node_id("assess", i)], changed_outputs)
                with pytest.raises(ValueError, match=expected):
                    runner.execute(changed_context)
                assert all(port.closed for port in changed_context.input_ports)
    assert effects == [1, 3, 3]
    for i in range(2):
        runner, context = context_for(stock, stock.configs[ob.node_id("pair", i)], outputs)
        result = runner.execute(context)
        outputs.update((row.output_id, row.payload) for row in result.outputs)
        paired = decode_canonical_bytes(result.outputs[0].payload, FullStateStreamAssessment, maximum_bytes=None)
        assert paired.declared_segment_counts == (effects[i], effects[i + 1])
        assert paired.disposition is not A.SATISFIED
    runner, context = context_for(stock, stock.configs[ob.node_id("summarize")], outputs)
    result = runner.execute(context)
    readout = decode_canonical_bytes(result.outputs[0].payload, ct.ObservationReadout, maximum_bytes=None)
    assert len(readout.methods) == 3 and len(readout.pairs) == 2 and readout.selected_model is None
    assert not readout.full_forecast_completed and not readout.physical_qualification and readout.scientific_authority == "NONE"
    for damage in ({"methods": readout.methods[:2]}, {"pairs": readout.pairs[:1]}, {"selected_model": "oregan-spme"}, {"disposition": A.SATISFIED}):
        with pytest.raises(ValueError):
            replace(readout, **damage)
    with pytest.raises(ValueError, match="unobserved stopping clock"):
        replace(windows[0], result=replace(windows[0].result, actual_last_model_clock_s=windows[0].result.actual_last_model_clock_s + 1))


def test_zero_call_observation_stays_unevaluable_without_a_preparation_checkpoint(tmp_path, monkeypatch):
    plane = _plane(tmp_path / "zero-call")
    stock = make_stock(plane.root.contract)
    config = stock.configs[ob.node_id("observe", 0)]
    runner, context = context_for(stock, config)
    store, service, progress = native_progress(plane, context, stock.old.provenance, tmp_path)
    fake = N(config=stock.observation.configurations[0], protocol=stock.protocols[0], store=store)
    _, _, calls = exposed_backend(fake, monkeypatch)
    monkeypatch.setattr(native, "_validate_entry_sources", lambda *_: None)
    monkeypatch.setattr(native, "_validate_selected_source_inputs", lambda *_: None)

    def unavailable_runtime(*args):
        raise RuntimeError("EXPOSED preparation failure before any solver entry")

    monkeypatch.setattr(native, "build_runtime", unavailable_runtime)
    definition = native.build_observation_definition(config.observation, 0, stock.protocols[0], config.provenance,
        progress, stock.declarations[0], context.input_materialization_ids)
    emitter = Emitter()
    try:
        runner.execute_streaming_with_native_subwork(context, progress, emitter)
    finally:
        service.close()
    assert calls == [] and base.completed_preparation_checkpoint(store, definition) is None
    outputs = {key: bytes(value) for key, value in emitter.outputs.items()}
    window = decode_canonical_bytes(outputs[context.task_id + ".window"], ct.ObservedWindow, maximum_bytes=None)
    assert window.result.observed_native_calls == 0 and window.result.disposition == "TECHNICAL_FAILURE"
    runner, context = context_for(stock, stock.configs[ob.node_id("assess", 0)], outputs)
    assessment = decode_canonical_bytes(runner.execute(context).outputs[0].payload, ct.ObservationMethodAssessment, maximum_bytes=None)
    assert assessment.segments == () and assessment.disposition is A.UNEVALUABLE
    assert all(port.closed for port in context.input_ports)


@pytest.mark.parametrize("adverse", (A.REFUSED, A.UNSUPPORTED, A.NOT_ATTEMPTED))
def test_other_adverse_scientific_dispositions_cannot_fall_through_to_satisfaction(adverse):
    assert ct.combined_disposition((A.SATISFIED, adverse)) is A.UNEVALUABLE
    assert ct.combined_disposition((A.SATISFIED, adverse, A.FALSIFIED)) is A.FALSIFIED


def test_worker_foreign_source_refuses_before_native_port(stock):
    runner, context = context_for(stock, stock.configs[ob.node_id("observe", 0)])
    source = next(port for port in context.input_ports if port.artifact_id == stock.old.source.source_id)
    document = json.loads(source.raw)
    document["value"]["source_id"] = "source.foreign"
    source.raw = json.dumps(document).encode()
    source.reader, source.size_bytes = io.BytesIO(source.raw), len(source.raw)
    with pytest.raises(ValueError):
        runner.execute_streaming_with_native_subwork(context, N(), Emitter())
    assert all(port.closed for port in context.input_ports)


def test_four_unregistered_descriptors_are_cold():
    import subprocess
    import sys
    result = subprocess.run((sys.executable, "-c", "import sys; from empirical_lawhood.adapters.methods.battery_observation_inquiry.executable_binding import EXECUTABLE_BINDING_FACTORIES; assert len(EXECUTABLE_BINDING_FACTORIES)==4; assert 'pybamm' not in sys.modules; assert 'numpy' not in sys.modules; assert 'flint' not in sys.modules"), capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr


def test_outer_scheduler_keeps_pure_observation_consumers_out_of_native_custody():
    scheduler = object.__new__(LocalScheduler)
    for operation in ("assess", "pair", "summarize"):
        assert scheduler._native_subwork_progress(ob.ObservationRunner(operation), None, ()) is None
    with pytest.raises(ResourceAdmissionError, match="no selected native-effect parent"):
        scheduler._native_subwork_progress(ob.ObservationRunner("observe"), None, ())
