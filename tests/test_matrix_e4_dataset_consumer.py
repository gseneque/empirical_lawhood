# SPDX-License-Identifier: MPL-2.0
"""Exact protected E4 carriers through the real bounded worker callback.

The reused literal phase arrays are exposed authored controls. Their numerical
failures remain; these tests perform no native work or scientific qualification.
"""

from contextlib import ExitStack
from dataclasses import replace
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_dataset_readers import bridge_saved_arrays
from empirical_lawhood.adapters.methods.matrix_scheduled_history import science
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_array_preparation import selected_record_array_mappings
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_native_records import SelectedE4ProtectedArrays
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from tests.test_matrix_dataset_readers import real_port
from tests.test_matrix_e3_scheduled_datasets import physical_dataset
from tests.test_matrix_e3_protected_prefix_science import (  # noqa: F401
    case, forbid_native, products,
)


def protected_arrays(original):
    return SelectedE4ProtectedArrays(original.operand_id, original.source, original.role,
        original.array_artifact, original.members, original.producers,
        original.outcome_access, original.visibility_ceiling)


@pytest.mark.parametrize("encoding", ("npz", "sealed-port", "physical-members"))
def test_real_protected_e4_worker_callback_preserves_original_adverse_numerical_controls(case, tmp_path, encoding):  # noqa: F811
    original = case.old_history.arrays
    owner = protected_arrays(original)
    with ExitStack() as stack:
        supplied = case.native_raw
        if encoding == "sealed-port":
            supplied = real_port(owner.array_artifact, supplied)
            stack.callback(supplied.close)
        elif encoding == "physical-members":
            supplied = stack.enter_context(physical_dataset(owner, supplied, tmp_path / "protected-prefix"))
        with selected_record_array_mappings({"prefix": SimpleNamespace(arrays=owner)},
                {"prefix-arrays": supplied}, protocol=None) as values:
            observed = science.assess_prefix_values(case.source, values["prefix-arrays"])
    assert canonical_json_bytes(observed) == canonical_json_bytes(case.old_numerical.controls)
    assert any(value.disposition == "VIOLATED" for value in observed)
    assert tuple((value.denominator_steps, value.denominator_real_coordinates) for value in observed) == (
        (256, 192), (512, 192), (256, 192), (256, 96))


@pytest.mark.parametrize("kind", ("prefix", "diagnostic", "causal"))
def test_each_protected_e4_carrier_retains_complete_original_member_bytes(case, products, kind):  # noqa: F811
    if kind == "prefix":
        original, raw, record_key, port_key = case.old_history.arrays, case.native_raw, "prefix", "prefix-arrays"
    elif kind == "diagnostic":
        original, raw, record_key, port_key = products.witness.arrays, products.diagnostic_raw, "witness", "diagnostic-arrays"
    else:
        original, raw, record_key, port_key = products.causal.arrays, products.causal_raw, "causal", "causal-arrays"
    owner = protected_arrays(original)
    original_bridge = bridge_saved_arrays(original, raw, maximum_chunk_bytes=65536, maximum_slice_bytes=64 * 1024**2)
    try:
        with original_bridge.reader.verified_session(block_size_bytes=65536) as original_session:
            expected = original_bridge.array_mapping(original_session)
            with selected_record_array_mappings({record_key: SimpleNamespace(arrays=owner)},
                    {port_key: raw}, protocol=None) as selected:
                actual = selected[port_key]
                assert tuple(actual) == tuple(expected)
                for name in expected:
                    left, right = actual[name], expected[name]
                    assert (left.dtype.str, left.shape, left.tobytes()) == (right.dtype.str, right.shape, right.tobytes())
    finally:
        original_bridge.close()


@pytest.mark.parametrize("damage", ("mutation", "truncation", "missing-member", "shape", "dtype"))
def test_real_protected_e4_callback_refuses_incomplete_or_changed_arrays_before_arithmetic(case, monkeypatch, damage):  # noqa: F811
    owner, raw = protected_arrays(case.old_history.arrays), case.native_raw
    if damage == "mutation":
        raw = raw[:-1] + bytes((raw[-1] ^ 1,))
    elif damage == "truncation":
        raw = raw[:-1]
    elif damage == "missing-member":
        owner = replace(owner, members=owner.members[:-1])
    else:
        member = next(value for value in owner.members if value.dtype == "<c16")
        changed = replace(member, dtype="<f8") if damage == "dtype" else replace(member, shape=(member.shape[0] + 1, *member.shape[1:]))
        owner = replace(owner, members=tuple(changed if value is member else value for value in owner.members))

    def forbidden(*args, **kwargs):
        raise AssertionError("changed complete protected arrays reached numerical arithmetic")

    monkeypatch.setattr(science, "assess_prefix_values", forbidden)
    with pytest.raises(ValueError):
        with selected_record_array_mappings({"prefix": SimpleNamespace(arrays=owner)},
                {"prefix-arrays": raw}, protocol=None) as values:
            science.assess_prefix_values(case.source, values["prefix-arrays"])


def test_protected_e4_admission_does_not_admit_unregistered_subclasses(case):  # noqa: F811
    class UnregisteredArrays(SelectedE4ProtectedArrays):
        pass

    original = case.old_history.arrays
    foreign = UnregisteredArrays(original.operand_id, original.source, original.role,
        original.array_artifact, original.members, original.producers,
        original.outcome_access, original.visibility_ceiling)
    with pytest.raises(TypeError, match="exact original saved operand"):
        bridge_saved_arrays(foreign, case.native_raw, maximum_chunk_bytes=65536, maximum_slice_bytes=64 * 1024**2)
