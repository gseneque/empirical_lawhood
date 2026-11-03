# SPDX-License-Identifier: MPL-2.0
"""Exact legacy sidecar codecs using exposed metadata, without custody claims."""

import json
from dataclasses import replace
from hashlib import sha256

import pytest

from empirical_lawhood.infrastructure import task_receipts
from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest, encode_artifact_manifest
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalizationError
from empirical_lawhood.runtime.artifacts import (
    ArtifactGenericValidation, ArtifactManifest, ArtifactMaterialization, ArtifactProfile,
    ArtifactPublicationBinding, ArtifactPublicationCommit, ArtifactPublicationScope,
    LogicalArtifactIdentity, artifact_publication_batch_id, artifact_publication_commit_relative_path,
    artifact_publication_member,
)


def _manifests(count=4, *, media_type="application/json"):
    generic = ArtifactGenericValidation("exposed.codec", "1.0.0", "b" * 64,
        ObjectIdentity.SCHEMA, ArtifactProfile.CANONICAL_JSON)
    pairs = []
    for index in range(count):
        digest = sha256(("exposed software member " + str(index)).encode()).hexdigest()
        logical = LogicalArtifactIdentity("exposed.member." + str(index), digest,
            ObjectIdentity.SCHEMA, ArtifactProfile.CANONICAL_JSON, media_type,
            VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND, generic)
        physical = ArtifactMaterialization("exposed.materialization." + str(index),
            logical.logical_artifact_id, "exposed.storage", "outputs/member-" + str(index) + ".json",
            digest, index + 1, "none")
        pairs.append((logical, physical))
    scope = ArtifactPublicationScope("exposed.publication", "exposed.storage", "outputs",
        VisibilityCeiling.PROSPECTIVE, OutcomeAccess.OUTCOME_BLIND)
    members = tuple(sorted((artifact_publication_member(*pair) for pair in pairs),
        key=lambda row: row.materialization_id))
    batch = artifact_publication_batch_id(scope, members)
    commit = ArtifactPublicationCommit(batch, scope, members).canonical_bytes()
    binding = ArtifactPublicationBinding(batch, scope, artifact_publication_commit_relative_path(scope, batch),
        sha256(commit).hexdigest(), len(commit), members)
    return tuple(ArtifactManifest(*pair, binding) for pair in pairs)


@pytest.mark.parametrize("count", (1, 4, 64))
def test_known_publication_matches_original_canonical_bytes_and_shared_records(count):
    manifests = _manifests(count)
    binding = manifests[0].publication
    for original in manifests:
        raw = original.canonical_bytes()
        assert encode_artifact_manifest(original.logical, original.materialization, binding) == raw
        assert decode_artifact_manifest(raw) == original
        decoded = decode_artifact_manifest(raw, publication=binding, maximum_bytes=len(raw))
        assert decoded == original
        assert decoded.publication is binding
        assert decoded.publication.members is binding.members
        assert not hasattr(decoded, "_canonical_encoding")
        assert decoded.canonical_bytes() == raw
        assert decoded.fingerprint() == sha256(raw).hexdigest()


def test_known_publication_does_not_redecode_roster_and_omitted_argument_keeps_original_path(monkeypatch):
    original = _manifests()[0]
    raw = original.canonical_bytes()
    calls = []
    old = task_receipts._publication_binding

    def observed(document):
        calls.append(document)
        return old(document)

    monkeypatch.setattr(task_receipts, "_publication_binding", observed)
    assert decode_artifact_manifest(raw) == original
    assert len(calls) == 1
    assert decode_artifact_manifest(raw, publication=None) == original
    assert len(calls) == 2
    decoded = decode_artifact_manifest(raw, publication=original.publication)
    assert decoded == original and decoded.publication is original.publication
    assert len(calls) == 2


@pytest.mark.parametrize("media_type", (
    'application/json; marker=,"publication":null},"version":"1.0.0"}',
    'application/json; marker={"logical":"other","publication":{"members":[]}}',
    "application/json; marker=α\\quoted\"value",
))
def test_escaped_embedded_delimiters_and_unicode_are_metadata_not_split_points(media_type):
    original = _manifests(media_type=media_type)[0]
    raw = original.canonical_bytes()
    decoded = decode_artifact_manifest(raw, publication=original.publication)
    assert decoded == original
    assert decoded.logical.media_type == media_type
    assert encode_artifact_manifest(decoded.logical, decoded.materialization, decoded.publication) == raw


