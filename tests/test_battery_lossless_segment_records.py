# SPDX-License-Identifier: MPL-2.0
"""Exact old scientific subjects and bounded lazy consumption; exposed only."""
from dataclasses import replace
from hashlib import sha256
from io import BytesIO
import struct
from tempfile import TemporaryFile

import pytest

from empirical_lawhood.adapters.methods.battery_refined_inquiry import lossless_segment_arrays as codec
from empirical_lawhood.adapters.methods.battery_refined_inquiry import lossless_segment_records as r
from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_native as native
from empirical_lawhood.kernel.provenance import ObjectIdentity
from tests.test_battery_segmented_fidelity import _operand, prepared as prepared_fixture

prepared = prepared_fixture


def encoded_original(raw, full):
    sources, declarations, counts = {}, [], []
    for role, arrays in zip(("all_ts", "all_ys", "all_yps"), (raw.clock_blocks, raw.state_blocks, raw.derivative_blocks), strict=True):
        counts.append(None if arrays is None else len(arrays))
        for at, array in enumerate(arrays or ()):
            payload = bytes.fromhex(array.bytes_hex)
            declaration = codec.LosslessArrayDeclaration("array.exposed." + role.replace("_", "-") + "." + str(at),
                r.identity(raw, "raw_id"), role, at, array.dtype, array.shape, array.itemsize, sha256(payload).hexdigest())
            declarations.append(declaration)
            def chunks(data=payload):
                return (data[offset:offset + codec.CHUNK_BYTES] for offset in range(0, len(data), codec.CHUNK_BYTES))
            def read_at(offset, size, data=payload):
                return data[offset:offset + size]
            sources[declaration.array_id] = chunks, read_at
    index = r.RawSegmentIndex("index.exposed-raw", r.identity(raw, "raw_id"), raw.protocol, raw.request, raw.returned,
        raw.present_attributes, tuple(counts), tuple(declarations))
    typed = None if full is None else r.FullSegmentIndex("index.exposed-full", r.identity(full, "segment_id"), full.protocol,
        full.layout, full.request, full.returned, r.identity(index, "index_id"), r.identity(raw, "raw_id"),
        tuple(block.state_rows for block in full.blocks), full.returned_model_expression_sha256,
        full.returned_inputs_json, full.actual_termination)
    return index, typed, sources


def test_exact_original_raw_and_full_subject_hashes_and_lazy_cache(prepared, tmp_path):
    operand = _operand(prepared, tmp_path / "original", extra_knot=7.5)
    raw, full = operand.frame.raw_return, operand.frame.full_state
    index, typed, sources = encoded_original(raw, full)
    assert b"".join(r.raw_subject_fragments(raw.raw_id, raw.protocol, raw.request, raw.returned,
        raw.present_attributes, index.block_counts, tuple((row, sources[row.array_id][0]) for row in index.arrays))) == raw.canonical_bytes()
    index2, decoded, handles = r.decode_raw_segment(r.encode_raw_segment(index, sources), lambda: TemporaryFile(dir=tmp_path))
    try:
        assert index2 == index
        view = r.DecodedFullSegment(typed, index2, decoded)
        assert b"".join(r.full_subject_fragments(typed, view.blocks)) == full.canonical_bytes()
        assert view.fingerprint() == full.fingerprint()
        for a, b in zip(view.blocks, full.blocks, strict=True):
            assert a.clock_binary64 == b.clock_binary64
            assert tuple(a.state_binary64) == b.state_binary64
            assert tuple(a.derivative_binary64) == b.derivative_binary64
            assert len(a.state_binary64.cache) <= codec.CHUNK_BYTES
            assert len(a.derivative_binary64.cache) <= codec.CHUNK_BYTES
    finally:
        for handle in handles:
            handle.close()


