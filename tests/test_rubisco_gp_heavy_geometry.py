# SPDX-License-Identifier: MPL-2.0
"""Independent close-pair oracle and adverse upstream coordinate controls."""

from decimal import Decimal as D
from itertools import combinations
from types import SimpleNamespace

import pytest

from empirical_lawhood.domains.rubisco.rubisco_response.gp_heavy_geometry import heavy_stereochemistry, inspect_heavy_geometry, require_initial_heavy_geometry


def row(chain, position, name, xyz):
    return chain,position,"ALA",name,"C",tuple(D(str(v)) for v in xyz)


@pytest.mark.numerical(oracle="Independent exhaustive unordered-pair Decimal distances check the cell-list contact population across negative boundaries and chains.")
def test_complete_cell_search_matches_all_pairs_across_chains_and_negative_cells():
    rows = tuple(row(chr(65+i%4),i+1,"X",xyz) for i,xyz in enumerate((
        (-1.01,0,0),(-0.99,0,0),(0,0,0),(0.99,0,0),(1,0,0),(2,0,0),
        (0,0.99,0.99),(0,-0.01,-0.01),(-1.999,-1.999,-1.999),(-2.001,-2.001,-2.001))))
    expected=[]
    for a,b in combinations(rows,2):
        d2=sum((x-y)**2 for x,y in zip(a[-1],b[-1],strict=True))
        if d2<D(1):expected.append((*sorted(((a[0],a[1],a[3]),(b[0],b[1],b[3]))),d2))
    result=inspect_heavy_geometry(rows)
    assert result["short_contacts_squared_angstrom"] == tuple(sorted(expected))
    assert result["all_unordered_pair_count"] == len(rows)*(len(rows)-1)//2
    assert result["gross_geometry_disposition"] == "FALSIFIED"
    assert result["physical_geometry_admission"] == "UNEVALUABLE"


@pytest.mark.numerical(oracle="Exact Decimal distances1 and0.999999999999 lie on opposite sides of the strict1-Angstrom contact threshold.")
def test_exact_cutoff_is_not_rounded_into_a_false_contact():
    a=row("A",1,"X",(0,0,0))
    assert not inspect_heavy_geometry((a,row("B",1,"X",(1,0,0))))["short_contacts_squared_angstrom"]
    assert inspect_heavy_geometry((a,row("B",1,"X",("0.999999999999",0,0))))["short_contacts_squared_angstrom"]


@pytest.mark.numerical(oracle="The CA-C separation3.41-1.46=1.95 Angstrom has squared length3.8025 and exceeds the declared1.8-Angstrom upper bound.")
def test_backbone_stretch_is_detected_when_no_atoms_overlap():
    rows=(row("A",1,"N",(0,0,0)),row("A",1,"CA",(1.46,0,0)),row("A",1,"C",(3.41,0,0)),
          row("A",2,"N",(4.74,0,0)))
    result=inspect_heavy_geometry(rows)
    assert not result["short_contacts_squared_angstrom"] and result["backbone_bond_count"] == 3
    assert result["backbone_anomalies_squared_angstrom"] == ((("A",1,"CA"),("A",1,"C"),D("3.8025")),)
    assert result["gross_geometry_disposition"] == "FALSIFIED"


def test_good_gross_geometry_leaves_physical_admission_unresolved():
    result=inspect_heavy_geometry((row("A",1,"N",(0,0,0)),row("A",1,"CA",(1.46,0,0))))
    assert result["gross_geometry_disposition"] == "SATISFIED"
    assert result["physical_geometry_admission"] == "UNEVALUABLE"


@pytest.mark.parametrize("component,centre,names",(("ALA","CA",("N","C","CB")),
    ("CYS","CA",("N","C","CB")),("ILE","CB",("CA","CG1","CG2")),("THR","CB",("CA","OG1","CG2"))))
@pytest.mark.numerical(oracle="The three Cartesian unit vectors have determinant+1; reflection of one vector gives-1 and a coplanar replacement gives0 for every named stereocentre.")
def test_mirrored_or_planar_protein_stereocentres_are_refused(component,centre,names):
    coordinates={centre:(0,0,0),names[0]:(1,0,0),names[1]:(0,1,0),names[2]:(0,0,1)}
    def rows(values):return tuple(("A",1,component,name,"C",tuple(map(D,xyz))) for name,xyz in values.items())
    assert heavy_stereochemistry(rows(coordinates)) == (1,())
    coordinates[names[2]]=(0,0,-1)
    assert heavy_stereochemistry(rows(coordinates)) == (1,((("A",1,centre),D(-1)),))
    coordinates[names[2]]=(1,1,0)
    assert heavy_stereochemistry(rows(coordinates)) == (1,((("A",1,centre),D(0)),))


@pytest.mark.parametrize("kind",("empty","duplicate","nan","hydrogen"))
def test_incomplete_or_unsupported_atom_rows_refuse(kind):
    a=row("A",1,"X",(0,0,0))
    rows=() if kind=="empty" else (a,a) if kind=="duplicate" else (
        (*a[:-1],(D("NaN"),D(0),D(0))),) if kind=="nan" else ((*a[:4],"H",a[-1]),)
    with pytest.raises(ValueError):inspect_heavy_geometry(rows)


def test_all_arms_are_assessed_and_bad_arm_refuses_before_authoring_io(monkeypatch):
    from empirical_lawhood.domains.rubisco.rubisco_response import gp_initial_topology as formats
    from empirical_lawhood.api.domain_composition.rubisco_response.initial_amber import author_initial_gp_amber
    visited=[]
    def read(text):
        visited.append(text)
        return (row("A",1,"X",(0,0,0)),row("B",1,"X",(0.3 if text=="bad" else 2,0,0)))
    monkeypatch.setattr(formats,"heavy_pdb_rows",read)
    source=SimpleNamespace(models=tuple(SimpleNamespace(name=name,heavy_pdb=text,material=SimpleNamespace(chains=()),chain_map=()) for name,text in
        (("m1-wt","good1"),("m1-i95m","bad"),("v1-wt","good2"),("v1-i95m","good3"))))
    with pytest.raises(ValueError,match="m1-i95m: 1 sub-Angstrom"):
        require_initial_heavy_geometry(source)
    assert visited==["good1","bad","good2","good3"]
    with pytest.raises(ValueError,match="before Amber entry"):
        author_initial_gp_amber(source=source,project_root=None,work_directory=None,artifact_writer=None,output_dir=None)
