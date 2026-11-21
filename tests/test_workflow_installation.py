# SPDX-License-Identifier: MPL-2.0
"""Finite metadata and refusal controls, with no solver or scientific acquisition."""

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import venv
import zipfile

import pytest
from typer.testing import CliRunner

from empirical_lawhood.api import workflow_installation as owner
from empirical_lawhood.api.application import execute_application
from empirical_lawhood.api.application_contracts import ApplicationContext, ApplicationRequest
from empirical_lawhood.api.results import OperationStatus
from empirical_lawhood.cli.app import app
from empirical_lawhood.execution.resources.environment_probe import inspect_interpreter_metadata
from empirical_lawhood.execution.installation_descriptors import ExternalSoftware, WorkerEnvironment, WorkflowInstallationDeclaration
from scripts.generate_workflow_installations import parse_requirements
from scripts.export_workflow_requirements import export_requirements


def _requirements(raw):
    return parse_requirements(raw, python_version="3.11.14", python_implementation="CPython",
                              system="Linux", architecture="x86_64")


def test_frozen_requirements_keep_exact_target_markers_and_artifact_hashes():
    raw = ("example_module==1.0 ; sys_platform == 'linux' \\\n    --hash=sha256:" + "a" * 64 + "\nexample-module==2.0 ; sys_platform == 'win32' --hash=sha256:" + "b" * 64 + "\n").encode()
    assert _requirements(raw) == [{"name": "example-module", "version": "1.0", "artifact_sha256": ["a" * 64]}]


@pytest.mark.parametrize("line", (
    "numpy>=2.4.6 --hash=sha256:" + "a" * 64,
    "numpy==2.4.6",
    "numpy==2.* --hash=sha256:" + "a" * 64,
    "numpy @ https://example.invalid/numpy.whl --hash=sha256:" + "a" * 64,
    "numpy==2.4.6 --hash=sha256:wrong",
))
def test_requirements_refuse_unhashed_ranges_or_external_resolution(line):
    with pytest.raises(ValueError):
        _requirements(line.encode())


def test_installation_roles_are_closed_unique_and_bounded():
    worker = WorkerEnvironment("worker", "base")
    row = WorkflowInstallationDeclaration("fixture", "standard", "empirical_lawhood.adapters.fixture", "1.0.0", "base", (worker,))
    for change in ({"workers": (worker, worker)}, {"adapter_module": "os"}, {"adapter_version": "latest"},
                   {"source_prerequisites": ["mutable"]}):
        with pytest.raises(ValueError):
            replace(row, **change)
    with pytest.raises(ValueError):
        WorkerEnvironment("controller", "base")
    with pytest.raises(ValueError):
        ExternalSoftware("source-client", "executable", "a" * 64, True, "explicit client")


def test_every_workflow_has_a_standard_manifest_and_brian2_keeps_separate_numpy():
    from empirical_lawhood.api.workflows import list_workflows

    for workflow in list_workflows():
        manifest = owner.workflow_installation(workflow.workflow_id)
        assert manifest["profile"]["declaration"]["workflow_id"] == workflow.workflow_id
        assert manifest["profile"]["source_inputs"] == json.loads(json.dumps([
            {"path": row.path, "role": row.role, "schema_id": row.schema_id} for row in workflow.inputs]))
    brian = owner.workflow_installation("neuron-current-response")
    assert brian["profile"]["declaration"]["workers"] == [
        {"role_id": "brian2", "environment_id": "brian2-worker", "selection": "explicit"}]
    controller = {row["name"]: row["version"] for row in brian["environments"]["base"]["targets"][0]["requirements"]}
    worker = {row["name"]: row["version"] for row in brian["environments"]["brian2-worker"]["targets"][0]["requirements"]}
    assert controller["numpy"] == "2.4.6" and worker["numpy"] == "1.26.4" and worker["brian2"] == "2.9.0"
    assert owner.workflow_installation("recursive-inquiry", profile="battery")["profile"]["declaration"]["controller_environment"] == "battery-recursion"
    with pytest.raises(ValueError, match="unknown workflow"):
        owner.workflow_installation("neuron-current-response", profile="unregistered")


