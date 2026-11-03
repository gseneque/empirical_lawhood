# SPDX-License-Identifier: MPL-2.0
"""Observed assembly expansion; no built atoms, mutant coordinates or kinetics."""

from collections import Counter, defaultdict
from decimal import Decimal as D
from hashlib import sha256
import json
import shlex

import numpy as np

from . import contracts as c


class _QuotedCifValue(str):
    """Quoted/text values never become CIF control/header tokens."""


def cif_tables(text):
    """Read the selected original mmCIF lexical forms, refusing malformed loops."""
    lines = text.splitlines()
    tokens = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith(";"):
            block = [line[1:]]
            i += 1
            while i < len(lines) and not lines[i].startswith(";"):
                block.append(lines[i])
                i += 1
            if i == len(lines):
                raise ValueError("unterminated CIF text")
            tokens.append(_QuotedCifValue("\n".join(block)))
        else:
            for token in shlex.split(line, comments=True, posix=False):
                tokens.append(
                    _QuotedCifValue(token[1:-1]) if token[:1] in ('"', "'") else token
                )
        i += 1
    if not tokens or not tokens[0].startswith("data_"):
        raise ValueError("missing selected CIF data block")
    tables = {}
    i = 1
    while i < len(tokens):
        token = tokens[i]
        if token == "loop_":
            i += 1
            headers = []
            while (
                i < len(tokens)
                and not isinstance(tokens[i], _QuotedCifValue)
                and tokens[i].startswith("_")
            ):
                headers.append(tokens[i])
                i += 1
            if not headers or len(set(headers)) != len(headers):
                raise ValueError("invalid CIF loop headers")
            category = headers[0].split(".")[0]
            if any(h.split(".")[0] != category for h in headers) or category in tables:
                raise ValueError("mixed/duplicate CIF category")
            values = []
            while i < len(tokens) and (
                isinstance(tokens[i], _QuotedCifValue)
                or (
                    tokens[i] != "loop_"
                    and not tokens[i].startswith(("_", "data_", "save_"))
                )
            ):
                values.append(tokens[i])
                i += 1
            if len(values) % len(headers):
                raise ValueError(
                    f"incomplete CIF loop row {category}: {len(values)} values/{len(headers)} columns"
                )
            tables[category] = [
                dict(
                    zip(
                        (h.split(".", 1)[1] for h in headers),
                        (str(v) for v in values[j : j + len(headers)]),
                        strict=True,
                    )
                )
                for j in range(0, len(values), len(headers))
            ]
        elif token.startswith("_"):
            category, key = token.split(".", 1)
            if i + 1 == len(tokens):
                raise ValueError("missing CIF scalar")
            rows = tables.setdefault(category, [{}])
            if len(rows) != 1 or key in rows[0]:
                raise ValueError("duplicate CIF scalar")
            rows[0][key] = str(tokens[i + 1])
            i += 2
        else:
            raise ValueError("unsupported extra CIF data block/control token")
    return tables


def fasta(text):
    rows = text.splitlines()
    if (
        not rows
        or not rows[0].startswith(">")
        or any(r.startswith(">") for r in rows[1:])
    ):
        raise ValueError("selected sequence is not one FASTA member")
    sequence = "".join(rows[1:])
    if not sequence or any(a not in "ACDEFGHIKLMNPQRSTVWY" for a in sequence):
        raise ValueError("invalid full protein sequence")
    return sequence


