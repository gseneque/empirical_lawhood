# SPDX-License-Identifier: MPL-2.0
"""Real SQLite controls for a read-only final current attempt lease observation.

Only literal software catalogs are created. No actual run, source binding,
provider, scheduler, native worker, authority or scientific array is opened.
"""
from types import SimpleNamespace

import pytest
from sqlalchemy import delete, event, select, update

from empirical_lawhood.infrastructure.sql import (
    SQLiteOperationalRepository,
    OperationalWriteConflict,
    create_catalog_engine,
    upgrade_catalog,
)
from empirical_lawhood.infrastructure.sql.operations import OperationalQueryWorkLimitExceeded
from empirical_lawhood.infrastructure.sql.schema import lease, run_event, task_attempt, workflow_run
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.execution import OperationalAttempt, TaskAttemptDisposition, TaskBlockReason


RUN = "run.disclosed.current-attempt-lease"
TASK = "task.disclosed.native-first"
ATTEMPT = RUN + "." + TASK + ".attempt-001"
LEASE = "lease." + ATTEMPT
OWNER = "scheduler.disclosed.current-attempt"
PLAN = "a" * 64
NOW = 200
EXPIRY = 260


def _rows(engine):
    with engine.connect() as connection:
        return {table.name: tuple(dict(row) for row in connection.execute(
            select(table).order_by(table.c.pk)).mappings())
            for table in (workflow_run, task_attempt, lease, run_event)}


def _new_case(tmp_path, *, blocked=0):
    engine = create_catalog_engine("sqlite+pysqlite:///" + str(tmp_path / "literal.sqlite3"))
    upgrade_catalog(engine)
    repo = SQLiteOperationalRepository(engine)
    repo.register_run(RUN, PLAN)
    repo.set_run_status(RUN, OperationalStatus.RUNNING)
    for _ in range(blocked):
        repo.block_task(RUN, TASK, TaskBlockReason.DEPENDENCY_FAILED)
    repo.start_attempt(run_id=RUN, task_id=TASK, attempt_id=ATTEMPT,
        lease_id=LEASE, owner_id=OWNER, expires_epoch_seconds=EXPIRY)
    return SimpleNamespace(engine=engine, repo=repo)


@pytest.fixture
def case(tmp_path):
    value = _new_case(tmp_path)
    try:
        yield value
    finally:
        value.engine.dispose()


def _read(case, **changes):
    return case.repo.current_attempt_lease(**({
        "run_id": RUN, "execution_plan_sha256": PLAN, "task_id": TASK,
        "attempt_id": ATTEMPT, "lease_id": LEASE, "owner_id": OWNER,
        "at_epoch_seconds": NOW,
    } | changes))


@pytest.mark.parametrize("blocked", (0, 1, 2))
def test_real_retained_dependency_blocks_preserve_catalog_display_ordinal(tmp_path, blocked):
    case = _new_case(tmp_path, blocked=blocked)
    try:
        before = _rows(case.engine)
        result = _read(case)
        assert type(result) is OperationalAttempt
        assert result == OperationalAttempt(ATTEMPT, RUN, TASK, blocked + 1,
            TaskAttemptDisposition.RUNNING, None, LEASE, EXPIRY)
        assert _rows(case.engine) == before
        # The fixed recovery candidate remains first even when display ordinal is 2.
        assert ATTEMPT.endswith("attempt-001")
        assert tuple(row["reason_code"] for row in before["task_attempt"][:-1]) == (
            TaskBlockReason.DEPENDENCY_FAILED.value,) * blocked
    finally:
        case.engine.dispose()


def test_actual_read_is_one_bounded_select_and_does_not_renew_or_append(case):
    before = _rows(case.engine)
    statements = []
    def observe(_conn, _cursor, statement, _parameters, _context, _executemany):
        statements.append(statement)
    event.listen(case.engine, "before_cursor_execute", observe)
    try:
        assert _read(case).lease_expires_epoch_seconds == EXPIRY
    finally:
        event.remove(case.engine, "before_cursor_execute", observe)
    assert len(statements) == 1
    assert statements[0].lstrip().upper().startswith("SELECT ")
    assert _rows(case.engine) == before


