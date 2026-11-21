# SPDX-License-Identifier: MPL-2.0
"""Bounded fixed-argument transport to an explicitly selected engine installation."""

from dataclasses import dataclass
import json
import os

from empirical_lawhood.api.application_contracts import APPLICATION_VERSION, PROJECTION_VERSION, MAX_REQUEST_BYTES, MAX_RESPONSE_BYTES, ApplicationContext, ApplicationError, ApplicationRequest, load_application_json
from empirical_lawhood.api.results import ErrorCategory
from empirical_lawhood.execution.local.bounded_process import run_bounded_command, BoundedProcessError

from empirical_lawhood.workbench.engine import ENGINE_SCHEMA, ENGINE_VERSION


@dataclass(frozen=True, slots=True)
class SelectedEngine:
    context: ApplicationContext
    identity_sha256: str
    description: dict


def engine_environment():
    from empirical_lawhood.execution.local.worker_bootstrap import NUMERICAL_THREAD_ENV_VARS
    environment = {key: value for key, value in os.environ.items() if key not in ("PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP")}
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment.update(dict.fromkeys((*NUMERICAL_THREAD_ENV_VARS, "NUMBA_NUM_THREADS", "BLIS_NUM_THREADS"), "1"))
    return environment


def _command(context, argument, input_bytes=b""):
    environment = engine_environment()
    try:
        result = run_bounded_command((str(context.python_executable), "-I", "-B", "-m",
            "empirical_lawhood.workbench.engine", argument), cwd=context.project_root,
            environment=environment, input_bytes=input_bytes, timeout_seconds=180,
            maximum_input_bytes=MAX_REQUEST_BYTES, maximum_stdout_bytes=MAX_RESPONSE_BYTES,
            maximum_stderr_bytes=64*1024)
    except (OSError, BoundedProcessError) as error:
        raise ApplicationError("ENGINE_TRANSPORT_UNAVAILABLE", "The selected engine could not complete this bounded read.",
            category=ErrorCategory.CAPABILITY) from error
    if result.returncode != 0:
        raise ApplicationError("ENGINE_ENTRY_UNAVAILABLE", "The selected installation has no compatible application entry point.",
            category=ErrorCategory.CAPABILITY)
    try:
        value = load_application_json(result.stdout, maximum_bytes=MAX_RESPONSE_BYTES)
        if (type(value) is not dict or value.get("schema") != "empirical-lawhood/api/result"
                or value.get("version") != "1.0.0" or value.get("status") not in (
                    "SUCCEEDED", "INVALID", "NOT_FOUND", "BLOCKED", "CONFLICT", "FAILED")):
            raise ValueError("result envelope")
    except (ValueError, TypeError) as error:
        raise ApplicationError("ENGINE_RESPONSE_INVALID", "The selected engine returned an incompatible bounded response.",
            category=ErrorCategory.CAPABILITY) from error
    return value, result.stdout


def negotiate_engine(context: ApplicationContext) -> SelectedEngine:
    if type(context) is not ApplicationContext:
        raise TypeError("Selected engine requires its exact context")
    context.__post_init__()
    envelope, _raw = _command(context, "--describe")
    value = envelope.get("payload")
    if (envelope["status"] != "SUCCEEDED" or type(value) is not dict
            or value.get("schema") != ENGINE_SCHEMA or value.get("version") != ENGINE_VERSION
            or value.get("application_version") != APPLICATION_VERSION
            or value.get("projection_version") != PROJECTION_VERSION
            or type(value.get("operations")) is not list or type(value.get("identity_sha256")) is not str):
        raise ApplicationError("ENGINE_CONTRACT_UNSUPPORTED", "This engine cannot negotiate the selected application contract.",
            category=ErrorCategory.CAPABILITY)
    return SelectedEngine(context, value["identity_sha256"], value)


def invoke_engine(selected: SelectedEngine, request: ApplicationRequest, *, client="browser"):
    if type(selected) is not SelectedEngine or type(request) is not ApplicationRequest:
        raise TypeError("Selected engine and typed request are required")
    if request.context_id != selected.context.context_id:
        raise ApplicationError("CONTEXT_MISMATCH", "The request selects another engine context.")
    descriptions = [row for row in selected.description["operations"] if row.get("operation_id") == request.operation]
    if len(descriptions) == 1 and descriptions[0].get("lifecycle") in ("DURABLE_READ", "EFFECT"):
        raise ApplicationError("DURABLE_INVOCATION_REQUIRED", "Use a retained invocation for this selected operation.")
    if len(descriptions) != 1 or (client == "browser" and (
            not descriptions[0].get("browser_available")
            or descriptions[0].get("lifecycle") not in ("STATIC", "READ", "BOUNDED_SCIENTIFIC_READ"))):
        raise ApplicationError("UNAVAILABLE_BROWSER_OPERATION", "This engine has no enabled handler for the selected operation.",
            category=ErrorCategory.CAPABILITY)
    payload = {"schema": ENGINE_SCHEMA, "version": ENGINE_VERSION,
        "expected_engine": selected.identity_sha256, "context": selected.context.to_document(),
        "request": request.to_document(), "client": client}
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    result, body = _command(selected.context, "--invoke", raw)
    if result.get("operation") not in (request.operation, "application.engine"):
        raise ApplicationError("ENGINE_OPERATION_MISMATCH", "The engine returned another operation.", category=ErrorCategory.IDENTITY)
    return result, body
