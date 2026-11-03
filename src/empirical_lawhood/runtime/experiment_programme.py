# SPDX-License-Identifier: MPL-2.0
"""Public composite programme selector; component receipts retain authority."""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id


PROGRAMME_DESCRIPTOR_FILENAME = "experiment-programme.json"
MAX_PROGRAMME_DESCRIPTOR_BYTES = 64 * 1024


@dataclass(frozen=True, slots=True)
class ExperimentProgrammeDescriptor(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/runtime/experiment-programme-descriptor"
    record_id: str
    protocol_id: str
    specification: ObjectIdentity
    programme: ObjectIdentity

    def __post_init__(self):
        validate_stable_id(self.record_id)
        validate_stable_id(self.protocol_id)
        for value in (self.specification, self.programme):
            if type(value) is not ObjectIdentity:
                raise TypeError("Programme descriptor requires exact immutable selection identities")
            value.__post_init__()
