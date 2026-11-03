# SPDX-License-Identifier: MPL-2.0
"""Actual E4 DEV worker inputs and Ready/Stop over exposed software streams.

The tiny native source and synthetic entry/point records are software controls,
never fresh allocation, scientific eligibility or original E3 authority. Every
worker has its complete actual configuration, input bytes, producer bindings,
current numerical provenance and nested native receipt. No public scientific
campaign or protected outcome is entered.
"""
from dataclasses import replace
from decimal import Decimal as D, localcontext
from hashlib import sha256
import json
import os
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from threadpoolctl import threadpool_limits

from empirical_lawhood.adapters.methods.matrix_factor_response.configured_secondary_readout import MatrixE4SecondaryReadoutSelection
from empirical_lawhood.adapters.methods.matrix_factor_response.experiment_methods import METHODS
from empirical_lawhood.adapters.methods.matrix_factor_response.response_error_prediction import FEATURES
from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as old, science
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_bindings as owner
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_records as r
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_science as method
from empirical_lawhood.adapters.methods.matrix_scheduled_history import response_forecast
from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex
from empirical_lawhood.adapters.methods.matrix_scheduled_history.forecast import FAMILY_MAP, ScheduledPublicSource
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_records import ScheduledProgrammeFactor
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e3_e4_workers import SelectedE3E4Worker
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_native_source import bind_selected_native_source
from empirical_lawhood.api.recursive_authoring import implementation_binding
from empirical_lawhood.infrastructure import execution as lifecycle
from empirical_lawhood.infrastructure.matrix_array_io import encode_matrix_arrays
from empirical_lawhood.infrastructure.numerical_provenance import selected_worker_environment
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess as Access, VisibilityCeiling as Visibility
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactManifest, ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.capabilities import CapabilityConfigRef, CapabilityRequirement
from empirical_lawhood.runtime.execution import DependencyReceiptBinding, TaskContext, VerifiedArtifactInput, WorkerInputBinding, WorkerInputKind, WorkerIsolationProfile, WorkerOutputPort
from empirical_lawhood.runtime.plans import ArtifactOutputSpec, BarrierKind, ExecutionTask, ExternalInputSpec, ScientificInputRole, ScientificInputSpec
from empirical_lawhood.adapters.methods.matrix_response_study.numerical_runtime import MATRIX_PROVENANCE_REQUIREMENT
from tests.runtime_platform.test_native_subwork import _store
from tests.test_matrix_factor_confirmation_eligibility import stock, provenance, publish  # noqa: F401
from tests.test_matrix_scheduled_history import scheduled  # noqa: F401
from tests.test_matrix_scheduled_response_forecast import pauli
from tests.test_matrix_prepared_assay_method import literal_protocol
from tests.test_matrix_selected_package import package
from tests.test_matrix_selected_protected_worker import MemoryReader
from tests.worker_configuration_support import freeze_worker_configuration


def pin(name, kind):
    return ObjectIdentity(name, kind.SCHEMA, kind.VERSION, sha256(name.encode()).hexdigest())


