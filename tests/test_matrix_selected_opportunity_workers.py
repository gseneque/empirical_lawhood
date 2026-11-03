# SPDX-License-Identifier: MPL-2.0
"""Actual pure opportunity workers over typed in-memory issued transports.

All grants, locators and receipt descriptors here are disclosed synthetic
software controls. No native child, source qualification or publication runs.
"""

from dataclasses import replace
from decimal import Decimal as D
from hashlib import sha256
import pickle
from types import SimpleNamespace
import multiprocessing

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_opportunity as science
from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_opportunity_bindings as owner
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_opportunity_workers import SelectedOpportunityWorker
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_point import MatrixSelectedPointForecast
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_public import MatrixSelectedPointPayload, package_identity
from empirical_lawhood.adapters.methods.matrix_experimental_programme.science import MatrixPreparationNomination
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess as Access, VisibilityCeiling as Visibility
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.runtime.artifacts import ArtifactGenericValidation, ArtifactProfile, LogicalArtifactIdentity
from empirical_lawhood.runtime.capabilities import CapabilityConfigRef, CapabilityRequirement
from empirical_lawhood.runtime.execution import DependencyReceiptBinding, TaskContext, WorkerInputBinding, WorkerInputKind, WorkerInputPort, WorkerIsolationProfile, WorkerOutputPort
from empirical_lawhood.runtime.plans import ArtifactOutputSpec, BarrierKind, ExecutionTask, ExternalInputSpec, ScientificInputRole, ScientificInputSpec
from empirical_lawhood.runtime.prepared_native_invocation import PreparedInvocationContract, PreparedNativeInputContract, PreparedWorkerEnvironment
from empirical_lawhood.runtime.recursive_handoff import RecursiveImplementationBinding
from tests.test_matrix_selected_package import reference
from tests.worker_configuration_support import freeze_worker_configuration
from tests.test_matrix_selected_point import literal_unavailable_measurement
from tests.test_matrix_selected_protected_worker import MemoryReader
from tests.test_matrix_selected_opportunity import opportunity, transfer, literal_observations, committed_evidence_for  # noqa: F401 - shared in-memory fixtures


