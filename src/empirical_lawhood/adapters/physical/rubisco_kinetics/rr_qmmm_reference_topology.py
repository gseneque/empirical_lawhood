# SPDX-License-Identifier: MPL-2.0
"""Cold source/index plan for reference V2; no constructed QM/MM Hamiltonian.

Existing authenticated preparation, field and original Amber source records
own admission. This module restores physical cut bonds, separates generated
links, and binds a complete spectator HID donor map. Native ParmEd/OpenMM/ASH
construction and missing donor angle/torsion extraction belong to a later
explicitly selected operation.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from hashlib import sha256
import json
from math import isfinite
from typing import ClassVar

from .rr_amber_nonbonded import (
    RrAmberNonbondedSourceV1,
    SOURCE_BYTES as PRMTOP_BYTES,
    SOURCE_MEMBER as PRMTOP_MEMBER,
    SOURCE_SHA256 as PRMTOP_SHA256,
)
from .rr_coupled_embedding import ExactChargeV1, RrEmbeddingFieldV1
from .rr_coupled_preparation import (
    BoundaryCapV1, CoreAtomV1, PreparedAtomV1, PROTOCOL_SHA256,
    RrInitialContextV1, SIDECHAIN_POSITIONS, SOURCE_BINDINGS,
)


PHOSPHATE_FIXED_NAMES = frozenset(("P1", "P2", "O1P", "O2P", "O3P", "O4P", "O5P", "O6P", "O1", "O5"))
HID_NAMES = frozenset("N H CA HA CB HB2 HB3 CG ND1 HD1 CE1 HE1 NE2 CD2 HD2 C O".split())
HIE_NAMES = (HID_NAMES - {"HD1"}) | {"HE2"}
PLAN_ID = "rr-reference-v2-qmmm-topology-index-plan-v1"
QM_LJ_TYPE_POLICY = "ORIGINAL_SOURCE_TYPES_INCLUDING_RELOCATED_HA_HB_AND_ACTIVE_HIS_H"
RUNTIME_SPLICE_REQUIREMENTS = (
    "authenticate-complete-original-prmtop-before-ParmEd-read",
    "extract-donor-internal-angle-and-dihedral-constants-and-native-multiplicity",
    "retain-target-peptide-backbone-and-explicitly-audit-external-boundary-terms",
    "splice-changed-local-HID-bonds-angles-dihedrals-from-B91-source-parameters",
    "reconcile-new-physical-graph-exclusions-and-one-four-scales-with-source-witnesses",
    "zero-QM-classical-particle-and-exception-charge-products-preserve-cross-LJ",
    "remove-wholly-QM-classical-terms-and-QM-QM-LJ-with-explicit-term-census",
    "generate-exactly-five-links-from-restored-cut-bonds-and-verify-expected-order-positions",
)


def _immutable_result(record) -> None:
    """Validate only the bounded immutable structure of this owner's records."""
    def check(value, depth=0):
        if depth > 8:
            raise ValueError("ordinary result immutable nesting bound exceeded")
        if type(value) is tuple:
            for member in value:
                check(member, depth+1)
        elif type(value) in (str, int, bool, type(None)):
            return
        elif type(value) is Decimal and value.is_finite():
            return
        elif type(value) is float and isfinite(value):
            return
        elif is_dataclass(value) and getattr(type(value), "__dataclass_params__").frozen:
            for member in fields(value):
                check(getattr(value, member.name), depth+1)
        else:
            raise ValueError("ordinary result must remain finite and deeply immutable")
    for member in fields(record):
        check(getattr(record, member.name))


def _pair(first: str, second: str) -> tuple[str, str]:
    if type(first) is not str or type(second) is not str or not first or not second or first == second:
        raise ValueError("distinct physical bond IDs required")
    return tuple(sorted((first, second)))  # type: ignore[return-value]


