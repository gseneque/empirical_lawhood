"""Focused all-family compiler and exposed no-native worker controls.

Synthetic provenance and progress ports below are explicitly disclosed test
fixtures, not evidence of native execution, actual runtime pins or custody.
"""

from dataclasses import replace
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from empirical_lawhood.api.joint_description import new_recipe, specification_from_recipe
from empirical_lawhood.adapters.joint_description import bindings, experiment
from empirical_lawhood.adapters.joint_description.records import PHASES, config_for
from empirical_lawhood.adapters.joint_description import lowering as workflow
from empirical_lawhood.design.joint_description import SelectedInputs
from empirical_lawhood.execution.capabilities import CapabilityRegistry
from empirical_lawhood.execution.experiment_preparation import ExecutionSelection
from empirical_lawhood.execution.recursive_compiler import compile_recursive_wave
from empirical_lawhood.science.identity.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.joint_description import FAMILIES
from empirical_lawhood.science.models.worlds import WorldKind
from empirical_lawhood.science.records.serialization import canonical_json_bytes


def operands(family="R01", *, tiny=False, device="cpu", raw=None):
    recipe = new_recipe(family)
    if tiny:
        recipe["calibration_unit_ids"] = recipe["calibration_unit_ids"][:2]
        recipe["evaluation_unit_ids"] = recipe["evaluation_unit_ids"][:2]
        recipe["actions"] = recipe["actions"][:2]
        recipe["horizons"] = recipe["horizons"][:1]
    spec = specification_from_recipe(recipe)
    selected = SelectedInputs("fixture.selected." + family.lower(), spec.identity, device, raw,
                              None if raw is None else sha256(raw.encode()).hexdigest())
    sources = (("src/disclosed-no-native-fixture.py", "a" * 64),)
    provenance = NumericalProducingProvenance(
        json.dumps({"python": "fixture", "numpy": "fixture", "scipy": "fixture",
                    "system": "fixture", "machine": "fixture", "threadpools": []}),
        "b" * 64, sources, sha256(canonical_json_bytes(sources)).hexdigest(), "c" * 40, True,
    )
    return spec, selected, provenance


def compiler_inputs():
    declarations = bindings.operation_declarations()
    return dict(
        registry=CapabilityRegistry("fixture.joint.registry", tuple(d.manifest() for d in declarations)),
        registrations=tuple(d.registration() for d in declarations), implementation_commit="c" * 40,
        output_codecs={key: value for declaration in declarations for key, value in declaration.record_codecs.items()},
    )


@pytest.mark.parametrize("family", FAMILIES)
def test_every_public_recipe_lowers_and_compiles_its_actual_six_phase_graph(family):
    spec, selected, provenance = operands(family)
    draft, external = workflow.lower(spec, selected, provenance)
    compiled = compile_recursive_wave(draft=draft, **compiler_inputs())
    tasks = {task.task_id.rsplit(".", 1)[-1]: task for task in compiled.execution_plan.tasks}
    assert set(tasks) == set(PHASES)
    assert len(external) == 2
    assert len(draft.requirements) == len(draft.connections) == 9
    assert set(draft.development_study.assigned_unit_ids) == set(spec.all_unit_ids)
    assert tasks["prepare"].dependency_task_ids == (tasks["fit"].task_id,)
    assert set(tasks["evaluate"].dependency_task_ids) == {tasks["forecast"].task_id, tasks["prepare"].task_id}
    assert set(tasks["assess"].dependency_task_ids) == {tasks[p].task_id for p in ("evaluate", "fit", "forecast")}
    if family in ("R17", "R18", "R19", "R20", "R21", "R22"):
        assert draft.development_study.world_kind is WorldKind.NUMERICAL_SIMULATOR


@pytest.mark.parametrize("removed", ["forecast", "predictors"])
def test_compiler_refuses_removing_the_evaluation_forecast_or_predictor_barrier(removed):
    spec, selected, provenance = operands(tiny=True)
    draft, _ = workflow.lower(spec, selected, provenance)
    victim = next(link for link in draft.links if link.consumer_node_id.endswith(".evaluate")
                  and link.consumer_input_id == removed)
    with pytest.raises(ValueError):
        compile_recursive_wave(draft=replace(draft, links=tuple(link for link in draft.links if link != victim)),
                               **compiler_inputs())


