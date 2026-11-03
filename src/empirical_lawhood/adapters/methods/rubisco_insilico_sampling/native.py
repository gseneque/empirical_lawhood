# SPDX-License-Identifier: MPL-2.0
"""Selected isolated native calibration and full structural sampling.

No import in this module creates a model or native context. The exact engine,
actual assessed file assets, allocation and programme paths precede effects.
"""

from decimal import Decimal
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import contracts as p
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A

from . import contracts as c, science, storage


def _json(path, value):
    storage.immutable_bytes(path,(json.dumps(value,sort_keys=True,separators=(",",":"),default=str)+"\n").encode())


def _platform_properties(platform, context):
    return {name:platform.getPropertyValue(context,name) for name in platform.getPropertyNames()}


def _context(mm, ledger, directory, system, integrator, platform_name, properties):
    """Retain complete applied System/Integrator before each native constructor."""
    ordinal=ledger.counter+1
    system_path=directory/("system-"+str(ordinal).zfill(8)+".xml")
    integrator_path=directory/("integrator-"+str(ordinal).zfill(8)+".xml")
    storage.immutable_bytes(system_path,mm.XmlSerializer.serialize(system).encode())
    storage.immutable_bytes(integrator_path,mm.XmlSerializer.serialize(integrator).encode())

    def realized(context):
        platform=context.getPlatform()
        observed=_platform_properties(platform,context)
        if platform.getName()!=platform_name or any(observed.get(k)!=v for k,v in properties.items()):
            raise ValueError("native context substitutes selected platform properties")
        return dict(platform=platform.getName(),actual_properties=observed)

    return ledger.call("sampling.context",dict(platform=platform_name,properties=properties,
                       system_sha256=storage.file_hash(system_path)[1],
                       integrator_sha256=storage.file_hash(integrator_path)[1]),
                       lambda:mm.Context(system,integrator,mm.Platform.getPlatformByName(platform_name),properties),
                       realization=realized)


def _receiver(mm, ledger, context, directory, name, *, positions=True, velocities=True, forces=False):
    path=directory/(name+".xml")
    def realize(state):
        storage.immutable_bytes(path,mm.XmlSerializer.serialize(state).encode())
        return dict(state_sha256=storage.file_hash(path)[1],actual_steps=context.getStepCount(),
                    actual_time_picosecond=str(storage._clock(state)))
    return ledger.call("sampling.receiver",dict(positions=positions,velocities=velocities,forces=forces),
                       lambda:context.getState(getPositions=positions,getVelocities=velocities,
                                               getForces=forces,getEnergy=True,getParameters=True),
                       realization=realize)


def _gpu_properties(source):
    return dict(Precision=source.platform_precision,DeviceIndex=source.device_index,
                DeterministicForces=source.deterministic_forces,UseCpuPme=source.use_cpu_pme)


def _verify_hardware(source,root,ledger):
    command=["nvidia-smi","--query-gpu=uuid,name,driver_version,pci.bus_id,memory.total,compute_cap","--format=csv,noheader,nounits","--id="+source.device_index]
    result=ledger.call("sampling.hardware-inspection",dict(command=command),lambda:subprocess.run(command,capture_output=True,check=True),realization=lambda result:dict(returncode=result.returncode,stdout=result.stdout.decode(),stderr=result.stderr.decode()))
    storage.immutable_bytes(root/"actual-hardware-query.txt",result.stdout)
    if result.stdout.decode()!=source.hardware.query_stdout_utf8:
        raise ValueError("actual device/driver differs from frozen hardware allocation")


def _materialize(assets, directory):
    """Materialize authentic supplied bytes; never follow producing absolute paths."""
    assets.__post_init__()
    result={}
    for row in assets.files:
        row.__post_init__()
        path=directory/row.evidence.relative_path
        path.parent.mkdir(parents=True,exist_ok=True)
        storage.immutable_bytes(path,row.raw_utf8.encode())
        if storage.file_hash(path)!=(row.evidence.byte_count,row.evidence.sha256):
            raise ValueError("materialized assessed native asset changes original bytes")
        result[Path(row.evidence.relative_path).name]=path
    return result


def _build_system(topology, source, resolution, app, unit, ledger):
    tolerance=next(row[2] for row in c.INTEGRATION if row[0]==resolution)
    request=dict(nonbonded_method="PME",cutoff_nanometer=source.cutoff_nanometer,constraints="HBonds",rigid_water=True,remove_center_of_mass_motion=False,hydrogen_mass_repartitioning=False,ewald_error_tolerance=tolerance)
    return ledger.call("sampling.build-system",request,lambda:topology.createSystem(nonbondedMethod=app.PME,nonbondedCutoff=float(source.cutoff_nanometer)*unit.nanometer,
                                 constraints=app.HBonds,rigidWater=True,removeCMMotion=False,
                                 hydrogenMass=None,ewaldErrorTolerance=float(tolerance)),realization=lambda system:dict(particles=system.getNumParticles(),force_classes=tuple(type(f).__name__ for f in system.getForces())))


