# SPDX-License-Identifier: MPL-2.0
"""Read retained repair outputs without invoking Amber, OpenMM or an optimizer."""

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
from io import BytesIO
import json
import math
from typing import ClassVar

import numpy as np

from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.amber_parameters import assigned_census_supported_inactive14, read_prmtop
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.serialized_heavy_pdb import read_serialized_heavy_pdb
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_strings, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.gp_constructed_geometry import origin_mobility
from empirical_lawhood.domains.rubisco.rubisco_response.gp_geometry_repair import (
    REPAIR_INPUT_TYPES, GpAmberFragmentRepairInput, GpCarboxylateRepairInput, inherited_carboxylate_keys,
)
from empirical_lawhood.domains.rubisco.rubisco_response.gp_heavy_geometry import inspect_heavy_geometry
from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology import heavy_pdb_rows
from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology_assessment import _residues, read_initial_coordinates, solvent_last_residues
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.gp_terminal_geometry import (
    TERMINAL_GEOMETRY_FILE, initial_terminal_geometry, require_initial_terminal_geometry, terminal_geometry_bytes,
)


ASSESSMENT_FILES = tuple(sorted(("amber-heavy.pdb", "amber.stdout", "amber.stderr", "atom-origin-provenance.json",
    "atom-selection.json", "complete-heavy.pdb", "dry.inpcrd", "dry.prmtop", "final-coordinates-nm.npy",
    "final-forces-kj-mol-nm.npy", "force-assignment.json", "initial-coordinates-nm.npy", "initialization.json",
    "initialized-heavy.pdb", "optimizer-return.json", "parent-heavy.pdb")))
CARBOXYLATE_ASSESSMENT_FILES = tuple(sorted((*ASSESSMENT_FILES, TERMINAL_GEOMETRY_FILE)))
AMBER_FRAGMENT_ASSESSMENT_FILES = tuple(sorted((*CARBOXYLATE_ASSESSMENT_FILES, "terminal-fragments.json")))


def repair_assessment_files(source_identity):
    if source_identity.object_version == GpAmberFragmentRepairInput.VERSION:
        return AMBER_FRAGMENT_ASSESSMENT_FILES
    if source_identity.object_version == GpCarboxylateRepairInput.VERSION:
        return CARBOXYLATE_ASSESSMENT_FILES
    return ASSESSMENT_FILES


@dataclass(frozen=True, slots=True)
class GpGeometryRepairAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/gp-geometry-repair-assessment"
    VERSION: ClassVar[str] = "2.0.0"
    assessment_id: str
    source: ObjectIdentity
    file_sha256s: tuple[tuple[str, str], ...]
    heavy_atoms: int
    fixed_heavy_atoms: int
    constructed_heavy_atoms: int
    movable_atoms: int
    maximum_mobile_gradient_kj_mol_nm: Decimal
    maximum_mobile_bond_error_angstrom: Decimal
    minimum_mobile_nonbonded_heavy_distance_angstrom: Decimal
    short_heavy_contacts: int
    gross_backbone_anomalies: int
    stereo_anomalies: int
    peptide_anomalies: int
    findings: tuple[str, ...]
    repair_disposition: A
    ensemble_admission: A = A.UNEVALUABLE
    rate_admission: A = A.UNEVALUABLE

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        exact(self.source,ObjectIdentity)
        require_sorted_unique_strings(self.findings,field_name="findings")
        if (tuple(name for name,_ in self.file_sha256s)!=repair_assessment_files(self.source)
                or self.heavy_atoms!=self.fixed_heavy_atoms+self.constructed_heavy_atoms+self.refined_heavy_count
                or self.movable_atoms<self.constructed_heavy_atoms+self.refined_heavy_count
                or any(type(n) is not int or n<0 for n in (self.heavy_atoms,self.fixed_heavy_atoms,
                    self.constructed_heavy_atoms,self.movable_atoms,self.short_heavy_contacts,
                    self.gross_backbone_anomalies,self.stereo_anomalies,self.peptide_anomalies))
                or any(type(v) is not Decimal or not v.is_finite() or v<0 for v in (
                    self.maximum_mobile_gradient_kj_mol_nm,self.maximum_mobile_bond_error_angstrom,
                    self.minimum_mobile_nonbonded_heavy_distance_angstrom))
                or self.repair_disposition is not (A.FALSIFIED if self.findings else A.SATISFIED)
                or self.ensemble_admission is not A.UNEVALUABLE or self.rate_admission is not A.UNEVALUABLE):
            raise ValueError("geometry repair assessment changes its complete scope or promotes physical evidence")

    @property
    def identity(self):return ObjectIdentity.from_record(self.assessment_id,self)

    @property
    def refined_heavy_count(self):
        return 0


