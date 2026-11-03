# SPDX-License-Identifier: MPL-2.0
"""Complete progress and lifecycle refusals; no new scientific authority."""

from pathlib import Path

import pytest

from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService, _phase_progress
from tests.runtime_platform.test_recursive_compiler import compile_fixture


@pytest.mark.parametrize("second_status", ("SUCCEEDED", "FAILED", "BLOCKED", "NOT_ATTEMPTED"))
def test_progress_retains_every_selected_task_and_adverse_disposition(second_status):
    plan = compile_fixture().execution_plan
    report = {"task_census": [{"task_id": task.task_id, "operational_status": state,
                              "reason_code": None if state == "SUCCEEDED" else "retained-negative"}
                             for task, state in zip(plan.tasks, ("SUCCEEDED", second_status), strict=True)]}
    phases = _phase_progress(report, plan)
    assert sum(row["assigned_tasks"] for row in phases) == 2
    assert sum(row["completed_tasks"] for row in phases) == 1 + (second_status == "SUCCEEDED")
    assert sorted((task for row in phases for task in row["tasks"]), key=lambda row: row["task_id"]) == report["task_census"]


@pytest.mark.parametrize("damage", ("missing", "duplicate", "foreign"))
def test_progress_cannot_drop_duplicate_or_replace_a_selected_task(damage):
    plan = compile_fixture().execution_plan
    rows = [{"task_id": task.task_id, "operational_status": "SUCCEEDED"} for task in plan.tasks]
    if damage == "missing":
        rows.pop()
    elif damage == "duplicate":
        rows.append(rows[0])
    else:
        rows[-1] = {"task_id": "foreign", "operational_status": "SUCCEEDED"}
    with pytest.raises(ValueError, match="complete selected task census"):
        _phase_progress({"task_census": rows}, plan)


@pytest.mark.parametrize("request_value", (None, {}, object()))
def test_programme_selection_cannot_supply_an_untyped_decision_or_authority(request_value):
    with pytest.raises(TypeError, match="typed inquiry request"):
        ExperimentProgrammeService(Path("/unused"), None).decide(request=request_value, output_dir=Path("/unused"))


@pytest.mark.parametrize("selection", (None, 0, 1, "development", "prospective"))
def test_lifecycle_labels_cannot_select_or_promote_programme_execution(selection):
    with pytest.raises(TypeError, match="explicit lifecycle selection"):
        ExperimentProgrammeService(Path("/unused"), None).run(directory=Path("/unused"), inquiry_successor=selection)


@pytest.mark.parametrize("workers", (None, 0, -1, True, 1.5, "2"))
def test_invalid_workers_refuse_before_programme_custody(workers):
    with pytest.raises(ValueError, match="positive integer"):
        ExperimentProgrammeService(Path("/unused"), None).run(directory=Path("/unused"), maximum_parallel_tasks=workers)


@pytest.mark.parametrize("partial", (None, 0, 1, "partial"))
def test_partial_label_cannot_select_scientific_assessment_scope(partial):
    with pytest.raises(TypeError, match="partial-custody selection"):
        ExperimentProgrammeService(Path("/unused"), None).read(directory=Path("/unused"), allow_partial=partial)


@pytest.mark.parametrize("selection", (None, 0, 1, "custody-only"))
def test_custody_only_recovery_requires_boolean_before_any_custody(selection):
    with pytest.raises(TypeError, match="explicit boolean"):
        ExperimentProgrammeService(Path("/unused"), None).recover(directory=Path("/unused"), custody_only=selection)


@pytest.mark.parametrize("options", (
    {"maximum_parallel_tasks": 4}, {"inquiry_successor": True}, {"inquiry_successor": None},
    {"request": object()}, {"programme_request_path": Path("/unused/request.json")}, {"confirmed": True},
))
def test_custody_only_refuses_execution_and_other_authority_options_before_custody(options):
    with pytest.raises(ValueError, match="without execution or authority options"):
        ExperimentProgrammeService(Path("/unused"), None).recover(directory=Path("/unused"), custody_only=True, **options)


def test_custody_only_service_uses_the_distinct_owner_without_selecting_an_execution_lifecycle(monkeypatch):
    from empirical_lawhood.api import recursive_execution

    def forbidden(*args, **kwargs):
        pytest.fail("custody-only recovery selected an execution lifecycle")
    monkeypatch.setattr(ExperimentProgrammeService, "_composite_programme", forbidden)
    monkeypatch.setattr(ExperimentProgrammeService, "_is_prospective", forbidden)
    monkeypatch.setattr(ExperimentProgrammeService, "run", forbidden)
    calls = []
    expected = {"native_contact": "none", "new_native_contact_count": 0}
    def custody(**kwargs):
        calls.append(kwargs)
        return expected
    monkeypatch.setattr(recursive_execution, "recover_recursive_custody", custody)
    root, directory, plane = Path("/unused"), Path("/unused/wave"), object()
    actual = ExperimentProgrammeService(root, plane).recover(directory=directory, custody_only=True)
    assert actual == expected
    assert calls == [{"directory": directory, "project_root": root, "artifact_writer": plane}]
