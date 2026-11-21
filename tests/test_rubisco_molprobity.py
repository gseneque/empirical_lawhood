# SPDX-License-Identifier: MPL-2.0
"""Retained controls for exact MolProbity exchange and independent row adjudication."""

from collections import Counter
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import struct
from types import SimpleNamespace as NS

import pytest

from empirical_lawhood.adapters.rubisco.rubisco_response.molprobity_projection import file_sha, json_bytes, project_material
from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology import MODEL_NAMES
from empirical_lawhood.api.domain_composition.rubisco_response.molprobity_read import COMPONENTS, assess_model
from empirical_lawhood.adapters.rubisco.rubisco_response.molprobity_driver import atom_census
from scripts.validate_gp_molprobity import original_export, review_batch


def tiny_mapping():
    topology = object()
    residues = [NS(residue_id=f"residue.{i}", component=comp, role="PROTEIN", site_id=None,
                   author_chain="A", author_number=i, chain_id="ssu.a", sequence_position_1based=i, insertion_code="")
                for i, comp in enumerate(("ALA", "ILE", "PRO"), 1)]
    residues += [NS(residue_id="water.1", component="WAT", role="WATER", site_id=None,
                    author_chain=None, author_number=None, chain_id=None, sequence_position_1based=None, insertion_code="")]
    atoms, points = [], []
    for ri, spec in enumerate(([("CA", 6)], [("CA", 6), ("H", 1)], [("CA", 6)], [("O", 8)])):
        for name, elem in spec:
            i = len(atoms)
            atoms.append(NS(residue_id=residues[ri].residue_id, name=name, atomic_number=elem,
                            source=topology, source_atom_id=str(i + 1)))
            points.extend((i + .1234567, i - .2345678, i * 1.1111111))
    xyz = struct.pack("<" + "d" * len(points), *points)
    member = NS(name="coordinates-angstrom", dtype="<f8", shape=(len(atoms), 3), order="C",
                sha256=sha256(xyz).hexdigest())
    rep = NS(atoms=atoms, residues=residues, material=NS(chains=[NS(chain_id="ssu.a", sequence="AIP", subunit="SSU")]),
             raw_topology=topology, arrays=NS(members=[member]), sites=[], bonds=[NS(first=0, second=1), NS(first=1, second=3)])
    return dict(representation=rep, coordinate_bytes=xyz, box_angstrom=(12, 13, 14, 90, 90, 90))


def native_res(table, ri):
    r = table["residues"][ri]
    return dict(chain_id=r["chain"], resseq=str(r["seq"]), resname=r["component"], icode=" ", altloc="",
                model_id="", outlier=False)


def native_term(table, atoms, *, score=0.):
    rows = [dict(native_res(table, table["atoms"][i][0]), name=table["atoms"][i][1]) for i in atoms]
    if len(rows) == 2 and score < -10:
        return {**rows[0], **{"target_" + k: v for k, v in rows[1].items()}, "outlier": True, "overlap": -0.4}
    return {**{"atoms_" + field: [row[field] for row in rows] for field in ("chain_id", "resseq", "resname", "name", "icode", "altloc")},
            "model_id": "", "score": score, "outlier": abs(score) >= 4}


