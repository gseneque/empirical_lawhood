# SPDX-License-Identifier: MPL-2.0
"""Exposed ordinary graph and exact segment transport; no scientific entry."""

from dataclasses import dataclass, replace
from decimal import Decimal as D
import io
import json
from types import SimpleNamespace as N

import pytest

from empirical_lawhood.adapters.methods.battery_segmented_inquiry import evidence_stream as es
from empirical_lawhood.adapters.methods.battery_segmented_inquiry import operation_bindings as ob, recursive_translation as rt
from empirical_lawhood.adapters.methods.battery_segmented_inquiry.runner import _assess, _original_evidence
from empirical_lawhood.adapters.methods.battery_refined_inquiry import contracts as c, preparation_contracts as pc, preparation_science as ps
from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_contracts as sc, segmented_evidence as se, segmented_roster as sr
from empirical_lawhood.adapters.methods.battery_refined_inquiry.source_derived_preparation import supply_source_roots, assess_source_roots
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.kernel.serialization import CanonicalRecord, canonical_json_bytes
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.capabilities import CapabilityRegistry
from empirical_lawhood.runtime.execution import DependencyReceiptBinding, WorkerInputKind, WorkerOutputPort
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
from empirical_lawhood.runtime.native_effects import NativeEffectContact
from empirical_lawhood.infrastructure.execution import LocalScheduler, ResourceAdmissionError, _PipeOutputEmitter
from tests.test_battery_durable_graph import stock as retained_stock
from tests.test_battery_refined_inquiry_binding import Port
from tests.test_battery_segmented_native import custody as native_custody, selected as native_selected, exposed_backend, acquire

custody = native_custody
selected = native_selected


@pytest.fixture(scope="module")
def stock():
    old = retained_stock.__wrapped__()
    method = sc.SegmentedMethodProtocol("method.exposed.graph.60s", D(60))
    supplies = {}
    for name in ("Chen2020", "ORegan2022"):
        preparation = supply_source_roots(c.identity(old.source), name)
        supplies[name] = (preparation, assess_source_roots(preparation))
    roster = sr.freeze_segmented_roster(old.roster, old.uncertain, method, supplies)
    representatives = tuple(i for i in range(54) if ob.representative_index(roster, i) == i)
    protocols = tuple(pc.PreparationProtocol("protocol.exposed.segmented." + native.config_id, c.identity(native), c.identity(old.source), old.provenance.identity,
        native.preparation.parameter_source, "DFN" if "dfn" in native.model_view else "SPMe",
        native.numerical_view.electrode_points, native.numerical_view.particle_points, native.initial_temperature_k,
        ps.PREPARATION_SOURCE_MEMBERS) for native in (roster.configurations[i] for i in representatives))
    draft = rt.qualification_draft(roster, old.uncertain, old.provenance, protocols, parent=old.parent)
    configs = {operation.node_id: decode_canonical_bytes(operation.config_payload.encode(), ob.SegmentedOperationConfig, maximum_bytes=None)
        for operation in draft.operations}
    return N(source=old.source, policy=old.policy, history=old.history, uncertain=old.uncertain, provenance=old.provenance,
        parent=old.parent, roster=roster, protocols=protocols, draft=draft, configs=configs)


def compile_stock(stock, draft=None):
    registry = CapabilityRegistry("registry.exposed-segmented", tuple(sorted(ob.operation_manifests(), key=lambda row: row.registry_id)))
    return compile_recursive_wave(draft=draft or stock.draft, registrations=ob.operation_registrations(), registry=registry,
        implementation_commit="1" * 40, output_codecs=ob.output_codecs())


def test_graph_keeps_complete54_36_and_distinct48_without_aggregate_arrays(stock):
    compiled = compile_stock(stock)
    tasks = {task.task_id: task for task in compiled.execution_plan.tasks}
    assert len(tasks) == 140
    assert sum(".forecast." in node for node in tasks) == sum(".assess." in node for node in tasks) == 48
    assert sum(".reuse." in node for node in tasks) == 6 and sum(".compare." in node for node in tasks) == 36
    assert all(task.maximum_attempts == 1 for task in tasks.values())
    slots = tuple(slot for config in stock.configs.values() if config.operation == "forecast" for slot in ob.native_effect_slot_ids(config))
    assert len(slots) == len(set(slots)) == 48
    aggregate = tasks[ob.node_id("qualify")]
    assert len(aggregate.dependency_task_ids) == 90
    assert not any(value.payload_schema in {sc.SegmentedTrace.SCHEMA, es.SegmentStreamChunk.SCHEMA, se.SegmentedNativeEvidence.SCHEMA}
        for value in aggregate.scientific_inputs)
    producer = tasks[ob.node_id("forecast", 0)]
    assert tuple((output.payload_schema, output.profile) for output in producer.outputs) == (
        (se.SegmentedNativeEvidence.SCHEMA, ArtifactProfile.CANONICAL_JSON), (es.SegmentStreamChunk.SCHEMA, ArtifactProfile.JSONL_CHUNKS))


