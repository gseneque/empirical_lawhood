# SPDX-License-Identifier: MPL-2.0
"""Exposed stereochemical transformations and immutable-coordinate controls."""

from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.domains.rubisco.rubisco_response.gp_constructed_geometry import _omega, initialize_constructed_geometry, origin_mobility, replace_heavy_coordinates
from empirical_lawhood.adapters.rubisco.rubisco_response.fixed_coordinate_mm import FixedCoordinateObjective
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.serialized_heavy_pdb import read_serialized_heavy_pdb


def fixture(coordinates, *, component="ALA", constructed=None):
    names = tuple(coordinates)
    constructed = set(names) if constructed is None else set(constructed)
    text = "REMARK EXPOSED GEOMETRY CONTROL\n"
    origin = {"complete_heavy_atoms":[]}
    for i,(name,xyz) in enumerate(coordinates.items(),1):
        element = name[0]
        text += f"ATOM  {i:5d} {' '+name:<4s} {component} A   1    {''.join(f'{x:8.3f}' for x in xyz)}  1.00  0.00          {element:>2s}  \n"
        moving = name in constructed
        origin["complete_heavy_atoms"].append(dict(chain="A",position=1,atom=name,component=component,element=element,
            status="DECLARED_CONSTRUCTED_MUTANT_OR_MISSING_ATOM" if moving else "INHERITED_OBSERVED_SOURCE",
            source_origin=None if moving else {"exposed":True}))
    return text+"END\n",origin


def points(text):
    return {a["atom"]:np.array(a["xyz"],float) for a in read_serialized_heavy_pdb(text).atoms}


def test_alpha_reflection_preserves_backbone_and_every_sidechain_internal_distance():
    text,origin=fixture({"N":(1,0,0),"CA":(0,0,0),"C":(0,1,0),"O":(1,1,0),
        "CB":(0,0,-1),"CG":(0,1,-2),"CD":(0,2,-3)},component="LEU",constructed=("CB","CG","CD"))
    result,changes,mobile=initialize_constructed_geometry(text,origin)
    before,after=points(text),points(result)
    assert len(changes)==1 and len(mobile)==3 and after["CB"][2]>0
    for a in before:
        for b in before:
            assert np.linalg.norm(before[a]-before[b]) == pytest.approx(np.linalg.norm(after[a]-after[b]))
    for old,new in zip(text.splitlines(),result.splitlines(),strict=True):
        assert old[:30]==new[:30] and old[54:]==new[54:]
        if old.startswith("ATOM") and old[12:16].strip() not in {"CB","CG","CD"}:assert old==new


@pytest.mark.parametrize("component,branch",(("ILE","CG1"),("THR","OG1")))
def test_beta_reflection_keeps_its_three_bonds_and_other_branch(component,branch):
    text,origin=fixture({"N":(0,-1,0),"CA":(1,0,0),"C":(0,0,1),"CB":(0,0,0),
        branch:(0,1,0),"CG2":(0,0,-1)},component=component,constructed=("CG2",))
    # This fixture has the specified positive alpha centre and negative beta centre.
    result,changes,_=initialize_constructed_geometry(text,origin)
    assert tuple(c["kind"] for c in changes)==("constructed-CB-reflection",)
    assert points(result)["CG2"][2]==1
    assert np.array_equal(points(result)[branch],points(text)[branch])


@pytest.mark.parametrize("value",(-1,0))
def test_invalid_observed_or_planar_stereochemistry_cannot_be_silently_repaired(value):
    text,origin=fixture({"N":(1,0,0),"CA":(0,0,0),"C":(0,1,0),"CB":(0,0,value)},
        constructed=() if value else ("CB",))
    with pytest.raises(ValueError,match="observed|planar"):initialize_constructed_geometry(text,origin)


def test_origin_census_and_coordinate_permissions_are_complete():
    text,origin=fixture({"N":(1,0,0),"CA":(0,0,0)},constructed=("N",))
    with pytest.raises(ValueError,match="observed"):replace_heavy_coordinates(text,{("A",1,"CA"):(2,2,2)},(("A",1,"N"),))
    with pytest.raises(ValueError,match="observed"):replace_heavy_coordinates(text,{("A",1,"X"):(2,2,2)},(("A",1,"X"),))
    origin["complete_heavy_atoms"].append(origin["complete_heavy_atoms"][0])
    with pytest.raises(ValueError,match="census"):origin_mobility(text,origin)


def test_degenerate_peptide_axis_refuses_without_nan():
    with pytest.raises(ValueError,match="degenerate"):
        _omega([np.array(v,float) for v in ((1,0,0),(0,0,0),(0,0,0),(0,1,0))])


def test_optimizer_has_no_coordinates_for_fixed_atoms_and_cannot_mutate_original():
    original=np.arange(12,dtype=float).reshape(4,3)
    context=SimpleNamespace(getSystem=lambda:SimpleNamespace(getNumParticles=lambda:4))
    objective=FixedCoordinateObjective(context,original,(1,3))
    original[:]=99
    result=objective.complete_coordinates(np.zeros(6))
    assert np.array_equal(result[[0,2]],np.arange(12,dtype=float).reshape(4,3)[[0,2]])
    result[:]=999
    assert np.array_equal(objective.complete_coordinates(np.ones(6))[[0,2]],np.arange(12,dtype=float).reshape(4,3)[[0,2]])
    with pytest.raises(ValueError):objective.coordinates[0,0]=1
    for invalid in (np.zeros(9),np.full(6,np.nan)):
        with pytest.raises(ValueError):objective.complete_coordinates(invalid)
    with pytest.raises(ValueError):FixedCoordinateObjective(context,np.zeros((3,3)),(1,))