def validate_source(source, dossier):
    source.__post_init__()
    dossier.__post_init__()
    if c.identity(dossier) != source.nomination:
        raise ValueError("source substitutes authentic actual nomination")
    members = {r.filename: r.raw_utf8 for r in source.source_members}
    sequences = {
        name: fasta(text) for name, text in members.items() if name.endswith(".fasta")
    }
    if len(sequences["gp.lsu.fasta"]) != 493:
        raise ValueError("full LSU omitted")
    for processing in ("m1", "v1"):
        wt = sequences[f"gp.ssu.wt.{processing}.fasta"]
        mutant = sequences[f"gp.ssu.i95m.{processing}.fasta"]
        if (
            len(wt) != 138
            or len(mutant) != 138
            or wt[94] != "I"
            or mutant != wt[:94] + "M" + wt[95:]
        ):
            raise ValueError("full I95M intervention changes another position")
    for genotype in ("wt", "i95m"):
        m = sequences[f"gp.ssu.{genotype}.m1.fasta"]
        v = sequences[f"gp.ssu.{genotype}.v1.fasta"]
        if m != "M" + v[1:] or v[0] != "V":
            raise ValueError("M1/V1 processing changes numbering")
    options = [
        r
        for r in dossier.preparation.source_members
        if r.filename == "construct-options.json"
    ]
    if len(options) != 1:
        raise ValueError("authentic preparation lacks construct options")
    actual = json.loads(options[0].raw_utf8)
    if (
        actual["lsu_sequence"] != sequences["gp.lsu.fasta"]
        or actual["proposed_m1_ssu_sequence"] != sequences["gp.ssu.i95m.m1.fasta"]
    ):
        raise ValueError("structure sequence views change actual proposed material")
    return members, tuple(sorted(sequences.items()))


def expand(pdb, text):
    tables = cif_tables(text)
    operators = {}
    for row in tables["_pdbx_struct_oper_list"]:
        matrix = tuple(
            D(row[f"matrix[{i}][{j}]"]) for i in range(1, 4) for j in range(1, 4)
        )
        vector = tuple(D(row[f"vector[{i}]"]) for i in range(1, 4))
        operators[row["id"]] = (matrix, vector)
    generation = [
        r for r in tables["_pdbx_struct_assembly_gen"] if r["assembly_id"] == "1"
    ]
    if len(generation) != 1 or generation[0]["oper_expression"] != "1,2":
        raise ValueError("selected assembly generation changed")
    asymids = generation[0]["asym_id_list"].split(",")
    selected = ("1", "2")
    atoms = []
    for op in selected:
        matrix, vector = operators[op]
        for row in tables["_atom_site"]:
            if row["label_asym_id"] not in asymids:
                continue
            if row["pdbx_PDB_model_num"] != "1":
                raise ValueError(
                    "multiple structural models require selected interpretation"
                )
            xyz = tuple(D(row["Cartn_" + axis]) for axis in "xyz")
            transformed = tuple(
                sum((matrix[3 * i + j] * xyz[j] for j in range(3)), D(0)) + vector[i]
                for i in range(3)
            )
            atoms.append(
                c.AssemblyAtom(
                    pdb,
                    op,
                    row["id"],
                    row["label_asym_id"],
                    row["auth_asym_id"],
                    row["label_entity_id"],
                    row["label_seq_id"],
                    row["auth_seq_id"],
                    row["pdbx_PDB_ins_code"],
                    row["label_comp_id"],
                    row["label_atom_id"],
                    row["type_symbol"],
                    row["label_alt_id"],
                    D(row["occupancy"]),
                    transformed,
                )
            )
    entities = {
        r["entity_id"]: "".join(r["pdbx_seq_one_letter_code_can"].split())
        for r in tables["_entity_poly"]
    }
    observed_atoms = defaultdict(set)
    for atom in atoms:
        observed_atoms[(atom.operator_id, atom.label_asym_id, atom.label_seq_id)].add(
            atom.atom_id
        )
    chains = []
    for op in selected:
        for asym in asymids:
            scheme = [
                r for r in tables["_pdbx_poly_seq_scheme"] if r["asym_id"] == asym
            ]
            if not scheme:
                continue
            entity = scheme[0]["entity_id"]
            sequence = entities[entity]
            scheme.sort(key=lambda r: int(r["seq_id"]))
            residues = []
            for row in scheme:
                linear = int(row["seq_id"])
                observed = tuple(sorted(observed_atoms[(op, asym, str(linear))]))
                residues.append(
                    (
                        linear,
                        row["auth_seq_num"],
                        row["pdb_ins_code"],
                        row["mon_id"],
                        observed,
                    )
                )
            chains.append(
                c.AssemblyChain(
                    pdb,
                    op,
                    asym,
                    scheme[0]["pdb_strand_id"],
                    entity,
                    sequence,
                    tuple(residues),
                )
            )
    expected = (493, 138) if pdb == "1BWV" else (475, 118)
    if Counter(len(r.full_sequence) for r in chains) != Counter(
        {expected[0]: 8, expected[1]: 8}
    ):
        raise ValueError("selected original does not expand to complete L8S8")
    return (
        tuple(atoms),
        tuple(chains),
        tuple((pdb, op, *operators[op]) for op in selected),
    )