def _integrator(mm, unit, ledger, resolution):
    dt,tolerance=next(row[1:] for row in c.INTEGRATION if row[0]==resolution)
    result=ledger.call("sampling.verlet-integrator",dict(step_size_picosecond=dt),lambda:mm.VerletIntegrator(float(dt)*unit.picosecond))
    ledger.call("sampling.apply-constraint-tolerance",dict(tolerance=tolerance),lambda:result.setConstraintTolerance(float(tolerance)),realization=lambda _:dict(actual_tolerance=result.getConstraintTolerance()))
    return result


def _set_configuration(ledger, context, box, positions, source_member):
    ledger.call("sampling.set-box",dict(source_member=source_member,box=str(box)),lambda:context.setPeriodicBoxVectors(*box))
    ledger.call("sampling.set-positions",dict(source_member=source_member,particles=len(positions)),lambda:context.setPositions(positions))


def _arrays(path, **arrays):
    import numpy as np
    storage.immutable_file(path,lambda stream:np.savez_compressed(stream,**arrays))


def _shared_model(source, assets, root, ledger, mm, app, unit, np):
    """One actually attempted shared construction; caller caches its failure."""
    directory=root/("shared-model."+".".join((assets.construct_id,assets.joint_view_id,assets.parameter_view)))
    directory.mkdir()
    context=cpu=integrator=cpu_integrator=system=None
    try:
        paths=_materialize(assets,directory)
        topology=ledger.call("sampling.read-amber-topology",dict(member=str(paths["model.prmtop"].relative_to(root))),lambda:app.AmberPrmtopFile(str(paths["model.prmtop"])))
        coordinates=ledger.call("sampling.read-amber-coordinates",dict(member=str(paths["model.inpcrd"].relative_to(root))),lambda:app.AmberInpcrdFile(str(paths["model.inpcrd"])))
        if coordinates.boxVectors is None:
            raise ValueError("assessed periodic full assembly has no native box")
        system=_build_system(topology,source,"primary",app,unit,ledger)
        atom_count=system.getNumParticles()
        integrator=_integrator(mm,unit,ledger,"primary")
        context=_context(mm,ledger,directory,system,integrator,"CUDA",_gpu_properties(source))
        _set_configuration(ledger,context,coordinates.boxVectors,coordinates.positions,assets.fingerprint())
        ledger.call("sampling.chemical-minimization",dict(tolerance_kj_mol_nm=10,max_iterations=0,meaning="NATIVE_CONVERGENCE_NO_ITERATION_CEILING"),lambda:mm.LocalEnergyMinimizer.minimize(context,10*unit.kilojoule_per_mole/unit.nanometer,0))
        state=_receiver(mm,ledger,context,directory,"minimized",forces=True)
        positions=state.getPositions(asNumpy=True)
        box=state.getPeriodicBoxVectors()
        cuda_force=np.asarray(state.getForces(asNumpy=True).value_in_unit(unit.kilojoule_per_mole/unit.nanometer),dtype=np.float64)
        cuda_energy=float(state.getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole))
        cpu_integrator=_integrator(mm,unit,ledger,"primary")
        cpu=_context(mm,ledger,directory,system,cpu_integrator,"CPU",{"Threads":"1"})
        _set_configuration(ledger,cpu,box,positions,storage.file_hash(directory/"minimized.xml")[1])
        reference=_receiver(mm,ledger,cpu,directory,"cpu-force-reference",forces=True)
        cpu_force=np.asarray(reference.getForces(asNumpy=True).value_in_unit(unit.kilojoule_per_mole/unit.nanometer),dtype=np.float64)
        cpu_positions=np.asarray(reference.getPositions(asNumpy=True).value_in_unit(unit.nanometer),dtype=np.float64)
        gpu_positions=np.asarray(positions.value_in_unit(unit.nanometer),dtype=np.float64)
        cpu_energy=float(reference.getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole))
        force_path=directory/"independent-force-receivers.npz"
        _arrays(force_path,cpu_force_kj_mol_nm=cpu_force,cuda_force_kj_mol_nm=cuda_force,
                cpu_positions_nm=cpu_positions,cuda_positions_nm=gpu_positions,
                cpu_potential_kj_mol=np.array(cpu_energy),cuda_potential_kj_mol=np.array(cuda_energy))
        force_error,energy_error=science.reduce_force_control(dict(cpu_force_kj_mol_nm=cpu_force,cuda_force_kj_mol_nm=cuda_force,cpu_positions_nm=cpu_positions,cuda_positions_nm=gpu_positions,cpu_potential_kj_mol=cpu_energy,cuda_potential_kj_mol=cuda_energy),atom_count)
        return dict(paths=paths,positions=positions,box=box,atom_count=atom_count,
                    force_error=force_error,energy_error=energy_error,
                    force_path=force_path.relative_to(root).as_posix(),error=None)
    finally:
        # Contexts own device state. Do not retain them across selected controls.
        cpu=context=cpu_integrator=integrator=system=None


