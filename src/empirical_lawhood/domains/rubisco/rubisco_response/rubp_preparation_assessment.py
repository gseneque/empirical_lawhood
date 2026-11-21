# SPDX-License-Identifier: MPL-2.0
"""Independent source, valence, charge and stereo checks for prepared RuBP.

The assessor uses a separate CIF parser and exact signed coordinate volumes.
It enters no ligand constructor, force field, molecular backend or native task.
"""

from collections import Counter
from dataclasses import dataclass
from fractions import Fraction
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_insilico_mechanism.contracts import Exact
from empirical_lawhood.domains.rubisco.rubisco_insilico_structure.independent_cif import read_cif
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_strings, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_chemistry import LigandChemicalGraph
from empirical_lawhood.domains.rubisco.rubisco_response.rubp_preparation import RuBPTetraanionPreparation


@dataclass(frozen=True, slots=True)
class RuBPTetraanionAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/rubp-tetraanion-assessment"
    assessment_id: str
    preparation: ObjectIdentity
    chemical_graph: ObjectIdentity
    atom_count: int
    bond_count: int
    electron_count: int
    graph_formal_charge: int
    stereocentre_signed_volumes_angstrom3: tuple[tuple[str, Exact], ...]
    findings: tuple[str, ...]
    graph_disposition: A
    enzyme_preparation_admission: A = A.UNEVALUABLE
    parameter_admission: A = A.UNEVALUABLE
    new_native_calls: int = 0

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        for row in (self.preparation, self.chemical_graph):
            exact(row, ObjectIdentity)
        if (self.preparation.object_schema, self.preparation.object_version) != (
                RuBPTetraanionPreparation.SCHEMA, RuBPTetraanionPreparation.VERSION):
            raise ValueError("RuBP assessment changes its retained preparation type")
        if (self.chemical_graph.object_schema, self.chemical_graph.object_version) != (
                LigandChemicalGraph.SCHEMA, LigandChemicalGraph.VERSION):
            raise ValueError("RuBP assessment changes its retained chemical graph type")
        for name in ("atom_count", "bond_count", "electron_count"):
            if type(getattr(self, name)) is not int or getattr(self, name) < 0:
                raise ValueError("RuBP assessment needs exact complete population counts")
        if type(self.graph_formal_charge) is not int:
            raise ValueError("RuBP assessment needs an integer formal charge")
        require_sorted_unique_strings(self.findings, field_name="findings")
        if self.graph_disposition is not (A.FALSIFIED if self.findings else A.SATISFIED):
            raise ValueError("RuBP graph disposition contradicts its independent findings")
        if (self.enzyme_preparation_admission is not A.UNEVALUABLE or self.parameter_admission is not A.UNEVALUABLE
                or type(self.new_native_calls) is not int or self.new_native_calls != 0):
            raise ValueError("RuBP graph checking cannot admit an enzyme or parameter set")
        if (type(self.stereocentre_signed_volumes_angstrom3) is not tuple
                or tuple(row[0] for row in self.stereocentre_signed_volumes_angstrom3) != ("C3", "C4")):
            raise ValueError("RuBP assessment drops a selected stereocentre")
        for _, value in self.stereocentre_signed_volumes_angstrom3:
            exact(value, Exact)
        if self.graph_disposition is A.SATISFIED and (
                (self.atom_count, self.bond_count, self.electron_count, self.graph_formal_charge) != (26, 25, 160, -4)
                or any(value.fraction >= 0 for _, value in self.stereocentre_signed_volumes_angstrom3)):
            raise ValueError("satisfied RuBP assessment contradicts its complete graph or stereochemistry")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.assessment_id, self)


