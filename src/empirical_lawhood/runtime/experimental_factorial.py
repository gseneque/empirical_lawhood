# SPDX-License-Identifier: MPL-2.0
"""Exact complete-block factorial contrasts and declared-family Holm arithmetic.

The domain must establish the matched groups, endpoint, factor meanings and
valid physical grid. Coded levels are -1/+1, with a declared actual center at
0/0/0; symmetry in linear or log physical coordinates is a domain obligation.
Nine coordinates are nested observations of one group, never nine independent
units. This method requires all nine values to be finite for every contrast of
that group. A different endpoint-specific missingness policy needs a separate
explicit contract, rather than implicit omission or imputation here.

No function supplies a p-value, IID/exchangeability warrant, source eligibility,
model selection, scientific qualification or authority. Holm controls a declared
family only when its supplied probabilities and scientific procedure are valid.
The descriptive three-way contrast is outside an inferential family unless the
domain prospectively declares an additional formal comparison.
"""

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from fractions import Fraction
from itertools import product

from empirical_lawhood.kernel.serialization import validate_stable_id


_CORNERS = frozenset(product((-1, 1), repeat=3))
_CENTER = (0, 0, 0)
_PAIR_AXES = ((0, 1), (0, 2), (1, 2))


class PairInteractionScale(StrEnum):
    """Explicit endpoint-unit contrasts, not raw coded polynomial coefficients."""

    SIGNED_MEAN_DIFFERENCE = "SIGNED_MEAN_DIFFERENCE"
    DIFFERENCE_OF_DIFFERENCES = "DIFFERENCE_OF_DIFFERENCES"


class FactorialDisposition(StrEnum):
    FINITE = "FINITE"
    UNEVALUABLE = "UNEVALUABLE"


@dataclass(frozen=True, slots=True)
class FactorialCoordinate:
    coordinate_id: str
    levels: tuple[int, int, int]

    def __post_init__(self):
        validate_stable_id(self.coordinate_id)
        if (type(self.levels) is not tuple or len(self.levels) != 3
                or any(type(value) is not int for value in self.levels)
                or self.levels not in _CORNERS | {_CENTER}):
            raise ValueError("factorial coordinate must be an exact cube corner or the declared center")


@dataclass(frozen=True, slots=True)
class FactorialGrid:
    """Factor order fixes the sign/orientation of each coded contrast."""

    factor_ids: tuple[str, str, str]
    coordinates: tuple[FactorialCoordinate, ...]

    def __post_init__(self):
        if (type(self.factor_ids) is not tuple or len(self.factor_ids) != 3
                or len(set(self.factor_ids)) != 3):
            raise ValueError("factorial grid needs three distinct ordered factor identifiers")
        for factor_id in self.factor_ids:
            validate_stable_id(factor_id)
        if (type(self.coordinates) is not tuple or len(self.coordinates) != 9
                or any(type(row) is not FactorialCoordinate for row in self.coordinates)):
            raise ValueError("factorial grid needs its complete eight corners and one center")
        for row in self.coordinates:
            row.__post_init__()
        if (len({row.coordinate_id for row in self.coordinates}) != 9
                or {row.levels for row in self.coordinates} != _CORNERS | {_CENTER}):
            raise ValueError("factorial grid duplicates or omits its exact corner/center census")


@dataclass(frozen=True, slots=True)
class FactorialObservation:
    group_id: str
    coordinate: FactorialCoordinate
    value: Decimal | None

    def __post_init__(self):
        validate_stable_id(self.group_id)
        if type(self.coordinate) is not FactorialCoordinate:
            raise TypeError("factorial observation needs its exact declared coordinate")
        self.coordinate.__post_init__()
        if self.value is not None and type(self.value) is not Decimal:
            raise TypeError("factorial observations require exact Decimal values or explicit missingness")


@dataclass(frozen=True, slots=True)
class FactorialGroupContrasts:
    group_id: str
    disposition: FactorialDisposition
    observations: tuple[FactorialObservation, ...]
    expected_coordinate_count: int
    missing_coordinate_ids: tuple[str, ...]
    nonfinite_coordinate_ids: tuple[str, ...]
    main_effects: tuple[Fraction | None, Fraction | None, Fraction | None]
    pair_interactions: tuple[Fraction | None, Fraction | None, Fraction | None]
    three_way: Fraction | None
    curvature: Fraction | None

    @property
    def observed_coordinate_count(self) -> int:
        return len(self.observations)

    @property
    def finite_coordinate_count(self) -> int:
        return sum(row.value is not None and row.value.is_finite() for row in self.observations)

    @property
    def three_way_scope(self) -> str:
        return "DESCRIPTIVE_ONLY"


