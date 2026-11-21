# SPDX-License-Identifier: MPL-2.0
"""Fixed-cell Hamiltonian Monte Carlo with natural masses and electronic energy/gradient returns."""

from dataclasses import dataclass
from decimal import Decimal
import math
from numbers import Real

import numpy as np


def velocity_verlet_drift(positions_angstrom, velocity_nm_per_ps, acceleration_nm_per_ps2, step_ps):
    """First half kick and full coordinate drift, before the next force evaluation."""
    with np.errstate(over="raise", invalid="raise"):
        half_velocity = velocity_nm_per_ps + .5 * step_ps * acceleration_nm_per_ps2
        trial = positions_angstrom + (10 * step_ps) * half_velocity
    if not np.isfinite(trial).all() or not np.isfinite(half_velocity).all():
        raise ValueError("velocity-Verlet produced a nonfinite trial before force entry")
    return trial, half_velocity


def velocity_verlet_finish(half_velocity_nm_per_ps, acceleration_nm_per_ps2, step_ps):
    """Synchronize velocity at the position of the returned force."""
    with np.errstate(over="raise", invalid="raise"):
        velocity = half_velocity_nm_per_ps + .5 * step_ps * acceleration_nm_per_ps2
    if not np.isfinite(velocity).all():
        raise ValueError("velocity-Verlet produced a nonfinite full-step velocity")
    return velocity


@dataclass(frozen=True, slots=True)
class _ForcePoint:
    coordinates: np.ndarray
    energy: float
    gradient: np.ndarray


def _relax(initial, evaluate, bohr_angstrom, maximum):
    """Keep the lowest actually evaluated point under the selected force-call limit."""
    from scipy.optimize import minimize

    class CallLimit(Exception):
        pass

    best = None
    evaluations = 0

    def objective(flat):
        nonlocal best, evaluations
        if evaluations == maximum:
            raise CallLimit
        point = evaluate(flat.reshape(initial.shape))
        evaluations += 1
        if best is None or point.energy < best.energy:
            best = point
        return point.energy, point.gradient.ravel() / bohr_angstrom

    try:
        minimize(objective, initial.ravel(), method="L-BFGS-B", jac=True,
                 options={"maxiter": maximum, "maxcor": 3, "ftol": 0.0})
    except CallLimit:
        pass
    if best is None:
        raise ValueError("host relaxation yielded no finite force evaluation")
    return best


