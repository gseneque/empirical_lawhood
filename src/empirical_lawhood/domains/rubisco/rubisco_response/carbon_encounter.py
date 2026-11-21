# SPDX-License-Identifier: MPL-2.0
"""Released CO2 encounter placement through the shared complete-target owner."""

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

import numpy as np

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_decimal, validate_sha256
from empirical_lawhood.domains.rubisco.rubisco_response.carbon_source_geometry import CarbonSourceProjection
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.oxygen_encounter import fit_gas_encounter, assess_gas_encounter, selected_gas_free_target


ANCHORS = ('C2','C3','O2','O3','Mg')
SOURCE_ANCHORS = (53,54,59,60,51)
SOURCE_GAS = (57,63,64)
SCOPE = 'NEW_UNRELAXED_CO2_ENCOUNTER_COORDINATES_NOT_AUGMENTED_TOPOLOGY_OR_PHYSICAL_ADMISSION'


@dataclass(frozen=True, slots=True)
class CarbonEncounterGeometry(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/carbon-encounter-geometry'
    representation: ObjectIdentity
    preparation: ObjectIdentity
    selected_seed: ObjectIdentity
    selected_site: ObjectIdentity
    source_projection: ObjectIdentity
    cell: ObjectIdentity
    original_coordinate_sha256: str
    expanded_seed_coordinate_sha256: str
    retained_physical_atom_count: int
    anchors: tuple[tuple[str,int,int], ...]
    source_gas_indices_1based: tuple[int,int,int]
    rotation: tuple[Decimal, ...]
    translation_angstrom: tuple[Decimal, ...]
    anchor_residuals_angstrom: tuple[Decimal, ...]
    fit_rmsd_angstrom: Decimal
    gas_coordinates_angstrom: tuple[tuple[Decimal, ...], ...]
    nearest_original_contacts: tuple[tuple[int,Decimal,int,Decimal], ...]
    inspected_gas_environment_pairs: int
    native_source_label: str = 'P'
    scope: str = SCOPE

    def __post_init__(self):
        for value in (self.representation,self.preparation,self.selected_seed,self.selected_site,
                self.source_projection,self.cell):
            exact(value,ObjectIdentity)
        for value in (self.original_coordinate_sha256,self.expanded_seed_coordinate_sha256):
            validate_sha256(value)
        n=self.retained_physical_atom_count
        if (type(n) is not int or n <= 0 or type(self.anchors) is not tuple or len(self.anchors)!=5
                or tuple((r[0],r[1]) for r in self.anchors)!=tuple(zip(ANCHORS,SOURCE_ANCHORS,strict=True))
                or any(type(r[2]) is not int or not 0<=r[2]<n for r in self.anchors)
                or len({r[2] for r in self.anchors})!=5 or self.source_gas_indices_1based!=SOURCE_GAS
                or type(self.inspected_gas_environment_pairs) is not int
                or self.inspected_gas_environment_pairs!=3*n or self.native_source_label!='P' or self.scope!=SCOPE):
            raise ValueError('carbon encounter changes its original source direction, atoms or complete environment')
        for row,count in ((self.rotation,9),(self.translation_angstrom,3),(self.anchor_residuals_angstrom,5)):
            if type(row) is not tuple or len(row)!=count:
                raise ValueError('carbon encounter requires the complete retained transform')
            for value in row:
                validate_decimal(value,field_name='carbon_coordinate_transform')
        validate_decimal(self.fit_rmsd_angstrom,field_name='carbon_fit_rmsd',minimum=Decimal(0))
        if any(v<0 for v in self.anchor_residuals_angstrom):
            raise ValueError('carbon anchor residual cannot be negative')
        if (type(self.gas_coordinates_angstrom) is not tuple or len(self.gas_coordinates_angstrom)!=3
                or type(self.nearest_original_contacts) is not tuple or len(self.nearest_original_contacts)!=3):
            raise ValueError('carbon encounter must preserve all three gas atoms and their contact observations')
        for row in self.gas_coordinates_angstrom:
            if type(row) is not tuple or len(row)!=3:
                raise ValueError('carbon gas position requires three coordinates')
            for value in row:
                validate_decimal(value,field_name='carbon_gas_coordinate')
        for atom,distance,heavy,heavy_distance in self.nearest_original_contacts:
            if any(type(i) is not int or not 0<=i<n for i in (atom,heavy)):
                raise ValueError('carbon contact points outside its complete original environment')
            for value in (distance,heavy_distance):
                validate_decimal(value,field_name='carbon_contact_distance',minimum=Decimal(0))

    @property
    def identity(self):
        return ObjectIdentity.from_record('carbon-encounter.'+self.fingerprint(),self)


def carbon_source_operands(source):
    """Use P for addition; the source's native direction is decarboxylation."""
    exact(source,CarbonSourceProjection)
    state=next(row for row in source.states if row.native_label=='P')
    atoms=state.successor_atoms
    if (tuple(atoms[i-1].element for i in SOURCE_ANCHORS)!=('C','C','O','O','Mg')
            or tuple(atoms[i-1].element for i in SOURCE_GAS)!=('C','O','O')
            or state.gas_addition_role!='SEPARATED_CO2_SOURCE'):
        raise ValueError('carbon encounter changes the released P geometry or original atom elements')
    xyz=np.asarray([[float(v) for v in atom.coordinate_tokens] for atom in atoms])
    return dict(source_anchors=xyz[[i-1 for i in SOURCE_ANCHORS]],source_gas=xyz[[i-1 for i in SOURCE_GAS]])


def prepare_carbon_encounter(*, source, representation, preparation, seed, coordinate_bytes, cell):
    site,targets,operands=selected_gas_free_target(representation=representation,preparation=preparation,
        seed=seed,coordinate_bytes=coordinate_bytes,cell=cell)
    operands.update(carbon_source_operands(source))
    rotation,translation,rmsd,residuals,gas,contacts=fit_gas_encounter(**operands)
    def decimal(values):
        return tuple(Decimal(str(float(v))) for v in values)
    return CarbonEncounterGeometry(representation.identity,preparation.identity,seed.identity,site.identity,
        source.identity,cell.identity,seed.original_coordinate_sha256,seed.expanded_coordinate_sha256,
        len(representation.atoms),tuple(zip(ANCHORS,SOURCE_ANCHORS,targets,strict=True)),SOURCE_GAS,
        decimal(rotation.ravel()),decimal(translation),decimal(residuals),Decimal(str(rmsd)),
        tuple(decimal(row) for row in gas),contacts,3*len(representation.atoms))


def assess_carbon_encounter(*, result, source, representation, preparation, seed, coordinate_bytes, cell):
    exact(result,CarbonEncounterGeometry)
    site,targets,operands=selected_gas_free_target(representation=representation,preparation=preparation,
        seed=seed,coordinate_bytes=coordinate_bytes,cell=cell)
    operands.update(carbon_source_operands(source))
    if ((result.representation,result.preparation,result.selected_seed,result.selected_site,result.source_projection,
            result.cell)!=(representation.identity,preparation.identity,seed.identity,site.identity,source.identity,cell.identity)
            or (result.original_coordinate_sha256,result.expanded_seed_coordinate_sha256)!=(
                seed.original_coordinate_sha256,seed.expanded_coordinate_sha256)
            or result.retained_physical_atom_count!=len(representation.atoms)
            or result.anchors!=tuple(zip(ANCHORS,SOURCE_ANCHORS,targets,strict=True))):
        raise ValueError('carbon encounter substitutes an original source, target or atom correspondence')
    arithmetic=assess_gas_encounter(observation=(np.asarray(result.rotation,dtype=float).reshape(3,3),
        result.translation_angstrom,result.fit_rmsd_angstrom,result.anchor_residuals_angstrom,
        result.gas_coordinates_angstrom,result.nearest_original_contacts),**operands)
    return dict(status='COORDINATE_TRANSFER_INDEPENDENTLY_CHECKED',arithmetic=arithmetic,new_native_calls=0,
        physical_or_chemical_admission=False,gas_atoms_added_to_topology=0,
        required=('RELAXED_TARGET_STATE','GAS_AUGMENTED_TOPOLOGY_AND_FULL_COMPLEMENT',
            'SELECTED_QM_REGION_CHARGE_AND_PROTONATION','ENERGY_FORCE_AND_GEOMETRY_ASSESSMENT',
            'BULK_ACCESS_AND_TRANSMISSION','CARBON_PRODUCTIVE_OR_RETURN_EXITS'))
