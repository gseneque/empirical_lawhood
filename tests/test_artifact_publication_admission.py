# SPDX-License-Identifier: MPL-2.0
"""Disposable publication controls; no native work or scientific authority."""

from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import json
import os
import resource
import threading

import pytest

from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict, ExternalArtifactPlane, ExternalRootUnavailable, GuardedExternalRoot
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest, ExternalRootContract


def _plane(directory):
    directory.mkdir(parents=True)
    mount = next(parent for parent in directory.parents if parent.is_mount())
    return ExternalArtifactPlane(GuardedExternalRoot(ExternalRootContract(
        "software.publication.root", "disposable publication unit controls", str(directory), str(mount),
        "empirical-lawhood/tests/publication-storage", 1,
    )))


def _requests(count):
    return tuple(ArtifactWriteRequest(
        logical_artifact_id=f"software.publication-{index:04d}",
        relative_path=f"software/publication/member-{index:04d}.json",
        payload_schema=ObjectIdentity.SCHEMA,
        profile=ArtifactProfile.CANONICAL_JSON,
        media_type="application/json",
        publication_scope_id="software.publication-admission",
        publication_scope_relative_root="software/publication",
        payload=ObjectIdentity(f"software.member-{index:04d}", ObjectIdentity.SCHEMA, "1.0.0", "a" * 64).canonical_bytes(),
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY,
        parent_visibility_ceilings=(),
        outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
    ) for index in range(count))


def _census(root):
    import hashlib

    return {str(path.relative_to(root)): (path.stat().st_size, hashlib.sha256(path.read_bytes()).hexdigest())
            for path in root.rglob("*") if path.is_file() and not path.name.endswith(".lock")}


def _no_staging(*arguments, **options):
    raise AssertionError("committed publication reached payload/control staging")


@contextmanager
def _descriptor_limit(soft):
    previous = resource.getrlimit(resource.RLIMIT_NOFILE)
    assert previous[1] == resource.RLIM_INFINITY or previous[1] >= soft
    resource.setrlimit(resource.RLIMIT_NOFILE, (soft, previous[1]))
    try:
        yield
    finally:
        resource.setrlimit(resource.RLIMIT_NOFILE, previous)


def test_rlimit64_refuses_80_members_before_any_payload_staging(tmp_path, monkeypatch):
    plane = _plane(tmp_path / "descriptor-capacity")
    staged = []
    original = plane._stage_publication

    def count_staging(*arguments, **options):
        staged.append(None)
        return original(*arguments, **options)

    monkeypatch.setattr(plane, "_stage_publication", count_staging)
    try:
        with _descriptor_limit(64), pytest.raises(ExternalRootUnavailable, match="descriptor capacity"):
            plane.write_batch(_requests(80))
    finally:
        print(json.dumps({"rlimit_nofile": 64, "requested_members": 80, "payload_staging_calls": len(staged)}))
    assert not staged
    assert not tuple((tmp_path / "descriptor-capacity").rglob("*.partial"))
    assert not tuple((tmp_path / "descriptor-capacity").rglob("*.json"))


@pytest.mark.parametrize("count", (2, 257))
def test_exact_committed_replay_has_no_payload_or_control_staging(tmp_path, monkeypatch, count):
    plane = _plane(tmp_path / "exact-replay")
    requests = _requests(count)
    initial = plane.write_batch(requests)
    assert len(initial) == count and all(item.created for item in initial)
    before = _census(tmp_path / "exact-replay")
    staged = []

    def refuse_staging(*arguments, **options):
        staged.append(None)
        raise AssertionError("committed exact replay staged publication bytes")

    monkeypatch.setattr(plane, "_stage_publication", refuse_staging)
    monkeypatch.setattr(plane, "_write_staged_bytes", refuse_staging)
    try:
        repeated = plane.write_batch(requests)
    finally:
        print(json.dumps({"committed_members": count, "replay_staging_calls": len(staged)}))
    assert not staged
    assert repeated == tuple(replace(item, created=False) for item in initial)
    assert _census(tmp_path / "exact-replay") == before


def test_descriptor_admission_counts_current_open_files_and_preserves_reserve(tmp_path, monkeypatch):
    plane = _plane(tmp_path / "occupied-descriptors")
    monkeypatch.setattr(plane, "_stage_publication", _no_staging)
    occupied = []
    try:
        with _descriptor_limit(64):
            for _ in range(24):
                occupied.append(os.open(os.devnull, os.O_RDONLY))
            with pytest.raises(ExternalRootUnavailable, match="descriptor capacity"):
                plane.write_batch(_requests(32))
    finally:
        for descriptor in occupied:
            os.close(descriptor)


