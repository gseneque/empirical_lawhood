# SPDX-License-Identifier: MPL-2.0
"""Launch one durable selected-engine worker without a scientific time limit."""

from hashlib import sha256
from pathlib import Path
import subprocess
import threading

from empirical_lawhood.api.application_contracts import MAX_RESPONSE_BYTES, ApplicationError, load_application_json
from empirical_lawhood.api.results import ErrorCategory
from empirical_lawhood.storage.application_invocations import ApplicationInvocationStore, process_identity, record_bytes, utc_now
from empirical_lawhood.execution.local.bounded_process import BoundedProcessError, BoundedProcessReader
from empirical_lawhood.storage.development_attempts import safe_failure


class InvocationDelivery:
    """One original response pipe. Closing it never kills or repeats the worker."""

    def __init__(self, process, input_bytes):
        self.process = process
        self.reader = BoundedProcessReader(process, input_bytes=input_bytes, timeout_seconds=3600,
            maximum_stdout_bytes=MAX_RESPONSE_BYTES, maximum_stderr_bytes=64*1024)

    def result(self):
        chunks = []
        try:
            while chunk := self.reader.read(64*1024):
                chunks.append(chunk)
            code = self.reader.finish()
            raw = b"".join(chunks)
            value = load_application_json(raw, maximum_bytes=MAX_RESPONSE_BYTES)
            if code != 0 or type(value) is not dict or value.get("schema") != "empirical-lawhood/api/result":
                raise ApplicationError("INVOCATION_RESPONSE_UNAVAILABLE", "The worker returned no compatible result. Inspect its original handle.")
            return raw
        except BoundedProcessError as error:
            raise ApplicationError("INVOCATION_DELIVERY_UNAVAILABLE",
                "Response delivery ended before a complete result. The original worker may still be running. "
                "Inspect its retained handle before selecting recovery.", category=ErrorCategory.EXECUTION) from error
        finally:
            self.reader.close()
            if self.process.poll() is None:
                threading.Thread(target=self.process.wait, daemon=True).start()


def selected_store(context, required_mount):
    if context.invocation_root is None or required_mount is None:
        raise ApplicationError("INVOCATION_STORAGE_REQUIRED", "Select an existing invocation root and operational mount for this operation.",
            category=ErrorCategory.CAPABILITY)
    return ApplicationInvocationStore(context.invocation_root, Path(required_mount))


def dispatch(selected, request, *, required_mount, client="browser"):
    descriptions = [row for row in selected.description["operations"] if row.get("operation_id") == request.operation]
    if (request.context_id != selected.context.context_id or len(descriptions) != 1
            or descriptions[0].get("lifecycle") not in ("DURABLE_READ", "EFFECT")
            or (client == "browser" and not descriptions[0].get("browser_available"))):
        raise ApplicationError("UNAVAILABLE_DURABLE_OPERATION", "The selected engine does not expose this durable operation.", category=ErrorCategory.CAPABILITY)
    store = selected_store(selected.context, required_mount)
    process = delivery = None
    try:
        handle, fresh = store.claim(context_id=selected.context.context_id, context_sha256=selected.context.fingerprint(),
            engine_sha256=selected.identity_sha256, context=selected.context.to_document(), request=request.to_document(), client=client)
    except ValueError as error:
        raise ApplicationError("REQUEST_KEY_CONFLICT", "The request key has incompatible or incomplete retained operands.", category=ErrorCategory.CONFLICT) from error
    except RuntimeError as error:
        raise ApplicationError("INVOCATION_RECONCILIATION_REQUIRED", "Inspect the active or uncertain invocation before dispatching another operation.", category=ErrorCategory.CONFLICT) from error
    if not fresh:
        return store.snapshot(handle), None
    intent = store.intent(handle)
    command = record_bytes({"root": str(store.root), "required_mount": str(store.required_mount),
        "handle": handle, "intent_sha256": sha256(record_bytes(intent)).hexdigest(), "request": request.to_document()})
    from empirical_lawhood.workbench.launcher import engine_environment
    environment = engine_environment()
    try:
        process = subprocess.Popen((str(selected.context.python_executable), "-I", "-B", "-m",
            "empirical_lawhood.workbench.worker"), cwd=selected.context.project_root, env=environment,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0, start_new_session=True)
        delivery = InvocationDelivery(process, command)
        store.publish(handle, "launched", {"handle": handle, "binding_sha256": intent["binding_sha256"],
            "launched_utc": utc_now(), "process": process_identity(process.pid)})
    except Exception as error:
        if delivery is not None:
            delivery.reader.close()
        elif process is not None:
            for stream in (process.stdin, process.stdout, process.stderr):
                stream.close()
        if process is not None:
            threading.Thread(target=process.wait, daemon=True).start()
        store.publish(handle, "launch-failed", {"handle": handle, "binding_sha256": intent["binding_sha256"],
            "failed_utc": utc_now(), "failure": safe_failure(error, stage="worker_launch")})
        raise
    return store.snapshot(handle), delivery


def inspect_invocation(context, handle, *, required_mount):
    store = selected_store(context, required_mount)
    intent = store.intent(handle)
    if (intent["binding"]["context_sha256"] != context.fingerprint()
            or intent["binding"]["context"] != context.to_document()):
        raise ApplicationError("INVOCATION_CONTEXT_MISMATCH", "Select the original invocation context before inspecting this handle.")
    from empirical_lawhood.execution.local.application_progress import invocation_progress
    return {**store.snapshot(handle), "progress": invocation_progress(store, handle, progress_root=context.progress_root)}
