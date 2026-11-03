# SPDX-License-Identifier: MPL-2.0
"""Exposed raw-text counterexamples, never an actual prepared/native model."""

from copy import deepcopy
from dataclasses import replace
from decimal import Decimal as D
from hashlib import sha256
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import contracts as c
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import preparation, science
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.amber_parameters import assigned_census, read_prmtop, validate_assignment
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.preparation_integrity import AMINO, PreparationIntegrity, assess, disposition_census, read_heavy_pdb, validate_origins
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from tests.test_rubisco_insilico_dynamics import sequences


def topology():
    pointers = [0]*31
    for index,value in {0:4,1:2,2:1,3:1,5:1,7:1,10:4,11:1,15:1,16:1,17:1}.items():
        pointers[index] = value
    return {
        "POINTERS":pointers, "ATOM_NAME":["C","N","CA","H"], "AMBER_ATOM_TYPE":["CT","N","CT","H"],
        "ATOMIC_NUMBER":[6,7,6,1], "MASS":[D(12),D(14),D(12),D(1)], "CHARGE":[D('9.11115'),D('-9.11115'),D(0),D(0)],
        "ATOM_TYPE_INDEX":[1,2,1,2], "RESIDUE_LABEL":["ALA"], "RESIDUE_POINTER":[1],
        "NONBONDED_PARM_INDEX":[1,2,2,3], "LENNARD_JONES_ACOEF":[D(64),D(128),D(256)], "LENNARD_JONES_BCOEF":[D(8),D(16),D(32)],
        "NUMBER_EXCLUDED_ATOMS":[1,1,1,1], "EXCLUDED_ATOMS_LIST":[2,3,4,0],
        "BOND_FORCE_CONSTANT":[D(0)], "BOND_EQUIL_VALUE":[D('1.379')], "ANGLE_FORCE_CONSTANT":[D(66)], "ANGLE_EQUIL_VALUE":[D(0)],
        "DIHEDRAL_FORCE_CONSTANT":[D('-1.7')], "DIHEDRAL_PERIODICITY":[D(2)], "DIHEDRAL_PHASE":[D(0)],
        "SCEE_SCALE_FACTOR":[D('1.2')], "SCNB_SCALE_FACTOR":[D(2)],
        "BONDS_INC_HYDROGEN":[6,9,1], "BONDS_WITHOUT_HYDROGEN":[0,3,1],
        "ANGLES_INC_HYDROGEN":[], "ANGLES_WITHOUT_HYDROGEN":[0,3,6,1],
        "DIHEDRALS_INC_HYDROGEN":[], "DIHEDRALS_WITHOUT_HYDROGEN":[0,3,-6,-9,1],
    }


def amber_text(sections):
    rows = ["%VERSION VERSION_STAMP = V0001.000  DATE = exposed\n"]
    for name,values in sections.items():
        kind = "A" if values and type(values[0]) is str else "E" if values and type(values[0]) is D else "I"
        repeat,width = (20,4) if kind == "A" else (5,16) if kind == "E" else (10,8)
        rows.extend(("%FLAG "+name+"\n",f"%FORMAT({repeat}{kind.lower()}{width}"+(".8" if kind == "E" else "")+")\n"))
        fields = [f"{value:<4}" if kind == "A" else f"{value:16.8E}" if kind == "E" else f"{value:8d}" for value in values]
        rows.extend("".join(fields[index:index+repeat])+"\n" for index in range(0,len(fields),repeat))
    return "".join(rows)


