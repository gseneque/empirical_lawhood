# SPDX-License-Identifier: MPL-2.0
"""Independent logical-value and adverse-stream controls; no qualification."""

from collections import Counter
from dataclasses import replace
from hashlib import sha256
from math import sqrt
from itertools import permutations
import fcntl
import json
import os
import struct
import tempfile
import tracemalloc

import numpy as np
import pytest

from empirical_lawhood.infrastructure.artifact_stream_primitives import _anonymous_input_descriptor, _seal_anonymous_input
from empirical_lawhood.infrastructure import dataset_readers as shared_reader
from empirical_lawhood.infrastructure.dataset_readers import (
    ArrayDatasetReader, ArrayTransformWriter, AuthenticatedBlockByteSource, DatasetFDMember,
    PhysicalFDByteSource, SealedFDByteSource, VerifiedArrayTransform,
)
from empirical_lawhood.kernel.datasets import ArrayDatasetManifest, ArrayDatasetMember
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.array_datasets import ArrayDatasetReader as ReaderContract


class BytesSource:
    def __init__(self, values, *, block_bytes=17):
        self.values, self.block_bytes, self.opens = dict(values), block_bytes, Counter()

    def open_member(self, name):
        self.opens[name] += 1
        raw = self.values[name]
        return (raw[start:start + self.block_bytes] for start in range(0, len(raw), self.block_bytes))


def case(*, nonfinite=False):
    arrays = {"complex": (np.arange(12) + 1j * np.arange(12)).astype("<c16").reshape(6, 2),
        "empty": np.empty((0, 2), dtype="<f8"), "scalar": np.asarray(1.25, dtype=">f8"),
        "state": np.arange(24, dtype="<f8").reshape(8, 3), "ticks": np.arange(8, dtype="<i8")}
    if nonfinite:
        arrays["state"][7, 2] = np.nan
    raw = {name: value.tobytes(order="C") for name, value in arrays.items()}
    members = tuple(ArrayDatasetMember(name, value.dtype.str, value.shape, sha256(raw[name]).hexdigest(),
        finite_required=not (nonfinite and name == "state")) for name, value in sorted(arrays.items()))
    reference = ObjectIdentity("fixture.exposed.array-context", "empirical-lawhood/tests/exposed-array-context", "1.0.0", "a" * 64)
    manifest = ArrayDatasetManifest("fixture.logical-arrays", members, (reference,))
    source = BytesSource(raw)
    return arrays, manifest, source


def reader(manifest, source, *, slice_bytes=256):
    return ArrayDatasetReader(manifest, source, maximum_chunk_bytes=32, maximum_slice_bytes=slice_bytes)


def test_exact_members_scalar_empty_split_values_and_canonical_roundtrip():
    arrays, manifest, source = case()
    decoded = decode_canonical_bytes(manifest.canonical_bytes(), ArrayDatasetManifest, maximum_bytes=None)
    assert decoded == manifest and decoded.identity == manifest.identity
    actual = reader(decoded, source)
    assert isinstance(actual, ReaderContract)
    for name, expected in arrays.items():
        value = actual.read_array(name)
        assert value.dtype.str == expected.dtype.str and value.shape == expected.shape
        assert value.tobytes(order="C") == expected.tobytes(order="C")
        assert not value.flags.writeable
        with pytest.raises(ValueError):
            value.setflags(write=True)
    selected = actual.read_array_slice("state", 2, 7)
    assert selected.shape == (5, 3) and np.array_equal(selected, arrays["state"][2:7])
    verification = actual.verify_complete()
    assert verification.manifest == manifest.identity
    assert verification.member_hashes == tuple((member.name, member.sha256) for member in manifest.members)
    assert verification.verified_value_bytes == sum(value.nbytes for value in arrays.values())
    assert verification.scientific_authority == "NONE" and verification.qualification == "NOT_ESTABLISHED"


def test_declared_empty_dataset_is_complete_and_cannot_supply_an_undeclared_member():
    manifest = ArrayDatasetManifest("fixture.explicit-empty-dataset", (), ())
    source = BytesSource({})
    actual = ArrayDatasetReader(manifest, source, maximum_chunk_bytes=1, maximum_slice_bytes=1)
    verification = actual.verify_complete()
    assert verification.member_hashes == () and verification.verified_value_bytes == 0 and not source.opens
    with pytest.raises(ValueError, match="undeclared"):
        actual.read_array("not-declared")


@pytest.mark.parametrize("dtype", ("O", "|O8", "=f8", "S8", "U8", "V8", "<M8", "<f16", "<c32"))
def test_unsafe_ambiguous_or_nonportable_dtypes_refuse(dtype):
    with pytest.raises(ValueError, match="safe exact dtype"):
        ArrayDatasetMember("value", dtype, (1,), "a" * 64)


@pytest.mark.parametrize("mutation", ("negative-axis", "boolean-axis", "list-shape", "fortran", "duplicate", "reordered"))
def test_invalid_shape_order_and_complete_member_census_refuse(mutation):
    _, manifest, _ = case()
    first = manifest.members[0]
    with pytest.raises(ValueError):
        if mutation == "negative-axis":
            replace(first, shape=(-1,))
        elif mutation == "boolean-axis":
            replace(first, shape=(True,))
        elif mutation == "list-shape":
            replace(first, shape=[1])
        elif mutation == "fortran":
            replace(first, order="F")
        elif mutation == "duplicate":
            replace(manifest, members=(first, first))
        else:
            replace(manifest, members=tuple(reversed(manifest.members)))


@pytest.mark.parametrize("mutation", ("missing", "truncated", "extra", "changed-value", "wrong-byte-shape", "late-nonfinite"))
def test_complete_preverification_refuses_late_adverse_members_before_any_delivery(mutation):
    _, manifest, source = case()
    last = manifest.members[-1]
    if mutation == "missing":
        del source.values[last.name]
    elif mutation == "truncated":
        source.values[last.name] = source.values[last.name][:-1]
    elif mutation == "extra":
        source.values[last.name] += b"x"
    elif mutation == "changed-value":
        source.values[last.name] = bytes(8) + source.values[last.name][8:]
        # First tick is already0; independently change the last assigned tick.
        source.values[last.name] = source.values[last.name][:-8] + struct.pack("<q", 99)
    elif mutation == "wrong-byte-shape":
        manifest = replace(manifest, members=tuple(replace(member, shape=(7,)) if member == last else member for member in manifest.members))
    else:
        value = np.arange(24, dtype="<f8").reshape(8, 3)
        value[-1, -1] = np.inf
        source.values["state"] = value.tobytes()
        manifest = replace(manifest, members=tuple(replace(member, sha256=sha256(source.values["state"]).hexdigest())
            if member.name == "state" else member for member in manifest.members))
    delivered = reader(manifest, source).iter_member_bytes("complex")
    with pytest.raises(ValueError):
        next(delivered)


def test_explicit_nonfinite_payload_and_missingness_contract_preserve_exact_values():
    arrays, manifest, source = case(nonfinite=True)
    actual = reader(manifest, source)
    value = actual.read_array("state")
    assert value.tobytes() == arrays["state"].tobytes() and np.isnan(value[-1, -1])
    finite = replace(manifest, members=tuple(replace(member, finite_required=True) if member.name == "state" else member for member in manifest.members))
    with pytest.raises(ValueError, match="finite"):
        reader(finite, source).verify_complete()


