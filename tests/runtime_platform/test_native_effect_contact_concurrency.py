# SPDX-License-Identifier: MPL-2.0
"""Native admission atomicity with independent synthetic launches and catalogs."""

import multiprocessing
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from tests.runtime_platform.test_execution_scheduler import _plane
from tests.runtime_platform.test_native_effect_contact import _native_runtime
from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
from empirical_lawhood.infrastructure.sql import create_catalog_engine
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.native_effects import NativeEffectContact


def _contact(plan):
    task = next(value for value in plan.tasks if value.task_id == "prepare")
    return NativeEffectContact(plan.source_plan.object_id, task.task_id, "attempt.synthetic-contact",
        ObjectIdentity.from_record(plan.execution_plan_id, plan),
        ObjectIdentity.from_record(task.task_id, task), plan.implementation_commit, (), ())


def _store(path, contact):
    return ExternalNativeEffectContactStore(plane=_plane(path), execution_plan=contact.execution_plan,
        visibility_ceiling=VisibilityCeiling.PROSPECTIVE, outcome_access=OutcomeAccess.OUTCOME_BLIND)


def _launch(path, launcher, fixture, barrier, entered, release, queue, timing):
    result = {"launcher": launcher, "worker_entries": 0, "native_publications_created": [], "elapsed_begin_calls": 0}
    repository = None
    try:
        # Resource catalogs are independent; only immutable external custody
        # is shared. Both schedulers therefore consider the attempt runnable.
        catalog = path / f"catalog-launch-{launcher}.sqlite3"
        with patch("tests.runtime_platform.test_execution_scheduler.create_catalog_engine",
                   side_effect=lambda _url: create_catalog_engine(f"sqlite+pysqlite:///{catalog}")):
            scheduler, repository, store, runners, plan = _native_runtime(path, fixture)
        original_read, original_write = store.read, store.plane.write
        original_elapsed_begin = scheduler._begin_campaign_elapsed_interval
        runner = next(value for value in runners if value.manifest.capability_key == plan.tasks[0].capability.capability_key)
        original_execute = runner.execute

        def wait_for_contender(context):
            entered.set()
            if not release.wait(timeout=30):
                raise AssertionError("the losing launch did not finish its refusal")
            return original_execute(context)

        def record_write(request):
            publication = original_write(request)
            if request.payload_schema == NativeEffectContact.SCHEMA:
                result["native_publications_created"].append(publication.created)
            return publication

        def record_elapsed_begin(run_id):
            result["elapsed_begin_calls"] += 1
            return original_elapsed_begin(run_id)

        runner.execute, store.plane.write = wait_for_contender, record_write
        scheduler._begin_campaign_elapsed_interval = record_elapsed_begin
        if timing == "simultaneous":
            barrier.wait(timeout=30)
        elif launcher == 1 and not entered.wait(timeout=30):
            raise AssertionError("the owner did not commit contact and enter its synthetic worker")
        try:
            report = scheduler.execute(plan.source_plan.object_id, plan)
            result["status"] = report.status.value
            result["receipt_sha256"] = report.receipts[0].fingerprint()
        except Exception as error:
            result["error_type"], result["error"] = type(error).__name__, str(error)
            release.set()
        result["worker_entries"] = sum(len(runner.contexts) for runner in runners)
        result["catalog_attempt_count"] = len(repository.attempts(plan.source_plan.object_id))
        marker = original_read(plan.source_plan.object_id, "prepare")
        result["contact_sha256"] = None if marker is None else marker.fingerprint()
    except Exception as error:
        result["setup_error_type"], result["setup_error"] = type(error).__name__, str(error)
    finally:
        if repository is not None:
            repository.engine.dispose()
        queue.put(result)


def _publish_contact(path, contact, barrier, queue):
    store = _store(path, contact)
    original_read = store.read
    first_read = True

    def absent_before_publication(run_id, task_id):
        nonlocal first_read
        observed = original_read(run_id, task_id)
        if first_read:
            first_read = False
            assert observed is None
            barrier.wait(timeout=30)
        return observed

    store.read = absent_before_publication
    try:
        store.begin(contact)
        queue.put({"admitted": True})
    except ValueError as error:
        queue.put({"admitted": False, "reason": str(error)})


def _crash_after_native_contact(path, fixture):
    scheduler, _repository, store, _runners, plan = _native_runtime(path, fixture)
    original_begin = store.begin

    def commit_then_die(contact):
        original_begin(contact)
        os._exit(38)

    store.begin = commit_then_die
    scheduler.execute(plan.source_plan.object_id, plan)
    raise AssertionError("the injected native-contact interruption did not occur")


