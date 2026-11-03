# SPDX-License-Identifier: MPL-2.0
"""Retained factor diagnostic row consumers; exposed fixtures, no acquisition."""

from dataclasses import replace
from hashlib import sha256
from io import BytesIO
import json
import tracemalloc
import zipfile

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_factor_lifetime import products
from empirical_lawhood.adapters.methods.matrix_factor_lifetime.science import measure_trace
from empirical_lawhood.adapters.methods.matrix_history_analysis import algebra
from empirical_lawhood.adapters.methods.matrix_dataset_readers import bridge_factor_diagnostics
from empirical_lawhood.infrastructure.matrix_array_io import MatrixArtifactSource, MatrixNPZSource, NPZMemberSelection, NPZMemberSource, encode_matrix_arrays
from tests.test_matrix_factor_lifetime import artifact, population_result, root, spec


def case(*, count=4):
    rule = spec(lattice=tuple(16 * at for at in range(count)))
    positions = np.broadcast_to(np.stack((algebra.LEFT, algebra.RIGHT)), (2 * rule.lattice[-1] + 1, 2, 3, 4, 4))
    store = {root().native_arrays.artifact_id: b"native", root().native_result.artifact_id: b"receipt",
        "test.factor.inventory": b"inventory"}
    traces = []
    for view in ("PRIMARY", "FINE"):
        trace, arrays = measure_trace(rule, root(), view, "Y", positions)
        raw, members = encode_matrix_arrays(arrays,
            nonfinite_members=("spectrum", "projector", "basis", "factor", "aligned_factor"))
        identity = artifact("test.diagnostics." + view.lower(), raw, media="application/zip")
        traces.append(replace(trace, diagnostics=identity, diagnostic_members=members))
        store[identity.artifact_id] = raw
    return population_result(rule, traces), store


def read(result, store):
    return products.read_result(result.canonical_bytes(), expected_population=result.population,
        expected_rule=result.rule, expected_provenance=result.producing_provenance,
        artifact_reader=lambda identity: store[identity.artifact_id])


@pytest.mark.parametrize("compression,reverse", ((zipfile.ZIP_STORED, False), (zipfile.ZIP_DEFLATED, True)))
def test_same_retained_scientific_consumer_accepts_equivalent_original_npz(compression, reverse, monkeypatch):
    result, store = case()
    logical, selected = [], []
    monkeypatch.setattr(np, "load", lambda *args, **kwargs: pytest.fail("retained reader expands an entire NPZ"))
    monkeypatch.setattr(algebra, "sector", lambda *args, **kwargs: pytest.fail("retained read recalculates spectra"))
    for trace in result.traces:
        original = store[trace.diagnostics.artifact_id]
        target = BytesIO()
        with zipfile.ZipFile(BytesIO(original)) as source, zipfile.ZipFile(target, "w", compression=compression) as output:
            for name in sorted(source.namelist(), reverse=reverse):
                output.writestr(name, source.read(name))
        raw = target.getvalue()
        changed = replace(trace, diagnostics=replace(trace.diagnostics, sha256=sha256(raw).hexdigest(), size_bytes=len(raw)))
        first = bridge_factor_diagnostics(trace, original, maximum_chunk_bytes=65536, maximum_slice_bytes=65536)
        second = bridge_factor_diagnostics(changed, raw, maximum_chunk_bytes=65536, maximum_slice_bytes=65536)
        try:
            assert first.reader.manifest == second.reader.manifest
            with second.reader.verified_session(block_size_bytes=65536) as reader:
                rows = second.row_mapping(reader)
                with pytest.raises(TypeError, match="whole-population"):
                    np.asarray(rows["projector"])
                products.validate_diagnostics(rows, changed, result.rule)
                assert not rows["projector"][0].flags.writeable
            with pytest.raises(ValueError, match="closed"):
                rows["projector"][0]
        finally:
            first.close()
            second.close()
        logical.append((changed.observations, changed.moving_lifetime, changed.origin_fixed_lifetime))
        selected.append(changed)
        store[changed.diagnostics.artifact_id] = raw
    expected = replace(result, traces=tuple(selected))
    assert read(expected, store).canonical_bytes() == expected.canonical_bytes()
    assert logical == [(trace.observations, trace.moving_lifetime, trace.origin_fixed_lifetime) for trace in result.traces]