def _native_bonds(rows: tuple[tuple, ...]) -> dict[tuple[int, int], tuple]:
    if type(rows) is not tuple or len(rows) > 15000:
        raise ValueError("immutable source bond rows required")
    result = {}
    for row in rows:
        if type(row) is not tuple or len(row) != 9 or any(type(v) is not int or v < 1 for v in row[:3]) or any(type(v) is not str for v in row[3:]):
            raise ValueError("native source bond witness shape differs")
        key = tuple(sorted(row[:2]))
        try:
            encoded = tuple(int(v) for v in row[4:7])
            force, length = Decimal(row[7]), Decimal(row[8])
        except (ValueError, InvalidOperation) as exc:
            raise ValueError("native source bond lexical parameter differs") from exc
        if key[0] == key[1] or key in result or encoded != (3*(row[0]-1), 3*(row[1]-1), row[2]):
            raise ValueError("native source bond index/parameter join differs")
        if row[3] not in ("BONDS_INC_HYDROGEN", "BONDS_WITHOUT_HYDROGEN") or not force.is_finite() or not length.is_finite() or force <= 0 or length <= 0:
            raise ValueError("native source bond lexical parameter differs")
        result[key] = row
    return result


@dataclass(frozen=True, slots=True)
class ReferenceIndexMapV1:
    full_physical_ids: tuple[str, ...]
    real_qm_ids: tuple[str, ...]
    real_qm_full_indices_0based: tuple[int, ...]
    mobile_real_qm_ids: tuple[str, ...]
    mobile_full_indices_0based: tuple[int, ...]
    fixed_real_qm_ids: tuple[str, ...]
    fixed_full_indices_0based: tuple[int, ...]
    mm_ids: tuple[str, ...]
    mm_full_indices_0based: tuple[int, ...]
    generated_link_ids: tuple[str, ...]
    generated_link_quantum_indices_0based: tuple[int, ...]
    restored_cut_pairs: tuple[tuple[str, str], ...]
    physical_bonds: tuple[tuple[str, str], ...]

    def __post_init__(self):
        _immutable_result(self)
        ids = self.full_physical_ids
        full_set = set(ids)
        if not ids or len(set(ids)) != len(ids) or any(type(v) is not str or not v for v in ids):
            raise ValueError("unique ordered full physical IDs required")
        for names, indices in ((self.real_qm_ids, self.real_qm_full_indices_0based), (self.mobile_real_qm_ids, self.mobile_full_indices_0based), (self.fixed_real_qm_ids, self.fixed_full_indices_0based), (self.mm_ids, self.mm_full_indices_0based)):
            if len(names) != len(indices) or len(set(names)) != len(names) or any(type(i) is not int or not 0 <= i < len(ids) for i in indices) or tuple(ids[i] for i in indices) != names:
                raise ValueError("physical/QM/MM ordered index bijection differs")
        if set(self.real_qm_ids) & set(self.mm_ids) or set(self.real_qm_ids) | set(self.mm_ids) != set(ids) or set(self.mobile_real_qm_ids) & set(self.fixed_real_qm_ids) or set(self.mobile_real_qm_ids) | set(self.fixed_real_qm_ids) != set(self.real_qm_ids):
            raise ValueError("complete disjoint physical/QM/mobile census differs")
        if len(set(self.generated_link_ids)) != len(self.generated_link_ids) or set(self.generated_link_ids) & set(ids) or self.generated_link_quantum_indices_0based != tuple(range(len(self.real_qm_ids), len(self.real_qm_ids)+len(self.generated_link_ids))):
            raise ValueError("generated links must be disjoint and appended exactly once")
        if tuple(sorted(set(self.physical_bonds))) != self.physical_bonds or any(len(pair) != 2 or _pair(*pair) != pair or not set(pair) <= full_set for pair in self.physical_bonds):
            raise ValueError("physical bond graph includes links or ambiguous edges")
        if len(set(self.restored_cut_pairs)) != len(self.restored_cut_pairs) or any(pair not in self.physical_bonds for pair in self.restored_cut_pairs):
            raise ValueError("declared physical cut bonds are not restored uniquely")


