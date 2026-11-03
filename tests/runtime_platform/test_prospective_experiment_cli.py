# SPDX-License-Identifier: MPL-2.0
"""Typed request forwarding only; no issue, authority or worker execution."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
from empirical_lawhood.api.results import CampaignStatusRequest, ResumeCampaignRequest, RunCampaignRequest
from empirical_lawhood.cli import integrations
from empirical_lawhood.cli.app import app


@pytest.mark.parametrize("method,arguments,expected", (
    ("run", ("--plan", "/selected/issued.json", "--yes", "--reveal-authority-id", "authority.reveal",
        "--parent-record", "/selected/parent.json", "--parent-input-binding", "/selected/input.json"),
        RunCampaignRequest(Path("/selected/issued.json"), True, "authority.reveal", Path("/selected/parent.json"), (Path("/selected/input.json"),))),
    ("read", ("--run", "run.original", "--attempt-history"), CampaignStatusRequest("run.original", True)),
    ("recover", ("--run", "run.original", "--yes", "--reveal-authority-id", "authority.reveal",
        "--parent-record", "/selected/parent.json", "--parent-input-binding", "/selected/input.json"),
        ResumeCampaignRequest("run.original", True, "authority.reveal", Path("/selected/parent.json"),
            (Path("/selected/input.json"),))),
))
def test_programme_cli_preserves_selected_typed_request_and_operator_profile(tmp_path, monkeypatch, method, arguments, expected):
    profile, plane = object(), object()
    seen = []

    def execute(service, **kwargs):
        seen.append((service, kwargs))
        return {"scope": "CLI_FORWARDING_ONLY_NO_EXECUTION"}

    monkeypatch.setattr(integrations, "_storage", lambda *, read_only=False: (tmp_path, profile, plane))
    monkeypatch.setattr(ExperimentProgrammeService, method, execute)
    result = CliRunner().invoke(app, ["campaign", "experiment-" + method, "--authoring-dir", str(tmp_path), *arguments])
    assert result.exit_code == 0, result.stdout + result.stderr + repr(result.exception)
    service, options = seen.pop()
    assert not seen
    assert (service.project_root, service.artifact_writer, service.storage_profile) == (tmp_path, plane, profile)
    assert options["directory"] == tmp_path and options["request"] == expected


@pytest.mark.parametrize("method,arguments", (
    ("run", ("--reveal-authority-id", "authority.reveal")),
    ("read", ("--attempt-history",)), ("recover", ("--reveal-authority-id", "authority.reveal")),
    ("recover", ("--parent-input-binding", "/selected/input.json")),
))
def test_issued_only_options_cannot_silently_select_development_execution(tmp_path, monkeypatch, method, arguments):
    monkeypatch.setattr(integrations, "_storage", lambda *, read_only=False: (tmp_path, object(), object()))

    def forbidden(*_args, **_kwargs):
        pytest.fail("incomplete issued request reached programme dispatch")

    monkeypatch.setattr(ExperimentProgrammeService, method, forbidden)
    result = CliRunner().invoke(app, ["campaign", "experiment-" + method, "--authoring-dir", str(tmp_path), *arguments])
    assert result.exit_code == 2
    assert "require" in result.stderr
