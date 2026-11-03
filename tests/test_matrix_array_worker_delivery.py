# SPDX-License-Identifier: MPL-2.0
"""Actual anonymous ports and exact exposed arrays; no scientific qualification."""

from dataclasses import replace
from hashlib import sha256
from io import BytesIO
import shutil

import numpy as np
import pytest

from empirical_lawhood.infrastructure.matrix_array_io import encode_matrix_arrays, iter_worker_matrix_array_chunks
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import (
    MATRIX_ARRAY_SCHEMA, MATRIX_NATIVE_PURPOSES, MatrixAllocation, MatrixPurposeSeed,
    MatrixRootAllocation, SavedMatrixArrays,
)
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest, ArtifactSemanticValidationRegistry
from empirical_lawhood.runtime.execution import VerifiedArtifactInput
from empirical_lawhood.runtime.recursive_handoff import RecursiveWaveMember
from tests.test_recursive_public_service import _plane as _standard_plane

def _plane(root):
    from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_STORAGE_CODECS
    from empirical_lawhood.infrastructure.artifact_validation import ArtifactProfileValidatorRegistry

    plane = _standard_plane(root)
    plane.validators = ArtifactProfileValidatorRegistry(binary_codecs=MATRIX_STORAGE_CODECS)
    return plane



def stock(tmp_path, *, arrays=None, nonfinite=()):
    plane = _plane(tmp_path / "selected")
    allocation = MatrixAllocation("allocation.exposed.worker", (
        MatrixRootAllocation("root.exposed.worker", "constructed",
            tuple(MatrixPurposeSeed(name, number + 1) for number, name in enumerate(MATRIX_NATIVE_PURPOSES)),
            conditioning_seeds=(MatrixPurposeSeed("passive-probes", 123, "PCG64DXSM"),)),))
    values = arrays if arrays is not None else {
        "complex": (np.arange(51, dtype="<f8") + 1j * np.arange(51, dtype="<f8")[::-1]).reshape(3, 17),
        "empty": np.empty((0, 2), dtype="<f8"),
        "mask": np.asarray([True, False, True], dtype="|b1"),
    }
    raw, members = encode_matrix_arrays(values, nonfinite_members=nonfinite)
    producers = (ObjectIdentity("source.exposed.worker", "empirical-lawhood/testing/exposed-source", "1.0.0", "a" * 64),)
    artifact = ArtifactIdentity("array.exposed.worker", "matrix-arrays", MATRIX_ARRAY_SCHEMA,
                                sha256(raw).hexdigest(), "application/x-npz", len(raw))
    manifest = SavedMatrixArrays("operand.exposed.worker", allocation.identity, artifact, members, producers)
    published = plane.write(ArtifactWriteRequest(artifact.artifact_id, "arrays/selected.npz", MATRIX_ARRAY_SCHEMA,
        ArtifactProfile.MATRIX_ARRAY_NPZ, "application/x-npz", "publication.exposed.worker", "arrays", raw,
        VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE))
    return plane, allocation, manifest, values, raw, VerifiedArtifactInput(published.logical, published.materialization)


def consume(plane, value, manifest, allocation):
    port = plane.open(value, maximum_bytes=manifest.array_artifact.size_bytes)
    try:
        observed = {member.name: [] for member in manifest.members}
        offsets = {member.name: 0 for member in manifest.members}
        for member, offset, chunk in iter_worker_matrix_array_chunks(port, manifest=manifest,
                allocation=allocation, expected_producers=manifest.producers, maximum_chunk_bytes=32):
            assert offset == offsets[member.name]
            assert not chunk.flags.writeable and chunk.nbytes <= 32
            observed[member.name].append(chunk)
            offsets[member.name] += chunk.size
        assert port.bytes_read == 0  # bounded replay cursors own the actual same-FD reads
        return {member.name: np.concatenate(observed[member.name]).reshape(member.shape) for member in manifest.members}
    finally:
        port.close()


def test_actual_npz_port_delivers_complete_complex_census_after_relocation(tmp_path):
    plane, allocation, manifest, expected, _, value = stock(tmp_path)
    actual = consume(plane, value, manifest, allocation)
    for name in expected:
        np.testing.assert_array_equal(actual[name], expected[name])
        assert actual[name].dtype.str == expected[name].dtype.str
    selected = tmp_path / "relocated"
    relocated = _plane(selected)
    shutil.copytree(plane.root.contract.canonical_path, selected, dirs_exist_ok=True)
    recovered = consume(relocated, value, manifest, allocation)
    for name in expected:
        np.testing.assert_array_equal(recovered[name], expected[name])


