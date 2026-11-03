# SPDX-License-Identifier: MPL-2.0
"""Battery storage records and exact, lazy decoded scientific subjects.

Physical encoded records have their own schemas. A decoded historical-format
subject hash is an equivalence witness, never a manufactured legacy receipt.
Decoded arrays use caller-selected temporary files and bounded read caches;
the complete encoded footer must authenticate before scientific interpretation.
"""

from collections import OrderedDict
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from hashlib import sha256
from io import UnsupportedOperation
import json
import math
import struct
from typing import ClassVar

from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.datasets import ArrayDatasetManifest, ArrayDatasetMember
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, canonical_json_bytes, validate_stable_id
from empirical_lawhood.infrastructure.dataset_readers import ArrayTransformWriter, DatasetFDMember
from . import lossless_segment_arrays as codec
from . import preparation_contracts as pc
from . import segmented_native as native


def identity(record, field):
    return ObjectIdentity.from_record(getattr(record, field), record)


@dataclass(frozen=True, slots=True)
class RawSegmentIndex(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/lossless-raw-segment-index"
    index_id: str
    decoded_subject: ObjectIdentity
    protocol: ObjectIdentity
    request: ObjectIdentity
    returned: ObjectIdentity
    present_attributes: tuple[str, ...]
    # None and an empty array collection are distinct actual observations.
    block_counts: tuple[int | None, int | None, int | None]
    arrays: tuple[codec.LosslessArrayDeclaration, ...]
    scope: str = "COMPLETE_ACTUAL_RAW_REPRESENTATION;DECODED_SUBJECT_EQUIVALENCE;NO_SCIENTIFIC_QUALIFICATION"

    def __post_init__(self):
        validate_stable_id(self.index_id)
        if (self.decoded_subject.object_schema != native.RawReturnedSegment.SCHEMA
                or self.protocol.object_schema != pc.PreparationProtocol.SCHEMA
                or self.request.object_schema != native.SegmentRequest.SCHEMA
                or self.returned.object_schema != native.SegmentReturn.SCHEMA
                or self.present_attributes != tuple(sorted(set(self.present_attributes)))
                or set(self.present_attributes) - {"all_ts", "all_ys", "all_yps"}
                or len(self.block_counts) != 3
                or any(n is not None and (type(n) is not int or n < 0) for n in self.block_counts)
                or self.scope != "COMPLETE_ACTUAL_RAW_REPRESENTATION;DECODED_SUBJECT_EQUIVALENCE;NO_SCIENTIFIC_QUALIFICATION"):
            raise ValueError("lossless raw index changes actual availability, source or scientific scope")
        expected = []
        for role, count in zip(("all_ts", "all_ys", "all_yps"), self.block_counts, strict=True):
            if role not in self.present_attributes and count is not None:
                raise ValueError("lossless raw index invents an absent attribute")
            expected.extend((role, at) for at in range(count or 0))
        if tuple((row.role, row.block_index) for row in self.arrays) != tuple(expected):
            raise ValueError("lossless raw index omits or reorders actual array blocks")
        if len({row.array_id for row in self.arrays}) != len(self.arrays):
            raise ValueError("lossless raw index aliases distinct original arrays")
        for row in self.arrays:
            if type(row) is not codec.LosslessArrayDeclaration or row.source != self.decoded_subject or row.layout is not None:
                raise ValueError("lossless raw index substitutes original array source or claims a layout")
            row.__post_init__()


@dataclass(frozen=True, slots=True)
class FullSegmentIndex(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/lossless-full-segment-index"
    index_id: str
    decoded_subject: ObjectIdentity
    protocol: ObjectIdentity
    layout: ObjectIdentity
    request: ObjectIdentity
    returned: ObjectIdentity
    raw_index: ObjectIdentity
    decoded_raw_subject: ObjectIdentity
    state_rows: tuple[int, ...]
    returned_model_expression_sha256: tuple[str, ...]
    returned_inputs_json: str
    actual_termination: str
    interpretation: str = "COMPLETE_C_ORDER_FINITE_BINARY64;EXACT_FLOAT_HEX_SUBJECT;NO_ACCURACY_CLAIM"

    def __post_init__(self):
        from empirical_lawhood.kernel.serialization import validate_sha256
        validate_stable_id(self.index_id)
        if (self.decoded_subject.object_schema != native.FullStateSegment.SCHEMA
                or self.protocol.object_schema != pc.PreparationProtocol.SCHEMA
                or self.layout.object_schema != pc.ProcessedInitialStateLayout.SCHEMA
                or self.request.object_schema != native.SegmentRequest.SCHEMA
                or self.returned.object_schema != native.SegmentReturn.SCHEMA
                or self.raw_index.object_schema != RawSegmentIndex.SCHEMA
                or self.decoded_raw_subject.object_schema != native.RawReturnedSegment.SCHEMA
                or not self.state_rows or any(type(n) is not int or n < 1 for n in self.state_rows)
                or len(set(self.state_rows)) != 1
                or len(self.returned_model_expression_sha256) != len(self.state_rows)
                or not self.actual_termination
                or self.interpretation != "COMPLETE_C_ORDER_FINITE_BINARY64;EXACT_FLOAT_HEX_SUBJECT;NO_ACCURACY_CLAIM"):
            raise ValueError("lossless full index changes complete layout, source, rows or interpretation")
        for digest in self.returned_model_expression_sha256:
            validate_sha256(digest)
        native.passive._validate_primitive_json(self.returned_inputs_json)


def _atom(value):
    return canonical_json_bytes(value)[:-1]


@dataclass(frozen=True)
class _Fragments:
    factory: object


def _value(value):
    if type(value) is _Fragments:
        yield from value.factory()
    else:
        yield _atom(value)


def _array(values):
    yield b"["
    for at, value in enumerate(values):
        if at:
            yield b"," 
        yield from _value(value)
    yield b"]"


def _record(schema, values, *, newline=False):
    yield b'{"schema":' + _atom(schema) + b',"value":{'
    for at, name in enumerate(sorted(values)):
        if at:
            yield b"," 
        yield _atom(name) + b":"
        yield from _value(values[name])
    yield b'},"version":"1.0.0"}' + (b"\n" if newline else b"")


def digest_fragments(fragments):
    digest = sha256()
    for block in fragments:
        digest.update(block)
    return digest.hexdigest()


def raw_subject_fragments(raw_id, protocol, request, returned, present, counts, arrays):
    """Exact old canonical bytes, composed without constructing bytes_hex."""
    def collection(role, count):
        if count is None:
            return None
        def fragments():
            records = []
            for declaration, source in arrays:
                if declaration.role != role:
                    continue
                def record(d=declaration, s=source):
                    def hex_bytes():
                        yield b'"'
                        for block in s():
                            yield block.hex().encode()
                        yield b'"'
                    yield from _record(native.RawReturnedArray.SCHEMA, {
                        "dtype": d.dtype, "shape": d.shape, "itemsize": d.itemsize,
                        "order": "C", "bytes_hex": _Fragments(hex_bytes)})
                records.append(_Fragments(record))
            yield from _array(records)
        return _Fragments(fragments)
    yield from _record(native.RawReturnedSegment.SCHEMA, {"raw_id": raw_id, "protocol": protocol,
        "request": request, "returned": returned, "present_attributes": present,
        **{field: collection(role, count) for field, role, count in zip(
            ("clock_blocks", "state_blocks", "derivative_blocks"), ("all_ts", "all_ys", "all_yps"), counts, strict=True)}}, newline=True)


def full_subject_fragments(index, blocks):
    def block_values():
        for block in blocks:
            def values(b=block):
                yield from _record(native.FullStateBlock.SCHEMA, {"clock_binary64": b.clock_binary64,
                    "state_rows": b.state_rows,
                    "state_binary64": _Fragments(lambda: _array(b.state_binary64)),
                    "derivative_binary64": None if b.derivative_binary64 is None else _Fragments(lambda: _array(b.derivative_binary64))})
            yield _Fragments(values)
    yield from _record(native.FullStateSegment.SCHEMA, {"segment_id": index.decoded_subject.object_id,
        "protocol": index.protocol, "layout": index.layout, "request": index.request, "returned": index.returned,
        "raw_return": index.decoded_raw_subject, "blocks": _Fragments(lambda: _array(block_values())),
        "returned_model_expression_sha256": index.returned_model_expression_sha256,
        "returned_inputs_json": index.returned_inputs_json, "actual_termination": index.actual_termination}, newline=True)


class Binary64View(Sequence):
    """Exact float.hex values from a bounded cache over a completed byte source."""
    def __init__(self, declaration, read_at):
        if declaration.dtype not in {"<f8", ">f8"} or declaration.itemsize != 8:
            raise ValueError("lossless interpretation requires actual binary64 dtype and item size")
        self.declaration, self.read_at = declaration, read_at
        self.length = math.prod(declaration.shape)
        self.cache_offset, self.cache = -1, b""

    def __len__(self):
        return self.length

    def __getitem__(self, index):
        if isinstance(index, slice):
            return tuple(self[at] for at in range(*index.indices(self.length)))
        if type(index) is not int:
            raise TypeError("binary64 view needs an exact index")
        if index < 0:
            index += self.length
        if not 0 <= index < self.length:
            raise IndexError(index)
        byte = index * 8
        offset = byte // codec.CHUNK_BYTES * codec.CHUNK_BYTES
        if self.cache_offset != offset:
            self.cache = self.read_at(offset, min(codec.CHUNK_BYTES, self.declaration.size_bytes - offset))
            self.cache_offset = offset
        if len(self.cache) != min(codec.CHUNK_BYTES, self.declaration.size_bytes - offset):
            raise ValueError("lossless completed source lost exact decoded bytes")
        value = struct.unpack_from(("<" if self.declaration.dtype == "<f8" else ">") + "d", self.cache, byte - offset)[0]
        if not math.isfinite(value):
            raise ValueError("actual raw nonfinite bytes cannot become a finite scientific state")
        return value.hex()


class ClockMajorView(Binary64View):
    """Same logical C-order values over a temporary clock-major population.

    The interval algorithm visits rows at two adjacent clocks. Two 64KiB
    cached physical chunks avoid rereading a complete C-order array per query.
    This scratch layout changes no scientific source/order or primary bytes.
    """
    def __init__(self, declaration, handle, *, dataset_reader=None):
        super().__init__(declaration, lambda offset, size: b"")
        self.handle = handle
        self.dataset_reader = dataset_reader
        self.rows, self.width = declaration.shape
        self.cached = OrderedDict()

    def __getitem__(self, index):
        if isinstance(index, slice):
            return tuple(self[at] for at in range(*index.indices(self.length)))
        if type(index) is not int:
            raise TypeError("clock-major view needs an exact logical C-order index")
        if index < 0:
            index += self.length
        if not 0 <= index < self.length:
            raise IndexError(index)
        row, clock = divmod(index, self.width)
        byte = (clock * self.rows + row) * 8
        offset = byte // codec.CHUNK_BYTES * codec.CHUNK_BYTES
        block = self.cached.get(offset)
        if block is None:
            size = min(codec.CHUNK_BYTES, self.declaration.size_bytes - offset)
            if self.dataset_reader is None:
                self.handle.seek(offset)
                block = self.handle.read(size)
            else:
                block = self.dataset_reader.read_permuted_member_bytes(
                    self.declaration.array_id, (1, 0), offset, offset + size)
            if len(block) != min(codec.CHUNK_BYTES, self.declaration.size_bytes - offset):
                raise ValueError("clock-major scratch loses complete original decoded bytes")
            self.cached[offset] = block
            if len(self.cached) > 2:
                self.cached.popitem(last=False)
        self.cached.move_to_end(offset)
        value = struct.unpack_from(("<" if self.declaration.dtype == "<f8" else ">") + "d", block, byte - offset)[0]
        if not math.isfinite(value):
            raise ValueError("clock-major scratch invents nonfinite scientific values")
        return value.hex()


class _ClockMajorWorkingSource:
    """One working population, with exact inverse C-order bounded byte views.

    The encoded primary remains unchanged. Decode writes bytes directly to the
    selected scratch layout; canonical subject authentication sees the original
    C-order bytes through ``chunks``/``read_at``. No floating operation occurs.
    """
    def __init__(self, declaration, handle, *, transform_writer=None):
        self.declaration, self.handle = declaration, handle
        self.rows, self.width = declaration.shape
        self.pending = bytearray()
        self.received = self.written = 0
        self.transform_writer = transform_writer
        self.handle.truncate(declaration.size_bytes)

    def _tile_size(self):
        row_bytes = self.width * 8
        if row_bytes > codec.CHUNK_BYTES:
            return min(codec.CHUNK_BYTES, row_bytes - self.written % row_bytes)
        return min(32, max(1, codec.CHUNK_BYTES // row_bytes)) * row_bytes

    def _write_tile(self, raw):
        first_row, first_clock = divmod(self.written // 8, self.width)
        if first_clock or len(raw) < self.width * 8:
            # A wide row is split into bounded pieces. Each represented byte
            # is still written once, even when a complete row exceeds a tile.
            for clock in range(len(raw) // 8):
                self.handle.seek(((first_clock + clock) * self.rows + first_row) * 8)
                if self.handle.write(raw[clock * 8:(clock + 1) * 8]) != 8:
                    raise ValueError("clock-major working population lost decoded bytes")
        else:
            # Strided buffer copies move complete eight-byte elements without
            # unpacking, conversion or floating arithmetic, including either
            # source endianness and all IEEE payload bits.
            elements = memoryview(raw).cast("Q")
            for clock in range(self.width):
                part = elements[clock::self.width].tobytes()
                self.handle.seek((clock * self.rows + first_row) * 8)
                if self.handle.write(part) != len(part):
                    raise ValueError("clock-major working population lost decoded byte tile")
        self.written += len(raw)

    def write(self, raw):
        if type(raw) is not bytes or len(raw) > codec.CHUNK_BYTES:
            raise ValueError("clock-major decode requires bounded original byte chunks")
        self.received += len(raw)
        if self.received > self.declaration.size_bytes:
            raise ValueError("clock-major decode exceeds the complete declared population")
        if self.transform_writer is not None:
            self.transform_writer.write(raw)
            self.written += len(raw)
            return
        self.pending.extend(raw)
        while len(self.pending) >= self._tile_size():
            size = self._tile_size()
            tile = bytes(self.pending[:size])
            del self.pending[:size]
            self._write_tile(tile)

    def finish(self):
        if self.received != self.declaration.size_bytes or len(self.pending) % 8:
            raise ValueError("clock-major decode omits complete original bytes")
        if self.pending:
            self._write_tile(bytes(self.pending))
            self.pending.clear()
        self.handle.flush()
        if self.written != self.declaration.size_bytes or self.handle.seek(0, 2) != self.written:
            raise ValueError("clock-major working population changes complete byte size")

    def read_at(self, offset, size):
        if (type(offset) is not int or type(size) is not int or offset < 0
                or not 0 <= size <= codec.CHUNK_BYTES
                or offset + size > self.declaration.size_bytes):
            raise ValueError("clock-major inverse view changes bounded original byte range")
        if not size:
            return b""
        first, last = offset // 8, (offset + size - 1) // 8
        first_row, first_clock = divmod(first, self.width)
        last_row, last_clock = divmod(last, self.width)
        # Only the first/last partial elements are padded locally. The tile
        # is bounded by CHUNK_BYTES + 8; returned bytes retain the exact range.
        output = bytearray((last - first + 1) * 8)
        elements = memoryview(output).cast("Q")
        clocks = range(first_clock, last_clock + 1) if first_row == last_row else range(self.width)
        for clock in clocks:
            low = first_row + (clock < first_clock)
            high = last_row - (clock > last_clock)
            if low > high:
                continue
            self.handle.seek((clock * self.rows + low) * 8)
            part = self.handle.read((high - low + 1) * 8)
            if len(part) != (high - low + 1) * 8:
                raise ValueError("clock-major inverse view loses original decoded bytes")
            start, end = low * self.width + clock - first, high * self.width + clock - first + 1
            elements[start:end:self.width] = memoryview(part).cast("Q")
        start = offset % 8
        return bytes(output[start:start + size])

    def chunks(self):
        for offset in range(0, self.declaration.size_bytes, codec.CHUNK_BYTES):
            yield self.read_at(offset, min(codec.CHUNK_BYTES, self.declaration.size_bytes - offset))


def _clock_major(declaration, source, temporary_file):
    """Lossless byte transpose with one bounded tile, no numerical operation."""
    rows, width = declaration.shape
    target = temporary_file()
    # Tile size bounds copying memory, not state/clock dimensions. Each row
    # slice and each transposed tile remain at most 64KiB.
    row_tile, clock_tile = 32, 128
    try:
        for first_row in range(0, rows, row_tile):
            count_rows = min(row_tile, rows - first_row)
            for first_clock in range(0, width, clock_tile):
                count_clocks = min(clock_tile, width - first_clock)
                tile = tuple(source((row * width + first_clock) * 8, count_clocks * 8)
                    for row in range(first_row, first_row + count_rows))
                if any(len(part) != count_clocks * 8 for part in tile):
                    raise ValueError("clock-major scratch omits original byte tile")
                for clock in range(count_clocks):
                    part = b"".join(row[clock * 8:(clock + 1) * 8] for row in tile)
                    target.seek(((first_clock + clock) * rows + first_row) * 8)
                    target.write(part)
                    target.seek(((first_clock + clock) * rows + first_row) * 8)
                    if target.read(count_rows * 8) != part:
                        raise ValueError("clock-major scratch changes original represented byte tile")
        target.flush()
        if target.seek(0, 2) != declaration.size_bytes:
            raise ValueError("clock-major scratch omits complete original array population")
        # Every original tile has been copied and read back byte-identically.
        # The original source's complete SHA/footer was authenticated before
        # this derivation; no tolerant equality or numerical conversion occurs.
        return target
    except BaseException:
        target.close()
        raise


@dataclass(frozen=True)
class DecodedFullBlock:
    clock_binary64: tuple[str, ...]
    state_rows: int
    state_binary64: Binary64View
    derivative_binary64: Binary64View | None


class DecodedFullSegment:
    """Transient scientific view; receipt authority belongs to its physical index."""
    SCHEMA, VERSION = native.FullStateSegment.SCHEMA, native.FullStateSegment.VERSION
    def __init__(self, index, raw_index, sources, *, temporary_file=None, dataset_reader=None):
        index.__post_init__()
        raw_index.__post_init__()
        if (index.raw_index != identity(raw_index, "index_id") or index.decoded_raw_subject != raw_index.decoded_subject
                or (index.protocol, index.request, index.returned) != (raw_index.protocol, raw_index.request, raw_index.returned)):
            raise ValueError("lossless interpretation substitutes its authentic raw source index")
        self.index = index
        self.segment_id, self.protocol, self.layout = index.decoded_subject.object_id, index.protocol, index.layout
        self.request, self.returned, self.raw_return = index.request, index.returned, index.decoded_raw_subject
        self.returned_model_expression_sha256 = index.returned_model_expression_sha256
        self.returned_inputs_json, self.actual_termination = index.returned_inputs_json, index.actual_termination
        counts = raw_index.block_counts
        if counts[0] != counts[1] or counts[0] != len(index.state_rows) or counts[2] not in (None, 0, counts[0]):
            raise ValueError("lossless full interpretation changes complete original array availability")
        by_key = {(row.role, row.block_index): row for row in raw_index.arrays}
        blocks = []
        for at, rows in enumerate(index.state_rows):
            clock = by_key[("all_ts", at)]
            state = by_key[("all_ys", at)]
            if len(clock.shape) != 1 or state.shape != (rows, clock.shape[0]) or not clock.shape[0]:
                raise ValueError("lossless full interpretation changes original axes or row ordering")
            clocks = tuple(Binary64View(clock, sources[clock.array_id][1]))
            if any(a >= b for a, b in zip(map(float.fromhex, clocks), map(float.fromhex, clocks[1:]))):
                raise ValueError("lossless full interpretation changes strict native clock order")
            derivative = None
            if counts[2]:
                d = by_key[("all_yps", at)]
                if d.shape != state.shape:
                    raise ValueError("lossless derivative omits the complete state/clock denominator")
                derivative = Binary64View(d, sources[d.array_id][1])
            blocks.append(DecodedFullBlock(clocks, rows, Binary64View(state, sources[state.array_id][1]), derivative))
        self.blocks = tuple(blocks)
        # Exhaust every represented component before exposing an equivalence
        # witness. This also refuses nonfinite interpretation without deleting
        # the independently authenticated raw bytes.
        if digest_fragments(full_subject_fragments(index, self.blocks)) != index.decoded_subject.object_fingerprint:
            raise ValueError("lossless full interpretation changes exact old canonical scientific subject bytes")
        self.scratch_handles = []
        if temporary_file is not None:
            interpreted = []
            try:
                for at, block in enumerate(self.blocks):
                    state = by_key[("all_ys", at)]
                    state_source = getattr(sources[state.array_id][1], "__self__", None)
                    if isinstance(state_source, _ClockMajorWorkingSource):
                        state_file = state_source.handle
                    else:
                        state_file = _clock_major(state, sources[state.array_id][1], temporary_file)
                        self.scratch_handles.append(state_file)
                    derivative = None
                    if block.derivative_binary64 is not None:
                        d = by_key[("all_yps", at)]
                        derivative_source = getattr(sources[d.array_id][1], "__self__", None)
                        if isinstance(derivative_source, _ClockMajorWorkingSource):
                            derivative_file = derivative_source.handle
                        else:
                            derivative_file = _clock_major(d, sources[d.array_id][1], temporary_file)
                            self.scratch_handles.append(derivative_file)
                        derivative = ClockMajorView(d, derivative_file, dataset_reader=dataset_reader)
                    interpreted.append(DecodedFullBlock(block.clock_binary64, block.state_rows,
                        ClockMajorView(state, state_file, dataset_reader=dataset_reader), derivative))
                self.blocks = tuple(interpreted)
            except BaseException:
                for handle in self.scratch_handles:
                    handle.close()
                raise

    def fingerprint(self):
        return self.index.decoded_subject.object_fingerprint

    def __post_init__(self):
        self.index.__post_init__()


@dataclass(frozen=True, slots=True)
class RawSegmentStreamLine(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/lossless-raw-segment-stream"
    sequence: int
    index: RawSegmentIndex | None
    array_index: int | None
    array_line: str | None
    complete_arrays: int | None
    decoded_subject: ObjectIdentity | None

    def __post_init__(self):
        if type(self.sequence) is not int or self.sequence < 0:
            raise ValueError("lossless segment transport changes exact sequence")
        header, data, final = self.index is not None, self.array_line is not None, self.complete_arrays is not None
        if sum((header, data, final)) != 1 or header != (self.sequence == 0):
            raise ValueError("lossless segment transport omits or overlaps its complete census")
        if header:
            self.index.__post_init__()
        if data and (type(self.array_index) is not int or self.array_index < 0 or len(self.array_line.encode()) > 2 * codec.CHUNK_BYTES):
            raise ValueError("lossless segment transport changes bounded array framing")
        if (not data and self.array_index is not None or not final and self.decoded_subject is not None
                or final and (type(self.complete_arrays) is not int or self.complete_arrays < 0 or self.decoded_subject is None)):
            raise ValueError("lossless segment transport changes final source/count denominator")

    def canonical_bytes(self):
        return canonical_json_bytes({"schema": self.SCHEMA, "version": self.VERSION, "sequence": self.sequence,
            "value": {name: getattr(self, name) for name in ("index", "array_index", "array_line", "complete_arrays", "decoded_subject")}})


def encode_raw_segment(index, sources):
    """One actual JSONL raw output, including all array headers and footers."""
    index.__post_init__()
    yield RawSegmentStreamLine(0, index, None, None, None, None).canonical_bytes()
    sequence = 1
    for at, declaration in enumerate(index.arrays):
        for line in codec.encode_array(declaration, sources[declaration.array_id][0]()):
            yield RawSegmentStreamLine(sequence, None, at, line.decode(), None, None).canonical_bytes()
            sequence += 1
    yield RawSegmentStreamLine(sequence, None, None, None, len(index.arrays), index.decoded_subject).canonical_bytes()


def _read_line(line, expected_sequence):
    from empirical_lawhood.kernel.decoding import decode_canonical_record
    if type(line) is not bytes or len(line) > 3 * codec.CHUNK_BYTES:
        raise ValueError("lossless segment transport exceeds bounded original line size")
    document = json.loads(line)
    envelope = {"schema": document.get("schema"), "version": document.get("version"),
        "value": {"sequence": document.get("sequence"), **document.get("value", {})}}
    record = decode_canonical_record(envelope, RawSegmentStreamLine)
    if record.canonical_bytes() != line or record.sequence != expected_sequence:
        raise ValueError("lossless segment transport changes canonical contiguous bytes")
    return record


def decode_raw_segment(lines: Iterator[bytes], temporary_file, *, clock_major_working=False,
        dataset_manifest=None, transform_witnesses=None):
    """Exhaust actual arrays/footer; return byte sources owned by the caller.

    ``temporary_file`` explicitly selects scratch storage. Returned handles
    close on any failure. No scientific result can precede final exhaustion.
    The opt-in layout stores complete binary64 state/derivative arrays once,
    while returned byte sources still expose their exact original C-order.
    """
    lines = iter(lines)
    header = _read_line(next(lines), 0)
    index, sources, handles = header.index, {}, []
    if index is None:
        raise ValueError("lossless raw segment omits its authentic header")
    if (dataset_manifest is None) != (transform_witnesses is None):
        raise ValueError("lossless dataset ingestion requires both its manifest and owned witness collection")
    if dataset_manifest is not None:
        if type(dataset_manifest) is not ArrayDatasetManifest or type(transform_witnesses) is not dict or transform_witnesses:
            raise TypeError("lossless dataset ingestion requires its exact manifest and empty owned witness collection")
        dataset_manifest.__post_init__()
        expected_members = tuple(sorted((ArrayDatasetMember(row.array_id, row.dtype, row.shape,
            row.raw_sha256, finite_required=False, order=row.order) for row in index.arrays), key=lambda row: row.name))
        if (dataset_manifest.members != expected_members
                or identity(index, "index_id") not in dataset_manifest.scientific_references):
            raise ValueError("lossless dataset ingestion substitutes its original source or complete array census")
    sequence = 1
    pending = None
    writers = []
    try:
        for at, declaration in enumerate(index.arrays):
            handle = temporary_file()
            handles.append(handle)
            clock_major = (clock_major_working and declaration.role in {"all_ys", "all_yps"}
                    and len(declaration.shape) == 2 and all(declaration.shape)
                    and declaration.dtype in {"<f8", ">f8"} and declaration.itemsize == 8)
            writer = None
            if dataset_manifest is not None:
                try:
                    descriptor = handle.fileno()
                except (AttributeError, UnsupportedOperation, OSError, ValueError):
                    descriptor = None  # Explicit non-FD test/backend: logical authenticated lease later.
                if descriptor is not None:
                    handle.flush()
                    handle.truncate(declaration.size_bytes)
                    writer = ArrayTransformWriter(dataset_manifest, declaration.array_id,
                        DatasetFDMember(descriptor, 0, declaration.size_bytes, declaration.size_bytes),
                        axis_order=(1, 0) if clock_major else tuple(range(len(declaration.shape))),
                        block_size_bytes=codec.CHUNK_BYTES, maximum_chunk_bytes=codec.CHUNK_BYTES)
                    writers.append(writer)
            working = _ClockMajorWorkingSource(declaration, handle, transform_writer=writer) if clock_major else None
            def inner_lines(array_index=at):
                nonlocal sequence, pending
                while True:
                    try:
                        row = pending if pending is not None else _read_line(next(lines), sequence)
                    except StopIteration as error:
                        raise ValueError("lossless segment omits its complete array/footer denominator") from error
                    pending = None
                    if row.array_index != array_index:
                        pending = row
                        return
                    sequence += 1
                    if row.array_line is None:
                        raise ValueError("lossless array frame lacks its exact selected bytes")
                    yield row.array_line.encode()
            for decoded in codec.decode_array(inner_lines(), declaration):
                if working is None:
                    if writer is None:
                        handle.write(decoded)
                    else:
                        writer.write(decoded)
                else:
                    working.write(decoded)
            handle.flush()
            if working is not None:
                working.finish()
            if writer is not None:
                transform_witnesses[declaration.array_id] = writer.finish()
            if working is not None:
                sources[declaration.array_id] = working.chunks, working.read_at
                continue
            def chunks(h=handle):
                h.seek(0)
                while block := h.read(codec.CHUNK_BYTES):
                    yield block
            def read_at(offset, size, h=handle):
                h.seek(offset)
                return h.read(size)
            sources[declaration.array_id] = chunks, read_at
        final = pending if pending is not None else _read_line(next(lines), sequence)
        if (final.sequence != sequence or final.complete_arrays != len(index.arrays)
                or final.decoded_subject != index.decoded_subject or next(lines, None) is not None):
            raise ValueError("lossless segment omits final full denominator or adds trailing output")
        subject_arrays = tuple((row, sources[row.array_id][0]) for row in index.arrays)
        expected = digest_fragments(raw_subject_fragments(index.decoded_subject.object_id, index.protocol,
            index.request, index.returned, index.present_attributes, index.block_counts, subject_arrays))
        if expected != index.decoded_subject.object_fingerprint:
            raise ValueError("lossless raw bytes change exact old canonical scientific subject")
        return index, sources, tuple(handles)
    except BaseException:
        for writer in writers:
            writer.close()
        if transform_witnesses is not None:
            for witness in transform_witnesses.values():
                witness.close()
            transform_witnesses.clear()
        for handle in handles:
            handle.close()
        raise


def decode_full_index(payload):
    record = decode_canonical_bytes(payload, FullSegmentIndex, maximum_bytes=None)
    if record.canonical_bytes() != payload:
        raise ValueError("lossless full index changes exact canonical physical bytes")
    return record
