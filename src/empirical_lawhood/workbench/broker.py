# SPDX-License-Identifier: MPL-2.0
"""One-operator loopback service. Scientific work stays in selected engines."""

import argparse
from datetime import datetime, timezone
from hashlib import sha256
from hmac import compare_digest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
import json
import os
from pathlib import Path
import secrets
import threading
import time

from empirical_lawhood.api.application_contracts import APPLICATION_VERSION, MAX_REQUEST_BYTES, ApplicationContext, ApplicationError, ApplicationRequest, absolute_path, application_result, error_result, exact_mapping, load_application_json, response_bytes
from empirical_lawhood.api.results import ErrorCategory
from empirical_lawhood.storage.application_invocations import request_binding

from empirical_lawhood.workbench.launcher import invoke_engine, negotiate_engine


_ASSETS = {"/": ("index.html", "text/html; charset=utf-8"),
    "/tools.html": ("tools.html", "text/html; charset=utf-8"),
    "/explorer.js": ("explorer.js", "text/javascript; charset=utf-8"),
    "/explorer-core.js": ("explorer-core.js", "text/javascript; charset=utf-8"),
    "/explorer-transport.js": ("explorer-transport.js", "text/javascript; charset=utf-8"),
    "/explorer-geometry.js": ("explorer-geometry.js", "text/javascript; charset=utf-8"),
    "/explorer-diagrams.js": ("explorer-diagrams.js", "text/javascript; charset=utf-8"),
    "/explorer-details.js": ("explorer-details.js", "text/javascript; charset=utf-8"),
    "/explorer-collection.js": ("explorer-collection.js", "text/javascript; charset=utf-8"),
    "/explorer-activity.js": ("explorer-activity.js", "text/javascript; charset=utf-8"),
    "/explorer.css": ("explorer.css", "text/css; charset=utf-8"),
    "/el-equal-circles.svg": ("el-equal-circles.svg", "image/svg+xml"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"), "/style.css": ("style.css", "text/css; charset=utf-8"),
    "/invocation-progress.js": ("invocation-progress.js", "text/javascript; charset=utf-8"),
    "/el-logo.svg": ("el-logo.svg", "image/svg+xml"), "/InterVariable.woff2": ("InterVariable.woff2", "font/woff2")}
_CSP = "default-src 'none'; script-src 'self'; style-src 'self'; font-src 'self'; connect-src 'self'; img-src 'self' data:; base-uri 'none'; form-action 'none'; frame-ancestors 'none'"


def _json_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()+b"\n"


def load_contexts(path):
    with path.open("rb") as source:
        document = load_application_json(source.read(MAX_REQUEST_BYTES+1))
    exact_mapping(document, ("schema", "version", "contexts"), required=("schema", "version", "contexts"))
    if document["schema"] != "empirical-lawhood/application/contexts" or document["version"] != APPLICATION_VERSION:
        raise ApplicationError("UNSUPPORTED_CONTEXTS", "Select a compatible workbench context document.")
    rows = document["contexts"]
    if type(rows) is not list or not 1 <= len(rows) <= 16:
        raise ApplicationError("CONTEXT_LIMIT", "Select between one and sixteen explicit contexts.")
    result = tuple(ApplicationContext.from_document(row) for row in rows)
    if len({row.context_id for row in result}) != len(result):
        raise ApplicationError("DUPLICATE_CONTEXT", "Context IDs must not repeat.")
    return result


class Broker:
    """Session-scoped routing; no cached scientific reports or access verdicts."""

    def __init__(self, contexts, output_directory, *, required_mount=None):
        self.output_directory = absolute_path(output_directory, "output_directory")
        if any(path.is_symlink() for path in (self.output_directory, *self.output_directory.parents)):
            raise ApplicationError("INVALID_OUTPUT", "Invocation output requires an actual directory without symbolic links.")
        self.output_directory.mkdir(mode=0o700, parents=True, exist_ok=False)
        if self.output_directory.is_symlink():
            raise ApplicationError("INVALID_OUTPUT", "Select a new invocation directory.")
        self.contexts = {row.context_id: row for row in contexts}
        if not self.contexts or len(self.contexts) != len(contexts):
            raise ApplicationError("INVALID_CONTEXTS", "Select a unique context census.")
        self.locks = {name: threading.Lock() for name in self.contexts}
        self.required_mount = required_mount
        self.session = secrets.token_urlsafe(32)
        self.engines, self.errors = {}, {}
        for name, context in self.contexts.items():
            try:
                self.engines[name] = negotiate_engine(context)
            except Exception as error:
                self.errors[name] = error_result("application.negotiate", error).to_mapping()
        (self.output_directory/"session.json").write_bytes(_json_bytes({
            "schema": "empirical-lawhood/application/broker-session", "version": APPLICATION_VERSION,
            "started_utc": datetime.now(timezone.utc).isoformat(),
            "contexts": [context.to_document() for context in contexts],
            "engines": {name: row.description for name, row in self.engines.items()}, "errors": self.errors,
            "scientific_responses_retained": False, "session_secret_retained": False}))

    def configuration(self):
        return {"application_version": APPLICATION_VERSION,
            "contexts": [{"selection": row.to_document(),
                "engine": None if name not in self.engines else self.engines[name].description,
                "error": self.errors.get(name)} for name, row in self.contexts.items()],
            "effectful_controls": "SELECTED_BOUNDED_RC_LIFECYCLE_WITH_DURABLE_INVOCATIONS"}

    def execute(self, document):
        request = ApplicationRequest.from_document(document)
        if request.context_id not in self.contexts:
            raise ApplicationError("UNKNOWN_CONTEXT", "Select a context from this application session.")
        selected = self.engines.get(request.context_id)
        if selected is None:
            raise ApplicationError("ENGINE_UNAVAILABLE", "The selected context has no compatible engine.", category=ErrorCategory.CAPABILITY)
        lock = self.locks[request.context_id]
        if not lock.acquire(blocking=False):
            raise ApplicationError("CONTEXT_BUSY", "The selected context already has an active read.", category=ErrorCategory.CONFLICT)
        try:
            key = sha256((request.context_id+":"+request.request_id).encode()).hexdigest()
            path = self.output_directory/(key+".json")
            record = {"schema": "empirical-lawhood/application/read-invocation", "version": APPLICATION_VERSION,
                "request": request_binding(request.to_document()), "context_sha256": selected.context.fingerprint(),
                "engine_sha256": selected.identity_sha256, "state": "ENTERED", "effect_scope": "READ_ONLY",
                "started_utc": datetime.now(timezone.utc).isoformat()}
            try:
                with path.open("xb") as output:
                    output.write(_json_bytes(record)); output.flush(); os.fsync(output.fileno())
            except FileExistsError as error:
                raise ApplicationError("REQUEST_ALREADY_OBSERVED", "This request ID already has a retained invocation. Select a new read request.",
                    category=ErrorCategory.CONFLICT) from error
            started = time.monotonic()
            try:
                envelope, body = invoke_engine(selected, request)
            except Exception as error:
                body = response_bytes(error_result(request.operation, error))
                envelope = load_application_json(body)
            record.update(state="RETURNED", status=envelope["status"], reason_codes=envelope.get("reason_codes", []),
                elapsed_seconds={"decimal": str(time.monotonic()-started)},
                response_bytes=len(body), response_sha256=sha256(body).hexdigest(),
                completed_utc=datetime.now(timezone.utc).isoformat())
            # Publication is separate from engine effects. An interrupted record
            # remains ENTERED; reconnect never silently repeats it.
            final = path.with_suffix(".return.json")
            with final.open("xb") as output:
                output.write(_json_bytes(record)); output.flush(); os.fsync(output.fileno())
            return body
        finally:
            lock.release()

    def invoke(self, document, notify):
        from empirical_lawhood.workbench.invocations import dispatch, inspect_invocation, selected_store
        request = ApplicationRequest.from_document(document)
        selected = self.engines.get(request.context_id)
        if selected is None:
            raise ApplicationError("ENGINE_UNAVAILABLE", "The selected context has no compatible engine.", category=ErrorCategory.CAPABILITY)
        lock = self.locks[request.context_id]
        if not lock.acquire(blocking=False):
            handle = sha256((request.context_id+":"+request.request_id).encode()).hexdigest()
            store = selected_store(selected.context, self.required_mount)
            try:
                intent = store.intent(handle)
            except (FileNotFoundError, ValueError) as error:
                raise ApplicationError("CONTEXT_BUSY", "The selected context has an active invocation.", category=ErrorCategory.CONFLICT) from error
            if intent["binding"]["request"] != request_binding(request.to_document()):
                raise ApplicationError("REQUEST_KEY_CONFLICT", "The request key selects different operands.", category=ErrorCategory.CONFLICT)
            snapshot = inspect_invocation(selected.context, handle, required_mount=self.required_mount)
            notify("invocation", snapshot)
            return None
        try:
            snapshot, delivery = dispatch(selected, request, required_mount=self.required_mount)
            notify("invocation", snapshot)
            return None if delivery is None else delivery.result()
        finally:
            lock.release()

    def invocation_state(self, document):
        from empirical_lawhood.workbench.invocations import inspect_invocation
        exact_mapping(document, ("context_id", "handle"), required=("context_id", "handle"))
        context = self.contexts.get(document["context_id"])
        if context is None:
            raise ApplicationError("UNKNOWN_CONTEXT", "Select an original invocation context.")
        return response_bytes(application_result("application.invocation-state", inspect_invocation(context,
            document["handle"], required_mount=self.required_mount)))


class LocalServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False

    def __init__(self, address, broker):
        if address[0] != "127.0.0.1":
            raise ValueError("The workbench binds only explicit IPv4 loopback")
        self.broker = broker
        self.active_requests = threading.BoundedSemaphore(8)
        super().__init__(address, Handler)
        self.expected_host = f"127.0.0.1:{self.server_address[1]}"
        self.origin = "http://"+self.expected_host


class Handler(BaseHTTPRequestHandler):
    server_version = "ELWorkbench"
    sys_version = ""

    def setup(self):
        super().setup()
        self.connection.settimeout(10)

    def log_message(self, _format, *args):
        pass  # Do not write request paths, source values or session headers.

    def _start_response(self, status, media, length=None):
        self.send_response(status)
        self.send_header("Content-Type", media)
        if length is not None:
            self.send_header("Content-Length", str(length))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", _CSP)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Connection", "close")
        self.end_headers()
        self.close_connection = True

    def _send(self, status, body, media="application/json; charset=utf-8"):
        self._start_response(status, media, len(body))
        self.wfile.write(body)

    def _invoke_stream(self, document):
        self._start_response(200, "application/x-ndjson; charset=utf-8")
        connected = True
        def notify(event, payload):
            nonlocal connected
            if connected:
                try:
                    self.wfile.write(_json_bytes({"event": event, "payload": payload}))
                    self.wfile.flush()
                except OSError:
                    connected = False
        try:
            body = self.server.broker.invoke(document, notify)
            if body is not None:
                notify("result", load_application_json(body, maximum_bytes=8*1024**2))
            else:
                notify("existing", {"message": "The original handle is retained. Inspect its state; no dispatch was repeated."})
        except Exception as error:
            notify("result", error_result("application.invocation", error).to_mapping())

    def _error(self, code, message, status=400):
        self._send(status, response_bytes(error_result("application.transport", ApplicationError(code, message))))

    def _headers(self, *, protected=False, post=False):
        if (len(self.headers.get_all("Host", [])) != 1 or self.headers.get("Host") != self.server.expected_host
                or sum(len(k)+len(v) for k, v in self.headers.items()) > 16384):
            self._error("INVALID_LOCAL_HOST", "Select the exact local application address.", 403); return False
        origins = self.headers.get_all("Origin", [])
        if len(origins) > 1 or (origins and origins[0] != self.server.origin) or (post and not origins):
            self._error("ORIGIN_REFUSED", "This request is outside the current local application origin.", 403); return False
        if self.headers.get("Sec-Fetch-Site") not in (None, "same-origin", "none"):
            self._error("ORIGIN_REFUSED", "This request is outside the current local application origin.", 403); return False
        if protected:
            tokens = self.headers.get_all("X-EL-Session", [])
            if len(tokens) != 1 or not compare_digest(tokens[0], self.server.broker.session):
                self._error("SESSION_REFUSED", "Open the current local application session.", 403); return False
        return True

    def do_GET(self):
        if not self._headers(protected=self.path.startswith("/api/")):
            return
        if self.path in _ASSETS:
            name, media = _ASSETS[self.path]
            self._send(200, files("empirical_lawhood.workbench.assets").joinpath(name).read_bytes(), media)
        elif self.path == "/api/context":
            self._send(200, _json_bytes(self.server.broker.configuration()))
        else:
            self._error("UNKNOWN_ROUTE", "This local application route is unavailable.", 404)

    def do_POST(self):
        if not self._headers(protected=True, post=True):
            return
        if self.path not in ("/api/execute", "/api/invoke", "/api/invocation-state"):
            self._error("UNKNOWN_ROUTE", "This local application route is unavailable.", 404); return
        if (self.headers.get_all("Content-Type", []) != ["application/json"]
                or self.headers.get("Transfer-Encoding") is not None or self.headers.get("Content-Encoding") is not None):
            self._error("UNSUPPORTED_CONTENT", "Select an unencoded application/json request.", 415); return
        lengths = self.headers.get_all("Content-Length", [])
        if len(lengths) != 1 or not lengths[0].isascii() or not lengths[0].isdigit() or len(lengths[0]) > 7:
            self._error("INVALID_CONTENT_LENGTH", "Select one bounded request length.", 400); return
        size = int(lengths[0])
        if not 0 < size <= MAX_REQUEST_BYTES:
            self._error("PAYLOAD_LIMIT", "The request exceeds its application byte limit.", 413); return
        if not self.server.active_requests.acquire(blocking=False):
            self._error("BROKER_BUSY", "The local application is serving its bounded request population.", 429); return
        try:
            raw = self.rfile.read(size)
            if len(raw) != size:
                raise ApplicationError("TRUNCATED_REQUEST", "The request ended before its selected byte length.")
            document = load_application_json(raw)
            if self.path == "/api/invoke":
                self._invoke_stream(document)
                return
            body = (self.server.broker.invocation_state(document) if self.path == "/api/invocation-state"
                    else self.server.broker.execute(document))
            self._send(200, body)
        except Exception as error:
            status = 409 if isinstance(error, ApplicationError) and error.category is ErrorCategory.CONFLICT else 400
            self._send(status, response_bytes(error_result("application.transport", error)))
        finally:
            self.server.active_requests.release()

    def _unsupported(self):
        self._error("UNSUPPORTED_METHOD", "This local method is unavailable.", 405)

    do_OPTIONS = do_PUT = do_PATCH = do_DELETE = do_HEAD = do_TRACE = do_CONNECT = _unsupported


def main(argv=None):
    parser = argparse.ArgumentParser(description="Open the local retained research workbench.")
    parser.add_argument("--contexts", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--required-mount", type=Path, required=True)
    parser.add_argument("--port", type=int, default=0)
    args = parser.parse_args(argv)
    mount = absolute_path(args.required_mount, "required_mount")
    destination = absolute_path(args.output_dir, "output_dir")
    if not mount.is_mount() or not os.access(mount, os.W_OK):
        parser.error("The selected operational mount is unavailable for writes.")
    if not destination.resolve().is_relative_to(mount.resolve()) or destination == mount:
        parser.error("Select a new output directory beneath the required operational mount.")
    if not 0 <= args.port <= 65535:
        parser.error("Select a valid local port or zero for an available port.")
    broker = Broker(load_contexts(absolute_path(args.contexts, "contexts")), destination, required_mount=mount)
    server = LocalServer(("127.0.0.1", args.port), broker)
    print(server.origin+"/#session="+broker.session, flush=True)
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
