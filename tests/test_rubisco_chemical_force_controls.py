# SPDX-License-Identifier: MPL-2.0
"""Exposed PURE numerical/custody controls; no molecular qualification."""

from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
import json
import math
from io import BytesIO
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import contracts as p
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_contracts import DurableUnitReturn
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.physical_preparation_geometry import PhysicalPreparationGeometry
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.preparation_integrity import PreparationIntegrity
from empirical_lawhood.adapters.methods.rubisco_insilico_sampling import control_contracts as c
from empirical_lawhood.adapters.methods.rubisco_insilico_sampling.control_instrumentation import TerminalReporterCapture
from empirical_lawhood.adapters.methods.rubisco_insilico_sampling.control_science import assess_control, constraints_from_system_xml, reduce_same_geometry_force_control, reduce_terminal_minimizer, terminal_objective_reduction
from empirical_lawhood.adapters.methods.rubisco_insilico_sampling.control_native_ledger import ChemicalForceLedger, request_values
from empirical_lawhood.adapters.methods.rubisco_insilico_sampling import control_roster
from empirical_lawhood.adapters.methods.rubisco_insilico_sampling.control_runner import ChemicalForceRunner
from empirical_lawhood.adapters.methods.rubisco_insilico_sampling.control_native_entry import validate_plugin_environment
from empirical_lawhood.adapters.methods.rubisco_insilico_sampling.science import hardware_from_stdout
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.execution import WorkerInputBinding, WorkerInputKind, WorkerInputPort, WorkerOutputPort
from empirical_lawhood.runtime.native_subwork import NativeSubworkCompletion, NativeSubworkDefinition, NativeSubworkRoster, NativeSubworkState
from tests.test_rubisco_durable_preparation import selected as selected, unit


def exposed_identity(name, kind):
    return ObjectIdentity("exposed."+name,kind.SCHEMA,"1.0.0",sha256(name.encode()).hexdigest())


@pytest.fixture
def plan():
    key = p.model_roster()[0]
    selected = c.model_id(key)
    return c.ChemicalForcePlan("config.exposed.chemical-control",
        exposed_identity("source",p.PreparationSelection),exposed_identity("preparation",p.PreparationProduct),
        exposed_identity("assignment",PreparationIntegrity),exposed_identity("geometry",PhysicalPreparationGeometry),
        ((selected,exposed_identity("model",p.ModelAssets)),),
        ((selected,exposed_identity("definition",NativeSubworkDefinition),
            exposed_identity("completion",NativeSubworkCompletion),exposed_identity("return",DurableUnitReturn)),),
        hardware_from_stdout(b"GPU-exposed, Exposed device, 0, 0000:00:00.0, 1, 0\n"),
        p.NATIVE_WORK_ROOT+"/exposed-control-never-entered","/tmp/exposed-python","1"*64,"2"*64,
        "/tmp/exposed-hardware-inspector","3"*64,(("src/exposed.py","4"*64),),"5"*64)


@pytest.mark.parametrize("field,value",[("selected_assets",()),("model_census",p.model_roster()[:-1]),
    ("nve_census",()),("minimizer_max_iterations",100), ("minimizer_reporter_early_stop",True)])
def test_subset_needs_actual_assets_full_denominators_and_native_stopping(plan,field,value):
    with pytest.raises(ValueError):
        replace(plan,**{field:value})


def test_chemical_force_census_preserves_all_24_and_96_unentered_controls(plan):
    census=c.ChemicalForceCensus(plan.identity,tuple((name,NativeSubworkState.NOT_ENTERED) for name in c.control_ids()))
    assert len(census.states)==120
    assert sum(name.startswith("control.nve.") for name,_ in census.states)==96
    assert sum(name.startswith("control.chemical-force.") for name,_ in census.states)==24
    with pytest.raises(ValueError):
        replace(census,states=census.states[:-1])


