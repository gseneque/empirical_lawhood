# SPDX-License-Identifier: MPL-2.0
"""Bounded mutable operational snapshots; these are not scientific evidence."""

from __future__ import annotations

from collections import deque
from datetime import UTC, datetime
import json
import math
import os
from pathlib import Path
import re
import stat
import sys
from threading import Event, Lock, Thread, current_thread
import time
from uuid import uuid4

from empirical_lawhood.storage.atomic_files import rename_noreplace
from empirical_lawhood.storage.bounded_io import read_bounded_bytes
from empirical_lawhood.execution.progress import current_progress, progress_reporting


MAX_PROGRESS_BYTES = 64 * 1024
MAX_COMPLETED_STEPS = 64
_SCHEMA = "empirical-lawhood/operational-progress.v2"
_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}\Z")
_LABEL = re.compile(r"[A-Za-z0-9][A-Za-z0-9 ._:/-]{0,127}\Z")
_MAX_COUNTER = 2**63 - 1
_STATUSES = frozenset(("RUNNING", "RETURNED", "FAILED", "INTERRUPTED"))
_FIELDS = frozenset(("schema", "operation", "phase", "done", "total", "failed", "percent",
    "updated_at_utc", "elapsed_seconds", "pid", "status", "unit", "detail", "sequence",
    "phase_elapsed_seconds", "activity_age_seconds", "heartbeat", "task_id", "workflow_done",
    "workflow_total", "workflow_failed", "workflow_percent", "workflow_unit", "completed_steps", "completed_steps_total", "completed_steps_omitted"))


def _token(value: str) -> None:
    if type(value) is not str or _TOKEN.fullmatch(value) is None:
        raise ValueError("progress phase must be a bounded token")


def _operation(value: str) -> None:
    if type(value) is not str or _LABEL.fullmatch(value) is None or value != value.strip():
        raise ValueError("progress operation must be a bounded safe label")


def _counter(value: int | None, *, optional: bool = True) -> None:
    if value is None and optional:
        return
    if type(value) is not int or not 0 <= value <= _MAX_COUNTER:
        raise ValueError("progress counters must be bounded nonnegative integers")


def _counters(done: int | None, total: int | None, failed: int) -> None:
    _counter(done)
    _counter(total)
    _counter(failed, optional=False)
    if done is not None and total is not None and done > total:
        raise ValueError("progress done exceeds its denominator")
    if (done is not None and failed > done) or (total is not None and failed > total):
        raise ValueError("progress failures exceed the observed population")


def _percent(done: int | None, total: int | None) -> float | None:
    return None if done is None or total in (None, 0) else done / total * 100


