# SPDX-License-Identifier: MPL-2.0
"""Exposed eight-site atom-table control, with isolated padding residues.

The small catalytic coordinates are disclosed construction inputs. The padded
assembly and its minimal Amber text are not physical molecular models. Native
engines must always be replaced by explicitly exposed software callbacks.
"""

from decimal import Decimal as D
from functools import lru_cache
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

from empirical_lawhood.domains.rubisco.rubisco_response.active_model_preparation import prepare_catalytic_sites
from empirical_lawhood.domains.rubisco.rubisco_response.active_model_assessment import assess_catalytic_seed
from empirical_lawhood.domains.rubisco.rubisco_response.active_model_packet import ActiveModelPreparation
from empirical_lawhood.domains.rubisco.rubisco_response.active_state_geometry import materialize_catalytic_states
from empirical_lawhood.domains.rubisco.rubisco_response.catalytic_path_selection import CatalyticPathSelection, CatalyticProteinRegion
from empirical_lawhood.domains.rubisco.rubisco_response.contexts import ActiveSiteSelection, ChemicalProtocol
from empirical_lawhood.domains.rubisco.rubisco_response.disclosed_examples import DisclosedResponseAssumption
from empirical_lawhood.domains.rubisco.rubisco_response.materials import homogeneous_material
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_atoms import MolecularAtom, MolecularBond, MolecularRepresentation, MolecularResidue, MolecularSite
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import prepare_periodic_probe_selection
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_force_contracts import PeriodicForceSettings, PeriodicMMSettings, read_amber_periodic_cell
from empirical_lawhood.domains.rubisco.rubisco_response.reactive_selection import ReactiveBoundary
from empirical_lawhood.science.models.datasets import ArrayDatasetManifest, ArrayDatasetMember
from tests.rubisco_response_molecular_fixture import raw_identity
from tests.test_rubisco_active_state_geometry import protocol
from tests.test_rubisco_preparation_integrity import amber_text
from tests.test_rubisco_physical_preparation_geometry import inpcrd


TEMPLATE = Path(__file__).parent/'fixtures/rubisco/active-states/exposed-core-geometry.json'
POSITIONS = {184:('LYS','K'), 186:('LYS','K'), 210:('KCX','K'), 212:('ASP','D'),
    213:('GLU','E'), 302:('HIE','H'), 342:('LYS','K')}


