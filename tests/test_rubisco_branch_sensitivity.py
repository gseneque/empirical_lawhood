# SPDX-License-Identifier: MPL-2.0
"""Synthetic analytic oracles; these tests produce no mutant kinetics."""

from dataclasses import FrozenInstanceError, replace
from decimal import Decimal, localcontext
import math
from pathlib import Path
import subprocess
import sys

import pytest

from empirical_lawhood.adapters.physical.rubisco_kinetics import branch_sensitivity as b


def hypothetical(**changes):
    values = dict(
        carbon_acceleration=3.0, initial_dg_kcal_mol=12.0, dg_shift_kcal_mol=-3.0,
        reorganization_kcal_mol=55.0, rt_kcal_mol=0.6, productive_step_time_fraction=0.4,
    )
    values.update(changes)
    return b.BranchHypothesisV1(**values)


def decimal_barrier_difference(dg, shift, lam):
    with localcontext() as context:
        context.prec = 80
        g, d, l = (Decimal(str(x)) for x in (dg, shift, lam))
        return float(((l + g + d) ** 2 - (l + g) ** 2) / (4 * l))


@pytest.mark.parametrize("dg,shift,lam", [
    (12, -3, 55), (0, 2, 8), (-8, 3, 8), (-12, -2, 8), (-12, 9, 8),
    (12, 1e-14, 55), (12, 0, 55),
])
def test_factorized_barrier_matches_independent_high_precision_raw_difference(dg, shift, lam):
    result = b.evaluate_branch_hypothesis(hypothetical(
        initial_dg_kcal_mol=dg, dg_shift_kcal_mol=shift, reorganization_kcal_mol=lam,
    ))
    assert result.barrier_shift_kcal_mol == pytest.approx(
        decimal_barrier_difference(dg, shift, lam), rel=3e-15, abs=0,
    )


def test_small_shift_survives_cancellation_in_raw_float_barriers():
    result = b.evaluate_branch_hypothesis(hypothetical(dg_shift_kcal_mol=1e-16))
    assert result.final_barrier_kcal_mol == result.initial_barrier_kcal_mol
    assert result.barrier_shift_kcal_mol > 0


def test_inverted_endpoint_survives_cancellation_near_zero():
    hypothesis = hypothetical(initial_dg_kcal_mol=-100, carbon_acceleration=1.0000000000000002)
    endpoint = b.specificity_preserving_shifts(hypothesis).all_branch_intervals[0].upper_kcal_mol
    with localcontext() as context:
        context.prec = 80
        a, lam, rt = Decimal(-45), Decimal(55), Decimal("0.6")
        # Decimal.from_float admits the exact declared binary rate ratio.
        compensation = 4 * lam * rt * Decimal.from_float(hypothesis.carbon_acceleration).ln()
        independent = -a - (a * a - compensation).sqrt()
    assert endpoint > 0
    assert endpoint == pytest.approx(float(independent), rel=3e-15, abs=0)


@pytest.mark.parametrize("dg,shift,initial,final", [
    (0, 1, "NORMAL", "NORMAL"), (-8, 0, "ACTIVATIONLESS", "ACTIVATIONLESS"),
    (-8, 1, "ACTIVATIONLESS", "NORMAL"), (-8, -1, "ACTIVATIONLESS", "INVERTED"),
    (-12, 1, "INVERTED", "INVERTED"), (-12, 6, "INVERTED", "NORMAL"),
])
def test_branch_census_includes_activationless_and_inverted_region(dg, shift, initial, final):
    result = b.evaluate_branch_hypothesis(hypothetical(
        initial_dg_kcal_mol=dg, dg_shift_kcal_mol=shift, reorganization_kcal_mol=8,
    ))
    assert (result.initial_branch, result.final_branch) == (initial, final)