def _parent(path: Path) -> int:
    """Open an existing real parent, refusing links in every path component."""
    if not path.is_absolute() or ".." in path.parts or not path.name:
        raise ValueError("progress destination must have an unambiguous parent")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    descriptor = os.open(path.anchor, flags)
    try:
        for part in path.parts[1:-1]:
            child = os.open(part, flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def _identity(value: os.stat_result) -> tuple[int, int, int, int]:
    return value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns


class OperationalProgressReporter:
    """Throttled CLI and atomic UI snapshots owned by one live invocation.

    The heartbeat measures controller liveness, not solver advancement. A
    bounded latest snapshot is enough for a UI reader; no unbounded telemetry
    history, scientific fsync or evidence reauthentication is introduced.
    """

    def __init__(self, path: Path | None, operation: str, minimum_interval: float = 1.0,
                 *, expected_parent_device: int | None = None, stream=None,
                 heartbeat_interval: float = 2.0) -> None:
        _operation(operation)
        for value in (minimum_interval, heartbeat_interval):
            if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
                raise ValueError("progress interval must be finite and nonnegative")
        if heartbeat_interval == 0:
            raise ValueError("heartbeat interval must be positive")
        selected = None if path is None else Path(path)
        if selected is not None and ".." in selected.parts:
            raise ValueError("progress destination cannot traverse parents")
        self.path = None if selected is None else selected.absolute()
        self.operation, self.stream = operation, stream
        self.expected_parent_device = expected_parent_device
        self.minimum_interval, self.heartbeat_interval = minimum_interval, heartbeat_interval
        self._started = time.monotonic()
        self._last_write = self._started
        self._phase_started = self._last_activity = self._started
        self._current = ("starting", None, None, 0, "items", None, None)
        self._workflow = (None, None, 0, "tasks")
        self._completed_steps = deque(maxlen=MAX_COMPLETED_STEPS)
        self._completed_steps_total = 0
        self._owned: tuple[int, int, int, int] | None = None
        self._error: str | None = None
        self._finished = False
        self._scope = None
        self._lock = Lock()
        self._sequence = 0
        self._pid = os.getpid()
        self._stop = Event()
        self._thread = None
        self._parent = None
        self._followers = []
        self._publish("RUNNING", self._started, initial=True)

    def __enter__(self) -> OperationalProgressReporter:
        if os.getpid() != self._pid or self._scope is not None or self._finished:
            raise RuntimeError("progress reporter is not available for a new lifetime")
        parent = current_progress()
        if isinstance(parent, OperationalProgressReporter):
            self._parent = parent
            with parent._lock:
                parent._followers.append(self)
        self._scope = progress_reporting(self)
        self._scope.__enter__()
        if self._parent is None:
            self._thread = Thread(target=self._heartbeats, name="el-operational-progress", daemon=True)
            self._thread.start()
        return self

    def __exit__(self, kind, value, traceback) -> bool:
        try:
            code = getattr(value, "exit_code", getattr(value, "code", None))
            status = ("RETURNED" if kind is None or code == 0 else
                      "INTERRUPTED" if issubclass(kind, (KeyboardInterrupt, SystemExit)) else "FAILED")
            self.finish(status)
        finally:
            scope, self._scope = self._scope, None
            if scope is not None:
                scope.__exit__(kind, value, traceback)
        return False

    def _heartbeats(self) -> None:
        while not self._stop.wait(self.heartbeat_interval):
            self.heartbeat()

    def heartbeat(self) -> None:
        """Publish unchanged counters with fresh liveness and activity age."""
        if os.getpid() != self._pid:
            return
        with self._lock:
            if not self._finished:
                self._publish("RUNNING", time.monotonic(), heartbeat=True)
                for follower in tuple(self._followers):
                    follower.heartbeat()

    @property
    def active_in_process(self) -> bool:
        return os.getpid() == self._pid and not self._finished

    @property
    def error(self) -> str | None:
        return self._error

    def update(self, *, phase: str, done: int | None = None, total: int | None = None,
               failed: int = 0, unit: str = "items", detail: str | None = None,
               started_at: float | None = None, task_id: str | None = None) -> None:
        if os.getpid() != self._pid:
            return
        if self._parent is not None:
            self._parent.update(phase=phase, done=done, total=total, failed=failed,
                unit=unit, detail=detail, started_at=started_at, task_id=task_id)
        with self._lock:
            if self._finished:
                return
            _token(phase)
            _token(unit)
            if task_id is not None:
                _token(task_id)
            _counters(done, total, failed)
            if detail is not None and (type(detail) is not str or len(detail) > 256
                                       or any(ord(c) < 32 for c in detail)):
                raise ValueError("progress detail must be a bounded single line")
            previous_phase = self._current[0]
            now = time.monotonic()
            self._last_activity = now
            if started_at is not None:
                if type(started_at) not in (int, float) or not math.isfinite(started_at) or started_at > now:
                    raise ValueError("progress phase clock is invalid")
                self._phase_started = started_at
            elif phase != previous_phase:
                self._phase_started = now
            self._current = phase, done, total, failed, unit, detail, task_id
            # Phase changes are coalesced too: deep recursive graphs must not
            # perform one file replacement and terminal write for every node.
            if previous_phase == "starting" or now - self._last_write >= self.minimum_interval:
                self._publish("RUNNING", now)

    def workflow_update(self, *, done: int, total: int, failed: int = 0, unit: str = "tasks") -> None:
        if os.getpid() != self._pid:
            return
        if self._parent is not None:
            self._parent.workflow_update(done=done, total=total, failed=failed, unit=unit)
        with self._lock:
            if self._finished:
                return
            _counters(done, total, failed)
            _token(unit)
            self._workflow = done, total, failed, unit
            self._last_activity = time.monotonic()
            if self._last_activity - self._last_write >= self.minimum_interval:
                self._publish("RUNNING", self._last_activity)

    def step_completed(self, *, phase: str, done: int, total: int | None, unit: str,
                       elapsed_seconds: float, status: str) -> None:
        if os.getpid() != self._pid:
            return
        if self._parent is not None:
            self._parent.step_completed(phase=phase, done=done, total=total, unit=unit,
                elapsed_seconds=elapsed_seconds, status=status)
        with self._lock:
            if self._finished:
                return
            _token(phase)
            _token(unit)
            _counters(done, total, 0)
            if status not in _STATUSES - {"RUNNING"} or not math.isfinite(elapsed_seconds) or elapsed_seconds < 0:
                raise ValueError("completed step is invalid")
            self._completed_steps_total += 1
            self._completed_steps.append({"phase": phase, "done": done, "total": total, "unit": unit,
                "elapsed_seconds": elapsed_seconds, "status": status})

    def finish(self, status: str = "RETURNED") -> None:
        """Force a final partial/unknown snapshot and stop the heartbeat owner."""
        if os.getpid() != self._pid:
            return
        with self._lock:
            if self._finished:
                return
            if status not in _STATUSES - {"RUNNING"}:
                raise ValueError("progress finish status is invalid")
            self._finished = True
            self._stop.set()
            self._publish(status, time.monotonic())
        if self._parent is not None:
            with self._parent._lock:
                self._parent._followers.remove(self)
            self._parent = None
        if self._thread is not None and self._thread is not current_thread():
            self._thread.join(timeout=self.heartbeat_interval + 1)

    def _publish(self, status: str, now: float, *, initial: bool = False, heartbeat: bool = False) -> None:
        if os.getpid() != self._pid:
            return
        phase, done, total, failed, unit, detail, task_id = self._current
        workflow_done, workflow_total, workflow_failed, workflow_unit = self._workflow
        self._sequence += 1
        document = {"schema": _SCHEMA, "operation": self.operation, "phase": phase,
            "done": done, "total": total, "failed": failed, "percent": _percent(done, total),
            "updated_at_utc": datetime.now(UTC).isoformat(),
            "elapsed_seconds": max(0.0, now - self._started), "pid": self._pid, "status": status,
            "unit": unit, "detail": detail, "sequence": self._sequence, "task_id": task_id,
            "phase_elapsed_seconds": max(0.0, now - self._phase_started),
            "activity_age_seconds": max(0.0, now - self._last_activity), "heartbeat": heartbeat,
            "workflow_done": workflow_done, "workflow_total": workflow_total,
            "workflow_failed": workflow_failed, "workflow_unit": workflow_unit, "workflow_percent": _percent(workflow_done, workflow_total),
            "completed_steps": list(self._completed_steps), "completed_steps_total": self._completed_steps_total,
            "completed_steps_omitted": self._completed_steps_total - len(self._completed_steps)}
        if self.path is not None and self._error is None:
            try:
                raw = (json.dumps(document, allow_nan=False, separators=(",", ":")) + "\n").encode()
                if len(raw) > MAX_PROGRESS_BYTES:
                    raise ValueError("progress snapshot exceeds its bound")
                self._install(raw)
            except Exception as error:
                if initial:
                    raise
                self._error = type(error).__name__
                try:
                    sys.stderr.write("Progress file disabled (" + self._error + ").\n")
                except Exception:
                    pass
        if self.stream is not None:
            try:
                self.stream.write(format_progress(document) + "\n")
                self.stream.flush()
            except Exception:
                self.stream = None
        self._last_write = now


    def _install(self, raw: bytes) -> None:
        parent = _parent(self.path)
        temporary = ".el-progress." + uuid4().hex + ".tmp"
        descriptor = -1
        created: tuple[int, int, int, int] | None = None
        installed = False
        try:
            if self.expected_parent_device is not None and os.fstat(parent).st_dev != self.expected_parent_device:
                raise OSError("progress output changed its selected storage device")
            if self._owned is not None:
                current = os.stat(self.path.name, dir_fd=parent, follow_symlinks=False)
                if not stat.S_ISREG(current.st_mode) or current.st_nlink != 1 or _identity(current) != self._owned:
                    raise FileExistsError("progress destination ownership changed")
            descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                0o600, dir_fd=parent)
            created = _identity(os.fstat(descriptor))
            offset = 0
            while offset < len(raw):
                written = os.write(descriptor, raw[offset:])
                if written <= 0:
                    raise OSError("progress write made no progress")
                offset += written
            observed = os.fstat(descriptor)
            selected, descriptor = descriptor, -1
            os.close(selected)
            if self._owned is None:
                rename_noreplace(temporary, self.path.name, source_dir_fd=parent, destination_dir_fd=parent)
            else:
                os.replace(temporary, self.path.name, src_dir_fd=parent, dst_dir_fd=parent)
            installed = True
            self._owned = _identity(observed)
        finally:
            if descriptor >= 0:
                os.close(descriptor)
            if created is not None and not installed:
                try:
                    current = os.stat(temporary, dir_fd=parent, follow_symlinks=False)
                    if (current.st_dev, current.st_ino) == created[:2]:
                        os.unlink(temporary, dir_fd=parent)
                except OSError:
                    pass
            os.close(parent)


