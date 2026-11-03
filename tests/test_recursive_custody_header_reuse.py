# SPDX-License-Identifier: MPL-2.0
"""Exact constructor-owned JSON header reuse with fresh actual byte custody."""

from dataclasses import replace
from types import SimpleNamespace

import pytest

from empirical_lawhood.infrastructure import recursive_custody as owner
from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict, ArtifactProfileValidatorRegistry
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from tests.test_recursive_custody_batched_members import _case


def test_json_getters_reuse_exact_header_proof_but_keep_current_publication_and_body_checks(tmp_path, monkeypatch):
    plane, _, members, directory = _case(tmp_path)
    payloads = owner.AuthenticatedRecursivePayloads(plane=plane, directory=directory, members=members)
    calls = []
    verify = plane.verify_manifest

    def actual(manifest):
        calls.append(manifest)
        return verify(manifest)

    monkeypatch.setattr(plane, "verify_manifest", actual)
    monkeypatch.setattr(owner, "json", SimpleNamespace(loads=lambda *_args:
        pytest.fail("an exact previously inspected JSON body was parsed before its typed consumer")))
    for _ in range(2):
        for member in members:
            raw = payloads[member.filename]
            assert decode_canonical_bytes(raw, ObjectIdentity, maximum_bytes=None).canonical_bytes() == raw
    assert len(calls) == 2 * len(members)
    with pytest.raises(TypeError):
        payloads._json_headers[members[0].filename] = (members[1].identity, members[1].size_bytes)
    path = directory / members[0].filename
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises((ArtifactIdentityConflict, ValueError, OSError)):
        payloads[members[0].filename]
    assert len(calls) == 2 * len(members) + 1


@pytest.mark.parametrize("changed", ("schema", "version"))
def test_header_proof_is_bound_to_exact_member_identity_not_only_unchanged_body_hash(tmp_path, monkeypatch, changed):
    plane, _, members, directory = _case(tmp_path, count=1)
    payloads = owner.AuthenticatedRecursivePayloads(plane=plane, directory=directory, members=members)
    member = members[0]
    identity = replace(member.identity, **({"object_schema": "empirical-lawhood/testing/other-schema"}
        if changed == "schema" else {"object_version": "9.0.0"}))
    payloads._members[member.filename] = replace(member, identity=identity)
    parsed = []
    loads = owner.json.loads

    def actual(raw):
        parsed.append(raw)
        return loads(raw)

    monkeypatch.setattr(owner, "json", SimpleNamespace(loads=actual))
    with pytest.raises(ValueError, match="schema or revision"):
        payloads[member.filename]
    assert len(parsed) == 1


def test_changing_current_registry_does_not_skip_fresh_custody_or_reparse_an_exact_json_header(tmp_path, monkeypatch):
    plane, _, members, directory = _case(tmp_path, count=1)
    payloads = owner.AuthenticatedRecursivePayloads(plane=plane, directory=directory, members=members)
    plane.validators = ArtifactProfileValidatorRegistry()
    calls = []
    verify = plane.verify_manifest

    def actual(manifest):
        calls.append(manifest)
        return verify(manifest)

    monkeypatch.setattr(plane, "verify_manifest", actual)
    monkeypatch.setattr(owner, "json", SimpleNamespace(loads=lambda *_args:
        pytest.fail("an exact header depended on the old registry object")))
    assert payloads[members[0].filename] == (directory / members[0].filename).read_bytes()
    assert len(calls) == 1


def test_constructor_binary_member_cannot_inherit_json_header_proof_after_codec_change(tmp_path, monkeypatch):
    from pathlib import Path
    from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
    from empirical_lawhood.runtime.recursive_handoff import RecursiveWaveMember
    from tests.test_matrix_array_worker_delivery import stock
    plane, _, manifest, _, raw, _ = stock(tmp_path)
    member = RecursiveWaveMember("selected.npz", ObjectIdentity("recursive-member.exposed-arrays", MATRIX_ARRAY_SCHEMA,
        "1.0.0", manifest.array_artifact.sha256), len(raw))
    payloads = owner.AuthenticatedRecursivePayloads(plane=plane,
        directory=Path(plane.root.contract.canonical_path) / "arrays", members=(member,))
    assert member.filename not in payloads._json_headers
    plane.validators = ArtifactProfileValidatorRegistry()
    # A current physical/codec guard may refuse first. Otherwise the original
    # JSON fallback must reject the actual NPZ; no constructor JSON proof exists.
    with pytest.raises((ArtifactIdentityConflict, ValueError, OSError)):
        payloads[member.filename]


def test_exposed_payload_read_computes_one_local_digest_for_both_expected_identities(tmp_path, monkeypatch):
    plane, manifests, members, directory = _case(tmp_path, count=1)
    calls = []
    digest = owner.sha256

    def actual(raw):
        calls.append(raw)
        return digest(raw)

    monkeypatch.setattr(owner, "sha256", actual)
    raw = owner.read_exposed_recursive_payload(plane, manifests[0], maximum_bytes=members[0].size_bytes)
    assert calls == [raw]
    assert raw == (directory / members[0].filename).read_bytes()
