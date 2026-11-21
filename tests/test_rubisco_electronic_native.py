# SPDX-License-Identifier: MPL-2.0
"""Small original-integral and constrained-gradient controls; no enzyme evidence."""

from dataclasses import fields
from decimal import Decimal
import json

import numpy as np
import pytest

from tests.test_rubisco_periodic_density_reuse import numeric_operator as numeric_operator


@pytest.mark.native('pyscf')
def test_breit_pauli_direct_contractions_match_dense_integral_oracle():
    from pyscf import gto
    from pyscf.lib.parameters import LIGHT_SPEED
    from empirical_lawhood.domains.rubisco.rubisco_response.electronic_states import SpinOrbitMeanFieldSettings
    from empirical_lawhood.adapters.rubisco.rubisco_response.spin_orbit_native import breit_pauli_mean_field
    mol = gto.M(atom='O 0 0 0; H .76 0 .59; H -.76 0 .59',basis='sto-3g',verbose=0)
    overlap = mol.intor('int1e_ovlp')
    # A disclosed finite test density, with no new electronic-state solve.
    density = np.linalg.inv(overlap)
    settings = SpinOrbitMeanFieldSettings('soc.exposed-integral-control',256,Decimal('1e-14'))
    report,terms = breit_pauli_mean_field(mol,density,settings=settings)
    tensor = mol.intor('int2e_p1vxp1_sph',comp=3,aosym='s1')
    direct = np.einsum('xijkl,lk->xij',tensor,density)
    exchange1 = np.einsum('xijkl,jk->xil',tensor,density)
    exchange2 = np.einsum('xijkl,li->xkj',tensor,density)
    expected_two = -(direct-1.5*exchange1-1.5*exchange2)/(2*LIGHT_SPEED**2)
    expected_one = np.zeros_like(expected_two)
    for atom in range(mol.natm):
        with mol.with_rinv_origin(mol.atom_coord(atom)):
            expected_one += mol.atom_charge(atom)*mol.intor('int1e_prinvxp_sph',comp=3)/(2*LIGHT_SPEED**2)
    np.testing.assert_allclose(terms['soc-one-electron-imaginary'],expected_one,rtol=0,atol=2e-13)
    np.testing.assert_allclose(terms['soc-two-electron-imaginary'],expected_two,rtol=0,atol=2e-13)
    assert report['physical_spin_admission'] == 'UNEVALUABLE'
    assert np.linalg.norm(expected_two) > 0


@pytest.mark.native('pyscf','openmm','openmm-cuda-12','gpu4pyscf-cuda12x')
def test_constrained_gpu_periodic_complete_gradient_has_independent_two_step_differences(numeric_operator,tmp_path):
    from empirical_lawhood.adapters.rubisco.rubisco_response.constrained_electronic_native import record_constrained_state
    from empirical_lawhood.domains.rubisco.rubisco_response.constrained_electronic_read import assess_electronic_arrays
    from empirical_lawhood.domains.rubisco.rubisco_response.electronic_states import ConstrainedElectronicState, ElectronicPopulationConstraint, ElectronicStateCriteria
    from empirical_lawhood.adapters.rubisco.rubisco_response.gpu_periodic_backend import GpuPeriodicBackend
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_force_contracts import ConstrainedPeriodicForceSettings
    from empirical_lawhood.science.identity.provenance import ObjectIdentity
    operator,xyz,rows = numeric_operator('RKS',False)
    pin = ObjectIdentity('exposed.numeric-state','empirical-lawhood/testing/exposed-state','1.0.0','0'*64)
    state = ConstrainedElectronicState('state.exposed-minao-water',pin,operator.qm,0,1,
        (ElectronicPopulationConstraint('constraint.exposed-oxygen','ELECTRON_POPULATION',(0,),Decimal('8.2')),),
        Decimal('1e-7'),Decimal('1e-10'),100,(Decimal(0),),pin)
    values = {f.name:getattr(operator.settings,f.name) for f in fields(operator.settings)}
    values.update(settings_id='settings.exposed-constrained-control',ks_flavour='UKS',state=state)
    operator.settings = ConstrainedPeriodicForceSettings(**values)
    operator.gpu_backend = GpuPeriodicBackend(device_memory_bytes=4*2**30,observe=rows.append)
    operator.dft = operator.gpu_backend.dft
    operator.integrator = operator.mm.VerletIntegrator(.0005)
    operator.context = operator.gpu_backend.openmm_context(operator.remainder,operator.integrator,operator.mm)
    operator.capture_electronic_state = lambda mf,gpu,evaluation,diagnostics:record_constrained_state(
        tmp_path,mf=mf,gpu=gpu,state=state,evaluation=evaluation,diagnostics=diagnostics)
    actual = operator.evaluate(xyz)
    metadata = json.loads((tmp_path/'electronic.0000000000000001.state.json').read_text())
    arrays = {name:np.load(tmp_path/('electronic.0000000000000001.'+name+'.npy'),allow_pickle=False)
        for name in metadata['arrays']}
    criteria = ElectronicStateCriteria('criteria.exposed-electronic',Decimal('1e-7'),Decimal('.001'),
        Decimal('.999'),Decimal('.0001'),2**28)
    checked = assess_electronic_arrays(state=state,metadata=metadata,arrays=arrays,criteria=criteria)
    assert checked['selected_matrix_criteria'] == checked['selected_spin_square_criteria'] == 'SATISFIED'
    differences = []
    for atom,axis in ((0,0),(1,2),(len(xyz)-1,1)):
        errors = []
        for step in (.002,.001):
            plus,minus = xyz.copy(),xyz.copy()
            plus[atom,axis] += step*operator.bohr_angstrom
            minus[atom,axis] -= step*operator.bohr_angstrom
            observed = (operator.evaluate(plus)['energy_hartree']-operator.evaluate(minus)['energy_hartree'])/(2*step)
            errors.append(abs(observed-actual['gradient_hartree_per_bohr'][atom,axis]))
        assert max(errors) < 4e-6
        differences.append(errors)
    assert operator.evaluations == 13
    assert all(row['policy'] == 'COLD_START' for row in rows if row['event'] == 'scf-initial-density')
    print(json.dumps(dict(control='CONSTRAINED_PERIODIC_COMPLETE_GRADIENT',differences=differences,
        original_electronic_assessment=checked,complete_force_returns=13,enzyme_force_returns=0)))
