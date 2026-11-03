# SPDX-License-Identifier: MPL-2.0
"""Public declaration/specification preparation; exposed software checks only."""

from dataclasses import dataclass, replace
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import ClassVar

import pytest
from typer.testing import CliRunner

from empirical_lawhood.adapters.methods.matrix_factor_response.experiment_specification import (
    selected_deanneal_specification,
)
from empirical_lawhood.api.configuration import validate_configuration
from empirical_lawhood.api.experiment_preparation import (
    experiment_preparation_report,
    experiment_protocols,
    load_experiment_inputs,
    load_experiment_specification,
    prepare_experiment,
)
from empirical_lawhood.cli.app import app
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.planning.experiment_inputs import ExperimentInputBinding, ExperimentInputSelection
from empirical_lawhood.runtime.experiment_preparation import (
    DependencyKind,
    ExecutionSelection,
    ExperimentCensus,
    ExperimentDependency,
    ExperimentPreparation,
    ExperimentProtocolDeclaration,
    PreparedExperimentInputs,
)


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = ROOT / "programmes/foundations/emergent-structure/records/matrix-e2-e3-candidate/candidate-design02.json"
PROTOCOL = PROTOCOL_PATH.read_bytes()


def _specification(alternative=False):
    specification = selected_deanneal_specification(protocol_sha256=sha256(PROTOCOL).hexdigest())
    if not alternative:
        return specification
    counts = {"TRAIN": 12, "CALIBRATION": 20, "EVALUATION": 8, "TRANSFER_NEARBY": 2, "TRANSFER_SHIFTED": 2}
    return replace(specification, specification_id="fixture.public.response-error.alternative",
        populations=tuple(replace(population, expected_units=counts[population.role])
            for population in specification.populations),
        assessment=replace(specification.assessment, minimum_usable_units=8),
        evidence_scope="EXPOSED_CONFORMANCE", calibration_target_view="PRIMARY")


def _copied_input(tmp_path, alternative=False):
    specification = _specification(alternative)
    destination = tmp_path / "specification.json"
    destination.write_bytes(specification.canonical_bytes())
    return specification, destination


def _report(result):
    assert result.exit_code == 0, result.stdout + result.stderr
    return json.loads(result.stdout)


def _assert_no_scientific_entry(report):
    assert report["native_contact"] == "NONE"
    assert report["scientific_execution_performed"] is False
    assert report["scientific_authority"] == "NONE"
    assert report["qualification"] == "NOT_ESTABLISHED"
    assert report["executable"] is False


@pytest.mark.parametrize("alternative", (False, True), ids=("selected64", "exposed12-20-8"))
def test_public_decode_config_and_explanation_preserve_specification_and_complete_census(tmp_path, alternative):
    specification, source = _copied_input(tmp_path, alternative)
    original = source.read_bytes()
    assert load_experiment_specification(source) == specification
    validated = validate_configuration(source, consumer="matrix-response-experiment")
    assert validated["consumer_byte_ready"]
    assert not validated["authority_granted"]
    assert not validated["external_prerequisites_checked"]
    args = ["campaign", "experiment-explain", "--input", str(source)]
    first = _report(CliRunner().invoke(app, args))
    assert _report(CliRunner().invoke(app, args)) == first
    assert first == experiment_preparation_report(prepare_experiment(specification))
    _assert_no_scientific_entry(first)
    assert first["specification"] == specification.identity.to_document()
    assert first["allocation"] is None and first["draft"] is None
    assert set(first["census"]["resolved_roles"].values()) == {0}
    assert first["census"]["native_effects"] == (0 if alternative else 256)
    if alternative:
        assert first["census"]["roles"] == {
            "train": 12, "calibration": 20, "evaluation": 8, "transfer_nearby": 2, "transfer_shifted": 2}
        assert first["census"]["outputs"]["calibration-rank"] == 20
        assert first["census"]["outputs"]["minimum-primary-successes"] == 8
        assert first["census"]["outputs"]["point-forecast-endpoints"] == 1260
        assert first["census"]["outputs"]["response-view-endpoints"] == 1200
    else:
        assert first["census"]["roles"] == {
            "train": 64, "calibration": 64, "evaluation": 64, "transfer_nearby": 64, "transfer_shifted": 64}
        assert first["census"]["outputs"]["calibration-rank"] == 62
        assert first["census"]["outputs"]["minimum-primary-successes"] == 43
        assert first["census"]["outputs"]["point-forecast-endpoints"] == 5760
    assert source.read_bytes() == original
    assert tuple(tmp_path.iterdir()) == (source,)