def _nve_case(source, shared, roster, directory, root, ledger, mm, app, unit):
    """One selected100ps full-model control, retaining every actual subcall."""
    _,_,_,ensemble,resolution=roster
    context=integrator=system=None
    try:
        topology=ledger.call("sampling.read-amber-topology",dict(member=shared["paths"]["model.prmtop"].relative_to(root).as_posix()),lambda:app.AmberPrmtopFile(str(shared["paths"]["model.prmtop"])))
        system=_build_system(topology,source,resolution,app,unit,ledger)
        integrator=_integrator(mm,unit,ledger,resolution)
        context=_context(mm,ledger,directory,system,integrator,"CUDA",_gpu_properties(source))
        _set_configuration(ledger,context,shared["box"],shared["positions"],shared["force_path"])
        _,velocity_seed,_=next(row for row in c.ENSEMBLES if row[0]==ensemble)
        ledger.call("sampling.initialize-thermal-velocities",dict(temperature_kelvin=source.temperature_kelvin,velocity_seed=velocity_seed),lambda:context.setVelocitiesToTemperature(float(source.temperature_kelvin)*unit.kelvin,velocity_seed))
        dt,tolerance=next(row[1:] for row in c.INTEGRATION if row[0]==resolution)
        ledger.call("sampling.apply-position-constraints",dict(tolerance=tolerance),lambda:context.applyConstraints(float(tolerance)))
        ledger.call("sampling.apply-velocity-constraints",dict(tolerance=tolerance),lambda:context.applyVelocityConstraints(float(tolerance)))
        initial=_receiver(mm,ledger,context,directory,"initial-full-state")
        def receiver_values(state):
            return dict(total_energy_kj_mol=float((state.getPotentialEnergy()+state.getKineticEnergy()).value_in_unit(unit.kilojoule_per_mole)),time_picosecond=str(storage._clock(state)),steps=int(context.getStepCount()))
        raw=[receiver_values(initial)]
        interval_steps=int(Decimal(10)/dt)
        started=time.perf_counter()
        for index in range(1,11):
            ledger.call("sampling.nve-integration",dict(steps=interval_steps,step_size_picosecond=dt,physical_time_picosecond=10),lambda:integrator.step(interval_steps))
            state=_receiver(mm,ledger,context,directory,"nve-state-"+str(index).zfill(2),positions=False,velocities=False)
            raw.append(receiver_values(state))
        wall=Decimal(str(time.perf_counter()-started))
        control=dict(atom_count=system.getNumParticles(),step_size_picosecond=str(dt),receivers=raw,integration_wall_seconds=str(wall))
        path=directory/"numerical-control.json"
        _json(path,control)
        excursion,steps,clock=science.reduce_nve_control(control,shared["atom_count"],dt)
        return excursion,steps,clock,wall,path.relative_to(root).as_posix()
    finally:
        context=integrator=system=None


