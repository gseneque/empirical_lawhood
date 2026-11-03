# SPDX-License-Identifier: MPL-2.0
"""Read uses the selected operational concurrency and never launches work.

Existing synthetic retained custody authenticates the read metadata. A missing
run remains NOT_FOUND; it is not fabricated as a completed scientific result.
The actual default API and guarded catalog are used without an injected service.
"""

from dataclasses import replace
from pathlib import Path

import pytest
from typer.testing import CliRunner

from empirical_lawhood.api.results import CampaignStatusRequest, ResumeCampaignRequest, RunCampaignRequest
from empirical_lawhood.cli.app import app
from empirical_lawhood.infrastructure.execution import LocalProcessExecutor
from tests.test_programme_catalog_selection import (
    CATALOG, ROOT, _cli_fixture, _service, _source_catalog_census,
    operator, prospective_selection,  # noqa: F401
)


def _no_children(monkeypatch):
    def refuse(*_arguments, **_options):
        pytest.fail("programme inspection launched a worker")
    monkeypatch.setattr(LocalProcessExecutor, "execute", refuse)
    monkeypatch.setattr(LocalProcessExecutor, "execute_deadline_free", refuse)


def test_real_four_core_profile_read_composes_selected_api_without_work_or_root_writes(
        prospective_selection, operator, monkeypatch):  # noqa: F811
    selection = prospective_selection
    profile = replace(operator, maximum_parallel_tasks=4)
    service = _service(selection, profile, catalog_relative_path=CATALOG)
    before = _source_catalog_census(ROOT)
    _no_children(monkeypatch)
    # Observe the real default API used by read(), preserving its actual status
    # and missing-original-package refusal rather than supplying a fake success.
    from empirical_lawhood.api import composition
    actual = composition.create_api
    apis = []

    def compose(**arguments):
        api = actual(**arguments)
        apis.append(api)
        return api

    monkeypatch.setattr(composition, "create_api", compose)
    report = service.read(directory=selection.directory, request=CampaignStatusRequest("run.synthetic.absent"))
    assert report["status"] == "NOT_FOUND", report
    api, = apis
    assert api._execution_service.maximum_parallel_tasks == 4
    assert api.check_catalog().succeeded and api.check_catalog().payload.present is False
    assert not api._execution_service.catalog_path.parent.exists()
    assert _source_catalog_census(ROOT) == before


@pytest.mark.parametrize("lifecycle", ("run", "recover"))
def test_explicit_run_and_recovery_workers_still_refuse_profile_mismatch(
        prospective_selection, operator, monkeypatch, lifecycle):  # noqa: F811
    selection = prospective_selection
    profile = replace(operator, maximum_parallel_tasks=4)
    _no_children(monkeypatch)
    service = _service(selection, profile, catalog_relative_path=CATALOG)
    request = (RunCampaignRequest(Path(profile.external_root_locator) / "absent-package.json")
        if lifecycle == "run" else ResumeCampaignRequest("run.synthetic.absent"))
    with pytest.raises(ValueError, match="experiment workers differ from the selected operator profile"):
        getattr(service, lifecycle)(directory=selection.directory, maximum_parallel_tasks=1, request=request)
    assert list((Path(profile.external_root_locator) / "scratch").iterdir()) == []


def test_actual_cli_read_of_four_core_profile_reaches_honest_missing_run_without_workers_flag(
        prospective_selection, operator, monkeypatch):  # noqa: F811
    selection = prospective_selection
    profile = replace(operator, maximum_parallel_tasks=4)
    _cli_fixture(monkeypatch, selection, profile)
    _no_children(monkeypatch)
    before = _source_catalog_census(ROOT)
    result = CliRunner().invoke(app, ["--catalog-relative-path", CATALOG, "campaign", "experiment-read",
        "--authoring-dir", str(selection.directory), "--run", "run.synthetic.absent"])
    assert result.exit_code == 0, result.output
    assert '"status":"NOT_FOUND"' in result.output.replace(" ", ""), result.output
    assert "operator profile and execution concurrency differ" not in result.output
    assert _source_catalog_census(ROOT) == before
    assert list((Path(profile.external_root_locator) / "scratch").iterdir()) == []
