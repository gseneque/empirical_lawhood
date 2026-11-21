# SPDX-License-Identifier: MPL-2.0
"""Construct the selected keto RuBP tetraanion from an explicit CCD source.

This is a chemical graph and unrelaxed ligand template. It does not transplant
an inhibited pose, construct an enzyme, parameterize it or enter a native task.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_insilico_structure.contracts import StructuralSourceMember
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_decimal, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_atoms import MolecularBond
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_chemistry import LigandAtom, LigandChemicalGraph


REMOVED_PROTONS = ("HOP2", "HOP3", "HOP5", "HOP6")
ANION_OXYGENS = ("O2P", "O3P", "O5P", "O6P")
STEREOCENTRES = (("C3", "R", ("O3", "C2", "C4", "H3")),
                 ("C4", "R", ("O4", "C3", "C5", "H4")))
TEMPLATE_SCOPE = "CCD_IDEAL_COORDINATES_UNRELAXED_NOT_GP_MG_ENZYME_COORDINATES"
REQUIREMENTS = (
    "requirement.rubp-tetraanion.active-site-placement-and-stereochemistry",
    "requirement.rubp-tetraanion.assessed-nonstandard-parameters",
    "requirement.rubp-tetraanion.enzyme-protonation-and-metal-coordination",
    "requirement.rubp-tetraanion.full-paired-assembly-and-force-assessment",
)


def component_source_identity(source):
    exact(source, StructuralSourceMember)
    return ObjectIdentity.from_record("source.chemical-component." + source.sha256, source)


@dataclass(frozen=True, slots=True)
class RuBPTetraanionPreparation(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/rubp-tetraanion-preparation"
    preparation_id: str
    original_component: StructuralSourceMember
    chemical_graph: LigandChemicalGraph
    removed_source_proton_names: tuple[str, ...]
    # Each tuple lists the centre, absolute configuration and four substituents
    # in decreasing CIP priority for this explicitly selected keto graph.
    stereocentres: tuple[tuple[str, str, tuple[str, ...]], ...]
    template_coordinates_angstrom: tuple[tuple[str, tuple[Decimal, ...]], ...]
    selected_multiplicity: int = 1
    design: str = "GP-WT-I95M-REF1_KETO_RUBP_TETRAANION"
    coordinate_scope: str = TEMPLATE_SCOPE
    unresolved_requirement_ids: tuple[str, ...] = REQUIREMENTS
    new_native_calls: int = 0

    def __post_init__(self):
        validate_stable_id(self.preparation_id)
        exact(self.original_component, StructuralSourceMember)
        exact(self.chemical_graph, LigandChemicalGraph)
        if (self.chemical_graph.ligand_state != "RUBP"
                or self.chemical_graph.sources != (component_source_identity(self.original_component),)):
            raise ValueError("RuBP preparation loses its original chemical source or ligand meaning")
        if (type(self.removed_source_proton_names) is not tuple
                or self.removed_source_proton_names != REMOVED_PROTONS):
            raise ValueError("RuBP preparation must retain all four removed phosphate protons")
        if self.stereocentres != STEREOCENTRES:
            raise ValueError("RuBP preparation changes its selected D-ribulose stereochemistry")
        if (type(self.template_coordinates_angstrom) is not tuple
                or tuple(row[0] for row in self.template_coordinates_angstrom)
                != tuple(row.native_atom_name for row in self.chemical_graph.atoms)):
            raise ValueError("RuBP template omits or reorders a graph atom")
        for _, coordinates in self.template_coordinates_angstrom:
            if type(coordinates) is not tuple or len(coordinates) != 3:
                raise ValueError("RuBP template needs all three Cartesian coordinates")
            for coordinate in coordinates:
                validate_decimal(coordinate, field_name="template_coordinate_angstrom")
        if (type(self.selected_multiplicity) is not int or self.selected_multiplicity != 1
                or self.design != "GP-WT-I95M-REF1_KETO_RUBP_TETRAANION"
                or self.coordinate_scope != TEMPLATE_SCOPE
                or self.unresolved_requirement_ids != REQUIREMENTS
                or type(self.new_native_calls) is not int or self.new_native_calls != 0):
            raise ValueError("ligand construction cannot establish an enzyme, parameters or native execution")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.preparation_id, self)


def prepare_rubp_tetraanion(source, *, preparation_id):
    """Remove the four explicit phosphate protons and retain every other atom.

    Source coordinates are a template only. The source hydrogen removal changes
    the ligand charge by -4 and leaves its electron count unchanged.
    """
    from empirical_lawhood.domains.rubisco.rubisco_insilico_structure.science import cif_tables

    exact(source, StructuralSourceMember)
    tables = cif_tables(source.raw_utf8)
    definition, = tables["_chem_comp"]
    source_atoms, source_bonds = tables["_chem_comp_atom"], tables["_chem_comp_bond"]
    atoms = {row["atom_id"]: row for row in source_atoms}
    if (definition["id"] != "RUB" or definition["formula"] != "C5 H12 O11 P2"
            or definition["pdbx_formal_charge"] != "0"
            or len(atoms) != 30 or len(source_atoms) != 30
            or any(row["comp_id"] != "RUB" or row["charge"] != "0" for row in source_atoms)):
        raise ValueError("RuBP preparation needs the complete explicit neutral RUB dictionary")
    elements = {"C": 6, "H": 1, "O": 8, "P": 15}
    edges = {tuple(sorted((row["atom_id_1"], row["atom_id_2"]))): row["value_order"]
             for row in source_bonds}
    if (len(edges) != len(source_bonds) or len(edges) != 29
            or any(name not in atoms for edge in edges for name in edge)
            or any(row["comp_id"] != "RUB" for row in source_bonds)
            or any(order not in {"SING", "DOUB"} for order in edges.values())):
        raise ValueError("RuBP preparation needs the complete source bond census")
    for proton, oxygen in zip(REMOVED_PROTONS, ANION_OXYGENS, strict=True):
        neighbours = [edge for edge in edges if proton in edge]
        if (atoms[proton]["type_symbol"] != "H" or atoms[oxygen]["type_symbol"] != "O"
                or neighbours != [tuple(sorted((proton, oxygen)))]
                or edges[neighbours[0]] != "SING"):
            raise ValueError("RuBP phosphate proton removal changes a source atom or bond")
    if (edges.get(("C2", "O2")) != "DOUB" or edges.get(("C2", "C3")) != "SING"
            or tuple(sorted((name, row["pdbx_stereo_config"]) for name, row in atoms.items()
                            if row["pdbx_stereo_config"] != "N")) != (("C3", "R"), ("C4", "R"))):
        raise ValueError("RuBP source is not the selected keto D-ribulose graph")
    selected = tuple(sorted(set(atoms) - set(REMOVED_PROTONS)))
    graph_atoms = tuple(LigandAtom("rubp." + name.lower(), name, elements[atoms[name]["type_symbol"]],
                                  -1 if name in ANION_OXYGENS else 0) for name in selected)
    index = {name: i for i, name in enumerate(selected)}
    bonds = tuple(MolecularBond(index[first], index[second], Decimal(1 if order == "SING" else 2))
                  for (first, second), order in sorted(edges.items())
                  if first in index and second in index)
    graph = LigandChemicalGraph("graph." + preparation_id, "RUBP", graph_atoms, bonds, -4,
                                (component_source_identity(source),))
    coordinates = tuple((name, tuple(Decimal(atoms[name]["pdbx_model_Cartn_" + axis + "_ideal"])
                                     for axis in "xyz")) for name in selected)
    return RuBPTetraanionPreparation(preparation_id, source, graph, REMOVED_PROTONS, STEREOCENTRES, coordinates)
