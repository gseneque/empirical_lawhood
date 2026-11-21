# SPDX-License-Identifier: MPL-2.0
"""Installed paired-response preparation, custody and no-acquisition recovery."""

from dataclasses import replace
from decimal import Decimal as D
import json
from pathlib import Path
import subprocess
import sys

import pytest

from empirical_lawhood.domains.rubisco.rubisco_response.disclosed_examples import disclosed_study, disclosed_supply
from empirical_lawhood.domains.rubisco.rubisco_response.experiment_preparation import bind_response_inputs, validate_response_instance
from empirical_lawhood.domains.rubisco.rubisco_response.experiment_specification import PROTOCOL_ID, response_experiment_specification
from empirical_lawhood.domains.rubisco.rubisco_response.operation_bindings import ResponseOperationConfig, operation_declarations
from empirical_lawhood.domains.rubisco.rubisco_response.recursive_translation import scientific_work
from empirical_lawhood.domains.rubisco.rubisco_response.study import exposed_source_allocation
from empirical_lawhood.domains.rubisco.rubisco_response.study_science import ResponseAssessment
from empirical_lawhood.api.configuration import validate_configuration
from empirical_lawhood.api.experiment_preparation import experiment_preparation_report, load_experiment_inputs, load_experiment_specification, prepare_experiment
from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.design.experiment_inputs import ExperimentInputBinding, ExperimentInputSelection
from empirical_lawhood.execution.capabilities import CapabilityRegistry
from empirical_lawhood.execution.experiment_preparation import DependencyKind, ExecutionSelection
from empirical_lawhood.execution.recursive_compiler import compile_recursive_wave
from scripts.generate_rubisco_response_experiment import projections

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "programmes/biology/photosynthesis/workflows/rubisco-response"


def _execution(directory, source=None):
    # This pure authoring selection grants no execution or scientific authority.
    source = source or ObjectIdentity("source.exposed-pure-selection", "empirical-lawhood/recursive/implementation-binding",
                                      "1.0.0", "a" * 64)
    return ExecutionSelection(workers=1, environment_id="rubisco-prediction",
                              source_snapshot=source, output_root=str(directory))


def _prepare(specification, original, directory):
    inputs = bind_response_inputs(specification, {"study": original})
    return prepare_experiment(specification, scientific_inputs=inputs.scientific_inputs,
                              method_inputs=inputs.method_inputs, execution=_execution(directory))


def _compile(draft):
    declarations = operation_declarations()
    return compile_recursive_wave(draft=draft, registrations=tuple(row.registration() for row in declarations),
        registry=CapabilityRegistry("registry.rubisco-response.exposed", tuple(sorted((row.manifest() for row in declarations), key=lambda row: row.registry_id))),
        implementation_commit="a" * 40, output_codecs=declarations[0].record_codecs)


def _selection(directory, original):
    directory.mkdir()
    raw = original.canonical_bytes()
    (directory / "study.json").write_bytes(raw)
    selected = ExperimentInputSelection("selection.response-test.original", PROTOCOL_ID,
        (ExperimentInputBinding("study", original.identity, "study.json", len(raw)),))
    (directory / "sources.json").write_bytes(selected.canonical_bytes())
    return directory / "sources.json"


def test_public_projections_validate_without_claiming_external_prerequisites():
    for name, raw in projections().items():
        assert (EXAMPLE / name).read_bytes() == raw
        consumer = {"study.json": "rubisco-response-study",
                    "experiment.json": "rubisco-response-experiment",
                    "experiment-sources.json": "experiment-inputs"}[name]
        if name == "experiment-sources.json":
            continue  # The protocol-specific loader authenticates this selection below.
        report = validate_configuration(EXAMPLE / name, consumer=consumer)
        assert report["consumer_byte_ready"]
        assert not report["authority_granted"] and not report["external_prerequisites_checked"]
    specification = load_experiment_specification(EXAMPLE / "experiment.json")
    bound = load_experiment_inputs(specification, EXAMPLE / "experiment-sources.json")
    assert bound.method_inputs.study == disclosed_study()