def test_all_callback_rows_restarts_and_final_arrays_survive_known_error(tmp_path):
    capture=TerminalReporterCapture(tmp_path,np)
    for ordinal,(iteration,strength) in enumerate(((0,1000.),(1,1000.),(0,10000.)),1):
        point=np.arange(6,dtype=float)+ordinal
        gradient=np.full(6,float(ordinal))
        if ordinal==3:
            gradient[-1]=np.nan
        assert capture.record(iteration,point,gradient,{"system energy":-1.,
            "restraint energy":strength,"restraint strength":strength,"max constraint error":.1}) is False
    capture.finish(native_returned=False,error_text="exposed known native failure")
    rows=[json.loads(line) for line in (tmp_path/"minimizer-progress.jsonl").read_text().splitlines()]
    assert [r["callback_ordinal"] for r in rows]==[1,2,3]
    assert [r["optimizer_iteration_index"] for r in rows]==[0,1,0]
    assert all(not r["reporter_requests_early_stop"] for r in rows)
    with np.load(tmp_path/"minimizer-terminal.npz",allow_pickle=False) as raw:
        np.testing.assert_array_equal(raw["x_nm"],np.arange(6,dtype=float)+3)
        assert np.isnan(raw["objective_gradient_kj_mol_nm"][-1])
    terminal=json.loads((tmp_path/"minimizer-termination.json").read_text())
    assert terminal["native_returned"] is False and terminal["callback_count"]==3
    assert terminal["max_iterations"]==0 and terminal["reporter_ever_requests_early_stop"] is False


@pytest.mark.parametrize("changed,verdict",[("none",A.SATISFIED),("point",A.UNEVALUABLE),
    ("gradient",A.REFUSED),("constraint",A.REFUSED)])
def test_terminal_native_objective_and_every_constraint_are_independent_requirements(changed,verdict):
    final=np.array([[0.,0.,0.],[1.,0.,0.]])
    point=final.reshape(-1).copy()
    gradient=np.full(6,.5)
    target="1"
    if changed=="point":point[0]=.01
    if changed=="gradient":gradient[:]=11.
    if changed=="constraint":target="1.05"
    rms,residual,status,reasons=terminal_objective_reduction(point,gradient,final,((0,1,target),),
        atom_count=2,constraint_tolerance=Decimal("0.000001"))
    assert status is verdict
    expected=(11. if changed=="gradient" else .5)*math.sqrt(3.)
    assert abs(rms-Decimal(str(expected))) < Decimal("0.000000000001")
    assert (residual>0)==(changed=="constraint")
    assert bool(reasons)==(verdict is not A.SATISFIED)


def test_missing_nonfinite_native_gradient_never_becomes_positive():
    with pytest.raises(ValueError,match="finite native arrays"):
        terminal_objective_reduction(np.zeros(6),np.array([0.,0.,0.,0.,0.,np.nan]),np.zeros((2,3)),(),
            atom_count=2,constraint_tolerance=Decimal("1e-6"))


def test_objective_gate_uses_full_vector_norm_per_particle_not_per_component():
    rms,_,verdict,_=terminal_objective_reduction(np.zeros(6),np.full(6,6.),np.zeros((2,3)),(),
        atom_count=2,constraint_tolerance=Decimal("1e-6"))
    assert rms>Decimal("10") and verdict is A.REFUSED


def test_binary64_objective_boundary_does_not_turn_a_small_exact_miss_into_satisfied():
    gradient=np.array([6.,8.,1e-8])
    assert float(np.linalg.norm(gradient))==10.
    rms,_,verdict,_=terminal_objective_reduction(np.zeros(3),gradient,np.zeros((1,3)),(),
        atom_count=1,constraint_tolerance=Decimal("1e-6"))
    assert rms>10 and verdict is A.REFUSED


def test_exact_squared_constraint_boundary_and_nonreal_native_operands():
    final=np.array([[0.,0.,0.],[1.,1e-8,0.]])
    assert math.dist(final[0],final[1])==1.
    _,residual,verdict,_=terminal_objective_reduction(final.reshape(-1),np.zeros(6),final,((0,1,"1"),),
        atom_count=2,constraint_tolerance=Decimal("0.00000000000000004"))
    assert residual>Decimal("0.00000000000000004") and verdict is A.REFUSED
    with pytest.raises(ValueError,match="no silent conversion"):
        terminal_objective_reduction(np.zeros(3),np.array([1+1j,2.,3.]),np.zeros((1,3)),(),
            atom_count=1,constraint_tolerance=Decimal("1e-6"))


