# SPDX-License-Identifier: MPL-2.0
"""Supplementary Ramachandran observations with the selected CCTBX installation."""

import importlib.util
from itertools import product
import json
import math
from pathlib import Path
import sys


def target_backbones(table):
    """Join each quartet by actual selected residue, element, atom and Amber edge."""
    residues, atoms = table["residues"], table["atoms"]
    chains = sorted({r["chain"] for r in residues if r["role"] == "PROTEIN" and r["chain_length"] == 493})
    if len(chains) != 8:
        raise ValueError("Gp backbone supplement requires eight complete original large-subunit chains")
    lookup = {(r["chain"], r["position"]): i for i, r in enumerate(residues)
              if r["role"] == "PROTEIN" and r["chain"] in chains}
    if len(lookup) != sum(r["role"] == "PROTEIN" and r["chain"] in chains for r in residues):
        raise ValueError("Duplicate prepared large-subunit residue")
    native = {(ri, name): (i, elem) for i, (ri, name, elem) in enumerate(atoms)}
    if len(native) != len(atoms):
        raise ValueError("Ambiguous selected native backbone atom")
    bonds = {tuple(bond) for bond in table["heavy_covalent_bonds"]}
    expected = {208: "PHE", 209: "VAL", 210: "KCX", 211: "ASP", 212: "ASP", 213: "GLU"}
    rows = []
    for chain in chains:
        for pos in (208, 209, 210, 211, 212):
            component = expected[pos]
            kind = "NATIVE_FLANK_CONTROL" if pos in (208, 212) else "KCX_NEIGHBORHOOD"
            transfer = "PARENT_LYS_GENERAL_PROXY" if pos == 210 else "STANDARD_AMINO_ACID"
            row = dict(chain=chain, position=pos, component=component, role=kind, reference_scope=transfer,
                       reference_class="isoleucine or valine" if pos == 209 else "general",
                       native_residue_index=lookup.get((chain, pos)), status="UNEVALUABLE")
            rows.append(row)
            positions = [lookup.get((chain, j)) for j in (pos-1, pos, pos+1)]
            if None in positions:
                row["reason"] = "missing-protein-position"
                continue
            prev, center, following = positions
            row["residue_id"] = residues[center]["id"]
            if any(residues[ri]["component"] != expected[j] or residues[ri]["original_component"] != expected[j]
                   for ri, j in ((center, pos), (following, pos+1))):
                row["reason"] = "source-residue-or-reference-context-differs"
                continue
            keys = ((prev, "C"), (center, "N"), (center, "CA"), (center, "C"), (following, "N"))
            mapped = [native.get(key) for key in keys]
            if any(item is None or item[1] != element for item, element in zip(mapped, "CNCCN", strict=True)):
                row["reason"] = "missing-native-backbone-atom-or-element"
                continue
            indices = [item[0] for item in mapped]
            if any(table["native_atom_names"][i] != name for i, (_, name) in zip(indices, keys, strict=True)):
                row["reason"] = "substituted-original-amber-backbone-name"
                continue
            row["native_atom_indices"] = indices
            missing = [sorted((a,b)) for a,b in zip(indices, indices[1:]) if tuple(sorted((a,b))) not in bonds]
            if missing:
                row.update(reason="missing-original-covalent-bond", missing_native_edges=missing)
                continue
            row["status"] = "MAPPED"
    return rows


def connected_points(xyz, physical_cell):
    """Unwrap along four authenticated covalent edges of the selected peptide."""
    import numpy as np
    if physical_cell is None:
        return xyz, []
    from cctbx import uctbx
    cell = uctbx.unit_cell(tuple(map(float, physical_cell)))
    lattice = np.array([cell.orthogonalize(e) for e in np.eye(3)])
    inverse = np.linalg.inv(lattice)
    result, shifts = [np.asarray(xyz[0])], []
    for a, b in zip(xyz, xyz[1:]):
        delta = np.asarray(b) - a
        frac = delta @ inverse
        nearest = np.floor(frac+.5).astype(int)
        remainder = frac-nearest
        # A better image must be inside the sphere through the rounded candidate.
        # A fractional component is bounded by radius times its reciprocal-axis norm.
        radius = np.linalg.norm(remainder @ lattice)
        limits = radius*np.linalg.norm(inverse, axis=0) + 1e-9
        options = product(*(range(math.ceil(f-d), math.floor(f+d)+1) for f,d in zip(remainder, limits, strict=True)))
        lengths = sorted((float(np.linalg.norm((remainder-candidate) @ lattice)), candidate) for candidate in options)
        if not lengths or len(lengths) > 1 and math.isclose(lengths[0][0], lengths[1][0], rel_tol=1e-12, abs_tol=1e-12):
            raise ValueError("Peptide bond has no unique nearest periodic image")
        shift = nearest+lengths[0][1]
        result.append(result[-1] + (delta - shift @ lattice))
        shifts.append(shift.tolist())
    return result, shifts