def fixture_report(tmp, *, adverse=False, drop=False):
    mapping = tiny_mapping()
    project_material(mapping, tmp)
    table = json.loads((tmp / "atom-map.json").read_bytes())
    census = {"model_id": "", "atom_count": len(table["atoms"]), "coordinate_array_sha256": table["coordinate_array_sha256"]}
    def with_category(ri, **kw):
        return dict(native_res(table, ri), **kw)
    streams = dict(ramalyze=[with_category(1, rama_type="Favored")],
                   rotalyze=[with_category(i, evaluation="Favored") for i in (1, 2)],
                   omegalyze=[with_category(i, omega_type="Cis" if i == 2 else "Trans") for i in (1, 2)],
                   cbetadev=[with_category(i, deviation=.25 if i == 0 and adverse else .1,
                                          outlier=i == 0 and adverse) for i in range(3)],
                   bonds=[native_term(table, (0, 1), score=4.0 if adverse else 0), native_term(table, (1, 3))],
                   angles=[native_term(table, (0, 1, 3))],
                   clashscore=[native_term(table, (0, 2), score=-99)] if adverse else [])
    if drop:
        streams["bonds"].pop(0)
    components = {}
    for name, rows in streams.items():
        raw = b"".join(json_bytes(r) for r in rows)
        (tmp / (name + ".jsonl")).write_bytes(raw)
        components[name] = dict(status="RETURNED", bytes=len(raw), rows=len(rows), sha256=sha256(raw).hexdigest())
        if name in ("bonds", "angles", "clashscore"):
            components[name]["used_atom_census"] = census
    components["clashscore"].update(clashscore=250. if adverse else 0., native_nonwater_atoms=4, native_serious_clashes=int(adverse))
    return table, dict(input_census=census, components=components)


def test_original_primes_explicit_water_h_and_exact_ordinal_coordinates(tmp_path):
    mapping = tiny_mapping()
    mapping["representation"].atoms[2].name = "H1'"
    summary = project_material(mapping, tmp_path)
    assert summary["hydrogen_count"] == 1
    table = json.loads((tmp_path / "atom-map.json").read_bytes())
    assert table["residues"][-1]["original_chain"] is None and table["residues"][-1]["component"] == "HOH"
    rows = [line.split() for line in (tmp_path / "model.cif").read_text().splitlines() if line.startswith(("ATOM ", "HETATM "))]
    points = [float(s) for row in rows for s in row[10:13]]
    assert struct.pack("<" + "d"*len(points), *points) == mapping["coordinate_bytes"]
    assert rows[2][3] == '"H1\'"' and rows[-1][5] == "HOH"
    hierarchy_rows = []
    for row in rows:
        hierarchy_rows.append(NS(chain_id=row[17], resseq=row[15], resname=row[16], name=row[18].strip('"'),
                                 element=row[2], icode="", altloc="", xyz=list(map(float, row[10:13]))))
    hierarchy = NS(models=lambda: [NS(id="")], atoms_with_labels=lambda: list(reversed(hierarchy_rows)))
    assert atom_census(hierarchy, table)["coordinate_array_sha256"] == summary["coordinate_array_sha256"]
    hierarchy_rows[0].xyz[0] += 1e-10
    with pytest.raises(ValueError, match="exact relaxed"):
        atom_census(hierarchy, table)
    hierarchy_rows.pop(2)
    with pytest.raises(ValueError, match="lost a native atom"):
        atom_census(hierarchy, table)


def test_projection_rejects_substituted_coordinate_bytes_before_writing(tmp_path):
    mapping = tiny_mapping()
    mapping["coordinate_bytes"] = bytes(len(mapping["coordinate_bytes"]))
    with pytest.raises(ValueError, match="native-order"):
        project_material(mapping, tmp_path)
    assert not list(tmp_path.iterdir())


def test_exact_original_rows_missing_and_protected_critical_sites(tmp_path):
    table, report = fixture_report(tmp_path, adverse=True, drop=True)
    output = assess_model(tmp_path, table, report)
    assert output["status"] == "UNEVALUABLE"
    assert set(output["components_with_outliers"]) == {"clashscore", "cbetadev"}
    assert output["components"]["bonds"]["protected_scope"]["ssu.a.position.1"]["missing_assigned"] == 1
    assert output["components"]["cbetadev"]["outliers"][0]["critical"] == ["ssu.a.position.1"]
    assert output["components"]["omegalyze"]["categories"]["CIS_PRO"] == 1
    assert output["components"]["clashscore"]["probe_source_nonwater_atoms"] == 4


