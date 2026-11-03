# SPDX-License-Identifier: MPL-2.0
"""Explicit operational phase selections for current selected E5/E6 inputs."""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id


def _owner(family):
    if family == "OPPORTUNITY":
        from . import selected_opportunity_bindings
        return selected_opportunity_bindings
    if family == "PROTECTED":
        from . import selected_protected_bindings
        return selected_protected_bindings
    raise ValueError("Selected resources require an installed opportunity or protected phase family")


@dataclass(frozen=True, slots=True)
class MatrixSelectedOperationalResources(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/selected-operational-resources"
    record_id: str
    family: str
    phase_budgets: tuple[tuple[str, ResourceBudget], ...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        owner = _owner(self.family)
        if (type(self.phase_budgets) is not tuple
                or any(type(row) is not tuple or len(row) != 2 for row in self.phase_budgets)
                or tuple(phase for phase, _ in self.phase_budgets) != tuple(sorted(owner.PHASES))):
            raise ValueError("Selected resources must retain every installed phase exactly once")
        for phase, budget in self.phase_budgets:
            if type(budget) is not ResourceBudget:
                raise TypeError("Selected phase resources require the existing exact ResourceBudget")
            budget.__post_init__()
            required = (budget.cpu_cores, budget.gpu_devices)
            optional = (budget.memory_bytes, budget.wall_time_seconds, budget.source_scan_bytes, budget.output_bytes)
            if (any(type(value) is not int for value in required)
                    or any(value is not None and type(value) is not int for value in optional)):
                raise TypeError("Selected phase resource operands require exact integers or explicit unlimited values")
            if not owner.preparation.BUDGET.contains(budget):
                raise ValueError("Selected phase resources exceed the installed operation capability ceiling")

    @property
    def identity(self):
        from empirical_lawhood.kernel.provenance import ObjectIdentity
        return ObjectIdentity.from_record(self.record_id, self)

    def for_family(self, family):
        self.__post_init__()
        if self.family != family:
            raise ValueError("Selected resources belong to a different operation family")
        return dict(self.phase_budgets)


def selected_phase_budgets(resources, *, family):
    """Preserve old direct-call contracts; current public preparation requires a selection."""
    owner = _owner(family)
    if resources is None:
        return {phase: owner.preparation.BUDGET for phase in owner.PHASES}
    if type(resources) is not MatrixSelectedOperationalResources:
        raise TypeError("Select the exact operational phase-resource record")
    return resources.for_family(family)
