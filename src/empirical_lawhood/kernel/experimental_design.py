# SPDX-License-Identifier: MPL-2.0
"""Immutable independent-unit allocations, separate from domain eligibility."""

from dataclasses import dataclass
from typing import ClassVar

from .provenance import ObjectIdentity
from .serialization import CanonicalRecord, validate_stable_id


@dataclass(frozen=True, slots=True)
class IndependentUnit(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/experimental-design/independent-unit"
    unit_id: str
    source_id: str
    family_id: str
    numerical_view_ids: tuple[str, ...]
    exposed: bool

    def __post_init__(self):
        for value in (self.unit_id, self.source_id, self.family_id):
            validate_stable_id(value)
        if (type(self.numerical_view_ids) is not tuple
                or self.numerical_view_ids != tuple(sorted(set(self.numerical_view_ids)))
                or type(self.exposed) is not bool):
            raise ValueError("independent unit needs exact unique nested views and exposure metadata")
        for value in self.numerical_view_ids:
            validate_stable_id(value)


@dataclass(frozen=True, slots=True)
class UnitRoleAssignment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/experimental-design/unit-role-assignment"
    unit_id: str
    role: str

    def __post_init__(self):
        validate_stable_id(self.unit_id)
        validate_stable_id(self.role)


@dataclass(frozen=True, slots=True)
class UnitAllocation(CanonicalRecord):
    """One complete roster; consumers refer to its identity rather than copy it.

    Domain validators authenticate source membership, exposure and comparability.
    Nested views never create additional independent units.
    """

    SCHEMA: ClassVar[str] = "empirical-lawhood/experimental-design/unit-allocation"
    allocation_id: str
    sources: tuple[ObjectIdentity, ...]
    units: tuple[IndependentUnit, ...]
    roles: tuple[UnitRoleAssignment, ...]

    def __post_init__(self):
        validate_stable_id(self.allocation_id)
        if (type(self.sources) is not tuple or not self.sources
                or any(type(source) is not ObjectIdentity for source in self.sources)
                or tuple(source.object_id for source in self.sources)
                != tuple(sorted({source.object_id for source in self.sources}))):
            raise ValueError("allocation needs sorted unique immutable source references")
        if (type(self.units) is not tuple or not self.units
                or any(type(unit) is not IndependentUnit for unit in self.units)
                or tuple(unit.unit_id for unit in self.units)
                != tuple(sorted({unit.unit_id for unit in self.units}))):
            raise ValueError("allocation needs a sorted unique independent-unit roster")
        source_ids = {source.object_id for source in self.sources}
        for unit in self.units:
            unit.__post_init__()
            if unit.source_id not in source_ids:
                raise ValueError("allocation unit lacks its exact source reference")
        if (type(self.roles) is not tuple
                or any(type(role) is not UnitRoleAssignment for role in self.roles)
                or tuple(role.unit_id for role in self.roles)
                != tuple(unit.unit_id for unit in self.units)):
            raise ValueError("allocation roles must cover every unit exactly once")
        for role in self.roles:
            role.__post_init__()

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.allocation_id, self)

    def unit_ids(self, role: str | None = None) -> tuple[str, ...]:
        return tuple(row.unit_id for row in self.roles if role is None or row.role == role)

    def unit(self, unit_id: str) -> IndependentUnit | None:
        """Find a unit in the canonical sorted roster without rebuilding an index."""
        left, right = 0, len(self.units)
        while left < right:
            middle = (left + right) // 2
            candidate = self.units[middle]
            if candidate.unit_id < unit_id:
                left = middle + 1
            elif candidate.unit_id > unit_id:
                right = middle
            else:
                return candidate
        return None

    @property
    def role_counts(self) -> tuple[tuple[str, int], ...]:
        return tuple((role, sum(row.role == role for row in self.roles))
                     for role in sorted({row.role for row in self.roles}))


def require_disjoint_allocations(*allocations: UnitAllocation) -> None:
    """Reject reused unit identities; physical/seed compatibility is domain-owned."""
    seen: set[str] = set()
    for allocation in allocations:
        allocation.__post_init__()
        ids = set(allocation.unit_ids())
        if seen.intersection(ids):
            raise ValueError("independent-unit allocations overlap")
        seen.update(ids)