def test_combined_reader_publishes_only_fully_authenticated_ramalyze_rows(tmp_path):
    from empirical_lawhood.api.domain_composition.rubisco_response.molprobity_read import assess_component, dimensions

    table, report = fixture_report(tmp_path)
    returned = report["components"]["ramalyze"]
    census = report["input_census"]
    captured = {}
    assessed = assess_component(tmp_path, "ramalyze", returned, census, table, dimensions(table), ramalyze_rows=captured)
    assert len(captured) == assessed["raw_rows"] == 1
    assert next(iter(captured.values()))["rama_type"] == "Favored"
    captured.clear()
    with pytest.raises(ValueError, match="authenticated returned component"):
        assess_component(tmp_path, "ramalyze", {**returned, "sha256": "0" * 64}, census,
                         table, dimensions(table), ramalyze_rows=captured)
    assert not captured


def test_validation_exception_still_checks_original_material(tmp_path, monkeypatch):
    from empirical_lawhood.adapters.rubisco.rubisco_response import molprobity_runtime
    from empirical_lawhood.api.domain_composition.rubisco_response import molprobity_validation

    export = dict(models=[dict(name="exposed", status="EXPORTED")])
    reads = []
    def original(*args):
        reads.append(args)
        if len(reads) > 1:
            raise ValueError("changed material during native failure")
        return export
    def interrupted(*args, **kwargs):
        raise RuntimeError("interrupted native component")
    monkeypatch.setattr(molprobity_validation, "original_export", original)
    monkeypatch.setattr(molprobity_runtime, "verify_runtime", lambda *a, **kw: {})
    monkeypatch.setattr(molprobity_validation, "run_validation_driver", interrupted)
    args = NS(runtime_prefix=tmp_path, runtime_receipt_sha256="f" * 64, export_directory=tmp_path,
              export_sha256="e" * 64, timeout_seconds=9, restraint=())
    with pytest.raises(ValueError, match="changed material during native failure") as failure:
        molprobity_validation.run_components(args, tmp_path)
    assert isinstance(failure.value.__context__, RuntimeError)
    assert len(reads) == 2


def test_scoped_complete_positive_does_not_admit_chemistry_or_turnover(tmp_path):
    table, report = fixture_report(tmp_path)
    output = assess_model(tmp_path, table, report)
    assert output["status"] == "COVERED" and len(output["components"]) == 7
    assert output["metal_coordination_and_ligand_chemistry"] == output["catalysis_and_paired_forecast"] == "UNEVALUABLE"
    report["components"]["clashscore"]["used_atom_census"] = None
    assert assess_model(tmp_path, table, report)["incomplete_components"] == ["clashscore"]


def test_raw_substitution_and_wrong_denominator_refused(tmp_path):
    table, report = fixture_report(tmp_path)
    replacement = deepcopy(report)
    replacement["input_census"]["coordinate_array_sha256"] = "1" * 64
    with pytest.raises(ValueError, match="different selected"):
        assess_model(tmp_path, table, replacement)
    replacement = deepcopy(report)
    replacement["components"]["clashscore"].update(clashscore=1200., native_serious_clashes=1)
    with pytest.raises(ValueError, match="denominator"):
        assess_model(tmp_path, table, replacement)
    (tmp_path / "bonds.jsonl").write_bytes(b"")
    with pytest.raises(ValueError, match="authenticated returned"):
        assess_model(tmp_path, table, report)


def test_foreign_site_source_and_duplicate_native_row_rejected(tmp_path):
    table, report = fixture_report(tmp_path)
    path = tmp_path / "ramalyze.jsonl"
    row = json.loads(path.read_bytes())
    for rows, message in (([dict(row, chain_id="X")], "absent from"), ([row, row], "Duplicated original")):
        raw = b"".join(json_bytes(r) for r in rows)
        path.write_bytes(raw)
        report["components"]["ramalyze"].update(rows=len(rows), bytes=len(raw), sha256=sha256(raw).hexdigest())
        with pytest.raises(ValueError, match=message):
            assess_model(tmp_path, table, report)


