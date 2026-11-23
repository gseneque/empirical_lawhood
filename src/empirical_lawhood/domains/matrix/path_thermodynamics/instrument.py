# SPDX-License-Identifier: MPL-2.0
"""Six-matrix preparation, physical reversal and the BAOAB calorimeter."""

from dataclasses import replace
from decimal import Decimal
from functools import lru_cache

import numpy as np
from scipy.special import logsumexp

from empirical_lawhood.domains.matrix.six_matrix_response.contracts import (
    BetaCouplingRule,
    MatrixIntegratorKind,
    MatrixPrecision,
    SixMatrixResponseModelFamilyMember,
    SixMatrixResponseNumericalView,
)
from empirical_lawhood.domains.matrix.six_matrix_response.gradients import (
    SixMatrixParameters,
    optimized_action_terms,
)
from empirical_lawhood.domains.matrix.six_matrix_response.model import (
    SixMatrixState,
    ideal_positions,
)
from empirical_lawhood.domains.matrix.six_matrix_response.shooting import (
    decode_hermitian_matrices,
)
from empirical_lawhood.domains.matrix.six_matrix_response.simulation import (
    BAOABGradientCache,
    baoab_step_with_hermitian_noise,
)

MEMBER = SixMatrixResponseModelFamilyMember(
    "member.matrix.thermal.symmetric",
    Decimal(".5"),
    Decimal(".5"),
    Decimal(1),
    BetaCouplingRule.PUBLISHED_DETERMINISTIC,
)
U = np.diag([1.0, -1.0, 1.0, -1.0])
D = U / 2
E = np.kron(np.eye(2), np.array([[0.0, 1.0], [1.0, 0.0]])) / 2


@lru_cache(maxsize=32)
def view(h):
    return SixMatrixResponseNumericalView(
        "view.matrix.thermal",
        MatrixIntegratorKind.BAOAB_UNDERDAMPED_LANGEVIN,
        Decimal(str(h)),
        "dimensionless-langevin-time",
        Decimal(1),
        Decimal(1),
        MatrixPrecision.COMPLEX128,
        "numpy.pcg64dxsm",
        "1.0.0",
        "matrix-thermal.independent-purpose",
        512,
    )


def rng(root, purpose):
    return np.random.Generator(
        np.random.PCG64DXSM(np.random.SeedSequence([root, purpose]))
    )


def noise(generator, steps):
    return decode_hermitian_matrices(generator.normal(size=(steps, 2, 3, 16)), n=4)


def hs2(a):
    return float(np.vdot(a, a).real)


def initial(root, purpose, options, *, jitter):
    gen = rng(root, purpose)
    x, y = float(options["alpha_x"]), float(options["alpha_y"])
    origin = ideal_positions(q=2, alpha_tilde_x=x, alpha_tilde_y=y, constitution="11")
    centers = (origin, U @ origin @ U)
    bit = int(gen.integers(2))
    q, p = noise(gen, 2)
    return SixMatrixState(2, centers[bit] + jitter * q, p, 0, x, y), centers


def negative_log_initial(state, centers, jitter, tp):
    logweights = [-hs2(state.positions - c) / (2 * jitter**2) for c in centers]
    return (
        48 * np.log(2 * np.pi * jitter**2)
        + np.log(2)
        - logsumexp(logweights)
        + 48 * np.log(2 * np.pi * tp)
        + hs2(state.momenta) / (2 * tp)
    )


def params(x, y):
    return SixMatrixParameters(2, 0.5, 0.5, 1.0, x, y)


def hamiltonian(state):
    return (
        optimized_action_terms(
            state.positions, params(state.alpha_tilde_x, state.alpha_tilde_y)
        ).total
        + hs2(state.momenta) / 2
    )


def position_ports(q):
    x, y = q
    cubic = 2 * (1j * np.trace(x[0] @ (x[1] @ x[2] - x[2] @ x[1]))).real
    return np.array(
        [np.vdot(D, y[0]).real, np.vdot(E, y[0]).real, hs2(x), cubic, hs2(y)]
    )


