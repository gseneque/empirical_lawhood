# SPDX-License-Identifier: MPL-2.0
"""Exposed coordinate/math controls, never an actual/native model result."""

from dataclasses import replace
from decimal import Context, Decimal as D, localcontext
from fractions import Fraction as F
from hashlib import sha256
import os
from pathlib import Path
import subprocess
import sys

import pytest

from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import physical_preparation_geometry as g
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.amber_parameters import assigned_census, read_prmtop
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.preparation_integrity import assess
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from tests.test_rubisco_preparation_integrity import amber_text, exposed_preparation, topology


def stock():
    rows = topology()
    rows["POINTERS"][27] = 1
    rows["BOX_DIMENSIONS"] = [D(90),D(20),D(20),D(20)]
    return rows


POINTS = ((D(0),D(0),D(0)),(D(1),D(0),D(0)),(D(1),D(1),D(0)),(D(1),D(1),D(1)))


def inpcrd(points=POINTS,box=(20,20,20,90,90,90),time=None):
    values = [value for row in points for value in row]
    result = ["exposed original coordinates\n",str(len(points))+(" "+str(time) if time is not None else "")+"\n"]
    result.extend("".join(f"{value:12.7f}" for value in values[index:index+6])+"\n" for index in range(0,len(values),6))
    result.append("".join(f"{D(value):12.7f}" for value in box)+"\n")
    return "".join(result)


def heavy_pdb(points=POINTS):
    names,elements = ("C","N","CA"),("C","N","C")
    return "".join(f"ATOM  {index+1:5d} {name:^4s} ALA A   1    {float(x):8.3f}{float(y):8.3f}{float(z):8.3f}  1.00  0.00          {element:>2s}  \n"
        for index,(name,element,(x,y,z)) in enumerate(zip(names,elements,points[:3],strict=True)))


def origins():
    names = ("C","N","CA","H")
    return {"amber_realization":{"atoms":[dict(amber_atom_index=index,amber_residue_index=0,
        atom=name,residue_name="ALA",chain="A",position=1,
        source_origin={"declared":"exposed-built-heavy"} if index < 3 else None,
        status="REALIZED_COMPLETE_PREPARATION_ATOM" if index < 3 else "DECLARED_AMBER_ADDED_HYDROGEN")
        for index,name in enumerate(names)]}}


def diagnostic(points=POINTS,sections=None,pdb=None,origin=None):
    return g.diagnose_geometry(amber_text(stock() if sections is None else sections),inpcrd(points),
        heavy_pdb(points) if pdb is None else pdb,origins() if origin is None else origin)


def test_literal_full_coordinate_pair_bonded_denominator_and_claim_ceiling():
    result = diagnostic()
    assert result.atom_count == 4 and result.heavy_atom_count == 3
    assert result.pair_counts == (("ordinary",3),("excluded-non14",3),("active14",0))
    assert result.raw_interaction_counts == (4,1,3,1,1,0)
    assert result.bonded_counts == (("bonds",2),("angles",1),("dihedrals",1),("bonds-zero-leg",0),
                                   ("angles-zero-leg",0),("dihedrals-zero-leg",0),("dihedrals-undefined-plane",0))
    assert result.positive_lj_counts == (("ordinary",0),("active14",0))
    assert result.positive_lj_census_sha256 == sha256(b"").hexdigest()
    assert result.hard_geometry_disposition is A.SATISFIED
    assert result.geometry_adequacy is result.force_adequacy is result.relaxation_adequacy is result.chemical_adequacy is A.UNEVALUABLE
    assert result.interpretation.startswith("DERIVED_RETAINED_LEXICAL_INPUT")
    with pytest.raises(ValueError,match="physical adequacy"):
        replace(result,geometry_adequacy=A.SATISFIED)


def test_hand_computed_source_positive_contact_is_finite_diagnostic_not_rejection():
    points = (POINTS[0],POINTS[1],(D('.5'),D('.5'),D(0)),POINTS[3])
    result = diagnostic(points)
    # Ordinary0/2 source table is A64/B8; r²=1/2 gives64*64-8*8=4032.
    assert dict(result.positive_lj_counts)["ordinary"] == 1
    assert result.maximum_lj_pair == (0,2,"ordinary",1,(1,2),(4032,1))
    assert result.hard_geometry_disposition is A.SATISFIED
    assert result.geometry_adequacy is A.UNEVALUABLE


