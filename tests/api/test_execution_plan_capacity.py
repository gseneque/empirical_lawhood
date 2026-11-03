# SPDX-License-Identifier: MPL-2.0
"""Actual retained plan capacity using disclosed software metadata only."""

from pathlib import Path

import pytest

from empirical_lawhood.api import execution as owner
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.runtime.artifacts import ArtifactCustodyLimits, ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.plans import CandidateExecutionPlan
from tests.runtime_plan_capacity_fixture import expanded_plan_metadata
from tests.runtime_platform.test_execution_scheduler import _plane


def test_retained_status_plan_above_64_mib_uses_exact_publication_and_selected_limits(tmp_path, monkeypatch):
    original = (Path(__file__).parents[1] / "fixtures/authoring-execution-plan.json").read_bytes()
    plan = expanded_plan_metadata(decode_canonical_bytes(original, CandidateExecutionPlan, maximum_bytes=len(original)))
    raw, run_id = plan.canonical_bytes(), plan.source_plan.object_id
    assert len(raw) > 64 * 1024**2
    writer = _plane(tmp_path)
    writer.write(ArtifactWriteRequest("execution-plan." + run_id,
        f"runs/{run_id}/plans/execution-plan.json", plan.SCHEMA, ArtifactProfile.CANONICAL_JSON,
        "application/json", "capacity.disclosed", f"runs/{run_id}/plans", raw,
        VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND))
    service = object.__new__(owner.CampaignExecutionService)
    service.artifact_plane = writer
    assert service._load_status_execution_plan(run_id) == plan
    writer.custody_limits = ArtifactCustodyLimits(control_record_bytes=len(raw), in_memory_payload_bytes=len(raw))
    assert service._load_status_execution_plan(run_id) == plan
    monkeypatch.setattr(owner, "decode_canonical_bytes",
        lambda *_args, **_kwargs: pytest.fail("selected capacity refusal reached full-plan decoding"))
    for field in ("control_record_bytes", "in_memory_payload_bytes"):
        writer.custody_limits = ArtifactCustodyLimits(**{field: len(raw) - 1})
        with pytest.raises(owner.CampaignIdentityError, match="selected finite custody allowance"):
            service._load_status_execution_plan(run_id)
