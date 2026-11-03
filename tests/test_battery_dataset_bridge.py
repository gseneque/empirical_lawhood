# SPDX-License-Identifier: MPL-2.0
"""Exact unreceipted array fixtures; no native source or authority claim."""

from dataclasses import replace
from hashlib import sha256
from io import BytesIO
import struct
import tracemalloc

import pytest

from empirical_lawhood.adapters.methods.battery_refined_inquiry.dataset_bridge import (
    BatteryColumnSource, bridge_lossless_frame, bridge_raw_segment,
)
from empirical_lawhood.adapters.methods.battery_refined_inquiry import lossless_segment_arrays as codec
from empirical_lawhood.adapters.methods.battery_refined_inquiry import lossless_segment_records as records
from empirical_lawhood.adapters.methods.battery_refined_inquiry import preparation_contracts as pc
from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_native as native
from empirical_lawhood.kernel.provenance import ObjectIdentity
from tests.test_battery_lossless_segment_records import encoded_original


def _unexecuted_reference(label, kind):
    # These references expressly supply no authenticated source, execution or
    # completion. Only the exact constructed array subjects are under test.
    return ObjectIdentity("fixture.unexecuted." + label, kind.SCHEMA, kind.VERSION,
        sha256(("disclosed unexecuted fixture " + label).encode()).hexdigest())


def _raw(*, endian="<", derivatives="values", nonfinite=False, empty=False):
    def array(shape, values):
        return native.RawReturnedArray(endian + "f8", shape, 8,
            b"".join(struct.pack(endian + "d", value) for value in values).hex())
    present = ("all_ts", "all_yps", "all_ys")
    clocks, states = (), ()
    derivative = None
    if not empty:
        values = (-0., 0., float.fromhex("0x0.0000000000001p-1022"), 1.25,
            2., 3., 4., 5., 6., 7., 8., 9.)
        if nonfinite:
            values = (float("inf"), *values[1:])
        clocks = (array((4,), (0., .5, 1., 1.5)),)
        states = (array((3, 4), values),)
        derivative = (array((3, 4), tuple(float(at) / 8 for at in range(12))),)
    if derivatives == "absent":
        present = ("all_ts", "all_ys")
        derivative = None
    elif derivatives == "none":
        derivative = None
    elif derivatives == "empty":
        derivative = ()
    return native.RawReturnedSegment("raw.exposed-unreceipted-columns",
        _unexecuted_reference("protocol", pc.PreparationProtocol),
        _unexecuted_reference("request", native.SegmentRequest),
        _unexecuted_reference("returned", native.SegmentReturn), present, clocks, states, derivative)


def _raw_subject(index, source):
    """The unchanged independent historical-subject consumer accepts both sources."""
    arrays = tuple((row, lambda name=row.array_id: source(name)) for row in index.arrays)
    return records.digest_fragments(records.raw_subject_fragments(index.decoded_subject.object_id,
        index.protocol, index.request, index.returned, index.present_attributes, index.block_counts, arrays))


@pytest.mark.parametrize("endian", ("<", ">"))
def test_same_historical_subject_consumer_reads_original_and_shared_named_values(endian):
    raw = _raw(endian=endian)
    index, _, sources = encoded_original(raw, None)
    bridge = bridge_raw_segment(index, sources, maximum_slice_bytes=96)
    assert bridge.raw_index == index and bridge.full_index is None
    assert _raw_subject(index, lambda name: sources[name][0]()) == raw.fingerprint()
    assert _raw_subject(index, bridge.reader.iter_member_bytes) == raw.fingerprint()
    assert index.decoded_subject in bridge.reader.manifest.scientific_references
    for declaration in index.arrays:
        original = b"".join(sources[declaration.array_id][0]())
        assert bridge.reader.read_array(declaration.array_id).tobytes(order="C") == original
        member = next(row for row in bridge.reader.manifest.members if row.name == declaration.array_id)
        assert (member.dtype, member.shape, member.itemsize, member.sha256) == (
            declaration.dtype, declaration.shape, declaration.itemsize, declaration.raw_sha256)
        assert member.finite_required is False
    state, = bridge.member_names("all_ys")
    expected = b"".join(sources[state][0]())[32:64]
    assert bridge.reader.read_array_slice(state, 1, 2).tobytes(order="C") == expected
    verified = bridge.reader.verify_complete()
    assert verified.verified_value_bytes == sum(row.size_bytes for row in index.arrays)
    assert verified.scientific_authority == "NONE" and verified.qualification == "NOT_ESTABLISHED"


@pytest.mark.parametrize("availability", ("absent", "none", "empty", "values"))
def test_original_derivative_and_attribute_availability_survives_named_arrays(availability):
    raw = _raw(derivatives=availability)
    index, _, sources = encoded_original(raw, None)
    bridge = bridge_raw_segment(index, sources, maximum_slice_bytes=96)
    assert bridge.present_attributes == raw.present_attributes
    assert bridge.block_counts == index.block_counts
    names = bridge.member_names("all_yps")
    if availability in ("absent", "none"):
        assert names is None
    else:
        assert names == (() if availability == "empty" else ("array.exposed.all-yps.0",))
    assert _raw_subject(index, bridge.reader.iter_member_bytes) == raw.fingerprint()
    bridge.reader.verify_complete()


def test_empty_complete_population_has_no_invented_member_or_derivative():
    raw = _raw(empty=True, derivatives="none")
    index, _, sources = encoded_original(raw, None)
    bridge = bridge_raw_segment(index, sources, maximum_slice_bytes=8)
    assert bridge.reader.manifest.members == ()
    assert bridge.member_names("all_ts") == () and bridge.member_names("all_ys") == ()
    assert bridge.member_names("all_yps") is None
    assert bridge.reader.verify_complete().verified_value_bytes == 0
    assert _raw_subject(index, bridge.reader.iter_member_bytes) == raw.fingerprint()


