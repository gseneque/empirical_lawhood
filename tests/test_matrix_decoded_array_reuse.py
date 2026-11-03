# SPDX-License-Identifier: MPL-2.0
"""Invocation-local physical array reuse; no science, RNG or authority."""

from dataclasses import replace
from hashlib import sha256

import numpy as np
import pytest

from empirical_lawhood.infrastructure import matrix_array_io as owner
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.references import ArtifactIdentity


@pytest.mark.parametrize("population", (8, 257))
def test_reuse_preserves_complete_readonly_values_and_each_invocation_decodes_afresh(population, monkeypatch):
    arrays = {"values": np.arange(3 * population, dtype="<f8").reshape(population, 3),
        "ticks": np.arange(population, dtype="<i8")}
    raw, members = owner.encode_matrix_arrays(arrays)
    operand = owner.NPZMemberSelection(ArtifactIdentity("array.software-decoded-reuse", "software-codec-control",
        MATRIX_ARRAY_SCHEMA, sha256(raw).hexdigest(), "application/x-npz", len(raw)), members)
    calls = []
    decode = owner._decode_matrix_arrays

    def actual_decode(raw, manifest):
        calls.append((raw, manifest))
        return decode(raw, manifest)

    monkeypatch.setattr(owner, "_decode_matrix_arrays", actual_decode)
    for invocation in (1, 2):
        selected = owner.DecodedMatrixArrayInput(raw, operand)
        first = selected.for_operand(raw, operand)
        assert selected.for_operand(raw, operand) is first
        assert len(calls) == invocation
        assert set(first) == set(arrays)
        for name, expected in arrays.items():
            value = first[name]
            assert (value.dtype.str, value.shape, value.tobytes()) == (expected.dtype.str, expected.shape, expected.tobytes())
            with pytest.raises(ValueError):
                value.reshape(-1)[0] = 0
            with pytest.raises(ValueError):
                value.setflags(write=True)
        with pytest.raises(TypeError):
            first["unselected"] = np.zeros(1)
        with pytest.raises(AttributeError, match="read-only"):
            selected.original = operand
        with pytest.raises(AttributeError, match="read-only"):
            del selected.original
        with pytest.raises(TypeError):
            owner.DecodedMatrixArrayInput(raw, operand, arrays)


@pytest.mark.parametrize("damage", ("same-bytes-other-object", "changed-byte", "artifact-id", "physical-hash", "member-hash", "finite-policy"))
def test_reuse_refuses_other_bytes_or_descriptor_without_another_expansion(damage, monkeypatch):
    raw, members = owner.encode_matrix_arrays({"values": np.arange(8, dtype="<f8")})
    operand = owner.NPZMemberSelection(ArtifactIdentity("array.software-reuse-refusal", "software-codec-control",
        MATRIX_ARRAY_SCHEMA, sha256(raw).hexdigest(), "application/x-npz", len(raw)), members)
    selected = owner.DecodedMatrixArrayInput(raw, operand)
    received, actual = raw, operand
    if damage == "same-bytes-other-object":
        received = bytes(memoryview(raw))
        assert received == raw and received is not raw
    elif damage == "changed-byte":
        received = raw[:-1] + bytes((raw[-1] ^ 1,))
    elif damage == "artifact-id":
        actual = replace(operand, array_artifact=replace(operand.array_artifact, artifact_id="array.other-control"))
    elif damage == "physical-hash":
        actual = replace(operand, array_artifact=replace(operand.array_artifact, sha256="f" * 64))
    elif damage == "member-hash":
        actual = replace(operand, members=(replace(members[0], sha256="f" * 64),))
    else:
        actual = replace(operand, members=(replace(members[0], finite_required=False),))
    monkeypatch.setattr(owner, "_decode_matrix_arrays", lambda *_args:
        pytest.fail("mismatched reuse re-entered array expansion"))
    with pytest.raises(ValueError, match="received bytes or exact original operand"):
        selected.for_operand(received, actual)


