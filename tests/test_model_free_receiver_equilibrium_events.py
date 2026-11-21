# SPDX-License-Identifier: MPL-2.0
"""Small native controls for signed equilibrium and entry-conditioned first passage."""

from copy import deepcopy
from dataclasses import replace
import json

import numpy as np
import pytest

from empirical_lawhood.domains.matrix.model_free import (
    native,
    receiver_equilibrium_events as study,
)
from empirical_lawhood.domains.matrix.model_free.science import normalise_settings


def _settings():
    settings = normalise_settings(
        {
            "native": {
                "coordinates": [
                    {
                        "id": "nominal",
                        "temperature": "1",
                        "friction": "1",
                        "cross_coupling": "1",
                    },
                    {
                        "id": "high-coupling",
                        "temperature": "1",
                        "friction": "1",
                        "cross_coupling": "2",
                    },
                    {
                        "id": "high-temperature",
                        "temperature": "2",
                        "friction": "1",
                        "cross_coupling": "1",
                    },
                ]
            },
            "equilibrium": {
                "centers": ["-0.2", "-0.1", "0", "0.1", "0.2"],
                "burnin_ticks": 2,
                "sample_ticks": 4,
                "reference_ticks": 8,
                "stride": 2,
                "importance_samples": 6,
            },
            "events": {
                "horizon_ticks": 16,
                "replicas": 2,
                "upper_target": "0.03",
                "lower_target": "-0.03",
            },
        }
    )
    settings["receiver_study"] = deepcopy(study.DEFAULTS)
    settings["receiver_study"]["M1"] = {
        "coordinates": ["nominal", "high-temperature"],
        "structural_service": True,
    }
    settings["receiver_study"]["M7"].update(entry_window_ticks=4, dwell_ticks=2)
    return settings


def test_analytic_control_null_effect_overlap_and_hidden_commitment():
    controls = study._harmonic_controls([-0.2, -0.1, 0, 0.1, 0.2], 1, 0.1)
    assert [r["admissible"] for r in controls["gaussian_overlap"]] == [True, False]
    assert controls["signed_controls"][0]["analytic_signed_difference"] == 0
    assert controls["signed_controls"][1][
        "analytic_signed_difference"
    ] == pytest.approx(-2 / 15)
    assert all(c["maximum_absolute_error"] < 1e-12 for c in controls["signed_controls"])
    null, positive, holding = study._hidden_commitment_controls(4.096, 0.1)
    assert null["signed_incidence"] == 0 and null["visible_meets_budget"]
    assert positive["signed_incidence"] > 0.75 and not positive["visible_meets_budget"]
    assert (
        positive["signed_restricted_mean"] == 0
        and holding["signed_restricted_mean"] > 0
    )
    assert positive["history_meets_budget"]


def test_signed_native_reference_clocks_and_incomplete_pair():
    settings = _settings()
    roots = []
    for seed in (21, 23):
        raw = study.acquire(settings, seed, "M6", {}, None, None)
        assert raw["work_accounting"]["native_force_evaluations"] > 0
        assert raw["work_accounting"]["native_energy_evaluations"] == 18
        assert all(
            c["independent"]["centers"][0]["completed_steps"] == 20
            for c in raw["cases"]
        )
        assert all(
            len(c["independent"]["centers"][0]["samples"]) == 5 for c in raw["cases"]
        )
        roots.append({"seed": seed, **study.analyse(settings, "M6", raw)})
    output = study.synthesise(settings, "M6", roots, 0.01)
    json.dumps(output, allow_nan=False)
    primary, stress = output["paired_equilibrium"]
    assert primary["decision"] == "UNRESOLVED"
    assert primary["energy_budget"] == pytest.approx(np.log(1.05))
    assert (
        primary["canonical_total_error_bound"] is None
        and stress["energy_budget"] is None
    )
    assert (
        primary["independent_root_moment_transport"]["moment_estimator"]
        == "INDEPENDENT_ROOT_CROSS_PRODUCT_U_STATISTIC"
    )
    assert len(primary["estimators"]["short"]["full_mean_covariance"]) == 10
    roots[1]["cases"][1]["status"] = "UNAVAILABLE"
    primary, stress = study.synthesise(settings, "M6", roots, 0.01)[
        "paired_equilibrium"
    ]
    assert primary["missing"] == [{"seed": 23, "coordinate": "high-coupling"}]
    assert stress["status"] == "ESTIMATED"


def test_history_cannot_absorb_a_tick_zero_exit_and_dwell_resets():
    rule = study._ExitObservation(2)
    for t, side in enumerate([0, 1, 1, 0, -1, -1, -1]):
        rule.observe(t, side)
    assert (rule.event, rule.event_step) == ("competing", 6)
    settings = _settings()
    c = settings["native"]
    row = c["coordinates"][0]
    _, initial = native.target_state(c, row)
    force, _ = native.physical_chart(c, settings["events"]["receiver_seed"])
    direction = native.native_position_lift(force[:, 0])
    cp = {
        "state": native.checkpoint(
            replace(initial, positions=initial.positions + 0.5 * direction)
        ),
        "present": True,
        "tick": 1152,
    }
    work = study._work()
    case = study._event_case(settings, row, 9, "baseline", cp, {}, work)
    assert (
        case["fixed_occupancy"] == "target"
        and case["entry_status"] == "NO_INTERIOR_BEFORE_DEADLINE"
    )
    assert case["wait_ticks"] == 4 and not case["futures"]
    cp["state"] = native.checkpoint(
        replace(initial, momenta=initial.momenta + 20 * direction)
    )
    entered = study._event_case(settings, row, 9, "baseline", cp, {}, work)
    assert (
        entered["fixed_occupancy"] == "between_boundaries"
        and entered["entry_status"] == "ENTERED"
    )
    assert entered["history_increment"] is None
    assert entered["wait_ticks"] == 0 and work["native_force_evaluations"] > 0
    for future in entered["futures"]:
        for key in ("h1_dwell", "h2_dwell"):
            assert future[key]["event"] == "target" and future[key]["event_time"] > 0
            assert (
                future[key]["event_time"]
                - future[key.replace("dwell", "first")]["event_time"]
                >= 0.002 - 1e-15
            )
    cp["present"] = False
    absent = study._event_case(
        settings,
        row,
        9,
        "baseline",
        cp,
        {"observations": [{"tick": 1152, "factors": {"Y": {"raw_admitted": False}}}]},
        work,
    )
    assert absent["entry_status"] == "NO_STRUCTURAL_ADMISSION" and not absent["futures"]