def test_preparation_reports_missing_raw_input_and_rejects_graph_substitution(tmp_path):
    spec, selected, provenance = operands("R13", tiny=True)
    bound = experiment.bind_inputs(spec, {"selected": selected, "provenance": provenance})
    missing = experiment.prepare(spec, scientific_inputs=bound.scientific_inputs,
                                 method_inputs=bound.method_inputs, execution=ExecutionSelection())
    assert missing.draft is None
    assert any(dependency.code == "joint-description.input.raw-cohort" for dependency in missing.dependencies)
    spec, selected, provenance = operands("R01", tiny=True)
    bound = experiment.bind_inputs(spec, {"selected": selected, "provenance": provenance})
    ready = experiment.prepare(spec, scientific_inputs=bound.scientific_inputs,
        method_inputs=bound.method_inputs, execution=ExecutionSelection(
            workers=1, environment_id="fixture.environment", output_root=str(tmp_path),
            source_snapshot=ObjectIdentity("fixture.source", "empirical-lawhood/testing/source", "1.0.0", "a"*64)))
    assert ready.executable
    experiment.validate_instance(specification=spec, allocation=ready.allocation,
                                 draft=ready.draft, source_records=ready.design_records)
    with pytest.raises(ValueError, match="graph"):
        experiment.validate_instance(specification=spec, allocation=ready.allocation,
                                     draft=replace(ready.draft, question="substituted question"),
                                     source_records=ready.design_records)


@pytest.mark.parametrize(("defect", "error"), (
    (None, None), ("missing-unit", "absent"), ("wrong-split", "cross"),
    ("negative-temperature", "initial_temperature_k must be positive"),
))
def test_preparation_checks_entire_physical_roster_before_lowering(tmp_path, monkeypatch, defect, error):
    from empirical_lawhood.adapters.physical import joint_description as physical

    spec, _, _ = operands("R15", tiny=True)
    units = [
        {"unit_id": unit_id, "split": split, "preparation_time_s": -1,
         "preparation": {"initial_soc": 0.5, "initial_temperature_k": 296, "history_current_a": 0},
         "episodes": [{"action": 1, "status": "failed", "reason": "sensor dropout", "data": None}]}
        for split, roster in (("calibration", spec.calibration_unit_ids), ("evaluation", spec.evaluation_unit_ids))
        for unit_id in roster
    ]
    if defect == "missing-unit":
        units.pop()
    elif defect == "wrong-split":
        units[-1]["split"] = "calibration"
    elif defect == "negative-temperature":
        units[-1]["preparation"]["initial_temperature_k"] = -3820.777
    # A larger physical source may supply unselected units, and raw signed
    # outcome data stays with the acquisition operation that owns its reduction.
    units.append({**units[0], "unit_id": "unit.unselected",
                  "episodes": [{"action": 1, "status": "complete", "reason": "", "data": {"opaque": True}}]})
    raw = json.dumps({"schema": physical.SCHEMA, "family_id": "R15", "source_id": "fixture.raw",
                      "exposure": "recorded-archive", "action_unit": "A", "receiver_unit": "V;A.h", "units": units})
    spec, selected, provenance = operands("R15", tiny=True, raw=raw)
    bound = experiment.bind_inputs(spec, {"selected": selected, "provenance": provenance})
    execution = ExecutionSelection(workers=1, environment_id="fixture.environment", output_root=str(tmp_path),
        source_snapshot=ObjectIdentity("fixture.source", "empirical-lawhood/testing/source", "1.0.0", "a" * 64))
    decode = physical.decode_cohort
    reads = []
    def tracked(payload, family):
        reads.append(family)
        return decode(payload, family)
    monkeypatch.setattr(physical, "decode_cohort", tracked)
    monkeypatch.setattr(physical, "_reduce", lambda *args: pytest.fail("preparation reduced a receiver"))
    args = dict(scientific_inputs=bound.scientific_inputs, method_inputs=bound.method_inputs, execution=execution)
    if error:
        monkeypatch.setattr(experiment, "lower", lambda *args: pytest.fail("invalid cohort reached lowering"))
        with pytest.raises(ValueError, match=error):
            experiment.prepare(spec, **args)
    else:
        assert experiment.prepare(spec, **args).executable
    assert reads == ["R15"]


def test_native_gpu_selection_is_a_config_choice_only_for_implemented_families():
    for family in ("R17", "R22"):
        spec, selected, provenance = operands(family, tiny=True, device="gpu")
        draft, _ = workflow.lower(spec, selected, provenance)
        compiled = compile_recursive_wave(draft=draft, **compiler_inputs())
        for task in compiled.execution_plan.tasks:
            native = task.task_id.endswith((".calibrate", ".prepare", ".evaluate"))
            assert task.capability.requested_resources.gpu_devices == int(native)
    spec, selected, provenance = operands("R20", tiny=True, device="gpu")
    with pytest.raises(ValueError, match="GPU"):
        config_for(spec, selected, provenance, "prepare")


