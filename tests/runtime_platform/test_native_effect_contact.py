# SPDX-License-Identifier: MPL-2.0
"""Durable uncertain-contact conformance, using synthetic worker effects."""

from dataclasses import replace
from pathlib import Path

import pytest

from tests.runtime_platform.test_execution_scheduler import _runtime, CrashAfterReceipt
from tests.runtime_platform.test_run_recovery import _delete_test_projection
from empirical_lawhood.infrastructure.execution import InjectedSchedulerCrash, LocalScheduler, SchedulerConsistencyError
from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.execution import TaskAttemptDisposition, TaskBlockReason


def _native_runtime(path, fixture, *, failures=0, clock=None, crash=None):
    task = next(value for value in fixture.execution_plan.tasks if value.task_id == "prepare")
    task = replace(task, maximum_attempts=1)
    plan = replace(fixture.execution_plan, tasks=(task,))
    fixture = replace(fixture, execution_plan=plan)
    prior, repository, plane, receipts, runners = _runtime(path, fixture,
        runner_failures={task.capability.capability_key: failures}, clock=clock, failure_injector=crash)
    contact = ExternalNativeEffectContactStore(plane=plane,
        execution_plan=ObjectIdentity.from_record(plan.execution_plan_id, plan),
        visibility_ceiling=VisibilityCeiling.PROSPECTIVE, outcome_access=OutcomeAccess.OUTCOME_BLIND)
    scheduler = LocalScheduler(operational_repository=repository, artifact_writer=plane,
        receipt_store=receipts, recovery_index=prior.recovery_index, recovery_store=prior.recovery_store,
        runner_registry=prior.runner_registry, implementation_commit=plan.implementation_commit,
        external_input_resolver=prior.external_input_resolver, input_port_factory=plane,
        executor=prior.executor, clock=clock, failure_injector=crash,
        native_effect_contact_store=contact, native_effect_capability_keys=(task.capability.capability_key,))
    return scheduler, repository, contact, runners, plan


def test_uncertain_effect_is_blocked_and_survives_total_catalog_loss(tmp_path, protocol_fixture):
    scheduler, repository, contact, runners, plan = _native_runtime(tmp_path, protocol_fixture, failures=1)
    run_id = plan.source_plan.object_id
    result = scheduler.execute(run_id, plan)
    assert result.status is OperationalStatus.BLOCKED
    assert len(tuple(context for runner in runners for context in runner.contexts)) == 1
    marker = contact.read(run_id, "prepare")
    assert marker is not None
    attempt = repository.attempts(run_id)[0]
    assert attempt.disposition is TaskAttemptDisposition.BLOCKED and attempt.reason_code == TaskBlockReason.UNKNOWN_COMPLETION.value
    _delete_test_projection(repository, tmp_path / "catalog.sqlite3")
    resumed, rebuilt, again, new_runners, _ = _native_runtime(tmp_path, protocol_fixture)
    recovered = resumed.execute(run_id, plan)
    assert recovered.status is OperationalStatus.BLOCKED
    assert again.read(run_id, "prepare") == marker
    assert all(not runner.contexts for runner in new_runners)
    rebuilt.engine.dispose()


def test_completed_contact_receipt_recovers_without_worker_after_catalog_loss(tmp_path, protocol_fixture):
    scheduler, repository, contact, runners, plan = _native_runtime(tmp_path, protocol_fixture, crash=CrashAfterReceipt("prepare"))
    run_id = plan.source_plan.object_id
    with pytest.raises(InjectedSchedulerCrash):
        scheduler.execute(run_id, plan)
    marker = contact.read(run_id, "prepare")
    assert marker is not None and sum(len(runner.contexts) for runner in runners) == 1
    _delete_test_projection(repository, tmp_path / "catalog.sqlite3")
    resumed, rebuilt, again, new_runners, _ = _native_runtime(tmp_path, protocol_fixture)
    result = resumed.execute(run_id, plan)
    assert result.status is OperationalStatus.SUCCEEDED
    assert all(not runner.contexts for runner in new_runners)
    assert again.read(run_id, "prepare") == marker
    rebuilt.engine.dispose()


