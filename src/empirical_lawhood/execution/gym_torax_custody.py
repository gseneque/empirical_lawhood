"""Reusable scientific contracts and calculations; native effects are owned by the adapter."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, TypeVar
from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_strings, validate_relative_locator, validate_stable_id
from empirical_lawhood.storage.contracts.artifacts import ArtifactLineageParent

_RecordT = TypeVar("_RecordT", bound=CanonicalRecord)

@dataclass(frozen=True, slots=True)
class GymToraxArtifactPublicationItem:
    logical_artifact_id: str
    relative_path: str
    record: CanonicalRecord
    visibility_ceiling: VisibilityCeiling
    outcome_access: OutcomeAccess
    lineage_parents: tuple[ArtifactLineageParent, ...]

    def __post_init__(self) -> None:
        validate_stable_id(self.logical_artifact_id, field_name="logical_artifact_id")
        validate_relative_locator(self.relative_path)
        require_sorted_unique_strings(
            tuple(value.identity.object_id for value in self.lineage_parents),
            field_name="lineage_parents",
        )

class GymToraxBoundedArtifactStore(Protocol):
    """Exact no-replace canonical artifact port; implementations may not scan."""

    @property
    def storage_root_id(self) -> str: ...

    def publish_atomic(
        self,
        *,
        publication_scope_id: str,
        publication_scope_relative_root: str,
        implementation_sha256: str,
        items: tuple[GymToraxArtifactPublicationItem, ...],
    ) -> tuple[ObjectIdentity, ...]: ...

    def load_optional(
        self,
        *,
        logical_artifact_id: str,
        relative_path: str,
        record_type: type[_RecordT],
        maximum_bytes: int,
    ) -> _RecordT | None: ...
