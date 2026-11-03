# SPDX-License-Identifier: MPL-2.0
"""Explicit software fixtures test Wilson role joins and worker information stops."""

from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.rubisco_combinations import analysis, records as r, source_binding
from empirical_lawhood.adapters.methods.rubisco_combinations.operation_bindings import (
    MAX_BYTES, MEDIA_TYPE, NODE_IDS, PHASES, operation_declarations, output_codecs,
)
from empirical_lawhood.adapters.methods.rubisco_combinations.operation_contracts import (
    CombinationCommitConfigV1, CombinationEvaluateConfigV1, CombinationPredictConfigV1, CombinationSourceConfigV1,
)
from empirical_lawhood.adapters.methods.rubisco_combinations.recursive_translation import wilson_combinations_recursive_draft
from empirical_lawhood.adapters.methods.rubisco_combinations.source_binding import TeParentGenbankInputV1, WilsonArticleInputV1
from empirical_lawhood.adapters.physical.rubisco_kinetics.genbank import decode_te_parent_genbank
from empirical_lawhood.adapters.physical.rubisco_kinetics.wilson2017 import build_wilson2017_panel, decode_wilson2017_html
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.serialization import canonical_value
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.capabilities import CapabilityConfigRef, CapabilityRegistry
from empirical_lawhood.runtime.execution import (
    DependencyReceiptBinding, TaskContext, WorkerInputBinding, WorkerInputKind, WorkerInputPort, WorkerIsolationProfile, WorkerOutputPort,
)
from empirical_lawhood.runtime.plans import BarrierKind, ScientificStage
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
from tests.test_rubisco_wilson import parent_fixture, table_fixture

ROOT = Path(__file__).resolve().parents[1]
CONFIGS = {"source": CombinationSourceConfigV1, "predict": CombinationPredictConfigV1,
           "commit": CombinationCommitConfigV1, "evaluate": CombinationEvaluateConfigV1}


@pytest.fixture
def fixture_sources(monkeypatch):
    # Fixtures contain synthetic endpoints and synthetic deposited sequences.
    # Only this test overrides reviewed source pins; no producing provenance,
    # signers or real scientific execution are synthesized.
    html = table_fixture().decode()
    old_names = tuple(f"Te-2G{chr(97+i)} ({i+1})" for i in range(10))
    new_names = tuple(name for _, name in r.SOURCE_ROSTER if name.startswith("Te-2G"))
    for old, new in zip(old_names, new_names, strict=True):
        html = html.replace(old, new)
    rows = html.split("<tr>")
    for name, kcat, specificity in (("Te-P415A", "8.0", "60.0"), ("Te-2Gj (15)", "10.0", "66.0"),
                                   ("Te-2Gb (2)", "12.0", "54.0"), ("Te-2Gf (10)", "9.0", "57.0")):
        for index, row in enumerate(rows):
            if f">{name}<" in row:
                rows[index] = row.replace("10.0 ± 0.2**", kcat + " ± 0.2").replace("50.0 ± 0.3", specificity + " ± 0.3")
    article_raw = "<tr>".join(rows).encode()
    genbank_raw = parent_fixture()
    article_sha, genbank_sha = sha256(article_raw).hexdigest(), sha256(genbank_raw).hexdigest()
    parent = decode_te_parent_genbank(genbank_raw, expected_sha256=genbank_sha)
    panel = build_wilson2017_panel(decode_wilson2017_html(article_raw, expected_sha256=article_sha), parent)
    for name, value in (("SOURCE_PANEL_FINGERPRINT", panel.fingerprint()), ("PARENT_FINGERPRINT", parent.fingerprint()),
                        ("SOURCE_ARTICLE_SHA256", article_sha), ("DEPOSITED_PARENT_SHA256", genbank_sha),
                        ("SOURCE_MEMBER_FINGERPRINTS", {row.native_table_row.ordinal_0based: row.fingerprint() for row in panel.rows})):
        monkeypatch.setattr(r, name, value)
    monkeypatch.setattr(source_binding, "WILSON_SOURCE_SHA256", article_sha)
    monkeypatch.setattr(source_binding, "GENBANK_SOURCE_SHA256", genbank_sha)
    article = WilsonArticleInputV1("input.software-wilson-original", article_sha, article_raw.decode())
    genbank = TeParentGenbankInputV1("input.software-te-parent", genbank_sha, genbank_raw.decode())
    science, training, features, labels = analysis.prepare_roles(panel, parent)
    return article, genbank, panel, science, training, features, labels


