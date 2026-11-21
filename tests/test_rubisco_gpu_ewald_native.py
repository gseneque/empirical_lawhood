# SPDX-License-Identifier: MPL-2.0
"""GPU Ewald blocking parity on the pinned upstream operator, without enzyme SCF."""

import json

import numpy as np
import pytest

pytestmark = pytest.mark.native('pyscf', 'gpu4pyscf-cuda12x')


@pytest.mark.parametrize('gaussian', (False, True))
def test_complete_gpu_ewald_potential_and_gradient_across_uneven_blocks(monkeypatch, gaussian):
    import cupy as cp
    from gpu4pyscf import dft
    from gpu4pyscf.qmmm.pbc import itrf
    from pyscf import gto
    from empirical_lawhood.adapters.rubisco.rubisco_response import gpu_periodic_ewald as owner

    mol = gto.M(atom='He 0 0 0; H 0 0 1.2; H 0 0 -1.2', basis='sto-3g', verbose=0)
    coords = np.array([[3., .5, 1.], [-3., 1., .5], [1., -2., 3.], [2., 3., -1.]])
    charges = np.array([.4, -.2, -.3, .1])
    mean_field = itrf.add_mm_charges(dft.RKS(mol), coords, np.eye(3)*14, charges,
        radii=np.array([.6, .8, .7, 1.]) if gaussian else None,
        rcut_ewald=6, rcut_hcore=4, unit='Angstrom')
    cell = mean_field.mm_mol
    cell.mesh = np.array([5, 7, 5])
    cell.get_ewald_params = lambda precision=None, rcut=None: (.2, 6/.52917721092)
    dm = cp.eye(mol.nao)*.5
    upstream_potential = cell.get_ewald_pot
    original_cross = upstream_potential(mol.atom_coords(), cell.atom_coords(), cell.atom_charges(), cell.get_zetas())
    original_self = upstream_potential(mol.atom_coords())
    original_derivative = mean_field.Gradients()
    expected = original_derivative.grad_ewald(dm, with_mm=True)
    rows = []
    owner.bind_bounded_ewald(mean_field, device_memory_bytes=2**30, observe=rows.append)
    original_length = owner.reciprocal_block_length

    def small_blocks(**values):
        block, per_point, budget = original_length(**values)
        return min(block, 13), per_point, budget

    monkeypatch.setattr(owner, 'reciprocal_block_length', small_blocks)
    actual_cross = cell.get_ewald_pot(mol.atom_coords(), cell.atom_coords(), cell.atom_charges(), cell.get_zetas())
    actual_self = cell.get_ewald_pot(mol.atom_coords())
    for original, actual in zip((*original_cross, *original_self), (*actual_cross, *actual_self)):
        np.testing.assert_allclose(cp.asnumpy(actual), cp.asnumpy(original), atol=2e-12, rtol=0)
    derivative = owner.bind_bounded_ewald_gradient(mean_field.Gradients())
    actual = derivative.grad_ewald(dm, with_mm=True)
    for original, value in zip(expected, actual):
        np.testing.assert_allclose(value, original, atol=2e-12, rtol=0)
    np.testing.assert_allclose(derivative.grad_ewald(cp.stack((dm/2, dm/2))), actual[0], atol=2e-12, rtol=0)
    completed = [row for row in rows if row['event'] == 'gpu-ewald-reciprocal-return']
    assert completed and all(row['blocks'] > 1 and row['reciprocal_points'] == 175 for row in completed)
    print(json.dumps(dict(gaussian=gaussian, maximum_gradient_error=max(
        float(np.max(np.abs(x-y))) for x, y in zip(expected, actual)), observations=rows)))