def derive_reference_indices(physical_atoms: tuple[PreparedAtomV1, ...], quantum_atoms: tuple[PreparedAtomV1, ...], candidate_bonds: tuple[tuple[str, str], ...], caps: tuple[BoundaryCapV1, ...]) -> ReferenceIndexMapV1:
    """Pure bounded role/index arithmetic; standalone results confer no admission."""
    if any(type(rows) is not tuple for rows in (physical_atoms, quantum_atoms, candidate_bonds, caps)) or any(type(a) is not PreparedAtomV1 for a in physical_atoms+quantum_atoms) or any(type(c) is not BoundaryCapV1 for c in caps):
        raise ValueError("immutable typed preparation atoms/caps required")
    full = tuple(a.atom_id for a in physical_atoms)
    positions = {atom_id: i for i, atom_id in enumerate(full)}
    if len(positions) != len(full) or len(full) > 14000:
        raise ValueError("physical atom roster is duplicate or overbound")
    cap_ids = tuple(c.cap_atom_id for c in caps)
    real = tuple(a.atom_id for a in quantum_atoms if a.component != "CAP")
    links = tuple(a.atom_id for a in quantum_atoms if a.component == "CAP")
    if links != cap_ids or any(i not in positions for i in real) or len(set(a.atom_id for a in quantum_atoms)) != len(quantum_atoms):
        raise ValueError("real QM/generated-link inventory differs")
    physical_by_id = {a.atom_id: a for a in physical_atoms}
    if any(a != physical_by_id[a.atom_id] for a in quantum_atoms if a.component != "CAP"):
        raise ValueError("real QM atom does not match physical source operand")
    graph = set()
    adjacency = {atom_id: set() for atom_id in full+cap_ids}
    allowed_ids = set(adjacency)
    real_set = set(real)
    for row in candidate_bonds:
        if type(row) is not tuple or len(row) != 2 or _pair(*row) != row or row in graph or not set(row) <= allowed_ids:
            raise ValueError("complete candidate graph has invalid/duplicate membership")
        graph.add(row)
        for first, second in (row, row[::-1]):
            adjacency[first].add(second)
    cuts = []
    for cap in caps:
        link_bond = _pair(cap.cap_atom_id, cap.quantum_cb_atom_id)
        cut = _pair(cap.quantum_cb_atom_id, cap.environment_ca_atom_id)
        if cap.quantum_cb_atom_id not in real or cap.environment_ca_atom_id not in positions or cap.environment_ca_atom_id in real or adjacency[cap.cap_atom_id] != {cap.quantum_cb_atom_id} or link_bond not in graph or cut in graph:
            raise ValueError("generated cap or original CA-CB cut mapping differs")
        if (physical_by_id[cap.quantum_cb_atom_id].name, physical_by_id[cap.environment_ca_atom_id].name) != ("CB", "CA"):
            raise ValueError("restored cut must join the declared native CA and CB")
        graph.remove(link_bond)
        graph.add(cut)
        cuts.append(cut)
    fixed = set()
    for atom in quantum_atoms:
        if atom.component == "CAP":
            continue
        if atom.element == "Mg" or atom.component == "RUB" and atom.name in PHOSPHATE_FIXED_NAMES:
            fixed.add(atom.atom_id)
        if atom.name == "CB" and atom.component != "RUB":
            fixed.add(atom.atom_id)
            fixed.update(i for i in adjacency[atom.atom_id] if i in physical_by_id and physical_by_id[i].element == "H" and i in real_set)
    fixed_ids = tuple(i for i in real if i in fixed)
    mobile = tuple(i for i in real if i not in fixed)
    mm = tuple(i for i in full if i not in real_set)
    return ReferenceIndexMapV1(full, real, tuple(positions[i] for i in real), mobile, tuple(positions[i] for i in mobile), fixed_ids, tuple(positions[i] for i in fixed_ids), mm, tuple(positions[i] for i in mm), links, tuple(range(len(real), len(real)+len(links))), tuple(cuts), tuple(sorted(graph)))


