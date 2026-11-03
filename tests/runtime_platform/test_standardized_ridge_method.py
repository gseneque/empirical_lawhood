# SPDX-License-Identifier: MPL-2.0
"""Independent small ridge equations and missing-target denominators."""

from decimal import Decimal as D

import pytest

from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.runtime.experimental_statistics import (
    StandardizedRidgeParameters, fit_standardized_ridge, predict_standardized_ridge,
)


def test_independent_two_row_equations_and_unpenalized_intercept():
    # Sum x=0, sum x²=2: intercept=2 and slope=2/(2+lambda).
    model = fit_standardized_ridge(((D(-1),), (D(1),)), (D(1), D(3)), penalty=D(1))
    assert model.coefficients[0] == D(2)
    assert abs(model.coefficients[1] - D(2)/D(3)) < D("1e-15")
    assert abs(predict_standardized_ridge(model, (D(1),)) - D(8)/D(3)) < D("1e-15")
    assert (model.training_rows, model.fitted_rows) == (2, 2)


def test_literal_constant_column_and_raw_intercept_mean():
    model = fit_standardized_ridge(((D(7),), (D(7),)), (D(1), D(3)), penalty=D(1))
    assert model.means == (D(7),)
    assert model.scales == (D(1),)
    assert model.zero_variance_mask == (True,)
    assert model.coefficients == (D(2), D(0))
    assert predict_standardized_ridge(model, (D(7),)) == D(2)


def test_standardization_keeps_feature_row_with_missing_target():
    # All three feature rows give variance6. Fitted two-row normal equations
    # give prediction3 +/- 9/4. Dropping the middle feature before scaling gives
    # a different prediction and therefore cannot pass this oracle.
    model = fit_standardized_ridge(((D(-3),), (D(0),), (D(3),)),
                                   (D(0), None, D(6)), penalty=D(1))
    assert abs(model.scales[0]**2 - D(6)) < D("1e-14")
    assert abs(predict_standardized_ridge(model, (D(3),)) - D("5.25")) < D("1e-14")
    assert (model.training_rows, model.fitted_rows) == (3, 2)


def test_no_finite_target_is_retained_as_no_fit():
    model = fit_standardized_ridge(((D(-1),), (D(1),)), (None, None), penalty=D(1))
    assert model.coefficients is None
    assert (model.training_rows, model.fitted_rows) == (2, 0)
    assert predict_standardized_ridge(model, (D(1),)) is None
    assert decode_canonical_bytes(model.canonical_bytes(), StandardizedRidgeParameters,
                                  maximum_bytes=None) == model


@pytest.mark.parametrize("value", [D("NaN"), D("Infinity"), D("1e1000")])
def test_nonfinite_or_unrepresentable_observation_refuses(value):
    with pytest.raises(ValueError):
        fit_standardized_ridge(((value,),), (D(1),), penalty=D(1))


def test_explicit_intercept_penalty_changes_declared_fit():
    model = fit_standardized_ridge(((D(7),), (D(7),)), (D(1), D(3)),
                                   penalty=D(1), penalize_intercept=True)
    assert abs(model.coefficients[0] - D(4)/D(3)) < D("1e-15")


def test_positive_decimal_penalty_that_underflows_refuses_before_solve():
    with pytest.raises(ValueError, match="penalty is numerically unrepresentable"):
        fit_standardized_ridge(((D(1),), (D(1),)), (D(2), D(3)), penalty=D("1e-999"))