@dataclass(frozen=True, slots=True)
class FactorialReduction:
    grid: FactorialGrid
    group_ids: tuple[str, ...]
    pair_scale: PairInteractionScale
    groups: tuple[FactorialGroupContrasts, ...]

    @property
    def group_count(self) -> int:
        return len(self.group_ids)

    @property
    def complete_group_count(self) -> int:
        return sum(row.disposition is FactorialDisposition.FINITE for row in self.groups)

    @property
    def unevaluable_group_count(self) -> int:
        return self.group_count - self.complete_group_count

    @property
    def pair_factor_ids(self) -> tuple[tuple[str, str], ...]:
        return tuple((self.grid.factor_ids[left], self.grid.factor_ids[right]) for left, right in _PAIR_AXES)


def _declared_ids(values, *, label):
    if (type(values) is not tuple or not values
            or any(type(value) is not str for value in values)
            or len(set(values)) != len(values)):
        raise ValueError(f"{label} requires an explicit nonempty unique immutable identifier census")
    for value in values:
        validate_stable_id(value)


def factorial_group_contrasts(grid: FactorialGrid, group_ids: tuple[str, ...],
                              observations: tuple[FactorialObservation, ...], *,
                              pair_scale: PairInteractionScale) -> FactorialReduction:
    """Reduce every declared matched group without dropping incomplete groups.

    Main effect i is mean(high i) minus mean(low i): sum(x_i*y)/4.
    Signed-mean pair interaction ij is sum(x_i*x_j*y)/4, the same-sign
    corner mean minus the opposite-sign corner mean. Difference-of-differences
    is twice that: sum(x_i*x_j*y)/2. For y=beta_ij*x_i*x_j these are
    2*beta_ij and 4*beta_ij respectively; neither is the raw coefficient.
    Pairs are ordered (factor0,factor1), (factor0,factor2), (factor1,factor2).
    The descriptive three-way effect is sum(x0*x1*x2*y)/4. Curvature is
    center minus mean(corners), identifying only aggregate curvature.

    Absent rows and None values are reported as missing. Nonfinite Decimal
    values remain in the retained observations and are reported separately.
    Any such coordinate makes all contrasts of its whole nine-setting group
    UNEVALUABLE. No finite-only across-group mean is produced.
    """
    if type(grid) is not FactorialGrid:
        raise TypeError("factorial reduction requires its typed complete declared grid")
    grid.__post_init__()
    _declared_ids(group_ids, label="factorial groups")
    if type(pair_scale) is not PairInteractionScale:
        raise TypeError("factorial pair scaling requires its explicit typed declaration")
    if type(observations) is not tuple or any(type(row) is not FactorialObservation for row in observations):
        raise TypeError("factorial reduction requires an immutable typed observation census")
    declared = {row.coordinate_id: row for row in grid.coordinates}
    grouped = {group_id: {} for group_id in group_ids}
    for row in observations:
        row.__post_init__()
        if row.group_id not in grouped:
            raise ValueError("factorial observation is outside the complete declared group census")
        if declared.get(row.coordinate.coordinate_id) != row.coordinate:
            raise ValueError("factorial observation substitutes its declared corner grid or center")
        previous = grouped[row.group_id]
        if row.coordinate.coordinate_id in previous:
            raise ValueError("factorial observation duplicates a coordinate of one matched group")
        previous[row.coordinate.coordinate_id] = row
    results = []
    for group_id in group_ids:
        rows = grouped[group_id]
        retained = tuple(rows[name] for name in sorted(rows))
        missing = tuple(sorted(name for name in declared if name not in rows or rows[name].value is None))
        nonfinite = tuple(sorted(name for name, row in rows.items()
            if row.value is not None and not row.value.is_finite()))
        if missing or nonfinite:
            results.append(FactorialGroupContrasts(group_id, FactorialDisposition.UNEVALUABLE,
                retained, 9, missing, nonfinite, (None,) * 3, (None,) * 3, None, None))
            continue
        values = {row.coordinate.levels: Fraction(row.value) for row in retained}
        main = tuple(sum((level[axis] * values[level] for level in _CORNERS), Fraction(0)) / 4
                     for axis in range(3))
        pair_divisor = 4 if pair_scale is PairInteractionScale.SIGNED_MEAN_DIFFERENCE else 2
        pairs = tuple(sum((level[left] * level[right] * values[level] for level in _CORNERS), Fraction(0))
                      / pair_divisor for left, right in _PAIR_AXES)
        three_way = sum((level[0] * level[1] * level[2] * values[level] for level in _CORNERS), Fraction(0)) / 4
        curvature = values[_CENTER] - sum((values[level] for level in _CORNERS), Fraction(0)) / 8
        results.append(FactorialGroupContrasts(group_id, FactorialDisposition.FINITE,
            retained, 9, (), (), main, pairs, three_way, curvature))
    return FactorialReduction(grid, group_ids, pair_scale, tuple(results))