@dataclass(frozen=True, slots=True)
class SpectatorDonorAtomV1:
    target_physical_id: str
    target_native_atom_index_1based: int
    target_previous_native_name: str
    target_prepared_name: str
    donor_native_atom_index_1based: int
    donor_native_tokens: tuple

    def __post_init__(self):
        _immutable_result(self)
        if self.target_physical_id != f"amber:{self.target_native_atom_index_1based}" or type(self.target_native_atom_index_1based) is not int or self.target_native_atom_index_1based < 1 or type(self.donor_native_atom_index_1based) is not int or self.donor_native_atom_index_1based < 1 or len(self.donor_native_tokens) != 15 or self.donor_native_tokens[0] != self.donor_native_atom_index_1based or self.donor_native_tokens[2] != self.target_prepared_name:
            raise ValueError("complete donor atom identity/source row differs")


@dataclass(frozen=True, slots=True)
class SpectatorHidSpliceV1:
    target_chain: str
    target_author_position: int
    donor_author_position: int
    atom_joins: tuple[SpectatorDonorAtomV1, ...]
    donor_internal_bond_witnesses: tuple[tuple, ...]
    donor_external_bond_witnesses: tuple[tuple, ...]
    target_original_external_bond_witnesses: tuple[tuple, ...]
    target_prepared_external_bonds: tuple[tuple[str, str], ...]
    target_original_internal_bonds: tuple[tuple[str, str], ...]
    target_prepared_internal_bonds: tuple[tuple[str, str], ...]
    donor_internal_bonds_mapped_to_target: tuple[tuple[str, str], ...]
    removed_target_bonds: tuple[tuple[str, str], ...]
    added_target_bonds: tuple[tuple[str, str], ...]
    original_source_partial_charge: ExactChargeV1
    assigned_donor_partial_charge: ExactChargeV1
    bonded_parameter_splice_complete: bool = field(init=False, default=False)

    def __post_init__(self):
        _immutable_result(self)
        if (self.target_chain, self.target_author_position, self.donor_author_position) != ("B", 287, 91) or len(self.atom_joins) != 17 or any(type(v) is not SpectatorDonorAtomV1 for v in self.atom_joins) or {v.target_prepared_name for v in self.atom_joins} != HID_NAMES or len({v.target_physical_id for v in self.atom_joins}) != 17 or len({v.donor_native_atom_index_1based for v in self.atom_joins}) != 17:
            raise ValueError("complete B287/HID91 donor roster required")
        if self.donor_internal_bonds_mapped_to_target != self.target_prepared_internal_bonds:
            raise ValueError("HID donor graph does not match target completed graph")
        expected_external = tuple(sorted(_pair(f"amber:{row[0]}", f"amber:{row[1]}") for row in self.target_original_external_bond_witnesses))
        if self.target_prepared_external_bonds != expected_external:
            raise ValueError("spectator peptide-backbone external bonds must remain unchanged")
        if self.removed_target_bonds != tuple(sorted(set(self.target_original_internal_bonds)-set(self.target_prepared_internal_bonds))) or self.added_target_bonds != tuple(sorted(set(self.target_prepared_internal_bonds)-set(self.target_original_internal_bonds))):
            raise ValueError("HIE-to-HID physical bond edit census differs")


