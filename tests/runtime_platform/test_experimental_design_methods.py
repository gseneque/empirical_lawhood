# SPDX-License-Identifier: MPL-2.0
"""Independent exact design/reduction checks; no scientific qualification."""

from dataclasses import replace
from decimal import Decimal, localcontext
from fractions import Fraction
from itertools import product
from pathlib import Path

import pytest

from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.experimental_design import (
    IndependentUnit,
    UnitAllocation,
    UnitRoleAssignment,
    require_disjoint_allocations,
)
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.planning.recursive_authoring import RecursiveStudyDraft
from empirical_lawhood.runtime.experiment_preparation import (
    DependencyKind,
    ExecutionSelection,
    ExperimentCensus,
    ExperimentDependency,
    ExperimentPreparation,
)
from empirical_lawhood.runtime.experimental_statistics import (
    binomial_minimum_successes,
    binomial_upper_tail,
    calibration_rank,
    raw_median,
    split_upper_calibration,
)


D = Decimal
ROOT = Path(__file__).resolve().parents[2]


def _source(name="source.fixture", fingerprint="a" * 64):
    return ObjectIdentity(name, "empirical-lawhood/testing/selected-source", "1.0.0", fingerprint)


def _allocation():
    source = _source()
    units = tuple(
        IndependentUnit(f"unit.{index}", source.object_id, "family.fixture", ("view.coarse", "view.fine"), index < 2)
        for index in range(4)
    )
    roles = tuple(UnitRoleAssignment(unit.unit_id, role) for unit, role in zip(
        units, ("train", "train", "calibration", "confirmation"), strict=True))
    return UnitAllocation("allocation.fixture", (source,), units, roles)


def _census():
    return ExperimentCensus(
        (("calibration", 1), ("confirmation", 1), ("train", 2)),
        (("train", 2),), (("fit", 1),), (("model", 1),), 0,
    )


def test_allocation_canonical_roundtrip_preserves_exact_sources_and_role_census():
    allocation = _allocation()
    payload = allocation.canonical_bytes()
    recovered = decode_canonical_bytes(payload, UnitAllocation, maximum_bytes=len(payload))
    assert recovered == allocation
    assert recovered.canonical_bytes() == payload
    assert recovered.identity == allocation.identity
    assert recovered.sources == (_source(),)
    assert recovered.unit_ids() == ("unit.0", "unit.1", "unit.2", "unit.3")
    assert recovered.unit_ids("train") == ("unit.0", "unit.1")
    assert recovered.unit_ids("reserved-transfer") == ()
    assert recovered.role_counts == (("calibration", 1), ("confirmation", 1), ("train", 2))
    assert tuple(unit.exposed for unit in recovered.units) == (True, True, False, False)


def test_nested_views_change_instance_identity_without_inflating_independent_units():
    allocation = _allocation()
    original = allocation.canonical_bytes()
    expanded = replace(allocation, units=tuple(replace(unit, numerical_view_ids=(
        "view.coarse", "view.fine", "view.refined", "view.secondary")) for unit in allocation.units))
    assert sum(len(unit.numerical_view_ids) for unit in allocation.units) == 8
    assert sum(len(unit.numerical_view_ids) for unit in expanded.units) == 16
    assert expanded.unit_ids() == allocation.unit_ids()
    assert expanded.role_counts == allocation.role_counts
    assert expanded.identity != allocation.identity
    assert allocation.canonical_bytes() == original


@pytest.mark.parametrize("mutation", ("duplicate", "missing", "foreign", "unsorted", "repeated-role"))
def test_roles_cannot_duplicate_drop_or_assign_one_unit_twice(mutation):
    allocation = _allocation()
    roles = allocation.roles
    changed = {
        "duplicate": (roles[0], roles[0], *roles[2:]),
        "missing": roles[:-1],
        "foreign": (*roles[:-1], UnitRoleAssignment("unit.foreign", "confirmation")),
        "unsorted": tuple(reversed(roles)),
        "repeated-role": (*roles, UnitRoleAssignment(roles[0].unit_id, "confirmation")),
    }[mutation]
    with pytest.raises(ValueError, match="every unit exactly once"):
        replace(allocation, roles=changed)