def _refresh(case, **changes):
    return case.repo.refresh_attempt_lease(**({
        "run_id": RUN, "execution_plan_sha256": PLAN, "task_id": TASK,
        "attempt_id": ATTEMPT, "lease_id": LEASE, "owner_id": OWNER,
        "at_epoch_seconds": NOW, "expires_epoch_seconds": 300,
    } | changes))


def test_owned_live_lease_refresh_changes_only_liveness(case):
    before = _rows(case.engine)
    _refresh(case)
    after = _rows(case.engine)
    assert _read(case).lease_expires_epoch_seconds == 300
    assert after.keys() == before.keys()
    for table in before:
        if table != "lease":
            assert after[table] == before[table]
    assert len(after["lease"]) == len(before["lease"]) == 1
    assert after["lease"][0] == {**before["lease"][0], "expires_epoch_seconds": 300}
    # Refresh never shortens the already owned interval.
    _refresh(case, expires_epoch_seconds=280)
    assert _read(case).lease_expires_epoch_seconds == 300


@pytest.mark.parametrize("changes", (
    {"owner_id": "scheduler.foreign"}, {"lease_id": "lease.foreign"},
    {"attempt_id": "attempt.foreign"}, {"execution_plan_sha256": "b" * 64},
    {"at_epoch_seconds": EXPIRY}, {"at_epoch_seconds": EXPIRY + 1},
))
def test_refresh_cannot_take_over_or_resurrect_expired_lease(case, changes):
    before = _rows(case.engine)
    with pytest.raises(OperationalWriteConflict):
        _refresh(case, **changes)
    assert _rows(case.engine) == before


def test_refresh_rechecks_replacement_attempt_inside_atomic_update(case):
    original = case.repo.current_attempt_lease

    def replace_after_observation(**kwargs):
        value = original(**kwargs)
        case.repo.start_attempt(run_id=RUN, task_id=TASK, attempt_id=ATTEMPT + ".next",
            lease_id=LEASE + ".next", owner_id=OWNER, expires_epoch_seconds=300)
        return value

    case.repo.current_attempt_lease = replace_after_observation
    with pytest.raises(OperationalWriteConflict, match="changed before refresh"):
        _refresh(case)
    rows = _rows(case.engine)
    assert rows["lease"][0]["expires_epoch_seconds"] == EXPIRY


def test_refresh_keeps_the_existing_single_writer_boundary(case):
    from concurrent.futures import ThreadPoolExecutor

    before = _rows(case.engine)
    with ThreadPoolExecutor(max_workers=1) as pool:
        with pytest.raises(OperationalWriteConflict, match="owner thread"):
            pool.submit(_refresh, case).result()
    assert _rows(case.engine) == before


@pytest.mark.parametrize("coordinate,value", (
    ("run_id", "run.disclosed.foreign"),
    ("task_id", "task.disclosed.foreign"),
    ("attempt_id", "attempt.disclosed.foreign"),
    ("lease_id", "lease.disclosed.foreign"),
    ("owner_id", "scheduler.disclosed.foreign"),
    ("execution_plan_sha256", "b" * 64),
))
def test_exact_selected_identity_mismatch_refuses_without_writes(case, coordinate, value):
    before = _rows(case.engine)
    with pytest.raises(OperationalWriteConflict):
        _read(case, **{coordinate: value})
    assert _rows(case.engine) == before


