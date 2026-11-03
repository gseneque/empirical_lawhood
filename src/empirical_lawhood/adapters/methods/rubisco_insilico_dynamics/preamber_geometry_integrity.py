# SPDX-License-Identifier: MPL-2.0
"""Independent source/genotype/origin checks before genuine Amber assignment.

The caller authenticates the original completed geometry definition, receipt,
raw archive and complete census. Original deposited structures are read by the
independent structural owner. This module performs no producer replay or native
import. Reuse integrity is separate from chemical/topological completeness,
protonation adequacy, physical geometry, dynamics and mutant function.
"""

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.runtime.artifacts import CanonicalTaskReceipt
from empirical_lawhood.runtime.native_subwork import NativeSubworkCompletion, NativeSubworkDefinition

from . import contracts as c
from .preparation_integrity import AMINO, _selected_originals
from .serialized_heavy_pdb import METHOD as PDB_METHOD, read_serialized_heavy_pdb


DESCRIPTION = (
    "Independent original assembly alternate/source-token joins, full selected "
    "L8S8 genotype/residue denominator, every serialized heavy atom origin and "
    "inherited/constructed role, finite raw coordinate tokens, source-named "
    "disulfide declarations and raw SG CONECT references. Original geometry "
    "serials/TER and every directed bond term retained. Reuse integrity only; "
    "no Amber assignment/full covalent completeness/protonation/physical or "
    "ensemble/kinetic/biological admission."
)
METHOD = ObjectIdentity(
    "method.rubisco-dynamics.pre-amber-geometry-integrity",
    "empirical-lawhood/rubisco-insilico-dynamics/pre-amber-geometry-integrity-method",
    "1.0.0", sha256(DESCRIPTION.encode()).hexdigest(),
)


