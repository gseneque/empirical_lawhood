# SPDX-License-Identifier: MPL-2.0
"""Selected native TRAIN bank publication; no task or authority transition."""
from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_relative_locator, validate_stable_id


@dataclass(frozen=True, slots=True)
class NativeTrainingBankExportSelection(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-experiment/native-training-bank-export-selection'
    VERSION: ClassVar[str] = '2.0.0'
    record_id: str
    bank_record_id: str
    output_relative_path: str

    def __post_init__(self):
        validate_stable_id(self.record_id)
        validate_stable_id(self.bank_record_id)
        validate_relative_locator(self.output_relative_path)

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)
