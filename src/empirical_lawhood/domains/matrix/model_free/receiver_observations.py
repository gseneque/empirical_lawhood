# SPDX-License-Identifier: MPL-2.0
"""Known decision controls, assigned structural service and a common finite-age future."""

import math
from decimal import Decimal

import numpy as np
from scipy.stats import beta

from . import native
from .receiver_campaign import decimal_value
from .structural_service_design import paired_delivery_halfwidth

DEFAULTS = {
    "M0": {
        "populations": 512,
        "trials_per_stratum": 128,
        "risk_budget": "0.10",
        "false_delivery_limit": "0.05",
        "power_minimum": "0.80",
        "identity_tolerance": "0.0000000001",
    },
    "M1": {
        "structural_service": True,
        "coordinates": ["nominal", "high-temperature"],
        "primary_coordinate": "high-temperature",
        "primary_recipe": "joint-increasing",
        "maximum_coverage_loss": "0.0625",
        "minimum_delivery": "0.75",
        "maximum_wrong_delivery": "0.10",
        "minimum_signed_impulse": "0.10",
        "yoked_ticks": [
            976,
            None,
            1120,
            880,
            832,
            1024,
            736,
            880,
            688,
            None,
            704,
            800,
            880,
            880,
            800,
            912,
        ],
    },
    "M2": {
        "coordinates": ["nominal", "high-temperature"],
        "future_lag_ticks": 64,
        "origin_record_age_ticks": 8192,
        "history_lag_ticks": 64,
        "risk_budget": "0.10",
    },
}


def validate(module, opts, base):
    if module == "M0":
        for key in ("populations", "trials_per_stratum"):
            if type(opts[key]) is not int or opts[key] < 2:
                raise ValueError(
                    "M0 control populations and sample sizes must be positive integers above one"
                )
        for key in (
            "risk_budget",
            "false_delivery_limit",
            "power_minimum",
            "identity_tolerance",
        ):
            decimal_value(opts[key], key, maximum=Decimal(1))
        return
    if (
        type(opts["coordinates"]) is not list
        or not opts["coordinates"]
        or len(set(opts["coordinates"])) != len(opts["coordinates"])
        or not all(type(v) is str and v for v in opts["coordinates"])
    ):
        raise ValueError(f"{module} needs explicitly named coordinates")
    if module == "M1":
        if (
            type(opts["structural_service"]) is not bool
            or opts["primary_coordinate"] not in opts["coordinates"]
        ):
            raise ValueError("Declare the M1 structural policy and primary coordinate")
        for key in (
            "maximum_coverage_loss",
            "minimum_delivery",
            "maximum_wrong_delivery",
            "minimum_signed_impulse",
        ):
            decimal_value(opts[key], key, maximum=Decimal(1))
        if not opts["yoked_ticks"] or any(
            t is not None and (type(t) is not int or t < 0) for t in opts["yoked_ticks"]
        ):
            raise ValueError("Yoked times must be frozen observed times or nonentry")
    else:
        for key in ("future_lag_ticks", "origin_record_age_ticks", "history_lag_ticks"):
            if type(opts[key]) is not int or opts[key] < 1:
                raise ValueError("M2 needs positive physical tick indices")
        decimal_value(opts["risk_budget"], "M2 risk budget", maximum=Decimal(1))


def _coords(settings, module):
    ids = settings["receiver_study"][module]["coordinates"]
    rows = {v["id"]: v for v in settings["native"]["coordinates"]}
    if set(ids) - set(rows):
        raise ValueError(
            f"{module} selected coordinates absent from the physical definition"
        )
    return [rows[key] for key in ids]


def case_ids(settings, module):
    from .science import _recipes

    if module == "M0":
        return ("known-laws",)
    if module == "M2":
        return [r["id"] for r in _coords(settings, module)]
    if not settings["receiver_study"]["M1"]["structural_service"]:
        return ("response-preparation",)
    return [
        r["id"] + "." + recipe
        for r in _coords(settings, module)
        for recipe in _recipes(settings)
    ]