@pytest.mark.parametrize("block", (b"", bytearray(b"x"), b"x" * 33))
def test_sources_cannot_ignore_selected_byte_block_bounds(block):
    _, manifest, _ = case()
    class InvalidSource:
        def open_member(self, name):
            yield block
    with pytest.raises(ValueError, match="bounded nonempty"):
        reader(manifest, InvalidSource()).verify_complete()


def test_mutated_delivery_is_not_returned_and_final_complete_seal_rechecks_other_members():
    arrays, manifest, source = case()
    class ChangedOnDelivery(BytesSource):
        def open_member(self, name):
            if name == "state" and self.opens[name] == 1:
                self.values[name] = self.values[name][:-8] + struct.pack("<d", 999)
            return super().open_member(name)
    changed = ChangedOnDelivery(source.values)
    with pytest.raises(ValueError, match="value hash"):
        reader(manifest, changed).read_array_slice("state", 0, 1)
    actual = reader(manifest, source)
    selected = actual.read_array_slice("state", 0, 1)
    assert np.array_equal(selected, arrays["state"][:1])
    source.values["ticks"] = source.values["ticks"][:-8] + struct.pack("<q", 99)
    with pytest.raises(ValueError, match="value hash"):
        actual.verify_complete()


@pytest.mark.parametrize("interval", ((-1, 1), (0, 9), (2, 1), (False, 1)))
def test_first_axis_intervals_are_exact_and_do_not_open_sources_on_refusal(interval):
    _, manifest, source = case()
    with pytest.raises(ValueError, match="first-axis"):
        reader(manifest, source).read_array_slice("state", *interval)
    assert not source.opens


def test_selected_slice_limit_refuses_whole_array_before_opening_source():
    _, manifest, source = case()
    actual = reader(manifest, source, slice_bytes=24)
    with pytest.raises(ValueError, match="selected value byte bound"):
        actual.read_array("state")
    assert not source.opens
    assert np.array_equal(actual.read_array_slice("state", 7, 8), np.asarray([[21., 22., 23.]]))
    with pytest.raises(ValueError, match="first-axis"):
        actual.read_array_slice("scalar", 0, 0)


def test_larger_declared_dataset_has_bounded_reader_and_example_reduction_memory():
    # Generated value streams exceed64MiB without materializing that population.
    # This measures the shared reader plus this explicit scalar reduction only;
    # domain assessment-memory acceptance is a separate bridge obligation.
    rows, block = 2**21 + 17, struct.pack("<d", 1.25) * 4096
    size = rows * 4 * 8
    class GeneratedSource:
        opens = 0
        def open_member(self, name):
            assert name == "state"
            self.opens += 1
            remaining = size
            while remaining:
                amount = min(remaining, len(block))
                yield block[:amount]
                remaining -= amount
    source = GeneratedSource()
    digest = sha256()
    for chunk in source.open_member("state"):
        digest.update(chunk)
    source.opens = 0
    manifest = ArrayDatasetManifest("fixture.larger-streamed-dataset",
        (ArrayDatasetMember("state", "<f8", (rows, 4), digest.hexdigest()),), ())
    assert manifest.size_bytes > 64 * 1024**2
    actual = ArrayDatasetReader(manifest, source, maximum_chunk_bytes=len(block), maximum_slice_bytes=65536)
    with pytest.raises(ValueError, match="selected value byte bound"):
        actual.read_array("state")
    assert source.opens == 0
    tracemalloc.start()
    try:
        selected = actual.read_array_slice("state", rows - 2, rows)
        norm = float(np.linalg.norm(selected))
        verification = actual.verify_complete()
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert norm == pytest.approx(1.25 * sqrt(8)) and selected.shape == (2, 4)
    assert verification.verified_value_bytes == size and source.opens == 3
    assert peak < 2 * 1024**2


class RegularFileSource:
    """Independent existing file leases, without a cache or extra population."""

    def __init__(self, values, *, block_bytes=17):
        self.files, self.opens, self.ranges, self.closed = {}, Counter(), [], False
        self.block_bytes = block_bytes
        for name, value in values.items():
            handle = tempfile.TemporaryFile()
            handle.write(value)
            handle.flush()
            self.files[name] = handle

    def open_member(self, name):
        self.opens[name] += 1
        handle = self.files[name]
        length = os.fstat(handle.fileno()).st_size
        return (os.pread(handle.fileno(), min(self.block_bytes, length - start), start)
            for start in range(0, length, self.block_bytes))

    def read_range(self, name, start, stop):
        self.ranges.append((name, start, stop))
        return os.pread(self.files[name].fileno(), stop - start, start)

    def change(self, name, offset, value):
        os.pwrite(self.files[name].fileno(), value, offset)

    def close(self):
        self.closed = True
        for handle in self.files.values():
            handle.close()

    def authenticated(self, *, read_range=None):
        return AuthenticatedBlockByteSource(self, read_range=read_range or self.read_range, close=self.close)


def test_authenticated_session_full_scan_twice_and_only_touched_ranges_between():
    arrays, manifest, values = case()
    source = RegularFileSource(values.values)
    actual = reader(manifest, source.authenticated(), slice_bytes=48)
    with actual.verified_session(block_size_bytes=64) as session:
        assert source.opens == Counter({name: 1 for name in arrays})
        for _ in range(20):
            assert session.read_elements("state", 10, 11).tolist() == [10.]
        assert session.read_member_bytes("state", 61, 67) == arrays["state"].tobytes()[61:67]
        assert np.array_equal(session.read_array_slice("state", 6, 8), arrays["state"][6:8])
        assert session.read_array("scalar").item() == 1.25
        assert session.read_array("empty").shape == (0, 2)
        assert session.read_elements("empty", 0, 0).size == 0
        # Each scalar touches one complete64-byte block; the cross-boundary
        # byte range touches two, and two final rows touch one.
        assert source.ranges == [("state", 64, 128)] * 20 + [
            ("state", 0, 64), ("state", 64, 128), ("state", 128, 192), ("scalar", 0, 8)]
        seal = session.verify_complete()
        assert source.opens == Counter({name: 2 for name in arrays})
        assert session.verify_complete() is seal
        with pytest.raises(ValueError, match="already sealed"):
            session.read_elements("state", 0, 1)
    assert source.closed and session.final_verification is seal
    assert seal.scientific_authority == "NONE" and seal.qualification == "NOT_ESTABLISHED"
    assert source.opens == Counter({name: 2 for name in arrays})
    with pytest.raises(ValueError, match="closed"):
        session.verify_complete()


def test_authenticated_streaming_bound_is_independent_of_materialized_slice_bound():
    arrays, manifest, values = case()
    source = RegularFileSource(values.values)
    with reader(manifest, source.authenticated(), slice_bytes=8).verified_session(block_size_bytes=64) as session:
        chunks = tuple(session.iter_member_bytes("complex"))
        assert b"".join(chunks) == arrays["complex"].tobytes()
        assert all(0 < len(value) <= 32 for value in chunks)
        with pytest.raises(ValueError, match="selected value byte bound"):
            session.read_array_slice("state", 0, 1)
    assert source.closed