@pytest.mark.parametrize("damage", ("missing-footer", "trailing", "missing-array", "changed-subject", "swapped-arrays"))
@pytest.mark.parametrize("clock_major_working", (False, True))
def test_complete_segment_refuses_adverse_transport_or_subject_denominator(prepared, tmp_path, damage, clock_major_working):
    operand = _operand(prepared, tmp_path / "original")
    index, _, sources = encoded_original(operand.frame.raw_return, None)
    lines = list(r.encode_raw_segment(index, sources))
    if damage == "missing-footer":
        lines.pop()
    elif damage == "trailing":
        lines.append(lines[-1])
    elif damage == "missing-array":
        del lines[1:4]
    elif damage == "swapped-arrays":
        lines[1], lines[4] = lines[4], lines[1]
    else:
        forged = replace(index, decoded_subject=replace(index.decoded_subject, object_fingerprint="e" * 64),
            arrays=tuple(replace(row, source=replace(index.decoded_subject, object_fingerprint="e" * 64)) for row in index.arrays))
        lines = list(r.encode_raw_segment(forged, sources))
    opened = []
    def temporary():
        handle = BytesIO()
        opened.append(handle)
        return handle
    with pytest.raises((ValueError, StopIteration)):
        r.decode_raw_segment(iter(lines), temporary, clock_major_working=clock_major_working)
    assert all(handle.closed for handle in opened)


@pytest.mark.parametrize("damage", ("wrong-raw-index", "wrong-layout", "wrong-subject", "omitted-rows", "wrong-dtype"))
def test_full_consumer_refuses_scientific_source_or_shape_substitution(prepared, tmp_path, damage):
    operand = _operand(prepared, tmp_path / "original")
    index, typed, sources = encoded_original(operand.frame.raw_return, operand.frame.full_state)
    if damage == "wrong-raw-index":
        typed = replace(typed, raw_index=replace(typed.raw_index, object_fingerprint="f" * 64))
    elif damage == "wrong-layout":
        typed = replace(typed, layout=replace(typed.layout, object_fingerprint="f" * 64))
    elif damage == "wrong-subject":
        typed = replace(typed, decoded_subject=replace(typed.decoded_subject, object_fingerprint="f" * 64))
    elif damage == "omitted-rows":
        typed = replace(typed, state_rows=(173,))
    else:
        index = replace(index, arrays=tuple(replace(row, dtype="<i8") if row.role == "all_ys" else row for row in index.arrays))
        typed = replace(typed, raw_index=r.identity(index, "index_id"))
    with pytest.raises(ValueError):
        r.DecodedFullSegment(typed, index, sources)


@pytest.mark.parametrize("clock_major_working", (False, True))
def test_raw_nonfinite_ieee_payload_is_retained_but_interpretation_refuses(prepared, tmp_path, clock_major_working):
    operand = _operand(prepared, tmp_path / "original")
    raw = operand.frame.raw_return
    original = raw.state_blocks[0]
    payload = struct.pack("<Q", 0x7ff8000000000042) + bytes.fromhex(original.bytes_hex)[8:]
    raw = replace(raw, state_blocks=(replace(original, bytes_hex=payload.hex()),))
    index, _, sources = encoded_original(raw, None)
    decoded_index, decoded, handles = r.decode_raw_segment(r.encode_raw_segment(index, sources), BytesIO,
        clock_major_working=clock_major_working)
    try:
        assert decoded_index.decoded_subject == r.identity(raw, "raw_id")
        state = next(row for row in index.arrays if row.role == "all_ys")
        assert decoded[state.array_id][1](0, 8) == payload[:8]
        with pytest.raises(ValueError, match="nonfinite"):
            r.Binary64View(state, decoded[state.array_id][1])[0]
        if clock_major_working:
            with pytest.raises(ValueError, match="nonfinite"):
                r.ClockMajorView(state, decoded[state.array_id][1].__self__.handle)[0]
    finally:
        for handle in handles:
            handle.close()