def _crash_after_contact_payload(path, contact):
    store = _store(path, contact)
    target = path / store._path(contact.run_id, contact.task_id)
    original_move = store.plane._move_file_once

    def publish_then_crash(source, destination):
        original_move(source, destination)
        if destination == target:
            os._exit(37)

    store.plane._move_file_once = publish_then_crash
    store.begin(contact)
    raise AssertionError("the injected process interruption did not occur")


def test_false_created_matching_marker_never_admits_worker(tmp_path, protocol_fixture, monkeypatch):
    contact = _contact(protocol_fixture.execution_plan)
    store = _store(tmp_path, contact)
    observations = iter((None, contact))
    monkeypatch.setattr(store, "read", lambda *_: next(observations))
    monkeypatch.setattr(store.plane, "write", lambda _request: SimpleNamespace(created=False))
    worker_entries = []
    with pytest.raises(ValueError, match="reused"):
        store.begin(contact)
        worker_entries.append(contact)
    assert worker_entries == []


def test_stale_absence_read_cannot_reuse_another_instances_real_publication(tmp_path, protocol_fixture, monkeypatch):
    contact = _contact(protocol_fixture.execution_plan)
    creator = _store(tmp_path, contact)
    creator.begin(contact)
    raw_path = tmp_path / creator._path(contact.run_id, contact.task_id)
    before = raw_path.read_bytes()
    contender = _store(tmp_path, contact)
    observations = iter((None, contact))
    monkeypatch.setattr(contender, "read", lambda *_: next(observations))
    with pytest.raises(ValueError, match="reused"):
        contender.begin(contact)
    assert raw_path.read_bytes() == before == contact.canonical_bytes()
    assert creator.read(contact.run_id, contact.task_id) == contact


@pytest.mark.parametrize("timing", ("simultaneous", "staggered"))
def test_concurrent_scheduler_launches_preserve_winning_receipt_and_terminal(tmp_path, protocol_fixture, timing):
    path = tmp_path / timing
    path.mkdir()
    context = multiprocessing.get_context("spawn")
    barrier, entered, release, queue = context.Barrier(2), context.Event(), context.Event(), context.Queue()
    children = [context.Process(target=_launch, args=(path, i, protocol_fixture, barrier, entered, release, queue, timing)) for i in range(2)]
    try:
        for child in children:
            child.start()
        results = [queue.get(timeout=60) for _ in children]
        for child in children:
            child.join(timeout=10)
            assert child.exitcode == 0
        assert not any("setup_error" in result for result in results), results
        assert sum(result["worker_entries"] for result in results) == 1, results
        assert sorted(result["native_publications_created"] for result in results) == [[], [True]], results
        winner = next(result for result in results if result["native_publications_created"] == [True])
        loser = next(result for result in results if result["native_publications_created"] == [])
        assert winner["worker_entries"] == 1 and loser["worker_entries"] == 0, results
        assert winner["status"] == "SUCCEEDED" and loser["error_type"] == "LiveLeaseError", results
        assert winner["elapsed_begin_calls"] == 1 and loser["elapsed_begin_calls"] == 0
        assert winner["catalog_attempt_count"] == 1 and loser["catalog_attempt_count"] == 0
        if loser["contact_sha256"] is not None:
            assert winner["contact_sha256"] == loser["contact_sha256"]
        assert all((path / f"catalog-launch-{i}.sqlite3").is_file() for i in range(2))
        # Authenticate the winner from external primary custody with a third,
        # fresh catalog, rather than trusting either launch's local projection.
        scheduler, repository, store, runners, plan = _native_runtime(path, protocol_fixture)
        try:
            marker = store.read(plan.source_plan.object_id, "prepare")
            receipt = scheduler.receipt_store.read(marker.run_id, marker.task_id, marker.attempt_id)
            assert receipt is not None and receipt.fingerprint() == winner["receipt_sha256"]
            terminal = scheduler.recovery_store.read_terminal(scheduler.recovery_index)
            assert terminal.operational_status == "SUCCEEDED"
            assert terminal.completed_task_ids == ("prepare",)
            assert terminal.failed_task_ids == terminal.blocked_task_ids == ()
            binding = scheduler.recovery_index.task("prepare").attempts[0]
            event = scheduler.recovery_store.read_event(scheduler.recovery_index, binding.event_relative_path)
            assert event.failure is None and event.receipt_id == receipt.receipt_id
            assert all(not runner.contexts for runner in runners)
        finally:
            repository.engine.dispose()
    finally:
        for child in children:
            if child.is_alive():
                child.terminate()
                child.join(timeout=10)
        queue.close()


