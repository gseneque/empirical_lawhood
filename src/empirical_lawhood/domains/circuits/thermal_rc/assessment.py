# SPDX-License-Identifier: MPL-2.0
"""Independent assessments at fixed phases, grid refinements and memory lags."""

import numpy as np
from scipy.integrate import quad
from scipy.linalg import toeplitz
from scipy.stats import t

from empirical_lawhood.methods.path_likelihood.scores import (
    gaussian_joint_log_density,
    gaussian_log_density,
    mean_interval,
)
from empirical_lawhood.methods.retained_gaussian_response import (
    GaussianReference,
    conditional_reference,
)
from .physics import LAGS, PHASES, SETTINGS, forward_mean, independent_mean, means


def finite_lag(phase, h, driven):
    dm = forward_mean(phase + h, driven) - forward_mean(phase, driven)
    variance = -2 * np.expm1(-h)
    return float(2 * dm**2 / (h * (variance + dm**2))), float(
        2 * dm**2 / (h * variance)
    )


def correlation(delta, h, alpha):
    n = len(delta)
    half = n // 2
    second = np.mean(delta**2)
    point = 2 * delta[:half].mean() * delta[half:].mean() / (h * second)
    mu, m2 = mean_interval(delta, alpha / 2), mean_interval(delta**2, alpha / 2)
    a, b = mu["lower"], mu["upper"]
    lower = min(a * a, b * b) if a * b > 0 else 0.0
    return {
        "estimate": float(point),
        "lower": float(2 * lower / (h * m2["upper"])),
        "upper": float(2 * max(a * a, b * b) / (h * m2["lower"]))
        if m2["lower"] > 0
        else None,
    }


def path_ratio(path, fmean, rmean, rates, h):
    """Evaluate physical P against time-reversed R on the same voltages."""

    def score(obs, mu):
        centered = obs.copy()
        centered[:, :, 0] -= mu
        decay = np.exp(-h * rates)
        var = -np.expm1(-2 * h * rates)
        return gaussian_log_density(centered[:, 0], 0.0, 1.0) + gaussian_log_density(
            centered[:, 1:], centered[:, :-1] * decay, var
        ).sum(axis=1)

    return score(path, fmean) - score(path[:, ::-1], rmean)


def memory_score(path, rate):
    sums = path[:, :, 1:].sum(axis=2)
    lags = np.arange(sums.shape[1])
    cov = np.exp(-0.25 * lags) + np.exp(-rate * 0.25 * lags)
    a = cov[1] / cov[0]
    measured = mean_interval(
        (sums[:, -1] - a * sums[:, -2]) * (sums[:, -3] - a * sums[:, -2])
    )
    errors = {}
    observation = np.ones(2)
    decay = np.diag(np.exp(-0.25 * np.array([1.0, rate])))
    for depth in (1, 2, 4, 8):
        history = sums[:, -depth - 1 : -1]
        coeff = np.linalg.solve(toeplitz(cov[:depth]), cov[1 : depth + 1][::-1])
        dense = history @ coeff
        # Exact two-state filter with a noiseless scalar observation.
        means_ = np.zeros((len(sums), 2))
        variance = np.eye(2)
        for sample in history.T:
            gain = variance @ observation / (observation @ variance @ observation)
            means_ += (sample - means_.sum(axis=1))[:, None] * gain
            variance -= np.outer(gain, observation @ variance)
            means_ = means_ @ decay.T
            variance = decay @ variance @ decay.T + np.eye(2) - decay @ decay.T
        errors[str(depth)] = {
            "mse": float(np.mean((dense - sums[:, -1]) ** 2)),
            "filter_discrepancy": float(np.max(np.abs(means_.sum(axis=1) - dense))),
        }
    gaussian = GaussianReference(np.zeros(3), toeplitz(cov[:3]), 1.0)
    truth = float(conditional_reference(gaussian, (1,), (0.0,)).covariance[0, 1])
    return {"analytic": truth, "measured": measured, "prediction": errors}


def correlation_panel(voltages, phase, driven):
    n = len(voltages)
    target = float((np.cos(phase) + np.sin(phase)) ** 2 / 4) if driven else 0.0
    if abs(target) < 1e-28:
        target = 0.0
    values, blind = [], []
    for j, h in enumerate(LAGS):
        lag = voltages[:, j + 1] - voltages[:, 0]
        dx = lag[:, 0] + forward_mean(phase + h, driven) - forward_mean(phase, driven)
        analytic, transpose = finite_lag(phase, h, driven)
        row = correlation(dx, h, 0.05 / len(LAGS))
        values.append(
            {
                **row,
                "lag": float(h),
                "analytic": analytic,
                "transposed_pair_kl_rate": transpose,
            }
        )
        blind.append(correlation(lag[:, 1:].sum(axis=1), h, 0.05 / len(LAGS)))
    # Quadratic zero-lag intercept on the fixed five longest lags.
    # Paired root influence carries cross-lag covariance through extrapolation.
    grid = LAGS[1:]
    weights = np.linalg.pinv(np.column_stack((np.ones(len(grid)), grid, grid**2)))[0]
    increments = voltages[:, 2:, 0] - voltages[:, :1, 0]
    increments += forward_mean(phase + grid, driven) - forward_mean(phase, driven)
    mu, m2 = increments.mean(axis=0), (increments**2).mean(axis=0)
    influences = 4 * mu / (grid * m2) * (increments - mu) - 2 * mu**2 / (
        grid * m2**2
    ) * (increments**2 - m2)
    intercept = float(weights @ [v["estimate"] for v in values[1:]])
    error = float(
        t.isf(0.025, n - 1) * np.std(influences @ weights, ddof=1) / np.sqrt(n)
    )
    bias = abs(float(weights @ [v["analytic"] for v in values[1:]]) - target)
    # The zero-rate null is nonregular. Propagate simultaneous finite-lag
    # limits through the same signed intercept, also on the squared scale.
    finite_limits = all(v["upper"] is not None for v in values[1:])
    if target == 0 and not finite_limits:
        lo, hi = None, None
    elif target == 0:
        lo = sum(
            w * (v["lower"] if w >= 0 else v["upper"])
            for w, v in zip(weights, values[1:])
        )
        hi = sum(
            w * (v["upper"] if w >= 0 else v["lower"])
            for w, v in zip(weights, values[1:])
        )
    else:
        lo, hi = intercept - error, intercept + error
    return {
        "instantaneous_epr": target,
        "finite_lags": values,
        "blind_lags": blind,
        "empirical_limit": {
            "estimate": intercept,
            "lower": float(lo - bias) if lo is not None else None,
            "upper": float(hi + bias) if hi is not None else None,
            "extrapolation_bias_allowance": bias,
            "within_margin": bool(
                lo is not None
                and lo - bias >= target - 0.025
                and hi + bias <= target + 0.025
            ),
        },
    }