def test_identity_and_information_role_are_explicit_and_immutable():
    result = b.evaluate_branch_hypothesis(hypothetical(carbon_acceleration=1, dg_shift_kcal_mol=0))
    assert result.barrier_shift_kcal_mol == result.log_oxygen_acceleration == 0
    assert result.log_carbon_acceleration == result.log_specificity_ratio == result.log_turnover_ratio == 0
    assert result.role == result.hypothesis.role == result.specificity_preserving_shifts.role == b.ROLE
    with pytest.raises(FrozenInstanceError):
        result.log_specificity_ratio = 1


@pytest.mark.parametrize("fraction", [0, 0.2, 0.8, 1])
def test_serial_turnover_matches_independent_time_accounting(fraction):
    result = b.evaluate_branch_hypothesis(hypothetical(productive_step_time_fraction=fraction))
    assert result.log_turnover_ratio == pytest.approx(-math.log(1 - fraction + fraction / 3))
    if fraction == 0:
        assert result.log_turnover_ratio == 0
    if fraction == 1:
        assert result.log_turnover_ratio == math.log(3)


def test_log_outputs_allow_tiny_carbon_rate_without_reciprocal_overflow():
    result = b.evaluate_branch_hypothesis(hypothetical(
        carbon_acceleration=1e-320, productive_step_time_fraction=0.5,
    ))
    assert math.isfinite(result.log_turnover_ratio)
    assert result.log_turnover_ratio == pytest.approx(math.log(1e-320) - math.log(0.5))


@pytest.mark.parametrize("fraction", [1e-300, 0.1, 0.9, 1])
def test_identity_is_exact_for_all_serial_time_fractions(fraction):
    result = b.evaluate_branch_hypothesis(hypothetical(
        carbon_acceleration=1, dg_shift_kcal_mol=0, productive_step_time_fraction=fraction,
    ))
    assert result.log_turnover_ratio == 0


def test_carbon_gain_need_not_compensate_oxygen_gain_or_accelerate_full_turnover():
    result = b.evaluate_branch_hypothesis(hypothetical(productive_step_time_fraction=0))
    assert result.log_carbon_acceleration > 0
    assert result.log_oxygen_acceleration > result.log_carbon_acceleration
    assert result.log_specificity_ratio < 0
    assert result.log_turnover_ratio == 0


@pytest.mark.parametrize("dg,carbon", [(0, 3), (-12, 3), (-8, 1), (-8, 0.5), (-8, 3)])
def test_complete_interval_set_matches_direct_inequality_on_both_branches(dg, carbon):
    hypothesis = hypothetical(initial_dg_kcal_mol=dg, carbon_acceleration=carbon, reorganization_kcal_mol=8)
    envelope = b.specificity_preserving_shifts(hypothesis)
    for shift in range(-40, 41):
        delta = decimal_barrier_difference(dg, shift, 8)
        expected = delta >= -hypothesis.rt_kcal_mol * math.log(carbon)
        actual = any(interval.contains(shift) for interval in envelope.all_branch_intervals)
        assert actual == expected, (dg, carbon, shift)
        normal_expected = expected and dg + shift >= -8
        assert envelope.normal_branch_interval.contains(shift) == normal_expected
        subset = envelope.normal_branch_nonpositive_interval
        assert (subset is not None and subset.contains(shift)) == (normal_expected and shift <= 0)


def test_discriminant_zero_negative_and_impossible_nonpositive_subset():
    zero = b.specificity_preserving_shifts(hypothetical(
        initial_dg_kcal_mol=-8, reorganization_kcal_mol=8, carbon_acceleration=1,
    ))
    assert zero.quadratic_case == "ZERO_ALL_REAL"
    assert zero.normal_branch_nonpositive_interval == b.ClosedShiftIntervalV1(0, 0)
    negative = b.specificity_preserving_shifts(hypothetical(
        initial_dg_kcal_mol=-8, reorganization_kcal_mol=8, carbon_acceleration=3,
    ))
    assert negative.quadratic_case == "NEGATIVE_ALL_REAL"
    slowdown = b.specificity_preserving_shifts(hypothetical(carbon_acceleration=0.5))
    assert slowdown.normal_branch_nonpositive_interval is None
    assert len(slowdown.all_branch_intervals) == 2


