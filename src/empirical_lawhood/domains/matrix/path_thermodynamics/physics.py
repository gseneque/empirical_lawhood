# SPDX-License-Identifier: MPL-2.0
"""Matched physical clocks, terminal bank and independent reversed continuations."""

from dataclasses import replace
import numpy as np

from empirical_lawhood.domains.matrix.six_matrix_response.shooting import (
    brownian_bridge_split,
)
from empirical_lawhood.domains.matrix.six_matrix_response.simulation import (
    BAOABGradientCache,
)
from .instrument import (
    hs2,
    initial,
    negative_log_initial,
    noise,
    reversed_state,
    rng,
    schedule,
    step,
    trajectory,
)

WINDOWS = np.array([0.001, 0.002, 0.004])
STEPS = (4, 8, 16)
FAMILIES = ("forward", "terminal_bank", "reverse", "fixed")


def transient(root, options):
    jitter = float(options["jitter"])
    nominal, centers = initial(root, 11, options, jitter=jitter)
    finest = 0.001 / 16
    original_noise = noise(rng(root, 12), 64)
    result = np.zeros((2, 3, 3, 3))
    work = 0
    for stride in (1, 2, 4, 8, 16):
        h = stride * finest
        selected = {
            (round(w / h), i, j)
            for i, w in enumerate(WINDOWS)
            for j, k in enumerate(STEPS)
            if abs(w / h - k) < 1e-10
        }
        if not selected:
            continue
        last = max(v[0] for v in selected)
        weights = np.exp(-finest * np.arange(stride - 1, -1, -1))
        weights /= np.linalg.norm(weights)
        pulses = np.einsum(
            "j,ij...->i...",
            weights,
            original_noise[: stride * last].reshape(last, stride, 2, 3, 4, 4),
        )
        for arm, tp in enumerate((1.0, 2.0)):
            for psign in (-1, 1):
                start = replace(nominal, momenta=psign * np.sqrt(tp) * nominal.momenta)
                cross0 = negative_log_initial(start, centers, jitter, tp)
                for sign in (-1, 1):
                    state, cache, bath = start, BAOABGradientCache(), 0.0
                    for tick, pulse in enumerate(pulses, 1):

                        def receive(frame):
                            nonlocal bath
                            bath += 0.5 * (hs2(frame.p_minus) - hs2(frame.p_plus))

                        state = step(
                            state, sign * pulse, h, state.alpha_tilde_x, cache, receive
                        )
                        work += 1
                        for limit, i, j in selected:
                            if tick == limit:
                                system = (
                                    negative_log_initial(state, centers, jitter, tp)
                                    - cross0
                                )
                                result[arm, i, j] += np.array(
                                    [bath, system, bath + system]
                                ) / (4 * WINDOWS[i])
    return result, work


def paired_tapes(root, purpose, cycle, ticks, h):
    coarse = noise(rng(root, 1000 + 100 * purpose + cycle), ticks)
    extra = noise(rng(root, 2000 + 100 * purpose + cycle), ticks)
    first, last = brownian_bridge_split(
        coarse_noise=coarse, bridge_noise=extra, half_decay=float(np.exp(-h / 2))
    )
    fine = np.stack((first, last), axis=1).reshape(2 * ticks, 2, 3, 4, 4)
    return coarse, fine


def acquire_root(root, options, retain):
    journal = {}
    journal["transient"], updates = transient(root, options)
    if options.get("panel") == "preparation":
        return journal, updates
    ticks, burn, h = (
        options["cycle_ticks"],
        options["burn_cycles"],
        float(options["timestep"]),
    )
    terminal = None
    jitter = float(options["jitter"]) * (1 if root % 2 == 0 else 4)
    for name, purpose in zip(FAMILIES, (1, 2, 3, 4)):
        reverse, fixed = name == "reverse", name == "fixed"
        if reverse:
            states = [reversed_state(state) for state in terminal]
        else:
            start, _ = initial(root, 30 + purpose, options, jitter=jitter)
            states = [start, start]
        cycles = 1 if reverse else burn + 1
        rows = np.empty((cycles, 2, 9))
        schedules = [schedule(options, r, reverse=reverse, fixed=fixed) for r in (1, 2)]
        for cycle in range(cycles):
            tapes = paired_tapes(root, purpose, cycle, ticks, h)
            last = cycle == cycles - 1
            for i, r in enumerate((1, 2)):
                keep = last and retain and name in ("forward", "reverse")
                project = last and name in ("forward", "reverse")
                state, metrics, ports, frames = trajectory(
                    states[i],
                    tapes[i],
                    h / r,
                    schedules[i],
                    reverse=reverse,
                    retain=keep,
                    project=project,
                )
                states[i] = state
                updates += r * ticks
                rows[cycle, i] = metrics
                if project:
                    journal[name + "_ports_" + str(r)] = ports
                if keep:
                    journal[name + "_frames_" + str(r)] = frames
        journal[name + "_cycles"] = rows
        if name == "terminal_bank":
            terminal = tuple(states)
    return journal, updates


def acquire(options, first, count, freeze):
    collected, full, failures = {}, {}, []
    roots = np.arange(first, first + count, dtype="<i8")
    good, work = [], 0
    for root in roots:
        try:
            measured, native = acquire_root(
                int(root), options, int(root) == options["retained_root"]
            )
        except (FloatingPointError, OverflowError, np.linalg.LinAlgError) as exc:
            failures.append(
                {"root": int(root), "reason": type(exc).__name__, "message": str(exc)}
            )
            continue
        if not all(np.isfinite(x).all() for x in measured.values()):
            failures.append({"root": int(root), "reason": "NONFINITE_PATH"})
            continue
        good.append(root)
        work += native
        for name, value in measured.items():
            if "_frames_" in name:
                full[name] = value
            else:
                collected.setdefault(name, []).append(value)
    arrays = {k: np.stack(values) for k, values in collected.items()}
    arrays.update(full, root=roots, evaluable_root=np.array(good, dtype="<i8"))
    return {
        "root_failures": failures,
        "native_intervals": work,
        "full_frame_root": options["retained_root"] if full else None,
        "frame_order": [
            "q_start",
            "p_start",
            "q_mid",
            "p_minus",
            "p_plus",
            "q_end",
            "p_end",
        ],
        "cycle_metrics": [
            "bath_heat",
            "protocol_work",
            "shadow_work",
            "energy",
            "y_even",
            "y_odd",
            "ou_error",
            "inverse_error",
            "jump_error",
        ],
    }, arrays