def test_exact_sign_boundary_and_cross_table_not_combination_rules():
    rows = stock()
    rows["LENNARD_JONES_ACOEF"] = [D(64),D(123),D(256)]
    rows["LENNARD_JONES_BCOEF"] = [D(8),D(45),D(32)]
    # 0/2 distance sqrt2 is exact zero in its original A64/B8 table.
    assert dict(diagnostic(sections=rows).positive_lj_counts)["ordinary"] == 0
    points = (POINTS[0],POINTS[1],POINTS[2],(D('-.5'),D(0),D(0)))
    result = diagnostic(points,sections=rows)
    # Cross0/3 actual source123/45, r=.5:123*4096-45*64=500928.
    assert result.maximum_lj_pair == (0,3,"ordinary",2,(1,4),(500928,1))


def test_exact_rational_contact_arithmetic_does_not_use_decimal_context():
    points = (POINTS[0],POINTS[1],(D('.5'),D('.5'),D(0)),POINTS[3])
    raw,pdb = inpcrd(points),heavy_pdb(points)
    topology_text = amber_text(stock())
    with localcontext(Context(prec=2)):
        result = g.diagnose_geometry(topology_text,raw,pdb,origins())
    assert result.maximum_lj_pair[-1] == (4032,1)


@pytest.mark.parametrize("mutation",["wrong-count","truncated","extra","nonfinite","no-box","zero-box","time-extra"])
def test_malformed_coordinate_inputs_fail_before_geometry_claim(mutation):
    raw = inpcrd()
    if mutation == "wrong-count": raw = raw.replace("\n4\n","\n5\n")
    if mutation == "truncated": raw = "\n".join(raw.splitlines()[:-2])+"\n"
    if mutation == "extra": raw = raw.replace("  1.0000000\n","  1.0000000  9.0000000\n",1)
    if mutation == "nonfinite": raw = raw.replace("   0.0000000","         NaN",1)
    if mutation == "no-box": raw = "\n".join(raw.splitlines()[:-1])+"\n"
    if mutation == "zero-box": raw = inpcrd(box=(0,20,20,90,90,90))
    if mutation == "time-extra": raw = raw.replace("\n4\n","\n4 0 1\n")
    with pytest.raises(ValueError): g.read_inpcrd(raw,4)


@pytest.mark.parametrize("mutation",["triclinic","velocity","tiny","nonascii"])
def test_unsupported_coordinate_views_remain_explicit(mutation):
    raw = inpcrd()
    n = 4
    if mutation == "triclinic": raw = inpcrd(box=(20,20,20,90,109,90))
    if mutation == "velocity": raw = "\n".join(raw.splitlines()[:-1]+raw.splitlines()[2:4]+raw.splitlines()[-1:])+"\n"
    if mutation == "tiny": n = 2
    if mutation == "nonascii": raw = "nonASCIIα\n"+raw
    with pytest.raises(g.UnsupportedGeometry): g.read_inpcrd(raw,n)


def test_topology_box_join_uses_serialization_cells_and_refuses_changed_dimensions():
    sections = read_prmtop(amber_text(stock()))
    g._box_join(sections,(F('20.0000001'),F(20),F(20)))
    with pytest.raises(ValueError,match="serialization"):
        g._box_join(sections,(F('20.001'),F(20),F(20)))


def test_full_origin_order_component_element_and_pdb_coordinate_joins():
    moved = tuple(tuple(value+D(3) for value in row) for row in POINTS)
    result = diagnostic(moved,pdb=heavy_pdb())
    assert result.common_translation_intervals[0] == ((59999999,20000000),(60000001,20000000))
    shifted = list(moved); shifted[2] = (shifted[2][0]+D('.001'),*shifted[2][1:])
    with pytest.raises(ValueError,match="translation"):
        diagnostic(tuple(shifted),pdb=heavy_pdb())
    for field,value in (("amber_atom_index",1),("atom","X"),("residue_name","KCX"),("source_origin",None)):
        changed = origins(); changed["amber_realization"]["atoms"][0][field] = value
        with pytest.raises(ValueError): diagnostic(origin=changed)
    changed = origins(); changed["amber_realization"]["atoms"].pop()
    with pytest.raises(ValueError,match="mapping"): diagnostic(origin=changed)


