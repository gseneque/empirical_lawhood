# SPDX-License-Identifier: MPL-2.0
"""Atom-conserving unrelaxed proton and magnesium-water starting geometries.

Sparse coordinate changes bind the complete original array and its expanded
successor digest. Neither graph labels nor geometry construction admit basins.
"""

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
import math
from typing import ClassVar

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_decimal, validate_sha256, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.active_model_preparation import ActivePreparationProtocol, CatalyticCoreGraph, PreparedCatalyticSite, minimum_image, verified_coordinates
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact


@dataclass(frozen=True, slots=True)
class ActiveCoordinateChange(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/active-coordinate-change'
    atom_index: int
    before_angstrom: tuple[Decimal, Decimal, Decimal]
    after_angstrom: tuple[Decimal, Decimal, Decimal]

    def __post_init__(self):
        if type(self.atom_index) is not int or self.atom_index < 0:
            raise ValueError('coordinate change requires its actual physical atom index')
        for row in (self.before_angstrom, self.after_angstrom):
            if type(row) is not tuple or len(row) != 3:
                raise ValueError('coordinate change requires complete Cartesian triples')
            for value in row:
                validate_decimal(value, field_name='coordinate')
        if self.before_angstrom == self.after_angstrom:
            raise ValueError('coordinate change cannot conceal an unchanged atom')


@dataclass(frozen=True, slots=True)
class CatalyticStateSeed(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/catalytic-state-seed'
    seed_id: str
    site: ObjectIdentity
    protocol: ObjectIdentity
    graph: ObjectIdentity
    state_label: str
    water_occupancy: str
    physical_atom_count: int
    original_coordinate_sha256: str
    coordinate_changes: tuple[ActiveCoordinateChange, ...]
    expanded_coordinate_sha256: str
    construction_findings: tuple[str, ...]
    scope: str = 'UNRELAXED_ATOM_CONSERVING_HYPOTHESIS_WITHOUT_POPULATION_OR_RATE_ADMISSION'

    def __post_init__(self):
        validate_stable_id(self.seed_id)
        validate_stable_id(self.state_label)
        for row in (self.site, self.protocol, self.graph):
            exact(row, ObjectIdentity)
        if (type(self.physical_atom_count) is not int or self.physical_atom_count <= 0
                or self.water_occupancy not in {'AS_CONSTRUCTED', 'OCCUPIED', 'UNOCCUPIED'}
                or self.state_label.startswith('reactive-') != (self.water_occupancy != 'AS_CONSTRUCTED')):
            raise ValueError('state seed changes its explicit chemical/coordination alternative')
        for value in (self.original_coordinate_sha256, self.expanded_coordinate_sha256):
            validate_sha256(value)
        if type(self.coordinate_changes) is not tuple:
            raise ValueError('state seed requires immutable complete coordinate changes')
        for row in self.coordinate_changes:
            exact(row, ActiveCoordinateChange)
        indices = tuple(row.atom_index for row in self.coordinate_changes)
        if indices != tuple(sorted(set(indices))) or any(i >= self.physical_atom_count for i in indices):
            raise ValueError('state seed changes an absent or repeated physical atom')
        if (type(self.construction_findings) is not tuple
                or self.construction_findings != tuple(sorted(set(self.construction_findings)))):
            raise ValueError('state seed requires its complete ordered construction findings')
        for finding in self.construction_findings:
            validate_stable_id(finding)
        if self.scope != 'UNRELAXED_ATOM_CONSERVING_HYPOTHESIS_WITHOUT_POPULATION_OR_RATE_ADMISSION':
            raise ValueError('coordinate construction cannot admit an active basin or rate')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.seed_id, self)


def expand_state_coordinates(seed, original_coordinate_bytes):
    """Apply an exact complete-array-bound overlay; never reconstruct a missing source."""
    import numpy as np
    exact(seed, CatalyticStateSeed)
    if (type(original_coordinate_bytes) is not bytes or len(original_coordinate_bytes) != seed.physical_atom_count*24
            or sha256(original_coordinate_bytes).hexdigest() != seed.original_coordinate_sha256):
        raise ValueError('state expansion substitutes its original full coordinate array')
    xyz = np.frombuffer(original_coordinate_bytes, dtype='<f8').reshape(-1, 3).copy()
    for row in seed.coordinate_changes:
        if not np.array_equal(xyz[row.atom_index], tuple(map(float, row.before_angstrom))):
            raise ValueError('state coordinate change has a different original atom position')
        xyz[row.atom_index] = tuple(map(float, row.after_angstrom))
    if not np.isfinite(xyz).all() or sha256(xyz.astype('<f8').tobytes()).hexdigest() != seed.expanded_coordinate_sha256:
        raise ValueError('state expansion differs from its complete declared successor coordinates')
    return xyz


@dataclass(frozen=True, slots=True)
class FixedProtonReferences:
    """Three sparse placements on one O–O line in the selected dry proton diagnostic."""

    proton_atom_index: int
    donor_acceptor_angstrom: float
    spectator_bond_angstrom: float
    initial_proton_distances_angstrom: tuple[float, float]
    positions_angstrom: tuple[tuple[str, tuple[Decimal, Decimal, Decimal]], ...]
    refusal: str | None


def fixed_proton_references(coordinates_angstrom, elements, *, donor: int, acceptor: int,
                            proton: int, spectator_proton: int, spectator_oxygen: int) -> FixedProtonReferences:
    """Place one hydrogen at the two 1 Å endpoints and midpoint of a source-mapped O–O line.

    The original coordinates must share one unwrapped Cartesian frame. All other nuclei
    and the external field stay fixed in these conditional electronic references.
    """
    import numpy as np

    raw = np.asarray(coordinates_angstrom)
    if raw.dtype.kind not in "iuf" or raw.shape != (len(elements), 3):
        raise ValueError("the proton reference requires one real Cartesian position per atom")
    xyz = np.asarray(raw, dtype=np.float64)
    if not np.isfinite(xyz).all():
        raise ValueError("proton reference coordinates must be finite")
    indices = (donor, acceptor, proton, spectator_proton, spectator_oxygen)
    if (any(type(i) is not int or not 0 <= i < len(xyz) for i in indices)
            or len(set(indices)) != len(indices)
            or tuple(elements[i] for i in indices) != ("O", "O", "H", "H", "O")):
        raise ValueError("proton reference roles require distinct source-mapped oxygens and hydrogens")
    direction = xyz[acceptor] - xyz[donor]
    separation = float(np.linalg.norm(direction))
    spectator = float(np.linalg.norm(xyz[spectator_proton] - xyz[spectator_oxygen]))
    distances = tuple(float(np.linalg.norm(xyz[proton] - xyz[i])) for i in (donor, acceptor))
    if not all(math.isfinite(value) for value in (separation, spectator, *distances)):
        raise ValueError("proton reference distances must be finite")
    if not 2.20 <= separation <= 3.50 or spectator > 1.30:
        return FixedProtonReferences(proton, separation, spectator, distances, (), "OUTSIDE_SELECTED_BOND_SUPPORT")
    positions = []
    for role, along in (("donor", 1.0), ("midpoint", separation / 2), ("acceptor", separation - 1.0)):
        point = xyz[donor] + direction * along / separation
        after = tuple(Decimal(str(float(x))) for x in point)
        positions.append((role, after))
    return FixedProtonReferences(proton, separation, spectator, distances, tuple(positions), None)


def _unit(vector):
    import numpy as np
    length = float(np.linalg.norm(vector))
    if not math.isfinite(length) or length < 1e-10:
        raise ValueError('state geometry requires a nondegenerate source direction')
    return vector/length


def _frame(xyz, named, box):
    import numpy as np
    origin = xyz[named['magnesium.MG']]
    first = _unit(minimum_image(xyz[named['protein.210.OQ1']]-origin, box))
    other = minimum_image(xyz[named['protein.212.OD1']]-origin, box)
    second = _unit(other-first*np.dot(first, other))
    return np.column_stack((first, second, np.cross(first, second)))


def _hydrogen_position(xyz, graph, atom_ordinal, target, mapping, box, frame, protocol):
    import numpy as np
    host = mapping[target]
    neighbours = [b.second if b.first == target else b.first for b in graph.bonds
        if target in (b.first, b.second) and atom_ordinal not in (b.first, b.second)
        and graph.atoms[b.second if b.first == target else b.first].atomic_number != 1]
    vectors = [_unit(minimum_image(xyz[mapping[i]]-xyz[host], box)) for i in neighbours]
    if not vectors:
        raise ValueError('transferred proton acceptor has no source-bound heavy neighbour')
    if graph.atoms[target].atomic_number == 7:
        direction = _unit(-np.sum(vectors, axis=0))
        length = float(protocol.hydrogen_nitrogen_distance_angstrom)
    elif graph.atoms[target].atomic_number == 8 and len(vectors) == 1:
        axis = vectors[0]
        desired = minimum_image(xyz[mapping[atom_ordinal]]-xyz[host], box)
        tangent = desired-axis*np.dot(desired, axis)
        if np.linalg.norm(tangent) < 1e-10:
            candidate = min(frame.T, key=lambda v: abs(float(np.dot(v, axis))))
            tangent = candidate-axis*np.dot(candidate, axis)
        angle = math.radians(109.5)
        direction = math.cos(angle)*axis+math.sin(angle)*_unit(tangent)
        length = float(protocol.hydrogen_oxygen_distance_angstrom)
    else:
        raise ValueError('transferred proton has an unsupported explicitly selected acceptor')
    return xyz[host]+length*direction


def _water_geometry(xyz, water, magnesium, direction, radius, frame, box):
    """Properly rotate the original rigid water; point its H bisector away from Mg."""
    import numpy as np
    oxygen, h1, h2 = water
    first = minimum_image(xyz[h1]-xyz[oxygen], box)
    second = minimum_image(xyz[h2]-xyz[oxygen], box)
    bisector = _unit(first+second)
    transverse = _unit(first-second-bisector*np.dot(first-second, bisector))
    old_frame = np.column_stack((bisector, transverse, np.cross(bisector, transverse)))
    tangent = min(frame.T, key=lambda v: abs(float(np.dot(v, direction))))
    transverse_new = _unit(tangent-direction*np.dot(tangent, direction))
    new_frame = np.column_stack((direction, transverse_new, np.cross(direction, transverse_new)))
    rotation = new_frame @ old_frame.T
    origin = xyz[magnesium]+radius*direction
    return np.asarray((origin, origin+rotation@first, origin+rotation@second))


def _place_water(xyz, water, magnesium, named, numbers, box, frame, radius, protocol):
    """Search one frozen geometric menu, without energies or outcome-dependent selection."""
    import numpy as np
    donors = ('protein.210.OQ1', 'protein.212.OD1', 'protein.213.OE1', 'ligand.O2', 'ligand.O3')
    vacancy = _unit(-sum((_unit(minimum_image(xyz[named[k]]-xyz[magnesium], box)) for k in donors)))
    # The complete finite direction menu is a construction algorithm, not a
    # ceiling on molecular execution, SCF convergence or relaxation iterations.
    directions = [vacancy]
    golden = math.pi*(3-math.sqrt(5))
    for i in range(512):
        z = 1-2*(i+.5)/512
        radial = math.sqrt(1-z*z)
        directions.append(frame@np.asarray((radial*math.cos(golden*i), radial*math.sin(golden*i), z)))
    distances = np.linalg.norm(minimum_image(xyz-xyz[magnesium], box), axis=1)
    local = np.flatnonzero(distances <= radius+3)
    local = np.asarray([int(i) for i in local if int(i) not in water], dtype=int)
    candidates = []
    for ordinal, direction in enumerate(directions):
        placed = _water_geometry(xyz, water, magnesium, direction, radius, frame, box)
        separation = np.linalg.norm(minimum_image(placed[:, None, :]-xyz[local][None, :, :], box), axis=2)
        limits = np.full(separation.shape, float(protocol.minimum_new_hydrogen_contact_angstrom))
        limits[0, numbers[local] != 1] = float(protocol.minimum_new_heavy_contact_angstrom)
        clearance = float(np.min(separation-limits))
        if clearance >= 0:
            candidates.append((float(np.dot(direction, vacancy)), clearance, -ordinal, placed))
    if not candidates:
        return None
    return max(candidates, key=lambda row: row[:3])[3]


def materialize_catalytic_states(*, representation, site, protocol, coordinate_bytes, cell):
    """Derive six initial/intermediate seeds and six reactive coordination seeds."""
    import numpy as np
    exact(site, PreparedCatalyticSite)
    exact(protocol, ActivePreparationProtocol)
    if site.protocol != protocol.identity or site.path.representation != representation.identity:
        raise ValueError('state geometry substitutes its prepared site or chemical protocol')
    xyz = verified_coordinates(representation, coordinate_bytes)
    box = np.asarray(tuple(map(float, cell.lengths_angstrom)))
    if cell.raw_coordinates != representation.raw_coordinates or cell.raw_topology != representation.raw_topology:
        raise ValueError('state geometry changes its original periodic cell')
    initial = next(g for g in protocol.graphs if g.label == 'keto-hie')
    mapping = site.core_atom_indices
    named = {a.label: i for a, i in zip(initial.atoms, mapping, strict=True)}
    frame = _frame(xyz, named, box)
    numbers = np.asarray([a.atomic_number for a in representation.atoms])
    water = site.water_atom_indices[site.water_residue_ids.index(site.coordination_water_residue_id)]
    magnesium = named['magnesium.MG']

    def hydrogen_hosts(graph):
        hosts = {}
        for bond in graph.bonds:
            for first, second in ((bond.first, bond.second), (bond.second, bond.first)):
                if graph.atoms[first].atomic_number == 1 and not graph.atoms[first].cap:
                    hosts[first] = second
        return hosts

    original_hosts = hydrogen_hosts(initial)
    seeds = []
    for graph in protocol.graphs:
        exact(graph, CatalyticCoreGraph)
        proton_xyz = xyz.copy()
        for hydrogen, host in hydrogen_hosts(graph).items():
            if original_hosts[hydrogen] != host:
                proton_xyz[mapping[hydrogen]] = _hydrogen_position(xyz, graph, hydrogen, host,
                    mapping, box, frame, protocol)
        for occupancy in (('OCCUPIED', 'UNOCCUPIED') if graph.label.startswith('reactive-') else ('AS_CONSTRUCTED',)):
            changed = proton_xyz.copy()
            findings = []
            if occupancy == 'OCCUPIED':
                placed = _place_water(changed, water, magnesium, named, numbers, box, frame,
                    float(protocol.occupied_water_distance_angstrom), protocol)
                if placed is None:
                    findings.append('occupied-water-placement-unavailable')
                else:
                    changed[list(water)] = placed
            elif occupancy == 'UNOCCUPIED':
                distance = float(np.linalg.norm(minimum_image(changed[water[0]]-changed[magnesium], box)))
                if distance < float(protocol.unoccupied_water_minimum_angstrom):
                    placed = _place_water(changed, water, magnesium, named, numbers, box, frame,
                        float(protocol.unoccupied_water_minimum_angstrom)+1, protocol)
                    if placed is None:
                        findings.append('unoccupied-water-placement-unavailable')
                    else:
                        changed[list(water)] = placed
            delta = np.flatnonzero(np.any(changed != xyz, axis=1))
            changes = tuple(ActiveCoordinateChange(int(i),
                tuple(Decimal(str(float(x))) for x in xyz[i]), tuple(Decimal(str(float(x))) for x in changed[i])) for i in delta)
            seed_id = 'seed.'+site.path.reactive_site_id+'.'+graph.label+'.'+occupancy.lower()+'.'+site.fingerprint()
            seeds.append(CatalyticStateSeed(seed_id, site.identity, protocol.identity, graph.identity,
                graph.label, occupancy, len(xyz), sha256(coordinate_bytes).hexdigest(), changes,
                sha256(changed.astype('<f8').tobytes()).hexdigest(), tuple(sorted(findings))))
    return tuple(sorted(seeds, key=lambda s: s.seed_id))
