# SPDX-License-Identifier: MPL-2.0
"""Single-owner temporary output files, consumable as streams or by transfer.

These objects own newly created scratch, never retained evidence. They carry no
format-validation proof. The artifact plane still measures the actual bytes,
validates its selected codecs and publishes through its ordinary batch protocol.
"""

from __future__ import annotations

from collections.abc import Iterator
import errno
import hashlib
import os
from pathlib import Path
import stat
import threading

from empirical_lawhood.storage.artifact_validation import ArtifactIdentityConflict
from empirical_lawhood.storage.atomic_files import rename_noreplace


def _identity(value: os.stat_result) -> tuple[int, int, int, int, int, int]:
    return (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns,
            value.st_ctime_ns, value.st_nlink)


def _same_file(path: Path, identity: tuple[int, int]) -> bool:
    if not identity[1]:
        return False
    try:
        current = path.lstat()
    except FileNotFoundError:
        return False
    return stat.S_ISREG(current.st_mode) and (current.st_dev, current.st_ino) == identity


class OwnedOutputFile:
    """Create, seal and consume one private file in its original process/thread.

    ``close`` releases scratch and descriptors on every exit. Once storage takes
    the file, only its staging cleanup owns the moved pathname. Closing the
    producer cannot delete a published artifact, even after a failed commit.
    """

    def __init__(self, path: Path) -> None:
        self._owner = (os.getpid(), threading.get_ident())
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                             stat.S_IRUSR | stat.S_IWUSR)
        original = None
        try:
            original = os.fstat(descriptor)
            self._writer = os.fdopen(descriptor, "wb", closefd=True)
        except BaseException:
            try:
                if original is not None and _same_file(path, (original.st_dev, original.st_ino)):
                    path.unlink()
            finally:
                os.close(descriptor)
            raise
        self._file_identity = (original.st_dev, original.st_ino)
        self._path = path
        self._owned_path: Path | None = path
        self._reader: int | None = None
        self._snapshot: os.stat_result | None = None
        self._digest = hashlib.sha256()
        self._size = 0
        self._offered = False
        self._reading = False
        self._closed = False

    def __reduce__(self):
        raise TypeError("owned output files cannot cross a process or copy boundary")

    def _require_owner(self) -> None:
        if self._owner != (os.getpid(), threading.get_ident()):
            raise ArtifactIdentityConflict("owned output file belongs to another lifetime")
        if self._closed:
            raise ArtifactIdentityConflict("owned output file is closed")

    @property
    def size_bytes(self) -> int:
        return self._size

    @property
    def physical_sha256(self) -> str:
        return self._digest.hexdigest()

    def write(self, chunk: bytes) -> None:
        self._require_owner()
        if self._snapshot is not None or self._writer.closed:
            raise ArtifactIdentityConflict("owned output file is already sealed")
        if not isinstance(chunk, bytes):
            raise TypeError("output chunks must be immutable bytes")
        if self._writer.write(chunk) != len(chunk):
            raise OSError("incomplete temporary output write")
        self._size += len(chunk)
        self._digest.update(chunk)

    def seal(self) -> None:
        """Flush once, then retain only a read descriptor for the same file."""
        self._require_owner()
        if self._snapshot is not None or self._writer.closed:
            raise ArtifactIdentityConflict("owned output file is already sealed")
        self._writer.flush()
        os.fsync(self._writer.fileno())
        original = os.fstat(self._writer.fileno())
        flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC
        reader = os.open(self._path, flags)
        try:
            current = os.fstat(reader)
            if (not stat.S_ISREG(current.st_mode) or current.st_nlink != 1
                    or current.st_size != self._size or _identity(current) != _identity(original)):
                raise ArtifactIdentityConflict("temporary output identity changed before sealing")
            self._writer.close()
        except BaseException:
            os.close(reader)
            raise
        self._reader = reader
        self._snapshot = current

    def _require_sealed(self) -> os.stat_result:
        self._require_owner()
        if self._reader is None or self._snapshot is None:
            raise ArtifactIdentityConflict("owned output file is not sealed")
        current = os.fstat(self._reader)
        try:
            selected = self._path.lstat()
        except OSError as error:
            raise ArtifactIdentityConflict("owned output pathname is unavailable") from error
        if (not stat.S_ISREG(selected.st_mode) or _identity(current) != _identity(self._snapshot)
                or _identity(selected) != _identity(current)):
            raise ArtifactIdentityConflict("owned output file changed")
        return current

    def chunks(self, maximum_chunk_bytes: int) -> OwnedFileChunks:
        self._require_sealed()
        if maximum_chunk_bytes <= 0:
            raise ValueError("output stream chunk limit must be positive")
        if self._offered:
            raise ArtifactIdentityConflict("owned output stream was already selected")
        self._offered = True
        return OwnedFileChunks(self, maximum_chunk_bytes)

    def _chunks(self, maximum_chunk_bytes: int) -> Iterator[bytes]:
        self._require_sealed()
        if self._reading:
            raise ArtifactIdentityConflict("owned output stream was already consumed")
        self._reading = True
        remaining = self._size
        try:
            while remaining:
                self._require_owner()
                assert self._reader is not None
                chunk = os.read(self._reader, min(maximum_chunk_bytes, remaining))
                if not chunk:
                    raise ArtifactIdentityConflict("owned output file was truncated")
                remaining -= len(chunk)
                yield chunk
            self._require_owner()
            assert self._reader is not None
            if os.read(self._reader, 1):
                raise ArtifactIdentityConflict("owned output file grew")
        finally:
            if not self._closed:
                self._require_sealed()

    def close(self) -> None:
        if self._closed:
            return
        self._require_owner()
        self._closed = True
        try:
            self._writer.close()
        finally:
            try:
                if self._owned_path is not None and _same_file(self._owned_path, self._file_identity):
                    self._owned_path.unlink()
            finally:
                if self._reader is not None:
                    os.close(self._reader)
                    self._reader = None


