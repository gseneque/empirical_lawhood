# SPDX-License-Identifier: MPL-2.0
"""Opt-in operational telemetry, separate from scientific records and effects."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Protocol


class ProgressReporter(Protocol):
    def update(
        self, *, phase: str, done: int | None = None, total: int | None = None,
        failed: int = 0,
    ) -> None: ...


_REPORTER: ContextVar[ProgressReporter | None] = ContextVar("operational_progress", default=None)


def active_progress() -> bool:
    """Whether this context has explicitly selected a reporter."""
    return _REPORTER.get() is not None


def report_progress(
    *, phase: str, done: int | None = None, total: int | None = None, failed: int = 0,
) -> None:
    """Report advisory counters without allowing telemetry errors to stop work."""
    reporter = _REPORTER.get()
    if reporter is not None:
        try:
            reporter.update(phase=phase, done=done, total=total, failed=failed)
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
