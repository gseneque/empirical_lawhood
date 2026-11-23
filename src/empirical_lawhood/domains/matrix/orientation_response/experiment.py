# SPDX-License-Identifier: MPL-2.0
"""Paired laboratory pulses, independently shot conditional means and bit-informed repair."""

import numpy as np

from empirical_lawhood.domains.matrix.path_thermodynamics.continuation import (
    RECIPES,
    driven_prefix,
    futures,
    pulse_scales,
)
from empirical_lawhood.methods.path_likelihood.forecast import role
from empirical_lawhood.methods.statistics.conditional_response import (
    independent_product,
    paired_mean_loss,
    ridge_fit,
    ridge_predict,
    root_interval,
)

EXCLUDE_REDUCTION = ("orbit_1", "orbit_2")


def prefix(root, options):
    private, work = driven_prefix(root, options, retain_orbit=True)
    if role(root, options) == 4:
        oracle, steps = futures(
            root,
            private,
            options,
            recipes=("plus", "minus"),
            tapes=options["oracle_tapes"],
            purpose=39,
        )
        private["oracle"] = (
            (oracle[:, 0, :, 0, :, 1] - oracle[:, 0, :, 1, :, 1])
            / (2 * pulse_scales(options))
        ).mean(axis=1)
        work += steps
    return private, work


def observe(private, options):
    # Exactly one canonical path is released to both physical lifts. The derived
    # features exclude its provenance, the native lift and all future innovations.
    out = []
    for k, r in enumerate((1, 2)):
        frames = private["orbit_" + str(r)]
        # 2 starting frames followed by q_mid, p_minus, p_plus, q_end, p_end per tick.
        tail = frames[-5 * 16 * r :].reshape(16 * r, 5, 2, 3, 16)
        q, p = tail[-1, 3], tail[-1, 4]
        earlier = tail[0, 0]
        out.append(
            np.r_[
                q[1, 0],
                p[1, 0],
                (q - earlier)[1, 0],
                np.sum(q * q, axis=(-1, -2)),
                np.sum(p * p, axis=(-1, -2)),
            ]
        )
    return {"features": np.asarray(out), "orientation_bit": private["lift"]}


def reference(root, private, options, development):
    raw, n = futures(
        root,
        private,
        options,
        recipes=RECIPES[:3],
        tapes=options["tapes"],
        purpose=31,
        twins=True,
    )
    controls = np.zeros(2)
    if development and role(root, options) == 0:
        half, m = futures(
            root,
            private,
            options,
            recipes=("plus", "minus"),
            tapes=1,
            purpose=31,
            twins=True,
            amplitude_factor=0.5,
        )
        zero, z = futures(
            root,
            private,
            options,
            recipes=("plus", "minus"),
            tapes=1,
            purpose=31,
            twins=True,
            amplitude_factor=0.0,
        )
        controls[0] = np.max(abs(zero[:, :, :, 0] - zero[:, :, :, 1]))
        full_difference = raw[:, :, :1, 0] - raw[:, :, :1, 2]
        controls[1] = np.max(
            abs(2 * (half[:, :, :, 0] - half[:, :, :, 1]) - full_difference)
        )
        n += m + z
    return {"readings": raw, "amplitude_controls": controls}, n


def contrast(raw, options):
    return (raw[:, :, :, 0, :, 1] - raw[:, :, :, 2, :, 1]) / (2 * pulse_scales(options))


def training(private, observed, truth, options):
    return {
        **observed,
        **truth,
        **{
            key: private[key]
            for key in ("lift", "equivariance", "stabilizer", "orbit_1", "orbit_2")
        },
    }


def fit(data, options):
    where = data["split"]
    train, cal = where == 1, where == 3
    # Each canonical response is averaged over matched future noise, one row per root.
    native = np.stack(
        [contrast(v, options)[:, 0].mean(axis=1) for v in data["readings"]]
    )
    target = native * (1 - 2 * data["lift"])[..., None]
    fits, cv = [], []
    for clock in range(2):
        features = data["features"][:, clock]
        scores, candidates = [], []
        for penalty in options["ridge"]:
            candidate = ridge_fit(features[train], target[train, clock], float(penalty))
            predicted = ridge_predict(features[cal], candidate)
            scores.append(
                float(np.mean((predicted[:, 1] - target[cal, clock, 1]) ** 2))
            )
            candidates.append(candidate)
        fits.append(candidates[int(np.argmin(scores))])
        cv.append(scores)
    return dict(
        model={"fits": fits},
        calibration_loss_by_penalty=cv,
        development_amplitude_controls=np.max(
            data["amplitude_controls"], axis=0
        ).tolist(),
        maximum_twin_prefix_error=float(data["equivariance"].max()),
        training=int(train.sum()),
        calibration=int(cal.sum()),
    )