@pytest.mark.parametrize("mutation", ("duplicate-unit", "missing-source", "duplicate-source", "no-sources"))
def test_allocation_requires_complete_unique_units_and_actual_source_references(mutation):
    allocation = _allocation()
    changes = {
        "duplicate-unit": {"units": (allocation.units[0], allocation.units[0], *allocation.units[2:])},
        "missing-source": {"units": (replace(allocation.units[0], source_id="source.absent"), *allocation.units[1:])},
        "duplicate-source": {"sources": (allocation.sources[0], _source(fingerprint="b" * 64))},
        "no-sources": {"sources": ()},
    }[mutation]
    with pytest.raises(ValueError):
        replace(allocation, **changes)


def test_disjointness_checks_units_across_all_allocations_not_only_adjacent_pairs():
    first = _allocation()
    second = replace(first, allocation_id="allocation.second",
        units=tuple(replace(unit, unit_id=f"next.{index}") for index, unit in enumerate(first.units)),
        roles=tuple(replace(role, unit_id=f"next.{index}") for index, role in enumerate(first.roles)))
    require_disjoint_allocations(first, second)
    with pytest.raises(ValueError, match="overlap"):
        require_disjoint_allocations(first, second, replace(first, allocation_id="allocation.alias"))


@pytest.mark.parametrize("views", (("view.fine", "view.coarse"), ("view.coarse", "view.coarse")))
def test_nested_view_roster_must_be_unique_and_ordered(views):
    with pytest.raises(ValueError, match="unique nested views"):
        replace(_allocation().units[0], numerical_view_ids=views)


def test_binomial64_gate_uses_exact_tail_counts_on_both_sides_of_43():
    # Coefficients of (1+x)^64 count equiprobable binary outcome strings.
    # This recurrence enumerates counts independently of the production comb.
    counts = [1]
    for _ in range(64):
        counts = [left + right for left, right in zip([0, *counts], [*counts, 0], strict=True)]
    assert sum(counts) == 18_446_744_073_709_551_616
    assert sum(counts[42:]) == 155_489_358_646_406_149
    assert sum(counts[43:]) == 75_141_910_203_168_229
    tail42 = Fraction(155_489_358_646_406_149, 18_446_744_073_709_551_616)
    tail43 = Fraction(75_141_910_203_168_229, 18_446_744_073_709_551_616)
    assert binomial_upper_tail(64, 42, Fraction(1, 2)) == tail42
    assert binomial_upper_tail(64, 43, Fraction(1, 2)) == tail43
    assert tail43 <= Fraction(1, 240) < tail42
    assert binomial_minimum_successes(64, Fraction(1, 2), Fraction(1, 240)) == 43


def test_binomial8_gate_matches_exhaustive_binary_outcomes():
    outcomes = tuple(product((False, True), repeat=8))
    for threshold in range(10):
        expected = Fraction(sum(sum(row) >= threshold for row in outcomes), 256)
        assert binomial_upper_tail(8, threshold, Fraction(1, 2)) == expected
    assert binomial_upper_tail(8, 7, Fraction(1, 2)) == Fraction(9, 256)
    assert binomial_upper_tail(8, 8, Fraction(1, 2)) == Fraction(1, 256)
    assert binomial_minimum_successes(8, Fraction(1, 2), Fraction(1, 240)) == 8


def test_binomial_probability_endpoints_keep_impossible_success_threshold_explicit():
    assert binomial_upper_tail(8, 0, Fraction(0)) == 1
    assert binomial_upper_tail(8, 1, Fraction(0)) == 0
    assert binomial_minimum_successes(8, Fraction(0), Fraction(1, 240)) == 1
    assert binomial_upper_tail(8, 8, Fraction(1)) == 1
    assert binomial_upper_tail(8, 9, Fraction(1)) == 0
    assert binomial_minimum_successes(8, Fraction(1), Fraction(1, 240)) == 9


@pytest.mark.parametrize("alpha", (Fraction(1, 20), D(".05")))
def test_calibration_ranks_preserve_exact_finite_and_unattainable_boundaries(alpha):
    assert calibration_rank(64, alpha) == 62  # 65*19/20 = 61.75.
    assert calibration_rank(20, alpha) == 20  # 21*19/20 = 19.95.
    assert calibration_rank(19, alpha) == 19  # Exact integer boundary, 20*19/20.
    assert calibration_rank(16, alpha) == 17  # No finite 17th score in 16 units.
    assert calibration_rank(1, alpha) == 2