def invocation(config, values, producers, *, selected_owner=owner):
    owner = selected_owner
    protected = owner.NAMESPACE == "matrix-selected-protected-prepared"
    access = Access.OUTCOME_BLIND if protected else Access.DEVELOPMENT_VISIBLE
    task_access = owner.access(config.phase) if protected else access
    visibility = Visibility.PROSPECTIVE if protected else Visibility.DEVELOPMENT_ONLY
    declaration = next(row for row in owner.operation_declarations() if row.config_record_type is type(config)
        and row.capability_key == owner.capability_key(config.phase,
            owner.config_capability_version(config) if hasattr(owner, "config_capability_version") else
            "2.0.0" if type(config) in (*owner.preparation.native_config_types(), owner.MatrixSelectedOpportunityRootConfigV2) else "1.0.0"))
    manifest, task_id = declaration.manifest(), owner.task_id(config)
    ports, contracts, external, edges, receipts = [], [], [], [], {}
    for name, value in sorted({"automatic": config, **values}.items()):
        raw = value if type(value) is bytes else value.canonical_bytes()
        arrays = type(value) is bytes
        schema, media, profile = (MATRIX_ARRAY_SCHEMA, "application/x-npz", ArtifactProfile.MATRIX_ARRAY_NPZ) if arrays else (value.SCHEMA, "application/json", ArtifactProfile.CANONICAL_JSON)
        digest = sha256(raw).hexdigest()
        producer = producers.get(name)
        artifact_id = config.config_id if name == "automatic" else "artifact." + name
        logical = LogicalArtifactIdentity(artifact_id, digest, schema, profile, media, visibility, (), access,
            ArtifactGenericValidation("validator.synthetic-opportunity", "1.0.0", "1" * 64, schema, profile))
        binding = WorkerInputBinding(logical.logical_artifact_id, "material." + name, schema, media, len(raw), visibility,
            access, WorkerInputKind.DEPENDENCY if producer else WorkerInputKind.EXTERNAL)
        ports.append(WorkerInputPort(binding, MemoryReader(raw)))
        contracts.append(PreparedNativeInputContract(logical, binding, digest))
        output = None if producer is None else producer + (".arrays" if arrays else ".decision" if name == "decision" else ".product")
        if producer:
            receipts.setdefault(producer, []).append(binding.materialization_id)
        else:
            external.append(ExternalInputSpec("external." + name, logical.logical_artifact_id, digest, schema, media,
                len(raw), visibility, access, None))
        if name != "automatic":
            edges.append(ScientificInputSpec("edge." + name, name, ScientificInputRole.HISTORY if producer else ScientificInputRole.SOURCE,
                producer, output, None if producer else "external." + name, "scientific." + name, logical.logical_artifact_id,
                schema, media, len(raw), access, visibility, BarrierKind.NONE))
    ports.sort(key=lambda row: row.artifact_id)
    contracts.sort(key=lambda row: row.artifact_id)
    dependencies = tuple(DependencyReceiptBinding("receipt." + task, task, tuple(sorted(materials))) for task, materials in sorted(receipts.items()))
    config_ref = CapabilityConfigRef(config.config_id, config.SCHEMA, manifest.config_schema_sha256, config.fingerprint(), config.config_id)
    outputs = tuple(WorkerOutputPort(task_id + "." + row.output_id, row.payload_schema, row.profile, row.media_type,
        "output.synthetic-opportunity." + row.output_id) for row in declaration.outputs)
    requirement = CapabilityRequirement(manifest.capability_key, manifest.capability_version, manifest.kind, config_ref,
        manifest.input_schema_ids, manifest.output_schema_ids, manifest.permissions, EvidenceCeiling.RESPONSE if protected else EvidenceCeiling.NON_PROMOTABLE, task_access, owner.preparation.BUDGET)
    task = ExecutionTask(task_id, owner.stage(config.phase), requirement, manifest.implementation_sha256, tuple(sorted(receipts)), tuple(external),
        tuple(ArtifactOutputSpec(output.output_id, output.logical_artifact_id, "unpublished/" + output.output_id + ".json", output.payload_schema, output.profile,
            output.media_type, visibility, (visibility,), task_access) for output in outputs),
        (), BarrierKind.NONE, 1, ("obligation.synthetic-opportunity",), scientific_inputs=tuple(edges))
    task = freeze_worker_configuration(task)
    plan = ObjectIdentity("plan.synthetic-opportunity", "empirical-lawhood/runtime/execution-plan", "1.0.0", "a" * 64)
    packages = (("synthetic/control.py", "1" * 64),)
    implementation = RecursiveImplementationBinding(packages, sha256(canonical_json_bytes(packages)).hexdigest(), "2" * 64, "3" * 40, False)
    if config.phase in owner.NATIVE:
        provenance = config.source.provenance
        implementation = RecursiveImplementationBinding(provenance.package_sources, provenance.code_sources_sha256,
            provenance.dependency_lock_sha256, provenance.observed_git_head, provenance.observed_checkout_clean)
    context = TaskContext("run.synthetic-opportunity", task_id, "attempt.synthetic-opportunity", config_ref, tuple(row.binding for row in ports), tuple(ports),
        outputs, manifest.permissions, task_access, owner.preparation.BUDGET, WorkerIsolationProfile.TRUSTED_LOCAL, dependencies)
    prepared = PreparedInvocationContract("prepared.synthetic-opportunity", manifest, implementation,
        PreparedWorkerEnvironment("/synthetic/python", "4" * 64, "/synthetic", ()), context.run_id, task_id, context.attempt_id,
        config_ref, tuple(contracts), outputs, manifest.permissions, task_access, owner.preparation.BUDGET,
        WorkerIsolationProfile.TRUSTED_LOCAL, dependencies, execution_plan=plan, execution_task=ObjectIdentity.from_record(task_id, task),
        execution_task_record=task, required_input_artifact_ids=tuple(row.artifact_id for row in ports),
        native_effect=config.phase in owner.NATIVE)
    context = replace(context, prepared_invocation=prepared)
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_protected_workers import SelectedProtectedWorker
    runner_type = SelectedProtectedWorker if protected else SelectedOpportunityWorker
    runner = runner_type(config.phase, manifest).with_prepared_scope((context.run_id, task_id, context.input_materialization_ids, plan))
    return runner, context


@pytest.mark.parametrize("protected", (False, True))
def test_current_history_worker_pure_projection_binds_actual_direct_carriers_before_native(opportunity, transfer, protected):  # noqa: F811
    from tests.test_matrix_selected_declarative_preparation import literal_files
    from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_protected_bindings
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_protected_programme import MatrixSelectedPublicProgramme
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_protected_results import entry_seal
    from tests.test_matrix_selected_native_work import literal_history
    programme = MatrixSelectedPublicProgramme.from_programme(transfer) if protected else science.public_programme(opportunity)
    current = selected_protected_bindings if protected else owner
    if protected:
        source, _, _, initial_raw, _ = literal_history(programme, native_version="2.0.0")
        allocation = programme.sources.closure.reservation.allocation
    else:
        source = programme.sources.sources[0]
        initial_raw = literal_files(opportunity)[source.initial.array_artifact]
        allocation = next(value for value in programme.sources.allocations
            if ObjectIdentity.from_record(value.allocation_id, value) == source.original.allocation)
    task = owner.preparation.node_id(source, "history")
    config = owner.preparation.MatrixPreparationOperationConfigV2("config." + task, "history", source,
        len(allocation.canonical_bytes()))
    selected = owner.preparation.native_input_records(source)
    gate = "entry" if protected else "design"
    values = {"source": source, "allocation": allocation, "initial-state": initial_raw,
        gate: entry_seal(programme) if protected else science.opportunity_seal(programme),
        **{name: value for name, _, value in selected}}
    producers = {gate: current.global_node(programme, gate)}
    runner, context = invocation(config, values, producers, selected_owner=current)
    work = runner.prepare_native_work(context, expected_parent=context.prepared_invocation.expected_parent_contact)
    definition, = work.definitions
    assert definition.operation_id.endswith(".direct-inputs.v2")
    assert len(definition.streams) == 2
    available = [(value.logical.payload_schema, value.logical.content_sha256) for value in context.prepared_invocation.inputs]
    assert all(available.count((pin.object_schema, pin.object_fingerprint)) == 1
        for pin in (definition.configuration, *definition.sources, *definition.streams))
    first = next(name for name in values if name.startswith("native-stream."))
    wrong = {**values, first: replace(values[first], digest_sha256="f" * 64)}
    runner.preflight(context)
    assert runner._native_array_preparation.arrays(context)[0].step_index == 0
    refused, actual = invocation(config, wrong, producers, selected_owner=current)
    with pytest.raises(ValueError, match="provenance or used RNG"):
        refused.prepare_native_work(actual, expected_parent=actual.prepared_invocation.expected_parent_contact)
    for value in (context, actual):
        for port in value.input_ports:
            port.close()
    runner._native_array_preparation.clear()


