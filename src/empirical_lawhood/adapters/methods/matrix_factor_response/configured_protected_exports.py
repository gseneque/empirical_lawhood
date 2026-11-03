# SPDX-License-Identifier: MPL-2.0
"""Explicit export destination and original issued configured E3 selection."""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_relative_locator, validate_stable_id


@dataclass(frozen=True, slots=True)
class ConfiguredProtectedE3ProductExportSelection(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/configured-protected-product-export-selection"
    record_id: str
    run_id: str
    original_package: ObjectIdentity
    reveal_authority_id: str
    frozen_package_record_id: str
    output_relative_path: str

    def __post_init__(self):
        for name in ("record_id", "run_id", "reveal_authority_id", "frozen_package_record_id"):
            validate_stable_id(getattr(self, name), field_name=name)
        validate_relative_locator(self.output_relative_path)
        if (type(self.original_package) is not ObjectIdentity
                or (self.original_package.object_schema, self.original_package.object_version) !=
                    ("empirical-lawhood/api/experiment-package", "1.0.0")):
            raise TypeError("configured E3 export requires its exact original issued package identity")
        self.original_package.__post_init__()

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)
