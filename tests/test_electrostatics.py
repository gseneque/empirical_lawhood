# SPDX-License-Identifier: MPL-2.0
"""Independent Ewald-background values and explicit arithmetic refusals."""

import math

import pytest

from empirical_lawhood.methods.electrostatics import charged_background_energy


@pytest.mark.numerical(oracle='Analytic uniform-background QM self/cross energies: pi/90, -4pi, 0 and -pi/2 hartree for the declared exact charge/cell cases')
@pytest.mark.parametrize('qm,mm,volume,eta,coefficient', (
    (-2, 5, 8000, .3, 1/90),
    (2, 0, 2, .5, -4),
    (2, -1, 2, .5, 0),
    (1, 0, 1, 1, -.5),
))
def test_uniform_background_independent_analytic_cases(qm, mm, volume, eta, coefficient):
    result = charged_background_energy(qm_charge=qm, mm_charge=mm,
        volume_bohr3=volume, eta_inverse_bohr=eta)
    assert result == pytest.approx(math.pi*coefficient, abs=1e-15, rel=1e-15)


@pytest.mark.parametrize('changed', (
    {'qm_charge': math.nan}, {'mm_charge': math.inf}, {'volume_bohr3': 0},
    {'eta_inverse_bohr': -1}, {'qm_charge': 1e308},
    {'volume_bohr3': 1e308, 'eta_inverse_bohr': 1e308},
    {'eta_inverse_bohr': 1e-300},
))
def test_background_refuses_invalid_or_unrepresentable_arithmetic(changed):
    selected = dict(qm_charge=1, mm_charge=0, volume_bohr3=1, eta_inverse_bohr=1)
    with pytest.raises(ValueError, match='charged periodic background'):
        charged_background_energy(**(selected | changed))
