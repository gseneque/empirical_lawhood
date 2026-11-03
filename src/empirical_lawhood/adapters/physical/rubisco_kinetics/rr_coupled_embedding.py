# SPDX-License-Identifier: MPL-2.0
"""Cold source-charge embedding proposal; no native Hamiltonian or execution.

The active-A backbone retains its parent charge witnesses. Changed full B
residues use same-chain ASN9/HID91 witnesses. Exact rational transfers remove
the five CA point charges and split each among its own N/C/HA. All environment
atoms, including those five zero-charge sites, remain in the derived census.
"""

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from fractions import Fraction
from hashlib import sha256
import json
from math import gcd

from .rr_coupled_preparation import (
    BACKBONE, PROTOCOL_SHA256, SIDECHAIN_POSITIONS, SOURCE_BINDINGS,
    CoreAtomV1, PreparedAtomV1, RrInitialContextV1,
)


MODEL_ID = 'rr-coupled-source-charge-embedding-proposal-v1'
MAXIMUM_FIELD_ATOMS = 14000
MAXIMUM_COORDINATE_ANGSTROM = Decimal('10000')
MAXIMUM_ABSOLUTE_POINT_CHARGE = Fraction(4)
CHARGE_SCALE = Fraction('18.2223')


@dataclass(frozen=True, slots=True)
class ExactChargeV1:
    numerator: int
    denominator: int
    decimal50: Decimal = field(init=False)

    def __post_init__(self):
        if (type(self.numerator) is not int or type(self.denominator) is not int
                or self.denominator <= 0 or gcd(self.numerator, self.denominator) != 1):
            raise ValueError('charge must be a canonical exact rational')
        with localcontext() as context:
            context.prec = 50
            context.rounding = ROUND_HALF_EVEN
            value = Decimal(self.numerator) / Decimal(self.denominator)
        object.__setattr__(self, 'decimal50', value)

    @classmethod
    def from_fraction(cls, value: Fraction):
        if type(value) is not Fraction:
            raise ValueError('exact Fraction charge required')
        return cls(value.numerator, value.denominator)

    def as_fraction(self) -> Fraction:
        return Fraction(self.numerator, self.denominator)


def redistribute_cut_charge(ca: ExactChargeV1, recipients: tuple[ExactChargeV1, ...]):
    """Return CA=0 and equal increments to exactly N/C/HA, conserving q."""
    if (type(ca) is not ExactChargeV1 or type(recipients) is not tuple
            or len(recipients) != 3 or any(type(q) is not ExactChargeV1 for q in recipients)):
        raise ValueError('cut requires one exact CA charge and three immutable recipients')
    increment = ca.as_fraction() / 3
    shifted = tuple(ExactChargeV1.from_fraction(q.as_fraction() + increment) for q in recipients)
    if sum((q.as_fraction() for q in shifted), Fraction()) != (
            ca.as_fraction() + sum((q.as_fraction() for q in recipients), Fraction())):
        raise ValueError('boundary charge conservation failed')
    return ExactChargeV1(0, 1), shifted


def _source_charge(atom: CoreAtomV1) -> ExactChargeV1:
    value = ExactChargeV1.from_fraction(Fraction(atom.native_tokens[8]) / CHARGE_SCALE)
    if value.decimal50 != Decimal(atom.native_tokens[9]):
        raise ValueError('native scaled token / Decimal50 charge witness differs')
    return value


@dataclass(frozen=True, slots=True)
class MMFieldAtomV1:
    atom: PreparedAtomV1
    source_charge_atom_index: int
    source_scaled_charge_token: str
    source_charge_decimal50: Decimal
    source_amber_atom_type: str
    source_atom_type_index: int
    source_mass_token: str
    assignment_role: str
    charge_before_boundary: ExactChargeV1
    field_charge: ExactChargeV1
    boundary_transfer_ids: tuple[str, ...]

    def __post_init__(self):
        if (type(self.atom) is not PreparedAtomV1
                or type(self.source_charge_atom_index) is not int or self.source_charge_atom_index < 1
                or type(self.source_atom_type_index) is not int or self.source_atom_type_index < 1
                or type(self.source_charge_decimal50) is not Decimal
                or not self.source_charge_decimal50.is_finite()
                or type(self.charge_before_boundary) is not ExactChargeV1
                or type(self.field_charge) is not ExactChargeV1
                or type(self.boundary_transfer_ids) is not tuple
                or any(type(v) is not str for v in self.boundary_transfer_ids)
                or any(type(v) is not str or not v for v in (
                    self.source_scaled_charge_token, self.source_amber_atom_type,
                    self.source_mass_token, self.assignment_role))
                or self.atom.component == 'CAP'
                or len(self.atom.coordinates) != 3
                or any(type(v) is not Decimal or not v.is_finite()
                       or abs(v) > MAXIMUM_COORDINATE_ANGSTROM for v in self.atom.coordinates)
                or abs(self.field_charge.as_fraction()) > MAXIMUM_ABSOLUTE_POINT_CHARGE):
            raise ValueError('invalid bounded immutable MM field row')
        if (ExactChargeV1.from_fraction(Fraction(self.source_scaled_charge_token) / CHARGE_SCALE)
                != self.charge_before_boundary
                or self.source_charge_decimal50 != self.charge_before_boundary.decimal50):
            raise ValueError('MM row source charge witnesses differ')


