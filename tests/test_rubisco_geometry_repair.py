# SPDX-License-Identifier: MPL-2.0
"""Adverse repair-source, native-census and independent numerical-read controls."""

from dataclasses import replace
from decimal import Decimal as D
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.contracts import FileEvidence
from empirical_lawhood.domains.rubisco.rubisco_response.construction_engine import NUMERIC_PACKAGES, GpRepairNumericEngine
from empirical_lawhood.adapters.rubisco.rubisco_response.construction_engine import authenticate_numeric_engine
from empirical_lawhood.domains.rubisco.rubisco_response.gp_geometry_repair_assessment import _array, _omega_degrees
from empirical_lawhood.adapters.rubisco.rubisco_response.gp_geometry_repair_native import join_heavy_atoms, movable_atoms
from empirical_lawhood.domains.rubisco.rubisco_response.gp_geometry_repair_operation import BUDGET, CAPABILITY, _decode, operation_declaration
from empirical_lawhood.science.evidence.evidence import OutcomeAccess


def numeric_engine(directory):
    for name in NUMERIC_PACKAGES:
        child=directory/name;child.mkdir(parents=True)
        (child/"exposed.txt").write_bytes(b"not an executable numerical engine\n")
    interpreter=Path(sys.executable).resolve()
    return GpRepairNumericEngine("engine.exposed-numeric-stock",str(directory),
        tuple(FileEvidence(p.relative_to(directory).as_posix(),p.stat().st_size,sha256(p.read_bytes()).hexdigest())
            for p in sorted(directory.rglob("*"),key=str) if p.is_file()),str(interpreter),sha256(interpreter.read_bytes()).hexdigest())


@pytest.mark.parametrize("change",("extra","missing","bytes","link","interpreter"))
def test_numeric_closure_cannot_change_after_selection(tmp_path,change):
    engine=numeric_engine(tmp_path)
    authenticate_numeric_engine(engine)
    member=tmp_path/NUMERIC_PACKAGES[0]/"exposed.txt"
    if change=="extra":(member.parent/"undeclared.txt").write_text("unexpected")
    elif change=="missing":member.unlink()
    elif change=="bytes":member.write_text("substitution")
    elif change=="link":member.unlink();member.symlink_to(tmp_path/NUMERIC_PACKAGES[1]/"exposed.txt")
    else:engine=replace(engine,interpreter_sha256="0"*64)
    with pytest.raises((ValueError,FileNotFoundError)):authenticate_numeric_engine(engine)


def test_all_hydrogens_move_while_each_retains_its_unique_heavy_parent():
    census=dict(term_census={"atoms":6},atomic_numbers=(6,1,6,1,8,1),
        indexed_bonded_terms={"BONDS_INC_HYDROGEN":((0,3,1),(6,9,1),(12,15,1)),
            "BONDS_WITHOUT_HYDROGEN":((0,6,1),(6,12,1))})
    joined=((('A',1,'CA'),0),(('A',1,'CB'),2),(('Z',1,'O'),4))
    assert movable_atoms(census,joined,(("A",1,"CB"),))==(1,2,3,5)
    census["indexed_bonded_terms"]["BONDS_INC_HYDROGEN"]+=((0,9,1),)
    with pytest.raises(ValueError,match="uniquely attached"):movable_atoms(census,joined,(("A",1,"CB"),))


def test_heavy_join_preserves_names_elements_and_exact_initial_coordinates():
    text="ATOM      1  CA  ALA A   1       1.000   2.000   3.000  1.00  0.00           C  \nEND\n"
    census=dict(residue_starts=(1,),residue_names=("ALA",),atom_names=("HA","CA"),atomic_numbers=(1,6),term_census={"atoms":2})
    coordinates=((D(0),D(0),D(0)),(D(1),D(2),D(3)))
    assert join_heavy_atoms(text,census,coordinates)==((("A",1,"CA"),1),)
    with pytest.raises(ValueError,match="element or starting coordinate"):
        join_heavy_atoms(text,census,(*coordinates[:1],(D(1),D(2),D("3.000002"))))
    census["atomic_numbers"]=(1,7)
    with pytest.raises(ValueError,match="element or starting coordinate"):join_heavy_atoms(text,census,coordinates)


@pytest.mark.parametrize("change",(None,"nonwater","extra-heavy","different-water"))
def test_water_triangle_keeps_unique_heavy_parents_and_refuses_other_hydrogen_edges(change):
    census=dict(term_census={"atoms":6},atomic_numbers=(8,1,1,8,1,1),
        residue_starts=(1,4),residue_names=("WAT","WAT"),atom_names=("O","H1","H2","O","H1","H2"),
        indexed_bonded_terms={"BONDS_INC_HYDROGEN":((0,3,1),(0,6,1),(3,6,2),(9,12,1),(9,15,1),(12,15,2))})
    if change=="nonwater":census["residue_names"]=("UNK","WAT")
    elif change=="extra-heavy":census["indexed_bonded_terms"]["BONDS_INC_HYDROGEN"]+=((9,3,1),)
    elif change=="different-water":census["indexed_bonded_terms"]["BONDS_INC_HYDROGEN"]+=((3,12,2),)
    joined=((('Z',1,'O'),0),(('Z',2,'O'),3))
    if change:
        with pytest.raises(ValueError,match="uniquely attached"):movable_atoms(census,joined,(("Z",1,"O"),))
    else:
        assert movable_atoms(census,joined,())==(1,2,4,5)
        assert movable_atoms(census,joined,(("Z",1,"O"),))==(0,1,2,4,5)


