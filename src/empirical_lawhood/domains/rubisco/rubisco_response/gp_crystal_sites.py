# SPDX-License-Identifier: MPL-2.0
"""Two local coordinate hypotheses for the inhibited 1BWV active sites."""

from decimal import Context, Decimal, localcontext
from hashlib import sha256

from empirical_lawhood.domains.rubisco.rubisco_insilico_structure.science import (
    cif_tables,
    expand,
)
from empirical_lawhood.science.records.serialization import canonical_json_bytes


DEPOSIT_SHA256 = "4fe0d7197062a6643568937520582a58673a91d032ed313a8c37545d22a0d6b6"
REDO_SHA256 = "e5d349591ad52b46d594ef985b3539ac8f319477309f33bc9e9446805ced71d2"
SELECTIONS = ("acid-sidechains", "first-shell")
SITE = {("201", "KCX"), ("203", "ASP"), ("204", "GLU"), ("490", "MG"), ("491", "CAP")}
ACIDS = {"ASP": {"CB", "CG", "OD1", "OD2"}, "GLU": {"CB", "CG", "CD", "OE1", "OE2"}}


def _key(row):
    return tuple(
        row[name]
        for name in (
            "auth_asym_id",
            "auth_seq_id",
            "pdbx_PDB_ins_code",
            "auth_comp_id",
            "auth_atom_id",
            "label_alt_id",
        )
    )


def select_gp_crystal_sites(
    deposition: bytes, refinement: bytes, selection: str
) -> bytes:
    """Return canonical exact assembly edits. Admission belongs to a subsequent independent read."""
    if selection not in SELECTIONS:
        raise ValueError("Select a registered 1BWV inherited-coordinate hypothesis")
    if (
        sha256(deposition).hexdigest() != DEPOSIT_SHA256
        or sha256(refinement).hexdigest() != REDO_SHA256
    ):
        raise ValueError(
            "Select the original 1BWV and the pinned PDB-REDO coordinate bytes"
        )
    # The source transformation has finite decimal inputs. Use a local context sufficient
    # for every product and sum regardless of the caller's decimal precision.
    with localcontext(Context(prec=50)):
        original, _, operators = expand("1BWV", deposition.decode())
        redo = cif_tables(refinement.decode())["_atom_site"]
        other = {_key(row): row for row in redo}
        if len(other) != len(redo):
            raise ValueError("Ambiguous refined atom identity")
        transforms = {op: (matrix, shift) for _, op, matrix, shift in operators}
        edits = []
        for atom in original:
            if (
                atom.auth_asym_id not in ("A", "C", "E", "G")
                or (atom.auth_seq_id, atom.component_id) not in SITE
            ):
                continue
            if selection == "acid-sidechains" and atom.atom_id not in ACIDS.get(
                atom.component_id, ()
            ):
                continue
            key = (
                atom.auth_asym_id,
                atom.auth_seq_id,
                atom.insertion_code,
                atom.component_id,
                atom.atom_id,
                atom.alternate_id,
            )
            candidate = other[key]
            if (
                candidate["type_symbol"] != atom.element
                or Decimal(candidate["occupancy"]) != atom.occupancy
                or candidate["pdbx_PDB_model_num"] != "1"
            ):
                raise ValueError(
                    "Incompatible refined atom occupancy, model or element"
                )
            matrix, shift = transforms[atom.operator_id]
            xyz = tuple(Decimal(candidate["Cartn_" + axis]) for axis in "xyz")
            destination = tuple(
                sum((matrix[3 * i + j] * xyz[j] for j in range(3)), shift[i])
                for i in range(3)
            )
            edits.append(
                dict(
                    operator=atom.operator_id,
                    deposited_atom_id=atom.source_atom_id,
                    refined_atom_id=candidate["id"],
                    author_atom=key,
                    element=atom.element,
                    occupancy=atom.occupancy,
                    label_asym=atom.label_asym_id,
                    label_seq=atom.label_seq_id,
                    original_A=atom.xyz_angstrom,
                    selected_A=destination,
                )
            )
    return canonical_json_bytes(
        dict(
            schema="el.gp.inhibited-crystal-site-candidate.v1",
            selection=selection,
            source_sha256=DEPOSIT_SHA256,
            comparator_sha256=REDO_SHA256,
            domain="INHERITED_COORDINATE_HYPOTHESIS",
            assembly_atoms=len(original),
            edits=tuple(edits),
        )
    )