def test_criteria_edit_keeps_original_sources_and_prediction_work(tmp_path):
    original = disclosed_study()
    first = response_experiment_specification(original)
    second = replace(first, decisions=tuple(
        replace(row, minimum_turnover_ratio=D("2")) if row.case.object_id.endswith("candidate") else row
        for row in first.decisions))
    source_path = _selection(tmp_path / "sources", original)
    before = source_path.read_bytes()
    prepared = []
    for specification in (first, second):
        bound = load_experiment_inputs(specification, source_path)
        preparation = prepare_experiment(specification, scientific_inputs=bound.scientific_inputs,
            method_inputs=bound.method_inputs, execution=_execution(tmp_path / "unentered"))
        assert preparation.executable and preparation.dependencies == ()
        assert dict(preparation.census.role_counts) == {"analytical": 1, "biological": 0, "cases": 2, "scenarios": 2}
        assert preparation.census.native_effect_count == 0
        assert dict(preparation.input_records) == {"external.rubisco-response.study": original}
        assert len(_compile(preparation.draft).execution_plan.tasks) == 2
        validate_response_instance(specification=specification, allocation=preparation.allocation,
            draft=preparation.draft, source_records=preparation.design_records)
        report = experiment_preparation_report(preparation)
        assert not report["scientific_execution_performed"]
        assert report["qualification"] == "NOT_ESTABLISHED"
        prepared.append(preparation)
    assert prepared[0].draft.fingerprint() != prepared[1].draft.fingerprint()
    assert scientific_work(prepared[0].draft, "rubisco-response.predict") == scientific_work(
        prepared[1].draft, "rubisco-response.predict")
    assert scientific_work(prepared[0].draft, "rubisco-response.assess") != scientific_work(
        prepared[1].draft, "rubisco-response.assess")
    assert source_path.read_bytes() == before
    assert (source_path.parent / "study.json").read_bytes() == original.canonical_bytes()
    assert not (tmp_path / "unentered").exists()


def test_missing_inputs_keep_declared_denominators_and_environment_dependencies():
    specification = response_experiment_specification(disclosed_study())
    preparation = prepare_experiment(specification)
    dependencies = {row.code: row.kind for row in preparation.dependencies}
    assert dependencies["rubisco.response.study.missing"] is DependencyKind.EXTERNAL_INPUT
    for name in ("environment", "source-snapshot"):
        assert dependencies["rubisco.response." + name] is DependencyKind.ENVIRONMENT
    assert dependencies["rubisco.response.output-root"] is DependencyKind.STORAGE
    assert dict(preparation.census.role_counts)["cases"] == 2
    assert dict(preparation.census.resolved_role_counts)["cases"] == 0
    assert dict(preparation.census.role_counts)["analytical"] == 1
    assert not preparation.executable and preparation.draft is None


@pytest.mark.parametrize("change", ["source", "scenarios", "units", "validation", "matrix", "criteria-admission"])
def test_changed_original_evidence_and_denominators_refuse_before_lowering(change, tmp_path):
    original = disclosed_study()
    selected = response_experiment_specification(original)
    if change == "source":
        selected = replace(selected, study=replace(selected.study, object_fingerprint="a" * 64))
    elif change == "scenarios":
        selected = replace(selected, expected_scenarios=tuple((key, ("scenario.substituted",)) for key, _ in selected.expected_scenarios))
    elif change == "units":
        selected = replace(selected, expected_analytical_unit_ids=("unit.substituted",))
    elif change == "validation":
        selected = replace(selected, acceptance=replace(selected.acceptance,
            predictive_evidence_requirement_ids=("requirement.substituted",)))
    elif change == "matrix":
        selected = replace(selected, acceptance=replace(selected.acceptance,
            matrix_handoff_requirement_id="requirement.substituted"))
    else:
        selected = replace(selected, acceptance=replace(selected.acceptance,
            criterion_admission_requirement_ids=("requirement.substituted",)))
    preparation = _prepare(selected, original, tmp_path / "unentered")
    assert not preparation.executable and preparation.draft is None
    assert any(row.code == "rubisco.response.study.selection" for row in preparation.dependencies)
    assert not (tmp_path / "unentered").exists()