def test_selected_public_report_names_closed_missing_inputs_and_distinct_scientific_authority_choices(tmp_path):
    specification = replace(_specification(), calibration_target_view=None)
    source = tmp_path / "unselected-calibration-view.json"
    source.write_bytes(specification.canonical_bytes())
    report = _report(CliRunner().invoke(app, ["campaign", "experiment-explain", "--input", str(source)]))
    findings = {row["code"]: row for row in report["dependencies"]}
    expected = {
        "matrix.e3.protocol.0": "EXTERNAL_INPUT",
        "matrix.e3.environment": "ENVIRONMENT",
        "matrix.e3.source-snapshot": "ENVIRONMENT",
        "matrix.e3.output-root": "STORAGE",
        "matrix.e3.calibration-target-view": "SCIENTIFIC_EVIDENCE",
        "matrix.e3.protected-selection": "EXTERNAL_INPUT",
    }
    assert expected.items() <= {code: row["kind"] for code, row in findings.items()}.items()
    assert "matrix.e3.prospective-operation-lowering" not in findings
    assert list(findings) == sorted(findings)
    assert findings["matrix.e3.protected-selection"]["source_key"] == "protected-selection"
    assert all(row["detail"] for row in findings.values())
    _assert_no_scientific_entry(report)


@pytest.mark.parametrize("filename", ("specification.json", "alternative.json"))
def test_shipped_examples_are_copyable_public_inputs_with_an_explicit_calibration_choice(tmp_path, filename):
    original_path = ROOT / "programmes/foundations/emergent-structure/workflows/matrix-response-experiment" / filename
    original = original_path.read_bytes()
    source = tmp_path / filename
    source.write_bytes(original)
    specification = load_experiment_specification(source)
    assert specification.calibration_target_view in {"PRIMARY", "MAX_PAIRED_VIEWS"}
    if filename == "specification.json":
        assert specification.calibration_target_view == "MAX_PAIRED_VIEWS"
    assert validate_configuration(source, consumer="matrix-response-experiment")["consumer_byte_ready"]
    report = _report(CliRunner().invoke(app, ["campaign", "experiment-explain", "--input", str(source)]))
    assert report["specification"] == specification.identity.to_document()
    assert "matrix.e3.calibration-target-view" not in {row["code"] for row in report["dependencies"]}
    _assert_no_scientific_entry(report)
    assert original_path.read_bytes() == source.read_bytes() == original


@pytest.mark.parametrize("alternative", (False, True), ids=("selected64", "exposed12-20-8"))
def test_public_prepare_writes_only_explicit_new_report_and_refuses_overwrite(tmp_path, alternative):
    specification, source = _copied_input(tmp_path, alternative)
    destination = tmp_path / "preparation.json"
    custody_root = tmp_path / "unentered-scientific-storage"
    args = ["campaign", "experiment-prepare", "--input", str(source), "--output", str(destination),
        "--protocol", str(PROTOCOL_PATH), "--environment-id", "fixture.locked-main",
        "--output-root", str(custody_root), "--workers", "2"]
    report = _report(CliRunner().invoke(app, args))
    assert report.pop("preparation_report") == str(destination)
    assert json.loads(destination.read_bytes()) == report
    assert report == experiment_preparation_report(prepare_experiment(specification, protocol_bytes=PROTOCOL,
        execution=ExecutionSelection(workers=2, environment_id="fixture.locked-main", output_root=str(custody_root))))
    codes = {row["code"] for row in report["dependencies"]}
    assert "matrix.e3.protocol.0" not in codes
    assert "matrix.e3.environment" not in codes
    assert "matrix.e3.output-root" not in codes
    assert "matrix.e3.source-snapshot" in codes  # A declared environment is not a frozen source.
    _assert_no_scientific_entry(report)
    before = {path.name: path.read_bytes() for path in tmp_path.iterdir()}
    refused = CliRunner().invoke(app, args)
    assert refused.exit_code == 2
    assert {path.name: path.read_bytes() for path in tmp_path.iterdir()} == before
    assert source.read_bytes() == specification.canonical_bytes()
    assert not custody_root.exists()


def test_public_explanation_retains_only_explicit_operational_attempt(tmp_path):
    _, source = _copied_input(tmp_path)
    retained = tmp_path / "explicit-attempt"
    report = _report(CliRunner().invoke(app, ["campaign", "experiment-explain", "--input", str(source),
        "--attempt-dir", str(retained)]))
    _assert_no_scientific_entry(report)
    invocation = json.loads((retained / "invocation.json").read_bytes())
    assert invocation["operation"] == "campaign experiment-explain"
    assert invocation["native_contact"] == "none"
    assert invocation["scientific_adjudication"] == "NOT_PERFORMED"
    assert invocation["handler_entered"] and invocation["operation_completed"]
    assert (retained / "input.json").read_bytes() == source.read_bytes()


