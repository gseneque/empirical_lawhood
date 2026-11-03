# SPDX-License-Identifier: MPL-2.0
"""Exact event arithmetic; these synthetic labels supply no sampling authority."""

from dataclasses import replace
from fractions import Fraction
from math import comb
from types import SimpleNamespace

import pytest
from scipy.stats import binom

from empirical_lawhood.runtime.experimental_statistics import assigned_binomial_inference
from empirical_lawhood.adapters.methods.matrix_factor_response import native_utility_records as r
from empirical_lawhood.adapters.methods.matrix_factor_response.native_utility_science import amended_primary_report


@pytest.mark.parametrize('n,p,critical', ((96, Fraction(4, 5), 87), (96, Fraction(1, 2), 61),
    (80, Fraction(1, 2), 52), (32, Fraction(1, 2), 24), (64, Fraction(1, 2), 43)))
def test_complete_assigned_tests_match_independent_binomial_boundaries(n, p, critical):
    units = tuple('exposed.unit.' + str(index).zfill(3) for index in range(n))
    result = assigned_binomial_inference(units, (True,) * critical + (None,) * (n - critical),
        null_probability=p, alpha=Fraction(1, 160))
    assert result.critical_successes == critical and result.criterion_met
    assert result.successes == critical and result.failures == 0 and result.unknowns == n - critical
    assert binom.sf(critical - 1, n, float(p)) <= 1 / 160 < binom.sf(critical - 2, n, float(p))
    assert float(Fraction(result.tail_numerator, result.tail_denominator)) == pytest.approx(binom.sf(critical - 1, n, float(p)), rel=1e-12)
    assert result.descriptive_interval.risk_count_lower == result.descriptive_interval.risk_count_upper == n
    assert result.descriptive_interval.upper == 1
    with pytest.raises(ValueError):
        replace(result, events=(True,) * (critical - 1) + (None,) * (n - critical + 1))


@pytest.mark.parametrize('n,critical,p,expected', (
    (80, 52, Fraction(7, 10), .863314181683), (96, 61, Fraction(7, 10), .930132173927),
    (32, 24, Fraction(4, 5), .825395312268), (32, 24, Fraction(7, 10), .343979059915),
    (96, 87, Fraction(19, 20), .978072357396), (96, 87, Fraction(9, 10), .504785294624),
    (64, 43, Fraction(7, 10), .738273005289)))
def test_declared_planning_power_matches_literal_rational_probability_law(n, critical, p, expected):
    power = sum(Fraction(comb(n, successes)) * p**successes * (1-p)**(n-successes)
        for successes in range(critical, n+1))
    assert float(power) == pytest.approx(expected, abs=5e-13)
    assert float(power) == pytest.approx(binom.sf(critical-1, n, float(p)), abs=1e-14)


def test_amended_e2_keeps_both_questions_and_all_missing_whole_roots():
    # Minimal mathematical event operands, deliberately without source/custody.
    rows = tuple(SimpleNamespace(unit_id='exposed.unit.' + str(index).zfill(3),
        amended=r.NativeUtilityAmendedEndpoints(index < 87, index < 61, False)) for index in range(90))
    missing = tuple('exposed.unit.' + str(index).zfill(3) for index in range(90, 96))
    result = r.amended_utility_inference(rows, missing)
    assert result.adequacy.criterion_met and result.structural_advantage.criterion_met
    assert result.adequacy.unknowns == result.structural_advantage.unknowns == 6
    assert result.adequacy.failures == 3 and result.structural_advantage.failures == 29
    report = amended_primary_report(result)
    assert report['paired-factor-adequacy-through32']['critical_successes'] == 87
    assert report['three-challenger-advantage-through128']['critical_successes'] == 61
    with pytest.raises(ValueError, match='assigned'):
        result.validate_outcomes(rows, missing[:-1])
    unknown = r.amended_utility_inference((), tuple('exposed.unit.' + str(i).zfill(3) for i in range(96)))
    assert not unknown.adequacy.criterion_met and unknown.adequacy.unknowns == 96
    assert unknown.adequacy.descriptive_interval.lower == 0 and unknown.adequacy.descriptive_interval.upper == 1


def test_amended_e2_does_not_select_a_single_favorable_challenger_or_zero_task():
    criterion = r.NativeAmendedUtilityCriterion('exposed.amended.e2')
    assert criterion.comparators == ('GENERIC_SLOW', 'IO48', 'SPECTRA')
    with pytest.raises(ValueError, match='conjunction'):
        replace(criterion, comparators=('GENERIC_SLOW',))
    with pytest.raises(ValueError, match='tolerance'):
        replace(criterion, improvement_margin=criterion.improvement_margin * 2)
    partial = r.NativeUtilityAmendedEndpoints(True, None, False)
    assert partial.joint_adequacy_advantage is None and partial.factor_adequate_zero_inadequate
    quiet = r.NativeUtilityAmendedEndpoints(True, True, True)
    assert quiet.joint_adequacy_advantage and not quiet.factor_adequate_zero_inadequate