def predict(observed, model, options):
    magnitude = np.stack(
        [
            ridge_predict(v, f)
            for v, f in zip(observed["features"], model["fits"], strict=True)
        ]
    )
    return {
        "canonical_response": magnitude,
        "bit_informed": magnitude * (1 - 2 * observed["orientation_bit"])[:, None],
        "folded_response": np.zeros_like(magnitude),
    }


def measured(private, prediction, truth, options):
    return {
        **prediction,
        **truth,
        **{
            key: private[key]
            for key in ("lift", "oracle", "equivariance", "stabilizer")
        },
    }


def assess(data, model, options):
    raw = data["readings"]
    contrasts = np.stack([contrast(a, options) for a in raw])
    panels = np.stack([a.mean(axis=3) for a in np.split(contrasts, 2, axis=3)])
    a, b = panels
    g = independent_product(a[:, :, 0] - a[:, :, 1], b[:, :, 0] - b[:, :, 1]) / 4
    signs = (1 - 2 * data["lift"])[..., None]
    issued = data["bit_informed"]
    perm = np.random.default_rng(298113).permutation(len(signs))
    methods = {
        "folded_zero": data["folded_response"],
        "bit_informed": issued,
        "shuffled_bit": data["canonical_response"] * signs[perm],
        "native_shooting": data["oracle"],
    }
    losses = {
        key: (
            paired_mean_loss(p, a[:, :, 0], b[:, :, 0])
            + paired_mean_loss(-p, a[:, :, 1], b[:, :, 1])
        )
        / 2
        for key, p in methods.items()
    }
    primary = g[:, 0, 1]
    stats = lambda values: root_interval(values, alpha=0.025)
    interval = stats(primary)
    grid = stats(g[:, 1, 1] - primary)
    bias = max(abs(grid["lower"]), abs(grid["upper"]))
    limits = [interval["lower"] - bias, interval["upper"] + bias]
    margin = float(options["margin"]) ** 2
    decision = (
        "PRACTICALLY_CONSEQUENTIAL"
        if limits[0] > margin
        else "BELOW_PRACTICAL_MARGIN"
        if limits[1] < margin
        else "UNRESOLVED"
    )
    improvement = stats((losses["folded_zero"] - losses["bit_informed"])[:, 0, 1])
    repaired = stats(losses["bit_informed"][:, 0, 1])
    gain = losses["folded_zero"] - losses["bit_informed"]

    def grid_allowance(quantity):
        limits = stats(quantity[:, 1, 1] - quantity[:, 0, 1])
        return max(abs(limits["lower"]), abs(limits["upper"]))

    gain_floor = improvement["lower"] - grid_allowance(gain)
    repair_ceiling = repaired["upper"] + grid_allowance(losses["bit_informed"])
    even_error = float(abs(raw[:, :, 0, ..., 0] - raw[:, :, 1, ..., 0]).max())
    corotated_error = float(abs(raw[:, :, 0, ..., 1] + raw[:, :, 1, ..., 1]).max())
    equivariance = float(data["equivariance"].max())
    controls = max(even_error, corotated_error, equivariance) < 1e-9
    if not controls:
        decision = "NUMERICAL_CONTROLS_FAILED"
    return dict(
        ambiguity=decision,
        primary_ambiguity_squared=interval,
        fine_minus_primary=grid,
        widened_squared_interval=limits,
        practical_margin_squared=margin,
        ambiguity_by_clock_horizon=[
            [stats(g[:, k, j]) for j in range(3)] for k in range(2)
        ],
        conditional_mean_losses={key: stats(v[:, 0, 1]) for key, v in losses.items()},
        bit_loss_improvement=improvement,
        grid_adjusted_gain_lower=gain_floor,
        grid_adjusted_bit_error_upper=repair_ceiling,
        repair=(
            "ADEQUATE_AND_IMPROVED"
            if controls and gain_floor > 0 and repair_ceiling < margin
            else "NOT_ESTABLISHED"
        ),
        stabilizer_clock_rows=int(data["stabilizer"].sum()),
        controls={
            "pass": controls,
            "twin_prefix_max": equivariance,
            "co_rotated_max": corotated_error,
            "even_port_max": even_error,
            "even_direct_signal": float(
                np.mean(
                    (raw[:, 0, 0, :, 0, 1, 0] - raw[:, 0, 0, :, 2, 1, 0])
                    / (2 * pulse_scales(options)[1])
                )
            ),
        },
        native_port_mean_by_lift_arm_horizon=raw[:, 0].mean(axis=(0, 2)).tolist(),
        scaled_increment_from_hold=(
            np.stack(
                (
                    (raw[:, 0, :, :, 0] - raw[:, 0, :, :, 1]),
                    (raw[:, 0, :, :, 2] - raw[:, 0, :, :, 1]),
                )
            ).mean(axis=(1, 3))
            / pulse_scales(options)[:, None]
        ).tolist(),
        units=pulse_scales(options).tolist(),
        primary_horizon=64,
        dissipation="UNRESOLVED_ON_MATCHED_PREFIX",
        scope="RECEIVER_ONLY_NUMERICAL_PILOT",
    )
