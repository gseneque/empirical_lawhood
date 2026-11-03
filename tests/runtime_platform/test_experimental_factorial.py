# SPDX-License-Identifier: MPL-2.0
"""Independent polynomial and rational-family checks; no scientific warrant."""

from dataclasses import FrozenInstanceError, replace
from decimal import Decimal, localcontext
from fractions import Fraction
from itertools import product

import pytest

from empirical_lawhood.runtime.experimental_factorial import (
    FactorialCoordinate, FactorialDisposition, FactorialGrid, FactorialObservation,
    HolmDisposition, PairInteractionScale, factorial_group_contrasts, holm_adjustment,
)


D = Decimal
SIGNED = PairInteractionScale.SIGNED_MEAN_DIFFERENCE
DOD = PairInteractionScale.DIFFERENCE_OF_DIFFERENCES


def _grid():
    corners = tuple(FactorialCoordinate("corner." + "".join("h" if value == 1 else "l" for value in levels),
        levels) for levels in product((-1, 1), repeat=3))
    return FactorialGrid(("temperature", "friction", "coupling"),
                         (*corners, FactorialCoordinate("reference.center", (0, 0, 0))))


def _polynomial(levels):
    # A declared polynomial supplies an independent coefficient oracle. This
    # evaluates each point; it does not implement any contrast reduction.
    a, b, c = levels
    return D(17 + 2*a - 3*b + 5*c + 7*a*b - 11*a*c + 13*b*c - 19*a*b*c
             + 23*a*a + 29*b*b + 31*c*c)


def _observations(grid, group_ids=("group.one",), function=_polynomial):
    return tuple(FactorialObservation(group_id, coordinate, function(coordinate.levels))
                 for group_id in group_ids for coordinate in grid.coordinates)


@pytest.mark.parametrize("scale,expected_pairs", ((SIGNED, (14, -22, 26)), (DOD, (28, -44, 52))))
def test_polynomial_coefficients_independently_determine_every_contrast(scale, expected_pairs):
    grid = _grid()
    result = factorial_group_contrasts(grid, ("group.one",), _observations(grid), pair_scale=scale)
    group, = result.groups
    assert group.main_effects == (Fraction(4), Fraction(-6), Fraction(10))
    assert group.pair_interactions == tuple(Fraction(value) for value in expected_pairs)
    assert group.three_way == Fraction(-38)
    # All eight corners have sum-of-quadratic contribution23+29+31=83;
    # the center has none. Individual quadratic coefficients are unidentified.
    assert group.curvature == Fraction(-83)
    assert group.three_way_scope == "DESCRIPTIVE_ONLY"
    assert group.disposition is FactorialDisposition.FINITE
    assert group.expected_coordinate_count == group.observed_coordinate_count == group.finite_coordinate_count == 9
    assert result.group_count == result.complete_group_count == 1
    assert result.pair_factor_ids == (("temperature", "friction"), ("temperature", "coupling"),
                                      ("friction", "coupling"))


@pytest.mark.parametrize("powers,main,pairs,three_way,curvature", (
    ((1, 0, 0), (6, 0, 0), (0, 0, 0), 0, 0),
    ((0, 1, 0), (0, 6, 0), (0, 0, 0), 0, 0),
    ((0, 0, 1), (0, 0, 6), (0, 0, 0), 0, 0),
    ((1, 1, 0), (0, 0, 0), (6, 0, 0), 0, 0),
    ((1, 0, 1), (0, 0, 0), (0, 6, 0), 0, 0),
    ((0, 1, 1), (0, 0, 0), (0, 0, 6), 0, 0),
    ((1, 1, 1), (0, 0, 0), (0, 0, 0), 6, 0),
    ((2, 0, 0), (0, 0, 0), (0, 0, 0), 0, -3),
    ((0, 2, 0), (0, 0, 0), (0, 0, 0), 0, -3),
    ((0, 0, 2), (0, 0, 0), (0, 0, 0), 0, -3),
))
def test_isolated_polynomial_terms_do_not_leak_into_other_contrasts(powers, main, pairs, three_way, curvature):
    def point(levels):
        value = 3
        for level, power in zip(levels, powers, strict=True):
            value *= level**power
        return D(101 + value)
    grid = _grid()
    group, = factorial_group_contrasts(grid, ("group.one",), _observations(grid, function=point),
                                      pair_scale=SIGNED).groups
    assert group.main_effects == tuple(Fraction(value) for value in main)
    assert group.pair_interactions == tuple(Fraction(value) for value in pairs)
    assert group.three_way == Fraction(three_way)
    assert group.curvature == Fraction(curvature)