def test_manifest_and_requirements_tampering_refuse_before_metadata_probe(monkeypatch):
    original = owner._resource
    monkeypatch.setattr(owner, "inspect_interpreter_metadata", lambda *a, **k: pytest.fail("entered interpreter probe"))
    monkeypatch.setattr(owner, "_resource", lambda name, **kwargs: original(name, **kwargs) + b" " if name == "manifest.json" else original(name, **kwargs))
    with pytest.raises(ValueError, match="generated source binding"):
        owner.workflow_installation("mass-balance-starter")
    monkeypatch.setattr(owner, "_resource", lambda name, **kwargs: original(name, **kwargs) + b" " if name.endswith("requirements.txt") else original(name, **kwargs))
    with pytest.raises(ValueError, match="requirements export"):
        owner.workflow_installation("mass-balance-starter")


def test_selected_manifest_binds_its_owning_source_and_lock(monkeypatch, tmp_path):
    from empirical_lawhood.storage import source_origin

    manifest = owner.workflow_installation("mass-balance-starter")
    pins = [manifest["profile"]["owner"]]
    for environment in manifest["environments"].values():
        pins.extend((environment["project"], environment["lock"]))
    tracked = [SimpleNamespace(relative_path=row["path"], size_bytes=row["size_bytes"], sha256=row["sha256"]) for row in pins]
    visits = []
    candidate = SimpleNamespace(tracked_files=tracked, implementation_commit="a" * 40,
        implementation_sha256="b" * 64, source_tree_sha256="c" * 64, require_current=lambda: visits.append("current"))
    monkeypatch.setattr(source_origin, "observe_selected_implementation", lambda root: (root, candidate))
    result = owner._source_binding(manifest, project_root=tmp_path)
    assert result["implementation_commit"] == "a" * 40 and visits == ["current"]
    next(row for row in tracked if row.relative_path == "uv.lock").sha256 = "d" * 64
    with pytest.raises(ValueError, match="installed build-source input: uv.lock"):
        owner._source_binding(manifest, project_root=tmp_path)
    assert visits == ["current"]


def test_real_metadata_probe_ignores_site_startup_and_native_module_code(tmp_path):
    environment = tmp_path / "isolated"
    venv.EnvBuilder(with_pip=False).create(environment)
    site = environment / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages"
    marker = tmp_path / "CONTACT_OCCURRED"
    side_effect = f"from pathlib import Path; Path({str(marker)!r}).write_text('unexpected')\n"
    (site / "sitecustomize.py").write_text(side_effect)
    (site / "startup.pth").write_text("import pathlib; pathlib.Path(" + repr(str(marker)) + ").write_text('unexpected')\n")
    module = site / "brian2"; module.mkdir(); (module / "__init__.py").write_text(side_effect)
    distribution = site / "brian2-2.9.0.dist-info"; distribution.mkdir()
    (distribution / "METADATA").write_text("Metadata-Version: 2.1\nName: brian2\nVersion: 2.9.0\n")
    observation = inspect_interpreter_metadata(environment / "bin/python", ("brian2", "numpy"))
    assert observation["distributions"] == {"brian2": ["2.9.0"], "numpy": []}
    assert observation["site_startup_enabled"] is False and observation["native_modules_loaded"] == []
    assert observation["interpreter_file"]["sha256"] and not marker.exists()
    assert not tuple(module.glob("__pycache__/*"))


def _matching_observation(python, names):
    manifest = owner.workflow_installation("mass-balance-starter")
    environment = manifest["environments"]["mass-balance"]
    versions = {row["name"]: row["version"] for row in environment["targets"][0]["requirements"]}
    return {"python_version": "3.11.14", "python_implementation": "CPython", "system": "Linux", "architecture": "x86_64",
            "distributions": {name: [versions[name]] for name in names}, "native_modules_loaded": [], "site_startup_enabled": False}