@pytest.mark.parametrize("changed",["none","system","box","positions","groups","relaxed","force","energy",
    "tiny-position","signed-zero-position","complex-force","float32-force","nonfinite-force",
    "signed-zero-force","signed-zero-energy"])
def test_backend_agreement_requires_same_system_relaxed_source_full_geometry_and_box(changed):
    system=b'<System type="System" version="1"><Particles><Particle mass="1"/><Particle mass="1"/></Particles><Constraints><Constraint p1="0" p2="1" d="1"/></Constraints></System>'
    state=b'<State type="State" version="1"><PeriodicBoxVectors><A x="1" y="0" z="0"/><B x="0" y="1" z="0"/><C x="0" y="0" z="1"/></PeriodicBoxVectors><Positions><Position x="0" y="0" z="0"/><Position x="0" y="0" z="0"/></Positions><Forces><Force x="1" y="1" z="1"/><Force x="1" y="1" z="1"/></Forces><Energies PotentialEnergy="-1" KineticEnergy="0"/></State>'
    digest,relaxed=sha256(system).hexdigest(),sha256(state).hexdigest()
    data=dict(cpu_force_kj_mol_nm=np.ones((2,3)),cuda_force_kj_mol_nm=np.ones((2,3)),
        cpu_positions_nm=np.zeros((2,3)),cuda_positions_nm=np.zeros((2,3)),
        cpu_potential_kj_mol=-1.,cuda_potential_kj_mol=-1.,
        cpu_box_vectors_nm=np.eye(3),cuda_box_vectors_nm=np.eye(3),
        cpu_system_xml_sha256=np.array(digest),cuda_system_xml_sha256=np.array(digest),
        cpu_integration_force_groups=np.array(-1),cuda_integration_force_groups=np.array(-1),
        common_relaxed_state_sha256=np.array(relaxed))
    if changed=="system":data["cpu_system_xml_sha256"]=np.array("3"*64)
    if changed=="box":data["cpu_box_vectors_nm"][0,0]=2.
    if changed=="positions":data["cpu_positions_nm"][0,0]=1.
    if changed=="groups":data["cpu_integration_force_groups"]=np.array(1)
    if changed=="relaxed":data["common_relaxed_state_sha256"]=np.array("4"*64)
    if changed=="force":data["cpu_force_kj_mol_nm"][0,0]=2.
    if changed=="energy":data["cpu_potential_kj_mol"]=-2.
    if changed=="tiny-position":data["cpu_positions_nm"][0,0]=1e-15
    if changed=="signed-zero-position":data["cpu_positions_nm"][0,0]=-0.
    if changed=="complex-force":data["cpu_force_kj_mol_nm"]=np.ones((2,3),dtype=complex)
    if changed=="float32-force":data["cpu_force_kj_mol_nm"]=np.ones((2,3),dtype=np.float32)
    if changed=="nonfinite-force":data["cpu_force_kj_mol_nm"][0,0]=np.nan
    if changed=="signed-zero-force":
        state=state.replace(b'<Force x="1" y="1" z="1"/>',b'<Force x="0" y="0" z="0"/>')
        data["cpu_force_kj_mol_nm"]=np.zeros((2,3))
        data["cuda_force_kj_mol_nm"]=np.zeros((2,3))
        data["cpu_force_kj_mol_nm"][0,0]=-0.
    if changed=="signed-zero-energy":
        state=state.replace(b'PotentialEnergy="-1"',b'PotentialEnergy="0"')
        data["cpu_potential_kj_mol"],data["cuda_potential_kj_mol"]=-0.,0.
    if changed in ("signed-zero-force","signed-zero-energy"):
        data["common_relaxed_state_sha256"]=np.array(sha256(state).hexdigest())
    if changed=="none":
        assert reduce_same_geometry_force_control(data,2,system_xml=system,relaxed_state_xml=state,cpu_state_xml=state)==(Decimal("0.0"),Decimal("0.0"))
    else:
        with pytest.raises(ValueError):
            reduce_same_geometry_force_control(data,2,system_xml=system,relaxed_state_xml=state,cpu_state_xml=state)