def draft_for(source):
    return wilson_combinations_recursive_draft(source[0], source[1],
        protocol_payload=(ROOT / "programmes/biology/photosynthesis/records/assessment-protocol.md").read_bytes())


def compile_draft(draft):
    return compile_recursive_wave(draft=draft, registrations=tuple(declaration.registration() for declaration in operation_declarations()),
        registry=CapabilityRegistry("registry.combinations-software-fixture", tuple(sorted(tuple(declaration.manifest() for declaration in operation_declarations()), key=lambda v: v.registry_id))),
        implementation_commit="a" * 40, output_codecs=output_codecs())


class CountingReader(BytesIO):
    bytes_read = 0

    def read(self, size=-1):
        payload = super().read(size)
        self.bytes_read += len(payload)
        return payload


def worker(role, science, operands, *, compiled_task=None):
    config = CONFIGS[role](f"config.{NODE_IDS[role]}", science)
    runner = next(declaration.runner_factory() for declaration in operation_declarations()
                  if declaration.capability_key.endswith(f".{role}"))
    inputs = [(config.config_id, config, None), *operands]
    ports, readers, receipts = [], {}, []
    for artifact, record, producer in sorted(inputs):
        raw = record.canonical_bytes()
        materialization = f"material.{artifact}"
        binding = WorkerInputBinding(artifact, materialization, record.SCHEMA, MEDIA_TYPE, len(raw),
            VisibilityCeiling.DEVELOPMENT_ONLY, OutcomeAccess.DEVELOPMENT_VISIBLE,
            WorkerInputKind.DEPENDENCY if producer else WorkerInputKind.EXTERNAL)
        readers[artifact] = CountingReader(raw)
        ports.append(WorkerInputPort(binding, readers[artifact]))
        if producer:
            receipts.append(DependencyReceiptBinding(f"receipt.{artifact}", NODE_IDS[producer], (materialization,)))
    row = next(v for v in PHASES if v[0] == role)
    outputs = tuple(WorkerOutputPort(f"{NODE_IDS[role]}.{name}", record.SCHEMA, ArtifactProfile.CANONICAL_JSON, MEDIA_TYPE)
                    for name, record in row[3])
    config_ref = CapabilityConfigRef(config.config_id, config.SCHEMA, sha256(config.SCHEMA.encode()).hexdigest(),
                                    config.fingerprint(), config.config_id)
    if compiled_task is not None:
        config_ref = compiled_task.capability.config
        outputs = tuple(WorkerOutputPort(v.output_id, v.payload_schema, v.profile, v.media_type, v.logical_artifact_id)
                        for v in compiled_task.outputs)
    context = TaskContext("run.combinations-software-fixture", NODE_IDS[role], f"{NODE_IDS[role]}.attempt-001", config_ref,
        tuple(v.binding for v in ports), tuple(ports), outputs, runner.manifest.permissions,
        OutcomeAccess.DEVELOPMENT_VISIBLE, runner.manifest.resource_ceiling, WorkerIsolationProfile.TRUSTED_LOCAL,
        tuple(sorted(receipts, key=lambda v: v.receipt_id)))
    return runner, context, readers


def products_of(result, role):
    outputs = next(v[3] for v in PHASES if v[0] == role)
    return {name: decode_canonical_bytes(value.payload, kind, maximum_bytes=MAX_BYTES)
            for value, (name, kind) in zip(result.outputs, outputs, strict=True)}


def test_four_compiled_stages_use_separate_roles_and_freeze_before_falsification(fixture_sources):
    draft = draft_for(fixture_sources)
    compiled = compile_draft(draft)
    assert len(compiled.execution_plan.tasks) == 4 and len(draft.external_inputs) == 2 and len(draft.links) == 7
    tasks = {v.task_id: v for v in compiled.execution_plan.tasks}
    assert tasks[NODE_IDS["commit"]].barrier is BarrierKind.FREEZE
    assert tasks[NODE_IDS["evaluate"]].stage is ScientificStage.FALSIFY
    assert tasks[NODE_IDS["evaluate"]].barrier is BarrierKind.NONE
    assert NODE_IDS["commit"] in tasks[NODE_IDS["evaluate"]].dependency_task_ids
    assert all(v.barrier is not BarrierKind.REVEAL for v in tasks.values())
    assert all(not v.native_effect for v in tuple(declaration.registration() for declaration in operation_declarations()))
    prediction_links = tuple(v for v in draft.links if v.consumer_node_id == NODE_IDS["predict"])
    assert {v.consumer_input_id for v in prediction_links} == {"training", "features"}
    assert all(v.producer_output_id not in {"labels", "panel"} for v in prediction_links)
    assert draft.development_study.assigned_unit_ids == ("rubisco-combinations.analysis.a398t-a48v",)
    assert "nineteen source enzymes remain context" in draft.development_study.claims[0].estimand