def test_edited_instance_cannot_borrow_another_criterion_graph(tmp_path):
    original = disclosed_study()
    first = response_experiment_specification(original)
    second = replace(first, decisions=tuple(replace(row, minimum_turnover_ratio=D(2)) for row in first.decisions))
    a, b = (_prepare(specification, original, tmp_path / "unentered") for specification in (first, second))
    with pytest.raises(ValueError, match="source/specification lowering"):
        validate_response_instance(specification=first, allocation=a.allocation, draft=b.draft,
                                   source_records=a.design_records)


def test_unknown_failed_scenarios_remain_visible_with_no_native_effects(tmp_path):
    original = disclosed_study()
    supplies = tuple(disclosed_supply(case_role=supply.case.case_role,
        scenario_states=("AVAILABLE", "UNKNOWN", "FAILED")) for supply in original.supplies)
    original = replace(original, supplies=supplies, allocation=exposed_source_allocation(original.cases, supplies))
    specification = response_experiment_specification(original)
    preparation = _prepare(specification, original, tmp_path / "unentered")
    assert preparation.executable
    outputs = dict(preparation.census.output_counts)
    assert outputs["unknown-scenarios"] == outputs["failed-scenarios"] == 2
    assert dict(preparation.census.role_counts)["scenarios"] == 6
    assert outputs["supplied-solver-calls"] == 4
    assert preparation.census.native_effect_count == 0


def test_root_refuses_missing_original_units_and_changed_dependency_edges(tmp_path):
    original = disclosed_study()
    draft = _prepare(response_experiment_specification(original), original, tmp_path).draft
    wrong_root = replace(draft.development_study, assigned_unit_ids=("unit.substituted",))
    with pytest.raises(ValueError):
        _compile(replace(draft, development_study=wrong_root))
    with pytest.raises(ValueError):
        _compile(replace(draft, links=draft.links[:-1]))
    config = decode_canonical_bytes(draft.operations[0].config_payload.encode(), ResponseOperationConfig,
                                   maximum_bytes=None)
    with pytest.raises(ValueError, match="evidence lane"):
        replace(config, science=replace(config.science, evidence_scope="PROSPECTIVE_REQUIRED"))


def test_fresh_discovery_never_imports_molecular_backends_or_prepares_science(tmp_path):
    script = """
from dataclasses import replace
import importlib.abc
import platform
import subprocess
import sys
platform.processor()
def forbidden(*args, **kwargs):
    raise AssertionError("cold discovery attempted native entry, a prerequisite probe or preparation")
blocked = {"pybamm", "brian2", "cantera", "fipy", "grid2op", "torax", "gymtorax", "jax", "jaxlib",
           "openmm", "pdbfixer", "parmed", "pyscf", "xtb"}
class RefuseNative(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".")[0] in blocked:
            forbidden()
sys.meta_path.insert(0, RefuseNative())
subprocess.Popen = forbidden
from empirical_lawhood.execution.recursive_provider import RecursiveOperationProviderFactory, RecursiveOperationProvider
RecursiveOperationProviderFactory.build_provider = forbidden
RecursiveOperationProvider.runners = forbidden
import empirical_lawhood.api.generated_experiment_protocols as generated
generated.EXPERIMENT_PROTOCOL_DECLARATIONS = tuple(replace(row, prepare=forbidden)
    for row in generated.EXPERIMENT_PROTOCOL_DECLARATIONS)
from empirical_lawhood.api.experiment_preparation import experiment_protocols
from empirical_lawhood.api.configuration_registry import consumers_for_schema
declaration, = (row for row in experiment_protocols() if row.protocol_id == "rubisco-response-experiment-v1")
assert any(row.consumer == declaration.consumer_id for row in consumers_for_schema(declaration.specification_type.SCHEMA))
"""
    result = subprocess.run([sys.executable, "-c", script], cwd=tmp_path, capture_output=True, text=True, timeout=45)
    assert result.returncode == 0, result.stdout + result.stderr
    assert not tuple(tmp_path.iterdir())


