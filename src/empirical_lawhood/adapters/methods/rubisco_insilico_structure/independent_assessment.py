# SPDX-License-Identifier: MPL-2.0
"""Direct original-to-product structural checks independent of the producer.

No producer parser/expander/neighborhood routine, native import, model building
or I/O occurs here. Decimal transforms verify exact deposited values. Scalar
math.dist independently checks the producer's float64 descriptive distances;
the 1e-10 Angstrom comparison allowance is computational, not physical error.
Boundary ambiguity remains unevaluable instead of inventing a shell member.
"""

from collections import Counter, defaultdict
from dataclasses import replace
from decimal import Decimal as D
from hashlib import sha256
import json
from math import dist

from . import contracts as c
from .independent_cif import read_cif
from .integrity_records import StructuralIntegrityAssessment

DISTANCE_TOLERANCE = D("1e-10")


def _sequence(text):
    rows = text.splitlines()
    if not rows or not rows[0].startswith(">") or any(row.startswith(">") for row in rows[1:]):
        raise ValueError("independent structural sequence is not one FASTA member")
    result = "".join(rows[1:])
    if not result or set(result) - set("ACDEFGHIKLMNPQRSTVWY"):
        raise ValueError("independent structural sequence has unknown residue")
    return result


def _source_members(source, dossier):
    if type(source) is not c.StructuralSource:
        raise ValueError("independent structural assessment needs exact original source")
    source.__post_init__()
    dossier.__post_init__()
    if c.identity(dossier) != source.nomination:
        raise ValueError("independent structural assessment substitutes nomination")
    members = {row.filename: row.raw_utf8 for row in source.source_members}
    sequences = tuple(sorted((name, _sequence(text)) for name, text in members.items() if name.endswith(".fasta")))
    selected = dict(sequences)
    if len(selected["gp.lsu.fasta"]) != 493:
        raise ValueError("independent structural full LSU census missing")
    for processing in ("m1", "v1"):
        wt = selected[f"gp.ssu.wt.{processing}.fasta"]
        mutant = selected[f"gp.ssu.i95m.{processing}.fasta"]
        if len(wt) != 138 or wt[94] != "I" or mutant != wt[:94] + "M" + wt[95:]:
            raise ValueError("independent structural I95M material substitution")
    for genotype in ("wt", "i95m"):
        m1, v1 = (selected[f"gp.ssu.{genotype}.{processing}.fasta"] for processing in ("m1", "v1"))
        if v1[0] != "V" or m1 != "M" + v1[1:]:
            raise ValueError("independent structural processing view substitution")
    options = [row for row in dossier.preparation.source_members if row.filename == "construct-options.json"]
    if len(options) != 1:
        raise ValueError("independent structural actual construct options missing")
    actual = json.loads(options[0].raw_utf8)
    if actual["lsu_sequence"] != selected["gp.lsu.fasta"] or actual["proposed_m1_ssu_sequence"] != selected["gp.ssu.i95m.m1.fasta"]:
        raise ValueError("independent structural material differs from nomination")
    return members, sequences


