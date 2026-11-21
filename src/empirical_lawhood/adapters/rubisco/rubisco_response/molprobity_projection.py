# SPDX-License-Identifier: MPL-2.0
"""Coordinate and atom-identity projection into the independent MolProbity format."""

from hashlib import sha256
import json
import math
import re
import struct
from itertools import product

from empirical_lawhood.storage.bounded_io import read_bounded_bytes
from empirical_lawhood.domains.rubisco.rubisco_response.amber_template import RUBP_NAMES


ELEMENTS = {1: "H", 6: "C", 7: "N", 8: "O", 11: "NA", 12: "MG", 15: "P", 16: "S", 17: "CL"}
# Label aliases are reversible. They do not add/remove H or assign connectivity.
COMPONENTS = {"HIE": "HIS", "HID": "HIS", "HIP": "HIS", "CYX": "CYS", "WAT": "HOH", "Na+": "NA", "Cl-": "CL"}
FIELDS = ("group_PDB", "id", "type_symbol", "label_atom_id", "label_alt_id", "label_comp_id", "label_asym_id",
          "label_entity_id", "label_seq_id", "pdbx_PDB_ins_code", "Cartn_x", "Cartn_y", "Cartn_z", "occupancy",
          "B_iso_or_equiv", "auth_seq_id", "auth_comp_id", "auth_asym_id", "auth_atom_id", "pdbx_PDB_model_num")


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def file_sha(path):
    with path.open("rb") as stream:
        from hashlib import file_digest
        return file_digest(stream, "sha256").hexdigest()


def strict_json(raw):
    def unique(pairs):
        result = dict(pairs)
        if len(result) != len(pairs):
            raise ValueError("Duplicated external report field")
        return result
    return json.loads(raw, object_pairs_hook=unique, parse_constant=lambda token: float_rejected(token))


def float_rejected(token):
    raise ValueError("Nonfinite external report field: " + token)


def selected_bytes(path, digest, limit=256 * 2**20):
    if path.is_symlink() or not path.is_file():
        raise ValueError("Select an original regular evidence file")
    raw = read_bounded_bytes(path, maximum_bytes=limit)
    if sha256(raw).hexdigest() != digest:
        raise ValueError("Selected evidence substituted its predeclared SHA-256")
    return raw


def token(value):
    """Quote atom primes while excluding CIF control words and embedded lines."""
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9+'*_-]*", value) or value.lower().startswith(("data_", "save_")):
        raise ValueError("Unsupported exact CIF label: " + repr(value))
    return '"' + value + '"' if "'" in value else value


RUB_REPORT_NAMES = {amber: chemical for chemical, amber in RUBP_NAMES}


def report_atom_name(component, name):
    if component == "RUB":
        return RUB_REPORT_NAMES.get(name, name)
    if component == "KCX" and name == "HN1":
        return "H"
    return {"Na+": "NA", "Cl-": "CL"}.get(name, name)


