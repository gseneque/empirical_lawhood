# SPDX-License-Identifier: MPL-2.0
"""Generic experiment CLI custody and dispatch, without worker execution."""

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
from empirical_lawhood.api.recursive_authoring import implementation_binding, load_authored_wave
from empirical_lawhood.cli import integrations
from empirical_lawhood.cli.app import app
from empirical_lawhood.infrastructure.execution import LocalProcessExecutor
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.planning.recursive_authoring import RecursiveStudyDraft
from tests.test_experiment_preparation_public import PROTOCOL_PATH, _write_source_selection
from tests.test_matrix_experiment_methods import fixture, selected_input_records
from tests.test_recursive_public_service import _plane


ROOT = Path(__file__).resolve().parents[2]


def _forbidden(*_args, **_kwargs):
    raise AssertionError("CLI custody or dispatch test executed scientific workers")


def _author_inputs(tmp_path, monkeypatch, *, missing=(), wrong_snapshot=False):
    specification, sources, _, methods = fixture()
    records = selected_input_records(sources, methods)
    for key in missing:
        del records[key]
    input_path = tmp_path / "specification.json"
    input_path.write_bytes(specification.canonical_bytes())
    _, selection_path = _write_source_selection(tmp_path, specification, records)
    snapshot = implementation_binding(ROOT)
    if wrong_snapshot:
        snapshot = replace(snapshot, observed_git_head="f" * 40)
    snapshot_path = tmp_path / "implementation.json"
    snapshot_path.write_bytes(snapshot.canonical_bytes())
    plane = _plane(tmp_path / "guarded-custody")
    monkeypatch.setattr(integrations, "_storage", lambda *, read_only=False: (ROOT, None, plane))
    destination = Path(plane.root.contract.canonical_path) / "authored"
    args = ["campaign", "experiment-author", "--input", str(input_path), "--sources", str(selection_path),
        "--source-snapshot", str(snapshot_path), "--protocol", str(PROTOCOL_PATH),
        "--environment-id", "fixture.locked-main", "--output-dir", str(destination), "--workers", "2"]
    return specification, snapshot, plane, destination, args


def _files(directory):
    return {str(path.relative_to(directory)): path.read_bytes() for path in directory.rglob("*") if path.is_file()}


def test_author_cli_retains_real_declared_graph_and_automatically_bound_original_records(tmp_path, monkeypatch):
    from empirical_lawhood.adapters.methods.matrix_factor_response import experiment_methods as science

    specification, snapshot, plane, directory, args = _author_inputs(tmp_path, monkeypatch)
    selected_inputs = {name: raw for name, raw in _files(tmp_path).items() if not name.startswith("guarded-custody/")}
    monkeypatch.setattr(science, "fit_models", _forbidden)
    monkeypatch.setattr(LocalProcessExecutor, "execute", _forbidden)
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0, result.stdout + result.stderr + repr(result.exception)
    report = json.loads(result.stdout)
    assert report["task_count"] == 61 and report["native_contact"] == "none"
    assert report["specification"] == specification.identity.to_document()
    assert report["experiment_census"] == {"train": 12, "calibration": 20, "evaluation": 8,
        "transfer_nearby": 2, "transfer_shifted": 2}
    packet, draft, source, payloads = load_authored_wave(directory=directory, artifact_writer=plane)
    assert type(draft) is RecursiveStudyDraft and len(draft.operations) == 61
    assert source == snapshot
    assert packet.draft.object_fingerprint == draft.fingerprint()
    assert decode_canonical_bytes(payloads["draft.json"], RecursiveStudyDraft,
                                  maximum_bytes=len(payloads["draft.json"])) == draft
    assert len(draft.external_inputs) == 60
    assert all(row.expected_content_sha256 is not None for row in draft.external_inputs)
    assert {name: raw for name, raw in _files(tmp_path).items() if not name.startswith("guarded-custody/")} == selected_inputs
    assert not tuple(Path(plane.root.contract.canonical_path).glob(".experiment-inputs-*"))
    assert not tuple(Path(plane.root.contract.canonical_path).glob("runs/*"))
    assert not tuple(directory.glob("*qualification*"))


def test_author_cli_lists_all_missing_prerequisites_before_new_custody_or_workers(tmp_path, monkeypatch):
    _, _, plane, directory, args = _author_inputs(tmp_path, monkeypatch,
        missing=("campaign", "calibration-features", "evaluation-outcomes"))
    before = _files(tmp_path)
    monkeypatch.setattr(LocalProcessExecutor, "execute", _forbidden)
    refused = CliRunner().invoke(app, args)
    assert refused.exit_code == 2, repr(refused.exception)
    assert all(code in refused.stderr for code in (
        "matrix.e3.campaign", "matrix.e3.calibration-features", "matrix.e3.evaluation-outcomes"))
    assert _files(tmp_path) == before
    assert not directory.exists() and not tuple(Path(plane.root.contract.canonical_path).iterdir())


def test_author_cli_refuses_a_substituted_source_snapshot_before_any_publication(tmp_path, monkeypatch):
    _, _, _, directory, args = _author_inputs(tmp_path, monkeypatch, wrong_snapshot=True)
    before = _files(tmp_path)
    monkeypatch.setattr(LocalProcessExecutor, "execute", _forbidden)
    refused = CliRunner().invoke(app, args)
    assert refused.exit_code == 2, repr(refused.exception)
    assert "actual selected implementation" in refused.stderr
    assert _files(tmp_path) == before and not directory.exists()


