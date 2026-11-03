# SPDX-License-Identifier: MPL-2.0
"""Reusable exact reductions; sampling and applicability require domain evidence."""

from dataclasses import dataclass
from decimal import Decimal, DecimalException, localcontext
from enum import StrEnum
from fractions import Fraction
from math import comb, isfinite

from empirical_lawhood.kernel.serialization import CanonicalRecord
from typing import ClassVar


class PairedMeanTAlternative(StrEnum):
    TWO_SIDED_POINT_NULL = "TWO_SIDED_POINT_NULL"
    GREATER = "GREATER"
    LESS = "LESS"


class PairedMeanTDisposition(StrEnum):
    CONDITIONAL_NUMERIC_RESULT = "CONDITIONAL_NUMERIC_RESULT"
    UNEVALUABLE = "UNEVALUABLE"


@dataclass(frozen=True, slots=True)
class PairedMeanTResult:
    """Complete assigned-unit accounting, without a sampling-assumption warrant."""

    group_ids: tuple[str, ...]
    values: tuple[Decimal | Fraction | None, ...]
    null_value: Fraction
    alternative: PairedMeanTAlternative
    finite_count: int
    missing_group_ids: tuple[str, ...]
    nonfinite_group_ids: tuple[str, ...]
    mean: Fraction | None
    sample_variance: Fraction | None
    degrees_of_freedom: int
    statistic: Decimal | None
    p_value: Decimal | None
    disposition: PairedMeanTDisposition
    reason_codes: tuple[str, ...]

    @property
    def assigned_count(self) -> int:
        return len(self.group_ids)


def paired_mean_t(group_ids: tuple[str, ...], values: tuple[Decimal | Fraction | None, ...], *,
                  null_value: Decimal | Fraction, alternative: PairedMeanTAlternative) -> PairedMeanTResult:
    """Conditional Student mean test of whole-group differences, never nested rows.

    Valid inference additionally requires independent common-normal whole-group
    differences with a common mean and variance, a suitable predeclared endpoint
    and null/margin, and genuine scientific evidence for that scope. This pure
    calculation neither establishes those assumptions nor grants authority.
    TWO_SIDED_POINT_NULL tests equality to the supplied null; it does not test
    practical equivalence or prove an absolute effect exceeds a practical margin.

    Every assigned group is retained. Any missing/nonfinite value prevents all
    finite-only moments and inference. Moments use exact Fraction arithmetic;
    SciPy's Student sf/cdf supplies the explicitly numerical probability only.
    A zero variance or a numerically unrepresentable/underflowed result is
    UNEVALUABLE, including a tail rounded to zero for a finite statistic.
    """
    from empirical_lawhood.kernel.serialization import validate_stable_id

    if (type(group_ids) is not tuple or not group_ids or any(type(value) is not str for value in group_ids)
            or len(set(group_ids)) != len(group_ids) or type(values) is not tuple or len(values) != len(group_ids)):
        raise ValueError("paired mean test needs its complete unique aligned whole-group census")
    for group_id in group_ids:
        validate_stable_id(group_id)
    if (any(value is not None and type(value) not in (Decimal, Fraction) for value in values)
            or type(null_value) not in (Decimal, Fraction) or type(alternative) is not PairedMeanTAlternative):
        raise TypeError("paired mean test requires exact Decimal/Fraction operands and an explicit alternative")
    if type(null_value) is Decimal and not null_value.is_finite():
        raise ValueError("paired mean test null/margin must be finite")
    null = Fraction(null_value)
    missing = tuple(name for name, value in zip(group_ids, values, strict=True) if value is None)
    nonfinite = tuple(name for name, value in zip(group_ids, values, strict=True)
        if type(value) is Decimal and not value.is_finite())
    finite = len(values)-len(missing)-len(nonfinite)
    reasons = []
    if missing:
        reasons.append("MISSING_ASSIGNED_GROUP")
    if nonfinite:
        reasons.append("NONFINITE_ASSIGNED_GROUP")
    mean = variance = statistic = probability = None
    if not reasons:
        exact = tuple(Fraction(value) for value in values)
        mean = sum(exact, Fraction(0))/len(exact)
        if len(exact) < 2:
            reasons.append("INSUFFICIENT_ASSIGNED_GROUPS")
        else:
            variance = sum(((value-mean)**2 for value in exact), Fraction(0))/(len(exact)-1)
            if variance == 0:
                reasons.append("ZERO_SAMPLE_VARIANCE")
            else:
                from scipy.stats import t

                difference = mean-null
                try:
                    # Compute the ratio before binary conversion so a small
                    # variance alone does not spuriously underflow to zero.
                    squared = difference*difference*len(exact)/variance
                    with localcontext() as context:
                        context.prec = 80
                        magnitude = (Decimal(squared.numerator)/Decimal(squared.denominator)).sqrt()
                    numerical_t = float(magnitude) * (-1 if difference < 0 else 1)
                    if not isfinite(numerical_t) or difference != 0 and numerical_t == 0:
                        raise ValueError("unrepresentable Student statistic")
                    df = len(exact)-1
                    if alternative is PairedMeanTAlternative.TWO_SIDED_POINT_NULL:
                        p = 2*float(t.sf(abs(numerical_t), df))
                    elif alternative is PairedMeanTAlternative.GREATER:
                        p = float(t.sf(numerical_t, df))
                    else:
                        p = float(t.cdf(numerical_t, df))
                    if not isfinite(p) or not 0 < p <= 1:
                        raise ValueError("unrepresentable Student probability")
                    statistic, probability = Decimal(str(numerical_t)), Decimal(str(p))
                except (DecimalException, OverflowError, ValueError, ZeroDivisionError):
                    reasons.append("NUMERICALLY_UNEVALUABLE_STUDENT_TAIL")
    return PairedMeanTResult(group_ids, values, null, alternative, finite, missing, nonfinite,
        mean, variance, len(values)-1, statistic, probability,
        PairedMeanTDisposition.UNEVALUABLE if reasons else PairedMeanTDisposition.CONDITIONAL_NUMERIC_RESULT,
        tuple(sorted(reasons)))


