# SPDX-License-Identifier: MPL-2.0
"""Actual small E/G controls; constructor and enzyme admission are not claimed."""
from dataclasses import replace
from decimal import Decimal
import json
from types import SimpleNamespace

import pytest

pytestmark = [pytest.mark.native('pyscf'), pytest.mark.native('openmm')]


@pytest.fixture
def numeric_operator():
    import numpy as np
    import openmm as mm
    from openmm import unit
    from pyscf import dft, gto, lib
    from empirical_lawhood.domains.rubisco.rubisco_response import periodic_images, periodic_mm_remainder
    from empirical_lawhood.adapters.rubisco.rubisco_response import pyscf_periodic_electronic
    from empirical_lawhood.adapters.rubisco.rubisco_response.periodic_qmmm import COULOMB_KJ_NM_PER_MOL_E2, PeriodicCoupledOperator
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_force_contracts import PeriodicForceSettings
    instances = []

    def make(flavour, reuse):
        # Disclosed water/OH plus five-charge numeric fixture. A zero MM
        # remainder permits independent embedded-quantum comparisons. This
        # bypasses constructor/topology admission and supplies no enzyme model.
        qm_xyz = [[0., 0., 0.], [.77, .08 if flavour == 'UKS' else 0., .6]]
        if flavour == 'RKS':
            qm_xyz.append([-.77, 0., .6])
        field = [[3.1, 1.2, -.8], [-3.8, .7, 1.4], [1.1, -3.1, 1.8],
            [-1.4, 2.8, 1.5], [.6, -.9, -3.2]]
        xyz = np.asarray(qm_xyz+field)
        obj = object.__new__(PeriodicCoupledOperator)
        obj.np, obj.mm, obj.unit, obj.gto = np, mm, unit, gto

        def direct(factory):
            def make_mean_field(mol):
                mf = factory(mol)
                mf._is_mem_enough = lambda: False
                return mf
            return make_mean_field

        obj.dft = SimpleNamespace(RKS=direct(dft.RKS), UKS=direct(dft.UKS))
        obj.coupling, obj.images = periodic_mm_remainder, periodic_images
        obj.electronic = pyscf_periodic_electronic
        obj.settings = PeriodicForceSettings('settings.exposed-density-reuse',
            'wb97x', 'def2-svpd', flavour, 3, Decimal('1e-11'), Decimal('1e-7'),
            None, 1024, Decimal(8), Decimal(6), Decimal('.3'), (17, 17, 17), Decimal('1e-10'))
        obj.representation = SimpleNamespace(atoms=tuple(SimpleNamespace(atomic_number=z)
            for z in (8, *([1]*(len(xyz)-1)))))
        obj.selection = SimpleNamespace(qm_formal_charge=0, spin_multiplicity=1 if flavour == 'RKS' else 2)
        obj.qm, obj.mm_indices = tuple(range(len(qm_xyz))), tuple(range(len(qm_xyz), len(xyz)))
        obj.physical_count = len(xyz)
        obj.numbers = [obj.representation.atoms[i].atomic_number for i in obj.qm]
        obj.qm_charge = obj.selection.qm_formal_charge
        obj.multiplicity = obj.selection.spin_multiplicity
        obj.links = ()
        obj.lattice = np.eye(3)*20
        obj.embedding = np.array([.13, -.15, .07, -.12, .06])
        obj.remainder = mm.System()
        for _ in xyz:
            obj.remainder.addParticle(1)
        obj.remainder.setDefaultPeriodicBoxVectors(mm.Vec3(2, 0, 0), mm.Vec3(0, 2, 0), mm.Vec3(0, 0, 2))
        obj.bohr_angstrom, obj.bohr_nm = .52917721092, .52917721092/10
        obj.hartree_kj_mol = COULOMB_KJ_NM_PER_MOL_E2/obj.bohr_nm
        obj.integrator = mm.VerletIntegrator(.0005)
        obj.context = mm.Context(obj.remainder, obj.integrator, mm.Platform.getPlatformByName('Reference'))
        obj.gradient_unit = 'Eh/PySCF-Bohr-0.52917721092-A'
        obj.evaluations, obj.reuse_converged_density = 0, reuse
        obj._converged_density_guess = None
        observations = []
        obj.observe = observations.append
        instances.append(obj)
        return obj, xyz, observations

    with lib.with_omp_threads(1):
        yield make
    for obj in instances:
        del obj.context, obj.integrator


