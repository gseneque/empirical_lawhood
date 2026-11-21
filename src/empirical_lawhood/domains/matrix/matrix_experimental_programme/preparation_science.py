"""Coupling-only preparation using the original paired native equations.

No producer executes at import. The supplied-innovation function is useful for
independent mathematical checks; the RNG wrapper requires an ordinary guarded
native caller. Original four-purpose streams are never reseeded per arm.
"""
from hashlib import sha256
import numpy as np
from empirical_lawhood.domains.matrix.matrix_parameter_history import independent
from empirical_lawhood.domains.matrix.matrix_parameter_history.records import MatrixParameterHistoryControl, expected_members
from empirical_lawhood.domains.matrix.six_matrix_response.model import SixMatrixState
from empirical_lawhood.domains.matrix.six_matrix_response.simulation import BAOABGradientCache, hermitian_noise
from empirical_lawhood.domains.matrix.input_contracts import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.science.identity.references import ArtifactIdentity
from empirical_lawhood.domains.matrix.matrix_experimental_programme.preparation_records import MatrixPreparationArrays, MatrixPreparationAssessment, MatrixPreparationInitialStateV2, MatrixPreparationSource, initial_state_types, preparation_identity
from empirical_lawhood.domains.matrix.matrix_experimental_programme.preparation_intervals import advance_preparation_pair

def initial_state_from_arrays(initial, arrays):
    if type(initial) not in initial_state_types():
        raise TypeError('prepared initial bytes need the exact selected original state record')
    initial.__post_init__()
    if type(initial) is MatrixPreparationInitialStateV2:
        from empirical_lawhood.domains.matrix.matrix_experimental_programme.preparation_initialization_science import validate_initial_state
        validate_initial_state(initial, arrays)
    for value in arrays.values():
        if np.linalg.norm(value - value.conj().swapaxes(-1, -2)) > 1e-12:
            raise ValueError('prepared initial state must retain all finite Hermitian phase-space coordinates')
    return SixMatrixState(2, arrays['positions'], arrays['momenta'], 0, *map(float, initial.alpha_tilde))

def _noise(values, count):
    if type(values) is not np.ndarray or values.shape != (count, 2, 3, 4, 4) or values.dtype.str != '<c16' or (not np.isfinite(values).all()) or (np.linalg.norm(values - values.conj().swapaxes(-1, -2)) > 1e-12 * max(1, np.linalg.norm(values))):
        raise ValueError('prepared paired step requires every full finite Hermitian original innovation')