def _probability(value: Fraction | Decimal, *, endpoints: bool = False) -> Fraction:
    if not isinstance(value, (Fraction, Decimal)):
        raise TypeError("statistical probabilities require exact Fraction or Decimal values")
    if isinstance(value, Decimal) and not value.is_finite():
        raise ValueError("statistical probability must be finite")
    result = Fraction(value)
    if not (0 <= result <= 1 if endpoints else 0 < result < 1):
        raise ValueError("statistical probability is outside its declared interval")
    return result


def _unit_count(unit_count: int) -> None:
    if type(unit_count) is not int or unit_count < 1:
        raise ValueError("statistical reduction needs a positive whole-unit denominator")


def calibration_rank(unit_count: int, alpha: Fraction | Decimal) -> int:
    """Return ceil((n+1)(1-alpha)); n+1 denotes an infinite upper bound."""
    _unit_count(unit_count)
    rank = (unit_count + 1) * (1 - _probability(alpha))
    return (rank.numerator + rank.denominator - 1) // rank.denominator


def binomial_upper_tail(unit_count: int, successes: int,
                        null_probability: Fraction) -> Fraction:
    """Exact arithmetic only; this function supplies no IID/sampling warrant."""
    _unit_count(unit_count)
    if type(successes) is not int or not 0 <= successes <= unit_count + 1:
        raise ValueError("success census differs from its complete denominator")
    p = _probability(null_probability, endpoints=True)
    return sum((Fraction(comb(unit_count, k)) * p**k * (1-p)**(unit_count-k)
                for k in range(successes, unit_count+1)), Fraction(0))


