# SPDX-License-Identifier: MPL-2.0
"""Supported scientific value objects, independent of execution and storage.

Focused subpackages expose the complete contracts. These common symbols are
kept together so a small scientific calculation needs no framework internals.
"""
from .records.serialization import CanonicalRecord
from .records.decoding import decode_canonical_bytes
from .identity.authority import ResourceBudget
from .identity.provenance import ObjectIdentity
from .evidence.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling

__all__ = [
    "CanonicalRecord", "decode_canonical_bytes", "ResourceBudget", "ObjectIdentity",
    "EvidenceCeiling", "OutcomeAccess", "VisibilityCeiling",
]
