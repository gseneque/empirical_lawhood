# SPDX-License-Identifier: MPL-2.0
"""Construct missing terminal residues from retained Amber Cartesian templates.

This is a steric starting-pose heuristic. It is not an energy, ensemble, or
rate calculation. Original coordinates and all original atom identities stay
fixed. Subsequent original-potential minimization and assessment are required.
"""
import math
import shlex

import numpy as np
from scipy.spatial import cKDTree


def read_templates(text):
    sections = {}
    current = None
    for line in text.splitlines():
        if line.startswith("!entry."):
            current = line.split()[0][7:]
            if current in sections:
                raise ValueError("Amber template repeats a selected data section")
            sections[current] = []
        elif line.startswith("!"):
            current = None
        elif current is not None and line.strip():
            sections[current].append(shlex.split(line))
    result = {}
    for key, atoms in sections.items():
        if not key.endswith(".unit.atoms"):
            continue
        name = key.split(".")[0]
        positions = sections[name + ".unit.positions"]
        if len(atoms) != len(positions):
            raise ValueError("Amber template atom/coordinate denominator differs")
        coordinates = {}
        elements = {}
        for row, xyz in zip(atoms, positions, strict=True):
            if int(row[6]) != 1:
                if row[0] in coordinates or len(xyz) != 3 or not np.isfinite(np.array(xyz,float)).all():
                    raise ValueError("Amber template has duplicate or nonfinite heavy coordinates")
                coordinates[row[0]] = np.array(xyz, float)
                elements[row[0]] = int(row[6])
        result[name] = coordinates, elements
    return result


def peptide_parameters(parm_dat, frcmod):
    """Read the actual selected stock's peptide bond and junction angles."""
    from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.preparation import _frcmod_sections, _parm_dat_sections
    wanted = {("C","N"):"peptide_length", ("CX","C","N"):"ca_c_n_angle",
              ("C","N","CX"):"c_n_ca_angle"}
    result = {}
    for sections in (_parm_dat_sections(parm_dat), _frcmod_sections(frcmod)):
        for name,count in (("BOND",2),("ANGLE",3)):
            width=3*count-1
            for line in sections[name]:
                types=tuple(value.strip() for value in line[:width].split("-"))
                key=types if types in wanted else types[::-1]
                if key in wanted:
                    value=float(line[width:].split()[1])
                    if not math.isfinite(value) or value<=0 or (count==3 and value>=180):
                        raise ValueError("selected peptide parameter is outside its geometric domain")
                    result[wanted[key]]=value if count==2 else math.radians(value)
    if set(result)!=set(wanted.values()):
        raise ValueError("selected Amber stock lacks a complete peptide junction geometry")
    return result


def unit(vector):
    length = np.linalg.norm(vector)
    if length < 1e-10:
        raise ValueError("terminal construction encountered a degenerate frame")
    return vector / length


def angle(first, centre, last):
    return math.acos(float(np.clip(np.dot(unit(first-centre), unit(last-centre)), -1, 1)))


def place(a, b, c, length, theta, torsion):
    """Place D with specified C-D length, B-C-D angle, and A-B-C-D torsion."""
    axis = unit(c-b)
    normal = unit(np.cross(b-a, axis))
    across = np.cross(normal, axis)
    return c + length * (-math.cos(theta)*axis + math.sin(theta) * (
        math.cos(torsion)*across + math.sin(torsion)*normal))


def frame(points):
    along = unit(points["N"] - points["CA"])
    normal = unit(np.cross(along, points["C"]-points["CA"]))
    return np.array([along, np.cross(normal, along), normal])


def orient(template, backbone):
    rotation = frame(template).T @ frame(backbone)
    if np.linalg.det(rotation) < 0.999999:
        raise ValueError("terminal construction attempted a stereochemical reflection")
    result = {name: (xyz-template["CA"]) @ rotation + backbone["CA"]
              for name, xyz in template.items()}
    for name in ("N", "CA", "C"):
        if np.linalg.norm(result[name]-backbone[name]) > 1e-5:
            raise ValueError("backbone construction is inconsistent with the template geometry")
    return result


