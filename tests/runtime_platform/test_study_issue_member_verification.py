# SPDX-License-Identifier: MPL-2.0
"""Same-invocation issue member joins retain complete custody and mutation guards.

The issued design and authority scaffolding are disclosed software fixtures;
these checks do not provide scientific qualification or execution authority.
"""

from collections import Counter
from hashlib import sha256
from types import MappingProxyType

import pytest

from empirical_lawhood.infrastructure import study_issue as owner
from empirical_lawhood.infrastructure import artifacts as artifact_owner
from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict
from empirical_lawhood.infrastructure.bounded_io import BoundedFileIOError
from tests.runtime_platform.test_study_issue import _issue_api_fixture, _issue_request


@pytest.fixture(scope="module")
def issued(tmp_path_factory):
    directory = tmp_path_factory.mktemp("member-verification")
    api, paths, external, _ = _issue_api_fixture(directory)
    result = api.issue_study(_issue_request(paths, confirmed=True))
    assert result.succeeded, (result.reason_codes, result.errors)
    assert result.payload is not None and result.payload.publication_receipt is not None
    return api._study_issue_publisher, result.payload.manifest, result.payload.publication_receipt, external


def _files(directory):
    return {path.relative_to(directory).as_posix(): sha256(path.read_bytes()).hexdigest()
        for path in directory.rglob("*") if path.is_file()}


def test_scoped_member_joins_match_fresh_reads_without_a_second_decode_pass(issued, monkeypatch):
    publisher, manifest, receipt, external = issued
    before = _files(external)
    original_decoder = owner.decode_artifact_manifest
    original_custody_decoder = artifact_owner.decode_artifact_sidecar
    original_read = publisher.artifact_plane.read_manifest
    source_decodes = []
    custody_decodes = []
    source_reads = []

    def source_decode(raw, **kwargs):
        value = original_decoder(raw, **kwargs)
        source_decodes.append(value.logical.logical_artifact_id)
        return value

    def custody_decode(raw, **kwargs):
        value = original_custody_decoder(raw, **kwargs)
        custody_decodes.append(value.logical.logical_artifact_id)
        return value

    def read(relative, *, maximum_bytes=None):
        source_reads.append((relative, maximum_bytes))
        return original_read(relative, maximum_bytes=maximum_bytes)

    monkeypatch.setattr(owner, "decode_artifact_manifest", source_decode)
    monkeypatch.setattr(artifact_owner, "decode_artifact_sidecar", custody_decode)
    monkeypatch.setattr(publisher.artifact_plane, "read_manifest", read)
    publisher._validate_manifest_members(manifest, publication=receipt.publication)
    # Independent joins now ask the custody owner to normalize each compact
    # sidecar. The issue consumer retains its own bound and does no decoding.
    assert source_decodes == []
    assert Counter(source_reads) == Counter((row.relative_path, owner.MAX_PROGRAMME_AUTHORITY_BYTES)
        for row in manifest.members)
    source_reads.clear()
    original_join = publisher._validate_manifest_members
    joined = []

    def join(selected, *, publication, sidecars=None):
        assert sidecars is not None
        assert set(sidecars) == {row.relative_path for row in publication.members}
        # The selected binding survives custody verification. All members
        # reuse that same authenticated roster, avoiding repeated deep joins.
        assert all(value.publication is publication for value in sidecars.values())
        with pytest.raises(TypeError):
            sidecars["foreign"] = next(iter(sidecars.values()))
        joined.append(len(sidecars))
        return original_join(selected, publication=publication, sidecars=sidecars)

    monkeypatch.setattr(publisher, "_validate_manifest_members", join)
    scoped = publisher.load_study(manifest.issue_id)
    assert joined == [len(receipt.publication.members)]
    # The initial manifest has one metadata read; member sidecars are decoded
    # once in the complete custody callback. Only the receipt stays legacy.
    assert source_reads == [(f"issued-programmes/{manifest.issue_id}/manifest.json",
        owner.MAX_PROGRAMME_AUTHORITY_BYTES)]
    assert source_decodes == [receipt.receipt_id]
    decoded_counts = Counter(custody_decodes)
    assert all(decoded_counts[row.member_id] == 1 for row in manifest.members)

    class PlainPlane:
        root = publisher.artifact_plane.root
        verify_manifest = publisher.artifact_plane.verify_manifest
        read_manifest = staticmethod(publisher.artifact_plane.read_manifest)

    plain = owner.ExternalIssuedStudyPublisher(artifact_plane=PlainPlane(),
        authority_store=publisher.authority_store, grantee_id=publisher.grantee_id)
    ordinary = plain.load_study(manifest.issue_id)
    assert ordinary == scoped
    assert ordinary.manifest.canonical_bytes() == manifest.canonical_bytes()
    assert ordinary.publication_receipt.canonical_bytes() == receipt.canonical_bytes()
    assert _files(external) == before