def test_exclusion_direction_placeholders_and_selected_native1_4_flags():
    rows = stock()
    rows["EXCLUDED_ATOMS_LIST"] = [0,1,2,3]
    rows["DIHEDRALS_WITHOUT_HYDROGEN"] = [0,3,6,9,1]
    sections = read_prmtop(amber_text(rows))
    excluded,active,counts,raw = g.interaction_partition(sections,assigned_census(sections))
    assert excluded == {(0,1),(1,2),(2,3)} and active == {(0,3):(F(6,5),F(2))}
    assert counts == (2,3,1) and raw == (4,1,3,0,0,0)
    result = diagnostic(sections=rows)
    assert dict(result.pair_counts)["active14"] == 1
    for third,fourth in ((-6,9),(6,-9),(0,9),(6,0)):
        rows["DIHEDRALS_WITHOUT_HYDROGEN"] = [0,3,third,fourth,1]
        sections = read_prmtop(amber_text(rows))
        assert g.interaction_partition(sections,assigned_census(sections))[1] == {}


def test_duplicate_active1_4_and_self_directed_exclusion_refuse_without_deduplication():
    rows = stock(); rows["POINTERS"][7] = 2
    rows["DIHEDRALS_WITHOUT_HYDROGEN"] = [0,3,6,9,1]*2
    with pytest.raises(ValueError,match="duplicate active"):
        diagnostic(sections=rows)
    rows = stock(); rows["EXCLUDED_ATOMS_LIST"][0] = 1
    with pytest.raises(ValueError,match="self/duplicate"):
        diagnostic(sections=rows)


def test_zero_lj_source_pairs_keep_denominator_and_mixed_zero_is_unsupported():
    rows = stock(); rows["LENNARD_JONES_ACOEF"] = [D(0)]*3; rows["LENNARD_JONES_BCOEF"] = [D(0)]*3
    result = diagnostic(sections=rows)
    assert sum(number for _,number in result.pair_counts) == 6 and result.maximum_lj_pair is None
    rows["LENNARD_JONES_ACOEF"][0] = D(1)
    with pytest.raises(g.UnsupportedGeometry,match="mixed-zero"):
        diagnostic(sections=rows)


def test_exact_singular_input_is_separate_from_finite_repulsive_contact():
    points = (POINTS[0],POINTS[1],POINTS[0],POINTS[3])
    result = diagnostic(points)
    assert result.coincident_unwrapped_pair_count == result.singular_interacting_pair_count == 1
    assert result.hard_geometry_disposition is A.FALSIFIED
    assert result.geometry_adequacy is result.force_adequacy is A.UNEVALUABLE


def test_periodic_boundary_contacts_and_small_wrapped_grid_are_counted_once():
    rows = stock(); rows["BOX_DIMENSIONS"] = [D(90),D(2),D(2),D(2)]
    points = ((D('.1'),D('.1'),D('.1')),(D('.1'),D('.1'),D('1.1')),
              (D('1.9'),D('.1'),D('.1')),(D('1.9'),D('.1'),D('1.1')))
    result = g.diagnose_geometry(amber_text(rows),inpcrd(points,box=(2,2,2,90,90,90)),heavy_pdb(points),origins())
    assert result.ordinary_candidate_count == 3
    assert dict(result.positive_lj_counts)["ordinary"] == 3
    assert result.maximum_lj_pair[:5] == (1,3,"ordinary",3,(1,25))
    assert result.maximum_lj_pair[-1] == (62499500000,1)


def test_active1_4_diagnostic_uses_unwrapped_distance_and_exact_source_scnb():
    rows = stock(); rows["DIHEDRALS_WITHOUT_HYDROGEN"] = [0,3,6,9,1]
    points = (POINTS[0],POINTS[1],POINTS[2],(D('-.5'),D(0),D(0)))
    result = diagnostic(points,sections=rows)
    assert dict(result.positive_lj_counts)["active14"] == 1
    # Cross128/16 at r=.5 gives523264/SCNB2 =261632, unwrapped.
    assert result.maximum_lj_pair == (0,3,"active14",2,(1,4),(261632,1))