def original_assembly(pdb, text):
    """Separate source expansion used solely as the falsifier's expected census."""
    tables = read_cif(text)
    generations = [row for row in tables["_pdbx_struct_assembly_gen"] if row["assembly_id"] == "1"]
    if len(generations) != 1 or generations[0]["oper_expression"] != "1,2":
        raise ValueError("independent structural assembly generation changed")
    asymids = tuple(generations[0]["asym_id_list"].split(","))
    if len(set(asymids)) != len(asymids):
        raise ValueError("independent structural assembly asymmetry roster duplicated")
    operator_rows = {row["id"]: row for row in tables["_pdbx_struct_oper_list"]}
    if len(operator_rows) != len(tables["_pdbx_struct_oper_list"]):
        raise ValueError("independent structural operator duplicated")
    source_atoms = tables["_atom_site"]
    if len({row["id"] for row in source_atoms}) != len(source_atoms):
        raise ValueError("independent structural original atom identity duplicated")
    atoms, operators, rigid = [], [], []
    for op in ("1", "2"):
        row = operator_rows[op]
        matrix = tuple(D(row[f"matrix[{i}][{j}]"]) for i in (1, 2, 3) for j in (1, 2, 3))
        vector = tuple(D(row[f"vector[{i}]"]) for i in (1, 2, 3))
        if any(not value.is_finite() for value in matrix + vector):
            raise ValueError("independent structural operator is nonfinite")
        operators.append((pdb, op, matrix, vector))
        gram = max(abs(sum((matrix[3*k+i]*matrix[3*k+j] for k in range(3)), D(0)) - (1 if i == j else 0)) for i in range(3) for j in range(3))
        determinant = matrix[0]*(matrix[4]*matrix[8]-matrix[5]*matrix[7])-matrix[1]*(matrix[3]*matrix[8]-matrix[5]*matrix[6])+matrix[2]*(matrix[3]*matrix[7]-matrix[4]*matrix[6])
        rigid.append((pdb, op, gram, abs(determinant - 1)))
        for raw in source_atoms:
            if raw["label_asym_id"] not in asymids:
                continue
            if raw["pdbx_PDB_model_num"] != "1":
                raise ValueError("independent structural multi-model source not selected")
            xyz = tuple(D(raw["Cartn_" + axis]) for axis in "xyz")
            # Independent row-wise dot products over raw tokens, preserving the
            # original Decimal exponents needed for exact historical exports.
            transformed = tuple(sum((coefficient*value for coefficient, value in zip(matrix[3*i:3*i+3], xyz, strict=True)), vector[i]) for i in range(3))
            atoms.append(c.AssemblyAtom(pdb, op, raw["id"], raw["label_asym_id"], raw["auth_asym_id"], raw["label_entity_id"], raw["label_seq_id"], raw["auth_seq_id"], raw["pdbx_PDB_ins_code"], raw["label_comp_id"], raw["label_atom_id"], raw["type_symbol"], raw["label_alt_id"], D(raw["occupancy"]), transformed))
    entities = {row["entity_id"]: "".join(row["pdbx_seq_one_letter_code_can"].split()) for row in tables["_entity_poly"]}
    observed = defaultdict(set)
    for atom in atoms:
        atom.__post_init__()
        observed[(atom.operator_id, atom.label_asym_id, atom.label_seq_id)].add(atom.atom_id)
    chains = []
    for op in ("1", "2"):
        for asym in asymids:
            rows = sorted((row for row in tables["_pdbx_poly_seq_scheme"] if row["asym_id"] == asym), key=lambda row: int(row["seq_id"]))
            if not rows:
                continue
            entity = rows[0]["entity_id"]
            if any(row["entity_id"] != entity or row["pdb_strand_id"] != rows[0]["pdb_strand_id"] for row in rows):
                raise ValueError("independent structural residue source chain inconsistent")
            residues = tuple((int(row["seq_id"]), row["auth_seq_num"], row["pdb_ins_code"], row["mon_id"], tuple(sorted(observed[(op, asym, row["seq_id"])]))) for row in rows)
            chain = c.AssemblyChain(pdb, op, asym, rows[0]["pdb_strand_id"], entity, entities[entity], residues)
            chain.__post_init__()
            chains.append(chain)
    sizes = (493, 138) if pdb == "1BWV" else (475, 118)
    if Counter(len(chain.full_sequence) for chain in chains) != Counter({sizes[0]:8, sizes[1]:8}):
        raise ValueError("independent structural full L8S8 denominator missing")
    return tuple(atoms), tuple(chains), tuple(operators), tuple(rigid), tables