def test_reauthoring_rc_dimensions_refuses_stale_channels_and_cheap_work_budget():
    recipe = new_recipe("R02")
    recipe["parameters"]["n_cells"] = 16
    for description in recipe["descriptions"]:
        description["forecast_work_units"] = 10**9
    spec = specification_from_recipe(recipe)
    with pytest.raises(ValueError, match="counts"):
        experiment.bind_inputs(spec, {})
    recipe = new_recipe("R01")
    recipe["descriptions"][0]["forecast_work_units"] = 1
    spec = specification_from_recipe(recipe)
    with pytest.raises(ValueError, match="budget"):
        experiment.bind_inputs(spec, {})
    recipe = new_recipe("R01")
    recipe["parameters"]["unimplemented_history"] = 5
    with pytest.raises(ValueError, match="unimplemented"):
        experiment.bind_inputs(specification_from_recipe(recipe), {})


class _ReadPort:
    """Exposed byte/lifetime double for the ordinary typed worker input port."""

    def __init__(self, value):
        self.payload_schema = value.SCHEMA
        self.media_type = "application/json"
        self.raw = value.canonical_bytes()
        self.decode_bounds = []
        self.closed = False

    def decode_canonical_record(self, record_type, *, maximum_bytes):
        from empirical_lawhood.science.records.decoding import decode_canonical_bytes

        assert not self.closed
        self.decode_bounds.append(maximum_bytes)
        return decode_canonical_bytes(self.raw, record_type, maximum_bytes=maximum_bytes)

    def close(self):
        self.closed = True


class _Progress:
    """Explicit in-memory protocol double; it cannot certify real custody."""

    def __init__(self, parent):
        self.parent_contact = parent
        self.completed = {}
        self.payloads = {}
        self.events = []
        self.contacted = set()

    def freeze_roster(self, roster, *, definitions):
        assert roster.parent_contact == self.parent_contact
        assert roster.subworks == tuple(value.identity for value in definitions)
        self.events.append(("roster", len(definitions)))

    def recover(self, definition):
        if definition.subwork_id in self.contacted and definition.subwork_id not in self.completed:
            from empirical_lawhood.execution.native_subwork import NativeSubworkUncertainContact
            raise NativeSubworkUncertainContact("fixture uncertain contact must not be repeated")
        self.events.append(("recover", definition.subwork_id))
        return self.completed.get(definition.subwork_id)

    def begin(self, definition):
        self.events.append(("begin", definition.subwork_id))
        return SimpleNamespace(definition=definition)

    def contact(self, entry):
        self.contacted.add(entry.definition.subwork_id)
        self.events.append(("contact", entry.definition.subwork_id))

    def publish_output(self, entry, output_id, chunks, **constraints):
        assert entry.definition.subwork_id in self.contacted
        raw = b"".join(chunks)
        assert len(raw) == constraints["expected_size_bytes"]
        assert sha256(raw).hexdigest() == constraints["expected_physical_sha256"]
        self.payloads[entry.definition.subwork_id, output_id] = raw
        self.events.append(("publish", entry.definition.subwork_id))

    def complete(self, entry, *, operational_status, **_kwargs):
        from empirical_lawhood.science.records.status import OperationalStatus
        self.events.append((operational_status.value, entry.definition.subwork_id))
        if operational_status is OperationalStatus.SUCCEEDED:
            self.completed[entry.definition.subwork_id] = SimpleNamespace(receipt="explicit-fixture-receipt")

    def iter_completed_output(self, definition, output_id):
        assert definition.subwork_id in self.completed
        yield self.payloads[definition.subwork_id, output_id]


def _fixture_trials(request, *, predictors_only=False):
    from empirical_lawhood.science.joint_description import TrialBatch, TrialRow
    fields = ("independent_prediction", "interface_prediction", "joint_prediction", "memory_prediction", "partition_prediction")
    rows = tuple(TrialRow(unit, action, horizon, receiver,
                         tuple((key, 0.5) for key in fields), None if predictors_only else 0.5,
                         "unsupported" if predictors_only else "supported", "not-yet-acquired" if predictors_only else "")
                 for unit in request.unit_ids for action in request.actions for horizon in request.horizons
                 for receiver in request.parameters["receivers"])
    return TrialBatch(request.family_id, request.split, rows, "explicit-no-native-software-fixture")


