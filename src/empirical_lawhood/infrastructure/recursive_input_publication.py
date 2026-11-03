# SPDX-License-Identifier: MPL-2.0
"""Bounded publication of recursive configuration and input metadata."""

from hashlib import sha256

from empirical_lawhood.runtime.artifacts import (
    ArtifactProfile, ArtifactPublicationScope, ArtifactStreamWriteRequest, ArtifactWriteRequest, ArtifactWriteResult,
    artifact_publication_intent_relative_path,
)

from .artifacts import ArtifactIdentityConflict, supports_closed_batch_writes
from .bounded_io import read_bounded_bytes


def _size(request):
    return len(request.payload) if type(request) is ArtifactWriteRequest else request.expected_size_bytes


def _groups(plane, requests, group_member):
    """Use small closed publications without increasing any selected bound."""
    limits = plane.custody_limits
    count = min(64, limits.publication_members or 64)
    size = min(4 * 1024**2, limits.publication_aggregate_bytes or 4 * 1024**2,
        limits.in_memory_payload_bytes or 4 * 1024**2)
    pending, total, selected = [], 0, None
    for request in requests:
        if type(request) not in (ArtifactWriteRequest, ArtifactStreamWriteRequest):
            raise TypeError('recursive publication requires exact artifact requests')
        amount = len(request.payload) if type(request) is ArtifactWriteRequest else request.maximum_bytes
        key = (request.publication_scope_id, request.publication_scope_relative_root,
            request.outcome_access, request.visibility_ceiling)
        bounded = ((group_member is None or group_member(request))
            and request.profile is ArtifactProfile.CANONICAL_JSON and _size(request) is not None
            and amount <= size and (type(request) is ArtifactWriteRequest
                or request.expected_physical_sha256 is not None))
        if pending and (not bounded or key != selected or len(pending) >= count or total + amount > size):
            yield tuple(pending)
            pending, total = [], 0
        if not bounded:
            yield (request,)
        else:
            pending.append(request)
            total += amount
            selected = key
    if pending:
        yield tuple(pending)


def _existing(plane, request, *, before_member):
    """Retain an older complete publication without changing its member set."""
    plane._validate_publication_request(request)
    manifest = plane.read_manifest(request.relative_path)
    size = _size(request)
    declared = len(request.payload) if type(request) is ArtifactWriteRequest else request.maximum_bytes
    if plane.custody_limits.exceeds('publication_aggregate_bytes', declared):
        raise ArtifactIdentityConflict('recursive input exceeds its selected publication byte bound')
    scope = ArtifactPublicationScope(request.publication_scope_id, plane.root.contract.storage_root_id,
        request.publication_scope_relative_root, request.visibility_ceiling, request.outcome_access)
    digest = (sha256(request.payload).hexdigest() if type(request) is ArtifactWriteRequest
        else request.expected_physical_sha256)
    logical, material, _, _ = plane._prepare_identity(request, physical_sha256=digest, size_bytes=size)
    if (manifest.logical != logical or manifest.materialization != material
            or manifest.publication is None or manifest.publication.publication_scope != scope):
        raise ArtifactIdentityConflict('recursive input changes its original publication contract')
    plane.verify_manifest(manifest, **({} if before_member is None else {'before_member': before_member}))
    path = plane.root.resolve(request.relative_path, for_write=False)
    if type(request) is ArtifactWriteRequest:
        if not plane._file_equals(path, request.payload):
            raise ArtifactIdentityConflict('recursive input changes its original exact bytes')
    else:
        plane._require_replayed_stream(request, material, path)
    relative = request.relative_path + '.manifest.json'
    raw = read_bounded_bytes(plane.root.resolve(relative, for_write=False),
        maximum_bytes=plane.custody_limits.manifest_bytes)
    sidecar = plane._manifest_materialization(logical_artifact_id=logical.logical_artifact_id,
        relative_path=relative, payload=raw)
    return ArtifactWriteResult(logical, material, sidecar, False)


def publish_recursive_metadata(plane, requests, *, require_current, before_member=None, group_member=None):
    """Publish bounded canonical groups through the ordinary immutable owner.

    Binary/large streams and customized writers keep their individual route.
    Existing groups and original singletons keep their exact member contracts.
    The ordinary intent/commit owner resumes an interrupted matching group.
    Each group retains current access before publication and on return/refusal.
    """
    if not callable(require_current) or before_member is not None and not callable(before_member):
        raise TypeError('recursive metadata requires its current custody callbacks')
    if group_member is not None and not callable(group_member):
        raise TypeError('recursive metadata grouping requires a callable member selection')

    def single(request):
        return (plane.write(request) if type(request) is ArtifactWriteRequest
            else plane.write_stream(request))

    def present(request):
        return any(plane.root.resolve(path, for_write=False).exists() for path in (
            request.relative_path, request.relative_path + '.manifest.json'))

    if not supports_closed_batch_writes(plane):
        results = []
        for request in requests:
            require_current()
            try:
                results.append(single(request))
            finally:
                require_current()
        return tuple(results)

    results = []
    for group in _groups(plane, requests, group_member):
        require_current()
        try:
            if len(group) == 1:
                request = group[0]
                pinned = (_size(request) is not None and (type(request) is ArtifactWriteRequest
                    or request.expected_physical_sha256 is not None))
                # A changed operational group bound does not dissolve a
                # previously complete publication into singleton records.
                if pinned and present(request):
                    sidecar = plane.root.resolve(request.relative_path + '.manifest.json', for_write=False)
                    if sidecar.exists():
                        from .artifact_sidecars import decode_artifact_sidecar
                        from empirical_lawhood.runtime.artifact_sidecar import ArtifactManifestReference
                        stored = decode_artifact_sidecar(read_bounded_bytes(sidecar,
                            maximum_bytes=plane.custody_limits.manifest_bytes),
                            maximum_bytes=plane.custody_limits.manifest_bytes)
                        marker = (stored.commit_marker_relative_path if type(stored) is ArtifactManifestReference
                            else None if stored.publication is None else stored.publication.commit_marker_relative_path)
                        if marker is not None and plane.root.resolve(marker, for_write=False).exists():
                            results.append(_existing(plane, request, before_member=before_member))
                            continue
                results.append(single(request))
                continue
            # The same bounded preflight computes the exact interrupted roster.
            # It supplies no authority and stages no bytes.
            preflight = plane._preflight_publication(group, compact_manifests=True)
            publication = preflight.publication
            intent = artifact_publication_intent_relative_path(
                publication.publication_scope, publication.publication_batch_id)
            selected = (publication.commit_marker_relative_path, intent)
            existing_group = any(plane.root.resolve(path, for_write=False).exists() for path in selected)
            retained = tuple(present(request) for request in group)
            if existing_group or not any(retained):
                results.extend(plane.write_compact_batch(group))
            else:
                # Never regroup an old committed singleton or atomic sibling.
                # The read checks the complete old publications before return.
                for request, exists in zip(group, retained, strict=True):
                    require_current()
                    results.append(_existing(plane, request, before_member=before_member)
                        if exists else single(request))
        finally:
            require_current()
    return tuple(results)
