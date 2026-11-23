# SPDX-License-Identifier: MPL-2.0
"""Training-only causal estimators for a blind composed pulse and coherent future trajectory."""

import numpy as np
from empirical_lawhood.domains.matrix.path_thermodynamics.instrument import schedule
from empirical_lawhood.domains.matrix.path_thermodynamics.continuation import (
    HORIZONS,
    RECIPES,
    pulse_scales,
    strength,
)
from empirical_lawhood.methods.statistics.conditional_response import (
    ridge_fit,
    ridge_predict,
)
from .linear import train_maps

AR_MODELS = ("present", "history_1", "history_4", "history_8", "history_16", "momentum")
KERNEL_MODELS = (
    "static",
    "kernel_1",
    "kernel_4",
    "kernel_8",
    "kernel_16",
    "kernel_128",
    "unconditional_kernel",
)
NAMES = ("drive_mean",) + AR_MODELS + KERNEL_MODELS


def features(q, previous, velocity, drive, action, name, h):
    values = [q]
    if name.startswith("history"):
        length = int(name.split("_")[1])
        increments = (
            np.diff(
                np.concatenate((previous[..., -length:, :], q[..., None, :]), axis=-2),
                axis=-2,
            )
            / h
        )
        values.append(increments.reshape(q.shape[:-1] + (-1,)))
    if name == "momentum":
        values.append(velocity)
    t, u = np.broadcast_arrays(drive, action, np.empty(q.shape[:-1]))[:2]
    return np.concatenate((*values, t[..., None], u[..., None]), axis=-1)


def training_rows(history, traces, options, name):
    # axes: root, tape, recipe, tick, port. Train only on the three single-pulse arms.
    h = float(options["timestep"])
    q = traces[..., :-1, :2]
    prefix = np.broadcast_to(history[:, None, None, -17:-1, :], q.shape[:-2] + (16, 2))
    joined = np.concatenate((prefix, q), axis=-2)
    windows = np.lib.stride_tricks.sliding_window_view(joined, 17, axis=-2).swapaxes(
        -2, -1
    )
    cycle = schedule(options, 1)[:-1]
    t = cycle[(np.arange(128) + 1) % len(cycle)]
    u = np.array([[strength(recipe, i) for i in range(128)] for recipe in RECIPES[:3]])
    x = features(q, windows[..., :-1, :], traces[..., :-1, 2:], t, u, name, h)
    count = 4 if name == "momentum" else 2
    y = np.diff(traces[..., :count], axis=-2) / h
    return x.reshape(-1, x.shape[-1]), y.reshape(-1, count)


def recursive_mean(histories, velocity, options, name, fit, recipes):
    h = float(options["timestep"])
    hist = np.repeat(histories[:, None], len(recipes), axis=1)
    v = np.repeat(velocity[:, None], len(recipes), axis=1)
    outputs = []
    cycle = schedule(options, 1)[:-1]
    for tick in range(128):
        q = hist[:, :, -1]
        u = np.array([strength(recipe, tick) for recipe in recipes])
        x = features(q, hist[:, :, :-1], v, cycle[(tick + 1) % len(cycle)], u, name, h)
        diff = ridge_predict(x, fit) * h
        new = q + diff[..., :2]
        if name == "momentum":
            v = v + diff[..., 2:]
        hist = np.concatenate((hist[:, :, 1:], new[:, :, None]), axis=2)
        if tick + 1 in HORIZONS:
            outputs.append(new)
    return np.stack(outputs, axis=2)


def drive_mean(curve):
    # Apply the learned single-pulse displacement at its native lag.
    hold = curve[1]
    first = (curve[0] - curve[2]) / 2
    second = np.zeros_like(first)
    second[32:] = first[:-32]
    all_recipes = np.stack(
        (curve[0], hold, curve[2], hold + first - second, hold - first + second)
    )
    return all_recipes[:, HORIZONS, :]


def hidden_features(hist):
    return hist[:, -9:, :].reshape(len(hist), -1)


def all_means(history, velocity, model, options):
    n = len(history)
    output = [np.broadcast_to(np.asarray(model["baseline"]), (n, 5, 3, 2))]
    output.extend(
        recursive_mean(history, velocity, options, name, fit, RECIPES)
        for name, fit in zip(AR_MODELS, model["ar"], strict=True)
    )
    state = ridge_predict(hidden_features(history), model["initial"])
    state[:, :2] = history[:, -1]
    static = np.array(model["static"])
    state4 = state[:, [0, 1, 96, 97]]

    def project(weights, x):
        size = x.shape[1]
        component = np.einsum("hvi,ni->nhv", weights[:, :, :size], x)
        return component[:, None, :, :] + weights[:, :, size:].transpose(2, 0, 1)[None]

    output.append(project(static, state4))
    read = np.asarray(model["kernels"])
    output.extend(project(w, state) for w in read)
    unconditional = np.broadcast_to(model["mean_state"], state.shape).copy()
    unconditional[:, :2] = history[:, -1]
    output.append(project(read[-1], unconditional))
    return np.stack(output, axis=1)


