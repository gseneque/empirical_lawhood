# SPDX-License-Identifier: MPL-2.0
"""Direct controls for the separately scoped Gp KCX-neighborhood validation."""

from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess

import pytest

from empirical_lawhood.adapters.rubisco.rubisco_response.kcx_backbone_driver import signed_angle, target_backbones
from scripts.assess_gp_kcx_backbone import assess_supplement, compare, native_ramalyze


def exposed_table():
    residues, atoms, bonds = [], [], []
    components = {207: "ASP", 208: "PHE", 209: "VAL", 210: "KCX", 211: "ASP", 212: "ASP", 213: "GLU"}
    for chain in "ACEGIKMO":
        previous = None
        for position, comp in components.items():
            ri, first = len(residues), len(atoms)
            residues.append(dict(role="PROTEIN", chain=chain, chain_length=493, original_component=comp, seq=position,
                                 component=comp, position=position, id=f"exposed.{chain}.{position}"))
            atoms.extend([[ri,"N","N"],[ri,"CA","C"],[ri,"C","C"]])
            bonds.extend([[first,first+1],[first+1,first+2]])
            if previous is not None:
                bonds.append([previous,first])
            previous = first+2
    return dict(residues=residues, atoms=atoms, native_atom_names=[a[1] for a in atoms], heavy_covalent_bonds=bonds)


def fake_native(row):
    return dict(altloc="", icode="", chain_id=row["chain"], resseq=str(row["position"]), resname=row["component"],
                model_id="", res_type=row["reference_class"], phi=-100., psi=150., score=52., rama_type="Favored", outlier=False)


def evaluated(table):
    rows = target_backbones(table)
    for row in rows:
        row.update(phi_deg=-100., psi_deg=150., cctbx_raw_table_value=.52, ramalyze_score=52.,
                   category="FAVORED", outlier=False, status="MEASURED")
    native = {r["native_residue_index"]:fake_native(r) for r in rows if r["role"] == "NATIVE_FLANK_CONTROL"}
    return dict(rows=rows), native


def test_exact_five_backbone_atoms_four_edges_and_residue_specific_scopes():
    table = exposed_table()
    rows = target_backbones(table)
    target = [r for r in rows if r["role"] == "KCX_NEIGHBORHOOD"]
    assert len(rows) == 40 and len(target) == 24 and all(r["status"] == "MAPPED" for r in rows)
    assert [(r["position"], r["reference_class"], r["reference_scope"]) for r in target[:3]] == [
        (209, "isoleucine or valine", "STANDARD_AMINO_ACID"),
        (210, "general", "PARENT_LYS_GENERAL_PROXY"),
        (211, "general", "STANDARD_AMINO_ACID")]
    assert target[1]["native_atom_indices"] == [8,9,10,11,12]


@pytest.mark.parametrize("damage", ("missing-link", "element", "native-alias", "original-component", "duplicate-atom", "chain-loss"))
def test_missing_topology_or_disguised_chemistry_cannot_generate_a_measurement(damage):
    t = exposed_table()
    if damage == "missing-link":
        t["heavy_covalent_bonds"].remove([8,9])
    elif damage == "element":
        t["atoms"][9][2] = "C"
    elif damage == "native-alias":
        t["native_atom_names"][9] = "NX"
    elif damage == "original-component":
        t["residues"][3]["original_component"] = "LYS"
    elif damage == "duplicate-atom":
        t["atoms"].append(t["atoms"][9])
    else:
        for r in t["residues"]:
            if r["chain"] == "O":
                r["chain_length"] = 100
    if damage in ("duplicate-atom", "chain-loss"):
        with pytest.raises(ValueError):
            target_backbones(t)
    else:
        rows = target_backbones(t)
        assert len(rows) == 40
        kcx = next(r for r in rows if r["chain"] == "A" and r["position"] == 210)
        assert kcx["status"] == "UNEVALUABLE"
        if damage == "missing-link":
            assert kcx["missing_native_edges"] == [[8,9]]


@pytest.mark.numerical(oracle="Orienting a quadrant around the positive x axis gives +90 or -90 degrees. Collinear points have no defined dihedral.")
def test_plane_normal_sign_has_an_independent_quadrant_and_degeneracy_control():
    core = [(0,1,0),(0,0,0),(1,0,0)]
    assert signed_angle(core+[(1,0,1)]) == pytest.approx(90)
    assert signed_angle(core+[(1,0,-1)]) == pytest.approx(-90)
    with pytest.raises(ValueError, match="Degenerate"):
        signed_angle([(i,0,0) for i in range(4)])


def test_scope_and_failed_flanks_never_increment_native_denominator_or_imply_kcx_transfer():
    table = exposed_table()
    native_report, seen = evaluated(table)
    original = dict(assigned=56, returned=16, joined=16)
    good = assess_supplement(table, native_report, seen, original)
    assert good["native_ramalyze"] == original
    assert good["kcx_chemical_reference_transfer"] == "UNEVALUABLE" and not good["modifies_native_molprobity_scores"]
    assert good["categories_by_reference_scope"] == {"STANDARD_AMINO_ACID":{"FAVORED":16}, "PARENT_LYS_GENERAL_PROXY":{"FAVORED":8}}
    control = native_report["rows"][0]
    seen[control["native_residue_index"]]["phi"] *= -1
    partial = assess_supplement(table, native_report, seen, original)
    assert partial["evaluated_with_two_flank_controls"] == 21
    assert len(partial["supplementary_positions"]) == 24
    assert partial["additional_missing_native_positions_by_reference_scope"] == {"STANDARD_AMINO_ACID":14, "PARENT_LYS_GENERAL_PROXY":7}
    assert partial["status"].startswith("INCOMPLETE")
    row = native_report["rows"][1]
    # If a future native run directly observes a target, it cannot count as a distinct missing position.
    seen[row["native_residue_index"]] = fake_native(row)
    seen[control["native_residue_index"]]["phi"] = -100
    overlap = assess_supplement(table,native_report,seen,original)
    assert overlap["additional_missing_native_positions_by_reference_scope"]["STANDARD_AMINO_ACID"] == 15


