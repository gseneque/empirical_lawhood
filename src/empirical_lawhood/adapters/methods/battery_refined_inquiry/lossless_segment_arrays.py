# SPDX-License-Identifier: MPL-2.0
"""Battery raw-array storage with complete, lossless, bounded decode witnesses.

This domain format removes text expansion without changing scientific values.
Every source byte, including signed zero and nonfinite payloads, is retained.
Consumers must exhaust the complete stream before publishing an assessment.
The byte chunk size bounds working memory, never the scientific population.
Native entry, native custody and numerical interpretation are separate owners.
"""

import base64
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from hashlib import sha256
import math
from typing import ClassVar
import zlib

from empirical_lawhood.kernel.decoding import decode_canonical_record
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord, canonical_json_bytes, validate_sha256, validate_stable_id,
)

CHUNK_BYTES = 64 * 1024
MAX_ENCODED_CHUNK_BYTES = CHUNK_BYTES + 1024
SCOPE = "LOSSLESS_ACTUAL_RAW_BYTES;NOT_NUMERICAL_INTERPRETATION_OR_QUALIFICATION"


@dataclass(frozen=True, slots=True)
class LosslessArrayDeclaration(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/lossless-array-declaration"
    array_id: str
    source: ObjectIdentity
    role: str
    block_index: int
    dtype: str
    shape: tuple[int, ...]
    itemsize: int
    raw_sha256: str
    layout: ObjectIdentity | None = None
    order: str = "C"
    encoding: str = "INDEPENDENT_GZIP6_CHUNKS;BASE64;EXACT_C_ORDER_BYTES"
    row_semantics: str = "RAW_ONLY;NUMERICAL_UNITS_SCALES_AND_AVAILABILITY_REQUIRE_INDEPENDENT_LAYOUT_JOIN"
    scope: str = SCOPE

    def __post_init__(self):
        validate_stable_id(self.array_id)
        validate_sha256(self.raw_sha256)
        if (type(self.source) is not ObjectIdentity or type(self.role) is not str
                or self.role not in {"all_ts", "all_ys", "all_yps"}
                or type(self.block_index) is not int or self.block_index < 0
                or type(self.dtype) is not str or not self.dtype
                or type(self.shape) is not tuple
                or any(type(size) is not int or size < 0 for size in self.shape)
                or type(self.itemsize) is not int or self.itemsize < 1
                or self.layout is not None and type(self.layout) is not ObjectIdentity
                or self.order != "C" or self.scope != SCOPE
                or self.encoding != "INDEPENDENT_GZIP6_CHUNKS;BASE64;EXACT_C_ORDER_BYTES"
                or self.row_semantics != "RAW_ONLY;NUMERICAL_UNITS_SCALES_AND_AVAILABILITY_REQUIRE_INDEPENDENT_LAYOUT_JOIN"):
            raise ValueError("lossless battery array changes exact representation, source or claim")
        if self.size_bytes == 0 and self.raw_sha256 != sha256(b"").hexdigest():
            raise ValueError("empty raw array changes its complete source hash")

    @property
    def size_bytes(self):
        return math.prod(self.shape) * self.itemsize

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.array_id, self)