class OwnedFileChunks:
    """One stream selection with an optional same-filesystem ownership transfer."""

    def __init__(self, source: OwnedOutputFile, maximum_chunk_bytes: int) -> None:
        self._source = source
        self._maximum_chunk_bytes = maximum_chunk_bytes
        self._staged: tuple[Path, tuple[int, int]] | None = None

    def __iter__(self) -> Iterator[bytes]:
        return self._source._chunks(self._maximum_chunk_bytes)

    def try_adopt(self, destination: Path, *, maximum_bytes: int) -> bool:
        """Move only an unconsumed, sealed source. EXDEV keeps the stream route."""
        source = self._source
        before = source._require_sealed()
        if source._reading or source._owned_path is None or self._staged is not None:
            raise ArtifactIdentityConflict("owned output file was already consumed or transferred")
        if before.st_size > maximum_bytes:
            raise ArtifactIdentityConflict("owned output exceeds its publication byte limit")
        # A missing usable inode cannot establish exclusive pathname ownership.
        if not before.st_ino:
            return False
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
        source_parent = os.open(source._path.parent, flags)
        try:
            destination_parent = os.open(destination.parent, flags)
            try:
                if os.fstat(destination_parent).st_dev != before.st_dev:
                    return False
                selected = os.stat(source._path.name, dir_fd=source_parent, follow_symlinks=False)
                if _identity(selected) != _identity(before):
                    raise ArtifactIdentityConflict("owned output pathname changed before transfer")
                try:
                    rename_noreplace(source._path.name, destination.name,
                                     source_dir_fd=source_parent, destination_dir_fd=destination_parent)
                except OSError as error:
                    if error.errno == errno.EXDEV:
                        return False
                    raise
                finally:
                    # Also recognize a completed syscall followed by an exception.
                    # Never claim an occupied foreign destination for cleanup.
                    if (not source._path.exists()
                            and _same_file(destination, source._file_identity)):
                        source._owned_path = None
                        source._path = destination
                        self.record_staged(destination, before)
                assert source._reader is not None
                after = os.fstat(source._reader)
                if _identity(before)[:4] + (before.st_nlink,) != _identity(after)[:4] + (after.st_nlink,):
                    raise ArtifactIdentityConflict("owned output changed during transfer")
                # Rename may change ctime. Subsequent checks use the moved file.
                source._snapshot = after
                source._require_sealed()
                os.fsync(destination_parent)
                os.fsync(source_parent)
                return True
            finally:
                os.close(destination_parent)
        finally:
            os.close(source_parent)

    def record_staged(self, path: Path, observed: os.stat_result) -> None:
        """Remember only a file created or transferred by this staging call."""
        self._source._require_owner()
        self._staged = (path, (observed.st_dev, observed.st_ino))

    def require_identity(self, size: int, digest: str) -> None:
        self._source._require_sealed()
        if (size, digest) != (self._source.size_bytes, self._source.physical_sha256):
            raise ArtifactIdentityConflict("owned output differs from its collected bytes")

    def discard_staged(self, path: Path) -> None:
        """Release this call's staging file; never remove a replacement path."""
        if self._source._owner != (os.getpid(), threading.get_ident()):
            raise ArtifactIdentityConflict("owned output file belongs to another lifetime")
        if self._staged is not None and self._staged[0] == path:
            if _same_file(path, self._staged[1]):
                path.unlink()
            self._staged = None
