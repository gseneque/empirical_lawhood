# SPDX-License-Identifier: MPL-2.0
"""Independent paired-table and completion oracles; no scientific source claim."""
from dataclasses import replace
from decimal import Decimal as D
from fractions import Fraction
from functools import cache
from itertools import product
from math import comb

import pytest
from scipy.stats import beta, binomtest

from empirical_lawhood.adapters.methods.matrix_experimental_programme import paired_adequacy as owner
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.planning.paired_power import paired_binary_power


def compare(rows):
    return owner.paired_adequacy(tuple('test.pair.%03d' % i for i in range(len(rows))),
        tuple(row[0] for row in rows), tuple(row[1] for row in rows))


@pytest.mark.parametrize('gains,significant', ((7, False), (8, True)))
def test_conf80_exact_discordance_boundary_and_practical_point_estimate(gains, significant):
    result = compare(((True, False),) * gains + ((False, False),) * (80 - gains))
    expected = Fraction(1, 2**gains)
    assert result.conservative.tail_probability == expected
    assert float(expected) == binomtest(gains, gains, .5, alternative='greater').pvalue
    assert result.significant is significant and result.practically_meaningful is significant
    assert result.conservative.net_gain == Fraction(gains, 80)
    assert result.observed == result.conservative == result.optimistic
    assert result.observed.absolute_gain_interval == result.absolute_gain_interval
    assert decode_canonical_bytes(result.canonical_bytes(), type(result), maximum_bytes=None) == result


def test_no_discordance_and_all_unknown_keep_distinct_observed_and_completed_tables():
    equal = compare(((True, True), (False, False)) * 40)
    assert equal.conservative.tail_probability == 1 and not equal.significant
    unknown = compare(((None, None),) * 80)
    assert unknown.observed.unit_count == 0 and unknown.observed.absolute_gain_interval == (None, None)
    assert unknown.conservative.harms == unknown.optimistic.gains == 80
    assert unknown.absolute_gain_interval == (D(-1), D(1)) and len(unknown.unknown_group_ids) == 80
    assert not unknown.observed_harm_ids and not unknown.observed_gain_ids
    assert unknown.conservative.net_gain == -1 and not unknown.criterion_met


@cache
def literal_interval(n, gain, harm):
    def interval(successes):
        return (0. if not successes else float(beta.ppf(1 / 80, successes, n - successes + 1)),
            1. if successes == n else float(beta.isf(1 / 80, successes + 1, n - successes)))
    lo, hi = interval(gain)
    lh, uh = interval(harm)
    return lo - uh, hi - lh


def test_interval_envelope_matches_every_feasible_completion_of729_partly_known_tables():
    for rows in product(tuple(product((False, True, None), repeat=2)), repeat=3):
        result = compare(rows)
        completions = product(*(tuple(product((False, True) if prepared is None else (prepared,),
            (False, True) if baseline is None else (baseline,))) for prepared, baseline in rows))
        intervals = tuple(literal_interval(3, sum(p and not b for p, b in values),
            sum(b and not p for p, b in values)) for values in completions)
        expected = min(lo for lo, _ in intervals), max(hi for _, hi in intervals)
        assert tuple(float(value) for value in result.absolute_gain_interval) == pytest.approx(expected, abs=1e-15)
        assert result.outcomes == rows


def test_partly_known_outcomes_are_preserved_in_worst_case_and_not_reported_as_observed_harms():
    rows = ((True, None), (False, None), (None, True), (None, False), (True, False), (False, True))
    result = compare(rows)
    assert (result.observed.gains, result.observed.harms, result.observed.unit_count) == (1, 1, 2)
    assert (result.conservative.gains, result.conservative.harms) == (1, 3)
    assert (result.optimistic.gains, result.optimistic.harms) == (3, 1)
    assert result.observed_gain_ids == ('test.pair.004',) and result.observed_harm_ids == ('test.pair.005',)
    assert result.conservative.net_gain == Fraction(-1, 3)
    with pytest.raises(ValueError, match='observed cells'):
        replace(result, conservative=result.observed)
    with pytest.raises(ValueError, match='interval'):
        replace(result, absolute_gain_interval=(D(0), D(1)))
    with pytest.raises(ValueError, match='binary/unknown'):
        replace(result, outcomes=((1, None), *rows[1:]))
    with pytest.raises(ValueError, match='independent group'):
        replace(result, group_ids=(result.group_ids[1], *result.group_ids[1:]))


def test_conf80_planning_power_matches_exact_multinomial_enumeration():
    n = 80
    accepted = tuple((g, h) for g in range(n + 1) for h in range(n - g + 1)
        if g + h and sum(comb(g + h, k) for k in range(g, g + h + 1)) * 160 <= 2**(g + h))
    assert min(g - h for g, h in accepted) == 8
    for gain, harm, published in ((6, 1, .920251201), (4, 1, .518865666), (3, 1, .219688486), (4, 2, .139199889)):
        exact = Fraction(sum(comb(n, g) * comb(n - g, h) * gain**g * harm**h * (20 - gain - harm)**(n - g - h)
            for g, h in accepted), 20**n)
        actual = paired_binary_power(n, (gain - harm) / 20, (gain + harm) / 20, 1 / 160, .1)
        assert actual == pytest.approx(float(exact), abs=1e-13)
        assert actual == pytest.approx(published, abs=5e-10)
