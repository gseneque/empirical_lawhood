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


def test_handoff_policies_preserve_nonentry_and_seal_the_same_entry_before_different_futures(monkeypatch):
    settings = _settings()
    options = settings["receiver_study"]["M7"]
    options.update(handoff_clocks=["fixed", "triggered", "yoked"],
                   primary_histories=["joint-increasing.fixed", "joint-increasing.triggered"])
    ids = study.case_ids(settings, "M7")
    assert "nominal.joint-increasing.triggered" in ids
    assert "nominal.joint-increasing.yoked" in ids
    c = settings["native"]
    row = c["coordinates"][0]
    _, ideal = native.target_state(c, row)
    direction = native.native_position_lift(native.physical_chart(c, settings["events"]["receiver_seed"])[0][:, 0])
    previous = replace(ideal, step_index=15, positions=ideal.positions - 0.01 * direction)
    cp = {"state": native.checkpoint(replace(ideal, step_index=16)),
          "tick": 16, "present": True, "incoming_state": native.checkpoint(previous)}
    history = "joint-increasing.triggered"
    def measure():
        return study._event_case(settings, row, 7, history, cp, {}, study._work(), clock="triggered")
    first = measure()
    assert first["wait_ticks"] == 0
    assert first["entry_forecast"]["operand"]["previous_tick"] == 15
    assert first["entry_forecast"]["operand"]["last_entry_increment"] is True
    original = study._committed_paths
    def different_future(settings, row, seed, *args):
        return original(settings, row, seed + 1, *args)
    monkeypatch.setattr(study, "_committed_paths", different_future)
    second = measure()
    assert first["entry_forecast"] == second["entry_forecast"]
    assert first["futures"] != second["futures"]
    cp["incoming_state"] = None
    missing_previous = measure()
    assert missing_previous["entry_forecast"]["operand"]["last_entry_increment"] is None
    source = {"status": "COMPLETED", "unknown_grid_observations": 0}
    none = study._event_case(settings, row, 7, history, None, source, study._work(), clock="triggered")
    assert (none["entry_status"], none["status"], none["futures"]) == ("NO_HANDOFF", "COMPLETED", [])
    source["unknown_grid_observations"] = 1
    unknown = study._event_case(settings, row, 7, history, None, source, study._work(), clock="triggered")
    assert unknown["entry_status"] == "UNKNOWN"
    reference = study._same_entry_forecast_reference(
        [first, missing_previous, none, unknown], [[0.25, 0.5], [0.0, 0.25], [0.0, 0.0], [0.0, 1.0]],
    )
    assert reference["entrant_roots"] == 2
    assert reference["always_competing_error_completion_bounds"] == [0.125, 0.375]
    assert reference["sealed_calls_by_root"]["last_entry_increment"] == {"target": 1, "competing": 0, "unknown": 1}
    assert study._same_entry_forecast_reference([none, unknown], [[0.0, 0.0], [0.0, 1.0]])["always_competing_error_completion_bounds"] is None


def test_paired_policy_readout_checks_the_actual_state_and_causal_window():
    from pathlib import Path
    from empirical_lawhood.domains.matrix.model_free.handoff_observations import paired_policy_handoffs
    from empirical_lawhood.domains.matrix.model_free.receiver_equilibrium_events import case_ids
    from empirical_lawhood.domains.matrix.model_free.records import Product, RootAssignment, json_text
    from empirical_lawhood.domains.matrix.model_free.design import configs_for
    from empirical_lawhood.api.model_free_matrix import specification_for

    recipe = Path(__file__).resolve().parents[1] / "programmes/foundations/emergent-structure/workflows/model-free/handoff-entry-pilot.json"
    spec = specification_for("Exposed checkpoint pairing control", (RootAssignment(7, ("M1", "M7")),), json.loads(recipe.read_text())["settings"])
    configs = {config.module: config for config in configs_for(spec) if config.phase == "acquire"}
    source_cases, events = {}, []
    for slot in case_ids(spec.settings, "M7"):
        case_id, clock = slot.rsplit(".", 1)
        case = source_cases.setdefault(case_id, {"case_id": case_id, "checkpoints": {},
            "observations": [{"tick": t, "present": True} for t in range(0, 1153, 16)]})
        tick = {"fixed": 1152, "triggered": 128, "yoked": None}[clock]
        state = None if tick is None else {"step_index": tick, "sha256": "a" * 64}
        before = None if tick is None else {"step_index": tick - 1, "sha256": "b" * 64}
        case["checkpoints"][clock] = {"tick": tick, "state": state, "incoming_state": before}
        events.append({"case_id": slot, "handoff_clock": clock, "handoff_tick": tick,
            "handoff_checkpoint_sha256": None if state is None else state["sha256"],
            "wait_ticks": 0, "entry_status": "NO_HANDOFF" if state is None else "NO_STRUCTURAL_ADMISSION"})

    def acquired(module, cases, deps=()):
        config = configs[module]
        payload = {"schema": "matrix-model-free-acquisition.v1", "module": module, "seed": 7, "cases": cases}
        return Product(config.node_id + ".product", config, json_text(payload), deps)

    m1 = acquired("M1", list(source_cases.values()))
    m7 = acquired("M7", events, (m1.identity,))
    root = spec.assignments[0].unit_id
    rows = paired_policy_handoffs(spec, (m1, m7))[root]
    row = rows["nominal.joint-increasing.triggered"]
    assert row["handoff_observed_by_both"] and row["preceding_sample_tick"] == 127
    assert row["trailing_window_observed"] and row["trailing_window_ticks"] == [0, 128]
    assert rows["nominal.joint-increasing.yoked"]["handoff_checkpoint_sha256"] is None
    assert paired_policy_handoffs(spec, (m1,)) == {root: None}

    wrong = deepcopy(events)
    wrong[0]["handoff_checkpoint_sha256"] = "d" * 64
    with pytest.raises(ValueError, match="another structural handoff"):
        paired_policy_handoffs(spec, (m1, acquired("M7", wrong, (m1.identity,))))
    later = deepcopy(source_cases)
    checkpoint = later["nominal.joint-increasing"]["checkpoints"]["triggered"]
    checkpoint["tick"] = checkpoint["state"]["step_index"] = 144
    checkpoint["incoming_state"]["step_index"] = 143
    later_events = deepcopy(events)
    event = next(e for e in later_events if e["case_id"] == "nominal.joint-increasing.triggered")
    event["handoff_tick"] = 144
    moved = acquired("M1", list(later.values()))
    with pytest.raises(ValueError, match="first trailing admission window"):
        paired_policy_handoffs(spec, (moved, acquired("M7", later_events, (moved.identity,))))
    checkpoint.update(tick=None, state=None, incoming_state=None)
    event.update(handoff_tick=None, handoff_checkpoint_sha256=None, entry_status="NO_HANDOFF")
    omitted = acquired("M1", list(later.values()))
    with pytest.raises(ValueError, match="first trailing admission window"):
        paired_policy_handoffs(spec, (omitted, acquired("M7", later_events, (omitted.identity,))))
    source_cases["nominal.joint-increasing"]["observations"][3]["present"] = False
    changed = acquired("M1", list(source_cases.values()))
    with pytest.raises(ValueError, match="same root's structural acquisition"):
        paired_policy_handoffs(spec, (changed, m7))
    with pytest.raises(ValueError, match="trailing admission window"):
        paired_policy_handoffs(spec, (changed, acquired("M7", events, (changed.identity,))))


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
