# SPDX-License-Identifier: MPL-2.0
"""Software checks for cold plant stages and label-read ordering.

Original public sources are decoded for source conformance only. Numerical
construction uses explicitly synthetic source pins and truth-known point means;
these tests create no real authority, qualification or scientific run.
"""

from dataclasses import replace
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.rubisco_prediction import knn, records as r
from empirical_lawhood.adapters.methods.rubisco_prediction.operation_bindings import (
    BUDGETS, MAX_BYTES, MEDIA_TYPE, NODE_IDS, PHASES, SOURCE_OUTPUTS, TOTAL_BUDGET,
    operation_declarations, output_codecs,
    prepare_source, scientific_design,
)
from empirical_lawhood.adapters.methods.rubisco_prediction.operation_contracts import (
    ANALYSIS_UNIT_ID, SOURCE_IDS, PlantPredictionConstructConfigV1,
    PlantPredictionEvaluateConfigV1, PlantPredictionSourceConfigV1,
)
from empirical_lawhood.adapters.methods.rubisco_prediction.recursive_translation import plant_prediction_recursive_draft
from empirical_lawhood.adapters.physical.rubisco_kinetics.iqbal2023 import decode_iqbal2023
from empirical_lawhood.adapters.physical.rubisco_kinetics.mcdonald2026 import decode_mcdonald2026
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.capabilities import CapabilityConfigRef, CapabilityRegistry
from empirical_lawhood.runtime.execution import (
    DependencyReceiptBinding, TaskContext, WorkerInputBinding, WorkerInputKind,
    WorkerInputPort, WorkerIsolationProfile, WorkerOutputPort,
)
from empirical_lawhood.runtime.plans import BarrierKind, ScientificStage
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
from tests.test_rubisco_prediction import software_natural, software_plant

ROOT = Path(__file__).resolve().parents[1]
CONFIGS = {"source": PlantPredictionSourceConfigV1, "construct": PlantPredictionConstructConfigV1,
           "evaluate": PlantPredictionEvaluateConfigV1}


@pytest.fixture(scope="module")
def original_sources():
    fixtures = ROOT / "tests/fixtures/rubisco"
    natural = decode_iqbal2023((fixtures / "iqbal2023/primary.xml").read_bytes(),
                              (fixtures / "iqbal2023/table_s2.xlsx").read_bytes())
    plant = decode_mcdonald2026(*((fixtures / "mcdonald2026" / name).read_bytes() for name in (
        "primary.xml", "sciadv.aeh3246_table_s4.xlsx", "sciadv.aeh3246_table_s5.xlsx", "sciadv.aeh3246_table_s8.xlsx")))
    return natural, plant


def draft_for(sources):
    return plant_prediction_recursive_draft(*sources,
        protocol_payload=(ROOT / "programmes/biology/photosynthesis/records/plant-prediction-protocol-v1.md").read_bytes())


def compile_draft(draft):
    return compile_recursive_wave(draft=draft, registrations=tuple(declaration.registration() for declaration in operation_declarations()),
        registry=CapabilityRegistry("registry.plant-prediction-software-fixture",
                                   tuple(sorted(tuple(declaration.manifest() for declaration in operation_declarations()), key=lambda value: value.registry_id))),
        implementation_commit="a" * 40, output_codecs=output_codecs())


class CountingReader(BytesIO):
    bytes_read = 0

    def read(self, size=-1):
        payload = super().read(size)
        self.bytes_read += len(payload)
        return payload


def worker(role, operands, *, compiled_task=None):
    config = CONFIGS[role](f"config.{NODE_IDS[role]}", scientific_design())
    runner = next(declaration.runner_factory() for declaration in operation_declarations()
                  if declaration.capability_key.endswith(f".{role}"))
    inputs = [(config.config_id, config, None), *operands]
    ports, readers, receipts = [], {}, []
    for artifact, record, producer in sorted(inputs):
        payload = record.canonical_bytes()
        materialization = f"material.{artifact}"
        binding = WorkerInputBinding(artifact, materialization, record.SCHEMA, MEDIA_TYPE, len(payload),
            VisibilityCeiling.DEVELOPMENT_ONLY, OutcomeAccess.DEVELOPMENT_VISIBLE,
            WorkerInputKind.DEPENDENCY if producer else WorkerInputKind.EXTERNAL)
        readers[artifact] = CountingReader(payload)
        ports.append(WorkerInputPort(binding, readers[artifact]))
        if producer:
            receipts.append(DependencyReceiptBinding(f"receipt.{artifact}", NODE_IDS[producer], (materialization,)))
    row = next(value for value in PHASES if value[0] == role)
    outputs = tuple(WorkerOutputPort(f"{NODE_IDS[role]}.{name}", record.SCHEMA,
                                    ArtifactProfile.CANONICAL_JSON, MEDIA_TYPE) for name, record in row[3])
    config_ref = CapabilityConfigRef(config.config_id, config.SCHEMA, sha256(config.SCHEMA.encode()).hexdigest(),
                                    config.fingerprint(), config.config_id)
    if compiled_task is not None:
        config_ref = compiled_task.capability.config
        outputs = tuple(WorkerOutputPort(value.output_id, value.payload_schema, value.profile,
                                        value.media_type, value.logical_artifact_id) for value in compiled_task.outputs)
    context = TaskContext("run.plant-prediction-software-fixture", NODE_IDS[role],
        NODE_IDS[role] + ".attempt-001", config_ref, tuple(port.binding for port in ports),
        tuple(ports), outputs, runner.manifest.permissions, OutcomeAccess.DEVELOPMENT_VISIBLE,
        BUDGETS[role], WorkerIsolationProfile.TRUSTED_LOCAL,
        tuple(sorted(receipts, key=lambda receipt: receipt.receipt_id)))
    return runner, context, readers