def schedule(options, refinement, *, reverse=False, fixed=False):
    ticks, rise = options["cycle_ticks"], options["rise_ticks"]
    clock = np.arange(ticks * refinement + 1) / refinement
    lift = np.where(clock <= rise, clock / rise, (ticks - clock) / (ticks - rise))
    path = float(options["alpha_x"]) + (np.zeros_like(lift) if fixed else lift)
    return path[::-1] if reverse else path


class Ledger:
    def __init__(self, h, *, reverse=False, retain=False):
        self.h, self.reverse = h, reverse
        self.heat = self.work = self.ou_error = self.inverse_error = self.jump_error = (
            0.0
        )
        self.frames = [] if retain else None
        self.first_step = True

    def observe(self, frame):
        h = self.h
        heat = (hs2(frame.p_minus) - hs2(frame.p_plus)) / 2
        self.heat += heat
        decay = np.exp(-h)
        ratio = (
            hs2(frame.p_minus - decay * frame.p_plus)
            - hs2(frame.p_plus - decay * frame.p_minus)
        ) / (-2 * np.expm1(-2 * h))
        self.ou_error = max(self.ou_error, abs(heat - ratio))
        pminus = 2 * (frame.q_mid - frame.q_start) / h
        pplus = 2 * (frame.q_end - frame.q_mid) / h
        self.inverse_error = max(
            self.inverse_error,
            float(
                np.max(
                    np.abs(frame.p_start - (pminus + 0.5 * h * frame.gradient_start))
                )
            ),
            float(np.max(np.abs(frame.p_end - (pplus - 0.5 * h * frame.gradient_end)))),
        )
        q = frame.q_start if self.reverse else frame.q_end
        if frame.couplings_before != frame.couplings_after:
            a, b = params(*frame.couplings_before), params(*frame.couplings_after)
            ports = position_ports(q)
            # Only the cubic and quadratic coefficients change on this drive.
            jump = a.n * (
                (b.alpha_x - a.alpha_x) * ports[3] + (b.beta_x - a.beta_x) * ports[2]
            )
            if self.first_step:
                full = (
                    optimized_action_terms(q, b).total
                    - optimized_action_terms(q, a).total
                )
                self.jump_error = abs(full - jump)
            self.work += jump
        self.first_step = False
        if self.frames is not None:
            self.frames.append(
                np.stack(
                    (
                        frame.q_start,
                        frame.p_start,
                        frame.q_mid,
                        frame.p_minus,
                        frame.p_plus,
                        frame.q_end,
                        frame.p_end,
                    )
                )
            )


def step(state, eta, h, x, cache, recorder=None):
    return baoab_step_with_hermitian_noise(
        state,
        member=MEMBER,
        numerical_view=view(h),
        next_alpha_tilde_x=x,
        next_alpha_tilde_y=state.alpha_tilde_y,
        standardized_noise=eta,
        gradient_cache=cache,
        recorder=recorder,
    )


def trajectory(state, eta, h, values, *, reverse=False, retain=False, project=False):
    ledger = Ledger(h, reverse=reverse, retain=retain)
    initial_energy = hamiltonian(state)
    port_series = [position_ports(state.positions)] if project else None
    cache = BAOABGradientCache()
    for z, x in zip(eta, values[1:], strict=True):
        state = step(state, z, h, float(x), cache, ledger.observe)
        if project:
            port_series.append(position_ports(state.positions))
    final_energy = hamiltonian(state)
    port = position_ports(state.positions)
    metrics = np.array(
        [
            ledger.heat,
            ledger.work,
            final_energy - initial_energy - ledger.work + ledger.heat,
            final_energy,
            port[0],
            port[1],
            ledger.ou_error,
            ledger.inverse_error,
            ledger.jump_error,
        ]
    )
    return (
        state,
        metrics,
        np.array(port_series) if project else None,
        np.stack(ledger.frames) if retain else None,
    )


def reversed_state(state):
    return replace(state, momenta=-state.momenta, step_index=0)
