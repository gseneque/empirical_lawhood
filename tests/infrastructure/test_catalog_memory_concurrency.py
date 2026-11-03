# SPDX-License-Identifier: MPL-2.0
"""Concurrent literal SQLite controls; no native science or authority is used."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess
import sys
from threading import Event

from empirical_lawhood.infrastructure.sql import (
    SQLiteOperationalRepository,
    create_catalog_engine,
    upgrade_catalog,
)
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.execution import TaskAttemptDisposition


def test_memory_reader_cannot_rollback_another_connection_transaction():
    engine = create_catalog_engine()
    requested, returned = Event(), Event()

    def read():
        requested.set()
        with engine.connect() as connection:
            rows = tuple(connection.exec_driver_sql("SELECT value FROM literal_probe"))
        returned.set()
        return rows

    try:
        with engine.begin() as connection:
            connection.exec_driver_sql("CREATE TABLE literal_probe (value INTEGER NOT NULL)")
        with ThreadPoolExecutor(max_workers=1) as readers:
            with engine.begin() as connection:
                connection.exec_driver_sql("INSERT INTO literal_probe VALUES (17)")
                pending = readers.submit(read)
                assert requested.wait(timeout=5)
                # Allow an independently checked-out reader to close while the
                # writer's transaction is open. A serialized reader waits here.
                returned.wait(timeout=0.2)
            assert pending.result(timeout=5) == ((17,),)
        with engine.connect() as connection:
            assert tuple(connection.exec_driver_sql("SELECT value FROM literal_probe")) == ((17,),)
    finally:
        engine.dispose()


def _concurrent_repository_case():
    engine = create_catalog_engine()
    upgrade_catalog(engine)
    repository = SQLiteOperationalRepository(engine)
    run, plan = "run.disclosed.memory-concurrency", "a" * 64
    repository.register_run(run, plan)
    repository.set_run_status(run, OperationalStatus.RUNNING)
    probe = "attempt.disclosed.reader"
    repository.start_attempt(run_id=run, task_id="task.disclosed.reader", attempt_id=probe,
        lease_id="lease.disclosed.reader", owner_id="owner.disclosed", expires_epoch_seconds=300)
    start = Event()

    def read_current():
        assert start.wait(timeout=5)
        for _ in range(100):
            actual = repository.current_attempt_lease(run_id=run, execution_plan_sha256=plan,
                task_id="task.disclosed.reader", attempt_id=probe, lease_id="lease.disclosed.reader",
                owner_id="owner.disclosed", at_epoch_seconds=200)
            assert actual.disposition is TaskAttemptDisposition.RUNNING
        return True

    try:
        with ThreadPoolExecutor(max_workers=8) as readers:
            pending = [readers.submit(read_current) for _ in range(8)]
            start.set()
            for index in range(80):
                task = "task.disclosed.writer." + str(index)
                attempt = "attempt.disclosed.writer." + str(index)
                repository.start_attempt(run_id=run, task_id=task, attempt_id=attempt,
                    lease_id="lease." + attempt, owner_id="owner.disclosed", expires_epoch_seconds=300)
                repository.complete_attempt(attempt)
            assert all(future.result(timeout=5) for future in pending)
        with engine.connect() as connection:
            assert connection.exec_driver_sql(
                "SELECT COUNT(*) FROM task_attempt WHERE state = 'SUCCEEDED'"
            ).scalar_one() == 80
            assert connection.exec_driver_sql("SELECT COUNT(*) FROM lease").scalar_one() == 1
    finally:
        engine.dispose()


def test_parallel_bounded_lease_reads_and_owner_writes_complete(tmp_path):
    # Isolate a possible DBAPI deadlock so a regression fails with a finite
    # diagnostic instead of hanging the test process or touching a real run.
    result = subprocess.run([sys.executable, str(Path(__file__).resolve())], cwd=tmp_path,
        text=True, capture_output=True, timeout=30, check=False)
    assert result.returncode == 0, result.stdout + result.stderr


if __name__ == "__main__":
    _concurrent_repository_case()