def products(result, role):
    specs = next(value[3] for value in PHASES if value[0] == role)
    return {name: decode_canonical_bytes(output.payload, kind, maximum_bytes=MAX_BYTES)
            for output, (name, kind) in zip(result.outputs, specs, strict=True)}


def invalid_commitment():
    payload = json.dumps({"schema": r.PlantCommitmentV1.SCHEMA, "value": {}, "version": "1.0.0"},
                         sort_keys=True, separators=(",", ":")).encode() + b"\n"
    return SimpleNamespace(SCHEMA=r.PlantCommitmentV1.SCHEMA, canonical_bytes=lambda: payload)


def test_complete_three_stage_graph_freezes_all_cases_before_falsification(original_sources):
    draft = draft_for(original_sources)
    tasks = {task.task_id: task for task in compile_draft(draft).execution_plan.tasks}
    assert len(tasks) == 3 and len(draft.external_inputs) == 2 and len(draft.links) == 7
    assert tasks[NODE_IDS["construct"]].stage is ScientificStage.FREEZE
    assert tasks[NODE_IDS["construct"]].barrier is BarrierKind.FREEZE
    assert tasks[NODE_IDS["evaluate"]].stage is ScientificStage.FALSIFY
    assert tasks[NODE_IDS["evaluate"]].barrier is BarrierKind.NONE
    assert NODE_IDS["construct"] in tasks[NODE_IDS["evaluate"]].dependency_task_ids
    assert all(task.barrier is not BarrierKind.REVEAL for task in tasks.values())
    assert all(not registration.native_effect for registration in tuple(declaration.registration() for declaration in operation_declarations()))
    links = tuple(link for link in draft.links if link.consumer_node_id == NODE_IDS["construct"])
    assert {link.consumer_input_id for link in links} == {"anchors", "queries", "training"}
    assert all(link.producer_output_id not in {"labels", "panel"} for link in links)
    assert draft.development_study.assigned_unit_ids == (ANALYSIS_UNIT_ID,)
    assert "unknown independent biological n" in draft.development_study.claims[0].estimand
    assert sum(budget.wall_time_seconds for budget in BUDGETS.values()) == 600
    assert sum(budget.source_scan_bytes for budget in BUDGETS.values()) == TOTAL_BUDGET.source_scan_bytes
    assert sum(budget.output_bytes for budget in BUDGETS.values()) <= TOTAL_BUDGET.output_bytes == 128 * 1024**2
    assert {value.logical_artifact_id for value in draft.external_inputs} == set(SOURCE_IDS)


def test_source_worker_reproves_native_sources_and_separates_parent_from_labels(original_sources):
    tasks = {task.task_id: task for task in compile_draft(draft_for(original_sources)).execution_plan.tasks}
    runner, context, readers = worker("source", [(SOURCE_IDS[0], original_sources[0], None),
                                                (SOURCE_IDS[1], original_sources[1], None)],
                                      compiled_task=tasks[NODE_IDS["source"]])
    result = runner.execute(context)
    prepared = products(result, "source")
    assert tuple((name, type(value)) for name, value in prepared.items()) == SOURCE_OUTPUTS
    assert len(prepared["training"].rows) == 183
    assert len(prepared["queries"].queries) == len(prepared["labels"].labels) == 10
    assert prepared["queries"].queries[-1].recipe.edit == "A369V"
    assert prepared["anchors"].native_parent.protein_recipe.edit is None
    assert not hasattr(prepared["queries"], "labels")
    assert all(reader.closed and reader.bytes_read > 0 for reader in readers.values())
    assert sum(len(output.payload) for output in result.outputs) < BUDGETS["source"].output_bytes
    wrong = replace(context.config, content_sha256="0" * 64)
    _, altered, streams = worker("source", [(SOURCE_IDS[0], original_sources[0], None),
                                            (SOURCE_IDS[1], original_sources[1], None)])
    with pytest.raises(ValueError, match="immutable"):
        runner.execute(replace(altered, config=wrong))
    assert streams[SOURCE_IDS[0]].bytes_read == streams[SOURCE_IDS[1]].bytes_read == 0