@pytest.mark.parametrize("fault,reason", (
    ("absent", "DISTRIBUTION_ABSENT"), ("drift", "DISTRIBUTION_VERSION_MISMATCH"),
    ("duplicate", "AMBIGUOUS_DISTRIBUTION_METADATA"), ("platform", "UNSUPPORTED_SOFTWARE_PLATFORM"),
))
def test_selected_assertion_fails_while_ordinary_inspection_keeps_success(monkeypatch, fault, reason):
    monkeypatch.setattr(owner, "_source_binding", lambda *a, **k: {"status": "MATCHED"})

    def observe(python, names):
        result = _matching_observation(python, names)
        if fault == "platform":
            result["architecture"] = "unsupported"
        else:
            result["distributions"]["numpy"] = {"absent": [], "drift": ["0.0.0"], "duplicate": ["2.4.6", "2.4.6"]}[fault]
        return result

    monkeypatch.setattr(owner, "inspect_interpreter_metadata", observe)
    inspected = owner.workflow_environment_result("mass-balance-starter")
    asserted = owner.workflow_environment_result("mass-balance-starter", assert_prerequisites=True)
    assert inspected.status is OperationStatus.SUCCEEDED and asserted.status is OperationStatus.BLOCKED
    assert reason in inspected.payload["reason_codes"] and reason in asserted.reason_codes
    assert asserted.payload["source_inputs_state"] == "NOT_INSPECTED"
    assert asserted.payload["execution_authority"] == "NOT_ASSESSED"
    assert asserted.payload["scientific_qualification"] == "NOT_ESTABLISHED"


def test_missing_explicit_worker_refuses_without_worker_contact(monkeypatch):
    calls = []
    monkeypatch.setattr(owner, "_source_binding", lambda *a, **k: {"status": "MATCHED"})

    def observe(python, names):
        calls.append(python)
        return _matching_observation(python, names)

    monkeypatch.setattr(owner, "inspect_interpreter_metadata", observe)
    result = owner.workflow_environment_result("neuron-current-response", assert_prerequisites=True)
    assert result.status is OperationStatus.BLOCKED and "WORKER_PYTHON_REQUIRED" in result.reason_codes
    assert calls == [Path(sys.executable)]
    assert result.payload["environments"][1]["observation"] is None
    assert result.payload["native_contacts"] == 0


def test_external_software_identity_is_hashed_without_execution(monkeypatch, tmp_path):
    manifest = owner.workflow_installation("mass-balance-starter")
    external = tmp_path / "native-client.py"
    raw = b"raise AssertionError('external client must not execute')\n"
    external.write_bytes(raw)
    manifest["profile"]["declaration"]["external_software"] = [{"software_id": "client", "kind": "module-file",
        "sha256": sha256(raw).hexdigest(), "maximum_bytes": 1024, "description": "fixture module identity"}]
    # Save the observation before replacing the manifest lookup used by that helper.
    original = _matching_observation(Path(sys.executable), tuple(row["name"] for row in manifest["environments"]["mass-balance"]["targets"][0]["requirements"]))
    monkeypatch.setattr(owner, "workflow_installation", lambda *a, **k: manifest)
    monkeypatch.setattr(owner, "_source_binding", lambda *a, **k: {"status": "MATCHED"})
    monkeypatch.setattr(owner, "inspect_interpreter_metadata", lambda *a, **k: original)
    report = owner.inspect_workflow_environment("mass-balance-starter", external_software=("client=" + str(external),))
    assert report["software_prerequisites_satisfied"] is True
    external.write_bytes(raw + b"# changed\n")
    report = owner.inspect_workflow_environment("mass-balance-starter", external_software=("client=" + str(external),))
    assert report["software_prerequisites_satisfied"] is False
    assert "EXTERNAL_SOFTWARE_IDENTITY_MISMATCH" in report["reason_codes"]


