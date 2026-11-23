# SPDX-License-Identifier: MPL-2.0
"""Native Hessian, physical HS axes and the priced frozen matrix memory model."""

from functools import lru_cache
import numpy as np
from scipy.linalg import block_diag, null_space
from empirical_lawhood.domains.matrix.matrix_factor_response.origin_mechanics import (
    discrete_baoab_maps,
)
from empirical_lawhood.domains.matrix.matrix_factor_response.science import (
    native_position_coordinates as coordinates,
    native_position_lift as lift,
)
from empirical_lawhood.domains.matrix.six_matrix_response.gradients import (
    analytic_gradient_terms,
)
from empirical_lawhood.domains.matrix.six_matrix_response.parameter_derivatives import (
    hessian_image,
)
from empirical_lawhood.domains.matrix.path_thermodynamics.continuation import (
    FORCE,
    HORIZONS,
    RECIPES,
    strength,
)
from empirical_lawhood.domains.matrix.path_thermodynamics.instrument import E, params
from empirical_lawhood.methods.linear_memory.elimination import (
    finite_map_outputs,
    quadratic_noise_map,
    switched_elimination,
)
from empirical_lawhood.methods.retained_gaussian_response import (
    HarmonicBath,
    conditional_reference,
    GaussianReference,
)


@lru_cache(maxsize=1)
def phase_basis():
    other = np.zeros_like(FORCE)
    other[1, 0] = E
    rows = np.stack((coordinates(FORCE), coordinates(other)))
    positions = np.vstack((rows, null_space(rows).T))
    return block_diag(positions, positions)


def phase(q, p):
    return phase_basis() @ np.r_[coordinates(q), coordinates(p)]


def maps(native_q, h, options):
    param = params(float(options["alpha_x"]), float(options["alpha_y"]))
    q = lift(native_q)
    hessian = np.column_stack(
        [coordinates(hessian_image(q, lift(v), param)) for v in np.eye(96)]
    )
    symmetric = (hessian + hessian.T) / 2
    grad = coordinates(analytic_gradient_terms(q, param).total)
    constant = symmetric @ native_q - grad
    forces = np.stack(
        (float(options["amplitude"]) * coordinates(FORCE), constant), axis=1
    )
    decay = np.exp(-h)
    m, b = discrete_baoab_maps(symmetric, forces, timestep=h, decay=decay)
    transform = phase_basis()
    g = quadratic_noise_map(symmetric, h, decay)
    return transform @ m @ transform.T, transform @ b, transform @ g, symmetric, grad


def schedules():
    return np.array(
        [[[strength(recipe, i), 1.0] for recipe in RECIPES] for i in range(128)]
    )


def train_maps(native_q, options):
    h = float(options["timestep"])
    m, b, g, k, grad = maps(native_q, h, options)
    depths = options["kernel_lengths"]
    actions = schedules()
    read, norms = finite_map_outputs(m, b, 2, actions, HORIZONS, depths)
    # A static Schur complement and its affine force define a separate positive
    # position / momentum model; nonsingularity alone does not imply equilibrium.
    axes = phase_basis()[:96, :96]
    stiffness = axes @ k @ axes.T
    external = axes @ (k @ native_q - grad)
    correction = np.linalg.solve(
        stiffness[2:, 2:], np.c_[stiffness[2:, :2], external[2:]]
    )
    static_k = stiffness[:2, :2] - stiffness[:2, 2:] @ correction[:, :2]
    static_f = external[:2] - stiffness[:2, 2:] @ correction[:, 2]
    small, force = discrete_baoab_maps(
        (static_k + static_k.T) / 2,
        np.c_[[float(options["amplitude"]), 0.0], static_f],
        timestep=h,
        decay=np.exp(-h),
    )
    static, _ = finite_map_outputs(small, force, 2, actions, HORIZONS, [128])
    # Independent controls on the same matrix, including hidden preparation,
    # isolated OU injection, ordered switched maps and the physical forcing.
    gen = np.random.default_rng(335109)
    x = gen.normal(size=192)
    full = np.eye(192)
    particular = np.zeros((192, len(RECIPES)))
    errors = []
    for tick, u in enumerate(actions, 1):
        full = m @ full
        particular = m @ particular + b @ u.T
        if tick in HORIZONS:
            errors.append(
                float(
                    np.max(
                        abs(
                            read[-1, HORIZONS.index(tick)]
                            - np.c_[full[:2], particular[:2]]
                        )
                    )
                )
            )
    delta = gen.normal(size=96)
    delta /= np.linalg.norm(delta)
    position = lift(native_q)
    direction = lift(delta)
    native = params(float(options["alpha_x"]), float(options["alpha_y"]))

    def gradient(z):
        return coordinates(analytic_gradient_terms(z, native).total)

    fd = (
        gradient(position + 1e-5 * direction) - gradient(position - 1e-5 * direction)
    ) / (2e-5)
    # A different frozen Hessian supplies a noncommuting physical map for the switch.
    second, _, _, _, _ = maps(native_q + 0.002 * delta, h, options)
    switch = np.stack((m, second, m, second))
    impulses = np.stack((g[:, 0], b[:, 0], -b[:, 0], np.zeros(192)))
    exact = [x]
    for linear, drive in zip(switch, impulses, strict=True):
        exact.append(linear @ exact[-1] + drive)
    ordering = float(
        np.max(
            abs(switched_elimination(switch, impulses, x, 2) - np.stack(exact)[:, :2])
        )
    )
    gcheck = gen.normal(size=96)
    force = coordinates(FORCE) * float(options["amplitude"])
    q0, p0 = np.split(phase_basis().T @ x, 2)
    added = k @ native_q - grad + force
    kick = p0 + h / 2 * (added - k @ q0)
    mid = q0 + h / 2 * kick
    refresh = np.exp(-h) * kick + np.sqrt(-np.expm1(-2 * h)) * gcheck
    q1 = mid + h / 2 * refresh
    p1 = refresh + h / 2 * (added - k @ q1)
    injection = float(
        np.max(
            abs(phase_basis() @ np.r_[q1, p1] - (m @ x + b.sum(axis=1) + g @ gcheck))
        )
    )
    return (
        read,
        static[0],
        {
            "feedback_norm_first_last": [float(norms[0]), float(norms[-1])],
            "full_finite_error": max(errors),
            "switched_error": ordering,
            "hessian_gradient_fd_error": float(np.max(abs(k @ delta - fd))),
            "static_hidden_condition": float(np.linalg.cond(stiffness[2:, 2:])),
            "visible_basis_error": float(
                np.max(abs(phase_basis() @ phase_basis().T - np.eye(192)))
            ),
            "affine_noise_force_error": injection,
            "noise_columns": g.shape[1],
        },
    )


def analytic_controls():
    baths = [
        HarmonicBath(np.array([[3.0]]), np.array([[w]]), np.array([[w * w]]))
        for w in (1.0, 2.0)
    ]
    gaussian = GaussianReference(
        np.array([0.0, 0.0]), np.array([[2.0, 0.8], [0.8, 1.0]]), 1.0
    )
    posterior = conditional_reference(gaussian, (0,), np.array([1.0]))
    return {
        "static_stiffness": [float(h.effective_stiffness[0, 0]) for h in baths],
        "memory_at_one": [float(h.memory(1.0)[0, 0]) for h in baths],
        "memory_error": max(
            abs(float(h.memory(1.0)[0, 0]) - np.cos(w)) for h, w in zip(baths, (1, 2))
        ),
        "conditional_hidden_mean": float(posterior.mean[0]),
    }
