# SPDX-License-Identifier: MPL-2.0
"""Existing raw-byte transport primitives, independent of array/catalog owners.

The original artifact and native-subwork modules reexport these exact classes
and functions. Custody roots, creator tokens, stores and authority remain with
those owners; importing the selected child needs no coordinator dependencies.
"""

from __future__ import annotations

import ctypes
import errno
import fcntl
from multiprocessing.reduction import DupFd
import os
from typing import Any, BinaryIO

from empirical_lawhood.kernel.serialization import validate_sha256

STREAM_CHUNK_BYTES = 1024 * 1024

class ArtifactPlaneError(RuntimeError):
    "Base error for guarded artifact operations."


class ExternalRootUnavailable(ArtifactPlaneError):
    pass


class ArtifactIdentityConflict(ArtifactPlaneError):
    pass


class ArtifactInputLimitExceeded(ArtifactPlaneError):
    pass



def _anonymous_input_descriptor() -> int:
    """Return one sealable anonymous descriptor without a filesystem locator."""

    # The bundled CPython omits os.memfd_create even on Linux.  Calling the
    # libc wrapper preserves the same kernel primitive without falling back to
    # a named or directory-revealing temporary file.
    libc = ctypes.CDLL(None, use_errno=True)
    try:
        memfd_create = libc.memfd_create
    except AttributeError as error:
        raise ArtifactInputLimitExceeded(
            "anonymous path-free worker inputs are unavailable"
        ) from error
    memfd_create.argtypes = (ctypes.c_char_p, ctypes.c_uint)
    memfd_create.restype = ctypes.c_int
    # linux/memfd.h: MFD_CLOEXEC | MFD_ALLOW_SEALING
    descriptor = int(memfd_create(b"empirical-lawhood-worker-input", 0x0001 | 0x0002))
    if descriptor < 0:
        error_number = ctypes.get_errno()
        raise ArtifactInputLimitExceeded(
            "anonymous path-free worker inputs are unavailable"
        ) from OSError(error_number, os.strerror(error_number))
    return descriptor


def _seal_anonymous_input(descriptor: int) -> None:
    """Make an anonymous staged input immutable before exposing it."""

    # linux/fcntl.h: F_ADD_SEALS with F_SEAL_SEAL, SHRINK, GROW and WRITE.
    try:
        fcntl.fcntl(descriptor, 1033, 0x0001 | 0x0002 | 0x0004 | 0x0008)
    except OSError as error:
        raise ArtifactInputLimitExceeded(
            "anonymous worker input could not be made immutable"
        ) from error


