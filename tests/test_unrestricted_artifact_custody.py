# SPDX-License-Identifier: MPL-2.0
"""Exposed custody software checks; no scientific execution or authority.

Stage for tests/test_unrestricted_artifact_custody.py after ArtifactCustodyLimits
is installed. All payloads and lineage leaves have actual canonical bytes. The
real guarded artifact plane publishes and authenticates them; no test signer,
native provider, qualification record or synthetic scientific outcome is used.
"""

from dataclasses import dataclass, replace
from hashlib import sha256
from typing import ClassVar

import pytest

from empirical_lawhood.infrastructure.artifacts import (
    ArtifactIdentityConflict,
    ExternalArtifactPlane,
)
from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.infrastructure.development_native_custody import (
    read_development_native_payload,
)
from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.runtime.artifacts import (
    ArtifactCustodyLimits,
    ArtifactLineageParent,
    ArtifactProfile,
    ArtifactWriteRequest,
    lineage_parent_sort_key,
)
from tests.numerical_provenance_fixtures import numerical_plane


@dataclass(frozen=True, slots=True)
class SoftwarePayload(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/tests/exposed-custody-payload"
    record_id: str
    text: str


@dataclass(frozen=True, slots=True)
class SoftwareSources(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/tests/exposed-custody-sources"
    record_id: str
    sources: tuple[SoftwarePayload, ...]


def request(record, *, scope="software.outputs", root="software/outputs", parents=()):
    return ArtifactWriteRequest(
        logical_artifact_id=record.record_id,
        relative_path=f"{root}/{record.record_id}.json",
        payload_schema=record.SCHEMA,
        profile=ArtifactProfile.CANONICAL_JSON,
        media_type="application/json",
        publication_scope_id=scope,
        publication_scope_relative_root=root,
        payload=record.canonical_bytes(),
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY,
        parent_visibility_ceilings=tuple(parent.visibility_ceiling for parent in parents),
        outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
        lineage_parents=parents,
    )


def manifest(plane, result):
    raw = read_bounded_bytes(
        plane.root.resolve(result.manifest_materialization.relative_path, for_write=False),
        maximum_bytes=None,
    )
    assert len(raw) == result.manifest_materialization.size_bytes
    assert sha256(raw).hexdigest() == result.manifest_materialization.physical_sha256
    value = decode_artifact_manifest(raw)
    assert value.logical == result.logical
    assert value.materialization == result.materialization
    return value


def census(plane):
    root = plane.root.resolve("software", for_write=False).parent
    return {
        path.relative_to(root).as_posix(): (path.stat().st_size, sha256(path.read_bytes()).hexdigest())
        for path in root.rglob("*") if path.is_file() and not path.name.endswith(".lock")
    }


def test_actual_canonical_payload_and_string_exceed_former_custody_limits(tmp_path, monkeypatch):
    from empirical_lawhood.infrastructure import artifact_validation as formats
    monkeypatch.setattr(formats._CanonicalJsonFileInspector, 'validate',
        lambda self: pytest.fail('bounded large canonical control selected the token-by-token parser'))
    plane = numerical_plane(tmp_path / "custody")
    record = SoftwarePayload("software.large-payload", "x" * (33 * 1024**2))
    selected = request(record)
    assert len(selected.payload) > 32 * 1024**2
    result = plane.write(selected)
    retained = manifest(plane, result)
    fresh = ExternalArtifactPlane(plane.root)
    raw = read_development_native_payload(fresh, retained, maximum_bytes=None)
    assert raw == selected.payload
    assert decode_canonical_bytes(raw, SoftwarePayload, maximum_bytes=None) == record
    with pytest.raises(ValueError, match="bound"):
        read_development_native_payload(fresh, retained, maximum_bytes=len(raw) - 1)
    altered = replace(selected, payload=SoftwarePayload(record.record_id, "changed").canonical_bytes())
    before = census(plane)
    with pytest.raises(ArtifactIdentityConflict):
        fresh.write(altered)
    assert census(plane) == before


def test_authentic_direct_lineage_manifest_exceeds_former_megabyte_limit(tmp_path):
    plane = numerical_plane(tmp_path / "custody")
    # Retain every actual leaf byte in one authenticated collection. The child
    # names both that complete source collection and its nested canonical leaves.
    original = SoftwareSources("software.parent-collection", tuple(
        SoftwarePayload(f"software.parent-{index:05d}", f"exposed source value {index}")
        for index in range(4096)
    ))
    published_sources = plane.write(request(original, scope="software.sources", root="software/sources"))
    source_manifest = manifest(plane, published_sources)
    authentic = decode_canonical_bytes(
        read_development_native_payload(plane, source_manifest, maximum_bytes=None),
        SoftwareSources, maximum_bytes=None,
    )
    assert authentic == original
    identities = (ObjectIdentity.from_record(authentic.record_id, authentic), *(
        ObjectIdentity.from_record(record.record_id, record) for record in authentic.sources
    ))
    parents = tuple(sorted((ArtifactLineageParent(
        identity, VisibilityCeiling.DEVELOPMENT_ONLY, OutcomeAccess.DEVELOPMENT_VISIBLE,
    ) for identity in identities), key=lineage_parent_sort_key))
    record = SoftwarePayload("software.large-lineage", "complete direct source fan-in")
    written = plane.write(request(record, parents=parents))
    assert written.manifest_materialization.size_bytes > 1024**2
    retained = manifest(plane, written)
    assert retained.logical.lineage_parents == parents
    assert len(retained.logical.lineage_parents) == 4097
    fresh = ExternalArtifactPlane(plane.root)
    assert read_development_native_payload(fresh, retained, maximum_bytes=None) == record.canonical_bytes()
    limited = ExternalArtifactPlane(plane.root, custody_limits=ArtifactCustodyLimits(manifest_bytes=1024**2))
    with pytest.raises(ArtifactIdentityConflict):
        limited.verify_manifest(retained)
    forged_parent = replace(parents[-1], identity=replace(parents[-1].identity, object_fingerprint="0" * 64))
    forged = replace(retained, logical=replace(retained.logical, lineage_parents=(*parents[:-1], forged_parent)), publication=None)
    with pytest.raises(ArtifactIdentityConflict):
        fresh.verify_manifest(forged)


def test_257_output_batch_preserves_exact_siblings_and_corruption_refusals(tmp_path):
    plane = numerical_plane(tmp_path / "custody")
    requests = tuple(request(SoftwarePayload(f"software.output-{index:04d}", f"software-output-{index:04d}"))
                     for index in range(257))
    results = plane.write_batch(requests)
    assert len(results) == 257 and all(result.created for result in results)
    manifests = tuple(manifest(plane, result) for result in results)
    publication = manifests[0].publication
    assert publication is not None and len(publication.members) == 257
    assert all(value.publication == publication for value in manifests)
    assert {member.relative_path for member in publication.members} == {value.relative_path for value in requests}
    assert {member.physical_sha256 for member in publication.members} == {sha256(value.payload).hexdigest() for value in requests}
    fresh = ExternalArtifactPlane(plane.root)
    fresh.verify_manifests(manifests)
    before = census(plane)
    repeated = fresh.write_batch(requests)
    assert all(not result.created for result in repeated)
    assert tuple((value.logical, value.materialization) for value in repeated) == tuple(
        (value.logical, value.materialization) for value in results
    )
    assert census(plane) == before
    forged = replace(manifests[0], logical=replace(manifests[0].logical, content_sha256="0" * 64), publication=None)
    with pytest.raises(ArtifactIdentityConflict):
        fresh.verify_manifest(forged)
    # Asking for the first member must still authenticate the last assigned
    # sibling. A reader cannot exclude an inconvenient corrupt or missing case.
    victim = manifests[-1]
    path = plane.root.resolve(victim.materialization.relative_path, for_write=False)
    original_payload = path.read_bytes()
    changed_payload = original_payload.replace(b"software-output-", b"software-mutant-", 1)
    assert changed_payload != original_payload
    path.write_bytes(changed_payload)
    with pytest.raises(ArtifactIdentityConflict):
        fresh.verify_manifest(manifests[0])
    path.write_bytes(original_payload)
    sidecar = plane.root.resolve(results[-1].manifest_materialization.relative_path, for_write=False)
    original_sidecar = sidecar.read_bytes()
    sidecar.unlink()
    with pytest.raises(ArtifactIdentityConflict):
        fresh.verify_manifest(manifests[0])
    sidecar.write_bytes(original_sidecar)
    commit = plane.root.resolve(publication.commit_marker_relative_path, for_write=False)
    commit.write_bytes(commit.read_bytes() + b"\n")
    with pytest.raises(ArtifactIdentityConflict):
        fresh.verify_manifest(manifests[0])


@pytest.mark.parametrize("field", (
    "in_memory_payload_bytes", "canonical_json_token_bytes", "canonical_json_depth", "manifest_bytes",
    "publication_aggregate_bytes", "publication_marker_bytes", "publication_intent_bytes",
))
def test_explicit_finite_custody_limits_refuse_without_visible_publication(tmp_path, field):
    base = numerical_plane(tmp_path / "custody")
    plane = ExternalArtifactPlane(base.root, custody_limits=ArtifactCustodyLimits(**{field: 1}))
    selected = request(SoftwarePayload("software.finite-refusal", "ordinary valid software bytes"))
    with pytest.raises(ArtifactIdentityConflict):
        plane.write(selected)
    assert not base.root.resolve(selected.relative_path, for_write=False).exists()
    assert not base.root.resolve(selected.relative_path + ".manifest.json", for_write=False).exists()


def test_explicit_finite_member_and_stream_bounds_remain_enforced(tmp_path):
    base = numerical_plane(tmp_path / "custody")
    requests = tuple(request(SoftwarePayload(f"software.member-{index:04d}", "retained software bytes"))
                     for index in range(257))
    finite = ExternalArtifactPlane(base.root, custody_limits=ArtifactCustodyLimits(publication_members=256))
    with pytest.raises(ArtifactIdentityConflict):
        finite.write_batch(requests)
    assert not any(base.root.resolve(value.relative_path, for_write=False).exists() for value in requests)
    selected = requests[0]
    stream = replace(selected.as_stream(), maximum_bytes=len(selected.payload) - 1,
                     chunks=(selected.payload[index:index + 1] for index in range(len(selected.payload))),
                     maximum_chunk_bytes=1, expected_size_bytes=None, expected_physical_sha256=None)
    with pytest.raises(ArtifactIdentityConflict):
        base.write_stream(stream)
    assert not base.root.resolve(selected.relative_path, for_write=False).exists()
    assert not base.root.resolve(selected.relative_path + ".manifest.json", for_write=False).exists()




def test_finite_limits_survive_semantic_registry_view(tmp_path):
    base = numerical_plane(tmp_path / "custody")
    limits = ArtifactCustodyLimits(publication_members=1)
    finite = ExternalArtifactPlane(base.root, custody_limits=limits)
    view = finite.with_semantic_validation_registry(finite.semantic_validations)
    assert view.custody_limits == limits
    with pytest.raises(ArtifactIdentityConflict):
        view.write_batch(tuple(request(SoftwarePayload(f"software.member-{i}", "bytes")) for i in range(2)))