def test_different_quadratic_distributions_are_the_same_aggregate_curvature():
    grid = _grid()
    results = []
    for weights in ((3, 0, 0), (0, 1, 2)):
        observations = _observations(grid, function=lambda levels, weights=weights:
            D(7 + sum(weight * value**2 for weight, value in zip(weights, levels, strict=True))))
        results.append(factorial_group_contrasts(grid, ("group.one",), observations, pair_scale=SIGNED).groups[0])
    assert results[0].curvature == results[1].curvature == -3
    assert results[0].main_effects == results[1].main_effects == (0, 0, 0)
    assert results[0].pair_interactions == results[1].pair_interactions == (0, 0, 0)


def test_high_low_effect_and_pair_scale_are_direct_matched_mean_differences():
    grid = _grid()
    observations = _observations(grid, function=lambda levels: D(2 + 3*levels[0] + 5*levels[0]*levels[1]))
    signed = factorial_group_contrasts(grid, ("group.one",), observations, pair_scale=SIGNED).groups[0]
    doubled = factorial_group_contrasts(grid, ("group.one",), observations, pair_scale=DOD).groups[0]
    high = [Fraction(row.value) for row in observations if row.coordinate.levels[0] == 1]
    low = [Fraction(row.value) for row in observations if row.coordinate.levels[0] == -1]
    assert signed.main_effects[0] == sum(high) / 4 - sum(low) / 4 == 6
    # For the two-factor cell means (averaging over factor3), the difference
    # at factor2high is16, at factor2low is-4; their difference is20.
    assert doubled.pair_interactions[0] == 20
    assert signed.pair_interactions[0] == 10


def test_fraction_results_preserve_decimal_operands_under_low_decimal_precision():
    grid = _grid()
    observations = _observations(grid, function=lambda levels:
        D("0.1000000000000000000000000000001") if levels == (1, 1, 1) else D(0))
    original = observations[-2].value
    with localcontext() as context:
        context.prec = 2
        group, = factorial_group_contrasts(grid, ("group.one",), observations, pair_scale=SIGNED).groups
    exact = Fraction(1000000000000000000000000000001, 10**31)
    assert group.main_effects == (exact / 4,) * 3
    assert group.pair_interactions == (exact / 4,) * 3
    assert group.three_way == exact / 4 and group.curvature == -exact / 8
    retained = next(row for row in group.observations if row.coordinate.levels == (1, 1, 1))
    assert retained.value is original


@pytest.mark.parametrize("group_count", (1, 3, 32, 64))
def test_group_denominator_is_declared_count_and_never_nine_times_count(group_count):
    grid = _grid()
    group_ids = tuple("group." + str(index).zfill(3) for index in range(group_count))
    result = factorial_group_contrasts(grid, group_ids, _observations(grid, group_ids), pair_scale=SIGNED)
    assert result.group_count == result.complete_group_count == group_count
    assert tuple(row.group_id for row in result.groups) == group_ids
    assert sum(row.observed_coordinate_count for row in result.groups) == 9 * group_count


