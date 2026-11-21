# SPDX-License-Identifier: MPL-2.0
"""Bounded exposed contract checks; installed recovery is separate acceptance."""

from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.isolated_native_starter import bindings, design, experiment, native_entry, runner
from empirical_lawhood.adapters.isolated_native_starter.records import MAX_CONTROL_BYTES, MAX_LOG_BYTES, MAX_RESULT_BYTES, UNIT, ProcessLog, SquareInput, SquareNativeResult, SquareResult, SquareSpecification, WorkerSelection
from empirical_lawhood.adapters.isolated_native_starter.work import definitions_for, invocation_bytes
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.identity.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import canonical_json_bytes
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.execution.capabilities import CapabilityRegistry
from empirical_lawhood.storage.contracts.artifacts import ExternalRootContract
from empirical_lawhood.execution.experiment_preparation import ExecutionSelection
from empirical_lawhood.execution.native_effects import NativeEffectContact
from empirical_lawhood.execution.recursive_compiler import compile_recursive_wave


def operands(last_integer=64):
    """Explicit software operands; source placeholders supply no execution proof."""
    sources = (("disclosed-software-fixture.py", "a" * 64),)
    provenance = NumericalProducingProvenance(canonical_json_bytes({"python": "3.11.14", "numpy": "2.4.6",
        "scipy": "1.17.1", "system": "linux", "machine": "x86_64", "threadpools": ()}).decode(),
        "b" * 64, sources, sha256(canonical_json_bytes(sources)).hexdigest(), "c" * 40, False)
    environment = tuple(sorted({"PYTHONDONTWRITEBYTECODE": "1", **{name: "1" for name in (
        "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS")}}.items()))
    scratch_contract = ExternalRootContract("exposed.scratch", "Exposed scratch declaration only", "/selected/scratch",
        "/selected", "empirical-lawhood/runtime/operator-storage-profile", 1024**2, None, None, ("ext4",))
    worker = WorkerSelection("/selected/bin/python", "d" * 64, "2.4.6", "/selected/source", "/selected/package",
        "/selected/scratch/new-case", scratch_contract, environment)
    operand = SquareInput("exposed.integer-sequence", last_integer)
    spec = SquareSpecification("exposed.isolated.specification", operand.identity, provenance.identity, worker)
    return operand, provenance, spec, design.config_for(spec)


@pytest.mark.parametrize("last,expected", ((0, 0), (64, 89440), (1024, 358438400)))
@pytest.mark.numerical(oracle='Exact sum-of-squares integers 0, 89440, 358438400 and independently implemented n(n+1)(2n+1)/6')
def test_bounded_numpy_calculation_matches_independently_derived_integer_oracle(last, expected):
    operand, _, _, config = operands(last)
    value, version, cpu, wall = native_entry.calculate(operand)
    assert value == expected == runner.independent_sum(last)
    assert version == "2.4.6" and cpu >= 0 and wall >= 0
    product = SquareNativeResult(config.node_id + ".native", config.identity, operand.identity,
        last, value, version, cpu, wall, 1024)
    assert decode_canonical_bytes(product.canonical_bytes(), SquareNativeResult, maximum_bytes=65536) == product


def test_independent_comparison_keeps_wrong_return_as_falsified():
    operand, _, _, config = operands()
    native = SquareNativeResult(config.node_id + ".native", config.identity, operand.identity,
        64, 89441, "2.4.6", Decimal("0.001"), Decimal("0.002"), 1024)
    product = SquareResult(config.node_id + ".product", config, native, 89440, "FALSIFIED")
    assert decode_canonical_bytes(product.canonical_bytes(), SquareResult, maximum_bytes=65536) == product
    with pytest.raises(ValueError, match="comparison"):
        replace(product, disposition="SATISFIED")


@pytest.mark.parametrize("last", (-1, 1025, True, 1.0))
def test_integer_boundary_refuses_before_calculation(last):
    with pytest.raises(ValueError, match="1024"):
        SquareInput("exposed.invalid-integer", last)


