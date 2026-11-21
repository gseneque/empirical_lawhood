# SPDX-License-Identifier: MPL-2.0
"""Independent all-site ligand-graph correspondence from retained operands.

Graph agreement is a representation check. It does not establish protonation,
metal coordination, electronic accuracy or a physically active ensemble.
"""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_ids, validate_nonempty, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.contexts import SITE_LIGANDS
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact, identities
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_atoms import MolecularBond, MolecularRepresentation, indices


@dataclass(frozen=True, slots=True)
class LigandAtom(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/ligand-atom"
    atom_id: str
    native_atom_name: str
    atomic_number: int
    formal_charge: int

    def __post_init__(self):
        validate_stable_id(self.atom_id)
        validate_nonempty(self.native_atom_name, field_name="native_atom_name")
        if (type(self.atomic_number) is not int or not 1 <= self.atomic_number <= 118
                or type(self.formal_charge) is not int):
            raise ValueError("ligand graph needs exact elements and integer formal charges")


@dataclass(frozen=True, slots=True)
class LigandChemicalGraph(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/ligand-chemical-graph"
    graph_id: str
    ligand_state: str
    atoms: tuple[LigandAtom, ...]
    bonds: tuple[MolecularBond, ...]
    formal_charge: int
    sources: tuple[ObjectIdentity, ...]
    interpretation: str = "SELECTED_CHEMICAL_GRAPH_NOT_PHYSICAL_OR_RATE_VALIDATION"

    def __post_init__(self):
        validate_stable_id(self.graph_id)
        if self.ligand_state not in SITE_LIGANDS:
            raise ValueError("ligand graph must name its exact selected chemical state")
        if type(self.atoms) is not tuple or type(self.bonds) is not tuple:
            raise ValueError("ligand graph needs complete immutable atom and bond populations")
        if (self.ligand_state == "EMPTY") != (not self.atoms):
            raise ValueError("empty and occupied ligand graphs cannot alias")
        require_sorted_unique_ids(self.atoms, attribute="atom_id", field_name="atoms")
        for row in self.atoms:
            exact(row, LigandAtom)
        for row in self.bonds:
            exact(row, MolecularBond)
        edges = tuple((row.first, row.second) for row in self.bonds)
        if edges != tuple(sorted(set(edges))) or any(row.second >= len(self.atoms) for row in self.bonds):
            raise ValueError("ligand graph bond census duplicates or escapes its atoms")
        if type(self.formal_charge) is not int or sum(row.formal_charge for row in self.atoms) != self.formal_charge:
            raise ValueError("ligand formal charge differs from its complete atom sum")
        identities(self.sources)
        if self.interpretation != "SELECTED_CHEMICAL_GRAPH_NOT_PHYSICAL_OR_RATE_VALIDATION":
            raise ValueError("chemical graph selection cannot establish physical or kinetic accuracy")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.graph_id, self)


@dataclass(frozen=True, slots=True)
class SiteLigandBinding(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/site-ligand-binding"
    site_id: str
    chemical_graph: ObjectIdentity
    # Native index for every graph atom, in the graph's immutable atom order.
    atom_indices: tuple[int, ...]

    def __post_init__(self):
        validate_stable_id(self.site_id)
        exact(self.chemical_graph, ObjectIdentity)
        if (type(self.atom_indices) is not tuple
                or any(type(value) is not int or value < 0 for value in self.atom_indices)
                or len(set(self.atom_indices)) != len(self.atom_indices)):
            raise ValueError("site ligand binding must preserve each distinct graph atom")


def validate_ligand_correspondence(representation, graphs, bindings):
    """Check every selected site's named chemical graph against every ligand atom.

    The original graph identities must already be in the selected chemistry's
    source closure. Native Amber bond presence is checked separately: its
    fixed-topology bond list alone does not establish chemical bond orders.
    """
    exact(representation, MolecularRepresentation)
    if type(graphs) is not tuple or type(bindings) is not tuple:
        raise ValueError("chemical assessment needs the complete immutable selected inputs")
    require_sorted_unique_ids(graphs, attribute="graph_id", field_name="graphs")
    require_sorted_unique_ids(bindings, attribute="site_id", field_name="bindings")
    for row in graphs:
        exact(row, LigandChemicalGraph)
    for row in bindings:
        exact(row, SiteLigandBinding)
    by_graph = {row.identity: row for row in graphs}
    if set(by_graph) != {row.ligand_chemical_graph for row in representation.chemistry.sites}:
        raise ValueError("chemical assessment substitutes the exact selected graph census")
    if tuple(row.site_id for row in bindings) != tuple(row.site_id for row in representation.sites):
        raise ValueError("chemical assessment drops an all-site ligand binding")
    native_bonds = {(row.first, row.second): row.order for row in representation.bonds}
    summaries = []
    for site, selected, binding in zip(representation.sites, representation.chemistry.sites, bindings, strict=True):
        graph = by_graph.get(binding.chemical_graph)
        if (graph is None or binding.chemical_graph != site.chemical_graph
                or graph.ligand_state != selected.ligand_state):
            raise ValueError("chemical assessment relabels a different site's ligand graph")
        indices(tuple(sorted(binding.atom_indices)), count=len(representation.atoms), name="ligand graph binding")
        if (len(binding.atom_indices) != len(graph.atoms)
                or set(binding.atom_indices) != set(site.ligand_atom_indices)):
            raise ValueError("chemical assessment omits or invents a ligand atom")
        for native_index, atom in zip(binding.atom_indices, graph.atoms, strict=True):
            native = representation.atoms[native_index]
            if (native.name, native.atomic_number) != (atom.native_atom_name, atom.atomic_number):
                raise ValueError("chemical graph differs from its actual atom-name/element correspondence")
        expected_bonds = {tuple(sorted((binding.atom_indices[row.first], binding.atom_indices[row.second]))): row.order
                          for row in graph.bonds}
        ligand = set(binding.atom_indices)
        actual_bonds = {edge: order for edge, order in native_bonds.items() if set(edge).issubset(ligand)}
        if expected_bonds != actual_bonds:
            raise ValueError("chemical graph differs from the full selected ligand bond orders")
        # Cross-fragment covalent bonds require a different explicit chemical
        # state; this ligand-only graph does not silently authorize them.
        if any((first in ligand) != (second in ligand) for first, second in native_bonds):
            raise ValueError("ligand graph omits a covalent bond to another molecular component")
        summaries.append((site.site_id, graph.identity, len(graph.atoms), graph.formal_charge))
    return tuple(summaries)


def changed_ligand_bonds(before, after):
    """Exact finite chemical graph change, including bond-order changes."""
    exact(before, LigandChemicalGraph)
    exact(after, LigandChemicalGraph)
    def edges(graph):
        return {(graph.atoms[row.first].atom_id, graph.atoms[row.second].atom_id, row.order)
                for row in graph.bonds}
    old, new = edges(before), edges(after)
    return tuple(sorted(old - new)), tuple(sorted(new - old))