def test_atomic_marker_publication_rejects_identical_concurrent_creator(tmp_path, protocol_fixture):
    contact = _contact(protocol_fixture.execution_plan)
    context = multiprocessing.get_context("spawn")
    barrier, queue = context.Barrier(2), context.Queue()
    children = [context.Process(target=_publish_contact, args=(tmp_path, contact, barrier, queue)) for _ in range(2)]
    try:
        for child in children:
            child.start()
        results = [queue.get(timeout=60) for _ in children]
        for child in children:
            child.join(timeout=10)
            assert child.exitcode == 0
        assert sorted(result["admitted"] for result in results) == [False, True]
        assert "reused" in next(result["reason"] for result in results if not result["admitted"])
        assert _store(tmp_path, contact).read(contact.run_id, contact.task_id) == contact
    finally:
        for child in children:
            if child.is_alive():
                child.terminate()
                child.join(timeout=10)
        queue.close()


def test_process_death_releases_run_claim_but_contact_grants_no_retry(tmp_path, protocol_fixture):
    context = multiprocessing.get_context("spawn")
    child = context.Process(target=_crash_after_native_contact, args=(tmp_path, protocol_fixture))
    child.start()
    try:
        child.join(timeout=30)
        assert child.exitcode == 38
        # Ignore the interrupted process's catalog and use a fresh projection.
        with patch("tests.runtime_platform.test_execution_scheduler.create_catalog_engine",
                   side_effect=lambda _: create_catalog_engine(f"sqlite+pysqlite:///{tmp_path / 'fresh-catalog.sqlite3'}")):
            scheduler, repository, store, runners, plan = _native_runtime(tmp_path, protocol_fixture)
        try:
            before = store.read(plan.source_plan.object_id, "prepare")
            report = scheduler.execute(plan.source_plan.object_id, plan)
            assert report.status.value == "BLOCKED"
            assert store.read(plan.source_plan.object_id, "prepare") == before
            assert all(not runner.contexts for runner in runners)
        finally:
            repository.engine.dispose()
    finally:
        if child.is_alive():
            child.terminate()
            child.join(timeout=10)


def test_completed_replay_preserves_run_lock_bytes_and_mtime(tmp_path, protocol_fixture):
    scheduler, repository, _store_value, runners, plan = _native_runtime(tmp_path, protocol_fixture)
    try:
        first = scheduler.execute(plan.source_plan.object_id, plan)
        assert first.status.value == "SUCCEEDED"
        path = tmp_path / "runs" / plan.source_plan.object_id / ".native-execution.lock"
        before = (path.read_bytes(), path.stat().st_mtime_ns)
        entries = sum(len(runner.contexts) for runner in runners)
        second = scheduler.execute(plan.source_plan.object_id, plan)
        assert second.status.value == "SUCCEEDED"
        assert second.receipts == first.receipts
        assert (path.read_bytes(), path.stat().st_mtime_ns) == before
        assert before[0] == b""
        assert sum(len(runner.contexts) for runner in runners) == entries == 1
    finally:
        repository.engine.dispose()


def test_publication_exception_after_commit_retains_contact_and_grants_no_repeat(tmp_path, protocol_fixture, monkeypatch):
    contact = _contact(protocol_fixture.execution_plan)
    store = _store(tmp_path, contact)
    original_write = store.plane.write

    def commit_then_fail(request):
        publication = original_write(request)
        assert publication.created is True
        raise OSError("synthetic interruption after durable contact publication")

    monkeypatch.setattr(store.plane, "write", commit_then_fail)
    with pytest.raises(OSError, match="synthetic interruption"):
        store.begin(contact)
    assert store.read(contact.run_id, contact.task_id) == contact
    again = _store(tmp_path, contact)
    with pytest.raises(ValueError, match="already committed"):
        again.begin(contact)


def test_process_death_between_payload_and_manifest_refuses_repeated_contact(tmp_path, protocol_fixture):
    contact = _contact(protocol_fixture.execution_plan)
    context = multiprocessing.get_context("spawn")
    child = context.Process(target=_crash_after_contact_payload, args=(tmp_path, contact))
    child.start()
    try:
        child.join(timeout=30)
        assert child.exitcode == 37
        store = _store(tmp_path, contact)
        path = tmp_path / store._path(contact.run_id, contact.task_id)
        assert path.read_bytes() == contact.canonical_bytes()
        assert not Path(str(path) + ".manifest.json").exists()
        with pytest.raises(ValueError, match="partial"):
            store.read(contact.run_id, contact.task_id)
        with pytest.raises(ValueError, match="partial"):
            store.begin(contact)
        assert path.read_bytes() == contact.canonical_bytes()
    finally:
        if child.is_alive():
            child.terminate()
            child.join(timeout=10)