@pytest.mark.parametrize("unavailable", ("limit", "census"))
def test_unobservable_descriptor_capacity_refuses_before_staging(tmp_path, monkeypatch, unavailable):
    plane = _plane(tmp_path / "unobservable-capacity")
    monkeypatch.setattr(plane, "_stage_publication", _no_staging)

    def unsupported(*arguments, **options):
        raise OSError("software fixture cannot observe descriptor capacity")

    if unavailable == "limit":
        monkeypatch.setattr(resource, "getrlimit", unsupported)
    else:
        monkeypatch.setattr(os, "scandir", unsupported)
    with pytest.raises(ExternalRootUnavailable, match="descriptor capacity cannot be observed safely"):
        plane.write_batch(_requests(2))


@pytest.mark.parametrize("expected_identity", (False, True))
def test_committed_stream_replay_checks_actual_chunks_without_staging(tmp_path, monkeypatch, expected_identity):
    plane = _plane(tmp_path / "stream-replay")
    requests = _requests(3)
    initial = plane.write_batch(requests)
    before = _census(tmp_path / "stream-replay")
    consumed = []

    def chunks(request):
        consumed.append(request.relative_path)
        for offset in range(0, len(request.payload), 7):
            yield request.payload[offset:offset + 7]

    streams = tuple(replace(request.as_stream(), chunks=chunks(request), maximum_chunk_bytes=7,
                    **({} if expected_identity else {"expected_size_bytes": None, "expected_physical_sha256": None}))
                    for request in requests)
    monkeypatch.setattr(plane, "_stage_publication", _no_staging)
    monkeypatch.setattr(plane, "_write_staged_bytes", _no_staging)
    repeated = plane.write_batch(streams)
    assert consumed == [request.relative_path for request in requests]
    assert repeated == tuple(replace(item, created=False) for item in initial)
    assert _census(tmp_path / "stream-replay") == before


@pytest.mark.parametrize("damage", ("wrong-bytes", "short", "too-long", "wrong-chunk-type"))
def test_declared_stream_identity_cannot_hide_different_actual_replay_bytes(tmp_path, monkeypatch, damage):
    plane = _plane(tmp_path / "changed-stream")
    requests = _requests(2)
    plane.write_batch(requests)
    selected = requests[-1]
    chunks = {
        "wrong-bytes": (b"x" + selected.payload[1:],),
        "short": (selected.payload[:-1],),
        "too-long": (selected.payload, b"x"),
        "wrong-chunk-type": (bytearray(selected.payload),),
    }[damage]
    streams = (requests[0].as_stream(), replace(selected.as_stream(), chunks=iter(chunks)))
    before = _census(tmp_path / "changed-stream")
    monkeypatch.setattr(plane, "_stage_publication", _no_staging)
    monkeypatch.setattr(plane, "_write_staged_bytes", _no_staging)
    with pytest.raises(ArtifactIdentityConflict):
        plane.write_batch(streams)
    assert _census(tmp_path / "changed-stream") == before


@pytest.mark.parametrize("damage", ("payload", "sidecar", "marker", "missing-payload", "missing-first-sidecar", "intent"))
def test_committed_replay_refuses_incomplete_or_changed_custody_without_staging(tmp_path, monkeypatch, damage):
    plane = _plane(tmp_path / "changed-custody")
    requests = _requests(2)
    results = plane.write_batch(requests)
    marker = next((tmp_path / "changed-custody").rglob("*.commit.json"))
    if damage == "marker":
        path = marker
    elif damage == "intent":
        path = marker.with_name(marker.name.replace(".commit.json", ".intent.json"))
    elif damage == "missing-first-sidecar":
        path = plane.root.resolve(results[0].manifest_materialization.relative_path, for_write=False)
    elif damage == "sidecar":
        path = plane.root.resolve(results[-1].manifest_materialization.relative_path, for_write=False)
    else:
        path = plane.root.resolve(results[-1].materialization.relative_path, for_write=False)
    if damage.startswith("missing-"):
        path.unlink()
    else:
        path.write_bytes(b"{}")
    before = _census(tmp_path / "changed-custody")
    monkeypatch.setattr(plane, "_stage_publication", _no_staging)
    monkeypatch.setattr(plane, "_write_staged_bytes", _no_staging)
    with pytest.raises(ArtifactIdentityConflict):
        plane.write_batch(requests)
    assert _census(tmp_path / "changed-custody") == before


