# SPDX-License-Identifier: MPL-2.0
"""Additive saved-episode reliability contracts, with no selected grid criterion.

The receiver must supply demanded and actually delivered interval energy in
MWh. Neither a reward nor topology/thermal observations can fill that receiver.
Source references and declared chronology remain evidence to authenticate;
these records confer no acquisition, qualification or operating authority.
"""

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord, require_sorted_unique_strings, validate_decimal,
    validate_nonempty, validate_stable_id,
)

from .contracts import Grid2OpChronicBinding, Grid2OpNativeStep, Grid2OpSourceBinding


def _identity(value, kind=None):
    if type(value) is not ObjectIdentity:
        raise TypeError("grid reliability requires exact immutable source identities")
    value.__post_init__()
    if kind is not None and (value.object_schema, value.object_version) != (kind.SCHEMA, kind.VERSION):
        raise ValueError("grid reliability source type or revision differs")


def _ids(values, name, *, empty=False):
    if type(values) is not tuple:
        raise TypeError(name + " must be an exact tuple")
    require_sorted_unique_strings(values, field_name=name, allow_empty=empty)
    for value in values:
        validate_stable_id(value, field_name=name)


def _reasons(values):
    if type(values) is not tuple:
        raise TypeError("grid reason codes require an exact tuple")
    require_sorted_unique_strings(values, field_name="grid reason codes")


@dataclass(frozen=True, slots=True)
class GridDeliveredEnergyReceiver(CanonicalRecord):
    """An explicitly sourced interval-total receiver; no proxy is inferred."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/simulators/grid2op-response/delivered-energy-receiver"
    receiver_id: str
    source_binding: ObjectIdentity
    definition_source: ObjectIdentity
    terminal_semantics_source: ObjectIdentity
    description: str
    energy_unit: str = "MWh"
    interval_semantics: str = "DEMANDED_AND_ACTUALLY_DELIVERED_INTERVAL_TOTALS"

    def __post_init__(self):
        validate_stable_id(self.receiver_id)
        _identity(self.source_binding, Grid2OpSourceBinding)
        _identity(self.definition_source)
        _identity(self.terminal_semantics_source)
        validate_nonempty(self.description, field_name="receiver description")
        if (self.energy_unit != "MWh"
                or self.interval_semantics != "DEMANDED_AND_ACTUALLY_DELIVERED_INTERVAL_TOTALS"):
            raise ValueError("grid reliability requires explicit actual delivered interval energy in MWh")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.receiver_id, self)


@dataclass(frozen=True, slots=True)
class GridReliabilityRequirement(CanonicalRecord):
    """Caller-selected consequential limits, never supplied by this adapter."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/simulators/grid2op-response/reliability-requirement"
    requirement_id: str
    source_binding: ObjectIdentity
    criterion_source: ObjectIdentity
    receiver: ObjectIdentity
    maximum_unserved_energy_mwh: Decimal
    maximum_rho: Decimal
    maximum_thermal_violation_intervals: int
    require_complete_survival: bool

    def __post_init__(self):
        validate_stable_id(self.requirement_id)
        _identity(self.source_binding, Grid2OpSourceBinding)
        _identity(self.criterion_source)
        _identity(self.receiver, GridDeliveredEnergyReceiver)
        for name in ("maximum_unserved_energy_mwh", "maximum_rho"):
            validate_decimal(getattr(self, name), field_name=name, minimum=Decimal(0))
        if (type(self.maximum_thermal_violation_intervals) is not int
                or self.maximum_thermal_violation_intervals < 0
                or type(self.require_complete_survival) is not bool):
            raise ValueError("grid reliability limits need explicit interval counts and survival policy")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.requirement_id, self)


class GridEpisodeTermination(StrEnum):
    COMPLETED = "COMPLETED"
    PREMATURE_TERMINAL = "PREMATURE_TERMINAL"
    BACKEND_DIVERGENCE = "BACKEND_DIVERGENCE"
    REFUSED = "REFUSED"
    MISSING_OBSERVATION = "MISSING_OBSERVATION"
    NOT_ENTERED = "NOT_ENTERED"


class GridEpisodeRole(StrEnum):
    DEVELOPMENT = "DEVELOPMENT"
    ASSESSMENT = "ASSESSMENT"
    LATER_USE = "LATER_USE"
    REUSE = "REUSE"


