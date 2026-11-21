# SPDX-License-Identifier: MPL-2.0
"""Limited-memory construction minimization with explicit admissible trials.

Armijo backtracking rejects an invalid geometric trial before native contact.
The temporary barrier is owned by the supplied objective; this algorithm never
changes the molecular energy or substitutes a force-convergence criterion.
"""

from collections import deque
from types import SimpleNamespace
import numpy as np
from empirical_lawhood.methods.binary64_reduction import REDUCTION_CONTRACT, dot, norm


def minimize_geometry(objective, coordinates, *, violation_type, maximum_gradient=1.0,
        maximum_iterations=None, maximum_evaluations=None, callback=None, proposal_filter=None,
        resume_state=None, checkpoint_callback=None):
    from empirical_lawhood.domains.rubisco.rubisco_response.geometry_minimizer_state import GeometryMinimizerState

    x = np.asarray(coordinates, dtype=float).copy()
    if (x.ndim != 1 or not x.size or x.size % 3 or not np.isfinite(x).all()
            or not np.isfinite(maximum_gradient) or maximum_gradient <= 0
            or maximum_iterations is not None and (type(maximum_iterations) is not int or maximum_iterations < 1)
            or maximum_evaluations is not None and (type(maximum_evaluations) is not int or maximum_evaluations < 1)
            or proposal_filter is not None and not callable(proposal_filter)
            or checkpoint_callback is not None and not callable(checkpoint_callback)
            or not isinstance(violation_type, type) or not issubclass(violation_type, ValueError)):
        raise ValueError("geometry minimization needs finite Cartesian variables and explicit positive limits")
    history = deque(maxlen=20)
    evaluations, invalid_trials, iterations, curvature_skips = 0, 0, 0, 0

    def evaluate(values):
        nonlocal evaluations
        if maximum_evaluations is not None and evaluations >= maximum_evaluations:
            raise RuntimeError("geometry-minimizer-evaluation-limit")
        energy, gradient = objective(values)
        evaluations += 1
        gradient = np.asarray(gradient, dtype=float)
        if not np.isfinite(energy) or gradient.shape != x.shape or not np.isfinite(gradient).all():
            raise ValueError("geometry minimizer received nonfinite or incomplete objective output")
        return float(energy), gradient.copy()

    filter_contract = 'LOCAL_CONSTRUCTION_DOMAIN_V1' if proposal_filter is not None else None
    if resume_state is None:
        energy, gradient = evaluate(x)
        initial_energy = energy
        phase = "initial-scaled-descent"
        descent_iterations = 0
    else:
        if (type(resume_state) is not GeometryMinimizerState
                or not np.array_equal(x, resume_state.coordinates)
                or float(maximum_gradient) != resume_state.maximum_gradient
                or filter_contract != resume_state.proposal_filter_contract
                or maximum_iterations is not None and maximum_iterations < resume_state.iterations
                or maximum_evaluations is not None and maximum_evaluations < resume_state.evaluations):
            raise ValueError('optimizer continuation changes its accepted variables, settings or prior work')
        x, gradient = resume_state.coordinates.copy(), resume_state.gradient.copy()
        energy, initial_energy = resume_state.energy, resume_state.initial_energy
        history.extend((s.copy(), y.copy(), rho) for s, y, rho in resume_state.history)
        phase = resume_state.phase
        iterations, evaluations = resume_state.iterations, resume_state.evaluations
        invalid_trials, curvature_skips = resume_state.invalid_trials, resume_state.curvature_skips
        descent_iterations = resume_state.descent_iterations

    def checkpoint():
        state = GeometryMinimizerState(x, float(energy), gradient, float(initial_energy),
            tuple(history), phase, iterations, evaluations, invalid_trials, curvature_skips,
            descent_iterations, float(maximum_gradient), filter_contract)
        stopped = False if checkpoint_callback is None else checkpoint_callback(state)
        if type(stopped) is not bool:
            raise ValueError('accepted-state callback must explicitly select continuation or stopping')
        return state, stopped

    accepted_state, stop_requested = checkpoint() if checkpoint_callback is not None or resume_state is not None else (None, False)
    success = False
    reason = "accepted-geometry-checkpoint-stop" if stop_requested else "maximum-geometry-iterations"
    while not stop_requested and (maximum_iterations is None or iterations < maximum_iterations):
        if np.max(np.abs(gradient)) <= maximum_gradient:
            success, reason = True, "geometry-gradient-target-reached"
            break
        if maximum_evaluations is not None and evaluations >= maximum_evaluations:
            reason = "maximum-geometry-evaluations"
            break
        if phase == "initial-scaled-descent" and np.max(np.abs(gradient)) <= 1e6:
            phase = "domain-lbfgs"
        if phase == "initial-scaled-descent":
            atoms = gradient.reshape((-1, 3))
            direction = (-0.01*atoms/np.maximum(np.linalg.norm(atoms, axis=1)[:, None], 1e4)).reshape(-1)
        else:
            q = gradient.copy()
            alphas = []
            for s, y, rho in reversed(history):
                alpha = rho*dot(s, q)
                alphas.append(alpha)
                q -= alpha*y
            if history:
                s, y, _ = history[-1]
                scale = dot(s, y)/dot(y, y)
            else:
                scale = 1.0
            r = scale*q
            for (s, y, rho), alpha in zip(history, reversed(alphas), strict=True):
                r += s*(alpha-rho*dot(y, r))
            direction = -r
            if not np.isfinite(direction).all() or dot(direction, gradient) >= 0:
                history.clear()
                direction = -gradient.copy()
            maximum_step = float(np.max(np.linalg.norm(direction.reshape((-1, 3)), axis=1)))
            if maximum_step > 0.02:
                direction *= 0.02/maximum_step
        proposal_diagnostics={}
        if proposal_filter is not None:
            direction,proposal_diagnostics=proposal_filter(x,direction)
            direction=np.asarray(direction,dtype=float)
            if direction.shape!=x.shape or not np.isfinite(direction).all():
                raise ValueError('local geometry filter changed the complete finite variable census')
            if dot(gradient,direction)>=0:
                history.clear()
                atoms=gradient.reshape((-1,3))
                direction=(-.01*atoms/np.maximum(np.linalg.norm(atoms,axis=1)[:,None],1e4)).reshape(-1)
                direction,proposal_diagnostics=proposal_filter(x,direction)
        directional = dot(gradient, direction)
        if not directional < 0:
            reason = "geometry-nondecreasing-direction"
            break
        alpha, accepted = 1.0, False
        for _ in range(60):
            trial = x+alpha*direction
            if np.array_equal(trial, x):
                reason = "geometry-coordinate-resolution"
                break
            if maximum_evaluations is not None and evaluations >= maximum_evaluations:
                reason = "maximum-geometry-evaluations"
                break
            try:
                new_energy, new_gradient = evaluate(trial)
            except violation_type:
                invalid_trials += 1
                alpha *= 0.5
                continue
            if new_energy < energy and new_energy <= energy+1e-4*alpha*directional:
                accepted = True
                break
            alpha *= 0.5
        if not accepted:
            if reason not in ("geometry-coordinate-resolution", "maximum-geometry-evaluations"):
                reason = "geometry-backtracking-exhausted"
            break
        s, y = trial-x, new_gradient-gradient
        sy = dot(s, y)
        if phase == "domain-lbfgs":
            if sy > 1e-10*norm(s)*norm(y):
                history.append((s.copy(), y.copy(), 1/sy))
            else:
                curvature_skips += 1
        else:
            descent_iterations += 1
        x, energy, gradient = trial, new_energy, new_gradient
        iterations += 1
        if checkpoint_callback is not None or resume_state is not None:
            accepted_state, stop_requested = checkpoint()
            if stop_requested:
                reason = "accepted-geometry-checkpoint-stop"
        if callback is not None:
            callback(dict(iteration=iterations, phase=phase, energy_kj_mol=energy,
                maximum_gradient_kj_mol_nm=float(np.max(np.abs(gradient))),
                native_objective_evaluations=evaluations, rejected_domain_trials=invalid_trials,
                accepted_step_scale=alpha, curvature_history=len(history),**proposal_diagnostics))
    if np.max(np.abs(gradient)) <= maximum_gradient:
        success, reason = True, "geometry-gradient-target-reached"
    return SimpleNamespace(x=x, fun=energy, jac=gradient, success=success, status=0 if success else 1,
        message=reason, nit=iterations, nfev=evaluations, initial_energy_kj_mol=initial_energy,
        rejected_domain_trials=invalid_trials, curvature_skips=curvature_skips,
        initial_descent_iterations=descent_iterations,
        accepted_state=accepted_state,
        settings=dict(memory=20, armijo_coefficient=1e-4, maximum_backtracks=60,
            scalar_reduction=REDUCTION_CONTRACT,
            initial_maximum_atom_step_nm=0.01, maximum_atom_step_nm=0.02,
            initial_handoff_gradient_kj_mol_nm=1e6, initial_gradient_scale_kj_mol_nm=1e4,
            maximum_gradient_kj_mol_nm=maximum_gradient, maximum_iterations=maximum_iterations,
            maximum_evaluations=maximum_evaluations,
            proposal_filter='LOCAL_CONSTRUCTION_DOMAIN_V1' if proposal_filter is not None else None))
