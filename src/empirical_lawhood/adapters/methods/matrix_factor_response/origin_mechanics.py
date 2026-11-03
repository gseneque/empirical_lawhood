# SPDX-License-Identifier: MPL-2.0
"""Discrete origin mechanics and finite-horizon input/output reduction.

Only a frozen Hessian, instrument and physical clock enter. No future state,
noise, fitting target or authority enters this numerical owner. Retained IO48
witnesses are checked by Stein recurrences and eigenpair/SVD residuals without
rerunning an eigensolver or singular-value decomposition.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

import numpy as np

from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.kernel.provenance import ObjectIdentity


ORIGIN_RESPONSE_PREDICTORS = ('FACTOR', 'FULL_COUPLED', 'GENERIC_SLOW', 'IO48',
    'NORM_RADIUS', 'SPECTRA', 'ZERO_RESPONSE')

# The integer index is retained with the original forecast arrays. It is not a
# scientific success code: decomposition failures remain producer-reported
# nonuse even when preceding finite witnesses independently verify.
IO48_FAILURES = ('NONFINITE_FINITE_HORIZON_GRAMIANS', 'GRAMIAN_EIGENSOLVE_FAILED',
    'INDEFINITE_CONTROLLABILITY_GRAMIAN', 'INDEFINITE_OBSERVABILITY_GRAMIAN',
    'HANKEL_SVD_FAILED', 'HANKEL_CAP_CUTOFF_UNRESOLVED',
    'BALANCED_PROJECTION_ILL_CONDITIONED', 'BALANCED_BIORTHOGONALITY_UNRESOLVED',
    'NONFINITE_BALANCED_REDUCTION', 'NONFINITE_ORIGIN_PULSE_RESPONSE')


@dataclass(frozen=True, slots=True)
class MatrixIO48Construction(CanonicalRecord):
    """Issued numerical choices, fixed before any fresh scientific outcomes."""

    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-response/io48-construction'
    construction_id: str
    maximum_phase_dimension: int = 48
    gramian_relative_floor: Decimal = Decimal('1e-14')
    hankel_relative_floor: Decimal = Decimal('1e-10')
    hankel_absolute_floor: Decimal = Decimal('1e-12')
    witness_relative_tolerance: Decimal = Decimal('1e-8')
    cutoff_relative_gap: Decimal = Decimal('1e-8')
    projection_condition_limit: Decimal = Decimal('1e8')
    state_metric: str = 'FINAL_HORIZON_NOMINAL_ACTUATOR_Q_P'
    trace_treatment: str = 'ALL_NATIVE_TRACE_DIRECTIONS_INCLUDED'
    gramian_rule: str = 'SUM_K_ZERO_THROUGH_N_MINUS_ONE'

    def __post_init__(self):
        validate_stable_id(self.construction_id)
        if (type(self.maximum_phase_dimension) is not int or self.maximum_phase_dimension != 48
                or tuple(getattr(self, name) for name in (
                    'gramian_relative_floor', 'hankel_relative_floor', 'hankel_absolute_floor',
                    'witness_relative_tolerance', 'cutoff_relative_gap', 'projection_condition_limit'))
                != tuple(Decimal(v) for v in ('1e-14', '1e-10', '1e-12', '1e-8', '1e-8', '1e8'))
                or any(type(getattr(self, name)) is not Decimal for name in (
                    'gramian_relative_floor', 'hankel_relative_floor', 'hankel_absolute_floor',
                    'witness_relative_tolerance', 'cutoff_relative_gap', 'projection_condition_limit'))
                or self.state_metric != 'FINAL_HORIZON_NOMINAL_ACTUATOR_Q_P'
                or self.trace_treatment != 'ALL_NATIVE_TRACE_DIRECTIONS_INCLUDED'
                or self.gramian_rule != 'SUM_K_ZERO_THROUGH_N_MINUS_ONE'):
            raise ValueError('IO48 changes its frozen rank, conditioning, metric or trace policy')


@dataclass(frozen=True, slots=True)
class MatrixOriginResponseModel(CanonicalRecord):
    """Amended seven-method assay, separate from closed five-method records."""

    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-response/origin-response-model'
    model_id: str
    implementation: ObjectIdentity
    io48: MatrixIO48Construction
    predictors: tuple[str, ...] = ORIGIN_RESPONSE_PREDICTORS
    fitting_budget: int = 0
    factor_phase_dimension: int = 48
    radius_phase_dimension: int = 24
    spectra_phase_dimension: int = 48
    generic_phase_dimension: int = 48
    benchmark_phase_dimension: int = 192
    zero_phase_dimension: int = 0
    target: str = 'ODD_FINITE_RESPONSE_HALF_PLUS_MINUS'

    def __post_init__(self):
        validate_stable_id(self.model_id)
        if type(self.implementation) is not ObjectIdentity or type(self.io48) is not MatrixIO48Construction:
            raise TypeError('origin response requires its exact implementation and issued IO48 construction')
        self.implementation.__post_init__()
        self.io48.__post_init__()
        if (self.predictors != ORIGIN_RESPONSE_PREDICTORS
                or any(type(getattr(self, name)) is not int for name in ('fitting_budget',
                    'factor_phase_dimension', 'radius_phase_dimension', 'spectra_phase_dimension',
                    'generic_phase_dimension', 'benchmark_phase_dimension', 'zero_phase_dimension'))
                or (self.fitting_budget, self.factor_phase_dimension, self.radius_phase_dimension,
                    self.spectra_phase_dimension, self.generic_phase_dimension,
                    self.benchmark_phase_dimension, self.zero_phase_dimension) != (0, 48, 24, 48, 48, 192, 0)
                or self.target != 'ODD_FINITE_RESPONSE_HALF_PLUS_MINUS'):
            raise ValueError('origin response changes its complete zero-fit methods, dimension or native task')


def model_predictors(model):
    """Exact typed dispatch; the selected model fixes the complete method menu."""
    from .records import MatrixFactorResponseModel, PREDICTORS
    if type(model) in (MatrixFactorResponseModel, MatrixOriginResponseModel):
        model.__post_init__()
        return model.predictors
    if type(model) is ObjectIdentity:
        if model.object_schema == MatrixOriginResponseModel.SCHEMA:
            return ORIGIN_RESPONSE_PREDICTORS
        if model.object_schema == MatrixFactorResponseModel.SCHEMA:
            return PREDICTORS
    raise TypeError('origin response requires an exact selected mechanical model or its sealed identity')


class IO48Unresolved(ValueError):
    """Numerical nonuse; never an outcome-selected replacement reduction."""

    def __init__(self, reason, witnesses):
        super().__init__(reason)
        self.reason, self.witnesses = reason, witnesses


def _finite_matrix(value, name):
    if (not isinstance(value, np.ndarray) or value.dtype.str != '<f8'
            or value.ndim != 2 or not np.isfinite(value).all()):
        raise ValueError(name + ' requires a finite real float64 matrix')
    return value


def _system(transition, inputs, outputs):
    for name, value in (('transition', transition), ('inputs', inputs), ('outputs', outputs)):
        _finite_matrix(value, name)
    n = transition.shape[0]
    if (not 1 <= n <= 192 or transition.shape != (n, n) or inputs.shape[0] != n
            or outputs.shape[1] != n or not inputs.shape[1] or not outputs.shape[0]):
        raise ValueError('origin response changes its bounded state/input/output geometry')
    return n


def discrete_baoab_maps(hessian, force_inputs, *, timestep, decay):
    """Zero-initial-response affine map, including both per-step force kicks.

    ``force_inputs`` already contains each action's amplitude. Momentum is the
    native velocity; potential mass coefficients do not add a kinetic mass.
    """
    _finite_matrix(hessian, 'Hessian')
    _finite_matrix(force_inputs, 'force inputs')
    n = hessian.shape[0]
    if (not 1 <= n <= 96 or hessian.shape != (n, n) or force_inputs.shape[0] != n
            or not force_inputs.shape[1] or not np.isfinite(timestep) or timestep <= 0
            or not np.isfinite(decay) or not 0 < decay <= 1
            or not np.allclose(hessian, hessian.T, rtol=0, atol=1e-12)):
        raise ValueError('discrete BAOAB requires the symmetric frozen Hessian and physical clock')
    half = timestep / 2
    drift = half * (1 + decay)
    qq = np.eye(n) - drift * half * hessian
    qp = drift * np.eye(n)
    pq = -half * (decay * hessian + hessian @ qq)
    pp = decay * np.eye(n) - half * hessian @ qp
    bq = drift * half * force_inputs
    bp = drift * force_inputs - half * hessian @ bq
    return np.block([[qq, qp], [pq, pp]]), np.concatenate((bq, bp))


def scaled_origin_system(hessian, force_inputs, receiver_map, *, timestep, decay,
        position_scale, momentum_scale):
    """Common dimensionless state and final-horizon quadratic output metric.

    The first half of receiver rows has position support and the second half
    momentum support. The scored task later uses each horizon's own scales.
    """
    transition, inputs = discrete_baoab_maps(hessian, force_inputs, timestep=timestep, decay=decay)
    n = hessian.shape[0]
    _finite_matrix(receiver_map, 'receiver map')
    m = receiver_map.shape[0]
    if (receiver_map.shape[1] != 2 * n or m < 2 or m % 2
            or not np.isfinite(position_scale) or position_scale <= 0
            or not np.isfinite(momentum_scale) or momentum_scale <= 0
            or np.any(receiver_map[:m // 2, n:]) or np.any(receiver_map[m // 2:, :n])):
        raise ValueError('origin scaling changes the positive actuator scales or phase receiver blocks')
    state_units = np.repeat(np.asarray((position_scale, momentum_scale)), n)
    output_units = np.repeat(np.asarray((position_scale, momentum_scale)), m // 2)
    return (transition * state_units[None, :] / state_units[:, None],
        inputs / state_units[:, None],
        receiver_map * state_units[None, :] / output_units[:, None], state_units, output_units)


def finite_horizon_gramians(transition, inputs, outputs, steps):
    """Explicit k=0..N-1 sums: impulse outputs include CB and CA**(N-1)B."""
    n = _system(transition, inputs, outputs)
    if type(steps) is not int or not 1 <= steps <= 256:
        raise ValueError('finite-horizon balancing requires between one and 256 physical steps')
    wc, wo = np.zeros((n, n)), np.zeros((n, n))
    reachable, observed = inputs.copy(), outputs.copy()
    with np.errstate(over='ignore', invalid='ignore'):
        for k in range(steps):
            wc += reachable @ reachable.T
            wo += observed.T @ observed
            if k + 1 < steps:
                reachable, observed = transition @ reachable, observed @ transition
    if not np.isfinite(wc).all() or not np.isfinite(wo).all():
        raise IO48Unresolved('NONFINITE_FINITE_HORIZON_GRAMIANS', {})
    return wc / 2 + wc.T / 2, wo / 2 + wo.T / 2


def _norm(value):
    scale = float(np.max(np.abs(value), initial=0.))
    return scale * float(np.linalg.norm(value / scale)) if scale else 0.


def _close(actual, expected, tolerance, label):
    if actual.shape != expected.shape or not np.isfinite(actual).all() or not np.isfinite(expected).all():
        raise ValueError('IO48 retained ' + label + ' fails independent numerical reproof')
    scale = max(1., float(np.max(np.abs(expected), initial=0.)))
    if _norm(actual / scale - expected / scale) > tolerance * max(1 / scale, _norm(expected / scale)):
        raise ValueError('IO48 retained ' + label + ' fails independent numerical reproof')


def _stein_gramians(transition, inputs, outputs, steps):
    """Independent Stein recurrences, not the producer's propagated-column sum."""
    n = _system(transition, inputs, outputs)
    if type(steps) is not int or not 1 <= steps <= 256:
        raise ValueError('IO48 reproof changes its finite physical horizon')
    actual_c, actual_o = np.zeros((n, n)), np.zeros((n, n))
    bb, cc = inputs @ inputs.T, outputs.T @ outputs
    with np.errstate(over='ignore', invalid='ignore'):
        for _ in range(steps):
            actual_c = bb + transition @ actual_c @ transition.T
            actual_o = cc + transition.T @ actual_o @ transition
    return actual_c, actual_o


