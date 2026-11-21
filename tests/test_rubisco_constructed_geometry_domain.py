# SPDX-License-Identifier: MPL-2.0
"""Independent derivatives, forbidden trials and final original-force controls."""

from decimal import Decimal
import json
import math

import numpy as np
import pytest

from empirical_lawhood.domains.rubisco.rubisco_response.constructed_geometry_domain import ConstructedGeometryDomain, GeometryDomainViolation, domain_from_heavy_source
from empirical_lawhood.domains.rubisco.rubisco_response.geometry_domain_minimizer import minimize_geometry
from empirical_lawhood.domains.rubisco.rubisco_response.gp_geometry_repair_assessment import library_minimizer_findings


def active_coordinates():
    return np.array([[0,0,0],[.1,0,0],[0,.1,0],[0,0,.05],
        [1,.1,0],[1,0,0],[1.1,0,0],
        [1.1,.1*math.cos(math.radians(155)),.1*math.sin(math.radians(155))]])


@pytest.mark.numerical(oracle="Central differences independently check every barrier-gradient component; translation and rotation preserve scalar energy, zero net force and torque.")
def test_barrier_derivatives_rigid_invariance_and_exact_zero_interior():
    domain=ConstructedGeometryDomain(8,((0,1,2,3),),((4,5,6,7),))
    xyz=active_coordinates()
    energy,gradient,diagnostic=domain.evaluate(xyz)
    assert diagnostic['active_stereocentres']==diagnostic['active_peptides']==1
    for i in range(8):
        for j in range(3):
            plus,minus=xyz.copy(),xyz.copy();plus[i,j]+=1e-7;minus[i,j]-=1e-7
            numerical=(domain.evaluate(plus)[0]-domain.evaluate(minus)[0])/2e-7
            assert abs(numerical-gradient[i,j])<1e-5
    assert np.max(np.abs(gradient.sum(axis=0)))<1e-10
    assert np.max(np.abs(np.cross(xyz,gradient).sum(axis=0)))<1e-10
    rotation=np.array([[0,-1,0],[1,0,0],[0,0,1]])
    moved=xyz@rotation.T+[.7,-.3,.4]
    changed_energy,changed_gradient,_=domain.evaluate(moved)
    assert abs(energy-changed_energy)<1e-11
    assert np.max(np.abs(changed_gradient-gradient@rotation.T))<1e-9
    xyz[3,2]=.15
    xyz[7]=[1.1,.1*math.cos(math.radians(175)),.1*math.sin(math.radians(175))]
    energy,gradient,_=domain.evaluate(xyz)
    assert energy==0 and np.count_nonzero(gradient)==0


@pytest.mark.parametrize('change',('inverted','planar','cis','degenerate'))
def test_domain_refuses_nonphysical_geometry(change):
    domain=ConstructedGeometryDomain(8,((0,1,2,3),),((4,5,6,7),))
    xyz=active_coordinates()
    if change=='inverted':xyz[3,2]=-.05
    elif change=='planar':xyz[3,2]=0
    elif change=='cis':xyz[7]=[1.1,.1,0]
    else:xyz[7]=[1.2,0,0]
    with pytest.raises(GeometryDomainViolation):domain.evaluate(xyz)


@pytest.mark.parametrize('indices',(((0,1,2,2),),((0,1,2,4),),((0,1,2,True),),((0,1,2,3),(0,1,2,3))))
def test_domain_refuses_ambiguous_or_missing_atoms(indices):
    with pytest.raises(ValueError):ConstructedGeometryDomain(4,indices,())


@pytest.mark.numerical(oracle="An independently specified quadratic has its physical minimum at z=-0.1, outside the positive-volume domain; a barrier optimum must retain nonzero original force.")
def test_invalid_optimizer_trials_never_reach_original_objective_and_barrier_optimum_is_not_physical():
    domain=ConstructedGeometryDomain(4,((0,1,2,3),),())
    xyz=active_coordinates()[:4];xyz[3,2]=.005
    calls=0
    def objective(value):
        nonlocal calls
        full=xyz.copy();full[3]=value
        barrier,gradient,_=domain.evaluate(full)
        calls+=1
        delta=value-[0,0,-.1]
        return 1e5*np.sum(delta**2)+barrier,2e5*delta+gradient[3]
    result=minimize_geometry(objective,xyz[3],violation_type=GeometryDomainViolation,
        maximum_gradient=1e-3,maximum_iterations=1000)
    assert result.success,result.message
    assert result.rejected_domain_trials>0
    assert calls==result.nfev
    assert result.x[2]>0
    final=xyz.copy();final[3]=result.x
    assert domain.evaluate(final)[0]>0
    assert np.max(np.abs(2e5*(result.x-[0,0,-.1])))>1


