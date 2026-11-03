# SPDX-License-Identifier: MPL-2.0
"""Public progress is optional, independent from custody and safe to inspect."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
from empirical_lawhood.cli import integrations
from empirical_lawhood.cli.app import app
from empirical_lawhood.infrastructure.progress import JsonProgressReporter, read_progress
from empirical_lawhood.runtime.progress import report_progress


ROOT = Path(__file__).resolve().parents[1]


def test_real_public_preparation_progress_preserves_report_bytes(tmp_path):
    arguments = ["campaign", "experiment-explain", "--input",
                 str(ROOT / "programmes/foundations/emergent-structure/workflows/matrix-response-experiment/alternative.json")]
    ordinary = CliRunner().invoke(app, arguments)
    selected = tmp_path / "progress.json"
    observed = CliRunner().invoke(app, [*arguments, "--progress-file", str(selected)])
    assert ordinary.exit_code == observed.exit_code == 0, observed.output
    assert observed.stdout == ordinary.stdout
    record = read_progress(selected)
    assert record["operation"] == "campaign experiment-explain"
    assert record["status"] == "RETURNED"
    assert record["phase"] != "starting"
    assert record["done"] is not None


@pytest.mark.parametrize("method", ("run", "read", "recover"))
def test_cli_progress_keeps_result_and_can_be_read_without_storage(tmp_path, monkeypatch, method):
    authoring = tmp_path / "closed"
    authoring.mkdir()
    selected = tmp_path / "progress.json"
    seen = []
    storage_modes = []

    def execute(_service, **options):
        seen.append(options)
        report_progress(phase="execution.tasks", done=2, total=4, failed=1)
        return {"software_fixture": True, "scientific_result": "UNCHANGED"}

    def storage(*, read_only=False):
        storage_modes.append(read_only)
        return tmp_path, object(), object()

    monkeypatch.setattr(integrations, "_storage", storage)
    monkeypatch.setattr(ExperimentProgrammeService, method, execute)
    arguments = ["campaign", "experiment-" + method, "--authoring-dir", str(authoring)]
    ordinary = CliRunner().invoke(app, arguments)
    observed = CliRunner().invoke(app, [*arguments, "--progress-file", str(selected)])
    assert ordinary.exit_code == observed.exit_code == 0, observed.output
    assert ordinary.stdout == observed.stdout
    assert len(seen) == 2 and seen[0] == seen[1]
    assert storage_modes == [method == "read"] * 2

    def forbidden():
        pytest.fail("advisory progress view opened scientific storage")

    monkeypatch.setattr(integrations, "_storage", forbidden)
    viewed = CliRunner().invoke(app, ["progress", "--file", str(selected)])
    assert viewed.exit_code == 0, viewed.output
    assert "2/4 (50.0%)" in viewed.stdout and "failed=1" in viewed.stdout
    assert "RETURNED" in viewed.stdout
    document = CliRunner().invoke(app, ["progress", "--file", str(selected), "--json"])
    assert document.exit_code == 0
    assert json.loads(document.stdout) == read_progress(selected)


@pytest.mark.parametrize("location", ("occupied", "package", "missing_parent"))
def test_bad_progress_destination_refuses_before_work(tmp_path, monkeypatch, location):
    authoring = tmp_path / "closed"
    authoring.mkdir()
    selected = authoring / "progress.json" if location == "package" else tmp_path / "progress.json"
    if location == "occupied":
        selected.write_bytes(b"preserve existing bytes")
    elif location == "missing_parent":
        selected = tmp_path / "absent" / "progress.json"

    def forbidden():
        pytest.fail("bad progress destination reached scientific storage")

    monkeypatch.setattr(integrations, "_storage", forbidden)
    result = CliRunner().invoke(app, ["campaign", "experiment-run", "--authoring-dir", str(authoring),
                                    "--progress-file", str(selected)])
    assert result.exit_code == 2, result.output
    if location == "occupied":
        assert selected.read_bytes() == b"preserve existing bytes"
    assert list(authoring.iterdir()) == []


def test_refused_work_preserves_partial_progress_and_original_exit(tmp_path, monkeypatch):
    authoring = tmp_path / "closed"
    authoring.mkdir()
    selected = tmp_path / "progress.json"

    def refuse(_service, **_options):
        report_progress(phase="execution.tasks", done=1, total=4)
        raise ValueError("software fixture refusal")

    monkeypatch.setattr(integrations, "_storage", lambda: (tmp_path, object(), object()))
    monkeypatch.setattr(ExperimentProgrammeService, "run", refuse)
    result = CliRunner().invoke(app, ["campaign", "experiment-run", "--authoring-dir", str(authoring),
                                    "--progress-file", str(selected)])
    assert result.exit_code == 2, result.output
    assert "software fixture refusal" in result.stderr
    record = read_progress(selected)
    assert record["status"] == "FAILED" and record["done"] == 1 and record["percent"] == 25


def test_progress_view_shows_unknown_total_without_guess(tmp_path):
    selected = tmp_path / "progress.json"
    reporter = JsonProgressReporter(selected, "software fixture", minimum_interval=0)
    reporter.update(phase="validate_inputs", done=7)
    result = CliRunner().invoke(app, ["progress", "--file", str(selected)])
    assert result.exit_code == 0, result.output
    assert "validate_inputs | 7" in result.stdout and "%" not in result.stdout
    reporter.finish()


@pytest.mark.parametrize("payload", (b"{", b"x" * (16 * 1024 + 1)), ids=("malformed", "oversized"))
def test_invalid_progress_view_has_bounded_public_refusal(tmp_path, payload):
    selected = tmp_path / "progress.json"
    selected.write_bytes(payload)
    result = CliRunner().invoke(app, ["progress", "--file", str(selected)])
    assert result.exit_code == 2, result.output
    assert "Cannot read progress" in result.stderr
    assert result.stdout == ""


def test_progress_cannot_create_missing_list_valued_scientific_operand(tmp_path, monkeypatch):
    authoring = tmp_path / "closed"
    authoring.mkdir()
    selected = tmp_path / "missing-parent-binding.json"

    def forbidden():
        pytest.fail("progress destination overwrote a selected scientific operand")

    monkeypatch.setattr(integrations, "_storage", forbidden)
    result = CliRunner().invoke(app, ["campaign", "experiment-run", "--authoring-dir", str(authoring),
                                    "--plan", str(tmp_path / "plan.json"), "--parent-input-binding", str(selected),
                                    "--progress-file", str(selected)])
    assert result.exit_code == 2, result.output
    assert not selected.exists()


def test_progress_stays_outside_selected_output_root_before_preparation(tmp_path, monkeypatch):
    from empirical_lawhood.cli import experiment_preparation

    def forbidden(*_args, **_kwargs):
        pytest.fail("invalid progress destination entered preparation")

    monkeypatch.setattr(experiment_preparation, "_prepare", forbidden)
    selected = tmp_path / "progress.json"
    result = CliRunner().invoke(app, ["campaign", "experiment-explain", "--input", str(tmp_path / "specification.json"),
                                    "--output-root", str(tmp_path), "--progress-file", str(selected)])
    assert result.exit_code == 2, result.output
    assert not selected.exists()
