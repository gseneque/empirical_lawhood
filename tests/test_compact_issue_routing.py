# SPDX-License-Identifier: MPL-2.0
"""Compact ISSUE routing uses the custody owner and preserves legacy controls.

All issues and grants here are disclosed synthetic software fixtures. These
checks create no scientific qualification, real authority or native work.
"""

from dataclasses import replace
import json
from types import SimpleNamespace

import pytest

from empirical_lawhood.infrastructure import catalog_rebuild
from empirical_lawhood.infrastructure import publication_metadata
from empirical_lawhood.infrastructure import study_issue
from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict
from empirical_lawhood.infrastructure.bounded_io import MAX_ARTIFACT_MANIFEST_BYTES
from empirical_lawhood.infrastructure.publication_metadata import read_publication_metadata
from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest
from empirical_lawhood.kernel.evidence import OutcomeAccess
from empirical_lawhood.runtime.artifact_sidecar import ArtifactManifestReference
from empirical_lawhood.runtime.artifacts import ArtifactManifest
from empirical_lawhood.runtime.catalog import (
    ArtifactLocatorRecord, CatalogSnapshot, CatalogVerificationStatus,
    LogicalArtifactRecord, StorageRootRecord,
)
from tests.numerical_provenance_fixtures import numerical_plane
from tests.runtime_platform.test_study_issue import _issue_api_fixture, _issue_request
from tests.test_publication_metadata import _block_payload_access, _requests


class _AlternatePlane:
    def __init__(self, plane, *, missing=(), **hooks):
        self._plane, self._missing, self._hooks = plane, missing, hooks

    def __getattr__(self, name):
        if name in self._missing:
            raise AttributeError(name)
        if name in self._hooks:
            return self._hooks[name]
        return getattr(self._plane, name)


def _snapshot(plane, publication):
    logical, physical, root = publication.logical, publication.materialization, plane.root.contract
    return CatalogSnapshot(
        storage_roots=(StorageRootRecord(root.storage_root_id, root.logical_name,
            root.canonical_path, root.mount_contract_schema, CatalogVerificationStatus.VERIFIED),),
        logical_artifacts=(LogicalArtifactRecord(logical.logical_artifact_id, logical.content_sha256,
            logical.payload_schema, logical.profile, logical.media_type, logical.visibility_ceiling),),
        artifact_locators=(ArtifactLocatorRecord(physical.materialization_id, physical.logical_artifact_id,
            physical.storage_root_id, physical.relative_path, physical.physical_sha256, physical.size_bytes,
            physical.compression, physical.partition_selector, CatalogVerificationStatus.VERIFIED),),
        receipts=(), scientific_objects=(), knowledge_edges=(), metric_definitions=(),
        metric_observations=(), exploration_attempts=(),
    )


def test_public_standard_issue_uses_compact_batch_and_owner_reads_but_keeps_receipt_legacy(
        tmp_path, monkeypatch):
    api, paths, external, _ = _issue_api_fixture(tmp_path)
    plane = api._study_issue_publisher.artifact_plane
    original_write, original_read = plane.write_compact_batch, plane.read_manifest
    writes, reads = [], []

    def write(requests):
        writes.append(tuple(request.relative_path for request in requests))
        return original_write(requests)

    def read(relative, *, maximum_bytes=None):
        reads.append((relative, maximum_bytes))
        return original_read(relative, maximum_bytes=maximum_bytes)

    monkeypatch.setattr(plane, "write_compact_batch", write)
    monkeypatch.setattr(plane, "read_manifest", read)
    preview = api.issue_study(_issue_request(paths, confirmed=False))
    assert preview.reason_codes == ("WRITE_CONFIRMATION_REQUIRED",)
    assert writes == [] and list(external.iterdir()) == []
    issued = api.issue_study(_issue_request(paths, confirmed=True))
    assert issued.succeeded, (issued.reason_codes, issued.errors)
    manifest, receipt = issued.payload.manifest, issued.payload.publication_receipt
    assert receipt is not None and len(writes) == 1
    main = f"issued-programmes/{manifest.issue_id}/manifest.json"
    assert set(writes[0]) == {main, *(member.relative_path for member in manifest.members)}
    assert json.loads((external / (main + ".manifest.json")).read_bytes())["schema"] == ArtifactManifestReference.SCHEMA
    receipt_path = external / f"issued-programmes/{manifest.issue_id}/publication-receipt.json"
    receipt_raw = receipt_path.with_name(receipt_path.name + ".manifest.json").read_bytes()
    assert json.loads(receipt_raw)["schema"] == ArtifactManifest.SCHEMA
    assert decode_artifact_manifest(receipt_raw).logical.logical_artifact_id == receipt.receipt_id
    replayed = api._study_issue_publisher.load_study(manifest.issue_id)
    assert replayed.manifest.canonical_bytes() == manifest.canonical_bytes()
    assert replayed.publication_receipt.canonical_bytes() == receipt.canonical_bytes()
    assert (main, study_issue.MAX_PROGRAMME_AUTHORITY_BYTES) in reads
    # The issue consumer's own calls retain its bound. Receipt read paths stay
    # with their original decoder; custody may inspect them independently.
    assert not any(path.endswith("/publication-receipt.json") for path, _ in reads)