@pytest.mark.parametrize("missing", (0, 1, 2, 3, 4, 64))
def test_missing_calibration_units_remain_in_denominator_and_can_force_infinity(missing):
    finite = tuple(D(index) for index in reversed(range(64 - missing)))
    scores = (None,) * missing + finite
    calibration = split_upper_calibration(scores, Fraction(1, 20))
    assert calibration.unit_count == 64
    assert calibration.rank == 62
    assert calibration.radius == (D("Infinity") if missing >= 3 else D(61))


def test_explicit_infinite_nonuse_and_missing_scores_have_identical_rank_effect():
    finite = tuple(D(index) for index in range(61))
    missing = split_upper_calibration((*finite, None, None, None), Fraction(1, 20))
    nonuse = split_upper_calibration((*finite, D("Infinity"), D("Infinity"), D("Infinity")), Fraction(1, 20))
    assert missing == nonuse
    assert missing.radius.is_infinite()
    assert split_upper_calibration((D(0),) * 16, Fraction(1, 20)).radius.is_infinite()
    assert split_upper_calibration(tuple(D(index) for index in range(20)), Fraction(1, 20)).radius == D(19)


def test_raw_median_uses_original_units_and_even_midpoint():
    assert raw_median((D(0), D(3))) == D("1.5")
    assert raw_median((D(3), D(0))) == D("1.5")
    assert raw_median((D(7), D(2), D(3))) == D(3)
    assert raw_median((D("-3.00"), D("0.10"))) == D("-1.45")


@pytest.mark.parametrize("precision", (2, 6, 28))
def test_raw_even_median_preserves_exact_decimal_value_in_caller_context(precision):
    values = (D("123456789012345678901234567890.123456789"),
              D("123456789012345678901234567890.12345679"))
    expected = D("123456789012345678901234567890.1234567895")
    exact = sum((Fraction(value) for value in values), Fraction(0)) / 2
    with localcontext() as context:
        context.prec = precision
        observed = raw_median(values)
    assert observed == expected and Fraction(observed) == exact


@pytest.mark.parametrize("count", (0, -1, True, False, 1.5, "64"))
def test_invalid_whole_unit_denominators_refuse(count):
    for reduce in (
        lambda: calibration_rank(count, Fraction(1, 20)),
        lambda: binomial_upper_tail(count, 0, Fraction(1, 2)),
        lambda: binomial_minimum_successes(count, Fraction(1, 2), Fraction(1, 20)),
    ):
        with pytest.raises(ValueError, match="whole-unit denominator"):
            reduce()


@pytest.mark.parametrize("successes", (-1, 10, True, 1.5, "8"))
def test_invalid_success_census_refuses(successes):
    with pytest.raises(ValueError, match="success census"):
        binomial_upper_tail(8, successes, Fraction(1, 2))


@pytest.mark.parametrize("probability", (Fraction(-1, 2), Fraction(3, 2), D("-.01"), D("1.01")))
def test_probabilities_outside_unit_interval_refuse(probability):
    for reduce in (
        lambda: calibration_rank(64, probability),
        lambda: binomial_upper_tail(8, 8, probability),
        lambda: binomial_minimum_successes(8, probability, Fraction(1, 20)),
    ):
        with pytest.raises(ValueError, match="probability"):
            reduce()


@pytest.mark.parametrize("alpha", (Fraction(0), Fraction(1), D(0), D(1)))
def test_error_probability_endpoints_do_not_create_calibration_or_test_warrants(alpha):
    with pytest.raises(ValueError, match="probability"):
        calibration_rank(64, alpha)
    with pytest.raises(ValueError, match="probability"):
        binomial_minimum_successes(8, Fraction(1, 2), alpha)


@pytest.mark.parametrize("probability", (.05, 0, 1, True, ".05"))
def test_inexact_or_untyped_probabilities_refuse(probability):
    with pytest.raises(TypeError, match="exact Fraction or Decimal"):
        calibration_rank(64, probability)
    with pytest.raises(TypeError, match="exact Fraction or Decimal"):
        binomial_upper_tail(8, 8, probability)


@pytest.mark.parametrize("probability", (D("NaN"), D("sNaN"), D("Infinity"), D("-Infinity")))
def test_nonfinite_probabilities_are_controlled_value_refusals(probability):
    with pytest.raises(ValueError):
        calibration_rank(64, probability)
    with pytest.raises(ValueError):
        binomial_upper_tail(8, 8, probability)
    with pytest.raises(ValueError):
        binomial_minimum_successes(8, Fraction(1, 2), probability)


