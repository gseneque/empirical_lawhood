# SPDX-License-Identifier: MPL-2.0
"""Explicit chemical custody supply; original task and scientific IDs survive.

The original definition and chemical return legitimately share a unit ID but
have different schemas. This new supplier product binds their complete records;
it does not manufacture a fresh assessment or alter numerical admission.
"""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.runtime.native_subwork import NativeSubworkCompletion, NativeSubworkDefinition

from .control_contracts import ChemicalForceAssessment, ChemicalForceReturn
from .nve_preparation_admission import SerializedPreparationNVEControlPlan


@dataclass(frozen=True, slots=True)
class ChemicalForceCustodySupply(CanonicalRecord):
    """Original complete custody, including negative independent assessments."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-sampling/chemical-force-custody-supply"
    product_id: str
    definition: NativeSubworkDefinition
    completion_identity: ObjectIdentity
    completion: NativeSubworkCompletion
    returned: ChemicalForceReturn
    assessment: ChemicalForceAssessment

    def __post_init__(self):
        validate_stable_id(self.product_id)
        for record, kind in ((self.definition, NativeSubworkDefinition),
                (self.completion_identity, ObjectIdentity), (self.completion, NativeSubworkCompletion),
                (self.returned, ChemicalForceReturn), (self.assessment, ChemicalForceAssessment)):
            if type(record) is not kind:
                raise ValueError("chemical custody supply omits an exact original record")
            record.__post_init__()
        if (self.definition.operation_id != "rubisco.chemical-force.unit"
                or self.completion.definition != self.definition.identity
                or self.completion_identity != ObjectIdentity.from_record(
                    self.completion_identity.object_id, self.completion)
                or self.returned.unit_id != self.definition.subwork_id
                or self.returned.plan != self.definition.configuration
                or self.assessment.plan != self.definition.configuration
                or self.assessment.returned != self.returned.identity):
            raise ValueError("chemical custody supply substitutes its original definition/completion/return/assessment join")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.product_id, self)

    @property
    def model_id(self):
        return self.returned.unit_id.removeprefix("control.chemical-force.")

    @property
    def original_custody(self):
        return (self.model_id, self.definition, self.completion_identity,
            self.completion, self.returned, self.assessment)


@dataclass(frozen=True, slots=True, kw_only=True)
class SerializedCustodyNVEControlPlan(SerializedPreparationNVEControlPlan):
    """Named supplier projection; the original full 96/48 contracts are unchanged."""

    VERSION: ClassVar[str] = "1.2.0"
    chemical_custody_supplies: tuple[ChemicalForceCustodySupply, ...]

    def __post_init__(self):
        SerializedPreparationNVEControlPlan.__post_init__(self)
        if (not self.chemical_custody_supplies
                or any(type(row) is not ChemicalForceCustodySupply for row in self.chemical_custody_supplies)
                or tuple(row.model_id for row in self.chemical_custody_supplies)
                    != tuple(row[0] for row in self.admitted_parents)):
            raise ValueError("named NVE custody plan omits its exact original parent denominator")
        for supply, parent in zip(self.chemical_custody_supplies, self.admitted_parents, strict=True):
            supply.__post_init__()
            if (parent[2:] != (supply.definition.identity, supply.completion_identity,
                    supply.returned.identity, ObjectIdentity.from_record(supply.assessment.product_id, supply.assessment))
                    or supply.definition.configuration != self.chemical_controls.identity):
                raise ValueError("named NVE custody plan substitutes its original assessed parent identities")
        sources = self.custody_source_identities
        if len({row.object_id for row in sources}) != len(sources):
            raise ValueError("named NVE custody suppliers need distinct legitimate source product IDs")

    @property
    def custody_source_identities(self):
        return tuple(sorted((self.chemical_controls.identity, self.chemical_controls.source,
            *(row[1] for row in self.admitted_parents),
            *(supply.identity for supply in self.chemical_custody_supplies)), key=lambda row: row.object_id))


def validate_direct_custody(plan, custody):
    """Join every unchanged direct native operand to its selected supplier product."""
    if type(plan) is SerializedCustodyNVEControlPlan:
        plan.__post_init__()
        if tuple(custody) != tuple(row.original_custody for row in plan.chemical_custody_supplies):
            raise ValueError("named NVE custody supply differs from complete direct original operands")


def source_projection(plan, legacy):
    """Select the named product route without changing historical default sources."""
    return set(plan.custody_source_identities) if type(plan) is SerializedCustodyNVEControlPlan else legacy