@pytest.mark.parametrize("write_hook", ("absent", "noncallable"))
def test_alternate_plane_keeps_original_write_and_decode_fallback(tmp_path, write_hook):
    api, paths, external, _ = _issue_api_fixture(tmp_path)
    publisher = api._study_issue_publisher
    hidden = {"read_manifest", "verify_manifest_members", "write_compact_batch"}
    hooks = {}
    if write_hook == "noncallable":
        hidden.remove("write_compact_batch")
        hooks["write_compact_batch"] = None
    publisher._artifact_plane = _AlternatePlane(publisher.artifact_plane, missing=hidden, **hooks)
    issued = api.issue_study(_issue_request(paths, confirmed=True))
    assert issued.succeeded, (issued.reason_codes, issued.errors)
    manifest, receipt = issued.payload.manifest, issued.payload.publication_receipt
    replayed = publisher.load_study(manifest.issue_id)
    assert replayed.manifest == manifest and replayed.publication_receipt == receipt
    for member in manifest.members:
        raw = (external / (member.relative_path + ".manifest.json")).read_bytes()
        assert json.loads(raw)["schema"] == ArtifactManifest.SCHEMA
        assert decode_artifact_manifest(raw).publication == receipt.publication


@pytest.mark.parametrize("access", (OutcomeAccess.OUTCOME_BLIND, OutcomeAccess.EVALUATION_SEALED))
@pytest.mark.parametrize("compact", (False, True))
def test_metadata_normalizes_every_sidecar_without_payload_access(tmp_path, monkeypatch, access, compact):
    plane = numerical_plane(tmp_path / "metadata")
    writer = plane.write_compact_batch if compact else plane.write_batch
    first, second = writer(_requests(access))
    read = plane.read_manifest
    reads = []

    def observed(relative, *, maximum_bytes=None):
        reads.append((relative, maximum_bytes))
        return read(relative, maximum_bytes=maximum_bytes)

    monkeypatch.setattr(plane, "read_manifest", observed)
    _block_payload_access(monkeypatch, plane, (first, second))
    actual = read_publication_metadata(plane, first)
    assert actual.logical == first.logical and actual.materialization == first.materialization
    assert actual.publication is not None and len(actual.publication.members) == 2
    # Only the selected sidecar resolves the marker. Siblings use the pure
    # owner codec with this call's checked binding, avoiding N full rosters.
    assert {relative for relative, _ in reads} == {first.materialization.relative_path}
    assert all(bound == plane.custody_limits.manifest_bytes for _, bound in reads)


@pytest.mark.parametrize("compact", (False, True))
def test_catalog_verifies_normalized_manifest_without_requiring_its_raw_encoding(tmp_path, monkeypatch, compact):
    plane = numerical_plane(tmp_path / "catalog")
    writer = plane.write_compact_batch if compact else plane.write_batch
    first, _ = writer(_requests(OutcomeAccess.OUTCOME_BLIND))
    snapshot = _snapshot(plane, first)
    original = plane.read_manifest
    reads = []

    def observed(relative, *, maximum_bytes=None):
        reads.append((relative, maximum_bytes))
        return original(relative, maximum_bytes=maximum_bytes)

    monkeypatch.setattr(plane, "read_manifest", observed)
    catalog_rebuild._verify_projected_artifacts(snapshot, plane)
    assert reads == [(first.materialization.relative_path, MAX_ARTIFACT_MANIFEST_BYTES)]
    substituted = replace(snapshot, artifact_locators=(replace(snapshot.artifact_locators[0],
        physical_sha256="f" * 64),))
    with pytest.raises(catalog_rebuild.CatalogRebuildError, match="locator differs"):
        catalog_rebuild._verify_projected_artifacts(substituted, plane)


