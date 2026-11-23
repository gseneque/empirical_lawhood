# SPDX-License-Identifier: MPL-2.0
"""Causal propagation after elimination, including the independently prepared hidden state."""

import numpy as np


def impulse_hankel(transition, forcing, receiver, horizons):
    """Singular spectra of finite block Hankel matrices for a specified input and receiver."""
    m, b, c = map(np.asarray, (transition, forcing, receiver))
    if (
        not horizons
        or min(horizons) < 1
        or m.shape != (len(m), len(m))
        or b.shape[0] != len(m)
        or c.shape[1] != len(m)
    ):
        raise ValueError("block Hankel requires consistent maps and positive horizons")
    column = b
    blocks = []
    for _ in range(2 * max(horizons) - 1):
        blocks.append(c @ column)
        column = m @ column
    result = []
    for h in horizons:
        hankel = np.block([[blocks[i + j] for j in range(h)] for i in range(h)])
        spectrum = np.linalg.svd(hankel, compute_uv=False)
        tolerance = float(max(hankel.shape) * np.finfo(float).eps * spectrum[0])
        result.append(
            {
                "horizon": h,
                "shape": list(hankel.shape),
                "singular_values": spectrum.tolist(),
                "absolute_tolerance": tolerance,
                "numerical_rank": int(np.count_nonzero(spectrum > tolerance)),
            }
        )
    return result


def switched_elimination(transitions, inputs, state, visible, *, memory=None):
    """Propagate visible coordinates using ordered hidden products, exact at full depth."""
    maps, forcing = np.asarray(transitions), np.asarray(inputs)
    state = np.asarray(state)
    if (
        maps.ndim != 3
        or maps.shape[1:] != (len(state), len(state))
        or forcing.shape != (len(maps), len(state))
        or not 0 < visible < len(state)
    ):
        raise ValueError(
            "switched elimination requires aligned full maps, vectors and a proper visible split"
        )
    depth = len(maps) if memory is None else memory
    if type(depth) is not int or depth < 0:
        raise ValueError("memory length must be nonnegative")
    initial = state[visible:].copy()
    previous = state[:visible]
    contributions = []
    result = [previous]
    for m, b in zip(maps, forcing, strict=True):
        hidden = initial + sum(contributions, np.zeros_like(initial))
        result.append(
            m[:visible, :visible] @ previous
            + m[:visible, visible:] @ hidden
            + b[:visible]
        )
        new = m[visible:, :visible] @ previous + b[visible:]
        hh = m[visible:, visible:]
        initial = hh @ initial
        contributions = (
            ([hh @ v for v in contributions] + [new])[-depth:] if depth else []
        )
        previous = result[-1]
    return np.array(result)


def finite_map_outputs(transition, channels, visible, schedules, horizons, depths):
    """Receiver maps for many initial states, forcing schedules and kernel truncations.

    The initial hidden-state term is propagated to every horizon. The selected
    depth truncates past visible feedback and hidden forcing, as declared.
    Output axes are depth, horizon, visible coordinate, then either initial
    coordinate or the particular input schedule.
    """
    m, b, u = map(np.asarray, (transition, channels, schedules))
    n, v = len(m), visible
    if m.shape != (n, n) or b.shape[0] != n or u.ndim != 3 or u.shape[2] != b.shape[1]:
        raise ValueError("incompatible finite kernel drive axes")
    steps, recipes, _ = u.shape
    if not 0 < v < n or not horizons or max(horizons) > steps or min(horizons) < 1:
        raise ValueError("receiver horizons must lie inside the supplied schedule")
    eye = np.eye(n)
    row = m[:v, v:].copy()
    hidden_rows, feedback, hidden_force = [], [], []
    for _ in range(steps):
        hidden_rows.append(row)
        feedback.append(row @ m[v:, :v])
        hidden_force.append(row @ b[v:])
        row = row @ m[v:, v:]
    outputs = []
    for depth in depths:
        if type(depth) is not int or depth < 0:
            raise ValueError("invalid feedback depth")
        previous = [np.c_[eye[:v], np.zeros((v, recipes))]]
        for k in range(steps):
            value = m[:v, :v] @ previous[-1]
            value[:, v:n] += hidden_rows[k]
            value[:, n:] += b[:v] @ u[k].T
            for lag in range(min(k, depth)):
                j = k - 1 - lag
                value += feedback[lag] @ previous[j]
                value[:, n:] += hidden_force[lag] @ u[j].T
            previous.append(value)
        outputs.append(np.stack([previous[i] for i in horizons]))
    return np.stack(outputs), np.asarray([np.linalg.norm(q) for q in feedback])


def quadratic_noise_map(hessian, timestep, decay):
    """Injection of the unit-temperature standard normal at BAOAB's OU refresh."""
    n = len(hessian)
    q = timestep / 2 * np.eye(n)
    return np.vstack((q, np.eye(n) - timestep / 2 * np.asarray(hessian) @ q)) * np.sqrt(
        1 - decay**2
    )
