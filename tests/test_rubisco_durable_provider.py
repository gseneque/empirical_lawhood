# SPDX-License-Identifier: MPL-2.0
"""Exposed public preparation/custody controls; zero molecular entry."""

from dataclasses import replace
from hashlib import sha256
import io
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import contracts as c
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import durable_contracts as d
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import durable_operation_bindings as ob
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import durable_recursive_translation as rt
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import durable_stream as stream
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_preparation import complete_unit
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_roster import census
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.preparation import controlled_constructs
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.capabilities import CapabilityRegistry
from empirical_lawhood.runtime.native_subwork import NativeSubworkState
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
from tests.test_rubisco_durable_preparation import selected as custody_fixture, unit
from tests.test_rubisco_insilico_dynamics import sequences

selected = custody_fixture


class Emitter:
    def __init__(self):
        self.outputs = {}

    def write(self, name, raw):
        self.outputs.setdefault(name, bytearray()).extend(raw)


class Port:
    def __init__(self, raw, chunk=273):
        self.size_bytes, self.reader, self.chunk = len(raw), io.BytesIO(raw), chunk

    def read(self, size):
        return self.reader.read(min(size, self.chunk))


def exported(selected):
    emitter = Emitter()
    result = census(selected.progress, selected.plan, selected.selected)
    stream.emit_units(emitter, "units", selected.progress, result, selected.selected)
    return bytes(emitter.outputs["units"]), result


def test_full_unit_call_operand_and_return_recover_without_reexecution(selected):
    definition, entry, directory, ledger = unit(selected)
    effects = []
    (directory / "request.bin").write_bytes(b"original full operand\x00\xff")
    def actual():
        effects.append(True)
        (directory / "return.bin").write_bytes(b"actual full adverse return\x80")
        return -7
    ledger.call("exposed.actual-return", {"negative": -7}, actual)
    complete_unit(selected.progress, selected.plan, entry, selected.root, directory, ledger,
        succeeded=False, error="actual adverse return, retained before assessment")
    raw, expected = exported(selected)
    observed = {}
    def consume(evidence, name, block, done):
        observed.setdefault((evidence.definition.subwork_id, name), bytearray()).extend(block)
    assert stream.authenticate_units(Port(raw), selected.plan, on_chunk=consume) == expected
    assert len(observed) == 10  # unit3 + operand3 + call4
    import gzip
    assert any(b"actual full adverse return" in gzip.decompress(value)
        for (_, name), value in observed.items() if name == "files.raw")
    assert exported(selected)[0] == raw and len(effects) == 1
    assert dict(expected.states)[definition.subwork_id] is NativeSubworkState.COMPLETED
    assert len(expected.states) == 36 and expected.physical_independent_units == 0


def test_unknown_unit_cannot_supply_an_invented_return(selected):
    definition, _, directory, _ = unit(selected)
    (directory / "unreceipted-prefix.bin").write_bytes(b"unknown actual contact")
    raw, expected = exported(selected)
    assert dict(expected.states)[definition.subwork_id] is NativeSubworkState.UNKNOWN_COMPLETION
    calls = []
    assert stream.authenticate_units(Port(raw), selected.plan, on_chunk=lambda *args: calls.append(args)) == expected
    assert not calls


@pytest.mark.parametrize("damage", ("omit-last", "missing-lf", "duplicate-sequence", "bad-size", "changed-byte", "new-plan"))
def test_incomplete_or_changed_stream_refuses(selected, damage):
    _, entry, directory, ledger = unit(selected)
    (directory / "original.bin").write_bytes(b"source-bound original bytes" * 12)
    complete_unit(selected.progress, selected.plan, entry, selected.root, directory, ledger, succeeded=True)
    raw, _ = exported(selected)
    plan = replace(selected.plan, plan_id="config.changed-label") if damage == "new-plan" else selected.plan
    rows = raw.splitlines(keepends=True)
    if damage == "omit-last":
        raw = b"".join(rows[:-1])
    elif damage == "missing-lf":
        raw = raw[:-1]
    elif damage != "new-plan":
        row = json.loads(rows[-1])
        if damage == "duplicate-sequence":
            row["sequence"] -= 1
        elif damage == "bad-size":
            row["value"]["size_bytes"] += 1
        else:
            payload = bytearray.fromhex(row["value"]["payload_hex"])
            payload[-1] ^= 1
            row["value"]["payload_hex"] = payload.hex()
        raw = b"".join(rows[:-1]) + canonical_json_bytes(row)
    with pytest.raises(ValueError):
        stream.authenticate_units(Port(raw), plan)