def test_absent_commit_uses_original_publication_protocol_to_complete_exact_pairs(tmp_path, monkeypatch):
    plane = _plane(tmp_path / "missing-commit")
    requests = _requests(2)
    initial = plane.write_batch(requests)
    marker = next((tmp_path / "missing-commit").rglob("*.commit.json"))
    marker_bytes = marker.read_bytes()
    marker.unlink()
    staged = []
    original = plane._stage_publication

    def count_staging(*arguments, **options):
        staged.append(None)
        return original(*arguments, **options)

    monkeypatch.setattr(plane, "_stage_publication", count_staging)
    repeated = plane.write_batch(requests)
    assert len(staged) == len(requests)
    assert repeated == tuple(replace(item, created=False) for item in initial)
    assert marker.read_bytes() == marker_bytes


def test_interrupted_intent_owned_prefix_keeps_original_recovery_contract(tmp_path, monkeypatch):
    plane = _plane(tmp_path / "interrupted-intent")
    requests = _requests(2)
    original = plane._write_publication_intent

    def interrupted(path, intent):
        original(path, intent)
        raise KeyboardInterrupt("software interruption after durable intent")

    with monkeypatch.context() as patch:
        patch.setattr(plane, "_write_publication_intent", interrupted)
        with pytest.raises(KeyboardInterrupt, match="durable intent"):
            plane.write_batch(requests)
    intent = next((tmp_path / "interrupted-intent").rglob("*.intent.json"))
    original_intent = intent.read_bytes()
    partial = plane.root.resolve(requests[0].relative_path, for_write=True)
    partial.write_bytes(requests[0].payload[:17])
    assert original_intent and not tuple((tmp_path / "interrupted-intent").rglob("*.commit.json"))
    recovered = plane.write_batch(requests)
    assert all(item.created for item in recovered)
    assert not intent.exists()
    assert partial.read_bytes() == requests[0].payload


def _interrupted_unpinned_batch(plane, requests, monkeypatch, *, compact):
    """Retain the real durable intent and simulate an interrupted pair write."""
    captured = []
    publish = plane._publish_staged_batch
    write_intent = plane._write_publication_intent

    def capture(batch):
        captured.append((batch, tuple(item.staged_sidecar_path.read_bytes() for item in batch.members)))
        return publish(batch)

    def interrupt(path, intent):
        write_intent(path, intent)
        raise KeyboardInterrupt("software interruption after durable intent")

    with monkeypatch.context() as patch:
        patch.setattr(plane, "_publish_staged_batch", capture)
        patch.setattr(plane, "_write_publication_intent", interrupt)
        with pytest.raises(KeyboardInterrupt, match="durable intent"):
            plane.write_batch(_unpinned_streams(requests), compact_manifests=compact)
    batch, sidecars = captured[0]
    first = batch.members[0]
    first.artifact_path.write_bytes(requests[0].payload[:17])
    first.sidecar_path.write_bytes(sidecars[0][:31])
    assert batch.intent_path.is_file() and not batch.commit_path.exists()
    return batch, sidecars


def _unpinned_streams(requests):
    return tuple(replace(request.as_stream(), expected_size_bytes=None, expected_physical_sha256=None)
                 for request in requests)


@pytest.mark.parametrize("compact", (False, True))
def test_unpinned_stream_recovers_owned_interrupted_first_sidecar(tmp_path, monkeypatch, compact):
    root = tmp_path / "unpinned-interruption"
    plane = _plane(root)
    requests = _requests(2)
    batch, sidecars = _interrupted_unpinned_batch(plane, requests, monkeypatch, compact=compact)

    recovered = plane.write_batch(_unpinned_streams(requests), compact_manifests=compact)

    assert all(item.created for item in recovered)
    assert not batch.intent_path.exists()
    assert batch.commit_path.read_bytes() == batch.commit_payload
    for item, request, sidecar in zip(batch.members, requests, sidecars, strict=True):
        assert item.artifact_path.read_bytes() == request.payload
        assert item.sidecar_path.read_bytes() == sidecar
    assert not tuple(root.rglob("*.partial"))


