# SPDX-License-Identifier: MPL-2.0
"""Source-bound construction protocols for the common inhibited Gp parent."""

from dataclasses import dataclass, field
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import PurePosixPath
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.geometry_reuse import GeometryReuseSupply
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.preamber_geometry_integrity import PreAmberGeometryIntegrity
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, canonical_json_bytes, validate_decimal, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology import GpAmberEngine
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_quality import AMBER_PLANARITY_BASIS, MolecularGeometryPolicy


from empirical_lawhood.domains.rubisco.rubisco_response.construction_engine import CONSTRUCTION_PACKAGES, GpRepairNumericEngine, validate_construction_platform

GEOMETRY_ID = "geometry.gp.wt.m1.joint-01"
LEGACY_REPAIR_PROTOCOL = "constructed-only-v3"
CARBOXYLATE_REPAIR_PROTOCOL = "gp-1bwv-glu213-carboxylate-v1"
AMBER_FRAGMENT_PROTOCOL = "gp-1bwv-amber-terminal-fragments-v1"


def _validate_carboxylate_limits(displacement_limit, policy):
    validate_decimal(displacement_limit, field_name="maximum_refined_displacement_angstrom", minimum=Decimal(0))
    if displacement_limit == 0 or policy != MolecularGeometryPolicy(basis=AMBER_PLANARITY_BASIS):
        raise ValueError("Glu213 refinement requires a positive displacement limit and the selected unmodified nominal-Amber screen")


def inherited_carboxylate_keys(origin, *, parent_atoms=None):
    """Select only the inherited CD/OE1/OE2 triplet in each original 1BWV LSU."""
    chains = [r["chain"] for r in origin["complete_chains"] if r["subunit"] == "lsu"]
    if sorted(chains) != list("ACEGIKMO"):
        raise ValueError("Glu213 refinement requires the eight original 1BWV large subunit copies")
    elements = {"CD": "C", "OE1": "O", "OE2": "O"}
    expected = {(chain, 213, atom) for chain in chains for atom in elements}
    selected = {}
    for original in origin["selected_atom_origins"]:
        key = (original["chain"], original["position"], original["atom"])
        if key in expected:
            if key in selected:
                raise ValueError("Glu213 refinement repeats a selected crystallographic atom")
            selected[key] = original
    found = set()
    for row in origin["complete_heavy_atoms"]:
        key = (row["chain"], row["position"], row["atom"])
        if key not in expected:
            continue
        ref = row["source_origin"]
        if (key in found or row["component"] != "GLU" or row["element"].upper() != elements[key[2]]
                or row["status"] != "INHERITED_OBSERVED_SOURCE" or not isinstance(ref, dict)
                or (ref.get("chain"), ref.get("position"), ref.get("atom")) != key
                or (ref.get("source_component"), ref.get("model_component")) != ("GLU", "GLU")
                or ref != selected.get(key) or not ref.get("source") or ref["source"][0] != "1BWV"):
            raise ValueError("Glu213 refinement changes an inherited named 1BWV carboxylate atom")
        found.add(key)
    if found != expected:
        raise ValueError("Glu213 refinement lacks its full inherited carboxylate census")
    if parent_atoms is not None:
        positions = {(a["chain"], a["position"], a["atom"]): a["xyz"] for a in parent_atoms}
        for key in expected:
            original = selected[key]["original_xyz_angstrom"]
            if tuple(map(Decimal, original)) != positions.get(key):
                raise ValueError("Glu213 displacement must start at the authentic selected crystallographic coordinate")
    return tuple(sorted(found))


