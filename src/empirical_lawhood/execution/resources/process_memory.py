# SPDX-License-Identifier: MPL-2.0
"""Return unused allocator pages before a caller repeats its RSS admission."""

import ctypes
import gc
import sys


def release_unused_process_memory() -> None:
    """Collect unreachable objects and release free pages where supported.

    This changes no resource limit and establishes no admission decision.
    Callers must observe actual resident memory again. Live objects remain
    intact, and unavailable allocator support leaves the ordinary check intact.
    """
    gc.collect()
    if sys.platform != "linux":
        return
    try:
        trim = ctypes.CDLL(None).malloc_trim
    except (AttributeError, OSError):
        return
    trim.argtypes = (ctypes.c_size_t,)
    trim.restype = ctypes.c_int
    trim(0)