def test_installed_programme_runs_reads_recovers_and_exports_original_custody(tmp_path, monkeypatch):
    from empirical_lawhood.api import matrix_numerical_provenance as provenance
    from empirical_lawhood.api import recursive_authoring as author, recursive_execution as execute
    from empirical_lawhood.api.recursive_contributions import export_recursive_contribution, authenticate_recursive_contribution
    from empirical_lawhood.execution.local.execution import LocalProcessExecutor
    from tests.test_rubisco_gas_contrast import _real_plane

    # Freeze one actual private-environment observation for this exposed software
    # check. No signer, biological authority or molecular backend is fabricated.
    executor = LocalProcessExecutor.execute
    source = author.implementation_binding(ROOT)
    observed = provenance.capture_matrix_provenance(project_root=ROOT)
    monkeypatch.setattr(author, "implementation_binding", lambda root, **kwargs: source)
    monkeypatch.setattr(execute, "implementation_binding", lambda root, **kwargs: source)
    monkeypatch.setattr(provenance, "capture_matrix_provenance", lambda **kwargs: observed)
    root = tmp_path / "actual-custody"
    plane = _real_plane(root)
    service = ExperimentProgrammeService(ROOT, plane)
    specification = load_experiment_specification(EXAMPLE / "experiment.json")
    inputs = load_experiment_inputs(specification, EXAMPLE / "experiment-sources.json")
    wave = root / "response-programme"
    preparation = service.prepare(specification, scientific_inputs=inputs.scientific_inputs,
        method_inputs=inputs.method_inputs, execution=_execution(root, ObjectIdentity.from_record(
            "recursive-member.implementation", source)))
    assert preparation.executable
    authored = service.author(preparation=preparation, output_dir=wave)
    assert authored["status"] == "AUTHORED" and authored["native_contact"] == "none"
    run = service.run(directory=wave, maximum_parallel_tasks=1)
    assert run["status"] == "SUCCEEDED" and run["new_native_contact_count"] == 0
    documents = [document for outputs in run["terminal_products"].values() for document in outputs.values()]
    result, = (decode_canonical_bytes((json.dumps(document, sort_keys=True, separators=(",", ":"),
        ensure_ascii=True, allow_nan=False) + "\n").encode(), ResponseAssessment, maximum_bytes=None)
        for document in documents if document["schema"] == ResponseAssessment.SCHEMA)
    assert result.complete_case_census and len(result.cases) == 2
    assert result.conditional_candidate_action == "ADVANCE"
    assert result.combined_milestone == "OPEN" and result.biological_predictive_calibration == "NOT_ESTABLISHED"
    assert specification.acceptance.matrix_handoff_requirement_id in result.remaining_requirement_ids

    def no_execution(*args, **kwargs):
        raise AssertionError("completed response custody triggered new worker execution")
    monkeypatch.setattr(LocalProcessExecutor, "execute", no_execution)
    read = service.read(directory=wave)
    assert read["terminal_products"] == run["terminal_products"]
    recovered = service.recover(directory=wave, maximum_parallel_tasks=1)
    assert recovered == run
    exported = export_recursive_contribution(directory=wave, output_dir=root / "portable",
        project_root=ROOT, artifact_writer=plane)
    assert exported["status"] == "EXPORTED" and exported["native_contact"] == "none"
    authenticated = authenticate_recursive_contribution(directory=root / "portable", artifact_writer=plane)
    manifest = authenticated[2]
    assert {row.record.object_schema for row in manifest.products} == {
        "empirical-lawhood/rubisco-response/study-predictions", ResponseAssessment.SCHEMA}
    assert len({row.producing_receipt for row in manifest.products}) == 2
    assert specification.acceptance.matrix_handoff_requirement_id in {row.requirement_id for row in manifest.remaining_requirements}

    _accept_retained_adoption(root, plane, monkeypatch, executor)