def test_unknown_profile_fault_schema_and_calculation_refuse():
    operand, _, spec, _ = operands()
    for change in ({"numpy_version": "latest"}, {"fault": "retry"}, {"interpreter_path": "relative/python"}):
        with pytest.raises(ValueError):
            replace(spec.worker, **change)
    with pytest.raises(ValueError, match="unimplemented"):
        replace(spec, calculation="TODO")
    with pytest.raises(ValueError, match="revision"):
        replace(spec, operand=replace(operand.identity, object_version="99.0.0"))
    with pytest.raises(ValueError, match="dimensionless"):
        replace(operand, units="kg")


def test_compiler_derives_one_native_task_from_original_complete_inputs():
    operand, provenance, spec, config = operands()
    draft, inputs = design.lower(spec, operand, provenance)
    declaration = bindings.operation_declaration()
    kwargs = dict(registry=CapabilityRegistry("exposed.isolated.registry", (declaration.manifest(),)),
        registrations=(declaration.registration(),), implementation_commit="c" * 40, output_codecs=declaration.record_codecs)
    compiled = compile_recursive_wave(draft=draft, **kwargs)
    task, = compiled.execution_plan.tasks
    assert task.task_id == config.node_id and len(inputs) == 2
    assert declaration.execution_properties.native_effect
    assert declaration.scientific_hooks.scientific_unit_ids(config) == (UNIT,)
    assert len(declaration.scientific_hooks.native_effect_slot_ids(config)) == 1
    assert task.capability.requested_resources == design.BUDGET
    with pytest.raises(ValueError):
        compile_recursive_wave(draft=replace(draft, external_inputs=draft.external_inputs[:-1]), **kwargs)


def test_preparation_reports_inputs_and_operational_selections_before_authoring(tmp_path):
    operand, provenance, spec, _ = operands()
    records = {"operand": operand, "provenance": provenance}
    bound = experiment.bind_inputs(spec, records)
    missing = experiment.prepare(spec, scientific_inputs=bound.scientific_inputs,
        execution=ExecutionSelection(), method_inputs=bound.method_inputs)
    assert len(missing.dependencies) == 4 and missing.draft is None
    assert missing.census.native_effect_count == 1
    ready = experiment.prepare(spec, scientific_inputs=bound.scientific_inputs,
        execution=ExecutionSelection(workers=1, environment_id="exposed.environment", output_root=str(tmp_path),
            source_snapshot=ObjectIdentity("exposed.source", "empirical-lawhood/testing/source", "1.0.0", "a"*64)),
        method_inputs=bound.method_inputs)
    assert ready.executable and len(ready.allocation.units) == 1
    experiment.validate_instance(specification=spec, allocation=ready.allocation, draft=ready.draft,
        source_records=ready.design_records)
    with pytest.raises(ValueError, match="identity"):
        experiment.bind_inputs(spec, {**records, "operand": replace(operand, last_integer=63)})


def test_invocation_contains_small_controls_but_not_complete_source_inventory():
    operand, provenance, _, config = operands()
    parent = NativeEffectContact("exposed.run", config.node_id, "exposed.attempt",
        ObjectIdentity("exposed.plan", "empirical-lawhood/testing/plan", "1.0.0", "e"*64),
        ObjectIdentity(config.node_id, "empirical-lawhood/testing/task", "1.0.0", "f"*64),
        "c"*40, ("materialization.exposed.config", "materialization.exposed.operand", "materialization.exposed.source"), ())
    definitions = definitions_for(config, parent, materialization_ids=parent.input_materialization_ids,
        code_sha256=provenance.code_sources_sha256, lock_sha256=provenance.dependency_lock_sha256)
    raw = invocation_bytes(config, operand, definitions)
    assert len(raw) < MAX_CONTROL_BYTES
    assert b"disclosed-software-fixture.py" not in raw
    assert all(row.input_materialization_ids == parent.input_materialization_ids for row in definitions)
    assert all(provenance.identity in row.sources for row in definitions)


