# SPDX-License-Identifier: MPL-2.0
"""Read-only publication admission; disclosed bytes grant no scientific authority."""

from dataclasses import replace

import pytest

from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict
from tests.test_artifact_publication_admission import _census, _plane, _requests


def _snapshot(root):
    # Include directories and lock files omitted by the shared payload census.
    return _census(root), tuple(sorted(
        (str(path.relative_to(root)), path.is_dir(),
         path.read_bytes() if path.is_file() and path.name.endswith(".lock") else None)
        for path in root.rglob("*")))


def _forbid_effects(plane, monkeypatch):
    def refused(*arguments, **options):
        raise AssertionError("read-only admission reached publication, locking or cleanup")

    for name in ("_stage_publication", "_write_staged_bytes", "_write_publication_intent",
            "_publish_staged_batch", "_pair_lock", "_publication_batch_lock",
            "_remove_publication_intent", "_unlink_if_present"):
        monkeypatch.setattr(type(plane), name, refused)


def _interrupted(plane, request, monkeypatch, *, compact=False):
    """Retain the actual writer's durable intent, before any destination write."""
    captured = []
    publish = plane._publish_staged_batch
    write_intent = plane._write_publication_intent

    def capture(batch):
        captured.append((batch, batch.members[0].staged_sidecar_path.read_bytes()))
        return publish(batch)

    def interrupt(path, intent):
        write_intent(path, intent)
        raise KeyboardInterrupt("disclosed interruption after durable intent")

    with monkeypatch.context() as patch:
        patch.setattr(plane, "_publish_staged_batch", capture)
        patch.setattr(plane, "_write_publication_intent", interrupt)
        with pytest.raises(KeyboardInterrupt, match="durable intent"):
            plane.write_batch((request,), compact_manifests=compact)
    batch, sidecar = captured[0]
    assert batch.intent_path.is_file() and not batch.commit_path.exists()
    return batch, sidecar


@pytest.mark.parametrize("valid", (False, True))
def test_fresh_admission_validates_payload_without_creating_directories_or_files(tmp_path, monkeypatch, valid):
    root = tmp_path / "fresh-admission"
    plane = _plane(root)
    request, = _requests(1)
    if not valid:
        request = replace(request, payload=b"not canonical JSON")
    before = _snapshot(root)
    _forbid_effects(plane, monkeypatch)

    if valid:
        assert plane.preflight_write(request) is None
    else:
        with pytest.raises(ArtifactIdentityConflict):
            plane.preflight_write(request)

    assert _snapshot(root) == before


@pytest.mark.parametrize("compact", (False, True))
@pytest.mark.parametrize("damage", (None, "payload", "missing-sidecar"))
def test_committed_admission_authenticates_custody_without_effects(tmp_path, monkeypatch, damage, compact):
    root = tmp_path / "committed-admission"
    plane = _plane(root)
    request, = _requests(1)
    initial, = plane.write_batch((request,), compact_manifests=compact)
    if damage == "payload":
        plane.root.resolve(request.relative_path, for_write=False).write_bytes(b"foreign")
    elif damage == "missing-sidecar":
        plane.root.resolve(initial.manifest_materialization.relative_path, for_write=False).unlink()
    before = _snapshot(root)
    _forbid_effects(plane, monkeypatch)

    if damage is None:
        assert plane.preflight_write(request) is None
    else:
        with pytest.raises(ArtifactIdentityConflict):
            plane.preflight_write(request)

    assert _snapshot(root) == before


@pytest.mark.parametrize("compact", (False, True))
@pytest.mark.parametrize("partial", ("primary", "sidecar"))
def test_owned_prefix_admission_preserves_bytes_and_leaves_recovery_to_writer(tmp_path, monkeypatch, partial, compact):
    root = tmp_path / "owned-admission"
    plane = _plane(root)
    request, = _requests(1)
    batch, sidecar = _interrupted(plane, request, monkeypatch, compact=compact)
    member, = batch.members
    member.artifact_path.write_bytes(request.payload[:17] if partial == "primary" else request.payload)
    if partial == "sidecar":
        # A distinguishing prefix exercises the actual retained transport.
        member.sidecar_path.write_bytes(sidecar[:len(sidecar) // 2])
    before = _snapshot(root)

    with monkeypatch.context() as patch:
        _forbid_effects(plane, patch)
        assert plane.preflight_write(request) is None
        assert _snapshot(root) == before

    recovered = plane.write(request)
    assert recovered.created
    assert member.artifact_path.read_bytes() == request.payload
    manifest = plane.read_manifest(request.relative_path)
    assert (manifest.logical, manifest.materialization, manifest.publication) == (
        recovered.logical, recovered.materialization, batch.publication)
    if partial == "sidecar":
        assert member.sidecar_path.read_bytes() == sidecar
    assert batch.commit_path.read_bytes() == batch.commit_payload
    assert not batch.intent_path.exists()
    assert not tuple(root.rglob("*.partial"))


@pytest.mark.parametrize("damage", (
    "foreign-primary", "foreign-sidecar", "missing-intent", "changed-request", "exact-unowned-pair"))
def test_partial_admission_refuses_foreign_or_unowned_destinations_without_effects(tmp_path, monkeypatch, damage):
    root = tmp_path / "refused-admission"
    plane = _plane(root)
    request, = _requests(1)
    batch, sidecar = _interrupted(plane, request, monkeypatch)
    member, = batch.members
    member.artifact_path.write_bytes(request.payload[:17])
    if damage == "foreign-primary":
        member.artifact_path.write_bytes(b"foreign")
    elif damage == "foreign-sidecar":
        member.artifact_path.write_bytes(request.payload)
        member.sidecar_path.write_bytes(b"foreign")
    elif damage == "missing-intent":
        batch.intent_path.unlink()
    elif damage == "changed-request":
        request = replace(request, payload=request.payload.replace(b"a" * 64, b"b" * 64))
    else:
        member.artifact_path.write_bytes(request.payload)
        member.sidecar_path.write_bytes(sidecar)
        batch.intent_path.unlink()
    before = _snapshot(root)
    _forbid_effects(plane, monkeypatch)

    with pytest.raises(ArtifactIdentityConflict):
        plane.preflight_write(request)

    assert _snapshot(root) == before
    assert not batch.commit_path.exists()