@pytest.fixture
def config():
    def identity(name, schema, digest="1" * 64):
        return ObjectIdentity(name, schema, "1.0.0", digest)
    source = c.PreparationSelection("input.exposed.preparation",
        identity("inventory.exposed", "empirical-lawhood/rubisco-insilico-structure/inventory"),
        identity("coordinates.exposed", "empirical-lawhood/rubisco-insilico-structure/assembly-coordinates"),
        identity("nomination.exposed", "empirical-lawhood/rubisco-nomination-preparation/exploratory-dossier",
            "8121b9e941cbc66d0634dbc9f3047c6e22232fb1a783f2a313a17bf5f63f35fa"),
        c.NATIVE_WORK_ROOT + "/exposed-provider01", c.ENGINE_INVENTORY_SHA256,
        controlled_constructs(**sequences()),
        (c.SourceMember("source.exposed", "https://example.invalid/exposed", sha256(b"exposed").hexdigest(), "exposed"),))
    code = (("src/exposed.py", "2" * 64),)
    provenance = NumericalProducingProvenance(
        '{"python":"exposed","numpy":"exposed","scipy":"exposed","system":"Linux","machine":"exposed","threadpools":[]}',
        "3" * 64, code, sha256(canonical_json_bytes(code)).hexdigest(), "4" * 40, False)
    plan = d.DurablePreparationPlan("plan.exposed", c.identity(source), source.nomination, source.structural_inventory,
        source.structural_coordinates, source.native_workdir, sys.executable, "5" * 64, sys.executable, "5" * 64,
        source.engine_inventory_sha256, code, provenance.dependency_lock_sha256,
        attempted_geometry_ids=(d.geometry_id(*d.geometry_keys()[0]),), attempted_model_ids=())
    environment = tuple(sorted({"PYTHONPATH": "/exposed/source/src", "PYTHONDONTWRITEBYTECODE": "1",
        **{name: "1" for name in ("OPENMM_CPU_THREADS", "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS",
            "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS")}}.items()))
    return ob.DurablePreparationConfig("config." + ob.NODE, plan, source, provenance.identity,
        "/exposed/source", "/exposed/invocation.json", environment)


def compile_config(config, draft=None):
    registry = CapabilityRegistry("registry.exposed.durable-preparation", ob.operation_manifests())
    return compile_recursive_wave(draft=draft or rt.preparation_control_draft(config),
        registrations=ob.operation_registrations(), registry=registry, implementation_commit="1" * 40,
        output_codecs=ob.output_codecs())


def test_public_control_graph_fixed_outputs_full_unentered_denominator(config):
    result = compile_config(config)
    task, = result.execution_plan.tasks
    assert task.maximum_attempts == 1 and ob.operation_registrations()[0].native_effect
    assert tuple((row.payload_schema, row.profile) for row in task.outputs) == (
        (d.DurablePreparationCensus.SCHEMA, ArtifactProfile.CANONICAL_JSON),
        (stream.DurableUnitStreamChunk.SCHEMA, ArtifactProfile.JSONL_CHUNKS))
    assert len(config.plan.geometry_census) == 12 and len(config.plan.model_census) == 24
    assert len(config.plan.attempted_geometry_ids) == 1 and not config.plan.attempted_model_ids
    assert rt.scientific_work(rt.preparation_control_draft(config), ob.NODE)


@pytest.mark.parametrize("damage", ("missing-input", "wrong-history-role", "wrong-budget", "wrong-environment"))
def test_registered_control_refuses_changed_source_graph_and_entry_operands(config, damage):
    if damage == "wrong-environment":
        with pytest.raises(ValueError):
            replace(config, environment=tuple((name, "2" if name == "OMP_NUM_THREADS" else value)
                for name, value in config.environment))
        return
    draft = rt.preparation_control_draft(config)
    if damage == "missing-input":
        draft = replace(draft, links=draft.links[:-1])
    elif damage == "wrong-history-role":
        draft = replace(draft, links=(replace(draft.links[0], scientific_role="SOURCE"), *draft.links[1:]))
    else:
        operation, = draft.operations
        draft = replace(draft, operations=(replace(operation, resource_budget=replace(ob.BUDGET, cpu_cores=2)),))
    with pytest.raises(ValueError):
        compile_config(config, draft)


def test_operational_relabelling_does_not_recommission_same_physical_work(config):
    old = rt.scientific_work(rt.preparation_control_draft(config), ob.NODE)
    source = replace(config.source, selection_id="input.changed-label", native_workdir=c.NATIVE_WORK_ROOT + "/changed-working-label")
    plan = replace(config.plan, plan_id="plan.changed-label", source=c.identity(source), workdir=source.native_workdir)
    changed = replace(config, source=source, plan=plan, invocation_path="/exposed/changed-invocation.json")
    assert rt.native_effect_slot_ids(config) == rt.native_effect_slot_ids(changed)
    assert old == rt.scientific_work(rt.preparation_control_draft(changed, draft_id="draft.changed-label"), ob.NODE)
    changed = replace(config, plan=replace(config.plan, attempted_geometry_ids=tuple(sorted(
        d.geometry_id(*key) for key in config.plan.geometry_census[:2]))))
    assert rt.native_effect_slot_ids(config) != rt.native_effect_slot_ids(changed)


def test_descriptor_factory_imports_cold_without_native(tmp_path):
    code = """
import importlib.abc
import sys
class Refuse(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'numpy','scipy','openmm','pdbfixer','parmed','pybamm','flint'}:
            raise RuntimeError('native import refused: '+fullname)
sys.meta_path.insert(0,Refuse())
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_extension_bundle import EXTENSION_BUNDLE_CONTRIBUTION
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_executable_binding import EXECUTABLE_BINDING_FACTORIES
assert len(EXECUTABLE_BINDING_FACTORIES) == 1
assert len(EXTENSION_BUNDLE_CONTRIBUTION.capability_manifests) == 1
"""
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run([sys.executable, "-c", code], cwd=tmp_path,
        env=dict(os.environ, PYTHONPATH=str(root / "src"), PYTHONDONTWRITEBYTECODE="1"), capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr

