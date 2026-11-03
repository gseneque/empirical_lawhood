# SPDX-License-Identifier: MPL-2.0
"""Physical metadata controls, with real storage guards and no scientific entry."""

from dataclasses import replace
from hashlib import sha256
from pathlib import Path

import pytest

from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict, ExternalArtifactPlane, GuardedExternalRoot
from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import (
    ArtifactProfile, ArtifactPublicationIntent, ArtifactWriteRequest, ExternalRootContract,
    artifact_publication_intent_relative_path,
)


def _case(directory, *, compact=True, count=4):
    directory.mkdir()
    mount = next(parent for parent in directory.parents if parent.is_mount())
    plane = ExternalArtifactPlane(GuardedExternalRoot(ExternalRootContract(
        "software.compact-publication", "Exposed metadata custody", str(directory), str(mount),
        "empirical-lawhood/testing/compact-publication", 1)))
    requests = tuple(ArtifactWriteRequest(
        f"software.member.{number}", f"members/{number}.json", ObjectIdentity.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, "application/json", "software.members", "members",
        ObjectIdentity(f"software.subject.{number}", ObjectIdentity.SCHEMA, "1.0.0", "a" * 64).canonical_bytes(),
        VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND,
    ) for number in range(count))
    results = (plane.write_compact_batch if compact else plane.write_batch)(requests)
    manifests = tuple(plane.read_manifest(row.relative_path) for row in requests)
    return plane, requests, results, manifests


def _path(plane, relative):
    return plane.root.resolve(relative, for_write=False)


def _census(plane):
    root = Path(plane.root.contract.canonical_path)
    return {path.relative_to(root).as_posix(): (path.stat().st_size,
        sha256(path.read_bytes()).hexdigest(), path.stat().st_mtime_ns)
        for path in root.rglob("*") if path.is_file()}


def test_compact_transport_preserves_payloads_logical_identity_commit_and_normalized_canonical_bytes(tmp_path):
    legacy, requests, original, left = _case(tmp_path / "legacy", compact=False)
    compact, _, current, right = _case(tmp_path / "compact")
    assert left == right
    assert all(a.canonical_bytes() == b.canonical_bytes() for a, b in zip(left, right, strict=True))
    publication = left[0].publication
    assert _path(legacy, publication.commit_marker_relative_path).read_bytes() == _path(
        compact, publication.commit_marker_relative_path).read_bytes()
    for request, old, new in zip(requests, original, current, strict=True):
        assert old.logical == new.logical and old.materialization == new.materialization
        assert _path(compact, request.relative_path).read_bytes() == request.payload
        raw = _path(compact, new.manifest_materialization.relative_path).read_bytes()
        assert len(raw) == new.manifest_materialization.size_bytes
        assert sha256(raw).hexdigest() == new.manifest_materialization.physical_sha256
        with pytest.raises(ValueError):
            decode_artifact_manifest(raw)
    with compact.verification_scope() as scoped:
        members = tuple(scoped.read_manifest(row.relative_path) for row in requests)
        assert len({id(row.publication) for row in members}) == 1
        scoped.verify_manifests(members)


@pytest.mark.parametrize("original_compact", (False, True))
def test_replay_preserves_existing_sidecar_representation_without_staging(tmp_path, monkeypatch, original_compact):
    plane, requests, original, _ = _case(tmp_path / "custody", compact=original_compact)
    before = _census(plane)
    monkeypatch.setattr(plane, "_stage_publication", lambda *_args, **_kwargs: pytest.fail("committed replay staged bytes"))
    repeated = (plane.write_batch if original_compact else plane.write_compact_batch)(requests)
    assert all(not row.created for row in repeated)
    assert tuple(row.manifest_materialization for row in repeated) == tuple(row.manifest_materialization for row in original)
    assert _census(plane) == before


@pytest.mark.parametrize("committed", (False, True))
def test_undeclared_stream_replay_keeps_compact_custody_and_compares_actual_chunks(tmp_path, committed):
    plane, requests, _, manifests = _case(tmp_path / "custody")
    if not committed:
        _path(plane, manifests[0].publication.commit_marker_relative_path).unlink()
    before = {row.relative_path: _path(plane, row.relative_path + ".manifest.json").read_bytes()
        for row in requests}
    streams = tuple(replace(row.as_stream(), expected_size_bytes=None, expected_physical_sha256=None)
        for row in requests)
    plane.write_compact_batch(streams)
    assert all(_path(plane, relative + ".manifest.json").read_bytes() == raw for relative, raw in before.items())
    invalid = replace(requests[0].as_stream(), expected_size_bytes=None,
        expected_physical_sha256=None, chunks=iter((b"changed actual request",)))
    with pytest.raises(ArtifactIdentityConflict):
        plane.write_compact_batch((invalid, *(row.as_stream() for row in requests[1:])))


