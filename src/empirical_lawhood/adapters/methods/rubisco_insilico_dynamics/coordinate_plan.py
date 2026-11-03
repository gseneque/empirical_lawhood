# SPDX-License-Identifier: MPL-2.0
"""Pure declared native-coordinate plan; no built atoms or native imports."""

from collections import defaultdict
from decimal import Decimal
from math import sqrt

from empirical_lawhood.adapters.methods.rubisco_insilico_structure.science import (
    cif_tables,
)

THREE = dict(
    zip(
        "ACDEFGHIKLMNPQRSTVWY",
        (
            "ALA",
            "CYS",
            "ASP",
            "GLU",
            "PHE",
            "GLY",
            "HIS",
            "ILE",
            "LYS",
            "LEU",
            "MET",
            "ASN",
            "PRO",
            "GLN",
            "ARG",
            "SER",
            "THR",
            "VAL",
            "TRP",
            "TYR",
        ),
        strict=True,
    )
)


def _published_residues(text):
    rows = {}
    for line in text.splitlines():
        if line.startswith(("ATOM  ", "HETATM")):
            key = (line[21], line[22:27].strip())
            residue = rows.setdefault(key, dict(name=line[17:20].strip(), atoms={}))
            residue["atoms"][line[12:16].strip()] = tuple(
                float(line[i : i + 8]) for i in (30, 38, 46)
            )
    return rows


def _protonation_map(chains, atoms, published_text):
    """Transfer only source-stock states with an explicit coordinate join.

    No chain permutation or fitted alignment is assumed. Unmapped histidines
    use declared Amber HIE, and unverified stock CYX is kept as source CYS.
    These are computational protonation assumptions, not a pH measurement.
    """
    published = _published_residues(published_text)
    by_chain = defaultdict(dict)
    for (chain, residue), row in published.items():
        if "CA" in row["atoms"]:
            by_chain[chain][residue] = row
    lookup = defaultdict(dict)
    for atom in atoms:
        if atom.atom_id == "CA" and atom.chain_id in {row.chain_id for row in chains}:
            lookup[atom.chain_id][
                atom.auth_seq_id
                + ("" if atom.insertion_code in (".", "?") else atom.insertion_code)
            ] = tuple(float(x) for x in atom.xyz_angstrom)
    mappings = []
    states = {}
    for chain in chains:
        candidates = []
        for stock_chain, stock in by_chain.items():
            common = sorted(set(lookup[chain.chain_id]) & set(stock))
            if not common:
                continue
            error = sqrt(
                sum(
                    sum(
                        (lookup[chain.chain_id][key][i] - stock[key]["atoms"]["CA"][i])
                        ** 2
                        for i in range(3)
                    )
                    for key in common
                )
                / len(common)
            )
            candidates.append((error, stock_chain, len(common)))
        best = min(candidates) if candidates else None
        adopted = best is not None and best[0] <= 0.002
        mappings.append(
            dict(
                source_chain=chain.chain_id,
                stock_chain=best[1] if adopted else None,
                common_ca=best[2] if best else 0,
                rmsd_angstrom=best[0] if best else None,
                status="SOURCE_STOCK_COORDINATE_JOIN"
                if adopted
                else "UNMAPPED_DECLARED_AMBER_DEFAULT",
            )
        )
        if adopted:
            for position, author, insertion, original, _ in chain.residues:
                key = author + ("" if insertion in (".", "?") else insertion)
                row = by_chain[best[1]].get(key)
                if row and original == "HIS" and row["name"] in ("HID", "HIE", "HIP"):
                    states[(chain.chain_id, position)] = row["name"]
    return states, mappings