def record_exposure(case, phase, *, completion=None, raw=None):
    """Optional EL report of physical use, separate from four-purpose reservation."""
    destination = os.environ.get("EL_NATIVE_EXPOSURE_REPORT")
    if destination is None:
        return
    path = Path(destination)
    assert path.is_relative_to(Path("/media/chevre/EL/empirical-lawhood"))
    source = case.source
    start, stop = ((0, source.policy.cutoff_tick) if phase == "prefix" else
        (source.policy.cutoff_tick, source.coordinate.total_ticks))
    physically_used = tuple(value for value in source.root.streams if
        value.purpose.startswith("preparation") and start < source.coordinate.ramp_ticks
        or value.purpose.startswith("autonomous") and stop > max(start, source.coordinate.ramp_ticks))
    if completion is not None:
        assert set(completion.consumed_streams) == {source.root.stream_identity(value) for value in physically_used}
    event = {"root_id": source.root_id, "independent_group_id": source.root.root.independent_group_id,
        "source_id": source.source_id, "source_sha256": source.fingerprint(), "phase": phase,
        "start_tick": start, "stop_tick": stop, "ramp_ticks": source.coordinate.ramp_ticks,
        "cutoff_tick": source.policy.cutoff_tick, "total_ticks": source.coordinate.total_ticks,
        "archive_sha256": None if raw is None else sha256(raw).hexdigest(),
        "completion_sha256": None if completion is None else completion.fingerprint(),
        "consumed": [{"purpose": value.purpose, "seed_sha256": value.digest_sha256,
            "effective_seed": value.effective_seed} for value in physically_used]}
    report = json.loads(path.read_text()) if path.exists() else {"schema": "exposed-e4-software-native-use.v1",
        "scope": "Tiny existing exposed software fixture only; no public selected acquisition or response branch entered.",
        "events": []}
    if event not in report["events"]:
        report["events"].append(event)
    report["actual_acquired_group_ids"] = sorted({row["independent_group_id"] for row in report["events"]})
    report["actual_consumed_effective_seeds"] = sorted({item["effective_seed"] for row in report["events"] for item in row["consumed"]})
    all_declared = tuple(value for root in source.allocation.roots for value in root.streams) + tuple(value for panel in case.panels for value in panel.streams)
    report["reserved_or_excluded_group_ids"] = sorted(set(source.allocation.independent_group_ids) - set(report["actual_acquired_group_ids"]))
    report["reserved_or_excluded_effective_seeds"] = sorted((set(report.get("reserved_or_excluded_effective_seeds", ())) |
        {value.effective_seed for value in all_declared}) - set(report["actual_consumed_effective_seeds"]))
    report["response_branch_state"] = "NOT_ENTERED"
    report["test_source_sha256"] = sha256(Path(__file__).read_bytes()).hexdigest()
    path.write_text(json.dumps(report, indent=2, sort_keys=True)+"\n")


