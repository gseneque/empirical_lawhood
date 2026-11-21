# SPDX-License-Identifier: MPL-2.0
"""Explicit finite endpoint changes; no infinitesimal mutation approximation."""

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_decimal, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.materials import RubiscoPairedCase, exact, identities
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_atoms import MolecularRepresentation, indices


@dataclass(frozen=True, slots=True)
class AtomicTransformation(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/atomic-transformation"
    transformation_id: str
    before: ObjectIdentity
    after: ObjectIdentity
    kind: str
    case: ObjectIdentity | None
    common_atoms: tuple[tuple[int, int], ...]
    removed_atom_indices: tuple[int, ...]
    added_atom_indices: tuple[int, ...]
    changed_parameter_pairs: tuple[tuple[int, int], ...]
    # Bonds use their own endpoint's native atom order; order changes retain both.
    # None explicitly retains an unannotated native topology edge, not order one.
    removed_bonds: tuple[tuple[int, int, Decimal | None], ...]
    added_bonds: tuple[tuple[int, int, Decimal | None], ...]
    changed_site_ids: tuple[str, ...]
    protocol: ObjectIdentity
    sources: tuple[ObjectIdentity, ...]
    interpretation: str = "FINITE_ENDPOINT_CORRESPONDENCE_NOT_OVERLAP_OR_CHEMICAL_ADMISSION"

    def __post_init__(self):
        validate_stable_id(self.transformation_id)
        for row in (self.before, self.after, self.protocol):
            exact(row, ObjectIdentity)
        identities(self.sources)
        if self.kind not in {"FINITE_SEQUENCE_SUBSTITUTION", "CHEMICAL_STATE_TRANSFORMATION"}:
            raise ValueError("atomic transformation needs an explicit finite intervention kind")
        if (self.kind == "FINITE_SEQUENCE_SUBSTITUTION") != (self.case is not None):
            raise ValueError("finite sequence transformation requires its exact paired case")
        if self.case is not None:
            exact(self.case, ObjectIdentity)
        for pairs in (self.common_atoms, self.changed_parameter_pairs):
            if (type(pairs) is not tuple or any(type(row) is not tuple or len(row) != 2
                    or any(type(value) is not int or value < 0 for value in row) for row in pairs)
                    or tuple(sorted(set(pairs))) != pairs
                    or len({row[0] for row in pairs}) != len(pairs)
                    or len({row[1] for row in pairs}) != len(pairs)):
                raise ValueError("common atom mapping must be an exact one-to-one index relation")
        if not set(self.changed_parameter_pairs).issubset(self.common_atoms):
            raise ValueError("changed parameter pair is outside the common atom census")
        for values in (self.removed_atom_indices, self.added_atom_indices):
            if (type(values) is not tuple or tuple(sorted(set(values))) != values
                    or any(type(value) is not int or value < 0 for value in values)):
                raise ValueError("atomic transformation needs all added and removed atom indices")
        for rows in (self.removed_bonds, self.added_bonds):
            if (type(rows) is not tuple or any(type(row) is not tuple or len(row) != 3 for row in rows)
                    or tuple((row[0], row[1]) for row in rows) != tuple(sorted({(row[0], row[1]) for row in rows}))):
                raise ValueError("transformation needs a complete sorted bond-change census")
            for first, second, order in rows:
                if (type(first) is not int or type(second) is not int or not 0 <= first < second
                        or order is not None and (type(order) is not Decimal or not order.is_finite() or order <= 0)):
                    raise ValueError("transformed bond indices/order are invalid")
                if order is not None:
                    validate_decimal(order, field_name="transformed bond order")
        if type(self.changed_site_ids) is not tuple or tuple(sorted(set(self.changed_site_ids))) != self.changed_site_ids:
            raise ValueError("transformation needs a complete site-change census")
        for value in self.changed_site_ids:
            validate_stable_id(value)
        if self.protocol not in self.sources:
            raise ValueError("transformation omits its selected protocol source")
        if self.interpretation != "FINITE_ENDPOINT_CORRESPONDENCE_NOT_OVERLAP_OR_CHEMICAL_ADMISSION":
            raise ValueError("atom correspondence does not establish physical path overlap or chemistry")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.transformation_id, self)


def _parameter(atom):
    return atom.mass_dalton, atom.charge_electron, atom.parameter_type