def test_metadata_and_catalog_legacy_fallback_still_authenticate_siblings(tmp_path):
    plane = numerical_plane(tmp_path / "fallback")
    first, second = plane.write_batch(_requests(OutcomeAccess.OUTCOME_BLIND))
    alternate = _AlternatePlane(plane, missing={"read_manifest"})
    assert read_publication_metadata(alternate, first).logical == first.logical
    catalog_rebuild._verify_projected_artifacts(_snapshot(plane, first), alternate)
    victim = plane.root.resolve(second.materialization.relative_path + ".manifest.json", for_write=False)
    victim.unlink()
    with pytest.raises((ValueError, OSError)):
        read_publication_metadata(alternate, first)
    with pytest.raises(catalog_rebuild.CatalogRebuildError):
        catalog_rebuild._verify_projected_artifacts(_snapshot(plane, first), alternate)


@pytest.mark.parametrize("consumer", ("issue", "metadata", "catalog"))
def test_present_noncallable_reader_refuses_instead_of_using_a_legacy_decoder(tmp_path, consumer):
    api, paths, _, _ = _issue_api_fixture(tmp_path)
    issued = api.issue_study(_issue_request(paths, confirmed=True))
    assert issued.succeeded
    publisher = api._study_issue_publisher
    plane = publisher.artifact_plane
    broken = _AlternatePlane(plane, read_manifest=None)
    publisher._artifact_plane = broken
    receipt = issued.payload.publication_receipt
    publication = SimpleNamespace(logical=receipt.manifest_logical, materialization=receipt.manifest_materialization)
    with pytest.raises(TypeError, match="must be callable"):
        if consumer == "issue":
            publisher.load_study(issued.payload.manifest.issue_id)
        elif consumer == "metadata":
            read_publication_metadata(broken, publication)
        else:
            catalog_rebuild._verify_projected_artifacts(_snapshot(plane, publication), broken)


def test_compact_metadata_corruption_refuses_before_payload_access(tmp_path, monkeypatch):
    plane = numerical_plane(tmp_path / "corrupt-metadata")
    first, second = plane.write_compact_batch(_requests(OutcomeAccess.EVALUATION_SEALED))
    actual = plane.read_manifest(first.materialization.relative_path)
    plane.root.resolve(actual.publication.commit_marker_relative_path, for_write=False).unlink()
    _block_payload_access(monkeypatch, plane, (first, second))
    with pytest.raises((ArtifactIdentityConflict, ValueError, OSError)):
        read_publication_metadata(plane, first)


@pytest.mark.parametrize("compact", (False, True))
def test_metadata_rechecks_exact_commit_after_resolving_siblings(tmp_path, monkeypatch, compact):
    plane = numerical_plane(tmp_path / "changed-marker")
    writer = plane.write_compact_batch if compact else plane.write_batch
    first, second = writer(_requests(OutcomeAccess.EVALUATION_SEALED))
    actual = plane.read_manifest(first.materialization.relative_path)
    marker = plane.root.resolve(actual.publication.commit_marker_relative_path, for_write=False)
    decode = publication_metadata.decode_artifact_sidecar
    sibling_count = []

    def changed(raw, **options):
        sibling = decode(raw, **options)
        sibling_count.append(sibling)
        if len(sibling_count) == 2:
            marker.write_bytes(b"{}\n")
        return sibling

    monkeypatch.setattr(publication_metadata, "decode_artifact_sidecar", changed)
    _block_payload_access(monkeypatch, plane, (first, second))
    with pytest.raises(ValueError, match="changed during its read"):
        read_publication_metadata(plane, first)
    assert len(sibling_count) == 2
