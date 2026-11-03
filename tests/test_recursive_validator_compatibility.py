# SPDX-License-Identifier: MPL-2.0
"""Current format and complete custody under disclosed producing stamps.

The producing-stamp seam changes provenance only. Actual writers, current
structural validators, atomic publications and retained reads all execute.
No historical module, scientific source, native work or qualification is used.
"""

from dataclasses import replace
from hashlib import sha256
import shutil

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_NPZ_CODEC
from empirical_lawhood.infrastructure.artifact_validation import ArtifactProfileValidatorRegistry
from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict, ExternalArtifactPlane
from empirical_lawhood.infrastructure.matrix_array_io import encode_matrix_arrays
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactGenericValidation, ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.execution import VerifiedArtifactInput
from tests.numerical_provenance_fixtures import numerical_plane


@pytest.fixture
def retained(tmp_path, monkeypatch):
    base = numerical_plane(tmp_path / "producing")
    producing = ExternalArtifactPlane(base.root,
        validators=ArtifactProfileValidatorRegistry(binary_codecs=(MATRIX_NPZ_CODEC,)))
    record = ObjectIdentity("software.generic.record", ObjectIdentity.SCHEMA, "1.0.0", "a" * 64)
    arrays, _ = encode_matrix_arrays({"complex": np.asarray([1 + 2j, 3 - 4j], dtype="<c16")})
    requests = (ArtifactWriteRequest(record.object_id, "records/original.json", record.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, "application/json", "software.generic.atomic", "records",
        record.canonical_bytes(), VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE),
        ArtifactWriteRequest("software.generic.matrix", "records/original.npz", MATRIX_ARRAY_SCHEMA,
        ArtifactProfile.MATRIX_ARRAY_NPZ, "application/x-npz", "software.generic.atomic", "records", arrays,
        VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE))
    actual_stamp = ArtifactProfileValidatorRegistry.generic_validation

    def producing_stamp(registry, *, profile, payload_schema):
        value = actual_stamp(registry, profile=profile, payload_schema=payload_schema)
        return replace(value, validator_version="9.8.7",
            validator_implementation_sha256=sha256(b"disclosed independent producing build").hexdigest())

    # Only declared producing provenance differs. No validator or custody
    # callback is mocked, and no manifest is rewritten after publication.
    with monkeypatch.context() as origin:
        origin.setattr(ArtifactProfileValidatorRegistry, "generic_validation", producing_stamp)
        publications = producing.write_batch(requests)
    recovered = numerical_plane(tmp_path / "recovered")
    shutil.copytree(base.root.contract.canonical_path, recovered.root.contract.canonical_path, dirs_exist_ok=True)
    current = ExternalArtifactPlane(recovered.root,
        validators=ArtifactProfileValidatorRegistry(binary_codecs=(MATRIX_NPZ_CODEC,)))
    return current, publications, (record.canonical_bytes(), arrays)


def read(plane, publication):
    port = plane.open(VerifiedArtifactInput(publication.logical, publication.materialization),
        maximum_bytes=publication.materialization.size_bytes)
    try:
        return port.read()
    finally:
        port.close()


def test_current_decoders_relocate_actual_publication_and_preserve_producing_stamps(retained):
    current, publications, payloads = retained
    saved = {}
    for publication in publications:
        manifest = current.root.resolve(publication.manifest_materialization.relative_path, for_write=False)
        saved[manifest] = manifest.read_bytes()
        original = publication.logical.generic_validation
        assert original.validator_version == "9.8.7"
        assert current.validators.require_generic_validation(original) is original
        assert original != current.validators.generic_validation(profile=original.profile,
            payload_schema=original.payload_schema)
    for publication, payload in zip(publications, payloads, strict=True):
        assert read(current, publication) == payload
    assert all(path.read_bytes() == raw for path, raw in saved.items())
    record = ObjectIdentity("software.generic.current", ObjectIdentity.SCHEMA, "1.0.0", "b" * 64)
    written = current.write(ArtifactWriteRequest(record.object_id, "current/value.json", record.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, "application/json", "software.generic.current", "current",
        record.canonical_bytes(), VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE))
    assert written.logical.generic_validation == current.validators.generic_validation(
        profile=ArtifactProfile.CANONICAL_JSON, payload_schema=record.SCHEMA)


@pytest.mark.parametrize("damage", ("same-size", "truncated"))
def test_current_read_refuses_corrupt_or_truncated_unrequested_sibling(retained, damage):
    current, publications, payloads = retained
    path = current.root.resolve(publications[1].materialization.relative_path, for_write=False)
    raw = payloads[1]
    path.write_bytes(bytes([raw[0] ^ 1]) + raw[1:] if damage == "same-size" else raw[:-1])
    with pytest.raises(ArtifactIdentityConflict):
        read(current, publications[0])


@pytest.mark.parametrize("where", ("caller", "sidecar"))
def test_producing_stamp_substitution_changes_committed_manifest_identity(retained, where):
    current, publications, _ = retained
    publication = publications[1]
    original = publication.logical.generic_validation
    changed = replace(original, validator_implementation_sha256="c" * 64)
    if where == "caller":
        altered = replace(publication, logical=replace(publication.logical, generic_validation=changed))
        with pytest.raises(ArtifactIdentityConflict):
            read(current, altered)
    else:
        sidecar = current.root.resolve(publication.manifest_materialization.relative_path, for_write=False)
        raw = sidecar.read_bytes()
        needle = original.validator_implementation_sha256.encode()
        assert raw.count(needle) == 1
        sidecar.write_bytes(raw.replace(needle, changed.validator_implementation_sha256.encode()))
        with pytest.raises(ArtifactIdentityConflict):
            read(current, publications[0])


def test_producing_stamp_cannot_supply_a_missing_current_decoder(retained):
    current, publications, _ = retained
    absent = ExternalArtifactPlane(current.root, validators=ArtifactProfileValidatorRegistry())
    with pytest.raises(ArtifactIdentityConflict):
        read(absent, publications[0])


@pytest.mark.parametrize("damage", ("foreign-key", "untyped-profile", "untyped-stamp", "disabled-profile"))
def test_provenance_lookup_retains_current_identity_domain_refusals(damage):
    registry = ArtifactProfileValidatorRegistry(binary_codecs=(MATRIX_NPZ_CODEC,))
    value = registry.generic_validation(profile=ArtifactProfile.MATRIX_ARRAY_NPZ, payload_schema=MATRIX_ARRAY_SCHEMA)
    if damage == "foreign-key":
        value = replace(value, validator_key="artifact-profile.raw-source-bytes")
    elif damage == "untyped-profile":
        value = replace(value, profile="MATRIX_ARRAY_NPZ")
    elif damage == "untyped-stamp":
        value = dict(validator_key=value.validator_key)
    else:
        value = ArtifactGenericValidation("artifact-profile.audited-hdf5", "9.8.7", "a" * 64,
            "empirical-lawhood/tests/unregistered-hdf5", ArtifactProfile.AUDITED_HDF5)
    with pytest.raises((ArtifactIdentityConflict, TypeError, ValueError)):
        registry.require_generic_validation(value)
