# SPDX-License-Identifier: MPL-2.0
"""Pure independent controls for custom QM/MM coordinate and force composition."""
import numpy as np
import pytest

from empirical_lawhood.domains.rubisco.rubisco_response.periodic_mm_remainder import (
    linked_qm_coordinates, pullback_qm_gradient, shifted_embedding_charges,
)
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_images import localize_periodic_field


@pytest.mark.numerical(oracle='Central finite differences of an independently written fixed-length cap plus anisotropic quadratic potential on all four physical atoms.')
def test_link_pullback_and_mm_sum_match_complete_physical_energy_derivative():
    xyz = np.array([[.2, .3, -.1], [1.2, -.2, .4], [3.4, 1.1, -.6], [5.1, -2.3, 1.8]])
    qm, links = (0, 1), ((1, 2, 1.09),)
    matrix = np.diag(np.arange(1., 10.)) + .17*np.ones((9, 9))
    target = np.arange(9)*.13
    def independent_energy(points):
        d = points[2]-points[1]
        cap = points[1]+1.09*d/np.sqrt(sum(float(v)**2 for v in d))
        z = np.concatenate((points[0], points[1], cap))-target
        # An independently specified MM contribution includes every original
        # atom; its gradient must be added once, including both cut endpoints.
        return .5*z@matrix@z + .35*np.sum(points*points)
    values, jacobians = linked_qm_coordinates(xyz, qm, links)
    qm_gradient = (matrix@(values.reshape(-1)-target)).reshape((-1, 3))
    composed = pullback_qm_gradient(len(xyz), qm, qm_gradient, jacobians) + .7*xyz
    numerical = np.empty_like(xyz)
    h = 1e-5
    for i in range(len(xyz)):
        for axis in range(3):
            plus, minus = xyz.copy(), xyz.copy()
            plus[i, axis] += h
            minus[i, axis] -= h
            numerical[i, axis] = (independent_energy(plus)-independent_energy(minus))/(2*h)
    np.testing.assert_allclose(composed, numerical, rtol=2e-9, atol=3e-8)
    assert np.linalg.norm(composed[2]-.7*xyz[2]) > 0  # link force reaches MM endpoint


@pytest.mark.numerical(oracle='A potential depending only on cap-to-QM separation is invariant under rigid translation; complete pulled-back gradients sum to zero.')
def test_link_force_conservation_requires_both_physical_endpoints():
    xyz = np.array([[0., 0., 0.], [2., .7, -.2], [4., 1., .4]])
    values, jacobians = linked_qm_coordinates(xyz, (0, 1), ((1, 2, 1.09),))
    d = values[2]-values[0]
    gradient = np.array([-d, np.zeros(3), d])
    physical = pullback_qm_gradient(3, (0, 1), gradient, jacobians)
    np.testing.assert_allclose(physical.sum(axis=0), np.zeros(3), atol=1e-15)


@pytest.mark.numerical(oracle='A cut-MM charge0.6 splits equally among two non-cut MM neighbours: -.1+.3=.2 and .2+.3=.5; complete MM charge0.7 is conserved.')
def test_declared_embedding_redistribution_conserves_charge_without_claiming_dipoles():
    shifted, audit = shifted_embedding_charges((1., .6, -.1, .2), (0,), ((0, 1), (1, 2), (1, 3)), ((0, 1),))
    np.testing.assert_allclose(shifted, (0., 0., .2, .5), atol=1e-16)
    assert audit['embedding_mm_charge'] == pytest.approx(.7)
    assert audit['dipole_correction'] is False and audit['mm_force_field_charges_changed'] is False


@pytest.mark.numerical(oracle='A cell-centred field at x=25 in a length10 lattice shifts by exactly2 boxes; infinitesimal displacement away from a boundary has identity Jacobian.')
def test_periodic_field_images_preserve_coordinate_derivative_away_from_boundaries():
    qm = np.array([[0., 0., 0.], [2., 0., 0.]])
    mm = np.array([[25., 3., -12.], [2., -4., 1.]])
    local, images = localize_periodic_field(qm, mm, np.diag([10., 10., 10.]))
    np.testing.assert_array_equal(images, [[2, 0, -1], [0, 0, 0]])
    np.testing.assert_allclose(local, [[5., 3., -2.], [2., -4., 1.]])
    moved = mm.copy(); moved[0, 1] += 1e-5
    after, shifted = localize_periodic_field(qm, moved, np.diag([10., 10., 10.]))
    np.testing.assert_array_equal(shifted, images)
    np.testing.assert_allclose((after-local)/1e-5, [[0., 1., 0.], [0., 0., 0.]], atol=1e-10)
