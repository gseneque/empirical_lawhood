# SPDX-License-Identifier: MPL-2.0
"""An early-window, activity-weighted experiment with independent future-count controls."""

import numpy as np
from scipy.stats import t as student
from empirical_lawhood.methods.marked_process.consequences import (
    apply_projection,
    empirical_residual,
    paired_lower_contributions,
    projection,
)
from empirical_lawhood.methods.path_likelihood.forecast import role
from empirical_lawhood.methods.path_likelihood.scores import mean_interval
from .physics import (
    compressions,
    consequences,
    direct_late_count,
    parameters,
    physical_record,
    receivers,
    replay,
    system,
)

OBSERVERS = ("clock", "last_site", "last_site_age", "last_two", "last_four")
MAX_EVENTS = 64


def random(root, stream):
    return np.random.Generator(
        np.random.PCG64DXSM(np.random.SeedSequence([root, stream]))
    )


def prefix(root, options):
    args = parameters(options)
    basis, _, unitary, _, start = system(*args)
    times, marks, after = physical_record(
        random(root, 1), basis, unitary, start, args[-1], end=2.0
    )
    if len(times) > MAX_EVENTS:
        raise OverflowError("early event record exceeds frozen capacity")
    grids = [receivers(args, r * options["nodes"])[0] for r in (1, 2, 4)]

    def native(t):
        pos = int(np.searchsorted(times, t, side="left"))
        return unitary.propagate(
            after[pos - 1] if pos else start, t - (times[pos - 1] if pos else 0.0)
        )

    return {
        "times": np.pad(times, (0, MAX_EVENTS - len(times))),
        "marks": np.pad(marks, (0, MAX_EVENTS - len(times))),
        "count": len(times),
        "native": np.array([native(t) for t in np.concatenate(grids)]),
        "cutoff": native(2.0),
    }, len(times)


def observe(private, options):
    n = int(private["count"])
    t, m = private["times"][:n], private["marks"][:n]
    clock, _ = receivers(parameters(options), options["nodes"])
    return {
        "codes": compressions(t, m, clock, options["sites"]),
        "times": private["times"],
        "marks": private["marks"],
        "count": n,
    }


def reference(root, private, options, development):
    args = parameters(options)
    basis, _, unitary, _, _ = system(*args)
    rates, kernels, derivatives, nulls = [], [], [], []
    offset = 0
    for refinement in (1, 2, 4):
        nodes = options["nodes"] * refinement
        _, operators = receivers(args, nodes)
        activity, kernel = consequences(
            private["native"][offset : offset + nodes], operators, basis, args[-1]
        )
        offset += nodes
        rates.append(activity)
        kernels.append(kernel[:, :, 0])
        derivatives.append(float((activity * kernel[:, :, 0]).sum(axis=1).mean()))
        nulls.append(float(abs(kernel[:, :, 1]).max()))
    late, marks, _ = physical_record(
        random(root, 2), basis, unitary, private["cutoff"], args[-1], start=2.0
    )
    count = np.sum((late >= 3) & (marks == 0))
    early = np.count_nonzero(private["times"][: int(private["count"])] >= 1)
    shots, sampled = 0, np.zeros(3)
    if development and role(root, options) == 0:
        clock, operators = receivers(args, options["nodes"])
        k = len(clock) // 2
        state = private["native"][k]
        # Sample a positive-activity mark in its physical proportions, then price both futures.
        j = int(
            random(root, 8).choice(basis.l_sites, p=rates[0][k] / rates[0][k].sum())
        )
        after = state * basis.occupations[:, j]
        points = [state, after / np.linalg.norm(after)]
        sampled[2] = kernels[0][k, j]
        for arm, point in enumerate(points):
            for draw in range(options["shooting_tapes"]):
                tt, mm, _ = physical_record(
                    random(root, 100 + 100 * arm + draw),
                    basis,
                    unitary,
                    point,
                    args[-1],
                    start=clock[k],
                )
                sampled[arm] += (
                    np.sum((tt >= 3) & (mm == 0)) / options["shooting_tapes"]
                )
                shots += len(tt)
    return {
        "intensity": rates[0],
        "consequence": kernels[0],
        "refinement": np.asarray(derivatives),
        "all_sites_error": max(nulls),
        "late_count": int(count),
        "early_count": early,
        "score_response": count * (early - args[-1] * basis.particles),
        "shooting": sampled,
        "activity_error": float(
            abs(rates[0].sum(axis=1) - args[-1] * basis.particles).max()
        ),
    }, len(late) + shots