def test_author_cli_occupied_destination_preserves_existing_bytes(tmp_path, monkeypatch):
    _, _, _, directory, args = _author_inputs(tmp_path, monkeypatch)
    directory.mkdir()
    marker = directory / "keep-original.txt"
    marker.write_bytes(b"original selected destination\r\n")
    before = _files(tmp_path)
    monkeypatch.setattr(LocalProcessExecutor, "execute", _forbidden)
    refused = CliRunner().invoke(app, args)
    assert refused.exit_code == 2, repr(refused.exception)
    assert _files(tmp_path) == before
    assert marker.read_bytes() == b"original selected destination\r\n"


@pytest.mark.parametrize("command", ("experiment-run", "experiment-recover"))
def test_run_and_recover_commands_dispatch_the_same_frozen_directory_and_selected_workers(tmp_path, monkeypatch, command):
    # This row tests CLI composition only. Actual worker/recovery acceptance is
    # exercised separately on the coordinator's immutable source worktree.
    plane = _plane(tmp_path / "guarded")
    directory = Path(plane.root.contract.canonical_path) / "frozen"
    directory.mkdir()
    marker = directory / "selected-scientific-bytes.json"
    marker.write_bytes(b"exposed dispatch fixture\n")
    calls = []

    def run(service, **kwargs):
        calls.append({**kwargs, "project_root": service.project_root, "artifact_writer": service.artifact_writer})
        return {"test_boundary": "CLI_DISPATCH_ONLY", "native_contact": "none",
                "scientific_authority": "NONE", "qualification": "NOT_ESTABLISHED"}

    monkeypatch.setattr(integrations, "_storage", lambda *, read_only=False: (ROOT, None, plane))
    monkeypatch.setattr(ExperimentProgrammeService, "run" if command == "experiment-run" else "recover", run)
    monkeypatch.setattr(LocalProcessExecutor, "execute", _forbidden)
    before = _files(tmp_path)
    returned = CliRunner().invoke(app, ["campaign", command, "--authoring-dir", str(directory), "--workers", "3"])
    assert returned.exit_code == 0, returned.stdout + returned.stderr
    assert calls == [{"directory": directory, "project_root": ROOT, "artifact_writer": plane,
                      "maximum_parallel_tasks": 3}]
    assert json.loads(returned.stdout)["test_boundary"] == "CLI_DISPATCH_ONLY"
    assert _files(tmp_path) == before


@pytest.mark.parametrize("partial", (False, True))
def test_read_dispatch_preserves_complete_and_explicit_partial_inspection_scopes(tmp_path, monkeypatch, partial):
    plane = _plane(tmp_path / "guarded")
    directory = Path(plane.root.contract.canonical_path) / "frozen"
    directory.mkdir()
    calls = []

    def read(service, **kwargs):
        calls.append({**kwargs, "artifact_writer": service.artifact_writer})
        return {"test_boundary": "CLI_READ_DISPATCH_ONLY", "native_contact": "none"}

    def storage(*, read_only):
        assert read_only is True
        return ROOT, None, plane

    monkeypatch.setattr(integrations, "_storage", storage)
    monkeypatch.setattr(ExperimentProgrammeService, "read", read)
    monkeypatch.setattr(ExperimentProgrammeService, "run", _forbidden)
    arguments = ["campaign", "experiment-read", "--authoring-dir", str(directory)]
    if partial:
        arguments.append("--allow-partial")
    returned = CliRunner().invoke(app, arguments)
    assert returned.exit_code == 0, returned.stdout + returned.stderr
    assert calls == [{"directory": directory, "artifact_writer": plane, "allow_partial": partial,
                      "assess_incomplete": False}]
    assert json.loads(returned.stdout)["test_boundary"] == "CLI_READ_DISPATCH_ONLY"


@pytest.mark.parametrize("command", ("experiment-run", "experiment-read", "experiment-recover"))
def test_lifecycle_refusal_is_presented_without_changing_frozen_inputs(tmp_path, monkeypatch, command):
    plane = _plane(tmp_path / "guarded")
    directory = Path(plane.root.contract.canonical_path) / "frozen"
    directory.mkdir()
    marker = directory / "retain.json"
    marker.write_bytes(b"retained source-bound input\n")
    refusal = ValueError("retained source differs from its frozen scientific input")

    def refuse(_service, **_kwargs):
        raise refusal

    monkeypatch.setattr(integrations, "_storage", lambda *, read_only=False: (ROOT, None, plane))
    for method in ("run", "read", "recover"):
        monkeypatch.setattr(ExperimentProgrammeService, method, refuse)
    before = _files(tmp_path)
    returned = CliRunner().invoke(app, ["campaign", command, "--authoring-dir", str(directory)])
    assert returned.exit_code == 2, repr(returned.exception)
    assert str(refusal) in returned.stderr
    assert _files(tmp_path) == before
    assert sha256(marker.read_bytes()).hexdigest() == sha256(b"retained source-bound input\n").hexdigest()