def test_flank_rechecks_class_score_and_signed_periodic_angles():
    r = dict(reference_class="general", category="FAVORED", outlier=False, phi_deg=-180, psi_deg=160, ramalyze_score=52)
    n = dict(res_type="general", rama_type="Favored", outlier=False, phi=180, psi=160, score=52)
    assert compare(n,r)
    for change in (dict(res_type="glycine"), dict(rama_type="Allowed"), dict(outlier=True), dict(psi=-160), dict(score=51)):
        assert not compare({**n,**change},r)


def test_forged_native_rows_and_substituted_supplement_refused(tmp_path):
    table = exposed_table()
    returned, seen = evaluated(table)
    row = next(iter(seen.values()))
    raw = (json.dumps(row)+"\n").encode()
    path = tmp_path/"ramalyze.jsonl"
    path.write_bytes(raw)
    meta = dict(components={"ramalyze":dict(status="RETURNED", sha256=sha256(raw).hexdigest(), rows=1, bytes=len(raw))},
                input_census={"model_id":""})
    _, native = native_ramalyze(tmp_path,meta,table)
    assert native["joined"] == 1 and len(native["missing_native_residues"]) == 55
    path.write_bytes(raw.replace(b"Favored", b"Allowed"))
    with pytest.raises(ValueError, match="SHA-256"):
        native_ramalyze(tmp_path,meta,table)
    for damage in ("census", "reference", "source"):
        changed = deepcopy(returned)
        if damage == "census":
            changed["rows"].pop()
        elif damage == "reference":
            changed["rows"][1]["reference_class"] = "general"
        else:
            changed["rows"][2]["native_atom_indices"][1] += 1
        with pytest.raises(ValueError):
            assess_supplement(table,changed,seen,native)


@pytest.mark.native
@pytest.mark.numerical(oracle="Constructed Cartesian quartets encode the specified signed dihedrals. Translating each atom by known skew-cell lattice vectors must return the same scores and CCTBX Favored, Allowed and Outlier repertoire.")
def test_selected_cctbx_periodic_images_signed_angles_and_reference_classes(tmp_path, rubisco_molprobity_prefix):
    from empirical_lawhood.adapters.rubisco.rubisco_response import kcx_backbone_driver
    prefix = rubisco_molprobity_prefix
    code = """
import importlib.util, json, math, sys
import numpy as np
from cctbx import uctbx
from mmtbx.rotamer.ramachandran_eval import RamachandranEval
spec=importlib.util.spec_from_file_location("checked_driver",sys.argv[1])
driver=importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)
ev=RamachandranEval()
classes=("general","isoleucine or valine")
params=(10,12,14,80,85,75)
cell=uctbx.unit_cell(params)
lattice=np.array([cell.orthogonalize(e) for e in np.eye(3)])
out=[]
for phi,psi in ((-60,-45),(60,40),(75,40),(0,0)):
    p,q=np.deg2rad([phi,psi])
    points=[np.array(a) for a in ((0,1,0),(0,0,0),(1,0,0))]
    axis=np.array([0,np.cos(p),np.sin(p)])
    points.append(points[-1]+axis)
    left=np.cross([1,0,0],axis)
    right=np.cos(q)*left+np.sin(q)*np.cross(axis,left)
    points.append(points[-1]+np.cross(right,axis))
    moved=np.array(points)+np.array(((0,0,0),(1,0,-1),(-1,1,2),(2,-1,2),(1,1,-1)))@lattice
    rebuilt,shifts=driver.connected_points(moved,params)
    assert np.allclose(points,rebuilt,rtol=0,atol=1e-12) and len(shifts)==4
    for name in classes:
        val=driver.score_points(rebuilt,name,ev)
        assert math.isclose(val["phi_deg"],phi,abs_tol=1e-10)
        assert math.isclose(val["psi_deg"],psi,abs_tol=1e-10)
        out.append(val["category"])
try:
    driver.connected_points([(0,0,0),(5,0,0)],(10,10,10,90,90,90))
except ValueError:
    pass
else:
    raise AssertionError("tied periodic image accepted")
print(json.dumps(out))
"""
    completed = subprocess.run([str(Path(prefix)/"bin/python"), "-I", "-B", "-c", code, kcx_backbone_driver.__file__],
        env={"HOME":str(tmp_path), "TMPDIR":str(tmp_path), "PATH":str(Path(prefix)/"bin")+os.pathsep+os.defpath,
             "OPENBLAS_NUM_THREADS":"1", "OMP_NUM_THREADS":"1"},
        check=True, capture_output=True, text=True, timeout=60)
    assert json.loads(completed.stdout) == ["FAVORED","FAVORED","FAVORED","ALLOWED",
                                           "ALLOWED","OUTLIER","OUTLIER","OUTLIER"]