def expected_audit():
    # Independent literal reference: raw factor 16 gives radius 2**(-1/3),
    # charge +/-9.11115/18.2223, zero force and negative torsion retained.
    atoms = [dict(index=index,name=name,residue_index=0,residue_name="ALA",residue_number=0,chain="",
        atomic_number=number,atom_type=typ,charge_electron=charge,mass_dalton=mass,
        rmin_half_angstrom="0.7937005259840997",epsilon_kcal_mol=epsilon)
        for index,(name,number,typ,charge,mass,epsilon) in enumerate((
            ("C",6,"CT","0.5","12.0","0.25"),("N",7,"N","-0.5","14.0","1.0"),
            ("CA",6,"CT","0.0","12.0","0.25"),("H",1,"H","0.0","1.0","1.0")))]
    return dict(atoms=atoms,bonds=[dict(atoms=[0,1],coefficients=dict(k="0.0",req="1.379")),dict(atoms=[2,3],coefficients=dict(k="0.0",req="1.379"))],
        angles=[dict(atoms=[0,1,2],coefficients=dict(k="66.0",theteq="0.0"))],
        dihedrals=[dict(atoms=[0,1,2,3],coefficients=dict(phi_k="-1.7",per="2.0",phase="0.0",scee="1.2",scnb="2.0"),ignore_end=True,improper=True)],
        native_nonbonded_tables={key:[repr(float(value)) for value in topology()[key]] for key in ("NONBONDED_PARM_INDEX","LENNARD_JONES_ACOEF","LENNARD_JONES_BCOEF","NUMBER_EXCLUDED_ATOMS","EXCLUDED_ATOMS_LIST")},
        term_census=dict(atoms=4,bonds=2,angles=1,dihedrals=1))


def test_complete_raw_assignment_preserves_zero_negative_signs_and_all_tables(monkeypatch):
    from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import parameter_audit

    monkeypatch.setattr(parameter_audit,"assigned_parameter_inventory",lambda *args:pytest.fail("producer enumeration entered"))
    result = validate_assignment(amber_text(topology()),expected_audit())
    assert result["term_census"] == dict(atoms=4,bonds=2,angles=1,dihedrals=1)
    assert result["exclusions"] == (2,3,4,0)


@pytest.mark.parametrize("category,field",[("atoms","charge_electron"),("atoms","mass_dalton"),("atoms","epsilon_kcal_mol"),("bonds","k"),("angles","theteq"),("dihedrals","scee")])
def test_finite_rehashed_parameter_substitution_never_admitted(category,field):
    audit = expected_audit()
    row = audit[category][0] if category == "atoms" else audit[category][0]["coefficients"]
    row[field] = "1.234"
    with pytest.raises(ValueError,match="differs"):
        validate_assignment(amber_text(topology()),audit)


@pytest.mark.parametrize("key",["NONBONDED_PARM_INDEX","LENNARD_JONES_ACOEF","LENNARD_JONES_BCOEF","NUMBER_EXCLUDED_ATOMS","EXCLUDED_ATOMS_LIST"])
def test_full_raw_mixing_exclusion_tables_cannot_be_thinned_or_substituted(key):
    audit = expected_audit()
    audit["native_nonbonded_tables"][key][-1] = "123.0"
    with pytest.raises(ValueError,match="differs"):
        validate_assignment(amber_text(topology()),audit)
    audit["native_nonbonded_tables"][key].pop()
    with pytest.raises(ValueError,match="denominator"):
        validate_assignment(amber_text(topology()),audit)


@pytest.mark.parametrize("mutation",["unknown-force","unknown-extra-force","missing-scaling","bad-pointer","bad-sign","nonfinite","duplicate-flag","unsupported-format"])
def test_incomplete_or_unsupported_raw_parameterization_refuses(mutation):
    stock = topology()
    if mutation == "unknown-force":stock["CTITLE"] = ["CHAR"]
    if mutation == "unknown-extra-force":stock["EXTRA_FORCE_CONSTANT"] = [D(1)]
    if mutation == "missing-scaling":del stock["SCEE_SCALE_FACTOR"]
    if mutation == "bad-pointer":stock["POINTERS"][10] = 3
    if mutation == "bad-sign":stock["DIHEDRALS_WITHOUT_HYDROGEN"][0] = -3
    if mutation == "nonfinite":stock["MASS"][0] = D("NaN")
    raw = amber_text(stock)
    if mutation == "duplicate-flag":raw += "%FLAG MASS\n%FORMAT(1E16.8)\n  1.00000000E+00\n"
    if mutation == "unsupported-format":raw = raw.replace("10i8","1P10i8",1)
    with pytest.raises(ValueError):
        validate_assignment(raw,expected_audit())