def invoke(case, phase, extra=None, *, suffix="original"):
    config = replace(case.config, phase=phase, config_id="config."+owner.local_node(case.source.root_id, phase))
    declaration = next(row for row in owner.operation_declarations() if row.capability_key == owner.NAMESPACE+"."+phase)
    manifest = declaration.manifest()
    values = {"entry": case.entry, "source": case.local, "provenance": case.source.provenance,
        **{"streams."+str(index): value for index, value in enumerate(case.source.root.streams)}}
    producers = {"entry": (owner.NAMESPACE+".entry."+case.programme.object_fingerprint, "product")}
    if phase != "prefix":
        values.update(case.future)
        producers.update({name: (owner.local_node(case.source.root_id, producer), output) for name, producer, output in (
            ("prefix", "prefix", "product"), ("prefix-arrays", "prefix", "arrays"),
            ("checkpoint", "prefix", "checkpoint"), ("causal", "project", "product"),
            ("account", "account", "product"), ("mechanical", "mechanical", "product"))})
    if phase == "responses":
        values["mechanical-arrays"] = case.physical_raw
        producers["mechanical-arrays"] = (owner.local_node(case.source.root_id, "mechanical"), "arrays")
        independent = next(row for row in case.panels if row.role == "INDEPENDENT_FUTURE")
        values.update({"streams."+str(index+4): value for index, value in enumerate(independent.streams)})
    values.update(extra or {})
    values["automatic"] = config
    verified, bindings, external, edges, dependencies = [], [], [], [], {}
    for index, (name, value) in enumerate(sorted(values.items())):
        array = type(value) is bytes
        raw = value if array else value.canonical_bytes()
        logical_id = config.config_id if name == "automatic" else "e4-control."+phase+"."+suffix+"."+name
        result = case.plane.write(ArtifactWriteRequest(logical_id,
            "worker-inputs/"+phase+"/"+suffix+"/"+str(index).zfill(2)+( ".npz" if array else ".json"),
            MATRIX_ARRAY_SCHEMA if array else value.SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ if array else ArtifactProfile.CANONICAL_JSON,
            "application/x-npz" if array else "application/json", "e4-software-controls", "worker-inputs", raw,
            Visibility.DEVELOPMENT_ONLY, (), Access.DEVELOPMENT_VISIBLE))
        selected = VerifiedArtifactInput(result.logical, result.materialization)
        verified.append(selected)
        producer = producers.get(name)
        binding = WorkerInputBinding.from_verified(selected, kind=WorkerInputKind.DEPENDENCY if producer else WorkerInputKind.EXTERNAL)
        bindings.append(binding)
        if producer:
            dependencies.setdefault(producer[0], []).append(binding.materialization_id)
        else:
            external.append(ExternalInputSpec("external."+name, logical_id, result.logical.content_sha256,
                result.logical.payload_schema, result.logical.media_type, len(raw), Visibility.DEVELOPMENT_ONLY, Access.DEVELOPMENT_VISIBLE, None))
        if name != "automatic":
            edges.append(ScientificInputSpec("edge."+name, name, ScientificInputRole.HISTORY if producer else ScientificInputRole.SOURCE,
                None if producer is None else producer[0], None if producer is None else producer[0]+"."+producer[1],
                "external."+name if producer is None else None, "scientific."+name, logical_id,
                result.logical.payload_schema, result.logical.media_type, len(raw), Access.DEVELOPMENT_VISIBLE,
                Visibility.DEVELOPMENT_ONLY, BarrierKind.NONE))
    task_id = owner.local_node(case.source.root_id, phase)
    receipts = tuple(DependencyReceiptBinding("receipt.control."+name, name, tuple(sorted(materials)))
        for name, materials in sorted(dependencies.items()))
    config_input = next(row for row in verified if row.artifact_id == config.config_id)
    config_ref = CapabilityConfigRef(config.config_id, config.SCHEMA, manifest.config_schema_sha256,
        config.fingerprint(), config_input.artifact_id)
    outputs = tuple(WorkerOutputPort(task_id+"."+row.output_id, row.payload_schema, row.profile, row.media_type,
        "e4-control.output."+phase+"."+row.output_id) for row in declaration.outputs)
    requirement = CapabilityRequirement(manifest.capability_key, manifest.capability_version, manifest.kind, config_ref,
        manifest.input_schema_ids, manifest.output_schema_ids, manifest.permissions, EvidenceCeiling.NON_PROMOTABLE,
        Access.DEVELOPMENT_VISIBLE, owner.BUDGET)
    task = ExecutionTask(task_id, owner.stage(phase), requirement, manifest.implementation_sha256,
        tuple(sorted(dependencies)), tuple(external), tuple(ArtifactOutputSpec(row.output_id, row.logical_artifact_id,
            "outputs/"+phase+"/"+row.output_id, row.payload_schema, row.profile, row.media_type,
            Visibility.DEVELOPMENT_ONLY, (Visibility.DEVELOPMENT_ONLY,), Access.DEVELOPMENT_VISIBLE) for row in outputs),
        (), BarrierKind.NONE, 1, ("obligation.e4-control."+phase,), scientific_inputs=tuple(edges))
    task = freeze_worker_configuration(task)
    verified.sort(key=lambda row: row.artifact_id)
    bindings.sort(key=lambda row: row.artifact_id)
    ports = case.plane.open_many(tuple(verified), bindings=tuple(bindings), maximum_bytes=None)
    context = TaskContext("run.e4-worker-control", task_id, "attempt.e4-worker-control."+phase,
        config_ref, tuple(bindings), ports, outputs, manifest.permissions, Access.DEVELOPMENT_VISIBLE,
        owner.BUDGET, WorkerIsolationProfile.TRUSTED_LOCAL, receipts)
    plan = ObjectIdentity("plan.e4-worker-control", "empirical-lawhood/runtime/development-execution-plan", "1.0.0", "a"*64)
    runner = SelectedE3E4Worker(phase, manifest).with_prepared_scope((context.run_id, task_id, context.input_materialization_ids, plan))
    initial = lifecycle.prepare_worker_invocation(runner, context, tuple(verified), implementation=case.implementation,
        execution_plan=plan, execution_task=ObjectIdentity.from_record(task_id, task), execution_task_record=task,
        native_effect=True, provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,))
    bound = replace(context, prepared_invocation=initial)
    work = runner.prepare_native_work(bound, expected_parent=initial.expected_parent_contact)
    final = replace(initial, native_work=work)
    return runner, replace(context, prepared_invocation=final), final, tuple(verified)


