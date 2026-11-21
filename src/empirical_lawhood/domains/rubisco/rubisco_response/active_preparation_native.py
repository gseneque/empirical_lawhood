# SPDX-License-Identifier: MPL-2.0
"""Finite preparation purchases using the original unrestrained minimizer.

The selected complete-return allocation ends a preparation prefix. It never
asserts convergence or changes the original full-relaxation stopping rule.
"""

from hashlib import sha256

from empirical_lawhood.domains.rubisco.rubisco_response.active_relaxation_native import InvalidRelaxationGeometry, checked_reference_evaluation
from empirical_lawhood.domains.rubisco.rubisco_response.active_relaxation_selection import ActiveRelaxationSettings
from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_checkpoint import BOHR_ANGSTROM, HARTREE_KJ_MOL
from empirical_lawhood.domains.rubisco.rubisco_response.geometry_domain_minimizer import minimize_geometry
from empirical_lawhood.domains.rubisco.rubisco_response.geometry_minimizer_state import GeometryMinimizerState
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_native import GRADIENT_UNIT


def minimize_reference_prefix(*, operator, initial_angstrom, settings, complete_return_allowance,
        observe, retain_evaluation, retain_checkpoint, resume_state=None, original_evaluations=(), geometry_guard=None):
    """Retain actual evaluations before accepted states; replay completed work only.

    The caller must authenticate the original evaluation ledger and reject any
    unresolved native contact before selecting continuation. Restarted native
    electronic initialization is distinct from exact optimizer continuation.
    """
    import numpy as np
    exact(settings, ActiveRelaxationSettings)
    xyz = np.asarray(initial_angstrom, dtype='<f8')
    if (xyz.ndim != 2 or xyz.shape[1] != 3 or not len(xyz) or not np.isfinite(xyz).all()
            or type(complete_return_allowance) is not int or not 0 <= complete_return_allowance <= 10
            or any(not callable(callback) for callback in (observe, retain_evaluation, retain_checkpoint))
            or type(original_evaluations) is not tuple
            or not complete_return_allowance and not original_evaluations):
        raise ValueError('preparation prefix requires an explicit finite purchase and original return custody')
    if resume_state is not None:
        exact(resume_state, GeometryMinimizerState)
        if resume_state.maximum_gradient != float(settings.maximum_gradient_kj_mol_nm):
            raise ValueError('preparation continuation changes its original convergence criterion')
    cached = {}
    evaluation_count = 0
    for number, coordinates, returned in original_evaluations:
        if type(number) is not int or number != evaluation_count + 1:
            raise ValueError('preparation continuation omits or reorders a completed native effect')
        coordinates = np.asarray(coordinates, dtype='<f8')
        gradient = np.asarray(returned['gradient_hartree_per_bohr'], dtype='<f8')
        if (coordinates.shape != xyz.shape or gradient.shape != xyz.shape
                or not np.isfinite(coordinates).all() or not np.isfinite(gradient).all()
                or not np.isfinite(float(returned['energy_hartree']))
                or returned['gradient_unit'] != GRADIENT_UNIT
                or float(returned['bohr_angstrom']) != BOHR_ANGSTROM
                or float(returned['hartree_kj_mol']) != HARTREE_KJ_MOL):
            raise ValueError('preparation continuation has incomplete original force operands')
        key = sha256(coordinates.tobytes()).hexdigest()
        if key in cached:
            raise ValueError('preparation continuation repeats an original native coordinate effect')
        cached[key] = (number, coordinates.copy(), returned)
        evaluation_count = number
    previous_count = evaluation_count
    if resume_state is not None and not (resume_state.evaluations <= previous_count and cached):
        raise ValueError('preparation continuation loses its original accepted force and evaluation ledger')
    accepted = []
    replayed = []
    objective_values = {}

    def objective(flat_nm):
        nonlocal evaluation_count
        trial = np.asarray(flat_nm).reshape(xyz.shape) * 10
        if resume_state is None and not objective_values and np.array_equal(flat_nm.reshape(xyz.shape), xyz / 10):
            trial = xyz
        if geometry_guard is not None:
            geometry_guard(trial)
        key = sha256(trial.tobytes()).hexdigest()
        if key in cached:
            number, original, returned = cached[key]
            if not np.array_equal(original, trial):
                raise ValueError('preparation replay changes a completed native coordinate effect')
            replayed.append(number)
            observe(dict(event='relaxation-replay', evaluation=number, coordinate_sha256=key,
                         native_contact=False))
        else:
            if evaluation_count - previous_count >= complete_return_allowance:
                raise ValueError('preparation optimizer exceeds its selected native-return purchase')
            evaluation_count += 1
            number = evaluation_count
            returned, _ = checked_reference_evaluation(operator=operator, coordinates=trial,
                shape=xyz.shape, observe=observe, label=number, phase='preparation-prefix',
                conversion=(BOHR_ANGSTROM, HARTREE_KJ_MOL))
            # Publication failure propagates. A complete known effect must not be retried.
            retain_evaluation(number, trial, returned)
            cached[key] = (number, trial.copy(), returned)
        objective_values[np.asarray(flat_nm, dtype='<f8').tobytes()] = cached[key]
        return (float(returned['energy_hartree']) * HARTREE_KJ_MOL,
                (np.asarray(returned['gradient_hartree_per_bohr']) * HARTREE_KJ_MOL * 10 / BOHR_ANGSTROM).reshape(-1))

    if resume_state is not None:
        matches = [(number, coordinates, returned) for number, coordinates, returned in cached.values()
                   if (np.array_equal((coordinates / 10).reshape(-1), resume_state.coordinates)
                       or np.array_equal(resume_state.coordinates.reshape(xyz.shape) * 10, coordinates))]
        if len(matches) != 1:
            raise ValueError('preparation continuation cannot identify its exact original accepted evaluation')
        number, coordinates, returned = matches[0]
        if (float(returned['energy_hartree']) * HARTREE_KJ_MOL != resume_state.energy
                or not np.array_equal((np.asarray(returned['gradient_hartree_per_bohr'])
                    * HARTREE_KJ_MOL * 10 / BOHR_ANGSTROM).reshape(-1), resume_state.gradient)):
            raise ValueError('preparation continuation substitutes its accepted native energy or force')
        objective_values[resume_state.coordinates.tobytes()] = matches[0]

    def checkpoint(state):
        number, coordinates, returned = objective_values[state.coordinates.tobytes()]
        retain_checkpoint(state, number, coordinates, returned)
        accepted.append((state, number, coordinates, returned))
        observe(dict(event='accepted-preparation-state', iteration=state.iterations,
            evaluation=number, native_objective_evaluations=state.evaluations,
            coordinate_sha256=sha256(coordinates.tobytes()).hexdigest(),
            maximum_gradient_kj_mol_nm=float(np.max(np.abs(state.gradient)))))
        return False

    start = (xyz / 10).reshape(-1) if resume_state is None else resume_state.coordinates
    result = minimize_geometry(objective, start, violation_type=InvalidRelaxationGeometry,
        maximum_gradient=float(settings.maximum_gradient_kj_mol_nm),
        maximum_evaluations=previous_count + complete_return_allowance,
        resume_state=resume_state, checkpoint_callback=checkpoint)
    state, number, coordinates, returned = accepted[-1]
    from empirical_lawhood.domains.rubisco.rubisco_response.molecular_quality import gradient_statistics
    return dict(state=state, coordinates=coordinates, native_result=returned,
        accepted_evaluation=number, accepted_states=tuple(accepted), summary=dict(
            scope='FINITE_PREPARATION_PREFIX_WITHOUT_ENDPOINT_POPULATION_OR_RATE_ADMISSION',
            optimizer_reported_success=bool(result.success), optimizer_reason=str(result.message),
            new_complete_reference_evaluations=evaluation_count - previous_count,
            complete_reference_evaluations=evaluation_count, previous_complete_evaluations=previous_count,
            complete_return_allowance=complete_return_allowance, replayed_evaluations=replayed,
            accepted_iterations=state.iterations, selected_accepted_evaluation=number,
            optimizer_evaluations=int(result.nfev), optimizer_settings=result.settings,
            maximum_selected_gradient_kj_mol_nm=float(np.max(np.abs(state.gradient))),
            maximum_gradient_selection_kj_mol_nm=str(settings.maximum_gradient_kj_mol_nm),
            selected_gradient_statistics=gradient_statistics(returned['gradient_hartree_per_bohr'], unit=GRADIENT_UNIT,
                bohr_angstrom=BOHR_ANGSTROM, hartree_kj_mol=HARTREE_KJ_MOL),
            added_restraints=False, molecular_time_seconds=None, equilibrium_population='UNEVALUABLE',
            rate_admission='UNEVALUABLE', native_electronic_continuation='RESTARTED_INITIALIZATION' if original_evaluations else 'ORIGINAL_INITIALIZATION'))
