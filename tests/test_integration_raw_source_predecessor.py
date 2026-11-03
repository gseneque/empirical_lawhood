# SPDX-License-Identifier: MPL-2.0
"""Retained raw custody under current decoders; no scientific/native qualification.

The preserved atomic RAW publication retains its exact producing stamps.
The current integration registry validates every actual sibling and current raw
contract. No old module is imported or producing observation rewritten.
"""
import base64
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
import pytest

from empirical_lawhood.api.integration_artifact_profiles import integration_artifact_profile_validators
from empirical_lawhood.api.recursive_operations import operation_storage_codecs
from empirical_lawhood.infrastructure.artifact_validation import ArtifactProfileValidatorRegistry
from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict, ExternalArtifactPlane
from empirical_lawhood.infrastructure.matrix_array_io import decode_native_matrix_arrays, encode_matrix_arrays
from empirical_lawhood.infrastructure.publication_metadata import authenticate_published_materialization
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import (
    ArtifactCustodyLimits, ArtifactProfile, ArtifactSemanticValidation, ArtifactWriteRequest, ArtifactWriteResult,
)
from tests.numerical_provenance_fixtures import numerical_plane

RAW_SCHEMA = "empirical-lawhood/source/checksummed-uninterpreted-public-bytes"
PLAIN_RAW_SHA = "66f95a3adf1610af6982f2d4fecf49bb78c2e3b0cef3e1ab01b6b05a70862914"


def raw_request(raw=b"literal exposed audit support", *, media_type="text/plain"):
    return ArtifactWriteRequest("software.predecessor.raw", "records/audit.bin", RAW_SCHEMA,
        ArtifactProfile.RAW_SOURCE_BYTES, media_type, "software.predecessor.atomic", "records", raw,
        VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE)


def original_fixture():
    raw = (Path(__file__).parent / "fixtures/custody-validator/plain-raw-1.7.0-atomic.json").read_bytes()
    assert sha256(raw).hexdigest() == "3c2a70cff6b78b909dcc6ca668e0867b11b3c8d640952593514533f0806a6eb0"
    fixture = json.loads(raw)
    publications = []
    for row in fixture["publications"]:
        encoded = base64.b64decode(row["base64"], validate=True)
        assert len(encoded) == row["bytes"] and sha256(encoded).hexdigest() == row["sha256"]
        publications.append(decode_canonical_bytes(encoded, ArtifactWriteResult, maximum_bytes=len(encoded)))
    assert len(publications) == 2
    return fixture, tuple(publications)


def previous_batch(tmp_path):
    fixture, (requested, sibling) = original_fixture()
    base = numerical_plane(tmp_path / "custody")
    assert base.root.contract.storage_root_id == fixture["storage_root_id"]
    for row in fixture["files"]:
        raw = base64.b64decode(row["base64"], validate=True)
        assert len(raw) == row["bytes"] and sha256(raw).hexdigest() == row["sha256"]
        path = base.root.resolve(row["relative_path"], for_write=True)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    for publication in (requested, sibling):
        assert publication.logical.generic_validation.validator_version == "1.7.0"
        assert publication.logical.generic_validation.validator_implementation_sha256 == PLAIN_RAW_SHA
    current = ExternalArtifactPlane(base.root, validators=integration_artifact_profile_validators())
    return base, current, requested, sibling


def test_real_atomic_raw_publications_revalidate_with_current_registry(tmp_path):
    previous, current, requested, sibling = previous_batch(tmp_path)
    fixture, _ = original_fixture()
    paths = tuple(previous.root.resolve(row["relative_path"], for_write=False) for row in fixture["files"])
    before = tuple(path.read_bytes() for path in paths)
    actual = authenticate_published_materialization(current, requested)
    assert actual.logical == requested.logical and actual.materialization == requested.materialization
    assert len(actual.publication.members) == 2
    assert authenticate_published_materialization(current, sibling).logical == sibling.logical
    assert current.root.resolve(requested.materialization.relative_path, for_write=False).read_bytes() == (
        b"literal exposed requested support")
    assert tuple(path.read_bytes() for path in paths) == before


def test_raw_producing_stamp_is_preserved_and_foreign_key_refuses():
    _, (publication, _) = original_fixture()
    observed = publication.logical.generic_validation
    registry = integration_artifact_profile_validators()
    assert observed.validator_implementation_sha256 == PLAIN_RAW_SHA
    assert registry.require_generic_validation(observed) is observed
    independent = replace(observed, validator_version="9.8.7", validator_implementation_sha256="0" * 64)
    assert registry.require_generic_validation(independent) is independent
    with pytest.raises(ArtifactIdentityConflict, match="current domain"):
        registry.require_generic_validation(replace(observed, validator_key="artifact-profile.canonical-json"))


