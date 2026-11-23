# SPDX-License-Identifier: MPL-2.0
"""Native scalar-drive prefixes and laboratory pulse continuations on the thermal matrix clocks."""

from dataclasses import replace
from functools import lru_cache

import numpy as np

from empirical_lawhood.domains.matrix.six_matrix_response.model import SixMatrixState
from empirical_lawhood.domains.matrix.six_matrix_response.parameter_derivatives import (
    scheduled_force_step,
)
from empirical_lawhood.domains.matrix.six_matrix_response.simulation import (
    BAOABGradientCache,
)
from .instrument import D, E, MEMBER, initial, schedule, step, view
from .physics import paired_tapes

SIGN = np.outer([1.0, -1.0, 1.0, -1.0], [1.0, -1.0, 1.0, -1.0])
UPPER = np.triu_indices(4, 1)
PACK_SIGN = np.r_[np.ones(4), SIGN[UPPER], SIGN[UPPER]]
FORCE = np.zeros((2, 3, 4, 4), dtype=complex)
FORCE[1, 0] = D
HORIZONS = (32, 64, 128)
RECIPES = ("plus", "hold", "minus", "double_plus", "double_minus")


def raw_coordinates(value):
    """Independent native float64 components, with no HS scaling or rounding."""
    return np.concatenate(
        (
            value.diagonal(axis1=-2, axis2=-1).real,
            value[..., UPPER[0], UPPER[1]].real,
            value[..., UPPER[0], UPPER[1]].imag,
        ),
        axis=-1,
    )


def fold(path):
    """Choose one global lift using a fixed order on the whole native record."""
    array = np.asarray(path)
    other = array * PACK_SIGN
    indices = np.flatnonzero(array.ravel() != other.ravel())
    bit = int(
        bool(len(indices)) and array.ravel()[indices[0]] > other.ravel()[indices[0]]
    )
    return (other if bit else array), bit, not len(indices)


def ports(q):
    return np.array([np.vdot(D, q[1, 0]).real, np.vdot(E, q[1, 0]).real])


def reflected(state):
    return replace(
        state, positions=state.positions * SIGN, momenta=state.momenta * SIGN
    )


def clock_states(private, options):
    return [
        SixMatrixState(2, q, p, 0, float(options["alpha_x"]), float(options["alpha_y"]))
        for q, p in zip(private["positions"], private["momenta"], strict=True)
    ]


@lru_cache(maxsize=32)
def _schedule(ticks, rise, alpha_x, refinement):
    return schedule(
        dict(cycle_ticks=ticks, rise_ticks=rise, alpha_x=alpha_x), refinement
    )


def driven_prefix(root, options, *, retain_orbit):
    ticks, burn, h = (
        options["cycle_ticks"],
        options["burn_cycles"],
        float(options["timestep"]),
    )
    jit = float(options["jitter"]) * (1 if root % 2 == 0 else 4)
    start, _ = initial(root, 31, options, jitter=jit)
    states = [start, start]
    histories, bits, stabilizers, errors = [], [], [], []
    full = {}
    updates = 0
    for cycle in range(burn + 1):
        tapes = paired_tapes(root, 1, cycle, ticks, h)
        last = cycle == burn
        for k, r in enumerate((1, 2)):
            state = states[k]
            cache = BAOABGradientCache()
            values = _schedule(ticks, options["rise_ticks"], options["alpha_x"], r)
            history = [ports(state.positions)] if last else []
            if last and retain_orbit:
                twin, twin_cache = reflected(state), BAOABGradientCache()
                record = [
                    raw_coordinates(state.positions),
                    raw_coordinates(state.momenta),
                ]
                peak = 0.0
            for i, (eta, x) in enumerate(zip(tapes[k], values[1:], strict=True)):
                if last and retain_orbit:
                    captured, mirror = [], []
                    state = step(state, eta, h / r, x, cache, captured.append)
                    twin = step(twin, eta * SIGN, h / r, x, twin_cache, mirror.append)
                    # q_start and p_start are the preceding step's exact endpoint.
                    for name in ("q_mid", "p_minus", "p_plus", "q_end", "p_end"):
                        arr = getattr(captured[0], name)
                        peak = max(
                            peak,
                            float(np.max(abs(getattr(mirror[0], name) - arr * SIGN))),
                        )
                        record.append(raw_coordinates(arr))
                    updates += 1
                else:
                    state = step(state, eta, h / r, x, cache)
                updates += 1
                if last and (i + 1) % r == 0:
                    history.append(ports(state.positions))
            states[k] = state
            if last:
                histories.append(history[-17:])
                if retain_orbit:
                    canonical, bit, fixed = fold(np.stack(record))
                    full["orbit_" + str(r)] = canonical
                    bits.append(bit)
                    stabilizers.append(fixed)
                    errors.append(peak)
    result = dict(
        positions=np.stack([s.positions for s in states]),
        momenta=np.stack([s.momenta for s in states]),
        history=np.array(histories),
        velocity=np.stack([ports(s.momenta) for s in states]),
    )
    if retain_orbit:
        result.update(
            full,
            lift=np.asarray(bits),
            stabilizer=np.asarray(stabilizers),
            equivariance=np.asarray(errors),
        )
    return result, updates


