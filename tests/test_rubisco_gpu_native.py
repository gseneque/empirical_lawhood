# SPDX-License-Identifier: MPL-2.0
"""Required remote small-operator controls on a supported GPU, without enzymes.

The numerical fixture bypasses topology construction. Portable registered-route
controls own that boundary; none of these results authorize scientific entry.
"""

import json
import os

import numpy as np
import pytest

from tests.test_rubisco_periodic_density_reuse import numeric_operator as numeric_operator

pytestmark = pytest.mark.native('pyscf', 'openmm', 'openmm-cuda-12', 'gpu4pyscf-cuda12x')


@pytest.mark.parametrize('flavour,charge', (('RKS', 0), ('UKS', 0), ('RKS', 2), ('UKS', -2)))
@pytest.mark.parametrize('molecular_platform', ('CUDA', 'Reference'))
def test_direct_gpu_complete_return_cold_seeded_charged_and_periodic(numeric_operator, flavour, charge, molecular_platform):
    from empirical_lawhood.adapters.rubisco.rubisco_response.gpu_periodic_backend import GpuPeriodicBackend

    cpu, xyz, _ = numeric_operator(flavour, False)
    cpu.selection.qm_formal_charge = charge
    reference = os.environ.get('EL_RUBISCO_CPU_CONTROL')
    if reference is None:
        expected = cpu.evaluate(xyz)
    else:
        from tests.rubisco_gpu_reference import read_reference
        expected = read_reference(reference, os.environ['EL_RUBISCO_CPU_CONTROL_SHA256'],
            flavour=flavour, charge=charge, operator=cpu, coordinates=xyz)
    warm, _, rows = numeric_operator(flavour, True)
    warm.selection.qm_formal_charge = charge
    def observe(row):
        rows.append(row)
        if row['event'] in ('scf-entry', 'scf-iteration', 'scf-chunk-return', 'electronic-return',
                'qm-gradient-entry', 'qm-gradient-return', 'return', 'gpu-evaluation-cost'):
            fields = {k:v for k,v in row.items() if k in ('event', 'evaluation', 'cycle',
                'norm_gorb', 'norm_ddm', 'e_tot', 'converged', 'orbital_gradient_norm', 'failed')}
            print(json.dumps(dict(control='direct-periodic-gpu-progress', flavour=flavour,
                qm_charge=charge, **fields)), flush=True)
    warm.observe = observe
    warm.gpu_backend = GpuPeriodicBackend(device_memory_bytes=4*2**30, observe=observe,
        molecular_platform=molecular_platform)
    warm.dft = warm.gpu_backend.dft
    warm.integrator = warm.mm.VerletIntegrator(.0005)
    warm.context = warm.gpu_backend.openmm_context(warm.remainder, warm.integrator, warm.mm)
    actual = warm.evaluate(xyz)
    seeded = warm.evaluate(xyz)
    for label, returned in (('cold', actual), ('seeded', seeded)):
        print(json.dumps(dict(control='direct-periodic-gpu-cpu-comparison',
            flavour=flavour, qm_charge=charge, initial_density=label,
            energy_error_hartree=returned['energy_hartree']-expected['energy_hartree'],
            maximum_gradient_error_hartree_per_bohr=float(np.max(np.abs(
                returned['gradient_hartree_per_bohr']-expected['gradient_hartree_per_bohr']))))), flush=True)
        assert abs(returned['energy_hartree']-expected['energy_hartree']) < 1e-8
        np.testing.assert_allclose(returned['gradient_hartree_per_bohr'],
            expected['gradient_hartree_per_bohr'], atol=5e-7, rtol=0)
    moved = xyz.copy()
    moved[-1, 0] += warm.lattice[0, 0]
    periodic = warm.evaluate(moved)
    assert abs(periodic['energy_hartree']-actual['energy_hartree']) < 1e-8
    np.testing.assert_allclose(periodic['gradient_hartree_per_bohr'],
        actual['gradient_hartree_per_bohr'], atol=5e-7, rtol=0)
    # Independent central differences in both QM and MM coordinates. These
    # read complete energy returns rather than another analytic derivative.
    fd_errors = []
    for atom, axis in ((0, 0), (1, 2), (len(xyz)-1, 1)):
        plus, minus = xyz.copy(), xyz.copy()
        step_bohr = .001
        plus[atom, axis] += step_bohr*warm.bohr_angstrom
        minus[atom, axis] -= step_bohr*warm.bohr_angstrom
        gradient = (warm.evaluate(plus)['energy_hartree']-warm.evaluate(minus)['energy_hartree'])/(2*step_bohr)
        fd_errors.append(abs(gradient-actual['gradient_hartree_per_bohr'][atom, axis]))
    assert max(fd_errors) < 3e-6
    assert all(row['grid_response'] and not row['density_fitting'] for row in rows
        if row['event'] == 'compute-backend')
    policies = [row for row in rows if row['event'] == 'gpu-scf-potential-policy']
    assert len(policies) == 9
    assert all(not row['incremental_jk'] and not row['numerical_tolerances_changed'] for row in policies)
    assert [row['source_evaluation'] for row in rows if row['event'] == 'scf-initial-density'][:2] == [None, 1]
    assert len([row for row in rows if row['event'] == 'gpu-evaluation-cost']) == 9
    print(json.dumps(dict(control='direct-periodic-gpu', flavour=flavour, qm_charge=charge,
        molecular_platform=molecular_platform,
        energy_error_hartree=abs(actual['energy_hartree']-expected['energy_hartree']),
        maximum_gradient_error_hartree_per_bohr=float(np.max(np.abs(
            actual['gradient_hartree_per_bohr']-expected['gradient_hartree_per_bohr']))),
        maximum_finite_difference_error_hartree_per_bohr=max(fd_errors),
        gpu_complete_returns=9, cpu_complete_returns=1, full_enzyme_calls=0,
        observations=rows)))