@pytest.mark.parametrize("changed",["tiny","signed-zero"])
def test_final_callback_point_requires_exact_returned_state_bits(changed):
    point=np.zeros(3)
    point[0]=1e-15 if changed=="tiny" else -0.
    _,_,verdict,reasons=terminal_objective_reduction(point,np.zeros(3),np.zeros((1,3)),(),
        atom_count=1,constraint_tolerance=Decimal("1e-6"))
    assert verdict is A.UNEVALUABLE
    assert reasons==("FINAL_CONTEXT_DIFFERS_FROM_TERMINAL_OBJECTIVE_POINT",)


def test_actual_system_constraint_census_is_read_independently():
    raw=b'<System type="System" version="1"><Particles><Particle mass="1"/><Particle mass="1"/></Particles><Constraints><Constraint p1="0" p2="1" d="0.10000000000000001"/></Constraints></System>'
    assert constraints_from_system_xml(raw)==(2,((0,1,Decimal("0.10000000000000001")),))
    with pytest.raises(ValueError,match="incomplete"):
        constraints_from_system_xml(raw.replace(b'<Constraints><Constraint p1="0" p2="1" d="0.10000000000000001"/></Constraints>',b''))


@pytest.mark.parametrize("changed,verdict",[("none",A.SATISFIED),("missing",A.UNEVALUABLE),
    ("point",A.UNEVALUABLE),("objective",A.REFUSED),("constraint",A.REFUSED),("error",A.UNEVALUABLE)])
def test_terminal_assessment_reads_actual_native_constraint_and_callback_denominators(tmp_path,changed,verdict):
    system=b'<System type="System" version="1"><Particles><Particle mass="1"/><Particle mass="1"/></Particles><Constraints><Constraint p1="0" p2="1" d="1"/></Constraints></System>'
    integrator=b'<Integrator type="VerletIntegrator" version="1" constraintTolerance="0.000001" integrationForceGroups="-1"/>'
    state=b'<State type="State" version="1"><PeriodicBoxVectors><A x="1" y="0" z="0"/><B x="0" y="1" z="0"/><C x="0" y="0" z="1"/></PeriodicBoxVectors><Positions><Position x="0" y="0" z="0"/><Position x="1" y="0" z="0"/></Positions></State>'
    point=np.array([0.,0.,0.,1.,0.,0.])
    if changed=="point":point[0]=.01
    if changed=="constraint":system=system.replace(b'd="1"',b'd="1.05"')
    capture=TerminalReporterCapture(tmp_path,np)
    if changed!="missing":
        capture.record(0,point,np.full(6,11. if changed=="objective" else .5),{"restraint strength":1000.})
    capture.finish(native_returned=changed!="error",error_text="exposed known exception" if changed=="error" else None)
    termination=json.loads((tmp_path/"minimizer-termination.json").read_text())
    terminal=None
    if changed!="missing":
        with np.load(tmp_path/"minimizer-terminal.npz",allow_pickle=False) as values:
            terminal={name:values[name] for name in values.files}
    with (tmp_path/"minimizer-progress.jsonl").open() as rows:
        result=reduce_terminal_minimizer(terminal,termination,(json.loads(line) for line in rows),
            system_xml=system,integrator_xml=integrator,relaxed_state_xml=state)
    assert result[2] is verdict
    assert bool(result[3]) is (verdict is not A.SATISFIED)