class HolmDisposition(StrEnum):
    REJECTED = "REJECTED"
    NOT_REJECTED = "NOT_REJECTED"
    UNEVALUABLE = "UNEVALUABLE"


@dataclass(frozen=True, slots=True)
class HolmComparisonResult:
    comparison_id: str
    p_value: Fraction | None
    adjusted_p_value: Fraction | None
    stepdown_rank: int | None
    critical_alpha: Fraction | None
    disposition: HolmDisposition

    @property
    def rejected(self) -> bool:
        return self.disposition is HolmDisposition.REJECTED


@dataclass(frozen=True, slots=True)
class HolmAdjustment:
    family_ids: tuple[str, ...]
    alpha: Fraction
    comparisons: tuple[HolmComparisonResult, ...]

    @property
    def family_size(self) -> int:
        return len(self.family_ids)

    @property
    def evaluated_count(self) -> int:
        return sum(row.p_value is not None for row in self.comparisons)

    @property
    def unevaluable_count(self) -> int:
        return self.family_size - self.evaluated_count


def _probability(value, *, alpha=False):
    if type(value) not in (Fraction, Decimal):
        raise TypeError("Holm probabilities require exact Fraction or Decimal operands")
    if type(value) is Decimal and not value.is_finite():
        raise ValueError("Holm probabilities must be finite or explicitly unevaluable as None")
    exact = Fraction(value)
    if not (0 < exact < 1 if alpha else 0 <= exact <= 1):
        raise ValueError("Holm probability is outside its declared interval")
    return exact


def holm_adjustment(family_ids: tuple[str, ...],
                    p_values: tuple[tuple[str, Fraction | Decimal | None], ...], *,
                    alpha: Fraction | Decimal) -> HolmAdjustment:
    """Exact step-down adjustment of an entire prospectively declared family.

    Every family slot must occur exactly once. None is UNEVALUABLE and acts as
    p=1 for the mathematical family, retaining the original family size m and
    never receiving a rejection. Its public adjusted probability/rank remain
    None. Finite probabilities are ordered by (p, comparison_id); their adjusted
    values are min(1, max_{j<=i}((m-j+1)*p_j)), with one-based ranks. Rejection
    uses adjusted p <= alpha. Ties retain the same adjusted value.

    This function only adjusts supplied probabilities. It does not compute
    them, assess sampling assumptions or permit outcome-dependent family edits.
    """
    _declared_ids(family_ids, label="Holm family")
    a = _probability(alpha, alpha=True)
    if (type(p_values) is not tuple or any(type(row) is not tuple or len(row) != 2 for row in p_values)
            or any(type(name) is not str for name, _ in p_values)
            or len({name for name, _ in p_values}) != len(p_values)
            or {name for name, _ in p_values} != set(family_ids)):
        raise ValueError("Holm values must retain every predeclared comparison exactly once")
    values = {name: None if value is None else _probability(value) for name, value in p_values}
    # None's internal p=1 leaves the full m in every finite step; unavailable
    # slots cannot be removed to increase another comparison's allowance.
    ordered = sorted(((value, name) for name, value in values.items() if value is not None))
    by_id, previous = {}, Fraction(0)
    for rank, (value, name) in enumerate(ordered, start=1):
        remaining = len(family_ids) - rank + 1
        adjusted = min(Fraction(1), max(previous, remaining * value))
        previous = adjusted
        disposition = HolmDisposition.REJECTED if adjusted <= a else HolmDisposition.NOT_REJECTED
        by_id[name] = HolmComparisonResult(name, value, adjusted, rank, a / remaining, disposition)
    for name, value in values.items():
        if value is None:
            by_id[name] = HolmComparisonResult(name, None, None, None, None, HolmDisposition.UNEVALUABLE)
    return HolmAdjustment(family_ids, a, tuple(by_id[name] for name in family_ids))