@pytest.mark.parametrize("change", (
    lambda raw: raw[:-1],
    lambda raw: raw + b"\n",
    lambda raw: b" " + raw,
    lambda raw: raw.replace(b'"publication":', b'"publication": ', 1),
    lambda raw: raw[:-8] + b'2.0.0"}\n',
    lambda raw: raw.replace(b'"schema":"empirical-lawhood/runtime/artifact-manifest"',
        b'"schema":"empirical-lawhood/testing/unknown-manifest"', 1),
    lambda raw: raw.replace(b'"logical":', b'"unreviewed":false,"logical":', 1),
    lambda raw: raw.replace(b'"size_bytes":1', b'"size_bytes":true', 1),
    lambda raw: raw.replace(b'"publication":', b'"publication":null,"publication":', 1),
    lambda raw: raw.replace(b'"content_sha256":', b'"content_sha256":"' + b"a" * 64 + b'","content_sha256":', 1),
    lambda raw: raw.replace(b'"media_type":"application/json"', b'"media_type":"application/other"', 1),
    lambda raw: raw.replace(b'"relative_path":"outputs/member-0.json"', b'"relative_path":"outputs/other.json"', 1),
    lambda raw: raw.replace(b'"media_type":"application/json"', b'"media_type":"\xff"', 1),
), ids=("missing-newline", "extra-newline", "prefix-space", "binding-space", "wrong-version",
    "wrong-schema", "extra-field", "boolean-size", "duplicate-publication", "duplicate-logical-field",
    "changed-logical-metadata", "changed-materialization", "invalid-utf8"))
def test_known_publication_refuses_noncanonical_or_changed_metadata(change):
    original = _manifests()[0]
    raw = change(original.canonical_bytes())
    with pytest.raises(ValueError):
        decode_artifact_manifest(raw, publication=original.publication)
    with pytest.raises(ValueError):
        decode_artifact_manifest(raw)


def test_equal_but_distinct_binding_is_accepted_and_wrong_binding_refuses_without_fallback(monkeypatch):
    original = _manifests()[0]
    raw = original.canonical_bytes()
    equal = replace(original.publication)
    assert equal == original.publication and equal is not original.publication
    assert decode_artifact_manifest(raw, publication=equal).publication is equal
    wrong = replace(equal, commit_marker_sha256="f" * 64)
    monkeypatch.setattr(task_receipts, "_publication_binding", lambda _value: pytest.fail("wrong known binding fell back"))
    with pytest.raises(CanonicalizationError, match="differs from known binding"):
        decode_artifact_manifest(raw, publication=wrong)


@pytest.mark.parametrize("maximum", (0, -1, 1))
def test_whole_sidecar_size_bound_precedes_binding_access(monkeypatch, maximum):
    original = _manifests()[0]
    raw = original.canonical_bytes()
    monkeypatch.setattr(ArtifactPublicationBinding, "canonical_bytes",
        lambda _self: pytest.fail("oversized sidecar accessed publication encoding"))
    with pytest.raises(CanonicalizationError, match="exceeds its byte limit"):
        decode_artifact_manifest(raw, maximum_bytes=maximum, publication=original.publication)


@pytest.mark.parametrize("extra", (0, 1))
def test_whole_sidecar_limit_exact_boundary_and_one_byte_refusal(extra):
    original = _manifests()[0]
    raw = original.canonical_bytes()
    assert decode_artifact_manifest(raw, maximum_bytes=len(raw) + extra,
        publication=original.publication) == original
    with pytest.raises(CanonicalizationError, match="exceeds its byte limit"):
        decode_artifact_manifest(raw, maximum_bytes=len(raw) - 1, publication=original.publication)


@pytest.mark.parametrize("publication", (True, "binding", object()))
def test_known_binding_requires_exact_typed_record(publication):
    original = _manifests()[0]
    with pytest.raises(TypeError, match="typed publication"):
        decode_artifact_manifest(original.canonical_bytes(), publication=publication)
    with pytest.raises(TypeError, match="typed publication"):
        encode_artifact_manifest(original.logical, original.materialization, publication)


def test_encoder_retains_membership_and_logical_physical_identity_checks():
    original = _manifests()[0]
    changed = replace(original.materialization, relative_path="outputs/other.json")
    with pytest.raises(ValueError, match="does not include"):
        encode_artifact_manifest(original.logical, changed, original.publication)
    changed = replace(original.materialization, logical_artifact_id="exposed.other")
    with pytest.raises(ValueError, match="different logical/physical"):
        encode_artifact_manifest(original.logical, changed, original.publication)


def test_changed_binding_bytes_are_not_ignored_even_with_same_member_metadata():
    original = _manifests()[0]
    document = json.loads(original.canonical_bytes())
    document["value"]["publication"]["value"]["commit_marker_sha256"] = "f" * 64
    raw = (json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n").encode()
    assert decode_artifact_manifest(raw).publication.commit_marker_sha256 == "f" * 64
    with pytest.raises(CanonicalizationError, match="differs from known binding"):
        decode_artifact_manifest(raw, publication=original.publication)
