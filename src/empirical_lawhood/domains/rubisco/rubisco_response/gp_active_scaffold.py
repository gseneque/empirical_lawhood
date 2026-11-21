# SPDX-License-Identifier: MPL-2.0
"""Explicit full-assembly heavy-coordinate hypotheses, without native calls.

The retained protein scaffold is reused. Every ligand and changed side chain
is a declared constructed pose. Hydrogen completion, parameters, relaxation
and physical admission remain separate operands.
"""

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
import json
from typing import ClassVar

import numpy as np

from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.contracts import FileEvidence
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.preamber_geometry_integrity import PreAmberGeometryIntegrity
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.serialized_heavy_pdb import read_serialized_heavy_pdb
from empirical_lawhood.domains.rubisco.rubisco_insilico_structure.contracts import StructuralSourceMember
from empirical_lawhood.domains.rubisco.rubisco_insilico_structure.independent_assessment import original_assembly
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_decimal, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.gp_template_geometry import GpTemplateGeometryIntegrity
from empirical_lawhood.domains.rubisco.rubisco_response.materials import RubiscoCaseSet, RubiscoMaterial, exact, identities
from empirical_lawhood.domains.rubisco.rubisco_response.rubp_preparation import RuBPTetraanionPreparation


SCOPE = "FULL_HEAVY_COORDINATE_HYPOTHESES_NOT_HYDROGENATED_PARAMETERIZED_OR_RELAXED"
ROLES = {"RETAINED_PARENT", "CONSTRUCTED_MET_TEMPLATE", "SOURCE_VAL_TRANSPLANT", "CONSTRUCTED_RUBP_TEMPLATE"}
BACKBONE = {"N", "CA", "C", "O", "OXT", "CB"}


def text_source_identity(source):
    exact(source, StructuralSourceMember)
    return ObjectIdentity.from_record("source.scaffold." + source.sha256, source)