def _controls(settings, seed):
    from .science import acquire_root

    legacy = acquire_root(
        {k: v for k, v in settings.items() if k != "receiver_study"}, seed, "M0"
    )
    opts = settings["receiver_study"]["M0"]
    n, reps = opts["trials_per_stratum"], opts["populations"]
    rng = native.rng(seed, 650)
    # Columns are the two hidden states with identical visible observations.
    # A visible-only rule commits to action zero. A state-resolved rule chooses by stratum.
    tasks = {
        "common-action": [[0.01, 0.03], [0.98, 0.97]],
        "incompatible-actions": [[0.01, 0.98], [0.97, 0.03]],
        "near-ineligible": [[0.01, 0.1001], [0.98, 0.97]],
    }
    hidden_actions = {
        "common-action": [0, 0],
        "incompatible-actions": [0, 1],
        "near-ineligible": [0, 0],
    }
    output = []
    for task, table in tasks.items():
        risks = np.asarray(table)
        trials = rng.binomial(n, risks, size=(reps, 2, 2))
        for rule, actions in (
            ("visible", [0, 0]),
            ("hidden", hidden_actions[task]),
            ("zero-response", [0, 0]),
            ("always-refuse", []),
        ):
            if len(actions):
                counts = trials[:, actions, [0, 1]]
                upper = np.where(
                    counts == n,
                    1.0,
                    beta.ppf(
                        1 - float(opts["false_delivery_limit"]) / 2,
                        counts + 1,
                        np.maximum(1, n - counts),
                    ),
                )
                admitted = (
                    np.ones(reps, dtype=bool)
                    if rule == "zero-response"
                    else np.max(upper, axis=1) <= float(opts["risk_budget"])
                )
                possible = bool(
                    risks[actions, [0, 1]].max() <= float(opts["risk_budget"])
                )
            else:
                admitted = np.zeros(reps, dtype=bool)
                possible = bool(
                    risks[hidden_actions[task], [0, 1]].max()
                    <= float(opts["risk_budget"])
                )
            output.append(
                {
                    "task": task,
                    "policy": rule,
                    "true_eligible": possible,
                    "admissions": int(admitted.sum()),
                    "false_deliveries": int(admitted.sum()) if not possible else 0,
                    "false_refusals": int((~admitted).sum()) if possible else 0,
                    "independent_control_populations": reps,
                }
            )
    h = float(settings["native"]["timestep"])

    def free_position(n):
        dt = h / n
        q = velocity = 0.0
        for _ in range(n):
            velocity += dt / 2
            q += dt * velocity / 2
            velocity *= math.exp(-dt)
            q += dt * velocity / 2
            velocity += dt / 2
        return q / (0.5 * h * h)

    analytic = [free_position(r) for r in (1, 2, 4)]
    return {
        "case_id": "known-laws",
        "status": "COMPLETED",
        "decision_controls": output,
        "consequential_controls": {
            "good_action_worst_risk": 0.03,
            "bad_action_minimum_risk": 0.97,
            "near_ineligible_risk": 0.1001,
            "near_boundary_risk_overrun": 0.1001 - float(opts["risk_budget"]),
            "always_refuse_opportunity": "ANY_AVAILABLE_STATE_RESOLVED_ACTION",
            "zero_response_policy": "ALWAYS_DELIVER_ACTION_ZERO",
        },
        "exact_action_risks": tasks,
        "free_baoab": {
            "normalized_position": analytic,
            "coarse_difference": abs(analytic[0] - analytic[1]),
            "finer_difference": abs(analytic[1] - analytic[2]),
            "one_step_identity_error": abs(analytic[0] - (1 + math.exp(-h)) / 2),
        },
        "observation_controls": legacy["controls"],
        "harmonic_baths": legacy["harmonic_bath_controls"],
    }


