# SPDX-License-Identifier: MPL-2.0
"""Numerical geometry controls; actual full-assembly custody is assessed separately."""

from decimal import Decimal as D

import numpy as np
import pytest

from empirical_lawhood.domains.rubisco.rubisco_response.gp_active_scaffold import ScaffoldAtom, proper_rigid_fit, sidechain_transplant
from empirical_lawhood.science.records.decoding import decode_canonical_bytes


@pytest.mark.numerical(oracle="A prescribed proper 90-degree rotation and translation of a noncoplanar tetrahedron independently define the unique zero-residual rigid fit.")
def test_rigid_fit_recovers_known_rotation_without_changing_chirality_or_lengths():
    points = np.array(((0.,0.,0.),(1.,0.,0.),(0.,2.,0.),(0.,0.,3.)))
    rotation = np.array(((0.,1.,0.),(-1.,0.,0.),(0.,0.,1.)))
    target = points@rotation+np.array((2.,-3.,4.))
    fitted,offset,error = proper_rigid_fit(points,target)
    assert error<1e-12 and np.linalg.det(fitted)==pytest.approx(1)
    np.testing.assert_allclose(fitted,rotation,atol=1e-12)
    np.testing.assert_allclose(points@fitted+offset,target,atol=1e-12)


@pytest.mark.numerical(oracle="A reflected noncoplanar tetrahedron has opposite signed volume; any orientation-preserving fit must have nonzero residual and determinant+1.")
def test_mirrored_target_cannot_be_fitted_with_a_reflection():
    points = np.array(((0.,0.,0.),(1.,0.,0.),(0.,2.,0.),(0.,0.,3.)))
    mirrored = points*np.array((-1.,1.,1.))
    rotation,offset,error = proper_rigid_fit(points,mirrored)
    assert np.linalg.det(rotation)==pytest.approx(1) and error>0.4
    fitted = points@rotation+offset
    assert np.linalg.det(fitted[1:]-fitted[0])*np.linalg.det(points[1:]-points[0])>0


@pytest.mark.parametrize("points", (
    ((0,0,0),(1,0,0),(2,0,0)),
    ((0,0,0),(0,0,0),(0,0,0)),
    ((0,0,0),(1,1,0),(0,0,float("nan"))),
    ((0,0),(1,0),(2,0)),
))
def test_degenerate_or_nonfinite_fit_is_refused(points):
    with pytest.raises(ValueError):
        proper_rigid_fit(points,points)


@pytest.mark.numerical(oracle="An independently prescribed quarter-turn frame maps CG to(2,1,5), SD to(1,1,5), and leaves CB-CG length sqrt(2) exactly anchored.")
def test_side_chain_frame_preserves_lengths_with_exact_cb_anchor():
    donor = {"N":(0.,1.,0.),"CA":(0.,0.,0.),"CB":(1.,0.,0.),"CG":(1.,1.,1.),"SD":(2.,1.,1.)}
    target = {"N":(3.,1.,4.),"CA":(3.,2.,4.),"CB":(2.,2.,4.)}
    result = sidechain_transplant(donor,target,("CG","SD"))
    assert result=={"CG":(D(2),D(1),D(5)),"SD":(D(1),D(1),D(5))}
    np.testing.assert_allclose(np.linalg.norm(np.array(result["CG"],float)-target["CB"]),np.sqrt(2))


@pytest.mark.parametrize("cb,n", (((0,0,0),(0,1,0)),((1,0,0),(2,0,0)),((float("nan"),0,0),(0,1,0))))
def test_degenerate_side_chain_frame_is_refused(cb,n):
    donor = {"N":n,"CA":(0,0,0),"CB":cb,"CG":(1,1,1)}
    with pytest.raises(ValueError):
        sidechain_transplant(donor,donor,("CG",))


def test_atom_origin_is_canonical_and_cannot_mislabel_a_constructed_atom_as_inherited():
    atom = ScaffoldAtom("A",1,"MET","SD","S",(D("0.123456789012345"),D(2),D(3)),
                        "CONSTRUCTED_MET_TEMPLATE",None,"SD")
    assert decode_canonical_bytes(atom.canonical_bytes(),ScaffoldAtom,maximum_bytes=4096)==atom
    with pytest.raises(ValueError,match="original serial"):
        ScaffoldAtom("A",1,"MET","SD","S",atom.xyz_angstrom,"RETAINED_PARENT",None,"SD")
    with pytest.raises(ValueError,match="cannot inherit"):
        ScaffoldAtom("A",1,"MET","SD","S",atom.xyz_angstrom,"CONSTRUCTED_MET_TEMPLATE",1,"SD")