def _storage(source, initial):
    arrays = {name: np.empty(shape, dtype=dtype) for name, (dtype, shape) in expected_members(source).items()}
    for prefix, refinement in (('primary', 1), ('fine', 2)):
        count = refinement * source.total_ticks + 1
        arrays[prefix + '_ticks'][:] = np.arange(count, dtype='<i8')
        arrays[prefix + '_alpha_tilde'][:] = np.asarray(source.recipe.half_tick_couplings[::2 // refinement], dtype='<f8')
        arrays[prefix + '_positions'][0] = initial.positions
        arrays[prefix + '_momenta'][0] = initial.momenta
    return arrays

def propagate_preparation_state(source, initial, *, coarse_innovations, bridge_innovations, on_step=None):
    """Complete paired native trajectory with explicitly supplied innovations.

    This owns no acquisition, seed selection, persistence or qualification.
    Every fine half step is retained, including the supplied midpoint schedule.
    """
    if type(source) is not MatrixPreparationSource:
        raise TypeError('preparation propagator needs its separate coupling-only source')
    source.__post_init__()
    n = source.total_ticks
    _noise(coarse_innovations, n)
    _noise(bridge_innovations, n)
    return _propagate(source, initial, ((coarse_innovations[tick], bridge_innovations[tick]) for tick in range(n)), on_step=on_step)

def _propagate(source, initial, innovations, *, on_step=None):
    arrays = _storage(source, initial)
    primary = fine = initial
    primary_cache, fine_cache = (BAOABGradientCache(), BAOABGradientCache())
    for step, (coarse, bridge) in enumerate(innovations, start=1):
        primary, middle, fine, halves = advance_preparation_pair(primary, fine, source=source, step=step, coarse=coarse, bridge=bridge, primary_cache=primary_cache, fine_cache=fine_cache)
        arrays['primary_innovations'][step - 1] = coarse
        arrays['bridge_innovations'][step - 1] = bridge
        arrays['fine_innovations'][2 * step - 2:2 * step] = halves
        for state in (middle, fine):
            arrays['fine_positions'][state.step_index] = state.positions
            arrays['fine_momenta'][state.step_index] = state.momenta
        arrays['primary_positions'][primary.step_index] = primary.positions
        arrays['primary_momenta'][primary.step_index] = primary.momenta
        if on_step is not None:
            on_step(3 * step)
    if primary.step_index != source.total_ticks or fine.step_index != 2 * source.total_ticks:
        raise ValueError('preparation producer omits its complete declared paired duration')
    validate_preparation_arrays(source, arrays, initial=initial)
    return arrays

def acquire_preparation_state(source, initial, *, on_step=None):
    """Only the original native lifecycle caller may enter this RNG wrapper."""
    if type(source) is not MatrixPreparationSource:
        raise TypeError('preparation acquisition needs its exact selected native source')
    source.__post_init__()
    selected = {row.purpose: row for row in source.root.streams}
    coarse = np.random.Generator(np.random.PCG64DXSM(selected['preparation-coarse-driver'].effective_seed))
    bridge = np.random.Generator(np.random.PCG64DXSM(selected['preparation-fine-bridge'].effective_seed))
    return _propagate(source, initial, ((hermitian_noise(rng=coarse, q=2), hermitian_noise(rng=bridge, q=2)) for _ in range(source.total_ticks)), on_step=on_step)

def validate_preparation_arrays(source, arrays, *, initial):
    expected = expected_members(source)
    if set(arrays) != set(expected):
        raise ValueError('preparation loses complete phase-space, schedule, clock or innovation members')
    for name, (dtype, shape) in expected.items():
        value = arrays[name]
        if value.dtype.str != dtype or value.shape != shape or (not np.isfinite(value).all()):
            raise ValueError('preparation loses complete finite dtype/shape geometry')
        if dtype == '<c16' and np.linalg.norm(value - value.conj().swapaxes(-1, -2)) > 1e-10 * max(1, np.linalg.norm(value)):
            raise ValueError('preparation contains non-Hermitian native states or innovations')
    for prefix, refinement in (('primary', 1), ('fine', 2)):
        if not np.array_equal(arrays[prefix + '_ticks'], np.arange(refinement * source.total_ticks + 1, dtype='<i8')) or not np.array_equal(arrays[prefix + '_alpha_tilde'], np.asarray(source.recipe.half_tick_couplings[::2 // refinement], dtype='<f8')) or (not np.array_equal(arrays[prefix + '_positions'][0], initial.positions)) or (not np.array_equal(arrays[prefix + '_momenta'][0], initial.momenta)):
            raise ValueError('preparation substitutes original matched initial state, fixed schedule or physical clock')

def _preparation_array_operand(source, raw, members, *, artifact_id):
    """Bind already validated native bytes without expanding their archive again."""
    artifact = ArtifactIdentity(artifact_id, 'coupling-preparation-arrays', MATRIX_ARRAY_SCHEMA, sha256(raw).hexdigest(), 'application/x-npz', len(raw))
    return MatrixPreparationArrays('operand.' + source.source_id, source.identity, source.initial.identity, source.recipe.identity, artifact, members)

def assess_preparation_state(source, initial, operand, arrays, *, assessment_id):
    """Original independent derivative/OU checks over the complete new subject."""
    operand.validate_source(source)
    validate_preparation_arrays(source, arrays, initial=initial)
    design = source.numerical_design
    controls = tuple((MatrixParameterHistoryControl(**row) for row in independent.assess_arrays(source, arrays, trajectory_tolerance=design.trajectory_tolerance, bridge_tolerance=design.bridge_tolerance)))
    result = MatrixPreparationAssessment(assessment_id, source.identity, preparation_identity(operand), preparation_identity(design), controls, all((row.disposition == 'SATISFIED' for row in controls)))
    validate_preparation_assessment(source, operand, result)
    return result

def validate_preparation_assessment(source, operand, assessment):
    operand.validate_source(source)
    assessment.__post_init__()
    n, design = (source.total_ticks, source.numerical_design)
    if assessment.source != source.identity or assessment.arrays != preparation_identity(operand) or assessment.numerical_design != preparation_identity(design) or (tuple(((row.denominator_steps, row.denominator_real_coordinates, row.tolerance) for row in assessment.controls)) != ((n, 192, design.trajectory_tolerance), (2 * n, 192, design.trajectory_tolerance), (n, 192, design.bridge_tolerance), (n, 96, design.trajectory_tolerance))):
        raise ValueError('preparation assessment changes original selected source or full independent denominator')
