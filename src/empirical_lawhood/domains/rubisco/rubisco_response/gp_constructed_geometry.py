# SPDX-License-Identifier: MPL-2.0
"""Explicit stereochemical initialization of reconstructed Gp terminal atoms.

The original completion is a geometric hypothesis. Only atoms explicitly
constructed by that completion may move. Observed source atoms, identities,
serials, TER and CONECT records are preserved exactly. This creates a new
starting pose for subsequent MM repair, never an admitted relaxed structure.
"""

import math

import numpy as np

from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.serialized_heavy_pdb import read_serialized_heavy_pdb


def origin_mobility(heavy_text, origin):
    atoms = read_serialized_heavy_pdb(heavy_text).atoms
    rows = origin["complete_heavy_atoms"]
    declared = {(r["chain"],r["position"],r["atom"]):r for r in rows}
    keys = {(a["chain"],a["position"],a["atom"]) for a in atoms}
    if len(declared) != len(rows) or keys != set(declared):
        raise ValueError("geometry correction loses the complete original atom-origin census")
    selected = []
    for atom in atoms:
        key = atom["chain"],atom["position"],atom["atom"]
        row = declared[key]
        if (row["component"],row["element"].upper()) != (atom["component"],atom["element"]):
            raise ValueError("geometry correction substitutes an original atom identity")
        if row["status"] == "DECLARED_CONSTRUCTED_MUTANT_OR_MISSING_ATOM":
            if row["source_origin"] is not None:
                raise ValueError("constructed geometry incorrectly claims an observed source atom")
            selected.append(key)
        elif row["status"] != "INHERITED_OBSERVED_SOURCE" or row["source_origin"] is None:
            raise ValueError("geometry correction has an ambiguous atom origin")
    return atoms,tuple(sorted(selected))


def replace_heavy_coordinates(text, coordinates, permitted):
    """Preserve every original noncoordinate byte, including observed atom rows."""
    permitted = set(permitted)
    actual = {(a["chain"],a["position"],a["atom"]) for a in read_serialized_heavy_pdb(text).atoms}
    if not set(coordinates) <= permitted <= actual:
        raise ValueError("geometry correction attempts to move an observed atom")
    output = []
    for line in text.splitlines(keepends=True):
        if line.startswith(("ATOM  ","HETATM")):
            key = line[21],int(line[22:26]),line[12:16].strip()
            if key in coordinates:
                xyz = coordinates[key]
                if len(xyz) != 3 or not np.isfinite(np.asarray(xyz,float)).all():
                    raise ValueError("geometry correction has nonfinite coordinates")
                value = "".join(f"{v:8.3f}" for v in xyz)
                if len(value) != 24:
                    raise ValueError("geometry correction exceeds its fixed-column coordinate format")
                line = line[:30]+value+line[54:]
        output.append(line)
    result = "".join(output)
    read_serialized_heavy_pdb(result)
    return result


def _volume(points, centre, names):
    return float(np.linalg.det(np.array([points[n]-points[centre] for n in names])))


def _plane_normal(centre, first, second):
    normal = np.cross(first-centre,second-centre)
    length = np.linalg.norm(normal)
    if length < 1e-10:
        raise ValueError("constructed stereocentre has a degenerate backbone frame")
    return normal/length


def _omega(points):
    a,b,c,d = points
    axis = c-b
    length = np.linalg.norm(axis)
    if length < 1e-10:
        raise ValueError("constructed peptide has a degenerate bond axis")
    axis /= length
    first,last = a-b,d-c
    first -= axis*np.dot(first,axis)
    last -= axis*np.dot(last,axis)
    if min(np.linalg.norm(first),np.linalg.norm(last)) < 1e-10:
        raise ValueError("constructed peptide has a degenerate dihedral")
    return math.atan2(np.dot(np.cross(axis,first),last),np.dot(first,last))