@pytest.mark.parametrize("value", (None, D("NaN"), D("sNaN"), D("Infinity"), D("-Infinity")))
@pytest.mark.parametrize("coordinate_at", (0, 8))
def test_missing_or_nonfinite_corner_or_center_makes_the_entire_group_unevaluable(value, coordinate_at):
    grid = _grid()
    observations = _observations(grid)
    changed = replace(observations[coordinate_at], value=value)
    observations = (*observations[:coordinate_at], changed, *observations[coordinate_at + 1:])
    reduction = factorial_group_contrasts(grid, ("group.one",), observations, pair_scale=SIGNED)
    group, = reduction.groups
    assert reduction.group_count == reduction.unevaluable_group_count == 1
    assert reduction.complete_group_count == 0 and group.observed_coordinate_count == 9
    assert group.finite_coordinate_count == 8
    assert group.disposition is FactorialDisposition.UNEVALUABLE
    assert group.main_effects == group.pair_interactions == (None, None, None)
    assert group.three_way is None and group.curvature is None
    assert (group.missing_coordinate_ids, group.nonfinite_coordinate_ids) == (
        ((changed.coordinate.coordinate_id,), ()) if value is None else ((), (changed.coordinate.coordinate_id,)))
    retained = next(row for row in group.observations if row.coordinate == changed.coordinate)
    assert retained.value is value


def test_absent_rows_and_an_entire_missing_group_remain_in_the_full_roster():
    grid = _grid()
    group_ids = ("group.first", "group.second", "group.unobserved")
    rows = _observations(grid, group_ids[:2])
    rows = (replace(rows[0], value=None), *rows[2:])
    result = factorial_group_contrasts(grid, group_ids, rows, pair_scale=SIGNED)
    first, second, absent = result.groups
    assert result.group_count == 3 and result.complete_group_count == 1 and result.unevaluable_group_count == 2
    assert first.observed_coordinate_count == 8 and first.finite_coordinate_count == 7
    assert first.missing_coordinate_ids == tuple(sorted((grid.coordinates[0].coordinate_id, grid.coordinates[1].coordinate_id)))
    assert second.disposition is FactorialDisposition.FINITE
    assert absent.observed_coordinate_count == absent.finite_coordinate_count == 0
    assert absent.expected_coordinate_count == 9
    assert absent.missing_coordinate_ids == tuple(sorted(row.coordinate_id for row in grid.coordinates))
    assert absent.main_effects == (None, None, None)


def test_observation_order_cannot_change_exact_results_or_factor_orientation():
    grid = _grid()
    rows = _observations(grid)
    ordinary = factorial_group_contrasts(grid, ("group.one",), rows, pair_scale=SIGNED)
    reordered = factorial_group_contrasts(replace(grid, coordinates=tuple(reversed(grid.coordinates))),
        ("group.one",), tuple(reversed(rows)), pair_scale=SIGNED)
    assert ordinary.groups == reordered.groups


@pytest.mark.parametrize("damage", ("duplicate", "foreign-group", "foreign-coordinate", "wrong-levels"))
def test_duplicate_or_mismatched_observations_are_refused_instead_of_reduced(damage):
    grid = _grid()
    rows = _observations(grid)
    if damage == "duplicate":
        rows = (*rows, rows[0])
    elif damage == "foreign-group":
        rows = (replace(rows[0], group_id="group.unassigned"), *rows[1:])
    elif damage == "foreign-coordinate":
        rows = (replace(rows[0], coordinate=replace(rows[0].coordinate, coordinate_id="coordinate.unassigned")), *rows[1:])
    else:
        rows = (replace(rows[0], coordinate=replace(rows[0].coordinate, levels=(1, 1, 1))), *rows[1:])
    with pytest.raises(ValueError):
        factorial_group_contrasts(grid, ("group.one",), rows, pair_scale=SIGNED)


@pytest.mark.parametrize("levels", ((0, 1, -1), (0, 0, 1), (True, 1, 1), (-1, 1), [-1, -1, -1]))
def test_coordinates_refuse_partial_centers_boolean_levels_and_incomplete_axes(levels):
    with pytest.raises(ValueError):
        FactorialCoordinate("coordinate.invalid", levels)


@pytest.mark.parametrize("damage", ("missing-center", "duplicate-center", "duplicate-id", "two-factors", "repeated-factor"))
def test_grid_requires_the_exact_distinct_three_factor_cube_plus_center(damage):
    grid = _grid()
    with pytest.raises(ValueError):
        if damage == "missing-center":
            replace(grid, coordinates=grid.coordinates[:-1])
        elif damage == "duplicate-center":
            replace(grid, coordinates=(replace(grid.coordinates[-1], coordinate_id="another.center"), *grid.coordinates[1:]))
        elif damage == "duplicate-id":
            replace(grid, coordinates=(replace(grid.coordinates[0], coordinate_id=grid.coordinates[1].coordinate_id), *grid.coordinates[1:]))
        elif damage == "two-factors":
            replace(grid, factor_ids=grid.factor_ids[:2])
        else:
            replace(grid, factor_ids=("temperature", "temperature", "coupling"))


