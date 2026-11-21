# SPDX-License-Identifier: MPL-2.0
"""Large dynamic-range and false-stagnation controls for initial descent."""

import numpy as np
import pytest

from empirical_lawhood.domains.rubisco.rubisco_response.clash_descent import descend_clashes


def test_independent_severe_contacts_both_relax_without_changing_the_potential():
    fixed=np.array([[10.,8.,1.],[20.,8.,1.]])
    initial=fixed+np.array([[.0051,0,0],[.0175,0,0]])
    seen=[]
    def objective(values):
        delta=values.reshape((-1,3))-fixed
        r=np.linalg.norm(delta,axis=1)
        energy=np.sum((.32/r)**12+500*(r-.4)**2)
        gradient=(-12*(.32/r)**12/r+1000*(r-.4))[:,None]*delta/r[:,None]
        seen.append(values.copy())
        return energy,gradient.reshape(-1)
    final,result=descend_clashes(objective,initial.reshape(-1))
    assert result["success"] and result["iterations"]<100
    assert result["maximum_gradient_kj_mol_nm"]<=10000
    assert result["energy_kj_mol"]<result["initial_energy_kj_mol"]/1e12
    # The smaller clash cannot be frozen out by the much larger other force.
    assert np.all(np.linalg.norm(seen[1].reshape((-1,3))-initial,axis=1)>.0099)
    assert np.all(np.linalg.norm(final.reshape((-1,3))-fixed,axis=1)>.17)
    assert np.array_equal(initial,fixed+np.array([[.0051,0,0],[.0175,0,0]]))


def test_flat_energy_cannot_masquerade_as_initial_force_convergence():
    def quantized(values):return 1e20,np.array([1e18,0.,0.])
    initial=np.array([10.,8.,1.])
    final,result=descend_clashes(quantized,initial)
    assert not result["success"] and result["iterations"]==0
    assert result["reason"]=="initial-descent-coordinate-resolution"
    assert np.array_equal(final,initial)


def test_numerical_iteration_limit_preserves_unconverged_endpoint():
    def linear(values):return 1e5*float(values[0]),np.array([1e5,0.,0.])
    _,result=descend_clashes(linear,np.array([10.,8.,1.]),maximum_iterations=2)
    assert not result["success"] and result["iterations"]==2
    assert result["reason"]=="maximum-initial-descent-iterations"


def test_earlier_handoff_keeps_the_same_initial_path_and_requires_its_force_target():
    paths=[]
    def objective(values):
        radius=values[0]
        energy=(.32/radius)**12+500*(radius-.4)**2
        gradient=np.array([-12*(.32/radius)**12/radius+1000*(radius-.4),0.,0.])
        paths.append(values.copy())
        return energy,gradient
    start=np.array([.0051,0.,0.])
    early,first=descend_clashes(objective,start,maximum_gradient=1e6,gradient_scale=1e4)
    prefix=[p.copy() for p in paths]
    paths.clear()
    _,later=descend_clashes(objective,start,maximum_gradient=1e4,gradient_scale=1e4)
    assert first['success'] and first['maximum_gradient_kj_mol_nm']<=1e6
    assert first['maximum_gradient_kj_mol_nm']>1e4 and later['success']
    assert first['function_evaluations']<later['function_evaluations']
    assert np.array_equal(prefix,np.asarray(paths[:len(prefix)]))
    assert np.array_equal(early,prefix[-1])


@pytest.mark.parametrize("bad",(np.ones(2),np.array([np.inf,0.,0.])))
def test_incomplete_or_nonfinite_native_gradient_refuses(bad):
    with pytest.raises(ValueError,match="incomplete finite objective"):
        descend_clashes(lambda x:(1.,bad),np.ones(3))
