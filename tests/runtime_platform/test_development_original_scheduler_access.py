# SPDX-License-Identifier: MPL-2.0
"""Disclosed scheduler controls; parent descriptors never grant input access."""

from types import SimpleNamespace

import pytest

from empirical_lawhood.infrastructure.execution import LocalScheduler, ResourceAdmissionError
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.execution import VerifiedArtifactInput
from empirical_lawhood.runtime.plans import PlanLane
from tests.runtime_platform.test_development_original_input_contracts import _compile
from tests.test_recursive_public_service import _plane


@pytest.fixture
def input_case(tmp_path):
    compiled, _ = _compile()
    row = next(value for value in compiled.config_inputs if value.node_id == "source")
    task = next(value for value in compiled.execution_plan.tasks if value.task_id == "source")
    plane = _plane(tmp_path / "disclosed-original-input")
    published = plane.write(ArtifactWriteRequest(row.config_id, "operand.json", row.record.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, "application/json", "publication.disclosed-original-input", ".",
        row.payload, VisibilityCeiling.DEVELOPMENT_ONLY, tuple(value.visibility_ceiling for value in row.input_parents),
        OutcomeAccess.EVALUATION_SEALED, lineage_parents=row.input_parents))
    value = VerifiedArtifactInput(published.logical, published.materialization)
    scheduler = object.__new__(LocalScheduler)
    scheduler.lane = PlanLane.DEVELOPMENT
    scheduler.authorized_barriers = frozenset()
    scheduler.original_input_access_guard = None
    scheduler.before_input_member = None
    scheduler.input_port_factory = plane
    return SimpleNamespace(scheduler=scheduler, task=task, value=value, plane=plane)


def test_compiled_original_ancestry_does_not_open_a_worker_cursor_without_actual_guard(input_case, monkeypatch):
    case = input_case
    monkeypatch.setattr(case.plane, "open_many", lambda *args, **kwargs: pytest.fail("ungranted body reached worker ports"))
    assert not LocalScheduler._input_is_authorized(case.task, case.value)
    with pytest.raises(ResourceAdmissionError, match="lacks read or outcome authority"):
        case.scheduler._worker_inputs(case.task, (), (case.value,))


@pytest.mark.parametrize("verdict", (False, True, "allowed"))
def test_a_returned_verdict_is_not_the_actual_none_or_raise_guard(input_case, monkeypatch, verdict):
    case = input_case
    monkeypatch.setattr(case.plane, "open_many", lambda *args, **kwargs: pytest.fail("false guard reached worker ports"))
    case.scheduler.original_input_access_guard = lambda task, value: verdict
    with pytest.raises(ResourceAdmissionError, match="current original-input access refused"):
        case.scheduler._worker_inputs(case.task, (), (case.value,))


def test_current_guard_refusal_precedes_any_worker_cursor(input_case, monkeypatch):
    case = input_case
    def refused(task, value):
        assert task == case.task and value == case.value
        raise PermissionError("disclosed expired original-input access")
    case.scheduler.original_input_access_guard = refused
    monkeypatch.setattr(case.plane, "open_many", lambda *args, **kwargs: pytest.fail("expired guard reached worker ports"))
    with pytest.raises(ResourceAdmissionError, match="current original-input access refused"):
        case.scheduler._worker_inputs(case.task, (), (case.value,))
