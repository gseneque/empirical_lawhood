# SPDX-License-Identifier: MPL-2.0
"""Custody association beside the unchanged prospective authoring packet.

This record binds an original experiment design to its actual outer candidate.
It supplies no scientific qualification or issue, execution or reveal authority.
"""

from dataclasses import dataclass
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.kernel.experimental_design import UnitAllocation
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, require_sorted_unique_ids, validate_stable_id
from empirical_lawhood.runtime.candidate_compiler import ExecutableStudyCandidate
from empirical_lawhood.runtime.experiment_preparation import ExperimentInstanceBinding
from empirical_lawhood.runtime.recursive_handoff import AuthoredRecursiveWave, RecursiveWaveMember


ASSOCIATION_FILENAME = "experiment-association.json"
INSTANCE_FILENAME = "experiment-instance.json"
SPECIFICATION_FILENAME = "experiment-specification.json"
ALLOCATION_FILENAME = "experiment-allocation.json"
SOURCE_PREFIX = "experiment-source-"


def source_filename(reference: ObjectIdentity) -> str:
    return SOURCE_PREFIX + sha256(reference.object_id.encode()).hexdigest() + ".json"


def instance_identity(instance: ExperimentInstanceBinding) -> ObjectIdentity:
    """One original design role shared by authoring and every cold read."""
    return ObjectIdentity.from_record("experiment-instance." + instance.specification.object_fingerprint, instance)


@dataclass(frozen=True, slots=True)
class ProspectiveExperimentAssociation(CanonicalRecord):
    """The final committed reference to two independently authenticated packets."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/experiment-preparation/prospective-association"
    association_id: str
    prospective_wave: ObjectIdentity
    candidate: ObjectIdentity
    instance: ObjectIdentity
    members: tuple[RecursiveWaveMember, ...]

    def __post_init__(self):
        validate_stable_id(self.association_id)
        for value, kind in ((self.prospective_wave, AuthoredRecursiveWave),
                (self.candidate, ExecutableStudyCandidate), (self.instance, ExperimentInstanceBinding)):
            if (type(value) is not ObjectIdentity
                    or (value.object_schema, value.object_version) != (kind.SCHEMA, kind.VERSION)):
                raise ValueError("prospective experiment association requires its exact wave, outer candidate and instance types")
            value.__post_init__()
        if type(self.members) is not tuple or any(type(row) is not RecursiveWaveMember for row in self.members):
            raise TypeError("prospective experiment companion requires its closed typed member census")
        require_sorted_unique_ids(self.members, attribute="filename", field_name="experiment companion members")
        by_name = {}
        for row in self.members:
            row.__post_init__()
            if type(row.identity) is not ObjectIdentity:
                raise TypeError("prospective experiment member requires its exact canonical identity")
            row.identity.__post_init__()
            by_name[row.filename] = row.identity
            if row.filename not in (SPECIFICATION_FILENAME, ALLOCATION_FILENAME, INSTANCE_FILENAME) and row.filename != source_filename(row.identity):
                raise ValueError("prospective experiment companion includes an unselected member or source alias")
        if (not {SPECIFICATION_FILENAME, ALLOCATION_FILENAME, INSTANCE_FILENAME} <= set(by_name)
                or by_name[INSTANCE_FILENAME] != self.instance
                or (by_name[ALLOCATION_FILENAME].object_schema, by_name[ALLOCATION_FILENAME].object_version)
                    != (UnitAllocation.SCHEMA, UnitAllocation.VERSION)):
            raise ValueError("prospective experiment companion omits its original design or exact instance")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.association_id, self)


@dataclass(frozen=True, slots=True)
class PreparedProspectiveExperimentHandoff:
    """A fresh owning handoff and its authenticated original design association."""

    handoff: object
    association: ProspectiveExperimentAssociation
    instance: ExperimentInstanceBinding
    candidate: ExecutableStudyCandidate
    specification: CanonicalRecord
    allocation: UnitAllocation
    design_records: tuple[tuple[str, CanonicalRecord], ...]
    original_input_access: object | None = None