def binomial_minimum_successes(unit_count: int, null_probability: Fraction,
                               alpha: Fraction) -> int:
    """Return n+1 when no attainable success count reaches the declared alpha."""
    _unit_count(unit_count)
    p = _probability(null_probability, endpoints=True)
    a = _probability(alpha)
    for successes in range(unit_count + 1):
        if binomial_upper_tail(unit_count, successes, p) <= a:
            return successes
    return unit_count + 1


@dataclass(frozen=True, slots=True)
class BinomialProbabilityInterval(CanonicalRecord):
    """Exact binomial inversion, with numerically evaluated beta quantiles."""

    SCHEMA: ClassVar[str] = 'empirical-lawhood/experimental-methods/binomial-probability-interval'
    unit_count: int
    successes: int
    tail_numerator: int
    tail_denominator: int
    lower: Decimal | None
    upper: Decimal | None

    def __post_init__(self):
        if (type(self.unit_count) is not int or self.unit_count < 0
                or type(self.successes) is not int or not 0 <= self.successes <= self.unit_count
                or type(self.tail_numerator) is not int or type(self.tail_denominator) is not int
                or not 0 < 2 * self.tail_numerator < self.tail_denominator
                or (self.lower is None) != (self.unit_count == 0)
                or (self.upper is None) != (self.unit_count == 0)):
            raise ValueError('binomial interval changes its count, exact tail or undefined zero-risk cell')
        if self.unit_count and (any(type(value) is not Decimal or not value.is_finite() for value in (self.lower, self.upper))
                or not 0 <= self.lower <= self.upper <= 1):
            raise ValueError('binomial interval loses finite ordered probability bounds')


def binomial_probability_interval(unit_count: int, successes: int, *, tail_probability: Fraction) -> BinomialProbabilityInterval:
    """Two-sided Clopper–Pearson interval; n=0 is undefined, never [0,1].

    Tail allocation and counts are exact. Decimal bounds retain the shortest
    round-trip spellings of the numerical quantile results. This function does
    not establish independent sampling or applicability to a selected subset.
    """
    from scipy.stats import beta

    if (type(unit_count) is not int or unit_count < 0 or type(successes) is not int
            or not 0 <= successes <= unit_count or type(tail_probability) is not Fraction
            or not 0 < tail_probability < Fraction(1, 2)):
        raise ValueError('binomial interval requires exact counts and a positive sub-half tail allocation')
    lower = upper = None
    if unit_count:
        tail = float(tail_probability)
        if not 0 < tail < .5:
            raise ValueError('binomial interval tail is numerically unrepresentable')
        lo = 0. if successes == 0 else float(beta.ppf(tail, successes, unit_count - successes + 1))
        hi = 1. if successes == unit_count else float(beta.isf(tail, successes + 1, unit_count - successes))
        if (not isfinite(lo) or not isfinite(hi) or not 0 <= lo <= hi <= 1
                or successes > 0 and lo == 0 or successes < unit_count and hi == 1):
            raise ValueError('binomial interval quantile is numerically unrepresentable')
        lower, upper = Decimal(str(lo)), Decimal(str(hi))
    return BinomialProbabilityInterval(unit_count, successes, tail_probability.numerator,
        tail_probability.denominator, lower, upper)


BINOMIAL_COMPLETION_STATES = ('FAILURE', 'INELIGIBLE', 'SUCCESS')