def signed(mean, options, composed):
    plus, minus = (3, 4) if composed else (0, 2)
    return (mean[..., plus, :, :] - mean[..., minus, :, :]) / (
        2 * pulse_scales(options)[:, None]
    )


def fit_models(data, options):
    train, select, cal = (data["split"] == i for i in (1, 2, 3))
    histories, velocities = data["history"][:, 0], data["velocity"][:, 0]
    trace = data["trace"]
    truth = data["levels"][:, 0].mean(axis=1)
    scaled = pulse_scales(options)
    # One target per root for selection, regardless of the number of tapes.
    std = np.maximum(
        trace[train][:, :, :, HORIZONS, :2].reshape(-1, 3, 2).std(axis=0), 1e-8
    )
    scores, models = [], []
    for name in AR_MODELS:
        x, y = training_rows(histories[train], trace[train], options, name)
        choices = []
        errors = []
        for penalty in options["ridge"]:
            fitted = ridge_fit(x, y, float(penalty))
            pred = recursive_mean(
                histories[select],
                velocities[select],
                options,
                name,
                fitted,
                RECIPES[:3],
            )
            target = truth[select]
            sign = (
                (pred[:, 0, 1, 0] - pred[:, 2, 1, 0])
                - (target[:, 0, 1, 0] - target[:, 2, 1, 0])
            ) / (2 * scaled[1])
            errors.append(
                float(np.mean(((pred - target) / std) ** 2) + np.mean(sign**2))
            )
            choices.append(fitted)
        scores.append(errors)
        models.append(choices[int(np.argmin(errors))])
    source = data["native_q"][train].mean(axis=0)
    kernels, static, controls = train_maps(source, options)
    start = ridge_fit(
        hidden_features(histories[train]), data["phase_state"][train], 1.0
    )
    model = {
        "ar": models,
        "kernels": kernels.tolist(),
        "static": static.tolist(),
        "mean_state": data["phase_state"][train].mean(axis=0).tolist(),
        "initial": start,
        "baseline": drive_mean(trace[train].mean(axis=(0, 1))[:, :, :2]).tolist(),
        "scale": std.tolist(),
        "training_reference_q": source.tolist(),
    }
    means = all_means(histories, velocities, model, options)
    # Distribution of complete six-vectors, measured on training roots and HOLD/plus/minus.
    residual = (data["levels"][train, 0][:, None] - means[train, :, None, :3]).reshape(
        train.sum(), len(NAMES), -1, 6
    )
    covs = []
    for i in range(len(NAMES)):
        vectors = residual[:, i].reshape(-1, 6)
        covariance = np.cov(vectors.T) + 1e-14 * np.eye(6)
        covs.append(np.linalg.cholesky(covariance))
    model["cholesky"] = np.array(covs).tolist()
    sigmas = np.sqrt(np.sum(np.array(covs) ** 2, axis=-1)).reshape(len(covs), 3, 2)
    score = np.max(
        abs((data["levels"][cal, 0, 0, 0, None] - means[cal, :, 0]) / sigmas),
        axis=(-1, -2),
    )
    rank = min(len(score), int(np.ceil(0.9 * (len(score) + 1)))) - 1
    model["band"] = np.sort(score, axis=0)[rank].tolist()
    scl = scaled[1]
    ds = (
        (means[select, :, 0, 1, 0] - means[select, :, 2, 1, 0])
        - (truth[select, 0, 1, 0] - truth[select, 2, 1, 0])[:, None]
    ) / (2 * scl)
    errs = np.mean(
        ((means[select, :, :3] - truth[select, None]) / std) ** 2, axis=(0, 2, 3, 4)
    ) + np.mean(ds**2, axis=0)
    winner = int(np.argmin(errs))
    model["winner"] = winner
    return model, {
        "controls": controls,
        "penalty_losses": scores,
        "selection_loss": errs.tolist(),
        "selected": NAMES[winner],
        "band_rank": rank + 1,
        "band_calibration_roots": int(cal.sum()),
    }