def assess_rubp_tetraanion(prepared, *, assessment_id):
    """Reconcile original chemistry and assess the constructed ligand independently."""
    exact(prepared, RuBPTetraanionPreparation)
    source = prepared.original_component
    source.__post_init__()
    tables = read_cif(source.raw_utf8)
    graph = prepared.chemical_graph
    findings = set()
    definition, = tables["_chem_comp"]
    raw_atoms = tables["_chem_comp_atom"]
    raw = {row["atom_id"]: row for row in raw_atoms}
    protons = {"HOP2", "HOP3", "HOP5", "HOP6"}
    actual = {row.native_atom_name: row for row in graph.atoms}
    if (definition["id"] != "RUB" or definition["pdbx_formal_charge"] != "0"
            or len(raw_atoms) != len(raw) or len(raw) != 30
            or Counter(row["type_symbol"] for row in raw_atoms) != {"C": 5, "H": 12, "O": 11, "P": 2}
            or any(row["comp_id"] != "RUB" or int(row["charge"]) != 0 for row in raw_atoms)):
        findings.add("original-neutral-component")
    if len(actual) != len(graph.atoms) or set(actual) != set(raw) - protons:
        findings.add("complete-atom-correspondence")
    if Counter(row.atomic_number for row in graph.atoms) != {6: 5, 1: 8, 8: 11, 15: 2}:
        findings.add("tetraanion-formula")
    atomic_numbers = {"H": 1, "C": 6, "O": 8, "P": 15}
    for name, atom in actual.items():
        expected_charge = -1 if name in {"O2P", "O3P", "O5P", "O6P"} else 0
        if (name not in raw or atom.atomic_number != atomic_numbers.get(raw[name]["type_symbol"])
                or atom.formal_charge != expected_charge or atom.atom_id != "rubp." + name.lower()):
            findings.add("atom-element-charge-or-origin")
    bonds = {frozenset((graph.atoms[row.first].native_atom_name, graph.atoms[row.second].native_atom_name)):
             Fraction(row.order) for row in graph.bonds}
    original_edges = {}
    for row in tables["_chem_comp_bond"]:
        pair = frozenset((row["atom_id_1"], row["atom_id_2"]))
        order = {"SING": 1, "DOUB": 2}.get(row["value_order"])
        if len(pair) != 2 or pair in original_edges or order is None or row["comp_id"] != "RUB":
            findings.add("original-bond-census")
        original_edges[pair] = order
    expected_edges = {pair: order for pair, order in original_edges.items() if not pair.intersection(protons)}
    if bonds != expected_edges or len(graph.bonds) != 25:
        findings.add("retained-bond-orders")
    # Independent chemical specification: the two terminal phosphomonoesters,
    # five-carbon keto chain and all eight remaining hydrogens. Source labels
    # and atom counts alone cannot exclude a different constitutional isomer.
    single_bonds = (
        ("C1", "C2"), ("C2", "C3"), ("C3", "C4"), ("C4", "C5"),
        ("C1", "O1"), ("C3", "O3"), ("C4", "O4"), ("C5", "O5"),
        ("O1", "P1"), ("O5", "P2"), ("P1", "O2P"), ("P1", "O3P"),
        ("P2", "O5P"), ("P2", "O6P"), ("C1", "H11"), ("C1", "H12"),
        ("C3", "H3"), ("C4", "H4"), ("C5", "H51"), ("C5", "H52"),
        ("O3", "HO3"), ("O4", "HO4"),
    )
    constitutional_graph = {frozenset(edge): 1 for edge in single_bonds}
    constitutional_graph.update({frozenset(edge): 2 for edge in (("C2", "O2"), ("P1", "O1P"), ("P2", "O4P"))})
    if bonds != constitutional_graph:
        findings.add("keto-rubp-constitutional-graph")
    for proton, oxygen in (("HOP2", "O2P"), ("HOP3", "O3P"), ("HOP5", "O5P"), ("HOP6", "O6P")):
        edges = {edge: order for edge, order in original_edges.items() if proton in edge}
        if edges != {frozenset((proton, oxygen)): 1} or raw.get(proton, {}).get("type_symbol") != "H":
            findings.add("removed-phosphate-protons")
    for name, atom in actual.items():
        valence = sum(order for pair, order in bonds.items() if name in pair)
        expected = {1: 1, 6: 4, 8: 2 + atom.formal_charge, 15: 5}.get(atom.atomic_number)
        if valence != expected:
            findings.add("selected-atom-valence")
    electrons = sum(row.atomic_number - row.formal_charge for row in graph.atoms)
    if graph.formal_charge != -4 or electrons != 160 or electrons % 2:
        findings.add("tetraanion-charge-electron-count")
    if bonds.get(frozenset(("C2", "O2"))) != 2 or bonds.get(frozenset(("C2", "C3"))) != 1:
        findings.add("keto-state")
    positions = {name: tuple(Fraction(value) for value in xyz)
                 for name, xyz in prepared.template_coordinates_angstrom}
    for name, xyz in positions.items():
        if name not in raw or xyz != tuple(Fraction(raw[name]["pdbx_model_Cartn_" + axis + "_ideal"])
                                         for axis in "xyz"):
            findings.add("original-template-coordinate-correspondence")
    if {name: row["pdbx_stereo_config"] for name, row in raw.items()
            if row["pdbx_stereo_config"] != "N"} != {"C3": "R", "C4": "R"}:
        findings.add("original-stereochemical-census")
    volumes = []
    # For the keto graph these orders follow O > C > H and the next shell's
    # O,O,C > O,C,H at C3, and O,C,H > O,H,H at C4. Negative determinant is R.
    for centre, names in (("C3", ("O3", "C2", "C4", "H3")), ("C4", ("O4", "C3", "C5", "H4"))):
        if raw.get(centre, {}).get("pdbx_stereo_config") != "R":
            findings.add("original-stereochemical-label")
        if not set(names).issubset(positions):
            determinant = Fraction(0)
            findings.add("stereocentre-atom-census")
        else:
            first, second, third, fourth = (positions[name] for name in names)
            a, b, c = (tuple(value - origin for value, origin in zip(point, fourth, strict=True))
                       for point in (first, second, third))
            determinant = (a[0] * (b[1] * c[2] - b[2] * c[1])
                           - a[1] * (b[0] * c[2] - b[2] * c[0])
                           + a[2] * (b[0] * c[1] - b[1] * c[0]))
            if any(bonds.get(frozenset((centre, name))) != 1 for name in names):
                findings.add("stereocentre-substituents")
        volumes.append((centre, Exact.of(determinant)))
        if determinant >= 0:
            findings.add("template-stereochemistry")
    return RuBPTetraanionAssessment(assessment_id, prepared.identity, graph.identity, len(graph.atoms),
        len(graph.bonds), electrons, graph.formal_charge, tuple(volumes), tuple(sorted(findings)),
        A.FALSIFIED if findings else A.SATISFIED)