def ready(runner, context, contract):
    result = lifecycle._worker_preflight(runner, context, contract, (MATRIX_PROVENANCE_REQUIREMENT,),
        native_work_preparer=owner.prepare_native_work)
    assert result.ready, tuple((row.operand_id, row.reason) for row in result.mismatches)
    return result


@pytest.fixture
def native_case(scheduled, provenance, monkeypatch):  # noqa: F811
    for name, value in selected_worker_environment():
        monkeypatch.setenv(name, value)
    with threadpool_limits(limits=1):
        plane, sources = scheduled
        source = next(row for row in sources if row.root.root.role.value == "DEVELOPMENT")
        policy = replace(source.policy, origin_sector="Y")
        selection = replace(source.specification.selection, prefix_policies=(policy,),
            coordinate_policies=tuple((co, old.identity(policy)) for co, _ in source.specification.selection.coordinate_policies))
        specification = replace(source.specification, selection=selection,
            publication=publish(plane, selection, "worker-control.selection"))
        index=ScheduledSourceIndex.from_shared(reservation=source.reservation,specification=specification,provenances=(provenance,))
        source=index.resolve(index.reference(source_id=source.source_id,root_id=source.root_id,provenance=provenance.identity))
        programme, bank = pin("programme.e4-worker-control", r.SelectedE3E4DevelopmentProgramme), pin("bank.e4-worker-control", r.SelectedE3E4DevelopmentBank)
        local = r.SelectedE3E4NativeSourceReference("native."+source.source_id, programme, bank,
            source.reference, ScheduledPublicSource.from_source(source), policy,
            source.numerical_design, provenance.identity, len(provenance.canonical_bytes()))
        protocol, _ = literal_protocol()
        protocol = replace(protocol, public_source=local.public, horizon_steps=(1, 2),
            templates=replace(protocol.templates, source=local.reference.identity, producers=(local.reference.identity,)))
        from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponsePanel
        from empirical_lawhood.adapters.methods.matrix_history_analysis.records import HISTORY_PURPOSES, MatrixHistorySeed
        group = source.root.root.independent_group_id
        panels = (ScheduledResponsePanel("panel.e4-worker.common", group, "COMMON_NOISE_PANEL", "ORIGINAL_COMPLETED_PREFIX_GENERATOR_STATES", source.root.streams),
            ScheduledResponsePanel("panel.e4-worker.independent", group, "INDEPENDENT_FUTURE", "FRESH_DECLARED_FUTURE_START_AT_CUTOFF",
                tuple(MatrixHistorySeed(purpose, sha256(("EXPOSED_E4_WORKER_CONTROL"+purpose).encode()).hexdigest()) for purpose in HISTORY_PURPOSES)))
        config = owner.SelectedE3E4CompactConfig("config."+owner.local_node(source.root_id, "prefix"), programme,
            local, protocol, panels,
            ObjectIdentity("selection.e4-worker-control", "empirical-lawhood/matrix-scheduled-history/response-selection", "1.0.0", "b"*64), "prefix")
        design = r.SelectedE3E4Design("design.e4-worker-control", 4, D(".95"), tuple(ScheduledProgrammeFactor(name, "LINEAR", D(1), D(2), D(3))
            for name in ("temperature", "friction", "coupling")), 4)
        entry = r.SelectedE3E4EntrySeal("entry.e4-worker-control", programme, bank,
            pin("forecast-design.e4-worker-control", r.SelectedE3E4ForecastDesign), pin("evidence.e4-worker-control", r.SelectedE3E4Evidence),
            tuple(sorted((group, "group.control.1", "group.control.2", "group.control.3"))),
            tuple(sorted((local.reference.identity, *(pin("source.control."+str(index).zfill(2), old.ScheduledSource) for index in range(35))), key=lambda row: row.object_id)), design, secondary_readout=pin("secondary.disclosed-control", MatrixE4SecondaryReadoutSelection))
        case = SimpleNamespace(plane=plane, source=source, local=local, config=config, programme=programme,
            panels=panels, entry=entry, implementation=implementation_binding(Path(__file__).resolve().parents[1]))
        runner, context, contract, inputs = invoke(case, "prefix")
        ready(runner, context, contract)
        store = _store(plane, contract.expected_parent_contact, tuple(ArtifactManifest(row.logical, row.materialization) for row in inputs), prepared_invocation=contract)
        store.parent_contacts.begin(contract.expected_parent_contact)
        result = runner.execute_with_native_subwork(context, store)
        raw_outputs = {row.output_id.rsplit(".", 1)[-1]: row.payload for row in result.outputs}
        from empirical_lawhood.kernel.decoding import decode_canonical_bytes
        history = decode_canonical_bytes(raw_outputs["product"], r.SelectedE3E4PrefixHistory, maximum_bytes=None)
        record_exposure(case, "prefix", completion=history.native.completion, raw=raw_outputs["arrays"])
        prefix = science.consume_prefix(bind_selected_native_source(local, provenance), history.arrays, raw_outputs["arrays"])
        frame = np.asarray([np.kron(value, np.eye(2))/2 for value in pauli()], dtype="<c16")
        causal_values = {**prefix, "frame": frame}
        _, causal_arrays = method.array_product(source, causal_values, role="CAUSAL_STATE", artifact_id="control.causal.arrays",
            producers=(old.identity(source),))
        causal = r.SelectedE3E4CausalPrefix("causal.e4-worker-control", old.identity(source), old.identity(history),
            pin("numerical.control", r.SelectedE3E4NumericalAssessment), pin("witness.control", r.SelectedE3E4Witness),
            pin("frames.control", r.SelectedE3E4Frames), old.identity(policy), source.root.root, policy.cutoff_tick,
            sha256(frame.tobytes()).hexdigest(), "AVAILABLE", None, causal_arrays)
        feature = r.SelectedE3E4Feature("feature.e4-worker-control", old.identity(source), old.identity(causal), source.root_id,
            group, FAMILY_MAP[source.coordinate.family_id], source.coordinate.clock_id, source.coordinate.physical_time(policy.cutoff_tick),
            causal.frame_sha256, "AVAILABLE", tuple((name, D(1)) for name in FEATURES))
        original = package()
        account = r.SelectedE3E4AccountSeal("account.e4-worker-control", entry.forecast_design, old.identity(source), old.identity(causal),
            feature, original.identity, old.identity(original.calibration), tuple((name, (D(0),)*15) for name in METHODS))
        templates = {"generic_basis": np.asarray([np.kron(np.eye(2), value)/2 for value in pauli()], dtype="<c16"),
            "force_coefficients": np.stack((np.eye(3), np.eye(3))).astype("<f8")/np.sqrt(6),
            "trace_coefficients": np.ones((2, 3), dtype="<f8")/np.sqrt(6),
            "receiver_coefficients": np.eye(48, dtype="<f8").reshape(48, 2, 2, 3, 4)}
        physical_values, disposition, dispositions = response_forecast.forecast_response_arrays(protocol, causal_values, templates, disposition="AVAILABLE")
        assert disposition == "AVAILABLE"
        physical_raw, physical_arrays = response_forecast.array_product(protocol, physical_values, role="FORECAST",
            artifact_id="control.physical.arrays", producers=(old.identity(source), old.identity(causal)),
            access=Access.DEVELOPMENT_VISIBLE, visibility=Visibility.DEVELOPMENT_ONLY,
            nonfinite=tuple(name for name, value in physical_values.items() if not np.isfinite(value).all()))
        mechanical = r.SelectedE3E4MechanicalForecast("mechanical.e4-worker-control", old.identity(source), old.identity(causal),
            ObjectIdentity.from_record(protocol.protocol_id, protocol), ObjectIdentity.from_record(protocol.mechanical_model.model_id, protocol.mechanical_model),
            causal.frame_sha256, physical_arrays, disposition, dispositions)
        case.future = {"prefix": history, "prefix-arrays": raw_outputs["arrays"], "checkpoint": history.checkpoint,
            "causal": causal, "account": account, "mechanical": mechanical}
        case.physical_raw = physical_raw
        case.physical_values = physical_values
        case.prefix_store = store
        case.prefix_raw = raw_outputs
        yield case


