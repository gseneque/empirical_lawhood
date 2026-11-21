# SPDX-License-Identifier: MPL-2.0
"""Bounded static discovery controls; no provider or scientific execution."""

import ast
from dataclasses import replace
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from typer.testing import CliRunner

from empirical_lawhood.adapters.composition.generated_workflows import WORKFLOW_DECLARATIONS
from empirical_lawhood.api.configuration_registry import CONSUMERS
from empirical_lawhood.api.environment import EnvironmentRoute, environment_by_id, environment_routes
from empirical_lawhood.cli.app import app
from empirical_lawhood.execution.discovery_descriptors import ConfigurationDeclaration, EnvironmentDeclaration
from scripts import generate_extension_bundle_aggregate as aggregate
from scripts import generate_extension_projections as projections


def test_public_descriptor_discovery_excludes_its_own_projection():
    owners = aggregate.discover_public_facets()
    assert owners and aggregate.PUBLIC_FACET_OUTPUT.is_file()
    assert aggregate.PUBLIC_FACET_OUTPUT not in owners
    assert len(owners) == len(set(owners))


def test_duplicate_and_missing_facets_are_reported_with_independent_stale_outputs(monkeypatch, tmp_path):
    route = EnvironmentDeclaration("fixture-route", "3.11.14", ())
    modules = {
        "first_public_facets": SimpleNamespace(__name__="first_public_facets", ENVIRONMENT_DECLARATIONS=(route,)),
        "second_public_facets": SimpleNamespace(__name__="second_public_facets", ENVIRONMENT_DECLARATIONS=(route,)),
        "empty_public_facets": SimpleNamespace(__name__="empty_public_facets"),
    }
    monkeypatch.setattr(aggregate, "discover_descriptors", lambda: ())
    monkeypatch.setattr(aggregate, "discover_public_facets", lambda: tuple(Path(name + ".py") for name in modules))
    monkeypatch.setattr(aggregate, "_module_name", lambda path: path.stem)
    monkeypatch.setattr(aggregate.importlib, "import_module", modules.__getitem__)
    monkeypatch.setattr(aggregate, "PACKAGE_ROOT", tmp_path)
    monkeypatch.setattr(aggregate, "OUTPUT", tmp_path / "extension.py")
    monkeypatch.setattr(aggregate, "PROTOCOL_OUTPUT", tmp_path / "protocols.py")
    monkeypatch.setattr(aggregate, "WORKFLOW_OUTPUT", tmp_path / "workflows.py")
    monkeypatch.setattr(aggregate, "PUBLIC_FACET_OUTPUT", tmp_path / "public_facets.py")
    monkeypatch.setattr(aggregate, "API_BINDING_OUTPUT", tmp_path / "bindings.py")
    monkeypatch.setattr(aggregate, "APPLICATION_PRESENTATION_OUTPUT", tmp_path / "presentations.py")
    monkeypatch.setattr(aggregate, "render_generated_module", lambda paths: "new extension\n")
    monkeypatch.setattr(aggregate, "render_runtime_bindings", lambda: "new bindings\n")
    monkeypatch.setattr(aggregate, "render_application_presentations", lambda: "new presentations\n")
    (tmp_path / "extension.py").write_text("old extension\n")
    before = {path.name: path.read_bytes() for path in tmp_path.iterdir()}
    with pytest.raises(SystemExit) as error:
        aggregate.main(("--check",))
    diagnostic = str(error.value)
    assert "duplicate owners for fixture-route" in diagnostic
    assert "empty_public_facets: public descriptor omits every required facet" in diagnostic
    assert "missing or stale: " + str(tmp_path / "extension.py") in diagnostic
    assert "missing or stale: " + str(tmp_path / "protocols.py") in diagnostic
    assert "missing or stale: " + str(tmp_path / "bindings.py") in diagnostic
    assert {path.name: path.read_bytes() for path in tmp_path.iterdir()} == before
    with pytest.raises(SystemExit, match="duplicate owners"):
        aggregate.main(())
    assert {path.name: path.read_bytes() for path in tmp_path.iterdir()} == before


@pytest.mark.parametrize("change", (
    {"lock_path": "../other.lock"},
    {"lock_path": "/other/uv.lock"},
    {"python_version": "3.11"},
    {"distribution_versions": (("Example_Module", "1.0"), ("example-module", "1.0"))},
    {"distribution_versions": [("numpy", "2.4.6")]},
    {"distribution_versions": (("numpy", ">=2.4.6"),)},
    {"distribution_versions": (("numpy", "2.*"),)},
))
def test_invalid_environment_facts_refuse(change):
    with pytest.raises((TypeError, ValueError)):
        EnvironmentDeclaration(**{"route_id": "fixture-route", "python_version": "3.11.14",
                                  "distribution_versions": (), **change})


def test_configuration_paths_and_record_locators_are_static_and_closed():
    row = ConfigurationDeclaration("fixture-config", "fixture/specification", "empirical_lawhood.example",
        "Specification", "editable", 1024, True, "experiment prepare", "fixture", ("examples/input.json",))
    for change in ({"supplied_inputs": ("../outside.json",)}, {"supplied_inputs": ("C:\\input.json",)},
                   {"record_module": "os"}, {"record_name": None}, {"maximum_bytes": True}):
        with pytest.raises((TypeError, ValueError)):
            replace(row, **change)