@lru_cache(maxsize=4)
def molecular_control(name):
    template = json.loads(TEMPLATE.read_text())
    assert template['scope'].startswith('EXPOSED_')
    p = protocol()
    core = next(g for g in p.graphs if g.label == 'keto-hie')
    source = DisclosedResponseAssumption().identity
    lsu = ['G']*342
    for position, (_, letter) in POSITIONS.items():
        lsu[position-1] = letter
    ssu = 'G'*94+('M' if name.endswith('i95m') else 'I')
    material = homogeneous_material(material_id='material.exposed.active.'+name, organism='Exposed padded atom-table control',
        processing_view=name.split('-')[0], lsu=''.join(lsu), ssu=ssu, sources=(source,))
    chemical_sites = tuple(ActiveSiteSelection(f'site.gp.lsu.{i:02}', f'lsu.{i:02}', 210,
        True, True, 'RUBP', source, source, source) for i in range(1, 9))
    chemistry = ChemicalProtocol('chemistry.exposed.active', chemical_sites, 'EXCHANGEABLE', source, (source,), ())
    residues, atoms, points, edges = [], [], [], set()
    mapping = {}
    def add(residue_id, component, role, spec, *, chain=None, position=None, letter=None, site=None):
        residues.append(MolecularResidue(residue_id, component, role, chain, position, letter,
            None, None, '', source, site))
        selected = {}
        for atom_name, number, xyz in spec:
            index = len(atoms)
            atom_id = residue_id+'.'+atom_name.lower()
            atoms.append(MolecularAtom(atom_id, residue_id, atom_name, number,
                D({1:1,6:12,7:14,8:16,12:24,15:31,16:32}[number]), D(0), D('18.2223'), 'EXPOSED', source, atom_id))
            points.append(tuple(round(float(x), 7) for x in xyz))
            selected[atom_name] = index
        return selected
    def edge(a, b):
        edges.add(tuple(sorted((a, b))))
    for chain in material.chains:
        ordinal = int(chain.chain_id.rsplit('.',1)[1])-1
        offset = np.asarray((50+ordinal*40,50,50))
        mapping[chain.chain_id] = {}
        for position, letter in enumerate(chain.sequence, 1):
            residue_id = f'residue.{chain.chain_id}.{position:03}'
            if chain.subunit == 'LSU' and position in POSITIONS:
                component = POSITIONS[position][0]
                prefix = f'protein.{position}.'
                labels = sorted(k for k in template['coordinates'] if k.startswith(prefix))
                numbers = {a.label:a.atomic_number for a in core.atoms}
                numbers.update({prefix+n:z for n,z in (('CA',6),('N',7),('C',6),('O',8))})
                spec = [(label.rsplit('.',1)[1],numbers[label],np.asarray(template['coordinates'][label])+offset) for label in labels]
                selected = add(residue_id,component,'PROTEIN',spec,chain=chain.chain_id,position=position,
                    letter=letter,site=f'site.gp.lsu.{ordinal+1:02}' if position==210 else None)
                mapping[chain.chain_id].update((prefix+n,i) for n,i in selected.items())
                for a,b in (('CA','CB'),('CA','N'),('CA','C'),('C','O')):
                    edge(selected[a],selected[b])
            else:
                i=len(residues)
                offset=np.asarray((5*(i%100),200+5*(i//100),400))
                # Isolated padding residues deliberately have only one CA.
                spec=[('CA',6,offset)]
                if letter!='G':
                    spec += [('N',7,offset+(1.4,0,0)),('C',6,offset+(0,1.5,0)),
                        ('O',8,offset+(0,2.7,0)),('CB',6,offset+(0,0,1.5))]
                    if letter=='I':
                        spec += [('CG1',6,offset+(1.3,0,2.4)),('CG2',6,offset+(0,1.4,2.2))]
                selected=add(residue_id, 'GLY' if letter=='G' else ('MET' if letter=='M' else 'ILE'), 'PROTEIN',
                    spec,chain=chain.chain_id,position=position,letter=letter)
                if letter!='G':
                    for a,b in (('CA','N'),('CA','C'),('C','O'),('CA','CB')):
                        edge(selected[a],selected[b])
                    if letter=='I':
                        edge(selected['CB'],selected['CG1']);edge(selected['CB'],selected['CG2'])
                offset=np.asarray((50+ordinal*40,50,50))
    sites=[]
    for selected_site in chemistry.sites:
        ordinal=int(selected_site.lsu_chain_id.rsplit('.',1)[1])-1
        offset=np.asarray((50+ordinal*40,50,50))
        named=mapping[selected_site.lsu_chain_id]
        magnesium=add('residue.'+selected_site.site_id+'.mg','MG','MAGNESIUM', [('MG',12,offset)],site=selected_site.site_id)
        named['magnesium.MG']=magnesium['MG']
        spec=[(a.label.split('.')[1],a.atomic_number,np.asarray(template['coordinates'][a.label])+offset)
            for a in core.atoms if a.label.startswith('ligand.')]
        ligand=add('residue.'+selected_site.site_id+'.ligand','RUB','LIGAND',spec,site=selected_site.site_id)
        named.update(('ligand.'+n,i) for n,i in ligand.items())
        for b in core.bonds:
            a,c=core.atoms[b.first],core.atoms[b.second]
            if not a.cap and not c.cap:
                edge(named[a.label],named[c.label])
        for j,water in enumerate(template['waters']):
            water=add(f'residue.water.{ordinal:02}.{j:02}','WAT','WATER',
                [(n,z,np.asarray(xyz)+offset) for n,z,xyz in zip(('O','H1','H2'),(8,1,1),water,strict=True)])
            edge(water['O'],water['H1']);edge(water['O'],water['H2']);edge(water['H1'],water['H2'])
        sites.append(MolecularSite(selected_site.site_id,f'residue.{selected_site.lsu_chain_id}.210',
            (magnesium['MG'],),tuple(ligand.values()),(),(),source))
    raw_xyz=inpcrd(points,box=(1000,1000,1000,90,90,90)).encode('ascii')
    # Only the explicit original cell contract is exercised; this is never an
    # input to Amber/OpenMM. A stock parameter assignment is not fabricated.
    raw_top=amber_text({'POINTERS':[len(atoms)]+[0]*31,'BOX_DIMENSIONS':[D(90),D(1000),D(1000),D(1000)]}).encode('ascii')
    top,xyz=raw_identity('source.exposed.active-topology.'+name,raw_top),raw_identity('source.exposed.active-coordinates.'+name,raw_xyz)
    coordinates=np.asarray(points,dtype='<f8').tobytes()
    arrays=ArrayDatasetManifest('arrays.exposed.active.'+name,
        (ArrayDatasetMember('coordinates-angstrom','<f8',(len(atoms),3),sha256(coordinates).hexdigest()),),
        tuple(sorted((top,xyz),key=lambda r:r.object_id)))
    model=MolecularRepresentation('molecular.exposed.active.'+name,material,chemistry,D('298.15'),source,source,top,xyz,
        tuple(sorted(residues,key=lambda r:r.residue_id)),tuple(atoms),tuple(MolecularBond(a,b,D(1)) for a,b in sorted(edges)),
        tuple(sites),arrays,tuple(sorted((source,top,xyz),key=lambda r:r.object_id)))
    cell=read_amber_periodic_cell(model,raw_top,raw_xyz)
    electronic=PeriodicForceSettings('settings.exposed.active-electronic','wb97x','def2-svpd','RKS',3,
        D('1e-12'),D('1e-9'),None,256,D(9),D(6),D('.25'),(41,41,41),D('1e-8'))
    molecular=PeriodicMMSettings('settings.exposed.active-mm','Ewald',D(9),D('1e-6'))
    first=sites[0]
    named=mapping[chemical_sites[0].lsu_chain_id]
    qm={named[a.label] for a in core.atoms if not a.cap}
    # The first-site prototype only needs its core. The public preparer derives
    # every complete site/water selection from each original geometry itself.
    boundaries=tuple(ReactiveBoundary(f'link.exposed.{position}',named[f'protein.{position}.CB'],
        named[f'protein.{position}.CA'],1,D('1.09'),source) for position in POSITIONS)
    path= CatalyticPathSelection('path.exposed.active.'+name,model.identity,len(atoms),first.site_id,tuple(sorted(qm)),
        tuple(i for i in range(len(atoms)) if i not in qm),
        tuple(CatalyticProteinRegion(f'residue.lsu.01.{position:03}','SIDECHAIN_CB_CA') for position in POSITIONS),
        boundaries,'NONE',(),-2,1,electronic.identity,None,source,molecular.identity,'MOVING_FULL_ASSEMBLY',
        tuple(sorted({model.identity,electronic.identity,molecular.identity,*model.sources},key=lambda r:r.object_id)))
    return model,path,cell,electronic,molecular,raw_top,raw_xyz,coordinates,p


def prepared_control(name, stock):
    model,path,cell,electronic,molecular,raw_top,raw_xyz,coordinates,p=molecular_control(name)
    prototype=prepare_periodic_probe_selection(representation=model,path=path,cell=cell,electronic=electronic,
        molecular=molecular,engine=stock)
    sites=prepare_catalytic_sites(representation=model,prototype=prototype,coordinate_bytes=coordinates,protocol=p)
    seeds=[];assessments=[]
    for site in sites:
        for seed in materialize_catalytic_states(representation=model,site=site,protocol=p,coordinate_bytes=coordinates,cell=cell):
            seeds.append(seed)
            assessments.append(assess_catalytic_seed(representation=model,site=site,protocol=p,
                seed=seed,coordinate_bytes=coordinates,cell=cell))
    rows=sorted(zip(seeds,assessments,strict=True),key=lambda row:row[0].seed_id)
    prepared=ActiveModelPreparation('preparation.exposed.active.'+name,model.identity,prototype.identity,p,sites,
        tuple(s for s,_ in rows),tuple(a for _,a in rows))
    return model,prototype,prepared,raw_top,raw_xyz,coordinates