@dataclass(frozen=True, slots=True)
class PreAmberGeometryIntegrity(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-dynamics/pre-amber-geometry-integrity"
    VERSION: ClassVar[str] = "1.0.0"
    product_id: str
    source: ObjectIdentity
    geometry_definition: ObjectIdentity
    geometry_completion: ObjectIdentity
    geometry_receipt: ObjectIdentity
    construct: c.Construct
    joint_view_id: str
    heavy_file: c.FileEvidence
    origin_file: c.FileEvidence
    atom_count: int
    protein_residue_count: int
    residue_count: int
    inherited_atom_count: int
    constructed_atom_count: int
    ter_count: int
    conect_row_count: int
    directed_conect_term_count: int
    source_disulfide_count: int
    method: ObjectIdentity = METHOD
    pdb_reader_method: ObjectIdentity = PDB_METHOD
    source_origin_disposition: A = A.SATISFIED
    amber_assignment_disposition: A = A.UNEVALUABLE
    covalent_completeness_disposition: A = A.UNEVALUABLE
    chemical_adequacy_disposition: A = A.UNEVALUABLE
    physical_geometry_disposition: A = A.UNEVALUABLE
    dynamics_disposition: A = A.UNEVALUABLE
    kinetic_disposition: A = A.UNEVALUABLE
    physical_independent_units: int = 0

    def __post_init__(self):
        validate_stable_id(self.product_id)
        for value in (self.source, self.geometry_definition, self.geometry_completion, self.geometry_receipt):
            if type(value) is not ObjectIdentity:
                raise ValueError("pre-Amber reuse requires exact typed original parents")
            value.__post_init__()
        if (self.source.object_schema != c.PreparationSelection.SCHEMA
                or self.geometry_definition.object_schema != NativeSubworkDefinition.SCHEMA
                or self.geometry_completion.object_schema != NativeSubworkCompletion.SCHEMA
                or self.geometry_receipt.object_schema != CanonicalTaskReceipt.SCHEMA):
            raise ValueError("pre-Amber reuse substitutes the declared original source/progress parent types")
        if type(self.construct) is not c.Construct:
            raise ValueError("pre-Amber reuse omits its exact selected construct")
        self.construct.__post_init__()
        expected_geometry = "geometry." + self.construct.construct_id + "." + self.joint_view_id
        if self.joint_view_id not in ("joint-01", "joint-02") or self.geometry_definition.object_id != expected_geometry:
            raise ValueError("pre-Amber reuse substitutes its actual geometry/material/view")
        for evidence, name in ((self.heavy_file, "complete-heavy.pdb"), (self.origin_file, "atom-origin-provenance.json")):
            if type(evidence) is not c.FileEvidence:
                raise ValueError("pre-Amber reuse needs exact genuine raw operands")
            evidence.__post_init__()
            if evidence.relative_path != expected_geometry + "/" + name or type(evidence.byte_count) is not int or evidence.byte_count <= 0:
                raise ValueError("pre-Amber reuse changes its selected raw operand")
        counts = (self.atom_count, self.protein_residue_count, self.residue_count,
                  self.inherited_atom_count, self.constructed_atom_count, self.ter_count,
                  self.conect_row_count, self.directed_conect_term_count, self.source_disulfide_count)
        if any(type(value) is not int or value < 0 for value in counts):
            raise ValueError("pre-Amber reuse counts must retain exact integer denominators")
        expected_residues = 8 * (len(self.construct.lsu_sequence) + len(self.construct.ssu_sequence))
        if (self.protein_residue_count != expected_residues or self.residue_count < expected_residues
                or self.atom_count < self.residue_count
                or self.atom_count != self.inherited_atom_count + self.constructed_atom_count
                or self.ter_count > self.residue_count
                or self.directed_conect_term_count < self.conect_row_count
                or self.source_disulfide_count != (0 if self.construct.construct_id.startswith("gp.") else 12)):
            raise ValueError("pre-Amber reuse loses a complete source/atom/residue denominator")
        if (self.method != METHOD or self.pdb_reader_method != PDB_METHOD
                or self.source_origin_disposition is not A.SATISFIED
                or any(value is not A.UNEVALUABLE for value in (
                    self.amber_assignment_disposition, self.covalent_completeness_disposition,
                    self.chemical_adequacy_disposition, self.physical_geometry_disposition,
                    self.dynamics_disposition, self.kinetic_disposition))
                or self.physical_independent_units != 0):
            raise ValueError("pre-Amber source/origin integrity cannot establish downstream adequacy")


def validate_geometry_origins(construct, joint_view_id, origin, heavy_text,
                              source_atoms, source_chains, expected_disulfides):
    """Return complete reuse counts; malformed operands refuse without guessing."""
    construct.__post_init__()
    if type(origin) is not dict or joint_view_id not in ("joint-01", "joint-02") or origin.get("joint_view_id") != joint_view_id:
        raise ValueError("pre-Amber geometry changes the selected coordinate view")
    pdb = "1BWV" if construct.construct_id.startswith("gp.") else "3ZXW"
    chains = sorted((row for row in source_chains if row.pdb_id == pdb), key=lambda row: row.chain_id)
    atoms = tuple(row for row in source_atoms if row.pdb_id == pdb)
    if len(chains) != 16 or len({row.chain_id for row in chains}) != 16:
        raise ValueError("pre-Amber original source omits full unique L8S8 chains")
    expected = [dict(chain="ABCDEFGHIJKLMNOP"[index], source_chain=row.chain_id,
        subunit="lsu" if len(row.full_sequence) in (493, 475) else "ssu",
        sequence=construct.lsu_sequence if len(row.full_sequence) in (493, 475) else construct.ssu_sequence)
        for index, row in enumerate(chains)]
    if sum(row["subunit"] == "lsu" for row in expected) != 8 or any(len(row.full_sequence) != len(selected["sequence"]) for row, selected in zip(chains, expected, strict=True)):
        raise ValueError("pre-Amber source changes full L8S8 subunit lengths")
    sequences = {}
    for subunit in ("lsu", "ssu"):
        values = {observed.full_sequence for observed, selected in zip(chains, expected, strict=True) if selected["subunit"] == subunit}
        if len(values) != 1:
            raise ValueError("pre-Amber source substitutes a full assembly sequence")
        sequences[subunit] = values.pop()
    if pdb == "1BWV":
        expected_lsu = sequences["lsu"]
        expected_ssu = ("M" if construct.construct_id.endswith(".m1") else "V") + sequences["ssu"][1:]
        if sequences["ssu"][94] != "I":
            raise ValueError("pre-Amber original Gp source changes the I95 intervention")
        if construct.construct_id.startswith("gp.i95m."):
            expected_ssu = expected_ssu[:94] + "M" + expected_ssu[95:]
    else:
        if sequences["lsu"][414] != "P" or sequences["ssu"][97] != "V":
            raise ValueError("pre-Amber original Te source changes the declared background/intervention")
        expected_lsu = sequences["lsu"][:414] + "A" + sequences["lsu"][415:]
        expected_ssu = sequences["ssu"]
        if construct.construct_id.endswith(".v98m"):
            expected_ssu = expected_ssu[:97] + "M" + expected_ssu[98:]
    if (construct.lsu_sequence, construct.ssu_sequence) != (expected_lsu, expected_ssu):
        raise ValueError("pre-Amber selected construct adds an unnamed source intervention")
    declared = origin.get("complete_chains")
    if type(declared) is not list or len(declared) != 16 or any(type(actual) is not dict or any(actual.get(key) != value for key, value in selected.items()) for actual, selected in zip(declared, expected, strict=True)):
        raise ValueError("pre-Amber full genotype/source chain declaration differs")
    originals = _selected_originals(atoms, chains, joint_view_id)
    declared_originals = origin.get("selected_atom_origins")
    if type(declared_originals) is not list or len(declared_originals) != len(originals):
        raise ValueError("pre-Amber selected original atom denominator differs")
    declared_by_key = {}
    by_chain = {row["chain"]: row for row in expected}
    original_sequences = {selected["chain"]: observed.full_sequence for selected, observed in zip(expected, chains, strict=True)}
    for actual, selected in zip(declared_originals, originals.values(), strict=True):
        if type(actual) is not dict or set(actual) != set(selected) | {"model_component"} or any(actual.get(key) != value for key, value in selected.items()):
            raise ValueError("pre-Amber atom origin substitutes an independently reconstructed source token")
        chain = by_chain.get(selected["chain"])
        # This field belongs to the selected source intermediate, before the
        # declared processing/mutation intervention; it is not mutant evidence.
        if (chain and AMINO.get(actual["model_component"]) != original_sequences[selected["chain"]][selected["position"] - 1]
                or chain is None and actual["model_component"] != selected["source_component"]):
            raise ValueError("pre-Amber selected source origin changes its model component/genotype")
        declared_by_key[(selected["chain"], selected["position"], selected["atom"])] = actual
    serialized = read_serialized_heavy_pdb(heavy_text)
    heavy = serialized.atoms
    heavy_by_key = {(row["chain"], row["position"], row["atom"]): row for row in heavy}
    positions = {(row["chain"], position) for row in expected for position in range(1, len(row["sequence"]) + 1)}
    actual_positions = {(row["chain"], row["position"]) for row in heavy if row["chain"] in by_chain}
    if positions != actual_positions:
        raise ValueError("pre-Amber raw geometry omits a complete protein residue position")
    residue_names = {}
    for row in heavy:
        key = (row["chain"], row["position"])
        if key in residue_names and residue_names[key] != row["component"]:
            raise ValueError("pre-Amber raw geometry has conflicting residue components")
        residue_names[key] = row["component"]
        selected = by_chain.get(row["chain"])
        if selected and AMINO.get(row["component"]) != selected["sequence"][row["position"] - 1]:
            raise ValueError("pre-Amber raw geometry changes the full selected genotype")
        if selected is None and (row["chain"], row["position"], row["atom"]) not in originals:
            raise ValueError("pre-Amber raw geometry adds a non-source chemical atom")
    for actual, selected in zip(declared, expected, strict=True):
        names = [residue_names[(selected["chain"], position)] for position in range(1, len(selected["sequence"]) + 1)]
        if actual.get("actual_residue_names") != names:
            raise ValueError("pre-Amber declared actual residue names differ from original raw PDB")
    complete = origin.get("complete_heavy_atoms")
    if type(complete) is not list or len(complete) != len(heavy):
        raise ValueError("pre-Amber complete-heavy origin denominator differs")
    changed = {(selected["chain"], position) for selected, observed in zip(expected, chains, strict=True)
        for position, (target, original) in enumerate(zip(selected["sequence"], observed.full_sequence, strict=True), 1) if target != original}
    original_elements = {(row.pdb_id, row.operator_id, row.source_atom_id): row.element.upper() for row in atoms}
    inherited_count = 0
    for actual, raw in zip(complete, heavy, strict=True):
        key = (raw["chain"], raw["position"], raw["atom"])
        if type(actual) is not dict or any(actual.get(name) != raw[name] for name in ("chain", "position", "atom", "component")) or type(actual.get("element")) is not str or actual["element"].upper() != raw["element"]:
            raise ValueError("pre-Amber atom provenance differs from original raw atom identity")
        selected = originals.get(key)
        altered = key[:2] in changed and key[2] not in ("N", "CA", "C", "O", "OXT", "CB")
        inherited = selected is not None and not altered
        if inherited:
            given = actual.get("source_origin")
            if type(given) is not dict or set(given) != set(selected) | {"model_component"} or any(given.get(name) != value for name, value in selected.items()):
                raise ValueError("pre-Amber inherited atom substitutes authentic source tokens")
            if given != declared_by_key[key]:
                raise ValueError("pre-Amber inherited origin differs from its exact selected source declaration")
            if raw["element"] != original_elements[tuple(selected["source"])]:
                raise ValueError("pre-Amber inherited atom changes its deposited element")
            inherited_count += 1
        elif actual.get("source_origin") is not None:
            raise ValueError("pre-Amber constructed atom falsely inherits an observed source")
        if actual.get("status") != ("INHERITED_OBSERVED_SOURCE" if inherited else "DECLARED_CONSTRUCTED_MUTANT_OR_MISSING_ATOM"):
            raise ValueError("pre-Amber atom substitutes its inherited/constructed role")
    for key in originals:
        if key not in heavy_by_key and not (key[:2] in changed and key[2] not in ("N", "CA", "C", "O", "OXT", "CB")):
            raise ValueError("pre-Amber raw geometry drops an inherited original atom")
    declared_bonds = origin.get("authenticated_disulfides")
    if type(declared_bonds) is not list:
        raise ValueError("pre-Amber source disulfide declaration missing")
    declared_pairs = [tuple(sorted(tuple(partner) for partner in row["partners"])) for row in declared_bonds]
    if len(set(declared_pairs)) != len(declared_pairs) or set(declared_pairs) != expected_disulfides:
        raise ValueError("pre-Amber source disulfide declaration differs from original source")
    by_serial = {row["serial"]: row for row in heavy}
    actual_pairs = {tuple(sorted((by_serial[first]["chain"], by_serial[first]["position"]) for first in pair))
        for pair in serialized.directed_bonds if all(by_serial[first]["atom"] == "SG" for first in pair)}
    if actual_pairs != expected_disulfides:
        raise ValueError("pre-Amber raw SG bond references differ from source-named disulfides")
    return dict(atom_count=len(heavy), protein_residue_count=len(positions), residue_count=len(residue_names),
        inherited_atom_count=inherited_count, constructed_atom_count=len(heavy) - inherited_count,
        ter_count=len(serialized.ters), conect_row_count=len(serialized.conect_rows),
        directed_conect_term_count=len(serialized.directed_bonds), source_disulfide_count=len(expected_disulfides))


def assess(*, product_id, source, geometry_definition, geometry_completion,
           geometry_receipt, construct, joint_view_id, heavy_file, origin_file,
           heavy_bytes, origin_bytes, source_atoms, source_chains, expected_disulfides):
    """Assess authenticated two-file operands without any fictitious Amber data."""
    for evidence, raw in ((heavy_file, heavy_bytes), (origin_file, origin_bytes)):
        if type(raw) is not bytes or len(raw) != evidence.byte_count or sha256(raw).hexdigest() != evidence.sha256:
            raise ValueError("pre-Amber assessment raw bytes differ from genuine file evidence")
    counts = validate_geometry_origins(construct, joint_view_id, json.loads(origin_bytes),
        heavy_bytes.decode("ascii"), source_atoms, source_chains, expected_disulfides)
    return PreAmberGeometryIntegrity(product_id=product_id, source=source,
        geometry_definition=geometry_definition, geometry_completion=geometry_completion,
        geometry_receipt=geometry_receipt, construct=construct, joint_view_id=joint_view_id,
        heavy_file=heavy_file, origin_file=origin_file, **counts)
