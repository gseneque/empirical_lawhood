# SPDX-License-Identifier: MPL-2.0
"""Operational delivery selection; original science and custody stay unchanged."""
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_relative_locator, validate_stable_id
from empirical_lawhood.runtime.artifacts import ExternalRootContract

from .selection import MatrixResearchProgrammePlan


@dataclass(frozen=True, slots=True)
class MatrixProgrammeProductExportSelection(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-programme/product-export-selection'
    record_id: str
    programme: ObjectIdentity
    output_relative_path: str

    def __post_init__(self):
        validate_stable_id(self.record_id)
        validate_relative_locator(self.output_relative_path)
        if self.output_relative_path == '.':
            raise ValueError('Matrix product delivery needs its own selected directory')
        if (type(self.programme) is not ObjectIdentity
                or (self.programme.object_schema, self.programme.object_version) !=
                    (MatrixResearchProgrammePlan.SCHEMA, MatrixResearchProgrammePlan.VERSION)):
            raise TypeError('Matrix product delivery requires its exact current original programme')
        self.programme.__post_init__()

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)


@dataclass(frozen=True, slots=True)
class MatrixProgrammePortableProductExportSelection(MatrixProgrammeProductExportSelection):
    """Select a bounded physical replica without changing original identities."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-programme/portable-product-export-selection'
    replica_root: ExternalRootContract
    replica_receipt_path: str
    maximum_bytes: int
    maximum_files: int

    def __post_init__(self):
        super(MatrixProgrammePortableProductExportSelection, self).__post_init__()
        if type(self.replica_root) is not ExternalRootContract:
            raise TypeError('portable delivery requires its explicit guarded storage contract')
        self.replica_root.__post_init__()
        path = PurePosixPath(self.replica_receipt_path)
        if not path.is_absolute() or '..' in path.parts or str(path) != self.replica_receipt_path:
            raise ValueError('portable delivery receipt requires an absolute ordinary path')
        if any(type(value) is not int or value <= 0 for value in (self.maximum_bytes, self.maximum_files)):
            raise ValueError('portable delivery requires explicit positive byte and file bounds')