def test_native_lj_zero_branch_keeps_full_nonzero_raw_coefficients():
    stock = topology()
    stock["LENNARD_JONES_ACOEF"][0] = D("1e-11")
    audit = expected_audit()
    for index in (0,2):
        audit["atoms"][index].update(rmin_half_angstrom="0.0",epsilon_kcal_mol="0.0")
    audit["native_nonbonded_tables"]["LENNARD_JONES_ACOEF"][0] = "1e-11"
    assert validate_assignment(amber_text(stock),audit)["lj_a"][0] == D("1e-11")


def test_nonzero_pinned_radian_conversion_and_periodicity_integer_semantics():
    stock,audit = topology(),expected_audit()
    stock["ANGLE_EQUIL_VALUE"][0] = D("3.14159265")
    stock["DIHEDRAL_PHASE"][0] = D("1.57079633")
    stock["DIHEDRAL_PERIODICITY"][0] = D("2.75")
    audit["angles"][0]["coefficients"]["theteq"] = "179.99999979432002"
    audit["dihedrals"][0]["coefficients"]["phase"] = "90.0000001836389"
    assert validate_assignment(amber_text(stock),audit)["term_census"]["dihedrals"] == 1


def test_raw_assessor_imports_cold_without_numpy_producer_or_native(tmp_path):
    source = Path(__file__).resolve().parents[1]/"src"
    code = '''
import importlib.abc
import sys
class Refuse(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        blocked = ('numpy','parmed','openmm','pdbfixer','empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.native','empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.parameter_audit','empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.coordinate_plan','empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.science','empirical_lawhood.adapters.methods.rubisco_insilico_structure.science')
        if any(fullname == name or fullname.startswith(name+'.') for name in blocked):
            raise RuntimeError('producer/native import refused: '+fullname)
sys.meta_path.insert(0,Refuse())
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.amber_parameters import read_prmtop
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.preparation_integrity import disposition_census
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.contracts import model_roster
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
rows = tuple(('model.'+'.'.join(row),A.NOT_ATTEMPTED,('EXPOSED',)) for row in model_roster())
assert disposition_census(rows)[1] is A.NOT_ATTEMPTED
assert read_prmtop('%VERSION exposed\\n%FLAG TITLE\\n%FORMAT(20a4)\\nTEST\\n')['TITLE'] == ('TEST',)
'''
    result = subprocess.run([sys.executable,"-c",code],cwd=tmp_path,env=dict(os.environ,PYTHONPATH=str(source),PYTHONDONTWRITEBYTECODE="1"),capture_output=True,text=True,check=False)
    assert result.returncode == 0,result.stderr


MODEL_IDS = tuple("model."+".".join(row) for row in (
    (construct,joint,parameter) for construct in ("gp.i95m.m1","gp.i95m.v1","gp.wt.m1","gp.wt.v1","te.p415a.v98m","te.p415a.wt-ssu")
    for joint in ("joint-01","joint-02") for parameter in ("published-global-kcx-override","scoped-kcx-aliases")))


@pytest.mark.parametrize("verdict",tuple(A))
def test_every_disposition_keeps_complete24_literal_denominator(verdict):
    rows = tuple((name,verdict,("EXPOSED",)) for name in MODEL_IDS)
    counts,overall = disposition_census(rows)
    assert sum(count for _,count in counts) == 24
    assert dict(counts)[verdict] == 24
    assert overall is verdict
    assert tuple(key for key,_ in counts) == tuple(A)


@pytest.mark.parametrize("rows",[(MODEL_IDS[0],)*24,MODEL_IDS[:-1],MODEL_IDS[::-1]])
def test_closed24_duplicate_missing_and_reordered_rows_refuse(rows):
    with pytest.raises(ValueError):
        disposition_census(tuple((name,A.SATISFIED,()) for name in rows))