def format_progress(record: dict) -> str:
    """Render the same fields used by UI readers; no guessed remaining time."""
    done, total = record["done"], record["total"]
    count = "progress unknown" if done is None else str(done)
    count += "/" + str(total) if total is not None else "/?"
    percent = "" if record["percent"] is None else f" ({record['percent']:.1f}%)"
    workflow = "workflow unknown" if record["workflow_total"] is None else f"workflow {record['workflow_done']}/{record['workflow_total']} {record['workflow_unit']}"
    remaining = "remaining unknown" if done is None or total is None else f"remaining={total - done}"
    heartbeat = " | heartbeat: controller alive; work advancement unknown" if record["heartbeat"] else ""
    detail = "" if record["detail"] is None else " | " + record["detail"]
    task = "" if record["task_id"] is None else " | task=" + record["task_id"]
    return (f"{record['status']} | {record['phase']} | {count}{percent} {record['unit']} | "
            f"{remaining} | {workflow} | elapsed={record['elapsed_seconds']:.1f}s "
            f"phase={record['phase_elapsed_seconds']:.1f}s no-report={record['activity_age_seconds']:.1f}s "
            f"failed={record['failed']}{task}{heartbeat}{detail}")


def _unique_fields(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate progress field")
        result[key] = value
    return result


def read_progress(path: Path) -> dict:
    """Read one bounded operational snapshot; no scientific/provider inspection."""
    selected = Path(path).absolute()
    parent = _parent(selected)
    os.close(parent)
    raw = read_bounded_bytes(selected, maximum_bytes=MAX_PROGRESS_BYTES)
    document = json.loads(raw, object_pairs_hook=_unique_fields)
    if type(document) is not dict or set(document) != _FIELDS or document["schema"] != _SCHEMA:
        raise ValueError("progress snapshot schema is invalid")
    _operation(document["operation"])
    _token(document["phase"])
    _counters(document["done"], document["total"], document["failed"])
    if type(document["status"]) is not str or document["status"] not in _STATUSES:
        raise ValueError("progress status is invalid")
    if document["percent"] != _percent(document["done"], document["total"]):
        raise ValueError("progress status or percent is invalid")
    if document["percent"] is not None and type(document["percent"]) not in (int, float):
        raise ValueError("progress percent must be numeric")
    elapsed = document["elapsed_seconds"]
    if type(elapsed) not in (int, float) or not 0 <= elapsed <= _MAX_COUNTER or not math.isfinite(elapsed):
        raise ValueError("progress elapsed time is invalid")
    _counter(document["pid"], optional=False)
    if document["pid"] == 0:
        raise ValueError("progress PID must be positive")
    _token(document["workflow_unit"])
    _token(document["unit"])
    if document["task_id"] is not None:
        _token(document["task_id"])
    if document["detail"] is not None and (type(document["detail"]) is not str or len(document["detail"]) > 256
            or any(ord(c) < 32 for c in document["detail"])):
        raise ValueError("progress detail is invalid")
    _counter(document["sequence"], optional=False)
    if document["sequence"] == 0 or type(document["heartbeat"]) is not bool:
        raise ValueError("progress sequence/heartbeat is invalid")
    _counters(document["workflow_done"], document["workflow_total"], document["workflow_failed"])
    if (document["workflow_percent"] is not None and type(document["workflow_percent"]) not in (int, float)
            or document["workflow_percent"] != _percent(document["workflow_done"], document["workflow_total"])):
        raise ValueError("workflow percent is invalid")
    for key in ("phase_elapsed_seconds", "activity_age_seconds"):
        if type(document[key]) not in (int, float) or not math.isfinite(document[key]) or not 0 <= document[key] <= _MAX_COUNTER:
            raise ValueError("progress age is invalid")
    steps = document["completed_steps"]
    if type(steps) is not list or len(steps) > MAX_COMPLETED_STEPS:
        raise ValueError("completed step summaries are invalid")
    for key in ("completed_steps_total", "completed_steps_omitted"):
        _counter(document[key], optional=False)
    if document["completed_steps_total"] - len(steps) != document["completed_steps_omitted"]:
        raise ValueError("completed step population is inconsistent")
    for step in steps:
        if type(step) is not dict or set(step) != {"phase", "done", "total", "unit", "elapsed_seconds", "status"}:
            raise ValueError("completed step shape is invalid")
        _token(step["phase"])
        _token(step["unit"])
        _counters(step["done"], step["total"], 0)
        if type(step["status"]) is not str or step["status"] not in _STATUSES - {"RUNNING"} or type(step["elapsed_seconds"]) not in (float, int) or not math.isfinite(step["elapsed_seconds"]) or step["elapsed_seconds"] < 0:
            raise ValueError("completed step state is invalid")
    stamp = document["updated_at_utc"]
    if type(stamp) is not str or len(stamp) > 40:
        raise ValueError("progress timestamp is invalid")
    parsed = datetime.fromisoformat(stamp)
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        raise ValueError("progress timestamp must be UTC")
    return document