def test_amber_water_partition_keeps_every_original_atom_and_refuses_coordinate_changes():
    records=(("A",1,"ALA","CA","C",1),("Z",1,"HOH","O","O",2),("Z",2,"MG","MG","MG",3))
    text=""
    for serial,(chain,pos,residue,name,element,x) in enumerate(records,1):
        label=name.rjust(4) if len(element)==2 else (" "+name).ljust(4)
        text+=f"HETATM{serial:5d} {label} {residue:3s} {chain}{pos:4d}    {x:8.3f}{0:8.3f}{0:8.3f}  1.00  0.00          {element:>2s}  \n"
    census=dict(residue_starts=(1,2,3),residue_names=("ALA","MG","WAT"),atom_names=("CA","MG","O","H1","H2"),
        atomic_numbers=(6,12,8,1,1),term_census={"atoms":5})
    xyz=tuple((D(x),D(0),D(0)) for x in (1,3,2,2.5,1.5))
    assert join_heavy_atoms(text,census,xyz)==((("A",1,"CA"),0),(("Z",1,"O"),2),(("Z",2,"MG"),1))
    with pytest.raises(ValueError,match="element or starting coordinate"):
        join_heavy_atoms(text,census,(xyz[0],xyz[1],(D("2.01"),D(0),D(0)),*xyz[3:]))


@pytest.mark.parametrize("change",("shape","precision","nan"))
def test_independent_array_reader_refuses_lost_precision_or_denominators(change):
    values=np.zeros((3,3),dtype=np.float64)
    if change=="shape":values=values[:2]
    elif change=="precision":values=values.astype(np.float32)
    else:values[0,0]=np.nan
    stream=BytesIO();np.save(stream,values,allow_pickle=False)
    with pytest.raises(ValueError,match="complete finite double"):_array(stream.getvalue(),3)


@pytest.mark.numerical(oracle="Coplanar four-point controls have independently known cis=0 degrees and trans=180 degrees; coincident points are explicitly degenerate.")
def test_independent_peptide_dihedral_distinguishes_cis_trans_and_degenerate():
    common=((0,1,0),(0,0,0),(1,0,0))
    assert abs(_omega_degrees((*common,(1,-1,0))))==180
    assert _omega_degrees((*common,(1,1,0)))==0
    assert _omega_degrees(((0,0,0),)*4)==0


def test_metadata_and_incomplete_worker_inputs_make_no_native_contact(monkeypatch):
    from empirical_lawhood.domains.rubisco.rubisco_response import gp_geometry_repair_operation as owner
    def forbidden(*args,**kwargs):raise AssertionError("metadata or incomplete input reached native work")
    monkeypatch.setattr(owner,"authenticate_engine",forbidden)
    monkeypatch.setattr(owner,"authenticate_numeric_engine",forbidden)
    declared=operation_declaration()
    assert declared.execution_properties.native_effect and declared.resources.wall_time_seconds is None
    assert declared.resources.cpu_cores==8 and declared.resources.memory_bytes==8*2**30
    for count in (0,1,2,4):
        context=SimpleNamespace(task_id=CAPABILITY,permissions=declared.manifest().permissions,resource_budget=BUDGET,
            outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,input_ports=(object(),)*count)
        with pytest.raises(ValueError,match="complete task/input"):_decode(context)


def test_native_preparation_preserves_the_complete_canonical_output_census():
    from empirical_lawhood.domains.rubisco.rubisco_response.gp_geometry_repair import GEOMETRY_ID, GpGeometryRepairInput
    from empirical_lawhood.domains.rubisco.rubisco_response.gp_geometry_repair_operation import GpGeometryRepairConfig, native_work
    from empirical_lawhood.science.identity.numerical_provenance import NumericalProducingProvenance
    from empirical_lawhood.science.identity.provenance import ObjectIdentity
    from empirical_lawhood.execution.native_effects import NativeEffectContact
    parent=NativeEffectContact("exposed.run",CAPABILITY,"exposed.run."+CAPABILITY+".attempt-001",
        ObjectIdentity("plan.exposed","empirical-lawhood/runtime/development-execution-plan","1.0.0","1"*64),
        ObjectIdentity(CAPABILITY,"empirical-lawhood/runtime/execution-task","1.0.0","2"*64),
        "3"*40,("materialization.exposed.input",),())
    config=SimpleNamespace(identity=ObjectIdentity("config.exposed",GpGeometryRepairConfig.SCHEMA,"1.0.0","4"*64),
        source=SimpleNamespace(identity=ObjectIdentity("source.exposed",GpGeometryRepairInput.SCHEMA,"1.0.0","5"*64)),
        provenance=SimpleNamespace(identity=ObjectIdentity("provenance.exposed",NumericalProducingProvenance.SCHEMA,"1.0.0","6"*64)),
        implementation=SimpleNamespace(code_sources_sha256="7"*64,dependency_lock_sha256="8"*64),fingerprint=lambda:"9"*64)
    context=SimpleNamespace(input_ports=(SimpleNamespace(materialization_id="materialization.exposed.input"),))
    work=native_work(context,config,parent)
    assert len(work.definitions)==1 and work.definitions[0].subwork_id==GEOMETRY_ID
    assert tuple(port.output_id for port in work.definitions[0].outputs)==("files.census","files.raw","repair.return")
    assert work.rosters[0].subworks==(work.definitions[0].identity,)
