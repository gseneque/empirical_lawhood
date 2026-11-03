# SPDX-License-Identifier: MPL-2.0
"""Guarded publication metadata and explicit materialization access.

The metadata reader checks sidecars and the exact durable commit marker.
The separate access owner verifies actual member bytes when explicitly called.
Neither owner creates scientific qualification or access authority.
"""

from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.infrastructure.artifact_sidecars import decode_artifact_sidecar
from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest
from empirical_lawhood.runtime.artifacts import ArtifactPublicationCommit, artifact_publication_member
from empirical_lawhood.infrastructure.artifacts import (
    ExternalArtifactPlane, _ScopedArtifactPlane, _has_stock_manifest_reads,
)


def read_publication_metadata(plane, publication):
    """Read only the selected original sidecar, commit and sibling sidecars."""
    logical, physical = publication.logical, publication.materialization
    if (physical.storage_root_id != plane.root.contract.storage_root_id
            or physical.logical_artifact_id != logical.logical_artifact_id):
        raise ValueError('publication metadata changes its selected custody root or logical member')

    def sidecar(relative, *, publication=None):
        if publication is not None:
            # This binding belongs to this call's authenticated selected
            # sidecar and exact marker. Resolve siblings without reopening
            # the full commit roster for every compact reference.
            return decode_artifact_sidecar(read_bounded_bytes(
                plane.root.resolve(relative+'.manifest.json', for_write=False),
                maximum_bytes=plane.custody_limits.manifest_bytes),
                maximum_bytes=plane.custody_limits.manifest_bytes, publication=publication)
        try:
            read_manifest = plane.read_manifest
        except AttributeError:
            return decode_artifact_manifest(read_bounded_bytes(plane.root.resolve(relative+'.manifest.json', for_write=False),
                maximum_bytes=plane.custody_limits.manifest_bytes), maximum_bytes=plane.custody_limits.manifest_bytes)
        if not callable(read_manifest):
            raise TypeError("artifact plane manifest reader hook must be callable")
        return read_manifest(relative, maximum_bytes=plane.custody_limits.manifest_bytes)

    actual = sidecar(physical.relative_path)
    if actual.logical != logical or actual.materialization != physical or actual.publication is None:
        raise ValueError('publication metadata differs from its exact original declared sidecar')
    binding = actual.publication
    expected = ArtifactPublicationCommit(binding.publication_batch_id, binding.publication_scope, binding.members)
    expected_bytes = expected.canonical_bytes()
    if (plane.custody_limits.exceeds('publication_members', len(binding.members))
            or plane.custody_limits.exceeds('publication_marker_bytes', len(expected_bytes))
            or len(expected_bytes) != binding.commit_marker_size_bytes
            or expected.fingerprint() != binding.commit_marker_sha256):
        raise ValueError('publication metadata changes its exact bounded durable marker identity')
    marker = read_bounded_bytes(plane.root.resolve(binding.commit_marker_relative_path, for_write=False),
        maximum_bytes=len(expected_bytes))
    if marker != expected_bytes:
        raise ValueError('publication metadata lacks its exact original durable commit marker')
    members = []
    for member in binding.members:
        sibling = sidecar(member.relative_path, publication=binding)
        if (sibling.publication != binding
                or artifact_publication_member(sibling.logical, sibling.materialization) != member):
            raise ValueError('publication metadata changes a declared original sibling member')
        members.append(member)
    if artifact_publication_member(logical, physical) not in members:
        raise ValueError('publication metadata omits its exact original member')
    final_marker = read_bounded_bytes(plane.root.resolve(binding.commit_marker_relative_path, for_write=False),
        maximum_bytes=len(expected_bytes))
    if final_marker != expected_bytes:
        raise ValueError('publication metadata durable commit marker changed during its read')
    return actual