def _check_neighborhoods(inventory, shells):
    """Independent scalar distances and complete source-atom shell sets."""
    expected_chains = [row for row in inventory.chains if len(row.full_sequence) in (138, 118)]
    if len(inventory.neighborhoods) != len(expected_chains):
        raise ValueError("independent structural neighborhood denominator missing")
    protein = {row.chain_id for row in inventory.chains}
    maximum = D(0)
    ambiguities = []
    for chain, view in zip(expected_chains, inventory.neighborhoods, strict=True):
        position = 95 if chain.pdb_id == "1BWV" else 98
        residue = chain.residues[position-1]
        if chain.pdb_id == "1BWV" and (chain.full_sequence[position-1] != "I" or residue[1:4] != ("112", ".", "ILE")):
            raise ValueError("independent structural Gp I95/author I112 map changed")
        if chain.pdb_id == "3ZXW" and chain.full_sequence[position-1] != "V":
            raise ValueError("independent structural Te full V98 map changed")
        eligible = [atom for atom in inventory.atoms if atom.pdb_id == chain.pdb_id and atom.occupancy > 0 and atom.element not in ("H", "D")]
        query = [atom for atom in eligible if atom.chain_id == chain.chain_id and atom.label_seq_id == str(position)]
        if (view.chain_id, view.linear_position, view.author_position, view.original_component, view.query_atom_count) != (chain.chain_id, position, residue[1], residue[3], len(query)):
            raise ValueError("independent structural target atom/residue map changed")
        distances = [D(str(min(dist(tuple(float(x) for x in atom.xyz_angstrom), tuple(float(x) for x in q.xyz_angstrom)) for q in query))) for atom in eligible] if query else None

        def check_minima(actual, groups):
            nonlocal maximum
            if tuple(name for name, _ in actual) != tuple(name for name, _ in groups):
                raise ValueError("independent structural minimum distance denominator changed")
            for (_, reported), (_, indices) in zip(actual, groups, strict=True):
                expected = min(distances[index] for index in indices) if distances is not None and indices else None
                if expected is None:
                    if reported is not None:
                        raise ValueError("independent structural absent query became positive distance")
                else:
                    if type(reported) is not D or not reported.is_finite():
                        raise ValueError("independent structural distance not finite Decimal")
                    residual = abs(reported - expected)
                    if residual > DISTANCE_TOLERANCE:
                        raise ValueError("independent structural distance differs from source geometry")
                    maximum = max(maximum, residual)

        others = [(name, [i for i, atom in enumerate(eligible) if atom.chain_id == name]) for name in sorted(protein) if name != chain.chain_id and name.startswith(chain.pdb_id + ".")]
        chemicals = sorted({atom.component_id for atom in eligible if atom.chain_id not in protein or atom.component_id == "KCX"})
        chemical = [(name, [i for i, atom in enumerate(eligible) if atom.component_id == name and (atom.chain_id not in protein or atom.component_id == "KCX")]) for name in chemicals]
        check_minima(view.other_chain_minima_angstrom, others)
        check_minima(view.chemical_minima_angstrom, chemical)
        if tuple(radius for radius, _ in view.shells) != shells:
            raise ValueError("independent structural shell census changed")
        for radius, reported in view.shells:
            certain_inside, ambiguous = [], []
            if distances is not None:
                for atom, distance in zip(eligible, distances, strict=True):
                    if atom.chain_id == chain.chain_id and atom.label_seq_id == str(position):
                        continue
                    name = atom.chain_id + "." + atom.source_atom_id
                    if abs(distance-radius) <= DISTANCE_TOLERANCE:
                        ambiguous.append(name)
                        ambiguities.append((chain.chain_id, name, radius))
                    elif distance < radius:
                        certain_inside.append(name)
            if len(reported) != len(set(reported)) or set(reported)-set(ambiguous) != set(certain_inside):
                raise ValueError("independent structural atom shell differs from source geometry")
    return maximum, tuple(ambiguities)