def _verify_gramians(transition, inputs, outputs, steps, wc, wo, tolerance):
    actual_c, actual_o = _stein_gramians(transition, inputs, outputs, steps)
    _close(wc, actual_c, tolerance, 'controllability Gramian')
    _close(wo, actual_o, tolerance, 'observability Gramian')


def _root(gramian, values, vectors, construction, label):
    n, tol = len(gramian), float(construction.witness_relative_tolerance)
    if (values.dtype.str != '<f8' or values.shape != (n,) or not np.isfinite(values).all()
            or vectors.dtype.str != '<f8' or vectors.shape != (n, n) or not np.isfinite(vectors).all()
            or np.any(np.diff(values) < 0)):
        raise ValueError('IO48 loses complete ordered ' + label + ' eigenpair witnesses')
    _close(vectors.T @ vectors, np.eye(n), tol, label + ' orthogonality')
    _close((vectors * values) @ vectors.T, gramian, tol, label + ' eigenpairs')
    if values[0] < -tol * max(1., _norm(gramian)):
        raise IO48Unresolved('INDEFINITE_' + label.upper() + '_GRAMIAN', {})
    selected = values > float(construction.gramian_relative_floor) * max(0., values[-1])
    return vectors[:, selected] * np.sqrt(values[selected])


@dataclass(frozen=True, slots=True)
class IO48Reduction:
    """Numerical result; canonical source, array and custody owners bind it."""

    transition: np.ndarray
    inputs: np.ndarray
    outputs: np.ndarray
    lift: np.ndarray
    restrict: np.ndarray
    reachable_rank: int
    observable_rank: int
    balanced_rank: int
    effective_rank: int
    projection_condition_bound: float
    witnesses: dict[str, np.ndarray]