def test_complete_material_roster_external_runtime_and_original_join(tmp_path):
    from empirical_lawhood.adapters.rubisco.rubisco_response import molprobity_driver
    rows = [dict(name=name, status="CONSTRUCTION_UNAVAILABLE", receipt="retained-" + name, construction_disposition=None,
                 construction_findings=None, validated_material_eligible=False) for name in MODEL_NAMES]
    export = dict(schema="el-molprobity-export-1", roster="MATCHED_ACTIVE_CHILDREN", models=rows)
    (tmp_path / "export.json").write_bytes(json_bytes(export))
    pin = file_sha(tmp_path / "export.json")
    record = dict(schema="el-molprobity-run-1", roster="MATCHED_ACTIVE_CHILDREN", export_sha256=pin, engine_receipt_sha256="a"*64,
                  keep_input_hydrogens=True, allow_nqh_flips=False, xh_distance_convention="NUCLEAR",
                  driver_sha256=file_sha(Path(molprobity_driver.__file__)), restraint_sha256=[],
                  models=[dict(name=r["name"], status=r["status"], export_row_sha256=sha256(json_bytes(r)).hexdigest()) for r in rows])
    run_path = tmp_path / "run.json"
    run_path.write_bytes(json_bytes(record))
    args = NS(export_directory=tmp_path, export_sha256=pin, run_directory=tmp_path, run_sha256=file_sha(run_path),
              runtime_receipt_sha256="a"*64)
    result = review_batch(args)
    assert len(result["models"]) == 4 and all(m["unreturned"] == list(COMPONENTS) for m in result["models"])
    record["models"][1]["export_row_sha256"] = record["models"][0]["export_row_sha256"]
    run_path.write_bytes(json_bytes(record))
    args.run_sha256 = file_sha(run_path)
    with pytest.raises(ValueError, match="topology, restart"):
        review_batch(args)
    export["models"].pop()
    (tmp_path / "export.json").write_bytes(json_bytes(export))
    with pytest.raises(ValueError, match="SHA"):
        original_export(tmp_path, pin)
    with pytest.raises(ValueError, match="four-material"):
        original_export(tmp_path, file_sha(tmp_path / "export.json"))


