# SPDX-License-Identifier: MPL-2.0
"""Read selected Amber residue sources without a native engine.

Connectivity and charge correspondence do not validate a force field. In
particular, keto RuBP parameters cannot represent a reactive enolate, and
the anionic KCX template cannot represent a protonated carbamate.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.contracts import SourceMember
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_decimal, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.rubp_preparation import RuBPTetraanionPreparation
from empirical_lawhood.domains.rubisco.rubisco_response.rubp_preparation_assessment import assess_rubp_tetraanion


RUBP_NAMES = (("H11", "H1C1"), ("H12", "H2C1"), ("H3", "HC3"),
              ("H4", "HC4"), ("H51", "H1C5"), ("H52", "H2C5"))
ELEMENTS = {"c": 6, "c3": 6, "h1": 1, "ho": 1, "o": 8, "oh": 8, "os": 8, "p5": 15,
            "C": 6, "CT": 6, "H": 1, "H1": 1, "HC": 1, "N": 7, "O": 8, "O2": 8}
KCX_ELEMENTS = tuple(sorted({**{n: 6 for n in ("CA", "CB", "CG", "CD", "CE", "CX", "C")},
    **{n: 7 for n in ("N", "NZ")}, **{n: 8 for n in ("O", "OQ1", "OQ2")},
    **{n: 1 for n in ("HN1", "HA", "HB2", "HB3", "HG2", "HG3", "HD2", "HD3", "HE2", "HE3", "HZ")}}.items()))
KCX_EDGES = tuple(sorted(tuple(sorted(edge)) for edge in (
    ("N", "HN1"), ("N", "CA"), ("CA", "HA"), ("CA", "CB"), ("CA", "C"), ("C", "O"),
    ("CB", "HB2"), ("CB", "HB3"), ("CB", "CG"), ("CG", "HG2"), ("CG", "HG3"), ("CG", "CD"),
    ("CD", "HD2"), ("CD", "HD3"), ("CD", "CE"), ("CE", "HE2"), ("CE", "HE3"), ("CE", "NZ"),
    ("NZ", "HZ"), ("NZ", "CX"), ("CX", "OQ1"), ("CX", "OQ2"))))


@dataclass(frozen=True, slots=True)
class AmberTemplateAtom(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/amber-template-atom"
    source_index: int
    name: str
    atom_type: str
    parent_index: int
    partial_charge_e: Decimal

    def __post_init__(self):
        if (type(self.source_index) is not int or self.source_index < 4 or not self.name
                or type(self.parent_index) is not int or not 1 <= self.parent_index < self.source_index
                or self.atom_type not in ELEMENTS):
            raise ValueError("Amber template changes its selected atom/type/tree convention")
        validate_decimal(self.partial_charge_e, field_name="partial_charge_e")


@dataclass(frozen=True, slots=True)
class AmberResidueTemplate(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/amber-residue-template"
    template_id: str
    source: ObjectIdentity
    residue_name: str
    atoms: tuple[AmberTemplateAtom, ...]
    bonds: tuple[tuple[str, str], ...]
    impropers: tuple[tuple[str, ...], ...]
    partial_charge_e: Decimal

    def __post_init__(self):
        validate_stable_id(self.template_id)
        exact(self.source, ObjectIdentity)
        if self.source.object_schema != SourceMember.SCHEMA or self.residue_name not in ("RUB", "KCX"):
            raise ValueError("Amber template needs its explicit selected residue source")
        if type(self.atoms) is not tuple or not self.atoms:
            raise ValueError("Amber template needs every original atom")
        for atom in self.atoms:
            exact(atom, AmberTemplateAtom)
        names = {a.name for a in self.atoms}
        if (len(names) != len(self.atoms) or tuple(a.source_index for a in self.atoms) != tuple(range(4, 4 + len(self.atoms)))
                or self.bonds != tuple(sorted(set(self.bonds)))
                or any(len(e) != 2 or e[0] >= e[1] or not set(e).issubset(names) for e in self.bonds)
                or type(self.impropers) is not tuple
                or any(len(row) != 4 or not set(row).issubset(names | {"-M", "+M"}) for row in self.impropers)):
            raise ValueError("Amber template loses a complete atom/bond/improper denominator")
        validate_decimal(self.partial_charge_e, field_name="partial_charge_e")
        if sum((a.partial_charge_e for a in self.atoms), Decimal(0)) != self.partial_charge_e:
            raise ValueError("Amber template changes the original partial-charge sum")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.template_id, self)


def read_amber_template(source, *, template_id):
    """Read the selected INT/OMIT-DU layout, refusing unhandled controls."""
    exact(source, SourceMember)
    lines = source.raw_utf8.splitlines()
    headers = [i for i, line in enumerate(lines) if len(line.split()) == 3 and line.split()[1] == "INT"]
    if len(headers) != 1:
        raise ValueError("Amber template requires one INT residue")
    start = headers[0]
    residue, _, code = lines[start].split()
    if (residue not in ("KCX", "RUB") or code != "0" or lines[start+1].split() != ["CORRECT", "OMIT", "DU", "BEG"]
            or Decimal(lines[start+2].strip()) != 0):
        raise ValueError("Amber template has an unsupported coordinate/charge control")
    state, rows, loops, impropers = "ATOMS", [], [], []
    done = False
    stopped = False
    for line in lines[start+3:]:
        tokens = line.split()
        if not tokens:
            continue
        if tokens == ["LOOP"] and state == "ATOMS":
            state = "LOOP"
        elif tokens == ["IMPROPER"] and state in ("ATOMS", "LOOP"):
            state = "IMPROPER"
        elif tokens == ["DONE"] and not done:
            done, state = True, "DONE"
        elif tokens == ["STOP"] and state == "DONE" and not stopped:
            stopped = True
        elif state == "ATOMS":
            if len(tokens) != 11:
                raise ValueError("Amber template loses an exact atom row")
            index, name, typ, tree = tokens[:4]
            index, parent, angle, torsion = (int(tokens[j]) for j in (0, 4, 5, 6))
            if index != len(rows)+1 or tree not in ("M", "S", "E", "B", "3"):
                raise ValueError("Amber template changes its tree order")
            values = tuple(Decimal(v) for v in tokens[7:])
            if any(not v.is_finite() for v in values):
                raise ValueError("Amber template contains nonfinite coordinates/charges")
            if index <= 3:
                if (name, typ, tree, parent, angle, torsion, values[-1]) != ("DUMM", "DU", "M", index-1, index-2, index-3, Decimal(0)):
                    raise ValueError("Amber template changes the three dummy reference atoms")
            elif not (1 <= parent < index and 1 <= angle < index and 1 <= torsion < index
                      and len({parent, angle, torsion}) == 3 and values[0] > 0 and 0 < values[1] < 180):
                raise ValueError("Amber template changes an internal-coordinate reference")
            rows.append((index, name, typ, parent, values[-1]))
        elif state == "LOOP":
            if len(tokens) != 2:
                raise ValueError("Amber template has an unsupported loop bond")
            loops.append(tuple(sorted(tokens)))
        elif state == "IMPROPER":
            if len(tokens) != 4:
                raise ValueError("Amber template has an incomplete improper")
            impropers.append(tuple(tokens))
        else:
            raise ValueError("Amber template appends an unhandled control or residue")
    if not done or not stopped or len(rows) <= 3:
        raise ValueError("Amber template has no complete terminator or atoms")
    atoms = tuple(AmberTemplateAtom(*row) for row in rows[3:])
    names = {row.source_index: row.name for row in atoms}
    bonds = [tuple(sorted((row.name, names[row.parent_index]))) for row in atoms if row.parent_index in names]
    bonds.extend(loops)
    if len(bonds) != len(set(bonds)):
        raise ValueError("Amber template duplicates a covalent bond")
    return AmberResidueTemplate(template_id, ObjectIdentity.from_record(source.member_id, source), residue, atoms,
        tuple(sorted(bonds)), tuple(impropers), sum((a.partial_charge_e for a in atoms), Decimal(0)))


def assess_initial_templates(rubp, kcx, ligand):
    """Compare every template atom and edge with the selected initial chemistry.

    PREP has no chemical bond orders. The separate ligand graph owns them.
    This comparison cannot promote fixed-topology force parameters to reactive
    surfaces or establish accuracy of their numerical coefficients.
    """
    exact(rubp, AmberResidueTemplate)
    exact(kcx, AmberResidueTemplate)
    exact(ligand, RuBPTetraanionPreparation)
    if assess_rubp_tetraanion(ligand, assessment_id="assessment.amber-template.ligand").graph_disposition is not AssessmentDisposition.SATISFIED:
        raise ValueError("initial Amber templates require independently assessed keto RuBP")
    if rubp.residue_name != "RUB" or kcx.residue_name != "KCX":
        raise ValueError("initial templates substitute their selected chemical roles")
    mapping = dict(RUBP_NAMES)
    expected_atoms = {mapping.get(a.native_atom_name, a.native_atom_name): a.atomic_number for a in ligand.chemical_graph.atoms}
    actual_atoms = {a.name: ELEMENTS[a.atom_type] for a in rubp.atoms}
    graph = ligand.chemical_graph
    expected_edges = tuple(sorted(tuple(sorted(mapping.get(graph.atoms[i].native_atom_name, graph.atoms[i].native_atom_name)
        for i in (bond.first, bond.second))) for bond in graph.bonds))
    if (expected_atoms != actual_atoms or rubp.bonds != expected_edges
            or {a.name: a.atom_type for a in rubp.atoms}.get("C2") != "c"
            or {a.name: a.atom_type for a in rubp.atoms}.get("O2") != "o"
            or rubp.impropers != (("C3", "C1", "C2", "O2"),)):
        raise ValueError("RuBP template differs from the full selected keto tetraanion graph")
    if (tuple(sorted((a.name, ELEMENTS[a.atom_type]) for a in kcx.atoms)) != KCX_ELEMENTS or kcx.bonds != KCX_EDGES
            or any(a.atom_type != "C" for a in kcx.atoms if a.name in ("CX", "C"))
            or any(a.atom_type != "O2" for a in kcx.atoms if a.name in ("OQ1", "OQ2"))
            or kcx.impropers != (("-M", "CA", "N", "HN1"), ("CX", "CE", "NZ", "HZ"),
                                 ("NZ", "OQ1", "CX", "OQ2"), ("CA", "+M", "C", "O"))):
        raise ValueError("KCX template differs from the full anionic carbamylated peptide graph")
    # Source charges have finite decimal precision. This tolerance admits
    # rounding of the sum, not alteration or normalization of any charge.
    if abs(rubp.partial_charge_e + 4) > Decimal("0.00005") or abs(kcx.partial_charge_e + 1) > Decimal("0.00005"):
        raise ValueError("initial template partial charges disagree with selected integer charges")
    return {"rubp_atoms": len(rubp.atoms), "rubp_bonds": len(rubp.bonds), "rubp_charge_e": str(rubp.partial_charge_e),
        "kcx_atoms": len(kcx.atoms), "kcx_bonds": len(kcx.bonds), "kcx_charge_e": str(kcx.partial_charge_e),
        "ligand_name_map": tuple(sorted((a.native_atom_name, mapping.get(a.native_atom_name, a.native_atom_name)) for a in graph.atoms)),
        "graph_correspondence": "SATISFIED", "parameter_accuracy": "UNEVALUABLE", "reactive_states": "UNEVALUABLE",
        "scope": "KETO_RUBP4_MINUS_AND_ANIONIC_KCX_STARTING_TEMPLATES_ONLY"}