def test_outer_scheduler_keeps_pure_segmented_consumers_out_of_native_custody():
    scheduler = object.__new__(LocalScheduler)
    for operation in ("validate", "assess", "reuse", "compare", "qualify"):
        assert scheduler._native_subwork_progress(ob.SegmentedRunner(operation), None, ()) is None
    with pytest.raises(ResourceAdmissionError, match="no selected native-effect parent"):
        scheduler._native_subwork_progress(ob.SegmentedRunner("forecast"), None, ())


def test_large_canonical_report_survives_actual_process_chunk_contract_exactly():
    @dataclass(frozen=True)
    class ExposedReport(CanonicalRecord):
        SCHEMA = "empirical-lawhood/test/large-canonical-report"
        retained_payload: str

    report = ExposedReport("x" * (2 * 1024 * 1024 + 19))
    chunks = []
    emitter = _PipeOutputEmitter(N(send=chunks.append),
        N(output_ports=(N(output_id="report"),), resource_budget=N(output_bytes=None)))
    with pytest.raises(ResourceAdmissionError, match="chunk exceeds its byte limit"):
        emitter.write("report", report.canonical_bytes())
    assert not chunks
    es.emit_record(emitter, "report", report)
    assert b"".join(row.payload for row in chunks) == report.canonical_bytes()
    assert all(row.output_id == "report" and len(row.payload) <= es.CHUNK_BYTES for row in chunks)
    assert json.loads(b"".join(row.payload for row in chunks))["schema"] == ExposedReport.SCHEMA


@pytest.mark.parametrize("damage", ("missing-forecast", "changed-pair", "history-role", "lost-stream"))
def test_incomplete_graph_or_wrong_operand_join_refuses(stock, damage):
    draft = stock.draft
    if damage == "missing-forecast":
        node = next(row.node_id for row in draft.operations if ".forecast." in row.node_id)
        draft = replace(draft, selected_operation_ids=tuple(value for value in draft.selected_operation_ids if value != node))
    else:
        if damage == "changed-pair":
            link = next(row for row in draft.links if row.consumer_node_id == ob.node_id("compare", 0) and row.consumer_input_id == "left-evidence")
            altered = replace(link, producer_output_id="segments")
        elif damage == "lost-stream":
            link = next(row for row in draft.links if row.consumer_input_id == "segments")
            altered = replace(link, producer_output_id="evidence")
        else:
            link = next(row for row in draft.links if row.consumer_input_id == "history")
            altered = replace(link, scientific_role="SOURCE")
        draft = replace(draft, links=tuple(altered if row == link else row for row in draft.links))
    with pytest.raises(ValueError):
        compile_stock(stock, draft)


def test_primitive_uses_changed_actual_values_not_new_labels(stock):
    native = stock.roster.configurations[0]
    same = replace(native, config_id="config.exposed.changed-label", method=replace(native.method, method_id="method.changed-label"))
    assert ob.forecast_primitive(same) == ob.forecast_primitive(native)
    shorter = replace(native, method=sc.SegmentedMethodProtocol("method.exposed.30s", D(30)))
    assert ob.forecast_primitive(shorter) != ob.forecast_primitive(native)
    disposition = sr.method_dispositions(stock.roster, stock.uncertain)
    assert sum(row.original_entry.matching_uncertain_forecast_ids != () for row in disposition) == 12
    assert sum(row.original_entry.matching_uncertain_initializer_ids != () for row in disposition) == 20
    assert all(row.scientific_authority == "NONE" and row.original_entry.scientific_authority == "NONE" for row in disposition)


class Emitter:
    def __init__(self):
        self.outputs = {}

    def write(self, output_id, chunk):
        self.outputs.setdefault(output_id, bytearray()).extend(chunk)


class StreamPort:
    def __init__(self, payload, maximum=13):
        self.reader, self.size_bytes, self.maximum = io.BytesIO(payload), len(payload), maximum

    def read(self, size=-1):
        assert size > 0
        return self.reader.read(min(size, self.maximum))


