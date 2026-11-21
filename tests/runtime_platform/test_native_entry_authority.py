# SPDX-License-Identifier: MPL-2.0
"""Current native permission and attempt identity, without a lease deadline."""

from dataclasses import replace

import pytest

from empirical_lawhood.storage.native_parent_finalization import NativeParentFinalizationPending
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.execution.execution import RunnerRegistry, TaskAttemptDisposition
from empirical_lawhood.execution.native_effects import NativeEntryRefused
from tests.runtime_platform.test_native_parent_finalization_scheduler import _event, _runtime


@pytest.mark.parametrize("parallel", (1, 2))
def test_final_refusal_precedes_contact_without_inventing_a_native_failure(tmp_path, parallel):
    state = _runtime(tmp_path, parallel=parallel, parent_prepared=True)
    scheduler, contacts = state.scheduler()
    checked = []

    def require_permission(context, runner, *, prepared_contract):
        prepared_contract.require_complete()
        assert prepared_contract.native_effect
        assert prepared_contract.task_id == context.task_id == state.task.task_id
        assert prepared_contract.manifest == runner.manifest
        assert contacts.read(context.run_id, context.task_id) is None
        checked.append(context.attempt_id)
        raise PermissionError("disclosed current execution permission expired during Ready")

    scheduler.native_entry_guard = require_permission
    try:
        with pytest.raises(NativeEntryRefused, match="permission"):
            scheduler.execute("exposed.run", state.plan)
        attempt, = state.repository.attempts("exposed.run")
        assert checked == [attempt.attempt_id]
        assert attempt.disposition is TaskAttemptDisposition.RUNNING
        assert contacts.read("exposed.run", state.task.task_id) is None
        assert state.receipts.read("exposed.run", state.task.task_id, attempt.attempt_id) is None
        assert _event(state) is None
        assert state.recovery.read_terminal(state.index) is None
    finally:
        state.bundle.close()
        state.repository.engine.dispose()


@pytest.mark.parametrize("parallel", (1, 2))
def test_preparation_and_each_native_boundary_have_no_lease_deadline(tmp_path, monkeypatch, parallel):
    state = _runtime(tmp_path, parallel=parallel, parent_prepared=True)
    scheduler, contacts = state.scheduler()
    wrapper = scheduler.runner_registry.resolve(state.task)
    original = wrapper.prepare_callback
    checked = []

    def prepare(context):
        state.clock.value += 100 * scheduler.lease_seconds
        return original(context)

    prepare.definition = original.definition
    scheduler.runner_registry = RunnerRegistry((replace(wrapper, prepare_callback=prepare),),
        registry_sha256=scheduler.runner_registry.registry_sha256)

    def permission(context, runner, *, prepared_contract):
        prepared_contract.require_complete()
        checked.append(context.attempt_id)
        state.clock.value += 100 * scheduler.lease_seconds

    scheduler.native_entry_guard = permission
    monkeypatch.setattr(state.repository, "current_attempt_lease",
        lambda **kwargs: pytest.fail("native execution checked a lease deadline"))
    monkeypatch.setattr(state.repository, "refresh_attempt_lease",
        lambda **kwargs: pytest.fail("native execution renewed a lease"))
    try:
        result = scheduler.execute("exposed.run", state.plan)
        assert result.status is OperationalStatus.SUCCEEDED
        receipt, = result.receipts
        assert checked == [receipt.attempt_id] * 3
        assert contacts.read("exposed.run", state.task.task_id).attempt_id == receipt.attempt_id
        assert state.clock.value >= 100 + 400 * scheduler.lease_seconds
    finally:
        state.bundle.close()
        state.repository.engine.dispose()


@pytest.mark.parametrize("parallel", (1, 2))
def test_completed_parent_finalization_does_not_request_new_native_permission(tmp_path, monkeypatch, parallel):
    state = _runtime(tmp_path, parallel=parallel, parent_prepared=True)
    scheduler, contacts = state.scheduler()
    checks = []

    def allow(context, runner, *, prepared_contract):
        prepared_contract.require_complete()
        assert prepared_contract.manifest == runner.manifest
        checks.append(context.attempt_id)

    scheduler.native_entry_guard = allow
    original_commit = state.receipts.commit

    def interrupt(*args, **kwargs):
        raise OSError("disclosed interruption after authenticated native child return")

    monkeypatch.setattr(state.receipts, "commit", interrupt)
    try:
        with pytest.raises(NativeParentFinalizationPending):
            scheduler.execute("exposed.run", state.plan)
        contact = contacts.read("exposed.run", state.task.task_id)
        assert checks == [contact.attempt_id] * 3
        monkeypatch.setattr(state.receipts, "commit", original_commit)
        state.clock.value += scheduler.lease_seconds + 1
        resumed, current_contacts = state.scheduler()
        resumed.native_entry_guard = lambda *a, **k: pytest.fail("pure finalization requested new effect permission")
        result = resumed.execute("exposed.run", state.plan)
        assert result.status is OperationalStatus.SUCCEEDED
        receipt, = result.receipts
        assert receipt.attempt_id == contact.attempt_id
        assert current_contacts.read("exposed.run", state.task.task_id) == contact
        assert not current_contacts.is_live_creator(contact)
        assert checks == [contact.attempt_id] * 3
    finally:
        state.bundle.close()
        state.repository.engine.dispose()


@pytest.mark.parametrize("parallel", (1, 2))
@pytest.mark.parametrize("refuse_at", (2, 3))
def test_later_leaf_and_actual_call_entry_recheck_current_permission(tmp_path, parallel, refuse_at):
    state = _runtime(tmp_path, parallel=parallel, parent_prepared=True)
    scheduler, contacts = state.scheduler()
    checked = []
    stores = []
    original_store = scheduler._native_subwork_progress

    def remember(*args, **kwargs):
        store = original_store(*args, **kwargs)
        stores.append((store, kwargs["prepared_contract"].native_work.definitions[0]))
        return store

    def permission(context, runner, *, prepared_contract):
        prepared_contract.require_complete()
        checked.append(context.attempt_id)
        if len(checked) == refuse_at:
            raise PermissionError("disclosed expiry at the later native boundary")

    scheduler._native_subwork_progress = remember
    scheduler.native_entry_guard = permission
    try:
        with pytest.raises(NativeEntryRefused):
            scheduler.execute("exposed.run", state.plan)
        parent = contacts.read("exposed.run", state.task.task_id)
        assert len(checked) == refuse_at
        assert parent is not None
        attempt, = state.repository.attempts("exposed.run")
        assert attempt.disposition is TaskAttemptDisposition.RUNNING
        store, definition = stores[0]
        inspection = store.inspect(definition)
        assert (inspection.contact is None) is (refuse_at == 2)
        assert inspection.call_entry is None and inspection.call_return is None
        assert inspection.completion is None
        assert state.receipts.read("exposed.run", state.task.task_id, attempt.attempt_id) is None
        assert _event(state) is None and state.recovery.read_terminal(state.index) is None
    finally:
        state.bundle.close()
        state.repository.engine.dispose()