@pytest.mark.parametrize("scores", ((), (D(-1),), (D("NaN"),), (D("-Infinity"),), (0,), ("0",)))
def test_empty_negative_nonfinite_or_untyped_calibration_scores_refuse(scores):
    with pytest.raises(ValueError):
        split_upper_calibration(scores, Fraction(1, 20))


def test_mutable_calibration_roster_cannot_change_the_frozen_denominator():
    with pytest.raises(TypeError, match="immutable complete score roster"):
        split_upper_calibration([D(0)] * 64, Fraction(1, 20))


@pytest.mark.parametrize("values", ((), (D("NaN"),), (D("Infinity"),), (0,), [D(0), D(3)]))
def test_median_requires_immutable_finite_raw_decimal_observations(values):
    with pytest.raises(ValueError, match="finite raw observations"):
        raw_median(values)


def test_pure_preparation_retains_specific_dependencies_without_execution_or_authority():
    dependencies = tuple(ExperimentDependency("missing." + kind.value.lower(), kind,
        "The selected prerequisite remains unavailable.", "source.selected")
        for kind in sorted(DependencyKind, key=lambda kind: kind.value))
    prepared = ExperimentPreparation(_source("specification.fixture"), _census(), dependencies, _allocation())
    assert {dependency.kind for dependency in prepared.dependencies} == {
        DependencyKind.SOFTWARE, DependencyKind.SCIENTIFIC_EVIDENCE, DependencyKind.AUTHORITY,
        DependencyKind.EXTERNAL_INPUT, DependencyKind.ENVIRONMENT, DependencyKind.STORAGE,
    }
    assert prepared.census.resolved_role_counts == (("train", 2),)
    assert prepared.census.native_effect_count == 0
    assert prepared.draft is None and not prepared.executable
    # Removing dependency descriptions supplies neither an executable graph nor authority.
    assert not replace(prepared, dependencies=()).executable


def test_compiled_preparation_keeps_dependencies_and_requires_an_allocation():
    raw = (ROOT / "programmes/biology/photosynthesis/workflows/rubisco-kinetic-join/draft.json").read_bytes()
    draft = decode_canonical_bytes(raw, RecursiveStudyDraft, maximum_bytes=len(raw))
    prepared = ExperimentPreparation(_source("specification.fixture"), _census(), (), _allocation(), draft,
        execution=ExecutionSelection(workers=1))
    assert prepared.executable
    assert not replace(prepared, execution=None).executable
    assert not replace(prepared, execution=ExecutionSelection()).executable
    with pytest.raises(ValueError, match="immutable allocation"):
        replace(prepared, allocation=None)
    missing_method = ExperimentDependency("missing.method", DependencyKind.SOFTWARE, "The selected operation is not installed.")
    blocked = replace(prepared, dependencies=(missing_method,))
    assert blocked.draft is draft
    assert blocked.dependencies == (missing_method,)
    assert not blocked.executable


@pytest.mark.parametrize("resolved", ((("train", 3),), (("unknown", 1),)))
def test_preparation_census_keeps_all_actual_units_when_domain_reports_mismatch(resolved):
    census = replace(_census(), resolved_role_counts=resolved)
    discrepancy = ExperimentDependency("mismatched.roles", DependencyKind.SCIENTIFIC_EVIDENCE,
        "Actual source units do not match the selected domain roles.")
    prepared = ExperimentPreparation(_source("specification.fixture"), census, (discrepancy,))
    assert prepared.census.resolved_role_counts == resolved
    assert prepared.census.role_counts == (("calibration", 1), ("confirmation", 1), ("train", 2))
    assert not prepared.executable


@pytest.mark.parametrize("count", (-1, True, 1.5))
def test_preparation_census_and_execution_reject_invalid_counts(count):
    with pytest.raises(ValueError):
        replace(_census(), operation_counts=(("fit", count),))
    with pytest.raises(ValueError):
        replace(_census(), native_effect_count=count)
    with pytest.raises(ValueError):
        ExecutionSelection(workers=count)


def test_untyped_or_duplicate_preparation_dependencies_refuse():
    dependency = ExperimentDependency("missing.method", DependencyKind.SOFTWARE, "Method absent.")
    with pytest.raises(ValueError, match="category"):
        replace(dependency, kind="SOFTWARE")
    with pytest.raises(ValueError, match="category"):
        replace(dependency, detail="")
    with pytest.raises(ValueError, match="uniquely identified"):
        ExperimentPreparation(_source("specification.fixture"), _census(), (dependency, dependency))
