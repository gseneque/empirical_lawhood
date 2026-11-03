# SPDX-License-Identifier: MPL-2.0
"""Coupling-only preparation using the original paired native equations.

No producer executes at import. The supplied-innovation function is useful for
independent mathematical checks; the RNG wrapper requires an ordinary guarded
native caller. Original four-purpose streams are never reseeded per arm.
"""

from hashlib import sha256

import numpy as np

from empirical_lawhood.adapters.methods.matrix_parameter_history import independent
from empirical_lawhood.adapters.methods.matrix_parameter_history.records import MatrixParameterHistoryControl, expected_members
from empirical_lawhood.adapters.simulators.six_matrix_response.model import SixMatrixState
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history import split_parameter_innovations
from empirical_lawhood.adapters.simulators.six_matrix_response.simulation import BAOABGradientCache, baoab_step_with_hermitian_noise, hermitian_noise
from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays, encode_matrix_arrays, matrix_array_members
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.references import ArtifactIdentity

from .preparation_records import (
    MatrixPreparationArrays, MatrixPreparationAssessment, MatrixPreparationInitialStateV2, MatrixPreparationSource, initial_state_types,
    preparation_identity,
)


def initial_state(initial, raw):
    if type(initial) not in initial_state_types():
        raise TypeError("prepared initial bytes need the exact selected original state record")
    initial.__post_init__()
    arrays = decode_matrix_arrays(raw, initial)
    if type(initial) is MatrixPreparationInitialStateV2:
        from .preparation_initialization_science import validate_initial_state
        validate_initial_state(initial, arrays)
    for value in arrays.values():
        if np.linalg.norm(value - value.conj().swapaxes(-1, -2)) > 1e-12:
            raise ValueError("prepared initial state must retain all finite Hermitian phase-space coordinates")
    return SixMatrixState(2, arrays["positions"], arrays["momenta"], 0, *map(float, initial.alpha_tilde))


def _noise(values, count):
    if (type(values) is not np.ndarray or values.shape != (count, 2, 3, 4, 4)
            or values.dtype.str != "<c16" or not np.isfinite(values).all()
            or np.linalg.norm(values - values.conj().swapaxes(-1, -2)) > 1e-12 * max(1, np.linalg.norm(values))):
        raise ValueError("prepared paired step requires every full finite Hermitian original innovation")