def derive_spectator_hid_splice(source_atoms: tuple[CoreAtomV1, ...], native_bond_rows: tuple[tuple, ...], physical_atoms: tuple[PreparedAtomV1, ...], physical_bonds: tuple[tuple[str, str], ...]) -> SpectatorHidSpliceV1:
    """Join complete native donor atoms/bonds; missing angles/torsions stay missing."""
    if any(type(v) is not tuple for v in (source_atoms, physical_atoms, physical_bonds)) or any(type(a) is not CoreAtomV1 for a in source_atoms) or any(type(a) is not PreparedAtomV1 for a in physical_atoms):
        raise ValueError("typed immutable source and physical atoms required")
    native = _native_bonds(native_bond_rows)
    source_indices = {a.index for a in source_atoms}
    if len(source_indices) != len(source_atoms) or any(not set(pair) <= source_indices for pair in native):
        raise ValueError("native source graph has duplicate or absent atom membership")
    target_old = {a.name: a for a in source_atoms if (a.chain, a.author_position) == ("B", 287)}
    donor = {a.name: a for a in source_atoms if (a.chain, a.author_position) == ("B", 91)}
    target = {a.name: a for a in physical_atoms if (a.chain, a.author_position) == ("B", 287)}
    if any(len(group) != len([a for a in atoms if (a.chain, a.author_position) == ("B", position)]) for group, atoms, position in ((target_old, source_atoms, 287), (donor, source_atoms, 91), (target, physical_atoms, 287))):
        raise ValueError("ambiguous spectator/donor native atom-name roster")
    if set(target_old) != HIE_NAMES or set(donor) != HID_NAMES or set(target) != HID_NAMES or any(a.component != "HIE" for a in target_old.values()) or any(a.component != "HID" for a in donor.values()) or any(a.component != "HID" for a in target.values()):
        raise ValueError("complete native HIE target and HID donor inventories differ")
    old_by_index = {a.index: a for a in target_old.values()}
    donor_indices = {a.index for a in donor.values()}
    target_ids = {a.atom_id for a in target.values()}
    if target_ids != {f"amber:{a.index}" for a in target_old.values()}:
        raise ValueError("spectator tautomer must preserve all original physical nuclei")
    joins = []
    for atom in physical_atoms:
        if atom.atom_id not in target_ids:
            continue
        old = old_by_index.get(atom.parent_atom_index)
        witness = donor[atom.name]
        if old is None or atom.atom_id != f"amber:{old.index}" or atom.element != witness.element or old.name != ("HE2" if atom.name == "HD1" else atom.name):
            raise ValueError("spectator donor element/physical-H lineage differs")
        joins.append(SpectatorDonorAtomV1(atom.atom_id, old.index, old.name, atom.name, witness.index, witness.native_tokens))
    donor_to_target = {v.donor_native_atom_index_1based: v.target_physical_id for v in joins}
    internal = tuple(row for pair, row in native.items() if set(pair) <= donor_indices)
    external = tuple(row for pair, row in native.items() if bool(set(pair) & donor_indices) and not set(pair) <= donor_indices)
    mapped = tuple(sorted(_pair(donor_to_target[r[0]], donor_to_target[r[1]]) for r in internal))
    old_ids = {a.index for a in target_old.values()}
    old_bonds = tuple(sorted(_pair(f"amber:{pair[0]}", f"amber:{pair[1]}") for pair in native if set(pair) <= old_ids))
    new_bonds = tuple(sorted(pair for pair in physical_bonds if set(pair) <= target_ids))
    old_external = tuple(row for pair, row in native.items() if bool(set(pair) & old_ids) and not set(pair) <= old_ids)
    new_external = tuple(sorted(pair for pair in physical_bonds if bool(set(pair) & target_ids) and not set(pair) <= target_ids))
    old_charge = sum((Fraction(a.native_tokens[8])/Fraction("18.2223") for a in target_old.values()), Fraction())
    donor_charge = sum((Fraction(a.native_tokens[8])/Fraction("18.2223") for a in donor.values()), Fraction())
    return SpectatorHidSpliceV1("B", 287, 91, tuple(joins), internal, external, old_external, new_external, old_bonds, new_bonds, mapped, tuple(sorted(set(old_bonds)-set(new_bonds))), tuple(sorted(set(new_bonds)-set(old_bonds))), ExactChargeV1.from_fraction(old_charge), ExactChargeV1.from_fraction(donor_charge))