def test_actual_e4_continue_and_response_worker_ready_has_complete_native_operands(native_case):
    for phase in ("continue", "responses"):
        runner, context, contract, _ = invoke(native_case, phase)
        try:
            ready(runner, context, contract)
            definition, = contract.native_definitions
            assert len(definition.streams) == (8 if phase == "responses" else 4)
            assert all(sum((row.logical.payload_schema, row.logical.content_sha256) == (pin.object_schema, pin.object_fingerprint)
                for row in contract.inputs) == 1 for pin in (definition.configuration, *definition.sources, *definition.streams))
            assert runner._native_array_preparation.__getstate__() == {"_prepared": None}
            with localcontext() as selected:
                selected.prec += 1
                with pytest.raises(ValueError, match="preflight array inputs"):
                    runner._native_array_preparation.arrays(context)
        finally:
            for port in context.input_ports: port.close()


@pytest.mark.parametrize("phase", ("prefix", "continue", "responses"))
def test_actual_e4_worker_stops_missing_operand_and_mutated_invocation(native_case, phase):
    runner, context, contract, _ = invoke(native_case, phase)
    try:
        ready(runner, context, contract)
        removed = next(port for port in context.input_ports if port.payload_schema == native_case.source.provenance.SCHEMA)
        missing = replace(context, prepared_invocation=None,
            input_ports=tuple(port for port in context.input_ports if port is not removed),
            input_bindings=tuple(binding for binding in context.input_bindings if binding.artifact_id != removed.artifact_id))
        stopped = lifecycle._worker_preflight(runner, missing, contract, (MATRIX_PROVENANCE_REQUIREMENT,),
            native_work_preparer=owner.prepare_native_work)
        assert not stopped.ready and any(row.operand_id == removed.artifact_id for row in stopped.mismatches)
        definition, = contract.native_definitions
        changed = replace(definition, code_sources_sha256="e"*64)
        work = replace(contract.native_work, definitions=(changed,),
            rosters=(replace(contract.native_work.rosters[0], subworks=(changed.identity,)),))
        mutated = replace(contract, native_work=work)
        stopped = lifecycle._worker_preflight(runner, replace(context, prepared_invocation=mutated), mutated,
            (MATRIX_PROVENANCE_REQUIREMENT,), native_work_preparer=owner.prepare_native_work)
        assert not stopped.ready
        assert any("selected implementation/environment" in row.reason for row in stopped.mismatches)
    finally:
        for port in context.input_ports: port.close()