@pytest.mark.parametrize("compact", (False, True))
@pytest.mark.parametrize("damage", ("unowned", "foreign-sidecar", "changed-request"))
def test_unpinned_interruption_refuses_unowned_or_different_bytes(tmp_path, monkeypatch, compact, damage):
    root = tmp_path / "unpinned-refusal"
    plane = _plane(root)
    requests = _requests(2)
    batch, _sidecars = _interrupted_unpinned_batch(plane, requests, monkeypatch, compact=compact)
    if damage == "unowned":
        batch.intent_path.unlink()
    elif damage == "foreign-sidecar":
        batch.members[0].sidecar_path.write_bytes(b'{"foreign":')
    else:
        requests = tuple(replace(request, payload=request.payload.replace(b"a" * 64, b"b" * 64))
                         for request in requests)
    before = _census(root)

    with pytest.raises(ArtifactIdentityConflict):
        plane.write_batch(_unpinned_streams(requests), compact_manifests=compact)

    assert _census(root) == before
    assert not batch.commit_path.exists()
    assert not tuple(root.rglob("*.partial"))


@pytest.mark.parametrize("compact", (False, True))
@pytest.mark.parametrize("damage", ("prefix", "foreign"))
def test_unpinned_replay_never_repairs_a_committed_sidecar(tmp_path, compact, damage):
    root = tmp_path / "unpinned-committed-refusal"
    plane = _plane(root)
    requests = _requests(2)
    initial = plane.write_batch(_unpinned_streams(requests), compact_manifests=compact)
    sidecar = plane.root.resolve(initial[0].manifest_materialization.relative_path, for_write=False)
    sidecar.write_bytes(sidecar.read_bytes()[:31] if damage == "prefix" else b'{"foreign":')
    before = _census(root)

    with pytest.raises(ArtifactIdentityConflict):
        plane.write_batch(_unpinned_streams(requests), compact_manifests=compact)

    assert _census(root) == before
    assert not tuple(root.rglob("*.partial"))


def test_empty_expected_stream_retains_zero_byte_identity_on_initial_publish_and_replay(tmp_path, monkeypatch):
    """An empty software prefix is custody only, never native completion."""
    plane = _plane(tmp_path / "empty-stream")
    request = replace(_requests(1)[0], payload=b"", profile=ArtifactProfile.NATIVE_SUBWORK_PREFIX,
                      payload_schema="empirical-lawhood/runtime/native-subwork-received-prefix",
                      media_type="application/octet-stream")
    initial = plane.write_stream(request.as_stream())
    assert initial.created and initial.materialization.size_bytes == 0
    before = _census(tmp_path / "empty-stream")
    monkeypatch.setattr(plane, "_stage_publication", _no_staging)
    monkeypatch.setattr(plane, "_write_staged_bytes", _no_staging)
    repeated = plane.write_stream(request.as_stream())
    assert repeated == replace(initial, created=False)
    assert _census(tmp_path / "empty-stream") == before


@pytest.mark.parametrize("identical", (False, True))
def test_concurrent_publishers_preserve_one_exact_complete_winner(tmp_path, monkeypatch, identical):
    plane = _plane(tmp_path / "racing-publishers")
    other_plane = ExternalArtifactPlane(plane.root)
    first = _requests(2)
    second = first if identical else tuple(replace(request, payload=request.payload.replace(b"a" * 64, b"b" * 64))
                                           for request in first)
    assert identical or first != second
    barrier = threading.Barrier(2)
    original = ExternalArtifactPlane._publish_staged_batch

    def simultaneous_publish(selected, batch):
        barrier.wait(timeout=20)
        return original(selected, batch)

    monkeypatch.setattr(ExternalArtifactPlane, "_publish_staged_batch", simultaneous_publish)
    with ThreadPoolExecutor(max_workers=2) as workers:
        futures = [workers.submit(selected.write_batch, requests)
                   for selected, requests in ((plane, first), (other_plane, second))]
        results, conflicts = [], []
        for future in futures:
            try:
                results.append(future.result(timeout=40))
            except ArtifactIdentityConflict as error:
                conflicts.append(error)
    assert sum(all(item.created for item in result) for result in results) == 1
    if identical:
        assert len(results) == 2 and not conflicts
        assert sum(all(not item.created for item in result) for result in results) == 1
    else:
        assert len(results) == len(conflicts) == 1
    winner = next(result for result in results if all(item.created for item in result))
    winner_payloads = tuple(plane.root.resolve(item.materialization.relative_path, for_write=False).read_bytes()
                            for item in winner)
    assert winner_payloads in (tuple(item.payload for item in first), tuple(item.payload for item in second))
    assert not tuple((tmp_path / "racing-publishers").rglob("*.partial"))
    assert not tuple((tmp_path / "racing-publishers").rglob("*.intent.json"))