def neighborhoods(atoms, chains, shells):
    eligible = [a for a in atoms if a.occupancy > 0 and a.element not in ("H", "D")]
    xyz = np.array([[float(x) for x in a.xyz_angstrom] for a in eligible])
    protein = {chain.chain_id for chain in chains}
    result = []
    for chain in chains:
        target = 95 if chain.pdb_id == "1BWV" else 98
        if len(chain.full_sequence) not in (138, 118):
            continue
        query = [
            a
            for a in eligible
            if a.chain_id == chain.chain_id and a.label_seq_id == str(target)
        ]
        residue = chain.residues[target - 1]
        if chain.pdb_id == "1BWV" and (
            chain.full_sequence[target - 1] != "I"
            or residue[1] != "112"
            or residue[3] != "ILE"
        ):
            raise ValueError("Gp I95 does not bind authentic author I112")
        if chain.pdb_id == "3ZXW" and chain.full_sequence[target - 1] != "V":
            raise ValueError("Te correspondence does not bind authentic V98")
        distances = (
            np.min(
                np.linalg.norm(
                    xyz[:, None, :]
                    - np.array([[float(x) for x in a.xyz_angstrom] for a in query])[
                        None, :, :
                    ],
                    axis=2,
                ),
                axis=1,
            )
            if query
            else None
        )

        def minimum(indices):
            return (
                D(str(float(min(distances[i] for i in indices))))
                if distances is not None and indices
                else None
            )

        other = tuple(
            (name, minimum([i for i, a in enumerate(eligible) if a.chain_id == name]))
            for name in sorted(protein)
            if name != chain.chain_id and name.startswith(chain.pdb_id + ".")
        )
        chemicals = sorted(
            {
                a.component_id
                for a in eligible
                if (a.chain_id not in protein or a.component_id == "KCX")
                and a.pdb_id == chain.pdb_id
            }
        )
        chemical = tuple(
            (
                name,
                minimum(
                    [
                        i
                        for i, a in enumerate(eligible)
                        if a.component_id == name
                        and (a.chain_id not in protein or a.component_id == "KCX")
                        and a.pdb_id == chain.pdb_id
                    ]
                ),
            )
            for name in chemicals
        )
        nearby = tuple(
            (
                shell,
                tuple(
                    f"{a.chain_id}.{a.source_atom_id}"
                    for i, a in enumerate(eligible)
                    if distances is not None
                    and distances[i] <= float(shell)
                    and a.pdb_id == chain.pdb_id
                    and not (
                        a.chain_id == chain.chain_id and a.label_seq_id == str(target)
                    )
                ),
            )
            for shell in shells
        )
        result.append(
            c.SiteNeighborhood(
                chain.chain_id,
                target,
                residue[1],
                residue[3],
                len(query),
                nearby,
                other,
                chemical,
            )
        )
    return tuple(result)


def analyze(source, dossier):
    members, sequences = validate_source(source, dossier)
    pieces = [expand(pdb, members[pdb.lower() + ".cif"]) for pdb in ("1BWV", "3ZXW")]
    atoms = sum((p[0] for p in pieces), ())
    chains = sum((p[1] for p in pieces), ())
    sequence_map = dict(sequences)
    for chain in chains:
        if chain.pdb_id == "1BWV":
            expected = (
                sequence_map["gp.lsu.fasta"]
                if len(chain.full_sequence) == 493
                else sequence_map["gp.ssu.wt.v1.fasta"]
            )
            if chain.full_sequence != expected:
                raise ValueError(
                    "deposited Gp full sequence changes authentic construct WT view"
                )
    operators = sum((p[2] for p in pieces), ())
    protein = {r.chain_id for r in chains}
    census = Counter(
        (a.pdb_id, a.chain_id, a.component_id)
        for a in atoms
        if a.chain_id not in protein or a.component_id == "KCX"
    )
    return c.StructuralInventory(
        "product.rubisco-insilico-structure.observed-assembly",
        c.identity(source),
        c.identity(dossier),
        atoms,
        chains,
        operators,
        neighborhoods(atoms, chains, source.distance_shells_angstrom),
        sequences,
        tuple((*key, value) for key, value in sorted(census.items())),
    )


