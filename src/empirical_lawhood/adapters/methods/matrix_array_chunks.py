# SPDX-License-Identifier: MPL-2.0
"""Complete matrix populations composed of unchanged bounded NPZ leaves.

This domain transport grants no native, scientific, outcome-access or freshness
permission. Scientific owners declare complete axes, source, allocation and
producer identities. Each physical leaf uses the existing typed array contract.
"""

from dataclasses import dataclass
from hashlib import sha256
from math import prod
from typing import ClassVar

import numpy as np

from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays, encode_matrix_arrays
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA, MAXIMUM_MATRIX_ARRAY_BYTES, MatrixArrayMember
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, require_sorted_unique_ids, validate_sha256, validate_stable_id
from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_FRAMED_ARRAY_SCHEMA

_DTYPES = {'<f8':8,'<c16':16,'<i8':8,'|b1':1}
EXPOSURE = 'EXPOSED_DEVELOPMENT_NONPROMOTABLE'


@dataclass(frozen=True, slots=True)
class MatrixWholeArrayMember(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-chunks/whole-array-member'
    name: str
    dtype: str
    shape: tuple[int, ...]
    sha256: str
    finite_required: bool = True

    def __post_init__(self):
        validate_stable_id(self.name)
        validate_sha256(self.sha256)
        if (self.dtype not in _DTYPES or type(self.shape) is not tuple
                or any(type(n) is not int or n < 0 for n in self.shape)
                or type(self.finite_required) is not bool):
            raise ValueError('whole matrix member changes exact dtype/shape/missingness')

    @property
    def size_bytes(self):
        return prod(self.shape)*_DTYPES[self.dtype]

    @property
    def first_axis_extent(self):
        return self.shape[0] if self.shape else 1


@dataclass(frozen=True, slots=True)
class MatrixArrayInterval(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-chunks/array-interval'
    name: str
    start: int
    stop: int

    def __post_init__(self):
        validate_stable_id(self.name)
        if type(self.start) is not int or type(self.stop) is not int or not 0 <= self.start <= self.stop:
            raise ValueError('matrix interval changes exact nonnegative first-axis ownership')


@dataclass(frozen=True, slots=True)
class MatrixArrayChunk(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-chunks/array-chunk'
    chunk_id: str
    array_artifact: ArtifactIdentity
    members: tuple[MatrixArrayMember, ...]
    intervals: tuple[MatrixArrayInterval, ...]
    producers: tuple[ObjectIdentity, ...]

    def __post_init__(self):
        validate_stable_id(self.chunk_id)
        require_sorted_unique_ids(self.members,attribute='name',field_name='bounded chunk members')
        require_sorted_unique_ids(self.intervals,attribute='name',field_name='exact chunk intervals')
        require_sorted_unique_ids(self.producers,attribute='object_id',field_name='exact chunk producers')
        if (not self.members or tuple(m.name for m in self.members) != tuple(i.name for i in self.intervals)
                or not self.producers or self.array_artifact.payload_schema != MATRIX_ARRAY_SCHEMA
                or self.array_artifact.media_type != 'application/x-npz'
                or self.array_artifact.size_bytes > MAXIMUM_MATRIX_ARRAY_BYTES
                or sum(m.size_bytes for m in self.members) > MAXIMUM_MATRIX_ARRAY_BYTES):
            raise ValueError('matrix chunk loses actual bounded array/interval/producer census')


@dataclass(frozen=True, slots=True)
class ChunkedMatrixArrays(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-chunks/complete-arrays'
    operand_id: str
    source: ObjectIdentity
    allocation: ObjectIdentity
    members: tuple[MatrixWholeArrayMember, ...]
    chunks: tuple[MatrixArrayChunk, ...]
    producers: tuple[ObjectIdentity, ...]
    exposure: str = EXPOSURE

    def __post_init__(self):
        validate_stable_id(self.operand_id)
        require_sorted_unique_ids(self.members,attribute='name',field_name='complete scientific members')
        require_sorted_unique_ids(self.chunks,attribute='chunk_id',field_name='complete physical chunks')
        require_sorted_unique_ids(self.producers,attribute='object_id',field_name='complete scientific producers')
        if (type(self.source) is not ObjectIdentity or type(self.allocation) is not ObjectIdentity
                or not self.members or not self.chunks or not self.producers or self.exposure != EXPOSURE
                or len({c.array_artifact.artifact_id for c in self.chunks}) != len(self.chunks)):
            raise ValueError('chunked matrix population changes source/allocation/physical census')
        declared = {m.name:m for m in self.members}
        cursors, seen = {m.name:0 for m in self.members},set()
        for chunk in self.chunks:
            if chunk.producers != self.producers:
                raise ValueError('matrix leaf changes its complete population producing identities')
            for leaf,interval in zip(chunk.members,chunk.intervals,strict=True):
                if leaf.name not in declared:
                    raise ValueError('matrix chunk introduces an undeclared scientific member')
                member = declared[leaf.name]
                shape = (interval.stop-interval.start,)+member.shape[1:] if member.shape else ()
                if (interval.start != cursors[leaf.name] or interval.stop > member.first_axis_extent
                        or (interval.start == interval.stop and (member.first_axis_extent != 0 or leaf.name in seen))
                        or leaf.dtype != member.dtype or leaf.shape != shape or leaf.finite_required != member.finite_required
                        or (not member.shape and (interval.start,interval.stop) != (0,1))):
                    raise ValueError('matrix chunks overlap, omit, reorder or change exact scientific axes')
                cursors[leaf.name] = interval.stop
                seen.add(leaf.name)
        if seen != set(declared) or any(cursors[name] != m.first_axis_extent for name,m in declared.items()):
            raise ValueError('matrix chunks omit the complete scientific member denominator')

    @property
    def size_bytes(self):
        return sum(m.size_bytes for m in self.members)


def whole_member(name,value,*,finite_required=True):
    if not isinstance(value,np.ndarray) or value.dtype.hasobject:
        raise ValueError('whole array requires existing exact NumPy values')
    return MatrixWholeArrayMember(name,value.dtype.str,value.shape,sha256(value.tobytes(order='C')).hexdigest(),finite_required)


def encode_chunk(arrays,intervals,*,chunk_id,artifact_id,producers,nonfinite_members=()):
    """Encode one already bounded scientific slice, never a combined archive."""
    raw,members = encode_matrix_arrays(arrays,nonfinite_members=nonfinite_members)
    artifact = ArtifactIdentity(artifact_id,'matrix-array-chunk',MATRIX_ARRAY_SCHEMA,sha256(raw).hexdigest(),'application/x-npz',len(raw))
    chunk = MatrixArrayChunk(chunk_id,artifact,members,tuple(sorted(intervals,key=lambda i:i.name)),
        tuple(sorted(producers,key=lambda p:p.object_id)))
    return raw,chunk


def verify_chunked_arrays(manifest,fetch):
    """Authenticate the full denominator with one decoded leaf at a time."""
    if type(manifest) is not ChunkedMatrixArrays:
        raise ValueError('chunk reader requires its explicit complete transport edition')
    manifest.__post_init__()
    digests = {m.name:sha256() for m in manifest.members}
    for chunk in manifest.chunks:
        raw = fetch(chunk.array_artifact)
        arrays = decode_matrix_arrays(raw,chunk)
        for name,value in arrays.items():
            digests[name].update(value.tobytes(order='C'))
        # No complete population or branch dictionary survives each iteration.
        del arrays,raw
    if any(digests[m.name].hexdigest() != m.sha256 for m in manifest.members):
        raise ValueError('matrix chunk values differ from complete scientific member hashes')
    return manifest


def iter_chunk_arrays(manifest,fetch):
    """Expose no favourable prefix before the full immutable census verifies.

    Exact physical/value hashes are checked again on delivery. A missing late
    leaf, changed byte or unknown publication prevents all scientific delivery.
    Consumers must exhaust this iterator to consume every owned interval.
    """
    verify_chunked_arrays(manifest,fetch)
    for chunk in manifest.chunks:
        arrays = decode_matrix_arrays(fetch(chunk.array_artifact),chunk)
        yield chunk,arrays


FRAMED_ARRAY_SCHEMA = MATRIX_FRAMED_ARRAY_SCHEMA
FRAMED_ARRAY_MEDIA = 'application/octet-stream'


def framed_size(manifest):
    manifest.__post_init__()
    return sum(8+chunk.array_artifact.size_bytes for chunk in manifest.chunks)


def iter_framed_bytes(manifest,iter_fetch,*,maximum_chunk_bytes):
    """Stream exact receipted NPZ leaves; no combined archive or reencoding."""
    manifest.__post_init__()
    if type(maximum_chunk_bytes) is not int or maximum_chunk_bytes < 8:
        raise ValueError('framed matrix working buffer must hold its eight-byte length')
    for chunk in manifest.chunks:
        artifact = chunk.array_artifact
        yield artifact.size_bytes.to_bytes(8,'big')
        digest,count = sha256(),0
        for raw in iter_fetch(artifact):
            if not isinstance(raw,bytes) or not raw:
                raise ValueError('framed matrix leaf source yields invalid exact bytes')
            count += len(raw);digest.update(raw)
            if count > artifact.size_bytes:
                raise ValueError('framed matrix leaf exceeds its actual retained byte count')
            for start in range(0,len(raw),maximum_chunk_bytes):
                yield raw[start:start+maximum_chunk_bytes]
        if count != artifact.size_bytes or digest.hexdigest() != artifact.sha256:
            raise ValueError('framed matrix leaf differs from actual original receipt bytes')


def framed_artifact(manifest,iter_fetch,*,artifact_id,maximum_chunk_bytes=1024**2):
    digest,count = sha256(),0
    for raw in iter_framed_bytes(manifest,iter_fetch,maximum_chunk_bytes=maximum_chunk_bytes):
        count += len(raw);digest.update(raw)
    if count != framed_size(manifest):
        raise ValueError('framed matrix container loses complete physical leaf census')
    return ArtifactIdentity(artifact_id,'framed-matrix-array-container',FRAMED_ARRAY_SCHEMA,
        digest.hexdigest(),FRAMED_ARRAY_MEDIA,count)


def _read_exact(read,count):
    parts,seen = [],0
    while seen < count:
        raw = read(count-seen)
        if not isinstance(raw,bytes) or not raw or len(raw) > count-seen:
            raise ValueError('framed matrix input truncates or exceeds its exact selected interval')
        parts.append(raw);seen += len(raw)
    return b''.join(parts)


def iter_framed_chunk_arrays(manifest,container,read):
    """Single-pass worker delivery, with a final complete verification seal.

    The consumer may compute while reading. It must exhaust the iterator before
    constructing or publishing any successful scientific product or assessment.
    A late adverse/absent member or changed container prevents that final seal.
    """
    manifest.__post_init__()
    if ((container.payload_schema,container.media_type,container.size_bytes) !=
            (FRAMED_ARRAY_SCHEMA,FRAMED_ARRAY_MEDIA,framed_size(manifest))):
        raise ValueError('framed matrix port changes complete container schema/media/size')
    whole = {m.name:sha256() for m in manifest.members}
    digest,count = sha256(),0
    for chunk in manifest.chunks:
        header = _read_exact(read,8)
        length = int.from_bytes(header,'big')
        if length != chunk.array_artifact.size_bytes or length > MAXIMUM_MATRIX_ARRAY_BYTES:
            raise ValueError('framed matrix length changes actual bounded leaf size')
        raw = _read_exact(read,length)
        digest.update(header);digest.update(raw);count += 8+length
        arrays = decode_matrix_arrays(raw,chunk)
        for name,value in arrays.items():
            whole[name].update(value.tobytes(order='C'))
        del raw
        yield chunk,arrays
    if (read(1) or count != container.size_bytes or digest.hexdigest() != container.sha256
            or any(whole[m.name].hexdigest() != m.sha256 for m in manifest.members)):
        raise ValueError('framed matrix complete container/member verification failed')
