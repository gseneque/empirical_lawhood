# SPDX-License-Identifier: MPL-2.0
"""Pure inputs and exact recipes for four initial Gp Amber topologies.

This is the keto starting topology with explicitly neutral HIE histidines.
It does not prepare the reactive proton-allocation/Mg-water ensemble, run a
trajectory, or identify free-solution activities from a buffer label.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import PurePosixPath
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.contracts import FileEvidence, SourceMember, KCX_ALIASES
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.preparation import scoped_boundary_stock, scoped_kcx_stock, _parm_dat_sections, _frcmod_sections
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.coordinate_plan import THREE
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_relative_locator, validate_stable_id
from empirical_lawhood.storage.contracts.artifacts import ArtifactManifest
from empirical_lawhood.domains.rubisco.rubisco_response.amber_template import assess_initial_templates, read_amber_template
from empirical_lawhood.domains.rubisco.rubisco_response.gp_active_scaffold import GpActiveScaffold, scaffold_pdb
from empirical_lawhood.domains.rubisco.rubisco_response.gp_active_scaffold_assessment import GpScaffoldAssessment
from empirical_lawhood.domains.rubisco.rubisco_response.materials import RubiscoMaterial, exact
from empirical_lawhood.domains.rubisco.rubisco_response.rubp_preparation import RuBPTetraanionPreparation
from empirical_lawhood.domains.rubisco.rubisco_response.construction_engine import CONSTRUCTION_PACKAGES, GpRepairNumericEngine, validate_construction_platform
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_quality import MolecularGeometryPolicy


MODEL_NAMES = ("m1-wt", "m1-i95m", "v1-wt", "v1-i95m")
STOCK_NAMES = ("ff14sb.frcmod", "kcx.frcmod", "kcx.prepin", "parm10.dat", "rubp.frcmod", "rubp.prepi")
SCOPE = "FOUR_FULL_GP_KETO_STARTING_TOPOLOGIES_HIE_NEUTRALIZING_IONS_NOT_REACTIVE_ENSEMBLES"
CONTEXT = (
    "TIP3P water; 10 angstrom rectangular padding; original waters retained before ion placement.",
    "Neutralizing Na/Cl counterions only; no added bulk salt, free Mg reservoir or explicit buffer molecules.",
    "298.15 K and pH 8.0 are downstream selections, not a thermal or proton-equilibrium calculation by tleap.",
    "Standard ASP/GLU anionic, LYS/ARG cationic, CYS/TYR neutral, HIS initially HIE; charged protein termini.",
    "All eight bound Mg, anionic KCX and keto RuBP4- sites retained; no carbamate proton or enolate is modeled here.",
    "Assay-specific salt, free-Mg and buffer activities remain unresolved; no absolute assay prediction is admitted.",
)


@dataclass(frozen=True, slots=True)
class GpAmberEngine(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/gp-amber-engine"
    engine_id: str
    root: str
    files: tuple[FileEvidence, ...]
    executable: str = "toolchain/bin/teLeap"
    library_directory: str = "runtime/lib"

    def __post_init__(self):
        validate_stable_id(self.engine_id)
        root = PurePosixPath(self.root)
        if not root.is_absolute() or str(root) != self.root or ".." in root.parts:
            raise ValueError("initial Amber engine needs its exact selected absolute root")
        if type(self.files) is not tuple or not self.files:
            raise ValueError("initial Amber engine needs its complete selected file closure")
        for row in self.files:
            exact(row, FileEvidence)
            validate_relative_locator(row.relative_path)
        names = tuple(row.relative_path for row in self.files)
        if names != tuple(sorted(set(names))) or self.executable not in names:
            raise ValueError("initial Amber engine drops its executable or complete file census")
        if self.executable != "toolchain/bin/teLeap" or self.library_directory != "runtime/lib":
            raise ValueError("initial Amber engine changes its declared tool/library layout")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.engine_id, self)


@dataclass(frozen=True, slots=True)
class GpAmberModelInput(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/gp-amber-model-input"
    name: str
    scaffold: ObjectIdentity
    assessment: GpScaffoldAssessment
    material: RubiscoMaterial
    chain_map: tuple[tuple[str, str], ...]
    heavy_pdb: str
    original_manifest: ArtifactManifest

    def __post_init__(self):
        if self.name not in MODEL_NAMES:
            raise ValueError("initial Amber input changes the complete four-material selection")
        exact(self.scaffold, ObjectIdentity)
        exact(self.assessment, GpScaffoldAssessment)
        exact(self.material, RubiscoMaterial)
        exact(self.original_manifest, ArtifactManifest)
        if (self.scaffold.object_schema != GpActiveScaffold.SCHEMA or self.assessment.scaffold != self.scaffold
                or self.assessment.correspondence_disposition is not A.SATISFIED
                or self.assessment.active_ensemble_admission is not A.UNEVALUABLE):
            raise ValueError("initial topology requires original satisfied heavy correspondence without ensemble promotion")
        raw = self.heavy_pdb.encode("ascii")
        if (len(raw), sha256(raw).hexdigest()) != (self.original_manifest.materialization.size_bytes,
                                                 self.original_manifest.materialization.physical_sha256):
            raise ValueError("initial topology substitutes the original published heavy PDB bytes")
        if (tuple(a for a, _ in self.chain_map) != tuple("ABCDEFGHIJKLMNOP")
                or set(b for _, b in self.chain_map) != {c.chain_id for c in self.material.chains}):
            raise ValueError("initial topology drops the complete physical-to-sequence chain map")
        rows = heavy_pdb_rows(self.heavy_pdb)
        if len(rows) != self.assessment.atom_count:
            raise ValueError("initial topology drops the assessed heavy atom denominator")
        residues = {}
        for chain, position, component, name, element, xyz in rows:
            key = (chain, position)
            previous = residues.setdefault(key, component)
            if previous != component or element == "H":
                raise ValueError("initial heavy topology changes its residue or contains unassessed hydrogens")
        expected_chains = {physical: next(c for c in self.material.chains if c.chain_id == sequence)
                           for physical, sequence in self.chain_map}
        for chain, material_chain in expected_chains.items():
            values = tuple((position, component) for (key, position), component in residues.items() if key == chain)
            if tuple(p for p, _ in values) != tuple(range(1, len(material_chain.sequence)+1)):
                raise ValueError("initial topology omits a completed protein residue")
            for (_, component), letter in zip(values, material_chain.sequence, strict=True):
                permitted = {"HIS", "HID", "HIE"} if letter == "H" else {"LYS", "KCX"} if letter == "K" else {THREE[letter]}
                if component not in permitted:
                    raise ValueError("initial topology substitutes a full protein sequence")
        if set(residues) - {(c, p) for c, chain in expected_chains.items() for p in range(1, len(chain.sequence)+1)} != {
                key for key, component in residues.items() if key[0] == "Z" and component in ("RUB", "MG", "HOH")}:
            raise ValueError("initial topology contains an undeclared chemical or protein residue")
        if any(sum(component == name for component in residues.values()) != count
               for name, count in (("RUB", 8), ("MG", 8), ("KCX", 8), ("HOH", 1084))):
            raise ValueError("initial topology drops an all-site chemical or retained-water denominator")

    @property
    def identity(self):
        return ObjectIdentity.from_record("initial-topology-input." + self.name + "." + self.scaffold.object_fingerprint, self)


def heavy_pdb_rows(text):
    rows, keys = [], set()
    for line in text.splitlines():
        if not line.startswith(("ATOM  ", "HETATM")):
            continue
        if len(line) < 78 or line[16] != " " or line[26] != " ":
            raise ValueError("initial topology requires exact single-conformer heavy PDB rows")
        chain, position, component, name, element = line[21], int(line[22:26]), line[17:20].strip(), line[12:16].strip(), line[76:78].strip()
        xyz = tuple(Decimal(line[i:i+8].strip()) for i in (30, 38, 46))
        key = (chain, position, name)
        if key in keys or any(not v.is_finite() for v in xyz):
            raise ValueError("initial topology duplicates an atom or contains nonfinite coordinates")
        keys.add(key)
        rows.append((chain, position, component, name, element, xyz))
    if not rows:
        raise ValueError("initial topology has no original heavy coordinates")
    return tuple(rows)


@dataclass(frozen=True, slots=True)
class GpInitialAmberInput(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/gp-initial-amber-input"
    VERSION: ClassVar[str] = "3.0.0"
    input_id: str
    models: tuple[GpAmberModelInput, ...]
    ligand: RuBPTetraanionPreparation
    parameter_sources: tuple[SourceMember, ...]
    engine: GpAmberEngine
    numeric_engine: GpRepairNumericEngine
    geometry_quality: MolecularGeometryPolicy = field(default_factory=MolecularGeometryPolicy)
    maximum_minimization_iterations: int = 2000
    maximum_minimization_gradient_kj_mol_nm: Decimal = Decimal("1")
    minimization_nonbonded_cutoff_angstrom: Decimal = Decimal("10")
    minimization_ewald_tolerance: Decimal = Decimal("0.000001")
    construction_seed: int = 20261114
    minimum_stereocentre_volume_angstrom3: Decimal = Decimal("0.01")
    context: tuple[str, ...] = CONTEXT
    scope: str = SCOPE
    per_model_timeout_seconds: int | None = None
    maximum_model_output_bytes: int = 512 * 2**20
    independent_biological_units: int = 0
    construction_platform: str = "CPU"
    construction_threads: int = 8

    def __post_init__(self):
        validate_stable_id(self.input_id)
        validate_construction_platform(self.construction_platform, self.construction_threads)
        exact(self.ligand, RuBPTetraanionPreparation)
        exact(self.engine, GpAmberEngine)
        exact(self.numeric_engine, GpRepairNumericEngine)
        exact(self.geometry_quality, MolecularGeometryPolicy)
        if ({PurePosixPath(row.relative_path).parts[0] for row in self.numeric_engine.files} != set(CONSTRUCTION_PACKAGES)
                or type(self.maximum_minimization_iterations) is not int or self.maximum_minimization_iterations < 1
                or type(self.construction_seed) is not int or not 0 <= self.construction_seed < 2**31
                or any(type(value) is not Decimal or not value.is_finite() or value <= 0 for value in (
                    self.maximum_minimization_gradient_kj_mol_nm, self.minimization_nonbonded_cutoff_angstrom,
                    self.minimization_ewald_tolerance, self.minimum_stereocentre_volume_angstrom3)) or self.minimization_ewald_tolerance >= 1):
            raise ValueError("initial construction requires complete PDBFixer/OpenMM and finite source-selected minimization limits")
        if type(self.models) is not tuple or tuple(m.name for m in self.models) != MODEL_NAMES:
            raise ValueError("initial Amber input must retain all four paired materials")
        for model in self.models:
            exact(model, GpAmberModelInput)
        if (tuple(s.member_id for s in self.parameter_sources) != tuple("source.gp-initial-amber." + n for n in STOCK_NAMES)
                or self.context != CONTEXT or self.scope != SCOPE
                or self.per_model_timeout_seconds is not None and (
                    type(self.per_model_timeout_seconds) is not int or self.per_model_timeout_seconds <= 0)
                or type(self.maximum_model_output_bytes) is not int or self.maximum_model_output_bytes != 512 * 2**20
                or type(self.independent_biological_units) is not int or self.independent_biological_units != 0):
            raise ValueError("initial Amber input changes its exact context, parameter census or finite limits")
        for member in self.parameter_sources:
            exact(member, SourceMember)
        engine_files = {row.relative_path:row for row in self.engine.files}
        source_files = {row.member_id.removeprefix("source.gp-initial-amber."):row for row in self.parameter_sources}
        for name,path in (("ff14sb.frcmod","toolchain/dat/leap/parm/frcmod.ff14SB"),
                          ("parm10.dat","toolchain/dat/leap/parm/parm10.dat")):
            expected = engine_files.get(path)
            member = source_files[name]
            if expected is None or (expected.sha256,expected.byte_count) != (member.sha256,len(member.raw_utf8.encode())):
                raise ValueError("initial Amber boundary source differs from the actual selected engine stock")
        # Exact pair sequences are checked independently of source labels.
        for wild, mutant in ((self.models[0], self.models[1]), (self.models[2], self.models[3])):
            for left, right in zip(wild.material.chains, mutant.material.chains, strict=True):
                expected = left.sequence if left.subunit == "LSU" else left.sequence[:94] + "M" + left.sequence[95:]
                if right.sequence != expected or left.subunit != right.subunit or left.chain_id != right.chain_id:
                    raise ValueError("initial Amber input changes an all-eight-SSU paired I95M sequence")
                if left.subunit == "SSU" and left.sequence[94] != "I":
                    raise ValueError("initial Amber input lacks original SSU I95")
        for model in self.models:
            initial = "M" if model.name.startswith("m1-") else "V"
            if any(c.sequence[0] != initial for c in model.material.chains if c.subunit == "SSU"):
                raise ValueError("initial Amber input substitutes its M1/V1 processing case")
        initial_parameter_files(self.parameter_sources, self.ligand)

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.input_id, self)


def construct_kcx_hydrogen_distances(prepi, frcmod):
    """Derive terminal H distances from the original KCX bond parameters.

    The source template places ten H atoms at 0.849--0.850 Angstrom. Only
    terminal H internal distances change; charges, types, connectivity,
    angles, dihedrals and all heavy internal coordinates remain exact.
    This is explicit initial construction, not energy minimization.
    """
    from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.preparation import _prepi_rows
    from empirical_lawhood.domains.rubisco.rubisco_response.amber_template import ELEMENTS

    parameters = {}
    for line in _frcmod_sections(frcmod)["BOND"]:
        types = tuple(sorted(t.strip() for t in line[:5].split("-")))
        tokens = line[5:].split()
        if len(types) != 2 or len(tokens) < 2:
            raise ValueError("KCX hydrogen construction requires exact original bond rows")
        value = Decimal(tokens[1])
        if not value.is_finite() or value <= 0:
            raise ValueError("KCX hydrogen construction requires finite positive equilibrium distances")
        if types in parameters and Decimal(parameters[types]) != value:
            raise ValueError("KCX hydrogen construction refuses conflicting original bond parameters")
        parameters[types] = tokens[1]
    rows = _prepi_rows(prepi)
    atoms = {int(tokens[0].group()): tokens for _, tokens in rows}
    if len(atoms) != len(rows):
        raise ValueError("KCX hydrogen construction duplicates an original atom index")
    replacements, changes = {}, []
    for line, tokens in rows:
        typ = tokens[2].group()
        if typ == "DU":
            continue
        if typ not in ELEMENTS:
            raise ValueError("KCX hydrogen construction has an unknown original element")
        if ELEMENTS[typ] != 1:
            continue
        index, parent = int(tokens[0].group()), int(tokens[4].group())
        if (tokens[3].group() != "E" or parent not in atoms
                or any(int(row[4].group()) == index for row in atoms.values())
                or ELEMENTS.get(atoms[parent][2].group(), 1) == 1):
            raise ValueError("KCX hydrogen construction requires a terminal H with one heavy parent")
        pair = tuple(sorted((typ, atoms[parent][2].group())))
        if pair not in parameters:
            raise ValueError("KCX hydrogen construction lacks its original heavy-H bond parameter")
        original = Decimal(tokens[7].group())
        if not original.is_finite() or original <= 0:
            raise ValueError("KCX hydrogen construction has a nonpositive original distance")
        token, selected = tokens[7], parameters[pair]
        replacements[line] = line[:token.start()]+selected.rjust(token.end()-token.start())+line[token.end():]
        changes.append(dict(hydrogen=tokens[1].group(), parent=atoms[parent][1].group(), atom_types=pair,
            original_distance_angstrom=tokens[7].group(), selected_equilibrium_angstrom=selected))
    if len(changes) != 11 or len({row["hydrogen"] for row in changes}) != 11:
        raise ValueError("KCX hydrogen construction loses its complete eleven-H denominator")
    derived = "".join(replacements.get(line, line) for line in prepi.splitlines(keepends=True))
    report = dict(original_template_sha256=sha256(prepi.encode()).hexdigest(),
        original_parameters_sha256=sha256(frcmod.encode()).hexdigest(),
        derived_template_sha256=sha256(derived.encode()).hexdigest(), changes=changes,
        method="TERMINAL_H_INTERNAL_DISTANCE_FROM_ORIGINAL_BOND_EQUILIBRIUM",
        scope="INITIAL_CONSTRUCTION_ONLY_NO_MINIMIZATION_OR_PHYSICAL_ADMISSION")
    return derived, report


def initial_parameter_files(sources, ligand):
    """Reuse exact scoped-KCX owners and source decimals; execute no Amber code."""
    stock = {s.member_id.removeprefix("source.gp-initial-amber."): s for s in sources}
    if tuple(sorted(stock)) != STOCK_NAMES:
        raise ValueError("initial Amber parameter source census changed")
    rubp = read_amber_template(stock["rubp.prepi"], template_id="template.initial-gp.rubp")
    kcx = read_amber_template(stock["kcx.prepin"], template_id="template.initial-gp.kcx")
    assess_initial_templates(rubp, kcx, ligand)
    existing = {line.split()[0] for section in (_parm_dat_sections(stock["parm10.dat"].raw_utf8),
        _frcmod_sections(stock["ff14sb.frcmod"].raw_utf8)) for line in section["MASS"]}
    constructed_kcx, hydrogen_construction = construct_kcx_hydrogen_distances(
        stock["kcx.prepin"].raw_utf8, stock["kcx.frcmod"].raw_utf8)
    custom = scoped_kcx_stock(constructed_kcx, stock["kcx.frcmod"].raw_utf8, existing_atom_types=existing)
    boundary = scoped_boundary_stock(stock["parm10.dat"].raw_utf8, stock["ff14sb.frcmod"].raw_utf8)
    return {"kcx-scoped.prepin": custom.scoped_prepi_utf8, "kcx-scoped.frcmod": custom.scoped_custom_frcmod_utf8,
        "kcx-boundaries.frcmod": boundary.scoped_boundary_frcmod_utf8, "rubp.prepi": stock["rubp.prepi"].raw_utf8,
        "rubp.frcmod": stock["rubp.frcmod"].raw_utf8,
        "kcx-hydrogen-construction.json": json.dumps(hydrogen_construction, sort_keys=True, indent=2)+"\n"}


def initial_heavy_pdb(model):
    """Explicit HIE starting assignment; separate every chemical residue."""
    exact(model, GpAmberModelInput)
    lines, previous, serial = ["REMARK INITIAL KETO TOPOLOGY; HIE HYPOTHESIS; NOT EQUILIBRATED"], None, 0
    for chain, position, component, name, element, xyz in heavy_pdb_rows(model.heavy_pdb):
        if previous is not None and (previous[0] != chain or chain == "Z" and previous[1] != position):
            serial += 1
            lines.append(f"TER   {serial:5d}")
        serial += 1
        component = "HIE" if component in {"HIS", "HID", "HIE"} else component
        label = name.rjust(4) if len(element) == 2 else (" " + name).ljust(4)
        coordinate = "".join(f"{v:8.3f}" for v in xyz)
        lines.append(f"HETATM{serial:5d} {label} {component:3s} {chain}{position:4d}    {coordinate}  1.00  0.00          {element:>2s}  ")
        previous = chain, position
    return "\n".join((*lines, "TER", "END")) + "\n"


def initial_leap_script(*, random_solvent_replacement=False, explicit_solvated_check=True):
    element = dict(C="C", CT="C", H="H", H1="H", HC="H", N="N", O="O", O2="O")
    hybrid = dict(C="sp2", CT="sp3", H="sp3", H1="sp3", HC="sp3", N="sp2", O="sp2", O2="sp2")
    types = "addAtomTypes { " + " ".join('{ "' + alias + '" "' + element[typ] + '" "' + hybrid[typ] + '" }'
        for typ, alias in KCX_ALIASES) + " }"
    ions = "addIonsRand" if random_solvent_replacement else "addIons"
    return "\n".join(("source leaprc.protein.ff14SB", "source leaprc.water.tip3p", "source leaprc.gaff2", types,
        "loadAmberPrep kcx-scoped.prepin", "loadAmberParams kcx-boundaries.frcmod", "loadAmberParams kcx-scoped.frcmod",
        "loadAmberPrep rubp.prepi", "loadAmberParams rubp.frcmod", "model = loadPDB library-heavy.pdb", "check model",
        "saveAmberParm model dry.prmtop dry.inpcrd", "solvateBox model TIP3PBOX 10.0", f"{ions} model Na+ 0",
        f"{ions} model Cl- 0", *(("check model",) if explicit_solvated_check else ()), "saveAmberParm model model.prmtop model.inpcrd", "quit", ""))


def prepare_initial_amber_input(*, scaffolds, assessments, manifests, ligand, parameter_sources, engine,
                                numeric_engine, geometry_quality=None, maximum_minimization_iterations=2000,
                                maximum_minimization_gradient_kj_mol_nm=Decimal("1"),
                                minimization_nonbonded_cutoff_angstrom=Decimal("10"),
                                minimization_ewald_tolerance=Decimal("0.000001"), construction_seed=20261114,
                                minimum_stereocentre_volume_angstrom3=Decimal("0.01"),
                                construction_platform="CPU", construction_threads=8):
    """Derive the native input after the public retained scaffold read passes."""
    if not (len(scaffolds) == len(assessments) == len(manifests) == 4):
        raise ValueError("initial Amber preparation requires all four original model publications")
    models = tuple(GpAmberModelInput(name, scaffold.identity, assessment, scaffold.material, scaffold.chain_map,
        scaffold_pdb(scaffold, ligand), manifest) for name, scaffold, assessment, manifest
        in zip(MODEL_NAMES, scaffolds, assessments, manifests, strict=True))
    # Bind every authored construction choice into the new operand identity.
    from dataclasses import replace
    provisional = GpInitialAmberInput("input.gp-initial-topology.provisional", models, ligand, parameter_sources,
        engine, numeric_engine, MolecularGeometryPolicy() if geometry_quality is None else geometry_quality, maximum_minimization_iterations,
        maximum_minimization_gradient_kj_mol_nm, minimization_nonbonded_cutoff_angstrom, minimization_ewald_tolerance,
        construction_seed, minimum_stereocentre_volume_angstrom3,
        construction_platform=construction_platform, construction_threads=construction_threads)
    result = replace(provisional, input_id="input.gp-initial-topology." + provisional.fingerprint())
    from empirical_lawhood.domains.rubisco.rubisco_response.gp_heavy_geometry import require_initial_heavy_geometry
    require_initial_heavy_geometry(result)
    return result
