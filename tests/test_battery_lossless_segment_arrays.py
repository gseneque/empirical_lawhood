# SPDX-License-Identifier: MPL-2.0
"""Lossless represented values and complete adverse streams; exposed software."""

import base64
from dataclasses import replace
from hashlib import sha256
import json
import struct
import zlib

import pytest

from empirical_lawhood.adapters.methods.battery_refined_inquiry import lossless_segment_arrays as codec
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes


def declaration(raw, *, shape=None, dtype='<f8', itemsize=8, role='all_ys'):
    return codec.LosslessArrayDeclaration('array.exposed-original',
        ObjectIdentity('raw.exposed', 'empirical-lawhood/battery-segmented/raw-returned-segment', '1.0.0', '1' * 64),
        role, 0, dtype, (len(raw) // itemsize,) if shape is None else shape, itemsize, sha256(raw).hexdigest())


def chunks(raw, spacing=997):
    return (raw[at:at + spacing] for at in range(0, len(raw), spacing))


def change(line, mutate):
    value = json.loads(line)
    mutate(value)
    return canonical_json_bytes(value)


def test_independent_consumer_preserves_every_ieee_payload_and_c_order():
    # Explicit arbitrary NaN payloads, signed zeros, infinities and subnormals:
    # storage must preserve them; numerical interpretation must still assess them.
    words = (0, 1 << 63, 0x7ff0000000000000, 0xfff0000000000000,
        0x7ff8000000000042, 0x7ff0000000000042, 1, 0x8000000000000001)
    raw = b''.join(struct.pack('<Q', word) for word in words) * 5000
    owner = declaration(raw, shape=(200, 200))
    lines = tuple(codec.encode_array(owner, chunks(raw)))
    result = tuple(codec.decode_array(iter(lines), owner))
    assert b''.join(result) == raw
    assert max(map(len, result)) <= codec.CHUNK_BYTES
    assert all(len(line) <= 2 * codec.CHUNK_BYTES for line in lines)
    assert len(result) == (len(raw) + codec.CHUNK_BYTES - 1) // codec.CHUNK_BYTES
    assert owner.scope == codec.SCOPE


@pytest.mark.parametrize('dtype,itemsize,raw,shape', [
    ('>f8', 8, struct.pack('>d', -0.0), ()),
    ('<i4', 4, bytes(range(20)), (5,)),
    ('|u1', 1, b'\x00\xff\x00', (3,)),
    ('|O', 8, b'\xff' * 16, (2,)),
    ('<f8', 8, b'', (0, 7)),
])
def test_exact_representation_retained_without_portable_numerical_inference(dtype, itemsize, raw, shape):
    owner = declaration(raw, dtype=dtype, itemsize=itemsize, shape=shape)
    assert b''.join(codec.decode_array(codec.encode_array(owner, chunks(raw)), owner)) == raw
    assert owner.row_semantics.startswith('RAW_ONLY;')


@pytest.mark.parametrize('field,value', [('order', 'F'), ('scope', 'SATISFIED'),
    ('role', 'temperature-only'), ('block_index', -1), ('itemsize', 0)])
def test_declaration_refuses_representation_or_claim_substitution(field, value):
    with pytest.raises(ValueError):
        replace(declaration(b'\x00' * 16), **{field: value})


@pytest.mark.parametrize('field,value', [('dtype', '>f8'), ('shape', (2, 1)),
    ('role', 'all_yps'), ('block_index', 1),
    ('source', ObjectIdentity('raw.other', 'empirical-lawhood/battery-segmented/raw-returned-segment', '1.0.0', '2' * 64)),
    ('layout', ObjectIdentity('layout.other', 'empirical-lawhood/battery-preparation/processed-state-layout', '1.0.0', '3' * 64))])
def test_actual_consumer_refuses_changed_source_axes_role_or_units_operand(field, value):
    raw = b'\x00' * 16
    original = declaration(raw)
    altered = replace(original, **{field: value})
    with pytest.raises(ValueError):
        tuple(codec.decode_array(codec.encode_array(altered, chunks(raw)), original))


@pytest.mark.parametrize('kind', ['missing', 'reordered', 'duplicate', 'wrong-offset', 'missing-final',
    'wrong-total', 'wrong-raw-sha', 'after-final', 'wrong-chunk-sha', 'noncanonical'])
def test_complete_consumer_refuses_omitted_wrong_or_extended_denominator(kind):
    raw = b'abcdefgh' * 20000
    owner = declaration(raw)
    lines = list(codec.encode_array(owner, chunks(raw)))
    if kind == 'missing':
        del lines[1]
    elif kind == 'reordered':
        lines[1], lines[2] = lines[2], lines[1]
    elif kind == 'duplicate':
        lines.insert(2, lines[1])
    elif kind == 'wrong-offset':
        lines[1] = change(lines[1], lambda value: value['value']['chunk']['value'].update(offset=8))
    elif kind == 'missing-final':
        lines.pop()
    elif kind == 'wrong-total':
        lines[-1] = change(lines[-1], lambda value: value['value'].update(complete_bytes=len(raw) - 8))
    elif kind == 'wrong-raw-sha':
        lines[-1] = change(lines[-1], lambda value: value['value'].update(complete_sha256='4' * 64))
    elif kind == 'after-final':
        lines.append(change(lines[-1], lambda value: value.update(sequence=len(lines))))
    elif kind == 'wrong-chunk-sha':
        lines[1] = change(lines[1], lambda value: value['value']['chunk']['value'].update(decoded_sha256='5' * 64))
    else:
        lines[1] = lines[1].replace(b'"schema":', b'"schema": ')
    with pytest.raises(ValueError):
        tuple(codec.decode_array(iter(lines), owner))


@pytest.mark.parametrize('wrong', ['trailing', 'second-member', 'expansion'])
def test_bounded_decoder_refuses_trailing_and_expanding_gzip(wrong):
    raw = b'\x00' * 8
    owner = declaration(raw)
    lines = list(codec.encode_array(owner, chunks(raw)))
    value = json.loads(lines[1])['value']['chunk']['value']
    encoded = base64.b64decode(value['gzip_base64'])
    if wrong == 'trailing':
        encoded += b'\x00'
    elif wrong == 'second-member':
        encoded += encoded
    else:
        compressor = zlib.compressobj(level=6, wbits=31)
        encoded = compressor.compress(b'\x00' * 10**6) + compressor.flush()
    lines[1] = change(lines[1], lambda document: document['value']['chunk']['value'].update(
        gzip_base64=base64.b64encode(encoded).decode(), encoded_sha256=sha256(encoded).hexdigest()))
    with pytest.raises(ValueError):
        tuple(codec.decode_array(iter(lines), owner))


@pytest.mark.parametrize('kind', ['source-short', 'source-long', 'source-wrong', 'source-unbounded'])
def test_encoder_refuses_changed_complete_original_source(kind):
    raw = b'\x00' * 16
    owner = declaration(raw)
    provided = {'source-short': b'\x00' * 8, 'source-long': b'\x00' * 24,
        'source-wrong': b'\xff' * 16, 'source-unbounded': b'\x00' * (codec.CHUNK_BYTES + 1)}[kind]
    source = (provided,) if kind == 'source-unbounded' else chunks(provided)
    with pytest.raises(ValueError):
        tuple(codec.encode_array(owner, source))


def test_missing_completion_is_not_promoted_by_favourable_prefix():
    raw = b'\x00' * 16
    owner = declaration(raw)
    lines = list(codec.encode_array(owner, chunks(raw)))
    read = codec.decode_array(iter(lines[:-1]), owner)
    assert next(read) == raw
    with pytest.raises(ValueError):
        next(read)