@pytest.mark.parametrize("failure", (False, True))
def test_native_arrays_prepare_only_in_actual_child_reuse_exact_scope_and_clear_after_attempt(opportunity, monkeypatch, failure):  # noqa: F811
    from tests.test_matrix_selected_declarative_preparation import literal_files
    from empirical_lawhood.adapters.methods.matrix_experimental_programme import preparation_science
    from empirical_lawhood.adapters.methods.matrix_experimental_programme import prepared_native_body
    from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_native_execution
    from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_opportunity_workers as workers
    programme = science.public_programme(opportunity)
    source = programme.sources.sources[0]
    allocation = next(value for value in programme.sources.allocations
        if ObjectIdentity.from_record(value.allocation_id, value) == source.original.allocation)
    config = owner.preparation.MatrixPreparationOperationConfigV2("config." + owner.preparation.node_id(source, "history"),
        "history", source, len(allocation.canonical_bytes()))
    values = {"source": source, "allocation": allocation,
        "initial-state": literal_files(opportunity)[source.initial.array_artifact],
        "design": science.opportunity_seal(programme),
        **{name: value for name, _, value in owner.preparation.native_input_records(source)}}
    runner, context = invocation(config, values, {"design": owner.global_node(programme, "design")})
    calls = []
    actual_initial = preparation_science.initial_state
    def observed_initial(*args):
        calls.append("initial")
        return actual_initial(*args)
    monkeypatch.setattr(preparation_science, "initial_state", observed_initial)
    for _ in range(2):
        runner.prepare_native_work(context, expected_parent=context.prepared_invocation.expected_parent_contact)
    assert calls == []
    initial_port = next(value for value in context.input_ports if value.artifact_id == "artifact.initial-state")
    assert initial_port._reader.bytes_read == 0
    runner.preflight(context)
    runner.preflight(context)
    assert calls == ["initial"] and initial_port._reader.bytes_read == initial_port.size_bytes
    initial, _, _ = runner._native_array_preparation.arrays(context)
    reopened = pickle.loads(pickle.dumps(runner))
    with pytest.raises(ValueError, match="preflight array inputs"):
        reopened._native_array_preparation.arrays(context)
    changed = replace(context, attempt_id="attempt.changed-native-array",
        prepared_invocation=replace(context.prepared_invocation, attempt_id="attempt.changed-native-array"))
    with pytest.raises(ValueError, match="preflight array inputs"):
        runner._native_array_preparation.arrays(changed)
    def disclosed_body(*args, prepared_initial, **kwargs):
        assert prepared_initial is initial
        if failure:
            raise RuntimeError("disclosed software body failure before any native client contact")
        return object(), b"disclosed-no-scientific-output"
    monkeypatch.setattr(prepared_native_body, "_execute_preparation_native", disclosed_body)
    client = SimpleNamespace(parent_contact=context.prepared_invocation.expected_parent_contact)
    def exercise():
        return selected_native_execution.execute_selected_native(runner, context, client, native_phases=owner.NATIVE,
            decode=workers._decode, native_inputs=workers._native_inputs, execute_future=None,
            outputs=lambda *args: "DISCLOSED_SOFTWARE_CONTROL_ONLY")
    if failure:
        with pytest.raises(RuntimeError, match="disclosed software body failure"):
            exercise()
    else:
        assert exercise() == "DISCLOSED_SOFTWARE_CONTROL_ONLY"
    assert calls == ["initial"] and runner._native_array_preparation.__getstate__() == {"_prepared": None}
    with pytest.raises(ValueError, match="preflight array inputs"):
        runner._native_array_preparation.arrays(context)
    assert all(port._reader.stream.closed for port in context.input_ports)


