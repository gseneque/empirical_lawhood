# SPDX-License-Identifier: MPL-2.0
"""Pure complete-census source admission and independent numerical assessment."""

from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path

from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import contracts as p
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A

from . import contracts as c, storage

FORCE_TARGET = Decimal("0.0001")
ENERGY_TARGET_PER_ATOM = Decimal("0.0001")
NVE_TARGET_PER_ATOM = Decimal("0.001")
REFINEMENT_ROUNDOFF_FLOOR_PER_ATOM = Decimal("0.00001")


def hardware_from_stdout(raw):
    text=raw.decode("utf8")
    fields=tuple(value.strip() for value in text.strip().split(","))
    if len(fields)!=6:
        raise ValueError("selected hardware query omits exact single-device fields")
    return c.HardwareSelection("input."+c.NAMESPACE+".hardware",text,sha256(raw).hexdigest(),*fields[:4],int(fields[4]),fields[5])


def source_from_preparation(selection, assessment, assets, *, hardware, native_workdir):
    source = c.SamplingSource("input."+c.NAMESPACE+".calibration",selection,
                              p.identity(assessment),tuple(p.identity(row) for row in assets),
                              hardware,native_workdir)
    validate_source(source,assessment,assets)
    return source


def validate_source(source, assessment, assets):
    source.__post_init__()
    assessment.__post_init__()
    if p.identity(assessment)!=source.preparation_assessment or assessment.source!=p.identity(source.preparation_selection):
        raise ValueError("sampling replaces actual assessed preparation/source")
    if tuple(p.identity(row) for row in assets)!=source.model_assets:
        raise ValueError("sampling substitutes authentic prepared file assets")
    if tuple((row.construct_id,row.joint_view_id,row.parameter_view) for row in assets)!=p.model_roster():
        raise ValueError("sampling omits/reorders complete24 materials")
    if any(row.source!=p.identity(source.preparation_selection) for row in assets):
        raise ValueError("sampling relabels original model source lineage")
    if tuple(row[0] for row in assessment.model_dispositions)!=tuple("model."+".".join(row) for row in p.model_roster()):
        raise ValueError("sampling changes actual model assessment census")
    return source


def reduce_force_control(data, atom_count):
    """Independent full-array reduction, including actual identical geometry."""
    import numpy as np
    cpu=np.asarray(data["cpu_force_kj_mol_nm"],dtype=np.float64)
    gpu=np.asarray(data["cuda_force_kj_mol_nm"],dtype=np.float64)
    left=np.asarray(data["cpu_positions_nm"],dtype=np.float64)
    right=np.asarray(data["cuda_positions_nm"],dtype=np.float64)
    energies=np.asarray([data["cpu_potential_kj_mol"],data["cuda_potential_kj_mol"]],dtype=np.float64)
    if atom_count<=0 or any(row.shape!=(atom_count,3) for row in (cpu,gpu,left,right)) or not all(np.isfinite(row).all() for row in (cpu,gpu,left,right,energies)):
        raise ValueError("independent full-system force receiver omits/nonfinite atoms")
    if not np.allclose(left,right,rtol=0,atol=1e-12):
        raise ValueError("independent force engines evaluate different actual coordinates")
    norm=float(np.linalg.norm(cpu))
    if norm==0:
        raise ValueError("independent relative-force denominator is zero")
    return Decimal(str(float(np.linalg.norm(gpu-cpu))/norm)),Decimal(str(abs(float(energies[0]-energies[1]))/atom_count))


def reduce_nve_control(data, atom_count, dt):
    """Recompute numerical energy drift and all actual steps/global clocks."""
    receivers=data["receivers"]
    if data["atom_count"]!=atom_count or atom_count<=0 or Decimal(data["step_size_picosecond"])!=dt or len(receivers)!=11:
        raise ValueError("native NVE control substitutes the full frozen physical window")
    energies=[Decimal(str(row["total_energy_kj_mol"])) for row in receivers]
    if any(not value.is_finite() for value in energies):
        raise ValueError("native NVE energy receiver is nonfinite")
    for index,row in enumerate(receivers):
        time=Decimal(row["time_picosecond"])
        if not time.is_finite() or abs(time-Decimal(index*10))>Decimal("0.0000001") or row["steps"]!=int(Decimal(index*10)/dt):
            raise ValueError("native NVE receiver omits or changes actual clock/step progress")
    excursion=max(abs(value-energies[0]) for value in energies)/atom_count
    return excursion,receivers[-1]["steps"],Decimal(receivers[-1]["time_picosecond"])