@pytest.mark.parametrize("change", (
    lambda draft: replace(draft, development_study=replace(draft.development_study, question="Unseen biological generalization")),
    lambda draft: replace(draft, development_study=replace(draft.development_study, assigned_unit_ids=("invented.biological-root",))),
    lambda draft: replace(draft, links=tuple(link for link in draft.links if link.consumer_input_id != "commitment")),
    lambda draft: replace(draft, links=tuple(replace(link, producer_output_id="labels")
                         if link.consumer_node_id == NODE_IDS["construct"] and link.consumer_input_id == "queries" else link for link in draft.links)),
    lambda draft: replace(draft, links=tuple(replace(link, scientific_role="SOURCE")
                         if link.consumer_input_id == "labels" else link for link in draft.links)),
    lambda draft: replace(draft, links=tuple(replace(link, external_input_id="external." + SOURCE_IDS[1])
                         if link.consumer_input_id == "natural" else link for link in draft.links)),
))
def test_substituted_root_scope_label_role_or_commitment_dependency_refuses(original_sources, change):
    with pytest.raises(ValueError):
        compile_draft(change(draft_for(original_sources)))


def test_protocol_and_native_identity_substitutions_refuse(original_sources):
    with pytest.raises(ValueError, match="protocol"):
        plant_prediction_recursive_draft(*original_sources, protocol_payload=b"other protocol")
    with pytest.raises(ValueError, match="native source"):
        plant_prediction_recursive_draft(original_sources[1], original_sources[0],
            protocol_payload=(ROOT / "programmes/biology/photosynthesis/records/plant-prediction-protocol-v1.md").read_bytes())
    with pytest.raises(ValueError, match="frozen protocol"):
        replace(scientific_design(), protocol_sha256="0" * 64)
    config = PlantPredictionSourceConfigV1(f"config.{NODE_IDS['source']}", scientific_design())
    with pytest.raises(ValueError, match="sealed native"):
        prepare_source(config, original_sources[1], original_sources[0])


@pytest.fixture
def software_roles(monkeypatch):
    return software_natural(monkeypatch), software_plant(monkeypatch)


@pytest.mark.parametrize("role", ("source", "construct", "evaluate"))
def test_output_namespace_substitution_refuses_before_operand_reads(original_sources, software_roles, role):
    training, (queries, anchors, labels) = software_roles
    operands = {
        "source": [(SOURCE_IDS[0], original_sources[0], None), (SOURCE_IDS[1], original_sources[1], None)],
        "construct": [("role.training", training, "source"), ("role.queries", queries, "source"), ("role.anchors", anchors, "source")],
        "evaluate": [("a.labels", labels, "source"), ("z.commitment", invalid_commitment(), "construct")],
    }[role]
    runner, context, readers = worker(role, operands)
    changed = replace(context, output_ports=tuple(replace(port, output_id="wrong." + port.output_id) for port in context.output_ports))
    with pytest.raises(ValueError, match="task-prefixed"):
        runner.execute(changed)
    assert all(reader.bytes_read == 0 and reader.closed for reader in readers.values())


def test_label_injection_and_wrong_upstream_receipt_refuse_before_reads(software_roles):
    training, (queries, anchors, labels) = software_roles
    runner, context, readers = worker("construct", [("role.training", training, "source"),
        ("role.labels", labels, "source"), ("role.anchors", anchors, "source")])
    with pytest.raises(ValueError, match="information roles"):
        runner.execute(context)
    assert all(reader.bytes_read == 0 for reader in readers.values())
    runner, context, readers = worker("construct", [("role.training", training, "source"),
        ("role.queries", queries, "source"), ("role.anchors", anchors, "source")])
    substituted = replace(context, dependency_receipts=tuple(replace(receipt, task_id=NODE_IDS["evaluate"])
                                                            for receipt in context.dependency_receipts))
    with pytest.raises(ValueError, match="upstream"):
        runner.execute(substituted)
    assert all(reader.bytes_read == 0 for reader in readers.values())