def _formation(settings, seed, work):
    from .science import _recipes

    opts = settings["receiver_study"]["M1"]
    if not opts["structural_service"]:
        return [{"case_id": "response-preparation", "status": "COMPLETED"}]
    c, policy = settings["native"], settings["formation"]
    if opts["primary_recipe"] not in _recipes(settings):
        raise ValueError("The primary M1 recipe is absent")
    times = opts["yoked_ticks"]
    if any(
        t is not None
        and (t > policy["trigger_deadline"] or t % policy["observation_stride"])
        for t in times
    ):
        raise ValueError("Yoked clocks must be on the preparation observation grid")
    yoked = times[int(native.rng(seed, 651).integers(len(times)))]
    directed, _ = native.physical_chart(c, 0)
    force = directed[:, [c["actions"].index("FACTOR")]]
    receiver = np.concatenate((np.zeros(96), force[:, 0]))[None]
    scale = float(c["amplitude"]) * c["pulse_ticks"] * float(c["timestep"])
    policy_clocks = "handoff_clocks" in settings["receiver_study"].get("M7", {})
    cases = []
    for row in _coords(settings, "M1"):
        for recipe in _recipes(settings):
            case = native.formation(
                c, row, recipe, seed, policy, reviewed=True, yoked_tick=yoked,
                retain_incoming_state=policy_clocks,
            )
            case["case_id"] = row["id"] + "." + recipe
            case["yoked_tick_assignment"] = yoked
            work["native_force_evaluations"] += case["preparation_force_evaluations"]
            work["native_energy_evaluations"] += case["protocol_work"][
                "potential_evaluations_completed"
            ]
            case["unknown_grid_observations"] = sum(
                any(
                    o["factors"][s]["raw_admitted"] is None
                    for s in policy["required_sectors"]
                )
                for o in case["observations"]
            )
            case["checkpoints"].setdefault(
                "yoked",
                {
                    "tick": None,
                    "state": None,
                    "present": False,
                    "reason": "YOKED_NONENTRY",
                },
            )
            acquired_handoffs = {}
            for label, handoff in case["checkpoints"].items():
                handoff["panel_service"] = []
                if handoff["state"] is None:
                    continue
                if policy_clocks:
                    # Within this root and recipe the actuator, panel noises and
                    # numerical settings are identical for an identical state.
                    state_id = handoff["state"]["sha256"]
                    if state_id in acquired_handoffs:
                        original = acquired_handoffs[state_id]
                        handoff["panel_service"] = original["panel_service"]
                        handoff["shared_assay_with"] = original["assay_clock"]
                        if "service_failure" in original:
                            handoff["service_failure"] = original["service_failure"]
                        continue
                    acquired_handoffs[state_id] = handoff
                    handoff["assay_clock"] = label
                try:
                    for panel in range(policy["service_panels"]):
                        response = native.paired_response(
                            {**c, "horizon_ticks": 64},
                            row,
                            native.restore(handoff["state"]),
                            force,
                            receiver,
                            seed,
                            panel,
                            collect_survival=True,
                            required_sectors=policy["required_sectors"],
                            forced_survival=True,
                            synchronous_quench=True,
                            compute_tangent=False,
                        )
                        survival = response["survival"]
                        projected = float(response["odd_response"][0][-1][0]) / scale
                        handoff["panel_service"].append(
                            {
                                "panel": panel,
                                "signed_impulse": projected,
                                "momentum_in_native_units": projected * scale,
                                "above_assay_detection_floor": abs(projected * scale)
                                >= float(policy["minimum_signal"]),
                                "survives_all_paths": all(
                                    v is True
                                    for t in survival
                                    for path in t["branches"]
                                    for v in path
                                ),
                                "unknown_observations": sum(
                                    v is None
                                    for t in survival
                                    for path in t["branches"]
                                    for v in path
                                ),
                                "branch_survival": survival,
                                "work": response["protocol_handoff_work"],
                                "force_evaluations": response["force_evaluations"],
                            }
                        )
                        work["native_force_evaluations"] += response[
                            "force_evaluations"
                        ]
                        work["native_energy_evaluations"] += response[
                            "protocol_handoff_work"
                        ]["potential_evaluations"]
                except (
                    FloatingPointError,
                    OverflowError,
                    np.linalg.LinAlgError,
                ) as error:
                    handoff["service_failure"] = str(error)
                    for key in (
                        "native_force_evaluations",
                        "native_hessian_actions",
                        "native_energy_evaluations",
                    ):
                        work[key] += getattr(error, "partial_accounting", {}).get(
                            key, 0
                        )
                    work["counts_are_lower_bounds"] = True
            cases.append(case)
    return cases