@pytest.mark.parametrize("field,changed", (
    ("opportunity_baseline", "median of log-transformed TRAIN labels"),
    ("algorithm", "choose lambda after confirmation outcomes"),
    ("strong_conventional_baseline", "omit the ALL_ORIGIN comparison"),
))
def test_rehashed_protocol_cannot_replace_selected_scientific_rules(field, changed):
    document = json.loads(PROTOCOL)
    document["prediction"][field] = changed
    mutated = json.dumps(document, sort_keys=True, separators=(",", ":")).encode()
    specification = replace(_specification(), protocol_sha256=sha256(mutated).hexdigest())
    report = experiment_preparation_report(prepare_experiment(specification, protocol_bytes=mutated))
    assert any(row["code"].startswith("matrix.e3.protocol.") for row in report["dependencies"])
    _assert_no_scientific_entry(report)


@dataclass(frozen=True)
class OtherSpecification(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/testing/other-experiment-specification"
    specification_id: str
    selected_units: int

    def __post_init__(self):
        validate_stable_id(self.specification_id)
        if type(self.selected_units) is not int or self.selected_units < 1:
            raise ValueError("other protocol requires a complete positive unit count")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.specification_id, self)


def test_generic_schema_dispatch_uses_installed_declaration_without_matrix_wiring(tmp_path, monkeypatch):
    from empirical_lawhood.adapters.composition import generated_extension_bundles as generated

    calls = []

    def prepare_other(specification, *, scientific_inputs, execution, protocol_bytes):
        calls.append((specification, scientific_inputs, execution, protocol_bytes))
        census = ExperimentCensus((("other", specification.selected_units),), (("other", 0),),
            (("other-assessment", 1),), (("other-result", 1),), 0)
        dependency = ExperimentDependency("other.source-missing", DependencyKind.EXTERNAL_INPUT,
            "The other domain's selected observations are unavailable.", "other-source")
        return ExperimentPreparation(specification.identity, census, (dependency,))

    declaration = ExperimentProtocolDeclaration("fixture.other-domain", OtherSpecification, prepare_other,
        "fixture-other-experiment")
    monkeypatch.setattr(generated, "EXPERIMENT_PROTOCOL_DECLARATIONS", (declaration,))
    specification = OtherSpecification("fixture.other-specification", 3)
    source = tmp_path / "other.json"
    source.write_bytes(specification.canonical_bytes())
    assert experiment_protocols() == (declaration,)
    assert validate_configuration(source, consumer=declaration.consumer_id)["consumer_byte_ready"]
    assert not calls  # Strict configuration validation does not prepare science.
    assert load_experiment_specification(source) == specification
    assert not calls
    report = experiment_preparation_report(prepare_experiment(specification, scientific_inputs={"opaque": "input"},
        execution=ExecutionSelection(workers=1), protocol_bytes=b"explicit other protocol"))
    assert len(calls) == 1 and calls[0][0] == specification
    assert calls[0][1] == {"opaque": "input"} and calls[0][3] == b"explicit other protocol"
    assert report["census"]["roles"] == {"other": 3}
    assert report["dependencies"][0]["code"] == "other.source-missing"
    _assert_no_scientific_entry(report)


def test_undeclared_schema_or_wrong_returned_identity_cannot_select_scientific_code(tmp_path, monkeypatch):
    from empirical_lawhood.adapters.composition import generated_extension_bundles as generated

    specification = OtherSpecification("fixture.other-specification", 3)
    source = tmp_path / "undeclared.json"
    source.write_bytes(specification.canonical_bytes())
    with pytest.raises(ValueError):
        load_experiment_specification(source)
    with pytest.raises(ValueError, match="installed domain protocol"):
        prepare_experiment(specification)

    def substituted(specification, **kwargs):
        foreign = replace(specification, specification_id="fixture.substituted-specification")
        return ExperimentPreparation(foreign.identity, ExperimentCensus((), (), (), (), 0), ())

    declaration = ExperimentProtocolDeclaration("fixture.other-domain", OtherSpecification, substituted,
        "fixture-other-experiment")
    monkeypatch.setattr(generated, "EXPERIMENT_PROTOCOL_DECLARATIONS", (declaration,))
    with pytest.raises(ValueError, match="substitutes its selected specification"):
        prepare_experiment(specification)