@dataclass(frozen=True, slots=True)
class IncompleteBinomialInterval(CanonicalRecord):
    """Assigned-unit envelope and an explicitly assessable-only interval."""

    SCHEMA: ClassVar[str] = 'empirical-lawhood/experimental-methods/incomplete-binomial-interval'
    unit_ids: tuple[str, ...]
    allowed_states: tuple[tuple[str, ...], ...]
    tail_numerator: int
    tail_denominator: int
    lower: Decimal | None
    upper: Decimal | None
    complete_case: BinomialProbabilityInterval

    def __post_init__(self):
        from empirical_lawhood.kernel.serialization import validate_stable_id

        if (type(self.unit_ids) is not tuple or not self.unit_ids or len(set(self.unit_ids)) != len(self.unit_ids)
                or type(self.allowed_states) is not tuple or len(self.allowed_states) != len(self.unit_ids)
                or any(type(row) is not tuple or not row or row != tuple(sorted(set(row)))
                    or set(row) - set(BINOMIAL_COMPLETION_STATES) for row in self.allowed_states)
                or type(self.tail_numerator) is not int or type(self.tail_denominator) is not int
                or not 0 < 2 * self.tail_numerator < self.tail_denominator
                or type(self.complete_case) is not BinomialProbabilityInterval):
            raise ValueError('incomplete binomial interval changes its complete assigned-unit/eligibility census')
        for unit in self.unit_ids:
            validate_stable_id(unit)
        self.complete_case.__post_init__()
        if (self.complete_case.tail_numerator != self.tail_numerator or self.complete_case.tail_denominator != self.tail_denominator
                or self.complete_case.unit_count != sum(row in (('FAILURE',), ('SUCCESS',)) for row in self.allowed_states)
                or self.complete_case.successes != sum(row == ('SUCCESS',) for row in self.allowed_states)
                or (self.lower is None) != (self.risk_count_lower == 0)
                or (self.upper is None) != (self.risk_count_lower == 0)):
            raise ValueError('incomplete binomial interval invents conditional risk or assessability')
        if self.lower is not None and (any(type(value) is not Decimal or not value.is_finite() for value in (self.lower, self.upper))
                or not 0 <= self.lower <= self.upper <= 1):
            raise ValueError('incomplete binomial interval loses finite ordered probability bounds')

    @property
    def risk_count_lower(self):
        return sum('INELIGIBLE' not in row for row in self.allowed_states)

    @property
    def risk_count_upper(self):
        return sum(row != ('INELIGIBLE',) for row in self.allowed_states)

    @property
    def known_successes(self):
        return sum(row == ('SUCCESS',) for row in self.allowed_states)

    @property
    def known_failures(self):
        return sum(row == ('FAILURE',) for row in self.allowed_states)

    @property
    def known_risk_unknown_outcomes(self):
        return sum(row == ('FAILURE', 'SUCCESS') for row in self.allowed_states)

    @property
    def unknown_eligibility(self):
        return sum('INELIGIBLE' in row and len(row) > 1 for row in self.allowed_states)


def incomplete_binomial_interval(unit_ids: tuple[str, ...], allowed_states: tuple[tuple[str, ...], ...], *,
        tail_probability: Fraction) -> IncompleteBinomialInterval:
    """Union of CP bounds over every permitted eligibility/outcome completion.

    Each unit supplies its categorical feasible states. Correlated restrictions
    across units are not an operand of this independent-unit construction.
    Dynamic programming keeps the extremal success counts for each feasible
    risk count; it neither drops unknown roots nor treats them as failures.
    If no eligible unit is established, the conditional cell remains undefined.
    """
    if type(unit_ids) is not tuple or type(allowed_states) is not tuple:
        raise TypeError('incomplete binomial inference requires immutable assigned-unit and state tuples')
    complete_count = sum(row in (('FAILURE',), ('SUCCESS',)) for row in allowed_states)
    successes = sum(row == ('SUCCESS',) for row in allowed_states)
    complete = binomial_probability_interval(complete_count, successes, tail_probability=tail_probability)
    # Validate the full categorical contract before building any completion.
    established_risk = sum('INELIGIBLE' not in row for row in allowed_states)
    provisional = IncompleteBinomialInterval(unit_ids, allowed_states, tail_probability.numerator,
        tail_probability.denominator, Decimal(0) if established_risk else None,
        Decimal(1) if established_risk else None, complete)
    lower = upper = None
    if established_risk:
        counts = {0: (0, 0)}
        for options in allowed_states:
            next_counts = {}
            for n, (smallest, largest) in counts.items():
                for state in options:
                    count = n + (state != 'INELIGIBLE')
                    increment = int(state == 'SUCCESS')
                    lo, hi = smallest + increment, largest + increment
                    previous = next_counts.get(count)
                    next_counts[count] = (lo, hi) if previous is None else (min(lo, previous[0]), max(hi, previous[1]))
            counts = next_counts
        bounds = tuple((binomial_probability_interval(n, smallest, tail_probability=tail_probability).lower,
            binomial_probability_interval(n, largest, tail_probability=tail_probability).upper)
            for n, (smallest, largest) in counts.items())
        lower, upper = min(lo for lo, _ in bounds), max(hi for _, hi in bounds)
    return IncompleteBinomialInterval(provisional.unit_ids, provisional.allowed_states, provisional.tail_numerator,
        provisional.tail_denominator, lower, upper, complete)