def _accept_retained_adoption(root, plane, monkeypatch, executor, *, name="adoption-programme"):
    """Also callable against a previously completed packet without producer replay."""
    from empirical_lawhood.domains.rubisco.rubisco_response.adoption import CAPABILITY, CurrentResponseUse
    from empirical_lawhood.api.domain_composition.rubisco_response.adoption import author_response_adoption
    from empirical_lawhood.api.recursive_contributions import authenticate_recursive_contribution, export_recursive_contribution
    from empirical_lawhood.api.recursive_execution import read_recursive_wave, run_recursive_wave
    from empirical_lawhood.execution.local.execution import LocalProcessExecutor

    def no_execution(*args, **kwargs):
        raise AssertionError("retained response read, authoring or recovery entered a new worker")

    monkeypatch.setattr(LocalProcessExecutor, "execute", no_execution)
    parent = root / "portable"
    original = authenticate_recursive_contribution(directory=parent, artifact_writer=plane)
    original_manifest, original_products = original[2], original[4]
    before_records = {task: {key: value.canonical_bytes() for key, value in rows.items()}
                      for task, rows in original_products["records"].items()}
    before_receipts = {task: value.canonical_bytes() for task, value in original_products["receipts"].items()}
    specification = load_experiment_specification(EXAMPLE / "experiment.json")
    current = replace(specification, decisions=tuple(
        replace(row, minimum_turnover_ratio=D("2")) if row.case.object_id.endswith("candidate") else row
        for row in specification.decisions))
    wave = root / name
    authored = author_response_adoption(parent_directory=parent, specification=current,
        project_root=ROOT, artifact_writer=plane, output_dir=wave)
    assert authored["status"] == "AUTHORED" and authored["native_contact"] == "none"

    # Exactly one newly selected pure assessment is allowed. It cannot contain
    # either original producer task, and subsequent custody access forbids workers.
    monkeypatch.setattr(LocalProcessExecutor, "execute", executor)
    run = run_recursive_wave(directory=wave, project_root=ROOT, artifact_writer=plane, maximum_parallel_tasks=1)
    monkeypatch.setattr(LocalProcessExecutor, "execute", no_execution)
    assert run["status"] == "SUCCEEDED" and run["new_native_contact_count"] == 0
    read, products, draft, _ = read_recursive_wave(directory=wave, artifact_writer=plane, include_products=True)
    assert draft.selected_operation_ids == (CAPABILITY,)
    assert tuple(products["receipts"]) == (CAPABILITY,)
    use, = products["records"][CAPABILITY].values()
    assert type(use) is CurrentResponseUse
    assert use.original_assessment.conditional_candidate_action == "ADVANCE"
    assert use.current_assessment.conditional_candidate_action == "DEPRIORITIZE"
    assert use.current_assessment.combined_milestone == "OPEN"
    assert use.original_prediction.predictions == use.current_prediction.predictions
    assert use.new_native_acquisitions == use.fresh_independent_units == 0
    assert use.configuration.parent == original_manifest
    assert read["terminal_products"] == run["terminal_products"]
    assert run_recursive_wave(directory=wave, project_root=ROOT, artifact_writer=plane,
                              maximum_parallel_tasks=1) == run
    exported = export_recursive_contribution(directory=wave, output_dir=root / (name + "-portable"),
        project_root=ROOT, artifact_writer=plane)
    assert exported["status"] == "EXPORTED" and exported["native_contact"] == "none"
    accepted = authenticate_recursive_contribution(directory=root / (name + "-portable"), artifact_writer=plane)
    assert accepted[2].predecessors == (ObjectIdentity.from_record(original_manifest.contribution_id, original_manifest),)
    assert len(accepted[2].products) == 1
    assert accepted[2].products[0].record == use.identity
    assert accepted[2].products[0].producing_receipt not in {
        product.producing_receipt for product in original_manifest.products}
    assert current.acceptance.matrix_handoff_requirement_id in {
        row.requirement_id for row in accepted[2].remaining_requirements}
    original_after = authenticate_recursive_contribution(directory=parent, artifact_writer=plane)[4]
    assert before_records == {task: {key: value.canonical_bytes() for key, value in rows.items()}
                              for task, rows in original_after["records"].items()}
    assert before_receipts == {task: value.canonical_bytes() for task, value in original_after["receipts"].items()}
    from tests.test_rubisco_response_retained_inquiry import assert_actual_retained_projection
    assert_actual_retained_projection(root / "response-programme", plane, expected_attempts=2)
    assert_actual_retained_projection(wave, plane, expected_attempts=1)
    return {"status": "ACCEPTED_EXPOSED_SOFTWARE_ONLY", "original_contribution": original_manifest.fingerprint(),
            "current_contribution": accepted[2].fingerprint(), "current_action": use.current_assessment.conditional_candidate_action,
            "new_native_acquisitions": use.new_native_acquisitions, "fresh_independent_units": use.fresh_independent_units,
            "selected_tasks": list(draft.selected_operation_ids), "combined_milestone": use.current_assessment.combined_milestone}