def _response_invocation(programme, *, protected=False, damage=None, score=False):
    from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_protected_bindings
    from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_opportunity_future, selected_future
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.preparation_records import preparation_identity
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_forecast import forecast_public
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_prefix import identity
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_point import forecast_selected_point
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_protected_programme import MatrixSelectedPublicProgramme
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_protected_results import entry_seal
    from empirical_lawhood.infrastructure.matrix_array_io import encode_matrix_arrays
    from tests.test_matrix_selected_native_work import literal_history
    from tests.test_matrix_selected_point import feature

    if protected:
        programme = MatrixSelectedPublicProgramme.from_programme(programme)
        fixture = programme
    else:
        programme = science.public_programme(programme)
        fixture = SimpleNamespace(sources=SimpleNamespace(source_arms=lambda:
            tuple((None, source) for source in programme.sources.sources),
            closure=SimpleNamespace(reservation=programme.reservation)))
    current = selected_protected_bindings if protected else owner
    future = selected_future if protected else selected_opportunity_future
    source, history, _, initial_raw, history_raw = literal_history(fixture, native_version="2.0.0")
    public = next(row for _, row in programme.point_design.sources if row.source == source.identity)
    _, _, causal, _, _, causal_raw, _ = literal_unavailable_measurement("E6_TRANSFER" if protected else "E5_OPPORTUNITY")
    causal = replace(causal, source=source.identity, preparation=preparation_identity(history.arrays),
        arrays=replace(causal.arrays, source=source.identity, producers=tuple(sorted((source.identity,
            preparation_identity(history.arrays), causal.witness, causal.frame_assessment), key=lambda row: row.object_id))))
    point = forecast_selected_point(programme.point_design, replace(feature(programme.point_design, public),
        prefix=identity(causal), frame_sha256=None, disposition="UNAVAILABLE", values=()), record_id="point.disclosed-response-worker")
    protocol = programme.protocol(source)
    templates, _ = encode_matrix_arrays({"generic_basis": np.zeros((3, 4, 4), dtype="<c16"),
        "force_coefficients": np.zeros((2, 3, 3), dtype="<f8"), "trace_coefficients": np.zeros((2, 3), dtype="<f8"),
        "receiver_coefficients": np.zeros((48, 2, 2, 3, 4), dtype="<f8")})
    mechanical_raw, mechanical = forecast_public(public, protocol, causal, causal_raw, templates,
        artifact_id="mechanical.disclosed-response-worker")
    config_type = future.MatrixSelectedFutureConfigV2 if protected else future.MatrixSelectedOpportunityFutureConfigV2
    config = config_type("config." + future.node_id(source, "responses"), programme.identity, source, protocol,
        dict(programme.panels)[source.root.root.independent_group_id], programme.point_design.identity,
        package_identity(programme.point_design.package), "responses")
    allocation = programme.sources.closure.reservation.allocation if protected else programme.reservation.allocation
    gate = "entry" if protected else "design"
    values = {"source": source, "allocation": allocation, "initial-state": initial_raw, "history": history,
        "history-arrays": history_raw, "causal": causal, "point": point, "mechanical": mechanical,
        "mechanical-arrays": mechanical_raw, "protocol": protocol,
        gate: entry_seal(programme) if protected else science.opportunity_seal(programme),
        **{name: value for name, _, value in current.preparation.native_input_records(source, panels=config.panels)}}
    producers = {gate: current.global_node(programme, gate),
        "history": current.preparation.node_id(source, "history"),
        "history-arrays": current.preparation.node_id(source, "history"),
        "causal": future.node_id(source, "project"), "point": future.node_id(source, "point"),
        "mechanical": future.node_id(source, "mechanical"), "mechanical-arrays": future.node_id(source, "mechanical")}
    if score:
        from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_future_custody import MatrixPreparedFutureArrays
        from empirical_lawhood.kernel.references import ArtifactIdentity
        raw, members = encode_matrix_arrays({"unentered_branches": np.arange(48, dtype="<i8")})
        operand = MatrixPreparedFutureArrays("arrays.disclosed-score-unentered", source.identity,
            ArtifactIdentity("array.disclosed-score-unentered", "software-unentered-marker", MATRIX_ARRAY_SCHEMA,
                sha256(raw).hexdigest(), "application/x-npz", len(raw)), members)
        disposition = ("NO_ORIGIN" if causal.disposition == "NO_ORIGIN" else
            "INSTRUMENT_UNRESOLVED" if mechanical.disposition == "INSTRUMENT_UNRESOLVED" else "UNEVALUABLE")
        kind = future.MatrixSelectedFutureHistory if protected else future.MatrixSelectedOpportunityFutureHistory
        responses = kind("responses.disclosed-score", source.identity, preparation_identity(history), identity(causal),
            identity(point), identity(mechanical), ObjectIdentity.from_record(protocol.protocol_id, protocol),
            tuple(row.identity for row in config.panels), tuple(row[0] for row in future.branch_census(protocol, config.panels)),
            operand, (), disposition)
        kind = future.MatrixSelectedFutureConfig if protected else future.MatrixSelectedOpportunityFutureConfig
        config = kind("config." + future.node_id(source, "response-score"), config.programme, source, protocol,
            config.panels, config.point_design, config.frozen_package, "response-score")
        values = {name: value for name, value in values.items() if name in current.INPUTS["response-score"]}
        values.update({"causal-arrays": causal_raw, "templates": templates, "responses": responses, "response-arrays": raw})
        producers.update({"causal-arrays": future.node_id(source, "project"),
            "responses": future.node_id(source, "responses"), "response-arrays": future.node_id(source, "responses")})
        return invocation(config, values, producers, selected_owner=current)
    stream = next(name for name in values if name.startswith("native-stream."))
    if damage == "missing-stream":
        del values[stream]
    elif damage == "changed-stream":
        values[stream] = replace(values[stream], digest_sha256="f" * 64)
    elif damage == "history-producer":
        producers["history"] += ".foreign"
    elif damage == "array-bytes":
        values["history-arrays"] = history_raw[:-1]
    return invocation(config, values, producers, selected_owner=current)