@pytest.mark.parametrize("phase", ("continue", "responses"))
def test_actual_e4_worker_stops_changed_preopened_prefix_bytes(native_case, phase):
    from empirical_lawhood.runtime.execution import WorkerInputPort
    runner, context, contract, _ = invoke(native_case, phase)
    try:
        ready(runner, context, contract)
        original = next(port for port in context.input_ports if port.artifact_id.endswith(".prefix-arrays"))
        raw = native_case.future["prefix-arrays"]
        changed = WorkerInputPort(original.binding, MemoryReader(raw[:-1]+bytes((raw[-1] ^ 1,))))
        context = replace(context, prepared_invocation=None,
            input_ports=tuple(changed if port is original else port for port in context.input_ports))
        stopped = lifecycle._worker_preflight(runner, context, contract, (MATRIX_PROVENANCE_REQUIREMENT,),
            native_work_preparer=owner.prepare_native_work)
        assert not stopped.ready
        assert any(row.operand_id == original.artifact_id for row in stopped.mismatches)
        original.close()
    finally:
        for port in context.input_ports: port.close()


@pytest.mark.parametrize("damage", ("shape", "missing", "dtype", "nonfinite", "nonhermitian", "receiver"))
def test_actual_e4_response_worker_stops_bad_frozen_instrument_before_ready(native_case, damage):
    case = native_case
    values = {name: value.copy() for name, value in case.physical_values.items()}
    if damage == "shape": values["forces"] = values["forces"][:1]
    elif damage == "missing": del values["forces"]
    elif damage == "dtype": values["forces"] = values["forces"].real.copy()
    elif damage == "nonfinite": values["forces"][0, 0, 0, 0, 0] = np.nan
    elif damage == "nonhermitian": values["forces"][0, 0, 0, 0, 0] += 1j
    else: values["receivers"] = values["receivers"][:1]
    raw, members = encode_matrix_arrays(values, nonfinite_members=tuple(name for name, value in values.items() if not np.isfinite(value).all()))
    physical = case.future["mechanical"]
    artifact = replace(physical.arrays.array_artifact, sha256=sha256(raw).hexdigest(), size_bytes=len(raw))
    arrays = replace(physical.arrays, array_artifact=artifact, members=members)
    runner, context, contract, _ = invoke(case, "responses", {"mechanical": replace(physical, arrays=arrays), "mechanical-arrays": raw}, suffix=damage)
    try:
        result = lifecycle._worker_preflight(runner, context, contract, (MATRIX_PROVENANCE_REQUIREMENT,),
            native_work_preparer=owner.prepare_native_work)
        assert not result.ready
        assert any("force census" in row.reason or "receiver" in row.reason for row in result.mismatches)
        with pytest.raises(ValueError, match="preflight array inputs"):
            runner._native_array_preparation.arrays(context)
    finally:
        for port in context.input_ports: port.close()