@pytest.mark.native
@pytest.mark.parametrize("adverse", [False, True], ids=["original", "injected-contact"])
def test_selected_real_cctbx_numerical_control(tmp_path, adverse, rubisco_molprobity_prefix):
    """Three explicit-H residues from the selected installed CCTBX regression fixture."""
    import ast
    from collections import defaultdict
    import os
    import subprocess
    from empirical_lawhood.adapters.rubisco.rubisco_response import molprobity_driver
    prefix = rubisco_molprobity_prefix
    source = prefix / "lib/python3.11/site-packages/mmtbx/regression/discamb/tst_olex2_vs_pydiscamb_TAAM_1.py"
    text = next(n.value for n in ast.walk(ast.parse(source.read_text())) if isinstance(n, ast.Constant)
                and isinstance(n.value, str) and "PRO A  11" in n.value and "CYS A  12" in n.value and "LYS A  13" in n.value)
    selected = [l for l in text.splitlines() if l.startswith("ATOM  ") and l[16] == " " and l[21] == "A"
                and int(l[22:26]) in (11, 12, 13)]
    atoms, xyz, indices, protein = [], [], {}, []
    topology = object()
    chemical = defaultdict(list)
    for l in selected:
        position, component, name = int(l[22:26]) - 10, l[17:20], l[12:16].strip()
        element = l[76:78].strip()
        i = len(atoms)
        indices[position, name] = i
        if position not in chemical:
            protein.append(NS(residue_id=str(position), component=component, role="PROTEIN", site_id=None, author_chain="A",
                              author_number=position, chain_id="control", sequence_position_1based=position, insertion_code=""))
        chemical[position].append(name)
        atoms.append(NS(residue_id=str(position), name=name, atomic_number={"C": 6, "H": 1, "N": 7, "O": 8, "S": 16}[element],
                        source=topology, source_atom_id=str(i + 1)))
        xyz.extend(float(l[i:i+8]) for i in (30, 38, 46))
    pairs = []
    for i in chemical:
        edges = [("N", "CA"), ("CA", "C"), ("C", "O"), ("CA", "CB")]
        edges += {1: [("CB", "CG"), ("CG", "CD"), ("CD", "N")], 2: [("CB", "SG")],
                  3: [("CB", "CG"), ("CG", "CD"), ("CD", "CE"), ("CE", "NZ")]}[i]
        if (i, "OXT") in indices:
            edges.append(("C", "OXT"))
        pairs += [tuple(sorted((indices[i, a], indices[i, b]))) for a,b in edges]
        if i > 1:
            pairs.append(tuple(sorted((indices[i-1,"C"], indices[i,"N"]))))
    if adverse:
        target, moved = 3*indices[1,"CB"], 3*indices[3,"NZ"]
        xyz[moved:moved+3] = [xyz[target]+0.25, xyz[target+1], xyz[target+2]]
    raw = struct.pack("<" + "d"*len(xyz), *xyz)
    member = NS(name="coordinates-angstrom", dtype="<f8", shape=(len(atoms), 3), order="C", sha256=sha256(raw).hexdigest())
    rep = NS(raw_topology=topology, atoms=atoms, residues=protein, bonds=[NS(first=a, second=b) for a,b in pairs],
             sites=[], material=NS(chains=[NS(chain_id="control", sequence="PCK", subunit="TEST")]), arrays=NS(members=[member]))
    project_material(dict(representation=rep, box_angstrom=(30, 30, 30, 90, 90, 90), coordinate_bytes=raw), tmp_path)
    (tmp_path / "native").mkdir()
    with (tmp_path / "native.log").open("wb") as log:
        process = subprocess.run([str(prefix/"bin/python"), "-I", "-B", str(Path(molprobity_driver.__file__).resolve()),
                                  str(tmp_path/"model.cif"), str(tmp_path/"atom-map.json"), str(tmp_path/"native")],
                                 cwd=tmp_path, stdout=log, stderr=subprocess.STDOUT,
                                 env={"PATH": str(prefix/"bin")+os.pathsep+os.defpath, "HOME": str(tmp_path),
                                      "TMPDIR": str(tmp_path), "OMP_NUM_THREADS":"1","OPENBLAS_NUM_THREADS":"1"}, timeout=120)
    assert process.returncode == 0, (tmp_path/"native.log").read_text()[-2500:]
    report = json.loads((tmp_path/"native/components.json").read_bytes())
    results = assess_model(tmp_path/"native", json.loads((tmp_path/"atom-map.json").read_bytes()), report)
    assert results["incomplete_components"] == [], {name: row for name, row in results["components"].items() if row["status"] == "UNEVALUABLE"}
    assert results["components"]["ramalyze"]["raw_rows"] == 1
    assert results["components"]["bonds"]["raw_rows"] >= len(pairs)
    if adverse:
        assert results["components"]["clashscore"]["clashscore"] > 0
        assert results["components"]["clashscore"]["outliers"]
        assert results["components"]["bonds"]["outliers"]


def test_rejected_native_can_only_supply_labeled_geometry_diagnostics(monkeypatch):
    from empirical_lawhood.domains.rubisco.rubisco_response import gp_initial_molecular as mapping
    from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition as A
    from empirical_lawhood.science.records.status import OperationalStatus
    model = NS(identity="matched")
    source = NS(identity="original", models=(model,), ligand=NS(identity="ligand"))
    scaffold = NS(ligand_preparation="ligand")
    original = NS(assessment_id="read.1", construction_disposition=A.FALSIFIED)
    unit = NS(returned=NS(model=model.identity, return_code=0, error=None, timed_out=False),
              definition=NS(sources=(source.identity,)), completion=NS(operational_status=OperationalStatus.SUCCEEDED),
              assessment=original, assessment_error=None)
    monkeypatch.setattr(mapping, "exact", lambda a,b: None)
    monkeypatch.setattr(mapping, "assess_initial_topology", lambda *a, **k: original)
    monkeypatch.setattr(mapping, "_map_assessed_endpoint", lambda *a: dict(coordinate_bytes=b"exact unit-test operand"))
    args = dict(source=source, model=model, scaffold=scaffold, unit=unit, files={})
    with pytest.raises(ValueError, match="successful independently assessed"):
        mapping.map_initial_amber_representation(**args)
    diagnostic = mapping.map_initial_amber_diagnostic(**args)
    assert diagnostic["original_construction_disposition"] == "FALSIFIED" and not diagnostic["validated_material_eligible"]
    monkeypatch.setattr(mapping, "assess_initial_topology", lambda *a, **k: object())
    with pytest.raises(ValueError, match="independent current raw assessment"):
        mapping.map_initial_amber_diagnostic(**args)


