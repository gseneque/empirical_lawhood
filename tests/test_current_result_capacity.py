# SPDX-License-Identifier: MPL-2.0
"""Disclosed selected-size custody controls; no study or execution authority."""

from dataclasses import replace
from pathlib import Path

import pytest

from empirical_lawhood.api.current_result_custody import CurrentResultPlanReader, _current_control
from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict, ExternalArtifactPlane
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.runtime.artifacts import ArtifactCustodyLimits, ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.plans import CandidateExecutionPlan
from tests.runtime_plan_capacity_fixture import expanded_plan_metadata
from tests.runtime_platform.test_execution_scheduler import _plane


def test_current_result_plan_uses_selected_size_and_rejects_changed_body(tmp_path):
    small = decode_canonical_bytes((Path(__file__).parent / "fixtures/authoring-execution-plan.json").read_bytes(),
        CandidateExecutionPlan, maximum_bytes=None)
    plan = expanded_plan_metadata(small)
    raw = plan.canonical_bytes()
    assert len(raw) > 64 * 1024**2
    root = tmp_path / "current-result-capacity"
    root.mkdir()
    plane = _plane(root)
    run_id, name = "capacity.disclosed", "execution-plan"
    relative = f"runs/{run_id}/plans/{name}.json"
    plane.write(ArtifactWriteRequest(f"{name}.{run_id}", relative, plan.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, "application/json", "capacity.disclosed.plan",
        f"runs/{run_id}/plans", raw, VisibilityCeiling.DEVELOPMENT_ONLY, (),
        OutcomeAccess.DEVELOPMENT_VISIBLE))

    def read(writer, maximum, **extra):
        return _current_control(writer=writer, run_id=run_id, name=name,
            record_type=CandidateExecutionPlan, maximum_bytes=maximum, **extra)

    assert read(plane, None) == plan
    with plane.verification_scope() as view:
        reader = CurrentResultPlanReader(view)
        assert read(view, len(raw), control_reader=reader) == plan
        assert read(view, None, control_reader=reader) == plan
    with pytest.raises(PermissionError, match="EXACT_PUBLISHED_CONTROL"):
        read(plane, len(raw) - 1)
    limited = ExternalArtifactPlane(plane.root, custody_limits=replace(ArtifactCustodyLimits(),
        in_memory_payload_bytes=len(raw) - 1))
    with pytest.raises(PermissionError, match="EXACT_PUBLISHED_CONTROL"):
        read(limited, None)
    with pytest.raises(ArtifactIdentityConflict):
        with plane.verification_scope() as view:
            reader = CurrentResultPlanReader(view)
            assert read(view, None, control_reader=reader) == plan
            with plane.root.resolve(relative, for_write=True).open("ab") as stream:
                stream.write(b"\n")
            with pytest.raises(ArtifactIdentityConflict):
                read(view, None, control_reader=reader)
            # The owning lifetime must also refuse its successful exit.