def test_lazy_authored_npz_member_keeps_exact_raw_identity_and_custody(tmp_path):
    from pathlib import Path
    from empirical_lawhood.infrastructure.recursive_custody import AuthenticatedRecursivePayloads

    plane, _, manifest, _, raw, _ = stock(tmp_path)
    member = RecursiveWaveMember("selected.npz", ObjectIdentity("recursive-member.exposed-arrays",
        MATRIX_ARRAY_SCHEMA, "1.0.0", manifest.array_artifact.sha256), len(raw))
    payloads = AuthenticatedRecursivePayloads(plane=plane,
        directory=Path(plane.root.contract.canonical_path) / "arrays", members=(member,))
    assert payloads["selected.npz"] == raw
    assert payloads.manifest("selected.npz").logical.profile is ArtifactProfile.MATRIX_ARRAY_NPZ


def test_causal_predictor_can_join_allocation_identity_without_receiving_future_seeds(tmp_path):
    plane, allocation, manifest, expected, _, value = stock(tmp_path)
    # The only allocation operand delivered is its canonical identity; future
    # driver labels and seed values are neither copied nor decoded by this port.
    public_identity = allocation.identity
    actual = consume(plane, value, manifest, public_identity)
    for name in expected:
        np.testing.assert_array_equal(actual[name], expected[name])
    wrong_schema = replace(public_identity, object_schema="empirical-lawhood/testing/another-allocation")
    with pytest.raises(ValueError, match="allocation identity"):
        consume(plane, value, manifest, wrong_schema)


@pytest.mark.parametrize("damage", ("bytes", "member-digest", "shape", "allocation", "producers"))
def test_worker_refuses_exact_identity_substitution_before_any_value(tmp_path, damage):
    plane, allocation, manifest, _, raw, value = stock(tmp_path)
    if damage == "bytes":
        target = plane.root.resolve(value.materialization.relative_path, for_write=False)
        target.write_bytes(raw[:-1] + bytes((raw[-1] ^ 1,)))
        with pytest.raises((ValueError, RuntimeError)):
            plane.open(value, maximum_bytes=len(raw))
        return
    member = manifest.members[0]
    if damage == "member-digest":
        manifest = replace(manifest, members=(replace(member, sha256="b" * 64), *manifest.members[1:]))
    elif damage == "shape":
        manifest = replace(manifest, members=(replace(member, shape=(51,)), *manifest.members[1:]))
    elif damage == "allocation":
        allocation = replace(allocation, allocation_id="allocation.other")
    else:
        manifest = replace(manifest, producers=(replace(manifest.producers[0], object_id="source.other"),))
    port = plane.open(value, maximum_bytes=len(raw))
    try:
        iterator = iter_worker_matrix_array_chunks(port, manifest=manifest, allocation=allocation,
            expected_producers=(ObjectIdentity("source.exposed.worker", "empirical-lawhood/testing/exposed-source", "1.0.0", "a" * 64),))
        with pytest.raises(ValueError):
            next(iterator)
    finally:
        port.close()


def test_late_nonfinite_member_refuses_before_favourable_early_values(tmp_path):
    plane, allocation, manifest, _, raw, value = stock(tmp_path,
        arrays={"a": np.ones(3, dtype="<f8"), "z": np.asarray([np.nan], dtype="<f8")}, nonfinite=("z",))
    manifest = replace(manifest, members=tuple(replace(member, finite_required=True) for member in manifest.members))
    port = plane.open(value, maximum_bytes=len(raw))
    try:
        with pytest.raises(ValueError, match="finite population"):
            next(iter_worker_matrix_array_chunks(port, manifest=manifest, allocation=allocation,
                expected_producers=manifest.producers))
    finally:
        port.close()


@pytest.mark.parametrize("dtype", (object, "<f4"))
def test_selected_npz_profile_refuses_unsupported_or_pickle_values(tmp_path, dtype):
    plane = _plane(tmp_path / "selected")
    stream = BytesIO()
    np.savez(stream, unsafe=np.asarray([1], dtype=dtype))
    with pytest.raises((ValueError, RuntimeError), match="unsafe"):
        plane.write(ArtifactWriteRequest("array.exposed.unsafe", "arrays/unsafe.npz", MATRIX_ARRAY_SCHEMA,
            ArtifactProfile.MATRIX_ARRAY_NPZ, "application/x-npz", "publication.exposed.unsafe", "arrays", stream.getvalue(),
            VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE))


