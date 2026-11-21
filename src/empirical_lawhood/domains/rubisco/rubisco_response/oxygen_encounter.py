# SPDX-License-Identifier: MPL-2.0
"""Source-bound oxygen encounter placement in an unchanged full Gp environment.

This creates a coordinate proposal for two gas atoms. It does not append them
to a topology, transplant a foreign reaction barrier, or establish a basin.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

import numpy as np

from empirical_lawhood.domains.rubisco.kinetics.fm23_preparation import OXYGEN_TARGETS, distance_bounds, infer_role_candidates
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_decimal, validate_sha256
from empirical_lawhood.domains.rubisco.rubisco_response.active_model_packet import ActiveModelPreparation
from empirical_lawhood.domains.rubisco.rubisco_response.active_model_preparation import minimum_image, verified_coordinates
from empirical_lawhood.domains.rubisco.rubisco_response.active_state_geometry import CatalyticStateSeed, expand_state_coordinates
from empirical_lawhood.domains.rubisco.rubisco_response.gp_active_scaffold import proper_rigid_fit
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_atoms import MolecularRepresentation
from empirical_lawhood.domains.rubisco.rubisco_response.oxygen_source_geometry import OxygenSourceProjection
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_force_contracts import AmberPeriodicCell


_ANCHORS = ('C2', 'C3', 'O2', 'O3', 'Mg')
_SCOPE = 'NEW_UNRELAXED_OXYGEN_ENCOUNTER_COORDINATES_NOT_AUGMENTED_TOPOLOGY_OR_PHYSICAL_ADMISSION'


def _decimals(values):
    return tuple(Decimal(str(float(v))) for v in values)


@dataclass(frozen=True, slots=True)
class OxygenEncounterGeometry(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/oxygen-encounter-geometry'
    representation: ObjectIdentity
    preparation: ObjectIdentity
    selected_seed: ObjectIdentity
    selected_site: ObjectIdentity
    source_projection: ObjectIdentity
    cell: ObjectIdentity
    original_coordinate_sha256: str
    expanded_seed_coordinate_sha256: str
    retained_physical_atom_count: int
    # (role, one-based source ordinal, zero-based physical target index).
    anchors: tuple[tuple[str, int, int], ...]
    source_gas_indices_1based: tuple[int, int]
    rotation: tuple[Decimal, ...]
    translation_angstrom: tuple[Decimal, ...]
    anchor_residuals_angstrom: tuple[Decimal, ...]
    fit_rmsd_angstrom: Decimal
    gas_coordinates_angstrom: tuple[tuple[Decimal, ...], ...]
    # Per gas atom: nearest original physical atom, distance, nearest heavy atom, distance.
    nearest_original_contacts: tuple[tuple[int, Decimal, int, Decimal], ...]
    inspected_gas_environment_pairs: int
    scope: str = _SCOPE

    def __post_init__(self):
        for value in (self.representation, self.preparation, self.selected_seed, self.selected_site,
                self.source_projection, self.cell):
            exact(value, ObjectIdentity)
        for value in (self.original_coordinate_sha256, self.expanded_seed_coordinate_sha256):
            validate_sha256(value)
        n = self.retained_physical_atom_count
        if (type(n) is not int or n <= 0 or type(self.anchors) is not tuple
                or tuple(row[0] for row in self.anchors) != _ANCHORS
                or any(type(a) is not int or not 1 <= a <= 248 or type(b) is not int or not 0 <= b < n
                    for _, a, b in self.anchors)
                or len({r[1] for r in self.anchors}) != 5 or len({r[2] for r in self.anchors}) != 5
                or self.source_gas_indices_1based != (162, 168)
                or type(self.inspected_gas_environment_pairs) is not int
                or self.inspected_gas_environment_pairs != 2*n or self.scope != _SCOPE):
            raise ValueError('oxygen encounter changes its source, physical anchor or complete contact census')
        for row, length in ((self.rotation, 9), (self.translation_angstrom, 3),
                (self.anchor_residuals_angstrom, 5)):
            if type(row) is not tuple or len(row) != length:
                raise ValueError('oxygen encounter requires complete coordinate-transform operands')
            for value in row:
                validate_decimal(value, field_name='oxygen_coordinate_transform')
        validate_decimal(self.fit_rmsd_angstrom, field_name='oxygen_fit_rmsd', minimum=Decimal(0))
        if any(v < 0 for v in self.anchor_residuals_angstrom):
            raise ValueError('anchor residual cannot be negative')
        if type(self.gas_coordinates_angstrom) is not tuple or len(self.gas_coordinates_angstrom) != 2:
            raise ValueError('oxygen encounter requires both gas atoms')
        for row in self.gas_coordinates_angstrom:
            if type(row) is not tuple or len(row) != 3:
                raise ValueError('gas position requires three coordinates')
            for value in row:
                validate_decimal(value, field_name='oxygen_gas_coordinate')
        if type(self.nearest_original_contacts) is not tuple or len(self.nearest_original_contacts) != 2:
            raise ValueError('oxygen encounter omits a full-environment contact search')
        for atom, distance, heavy, heavy_distance in self.nearest_original_contacts:
            if any(type(i) is not int or not 0 <= i < n for i in (atom, heavy)):
                raise ValueError('oxygen contact points outside the original environment')
            for value in (distance, heavy_distance):
                validate_decimal(value, field_name='oxygen_contact_distance', minimum=Decimal(0))

    @property
    def identity(self):
        return ObjectIdentity.from_record('oxygen-encounter.'+self.fingerprint(), self)


def oxygen_source_roles(source):
    """Derive the original gas/core roles using the existing distance constraints."""
    exact(source, OxygenSourceProjection)
    atoms = source.geometries[0].atoms
    roles, _ = infer_role_candidates(atoms, tuple(row[0] for row in OXYGEN_TARGETS))
    candidates = tuple(i for i, atom in enumerate(atoms, 1)
        if atom.element == 'O' and i not in (roles.os1, roles.os2)
        and Decimal('1.15') < distance_bounds(atoms[roles.c2-1], atom)[0] < Decimal('1.6'))
    if len(candidates) != 1:
        raise ValueError('oxygen source has no unique substrate C2-bound oxygen')
    return (roles.c2, roles.c3, candidates[0], roles.o3, roles.mg), (roles.os1, roles.os2)


def fit_gas_encounter(*, source_anchors, target_anchors, source_gas, environment, atomic_numbers, box):
    """Pure proper-rotation transfer and complete periodic contact observation."""
    rotation, translation, rmsd = proper_rigid_fit(source_anchors, target_anchors)
    gas = np.asarray(source_gas, dtype=float) @ rotation + translation
    original = np.asarray(environment, dtype=float)
    numbers = np.asarray(atomic_numbers)
    box = np.asarray(box, dtype=float)
    if (gas.shape not in ((2, 3), (3, 3)) or original.ndim != 2 or original.shape[1] != 3 or not len(original)
            or numbers.shape != (len(original),) or not np.any(numbers > 1)
            or box.shape != (3,) or not np.isfinite(box).all() or np.any(box <= 0)
            or not np.isfinite(gas).all() or not np.isfinite(original).all()):
        raise ValueError('gas transfer requires a diatomic or triatomic gas and a complete finite periodic environment')
    heavy = np.flatnonzero(numbers > 1)
    contacts = []
    for point in gas:
        distances = np.linalg.norm(minimum_image(original-point, box), axis=1)
        nearest, nearest_heavy = int(np.argmin(distances)), int(heavy[np.argmin(distances[heavy])])
        contacts.append((nearest, Decimal(str(float(distances[nearest]))),
            nearest_heavy, Decimal(str(float(distances[nearest_heavy])))))
    residuals = np.linalg.norm(np.asarray(source_anchors) @ rotation + translation-target_anchors, axis=1)
    return rotation, translation, rmsd, residuals, gas, tuple(contacts)


def fit_oxygen_encounter(**operands):
    """Retain the two-atom oxygen contract on the shared gas geometry owner."""
    if np.asarray(operands['source_gas']).shape != (2, 3):
        raise ValueError('oxygen encounter requires exactly two source gas atoms')
    return fit_gas_encounter(**operands)


def assess_gas_encounter(*, observation, source_anchors, target_anchors, source_gas,
        environment, atomic_numbers, box):
    """Check a retained transform independently of the fitting implementation.

    Orthogonality, orientation and the singular-value lower bound establish a
    proper least-squares fit. All periodic nearest contacts are recomputed.
    The 1e-10 Angstrom comparison tolerance covers floating-point arithmetic;
    it is not a physical fit, overlap, energetic or chemical acceptance rule.
    """
    rotation, translation, rmsd, residuals, gas, contacts = observation
    left, right = np.asarray(source_anchors, dtype=float), np.asarray(target_anchors, dtype=float)
    rotation, translation = np.asarray(rotation, dtype=float), np.asarray(translation, dtype=float)
    source_gas, gas = np.asarray(source_gas, dtype=float), np.asarray(gas, dtype=float)
    residuals = np.asarray(residuals, dtype=float)
    original, box = np.asarray(environment, dtype=float), np.asarray(box, dtype=float)
    numbers = np.asarray(atomic_numbers)
    arrays = (left, right, rotation, translation, source_gas, gas, original, box,
        np.asarray(residuals, dtype=float), np.asarray([rmsd], dtype=float))
    if (left.shape != (5, 3) or right.shape != left.shape or rotation.shape != (3, 3)
            or translation.shape != (3,) or source_gas.shape not in ((2, 3), (3, 3))
            or gas.shape != source_gas.shape or original.ndim != 2 or original.shape[1:] != (3,)
            or not len(original) or numbers.shape != (len(original),) or not np.any(numbers > 1)
            or box.shape != (3,) or np.any(box <= 0) or residuals.shape != (5,) or len(contacts) != len(gas)
            or any(not np.isfinite(a).all() for a in arrays)):
        raise ValueError('gas assessment requires complete finite original operands and observations')
    if (not np.allclose(rotation.T @ rotation, np.eye(3), atol=1e-12, rtol=0)
            or not np.isclose(np.linalg.det(rotation), 1, atol=1e-12, rtol=0)):
        raise ValueError('gas transfer is not a proper rotation')
    centered_left, centered_right = left-left.mean(axis=0), right-right.mean(axis=0)
    if min(np.linalg.matrix_rank(a, tol=1e-10) for a in (centered_left, centered_right)) < 2:
        raise ValueError('gas assessment refuses collinear or coincident anchors')
    covariance = centered_left.T @ centered_right
    singular = np.linalg.svd(covariance, compute_uv=False)
    sign = 1 if np.linalg.det(covariance) >= 0 else -1
    lower = np.sum(centered_left**2)+np.sum(centered_right**2)-2*(sum(singular[:2])+sign*singular[2])
    actual_residuals = np.linalg.norm(left @ rotation+translation-right, axis=1)
    if (not np.allclose(translation, right.mean(axis=0)-left.mean(axis=0) @ rotation, atol=1e-10, rtol=0)
            or not np.isclose(np.sum(actual_residuals**2), max(0, lower), atol=1e-10, rtol=1e-12)
            or not np.allclose(residuals, actual_residuals, atol=1e-10, rtol=0)
            or not np.isclose(float(rmsd), np.sqrt(np.mean(actual_residuals**2)), atol=1e-10, rtol=0)
            or not np.allclose(gas, source_gas @ rotation+translation, atol=1e-10, rtol=0)):
        raise ValueError('gas transfer changes the least-squares fit, retained residuals or gas positions')
    heavy = np.flatnonzero(numbers > 1)
    for point, (index, distance, heavy_index, heavy_distance) in zip(gas, contacts, strict=True):
        delta = original-point
        delta -= box*np.floor(delta/box+.5)
        squared = np.einsum('ij,ij->i', delta, delta)
        nearest, nearest_heavy = int(np.argmin(squared)), int(heavy[np.argmin(squared[heavy])])
        if ((index, heavy_index) != (nearest, nearest_heavy)
                or not np.isclose(float(distance), np.sqrt(squared[nearest]), atol=1e-10, rtol=0)
                or not np.isclose(float(heavy_distance), np.sqrt(squared[nearest_heavy]), atol=1e-10, rtol=0)):
            raise ValueError('gas transfer changes its complete periodic nearest-contact observations')
    return dict(status='INDEPENDENT_GEOMETRY_ARITHMETIC_SATISFIED',
        inspected_gas_environment_pairs=len(gas)*len(original), physical_or_chemical_admission=False)


def selected_gas_free_target(*, representation, preparation, seed, coordinate_bytes, cell):
    """Bind the common complete target for source-gas coordinate proposals."""
    for value, kind in ((representation, MolecularRepresentation), (preparation, ActiveModelPreparation),
            (seed, CatalyticStateSeed), (cell, AmberPeriodicCell)):
        exact(value, kind)
    if (preparation.representation != representation.identity or seed not in preparation.seeds
            or (seed.state_label, seed.water_occupancy) not in {
                ('initial-enolate-kcxh-hie', 'AS_CONSTRUCTED'),
                ('reactive-enolate-kcxh-hie', 'UNOCCUPIED')}
            or cell.raw_topology != representation.raw_topology or cell.raw_coordinates != representation.raw_coordinates
            or cell.physical_atom_count != len(representation.atoms)):
        raise ValueError('gas preparation changes its original full Gp representation, enolate or periodic cell')
    site = next(s for s in preparation.sites if s.identity == seed.site)
    molecular_site = next(s for s in representation.sites if s.site_id == site.path.reactive_site_id)
    if site.path.gas != 'NONE' or molecular_site.gas_atom_indices:
        raise ValueError('gas insertion proposal requires the actual gas-free predecessor')
    verified_coordinates(representation, coordinate_bytes)
    xyz = expand_state_coordinates(seed, coordinate_bytes)
    named = {representation.atoms[i].name:i for i in molecular_site.ligand_atom_indices}
    if len(molecular_site.magnesium_atom_indices) != 1 or not set(_ANCHORS[:-1]).issubset(named):
        raise ValueError('Gp site lacks the exact substrate/Mg anchor correspondence')
    targets = tuple(named[name] for name in _ANCHORS[:-1]) + molecular_site.magnesium_atom_indices
    if tuple(representation.atoms[i].atomic_number for i in targets) != (6, 6, 8, 8, 12):
        raise ValueError('Gp anchor correspondence changes the source elements')
    box = np.asarray(cell.lengths_angstrom, dtype=float)
    magnesium = xyz[targets[-1]]
    target_xyz = magnesium + minimum_image(xyz[list(targets)]-magnesium, box)
    return site, targets, dict(target_anchors=target_xyz, environment=xyz,
        atomic_numbers=tuple(a.atomic_number for a in representation.atoms), box=box)


def _oxygen_operands(*, source, representation, preparation, seed, coordinate_bytes, cell):
    """Authenticate the common source and target selection before geometry."""
    site, targets, operands = selected_gas_free_target(representation=representation,
        preparation=preparation, seed=seed, coordinate_bytes=coordinate_bytes, cell=cell)
    source_indices, gas_indices = oxygen_source_roles(source)
    atoms = source.geometries[0].atoms
    source_xyz = np.asarray([[float(v) for v in atom.coordinate_tokens] for atom in atoms])
    operands.update(source_anchors=source_xyz[[i-1 for i in source_indices]],
        source_gas=source_xyz[[i-1 for i in gas_indices]])
    return site, targets, source_indices, gas_indices, operands


def prepare_oxygen_encounter(*, source, representation, preparation, seed, coordinate_bytes, cell):
    """Place two gas atoms beside an unchanged full Gp enolate environment.

    Fit residuals and closest contacts are observations, not pass thresholds.
    """
    site, targets, source_indices, gas_indices, operands = _oxygen_operands(source=source,
        representation=representation, preparation=preparation, seed=seed,
        coordinate_bytes=coordinate_bytes, cell=cell)
    rotation, translation, rmsd, residuals, gas, contacts = fit_oxygen_encounter(**operands)
    return OxygenEncounterGeometry(representation.identity, preparation.identity, seed.identity, site.identity,
        source.identity, cell.identity, seed.original_coordinate_sha256, seed.expanded_coordinate_sha256,
        len(representation.atoms), tuple(zip(_ANCHORS, source_indices, targets, strict=True)), gas_indices,
        _decimals(rotation.ravel()), _decimals(translation), _decimals(residuals), Decimal(str(rmsd)),
        tuple(_decimals(row) for row in gas), contacts, 2*len(representation.atoms))


def assess_oxygen_encounter(*, result, **originals):
    """Independently check the retained geometry against its original operands."""
    exact(result, OxygenEncounterGeometry)
    site, targets, source_indices, gas_indices, operands = _oxygen_operands(**originals)
    representation, preparation, seed, cell = (originals[k] for k in ('representation', 'preparation', 'seed', 'cell'))
    if ((result.representation, result.preparation, result.selected_seed, result.selected_site,
            result.source_projection, result.cell) != (representation.identity, preparation.identity,
                seed.identity, site.identity, originals['source'].identity, cell.identity)
            or (result.original_coordinate_sha256, result.expanded_seed_coordinate_sha256) != (
                seed.original_coordinate_sha256, seed.expanded_coordinate_sha256)
            or result.retained_physical_atom_count != len(representation.atoms)
            or result.anchors != tuple(zip(_ANCHORS, source_indices, targets, strict=True))
            or result.source_gas_indices_1based != gas_indices):
        raise ValueError('oxygen encounter substitutes original source, target or atom correspondence')
    arithmetic = assess_gas_encounter(observation=(np.asarray(result.rotation, dtype=float).reshape(3, 3),
        result.translation_angstrom, result.fit_rmsd_angstrom, result.anchor_residuals_angstrom,
        result.gas_coordinates_angstrom, result.nearest_original_contacts), **operands)
    return dict(status='COORDINATE_TRANSFER_INDEPENDENTLY_CHECKED', arithmetic=arithmetic, new_native_calls=0,
        physical_or_chemical_admission=False, gas_atoms_added_to_topology=0,
        required=('RELAXED_TARGET_STATE', 'GAS_AUGMENTED_TOPOLOGY_AND_FULL_COMPLEMENT',
            'SELECTED_QM_REGION_CHARGE_SPIN_AND_PROTONATION', 'ENERGY_FORCE_AND_GEOMETRY_ASSESSMENT',
            'ACCESS_AND_SPIN_TRANSMISSION', 'OXYGEN_PRODUCTIVE_VERSUS_RETURN_COMMITMENT'))
