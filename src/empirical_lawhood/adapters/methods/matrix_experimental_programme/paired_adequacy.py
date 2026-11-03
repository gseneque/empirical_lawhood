# SPDX-License-Identifier: MPL-2.0
"""Exact paired response-adequacy arithmetic over every assigned E5 group.

Known observations and statistical completions remain separate. This owner
receives binary adequacy outcomes, not native data or authority. The prepared
assessor authenticates the original paired subjects and sampled response rule.
"""
from dataclasses import dataclass
from decimal import Decimal, localcontext
from fractions import Fraction
from typing import ClassVar

from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.runtime.experimental_statistics import (
    BinomialProbabilityInterval, binomial_probability_interval, binomial_upper_tail,
)

PAIRED_ALPHA = Fraction(1, 160)
PRACTICAL_GAIN = Fraction(1, 10)
MARGINAL_TAIL = Fraction(1, 80)
CELLS = ('GAIN', 'HARM', 'BOTH_SUCCESS', 'BOTH_FAILURE')


def _cell(prepared, baseline):
    return ('BOTH_SUCCESS' if baseline else 'GAIN') if prepared else ('HARM' if baseline else 'BOTH_FAILURE')


@dataclass(frozen=True, slots=True)
class MatrixPairedAdequacyCounts(CanonicalRecord):
    """One complete paired table, with an exact test and descriptive interval."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-experimental-programme/paired-adequacy-counts'
    unit_count: int
    gains: int
    harms: int
    both_success: int
    both_failure: int
    tail_numerator: int
    tail_denominator: int
    gain_probability: BinomialProbabilityInterval
    harm_probability: BinomialProbabilityInterval

    def __post_init__(self):
        counts = (self.gains, self.harms, self.both_success, self.both_failure)
        if (type(self.unit_count) is not int or self.unit_count < 0
                or any(type(value) is not int or value < 0 for value in counts)
                or sum(counts) != self.unit_count
                or type(self.tail_numerator) is not int or type(self.tail_denominator) is not int
                or self.tail_denominator < 1):
            raise ValueError('paired adequacy changes the complete gain/harm/same-outcome table')
        tail = (binomial_upper_tail(self.gains + self.harms, self.gains, Fraction(1, 2))
            if self.gains + self.harms else Fraction(1))
        if (self.tail_numerator, self.tail_denominator) != (tail.numerator, tail.denominator):
            raise ValueError('paired adequacy changes its exact conditional discordance test')
        for interval, successes in ((self.gain_probability, self.gains), (self.harm_probability, self.harms)):
            if (type(interval) is not BinomialProbabilityInterval or interval !=
                    binomial_probability_interval(self.unit_count, successes, tail_probability=MARGINAL_TAIL)):
                raise ValueError('paired adequacy changes its descriptive97.5 marginal CP interval')

    @property
    def tail_probability(self):
        return Fraction(self.tail_numerator, self.tail_denominator)

    @property
    def net_gain(self):
        return Fraction(self.gains - self.harms, self.unit_count) if self.unit_count else None

    @property
    def absolute_gain_interval(self):
        if not self.unit_count:
            return None, None
        with localcontext() as context:
            context.prec = 80
            return (max(Decimal(-1), self.gain_probability.lower - self.harm_probability.upper),
                min(Decimal(1), self.gain_probability.upper - self.harm_probability.lower))


def _counts(outcomes):
    cells = tuple(_cell(*row) for row in outcomes)
    g, h, both, neither = (cells.count(name) for name in CELLS)
    tail = binomial_upper_tail(g + h, g, Fraction(1, 2)) if g + h else Fraction(1)
    return MatrixPairedAdequacyCounts(len(outcomes), g, h, both, neither, tail.numerator, tail.denominator,
        binomial_probability_interval(len(outcomes), g, tail_probability=MARGINAL_TAIL),
        binomial_probability_interval(len(outcomes), h, tail_probability=MARGINAL_TAIL))


def _completion(outcomes, *, optimistic):
    # These are statistical assignments. Original outcomes are never replaced.
    return tuple((optimistic if prepared is None else prepared,
        not optimistic if baseline is None else baseline) for prepared, baseline in outcomes)


@dataclass(frozen=True, slots=True)
class MatrixPairedAdequacy(CanonicalRecord):
    """Known pairs, both extreme completions, and the full assigned denominator."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-experimental-programme/paired-adequacy'
    group_ids: tuple[str, ...]
    outcomes: tuple[tuple[bool | None, bool | None], ...]
    observed: MatrixPairedAdequacyCounts
    conservative: MatrixPairedAdequacyCounts
    optimistic: MatrixPairedAdequacyCounts
    unknown_group_ids: tuple[str, ...]
    absolute_gain_interval: tuple[Decimal, Decimal]
    significant: bool
    practically_meaningful: bool
    interpretation: str = 'SAMPLED_RESPONSE_ADEQUACY_NOT_IDENTICAL_PHYSICAL_TASK_OR_EXTERNAL_SERVICE'

    def __post_init__(self):
        if (type(self.group_ids) is not tuple or not self.group_ids
                or self.group_ids != tuple(sorted(set(self.group_ids)))
                or type(self.outcomes) is not tuple or len(self.outcomes) != len(self.group_ids)
                or any(type(row) is not tuple or len(row) != 2
                    or any(value is not None and type(value) is not bool for value in row) for row in self.outcomes)
                or self.interpretation != 'SAMPLED_RESPONSE_ADEQUACY_NOT_IDENTICAL_PHYSICAL_TASK_OR_EXTERNAL_SERVICE'):
            raise ValueError('paired adequacy requires every assigned independent group and original binary/unknown outcomes')
        for group in self.group_ids:
            validate_stable_id(group)
        observed = tuple(row for row in self.outcomes if None not in row)
        unknown = tuple(group for group, row in zip(self.group_ids, self.outcomes, strict=True) if None in row)
        for actual, values in ((self.observed, observed),
                (self.conservative, _completion(self.outcomes, optimistic=False)),
                (self.optimistic, _completion(self.outcomes, optimistic=True))):
            if type(actual) is not MatrixPairedAdequacyCounts or actual != _counts(values):
                raise ValueError('paired adequacy substitutes observed cells or its declared worst/best completion')
        bounds = self.conservative.absolute_gain_interval[0], self.optimistic.absolute_gain_interval[1]
        if (self.unknown_group_ids != unknown or type(self.absolute_gain_interval) is not tuple
                or self.absolute_gain_interval != bounds
                or any(type(value) is not Decimal for value in self.absolute_gain_interval)
                or type(self.significant) is not bool or type(self.practically_meaningful) is not bool
                or self.significant != (self.conservative.tail_probability <= PAIRED_ALPHA)
                or self.practically_meaningful != (self.conservative.net_gain >= PRACTICAL_GAIN)):
            raise ValueError('paired adequacy changes the feasible-completion interval or exact/practical decisions')

    @property
    def observed_gain_ids(self):
        return tuple(group for group, row in zip(self.group_ids, self.outcomes, strict=True) if row == (True, False))

    @property
    def observed_harm_ids(self):
        return tuple(group for group, row in zip(self.group_ids, self.outcomes, strict=True) if row == (False, True))

    @property
    def criterion_met(self):
        return self.significant and self.practically_meaningful