def test_unchanged_durable_call_owner_receives_exact_decimal_science_and_retains_return(selected):
    definition,entry,directory,_=unit(selected)
    ledger=ChemicalForceLedger(selected.progress,selected.plan,selected.root,entry,directory)
    original=Decimal("0.00000100")
    request=dict(ewald_error_tolerance=original,cutoff_nanometer=Decimal("1.000"))
    assert request_values(request)==dict(ewald_error_tolerance={"decimal":"0.00000100"},cutoff_nanometer={"decimal":"1.000"})
    assert ledger.call("exposed.control-return",request,lambda:None) is None
    actual=ledger.call_definitions[0]
    assert selected.progress.recover(actual).completion.definition==actual.identity
    record=json.loads(b"".join(selected.progress.iter_completed_output(actual,"call.return")))
    assert json.loads(record["value"]["requested_json"])==request_values(request)
    assert request["ewald_error_tolerance"] is original


def test_all_120_definitions_use_real_initial_roster_contract_with_unentered_nve_scope(plan,selected):
    sources=(plan.source,plan.preparation,plan.assignment_integrity,plan.mathematical_geometry,
        *(row[1] for row in plan.selected_assets),*(identity for row in plan.preparation_custody for identity in row[1:]))
    rows=control_roster.definitions(plan,selected.progress.parent_contact,sources=sources,
        input_materialization_ids=selected.progress.parent_contact.input_materialization_ids)
    assert len(rows)==121
    actual=NativeSubworkRoster("selected.native-subwork",selected.progress.parent_contact,tuple(row.identity for row in rows))
    assert len(actual.subworks)==121
    nve=tuple(row for row in rows if row.subwork_id.startswith("control.nve."))
    assert len(nve)==96 and all(row.operation_id=="rubisco.chemical-force.unentered-nve" and row.outputs==() for row in nve)
    assert all(row.configuration==plan.identity for row in rows)


@pytest.mark.parametrize("changed",["none","prefix","schema","input-bytes","input-access"])
def test_runner_checks_actual_typed_input_and_output_port_joins_before_native_effects(plan,selected,changed):
    # Exposed byte rows exercise only the operational join. The real child still
    # independently decodes/admit all original scientific records before effects.
    rows={identity.object_id:(identity,b"exposed "+identity.object_id.encode()) for identity in (
        plan.source,plan.preparation,plan.assignment_integrity,plan.mathematical_geometry,
        *(row[1] for row in plan.selected_assets),*(identity for row in plan.preparation_custody for identity in row[1:]))}
    authenticated={name:replace(identity,object_fingerprint=sha256(raw).hexdigest()) for name,(identity,raw) in rows.items()}
    actual_plan=replace(plan,source=authenticated[plan.source.object_id],preparation=authenticated[plan.preparation.object_id],
        assignment_integrity=authenticated[plan.assignment_integrity.object_id],mathematical_geometry=authenticated[plan.mathematical_geometry.object_id],
        selected_assets=tuple((name,authenticated[identity.object_id]) for name,identity in plan.selected_assets),
        preparation_custody=tuple((name,*(authenticated[identity.object_id] for identity in identities))
            for name,*identities in plan.preparation_custody))
    actual={name:(authenticated[name],raw) for name,(_,raw) in rows.items()}
    actual[actual_plan.plan_id]=actual_plan.identity,actual_plan.canonical_bytes()
    ports=[]
    for ordinal,(name,(identity,raw)) in enumerate(sorted(actual.items())):
        binding=WorkerInputBinding(name,"exposed.materialized."+str(ordinal),identity.object_schema,"application/json",len(raw),
            VisibilityCeiling.DEVELOPMENT_ONLY,OutcomeAccess.DEVELOPMENT_VISIBLE,WorkerInputKind.EXTERNAL)
        if changed=="input-bytes" and ordinal==0:raw=raw[::-1]
        if changed=="input-access" and ordinal==0:binding=replace(binding,visibility_ceiling=VisibilityCeiling.OUTCOME_VISIBLE)
        ports.append(WorkerInputPort(binding,BytesIO(raw)))
    parent=replace(selected.progress.parent_contact,input_materialization_ids=tuple(sorted(port.materialization_id for port in ports)))
    definitions=control_roster.definitions(actual_plan,parent,sources=tuple(identity for name,(identity,_) in actual.items() if name!=actual_plan.plan_id),
        input_materialization_ids=parent.input_materialization_ids)
    force_id="control.chemical-force."+actual_plan.selected_assets[0][0]
    output_id="exposed.node."+force_id
    output=WorkerOutputPort(output_id,"empirical-lawhood/source/capture-assured-uninterpreted-public-bytes",ArtifactProfile.RAW_SOURCE_BYTES,"application/gzip")
    if changed=="prefix":output=replace(output,output_id=force_id)
    if changed=="schema":output=replace(output,payload_schema=c.ChemicalForceReturn.SCHEMA)
    context=SimpleNamespace(task_id=parent.task_id,input_ports=tuple(ports),outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
        output_ports=(output,WorkerOutputPort("exposed.node.census",c.ChemicalForceCensus.SCHEMA,ArtifactProfile.CANONICAL_JSON,"application/json")))
    environment=tuple(sorted(dict(PYTHONDONTWRITEBYTECODE="1",OPENMM_PLUGIN_DIR="/tmp/exposed-selected-plugins",OPENMM_CPU_THREADS="1",OPENBLAS_NUM_THREADS="1",OMP_NUM_THREADS="1",
        MKL_NUM_THREADS="1",NUMEXPR_NUM_THREADS="1",VECLIB_MAXIMUM_THREADS="1").items()))
    runner=ChemicalForceRunner(actual_plan,"/tmp/exposed-never-entered-invocation.json",definitions,environment,
        ((force_id,output_id),),"exposed.node.census")
    if changed=="none":assert runner.validate_context(context,SimpleNamespace(parent_contact=parent))==(force_id,)
    else:
        with pytest.raises(ValueError):runner.validate_context(context,SimpleNamespace(parent_contact=parent))