@dataclass(frozen=True, slots=True)
class GpRepairPlanarityAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/gp-repair-planarity-assessment"
    improper_terms: int
    positive_amplitude_terms: int
    negative_amplitude_terms: int
    zero_amplitude_terms: int
    applicable_terms: int
    checked_terms: int
    exempt_terms: int
    undefined_terms: int
    violating_terms: int
    maximum_residual_angstrom: Decimal

    def __post_init__(self):
        counts = (self.improper_terms, self.positive_amplitude_terms, self.negative_amplitude_terms,
                  self.zero_amplitude_terms, self.applicable_terms, self.checked_terms, self.exempt_terms,
                  self.undefined_terms, self.violating_terms)
        if (any(type(n) is not int or n < 0 for n in counts)
                or self.improper_terms != sum(counts[1:4])
                or self.applicable_terms > self.positive_amplitude_terms + self.negative_amplitude_terms
                or self.applicable_terms != self.checked_terms+self.exempt_terms+self.undefined_terms
                or self.violating_terms > self.checked_terms
                or type(self.maximum_residual_angstrom) is not Decimal
                or not self.maximum_residual_angstrom.is_finite() or self.maximum_residual_angstrom < 0
                or (self.checked_terms == 0 and self.maximum_residual_angstrom != 0)
                or (self.violating_terms > 0) != (self.maximum_residual_angstrom > Decimal("0.10"))):
            raise ValueError("repair planarity assessment changes its original term coverage or geometric threshold")

    @classmethod
    def from_quality(cls, quality):
        c = quality["counts"]
        return cls(c["impropers"], c["positive_amplitude_impropers"], c["negative_amplitude_impropers"],
                   c["zero_amplitude_impropers"], c["applicable_planar_impropers"], c["planar_impropers_checked"],
                   c["exempt_planar_impropers"], c["undefined_planar_impropers"], c["violating_planar_impropers"],
                   Decimal(str(quality["metrics"]["maximum_planar_improper_distance_angstrom"])))


@dataclass(frozen=True, slots=True, kw_only=True)
class GpCarboxylateRepairAssessment(GpGeometryRepairAssessment):
    VERSION: ClassVar[str] = "3.0.0"
    SOURCE_VERSION: ClassVar[str] = GpCarboxylateRepairInput.VERSION
    refined_inherited_heavy_atoms: int
    largest_refined_displacement_angstrom: Decimal
    refined_displacements_angstrom: tuple[tuple[str, int, str, tuple[Decimal, Decimal, Decimal]], ...]
    fixed_bonds_checked: int
    planarity: GpRepairPlanarityAssessment

    def __post_init__(self):
        GpGeometryRepairAssessment.__post_init__(self)
        exact(self.planarity, GpRepairPlanarityAssessment)
        keys = tuple((chain, 213, atom) for chain in "ACEGIKMO" for atom in ("CD", "OE1", "OE2"))
        rows = self.refined_displacements_angstrom
        if ((self.source.object_schema, self.source.object_version) != (GpCarboxylateRepairInput.SCHEMA, self.SOURCE_VERSION)
                or type(self.refined_inherited_heavy_atoms) is not int or self.refined_inherited_heavy_atoms != 24
                or type(self.fixed_bonds_checked) is not int or self.fixed_bonds_checked < 1
                or type(rows) is not tuple or any(type(row) is not tuple or len(row) != 4 for row in rows)
                or tuple(row[:3] for row in rows) != keys or any(type(row[3]) is not tuple or len(row[3]) != 3
                    or any(type(x) is not Decimal or not x.is_finite() for x in row[3]) for row in rows)
                or type(self.largest_refined_displacement_angstrom) is not Decimal
                or not self.largest_refined_displacement_angstrom.is_finite()
                or self.largest_refined_displacement_angstrom != _maximum_displacement(rows)
                or (self.repair_disposition is A.SATISFIED
                    and (self.planarity.checked_terms == 0 or self.planarity.violating_terms or self.planarity.undefined_terms))):
            raise ValueError("refined assessment lacks the 24 original carboxylate atoms or their physical displacement")

    @property
    def refined_heavy_count(self):
        return self.refined_inherited_heavy_atoms