def test_registered_workers_preserve_adverse_target_full_source_and_actual_compiler_output_ids(fixture_sources):
    article, genbank, _, science, _, _, _ = fixture_sources
    tasks = {v.task_id: v for v in compile_draft(draft_for(fixture_sources)).execution_plan.tasks}
    runner, context, _ = worker("source", science, [(article.input_id, article, None), (genbank.input_id, genbank, None)],
                                compiled_task=tasks[NODE_IDS["source"]])
    prepared = products_of(runner.execute(context), "source")
    assert len(prepared["panel"].rows) == 19
    assert len(prepared["training"].observations) == 3
    assert prepared["features"].target.role == "TARGET" and not hasattr(prepared["features"], "observations")
    runner, context, _ = worker("predict", science, [("role.training", prepared["training"], "source"),
        ("role.features", prepared["features"], "source")], compiled_task=tasks[NODE_IDS["predict"]])
    forecast = products_of(runner.execute(context), "predict")["forecast"]
    assert forecast.additive_point.turnover_s_inv == Decimal("15.0")
    assert forecast.additive_point.specificity_dimensionless == Decimal("59.4")
    runner, context, _ = worker("commit", science, [("role.forecast", forecast, "predict")],
                                compiled_task=tasks[NODE_IDS["commit"]])
    commitment = products_of(runner.execute(context), "commit")["commitment"]
    runner, context, _ = worker("evaluate", science, [("a.labels", prepared["labels"], "source"),
        ("z.commitment", commitment, "commit")], compiled_task=tasks[NODE_IDS["evaluate"]])
    evaluation = products_of(runner.execute(context), "evaluate")["evaluation"]
    assert len(evaluation.errors) == 2
    assert evaluation.observed_joint_point_improvement is False and evaluation.predicted_joint_point_improvement is False
    assert evaluation.labels.target.turnover.mean == Decimal("9.0")
    assert all(v.scientific_unit_ids is not None for v in tuple(declaration.registration() for declaration in operation_declarations()))


@pytest.mark.parametrize("change", [
    lambda d: replace(d, development_study=replace(d.development_study, question="Unseen biological generalization")),
    lambda d: replace(d, development_study=replace(d.development_study, assigned_unit_ids=("invented.biological-root",))),
    lambda d: replace(d, links=tuple(v for v in d.links if v.consumer_input_id != "commitment")),
    lambda d: replace(d, links=tuple(replace(v, producer_output_id="labels") if v.consumer_node_id == NODE_IDS["predict"]
                                    and v.consumer_input_id == "features" else v for v in d.links)),
    lambda d: replace(d, links=tuple(replace(v, scientific_role="SOURCE") if v.consumer_input_id == "labels" else v for v in d.links)),
])
def test_substituted_root_census_role_or_global_commit_dependency_refuses(fixture_sources, change):
    with pytest.raises(ValueError):
        compile_draft(change(draft_for(fixture_sources)))


def test_source_version_and_protocol_substitution_are_explicit_refusals(fixture_sources):
    article, genbank, _, science, *_ = fixture_sources
    wrong = replace(article, source_sha256=sha256(b"different native source").hexdigest(), raw_html_utf8="different native source")
    with pytest.raises(ValueError, match="exact reviewed"):
        source_binding.prepare_source(CombinationSourceConfigV1(f"config.{NODE_IDS['source']}", science), wrong, genbank)
    with pytest.raises(ValueError, match="protocol"):
        wilson_combinations_recursive_draft(article, genbank, protocol_payload=b"different protocol")