def test_all_assigned_service_keeps_known_nonentry_and_numerical_unknown_separate():
    settings = _settings()
    keys = study.case_ids(settings, "M7")
    rows = {row["id"]: row for row in settings["native"]["coordinates"]}
    roots = []
    for seed, status in [(100, "NO_INTERIOR_BEFORE_DEADLINE"), (103, "UNKNOWN")]:
        roots.append(
            {
                "seed": seed,
                "cases": [
                    {
                        "case_id": key,
                        "coordinate": rows[key.split(".")[0]],
                        "entry_history": key.split(".")[1],
                        "status": "UNAVAILABLE" if status == "UNKNOWN" else "COMPLETED",
                        "fixed_occupancy": "unobserved",
                        "wait_ticks": 0,
                        "futures": [],
                        "entry_status": status,
                    }
                    for key in keys
                ],
            }
        )
    result = study.synthesise(settings, "M7", roots, 0.01)
    assert all(
        c["target_service_per_original_assignment"]["completion_bounds"] == [0.0, 0.5]
        for c in result["entry_and_passage"]
    )
    assert result["both_arms_entered_estimand"] is None
    assert result["restricted_mean_decision_among_both_entered"] == "UNRESOLVED"
    assert result["primary"]["completion_bounds"] == [-0.5, 0.5]
    json.dumps(result, allow_nan=False)


def test_primary_energy_contrast_must_share_temperature():
    settings = _settings()
    settings["receiver_study"]["M6"]["primary_pair"] = ["nominal", "high-temperature"]
    with pytest.raises(ValueError, match="same temperature"):
        study.case_ids(settings, "M6")


def test_accelerated_reference_reproduces_original_baoab_and_innovations():
    settings = _settings()
    c = settings["native"]
    coord, canonical = native.target_state(c, c["coordinates"][1])
    force, _ = native.physical_chart(c, settings["equilibrium"]["receiver_seed"])
    direction = force[:, 0]
    ordinary = replace(
        canonical,
        positions=canonical.positions + 0.4 * native.native_position_lift(direction),
    )
    cached = ordinary
    stream = native.rng(31, 681, 3)
    fast = study._noise_blocks(native.rng(31, 681, 3), 131)
    path = study._RestrainedPath(ordinary, coord, direction, -0.2, 1.0, coord.fine_view)
    for tick, innovation in enumerate(fast):
        original = native.hermitian_noise(rng=stream, q=2)
        np.testing.assert_array_equal(innovation, original)
        if tick < 8:
            cached = path.advance(cached, innovation)
            ordinary = native.restrained_step(
                ordinary, coord, original, direction, -0.2, 1.0, coord.fine_view
            )
            np.testing.assert_array_equal(ordinary.positions, cached.positions)
            np.testing.assert_array_equal(ordinary.momenta, cached.momenta)
    assert path.cache.completed_evaluations == 9


def test_complete_nested_event_census_and_two_entered_history_contrast():
    settings = _settings()
    c = settings["native"]
    opts = settings["receiver_study"]["M7"]
    opts["coordinates"] = [opts["primary_coordinate"]]
    cases = []
    rows = {r["id"]: r for r in c["coordinates"]}
    for key in study.case_ids(settings, "M7"):
        coordinate, recipe = key.split(".")
        row = rows[coordinate]
        _, initial = native.target_state(c, row)
        force, _ = native.physical_chart(c, settings["events"]["receiver_seed"])
        sign = 1.0 if recipe == "joint-increasing" else -1.0
        state = replace(
            initial,
            momenta=initial.momenta
            + sign * 20 * native.native_position_lift(force[:, 0]),
        )
        cp = {"state": native.checkpoint(state), "tick": 1152, "present": True}
        cases.append(
            study._event_case(settings, row, 113, recipe, cp, {}, study._work())
        )
    root = {"seed": 113, **study.analyse(settings, "M7", {"seed": 113, "cases": cases})}
    result = study.synthesise(settings, "M7", [root], 0.01)
    assert result["primary"]["completion_bounds"] == [1.0, 1.0]
    assert result["both_arms_entered_estimand"]["independent_roots"] == 1
    assert result["both_arms_entered_estimand"]["commitment"]["completion_bounds"] == [
        1.0,
        1.0,
    ]
    assert len(result["entry_and_passage"][0]["entered_views"]) == 8
    assert result["primary"]["decision"] == "UNRESOLVED"
    json.dumps(result, allow_nan=False)
    cases[0]["futures"][1] = deepcopy(cases[0]["futures"][0])
    with pytest.raises(ValueError, match="replica"):
        study.analyse(settings, "M7", {"seed": 113, "cases": cases})