def assess_calibration(source, preparation, assets, result, *, current_raw_root, current_raw_prefix=""):
    validate_source(source,preparation,assets)
    result.__post_init__()
    if result.source!=c.identity(source) or result.preparation_assessment!=source.preparation_assessment:
        raise ValueError("calibration replaces exact selected native result/source")
    # The caller selects its current authenticated dependency/portable view.
    # This reader never consults the original absolute source.native_workdir.
    storage.verify_view(result.complete_members,current_raw_root,prefix=current_raw_prefix)
    rows={r.relative_path:r for r in result.complete_members}
    root=Path(current_raw_root)/current_raw_prefix
    cases=[]
    for case in result.cases:
        reasons=[]
        verdict=case.disposition
        if verdict is A.SATISFIED:
            if case.force_control_relative_path not in rows or case.nve_control_relative_path not in rows:
                verdict=A.UNEVALUABLE;reasons.append("ACTUAL_FORCE_ENERGY_CONTROL_MISSING")
            else:
                import numpy as np
                with np.load(root/case.force_control_relative_path,allow_pickle=False) as data:
                    force_error,energy_error=reduce_force_control(data,case.atom_count)
                dt=next(row[1] for row in c.INTEGRATION if row[0]==case.roster[-1])
                excursion,steps,clock=reduce_nve_control(json.loads((root/case.nve_control_relative_path).read_text()),case.atom_count,dt)
                if (force_error,energy_error,excursion,steps,clock)!=(case.force_rms_relative_error,case.energy_error_kj_mol_per_atom,case.nve_max_energy_excursion_kj_mol_per_atom,case.native_steps,case.nve_time_picosecond):
                    raise ValueError("reported numerical result differs from independent raw receiver reduction")
                if force_error>FORCE_TARGET or energy_error>ENERGY_TARGET_PER_ATOM or excursion>NVE_TARGET_PER_ATOM:
                    verdict=A.REFUSED;reasons.append("FROZEN_NUMERICAL_PRECISION_TARGET_FAILED")
        cases.append((case.case_id,verdict,tuple(reasons)))
    paired=[]
    for index in range(0,len(result.cases),2):
        primary,refined=result.cases[index:index+2]
        if primary.roster[:-1]!=refined.roster[:-1] or (primary.roster[-1],refined.roster[-1])!=("primary","refined"):
            raise ValueError("numerical refinement changes controlled source/ensemble")
        left=primary.nve_max_energy_excursion_kj_mol_per_atom
        right=refined.nve_max_energy_excursion_kj_mol_per_atom
        verdict=A.UNEVALUABLE if left is None or right is None else A.SATISFIED if right<=left+REFINEMENT_ROUNDOFF_FLOOR_PER_ATOM else A.REFUSED
        paired.append((primary.case_id.rsplit(".",1)[0],verdict,left,right))
    outcomes=[row[1] for row in cases]+[row[1] for row in paired]
    overall=A.UNEVALUABLE if A.UNEVALUABLE in outcomes else A.REFUSED if A.REFUSED in outcomes else A.SATISFIED
    valid=[row for row in result.cases if row.disposition is A.SATISFIED]
    complete=len(valid)==96
    coordinates=sum(row.atom_count*3*8*250 for row in valid) if complete else None
    checkpoints=sum(row.atom_count*3*8*2*25 for row in valid) if complete else None
    timings=[row.measured_integration_wall_seconds for row in valid]
    # 100ps NVE controls forecast250ns integration only. Construction, thermostat,
    # barostat, analysis, I/O, and actual compression remain separate unknowns.
    forecast=sum(timings,Decimal(0))*Decimal(2500) if complete and all(row is not None for row in timings) else None
    return c.CalibrationAssessment("product."+c.NAMESPACE+".calibration-assessment",
                                   c.identity(source),c.identity(result),source.preparation_assessment,
                                   tuple(cases),tuple(paired),overall,coordinates,checkpoints,forecast)