@dataclass(frozen=True, slots=True)
class AssignedBinomialInference(CanonicalRecord):
    """Whole-roster event test; unknown events are operational nonsuccess.

    The separately retained 95% interval envelopes the unresolved true events.
    This arithmetic supplies no independent-sampling or qualification warrant.
    """

    SCHEMA: ClassVar[str] = 'empirical-lawhood/experimental-methods/assigned-binomial-inference'
    unit_ids: tuple[str, ...]
    events: tuple[bool | None, ...]
    null_numerator: int
    null_denominator: int
    alpha_numerator: int
    alpha_denominator: int
    tail_numerator: int
    tail_denominator: int
    critical_successes: int
    descriptive_interval: IncompleteBinomialInterval

    def __post_init__(self):
        from empirical_lawhood.kernel.serialization import validate_stable_id
        if (type(self.unit_ids) is not tuple or not self.unit_ids or self.unit_ids != tuple(sorted(set(self.unit_ids)))
                or type(self.events) is not tuple or len(self.events) != len(self.unit_ids)
                or any(value is not None and type(value) is not bool for value in self.events)
                or any(type(value) is not int for value in (self.null_numerator, self.null_denominator,
                    self.alpha_numerator, self.alpha_denominator, self.tail_numerator, self.tail_denominator, self.critical_successes))
                or not 0 < self.null_numerator < self.null_denominator
                or not 0 < self.alpha_numerator < self.alpha_denominator
                or not 0 <= self.tail_numerator <= self.tail_denominator or self.tail_denominator < 1
                or type(self.descriptive_interval) is not IncompleteBinomialInterval):
            raise ValueError('assigned binomial test changes its exact whole-unit event/null/alpha census')
        for unit in self.unit_ids:
            validate_stable_id(unit)
        states = tuple(('SUCCESS',) if value is True else ('FAILURE',) if value is False else ('FAILURE', 'SUCCESS') for value in self.events)
        if (self.descriptive_interval.unit_ids != self.unit_ids or self.descriptive_interval.allowed_states != states
                or (self.descriptive_interval.tail_numerator, self.descriptive_interval.tail_denominator) != (1, 40)
                or Fraction(self.tail_numerator, self.tail_denominator) != binomial_upper_tail(len(self.unit_ids),
                    self.successes, Fraction(self.null_numerator, self.null_denominator))
                or self.critical_successes != binomial_minimum_successes(len(self.unit_ids),
                    Fraction(self.null_numerator, self.null_denominator), Fraction(self.alpha_numerator, self.alpha_denominator))):
            raise ValueError('assigned binomial test substitutes its full denominator, exact tail or descriptive uncertainty')
        self.descriptive_interval.__post_init__()

    @property
    def successes(self):
        return sum(value is True for value in self.events)

    @property
    def failures(self):
        return sum(value is False for value in self.events)

    @property
    def unknowns(self):
        return sum(value is None for value in self.events)

    @property
    def criterion_met(self):
        return Fraction(self.tail_numerator, self.tail_denominator) <= Fraction(self.alpha_numerator, self.alpha_denominator)