@pytest.mark.parametrize("damage", (
    "run-state", "run-plan", "attempt-state", "attempt-reason", "attempt-task",
    "lease-owner", "lease-id", "lease-expiry", "missing-lease", "relinked-lease",
))
def test_actual_catalog_or_lease_drift_refuses_without_projection_repair(case, damage):
    with case.engine.begin() as connection:
        if damage == "run-state":
            connection.execute(update(workflow_run).values(state=OperationalStatus.FAILED.value))
        elif damage == "run-plan":
            connection.execute(update(workflow_run).values(plan_fingerprint=bytes.fromhex("b" * 64)))
        elif damage == "attempt-state":
            connection.execute(update(task_attempt).values(state=TaskAttemptDisposition.SUCCEEDED.value))
        elif damage == "attempt-reason":
            connection.execute(update(task_attempt).values(reason_code="failure.disclosed.foreign"))
        elif damage == "attempt-task":
            connection.execute(update(task_attempt).values(task_id="task.disclosed.foreign"))
        elif damage == "lease-owner":
            connection.execute(update(lease).values(owner_id="scheduler.disclosed.foreign"))
        elif damage == "lease-id":
            connection.execute(update(lease).values(lease_id="lease.disclosed.foreign"))
        elif damage == "lease-expiry":
            connection.execute(update(lease).values(expires_epoch_seconds=NOW))
        elif damage == "missing-lease":
            connection.execute(delete(lease))
        elif damage == "relinked-lease":
            run_pk = connection.execute(select(workflow_run.c.pk)).scalar_one()
            inserted = connection.execute(task_attempt.insert().values(
                attempt_id="attempt.disclosed.unrelated", workflow_run_pk=run_pk,
                task_id="task.disclosed.unrelated", state=TaskAttemptDisposition.RUNNING.value,
                reason_code=None))
            connection.execute(update(lease).values(task_attempt_pk=inserted.inserted_primary_key[0]))
        else:
            raise AssertionError(damage)
    before = _rows(case.engine)
    with pytest.raises(OperationalWriteConflict):
        _read(case)
    assert _rows(case.engine) == before


def test_matching_old_attempt_is_not_current_when_a_later_task_row_exists(case):
    case.repo.block_task(RUN, TASK, TaskBlockReason.DEPENDENCY_FAILED)
    before = _rows(case.engine)
    with pytest.raises(OperationalWriteConflict, match="latest"):
        _read(case)
    assert _rows(case.engine) == before


@pytest.mark.parametrize("disposition", ("complete", "fail", "block"))
def test_genuine_finished_row_has_no_ready_lease(case, disposition):
    if disposition == "complete":
        case.repo.complete_attempt(ATTEMPT)
    elif disposition == "fail":
        case.repo.fail_attempt(ATTEMPT, "failure.disclosed.literal")
    else:
        case.repo.block_attempt(ATTEMPT, TaskBlockReason.DEPENDENCY_FAILED)
    before = _rows(case.engine)
    with pytest.raises(OperationalWriteConflict):
        _read(case)
    assert _rows(case.engine) == before


def test_expiry_is_strict_and_new_clock_observation_does_not_extend_it(case):
    before = _rows(case.engine)
    assert _read(case, at_epoch_seconds=EXPIRY - 1).lease_expires_epoch_seconds == EXPIRY
    for at in (EXPIRY, EXPIRY + 1):
        with pytest.raises(OperationalWriteConflict, match="expired"):
            _read(case, at_epoch_seconds=at)
    assert _rows(case.engine) == before


@pytest.mark.parametrize("at", (True, False, -1, 200.0, "200"))
def test_clock_requires_actual_nonnegative_integer(case, at):
    before = _rows(case.engine)
    with pytest.raises(ValueError, match="clock"):
        _read(case, at_epoch_seconds=at)
    assert _rows(case.engine) == before


def test_query_work_budget_still_applies_to_actual_roster(tmp_path):
    case = _new_case(tmp_path, blocked=80)
    try:
        case.repo = SQLiteOperationalRepository(case.engine, query_work_limit=1)
        before = _rows(case.engine)
        with pytest.raises(OperationalQueryWorkLimitExceeded):
            _read(case)
        assert _rows(case.engine) == before
    finally:
        case.engine.dispose()