@pytest.mark.parametrize("value", (1, 1., Fraction(1), True, "1"))
def test_observations_refuse_inexact_or_untyped_numeric_operands(value):
    with pytest.raises(TypeError):
        FactorialObservation("group.one", _grid().coordinates[0], value)


@pytest.mark.parametrize("scale", (None, "SIGNED_MEAN_DIFFERENCE", False))
def test_pair_scale_is_required_and_exactly_typed(scale):
    grid = _grid()
    with pytest.raises(TypeError):
        factorial_group_contrasts(grid, ("group.one",), _observations(grid), pair_scale=scale)
    with pytest.raises(TypeError):
        factorial_group_contrasts(grid, ("group.one",), _observations(grid))


@pytest.mark.parametrize("group_ids", ((), ("group.one", "group.one"), ["group.one"], ("",)))
def test_declared_group_census_cannot_be_empty_duplicated_or_mutable(group_ids):
    with pytest.raises(ValueError):
        factorial_group_contrasts(_grid(), group_ids, (), pair_scale=SIGNED)


def test_plain_results_and_coordinates_are_frozen():
    grid = _grid()
    reduction = factorial_group_contrasts(grid, ("group.one",), _observations(grid), pair_scale=SIGNED)
    for record, field, value in ((grid.coordinates[0], "levels", (1, 1, 1)),
                                 (reduction, "group_ids", ("replacement",)),
                                 (reduction.groups[0], "curvature", Fraction(99))):
        with pytest.raises(FrozenInstanceError):
            setattr(record, field, value)


def _holm(values, *, alpha=Fraction(1, 20)):
    ids = tuple("comparison." + str(index).zfill(2) for index in range(len(values)))
    return holm_adjustment(ids, tuple(zip(ids, values, strict=True)), alpha=alpha)


def test_holm_adjusted_values_have_independent_hand_rational_oracles():
    result = _holm((Fraction(1, 100), Fraction(1, 25), Fraction(3, 100), Fraction(1, 5)))
    # Sorted raw products:4*.01=.04,3*.03=.09,2*.04=.08,1*.2=.2.
    assert tuple(row.adjusted_p_value for row in result.comparisons) == (
        Fraction(1, 25), Fraction(9, 100), Fraction(9, 100), Fraction(1, 5))
    assert tuple(row.stepdown_rank for row in result.comparisons) == (1, 3, 2, 4)
    assert tuple(row.rejected for row in result.comparisons) == (True, False, False, False)


def test_holm_later_small_raw_probabilities_cannot_skip_an_earlier_failed_step():
    result = _holm((Fraction(1, 100), Fraction(1, 50), Fraction(3, 125), Fraction(13, 500)))
    assert tuple(row.adjusted_p_value for row in result.comparisons) == (
        Fraction(1, 25), Fraction(3, 50), Fraction(3, 50), Fraction(3, 50))
    assert tuple(row.rejected for row in result.comparisons) == (True, False, False, False)
    assert result.comparisons[2].p_value < result.comparisons[2].critical_alpha
    assert result.comparisons[3].p_value < result.comparisons[3].critical_alpha


def test_unevaluable_reserved_slots_never_reallocate_the_family_size():
    result = _holm((Fraction(13, 1000), None, None, None))
    assert result.family_size == 4 and result.evaluated_count == 1 and result.unevaluable_count == 3
    finite, *unused = result.comparisons
    assert finite.adjusted_p_value == Fraction(13, 250) and not finite.rejected
    assert finite.critical_alpha == Fraction(1, 80)
    assert all(row.disposition is HolmDisposition.UNEVALUABLE and row.p_value is None
        and row.adjusted_p_value is None and row.stepdown_rank is None and row.critical_alpha is None
        and not row.rejected for row in unused)
    assert _holm((Fraction(13, 1000),)).comparisons[0].rejected