def derive_atomic_transformation(before, after, *, transformation_id, kind,
                                 common_atoms, protocol, sources, case=None):
    """Derive every finite atom, parameter, bond and site change independently.

    The caller selects the common atoms explicitly. Equality of native indices
    or seeds is never used as evidence for correspondence. Same residue/name/
    element is mandatory for each selected common atom. Different elements,
    including ILE carbon versus MET sulfur, remain removal/addition events.
    """
    for record in (before, after):
        exact(record, MolecularRepresentation)
    if (before.preparation_protocol != after.preparation_protocol
            or before.parameter_model != after.parameter_model
            or before.temperature_k != after.temperature_k):
        raise ValueError("paired endpoint preparation protocol, parameter alternative or temperature differs")
    if kind == "FINITE_SEQUENCE_SUBSTITUTION":
        exact(case, RubiscoPairedCase)
        if (before.material != case.parent or after.material != case.mutant
                or before.chemistry != after.chemistry):
            raise ValueError("finite atomic endpoints change the selected case or matched all-site chemistry")
    elif kind == "CHEMICAL_STATE_TRANSFORMATION":
        if case is not None or before.material != after.material:
            raise ValueError("chemical transformation cannot conceal a sequence intervention")
    else:
        raise ValueError("unknown atomic transformation kind")
    if type(common_atoms) is not tuple or any(type(row) is not tuple or len(row) != 2 for row in common_atoms):
        raise ValueError("common atom mapping needs exact immutable index pairs")
    left = tuple(row[0] for row in common_atoms)
    right = tuple(row[1] for row in common_atoms)
    indices(left, count=len(before.atoms), name="before common atoms")
    indices(tuple(sorted(right)), count=len(after.atoms), name="after common atoms")
    for first, second in common_atoms:
        a, b = before.atoms[first], after.atoms[second]
        if (a.residue_id, a.name, a.atomic_number) != (b.residue_id, b.name, b.atomic_number):
            raise ValueError("common atom map changes residue, atom name or physical element")
    by_after_key = {(atom.residue_id, atom.name, atom.atomic_number): i for i, atom in enumerate(after.atoms)}
    complete_common = tuple((i, by_after_key[key]) for i, atom in enumerate(before.atoms)
        if (key := (atom.residue_id, atom.name, atom.atomic_number)) in by_after_key)
    if common_atoms != complete_common:
        raise ValueError("common atom mapping omits a shared physical atom")
    # Every unselected atom is an explicit removal or addition, never discarded.
    left_set, right_set = set(left), set(right)
    removed = tuple(i for i in range(len(before.atoms)) if i not in left_set)
    added = tuple(i for i in range(len(after.atoms)) if i not in right_set)
    mapping = dict(common_atoms)
    after_edges = {(row.first, row.second): row.order for row in after.bonds}
    retained_before, retained_after = set(), set()
    for bond in before.bonds:
        if bond.first in mapping and bond.second in mapping:
            edge = tuple(sorted((mapping[bond.first], mapping[bond.second])))
            if edge in after_edges and after_edges[edge] == bond.order:
                retained_before.add((bond.first, bond.second))
                retained_after.add(edge)
    old_sites = {row.site_id: row for row in before.chemistry.sites}
    new_sites = {row.site_id: row for row in after.chemistry.sites}
    if set(old_sites) != set(new_sites):
        raise ValueError("chemical transformation changes the all-eight-site denominator")
    result = AtomicTransformation(transformation_id, before.identity, after.identity, kind,
        None if case is None else case.identity, common_atoms, removed, added,
        tuple((a, b) for a, b in common_atoms if _parameter(before.atoms[a]) != _parameter(after.atoms[b])),
        tuple((row.first, row.second, row.order) for row in before.bonds if (row.first, row.second) not in retained_before),
        tuple((row.first, row.second, row.order) for row in after.bonds if (row.first, row.second) not in retained_after),
        tuple(sorted(site for site in old_sites if old_sites[site] != new_sites[site])), protocol, sources)
    # Unchanged residues cannot be silently renamed or moved to another chain.
    old_residues = {row.residue_id: row for row in before.residues}
    new_residues = {row.residue_id: row for row in after.residues}
    for key in set(old_residues) & set(new_residues):
        a, b = old_residues[key], new_residues[key]
        if (a.role, a.chain_id, a.sequence_position_1based, a.site_id) != (
                b.role, b.chain_id, b.sequence_position_1based, b.site_id):
            raise ValueError("atomic transformation aliases distinct physical residues")
    return result


def validate_atomic_transformation(transformation, before, after, *, case=None):
    exact(transformation, AtomicTransformation)
    expected = derive_atomic_transformation(before, after,
        transformation_id=transformation.transformation_id, kind=transformation.kind,
        common_atoms=transformation.common_atoms, protocol=transformation.protocol,
        sources=transformation.sources, case=case)
    if transformation != expected:
        raise ValueError("atomic transformation differs from the complete independent finite-change census")