@pytest.mark.parametrize("original_compact", (False, True))
def test_interrupted_owned_partial_keeps_existing_complete_pair_and_restores_exact_prefix(tmp_path, original_compact):
    plane, requests, results, manifests = _case(tmp_path / "custody", compact=original_compact)
    publication = manifests[0].publication
    commit = _path(plane, publication.commit_marker_relative_path)
    commit.unlink()
    retained = {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in (
        _path(plane, requests[0].relative_path), _path(plane, results[0].manifest_materialization.relative_path))}
    partial_payload = _path(plane, requests[1].relative_path)
    partial_sidecar = _path(plane, results[1].manifest_materialization.relative_path)
    prefix = partial_sidecar.read_bytes()[:96]
    partial_payload.write_bytes(requests[1].payload[:24])
    partial_sidecar.write_bytes(prefix)
    for request, result in zip(requests[2:], results[2:], strict=True):
        _path(plane, request.relative_path).unlink()
        _path(plane, result.manifest_materialization.relative_path).unlink()
    absent = tuple(sorted(path for request in requests for path in (
        request.relative_path, request.relative_path + ".manifest.json")))
    intent = ArtifactPublicationIntent(publication.publication_batch_id,
        publication.publication_scope, publication.members, absent)
    intent_path = plane.root.resolve(artifact_publication_intent_relative_path(
        publication.publication_scope, publication.publication_batch_id), for_write=True)
    plane._write_publication_intent(intent_path, intent)
    (plane.write_batch if original_compact else plane.write_compact_batch)(requests)
    assert not intent_path.exists()
    assert partial_sidecar.read_bytes().startswith(prefix)
    assert partial_payload.read_bytes() == requests[1].payload
    assert all((path.read_bytes(), path.stat().st_mtime_ns) == value for path, value in retained.items())
    with plane.verification_scope() as scoped:
        reconstructed = tuple(scoped.read_manifest(row.relative_path) for row in requests)
        assert reconstructed == manifests
        scoped.verify_manifests(reconstructed)


@pytest.mark.parametrize("damage", ("payload", "sidecar", "commit"))
def test_compact_batch_damage_refuses_before_consumer_callback(tmp_path, damage):
    plane, requests, _, manifests = _case(tmp_path / "custody")
    target = (manifests[0].publication.commit_marker_relative_path if damage == "commit" else
        requests[1].relative_path + (".manifest.json" if damage == "sidecar" else ""))
    path = _path(plane, target)
    path.write_bytes(path.read_bytes() + b" ")
    calls = []
    with pytest.raises((ArtifactIdentityConflict, ValueError)):
        plane.verify_manifest_members(manifests[0], validate_members=lambda rows: calls.append(rows))
    assert calls == []


def test_cached_metadata_keeps_stricter_read_limit_and_refuses_after_scope_exit(tmp_path):
    plane, requests, _, _ = _case(tmp_path / "custody")
    size = _path(plane, requests[1].relative_path + ".manifest.json").stat().st_size
    with plane.verification_scope() as scoped:
        scoped.read_manifest(requests[0].relative_path)
        with pytest.raises((ArtifactIdentityConflict, ValueError)):
            scoped.read_manifest(requests[1].relative_path, maximum_bytes=size - 1)
    with pytest.raises(ArtifactIdentityConflict, match="ended"):
        scoped.read_manifest(requests[0].relative_path)


@pytest.mark.parametrize("target", ("earlier-sidecar", "marker"))
def test_scoped_metadata_mutation_refuses_before_successful_exit(tmp_path, target):
    plane, requests, _, manifests = _case(tmp_path / "custody")
    relative = (requests[0].relative_path + ".manifest.json" if target == "earlier-sidecar"
        else manifests[0].publication.commit_marker_relative_path)
    with pytest.raises(ArtifactIdentityConflict):
        with plane.verification_scope() as scoped:
            scoped.read_manifest(requests[0].relative_path)
            path = _path(plane, relative)
            path.write_bytes(path.read_bytes() + b" ")
            scoped.read_manifest(requests[1].relative_path)