def acquire(settings, seed, module, prerequisites, sampling, assigned_modules):
    work = {
        "native_force_evaluations": 0,
        "native_hessian_actions": 0,
        "native_energy_evaluations": 0,
        "counts_are_lower_bounds": False,
    }
    if module == "M0":
        cases = [_controls(settings, seed)]
    elif module == "M1":
        cases = _formation(settings, seed, work)
    else:
        cases = []
        for row in _coords(settings, module):
            try:
                case = native.memory_record(
                    settings["native"], row, seed, settings["memory"]
                )
            except native.NativeResponseFailure as error:
                case = {
                    **error.partial_accounting,
                    **getattr(error, "partial_record", {}),
                    "coordinate": row,
                    "reason": str(error),
                    "status": "UNAVAILABLE",
                }
            case["case_id"] = row["id"]
            for key in ("native_force_evaluations", "native_energy_evaluations"):
                work[key] += case.get(key, 0)
            cases.append(case)
    work["counts_are_lower_bounds"] |= any(c["status"] != "COMPLETED" for c in cases)
    return {"cases": cases, "work_accounting": work}


def memory_case(settings, case, root_seed):
    """Project original native observations onto one future for every causal description."""
    opts = settings["receiver_study"]["M2"]
    if case["status"] != "COMPLETED":
        return {
            "case_id": case["case_id"],
            "status": "UNAVAILABLE",
            "reason": case.get("reason", "NATIVE_RECORD_INCOMPLETE"),
        }
    stride = settings["memory"]["stride"]
    age, lag, history = (
        opts[k]
        for k in ("origin_record_age_ticks", "future_lag_ticks", "history_lag_ticks")
    )
    if (
        any(t % stride for t in (age, lag, history))
        or age < history
        or age + lag > settings["memory"]["record_ticks"]
    ):
        raise ValueError(
            "Common M2 receiver requires the whole history and future on the original clock"
        )
    from empirical_lawhood.methods.model_free.memory import root_lag_counts

    values = np.asarray(case["observables"], dtype=float)
    expected = settings["memory"]["record_ticks"] // stride + 1
    if values.shape != (expected, 3) or not np.isfinite(values).all():
        raise ValueError(
            "The retained q/velocity/force record lost its physical clock or finite values"
        )
    tau = float(settings["native"]["timestep"]) * lag
    history_time = float(settings["native"]["timestep"]) * history
    anchor, step, past = age // stride, lag // stride, history // stride
    ids = np.arange(past, len(values) - step)
    q, v, force = values[ids].T
    actual = values[ids + step, 0] >= 0
    methods = {
        "always-nonnegative": np.ones(len(ids), dtype=bool),
        "q": q >= 0,
        "q-velocity": q + tau * v >= 0,
        "q-velocity-force": q + tau * v + 0.5 * tau * tau * force >= 0,
        "q-history": q + tau * (q - values[ids - past, 0]) / history_time >= 0,
    }
    losses = {k: (forecast != actual) for k, forecast in methods.items()}
    exact = anchor - past
    groups = {}
    for dim in (1, 2, 3):
        # Each added bit conditions the same scalar future. The bins cover both real tails.
        symbols = (values[ids, :dim] >= 0) @ (2 ** np.arange(dim))
        groups[str(dim)] = [
            {
                "cell": j,
                "observed": int((symbols == j).sum()),
                "future_positive": int(np.count_nonzero(actual & (symbols == j))),
            }
            for j in range(2**dim)
        ]
    sign = (values[:, 0] >= 0).astype(int)
    lag_options = dict(
        lags=[step], alphabet_size=2, history_order=1, root_id=str(root_seed)
    )
    history_counts = {
        "finite_record": root_lag_counts(sign, **lag_options),
        "exact_age": root_lag_counts(
            sign,
            record_scope="protocol_age",
            anchor_indices=[anchor + step],
            **lag_options,
        ),
    }
    boundaries = settings["memory"]["segment_boundaries_samples"]
    return {
        "case_id": case["case_id"],
        "status": "COMPLETED",
        "future_positive": bool(actual[exact]),
        "absolute_origin_tick": settings["memory"]["burnin_ticks"] + age,
        "absolute_future_tick": settings["memory"]["burnin_ticks"] + age + lag,
        "binary_history_counts": history_counts,
        "exact_age_decision": {k: bool(vv[exact]) for k, vv in methods.items()},
        "exact_age_loss": {k: int(vv[exact]) for k, vv in losses.items()},
        "pooled_root_loss": {k: float(vv.mean()) for k, vv in losses.items()},
        "pooled_common_future_cells": groups,
        "pooled_anchors": len(ids),
        "segment_mean_q": [
            float(np.mean(values[a:b, 0])) for a, b in zip(boundaries, boundaries[1:])
        ],
        "segment_mean_energy": [
            float(np.mean(case["energies"][a:b]))
            for a, b in zip(boundaries, boundaries[1:])
        ],
        "reset_controls": [
            {
                "age_tick": x["age_tick"],
                "clone_error": x["full_state_clone_max_abs_difference"],
                "momentum_reset_endpoint_difference": x["momentum_reset"][-1]
                - x["original"][-1],
            }
            for x in case["momentum_reset_controls"]
            if x["status"] == "COMPLETED"
        ],
    }


