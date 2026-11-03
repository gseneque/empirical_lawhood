# SPDX-License-Identifier: MPL-2.0
"""Source-free independent FD, trace-word, phase-space and geometry controls."""

from dataclasses import replace
from decimal import Decimal as D
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pytest
from empirical_lawhood.adapters.methods.matrix_factor_response import independent as v1, independent_v2 as v2
from empirical_lawhood.adapters.methods.matrix_factor_response.independent_v2_records import MatrixResponseIndependentMethodV2
from empirical_lawhood.kernel.provenance import ObjectIdentity
from tests.test_matrix_factor_response import mechanical_case


def method():
    raw = Path(v2.__file__).read_bytes()
    implementation = ObjectIdentity("implementation.fixture.independent-v2",
        "empirical-lawhood/matrix-factor-response/independent-implementation", "2.0.0", sha256(raw).hexdigest())
    return MatrixResponseIndependentMethodV2("method.fixture.independent-v2", implementation)



def parameter_case(mass, cross, alpha, eta, bath, dt):
    design, initial, _, _ = mechanical_case()
    d = replace(design,member=replace(design.member,mass_x=D(mass),mass_y=D(mass),cross_coupling_gamma=D(cross)),
        alpha_x=D(alpha[0]),alpha_y=D(alpha[1]),view=replace(design.view,timestep=D(dt),friction_gamma=D(eta),bath_temperature=D(bath)),
        rule=replace(design.rule,primary_dt=D(dt)))
    return d, initial



@pytest.mark.parametrize("params", (
    (".5","1",(".6666666666666667","7.333333333333333"),"1","1",".001"),
    (".2",".3",("0",".2"),".01",".1",".0005"),
    (".7","2",(".5","3.4"),"2","2",".002"),
))
def test_all96_gradient_against_literal_finite_difference_and_parameter_history(params):
    d, initial = parameter_case(*params)
    from empirical_lawhood.adapters.methods.matrix_parameter_history.independent import potential_gradient as other
    x = initial["positions"][0]
    measured = v2.potential_gradient(x,d.member,(d.alpha_x,d.alpha_y))
    reference = v2.potential_gradient_fd(x,d)
    np.testing.assert_allclose(measured,reference,rtol=1e-7,atol=1e-7)
    np.testing.assert_allclose(measured,other(x,d.member,(d.alpha_x,d.alpha_y)),rtol=1e-13,atol=1e-13)
    # A missing potential coefficient must be detectable by the independent FD.
    wrong = v2.potential_gradient(x,replace(d.member,cross_coupling_gamma=D("3")),(d.alpha_x,d.alpha_y))
    assert np.linalg.norm(wrong-reference) > 1e-5



@pytest.mark.parametrize("sign", (-1,0,1))
@pytest.mark.parametrize("dt", (".001",".0005"))
def test_parameter_force_sign_clock_noise_full_phase_reference_matches_fd(dt, sign):
    d, initial = parameter_case(".7","1.2",(".5","3.4"),".7","1.3",dt)
    force = v2.native_basis()[17]+v2.native_basis()[67]
    noise = v1.noise_panel(SimpleNamespace(seed=1805),2)
    past = {k:v.copy() for k,v in initial.items()}
    actual = v2.reference_branch(d,past,force,.03*sign,1,noise)
    expected = v1.reference_branch(d,past,force,.03*sign,1,noise)
    for name in ("positions","momenta"):
        np.testing.assert_allclose(actual[name],expected[name],rtol=1e-8,atol=1e-8)
    changed = v2.reference_branch(d,past,force,.03*sign,1,noise*1.01)
    assert np.linalg.norm(changed["momenta"]-actual["momenta"]) > 0



def test_basis_is_constant_complete_and_irreversibly_read_only():
    a, b = v2.native_basis(),v2.native_basis()
    assert a is b and a.shape == (96,2,3,4,4)
    np.testing.assert_array_equal(a,v1.native_basis())
    with pytest.raises(ValueError):
        a.setflags(write=True)
    np.testing.assert_allclose(np.einsum("ksjab,lsjab->kl",a.conj(),a).real,np.eye(96),atol=1e-15)



def test_parameter_reference_refuses_unrepresentable_ou_and_foreign_array_domain():
    d, initial = parameter_case(".5","1",(".5","3"),"1e-18","1",".001")
    with pytest.raises(ValueError,match="representable"):
        v2.reference_branch(d,initial,v2.native_basis()[0],.01,1,np.zeros((1,2,3,4,4),dtype="<c16"))
    with pytest.raises(ValueError,match="geometry"):
        v2.potential_gradient(initial["positions"][0].astype("<c8"),d.member,(d.alpha_x,d.alpha_y))
