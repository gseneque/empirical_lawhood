# SPDX-License-Identifier: MPL-2.0
"""Logical named-array contracts, independent of physical packaging.

Scientific references retain their original identities. These records establish
no source eligibility, scientific units, clocks, exposure or outcome authority.
"""

from dataclasses import dataclass
from math import prod
from typing import ClassVar

from .provenance import ObjectIdentity
from .serialization import CanonicalRecord, validate_sha256, validate_stable_id


_DTYPE_BYTES = {"|b1": 1, "|i1": 1, "|u1": 1,
    **{endian + kind + str(width): width for endian in ("<", ">")
        for kind, widths in (("i", (2, 4, 8)), ("u", (2, 4, 8)), ("f", (2, 4, 8)), ("c", (8, 16)))
        for width in widths}}


@dataclass(frozen=True, slots=True)
class ArrayDatasetMember(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/datasets/array-member"
    name: str
    dtype: str
    shape: tuple[int, ...]
    sha256: str
    finite_required: bool = True
    order: str = "C"

    def __post_init__(self):
        validate_stable_id(self.name, field_name="dataset member name")
        validate_sha256(self.sha256)
        if (type(self.dtype) is not str or self.dtype not in _DTYPE_BYTES or type(self.shape) is not tuple
                or any(type(extent) is not int or extent < 0 for extent in self.shape)
                or type(self.finite_required) is not bool or self.order != "C"):
            raise ValueError("array dataset member changes its safe exact dtype, shape, C order or finite contract")

    @property
    def itemsize(self) -> int:
        return _DTYPE_BYTES[self.dtype]

    @property
    def size_bytes(self) -> int:
        return prod(self.shape) * self.itemsize

    @property
    def first_axis_extent(self) -> int:
        return self.shape[0] if self.shape else 1


@dataclass(frozen=True, slots=True)
class ArrayDatasetManifest(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/datasets/array-manifest"
    dataset_id: str
    members: tuple[ArrayDatasetMember, ...]
    scientific_references: tuple[ObjectIdentity, ...]

    def __post_init__(self):
        validate_stable_id(self.dataset_id)
        if (type(self.members) is not tuple
                or any(type(member) is not ArrayDatasetMember for member in self.members)
                or tuple(member.name for member in self.members) != tuple(sorted({member.name for member in self.members}))):
            raise ValueError("array dataset needs one complete sorted unique named member census")
        for member in self.members:
            member.__post_init__()
        if (type(self.scientific_references) is not tuple
                or any(type(reference) is not ObjectIdentity for reference in self.scientific_references)
                or tuple(reference.object_id for reference in self.scientific_references)
                != tuple(sorted({reference.object_id for reference in self.scientific_references}))):
            raise ValueError("array dataset scientific references must retain sorted unique immutable identities")
        for reference in self.scientific_references:
            reference.__post_init__()

    @property
    def identity(self) -> ObjectIdentity:
        return ObjectIdentity.from_record(self.dataset_id, self)

    @property
    def size_bytes(self) -> int:
        return sum(member.size_bytes for member in self.members)
