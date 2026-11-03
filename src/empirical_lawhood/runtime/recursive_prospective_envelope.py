# SPDX-License-Identifier: MPL-2.0
"""Additive bounded operational storage for an exact prospective specification.

This envelope grants no scientific decoder capacity, source qualification,
issue or reveal authority. The enclosed v1 semantic specification and the
independently decoded scientific selection retain their original contracts.
"""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from .recursive_prospective import RecursiveProspectiveAuthoringSpec, LARGE_RECURSIVE_OPERATIONAL_ENVELOPE_MAXIMUM_BYTES

MAXIMUM_OPERATIONAL_ENVELOPE_BYTES = 32 * 1024**2
MAXIMUM_LARGE_OPERATIONAL_ENVELOPE_BYTES = 64 * 1024**2
MAXIMUM_LARGEST_OPERATIONAL_ENVELOPE_BYTES = LARGE_RECURSIVE_OPERATIONAL_ENVELOPE_MAXIMUM_BYTES


@dataclass(frozen=True, slots=True)
class RecursiveProspectiveAuthoringEnvelope(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/runtime/recursive-prospective-authoring-envelope'
    VERSION: ClassVar[str] = '2.0.0'
    envelope_id: str
    original_spec: RecursiveProspectiveAuthoringSpec
    semantic_spec: ObjectIdentity

    def __post_init__(self):
        validate_stable_id(self.envelope_id)
        if (type(self.original_spec) is not RecursiveProspectiveAuthoringSpec
                or self.envelope_id != self.original_spec.spec_id+'.operational-envelope'
                or self.semantic_spec != ObjectIdentity.from_record(self.original_spec.spec_id, self.original_spec)):
            raise ValueError('operational envelope changes its exact original v1 prospective specification')
        if len(self.canonical_bytes()) > MAXIMUM_OPERATIONAL_ENVELOPE_BYTES:
            raise ValueError('operational envelope exceeds its explicit 32 MiB allocation')

    @classmethod
    def from_spec(cls, spec):
        if type(spec) is not RecursiveProspectiveAuthoringSpec:
            raise ValueError('operational envelope requires the exact original prospective specification type')
        return cls(spec.spec_id+'.operational-envelope', spec, ObjectIdentity.from_record(spec.spec_id, spec))

    def reconstruct(self):
        self.__post_init__()
        return self.original_spec


@dataclass(frozen=True, slots=True)
class RecursiveProspectiveAuthoringEnvelopeV3(CanonicalRecord):
    """Exact v1 bytes in an explicitly larger operational carrier.

    The public owner admits this revision only with the separately installed
    bounded32 scientific decoder. The original v2 carrier remains unchanged.
    """

    SCHEMA: ClassVar[str] = RecursiveProspectiveAuthoringEnvelope.SCHEMA
    VERSION: ClassVar[str] = '3.0.0'
    envelope_id: str
    original_spec: RecursiveProspectiveAuthoringSpec
    semantic_spec: ObjectIdentity

    def __post_init__(self):
        validate_stable_id(self.envelope_id)
        if (type(self.original_spec) is not RecursiveProspectiveAuthoringSpec
                or self.envelope_id != self.original_spec.spec_id+'.operational-envelope-v3'
                or self.semantic_spec != ObjectIdentity.from_record(self.original_spec.spec_id, self.original_spec)):
            raise ValueError('large operational envelope changes its exact original v1 prospective specification')
        if len(self.canonical_bytes()) > MAXIMUM_LARGE_OPERATIONAL_ENVELOPE_BYTES:
            raise ValueError('large operational envelope exceeds its explicit 64 MiB allocation')

    @classmethod
    def from_spec(cls, spec):
        if type(spec) is not RecursiveProspectiveAuthoringSpec:
            raise ValueError('large operational envelope requires the exact original prospective specification type')
        return cls(spec.spec_id+'.operational-envelope-v3', spec, ObjectIdentity.from_record(spec.spec_id, spec))

    def reconstruct(self):
        self.__post_init__()
        return self.original_spec


@dataclass(frozen=True, slots=True)
class RecursiveProspectiveAuthoringEnvelopeV4(CanonicalRecord):
    """Exact v1 bytes in an explicitly larger operational carrier.

    The public owner admits this revision only with the separately installed
    bounded64 scientific decoder. The original v2/v3 carriers remain unchanged.
    """

    SCHEMA: ClassVar[str] = RecursiveProspectiveAuthoringEnvelope.SCHEMA
    VERSION: ClassVar[str] = '4.0.0'
    envelope_id: str
    original_spec: RecursiveProspectiveAuthoringSpec
    semantic_spec: ObjectIdentity

    def __post_init__(self):
        validate_stable_id(self.envelope_id)
        if (type(self.original_spec) is not RecursiveProspectiveAuthoringSpec
                or self.envelope_id != self.original_spec.spec_id+'.operational-envelope-v4'
                or self.semantic_spec != ObjectIdentity.from_record(self.original_spec.spec_id, self.original_spec)):
            raise ValueError('large operational envelope changes its exact original v1 prospective specification')
        if len(self.canonical_bytes()) > MAXIMUM_LARGEST_OPERATIONAL_ENVELOPE_BYTES:
            raise ValueError('large operational envelope exceeds its explicit 256 MiB allocation')

    @classmethod
    def from_spec(cls, spec):
        if type(spec) is not RecursiveProspectiveAuthoringSpec:
            raise ValueError('large operational envelope requires the exact original prospective specification type')
        return cls(spec.spec_id+'.operational-envelope-v4', spec, ObjectIdentity.from_record(spec.spec_id, spec))

    def reconstruct(self):
        self.__post_init__()
        return self.original_spec