@pytest.mark.parametrize("protected", (False, True))
def test_current_response_worker_projects_exact_four_rng_inputs_and_reuses_only_child_arrays(opportunity, transfer, protected, monkeypatch):  # noqa: F811
    runner, context = _response_invocation(transfer if protected else opportunity, protected=protected)
    ports = tuple(port for port in context.input_ports if port.payload_schema == MATRIX_ARRAY_SCHEMA)
    work = runner.prepare_native_work(context, expected_parent=context.prepared_invocation.expected_parent_contact)
    assert len(work.definitions[0].streams) == 4
    available = [(row.logical.payload_schema, row.logical.content_sha256) for row in context.prepared_invocation.inputs]
    assert all(available.count((pin.object_schema, pin.object_fingerprint)) == 1
        for pin in (work.definitions[0].configuration, *work.definitions[0].sources, *work.definitions[0].streams))
    assert all(port._reader.bytes_read == 0 for port in ports)
    runner.preflight(context)
    cached = runner._native_array_preparation.arrays(context)
    runner.preflight(context)
    assert all(port._reader.bytes_read == port.size_bytes for port in ports)
    assert runner._native_array_preparation.arrays(context) == cached
    from decimal import localcontext
    with localcontext() as selected_context:
        selected_context.prec += 1
        with pytest.raises(ValueError, match="preflight array inputs"):
            runner._native_array_preparation.arrays(context)
    from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_native_execution
    from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_protected_workers, selected_opportunity_workers
    workers = selected_protected_workers if protected else selected_opportunity_workers
    def future(*args, prepared_arrays, **kwargs):
        assert prepared_arrays == cached[1:]
        return b"disclosed-no-native-contact", object()
    result = selected_native_execution.execute_selected_native(runner, context,
        SimpleNamespace(parent_contact=context.prepared_invocation.expected_parent_contact),
        native_phases=("history", "responses"), decode=workers._decode, native_inputs=workers._native_inputs,
        execute_future=future, outputs=lambda *args: "DISCLOSED_NONENTRY_SOFTWARE_CONTROL")
    assert result == "DISCLOSED_NONENTRY_SOFTWARE_CONTROL" and runner._native_array_preparation._prepared is None
    assert all(port._reader.stream.closed for port in context.input_ports)


@pytest.mark.parametrize("protected", (False, True))
@pytest.mark.parametrize("damage", ("missing-stream", "changed-stream", "history-producer", "array-bytes"))
def test_current_response_worker_refuses_missing_rng_wrong_producer_and_changed_array_before_contact(opportunity, transfer, protected, damage):  # noqa: F811
    runner, context = _response_invocation(transfer if protected else opportunity, protected=protected, damage=damage)
    try:
        expected = {"missing-stream": "provenance or used RNG", "changed-stream": "provenance or used RNG",
            "history-producer": "actual ordinary producer output", "array-bytes": "Matrix array transport"}[damage]
        with pytest.raises(ValueError, match=expected):
            runner.preflight(context)
        assert runner._native_array_preparation._prepared is None
    finally:
        for port in context.input_ports:
            port.close()