@dataclass(frozen=True, slots=True)
class LosslessArrayChunk(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/lossless-array-chunk"
    array: ObjectIdentity
    offset: int
    decoded_bytes: int
    decoded_sha256: str
    encoded_sha256: str
    gzip_base64: str

    def __post_init__(self):
        validate_sha256(self.decoded_sha256)
        validate_sha256(self.encoded_sha256)
        if (type(self.array) is not ObjectIdentity or self.array.object_schema != LosslessArrayDeclaration.SCHEMA
                or type(self.offset) is not int or self.offset < 0
                or type(self.decoded_bytes) is not int or not 0 < self.decoded_bytes <= CHUNK_BYTES
                or type(self.gzip_base64) is not str
                or len(self.gzip_base64) > ((MAX_ENCODED_CHUNK_BYTES + 2) // 3) * 4):
            raise ValueError("lossless battery chunk changes its exact bounded census")
        try:
            encoded = base64.b64decode(self.gzip_base64, validate=True)
        except ValueError as error:
            raise ValueError("lossless battery chunk has invalid base64 bytes") from error
        if (base64.b64encode(encoded).decode() != self.gzip_base64
                or len(encoded) > MAX_ENCODED_CHUNK_BYTES
                or sha256(encoded).hexdigest() != self.encoded_sha256):
            raise ValueError("lossless battery chunk changes original encoded bytes")

    def decode(self):
        self.__post_init__()
        encoded = base64.b64decode(self.gzip_base64, validate=True)
        decoder = zlib.decompressobj(wbits=31)
        try:
            raw = decoder.decompress(encoded, self.decoded_bytes + 1)
        except zlib.error as error:
            raise ValueError("lossless battery chunk cannot decode exact gzip bytes") from error
        if (len(raw) != self.decoded_bytes or not decoder.eof
                or decoder.unconsumed_tail or decoder.unused_data
                or sha256(raw).hexdigest() != self.decoded_sha256):
            raise ValueError("lossless battery chunk changes decoded bytes or adds trailing members")
        return raw


@dataclass(frozen=True, slots=True)
class LosslessArrayFrame(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/lossless-array-stream"
    sequence: int
    declaration: LosslessArrayDeclaration | None
    chunk: LosslessArrayChunk | None
    complete_sha256: str | None
    complete_bytes: int | None

    def __post_init__(self):
        if type(self.sequence) is not int or self.sequence < 0:
            raise ValueError("lossless battery stream changes exact sequence")
        header = self.declaration is not None
        data = self.chunk is not None
        final = self.complete_sha256 is not None or self.complete_bytes is not None
        if sum((header, data, final)) != 1 or header != (self.sequence == 0):
            raise ValueError("lossless battery stream omits or overlaps header/data/complete census")
        if header:
            if type(self.declaration) is not LosslessArrayDeclaration:
                raise ValueError("lossless battery stream requires its exact declaration")
            self.declaration.__post_init__()
        if data:
            if type(self.chunk) is not LosslessArrayChunk:
                raise ValueError("lossless battery stream substitutes a typed chunk")
            self.chunk.__post_init__()
        if final:
            validate_sha256(self.complete_sha256)
            if type(self.complete_bytes) is not int or self.complete_bytes < 0:
                raise ValueError("lossless battery stream changes complete decoded denominator")

    def canonical_bytes(self):
        return canonical_json_bytes({"schema": self.SCHEMA, "version": self.VERSION,
            "sequence": self.sequence, "value": {name: getattr(self, name) for name in
                ("declaration", "chunk", "complete_sha256", "complete_bytes")}})


def _frame(sequence, *, declaration=None, chunk=None, digest=None, size=None):
    return LosslessArrayFrame(sequence, declaration, chunk, digest, size)


def _immutable_json(value):
    if isinstance(value, list):
        return tuple(_immutable_json(item) for item in value)
    if isinstance(value, dict):
        return {key: _immutable_json(item) for key, item in value.items()}
    return value


def encode_array(declaration: LosslessArrayDeclaration, source_chunks: Iterable[bytes]) -> Iterator[bytes]:
    """Emit all original bytes through the existing JSONL profile, without thinning."""
    declaration.__post_init__()
    yield _frame(0, declaration=declaration).canonical_bytes()
    pending = bytearray()
    digest, size, sequence = sha256(), 0, 1

    def encoded(raw, at):
        compressor = zlib.compressobj(level=6, wbits=31)
        compressed = compressor.compress(raw) + compressor.flush()
        return LosslessArrayChunk(declaration.identity, at, len(raw), sha256(raw).hexdigest(),
            sha256(compressed).hexdigest(), base64.b64encode(compressed).decode())

    for block in source_chunks:
        if type(block) is not bytes or len(block) > CHUNK_BYTES:
            raise ValueError("lossless battery source must use bounded original byte chunks")
        position = 0
        while position < len(block):
            length = min(CHUNK_BYTES - len(pending), len(block) - position)
            pending.extend(block[position:position + length])
            position += length
            if len(pending) == CHUNK_BYTES:
                raw = bytes(pending)
                pending.clear()
                if size + len(raw) > declaration.size_bytes:
                    raise ValueError("lossless battery source exceeds complete declared axes")
                yield _frame(sequence, chunk=encoded(raw, size)).canonical_bytes()
                digest.update(raw)
                size += len(raw)
                sequence += 1
    if pending:
        raw = bytes(pending)
        if size + len(raw) > declaration.size_bytes:
            raise ValueError("lossless battery source exceeds complete declared axes")
        yield _frame(sequence, chunk=encoded(raw, size)).canonical_bytes()
        digest.update(raw)
        size += len(raw)
        sequence += 1
    if size != declaration.size_bytes or digest.hexdigest() != declaration.raw_sha256:
        raise ValueError("lossless battery source omits or changes complete original array bytes")
    yield _frame(sequence, digest=digest.hexdigest(), size=size).canonical_bytes()


def decode_array(lines: Iterable[bytes], expected: LosslessArrayDeclaration) -> Iterator[bytes]:
    """Independent bounded consumer; exhaustion validates the full represented population."""
    import json

    expected.__post_init__()
    size, digest, complete, count = 0, sha256(), False, 0
    for count, line in enumerate(lines, start=1):
        if type(line) is not bytes or len(line) > 2 * CHUNK_BYTES:
            raise ValueError("lossless battery stream changes its bounded line framing")
        value = json.loads(line)
        if (canonical_json_bytes(_immutable_json(value)) != line
                or set(value) != {"schema", "version", "sequence", "value"}
                or value["schema"] != LosslessArrayFrame.SCHEMA
                or value["version"] != LosslessArrayFrame.VERSION or value["sequence"] != count - 1
                or complete):
            raise ValueError("lossless battery stream substitutes canonical sequence or adds data after completion")
        # Sequence is a transport field. Decode the unchanged canonical owner
        # fields through the typed record contract, then compare its exact line.
        envelope = {"schema": value["schema"], "version": value["version"],
            "value": {"sequence": value["sequence"], **value["value"]}}
        frame = decode_canonical_record(envelope, LosslessArrayFrame)
        if frame.canonical_bytes() != line:
            raise ValueError("lossless battery stream changes typed canonical frame bytes")
        if count == 1:
            if frame.declaration != expected:
                raise ValueError("lossless battery stream changes original source, shape, dtype, order or layout")
        elif frame.chunk is not None:
            chunk = frame.chunk
            if (chunk.array != expected.identity or chunk.offset != size
                    or size + chunk.decoded_bytes > expected.size_bytes):
                raise ValueError("lossless battery stream omits, reorders or adds original array bytes")
            raw = chunk.decode()
            digest.update(raw)
            size += len(raw)
            yield raw
        else:
            if (frame.complete_bytes != size or frame.complete_sha256 != digest.hexdigest()
                    or size != expected.size_bytes or digest.hexdigest() != expected.raw_sha256):
                raise ValueError("lossless battery complete array hash or denominator disagrees")
            complete = True
    if count < 2 or not complete:
        raise ValueError("lossless battery stream omits its complete population witness")
