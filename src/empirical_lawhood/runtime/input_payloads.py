# SPDX-License-Identifier: MPL-2.0
"""Immutable operational input bytes; consumers still authenticate their claims."""

from dataclasses import dataclass, field
from hashlib import sha256

from empirical_lawhood.kernel.serialization import CanonicalRecord


@dataclass(frozen=True, slots=True)
class InputBytes:
    """An in-memory alternative to a selected input path, with no trust grant.

    Size and digest describe these bytes only. The consuming owner must check
    its expected identity, schema, revision and scientific admissibility anew.
    This object is operational and is never serialized as a custody receipt.
    """

    payload: bytes
    size_bytes: int = field(init=False)
    sha256: str = field(init=False)

    def __post_init__(self):
        if type(self.payload) is not bytes:
            raise TypeError("in-memory input requires immutable bytes")
        object.__setattr__(self, "size_bytes", len(self.payload))
        object.__setattr__(self, "sha256", sha256(self.payload).hexdigest())

    @classmethod
    def from_record(cls, record):
        if not isinstance(record, CanonicalRecord):
            raise TypeError("in-memory record input requires a canonical record")
        return cls(record.canonical_bytes())

    def bounded_bytes(self, *, maximum_bytes):
        if maximum_bytes is not None and (type(maximum_bytes) is not int or maximum_bytes < 1):
            raise ValueError("in-memory input bound must be a positive integer or None")
        if maximum_bytes is not None and len(self.payload) > maximum_bytes:
            raise ValueError("in-memory input exceeds its byte bound")
        return self.payload