@pytest.mark.parametrize("role", ("source", "predict", "commit", "evaluate"))
def test_output_namespace_substitution_refuses_before_any_source_or_label_read(fixture_sources, role):
    article, genbank, _, science, training, features, labels = fixture_sources
    forecast = analysis.predict(science, training, features)
    commitment = analysis.commit(science, forecast)
    operands = {"source": [(article.input_id, article, None), (genbank.input_id, genbank, None)],
                "predict": [("role.training", training, "source"), ("role.features", features, "source")],
                "commit": [("role.forecast", forecast, "predict")],
                "evaluate": [("role.commitment", commitment, "commit"), ("role.labels", labels, "source")]}[role]
    runner, context, readers = worker(role, science, operands)
    context = replace(context, output_ports=tuple(replace(v, output_id="unrelated." + v.output_id) for v in context.output_ports))
    with pytest.raises(ValueError, match="task-prefixed"):
        runner.execute(context)
    assert all(v.bytes_read == 0 and v.closed for v in readers.values())


def payload_operand(schema, document):
    raw = json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode() + b"\n"
    return SimpleNamespace(SCHEMA=schema, canonical_bytes=lambda: raw)


def alter_observation(observation):
    # Every changed endpoint/token is internally self-consistent. Only the
    # authentic source-member fingerprint distinguishes this contributor.
    endpoint = observation["value"]["turnover"]
    endpoint["value"]["mean"] = canonical_value(Decimal("999"))
    endpoint["value"]["native_token"] = "999 ± 0.2"
    native = observation["value"]["native_row"]["value"]
    native["endpoints"][1] = endpoint
    native["native_table_row"]["value"]["cells"][5]["value"]["raw_text"] = "999 ± 0.2"


@pytest.mark.parametrize("role", ("predict", "evaluate"))
def test_correctly_hashed_fabricated_native_endpoint_operand_refuses(fixture_sources, role):
    _, _, _, science, training, features, labels = fixture_sources
    if role == "predict":
        document = training.to_document()
        alter_observation(document["value"]["observations"][0])
        bad = payload_operand(training.SCHEMA, document)
        operands = [("role.training", bad, "source"), ("role.features", features, "source")]
    else:
        document = labels.to_document()
        alter_observation(document["value"]["target"])
        bad = payload_operand(labels.SCHEMA, document)
        commitment = analysis.commit(science, analysis.predict(science, training, features))
        operands = [("role.labels", bad, "source"), ("role.commitment", commitment, "commit")]
    runner, context, _ = worker(role, science, operands)
    with pytest.raises(ValueError, match="source|native|fingerprint|projection"):
        runner.execute(context)


def test_invalid_commitment_stops_before_even_earlier_sorted_label_port(fixture_sources):
    _, _, _, science, training, features, labels = fixture_sources
    commitment = analysis.commit(science, analysis.predict(science, training, features))
    document = commitment.to_document()
    document["value"]["forecast"]["value"]["object_fingerprint"] = "0" * 64
    bad = payload_operand(commitment.SCHEMA, document)
    runner, context, readers = worker("evaluate", science, [("a.labels", labels, "source"), ("z.commitment", bad, "commit")])
    with pytest.raises(ValueError):
        runner.execute(context)
    assert readers["a.labels"].bytes_read == 0 and readers["a.labels"].closed


def test_upstream_receipt_task_substitution_and_label_oracle_port_refuse_before_reads(fixture_sources):
    _, _, _, science, training, features, labels = fixture_sources
    runner, context, readers = worker("predict", science, [("role.training", training, "source"), ("role.features", features, "source")])
    changed = replace(context, dependency_receipts=tuple(replace(v, task_id=NODE_IDS["evaluate"]) for v in context.dependency_receipts))
    with pytest.raises(ValueError, match="upstream"):
        runner.execute(changed)
    assert all(v.bytes_read == 0 for v in readers.values())
    runner, context, readers = worker("predict", science, [("role.training", training, "source"), ("role.labels", labels, "source")])
    with pytest.raises(ValueError, match="information roles"):
        runner.execute(context)
    assert all(v.bytes_read == 0 for v in readers.values())


def test_cold_descriptors_and_factories_do_not_decode_original_sources(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("cold descriptor inspected original source")
    monkeypatch.setattr(source_binding, "decode_source", forbidden)
    from empirical_lawhood.adapters.methods.rubisco_combinations.executable_binding import EXECUTABLE_BINDING_FACTORIES
    assert len(tuple(declaration.manifest() for declaration in operation_declarations())) == len(tuple(declaration.registration() for declaration in operation_declarations())) == len(EXECUTABLE_BINDING_FACTORIES) == 4
    assert r.CombinationLabelsV1.SCHEMA in output_codecs()
