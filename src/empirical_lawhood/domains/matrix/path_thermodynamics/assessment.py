# SPDX-License-Identifier: MPL-2.0
"""Root-level calorimetry, invertible observation and physical-direction tests."""

import numpy as np
from scipy.stats import t
from empirical_lawhood.methods.path_likelihood.scores import mean_interval
from .instrument import position_ports, schedule
from .observations import observe
from .physics import FAMILIES, STEPS, WINDOWS


def linear_intercept(samples, windows):
    return (
        samples @ np.linalg.pinv(np.column_stack((np.ones(len(windows)), windows)))[0]
    )


def slopes(samples):
    result = {}
    for i, (name, targets) in enumerate((("equal", (0, 0, 0)), ("hot", (96, -48, 48)))):
        terms = {}
        for j, (component, target) in enumerate(
            zip(("bath", "system", "total"), targets)
        ):
            grid = samples[:, i, :, :, j]
            fine = linear_intercept(grid[:, :, -1], WINDOWS)
            previous = linear_intercept(grid[:, :, -2], WINDOWS)
            short = linear_intercept(grid[:, :2, -1], WINDOWS[:2])
            # Paired differences account for shared noise across windows and views.
            # Three intervals per temperature share the error for a total-slope gate.
            alpha = 0.05 / 6
            row = mean_interval(fine, alpha)
            components = [
                mean_interval(v, alpha) for v in (fine - previous, fine - short)
            ]
            allowance = sum(max(abs(v["lower"]), abs(v["upper"])) for v in components)
            row.update(
                target=target,
                allowance=allowance,
                paired_numerical_differences=components,
                widened=[row["lower"] - allowance, row["upper"] + allowance],
                finite_window_steps=[
                    {"window": float(w), "steps": k, **mean_interval(grid[:, wi, ki])}
                    for wi, w in enumerate(WINDOWS)
                    for ki, k in enumerate(STEPS)
                ],
            )
            row["within_margin"] = bool(
                row["widened"][0] >= target - 2.4 and row["widened"][1] <= target + 2.4
            )
            terms[component] = row
        result[name] = terms
    result["passed"] = (
        all(result[name]["total"]["within_margin"] for name in ("hot", "equal"))
        and result["hot"]["bath"]["widened"][0] > 0
        and result["hot"]["system"]["widened"][1] < 0
    )
    return result


def dispersed_interval(a, b, alpha):
    if min(len(a), len(b)) < 2:
        return None
    variance = np.array([v.var(ddof=1) / len(v) for v in (a, b)])
    diff = float(a.mean() - b.mean())
    if not np.any(variance):
        return {"mean": diff, "lower": diff, "upper": diff}
    df = variance.sum() ** 2 / (variance**2 / np.array([len(a) - 1, len(b) - 1])).sum()
    radius = float(t.isf(alpha / 2, df) * np.sqrt(variance.sum()))
    return {"mean": diff, "lower": diff - radius, "upper": diff + radius}


def cycles(sets, roots, freeze):
    names = ("heat", "work", "shadow", "energy", "even", "odd")
    rows, diagnostics = {}, {}
    margins = (
        {
            key: 0.1 * float(sets["forward"][:, -2:, 1, j].ravel().std(ddof=1))
            for j, key in enumerate(names)
        }
        if freeze is None
        else freeze["stationarity_margins"]
    )
    for kind, data in sets.items():
        rows[kind] = {
            k: [
                {
                    "coarse": mean_interval(view[:, 0]),
                    "fine": mean_interval(view[:, 1]),
                    "fine_minus_coarse": mean_interval(view[:, 1] - view[:, 0]),
                }
                for view in data[:, :, :, j].transpose(1, 0, 2)
            ]
            for j, k in enumerate(names)
        }
        if kind not in ("forward", "fixed"):
            continue
        checks = {}
        for j, key in enumerate(names):
            value = data[:, -1, 1, j]
            # Independent groups were assigned alternately before any draws.
            drift = mean_interval(value - data[:, -2, 1, j], 0.05 / 20)
            dispersed = dispersed_interval(
                value[roots % 2 == 0], value[roots % 2 == 1], 0.05 / 20
            )
            view = mean_interval(value - data[:, -1, 0, j], 0.05 / 20)
            bias = max(abs(view["lower"]), abs(view["upper"]))
            checks[key] = {
                "previous_cycle_difference": drift,
                "start_group_difference": dispersed,
                "view_allowance": bias,
                "margin": margins[key],
                "within_margin": dispersed is not None
                and all(
                    max(abs(v["lower"]), abs(v["upper"])) + bias <= margins[key]
                    for v in (drift, dispersed)
                ),
            }
        diagnostics[kind] = checks
    return rows, diagnostics, margins


