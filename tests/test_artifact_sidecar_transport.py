# SPDX-License-Identifier: MPL-2.0
"""Compact physical metadata controls; no payload or authority qualification."""

import json
import os
from dataclasses import replace
from hashlib import sha256

import pytest

from empirical_lawhood.infrastructure import artifact_sidecars as owner
from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict, ExternalArtifactPlane, GuardedExternalRoot
from empirical_lawhood.infrastructure.artifact_sidecars import (
    decode_artifact_sidecar, encode_artifact_manifest_reference, read_artifact_sidecar,
    resolve_artifact_manifest_reference,
)
from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import VisibilityCeiling
from empirical_lawhood.runtime.artifact_sidecar import ArtifactManifestReference
from empirical_lawhood.runtime.artifacts import (
    ArtifactCustodyLimits, ArtifactManifest, ArtifactPublicationCommit, ExternalRootContract,
    artifact_publication_commit_relative_path,
)
from tests.test_artifact_manifest_known_publication import _manifests


def _canonical(document):
    return (json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _case(tmp_path, *, limits=None, reference=None, legacy=False):
    original = _manifests()[0]
    reference = reference or ArtifactManifestReference.from_manifest(original)
    root = tmp_path / "custody"
    root.mkdir()
    mount = root.resolve()
    while not os.path.ismount(mount):
        mount = mount.parent
    plane = ExternalArtifactPlane(GuardedExternalRoot(ExternalRootContract(
        "exposed.storage", "Software compact sidecar custody", str(root.resolve()), str(mount),
        "empirical-lawhood/testing/compact-sidecar", 1)), custody_limits=limits)
    relative = original.materialization.relative_path + ".manifest.json"
    sidecar = plane.root.resolve(relative, for_write=True)
    sidecar.parent.mkdir(parents=True)
    sidecar.write_bytes(original.canonical_bytes() if legacy else reference.canonical_bytes())
    commit = ArtifactPublicationCommit(original.publication.publication_batch_id,
        original.publication.publication_scope, original.publication.members).canonical_bytes()
    marker = plane.root.resolve(original.publication.commit_marker_relative_path, for_write=True)
    marker.parent.mkdir(parents=True)
    marker.write_bytes(commit)
    return plane, original, reference, relative, sidecar, marker


@pytest.mark.parametrize("count", (1, 4, 64))
def test_reference_roundtrip_and_shared_binding_normalization_preserve_existing_records(count):
    for original in _manifests(count):
        reference = ArtifactManifestReference.from_manifest(original)
        raw = encode_artifact_manifest_reference(original.logical, original.materialization, original.publication)
        assert raw == reference.canonical_bytes()
        assert "members" not in reference.__dataclass_fields__
        assert decode_canonical_bytes(raw, ArtifactManifestReference, maximum_bytes=len(raw)) == reference
        assert decode_artifact_sidecar(raw) == reference
        decoded = decode_artifact_sidecar(raw, publication=original.publication)
        assert type(decoded) is ArtifactManifest
        assert decoded == original and decoded.publication is original.publication
        assert not hasattr(decoded, "_canonical_encoding")
        assert decoded.canonical_bytes() == original.canonical_bytes()
        assert decoded.canonical_bytes() != raw
        with pytest.raises(ValueError):
            decode_artifact_manifest(raw)


def test_legacy_bytes_and_pure_decode_remain_unchanged_without_io(monkeypatch):
    original = _manifests()[0]
    raw = original.canonical_bytes()
    compact = ArtifactManifestReference.from_manifest(original).canonical_bytes()
    monkeypatch.setattr(owner, "read_bounded_bytes", lambda *_args, **_kw: pytest.fail("pure decode performed I/O"))
    assert decode_artifact_sidecar(raw) == original
    assert decode_artifact_sidecar(raw, publication=original.publication).publication is original.publication
    assert decode_artifact_sidecar(compact, publication=original.publication) == original
    wrong = replace(original.publication, commit_marker_sha256="f" * 64)
    for value in (raw, compact):
        with pytest.raises(ValueError):
            decode_artifact_sidecar(value, publication=wrong)


@pytest.mark.parametrize("value", (None, True, "{}", bytearray(b"{}"), memoryview(b"{}")))
def test_pure_decoder_requires_immutable_bytes(value):
    with pytest.raises(ValueError, match="immutable bytes"):
        decode_artifact_sidecar(value)


@pytest.mark.parametrize("count", (4, 64))
def test_physical_reference_metadata_excludes_the_shared_roster(count, record_property):
    manifests = _manifests(count)
    references = tuple(ArtifactManifestReference.from_manifest(row).canonical_bytes() for row in manifests)
    publication = manifests[0].publication
    commit = ArtifactPublicationCommit(publication.publication_batch_id,
        publication.publication_scope, publication.members).canonical_bytes()
    legacy_size = sum(len(row.canonical_bytes()) for row in manifests)
    compact_size = len(commit) + sum(map(len, references))
    # Only the one existing commit carries a roster. Per-member sidecars stay
    # within a few bytes as the roster and decimal size-pin token grow.
    small = ArtifactManifestReference.from_manifest(_manifests(1)[0]).canonical_bytes()
    assert all(b'"members":' not in raw for raw in references)
    assert all(abs(len(raw) - len(small)) <= 8 for raw in references)
    assert compact_size < legacy_size
    record_property("publication_members", count)
    record_property("legacy_sidecar_bytes", legacy_size)
    record_property("compact_sidecars_plus_existing_commit_bytes", compact_size)


@pytest.mark.parametrize("change", (
    {"logical": None}, {"materialization": None}, {"publication_scope": None},
    {"commit_marker_size_bytes": True}, {"commit_marker_size_bytes": 0},
    {"commit_marker_size_bytes": -1}, {"commit_marker_sha256": "A" * 64},
    {"commit_marker_relative_path": "../outside.json"},
    {"publication_batch_id": "UPPERCASE"},
))
def test_reference_refuses_bad_types_hashes_sizes_and_derived_paths(change):
    reference = ArtifactManifestReference.from_manifest(_manifests()[0])
    with pytest.raises((TypeError, ValueError)):
        replace(reference, **change)


def test_reference_scope_and_membership_are_preserved():
    original = _manifests()[0]
    reference = ArtifactManifestReference.from_manifest(original)
    for physical in (replace(original.materialization, storage_root_id="exposed.other"),
                     replace(original.materialization, relative_path="other/member.json")):
        with pytest.raises(ValueError, match="scope"):
            replace(reference, materialization=physical)
    with pytest.raises(ValueError, match="scope"):
        replace(reference, logical=replace(original.logical, visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY))
    changed = replace(reference, materialization=replace(original.materialization, size_bytes=100))
    with pytest.raises(ValueError, match="does not include"):
        changed.resolve(original.publication)
    with pytest.raises(TypeError):
        reference.resolve(True)


@pytest.mark.parametrize("field", (
    "publication_batch_id", "publication_scope", "commit_marker_relative_path",
    "commit_marker_sha256", "commit_marker_size_bytes",
))
def test_pure_resolution_requires_every_publication_pin(field):
    original = _manifests()[0]
    reference = ArtifactManifestReference.from_manifest(original)
    if field == "publication_batch_id":
        batch = "exposed.other-batch"
        changes = {field: batch, "commit_marker_relative_path":
            artifact_publication_commit_relative_path(reference.publication_scope, batch)}
    elif field == "publication_scope":
        scope = replace(reference.publication_scope, publication_scope_id="exposed.other-scope")
        changes = {field: scope, "commit_marker_relative_path":
            artifact_publication_commit_relative_path(scope, reference.publication_batch_id)}
    elif field == "commit_marker_relative_path":
        # A foreign path is rejected even before any binding can be supplied.
        with pytest.raises(ValueError, match="batch-derived"):
            replace(reference, commit_marker_relative_path="outputs/other.json")
        return
    elif field == "commit_marker_sha256":
        changes = {field: "f" * 64}
    else:
        changes = {field: reference.commit_marker_size_bytes + 1}
    with pytest.raises(ValueError, match="exact publication binding"):
        replace(reference, **changes).resolve(original.publication)


@pytest.mark.parametrize("mutation", ("duplicate", "extra", "version", "schema", "float", "space", "newline"))
def test_physical_reference_shape_and_canonical_bytes_are_closed(mutation):
    raw = ArtifactManifestReference.from_manifest(_manifests()[0]).canonical_bytes()
    document = json.loads(raw)
    if mutation == "duplicate":
        raw = raw.replace(b'"publication_batch_id":', b'"publication_batch_id":"other","publication_batch_id":')
    elif mutation == "extra":
        document["value"]["unreviewed"] = True
        raw = _canonical(document)
    elif mutation == "version":
        document["version"] = "9.0.0"
        raw = _canonical(document)
    elif mutation == "schema":
        document["schema"] = "empirical-lawhood/testing/unknown-sidecar"
        raw = _canonical(document)
    elif mutation == "float":
        document["value"]["commit_marker_size_bytes"] = 1.5
        raw = _canonical(document)
    elif mutation == "space":
        raw = b" " + raw
    else:
        raw += b"\n"
    with pytest.raises(ValueError):
        decode_artifact_sidecar(raw)


@pytest.mark.parametrize("known", (False, True))
def test_decode_checks_whole_frame_bound_and_exact_boundary(known):
    original = _manifests()[0]
    raw = ArtifactManifestReference.from_manifest(original).canonical_bytes()
    kwargs = {"publication": original.publication} if known else {}
    assert decode_artifact_sidecar(raw, maximum_bytes=len(raw), **kwargs) is not None
    with pytest.raises(ValueError, match="byte limit"):
        decode_artifact_sidecar(raw, maximum_bytes=len(raw) - 1, **kwargs)


def test_guarded_compact_read_authenticates_only_sidecar_and_exact_commit_without_payloads(tmp_path, monkeypatch):
    plane, original, reference, relative, sidecar, marker = _case(tmp_path)
    reads = []
    read = owner.read_bounded_bytes

    def observed(path, **kwargs):
        reads.append((path, kwargs["maximum_bytes"]))
        return read(path, **kwargs)

    monkeypatch.setattr(owner, "read_bounded_bytes", observed)
    decoded = read_artifact_sidecar(plane, relative)
    assert type(decoded) is ArtifactManifest and decoded == original
    assert reads == [(sidecar, None), (marker, reference.commit_marker_size_bytes)]
    assert all(not plane.root.resolve(member.relative_path, for_write=False).exists()
        for member in original.publication.members)
    assert not hasattr(decoded, "_canonical_encoding")


def test_guarded_legacy_read_does_not_silently_add_commit_or_payload_io(tmp_path, monkeypatch):
    plane, original, _reference, relative, sidecar, marker = _case(tmp_path, legacy=True)
    marker.unlink()
    reads = []
    read = owner.read_bounded_bytes
    monkeypatch.setattr(owner, "read_bounded_bytes", lambda path, **kwargs:
        (reads.append(path), read(path, **kwargs))[1])
    assert read_artifact_sidecar(plane, relative) == original
    assert reads == [sidecar]


@pytest.mark.parametrize("change", ("missing", "truncated", "extended", "wrong-digest", "noncanonical", "different-batch", "nonmember"))
def test_actual_commit_bytes_and_complete_join_are_required_before_return(tmp_path, change):
    plane, original, reference, relative, sidecar, marker = _case(tmp_path)
    raw = marker.read_bytes()
    if change == "missing":
        marker.unlink()
    elif change == "truncated":
        marker.write_bytes(raw[:-1])
    elif change == "extended":
        marker.write_bytes(raw + b"\n")
    elif change == "wrong-digest":
        marker.write_bytes(raw.replace(b"schema", b"schemb", 1))
    elif change == "noncanonical":
        raw = (json.dumps(json.loads(raw), indent=2) + "\n").encode()
        marker.write_bytes(raw)
        sidecar.write_bytes(replace(reference, commit_marker_sha256=sha256(raw).hexdigest(),
            commit_marker_size_bytes=len(raw)).canonical_bytes())
    elif change == "different-batch":
        other = _manifests(3)[0].publication
        raw = ArtifactPublicationCommit(other.publication_batch_id, other.publication_scope, other.members).canonical_bytes()
        marker.write_bytes(raw)
        sidecar.write_bytes(replace(reference, commit_marker_sha256=sha256(raw).hexdigest(),
            commit_marker_size_bytes=len(raw)).canonical_bytes())
    else:
        sidecar.write_bytes(replace(reference,
            materialization=replace(original.materialization, size_bytes=100)).canonical_bytes())
    with pytest.raises(ArtifactIdentityConflict):
        read_artifact_sidecar(plane, relative)


@pytest.mark.parametrize("mutation", ("omitted-member", "foreign-root", "foreign-path", "foreign-scope", "duplicate-member"))
def test_actual_commit_full_roster_and_scope_are_checked_even_after_repinning(tmp_path, mutation):
    plane, _original, reference, relative, sidecar, marker = _case(tmp_path)
    document = json.loads(marker.read_bytes())
    value = document["value"]
    if mutation == "omitted-member":
        value["members"].pop()
    elif mutation == "foreign-root":
        value["members"][-1]["value"]["storage_root_id"] = "exposed.other"
    elif mutation == "foreign-path":
        value["members"][-1]["value"]["relative_path"] = "outside/member.json"
    elif mutation == "foreign-scope":
        value["publication_scope"]["value"]["publication_scope_id"] = "exposed.other"
    else:
        value["members"].append(value["members"][-1])
    raw = _canonical(document)
    marker.write_bytes(raw)
    sidecar.write_bytes(replace(reference, commit_marker_sha256=sha256(raw).hexdigest(),
        commit_marker_size_bytes=len(raw)).canonical_bytes())
    with pytest.raises(ArtifactIdentityConflict):
        read_artifact_sidecar(plane, relative)


@pytest.mark.parametrize("mutation", ("sidecar", "commit"))
def test_a_prior_success_never_hides_changed_transport_bytes(tmp_path, monkeypatch, mutation):
    plane, original, _reference, relative, sidecar, marker = _case(tmp_path)
    assert read_artifact_sidecar(plane, relative) == original
    changed = sidecar if mutation == "sidecar" else marker
    changed.write_bytes(changed.read_bytes().replace(b"exposed.member.0", b"exposed.member.x"))
    reads = []
    read = owner.read_bounded_bytes
    monkeypatch.setattr(owner, "read_bounded_bytes", lambda path, **kwargs:
        (reads.append(path), read(path, **kwargs))[1])
    with pytest.raises(ArtifactIdentityConflict):
        read_artifact_sidecar(plane, relative)
    assert reads == [sidecar, marker]


def test_selected_commit_bound_refuses_before_marker_open(tmp_path, monkeypatch):
    plane, _original, reference, relative, sidecar, _marker = _case(tmp_path)
    plane.custody_limits = ArtifactCustodyLimits(publication_marker_bytes=reference.commit_marker_size_bytes - 1)
    reads = []
    read = owner.read_bounded_bytes
    monkeypatch.setattr(owner, "read_bounded_bytes", lambda path, **kwargs:
        (reads.append(path), read(path, **kwargs))[1])
    with pytest.raises(ArtifactIdentityConflict, match="selected byte bound"):
        read_artifact_sidecar(plane, relative)
    assert reads == [sidecar]


def test_selected_sidecar_and_member_bounds_are_enforced(tmp_path, monkeypatch):
    plane, _original, _reference, relative, sidecar, _marker = _case(tmp_path)
    with pytest.raises(ArtifactIdentityConflict):
        read_artifact_sidecar(plane, relative, maximum_bytes=sidecar.stat().st_size - 1)
    plane.custody_limits = ArtifactCustodyLimits(manifest_bytes=sidecar.stat().st_size - 1)
    with pytest.raises(ArtifactIdentityConflict):
        read_artifact_sidecar(plane, relative)
    plane.custody_limits = ArtifactCustodyLimits(publication_members=3)
    with pytest.raises(ArtifactIdentityConflict, match="member bound"):
        read_artifact_sidecar(plane, relative)


def test_sidecar_alias_and_another_storage_root_refuse_before_commit_read(tmp_path, monkeypatch):
    plane, _original, reference, _relative, sidecar, _marker = _case(tmp_path)
    alias = "outputs/alias.json.manifest.json"
    plane.root.resolve(alias, for_write=True).write_bytes(sidecar.read_bytes())
    reads = []
    read = owner.read_bounded_bytes
    monkeypatch.setattr(owner, "read_bounded_bytes", lambda path, **kwargs:
        (reads.append(path), read(path, **kwargs))[1])
    with pytest.raises(ArtifactIdentityConflict, match="actual member path"):
        read_artifact_sidecar(plane, alias)
    assert len(reads) == 1
    other = ExternalArtifactPlane(GuardedExternalRoot(replace(plane.root.contract, storage_root_id="exposed.other")))
    with pytest.raises(ArtifactIdentityConflict, match="another guarded storage root"):
        resolve_artifact_manifest_reference(other, reference)
    assert len(reads) == 1