def test_raw_sibling_corruption_refuses_when_only_other_member_requested(tmp_path):
    previous, current, requested, sibling = previous_batch(tmp_path)
    path = previous.root.resolve(sibling.materialization.relative_path, for_write=False)
    raw = path.read_bytes()
    try:
        path.write_bytes(b"x" * len(raw))
        with pytest.raises(ArtifactIdentityConflict, match="bytes differ"):
            authenticate_published_materialization(current, requested)
    finally:
        path.write_bytes(raw)
    authenticate_published_materialization(current, requested)


@pytest.mark.parametrize("invalid", ("empty", "semantic", "media"))
def test_registered_raw_contract_still_refuses_unsupported_payload_claims(tmp_path, invalid):
    plane = numerical_plane(tmp_path / "custody")
    current = ExternalArtifactPlane(plane.root, validators=integration_artifact_profile_validators())
    selected = raw_request()
    if invalid == "empty":
        selected = replace(selected, payload=b"")
    elif invalid == "semantic":
        semantic = ArtifactSemanticValidation("software.disclosed.semantic", "1.0.0", "a" * 64,
            RAW_SCHEMA, ArtifactProfile.RAW_SOURCE_BYTES)
        selected = replace(selected, semantic_validation=semantic)
    else:
        selected = replace(selected, media_type="application/octet-stream")
    with pytest.raises(ArtifactIdentityConflict):
        current.write_batch((selected,))
    assert not current.root.resolve(selected.relative_path, for_write=False).exists()
    assert not current.root.resolve(selected.relative_path + ".manifest.json", for_write=False).exists()


def test_existing_raw_custody_limit_still_bounds_complete_old_publication(tmp_path):
    previous, current, requested, sibling = previous_batch(tmp_path)
    limited = ExternalArtifactPlane(previous.root, validators=current.validators,
        custody_limits=ArtifactCustodyLimits(raw_source_bytes=min(requested.materialization.size_bytes, sibling.materialization.size_bytes) - 1))
    with pytest.raises(ArtifactIdentityConflict, match="byte|contract|limit"):
        authenticate_published_materialization(limited, requested)


def test_current_canonical_and_registered_matrix_identities_and_values_are_unchanged(tmp_path):
    # Integration selects the same current decoder contracts and retains
    # received array values; producing stamps do not choose an implementation.
    current = integration_artifact_profile_validators()
    unchanged = ArtifactProfileValidatorRegistry(binary_codecs=operation_storage_codecs())
    for profile, schema in ((ArtifactProfile.CANONICAL_JSON, ObjectIdentity.SCHEMA),
            (ArtifactProfile.MATRIX_ARRAY_NPZ, MATRIX_ARRAY_SCHEMA)):
        assert current.generic_validation(profile=profile, payload_schema=schema) == unchanged.generic_validation(
            profile=profile, payload_schema=schema)
    base = numerical_plane(tmp_path / "current")
    plane = ExternalArtifactPlane(base.root, validators=current)
    values = {"complex": np.asarray([1 + 2j, 3 - 4j], dtype="<c16")}
    raw, _ = encode_matrix_arrays(values)
    record = ObjectIdentity("software.current.canonical", ObjectIdentity.SCHEMA, "1.0.0", "b" * 64)
    canonical, result = plane.write_batch((ArtifactWriteRequest(record.object_id, "records/current.json",
        record.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", "software.current.atomic", "records",
        record.canonical_bytes(), VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE),
        ArtifactWriteRequest("software.current.matrix", "records/current.npz", MATRIX_ARRAY_SCHEMA,
            ArtifactProfile.MATRIX_ARRAY_NPZ, "application/x-npz", "software.current.atomic", "records", raw,
            VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE)))
    authenticate_published_materialization(plane, canonical)
    authenticate_published_materialization(plane, result)
    canonical_raw = plane.root.resolve(canonical.materialization.relative_path, for_write=False).read_bytes()
    assert decode_canonical_bytes(canonical_raw, ObjectIdentity, maximum_bytes=len(canonical_raw)) == record
    received = plane.root.resolve(result.materialization.relative_path, for_write=False).read_bytes()
    assert received == raw
    decoded = decode_native_matrix_arrays(received, {"complex": ("<c16", (2,))})
    np.testing.assert_array_equal(decoded["complex"], values["complex"])