def paired_adequacy(group_ids, prepared, baseline):
    """No complete-pair deletion in the primary test or practical estimate.

    The CP difference is monotone in the gain and harm counts. The adverse
    completion jointly minimizes gains and maximizes harms; the opposite
    completion attains the other endpoint. Their interval envelope therefore
    covers every feasible completion, including partly known pairs.
    """
    if (type(group_ids) is not tuple or type(prepared) is not tuple or type(baseline) is not tuple
            or not group_ids or len(prepared) != len(group_ids) or len(baseline) != len(group_ids)
            or any(value is not None and type(value) is not bool for value in (*prepared, *baseline))):
        raise ValueError('paired adequacy requires exact complete assigned outcome tuples')
    outcomes = tuple(zip(prepared, baseline, strict=True))
    observed = _counts(tuple(row for row in outcomes if None not in row))
    conservative = _counts(_completion(outcomes, optimistic=False))
    optimistic = _counts(_completion(outcomes, optimistic=True))
    return MatrixPairedAdequacy(group_ids, outcomes, observed, conservative, optimistic,
        tuple(group for group, row in zip(group_ids, outcomes, strict=True) if None in row),
        (conservative.absolute_gain_interval[0], optimistic.absolute_gain_interval[1]),
        conservative.tail_probability <= PAIRED_ALPHA, conservative.net_gain >= PRACTICAL_GAIN)