@dataclass(frozen=True, slots=True)
class ResidueChargeAssignmentV1:
    chain: str
    author_position: int
    target_component: str
    donor_author_position: int
    atom_joins: tuple[tuple[str, int], ...]

    def __post_init__(self):
        expected = 14 if self.target_component == 'ASN' else 17
        if (self.chain != 'B' or self.author_position not in (263, 287)
                or (self.target_component, self.donor_author_position) not in (('ASN', 9), ('HID', 91))
                or type(self.atom_joins) is not tuple or len(self.atom_joins) != expected
                or any(type(row) is not tuple or len(row) != 2 or type(row[0]) is not str
                       or not row[0] or type(row[1]) is not int or row[1] < 1 for row in self.atom_joins)
                or len({r[0] for r in self.atom_joins}) != expected
                or len({r[1] for r in self.atom_joins}) != expected):
            raise ValueError('complete immutable spectator donor assignment required')


@dataclass(frozen=True, slots=True)
class BoundaryTransferV1:
    identity: str
    author_position: int
    ca_atom_id: str
    recipient_atom_ids: tuple[str, str, str]
    ca_original_charge: ExactChargeV1
    equal_increment: ExactChargeV1

    def __post_init__(self):
        if (type(self.identity) is not str or not self.identity
                or type(self.author_position) is not int or self.author_position not in SIDECHAIN_POSITIONS
                or type(self.ca_atom_id) is not str or not self.ca_atom_id
                or type(self.recipient_atom_ids) is not tuple or len(self.recipient_atom_ids) != 3
                or any(type(v) is not str or not v for v in self.recipient_atom_ids)
                or len(set((self.ca_atom_id,) + self.recipient_atom_ids)) != 4
                or type(self.ca_original_charge) is not ExactChargeV1
                or type(self.equal_increment) is not ExactChargeV1
                or self.equal_increment.as_fraction() != self.ca_original_charge.as_fraction() / 3):
            raise ValueError('immutable distinct equal-share boundary transfer required')


def _nominal_source_formal_charge(source_atoms) -> int:
    """Declared component/terminus inventory, independent of partial q sums."""
    charged = {'ARG': 1, 'LYS': 1, 'ASP': -1, 'GLU': -1,
               'KCX': -1, 'RUB': -4, 'MG': 2}
    neutral = {'ALA', 'GLY', 'LEU', 'VAL', 'THR', 'PHE', 'ILE', 'PRO',
               'SER', 'TYR', 'ASN', 'GLN', 'MET', 'HIE', 'HID', 'TRP', 'CYS'}
    residues = {}
    for atom in source_atoms:
        residues.setdefault((atom.chain, atom.author_position), []).append(atom)
    if len(residues) != 920:
        raise ValueError('nominal source formal-charge residue census differs')
    q = 0
    for (chain, position), atoms in residues.items():
        labels = {a.component for a in atoms}
        if len(labels) != 1 or not labels <= (neutral | charged.keys()):
            raise ValueError('unknown native nominal component charge')
        q += charged.get(atoms[0].component, 0)
        names = {a.name for a in atoms}
        if position == 2:
            if atoms[0].component != 'ASP' or not {'N', 'H1', 'H2', 'H3'} <= names:
                raise ValueError('source N-terminal formal assignment differs')
            q += 1
        if position == 459:
            if atoms[0].component != 'ASP' or not {'C', 'O', 'OXT'} <= names:
                raise ValueError('source C-terminal formal assignment differs')
            q -= 1
    return q