def test_cli_and_application_share_selected_assertion_and_refusal(monkeypatch, tmp_path):
    monkeypatch.setattr(owner, "_source_binding", lambda *a, **k: {"status": "MATCHED"})
    monkeypatch.setattr(owner, "inspect_interpreter_metadata", _matching_observation)
    selected = ApplicationContext("metadata", "Metadata", Path(sys.executable))
    request = ApplicationRequest("metadata.one", "metadata", "workflow.environment", (
        ("assert_prerequisites", True), ("workflow_id", "mass-balance-starter")))
    application = execute_application(selected, request)
    assert application.succeeded and application.payload["software_prerequisites_satisfied"]
    monkeypatch.chdir(tmp_path)
    cli = CliRunner().invoke(app, ["doctor", "--workflow", "mass-balance-starter", "--assert-prerequisites", "--format", "json"])
    assert cli.exit_code == 0, cli.output
    assert json.loads(cli.stdout)["payload"] == application.to_mapping()["payload"]
    worker = CliRunner().invoke(app, ["--no-progress", "doctor", "--workflow", "neuron-current-response", "--assert-prerequisites", "--format", "json"])
    assert worker.exit_code == 3, worker.output
    assert "WORKER_PYTHON_REQUIRED" in json.loads(worker.stderr)["reason_codes"]
    assert CliRunner().invoke(app, ["doctor", "--assert-prerequisites"]).exit_code == 2
    assert CliRunner().invoke(app, ["doctor", "--route", "reactor", "--workflow", "mass-balance-starter"]).exit_code == 2
    assert not tuple(tmp_path.iterdir())


@pytest.mark.parametrize("change", (None, "requirements", "source-lock"))
def test_wheel_requirements_export_authenticates_bytes_before_writes(tmp_path, change):
    # This small wheel is a software-only custody fixture, never an installed
    # candidate or scientific qualification. Installed acceptance uses a real build.
    source_root = Path(__file__).parents[1]
    manifest = owner.workflow_installation("mass-balance-starter")
    root = source_root / "src/empirical_lawhood"
    paths = ["package_data/workflow_installations/manifest.json", "package_data/workflow_installations/mass-balance.requirements.txt",
             "adapters/composition/generated_installation_manifest.py"]
    payloads = {"empirical_lawhood/" + name: (root / name).read_bytes() for name in paths}
    pins = [manifest["profile"]["owner"], manifest["environments"]["mass-balance"]["project"],
            manifest["environments"]["mass-balance"]["lock"]]
    tracked = {row["path"]: {"relative_path": row["path"], "mode": "100644", "size_bytes": row["size_bytes"],
                            "sha256": row["sha256"]} for row in pins}
    for name, raw in payloads.items():
        tracked["src/" + name] = {"relative_path": "src/" + name, "mode": "100644", "size_bytes": len(raw), "sha256": sha256(raw).hexdigest()}
    source = {"schema": "empirical-lawhood/build/source", "version": "1.0.0", "implementation_commit": "a" * 40,
        "implementation_sha256": "b" * 64, "source_tree_sha256": "c" * 64,
        "tracked_files": [tracked[name] for name in sorted(tracked)]}
    if change == "requirements":
        payloads["empirical_lawhood/package_data/workflow_installations/mass-balance.requirements.txt"] += b"# changed\n"
    if change == "source-lock":
        tracked["uv.lock"]["sha256"] = "d" * 64
    payloads["fixture.dist-info/extra_metadata/source.json"] = (
        json.dumps(source, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode()
    wheel = tmp_path / "metadata-fixture.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        for name, raw in payloads.items():
            archive.writestr(name, raw)
    destination = tmp_path / "requirements"
    arguments = dict(expected_sha256=sha256(wheel.read_bytes()).hexdigest(), workflow_id="mass-balance-starter",
                     output_directory=destination)
    if change:
        with pytest.raises(ValueError):
            export_requirements(wheel, **arguments)
        assert not destination.exists()
    else:
        report = export_requirements(wheel, **arguments)
        assert report["implementation_commit"] == "a" * 40 and report["software_installed"] is False
        assert (destination / "controller.requirements.txt").read_bytes() == payloads[
            "empirical_lawhood/package_data/workflow_installations/mass-balance.requirements.txt"]
        with pytest.raises(ValueError, match="new absolute output directory"):
            export_requirements(wheel, **arguments)