@dataclass(frozen=True, slots=True)
class GpGeometryRepairInput(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/gp-geometry-repair-input"
    VERSION: ClassVar[str] = "3.0.0"
    SCOPE: ClassVar[str] = "CONSTRUCTED_ATOMS_ONLY_COMMON_GP_PARENT_NO_ENSEMBLE_OR_RATE_ADMISSION"
    input_id: str
    parent: GeometryReuseSupply
    parent_assessment: PreAmberGeometryIntegrity
    heavy_pdb: str
    origin_json: str
    amber_engine: GpAmberEngine
    numeric_engine: GpRepairNumericEngine
    maximum_gradient_kj_mol_nm: Decimal = Decimal("1")
    maximum_mobile_bond_error_angstrom: Decimal = Decimal("0.15")
    minimum_mobile_nonbonded_heavy_distance_angstrom: Decimal = Decimal("1.6")
    maximum_iterations: int | None = 2000
    geometry_quality: MolecularGeometryPolicy = field(default_factory=MolecularGeometryPolicy)
    construction_seed: int = 20261114
    dry_charge_policy: str = "SOURCE_ASSIGNED_INTEGRAL_CHARGE_NONPERIODIC"
    scope: str = SCOPE
    construction_platform: str = "CPU"
    construction_threads: int = 8

    def __post_init__(self):
        validate_stable_id(self.input_id)
        validate_construction_platform(self.construction_platform, self.construction_threads)
        exact(self.geometry_quality, MolecularGeometryPolicy)
        for record,kind in ((self.parent,GeometryReuseSupply),(self.parent_assessment,PreAmberGeometryIntegrity),
                            (self.amber_engine,GpAmberEngine),(self.numeric_engine,GpRepairNumericEngine)):
            exact(record,kind)
        assessment = self.parent_assessment
        if (self.parent.definition.subwork_id != GEOMETRY_ID
                or assessment.geometry_definition != self.parent.definition.identity
                or assessment.geometry_receipt != self.parent.geometry_receipt
                or self.parent.independent_integrity != ObjectIdentity.from_record(assessment.product_id,assessment)
                or self.scope != self.SCOPE
                or self.dry_charge_policy != "SOURCE_ASSIGNED_INTEGRAL_CHARGE_NONPERIODIC"
                or type(self.construction_seed) is not int or not 0 <= self.construction_seed < 2**31
                or any(type(v) is not Decimal for v in (self.maximum_gradient_kj_mol_nm,
                    self.maximum_mobile_bond_error_angstrom,self.minimum_mobile_nonbonded_heavy_distance_angstrom))
                or (self.maximum_gradient_kj_mol_nm,self.maximum_mobile_bond_error_angstrom,
                    self.minimum_mobile_nonbonded_heavy_distance_angstrom) != (Decimal("1"),Decimal("0.15"),Decimal("1.6"))
                or (self.maximum_iterations is not None and
                    (type(self.maximum_iterations) is not int or self.maximum_iterations < 1))):
            raise ValueError("geometry repair changes its original common parent or declared numerical stopping rules")
        if {PurePosixPath(row.relative_path).parts[0] for row in self.numeric_engine.files} != set(CONSTRUCTION_PACKAGES):
            raise ValueError("new construction requires authenticated PDBFixer and complete OpenMM; custom pair kernels are not a default")
        for text,evidence in ((self.heavy_pdb,assessment.heavy_file),(self.origin_json,assessment.origin_file)):
            if type(text) is not str or (len(text.encode()),sha256(text.encode()).hexdigest()) != (evidence.byte_count,evidence.sha256):
                raise ValueError("geometry repair substitutes the original authenticated geometry/origin bytes")
        from empirical_lawhood.domains.rubisco.rubisco_response.gp_constructed_geometry import origin_mobility
        origin = json.loads(self.origin_json)
        atoms,movable = origin_mobility(self.heavy_pdb,origin)
        if len(atoms) != assessment.atom_count or len(movable) != assessment.constructed_atom_count:
            raise ValueError("geometry repair changes its complete observed/constructed atom denominator")
        if isinstance(self, GpCarboxylateRepairInput):
            inherited_carboxylate_keys(origin, parent_atoms=atoms)
        source = {s.member_id:s for s in self.parent.original_source.source_members}
        actual = {r.relative_path:r for r in self.amber_engine.files}
        for name,path in (("source.parm10-dat","parm/parm10.dat"),
                ("source.ff14sb-frcmod","parm/frcmod.ff14SB"),("source.gaff2-dat","parm/gaff2.dat"),
                ("source.leaprc-protein-ff14sb","cmd/leaprc.protein.ff14SB"),
                ("source.leaprc-water-tip3p","cmd/leaprc.water.tip3p"),("source.leaprc-gaff2","cmd/leaprc.gaff2")):
            row = actual.get("toolchain/dat/leap/"+path)
            if row is None or (row.sha256,row.byte_count) != (source[name].sha256,len(source[name].raw_utf8.encode())):
                raise ValueError("geometry repair changes the original selected Amber parameter stock")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.input_id,self)