def test_absent_and_empty_array_collections_have_distinct_preserved_subjects(prepared, tmp_path):
    operand = _operand(prepared, tmp_path / "original")
    raw = operand.frame.raw_return
    a, _, sa = encoded_original(replace(raw, derivative_blocks=None), None)
    b, _, sb = encoded_original(replace(raw, derivative_blocks=()), None)
    assert a.block_counts == (1, 1, None) and b.block_counts == (1, 1, 0)
    assert a.decoded_subject != b.decoded_subject
    for index, source in ((a, sa), (b, sb)):
        decoded, _, handles = r.decode_raw_segment(r.encode_raw_segment(index, source), BytesIO)
        assert decoded == index
        for handle in handles:
            handle.close()


def test_lazy_view_reads_at_most_one_chunk_and_preserves_signed_zero():
    payload = struct.pack("<d", -0.) + struct.pack("<d", 1.) * 20000
    declaration = codec.LosslessArrayDeclaration("array.exposed-large", ObjectIdentity("raw.exposed-large", native.RawReturnedSegment.SCHEMA, "1.0.0", "0" * 64),
        "all_ys", 0, "<f8", (20001,), 8, sha256(payload).hexdigest())
    requests = []
    def read_at(offset, size):
        requests.append((offset, size))
        return payload[offset:offset + size]
    view = r.Binary64View(declaration, read_at)
    assert view[0] == "-0x0.0p+0" and view[19000] == "0x1.0000000000000p+0" and view[1] == "0x1.0000000000000p+0"
    assert all(size <= codec.CHUNK_BYTES for _, size in requests)
    assert len(view.cache) <= codec.CHUNK_BYTES and not hasattr(view, "state_binary64")


def test_clock_major_scratch_is_exact_and_two_cache_chunks_are_bounded(tmp_path):
    rows, width = 600, 200
    raw = b"".join(struct.pack("<d", float(row * width + clock)) for row in range(rows) for clock in range(width))
    declaration = codec.LosslessArrayDeclaration("array.exposed-clock-major", ObjectIdentity("raw.exposed-clock-major", native.RawReturnedSegment.SCHEMA, "1.0.0", "0" * 64),
        "all_ys", 0, "<f8", (rows, width), 8, sha256(raw).hexdigest())
    handle = r._clock_major(declaration, lambda offset, size: raw[offset:offset + size], lambda: TemporaryFile(dir=tmp_path))
    try:
        view = r.ClockMajorView(declaration, handle)
        for clock in (0, 1, 97, 199):
            for row in range(rows):
                assert view[row * width + clock] == float(row * width + clock).hex()
        assert sum(map(len, view.cached.values())) <= 2 * codec.CHUNK_BYTES
        assert b"".join(struct.pack("<d", float.fromhex(view[i])) for i in range(len(view))) == raw
    finally:
        handle.close()


def test_clock_major_scratch_byte_changes_refuse_and_close():
    raw = struct.pack("<d", 1.) * 12
    declaration = codec.LosslessArrayDeclaration("array.exposed-bad-scratch", ObjectIdentity("raw.exposed-bad-scratch", native.RawReturnedSegment.SCHEMA, "1.0.0", "0" * 64),
        "all_ys", 0, "<f8", (3, 4), 8, sha256(raw).hexdigest())
    class Altered(BytesIO):
        def write(self, value):
            changed = bytes((value[0] ^ 1,)) + value[1:]
            return super().write(changed)
    output = Altered()
    with pytest.raises(ValueError, match="byte tile"):
        r._clock_major(declaration, lambda offset, size: raw[offset:offset + size], lambda: output)
    assert output.closed