def signed_angle(points):
    """Independent signed atan2 and explicit degeneracy check, in degrees."""
    import numpy as np
    a, b, c, d = np.asarray(points)
    ab, bc, cd = b-a, c-b, d-c
    left, right = np.cross(ab, bc), np.cross(bc, cd)
    if np.linalg.norm(bc) == 0 or np.linalg.norm(left)*np.linalg.norm(right) < 1e-12:
        raise ValueError("Degenerate backbone torsion")
    return math.degrees(math.atan2(float(np.dot(np.cross(left, right), bc/np.linalg.norm(bc))),
                                   float(np.dot(left, right))))


def score_points(points, class_name, evaluator):
    from cctbx import geometry_restraints
    from mmtbx.validation import ramalyze
    angles = []
    for quartet in (points[:4], points[1:]):
        independent = signed_angle(quartet)
        observed = geometry_restraints.dihedral(sites=[tuple(p) for p in quartet], angle_ideal=-40, weight=1).angle_model
        if not math.isfinite(observed) or abs(math.remainder(independent-observed, 360)) > 1e-8:
            raise ValueError("Signed backbone convention differs from CCTBX ramalyze")
        angles.append(observed)
    score = float(evaluator.evaluate(class_name, angles))
    if not math.isfinite(score) or not 0 <= score <= 1:
        raise ValueError("Invalid CCTBX Ramachandran reference value")
    category = ramalyze.rama_types[ramalyze.ramalyze.evalScore(ramalyze.res_types_dict[class_name], score)].upper()
    return dict(phi_deg=angles[0], psi_deg=angles[1], cctbx_raw_table_value=score, ramalyze_score=100*score,
                category=category, outlier=category == "OUTLIER")


def calculate(cif, mapping):
    from iotbx import pdb
    from mmtbx.rotamer.ramachandran_eval import RamachandranEval
    spec = importlib.util.spec_from_file_location("el_pinned_molprobity_driver", Path(__file__).with_name("molprobity_driver.py"))
    shared = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(shared)
    table = json.loads(mapping.read_bytes())
    structure = pdb.input(file_name=str(cif))
    if not all(math.isclose(float(a), b, rel_tol=1e-14, abs_tol=1e-12)
               for a, b in zip(table["reader_cell_angstrom_degrees"], structure.crystal_symmetry().unit_cell().parameters(), strict=True)):
        raise ValueError("CCTBX read another selected reader cell")
    hierarchy = structure.construct_hierarchy()
    census = shared.atom_census(hierarchy, table)
    rows = target_backbones(table)
    atoms, residues = table["atoms"], table["residues"]
    index = {}
    for i in {i for row in rows if row["status"] == "MAPPED" for i in row["native_atom_indices"]}:
        ri, name, _ = atoms[i]
        r = residues[ri]
        index[r["chain"], r["seq"], r["component"], name] = i
    coords = {}
    for a in hierarchy.atoms_with_labels():
        key = (a.chain_id.strip(), int(a.resseq.strip()), a.resname.strip(), a.name.strip())
        if key in index:
            coords[index[key]] = tuple(a.xyz)
    evaluator = RamachandranEval()
    for row in rows:
        if row["status"] == "MAPPED":
            try:
                points, shifts = connected_points([coords[i] for i in row["native_atom_indices"]], table["cell_angstrom_degrees"])
                row.update(score_points(points, row["reference_class"], evaluator), periodic_bond_image_shifts=shifts, status="MEASURED")
            except ValueError as error:
                row.update(status="UNEVALUABLE", reason=str(error))
    return dict(input_census=census, rows=rows)


if __name__ == "__main__":
    source, mapping, destination = map(Path, sys.argv[1:])
    result = calculate(source, mapping)
    with destination.open("x") as stream:
        json.dump(result, stream, sort_keys=True, allow_nan=False, separators=(",", ":"))
        stream.write("\n")