def assigned_binomial_inference(unit_ids, events, *, null_probability, alpha):
    """Exact operational test plus descriptive true-event completion envelope."""
    if (type(unit_ids) is not tuple or type(events) is not tuple
            or type(null_probability) is not Fraction or type(alpha) is not Fraction):
        raise TypeError('assigned event inference requires immutable units/events and exact rational choices')
    tail = binomial_upper_tail(len(unit_ids), sum(value is True for value in events), null_probability)
    critical = binomial_minimum_successes(len(unit_ids), null_probability, alpha)
    states = tuple(('SUCCESS',) if value is True else ('FAILURE',) if value is False else ('FAILURE', 'SUCCESS') for value in events)
    interval = incomplete_binomial_interval(unit_ids, states, tail_probability=Fraction(1, 40))
    return AssignedBinomialInference(unit_ids, events, null_probability.numerator, null_probability.denominator,
        alpha.numerator, alpha.denominator, tail.numerator, tail.denominator, critical, interval)


def raw_median(values: tuple[Decimal, ...]) -> Decimal:
    """Median in the supplied units, including the arithmetic even-n midpoint."""
    if (type(values) is not tuple or not values
            or any(type(value) is not Decimal or not value.is_finite() for value in values)):
        raise ValueError("median needs explicitly selected finite raw observations")
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[midpoint]
    left, right = ordered[midpoint-1], ordered[midpoint]
    exponent = min(left.as_tuple().exponent, right.as_tuple().exponent)

    def coefficient(value):
        sign, digits, power = value.as_tuple()
        number = 0
        for digit in digits:
            number = 10 * number + digit
        return (-number if sign else number) * 10**(power-exponent)

    total = coefficient(left) + coefficient(right)
    # Decimal tuple construction is exact even under a low-precision caller
    # context. Half an integer has a terminating decimal representation.
    if total % 2:
        total *= 5
        exponent -= 1
    else:
        total //= 2
    return Decimal((int(total < 0), Decimal(abs(total)).as_tuple().digits, exponent))


@dataclass(frozen=True, slots=True)
class RankCalibration:
    unit_count: int
    rank: int
    radius: Decimal


def split_upper_calibration(scores: tuple[Decimal | None, ...],
                            alpha: Fraction | Decimal) -> RankCalibration:
    """Keep missing/nonuse whole-unit scores as infinity in the full denominator."""
    if type(scores) is not tuple:
        raise TypeError("calibration requires an immutable complete score roster")
    rank = calibration_rank(len(scores), alpha)
    ordered = []
    for value in scores:
        if value is None:
            ordered.append(Decimal("Infinity"))
        elif type(value) is not Decimal or value.is_nan() or value < 0:
            raise ValueError("upper-calibration scores must be nonnegative or explicitly missing")
        else:
            ordered.append(value)
    ordered.sort()
    radius = ordered[rank-1] if rank <= len(ordered) else Decimal("Infinity")
    return RankCalibration(len(scores), rank, radius)


