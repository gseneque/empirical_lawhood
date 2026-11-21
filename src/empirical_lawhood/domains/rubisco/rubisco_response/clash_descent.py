# SPDX-License-Identifier: MPL-2.0
"""Initial descent on the unchanged potential before quasi-Newton refinement.

Very short contacts produce inverse-power forces spanning many orders of
magnitude. Per-atom positive scaling limits each trial displacement without
changing the objective. Armijo backtracking requires an actual energy decrease.
This is coordinate preparation, never molecular dynamics or a physical clock.
"""


def descend_clashes(objective, coordinates, *, maximum_iterations=2000,
                    maximum_atom_step_nm=0.01, maximum_gradient=10000.0,
                    gradient_scale=None):
    import numpy as np

    x=np.asarray(coordinates,dtype=float).copy()
    gradient_scale=maximum_gradient if gradient_scale is None else gradient_scale
    if (x.ndim!=1 or not x.size or x.size%3 or not np.isfinite(x).all()
            or type(maximum_iterations) is not int or maximum_iterations<1
            or not np.isfinite(maximum_atom_step_nm) or maximum_atom_step_nm<=0
            or not np.isfinite(maximum_gradient) or maximum_gradient<=0
            or not np.isfinite(gradient_scale) or gradient_scale<=0):
        raise ValueError("initial clash descent needs finite complete atom coordinates and positive stopping rules")
    calls=0

    def evaluate(value):
        nonlocal calls
        energy,gradient=objective(value)
        gradient=np.asarray(gradient,dtype=float)
        calls+=1
        if not np.isfinite(energy) or gradient.shape!=x.shape or not np.isfinite(gradient).all():
            raise ValueError("initial clash descent received an incomplete finite objective")
        return float(energy),gradient

    energy,gradient=evaluate(x)
    first_energy=energy
    accepted=0
    reason="maximum-initial-descent-iterations"
    while accepted<maximum_iterations:
        if np.max(np.abs(gradient))<=maximum_gradient:
            reason="initial-gradient-target-reached"
            break
        atoms=gradient.reshape((-1,3))
        norms=np.linalg.norm(atoms,axis=1)
        direction=(-maximum_atom_step_nm*atoms/np.maximum(norms[:,None],gradient_scale)).reshape(-1)
        alpha=1.0
        for _ in range(60):
            trial=x+alpha*direction
            if np.array_equal(trial,x):
                reason="initial-descent-coordinate-resolution"
                break
            change=float(np.dot(gradient,trial-x))
            if not change<0:
                reason="initial-descent-nondecreasing-direction"
                break
            candidate,new_gradient=evaluate(trial)
            if candidate<energy and candidate<=energy+1e-4*change:
                x,energy,gradient=trial,candidate,new_gradient
                accepted+=1
                break
            alpha*=0.5
        else:
            reason="initial-descent-backtracking-exhausted"
            break
        if reason in ("initial-descent-coordinate-resolution","initial-descent-nondecreasing-direction"):
            break
    converged=bool(np.max(np.abs(gradient))<=maximum_gradient)
    if converged:reason="initial-gradient-target-reached"
    return x,dict(success=converged,reason=reason,iterations=accepted,function_evaluations=calls,
        initial_energy_kj_mol=first_energy,energy_kj_mol=energy,
        maximum_gradient_kj_mol_nm=float(np.max(np.abs(gradient))),
        maximum_iterations=maximum_iterations,maximum_atom_step_nm=maximum_atom_step_nm,
        gradient_target_kj_mol_nm=maximum_gradient,gradient_scale_kj_mol_nm=gradient_scale,
        armijo_coefficient=1e-4,maximum_backtracks=60)
