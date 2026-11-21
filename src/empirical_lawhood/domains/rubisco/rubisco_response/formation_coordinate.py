# SPDX-License-Identifier: MPL-2.0
"""Derive the selected proton-transfer receiver from retained chemical graphs."""

from dataclasses import dataclass,replace
from decimal import Decimal
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_sha256, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.active_model_packet import ActiveModelPreparation
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_atoms import MolecularRepresentation


STATES=('keto-hie','initial-enolate-kcxh-hie')


@dataclass(frozen=True,slots=True)
class PreparedFormationCoordinate(CanonicalRecord):
    SCHEMA: ClassVar[str]='empirical-lawhood/rubisco-response/prepared-formation-coordinate'
    coordinate_id: str
    representation: ObjectIdentity
    preparation: ObjectIdentity
    prepared_site: ObjectIdentity
    site_id: str
    state_seeds: tuple[ObjectIdentity, ...]
    graph_atom_labels: tuple[str, ...]
    native_atom_indices: tuple[int, ...]
    physical_atom_ids: tuple[str, ...]
    natural_masses_dalton: tuple[Decimal, ...]
    complete_mass_sha256: str
    physical_atom_count: int
    state_labels: tuple[str, ...]=STATES
    coordinate: str='DISTANCE_12_MINUS_DISTANCE_23'
    unit: str='ANGSTROM'
    required_constraints: str='NONE'
    scope: str='ORIGINAL_PHYSICAL_ATOM_AND_PROTON_ALLOCATION_NOT_ENSEMBLE_ADMISSION'

    def __post_init__(self):
        for name in (self.coordinate_id,self.site_id):
            validate_stable_id(name)
        for pin in (self.representation,self.preparation,self.prepared_site):
            exact(pin,ObjectIdentity)
        if (type(self.state_seeds) is not tuple or len(self.state_seeds)!=2
                or self.state_labels!=STATES or type(self.physical_atom_count) is not int or self.physical_atom_count<3):
            raise ValueError('formation coordinate requires both original selected states and full physical atom count')
        for pin in self.state_seeds:
            exact(pin,ObjectIdentity)
        for values in (self.graph_atom_labels,self.native_atom_indices,self.physical_atom_ids,self.natural_masses_dalton):
            if type(values) is not tuple or len(values)!=3:
                raise ValueError('formation coordinate needs its three ordered physical roles')
        if (self.graph_atom_labels[:2]!=('ligand.C3','ligand.HC3')
                or not self.graph_atom_labels[2].startswith('protein.')
                or len(set(self.native_atom_indices))!=3
                or any(type(i) is not int or not 0<=i<self.physical_atom_count for i in self.native_atom_indices)
                or len(set(self.physical_atom_ids))!=3):
            raise ValueError('formation coordinate substitutes a named role or its native physical atom')
        for name in self.physical_atom_ids:
            validate_stable_id(name)
        for mass in self.natural_masses_dalton:
            if type(mass) is not Decimal or not mass.is_finite() or mass<=0:
                raise ValueError('formation receiver must retain positive natural masses')
        validate_sha256(self.complete_mass_sha256)
        if (self.coordinate!='DISTANCE_12_MINUS_DISTANCE_23' or self.unit!='ANGSTROM' or self.required_constraints!='NONE'
                or self.scope!='ORIGINAL_PHYSICAL_ATOM_AND_PROTON_ALLOCATION_NOT_ENSEMBLE_ADMISSION'):
            raise ValueError('formation coordinate changes its geometry, measure or evidence scope')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.coordinate_id,self)


def prepare_formation_coordinate(*,representation,prepared,site_id):
    exact(representation,MolecularRepresentation)
    exact(prepared,ActiveModelPreparation)
    if prepared.representation!=representation.identity:
        raise ValueError('formation coordinate changes its complete original representation')
    sites=tuple(s for s in prepared.sites if s.path.reactive_site_id==site_id)
    if len(sites)!=1:
        raise ValueError('formation coordinate requires one actual selected catalytic site')
    site=sites[0]
    graphs={g.label:g for g in prepared.protocol.graphs}
    keto,enolate=(graphs[name] for name in STATES)
    labels=tuple(a.label for a in keto.atoms)
    carbon,hydrogen=(labels.index(label) for label in ('ligand.C3','ligand.HC3'))
    def neighbour(graph,index):
        return tuple(b.second if b.first==index else b.first for b in graph.bonds if index in (b.first,b.second))
    if neighbour(keto,hydrogen)!=(carbon,) or len(neighbour(enolate,hydrogen))!=1:
        raise ValueError('selected graphs do not retain the original C3 hydrogen transfer')
    oxygen=neighbour(enolate,hydrogen)[0]
    if enolate.atoms[oxygen].atomic_number!=8 or not enolate.atoms[oxygen].label.startswith('protein.'):
        raise ValueError('selected enolate has no source-defined protein oxygen proton acceptor')
    ordinals=(carbon,hydrogen,oxygen)
    indices=tuple(site.core_atom_indices[i] for i in ordinals)
    if any(i>=len(representation.atoms) for i in indices):
        raise ValueError('formation coordinate cannot use a boundary cap as a physical atom')
    atoms=tuple(representation.atoms[i] for i in indices)
    molecular_site=next(s for s in representation.sites if s.site_id==site_id)
    if (tuple(a.atomic_number for a in atoms)!=(6,1,8)
            or indices[0] not in molecular_site.ligand_atom_indices or indices[1] not in molecular_site.ligand_atom_indices
            or atoms[2].residue_id!=molecular_site.catalytic_residue_id
            or tuple(a.name for a in atoms)!=tuple(labels[i].rsplit('.',1)[1] for i in ordinals)):
        raise ValueError('formation graph roles do not match the complete physical substrate/KCX atom table')
    seeds=[]
    for label in STATES:
        selected=tuple(s for s in prepared.seeds if s.site==site.identity and s.state_label==label and s.water_occupancy=='AS_CONSTRUCTED')
        if len(selected)!=1:
            raise ValueError('formation coordinate omits or repeats an original selected physical state')
        seeds.append(selected[0].identity)
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_trajectory_selection import physical_masses
    masses=physical_masses(representation)
    provisional=PreparedFormationCoordinate('formation-coordinate.pending',representation.identity,prepared.identity,site.identity,
        site_id,tuple(seeds),tuple(labels[i] for i in ordinals),indices,tuple(a.atom_id for a in atoms),
        tuple(a.mass_dalton for a in atoms),sha256(masses.tobytes()).hexdigest(),len(representation.atoms))
    return replace(provisional,coordinate_id='formation-coordinate.'+provisional.fingerprint())