@dataclass(frozen=True, slots=True)
class StandardizedRidgeParameters(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/experimental-methods/standardized-ridge-parameters"
    means: tuple[Decimal, ...]
    scales: tuple[Decimal, ...]
    zero_variance_mask: tuple[bool, ...]
    coefficients: tuple[Decimal, ...] | None
    training_rows: int
    fitted_rows: int

    def __post_init__(self):
        count = len(self.means)
        if (not count or len(self.scales) != count or len(self.zero_variance_mask) != count
                or any(type(value) is not Decimal or not value.is_finite()
                       for value in (*self.means, *self.scales))
                or any(value <= 0 for value in self.scales)
                or any(type(value) is not bool for value in self.zero_variance_mask)
                or type(self.training_rows) is not int or type(self.fitted_rows) is not int
                or not 0 <= self.fitted_rows <= self.training_rows
                or ((self.coefficients is None) != (self.fitted_rows == 0))):
            raise ValueError("ridge parameters change complete standardization or training census")
        if self.coefficients is not None and (
                len(self.coefficients) != count+1
                or any(type(value) is not Decimal or not value.is_finite() for value in self.coefficients)):
            raise ValueError("ridge coefficients differ from the explicit intercept/feature census")


def _numerical_decimal(value) -> Decimal:
    # Match the established scientific numerical conversion, without binary
    # Decimal construction or arithmetic normalization of historical spellings.
    return Decimal(str(float(value)))


def fit_standardized_ridge(features: tuple[tuple[Decimal, ...], ...],
                           targets: tuple[Decimal | None, ...], *,
                           penalty: Decimal, penalize_intercept: bool = False
                           ) -> StandardizedRidgeParameters:
    """Standardize all TRAIN feature rows; fit only explicitly available targets.

    Feature/target meaning, eligible rows and transforms are domain decisions.
    Calibration/evaluation data are not operands of this function.
    """
    import numpy as np

    if (type(features) is not tuple or not features or type(targets) is not tuple
            or len(features) != len(targets) or not features[0]
            or any(type(row) is not tuple or len(row) != len(features[0]) for row in features)
            or any(type(value) is not Decimal or not value.is_finite() for row in features for value in row)
            or any(value is not None and (type(value) is not Decimal or not value.is_finite()) for value in targets)
            or type(penalty) is not Decimal or not penalty.is_finite() or penalty <= 0
            or type(penalize_intercept) is not bool):
        raise ValueError("ridge fitting requires complete finite feature rows and explicit target missingness")
    numerical_penalty = float(penalty)
    if not np.isfinite(numerical_penalty) or numerical_penalty <= 0:
        raise ValueError("ridge penalty is numerically unrepresentable")
    x = np.asarray([[float(value) for value in row] for row in features], dtype=float)
    if not np.isfinite(x).all():
        raise ValueError("ridge features are numerically unrepresentable")
    means, scales = x.mean(axis=0), x.std(axis=0)
    constant = np.ptp(x, axis=0) == 0
    means[constant] = x[0, constant]
    scales[constant] = 1
    scales[scales == 0] = 1
    if not np.isfinite(means).all() or not np.isfinite(scales).all():
        raise ValueError("ridge standardization is numerically unrepresentable")
    standardized = np.column_stack((np.ones(len(x)), (x-means)/scales))
    used = [index for index, target in enumerate(targets) if target is not None]
    coefficients = None
    if used:
        design = standardized[used]
        target = np.asarray([float(targets[index]) for index in used])
        regularization = np.eye(x.shape[1]+1) * numerical_penalty
        if not penalize_intercept:
            regularization[0, 0] = 0
        if not np.isfinite(target).all() or not np.isfinite(regularization).all():
            raise ValueError("ridge target or penalty is numerically unrepresentable")
        try:
            fitted = np.linalg.solve(design.T @ design + regularization, design.T @ target)
        except np.linalg.LinAlgError as error:
            raise ValueError("ridge normal equations are numerically unevaluable") from error
        if not np.isfinite(fitted).all():
            raise ValueError("ridge fit is numerically unrepresentable")
        coefficients = tuple(_numerical_decimal(value) for value in fitted)
    return StandardizedRidgeParameters(tuple(_numerical_decimal(value) for value in means),
        tuple(_numerical_decimal(value) for value in scales), tuple(bool(value) for value in constant),
        coefficients, len(features), len(used))


def predict_standardized_ridge(parameters: StandardizedRidgeParameters,
                               features: tuple[Decimal, ...]) -> Decimal | None:
    import numpy as np

    parameters.__post_init__()
    if (type(features) is not tuple or len(features) != len(parameters.means)
            or any(type(value) is not Decimal or not value.is_finite() for value in features)):
        raise ValueError("ridge prediction changes the declared finite feature census")
    if parameters.coefficients is None:
        return None
    row = np.asarray([float(value) for value in features])
    means = np.asarray([float(value) for value in parameters.means])
    scales = np.asarray([float(value) for value in parameters.scales])
    coefficients = np.asarray([float(value) for value in parameters.coefficients])
    value = float(coefficients[0] + ((row-means)/scales) @ coefficients[1:])
    if not np.isfinite(value):
        raise ValueError("ridge prediction is numerically unrepresentable")
    return _numerical_decimal(value)
