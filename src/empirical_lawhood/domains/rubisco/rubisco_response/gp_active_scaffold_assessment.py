# SPDX-License-Identifier: MPL-2.0
"""Independent complete-atom and rigid-geometry checks for initial Gp models."""

from collections import Counter
from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
from typing import ClassVar

import numpy as np

from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.preparation_integrity import AMINO
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.serialized_heavy_pdb import read_serialized_heavy_pdb
from empirical_lawhood.domains.rubisco.rubisco_insilico_structure.independent_assessment import original_assembly
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_strings, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.gp_active_scaffold import GpActiveScaffold, text_source_identity
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.rubp_preparation import RuBPTetraanionPreparation
from empirical_lawhood.domains.rubisco.rubisco_response.rubp_preparation_assessment import assess_rubp_tetraanion


@dataclass(frozen=True, slots=True)
class GpScaffoldAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/gp-scaffold-assessment"
    assessment_id: str
    scaffold: ObjectIdentity
    atom_count: int
    protein_residue_count: int
    retained_parent_atoms: int
    removed_parent_atoms: int
    constructed_atoms: int
    site_count: int
    maximum_ligand_distance_error_angstrom: Decimal
    minimum_ligand_environment_distance_angstrom: Decimal
    short_contacts: tuple[tuple[str, str, Decimal], ...]
    findings: tuple[str, ...]
    correspondence_disposition: A
    active_ensemble_admission: A = A.UNEVALUABLE
    parameter_admission: A = A.UNEVALUABLE
    new_native_calls: int = 0

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        exact(self.scaffold,ObjectIdentity)
        for count in (self.atom_count,self.protein_residue_count,self.retained_parent_atoms,
                      self.removed_parent_atoms,self.constructed_atoms,self.site_count):
            if type(count) is not int or count < 0:
                raise ValueError("scaffold assessment requires complete integer denominators")
        require_sorted_unique_strings(self.findings,field_name="findings")
        if (self.correspondence_disposition is not (A.FALSIFIED if self.findings else A.SATISFIED)
                or self.active_ensemble_admission is not A.UNEVALUABLE or self.parameter_admission is not A.UNEVALUABLE
                or type(self.new_native_calls) is not int or self.new_native_calls != 0):
            raise ValueError("scaffold correspondence cannot establish physical admission")
        if self.atom_count != self.retained_parent_atoms + self.constructed_atoms:
            raise ValueError("scaffold assessment loses an atom origin")
        for value in (self.maximum_ligand_distance_error_angstrom,self.minimum_ligand_environment_distance_angstrom):
            if type(value) is not Decimal or not value.is_finite() or value < 0:
                raise ValueError("scaffold distance diagnostics need finite nonnegative lengths")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.assessment_id,self)


def _signed_volume(coordinates, centre, neighbours):
    c = np.asarray(coordinates[centre],float)
    return float(np.linalg.det(np.array([np.asarray(coordinates[n],float)-c for n in neighbours])))