def _worker_context(spec, selected, provenance, phase, inputs):
    from empirical_lawhood.adapters.joint_description import runner
    from empirical_lawhood.execution.native_effects import NativeEffectContact
    from empirical_lawhood.execution.native_subwork import NativeSubworkRoster
    from empirical_lawhood.execution.prepared_native_invocation import PreparedNativeWork
    from empirical_lawhood.adapters.joint_description.records import effect_slots, units

    config = config_for(spec, selected, provenance, phase)
    declaration = next(value for value in bindings.operation_declarations()
                       if value.capability_key == "joint-description." + phase + ".cpu")
    manifest = declaration.manifest()
    values = {"selected": selected, "provenance": provenance, **inputs}
    values = {name: values[name] for name, _kind in runner.INPUTS[phase]}
    output_name, _kind = runner.OUTPUTS[phase]
    materializations = tuple(sorted("fixture.materialization." + name for name in ("config", *values)))
    parent = NativeEffectContact("fixture.run", config.node_id, "fixture.attempt",
        ObjectIdentity("fixture.plan", "empirical-lawhood/testing/plan", "1.0.0", "e"*64),
        ObjectIdentity(config.node_id, "empirical-lawhood/testing/task", "1.0.0", "f"*64),
        provenance.observed_git_head, materializations, ())
    context = SimpleNamespace(
        accelerated_compute=selected.device == "gpu",
        task_id=config.node_id,
        config=SimpleNamespace(config_id=config.config_id, content_sha256=config.fingerprint()),
        resource_budget=workflow.budget(phase, "cpu"), permissions=manifest.permissions,
        outcome_access=workflow.ACCESS,
        input_ports=tuple(_ReadPort(value) for value in (config, *values.values())),
        output_ports=(SimpleNamespace(output_id=config.node_id + "." + output_name),),
        input_materialization_ids=materializations, prepared_invocation=None,
    )
    definitions = runner.definitions(config, values, context, parent)
    prepared = PreparedNativeWork(parent, units(config), effect_slots(config), definitions,
                                 (NativeSubworkRoster("selected.native-subwork", parent,
                                                      tuple(value.identity for value in definitions)),))
    context.prepared_invocation = SimpleNamespace(
        expected_parent_contact=parent, native_work=prepared,
        implementation=SimpleNamespace(package_sources=provenance.package_sources,
            code_sources_sha256=provenance.code_sources_sha256,
            dependency_lock_sha256=provenance.dependency_lock_sha256),
        validate_context=lambda observed: None if observed is context else pytest.fail("contract context substituted"),
    )
    return context, runner.NativeRunner(manifest=manifest), parent


def test_worker_refuses_invocation_device_mismatch_before_native_contact():
    spec, selected, provenance = operands(tiny=True)
    context, worker, _ = _worker_context(spec, selected, provenance, "calibrate", {})
    context.accelerated_compute = True
    with pytest.raises(ValueError, match="invocation acceleration"):
        worker.preflight(context)


def _causal_records(spec, selected, provenance):
    from empirical_lawhood.science.joint_description import Calibration, TrialRequest, split_batch
    from empirical_lawhood.methods.joint_description import fit_response_laws, forecast_and_choose
    parameters = {"receivers": tuple(row.receiver_id for row in spec.receivers)}
    request = TrialRequest(spec.family_id, spec.seed, spec.calibration_unit_ids, "calibration",
        tuple(float(v) for v in spec.actions), tuple(float(v) for v in spec.horizons), parameters)
    calibration_prefix = config_for(spec, selected, provenance, "calibrate").node_id
    predictors, outcomes = split_batch(_fixture_trials(request), spec.identity, calibration_prefix)
    calibration = Calibration(calibration_prefix + ".calibration", spec.identity, predictors, outcomes)
    model = fit_response_laws(spec, calibration,
        record_id=config_for(spec, selected, provenance, "fit").node_id + ".model")
    evaluation = replace(request, unit_ids=spec.evaluation_unit_ids, split="evaluation")
    predictors, _ = split_batch(_fixture_trials(evaluation, predictors_only=True), spec.identity,
                                config_for(spec, selected, provenance, "prepare").node_id)
    forecast = forecast_and_choose(spec, model, predictors,
        record_id=config_for(spec, selected, provenance, "forecast").node_id + ".forecast")
    return model, predictors, forecast


