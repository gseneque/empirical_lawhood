# SPDX-License-Identifier: MPL-2.0
"""Declared matched observations, parameter grids and reservation references.

UnitAllocation remains the independent-unit roster owner. These records describe
comparisons and exact byte references; they supply no comparability, source
freshness, physical-regime, noise, chronology or scientific authority warrant.
"""

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import ClassVar

from .experimental_design import UnitAllocation
from .provenance import ObjectIdentity
from .references import ArtifactIdentity
from .serialization import CanonicalRecord, validate_stable_id


CoordinateScalar = str | int | Decimal


def _names(values, field):
    if type(values) is not tuple or not values or values != tuple(sorted(set(values))):
        raise ValueError(field + " requires sorted unique declared names")
    for value in values:
        if type(value) is not str:
            raise TypeError(field + " requires exact strings")
        validate_stable_id(value)


@dataclass(frozen=True, slots=True)
class MatchedCoordinate(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/experimental-design/matched-coordinate"
    unit_id: str
    arm_id: str
    source_record: ObjectIdentity
    values: tuple[tuple[str, CoordinateScalar], ...]

    def __post_init__(self):
        validate_stable_id(self.unit_id)
        validate_stable_id(self.arm_id)
        if type(self.source_record) is not ObjectIdentity:
            raise TypeError("matched coordinate requires its original immutable source record")
        self.source_record.__post_init__()
        if (type(self.values) is not tuple or not self.values
                or any(type(row) is not tuple or len(row) != 2 for row in self.values)):
            raise ValueError("matched coordinate requires exact named scalar values")
        _names(tuple(name for name, _ in self.values), "matched coordinate values")
        for _, value in self.values:
            if type(value) not in (str, int, Decimal):
                raise TypeError("matched values require exact str, int or finite Decimal; bool/float are forbidden")
            if type(value) is Decimal and not value.is_finite():
                raise ValueError("matched Decimal values must be finite")


@dataclass(frozen=True, slots=True)
class MatchedArmDesign(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/experimental-design/matched-arm-design"
    design_id: str
    allocation: ObjectIdentity
    arm_ids: tuple[str, ...]
    coordinate_names: tuple[str, ...]
    varying_coordinate_names: tuple[str, ...]
    coordinates: tuple[MatchedCoordinate, ...]

    def __post_init__(self):
        validate_stable_id(self.design_id)
        if type(self.allocation) is not ObjectIdentity or self.allocation.object_schema != UnitAllocation.SCHEMA:
            raise ValueError("matched design requires the original whole-unit allocation reference")
        self.allocation.__post_init__()
        _names(self.arm_ids, "matched arms")
        _names(self.coordinate_names, "matched coordinate names")
        if self.varying_coordinate_names:
            _names(self.varying_coordinate_names, "declared varying coordinates")
        elif type(self.varying_coordinate_names) is not tuple:
            raise TypeError("declared varying coordinates must be an exact tuple")
        if not set(self.varying_coordinate_names) <= set(self.coordinate_names):
            raise ValueError("matched design varies an undeclared coordinate")
        if (type(self.coordinates) is not tuple or not self.coordinates
                or any(type(row) is not MatchedCoordinate for row in self.coordinates)):
            raise TypeError("matched design requires its exact observation coordinates")
        keys = tuple((row.unit_id, row.arm_id) for row in self.coordinates)
        if keys != tuple(sorted(set(keys))):
            raise ValueError("matched coordinates duplicate or reorder a whole-unit/arm cell")
        for row in self.coordinates:
            row.__post_init__()
            if row.arm_id not in self.arm_ids or tuple(name for name, _ in row.values) != self.coordinate_names:
                raise ValueError("matched coordinate changes its complete declared arm/value census")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.design_id, self)


class ParameterAxisScale(StrEnum):
    LINEAR = "LINEAR"
    LOG = "LOG"


@dataclass(frozen=True, slots=True)
class ParameterGridAxis(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/experimental-design/parameter-grid-axis"
    axis_id: str
    levels: tuple[Decimal, Decimal, Decimal]
    scale: ParameterAxisScale

    def __post_init__(self):
        validate_stable_id(self.axis_id)
        if (type(self.levels) is not tuple or len(self.levels) != 3
                or any(type(value) is not Decimal or not value.is_finite() for value in self.levels)
                or not self.levels[0] < self.levels[1] < self.levels[2]
                or type(self.scale) is not ParameterAxisScale):
            raise ValueError("parameter axis requires exact finite ordered low/center/high levels and declared scale")
        if self.scale is ParameterAxisScale.LOG and self.levels[0] <= 0:
            raise ValueError("log parameter levels must be positive")


@dataclass(frozen=True, slots=True)
class ParameterGridSetting(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/experimental-design/parameter-grid-setting"
    setting_id: str
    values: tuple[Decimal, ...]

    def __post_init__(self):
        validate_stable_id(self.setting_id)
        if (type(self.values) is not tuple or not self.values
                or any(type(value) is not Decimal or not value.is_finite() for value in self.values)):
            raise ValueError("parameter setting requires exact finite Decimal coordinates")


@dataclass(frozen=True, slots=True)
class ParameterGrid(CanonicalRecord):
    """Ordered axes determine coordinate meaning; settings are nested cases."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/experimental-design/parameter-grid"
    grid_id: str
    axes: tuple[ParameterGridAxis, ...]
    settings: tuple[ParameterGridSetting, ...]

    def __post_init__(self):
        validate_stable_id(self.grid_id)
        if (type(self.axes) is not tuple or not self.axes
                or any(type(axis) is not ParameterGridAxis for axis in self.axes)
                or len({axis.axis_id for axis in self.axes}) != len(self.axes)):
            raise ValueError("parameter grid requires its distinct ordered declared axes")
        for axis in self.axes:
            axis.__post_init__()
        if (type(self.settings) is not tuple or not self.settings
                or any(type(setting) is not ParameterGridSetting for setting in self.settings)
                or tuple(setting.setting_id for setting in self.settings)
                != tuple(sorted({setting.setting_id for setting in self.settings}))):
            raise ValueError("parameter grid requires sorted unique setting identities")
        for setting in self.settings:
            setting.__post_init__()
            if len(setting.values) != len(self.axes):
                raise ValueError("parameter setting changes the full ordered axis census")


@dataclass(frozen=True, slots=True)
class PopulationReservationBinding(CanonicalRecord):
    """An original publication reference; actual pre-fit custody remains required."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/experimental-design/population-reservation-binding"
    reservation_id: str
    allocation: ObjectIdentity
    source_allocation: ObjectIdentity
    source_id_field: str
    publication: ArtifactIdentity
    materialization_id: str
    protected_roles: tuple[str, ...]

    def __post_init__(self):
        for value in (self.reservation_id, self.source_id_field, self.materialization_id):
            validate_stable_id(value)
        if (type(self.allocation) is not ObjectIdentity or self.allocation.object_schema != UnitAllocation.SCHEMA
                or type(self.source_allocation) is not ObjectIdentity or type(self.publication) is not ArtifactIdentity):
            raise TypeError("reservation requires exact allocation, original source and publication references")
        self.allocation.__post_init__()
        self.source_allocation.__post_init__()
        self.publication.__post_init__()
        if (self.publication.payload_schema != self.source_allocation.object_schema
                or self.publication.sha256 != self.source_allocation.object_fingerprint
                or self.publication.media_type != "application/json" or type(self.publication.size_bytes) is not int):
            raise ValueError("reservation publication must bind the original canonical source allocation")
        _names(self.protected_roles, "protected reservation roles")