def validate_observed_inventory(source, dossier, inventory):
    """Return source-spelled atoms only after complete independent validation."""
    members, sequences = _source_members(source, dossier)
    if type(inventory) is not c.StructuralInventory:
        raise ValueError("independent structural inventory must be typed")
    inventory.__post_init__()
    if inventory.source != c.identity(source) or inventory.nomination != c.identity(dossier):
        raise ValueError("independent structural source/nomination lineage substitution")
    pieces = [original_assembly(pdb, members[pdb.lower()+".cif"]) for pdb in ("1BWV", "3ZXW")]
    atoms, chains, operators = (tuple(row for piece in pieces for row in piece[index]) for index in (0, 1, 2))
    if inventory.atoms != atoms:
        raise ValueError("actual inventory fails independent source atom/operator/alternate reconstruction")
    if inventory.chains != chains:
        raise ValueError("actual inventory fails independent full residue/chain reconstruction")
    if inventory.operators != operators or inventory.proposed_sequences != sequences:
        raise ValueError("actual inventory fails independent operator/sequence reconstruction")
    selected = dict(sequences)
    for chain in chains:
        if chain.pdb_id == "1BWV" and chain.full_sequence != selected["gp.lsu.fasta" if len(chain.full_sequence) == 493 else "gp.ssu.wt.v1.fasta"]:
            raise ValueError("independent structural full deposited genotype differs")
    protein = {row.chain_id for row in chains}
    counts = Counter((atom.pdb_id, atom.chain_id, atom.component_id) for atom in atoms if atom.chain_id not in protein or atom.component_id == "KCX")
    if inventory.chemical_census != tuple((*key, value) for key, value in sorted(counts.items())):
        raise ValueError("independent structural full chemical/KCX/metal/ligand census changed")
    maximum, ambiguities = _check_neighborhoods(inventory, source.distance_shells_angstrom)
    # This is reconstruction of exact old serialization operands, not new
    # modeling or replacement of any retained bytes.
    return replace(inventory, atoms=atoms), tuple(row for piece in pieces for row in piece[3]), maximum, ambiguities


def validate_coordinate_export(source, inventory, coordinates):
    """Check every exported source atom column and exact Decimal coordinate."""
    if type(coordinates) is not c.AssemblyCoordinates or coordinates.inventory != c.identity(inventory):
        raise ValueError("independent structural coordinate export lineage changed")
    coordinates.__post_init__()
    members = {row.filename: row.raw_utf8 for row in source.source_members}
    for pdb, (name, digest, text) in zip(("1BWV", "3ZXW"), coordinates.files, strict=True):
        if name != pdb.lower()+"-assembly1.cif" or sha256(text.encode()).hexdigest() != digest:
            raise ValueError("independent structural exact coordinate export bytes changed")
        original = read_cif(members[pdb.lower()+".cif"])
        expanded = read_cif(text)
        originals = {row["id"]: row for row in original["_atom_site"]}
        atoms = [row for row in inventory.atoms if row.pdb_id == pdb]
        rows = expanded["_atom_site"]
        if len(rows) != len(atoms):
            raise ValueError("independent structural coordinate export atom denominator changed")
        for number, (atom, row) in enumerate(zip(atoms, rows, strict=True), 1):
            expected = dict(originals[atom.source_atom_id])
            expected.update(id=str(number), label_asym_id="op"+atom.operator_id+"_"+atom.label_asym_id, auth_asym_id="op"+atom.operator_id+"_"+atom.auth_asym_id)
            expected.update({"Cartn_"+axis: str(value) for axis, value in zip("xyz", atom.xyz_angstrom, strict=True)})
            if row != expected:
                raise ValueError("actual coordinate export changes exact source column/token/transform")
        for category in ("_entity", "_entity_poly_seq", "_chem_comp"):
            if expanded.get(category, []) != original.get(category, []):
                raise ValueError("independent structural coordinate export chemical/entity source changed")
        expected_polymers = []
        for row in original["_entity_poly"]:
            strands = ",".join("op"+op+"_"+author for op in ("1", "2") for author in row["pdbx_strand_id"].split(","))
            expected_polymers.append(row | {"pdbx_strand_id":strands})
        if expanded["_entity_poly"] != expected_polymers:
            raise ValueError("independent structural coordinate export full polymer map changed")
        # Full scheme metadata is essential to downstream atom-origin joins.
        selected = {atom.label_asym_id for atom in atoms}
        expected_asym = [dict(id="op"+op+"_"+row["id"], entity_id=row["entity_id"]) for op in ("1", "2") for row in original["_struct_asym"] if row["id"] in selected]
        if expanded["_struct_asym"] != expected_asym:
            raise ValueError("independent structural coordinate export full asymmetry map changed")
        expected_modifications = []
        for op in ("1", "2"):
            for row in original.get("_pdbx_struct_mod_residue", []):
                if row.get("label_asym_id") in selected:
                    expected_modifications.append(row | {"id":str(len(expected_modifications)+1), "label_asym_id":"op"+op+"_"+row["label_asym_id"], "auth_asym_id":"op"+op+"_"+row["auth_asym_id"]})
        if expanded.get("_pdbx_struct_mod_residue", []) != expected_modifications:
            raise ValueError("independent structural coordinate export activation/modification map changed")
        expected_scheme = []
        for op in ("1", "2"):
            for row in original["_pdbx_poly_seq_scheme"]:
                if row["asym_id"] in selected:
                    expected_scheme.append(row | {"asym_id":"op"+op+"_"+row["asym_id"], "pdb_strand_id":"op"+op+"_"+row["pdb_strand_id"]})
        if expanded["_pdbx_poly_seq_scheme"] != expected_scheme:
            raise ValueError("independent structural coordinate export residue map changed")
        expected_categories = {category for category in ("_entity", "_entity_poly_seq", "_chem_comp", "_entity_poly", "_struct_asym", "_pdbx_poly_seq_scheme", "_atom_site", "_pdbx_struct_mod_residue") if category in original and original[category]}
        if set(expanded) != expected_categories:
            raise ValueError("independent structural coordinate export category census changed")