def source_disulfides(original_text, pdb, inventory, selected, chain_map):
    """Expand explicit source connections through authentic named operators.

    Geometry verifies each joined source bond; proximity does not create one.
    The selected deposits use identity partner1, with named partner2 operators.
    Unsupported source symmetries refuse rather than invent a topology.
    """
    tables = cif_tables(original_text)
    named = {row["name"]: row["id"] for row in tables["_pdbx_struct_oper_list"]}
    operations = {
        operator: (matrix, vector)
        for entry, operator, matrix, vector in inventory.operators
        if entry == pdb
    }
    source_ops = {
        row["id"]: (
            tuple(
                Decimal(row[f"matrix[{i}][{j}]"])
                for i in range(1, 4)
                for j in range(1, 4)
            ),
            tuple(Decimal(row[f"vector[{i}]"]) for i in range(1, 4)),
        )
        for row in tables["_pdbx_struct_oper_list"]
    }
    if operations != source_ops:
        raise ValueError("disulfide mapping substitutes authentic assembly operators")
    identity = (
        Decimal(1),
        Decimal(0),
        Decimal(0),
        Decimal(0),
        Decimal(1),
        Decimal(0),
        Decimal(0),
        Decimal(0),
        Decimal(1),
    )
    atoms = {
        (row.operator_id, row.label_asym_id, row.label_seq_id, row.atom_id): row
        for row in selected
        if row.chain_id in chain_map
    }
    bonds = {}
    for connection in tables.get("_struct_conn", ()):
        if connection["conn_type_id"] != "disulf":
            continue
        first = source_ops[named[connection["ptnr1_symmetry"]]]
        if first != (identity, (Decimal(0),) * 3):
            raise ValueError("unsupported nonidentity source disulfide first symmetry")
        relative = source_ops[named[connection["ptnr2_symmetry"]]]
        for operator, (matrix, vector) in operations.items():
            product = tuple(
                sum(matrix[3 * i + k] * relative[0][3 * k + j] for k in range(3))
                for i in range(3)
                for j in range(3)
            )
            translation = tuple(
                sum(matrix[3 * i + k] * relative[1][k] for k in range(3)) + vector[i]
                for i in range(3)
            )
            target = [
                key
                for key, value in operations.items()
                if value == (product, translation)
            ]
            if len(target) != 1:
                raise ValueError("source disulfide symmetry exits selected assembly")
            partners = []
            for number, op in ((1, operator), (2, target[0])):
                key = (
                    op,
                    connection[f"ptnr{number}_label_asym_id"],
                    connection[f"ptnr{number}_label_seq_id"],
                    connection[f"ptnr{number}_label_atom_id"],
                )
                if key not in atoms:
                    raise ValueError(
                        "authentic disulfide lacks selected source SG atom"
                    )
                atom = atoms[key]
                if atom.component_id != "CYS" or atom.atom_id != "SG":
                    raise ValueError("source disulfide partner is not CYS SG")
                partners.append(atom)
            key = tuple(
                sorted(
                    (chain_map[row.chain_id], int(row.label_seq_id)) for row in partners
                )
            )
            distance = sqrt(
                sum(
                    float(a - b) ** 2
                    for a, b in zip(
                        partners[0].xyz_angstrom, partners[1].xyz_angstrom, strict=True
                    )
                )
            )
            if abs(distance - float(connection["pdbx_dist_value"])) > 0.002:
                raise ValueError(
                    "source disulfide distance does not match authenticated bond"
                )
            bond = bonds.setdefault(
                key,
                dict(
                    partners=key,
                    source_connection_ids=[],
                    distance_angstrom=distance,
                    native_bond_atom="SG",
                    basis="EXPLICIT_SOURCE_CONNECTION_NAMED_OPERATOR_JOIN",
                ),
            )
            if connection["id"] not in bond["source_connection_ids"]:
                bond["source_connection_ids"].append(connection["id"])
    expected = 12 if pdb == "3ZXW" else 0
    if len(bonds) != expected:
        raise ValueError("authentic full assembly disulfide denominator changed")
    endpoints = [partner for key in bonds for partner in key]
    if len(set(endpoints)) != len(endpoints):
        raise ValueError("source assigns multiple disulfides to one sulfur")
    return list(bonds.values())


