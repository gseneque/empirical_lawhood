# SPDX-License-Identifier: MPL-2.0
"""Actual exposed worker timing controls; no scientific acquisition or authority."""

from decimal import Decimal
import os
import time

import pytest

from empirical_lawhood.infrastructure.execution import (
    CampaignElapsedBoundaryReached, LocalProcessExecutor, ProgressStalledError,
)
from empirical_lawhood.infrastructure.native_subwork_ipc import NativeSubworkPipeService
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.runtime.execution_envelope import ProgressHeartbeat, ProgressLivenessContract
from tests.runtime_platform.test_native_subwork import ExposedInput, _store
from tests.runtime_platform.test_worker_preflight import ExposedPidRunner, _case, _native_work


class ExposedDelayedProgressRunner(ExposedPidRunner):
    def __init__(self, *, preflight_seconds=0, work_seconds=0.15, emit_progress=False):
        super().__init__()
        self.preflight_seconds = preflight_seconds
        self.work_seconds = work_seconds
        self.emit_progress = emit_progress

    def preflight(self, context):
        super().preflight(context)
        time.sleep(self.preflight_seconds)

    def execute_with_progress(self, context, emitter):
        if self.emit_progress:
            emitter.advance(Decimal(1))
        time.sleep(self.work_seconds)
        return super().execute(context)


class ExposedCustodyWaitRunner(ExposedPidRunner):
    def __init__(self, *, before, after, definitions, rosters):
        super().__init__(definitions=definitions, rosters=rosters)
        self.before, self.after = before, after

    def execute_with_native_subwork(self, context, native_subwork, progress=None):
        time.sleep(self.before)
        assert native_subwork.parent_contact.task_id == context.task_id
        time.sleep(self.after)
        return super().execute(context)


def _liveness():
    return ProgressLivenessContract("progress.exposed.admission", ProgressHeartbeat.SCHEMA,
        "exposed-work", Decimal(1), True, True)


@pytest.mark.parametrize("slow_boundary", ("worker-preflight", "parent-admission"))
def test_preflight_and_parent_admission_do_not_spend_native_progress_gap(tmp_path, slow_boundary):
    plane, bundle, _, context, contract, parent = _case(tmp_path, actual=True, native=True, nested=False)
    runner = ExposedDelayedProgressRunner(preflight_seconds=2 if slow_boundary == "worker-preflight" else 0)
    store = _store(plane, parent)
    entries = []
    counters = []

    def enter():
        if slow_boundary == "parent-admission":
            time.sleep(2)
        store.parent_contacts.begin(parent)
        entries.append(time.monotonic())
        return parent, None

    started = time.monotonic()
    try:
        result = LocalProcessExecutor(scratch_root=plane.root).execute_deadline_free(runner, context,
            progress_contract=_liveness(), progress_callback=counters.append,
            prepared_contract=contract, native_work_preparer=_native_work, native_entry=enter)
        assert time.monotonic() - started >= 2
        raw = result.outputs[0].payload
        record = decode_canonical_bytes(raw, ExposedInput, maximum_bytes=len(raw))
        preflight_pid, work_pid = map(int, record.value.split(":"))
        assert preflight_pid == work_pid and work_pid != os.getpid()
        assert len(entries) == 1
        assert store.parent_contacts.read(context.run_id, context.task_id) == parent
        assert counters == []  # Admission is not invented scientific progress.
        assert all(port.bytes_read == 0 for port in context.input_ports)
    finally:
        store.parent_contacts.retire_live_creator(parent)
        bundle.close()


