# SPDX-License-Identifier: MPL-2.0
"""Bounded, atomic operational selections outside scientific custody packages."""

from hashlib import sha256
import fcntl
import os
from pathlib import Path
import stat
from uuid import uuid4

from empirical_lawhood.storage.application_invocations import _directory
from empirical_lawhood.storage.artifacts import GuardedExternalRoot
from empirical_lawhood.storage.bounded_io import BoundedFileIOError, _open_contained_regular, _read_regular_descriptor


MAX_STATE_BYTES = 1024 * 1024


class WorkbenchStateConflict(ValueError):
    """Another operator changed the selected operational document."""


class WorkbenchStateStore:
    """One selected file under a guarded scratch root; reads never create it."""

    def __init__(self, root: GuardedExternalRoot, path: Path, *, writable: bool):
        if type(root) is not GuardedExternalRoot or type(writable) is not bool:
            raise TypeError("operational state requires its guarded root and access mode")
        self.root, self.path, self.writable = root, Path(path), writable
        parent = Path(root.contract.canonical_path)
        if not self.path.is_absolute() or ".." in self.path.parts or self.path == parent:
            raise ValueError("select one operational file below the scratch root")
        self.relative = self.path.relative_to(parent).as_posix()

    def _current(self, *, writing=False):
        if writing and not self.writable:
            raise PermissionError("the selected operational profile is read-only")
        self.root.verify(for_write=writing)
        return self.root.resolve(self.relative, for_write=writing)

    def read(self):
        path = self._current()
        try:
            descriptor, before = _open_contained_regular(Path(self.root.contract.canonical_path), path, MAX_STATE_BYTES)
        except BoundedFileIOError as error:
            if isinstance(error.__cause__, FileNotFoundError):
                self._current()
                return None
            raise
        raw = _read_regular_descriptor(descriptor, before, maximum_bytes=MAX_STATE_BYTES)
        self._current()
        current = path.stat(follow_symlinks=False)
        if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
                current.st_dev, current.st_ino, current.st_size, current.st_mtime_ns, current.st_ctime_ns):
            raise PermissionError("operational selection changed during its read")
        return raw

    def replace(self, raw: bytes, *, expected_sha256: str | None):
        if type(raw) is not bytes or len(raw) > MAX_STATE_BYTES:
            raise ValueError("operational selection exceeds its byte bound")
        path = self._current(writing=True)
        # Parents are an explicit operational selection, created only by a write.
        current = self.root.verify(for_write=True)
        for part in Path(self.relative).parts[:-1]:
            current /= part
            try:
                current.mkdir(mode=0o700)
            except FileExistsError:
                pass
            self._current(writing=True)
            if current.is_symlink() or not current.is_dir():
                raise PermissionError("operational parent must be an ordinary directory")
        with _directory(path.parent) as parent:
            lock = os.open(path.name + ".lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
                0o600, dir_fd=parent)
            temporary = "." + path.name + "." + uuid4().hex + ".pending"
            try:
                if not stat.S_ISREG(os.fstat(lock).st_mode):
                    raise PermissionError("operational lock must be regular")
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                previous = self.read()
                digest = None if previous is None else sha256(previous).hexdigest()
                if digest != expected_sha256:
                    raise WorkbenchStateConflict("reopen the changed operational selection before updating it")
                descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                    0o600, dir_fd=parent)
                with os.fdopen(descriptor, "wb") as output:
                    output.write(raw)
                    output.flush()
                    os.fsync(output.fileno())
                self._current(writing=True)
                observed = path.parent.stat(follow_symlinks=False)
                opened = os.fstat(parent)
                if (observed.st_dev, observed.st_ino) != (opened.st_dev, opened.st_ino):
                    raise PermissionError("operational parent changed before publication")
                os.replace(temporary, path.name, src_dir_fd=parent, dst_dir_fd=parent)
                os.fsync(parent)
                self._current(writing=True)
            finally:
                try:
                    os.unlink(temporary, dir_fd=parent)
                except FileNotFoundError:
                    pass
                os.close(lock)
        return sha256(raw).hexdigest()