@dataclass(frozen=True, slots=True)
class RrEmbeddingFieldV1:
    context: RrInitialContextV1
    field_atoms: tuple[MMFieldAtomV1, ...] = field(init=False)
    residue_assignments: tuple[ResidueChargeAssignmentV1, ...] = field(init=False)
    boundary_transfers: tuple[BoundaryTransferV1, ...] = field(init=False)
    source_excluded_parent_indices: tuple[int, ...] = field(init=False)
    real_qm_atom_ids: tuple[str, ...] = field(init=False)
    cap_atom_ids: tuple[str, ...] = field(init=False)
    source_bindings: tuple[tuple[str, int, str], ...] = field(init=False)
    source_core_charge: ExactChargeV1 = field(init=False)
    source_excluded_partial_charge: ExactChargeV1 = field(init=False)
    spectator_donor_charge_delta: ExactChargeV1 = field(init=False)
    mm_charge_before_boundary: ExactChargeV1 = field(init=False)
    mm_charge: ExactChargeV1 = field(init=False)
    hybrid_charge: ExactChargeV1 = field(init=False)
    nominal_source_formal_charge: int = field(init=False)
    nominal_context_formal_charge: int = field(init=False)
    hybrid_minus_nominal_formal_charge: ExactChargeV1 = field(init=False)
    decimal50_field_rounding_residual: ExactChargeV1 = field(init=False)
    binary64_field_rounding_residual: ExactChargeV1 = field(init=False)
    source_decimal50_rounding_residual: ExactChargeV1 = field(init=False)
    nonzero_charge_count: int = field(init=False)
    field_sha256: str = field(init=False)
    model_id: str = field(init=False, default=MODEL_ID)
    native_effects: int = field(init=False, default=0)
    executable_native_hamiltonian: bool = field(init=False, default=False)

    def __post_init__(self):
        c = self.context
        if type(c) is not RrInitialContextV1 or c.protocol_sha256 != PROTOCOL_SHA256:
            raise ValueError('exact typed frozen initial context required')
        if c.source.source_bindings != SOURCE_BINDINGS or c.executable_mm_hamiltonian:
            raise ValueError('source bindings or initial Hamiltonian scope differs')
        native = {a.index: a for a in c.source.atoms}
        groups = {}
        for atom in c.source.atoms:
            groups.setdefault((atom.chain, atom.author_position), {})[atom.name] = atom
        by_id = {a.atom_id: a for a in c.environment_atoms}
        real_qm = tuple(a.atom_id for a in c.quantum_atoms if a.component != 'CAP')
        caps = tuple(a.atom_id for a in c.quantum_atoms if a.component == 'CAP')
        if (len(by_id) != len(c.environment_atoms) or len(caps) != 5
                or set(by_id) & set(real_qm + caps)
                or set(by_id) | set(real_qm) != {a.atom_id for a in c.physical_atoms}
                or len(by_id) > MAXIMUM_FIELD_ATOMS):
            raise ValueError('complete disjoint QM/MM/cap census differs')
        targets = {}
        if c.variant == 'D263N':
            targets['B', 263] = ('ASN', 9)
        if c.variant == 'H287N':
            targets['B', 287] = ('ASN', 9)
        else:
            targets['B', 287] = ('HID', 91)
        assignments = []
        overrides = {}
        delta = Fraction()
        for (chain, position), (component, donor_position) in targets.items():
            donor = groups[chain, donor_position]
            target = {a.name: a for a in c.environment_atoms
                      if (a.chain, a.author_position) == (chain, position)}
            if (set(target) != set(donor) or any(a.component != component for a in target.values())
                    or any(a.element != donor[n].element for n, a in target.items())):
                raise ValueError('complete spectator residue/donor name join differs')
            joins = []
            for name, atom in target.items():
                overrides[atom.atom_id] = donor[name]
                joins.append((atom.atom_id, donor[name].index))
            assignments.append(ResidueChargeAssignmentV1(chain, position, component,
                                                          donor_position, tuple(joins)))
            delta += sum((_source_charge(a).as_fraction() for a in donor.values()), Fraction())
            delta -= sum((_source_charge(a).as_fraction() for a in groups[chain, position].values()), Fraction())
        witnesses = {}
        roles = {}
        before = {}
        for atom in c.environment_atoms:
            witness = overrides.get(atom.atom_id)
            if witness is not None:
                role = 'complete-same-chain-' + witness.component + str(witness.author_position) + '-donor'
            else:
                if atom.parent_atom_index not in native:
                    raise ValueError('MM atom lacks an exact parent/donor charge witness')
                witness = native[atom.parent_atom_index]
                if atom.name != witness.name or atom.element != witness.element:
                    raise ValueError('unchanged MM parent name/element join differs')
                role = ('active-A-fixed-parent-backbone' if atom.chain == 'A'
                        and atom.author_position in SIDECHAIN_POSITIONS else 'unchanged-parent')
            witnesses[atom.atom_id] = witness
            roles[atom.atom_id] = role
            before[atom.atom_id] = _source_charge(witness)
        after = dict(before)
        transfers = []
        transfer_ids = {key: () for key in by_id}
        for position in SIDECHAIN_POSITIONS:
            group = {a.name: a for a in c.environment_atoms
                     if a.chain == 'A' and a.author_position == position}
            if not {'CA', 'N', 'C', 'HA'} <= set(group) or not set(group) <= BACKBONE:
                raise ValueError('common active-A backbone/cut recipient census differs')
            ca = group['CA'].atom_id
            ids = tuple(group[n].atom_id for n in ('N', 'C', 'HA'))
            zero, shifted = redistribute_cut_charge(before[ca], tuple(before[key] for key in ids))
            after[ca] = zero
            after.update(zip(ids, shifted, strict=True))
            identity = f'CA-charge-shift:A:{position}:N-C-HA'
            for key in (ca,) + ids:
                if transfer_ids[key]:
                    raise ValueError('duplicate boundary charge recipient')
                transfer_ids[key] = (identity,)
            transfers.append(BoundaryTransferV1(identity, position, ca, ids, before[ca],
                ExactChargeV1.from_fraction(before[ca].as_fraction() / 3)))
        rows = tuple(MMFieldAtomV1(atom, witnesses[atom.atom_id].index,
            witnesses[atom.atom_id].native_tokens[8], Decimal(witnesses[atom.atom_id].native_tokens[9]),
            witnesses[atom.atom_id].native_tokens[5], witnesses[atom.atom_id].native_tokens[6],
            witnesses[atom.atom_id].native_tokens[7], roles[atom.atom_id], before[atom.atom_id],
            after[atom.atom_id], transfer_ids[atom.atom_id]) for atom in c.environment_atoms)
        source_qm = tuple(a for a in c.source.atoms if a.chain == 'A' and (
            a.component in ('RUB', 'MG') or a.author_position in SIDECHAIN_POSITIONS and a.name not in BACKBONE))
        core_q = sum((_source_charge(a).as_fraction() for a in c.source.atoms), Fraction())
        removed_q = sum((_source_charge(a).as_fraction() for a in source_qm), Fraction())
        mm_before = sum((q.as_fraction() for q in before.values()), Fraction())
        mm_after = sum((q.as_fraction() for q in after.values()), Fraction())
        if len(source_qm) != 76 or mm_before != core_q - removed_q + delta or mm_after != mm_before:
            raise ValueError('source deletion/donor/boundary charge conservation differs')
        expected = {'unedited-reference': (13752, -6), 'D263N': (13754, -5), 'H287N': (13749, -6)}
        if (len(rows), c.formal_quantum_charge) != expected[c.variant]:
            raise ValueError('whole-field/QM assigned context denominator differs')
        nominal_source = _nominal_source_formal_charge(c.source.atoms)
        if nominal_source != -30:
            raise ValueError('source nominal formal inventory differs')
        nominal = nominal_source + (2 if c.variant == 'D263N' else 0)
        hybrid = mm_after + c.formal_quantum_charge
        payload = {'model_id': MODEL_ID, 'source_bindings': SOURCE_BINDINGS,
            'variant': c.variant, 'field_atoms': [
                (r.atom.atom_id, r.atom.chain, r.atom.author_position, r.atom.component,
                 r.atom.name, r.atom.element, tuple(str(v) for v in r.atom.coordinates),
                 r.source_charge_atom_index, r.source_scaled_charge_token,
                 r.source_amber_atom_type, r.source_atom_type_index, r.assignment_role,
                 r.field_charge.numerator, r.field_charge.denominator, r.boundary_transfer_ids) for r in rows]}
        values = dict(field_atoms=rows, residue_assignments=tuple(assignments),
            boundary_transfers=tuple(transfers), source_excluded_parent_indices=tuple(a.index for a in source_qm),
            real_qm_atom_ids=real_qm, cap_atom_ids=caps, source_bindings=SOURCE_BINDINGS,
            source_core_charge=core_q, source_excluded_partial_charge=removed_q,
            spectator_donor_charge_delta=delta, mm_charge_before_boundary=mm_before,
            mm_charge=mm_after, hybrid_charge=hybrid, nominal_source_formal_charge=nominal_source,
            nominal_context_formal_charge=nominal,
            hybrid_minus_nominal_formal_charge=hybrid - nominal,
            decimal50_field_rounding_residual=sum((Fraction(r.field_charge.decimal50) for r in rows), Fraction()) - mm_after,
            binary64_field_rounding_residual=sum((Fraction.from_float(float(r.field_charge.decimal50)) for r in rows), Fraction()) - mm_after,
            source_decimal50_rounding_residual=sum((Fraction(Decimal(a.native_tokens[9])) for a in c.source.atoms), Fraction()) - core_q,
            nonzero_charge_count=sum(r.field_charge.numerator != 0 for r in rows),
            field_sha256=sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest())
        for name, value in values.items():
            object.__setattr__(self, name, ExactChargeV1.from_fraction(value) if type(value) is Fraction else value)


def derive_rr_embedding(context: RrInitialContextV1) -> RrEmbeddingFieldV1:
    return RrEmbeddingFieldV1(context)
