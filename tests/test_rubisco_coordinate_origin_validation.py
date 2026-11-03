# SPDX-License-Identifier: MPL-2.0
"""Complete exposed origin falsifiers; no actual/native molecular result."""
from copy import deepcopy
from decimal import Decimal as D
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.preparation_integrity import (
    COORDINATE_ORIGIN_METHOD,
    validate_origins,
    validate_origins_from_coordinates,
)
from tests.test_rubisco_physical_preparation_geometry import inpcrd
from tests.test_rubisco_preparation_integrity import full_exposed_origins


def exposed(swapped=True, duplicate_added=False):
    model,census,origin,_,atoms,chains = full_exposed_origins()
    origin=deepcopy(origin)
    n=len(origin['complete_heavy_atoms'])
    points=[(D(i)/10,D(2),D(3)) for i in range(n)]
    lines=[]
    for i,row in enumerate(origin['complete_heavy_atoms']):
        x,y,z=points[i]
        lines.append(f"HETATM{i+1:5d}  CA  {row['component']:>3} {row['chain']}{row['position']:4d}    {x:8.3f}{y:8.3f}{z:8.3f}  1.00  0.00           C  \n")
    source_atoms=list(atoms)
    for position,x in ((1,D(700)),(2,D(800))):
        source=SimpleNamespace(pdb_id='1BWV',chain_id='solvent',operator_id='1',source_atom_id='water'+str(position),
            label_seq_id='.',auth_seq_id=str(position),insertion_code='?',component_id='HOH',alternate_id='.',occupancy=D(1),atom_id='O',xyz_angstrom=(x,D(2),D(3)))
        source_atoms.append(source)
        original=dict(serial=16+position,chain='Z',position=position,atom='O',source=['1BWV','1',source.source_atom_id],source_component='HOH',model_component='HOH',source_alternate='.',source_occupancy='1',original_xyz_angstrom=[str(x),'2','3'])
        origin['selected_atom_origins'].append(original)
        complete=dict(chain='Z',position=position,atom='O',component='HOH',element='O',source_origin=original,status='INHERITED_OBSERVED_SOURCE')
        origin['complete_heavy_atoms'].append(complete)
        lines.append(f"HETATM{n+position:5d}  O   HOH Z{position:4d}    {x:8.3f}{D(2):8.3f}{D(3):8.3f}  1.00  0.00           O  \n")
    order=(2,1) if swapped else (1,2)
    positions=points+[(D(700 if position==1 else 800),D(2),D(3)) for position in order]
    for offset,position in enumerate(order):
        atom=n+offset
        complete=origin['complete_heavy_atoms'][n+position-1]
        origin['amber_realization']['atoms'].append(dict(amber_atom_index=atom,amber_residue_index=atom,chain='Z',position=position,atom='O',residue_name='WAT',source_origin=complete,status='REALIZED_COMPLETE_PREPARATION_ATOM'))
    origin['amber_realization']['chemical_residue_map']=[dict(chain='Z',position=position,amber_residue_index=n+order.index(position)) for position in (1,2)]
    if duplicate_added:
        atom=n+2
        positions.append((D(700),D(2),D(3)))
        origin['amber_realization']['atoms'].append(dict(amber_atom_index=atom,amber_residue_index=atom,chain=None,position=None,atom='O',residue_name='WAT',source_origin=None,status='DECLARED_ADDED_SOLVENT_OR_NEUTRALIZING_ION'))
    count=len(positions)
    census=dict(census,term_census=dict(atoms=count),residue_starts=tuple(range(1,count+1)),
        residue_names=census['residue_names']+('WAT',)*(count-n),atom_names=census['atom_names']+('O',)*(count-n),
        atomic_numbers=census['atomic_numbers']+(8,)*(count-n))
    coordinates=[(x+10,y+20,z+30) for x,y,z in positions]
    return [model,census,origin,''.join(lines),inpcrd(coordinates,box=(2000,2000,2000,90,90,90)),tuple(source_atoms),chains,set()]


