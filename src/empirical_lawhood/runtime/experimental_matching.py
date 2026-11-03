# SPDX-License-Identifier: MPL-2.0
"""Exact complete matched censuses, grids and original reservation-byte joins.

Domains authenticate the source projection, exposure, full physical regimes,
starting-state and noise construction. Exact scalar equality checks include the
type: integer 1 does not silently match Decimal(1). No method supplies an IID,
transfer-validity or authority warrant. Reservation chronology is established
by the registered pre-fit dependency/barrier path, never by this byte join alone.
"""

from dataclasses import dataclass, fields
from fractions import Fraction
from hashlib import sha256
from itertools import product

from empirical_lawhood.kernel.experimental_design import UnitAllocation
from empirical_lawhood.kernel.experimental_matching import (
    MatchedArmDesign, MatchedCoordinate, ParameterAxisScale, ParameterGrid, PopulationReservationBinding,
)
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.runtime.execution import WorkerInputKind, WorkerInputPort


@dataclass(frozen=True, slots=True)
class MatchedGroup:
    unit_id: str
    coordinates: tuple[MatchedCoordinate, ...]


@dataclass(frozen=True, slots=True)
class MatchedArmCensus:
    allocation: ObjectIdentity
    arm_ids: tuple[str, ...]
    groups: tuple[MatchedGroup, ...]

    @property
    def independent_unit_count(self):
        return len(self.groups)

    @property
    def nested_coordinate_count(self):
        return sum(len(group.coordinates) for group in self.groups)


def validate_matched_arms(design: MatchedArmDesign, allocation: UnitAllocation) -> MatchedArmCensus:
    """Retain every allocated whole unit and every declared nested arm."""
    if type(design) is not MatchedArmDesign or type(allocation) is not UnitAllocation:
        raise TypeError("matched comparisons require their exact design and whole-unit allocation")
    design.__post_init__()
    allocation.__post_init__()
    if allocation.identity != design.allocation:
        raise ValueError("matched design substitutes its original whole-unit allocation")
    by_unit = {unit.unit_id: [] for unit in allocation.units}
    for coordinate in design.coordinates:
        if coordinate.unit_id not in by_unit:
            raise ValueError("matched design supplies an unallocated independent unit")
        by_unit[coordinate.unit_id].append(coordinate)
    varying = set(design.varying_coordinate_names)
    groups = []
    for unit_id, coordinates in by_unit.items():
        if tuple(row.arm_id for row in coordinates) != design.arm_ids:
            raise ValueError("matched design omits a required whole-unit/arm cell")
        invariant = tuple((name, type(value), value) for name, value in coordinates[0].values if name not in varying)
        if any(tuple((name, type(value), value) for name, value in row.values if name not in varying) != invariant
                for row in coordinates[1:]):
            raise ValueError("matched arms change an undeclared invariant coordinate or scalar type")
        groups.append(MatchedGroup(unit_id, tuple(coordinates)))
    return MatchedArmCensus(allocation.identity, design.arm_ids, tuple(groups))


def validate_parameter_grid(grid: ParameterGrid) -> ParameterGrid:
    """Require all two-level corners plus the exact common center.

    LINEAR symmetry is arithmetic; LOG symmetry is geometric. Rational Decimal
    conversion avoids context-rounded products when checking a log midpoint.
    Axes and settings do not create independent units or inference themselves.
    """
    if type(grid) is not ParameterGrid:
        raise TypeError("parameter grid requires its exact typed declaration")
    grid.__post_init__()
    for axis in grid.axes:
        low, center, high = map(Fraction, axis.levels)
        if (2 * center != low + high if axis.scale is ParameterAxisScale.LINEAR else center * center != low * high):
            raise ValueError("parameter grid reference is not the exact center in its declared scale")
    if len(grid.settings) != 2 ** len(grid.axes) + 1:
        raise ValueError("parameter grid omits its complete corner/center setting census")
    expected = set(product(*((axis.levels[0], axis.levels[2]) for axis in grid.axes)))
    expected.add(tuple(axis.levels[1] for axis in grid.axes))
    observed = tuple(setting.values for setting in grid.settings)
    if len(observed) != len(expected) or set(observed) != expected:
        raise ValueError("parameter grid duplicates or omits a required corner/center setting")
    return grid


