"""Bounded no-pickle array framing for public reusable matrix operands."""

from collections import OrderedDict
from collections.abc import Mapping
from contextlib import ExitStack, contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
from math import prod
from types import MappingProxyType
from threading import get_ident
import zipfile

import numpy as np
from numpy.typing import NDArray

from empirical_lawhood.runtime.execution import WorkerInputPort

from empirical_lawhood.kernel.matrix_inputs import (
    MATRIX_ARRAY_SCHEMA,
    MAXIMUM_MATRIX_ARRAY_BYTES,
    MatrixAllocation,
    MatrixArrayMember,
    SavedMatrixArrays,
)
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord


_decoded_array_scope = ContextVar('decoded_matrix_arrays', default=None)


@contextmanager
def decoded_matrix_array_scope(*, maximum_bytes=4 * MAXIMUM_MATRIX_ARRAY_BYTES):
    """Reuse immutable decoded operands within one bounded root/case consumer.

    Physical reads and current access remain with the caller. No bytes or
    values survive this scope; separate roots and invocations decode afresh.
    The bound includes both retained compressed bytes and expanded arrays.
    """
    if type(maximum_bytes) is not int or not 0 < maximum_bytes <= 4 * MAXIMUM_MATRIX_ARRAY_BYTES:
        raise ValueError('Matrix decoded lifetime requires a bounded positive byte allowance')
    state = {'owner': get_ident(), 'entries': OrderedDict(), 'bytes': 0, 'limit': maximum_bytes}
    token = _decoded_array_scope.set(state)
    try:
        yield
    finally:
        state['entries'].clear()
        state['bytes'] = 0
        state['owner'] = None
        _decoded_array_scope.reset(token)


def matrix_npz_infos(archive, members):
    """The unchanged closed NPZ member and expanded-byte contract."""
    declared = {member.name + ".npy": member for member in members}
    infos = archive.infolist()
    if (len(infos) != len(declared) or {info.filename for info in infos} != set(declared)
            or sum(info.file_size for info in infos) > MAXIMUM_MATRIX_ARRAY_BYTES + 256 * 10000):
        raise ValueError("Matrix archive members or expanded byte census differs")
    return infos, declared


def matrix_npy_header(stream, info, member):
    """Validate the existing exact axes, safe dtype and bounded NPY header."""
    return matrix_npy_layout(stream, info, dtype=member.dtype, shape=member.shape)


def matrix_npy_layout(stream, info, *, dtype, shape):
    """One physical header check for saved members and receipt-only returns."""
    expected_shape = shape
    expected_dtype = np.dtype(dtype)
    size_bytes = prod(shape) * expected_dtype.itemsize
    if expected_dtype.hasobject or info.file_size > size_bytes + 10000 or info.flag_bits & 1:
        raise ValueError("Matrix archive member is oversized or encrypted")
    version = np.lib.format.read_magic(stream)
    if version == (1, 0):
        shape, fortran, dtype = np.lib.format.read_array_header_1_0(stream, max_header_size=10000)
    elif version == (2, 0):
        shape, fortran, dtype = np.lib.format.read_array_header_2_0(stream, max_header_size=10000)
    else:
        raise ValueError("Unsupported bounded matrix NPY header revision")
    if shape != expected_shape or dtype.str != expected_dtype.str or dtype.hasobject or fortran:
        raise ValueError("Matrix NPY axes, dtype or layout differ from the manifest")
    if stream.tell() + size_bytes != info.file_size:
        raise ValueError("Matrix NPY payload length differs from the declared axes")
    return dtype