def authenticate_published_materialization(plane, publication):
    """Verify selected sidecar identity and actual complete member bytes.

    This ordinary access owner creates no scientific qualifier or authority.
    Unlike the metadata-only reader above, this opens actual member payloads.
    """
    from empirical_lawhood.runtime.artifacts import ArtifactWriteResult
    if type(publication) is not ArtifactWriteResult:
        raise TypeError("publication access requires its exact original write result")
    actual = read_publication_metadata(plane, publication)
    relative = publication.materialization.relative_path + ".manifest.json"
    raw = read_bounded_bytes(plane.root.resolve(relative, for_write=False),
        maximum_bytes=plane.custody_limits.manifest_bytes)
    expected = plane._manifest_materialization(logical_artifact_id=publication.logical.logical_artifact_id,
        relative_path=relative, payload=raw)
    if expected != publication.manifest_materialization:
        raise ValueError("publication access changes exact original manifest materialization")
    plane.verify(publication.manifest_materialization)
    plane.verify_manifest(actual)
    return actual


def read_published_canonical_record(plane, publication, record_type, *, maximum_bytes=None):
    """Join the exact original sidecar before the combined typed-body read."""
    from empirical_lawhood.runtime.artifacts import ArtifactWriteResult
    from .canonical_record_read import read_verified_canonical_record

    if type(publication) is not ArtifactWriteResult:
        raise TypeError('canonical publication requires its exact original write result')
    if not supports_closed_publication_access(plane):
        actual = authenticate_published_materialization(plane, publication)
        return read_verified_canonical_record(plane, actual, record_type, maximum_bytes=maximum_bytes)
    logical, material = publication.logical, publication.materialization
    if (material.storage_root_id != plane.root.contract.storage_root_id
            or material.logical_artifact_id != logical.logical_artifact_id):
        raise ValueError('canonical publication changes its root or logical member')
    relative = material.relative_path + '.manifest.json'
    raw = read_bounded_bytes(plane.root.resolve(relative, for_write=False),
        maximum_bytes=plane.custody_limits.manifest_bytes)
    if plane._manifest_materialization(logical_artifact_id=logical.logical_artifact_id,
            relative_path=relative, payload=raw) != publication.manifest_materialization:
        raise ValueError('canonical publication changes its exact original sidecar bytes')
    actual = plane.read_manifest(material.relative_path, maximum_bytes=plane.custody_limits.manifest_bytes)
    if actual.logical != logical or actual.materialization != material:
        raise ValueError('canonical publication differs from its actual original manifest')
    return read_verified_canonical_record(plane, actual, record_type, maximum_bytes=maximum_bytes)


# These identities select an explicit closed batch, never a default admission.
# Capture resolved methods on both classes: an inherited method can be shadowed.

_STOCK_CLOSED_PUBLICATION_METHODS = tuple((owner, name, getattr(owner, name))
    for owner in (ExternalArtifactPlane, _ScopedArtifactPlane)
    for name in ("write", "write_batch", "write_stream", "write_compact_batch",
        "verify", "_manifest_materialization", "_stream_identity"))


def supports_closed_publication_access(plane):
    """Select stock closed-batch ordering; custom callers keep interleaving."""
    from .artifacts import _has_stock_artifact_plane_state
    return (_has_stock_manifest_reads(plane)
        and _has_stock_artifact_plane_state(plane)
        and all(getattr(owner, name) is method
            for owner, name, method in _STOCK_CLOSED_PUBLICATION_METHODS))


def checkpoint_publication_access(plane):
    """Check the prior observed union before a caller's publication effects.

    A base plane has no retained read roster. The immutable writer still owns
    every ordinary output/intent/commit check. This is not a reusable permit.
    """
    if not supports_closed_publication_access(plane):
        raise TypeError("closed publication access requires unchanged stock read/write hooks")
    if type(plane) is _ScopedArtifactPlane:
        plane.require_full_verification_snapshot()


def checkpoint_input_publications(plane, publications):
    """Recheck complete input publications inside a shared read lifetime.

    This checks each selected body, every atomic sibling, sidecar and commit
    marker, with live access callbacks. Unrelated observed history stays in
    the outer census for publication and final-return guards. This function
    is an input checkpoint, never a substitute for those effect boundaries.
    Custom custody policies retain their complete original snapshot check.
    """
    from pathlib import Path
    from .artifacts import ArtifactIdentityConflict, GuardedExternalRoot, LocalFilesystemInspector

    if (not supports_closed_publication_access(plane) or type(plane) is not _ScopedArtifactPlane
            or not plane._read_verification.context_depth
            or type(plane.root) is not GuardedExternalRoot
            or type(plane.root.inspector) is not LocalFilesystemInspector):
        plane.require_verification_snapshot()
        return
    plane.require_active_verification_scope()
    members = consume_published_materializations(plane, publications, consume=lambda members: members)
    root = Path(plane.root.contract.canonical_path)
    paths = set()
    for manifest in members.values():
        relative = manifest.materialization.relative_path
        paths.update((root / relative, root / (relative + '.manifest.json'),
            root / manifest.publication.commit_marker_relative_path))
    verification = plane._read_verification
    try:
        snapshots = {path: verification.snapshots[path] for path in paths}
    except KeyError as error:
        raise ArtifactIdentityConflict('input checkpoint lacks complete publication byte custody') from error
    plane._require_verification_snapshot_paths(snapshots,
        reason='input publication changed during its read', member_preflights=verification.member_preflights)
    plane.require_active_verification_scope()


