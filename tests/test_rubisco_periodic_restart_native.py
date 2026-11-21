# SPDX-License-Identifier: MPL-2.0
"""Actual small checkpoint/SCF/full-gradient controls, without enzyme admission.

These numerical controls inject the checked density at the solver seam. The
separate portable controls exercise full model binding and native-entry wiring.
"""

from hashlib import sha256
import json
import shutil

import numpy as np
import pytest

from empirical_lawhood.adapters.rubisco.rubisco_response import periodic_density_seed as selected
from empirical_lawhood.adapters.rubisco.rubisco_response import periodic_qmmm as qmmm
from tests.test_rubisco_periodic_density_reuse import numeric_operator as numeric_operator

pytestmark = [pytest.mark.native('pyscf'), pytest.mark.native('openmm')]


@pytest.mark.parametrize('flavour', ['RKS', 'UKS'])
def test_checkpoint_density_matches_independent_cold_complete_energy_and_gradient(numeric_operator, tmp_path, monkeypatch, flavour):
    from pyscf.scf import chkfile, hf, uhf
    solve = qmmm.solve_selected_scf
    checkpoint = tmp_path/'original-scf.h5'
    actual_density = None
    molecule_sha256 = None
    populations = None
    seeded_calls = []

    def selected_solve(mf, maximum_cycles, *, observe, evaluation, initial_density=None):
        nonlocal populations
        if actual_density is not None:
            assert initial_density is None
            assert selected.molecule_signature(mf.mol) == molecule_sha256
            populations = selected.validate_density_electrons(actual_density, mf.mol)
            initial_density = actual_density
            seeded_calls.append(sha256(initial_density.tobytes()).hexdigest())
        result = solve(mf, maximum_cycles, observe=observe, evaluation=evaluation, initial_density=initial_density)
        if actual_density is None:
            shutil.copyfile(mf.chkfile, checkpoint)
        return result

    monkeypatch.setattr(qmmm, 'solve_selected_scf', selected_solve)
    cold, xyz, cold_rows = numeric_operator(flavour, False)
    expected = cold.evaluate(xyz)
    mol, record = chkfile.load_scf(str(checkpoint))
    molecule_sha256 = selected.molecule_signature(mol)
    actual_density = np.asarray((hf if flavour == 'RKS' else uhf).make_rdm1(record['mo_coeff'], record['mo_occ']), dtype='<f8')
    actual_density.setflags(write=False)
    assert np.isfinite(actual_density).all()
    np.testing.assert_allclose(actual_density, actual_density.swapaxes(-1, -2), rtol=0, atol=1e-12)
    warm, _, warm_rows = numeric_operator(flavour, False)
    actual = warm.evaluate(xyz)
    assert len(seeded_calls) == 1
    energy_error = abs(actual['energy_hartree']-expected['energy_hartree'])
    gradient_error = float(np.max(np.abs(actual['gradient_hartree_per_bohr']-expected['gradient_hartree_per_bohr'])))
    assert energy_error < 1e-8 and gradient_error < 3e-7
    assert actual['orbital_gradient_norm'] < 1e-7 and actual['scf_converged']
    with pytest.raises(ValueError, match='electron or spin population'):
        selected.validate_density_electrons(actual_density*1.01, mol)
    if flavour == 'UKS':
        with pytest.raises(ValueError, match='electron or spin population'):
            selected.validate_density_electrons(actual_density[::-1], mol)
    print(json.dumps(dict(control='checkpoint-density-complete-coupled-return', flavour=flavour,
        entry_scope='SOLVER_SEAM; DOMAIN_IDENTITY_AND_ENTRY_WIRING_CHECKED_SEPARATELY',
        complete_energy_gradient_calls=2, full_enzyme_calls=0, electron_populations=populations,
        checkpoint_sha256=sha256(checkpoint.read_bytes()).hexdigest(), molecule_sha256=molecule_sha256,
        density_sha256=seeded_calls[0], energy_error_hartree=energy_error,
        maximum_gradient_error_hartree_per_bohr=gradient_error,
        cold_scf_iterations=sum(row['event'] == 'scf-iteration' for row in cold_rows),
        seeded_scf_iterations=sum(row['event'] == 'scf-iteration' for row in warm_rows),
        cold_wall_seconds=[row['wall_seconds'] for row in cold_rows if row['event'] == 'return'],
        seeded_wall_seconds=[row['wall_seconds'] for row in warm_rows if row['event'] == 'return'])))


@pytest.mark.parametrize('change', ['order', 'coordinates', 'basis', 'charge', 'spin', 'cartesian'])
def test_native_molecule_signature_detects_order_geometry_and_electronic_context(change):
    from pyscf import gto
    selected_args = dict(atom=[('O', (0., 0., 0.)), ('H', (.77, 0., .6)), ('H', (-.77, 0., .6))],
        basis='def2-svpd', charge=0, spin=0, verbose=0)
    original = gto.M(**selected_args)
    if change == 'order':
        selected_args['atom'] = selected_args['atom'][::-1]
    elif change == 'coordinates':
        selected_args['atom'] = [*selected_args['atom'][:2], ('H', (-.77, 0., .6000001))]
    elif change == 'basis':
        selected_args['basis'] = 'def2-svp'
    elif change == 'charge':
        selected_args['charge'] = 2
    elif change == 'spin':
        selected_args['spin'] = 2
    else:
        selected_args['cart'] = True
    assert selected.molecule_signature(original) != selected.molecule_signature(gto.M(**selected_args))


@pytest.mark.parametrize('change', ['none', 'extra', 'shape', 'dtype', 'soft-link', 'external-link', 'compressed'])
def test_checkpoint_layout_is_closed_bounded_and_direct(tmp_path, change):
    import h5py
    path = tmp_path/'layout.h5'
    with h5py.File(path, 'w') as handle:
        handle['mol'] = 'EXPOSED LAYOUT CONTROL ONLY'
        handle['scf/e_tot'] = -1.
        handle['scf/mo_coeff'] = np.eye(2)
        handle['scf/mo_energy'] = np.arange(2, dtype=float)
        handle['scf/mo_occ'] = np.array([2., 0.])
        if change == 'extra':
            handle['scf/extra'] = np.zeros(2)
        elif change != 'none':
            del handle['scf/mo_coeff']
            if change == 'shape':
                handle['scf/mo_coeff'] = np.eye(3)
            elif change == 'dtype':
                handle['scf/mo_coeff'] = np.eye(2, dtype=np.complex128)
            elif change == 'soft-link':
                handle['scf/mo_coeff'] = h5py.SoftLink('/scf/mo_energy')
            elif change == 'external-link':
                handle['scf/mo_coeff'] = h5py.ExternalLink('must-not-be-opened.h5', '/hidden')
            else:
                handle.create_dataset('scf/mo_coeff', data=np.eye(2), compression='gzip')
    original = path.read_bytes()
    if change == 'none':
        selected.validate_checkpoint_layout(path, (2, 2), (2,))
    else:
        with pytest.raises(ValueError, match='checkpoint'):
            selected.validate_checkpoint_layout(path, (2, 2), (2,))
    assert path.read_bytes() == original
    with pytest.raises(ValueError, match='allocation'):
        selected.validate_checkpoint_layout(path, (100000, 100000), (100000,))
