"""Composable native preparations and interventions for fresh matrix trials.

No historical source, campaign, storage, scheduler or verdict lives here.  A
caller supplies a root's random generator and receives immutable native states.
All force and derivative equations are the shared six-matrix scientific cores.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal

import numpy as np

from empirical_lawhood.domains.matrix.six_matrix_response.contracts import (
    BetaCouplingRule, MatrixIntegratorKind, MatrixPrecision,
    SixMatrixResponseModelFamilyMember, SixMatrixResponseNumericalView,
)
from empirical_lawhood.domains.matrix.six_matrix_response.model import (
    SixMatrixState, hermitian_part, ideal_state,
)
from empirical_lawhood.domains.matrix.six_matrix_response.parameter_derivatives import (
    hessian_image, parameters, scheduled_force_step, tangent_step,
)
from empirical_lawhood.domains.matrix.six_matrix_response.preparation_differential import NativeStateDifferential
from empirical_lawhood.domains.matrix.six_matrix_response.shooting import (
    brownian_bridge_split, hermitian_basis,
)
from empirical_lawhood.domains.matrix.six_matrix_response.simulation import (
    BAOABGradientCache, hermitian_noise,
)


@dataclass(frozen=True, slots=True)
class MatrixSettings:
    """Native scientific settings; q=2 is the declared instrument domain."""

    dt: float = 0.002
    friction: float = 1.0
    temperature: float = 0.15
    mass: float = 0.5
    cross_coupling: float = 1.0
    alpha_x: float = 1.0
    alpha_y: float = 2.0
    position_jitter: float = 0.03
    momentum_jitter: float = 0.03
    prefix_steps: int = 32
    history_stride: int = 4
    radius_limit: float = 1e6
    q: int = 2

    def __post_init__(self) -> None:
        positive = (self.dt, self.friction, self.temperature, self.mass,
                    self.cross_coupling, self.radius_limit)
        nonnegative = (self.alpha_x, self.alpha_y, self.position_jitter, self.momentum_jitter)
        if (self.q != 2 or not np.isfinite((*positive, *nonnegative)).all()
                or min(positive) <= 0 or min(nonnegative) < 0
                or type(self.prefix_steps) is not int or self.prefix_steps < 2
                or type(self.history_stride) is not int or self.history_stride < 1):
            raise ValueError("Matrix joint-description instruments require finite q=2 native settings and a causal prefix")

    @property
    def member(self) -> SixMatrixResponseModelFamilyMember:
        return SixMatrixResponseModelFamilyMember(
            "joint-description.matrix.member", Decimal(str(self.mass)),
            Decimal(str(self.mass)), Decimal(str(self.cross_coupling)),
            BetaCouplingRule.PUBLISHED_DETERMINISTIC,
        )

    def view(self, refinement: int = 1) -> SixMatrixResponseNumericalView:
        if refinement not in (1, 2):
            raise ValueError("Only primary and Brownian-bridge half-step views are declared")
        return SixMatrixResponseNumericalView(
            "joint-description.matrix.primary" if refinement == 1 else "joint-description.matrix.half",
            MatrixIntegratorKind.BAOAB_UNDERDAMPED_LANGEVIN,
            Decimal(str(self.dt)) / refinement, "dimensionless-langevin-time",
            Decimal(str(self.friction)), Decimal(str(self.temperature)),
            MatrixPrecision.COMPLEX128, "numpy.pcg64dxsm", "1.0.0",
            "joint-description.matrix.independent-root", 1,
        )


CONSTITUTIONS = {"product": "11", "x-factor": "10", "y-factor": "01", "disordered": "00"}


def initial_state(settings: MatrixSettings, preparation: str, rng: np.random.Generator) -> SixMatrixState:
    """Declared exact background plus independently specified HS perturbations."""
    if preparation not in CONSTITUTIONS:
        raise ValueError(f"Unknown matrix preparation {preparation!r}")
    state = ideal_state(q=2, alpha_tilde_x=settings.alpha_x,
                        alpha_tilde_y=settings.alpha_y,
                        constitution=CONSTITUTIONS[preparation])
    return replace(state,
        positions=hermitian_part(state.positions + settings.position_jitter * hermitian_noise(rng=rng, q=2)),
        momenta=hermitian_part(settings.momentum_jitter * hermitian_noise(rng=rng, q=2)))


def noise_tape(rng: np.random.Generator, steps: int) -> np.ndarray:
    if type(steps) is not int or steps < 1:
        raise ValueError("A native noise tape needs a positive interval count")
    return np.asarray([hermitian_noise(rng=rng, q=2) for _ in range(steps)], dtype="<c16")


def _admit(state: SixMatrixState, settings: MatrixSettings) -> None:
    if not state.finite or float(np.linalg.norm(state.positions)) > settings.radius_limit:
        raise FloatingPointError("NATIVE_NONFINITE_OR_RADIUS_LIMIT")


def force_direction(state: SixMatrixState, direction_id: str) -> np.ndarray:
    """Past-state or fixed-coordinate force charts, selected before a future."""
    direction = np.zeros_like(state.positions)
    if direction_id in ("x-radial", "y-radial"):
        sector = 0 if direction_id.startswith("x") else 1
        direction[sector] = state.positions[sector]
    elif direction_id in ("x-trace", "y-trace"):
        direction[0 if direction_id.startswith("x") else 1, 0] = np.eye(4) / 2
    elif direction_id in ("x-coordinate", "y-coordinate"):
        direction[0 if direction_id.startswith("x") else 1, 0] = hermitian_basis(4)[4]
    elif direction_id == "joint-radial":
        direction[:] = state.positions
    else:
        raise ValueError(f"Unknown matrix force direction {direction_id!r}")
    norm = float(np.linalg.norm(direction))
    if norm <= 1e-14:
        raise FloatingPointError("DIRECTION_UNRESOLVED")
    result = np.asarray(direction / norm, dtype="<c16")
    result.setflags(write=False)
    return result


def native_path(
    initial: SixMatrixState, settings: MatrixSettings, innovations: np.ndarray,
    *, direction: np.ndarray | None = None, amplitude: float = 0.0,
    pulse_steps: int | None = None, coupling_delta: tuple[float, float] = (0.0, 0.0),
) -> tuple[SixMatrixState, ...]:
    """Advance true native intervals with a declared force and linear coupling ramp.

    Both kicks of each native interval use the same force amplitude. The native
    schedule, including a zero-length force pulse, is fixed before integration.
    """
    tape = np.asarray(innovations)
    if tape.ndim != 5 or tape.shape[1:] != (2, 3, 4, 4) or not len(tape):
        raise ValueError("Matrix innovations require complete (steps,2,3,4,4) arrays")
    if not np.isfinite((amplitude, *coupling_delta)).all():
        raise ValueError("Native interventions must be finite")
    if pulse_steps is None:
        pulse_steps = len(tape)
    if type(pulse_steps) is not int or not 0 <= pulse_steps <= len(tape):
        raise ValueError("Pulse duration lies outside its native future")
    if min(initial.alpha_tilde_x + coupling_delta[0], initial.alpha_tilde_y + coupling_delta[1]) < 0:
        raise ValueError("Coupling intervention leaves the nonnegative native domain")
    selected = np.zeros_like(initial.positions) if direction is None else direction
    state, states = initial, [initial]
    cache, member, view = BAOABGradientCache(), settings.member, settings.view()
    for index, noise in enumerate(tape):
        fraction = (index + 1) / len(tape)
        state = scheduled_force_step(state, direction=selected,
            amplitude=amplitude if index < pulse_steps else 0.0,
            member=member, numerical_view=view,
            next_alpha_tilde_x=initial.alpha_tilde_x + fraction * coupling_delta[0],
            next_alpha_tilde_y=initial.alpha_tilde_y + fraction * coupling_delta[1],
            standardized_noise=noise, gradient_cache=cache)
        _admit(state, settings)
        states.append(state)
    return tuple(states)


def acquire_prefix(settings: MatrixSettings, preparation: str, rng: np.random.Generator) -> tuple[SixMatrixState, ...]:
    initial = initial_state(settings, preparation, rng)
    return native_path(initial, settings, noise_tape(rng, settings.prefix_steps))


def paired_refinement(
    initial: SixMatrixState, settings: MatrixSettings, coarse_noise: np.ndarray,
    bridge_noise: np.ndarray, *, direction: np.ndarray | None = None, amplitude: float = 0.0,
    pulse_steps: int | None = None, coupling_delta: tuple[float, float] = (0.0, 0.0),
    fine_initial: SixMatrixState | None = None,
) -> tuple[tuple[SixMatrixState, ...], tuple[SixMatrixState, ...]]:
    """Advance a matched OU pair, carrying each resolution's state across stages."""
    if np.shape(coarse_noise) != np.shape(bridge_noise):
        raise ValueError("Coarse and bridge innovations need the same complete interval census")
    if pulse_steps is None:
        pulse_steps = len(coarse_noise)
    primary = native_path(initial, settings, coarse_noise, direction=direction,
                          amplitude=amplitude, pulse_steps=pulse_steps, coupling_delta=coupling_delta)
    fine_settings = replace(settings, dt=settings.dt / 2)
    half_decay = float(np.exp(-settings.friction * settings.dt / 2))
    fine_tape = np.asarray([noise for coarse, bridge in zip(coarse_noise, bridge_noise, strict=True)
        for noise in brownian_bridge_split(coarse_noise=coarse, bridge_noise=bridge, half_decay=half_decay)])
    fine = native_path(initial if fine_initial is None else fine_initial, fine_settings, fine_tape, direction=direction,
                       amplitude=amplitude, pulse_steps=2 * pulse_steps, coupling_delta=coupling_delta)
    return primary, tuple(fine[::2])


