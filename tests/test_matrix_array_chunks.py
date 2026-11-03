"""Exposed complete chunk transport, with old physical array schemas intact."""

from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import shutil

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_array_chunks import (
    ChunkedMatrixArrays, MatrixArrayInterval, MatrixWholeArrayMember,
    encode_chunk, iter_chunk_arrays, verify_chunked_arrays, whole_member,
)
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.matrix_inputs import MAXIMUM_MATRIX_ARRAY_BYTES
from empirical_lawhood.kernel.provenance import ObjectIdentity


def identity(name):
    return ObjectIdentity(name,'empirical-lawhood/tests/'+name,'1.0.0','a'*64)


def small_case():
    values = {'state':np.arange(24,dtype='<f8').reshape(8,3),'ticks':np.arange(8,dtype='<i8'),
        'scalar':np.asarray(1.,dtype='<f8'),'empty':np.empty((0,2),dtype='<c16')}
    producers = (identity('producer'),)
    chunks,raws = [],{}
    for index,(start,stop) in enumerate(((0,3),(3,5),(5,8))):
        arrays = {name:v[start:stop] for name,v in values.items() if name in ('state','ticks')}
        intervals = [MatrixArrayInterval(name,start,stop) for name in arrays]
        if index == 0:
            arrays |= {name:values[name] for name in ('empty','scalar')}
            intervals += [MatrixArrayInterval('empty',0,0),MatrixArrayInterval('scalar',0,1)]
        raw,chunk = encode_chunk(arrays,intervals,chunk_id=f'chunk.{index:04d}',artifact_id=f'array.{index:04d}',producers=producers)
        chunks.append(chunk);raws[chunk.array_artifact.artifact_id] = raw
    members = tuple(whole_member(name,value) for name,value in sorted(values.items()))
    manifest = ChunkedMatrixArrays('arrays.complete',identity('source'),identity('allocation'),members,tuple(chunks),producers)
    return values,manifest,raws


def test_complete_scalar_empty_and_segment_axes_roundtrip(tmp_path):
    values,manifest,raws = small_case()
    decoded = decode_canonical_bytes(manifest.canonical_bytes(),ChunkedMatrixArrays,maximum_bytes=None)
    assert decoded == manifest
    files = {}
    for artifact_id,raw in raws.items():
        path = tmp_path/artifact_id;path.write_bytes(raw);files[artifact_id] = path
    target = tmp_path/'portable';target.mkdir()
    for path in files.values():
        shutil.copy2(path,target/path.name)
    delivered = {name:[] for name in values}
    for chunk,arrays in iter_chunk_arrays(manifest,lambda artifact:(target/artifact.artifact_id).read_bytes()):
        assert set(arrays) == {m.name for m in chunk.members}
        for name,value in arrays.items():
            delivered[name].append(value)
    for name,pieces in delivered.items():
        actual = pieces[0] if name in ('scalar','empty') else np.concatenate(pieces)
        assert np.array_equal(actual,values[name])


@pytest.mark.parametrize('defect',('missing-tail','overlap','gap','wrong-shape','wrong-producer','duplicate-artifact'))
def test_structural_complete_denominator_refusal(defect):
    _,manifest,_ = small_case()
    chunks = list(manifest.chunks)
    if defect == 'missing-tail':
        chunks.pop()
    elif defect in ('overlap','gap'):
        row = chunks[1]
        changed = tuple(replace(interval,start=interval.start+(-1 if defect == 'overlap' else 1)) for interval in row.intervals)
        chunks[1] = replace(row,intervals=changed)
    elif defect == 'wrong-shape':
        row = chunks[1]
        chunks[1] = replace(row,members=tuple(replace(m,shape=(3,3)) if m.name == 'state' else m for m in row.members))
    elif defect == 'wrong-producer':
        chunks[1] = replace(chunks[1],producers=(identity('other-producer'),))
    else:
        chunks[1] = replace(chunks[1],array_artifact=replace(chunks[1].array_artifact,artifact_id=chunks[0].array_artifact.artifact_id))
    with pytest.raises(ValueError,match='omit|overlap|axes|produc|census'):
        replace(manifest,chunks=tuple(chunks))


@pytest.mark.parametrize('defect',('missing-file','changed-byte','changed-whole-hash'))
def test_late_error_delivers_no_favourable_prefix(defect):
    _,manifest,raws = small_case()
    if defect == 'changed-whole-hash':
        manifest = replace(manifest,members=tuple(replace(m,sha256='f'*64) if m.name == 'state' else m for m in manifest.members))
    else:
        artifact = manifest.chunks[-1].array_artifact
        if defect == 'missing-file':
            raws.pop(artifact.artifact_id)
        else:
            raw = bytearray(raws[artifact.artifact_id]);raw[-30] ^= 1;raws[artifact.artifact_id] = bytes(raw)
    output = iter_chunk_arrays(manifest,lambda artifact:raws[artifact.artifact_id])
    with pytest.raises((ValueError,KeyError)):
        next(output)