def test_fresh_protocol_discovery_is_static_and_never_prepares_or_builds_science(tmp_path):
    script = '''
from dataclasses import replace
import importlib.abc
import json
import platform
import subprocess
import sys

# Cache the ordinary host-description probe before forbidding scientific launches.
# h5py reads this cached platform fact during static aggregate imports.
platform.processor()

def forbidden(*args, **kwargs):
    raise AssertionError("static discovery attempted scientific preparation or execution")
blocked = {"pybamm", "brian2", "cantera", "fipy", "grid2op", "torax", "gymtorax", "jax", "jaxlib", "openmm", "pdbfixer", "parmed"}
class NativeImportRefusal(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".")[0] in blocked:
            forbidden()
sys.meta_path.insert(0, NativeImportRefusal())
subprocess.Popen = forbidden
from empirical_lawhood.runtime.recursive_provider import RecursiveOperationProviderFactory, RecursiveOperationProvider
RecursiveOperationProviderFactory.build_provider = forbidden
RecursiveOperationProvider.runners = forbidden
from empirical_lawhood.adapters.composition import generated_extension_bundles as generated
generated.EXPERIMENT_PROTOCOL_DECLARATIONS = tuple(replace(declaration, prepare=forbidden)
    for declaration in generated.EXPERIMENT_PROTOCOL_DECLARATIONS)
from empirical_lawhood.api.experiment_preparation import experiment_protocols
from empirical_lawhood.api.configuration_registry import consumers_for_schema
declarations = experiment_protocols()
for declaration in declarations:
    assert any(value.consumer == declaration.consumer_id
        for value in consumers_for_schema(declaration.specification_type.SCHEMA))
print(json.dumps([declaration.protocol_id for declaration in declarations]))
'''
    returned = subprocess.run([sys.executable, "-c", script], cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src"), "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True, text=True, check=False)
    assert returned.returncode == 0, returned.stderr
    assert json.loads(returned.stdout) == [declaration.protocol_id for declaration in experiment_protocols()]
    assert not tuple(tmp_path.iterdir())


