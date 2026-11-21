# SPDX-License-Identifier: MPL-2.0
"""Shared operational attempt composition, independent of either client."""

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import replace
import json
from pathlib import Path

from empirical_lawhood.storage.bounded_io import BoundedFileIOError
from empirical_lawhood.storage.development_attempts import DevelopmentAttempt, MAX_INPUT_COPY_BYTES


_current: ContextVar[DevelopmentAttempt | None] = ContextVar("development_attempt", default=None)
_operational_configuration = ContextVar("invocation_operational_configuration", default=None)


def retain_failure_diagnostic(diagnostic):
    """Attach one shared operational diagnostic to the current retained attempt."""
    attempt = _current.get()
    if attempt is None:
        return diagnostic
    selected = replace(diagnostic, evidence=str(attempt.path / "contract-diagnostic.json"))
    attempt.diagnostic(selected.to_mapping())
    return selected


def retain_output_reservations(record: dict) -> None:
    """Keep the live operational selection and bounded plan arithmetic."""
    attempt = _current.get()
    if attempt is not None:
        attempt.record["output_reservations"] = record

def _disjoint(destination: Path, scientific: Path | None) -> None:
    if scientific is None:
        return
    attempt, product = destination.resolve(), scientific.resolve()
    if attempt.is_relative_to(product) or product.is_relative_to(attempt):
        raise ValueError("operational attempt and scientific output locations must be disjoint")

def attempt_input(path: Path, *, maximum_bytes: int, copy: bool = True, role: str = "config", consumer: str | None = None,
                  expected_sha256: str | None = None) -> Path:
    """Keep one owned small snapshot and pass its exact bytes to the real owner."""
    attempt = _current.get()
    if attempt is None:
        return path
    try:
        attempt.record["native_contact"] = "none"
        attempt.event("input_validation")
        attempt.capture_input(role, path, maximum_bytes=maximum_bytes, copy=False, expected_sha256=expected_sha256)
        attempt.record["last_completed_stage"] = "input_identity_recorded"
        if not copy:
            return path
        expected = None
        if copy and path.suffix.casefold() in {".json", ".yaml", ".yml"}:
            from empirical_lawhood.api.configuration import validate_configuration
            from empirical_lawhood.api.configuration_registry import CONSUMERS

            consumers = [item.consumer for item in CONSUMERS if item.command == attempt.record["operation"]]
            selected = consumer if consumer is not None else (consumers[0] if len(consumers) == 1 else None)
            # Invalid arbitrary payloads are never persisted as input.json.
            # Value-valid pretty JSON still reaches the real exact-byte reader.
            validation = validate_configuration(path, consumer=selected)
            if expected_sha256 is not None and validation["input_sha256"] != expected_sha256:
                raise ValueError("invocation input changed its reviewed exact bytes")
            attempt.record["input_validation"] = validation
            # Larger closed scientific inputs keep their bounded observed
            # identity; operational retention never expands its snapshot ceiling.
            copy = validation["disposition"] == "editable" and validation["input_bytes"] <= MAX_INPUT_COPY_BYTES
            expected = str(validation["input_sha256"])
        elif copy:
            copy = False
        snapshot = attempt.capture_input(role, path, maximum_bytes=maximum_bytes, copy=copy, expected_sha256=expected)
        attempt.record["last_completed_stage"] = "input_snapshot_validated" if copy else "input_identity_recorded"
        return snapshot
    except BoundedFileIOError as error:
        raise ValueError("development input snapshot refused its bounded regular-file contract") from error

def attempt_stage(stage: str, *, native_contact: str = "unknown") -> None:
    from empirical_lawhood.execution.progress import report_progress
    report_progress(phase="operation." + stage)
    attempt = _current.get()
    if attempt is not None:
        attempt.record["native_contact"] = native_contact
        attempt.event(stage)

def retain_development_report(report: object, *, allow_nan: bool = True) -> None:
    attempt = _current.get()
    if attempt is not None:
        attempt.operation_completed()
        attempt.event("result_serialization")
        attempt.report(json.dumps(report, sort_keys=True, indent=2, allow_nan=allow_nan))

def retain_operational_configuration(configuration):
    """Record selected check policy separately from scientific result bytes."""
    token = _operational_configuration.set(configuration)
    attempt = _current.get()
    if attempt is not None:
        attempt.record['operational_configuration'] = configuration.to_document()
    return lambda: _operational_configuration.reset(token)


def start_attempt(destination: Path, operation: str, *, native: bool, scientific: Path | None = None):
    _disjoint(destination, scientific)
    return DevelopmentAttempt(destination, operation, native=native)


@contextmanager
def retained_attempt(attempt):
    token = _current.set(attempt)
    try:
        yield attempt
    finally:
        _current.reset(token)