def test_continuation_reuses_preflight_prefix_and_matches_original_archive(native_case, monkeypatch):
    from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_history_segments as segments
    case = native_case
    history = case.future["prefix"]
    prefix = science.consume_prefix(case.source, history.arrays, case.future["prefix-arrays"])
    terminal = {view+"_"+component: prefix[view+"_"+component][-1] for view in ("primary", "fine") for component in ("positions", "momenta")}
    segment = segments.acquire_parameter_segment(case.source.coordinate, case.source.root.streams,
        case.source.policy.cutoff_tick, case.source.coordinate.total_ticks,
        terminal=terminal, generator_states=history.checkpoint.generators)
    expected, operand = science.full_from_continuation(case.source, history, case.future["prefix-arrays"], segment, artifact_id="control.full")
    record_exposure(case, "continue", raw=expected)
    def forbidden(*args, **kwargs): pytest.fail("validated continuation expanded an archive again")
    monkeypatch.setattr(science, "consume_prefix", forbidden)
    monkeypatch.setattr(science, "decode_matrix_arrays", forbidden)
    actual, selected = science.full_from_continuation(case.source, history, case.future["prefix-arrays"], segment,
        artifact_id="control.full", prefix_values=prefix)
    assert actual == expected and selected == operand
    changed = dict(prefix)
    changed["primary_positions"] = prefix["primary_positions"].copy()
    changed["primary_positions"][0, 0, 0, 0, 0] += 1
    with pytest.raises(ValueError, match="exact preflight prefix"):
        science.full_from_continuation(case.source, history, case.future["prefix-arrays"], segment,
            artifact_id="control.full", prefix_values=changed)


def test_actual_e4_continuation_return_and_recovery_preserve_bytes_without_expansion(native_case, monkeypatch):
    from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_history_segments as segments
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    case = native_case
    runner, context, contract, inputs = invoke(case, "continue")
    ready(runner, context, contract)
    store = _store(case.plane, contract.expected_parent_contact,
        tuple(ArtifactManifest(row.logical, row.materialization) for row in inputs), prepared_invocation=contract)
    store.parent_contacts.begin(contract.expected_parent_contact)
    original_decoder = science.decode_matrix_arrays
    def forbidden(*args, **kwargs): pytest.fail("fresh native continuation expanded a preflight/archive return again")
    monkeypatch.setattr(science, "decode_matrix_arrays", forbidden)
    first = runner.execute_with_native_subwork(context, store)
    first_raw = {row.output_id.rsplit(".", 1)[-1]: row.payload for row in first.outputs}
    product = decode_canonical_bytes(first_raw["product"], r.SelectedE3E4FullHistory, maximum_bytes=None)
    record_exposure(case, "continue", completion=product.native.completion, raw=first_raw["arrays"])
    monkeypatch.setattr(science, "decode_matrix_arrays", original_decoder)
    runner, context, contract, _ = invoke(case, "continue")
    ready(runner, context, contract)
    decoded = []
    unpack = science.unpack_native
    def one_decode(*args, **kwargs):
        decoded.append(True)
        return unpack(*args, **kwargs)
    monkeypatch.setattr(science, "unpack_native", one_decode)
    monkeypatch.setattr(segments, "acquire_parameter_segment", forbidden)
    recovered = runner.execute_with_native_subwork(context, store)
    assert {row.output_id.rsplit(".", 1)[-1]: row.payload for row in recovered.outputs} == first_raw
    assert len(decoded) == 1


