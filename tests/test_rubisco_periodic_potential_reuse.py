# SPDX-License-Identifier: MPL-2.0
"""Actual small PySCF controls for energy and direct J/K reuse, not an enzyme."""
import numpy as np
import pytest


pytestmark = pytest.mark.native('pyscf')


@pytest.fixture(params=('RKS', 'UKS'))
def periodic(request):
    from pyscf import dft, gto, lib
    from empirical_lawhood.adapters.rubisco.rubisco_response import pyscf_periodic_electronic as owner

    spin = int(request.param == 'UKS')
    atoms = 'O 0 0 0; H .77 .08 .6' if spin else 'O 0 0 0; H .77 0 .6; H -.77 0 .6'
    mol = gto.M(atom=atoms, basis='def2-svpd', spin=spin, verbose=0)
    base = getattr(dft, request.param)(mol)
    base.xc, base.grids.level = 'wb97x', 1
    field = np.array([[3.1, 1.2, -.8], [-3.8, .7, 1.4], [1.1, -3.1, 1.8],
        [-1.4, 2.8, 1.5], [.6, -.9, -3.2]])
    charges = np.array([.13, -.15, .07, -.12, .06])
    mf = owner.add_mm_charges(base, field, np.diag([20., 20., 20.]), charges,
        rcut_ewald=8., rcut_hcore=6., unit='Angstrom')
    mf.mm_mol.mesh = np.array([17, 17, 17])
    mf.max_memory = mf.mm_mol.max_memory = 512
    # Large enzyme calls use direct integrals. Select that same branch for
    # this small control without changing its Hamiltonian or density.
    mf._is_mem_enough = lambda: False
    with lib.with_omp_threads(1):
        overlap = mf.get_ovlp()
        density = mf.get_init_guess(mol, mf.init_guess, s1e=overlap)
        core = mf.get_hcore()
        potential = mf.get_veff(mol, density)
        yield mf, density, core, overlap, potential


def test_retained_potential_energy_needs_no_new_potential_or_integrals(periodic, monkeypatch):
    mf, density, core, _, potential = periodic
    total_density = density.sum(axis=0) if density.ndim == 3 else density
    expected = (np.einsum('ij,ji', core, total_density).real
        + potential.ecoul.real + potential.exc.real)

    def forbidden(*args, **kwargs):
        raise AssertionError('energy read repeated a completed potential or integral')

    monkeypatch.setattr(mf, 'get_veff', forbidden)
    monkeypatch.setattr(mf, 'get_jk', forbidden)
    actual, two_electron = mf.energy_elec(density, core, potential)
    assert abs(actual-expected) < 1e-12
    assert two_electron == potential.ecoul.real + potential.exc.real


def test_next_density_uses_incremental_integrals_and_matches_full_contraction(periodic, monkeypatch):
    mf, previous, core, overlap, old_potential = periodic
    fock = mf.get_fock(core, overlap, old_potential, previous)
    energies, coefficients = mf.eig(fock, overlap)
    density = mf.make_rdm1(coefficients, mf.get_occ(energies, coefficients))
    original = mf.get_jk
    received = []

    def get_jk(mol=None, dm=None, hermi=1, with_j=True, with_k=True, omega=None):
        received.append(np.array(dm, copy=True))
        return original(mol, dm, hermi, with_j, with_k, omega)

    monkeypatch.setattr(mf, 'get_jk', get_jk)
    incremental = mf.get_veff(mf.mol, density, previous, old_potential)
    assert len(received) == 2  # Full-range and long-range exchange of wb97x.
    for actual in received:
        np.testing.assert_array_equal(actual, density-previous)
    received.clear()
    complete = mf.get_veff(mf.mol, density)
    for actual in received:
        np.testing.assert_array_equal(actual, density)
    np.testing.assert_allclose(incremental, complete, rtol=0, atol=2e-10)
    for name in ('vj', 'vk', 'ecoul', 'exc'):
        np.testing.assert_allclose(getattr(incremental, name), getattr(complete, name), rtol=0, atol=2e-10)
