"""Local construction restrictions preserve independent relaxation and force criteria."""
import numpy as np
import pytest

from empirical_lawhood.domains.rubisco.rubisco_response.constructed_geometry_domain import ConstructedGeometryDomain, GeometryDomainViolation
from empirical_lawhood.domains.rubisco.rubisco_response.geometry_domain_minimizer import minimize_geometry


def test_one_near_boundary_atom_does_not_shrink_unrelated_motion():
    xyz=np.array([[0,0,0],[.1,0,0],[0,.1,0],[0,0,.005],[2,0,0]],dtype=float)
    domain=ConstructedGeometryDomain(5,((0,1,2,3),),())
    direction=np.array([[0,0,-.01],[.1,0,0]])
    adjusted,info=domain.restrict_step(xyz,(3,4),direction)
    assert np.array_equal(adjusted[1],direction[1])
    assert 0<np.linalg.norm(adjusted[0])<np.linalg.norm(direction[0])
    complete=xyz.copy();complete[[3,4]]+=adjusted
    domain.evaluate(complete)
    assert np.array_equal(complete[:3],xyz[:3])
    assert info['locally_restricted_atoms']==1 and info['minimum_local_step_scale']==.25
    assert np.sum(adjusted*np.array([[0,0,1],[-1,0,0]]))<0


@pytest.mark.numerical(oracle="Independent positive quadratic minimum at the prescribed interior target with exactly zero construction barrier")
def test_local_filter_and_no_count_ceiling_reach_the_same_original_potential_minimum():
    xyz=np.array([[0,0,0],[.1,0,0],[0,.1,0],[0,0,.005],[2,0,0]],dtype=float)
    target=np.array([[0,0,.15],[2.5,.3,-.2]])
    domain=ConstructedGeometryDomain(5,((0,1,2,3),),())
    moving=(3,4);native_calls=[]
    def complete(value):
        result=xyz.copy();result[list(moving)]=value.reshape((-1,3));return result
    def objective(value):
        points=complete(value);barrier,gradient,_=domain.evaluate(points)
        delta=points[list(moving)]-target;native_calls.append(points)
        return 5000*np.sum(delta**2)+barrier,(10000*delta+gradient[list(moving)]).reshape(-1)
    def proposal(value,direction):
        selected,info=domain.restrict_step(complete(value),moving,direction.reshape((-1,3)))
        return selected.reshape(-1),info
    result=minimize_geometry(objective,xyz[list(moving)].reshape(-1),violation_type=GeometryDomainViolation,
        maximum_gradient=1e-5,proposal_filter=proposal)
    assert result.success,result.message
    assert np.max(np.abs(result.x.reshape((-1,3))-target))<1e-8
    assert result.settings['maximum_iterations'] is result.settings['maximum_evaluations'] is None
    assert result.nfev==len(native_calls)
    assert all(np.array_equal(points[:3],xyz[:3]) for points in native_calls)
    assert domain.evaluate(complete(result.x))[0]==0


def test_selected_work_limits_do_not_claim_force_convergence():
    result=minimize_geometry(lambda x:(float(np.sum(x*x)),2*x),np.array([10.,0,0]),
        violation_type=GeometryDomainViolation,maximum_iterations=1)
    assert not result.success and result.nit==1
    assert result.settings['maximum_iterations']==1 and result.message=='maximum-geometry-iterations'
