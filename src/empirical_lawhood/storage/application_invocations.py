# SPDX-License-Identifier: MPL-2.0
"""Durable dispatch metadata; no scientific responses or authority are cached."""

from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import stat
from uuid import uuid4

from empirical_lawhood.storage.atomic_files import rename_noreplace
from empirical_lawhood.storage.bounded_io import BoundedFileIOError, _open_contained_regular, _read_regular_descriptor


MAX_INVOCATION_RECORD_BYTES = 256 * 1024
_HANDLE = re.compile(r"[0-9a-f]{64}\Z")


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def record_bytes(document):
    raw = json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()+b"\n"
    if len(raw) > MAX_INVOCATION_RECORD_BYTES:
        raise ValueError("application invocation metadata exceeds its byte bound")
    return raw


def request_binding(request):
    """Bind unsaved text exactly without copying arbitrary edits into general logs."""
    parameters = dict(request["parameters"])
    if "text" in parameters:
        text = parameters["text"]
        if type(text) is not str:
            raise ValueError("editable request text must be a string")
        raw = text.encode("utf-8")
        parameters["text"] = {"sha256": sha256(raw).hexdigest(), "bytes": len(raw), "body_retained": False}
    return {**request, "parameters": parameters}


def process_identity(pid=None):
    """Linux PID reuse guard; unavailable observations are never called dead."""
    pid = os.getpid() if pid is None else pid
    if type(pid) is not int or pid <= 0:
        raise ValueError("process observation requires a positive PID")
    try:
        raw = Path(f"/proc/{pid}/stat").read_text()
        rest = raw.rsplit(") ", 1)[1].split()
        boot = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
    except FileNotFoundError:
        return {"pid": pid, "observation": "ABSENT"}
    except (OSError, ValueError, IndexError):
        return {"pid": pid, "observation": "UNAVAILABLE"}
    return {"pid": pid, "boot_id": boot, "start_ticks": rest[19],
            "observation": "EXITED" if rest[0] == "Z" else "PRESENT"}


def same_live_process(selected):
    if type(selected) is not dict or selected.get("observation") != "PRESENT":
        return None
    current = process_identity(selected["pid"])
    if current["observation"] == "UNAVAILABLE":
        return None
    return current == selected


@contextmanager
def _directory(path):
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    fd = os.open(path.anchor, flags)
    try:
        for part in path.parts[1:]:
            child = os.open(part, flags, dir_fd=fd)
            os.close(fd)
            fd = child
        yield fd
    finally:
        os.close(fd)


