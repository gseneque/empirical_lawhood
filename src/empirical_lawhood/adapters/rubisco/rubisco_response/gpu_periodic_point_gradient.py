# SPDX-License-Identifier: Apache-2.0
# Copyright 2021-2024 The PySCF Developers. All Rights Reserved.
# Modified by the Empirical Lawhood project, 2026-11-05.
# Adapted from GPU4PySCF 1.8.1 qmmm/pbc/itrf.py (pinned by gpu_periodic_backend).
# See pyscf-periodic-LICENSE.txt.
"""Connect the pinned GPU point-charge potential and derivative kernels.

Upstream's periodic potential omits point charges and its AO derivative refuses
them, although the integral kernels support charge_exponents=None. Bind only
selected instances; retain Ewald, nuclear, XC and gas-phase owners.
"""

from types import MethodType


def selected_images(cell, mol):
    """Use the same images, centre and direct-field mask as the potential."""
    import cupy as cp
    coords = cp.asarray(cell.atom_coords())
    charges = cp.asarray(cell.atom_charges())
    lattice_images = cp.asarray(cell.get_lattice_Ls())
    all_coords = (coords[None, :, :] + lattice_images[:, None, :]).reshape(-1, 3)
    delta = all_coords - cp.mean(cp.asarray(mol.atom_coords()), axis=0)
    mask = cp.einsum('ix,ix->i', delta, delta) <= cell.rcut_hcore**2
    all_charges = cp.tile(charges, len(lattice_images))
    return all_coords, mask, all_coords[mask], all_charges[mask], len(lattice_images)


def bind_point_charge_potential(mean_field, *, observe):
    if mean_field.mm_mol.charge_model != 'point':
        return mean_field
    if getattr(mean_field, '_el_point_charge_potential', False):
        raise ValueError('GPU point-charge potential was already bound')
    original = mean_field.get_hcore

    def get_hcore(self, mol=None):
        from gpu4pyscf.gto.int3c1e import int1e_grids
        if mol is None:
            mol = self.mol
        # The pinned upstream method retains cell/region checks and the gas
        # Hamiltonian, but its != 'point' branch omits this entire operand.
        hcore = original(mol)
        _, _, coords, charges, _ = selected_images(self.mm_mol, mol)
        if len(coords):
            hcore += int1e_grids(mol, coords, charges=-charges, charge_exponents=None)
        return hcore

    mean_field.get_hcore = MethodType(get_hcore, mean_field)
    mean_field._el_point_charge_potential = True
    observe(dict(event='gpu-point-charge-potential', charge_exponents=None,
        kernel='int1e_grids', precision='float64'))
    return mean_field


def point_hcore_derivative(derivative, mol):
    import cupy as cp
    from gpu4pyscf.gto.int3c1e_ip import int1e_grids_ip1
    _, _, coords, charges, _ = selected_images(derivative.base.mm_mol, mol)
    if not len(coords):
        return cp.zeros((3, mol.nao, mol.nao))
    # Contract charges inside the GPU kernel; do not allocate nMM*nao*nao.
    return int1e_grids_ip1(mol, coords, charges=charges, charge_exponents=None)


def get_hcore(self, mol=None, exclude_ecp=False):
    import cupy as cp
    from gpu4pyscf.qmmm.pbc.itrf import QMMMGrad
    if mol is None:
        mol = self.mol
    original = super(QMMMGrad, self).get_hcore(mol, exclude_ecp=exclude_ecp)
    return cp.asarray(original) + point_hcore_derivative(self, mol)


def extra_force(self, atom_id=None):
    from gpu4pyscf.grad.rhf import contract_h1e_dm
    from gpu4pyscf.qmmm.pbc.itrf import QMMMGrad
    assert atom_id is None
    density = self.base.make_rdm1()
    if density.ndim == 3:
        density = density[0] + density[1]
    direct = contract_h1e_dm(self.mol, point_hcore_derivative(self, self.mol), density, hermi=1)
    return direct + super(QMMMGrad, self).extra_force()


def grad_hcore_mm(self, dm, mol=None):
    import cupy as cp
    from gpu4pyscf.gto.int3c1e_ip import int1e_grids_ip2
    if mol is None:
        mol = self.mol
    density = cp.asarray(dm)
    if density.ndim == 3:
        density = density[0] + density[1]
    all_coords, mask, coords, charges, image_count = selected_images(self.base.mm_mol, mol)
    gradient = cp.zeros_like(all_coords)
    if len(coords):
        gradient[mask] = int1e_grids_ip2(mol, coords, dm=density,
            charges=charges, charge_exponents=None).T
    return cp.asnumpy(gradient.reshape(image_count, -1, 3).sum(axis=0))


def bind_point_charge_gradient(derivative, *, observe):
    if derivative.base.mm_mol.charge_model != 'point':
        return derivative
    if getattr(derivative, '_el_point_charge_gradient', False):
        raise ValueError('GPU point-charge gradient was already bound')
    for name, method in (('get_hcore', get_hcore), ('extra_force', extra_force),
            ('grad_hcore_mm', grad_hcore_mm), ('contract_hcore_mm', grad_hcore_mm)):
        setattr(derivative, name, MethodType(method, derivative))
    derivative._el_point_charge_gradient = True
    observe(dict(event='gpu-point-charge-gradient', charge_exponents=None,
        qm_kernel='int1e_grids_ip1', mm_kernel='int1e_grids_ip2', precision='float64'))
    return derivative