def test_actual_e4_prefix_recovery_rebinds_original_bytes_after_one_decode(native_case, monkeypatch):
    from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_history_segments as segments
    case = native_case
    runner, context, contract, _ = invoke(case, "prefix")
    ready(runner, context, contract)
    decoded = []
    unpack = science.unpack_native
    def one_decode(*args, **kwargs):
        decoded.append(True)
        return unpack(*args, **kwargs)
    def forbidden(*args, **kwargs): pytest.fail("prefix recovery reacquired or expanded the same archive again")
    monkeypatch.setattr(science, "unpack_native", one_decode)
    monkeypatch.setattr(method, "decode_matrix_arrays", forbidden)
    monkeypatch.setattr(segments, "acquire_parameter_segment", forbidden)
    recovered = runner.execute_with_native_subwork(context, case.prefix_store)
    assert {row.output_id.rsplit(".", 1)[-1]: row.payload for row in recovered.outputs} == case.prefix_raw
    assert len(decoded) == 1


def test_prefix_local_carrier_rebinding_checks_exact_archive_members_source_and_checkpoint(scheduled, monkeypatch):  # noqa: F811
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import parameter_native
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_records as protected
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_science as protected_method
    from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_history_segments as segments
    _, sources = scheduled
    source = sources[0]
    segment = segments.acquire_parameter_segment(source.coordinate, source.root.streams, 0, source.policy.cutoff_tick)
    raw, operand, checkpoint, arrays = science.prefix_from_segment(source, segment,
        artifact_id="control.prefix.local", return_values=True)
    record_exposure(SimpleNamespace(source=source, panels=()), "prefix", raw=raw)
    returned = parameter_native.ParameterNativeReturn(raw, arrays, checkpoint, None, None, operand)
    expected = method.array_product(source, arrays, role="PREFIX", artifact_id="control.prefix.outer",
        producers=operand.producers, raw=raw)[1]
    expected_protected = protected_method.array_product(source, arrays, role="PREFIX", artifact_id="control.prefix.outer",
        producers=operand.producers, raw=raw)[1]
    recovered_operand = parameter_native._recovered_prefix_operand(source, raw, arrays, checkpoint)
    assert recovered_operand == operand
    def forbidden(*args, **kwargs): pytest.fail("local prefix rebinding expanded an archive again")
    monkeypatch.setattr(science, "decode_matrix_arrays", forbidden)
    monkeypatch.setattr(method, "decode_matrix_arrays", forbidden)
    monkeypatch.setattr(protected_method, "decode_matrix_arrays", forbidden)
    scope = {"record_type": r.SelectedE3E4Arrays, "artifact_id": "control.prefix.outer",
        "artifact_role": "selected-e4-exposed-prefix", "access": r.DEV, "visibility": r.EXPOSED}
    assert returned.rebind_prefix(source, **scope) == expected
    assert replace(returned, array_product=recovered_operand).rebind_prefix(source, **scope) == expected
    assert returned.rebind_prefix(source, **{**scope, "record_type": protected.SelectedE4ProtectedArrays,
        "artifact_role": "selected-e4-protected-prefix", "access": protected.BLIND,
        "visibility": protected.PROSPECTIVE}) == expected_protected
    with pytest.raises(ValueError, match="exact local archive"):
        replace(returned, raw=raw[:-1]+bytes((raw[-1] ^ 1,))).rebind_prefix(source, **scope)
    changed = dict(arrays)
    changed["primary_positions"] = arrays["primary_positions"].copy()
    changed["primary_positions"][1, 0, 0, 0, 0] += 1
    with pytest.raises(ValueError, match="exact local archive"):
        replace(returned, arrays=changed).rebind_prefix(source, **scope)
    with pytest.raises(ValueError, match="source"):
        returned.rebind_prefix(sources[1], **scope)
    with pytest.raises(ValueError, match="checkpoint"):
        replace(returned, checkpoint=replace(checkpoint, cutoff_tick=checkpoint.cutoff_tick+1)).rebind_prefix(source, **scope)
