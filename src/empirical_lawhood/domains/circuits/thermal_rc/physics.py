# SPDX-License-Identifier: MPL-2.0
"""Exact three-branch thermal circuit on a dimensionless clock."""

import numpy as np
from scipy.integrate import quad

LAGS = np.array([1, 2, 4, 8, 16, 32]) / 128
PHASES = (0.0, 3 * np.pi / 4, 0.0)
SETTINGS = ("positive", "zero", "equilibrium")
PATH_NODES = 17


def forward_mean(t, driven=True):
    return (np.sin(t) - np.cos(t)) / 2 if driven else np.zeros_like(t)


def reverse_particular(terminal, s, driven=True):
    return (
        (np.sin(terminal - s) + np.cos(terminal - s)) / 2
        if driven
        else np.zeros_like(s)
    )


def means(phase, clock, *, reverse, driven):
    if not reverse:
        return forward_mean(phase + clock, driven)
    terminal = phase + 1.0
    return reverse_particular(terminal, clock, driven) + np.exp(-clock) * (
        forward_mean(terminal, driven) - reverse_particular(terminal, 0.0, driven)
    )


def independent_mean(phase, s, *, reverse, driven):
    start = phase + 1 if reverse else phase
    value = forward_mean(start, driven) * np.exp(-s)
    if driven:
        direction = -1 if reverse else 1
        value += quad(
            lambda u: np.exp(u - s) * np.sin(start + direction * u),
            0.0,
            s,
            epsabs=1e-13,
        )[0]
    return float(value)


def normals(first, count, ticks, stream):
    """Counter per root and purpose. Batching preserves each original tape."""
    width = 4 * ((3 * (ticks + 1) + 3) // 4)
    bitgen = np.random.Philox(
        counter=first * (width // 4), key=0xEF3422026112300 + stream
    )
    bits = bitgen.random_raw(count * width).reshape(count, width)
    uniform = ((bits >> np.uint64(11)).astype(float) + 0.5) * 2.0**-53
    radii = np.sqrt(-2 * np.log(uniform[:, 0::2]))
    angles = 2 * np.pi * uniform[:, 1::2]
    z = np.empty_like(uniform)
    z[:, 0::2], z[:, 1::2] = radii * np.cos(angles), radii * np.sin(angles)
    return z[:, : 3 * (ticks + 1)].reshape(count, ticks + 1, 3)


def stationary_path(innovations, rates, dt):
    """G/C sets decay and TG/C² sets diffusion, with T=C_i=1 here."""
    rates = np.asarray(rates)
    intervals = np.broadcast_to(dt, (innovations.shape[1] - 1,))
    decay = np.exp(-intervals[:, None] * rates)
    scale = np.sqrt(-np.expm1(-2 * intervals[:, None] * rates))
    path = np.empty_like(innovations)
    path[:, 0] = innovations[:, 0]
    for i in range(1, path.shape[1]):
        path[:, i] = decay[i - 1] * path[:, i - 1] + scale[i - 1] * innovations[:, i]
    return path


def acquire(settings, first, count, freeze):
    rates = [1.0, 1.0, float(settings["hidden_rate"])]
    if settings.get("panel") == "correlation":
        # Exact transitions on the six physical intervals have the same
        # joint law as selecting these times from the fine-clock process.
        data = stationary_path(
            normals(first, count, len(LAGS), 4), rates, np.diff(LAGS, prepend=0.0)
        )
        return {
            "clock": "model-time",
            "centered_voltages": True,
            "root_failures": [],
            "native_intervals": count * len(LAGS),
        }, {"root": np.arange(first, first + count, dtype="<i8"), "lag_voltages": data}
    forward = stationary_path(normals(first, count, 128, 1), rates, 1 / 128)
    reverse = stationary_path(normals(first, count, 128, 2), rates, 1 / 128)
    memory_noise = normals(first, count, 8, 3)
    arrays = {
        "root": np.arange(first, first + count, dtype="<i8"),
        "forward_nodes": forward[:, ::8],
        "reverse_nodes": reverse[:, ::8],
        "lag_voltages": forward[:, [0, 1, 2, 4, 8, 16, 32]],
        "distinct_memory": stationary_path(memory_noise, rates, 0.25),
        "equal_memory": stationary_path(memory_noise, [1.0, 1.0, 1.0], 0.25),
    }
    return {
        "clock": "model-time",
        "centered_voltages": True,
        "independent_reverse_bank": True,
        "root_failures": [],
        "native_intervals": count * (256 + 16),
    }, arrays