@dataclass(frozen=True, slots=True)
class GridOperatingEpisodeContext(CanonicalRecord):
    """Whole chronic identity plus nested action/contingency and original order.

    Sequence numbers describe the selected original provenance record. The
    original chronology source must still be authenticated by its consumer.
    Changing a role or sequence does not establish fresh or qualified evidence.
    """

    SCHEMA: ClassVar[str] = "empirical-lawhood/simulators/grid2op-response/operating-episode-context"
    episode_id: str
    unit_id: str
    source_binding: ObjectIdentity
    chronic: ObjectIdentity
    receiver: ObjectIdentity
    branch_id: str
    contingency: ObjectIdentity
    role: GridEpisodeRole
    chronology_source: ObjectIdentity
    selection_sequence: int
    first_observation_sequence: int | None
    termination: GridEpisodeTermination
    reason_codes: tuple[str, ...]
    evidence_scope: str = "EXPOSED_SAVED_EPISODES_NONPROMOTABLE"

    def __post_init__(self):
        for name in ("episode_id", "unit_id", "branch_id"):
            validate_stable_id(getattr(self, name), field_name=name)
        _identity(self.source_binding, Grid2OpSourceBinding)
        _identity(self.chronic, Grid2OpChronicBinding)
        _identity(self.receiver, GridDeliveredEnergyReceiver)
        _identity(self.contingency)
        _identity(self.chronology_source)
        if self.unit_id != self.chronic.object_id:
            raise ValueError("one complete grid chronic stays one unit across reset/action/contingency views")
        if type(self.role) is not GridEpisodeRole or type(self.termination) is not GridEpisodeTermination:
            raise TypeError("grid operating episode needs explicit role and terminal semantics")
        if (type(self.selection_sequence) is not int or self.selection_sequence < 0
                or self.first_observation_sequence is not None and (
                    type(self.first_observation_sequence) is not int
                    or self.first_observation_sequence <= self.selection_sequence)):
            raise ValueError("grid episode selection must precede its original dependent observation")
        if (self.termination is GridEpisodeTermination.NOT_ENTERED and self.first_observation_sequence is not None
                or self.termination in (GridEpisodeTermination.COMPLETED, GridEpisodeTermination.PREMATURE_TERMINAL,
                    GridEpisodeTermination.BACKEND_DIVERGENCE) and self.first_observation_sequence is None):
            raise ValueError("grid episode entry status and original observation chronology differ")
        _reasons(self.reason_codes)
        if self.termination is not GridEpisodeTermination.COMPLETED and not self.reason_codes:
            raise ValueError("an incomplete grid episode requires retained original reasons")
        if self.evidence_scope != "EXPOSED_SAVED_EPISODES_NONPROMOTABLE":
            raise ValueError("saved grid episode inspection cannot relabel exposed evidence fresh")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.episode_id, self)