@dataclass(frozen=True, slots=True, kw_only=True)
class GpAmberFragmentRepairAssessment(GpCarboxylateRepairAssessment):
    VERSION: ClassVar[str] = "4.0.0"
    SOURCE_VERSION: ClassVar[str] = GpAmberFragmentRepairInput.VERSION


def _array(raw,count):
    value=np.load(BytesIO(raw),allow_pickle=False)
    if value.dtype!=np.dtype("float64") or value.shape!=(count,3) or not np.isfinite(value).all():
        raise ValueError("retained repair array is not a complete finite double coordinate/force census")
    return value


def _maximum_displacement(rows):
    return Decimal(str(max(float(np.linalg.norm(np.array(delta, dtype=float))) for _, _, _, delta in rows)))


def _refined_displacement_assessment(refined, joined, first, final, reported, limit):
    """Reconstruct all 24 signed displacement vectors at full native precision."""
    displacements = [[list(key), ((final[joined[key]] - first[joined[key]])*10).tolist()] for key in refined]
    if reported != displacements:
        raise ValueError("retained repair substitutes its source-relative inherited coordinate displacements")
    rows = tuple((*key, tuple(Decimal(str(x)) for x in delta)) for key, delta in displacements)
    maximum = _maximum_displacement(rows)
    return maximum, ("refined-inherited-heavy-atom-displacement",) if maximum > limit else (), rows


def _omega_degrees(values):
    # Independent atan2 of the two plane normals; cis=0, trans=180.
    a,b,c,d=(np.asarray(v,float) for v in values)
    axis=c-b;length=np.linalg.norm(axis)
    if length<1e-10:return 0.0
    left,right=np.cross(b-a,axis),np.cross(axis,d-c)
    if min(np.linalg.norm(left),np.linalg.norm(right))<1e-10:return 0.0
    return math.degrees(math.atan2(np.dot(np.cross(left,right),axis/length),np.dot(left,right)))


def library_minimizer_findings(optimizer, coordinates, maximum_gradient, *, platform="CPU", threads=1):
    """Check the independent declared-library endpoint contract, not success alone."""
    method = optimizer.get("numerical_method")
    if method != "OPENMM_LOCAL_ENERGY_MINIMIZER_COMPLETE_AMBER_V1":
        raise ValueError("new geometry repair requires the complete Amber/OpenMM minimizer")
    if (optimizer.get("all_original_force_groups") is not True
            or optimizer.get("projected_pair_kernel") is not False
            or optimizer.get("platform") != platform
            or type(optimizer.get("threads")) is not int
            or optimizer.get("threads") != threads
            or optimizer.get("platform_properties") != ({"Threads": str(threads), "DeterministicForces": "true"} if platform == "CPU" else {})
            or optimizer.get("iteration_limit_is_convergence") is not False):
        raise ValueError("geometry repair changes its complete original force or stopping contract")
    tolerance = optimizer.get("requested_openmm_rms_tolerance_kj_mol_nm")
    required = float(maximum_gradient)/math.sqrt(3*len(coordinates))
    if type(tolerance) not in (int, float) or not math.isfinite(tolerance) or not 0 < tolerance <= required*(1+1e-14):
        raise ValueError("OpenMM RMS tolerance does not imply the selected maximum-component bound")
    return ()