@dataclass(frozen=True, slots=True)
class ScaffoldAtom(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/scaffold-atom"
    chain: str
    position: int
    component: str
    name: str
    element: str
    xyz_angstrom: tuple[Decimal, ...]
    role: str
    parent_serial: int | None
    template_atom: str | None

    def __post_init__(self):
        if (type(self.chain) is not str or len(self.chain) != 1
                or type(self.position) is not int or self.position <= 0
                or type(self.component) is not str or not 1 <= len(self.component) <= 3
                or type(self.name) is not str or not 1 <= len(self.name) <= 4
                or self.element not in {"C", "N", "O", "S", "P", "MG"}
                or self.role not in ROLES):
            raise ValueError("scaffold atom loses its complete heavy-atom identity")
        if type(self.xyz_angstrom) is not tuple or len(self.xyz_angstrom) != 3:
            raise ValueError("scaffold atom requires three coordinates in angstrom")
        for value in self.xyz_angstrom:
            validate_decimal(value, field_name="scaffold_xyz_angstrom")
        if self.role == "RETAINED_PARENT":
            if type(self.parent_serial) is not int or self.parent_serial <= 0 or self.template_atom is not None:
                raise ValueError("retained scaffold atom requires its original serial")
        elif self.parent_serial is not None or type(self.template_atom) is not str or not self.template_atom:
            raise ValueError("constructed scaffold atom cannot inherit a parent serial")

    @property
    def key(self):
        return self.chain, self.position, self.name


@dataclass(frozen=True, slots=True)
class LigandPlacement(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/ligand-placement"
    lsu_chain: str
    ligand_position: int
    magnesium_position: int
    fit_atom_names: tuple[str, ...]
    rotation: tuple[Decimal, ...]
    translation_angstrom: tuple[Decimal, ...]
    fit_rmsd_angstrom: Decimal

    def __post_init__(self):
        if (len(self.lsu_chain) != 1 or type(self.ligand_position) is not int or self.ligand_position <= 0
                or type(self.magnesium_position) is not int or self.magnesium_position <= 0
                or self.fit_atom_names != tuple(sorted(set(self.fit_atom_names))) or len(self.fit_atom_names) != 18
                or len(self.rotation) != 9 or len(self.translation_angstrom) != 3):
            raise ValueError("ligand placement loses its complete source/fit census")
        for value in (*self.rotation, *self.translation_angstrom, self.fit_rmsd_angstrom):
            validate_decimal(value, field_name="ligand_placement_operand")
        if self.fit_rmsd_angstrom < 0:
            raise ValueError("ligand placement RMSD cannot be negative")


@dataclass(frozen=True, slots=True)
class GpActiveScaffold(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/gp-active-scaffold"
    scaffold_id: str
    material: RubiscoMaterial
    retained_geometry: ObjectIdentity
    retained_heavy_file: FileEvidence
    ligand_preparation: ObjectIdentity
    sources: tuple[ObjectIdentity, ...]
    chain_map: tuple[tuple[str, str], ...]
    atoms: tuple[ScaffoldAtom, ...]
    placements: tuple[LigandPlacement, ...]
    removed_parent_serials: tuple[int, ...]
    changed_residues: tuple[tuple[str, int, str, str], ...]
    scope: str = SCOPE
    new_native_calls: int = 0
    independent_biological_units: int = 0

    def __post_init__(self):
        validate_stable_id(self.scaffold_id)
        exact(self.material, RubiscoMaterial)
        exact(self.retained_heavy_file, FileEvidence)
        for value in (self.retained_geometry, self.ligand_preparation):
            exact(value, ObjectIdentity)
        identities(self.sources)
        if (self.retained_geometry.object_schema not in (PreAmberGeometryIntegrity.SCHEMA, GpTemplateGeometryIntegrity.SCHEMA)
                or self.ligand_preparation.object_schema != RuBPTetraanionPreparation.SCHEMA
                or len(self.chain_map) != 16 or len(set(self.chain_map)) != 16
                or tuple(row[0] for row in self.chain_map) != tuple("ABCDEFGHIJKLMNOP")
                or set(row[1] for row in self.chain_map) != {c.chain_id for c in self.material.chains}):
            raise ValueError("scaffold loses its original assessment, ligand or full chain correspondence")
        keys = set()
        for atom in self.atoms:
            exact(atom, ScaffoldAtom)
            if atom.key in keys:
                raise ValueError("scaffold repeats a complete atom identity")
            keys.add(atom.key)
        for placement in self.placements:
            exact(placement, LigandPlacement)
        if (len(self.placements) != 8 or len({p.lsu_chain for p in self.placements}) != 8
                or len({p.ligand_position for p in self.placements}) != 8
                or len({p.magnesium_position for p in self.placements}) != 8
                or self.removed_parent_serials != tuple(sorted(set(self.removed_parent_serials)))
                or self.changed_residues != tuple(sorted(set(self.changed_residues)))
                or self.scope != SCOPE or type(self.new_native_calls) is not int or self.new_native_calls != 0
                or type(self.independent_biological_units) is not int or self.independent_biological_units != 0):
            raise ValueError("heavy geometry cannot conceal site denominators or establish physical admission")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.scaffold_id, self)


def _decimal_vector(vector):
    return tuple(Decimal(str(float(value))) for value in vector)


def proper_rigid_fit(template, target):
    """Least-squares proper rotation; reject degenerate anchor geometries."""
    left, right = np.asarray(template, dtype=float), np.asarray(target, dtype=float)
    if (left.shape != right.shape or left.ndim != 2 or left.shape[1] != 3 or len(left) < 3
            or not np.isfinite(left).all() or not np.isfinite(right).all()):
        raise ValueError("rigid fit requires matched finite Cartesian anchors")
    x, y = left - left.mean(axis=0), right - right.mean(axis=0)
    if np.linalg.matrix_rank(x, tol=1e-10) < 2 or np.linalg.matrix_rank(y, tol=1e-10) < 2:
        raise ValueError("rigid fit refuses collinear or coincident anchors")
    u, _, vt = np.linalg.svd(x.T @ y)
    correction = np.eye(3)
    correction[-1, -1] = np.linalg.det(u @ vt)
    rotation = u @ correction @ vt
    translation = right.mean(axis=0) - left.mean(axis=0) @ rotation
    rmsd = np.sqrt(np.mean(np.sum((left @ rotation + translation - right)**2, axis=1)))
    return rotation, translation, float(rmsd)


def sidechain_transplant(template, target, names):
    """Proper backbone frame with an exact CB anchor; no native minimization."""
    def frame(points):
        ca, cb, nitrogen = (np.asarray(points[name], dtype=float) for name in ("CA", "CB", "N"))
        if any(value.shape != (3,) or not np.isfinite(value).all() for value in (ca,cb,nitrogen)):
            raise ValueError("side-chain frame requires finite Cartesian coordinates")
        axis = cb - ca
        if np.linalg.norm(axis) < 1e-10:
            raise ValueError("side-chain frame has coincident CA/CB")
        axis /= np.linalg.norm(axis)
        plane = nitrogen - ca
        plane -= np.dot(plane, axis) * axis
        if np.linalg.norm(plane) < 1e-10:
            raise ValueError("side-chain frame has collinear N/CA/CB")
        plane /= np.linalg.norm(plane)
        return np.array((axis, plane, np.cross(axis, plane))), cb

    source_axes, source_cb = frame(template)
    target_axes, target_cb = frame(target)
    if any(np.asarray(template[name]).shape!=(3,) or not np.isfinite(np.asarray(template[name],float)).all() for name in names):
        raise ValueError("side-chain template requires finite Cartesian coordinates")
    rotation = source_axes.T @ target_axes
    return {name: _decimal_vector((np.asarray(template[name], dtype=float)-source_cb) @ rotation + target_cb)
            for name in names}


def read_methionine_template(source):
    exact(source, StructuralSourceMember)
    result = {}
    for line in source.raw_utf8.splitlines():
        if line.startswith("ATOM  "):
            name = line[12:16].strip()
            if line[17:20] != "MET" or name in result:
                raise ValueError("methionine template has a duplicate or different residue")
            if line[76:78].strip() and line[76:78].strip() != ("S" if name=="SD" else "N" if name=="N" else "O" if name=="O" else "C"):
                raise ValueError("methionine template has a different heavy element")
            result[name] = tuple(Decimal(line[i:i+8]) for i in (30, 38, 46))
            if any(not value.is_finite() for value in result[name]):
                raise ValueError("methionine template has nonfinite coordinates")
    if set(result) != {"N", "CA", "CB", "CG", "SD", "CE", "C", "O"}:
        raise ValueError("methionine template omits a complete heavy atom")
    return result


def prepare_gp_active_scaffolds(*, cases, retained_integrity, heavy_bytes, origin_bytes,
                                gp_source, ligand, methionine, preparation_id):
    """Construct all four declared initial heavy geometries from exact sources."""
    exact(cases, RubiscoCaseSet)
    if type(retained_integrity) not in (PreAmberGeometryIntegrity, GpTemplateGeometryIntegrity):
        raise TypeError("active scaffold requires an exact independently assessed starting parent")
    retained_integrity.__post_init__()
    if (type(retained_integrity) is GpTemplateGeometryIntegrity
            and retained_integrity.structural_disposition.value != "SATISFIED"):
        raise ValueError("active scaffold cannot use a structurally invalid template parent")
    exact(gp_source, StructuralSourceMember)
    exact(ligand, RuBPTetraanionPreparation)
    validate_stable_id(preparation_id)
    for raw, evidence in ((heavy_bytes, retained_integrity.heavy_file), (origin_bytes, retained_integrity.origin_file)):
        if type(raw) is not bytes or len(raw) != evidence.byte_count or sha256(raw).hexdigest() != evidence.sha256:
            raise ValueError("active scaffold substitutes the independently assessed parent bytes")
    selected = tuple(c for c in cases.cases if c.case_role == "CANDIDATE")
    if (tuple(c.case_id for c in selected) != ("case.gp-i95m.m1", "case.gp-i95m.v1")
            or retained_integrity.construct.construct_id != "gp.wt.m1"):
        raise ValueError("active scaffold requires both actual Gp processing cases and the M1-WT parent")
    origin = json.loads(origin_bytes)
    native_chains = origin["complete_chains"]
    source_atoms, source_chains, _, _, _ = original_assembly("1BWV", gp_source.raw_utf8)
    source_chains = sorted(source_chains, key=lambda c:c.chain_id)
    chain_map, counters = [], {"lsu":0, "ssu":0}
    source_to_native = {}
    for original, declared, native in zip(source_chains, native_chains, "ABCDEFGHIJKLMNOP", strict=True):
        kind = "lsu" if len(original.full_sequence) == 493 else "ssu"
        counters[kind] += 1
        logical = f"{kind}.{counters[kind]:02}"
        if declared["chain"] != native or declared["source_chain"] != original.chain_id:
            raise ValueError("retained native chain mapping differs from deposited Gp assembly")
        chain_map.append((native, logical))
        source_to_native[original.chain_id] = native
    if counters != {"lsu":8,"ssu":8}:
        raise ValueError("active scaffold loses a full Gp subunit")
    source_val = {native:{} for native, logical in chain_map if logical.startswith("ssu.")}
    for atom in source_atoms:
        native = source_to_native.get(atom.chain_id)
        if native in source_val and atom.label_seq_id == "1":
            if atom.component_id != "VAL" or atom.alternate_id not in (".", "?") or atom.occupancy != 1:
                raise ValueError("V1 source requires one complete unambiguous Val pose")
            source_val[native][atom.atom_id] = atom.xyz_angstrom
    if any(set(atoms) != {"N","CA","CB","CG1","CG2","C","O"} for atoms in source_val.values()):
        raise ValueError("V1 source omits an observed complete Val side chain")
    template = read_methionine_template(methionine)
    parent = read_serialized_heavy_pdb(heavy_bytes.decode("ascii")).atoms
    parent_groups = {}
    for atom in parent:
        parent_groups.setdefault((atom["chain"],atom["position"]), []).append(atom)
    carbon = {key:rows for key,rows in parent_groups.items() if rows[0]["component"] == "CAP"}
    magnesium = {key:rows[0] for key,rows in parent_groups.items() if rows[0]["component"] == "MG"}
    kcx = {key:rows for key,rows in parent_groups.items() if rows[0]["component"] == "KCX"}
    if len(carbon) != 8 or len(magnesium) != 8 or len(kcx) != 8:
        raise ValueError("retained scaffold omits an inhibitor, magnesium or carbamylated lysine")
    heavy_names = tuple(a.native_atom_name for a in ligand.chemical_graph.atoms if a.atomic_number != 1)
    ligand_xyz = dict(ligand.template_coordinates_angstrom)
    element = {a.native_atom_name:{6:"C",8:"O",15:"P"}[a.atomic_number]
               for a in ligand.chemical_graph.atoms if a.atomic_number != 1}
    ligand_atoms, placements, removed_ligands = [], [], []
    for key, rows in sorted(carbon.items()):
        by_name = {r["atom"]:r for r in rows}
        if set(by_name) != set(heavy_names) | {"C","O6","O7"}:
            raise ValueError("CABP-to-RuBP preparation loses the original inhibitor atom denominator")
        rotation, translation, rmsd = proper_rigid_fit(
            [ligand_xyz[n] for n in heavy_names], [by_name[n]["xyz"] for n in heavy_names])
        mg_key = min(magnesium, key=lambda m:min(np.linalg.norm(np.array(magnesium[m]["xyz"],float)-np.array(r["xyz"],float)) for r in rows))
        lsu_key = min(kcx, key=lambda c:min(np.linalg.norm(np.array(magnesium[mg_key]["xyz"],float)-np.array(r["xyz"],float)) for r in kcx[c]))
        placements.append(LigandPlacement(lsu_key[0],key[1],mg_key[1],heavy_names,
            _decimal_vector(rotation.ravel()),_decimal_vector(translation),Decimal(str(rmsd))))
        for name in heavy_names:
            xyz = _decimal_vector(np.array(ligand_xyz[name],float) @ rotation + translation)
            ligand_atoms.append(ScaffoldAtom(*key,"RUB",name,element[name],xyz,"CONSTRUCTED_RUBP_TEMPLATE",None,name))
        removed_ligands.extend(r["serial"] for r in rows)
    outputs = []
    for case in selected:
        for arm, material in (("wt",case.parent),("i95m",case.mutant)):
            processing = "m1" if case.case_id.endswith(".m1") else "v1"
            expected = {c.chain_id:c.sequence for c in material.chains}
            for native, logical in chain_map:
                parent_sequence = next(c["sequence"] for c in native_chains if c["chain"]==native)
                target = expected[logical]
                edits = [(i,a,b) for i,(a,b) in enumerate(zip(parent_sequence,target,strict=True),1) if a!=b]
                intended = ([(1,"M","V")] if processing=="v1" and logical.startswith("ssu.") else [])
                if arm=="i95m" and logical.startswith("ssu."):
                    intended += [(95,"I","M")]
                if edits != intended:
                    raise ValueError("scaffold material changes an unnamed sequence position")
            atoms, removed, changes = list(ligand_atoms), list(removed_ligands), []
            for key, rows in parent_groups.items():
                if key in carbon:
                    continue
                native, position = key
                logical = dict(chain_map).get(native, "")
                mutation = ("VAL" if processing=="v1" and position==1 else
                            "MET" if arm=="i95m" and position==95 else None) if logical.startswith("ssu.") else None
                if mutation is not None:
                    old = "MET" if position==1 else "ILE"
                    if any(r["component"] != old for r in rows):
                        raise ValueError("native mutation does not start from its named residue")
                    changes.append((native,position,old,mutation))
                    donor = source_val[native] if mutation=="VAL" else template
                    names = ("CG1","CG2") if mutation=="VAL" else ("CG","SD","CE")
                    target = {r["atom"]:r["xyz"] for r in rows}
                    added = sidechain_transplant(donor,target,names)
                    for name in names:
                        atoms.append(ScaffoldAtom(native,position,mutation,name,"S" if name=="SD" else "C",added[name],
                            "SOURCE_VAL_TRANSPLANT" if mutation=="VAL" else "CONSTRUCTED_MET_TEMPLATE",None,name))
                for row in rows:
                    if mutation is not None and row["atom"] not in BACKBONE:
                        removed.append(row["serial"])
                        continue
                    atoms.append(ScaffoldAtom(native,position,mutation or row["component"],row["atom"],row["element"],row["xyz"],
                                              "RETAINED_PARENT",row["serial"],None))
            sources = tuple(sorted((text_source_identity(gp_source), text_source_identity(methionine)),key=lambda s:s.object_id))
            outputs.append(GpActiveScaffold(f"{preparation_id}.{processing}.{arm}",material,
                ObjectIdentity.from_record(retained_integrity.product_id,retained_integrity),retained_integrity.heavy_file,
                ligand.identity,sources,tuple(chain_map),tuple(sorted(atoms,key=lambda a:a.key)),
                tuple(sorted(placements,key=lambda p:p.lsu_chain)),tuple(sorted(removed)),tuple(sorted(changes))))
    return tuple(outputs)


def scaffold_pdb(scaffold, ligand):
    """Serialize a heavy-coordinate hypothesis for later native preparation."""
    exact(scaffold,GpActiveScaffold)
    exact(ligand,RuBPTetraanionPreparation)
    if scaffold.ligand_preparation != ligand.identity:
        raise ValueError("scaffold PDB graph differs from its selected ligand")
    lines = ["REMARK   MODELED ACTIVE HEAVY SCAFFOLD; NOT RELAXED OR PARAMETERIZED"]
    serials, previous, serial = {}, None, 0
    for atom in scaffold.atoms:
        if previous is not None and atom.chain != previous.chain:
            serial += 1
            lines.append(f"TER   {serial:5d}      {previous.component:3s} {previous.chain}{previous.position:4d}")
        serial += 1
        serials[atom.key] = serial
        if max(abs(float(x)) for x in atom.xyz_angstrom) >= 1000 or serial >= 100000:
            raise ValueError("scaffold exceeds the selected PDB coordinate or serial representation")
        label = atom.name.rjust(4) if len(atom.element)==2 else (" " + atom.name).ljust(4)
        xyz = "".join(f"{float(x):8.3f}" for x in atom.xyz_angstrom)
        lines.append(f"HETATM{serial:5d} {label} {atom.component:3s} {atom.chain}{atom.position:4d}    {xyz}  1.00  0.00          {atom.element:>2s}  ")
        previous = atom
    for placement in scaffold.placements:
        for bond in ligand.chemical_graph.bonds:
            left, right = (ligand.chemical_graph.atoms[i] for i in (bond.first,bond.second))
            if left.atomic_number==1 or right.atomic_number==1:
                continue
            a,b = (serials[("Z",placement.ligand_position,x.native_atom_name)] for x in (left,right))
            for first,second in ((a,b),(b,a)):
                lines.append("CONECT"+f"{first:5d}"+f"{second:5d}"*int(bond.order))
    lines.append("END")
    return "\n".join(lines)+"\n"