@pytest.mark.parametrize("protected", (False, True))
def test_future_custody_refuses_coherent_completion_from_another_array_lane(opportunity, transfer, protected, monkeypatch):  # noqa: F811
    """Isolate embedded receipt custody; this fabricates no scientific observation."""
    from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_protected_workers, selected_opportunity_workers
    from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_future, selected_opportunity_future
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.preparation_records import preparation_identity
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_prefix import identity
    from empirical_lawhood.adapters.methods.matrix_parameter_history.records import MatrixParameterNativeHistory
    from empirical_lawhood.kernel.recursive_inquiry import InquiryCost
    from empirical_lawhood.kernel.status import OperationalStatus
    from empirical_lawhood.runtime.artifacts import ArtifactMaterialization, CanonicalTaskReceipt
    from empirical_lawhood.runtime.native_subwork import NativeSubworkCompletion, NativeSubworkContact
    from tests.native_completion_fixtures import literal_completion, receipt_with_completion
    from tests.test_matrix_prepared_future_custody import marker

    workers = selected_protected_workers if protected else selected_opportunity_workers
    future = selected_future if protected else selected_opportunity_future
    runner, context = _response_invocation(transfer if protected else opportunity, protected=protected)
    try:
        config, records, _ = workers._decode(context, runner)
        work = runner.prepare_native_work(context, expected_parent=context.prepared_invocation.expected_parent_contact)
        definition, = work.definitions
        task = "native-subwork." + sha256((definition.parent_contact.task_id + ":" + definition.subwork_id).encode()).hexdigest()
        attempt = definition.parent_contact.run_id + "." + task + ".attempt-001"
        contact = NativeSubworkContact(ObjectIdentity("begin.disclosed-lane", "empirical-lawhood/runtime/native-subwork-begin", "1.0.0", "c" * 64))
        completion = NativeSubworkCompletion(definition.identity, ObjectIdentity.from_record("contact.disclosed-lane", contact),
            OperationalStatus.SUCCEEDED, ("arrays",), (), definition.streams, (), (), InquiryCost(None, None, None),
            "disclosed metadata only; no native contact or scientific observations", None, ())
        access = Access.EVALUATION_SEALED if protected else Access.DEVELOPMENT_VISIBLE
        visibility = Visibility.PROSPECTIVE if protected else Visibility.DEVELOPMENT_ONLY
        publication = literal_completion(completion, task, visibility=visibility, access=access)
        raw, marker_operand = marker()
        logical = LogicalArtifactIdentity(task + ".output.arrays", sha256(raw).hexdigest(), MATRIX_ARRAY_SCHEMA,
            ArtifactProfile.MATRIX_ARRAY_NPZ, "application/x-npz", visibility, (), access,
            ArtifactGenericValidation("validator.disclosed-lane", "1.0.0", "a" * 64, MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ))
        materialization = ArtifactMaterialization("material." + logical.logical_artifact_id, logical.logical_artifact_id, "storage.synthetic-unpublished",
            "unpublished/disclosed-lane.npz", logical.content_sha256, len(raw), "none")
        receipt = CanonicalTaskReceipt("receipt." + attempt, definition.parent_contact.run_id, task, attempt,
            definition.parent_contact.implementation_commit, definition.parent_contact.input_materialization_ids,
            tuple(sorted((materialization, publication.materialization), key=lambda row: row.materialization_id)),
            tuple(sorted((logical, publication.logical), key=lambda row: row.logical_artifact_id)), (), OperationalStatus.SUCCEEDED, ())
        native = MatrixParameterNativeHistory(definition, completion, receipt)
        operand = replace(marker_operand, source=config.source.identity,
            array_artifact=replace(marker_operand.array_artifact, artifact_id=logical.logical_artifact_id))
        product_type = future.MatrixSelectedFutureHistory if protected else future.MatrixSelectedOpportunityFutureHistory
        product = product_type("responses.disclosed-lane", config.source.identity, preparation_identity(records["history"]),
            identity(records["causal"]), identity(records["point"]), identity(records["mechanical"]),
            ObjectIdentity.from_record(config.protocol.protocol_id, config.protocol), tuple(row.identity for row in config.panels),
            tuple(row[0] for row in future.branch_census(config.protocol, config.panels)), operand, (native,), "COMPLETED")
        # Original source/causal science is separately exercised by worker tests.
        # Only the custody predicate is exercised with disclosed AVAILABLE flags.
        monkeypatch.setattr(future, "check_handoff", lambda *args: None)
        causal = SimpleNamespace(disposition="AVAILABLE")
        mechanical = SimpleNamespace(disposition="AVAILABLE")
        monkeypatch.setattr(future, "identity", lambda record: identity(records["causal"]) if record is causal else
            identity(records["mechanical"]) if record is mechanical else identity(record))
        future.validate_future_history(config, records["history"], causal, records["point"], mechanical, product)
        changed = literal_completion(completion, task, visibility=Visibility.PROSPECTIVE if not protected else Visibility.DEVELOPMENT_ONLY,
            access=Access.OUTCOME_BLIND if not protected else Access.DEVELOPMENT_VISIBLE)
        altered = replace(product, native=(replace(native, receipt=receipt_with_completion(receipt, changed)),))
        with pytest.raises(ValueError, match="completion bytes, access or lineage"):
            future.validate_future_history(config, records["history"], causal, records["point"], mechanical, altered)
    finally:
        for port in context.input_ports:
            port.close()