def transport(custody, result):
    emitter = Emitter()
    header = es.SegmentStreamHeader(c.identity(result.trace), pc.identity(result.protocol, result.protocol.protocol_id), len(result.trace.segments))
    sequence = es.emit_frame(emitter, "segments", header, 0, 0)
    frames = []
    for frame in es.relay_segments(custody.store, custody.definition, result.inspection, result.trace, result.protocol):
        sequence = es.emit_frame(emitter, "segments", frame, frame.segment_index, sequence)
        frames.append(frame)
    return bytes(emitter.outputs["segments"]), tuple(frames)


def test_actual_original_full_raw_stream_recovers_without_native_replay(custody, monkeypatch):
    _, _, effects = exposed_backend(custody, monkeypatch)
    result = acquire(custody)
    payload, frames = transport(custody, result)
    decoded = tuple(es.read_frames(StreamPort(payload)))
    assert decoded[1:] == frames and len(frames) == len(result.trace.segments) == len(effects) == 3
    assert max(map(len, payload.splitlines())) < 1024 * 1024
    assert all(frame.definition.identity == summary.native_definition for frame, summary in zip(frames, result.trace.segments, strict=True))
    evidence = _original_evidence(custody.store, custody.definition, result.inspection, custody.config)
    summary = _assess(custody.config, evidence, StreamPort(payload, 271))
    assert len(summary.segment_assessments) == 3
    assert sum(check.full_state_components for check in summary.segment_assessments) == 174 * 3 * 3
    # Real original state/custody survives; these exposed receiver doubles are
    # deliberately not a scientifically qualified battery trajectory.
    assert summary.disposition is not A.SATISFIED
    recovered = acquire(custody)
    assert recovered.recovered and len(effects) == 3
    again = _original_evidence(custody.store, custody.definition, recovered.inspection, custody.config)
    assert again == evidence
    assert transport(custody, replace(recovered, trace=again.trace))[0] == payload and len(effects) == 3


def test_original_receipt_refuses_optional_output_omission_and_substitution(custody, monkeypatch):
    exposed_backend(custody, monkeypatch)
    result = acquire(custody)
    _, frames = transport(custody, result)
    frame = frames[0]
    fields = ("raw_return", "full_state", "requested_initial", "actual_initial", "initial_derivative",
        "actual_terminal", "terminal_derivative")
    assert all(getattr(frame, name) is not None for name in fields)
    for name in fields:
        with pytest.raises(ValueError, match="actual receipt census"):
            replace(frame, **{name: None})
    with pytest.raises(ValueError, match="actual receipt census"):
        replace(frame, requested_initial=frame.actual_terminal)
    with pytest.raises(ValueError, match="actual receipt census"):
        replace(frame, full_state=replace(frame.full_state, segment_id=frame.full_state.segment_id + ".substituted"))


@pytest.mark.parametrize("damage", ("truncate", "reorder", "payload", "wrong-header"))
def test_stream_omission_substitution_and_order_refuse(custody, monkeypatch, damage):
    exposed_backend(custody, monkeypatch, malformed=True)
    result = acquire(custody)
    payload, _ = transport(custody, result)
    lines = payload.splitlines(keepends=True)
    if damage == "truncate":
        payload = payload[:-2]
    elif damage == "reorder":
        payload = b"".join((*lines[1:], lines[0]))
    else:
        row = json.loads(lines[0])
        if damage == "payload":
            row["value"]["payload_hex"] = "00" + row["value"]["payload_hex"][2:]
        else:
            row["value"]["frame_schema"] = es.SegmentEvidenceFrame.SCHEMA
        payload = canonical_json_bytes(row) + b"".join(lines[1:])
    with pytest.raises((ValueError, json.JSONDecodeError)):
        tuple(es.read_frames(StreamPort(payload)))


def test_malformed_actual_return_stream_preserves_all_raw_and_unevaluable(custody, monkeypatch):
    exposed_backend(custody, monkeypatch, malformed=True)
    result = acquire(custody)
    payload, frames = transport(custody, result)
    evidence = _original_evidence(custody.store, custody.definition, result.inspection, custody.config)
    assert len(frames) == 1 and frames[0].raw_return.state_blocks[0].shape == (173, 3) and frames[0].full_state is None
    summary = _assess(custody.config, evidence, StreamPort(payload))
    assert summary.disposition is A.UNEVALUABLE
    assert summary.segment_assessments[0].retained_raw_state_elements == 173 * 3
    with pytest.raises(ValueError, match="actual receipt census"):
        replace(frames[0], raw_return=None)
    with pytest.raises(ValueError, match="input/returned-output custody"):
        replace(frames[0], definition=replace(frames[0].definition, input_materialization_ids=custody.definition.input_materialization_ids))