@pytest.mark.parametrize("moment", ("early", "touched", "unused-late", "restored-after-refusal"))
def test_authenticated_session_mutations_never_return_a_successful_final_seal(moment):
    arrays, manifest, values = case()
    source = RegularFileSource(values.values)
    original = arrays["state"].tobytes()[:8]
    if moment == "early":
        source.change("state", 0, struct.pack("<d", 999))
    with pytest.raises(ValueError, match="value hash|touched block|refused"):
        with reader(manifest, source.authenticated()).verified_session(block_size_bytes=64) as session:
            if moment == "unused-late":
                session.read_elements("state", 0, 1)
                source.change("ticks", 0, struct.pack("<q", 999))
            elif moment == "restored-after-refusal":
                source.change("state", 0, struct.pack("<d", 999))
                with pytest.raises(ValueError, match="touched block"):
                    session.read_elements("state", 0, 1)
                source.change("state", 0, original)
                session.verify_complete()
            else:
                source.change("state", 0, struct.pack("<d", 999))
                session.read_elements("state", 0, 1)
    assert source.closed


def test_authenticated_delivery_change_is_observed_even_if_restored_before_finalization():
    arrays, manifest, values = case()
    source = RegularFileSource(values.values)
    def changed_delivery(name, start, stop):
        raw = source.read_range(name, start, stop)
        if name == "state":
            return struct.pack("<d", 999) + raw[8:]
        return raw
    with pytest.raises(ValueError, match="touched block"):
        with reader(manifest, source.authenticated(read_range=changed_delivery)).verified_session(block_size_bytes=64) as session:
            session.read_elements("state", 0, 1)
    assert source.closed and arrays["state"][0, 0] == 0


@pytest.mark.parametrize("replacement", ({}, {"state": ()}))
def test_authenticated_session_rejects_replaced_or_incomplete_digest_index(replacement):
    _, manifest, values = case()
    source = RegularFileSource(values.values)
    with reader(manifest, source.authenticated()).verified_session(block_size_bytes=64) as session:
        with pytest.raises(AttributeError, match="read-only"):
            session._index = replacement
        assert session.read_elements("state", 0, 1).tolist() == [0.]
    assert source.closed


@pytest.mark.parametrize("bad", (b"", bytearray(b"x" * 64), b"x" * 65))
def test_authenticated_range_callback_must_return_exact_complete_block_bytes(bad):
    _, manifest, values = case()
    source = RegularFileSource(values.values)
    with pytest.raises(ValueError, match="touched block"):
        with reader(manifest, source.authenticated(read_range=lambda *args: bad)).verified_session(block_size_bytes=64) as session:
            session.read_elements("state", 0, 1)
    assert source.closed


def test_plain_source_labels_never_activate_immutable_or_block_capability():
    _, manifest, source = case()
    source.immutable, source.sealed = True, True
    with pytest.raises(ValueError, match="value hash"):
        with reader(manifest, source).verified_session(block_size_bytes=64) as session:
            assert session.read_elements("state", 0, 1).tolist() == [0.]
            assert source.opens["state"] == 3  # initial, fresh preverify, delivery
            source.values["ticks"] = struct.pack("<q", 999) + source.values["ticks"][8:]
            session.read_elements("state", 0, 1)


def test_sealed_descriptor_session_reuses_existing_bytes_and_closes_only_owned_duplicates():
    arrays, manifest, values = case()
    descriptor = _anonymous_input_descriptor()
    members, cursor = {}, 0
    try:
        whole = b"".join(values.values[name] for name in sorted(values.values))
        os.write(descriptor, whole)
        _seal_anonymous_input(descriptor)
        for name in sorted(values.values):
            raw = values.values[name]
            members[name] = DatasetFDMember(descriptor, cursor, len(raw), len(whole))
            cursor += len(raw)
        source = SealedFDByteSource(members, maximum_chunk_bytes=17)
        try:
            with reader(manifest, source).verified_session(block_size_bytes=64) as session:
                leased = tuple(session._source._descriptors.values())
                assert np.array_equal(session.read_array_slice("state", 1, 4), arrays["state"][1:4])
                assert session.read_elements("ticks", 3, 5).tolist() == [3, 4]
                assert session.read_array("scalar").item() == 1.25
                assert session.read_array("empty").shape == (0, 2)
                with pytest.raises(OSError):
                    os.pwrite(descriptor, b"x", 0)
            assert session.final_verification.verified_value_bytes == len(whole)
            for owned in leased:
                with pytest.raises(OSError):
                    os.fstat(owned)
            assert os.pread(descriptor, len(whole), 0) == whole
            assert source.read_member_range("state", 0, 8) == arrays["state"].tobytes()[:8]
        finally:
            source.close()
    finally:
        os.close(descriptor)


@pytest.mark.parametrize("seals", (0, 1, 7, 14))
def test_descriptor_capability_requires_actual_complete_seals(seals):
    descriptor = _anonymous_input_descriptor()
    try:
        os.write(descriptor, b"12345678")
        if seals:
            fcntl.fcntl(descriptor, getattr(fcntl, "F_ADD_SEALS", 1033), seals)
        with pytest.raises(ValueError, match="seals"):
            SealedFDByteSource({"state": DatasetFDMember(descriptor, 0, 8, 8)}, maximum_chunk_bytes=8)
        assert os.fstat(descriptor).st_size == 8
    finally:
        os.close(descriptor)


def test_regular_file_or_wrong_extent_cannot_claim_immutable_descriptor_capability():
    with tempfile.TemporaryFile() as handle:
        handle.write(b"12345678")
        handle.flush()
        with pytest.raises(ValueError, match="protections"):
            SealedFDByteSource({"state": DatasetFDMember(handle.fileno(), 0, 8, 8)}, maximum_chunk_bytes=8)
    descriptor = _anonymous_input_descriptor()
    try:
        os.write(descriptor, b"12345678")
        _seal_anonymous_input(descriptor)
        with pytest.raises(ValueError, match="extent"):
            SealedFDByteSource({"state": DatasetFDMember(descriptor, 0, 8, 9)}, maximum_chunk_bytes=8)
    finally:
        os.close(descriptor)


def test_sealed_member_intervals_and_values_still_require_the_complete_manifest():
    _, manifest, _ = case()
    descriptor = _anonymous_input_descriptor()
    try:
        os.write(descriptor, b"12345678")
        _seal_anonymous_input(descriptor)
        source = SealedFDByteSource({"scalar": DatasetFDMember(descriptor, 0, 8, 8)}, maximum_chunk_bytes=8)
        try:
            with pytest.raises(ValueError, match="member census"):
                with reader(manifest, source).verified_session(block_size_bytes=64):
                    pytest.fail("incomplete manifest must refuse before lease exposure")
            wrong_values = replace(manifest, members=(manifest.members[2],))
            with pytest.raises(ValueError, match="value hash"):
                with reader(wrong_values, source).verified_session(block_size_bytes=64):
                    pytest.fail("sealed values still require their original scientific value hash")
        finally:
            source.close()
    finally:
        os.close(descriptor)


def test_empty_session_finalizes_without_inventing_a_missing_member():
    manifest = ArrayDatasetManifest("fixture.empty-session", (), ())
    source = RegularFileSource({})
    with ArrayDatasetReader(manifest, source.authenticated(), maximum_chunk_bytes=1,
            maximum_slice_bytes=1).verified_session(block_size_bytes=1) as session:
        assert session.manifest.members == ()
    assert session.final_verification.verified_value_bytes == 0 and source.closed


