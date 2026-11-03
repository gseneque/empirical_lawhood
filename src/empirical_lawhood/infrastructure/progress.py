# SPDX-License-Identifier: MPL-2.0
"""Bounded mutable operational snapshots; these are not scientific evidence."""

from __future__ import annotations

from datetime import UTC, datetime
import json
import math
import os
from pathlib import Path
import re
import stat
import sys
from threading import Lock
import time
from uuid import uuid4

from empirical_lawhood.infrastructure.atomic_files import rename_noreplace
from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.runtime.progress import progress_reporting


MAX_PROGRESS_BYTES = 16 * 1024
_SCHEMA = "empirical-lawhood/operational-progress.v1"
_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}\Z")
_LABEL = re.compile(r"[A-Za-z0-9][A-Za-z0-9 ._:/-]{0,127}\Z")
_MAX_COUNTER = 2**63 - 1
_STATUSES = frozenset(("RUNNING", "RETURNED", "FAILED", "INTERRUPTED"))
_FIELDS = frozenset(("schema", "operation", "phase", "done", "total", "failed", "percent",
    "updated_at_utc", "elapsed_seconds", "pid", "status"))


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


class JsonProgressReporter:
    """Claim a new status path, then atomically replace only our own snapshots.

    Publication is advisory: it has no fsync or scientific durability claim.
    I/O failures disable this sink and preserve the previously installed file.
    The CLI owns separation from scientific input and output paths.
    """

    def __init__(self, path: Path, operation: str, minimum_interval: float = 1.0) -> None:
        _operation(operation)
        if isinstance(minimum_interval, bool) or not isinstance(minimum_interval, (int, float)):
            raise ValueError("progress interval must be finite and nonnegative")
        if not math.isfinite(minimum_interval) or minimum_interval < 0:
            raise ValueError("progress interval must be finite and nonnegative")
        selected = Path(path)
        if ".." in selected.parts:
            raise ValueError("progress destination cannot traverse parents")
        self.path = selected.absolute()
        self.operation = operation
        self.minimum_interval = minimum_interval
        self._started = time.monotonic()
        self._last_write = self._started
        self._current = ("starting", None, None, 0)
        self._owned: tuple[int, int, int, int] | None = None
        self._error: str | None = None
        self._finished = False
        self._scope = None
        self._lock = Lock()
        self._publish("RUNNING", self._started, initial=True)

    def __enter__(self) -> JsonProgressReporter:
        if self._scope is not None:
            raise RuntimeError("progress reporter is already active")
        self._scope = progress_reporting(self)
        self._scope.__enter__()
        return self

    def __exit__(self, kind, value, traceback) -> bool:
        try:
            status = "RETURNED" if kind is None else "FAILED" if issubclass(kind, Exception) else "INTERRUPTED"
            self.finish(status)
        finally:
            scope, self._scope = self._scope, None
            if scope is not None:
                scope.__exit__(kind, value, traceback)
        return False

    @property
    def error(self) -> str | None:
        """The failure type only; no paths, arbitrary messages or science data."""
        return self._error

    def update(
        self, *, phase: str, done: int | None = None, total: int | None = None,
        failed: int = 0,
    ) -> None:
        with self._lock:
            if self._error is not None or self._finished:
                return
            _token(phase)
            _counters(done, total, failed)
            previous_phase = self._current[0]
            self._current = phase, done, total, failed
            now = time.monotonic()
            if phase != previous_phase or now - self._last_write >= self.minimum_interval:
                self._publish("RUNNING", now)

    def finish(self, status: str = "RETURNED") -> None:
        """Force one final snapshot, preserving partial or unknown counters."""
        with self._lock:
            if self._error is not None or self._finished:
                return
            if status not in _STATUSES - {"RUNNING"}:
                raise ValueError("progress finish status is invalid")
            self._finished = True
            self._publish(status, time.monotonic())

    def _publish(self, status: str, now: float, *, initial: bool = False) -> None:
        try:
            phase, done, total, failed = self._current
            document = {"schema": _SCHEMA, "operation": self.operation, "phase": phase,
                "done": done, "total": total, "failed": failed, "percent": _percent(done, total),
                "updated_at_utc": datetime.now(UTC).isoformat(),
                "elapsed_seconds": max(0.0, now - self._started), "pid": os.getpid(), "status": status}
            raw = (json.dumps(document, allow_nan=False, separators=(",", ":")) + "\n").encode()
            if len(raw) > MAX_PROGRESS_BYTES:
                raise ValueError("progress snapshot exceeds its bound")
            self._install(raw)
            self._last_write = now
        except Exception as error:
            if initial:
                raise
            self._error = type(error).__name__
            try:
                sys.stderr.write("Progress reporting disabled (" + self._error + ").\n")
            except Exception:
                pass

    def _install(self, raw: bytes) -> None:
        parent = _parent(self.path)
        temporary = ".el-progress." + uuid4().hex + ".tmp"
        descriptor = -1
        created: tuple[int, int, int, int] | None = None
        installed = False
        try:
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
    stamp = document["updated_at_utc"]
    if type(stamp) is not str or len(stamp) > 40:
        raise ValueError("progress timestamp is invalid")
    parsed = datetime.fromisoformat(stamp)
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        raise ValueError("progress timestamp must be UTC")
    return document
