# SPDX-License-Identifier: MPL-2.0
"""Finite exposed software fixtures for the editable development starter."""

from dataclasses import replace
from decimal import Decimal, localcontext
from hashlib import sha256
from types import SimpleNamespace

import pytest

from empirical_lawhood.methods.mass_balance_starter import bindings, design, experiment, science
from empirical_lawhood.methods.mass_balance_starter.examples import example_evidence
from empirical_lawhood.methods.mass_balance_starter.records import MassAssessment, MassEvidence, MassSpecification
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.execution.capabilities import CapabilityRegistry
from empirical_lawhood.execution.experiment_preparation import ExecutionSelection
from empirical_lawhood.execution.recursive_compiler import compile_recursive_wave


def operands(case="positive"):
    evidence = example_evidence(case)
    specification = MassSpecification("test.mass.specification", evidence.identity, evidence.scope,
        evidence.independent_unit_ids, Decimal("0.01"))
    config = design.config_for(specification, evidence)
    predictors, outcomes = design.inputs_for(evidence)
    return evidence, specification, config, predictors, outcomes


@pytest.mark.parametrize("case,disposition", (("positive", "SATISFIED"), ("adverse", "FALSIFIED"), ("unevaluable", "UNEVALUABLE")))
def test_exact_prediction_and_independent_falsifier_keep_complete_census(case, disposition, monkeypatch):
    evidence, spec, config, predictors, outcomes = operands(case)
    with localcontext() as context:
        context.prec = 8
        forecast = science.predict(science.prediction_config(config), predictors)
    assert tuple(r.final_kg for r in forecast.rows) == (Decimal("3.000000000000000000000000000001"), Decimal(3), Decimal("0.01"))
    assert not hasattr(predictors.rows[0], "final_kg")
    monkeypatch.setattr(science, "predict_final_mass", lambda *a: pytest.fail("assessor reran predictor"))
    result = science.assess(config, forecast, outcomes)
    assert tuple(r.unit_id for r in result.rows) == evidence.independent_unit_ids
    assert tuple(r.disposition for r in result.rows) == (disposition, "SATISFIED", "SATISFIED")
    assert decode_canonical_bytes(result.canonical_bytes(), MassAssessment, maximum_bytes=128*1024) == result
    if case == "unevaluable":
        assert result.rows[0].observed_kg is None and result.rows[0].absolute_error_kg is None
    requirement, connection = design.scientific_contract(config)
    supply, = bindings.assessment_projector(result, requirement, connection)
    assert supply.disposition.value == "SATISFIED" and supply.phase.value == "INSTANCE"
    assert supply.evidence_ceiling.value == "NON_PROMOTABLE"


def test_compiler_derives_exact_two_operations_and_scientific_consumer():
    evidence, spec, config, _, _ = operands()
    draft, inputs = design.lower(spec, evidence)
    declarations = bindings.operation_declarations()
    kwargs = dict(registry=CapabilityRegistry("test.mass.registry", tuple(d.manifest() for d in declarations)),
        registrations=tuple(d.registration() for d in declarations), implementation_commit="a" * 40,
        output_codecs={key: value for d in declarations for key, value in d.record_codecs.items()})
    compiled = compile_recursive_wave(draft=draft, **kwargs)
    tasks = {t.task_id: t for t in compiled.execution_plan.tasks}
    assert len(tasks) == 2 and len(inputs) == 2
    assert tasks[config.node_id].dependency_task_ids == (science.prediction_config(config).node_id,)
    assert not tasks[science.prediction_config(config).node_id].dependency_task_ids
    assert len(draft.requirements) == len(draft.connections) == 1
    assert draft.requirements[0].scope.native_units == ("kg",)
    assert all(not d.execution_properties.native_effect for d in declarations)
    with pytest.raises(ValueError):
        compile_recursive_wave(draft=replace(draft, connections=()), **kwargs)
    with pytest.raises(ValueError):
        compile_recursive_wave(draft=replace(draft, external_inputs=draft.external_inputs[:-1]), **kwargs)


