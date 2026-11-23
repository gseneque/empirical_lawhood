# SPDX-License-Identifier: MPL-2.0
"""Physical jump record, deterministic replay and independent late-count reference."""

from functools import lru_cache
import numpy as np
from scipy.integrate import solve_ivp
from scipy.linalg import expm

from empirical_lawhood.domains.quantum.trajectory_burnin_screen.basis import build_basis
from empirical_lawhood.domains.quantum.trajectory_burnin_screen.operators import (
    DenseEigensystemPropagator,
    build_hamiltonian,
    lindblad_superoperator,
    site_occupations,
)
from empirical_lawhood.domains.quantum.trajectory_burnin_screen.types import Action


@lru_cache(maxsize=16)
def system(sites, particles, xy, zz, gamma):
    basis = build_basis(sites, particles)
    ham = build_hamiltonian(basis, action=Action.HOLD, epsilon=0, j_xy=xy, j_z=zz)
    unitary = DenseEigensystemPropagator(ham)
    operator = lindblad_superoperator(basis, ham, gamma=gamma).toarray()
    initial = basis.state_vector((1 << particles) - 1)
    return basis, ham, unitary, operator, initial


def parameters(opts):
    return (
        opts["sites"],
        opts["particles"],
        float(opts["j_xy"]),
        float(opts["j_z"]),
        float(opts["gamma"]),
    )


def physical_record(
    random, basis, unitary, initial, gamma, *, start=0.0, end=4.0, early_log_rate=0.0
):
    """Draw from the integrated hazard across exact piecewise rate boundaries."""
    times, marks, states = [], [], []
    time, state = start, initial.copy()
    while time < end:
        hazard = random.exponential()
        candidate = time
        for boundary in sorted({v for v in (1.0, 2.0, end) if time < v <= end}):
            rate = (
                gamma
                * basis.particles
                * (np.exp(early_log_rate) if 1 <= candidate < 2 else 1.0)
            )
            width = boundary - candidate
            if hazard < rate * width:
                candidate += hazard / rate
                break
            hazard -= rate * width
            candidate = boundary
        if candidate >= end:
            break
        state = unitary.propagate(state, candidate - time)
        mass = site_occupations(basis, state)
        mark = int(random.choice(basis.l_sites, p=mass / mass.sum()))
        state = (state * basis.occupations[:, mark]) / np.sqrt(mass[mark])
        times.append(candidate)
        marks.append(mark)
        states.append(state.copy())
        time = candidate
    return np.array(times), np.array(marks, dtype="int64"), states


@lru_cache(maxsize=64)
def receivers(args, nodes):
    basis, _, _, gen, _ = system(*args)
    gamma = args[-1]
    n = basis.dimension
    count = gamma * np.stack(
        [
            np.diag(basis.occupations[:, 0]).ravel(order="F"),
            np.eye(n).ravel(order="F") * basis.particles,
        ]
    )
    extended = np.zeros((n * n + 2, n * n + 2), complex)
    extended[: n * n, : n * n] = gen
    extended[n * n :, : n * n] = count
    integrated = expm(extended)[n * n :, : n * n]
    clock = 1 + (np.arange(nodes) + 0.5) / nodes
    operators = [integrated @ expm((3 - t) * gen) for t in clock]
    return clock, np.array(
        [[v.reshape(n, n, order="F").T for v in a] for a in operators]
    )


def replay(times, marks, nodes, basis, unitary, initial):
    cursor, clock, state = 0, 0.0, initial.copy()
    out = []
    for t in nodes:
        while cursor < len(times) and times[cursor] < t:
            z = (
                unitary.propagate(state, times[cursor] - clock)
                * basis.occupations[:, marks[cursor]]
            )
            state = z / np.linalg.norm(z)
            clock = times[cursor]
            cursor += 1
        out.append(unitary.propagate(state, t - clock))
    return np.asarray(out)


def consequences(states, observables, basis, gamma):
    projected = states[:, None, :] * basis.occupations.T[None, :, :]
    mass = np.sum(abs(projected) ** 2, axis=-1)
    activity = gamma * mass
    post = np.divide(
        projected,
        np.sqrt(mass)[..., None],
        out=np.zeros_like(projected),
        where=mass[..., None] > 0,
    )
    pre_value = np.einsum("ti,trij,tj->tr", states.conj(), observables, states).real
    post_value = np.einsum("tmi,trij,tmj->tmr", post.conj(), observables, post).real
    kernel = np.where(mass[..., None] > 0, post_value - pre_value[:, None, :], 0.0)
    return activity, kernel


def compressions(times, marks, nodes, sites):
    # Sentinel 0. Nonzero tokens code the site and the elapsed physical gap.
    rows = []
    radix = 1 + 3 * sites
    for t in nodes:
        end = np.searchsorted(times, t, side="left")
        past = list(range(end - 1, max(-1, end - 5), -1))
        code = 0
        codes = []
        previous = t
        for j in range(4):
            token = 0
            if j < len(past):
                i = past[j]
                age = int(
                    np.searchsorted([0.25, 0.75], previous - times[i], side="right")
                )
                token = 1 + 3 * int(marks[i]) + age
                previous = times[i]
            code = code * radix + token
            codes.append(code)
        rows.append(
            [0, int(marks[end - 1]) + 1 if end else 0, codes[0], codes[1], codes[3]]
        )
    return np.asarray(rows, dtype="<i8")


def direct_late_count(args, epsilon, *, start=0.0, initial_state=None):
    """Independent density-matrix ODE, integrating the physical count on [3,4)."""
    basis, sparse, _, _, initial = system(*args)
    ham = sparse.toarray()
    n = basis.dimension
    occupancy = basis.occupations
    # For diagonal occupation projectors this is the full sum of dissipators.
    decay = -0.5 * np.sum((occupancy[:, None, :] - occupancy[None, :, :]) ** 2, axis=2)
    psi = initial if initial_state is None else initial_state
    state = np.r_[np.outer(psi, psi.conj()).ravel(), 0j]
    for left, right in ((0.0, 1.0), (1.0, 2.0), (2.0, 3.0), (3.0, 4.0)):
        if right <= start:
            continue
        gamma = args[-1] * (np.exp(epsilon) if left == 1 else 1.0)

        def rhs(t, value):
            rho = value[:-1].reshape(n, n)
            derivative = -1j * (ham @ rho - rho @ ham) + gamma * decay * rho
            count = (
                gamma * np.dot(rho.diagonal(), occupancy[:, 0]) if left == 3 else 0.0
            )
            return np.r_[derivative.ravel(), count]

        solved = solve_ivp(
            rhs,
            (max(start, left), right),
            state,
            method="DOP853",
            rtol=2e-12,
            atol=1e-13,
        )
        if not solved.success:
            raise ArithmeticError(solved.message)
        state = solved.y[:, -1]
    return float(state[-1].real)