def test_unknown_enum_and_mixed_negative_census_never_reduce_to_positive():
    rows = tuple((name,A.SATISFIED,()) for name in MODEL_IDS)
    for negative in (A.FALSIFIED,A.UNSUPPORTED,A.NOT_ATTEMPTED,A.UNEVALUABLE,A.REFUSED):
        counts,overall = disposition_census(((rows[0][0],negative,("ADVERSE",)),)+rows[1:])
        assert overall is negative and dict(counts)[A.SATISFIED] == 23
    with pytest.raises(ValueError,match="typed"):
        disposition_census(((rows[0][0],"UNKNOWN",()),)+rows[1:])


def exposed_preparation(verdict=A.REFUSED):
    def identity(name,schema,digest="0"*64):
        return ObjectIdentity(name,schema,"1.0.0",digest)
    source = c.PreparationSelection("input.exposed.preparation",
        identity("inventory.exposed","empirical-lawhood/rubisco-insilico-structure/inventory"),
        identity("coordinates.exposed","empirical-lawhood/rubisco-insilico-structure/assembly-coordinates"),
        identity("nomination.exposed","empirical-lawhood/rubisco-nomination-preparation/exploratory-dossier","8121b9e941cbc66d0634dbc9f3047c6e22232fb1a783f2a313a17bf5f63f35fa"),
        c.NATIVE_WORK_ROOT+"/exposed-unit-not-entered",c.ENGINE_INVENTORY_SHA256,
        preparation.controlled_constructs(**sequences()),
        (c.SourceMember("source.exposed","https://example.invalid/exposed",sha256(b"exposed").hexdigest(),"exposed"),))
    constructs = {row.construct_id:row for row in source.constructs}
    bundles = tuple(c.ModelAssets("product.assets.exposed."+str(index),c.identity(source),*roster,()) for index,roster in enumerate(c.model_roster()))
    models = tuple(c.PreparedModel(name,constructs[roster[0]],roster[1],roster[2],verdict,("EXPOSED",),(),c.identity(bundle),0,(),None,())
        for name,roster,bundle in zip(MODEL_IDS,c.model_roster(),bundles,strict=True))
    product = c.PreparationProduct("product.exposed.preparation",c.identity(source),source.structural_inventory,source.structural_coordinates,source.nomination,models,(),(),1)
    return source,product,bundles


def test_actual_census_retains_all_negative_rows_and_unknown_native_coverage():
    source,product,bundles = exposed_preparation(A.UNSUPPORTED)
    result = assess(source,product,bundles,(),(),{})
    assert result.assignment_disposition is A.UNSUPPORTED
    assert result.model_dispositions == tuple((name,A.UNSUPPORTED,("EXPOSED",)) for name in MODEL_IDS)
    assert result.retained_native_call_count == 0
    assert result.actual_native_attempt_count is result.actual_native_completed_count is None
    assert result.native_coverage_disposition is result.geometry_disposition is A.UNEVALUABLE
    assert result.physical_independent_units == 0
    with pytest.raises(ValueError,match="coverage"):
        replace(result,actual_native_attempt_count=0)


@pytest.mark.parametrize("verdict",(A.FALSIFIED,A.UNSUPPORTED,A.NOT_ATTEMPTED,A.UNEVALUABLE,A.REFUSED))
def test_legacy_public_projection_retains_adverse_enum_without_positive_fallback(monkeypatch,verdict):
    source,product,bundles = exposed_preparation(verdict)
    result = assess(source,product,bundles,(),(),{})
    monkeypatch.setattr(science,"assess_preparation_integrity",lambda *args:result)
    scope = c.scope(source)
    projected = science.assess_preparation(source,SimpleNamespace(scope=scope),None,None,product,bundles)
    assert projected.preparation_disposition is verdict
    assert len(projected.model_dispositions) == 24
    assert projected.dynamics_disposition is projected.kinetic_disposition is A.UNEVALUABLE


