# SPDX-License-Identifier: MPL-2.0
"""Compose one application attempt and advisory progress below either client."""

from contextlib import nullcontext
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
import time

from empirical_lawhood.api.application_contracts import ApplicationError, error_result, response_bytes


def run_application_invocation(context, request, *, directory, handle, store=None):
    from empirical_lawhood.api.application import execute_application
    from empirical_lawhood.api.invocation_retention import retained_attempt, start_attempt
    from empirical_lawhood.storage.progress import OperationalProgressReporter
    values = dict(request.parameters)
    knowledge_locators = {}
    if request.operation in ("knowledge.resolve", "knowledge.review", "knowledge.apply"):
        from empirical_lawhood.api.application_knowledge import _selection
        from empirical_lawhood.api.application_contracts import exact_mapping
        selection = _selection(values)
        exact_mapping(selection, selection if type(selection) is dict else ())
        knowledge_locators = {"knowledge." + key: selection[key] for key in (
            "directory", "transfer_directory", "output_directory", "source_profile", "source_root_contract") if key in selection}
    if request.operation in ("inquiry.review-author", "inquiry.author"):
        from empirical_lawhood.api.application_inquiry import input_bindings
        knowledge_locators.update({"inquiry.input." + name: str(path) for name, path in input_bindings(values)})
    if request.operation in ("programme.read", "programme.review", "programme.apply") and context.programme_request_path is not None:
        knowledge_locators["programme.context_request"] = str(context.programme_request_path)
    attempt_path = directory / "attempt"
    progress_path = None if context.progress_root is None else context.progress_root / (handle + ".json")
    destinations = (attempt_path,) if progress_path is None else (attempt_path, progress_path)
    for value in (*values.values(), *knowledge_locators.values()):
        if type(value) is str and value.startswith("/"):
            other = Path(value).resolve()
            for destination in destinations:
                location = destination.resolve()
                if location == other or location.is_relative_to(other) or other.is_relative_to(location):
                    raise ApplicationError("INVOCATION_OUTPUT_OVERLAP", "Invocation, progress and scientific selections must be disjoint.")
    if progress_path is not None and (progress_path.is_relative_to(directory) or directory.is_relative_to(context.progress_root)):
        raise ApplicationError("INVOCATION_OUTPUT_OVERLAP", "Progress and invocation packages must be disjoint.")
    started = time.monotonic()
    attempt = start_attempt(attempt_path, request.operation, native=request.operation in ("recursive.run", "recursive.recover", "programme.apply"))
    try:
        attempt.record.update(application_handle=handle, application_context_sha256=context.fingerprint(),
            declared_input_locators=[{"role": key, "locator": value} for key, value in values.items()
                if key in ("directory", "input", "origins", "initial_draft", "supplier_directory", "contribution_directory", "output_dir",
                    "sources", "source_snapshot", "protocol", "programme_request") and type(value) is str]
                + [{"role": key, "locator": value} for key, value in knowledge_locators.items() if type(value) is str])
        attempt.event("application_preflight")
        progress = nullcontext()
        if progress_path is not None:
            if store is None:
                progress = OperationalProgressReporter(progress_path, request.operation)
            else:
                from empirical_lawhood.execution.local.application_progress import ApplicationProgressReporter
                progress = ApplicationProgressReporter(progress_path, request.operation, store=store, handle=handle)
        with retained_attempt(attempt), progress:
            attempt.record["handler_entered"] = True
            result = execute_application(context, request)
        if result.succeeded:
            attempt.operation_completed()
            if isinstance(result.payload, dict) and "native_contact" in result.payload:
                attempt.record["native_contact"] = result.payload["native_contact"]
        body = response_bytes(result)
        attempt.record["application_result"] = {"status": result.status.value,
            "reason_codes": result.reason_codes, "response_bytes": len(body), "response_sha256": sha256(body).hexdigest(),
            "elapsed_seconds": str(Decimal(str(time.monotonic()-started))), "response_body_retained": False}
        attempt.finish(0 if result.succeeded else 1, None if result.succeeded else RuntimeError("application owner refused"))
        return result, body
    except BaseException as error:
        attempt.finish(130 if isinstance(error, KeyboardInterrupt) else 1, error)
        raise
    finally:
        attempt.close()


def invocation_failure(operation, error):
    if isinstance(error, KeyboardInterrupt):
        return error_result(operation, ApplicationError("INVOCATION_INTERRUPTED", "The invocation was interrupted. Inspect original receipts before recovery."))
    return error_result(operation, error)