def consume_published_materializations(plane, publications, *, consume):
    """Authenticate a closed typed roster, then consume under existing guards.

    Stock callers checkpoint before publishing, preserve each original atomic
    write, then call this once. Every selected sidecar identity and all complete
    atomic siblings, markers and physical bodies authenticate before consume.
    The existing plural owner checks the entire observed union before/after
    consume; an owned scope also checks it before its public return. No live
    plane or reusable proof is passed to consume. Custom hooks keep the original
    singular accesses before the closed callback. Metadata-first fault ordering
    differs from interleaved singular access; callers must select it explicitly.
    """
    from empirical_lawhood.runtime.artifacts import ArtifactWriteResult
    if not callable(consume):
        raise TypeError("publication consumption requires a callable")
    if type(publications) is not tuple or not publications:
        raise ValueError("publication consumption requires a nonempty closed tuple")
    if any(type(value) is not ArtifactWriteResult for value in publications):
        raise TypeError("publication access requires exact original write results")
    if plane.custody_limits.exceeds("publication_members", len(publications)):
        raise ValueError("publication consumption roster exceeds its bound")
    selected = {}
    for publication in publications:
        key = (publication.materialization.storage_root_id,
            publication.materialization.relative_path)
        if selected.setdefault(key, publication) != publication:
            raise ValueError("publication consumption aliases an exact selected member")
    if not supports_closed_publication_access(plane):
        # Invoke every original singular hook; custom policies are not silently
        # promoted into the stock batch. The existing plural owner still owns
        # callback/final guards, and a refusal never reaches consume.
        manifests = tuple(authenticate_published_materialization(plane, publication)
            for publication in publications)
        return plane.verify_manifests_members(manifests, validate_members=consume)
    publications = tuple(selected.values())

    def access(scoped):
        manifests = []
        for publication in publications:
            logical, physical = publication.logical, publication.materialization
            if (physical.storage_root_id != scoped.root.contract.storage_root_id
                    or physical.logical_artifact_id != logical.logical_artifact_id):
                raise ValueError("publication metadata changes its selected custody root or logical member")
            # Do not reopen every sibling roster for every selected handle.
            # Stock scoped read_manifest binds one actual publication owner;
            # the plural verifier below checks its complete sibling set once.
            actual = scoped.read_manifest(physical.relative_path,
                maximum_bytes=scoped.custody_limits.manifest_bytes)
            if actual.logical != logical or actual.materialization != physical or actual.publication is None:
                raise ValueError("publication metadata differs from its exact original declared sidecar")
            relative = physical.relative_path + ".manifest.json"
            raw = read_bounded_bytes(scoped.root.resolve(relative, for_write=False),
                maximum_bytes=scoped.custody_limits.manifest_bytes)
            expected = scoped._manifest_materialization(logical_artifact_id=logical.logical_artifact_id,
                relative_path=relative, payload=raw)
            if expected != publication.manifest_materialization:
                raise ValueError("publication access changes exact original manifest materialization")
            # read_manifest already retained the sidecar's exact snapshot.
            # The plural owner's final guards recheck it before returning.
            # Do not pass metadata to the raw-body access owner: in a guarded
            # scope that would look for a sidecar of this sidecar, instead of
            # invoking the actual member's current-access preflight below.
            manifests.append(actual)
        return scoped.verify_manifests_members(tuple(manifests), validate_members=consume)

    if type(plane) is ExternalArtifactPlane:
        with plane.verification_scope() as scoped:
            return access(scoped)
    return access(plane)