class _PreopenedBoundedReader:
    """Pickle-safe bounded cursor over an anonymous descriptor.

    Positional reads keep duplicated process descriptors independent. A fresh
    preflight cursor may only be minted from kernel-sealed input bytes.
    """

    def __init__(self, descriptor: int, *, maximum_bytes: int) -> None:
        self._descriptor: int | Any | None = descriptor
        self._maximum_bytes = maximum_bytes
        self._bytes_read = 0
        self._position = 0
        self._extent = min(maximum_bytes, os.fstat(descriptor).st_size)
        self._handle: BinaryIO | None = None

    def __getstate__(self) -> dict[str, object]:
        """Duplicate the descriptor only into the spawned-process payload."""

        state = self.__dict__.copy()
        descriptor = self._descriptor
        if isinstance(descriptor, int):
            state["_descriptor"] = DupFd(descriptor)
        return state

    @property
    def bytes_read(self) -> int:
        return self._bytes_read

    def _binary_handle(self) -> BinaryIO:
        if self._handle is None:
            descriptor_reference = self._descriptor
            if descriptor_reference is None:
                raise ValueError("worker input is closed")
            descriptor = (
                descriptor_reference
                if isinstance(descriptor_reference, int)
                else descriptor_reference.detach()
            )
            self._descriptor = None
            self._handle = os.fdopen(descriptor, "rb", closefd=True)
        return self._handle

    def read(self, size: int = -1) -> bytes:
        if size < -1:
            raise ValueError("input read size must be -1 or nonnegative")
        if size == 0:
            # A prepared-port liveness check must not turn its transferable
            # descriptor into a BufferedReader before the worker is spawned.
            if self._descriptor is None and (self._handle is None or self._handle.closed):
                raise ValueError("worker input is closed")
            return b""
        remaining = self._extent - self._position
        requested = remaining + 1 if size == -1 else min(size, remaining + 1)
        payload = os.pread(self._binary_handle().fileno(), requested, self._position)
        if len(payload) > remaining:
            raise ArtifactInputLimitExceeded("worker exceeded its input-scan budget")
        self._bytes_read += len(payload)
        self._position += len(payload)
        return payload

    def tell(self) -> int:
        self.read(0)
        return self._position

    def seek(self, offset: int, whence: int = os.SEEK_SET) -> int:
        """Replay only within the exact selected descriptor interval.

        ``bytes_read`` remains cumulative diagnostic work; it is never reset
        by seeking or confused with the independent positional offset.
        """
        self.read(0)
        if type(offset) is not int or type(whence) is not int or whence not in (os.SEEK_SET, os.SEEK_CUR, os.SEEK_END):
            raise ValueError("worker cursor requires an integer bounded seek")
        origin = 0 if whence == os.SEEK_SET else self._position if whence == os.SEEK_CUR else self._extent
        position = origin + offset
        if not 0 <= position <= self._extent:
            raise ValueError("worker cursor seek exceeds its exact selected interval")
        self._position = position
        return position

    def readable(self) -> bool:
        self.read(0)
        return True

    def seekable(self) -> bool:
        self.read(0)
        return True

    def cursor(self) -> _PreopenedBoundedReader:
        """Fresh independent offset over these exact immutable bytes; no copy."""
        if self._handle is not None:
            descriptor = self._handle.fileno()
        else:
            reference = self._descriptor
            if reference is None:
                raise ValueError("worker input is closed")
            descriptor = reference if isinstance(reference, int) else reference.detach()
            self._descriptor = descriptor
        try:
            seals = fcntl.fcntl(descriptor, 1034)  # Linux F_GET_SEALS.
        except OSError as error:
            raise ArtifactInputLimitExceeded("preflight input is not kernel-sealed") from error
        if seals & 0x000F != 0x000F:
            raise ArtifactInputLimitExceeded("preflight input is not kernel-sealed")
        return _PreopenedBoundedReader(os.dup(descriptor), maximum_bytes=self._maximum_bytes)

    def close(self) -> None:
        if self._handle is not None:
            self._handle.close()
            self._handle = None
            return
        descriptor_reference = self._descriptor
        self._descriptor = None
        if descriptor_reference is None:
            return
        if isinstance(descriptor_reference, int):
            try:
                os.close(descriptor_reference)
            except OSError as error:
                # A long-lived spawned worker can outlive the resource-sharer
                # copy of this descriptor.  EBADF therefore means the port is
                # already closed, which is the exact requested postcondition.
                if error.errno != errno.EBADF:
                    raise
            return
        try:
            descriptor = descriptor_reference.detach()
        except (EOFError, ValueError):
            return
        try:
            os.close(descriptor)
        except OSError as error:
            if error.errno != errno.EBADF:
                raise



def _output_chunk_bound(maximum_bytes, maximum_chunk_bytes, expected_size_bytes,
                        expected_physical_sha256):
    """Validate source allowances before narrowing the transport chunk size."""
    if (type(maximum_bytes) is not int or maximum_bytes <= 0
            or type(maximum_chunk_bytes) is not int or maximum_chunk_bytes <= 0):
        raise ValueError("native subwork output requires positive integer byte and source chunk allowances")
    if (expected_size_bytes is None) != (expected_physical_sha256 is None):
        raise ValueError("native subwork output requires expected size and digest together")
    if expected_size_bytes is not None:
        if type(expected_size_bytes) is not int or not 0 <= expected_size_bytes <= maximum_bytes:
            raise ValueError("native subwork output expected size exceeds its integer byte allowance")
        if type(expected_physical_sha256) is not str:
            raise ValueError("native subwork output expected digest must be a SHA256 string")
        validate_sha256(expected_physical_sha256, field_name="expected_physical_sha256")
    return min(maximum_bytes, maximum_chunk_bytes, STREAM_CHUNK_BYTES)


def _output_chunks(chunks, source_chunk_bound, transport_chunk_bound):
    for chunk in chunks:
        if type(chunk) is not bytes or len(chunk) > source_chunk_bound:
            raise ValueError("native subwork output changes its selected immutable chunk contract")
        for offset in range(0, len(chunk), transport_chunk_bound):
            yield chunk[offset:offset + transport_chunk_bound]