def test_preparation_reports_real_prerequisites_and_instance_refuses_substitution(tmp_path):
    import json
    from empirical_lawhood.api.experiment_preparation import experiment_preparation_report

    evidence, spec, _, _, _ = operands()
    bound = experiment.bind_inputs(spec, {"evidence": evidence})
    unresolved = experiment.prepare(spec, scientific_inputs=bound.scientific_inputs,
        execution=ExecutionSelection(), method_inputs=bound.method_inputs)
    assert len(unresolved.dependencies) == 4 and unresolved.draft is None
    assert unresolved.census.native_effect_count == 0
    result = experiment.prepare(spec, scientific_inputs=bound.scientific_inputs,
        execution=ExecutionSelection(workers=1, environment_id="test.environment", output_root=str(tmp_path),
            source_snapshot=ObjectIdentity("test.source", "empirical-lawhood/testing/source", "1.0.0", "a"*64)),
        method_inputs=bound.method_inputs)
    assert result.executable and len(result.allocation.units) == 3
    assert result.census.native_effect_count == 0
    report = experiment_preparation_report(result)
    assert report['operation_origins']
    assert json.loads(json.dumps(report)) == report
    experiment.validate_instance(specification=spec, allocation=result.allocation, draft=result.draft, source_records=result.design_records)
    with pytest.raises(ValueError, match="identity"):
        experiment.bind_inputs(spec, {"evidence": example_evidence("adverse")})
    with pytest.raises(ValueError, match="code-derived"):
        experiment.validate_instance(specification=spec, allocation=result.allocation,
            draft=replace(result.draft, question="substituted scientific question"), source_records=result.design_records)


def test_incompatible_units_scope_schema_and_unimplemented_calculation_refuse():
    evidence, spec, config, predictors, outcomes = operands()
    with pytest.raises(ValueError, match="kg"):
        replace(evidence.scope, units="g")
    changed_scope = replace(evidence.scope, receiver_id="receiver.other")
    with pytest.raises(ValueError, match="scope"):
        experiment.bind_inputs(spec, {"evidence": replace(evidence, scope=changed_scope)})
    with pytest.raises(ValueError, match="scope"):
        science.predict(science.prediction_config(config), replace(predictors, scope=changed_scope))
    with pytest.raises(ValueError, match="unimplemented"):
        replace(spec, calculation="TODO")
    with pytest.raises(ValueError, match="schema"):
        replace(spec, evidence=replace(spec.evidence, object_schema="empirical-lawhood/other/evidence"))
    with pytest.raises(ValueError):
        decode_canonical_bytes(evidence.canonical_bytes().replace(MassEvidence.SCHEMA.encode(), b"empirical-lawhood/other/evidence"),
                               MassEvidence, maximum_bytes=128*1024)
    forecast = science.predict(science.prediction_config(config), predictors)
    with pytest.raises(ValueError, match="identity"):
        science.assess(config, forecast, replace(outcomes, record_id="other.outcomes"))
    with pytest.raises(ValueError, match="independent unit"):
        replace(forecast, rows=forecast.rows[:-1])


def test_largest_inputs_produce_supported_mass_without_context_rounding():
    evidence, spec, _, _, _ = operands()
    evidence = replace(evidence, observations=tuple(replace(r, initial_kg=Decimal("1e9"), added_kg=Decimal("1e9")) for r in evidence.observations))
    spec = replace(spec, evidence=evidence.identity)
    config = design.config_for(spec, evidence)
    predictors, outcomes = design.inputs_for(evidence)
    forecast = science.predict(science.prediction_config(config), predictors)
    assert all(r.final_kg == Decimal("2e9") for r in forecast.rows)
    assert all(r.disposition == "FALSIFIED" for r in science.assess(config, forecast, outcomes).rows)