def rotate_sidechain(points, theta, component):
    result = {k: v.copy() for k, v in points.items()}
    if "CB" not in points or component == "PRO" or theta == 0:
        return result
    axis = unit(points["CB"]-points["CA"])
    for name in set(points)-{"N", "CA", "C", "O", "OXT", "CB"}:
        v = points[name]-points["CB"]
        result[name] = points["CB"] + math.cos(theta)*v + math.sin(theta)*np.cross(axis, v) + (
            1-math.cos(theta))*np.dot(axis, v)*axis
    return result


class StericEnvironment:
    """A dimensionless overlap score; no physical-energy interpretation."""
    def __init__(self, coordinates):
        self.coordinates = dict(coordinates)
        self.rebuild()

    def rebuild(self):
        self.keys = tuple(self.coordinates)
        self.values = np.array([self.coordinates[k] for k in self.keys])
        self.tree = cKDTree(self.values)

    def add(self, chain, position, points):
        self.coordinates.update({(chain, position, name): xyz for name, xyz in points.items()})
        self.rebuild()

    def score(self, chain, position, points):
        names = tuple(points)
        locations = np.array([points[n] for n in names])
        neighbours = self.tree.query_ball_point(locations, 3.2)
        score = 0.0
        minimum = float("inf")
        for i, js in enumerate(neighbours):
            for j in js:
                other_chain, other_position, other_name = self.keys[j]
                # Omit inter-residue 1-2 and 1-3 pairs at the one new junction.
                pair = (names[i], other_name)
                if other_chain == chain:
                    if other_position == position+1 and pair in {
                            ("C", "N"), ("CA", "N"), ("O", "N"), ("C", "CA")}:
                        continue
                    if other_position == position-1 and pair in {
                            ("N", "C"), ("N", "CA"), ("N", "O"), ("CA", "C")}:
                        continue
                distance = float(np.linalg.norm(locations[i]-self.values[j]))
                minimum = min(minimum, distance)
                score += (3.2/max(distance, 0.01))**12-1
        return score, minimum