def test_invalid_commitment_refuses_before_earlier_sorted_label_port(software_roles):
    _, (_, _, labels) = software_roles
    runner, context, readers = worker("evaluate", [("a.labels", labels, "source"),
                                                   ("z.commitment", invalid_commitment(), "construct")])
    with pytest.raises(ValueError):
        runner.execute(context)
    assert readers["a.labels"].bytes_read == 0 and readers["a.labels"].closed


@pytest.mark.parametrize("role,schema,maximum", (
    ("construct", r.NaturalTrainingV1.SCHEMA, 4 * 1024**2),
    ("construct", r.PlantQueriesV1.SCHEMA, 128 * 1024),
    ("construct", r.PlantParentAnchorsV1.SCHEMA, 128 * 1024),
    ("evaluate", r.PlantLabelsV1.SCHEMA, 1024**2),
))
def test_role_read_bounds_remain_narrower_than_conservative_dependency_contracts(software_roles, role, schema, maximum):
    training, (queries, anchors, labels) = software_roles
    operands = [("role.training", training, "source"), ("role.queries", queries, "source"),
                ("role.anchors", anchors, "source")] if role == "construct" else [
                    ("a.labels", labels, "source"), ("z.commitment", invalid_commitment(), "construct")]
    runner, context, readers = worker(role, operands)
    ports = tuple(replace(port, binding=replace(port.binding, size_bytes=maximum + 1))
                  if port.payload_schema == schema else port for port in context.input_ports)
    changed = replace(context, input_ports=ports, input_bindings=tuple(port.binding for port in ports))
    registration = next(value for value in tuple(declaration.registration() for declaration in operation_declarations()) if value.config_record_type is CONFIGS[role])
    assert next(port.maximum_size_bytes for port in registration.input_ports if port.payload_schema == schema) == 8 * 1024**2
    with pytest.raises(ValueError, match="unbounded information roles"):
        runner.execute(changed)
    assert all(reader.bytes_read == 0 and reader.closed for reader in readers.values())


@pytest.mark.native("rapidfuzz")
def test_construct_and_evaluate_workers_retain_complete_synthetic_forecasts_and_label_order(software_roles, monkeypatch):
    training, (queries, anchors, labels) = software_roles
    runner, context, _ = worker("construct", [("role.training", training, "source"),
        ("role.queries", queries, "source"), ("role.anchors", anchors, "source")])
    output = runner.execute(context)
    commitment = products(output, "construct")["commitment"]
    assert len(commitment.forecasts.forecasts) == 60
    assert len(commitment.forecasts.queries.queries) == 10
    assert len(output.outputs[0].payload) < MAX_BYTES
    runner, context, readers = worker("evaluate", [("a.labels", labels, "source"),
                                                   ("z.commitment", commitment, "construct")])
    original = knn.validate_commitment
    calls = []

    def prove_before_labels(value):
        if not calls:
            assert readers["a.labels"].bytes_read == 0
        original(value)
        calls.append(True)

    monkeypatch.setattr(knn, "validate_commitment", prove_before_labels)
    report = products(runner.execute(context), "evaluate")["evaluation"]
    assert calls and readers["a.labels"].bytes_read > 0
    assert len(report.errors) == 60 and len(report.summaries) == 12
    assert report.independent_biological_units is None and report.calibrated_joint_coverage is None
    assert not report.el_advantage_established and not report.candidate_nomination_established


def test_fresh_factories_and_registration_import_no_optional_library_or_source():
    script = """
import importlib.abc, sys
class Refuse(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == 'rapidfuzz' or fullname.startswith('rapidfuzz.'):
            raise AssertionError('optional distance import during registration')
sys.meta_path.insert(0, Refuse())
from empirical_lawhood.adapters.methods.rubisco_prediction import knn
def refuse(*args, **kwargs):
    raise AssertionError('cold descriptor interpreted source or computed')
knn.prepare_training = knn.prepare_plant_roles = knn.fit = knn.predict = refuse
from empirical_lawhood.adapters.methods.rubisco_prediction.executable_binding import EXECUTABLE_BINDING_FACTORIES
from empirical_lawhood.adapters.methods.rubisco_prediction.operation_bindings import operation_declarations
assert len(EXECUTABLE_BINDING_FACTORIES) == len(tuple(declaration.registration() for declaration in operation_declarations())) == len(tuple(declaration.runner_factory() for declaration in operation_declarations())) == 3
assert 'rapidfuzz' not in sys.modules
"""
    completed = subprocess.run([sys.executable, "-c", script], cwd=ROOT,
                               capture_output=True, text=True, check=False)
    assert completed.returncode == 0, completed.stderr
