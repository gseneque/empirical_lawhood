# SPDX-License-Identifier: MPL-2.0
"""Independent tail equations and exhaustive small completion oracles."""

from dataclasses import replace
from decimal import Decimal, localcontext
from fractions import Fraction
from itertools import combinations, product

import pytest
from scipy.stats import binom

from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.runtime.experimental_statistics import (
    BINOMIAL_COMPLETION_STATES, binomial_probability_interval, incomplete_binomial_interval,
)


TAIL = Fraction(1, 2560)


def interval(n, s):
    return binomial_probability_interval(n, s, tail_probability=TAIL)


def envelope(states):
    return incomplete_binomial_interval(tuple('unit.' + str(index) for index in range(len(states))),
        tuple(states), tail_probability=TAIL)


@pytest.mark.parametrize('n,s', ((1, 0), (1, 1), (5, 2), (32, 16), (96, 0), (96, 48), (96, 96)))
def test_quantiles_invert_independent_binomial_tail_equations(n, s):
    result = interval(n, s)
    if s:
        assert binom.sf(s - 1, n, float(result.lower)) == pytest.approx(float(TAIL), rel=1e-10)
    else:
        assert result.lower == 0
    if s < n:
        assert binom.cdf(s, n, float(result.upper)) == pytest.approx(float(TAIL), rel=1e-10)
    else:
        assert result.upper == 1
    assert (result.tail_numerator, result.tail_denominator) == (1, 2560)


def test_e1_midpoint_and_boundary_intervals_have_the_declared_simultaneous_scale():
    middle = interval(96, 48)
    assert float(middle.lower) == pytest.approx(.3291, abs=.00005)
    assert float(middle.upper) == pytest.approx(.6709, abs=.00005)
    with localcontext() as context:
        context.prec = 80
        expected_all = ((Decimal(1) / 2560).ln() / 96).exp()
    assert float(interval(96, 96).lower) == pytest.approx(float(expected_all), rel=1e-14)
    assert float(interval(96, 0).upper) == pytest.approx(float(1 - expected_all), rel=1e-14)


def test_known_risk_uses_full_n_for_unknown_outcome_envelope():
    result = envelope([('SUCCESS',)] * 3 + [('FAILURE',)] * 2 + [('FAILURE', 'SUCCESS')] * 5)
    assert (result.risk_count_lower, result.risk_count_upper) == (10, 10)
    assert (result.known_successes, result.known_failures, result.known_risk_unknown_outcomes) == (3, 2, 5)
    assert result.lower == interval(10, 3).lower and result.upper == interval(10, 8).upper
    assert result.complete_case == interval(5, 3)
    assert result.lower < result.complete_case.lower and result.upper > result.complete_case.upper


def test_unknown_eligibility_and_outcome_stay_in_the_population_envelope():
    result = envelope([('SUCCESS',), ('FAILURE',), ('FAILURE', 'INELIGIBLE', 'SUCCESS'), ('FAILURE', 'INELIGIBLE', 'SUCCESS')])
    assert result.unknown_eligibility == 2 and (result.risk_count_lower, result.risk_count_upper) == (2, 4)
    assert result.lower == interval(4, 1).lower and result.upper == interval(4, 3).upper
    assert result.complete_case == interval(2, 1)


def test_restricted_feasible_eligibility_does_not_invent_success_completions():
    result = envelope([('SUCCESS',), ('FAILURE',), ('FAILURE', 'INELIGIBLE')])
    assert result.lower == interval(3, 1).lower
    assert result.upper == interval(2, 1).upper
    unconstrained = envelope([('SUCCESS',), ('FAILURE',), ('FAILURE', 'INELIGIBLE', 'SUCCESS')])
    assert result.upper < unconstrained.upper


def test_dynamic_envelope_matches_exhaustive_completions_for_every_small_categorical_pair():
    options = tuple(tuple(values) for count in (1, 2, 3) for values in combinations(BINOMIAL_COMPLETION_STATES, count))
    for left, right in product(options, repeat=2):
        rows = (('SUCCESS',), left, right)
        result = envelope(rows)
        completions = tuple(interval(sum(value != 'INELIGIBLE' for value in values),
            sum(value == 'SUCCESS' for value in values)) for values in product(*rows))
        assert result.lower == min(value.lower for value in completions)
        assert result.upper == max(value.upper for value in completions)


@pytest.mark.parametrize('states,maximum', (
    ((('INELIGIBLE',),) * 4, 0),
    ((('FAILURE', 'INELIGIBLE', 'SUCCESS'),) * 4, 4),
    ((('INELIGIBLE',), ('INELIGIBLE', 'SUCCESS')), 1)))
def test_no_established_eligible_population_keeps_conditional_cell_undefined(states, maximum):
    result = envelope(states)
    assert result.risk_count_lower == 0 and result.risk_count_upper == maximum
    assert result.lower is None and result.upper is None
    assert result.complete_case.lower is None and result.complete_case.upper is None
    with pytest.raises(ValueError, match='conditional risk'):
        replace(result, lower=Decimal(0), upper=Decimal(1))


def test_whole_assigned_units_are_retained_and_nested_duplicates_refuse():
    result = envelope([('SUCCESS',), ('INELIGIBLE',), ('FAILURE', 'SUCCESS')])
    assert len(result.unit_ids) == 3 and result.risk_count_lower == 2
    for value in (result, result.complete_case):
        assert decode_canonical_bytes(value.canonical_bytes(), type(value), maximum_bytes=10000) == value
    with pytest.raises(ValueError, match='assigned-unit'):
        incomplete_binomial_interval(('unit.0', 'unit.0'), (('SUCCESS',), ('FAILURE',)), tail_probability=TAIL)
    with pytest.raises(ValueError, match='assigned-unit'):
        incomplete_binomial_interval(('unit.0', 'unit.1'), (('SUCCESS',),), tail_probability=TAIL)


@pytest.mark.parametrize('states', (((),), (('UNKNOWN',),), (('SUCCESS', 'FAILURE'),), (('SUCCESS', 'SUCCESS'),)))
def test_unknowns_require_explicit_valid_feasible_states(states):
    with pytest.raises(ValueError, match='assigned-unit'):
        envelope(states)


def test_zero_denominator_and_invalid_or_unrepresentable_probability_are_explicit():
    assert interval(0, 0).lower is None
    with pytest.raises(ValueError, match='exact counts'):
        binomial_probability_interval(1, 1, tail_probability=.05)
    with pytest.raises(ValueError, match='numerically unrepresentable'):
        binomial_probability_interval(96, 48, tail_probability=Fraction(1, 10 ** 1000))
    with pytest.raises(ValueError, match='zero-risk'):
        replace(interval(0, 0), lower=Decimal(0), upper=Decimal(1))
