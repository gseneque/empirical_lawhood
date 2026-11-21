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
from hashlib import sha256
from multiprocessing.reduction import DupFd
import os
import sys
from threading import get_ident
from typing import Any, BinaryIO

from empirical_lawhood.science.records.serialization import validate_sha256

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
        self._decoded_owner = None
        self._owns_decoded = True

    def __getstate__(self) -> dict[str, object]:
        """Duplicate the descriptor only into the spawned-process payload."""

        state = self.__dict__.copy()
        # Typed values never cross a process boundary or enlarge its payload.
        state['_decoded_owner'] = None
        state['_owns_decoded'] = True
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
        cursor = _PreopenedBoundedReader(os.dup(descriptor), maximum_bytes=self._maximum_bytes)
        owner = self._typed_owner()
        if owner is self._decoded_owner:
            cursor._decoded_owner = owner
            cursor._owns_decoded = False
        return cursor

    def _typed_owner(self):
        owner = self._decoded_owner
        current = os.getpid(), get_ident()
        if owner is not None and owner['lifetime'][0] == current[0] and owner['lifetime'][1] != current[1]:
            # Reading from another thread must not replace the creator's state.
            return dict(active=True, lifetime=current, key=None, record=None)
        if owner is None or not owner['active'] or owner['lifetime'] != current:
            owner = dict(active=True, lifetime=current, key=None, record=None)
            self._decoded_owner, self._owns_decoded = owner, True
        return owner

    def decode_canonical_record(self, record_type, *, maximum_bytes):
        """Share one immutable value only while its sealed input owner is live.

        Every cursor still consumes the complete bytes. The existing record key
        binds type, validators and Decimal context; numerical settings also
        invalidate reuse. Custom/mutable encodings retain the ordinary decoder.
        """
        from empirical_lawhood.science.records.decoding import decode_canonical_bytes
        from empirical_lawhood.science.records.decoded_record_store import record_store_key
        from empirical_lawhood.execution.local.worker_bootstrap import NUMERICAL_THREAD_ENV_VARS
        if type(maximum_bytes) is not int or maximum_bytes <= 0 or self._extent > maximum_bytes:
            raise ArtifactInputLimitExceeded('typed worker input exceeds its selected byte allowance')
        if self.tell() != 0:
            raise ValueError('typed worker input requires a fresh complete cursor')
        raw = self.read(self._extent + 1)
        descriptor = self._binary_handle().fileno()
        try:
            sealed = fcntl.fcntl(descriptor, 1034) & 0x000F == 0x000F
        except OSError:
            sealed = False
        if not sealed:
            return decode_canonical_bytes(raw, record_type, maximum_bytes=maximum_bytes)

        def numerical_settings():
            controller = sys.modules.get('threadpoolctl')
            pools = () if controller is None else tuple(sorted(
                (p['filepath'], p['num_threads']) for p in controller.threadpool_info()))
            return tuple(os.environ.get(name) for name in
                (*NUMERICAL_THREAD_ENV_VARS, 'NUMBA_NUM_THREADS', 'BLIS_NUM_THREADS')), pools

        digest = sha256(raw).hexdigest()
        proof = record_store_key(record_type, digest, len(raw))
        key = None if proof is None else (proof, numerical_settings())
        owner = self._typed_owner()
        if key is not None and owner['key'] == key:
            return owner['record']
        # Release the superseded value even if fresh decoding subsequently fails.
        owner['key'] = owner['record'] = None
        record = decode_canonical_bytes(raw, record_type, maximum_bytes=maximum_bytes)
        if (key is not None and record._is_cacheable()
                and key == (record_store_key(record_type, digest, len(raw)), numerical_settings())):
            owner['key'], owner['record'] = key, record
        return record

    def close(self) -> None:
        if self._owns_decoded and self._decoded_owner is not None:
            self._decoded_owner.update(active=False, key=None, record=None)
        self._decoded_owner = None
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