def test_zero_segment_known_failure_has_header_and_explicit_unavailable_preparation(custody, monkeypatch):
    from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_native as native
    _, _, effects = exposed_backend(custody, monkeypatch)
    monkeypatch.setattr(native, "build_runtime", lambda *_: (_ for _ in ()).throw(RuntimeError("exposed build failure")))
    result = acquire(custody)
    assert result.trace.disposition == "TECHNICAL_FAILURE" and not result.trace.segments and not effects
    payload, frames = transport(custody, result)
    assert not frames and len(tuple(es.read_frames(StreamPort(payload)))) == 1
    evidence = _original_evidence(custody.store, custody.definition, result.inspection, custody.config)
    summary = _assess(custody.config, evidence, StreamPort(payload))
    assert summary.preparation.disposition is summary.disposition is A.UNEVALUABLE
    assert summary.preparation.missing_output_ids == ("actual-initial", "layout", "requested-initial", "source-assignment")
    assert summary.charging_segment_calls == 0 and summary.native_contacts == 1


def context_for(stock, config, *, changed_protocol=False):
    node, run_id = ob.node_id(config.operation, config.index), "run.exposed-segmented"
    values = {"source": stock.source, "policy": stock.policy, "selection": stock.policy.selection, "history": stock.history,
        "roster": stock.roster, "uncertain-work": stock.uncertain, "producing-provenance": stock.provenance,
        "method": config.method}
    for label, pair in zip(("chen", "oregan"), config.supplies, strict=True):
        values["preparation-" + label], values["source-assessment-" + label] = pair
    if config.operation == "forecast":
        native = stock.roster.configurations[config.index]
        protocol = next(row for row in stock.protocols if row.configuration == c.identity(native))
        values.update({"native-config": native, "selected-protocol": replace(protocol, initial_temperature_k=protocol.initial_temperature_k + 1) if changed_protocol else protocol,
            "admission": ob.SourcePolicyAdmission("admission.battery-refined-inquiry.source-policy", c.identity(stock.source), c.identity(stock.policy),
                ObjectIdentity.from_record("selection." + stock.policy.policy_id, stock.policy.selection), c.identity(stock.history)),
            "entry": sr.method_dispositions(stock.roster, stock.uncertain)[config.index]})
    ports = []
    sources = rt.input_sources(config)
    for name, (kind, origin) in sources.items():
        dependency = kind == "DEPENDENCY"
        port = Port("artifact." + run_id + "." + origin if dependency else origin, values[name],
            WorkerInputKind.DEPENDENCY if dependency else WorkerInputKind.EXTERNAL)
        ports.append(port)
    config_port = Port("config.external", config, WorkerInputKind.EXTERNAL)
    ports.append(config_port)
    producers = {origin.rsplit(".", 1)[0] for kind, origin in sources.values() if kind == "DEPENDENCY"}
    receipts = tuple(DependencyReceiptBinding("receipt." + producer, producer,
        tuple(sorted(port.materialization_id for name, port in zip(sources, ports, strict=False)
            if sources[name][0] == "DEPENDENCY" and sources[name][1].rsplit(".", 1)[0] == producer))) for producer in sorted(producers))
    runner = ob.SegmentedRunner(config.operation)
    outputs = tuple(WorkerOutputPort(node + "." + name, record.SCHEMA,
        ArtifactProfile.JSONL_CHUNKS if name == "segments" else ArtifactProfile.CANONICAL_JSON, ob.media_for(name)) for name, record in ob.operation_outputs(config.operation))
    return runner, N(task_id=node, run_id=run_id, input_ports=tuple(ports), output_ports=outputs,
        permissions=runner.manifest.permissions, resource_budget=ob.BUDGET, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
        dependency_receipts=receipts, config=N(artifact_id=config_port.artifact_id, content_sha256=config.fingerprint(), config_id=config.config_id))