@pytest.mark.parametrize("damage", ("missing-member", "wrong-dtype", "wrong-axis", "wrong-media"))
def test_invalid_declared_diagnostic_contract_refuses_before_cursor(damage, monkeypatch):
    result, store = case()
    trace = result.traces[0]
    members = trace.diagnostic_members
    if damage == "missing-member":
        members = members[1:]
    elif damage == "wrong-dtype":
        members = tuple(replace(member, dtype="<i8") if member.name == "basis" else member for member in members)
    elif damage == "wrong-axis":
        members = tuple(replace(member, shape=(5, *member.shape[1:])) if member.name == "basis" else member for member in members)
    changed = replace(trace, diagnostic_members=members,
        diagnostics=replace(trace.diagnostics, media_type="application/json") if damage == "wrong-media" else trace.diagnostics)
    result = replace(result, traces=(changed, result.traces[1]))
    monkeypatch.setattr(products, "bridge_factor_diagnostics", lambda *args, **kwargs: pytest.fail("invalid metadata opened cursor"))
    with pytest.raises(ValueError, match="census|precision|ZIP media"):
        read(result, store)


def test_changed_touched_decoded_block_refuses_independent_scientific_delivery(monkeypatch):
    result, store = case()
    original = NPZMemberSource.read_member_range
    def changed(source, name, start, stop):
        raw = original(source, name, start, stop)
        return raw[:-1] + bytes((raw[-1] ^ 1,)) if raw and name == "projector" else raw
    monkeypatch.setattr(NPZMemberSource, "read_member_range", changed)
    with pytest.raises(ValueError, match="touched block"):
        read(result, store)


def test_late_decoder_fault_refuses_final_seal_before_result_return(monkeypatch):
    result, store = case()
    validated = []
    original_validate, original_open = products.validate_diagnostics, NPZMemberSource.open_member
    def checked(*args, **kwargs):
        original_validate(*args, **kwargs)
        validated.append(True)
    def changed(source, name):
        for raw in original_open(source, name):
            yield raw[:-1] + bytes((raw[-1] ^ 1,)) if validated and raw and name == "projector" else raw
    monkeypatch.setattr(products, "validate_diagnostics", checked)
    monkeypatch.setattr(NPZMemberSource, "open_member", changed)
    with pytest.raises(ValueError, match="hash verification"):
        read(result, store)
    assert validated == [True]  # Complete unchanged science ran before late refusal.


def test_forward_member_streams_preserve_arbitrary_bytes_rewind_eviction_and_close():
    result, store = case()
    trace = result.traces[0]
    raw = store[trace.diagnostics.artifact_id]
    with zipfile.ZipFile(BytesIO(raw)) as archive:
        expected = {name.removesuffix(".npy"): np.lib.format.read_array(BytesIO(archive.read(name)), allow_pickle=False).tobytes()
            for name in archive.namelist()}
    physical = MatrixArtifactSource(trace.diagnostics, raw, 65536)
    source = NPZMemberSource(NPZMemberSelection(trace.diagnostics, trace.diagnostic_members), physical, 65536,
        maximum_open_members=1)
    try:
        with pytest.raises(ValueError, match="exact original codec schema or media"):
            MatrixNPZSource(NPZMemberSelection(trace.diagnostics, trace.diagnostic_members), physical, 65536)
        assert source.read_member_range("basis", 1, 21) == expected["basis"][1:21]
        old = source._ranges["basis"][1]
        assert source.read_member_range("basis", 21, 117) == expected["basis"][21:117]
        assert source._ranges["basis"][1] is old
        assert source.read_member_range("factor", 3, 51) == expected["factor"][3:51]
        assert old.closed and tuple(source._ranges) == ("factor",)
        displaced = source._ranges["factor"][1]
        assert source.read_member_range("basis", 71, 103) == expected["basis"][71:103]
        assert displaced.closed
        before_rewind = source._ranges["basis"][1]
        assert source.read_member_range("basis", 0, 7) == expected["basis"][:7]
        assert before_rewind.closed
        assert source.read_member_range("basis", 7, 7) == b""
        last = source._ranges["basis"][1]
    finally:
        source.close()
        physical.close()
    assert last.closed
    with pytest.raises(ValueError, match="closed"):
        source.read_member_range("basis", 0, 1)


