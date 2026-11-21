"""Independent supplied-array force checks, with no molecular engine contact."""
import numpy as np
import pytest
from empirical_lawhood.domains.rubisco.rubisco_response.gp_geometry_diagnostics import mobile_force_diagnostics, optimizer_force_diagnostics


@pytest.mark.numerical(oracle="Literal 3-4-0 force vector, sign-reversed construction gradient, and exact fixed-atom equality")
def test_force_and_optimizer_diagnostics_keep_physical_sign_and_denominator():
    forces = np.array([[3., -4., 0.], [100., 200., 300.]])
    barrier = np.array([[1., 2., 0.], [0., 0., 0.]])
    observed = mobile_force_diagnostics(forces=forces, moving=(0,), barrier_gradient=barrier,
                                        energy=10., barrier_energy=2.)
    assert observed == {
        'maximum_mobile_gradient_kj_mol_nm': 4.,
        'mobile_gradient_rms_kj_mol_nm': pytest.approx((25./3.)**.5),
        'augmented_energy_kj_mol': 12.,
        'maximum_augmented_mobile_gradient_kj_mol_nm': 6.,
    }
    initial = np.zeros((2, 3)); final = np.array([[1., 2., 3.], [0., 0., 0.]])
    final_metrics = optimizer_force_diagnostics(
        gradient=np.array([-3., 4., 0.]), barrier_gradient=barrier, moving=(0,),
        optimizer_gradient=np.array([-2., 6., 0.]), initial_coordinates=initial,
        final_coordinates=final,
    )
    assert final_metrics['maximum_final_original_vs_optimizer_gradient_error_kj_mol_nm'] == 0.
    assert final_metrics['maximum_final_construction_barrier_gradient_kj_mol_nm'] == 2.
    assert final_metrics['maximum_final_augmented_mobile_gradient_kj_mol_nm'] == 6.
    assert final_metrics['maximum_mobile_gradient_kj_mol_nm'] == 4.
    assert final_metrics['mobile_gradient_rms_kj_mol_nm'] == pytest.approx((25./3.)**.5)
    assert final_metrics['fixed_coordinates_bitwise_unchanged'] is True
    final[1,0] = np.nextafter(0., 1.)
    changed = optimizer_force_diagnostics(
        gradient=np.array([-3., 4., 0.]), barrier_gradient=barrier, moving=(0,),
        optimizer_gradient=np.array([-2., 6., 0.]), initial_coordinates=initial,
        final_coordinates=final,
    )
    assert changed['fixed_coordinates_bitwise_unchanged'] is False