@pytest.mark.parametrize("phase", ("calibrate", "prepare", "evaluate"))
def test_worker_split_census_contact_before_calculation_and_receipt_recovery(phase, monkeypatch):
    from empirical_lawhood.adapters.joint_description import runner
    from empirical_lawhood.domains import joint_description_catalogue
    from empirical_lawhood.science.records.decoding import decode_canonical_bytes
    from empirical_lawhood.science.joint_description import MAX_BYTES, MAX_COHORT_BYTES

    spec, selected, provenance = operands(tiny=True)
    model, predictors, forecast = _causal_records(spec, selected, provenance)
    inputs = {"model": model, "predictors": predictors, "forecast": forecast}
    context, worker, parent = _worker_context(spec, selected, provenance, phase, inputs)
    progress = _Progress(parent)
    calls = []

    def acquire(request, *, native_port=None):
        assert "unit." + request.unit_ids[0] in progress.contacted
        calls.append((phase, request.split, request.unit_ids))
        return _fixture_trials(request, predictors_only=phase == "prepare")

    owner = SimpleNamespace(produce=acquire, prepare_predictors=acquire)
    monkeypatch.setattr(joint_description_catalogue, "family_module", lambda _family: owner)
    monkeypatch.setattr(runner, "native_port", lambda _family: None)
    from collections import defaultdict

    chunk_bytes = 1024
    monkeypatch.setattr(runner, "STREAM_CHUNK_BYTES", chunk_bytes)
    outputs = defaultdict(list)

    def write(key, chunk):
        assert 0 < len(chunk) <= chunk_bytes
        outputs[key].append(chunk)

    emitter = SimpleNamespace(write=write)
    worker.preflight(context)
    checks = worker.execute_streaming_with_native_subwork(context, progress, emitter)
    assert all(check.passed for check in checks)
    assert all(port.closed for port in context.input_ports)
    expected = spec.calibration_unit_ids if phase == "calibrate" else spec.evaluation_unit_ids
    assert [call[2][0] for call in calls] == list(expected)
    assert all(call[1] == ("calibration" if phase == "calibrate" else "evaluation") for call in calls)
    _name, kind = runner.OUTPUTS[phase]
    chunks, = outputs.values()
    assert len(chunks) > 1
    product = decode_canonical_bytes(b"".join(chunks), kind, maximum_bytes=MAX_BYTES)
    assert product.specification == spec.identity
    assert context.resource_budget.output_bytes == 2 * MAX_COHORT_BYTES
    assert workflow.budget("fit", "cpu").output_bytes == MAX_BYTES
    for port in context.input_ports:
        bound = MAX_COHORT_BYTES if port.payload_schema == runner.Predictors.SCHEMA else MAX_BYTES
        assert set(port.decode_bounds) == {bound}
    # New input-port lifetimes, same original source/effect identity. Recovery
    # must return original output bytes without re-entering a substrate.
    recovered_context, recovered_worker, recovered_parent = _worker_context(spec, selected, provenance, phase, inputs)
    assert recovered_parent == parent
    recovered = defaultdict(list)
    recovered_worker.execute_streaming_with_native_subwork(recovered_context, progress,
        SimpleNamespace(write=lambda key, raw: recovered[key].append(raw)))
    assert recovered == outputs
    assert len(calls) == len(expected)
    assert all(port.closed for port in recovered_context.input_ports)
    if phase == "calibrate":
        size = sum(map(len, chunks))
        # The population can exceed an individual root's limit. The same
        # original returns must publish at the exact cohort bound on recovery.
        largest_root = max(map(len, progress.payloads.values()))
        assert largest_root < size
        monkeypatch.setattr(runner, "MAX_COHORT_BYTES", size)
        retry, retry_worker, _ = _worker_context(spec, selected, provenance, phase, inputs)
        at_limit = defaultdict(list)
        retry_worker.execute_streaming_with_native_subwork(retry, progress,
            SimpleNamespace(write=lambda key, raw: at_limit[key].append(raw)))
        assert at_limit == outputs
        monkeypatch.setattr(runner, "MAX_COHORT_BYTES", size - 1)
        refused, refused_worker, _ = _worker_context(spec, selected, provenance, phase, inputs)
        with pytest.raises(ValueError, match="cohort product exceeds"):
            refused_worker.execute_streaming_with_native_subwork(refused, progress,
                SimpleNamespace(write=lambda *_: pytest.fail("oversized cohort reached publication")))
        assert len(calls) == len(expected)