def test_range_decode_failure_closes_every_live_member_stream(monkeypatch):
    result, store = case()
    trace = result.traces[0]
    physical = MatrixArtifactSource(trace.diagnostics, store[trace.diagnostics.artifact_id], 65536)
    source = NPZMemberSource(NPZMemberSelection(trace.diagnostics, trace.diagnostic_members), physical, 65536,
        maximum_open_members=8)
    source.read_member_range("basis", 0, 8)
    source.read_member_range("factor", 0, 8)
    streams = [lease[1] for lease in source._ranges.values()]
    original = zipfile.ZipExtFile.read
    def failure(stream, *args, **kwargs):
        if stream is streams[1]:
            return b""
        return original(stream, *args, **kwargs)
    monkeypatch.setattr(zipfile.ZipExtFile, "read", failure)
    try:
        with pytest.raises(ValueError, match="truncates"):
            source.read_member_range("factor", 8, 16)
        assert all(stream.closed for stream in streams) and not source._ranges
    finally:
        source.close()
        physical.close()


def test_nonmonotonic_compressed_range_replay_is_measured_without_population_cache(monkeypatch, tmp_path):
    result, store = case(count=257)
    trace = result.traces[0]
    raw = store[trace.diagnostics.artifact_id]
    with zipfile.ZipFile(BytesIO(raw)) as archive:
        expected = np.lib.format.read_array(BytesIO(archive.read("projector.npy")), allow_pickle=False).tobytes()
    physical = MatrixArtifactSource(trace.diagnostics, raw, 65536)
    source = NPZMemberSource(NPZMemberSelection(trace.diagnostics, trace.diagnostic_members), physical, 65536)
    count = [0]
    original = zipfile.ZipExtFile.read
    def read(stream, *args, **kwargs):
        selected = original(stream, *args, **kwargs)
        count[0] += len(selected)
        return selected
    monkeypatch.setattr(zipfile.ZipExtFile, "read", read)
    starts = tuple(reversed(range(0, len(expected), 65536)))
    try:
        for start in starts:
            assert source.read_member_range("projector", start, start + 1) == expected[start:start + 1]
        assert len(source._ranges) == 1
    finally:
        source.close()
        physical.close()
    report = {"scope": "adverse reverse-block one-byte range requests in compressed NPZ; no scientific method or source claim",
        "member_value_bytes": len(expected), "requested_range_bytes": len(starts),
        "zip_uncompressed_delivered_bytes": count[0],
        "limitation": "backward/evicted compressed requests must replay prefixes; forward scientific row delivery alone has the constant scan evidence"}
    assert count[0] > len(expected)
    (tmp_path / "nonmonotonic-compression-replay.json").write_text(json.dumps(report, indent=2) + "\n")


@pytest.mark.parametrize("count", (65, 257))
def test_retained_row_working_memory_and_actual_npz_delivery_census(count, monkeypatch, tmp_path):
    result, store = case(count=count)
    counters = {"zip_uncompressed_delivered_bytes": 0, "range_calls": 0, "range_bytes": 0,
        "maximum_range_bytes": 0}
    original_read, original_range = zipfile.ZipExtFile.read, NPZMemberSource.read_member_range
    def delivered(stream, *args, **kwargs):
        raw = original_read(stream, *args, **kwargs)
        counters["zip_uncompressed_delivered_bytes"] += len(raw)
        return raw
    def selected(source, name, start, stop):
        counters["range_calls"] += 1
        counters["range_bytes"] += stop - start
        counters["maximum_range_bytes"] = max(counters["maximum_range_bytes"], stop - start)
        return original_range(source, name, start, stop)
    monkeypatch.setattr(zipfile.ZipExtFile, "read", delivered)
    monkeypatch.setattr(NPZMemberSource, "read_member_range", selected)
    tracemalloc.start()
    try:
        actual = read(result, store)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert actual == result
    assert counters["maximum_range_bytes"] <= 65536
    value_bytes = sum(member.size_bytes for trace in result.traces for member in trace.diagnostic_members)
    assert counters["range_bytes"] == value_bytes
    assert counters["zip_uncompressed_delivered_bytes"] < 3.1 * value_bytes
    report = {"scope": "retained diagnostic decode, independent unchanged algebra/causal checks and finalseal; excludes existing input bytes/fixture/native HDF5/API materialization and RSS",
        "fixture": "exposed broadcast constant exact factor, no native contact or qualification",
        "lattice_rows_per_view": count, "logical_diagnostic_value_bytes": value_bytes,
        "tracemalloc_peak_bytes": peak, **counters,
        "compression_amplification": counters["zip_uncompressed_delivered_bytes"] / value_bytes}
    (tmp_path / "diagnostic-row-memory-io.json").write_text(json.dumps(report, indent=2) + "\n")
