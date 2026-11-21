# SPDX-License-Identifier: MPL-2.0
"""Exact periodic gas particle density with its complete molecular census.

Box density does not establish a free bulk reservoir, accessible-volume
correction or dilute limit. Those physical premises remain separately assessed.
"""

from dataclasses import dataclass
from decimal import Decimal, localcontext
from fractions import Fraction
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_insilico_mechanism.contracts import Exact
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_atoms import MolecularRepresentation
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import PeriodicProbeSelection, validate_periodic_probe_model


AVOGADRO_PER_MOL = 602214076000000000000000


def _ids(values):
    if type(values) is not tuple or values != tuple(sorted(set(values))):
        raise ValueError('gas density requires a sorted complete free/bound molecule census')
    for value in values:
        validate_stable_id(value)


@dataclass(frozen=True, slots=True)
class PeriodicGasConcentration(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/periodic-gas-concentration'
    VERSION: ClassVar[str] = '1.0.0'
    concentration_id: str
    prototype: ObjectIdentity
    representation: ObjectIdentity
    gas: str
    free_gas_residue_ids: tuple[str, ...]
    bound_gas_residue_ids: tuple[str, ...]
    cell_volume_angstrom_cubed: Exact
    particle_concentration_uM: Exact
    free_bound_assignment_source: ObjectIdentity
    scope: str = 'FULL_PERIODIC_CELL_PARTICLE_DENSITY_WITHOUT_BULK_OR_DILUTE_ADMISSION'

    def __post_init__(self):
        validate_stable_id(self.concentration_id)
        for value in (self.prototype,self.representation,self.free_bound_assignment_source):
            exact(value,ObjectIdentity)
        if (self.prototype.object_schema!=PeriodicProbeSelection.SCHEMA or self.prototype.object_version!=PeriodicProbeSelection.VERSION
                or self.representation.object_schema!=MolecularRepresentation.SCHEMA or self.representation.object_version!=MolecularRepresentation.VERSION):
            raise ValueError('gas density changes its original periodic molecular model')
        _ids(self.free_gas_residue_ids)
        _ids(self.bound_gas_residue_ids)
        if (self.gas not in {'CO2','O2'} or not self.free_gas_residue_ids
                or set(self.free_gas_residue_ids).intersection(self.bound_gas_residue_ids)):
            raise ValueError('gas density must distinguish its complete free and bound selected species')
        exact(self.cell_volume_angstrom_cubed,Exact)
        exact(self.particle_concentration_uM,Exact)
        volume = self.cell_volume_angstrom_cubed.fraction
        if volume<=0 or self.particle_concentration_uM.fraction!=Fraction(len(self.free_gas_residue_ids)*10**33,AVOGADRO_PER_MOL)/volume:
            raise ValueError('periodic gas concentration differs from exact particle, volume and SI unit conversion')
        if self.scope!='FULL_PERIODIC_CELL_PARTICLE_DENSITY_WITHOUT_BULK_OR_DILUTE_ADMISSION':
            raise ValueError('periodic particle density cannot establish a dissolved bulk reservoir')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.concentration_id,self)

    @property
    def decimal_uM(self):
        with localcontext() as ctx:
            ctx.prec = 80
            value = self.particle_concentration_uM.fraction
            return Decimal(value.numerator)/Decimal(value.denominator)


def prepare_periodic_gas_concentration(*, prototype, representation, gas, free_gas_residue_ids,
        bound_gas_residue_ids, free_bound_assignment_source):
    validate_periodic_probe_model(prototype,representation)
    _ids(free_gas_residue_ids)
    _ids(bound_gas_residue_ids)
    if gas not in {'CO2','O2'}:
        raise ValueError('periodic gas concentration requires carbon dioxide or molecular oxygen')
    expected_elements = {'CO2':(6,8,8),'O2':(8,8)}
    selected = []
    for residue in representation.residues:
        if residue.role!='GAS':
            continue
        indices = {i for i,a in enumerate(representation.atoms) if a.residue_id==residue.residue_id}
        elements = tuple(sorted(representation.atoms[i].atomic_number for i in indices))
        if elements not in expected_elements.values():
            raise ValueError('periodic gas census contains an unresolved molecular species')
        if any((b.first in indices)!=(b.second in indices) for b in representation.bonds):
            raise ValueError('periodic gas density cannot count a covalently incorporated species as a free molecule')
        if elements==expected_elements[gas]:
            selected.append(residue.residue_id)
    if set(selected)!=set(free_gas_residue_ids)|set(bound_gas_residue_ids):
        raise ValueError('periodic gas concentration omits or invents an original gas molecule')
    if prototype.path.gas!=gas:
        raise ValueError('periodic gas concentration differs from the actual focal reactive gas')
    volume = Fraction(1)
    for length in prototype.cell.lengths_angstrom:
        volume *= Fraction(length)
    concentration = Fraction(len(free_gas_residue_ids)*10**33,AVOGADRO_PER_MOL)/volume
    key = sha256(prototype.canonical_bytes()+representation.canonical_bytes()+
        repr((gas,free_gas_residue_ids,bound_gas_residue_ids)).encode('ascii')+free_bound_assignment_source.canonical_bytes()).hexdigest()
    return PeriodicGasConcentration('concentration.periodic-gas.'+key,prototype.identity,representation.identity,gas,
        free_gas_residue_ids,bound_gas_residue_ids,Exact.of(volume),Exact.of(concentration),free_bound_assignment_source)


def validate_periodic_gas_concentration(selected,prototype,representation):
    exact(selected,PeriodicGasConcentration)
    reproduced = prepare_periodic_gas_concentration(prototype=prototype,representation=representation,gas=selected.gas,
        free_gas_residue_ids=selected.free_gas_residue_ids,bound_gas_residue_ids=selected.bound_gas_residue_ids,
        free_bound_assignment_source=selected.free_bound_assignment_source)
    if selected!=reproduced:
        raise ValueError('periodic gas concentration changes its original complete molecular census or box volume')
