# SPDX-License-Identifier: MPL-2.0
"""Complete site-specific partitions and source-bound catalytic graph hypotheses.

The original full molecular record and arrays stay separate immutable operands.
This owner derives every site from its own geometry. It makes no force call.
"""

from collections import Counter
from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
import json
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.contracts import SourceMember
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_decimal, validate_nonempty, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.catalytic_path_selection import CatalyticPathSelection, CatalyticProteinRegion, validate_catalytic_path_selection
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact, identities
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_atoms import MolecularBond, MolecularRepresentation
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import PeriodicProbeSelection, validate_periodic_probe_model
from empirical_lawhood.domains.rubisco.rubisco_response.reactive_selection import ReactiveBoundary


STATE_NAMES = tuple(sorted(('keto-hie', 'keto-hid', 'initial-enolate-kcxh-hie',
    'initial-enolate-kcxh-hid', 'enediol-hie', 'enediol-hid',
    'reactive-enolate-kcxh-hie', 'reactive-enolate-kcxh-hid', 'reactive-enolate-kcx-hip')))
VALENCES = {(1, 0): 1, (6, 0): 4, (7, 0): 3, (7, 1): 4,
    (8, 0): 2, (8, -1): 1, (12, 2): 0, (15, 0): 5}


@dataclass(frozen=True, slots=True)
class CatalyticGraphAtom(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/catalytic-graph-atom'
    label: str
    atomic_number: int
    formal_charge: int
    cap: bool

    def __post_init__(self):
        validate_nonempty(self.label, field_name='chemical_atom_label')
        if not self.label.isascii() or any(c.isspace() for c in self.label):
            raise ValueError('chemical atom label must retain its exact ASCII spelling')
        if (type(self.atomic_number) is not int or type(self.formal_charge) is not int
                or (self.atomic_number, self.formal_charge) not in VALENCES or type(self.cap) is not bool
                or self.cap and (self.atomic_number, self.formal_charge) != (1, 0)):
            raise ValueError('catalytic graph requires explicit supported valence and cap identities')


@dataclass(frozen=True, slots=True)
class CatalyticCoreGraph(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/catalytic-core-graph'
    label: str
    atoms: tuple[CatalyticGraphAtom, ...]
    bonds: tuple[MolecularBond, ...]
    source: ObjectIdentity

    def __post_init__(self):
        if self.label not in STATE_NAMES or type(self.atoms) is not tuple or type(self.bonds) is not tuple:
            raise ValueError('catalytic core requires its exact complete selected graph')
        exact(self.source, ObjectIdentity)
        for atom in self.atoms:
            exact(atom, CatalyticGraphAtom)
        labels = tuple(a.label for a in self.atoms)
        if labels != tuple(sorted(set(labels))) or len(labels) != 125 or sum(a.cap for a in self.atoms) != 7:
            raise ValueError('catalytic core changes its 118 physical atoms and seven caps')
        degree = Counter()
        edges = []
        for bond in self.bonds:
            exact(bond, MolecularBond)
            if bond.second >= len(self.atoms) or bond.order not in (Decimal(1), Decimal(2), Decimal(3)):
                raise ValueError('catalytic graph has an absent atom or unsupported bond order')
            edges.append((bond.first, bond.second))
            degree[bond.first] += bond.order
            degree[bond.second] += bond.order
        if tuple(edges) != tuple(sorted(set(edges))):
            raise ValueError('catalytic core repeats or reorders an edge')
        if (sum(a.formal_charge for a in self.atoms) != -2
                or sum(a.atomic_number for a in self.atoms) + 2 != 476
                or any(degree[i] != VALENCES[a.atomic_number, a.formal_charge] for i, a in enumerate(self.atoms))):
            raise ValueError('catalytic core violates complete valence, charge or electron conservation')

    @property
    def identity(self):
        return ObjectIdentity.from_record('graph.gp-catalytic.'+self.label+'.'+self.fingerprint(), self)


def read_catalytic_core_graphs(source):
    """Decode a selected retained graph census, then check every complete graph.

    A report's self-described disposition grants no scientific admission.
    Initial graph/native correspondence is checked separately for every site.
    """
    exact(source, SourceMember)
    document = json.loads(source.raw_utf8)
    rows = document['core_chemical_hypotheses']
    if type(rows) is not list or tuple(sorted(row['label'] for row in rows)) != STATE_NAMES:
        raise ValueError('catalytic source omits or repeats a selected chemical hypothesis')
    pin = ObjectIdentity.from_record(source.member_id, source)
    graphs = []
    for row in sorted(rows, key=lambda r: r['label']):
        atoms = tuple(CatalyticGraphAtom(label, atom['element'], atom['formal_charge'], atom['cap'])
            for label, atom in sorted(row['atoms'].items()))
        index = {a.label: i for i, a in enumerate(atoms)}
        bonds = tuple(sorted((MolecularBond(*sorted((index[b['first']], index[b['second']])), Decimal(b['order']))
            for b in row['bonds']), key=lambda b: (b.first, b.second)))
        graphs.append(CatalyticCoreGraph(row['label'], atoms, bonds, pin))
    census = tuple((a.label, a.atomic_number, a.cap) for a in graphs[0].atoms)
    if any(tuple((a.label, a.atomic_number, a.cap) for a in g.atoms) != census for g in graphs):
        raise ValueError('chemical alternatives create, delete or relabel a physical atom')
    return tuple(graphs)


@dataclass(frozen=True, slots=True)
class ActivePreparationProtocol(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/active-preparation-protocol'
    protocol_id: str
    graphs: tuple[CatalyticCoreGraph, ...]
    polar_water_cutoff_angstrom: Decimal = Decimal('3.5')
    magnesium_water_cutoff_angstrom: Decimal = Decimal('3.0')
    occupied_water_distance_angstrom: Decimal = Decimal('2.15')
    unoccupied_water_minimum_angstrom: Decimal = Decimal('3.5')
    hydrogen_oxygen_distance_angstrom: Decimal = Decimal('0.98')
    hydrogen_nitrogen_distance_angstrom: Decimal = Decimal('1.01')
    minimum_new_heavy_contact_angstrom: Decimal = Decimal('1.4')
    minimum_new_hydrogen_contact_angstrom: Decimal = Decimal('0.7')

    def __post_init__(self):
        validate_stable_id(self.protocol_id)
        if type(self.graphs) is not tuple or tuple(g.label for g in self.graphs) != STATE_NAMES:
            raise ValueError('active preparation requires all nine ordered chemical graphs')
        for graph in self.graphs:
            exact(graph, CatalyticCoreGraph)
        first = self.graphs[0]
        conserved = tuple((a.label, a.atomic_number, a.cap) for a in first.atoms)
        if any(g.source != first.source or tuple((a.label, a.atomic_number, a.cap) for a in g.atoms) != conserved
                for g in self.graphs):
            raise ValueError('active preparation changes its chemical source or conserved atoms')
        for name in ('polar_water_cutoff_angstrom', 'magnesium_water_cutoff_angstrom',
                'occupied_water_distance_angstrom', 'unoccupied_water_minimum_angstrom',
                'hydrogen_oxygen_distance_angstrom', 'hydrogen_nitrogen_distance_angstrom',
                'minimum_new_heavy_contact_angstrom', 'minimum_new_hydrogen_contact_angstrom'):
            value = getattr(self, name)
            validate_decimal(value, field_name=name, minimum=Decimal(0))
            if value == 0:
                raise ValueError('active preparation distances must be positive')
        if not self.occupied_water_distance_angstrom < self.magnesium_water_cutoff_angstrom < self.unoccupied_water_minimum_angstrom:
            raise ValueError('occupied and unoccupied magnesium-water selections overlap')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.protocol_id, self)


@dataclass(frozen=True, slots=True)
class PreparedCatalyticSite(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/prepared-catalytic-site'
    path: CatalyticPathSelection
    protocol: ObjectIdentity
    # Native physical indices, then caps at physical_atom_count + boundary ordinal.
    core_atom_indices: tuple[int, ...]
    water_residue_ids: tuple[str, ...]
    water_atom_indices: tuple[tuple[int, int, int], ...]
    # O, H1, H2 order for each complete water; no water is created or deleted.
    coordination_water_residue_id: str
    initial_water_distances_angstrom: tuple[Decimal, ...]
    sources: tuple[ObjectIdentity, ...]

    def __post_init__(self):
        exact(self.path, CatalyticPathSelection)
        exact(self.protocol, ObjectIdentity)
        count = self.path.physical_atom_count
        if (type(self.core_atom_indices) is not tuple or len(self.core_atom_indices) != 125
                or len(set(self.core_atom_indices)) != 125
                or any(type(i) is not int or not 0 <= i < count + 7 for i in self.core_atom_indices)
                or set(i for i in self.core_atom_indices if i >= count) != set(range(count, count+7))):
            raise ValueError('site changes its complete 118-atom core and seven boundary caps')
        if (type(self.water_residue_ids) is not tuple or not self.water_residue_ids
                or self.water_residue_ids != tuple(sorted(set(self.water_residue_ids)))
                or self.coordination_water_residue_id not in self.water_residue_ids
                or type(self.water_atom_indices) is not tuple
                or len(self.water_atom_indices) != len(self.water_residue_ids)
                or type(self.initial_water_distances_angstrom) is not tuple
                or len(self.initial_water_distances_angstrom) != len(self.water_residue_ids)):
            raise ValueError('site omits its complete water population or coordination-water identity')
        water_atoms = []
        for name, row, distance in zip(self.water_residue_ids, self.water_atom_indices,
                self.initial_water_distances_angstrom, strict=True):
            validate_stable_id(name)
            if type(row) is not tuple or len(row) != 3 or any(type(i) is not int or not 0 <= i < count for i in row):
                raise ValueError('site requires all three distinct physical atoms of each water')
            validate_decimal(distance, field_name='initial_water_distance', minimum=Decimal(0))
            water_atoms.extend(row)
        core = {i for i in self.core_atom_indices if i < count}
        if (len(set(water_atoms)) != len(water_atoms) or core & set(water_atoms)
                or core | set(water_atoms) != set(self.path.qm_atom_indices)):
            raise ValueError('site water/core union changes the exact QM population')
        identities(self.sources)
        if not {self.protocol, self.path.identity, *self.path.sources}.issubset(self.sources):
            raise ValueError('prepared site loses actual source closure')

    @property
    def identity(self):
        return ObjectIdentity.from_record('prepared.'+self.path.reactive_site_id+'.'+self.fingerprint(), self)


def verified_coordinates(representation, coordinate_bytes):
    """Verify a complete array for an already constructed immutable model.

    The preparation/reader entry separately validates the full representation.
    Repeating all 300,000 atom constructors for every state adds no new source
    observation. Array bytes and their digest remain checked on every call.
    """
    import numpy as np
    if type(representation) is not MolecularRepresentation:
        raise TypeError('active coordinates require an exact MolecularRepresentation')
    member = representation.arrays.members[0]
    if (type(coordinate_bytes) is not bytes or member.name != 'coordinates-angstrom'
            or member.dtype != '<f8' or member.shape != (len(representation.atoms), 3)
            or len(coordinate_bytes) != len(representation.atoms)*24
            or sha256(coordinate_bytes).hexdigest() != member.sha256):
        raise ValueError('active preparation changes the complete original coordinate array')
    xyz = np.frombuffer(coordinate_bytes, dtype='<f8').reshape(-1, 3)
    if not np.isfinite(xyz).all():
        raise ValueError('active preparation coordinates are not all finite')
    return xyz


def minimum_image(delta, lengths):
    import numpy as np
    return delta-lengths*np.rint(delta/lengths)


def prepare_catalytic_sites(*, representation, prototype, coordinate_bytes, protocol):
    """Derive all eight partitions independently from each site's actual water geometry."""
    import numpy as np
    exact(prototype, PeriodicProbeSelection)
    exact(protocol, ActivePreparationProtocol)
    validate_periodic_probe_model(prototype, representation)
    xyz = verified_coordinates(representation, coordinate_bytes)
    box = np.asarray(tuple(map(float, prototype.cell.lengths_angstrom)))
    residues = {r.residue_id: r for r in representation.residues}
    by_residue = {r: {} for r in residues}
    for i, atom in enumerate(representation.atoms):
        by_residue[atom.residue_id][atom.name] = i
    by_position = {(r.chain_id, r.sequence_position_1based): r for r in representation.residues if r.role == 'PROTEIN'}
    initial = next(g for g in protocol.graphs if g.label == 'keto-hie')
    initial_edges = {(initial.atoms[b.first].label, initial.atoms[b.second].label) for b in initial.bonds
        if not initial.atoms[b.first].cap and not initial.atoms[b.second].cap}
    native_edges = {(b.first, b.second) for b in representation.bonds}
    positions = sorted({int(a.label.split('.')[1]) for a in initial.atoms if a.label.startswith('protein.')})
    water_names, water_rows = [], []
    for name in sorted(residues):
        if residues[name].role != 'WATER':
            continue
        members = by_residue[name]
        if set(members) != {'O', 'H1', 'H2'}:
            raise ValueError('active water selection requires each complete named three-site water')
        row = tuple(members[n] for n in ('O', 'H1', 'H2'))
        if tuple(representation.atoms[i].atomic_number for i in row) != (8, 1, 1):
            raise ValueError('active water selection changes a water element')
        water_names.append(name)
        water_rows.append(row)
    oxygen = np.asarray([r[0] for r in water_rows], dtype=int)
    all_polar = np.asarray([i for i, a in enumerate(representation.atoms) if a.atomic_number in (7, 8)], dtype=int)
    boundary_source = prototype.path.boundaries[0].construction_and_force_projection
    if any(b.construction_and_force_projection != boundary_source for b in prototype.path.boundaries):
        raise ValueError('active preparation requires one declared boundary construction')
    result = []
    for site in representation.sites:
        chain = residues[site.catalytic_residue_id].chain_id
        named, regions, boundaries = {}, [], []
        for position in positions:
            residue = by_position[chain, position]
            names = by_residue[residue.residue_id]
            regions.append(CatalyticProteinRegion(residue.residue_id, 'SIDECHAIN_CB_CA'))
            boundaries.append(ReactiveBoundary('link.cb-ca.'+residue.residue_id,
                names['CB'], names['CA'], 1, Decimal('1.09'), boundary_source))
            named.update(('protein.'+str(position)+'.'+name, i) for name, i in names.items())
        boundaries = tuple(sorted(boundaries, key=lambda b: b.link_id))
        for j, boundary in enumerate(boundaries):
            position = residues[representation.atoms[boundary.qm_atom_index].residue_id].sequence_position_1based
            named['protein.'+str(position)+'.LINK-H'] = len(representation.atoms)+j
        named.update(('ligand.'+representation.atoms[i].name, i) for i in site.ligand_atom_indices)
        named.update(('magnesium.'+representation.atoms[i].name, i) for i in site.magnesium_atom_indices)
        mapping = tuple(named[a.label] for a in initial.atoms)
        physical = {i for i in mapping if i < len(representation.atoms)}
        for atom, index in zip(initial.atoms, mapping, strict=True):
            if not atom.cap and representation.atoms[index].atomic_number != atom.atomic_number:
                raise ValueError('catalytic template changes an actual core element')
        expected = {tuple(sorted((named[a], named[b]))) for a, b in initial_edges}
        if expected != {e for e in native_edges if e[0] in physical and e[1] in physical}:
            raise ValueError('initial catalytic graph differs from complete native core connectivity')
        polar = sorted(i for i in physical if representation.atoms[i].atomic_number in (7, 8))
        if len(site.magnesium_atom_indices) != 1:
            raise ValueError('active preparation requires the selected single site magnesium')
        mg = site.magnesium_atom_indices[0]
        dmag = np.linalg.norm(minimum_image(xyz[oxygen]-xyz[mg], box), axis=1)
        dpolar = np.full(len(oxygen), np.inf)
        for index in polar:
            dpolar = np.minimum(dpolar, np.linalg.norm(minimum_image(xyz[oxygen]-xyz[index], box), axis=1))
        selected = np.flatnonzero((dpolar <= float(protocol.polar_water_cutoff_angstrom))
            | (dmag <= float(protocol.magnesium_water_cutoff_angstrom)))
        if not len(selected):
            raise ValueError('site has no selected complete water for its coordination alternative')
        qm = physical | {i for j in selected for i in water_rows[j]}
        shell = all_polar[np.linalg.norm(minimum_image(xyz[all_polar]-xyz[mg], box), axis=1)
            <= float(protocol.magnesium_water_cutoff_angstrom)]
        if not set(map(int, shell)).issubset(qm):
            raise ValueError('site partition omits an actual first-shell magnesium donor')
        pathsources = tuple(sorted({*prototype.path.sources, protocol.identity, initial.source}, key=lambda r: r.object_id))
        selection_digest = sha256((representation.fingerprint()+protocol.fingerprint()).encode('ascii')).hexdigest()
        path = CatalyticPathSelection('path.active-start.'+site.site_id+'.'+selection_digest,
            representation.identity, len(representation.atoms), site.site_id, tuple(sorted(qm)),
            tuple(i for i in range(len(representation.atoms)) if i not in qm),
            tuple(sorted(regions, key=lambda r: r.residue_id)), boundaries, 'NONE', (), -2, 1,
            prototype.electronic.identity, None, prototype.path.embedding_method,
            prototype.molecular.identity, 'MOVING_FULL_ASSEMBLY', pathsources)
        validate_catalytic_path_selection(path, representation)
        chosen = min(map(int, selected), key=lambda j: (float(dmag[j]), water_names[j]))
        sources = tuple(sorted({path.identity, protocol.identity, *pathsources}, key=lambda r: r.object_id))
        result.append(PreparedCatalyticSite(path, protocol.identity, mapping,
            tuple(water_names[j] for j in selected), tuple(water_rows[j] for j in selected), water_names[chosen],
            tuple(Decimal(str(float(dmag[j]))) for j in selected), sources))
    if len(result) != 8:
        raise ValueError('active preparation requires all eight original catalytic sites')
    return tuple(result)