@pytest.mark.parametrize("family_size,adjusted,rejected", ((1, Fraction(1, 100), True),
    (4, Fraction(1, 25), True), (12, Fraction(3, 25), False)))
def test_family_count_is_explicit_and_changes_adjustment_without_a_twelve_slot_default(family_size, adjusted, rejected):
    result = _holm((Fraction(1, 100), *(None for _ in range(family_size - 1))))
    assert result.family_size == family_size
    assert result.comparisons[0].adjusted_p_value == adjusted
    assert result.comparisons[0].rejected is rejected


def test_ties_have_identical_adjusted_values_and_stable_identifier_order():
    result = holm_adjustment(("comparison.z", "comparison.a", "comparison.m"),
        (("comparison.z", Fraction(1, 100)), ("comparison.m", Fraction(1, 50)),
         ("comparison.a", Fraction(1, 100))), alpha=Fraction(1, 20))
    assert tuple(row.adjusted_p_value for row in result.comparisons) == (Fraction(3, 100),) * 3
    assert tuple(row.stepdown_rank for row in result.comparisons) == (2, 1, 3)
    assert tuple(row.comparison_id for row in result.comparisons) == result.family_ids


def test_endpoint_probabilities_inclusive_boundary_and_cap_at_one_are_exact():
    result = _holm((Fraction(0), Fraction(1), None))
    assert result.comparisons[0].rejected and result.comparisons[0].adjusted_p_value == 0
    assert not result.comparisons[1].rejected and result.comparisons[1].adjusted_p_value == 1
    boundary = _holm((Fraction(1, 40), None))
    assert boundary.comparisons[0].adjusted_p_value == Fraction(1, 20) and boundary.comparisons[0].rejected
    assert not _holm((Fraction(1, 40) + Fraction(1, 100000), None)).comparisons[0].rejected


def test_decimal_probabilities_and_alpha_are_exact_under_low_precision():
    with localcontext() as context:
        context.prec = 2
        result = _holm((D("0.010000000000000000000000000001"), None), alpha=D("0.05"))
    assert result.alpha == Fraction(1, 20)
    assert result.comparisons[0].adjusted_p_value == Fraction(10000000000000000000000000001, 10**30) * 2


def test_all_unevaluable_family_is_retained_without_rejection():
    result = _holm((None, None, None))
    assert result.family_size == result.unevaluable_count == 3 and result.evaluated_count == 0
    assert all(row.disposition is HolmDisposition.UNEVALUABLE for row in result.comparisons)


@pytest.mark.parametrize("value", (D("NaN"), D("sNaN"), D("Infinity"), D("-Infinity"),
    Fraction(-1, 100), Fraction(101, 100), 0, 0.1, True, "0.1"))
def test_holm_refuses_invalid_or_inexact_probabilities(value):
    with pytest.raises((ValueError, TypeError)):
        _holm((value,))


@pytest.mark.parametrize("alpha", (None, D("NaN"), D("Infinity"), Fraction(0), Fraction(1),
    Fraction(-1), 0.05, True, "0.05"))
def test_holm_requires_an_explicit_valid_exact_family_alpha(alpha):
    with pytest.raises((ValueError, TypeError)):
        _holm((Fraction(1, 100),), alpha=alpha)


@pytest.mark.parametrize("family,values", (
    ((), ()), (("comparison.a", "comparison.a"), (("comparison.a", Fraction(1, 100)),)),
    (("comparison.a", "comparison.b"), (("comparison.a", Fraction(1, 100)),)),
    (("comparison.a",), (("comparison.a", Fraction(1, 100)), ("comparison.a", None))),
    (("comparison.a",), (("comparison.foreign", Fraction(1, 100)),)),
    (["comparison.a"], (("comparison.a", Fraction(1, 100)),)),
    (("comparison.a",), [("comparison.a", Fraction(1, 100))]),
))
def test_holm_cannot_hide_drop_duplicate_or_extend_a_predeclared_family(family, values):
    with pytest.raises(ValueError):
        holm_adjustment(family, values, alpha=Fraction(1, 20))