def test_partial_native_contact_publication_refuses_before_worker(tmp_path, protocol_fixture):
    scheduler, repository, contact, runners, plan = _native_runtime(tmp_path, protocol_fixture)
    relative = contact._path(plan.source_plan.object_id, "prepare")
    target = Path(tmp_path / relative)
    target.parent.mkdir(parents=True)
    target.write_bytes(b"incomplete contact")
    with pytest.raises(ValueError, match="partial"):
        scheduler.execute(plan.source_plan.object_id, plan)
    assert all(not runner.contexts for runner in runners)
    repository.engine.dispose()


def test_native_retry_cannot_be_enabled_by_edited_task(tmp_path, protocol_fixture):
    scheduler, repository, _contact, runners, plan = _native_runtime(tmp_path, protocol_fixture)
    changed = replace(plan, tasks=(replace(plan.tasks[0], maximum_attempts=2),))
    with pytest.raises(SchedulerConsistencyError, match="automatic effect retries"):
        scheduler.execute(plan.source_plan.object_id, changed)
    assert all(not runner.contexts for runner in runners)
    repository.engine.dispose()


def test_scoped_native_store_keeps_scheduler_parent_receipt_and_live_ownership(tmp_path, protocol_fixture):
    scheduler, repository, original, runners, plan = _native_runtime(tmp_path, protocol_fixture)
    scopes = {"prepare": (VisibilityCeiling.PROSPECTIVE, OutcomeAccess.OUTCOME_BLIND),
        "sealed.future": (VisibilityCeiling.DEVELOPMENT_ONLY, OutcomeAccess.EVALUATION_SEALED)}
    contact = ExternalNativeEffectContactStore(plane=original.plane, execution_plan=original.execution_plan,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, outcome_access=OutcomeAccess.EVALUATION_SEALED,
        task_scopes=scopes)
    scheduler.native_effect_contact_store = contact
    result = scheduler.execute(plan.source_plan.object_id, plan)
    assert result.status is OperationalStatus.SUCCEEDED
    receipt, = result.receipts
    assert receipt.task_id == "prepare"
    assert sum(len(runner.contexts) for runner in runners) == 1
    marker = contact.read(plan.source_plan.object_id, "prepare")
    assert marker is not None
    assert not contact.is_live_creator(marker)
    assert contact.for_task("prepare").outcome_access is OutcomeAccess.OUTCOME_BLIND
    assert contact.for_task("sealed.future").outcome_access is OutcomeAccess.EVALUATION_SEALED
    sealed = replace(marker, task_id="sealed.future", attempt_id="attempt.sealed.future",
        execution_task=replace(marker.execution_task, object_id="sealed.future"))
    blind = contact.for_task("prepare")
    for action in (lambda: blind.begin(sealed), lambda: blind.read(sealed.run_id, sealed.task_id),
            lambda: blind.is_live_creator(sealed), lambda: blind.retire_live_creator(sealed),
            lambda: blind.for_task(sealed.task_id)):
        with pytest.raises(ValueError, match="another exact frozen task"):
            action()
    assert contact.read(sealed.run_id, sealed.task_id) is None
    contact.begin(sealed)
    assert contact.read(sealed.run_id, sealed.task_id) == sealed
    assert contact.for_task(sealed.task_id).is_live_creator(sealed)
    with pytest.raises(ValueError, match="exact frozen scope roster"):
        contact.for_task("undeclared.task")
    # Selecting an existing historical view does not confer this launch's live
    # native progress capability, and altered custody labels cannot relabel it.
    fresh = ExternalNativeEffectContactStore(plane=original.plane, execution_plan=original.execution_plan,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, outcome_access=OutcomeAccess.EVALUATION_SEALED,
        task_scopes=scopes)
    assert fresh.read(marker.run_id, marker.task_id) == marker
    assert not fresh.is_live_creator(marker)
    forged = ExternalNativeEffectContactStore(plane=original.plane, execution_plan=original.execution_plan,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, outcome_access=OutcomeAccess.EVALUATION_SEALED)
    with pytest.raises(ValueError, match="access role"):
        forged.read(marker.run_id, marker.task_id)
    repository.engine.dispose()
