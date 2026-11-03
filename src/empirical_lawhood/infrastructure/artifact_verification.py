# SPDX-License-Identifier: MPL-2.0
"""Bounded invocation-local format proofs, separate from live custody scopes.

This ledger retains no payload, access verdict or callback. Each borrowing read
scope owns its complete byte census and checks it fully before that scope ends.
Eviction only restores ordinary verification; it cannot refuse a larger study.
"""

from collections import OrderedDict
from contextlib import contextmanager
from contextvars import ContextVar
from threading import RLock


MAX_VERIFICATION_PROOFS = 16_384
MAX_VERIFICATION_PROOF_BYTES = 8 * 1024**2
_operation = ContextVar("artifact_verification_operation", default=None)
_forced = ContextVar("artifact_verification_forced", default=False)


class ArtifactVerificationLedger:
    def __init__(self):
        self.active = True
        self.proofs = OrderedDict()
        self.bytes = 0
        self.lock = RLock()

    def get(self, key):
        with self.lock:
            if not self.active:
                return None
            found = self.proofs.get(key)
            if found is not None:
                self.proofs.move_to_end(key)
                return found[0]
            return None

    def put(self, key, identity, header):
        # Header facts are bounded strings, never a decoded scientific body.
        strings = () if header is None else (*tuple(header.top_level_keys or ()), header.schema, header.version)
        if any(type(value) is not str for value in strings):
            return
        size = 512 + sum(len(value.encode("utf-8")) for value in strings)
        size += sum(len(value.encode("utf-8")) for value in key if type(value) is str)
        if size > MAX_VERIFICATION_PROOF_BYTES:
            return
        with self.lock:
            if not self.active:
                return
            previous = self.proofs.pop(key, None)
            if previous is not None:
                self.bytes -= previous[1]
            while self.proofs and (len(self.proofs) >= MAX_VERIFICATION_PROOFS
                    or self.bytes + size > MAX_VERIFICATION_PROOF_BYTES):
                _, (_, removed) = self.proofs.popitem(last=False)
                self.bytes -= removed
            self.proofs[key] = ((identity, header), size)
            self.bytes += size

    def close(self):
        with self.lock:
            self.active = False
            self.proofs.clear()
            self.bytes = 0


@contextmanager
def artifact_verification_operation(*, new=False):
    """Share bounded proofs within this invocation, never with a later call."""
    current = _operation.get()
    if not new and current is not None and current.active:
        yield current
        return
    ledger = ArtifactVerificationLedger()
    token = _operation.set(ledger)
    try:
        yield ledger
    finally:
        ledger.close()
        _operation.reset(token)


@contextmanager
def force_full_verification():
    token = _forced.set(True)
    try:
        yield
    finally:
        _forced.reset(token)


def full_verification_forced():
    return _forced.get()