@pytest.mark.parametrize('flavour', ['RKS', 'UKS'])
def test_following_geometry_matches_independent_cold_energy_and_complete_gradient(numeric_operator, flavour):
    import numpy as np
    warm, original, rows = numeric_operator(flavour, True)
    first = warm.evaluate(original)
    moved = original.copy()
    moved[1, 0] += .002
    moved[-1, 1] += .003  # Fresh MM electrostatics and fresh QM geometry.
    second = warm.evaluate(moved)
    cold, _, cold_rows = numeric_operator(flavour, False)
    reference = cold.evaluate(moved)
    returned = warm.evaluate(original)
    comparisons = []
    for actual, expected in ((second, reference), (returned, first)):
        assert abs(actual['energy_hartree']-expected['energy_hartree']) < 1e-8
        np.testing.assert_allclose(actual['gradient_hartree_per_bohr'],
            expected['gradient_hartree_per_bohr'], rtol=0, atol=3e-7)
        assert actual['orbital_gradient_norm'] < 1e-7
        comparisons.append(dict(energy_difference_hartree=abs(actual['energy_hartree']-expected['energy_hartree']),
            maximum_gradient_difference_hartree_per_bohr=float(np.max(np.abs(
                actual['gradient_hartree_per_bohr']-expected['gradient_hartree_per_bohr'])))))
    guesses = [row for row in rows if row['event'] == 'scf-initial-density']
    assert [row['source_evaluation'] for row in guesses] == [None, 1, 2]
    assert guesses[1]['source_coordinate_sha256'] != guesses[2]['source_coordinate_sha256']
    assert all(row['density_sha256'] and row['density_shape'] for row in guesses[1:])
    assert [row['source_evaluation'] for row in cold_rows if row['event'] == 'scf-initial-density'] == [None]
    assert sum(row['event'] == 'entry' for row in rows) == 3
    assert sum(row['event'] == 'return' for row in rows) == 3
    print(json.dumps(dict(control='complete-periodic-density-reuse', flavour=flavour,
        complete_energy_gradient_calls=4, enzyme_calls=0, comparisons=comparisons,
        warm_iteration_counts=[sum(row['event'] == 'scf-iteration' and row['evaluation'] == i
            for row in rows) for i in (1, 2, 3)],
        cold_comparison_iteration_count=sum(row['event'] == 'scf-iteration' for row in cold_rows),
        warm_complete_call_wall_seconds=[row['wall_seconds'] for row in rows if row['event'] == 'return'],
        cold_comparison_call_wall_seconds=[row['wall_seconds'] for row in cold_rows if row['event'] == 'return'],
        initial_density_observations=guesses)))


@pytest.mark.parametrize('failure', ['engine-error', 'changed-context', 'invalid-coordinates'])
def test_failure_does_not_replay_or_supply_the_next_density(numeric_operator, failure):
    obj, xyz, rows = numeric_operator('RKS', True)
    first = obj.evaluate(xyz)
    original_gto, original_settings = obj.gto, obj.settings
    if failure == 'engine-error':
        def broken(**kwargs):
            raise ArithmeticError('original engine failure')
        obj.gto = SimpleNamespace(M=broken)
        expected = ArithmeticError
        message = 'original engine failure'
    elif failure == 'changed-context':
        obj.settings = replace(obj.settings, basis='def2-tzvpd')
        expected = ValueError
        message = 'changed fixed operator context'
    else:
        expected = ValueError
        message = 'all finite physical coordinates'
    with pytest.raises(expected, match=message):
        obj.evaluate(xyz[:-1] if failure == 'invalid-coordinates' else xyz)
    entered_failure = failure != 'invalid-coordinates'
    assert [row['event'] for row in rows].count('error') == int(entered_failure)
    assert [row['event'] for row in rows].count('entry') == 1+int(entered_failure)
    assert [row['event'] for row in rows].count('return') == 1
    obj.gto, obj.settings = original_gto, original_settings
    last = obj.evaluate(xyz)
    assert abs(last['energy_hartree']-first['energy_hartree']) < 1e-8
    guesses = [row for row in rows if row['event'] == 'scf-initial-density']
    assert guesses[-1]['evaluation'] == 2+int(entered_failure) and guesses[-1]['source_evaluation'] is None


def test_spin_trial_uses_the_selected_electron_counts_and_only_this_call(numeric_operator):
    import numpy as np
    operator, xyz, events = numeric_operator("UKS", False)
    captured = []
    control = operator.evaluate(xyz, capture_numerical_state=lambda mf: captured.append(np.array(mf.make_rdm1())))
    assert len(captured) == 1
    density = captured[0]
    for invalid, message in ((density[0], "two finite symmetric"), (np.zeros_like(density), "electron populations")):
        with pytest.raises(ValueError, match=message):
            operator.evaluate(xyz, spin_trial_density=invalid, capture_numerical_state=lambda _: pytest.fail("invalid state returned"))
    observed = operator.evaluate(xyz, spin_trial_density=density)
    assert abs(observed["energy_hartree"] - control["energy_hartree"]) < 1e-8
    np.testing.assert_allclose(observed["gradient_hartree_per_bohr"], control["gradient_hartree_per_bohr"], rtol=0, atol=3e-7)
    assert [r["event"] for r in events].count("error") == 2
    operator.close()
    with pytest.raises(ValueError, match="active native context"):
        operator.evaluate(xyz)