def sample_fixed_cell_hamiltonian(
    *, initial_angstrom, masses_dalton, energy_gradient, bohr_angstrom, hartree_kj_mol,
    thermal_energy_kj_mol, step_ps, steps_per_proposal, burn_in, draws,
    relaxation_evaluations, rng, capture,
):
    """Stream every move, including the repeated current position of a rejected proposal.

    The supplied force returns electronic energy in Hartree and the complete Cartesian
    energy derivative in Hartree/Bohr. Positions are unwrapped at fixed cell. Draws of
    Maxwell momenta and the Metropolis variate consume the caller's generator in order.
    The optional bounded relaxation precedes all proposals. Force or capture failures
    propagate with the already delivered prefix intact.
    """
    if (any(type(n) is not int or n < 0 for n in (burn_in, draws, relaxation_evaluations))
            or type(steps_per_proposal) is not int or steps_per_proposal < 1):
        raise ValueError("select nonnegative counts and at least one integration step per proposal")
    scales = (step_ps, thermal_energy_kj_mol, bohr_angstrom, hartree_kj_mol)
    if any(isinstance(value, (bool, np.bool_)) or not isinstance(value, (Real, Decimal)) for value in scales):
        raise ValueError("the physical units, temperature energy and step must be real scalars")
    step_ps, thermal_energy_kj_mol, bohr_angstrom, hartree_kj_mol = scales = tuple(map(float, scales))
    if any(not math.isfinite(value) or value <= 0 for value in scales):
        raise ValueError("select finite positive physical units, temperature energy and step")
    if not callable(energy_gradient) or not callable(capture) or not isinstance(rng, np.random.Generator):
        raise TypeError("select a force callback, capture callback and explicit NumPy generator")
    if np.iscomplexobj(initial_angstrom) or np.iscomplexobj(masses_dalton):
        raise ValueError("the host coordinates and masses must be real")
    initial = np.array(initial_angstrom, dtype="<f8", copy=True)
    masses = np.array(masses_dalton, dtype="<f8", copy=True)
    if (initial.ndim != 2 or initial.shape[1] != 3 or not len(initial)
            or masses.shape != (len(initial),) or not np.isfinite(initial).all()
            or not np.isfinite(masses).all() or np.any(masses <= 0)):
        raise ValueError("select complete Cartesian positions and one finite positive mass per atom")
    mass_column = masses[:, None]
    with np.errstate(over="raise", divide="raise", invalid="raise"):
        sigma = np.sqrt(thermal_energy_kj_mol / masses)[:, None]
        acceleration_scale = 10 * hartree_kj_mol / bohr_angstrom
    if not math.isfinite(acceleration_scale) or not np.isfinite(sigma).all() or np.any(sigma <= 0):
        raise ValueError("the selected thermal velocity or force conversion is unrepresentable")
    evaluations = 0

    def evaluate(coordinates):
        nonlocal evaluations
        delivered = coordinates.copy()
        energy, gradient = energy_gradient(delivered)
        if not np.array_equal(delivered, coordinates):
            raise ValueError("the force changed its delivered host coordinates")
        value = np.asarray(energy)
        energy = value.item() if value.ndim == 0 else None
        if (isinstance(energy, (bool, np.bool_)) or not isinstance(energy, (Real, Decimal))
                or np.iscomplexobj(gradient)):
            raise ValueError("the host force requires a real energy and gradient")
        energy = float(energy)
        gradient = np.array(gradient, dtype="<f8", copy=True)
        if not math.isfinite(energy) or gradient.shape != initial.shape or not np.isfinite(gradient).all():
            raise ValueError("the host force returned an incomplete or nonfinite energy/gradient")
        evaluations += 1
        return _ForcePoint(coordinates.copy(), energy, gradient)

    def acceleration(point):
        with np.errstate(over="raise", divide="raise", invalid="raise"):
            return -point.gradient * acceleration_scale / mass_column

    def hamiltonian(point, velocity):
        with np.errstate(over="raise", invalid="raise"):
            kinetic = .5 * np.sum(mass_column * velocity * velocity)
            return point.energy * hartree_kj_mol + float(kinetic)

    if relaxation_evaluations:
        current = _relax(initial, evaluate, bohr_angstrom, relaxation_evaluations)
        capture({"stage": "initial-relaxation", "evaluations": evaluations, "energy_hartree": current.energy},
                current.coordinates.copy())
    else:
        current = evaluate(initial)
    initial_evaluations = evaluations
    accepted_moves = 0
    for index in range(burn_in + draws):
        velocity = rng.normal(size=initial.shape) * sigma
        candidate = current
        old_total = hamiltonian(current, velocity)
        force = acceleration(current)
        for _ in range(steps_per_proposal):
            coordinates, half_velocity = velocity_verlet_drift(candidate.coordinates, velocity, force, step_ps)
            candidate = evaluate(coordinates)
            force = acceleration(candidate)
            velocity = velocity_verlet_finish(half_velocity, force, step_ps)
        change = hamiltonian(candidate, velocity) - old_total
        if not math.isfinite(change):
            raise ValueError("nonfinite host Hamiltonian change")
        draw = float(rng.uniform())
        accepted = math.log1p(-draw) < -change / thermal_energy_kj_mol
        if accepted:
            current = candidate
            accepted_moves += 1
        capture({"stage": "proposal", "index": index, "burn_in": index < burn_in, "accepted": accepted,
                 "uniform_draw": draw, "delta_h_kj_mol": change, "proposed_energy_hartree": candidate.energy,
                 "energy_hartree": current.energy, "completed_force_evaluations": evaluations},
                current.coordinates.copy())
    return {"relaxation_evaluation_limit": relaxation_evaluations,
            "initialization_force_evaluations": initial_evaluations, "completed_force_evaluations": evaluations,
            "burn_in": burn_in, "retained_draws": draws, "accepted_moves": accepted_moves,
            "rejected_moves": burn_in + draws - accepted_moves}