@dataclass(frozen=True, slots=True)
class GridServiceInterval(CanonicalRecord):
    """Actual energy and cost alongside the unchanged native observation."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/simulators/grid2op-response/service-interval"
    native_step: Grid2OpNativeStep
    duration_seconds: int
    demanded_energy_mwh: Decimal | None
    delivered_energy_mwh: Decimal | None
    redispatch_magnitude_mwh: Decimal | None
    curtailed_energy_mwh: Decimal | None
    runtime_seconds: Decimal | None
    forecast_available: bool
    supplier_refused: bool
    fallback_used: bool

    def __post_init__(self):
        if type(self.native_step) is not Grid2OpNativeStep:
            raise TypeError("grid service requires its exact existing native step observation")
        self.native_step.__post_init__()
        if type(self.duration_seconds) is not int or self.duration_seconds <= 0:
            raise ValueError("grid service interval needs its actual positive duration")
        for name in ("demanded_energy_mwh", "delivered_energy_mwh", "redispatch_magnitude_mwh",
                "curtailed_energy_mwh", "runtime_seconds"):
            value = getattr(self, name)
            if value is not None:
                validate_decimal(value, field_name=name, minimum=Decimal(0))
        if (self.demanded_energy_mwh is None) != (self.delivered_energy_mwh is None):
            raise ValueError("grid service requires paired demanded and delivered interval energy")
        if (self.delivered_energy_mwh is not None
                and self.delivered_energy_mwh > self.demanded_energy_mwh):
            raise ValueError("delivered load energy exceeds the matched demanded load energy")
        for name in ("forecast_available", "supplier_refused", "fallback_used"):
            if type(getattr(self, name)) is not bool:
                raise TypeError("grid service events require exact booleans")


@dataclass(frozen=True, slots=True)
class GridSavedOperatingEpisode(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/simulators/grid2op-response/saved-operating-episode"
    context: GridOperatingEpisodeContext
    intervals: tuple[GridServiceInterval, ...]

    def __post_init__(self):
        if type(self.context) is not GridOperatingEpisodeContext:
            raise TypeError("saved grid episode needs its exact complete-unit context")
        self.context.__post_init__()
        if (type(self.intervals) is not tuple
                or any(type(row) is not GridServiceInterval for row in self.intervals)):
            raise TypeError("saved grid episode intervals require exact original observations")
        for row in self.intervals:
            row.__post_init__()


class GridReliabilityDisposition(StrEnum):
    SATISFIED = "SATISFIED"
    FAILED = "FAILED"
    UNEVALUABLE = "UNEVALUABLE"


@dataclass(frozen=True, slots=True)
class GridEpisodeReliability(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/simulators/grid2op-response/episode-reliability"
    episode: ObjectIdentity | None
    unit_id: str
    branch_id: str
    requirement: ObjectIdentity
    observed_intervals: int
    expected_intervals: int
    demanded_energy_mwh: Decimal | None
    delivered_energy_mwh: Decimal | None
    unserved_energy_mwh: Decimal | None
    unserved_energy_lower_bound_mwh: Decimal
    redispatch_magnitude_mwh: Decimal | None
    curtailed_energy_mwh: Decimal | None
    runtime_seconds: Decimal | None
    thermal_violation_intervals: int
    illegal_action_intervals: int
    ambiguous_action_intervals: int
    unrealized_action_intervals: int
    unavailable_forecast_intervals: int
    supplier_refusal_intervals: int
    fallback_intervals: int
    termination: GridEpisodeTermination
    disposition: GridReliabilityDisposition
    reason_codes: tuple[str, ...]

    def __post_init__(self):
        if self.episode is not None:
            _identity(self.episode, GridOperatingEpisodeContext)
        _identity(self.requirement, GridReliabilityRequirement)
        for value in (self.unit_id, self.branch_id):
            validate_stable_id(value)
        for name in ("observed_intervals", "expected_intervals", "thermal_violation_intervals",
                "illegal_action_intervals", "ambiguous_action_intervals", "unrealized_action_intervals",
                "unavailable_forecast_intervals", "supplier_refusal_intervals", "fallback_intervals"):
            if type(getattr(self, name)) is not int or getattr(self, name) < 0:
                raise ValueError("grid reliability census needs exact nonnegative interval counts")
        if self.expected_intervals < 1 or self.observed_intervals > self.expected_intervals:
            raise ValueError("grid reliability report changes the full chronic interval denominator")
        for name in ("demanded_energy_mwh", "delivered_energy_mwh", "unserved_energy_mwh", "unserved_energy_lower_bound_mwh",
                "redispatch_magnitude_mwh", "curtailed_energy_mwh", "runtime_seconds"):
            if getattr(self, name) is not None:
                validate_decimal(getattr(self, name), field_name=name, minimum=Decimal(0))
        if self.unserved_energy_lower_bound_mwh is None:
            raise ValueError("grid reliability must retain observed unserved energy even when later receivers are missing")
        _reasons(self.reason_codes)
        if type(self.disposition) is not GridReliabilityDisposition or type(self.termination) is not GridEpisodeTermination:
            raise TypeError("grid reliability report requires explicit scientific and terminal dispositions")


@dataclass(frozen=True, slots=True)
class GridReliabilityPanel(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/simulators/grid2op-response/reliability-panel"
    panel_id: str
    source_binding: ObjectIdentity
    requirement: ObjectIdentity
    role: GridEpisodeRole
    planned_unit_ids: tuple[str, ...]
    branch_ids: tuple[str, ...]
    branches: tuple[GridEpisodeReliability, ...]
    unit_dispositions: tuple[tuple[str, GridReliabilityDisposition], ...]
    evidence_scope: str = "EXPOSED_SAVED_EPISODES_NONPROMOTABLE"

    def __post_init__(self):
        validate_stable_id(self.panel_id)
        _identity(self.source_binding, Grid2OpSourceBinding)
        _identity(self.requirement, GridReliabilityRequirement)
        _ids(self.planned_unit_ids, "planned chronic units")
        _ids(self.branch_ids, "nested grid branches")
        expected = tuple((unit, branch) for unit in self.planned_unit_ids for branch in self.branch_ids)
        if (type(self.branches) is not tuple or any(type(row) is not GridEpisodeReliability for row in self.branches)
                or tuple((row.unit_id, row.branch_id) for row in self.branches) != expected
                or any(row.requirement != self.requirement for row in self.branches)
                or type(self.unit_dispositions) is not tuple
                or tuple(unit for unit, _ in self.unit_dispositions) != self.planned_unit_ids
                or any(type(status) is not GridReliabilityDisposition for _, status in self.unit_dispositions)
                or type(self.role) is not GridEpisodeRole
                or self.evidence_scope != "EXPOSED_SAVED_EPISODES_NONPROMOTABLE"):
            raise ValueError("grid reliability panel must retain every whole chronic and nested branch")
        for row in self.branches:
            row.__post_init__()
        for unit, disposition in self.unit_dispositions:
            local = tuple(row.disposition for row in self.branches if row.unit_id == unit)
            expected_disposition = (GridReliabilityDisposition.FAILED if GridReliabilityDisposition.FAILED in local else
                GridReliabilityDisposition.UNEVALUABLE if GridReliabilityDisposition.UNEVALUABLE in local else
                GridReliabilityDisposition.SATISFIED)
            if disposition is not expected_disposition:
                raise ValueError("grid whole-unit disposition differs from its complete nested branch census")

    @property
    def independent_unit_count(self):
        return len(self.planned_unit_ids)

    @property
    def satisfied_unit_count(self):
        return sum(status is GridReliabilityDisposition.SATISFIED for _, status in self.unit_dispositions)
