# SPDX-License-Identifier: MPL-2.0
"""Root-level receiver controls against independently specified observations."""

from copy import deepcopy

import numpy as np
import pytest

from empirical_lawhood.domains.matrix.model_free import (
    native,
    receiver_observations as study,
    science,
)


def memory_settings():
    return {
        "receiver_study": {
            "M2": {
                **study.DEFAULTS["M2"],
                "coordinates": ["nominal"],
                "origin_record_age_ticks": 4,
                "future_lag_ticks": 2,
                "history_lag_ticks": 2,
            }
        },
        "native": {"timestep": "0.1", "coordinates": [{"id": "nominal"}]},
        "memory": {
            "burnin_ticks": 10,
            "record_ticks": 8,
            "stride": 1,
            "segment_boundaries_samples": [0, 3, 6, 9],
            "minimum_support": 2,
        },
    }


@pytest.mark.numerical(
    oracle="fixed three-time binary word and an explicit change to a withheld future"
)
def test_position_sign_uses_the_same_future_and_older_causal_values():
    settings = memory_settings()
    q = np.array([-1.0, -1.0, -1.0, -1.0, -0.1, -0.1, 0.5, 0.6, 0.7])
    values = np.column_stack([q, np.ones(9), np.zeros(9)])
    case = {
        "case_id": "nominal",
        "status": "COMPLETED",
        "observables": values.tolist(),
        "energies": [1.0] * 9,
        "momentum_reset_controls": [],
    }
    actual = study.memory_case(settings, case, 7)
    assert actual["absolute_origin_tick"] == 14 and actual["absolute_future_tick"] == 16
    assert (
        actual["exact_age_loss"]["q"] == 1
        and actual["exact_age_loss"]["q-velocity"] == 0
    )
    assert (
        actual["binary_history_counts"]["exact_age"]["lags"]["2"]["joint_counts"][0][0][
            1
        ]
        == 1
    )
    changed = deepcopy(case)
    changed["observables"][6][0] = -0.5
    second = study.memory_case(settings, changed, 7)
    assert second["exact_age_decision"] == actual["exact_age_decision"]
    assert (
        second["exact_age_loss"]["q"] == 0
        and second["exact_age_loss"]["q-velocity"] == 1
    )
    unknown = {"case_id": "nominal", "status": "UNAVAILABLE"}
    summary = study.synthesise(
        settings,
        "M2",
        [{"seed": 7, "cases": [actual]}, {"seed": 8, "cases": [unknown]}],
        0.05,
    )
    velocity = next(
        item
        for item in summary["common_future_risks"]
        if item["method"] == "q-velocity"
    )
    assert (
        velocity["assigned"] == 2
        and velocity["evaluated"] == 1
        and velocity["unknown"] == 1
    )
    assert velocity["risk_interval"][1] >= 0.5 and velocity["decision"] == "UNRESOLVED"
    assert summary["history_and_ck"][0]["exact_age"]["status"] == "UNRESOLVED"


def test_first_admission_is_excluded_from_genuine_reentries_and_affordable_prefix(
    monkeypatch,
):
    config = science.normalise_settings({})["native"]
    observed = {0: False, 1: True, 2: True, 3: False, 4: True}
    index = iter([0, 1, 2, 3, 4, 4])
    monkeypatch.setattr(
        native.classical,
        "_factor_measure",
        lambda positions, c: {"Y": {"raw_admitted": observed[next(index)]}},
    )
    case = native.formation(
        config,
        config["coordinates"][0],
        "joint-increasing",
        1,
        {
            "fixed_tick": 4,
            "trigger_deadline": 4,
            "observation_stride": 1,
            "trailing_ticks": 1,
            "required_sectors": ["Y"],
            "service_protocol": "control",
        },
        reviewed=True,
        yoked_tick=2,
    )
    assert case["first_observed_admission"] == 1 and case["reentries"] == 1
    assert (
        case["checkpoints"]["triggered"]["preparation_force_calls"]
        == case["checkpoints"]["yoked"]["preparation_force_calls"]
    )
    assert (
        case["checkpoints"]["fixed"]["preparation_force_calls"]
        == case["preparation_force_evaluations"]
    )


def test_known_law_controls_expose_zero_and_false_refusal(monkeypatch):
    monkeypatch.setattr(
        science,
        "acquire_root",
        lambda *a, **k: {"controls": [], "harmonic_bath_controls": []},
    )
    settings = {
        "native": {"timestep": "0.001"},
        "receiver_study": {"M0": study.DEFAULTS["M0"]},
    }
    case = study._controls(settings, 9)
    result = study.synthesise(settings, "M0", [{"cases": [case]}], 0.01)
    rows = {(row["task"], row["policy"]): row for row in result["known_law_decisions"]}
    assert rows["incompatible-actions", "zero-response"]["false_deliveries"] == 512
    assert rows["incompatible-actions", "always-refuse"]["false_refusals"] == 512
    assert rows["near-ineligible", "hidden"]["true_eligible"] is False
    assert result["maximum_exact_identity_error"] < 1e-12
    assert (
        result["free_baoab"]["finer_difference"]
        < 1e-4
        < result["free_baoab"]["coarse_difference"]
    )