def _spawn_cache_check(runner, connection):
    try:
        assert runner._native_array_preparation._prepared is None
        try:
            runner._native_array_preparation.arrays(object())
        except ValueError:
            connection.send("EMPTY_INVOCATION_CACHE")
        else:
            connection.send("UNSAFE_DERIVED_ARRAY_REUSE")
    finally:
        connection.close()


def test_spawned_selected_worker_cannot_inherit_preflight_arrays(opportunity):  # noqa: F811
    runner, context = _response_invocation(opportunity)
    try:
        runner.preflight(context)
        selected = multiprocessing.get_context("spawn")
        receiving, sending = selected.Pipe(duplex=False)
        child = selected.Process(target=_spawn_cache_check, args=(runner, sending))
        try:
            child.start()
            sending.close()
            assert receiving.poll(30), "spawned software control did not return"
            assert receiving.recv() == "EMPTY_INVOCATION_CACHE"
            child.join(timeout=10)
            assert child.exitcode == 0
        finally:
            receiving.close()
            sending.close()
            if child.is_alive():
                child.terminate()
                child.join(timeout=10)
    finally:
        runner._native_array_preparation.clear()
        for port in context.input_ports:
            port.close()


def point_invocation():
    design, source, causal, witness, frames, causal_raw, diagnostic_raw = literal_unavailable_measurement("E5_OPPORTUNITY")
    design = MatrixSelectedPointPayload.from_design(design)
    programme = reference("programme.synthetic-opportunity-point", science.MatrixSelectedOpportunityPublicProgramme)
    config = owner.MatrixSelectedOpportunityConfig("config." + owner.NAMESPACE + "." + source.source.object_id + ".point", programme, source, "point")
    seal = science.MatrixSelectedOpportunitySeal("design.synthetic-opportunity-point", programme,
        reference("sources.synthetic-opportunity", science.MatrixPreparationSourceBank), design.identity, package_identity(design.package),
        tuple(sorted(row.source.object_id for _, row in design.sources)))
    values = {"point-design": design, "design": seal, "witness": witness, "frames": frames, "causal": causal,
        "causal-arrays": causal_raw, "diagnostic-arrays": diagnostic_raw}
    producers = {name: owner.NAMESPACE + "." + source.source.object_id + "." + phase
        for name, phase in (("witness", "measure"), ("diagnostic-arrays", "measure"), ("frames", "frames"), ("causal", "project"), ("causal-arrays", "project"))}
    producers["design"] = owner.NAMESPACE + ".design." + programme.object_fingerprint
    return invocation(config, values, producers)


def nomination_invocation(programme, *, headroom=True):
    programme = science.public_programme(programme)
    config = owner.MatrixSelectedOpportunityRootConfig("config." + owner.global_node(programme, "nominate"), programme, "nominate")
    values, producers = {"design": science.opportunity_seal(programme)}, {"design": owner.global_node(programme, "design")}
    observations = literal_observations(programme, hold_error=D(".9") if headroom else D(".01"))
    for case_id, products in observations.items():
        source_id = case_id.removeprefix("case.")
        for name, phase, product in zip(("points", "mechanicals", "readouts"), ("point", "mechanical", "response-score"), products, strict=True):
            key = name + "." + source_id
            values[key], producers[key] = product, owner.NAMESPACE + "." + source_id + "." + phase
    return invocation(config, values, producers)


def test_actual_selected_opportunity_point_worker_uses_literal_causal_arrays_and_preserves_unavailable_values():
    runner, context = point_invocation()
    result = runner.execute(context)
    point = decode_canonical_bytes(result.outputs[0].payload, MatrixSelectedPointForecast, maximum_bytes=None)
    assert point.feature.disposition == "UNAVAILABLE" and all(values == (None,) * 15 for _, values in point.log_points)
    assert point.uncertainty_status == "POINT_ONLY_DOWNSTREAM_APPLICABILITY_NOT_ASSESSED"
    assert all(port._reader.stream.closed for port in context.input_ports)


@pytest.mark.parametrize("headroom,expected", ((True, "NOMINATED"), (False, "NONDISCRIMINATING_OPPORTUNITY")))
def test_actual_selected_nomination_worker_authenticates_full_receipt_graph_and_keeps_negative(opportunity, headroom, expected):  # noqa: F811
    runner, context = nomination_invocation(opportunity, headroom=headroom)
    result = runner.execute(context)
    payload = next(row.payload for row in result.outputs if row.output_id.endswith(".product"))
    nomination = decode_canonical_bytes(payload, MatrixPreparationNomination, maximum_bytes=None)
    assert nomination.disposition == expected and len(nomination.cases) == 3
    assert nomination.package == opportunity.point_design.package.identity
    assert nomination.selected_arm_id == ("fixed-a" if headroom else None)
    assert all(port._reader.stream.closed for port in context.input_ports)