@pytest.mark.numerical(oracle="A constant reported objective with fixed gradient (2,0,0) cannot meet a 1e-6 gradient threshold, regardless of energy stagnation.")
def test_minimizer_does_not_call_energy_stagnation_force_convergence():
    result=minimize_geometry(lambda x:(1.,np.array([2.,0,0])),np.array([.1,0,0]),
        violation_type=GeometryDomainViolation,maximum_gradient=1e-6,maximum_iterations=10)
    assert not result.success
    assert np.max(np.abs(result.jac))==2


def exposed_source():
    coordinates=np.array([[0,0,0],[.1,0,0],[0,.1,0],[0,0,.15],
        [.1,.2,0],[.1,.1,0],[.2,.2,0],[.1,.2,.15]])
    names=('CA','N','C','CB')*2
    text='';joined=[];atoms={}
    for i,(name,xyz) in enumerate(zip(names,coordinates,strict=True)):
        pos=1+i//4;key=('A',pos,name);element='N' if name=='N' else 'C'
        x,y,z=xyz*10
        text+=f'ATOM  {i+1:5d} {(" "+name):4s} ALA A{pos:4d}    {x:8.3f}{y:8.3f}{z:8.3f}  1.00  0.00          {element:>2s}  \n'
        joined.append((key,i));atoms[key]=dict(component='ALA')
    permitted={('A',1,'CB'),('A',2,'CA'),('A',2,'CB')}
    domain,labels=domain_from_heavy_source(text+'END\n',tuple(joined),permitted,8)
    assert len(domain.stereocentres)==2 and len(domain.peptides)==1
    optimizer=dict(numerical_method='CONSTRUCTION_DOMAIN_LBFGS_V1',construction_domain=domain.settings(),
        construction_domain_labels=labels,final_construction_barrier_energy_kj_mol=0.,
        maximum_final_construction_barrier_gradient_kj_mol_nm=0.,maximum_final_augmented_mobile_gradient_kj_mol_nm=.1)
    return json.loads(json.dumps(optimizer)),atoms,permitted,dict(joined),coordinates


def test_explicit_custom_domain_retains_complete_stereocentre_and_peptide_census():
    exposed_source()


def test_default_repair_refuses_custom_or_absent_minimizer_contract():
    for optimizer in ({}, exposed_source()[0]):
        with pytest.raises(ValueError, match="complete Amber/OpenMM"):
            library_minimizer_findings(optimizer, np.zeros((8, 3)), Decimal(1))


def library_report():
    return dict(numerical_method="OPENMM_LOCAL_ENERGY_MINIMIZER_COMPLETE_AMBER_V1",
        all_original_force_groups=True, projected_pair_kernel=False, platform="CPU", threads=1,
        platform_properties={"Threads": "1", "DeterministicForces": "true"},
        iteration_limit_is_convergence=False, requested_openmm_rms_tolerance_kj_mol_nm=1/math.sqrt(24))


@pytest.mark.parametrize("change", ("partial-force", "projected", "iteration-success", "wrong-platform", "rms-too-loose", "boolean"))
def test_library_reader_refuses_a_stopping_rule_that_cannot_prove_the_selected_force_bound(change):
    report = library_report()
    if change == "partial-force": report["all_original_force_groups"] = False
    elif change == "projected": report["projected_pair_kernel"] = True
    elif change == "iteration-success": report["iteration_limit_is_convergence"] = True
    elif change == "wrong-platform": report["platform"] = "CUDA"
    elif change == "rms-too-loose": report["requested_openmm_rms_tolerance_kj_mol_nm"] = 1
    else: report["requested_openmm_rms_tolerance_kj_mol_nm"] = True
    with pytest.raises(ValueError):
        library_minimizer_findings(report, np.zeros((8, 3)), Decimal(1))


def test_library_reader_accepts_the_conservative_complete_force_rule():
    assert library_minimizer_findings(library_report(), np.zeros((8, 3)), Decimal(1)) == ()
