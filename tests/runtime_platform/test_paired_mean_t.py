# SPDX-License-Identifier: MPL-2.0
"""Analytic low-df falsifiers, exact moments and complete-unit adverse census."""

from decimal import Decimal, localcontext
from fractions import Fraction

import pytest

from empirical_lawhood.runtime.experimental_statistics import (
    PairedMeanTAlternative as Alternative,
    PairedMeanTDisposition as Disposition,
    paired_mean_t,
)


def calculate(values, *, null=Fraction(0), alternative=Alternative.TWO_SIDED_POINT_NULL):
    return paired_mean_t(tuple(f"group.{index}" for index in range(len(values))), tuple(values),
        null_value=null, alternative=alternative)


@pytest.mark.parametrize("alternative,expected", ((Alternative.TWO_SIDED_POINT_NULL, Decimal(".5")),
    (Alternative.GREATER, Decimal(".25")), (Alternative.LESS, Decimal(".75"))))
def test_df1_cauchy_integral_at_one(alternative, expected):
    # With observations 0,2, mean=1 and unbiased variance=2, t=1.
    # Cauchy F(1)=1/2+atan(1)/pi=3/4, independent of a Student implementation.
    result = calculate((Fraction(0), Decimal(2)), alternative=alternative)
    assert result.mean == 1 and result.sample_variance == 2
    assert result.statistic == 1 and result.degrees_of_freedom == 1
    assert abs(result.p_value-expected) < Decimal("2e-15")
    assert result.disposition is Disposition.CONDITIONAL_NUMERIC_RESULT


def test_df2_closed_density_integral_at_two():
    # n=3: mean 2/3, variance 1/3 -> t=2. Integrating the df2 density
    # gives F(t)=1/2+t/(2*sqrt(t*t+2)), so two-sided tail=1-2/sqrt(6).
    result = calculate((Fraction(0), Fraction(1), Fraction(1)))
    with localcontext() as context:
        context.prec = 70
        expected = 1-Decimal(2)/Decimal(6).sqrt()
    assert result.mean == Fraction(2, 3) and result.sample_variance == Fraction(1, 3)
    assert result.statistic == 2 and result.degrees_of_freedom == 2
    assert abs(result.p_value-expected) < Decimal("2e-15")


@pytest.mark.parametrize("alternative,expected", ((Alternative.TWO_SIDED_POINT_NULL, ".5"),
    (Alternative.GREATER, ".75"), (Alternative.LESS, ".25")))
def test_declared_null_or_one_sided_margin_changes_sign_without_absolute_margin_claim(alternative, expected):
    result = calculate((Decimal(0), Decimal(2)), null=Decimal(2), alternative=alternative)
    assert result.statistic == -1 and result.null_value == 2
    assert abs(result.p_value-Decimal(expected)) < Decimal("2e-15")


@pytest.mark.parametrize("alternative,expected", ((Alternative.TWO_SIDED_POINT_NULL, "1"),
    (Alternative.GREATER, ".5"), (Alternative.LESS, ".5")))
def test_exact_null_has_unit_two_sided_tail_and_half_one_sided_tails(alternative, expected):
    result = calculate((Decimal(0), Decimal(2)), null=Fraction(1), alternative=alternative)
    assert result.statistic == 0 and result.p_value == Decimal(expected)


def test_fraction_moments_remain_exact_under_low_decimal_context():
    with localcontext() as context:
        context.prec = 2
        result = calculate((Fraction(1, 3), Fraction(2, 3), Fraction(4, 3)))
    assert result.mean == Fraction(7, 9) and result.sample_variance == Fraction(7, 27)


@pytest.mark.parametrize("count", (2, 3, 8, 32, 64))
def test_actual_assigned_denominator_and_df_are_whole_groups(count):
    result = calculate(tuple(Fraction(index) for index in range(count)))
    assert result.assigned_count == result.finite_count == count
    assert result.degrees_of_freedom == count-1
    assert result.mean == Fraction(count-1, 2)
    assert result.sample_variance == Fraction(count*(count+1), 12)


@pytest.mark.parametrize("bad,reason", ((None, "MISSING_ASSIGNED_GROUP"),
    (Decimal("Infinity"), "NONFINITE_ASSIGNED_GROUP"), (Decimal("-Infinity"), "NONFINITE_ASSIGNED_GROUP"),
    (Decimal("NaN"), "NONFINITE_ASSIGNED_GROUP"), (Decimal("sNaN"), "NONFINITE_ASSIGNED_GROUP")))
