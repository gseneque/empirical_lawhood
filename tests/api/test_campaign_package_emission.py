# SPDX-License-Identifier: MPL-2.0
"""Closed-package emission capacity; synthetic software conformance only."""
from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

from empirical_lawhood.api import facade
from empirical_lawhood.api.codecs import load_campaign_package_authoring
from empirical_lawhood.api.facade import EmpiricalLawhoodApi
from empirical_lawhood.api.models import bind_issued_execution_package_elapsed_budget
from empirical_lawhood.api.results import (
    AssembleExperimentPackageRequest,
    BindElapsedBudgetRequest,
    CompileCampaignRequest,
    OperationStatus,
)
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.campaign_elapsed_budget import (
    CampaignElapsedBudgetSpec,
    CampaignElapsedReservationPlan,
    CampaignElapsedTaskProjection,
)
from tests.issued_study_support import build_issued_study_fixture
from tests.runtime_platform.test_deadline_free_execution_package import _execution_package_fixture, _identity
from tests.runtime_platform.test_standard_issued_package import _AuthorityStore


@pytest.mark.parametrize("elapsed", (False, True), ids=("assemble", "bind-elapsed"))
def test_closed_package_api_emission_uses_its_existing_package_allocation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, elapsed: bool,
) -> None:
    # Real assembly, authority replay and closed consumer with small fixtures.
    # Lower only ordinary local-emission capacity to reproduce the E1 failure;
    # the closed package's separate existing allocation remains available.
    fixture = build_issued_study_fixture(tmp_path)
    package = _execution_package_fixture(fixture, jit=False)
    local = tmp_path / "local-controls"
    local.mkdir()
    external = tmp_path / "scientific-plane"
    external.mkdir()
    api = EmpiricalLawhoodApi(
        repo_root=tmp_path,
        approval_service=fixture.approval_service,
        study_authority_store=_AuthorityStore(package.execution_authority),
        external_root=external,
    )

    def write(name, record):
        path = local / name
        path.write_bytes(record.canonical_bytes())
        return path

    if elapsed:
        budget = CampaignElapsedBudgetSpec(
            "campaign-elapsed-budget.local-emission",
            ObjectIdentity.from_record(package.campaign.campaign_id, package.campaign),
            100, Decimal("0.20"),
        )
        reservations = CampaignElapsedReservationPlan(
            "campaign-elapsed-reservations.local-emission",
            ObjectIdentity.from_record(budget.budget_id, budget),
            "stage.local-package-emission", "elapsed-envelope.local-package-emission",
            ObjectIdentity.from_record(
                package.execution_resource_envelope_spec.envelope_spec_id,
                package.execution_resource_envelope_spec,
            ),
            _identity("elapsed-canary.local-package-emission"),
            tuple(CampaignElapsedTaskProjection(cell.task_id, Decimal(1))
                for cell in package.execution_resource_envelope_spec.task_cells
                if cell.native_simulator_launch),
        )
        expected = bind_issued_execution_package_elapsed_budget(
            execution_package=package, campaign_elapsed_budget=budget,
            campaign_elapsed_reservation_plan=reservations,
        )
        request = BindElapsedBudgetRequest(
            write("plain-package.json", package), write("elapsed-budget.json", budget),
            write("elapsed-reservations.json", reservations), emit_path=Path("emitted-package.json"),
        )
        invoke = api.bind_elapsed_budget
    else:
        expected = package
        request = AssembleExperimentPackageRequest(
            write("base-package.json", package.base), write("issued-study.json", package.issued_study),
            write("publication-receipt.json", package.publication_receipt),
            write("frozen-proposal.json", package.frozen_proposal),
            write("scientific-approval.json", package.scientific_approval),
            write("execution-authority.json", package.execution_authority),
            write("resources.json", package.execution_resource_envelope_spec),
            package.run_plan_id, "operator.execution-service", "2026-08-22T20:44:00Z",
            emit_path=Path("emitted-package.json"),
        )
        invoke = api.assemble_package
    raw = expected.canonical_bytes()
    monkeypatch.setattr(facade, "MAX_AUTHORING_BYTES", len(raw) - 1)
    assert len(raw) < facade.MAX_CAMPAIGN_PACKAGE_BYTES

    result = invoke(request)
    assert result.status is OperationStatus.SUCCEEDED, result.to_mapping()
    assert result.payload.authority_replayed and not result.payload.executed
    assert result.payload.local_package_sha256 == expected.fingerprint()
    assert result.payload.local_bytes_written == len(raw)
    emitted = local / "emitted-package.json"
    assert emitted.read_bytes() == raw
    assert load_campaign_package_authoring(emitted) == expected
    compiled = api.compile_campaign(CompileCampaignRequest(emitted))
    assert compiled.status is OperationStatus.SUCCEEDED, compiled.to_mapping()

    # Ordinary candidate emission keeps its independent original limit.
    with pytest.raises(ValueError, match="authoring byte limit"):
        api._emit_local_candidate(
            draft_path=local / "base-package.json" if not elapsed else local / "plain-package.json",
            requested_path=Path("ordinary-candidate.json"), payload=raw,
        )
    assert not (local / "ordinary-candidate.json").exists()

    # The larger closed allocation is still finite and fails before any output.
    monkeypatch.setattr(facade, "MAX_CAMPAIGN_PACKAGE_BYTES", len(raw) - 1)
    refused = invoke(replace(request, emit_path=Path("oversized-package.json")))
    assert not refused.succeeded
    assert not (local / "oversized-package.json").exists()