def assess(source, dossier, inventory, *, assessor_source, coordinates=None):
    source_spelled, rigid, maximum, ambiguities = validate_observed_inventory(source, dossier, inventory)
    if coordinates is not None:
        validate_coordinate_export(source, source_spelled, coordinates)
    coverage = tuple((row.chain_id, len(row.full_sequence), sum(bool(position[4]) for position in row.residues), tuple(position[0] for position in row.residues if not position[4])) for row in inventory.chains)
    return StructuralIntegrityAssessment("product.rubisco-insilico-structure.independent-integrity", c.identity(source), c.identity(inventory), None if coordinates is None else c.identity(coordinates), assessor_source, coverage, tuple((pdb, sum(atom.pdb_id == pdb for atom in inventory.atoms)) for pdb in ("1BWV", "3ZXW")), rigid, maximum, DISTANCE_TOLERANCE, ambiguities, c.A.SATISFIED, c.A.UNEVALUABLE if ambiguities else c.A.SATISFIED)


def legacy_mapping_assessment(source, dossier, inventory):
    """Preserve the exact legacy result shape/bytes with an independent check."""
    checked, _, _, ambiguities = validate_observed_inventory(source, dossier, inventory)
    coverage = tuple((row.chain_id, len(row.full_sequence), sum(bool(position[4]) for position in row.residues), tuple(position[0] for position in row.residues if not position[4])) for row in checked.chains)
    return c.StructuralAssessment("product.rubisco-insilico-structure.mapping-assessment", c.identity(source), c.identity(inventory), c.identity(dossier), dossier.scope, coverage, tuple((name, sha256(seq.encode()).hexdigest()) for name, seq in inventory.proposed_sequences), c.A.UNEVALUABLE if ambiguities else c.A.SATISFIED, c.A.UNEVALUABLE, c.A.UNEVALUABLE, ("OBSERVED_ORIGINAL_L8S8_MAPPING_ONLY", "ACTIVATED_INHIBITED_SOURCE_NOT_PRODUCTIVE_KINETICS", "MISSING_COORDINATES_RETAINED", "MUTANT_PREPARATION_COMPARISON_PENDING", "ZERO_NEW_BIOLOGICAL_UNITS"))