def assess_gp_scaffold(scaffold, *, parent_heavy_bytes, ligand, gp_source, methionine, assessment_id):
    """Check exact inherited atoms, complete changes, stereo and rigid distances.

    Short contacts are reported at a disclosed 1-Angstrom diagnostic cutoff.
    Their absence is not a physical-geometry, force-field or ensemble admission.
    """
    exact(scaffold,GpActiveScaffold)
    exact(ligand,RuBPTetraanionPreparation)
    if (len(parent_heavy_bytes) != scaffold.retained_heavy_file.byte_count
            or sha256(parent_heavy_bytes).hexdigest() != scaffold.retained_heavy_file.sha256):
        raise ValueError("scaffold assessor requires the exact original parent geometry")
    if (scaffold.ligand_preparation != ligand.identity
            or set(scaffold.sources) != {text_source_identity(gp_source),text_source_identity(methionine)}):
        raise ValueError("scaffold assessor source identities differ")
    graph_assessment = assess_rubp_tetraanion(ligand,assessment_id="assessment.scaffold.ligand-graph")
    findings = set()
    if graph_assessment.graph_disposition is not A.SATISFIED:
        findings.add("source-ligand-graph")
    raw_parent = read_serialized_heavy_pdb(parent_heavy_bytes.decode("ascii")).atoms
    parent = {row["serial"]:row for row in raw_parent}
    retained = [a for a in scaffold.atoms if a.role=="RETAINED_PARENT"]
    retained_serials = [a.parent_serial for a in retained]
    removed = set(scaffold.removed_parent_serials)
    if (len(set(retained_serials)) != len(retained_serials) or set(retained_serials)&removed
            or set(retained_serials)|removed != set(parent)):
        findings.add("complete-parent-atom-denominator")
    by_chain = {native:next(c for c in scaffold.material.chains if c.chain_id==logical)
                for native,logical in scaffold.chain_map}
    residues = {}
    for atom in scaffold.atoms:
        residues.setdefault((atom.chain,atom.position),[]).append(atom)
    expected_residues = {(native,i) for native,c in by_chain.items() for i in range(1,len(c.sequence)+1)}
    actual_residues = {key for key in residues if key[0] in by_chain}
    if expected_residues != actual_residues:
        findings.add("full-protein-residue-denominator")
    for key in actual_residues:
        components = {a.component for a in residues[key]}
        chain = by_chain[key[0]]
        if (len(components) != 1 or key[1]>len(chain.sequence)
                or AMINO.get(next(iter(components))) != chain.sequence[key[1]-1]):
            findings.add("full-material-sequence")
    expected_changes = {}
    for native,chain in by_chain.items():
        if chain.subunit=="SSU":
            if chain.sequence[0]=="V":
                expected_changes[(native,1)] = ("MET","VAL")
            if chain.sequence[94]=="M":
                expected_changes[(native,95)] = ("ILE","MET")
    if scaffold.changed_residues != tuple((c,p,*change) for (c,p),change in sorted(expected_changes.items())):
        findings.add("complete-declared-sequence-edits")
    permitted_removals = {serial for serial,p in parent.items() if p["component"]=="CAP" or
                         ((p["chain"],p["position"]) in expected_changes and p["atom"] not in {"N","CA","CB","C","O","OXT"})}
    if removed != permitted_removals:
        findings.add("exact-removed-atoms")
    for atom in retained:
        old = parent.get(atom.parent_serial)
        if old is None:
            findings.add("original-parent-serial")
            continue
        changed_component = expected_changes.get((atom.chain,atom.position),(None,old["component"]))[1]
        if ((atom.chain,atom.position,atom.name,atom.element,atom.xyz_angstrom,atom.component)
                != (old["chain"],old["position"],old["atom"],old["element"],old["xyz"],changed_component)):
            findings.add("inherited-atom-coordinate-or-identity")
    expected_added = {}
    for (chain,position),(_,component) in expected_changes.items():
        for name in (("CG1","CG2") if component=="VAL" else ("CG","SD","CE")):
            expected_added[(chain,position,name)] = (component,"SOURCE_VAL_TRANSPLANT" if component=="VAL" else "CONSTRUCTED_MET_TEMPLATE")
    heavy_graph = {a.native_atom_name:a for a in ligand.chemical_graph.atoms if a.atomic_number!=1}
    for placement in scaffold.placements:
        for name in heavy_graph:
            expected_added[("Z",placement.ligand_position,name)] = ("RUB","CONSTRUCTED_RUBP_TEMPLATE")
    actual_added = {a.key:(a.component,a.role) for a in scaffold.atoms if a.role!="RETAINED_PARENT"}
    if actual_added != expected_added:
        findings.add("complete-constructed-atom-denominator")
    if any(a.template_atom != a.name for a in scaffold.atoms if a.role!="RETAINED_PARENT"):
        findings.add("constructed-template-atom-correspondence")
    if any(a.element != ("S" if a.name=="SD" else "C") for a in scaffold.atoms
           if a.role in {"CONSTRUCTED_MET_TEMPLATE","SOURCE_VAL_TRANSPLANT"}):
        findings.add("constructed-side-chain-element")
    # Check the side-chain transform in local coordinates, without calling the
    # producer's frame/transplant helper or solving a second fitted transform.
    observed, source_chains, _, _, _ = original_assembly("1BWV",gp_source.raw_utf8)
    source_native = {c.chain_id:n for c,n in zip(sorted(source_chains,key=lambda c:c.chain_id),"ABCDEFGHIJKLMNOP",strict=True)}
    val_donors = {}
    for a in observed:
        if a.label_seq_id=="1" and a.component_id=="VAL":
            val_donors.setdefault(source_native[a.chain_id],{})[a.atom_id] = np.array(a.xyz_angstrom,float)
    met_donor = {line[12:16].strip():np.array([float(line[i:i+8]) for i in (30,38,46)])
                 for line in methionine.raw_utf8.splitlines() if line.startswith("ATOM  ")}

    def local_coordinates(points,names):
        x = points["CB"]-points["CA"]
        x /= np.linalg.norm(x)
        z = np.cross(x,points["N"]-points["CA"])
        z /= np.linalg.norm(z)
        y = np.cross(z,x)
        return np.array([[(points[name]-points["CB"])@axis for axis in (x,y,z)] for name in names])

    for key,(_,component) in expected_changes.items():
        donor = val_donors.get(key[0],{}) if component=="VAL" else met_donor
        target = {a.name:np.array(a.xyz_angstrom,float) for a in residues.get(key,[])}
        names = ("CG1","CG2") if component=="VAL" else ("CG","SD","CE")
        needed = {"N","CA","CB",*names}
        if not needed<=set(donor) or not needed<=set(target):
            findings.add("complete-side-chain-template")
        else:
            old_local,new_local = local_coordinates(donor,names),local_coordinates(target,names)
            if (not np.isfinite(old_local).all() or not np.isfinite(new_local).all()
                    or np.max(np.abs(old_local-new_local))>1e-9):
                findings.add("side-chain-template-frame")
    if Counter(a.component for a in scaffold.atoms if a.chain=="Z") != {"RUB":144,"MG":8,"HOH":1084}:
        findings.add("all-eight-active-ligands-metals-and-original-water")
    if sum(rows[0].component=="KCX" for rows in residues.values()) != 8:
        findings.add("all-eight-carbamylated-lysines")
    if {p.lsu_chain for p in scaffold.placements} != {n for n,c in by_chain.items() if c.subunit=="LSU"}:
        findings.add("active-site-lsu-correspondence")
    original_ligands = {}
    for a in raw_parent:
        if a["component"]=="CAP":
            original_ligands.setdefault(a["position"],{})[a["atom"]] = a["xyz"]
    if {p.ligand_position for p in scaffold.placements} != set(original_ligands):
        findings.add("original-ligand-site-denominator")
    template = dict(ligand.template_coordinates_angstrom)
    maximum_error, minimum_distance, contacts = 0.0, float("inf"), []
    for placement in scaffold.placements:
        mg = residues.get(("Z",placement.magnesium_position),[])
        catalytic = [a for a in scaffold.atoms if a.component=="KCX"]
        if len(mg)!=1 or mg[0].component!="MG" or not catalytic:
            findings.add("site-magnesium-correspondence")
        elif min(catalytic,key=lambda a:sum((x-y)**2 for x,y in zip(a.xyz_angstrom,mg[0].xyz_angstrom,strict=True))).chain!=placement.lsu_chain:
            findings.add("site-catalytic-residue-correspondence")
        rows = residues.get(("Z",placement.ligand_position),[])
        actual = {a.name:a.xyz_angstrom for a in rows}
        if set(actual) != set(heavy_graph):
            findings.add("complete-site-heavy-graph")
            continue
        for atom in rows:
            if atom.element != {6:"C",8:"O",15:"P"}[heavy_graph[atom.name].atomic_number]:
                findings.add("site-graph-element")
        keys = sorted(heavy_graph)
        source_xyz = np.array([template[k] for k in keys],float)
        placed_xyz = np.array([actual[k] for k in keys],float)
        original = original_ligands.get(placement.ligand_position,{})
        if placement.fit_atom_names != tuple(keys) or not set(keys)<=set(original):
            findings.add("original-placement-fit-anchors")
        else:
            original_xyz = np.array([original[k] for k in keys],float)
            rmsd = float(np.sqrt(np.mean(np.sum((placed_xyz-original_xyz)**2,axis=1))))
            if abs(rmsd-float(placement.fit_rmsd_angstrom))>1e-9:
                findings.add("original-placement-fit-rmsd")
        lengths_source = np.linalg.norm(source_xyz[:,None]-source_xyz[None,:],axis=2)
        lengths_placed = np.linalg.norm(placed_xyz[:,None]-placed_xyz[None,:],axis=2)
        maximum_error = max(maximum_error,float(np.max(np.abs(lengths_source-lengths_placed))))
        if maximum_error>1e-9:
            findings.add("rigid-ligand-internal-distances")
        for centre,neighbours in (("C3",("O3","C2","C4")),("C4",("O4","C3","C5"))):
            if _signed_volume(template,centre,neighbours)*_signed_volume(actual,centre,neighbours)<=0:
                findings.add("ligand-stereochemistry")
        rotation = np.array(placement.rotation,float).reshape(3,3)
        translation = np.array(placement.translation_angstrom,float)
        if (np.max(np.abs(rotation.T@rotation-np.eye(3)))>1e-10 or abs(np.linalg.det(rotation)-1)>1e-10
                or np.max(np.abs(source_xyz@rotation+translation-placed_xyz))>1e-9):
            findings.add("proper-placement-map")
        environment = [a for a in scaffold.atoms if (a.chain,a.position)!=("Z",placement.ligand_position)]
        environment_xyz = np.array([a.xyz_angstrom for a in environment],float)
        for atom in rows:
            distances = np.linalg.norm(environment_xyz-np.array(atom.xyz_angstrom,float),axis=1)
            minimum_distance = min(minimum_distance,float(distances.min()))
            for index in np.flatnonzero(distances<1.0):
                other = environment[index]
                contacts.append((".".join(map(str,atom.key)),".".join(map(str,other.key)),Decimal(str(float(distances[index])))))
    if not np.isfinite(minimum_distance):
        minimum_distance = 0.0
        findings.add("missing-site-distance-diagnostic")
    return GpScaffoldAssessment(assessment_id,scaffold.identity,len(scaffold.atoms),len(actual_residues),len(retained),
        len(removed),len(actual_added),len(scaffold.placements),Decimal(str(maximum_error)),Decimal(str(minimum_distance)),
        tuple(sorted(contacts)),tuple(sorted(findings)),A.FALSIFIED if findings else A.SATISFIED)