def training(private, observed, truth, options):
    return {
        **truth,
        "codes": observed["codes"],
        "times": observed["times"],
        "marks": observed["marks"],
        "count": observed["count"],
    }


def compressed_predict(codes, tables):
    pred, seen = [], []
    for node, by_observer in enumerate(tables):
        values = [
            apply_projection(codes[..., node, j], table)
            for j, table in enumerate(by_observer)
        ]
        pred.append(np.stack([item[0] for item in values], axis=-2))
        seen.append(np.stack([item[1] for item in values], axis=-1))
    return np.stack(pred, axis=-3), np.stack(seen, axis=-2)


def fit(data, options):
    args = parameters(options)
    train, cal, dev = (data["split"] == j for j in (1, 3, 0))
    x, w, y = (data[k] for k in ("codes", "intensity", "consequence"))
    tables, losses = [], []
    for pooling in options["pooling"]:
        panel = [
            [
                projection(x[train, k, j], w[train, k], y[train, k], float(pooling))
                for j in range(len(OBSERVERS))
            ]
            for k in range(options["nodes"])
        ]
        val, _ = compressed_predict(x[cal], panel)
        loss = np.mean(
            np.sum(w[cal, :, None, :] * (val - y[cal, :, None, :]) ** 2, axis=-1),
            axis=(0, 1),
        )
        tables.append(panel)
        losses.append(loss)
    selected = np.argmin(losses, axis=0)
    model = {
        "tables": [
            [tables[selected[j]][k][j] for j in range(len(OBSERVERS))]
            for k in range(options["nodes"])
        ],
        "pooling": [options["pooling"][i] for i in selected],
    }
    eps = [float(v) for v in options["epsilon"]]
    differences = [
        (direct_late_count(args, e) - direct_late_count(args, -e)) / (2 * e)
        for e in eps
    ]
    shooting = data["shooting"][dev]
    basis, _, unitary, _, initial = system(*args)
    clock, operators = receivers(args, options["nodes"])
    first = np.flatnonzero(dev)[0]
    size = int(data["count"][first])
    states = replay(
        data["times"][first, :size],
        data["marks"][first, :size],
        clock,
        basis,
        unitary,
        initial,
    )
    k = len(clock) // 2
    j = int(np.argmax(w[first, k]))
    after = states[k] * basis.occupations[:, j]
    independent = direct_late_count(
        args, 0, start=clock[k], initial_state=after / np.linalg.norm(after)
    ) - direct_late_count(args, 0, start=clock[k], initial_state=states[k])
    conditional_error = float(abs(independent - y[first, k, j]))
    if conditional_error > 1e-8:
        raise ArithmeticError(
            "conditional count disagrees with direct density integration"
        )
    return {
        "model": model,
        "receivers": list(OBSERVERS),
        "calibration_losses": np.stack(losses).tolist(),
        "conditional_direct_density_error": conditional_error,
        "independent_rate_derivatives": differences,
        "epsilon": eps,
        "shooting_minus_deterministic": mean_interval(
            shooting[:, 1] - shooting[:, 0] - shooting[:, 2]
        ),
        "development_quadrature": data["refinement"][dev].mean(axis=0).tolist(),
    }


def predict(observed, model, options):
    fit, seen = compressed_predict(observed["codes"], model["tables"])
    args = parameters(options)
    basis, _, unitary, _, initial = system(*args)
    time, operators = receivers(args, options["nodes"])
    n = int(observed["count"])
    states = replay(
        observed["times"][:n], observed["marks"][:n], time, basis, unitary, initial
    )
    _, kernel = consequences(states, operators, basis, args[-1])
    return {
        "predictions": fit,
        "seen": seen,
        "replayed": kernel[:, :, 0],
        "codes": observed["codes"],
    }