@dataclass(frozen=True, slots=True, kw_only=True)
class GpCarboxylateRepairInput(GpGeometryRepairInput):
    VERSION: ClassVar[str] = "4.0.0"
    SCOPE: ClassVar[str] = "CONSTRUCTED_AND_INHERITED_LSU_GLU213_CARBOXYLATES_COMMON_GP_PARENT_NO_ENSEMBLE_OR_RATE_ADMISSION"
    scope: str = SCOPE
    maximum_refined_displacement_angstrom: Decimal

    def __post_init__(self):
        _validate_carboxylate_limits(self.maximum_refined_displacement_angstrom, self.geometry_quality)
        GpGeometryRepairInput.__post_init__(self)


@dataclass(frozen=True, slots=True, kw_only=True)
class GpAmberFragmentRepairInput(GpCarboxylateRepairInput):
    VERSION: ClassVar[str] = "5.0.0"
    SCOPE: ClassVar[str] = "AMBER_STOCK_TERMINAL_FRAGMENTS_AND_LSU_GLU213_COMMON_GP_PARENT_NO_ENSEMBLE_OR_RATE_ADMISSION"
    scope: str = SCOPE

    def __post_init__(self):
        from .terminal_fragment_placement import met_template_pin, terminal_stock_pins
        if self.maximum_iterations is None or self.construction_seed != 20261114:
            raise ValueError("deterministic Amber fragments require a finite full-optimizer ceiling and the fixed seed field")
        GpCarboxylateRepairInput.__post_init__(self)
        terminal_stock_pins(self.amber_engine)
        met_template_pin(self.numeric_engine)


REPAIR_INPUT_TYPES = (GpGeometryRepairInput, GpCarboxylateRepairInput, GpAmberFragmentRepairInput)


def prepare_geometry_repair_input(*,parent,parent_assessment,heavy_pdb,origin_json,amber_engine,numeric_engine,
                                 geometry_quality=None, maximum_iterations=2000, construction_seed=20261114,
                                 construction_platform="CPU", construction_threads=8,
                                 parent_repair_protocol=LEGACY_REPAIR_PROTOCOL, maximum_refined_displacement_angstrom=None):
    """Derive the exact common-parent repair operand; make no native call."""
    if parent_repair_protocol not in (LEGACY_REPAIR_PROTOCOL, CARBOXYLATE_REPAIR_PROTOCOL, AMBER_FRAGMENT_PROTOCOL):
        raise ValueError("unknown common-parent repair protocol")
    fresh = parent_repair_protocol != LEGACY_REPAIR_PROTOCOL
    if fresh != (maximum_refined_displacement_angstrom is not None):
        raise ValueError("select an explicit displacement limit only with the named Glu213 repair protocol")
    policy = geometry_quality
    if policy is None:
        policy = MolecularGeometryPolicy(basis=AMBER_PLANARITY_BASIS) if fresh else MolecularGeometryPolicy()
    exact(policy, MolecularGeometryPolicy)
    selection = json.dumps([maximum_iterations, construction_seed, construction_platform, construction_threads]).encode()
    kwargs = {}
    kind = GpGeometryRepairInput
    if fresh:
        _validate_carboxylate_limits(maximum_refined_displacement_angstrom, policy)
        kwargs["maximum_refined_displacement_angstrom"] = maximum_refined_displacement_angstrom
        kind = GpAmberFragmentRepairInput if parent_repair_protocol == AMBER_FRAGMENT_PROTOCOL else GpCarboxylateRepairInput
        selection += canonical_json_bytes((parent_repair_protocol, maximum_refined_displacement_angstrom))
    digest=sha256(parent.canonical_bytes()+parent_assessment.canonical_bytes()+heavy_pdb.encode()+origin_json.encode()
        +amber_engine.canonical_bytes()+numeric_engine.canonical_bytes()+policy.canonical_bytes()
        +selection).hexdigest()
    return kind("input.gp-constructed-repair."+digest,parent,parent_assessment,heavy_pdb,origin_json,amber_engine,numeric_engine,
        maximum_iterations=maximum_iterations, geometry_quality=policy, construction_seed=construction_seed,
        construction_platform=construction_platform, construction_threads=construction_threads, **kwargs)