def test_retained_read_preserves_adverse_findings_without_provider_or_recalculation(monkeypatch):
    from empirical_lawhood.api.mass_balance_starter import read_result
    from empirical_lawhood.execution.recursive_provider import RecursiveOperationProvider
    evidence, spec, config, predictors, outcomes = operands("adverse")
    forecast = science.predict(science.prediction_config(config), predictors)
    assessment = science.assess(config, forecast, outcomes)
    draft, _ = design.lower(spec, evidence)
    run_id = "test.mass.run"
    # Deliberately disclosed authenticated-context stand-in. Installed acceptance
    # separately exercises real receipts and the ordinary reader's custody owner.
    products = {"receipts": {}, "records": {}}
    for value in (forecast, assessment):
        node = value.config.node_id
        products["receipts"][node] = SimpleNamespace(run_id=run_id, task_id=node, operational_status=OperationalStatus.SUCCEEDED)
        products["records"][node] = {node + ".product": value}
    source_name = "experiment-source-" + sha256(evidence.record_id.encode()).hexdigest() + ".json"
    def refused(*args, **kwargs):
        pytest.fail("retained reader entered provider or scientific calculation")
    monkeypatch.setattr(science, "predict", refused)
    monkeypatch.setattr(science, "assess", refused)
    monkeypatch.setattr(RecursiveOperationProvider, "runners", refused)
    report = read_result(directory=None, artifact_writer=None, specification=spec,
        instance=SimpleNamespace(specification=spec.identity), payloads={source_name: evidence.canonical_bytes()},
        report={"run_id": run_id}, products=products, draft=draft,
        plan=SimpleNamespace(source_plan=SimpleNamespace(object_id=run_id),
                             tasks=tuple(SimpleNamespace(task_id=c.node_id) for c in (config, forecast.config))))
    assert report["claim_disposition"] == "FALSIFIED" and report["forecast_supply_disposition"] == "SATISFIED"
    assert report["counts"] == {"SATISFIED": 2, "FALSIFIED": 1, "UNEVALUABLE": 0}
    assert report["assigned_units"] == 3 and not report["scientific_reconstruction_performed"]


def test_adapter_workflow_projection_is_inert_and_has_one_owner(monkeypatch):
    import ast
    from empirical_lawhood.api.workflows import show_workflow
    from empirical_lawhood.methods.mass_balance_starter.workflow import WORKFLOW_DECLARATIONS
    from empirical_lawhood.execution.recursive_provider import RecursiveOperationProvider
    from empirical_lawhood.execution.workflow_descriptors import WorkflowDeclaration
    from scripts import generate_extension_bundle_aggregate as generator

    def refuse(*a, **kw):
        pytest.fail("discovery invoked an execution or preparation owner")
    monkeypatch.setattr(RecursiveOperationProvider, "runners", refuse)
    monkeypatch.setattr(experiment, "prepare", refuse)
    assert show_workflow("mass-balance-starter") == WORKFLOW_DECLARATIONS[0].workflow
    monkeypatch.setattr(generator, "_module_name", lambda path: path)
    monkeypatch.setattr(generator.importlib, "import_module", lambda module: SimpleNamespace(__name__=module, WORKFLOW_DECLARATIONS=WORKFLOW_DECLARATIONS))
    text = generator.render_workflow_declarations(("example.one",))
    imports = [node.module for node in ast.walk(ast.parse(text)) if isinstance(node, ast.ImportFrom)]
    assert imports == ["empirical_lawhood.execution.workflow_descriptors"]
    with pytest.raises(ValueError, match="duplicate"):
        generator.render_workflow_declarations(("example.one", "example.two"))
    with pytest.raises(ValueError, match="paths"):
        WorkflowDeclaration(replace(WORKFLOW_DECLARATIONS[0].workflow, guide="../outside.md"), "Exposed")