def initialize_constructed_geometry(heavy_text, origin):
    """Restore declared L stereochemistry and trans non-Pro terminal junctions.

    Reflect a wholly constructed side chain in the N/CA/C plane to correct CA.
    Correct Ile/Thr CB separately by reflecting its terminal CG2 branch. Both
    transformations preserve the affected internal distances. The declared
    trans initialization at a constructed non-Pro N-terminal junction rotates
    only the constructed prefix around that peptide bond. MM relaxation and
    independent complete geometry assessment must still follow.
    """
    atoms,movable = origin_mobility(heavy_text,origin)
    permitted = set(movable)
    xyz = {(a["chain"],a["position"],a["atom"]):np.array(a["xyz"],float) for a in atoms}
    residues = {}
    for atom in atoms:
        if atom["chain"] != "Z":
            residues.setdefault((atom["chain"],atom["position"],atom["component"]),[]).append(atom["atom"])
    changes = []
    for (chain,position,component),names in residues.items():
        points = {n:xyz[(chain,position,n)] for n in names}
        if {"N","CA","C","CB"} <= set(points):
            volume = _volume(points,"CA",("N","C","CB"))
            if volume <= 0:
                chosen = tuple(n for n in names if n not in {"N","CA","C","O","OXT"})
                if not {(chain,position,n) for n in chosen} <= permitted:
                    raise ValueError("incorrect observed stereochemistry cannot be repaired as constructed geometry")
                normal = _plane_normal(points["CA"],points["N"],points["C"])
                for name in chosen:
                    value = points[name]-points["CA"]
                    xyz[(chain,position,name)] = points["CA"]+value-2*np.dot(value,normal)*normal
                changes.append(dict(kind="constructed-CA-reflection",chain=chain,position=position,
                    before_volume_angstrom3=volume,atoms=chosen))
        points = {n:xyz[(chain,position,n)] for n in names}
        branch = "CG1" if component == "ILE" else "OG1" if component == "THR" else None
        if branch is not None:
            volume = _volume(points,"CB",("CA",branch,"CG2"))
            if volume <= 0:
                key = chain,position,"CG2"
                if key not in permitted:
                    raise ValueError("incorrect observed beta stereochemistry is outside constructed geometry")
                normal = _plane_normal(points["CB"],points["CA"],points[branch])
                value = points["CG2"]-points["CB"]
                xyz[key] = points["CB"]+value-2*np.dot(value,normal)*normal
                changes.append(dict(kind="constructed-CB-reflection",chain=chain,position=position,
                    before_volume_angstrom3=volume,atoms=("CG2",)))
    for (chain,position,component),names in residues.items():
        if position != 14 or component != "THR" or (chain,14,"CA") not in permitted:
            continue
        keys = ((chain,14,"CA"),(chain,14,"C"),(chain,15,"N"),(chain,15,"CA"))
        if not all(k in xyz for k in keys) or (chain,15,"CA") in permitted:
            raise ValueError("Gp terminal correction loses its observed residue-15 anchor")
        points = [xyz[k].copy() for k in keys]
        before = _omega(points)
        if abs(before) >= math.radians(150):
            continue
        chosen = tuple(k for k in xyz if k[0] == chain and k[1] <= 14)
        if not set(chosen) <= permitted:
            raise ValueError("terminal peptide correction crosses an observed atom")
        axis = points[2]-points[1]
        axis /= np.linalg.norm(axis)
        angle = before-math.pi
        cosine,sine = math.cos(angle),math.sin(angle)
        pivot = points[1]
        for key in chosen:
            value = xyz[key]-pivot
            xyz[key] = pivot+cosine*value+sine*np.cross(axis,value)+(1-cosine)*np.dot(axis,value)*axis
        after = _omega([xyz[k].copy() for k in keys])
        if abs(abs(after)-math.pi)>1e-8:
            raise ValueError("constructed terminal peptide did not reach its declared trans initialization")
        changes.append(dict(kind="constructed-trans-terminal-peptide",chain=chain,position=14,
            before_omega_degrees=math.degrees(before),after_omega_degrees=math.degrees(after),
            rotated_atom_count=len(chosen)))
    initialized = replace_heavy_coordinates(heavy_text,{k:xyz[k] for k in movable},movable)
    from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology import heavy_pdb_rows
    from empirical_lawhood.domains.rubisco.rubisco_response.gp_heavy_geometry import heavy_stereochemistry
    if heavy_stereochemistry(heavy_pdb_rows(initialized))[1]:
        raise ValueError("constructed initialization retains an inverted or planar stereocentre")
    return initialized,tuple(changes),movable
