# SPDX-License-Identifier: MPL-2.0
"""Exact Matrix values and adverse transport controls, never qualification."""

from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
from io import BytesIO
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_array_chunks import (
    ChunkedMatrixArrays, MatrixArrayInterval, encode_chunk, framed_artifact, iter_chunk_arrays,
    iter_framed_bytes, whole_member,
)
from empirical_lawhood.adapters.methods.matrix_dataset_readers import (
    bridge_chunked_arrays, bridge_framed_arrays, bridge_saved_arrays, bridge_worker_arrays,
)
from empirical_lawhood.adapters.methods.matrix_factor_response.records import MatrixResponseArrays
from empirical_lawhood.infrastructure.artifact_stream_primitives import (
    ArtifactInputLimitExceeded, _PreopenedBoundedReader, _anonymous_input_descriptor, _seal_anonymous_input,
)
from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays, encode_matrix_arrays
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA, MatrixAllocation, SavedMatrixArrays
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.runtime.execution import WorkerInputBinding, WorkerInputKind, WorkerInputPort
from tests.test_matrix_factor_confirmation_eligibility import stock, provenance  # noqa: F401
import os


def transport_case():
    arrays = {"complex": (np.arange(36) + 1j * np.arange(36)).astype("<c16").reshape(12, 3),
        "empty": np.empty((0, 2), dtype="<f8"), "scalar": np.asarray(-0., dtype="<f8"),
        "state": np.arange(24, dtype="<f8").reshape(8, 3), "ticks": np.arange(8, dtype="<i8")}
    source = ObjectIdentity("fixture.matrix.original-source", "empirical-lawhood/tests/exposed-matrix-source", "1.0.0", "1" * 64)
    allocation = ObjectIdentity("fixture.matrix.allocation", MatrixAllocation.SCHEMA, "1.0.0", "2" * 64)
    raw, members = encode_matrix_arrays(arrays)
    artifact = ArtifactIdentity("fixture.matrix.npz", "fixture-matrix-values", MATRIX_ARRAY_SCHEMA,
        sha256(raw).hexdigest(), "application/x-npz", len(raw))
    saved = SavedMatrixArrays("fixture.matrix.saved", allocation, artifact, members, (source,))
    leaves, chunks = {}, []
    # Each declared member keeps its original first-axis ownership, including
    # scalar and explicit-empty members; packaging creates no scientific roots.
    for index, (name, value) in enumerate(sorted(arrays.items())):
        extent = value.shape[0] if value.shape else 1
        stops = (0,) if extent == 0 else (extent // 2, extent) if extent > 1 else (1,)
        start = 0
        for part, stop in enumerate(stops):
            chunk_id = f"fixture.chunk.{index:02}.{part:02}"
            payload, chunk = encode_chunk({name: value[start:stop] if value.shape else value},
                (MatrixArrayInterval(name, start, stop),), chunk_id=chunk_id,
                artifact_id="artifact." + chunk_id, producers=(source,))
            chunks.append(chunk)
            leaves[chunk.array_artifact.artifact_id] = payload
            start = stop
    chunked = ChunkedMatrixArrays("fixture.matrix.chunked", source, allocation,
        tuple(whole_member(name, value) for name, value in sorted(arrays.items())), tuple(chunks), (source,))
    fetch = lambda artifact: (leaves[artifact.artifact_id],)
    container = framed_artifact(chunked, fetch, artifact_id="fixture.matrix.framed", maximum_chunk_bytes=128)
    framed = b"".join(iter_framed_bytes(chunked, fetch, maximum_chunk_bytes=128))
    return arrays, raw, saved, leaves, chunked, framed, container

def real_port(artifact, raw):
    descriptor = _anonymous_input_descriptor()
    try:
        os.write(descriptor, raw)
        _seal_anonymous_input(descriptor)
    except BaseException:
        os.close(descriptor)
        raise
    binding = WorkerInputBinding(artifact.artifact_id, "materialization." + artifact.artifact_id,
        artifact.payload_schema, artifact.media_type, len(raw), VisibilityCeiling.DEVELOPMENT_ONLY,
        OutcomeAccess.DEVELOPMENT_VISIBLE, WorkerInputKind.DEPENDENCY)
    return WorkerInputPort(binding, _PreopenedBoundedReader(descriptor, maximum_bytes=len(raw)))

def independent_consumer(mapping):
    # Full original NumPy reduction and Decimal representation; no per-chunk
    # reassociation, clipping, view selection or omitted member is permitted.
    values = []
    for name in mapping:
        array = mapping[name]
        values.append((name, array.dtype.str, array.shape, sha256(array.tobytes()).hexdigest(),
            Decimal(repr(float(np.linalg.norm(array))))))
    return tuple(values)

@pytest.mark.parametrize("ports", (False, True))
def test_same_exact_consumer_and_logical_identity_across_npz_chunks_and_frames(ports):
    arrays, raw, saved, leaves, chunked, framed, container = transport_case()
    held = []
    def selected(artifact, data):
        if not ports:
            return data
        port = real_port(artifact, data)
        held.append(port)
        return port
    bridges = [bridge_saved_arrays(saved, selected(saved.array_artifact, raw), maximum_chunk_bytes=128, maximum_slice_bytes=1024),
        bridge_chunked_arrays(chunked, {name: selected(chunk.array_artifact, leaves[name])
            for name, chunk in ((chunk.array_artifact.artifact_id, chunk) for chunk in chunked.chunks)},
            maximum_chunk_bytes=128, maximum_slice_bytes=1024),
        bridge_framed_arrays(chunked, container, selected(container, framed), maximum_chunk_bytes=128, maximum_slice_bytes=1024)]
    try:
        expected = independent_consumer(decode_matrix_arrays(raw, saved))
        assert len({bridge.reader.manifest.identity for bridge in bridges}) == 1
        for bridge in bridges:
            assert bridge.original in (saved, chunked)
            bridge.require_original(chunked)
            with bridge.reader.verified_session(block_size_bytes=128) as session:
                assert independent_consumer(bridge.array_mapping(session)) == expected
                assert session.read_member_bytes("complex", 3, 71) == arrays["complex"].tobytes()[3:71]
                delivered = tuple(bridge.iter_chunk_arrays(session, original=chunked))
                assert tuple(chunk for chunk, _ in delivered) == chunked.chunks
            assert session.final_verification.qualification == "NOT_ESTABLISHED"
        original_chunks = tuple(iter_chunk_arrays(chunked, lambda artifact: leaves[artifact.artifact_id]))
        replay = bridge_framed_arrays(chunked, container, selected(container, framed), maximum_chunk_bytes=128, maximum_slice_bytes=1024)
        try:
            with replay.reader.verified_session(block_size_bytes=128) as session:
                for (actual_chunk, actual), (old_chunk, original) in zip(replay.iter_chunk_arrays(session), original_chunks, strict=True):
                    assert actual_chunk == old_chunk and set(actual) == set(original)
                    assert all(actual[name].tobytes() == original[name].tobytes() for name in actual)
        finally:
            replay.close()
    finally:
        for bridge in bridges:
            bridge.close()
        for port in held:
            # The bridge owns duplicates; original selected ports remain live.
            cursor = port.cursor()
            try:
                assert cursor.read(0) == b""
            finally:
                cursor.close()
            port.close()

@pytest.mark.parametrize("mutation", ("missing-leaf", "surplus-leaf", "late-leaf", "container-tail", "leaf-order"))
def test_complete_transport_refuses_late_missing_or_changed_members(mutation):
    _, _, _, leaves, chunked, framed, container = transport_case()
    if mutation in ("missing-leaf", "surplus-leaf", "late-leaf"):
        changed = dict(leaves)
        if mutation == "missing-leaf":
            changed.pop(next(reversed(changed)))
        elif mutation == "surplus-leaf":
            changed["artifact.undeclared"] = b"x"
        else:
            name = next(reversed(changed))
            changed[name] = changed[name][:-1] + bytes((changed[name][-1] ^ 1,))
        with pytest.raises(ValueError, match="physical leaf|original artifact"):
            bridge_chunked_arrays(chunked, changed, maximum_chunk_bytes=128, maximum_slice_bytes=1024)
    else:
        changed = framed + b"x" if mutation == "container-tail" else b"\0" * 8 + framed[8:]
        with pytest.raises(ValueError, match="original artifact"):
            bridge_framed_arrays(chunked, container, changed, maximum_chunk_bytes=128, maximum_slice_bytes=1024)

def test_full_member_hash_failure_precedes_any_favorable_early_value():
    _, _, _, leaves, chunked, _, _ = transport_case()
    changed = replace(chunked, members=tuple(replace(member, sha256="f" * 64) if member.name == "ticks" else member for member in chunked.members))
    bridge = bridge_chunked_arrays(changed, leaves, maximum_chunk_bytes=128, maximum_slice_bytes=1024)
    try:
        with pytest.raises(ValueError, match="value hash"):
            with bridge.reader.verified_session(block_size_bytes=128):
                pytest.fail("a favorable early member cannot precede complete census verification")
    finally:
        bridge.close()

def test_actual_worker_source_binding_and_unsealed_bytes_are_refused():
    _, raw, saved, _, _, _, _ = transport_case()
    port = real_port(saved.array_artifact, raw)
    try:
        wrong = WorkerInputPort(replace(port.binding, artifact_id="fixture.substituted"), port._reader)
        with pytest.raises(ValueError, match="artifact binding"):
            bridge_saved_arrays(saved, wrong, maximum_chunk_bytes=128, maximum_slice_bytes=1024)
    finally:
        port.close()
    descriptor = _anonymous_input_descriptor()
    os.write(descriptor, raw)
    unsealed = WorkerInputPort(port.binding, _PreopenedBoundedReader(descriptor, maximum_bytes=len(raw)))
    try:
        with pytest.raises(ArtifactInputLimitExceeded, match="sealed"):
            bridge_saved_arrays(saved, unsealed, maximum_chunk_bytes=128, maximum_slice_bytes=1024)
    finally:
        unsealed.close()

def test_genuine_extra_scientific_source_is_not_dropped_to_force_logical_parity():
    _, raw, saved, leaves, chunked, _, _ = transport_case()
    extra = ObjectIdentity("fixture.genuine-extra-source", "empirical-lawhood/tests/exposed-matrix-source", "1.0.0", "9" * 64)
    changed = replace(chunked, source=extra)
    left = bridge_saved_arrays(saved, raw, maximum_chunk_bytes=128, maximum_slice_bytes=1024)
    right = bridge_chunked_arrays(changed, leaves, maximum_chunk_bytes=128, maximum_slice_bytes=1024)
    try:
        assert left.reader.manifest.identity != right.reader.manifest.identity
        assert extra in right.reader.manifest.scientific_references
        with pytest.raises(ValueError, match="source associations"):
            right.require_original(chunked)
        with pytest.raises(ValueError, match="logical dataset"):
            left.array_mapping(right.reader)
    finally:
        left.close()
        right.close()

@pytest.mark.parametrize("mutation", ("object", "shape", "fortran", "extra-member"))
def test_authenticated_physical_bytes_still_require_original_closed_npy_headers(mutation):
    arrays, _, saved, _, _, _, _ = transport_case()
    values = dict(arrays)
    if mutation == "object":
        values["state"] = np.asarray([[None]], dtype=object)
    elif mutation == "shape":
        values["state"] = values["state"].reshape(4, 6)
    elif mutation == "fortran":
        values["state"] = np.asfortranarray(values["state"])
    else:
        values["extra"] = np.zeros(1, dtype="<f8")
    stream = BytesIO()
    np.savez_compressed(stream, **values)
    raw = stream.getvalue()
    changed = replace(saved, array_artifact=replace(saved.array_artifact, sha256=sha256(raw).hexdigest(), size_bytes=len(raw)))
    with pytest.raises(ValueError, match="dtype|layout|axes|member"):
        bridge_saved_arrays(changed, raw, maximum_chunk_bytes=128, maximum_slice_bytes=1024)
    with pytest.raises(ValueError, match="dtype|layout|axes|member"):
        decode_matrix_arrays(raw, changed)

@pytest.mark.parametrize("finite_required", (False, True))
def test_explicit_nonfinite_payload_retained_or_refused_by_same_original_member_contract(finite_required):
    _, _, saved, _, _, _, _ = transport_case()
    raw, members = encode_matrix_arrays({"state": np.asarray([1., np.nan], dtype="<f8")}, nonfinite_members=("state",))
    artifact = replace(saved.array_artifact, sha256=sha256(raw).hexdigest(), size_bytes=len(raw))
    changed = replace(saved, array_artifact=artifact, members=tuple(replace(member, finite_required=finite_required) for member in members))
    bridge = bridge_saved_arrays(changed, raw, maximum_chunk_bytes=128, maximum_slice_bytes=1024)
    try:
        if finite_required:
            with pytest.raises(ValueError, match="finite"):
                with bridge.reader.verified_session(block_size_bytes=128):
                    pytest.fail("finite-required controls must precede scientific delivery")
        else:
            with bridge.reader.verified_session(block_size_bytes=128) as session:
                assert session.read_array("state").tobytes() == np.asarray([1., np.nan], dtype="<f8").tobytes()
    finally:
        bridge.close()

def test_bridge_authenticated_physical_and_member_selection_cannot_be_rebound():
    _, raw, saved, _, _, _, _ = transport_case()
    bridge = bridge_saved_arrays(saved, raw, maximum_chunk_bytes=128, maximum_slice_bytes=1024)
    try:
        source = bridge._source
        for selected, field, replacement in ((source, "physical", ()), (source, "intervals", {}),
                (source.leaves[0], "physical", None), (source.physical[0], "_bytes", b"other")):
            with pytest.raises(AttributeError, match="read-only"):
                setattr(selected, field, replacement)
        with bridge.reader.verified_session(block_size_bytes=128) as session:
            mapping = bridge.array_mapping(session)
            with pytest.raises(AttributeError, match="read-only"):
                mapping.names = ()
            assert set(mapping) == {member.name for member in saved.members}
    finally:
        bridge.close()

def test_exact_historical_response_owner_keeps_absent_allocation_and_original_identity():
    _, raw, saved, _, _, _, _ = transport_case()
    historical = MatrixResponseArrays("fixture.historical.response", saved.array_artifact, saved.members, saved.producers)
    bridge = bridge_saved_arrays(historical, raw, maximum_chunk_bytes=128, maximum_slice_bytes=1024)
    bound = bridge_saved_arrays(historical, raw, maximum_chunk_bytes=128, maximum_slice_bytes=1024,
        scientific_references=(saved.allocation,))
    try:
        assert bridge.original is historical and not hasattr(bridge.original, "allocation")
        assert saved.allocation not in bridge.reader.manifest.scientific_references
        assert saved.allocation in bound.reader.manifest.scientific_references
        assert bridge.reader.manifest.identity != bound.reader.manifest.identity
        with bound.reader.verified_session(block_size_bytes=128) as session:
            assert independent_consumer(bound.array_mapping(session)) == independent_consumer(decode_matrix_arrays(raw, historical))
    finally:
        bridge.close()
        bound.close()

@pytest.mark.parametrize("defect", ("exact", "source", "allocation", "exposed-sha", "access", "visibility", "producers"))
def test_shared_worker_bridge_retains_every_original_eligible_array_guard(stock, defect):  # noqa: F811
    from empirical_lawhood.adapters.methods.matrix_factor_response import eligibility as selected
    _, source = stock
    arrays = {"momenta": np.zeros((3, 2, 3, 4, 4), dtype="<c16"), "positions": np.ones((3, 2, 3, 4, 4), dtype="<c16")}
    raw, members = encode_matrix_arrays(arrays)
    artifact = ArtifactIdentity("fixture.guarded.eligible", "matrix-arrays", MATRIX_ARRAY_SCHEMA,
        sha256(raw).hexdigest(), "application/x-npz", len(raw))
    owner = selected.EligibleMatrixArrays("fixture.guarded.owner", source.allocation.identity, selected.identity(source),
        "root.confirmation", "ORIGIN", artifact, members, (selected.identity(source),),
        OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE)
    held = real_port(artifact, raw)
    port = WorkerInputPort(replace(held.binding, outcome_access=OutcomeAccess.OUTCOME_BLIND,
        visibility_ceiling=VisibilityCeiling.PROSPECTIVE), held._reader)
    expected_producers = owner.producers
    if defect == "source":
        owner = replace(owner, source=replace(owner.source, object_fingerprint="a" * 64))
    elif defect == "allocation":
        owner = replace(owner, allocation=replace(owner.allocation, object_fingerprint="a" * 64))
    elif defect == "exposed-sha":
        owner = replace(owner, array_artifact=replace(artifact, sha256=source.allocation.exposure.exposed_artifact_sha256s[0]))
    elif defect == "access":
        port = WorkerInputPort(replace(port.binding, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE), held._reader)
    elif defect == "visibility":
        port = WorkerInputPort(replace(port.binding, visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY), held._reader)
    elif defect == "producers":
        expected_producers = (replace(owner.producers[0], object_fingerprint="a" * 64),)
    try:
        kwargs = dict(expected_producers=expected_producers, maximum_chunk_bytes=65536,
            maximum_slice_bytes=16384, source=SimpleNamespace(eligible=source))
        if defect != "exact":
            with pytest.raises(ValueError, match="eligible arrays|eligible worker"):
                bridge_worker_arrays({artifact.artifact_id: port}, owner, **kwargs)
            assert port.bytes_read == 0
        else:
            bridge = bridge_worker_arrays({artifact.artifact_id: port}, owner, **kwargs)
            try:
                with bridge.reader.verified_session(block_size_bytes=65536) as reader:
                    assert all(reader.read_array(name).tobytes() == value.tobytes() for name, value in arrays.items())
                assert reader.final_verification.scientific_authority == "NONE"
            finally:
                bridge.close()
    finally:
        held.close()