def test_two_ray_endpoints_saturate_specificity_and_retain_inverted_solution():
    hypothesis = hypothetical()
    envelope = b.specificity_preserving_shifts(hypothesis)
    left, right = envelope.all_branch_intervals
    assert left.lower_kcal_mol is None and right.upper_kcal_mol is None
    for endpoint in (left.upper_kcal_mol, right.lower_kcal_mol):
        result = b.evaluate_branch_hypothesis(replace(hypothesis, dg_shift_kcal_mol=endpoint))
        assert result.log_specificity_ratio == pytest.approx(0, abs=5e-14)
    assert b.evaluate_branch_hypothesis(replace(
        hypothesis, dg_shift_kcal_mol=left.upper_kcal_mol - 1,
    )).final_branch == "INVERTED"


@pytest.mark.parametrize("name,bad", [
    ("carbon_acceleration", 0), ("carbon_acceleration", -1),
    ("reorganization_kcal_mol", 0), ("rt_kcal_mol", -1),
    ("productive_step_time_fraction", -0.1), ("productive_step_time_fraction", 1.1),
    ("initial_dg_kcal_mol", float("nan")), ("dg_shift_kcal_mol", float("inf")),
    ("rt_kcal_mol", True), ("carbon_acceleration", False),
    ("productive_step_time_fraction", True), ("initial_dg_kcal_mol", "12"),
    ("reorganization_kcal_mol", 1e101), ("initial_dg_kcal_mol", 10**400),
])
def test_refuses_invalid_or_unbounded_operands(name, bad):
    with pytest.raises(ValueError):
        hypothetical(**{name: bad})


def test_refuses_unrepresentable_derived_results_and_undeclared_inputs():
    with pytest.raises(ValueError):
        b.evaluate_branch_hypothesis(hypothetical(reorganization_kcal_mol=1e-320))
    with pytest.raises(ValueError):
        b.evaluate_branch_hypothesis(hypothetical(rt_kcal_mol=1e-320))
    with pytest.raises(ValueError):
        b.evaluate_branch_hypothesis({})
    with pytest.raises(ValueError):
        b.specificity_preserving_shifts(None)
    with pytest.raises(ValueError):
        b.ClosedShiftIntervalV1(None, None).contains(True)


def test_refuses_underflow_that_would_erase_nonzero_quadratic_or_barrier_terms():
    tiny = hypothetical(
        initial_dg_kcal_mol=0, dg_shift_kcal_mol=0,
        reorganization_kcal_mol=1e-200, rt_kcal_mol=1e-200,
    )
    with pytest.raises(ValueError, match="underflow"):
        b.specificity_preserving_shifts(tiny)
    with pytest.raises(ValueError, match="underflow"):
        b.evaluate_branch_hypothesis(tiny)


@pytest.mark.parametrize("lower,upper", [
    (float("nan"), None), (None, float("inf")), (True, 1), (0, "1"),
    (2, 1), (10**400, None),
])
def test_interval_constructor_refuses_invalid_or_reversed_endpoints(lower, upper):
    with pytest.raises(ValueError):
        b.ClosedShiftIntervalV1(lower, upper)


def test_import_is_cold_in_fresh_process():
    script = """
import importlib.abc, sys
class Refuse(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'numpy', 'scipy', 'pyscf', 'h5py'}:
            raise AssertionError('native import during arithmetic discovery: ' + fullname)
sys.meta_path.insert(0, Refuse())
import empirical_lawhood.adapters.physical.rubisco_kinetics.branch_sensitivity
"""
    result = subprocess.run(
        [sys.executable, "-B", "-c", script], cwd=Path(__file__).parent.parent,
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr
