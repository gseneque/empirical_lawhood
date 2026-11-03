# SPDX-License-Identifier: MPL-2.0
"""Exposed scientific consumer parity and real decoded-lease refusal, no solver."""

from dataclasses import replace
from io import BytesIO
import os

import pytest

from empirical_lawhood.adapters.methods.battery_refined_inquiry import lossless_evidence_stream as stream
from empirical_lawhood.adapters.methods.battery_refined_inquiry import lossless_segment_consumer as consumer
from empirical_lawhood.adapters.methods.battery_refined_inquiry import lossless_segment_records as records
from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_fidelity as local
from tests.test_battery_lossless_segment_integration import new_operand
from tests.test_battery_lossless_segment_records import encoded_original
from tests.test_battery_segmented_fidelity import _operand, prepared as prepared_fixture

prepared = prepared_fixture


def _clone(original, metadata, temporary_file):
    index, _, sources = encoded_original(original.frame.raw_return, original.frame.full_state)
    return replace(original, summary=replace(original.summary,
        native_definition=metadata.definition.identity,
        native_receipt=records.identity(metadata.native_receipt, "receipt_id")),
        frame=stream.decoded_frame(metadata, records.encode_raw_segment(index, sources), temporary_file))


def test_same_complete_interval_product_over_physical_and_logical_leases(prepared, tmp_path):
    originals = (_operand(prepared, tmp_path / "left-original", extra_knot=7.5),
        _operand(prepared, tmp_path / "right-original", horizon=30, extra_knot=12.25,
            changed_derivative=(173, .001)))
    temporary = stream.selected_temporary_files(tmp_path)
    physical = tuple(new_operand(row, tmp_path / ("new-" + str(at)), temporary)
        for at, row in enumerate(originals))
    logical = tuple(_clone(row, selected.frame.metadata, BytesIO)
        for row, selected in zip(originals, physical, strict=True))
    control = local.FullStateControlProtocol("control.exposed.storage-parity")
    try:
        assert all(row.frame.dataset_reader._mode == "physical" for row in physical)
        assert all(row.frame.dataset_reader._mode == "blocks" for row in logical)
        with consumer.numerical_consumer_scope(temporary_file=temporary, assignments=()):
            actual = local.assess_interval(control, *physical)
            expected = local.assess_interval(control, *logical)
        assert actual.canonical_bytes() == expected.canonical_bytes()
        assert actual.checked_derivative_components == 174 * 33
        assert "componentwise-returned-derivative-convergence-budget-missed" in actual.reason_codes
        for a, b in zip(physical, logical, strict=True):
            assert a.frame.dataset.reader.manifest == b.frame.dataset.reader.manifest
    finally:
        for row in (*physical, *logical):
            row.frame.close()
    for row in (*physical, *logical):
        assert all(handle.closed for handle in row.frame.handles)
        with pytest.raises(ValueError, match="closed"):
            row.frame.dataset_reader.read_member_bytes(row.frame.raw_return.arrays[0].array_id, 0, 1)


@pytest.mark.parametrize("cached", (False, True))
def test_frame_final_seal_refuses_unvisited_and_cached_mutation(prepared, tmp_path, cached):
    original = _operand(prepared, tmp_path / "original")
    selected = new_operand(original, tmp_path / "new", stream.selected_temporary_files(tmp_path))
    frame = selected.frame
    state = frame.full_state.blocks[0].state_binary64
    if cached:
        assert state[0] == original.frame.full_state.blocks[0].state_binary64[0]
    declaration = next(row for row in frame.raw_return.arrays if row.role == "all_ys")
    handle = frame.handles[frame.raw_return.arrays.index(declaration)]
    original_byte = os.pread(handle.fileno(), 1, declaration.size_bytes - 1)
    os.pwrite(handle.fileno(), bytes((original_byte[0] ^ 1,)), declaration.size_bytes - 1)
    with pytest.raises(ValueError, match="physical array final whole seal changes admitted mapped bytes"):
        frame.close()
    assert all(handle.closed for handle in frame.handles)


def test_touched_physical_mutation_refuses_before_delivery_even_if_restored(prepared, tmp_path):
    original = _operand(prepared, tmp_path / "original")
    selected = new_operand(original, tmp_path / "new", stream.selected_temporary_files(tmp_path))
    frame = selected.frame
    declaration = next(row for row in frame.raw_return.arrays if row.role == "all_ys")
    handle = frame.handles[frame.raw_return.arrays.index(declaration)]
    byte = os.pread(handle.fileno(), 1, 0)
    try:
        os.pwrite(handle.fileno(), bytes((byte[0] ^ 1,)), 0)
        with pytest.raises(ValueError, match="physical array touched block changes its admitted mapped bytes"):
            frame.full_state.blocks[0].state_binary64[0]
    finally:
        os.pwrite(handle.fileno(), byte, 0)
    # A failed delivery cannot be repaired into an accepted report by restoring
    # the scratch byte. The session retains the negative disposition.
    with pytest.raises(ValueError, match="refused"):
        frame.close()
    assert all(handle.closed for handle in frame.handles)
