# SPDX-License-Identifier: MPL-2.0
"""Small actual CUDA controls; these establish no molecular qualification."""

import json

import numpy as np
import pytest

pytestmark = pytest.mark.native('openmm', 'openmm-cuda-12')


def test_cuda_double_complete_periodic_forces_match_reference_and_finite_difference(tmp_path):
    import openmm as mm
    from openmm import unit
    from empirical_lawhood.execution.resources.accelerated_compute import observe_cuda_devices

    devices = observe_cuda_devices()
    assert len(devices) == 1
    system = mm.System()
    nonbonded = mm.NonbondedForce()
    nonbonded.setNonbondedMethod(mm.NonbondedForce.PME)
    nonbonded.setCutoffDistance(.8)
    nonbonded.setPMEParameters(4.5, 32, 32, 32)
    # Binary-representable parameters separate arithmetic from the upstream
    # CUDA float32 nonbonded-parameter storage assessed in the next control.
    for mass, charge in ((16., -.75), (1., .375), (1., .5)):
        system.addParticle(mass)
        nonbonded.addParticle(charge, .125, .015625)
    system.addForce(nonbonded)
    system.setDefaultPeriodicBoxVectors(mm.Vec3(2, 0, 0), mm.Vec3(0, 2, 0), mm.Vec3(0, 0, 2))
    xyz = np.array([[.2, .3, .4], [.31, .28, .45], [.19, .42, .39]])
    contexts = []
    try:
        for name in ('Reference', 'CUDA'):
            integrator = mm.VerletIntegrator(.0005)
            platform = mm.Platform.getPlatformByName(name)
            properties = ({'Precision': 'double', 'DeviceIndex': '0', 'DeterministicForces': 'true'}
                if name == 'CUDA' else {})
            context = mm.Context(system, integrator, platform, properties)
            contexts.append((integrator, context))
            if name == 'CUDA':
                assert {key: platform.getPropertyValue(context, key) for key in properties} == properties

        def evaluate(context, points):
            context.setPositions(points*unit.nanometer)
            state = context.getState(getEnergy=True, getForces=True)
            return (state.getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole),
                state.getForces(asNumpy=True).value_in_unit(unit.kilojoule_per_mole/unit.nanometer))

        expected, forces = evaluate(contexts[0][1], xyz)
        actual, cuda_forces = evaluate(contexts[1][1], xyz)
        assert abs(actual-expected) < 1e-7
        np.testing.assert_allclose(cuda_forces, forces, atol=1e-5, rtol=0)
        errors = []
        for atom in range(3):
            for axis in range(3):
                plus, minus = xyz.copy(), xyz.copy()
                plus[atom, axis] += 1e-5
                minus[atom, axis] -= 1e-5
                numerical = -(evaluate(contexts[1][1], plus)[0]-evaluate(contexts[1][1], minus)[0])/2e-5
                errors.append(abs(numerical-cuda_forces[atom, axis]))
        assert max(errors) < 1e-3
        shifted = xyz.copy()
        shifted[-1, 0] += 2
        invariant, invariant_forces = evaluate(contexts[1][1], shifted)
        assert abs(invariant-actual) < 1e-8
        np.testing.assert_allclose(invariant_forces, cuda_forces, atol=1e-6, rtol=0)
        from hashlib import sha256
        from empirical_lawhood.adapters.rubisco.rubisco_response.amber_system_copy import native_system_sha256
        from empirical_lawhood.domains.rubisco.rubisco_response.periodic_mm_precision import assess_molecular_precision
        from empirical_lawhood.adapters.rubisco.rubisco_response.periodic_mm_precision import retain_molecular_precision
        native_digest = native_system_sha256(system, unit)
        retain_molecular_precision(system=system, context=contexts[1][1], coordinates_angstrom=xyz*10,
            directory=tmp_path)
        retained = {p.name:p.read_bytes() for p in tmp_path.iterdir()}
        compared = assess_molecular_precision(retained, physical_atom_count=3,
            coordinate_sha256=sha256(np.asarray(xyz*10, dtype='<f8').tobytes()).hexdigest(),
            remainder_sha256=native_digest)
        assert abs(compared['energy_change_kj_mol']) < 1e-7
        assert compared['maximum_force_change_kj_mol_nm'] < 1e-5
        assert compared['completed_mm_evaluations'] == 2 and compared['electronic_evaluations'] == 0
        assert compared['parameter_rounding_isolated'] is False
        assert native_system_sha256(system, unit) == native_digest
        print(json.dumps(dict(control='charged-periodic-openmm-cuda-double', openmm=mm.__version__,
            device=devices[0].name, device_uuid=devices[0].uuid,
            compute_capability=devices[0].compute_capability, charged_cell_e=.125,
            energy_difference_kj_mol=abs(actual-expected),
            maximum_force_difference_kj_mol_nm=float(np.max(np.abs(forces-cuda_forces))),
            maximum_finite_difference_error_kj_mol_nm=max(errors), full_enzyme_calls=0)))
    finally:
        contexts.clear()


def test_cuda_parameter_rounding_is_measured_separately_from_double_kernel_arithmetic():
    import openmm as mm
    from openmm import unit

    xyz = np.array([[0., 0., 0.], [.2, .13, .07]])
    values = []
    for platform_name, rounded in (('Reference', False), ('Reference', True), ('CUDA', False)):
        system, force = mm.System(), mm.NonbondedForce()
        for charge in (.13, -.27):
            system.addParticle(1)
            q = float(np.float32(charge)) if rounded else charge
            force.addParticle(q, .125, .015625)
        system.addForce(force)
        integrator = mm.VerletIntegrator(.0005)
        props = {'Precision': 'double', 'DeviceIndex': '0', 'DeterministicForces': 'true'} if platform_name == 'CUDA' else {}
        context = mm.Context(system, integrator, mm.Platform.getPlatformByName(platform_name), props)
        context.setPositions(xyz*unit.nanometer)
        state = context.getState(getEnergy=True, getForces=True)
        values.append((state.getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole),
            state.getForces(asNumpy=True).value_in_unit(unit.kilojoule_per_mole/unit.nanometer)))
        del context, integrator
    exact, rounded, cuda = values
    assert abs(cuda[0]-rounded[0]) < 1e-8
    np.testing.assert_allclose(cuda[1], rounded[1], atol=1e-7, rtol=0)
    assert abs(cuda[0]-exact[0]) > 1e-8
    print(json.dumps(dict(control='openmm-cuda-parameter-rounding',
        precision_property='double', nonbonded_parameter_storage='UPSTREAM_FLOAT32',
        exact_parameter_energy_difference_kj_mol=abs(cuda[0]-exact[0]),
        exact_parameter_force_difference_kj_mol_nm=float(np.max(np.abs(cuda[1]-exact[1]))),
        rounded_parameter_kernel_energy_difference_kj_mol=abs(cuda[0]-rounded[0]),
        molecular_accuracy_assessment='PENDING', full_enzyme_calls=0)))