def project_material(mapped, directory):
    rep = mapped["representation"]
    coordinates = mapped["coordinate_bytes"]
    member, = rep.arrays.members
    if (member.name, member.dtype, member.shape, member.order, member.sha256) != (
            "coordinates-angstrom", "<f8", (len(rep.atoms), 3), "C", sha256(coordinates).hexdigest()):
        raise ValueError("Exact native-order coordinate array differs from its original manifest")
    chains = {c.chain_id: c for c in rep.material.chains}
    by_rid = {row.residue_id: row for row in rep.residues}
    residues, atoms, residue_index = [], [], {}
    added = 0
    for index, atom in enumerate(rep.atoms):
        if atom.source != rep.raw_topology or atom.source_atom_id != str(index + 1):
            raise ValueError("CIF row loses its original Amber atom identity")
        src = by_rid[atom.residue_id]
        if atom.residue_id not in residue_index:
            chain, seq = src.author_chain, src.author_number
            if chain is None:
                chain, seq = "w" + str(added // 9000), 1 + added % 9000
                added += 1
            if src.insertion_code:
                raise ValueError("Unsupported original Amber insertion locator")
            protein = chains.get(src.chain_id)
            position = src.sequence_position_1based
            critical = protected(src.chain_id, protein.subunit if protein else None, position, src.site_id)
            row = dict(id=src.residue_id, chain=chain, seq=seq, component=COMPONENTS.get(src.component, src.component),
                       original_component=src.component, original_chain=src.author_chain, original_number=src.author_number,
                       role=src.role, chain_id=src.chain_id, site=src.site_id, critical=critical,
                       position=position, chain_length=len(protein.sequence) if protein else None)
            residue_index[atom.residue_id] = len(residues)
            residues.append(row)
        name = report_atom_name(src.component, atom.name)
        atoms.append([residue_index[atom.residue_id], name, ELEMENTS[atom.atomic_number]])
    return write_projection(directory, residues, atoms, ((b.first, b.second) for b in rep.bonds),
                            coordinates, mapped["box_angstrom"], [s.site_id for s in rep.sites],
                            native_names=[a.name for a in rep.atoms])


def protected(chain_id, subunit, position, site):
    labels = [site] if site else []
    if (subunit == "SSU" and position in (1, 95)) or (subunit == "LSU" and position == 213):
        labels.append(f"{chain_id}.position.{position}")
    if subunit == "LSU" and (1 <= position <= 14 or 487 <= position <= 493):
        labels.append(f"{chain_id}.modeled-terminal-segments")
    return labels


def critical_neighbors(residues, atoms, coordinates, cell):
    """All residue contacts within five Å of original SSU95 heavy atoms or site Mg."""
    import numpy as np
    from scipy.spatial import cKDTree
    reach = 5.0
    points = np.frombuffer(coordinates, dtype="<f8").reshape(-1, 3)
    heavy = [i for i,a in enumerate(atoms) if a[2] != "H"]
    anchors = {}
    for ri, r in enumerate(residues):
        names = [s for s in r["critical"] if s.endswith(".position.95")]
        if r["role"] == "MAGNESIUM" and r["site"]:
            names.append(r["site"] + ".magnesium")
        for label in names:
            if label in anchors:
                raise ValueError("Protected-geometry anchor has multiple original residues")
            anchors[label] = ri
    if not anchors:
        return {}
    if cell is None:
        space = points[heavy]
        tree = cKDTree(space)
        radius = reach
    else:
        a,b,c,alpha,beta,gamma = map(float,cell)
        ca,cb,cg = np.cos(np.deg2rad([alpha,beta,gamma]))
        sg = math.sin(math.radians(gamma))
        cy = (ca-cb*cg)/sg
        lattice = np.array([[a,0,0],[b*cg,b*sg,0],[c*cb,c*cy,c*math.sqrt(1-cb*cb-cy*cy)]])
        inverse = np.linalg.inv(lattice)
        space = (points[heavy] @ inverse) % 1
        # Floating modulo can return its upper endpoint for negative values near zero.
        space[space == 1] = 0
        tree = cKDTree(space,boxsize=1)
        radius = np.nextafter(reach * np.linalg.norm(inverse, 2), math.inf)
        bounds = np.floor(.5 + reach*np.linalg.norm(inverse,axis=0)).astype(int)
        shifts = np.array(list(product(*(range(-n, n+1) for n in bounds))))
    atom_rows = {}
    for i, atom_index in enumerate(heavy):
        atom_rows.setdefault(atoms[atom_index][0], []).append(i)
    record = {}
    for label, anchor in anchors.items():
        nearest = {}
        for h in atom_rows[anchor]:
            for j in tree.query_ball_point(space[h],radius):
                ai, aj = heavy[h], heavy[j]
                other = atoms[aj][0]
                if other == anchor:
                    continue
                delta = space[j] - space[h]
                if cell is None:
                    distance = float(np.linalg.norm(delta))
                else:
                    centered = delta - np.rint(delta)
                    distance = float(np.min(np.linalg.norm((centered + shifts) @ lattice, axis=1)))
                observation = (distance, ai, aj)
                if distance <= reach and (other not in nearest or observation < nearest[other]):
                    nearest[other] = observation
        rows = []
        for other, (distance, ai, aj) in sorted(nearest.items()):
            residues[other]["critical"].append("neighbors-of." + label)
            rows.append(dict(residue_index=other, native_atom_indices=[ai,aj], minimum_distance_angstrom=distance))
        record[label] = dict(anchor_residue_index=anchor, heavy_radius_angstrom=reach, neighbors=rows)
    return record


def write_projection(directory, residues, atoms, edges, coordinates, cell, sites, *, native_names=None):
    if native_names is None:
        native_names = [name for _,name,_ in atoms]
    native_keys = {(ri, source_name) for (ri,_,_),source_name in zip(atoms,native_names,strict=True)}
    if len(native_keys) != len(atoms) or len({(ri, name) for ri, name, _ in atoms}) != len(atoms):
        raise ValueError("Validator atom-name projection is not bijective within each original residue")
    keys = {(r["chain"], r["seq"]) for r in residues}
    if len(keys) != len(residues):
        raise ValueError("CIF projection has ambiguous residue locators")
    if cell is not None and (len(cell) != 6 or any(not math.isfinite(float(v)) or float(v) <= 0 for v in cell)):
        raise ValueError("Periodic model needs its original six finite cell parameters")
    # CCTBX can translate Cartesian coordinates when it invents symmetry for a box-free
    # model. Give the reader an explicit isolated computational box and keep original cell=null.
    if cell is None:
        points = struct.iter_unpack("<ddd", coordinates)
        lower = [math.inf] * 3
        upper = [-math.inf] * 3
        for point in points:
            for j, v in enumerate(point):
                lower[j], upper[j] = min(lower[j], v), max(upper[j], v)
        reader_cell = [hi-lo+40.0 for lo,hi in zip(lower,upper,strict=True)] + [90,90,90]
    else:
        reader_cell = cell
    entities = {}
    with (directory / "model.cif").open("x", encoding="ascii", newline="\n") as stream:
        stream.write("data_EL_Gp_endpoint\n")
        if cell is None:
            stream.write("# Nonperiodic source. P1 is an isolated reader box with 40 A image separation.\n")
        if reader_cell:
            for k, v in zip(("length_a", "length_b", "length_c", "angle_alpha", "angle_beta", "angle_gamma"), reader_cell, strict=True):
                stream.write(f"_cell.{k} {v}\n")
            stream.write("_symmetry.space_group_name_H-M 'P 1'\n")
        stream.write("#\nloop_\n")
        stream.writelines(f"_atom_site.{f}\n" for f in FIELDS)
        for i, ((ri, name, elem), point) in enumerate(zip(atoms, struct.iter_unpack("<ddd", coordinates), strict=True)):
            if not all(map(math.isfinite, point)):
                raise ValueError("Standalone CIF projection needs every finite original coordinate")
            r = residues[ri]
            chain, seq, comp = r["chain"], r["seq"], r["component"]
            entity = r["chain_id"] or comp
            eid = entities.setdefault(entity, len(entities) + 1)
            asym = chain if r["role"] == "PROTEIN" else ("W" + chain if r["role"] == "WATER" else "N" + str(ri))
            values = ("ATOM" if r["role"] == "PROTEIN" else "HETATM", str(i + 1), elem, token(name), ".",
                      token(comp), token(asym), str(eid), str(seq) if r["role"] == "PROTEIN" else ".", "?",
                      *(format(v, ".17g") for v in point), "1", "0", str(seq), token(comp), token(chain), token(name), "1")
            stream.write(" ".join(values) + "\n")
        stream.write("#\n")
    eligible = [a[2] != "H" and residues[a[0]]["role"] in ("PROTEIN", "LIGAND") for a in atoms]
    bonds = sorted([min(a, b), max(a, b)] for a, b in edges if eligible[a] and eligible[b])
    if len({tuple(b) for b in bonds}) != len(bonds):
        raise ValueError("Duplicate native covalent bond")
    neighborhood = critical_neighbors(residues, atoms, coordinates, cell)
    digest = sha256(coordinates).hexdigest()
    table = dict(critical_heavy_neighbors=neighborhood, residues=residues, atoms=atoms, native_atom_names=native_names, heavy_covalent_bonds=bonds,
                 cell_angstrom_degrees=list(map(str, cell)) if cell is not None else None,
                 reader_cell_angstrom_degrees=list(map(str, reader_cell)), coordinate_array_sha256=digest)
    (directory / "atom-map.json").write_bytes(json_bytes(table))
    return dict(atom_count=len(atoms), residues=len(residues), sites=sites, coordinate_array_sha256=digest,
                assigned_critical_neighbors={k:len(v["neighbors"]) for k,v in neighborhood.items()},
                modeled_lsu_terminal_residues=sum(any(tag.endswith(".modeled-terminal-segments") for tag in r["critical"]) for r in residues),
                hydrogen_count=sum(a[2] == "H" for a in atoms), mmcif_sha256=file_sha(directory / "model.cif"),
                atom_map_sha256=file_sha(directory / "atom-map.json"))
