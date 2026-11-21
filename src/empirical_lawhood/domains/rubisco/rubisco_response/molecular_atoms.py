# SPDX-License-Identifier: MPL-2.0
"""Complete molecular correspondence, separate from preparation admission.

The full atom table remains a scientific operand. Coordinates use the shared
array contract; neither a site subset nor an atom count replaces the table.
No historical inhibited-state record or fixed preparation roster is changed.
"""

from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from typing import ClassVar

from empirical_lawhood.science.models.datasets import ArrayDatasetManifest
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_ids, validate_decimal, validate_nonempty, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.contexts import ChemicalProtocol
from empirical_lawhood.domains.rubisco.rubisco_response.materials import AMINO_ACIDS, RubiscoMaterial, exact, identities


def indices(values, *, count, name, nonempty=False):
    if (type(values) is not tuple or (nonempty and not values)
            or any(type(value) is not int or not 0 <= value < count for value in values)
            or tuple(sorted(set(values))) != values):
        raise ValueError(name + " requires an exact sorted unique atom-index census")


@dataclass(frozen=True, slots=True)
class MolecularResidue(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/molecular-residue"
    residue_id: str
    component: str
    role: str
    chain_id: str | None
    sequence_position_1based: int | None
    sequence_letter: str | None
    author_chain: str | None
    author_number: int | None
    insertion_code: str
    source: ObjectIdentity
    site_id: str | None = None

    def __post_init__(self):
        validate_stable_id(self.residue_id)
        validate_nonempty(self.component, field_name="component")
        exact(self.source, ObjectIdentity)
        if self.role not in {"PROTEIN", "LIGAND", "GAS", "MAGNESIUM", "WATER", "ION"}:
            raise ValueError("molecular residue needs an explicit molecular role")
        protein = self.role == "PROTEIN"
        if protein:
            from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.coordinate_plan import THREE
            validate_stable_id(self.chain_id)
            if (type(self.sequence_position_1based) is not int
                    or self.sequence_position_1based <= 0
                    or self.sequence_letter not in AMINO_ACIDS):
                raise ValueError("protein residue needs its exact complete-sequence position")
            letters = {name: letter for letter, name in THREE.items()}
            letters.update(KCX="K", HID="H", HIE="H", HIP="H", CYX="C")
            if letters.get(self.component) != self.sequence_letter:
                raise ValueError("protein chemical component differs from its selected sequence residue")
        elif any(value is not None for value in
                 (self.chain_id, self.sequence_position_1based, self.sequence_letter)):
            raise ValueError("nonprotein residue cannot claim a protein sequence position")
        if (self.author_chain is None) != (self.author_number is None):
            raise ValueError("structural author chain and residue number must be joined together")
        if self.author_number is not None and (
                type(self.author_number) is not int or type(self.author_chain) is not str):
            raise ValueError("structural author numbering must be exact; blank chains are permitted")
        if type(self.insertion_code) is not str or (self.author_number is None and self.insertion_code):
            raise ValueError("insertion code cannot invent an absent structural residue")
        if self.site_id is not None:
            validate_stable_id(self.site_id)


@dataclass(frozen=True, slots=True)
class MolecularAtom(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/molecular-atom"
    atom_id: str
    residue_id: str
    name: str
    atomic_number: int
    mass_dalton: Decimal
    charge_native: Decimal
    charge_scale_per_electron: Decimal
    parameter_type: str
    source: ObjectIdentity
    source_atom_id: str | None

    def __post_init__(self):
        for value in (self.atom_id, self.residue_id):
            validate_stable_id(value)
        for name in ("name", "parameter_type"):
            validate_nonempty(getattr(self, name), field_name=name)
        if type(self.atomic_number) is not int or not 1 <= self.atomic_number <= 118:
            raise ValueError("physical atom must retain its actual element")
        validate_decimal(self.mass_dalton, field_name="mass_dalton", minimum=Decimal(0))
        validate_decimal(self.charge_native, field_name="charge_native")
        validate_decimal(self.charge_scale_per_electron, field_name="charge_scale_per_electron", minimum=Decimal(0))
        if self.mass_dalton == 0:
            raise ValueError("physical atom cannot have zero mass")
        if self.charge_scale_per_electron == 0:
            raise ValueError("native charge must have an explicit positive scale")
        exact(self.source, ObjectIdentity)
        if self.source_atom_id is not None:
            validate_nonempty(self.source_atom_id, field_name="source_atom_id")

    @property
    def charge_electron(self):
        return Fraction(self.charge_native) / Fraction(self.charge_scale_per_electron)


@dataclass(frozen=True, slots=True)
class MolecularBond(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/molecular-bond"
    first: int
    second: int
    order: Decimal

    def __post_init__(self):
        if type(self.first) is not int or type(self.second) is not int or not 0 <= self.first < self.second:
            raise ValueError("bond must retain two ordered distinct atom indices")
        validate_decimal(self.order, field_name="bond_order", minimum=Decimal(0))
        if self.order == 0:
            raise ValueError("bond order must be positive")


@dataclass(frozen=True, slots=True)
class NativeTopologyBond(CanonicalRecord):
    """An original force-topology edge whose chemical order is unspecified.

    Amber bond tables include geometric H-H water edges and do not encode
    chemical bond orders. A separate chemical graph can annotate selected
    edges with MolecularBond; an unannotated edge never implies order one.
    """
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/native-topology-bond"
    first: int
    second: int

    def __post_init__(self):
        if type(self.first) is not int or type(self.second) is not int or not 0 <= self.first < self.second:
            raise ValueError("native topology edge must retain two ordered distinct atom indices")

    @property
    def order(self):
        return None


@dataclass(frozen=True, slots=True)
class MolecularSite(CanonicalRecord):
    """An explicit site atom join, not proof of protonation or metal chemistry."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/molecular-site"
    site_id: str
    catalytic_residue_id: str
    magnesium_atom_indices: tuple[int, ...]
    ligand_atom_indices: tuple[int, ...]
    gas_atom_indices: tuple[int, ...]
    proton_transfer_atom_indices: tuple[int, ...]
    chemical_graph: ObjectIdentity

    def __post_init__(self):
        validate_stable_id(self.site_id)
        validate_stable_id(self.catalytic_residue_id)
        exact(self.chemical_graph, ObjectIdentity)
        for name in ("magnesium_atom_indices", "ligand_atom_indices", "gas_atom_indices", "proton_transfer_atom_indices"):
            values = getattr(self, name)
            if (type(values) is not tuple or any(type(value) is not int or value < 0 for value in values)
                    or tuple(sorted(set(values))) != values):
                raise ValueError("site atom assignment is not exact sorted unique indices")


@dataclass(frozen=True, slots=True)
class MolecularRepresentation(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/molecular-representation"
    representation_id: str
    material: RubiscoMaterial
    chemistry: ChemicalProtocol
    temperature_k: Decimal
    preparation_protocol: ObjectIdentity
    parameter_model: ObjectIdentity
    raw_topology: ObjectIdentity
    raw_coordinates: ObjectIdentity
    residues: tuple[MolecularResidue, ...]
    # Native order, not lexical atom-id order. Every downstream array uses it.
    atoms: tuple[MolecularAtom, ...]
    bonds: tuple[MolecularBond | NativeTopologyBond, ...]
    sites: tuple[MolecularSite, ...]
    arrays: ArrayDatasetManifest
    sources: tuple[ObjectIdentity, ...]
    interpretation: str = "COMPLETE_SELECTED_REPRESENTATION_NOT_PHYSICAL_OR_CHEMICAL_ADMISSION"

    def __post_init__(self):
        validate_stable_id(self.representation_id)
        exact(self.material, RubiscoMaterial)
        exact(self.chemistry, ChemicalProtocol)
        validate_decimal(self.temperature_k, field_name="temperature_k", minimum=Decimal(0))
        if self.temperature_k == 0:
            raise ValueError("molecular temperature must be a positive explicit selection")
        for row in (self.preparation_protocol, self.parameter_model, self.raw_topology, self.raw_coordinates):
            exact(row, ObjectIdentity)
        identities(self.sources)
        for rows, kind in ((self.residues, MolecularResidue), (self.atoms, MolecularAtom),
                           (self.sites, MolecularSite)):
            if type(rows) is not tuple or not rows:
                raise ValueError("molecular representation omits a complete immutable census")
            for row in rows:
                exact(row, kind)
        if (type(self.bonds) is not tuple or not self.bonds
                or any(type(row) not in {MolecularBond, NativeTopologyBond} for row in self.bonds)):
            raise ValueError("molecular representation requires its complete typed native/chemical edge census")
        require_sorted_unique_ids(self.residues, attribute="residue_id", field_name="residues")
        require_sorted_unique_ids(self.sites, attribute="site_id", field_name="sites")
        if len({atom.atom_id for atom in self.atoms}) != len(self.atoms):
            raise ValueError("full molecular atom census duplicates an identity")
        by_residue = {row.residue_id: row for row in self.residues}
        if {atom.residue_id for atom in self.atoms} != set(by_residue):
            raise ValueError("full atom census omits or invents a selected residue")
        if len({(atom.residue_id, atom.name) for atom in self.atoms}) != len(self.atoms):
            raise ValueError("full atom census duplicates a residue atom name")
        native_origins = [(atom.source, atom.source_atom_id) for atom in self.atoms if atom.source_atom_id is not None]
        if len(set(native_origins)) != len(native_origins):
            raise ValueError("full atom census duplicates one original source atom")
        sequence = {(row.chain_id, row.sequence_position_1based): row.sequence_letter
                    for row in self.residues if row.role == "PROTEIN"}
        expected = {(chain.chain_id, position): letter for chain in self.material.chains
                    for position, letter in enumerate(chain.sequence, 1)}
        if sequence != expected or len(sequence) != sum(row.role == "PROTEIN" for row in self.residues):
            raise ValueError("molecular residues differ from the complete sixteen-chain sequence census")
        author_keys = [(row.source, row.author_chain, row.author_number, row.insertion_code)
                       for row in self.residues if row.author_number is not None]
        if len(set(author_keys)) != len(author_keys):
            raise ValueError("structural author residue mapping is not one-to-one")
        edges = tuple((row.first, row.second) for row in self.bonds)
        if edges != tuple(sorted(set(edges))) or any(row.second >= len(self.atoms) for row in self.bonds):
            raise ValueError("complete bond census duplicates, reorders or escapes physical atoms")
        selected_sites = {row.site_id: row for row in self.chemistry.sites}
        if set(selected_sites) != {row.site_id for row in self.sites}:
            raise ValueError("representation omits an all-site chemical assignment")
        if any(row.site_id is not None and row.site_id not in selected_sites for row in self.residues):
            raise ValueError("residue names an absent chemical site")
        catalytic = []
        for row in self.sites:
            selected = selected_sites[row.site_id]
            residue = by_residue.get(row.catalytic_residue_id)
            if (residue is None or residue.role != "PROTEIN" or residue.site_id != row.site_id
                    or (residue.chain_id, residue.sequence_position_1based, residue.sequence_letter)
                    != (selected.lsu_chain_id, selected.catalytic_lysine_position_1based, "K")
                    or residue.component != ("KCX" if selected.carbamylated else "LYS")):
                raise ValueError("site loses its exact selected catalytic lysine correspondence")
            catalytic.append(residue.residue_id)
            for name in ("magnesium_atom_indices", "ligand_atom_indices", "gas_atom_indices", "proton_transfer_atom_indices"):
                indices(getattr(row, name), count=len(self.atoms), name=name)
            for role, actual in (("MAGNESIUM", row.magnesium_atom_indices), ("LIGAND", row.ligand_atom_indices),
                                 ("GAS", row.gas_atom_indices)):
                expected_atoms = tuple(i for i, atom in enumerate(self.atoms)
                    if by_residue[atom.residue_id].role == role and by_residue[atom.residue_id].site_id == row.site_id)
                if actual != expected_atoms:
                    raise ValueError("site mapping omits or substitutes its full ligand/metal atom census")
            if (len(row.magnesium_atom_indices) != int(selected.magnesium_bound)
                    or any(self.atoms[i].atomic_number != 12 for i in row.magnesium_atom_indices)):
                raise ValueError("site magnesium differs from its explicit activation selection")
            if ((selected.ligand_state == "EMPTY") != (not row.ligand_atom_indices)
                    or row.chemical_graph != selected.ligand_chemical_graph):
                raise ValueError("site ligand mapping changes its selected chemical graph")
        if len(set(catalytic)) != 8:
            raise ValueError("all sites must retain distinct catalytic residues")
        if any(row.role in {"MAGNESIUM", "LIGAND", "GAS"} and row.site_id is None for row in self.residues):
            raise ValueError("ligand/activation atoms cannot escape the complete site denominator")
        exact(self.arrays, ArrayDatasetManifest)
        if (tuple(row.name for row in self.arrays.members) != ("coordinates-angstrom",)
                or self.arrays.members[0].shape != (len(self.atoms), 3)
                or self.arrays.members[0].dtype != "<f8" or not self.arrays.members[0].finite_required
                or self.arrays.scientific_references != tuple(sorted(
                    (self.raw_coordinates, self.raw_topology), key=lambda row: row.object_id))):
            raise ValueError("molecular arrays must bind the complete raw topology/coordinate order")
        required = {self.raw_topology, self.raw_coordinates, self.preparation_protocol, self.parameter_model,
                    *self.material.sources, *self.chemistry.sources,
                    *(row.source for row in self.residues), *(row.source for row in self.atoms)}
        if not required.issubset(self.sources):
            raise ValueError("molecular representation drops its exact source closure")
        if self.interpretation != "COMPLETE_SELECTED_REPRESENTATION_NOT_PHYSICAL_OR_CHEMICAL_ADMISSION":
            raise ValueError("selected molecular representation cannot assert preparation admission")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.representation_id, self)


def validate_amber_atom_correspondence(representation, raw_prmtop):
    """Join every independently parsed Amber atom, parameter and bond to the map.

    Source/receipt authentication belongs to the caller. The raw topology digest
    is checked here; a producer's summary or a site-only map cannot replace it.
    Amber stores scaled charges. Compare exactly in that native convention.
    """
    from hashlib import sha256
    from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.amber_parameters import assigned_census_supported_inactive14, read_prmtop
    exact(representation, MolecularRepresentation)
    if (type(raw_prmtop) is not bytes
            or sha256(raw_prmtop).hexdigest() != representation.raw_topology.object_fingerprint):
        raise ValueError("raw topology differs from its exact selected source bytes")
    census = assigned_census_supported_inactive14(read_prmtop(raw_prmtop.decode("ascii")))
    if len(representation.atoms) != census["term_census"]["atoms"]:
        raise ValueError("atom correspondence changes the complete native atom denominator")
    residue_index = -1
    starts = set(value - 1 for value in census["residue_starts"])
    residue_ids = []
    by_residue = {row.residue_id: row for row in representation.residues}
    for i, atom in enumerate(representation.atoms):
        if i in starts:
            residue_index += 1
            residue_ids.append(atom.residue_id)
        if atom.residue_id != residue_ids[-1]:
            raise ValueError("atom correspondence crosses a native residue boundary")
        residue = by_residue[atom.residue_id]
        if ((atom.name, atom.atomic_number, atom.mass_dalton, atom.parameter_type, residue.component)
                != (census["atom_names"][i], census["atomic_numbers"][i], census["masses"][i],
                    census["atom_types"][i], census["residue_names"][residue_index])
                or (atom.charge_native, atom.charge_scale_per_electron)
                != (census["charges_scaled"][i], Decimal("18.2223"))):
            raise ValueError("atom correspondence changes a native element, mass, charge, type or residue")
    if len(set(residue_ids)) != len(residue_ids):
        raise ValueError("native residue correspondence is not one-to-one")
    actual_bonds = set()
    for name in ("BONDS_INC_HYDROGEN", "BONDS_WITHOUT_HYDROGEN"):
        actual_bonds.update(tuple(sorted((row[0] // 3, row[1] // 3)))
                            for row in census["indexed_bonded_terms"][name])
    if actual_bonds != {(row.first, row.second) for row in representation.bonds}:
        raise ValueError("atom correspondence drops or invents native bonds")
    return census
