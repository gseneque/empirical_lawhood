# SPDX-License-Identifier: MPL-2.0
"""Original battery columns through the shared bounded named-array reader.

The existing lossless codec owns physical decoding and receipt authentication.
This bridge reuses its completed byte sources, without another cache, temporary
population, transport or scientific interpretation. Raw nonfinite bytes remain
available; a verified dataset does not establish native or parent completion.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from empirical_lawhood.infrastructure.dataset_readers import (
    ArrayDatasetReader, AuthenticatedBlockByteSource, PhysicalFDByteSource,
)
from empirical_lawhood.kernel.datasets import ArrayDatasetManifest, ArrayDatasetMember
from empirical_lawhood.kernel.provenance import ObjectIdentity

from . import lossless_segment_arrays as codec
from . import lossless_segment_records as records
from .lossless_evidence_stream import LosslessSegmentFrame, LosslessSegmentMetadata


def _references(values):
    selected = {}
    for value in values:
        if type(value) is not ObjectIdentity:
            raise TypeError("battery dataset requires exact existing scientific/custody identities")
        previous = selected.setdefault(value.object_id, value)
        if previous != value:
            raise ValueError("battery dataset aliases differing original identities")
    return tuple(sorted(selected.values(), key=lambda row: row.object_id))


class BatteryColumnSource:
    """Fresh original C-order streams over caller-owned decoded byte handles."""

    __slots__ = ("_sources", "_sizes")

    def __init__(self, declarations, sources):
        if not isinstance(sources, Mapping) or set(sources) != {row.array_id for row in declarations}:
            raise ValueError("battery column source omits or adds an original raw array")
        if any(type(value) is not tuple or len(value) != 2
                or not all(callable(part) for part in value) for value in sources.values()):
            raise TypeError("battery column source requires existing completed chunk/range bindings")
        self._sources = MappingProxyType(dict(sources))
        self._sizes = MappingProxyType({row.array_id: row.size_bytes for row in declarations})

    def open_member(self, name):
        return self._sources[name][0]()

    def read_member_at(self, name, offset, size):
        """Reuse the existing bounded inverse range; no new cache or layout."""
        if (type(offset) is not int or type(size) is not int or offset < 0
                or not 0 <= size <= codec.CHUNK_BYTES or offset + size > self._sizes[name]):
            raise ValueError("battery source requires a bounded exact original byte range")
        return self._sources[name][1](offset, size)


@dataclass(frozen=True, slots=True)
class BatteryDatasetBridge:
    """Complete named values plus unchanged availability and original witnesses."""

    raw_index: records.RawSegmentIndex | None
    full_index: records.FullSegmentIndex | None
    reader: ArrayDatasetReader

    def member_names(self, role):
        """None, empty collection and represented columns stay distinguishable."""
        if role not in ("all_ts", "all_ys", "all_yps"):
            raise ValueError("battery dataset selects an unknown original array role")
        if self.raw_index is None:
            return None
        at = ("all_ts", "all_ys", "all_yps").index(role)
        if self.raw_index.block_counts[at] is None:
            return None
        return tuple(row.array_id for row in self.raw_index.arrays if row.role == role)

    @property
    def present_attributes(self):
        return None if self.raw_index is None else self.raw_index.present_attributes

    @property
    def block_counts(self):
        return None if self.raw_index is None else self.raw_index.block_counts


def raw_dataset_manifest(index, *, full_index=None, scientific_references=()):
    """One unchanged raw/full source census, available before decoded ingestion."""
    if type(index) is not records.RawSegmentIndex:
        raise TypeError("battery dataset requires its exact original raw index")
    index.__post_init__()
    references = [records.identity(index, "index_id"), index.decoded_subject,
        index.protocol, index.request, index.returned, *scientific_references]
    if full_index is not None:
        if type(full_index) is not records.FullSegmentIndex:
            raise TypeError("battery dataset requires its exact original full-state index")
        full_index.__post_init__()
        if (full_index.raw_index != records.identity(index, "index_id")
                or full_index.decoded_raw_subject != index.decoded_subject
                or (full_index.protocol, full_index.request, full_index.returned)
                    != (index.protocol, index.request, index.returned)):
            raise ValueError("battery dataset changes its original raw/full source association")
        references.extend((records.identity(full_index, "index_id"), full_index.decoded_subject, full_index.layout))
    members = []
    for declaration in index.arrays:
        member = ArrayDatasetMember(declaration.array_id, declaration.dtype, declaration.shape,
            declaration.raw_sha256, finite_required=False, order=declaration.order)
        if member.itemsize != declaration.itemsize:
            raise ValueError("battery dataset dtype disagrees with its actual original item size")
        members.append(member)
        references.append(declaration.identity)
    return ArrayDatasetManifest("dataset.battery.raw." + index.fingerprint(),
        tuple(sorted(members, key=lambda row: row.name)), _references(references))


def bridge_raw_segment(index, sources, *, full_index=None, scientific_references=(), transforms=None,
        maximum_chunk_bytes=codec.CHUNK_BYTES, maximum_slice_bytes):
    """Retain original values; actual leases, rather than labels, admit reads."""
    manifest = raw_dataset_manifest(index, full_index=full_index, scientific_references=scientific_references)
    if transforms is None:
        columns = BatteryColumnSource(index.arrays, sources)
        source = AuthenticatedBlockByteSource(columns, read_range=columns.read_member_at, close=lambda:None)
    else:
        source = PhysicalFDByteSource(manifest, transforms, maximum_chunk_bytes=maximum_chunk_bytes,
            maximum_cache_bytes=0)  # The original ClockMajorView owns its two bounded snapshot blocks.
    reader = ArrayDatasetReader(manifest, source, maximum_chunk_bytes=maximum_chunk_bytes,
        maximum_slice_bytes=maximum_slice_bytes)
    return BatteryDatasetBridge(index, full_index, reader)


def _metadata_references(metadata):
    if type(metadata) is not LosslessSegmentMetadata:
        raise TypeError("battery dataset requires its exact original lossless metadata")
    metadata.__post_init__()
    references = [ObjectIdentity.from_record("battery.segment-metadata." + metadata.fingerprint(), metadata),
        metadata.definition.identity, records.identity(metadata.request_receipt, "receipt_id"),
        records.identity(metadata.native_receipt, "receipt_id"), metadata.request.identity,
        records.identity(metadata.returned, "return_id")]
    for logical in metadata.native_receipt.output_logical_artifacts:
        references.append(ObjectIdentity.from_record(logical.logical_artifact_id, logical))
    for materialization in metadata.native_receipt.output_materializations:
        references.append(ObjectIdentity.from_record(materialization.materialization_id, materialization))
    return tuple(references)


def lossless_dataset_manifest(metadata):
    """Bind writer and reader to the same actual original metadata identities."""
    references = _metadata_references(metadata)
    if metadata.raw_index is not None:
        return raw_dataset_manifest(metadata.raw_index, full_index=metadata.full_index, scientific_references=references)
    return ArrayDatasetManifest("dataset.battery.absent-raw." + metadata.fingerprint(), (), _references(references))


def bridge_lossless_inputs(metadata, sources, *, transforms=None,
        maximum_chunk_bytes=codec.CHUNK_BYTES, maximum_slice_bytes):
    references = _metadata_references(metadata)
    if metadata.raw_index is not None:
        return bridge_raw_segment(metadata.raw_index, sources, full_index=metadata.full_index, transforms=transforms,
            scientific_references=references, maximum_chunk_bytes=maximum_chunk_bytes,
            maximum_slice_bytes=maximum_slice_bytes)
    manifest = lossless_dataset_manifest(metadata)
    reader = ArrayDatasetReader(manifest, BatteryColumnSource((), {}), maximum_chunk_bytes=maximum_chunk_bytes,
        maximum_slice_bytes=maximum_slice_bytes)
    return BatteryDatasetBridge(None, None, reader)


def bridge_lossless_frame(frame, *, maximum_chunk_bytes=codec.CHUNK_BYTES, maximum_slice_bytes):
    """Use an exhausted original stream frame while its caller-owned handles live."""
    if type(frame) is not LosslessSegmentFrame:
        raise TypeError("battery dataset requires the original authenticated lossless frame")
    frame.__post_init__()
    return bridge_lossless_inputs(frame.metadata, frame.sources,
        maximum_chunk_bytes=maximum_chunk_bytes, maximum_slice_bytes=maximum_slice_bytes)