def test_positive_missing_raw_parameters_and_false_unattempted_work_refuse():
    source,product,bundles = exposed_preparation()
    row = product.models[0]
    fake = c.NativeTextFile(c.FileEvidence(row.model_id+"/exposed.txt",7,sha256(b"exposed").hexdigest()),"exposed")
    bundle = replace(bundles[0],files=(fake,))
    # One retained actual native call is required by the legacy producer, but
    # it cannot replace the complete independently assessable raw artifacts.
    call = c.NativeCall("call.exposed",None,row.model_id,"exposed","{}","{}",D(0),D(0),"COMPLETED",None,())
    positive = replace(row,disposition=A.SATISFIED,files=(fake.evidence,),assets=c.identity(bundle),atom_count=4,
        complete_parameter_census=(("atoms",4),("bonds",2),("angles",1),("dihedrals",1)),provenance_manifest_path=row.model_id+"/absent.json",native_call_ids=(call.call_id,))
    changed = replace(product,models=(positive,)+product.models[1:],native_calls=(call,),files=(fake.evidence,))
    with pytest.raises(ValueError,match="complete raw"):
        assess(source,changed,(bundle,)+bundles[1:],(),(),{})
    false = replace(row,disposition=A.NOT_ATTEMPTED,atom_count=1)
    with pytest.raises(ValueError,match="contradicts"):
        assess(source,replace(product,models=(false,)+product.models[1:]),bundles,(),(),{})


def test_independent_fixed_pdb_atom_denominator_and_numeric_refusals():
    raw = "HETATM    1  CA  ALA A   1       1.000   2.000   3.000  1.00  0.00           C  \n"
    assert read_heavy_pdb(raw)[0]["xyz"] == (D(1),D(2),D(3))
    for changed in (raw+raw,raw.replace("1.000","  NaN"),raw.replace(" C  ","    ")):
        with pytest.raises(ValueError):
            read_heavy_pdb(changed)


def test_missing_complete_heavy_protein_positions_and_source_chain_substitution_refuse():
    source,product,_ = exposed_preparation()
    model = product.models[0]
    chains = tuple(SimpleNamespace(pdb_id="1BWV",chain_id=f"chain{index:02}",full_sequence="A"*493 if index < 8 else "A"*138) for index in range(16))
    expected = [dict(chain="ABCDEFGHIJKLMNOP"[index],source_chain=row.chain_id,subunit="lsu" if index < 8 else "ssu",sequence=model.construct.lsu_sequence if index < 8 else model.construct.ssu_sequence) for index,row in enumerate(chains)]
    origin = dict(complete_chains=expected,selected_atom_origins=[])
    raw = "HETATM    1  CA  ALA A   1       1.000   2.000   3.000  1.00  0.00           C  \n"
    with pytest.raises(ValueError,match="protein residue denominator"):
        validate_origins(model,{},origin,raw,(),chains,set())
    changed = deepcopy(origin)
    changed["complete_chains"][0]["source_chain"] = "other"
    with pytest.raises(ValueError,match="chain/full genotype"):
        validate_origins(model,{},changed,raw,(),chains,set())


