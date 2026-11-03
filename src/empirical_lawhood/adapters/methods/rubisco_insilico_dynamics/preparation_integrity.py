# SPDX-License-Identifier: MPL-2.0
"""Additive complete preparation integrity; legacy records remain readable.

The independent assessor reads retained raw Amber/PDB text, never the native
producer or its parameter enumeration. Assignment completeness does not
establish an acceptable geometry, force-field accuracy, ensemble or kinetics.
"""

from bisect import bisect_right
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal as D
from fractions import Fraction
from hashlib import sha256
import json
from itertools import product
from math import ceil, floor
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id

from . import contracts as c
from .amber_parameters import validate_assignment


PRECEDENCE = (A.UNEVALUABLE, A.REFUSED, A.FALSIFIED, A.UNSUPPORTED, A.NOT_ATTEMPTED, A.SATISFIED)
METHOD_DESCRIPTION = (
    "Complete immutable six-material/two-joint/two-parameter 24-model denominator; "
    "independent fixed-column Amber/PDB, complete actual residue/atom and original-source joins; "
    "exact selected ParmEd binary64 conversions including all mixing/exclusion rows; "
    "all six typed dispositions retained; UNEVALUABLE,REFUSED,FALSIFIED,UNSUPPORTED,NOT_ATTEMPTED,SATISFIED scalar order; "
    "assignment consistency cannot certify geometry, force-field accuracy, native-call coverage or kinetics."
)
METHOD = ObjectIdentity("method.rubisco-dynamics.independent-preparation-integrity",
    "empirical-lawhood/rubisco-insilico-dynamics/preparation-integrity-method", "1.0.0", sha256(METHOD_DESCRIPTION.encode()).hexdigest())
SOURCE_CONVERSIONS = (
    ("parmed/amber/_amberparm.py", "be23837b91fdda1c12165ea5a29000a157ef2a56086ca92e334540ddd5adc70d"),
    ("parmed/amber/amberformat.py", "00f03062ce3a56bdcc4542bf89c8448d7cc4d1c59538b4382944aece9c415f2a"),
    ("parmed/constants.py", "7d9e1c33f487c3f9a59a56840e8767e66419e076e7755b89f5a4bafb11aeeeda"),
    ("parmed/topologyobjects.py", "6ffac900b2f177ca64e2cf701a0b0bcf6301c42e3d2a98bc3d4995eee12250b8"),
)
AMINO = dict(zip(("ALA","CYS","ASP","GLU","PHE","GLY","HIS","ILE","LYS","LEU","MET","ASN","PRO","GLN","ARG","SER","THR","VAL","TRP","TYR"),"ACDEFGHIKLMNPQRSTVWY",strict=True))
AMINO.update(KCX="K",HID="H",HIE="H",HIP="H",CYX="C")


def disposition_census(dispositions):
    if type(dispositions) is not tuple or len(dispositions) != len(c.model_roster()):
        raise ValueError("preparation integrity requires the complete frozen 24-model denominator")
    ids = tuple(row[0] for row in dispositions)
    expected = tuple("model."+".".join(row) for row in c.model_roster())
    if ids != expected:
        raise ValueError("preparation integrity changes exact model identities/order")
    if any(type(row[1]) is not A for row in dispositions):
        raise ValueError("preparation integrity requires every typed disposition")
    if any(type(row) is not tuple or len(row) != 3 or type(row[2]) is not tuple or any(type(reason) is not str or not reason.strip() for reason in row[2]) for row in dispositions):
        raise ValueError("preparation integrity requires exact retained reason-code tuples")
    counts = tuple((value, sum(row[1] is value for row in dispositions)) for value in A)
    overall = next(value for value in PRECEDENCE if dict(counts)[value])
    return counts, overall


