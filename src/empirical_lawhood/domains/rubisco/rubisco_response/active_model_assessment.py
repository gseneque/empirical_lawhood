# SPDX-License-Identifier: MPL-2.0
"""Independent partition, atom-conservation and starting-geometry assessment.

Readers never call coordinate construction or a molecular engine. A satisfied
seed assessment does not supply an equilibrium population or physical rate.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.active_model_preparation import ActivePreparationProtocol, PreparedCatalyticSite, verified_coordinates
from empirical_lawhood.domains.rubisco.rubisco_response.active_state_geometry import CatalyticStateSeed, expand_state_coordinates
from empirical_lawhood.domains.rubisco.rubisco_response.catalytic_path_selection import validate_catalytic_path_selection
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact


@dataclass(frozen=True, slots=True)
class ActiveSeedAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/active-seed-assessment'
    seed: ObjectIdentity
    site: ObjectIdentity
    disposition: str
    findings: tuple[str, ...]
    changed_atoms: int
    physical_atom_count: int
    nearest_water_magnesium_angstrom: Decimal
    minimum_changed_nonbonded_distance_angstrom: Decimal | None
    active_basin: str = 'UNEVALUABLE'
    equilibrium_population: str = 'UNEVALUABLE'

    def __post_init__(self):
        for value in (self.seed, self.site):
            exact(value, ObjectIdentity)
        if (self.disposition != ('FALSIFIED' if self.findings else 'SATISFIED')
                or self.findings != tuple(sorted(set(self.findings)))
                or type(self.changed_atoms) is not int or type(self.physical_atom_count) is not int
                or not 0 <= self.changed_atoms <= self.physical_atom_count
                or self.active_basin != 'UNEVALUABLE' or self.equilibrium_population != 'UNEVALUABLE'):
            raise ValueError('seed assessment changes its exact findings or scientific scope')
        for finding in self.findings:
            validate_stable_id(finding)


def assess_catalytic_partition(*, representation, prototype, site, protocol, coordinate_bytes):
    """Recompute the complete water-selection denominator without the preparer."""
    import numpy as np
    exact(site, PreparedCatalyticSite)
    exact(protocol, ActivePreparationProtocol)
    if site.protocol != protocol.identity or site.path.representation != representation.identity:
        raise ValueError('partition assessment substitutes its selected source')
    validate_catalytic_path_selection(site.path, representation)
    original = verified_coordinates(representation, coordinate_bytes)
    box = np.asarray(tuple(map(float, prototype.cell.lengths_angstrom)))
    if prototype.cell.raw_coordinates != representation.raw_coordinates:
        raise ValueError('partition assessment changes its original cell')
    core = set(site.core_atom_indices)-set(range(len(representation.atoms), len(representation.atoms)+7))
    polar = [i for i in core if representation.atoms[i].atomic_number in (7, 8)]
    magnesium = [i for i in core if representation.atoms[i].atomic_number == 12]
    if len(magnesium) != 1:
        raise ValueError('partition assessment loses the original site magnesium')
    grouped = {}
    for i, atom in enumerate(representation.atoms):
        grouped.setdefault(atom.residue_id, []).append(i)
    expected, expected_rows, distances = [], [], []
    for residue in representation.residues:
        if residue.role != 'WATER':
            continue
        members = grouped[residue.residue_id]
        oxygen = [i for i in members if representation.atoms[i].atomic_number == 8]
        if len(oxygen) != 1 or sorted(representation.atoms[i].atomic_number for i in members) != [1, 1, 8]:
            raise ValueError('partition assessment finds an incomplete source water')
        offset = original[oxygen[0]]-original[polar+magnesium]
        offset -= box*np.floor(offset/box+.5)
        separation = np.sqrt(np.sum(offset**2, axis=1))
        if min(separation[:-1]) <= float(protocol.polar_water_cutoff_angstrom) or separation[-1] <= float(protocol.magnesium_water_cutoff_angstrom):
            expected.append(residue.residue_id)
            names = {representation.atoms[i].name: i for i in members}
            expected_rows.append(tuple(names[n] for n in ('O', 'H1', 'H2')))
            distances.append(float(separation[-1]))
    if (tuple(expected) != site.water_residue_ids or tuple(expected_rows) != site.water_atom_indices
            or any(abs(x-float(y)) > 1e-10 for x, y in zip(distances, site.initial_water_distances_angstrom, strict=True))):
        raise ValueError('partition assessment detects omitted, added or misplaced site water')
    initial = next(g for g in protocol.graphs if g.label == 'keto-hie')
    native_edges = {(b.first, b.second) for b in representation.bonds if b.first in core and b.second in core}
    mapped_edges = {tuple(sorted((site.core_atom_indices[b.first], site.core_atom_indices[b.second])))
        for b in initial.bonds if not initial.atoms[b.first].cap and not initial.atoms[b.second].cap}
    if native_edges != mapped_edges:
        raise ValueError('partition assessment changes native catalytic-core bonds')
    for atom, index in zip(initial.atoms, site.core_atom_indices, strict=True):
        if atom.cap:
            boundary = site.path.boundaries[index-len(representation.atoms)]
            matches = [b for b in initial.bonds if initial.atoms[b.first].label == atom.label or initial.atoms[b.second].label == atom.label]
            if len(matches) != 1:
                raise ValueError('partition assessment finds an invalid cap graph')
            b = matches[0]
            other = b.second if initial.atoms[b.first].label == atom.label else b.first
            if site.core_atom_indices[other] != boundary.qm_atom_index:
                raise ValueError('partition assessment changes a source-derived cap boundary')
        else:
            native = representation.atoms[index]
            if native.atomic_number != atom.atomic_number or native.name != atom.label.rsplit('.', 1)[1]:
                raise ValueError('partition assessment changes a named physical core atom')
    return {'site': site.path.reactive_site_id, 'status': 'SATISFIED', 'physical_core_atoms': len(core),
        'complete_waters': len(expected), 'physical_qm_atoms': len(site.path.qm_atom_indices), 'caps': len(site.path.boundaries)}


def assess_catalytic_seed(*, representation, site, protocol, seed, coordinate_bytes, cell):
    """Assess the original seed from identities and geometry, without rebuilding it."""
    import numpy as np
    exact(seed, CatalyticStateSeed)
    if (seed.site != site.identity or seed.protocol != protocol.identity or site.protocol != protocol.identity
            or site.path.representation != representation.identity):
        raise ValueError('seed assessment substitutes its exact selected site or protocol')
    graph = next((g for g in protocol.graphs if g.identity == seed.graph), None)
    if graph is None or graph.label != seed.state_label:
        raise ValueError('seed assessment changes its complete chemical graph')
    old = verified_coordinates(representation, coordinate_bytes)
    xyz = expand_state_coordinates(seed, coordinate_bytes)
    lengths = np.asarray(tuple(map(float, cell.lengths_angstrom)))
    if cell.raw_coordinates != representation.raw_coordinates or cell.raw_topology != representation.raw_topology:
        raise ValueError('seed assessment substitutes its selected original periodic cell')

    def delta(points, origin):
        values = points-origin
        return values-lengths*np.floor(values/lengths+.5)

    initial = next(g for g in protocol.graphs if g.label == 'keto-hie')
    mapping = site.core_atom_indices
    old_hosts, new_hosts, neighbours = {}, {}, {}
    for state, hosts in ((initial, old_hosts), (graph, new_hosts)):
        for bond in state.bonds:
            for i, j in ((bond.first, bond.second), (bond.second, bond.first)):
                if state.atoms[i].atomic_number == 1 and not state.atoms[i].cap:
                    hosts[mapping[i]] = mapping[j]
    for bond in graph.bonds:
        i, j = mapping[bond.first], mapping[bond.second]
        neighbours.setdefault(i, set()).add(j)
        neighbours.setdefault(j, set()).add(i)
    transferred = {i for i in new_hosts if new_hosts[i] != old_hosts[i]}
    water = site.water_atom_indices[site.water_residue_ids.index(site.coordination_water_residue_id)]
    allowed = transferred | (set(water) if seed.water_occupancy != 'AS_CONSTRUCTED' else set())
    changed = set(map(int, np.flatnonzero(np.any(xyz != old, axis=1))))
    findings = set(seed.construction_findings)
    if not transferred.issubset(changed) or not changed.issubset(allowed):
        findings.add('unexpected-or-missing-coordinate-change')
    for hydrogen in transferred:
        host = new_hosts[hydrogen]
        expected = float(protocol.hydrogen_oxygen_distance_angstrom if representation.atoms[host].atomic_number == 8
            else protocol.hydrogen_nitrogen_distance_angstrom)
        if abs(np.linalg.norm(delta(xyz[hydrogen], xyz[host]))-expected) > 1e-7:
            findings.add('transferred-proton-distance')
    for i in water:
        neighbours[i] = set(water)-{i}
        for j in water:
            if abs(np.linalg.norm(delta(xyz[i], xyz[j]))-np.linalg.norm(delta(old[i], old[j]))) > 1e-7:
                findings.add('changed-water-internal-geometry')
    mg = next(mapping[i] for i, atom in enumerate(graph.atoms) if atom.atomic_number == 12)
    all_waters = [r[0] for r in site.water_atom_indices]
    water_distances = np.linalg.norm(delta(xyz[all_waters], xyz[mg]), axis=1)
    selected_distance = float(np.linalg.norm(delta(xyz[water[0]], xyz[mg])))
    if seed.water_occupancy == 'OCCUPIED' and abs(selected_distance-float(protocol.occupied_water_distance_angstrom)) > 1e-7:
        findings.add('occupied-water-distance')
    if seed.water_occupancy == 'UNOCCUPIED' and min(water_distances) < float(protocol.unoccupied_water_minimum_angstrom)-1e-7:
        findings.add('unoccupied-water-distance')
    numbers = np.asarray([atom.atomic_number for atom in representation.atoms])
    minimum = None
    for i in changed:
        separation = np.linalg.norm(delta(xyz, xyz[i]), axis=1)
        excluded = {i, *neighbours.get(i, ())}
        indices = np.asarray([j for j in excluded if j < len(xyz)], dtype=int)
        separation[indices] = np.inf
        observed = float(np.min(separation))
        minimum = observed if minimum is None else min(minimum, observed)
        limit = np.full(len(xyz), float(protocol.minimum_new_hydrogen_contact_angstrom))
        if numbers[i] != 1:
            limit[numbers != 1] = float(protocol.minimum_new_heavy_contact_angstrom)
        if np.any(separation < limit):
            findings.add('new-nonbonded-close-contact')
    return ActiveSeedAssessment(seed.identity, site.identity, 'FALSIFIED' if findings else 'SATISFIED',
        tuple(sorted(findings)), len(changed), len(xyz), Decimal(str(float(min(water_distances)))),
        None if minimum is None else Decimal(str(minimum)))