def read_initial_terminal_geometry(files, origin):
    terminal = initial_terminal_geometry(files["initialized-heavy.pdb"].decode("ascii"), origin,
        origin_sha256=sha256(files["atom-origin-provenance.json"]).hexdigest())
    if files[TERMINAL_GEOMETRY_FILE] != terminal_geometry_bytes(terminal):
        raise ValueError("repair changes the independently read initial terminal geometry")
    return terminal


def read_amber_fragment_initialization(source, files, initialization):
    """Recompute the accepted placement from its original bound library operands."""
    from .terminal_fragment_placement import METHOD, replay_terminal_fragments
    initialized, transformations, constructed = replay_terminal_fragments(source, files["terminal-fragments.json"])
    if (initialization.get("method") != METHOD or initialized.encode("ascii") != files["initialized-heavy.pdb"]
            or initialization.get("constructed_atoms") != [list(k) for k in constructed]
            or json.dumps(initialization.get("transformations"), sort_keys=True) != json.dumps(transformations, sort_keys=True)):
        raise ValueError("repair changes the source-bound Amber fragment reconstruction")


def assess_geometry_repair(source,files,*,assessment_id):
    if type(source) not in REPAIR_INPUT_TYPES:
        raise TypeError("geometry repair requires its exact selected source revision")
    source_identity = source.identity
    assessment_files = repair_assessment_files(source_identity)
    if set(files)!=set(assessment_files) or any(type(raw) is not bytes for raw in files.values()):
        raise ValueError("repair assessment requires every original selected raw operand")
    if files["parent-heavy.pdb"]!=source.heavy_pdb.encode() or files["atom-origin-provenance.json"]!=source.origin_json.encode():
        raise ValueError("repair assessment changes the original parent or origins")
    origin = json.loads(source.origin_json)
    if isinstance(source, GpCarboxylateRepairInput):
        require_initial_terminal_geometry(read_initial_terminal_geometry(files, origin))
    original,movable_heavy=origin_mobility(source.heavy_pdb,origin)
    constructed = set(movable_heavy)
    refined = inherited_carboxylate_keys(origin) if isinstance(source, GpCarboxylateRepairInput) else ()
    permitted = constructed.union(refined)
    repaired=files["complete-heavy.pdb"].decode("ascii")
    actual=read_serialized_heavy_pdb(repaired).atoms
    before_lines=source.heavy_pdb.splitlines(keepends=True)
    after_lines=repaired.splitlines(keepends=True)
    initialized_lines=files["initialized-heavy.pdb"].decode("ascii").splitlines(keepends=True)
    if len(before_lines)!=len(after_lines) or len(before_lines)!=len(initialized_lines) or len(actual)!=len(original):
        raise ValueError("repair assessment loses the complete serialized heavy structure")
    for before,after,initialized in zip(before_lines,after_lines,initialized_lines,strict=True):
        key=(before[21],int(before[22:26]),before[12:16].strip()) if before.startswith(("ATOM  ","HETATM")) else None
        if (before!=after and (key not in permitted or before[:30]!=after[:30] or before[54:]!=after[54:])):
            raise ValueError("repair changes observed coordinates or original noncoordinate bytes")
        if before!=initialized and (key not in constructed or before[:30]!=initialized[:30] or before[54:]!=initialized[54:]):
            raise ValueError("repair initialization changes observed coordinates or original noncoordinate bytes")
    sections=read_prmtop(files["dry.prmtop"].decode("ascii"))
    census=assigned_census_supported_inactive14(sections)
    n=census["term_census"]["atoms"]
    raw_initial,_=read_initial_coordinates(files["dry.inpcrd"].decode("ascii"),n,periodic=False)
    first,final,forces=(_array(files[name],n) for name in (
        "initial-coordinates-nm.npy","final-coordinates-nm.npy","final-forces-kj-mol-nm.npy"))
    if not np.array_equal(first,np.array(raw_initial,float)/10):
        raise ValueError("repair changes its actual native initial coordinates")
    original_residues={}
    for atom in read_serialized_heavy_pdb(files["initialized-heavy.pdb"].decode("ascii")).atoms:
        original_residues.setdefault((atom["chain"],atom["position"],atom["component"]),{})[atom["atom"]]=atom
    original_residues=solvent_last_residues(original_residues)
    if len(original_residues)!=len(_residues(census)):
        raise ValueError("repair changes its independent residue count")
    joined={};elements={"C":6,"N":7,"O":8,"P":15,"S":16,"MG":12}
    for ((chain,pos,component),atoms),(residue,indices) in zip(original_residues.items(),_residues(census),strict=True):
        if residue.upper()!={"HIS":"HIE","HID":"HIE","HOH":"WAT"}.get(component,component).upper():
            raise ValueError("repair changes the independent full sequence")
        heavy={name:i for name,i in indices.items() if census["atomic_numbers"][i]!=1}
        if set(heavy)!=set(atoms):raise ValueError("repair changes an independent complete heavy residue")
        for name,i in heavy.items():
            atom=atoms[name]
            if census["atomic_numbers"][i]!=elements[atom["element"]] or max(abs(a-b) for a,b in zip(atom["xyz"],raw_initial[i],strict=True))>Decimal("0.000001"):
                raise ValueError("repair changes an independently joined heavy element or initial coordinate")
            joined[(chain,pos,name)]=i
    if len(joined)!=len(original):raise ValueError("repair loses independent heavy atom denominator")
    bonds={};neighbours={i:set() for i in range(n)}
    for name,rows in census["indexed_bonded_terms"].items():
        if name.startswith("BONDS"):
            for a,b,parameter in rows:
                a,b=abs(a)//3,abs(b)//3
                pair=tuple(sorted((a,b)))
                equilibrium=sections["BOND_EQUIL_VALUE"][parameter-1]
                if pair in bonds and bonds[pair]!=equilibrium:raise ValueError("repair duplicates a bond with different coefficients")
                bonds[pair]=equilibrium;neighbours[a].add(b);neighbours[b].add(a)
    mobile={joined[k] for k in permitted}
    water_by_atom={}
    for residue,atoms in _residues(census):
        if residue=="WAT" and set(atoms)=={"O","H1","H2"}:
            if [census["atomic_numbers"][atoms[k]] for k in ("O","H1","H2")]==[8,1,1]:
                for index in atoms.values():water_by_atom[index]=atoms
    for i,z in enumerate(census["atomic_numbers"]):
        if z==1:
            heavy_parents=[j for j in neighbours[i] if census["atomic_numbers"][j]>1]
            if len(heavy_parents)!=1:raise ValueError("repair has a hydrogen without a unique independent heavy bond")
            if len(neighbours[i])!=1:
                water=water_by_atom.get(i,{})
                if (not water or neighbours[i]!=set(water.values())-{i}
                        or neighbours[water["O"]]!={water["H1"],water["H2"]}):
                    raise ValueError("repair has an undeclared hydrogen-hydrogen edge")
            mobile.add(i)
    selection=json.loads(files["atom-selection.json"])
    if selection["movable"]!=sorted(mobile) or {tuple(key):i for key,i in selection["heavy_join"]}!=joined:
        raise ValueError("repair substituted its independent movable atom selection")
    fixed=sorted(set(range(n))-mobile)
    if not np.array_equal(first[fixed],final[fixed]):raise ValueError("repair changed fixed native coordinates")
    output={ (a["chain"],a["position"],a["atom"]):a for a in actual}
    for key,i in joined.items():
        if key not in output or max(abs(float(x)-y*10) for x,y in zip(output[key]["xyz"],final[i],strict=True))>0.000501:
            raise ValueError("published repaired coordinates differ from the retained native endpoint")
    gradient=float(np.max(np.abs(forces[sorted(mobile)])))
    optimizer=json.loads(files["optimizer-return.json"])
    findings=set()
    if not optimizer["success"]:findings.add("optimizer-did-not-converge")
    if gradient>float(source.maximum_gradient_kj_mol_nm):findings.add("mobile-force-tolerance")
    if abs(optimizer["maximum_mobile_gradient_kj_mol_nm"]-gradient)>1e-10:
        raise ValueError("optimizer summary substitutes the independently read final mobile forces")
    mobile_bonds=[(a,b,float(eq)) for (a,b),eq in bonds.items() if {a,b}&mobile]
    bond_error=max(abs(np.linalg.norm(final[a]-final[b])*10-eq) for a,b,eq in mobile_bonds)
    if bond_error>float(source.maximum_mobile_bond_error_angstrom):findings.add("mobile-bond-equilibrium-error")
    geometry=inspect_heavy_geometry(heavy_pdb_rows(repaired))
    contacts=len(geometry["short_contacts_squared_angstrom"])
    stretches=len(geometry["backbone_anomalies_squared_angstrom"])
    stereo=len(geometry["stereochemistry_anomalies_angstrom3"])
    if contacts:findings.add("sub-Angstrom-heavy-contact")
    if stretches:findings.add("gross-backbone-bond")
    if stereo:findings.add("inverted-or-planar-stereocentre")
    # Complete mobile-heavy / all-heavy comparison, without a producer cell grid.
    indices=np.array(sorted(joined.values()),dtype=int)
    minimum=math.inf
    for key in permitted:
        i=joined[key]; distances=np.linalg.norm(final[indices]-final[i],axis=1)*10
        allowed=~np.isin(indices,tuple(neighbours[i]|{i}))
        if allowed.any():minimum=min(minimum,float(np.min(distances[allowed])))
    if minimum<float(source.minimum_mobile_nonbonded_heavy_distance_angstrom):findings.add("mobile-nonbonded-heavy-contact")
    peptides=0
    for key in output:
        chain,pos,name=key
        if chain=="Z" or name!="C":continue
        keys=((chain,pos,"CA"),key,(chain,pos+1,"N"),(chain,pos+1,"CA"))
        if all(k in output for k in keys) and set(keys)&permitted and output[keys[2]]["component"]!="PRO":
            if abs(_omega_degrees([output[k]["xyz"] for k in keys]))<150:peptides+=1
    if peptides:findings.add("constructed-nonproline-peptide-not-trans")
    findings.update(library_minimizer_findings(optimizer, final, source.maximum_gradient_kj_mol_nm,
        platform=source.construction_platform, threads=source.construction_threads))
    from empirical_lawhood.domains.rubisco.rubisco_response.molecular_quality import assess_molecular_geometry, fixed_bond_feasibility, geometry_terms_from_amber
    terms = geometry_terms_from_amber(files["dry.prmtop"])
    assessment_type, extra = GpGeometryRepairAssessment, {}
    if refined:
        feasibility = fixed_bond_feasibility(first*10, terms, mobile, source.geometry_quality)
        if (selection.get("fixed_bond_feasibility") != feasibility or feasibility["violations"]
                or selection.get("refined_inherited_heavy_atoms") != [list(key) for key in refined]
                or selection.get("heavy_join") != [[list(key), index] for key, index in sorted(joined.items())]
                or selection.get("constructed_heavy_count") != len(constructed)
                or selection.get("fixed_heavy_count") != len(joined)-len(permitted)
                or selection.get("amber_term_census") != census["term_census"]
                or selection.get("atom_count") != n or selection.get("all_hydrogens_mobile") is not True
                or optimizer.get("interpretation") != source.scope or optimizer.get("no_ensemble_or_rate_admission") is not True):
            raise ValueError("retained repair changes the selected inherited mobility or fixed-bond feasibility")
        maximum, displacement_findings, rows = _refined_displacement_assessment(refined, joined, first, final,
            optimizer.get("refined_inherited_displacements_angstrom"), source.maximum_refined_displacement_angstrom)
        findings.update(displacement_findings)
        assessment_type = GpAmberFragmentRepairAssessment if type(source) is GpAmberFragmentRepairInput else GpCarboxylateRepairAssessment
        extra.update(refined_inherited_heavy_atoms=len(refined), largest_refined_displacement_angstrom=maximum,
                     refined_displacements_angstrom=rows, fixed_bonds_checked=feasibility["fixed_bonds"])
    quality = assess_molecular_geometry(final*10, terms, policy=source.geometry_quality)
    if refined:
        extra["planarity"] = GpRepairPlanarityAssessment.from_quality(quality)
    if quality["disposition"] != "SCREEN_PASSED":
        findings.add("whole-molecule-geometry-screen")
    if optimizer.get("whole_molecule_quality") != quality["disposition"]:
        raise ValueError("repair summary substitutes the independent complete geometry screen")
    from empirical_lawhood.domains.rubisco.rubisco_response.amber_construction_admission import assess_retained_force_assignment, _document
    assess_retained_force_assignment(files["dry.prmtop"], files["force-assignment.json"])
    initialization = _document(files["initialization.json"])
    if (initialization.get("no_custom_terminal_search") is not True
            or initialization.get("no_custom_minimizer") is not True
            or initialization.get("constructed_atoms") != [list(key) for key in movable_heavy]):
        raise ValueError("repair changes its declared library construction and complete selected atom scope")
    if type(source) is GpAmberFragmentRepairInput:
        read_amber_fragment_initialization(source, files, initialization)
    else:
        expected_transform = {"kind": "pdbfixer-complete-selected-missing-heavy-atoms", "seed": source.construction_seed,
            "platform": source.construction_platform, "threads": source.construction_threads,
            "constructed_heavy_atoms": len(constructed), "protected_heavy_atoms": len(original)-len(constructed),
            "replace_nonstandard_residues": False, "remove_heterogens": False}
        if (initialization.get("method") != "PDBFIXER_MISSING_HEAVY_ATOMS_AMBER_HYDROGENS_OPENMM_MINIMIZATION"
                or initialization.get("transformations") != [expected_transform]):
            raise ValueError("repair changes its selected library construction seed, platform or protected chemical scope")
    from empirical_lawhood.domains.rubisco.rubisco_response.amber_construction_log import assess_leap_diagnostics
    dry_charge = sum(census["charges_scaled"], Decimal(0))/Decimal("18.2223")
    integral_charge = abs(dry_charge-dry_charge.to_integral_value()) <= Decimal("0.0005")
    if not integral_charge:
        findings.add("nonintegral-source-dry-charge")
    logs = assess_leap_diagnostics(files["amber.stdout"], files["amber.stderr"],
        complete_endpoint_satisfied=not findings,
        selected_integral_dry_charge=integral_charge and source.dry_charge_policy == "SOURCE_ASSIGNED_INTEGRAL_CHARGE_NONPERIODIC")
    findings.update(logs["findings"])
    return assessment_type(assessment_id,source_identity,tuple((name,sha256(files[name]).hexdigest()) for name in assessment_files),
        len(original),len(original)-len(permitted),len(constructed),len(mobile),Decimal(str(gradient)),Decimal(str(bond_error)),
        Decimal(str(minimum)),contacts,stretches,stereo,peptides,tuple(sorted(findings)),A.FALSIFIED if findings else A.SATISFIED, **extra)
