# SPDX-License-Identifier: MPL-2.0
"""Current source preservation and explicit ordinary unit injection controls."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.api.execution import CampaignExecutionService
from empirical_lawhood.api.models import ExperimentPackage
from empirical_lawhood.infrastructure import run_source_admission
from empirical_lawhood.kernel.provenance import ObjectIdentity


def _identity(name):
    return ObjectIdentity(name, "empirical-lawhood/testing/entry-control", "1.0.0", "d" * 64)


def test_current_entry_keeps_exact_source_and_authority_bindings(monkeypatch):
    observed = []
    monkeypatch.setattr(ObjectIdentity, "from_record", classmethod(lambda cls, name, record: _identity(name)))
    monkeypatch.setattr(run_source_admission, "ensure_run_source_entry", lambda **kwargs: observed.append(kwargs))
    package = object.__new__(ExperimentPackage)
    object.__setattr__(package, "package_id", "package.actual")
    plan = SimpleNamespace(implementation_commit="a" * 40, source_plan=_identity("run.actual"),
        execution_plan_id="plan.actual")
    service = SimpleNamespace(enforce_git_identity=True, repo_root=Path("/selected/checkout"), artifact_plane=object())
    CampaignExecutionService._preserve_worker_source(service, package=package, execution_plan=plan,
        authority_identities=(_identity("authority.actual"),))
    assert len(observed) == 1
    assert observed[0]["expected_commit"] == "a" * 40
    assert {value.object_id for value in observed[0]["source_bindings"]} >= {
        "package.actual", "plan.actual", "run.actual", "authority.actual"}


def test_explicit_unit_injection_does_not_create_experiment_packets(monkeypatch):
    monkeypatch.setattr(run_source_admission, "ensure_run_source_entry", lambda **kwargs: pytest.fail("unit source entry"))
    service = SimpleNamespace(enforce_git_identity=False)
    assert CampaignExecutionService._preserve_worker_source(service, package=object.__new__(ExperimentPackage),
        execution_plan=None, authority_identities=()) is None


def test_public_preview_never_enters_source_preservation(tmp_path, monkeypatch):
    from empirical_lawhood.api import composition
    from empirical_lawhood.api.results import RunCampaignRequest
    from tests.api.test_campaign_execution import PACKAGE, _api

    monkeypatch.setattr(CampaignExecutionService, "_preserve_worker_source",
        lambda *args, **kwargs: pytest.fail("preview entered worker source preservation"))
    # Isolate preview from origin probing, which has its own refusal suite.
    monkeypatch.setattr(composition, "require_selected_implementation", lambda root: root)
    api, external, catalog = _api(tmp_path)
    result = api.run_campaign(RunCampaignRequest(PACKAGE, confirmed=False))
    assert result.reason_codes == ("WRITE_CONFIRMATION_REQUIRED",)
    assert not (external / "operational/run-source-entries").exists()
    assert not catalog.exists()




def test_retained_prospective_read_does_not_load_runtime_or_preserve_source(monkeypatch):
    from empirical_lawhood.api import composition, experiment_runtime_bindings
    from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
    from empirical_lawhood.api.prospective_experiment import RetainedProspectiveExperiment

    retained = RetainedProspectiveExperiment(None, None, None, None, None, None, {})
    monkeypatch.setattr(experiment_runtime_bindings, "experiment_runtime_binding",
        lambda *args: pytest.fail("retained read loaded current domain runtime"))
    monkeypatch.setattr(run_source_admission, "ensure_run_source_entry",
        lambda **kwargs: pytest.fail("retained read preserved current source"))
    monkeypatch.setattr(composition, "create_api", lambda **kwargs: object())
    service = ExperimentProgrammeService(Path("/unused"), object(), SimpleNamespace(maximum_parallel_tasks=1),
        prospective_experiment_loader=lambda **kwargs: retained)
    assert service._prospective_context(Path("/unused/retained"), lifecycle="read")[0] is retained