def test_changed_prospective_protocol_refuses_before_native_progress(stock):
    config = stock.configs[ob.node_id("forecast", 0)]
    runner, context = context_for(stock, config, changed_protocol=True)
    context.attempt_id = context.run_id + "." + context.task_id + ".attempt-001"
    context.input_materialization_ids = tuple(sorted(port.materialization_id for port in context.input_ports))
    context.dependency_receipt_ids = tuple(sorted(row.receipt_id for row in context.dependency_receipts))
    parent = NativeEffectContact(context.run_id, context.task_id, context.attempt_id,
        ObjectIdentity("plan.exposed", "empirical-lawhood/runtime/development-execution-plan", "1.0.0", "1" * 64),
        ObjectIdentity(context.task_id, "empirical-lawhood/runtime/execution-task", "1.0.0", "2" * 64),
        stock.provenance.observed_git_head, context.input_materialization_ids, context.dependency_receipt_ids)
    try:
        with pytest.raises(ValueError, match="prospective gate"):
            runner.project_forecast_scope(context, parent)
    finally:
        for port in context.input_ports:
            port.close()
    assert all(port.closed for port in context.input_ports)


def test_validate_returns_all_actual_old_holds_without_entry_authority(stock):
    runner, context = context_for(stock, stock.configs[ob.node_id("validate")])
    result = runner.execute(context)
    assert len(result.outputs) == 55 and all(port.closed for port in context.input_ports)
    rows = tuple(decode_canonical_bytes(row.payload, sr.ProspectiveMethodDisposition, maximum_bytes=None) for row in result.outputs[1:])
    assert sum(bool(row.original_entry.matching_uncertain_initializer_ids) for row in rows) == 20
    assert all(row.scientific_authority == "NONE" for row in rows)


def test_forecast_worker_requires_complete_prepared_scope_before_native_progress(stock):
    index = next(i for i, row in enumerate(stock.roster.configurations)
        if row.model_view == "oregan-spme" and ob.representative_index(stock.roster, i) == i)
    config = stock.configs[ob.node_id("forecast", index)]
    runner, context = context_for(stock, config)

    class ForbiddenProgress:
        def __getattr__(self, name):
            raise AssertionError("unprepared forecast used native progress: " + name)

    emitter = Emitter()
    with pytest.raises(ValueError, match="complete prepared native work"):
        runner.execute_streaming_with_native_subwork(context, ForbiddenProgress(), emitter)
    assert emitter.outputs == {} and all(port.closed for port in context.input_ports)


def test_all_installed_descriptors_are_cold_and_have_exact_roles():
    import subprocess
    import sys
    code = """import sys
from empirical_lawhood.adapters.composition.generated_executable_bindings import EXECUTABLE_CAPABILITY_PROVIDER_FACTORY_REGISTRY as installed
from empirical_lawhood.adapters.methods.battery_segmented_inquiry import executable_binding as b
for factory in b.EXECUTABLE_BINDING_FACTORIES:
    assert installed.provider_factory(factory.binding.binding_id) is factory
print(len(b.EXECUTABLE_BINDING_FACTORIES))
assert 'pybamm' not in sys.modules
assert 'flint' not in sys.modules
"""
    result = subprocess.run([sys.executable, "-c", code], check=True, capture_output=True, text=True)
    assert result.stdout.strip() == "7"
    from empirical_lawhood.adapters.methods.battery_segmented_inquiry import executable_binding as eb
    assert tuple(row.manifest.capability_key for row in eb.EXECUTABLE_BINDING_FACTORIES) == tuple(
        sorted(ob.NAMESPACE + "." + operation for operation in (*ob.OPERATIONS, "controlled-forecast")))


def test_installed_provider_creates_exact_declared_stream_semantic_contract():
    from empirical_lawhood.runtime.recursive_provider import RecursiveOperationProvider
    manifests = tuple(sorted(ob.operation_manifests(), key=lambda row: row.registry_id))
    registry = CapabilityRegistry("registry.exposed-segmented-provider", manifests)
    registration = next(row for row in ob.operation_registrations() if row.selection.capability_key.endswith(".forecast"))
    manifest = next(row for row in manifests if row.capability_key.endswith(".forecast"))
    provider = RecursiveOperationProvider(registry, registration, manifest, lambda: ob.SegmentedRunner("forecast"), ob.output_codecs(), N())
    contracts = provider.output_semantic_contracts(registry)
    assert len(contracts) == 2
    canonical = next(row for row in contracts if row.profile is ArtifactProfile.CANONICAL_JSON)
    streamed = next(row for row in contracts if row.profile is ArtifactProfile.JSONL_CHUNKS)
    assert canonical.record_version == se.SegmentedNativeEvidence.VERSION
    assert streamed.payload_schema == es.SegmentStreamChunk.SCHEMA
    assert not streamed.value_keys and not streamed.top_level_keys and streamed.record_version is None
