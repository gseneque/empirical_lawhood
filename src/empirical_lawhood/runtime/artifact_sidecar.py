# SPDX-License-Identifier: MPL-2.0
"""Compact physical sidecar metadata; existing scientific records stay exact."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_sha256, validate_stable_id

from .artifacts import (
    ArtifactManifest, ArtifactMaterialization, ArtifactPublicationBinding,
    ArtifactPublicationScope, LogicalArtifactIdentity, artifact_publication_commit_relative_path,
)


@dataclass(frozen=True, slots=True)
class ArtifactManifestReference(CanonicalRecord):
    """Physical representation referring to one exact existing batch commit.

    Resolution against a supplied binding checks data joins only. The custody
    owner must authenticate actual commit/member bytes and required semantics.
    """

    SCHEMA: ClassVar[str] = "empirical-lawhood/runtime/artifact-manifest-reference"

    logical: LogicalArtifactIdentity
    materialization: ArtifactMaterialization
    publication_batch_id: str
    publication_scope: ArtifactPublicationScope
    commit_marker_relative_path: str
    commit_marker_sha256: str
    commit_marker_size_bytes: int

    def __post_init__(self) -> None:
        if (type(self.logical) is not LogicalArtifactIdentity
                or type(self.materialization) is not ArtifactMaterialization
                or type(self.publication_scope) is not ArtifactPublicationScope):
            raise TypeError("sidecar reference requires exact logical, physical and scope records")
        ArtifactManifest(self.logical, self.materialization)
        validate_stable_id(self.publication_batch_id, field_name="publication_batch_id")
        validate_sha256(self.commit_marker_sha256, field_name="commit_marker_sha256")
        if type(self.commit_marker_size_bytes) is not int or self.commit_marker_size_bytes <= 0:
            raise ValueError("sidecar reference commit size must be a positive integer")
        if self.commit_marker_relative_path != artifact_publication_commit_relative_path(
            self.publication_scope, self.publication_batch_id,
        ):
            raise ValueError("sidecar reference commit path is not batch-derived")
        if (self.materialization.storage_root_id != self.publication_scope.storage_root_id
                or not self.publication_scope.contains(self.materialization.relative_path)
                or self.logical.visibility_ceiling is not self.publication_scope.visibility_ceiling
                or self.logical.outcome_access is not self.publication_scope.outcome_access):
            raise ValueError("sidecar reference member differs from its publication scope")

    @classmethod
    def from_manifest(cls, manifest: ArtifactManifest) -> ArtifactManifestReference:
        if type(manifest) is not ArtifactManifest or type(manifest.publication) is not ArtifactPublicationBinding:
            raise TypeError("sidecar reference requires an existing publication-bound manifest")
        publication = manifest.publication
        return cls(manifest.logical, manifest.materialization,
            publication.publication_batch_id, publication.publication_scope,
            publication.commit_marker_relative_path, publication.commit_marker_sha256,
            publication.commit_marker_size_bytes)

    def resolve(self, publication: ArtifactPublicationBinding) -> ArtifactManifest:
        """Require the exact binding and existing manifest membership checks."""
        if type(publication) is not ArtifactPublicationBinding:
            raise TypeError("sidecar reference requires an exact publication binding")
        if (self.publication_batch_id, self.publication_scope, self.commit_marker_relative_path,
                self.commit_marker_sha256, self.commit_marker_size_bytes) != (
                publication.publication_batch_id, publication.publication_scope,
                publication.commit_marker_relative_path, publication.commit_marker_sha256,
                publication.commit_marker_size_bytes):
            raise ValueError("sidecar reference differs from its exact publication binding")
        return ArtifactManifest(self.logical, self.materialization, publication)
