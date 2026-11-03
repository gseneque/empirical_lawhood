# SPDX-License-Identifier: MPL-2.0
"""Independent state-balance and boundary falsifiers for the declared topology."""

from decimal import Decimal as D

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.rubisco_cycle_constraints.science import (
    BranchRates, branch_observables, common_release_response, finite_gas_flux,
    joint_necessities, realize_conditional_branch,
)


@pytest.mark.parametrize('a,b,release,off', [(3, 0, 7, 2), (3, 5, 7, 2), (7, 2, 1, 0), (1, 20, 4, 13)])
@pytest.mark.parametrize('gas', ['0', '0.01', '1', '100'])
def test_flux_matches_independent_normalized_state_balance(a, b, release, off, gas):
    rates = BranchRates(D('0.2'), D(off), D(a), D(b), D(release))
    association = float(rates.association_um_inv_s_inv * D(gas))
    # Columns are origin states X/C/P; final row imposes the actual enzyme census.
    matrix = np.array([[-association, off, release],
                       [association, -(off + a), b], [1, 1, 1]], dtype=float)
    occupancy = np.linalg.solve(matrix, np.array([0, 0, 1], dtype=float))
    assert min(occupancy) >= -1e-14
    assert np.sum(occupancy) == pytest.approx(1)
    assert float(finite_gas_flux(rates, D(gas))) == pytest.approx(release * occupancy[2], rel=1e-12, abs=1e-14)


def test_irreversible_release_cancellation_and_reverse_product_exception():
    for reverse in [D(0), D(5)]:
        baseline = BranchRates(D('0.2'), D(2), D(3), reverse, D(7))
        faster = BranchRates(D('0.2'), D(2), D(3), reverse, D(70))
        first, second = branch_observables(baseline), branch_observables(faster)
        assert second.saturated_turnover_s_inv > first.saturated_turnover_s_inv
        if reverse == 0:
            assert second.catalytic_efficiency_um_inv_s_inv == first.catalytic_efficiency_um_inv_s_inv
        else:
            assert second.catalytic_efficiency_um_inv_s_inv > first.catalytic_efficiency_um_inv_s_inv


def test_joint_target_requires_unobserved_reverse_asymmetry_for_fast_low_specificity_parent():
    common = dict(parent_turnover=D('9.5'), parent_specificity=D('56.3'),
                  target_turnover=D('5.46'), target_specificity=D(238), carbon_v=D(6))
    rejected = joint_necessities(**common, carbon_u=D(0), oxygen_u=D(0))
    allowed = joint_necessities(**common, carbon_u=D(5), oxygen_u=D(0))
    assert not rejected.finite_release_can_meet_joint_targets
    assert allowed.finite_release_can_meet_joint_targets
    actual = common_release_response(carbon_v=D(6), carbon_u=D(5), oxygen_u=D(0), release_multiplier=D(20))
    assert actual.turnover_multiplier * common['parent_turnover'] >= common['target_turnover']
    assert actual.specificity_multiplier * common['parent_specificity'] >= common['target_specificity']


def test_limit_equality_is_not_finite_target_support():
    result = joint_necessities(parent_turnover=D(1), parent_specificity=D(1), target_turnover=D(2),
                               target_specificity=D(1), carbon_v=D(1), carbon_u=D(0), oxygen_u=D(0))
    assert not result.finite_release_can_meet_joint_targets
    assert result.reason_codes == ('TURNOVER_GAIN_UNREACHABLE_AT_FINITE_RELEASE',)


def test_specificity_headroom_can_admit_acceleration_before_decreasing_limit():
    result = joint_necessities(parent_turnover=D(1), parent_specificity=D(2), target_turnover=D('1.1'),
                               target_specificity=D(1), carbon_v=D(4), carbon_u=D(0), oxygen_u=D(3))
    assert result.finite_release_can_meet_joint_targets
    faster = joint_necessities(parent_turnover=D(1), parent_specificity=D(2), target_turnover=D(4),
                               target_specificity=D(1), carbon_v=D(4), carbon_u=D(0), oxygen_u=D(3))
    assert not faster.finite_release_can_meet_joint_targets


def test_invalid_latent_parameters_cannot_be_used_as_joint_support():
    with pytest.raises(ValueError):
        common_release_response(carbon_v=D(1), carbon_u=D(1), oxygen_u=D(0), release_multiplier=D(2))
    with pytest.raises(ValueError):
        BranchRates(D(1), D(1), D(1), D(-1), D(1))


@pytest.mark.parametrize('v,u', [('1', '0'), ('1', '.5'), ('4', '1'), ('10', '5')])
def test_latent_scenario_has_positive_rate_witness_without_fitting_microscopic_labels(v, u):
    rates = realize_conditional_branch(turnover=D('9.5'), catalytic_efficiency=D('.2'),
                                       formation_release_ratio=D(v), reverse_capture_ratio=D(u))
    actual = branch_observables(rates)
    assert float(actual.saturated_turnover_s_inv) == pytest.approx(9.5)
    assert float(actual.catalytic_efficiency_um_inv_s_inv) == pytest.approx(.2)
    assert float(actual.formation_release_ratio) == pytest.approx(float(v))
    assert float(actual.reverse_capture_ratio) == pytest.approx(float(u))


@pytest.mark.parametrize('gas_c,gas_o', [(1, 10), (.01, .1), (100, 3)])
def test_specificity_ratio_matches_independent_competing_branch_state_balance(gas_c, gas_o):
    carbon = BranchRates(D('.2'), D(2), D(3), D(5), D(7))
    oxygen = BranchRates(D('.003'), D(4), D(1), D(2), D(8))
    # X is shared by both branches. The independent five-state solve includes
    # competition instead of treating separately normalized occupancies as one.
    kc, ko = float(carbon.association_um_inv_s_inv) * gas_c, float(oxygen.association_um_inv_s_inv) * gas_o
    matrix = np.array([
        [-(kc + ko), 2, 7, 4, 8],
        [kc, -5, 5, 0, 0],
        [0, 3, -12, 0, 0],
        [ko, 0, 0, -5, 2],
        [1, 1, 1, 1, 1],
    ], dtype=float)
    occupancy = np.linalg.solve(matrix, np.array([0, 0, 0, 0, 1], dtype=float))
    assert min(occupancy) >= -1e-14
    specificity_from_flux = (7 * occupancy[2]) / (8 * occupancy[4]) * gas_o / gas_c
    derived = (branch_observables(carbon).catalytic_efficiency_um_inv_s_inv
               / branch_observables(oxygen).catalytic_efficiency_um_inv_s_inv)
    assert specificity_from_flux == pytest.approx(float(derived), rel=1e-12)