def build_terminals(heavy_text, origin, libraries, *, peptide_length, ca_c_n_angle, c_n_ca_angle):
    from empirical_lawhood.domains.rubisco.rubisco_response.gp_constructed_geometry import origin_mobility, replace_heavy_coordinates
    atoms, permitted = origin_mobility(heavy_text, origin)
    allowed = set(permitted)
    residues = {}
    components, atom_elements = {}, {}
    xyz = {}
    for atom in atoms:
        key = atom["chain"], atom["position"]
        residues.setdefault(key, []).append(atom["atom"])
        components[key] = atom["component"]
        xyz[(*key, atom["atom"])] = np.array(atom["xyz"], float)
        atom_elements[(*key, atom["atom"])] = atom["element"].upper()
    missing = {key for key, names in residues.items() if any((*key, n) in allowed for n in names)}
    partial = {key for key in missing if not all((*key, n) in allowed for n in residues[key])}
    retained = {}
    for key in partial:
        names = {n for n in residues[key] if (*key, n) in allowed}
        if components[key] != "MET" or key[1] != 1 or names != {"CG", "SD", "CE"}:
            raise ValueError("terminal reconstruction has an unsupported partial residue")
        retained.update({(*key, n): xyz[(*key, n)] for n in names})
    missing -= partial
    environment = StericEnvironment({k:v for k,v in xyz.items() if k not in allowed or k in retained})
    grid = tuple(math.radians(n) for n in range(-180, 180, 30))
    result, events = dict(retained), []
    for chain in sorted({c for c, _ in missing}):
        positions = sorted(p for c, p in residues if c == chain)
        absent = {p for c, p in missing if c == chain}
        observed = sorted(set(positions)-absent)
        if not observed:
            raise ValueError("terminal construction has no observed anchor")
        interior = absent - set(range(positions[0], observed[0])) - set(range(observed[-1]+1, positions[-1]+1))
        if interior:
            raise ValueError("terminal construction refuses missing internal loops")
        order = [(p, -1) for p in range(observed[0]-1, positions[0]-1, -1)]
        order += [(p, 1) for p in range(observed[-1]+1, positions[-1]+1)]
        for position, direction in order:
            component = components[chain, position]
            prefix = "N" if position == positions[0] else "C" if position == positions[-1] else ""
            template, elements = libraries[prefix + component]
            if not {"N", "CA", "C", "O"} <= set(template):
                raise ValueError("selected Amber template has an incomplete peptide backbone")
            if set(template) != set(residues[chain, position]):
                raise ValueError("terminal template changes the selected residue atom census")
            numbers={"C":6,"N":7,"O":8,"P":15,"S":16,"MG":12}
            if any(elements[n]!=numbers[atom_elements[chain,position,n]] for n in template):
                raise ValueError("terminal template changes a selected heavy element")
            if direction == -1:
                neighbour = {name: xyz[chain, position+1, name] for name in ("N", "CA", "C", "O")}
            else:
                neighbour = {name: xyz[chain, position-1, name] for name in ("N", "CA", "C", "O")}
            n_ca = np.linalg.norm(template["N"]-template["CA"])
            ca_c = np.linalg.norm(template["CA"]-template["C"])
            n_ca_c = angle(template["N"], template["CA"], template["C"])
            c_o = np.linalg.norm(template["C"]-template["O"])
            ca_c_o = angle(template["CA"], template["C"], template["O"])
            best = None
            for first in grid:
                for second in grid:
                    if direction == -1:
                        c = place(neighbour["C"], neighbour["CA"], neighbour["N"],
                                  peptide_length, c_n_ca_angle, first)
                        ca = place(neighbour["CA"], neighbour["N"], c, ca_c, ca_c_n_angle, math.pi)
                        n = place(neighbour["N"], c, ca, n_ca, n_ca_c, second)
                        points = orient(template, dict(N=n, CA=ca, C=c))
                        points["O"] = place(neighbour["N"], ca, c, c_o, ca_c_o, math.pi)
                    else:
                        # The preceding observed carbonyl fixes the initial peptide plane.
                        n = place(neighbour["O"], neighbour["CA"], neighbour["C"],
                                  peptide_length, ca_c_n_angle, math.pi)
                        ca = place(neighbour["CA"], neighbour["C"], n, n_ca, c_n_ca_angle, math.pi)
                        c = place(neighbour["C"], n, ca, ca_c, n_ca_c, first)
                        points = orient(template, dict(N=n, CA=ca, C=c))
                        points["O"] = place(n, ca, c, c_o, ca_c_o, second+math.pi)
                        if "OXT" in points:
                            points["OXT"] = place(n, ca, c, np.linalg.norm(template["OXT"]-template["C"]),
                                angle(template["CA"], template["C"], template["OXT"]), second)
                    for chi in (0, 2*math.pi/3, -2*math.pi/3) if component != "PRO" else (0,):
                        trial = rotate_sidechain(points, chi, component)
                        score, minimum = environment.score(chain, position, trial)
                        key = (score, -minimum, abs(first)+abs(second), first, second, chi)
                        if best is None or key < best[0]:
                            best = key, trial, minimum
            key, chosen, minimum = best
            if minimum < 1.6:
                raise ValueError(f"terminal construction has no feasible selected pose for {chain}:{position}; minimum scored contact {minimum:.6g} angstrom")
            for name, coordinate in chosen.items():
                xyz[chain, position, name] = coordinate
                result[chain, position, name] = coordinate
            environment.add(chain, position, chosen)
            events.append(dict(kind="constructed-Amber-template-terminal",chain=chain, position=position, component=component, template=prefix+component,
                direction="N-terminal" if direction == -1 else "C-terminal", overlap_score=key[0],
                minimum_scored_distance_angstrom=minimum, torsions_radians=key[3:]))
    if set(result) != allowed:
        raise ValueError("terminal construction loses the complete movable atom census")
    initialized = replace_heavy_coordinates(heavy_text, result, permitted)
    return initialized, tuple(events), permitted
