# SPDX-License-Identifier: MPL-2.0
"""Exact full-environment reactive selections; no electronic backend admission."""

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_ids, validate_decimal, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact, identities
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_atoms import MolecularRepresentation, indices


@dataclass(frozen=True, slots=True)
class ReactiveBoundary(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/reactive-boundary"
    link_id: str
    qm_atom_index: int
    mm_atom_index: int
    link_element: int
    link_distance_angstrom: Decimal
    construction_and_force_projection: ObjectIdentity

    def __post_init__(self):
        validate_stable_id(self.link_id)
        if (type(self.qm_atom_index) is not int or type(self.mm_atom_index) is not int
                or min(self.qm_atom_index, self.mm_atom_index) < 0
                or self.qm_atom_index == self.mm_atom_index
                or type(self.link_element) is not int or self.link_element != 1):
            raise ValueError("selected link boundary requires distinct physical atoms and explicit hydrogen")
        validate_decimal(self.link_distance_angstrom, field_name="link_distance_angstrom", minimum=Decimal(0))
        if self.link_distance_angstrom == 0:
            raise ValueError("selected link distance must be positive")
        exact(self.construction_and_force_projection, ObjectIdentity)


@dataclass(frozen=True, slots=True)
class ReactiveSelection(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/reactive-selection"
    selection_id: str
    representation: ObjectIdentity
    physical_atom_count: int
    reactive_site_id: str
    qm_atom_indices: tuple[int, ...]
    mm_atom_indices: tuple[int, ...]
    boundaries: tuple[ReactiveBoundary, ...]
    gas: str
    gas_atom_indices: tuple[int, ...]
    qm_formal_charge: int
    spin_multiplicity: int
    electronic_approximation: ObjectIdentity
    oxygenation_assumption: ObjectIdentity | None
    embedding_method: ObjectIdentity
    complement_hamiltonian: ObjectIdentity
    environment_mode: str
    sources: tuple[ObjectIdentity, ...]
    interpretation: str = "SELECTED_FULL_ENVIRONMENT_REACTIVE_MODEL_NOT_BACKEND_OR_KINETIC_QUALIFICATION"

    def __post_init__(self):
        for name in ("selection_id", "reactive_site_id"):
            validate_stable_id(getattr(self, name))
        if type(self.physical_atom_count) is not int or self.physical_atom_count <= 0:
            raise ValueError("reactive selection requires the complete physical atom denominator")
        for name in ("qm_atom_indices", "mm_atom_indices", "gas_atom_indices"):
            indices(getattr(self, name), count=self.physical_atom_count, name=name, nonempty=True)
        if (set(self.qm_atom_indices) & set(self.mm_atom_indices)
                or len(self.qm_atom_indices) + len(self.mm_atom_indices) != self.physical_atom_count):
            raise ValueError("QM/MM partition omits or duplicates the full physical environment")
        if not set(self.gas_atom_indices).issubset(self.qm_atom_indices):
            raise ValueError("selected reactive gas atoms must be in the physical QM region")
        if self.gas not in {"CO2", "O2"} or len(self.gas_atom_indices) != (3 if self.gas == "CO2" else 2):
            raise ValueError("reactive gas needs its complete selected molecular atom census")
        if (type(self.qm_formal_charge) is not int or type(self.spin_multiplicity) is not int
                or self.spin_multiplicity <= 0):
            raise ValueError("QM charge and spin multiplicity must be explicit integers")
        if type(self.boundaries) is not tuple:
            raise ValueError("reactive boundaries must retain their complete immutable census")
        for row in self.boundaries:
            exact(row, ReactiveBoundary)
            if row.qm_atom_index not in self.qm_atom_indices or row.mm_atom_index not in self.mm_atom_indices:
                raise ValueError("reactive boundary crosses the wrong selected partition")
        require_sorted_unique_ids(self.boundaries, attribute="link_id", field_name="boundaries")
        if len({(row.qm_atom_index, row.mm_atom_index) for row in self.boundaries}) != len(self.boundaries):
            raise ValueError("reactive boundary duplicates a physical cut bond")
        for row in (self.representation, self.electronic_approximation, self.embedding_method,
                    self.complement_hamiltonian):
            exact(row, ObjectIdentity)
        if self.oxygenation_assumption is not None:
            exact(self.oxygenation_assumption, ObjectIdentity)
            if self.gas != "O2":
                raise ValueError("oxygenation assumption cannot alias a different gas selection")
        if self.environment_mode not in {"FIXED_FULL_ASSEMBLY_FIELD", "MOVING_FULL_ASSEMBLY"}:
            raise ValueError("reactive environment treatment must be explicit and retain all subunits")
        identities(self.sources)
        required = {self.electronic_approximation, self.embedding_method, self.complement_hamiltonian,
                    *(row.construction_and_force_projection for row in self.boundaries)}
        if self.oxygenation_assumption is not None:
            required.add(self.oxygenation_assumption)
        if not required.issubset(self.sources):
            raise ValueError("reactive selection drops its exact electronic, boundary or environment sources")
        if self.interpretation != "SELECTED_FULL_ENVIRONMENT_REACTIVE_MODEL_NOT_BACKEND_OR_KINETIC_QUALIFICATION":
            raise ValueError("reactive selection cannot establish chemistry or backend support")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.selection_id, self)


def validate_reactive_selection(selection, representation):
    """Check actual atom joins, all cut bonds and electron parity independently."""
    exact(selection, ReactiveSelection)
    exact(representation, MolecularRepresentation)
    if (selection.representation != representation.identity
            or selection.physical_atom_count != len(representation.atoms)):
        raise ValueError("reactive selection substitutes its complete molecular representation")
    site = next((row for row in representation.sites if row.site_id == selection.reactive_site_id), None)
    if site is None:
        raise ValueError("reactive selection names an absent site")
    if selection.gas_atom_indices != site.gas_atom_indices:
        raise ValueError("reactive gas substitutes the complete site gas correspondence")
    qm = set(selection.qm_atom_indices)
    critical = {i for i, atom in enumerate(representation.atoms) if atom.residue_id == site.catalytic_residue_id}
    critical.update((*site.ligand_atom_indices, *site.magnesium_atom_indices, *site.proton_transfer_atom_indices))
    if not critical.issubset(qm):
        raise ValueError("reactive QM selection omits selected ligand, KCX, magnesium or proton-transfer atoms")
    gas_numbers = tuple(sorted(representation.atoms[i].atomic_number for i in selection.gas_atom_indices))
    if gas_numbers != ((6, 8, 8) if selection.gas == "CO2" else (8, 8)):
        raise ValueError("reactive gas correspondence changes the selected molecular elements")
    cut = {(row.first, row.second) if row.first in qm else (row.second, row.first)
           for row in representation.bonds if (row.first in qm) != (row.second in qm)}
    if cut != {(row.qm_atom_index, row.mm_atom_index) for row in selection.boundaries}:
        raise ValueError("reactive boundary census omits or invents a physical cut bond")
    if {row.link_id for row in selection.boundaries} & {row.atom_id for row in representation.atoms}:
        raise ValueError("nonphysical link atom aliases a physical atom")
    electrons = sum(representation.atoms[i].atomic_number for i in qm) + len(selection.boundaries) - selection.qm_formal_charge
    unpaired = selection.spin_multiplicity - 1
    if electrons <= 0 or unpaired > electrons or (electrons - unpaired) % 2:
        raise ValueError("reactive charge, link atoms and spin change the electron parity/count")
    return tuple(sorted({
        "requirement.reactive.chemical-admission",
        "requirement.reactive.coupled-hamiltonian-assessment",
        "requirement.reactive.force-and-geometry-assessment",
        "requirement.reactive.selected-backend-support",
        *({"requirement.reactive.oxygenation-assumption"}
          if selection.gas == "O2" and selection.oxygenation_assumption is None else set()),
    }))