@pytest.mark.parametrize("damage", ("corrupt-payload", "missing-sidecar", "foreign-sidecar"))
def test_complete_custody_refuses_damaged_siblings_before_the_scientific_join(issued, monkeypatch, damage):
    publisher, manifest, _, external = issued
    victim, other = manifest.members[:2]
    target = external / (victim.relative_path + (".manifest.json" if damage != "corrupt-payload" else ""))
    original = target.read_bytes()
    entered = []

    def forbidden_join(*args, **kwargs):
        entered.append(True)
        raise AssertionError("scientific join preceded complete custody")

    monkeypatch.setattr(publisher, "_validate_manifest_members", forbidden_join)
    try:
        if damage == "missing-sidecar":
            target.unlink()
        elif damage == "foreign-sidecar":
            target.write_bytes((external / (other.relative_path + ".manifest.json")).read_bytes())
        else:
            target.write_bytes(original + b" ")
        with pytest.raises(ArtifactIdentityConflict):
            publisher.load_study(manifest.issue_id)
        assert entered == []
    finally:
        target.write_bytes(original)


@pytest.mark.parametrize("damage", ("omitted", "foreign"))
def test_member_join_refuses_missing_or_foreign_callback_entries(issued, monkeypatch, damage):
    publisher, manifest, _, _ = issued
    victim, other = manifest.members[:2]
    original_join = publisher._validate_manifest_members

    def join(selected, *, publication, sidecars=None):
        assert sidecars is not None
        altered = dict(sidecars)
        if damage == "omitted":
            del altered[victim.relative_path]
        else:
            altered[victim.relative_path] = altered[other.relative_path]
        return original_join(selected, publication=publication, sidecars=MappingProxyType(altered))

    monkeypatch.setattr(publisher, "_validate_manifest_members", join)
    with pytest.raises(RuntimeError, match="member sidecar differs"):
        publisher.load_study(manifest.issue_id)


@pytest.mark.parametrize("target_kind,refuse", (("payload", False), ("marker", False), ("sidecar", True)))
def test_callback_mutation_is_refused_after_success_or_scientific_failure(issued, monkeypatch, target_kind, refuse):
    publisher, manifest, receipt, external = issued
    victim = manifest.members[0]
    relative = receipt.publication.commit_marker_relative_path if target_kind == "marker" else victim.relative_path
    if target_kind == "sidecar":
        relative += ".manifest.json"
    target = external / relative
    original = target.read_bytes()
    original_join = publisher._validate_manifest_members
    entered = []

    def join(selected, *, publication, sidecars=None):
        original_join(selected, publication=publication, sidecars=sidecars)
        entered.append(True)
        target.write_bytes(original + b" ")
        if refuse:
            raise ValueError("scientific join deliberately refused")

    monkeypatch.setattr(publisher, "_validate_manifest_members", join)
    try:
        with pytest.raises(ArtifactIdentityConflict, match="changed"):
            publisher.load_study(manifest.issue_id)
        assert entered == [True]
    finally:
        target.write_bytes(original)


def test_scoped_public_load_keeps_guards_until_the_outer_verification_scope_ends(issued):
    publisher, manifest, _, external = issued
    victim = external / manifest.members[0].relative_path
    original = victim.read_bytes()
    returned = []
    try:
        with pytest.raises(ArtifactIdentityConflict, match="changed"):
            with publisher.artifact_plane.verification_scope() as scoped:
                scoped_publisher = owner.ExternalIssuedStudyPublisher(artifact_plane=scoped,
                    authority_store=publisher.authority_store, grantee_id=publisher.grantee_id)
                returned.append(scoped_publisher.load_study(manifest.issue_id))
                victim.write_bytes(original + b" ")
        assert len(returned) == 1 and returned[0].manifest == manifest
    finally:
        victim.write_bytes(original)


def test_present_noncallable_member_hook_refuses_instead_of_falling_back(issued, monkeypatch):
    publisher, manifest, _, _ = issued
    monkeypatch.setattr(publisher.artifact_plane, "verify_manifest_members", None)
    with pytest.raises(TypeError, match="must be callable"):
        publisher.load_study(manifest.issue_id)


def test_member_callback_retains_its_consumer_byte_bound_when_the_plane_allows_more(issued, monkeypatch):
    publisher, manifest, receipt, external = issued
    sidecar = publisher.artifact_plane.read_manifest(f"issued-programmes/{manifest.issue_id}/manifest.json")
    monkeypatch.setattr(owner, "MAX_PROGRAMME_AUTHORITY_BYTES", 1)
    with pytest.raises(ArtifactIdentityConflict) as refused:
        publisher._validate_manifest_members(manifest, publication=receipt.publication)
    assert isinstance(refused.value.__cause__, BoundedFileIOError)
    assert "exceeds its byte limit" in str(refused.value.__cause__)
    entered = []

    def join(sidecars):
        entered.append(True)
        publisher._validate_manifest_members(manifest, publication=receipt.publication, sidecars=sidecars)

    with pytest.raises(BoundedFileIOError, match="exceeds its byte limit"):
        publisher.artifact_plane.verify_manifest_members(sidecar, validate_members=join)
    assert entered == [True]
