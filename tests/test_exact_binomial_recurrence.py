# SPDX-License-Identifier: MPL-2.0
"""Independent combinatorial tails and acceptance-boundary differentials."""

from decimal import Decimal, localcontext
from fractions import Fraction
from math import comb

import pytest

from empirical_lawhood.methods.statistics.experimental_statistics import binomial_minimum_successes, binomial_upper_tail


@pytest.mark.parametrize('count', (1, 2, 7, 16, 31, 64))
@pytest.mark.parametrize('probability', (Fraction(0), Fraction(1), Fraction(1, 2), Fraction(1, 3),
    Fraction(9, 10), Decimal('0.12345678901234567890123456789')))
@pytest.mark.numerical(oracle='Exact rational sums of math.comb binomial masses, including every acceptance boundary')
def test_exact_recurrence_matches_combinatorial_tails_at_and_around_every_boundary(count, probability):
    p = Fraction(probability)
    masses = tuple(Fraction(comb(count, k)) * p**k * (1-p)**(count-k) for k in range(count + 1))
    tails = tuple(sum(masses[k:], Fraction(0)) for k in range(count + 2))
    assert tails[0] == 1 and tails[-1] == 0
    alphas = {Fraction(1, 240), Fraction(1, 20), Fraction(1, 2)}
    for value in tails:
        if 0 < value < 1:
            step = min(value, 1-value) / 3
            alphas.update((value-step, value, value+step))
    with localcontext() as context:
        context.prec = 5
        assert tuple(binomial_upper_tail(count, k, probability) for k in range(count + 2)) == tails
        for alpha in sorted(alphas):
            expected = next(k for k, tail in enumerate(tails) if tail <= alpha)
            assert binomial_minimum_successes(count, probability, alpha) == expected


@pytest.mark.numerical(oracle='Independent integer binomial sum at n=512 and unattainable rational tail')
def test_large_denominator_and_unattainable_threshold_remain_exact():
    n, p = 512, Fraction(1, 2)
    expected = Fraction(sum(comb(n, k) for k in range(287, n + 1)), 2**n)
    assert binomial_upper_tail(n, 287, p) == expected
    assert binomial_minimum_successes(n, p, expected) == 287
    assert binomial_minimum_successes(n, p, Fraction(1, 2**513)) == 513