def test_direct_working_population_authenticates_old_subjects_without_duplicate_arrays(prepared, tmp_path):
    operand = _operand(prepared, tmp_path / "original", extra_knot=7.5)
    raw, full = operand.frame.raw_return, operand.frame.full_state
    index, typed, sources = encoded_original(raw, full)
    opened = []
    def temporary():
        handle = TemporaryFile(dir=tmp_path, buffering=0)
        opened.append(handle)
        return handle
    decoded_index, decoded, handles = r.decode_raw_segment(r.encode_raw_segment(index, sources), temporary,
        clock_major_working=True)
    try:
        view = r.DecodedFullSegment(typed, decoded_index, decoded, temporary_file=temporary)
        assert decoded_index == index and view.fingerprint() == full.fingerprint()
        assert b"".join(r.full_subject_fragments(typed, view.blocks)) == full.canonical_bytes()
        assert len(opened) == len(index.arrays) == 3 and not view.scratch_handles
        assert sum(handle.seek(0, 2) for handle in opened) == sum(row.size_bytes for row in index.arrays)
        for declaration in index.arrays:
            assert b"".join(decoded[declaration.array_id][0]()) == b"".join(sources[declaration.array_id][0]())
        for actual, original in zip(view.blocks, full.blocks, strict=True):
            assert isinstance(actual.state_binary64, r.ClockMajorView)
            assert isinstance(actual.derivative_binary64, r.ClockMajorView)
            assert tuple(actual.state_binary64) == original.state_binary64
            assert tuple(actual.derivative_binary64) == original.derivative_binary64
            assert sum(map(len, actual.state_binary64.cached.values())) <= 2 * codec.CHUNK_BYTES
    finally:
        for handle in handles:
            handle.close()


@pytest.mark.parametrize("shape", ((35, 127), (3, 8201), (22324, 2)))
@pytest.mark.parametrize("endian", ("<", ">"))
def test_direct_working_layout_preserves_exact_bits_and_unaligned_inverse_ranges(shape, endian):
    rows, width = shape
    # Signed zero and subnormal spellings are observable byte distinctions;
    # the remaining finite values identify both asymmetric axes independently.
    values = (-0., 0., float.fromhex("0x0.0000000000001p-1022"))
    raw = b"".join(struct.pack(endian + "d", values[at] if at < len(values) else float(at))
        for at in range(rows * width))
    declaration = codec.LosslessArrayDeclaration("array.exposed-direct", ObjectIdentity("raw.exposed-direct",
        native.RawReturnedSegment.SCHEMA, "1.0.0", "0" * 64), "all_ys", 0, endian + "f8", shape, 8,
        sha256(raw).hexdigest())
    handle = BytesIO()
    source = r._ClockMajorWorkingSource(declaration, handle)
    for offset in range(0, len(raw), 4093):
        source.write(raw[offset:offset + 4093])
    source.finish()
    assert b"".join(source.chunks()) == raw
    assert handle.getvalue() == b"".join(raw[(row * width + clock) * 8:(row * width + clock + 1) * 8]
        for clock in range(width) for row in range(rows))
    for offset, size in ((0, 0), (1, 13), (7, min(codec.CHUNK_BYTES, len(raw) - 7)), (len(raw) - 17, 17)):
        assert source.read_at(offset, size) == raw[offset:offset + size]
    view = r.ClockMajorView(declaration, handle)
    for at in (0, 1, 2, width - 1, width, rows * width - 1):
        assert view[at] == struct.unpack_from(endian + "d", raw, at * 8)[0].hex()
    assert len(source.pending) == 0 and handle.seek(0, 2) == len(raw)


@pytest.mark.parametrize("failure", ("changed-write", "short-write", "short-read"))
def test_direct_working_population_refuses_altered_scratch(prepared, tmp_path, failure):
    operand = _operand(prepared, tmp_path / "original")
    index, _, sources = encoded_original(operand.frame.raw_return, None)
    opened = []
    class Damaged(BytesIO):
        def write(self, value):
            if failure == "changed-write":
                value = bytes((value[0] ^ 1,)) + value[1:]
            if failure == "short-write":
                return super().write(value[:-1])
            return super().write(value)
        def read(self, size=-1):
            value = super().read(size)
            return value[:-1] if failure == "short-read" else value
    def temporary():
        handle = Damaged() if len(opened) == 1 else BytesIO()
        opened.append(handle)
        return handle
    with pytest.raises(ValueError):
        r.decode_raw_segment(r.encode_raw_segment(index, sources), temporary, clock_major_working=True)
    assert all(handle.closed for handle in opened)
