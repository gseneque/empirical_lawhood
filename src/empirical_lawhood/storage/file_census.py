# SPDX-License-Identifier: MPL-2.0
"""One current body hash per physical file in a complete census pass.

Every logical path still opens a descriptor under its own byte allowance.
Only unchanged hardlinks share a body hash. A closing census uses a new owner
and hashes every physical body again; this owner is not an artifact cache.
"""

import os
from pathlib import Path
from threading import get_ident

from empirical_lawhood.storage.bounded_io import (
    BoundedFileIOError,
    _hash_regular_descriptor,
    _identity,
    _open_regular,
    _stable_descriptor,
)


def _member_identity(observed):
    return (*_identity(observed), observed.st_mode, observed.st_uid, observed.st_gid)


class FileHashCensus:
    """Finite, thread-local body reuse; callers retain full census comparisons."""

    def __init__(self):
        self._owner = (os.getpid(), get_ident())
        self._bodies = {}
        self._active = False

    def __enter__(self):
        if self._active or self._owner != (os.getpid(), get_ident()):
            raise RuntimeError('file census requires its original independent owner')
        self._active = True
        return self

    def __exit__(self, *_):
        self._active = False
        self._bodies.clear()

    def sha256(self, path, *, maximum_bytes):
        if not self._active or self._owner != (os.getpid(), get_ident()):
            raise RuntimeError('file census reuse requires its active original owner')
        path = Path(path)
        descriptor, before = _open_regular(path, maximum_bytes=maximum_bytes)
        identity = _member_identity(before)
        # A zero inode supplies no usable physical identity. Single-link files
        # cannot share their body through another live name in this census.
        reusable = before.st_ino != 0 and before.st_nlink > 1
        previous = self._bodies.get(identity) if reusable else None
        if previous is None:
            result = _hash_regular_descriptor(descriptor, before, maximum_bytes=before.st_size if maximum_bytes is None else maximum_bytes, opened_size_bound=maximum_bytes is None)
        else:
            # Opening is mandatory even for aliases: current access, type, size
            # and identity cannot be supplied by a previous path's permission.
            with _stable_descriptor(descriptor, before, operation='hardlink census'):
                result = previous
        if _member_identity(path.lstat()) != identity:
            raise BoundedFileIOError('bounded census path changed during its read')
        if reusable:
            self._bodies[identity] = result
        return result
