# SPDX-License-Identifier: MPL-2.0
"""Pure display controls; no custody, authority, native contact or qualification.

Literal partial menus exercise defensive projection behavior. Current canonical
point consumers independently reject unsupported/inconsistent point records;
these controls do not authenticate the literal test operands as real forecasts.
"""
from copy import deepcopy
from decimal import Decimal as D
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import matrix_selected_scientific_read as reader
from empirical_lawhood.adapters.methods.matrix_experimental_programme.e6_transport_records import METHODS
from empirical_lawhood.adapters.methods.matrix_factor_response.records import PREDICTORS


HORIZONS = (16, 64, 128)
POLICY = SimpleNamespace(endpoint_order=tuple((description, horizon) for description in PREDICTORS
    for horizon in HORIZONS), criterion=SimpleNamespace(normalized_error_maximum=D(".1")))
CASES = (SimpleNamespace(case_id="case.disclosed"),)


def observation(points):
    return (SimpleNamespace(log_points=tuple((method, tuple(points) * len(PREDICTORS)) for method in METHODS)),
        None, None)


@pytest.mark.parametrize("points,expected", (
    (None, ("MISSING_POINT", None, None, None)),
    ((D(0), D(0), D(0)), ("RIGHT_CENSORED", None, None, 128)),
    ((None, None, None), ("FORECAST_NONUSE", 16, None, None)),
    ((D(0), None, None), ("FORECAST_NONUSE", 64, None, None)),
    ((D(0), D(0), None), ("FORECAST_NONUSE", 128, None, None)),
    ((None, D(1), D(1)), ("FORECAST_NONUSE", 16, 64, None)),
    ((D(0), None, D(1)), ("FORECAST_NONUSE", 64, 128, None)),
    ((D(0), D(1), None), ("PREDICTED_FAILURE", 128, 64, None)),
    ((D(1), None, D(1)), ("PREDICTED_FAILURE", 64, 16, None)),
))
def test_finite_lattice_status_keeps_missing_forecasts_and_observed_failures_distinct(points, expected):
    observations = {} if points is None else {CASES[0].case_id: observation(points)}
    before = deepcopy(observations)
    actual = reader._transport_predicted_lifetimes(POLICY, CASES, observations)
    assert actual["scope"] == "DECLARED_FINITE_HORIZON_LATTICE"
    assert actual["standing"] == "DESCRIPTIVE_FROZEN_POINTS_WITHOUT_CONTINUOUS_LIFETIME_OR_QUALIFICATION"
    assert len(actual["rows"]) == len(PREDICTORS) * len(METHODS)
    assert tuple((row["description"], row["method"]) for row in actual["rows"]) == tuple(
        (description, method) for description in PREDICTORS for method in METHODS)
    assert all(row["case_id"] == CASES[0].case_id and row["horizon_ticks"] == list(HORIZONS)
        and (row["status"], row["first_missing_horizon"], row["first_observed_predicted_failure_horizon"],
            row["right_censored_through_horizon"]) == expected for row in actual["rows"])
    assert observations == before


def test_same_legacy_none_horizon_is_disambiguated_for_missing_point_nonuse_and_finite_pass():
    cases = tuple(SimpleNamespace(case_id="case." + name) for name in ("missing", "nonuse", "passed"))
    observations = {"case.nonuse": observation((None, None, None)),
        "case.passed": observation((D(0), D(0), D(0)))}
    actual = reader._transport_predicted_lifetimes(POLICY, cases, observations)
    by_case = {case.case_id: tuple(row for row in actual["rows"] if row["case_id"] == case.case_id) for case in cases}
    assert all(row["first_observed_predicted_failure_horizon"] is None for row in actual["rows"])
    assert {name: {row["status"] for row in rows} for name, rows in by_case.items()} == {
        "case.missing": {"MISSING_POINT"}, "case.nonuse": {"FORECAST_NONUSE"}, "case.passed": {"RIGHT_CENSORED"}}
    assert all(row["first_missing_horizon"] == 16 for row in by_case["case.nonuse"])
    assert all(row["right_censored_through_horizon"] == 128 for row in by_case["case.passed"])