@dataclass(frozen=True, slots=True)
class OtherSource(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/testing/other-experiment-source"
    source_id: str
    observations: tuple[int, ...]


def _write_source_selection(directory, specification, records):
    bindings = []
    for index, (key, record) in enumerate(sorted(records.items())):
        path = directory / ("source-" + str(index) + ".json")
        payload = record.canonical_bytes()
        path.write_bytes(payload)
        bindings.append(ExperimentInputBinding(key, ObjectIdentity.from_record("selected-source." + key, record),
            path.name, len(payload)))
    declaration, = (row for row in experiment_protocols() if type(specification) is row.specification_type)
    selection = ExperimentInputSelection("selection.fixture.public-inputs", declaration.protocol_id, tuple(bindings))
    path = directory / "sources.json"
    path.write_bytes(selection.canonical_bytes())
    return selection, path


def _other_input_scope(tmp_path, monkeypatch):
    from empirical_lawhood.adapters.composition import generated_extension_bundles as generated

    calls = []
    method_handle = object()

    def bind_other(specification, records):
        calls.append((specification, dict(records)))
        return PreparedExperimentInputs({}, method_handle)

    def forbidden_prepare(*_args, **_kwargs):
        raise AssertionError("source decoding prepared or executed scientific methods")

    declaration = ExperimentProtocolDeclaration("fixture.other-source-protocol", OtherSpecification,
        forbidden_prepare, "fixture-other-source-experiment", input_record_types=(OtherSource,), bind_inputs=bind_other)
    monkeypatch.setattr(generated, "EXPERIMENT_PROTOCOL_DECLARATIONS", (declaration,))
    specification = OtherSpecification("fixture.other-source-specification", 3)
    records = {"other-observations": OtherSource("fixture.other-observations", (2, 3, 5))}
    selection, path = _write_source_selection(tmp_path, specification, records)
    return specification, records, selection, path, calls, method_handle


def test_generic_input_decode_dispatches_one_domain_callback_after_exact_byte_authentication(tmp_path, monkeypatch):
    specification, records, selection, path, calls, method_handle = _other_input_scope(tmp_path, monkeypatch)
    before = {member.name: member.read_bytes() for member in tmp_path.iterdir()}
    resolved = load_experiment_inputs(specification, path)
    assert calls == [(specification, records)]
    assert resolved.scientific_inputs == {} and resolved.method_inputs is method_handle
    assert {member.name: member.read_bytes() for member in tmp_path.iterdir()} == before
    assert selection.protocol_id == "fixture.other-source-protocol"


def test_generic_source_selection_is_reused_unchanged_after_supported_specification_id_edit(tmp_path, monkeypatch):
    specification, records, _, path, calls, method_handle = _other_input_scope(tmp_path, monkeypatch)
    original = path.read_bytes()
    changed = replace(specification, specification_id="fixture.other-source-renamed-question")
    assert changed.identity != specification.identity
    resolved = load_experiment_inputs(changed, path)
    assert calls == [(changed, records)]
    assert resolved.method_inputs is method_handle and resolved.scientific_inputs == {}
    assert path.read_bytes() == original


@pytest.mark.parametrize("mutation, message", (
    ("wrong-protocol", "protocol"),
    ("unknown-schema", "exact codec/revision"),
    ("wrong-version", "exact codec/revision"),
    ("changed-bytes", "selected bytes"),
    ("noncanonical-bytes", "canonical"),
    ("payload-schema", "schema"),
))
def test_generic_input_substitutions_refuse_before_domain_binding(tmp_path, monkeypatch, mutation, message):
    specification, _, selection, path, calls, _ = _other_input_scope(tmp_path, monkeypatch)
    binding = selection.bindings[0]
    member = tmp_path / binding.relative_path
    if mutation == "wrong-protocol":
        selection = replace(selection, protocol_id="fixture.another-source-protocol")
    elif mutation in ("unknown-schema", "wrong-version"):
        identity = replace(binding.identity, **({"object_schema": "empirical-lawhood/testing/undeclared-source"}
            if mutation == "unknown-schema" else {"object_version": "2.0.0"}))
        selection = replace(selection, bindings=(replace(binding, identity=identity),))
    elif mutation == "changed-bytes":
        member.write_bytes(OtherSource("fixture.other-observations", (2, 3, 7)).canonical_bytes())
    else:
        document = json.loads(member.read_bytes())
        if mutation == "payload-schema":
            document["schema"] = "empirical-lawhood/testing/undeclared-source"
            payload = (json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n").encode()
        else:
            payload = json.dumps(document, indent=2).encode()
        member.write_bytes(payload)
        selection = replace(selection, bindings=(replace(binding,
            identity=replace(binding.identity, object_fingerprint=sha256(payload).hexdigest()),
            maximum_bytes=len(payload)),))
    path.write_bytes(selection.canonical_bytes())
    with pytest.raises(ValueError, match=message):
        load_experiment_inputs(specification, path)
    assert not calls


@pytest.mark.parametrize("location", ("selection", "member", "member-parent"))
def test_generic_input_selection_and_members_refuse_symbolic_links(tmp_path, monkeypatch, location):
    specification, _, selection, path, calls, _ = _other_input_scope(tmp_path, monkeypatch)
    if location == "selection":
        linked = tmp_path / "linked-sources.json"
        linked.symlink_to(path)
        path = linked
    elif location == "member":
        linked = tmp_path / "linked-source.json"
        linked.symlink_to(tmp_path / selection.bindings[0].relative_path)
        selection = replace(selection, bindings=(replace(selection.bindings[0], relative_path=linked.name),))
        path.write_bytes(selection.canonical_bytes())
    else:
        real = tmp_path / "real-members"
        real.mkdir()
        member = tmp_path / selection.bindings[0].relative_path
        member.rename(real / member.name)
        linked = tmp_path / "linked-members"
        linked.symlink_to(real, target_is_directory=True)
        selection = replace(selection, bindings=(replace(selection.bindings[0], relative_path="linked-members/" + member.name),))
        path.write_bytes(selection.canonical_bytes())
    with pytest.raises(ValueError, match="symbolic links"):
        load_experiment_inputs(specification, path)
    assert not calls


@pytest.mark.parametrize("relative_path", ("../outside.json", "/absolute/source.json", "child/../../outside.json"))
def test_generic_input_path_traversal_refuses_during_strict_selection_decode(tmp_path, monkeypatch, relative_path):
    specification, _, selection, path, calls, _ = _other_input_scope(tmp_path, monkeypatch)
    document = selection.to_document()
    document["value"]["bindings"][0]["value"]["relative_path"] = relative_path
    path.write_bytes((json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n").encode())
    with pytest.raises(ValueError):
        load_experiment_inputs(specification, path)
    assert not calls


def test_generic_input_explicit_byte_bound_refuses_before_domain_binding(tmp_path, monkeypatch):
    from empirical_lawhood.infrastructure.bounded_io import BoundedFileIOError

    specification, _, selection, path, calls, _ = _other_input_scope(tmp_path, monkeypatch)
    binding = selection.bindings[0]
    path.write_bytes(replace(selection, bindings=(replace(binding, maximum_bytes=binding.maximum_bytes - 1),)).canonical_bytes())
    with pytest.raises(BoundedFileIOError, match="byte limit"):
        load_experiment_inputs(specification, path)
    assert not calls


def test_generic_input_callback_must_return_the_registered_typed_handle(tmp_path, monkeypatch):
    from empirical_lawhood.adapters.composition import generated_extension_bundles as generated

    specification, _, _, path, _, _ = _other_input_scope(tmp_path, monkeypatch)
    declaration = generated.EXPERIMENT_PROTOCOL_DECLARATIONS[0]
    monkeypatch.setattr(generated, "EXPERIMENT_PROTOCOL_DECLARATIONS",
        (replace(declaration, bind_inputs=lambda _specification, _records: {}),))
    with pytest.raises(TypeError, match="typed handle"):
        load_experiment_inputs(specification, path)


@pytest.mark.parametrize("train_count,cal_count,eval_count,minimum_usable,rank,threshold,tasks", (
    (12, 20, 8, 8, 20, 8, 61),
    (64, 64, 64, 58, 62, 43, 261),
), ids=("exposed12-20-8", "exposed64-64-64"))
def test_complete_exposed_source_banks_prepare_through_public_cli_without_scientific_contact(
        tmp_path, monkeypatch, train_count, cal_count, eval_count, minimum_usable, rank, threshold, tasks):
    from empirical_lawhood.adapters.methods.matrix_factor_response import experiment_methods as science
    from empirical_lawhood.api.recursive_authoring import implementation_binding
    from empirical_lawhood.runtime.recursive_provider import RecursiveOperationProviderFactory
    from tests.test_matrix_experiment_methods import fixture, selected_input_records

    specification, source_inputs, _, method_inputs = fixture(
        train_count=train_count, cal_count=cal_count, eval_count=eval_count, minimum_usable=minimum_usable)
    source = tmp_path / "specification.json"
    source.write_bytes(specification.canonical_bytes())
    _, selection_path = _write_source_selection(tmp_path, specification, selected_input_records(source_inputs, method_inputs))
    # This is an actual observation of the selected source, including dirtiness.
    # Preparation reads its identity; worker acceptance remains a separate check.
    binding = implementation_binding(ROOT)
    snapshot_path = tmp_path / "implementation.json"
    snapshot_path.write_bytes(binding.canonical_bytes())
    custody_root = tmp_path / "unentered-custody"
    destination = tmp_path / "prepared.json"

    def forbidden(*_args, **_kwargs):
        raise AssertionError("public source preparation constructed or executed science")

    monkeypatch.setattr(science, "fit_models", forbidden)
    monkeypatch.setattr(science.numerical, "fit_standardized_ridge", forbidden)
    monkeypatch.setattr(RecursiveOperationProviderFactory, "build_provider", forbidden)
    arguments = ["--input", str(source), "--protocol", str(PROTOCOL_PATH), "--sources", str(selection_path),
        "--source-snapshot", str(snapshot_path), "--environment-id", "fixture.locked-main",
        "--output-root", str(custody_root), "--workers", "2"]
    before = {member.name: member.read_bytes() for member in tmp_path.iterdir()}
    explained = _report(CliRunner().invoke(app, ["campaign", "experiment-explain", *arguments]))
    assert explained["executable"] is True and explained["dependencies"] == []
    assert explained["census"]["roles"] == explained["census"]["resolved_roles"] == {
        "train": train_count, "calibration": cal_count, "evaluation": eval_count,
        "transfer_nearby": 2, "transfer_shifted": 2}
    assert explained["census"]["operations"] == {
        "fit": 1, "freeze": 2, "forecast": cal_count + eval_count, "observe": cal_count + eval_count,
        "calibrate": 1, "evaluate": 1}
    assert explained["census"]["native_effects"] == 0
    assert explained["census"]["outputs"]["calibration-rank"] == rank
    assert explained["census"]["outputs"]["minimum-primary-successes"] == threshold
    assert explained["native_contact"] == "NONE" and explained["scientific_execution_performed"] is False
    assert explained["scientific_authority"] == "NONE" and explained["qualification"] == "NOT_ESTABLISHED"
    assert len(explained["draft"]["value"]["operations"]) == tasks
    assert {member.name: member.read_bytes() for member in tmp_path.iterdir()} == before
    prepared = _report(CliRunner().invoke(app, ["campaign", "experiment-prepare", *arguments,
        "--output", str(destination)]))
    assert prepared.pop("preparation_report") == str(destination)
    assert prepared == explained == json.loads(destination.read_bytes())
    assert not custody_root.exists()
    assert {member.name: member.read_bytes() for member in tmp_path.iterdir() if member != destination} == before


def test_public_cli_wrong_source_protocol_refuses_before_creating_preparation_report(tmp_path):
    from tests.test_matrix_experiment_methods import fixture, selected_input_records

    specification, source_inputs, _, method_inputs = fixture()
    source = tmp_path / "specification.json"
    source.write_bytes(specification.canonical_bytes())
    selection, selection_path = _write_source_selection(tmp_path, specification, selected_input_records(source_inputs, method_inputs))
    selection_path.write_bytes(replace(selection, protocol_id="fixture.another-public-protocol").canonical_bytes())
    destination = tmp_path / "refused-report.json"
    refused = CliRunner().invoke(app, ["campaign", "experiment-prepare", "--input", str(source),
        "--sources", str(selection_path), "--output", str(destination)])
    assert refused.exit_code == 2, refused.stdout + refused.stderr
    assert "protocol" in refused.stderr
    assert not destination.exists()


def test_matrix_source_selection_is_reused_unchanged_after_supported_question_edit(tmp_path, monkeypatch):
    from empirical_lawhood.adapters.methods.matrix_factor_response import experiment_methods as science
    from empirical_lawhood.api.recursive_authoring import implementation_binding
    from tests.test_matrix_experiment_methods import fixture, selected_input_records

    specification, source_inputs, _, method_inputs = fixture()
    source = tmp_path / "specification.json"
    source.write_bytes(specification.canonical_bytes())
    _, selection_path = _write_source_selection(tmp_path, specification, selected_input_records(source_inputs, method_inputs))
    snapshot_path = tmp_path / "implementation.json"
    snapshot_path.write_bytes(implementation_binding(ROOT).canonical_bytes())
    arguments = ["campaign", "experiment-explain", "--input", str(source), "--protocol", str(PROTOCOL_PATH),
        "--sources", str(selection_path), "--source-snapshot", str(snapshot_path),
        "--environment-id", "fixture.locked-main", "--output-root", str(tmp_path / "unentered-custody"), "--workers", "1"]

    def forbidden(*_args, **_kwargs):
        raise AssertionError("editing an exposed question fitted or executed scientific methods")

    monkeypatch.setattr(science, "fit_models", forbidden)
    first = _report(CliRunner().invoke(app, arguments))
    retained_bytes = {member.name: member.read_bytes() for member in tmp_path.iterdir() if member != source}
    changed = replace(specification, specification_id="fixture.public.matrix.changed-question",
        question=specification.question + " with a separately named exposed conformance question")
    source.write_bytes(changed.canonical_bytes())
    second = _report(CliRunner().invoke(app, arguments))
    assert first["executable"] and second["executable"]
    assert first["dependencies"] == second["dependencies"] == []
    assert first["specification"] == specification.identity.to_document()
    assert second["specification"] == changed.identity.to_document()
    assert first["allocation"] != second["allocation"]
    assert first["draft"] != second["draft"]
    assert first["census"] == second["census"]
    assert {member.name: member.read_bytes() for member in tmp_path.iterdir() if member != source} == retained_bytes
    assert second["scientific_execution_performed"] is False
    assert second["scientific_authority"] == "NONE" and second["qualification"] == "NOT_ESTABLISHED"


def test_public_partial_source_selection_reports_missing_campaign_bank_and_execution_choices_together(tmp_path, monkeypatch):
    from empirical_lawhood.adapters.methods.matrix_factor_response import experiment_methods as science
    from tests.test_matrix_experiment_methods import fixture, selected_input_records

    specification, source_inputs, _, method_inputs = fixture()
    records = selected_input_records(source_inputs, method_inputs)
    del records["campaign"]
    del records["evaluation-outcomes"]
    _, selection_path = _write_source_selection(tmp_path, specification, records)

    def forbidden(*_args, **_kwargs):
        raise AssertionError("incomplete public source preparation fitted scientific methods")

    monkeypatch.setattr(science, "fit_models", forbidden)
    resolved = load_experiment_inputs(specification, selection_path)
    prepared = prepare_experiment(specification, scientific_inputs=resolved.scientific_inputs,
        method_inputs=resolved.method_inputs, protocol_bytes=PROTOCOL)
    report = experiment_preparation_report(prepared)
    dependencies = {row["code"]: row["kind"] for row in report["dependencies"]}
    assert {
        "matrix.e3.campaign": "EXTERNAL_INPUT", "matrix.e3.evaluation-outcomes": "EXTERNAL_INPUT",
        "matrix.e3.environment": "ENVIRONMENT", "matrix.e3.source-snapshot": "ENVIRONMENT",
        "matrix.e3.output-root": "STORAGE",
    }.items() <= dependencies.items()
    assert report["census"]["roles"] == report["census"]["resolved_roles"]
    assert report["draft"] is None
    _assert_no_scientific_entry(report)


def test_public_count_and_unit_selection_edit_reuses_original_source_bindings_and_derives_complete_graph(tmp_path, monkeypatch):
    from empirical_lawhood.adapters.methods.matrix_factor_response import experiment_methods as science
    from empirical_lawhood.api.recursive_authoring import implementation_binding
    from tests.test_matrix_experiment_methods import fixture, selected_input_records

    specification, source_inputs, _, method_inputs = fixture()
    source = tmp_path / "specification.json"
    source.write_bytes(specification.canonical_bytes())
    _, selection_path = _write_source_selection(tmp_path, specification, selected_input_records(source_inputs, method_inputs))
    snapshot_path = tmp_path / "implementation.json"
    snapshot_path.write_bytes(implementation_binding(ROOT).canonical_bytes())

    def forbidden(*_args, **_kwargs):
        raise AssertionError("public design editing fitted or executed scientific methods")

    monkeypatch.setattr(science, "fit_models", forbidden)
    arguments = ["campaign", "experiment-explain", "--input", str(source), "--sources", str(selection_path),
        "--source-snapshot", str(snapshot_path), "--protocol", str(PROTOCOL_PATH),
        "--environment-id", "fixture.locked-main", "--output-root", str(tmp_path / "unentered-custody"), "--workers", "1"]
    original = _report(CliRunner().invoke(app, arguments))
    retained_bytes = {member.name: member.read_bytes() for member in tmp_path.iterdir() if member != source}
    counts = {"TRAIN": 6, "CALIBRATION": 16, "EVALUATION": 8, "TRANSFER_NEARBY": 2, "TRANSFER_SHIFTED": 2}
    changed = replace(specification, specification_id="fixture.public.matrix.selected-six-sixteen-eight",
        populations=tuple(replace(population, expected_units=counts[population.role],
            unit_ids=source_inputs[population.source_key].unit_ids()[:counts[population.role]])
            for population in specification.populations),
        assessment=replace(specification.assessment, minimum_usable_units=8))
    source.write_bytes(changed.canonical_bytes())
    report = _report(CliRunner().invoke(app, arguments))
    assert report["executable"] and report["dependencies"] == []
    assert report["specification"] == changed.identity.to_document()
    assert report["allocation"] != original["allocation"] and report["draft"] != original["draft"]
    assert report["census"]["roles"] == report["census"]["resolved_roles"] == {
        "train": 6, "calibration": 16, "evaluation": 8, "transfer_nearby": 2, "transfer_shifted": 2}
    assert report["census"]["operations"] == {
        "fit": 1, "freeze": 2, "forecast": 24, "observe": 24, "calibrate": 1, "evaluate": 1}
    assert len(report["draft"]["value"]["operations"]) == 53
    # ceil(17 * 19/20) is17. It exceeds CAL16: the method retains an infinite
    # bound, rather than silently selecting the largest finite score at16.
    assert report["census"]["outputs"]["calibration-rank"] == 17
    assert report["census"]["outputs"]["minimum-primary-successes"] == 8
    assert report["census"]["outputs"]["evaluation-unit-decisions"] == 8
    assert report["census"]["outputs"]["point-forecast-endpoints"] == 1080
    assert report["census"]["outputs"]["response-view-endpoints"] == 900
    assert {member.name: member.read_bytes() for member in tmp_path.iterdir() if member != source} == retained_bytes
    assert report["scientific_execution_performed"] is False
    assert report["scientific_authority"] == "NONE" and report["qualification"] == "NOT_ESTABLISHED"


@pytest.mark.parametrize("command", ("experiment-explain", "experiment-prepare"))
def test_public_cli_oversize_source_refuses_cleanly_without_creating_preparation_report(tmp_path, command):
    from tests.test_matrix_experiment_methods import fixture, selected_input_records

    specification, source_inputs, _, method_inputs = fixture()
    source = tmp_path / "specification.json"
    source.write_bytes(specification.canonical_bytes())
    selection, selection_path = _write_source_selection(tmp_path, specification,
        selected_input_records(source_inputs, method_inputs))
    first, *remaining = selection.bindings
    selection_path.write_bytes(replace(selection, bindings=(
        replace(first, maximum_bytes=first.maximum_bytes - 1), *remaining)).canonical_bytes())
    destination = tmp_path / "refused-oversize.json"
    arguments = ["campaign", command, "--input", str(source), "--sources", str(selection_path)]
    if command == "experiment-prepare":
        arguments.extend(("--output", str(destination)))
    refused = CliRunner().invoke(app, arguments)
    assert refused.exit_code == 2, repr(refused.exception)
    assert "byte limit" in refused.stderr
    assert not destination.exists()
