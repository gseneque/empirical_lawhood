# SPDX-License-Identifier: MPL-2.0
"""Configured worker selections survive public preparation and cold composition."""
from dataclasses import replace
from pathlib import Path

import pytest
from typer.testing import CliRunner

from empirical_lawhood.api.experiment_preparation import prepare_experiment
from empirical_lawhood.api.results import RunCampaignRequest, ResumeCampaignRequest
from empirical_lawhood.cli.app import app
from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection, select_experiment_workers
from tests.test_experiment_preparation_public import _copied_input, _report
from tests.test_programme_catalog_selection import (
    CATALOG, ROOT, _service, _source_catalog_census,
    operator, prospective_selection,  # noqa: F401
)


def test_missing_workers_remain_a_reported_dependency(tmp_path, monkeypatch):
    from empirical_lawhood.cli import platform

    monkeypatch.setattr(platform, "CLI_OPERATOR_PROFILE", None)
    spec, path = _copied_input(tmp_path)
    assert ExecutionSelection().workers is None
    prepared = prepare_experiment(spec)
    assert "experiment.workers" in {row.code for row in prepared.dependencies}
    assert not prepared.executable
    report = _report(CliRunner().invoke(app, ["campaign", "experiment-explain", "--input", str(path)]))
    assert "experiment.workers" in {row["code"] for row in report["dependencies"]}


@pytest.mark.parametrize("workers, profile_maximum", ((True, 4), (0, 4), (4, True), (4, 0), (1, 4)))
def test_invalid_or_conflicting_selection_refuses(workers, profile_maximum):
    with pytest.raises(ValueError):
        select_experiment_workers(workers, profile_maximum=profile_maximum)


def test_public_explanation_uses_selected_profile_without_mount_or_execution(tmp_path, operator, monkeypatch):  # noqa: F811
    from empirical_lawhood.cli import platform
    from empirical_lawhood.infrastructure.artifacts import GuardedExternalRoot

    profile = replace(operator, maximum_parallel_tasks=4)
    profile_path = tmp_path / "operator.json"
    profile_path.write_bytes(profile.canonical_bytes())
    monkeypatch.setattr(platform, "CLI_OPERATOR_PROFILE", profile_path)
    def no_mount(*_arguments, **_options):
        pytest.fail("pure explanation inspected storage")
    monkeypatch.setattr(GuardedExternalRoot, "verify", no_mount)
    _, path = _copied_input(tmp_path)
    # Global selection is supplied in the actual CLI callback rather than a
    # monkeypatched storage factory; this performs configuration reads only.
    report = _report(CliRunner().invoke(app, ["--project-root", str(ROOT), "--operator-profile", str(profile_path),
        "campaign", "experiment-explain", "--input", str(path)]))
    assert report["execution"]["workers"] == 4
    assert "experiment.workers" not in {row["code"] for row in report["dependencies"]}
    assert report["scientific_execution_performed"] is False
    bad = CliRunner().invoke(app, ["--project-root", str(ROOT), "--operator-profile", str(profile_path),
        "campaign", "experiment-explain", "--input", str(path), "--workers", "1"])
    assert bad.exit_code == 2 and "selected operator profile" in bad.stderr


@pytest.mark.parametrize("lifecycle", ("run", "recover"))
def test_omitted_run_and_recovery_use_real_selected_api_before_any_worker(
        prospective_selection, operator, monkeypatch, lifecycle):  # noqa: F811
    from empirical_lawhood.api import composition
    from empirical_lawhood.infrastructure.execution import LocalProcessExecutor

    profile = replace(operator, maximum_parallel_tasks=4)
    service = _service(prospective_selection, profile, catalog_relative_path=CATALOG)
    before = _source_catalog_census(ROOT)
    actual = composition.create_api
    apis = []
    def compose(**arguments):
        api = actual(**arguments)
        apis.append(api)
        return api
    def no_child(*_arguments, **_options):
        pytest.fail("missing-original replay launched a child")
    monkeypatch.setattr(composition, "create_api", compose)
    monkeypatch.setattr(LocalProcessExecutor, "execute", no_child)
    monkeypatch.setattr(LocalProcessExecutor, "execute_deadline_free", no_child)
    request = (RunCampaignRequest(Path(profile.external_root_locator) / "absent-package.json")
        if lifecycle == "run" else ResumeCampaignRequest("run.synthetic.absent"))
    result = getattr(service, lifecycle)(directory=prospective_selection.directory, request=request)
    assert not result["status"] == "SUCCEEDED"
    api, = apis
    assert api._execution_service.maximum_parallel_tasks == profile.maximum_parallel_tasks
    assert _source_catalog_census(ROOT) == before


@pytest.mark.parametrize("execution", ({}, object(), 1))
def test_service_rejects_untyped_execution_before_protocol_preparation(execution, monkeypatch):
    from empirical_lawhood.api import experiment_preparation
    from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService

    def no_preparation(*_arguments, **_options):
        pytest.fail("untyped operational selection reached protocol preparation")
    monkeypatch.setattr(experiment_preparation, "prepare_experiment", no_preparation)
    with pytest.raises(TypeError, match="typed operational selection"):
        ExperimentProgrammeService(ROOT, None).prepare(object(), execution=execution)