@dataclass(frozen=True, slots=True)
class ReferencePhysicalParameterV1:
    physical_id: str
    physical_index_0based: int
    original_source_index_1based: int
    parameter_source_index_1based: int
    native_atom_type: str
    native_type_index_1based: int
    native_mass_token: str
    native_scaled_charge_token: str
    classical_charge: ExactChargeV1
    assignment_role: str

    def __post_init__(self):
        _immutable_result(self)
        if any(type(v) is not int for v in (self.physical_index_0based, self.original_source_index_1based, self.parameter_source_index_1based, self.native_type_index_1based)) or self.physical_id != f"amber:{self.original_source_index_1based}" or self.physical_index_0based != self.original_source_index_1based-1 or not 1 <= self.parameter_source_index_1based <= 13828 or not 1 <= self.native_type_index_1based <= 256 or type(self.classical_charge) is not ExactChargeV1:
            raise ValueError("physical/source parameter row index differs")


@dataclass(frozen=True, slots=True)
class RrReferenceTopologyPlanV1:
    context: RrInitialContextV1 = field(repr=False)
    embedding: RrEmbeddingFieldV1 = field(repr=False)
    original_nonbonded: RrAmberNonbondedSourceV1 = field(repr=False)
    index_map: ReferenceIndexMapV1 = field(init=False)
    physical_parameters: tuple[ReferencePhysicalParameterV1, ...] = field(init=False)
    spectator_splice: SpectatorHidSpliceV1 = field(init=False)
    removed_original_physical_bonds: tuple[tuple[str, str], ...] = field(init=False)
    added_prepared_physical_bonds: tuple[tuple[str, str], ...] = field(init=False)
    source_bindings: tuple[tuple[str, int, str], ...] = field(init=False)
    full_prmtop_binding: tuple[str, int, str] = field(init=False)
    prmtop_chunk_bindings: tuple[tuple[int, int, str], ...] = field(init=False)
    field_sha256: str = field(init=False)
    plan_id: str = field(init=False, default=PLAN_ID)
    qm_lj_type_policy: str = field(init=False, default=QM_LJ_TYPE_POLICY)
    runtime_splice_requirements: tuple[str, ...] = field(init=False, default=RUNTIME_SPLICE_REQUIREMENTS)
    bonded_parameter_splice_complete: bool = field(init=False, default=False)
    executable_native_hamiltonian: bool = field(init=False, default=False)
    native_effects: int = field(init=False, default=0)
    CLAIM_SCOPE: ClassVar[str] = "SOURCE_BOUND_REFERENCE_INDEX_PLAN_NOT_CONSTRUCTED_OR_ASSAY_MAPPED_HAMILTONIAN"

    def __post_init__(self):
        c, f, source = self.context, self.embedding, self.original_nonbonded
        if type(c) is not RrInitialContextV1 or type(f) is not RrEmbeddingFieldV1 or type(source) is not RrAmberNonbondedSourceV1 or f.context is not c:
            raise ValueError("exact existing typed context/field/original-source join required")
        if (c.variant, c.proton_view, c.protocol_sha256) != ("unedited-reference", "V2", PROTOCOL_SHA256) or c.source.source_bindings != SOURCE_BINDINGS or f.source_bindings != SOURCE_BINDINGS:
            raise ValueError("reference-V2 preparation/source scope differs")
        p = source.projection
        if (p.source_member, p.source_bytes, p.source_sha256, len(p.selected_atoms)) != (PRMTOP_MEMBER, PRMTOP_BYTES, PRMTOP_SHA256, 13828):
            raise ValueError("original keto prmtop source role differs")
        indices = derive_reference_indices(c.physical_atoms, c.quantum_atoms, c.candidate_bonds, c.caps)
        if indices.full_physical_ids != tuple(f"amber:{i}" for i in range(1, 13829)) or (len(indices.real_qm_ids), len(indices.mobile_real_qm_ids), len(indices.fixed_real_qm_ids), len(indices.mm_ids), len(indices.generated_link_ids)) != (76, 50, 26, 13752, 5) or tuple(cap.author_position for cap in c.caps) != SIDECHAIN_POSITIONS:
            raise ValueError("complete reference physical/QM/mobile/link denominator differs")
        native = {a.index: a for a in c.source.atoms}
        for row in p.selected_atoms:
            atom = native[row.atom_index_1based]
            if (row.native_name, row.native_amber_type, row.type_index_1based) != (atom.name, atom.native_tokens[5], atom.native_tokens[6]):
                raise ValueError("original core/prmtop type-index correspondence differs")
        splice = derive_spectator_hid_splice(c.source.atoms, c.source.native_bond_rows, c.physical_atoms, indices.physical_bonds)
        assigned = {row.atom.atom_id: row for row in f.field_atoms}
        donor_map = {row.target_physical_id: row.donor_native_atom_index_1based for row in splice.atom_joins}
        if tuple(row.atom.atom_id for row in f.field_atoms) != indices.mm_ids:
            raise ValueError("whole held field order differs from classical topology")
        parameters = []
        for index, atom in enumerate(c.physical_atoms):
            if atom.parent_atom_index not in native or atom.atom_id != f"amber:{atom.parent_atom_index}":
                raise ValueError("reference physical nucleus lacks original source identity")
            if atom.atom_id in assigned:
                row = assigned[atom.atom_id]
                witness = native[row.source_charge_atom_index]
                if atom.atom_id in donor_map and row.source_charge_atom_index != donor_map[atom.atom_id]:
                    raise ValueError("spectator field/source donor mapping differs")
                charge, role = row.field_charge, row.assignment_role
            else:
                witness = native[atom.parent_atom_index]
                charge, role = ExactChargeV1(0, 1), "real-QM-zero-classical-charge-fixed-original-LJ-type"
            parameters.append(ReferencePhysicalParameterV1(atom.atom_id, index, atom.parent_atom_index, witness.index, witness.native_tokens[5], witness.native_tokens[6], witness.native_tokens[7], witness.native_tokens[8], charge, role))
        original_graph = {_pair(f"amber:{r[0]}", f"amber:{r[1]}") for r in c.source.native_bond_rows}
        prepared_graph = set(indices.physical_bonds)
        values = dict(index_map=indices, physical_parameters=tuple(parameters), spectator_splice=splice,
            removed_original_physical_bonds=tuple(sorted(original_graph-prepared_graph)), added_prepared_physical_bonds=tuple(sorted(prepared_graph-original_graph)),
            source_bindings=SOURCE_BINDINGS, full_prmtop_binding=(PRMTOP_MEMBER, PRMTOP_BYTES, PRMTOP_SHA256), prmtop_chunk_bindings=source.chunk_bindings, field_sha256=f.field_sha256)
        for name, value in values.items():
            object.__setattr__(self, name, value)

    def native_manifest(self) -> dict:
        """Ordinary copied operand projection, never native Hamiltonian authority."""
        index = {atom_id: i for i, atom_id in enumerate(self.index_map.full_physical_ids)}
        quantum = {a.atom_id: a for a in self.context.quantum_atoms}
        return {
            "manifest_kind": "DEVELOPMENT_REFERENCE_INDEX_PLAN",
            "plan_id": self.plan_id,
            "context_variant": "unedited-reference", "proton_view": "V2",
            "source_bindings": self.source_bindings,
            "original_prmtop_binding": self.full_prmtop_binding,
            "original_prmtop_chunk_bindings": self.prmtop_chunk_bindings,
            "field_sha256": self.field_sha256,
            "physical_atom_columns": ("physical_id", "element", "coordinates_angstrom", "chain", "author_position", "component", "name"),
            "physical_atoms": tuple((a.atom_id, a.element, tuple(str(v) for v in a.coordinates), a.chain, a.author_position, a.component, a.name) for a in self.context.physical_atoms),
            "real_qm_full_indices_0based": self.index_map.real_qm_full_indices_0based,
            "active_full_indices_0based": self.index_map.mobile_full_indices_0based,
            "fixed_real_qm_full_indices_0based": self.index_map.fixed_full_indices_0based,
            "fixed_mm_full_indices_0based": self.index_map.mm_full_indices_0based,
            "generated_link_columns": ("physical_id", "quantum_index_0based", "cb_full_index_0based", "ca_full_index_0based", "held_coordinates_angstrom"),
            "generated_links": tuple((cap.cap_atom_id, self.index_map.generated_link_quantum_indices_0based[i], index[cap.quantum_cb_atom_id], index[cap.environment_ca_atom_id], tuple(str(v) for v in quantum[cap.cap_atom_id].coordinates)) for i, cap in enumerate(self.context.caps)),
            "classical_charge_fractions": tuple((r.classical_charge.numerator, r.classical_charge.denominator) for r in self.physical_parameters),
            "physical_parameter_columns": ("physical_id", "original_source_index_1based", "parameter_source_index_1based", "native_atom_type", "native_type_index_1based", "native_mass_token", "native_scaled_charge_token", "assignment_role"),
            "physical_parameters": tuple((r.physical_id, r.original_source_index_1based, r.parameter_source_index_1based, r.native_atom_type, r.native_type_index_1based, r.native_mass_token, r.native_scaled_charge_token, r.assignment_role) for r in self.physical_parameters),
            "spectator_atom_join_columns": ("target_full_index_0based", "donor_source_index_1based", "target_name", "previous_native_name"),
            "spectator_atom_joins": tuple((index[r.target_physical_id], r.donor_native_atom_index_1based, r.target_prepared_name, r.target_previous_native_name) for r in self.spectator_splice.atom_joins),
            "spectator_donor_internal_bond_witnesses": self.spectator_splice.donor_internal_bond_witnesses,
            "spectator_donor_external_bond_witnesses": self.spectator_splice.donor_external_bond_witnesses,
            "spectator_target_original_external_bond_witnesses": self.spectator_splice.target_original_external_bond_witnesses,
            "spectator_target_prepared_external_bonds": self.spectator_splice.target_prepared_external_bonds,
            "physical_bonds_full_indices_0based": tuple(tuple(index[i] for i in pair) for pair in self.index_map.physical_bonds),
            "source_original_dihedral14_columns": ("flag", "row_1based", "native_tokens", "native_scee_token", "native_scnb_token", "source_14_enabled"),
            "source_original_dihedral14_rows": tuple((r.native_flag, r.native_row_1based, r.native_tokens, r.native_scee_token, r.native_scnb_token, r.source_14_enabled) for r in self.original_nonbonded.projection.selected_dihedrals),
            "qm_lj_type_policy": self.qm_lj_type_policy,
            "runtime_splice_requirements": self.runtime_splice_requirements,
            "bonded_parameter_splice_complete": False,
            "executable_native_hamiltonian": False,
            "native_effects": 0,
        }

    @property
    def manifest_sha256(self) -> str:
        raw = (json.dumps(self.native_manifest(), sort_keys=True, separators=(",", ":"), allow_nan=False)+"\n").encode()
        return sha256(raw).hexdigest()


def derive_rr_reference_topology(context: RrInitialContextV1, embedding: RrEmbeddingFieldV1, original_nonbonded: RrAmberNonbondedSourceV1) -> RrReferenceTopologyPlanV1:
    return RrReferenceTopologyPlanV1(context, embedding, original_nonbonded)
