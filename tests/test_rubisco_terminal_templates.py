# SPDX-License-Identifier: MPL-2.0
"""Geometry and immutability controls for an exposed three-residue chain."""
from copy import deepcopy
import math

import numpy as np
import pytest

from empirical_lawhood.domains.rubisco.rubisco_response.gp_geometry_repair_assessment import _omega_degrees
from empirical_lawhood.domains.rubisco.rubisco_response.gp_heavy_geometry import inspect_heavy_geometry
from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology import heavy_pdb_rows
from empirical_lawhood.domains.rubisco.rubisco_response.terminal_templates import build_terminals, place, read_templates


def fixture(missing=(1,3)):
    base={"N":np.array((-1.4,0.,0.)),"CA":np.zeros(3),"C":np.array((.5,1.4,0.)),
          "O":np.array((1.5,1.5,0.)),"CB":np.array((0.,0.,-1.5))}
    terminal={**base,"OXT":np.array((.3,2.6,0.))}
    libraries={name:(deepcopy(points),{n:7 if n=="N" else 8 if n.startswith("O") else 6 for n in points})
               for name,points in (("NALA",base),("ALA",base),("CALA",terminal))}
    lines=["REMARK EXPOSED STARTING-GEOMETRY CONTROL\n"];origins=[];serial=1
    for pos in (1,2,3):
        for name,point in (terminal if pos==3 else base).items():
            xyz=point+np.array((20.*(pos-2),0.,0.))
            element=name[0]
            lines.append(f"ATOM  {serial:5d} {' '+name:<4s} ALA A{pos:4d}    "
                         f"{xyz[0]:8.3f}{xyz[1]:8.3f}{xyz[2]:8.3f}  1.00  0.00          {element:>2s}  \n")
            origins.append(dict(chain="A",position=pos,component="ALA",atom=name,element=element,
                status="DECLARED_CONSTRUCTED_MUTANT_OR_MISSING_ATOM" if pos in missing else "INHERITED_OBSERVED_SOURCE",
                source_origin=None if pos in missing else {"exposed":True}))
            serial+=1
    return "".join(lines)+"END\n",{"complete_heavy_atoms":origins},libraries


def construct(text,origin,libraries):
    return build_terminals(text,origin,libraries,peptide_length=1.335,
        ca_c_n_angle=math.radians(116.6),c_n_ca_angle=math.radians(121.9))


@pytest.mark.parametrize("torsion",(-167.,-60.,0.,45.,180.))
@pytest.mark.numerical(oracle="Independent norms, dot-product angle and atan2 plane-normal dihedral verify prescribed 1.335-A bond, 116.6-degree angle and signed torsion.")
def test_internal_coordinate_placement_matches_independent_dihedral(torsion):
    a,b,c=(np.array(x,float) for x in ((0,1,0),(0,0,0),(1,0,0)))
    d=place(a,b,c,1.335,math.radians(116.6),math.radians(torsion))
    assert np.linalg.norm(d-c)==pytest.approx(1.335,abs=1e-14)
    theta=math.degrees(math.acos(np.dot(b-c,d-c)/(np.linalg.norm(b-c)*np.linalg.norm(d-c))))
    assert theta==pytest.approx(116.6,abs=1e-12)
    actual=_omega_degrees((a,b,c,d))
    assert abs(math.remainder(actual-torsion,360))<1e-12


def test_both_terminal_directions_preserve_observed_bytes_and_trans_peptides():
    text,origin,libraries=fixture()
    result,events,moving=construct(text,origin,libraries)
    assert len(events)==2 and len(moving)==11
    before=text.splitlines();after=result.splitlines()
    assert len(before)==len(after)
    for old,new in zip(before,after,strict=True):
        assert old[:30]==new[:30] and old[54:]==new[54:]
        if not old.startswith("ATOM") or int(old[22:26])==2:assert old==new
    rows=heavy_pdb_rows(result);geometry=inspect_heavy_geometry(rows)
    assert not geometry["backbone_anomalies_squared_angstrom"]
    assert not geometry["stereochemistry_anomalies_angstrom3"]
    atoms={(c,p,n):xyz for c,p,r,n,e,xyz in rows}
    for p in (1,2):
        angle=_omega_degrees([atoms["A",p,"CA"],atoms["A",p,"C"],atoms["A",p+1,"N"],atoms["A",p+1,"CA"]])
        assert abs(angle)>179.8


def test_terminal_constructor_refuses_internal_loops_and_partial_observed_backbones():
    text,origin,libraries=fixture((2,))
    with pytest.raises(ValueError,match="internal loops"):construct(text,origin,libraries)
    text,origin,libraries=fixture()
    origin["complete_heavy_atoms"][0].update(status="INHERITED_OBSERVED_SOURCE",source_origin={"exposed":True})
    with pytest.raises(ValueError,match="partial residue"):construct(text,origin,libraries)


def test_template_identity_cannot_substitute_atoms_or_elements():
    text,origin,libraries=fixture()
    libraries["NALA"][1]["CA"]=7
    with pytest.raises(ValueError,match="element"):construct(text,origin,libraries)
    _,_,libraries=fixture();libraries["NALA"][0]["CBX"]=libraries["NALA"][0].pop("CB")
    with pytest.raises(ValueError,match="atom census"):construct(text,origin,libraries)


def test_template_reader_retains_named_heavy_coordinates_and_rejects_incomplete_data():
    text='!entry.EXP.unit.atoms table\n "CA" "CX" 0 1 0 1 6 0.0\n "HA" "H1" 0 1 0 2 1 0.0\n'
    text+='!entry.EXP.unit.positions table\n 1.0 2.0 3.0\n 1.5 2.0 3.0\n'
    points,elements=read_templates(text)["EXP"]
    assert elements=={"CA":6} and np.array_equal(points["CA"],(1.,2.,3.))
    with pytest.raises(ValueError,match="denominator"):read_templates(text.rsplit(" 1.5",1)[0])
    with pytest.raises(ValueError,match="repeats"):read_templates(text+text)
    with pytest.raises(ValueError,match="nonfinite"):read_templates(text.replace("1.0 2.0 3.0","nan 2.0 3.0"))


def test_best_pose_is_refused_when_every_candidate_fails_the_feasibility_bound(monkeypatch):
    from empirical_lawhood.domains.rubisco.rubisco_response import terminal_templates as owner
    original = owner.StericEnvironment.score
    def infeasible(self, *args, **kwargs):
        score, _ = original(self, *args, **kwargs)
        return score, 1.2
    monkeypatch.setattr(owner.StericEnvironment, "score", infeasible)
    text, origin, libraries = fixture()
    with pytest.raises(ValueError, match="no feasible"):
        construct(text, origin, libraries)
