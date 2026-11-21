# SPDX-License-Identifier: MPL-2.0
"""One advisory progress port for CLI, application and storage owners.

Progress never establishes scientific completion or replay authority.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Protocol
from functools import wraps
import time


class ProgressReporter(Protocol):
    def update(
        self, *, phase: str, done: int | None = None, total: int | None = None,
        failed: int = 0, unit: str = "items", detail: str | None = None,
        task_id: str | None = None, started_at: float | None = None,
    ) -> None: ...

    def workflow_update(self, *, done: int, total: int, failed: int = 0, unit: str = "tasks") -> None: ...

    def step_completed(self, *, phase: str, done: int | None, total: int | None,
        unit: str, elapsed_seconds: float, status: str) -> None: ...


_REPORTER: ContextVar[ProgressReporter | None] = ContextVar("operational_progress", default=None)


def active_progress() -> bool:
    """Whether this context has explicitly selected a reporter."""
    return current_progress() is not None


def report_progress(
    *, phase: str, done: int | None = None, total: int | None = None, failed: int = 0,
    unit: str | None = None, detail: str | None = None, task_id: str | None = None,
    started_at: float | None = None,
) -> None:
    """Report advisory counters without allowing telemetry errors to stop work."""
    reporter = current_progress()
    if reporter is not None:
        try:
            options = {}
            if unit is not None:
                options["unit"] = unit
            if detail is not None:
                options["detail"] = detail
            if task_id is not None:
                options["task_id"] = task_id
            step = _STEP.get()
            if started_at is not None:
                options["started_at"] = started_at
            elif step is not None and step.phase == phase:
                options["started_at"] = step.started
            reporter.update(phase=phase, done=done, total=total, failed=failed, **options)
        except Exception:
            pass


@contextmanager
def progress_reporting(reporter: ProgressReporter | None) -> Iterator[None]:
    """Bind one invocation's reporter, restoring the previous context on exit."""
    token = _REPORTER.set(reporter)
    try:
        yield
    finally:
        _REPORTER.reset(token)


def report_workflow_progress(*, done: int, total: int, failed: int = 0, unit: str = "tasks") -> None:
    """Report the declared complete workflow census, independent of inner steps."""
    reporter = current_progress()
    if reporter is not None:
        try:
            reporter.workflow_update(done=done, total=total, failed=failed, unit=unit)
        except Exception:
            pass


class ProgressStep:
    """A caller-owned counter; no inferred denominator or fabricated completion."""

    def __init__(self, phase: str, total: int | None, unit: str, detail: str | None):
        self.phase, self.total, self.unit, self.detail = phase, total, unit, detail
        self.done = 0
        self.started = time.monotonic()

    def advance(self, amount: int = 1) -> None:
        if type(amount) is not int or amount < 0:
            raise ValueError("progress increments must be nonnegative integers")
        self.set(self.done + amount)

    def set(self, done: int, *, total: int | None = None) -> None:
        if type(done) is not int or done < 0:
            raise ValueError("progress must be a nonnegative integer")
        self.done = done
        if total is not None:
            self.total = total
        self.report()

    def report(self) -> None:
        report_progress(phase=self.phase, done=self.done, total=self.total,
                        unit=self.unit, detail=self.detail, started_at=self.started)


_STEP: ContextVar[ProgressStep | None] = ContextVar("operational_progress_step", default=None)


@contextmanager
def progress_step(phase: str, *, total: int | None = None, unit: str = "items",
                  detail: str | None = None) -> Iterator[ProgressStep]:
    """Expose an owned step, restoring its parent's measured counter on exit.

    Call ``advance`` only after actual completed work. Unknown work remains
    indeterminate. A returned scope does not manufacture 100% or a receipt.
    """
    parent = _STEP.get()
    step = ProgressStep(phase, total, unit, detail)
    token = _STEP.set(step)
    step.report()
    status = "RETURNED"
    try:
        yield step
    except BaseException as error:
        status = "INTERRUPTED" if isinstance(error, (KeyboardInterrupt, SystemExit)) else "FAILED"
        raise
    finally:
        reporter = current_progress()
        if reporter is not None:
            try:
                reporter.step_completed(phase=phase, done=step.done, total=step.total, unit=unit,
                    elapsed_seconds=max(0.0, time.monotonic() - step.started), status=status)
            except Exception:
                pass
        _STEP.reset(token)
        if parent is not None:
            parent.report()


def current_progress():
    """Capture only advisory telemetry for an explicitly joined worker thread."""
    reporter = _REPORTER.get()
    return reporter if reporter is not None and getattr(reporter, "active_in_process", True) else None


def run_with_progress(reporter, function, /, *args, **kwargs):
    """Carry telemetry into a selected thread without copying scientific contexts."""
    with progress_reporting(reporter):
        return function(*args, **kwargs)


def progress_operation(phase: str):
    """Name a public lifecycle boundary while preserving its actual return/error."""
    def decorate(function):
        @wraps(function)
        def invoke(*args, **kwargs):
            with progress_step(phase, total=1, unit="operations") as step:
                result = function(*args, **kwargs)
                step.advance()
                return result
        return invoke
    return decorate
