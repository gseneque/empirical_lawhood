# SPDX-License-Identifier: MPL-2.0
"""Source-bound Cartesian directions for complete periodic force actions."""

from dataclasses import dataclass, replace
from decimal import Decimal
from hashlib import sha256
import math
from typing import ClassVar

from empirical_lawhood.science.models.datasets import ArrayDatasetManifest
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_decimal, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact


@dataclass(frozen=True, slots=True)
class PeriodicPhysicalDirection(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/periodic-physical-direction'
    direction_id: str
    representation: ObjectIdentity
    coordinates: ArrayDatasetManifest
    source: ObjectIdentity
    physical_atom_count: int
    components: tuple[tuple[int, int, Decimal], ...]
    convention: str = 'UNIT_UNCONSTRAINED_CARTESIAN_DIRECTION'

    def __post_init__(self):
        validate_stable_id(self.direction_id)
        for pin in (self.representation, self.source):
            exact(pin, ObjectIdentity)
        exact(self.coordinates, ArrayDatasetManifest)
        if (type(self.physical_atom_count) is not int or self.physical_atom_count < 1
                or len(self.coordinates.members) != 1
                or self.coordinates.members[0].shape != (self.physical_atom_count, 3)
                or self.coordinates.members[0].dtype != '<f8'
                or not self.coordinates.members[0].finite_required
                or self.convention != 'UNIT_UNCONSTRAINED_CARTESIAN_DIRECTION'
                or type(self.components) is not tuple or not self.components):
            raise ValueError('physical direction requires its complete original Cartesian population')
        indices = []
        for row in self.components:
            if type(row) is not tuple or len(row) != 3:
                raise ValueError('physical direction requires exact atom, axis and coefficient triples')
            atom, axis, coefficient = row
            if (type(atom) is not int or not 0 <= atom < self.physical_atom_count
                    or type(axis) is not int or not 0 <= axis < 3):
                raise ValueError('physical direction escapes its original Cartesian population')
            validate_decimal(coefficient, field_name='direction_coefficient')
            if not coefficient or not math.isfinite(float(coefficient)) or float(coefficient) == 0:
                raise ValueError('physical direction requires finite representable nonzero components')
            indices.append((atom, axis))
        if tuple(indices) != tuple(sorted(set(indices))):
            raise ValueError('physical direction repeats or reorders Cartesian components')
        norm = math.hypot(*(float(row[2]) for row in self.components))
        if not math.isclose(norm, 1.0, rel_tol=32*math.ulp(1.0), abs_tol=0):
            raise ValueError('physical direction must retain its declared unit Cartesian normalization')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.direction_id, self)


def prepare_formation_response_direction(*, coordinate, prototype, coordinate_bytes):
    """Derive the local formation-coordinate gradient at the original construction.

    This is a Cartesian Hessian query, not a mass-weighted dynamical input,
    equilibrium observation or inverse-operator certificate.
    """
    import numpy as np

    from empirical_lawhood.domains.rubisco.rubisco_response.formation_coordinate import PreparedFormationCoordinate
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_bias import _bond
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import PeriodicProbeSelection

    exact(coordinate, PreparedFormationCoordinate)
    exact(prototype, PeriodicProbeSelection)
    if (coordinate.representation != prototype.representation
            or coordinate.physical_atom_count != prototype.physical_atom_count
            or prototype.molecular.constraints != 'NONE_NATURAL_MASSES'
            or type(coordinate_bytes) is not bytes
            or len(coordinate_bytes) != prototype.physical_atom_count*3*8
            or sha256(coordinate_bytes).hexdigest() != prototype.coordinates.members[0].sha256):
        raise ValueError('formation direction changes original atoms, coordinates or constraint semantics')
    xyz = np.frombuffer(coordinate_bytes, dtype='<f8').reshape((-1, 3))
    if not np.isfinite(xyz).all():
        raise ValueError('formation direction requires finite complete coordinates')
    carbon, hydrogen, oxygen = coordinate.native_atom_indices
    lengths = np.array(tuple(float(v) for v in prototype.cell.lengths_angstrom))
    _, _, first = _bond(xyz[carbon], xyz[hydrogen], lengths)
    _, _, second = _bond(xyz[hydrogen], xyz[oxygen], lengths)
    gradient = np.array((first, -first-second, second))
    gradient /= np.linalg.norm(gradient)
    components = tuple(sorted((atom, axis, Decimal.from_float(float(gradient[row, axis])))
        for row, atom in enumerate(coordinate.native_atom_indices) for axis in range(3)
        if gradient[row, axis] != 0))
    provisional = PeriodicPhysicalDirection('direction.formation.pending', prototype.representation,
        prototype.coordinates, coordinate.identity, prototype.physical_atom_count, components)
    return replace(provisional, direction_id='direction.formation.'+provisional.fingerprint())