def evaluate(settings, batches, freeze):
    arrays = {k: np.concatenate([a[k] for _, a in batches]) for k in batches[0][1]}
    roots = arrays["root"]
    if len(np.unique(roots)) != len(roots):
        raise ValueError("thermal triplet repeated between batches")
    rate = float(settings["hidden_rate"])
    rates = np.array([1.0, 1.0, rate])
    output = {
        "assigned": len(roots),
        "evaluable": len(roots),
        "root_range": [int(roots.min()), int(roots.max())],
        "memory": {},
        "phases": {},
        "exact_period_entropy": float(np.pi / 2),
    }
    for index, (label, phase) in enumerate(zip(SETTINGS, PHASES)):
        output["phases"][label] = correlation_panel(
            arrays["lag_voltages"], phase, index != 2
        )
    if settings.get("panel") == "correlation":
        output.pop("memory")
        return output
    distinct_signal = (np.exp(-0.25) - np.exp(-rate * 0.25)) ** 2 / 2
    for name, r in (("distinct", rate), ("equal", 1.0)):
        result = memory_score(arrays[name + "_memory"], r)
        interval = result["measured"]
        result["equivalent"] = bool(
            max(abs(interval[k] - result["analytic"]) for k in ("lower", "upper"))
            <= distinct_signal / 4
        )
        output["memory"][name] = result
    for index, (label, phase) in enumerate(zip(SETTINGS, PHASES)):
        driven = index != 2
        paths = []
        for stride in (4, 2, 1):
            clock = np.arange(0, 17, stride) / 16
            fmu, rmu = (
                means(phase, clock, reverse=reverse, driven=driven)
                for reverse in (False, True)
            )
            p = arrays["forward_nodes"][:, ::stride].copy()
            p[:, :, 0] += fmu
            r = arrays["reverse_nodes"][:, ::stride].copy()
            r[:, :, 0] += rmu
            forward = path_ratio(p, fmu, rmu, rates, stride / 16)
            backward = path_ratio(r[:, ::-1], fmu, rmu, rates, stride / 16)
            cx = toeplitz(np.exp(-clock))
            cs = cx + toeplitz(np.exp(-rate * clock))
            obs = p[:, :, 1:].sum(axis=2)
            # Independent covariance solve also scores the summed-voltage marginal.
            observed = (
                gaussian_joint_log_density(p[:, :, 0], fmu, cx)
                - gaussian_joint_log_density(p[:, ::-1, 0], rmu, cx)
                + gaussian_joint_log_density(obs, np.zeros(len(clock)), cs)
                - gaussian_joint_log_density(obs[:, ::-1], np.zeros(len(clock)), cs)
            )
            delta = fmu - rmu[::-1]
            exact = float(0.5 * delta @ np.linalg.solve(cx, delta))
            wrong_clock = forward_mean(phase + 1 + clock, driven)
            wrong_clock += np.exp(-clock) * (
                forward_mean(phase + 1, driven) - wrong_clock[0]
            )
            wrong = path_ratio(p, fmu, wrong_clock, rates, stride / 16)
            paths.append(
                {
                    "steps": len(clock) - 1,
                    "exact_grid_kl": exact,
                    "forward_kl": mean_interval(forward.sum(axis=1)),
                    "reverse_kl": mean_interval(-backward.sum(axis=1)),
                    "full_observed_max_error": float(
                        np.max(np.abs(observed - forward.sum(axis=1)))
                    ),
                    "hidden_log_ratio_max": float(np.max(np.abs(forward[:, 1:]))),
                    "wrong_protocol_mean_log_ratio": float(wrong.sum(axis=1).mean()),
                }
            )
        qerror = max(
            abs(
                independent_mean(phase, x, reverse=v, driven=driven)
                - means(phase, x, reverse=v, driven=driven)
            )
            for x in np.linspace(0, 1, 17)
            for v in (True, False)
        )
        output["phases"][label].update(
            {
                "continuous_window_kl": float(
                    quad(lambda u: (np.cos(u) + np.sin(u)) ** 2 / 4, phase, phase + 1)[
                        0
                    ]
                )
                if driven
                else 0.0,
                "path": paths,
                "transition_quadrature_max": float(qerror),
            }
        )
    output["transition_and_reversal_verified"] = all(
        v["transition_quadrature_max"] < 1e-12
        and max(p["full_observed_max_error"] for p in v["path"]) < 1e-10
        for v in output["phases"].values()
    )
    return output