def decode_native_matrix_arrays(raw, expected):
    """Decode one bounded native return without inventing saved member hashes.

    The native receipt owner authenticates the physical bytes. The caller
    supplies its scientific member layouts and validates clocks, finite values
    and interpretation after decoding. Each member owns a single immutable
    payload buffer; no second NumPy archive decode or array copy is needed.
    """
    if (type(raw) is not bytes or not 0 < len(raw) <= MAXIMUM_MATRIX_ARRAY_BYTES
            or not 0 < len(expected) <= 256):
        raise ValueError("Native Matrix return exceeds its closed transport")
    expanded = 0
    for dtype, shape in expected.values():
        kind = np.dtype(dtype)
        if (kind.hasobject or type(shape) is not tuple
                or any(type(axis) is not int or axis < 0 for axis in shape)):
            raise ValueError("Native Matrix return changes its declared member layout")
        expanded += prod(shape) * kind.itemsize
    if expanded > MAXIMUM_MATRIX_ARRAY_BYTES:
        raise ValueError("Native Matrix return exceeds its expanded byte bound")
    try:
        with zipfile.ZipFile(BytesIO(raw)) as archive:
            infos = archive.infolist()
            if (len(infos) != len(expected)
                    or {info.filename for info in infos} != {name + ".npy" for name in expected}
                    or sum(info.file_size for info in infos) > expanded + len(expected) * 10000):
                raise ValueError("Native Matrix return changes its complete member census")
            # Validate every header before expanding any member.
            for info in infos:
                dtype, shape = expected[info.filename[:-4]]
                with archive.open(info) as stream:
                    matrix_npy_layout(stream, info, dtype=dtype, shape=shape)
            values = {}
            for info in infos:
                name = info.filename[:-4]
                dtype, shape = expected[name]
                with archive.open(info) as stream:
                    kind = matrix_npy_layout(stream, info, dtype=dtype, shape=shape)
                    payload = stream.read(prod(shape) * kind.itemsize)
                    if len(payload) != prod(shape) * kind.itemsize or stream.read(1):
                        raise ValueError("Native Matrix return truncates its exact member bytes")
                values[name] = np.frombuffer(payload, dtype=kind).reshape(shape)
        return MappingProxyType(values)
    except (OSError, zipfile.BadZipFile, EOFError) as error:
        raise ValueError("Native Matrix return cannot decode its closed archive") from error


def iter_matrix_npy_chunks(stream, member, dtype, *, maximum_chunk_bytes):
    """Original bounded exact values and finite checks, without array loading."""
    if type(maximum_chunk_bytes) is not int or maximum_chunk_bytes < dtype.itemsize:
        raise ValueError("Matrix array chunk working memory must hold a complete value")
    size = maximum_chunk_bytes // dtype.itemsize * dtype.itemsize
    remaining = member.size_bytes
    while remaining:
        payload = stream.read(min(size, remaining))
        if not payload or len(payload) % dtype.itemsize:
            raise ValueError("Matrix array chunk truncates a declared exact value")
        remaining -= len(payload)
        value = np.frombuffer(payload, dtype=dtype)
        if member.finite_required and not np.isfinite(value).all():
            raise ValueError("Matrix array required finite population differs")
        yield payload, value
    if stream.read(1):
        raise ValueError("Matrix array exceeds its declared complete population")


class _MatrixIntervalCursor:
    """Bounded seek view over the same owned immutable worker cursor."""

    def __init__(self, cursor, offset, length):
        self.cursor, self.offset, self.length, self.position = cursor, offset, length, 0
        cursor.seek(offset)

    def read(self, size=-1):
        remaining = self.length - self.position
        requested = remaining if size == -1 else min(size, remaining)
        if type(size) is not int or size < -1:
            raise ValueError("Matrix archive cursor changes its bounded read interval")
        raw = self.cursor.read(requested)
        self.position += len(raw)
        return raw

    def seek(self, offset, whence=0):
        if type(offset) is not int or type(whence) is not int or whence not in (0, 1, 2):
            raise ValueError("Matrix archive cursor changes its exact seek")
        selected = offset + (self.position if whence == 1 else self.length if whence == 2 else 0)
        if not 0 <= selected <= self.length:
            raise ValueError("Matrix archive cursor exceeds its original leaf interval")
        self.cursor.seek(self.offset + selected)
        self.position = selected
        return selected

    def tell(self):
        return self.position

    def seekable(self):
        return True

    def readable(self):
        return True


