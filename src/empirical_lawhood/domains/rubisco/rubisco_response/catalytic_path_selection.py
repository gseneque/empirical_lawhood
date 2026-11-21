# SPDX-License-Identifier: MPL-2.0
"""Candidate complete catalytic path selection, including gas-free formation.

The existing gas-addition selection and its record format are unchanged.
This selection establishes atom correspondence, never chemical admission.
"""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact, identities
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_atoms import MolecularRepresentation, indices
from empirical_lawhood.domains.rubisco.rubisco_response.reactive_selection import ReactiveBoundary
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_ids, validate_stable_id


@dataclass(frozen=True, slots=True)
class CatalyticProteinRegion(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/catalytic-protein-region"
    residue_id: str
    treatment: str

    def __post_init__(self):
        validate_stable_id(self.residue_id)
        if self.treatment not in {"COMPLETE_RESIDUE", "SIDECHAIN_CB_CA"}:
            raise ValueError("protein region requires its explicit complete-residue or CB-CA sidechain treatment")


def protein_region_indices(region, atoms, bonds):
    """Derive the complete selected component from the original atom/bond graph."""
    exact(region, CatalyticProteinRegion)
    members = {i for i, atom in enumerate(atoms) if atom.residue_id == region.residue_id}
    if not members:
        raise ValueError("selected protein region names an absent residue")
    if region.treatment == "COMPLETE_RESIDUE":
        return tuple(sorted(members))
    by_name = {atoms[i].name: i for i in members}
    if (len(by_name) != len(members) or not {"CA", "CB", "N", "C", "O"}.issubset(by_name)
            or any(atoms[by_name[name]].atomic_number != number
                   for name, number in (("CA", 6), ("CB", 6), ("N", 7), ("C", 6), ("O", 8)))):
        raise ValueError("sidechain selection requires its complete named protein backbone and carbon cut")
    ca, cb = by_name["CA"], by_name["CB"]
    neighbours = {i: set() for i in members}
    for bond in bonds:
        if bond.first in members and bond.second in members:
            neighbours[bond.first].add(bond.second)
            neighbours[bond.second].add(bond.first)
    if cb not in neighbours[ca]:
        raise ValueError("selected sidechain has no original CB-CA bond")
    selected, pending = set(), [cb]
    while pending:
        atom = pending.pop()
        if atom in selected:
            continue
        selected.add(atom)
        pending.extend(neighbours[atom] - selected - {ca})
    if selected & {by_name[name] for name in ("CA", "N", "C", "O")}:
        raise ValueError("the selected CB-CA cut does not separate a complete sidechain")
    cuts = {(a, b) for a in selected for b in neighbours[a] if b not in selected}
    if cuts != {(cb, ca)}:
        raise ValueError("selected sidechain is not separated by exactly its original CB-CA cut")
    # Every original residue atom must belong to the sidechain or the connected
    # backbone. A disconnected omitted atom is not silently discarded.
    backbone, pending = set(), [ca]
    while pending:
        atom = pending.pop()
        if atom in backbone:
            continue
        backbone.add(atom)
        pending.extend(neighbours[atom] - backbone - selected)
    if selected | backbone != members:
        raise ValueError("selected protein residue contains a disconnected omitted atom")
    return tuple(sorted(selected))


@dataclass(frozen=True, slots=True)
class CatalyticPathSelection(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/catalytic-path-selection"
    selection_id: str
    representation: ObjectIdentity
    physical_atom_count: int
    reactive_site_id: str
    qm_atom_indices: tuple[int, ...]
    mm_atom_indices: tuple[int, ...]
    protein_regions: tuple[CatalyticProteinRegion, ...]
    boundaries: tuple[ReactiveBoundary, ...]
    gas: str
    gas_atom_indices: tuple[int, ...]
    qm_formal_charge: int
    spin_multiplicity: int
    electronic_approximation: ObjectIdentity
    oxygenation_assumption: ObjectIdentity | None
    embedding_method: ObjectIdentity
    complement_hamiltonian: ObjectIdentity
    environment_mode: str
    sources: tuple[ObjectIdentity, ...]
    interpretation: str = "SELECTED_CATALYTIC_PATH_NOT_BACKEND_OR_KINETIC_QUALIFICATION"

    def __post_init__(self):
        for name in ("selection_id", "reactive_site_id"):
            validate_stable_id(getattr(self, name))
        if type(self.physical_atom_count) is not int or self.physical_atom_count <= 0:
            raise ValueError("catalytic path requires the complete physical atom denominator")
        for name in ("qm_atom_indices", "mm_atom_indices", "gas_atom_indices"):
            indices(getattr(self, name), count=self.physical_atom_count, name=name,
                    nonempty=name != "gas_atom_indices")
        if (set(self.qm_atom_indices) & set(self.mm_atom_indices)
                or len(self.qm_atom_indices) + len(self.mm_atom_indices) != self.physical_atom_count):
            raise ValueError("catalytic partition omits or duplicates the full physical environment")
        if (self.gas not in {"NONE", "CO2", "O2"}
                or len(self.gas_atom_indices) != {"NONE": 0, "CO2": 3, "O2": 2}[self.gas]
                or not set(self.gas_atom_indices).issubset(self.qm_atom_indices)):
            raise ValueError("catalytic gas must retain its complete explicit atom population")
        if (type(self.qm_formal_charge) is not int or type(self.spin_multiplicity) is not int
                or self.spin_multiplicity <= 0):
            raise ValueError("QM charge and multiplicity must be explicit integers")
        if type(self.protein_regions) is not tuple or not self.protein_regions:
            raise ValueError("catalytic path requires its complete protein-region census")
        for region in self.protein_regions:
            exact(region, CatalyticProteinRegion)
        require_sorted_unique_ids(self.protein_regions, attribute="residue_id", field_name="protein_regions")
        if type(self.boundaries) is not tuple:
            raise ValueError("catalytic path requires its complete immutable cut census")
        for boundary in self.boundaries:
            exact(boundary, ReactiveBoundary)
            if boundary.qm_atom_index not in self.qm_atom_indices or boundary.mm_atom_index not in self.mm_atom_indices:
                raise ValueError("catalytic boundary crosses the wrong selected partition")
        require_sorted_unique_ids(self.boundaries, attribute="link_id", field_name="boundaries")
        if len({(row.qm_atom_index, row.mm_atom_index) for row in self.boundaries}) != len(self.boundaries):
            raise ValueError("catalytic boundary duplicates a physical cut")
        for row in (self.representation, self.electronic_approximation, self.embedding_method, self.complement_hamiltonian):
            exact(row, ObjectIdentity)
        if self.oxygenation_assumption is not None:
            exact(self.oxygenation_assumption, ObjectIdentity)
            if self.gas != "O2":
                raise ValueError("oxygen assumption cannot alias a different catalytic gas selection")
        if self.environment_mode not in {"FIXED_FULL_ASSEMBLY_FIELD", "MOVING_FULL_ASSEMBLY"}:
            raise ValueError("catalytic environment must retain the full assembly explicitly")
        identities(self.sources)
        required = {self.representation, self.electronic_approximation, self.embedding_method,
                    self.complement_hamiltonian, *(row.construction_and_force_projection for row in self.boundaries)}
        if self.oxygenation_assumption is not None:
            required.add(self.oxygenation_assumption)
        if not required.issubset(self.sources):
            raise ValueError("catalytic path drops its actual representation, electronic or boundary source")
        if self.interpretation != "SELECTED_CATALYTIC_PATH_NOT_BACKEND_OR_KINETIC_QUALIFICATION":
            raise ValueError("catalytic selection cannot establish physical admission")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.selection_id, self)


def validate_catalytic_path_selection(selection, representation):
    exact(selection, CatalyticPathSelection)
    exact(representation, MolecularRepresentation)
    if (selection.representation != representation.identity
            or selection.physical_atom_count != len(representation.atoms)
            or not set(representation.sources).issubset(selection.sources)):
        raise ValueError("catalytic selection substitutes the complete original representation or source closure")
    site = next((row for row in representation.sites if row.site_id == selection.reactive_site_id), None)
    if site is None or selection.gas_atom_indices != site.gas_atom_indices:
        raise ValueError("catalytic selection substitutes the complete site gas correspondence")
    qm = set(selection.qm_atom_indices)
    residues = {row.residue_id: row for row in representation.residues}
    by_residue_atoms = {key: set() for key in residues}
    for i, atom in enumerate(representation.atoms):
        by_residue_atoms[atom.residue_id].add(i)
    selected_protein = {representation.atoms[i].residue_id for i in qm
                        if residues[representation.atoms[i].residue_id].role == "PROTEIN"}
    if (selected_protein != {row.residue_id for row in selection.protein_regions}
            or site.catalytic_residue_id not in selected_protein):
        raise ValueError("catalytic protein census drops or invents a selected residue or KCX")
    for region in selection.protein_regions:
        expected = set(protein_region_indices(region, representation.atoms, representation.bonds))
        observed = {i for i in qm if representation.atoms[i].residue_id == region.residue_id}
        if observed != expected:
            raise ValueError("catalytic protein selection omits or invents an atom of the complete region")
    for residue in representation.residues:
        members = by_residue_atoms[residue.residue_id]
        if residue.role != "PROTEIN" and members & qm and not members.issubset(qm):
            raise ValueError("catalytic selection truncates a selected nonprotein molecule")
    critical = {*site.magnesium_atom_indices, *site.ligand_atom_indices, *site.proton_transfer_atom_indices}
    if not critical.issubset(qm):
        raise ValueError("catalytic selection omits selected ligand, magnesium or proton-transfer atoms")
    numbers = tuple(sorted(representation.atoms[i].atomic_number for i in selection.gas_atom_indices))
    if numbers != {"NONE": (), "CO2": (6, 8, 8), "O2": (8, 8)}[selection.gas]:
        raise ValueError("catalytic gas changes its selected molecular elements")
    cuts = {(bond.first, bond.second) if bond.first in qm else (bond.second, bond.first)
            for bond in representation.bonds if (bond.first in qm) != (bond.second in qm)}
    if cuts != {(row.qm_atom_index, row.mm_atom_index) for row in selection.boundaries}:
        raise ValueError("catalytic boundary omits or invents a physical cut bond")
    if {row.link_id for row in selection.boundaries} & {row.atom_id for row in representation.atoms}:
        raise ValueError("catalytic cap aliases a physical atom")
    electrons = sum(representation.atoms[i].atomic_number for i in qm) + len(selection.boundaries) - selection.qm_formal_charge
    unpaired = selection.spin_multiplicity - 1
    if electrons <= 0 or unpaired > electrons or (electrons - unpaired) % 2:
        raise ValueError("catalytic charge, caps and spin change the electron parity/count")
    return tuple(sorted({"requirement.reactive.chemical-admission",
        "requirement.reactive.coupled-hamiltonian-assessment", "requirement.reactive.force-and-geometry-assessment",
        "requirement.reactive.selected-backend-support",
        *({"requirement.reactive.oxygenation-assumption"}
          if selection.gas == "O2" and selection.oxygenation_assumption is None else set())}))