@dataclass(frozen=True, slots=True)
class PreparationIntegrity(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-dynamics/preparation-integrity"
    VERSION: ClassVar[str] = "1.0.0"
    product_id: str
    source: ObjectIdentity
    preparation: ObjectIdentity
    method: ObjectIdentity
    model_dispositions: tuple[tuple[str, A, tuple[str, ...]], ...]
    disposition_counts: tuple[tuple[A, int], ...]
    assignment_disposition: A
    retained_native_call_count: int
    raw_topologies: tuple[tuple[str, c.FileEvidence], ...]
    conversion_source_pins: tuple[tuple[str, str], ...] = SOURCE_CONVERSIONS
    geometry_disposition: A = A.UNEVALUABLE
    native_coverage_disposition: A = A.UNEVALUABLE
    dynamics_disposition: A = A.UNEVALUABLE
    kinetic_disposition: A = A.UNEVALUABLE
    actual_native_attempt_count: int | None = None
    actual_native_completed_count: int | None = None
    physical_independent_units: int = 0

    def __post_init__(self):
        validate_stable_id(self.product_id)
        for identity in (self.source, self.preparation, self.method):
            if type(identity) is not ObjectIdentity:
                raise ValueError("preparation integrity identities must be typed")
            identity.__post_init__()
        counts, overall = disposition_census(self.model_dispositions)
        if type(self.disposition_counts) is not tuple or any(type(value) is not A or type(number) is not int or number < 0 for value,number in self.disposition_counts):
            raise ValueError("preparation integrity disposition counts must be typed integers")
        if self.method != METHOD or self.conversion_source_pins != SOURCE_CONVERSIONS or self.disposition_counts != counts or self.assignment_disposition is not overall:
            raise ValueError("preparation integrity changes method/full disposition census")
        if type(self.retained_native_call_count) is not int or self.retained_native_call_count < 0:
            raise ValueError("retained native call count must be an observed nonnegative integer")
        expected = tuple(row[0] for row in self.model_dispositions if row[1] is A.SATISFIED)
        if tuple(row[0] for row in self.raw_topologies) != expected:
            raise ValueError("positive assignment omits complete raw topology evidence")
        for _, evidence in self.raw_topologies:
            if type(evidence) is not c.FileEvidence:
                raise ValueError("raw topology evidence must be typed")
            evidence.__post_init__()
            if type(evidence.byte_count) is not int or evidence.byte_count <= 0:
                raise ValueError("raw topology byte count must be a positive actual integer")
        if any(value is not A.UNEVALUABLE for value in (self.geometry_disposition, self.native_coverage_disposition,
                self.dynamics_disposition, self.kinetic_disposition)) or self.actual_native_attempt_count is not None or self.actual_native_completed_count is not None or self.physical_independent_units != 0:
            raise ValueError("PURE preparation integrity cannot establish geometry/native coverage/dynamics/biology")


def read_heavy_pdb(text):
    atoms = []
    for line in text.splitlines():
        if not line.startswith(("ATOM  ", "HETATM")):
            continue
        try:
            row = dict(serial=int(line[6:11]), chain=line[21].strip(), position=int(line[22:26]),
                atom=line[12:16].strip(), component=line[17:20].strip(), element=line[76:78].strip().upper(),
                xyz=tuple(D(line[index:index+8].strip()) for index in (30,38,46)))
        except (ValueError, ArithmeticError) as error:
            raise ValueError("independent complete-heavy PDB malformed atom") from error
        if not row["chain"] or not row["atom"] or not row["component"] or not row["element"] or row["element"] in ("H", "D") or any(not x.is_finite() for x in row["xyz"]):
            raise ValueError("independent complete-heavy PDB unknown/nonfinite atom")
        atoms.append(row)
    keys = tuple((row["chain"], row["position"], row["atom"]) for row in atoms)
    if not atoms or len(set(keys)) != len(keys) or tuple(row["serial"] for row in atoms) != tuple(range(1,len(atoms)+1)):
        raise ValueError("independent complete-heavy PDB empty/duplicate atom denominator")
    return tuple(atoms)


def _selected_originals(atoms, chains, joint):
    """Read-only source alternate selection, separate from coordinate producer."""
    chain_map = {row.chain_id:"ABCDEFGHIJKLMNOP"[index] for index,row in enumerate(chains)}
    groups = defaultdict(list)
    for atom in atoms:
        if atom.occupancy > 0:
            groups[(atom.chain_id, atom.label_seq_id, atom.auth_seq_id, atom.insertion_code, atom.component_id)].append(atom)
    selected = []
    for group in groups.values():
        weights = defaultdict(D)
        for atom in group:
            if atom.alternate_id not in (".","?",""):
                weights[atom.alternate_id] += atom.occupancy
        alternates = sorted(weights, key=lambda key:(-weights[key],key))
        choice = alternates[min(int(joint == "joint-02"),len(alternates)-1)] if alternates else None
        selected.extend(atom for atom in group if atom.alternate_id in (".","?","",choice))
    ordered, chemical = [], {}
    for chain in chains:
        ordered.extend(sorted((atom for atom in selected if atom.chain_id == chain.chain_id), key=lambda atom:(int(atom.label_seq_id),atom.source_atom_id)))
    for atom in selected:
        if atom.chain_id not in chain_map:
            key = (atom.chain_id,atom.auth_seq_id,atom.insertion_code,atom.component_id)
            chemical.setdefault(key,[]).append(atom)
    chemical_positions = {}
    for index,group in enumerate(chemical.values(),1):
        for atom in group:
            chemical_positions[(atom.operator_id,atom.source_atom_id)] = index
        ordered.extend(group)
    result = {}
    for serial, atom in enumerate(ordered,1):
        chain = chain_map.get(atom.chain_id,"Z")
        position = int(atom.label_seq_id) if chain != "Z" else chemical_positions[(atom.operator_id,atom.source_atom_id)]
        result[(chain,position,atom.atom_id)] = dict(serial=serial, chain=chain, position=position, atom=atom.atom_id,
            source=[atom.pdb_id,atom.operator_id,atom.source_atom_id], source_component=atom.component_id,
            source_alternate=atom.alternate_id, source_occupancy=str(atom.occupancy), original_xyz_angstrom=[str(x) for x in atom.xyz_angstrom])
    if len(result) != len(ordered):
        raise ValueError("independent selected source atom denominator duplicates")
    return result


def source_disulfide_partners(pdb, original_text, source_atoms, source_chains):
    """Independent named source-connection/operator join; proximity adds none."""
    from empirical_lawhood.adapters.methods.rubisco_insilico_structure.independent_cif import read_cif

    tables = read_cif(original_text)
    operators = {row["id"]:(tuple(D(row[f"matrix[{i}][{j}]"]) for i in range(1,4) for j in range(1,4)),tuple(D(row[f"vector[{i}]"]) for i in range(1,4))) for row in tables["_pdbx_struct_oper_list"]}
    names = {row["name"]:row["id"] for row in tables["_pdbx_struct_oper_list"]}
    chains = sorted((row for row in source_chains if row.pdb_id == pdb),key=lambda row:row.chain_id)
    chain_map = {row.chain_id:"ABCDEFGHIJKLMNOP"[index] for index,row in enumerate(chains)}
    atoms = {(row.operator_id,row.label_asym_id,row.label_seq_id,row.atom_id):row for row in source_atoms if row.pdb_id == pdb and row.chain_id in chain_map}
    identity = (D(1),D(0),D(0),D(0),D(1),D(0),D(0),D(0),D(1))
    selected = {row.operator_id for row in source_atoms if row.pdb_id == pdb}
    partners = set()
    for connection in tables.get("_struct_conn",()):
        if connection["conn_type_id"] != "disulf":
            continue
        if operators[names[connection["ptnr1_symmetry"]]] != (identity,(D(0),)*3):
            raise ValueError("independent source disulfide unsupported first symmetry")
        relative, offset = operators[names[connection["ptnr2_symmetry"]]]
        for operator in selected:
            matrix, vector = operators[operator]
            composed = tuple(sum(matrix[3*i+k]*relative[3*k+j] for k in range(3)) for i in range(3) for j in range(3))
            translated = tuple(sum(matrix[3*i+k]*offset[k] for k in range(3))+vector[i] for i in range(3))
            targets = [key for key in selected if operators[key] == (composed,translated)]
            if len(targets) != 1:
                raise ValueError("independent source disulfide leaves selected assembly")
            endpoints = []
            for number,op in ((1,operator),(2,targets[0])):
                key = (op,connection[f"ptnr{number}_label_asym_id"],connection[f"ptnr{number}_label_seq_id"],connection[f"ptnr{number}_label_atom_id"])
                atom = atoms.get(key)
                if atom is None or atom.component_id != "CYS" or atom.atom_id != "SG":
                    raise ValueError("independent source disulfide missing original CYS/SG")
                endpoints.append((chain_map[atom.chain_id],int(atom.label_seq_id)))
            partners.add(tuple(sorted(endpoints)))
    if len(partners) != (12 if pdb == "3ZXW" else 0):
        raise ValueError("independent source disulfide complete denominator changed")
    return partners


def validate_origins(model, census, origin, heavy_text, source_atoms, source_chains, expected_disulfides, *, chemical_residue_map=None):
    """Join raw actual residue/atom rows to full genotype and inherited origins.

    Coordinate construction, mutant geometry and protonation remain model
    assumptions. 'Inherited' here refers to atom/source identity, never a claim
    that modeled coordinates are unchanged observed mutant coordinates.
    """
    pdb = "1BWV" if model.construct.construct_id.startswith("gp.") else "3ZXW"
    chains = sorted((row for row in source_chains if row.pdb_id == pdb),key=lambda row:row.chain_id)
    atoms = tuple(row for row in source_atoms if row.pdb_id == pdb)
    if len(chains) != 16:
        raise ValueError("independent original source omits full L8S8 chains")
    expected_chains = [dict(chain="ABCDEFGHIJKLMNOP"[index],source_chain=row.chain_id,
        subunit="lsu" if len(row.full_sequence) in (493,475) else "ssu",
        sequence=model.construct.lsu_sequence if len(row.full_sequence) in (493,475) else model.construct.ssu_sequence)
        for index,row in enumerate(chains)]
    declared = origin.get("complete_chains")
    if type(declared) is not list or len(declared) != 16 or any(any(actual.get(key) != value for key,value in expected.items()) for actual,expected in zip(declared,expected_chains,strict=True)):
        raise ValueError("independent realized chain/full genotype declaration changed")
    originals = _selected_originals(atoms,chains,model.joint_view_id)
    declared_originals = origin.get("selected_atom_origins")
    if type(declared_originals) is not list or len(declared_originals) != len(originals):
        raise ValueError("selected original atom-origin full denominator changed")
    for declared,expected in zip(declared_originals,originals.values(),strict=True):
        if type(declared) is not dict or set(declared) != set(expected) | {"model_component"} or any(declared.get(key) != value for key,value in expected.items()):
            raise ValueError("selected atom origin differs from independently reconstructed original")
    heavy = read_heavy_pdb(heavy_text)
    heavy_by_key = {(row["chain"],row["position"],row["atom"]):row for row in heavy}
    by_chain = {row["chain"]:row for row in expected_chains}
    expected_positions = {(row["chain"],position) for row in expected_chains for position in range(1,len(row["sequence"])+1)}
    actual_positions = {(row["chain"],row["position"]) for row in heavy if row["chain"] in by_chain}
    if actual_positions != expected_positions:
        raise ValueError("independent complete-heavy PDB omits complete protein residue denominator")
    for row in heavy:
        chain = by_chain.get(row["chain"])
        if chain and AMINO.get(row["component"]) != chain["sequence"][row["position"]-1]:
            raise ValueError("independent raw complete-heavy PDB changes full genotype")
        if not chain and (row["chain"],row["position"],row["atom"]) not in originals:
            raise ValueError("independent complete-heavy PDB adds undeclared nonprotein atom")
    complete = origin.get("complete_heavy_atoms")
    if type(complete) is not list or len(complete) != len(heavy):
        raise ValueError("producer complete-heavy origin denominator differs from raw PDB")
    complete_by_key = {(row["chain"],row["position"],row["atom"]):row for row in complete}
    # Include the M1/V1 processing contrast as well as named interventions.
    change_positions = {(declared["chain"],position) for declared,original in zip(expected_chains,chains,strict=True)
        for position,(selected,observed) in enumerate(zip(declared["sequence"],original.full_sequence,strict=True),1) if selected != observed}
    for actual, raw in zip(complete,heavy,strict=True):
        key = (raw["chain"],raw["position"],raw["atom"])
        if any(actual.get(name) != raw[name] for name in ("chain","position","atom","component")) or str(actual.get("element")).upper() != raw["element"]:
            raise ValueError("complete-heavy provenance differs from independently read raw PDB atom")
        original = originals.get(key)
        changed = key[:2] in change_positions and key[2] not in ("N","CA","C","O","OXT","CB")
        inherited = original is not None and not changed
        expected_origin = None if not inherited else original
        if inherited:
            # Protonation labels may change; every original source operand is
            # still exact. The model component is separately present in PDB.
            given = actual.get("source_origin")
            if type(given) is not dict or set(given) != set(expected_origin) | {"model_component"} or any(given.get(name) != value for name,value in expected_origin.items()):
                raise ValueError("complete-heavy provenance substitutes authentic source atom/original token")
        elif actual.get("source_origin") is not None:
            raise ValueError("constructed mutant/missing atom falsely inherits observed source")
        if actual.get("status") != ("INHERITED_OBSERVED_SOURCE" if inherited else "DECLARED_CONSTRUCTED_MUTANT_OR_MISSING_ATOM"):
            raise ValueError("complete-heavy provenance changes observed/constructed role")
    for key in originals:
        if key not in heavy_by_key and not (key[:2] in change_positions and key[2] not in ("N","CA","C","O","OXT","CB")):
            raise ValueError("complete-heavy PDB drops inherited original atom")
    realization = origin.get("amber_realization")
    if type(realization) is not dict or type(realization.get("atoms")) is not list:
        raise ValueError("actual Amber atom origins are missing")
    joins = realization["atoms"]
    if len(joins) != census["term_census"]["atoms"] or tuple(row.get("amber_atom_index") for row in joins) != tuple(range(len(joins))):
        raise ValueError("actual Amber atom origin full denominator changed")
    # Complete protein residues precede every inherited chemical/water residue.
    expected_residues = [(row["chain"],position) for row in expected_chains for position in range(1,len(row["sequence"])+1)]
    expected_residues += list(dict.fromkeys((row["chain"],row["position"]) for row in heavy if row["chain"] not in by_chain))
    starts = census["residue_starts"]
    if len(starts) < len(expected_residues):
        raise ValueError("raw Amber omits complete protein/original chemical residues")
    offset = 0
    declared_chains = realization.get("complete_chains")
    if type(declared_chains) is not list or len(declared_chains) != 16:
        raise ValueError("actual Amber complete chain census is missing")
    for declared,chain in zip(declared_chains,expected_chains,strict=True):
        length = len(chain["sequence"])
        residue_names = census["residue_names"][offset:offset+length]
        if "".join(AMINO.get(name,"?") for name in residue_names) != chain["sequence"] or any(declared.get(key) != value for key,value in chain.items()) or declared.get("amber_residue_indices") != list(range(offset,offset+length)) or declared.get("actual_residue_names") != list(residue_names):
            raise ValueError("actual Amber full genotype/chain realization differs from raw residues")
        offset += length
    residue_sources = dict(enumerate(expected_residues))
    if chemical_residue_map is not None:
        chemical_keys = set(expected_residues[offset:])
        if (type(chemical_residue_map) is not dict or set(chemical_residue_map) != chemical_keys
                or any(type(key) is not tuple or len(key) != 2 or type(key[0]) is not str or type(key[1]) is not int
                       for key in chemical_residue_map)
                or any(type(value) is not int or not offset <= value < len(starts) for value in chemical_residue_map.values())
                or len(set(chemical_residue_map.values())) != len(chemical_keys)):
            raise ValueError("independent coordinate chemical residue map shape/denominator differs")
        residue_sources = dict(enumerate(expected_residues[:offset]))
        residue_sources.update((value,key) for key,value in chemical_residue_map.items())
        chemical_expected = defaultdict(dict)
        element_numbers = dict(C=6,N=7,O=8,P=15,S=16,MG=12,NA=11,CL=17)
        for row in complete:
            key = (row["chain"],row["position"])
            if key in chemical_keys:
                chemical_expected[key][row["atom"]] = element_numbers.get(str(row["element"]).upper())
        for key,residue in chemical_residue_map.items():
            end = starts[residue+1]-1 if residue+1 < len(starts) else len(joins)
            raw = {census["atom_names"][index]:census["atomic_numbers"][index]
                   for index in range(starts[residue]-1,end) if census["atomic_numbers"][index] != 1}
            if raw != chemical_expected[key] or len(raw) != sum(census["atomic_numbers"][index] != 1 for index in range(starts[residue]-1,end)):
                raise ValueError("independent coordinate chemical residue map changes complete raw group identity")
    realized_heavy = {}
    residue_index = 0
    elements = dict(C=6,N=7,O=8,P=15,S=16,MG=12,NA=11,CL=17)
    for index,join in enumerate(joins):
        while residue_index+1 < len(starts) and index+1 >= starts[residue_index+1]:
            residue_index += 1
        name,component,number = census["atom_names"][index],census["residue_names"][residue_index],census["atomic_numbers"][index]
        if join.get("amber_residue_index") != residue_index or join.get("atom") != name or join.get("residue_name") != component:
            raise ValueError("actual Amber atom origin differs from raw topology identity")
        if residue_index not in residue_sources:
            if component not in ("WAT","Na+","Cl-","NA","CL") or join.get("source_origin") is not None or join.get("chain") is not None or join.get("position") is not None or join.get("status") != "DECLARED_ADDED_SOLVENT_OR_NEUTRALIZING_ION":
                raise ValueError("actual Amber adds an undeclared chemical/origin")
            continue
        chain,position = residue_sources[residue_index]
        if (join.get("chain"),join.get("position")) != (chain,position):
            raise ValueError("actual Amber atom origin changes full chain/residue map")
        heavy_origin = complete_by_key.get((chain,position,name))
        if heavy_origin is None:
            if number != 1 or join.get("source_origin") is not None or join.get("status") != "DECLARED_AMBER_ADDED_HYDROGEN":
                raise ValueError("actual Amber adds an undeclared original-residue heavy atom")
        else:
            if number != elements.get(str(heavy_origin["element"]).upper()) or join.get("source_origin") != heavy_origin or join.get("status") != "REALIZED_COMPLETE_PREPARATION_ATOM" or component != heavy_origin["component"] and not (heavy_origin["component"] == "HOH" and component == "WAT"):
                raise ValueError("actual Amber replaces complete-heavy element/component/origin")
            key = (chain,position,name)
            if key in realized_heavy:
                raise ValueError("actual Amber duplicates inherited heavy atom identity")
            realized_heavy[key] = index
    if set(realized_heavy) != set(heavy_by_key):
        raise ValueError("actual Amber omits complete raw heavy atom denominator")
    declared_disulfides = {tuple(sorted(tuple(partner) for partner in row["partners"])) for row in origin.get("authenticated_disulfides",())}
    if declared_disulfides != expected_disulfides:
        raise ValueError("preparation changes independently authenticated source disulfides")
    expected_bonds = {tuple(sorted(realized_heavy[(chain,position,"SG")] for chain,position in pair)) for pair in expected_disulfides}
    actual_bonds = {tuple(sorted(abs(value)//3 for value in term[:2])) for name,terms in census["indexed_bonded_terms"].items() if name.startswith("BONDS_") for term in terms if all(census["atom_names"][abs(value)//3] == "SG" for value in term[:2])}
    if actual_bonds != expected_bonds:
        raise ValueError("raw Amber changes authenticated source disulfide bond assignment")
    return len(heavy), len(expected_residues)


COORDINATE_ORIGIN_DESCRIPTION = (
    "Additive full original-source/genotype/atom/addition/disulfide origin validation; "
    "independent Fraction raw restart/PDB common-translation cells and unique name/element/component candidates "
    "against the entire native nonhydrogen population; actual residue indices retained, no ordinal chemical assumption; "
    "no producer import or physical, force-field, dynamics or kinetic adequacy admission."
)
COORDINATE_ORIGIN_METHOD = ObjectIdentity("method.rubisco-dynamics.independent-coordinate-origins",
    "empirical-lawhood/rubisco-insilico-dynamics/coordinate-origin-method", "1.0.0",
    sha256(COORDINATE_ORIGIN_DESCRIPTION.encode()).hexdigest())


@dataclass(frozen=True, slots=True)
class CoordinateOriginValidation:
    """Explicit additive method result, never the legacy integrity record."""

    method: ObjectIdentity
    complete_heavy_atom_count: int
    complete_source_group_count: int
    chemical_residue_map: tuple[tuple[str, int, int], ...]
    common_translation_intervals: tuple[tuple[tuple[int, int], tuple[int, int]], ...]


def _coordinate_origin_readers():
    """Default legacy readers; an explicit successor may select named readers."""
    from .physical_preparation_geometry import _origin_join, read_inpcrd

    return _origin_join, read_inpcrd


def validate_origins_from_coordinates(model, census, origin, heavy_text, raw_inpcrd, source_atoms, source_chains, expected_disulfides):
    """Independently prove a complete origin map before invoking lower guards.

    The map declaration is never trusted. Fraction arithmetic derives its
    complete native-coordinate/name/element/component joins and global unique
    candidates using only the original serialization quantum. The producer's
    Decimal selector is neither imported nor used. The lower validator emits
    only counts; this successor returns its own explicit method identity.
    """
    _origin_join, read_inpcrd = _coordinate_origin_readers()

    realization = origin.get("amber_realization")
    declared = realization.get("chemical_residue_map") if type(realization) is dict else None
    if type(declared) is not list or any(type(row) is not dict or set(row) != {"chain","position","amber_residue_index"}
            or type(row["chain"]) is not str or type(row["position"]) is not int or type(row["amber_residue_index"]) is not int for row in declared):
        raise ValueError("independent coordinate chemical residue map declaration is missing/malformed")
    chemical = {(row["chain"],row["position"]):row["amber_residue_index"] for row in declared}
    if len(chemical) != len(declared):
        raise ValueError("independent coordinate chemical residue map duplicates a source group")
    coordinates, _, _ = read_inpcrd(raw_inpcrd,census["term_census"]["atoms"])
    _, interval_rows = _origin_join(census,coordinates,heavy_text,origin)
    half,scale = Fraction(1,20_000_000),10_000_000
    index = defaultdict(list)
    for atom,point in enumerate(coordinates):
        if census["atomic_numbers"][atom] == 1:
            continue
        lexical = tuple(value*scale for value in point)
        if any(value.denominator != 1 for value in lexical):
            raise ValueError("independent coordinate origin requires original seven-decimal restart grid")
        index[tuple(value.numerator for value in lexical)].append(atom)
    starts = tuple(value-1 for value in census["residue_starts"])
    joins = realization["atoms"]
    claimed = {(row["chain"],row["position"],row["atom"]):row["amber_atom_index"]
               for row in joins if row["status"] == "REALIZED_COMPLETE_PREPARATION_ATOM"}
    heavy = read_heavy_pdb(heavy_text)
    protein_ids = {row["chain"] for row in origin["complete_chains"]}
    intervals = [None]*3
    for source in heavy:
        if source["chain"] not in protein_ids:
            continue
        key = (source["chain"],source["position"],source["atom"])
        point = coordinates[claimed[key]]
        for axis in range(3):
            delta = point[axis]-Fraction(source["xyz"][axis])
            low,high = delta-half,delta+half
            if intervals[axis] is not None:
                low,high = max(low,intervals[axis][0]),min(high,intervals[axis][1])
            if low > high:
                raise ValueError("independent original protein frame has no common translation")
            intervals[axis] = (low,high)
    if any(interval is None for interval in intervals):
        raise ValueError("independent coordinate origin has no complete protein frame")
    elements = dict(C=6,N=7,O=8,P=15,S=16,MG=12,NA=11,CL=17)
    source_residues = defaultdict(set)
    # Freeze the full protein frame. Other source atoms may refine the common
    # translation, but cannot conceal an initially competing eligible origin.
    for source in heavy:
        key = (source["chain"],source["position"],source["atom"])
        axes = tuple(range(ceil((Fraction(value)+low-half)*scale),floor((Fraction(value)+high+half)*scale)+1)
                     for value,(low,high) in zip(source["xyz"],intervals,strict=True))
        candidates = []
        for cell in product(*axes):
            for atom in index.get(cell,()):
                residue = bisect_right(starts,atom)-1
                component = census["residue_names"][residue]
                if (census["atom_names"][atom] == source["atom"] and census["atomic_numbers"][atom] == elements[source["element"]]
                        and (component == source["component"] or (source["component"],component) == ("HOH","WAT"))):
                    candidates.append(atom)
        if len(candidates) != 1 or candidates[0] != claimed[key]:
            raise ValueError("independent coordinate origin lacks a unique complete raw candidate")
        source_residues[key[:2]].add(bisect_right(starts,candidates[0])-1)
    if any(source_residues.get(key) != {residue} for key,residue in chemical.items()):
        raise ValueError("independent coordinate declaration differs from recomputed chemical group map")
    counts = validate_origins(model,census,origin,heavy_text,source_atoms,source_chains,expected_disulfides,
                              chemical_residue_map=chemical)
    return CoordinateOriginValidation(COORDINATE_ORIGIN_METHOD,*counts,
        tuple((row["chain"],row["position"],row["amber_residue_index"]) for row in declared),interval_rows)


def assess(source, preparation, assets, source_atoms, source_chains, disulfides):
    """Complete current-use census after the caller authenticates source lineage."""
    preparation.__post_init__()
    if preparation.source != c.identity(source) or len(assets) != len(c.model_roster()):
        raise ValueError("preparation integrity changes full source/model denominator")
    whole_files = {row.relative_path:row for row in preparation.files}
    if len(whole_files) != len(preparation.files):
        raise ValueError("preparation complete file census duplicates actual paths")
    for row in preparation.files:
        row.__post_init__()
    for call in preparation.native_calls:
        call.__post_init__()
    dispositions, topologies = [], []
    constructs = {row.construct_id:row for row in source.constructs}
    for model,bundle,roster in zip(preparation.models,assets,c.model_roster(),strict=True):
        model.__post_init__()
        bundle.__post_init__()
        if (model.construct != constructs[roster[0]] or model.assets != c.identity(bundle) or bundle.source != c.identity(source)
                or (bundle.construct_id,bundle.joint_view_id,bundle.parameter_view) != roster
                or model.files != tuple(row.evidence for row in bundle.files)
                or any(whole_files.get(row.evidence.relative_path) != row.evidence for row in bundle.files)):
            raise ValueError("preparation integrity substitutes actual construct/source/full file custody")
        verdict = model.disposition
        if type(verdict) is not A:
            raise ValueError("preparation integrity requires typed actual model disposition")
        if type(model.atom_count) is not int or model.atom_count < 0 or type(model.complete_parameter_census) is not tuple or any(type(number) is not int or number < 0 for _,number in model.complete_parameter_census):
            raise ValueError("preparation integrity reports non-integer/negative actual counts")
        if verdict is A.NOT_ATTEMPTED and (model.atom_count or model.complete_parameter_census or model.native_call_ids or model.provenance_manifest_path is not None):
            raise ValueError("NOT_ATTEMPTED preparation contradicts reported actual native work")
        reasons = tuple(model.reason_codes)
        if verdict is A.SATISFIED:
            files = {row.evidence.relative_path:row for row in bundle.files}
            required = (model.model_id+"/model.prmtop",model.model_id+"/complete-heavy.pdb",model.model_id+"/complete-assigned-parameters.json",model.provenance_manifest_path)
            if any(name not in files for name in required):
                raise ValueError("positive preparation omits independently assessable complete raw artifacts")
            topology = files[required[0]]
            census = validate_assignment(topology.raw_utf8,json.loads(files[required[2]].raw_utf8))
            if census["term_census"] != dict(model.complete_parameter_census) or type(model.atom_count) is not int or census["term_census"]["atoms"] != model.atom_count:
                raise ValueError("positive preparation reports a different complete raw parameter census")
            pdb = "1BWV" if model.construct.construct_id.startswith("gp.") else "3ZXW"
            validate_origins(model,census,json.loads(files[required[3]].raw_utf8),files[required[1]].raw_utf8,source_atoms,source_chains,disulfides[pdb])
            topologies.append((model.model_id,topology.evidence))
        dispositions.append((model.model_id,verdict,reasons))
    dispositions = tuple(dispositions)
    counts, overall = disposition_census(dispositions)
    return PreparationIntegrity("product.rubisco-insilico-dynamics.preparation-integrity",c.identity(source),c.identity(preparation),METHOD,
        dispositions,counts,overall,len(preparation.native_calls),tuple(topologies))