class MatrixArtifactSource:
    """Own one actually authenticated immutable byte selection, without blobs."""

    __slots__ = ("_bytes", "_held", "artifact", "_closed")

    def __setattr__(self, name, value):
        if hasattr(self, name):
            raise AttributeError("Matrix authenticated physical selection is read-only")
        object.__setattr__(self, name, value)

    def __init__(self, artifact, source, maximum_chunk_bytes):
        artifact.__post_init__()
        if type(source) is bytes:
            if len(source) != artifact.size_bytes or sha256(source).hexdigest() != artifact.sha256:
                raise ValueError("Matrix dataset bytes differ from their original artifact")
            self._bytes, self._held = source, None
        elif type(source) is WorkerInputPort:
            if ((source.artifact_id, source.payload_schema, source.media_type, source.size_bytes)
                    != (artifact.artifact_id, artifact.payload_schema, artifact.media_type, artifact.size_bytes)):
                raise ValueError("Matrix dataset port substitutes its original artifact binding")
            held = source.cursor()  # actual kernel seals, same descriptor, independent cursor
            try:
                digest, count = sha256(), 0
                while raw := held.read(maximum_chunk_bytes):
                    digest.update(raw)
                    count += len(raw)
                if count != artifact.size_bytes or digest.hexdigest() != artifact.sha256:
                    raise ValueError("Matrix dataset port changes its actual original physical bytes")
                held.seek(0)
            except BaseException:
                held.close()
                raise
            self._bytes, self._held = None, held
        else:
            raise TypeError("Matrix dataset needs immutable explicit bytes or an actual sealed worker input")
        self.artifact, self._closed = artifact, False

    @contextmanager
    def cursor(self, offset=0, length=None):
        if self._closed:
            raise ValueError("Matrix dataset physical selection is closed")
        length = self.artifact.size_bytes - offset if length is None else length
        if not 0 <= offset <= offset + length <= self.artifact.size_bytes:
            raise ValueError("Matrix dataset physical selection changes its exact retained interval")
        cursor = BytesIO(self._bytes) if self._held is None else self._held.cursor()
        try:
            yield _MatrixIntervalCursor(cursor, offset, length)
        finally:
            cursor.close()

    def close(self):
        if not self._closed:
            object.__setattr__(self, "_closed", True)
            if self._held is not None:
                self._held.close()


@dataclass(frozen=True, slots=True)
class NPZMemberSelection:
    """Code-owned physical member selection, without a scientific allocation."""
    array_artifact: ArtifactIdentity
    members: tuple[MatrixArrayMember, ...]

    def __post_init__(self):
        if (type(self.array_artifact) is not ArtifactIdentity or type(self.members) is not tuple
                or any(type(member) is not MatrixArrayMember for member in self.members)):
            raise TypeError("NPZ selection requires exact original artifact and typed member contracts")
        self.array_artifact.__post_init__()
        for member in self.members:
            member.__post_init__()
        if (not self.members or tuple(member.name for member in self.members) != tuple(sorted({member.name for member in self.members}))
                or sum(member.size_bytes for member in self.members) > MAXIMUM_MATRIX_ARRAY_BYTES
                or not 0 < self.array_artifact.size_bytes <= MAXIMUM_MATRIX_ARRAY_BYTES):
            raise ValueError("NPZ selection changes its closed original member or byte census")