def balance_io48(transition, inputs, outputs, steps, construction, *, retained=None, declared_failure=None):
    """Square-root/SVD reduction; lower numerical rank is retained explicitly.

    Cold use authenticates original arrays, not regenerated eigenvectors or a
    newly selected subspace. The caller owns the exact original array identity.
    """
    if declared_failure is not None and (retained is None or declared_failure not in IO48_FAILURES[:-1]):
        raise ValueError('IO48 nonuse requires original retained stage witnesses and a declared reduction failure')
    try:
        result = _balance_io48(transition, inputs, outputs, steps, construction,
            retained=retained, declared_failure=declared_failure)
    except IO48Unresolved as error:
        if retained is not None and error.reason != declared_failure:
            raise ValueError('IO48 cold nonuse differs from the original sealed failure') from error
        raise
    if declared_failure is not None:
        raise ValueError('IO48 original nonuse is contradicted by its retained numerical witnesses')
    return result


def _balance_io48(transition, inputs, outputs, steps, construction, *, retained, declared_failure):
    if type(construction) is not MatrixIO48Construction:
        raise TypeError('IO48 requires its exact issued construction')
    construction.__post_init__()
    _system(transition, inputs, outputs)
    tol = float(construction.witness_relative_tolerance)
    gramian_names = {'gramian_c', 'gramian_o'}
    eigen_names = {label + suffix for label in ('controllability', 'observability')
        for suffix in ('_values', '_vectors')}
    svd_names = {'hankel_values', 'hankel_left', 'hankel_right_t'}
    map_names = {'lift', 'restrict', 'reduced_transition', 'reduced_inputs', 'reduced_outputs'}
    full_names = gramian_names | eigen_names | svd_names | map_names
    if retained is None:
        wc, wo = finite_horizon_gramians(transition, inputs, outputs, steps)
        arrays = {'gramian_c': wc, 'gramian_o': wo}
        try:
            for label, gramian in (('controllability', wc), ('observability', wo)):
                arrays[label + '_values'], arrays[label + '_vectors'] = np.linalg.eigh(gramian)
        except np.linalg.LinAlgError as error:
            raise IO48Unresolved('GRAMIAN_EIGENSOLVE_FAILED', arrays) from error
    else:
        expected = full_names
        if declared_failure == 'NONFINITE_FINITE_HORIZON_GRAMIANS':
            expected = set()
        elif declared_failure == 'GRAMIAN_EIGENSOLVE_FAILED':
            expected = gramian_names | (eigen_names & set(retained))
            if eigen_names & set(retained) not in (set(), {'controllability_values', 'controllability_vectors'}):
                raise ValueError('IO48 loses its exact failed eigensolve stage')
        elif declared_failure in ('INDEFINITE_CONTROLLABILITY_GRAMIAN', 'INDEFINITE_OBSERVABILITY_GRAMIAN', 'HANKEL_SVD_FAILED'):
            expected = gramian_names | eigen_names
        elif declared_failure in ('HANKEL_CAP_CUTOFF_UNRESOLVED', 'BALANCED_PROJECTION_ILL_CONDITIONED',
                'BALANCED_BIORTHOGONALITY_UNRESOLVED'):
            expected = gramian_names | eigen_names | svd_names
        if set(retained) != expected or any(not isinstance(a, np.ndarray) or a.dtype.str != '<f8'
                or not np.isfinite(a).all() and not (declared_failure == 'NONFINITE_BALANCED_REDUCTION' and name in map_names)
                for name, a in retained.items()):
            raise ValueError('IO48 cold reader loses its complete retained stage witness census')
        arrays = dict(retained)
        if declared_failure == 'NONFINITE_FINITE_HORIZON_GRAMIANS':
            actual_c, actual_o = _stein_gramians(transition, inputs, outputs, steps)
            if np.isfinite(actual_c).all() and np.isfinite(actual_o).all():
                raise ValueError('IO48 retained nonfinite Gramian nonuse fails independent reproof')
            raise IO48Unresolved(declared_failure, arrays)
        wc, wo = arrays['gramian_c'], arrays['gramian_o']
        _verify_gramians(transition, inputs, outputs, steps, wc, wo, tol)
        if declared_failure == 'GRAMIAN_EIGENSOLVE_FAILED':
            if 'controllability_values' in arrays:
                _root(wc, arrays['controllability_values'], arrays['controllability_vectors'], construction, 'controllability')
            # A failed solver call has no mathematical success witness. Original
            # custody authenticates reported nonuse; no solver is retried here.
            raise IO48Unresolved(declared_failure, arrays)
    try:
        rc = _root(wc, arrays['controllability_values'], arrays['controllability_vectors'], construction, 'controllability')
        ro = _root(wo, arrays['observability_values'], arrays['observability_vectors'], construction, 'observability')
    except IO48Unresolved as error:
        raise IO48Unresolved(error.reason, arrays) from error
    cross = ro.T @ rc
    if declared_failure == 'HANKEL_SVD_FAILED':
        raise IO48Unresolved(declared_failure, arrays)
    if retained is None:
        try:
            arrays['hankel_left'], arrays['hankel_values'], arrays['hankel_right_t'] = np.linalg.svd(cross, full_matrices=False)
        except np.linalg.LinAlgError as error:
            raise IO48Unresolved('HANKEL_SVD_FAILED', arrays) from error
    left, singular, right_t = (arrays[name] for name in ('hankel_left', 'hankel_values', 'hankel_right_t'))
    count = min(cross.shape)
    if (singular.shape != (count,) or left.shape != (cross.shape[0], count)
            or right_t.shape != (count, cross.shape[1]) or not np.isfinite(singular).all()
            or np.any(singular < 0) or np.any(np.diff(singular) > 0)):
        raise ValueError('IO48 changes complete ordered singular-value witnesses')
    _close((left * singular) @ right_t, cross, tol, 'Hankel SVD')
    _close(left.T @ left, np.eye(count), tol, 'left singular-vector orthogonality')
    _close(right_t @ right_t.T, np.eye(count), tol, 'right singular-vector orthogonality')
    threshold = max(float(construction.hankel_absolute_floor),
        float(construction.hankel_relative_floor) * (singular[0] if count else 0.))
    rank = int(np.count_nonzero(singular > threshold))
    kept = min(construction.maximum_phase_dimension, rank)
    if kept < rank and singular[kept - 1] - singular[kept] <= float(construction.cutoff_relative_gap) * singular[0]:
        raise IO48Unresolved('HANKEL_CAP_CUTOFF_UNRESOLVED', arrays)
    inverse = 1 / np.sqrt(singular[:kept])
    lift = (rc @ right_t[:kept].T) * inverse
    restrict = inverse[:, None] * (left[:, :kept].T @ ro.T)
    condition = _norm(lift) * _norm(restrict)
    if not np.isfinite(condition) or condition > float(construction.projection_condition_limit):
        raise IO48Unresolved('BALANCED_PROJECTION_ILL_CONDITIONED', arrays)
    try:
        _close(restrict @ lift, np.eye(kept), tol, 'biorthogonal projection')
    except ValueError as error:
        raise IO48Unresolved('BALANCED_BIORTHOGONALITY_UNRESOLVED', arrays) from error
    if declared_failure is not None and declared_failure != 'NONFINITE_BALANCED_REDUCTION':
        raise ValueError('IO48 original nonuse is contradicted by its retained numerical witnesses')
    derived = {'lift': lift, 'restrict': restrict, 'reduced_transition': restrict @ transition @ lift,
        'reduced_inputs': restrict @ inputs, 'reduced_outputs': outputs @ lift}
    if retained is not None:
        for name, value in derived.items():
            if not np.array_equal(value, retained[name], equal_nan=True):
                raise ValueError('IO48 changes its exact retained projection or reduced map')
    arrays.update(derived)
    if any(not np.isfinite(a).all() for a in arrays.values()):
        raise IO48Unresolved('NONFINITE_BALANCED_REDUCTION', arrays)
    return IO48Reduction(derived['reduced_transition'], derived['reduced_inputs'], derived['reduced_outputs'],
        lift, restrict, rc.shape[1], ro.shape[1], rank, kept, condition, arrays)