def test_one_unevaluable_unit_never_generates_finite_only_moments_or_pvalue(bad, reason):
    result = calculate((Fraction(0), bad, Fraction(2)))
    assert result.assigned_count == 3 and result.finite_count == 2 and result.degrees_of_freedom == 2
    assert result.values[1] is bad and result.reason_codes == (reason,)
    assert result.mean is result.sample_variance is result.statistic is result.p_value is None
    assert (result.missing_group_ids if bad is None else result.nonfinite_group_ids) == ("group.1",)


def test_missing_and_nonfinite_reasons_and_labels_are_both_retained():
    result = calculate((None, Decimal("Infinity"), Fraction(2)))
    assert result.finite_count == 1 and result.assigned_count == 3
    assert result.missing_group_ids == ("group.0",) and result.nonfinite_group_ids == ("group.1",)
    assert result.reason_codes == ("MISSING_ASSIGNED_GROUP", "NONFINITE_ASSIGNED_GROUP")


@pytest.mark.parametrize("values,reason,mean,variance", (((Fraction(2),), "INSUFFICIENT_ASSIGNED_GROUPS", Fraction(2), None),
    ((Decimal(2), Decimal(2)), "ZERO_SAMPLE_VARIANCE", Fraction(2), Fraction(0))))
def test_small_census_and_zero_variance_are_explicitly_unevaluable(values, reason, mean, variance):
    result = calculate(values)
    assert result.mean == mean and result.sample_variance == variance
    assert result.p_value is result.statistic is None and result.reason_codes == (reason,)
    assert result.disposition is Disposition.UNEVALUABLE


def test_common_scale_and_location_preserve_standardized_test():
    original = calculate((Fraction(-1), Fraction(2), Fraction(4)))
    shifted = calculate(tuple(Fraction(11)+Fraction(3, 7)*value for value in original.values), null=Fraction(11))
    assert shifted.statistic == original.statistic and shifted.p_value == original.p_value
    assert shifted.sample_variance == Fraction(9, 49)*original.sample_variance


def test_tiny_variance_does_not_underflow_before_standardization():
    original = calculate((Fraction(0), Fraction(2)))
    tiny = calculate((Decimal(0), Decimal("2e-10000")))
    assert tiny.sample_variance > 0
    assert tiny.statistic == original.statistic and tiny.p_value == original.p_value


def test_finite_statistic_with_numerical_zero_tail_is_unevaluable():
    # Relative variation 1e-200 at mean1 has finite t~2e200 (df1).
    # The selected SciPy tail implementation underflows here; never report p=0.
    result = calculate((Fraction(1), Fraction(1)+Fraction(1, 10**200)))
    assert result.mean > 0 and result.sample_variance > 0
    assert result.p_value is result.statistic is None
    assert result.reason_codes == ("NUMERICALLY_UNEVALUABLE_STUDENT_TAIL",)


def test_unrepresentable_statistic_retains_exact_positive_variance():
    result = calculate((Fraction(1), Fraction(1)+Fraction(1, 10**1000)))
    assert result.sample_variance == Fraction(1, 2*10**2000)
    assert result.disposition is Disposition.UNEVALUABLE and result.p_value is None


@pytest.mark.parametrize("operand", (True, False, 1, 1.0, "1", object()))
def test_nonexact_operands_cannot_enter_values_or_null(operand):
    with pytest.raises(TypeError):
        calculate((Fraction(0), operand))
    with pytest.raises(TypeError):
        calculate((Fraction(0), Fraction(1)), null=operand)


@pytest.mark.parametrize("operand", (Decimal("Infinity"), Decimal("NaN"), Decimal("sNaN")))
def test_nonfinite_null_is_refused(operand):
    with pytest.raises(ValueError, match="finite"):
        calculate((Fraction(0), Fraction(1)), null=operand)


@pytest.mark.parametrize("ids,values", (((), ()), (("group.a", "group.a"), (Fraction(0), Fraction(1))),
    (("group.a",), (Fraction(0), Fraction(1))), (("bad id",), (Fraction(0),)),
    ((True,), (Fraction(0),)), (["group.a"], (Fraction(0),)), (("group.a",), [Fraction(0)])))
def test_complete_immutable_unique_group_roster_is_mandatory(ids, values):
    with pytest.raises(ValueError):
        paired_mean_t(ids, values, null_value=Fraction(0), alternative=Alternative.GREATER)


def test_alternative_is_an_explicit_typed_choice():
    with pytest.raises(TypeError):
        calculate((Fraction(0), Fraction(1)), alternative="GREATER")