def test_retained_reader_keeps_adverse_result_without_calculation(monkeypatch):
    from empirical_lawhood.api.isolated_native_starter import read_result
    from empirical_lawhood.execution.recursive_provider import RecursiveOperationProvider
    operand, _, spec, config = operands()
    native = SquareNativeResult(config.node_id + ".native", config.identity, operand.identity,
        64, 89441, "2.4.6", Decimal("0.001"), Decimal("0.002"), 1024)
    product = SquareResult(config.node_id + ".product", config, native, 89440, "FALSIFIED")
    def refused(*a, **k):
        pytest.fail("retained read entered calculation or provider")
    monkeypatch.setattr(native_entry, "calculate", refused)
    monkeypatch.setattr(runner, "independent_sum", refused)
    monkeypatch.setattr(RecursiveOperationProvider, "runners", refused)
    receipt = SimpleNamespace(run_id="exposed.run", task_id=config.node_id, attempt_id="exposed.attempt",
        operational_status=OperationalStatus.SUCCEEDED)
    result = read_result(directory=None, artifact_writer=None, specification=spec,
        instance=SimpleNamespace(specification=spec.identity), payloads={}, report={"run_id": "exposed.run"},
        products={"receipts": {config.node_id: receipt}, "records": {config.node_id: {product.record_id: product}}},
        draft=None, plan=SimpleNamespace(source_plan=SimpleNamespace(object_id="exposed.run"),
            tasks=(SimpleNamespace(task_id=config.node_id),)))
    assert result["claim_disposition"] == "FALSIFIED" and result["original_attempt_id"] == "exposed.attempt"
    assert not result["native_acquisition_performed"] and result["qualification"] == "NOT_ESTABLISHED"


def test_fresh_descriptor_import_performs_no_native_import_or_process_contact():
    root = Path(__file__).resolve().parents[1]
    script = '''import importlib.abc, sys, subprocess, socket
class Guard(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'numpy','scipy','brian2','pyscf','openmm','jax','pybamm'}:
            raise RuntimeError('native initialization during static discovery: ' + fullname)
sys.meta_path.insert(0, Guard())
def refuse(*a, **k): raise RuntimeError('process or network contact during discovery')
subprocess.Popen = refuse
socket.create_connection = refuse
from empirical_lawhood.adapters.isolated_native_starter.extension import EXTENSION
assert EXTENSION.discovery is not None
from empirical_lawhood.adapters.isolated_native_starter.public_facets import WORKFLOW_INSTALLATIONS
assert len(WORKFLOW_INSTALLATIONS) == 2
'''
    result = subprocess.run([sys.executable, "-B", "-c", script], cwd=root, capture_output=True,
        env=dict(os.environ, PYTHONPATH=str(root / "src"), PYTHONDONTWRITEBYTECODE="1"), timeout=30)
    assert result.returncode == 0, result.stderr.decode()


def test_separate_worker_manifest_keeps_the_controller_and_brian2_pins():
    from empirical_lawhood.api.workflow_installation import workflow_installation
    selected = workflow_installation("isolated-native-starter", profile="separate-numpy")
    versions = lambda name: {r["name"]: r["version"] for r in selected["environments"][name]["targets"][0]["requirements"]}
    assert versions("base")["numpy"] == "2.4.6"
    assert versions("isolated-native-starter-worker")["numpy"] == "2.3.5"
    brian = workflow_installation("neuron-current-response")
    assert next(r["version"] for r in brian["environments"]["brian2-worker"]["targets"][0]["requirements"] if r["name"] == "numpy") == "1.26.4"


@pytest.mark.parametrize("raw", (b"", b"\xff\x00\x80\r\n", bytes(range(256)) * 128))
def test_process_log_preserves_empty_binary_and_maximum_streams(raw):
    original = ProcessLog.from_bytes("exposed.process.stderr", "stderr", raw)
    assert original.original_bytes() == raw and original.size_bytes == len(raw)
    assert len(original.canonical_bytes()) < MAX_RESULT_BYTES
    assert decode_canonical_bytes(original.canonical_bytes(), ProcessLog, maximum_bytes=MAX_RESULT_BYTES) == original
    with pytest.raises(ValueError, match="original complete bytes"):
        replace(original, content_sha256="a" * 64)
    with pytest.raises(ValueError, match="bounded original bytes"):
        ProcessLog.from_bytes("exposed.oversize", "stdout", b"x" * (MAX_LOG_BYTES + 1))