def test_control_composition_imports_no_native_or_coordinator_dependencies():
    script='''
import importlib.abc
import sys
blocked={"cryptography","pyarrow","h5py","onnx","safetensors","sqlalchemy","alembic","numpy","scipy","openmm","pdbfixer","parmed"}
class RefuseEffects(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,path=None,target=None):
        if fullname.split(".")[0] in blocked:raise AssertionError(fullname)
sys.meta_path.insert(0,RefuseEffects())
from empirical_lawhood.adapters.methods.rubisco_insilico_sampling import control_native_entry,control_runner,control_invocation,control_native_ledger
print("EXPOSED_COLD_IMPORT_PASSED")
'''
    result=subprocess.run([sys.executable,"-c",script],env=dict(os.environ,PYTHONPATH=str(Path(__file__).resolve().parents[1]/"src"),
        PYTHONDONTWRITEBYTECODE="1"),capture_output=True,text=True,check=True)
    assert result.stdout.strip()=="EXPOSED_COLD_IMPORT_PASSED"


@pytest.mark.parametrize("changed",["none","empty","missing-library","different-directory"])
def test_selected_existing_cuda_stock_and_explicit_loader_are_checked_without_context(changed):
    plugin="/tmp/exposed-engine/OpenMM.libs/lib/plugins"
    names=("libOpenMMCUDA.so","libOpenMMCPU.so","libOpenMMPME.so","libnvrtc.so.12","libcufft.so.11","libcudart.so.12")
    rows=[dict(kind="file",actual_path=plugin+"/"+name) for name in names]
    environment=dict(OPENMM_PLUGIN_DIR=plugin)
    if changed=="empty":environment["OPENMM_PLUGIN_DIR"]=""
    if changed=="missing-library":rows=rows[:-1]
    if changed=="different-directory":environment["OPENMM_PLUGIN_DIR"]="/tmp/other-engine"
    if changed=="none":assert set(validate_plugin_environment(dict(entries=rows),environment))==set(names)
    else:
        with pytest.raises(ValueError):validate_plugin_environment(dict(entries=rows),environment)


