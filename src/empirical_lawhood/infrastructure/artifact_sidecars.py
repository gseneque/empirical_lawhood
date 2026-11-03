# SPDX-License-Identifier: MPL-2.0
"""Physical sidecar codecs and bounded commit metadata resolution.

Pure decoders never perform I/O. Compact reads authenticate the actual commit;
member payload verification and access/authority remain with existing owners.
"""

from __future__ import annotations

from hashlib import sha256
from typing import TYPE_CHECKING

from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.serialization import CanonicalizationError
from empirical_lawhood.runtime.artifact_sidecar import ArtifactManifestReference
from empirical_lawhood.runtime.artifacts import (
    ArtifactManifest, ArtifactMaterialization, ArtifactPublicationBinding,
    ArtifactPublicationCommit, LogicalArtifactIdentity, artifact_custody_limits,
)

from .artifact_stream_primitives import ArtifactIdentityConflict
from .bounded_io import BoundedFileIOError, read_bounded_bytes

if TYPE_CHECKING:
    from .artifacts import ExternalArtifactPlane


def encode_artifact_manifest_reference(
    logical: LogicalArtifactIdentity,
    materialization: ArtifactMaterialization,
    publication: ArtifactPublicationBinding,
) -> bytes:
    return ArtifactManifestReference.from_manifest(
        ArtifactManifest(logical, materialization, publication)
    ).canonical_bytes()


def decode_artifact_sidecar(
    payload: bytes,
    *,
    maximum_bytes: int | None = None,
    publication: ArtifactPublicationBinding | None = None,
) -> ArtifactManifest | ArtifactManifestReference:
    """Decode exact transport bytes; a supplied binding resolves data only."""
    if not isinstance(payload, bytes):
        raise CanonicalizationError("artifact sidecar must be immutable bytes")
    if maximum_bytes is not None and len(payload) > maximum_bytes:
        raise CanonicalizationError("artifact sidecar exceeds its byte limit")
    if publication is not None and type(publication) is not ArtifactPublicationBinding:
        raise TypeError("artifact sidecar requires an exact publication binding")
    prefix = b'{"schema":"' + ArtifactManifestReference.SCHEMA.encode("ascii") + b'",'
    if not payload.startswith(prefix):
        # The legacy receipt store composes the plane; keep that import out of
        # the plane's own module initialization path.
        from .task_receipts import decode_artifact_manifest

        return decode_artifact_manifest(payload, maximum_bytes=maximum_bytes, publication=publication)
    reference = decode_canonical_bytes(payload, ArtifactManifestReference, maximum_bytes=maximum_bytes)
    return reference if publication is None else reference.resolve(publication)


def resolve_artifact_manifest_reference(
    plane: ExternalArtifactPlane,
    reference: ArtifactManifestReference,
) -> ArtifactManifest:
    """Read the exact bounded commit; never open any member payload."""
    if type(reference) is not ArtifactManifestReference:
        raise TypeError("commit resolution requires an exact sidecar reference")
    limits = artifact_custody_limits(plane)
    if reference.publication_scope.storage_root_id != plane.root.contract.storage_root_id:
        raise ArtifactIdentityConflict("sidecar reference belongs to another guarded storage root")
    if limits.exceeds("publication_marker_bytes", reference.commit_marker_size_bytes):
        raise ArtifactIdentityConflict("sidecar reference commit exceeds its selected byte bound")
    try:
        path = plane.root.resolve(reference.commit_marker_relative_path, for_write=False)
        raw = read_bounded_bytes(path, maximum_bytes=reference.commit_marker_size_bytes)
        if (len(raw) != reference.commit_marker_size_bytes
                or sha256(raw).hexdigest() != reference.commit_marker_sha256):
            raise ArtifactIdentityConflict("sidecar reference commit bytes differ from its exact pin")
        commit = decode_canonical_bytes(raw, ArtifactPublicationCommit,
            maximum_bytes=reference.commit_marker_size_bytes)
        if limits.exceeds("publication_members", len(commit.members)):
            raise ArtifactIdentityConflict("sidecar reference commit exceeds its selected member bound")
        publication = ArtifactPublicationBinding(commit.publication_batch_id, commit.publication_scope,
            reference.commit_marker_relative_path, reference.commit_marker_sha256,
            reference.commit_marker_size_bytes, commit.members)
        return reference.resolve(publication)
    except (BoundedFileIOError, OSError, ValueError) as error:
        raise ArtifactIdentityConflict("sidecar reference lacks its exact canonical durable commit") from error


def read_artifact_sidecar(
    plane: ExternalArtifactPlane,
    sidecar_relative_path: str,
    *,
    maximum_bytes: int | None = None,
) -> ArtifactManifest:
    """Read guarded metadata; resolve compact commit pins before returning.

    Legacy sidecars retain their existing strict decode semantics. Neither form
    proves payload custody, scientific qualification or authority to access it.
    """
    limits = artifact_custody_limits(plane)
    ceilings = tuple(value for value in (maximum_bytes, limits.manifest_bytes) if value is not None)
    ceiling = min(ceilings) if ceilings else None
    try:
        raw = read_bounded_bytes(plane.root.resolve(sidecar_relative_path, for_write=False),
            maximum_bytes=ceiling)
        decoded = decode_artifact_sidecar(raw, maximum_bytes=ceiling)
        if sidecar_relative_path != decoded.materialization.relative_path + ".manifest.json":
            raise ArtifactIdentityConflict("artifact sidecar differs from its actual member path")
        if type(decoded) is ArtifactManifestReference:
            return resolve_artifact_manifest_reference(plane, decoded)
        return decoded
    except (BoundedFileIOError, OSError, ValueError) as error:
        raise ArtifactIdentityConflict("artifact sidecar metadata is invalid") from error
