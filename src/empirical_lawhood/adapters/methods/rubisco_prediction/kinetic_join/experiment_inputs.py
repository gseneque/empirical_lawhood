# SPDX-License-Identifier: MPL-2.0
"""Closed original source bindings; selected gas actions belong to the spec."""

from collections.abc import Mapping
from dataclasses import dataclass

from empirical_lawhood.adapters.simulators.rubisco_assay.records import AssayQuery
from empirical_lawhood.kernel.experimental_design import IndependentUnit, UnitAllocation, UnitRoleAssignment
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.planning.campaigns import CampaignSpec
from empirical_lawhood.runtime.experiment_preparation import PreparedExperimentInputs

from ..kinetic_supply import JointKineticSupply, KineticTargetComparison
from .disclosed_examples import DisclosedAssumption
from .experiment_specification import RubiscoKineticExperimentSpecification
from .operation_bindings import UNIT


INPUT_TYPES = {"campaign": CampaignSpec, "material": DisclosedAssumption,
    "supply": JointKineticSupply, "query": AssayQuery, "comparison": KineticTargetComparison}


@dataclass(frozen=True, slots=True)
class KineticExperimentInputs:
    """A partial typed handle keeps every missing source visible to preparation."""

    campaign: CampaignSpec | None = None
    material: DisclosedAssumption | None = None
    supply: JointKineticSupply | None = None
    query: AssayQuery | None = None
    comparison: KineticTargetComparison | None = None

    def __post_init__(self):
        for key, kind in INPUT_TYPES.items():
            record = getattr(self, key)
            if record is not None:
                if type(record) is not kind:
                    raise TypeError("kinetic experiment input " + key + " has the wrong closed record type")
                record.__post_init__()


def source_allocation(supply):
    """One already exposed analytical unit; members are nested scenarios."""
    source = ObjectIdentity.from_record(supply.supply_id, supply)
    return UnitAllocation("allocation.rubisco-kinetic-source." + supply.fingerprint(), (source,),
        (IndependentUnit(UNIT, source.object_id, "rubisco.conditional-supplied-kinetics",
            ("conditional-numerical",), True),), (UnitRoleAssignment(UNIT, "analytical"),))


def input_record_types() -> tuple[type[CanonicalRecord], ...]:
    return tuple(INPUT_TYPES.values())


def bind_kinetic_experiment_inputs(specification, records) -> PreparedExperimentInputs:
    """Bind byte-checked records without numerical execution or source admission."""
    if type(specification) is not RubiscoKineticExperimentSpecification:
        raise TypeError("kinetic input binding requires its exact specification")
    specification.__post_init__()
    if not isinstance(records, Mapping):
        raise TypeError("kinetic input binding requires keyed canonical source records")
    unknown = set(records) - set(INPUT_TYPES)
    if unknown:
        raise ValueError("kinetic input binding includes unknown keys: " + ", ".join(sorted(unknown)))
    inputs = KineticExperimentInputs(**records)
    allocations = {} if inputs.supply is None else {"supply": source_allocation(inputs.supply)}
    return PreparedExperimentInputs(allocations, inputs)