class NPZMemberSource:
    """One bounded NPZ implementation; its caller owns scientific interpretation."""
    __slots__ = ("original", "physical", "offset", "maximum_chunk_bytes", "members", "maximum_open_members", "_ranges", "_closed")

    def __setattr__(self, name, value):
        if hasattr(self, name):
            raise AttributeError("Matrix original NPZ member and source bindings are read-only")
        object.__setattr__(self, name, value)

    def __init__(self, original, physical, maximum_chunk_bytes, *, offset=0, maximum_open_members=1):
        if type(original) is not NPZMemberSelection:
            raise TypeError("NPZ source requires its code-owned typed physical member selection")
        original.__post_init__()
        if (type(offset) is not int or offset < 0 or type(maximum_open_members) is not int or maximum_open_members < 1):
            raise ValueError("NPZ source requires exact interval and selected open-member bounds")
        if offset == 0 and physical.artifact != original.array_artifact:
            raise ValueError("NPZ source substitutes its actual authenticated physical artifact")
        self.original, self.physical, self.offset = original, physical, offset
        self.maximum_chunk_bytes = maximum_chunk_bytes
        self.members = MappingProxyType({value.name: value for value in original.members})
        self.maximum_open_members, self._ranges, self._closed = maximum_open_members, OrderedDict(), False
        with self._archive() as archive:
            infos, declared = matrix_npz_infos(archive, original.members)
            for info in infos:
                with archive.open(info) as stream:
                    matrix_npy_header(stream, info, declared[info.filename])

    @contextmanager
    def _archive(self):
        if self._closed:
            raise ValueError("NPZ source member lifetime is closed")
        try:
            with self.physical.cursor(self.offset, self.original.array_artifact.size_bytes) as cursor:
                with zipfile.ZipFile(cursor) as archive:
                    yield archive
        except (OSError, zipfile.BadZipFile, EOFError) as error:
            raise ValueError("Matrix NPZ source cannot decode its original closed archive") from error

    def open_member(self, name):
        member = self.members[name]
        with self._archive() as archive:
            info = archive.getinfo(name + ".npy")
            with archive.open(info) as stream:
                dtype = matrix_npy_header(stream, info, member)
                for raw, _ in iter_matrix_npy_chunks(stream, member, dtype, maximum_chunk_bytes=self.maximum_chunk_bytes):
                    yield raw

    def read_member_range(self, name, start, stop):
        member = self.members[name]
        if self._closed:
            raise ValueError("NPZ source member lifetime is closed")
        if (type(start) is not int or type(stop) is not int or not 0 <= start <= stop <= member.size_bytes):
            raise ValueError("NPZ source range changes its exact original member interval")
        try:
            lease = self._ranges.get(name)
            if lease is not None and start < lease[1].tell() - lease[2]:
                self._ranges.pop(name)[0].close()
                lease = None
            if lease is None:
                while len(self._ranges) >= self.maximum_open_members:
                    self._ranges.popitem(last=False)[1][0].close()
                stack = ExitStack()
                try:
                    archive = stack.enter_context(self._archive())
                    info = archive.getinfo(name + ".npy")
                    stream = stack.enter_context(archive.open(info))
                    matrix_npy_header(stream, info, member)
                    lease = (stack, stream, stream.tell())
                    self._ranges[name] = lease
                except BaseException:
                    stack.close()
                    raise
            self._ranges.move_to_end(name)
            _, stream, base = lease
            stream.seek(base + start)
            raw = stream.read(stop - start)
            if len(raw) != stop - start:
                raise ValueError("Matrix NPZ range truncates its complete declared value bytes")
            return raw
        except BaseException:
            self.close()
            raise

    def close(self):
        if not self._closed:
            object.__setattr__(self, "_closed", True)
            while self._ranges:
                self._ranges.popitem()[1][0].close()


class MatrixNPZSource(NPZMemberSource):
    """Original Matrix codec wrapper, preserving its exact schema/media gate."""
    __slots__ = ()

    def __init__(self, original, physical, maximum_chunk_bytes, *, offset=0):
        original.__post_init__()
        if (original.array_artifact.payload_schema, original.array_artifact.media_type) != (MATRIX_ARRAY_SCHEMA, "application/x-npz"):
            raise ValueError("Matrix NPZ source changes its exact original codec schema or media")
        super().__init__(NPZMemberSelection(original.array_artifact, original.members), physical,
            maximum_chunk_bytes, offset=offset)