def assess(source, dossier, inventory):
    from .independent_assessment import legacy_mapping_assessment

    return legacy_mapping_assessment(source, dossier, inventory)


def assembly_coordinates(source, inventory):
    """Export transformed observed WT atoms for PDBxFile, never model missing atoms."""
    if inventory.source != c.identity(source):
        raise ValueError("coordinates substitute selected inventory source")
    files = []
    for pdb in ("1BWV", "3ZXW"):
        tables = cif_tables(
            next(
                r.raw_utf8
                for r in source.source_members
                if r.filename == pdb.lower() + ".cif"
            )
        )
        original = {r["id"]: r for r in tables["_atom_site"]}
        assembled = [a for a in inventory.atoms if a.pdb_id == pdb]
        selected = {a.label_asym_id for a in assembled}

        def chain(op, asym):
            return "op" + op + "_" + asym

        def quote(value):
            if "\n" in value:
                return "\n;" + value + "\n;\n"
            if (
                not value
                or any(x.isspace() for x in value)
                or "'" in value
                or '"' in value
                or value.startswith(("_", "#", ";"))
            ):
                if '"' not in value:
                    return '"' + value + '"'
                if "'" not in value:
                    return "'" + value + "'"
                return "\n;" + value + "\n;\n"
            return value

        output = ["data_" + pdb + "_observed_assembly1", "#"]

        def loop(category, rows):
            if not rows:
                return
            keys = tuple(rows[0])
            output.extend(["loop_", *(category + "." + key for key in keys)])
            output.extend(
                " ".join(quote(str(row[key])) for key in keys) for row in rows
            )
            output.append("#")

        for category in ("_entity", "_entity_poly_seq", "_chem_comp"):
            loop(category, tables.get(category, []))
        polymers = []
        for raw in tables["_entity_poly"]:
            row = dict(raw)
            row["pdbx_strand_id"] = ",".join(
                chain(op, author)
                for op in ("1", "2")
                for author in raw["pdbx_strand_id"].split(",")
            )
            polymers.append(row)
        loop("_entity_poly", polymers)
        modifications = []
        for op in ("1", "2"):
            for raw in tables.get("_pdbx_struct_mod_residue", []):
                row = dict(raw)
                if row.get("label_asym_id") not in selected:
                    continue
                row["id"] = str(len(modifications) + 1)
                row["label_asym_id"] = chain(op, raw["label_asym_id"])
                row["auth_asym_id"] = chain(op, raw["auth_asym_id"])
                modifications.append(row)
        loop("_pdbx_struct_mod_residue", modifications)
        loop(
            "_struct_asym",
            [
                dict(id=chain(op, r["id"]), entity_id=r["entity_id"])
                for op in ("1", "2")
                for r in tables["_struct_asym"]
                if r["id"] in selected
            ],
        )
        mapped = []
        for op in ("1", "2"):
            for raw in tables["_pdbx_poly_seq_scheme"]:
                if raw["asym_id"] in selected:
                    row = dict(raw)
                    row["asym_id"] = chain(op, raw["asym_id"])
                    row["pdb_strand_id"] = chain(op, raw["pdb_strand_id"])
                    mapped.append(row)
        loop("_pdbx_poly_seq_scheme", mapped)
        rows = []
        for i, atom in enumerate(assembled, 1):
            row = dict(original[atom.source_atom_id])
            row["id"] = str(i)
            row["label_asym_id"] = chain(atom.operator_id, atom.label_asym_id)
            row["auth_asym_id"] = chain(atom.operator_id, atom.auth_asym_id)
            for axis, value in zip("xyz", atom.xyz_angstrom, strict=True):
                row["Cartn_" + axis] = str(value)
            rows.append(row)
        loop("_atom_site", rows)
        text = "\n".join(output) + "\n"
        files.append(
            (pdb.lower() + "-assembly1.cif", sha256(text.encode()).hexdigest(), text)
        )
    return c.AssemblyCoordinates(
        "product.rubisco-insilico-structure.observed-coordinates",
        c.identity(inventory),
        tuple(files),
    )