class ApplicationInvocationStore:
    """One explicitly selected mounted root, with immutable entry/return files."""

    def __init__(self, root: Path, required_mount: Path):
        self.root, self.required_mount = Path(root), Path(required_mount)
        if (not self.root.is_absolute() or not self.required_mount.is_absolute()
                or ".." in self.root.parts or ".." in self.required_mount.parts
                or not self.root.is_relative_to(self.required_mount) or self.root == self.required_mount):
            raise ValueError("invocation storage requires an explicit root below its selected mount")
        self._check_mount()
        with _directory(self.root) as fd:
            observed = os.fstat(fd)
            if observed.st_dev != self.required_mount.stat().st_dev:
                raise OSError("invocation storage is on a different selected volume")
            self.identity = observed.st_dev, observed.st_ino

    def _check_mount(self):
        if not self.required_mount.is_mount():
            raise OSError("the selected invocation mount is unavailable")

    def require_current(self):
        self._check_mount()
        with _directory(self.root) as fd:
            observed = os.fstat(fd)
            if (observed.st_dev, observed.st_ino) != self.identity or observed.st_dev != self.required_mount.stat().st_dev:
                raise OSError("invocation storage identity changed")

    def path(self, handle):
        if type(handle) is not str or _HANDLE.fullmatch(handle) is None:
            raise ValueError("invalid invocation handle")
        return self.root / handle

    @contextmanager
    def _locked(self):
        self.require_current()
        with _directory(self.root) as parent:
            fd = os.open(".dispatch.lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK, 0o600, dir_fd=parent)
            try:
                if not stat.S_ISREG(os.fstat(fd).st_mode):
                    raise OSError("invocation lock is not a regular file")
                fcntl.flock(fd, fcntl.LOCK_EX)
                self.require_current()
                yield
            finally:
                os.close(fd)

    def _read(self, path):
        self.require_current()
        try:
            fd, before = _open_contained_regular(self.root, path, MAX_INVOCATION_RECORD_BYTES)
        except FileNotFoundError:
            return None
        except BoundedFileIOError as error:
            if isinstance(error.__cause__, FileNotFoundError):
                self.require_current()
                return None
            raise
        raw = _read_regular_descriptor(fd, before, maximum_bytes=MAX_INVOCATION_RECORD_BYTES)
        document = json.loads(raw)
        if record_bytes(document) != raw:
            raise ValueError("invocation metadata changed its exact encoding")
        self.require_current()
        return document

    def _write(self, path, document, *, replace=False):
        raw = record_bytes(document)
        self.require_current()
        with _directory(path.parent) as parent:
            temporary = ".publish-" + uuid4().hex
            fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600, dir_fd=parent)
            try:
                try:
                    view = memoryview(raw)
                    while view:
                        count = os.write(fd, view)
                        if count <= 0:
                            raise OSError("invocation publication made no progress")
                        view = view[count:]
                    os.fsync(fd)
                finally:
                    os.close(fd)
                self.require_current()
                if replace:
                    os.replace(temporary, path.name, src_dir_fd=parent, dst_dir_fd=parent)
                else:
                    rename_noreplace(temporary, path.name, source_dir_fd=parent, destination_dir_fd=parent)
                os.fsync(parent)
            finally:
                try:
                    os.unlink(temporary, dir_fd=parent)
                except FileNotFoundError:
                    pass

    def publish(self, handle, name, document):
        if name not in ("launched", "entered", "returned", "launch-failed", "delivery", "progress"):
            raise ValueError("unsupported invocation record")
        self._write(self.path(handle) / (name + ".json"), document, replace=name == "progress")

    def intent(self, handle):
        intent = self._read(self.path(handle) / "intent.json")
        if intent is None or intent.get("handle") != handle:
            raise ValueError("invocation has no complete original dispatch intent")
        binding = intent["binding"]
        request = binding["request"]
        if (intent.get("schema") != "empirical-lawhood/application/invocation-intent" or intent.get("version") != "1.0.0"
                or sha256(record_bytes(binding)).hexdigest() != intent["binding_sha256"]
                or sha256((request["context_id"]+":"+request["request_id"]).encode()).hexdigest() != handle
                or binding["required_mount"] != str(self.required_mount)):
            raise ValueError("invocation intent changes its original identity")
        return intent

    def claim(self, *, context_id, context_sha256, engine_sha256, context, request, client):
        handle = sha256((context_id + ":" + request["request_id"]).encode()).hexdigest()
        binding = {"context_sha256": context_sha256, "engine_sha256": engine_sha256,
                   "context": context, "request": request_binding(request),
                   "request_sha256": sha256(record_bytes(request)).hexdigest(), "client": client,
                   "required_mount": str(self.required_mount)}
        pin = sha256(record_bytes(binding)).hexdigest()
        active = self.root / ("active-" + sha256(context_id.encode()).hexdigest() + ".json")
        with self._locked():
            directory = self.path(handle)
            if directory.exists() or directory.is_symlink():
                retained = self.intent(handle)
                if retained["binding_sha256"] != pin or retained["binding"] != binding:
                    raise ValueError("request key is already bound to different operands or context")
                return handle, False
            previous = self._read(active)
            if previous is not None:
                state = self.snapshot(previous["handle"])
                if state["state"] not in ("RETURNED", "LAUNCH_FAILED"):
                    raise RuntimeError("context has an active or uncertain invocation; inspect its original handle")
            with _directory(self.root) as parent:
                os.mkdir(handle, mode=0o700, dir_fd=parent)
                os.fsync(parent)
            self._write(directory / "intent.json", {
                "schema": "empirical-lawhood/application/invocation-intent", "version": "1.0.0",
                "handle": handle, "accepted_utc": utc_now(), "binding_sha256": pin, "binding": binding,
                "scientific_response_retained": False, "scientific_authority": "NONE"})
            self._write(active, {"handle": handle}, replace=True)
        return handle, True

    def snapshot(self, handle):
        intent = self.intent(handle)
        entered = self._read(self.path(handle) / "entered.json")
        returned = self._read(self.path(handle) / "returned.json")
        launched = self._read(self.path(handle) / "launched.json")
        failed = self._read(self.path(handle) / "launch-failed.json")
        selected = (entered or launched or {}).get("process")
        alive = same_live_process(selected) if selected is not None else None
        for record in (entered, returned, launched, failed):
            if record is not None and (record.get("handle") != handle or record.get("binding_sha256") != intent["binding_sha256"]):
                raise ValueError("invocation observation changes its original dispatch binding")
        state = "RETURNED" if returned else "LAUNCH_FAILED" if failed and entered is None else "RUNNING" if entered and alive else "ACCEPTED" if not entered and alive else "UNCERTAIN"
        return {"schema": "empirical-lawhood/application/invocation-state", "version": "1.0.0",
                "handle": handle, "context_id": intent["binding"]["request"]["context_id"],
                "operation": intent["binding"]["request"]["operation"], "state": state,
                "accepted_utc": intent["accepted_utc"], "binding_sha256": intent["binding_sha256"],
                "process_live": alive, "entry_observed": entered is not None,
                "return": returned, "launch_failure": failed,
                "result_access": "ORIGINAL_REQUEST_ONLY_OR_FRESH_OWNING_READ",
                "scientific_response_retained": False, "scientific_authority": "NONE"}
