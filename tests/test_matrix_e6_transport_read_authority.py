# SPDX-License-Identifier: MPL-2.0
"""E6 partial-science access ordering; disclosed reference issue, no acquisition.

The existing small issue fixture supplies real software grant replay. Only the
phase selector is projected to E6; no Matrix evidence or qualification is made.
"""
from dataclasses import replace
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import matrix_selected_scientific_read as reader
from empirical_lawhood.api import recursive_operations
from empirical_lawhood.infrastructure.study_issue import ExternalStudyOperationAuthorityStore
from tests.test_current_result_custody import actual_issued_current_task_controls  # noqa: F401
from tests.test_matrix_selected_scientific_read import _selected_reference
from tests.test_matrix_e6_transport_assessment import fixture_case


class ReachedCurrentGrant(RuntimeError):
    pass


@pytest.mark.parametrize("damage", ("missing-reveal", "expired-execution", "expired-reveal"))
def test_partial_e6_replays_current_grants_before_any_scientific_payload(
        actual_issued_current_task_controls, monkeypatch, damage):  # noqa: F811
    fixture = actual_issued_current_task_controls
    selected = _selected_reference(fixture)
    authenticate = reader.CurrentResultPlanReader.authenticate_execution_plan

    def phase_projection(self, **kwargs):
        plan = authenticate(self, **kwargs)
        # No modified plan is accepted as science. This closed selector seam
        # tests only the earlier ordinary current-authority refusal boundary.
        return SimpleNamespace(tasks=tuple(SimpleNamespace(task_id=task.task_id,
            capability=SimpleNamespace(capability_key=reader.ENTRY_TRANSPORT_KEY if index == 0
                else task.capability.capability_key)) for index, task in enumerate(plan.tasks)))

    monkeypatch.setattr(reader.CurrentResultPlanReader, "authenticate_execution_plan", phase_projection)
    monkeypatch.setattr(reader, "_design", lambda selected: (
        SimpleNamespace(account='ORIGINAL_E3',criterion=SimpleNamespace(is_matched=False)),None))
    def after_grants():
        raise ReachedCurrentGrant("ordinary current execution and reveal replay completed")
    monkeypatch.setattr(recursive_operations, "operation_catalog", after_grants)
    monkeypatch.setattr(reader, "_entry", lambda *args: pytest.fail("an invalid grant read Matrix science"))
    arguments = dict(selected=selected, artifact_writer=fixture.control.service.artifact_plane,
        run_id=fixture.context.run_id, allow_partial=True,
        reveal_authority_id=fixture.control.reveal.authority_id)
    with pytest.raises(ReachedCurrentGrant):
        reader.read_selected_protected_result(**arguments)

    if damage == "missing-reveal":
        arguments["reveal_authority_id"] = None
    else:
        load = ExternalStudyOperationAuthorityStore.load
        changed_id = (fixture.control.package.execution_authority.authority_id if damage == "expired-execution"
            else fixture.control.reveal.authority_id)
        def changed(store, authority_id):
            actual = load(store, authority_id)
            return replace(actual, expires_at_utc="2026-08-23T20:43:00Z") if authority_id == changed_id else actual
        monkeypatch.setattr(ExternalStudyOperationAuthorityStore, "load", changed)
    with pytest.raises(PermissionError):
        reader.read_selected_protected_result(**arguments)


def test_parent_entry_reopens_original_cal_before_accepting_every_projection(monkeypatch):
    from empirical_lawhood.api import matrix_selected_runtime as runtime
    from empirical_lawhood.api import matrix_prepared_original_commitments as commitments
    from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_publications as publications
    case = fixture_case()
    request, future, access, calls = object(), object(), object(), []
    def original_commitments(**kwargs):
        assert kwargs["current_access"] is access
        calls.append("actual-original-TRAIN-and-panel-custody")
        return request, future
    def original_products(*args, current_access):
        assert current_access is access
        calls.append("actual-issued-original-CAL-and-source-custody")
        return case.programme
    def policy(plane, actual_request, actual_policy, *, future_selections):
        assert actual_request is request and future_selections is future and actual_policy == case.policy
        calls.append("actual-preTRAIN-policy-publication")
    monkeypatch.setattr(commitments, "authenticate_prepared_original_commitments", original_commitments)
    monkeypatch.setattr(runtime, "authenticate_selected_original_products", original_products)
    monkeypatch.setattr(publications, "authenticate_e6_transport_policy", policy)
    arguments = dict(source_scan_bytes=128 * 1024**2, transport_policy=case.policy,
        transport_calibration=case.projection, current_access=access)
    # These disclosed I/O seams convey no custody or authority; the real parent
    # composition must join their facts to its independent original-CAL check.
    assert runtime._authenticate_entry(object(), case.programme, object(), {}, **arguments) == case.programme
    saved = tuple(calls)
    altered = replace(case.projection, radius=case.projection.radius + 1)
    with pytest.raises(ValueError, match="original.*radius|frozen ancestry"):
        runtime._authenticate_entry(object(), case.programme, object(), {},
            **{**arguments, "transport_calibration": altered})
    assert tuple(calls) == (*saved, *saved)
