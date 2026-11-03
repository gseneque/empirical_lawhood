# SPDX-License-Identifier: MPL-2.0
"""Named-array reader protocols and non-authoritative verification results."""

from collections.abc import Iterable
from dataclasses import dataclass
from typing import ClassVar, ContextManager, Protocol, runtime_checkable

from empirical_lawhood.kernel.datasets import ArrayDatasetManifest
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_sha256, validate_stable_id


@dataclass(frozen=True, slots=True)
class HDF5ReadLimits(CanonicalRecord):
    """Explicit physical working bounds, never scientific sample selections."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/runtime/hdf5-read-limits"
    maximum_chunk_bytes: int
    maximum_slice_bytes: int
    maximum_decoded_chunk_bytes: int
    maximum_raw_chunk_cache_bytes: int
    maximum_metadata_cache_bytes: int
    maximum_cache_slots: int
    maximum_members: int
    maximum_groups: int
    maximum_attributes: int
    maximum_attribute_bytes: int
    maximum_path_bytes: int

    def __post_init__(self):
        if any(type(getattr(self, name)) is not int or getattr(self, name) < 1 for name in self.__slots__):
            raise ValueError("HDF5 operational limits require explicit positive exact integers")


@runtime_checkable
class DatasetByteSource(Protocol):
    """Code-owned source yielding fresh bounded C-value streams for each member.

    Physical codecs authenticate archive framing, headers, shape, dtype, layout
    and exact artifact bytes before supplying the corresponding logical values.
    Source construction belongs to trusted code, never an import from config.
    """

    def open_member(self, name: str) -> Iterable[bytes]: ...


@dataclass(frozen=True, slots=True)
class DatasetVerification:
    """A completed current read, with no eligibility or scientific authority."""

    manifest: ObjectIdentity
    member_hashes: tuple[tuple[str, str], ...]
    verified_value_bytes: int

    def __post_init__(self):
        if (type(self.manifest) is not ObjectIdentity or self.manifest.object_schema != ArrayDatasetManifest.SCHEMA
                or type(self.verified_value_bytes) is not int or self.verified_value_bytes < 0
                or type(self.member_hashes) is not tuple
                or tuple(name for name, _ in self.member_hashes) != tuple(sorted({name for name, _ in self.member_hashes}))):
            raise ValueError("dataset verification needs its exact manifest and complete current member census")
        for name, digest in self.member_hashes:
            validate_stable_id(name)
            validate_sha256(digest)

    @property
    def scientific_authority(self) -> str:
        return "NONE"

    @property
    def qualification(self) -> str:
        return "NOT_ESTABLISHED"


@runtime_checkable
class ArrayDatasetReader(Protocol):
    manifest: ArrayDatasetManifest
    maximum_chunk_bytes: int
    maximum_slice_bytes: int

    def verify_complete(self) -> DatasetVerification: ...

    def iter_member_bytes(self, name: str) -> Iterable[bytes]: ...

    def read_array_slice(self, name: str, start: int, stop: int): ...

    def read_array(self, name: str): ...

    def read_member_bytes(self, name: str, start: int, stop: int) -> bytes: ...

    def read_permuted_member_bytes(self, name: str, axis_order: tuple[int, ...], start: int, stop: int) -> bytes: ...

    def read_elements(self, name: str, start: int, stop: int): ...

    def verified_session(self, *, block_size_bytes: int) -> ContextManager["ArrayDatasetReader"]: ...