def analyse(settings, module, payload):
    if module == "M0":
        return {"cases": payload["cases"]}
    if module == "M2":
        return {
            "cases": [
                memory_case(settings, case, payload["seed"])
                for case in payload["cases"]
            ]
        }
    opts = settings["receiver_study"]["M1"]
    if not opts["structural_service"]:
        return {
            "cases": payload["cases"],
            "preparation_scope": "ACTUAL_PAIRED_HANDOFFS_SUPPLIED_TO_NAMED_RECEIVER",
        }
    cases = []
    for case in payload["cases"]:
        handoffs = {}
        for label, cp in case["checkpoints"].items():
            panels = cp["panel_service"]
            entered = cp["state"] is not None
            enough = len(panels) == settings["formation"]["service_panels"]
            signal = enough and min(p["signed_impulse"] for p in panels) >= float(
                opts["minimum_signed_impulse"]
            )
            preserved = enough and all(p["survives_all_paths"] for p in panels)
            offered = entered and cp["present"]
            unknown = bool(
                cp.get("service_failure")
                or case["status"] != "COMPLETED"
                or entered
                and not cp.get("identifiable", True)
                or any(p["unknown_observations"] for p in panels)
            )
            prefix_calls = cp.get(
                "preparation_force_calls", case["preparation_force_evaluations"]
            )
            preparation_work = cp.get("protocol_work_prefix", case["protocol_work"])
            assay_calls = sum(p["force_evaluations"] for p in panels)
            handoffs[label] = {
                "entered": entered,
                "tick": cp["tick"],
                "present": cp["present"],
                "preserved": preserved,
                "signed_signal": signal,
                "delivery": bool(entered and cp["present"] and signal and preserved),
                "offered": offered,
                "wrong_offer": bool(
                    offered and enough and not unknown and not (signal and preserved)
                ),
                "waiting_ticks": cp["tick"]
                if entered
                else settings["formation"]["trigger_deadline"],
                "signed_values": [p["signed_impulse"] for p in panels],
                "assayed_panels": len(panels),
                "unknown": unknown,
                "preparation_work": preparation_work,
                "coupling_exposure": cp.get(
                    "coupling_exposure_prefix", case["coupling_exposure"]
                ),
                "assay_work": [p["work"] for p in panels],
                "preparation_force_evaluations": prefix_calls,
                "assay_force_evaluations": assay_calls,
                "policy_force_calls": prefix_calls + (assay_calls if offered else 0),
            }
        cases.append(
            {
                key: case[key]
                for key in (
                    "case_id",
                    "status",
                    "recipe",
                    "coordinate",
                    "reentries",
                    "unknown_grid_observations",
                    "coupling_exposure",
                    "protocol_work",
                    "first_observed_admission",
                    "initial_presence",
                )
            }
            | {"handoffs": handoffs}
        )
    return {"cases": cases}


