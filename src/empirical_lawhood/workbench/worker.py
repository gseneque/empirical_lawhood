# SPDX-License-Identifier: MPL-2.0
"""Detached selected-engine invocation; the original response has one live reader."""

from hashlib import sha256
import os
from pathlib import Path
import sys
import time

from empirical_lawhood.api.application_contracts import ApplicationContext, ApplicationRequest, ApplicationError, exact_mapping, load_application_json, response_bytes
from empirical_lawhood.storage.application_invocations import ApplicationInvocationStore, MAX_INVOCATION_RECORD_BYTES, process_identity, record_bytes, request_binding, utc_now
from empirical_lawhood.storage.development_attempts import safe_failure

from empirical_lawhood.workbench.engine import describe_engine


def execute(document):
    exact_mapping(document, ("root", "required_mount", "handle", "intent_sha256", "request"),
                  required=("root", "required_mount", "handle", "intent_sha256", "request"))
    store = ApplicationInvocationStore(Path(document["root"]), Path(document["required_mount"]))
    handle = document["handle"]
    intent = store.intent(handle)
    if sha256(record_bytes(intent)).hexdigest() != document["intent_sha256"]:
        raise ApplicationError("INVOCATION_INTENT_CHANGED", "The original dispatch intent changed before entry.")
    binding = intent["binding"]
    context = ApplicationContext.from_document(binding["context"])
    request = ApplicationRequest.from_document(document["request"])
    if (sha256(record_bytes(request.to_document())).hexdigest() != binding["request_sha256"]
            or request_binding(request.to_document()) != binding["request"]):
        raise ApplicationError("INVOCATION_REQUEST_CHANGED", "The worker input differs from its original request binding.")
    from empirical_lawhood.api.application_operations import application_operation
    operation = application_operation(request.operation)
    if (binding["client"] not in ("browser", "cli") or operation.lifecycle not in ("DURABLE_READ", "EFFECT")
            or binding["client"] == "browser" and not operation.browser_available):
        raise ApplicationError("UNAVAILABLE_DURABLE_OPERATION", "This operation is unavailable to the selected invocation client.")
    if (context.invocation_root != store.root or context.fingerprint() != binding["context_sha256"]
            or context.context_id != request.context_id or context.python_executable != Path(sys.executable).absolute()
            or binding["required_mount"] != str(store.required_mount)
            or describe_engine()["identity_sha256"] != binding["engine_sha256"]):
        raise ApplicationError("INVOCATION_CONTEXT_CHANGED", "The selected context or engine changed before invocation entry.")
    if context.project_root is not None:
        from empirical_lawhood.storage.source_origin import require_selected_implementation
        require_selected_implementation(context.project_root)
    store.publish(handle, "entered", {"handle": handle, "binding_sha256": intent["binding_sha256"],
        "entered_utc": utc_now(), "process": process_identity()})
    # Exclusive entry publication precedes handler entry. A second worker or
    # lost acknowledgement cannot repeat the operation under this handle.
    started = time.monotonic()
    from empirical_lawhood.api.application_invocation import invocation_failure, run_application_invocation
    failure = None
    try:
        result, body = run_application_invocation(context, request, directory=store.path(handle), handle=handle, store=store)
    except BaseException as error:
        failure = safe_failure(error, stage="application_invocation")
        result = invocation_failure(request.operation, error)
        body = response_bytes(result)
    store.publish(handle, "returned", {"handle": handle, "binding_sha256": intent["binding_sha256"],
        "returned_utc": utc_now(), "status": result.status.value, "reason_codes": result.reason_codes,
        "response_bytes": len(body), "response_sha256": sha256(body).hexdigest(),
        "elapsed_seconds": str(time.monotonic()-started), "failure": failure,
        "original_locators": {key: value for key, value in request.parameters if key in ("directory", "output_dir", "output_file")},
        "returned_bindings": {key: result.payload[key] for key in (
            "authoring_dir", "output_file", "output_sha256", "packet_sha256", "draft_sha256", "run_id")
            if isinstance(result.payload, dict) and type(result.payload.get(key)) is str},
        "response_body_retained": False})
    return store, handle, body


def main():
    document = load_application_json(sys.stdin.buffer.read(MAX_INVOCATION_RECORD_BYTES+1), maximum_bytes=MAX_INVOCATION_RECORD_BYTES)
    try:
        store, handle, body = execute(document)
    except BaseException as error:
        from empirical_lawhood.api.application_invocation import invocation_failure
        body = response_bytes(invocation_failure("application.invocation", error))
        # Pre-entry failures have no operation effect. Preserve the original
        # intent and report uncertainty if its storage itself is unavailable.
        try:
            store = ApplicationInvocationStore(Path(document["root"]), Path(document["required_mount"]))
            handle = document["handle"]
            intent = store.intent(handle)
            store.publish(handle, "launch-failed", {"handle": handle, "binding_sha256": intent["binding_sha256"],
                "failed_utc": utc_now(), "failure": safe_failure(error, stage="invocation_entry")})
        except Exception:
            pass
    delivered = False
    try:
        sys.stdout.buffer.write(body)
        sys.stdout.buffer.flush()
        delivered = True
    except (BrokenPipeError, OSError):
        # Broker/browser loss affects response delivery, not the completed work.
        try:
            with open(os.devnull, "wb") as null:
                os.dup2(null.fileno(), sys.stdout.fileno())
        except OSError:
            pass
    try:
        store.publish(handle, "delivery", {"handle": handle, "observed_utc": utc_now(), "pipe_write_completed": delivered,
            "browser_receipt": "UNKNOWN", "response_body_retained": False})
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    main()
