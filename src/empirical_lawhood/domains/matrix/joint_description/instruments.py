"""Causal matrix descriptions and evaluator-only receiver calculations.

Description blocks expose genuinely different operands.  The local block sees
one sector; the interface block sees cross-sector couplings; memory sees only
past samples.  Full joint coordinates retain both sectors and momenta.  Future
geometry/transfer values never enter description construction.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.linalg import expm

from empirical_lawhood.domains.matrix.matrix_history_analysis.algebra import measure, operator, sector
from empirical_lawhood.domains.matrix.matrix_history_analysis.passive import propagators
from empirical_lawhood.domains.matrix.six_matrix_response.gradients import commutator
from empirical_lawhood.domains.matrix.six_matrix_response.model import SixMatrixState
from empirical_lawhood.domains.matrix.six_matrix_response.parameter_derivatives import hessian_image, parameters
from empirical_lawhood.domains.matrix.six_matrix_response.shooting import hermitian_basis

from .native import MatrixSettings


@dataclass(frozen=True, slots=True)
class MatrixDescription:
    """Origin-only finite-dimensional candidate descriptions and accounting."""

    local: np.ndarray
    interface: np.ndarray
    memory: np.ndarray
    joint: np.ndarray
    local_labels: tuple[str, ...]
    interface_labels: tuple[str, ...]
    memory_labels: tuple[str, ...]
    joint_labels: tuple[str, ...]


def phase_coordinates(state: SixMatrixState) -> np.ndarray:
    phase = np.stack((state.positions, state.momenta))
    return np.asarray(np.einsum("iab,psjab->psji", hermitian_basis(4).conj(), phase).real, dtype="<f8")


def local_coordinates(state: SixMatrixState, observed_sector: int) -> np.ndarray:
    """All local phase coordinates; no hidden-sector measurement is consulted."""
    phase = np.stack((state.positions[observed_sector], state.momenta[observed_sector]))
    return np.asarray(np.einsum("iab,pjab->pji", hermitian_basis(4).conj(), phase).real, dtype="<f8").reshape(-1)


def cross_interface(state: SixMatrixState, settings: MatrixSettings, direction: np.ndarray) -> np.ndarray:
    """Explicit coupling measurements paid for when the interface is retained."""
    x, y = state.positions
    cross = commutator(x[:, None], y[None])
    image = hessian_image(state.positions, direction, parameters(state, settings.member))
    gradients = hessian_image(state.positions, state.momenta, parameters(state, settings.member))
    return np.asarray((
        np.linalg.norm(cross)**2, np.vdot(direction, image).real,
        np.linalg.norm(image[0]), np.linalg.norm(image[1]),
        np.linalg.norm(gradients[0]), np.linalg.norm(gradients[1]),
        state.alpha_tilde_x, state.alpha_tilde_y,
    ), dtype="<f8")


def describe_prefix(
    history: tuple[SixMatrixState, ...], settings: MatrixSettings, *, direction: np.ndarray,
    observed_sector: int = 0, memory_depth: int = 2,
) -> MatrixDescription:
    if observed_sector not in (0, 1) or type(memory_depth) is not int or memory_depth < 0:
        raise ValueError("Description requires one sector and a nonnegative finite history depth")
    if not history or tuple(state.step_index for state in history) != tuple(sorted(set(state.step_index for state in history))):
        raise ValueError("Description requires a strictly ordered causal history ending at its origin")
    origin = history[-1]
    local = local_coordinates(origin, observed_sector)
    interface = cross_interface(origin, settings, direction)
    needed = memory_depth * settings.history_stride
    if needed >= len(history) and memory_depth:
        raise ValueError("HISTORY_UNAVAILABLE")
    remembered = [local_coordinates(history[-1 - depth * settings.history_stride], observed_sector)
                  for depth in range(1, memory_depth + 1)]
    memory = np.concatenate(remembered) if remembered else np.empty(0, dtype="<f8")
    joint = phase_coordinates(origin).reshape(-1)
    local_labels = tuple(f"sector{observed_sector}.phase.{i}" for i in range(len(local)))
    return MatrixDescription(local, interface, memory, joint, local_labels,
        ("xy-commutator-squared", "forced-curvature", "x-coupled-hessian-norm", "y-coupled-hessian-norm",
         "x-momentum-curvature", "y-momentum-curvature", "alpha-x", "alpha-y"),
        tuple(f"lag{lag}.sector{observed_sector}.phase.{i}" for lag in range(1, memory_depth + 1) for i in range(len(local))),
        tuple(f"joint.phase.{i}" for i in range(len(joint))))


def geometry_observation(state: SixMatrixState) -> np.ndarray:
    """Continuous geometry receiver with distinct X, Y and joint eigengaps."""
    result = measure(state.positions)
    return np.asarray((result["x"]["metrics"]["gap"], result["y"]["metrics"]["gap"],
        result["joint_spectrum"][3] - result["joint_spectrum"][2],
        result["cross_metrics"]["xy_angle_degrees"] / 90.0), dtype="<f8")


def geometry_admission(state: SixMatrixState, *, sector_index: int, maximum_band_ratio: float,
                       maximum_associative_leakage: float) -> tuple[bool, str]:
    result = sector(state.positions[sector_index])
    if not result["identifiable"]:
        return False, "SLOW_SECTOR_NOT_IDENTIFIABLE"
    metrics = result["metrics"]
    accepted = (metrics["band_ratio"] <= maximum_band_ratio
                and metrics["associative_leakage"] <= maximum_associative_leakage)
    return accepted, "ADMITTED" if accepted else "STRUCTURE_CRITERION_NOT_MET"


def algebra_observation(state: SixMatrixState, observed_sector: int) -> np.ndarray:
    result = sector(state.positions[observed_sector])
    if not result["identifiable"]:
        raise FloatingPointError("SLOW_SECTOR_NOT_IDENTIFIABLE")
    metrics = result["metrics"]
    return np.asarray((metrics["associative_leakage"], metrics["lie_leakage"],
        metrics["band_ratio"], metrics["commutant_mixing"]), dtype="<f8")


def first_passage(
    path: tuple[SixMatrixState, ...], *, sector_index: int, maximum_band_ratio: float,
    maximum_associative_leakage: float, persistence_steps: int,
) -> tuple[float, float]:
    """Persistent target-entry and occupation fractions; nonentry is a zero.

    This finite-horizon receiver has no competing absorbing basin. It does not
    estimate eventual return or a target-versus-other-basin committor.
    """
    if type(persistence_steps) is not int or not 1 <= persistence_steps < len(path):
        raise ValueError("Persistence receiver exceeds the declared future")
    admitted = [geometry_admission(s, sector_index=sector_index,
        maximum_band_ratio=maximum_band_ratio,
        maximum_associative_leakage=maximum_associative_leakage)[0] for s in path[1:]]
    run, hit = 0, False
    for enters in admitted:
        run = run + 1 if enters else 0
        hit |= run >= persistence_steps
    return float(hit), float(np.mean(admitted))


def directional_passive_transfer(path: tuple[SixMatrixState, ...], settings: MatrixSettings,
                                 *, observed_sector: int, kappa: float) -> np.ndarray:
    """Evaluator full-operator transfer, retaining all15 independent directions."""
    result, _, _ = propagators(np.asarray([s.positions[observed_sector] for s in path]), settings.dt, [kappa])
    return result[-1, 0]


def causal_passive_transfer(origin: SixMatrixState, *, observed_sector: int,
                            kappa: float, horizon: float, radius_only: bool) -> np.ndarray:
    """Causal full frozen generator versus its scalar-radius compression."""
    if radius_only:
        triplet = origin.positions[observed_sector]
        centered = triplet - np.trace(triplet, axis1=-2, axis2=-1)[:, None, None] * np.eye(4) / 4
        # The exact adjoint trace is2*n*sum_a||Y_a-tr(Y_a)I/n||_HS^2.
        mean_rate = 8 * float(np.linalg.norm(centered)**2) / 15
        return np.eye(15) * np.exp(-kappa * horizon * mean_rate)
    return expm(-kappa * horizon * operator(origin.positions[observed_sector]))


def radial_increment(origin: SixMatrixState, final: SixMatrixState, observed_sector: int) -> float:
    return float((np.linalg.norm(final.positions[observed_sector])**2
                  - np.linalg.norm(origin.positions[observed_sector])**2) / 4)


def response_receiver(origin: SixMatrixState, final: SixMatrixState, direction: np.ndarray,
                      receiver_id: str) -> float:
    if receiver_id == "signed-displacement":
        return float(np.vdot(direction, final.positions - origin.positions).real)
    if receiver_id == "absolute-position":
        return float(np.vdot(direction, final.positions).real)
    if receiver_id == "x-radius":
        return float(np.linalg.norm(final.positions[0])**2 / 4)
    if receiver_id == "y-radius":
        return float(np.linalg.norm(final.positions[1])**2 / 4)
    if receiver_id == "work":
        return float(np.vdot(direction, final.positions - origin.positions).real)
    raise ValueError(f"Unsupported finite-response receiver {receiver_id!r}")