def test_verified_session_large_population_scalar_reads_have_two_whole_scans():
    rows, block = 2**21 + 17, struct.pack("<d", 1.25) * 4096
    size = rows * 4 * 8
    class GeneratedRanges:
        def __init__(self):
            self.whole_bytes, self.range_bytes, self.opens, self.closed = 0, 0, 0, False
        def open_member(self, name):
            assert name == "state"
            self.opens += 1
            for start in range(0, size, len(block)):
                raw = block[:min(len(block), size - start)]
                self.whole_bytes += len(raw)
                yield raw
        def read_range(self, name, start, stop):
            self.range_bytes += stop - start
            return (struct.pack("<d", 1.25) * ((stop - start + 15) // 8))[start % 8:start % 8 + stop - start]
        def close(self):
            self.closed = True
    source, digest = GeneratedRanges(), sha256()
    for payload in source.open_member("state"):
        digest.update(payload)
    source.opens = source.whole_bytes = 0
    manifest = ArrayDatasetManifest("fixture.large-session", (
        ArrayDatasetMember("state", "<f8", (rows, 4), digest.hexdigest()),), ())
    actual = ArrayDatasetReader(manifest, AuthenticatedBlockByteSource(source, read_range=source.read_range,
        close=source.close), maximum_chunk_bytes=len(block), maximum_slice_bytes=64)
    tracemalloc.start()
    try:
        with actual.verified_session(block_size_bytes=65536) as session:
            for at in range(100):
                assert session.read_elements("state", at * 1000, at * 1000 + 1).tolist() == [1.25]
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert source.opens == 2 and source.whole_bytes == 2 * size and source.range_bytes == 100 * 65536
    assert source.closed and peak < 2 * 1024**2


def test_active_mutable_iterator_is_invalidated_when_its_session_closes():
    _, manifest, source = case()
    with reader(manifest, source).verified_session(block_size_bytes=64) as session:
        delivered = session.iter_member_bytes("state")
        assert next(delivered)
    with pytest.raises(ValueError, match="closed"):
        next(delivered)


def transformed_case(arrays, axis_orders, *, finite_required=True, block_size_bytes=32):
    manifest = ArrayDatasetManifest("fixture.transformed-dataset", tuple(
        ArrayDatasetMember(name, array.dtype.str, array.shape, sha256(array.tobytes()).hexdigest(), finite_required)
        for name, array in sorted(arrays.items())), ())
    handles, witnesses = {}, {}
    try:
        for member in manifest.members:
            handle = tempfile.TemporaryFile()
            handle.truncate(member.size_bytes)
            handles[member.name] = handle
            writer = ArrayTransformWriter(manifest, member.name,
                DatasetFDMember(handle.fileno(), 0, member.size_bytes, member.size_bytes),
                axis_order=axis_orders[member.name], block_size_bytes=block_size_bytes, maximum_chunk_bytes=17)
            try:
                raw = arrays[member.name].tobytes()
                for at in range(0, len(raw), 17):
                    assert writer.write(raw[at:at + 17]) == min(17, len(raw) - at)
                witnesses[member.name] = writer.finish()
            finally:
                writer.close()
        return manifest, handles, witnesses
    except BaseException:
        for witness in witnesses.values():
            witness.close()
        for handle in handles.values():
            handle.close()
        raise


@pytest.mark.parametrize("axis_order", tuple(permutations(range(3))))
def test_actual_transform_all_nonsquare_three_dimensional_permutations(axis_order):
    expected = np.arange(2 * 3 * 5, dtype=">i2").reshape(2, 3, 5)
    manifest, handles, witnesses = transformed_case({"state": expected}, {"state": axis_order})
    try:
        assert os.pread(handles["state"].fileno(), expected.nbytes, 0) == expected.transpose(axis_order).tobytes()
        source = PhysicalFDByteSource(manifest, witnesses, maximum_chunk_bytes=17, maximum_cache_bytes=64)
        with reader(manifest, source).verified_session(block_size_bytes=32) as session:
            assert session.read_array("state").tobytes() == expected.tobytes()
            assert session.read_member_bytes("state", 3, 29) == expected.tobytes()[3:29]
            assert session.read_elements("state", 4, 13).tobytes() == expected.reshape(-1)[4:13].tobytes()
        assert session.final_verification.manifest == manifest.identity
    finally:
        for witness in witnesses.values():
            witness.close()
        for handle in handles.values():
            handle.close()


@pytest.mark.parametrize("identity_order", (False, True))
def test_transform_preserves_scalar_empty_complex_endian_signed_zero_and_nan_payload(identity_order):
    nan_bits = np.asarray([0, 1 << 63, 0x7FF800000000005A, 0x7FF0000000000000], dtype="<u8")
    arrays = {"bits": nan_bits.view("<f8").reshape(2, 2),
        "complex": np.asarray([complex(1, -2), complex(0, 4)], dtype=">c16").reshape(1, 2),
        "empty": np.empty((0, 3), dtype="<f8"), "scalar": np.asarray(-0., dtype=">f8")}
    axis_orders = {name: tuple(range(value.ndim)) if identity_order else tuple(reversed(range(value.ndim)))
        for name, value in arrays.items()}
    manifest, handles, witnesses = transformed_case(arrays, axis_orders, finite_required=False)
    try:
        source = PhysicalFDByteSource(manifest, witnesses, maximum_chunk_bytes=17, maximum_cache_bytes=64)
        with reader(manifest, source).verified_session(block_size_bytes=32) as session:
            for name, expected in arrays.items():
                value = session.read_array(name)
                assert value.dtype.str == expected.dtype.str and value.shape == expected.shape
                assert value.tobytes() == expected.tobytes() and not value.flags.writeable
                if expected.nbytes:
                    assert session.read_member_bytes(name, 1, expected.nbytes - 1) == expected.tobytes()[1:-1]
            assert session.read_member_bytes("empty", 0, 0) == b""
    finally:
        for handle in handles.values():
            handle.close()


@pytest.mark.parametrize("mutation", ("before-finish", "after-finish-touched", "after-finish-unused", "cached"))
@pytest.mark.parametrize("axis_order", ((0, 1), (1, 0)))
def test_transform_mutations_refuse_actual_admission_or_final_seal(mutation, axis_order):
    expected = np.arange(24, dtype="<f8").reshape(8, 3)
    manifest = ArrayDatasetManifest("fixture.mutation-transform", (
        ArrayDatasetMember("state", "<f8", expected.shape, sha256(expected.tobytes()).hexdigest()),), ())
    with tempfile.TemporaryFile() as handle:
        handle.truncate(expected.nbytes)
        writer = ArrayTransformWriter(manifest, "state", DatasetFDMember(handle.fileno(), 0, expected.nbytes, expected.nbytes),
            axis_order=axis_order, block_size_bytes=64, maximum_chunk_bytes=expected.nbytes)
        try:
            writer.write(expected.tobytes())
            if mutation == "before-finish":
                os.pwrite(handle.fileno(), struct.pack("<d", 999), 0)
                with pytest.raises(ValueError, match="actual physical bytes"):
                    writer.finish()
                return
            witness = writer.finish()
        finally:
            writer.close()
        source = PhysicalFDByteSource(manifest, {"state": witness}, maximum_chunk_bytes=32, maximum_cache_bytes=128)
        if mutation == "after-finish-touched":
            os.pwrite(handle.fileno(), struct.pack("<d", 999), 0)
        with pytest.raises(ValueError, match="touched block|final whole seal"):
            with reader(manifest, source).verified_session(block_size_bytes=64) as session:
                if mutation == "cached":
                    assert session.read_elements("state", 0, 1).tolist() == [0.]
                    os.pwrite(handle.fileno(), struct.pack("<d", 999), 0)
                    # An authenticated immutable cache returns the admission
                    # snapshot; successful exit still requires all current bytes.
                    assert session.read_elements("state", 0, 1).tolist() == [0.]
                elif mutation == "after-finish-unused":
                    os.pwrite(handle.fileno(), struct.pack("<d", 999), 128)
                    assert session.read_elements("state", 0, 1).tolist() == [0.]
                else:
                    session.read_elements("state", 0, 1)


@pytest.mark.parametrize("mutation", ("partial", "reordered", "duplicate", "nonfinite"))
def test_transform_original_ingest_census_and_values_must_match(mutation):
    expected = np.arange(8, dtype="<f8").reshape(2, 4)
    manifest = ArrayDatasetManifest("fixture.invalid-ingest", (
        ArrayDatasetMember("state", "<f8", expected.shape, sha256(expected.tobytes()).hexdigest()),), ())
    with tempfile.TemporaryFile() as handle:
        handle.truncate(expected.nbytes)
        writer = ArrayTransformWriter(manifest, "state", DatasetFDMember(handle.fileno(), 0, expected.nbytes, expected.nbytes),
            axis_order=(1, 0), block_size_bytes=32, maximum_chunk_bytes=expected.nbytes)
        try:
            with pytest.raises(ValueError, match="hash|byte census|finite"):
                raw = expected.tobytes()
                if mutation == "partial":
                    writer.write(raw[:-1])
                elif mutation == "reordered":
                    writer.write(raw[32:] + raw[:32])
                elif mutation == "duplicate":
                    writer.write(raw)
                    writer.write(raw)
                else:
                    writer.write(struct.pack("<d", float("nan")) + raw[8:])
                writer.finish()
        finally:
            writer.close()


@pytest.mark.parametrize("axis_order", ((0, 0), (1,), (0, 2), (False, 1), [1, 0]))
def test_transform_rejects_nonbijective_or_ambiguous_axis_mapping(axis_order):
    expected = np.arange(6, dtype="<i8").reshape(2, 3)
    manifest = ArrayDatasetManifest("fixture.invalid-permutation", (
        ArrayDatasetMember("state", "<i8", expected.shape, sha256(expected.tobytes()).hexdigest()),), ())
    with tempfile.TemporaryFile() as handle:
        handle.truncate(expected.nbytes)
        with pytest.raises(ValueError, match="axis permutation"):
            ArrayTransformWriter(manifest, "state", DatasetFDMember(handle.fileno(), 0, expected.nbytes, expected.nbytes),
                axis_order=axis_order, block_size_bytes=32, maximum_chunk_bytes=17)


def test_transform_witness_is_not_publicly_forgeable_reusable_or_detached_from_source():
    with pytest.raises(TypeError, match="minted"):
        VerifiedArrayTransform(None, None, None, None)
    expected = np.arange(6, dtype="<i8").reshape(2, 3)
    manifest, handles, witnesses = transformed_case({"state": expected}, {"state": (1, 0)})
    try:
        with pytest.raises(ValueError, match="source associations"):
            PhysicalFDByteSource(replace(manifest, dataset_id="fixture.substituted-source"), witnesses,
                maximum_chunk_bytes=32, maximum_cache_bytes=64)
        source = PhysicalFDByteSource(manifest, witnesses, maximum_chunk_bytes=32, maximum_cache_bytes=64)
        with pytest.raises(ValueError, match="consumed"):
            PhysicalFDByteSource(manifest, witnesses, maximum_chunk_bytes=32, maximum_cache_bytes=64)
        with reader(manifest, source).verified_session(block_size_bytes=32):
            pass
        with pytest.raises(ValueError, match="closed"):
            with reader(manifest, source).verified_session(block_size_bytes=32):
                pytest.fail("a transform lease cannot open a second session")
        assert os.fstat(handles["state"].fileno()).st_size == expected.nbytes
    finally:
        for handle in handles.values():
            handle.close()


@pytest.mark.parametrize("axis_order", ((0, 1), (1, 0)))
def test_physical_lease_descriptor_number_reuse_and_extent_changes_cannot_substitute_input(axis_order):
    expected = np.arange(6, dtype="<i8").reshape(2, 3)
    manifest, handles, witnesses = transformed_case({"state": expected}, {"state": axis_order})
    source = PhysicalFDByteSource(manifest, witnesses, maximum_chunk_bytes=32, maximum_cache_bytes=64)
    # Closing the caller's original descriptor does not close or substitute
    # the owned duplicate, even if another file takes the same integer slot.
    handles["state"].close()
    with tempfile.TemporaryFile() as other:
        other.write(b"x" * expected.nbytes)
        other.flush()
        with reader(manifest, source).verified_session(block_size_bytes=32) as session:
            assert session.read_array("state").tobytes() == expected.tobytes()
    manifest, handles, witnesses = transformed_case({"state": expected}, {"state": axis_order})
    try:
        source = PhysicalFDByteSource(manifest, witnesses, maximum_chunk_bytes=32, maximum_cache_bytes=64)
        handles["state"].truncate(expected.nbytes - 1)
        with pytest.raises(ValueError, match="exact extent"):
            with reader(manifest, source).verified_session(block_size_bytes=32):
                pytest.fail("extent changes must refuse before lease exposure")
    finally:
        for handle in handles.values():
            handle.close()


def test_physical_explicit_empty_manifest_has_a_complete_empty_lease():
    manifest = ArrayDatasetManifest("fixture.empty-transformed", (), ())
    source = PhysicalFDByteSource(manifest, {}, maximum_chunk_bytes=1, maximum_cache_bytes=0)
    with ArrayDatasetReader(manifest, source, maximum_chunk_bytes=1,
            maximum_slice_bytes=1).verified_session(block_size_bytes=1) as session:
        pass
    assert session.final_verification.verified_value_bytes == 0


def test_physical_transform_actual_reads_hashing_and_digest_state_memory(monkeypatch, tmp_path):
    # Observe actual primitive calls; no bytes, numerical result, verification
    # outcome or source authority is replaced. Both raw populations are
    # generated in bounded tiles into their already selected working files.
    original_read, original_write, original_stat, original_hash = os.pread, os.pwrite, os.fstat, sha256
    counters = Counter()
    def observed_read(descriptor, size, offset):
        result = original_read(descriptor, size, offset)
        counters["physical_read_bytes"] += len(result)
        counters["physical_read_calls"] += 1
        return result
    def observed_write(descriptor, payload, offset):
        count = original_write(descriptor, payload, offset)
        counters["physical_write_bytes"] += count
        counters["physical_write_calls"] += 1
        return count
    def observed_stat(descriptor):
        counters["fstat_calls"] += 1
        return original_stat(descriptor)
    class ObservedHash:
        def __init__(self, payload=b""):
            self.actual = original_hash(payload)
            counters["hash_value_bytes"] += len(payload)
        def update(self, payload):
            counters["hash_value_bytes"] += len(payload)
            self.actual.update(payload)
        def hexdigest(self):
            return self.actual.hexdigest()
    monkeypatch.setattr(shared_reader.os, "pread", observed_read)
    monkeypatch.setattr(shared_reader.os, "pwrite", observed_write)
    monkeypatch.setattr(shared_reader.os, "fstat", observed_stat)
    monkeypatch.setattr(shared_reader, "sha256", ObservedHash)
    records, tile_elements, block_size = [], 1024, 65536
    for rows, clocks in ((1025, 17), (8193, 65), (37, 129), (37, 1025)):
        elements, size = rows * clocks, rows * clocks * 8
        def value_tiles():
            for start in range(0, elements, tile_elements):
                yield (np.arange(start, min(start + tile_elements, elements), dtype="<f8") * .125).tobytes()
        oracle = original_hash()
        for payload in value_tiles():
            oracle.update(payload)
        manifest = ArrayDatasetManifest("fixture.measured-transform", (
            ArrayDatasetMember("state", "<f8", (rows, clocks), oracle.hexdigest()),), ())
        with tempfile.TemporaryFile() as handle:
            handle.truncate(size)
            counters.clear()
            max_live_states = 0
            tracemalloc.start()
            try:
                writer = ArrayTransformWriter(manifest, "state", DatasetFDMember(handle.fileno(), 0, size, size),
                    axis_order=(1, 0), block_size_bytes=block_size, maximum_chunk_bytes=tile_elements * 8)
                try:
                    for payload in value_tiles():
                        writer.write(payload)
                        max_live_states = max(max_live_states, len(writer._states))
                    witness = writer.finish()
                finally:
                    writer.close()
                blocks = len(witness._blocks)
                admission = dict(counters)
                source = PhysicalFDByteSource(manifest, {"state": witness}, maximum_chunk_bytes=tile_elements * 8,
                    maximum_cache_bytes=2 * block_size)
                with ArrayDatasetReader(manifest, source, maximum_chunk_bytes=tile_elements * 8,
                        maximum_slice_bytes=64).verified_session(block_size_bytes=block_size) as session:
                    for row in range(min(rows, 128)):
                        for clock in (5, 6):
                            index = row * clocks + clock
                            assert session.read_elements("state", index, index + 1).tolist() == [index * .125]
                _, peak = tracemalloc.get_traced_memory()
            finally:
                tracemalloc.stop()
            touched_bytes = 2 * min(rows * 8, block_size)
            expected_blocks = clocks * ((rows * 8 + block_size - 1) // block_size)
            assert blocks == expected_blocks and max_live_states <= clocks
            assert admission["physical_read_bytes"] == size
            assert counters["physical_read_bytes"] == 2 * size + touched_bytes
            assert counters["physical_read_calls"] == 2 * blocks + 2
            assert counters["physical_write_bytes"] == size
            assert counters["hash_value_bytes"] == 4 * size + touched_bytes
            # Narrow physical rows require one state/index row per clock;
            # neither digest-state memory nor index bytes are hidden here.
            assert peak < 2 * 1024**2
            records.append({"logical_shape": [rows, clocks], "physical_shape": [clocks, rows],
                "value_bytes": size, "block_size_bytes": block_size, "incoming_tile_bytes": tile_elements * 8,
                "snapshot_cache_bytes": 2 * block_size, "physical_blocks": blocks,
                "max_live_digest_states_observed_after_tile": max_live_states,
                "peak_traced_bytes": peak, "admission": admission, "complete": dict(counters)})
    report = {"scope": "actual generic transform admission, adjacent-clock scalar reads, and final physical seal; no scientific assessment or authority",
        "index_bound": "physical rows times ceil(last physical axis byte width / block size)",
        "digest_work": "logical ingest + expected mapped physical bytes + actual admission scan + actual final scan + touched cache misses",
        "cases": records}
    (tmp_path / "physical-transform-scaling.json").write_text(json.dumps(report, indent=2) + "\n")


@pytest.mark.parametrize("spent", (False, True))
def test_admitted_transform_witness_proof_fields_cannot_be_rebound(spent):
    expected = np.arange(8, dtype="<f8").reshape(2, 4)
    manifest, handles, witnesses = transformed_case({"state": expected}, {"state": (1, 0)})
    witness = witnesses["state"]
    source = PhysicalFDByteSource(manifest, witnesses, maximum_chunk_bytes=32, maximum_cache_bytes=64) if spent else None
    try:
        os.pwrite(handles["state"].fileno(), struct.pack("<d", 999), 0)
        for field, replacement in (("_manifest", replace(manifest, dataset_id="fixture.forged").identity),
                ("_blocks", ()), ("_binding", None), ("_spent", False)):
            with pytest.raises(AttributeError, match="read-only"):
                setattr(witness, field, replacement)
        if source is None:
            source = PhysicalFDByteSource(manifest, witnesses, maximum_chunk_bytes=32, maximum_cache_bytes=64)
        with pytest.raises(ValueError, match="touched block"):
            with reader(manifest, source).verified_session(block_size_bytes=32) as session:
                session.read_elements("state", 0, 1)
    finally:
        if source is not None:
            source.close()
        witness.close()
        for handle in handles.values():
            handle.close()


@pytest.mark.parametrize("axis_order", ((0, 1), (1, 0)))
def test_physical_admitted_source_proof_and_cache_replacements_cannot_forge_values(axis_order):
    expected = np.arange(8, dtype="<f8").reshape(2, 4)
    manifest, handles, witnesses = transformed_case({"state": expected}, {"state": axis_order})
    source = PhysicalFDByteSource(manifest, witnesses, maximum_chunk_bytes=32, maximum_cache_bytes=64)
    try:
        with pytest.raises(ValueError, match="snapshot cache"):
            with reader(manifest, source).verified_session(block_size_bytes=32) as session:
                assert session.read_elements("state", 0, 1).tolist() == [0.]
                for field, replacement in (("_indexes", {"state": ()}), ("_bindings", {}), ("_starts", {}),
                        ("_manifest", replace(manifest, dataset_id="fixture.forged").identity), ("_closed", False), ("_leased", False)):
                    with pytest.raises(AttributeError, match="read-only"):
                        setattr(source, field, replacement)
                with pytest.raises(TypeError):
                    source._indexes["state"] = ()
                cached = source._cache[("state", 0)]
                with pytest.raises(AttributeError):
                    cached.payload = b"x" * len(cached.payload)
                source._cache[("state", 0)] = b"x" * 16
                session.read_elements("state", 0, 1)
    finally:
        source.close()
        for handle in handles.values():
            handle.close()


@pytest.mark.parametrize("interval", ((False, 1), (0., 8), (-1, 1), (8, 0), (0, 99)))
@pytest.mark.parametrize("axis_order", ((0, 1), (1, 0)))
def test_physical_source_direct_range_is_an_exact_byte_interval(interval, axis_order):
    expected = np.arange(8, dtype="<f8").reshape(2, 4)
    manifest, handles, witnesses = transformed_case({"state": expected}, {"state": axis_order})
    source = PhysicalFDByteSource(manifest, witnesses, maximum_chunk_bytes=32, maximum_cache_bytes=64)
    try:
        with pytest.raises(ValueError, match="exact original value interval"):
            source.read_member_range("state", *interval)
    finally:
        source.close()
        for handle in handles.values():
            handle.close()


@pytest.mark.parametrize("axis_order", ((0, 1), (1, 0)))
def test_ordinary_physical_reader_complete_verification_cannot_trust_cached_old_bytes(axis_order):
    expected = np.arange(8, dtype="<f8").reshape(2, 4)
    manifest, handles, witnesses = transformed_case({"state": expected}, {"state": axis_order})
    source = PhysicalFDByteSource(manifest, witnesses, maximum_chunk_bytes=32, maximum_cache_bytes=64)
    try:
        assert source.read_member_range("state", 0, 8) == expected.tobytes()[:8]
        os.pwrite(handles["state"].fileno(), struct.pack("<d", 999), 0)
        with pytest.raises(ValueError, match="final whole seal"):
            reader(manifest, source).verify_complete()
    finally:
        source.close()
        for handle in handles.values():
            handle.close()


def test_transform_writer_proof_cannot_be_rebound_before_witness_admission():
    expected = np.arange(8, dtype="<f8").reshape(2, 4)
    manifest = ArrayDatasetManifest("fixture.unforgeable-writer", (
        ArrayDatasetMember("state", "<f8", expected.shape, sha256(expected.tobytes()).hexdigest()),), ())
    with tempfile.TemporaryFile() as handle:
        handle.truncate(expected.nbytes)
        writer = ArrayTransformWriter(manifest, "state", DatasetFDMember(handle.fileno(), 0, expected.nbytes, expected.nbytes),
            axis_order=(1, 0), block_size_bytes=32, maximum_chunk_bytes=32)
        try:
            writer.write(expected.tobytes()[:32])
            for field, replacement in (("_digest", None), ("_count", expected.nbytes), ("_binding", None),
                    ("_blocks", {}), ("_states", {}), ("_closed", False), ("_refused", False)):
                with pytest.raises(AttributeError, match="read-only"):
                    setattr(writer, field, replacement)
            state = next(iter(writer._states.values()))
            with pytest.raises(AttributeError):
                state.count = 32
            with pytest.raises(TypeError):
                writer._blocks[0] = None
            writer.write(expected.tobytes()[32:])
            os.pwrite(handle.fileno(), struct.pack("<d", 999), 0)
            with pytest.raises(ValueError, match="actual physical bytes"):
                writer.finish()
        finally:
            writer.close()


@pytest.mark.parametrize("axis_order", tuple(permutations(range(3))))
def test_permuted_view_generic_and_differently_packed_physical_sources_have_exact_bytes(axis_order):
    array = np.arange(30, dtype=">i2").reshape(2, 3, 5)
    manifest, handles, witnesses = transformed_case({"state": array}, {"state": (2, 0, 1)})
    expected = array.transpose(axis_order).tobytes()
    try:
        sources = (BytesSource({"state": array.tobytes()}),
            PhysicalFDByteSource(manifest, witnesses, maximum_chunk_bytes=17, maximum_cache_bytes=64))
        for source in sources:
            with reader(manifest, source).verified_session(block_size_bytes=32) as session:
                assert session.read_permuted_member_bytes("state", axis_order, 1, 59) == expected[1:59]
                assert session.read_permuted_member_bytes("state", axis_order, 29, 29) == b""
            with pytest.raises(ValueError, match="closed"):
                session.read_permuted_member_bytes("state", axis_order, 0, 1)
            assert session.final_verification.manifest == manifest.identity
    finally:
        for witness in witnesses.values():
            witness.close()
        for handle in handles.values():
            handle.close()


def test_permuted_view_preserves_partial_scalar_empty_and_raw_ieee_payload_bytes():
    bits = np.asarray([0, 1 << 63, 0x7FF800000000005A, 0x7FF0000000000000], dtype="<u8")
    arrays = {"empty":np.empty((0, 2), dtype="<c16"), "scalar":np.asarray(-0., dtype=">f8"),
        "state":bits.view("<f8").reshape(2, 2)}
    orders = {"empty":(1, 0), "scalar":(), "state":(1, 0)}
    manifest, handles, witnesses = transformed_case(arrays, orders, finite_required=False)
    try:
        for source in (BytesSource({name:array.tobytes() for name, array in arrays.items()}),
                PhysicalFDByteSource(manifest, witnesses, maximum_chunk_bytes=17, maximum_cache_bytes=64)):
            with reader(manifest, source).verified_session(block_size_bytes=32) as session:
                for name, array in arrays.items():
                    expected = array.transpose(orders[name]).tobytes()
                    start, stop = (1, len(expected) - 1) if expected else (0, 0)
                    assert session.read_permuted_member_bytes(name, orders[name], start, stop) == expected[start:stop]
    finally:
        for witness in witnesses.values():
            witness.close()
        for handle in handles.values():
            handle.close()


@pytest.mark.parametrize("axis_order,start,stop", (
    ((True, 1), 0, 8), ((0., 1), 0, 8), ([1, 0], 0, 8), ((0,), 0, 8),
    ((1, 1), 0, 8), ((-1, 0), 0, 8), ((2, 0), 0, 8), ((1, 0), True, 8),
    ((1, 0), 0., 8), ((1, 0), -1, 8), ((1, 0), 0, 193), ((1, 0), 0, 33),
))
def test_permuted_view_rejects_ambiguous_axes_ranges_and_unselected_value_bounds(axis_order, start, stop):
    _, manifest, source = case()
    with reader(manifest, source, slice_bytes=32).verified_session(block_size_bytes=32) as session:
        with pytest.raises(ValueError, match="permutation|interval|byte bound"):
            session.read_permuted_member_bytes("state", axis_order, start, stop)


def test_permuted_generic_mapping_coalesces_contiguous_logical_runs(monkeypatch):
    array = np.arange(24, dtype="<i2").reshape(2, 3, 4)
    manifest = ArrayDatasetManifest("fixture.coalesced-permuted-view", (
        ArrayDatasetMember("state", array.dtype.str, array.shape, sha256(array.tobytes()).hexdigest()),), ())
    calls = []
    original = shared_reader._VerifiedDatasetSession.read_member_bytes
    def recorded(self, name, start, stop):
        calls.append((start, stop))
        return original(self, name, start, stop)
    monkeypatch.setattr(shared_reader._VerifiedDatasetSession, "read_member_bytes", recorded)
    with reader(manifest, BytesSource({"state":array.tobytes()})).verified_session(block_size_bytes=32) as session:
        assert session.read_permuted_member_bytes("state", (1, 0, 2), 0, array.nbytes) == array.transpose(1, 0, 2).tobytes()
        assert calls == [(0, 8), (24, 32), (8, 16), (32, 40), (16, 24), (40, 48)]
        calls.clear()
        assert session.read_permuted_member_bytes("state", (0, 1, 2), 1, 47) == array.tobytes()[1:47]
        assert calls == [(1, 47)]


@pytest.mark.parametrize("cache_bytes", (0, 128, 192))
def test_identity_physical_ranges_visit_each_touched_block_once_and_retain_final_whole_scan(monkeypatch, cache_bytes):
    array = np.arange(512, dtype="<f8").reshape(4, 128)
    manifest, handles, witnesses = transformed_case({"state":array}, {"state":(0, 1)}, block_size_bytes=64)
    source = PhysicalFDByteSource(manifest, witnesses, maximum_chunk_bytes=64, maximum_cache_bytes=cache_bytes)
    reads, blocks, actual_pread, actual_block = [], [], os.pread, PhysicalFDByteSource._block
    def observed_read(descriptor, size, offset):
        reads.append((size, offset))
        return actual_pread(descriptor, size, offset)
    def observed_block(self, name, ordinal):
        blocks.append((name, ordinal))
        return actual_block(self, name, ordinal)
    monkeypatch.setattr(os, "pread", observed_read)
    monkeypatch.setattr(PhysicalFDByteSource, "_block", observed_block)
    try:
        with reader(manifest, source, slice_bytes=128).verified_session(block_size_bytes=64) as session:
            for _ in range(2):
                assert session.read_member_bytes("state", 3, 131) == array.tobytes()[3:131]
                assert session.read_member_bytes("state", 3, 3) == b""
                assert source._cache_bytes == min(cache_bytes, 192)
                assert sum(len(value.payload) for value in source._cache.values()) == source._cache_bytes
            assert blocks == [("state", ordinal) for ordinal in (0, 1, 2, 0, 1, 2)]
            touched_reads = [(64, offset) for offset in (0, 64, 128)] * (1 if cache_bytes == 192 else 2)
            assert reads == touched_reads
        assert reads == touched_reads + [(64, offset) for offset in range(0, array.nbytes, 64)]
        assert session.final_verification.manifest == manifest.identity
        assert session.final_verification.member_hashes == (("state", sha256(array.tobytes()).hexdigest()),)
        assert session.final_verification.verified_value_bytes == array.nbytes
    finally:
        source.close()
        for handle in handles.values():
            handle.close()


def test_permuted_physical_fastpath_uses_only_touched_blocks_then_one_final_whole_scan(monkeypatch):
    array = np.arange(512, dtype="<f8").reshape(128, 4)
    manifest, handles, witnesses = transformed_case({"state":array}, {"state":(1, 0)}, block_size_bytes=64)
    source = PhysicalFDByteSource(manifest, witnesses, maximum_chunk_bytes=64, maximum_cache_bytes=128)
    calls, actual_pread = [], os.pread
    def observed(descriptor, size, offset):
        calls.append((size, offset))
        return actual_pread(descriptor, size, offset)
    monkeypatch.setattr(os, "pread", observed)
    monkeypatch.setattr(PhysicalFDByteSource, "read_member_range",
        lambda *args, **kwargs:pytest.fail("matching physical transpose used logical scalar gather"))
    try:
        with reader(manifest, source, slice_bytes=128).verified_session(block_size_bytes=64) as session:
            expected = array.transpose(1, 0).tobytes()[:128]
            assert session.read_permuted_member_bytes("state", (1, 0), 0, 128) == expected
            assert session.read_permuted_member_bytes("state", (1, 0), 0, 128) == expected
            assert calls == [(64, 0), (64, 64)]
        assert sum(size for size, _ in calls) == array.nbytes + 128
        assert len(calls) == array.nbytes // 64 + 2
    finally:
        for handle in handles.values():
            handle.close()


@pytest.mark.parametrize("mutation", ("touched", "cached", "unused", "restored"))
def test_permuted_physical_delivery_and_final_seal_refuse_changed_baseline_bytes(mutation):
    array = np.arange(24, dtype="<f8").reshape(8, 3)
    manifest, handles, witnesses = transformed_case({"state":array}, {"state":(1, 0)}, block_size_bytes=64)
    source = PhysicalFDByteSource(manifest, witnesses, maximum_chunk_bytes=32, maximum_cache_bytes=64)
    descriptor = handles["state"].fileno()
    original = os.pread(descriptor, 8, 0)
    try:
        with pytest.raises(ValueError, match="touched block|final whole seal|refused"):
            with reader(manifest, source).verified_session(block_size_bytes=64) as session:
                if mutation == "touched":
                    os.pwrite(descriptor, struct.pack("<d", 999), 0)
                    session.read_permuted_member_bytes("state", (1, 0), 0, 8)
                elif mutation == "restored":
                    os.pwrite(descriptor, struct.pack("<d", 999), 0)
                    with pytest.raises(ValueError, match="touched block"):
                        session.read_permuted_member_bytes("state", (1, 0), 0, 8)
                    os.pwrite(descriptor, original, 0)
                else:
                    assert session.read_permuted_member_bytes("state", (1, 0), 0, 8) == original
                    os.pwrite(descriptor, struct.pack("<d", 999), 0 if mutation == "cached" else 128)
                    assert session.read_permuted_member_bytes("state", (1, 0), 0, 8) == original
    finally:
        for handle in handles.values():
            handle.close()


def test_sealed_descriptor_source_bindings_cannot_be_swapped_after_complete_admission():
    expected = np.asarray([1., 2.], dtype="<f8")
    raw = expected.tobytes()
    manifest = ArrayDatasetManifest("fixture.sealed-source-binding", (
        ArrayDatasetMember("state", "<f8", (2,), sha256(raw).hexdigest()),), ())
    descriptor = _anonymous_input_descriptor()
    try:
        os.write(descriptor, raw + np.asarray([999., 998.], dtype="<f8").tobytes())
        _seal_anonymous_input(descriptor)
        source = SealedFDByteSource({"state": DatasetFDMember(descriptor, 0, len(raw), 2 * len(raw))}, maximum_chunk_bytes=8)
        try:
            with reader(manifest, source).verified_session(block_size_bytes=16) as session:
                leased = session._source
                swapped = {"state": DatasetFDMember(next(iter(leased._descriptors.values())), len(raw), len(raw), 2 * len(raw))}
                with pytest.raises(AttributeError, match="read-only"):
                    leased._members = swapped
                with pytest.raises(TypeError):
                    leased._members["state"] = swapped["state"]
                with pytest.raises(AttributeError, match="read-only"):
                    leased._closed = False
                assert session.read_array("state").tobytes() == raw
        finally:
            source.close()
    finally:
        os.close(descriptor)


def test_reader_and_session_selected_sources_proof_and_final_seal_are_read_only():
    _, manifest, original = case()
    source = RegularFileSource(original.values)
    actual = reader(manifest, source.authenticated())
    for field, replacement in (("_manifest", replace(manifest, dataset_id="fixture.forged")),
            ("_source", original), ("_members", {}), ("_maximum_slice_bytes", 99999)):
        with pytest.raises(AttributeError, match="read-only"):
            setattr(actual, field, replacement)
    with pytest.raises(ValueError, match="value hash"):
        with actual.verified_session(block_size_bytes=64) as session:
            for field, replacement in (("_source", original), ("_manifest", replace(manifest, dataset_id="fixture.forged")),
                    ("_final", session._initial), ("_refused", False), ("_closed", False),
                    ("_mode", "sealed"), ("_authenticated_index", {})):
                with pytest.raises(AttributeError, match="read-only"):
                    setattr(session, field, replacement)
            source.change("ticks", 0, struct.pack("<q", 999))