@pytest.mark.parametrize("damage", ("unprepared", "run", "plan", "corrupt-array", "wrong-producer", "foreign-lane"))
def test_selected_opportunity_worker_refuses_current_scope_bytes_receipt_and_lane_substitution(damage):
    runner, context = point_invocation()
    if damage == "unprepared":
        runner = SelectedOpportunityWorker("point", runner.manifest)
    elif damage == "run":
        runner = runner.with_prepared_scope(("run.foreign", *runner.prepared_scope[1:]))
    elif damage == "plan":
        runner = runner.with_prepared_scope((*runner.prepared_scope[:3], replace(runner.prepared_scope[3], object_id="plan.foreign")))
    elif damage == "corrupt-array":
        port = next(row for row in context.input_ports if row.artifact_id == "artifact.causal-arrays")
        port._reader.raw = port._reader.raw[:-1] + b"X"
    elif damage == "foreign-lane":
        ports = tuple(WorkerInputPort(replace(port.binding, outcome_access=Access.OUTCOME_BLIND), port._reader) if port.artifact_id == "artifact.causal" else port
            for port in context.input_ports)
        prepared = context.prepared_invocation
        inputs = tuple(replace(item, logical=replace(item.logical, outcome_access=Access.OUTCOME_BLIND),
            binding=replace(item.binding, outcome_access=Access.OUTCOME_BLIND)) if item.artifact_id == "artifact.causal" else item for item in prepared.inputs)
        task = prepared.execution_task_record
        task = replace(task, scientific_inputs=tuple(replace(edge, outcome_access=Access.OUTCOME_BLIND) if edge.consumer_input_id == "causal" else edge
            for edge in task.scientific_inputs))
        prepared = replace(prepared, inputs=inputs, execution_task_record=task, execution_task=ObjectIdentity.from_record(task.task_id, task))
        context = replace(context, input_bindings=tuple(port.binding for port in ports), input_ports=ports, prepared_invocation=prepared)
    else:
        prepared = context.prepared_invocation
        task = prepared.execution_task_record
        edges = tuple(replace(edge, producer_output_id=edge.producer_task_id + ".foreign") if edge.consumer_input_id == "causal-arrays" else edge
            for edge in task.scientific_inputs)
        task = replace(task, scientific_inputs=edges)
        prepared = replace(prepared, execution_task_record=task, execution_task=ObjectIdentity.from_record(task.task_id, task))
        context = replace(context, prepared_invocation=prepared)
    with pytest.raises((ValueError, PermissionError)):
        runner.execute(context)


def test_actual_design_worker_requires_exact_original_four_products_and_emits_only_public_seal(opportunity):  # noqa: F811
    evidence, parents = committed_evidence_for(opportunity)
    programme = science.public_programme(opportunity)
    config = owner.MatrixSelectedOpportunityRootConfigV2("config." + owner.global_node(programme, "design"), programme, "design",
        evidence.identity, len(evidence.canonical_bytes()), parents)
    runner, context = invocation(config, {"evidence": evidence}, {})
    result = runner.execute(context)
    seal = decode_canonical_bytes(result.outputs[0].payload, science.MatrixSelectedOpportunitySeal, maximum_bytes=None)
    assert seal == science.opportunity_seal(programme)
    assert b'"scores"' not in result.outputs[0].payload



@pytest.mark.parametrize("protected", (False, True))
def test_actual_selected_response_score_worker_expands_mechanical_archive_once(opportunity, transfer, protected, monkeypatch):  # noqa: F811
    from empirical_lawhood.infrastructure import matrix_array_io
    from empirical_lawhood.adapters.methods.matrix_experimental_programme import prepared_response_science
    runner, context = _response_invocation(transfer if protected else opportunity, protected=protected, score=True)
    original_decode = matrix_array_io._decode_matrix_arrays
    target = next(port for port in context.input_ports if port.artifact_id == "artifact.mechanical-arrays")
    digest = next(row.physical_sha256 for row in context.prepared_invocation.inputs if row.logical.logical_artifact_id == target.artifact_id)
    calls = []

    def decode(raw, operand):
        if sha256(raw).hexdigest() == digest:
            calls.append(operand)
        return original_decode(raw, operand)

    monkeypatch.setattr(matrix_array_io, "_decode_matrix_arrays", decode)
    monkeypatch.setattr(np.random, "Generator", lambda *_args, **_kwargs: pytest.fail("score worker created RNG"))
    result = runner.execute(context)
    payload, = result.outputs
    readout = decode_canonical_bytes(payload.payload, prepared_response_science.MatrixPreparedResponseReadout, maximum_bytes=None)
    assert len(calls) == 1
    assert readout.disposition in ("NO_ORIGIN", "UNEVALUABLE", "INSTRUMENT_UNRESOLVED")
    assert not readout.controls and len(readout.unentered_branch_ids) == 48 and len(readout.cells) == 240
    assert readout.cumulative_log_errors == (None,) * 15
    assert all(port._reader.stream.closed for port in context.input_ports)
