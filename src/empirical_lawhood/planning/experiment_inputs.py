# SPDX-License-Identifier: MPL-2.0
"""Explicit byte bindings for a selected experiment's closed domain inputs.

These selections authenticate bytes and revisions. They convey no source
eligibility, exposure, issue, reveal or scientific qualification.
"""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord, validate_relative_locator, validate_semantic_version, validate_stable_id,
)


@dataclass(frozen=True, slots=True)
class ExperimentInputBinding(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/experiment-inputs/binding"
    key: str
    identity: ObjectIdentity
    relative_path: str
    maximum_bytes: int

    def __post_init__(self):
        validate_stable_id(self.key)
        if type(self.identity) is not ObjectIdentity:
            raise TypeError("experiment input needs its immutable byte identity")
        validate_relative_locator(self.relative_path)
        if type(self.maximum_bytes) is not int or self.maximum_bytes < 1:
            raise ValueError("experiment input needs an explicit positive byte bound")


@dataclass(frozen=True, slots=True)
class ExperimentInputSelection(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/experiment-inputs/selection"
    selection_id: str
    protocol_id: str
    bindings: tuple[ExperimentInputBinding, ...]

    def __post_init__(self):
        validate_stable_id(self.selection_id)
        validate_stable_id(self.protocol_id)
        if (type(self.bindings) is not tuple
                or any(type(row) is not ExperimentInputBinding for row in self.bindings)
                or tuple(row.key for row in self.bindings)
                != tuple(sorted({row.key for row in self.bindings}))):
            raise ValueError("experiment inputs need sorted unique domain binding keys")
        for row in self.bindings:
            row.__post_init__()


@dataclass(frozen=True, slots=True)
class ExperimentFileInputBinding(CanonicalRecord):
    """Original file bytes, independent of their domain interpretation."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/experiment-inputs/file-binding"
    key: str
    identity: ArtifactIdentity
    record_version: str
    relative_path: str
    maximum_bytes: int

    def __post_init__(self):
        validate_stable_id(self.key)
        if type(self.identity) is not ArtifactIdentity:
            raise TypeError("experiment file needs its exact original artifact identity")
        self.identity.__post_init__()
        if type(self.identity.size_bytes) is not int or self.identity.size_bytes < 0:
            raise ValueError("experiment file identity needs an exact nonnegative byte count")
        validate_semantic_version(self.record_version)
        validate_relative_locator(self.relative_path)
        if (type(self.maximum_bytes) is not int or self.maximum_bytes < 1
                or self.identity.size_bytes > self.maximum_bytes):
            raise ValueError("experiment file needs an explicit sufficient positive byte bound")


@dataclass(frozen=True, slots=True)
class ExperimentFileInputSelection(CanonicalRecord):
    """Mixed canonical records and original files; v1 selections stay exact."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/experiment-inputs/file-selection"
    selection_id: str
    protocol_id: str
    bindings: tuple[ExperimentInputBinding, ...]
    files: tuple[ExperimentFileInputBinding, ...]

    def __post_init__(self):
        ExperimentInputSelection(self.selection_id, self.protocol_id, self.bindings)
        if (type(self.files) is not tuple
                or any(type(row) is not ExperimentFileInputBinding for row in self.files)
                or tuple(row.key for row in self.files) != tuple(sorted({row.key for row in self.files}))
                or {row.key for row in self.files} & {row.key for row in self.bindings}):
            raise ValueError("experiment files need sorted unique disjoint input binding keys")
        for row in self.files:
            row.__post_init__()