def test_active1_4_is_not_silently_given_periodic_ordinary_distance():
    rows = stock(); rows["BOX_DIMENSIONS"] = [D(90),D(2),D(2),D(2)]
    rows["DIHEDRALS_WITHOUT_HYDROGEN"] = [0,3,6,9,1]
    points = (POINTS[0],POINTS[1],POINTS[2],(D('1.9'),D(0),D(0)))
    result = g.diagnose_geometry(amber_text(rows),inpcrd(points,box=(2,2,2,90,90,90)),heavy_pdb(points),origins())
    # Unwrapped0/3 is1.9A and has negative LJ; ordinary minimum image0.1A
    # would be strongly positive, and is deliberately a distinct operand.
    assert dict(result.positive_lj_counts)["active14"] == 0


def test_complete_cell_search_matches_independent_quadratic_source_oracle():
    n = 36
    rows = stock(); rows["POINTERS"][0] = rows["POINTERS"][10] = n
    rows["ATOM_NAME"] = ["C","N","CA"]+["H"+str(index) for index in range(3,n)]
    rows["AMBER_ATOM_TYPE"] = ["CT","N","CT"]+["H"]*(n-3)
    rows["ATOMIC_NUMBER"] = [6,7,6]+[1]*(n-3)
    rows["MASS"] = [D(12),D(14),D(12)]+[D(1)]*(n-3)
    rows["CHARGE"] = [D(0)]*n
    rows["ATOM_TYPE_INDEX"] = [1,2,1]+[1+index%2 for index in range(3,n)]
    rows["NUMBER_EXCLUDED_ATOMS"] = [1]*n; rows["EXCLUDED_ATOMS_LIST"] = [0]*n
    points = tuple((D(index%6)*D('.731'),D(index//6)*D('.683'),D(index%3)*D('.127')) for index in range(n))
    origin = origins()
    origin["amber_realization"]["atoms"] += [dict(amber_atom_index=index,amber_residue_index=0,
        atom=rows["ATOM_NAME"][index],residue_name="ALA",chain="A",position=1,source_origin=None,
        status="DECLARED_AMBER_ADDED_HYDROGEN") for index in range(4,n)]
    origin["amber_realization"]["atoms"][3]["atom"] = rows["ATOM_NAME"][3]
    result = diagnostic(points,sections=rows,origin=origin)
    positive,stream = 0,sha256()
    for second in range(n):
        for first in range(second):
            r2 = sum((F(points[first][axis])-F(points[second][axis]))**2 for axis in range(3))
            slot = rows["NONBONDED_PARM_INDEX"][(rows["ATOM_TYPE_INDEX"][first]-1)*2+rows["ATOM_TYPE_INDEX"][second]-1]
            a,b = F(rows["LENNARD_JONES_ACOEF"][slot-1]),F(rows["LENNARD_JONES_BCOEF"][slot-1])
            # Independent exhaustive oracle, no cell/radius/exclusion helper.
            energy = a/r2**6-b/r2**3
            if energy > 0:
                positive += 1
                row = (first,second,"ordinary",slot,(r2.numerator,r2.denominator),(energy.numerator,energy.denominator))
                raw = canonical_json_bytes(row); stream.update(len(raw).to_bytes(8,"big")); stream.update(raw)
    assert result.pair_counts == (("ordinary",630),("excluded-non14",0),("active14",0))
    assert dict(result.positive_lj_counts)["ordinary"] == positive
    assert result.positive_lj_census_sha256 == stream.hexdigest()
    assert result.ordinary_candidate_count <= 630


def test_count_and_exact_rational_contracts_reject_boolean_or_thinned_products():
    result = diagnostic()
    for changes in (dict(atom_count=True),dict(ordinary_candidate_count=100),dict(box_lengths_angstrom=((20,2),(20,1),(20,1))),
                    dict(bonded_counts=result.bonded_counts[:-1]),dict(positive_lj_counts=(("ordinary",4),("active14",0)))):
        with pytest.raises(ValueError): replace(result,**changes)


def test_canonical_raw_diagnostic_and_complete24_projection_decode_exactly():
    row = diagnostic((POINTS[0],POINTS[1],(D('.5'),D('.5'),D(0)),POINTS[3]))
    assert decode_canonical_bytes(row.canonical_bytes(),g.GeometryDiagnostic,maximum_bytes=None) == row
    source,product,assets = exposed_preparation(A.NOT_ATTEMPTED)
    integrity = assess(source,product,assets,(),(),{})
    result = g.assess_geometry(source,product,assets,integrity)
    assert decode_canonical_bytes(result.canonical_bytes(),g.PhysicalPreparationGeometry,maximum_bytes=None) == result
    raw = result.canonical_bytes().replace(b'"NOT_ATTEMPTED"',b'"UNKNOWN_ACTUAL_NATIVE"',1)
    with pytest.raises(ValueError): decode_canonical_bytes(raw,g.PhysicalPreparationGeometry,maximum_bytes=None)


@pytest.mark.parametrize("verdict",tuple(A))
def test_all24_original_adverse_unknown_dispositions_and_claim_ceiling(verdict):
    # Existing assessor accepts retained nonpositive rows; for the SAT enum we
    # use a missing-input row, which cannot form a positive assignment receipt.
    if verdict is A.SATISFIED:
        with pytest.raises(ValueError): exposed_preparation(verdict)
        return
    source,product,assets = exposed_preparation(verdict)
    integrity = assess(source,product,assets,(),(),{})
    result = g.assess_geometry(source,product,assets,integrity)
    assert len(result.models) == 24 and all(row.assignment_disposition is verdict for row in result.models)
    expected = A.NOT_ATTEMPTED if verdict is A.NOT_ATTEMPTED else A.UNEVALUABLE
    assert all(row.diagnostic_disposition is expected and row.diagnostic is None for row in result.models)
    assert result.geometry_adequacy is result.native_coverage is result.force_adequacy is result.relaxation_adequacy is A.UNEVALUABLE
    assert result.actual_native_attempt_count is result.actual_native_completion_count is None and result.physical_independent_units == 0
    for changed in (replace(result.models[0],assignment_disposition=A.UNEVALUABLE),):
        assert changed.assignment_disposition is A.UNEVALUABLE
    with pytest.raises(ValueError,match="24"):
        replace(result,models=result.models[:-1])
    with pytest.raises(ValueError,match="admission"):
        replace(result,force_adequacy=A.SATISFIED)


def test_complete24_source_and_asset_custody_cannot_be_relabelled():
    source,product,assets = exposed_preparation(A.NOT_ATTEMPTED)
    integrity = assess(source,product,assets,(),(),{})
    with pytest.raises(ValueError,match="complete24"):
        g.assess_geometry(source,product,assets[:-1],integrity)
    with pytest.raises(ValueError,match="custody"):
        g.assess_geometry(source,product,(replace(assets[0],product_id="other.assets"),)+assets[1:],integrity)
    with pytest.raises(ValueError,match="source"):
        g.assess_geometry(replace(source,selection_id="other.selection"),product,assets,integrity)


def test_pure_successor_import_is_cold_and_never_calls_native_or_producer(tmp_path):
    source = Path(__file__).resolve().parents[1]/"src"
    code = '''
import importlib.abc
import sys
class Refuse(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        blocked = ('numpy','parmed','openmm','pdbfixer','empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.native','empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.parameter_audit','empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.science','empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.coordinate_plan')
        if any(fullname == name or fullname.startswith(name+'.') for name in blocked):
            raise RuntimeError('producer/native import refused: '+fullname)
sys.meta_path.insert(0,Refuse())
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.physical_preparation_geometry import SOURCE_PINS, METHOD
assert len(SOURCE_PINS)==3
assert METHOD.object_schema.endswith('/physical-preparation-geometry-method')
'''
    result = subprocess.run([sys.executable,"-c",code],cwd=tmp_path,env=dict(os.environ,PYTHONPATH=str(source),PYTHONDONTWRITEBYTECODE="1"),capture_output=True,text=True,check=False)
    assert result.returncode == 0,result.stderr