def measured(private, prediction, truth, options):
    return {
        **truth,
        **prediction,
        "times": private["times"],
        "marks": private["marks"],
        "count": private["count"],
    }


def plugin(codes, w, y):
    return np.mean(
        [
            empirical_residual(codes[:, k], w[:, k], y[:, k])
            for k in range(codes.shape[1])
        ]
    )


def assess(data, model, options):
    w, y = data["intensity"], data["consequence"]
    args = parameters(options)
    total = args[-1] * args[1]
    practical = float(options["margin"]) ** 2
    summary = {}
    alpha = 0.05 / (2 * len(OBSERVERS))
    blocks = np.array_split(np.arange(len(w)), min(24, len(w) // 2))
    for j, name in enumerate(OBSERVERS):
        codes = data["codes"][:, :, j]
        fitted = (w * (y - data["predictions"][:, :, j, :]) ** 2).sum(axis=-1).mean(
            axis=1
        ) / total
        lower = (
            paired_lower_contributions(codes, w, y, maximum_rate=args[-1])
            .sum(axis=-1)
            .mean(axis=1)
            / total
        )
        low, high = (
            mean_interval(lower, alpha=alpha),
            mean_interval(fitted, alpha=alpha),
        )
        loss = plugin(codes, w, y) / total
        deleted = np.array(
            [
                plugin(
                    np.delete(codes, b, axis=0),
                    np.delete(w, b, axis=0),
                    np.delete(y, b, axis=0),
                )
                / total
                for b in blocks
            ]
        )
        error = (len(blocks) - 1) * deleted.std(ddof=1) / np.sqrt(len(blocks))
        radius = student.isf(0.025, len(blocks) - 1) * error
        missing = (w.sum(axis=-1) * ~data["seen"][:, :, j]).mean(axis=1) / total
        summary[name] = {
            "empirical_ideal_squared": loss,
            "delete_group_interval": [loss - radius, loss + radius],
            "independent_pair_lower": low,
            "held_out_fitted_upper": high,
            "decision": (
                "LOST_CONSEQUENCE"
                if low["lower"] > practical
                else "WITHIN_MARGIN"
                if high["upper"] < practical
                else "UNRESOLVED"
            ),
            "unseen_activity_fraction": mean_interval(missing),
            "occupied_cells_by_node": [len(np.unique(col)) for col in codes.T],
        }
    estimates = [mean_interval(col) for col in data["refinement"].T]
    e = float(options["epsilon"][-1])
    reference = (direct_late_count(args, e) - direct_late_count(args, -e)) / (2 * e)
    delta = mean_interval(data["refinement"][:, 0] - reference)
    drift = mean_interval(data["refinement"][:, -1] - data["refinement"][:, 0])
    radius = max(abs(drift["lower"]), abs(drift["upper"]))
    criterion = float(options["derivative_margin"])
    return {
        "observers": summary,
        "common_rate_derivative": estimates,
        "direct_finite_difference": reference,
        "measured_minus_direct": delta,
        "within_derivative_margin": (
            delta["lower"] - radius >= -criterion
            and delta["upper"] + radius <= criterion
        ),
        "refinement_difference": drift,
        "path_score_derivative": mean_interval(data["score_response"]),
        "late_site_count": mean_interval(data["late_count"]),
        "activity_by_node_site": w.mean(axis=0).tolist(),
        "full_replay_max_error": float(abs(y - data["replayed"]).max()),
        "all_sites_null_max": float(data["all_sites_error"].max()),
        "total_activity_max_error": float(data["activity_error"].max()),
        "event_free_prefixes": int((data["count"] == 0).sum()),
        "practical_squared": practical,
        "normalization": total,
        "derivative_margin": criterion,
        "root_counts": len(w),
    }