@pytest.mark.parametrize("emit_progress", (False, True), ids=("before-first-work", "after-progress"))
def test_native_progress_gap_still_stops_admitted_stalled_worker(tmp_path, emit_progress):
    plane, bundle, _, context, contract, parent = _case(tmp_path, actual=True, native=True, nested=False)
    runner = ExposedDelayedProgressRunner(preflight_seconds=2, work_seconds=3, emit_progress=emit_progress)
    store = _store(plane, parent)
    entries = []
    counters = []

    def enter():
        store.parent_contacts.begin(parent)
        entries.append(time.monotonic())
        return parent, None

    try:
        with pytest.raises(ProgressStalledError, match="no qualified progress"):
            LocalProcessExecutor(scratch_root=plane.root).execute_deadline_free(runner, context,
                progress_contract=_liveness(), progress_callback=counters.append,
                prepared_contract=contract, native_work_preparer=_native_work, native_entry=enter)
        assert len(entries) == 1
        assert time.monotonic() - entries[0] >= 1
        assert store.parent_contacts.read(context.run_id, context.task_id) == parent
        assert counters == ([Decimal(1)] if emit_progress else [])
    finally:
        store.parent_contacts.retire_live_creator(parent)
        bundle.close()


def test_campaign_hard_limit_still_covers_worker_preflight(tmp_path):
    plane, bundle, _, context, contract, parent = _case(tmp_path, actual=True, native=True, nested=False)
    runner = ExposedDelayedProgressRunner(preflight_seconds=2)
    store = _store(plane, parent)
    try:
        with pytest.raises(CampaignElapsedBoundaryReached):
            LocalProcessExecutor(scratch_root=plane.root).execute_deadline_free_until(runner, context,
                progress_contract=_liveness(), progress_callback=lambda _value: pytest.fail("no admitted work"),
                hard_remaining_seconds=Decimal("0.5"), prepared_contract=contract,
                native_work_preparer=_native_work,
                native_entry=lambda: pytest.fail("campaign exhausted before native admission"))
        assert store.parent_contacts.read(context.run_id, context.task_id) is None
    finally:
        bundle.close()


@pytest.mark.parametrize('case', ('controller-wait', 'accumulated-idle', 'campaign-limit'))
def test_controller_custody_wait_preserves_native_idle_and_campaign_limits(tmp_path, monkeypatch, case):
    plane, bundle, selected, context, contract, parent = _case(tmp_path, actual=True, native=True)
    store = _store(plane, parent, bundle.manifests)
    runner = ExposedCustodyWaitRunner(before=0.65 if case == 'accumulated-idle' else 0,
        after=0.65 if case == 'accumulated-idle' else 0.2,
        definitions=selected.selected_definitions, rosters=selected.selected_rosters)
    original = NativeSubworkPipeService._dispatch
    calls, counters = [], []
    clock, offset = time.monotonic, 0
    if case == 'campaign-limit':
        monkeypatch.setattr(time, 'monotonic', lambda: clock() + offset)

    def service(self, operation, arguments):
        nonlocal offset
        if operation == 'parent-contact':
            calls.append(operation)
            time.sleep(2)
            if case == 'campaign-limit':
                offset = 60  # Advance the controller clock during its own service.
        return original(self, operation, arguments)

    monkeypatch.setattr(NativeSubworkPipeService, '_dispatch', service)

    def enter():
        store.parent_contacts.begin(parent)
        return parent, store

    options = dict(progress_contract=_liveness(), progress_callback=counters.append,
        prepared_contract=contract, native_work_preparer=_native_work, native_entry=enter)
    executor = LocalProcessExecutor(scratch_root=plane.root)
    try:
        if case == 'campaign-limit':
            with pytest.raises(CampaignElapsedBoundaryReached):
                executor.execute_deadline_free_until(runner, context,
                    hard_remaining_seconds=Decimal(30), **options)
        elif case == 'accumulated-idle':
            with pytest.raises(ProgressStalledError):
                executor.execute_deadline_free(runner, context, **options)
        else:
            result = executor.execute_deadline_free(runner, context, **options)
            raw = result.outputs[0].payload
            record = decode_canonical_bytes(raw, ExposedInput, maximum_bytes=len(raw))
            preflight_pid, work_pid = map(int, record.value.split(':'))
            assert preflight_pid == work_pid != os.getpid()
        assert calls == ['parent-contact']
        assert counters == []  # Controller service is not scientific progress.
    finally:
        store.parent_contacts.retire_live_creator(parent)
        bundle.close()