def test_explicitly_unavailable_workflow_keeps_its_honest_stop():
    declaration = next(row for row in WORKFLOW_DECLARATIONS
                       if row.workflow.workflow_id == "battery-initial-window-observation")
    assert declaration.operations_available is False
    assert declaration.workflow.operations == ()
    assert declaration.workflow.first_missing_prerequisite
    with pytest.raises(ValueError):
        replace(declaration, operations_available=True)
    available = next(row for row in WORKFLOW_DECLARATIONS if row.workflow.operations)
    with pytest.raises(ValueError):
        replace(available, operations_available=False)
    for invalid in (-1, True):
        with pytest.raises(ValueError, match="catalogue order"):
            replace(available, catalogue_order=invalid)


@pytest.mark.parametrize("path,allowed_modules,constructors", (
    (aggregate.WORKFLOW_OUTPUT, {"empirical_lawhood.execution.workflow_descriptors"},
     {"Workflow", "WorkflowDeclaration", "WorkflowInput", "WorkflowOperation"}),
    (aggregate.PUBLIC_FACET_OUTPUT, {"empirical_lawhood.execution.discovery_descriptors", "empirical_lawhood.execution.installation_descriptors"},
     {"ConfigurationDeclaration", "EnvironmentDeclaration", "ExternalSoftware", "WorkerEnvironment", "WorkflowInstallationDeclaration"}),
))
def test_generated_public_projections_have_only_inward_constructors(path, allowed_modules, constructors):
    tree = ast.parse(path.read_text())
    allowed_nodes = (ast.Module, ast.Expr, ast.Constant, ast.ImportFrom, ast.alias, ast.Assign,
                     ast.Name, ast.Store, ast.Load, ast.Tuple, ast.Dict, ast.Call, ast.keyword)
    assert all(isinstance(node, allowed_nodes) for node in ast.walk(tree))
    imports = [node for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
    assert {node.module for node in imports} == allowed_modules
    assert {alias.name for node in imports for alias in node.names} == constructors
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
    assert calls and all(isinstance(node.func, ast.Name) and node.func.id in constructors for node in calls)


def test_adapter_environment_route_needs_no_enum_or_native_import(tmp_path, monkeypatch):
    assert "mass-balance" not in {route.value for route in EnvironmentRoute}
    declaration = environment_by_id("mass-balance")
    assert declaration in environment_routes() and declaration.distribution_versions == ()
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["doctor", "--route", declaration.route_id, "--format", "json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)["payload"]
    assert payload["environment_route"] == declaration.route_id
    assert {row["dependency_id"] for row in payload["optional_dependencies"]} == {"cpython"}
    assert not tuple(tmp_path.iterdir())
    with pytest.raises(ValueError, match="unknown environment route"):
        environment_by_id("../../other")


@pytest.mark.parametrize("consumer,schema,module,name", (
    ("matrix-sci02-h64", "matrix-sci02", "matrix_experimental_programme.sci02_experiment", "Sci02Specification"),
    ("matrix-sci02b-paired-description", "matrix-sci02b", "matrix_experimental_programme.sci02b_experiment", "Sci02BSpecification"),
    ("matrix-sci02c-consumer-prediction", "matrix-sci02c", "matrix_experimental_programme.sci02c_experiment", "Sci02CSpecification"),
    ("matrix-sci02d-paired-equilibrium", "matrix-sci02d", "matrix_equilibrium_bridge.experiment", "BridgeSpecification"),
))
def test_sci02_public_configuration_identities_survive_owner_migration(consumer, schema, module, name):
    rows = [row for row in CONSUMERS if row.consumer == consumer]
    assert len(rows) == 1
    row = rows[0]
    assert row.schema_id == f"empirical-lawhood/{schema}/specification"
    assert row.record_module == f"empirical_lawhood.domains.matrix.{module}"
    assert row.record_name == name


@pytest.mark.parametrize("check", (False, True))
def test_ordered_entrypoint_checks_all_stages_but_stops_mutation_after_failure(monkeypatch, check):
    commands = []
    monkeypatch.setattr(projections, "require_executing_target_source", lambda root: None)

    def command(argv, **bounds):
        commands.append(argv)
        assert bounds["timeout_seconds"] == 180
        assert bounds["maximum_stdout_bytes"] == 256 * 1024
        assert bounds["maximum_stderr_bytes"] == 64 * 1024
        assert ("--check" in argv) is check
        return SimpleNamespace(returncode=1 if len(commands) == 2 else 0, stdout=b"bounded output", stderr=b"")

    monkeypatch.setattr(projections, "run_bounded_command", command)
    report = projections.run_projections(check=check)
    assert report["status"] == "FAILED" and report["scientific_authority"] == "NONE"
    assert tuple(row["stage"] for row in report["stages"]) == projections.STAGES
    assert len(commands) == (6 if check else 2)
    assert [row["status"] for row in report["stages"]][2:] == (
        ["CURRENT"] * 4 if check else ["SKIPPED_DEPENDENCY"] * 4)