def test_worker_refuses_changed_evaluation_predictor_and_does_not_retry_contact(monkeypatch):
    from empirical_lawhood.adapters.joint_description import runner
    from empirical_lawhood.domains import joint_description_catalogue
    from empirical_lawhood.execution.native_subwork import NativeSubworkUncertainContact

    spec, selected, provenance = operands(tiny=True)
    model, predictors, forecast = _causal_records(spec, selected, provenance)
    inputs = {"model": model, "predictors": predictors, "forecast": forecast}
    context, worker, parent = _worker_context(spec, selected, provenance, "evaluate", inputs)
    progress = _Progress(parent)
    calls = []

    def changed(request, **_kwargs):
        calls.append(request.unit_ids)
        batch = _fixture_trials(request)
        return replace(batch, rows=tuple(replace(row, features=tuple((key, value + 1) for key, value in row.features))
                                        for row in batch.rows))

    monkeypatch.setattr(joint_description_catalogue, "family_module", lambda _family: SimpleNamespace(produce=changed))
    monkeypatch.setattr(runner, "native_port", lambda _family: None)
    emitter = SimpleNamespace(write=lambda *_args: pytest.fail("changed predictor emitted a product"))
    with pytest.raises(ValueError, match="predictor"):
        worker.execute_streaming_with_native_subwork(context, progress, emitter)
    assert all(port.closed for port in context.input_ports)
    assert len(calls) == 1
    retry_context, retry_worker, _ = _worker_context(spec, selected, provenance, "evaluate", inputs)
    with pytest.raises(NativeSubworkUncertainContact):
        retry_worker.execute_streaming_with_native_subwork(retry_context, progress, emitter)
    assert len(calls) == 1
    assert all(port.closed for port in retry_context.input_ports)


@pytest.mark.parametrize("substitution", ("manifest", "model-id", "forecast-parent"))
def test_worker_rejects_same_specification_predecessor_or_capability_substitution(substitution):
    spec, selected, provenance = operands(tiny=True)
    model, predictors, forecast = _causal_records(spec, selected, provenance)
    phase = "evaluate" if substitution == "forecast-parent" else "prepare"
    if substitution == "model-id":
        model = replace(model, record_id="fixture.forged-same-spec-model")
    if substitution == "forecast-parent":
        forecast = replace(forecast, predictors=replace(forecast.predictors, object_id="fixture.forged-predictors"))
    context, worker, parent = _worker_context(spec, selected, provenance, phase,
                                             {"model": model, "predictors": predictors, "forecast": forecast})
    if substitution == "manifest":
        worker.manifest = next(value.manifest() for value in bindings.operation_declarations()
                               if value.capability_key == "joint-description.calibrate.cpu")
    progress = _Progress(parent)
    emitter = SimpleNamespace(write=lambda *_: pytest.fail("substituted predecessor emitted a product"))
    with pytest.raises(ValueError, match="manifest|predecessor"):
        worker.execute_streaming_with_native_subwork(context, progress, emitter)
    assert not progress.contacted
    assert all(port.closed for port in context.input_ports)


def test_cold_new_owner_and_main_registry_discovery_do_not_contact_native_engines():
    root = Path(__file__).resolve().parents[1]
    script = '''import importlib.abc, sys, subprocess, socket
forbidden = {'numpy','scipy','brian2','pyscf','openmm','jax','pybamm','torax'}
class Guard(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in forbidden:
            raise RuntimeError('native initialization during static discovery: ' + fullname)
sys.meta_path.insert(0, Guard())
def refuse(*args, **kwargs):
    raise RuntimeError('process or network contact during static discovery')
subprocess.Popen = refuse
socket.create_connection = refuse
from empirical_lawhood.api.workflows import show_workflow
assert show_workflow('joint-description-experiments').workflow_id == 'joint-description-experiments'
from empirical_lawhood.adapters.joint_description.extension import EXTENSION
assert EXTENSION.discovery is not None
# Existing global protocol owners import base NumPy/SciPy through storage.
# The new extension above remains free of both imports. Global discovery still
# must not initialize an optional substrate or contact a process/network.
forbidden -= {'numpy','scipy'}
from empirical_lawhood.api.experiment_preparation import experiment_protocols
assert any(protocol.protocol_id == 'joint-description.development' for protocol in experiment_protocols())
'''
    result = subprocess.run([sys.executable, "-B", "-c", script], cwd=root, capture_output=True,
        env={**os.environ, "PYTHONPATH": str(root / "src"), "PYTHONDONTWRITEBYTECODE": "1"}, timeout=30)
    assert result.returncode == 0, result.stderr.decode()