def require_reserved_population(reservation: PopulationReservationBinding, allocation: UnitAllocation,
        source_record: CanonicalRecord, publication_port: WorkerInputPort, *,
        fitting_unit_ids: tuple[str, ...] = ()) -> tuple[str, ...]:
    """Authenticate original immutable allocation bytes before fitting/loading.

    The domain derives and independently validates UnitAllocation from this
    original source record. Historical source/publication records stay unchanged.
    This helper refuses exposure metadata and unit overlap; it does not determine
    actual source freshness, physical-regime overlap or publication chronology.
    Call it in the registered pre-fit path before invoking a training loader.
    """
    if (type(reservation) is not PopulationReservationBinding or type(allocation) is not UnitAllocation
            or not isinstance(source_record, CanonicalRecord) or type(publication_port) is not WorkerInputPort):
        raise TypeError("reservation use requires typed original records and its authenticated input port")
    reservation.__post_init__()
    allocation.__post_init__()
    validate_source = getattr(source_record, "__post_init__", None)
    if callable(validate_source):
        validate_source()
    if (reservation.source_id_field not in {field.name for field in fields(source_record)}
            or type(getattr(source_record, reservation.source_id_field)) is not str
            or ObjectIdentity.from_record(getattr(source_record, reservation.source_id_field), source_record)
                != reservation.source_allocation
            or reservation.source_allocation not in allocation.sources
            or reservation.allocation != allocation.identity):
        raise ValueError("reservation substitutes its original source or derived whole-unit allocation")
    publication = reservation.publication
    if ((publication_port.artifact_id, publication_port.materialization_id, publication_port.payload_schema,
            publication_port.media_type, publication_port.size_bytes, publication_port.visibility_ceiling,
            publication_port.outcome_access)
            != (publication.artifact_id, reservation.materialization_id, publication.payload_schema,
                publication.media_type, publication.size_bytes, VisibilityCeiling.PROSPECTIVE, OutcomeAccess.OUTCOME_BLIND)
            or publication_port.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE
            or publication_port.outcome_access is not OutcomeAccess.OUTCOME_BLIND
            or type(publication_port.kind) is not WorkerInputKind
            or publication_port.kind not in (WorkerInputKind.EXTERNAL, WorkerInputKind.DEPENDENCY)):
        raise ValueError("reservation lacks its exact original protected allocation publication")
    role_names = {row.role for row in allocation.roles}
    if not set(reservation.protected_roles) <= role_names:
        raise ValueError("reservation omits a declared protected population role")
    protected = tuple(row.unit_id for row in allocation.roles if row.role in reservation.protected_roles)
    protected_set = set(protected)
    if any(unit.exposed for unit in allocation.units if unit.unit_id in protected_set):
        raise ValueError("reservation includes an already exposed independent unit")
    if (type(fitting_unit_ids) is not tuple or fitting_unit_ids != tuple(sorted(set(fitting_unit_ids)))
            or any(type(unit_id) is not str for unit_id in fitting_unit_ids)):
        raise ValueError("fit use requires its exact unique declared whole-unit census")
    for unit_id in fitting_unit_ids:
        validate_stable_id(unit_id)
    if not set(fitting_unit_ids) <= set(allocation.unit_ids()) or protected_set.intersection(fitting_unit_ids):
        raise ValueError("fitting uses an unallocated unit or protected transfer population")
    expected = source_record.canonical_bytes()
    if len(expected) != publication.size_bytes or sha256(expected).hexdigest() != publication.sha256:
        raise ValueError("reservation changes its original full canonical publication bytes")
    cursor = publication_port.cursor()
    try:
        raw = cursor.read()
    finally:
        cursor.close()
    if len(raw) != publication.size_bytes or raw != expected:
        raise ValueError("reservation input substitutes the original full canonical allocation bytes")
    return protected