def pulse_scales(options):
    h = float(options["timestep"])
    return float(options["amplitude"]) * 8 * h * (np.array(HORIZONS) * h - 4 * h)


def strength(recipe, tick):
    if recipe == "hold":
        return 0
    sign = 1 if recipe.endswith("plus") else -1
    if tick < 8:
        return sign
    return -sign if recipe.startswith("double") and 32 <= tick < 40 else 0


def shoot(
    state, tape, options, refinement, recipe, *, amplitude_factor=1.0, trace=False
):
    r = refinement
    h = float(options["timestep"]) / r
    values = _schedule(
        options["cycle_ticks"], options["rise_ticks"], options["alpha_x"], r
    )
    readings = [np.r_[ports(state.positions), ports(state.momenta)]] if trace else []
    cache = BAOABGradientCache()
    for i, eta in enumerate(tape):
        x = values[(i + 1) % (len(values) - 1)]
        amp = strength(recipe, i // r) * float(options["amplitude"]) * amplitude_factor
        if amp:
            state = scheduled_force_step(
                state,
                direction=FORCE,
                amplitude=amp,
                member=MEMBER,
                numerical_view=view(h),
                next_alpha_tilde_x=x,
                next_alpha_tilde_y=state.alpha_tilde_y,
                standardized_noise=eta,
                gradient_cache=cache,
            )
        else:
            state = step(state, eta, h, x, cache)
        if trace and (i + 1) % r == 0:
            readings.append(np.r_[ports(state.positions), ports(state.momenta)])
        elif not trace and i + 1 in (32 * r, 64 * r, 128 * r):
            readings.append(ports(state.positions))
    return np.asarray(readings)


def futures(
    root,
    private,
    options,
    *,
    recipes,
    tapes,
    purpose,
    twins=False,
    clocks=(1, 2),
    amplitude_factor=1.0,
    trace=False,
):
    """Result axes are clock, lift, future tape, pulse recipe, horizon and receiver."""
    states = clock_states(private, options)
    result = np.empty(
        (
            len(clocks),
            2 if twins else 1,
            tapes,
            len(recipes),
            129 if trace else 3,
            4 if trace else 2,
        )
    )
    for j in range(tapes):
        coupled = paired_tapes(root, purpose, j, 128, float(options["timestep"]))
        for k, r in enumerate(clocks):
            for lift in range(result.shape[1]):
                state = reflected(states[r - 1]) if lift else states[r - 1]
                eta = coupled[r - 1] * SIGN if lift else coupled[r - 1]
                for a, recipe in enumerate(recipes):
                    result[k, lift, j, a] = shoot(
                        state,
                        eta,
                        options,
                        r,
                        recipe,
                        amplitude_factor=amplitude_factor,
                        trace=trace,
                    )
    return result, sum(clocks) * 128 * result.shape[1] * tapes * len(recipes)
