# SPDX-License-Identifier: MPL-2.0
"""Eight actual worker processes contending for disclosed controller custody.

The worker echoes a software literal. No scientific acquisition, authority or
native completion is constructed. Existing controls cover genuine idle/hard stops.
"""
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
import os
from threading import Barrier, Lock
import time

from empirical_lawhood.infrastructure.execution import LocalProcessExecutor
from empirical_lawhood.infrastructure.native_subwork_ipc import NativeSubworkPipeService
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from tests.runtime_platform.test_native_subwork import ExposedInput, _store
from tests.runtime_platform.test_worker_preflight import _case, _native_work
from tests.runtime_platform.test_worker_progress_admission import ExposedCustodyWaitRunner, _liveness


def test_eight_workers_wait_for_contended_custody_without_inventing_progress(tmp_path, monkeypatch):
    count = 8
    for index in range(count):
        (tmp_path / str(index)).mkdir()
    cases = tuple(_case(tmp_path / str(index), actual=True, native=True) for index in range(count))
    barrier, custody_lock, seen = Barrier(count, timeout=30), Lock(), []
    original = NativeSubworkPipeService._dispatch

    def service(self, operation, arguments):
        if operation == 'parent-contact':
            barrier.wait()
            # All eight controllers wait inside the actual synchronous service.
            # The final wait exceeds the unchanged one-second native idle gap.
            with custody_lock:
                time.sleep(0.2)
                seen.append(operation)
                return original(self, operation, arguments)
        return original(self, operation, arguments)

    monkeypatch.setattr(NativeSubworkPipeService, '_dispatch', service)

    def execute(case):
        plane, bundle, selected, context, contract, parent = case
        store = _store(plane, parent, bundle.manifests)
        runner = ExposedCustodyWaitRunner(before=0, after=0,
            definitions=selected.selected_definitions, rosters=selected.selected_rosters)
        counters = []

        def enter():
            store.parent_contacts.begin(parent)
            return parent, store

        try:
            result = LocalProcessExecutor(scratch_root=plane.root).execute_deadline_free(runner, context,
                progress_contract=_liveness(), progress_callback=counters.append,
                prepared_contract=contract, native_work_preparer=_native_work, native_entry=enter)
            raw = result.outputs[0].payload
            record = decode_canonical_bytes(raw, ExposedInput, maximum_bytes=len(raw))
            before, after = map(int, record.value.split(':'))
            assert before == after != os.getpid()
            assert counters == []
            assert _liveness().maximum_no_progress_gap_seconds == Decimal(1)
            return before
        finally:
            store.parent_contacts.retire_live_creator(parent)
            bundle.close()

    with ThreadPoolExecutor(max_workers=count) as pool:
        pids = tuple(pool.map(execute, cases))
    assert len(set(pids)) == count and seen == ['parent-contact'] * count