@pytest.mark.parametrize("changed",["none","missing-callback","unsupported-xml"])
def test_complete_exposed_raw_assessment_keeps_numerical_and_native_physical_claims_distinct(plan,tmp_path,changed):
    from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_preparation import directory_census
    directory=tmp_path/"shared-model.exposed"
    directory.mkdir()
    system=b'<System type="System" version="1"><Particles><Particle mass="1"/><Particle mass="1"/></Particles><Constraints><Constraint p1="0" p2="1" d="1"/></Constraints></System>'
    integrator=b'<Integrator type="VerletIntegrator" version="1" constraintTolerance="0.000001" integrationForceGroups="-1"/>'
    if changed=="unsupported-xml":integrator=integrator.replace(b' integrationForceGroups="-1"',b'')
    state=b'<State type="State" version="1"><PeriodicBoxVectors><A x="1" y="0" z="0"/><B x="0" y="1" z="0"/><C x="0" y="0" z="1"/></PeriodicBoxVectors><Positions><Position x="0" y="0" z="0"/><Position x="1" y="0" z="0"/></Positions><Forces><Force x="1" y="1" z="1"/><Force x="1" y="1" z="1"/></Forces><Energies PotentialEnergy="-1" KineticEnergy="0"/></State>'
    for name,raw in (("controlled-system-000001.xml",system),("controlled-integrator-000002.xml",integrator),
                     ("minimized.xml",state),("cpu-force-reference.xml",state)):
        (directory/name).write_bytes(raw)
    def evidence(name):
        raw=(directory/name).read_bytes()
        return dict(relative_path="shared-model.exposed/"+name,byte_count=len(raw),sha256=sha256(raw).hexdigest())
    apparatus=dict(system=evidence("controlled-system-000001.xml"),integrator=evidence("controlled-integrator-000002.xml"))
    for name in ("minimizer-apparatus.json","apparatus-cuda.json","apparatus-cpu.json"):
        (directory/name).write_text(json.dumps(apparatus))
    (directory/"declared-system-constraints.json").write_text('{"constraints":[]}')
    # The independent reader must use actual System constraints even when this
    # producer summary is deliberately empty.
    capture=TerminalReporterCapture(directory,np)
    if changed!="missing-callback":capture.record(0,np.array([0.,0.,0.,1.,0.,0.]),np.full(6,.5),{})
    capture.finish(native_returned=True,error_text=None)
    np.savez_compressed(directory/"independent-force-receivers.npz",cpu_force_kj_mol_nm=np.ones((2,3)),cuda_force_kj_mol_nm=np.ones((2,3)),
        cpu_positions_nm=np.array([[0.,0.,0.],[1.,0.,0.]]),cuda_positions_nm=np.array([[0.,0.,0.],[1.,0.,0.]]),
        cpu_potential_kj_mol=-1.,cuda_potential_kj_mol=-1.,cpu_box_vectors_nm=np.eye(3),cuda_box_vectors_nm=np.eye(3),
        cpu_system_xml_sha256=np.array(sha256(system).hexdigest()),cuda_system_xml_sha256=np.array(sha256(system).hexdigest()),
        cpu_integration_force_groups=np.array(-1),cuda_integration_force_groups=np.array(-1),common_relaxed_state_sha256=np.array(sha256(state).hexdigest()))
    returned=c.ChemicalForceReturn("control.chemical-force."+plan.selected_assets[0][0],plan.identity,plan.selected_assets[0][1],True,2,
        "shared-model.exposed/independent-force-receivers.npz",directory_census(directory,tmp_path).files,
        (exposed_identity("conditional-call",NativeSubworkDefinition),))
    result=assess_control(plan,returned,current_raw_root=tmp_path)
    assert result.objective_precision_disposition is (A.SATISFIED if changed=="none" else A.UNEVALUABLE)
    assert result.force_agreement_disposition is (A.UNEVALUABLE if changed=="unsupported-xml" else A.SATISFIED)
    assert all(row is A.UNEVALUABLE for row in (result.physical_preparation_disposition,result.ensemble_disposition,
        result.kinetic_disposition,result.native_optimizer_convergence_disposition))
    assert result.physical_independent_units==0