def causal_tangent_forecast(
    origin: SixMatrixState, settings: MatrixSettings, *, direction: np.ndarray,
    steps: int, pulse_steps: int | None = None, scalar_curvature: bool = False,
) -> np.ndarray:
    """Origin-frozen linear response; no realized future is an accepted argument.

    Full tangent propagates the two-sector Hessian at the origin. The scalar
    comparator projects it onto the declared forcing direction. Both integrate
    the same damped linearized unit-mass equations by the native B-A-O-A-B map.
    Future-path tangent diagnostics must not be passed as forecast features.
    """
    if type(steps) is not int or steps < 1:
        raise ValueError("Tangent horizon must contain a native interval")
    pulse_steps = steps if pulse_steps is None else pulse_steps
    if not 0 <= pulse_steps <= steps:
        raise ValueError("Tangent pulse lies outside its horizon")
    dt, decay = settings.dt, np.exp(-settings.friction * settings.dt)
    selected = parameters(origin, settings.member)
    curvature = float(np.vdot(direction, hessian_image(origin.positions, direction, selected)).real)
    position, momentum = np.zeros_like(direction), np.zeros_like(direction)
    for step in range(steps):
        force = direction if step < pulse_steps else np.zeros_like(direction)
        image = curvature * position if scalar_curvature else hessian_image(origin.positions, position, selected)
        momentum = momentum + dt * (force - image) / 2
        position = position + dt * momentum / 2
        momentum = decay * momentum
        position = position + dt * momentum / 2
        image = curvature * position if scalar_curvature else hessian_image(origin.positions, position, selected)
        momentum = momentum + dt * (force - image) / 2
    return hermitian_part(position)


def realized_tangent(
    path: tuple[SixMatrixState, ...], settings: MatrixSettings, *, direction: np.ndarray,
    pulse_steps: int,
) -> np.ndarray:
    """Evaluator-only derivative along an already realized zero-force native path."""
    differential = NativeStateDifferential(np.zeros_like(direction), np.zeros_like(direction))
    for index, (left, right) in enumerate(zip(path[:-1], path[1:], strict=True)):
        differential = tangent_step(left, right, differential, direction=direction,
            force_derivative=1.0 if index < pulse_steps else 0.0,
            member=settings.member, numerical_view=settings.view())
    return differential.positions