def validate_matrix_worker_array_input(port, *, manifest, allocation, expected_producers):
    """The original exact scientific allocation, producer and physical port join."""
    manifest.__post_init__()
    allocation.__post_init__()
    if type(allocation) is MatrixAllocation:
        allocation_identity = allocation.identity
    elif (type(allocation) is ObjectIdentity
            and allocation.object_schema == MatrixAllocation.SCHEMA
            and allocation.object_version == MatrixAllocation.VERSION):
        allocation_identity = allocation
    else:
        raise ValueError("Matrix worker needs its exact allocation identity or complete allocation record")
    if (not isinstance(port, WorkerInputPort)
            or manifest.allocation != allocation_identity
            or manifest.producers != expected_producers
            or port.artifact_id != manifest.array_artifact.artifact_id
            or port.payload_schema != manifest.array_artifact.payload_schema
            or port.media_type != manifest.array_artifact.media_type
            or port.size_bytes != manifest.array_artifact.size_bytes):
        raise ValueError("Matrix worker port changes its exact array, allocation or producing identities")


def iter_worker_matrix_array_chunks(port, *, manifest, allocation, expected_producers,
                                   maximum_chunk_bytes=1024**2):
    """Delegate complete typed delivery to the common reader over one sealed FD.

    The original closed NPZ bound and scientific joins remain unchanged. Every
    member is verified before the first value; exhaustion performs the final
    complete seal. Physical replay uses bounded cursors on the original FD.
    """
    from empirical_lawhood.infrastructure.dataset_readers import ArrayDatasetReader, AuthenticatedBlockByteSource
    from empirical_lawhood.kernel.datasets import ArrayDatasetManifest, ArrayDatasetMember

    validate_matrix_worker_array_input(port, manifest=manifest, allocation=allocation,
        expected_producers=expected_producers)
    if type(maximum_chunk_bytes) is not int or maximum_chunk_bytes < 16:
        raise ValueError("Matrix array chunk working memory must hold a complete complex value")
    chunk_bytes = maximum_chunk_bytes // 16 * 16
    references = tuple(sorted(set((manifest.allocation, *manifest.producers)), key=lambda value:value.object_id))
    logical = ArrayDatasetManifest("dataset.matrix.worker.logical",
        tuple(ArrayDatasetMember(member.name, member.dtype, member.shape, member.sha256, member.finite_required)
            for member in manifest.members), references)
    physical = MatrixArtifactSource(manifest.array_artifact, port, chunk_bytes)
    try:
        source = MatrixNPZSource(manifest, physical, chunk_bytes)
        reader = ArrayDatasetReader(logical,
            AuthenticatedBlockByteSource(source, read_range=source.read_member_range, close=physical.close),
            maximum_chunk_bytes=chunk_bytes, maximum_slice_bytes=chunk_bytes)
        with reader.verified_session(block_size_bytes=chunk_bytes) as selected:
            for member in manifest.members:
                offset = 0
                if member.size_bytes == 0:
                    yield member, offset, np.frombuffer(b"", dtype=member.dtype)
                for raw in selected.iter_member_bytes(member.name):
                    value = np.frombuffer(raw, dtype=member.dtype)
                    yield member, offset, value
                    offset += value.size
    finally:
        physical.close()


def matrix_array_members(
    arrays: Mapping[str, NDArray[np.generic]],
    *,
    nonfinite_members: tuple[str, ...] = (),
) -> tuple[MatrixArrayMember, ...]:
    """Validate and fingerprint exact values without constructing an archive."""
    if not 0 < len(arrays) <= 256 or not set(nonfinite_members) <= set(arrays):
        raise ValueError("Matrix array member or missingness census differs")
    members = []
    total = 0
    for name, value in sorted(arrays.items()):
        if not isinstance(value, np.ndarray) or value.dtype.hasobject:
            raise ValueError("Matrix array operands refuse Python object serialization")
        member = MatrixArrayMember(name, value.dtype.str, value.shape, sha256(value.tobytes(order="C")).hexdigest(), name not in nonfinite_members)
        total += member.size_bytes
        if total > MAXIMUM_MATRIX_ARRAY_BYTES or member.finite_required and not np.isfinite(value).all():
            raise ValueError("Matrix array expansion exceeds its bound or complete population")
        members.append(member)
    return tuple(members)