def _storage(source, initial):
    arrays = {name: np.empty(shape, dtype=dtype) for name, (dtype, shape) in expected_members(source).items()}
    for prefix, refinement in (("primary", 1), ("fine", 2)):
        count = refinement * source.total_ticks + 1
        arrays[prefix + "_ticks"][:] = np.arange(count, dtype="<i8")
        arrays[prefix + "_alpha_tilde"][:] = np.asarray(source.recipe.half_tick_couplings[::2 // refinement], dtype="<f8")
        arrays[prefix + "_positions"][0] = initial.positions
        arrays[prefix + "_momenta"][0] = initial.momenta
    return arrays


def propagate_preparation(source, initial_raw, *, coarse_innovations, bridge_innovations, on_step=None):
    """Complete paired native trajectory with explicitly supplied innovations.

    This owns no acquisition, seed selection, persistence or qualification.
    Every fine half step is retained, including the supplied midpoint schedule.
    """
    if type(source) is not MatrixPreparationSource:
        raise TypeError("preparation propagator needs its separate coupling-only source")
    source.__post_init__()
    n = source.total_ticks
    _noise(coarse_innovations, n)
    _noise(bridge_innovations, n)
    initial = initial_state(source.initial, initial_raw)
    return _propagate(source, initial, ((coarse_innovations[tick], bridge_innovations[tick]) for tick in range(n)), on_step=on_step)


def _propagate(source, initial, innovations, *, on_step=None):
    arrays = _storage(source, initial)
    primary = fine = initial
    primary_cache, fine_cache = BAOABGradientCache(), BAOABGradientCache()
    for step, (coarse, bridge) in enumerate(innovations, start=1):
        halves = split_parameter_innovations(source, coarse, bridge)
        arrays["primary_innovations"][step - 1] = coarse
        arrays["bridge_innovations"][step - 1] = bridge
        arrays["fine_innovations"][2 * step - 2:2 * step] = halves
        alpha = tuple(float(value) for value in source.recipe.half_tick_couplings[2 * step])
        primary = baoab_step_with_hermitian_noise(primary, member=source.member, numerical_view=source.primary_view,
            next_alpha_tilde_x=alpha[0], next_alpha_tilde_y=alpha[1], standardized_noise=coarse, gradient_cache=primary_cache)
        for half, noise in enumerate(halves, start=1):
            alpha = tuple(float(value) for value in source.recipe.half_tick_couplings[2 * step - 2 + half])
            fine = baoab_step_with_hermitian_noise(fine, member=source.member, numerical_view=source.fine_view,
                next_alpha_tilde_x=alpha[0], next_alpha_tilde_y=alpha[1], standardized_noise=noise, gradient_cache=fine_cache)
            if not fine.finite:
                raise FloatingPointError("prepared fine native trajectory became nonfinite")
            arrays["fine_positions"][fine.step_index] = fine.positions
            arrays["fine_momenta"][fine.step_index] = fine.momenta
        if not primary.finite:
            raise FloatingPointError("prepared primary native trajectory became nonfinite")
        arrays["primary_positions"][primary.step_index] = primary.positions
        arrays["primary_momenta"][primary.step_index] = primary.momenta
        if on_step is not None:
            # One complete primary step and both retained fine half steps.
            on_step(3 * step)
    if primary.step_index != source.total_ticks or fine.step_index != 2 * source.total_ticks:
        raise ValueError("preparation producer omits its complete declared paired duration")
    validate_preparation_arrays(source, arrays, initial=initial)
    return arrays


def acquire_preparation(source, initial_raw, *, on_step=None, prepared_initial=None):
    """Only the original native lifecycle caller may enter this RNG wrapper."""
    if type(source) is not MatrixPreparationSource:
        raise TypeError("preparation acquisition needs its exact selected native source")
    source.__post_init__()
    initial = initial_state(source.initial, initial_raw) if prepared_initial is None else prepared_initial
    selected = {row.purpose: row for row in source.root.streams}
    # Autonomous streams are untouched and retained as unconsumed custody.
    coarse = np.random.Generator(np.random.PCG64DXSM(selected["preparation-coarse-driver"].effective_seed))
    bridge = np.random.Generator(np.random.PCG64DXSM(selected["preparation-fine-bridge"].effective_seed))
    return _propagate(source, initial, ((hermitian_noise(rng=coarse, q=2), hermitian_noise(rng=bridge, q=2))
        for _ in range(source.total_ticks)), on_step=on_step)


def validate_preparation_arrays(source, arrays, *, initial):
    expected = expected_members(source)
    if set(arrays) != set(expected):
        raise ValueError("preparation loses complete phase-space, schedule, clock or innovation members")
    for name, (dtype, shape) in expected.items():
        value = arrays[name]
        if value.dtype.str != dtype or value.shape != shape or not np.isfinite(value).all():
            raise ValueError("preparation loses complete finite dtype/shape geometry")
        if dtype == "<c16" and np.linalg.norm(value - value.conj().swapaxes(-1, -2)) > 1e-10 * max(1, np.linalg.norm(value)):
            raise ValueError("preparation contains non-Hermitian native states or innovations")
    for prefix, refinement in (("primary", 1), ("fine", 2)):
        if (not np.array_equal(arrays[prefix + "_ticks"], np.arange(refinement * source.total_ticks + 1, dtype="<i8"))
                or not np.array_equal(arrays[prefix + "_alpha_tilde"], np.asarray(source.recipe.half_tick_couplings[::2 // refinement], dtype="<f8"))
                or not np.array_equal(arrays[prefix + "_positions"][0], initial.positions)
                or not np.array_equal(arrays[prefix + "_momenta"][0], initial.momenta)):
            raise ValueError("preparation substitutes original matched initial state, fixed schedule or physical clock")


def preparation_array_product(source, initial_raw, arrays, *, artifact_id, raw=None):
    return _preparation_array_product(source, initial_state(source.initial, initial_raw), arrays,
        artifact_id=artifact_id, raw=raw)


def _preparation_array_operand(source, raw, members, *, artifact_id):
    """Bind already validated native bytes without expanding their archive again."""
    artifact = ArtifactIdentity(artifact_id, "coupling-preparation-arrays", MATRIX_ARRAY_SCHEMA,
        sha256(raw).hexdigest(), "application/x-npz", len(raw))
    return MatrixPreparationArrays("operand." + source.source_id, source.identity, source.initial.identity,
        source.recipe.identity, artifact, members)


def _preparation_array_product(source, initial, arrays, *, artifact_id, raw=None):
    """Invocation-local closeout after the owning child authenticated its initial state."""
    validate_preparation_arrays(source, arrays, initial=initial)
    if raw is None:
        raw, members = encode_matrix_arrays(arrays)
    else:
        members = matrix_array_members(arrays)
    operand = _preparation_array_operand(source, raw, members, artifact_id=artifact_id)
    # Preserve original child bytes during recovery; a fresh ZIP is not evidence.
    decoded = decode_matrix_arrays(raw, operand)
    if any(not np.array_equal(decoded[name], arrays[name]) for name in arrays):
        raise ValueError("retained preparation bytes change their complete original numerical values")
    return raw, operand


def consume_preparation_arrays(source, initial_raw, operand, raw):
    operand.validate_source(source)
    arrays = decode_matrix_arrays(raw, operand)
    validate_preparation_arrays(source, arrays, initial=initial_state(source.initial, initial_raw))
    return arrays


def assess_preparation_arrays(source, initial_raw, operand, arrays, *, assessment_id):
    """Original independent derivative/OU checks over the complete new subject."""
    operand.validate_source(source)
    validate_preparation_arrays(source, arrays, initial=initial_state(source.initial, initial_raw))
    design = source.numerical_design
    controls = tuple(MatrixParameterHistoryControl(**row) for row in independent.assess_arrays(source, arrays,
        trajectory_tolerance=design.trajectory_tolerance, bridge_tolerance=design.bridge_tolerance))
    result = MatrixPreparationAssessment(assessment_id, source.identity, preparation_identity(operand),
        preparation_identity(design), controls, all(row.disposition == "SATISFIED" for row in controls))
    validate_preparation_assessment(source, operand, result)
    return result


def validate_preparation_assessment(source, operand, assessment):
    operand.validate_source(source)
    assessment.__post_init__()
    n, design = source.total_ticks, source.numerical_design
    if (assessment.source != source.identity or assessment.arrays != preparation_identity(operand)
            or assessment.numerical_design != preparation_identity(design)
            or tuple((row.denominator_steps, row.denominator_real_coordinates, row.tolerance) for row in assessment.controls) !=
                ((n, 192, design.trajectory_tolerance), (2 * n, 192, design.trajectory_tolerance),
                 (n, 192, design.bridge_tolerance), (n, 96, design.trajectory_tolerance))):
        raise ValueError("preparation assessment changes original selected source or full independent denominator")