def full_exposed_origins():
    """Complete actual residue/atom example with explicit synthetic source role.

    One CA per residue demonstrates identity joins, not chemical completeness.
    The current integrity record leaves template/geometry/biology unevaluable.
    """
    source,product,_ = exposed_preparation()
    model = product.models[8]  # gp.wt.m1: processing M1 differs from source V1.
    reverse = {letter:name for name,letter in AMINO.items() if name not in ("KCX","HID","HIE","HIP","CYX")}
    chains, source_atoms, declared, amber_chains, selected, heavy, complete, joins, raw_lines = [],[],[],[],[],[],[],[],[]
    for chain_index in range(16):
        subunit = "lsu" if chain_index < 8 else "ssu"
        sequence = model.construct.lsu_sequence if subunit == "lsu" else model.construct.ssu_sequence
        original_sequence = sequence if subunit == "lsu" else "V"+sequence[1:]
        source_chain,chain = f"source{chain_index:02}","ABCDEFGHIJKLMNOP"[chain_index]
        chains.append(SimpleNamespace(pdb_id="1BWV",chain_id=source_chain,full_sequence=original_sequence))
        start = len(heavy)
        chain_row = dict(chain=chain,source_chain=source_chain,subunit=subunit,sequence=sequence)
        declared.append(chain_row)
        residue_names = [reverse[letter] for letter in sequence]
        amber_chains.append(chain_row | dict(amber_residue_indices=list(range(start,start+len(sequence))),actual_residue_names=residue_names))
        for position,component in enumerate(residue_names,1):
            index = len(heavy)
            origin = None
            if position == 1:
                original_component = reverse[original_sequence[0]]
                source_atom_id = str(chain_index+1)
                source_atoms.append(SimpleNamespace(pdb_id="1BWV",chain_id=source_chain,operator_id="1",source_atom_id=source_atom_id,label_seq_id="1",auth_seq_id="1",insertion_code="?",component_id=original_component,alternate_id=".",occupancy=D(1),atom_id="CA",xyz_angstrom=(D(1),D(2),D(3))))
                origin = dict(serial=chain_index+1,chain=chain,position=1,atom="CA",source=["1BWV","1",source_atom_id],
                    source_component=original_component,model_component=original_component,source_alternate=".",source_occupancy="1",original_xyz_angstrom=["1","2","3"])
                selected.append(origin)
            entry = dict(chain=chain,position=position,atom="CA",component=component,element="C",source_origin=origin,
                status="INHERITED_OBSERVED_SOURCE" if origin else "DECLARED_CONSTRUCTED_MUTANT_OR_MISSING_ATOM")
            complete.append(entry)
            heavy.append(dict(chain=chain,position=position,atom="CA"))
            raw_lines.append(f"HETATM{index+1:5d}  CA  {component:>3} {chain}{position:4d}       1.000   2.000   3.000  1.00  0.00           C  \n")
            joins.append(dict(amber_atom_index=index,amber_residue_index=index,chain=chain,position=position,atom="CA",residue_name=component,source_origin=entry,status="REALIZED_COMPLETE_PREPARATION_ATOM"))
    size = len(heavy)
    census = dict(term_census=dict(atoms=size),residue_starts=tuple(range(1,size+1)),residue_names=tuple(row["component"] for row in complete),atom_names=("CA",)*size,atomic_numbers=(6,)*size,indexed_bonded_terms={"BONDS_WITHOUT_HYDROGEN":(),"BONDS_INC_HYDROGEN":()})
    origin = dict(complete_chains=declared,selected_atom_origins=selected,complete_heavy_atoms=complete,
        amber_realization=dict(complete_chains=amber_chains,atoms=joins),authenticated_disulfides=[])
    return model,census,origin,"".join(raw_lines),tuple(source_atoms),tuple(chains)


def test_complete_actual_raw_origins_join_full5048_residues_and_processing_contrast():
    args = full_exposed_origins()
    assert validate_origins(*args,set()) == (5048,5048)


@pytest.mark.parametrize("mutation",("source-token","raw-element","raw-residue","missing-amber-atom","amber-origin","false-observed-built","added-native-heavy"))
def test_full_raw_origin_counterexamples_refuse(mutation):
    model,census,origin,raw,atoms,chains = full_exposed_origins()
    if mutation == "source-token":origin["complete_heavy_atoms"][0]["source_origin"]["original_xyz_angstrom"][0] = "1.001"
    if mutation == "raw-element":census["atomic_numbers"] = (7,)+census["atomic_numbers"][1:]
    if mutation == "raw-residue":census["residue_names"] = ("LYS",)+census["residue_names"][1:]
    if mutation == "missing-amber-atom":origin["amber_realization"]["atoms"].pop()
    if mutation == "amber-origin":origin["amber_realization"]["atoms"][0]["chain"] = "other"
    if mutation == "false-observed-built":origin["complete_heavy_atoms"][1]["source_origin"] = origin["selected_atom_origins"][0]
    if mutation == "added-native-heavy":census["atom_names"] = ("FAKE",)+census["atom_names"][1:]
    with pytest.raises(ValueError):
        validate_origins(model,census,origin,raw,atoms,chains,set())


def test_additive_integrity_schema_does_not_revise_legacy_records():
    assert PreparationIntegrity.SCHEMA.endswith("/preparation-integrity")
    assert c.PreparationAssessment.SCHEMA.endswith("/preparation-assessment")
    assert c.PreparationAssessment.VERSION == "1.0.0"
    assert assigned_census(read_prmtop(amber_text(topology())))["term_census"]["atoms"] == 4