def pdb_plan(source, inventory, construct, joint_view_id):
    """Retain explicit alternates, all missing positions and original chemicals."""
    if construct not in source.constructs or joint_view_id not in (
        "joint-01",
        "joint-02",
    ):
        raise ValueError("coordinate plan changes the selected material/view")
    pdb = "1BWV" if construct.construct_id.startswith("gp.") else "3ZXW"
    chains = sorted(
        (row for row in inventory.chains if row.pdb_id == pdb),
        key=lambda row: row.chain_id,
    )
    if len(chains) != 16:
        raise ValueError("coordinate plan requires full sixteen-chain assembly")
    chain_map = {
        row.chain_id: "ABCDEFGHIJKLMNOP"[index] for index, row in enumerate(chains)
    }
    atoms = [row for row in inventory.atoms if row.pdb_id == pdb and row.occupancy > 0]
    stock = next(
        row.raw_utf8
        for row in source.source_members
        if row.member_id == "source." + pdb.lower() + "-ph8-pdb"
    )
    states, state_mapping = _protonation_map(chains, atoms, stock)
    grouped = defaultdict(list)
    for atom in atoms:
        grouped[
            (
                atom.chain_id,
                atom.label_seq_id,
                atom.auth_seq_id,
                atom.insertion_code,
                atom.component_id,
            )
        ].append(atom)
    selected, omitted_alternates = [], []
    for group in grouped.values():
        labels = sorted(
            {
                row.alternate_id
                for row in group
                if row.alternate_id not in (".", "?", "")
            }
        )
        scores = {
            label: sum(row.occupancy for row in group if row.alternate_id == label)
            for label in labels
        }
        ordered = sorted(labels, key=lambda label: (-scores[label], label))
        label = (
            ordered[min(1 if joint_view_id == "joint-02" else 0, len(ordered) - 1)]
            if ordered
            else None
        )
        names = set()
        for atom in group:
            if atom.alternate_id not in (".", "?", "", label):
                omitted_alternates.append(
                    (atom.operator_id, atom.source_atom_id, atom.alternate_id)
                )
            elif atom.atom_id in names:
                raise ValueError("one prepared conformer duplicates an atom identity")
            else:
                names.add(atom.atom_id)
                selected.append(atom)
    original = next(
        row.raw_utf8
        for row in source.source_members
        if row.member_id == "source.original-" + pdb.lower() + "-cif"
    )
    disulfides = source_disulfides(original, pdb, inventory, selected, chain_map)
    protein_atoms = defaultdict(list)
    chemicals = defaultdict(list)
    for atom in selected:
        if atom.chain_id in chain_map:
            protein_atoms[atom.chain_id].append(atom)
        else:
            chemicals[
                (
                    atom.chain_id,
                    atom.auth_seq_id,
                    atom.insertion_code,
                    atom.component_id,
                )
            ].append(atom)
    serial = 0
    lines = []
    origins = []
    missing = []
    mutations = []
    complete_chains = []

    def emit(atom, chain, position, component):
        nonlocal serial
        serial += 1
        if serial > 99999 or position > 9999:
            raise ValueError(
                "selected intermediate exceeds native PDB format dimensions"
            )
        name = (
            f" {atom.atom_id:<3}"
            if len(atom.element) == 1 and len(atom.atom_id) < 4
            else f"{atom.atom_id:<4}"
        )
        xyz = tuple(float(x) for x in atom.xyz_angstrom)
        lines.append(
            f"HETATM{serial:5d} {name} {component:>3} {chain}{position:4d}    {xyz[0]:8.3f}{xyz[1]:8.3f}{xyz[2]:8.3f}{1.0:6.2f}{0.0:6.2f}          {atom.element:>2}  \n"
        )
        origins.append(
            dict(
                serial=serial,
                chain=chain,
                position=position,
                atom=atom.atom_id,
                source=(atom.pdb_id, atom.operator_id, atom.source_atom_id),
                source_component=atom.component_id,
                model_component=component,
                source_alternate=atom.alternate_id,
                source_occupancy=str(atom.occupancy),
                original_xyz_angstrom=tuple(str(x) for x in atom.xyz_angstrom),
            )
        )

    for index, chain in enumerate(chains):
        subunit = "lsu" if len(chain.full_sequence) in (493, 475) else "ssu"
        sequence = (
            construct.lsu_sequence if subunit == "lsu" else construct.ssu_sequence
        )
        complete_chains.append(
            dict(
                chain=chain_map[chain.chain_id],
                source_chain=chain.chain_id,
                subunit=subunit,
                sequence=sequence,
            )
        )
        observed = {int(row.label_seq_id) for row in protein_atoms[chain.chain_id]}
        inserted = 0
        for position, original in enumerate(chain.full_sequence, 1):
            if position not in observed:
                if not missing or missing[-1][0:2] != [index, inserted]:
                    missing.append([index, inserted, []])
                missing[-1][2].append(THREE[sequence[position - 1]])
            else:
                inserted += 1
                if sequence[position - 1] != original:
                    mutations.append(
                        (
                            chain_map[chain.chain_id],
                            f"{THREE[original]}-{position}-{THREE[sequence[position - 1]]}",
                        )
                    )
        for atom in sorted(
            protein_atoms[chain.chain_id],
            key=lambda row: (int(row.label_seq_id), row.source_atom_id),
        ):
            position = int(atom.label_seq_id)
            name = states.get((chain.chain_id, position), atom.component_id)
            # Source CYS remains reduced unless authentic disulfide linkage is
            # independently selected. Published CYX alone is not bond evidence.
            emit(atom, chain_map[chain.chain_id], position, name)
        lines.append("TER\n")
    for index, group in enumerate(chemicals.values(), 1):
        for atom in group:
            emit(atom, "Z", index, atom.component_id)
        lines.append("TER\n")
    lines.append("END\n")
    return dict(
        pdb_text="".join(lines),
        missing_residues=missing,
        mutations=mutations,
        complete_chains=complete_chains,
        selected_atom_origins=origins,
        omitted_positive_alternates=omitted_alternates,
        protonation_correspondence=state_mapping,
        desired_histidine_states=tuple(
            (chain_map[chain], position, name)
            for (chain, position), name in sorted(states.items())
        ),
        authenticated_disulfides=disulfides,
        default_unmapped_histidine="HIE",
        cysteine_state="CYX_ONLY_EXPLICIT_SOURCE_DISULFIDES_OTHER_CYS_REDUCED",
        input_coordinate_quantization_max_angstrom=str(Decimal("0.0005")),
        physical_independent_units=0,
        joint_view_id=joint_view_id,
    )