def test_complete_same_wat_permutation_is_independently_proven_and_legacy_unchanged():
    args=exposed()
    model,census,origin,heavy,restart,atoms,chains,bonds=args
    with pytest.raises(ValueError,match='full chain/residue map'):
        validate_origins(model,census,origin,heavy,atoms,chains,bonds)
    before=deepcopy(origin)
    result=validate_origins_from_coordinates(*args)
    assert origin==before and result.method==COORDINATE_ORIGIN_METHOD
    assert result.complete_heavy_atom_count==5050 and result.complete_source_group_count==5050
    assert result.chemical_residue_map==(('Z',1,5049),('Z',2,5048))


def test_coherent_false_water_origin_map_cannot_pass_coordinate_successor():
    args=exposed();origin=args[2]
    rows=origin['amber_realization']['atoms'][-2:]
    rows[0]['position'],rows[1]['position']=rows[1]['position'],rows[0]['position']
    rows[0]['source_origin'],rows[1]['source_origin']=rows[1]['source_origin'],rows[0]['source_origin']
    origin['amber_realization']['chemical_residue_map']=[dict(chain='Z',position=1,amber_residue_index=5048),dict(chain='Z',position=2,amber_residue_index=5049)]
    with pytest.raises(ValueError,match='shared serialization translation'):
        validate_origins_from_coordinates(*args)


def test_global_duplicate_candidate_is_refused_instead_of_picking_one_water():
    with pytest.raises(ValueError,match='unique complete raw candidate'):
        validate_origins_from_coordinates(*exposed(duplicate_added=True))


def test_coordinate_proof_refuses_before_lower_predicates_are_entered(monkeypatch):
    from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import preparation_integrity

    monkeypatch.setattr(preparation_integrity,'validate_origins',lambda *args,**kwargs:pytest.fail('lower predicates entered before coordinate proof'))
    with pytest.raises(ValueError,match='unique complete raw candidate'):
        validate_origins_from_coordinates(*exposed(duplicate_added=True))


def test_final_translation_refinement_cannot_hide_protein_frame_ambiguity():
    args=exposed(duplicate_added=True)
    n=args[1]['term_census']['atoms']
    points=[(D(i)/10+10,D(22),D(33)) for i in range(n-3)]
    # The second source water refines the global translation to its upper
    # boundary. The extra native water remains a competing candidate in the
    # independently frozen protein frame, though the final interval hides it.
    points += [(D('810.0000001'),D(22),D(33)),(D(710),D(22),D(33)),(D('709.9999999'),D(22),D(33))]
    args[4]=inpcrd(points,box=(2000,2000,2000,90,90,90))
    with pytest.raises(ValueError,match='unique complete raw candidate'):
        validate_origins_from_coordinates(*args)


@pytest.mark.parametrize('mutation',['missing','duplicate','overlap','out-of-range','wrong-element','wrong-component','missing-original'])
def test_complete_shape_source_group_and_true_absence_falsifiers(mutation):
    args=exposed();census,origin=args[1],args[2]
    mapping=origin['amber_realization']['chemical_residue_map']
    if mutation=='missing':mapping.pop()
    if mutation=='duplicate':mapping.append(dict(mapping[0]))
    if mutation=='overlap':mapping[1]['amber_residue_index']=mapping[0]['amber_residue_index']
    if mutation=='out-of-range':mapping[0]['amber_residue_index']=99999
    if mutation=='wrong-element':census['atomic_numbers']=census['atomic_numbers'][:-1]+(11,)
    if mutation=='wrong-component':census['residue_names']=census['residue_names'][:-1]+('Na+',)
    if mutation=='missing-original':origin['amber_realization']['atoms'][-1]['status']='DECLARED_ADDED_SOLVENT_OR_NEUTRALIZING_ION'
    with pytest.raises(ValueError):validate_origins_from_coordinates(*args)
