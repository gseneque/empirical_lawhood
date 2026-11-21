# SPDX-License-Identifier: MPL-2.0
"""Explicit source selections for retained cross-programme comparison."""
from dataclasses import dataclass
from empirical_lawhood.science.identity.source_exports import IndependentSourceExport
from empirical_lawhood.science.models.worlds import WorldKind


@dataclass(frozen=True, slots=True)
class SourceMemberDefinition:
    artifact_id: str
    role_id: str
    locator: str
    source_export: IndependentSourceExport | None = None

    def __post_init__(self) -> None:
        if self.source_export is not None:
            if type(self.source_export) is not IndependentSourceExport:
                raise ValueError("post-hoc source requires its exact typed independent source export")
            if self.artifact_id != self.source_export.target_artifact.artifact_id or self.locator != self.source_export.target_relative_path:
                raise ValueError("post-hoc member differs from the exported current target artifact and path")



@dataclass(frozen=True, slots=True)
class ParentSourceDefinition:
    parent_id: str
    lane_id: str
    study_id: str
    target_id: str
    world_id: str
    world_kind: WorldKind
    independent_unit_id: str
    members: tuple[SourceMemberDefinition, ...]
    role_ids: tuple[str, ...]
    analysis_ids: tuple[str, ...]
    expected_unit_count: int | None = None
    eligibility_reason_codes: tuple[str, ...] = ()



def _member(artifact_id: str, role_id: str, locator: str) -> SourceMemberDefinition:
    return SourceMemberDefinition(artifact_id, role_id, locator)



def _parent(
    parent_id: str,
    lane_id: str,
    study_id: str,
    target_id: str,
    members: tuple[SourceMemberDefinition, ...],
    *,
    roles: tuple[str, ...],
    analyses: tuple[str, ...],
    units: int | None = None,
    world_kind: WorldKind = WorldKind.NUMERICAL_SIMULATOR,
    reasons: tuple[str, ...] = (),
) -> ParentSourceDefinition:
    return ParentSourceDefinition(
        parent_id=parent_id,
        lane_id=lane_id,
        study_id=study_id,
        target_id=target_id,
        world_id=f"world.{parent_id}",
        world_kind=world_kind,
        independent_unit_id=f"unit.{parent_id}",
        members=members,
        role_ids=tuple(sorted(roles)),
        analysis_ids=tuple(sorted(analyses)),
        expected_unit_count=units,
        eligibility_reason_codes=tuple(sorted(reasons)),
    )

