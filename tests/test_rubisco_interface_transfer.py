# SPDX-License-Identifier: MPL-2.0
"""Regress the complete two-endpoint comparison and its applicability boundary."""

from math import log
import pytest

from empirical_lawhood.domains.rubisco.rubisco_prediction.interface_transfer import (
    aligned_weights,
    classify_joint_bounds,
    descriptor,
    fit_predict,
    score_forecasts,
    site_vector,
)


@pytest.mark.native("rapidfuzz")
def test_geometry_is_local_and_gap_does_not_inherit_a_contact():
    weights = aligned_weights("ACIV", "ACI", {1: 0.2, 2: 0.3, 3: 0.75})
    vec, rows = site_vector("ACIV", "ACMVK", weights)
    assert [(r["position"], r["from"], r["to"], r["weight"]) for r in rows] == [
        (3, "I", "M", 0.75),
        (None, "-", "K", 0),
    ]
    assert vec[7] == 0.75 and vec[8] == 0 and vec[9] == -0.75
    assert descriptor("M")[0] - descriptor("I")[0] == -0.25
    assert site_vector("ACIV", "ACIV", weights) == ([0] * 10, [])


def test_freeze_and_signed_scoring_retains_all_assigned_materials():
    baseline = {
        "id": "a",
        "background": "train",
        "features": [1.0] * 10,
        "responses": {"turnover": ["3", "2"], "specificity": ["1", "2"]},
    }
    test = {"id": "b", "background": "test", "features": [1.0] * 10}
    _, result = fit_predict([baseline], [test])
    assert result["b"]["interface"] == pytest.approx(
        [10 / 11 * log(1.5), 10 / 11 * log(0.5)]
    )
    with pytest.raises(ValueError, match="LSU background"):
        fit_predict([baseline], [dict(test, background="train")])
    with pytest.raises(ValueError, match="label-free"):
        fit_predict([baseline], [dict(test, responses=baseline["responses"])])
    with pytest.raises(ValueError, match="census"):
        score_forecasts(result, {}, [0.3, 0.07])
    obs = {"b": {"role": "mass only", "mass_activity": {"mutant": "1", "parent": "2"}}}
    scores = score_forecasts(result, obs, [0.3, 0.07])["b"]["methods"]["zero"]
    assert scores["turnover"] is None and scores["specificity"] is None
    assert scores["mass_activity"]["signed_error"] == pytest.approx(log(2))
    assert scores["mass_activity"]["direction_matches"] is False


def test_future_joint_decision_uses_strict_turnover_inclusive_specificity_and_both_views():
    supported = {"turnover": (0.1, 0.2), "specificity": (0.0, 0.03)}
    assert (
        classify_joint_bounds({"M1": supported, "V1": supported})["joint"]
        == "SUPPORTED"
    )
    for bad in (
        dict(supported, turnover=(-0.2, 0.0)),
        {"turnover": None, "specificity": (-0.1, -0.001)},
    ):
        assert classify_joint_bounds({"M1": None, "V1": bad})["joint"] == "ADVERSE"
    assert classify_joint_bounds({"M1": None, "V1": supported})["joint"] == "UNRESOLVED"
    assert (
        classify_joint_bounds(
            {"M1": dict(supported, turnover=(0.0, 0.3)), "V1": supported}
        )["joint"]
        == "UNRESOLVED"
    )
    with pytest.raises(ValueError, match="Invalid simultaneous"):
        classify_joint_bounds(
            {"M1": dict(supported, specificity=(1.0, 0.0)), "V1": None}
        )