def frames_check(batches, options):
    rows = []
    for meta, data in batches:
        if meta["full_frame_root"] is None:
            continue
        root = meta["full_frame_root"]
        index = int(np.flatnonzero(data["evaluable_root"] == root)[0])
        for name in ("forward", "reverse"):
            for view in (1, 2):
                q0, p0, qm, pm, pp, q1, p1 = np.moveaxis(
                    data[f"{name}_frames_{view}"], 1, 0
                )
                h = float(options["timestep"]) / view
                delta_minus = 2 * (qm - q0) / h
                delta_plus = 2 * (q1 - qm) / h
                heat = float(0.5 * np.sum((np.abs(pm) ** 2 - np.abs(pp) ** 2)))
                registered = data[name + "_cycles"][index, -1, view - 1, 0]
                ports = np.stack([position_ports(q) for q in [q0[0], *q1]])
                stored = data[f"{name}_ports_{view}"][index]
                rows.append(
                    {
                        "root": root,
                        "direction": name,
                        "view": view,
                        "intervals": len(q0),
                        "midpoint_inverse": float(
                            max(
                                np.max(np.abs(delta_minus - pm)),
                                np.max(np.abs(delta_plus - pp)),
                            )
                        ),
                        "physical_inverse": float(
                            max(
                                np.max(np.abs(2 * (qm - q1) / h + pp)),
                                np.max(np.abs(2 * (q0 - qm) / h + pm)),
                            )
                        ),
                        "position_continuity": float(np.max(np.abs(q1[:-1] - q0[1:]))),
                        "momentum_continuity": float(np.max(np.abs(p1[:-1] - p0[1:]))),
                        "ports_error": float(np.max(np.abs(ports - stored))),
                        "heat_sum_error": abs(heat - registered),
                    }
                )
    return rows


def evaluate(options, batches, freeze):
    assigned = np.concatenate([a["root"] for _, a in batches])
    good = np.concatenate([a["evaluable_root"] for _, a in batches])
    failures = [f for meta, _ in batches for f in meta["root_failures"]]
    if len(set(assigned)) != len(assigned) or sorted(
        [*good, *(f["root"] for f in failures)]
    ) != sorted(assigned):
        raise ValueError("incomplete path family measurement census")
    result = {
        "assigned": len(assigned),
        "evaluable": len(good),
        "root_range": [int(assigned.min()), int(assigned.max())],
        "failures": failures,
        "native_intervals": sum(meta["native_intervals"] for meta, _ in batches),
        "phase": "DEVELOPMENT" if freeze is None else "HELD_OUT",
        "cycle_duration": options["cycle_ticks"] * float(options["timestep"]),
        "burn_cycles": options["burn_cycles"],
        "periodic_endpoint_entropy_bound": None,
    }
    if len(good) < 2 or (freeze is not None and "decision" not in freeze):
        result["disposition"] = "INSUFFICIENT_EVALUABLE_ROOTS_OR_FROZEN_DECISION"
        return result

    def stack(key):
        return np.concatenate([a[key] for _, a in batches if len(a["evaluable_root"])])

    result["transient"] = slopes(stack("transient"))
    if options.get("panel") == "preparation":
        result.pop("cycle_duration")
        result.pop("burn_cycles")
        result.pop("periodic_endpoint_entropy_bound")
        result["decision"] = {
            "windows": WINDOWS.tolist(),
            "steps": list(STEPS),
            "margin": 2.4,
            "terms": ["bath", "system", "total"],
        }
        if freeze is not None and result["decision"] != freeze["decision"]:
            raise ValueError("preparation assessment changed its frozen slope rule")
        return result
    sets = {k: stack(k + "_cycles") for k in FAMILIES}
    decision = None if freeze is None else freeze["decision"]
    result["cycles"], result["stationarity"], margins = cycles(sets, good, decision)
    result["stationarity_diagnostics_pass"] = all(
        result["stationarity"]["forward"][k]["within_margin"]
        for k in ("heat", "work", "energy", "even", "odd")
    )
    result["frames"] = frames_check(batches, options)
    result["clock"] = {
        "coarse_h": options["timestep"],
        "refinement": 2,
        "rise_ticks": options["rise_ticks"],
        "phase": "start and end of the first measured cycle after burn",
        "forward_parameters": schedule(options, 1).tolist(),
    }
    maxima = np.max(
        [np.max(a[:, :, :, 6:], axis=(0, 1, 2)) for a in sets.values()], axis=0
    )
    result["ledger_maxima"] = dict(
        zip(("ou_density", "endpoint_momentum", "native_jump_work"), maxima.tolist())
    )
    result["recorder_pass"] = (
        len(result["frames"]) == 4
        and max(maxima) < 1e-8
        and all(
            max(
                r[k]
                for k in (
                    "midpoint_inverse",
                    "physical_inverse",
                    "heat_sum_error",
                    "ports_error",
                    "momentum_continuity",
                    "position_continuity",
                )
            )
            < 1e-8
            for r in result["frames"]
        )
    )
    frozen_rule = None if decision is None else decision["observation"]
    rule, coarse, labels = observe(
        options, stack("forward_ports_1"), stack("reverse_ports_1"), frozen_rule
    )
    _, fine, fine_labels = observe(
        options,
        stack("forward_ports_2")[:, ::2],
        stack("reverse_ports_2")[:, ::2],
        rule,
    )
    result["observations"] = {
        "primary": "endpoints-1",
        "coarse": coarse,
        "fine": fine,
        "labels": labels,
        "fine_labels": fine_labels,
    }
    result["decision"] = {"stationarity_margins": margins, "observation": rule}
    result["irreversibility_test_pass"] = (
        freeze is not None
        and not failures
        and result["recorder_pass"]
        and min(table["endpoints-1"]["lower"] for table in (coarse, fine)) > 0
    )
    return result