def pulse_responses(transition, inputs, outputs, *, pulse_steps, horizons, output_units):
    """All action columns, with no amplitude division or output interpolation."""
    for name, value in (('transition', transition), ('inputs', inputs), ('outputs', outputs)):
        _finite_matrix(value, name)
    n, actions = inputs.shape
    if (transition.shape != (n, n) or outputs.shape[1] != n or not actions
            or type(pulse_steps) is not tuple or len(pulse_steps) != actions
            or type(horizons) is not tuple or not horizons or horizons != tuple(sorted(set(horizons)))
            or any(type(t) is not int or not 1 <= t <= 256 for t in horizons)
            or any(type(t) is not int or not 1 <= t <= horizons[-1] for t in pulse_steps)
            or not isinstance(output_units, np.ndarray) or output_units.shape != (outputs.shape[0],)
            or not np.isfinite(output_units).all() or np.any(output_units <= 0)):
        raise ValueError('origin pulse changes its action, output scale or sampled physical clock')
    state, result = np.zeros((n, actions)), []
    with np.errstate(over='ignore', invalid='ignore'):
        for tick in range(1, horizons[-1] + 1):
            state = transition @ state + inputs * (tick <= np.asarray(pulse_steps))[None, :]
            if tick in horizons:
                result.append((outputs @ state).T * output_units)
    values = np.stack(result, axis=1)
    if not np.isfinite(values).all():
        raise IO48Unresolved('NONFINITE_ORIGIN_PULSE_RESPONSE', {})
    return values