def test_parent_isolated_reader_cell_original_cap_and_one_to_one_sites(tmp_path):
    from empirical_lawhood.adapters.rubisco.rubisco_response.molprobity_projection import write_projection
    from empirical_lawhood.api.domain_composition.rubisco_response.molprobity_parent import parent_sites
    groups = {}
    for i, chain in enumerate("ACEGIKMO"):
        groups[chain,210,"KCX"] = [(15*i+2, 1, 0)]
        groups["Z",i+1,"CAP"] = [(15*i+1, 2, 0)]
        groups["Z",i+22,"MG"] = [(15*i+2, 2, 0)]
    sites = parent_sites(groups)
    assert len(set(sites.values())) == 8 and Counter(sites.values()).most_common(1)[0][1] == 3
    groups["Z",1,"RUB"] = groups.pop(("Z",1,"CAP"))
    with pytest.raises(ValueError, match="KCX/CAP/Mg"):
        parent_sites(groups)
    residue = dict(id="parent.Z.28", chain="Z", seq=28, component="MG", original_component="MG", original_chain="Z",
                   original_number=28, role="MAGNESIUM", chain_id=None, site="parent.site.A", critical=["parent.site.A"],
                   position=None, chain_length=None)
    raw = struct.pack("<ddd", -10.2715134567, -180.3, 0)
    write_projection(tmp_path, [residue], [[0, "MG", "MG"]], [], raw, None, ["parent.site.A"])
    table = json.loads((tmp_path/"atom-map.json").read_bytes())
    assert table["cell_angstrom_degrees"] is None
    assert table["reader_cell_angstrom_degrees"] == ["40.0"]*3 + ["90"]*3
    assert table["coordinate_array_sha256"] == sha256(raw).hexdigest()


def test_parent_tag_refuses_reuse_as_a_child_and_missing_parent_stays_unevaluable(tmp_path):
    from empirical_lawhood.adapters.rubisco.rubisco_response import molprobity_driver
    from empirical_lawhood.api.domain_composition.rubisco_response.molprobity_parent import PARENT
    row = dict(name=PARENT,status="CONSTRUCTION_UNAVAILABLE",construction_disposition="FALSIFIED",
               construction_findings=["optimizer-did-not-converge"], validated_material_eligible=False)
    export = dict(schema="el-molprobity-export-1",roster="COMMON_INHIBITED_PARENT", models=[row])
    (tmp_path / "export.json").write_bytes(json_bytes(export))
    pin = file_sha(tmp_path/"export.json")
    assert original_export(tmp_path, pin)["models"] == [row]
    run = dict(schema="el-molprobity-run-1",roster=export["roster"], export_sha256=pin, engine_receipt_sha256="a"*64,
               keep_input_hydrogens=True, allow_nqh_flips=False,xh_distance_convention="NUCLEAR",
               driver_sha256=file_sha(Path(molprobity_driver.__file__)),restraint_sha256=[],
               models=[dict(name=PARENT,status=row["status"],export_row_sha256=sha256(json_bytes(row)).hexdigest())])
    (tmp_path/"run.json").write_bytes(json_bytes(run))
    args = NS(export_directory=tmp_path,export_sha256=pin,run_directory=tmp_path,run_sha256=file_sha(tmp_path/"run.json"),
              runtime_receipt_sha256="a"*64)
    model, = review_batch(args)["models"]
    assert (model["status"],model["original_construction_disposition"], model["validated_material_eligible"]) == (
        "UNEVALUABLE","FALSIFIED",False)
    run["roster"] = "MATCHED_ACTIVE_CHILDREN"
    (tmp_path/"run.json").write_bytes(json_bytes(run))
    args.run_sha256 = file_sha(tmp_path/"run.json")
    with pytest.raises(ValueError, match="incomplete roster"):
        review_batch(args)