def test_none_and_empty_derivatives_retain_different_original_logical_subjects():
    bridges = []
    for availability in ("none", "empty"):
        raw = _raw(derivatives=availability)
        index, _, sources = encoded_original(raw, None)
        bridges.append(bridge_raw_segment(index, sources, maximum_slice_bytes=96))
    assert bridges[0].reader.manifest.members == bridges[1].reader.manifest.members
    assert bridges[0].raw_index.decoded_subject != bridges[1].raw_index.decoded_subject
    assert bridges[0].reader.manifest.identity != bridges[1].reader.manifest.identity


def test_nonfinite_original_bytes_and_signed_zero_are_retained_without_interpretation():
    raw = _raw(nonfinite=True)
    index, _, sources = encoded_original(raw, None)
    bridge = bridge_raw_segment(index, sources, maximum_slice_bytes=96)
    assert _raw_subject(index, bridge.reader.iter_member_bytes) == raw.fingerprint()
    state, = bridge.member_names("all_ys")
    assert bridge.reader.read_array(state).tobytes(order="C") == bytes.fromhex(raw.state_blocks[0].bytes_hex)
    bridge.reader.verify_complete()
    declaration = next(row for row in index.arrays if row.array_id == state)
    with pytest.raises(ValueError, match="nonfinite"):
        records.Binary64View(declaration, sources[state][1])[0]


@pytest.mark.parametrize("damage", ("missing", "extra", "wrong-itemsize", "wrong-dtype", "wrong-source"))
def test_source_and_original_representation_substitution_refuse(damage):
    raw = _raw()
    index, _, sources = encoded_original(raw, None)
    with pytest.raises(ValueError):
        if damage == "missing":
            sources = {key: value for key, value in sources.items() if key != index.arrays[0].array_id}
        elif damage == "extra":
            sources = {**sources, "array.unselected": sources[index.arrays[0].array_id]}
        elif damage == "wrong-itemsize":
            index = replace(index, arrays=(replace(index.arrays[0], itemsize=4), *index.arrays[1:]))
        elif damage == "wrong-dtype":
            index = replace(index, arrays=(replace(index.arrays[0], dtype="|O"), *index.arrays[1:]))
        else:
            index = replace(index, arrays=(replace(index.arrays[0], source=index.protocol), *index.arrays[1:]))
        bridge_raw_segment(index, sources, maximum_slice_bytes=96)


def test_late_changed_state_byte_and_oversized_slice_refuse_fresh_delivery():
    raw = _raw()
    index, _, original = encoded_original(raw, None)
    active = {key: b"".join(value[0]()) for key, value in original.items()}
    sources = {key: (lambda name=key: (active[name],),
        lambda offset, size, name=key: active[name][offset:offset + size]) for key in active}
    bridge = bridge_raw_segment(index, sources, maximum_slice_bytes=32)
    bridge.reader.verify_complete()
    state, = bridge.member_names("all_ys")
    with pytest.raises(ValueError, match="slice.*byte bound"):
        bridge.reader.read_array(state)
    active[state] = active[state][:-1] + bytes((active[state][-1] ^ 1,))
    with pytest.raises(ValueError, match="hash verification"):
        bridge.reader.read_array_slice(state, 0, 1)


def test_existing_decoded_handles_are_reused_without_another_scratch_population():
    raw = _raw()
    index, _, original = encoded_original(raw, None)
    decoded_index, sources, handles = records.decode_raw_segment(records.encode_raw_segment(index, original), BytesIO)
    try:
        bridge = bridge_raw_segment(decoded_index, sources, maximum_slice_bytes=96)
        assert bridge.reader.verify_complete().verified_value_bytes == sum(row.size_bytes for row in index.arrays)
        assert len(handles) == len(index.arrays) == 3
        assert _raw_subject(index, bridge.reader.iter_member_bytes) == raw.fingerprint()
        assert all(not handle.closed for handle in handles)
    finally:
        for handle in handles:
            handle.close()


def test_complete_shared_verification_is_bounded_by_chunk_size_not_population():
    count = 131072
    payload = struct.pack("<d", -0.) + struct.pack("<d", 1.) * (count - 1)
    raw = replace(_raw(derivatives="none"), state_blocks=(native.RawReturnedArray("<f8", (count,), 8, payload.hex()),))
    index, _, sources = encoded_original(raw, None)
    bridge = bridge_raw_segment(index, sources, maximum_slice_bytes=8)
    tracemalloc.start()
    try:
        verified = bridge.reader.verify_complete()
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert verified.verified_value_bytes == len(payload) + 32
    assert peak < 6 * codec.CHUNK_BYTES


def test_bridge_accepts_only_complete_original_frame_types_and_bounded_ranges():
    with pytest.raises(TypeError, match="authenticated lossless frame"):
        bridge_lossless_frame(object(), maximum_slice_bytes=8)
    raw = _raw()
    index, _, sources = encoded_original(raw, None)
    source = BatteryColumnSource(index.arrays, sources)
    name = index.arrays[0].array_id
    assert source.read_member_at(name, 0, 8) == sources[name][1](0, 8)
    for offset, size in ((-1, 8), (0, codec.CHUNK_BYTES + 1), (0, 33), (True, 8)):
        with pytest.raises(ValueError, match="bounded exact"):
            source.read_member_at(name, offset, size)