def factor_feedback_norms(transition, factor_basis, steps):
    """Scaled Frobenius escape, return and k=0..N-1 memory-block norms.

    A phase-space orthonormal basis retains the low-rank calculation. No dense
    matrix per tick is retained, and no realised future tangent enters.
    """
    _finite_matrix(transition, 'transition')
    _finite_matrix(factor_basis, 'factor phase basis')
    n, rank = factor_basis.shape
    if (transition.shape != (n, n) or not 1 <= n <= 192 or not 1 <= rank <= n
            or type(steps) is not int or not 1 <= steps <= 256
            or not np.allclose(factor_basis.T @ factor_basis, np.eye(rank), rtol=0, atol=1e-12)):
        raise ValueError('factor memory changes its scaled phase projector or finite horizon')
    complement = np.eye(n) - factor_basis @ factor_basis.T
    escape = complement @ transition @ factor_basis
    returning = factor_basis.T @ transition @ complement
    complement_map = complement @ transition @ complement
    carried, curve = escape.copy(), []
    with np.errstate(over='ignore', invalid='ignore'):
        for k in range(steps):
            curve.append(np.linalg.norm(returning @ carried))
            if k + 1 < steps:
                carried = complement_map @ carried
    result = np.asarray(curve, dtype='<f8')
    if not np.isfinite(result).all():
        raise IO48Unresolved('NONFINITE_ORIGIN_MEMORY_CURVE', {})
    return float(np.linalg.norm(escape)), float(np.linalg.norm(returning)), result