def test_structural_critical_scope_terminal_segments_and_periodic_neighbors():
    from empirical_lawhood.adapters.rubisco.rubisco_response.molprobity_projection import critical_neighbors, protected, report_atom_name
    assert all("lsu.01.modeled-terminal-segments" in protected("lsu.01", "LSU", k, None)
               for k in (*range(1,15),*range(487,494)))
    assert protected("lsu.01","LSU",15,None) == protected("lsu.01","LSU",486,None) == []
    assert [report_atom_name("RUB",n) for n in ("H1C1","H2C1","HC3","HC4","H1C5","H2C5")] == [
        "H11","H12","H3","H4","H51","H52"]
    assert report_atom_name("KCX","HN1") == "H" and report_atom_name("CAP","H11") == "H11"
    residues=[dict(role="PROTEIN",site=None,critical=["ssu.a.position.95"]), dict(role="WATER",site=None,critical=[])]
    points=struct.pack("<dddddd",1,0,0,28,0,0)
    atoms=[[0,"CA","C"],[1,"O","O"]]
    assert critical_neighbors(deepcopy(residues),atoms,points,None)["ssu.a.position.95"]["neighbors"] == []
    row, = critical_neighbors(residues,atoms,points,(30,30,30,90,90,90))["ssu.a.position.95"]["neighbors"]
    assert row["minimum_distance_angstrom"] == pytest.approx(3) and row["native_atom_indices"] == [0,1]
    assert residues[1]["critical"] == ["neighbors-of.ssu.a.position.95"]


def test_original_material_pin_shape_and_crossed_parent_restart_refused():
    from empirical_lawhood.science.identity.provenance import ObjectIdentity
    from scripts.validate_gp_molprobity import original_material_pins
    def identity(key, schema):
        return ObjectIdentity(key, schema, "1.0.0", "a"*64).to_document()
    source = identity("source.control","empirical-lawhood/rubisco-response/gp-geometry-repair-input")
    export = dict(source=source, roster="COMMON_INHIBITED_PARENT",construction_sha256="3"*64)
    record = dict(model=source, definition=identity("task.control","empirical-lawhood/control/definition"),
                  parent_integrity=identity("parent.control","empirical-lawhood/control/integrity"),
                  original_geometry_receipt=identity("receipt.control","empirical-lawhood/control/receipt"),original_ligand="CAP",
                  physical_periodicity="NONPERIODIC",construction_disposition="FALSIFIED",
                  validated_material_eligible=False,construction_findings=["rejected"])
    fields = ("assessment_sha256","completion_sha256","mmcif_sha256","atom_map_sha256","coordinate_array_sha256",
              "native_receipt_sha256","raw_topology_sha256","raw_endpoint_nm_npy_sha256","original_atom_origins_sha256","heavy_join_sha256")
    record.update({name:"0"*64 for name in fields})
    original_material_pins(export, record)
    with pytest.raises(ValueError,match="eligibility"):
        original_material_pins(export,dict(record,validated_material_eligible=True))
    with pytest.raises(ValueError,match="topology|material|ligand"):
        original_material_pins(export,dict(record,original_ligand="RUB"))
    with pytest.raises((TypeError,ValueError)):
        original_material_pins(export,dict(record,raw_endpoint_nm_npy_sha256="missing"))