def test_recursive_raw_output_has_capability_semantics_and_exact_port_custody(tmp_path):
    """Use registered output mechanics; this is an exposed software output."""
    from empirical_lawhood.adapters.methods.analytic_material_inquiry.executable_binding import EXECUTABLE_BINDING_FACTORIES
    from empirical_lawhood.runtime.plans import OutputTemplate
    from empirical_lawhood.runtime.recursive_provider import RecursiveOperationProviderFactory, recursive_operation_binding
    from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_STORAGE_CODECS

    template = EXECUTABLE_BINDING_FACTORIES[0]
    outputs = (OutputTemplate("arrays", MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ,
                              "application/x-npz", ".npz"),
               OutputTemplate("manifest", SavedMatrixArrays.SCHEMA, ArtifactProfile.CANONICAL_JSON,
                              "application/json", ".json"))
    registration = replace(template.registration, outputs=outputs, storage_codecs=MATRIX_STORAGE_CODECS)
    capability = replace(template.manifest, output_schema_ids=tuple(sorted((MATRIX_ARRAY_SCHEMA, SavedMatrixArrays.SCHEMA))))
    factory = RecursiveOperationProviderFactory(recursive_operation_binding(registration=registration,
        manifest=capability), registration, capability, template.runner_factory,
        {SavedMatrixArrays.SCHEMA: SavedMatrixArrays})
    from empirical_lawhood.runtime.capabilities import CapabilityRegistry
    from empirical_lawhood.runtime.recursive_provider import RecursiveOperationProvider

    registry = CapabilityRegistry("registry.exposed.array-output", (capability,))
    provider = RecursiveOperationProvider(registry, registration, capability, factory.runner_factory,
        factory.output_codecs, None)
    contracts = provider.output_semantic_contracts(registry)
    raw_contract = next(value for value in contracts if value.profile is ArtifactProfile.MATRIX_ARRAY_NPZ)
    assert raw_contract.top_level_keys == raw_contract.value_keys == ()
    plane, allocation, manifest, expected, raw, _ = stock(tmp_path)
    semantic = raw_contract.artifact_validation_registration(
        logical_artifact_id="array.exposed.output", task_id="task.exposed.output", output_id="arrays")
    view = plane.with_semantic_validation_registry(ArtifactSemanticValidationRegistry.from_registrations(
        registry_id="semantics.exposed.array-output", registrations=(semantic,)))
    written = view.write(ArtifactWriteRequest("array.exposed.output", "outputs/arrays.npz", MATRIX_ARRAY_SCHEMA,
        ArtifactProfile.MATRIX_ARRAY_NPZ, "application/x-npz", "publication.exposed.array-output", "outputs", raw,
        VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE,
        semantic_validation=semantic.validation))
    changed = replace(manifest, array_artifact=replace(manifest.array_artifact, artifact_id="array.exposed.output"))
    assert written.logical.semantic_validation == semantic.validation
    actual = consume(view, VerifiedArtifactInput(written.logical, written.materialization), changed, allocation)
    for name in expected:
        np.testing.assert_array_equal(actual[name], expected[name])


@pytest.mark.parametrize("wrong", ("schema", "media", "profile"))
def test_raw_output_seam_cannot_exempt_another_transport(wrong):
    from empirical_lawhood.adapters.methods.analytic_material_inquiry.executable_binding import EXECUTABLE_BINDING_FACTORIES
    from empirical_lawhood.runtime.plans import OutputTemplate
    from empirical_lawhood.runtime.recursive_provider import RecursiveOperationProviderFactory, recursive_operation_binding

    template = EXECUTABLE_BINDING_FACTORIES[0]
    schema = "empirical-lawhood/testing/another-array" if wrong == "schema" else MATRIX_ARRAY_SCHEMA
    media = "application/octet-stream" if wrong == "media" else "application/x-npz"
    profile = ArtifactProfile.NUMPY_NO_PICKLE if wrong == "profile" else ArtifactProfile.MATRIX_ARRAY_NPZ
    registration = replace(template.registration, outputs=(OutputTemplate("arrays", schema, profile, media, ".npz"),))
    capability = replace(template.manifest, output_schema_ids=(schema,))
    with pytest.raises(ValueError, match="exact typed codec"):
        RecursiveOperationProviderFactory(recursive_operation_binding(registration=registration,
            manifest=capability), registration, capability, template.runner_factory, {})