@pytest.mark.parametrize("damage", ("physical-byte", "member-hash", "omitted-member"))
def test_decoded_input_construction_authenticates_actual_closed_bytes(damage):
    raw, members = owner.encode_matrix_arrays({"a": np.arange(8, dtype="<f8"), "b": np.arange(8, dtype="<i8")})
    operand = owner.NPZMemberSelection(ArtifactIdentity("array.software-reuse-construction", "software-codec-control",
        MATRIX_ARRAY_SCHEMA, sha256(raw).hexdigest(), "application/x-npz", len(raw)), members)
    if damage == "physical-byte":
        raw = raw[:-1] + bytes((raw[-1] ^ 1,))
    elif damage == "member-hash":
        operand = replace(operand, members=(replace(members[0], sha256="f" * 64), members[1]))
    else:
        operand = replace(operand, members=members[:-1])
    with pytest.raises(ValueError):
        owner.DecodedMatrixArrayInput(raw, operand)


def _small_operand(index=0):
    raw, members = owner.encode_matrix_arrays({'values': np.arange(8, dtype='<f8') + index})
    return raw, owner.NPZMemberSelection(ArtifactIdentity('array.scope-' + str(index), 'software-codec-control',
        MATRIX_ARRAY_SCHEMA, sha256(raw).hexdigest(), 'application/x-npz', len(raw)), members)


def test_scope_reuses_exact_values_and_releases_them_on_consumer_refusal(monkeypatch):
    import weakref
    raw, operand = _small_operand()
    calls = []
    decode = owner._decode_matrix_arrays

    def counted(*args):
        calls.append(1)
        return decode(*args)

    monkeypatch.setattr(owner, '_decode_matrix_arrays', counted)
    with pytest.raises(RuntimeError, match='consumer refusal'):
        with owner.decoded_matrix_array_scope():
            values = owner.decode_matrix_arrays(raw, operand)
            assert owner.decode_matrix_arrays(raw, operand) is values
            ref = weakref.ref(values['values'])
            with pytest.raises(ValueError):
                values['values'].setflags(write=True)
            del values
            assert ref() is not None
            raise RuntimeError('consumer refusal')
    assert ref() is None
    with owner.decoded_matrix_array_scope():
        owner.decode_matrix_arrays(raw, operand)
    assert len(calls) == 2


def test_scope_bound_evicts_without_thinning_or_changing_values(monkeypatch):
    operands = (_small_operand(0), _small_operand(1))
    limit = max(len(raw) + 64 for raw, _ in operands)
    calls = []
    decode = owner._decode_matrix_arrays

    def counted(*args):
        calls.append(1)
        return decode(*args)

    monkeypatch.setattr(owner, '_decode_matrix_arrays', counted)
    with owner.decoded_matrix_array_scope(maximum_bytes=limit):
        first = owner.decode_matrix_arrays(*operands[0])
        owner.decode_matrix_arrays(*operands[1])
        state = owner._decoded_array_scope.get()
        assert state['bytes'] <= limit and len(state['entries']) == 1
        assert owner.decode_matrix_arrays(*operands[0])['values'].tobytes() == first['values'].tobytes()
    assert len(calls) == 3


def test_scope_authenticates_changed_bytes_and_descriptor():
    raw, operand = _small_operand()
    with owner.decoded_matrix_array_scope():
        owner.decode_matrix_arrays(raw, operand)
        with pytest.raises(ValueError):
            owner.decode_matrix_arrays(raw[:-1] + bytes((raw[-1] ^ 1,)), operand)
        with pytest.raises(ValueError):
            owner.decode_matrix_arrays(raw, replace(operand,
                members=(replace(operand.members[0], sha256='f' * 64),)))
        # A separately received immutable body is independently decoded.
        copied = bytes(memoryview(raw))
        assert copied is not raw
        assert owner.decode_matrix_arrays(copied, operand) is not owner.decode_matrix_arrays(raw, operand)