def _native_calibration(source, preparation, assets, root):
    """Exact96 controls. Shared24 constructions have no automatic replay."""
    science.validate_source(source,preparation,assets)
    from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.native import CallLedger,verify_engine
    verify_engine(source.preparation_selection)
    import numpy as np
    import openmm as mm
    from openmm import app,unit
    ledger=CallLedger(root)
    _verify_hardware(source,root,ledger)
    cases=[]
    by_assets={(row.construct_id,row.joint_view_id,row.parameter_view):row for row in assets}
    prior_dispositions=dict((row[0],row[1]) for row in preparation.model_dispositions)
    shared={}
    for roster in c.trajectory_roster():
        key=roster[:3]
        case_id="calibration."+".".join(roster)
        directory=root/case_id
        directory.mkdir()
        prior_ids={row.call_id for row in ledger.calls}
        ledger.model_id=case_id
        force_error=energy_error=excursion=integration_wall=None
        force_path=control_path=None
        atom_count=steps=0
        actual_time=Decimal(0)
        error=None
        inherited_calls=()
        verdict=prior_dispositions["model."+".".join(key)]
        entry="UNENTERED_PREPARATION_"+("REFUSED" if verdict is A.REFUSED else "UNEVALUABLE")
        if verdict is A.SATISFIED:
            verdict=A.UNEVALUABLE
            entry="ENTERED"
            if key not in shared:
                shared_start={row.call_id for row in ledger.calls}
                try:
                    shared[key]=_shared_model(source,by_assets[key],root,ledger,mm,app,unit,np)
                except Exception:
                    shared[key]=dict(error=traceback.format_exc())
                    _json(directory/"shared-technical-failure.json",dict(error=shared[key]["error"]))
                shared[key]["call_ids"]=tuple(row.call_id for row in ledger.calls if row.call_id not in shared_start)
            else:
                inherited_calls=shared[key]["call_ids"]
                if shared[key]["error"]:
                    entry="UNENTERED_SHARED_CONTROL_FAILURE"
            if shared[key]["error"]:
                error=shared[key]["error"]
            else:
                data=shared[key]
                atom_count=data["atom_count"]
                force_error,energy_error,force_path=data["force_error"],data["energy_error"],data["force_path"]
                try:
                    excursion,steps,actual_time,integration_wall,control_path=_nve_case(source,data,roster,directory,root,ledger,mm,app,unit)
                    verdict=A.SATISFIED
                except Exception:
                    error=traceback.format_exc()
                    _json(directory/"technical-failure.json",dict(error=error))
        actual_calls=tuple(row for row in ledger.calls if row.call_id not in prior_ids or row.call_id in inherited_calls)
        members=tuple(storage.member(path,root,"CALIBRATION_NATIVE_MEMBER") for path in sorted(directory.rglob("*")) if path.is_file())
        cases.append(c.CalibrationCase(case_id,roster,verdict,entry,atom_count,force_error,energy_error,actual_time,excursion,steps,integration_wall,members,actual_calls,error,force_path,control_path))
    product=c.CalibrationProduct("product."+c.NAMESPACE+".calibration",c.identity(source),source.preparation_assessment,tuple(cases),storage.complete_census(root),tuple(ledger.calls))
    storage.immutable_bytes(root/"calibration.json",product.canonical_bytes())
    return product


def calibrate(source, preparation, assets, *, workdir):
    """Actual registered caller only; an existing selected attempt is refused."""
    science.validate_source(source,preparation,assets)
    root=Path(workdir)
    if str(root)!=source.native_workdir:
        raise ValueError("calibration substitutes selected authored native workdir")
    root.mkdir(parents=True,exist_ok=False)
    temporary=root/"temporary";temporary.mkdir()
    for name,record in (("source",source),("preparation",preparation)):
        storage.immutable_bytes(root/(name+".json"),record.canonical_bytes())
    for index,record in enumerate(assets):
        storage.immutable_bytes(root/("assets-"+str(index).zfill(2)+".json"),record.canonical_bytes())
    environment=dict(os.environ,PYTHONPATH=str(Path(__file__).resolve().parents[4]),
                     PYTHONDONTWRITEBYTECODE="1",TMPDIR=str(temporary),TMP=str(temporary),TEMP=str(temporary),OPENMM_CPU_THREADS="1")
    for name in ("OPENBLAS_NUM_THREADS","OMP_NUM_THREADS","MKL_NUM_THREADS","NUMEXPR_NUM_THREADS","VECLIB_MAXIMUM_THREADS"):
        environment[name]="1"
    with (root/"isolated-worker.stdout.log").open("wb") as out,(root/"isolated-worker.stderr.log").open("wb") as err:
        result=subprocess.run([p.ENGINE_ROOT+"/.venv/bin/python","-m",__name__,"--selected-calibration",str(root)],
                               env=environment,cwd=root,stdout=out,stderr=err,check=False)
    if result.returncode!=0:
        raise RuntimeError("actual isolated calibration failed; complete bytes retained at "+str(root))
    return decode_canonical_bytes((root/"calibration.json").read_bytes(),c.CalibrationProduct,maximum_bytes=None)


def _main():
    if len(sys.argv)!=3 or sys.argv[1]!="--selected-calibration":
        raise SystemExit("explicit registered selected native calibration required")
    root=Path(sys.argv[2])
    source=decode_canonical_bytes((root/"source.json").read_bytes(),c.SamplingSource,maximum_bytes=None)
    preparation=decode_canonical_bytes((root/"preparation.json").read_bytes(),p.PreparationAssessment,maximum_bytes=None)
    assets=tuple(decode_canonical_bytes((root/("assets-"+str(index).zfill(2)+".json")).read_bytes(),p.ModelAssets,maximum_bytes=None) for index in range(24))
    if str(root)!=source.native_workdir:
        raise ValueError("isolated calibration root changes source selection")
    _native_calibration(source,preparation,assets,root)


if __name__=="__main__":
    _main()
