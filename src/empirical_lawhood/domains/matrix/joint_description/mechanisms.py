"""Causal reduced mechanisms composed from the native constitutive action.

The radial model is an explicitly lossy one-mode predictor, assessed against
full six-matrix trajectories. It does not replace the experimental substrate.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np

from empirical_lawhood.domains.matrix.six_matrix_response.gradients import analytic_gradient_terms
from empirical_lawhood.domains.matrix.six_matrix_response.model import SixMatrixState, hermitian_part
from empirical_lawhood.domains.matrix.six_matrix_response.parameter_derivatives import parameters

from .native import MatrixSettings, native_path


@dataclass(frozen=True, slots=True)
class RadialForcePolynomial:
    """Exact projected quartic-potential gradient on a fixed radial chart."""

    cubic: float
    quadratic_coupling: float
    linear_coupling_squared: float
    interface_linear: float

    def __post_init__(self):
        if not np.isfinite((self.cubic, self.quadratic_coupling,
                            self.linear_coupling_squared, self.interface_linear)).all():
            raise FloatingPointError("RADIAL_FORCE_POLYNOMIAL_NONFINITE")

    def evaluate(self, radius: float, scaled_coupling: float) -> float:
        return radius * (self.cubic * radius**2 + self.quadratic_coupling * scaled_coupling * radius
                         + self.linear_coupling_squared * scaled_coupling**2 + self.interface_linear)


def radial_force_polynomial(origin: SixMatrixState, settings: MatrixSettings, *,
                            axis: np.ndarray, observed_sector: int,
                            retain_interface: bool) -> RadialForcePolynomial:
    """Extract exact polynomial coefficients with four native gradient images.

    For Z=rF the local gradient is c3*r^3+c2*alpha*r^2+
    (c1*alpha^2+c_interface)*r. The native potential is quartic, its
    cubic-action coefficient linear in alpha, and beta quadratic in alpha.
    Four fixed coefficient probes derive this polynomial without fitting any
    experiment outcome. Subsequent time steps are scalar arithmetic only.
    """
    if observed_sector not in (0, 1) or np.shape(axis) != (3, 4, 4):
        raise ValueError("Radial coefficient chart requires one complete native sector")
    if not np.isclose(np.linalg.norm(axis), 1, atol=1e-12, rtol=0):
        raise ValueError("Radial coefficient chart must use a normalized HS direction")
    positions = np.zeros_like(origin.positions)
    if retain_interface:
        positions[1 - observed_sector] = origin.positions[1 - observed_sector]

    def projected(radius, coupling):
        values = positions.copy()
        values[observed_sector] = radius * axis
        state = replace(origin, positions=hermitian_part(values),
            alpha_tilde_x=coupling if observed_sector == 0 else origin.alpha_tilde_x,
            alpha_tilde_y=coupling if observed_sector == 1 else origin.alpha_tilde_y)
        gradient = analytic_gradient_terms(state.positions, parameters(state, settings.member)).total
        return float(np.vdot(axis, gradient[observed_sector]).real)

    g10, g20, g11, g12 = projected(1.0, 0.0), projected(2.0, 0.0), projected(1.0, 1.0), projected(1.0, 2.0)
    cubic = (g20 - 2 * g10) / 6
    linear_coupling = (g12 - 2 * g11 + g10) / 2
    return RadialForcePolynomial(cubic, g11 - g10 - linear_coupling, linear_coupling, g10 - cubic)


def deterministic_forecast(origin: SixMatrixState, settings: MatrixSettings, *, steps: int,
                           direction: np.ndarray, amplitude: float = 0.0,
                           coupling_delta: tuple[float, float] = (0.0, 0.0)) -> tuple[SixMatrixState, ...]:
    """Mean-zero-innovation native forecast issued with no future noise operand.

    Nonlinear conditional expectations need not equal this forecast; that
    discrepancy is an experimental error rather than an asserted identity.
    """
    tape = np.zeros((steps, 2, 3, 4, 4), dtype="<c16")
    return native_path(origin, settings, tape, direction=direction, amplitude=amplitude,
                       coupling_delta=coupling_delta)


def radial_forecast(origin: SixMatrixState, settings: MatrixSettings, *, steps: int,
                    direction: np.ndarray, observed_sector: int,
                    amplitude: float = 0.0, coupling_delta: tuple[float, float] = (0.0, 0.0),
                    retain_interface: bool = False,
                    previous: SixMatrixState | None = None) -> tuple[SixMatrixState, ...]:
    """One local HS direction, optional frozen other sector and optional memory.

    Reconstruct a single local amplitude. Force projection is derived from the
    full constitutive action, so the interface's influence is an actual term.
    Other-sector momentum and evolution are omitted and their error is tested.
    A supplied previous state replaces instantaneous velocity with a causal
    finite-difference estimate; no target/future state is accepted.
    """
    axis = direction[observed_sector]
    length = float(np.linalg.norm(axis))
    if length <= 1e-14:
        raise FloatingPointError("RADIAL_CHART_UNRESOLVED")
    axis = axis / length
    scalar = float(np.vdot(axis, origin.positions[observed_sector]).real)
    velocity = float(np.vdot(axis, origin.momenta[observed_sector]).real)
    if previous is not None:
        elapsed = (origin.step_index - previous.step_index) * settings.dt
        if elapsed <= 0:
            raise ValueError("Radial memory must strictly precede the origin")
        velocity = float(np.vdot(axis, origin.positions[observed_sector] - previous.positions[observed_sector]).real) / elapsed
    other = np.zeros_like(origin.positions)
    if retain_interface:
        other[1 - observed_sector] = origin.positions[1 - observed_sector]
    force = amplitude * float(np.vdot(axis, direction[observed_sector]).real)
    dt, decay = settings.dt, float(np.exp(-settings.friction * settings.dt))
    polynomial = radial_force_polynomial(origin, settings, axis=axis, observed_sector=observed_sector,
                                         retain_interface=retain_interface)

    def reconstruct(r: float, v: float, index: int) -> SixMatrixState:
        positions, momenta = other.copy(), np.zeros_like(other)
        positions[observed_sector], momenta[observed_sector] = r * axis, v * axis
        fraction = index / steps
        return replace(origin, positions=hermitian_part(positions), momenta=hermitian_part(momenta),
            step_index=origin.step_index + index,
            alpha_tilde_x=origin.alpha_tilde_x + fraction * coupling_delta[0],
            alpha_tilde_y=origin.alpha_tilde_y + fraction * coupling_delta[1])

    state, states = reconstruct(scalar, velocity, 0), []
    states.append(state)
    for index in range(steps):
        coupling = state.alpha_tilde_x if observed_sector == 0 else state.alpha_tilde_y
        velocity += dt * (force - polynomial.evaluate(scalar, coupling)) / 2
        scalar += dt * velocity / 2
        velocity *= decay
        scalar += dt * velocity / 2
        state = reconstruct(scalar, velocity, index + 1)
        coupling = state.alpha_tilde_x if observed_sector == 0 else state.alpha_tilde_y
        velocity += dt * (force - polynomial.evaluate(scalar, coupling)) / 2
        state = reconstruct(scalar, velocity, index + 1)
        if not state.finite or float(np.linalg.norm(state.positions)) > settings.radius_limit:
            raise FloatingPointError("RADIAL_PREDICTOR_NONFINITE_OR_RADIUS_LIMIT")
        states.append(state)
    return tuple(states)
