# SPDX-License-Identifier: MPL-2.0
"""Untrusted locator for fresh receipt-bound native TRAIN bank reconstruction."""
from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_relative_locator, validate_stable_id
from empirical_lawhood.runtime.artifacts import ArtifactWriteResult
from empirical_lawhood.runtime.recursive_handoff import RecursiveImplementationBinding


@dataclass(frozen=True, slots=True)
class NativeTrainingExportAdoptionSelection(CanonicalRecord):
    """Select original custody; no field attests a successful scientific replay."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/runtime/native-training-export-adoption-selection'
    record_id: str
    authored_directory: str
    run_id: str
    packet: ObjectIdentity
    execution_plan: ObjectIdentity
    producer_implementation: RecursiveImplementationBinding
    specification: ObjectIdentity
    request: ObjectIdentity
    bank_record_id: str
    bank_publications: tuple[ArtifactWriteResult, ...]

    def __post_init__(self):
        for value in (self.record_id, self.run_id, self.bank_record_id):
            validate_stable_id(value)
        validate_relative_locator(self.authored_directory)
        if type(self.producer_implementation) is not RecursiveImplementationBinding:
            raise TypeError('export adoption requires its exact historical producer implementation')
        self.producer_implementation.__post_init__()
        for value in (self.packet, self.execution_plan, self.specification, self.request):
            if type(value) is not ObjectIdentity:
                raise TypeError('export adoption requires exact original source and graph identities')
            value.__post_init__()
        if (type(self.bank_publications) is not tuple or len(self.bank_publications) != 3
                or any(type(value) is not ArtifactWriteResult for value in self.bank_publications)
                or len({value.materialization.relative_path for value in self.bank_publications}) != 3):
            raise ValueError('export adoption requires all three distinct original bank publications')
        for value in self.bank_publications:
            value.__post_init__()

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)