def test_explicit_unevaluable_values_preserved_in_complete_member():
    values = np.asarray([1.,np.nan,np.inf],dtype='<f8')
    producers = (identity('producer'),)
    raw,chunk = encode_chunk({'error':values},(MatrixArrayInterval('error',0,3),),chunk_id='chunk.0000',
        artifact_id='array.error',producers=producers,nonfinite_members=('error',))
    member = whole_member('error',values,finite_required=False)
    manifest = ChunkedMatrixArrays('arrays.unevaluable',identity('source'),identity('allocation'),(member,),(chunk,),producers)
    delivered = next(iter_chunk_arrays(manifest,lambda artifact:raw))[1]['error']
    assert np.isnan(delivered[1]) and np.isposinf(delivered[2])
    with pytest.raises(ValueError,match='axes'):
        replace(manifest,members=(replace(member,finite_required=True),))


def test_whole_member_beyond_original_64mib_has_complete_bounded_leaves(tmp_path):
    # A real over-capacity population, produced one bounded piece at a time.
    # Only transport is tested; there is no native model or qualification.
    count = MAXIMUM_MATRIX_ARRAY_BYTES//(8*32)+2
    producers = (identity('producer'),)
    chunks, digest = [],sha256()
    for index,(start,stop) in enumerate(((0,count//2),(count//2,count))):
        value = np.arange(start*32,stop*32,dtype='<f8').reshape(stop-start,32)
        digest.update(value.tobytes(order='C'))
        raw,chunk = encode_chunk({'all-rows':value},(MatrixArrayInterval('all-rows',start,stop),),
            chunk_id=f'chunk.large.{index:04d}',artifact_id=f'array.large.{index:04d}',producers=producers)
        (tmp_path/chunk.array_artifact.artifact_id).write_bytes(raw)
        chunks.append(chunk)
        assert len(raw) <= MAXIMUM_MATRIX_ARRAY_BYTES
        del raw,value
    member = MatrixWholeArrayMember('all-rows','<f8',(count,32),digest.hexdigest())
    manifest = ChunkedMatrixArrays('arrays.large',identity('source'),identity('allocation'),(member,),tuple(chunks),producers)
    assert manifest.size_bytes > MAXIMUM_MATRIX_ARRAY_BYTES
    fetch = lambda artifact:Path(tmp_path/artifact.artifact_id).read_bytes()
    assert verify_chunked_arrays(manifest,fetch) == manifest
    rows,final = 0,None
    for _,arrays in iter_chunk_arrays(manifest,fetch):
        rows += arrays['all-rows'].shape[0];final = arrays['all-rows'][-1,-1]
    assert rows == count and final == count*32-1


def test_framed_container_original_leaves_roundtrip_partial_reads():
    from io import BytesIO
    from empirical_lawhood.adapters.methods.matrix_array_chunks import framed_artifact, framed_size, iter_framed_bytes, iter_framed_chunk_arrays
    _,manifest,raws = small_case()
    def fetch(artifact):
        raw = raws[artifact.artifact_id]
        yield raw[:15];yield raw[15:]
    artifact = framed_artifact(manifest,fetch,artifact_id='array.container',maximum_chunk_bytes=31)
    payload = b''.join(iter_framed_bytes(manifest,fetch,maximum_chunk_bytes=31))
    assert len(payload) == framed_size(manifest) == artifact.size_bytes
    handle = BytesIO(payload)
    delivered = list(iter_framed_chunk_arrays(manifest,artifact,lambda size:handle.read(min(size,17))))
    assert tuple(c for c,_ in delivered) == manifest.chunks
    assert delivered[0][1]['scalar'] == 1.


@pytest.mark.parametrize('defect',('truncated','changed-header','changed-container-hash','changed-whole-hash','extra-tail','changed-leaf'))
def test_framed_late_error_prevents_final_success_seal(defect):
    from io import BytesIO
    from empirical_lawhood.adapters.methods.matrix_array_chunks import framed_artifact, iter_framed_bytes, iter_framed_chunk_arrays
    _,manifest,raws = small_case()
    fetch = lambda artifact:iter((raws[artifact.artifact_id],))
    artifact = framed_artifact(manifest,fetch,artifact_id='array.container')
    payload = b''.join(iter_framed_bytes(manifest,fetch,maximum_chunk_bytes=1024))
    if defect == 'truncated':
        payload = payload[:-1]
    elif defect == 'changed-header':
        payload = bytes(8)+payload[8:]
    elif defect == 'changed-container-hash':
        artifact = replace(artifact,sha256='f'*64)
    elif defect == 'changed-whole-hash':
        manifest = replace(manifest,members=tuple(replace(m,sha256='f'*64) if m.name == 'ticks' else m for m in manifest.members))
    elif defect == 'extra-tail':
        payload += b'x'
    else:
        payload = payload[:-15]+b'x'+payload[-14:]
    handle = BytesIO(payload)
    with pytest.raises(ValueError):
        tuple(iter_framed_chunk_arrays(manifest,artifact,handle.read))