def _one_sided(count, n, alpha):
    return 0.0 if count == 0 else float(beta.ppf(alpha, count, n - count + 1))


def synthesise(settings, module, roots, alpha):
    opts = settings["receiver_study"][module]
    if module == "M0":
        controls = [root["cases"][0] for root in roots]
        rows = []
        for idx, option in enumerate(controls[0]["decision_controls"]):
            population = sum(
                c["decision_controls"][idx]["independent_control_populations"]
                for c in controls
            )
            admissions = sum(
                c["decision_controls"][idx]["admissions"] for c in controls
            )
            tail = alpha / (2 * len(controls[0]["decision_controls"]))
            lower = _one_sided(admissions, population, tail)
            upper = 1 - _one_sided(population - admissions, population, tail)
            rows.append(
                {
                    **option,
                    "admissions": admissions,
                    "independent_control_populations": population,
                    "false_deliveries": sum(
                        c["decision_controls"][idx]["false_deliveries"]
                        for c in controls
                    ),
                    "false_refusals": sum(
                        c["decision_controls"][idx]["false_refusals"] for c in controls
                    ),
                    "admission_probability_interval": [lower, upper],
                    "decision": (
                        "BASELINE"
                        if option["policy"] in ("always-refuse", "zero-response")
                        else "MEETS"
                        if (
                            lower >= float(opts["power_minimum"])
                            if option["true_eligible"]
                            else upper <= float(opts["false_delivery_limit"])
                        )
                        else "UNRESOLVED"
                    ),
                }
            )
        identity_error = max(
            c["free_baoab"]["one_step_identity_error"] for c in controls
        )
        return {
            "decision": "MEETS"
            if (
                identity_error <= float(opts["identity_tolerance"])
                and all(row["decision"] != "UNRESOLVED" for row in rows)
            )
            else "UNRESOLVED",
            "known_law_decisions": rows,
            "maximum_exact_identity_error": identity_error,
            "free_baoab": controls[0]["free_baoab"],
            "original_observation_controls": controls[0]["observation_controls"],
            "baths": controls[0]["harmonic_baths"],
            "consequential_controls": controls[0]["consequential_controls"],
            "scientific_scope": "CONSTRUCTED_DECISION_LAWS",
        }
    if module == "M1" and not opts["structural_service"]:
        return {
            "decision": "PAIRED_PREPARATION_ONLY" if all(root["status"] == "COMPLETED" for root in roots)
            else "SOME_PAIRED_PREPARATIONS_UNAVAILABLE",
            "assigned_paired_preparations": len(roots),
            "available_paired_preparations": sum(root["status"] == "COMPLETED" for root in roots),
        }
    groups = {
        key: [next(c for c in root["cases"] if c["case_id"] == key) for root in roots]
        for key in case_ids(settings, module)
    }
    if module == "M2":
        from empirical_lawhood.methods.model_free.memory import assess_root_memory
        from .confirmation import common_future_tail_alpha

        result = []
        diagnostics = []
        for key, cases in groups.items():
            available = [case for case in cases if case["status"] == "COMPLETED"]
            diagnostic = {
                "coordinate": key,
                "assigned": len(cases),
                "evaluated": len(available),
            }
            for scope in ("exact_age", "finite_record"):
                counts = [
                    case["binary_history_counts"][scope]
                    if case["status"] == "COMPLETED"
                    else {"root_id": str(root["seed"]), "status": "UNRESOLVED"}
                    for root, case in zip(roots, cases)
                ]
                diagnostic[scope] = assess_root_memory(
                    counts,
                    alpha=alpha / (8 * len(groups)),
                    tolerance=float(opts["risk_budget"]),
                    minimum_support=settings["memory"]["minimum_support"],
                )
            diagnostic["segment_mean_q"] = (
                np.mean([c["segment_mean_q"] for c in available], axis=0).tolist()
                if available
                else None
            )
            diagnostic["segment_mean_energy"] = (
                np.mean([c["segment_mean_energy"] for c in available], axis=0).tolist()
                if available
                else None
            )
            resets = [r for c in available for r in c["reset_controls"]]
            diagnostic["nested_clone_and_reset_checks"] = len(resets)
            diagnostic["exact_clones"] = sum(v["clone_error"] == 0 for v in resets)
            diagnostic["momentum_changed_endpoint"] = sum(
                v["momentum_reset_endpoint_difference"] != 0 for v in resets
            )
            diagnostics.append(diagnostic)
            for method in (
                "always-nonnegative",
                "q",
                "q-velocity",
                "q-velocity-force",
                "q-history",
            ):
                errors = sum(c["exact_age_loss"][method] for c in available)
                n, unknown = len(cases), len(cases) - len(available)
                allowance = common_future_tail_alpha(alpha, len(groups))
                interval = [
                    _one_sided(errors, n, allowance),
                    1 - _one_sided(n - errors - unknown, n, allowance),
                ]
                observed_pooled_mass = (
                    sum(c["pooled_root_loss"][method] for c in available) / n
                )
                pooled_radius = math.sqrt(
                    math.log(8 * len(groups) * 5 / alpha) / (2 * n)
                )
                result.append(
                    {
                        "coordinate": key,
                        "method": method,
                        "assigned": n,
                        "evaluated": len(available),
                        "wrong_decisions": errors,
                        "unknown": unknown,
                        "risk_interval": interval,
                        "pooled_equal_root_loss": None
                        if not available
                        else float(
                            np.mean([c["pooled_root_loss"][method] for c in available])
                        ),
                        "pooled_risk_interval": [
                            max(0.0, observed_pooled_mass - pooled_radius),
                            min(
                                1.0, observed_pooled_mass + unknown / n + pooled_radius
                            ),
                        ],
                        "decision": "MEETS"
                        if interval[1] <= float(opts["risk_budget"])
                        else "EXCEEDS"
                        if interval[0] > float(opts["risk_budget"])
                        else "UNRESOLVED",
                    }
                )
        return {
            "decision": next(
                (
                    row["decision"]
                    for row in result
                    if row["coordinate"] == opts["coordinates"][0]
                    and row["method"] == "q-velocity"
                ),
                "UNRESOLVED",
            ),
            "common_future_risks": result,
            "future_target": "FUTURE_FIXED_PROJECTION_NONNEGATIVE",
            "risk_budget": opts["risk_budget"],
            "history_and_ck": diagnostics,
            "absolute_origin_tick": settings["memory"]["burnin_ticks"]
            + opts["origin_record_age_ticks"],
            "service_lag_ticks": opts["future_lag_ticks"],
            "population": "EXACT_FINITE_AGE_ROOTS_POOLED_ORIGINS_SECONDARY",
            "stationarity_established": False,
        }
    rows = []
    for key, cases in groups.items():
        for handoff in ("fixed", "triggered", "yoked"):
            views = [case["handoffs"][handoff] for case in cases]
            rows.append(
                {
                    "case_id": key,
                    "handoff": handoff,
                    "assigned": len(views),
                    "entered": sum(v["entered"] for v in views),
                    "delivered": sum(v["delivery"] for v in views),
                    "offered": sum(v["offered"] for v in views),
                    "wrong_offers": sum(v["wrong_offer"] for v in views),
                    "persisted": sum(v["preserved"] for v in views),
                    "signed_signal": sum(v["signed_signal"] for v in views),
                    "unknown": sum(v["unknown"] for v in views),
                    "mean_wait_ticks": float(
                        np.mean([v["waiting_ticks"] for v in views])
                    ),
                    "mean_assay_force_calls": float(
                        np.mean([v["assay_force_evaluations"] for v in views])
                    ),
                    "mean_policy_force_calls": float(
                        np.mean([v["policy_force_calls"] for v in views])
                    ),
                    "median_signed_parameter_work": float(
                        np.median([v["preparation_work"]["signed_work"] for v in views])
                    ),
                    "mean_coupling_exposure": np.mean(
                        [v["coupling_exposure"] for v in views], axis=0
                    ).tolist(),
                }
            )
    primary = groups[opts["primary_coordinate"] + "." + opts["primary_recipe"]]
    n = len(primary)
    comparisons = []
    for comparator in ("fixed", "yoked"):
        differences = [
            int(c["handoffs"]["triggered"]["delivery"])
            - int(c["handoffs"][comparator]["delivery"])
            for c in primary
        ]
        unknown_pairs = sum(
            c["handoffs"]["triggered"]["unknown"]
            or c["handoffs"][comparator]["unknown"]
            for c in primary
        )
        halfwidth = paired_delivery_halfwidth(n, alpha)
        diff = float(np.mean(differences))
        waits = [
            c["handoffs"]["triggered"]["waiting_ticks"]
            - c["handoffs"][comparator]["waiting_ticks"]
            for c in primary
        ]
        yes = sum(c["handoffs"]["triggered"]["delivery"] for c in primary)
        wrong = sum(
            c["handoffs"]["triggered"]["wrong_offer"]
            or c["handoffs"]["triggered"]["unknown"]
            for c in primary
        )
        offered = sum(c["handoffs"]["triggered"]["offered"] for c in primary)
        known_correct = sum(
            c["handoffs"]["triggered"]["delivery"]
            and not c["handoffs"]["triggered"]["unknown"]
            for c in primary
        )
        wrong_upper = 1 - _one_sided(n - wrong, n, alpha / 8)
        conditional_upper = (
            1 - _one_sided(known_correct, offered, alpha / 8) if offered else None
        )
        covered = _one_sided(known_correct, n, alpha / 8) >= float(
            opts["minimum_delivery"]
        )
        gain_interval = [
            max(-1.0, diff - halfwidth - 2 * unknown_pairs / n),
            min(1.0, diff + halfwidth + 2 * unknown_pairs / n),
        ]
        savings = [
            c["handoffs"][comparator]["policy_force_calls"]
            - c["handoffs"]["triggered"]["policy_force_calls"]
            for c in primary
        ]
        cheaper_roots = sum(
            s > 0
            and not c["handoffs"]["triggered"]["unknown"]
            and not c["handoffs"][comparator]["unknown"]
            for c, s in zip(primary, savings)
        )
        cheaper_lower = _one_sided(cheaper_roots, n, alpha / 8)
        comparisons.append(
            {
                "comparator": comparator,
                "assigned": n,
                "delivered_gain": diff,
                "trigger_deliveries": yes,
                "trigger_offers": offered,
                "trigger_wrong_assigned_upper": wrong_upper,
                "wrong_given_offer_upper": conditional_upper,
                "unknown_pairs": unknown_pairs,
                "gain_interval": gain_interval,
                "mean_wait_change": float(np.mean(waits)),
                "mean_policy_force_calls_saved": float(np.mean(savings)),
                "probability_cheaper_lower": cheaper_lower,
                "decision": "LOWER_COST_AT_REQUIRED_COVERAGE"
                if (
                    covered
                    and gain_interval[0] >= -float(opts["maximum_coverage_loss"])
                    and wrong_upper <= float(opts["maximum_wrong_delivery"])
                    and cheaper_lower > 0.5
                    and np.mean(savings) > 0
                )
                else "UNRESOLVED",
            }
        )
    return {
        "decision": comparisons[0]["decision"],
        "primary": opts["primary_coordinate"] + "." + opts["primary_recipe"],
        "structural_service": rows,
        "paired_primary": comparisons,
        "total_genuine_returns": sum(
            c["reentries"] for cases in groups.values() for c in cases
        ),
    }