def encode_matrix_arrays(
    arrays: Mapping[str, NDArray[np.generic]],
    *,
    nonfinite_members: tuple[str, ...] = (),
) -> tuple[bytes, tuple[MatrixArrayMember, ...]]:
    """Retain exact typed values; missingness must be explicitly declared."""
    members = matrix_array_members(arrays, nonfinite_members=nonfinite_members)
    stream = BytesIO()
    np.savez_compressed(stream, **{name: np.array(value, order="C", copy=True) for name, value in arrays.items()})
    raw = stream.getvalue()
    if len(raw) > MAXIMUM_MATRIX_ARRAY_BYTES:
        raise ValueError("Matrix array physical transport exceeds its byte bound")
    return raw, members


def decode_matrix_arrays(
    raw: bytes, manifest: SavedMatrixArrays
) -> Mapping[str, NDArray[np.generic]]:
    """Decode once for the exact immutable operand in an explicit lifetime."""
    state = _decoded_array_scope.get()
    immutable = (type(manifest) is NPZMemberSelection
        or isinstance(manifest, CanonicalRecord) and manifest._is_cacheable())
    if state is None or state['owner'] != get_ident() or type(raw) is not bytes or not immutable:
        return _decode_matrix_arrays(raw, manifest)
    entries = state['entries']
    key = (id(raw), id(manifest))
    cached = entries.get(key)
    if cached is not None:
        entries.move_to_end(key)
        return cached[0].for_operand(raw, manifest)
    decoded = DecodedMatrixArrayInput(raw, manifest)
    values = decoded.for_operand(raw, manifest)
    size = len(raw) + sum(value.nbytes for value in values.values())
    if size <= state['limit']:
        while entries and (state['bytes'] + size > state['limit'] or len(entries) >= 16):
            _, (_, removed_size) = entries.popitem(last=False)
            state['bytes'] -= removed_size
        entries[key] = (decoded, size)
        state['bytes'] += size
    return values


def _decode_matrix_arrays(raw, manifest):
    """Authenticate physical bytes and bounded NPY headers before expansion."""
    if (
        type(raw) is not bytes
        or len(raw) > MAXIMUM_MATRIX_ARRAY_BYTES
        or len(raw) != manifest.array_artifact.size_bytes
        or sha256(raw).hexdigest() != manifest.array_artifact.sha256
    ):
        raise ValueError("Matrix array transport differs from its current artifact")
    values = decode_native_matrix_arrays(raw, {member.name: (member.dtype, member.shape) for member in manifest.members})
    ordered = {}
    for member in manifest.members:
        value = values[member.name]
        if (sha256(value).hexdigest() != member.sha256
                or member.finite_required and not np.isfinite(value).all()):
            raise ValueError("Matrix array values or required finite population differ")
        ordered[member.name] = value
    return MappingProxyType(ordered)


class DecodedMatrixArrayInput:
    """One immutable decoded operand for immediate mathematical consumers.

    This reuses the existing closed NPZ decoder, not a transport or authority
    cache. A worker owns this value only during its current invocation. Later
    invocations still authenticate and decode their own actually received input.
    """

    __slots__ = ("_raw", "original", "_values")

    def __setattr__(self, name, value):
        if hasattr(self, name):
            raise AttributeError("Matrix decoded input and its original operand are read-only")
        object.__setattr__(self, name, value)

    def __delattr__(self, name):
        raise AttributeError("Matrix decoded input and its original operand are read-only")

    def __init__(self, raw, manifest):
        self._raw, self.original = raw, manifest
        self._values = _decode_matrix_arrays(raw, manifest)

    def for_operand(self, raw, manifest):
        """Reuse values only for the same immutable bytes and exact typed record."""
        if (type(raw) is not bytes or raw is not self._raw
                or type(manifest) is not type(self.original) or manifest != self.original):
            raise ValueError("Matrix decoded input substitutes its received bytes or exact original operand")
        return self._values
