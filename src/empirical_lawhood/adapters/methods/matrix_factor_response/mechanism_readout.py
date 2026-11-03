# SPDX-License-Identifier: MPL-2.0
"""Fixed same-bank mechanical controls and signed post-reveal accounting.

This owner consumes authenticated saved branches. It has no native runner,
random generator, fitted selection or access authority. Origin constructions
and the evaluator-only HOLD tangent have separate operand boundaries.
"""
from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
from time import perf_counter, process_time
from types import SimpleNamespace
from typing import ClassVar

import numpy as np

from empirical_lawhood.adapters.simulators.six_matrix_response.gradients import SixMatrixParameters
from empirical_lawhood.adapters.simulators.six_matrix_response.model import hermitian_part
from empirical_lawhood.kernel.serialization import CanonicalRecord

from .causal_hessian import CAUSAL_HESSIAN_RULE, causal_hessian_features
from .response_scoring import DENSE_RESPONSE_HORIZONS, nominal_actuator_scales
from .science import _linear_responses, origin_io_system


@dataclass(frozen=True, slots=True)
class MechanismReadoutRule(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-experiment/mechanism-readout-rule'
    reporting_horizons: tuple[int, ...] = (16, 32, 64, 128)
    secondary_comparator: str = 'INPUT_KRYLOV48'
    position_dimension: int = 24
    basis_rule: str = 'B_Q_THEN_B_P_ACTION_ORDER_THEN_A_K_B_Q_P_K_1_TO_NATIVE128_OR256_THEN_STABLE_ABS_H_SLOW_FILL'
    orthogonalization: str = 'TWO_PROJECTIONS_PER_COLUMN_SIGN_FIRST_LARGEST_ABSOLUTE_COORDINATE_POSITIVE'
    rank_relative_tolerance: Decimal = Decimal('1e-10')
    orthogonality_frobenius_tolerance: Decimal = Decimal('1e-10')
    whitening: str = 'ORIGINAL_FINAL_HORIZON_0128_NOMINAL_ACTUATOR_S_D'
    signed_terms: tuple[str, ...] = ('NATIVE_MINUS_HOLD', 'HOLD_MINUS_FULL', 'FULL_MINUS_FACTOR')
    identity_absolute_tolerance: Decimal = Decimal('1e-12')
    hessian_owner: str = 'six-matrix-q2.parameter-native-derivatives.v1'
    optional_attribution: str = 'NOT_SELECTED_NO_NINE_TERM_OR_SPECTRAL_EXTENSION'

    def __post_init__(self):
        if (self.reporting_horizons != (16, 32, 64, 128) or self.secondary_comparator != 'INPUT_KRYLOV48'
                or type(self.position_dimension) is not int or self.position_dimension != 24
                or self.basis_rule != 'B_Q_THEN_B_P_ACTION_ORDER_THEN_A_K_B_Q_P_K_1_TO_NATIVE128_OR256_THEN_STABLE_ABS_H_SLOW_FILL'
                or self.orthogonalization != 'TWO_PROJECTIONS_PER_COLUMN_SIGN_FIRST_LARGEST_ABSOLUTE_COORDINATE_POSITIVE'
                or self.rank_relative_tolerance != Decimal('1e-10')
                or self.orthogonality_frobenius_tolerance != Decimal('1e-10')
                or self.whitening != 'ORIGINAL_FINAL_HORIZON_0128_NOMINAL_ACTUATOR_S_D'
                or self.signed_terms != ('NATIVE_MINUS_HOLD', 'HOLD_MINUS_FULL', 'FULL_MINUS_FACTOR')
                or self.identity_absolute_tolerance != Decimal('1e-12')
                or self.hessian_owner != 'six-matrix-q2.parameter-native-derivatives.v1'
                or self.optional_attribution != 'NOT_SELECTED_NO_NINE_TERM_OR_SPECTRAL_EXTENSION'):
            raise ValueError('mechanism readout changes its prospective fixed comparator or signed accounting scope')


MECHANISM_READOUT_RULE = MechanismReadoutRule()


class MechanismUnavailable(ValueError):
    """A retained numerical failure, without a new basis, fit or acquisition."""


def input_krylov_basis(transition, inputs, spectrum, eigenvectors, *, native_horizon):
    """The exposed fixed INPUT_KRYLOV48 algorithm, including its slow fallback.

    The inputs and transition are in the declared final-horizon task whitening.
    The resulting position basis is used in both physical q and p blocks.
    """
    if (transition.shape != (192, 192) or inputs.shape != (192, 4)
            or spectrum.shape != (96,) or eigenvectors.shape != (96, 96)
            or type(native_horizon) is not int or native_horizon not in (128, 256)
            or any(value.dtype != np.dtype('float64') or not np.isfinite(value).all()
                for value in (transition, inputs, spectrum, eigenvectors))
            or np.any(np.diff(spectrum) < 0)):
        raise ValueError('INPUT_KRYLOV48 requires its full signed origin spectrum and exact paired-clock system')
    columns, origins = [], []

    def add(vector, label):
        if len(columns) == 24:
            return
        reference = np.linalg.norm(vector)
        if not np.isfinite(reference):
            raise MechanismUnavailable('NONFINITE_INPUT_KRYLOV_COLUMN')
        if reference == 0:
            return
        residual = vector.copy()
        for _ in range(2):
            if columns:
                basis = np.stack(columns, axis=1)
                residual -= basis @ (basis.T @ residual)
        length = np.linalg.norm(residual)
        if not np.isfinite(length):
            raise MechanismUnavailable('NONFINITE_INPUT_KRYLOV_RESIDUAL')
        if length <= float(MECHANISM_READOUT_RULE.rank_relative_tolerance) * reference:
            return
        residual /= length
        if residual[np.argmax(np.abs(residual))] < 0:
            residual = -residual
        columns.append(residual)
        origins.append(label)

    for vector in np.concatenate((inputs[:96], inputs[96:]), axis=1).T:
        add(vector, 'input')
    images = inputs.copy()
    for _ in range(native_horizon):
        images = transition @ images
        for vector in np.concatenate((images[:96], images[96:]), axis=1).T:
            add(vector, 'krylov')
        if len(columns) == 24:
            break
    for vector in eigenvectors[:, np.argsort(np.abs(spectrum), kind='stable')].T:
        add(vector, 'slow')
    if len(columns) != 24:
        raise MechanismUnavailable('INPUT_KRYLOV48_POSITION_RANK_NOT_REACHED')
    basis = np.stack(columns, axis=1)
    residual = np.linalg.norm(basis.T @ basis - np.eye(24))
    if not residual < float(MECHANISM_READOUT_RULE.orthogonality_frobenius_tolerance):
        raise MechanismUnavailable('INPUT_KRYLOV48_ORTHOGONALITY_FAILED')
    return basis, {'input_dimensions': origins.count('input'), 'krylov_dimensions': origins.count('krylov'),
        'slow_fallback_dimensions': origins.count('slow'), 'phase_dimension': 48,
        'orthogonality_residual': _decimal(residual), 'basis_sha256': sha256(basis.tobytes()).hexdigest()}


def hessian_action_batch(positions, perturbations, parameters):
    """Batch only the four action columns of the source-owned polynomial.

    Independent tests compare each column with parameter_derivatives.hessian_image.
    No finite differences, fitted Hessian or native integration enter this path.
    """
    from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_derivatives import matrix
    matrix(positions, 'HOLD positions')
    if (perturbations.ndim != 5 or perturbations.shape[1:] != (2, 3, 4, 4)
            or not 1 <= len(perturbations) <= 4 or perturbations.dtype != np.dtype('complex128')
            or not np.isfinite(perturbations).all() or type(parameters) is not SixMatrixParameters
            or parameters.q != 2):
        raise ValueError('HOLD tangent requires complete source-parameter Hermitian action columns')
    if not np.allclose(perturbations, perturbations.conj().swapaxes(-1, -2), rtol=0, atol=1e-12):
        raise ValueError('HOLD tangent changes its Hermitian coordinate convention')
    state = np.broadcast_to(positions, perturbations.shape)
    output = np.zeros_like(perturbations)

    def commutator(left, right):
        return left @ right - right @ left

    for sector, alpha, beta, mass in ((0, parameters.alpha_x, parameters.beta_x, parameters.mass_x),
            (1, parameters.alpha_y, parameters.beta_y, parameters.mass_y)):
        z, v = state[:, sector], perturbations[:, sector]
        other, w = state[:, 1 - sector], perturbations[:, 1 - sector]
        radius = np.sum(z @ z, axis=1)
        delta_radius = np.sum(v @ z + z @ v, axis=1)
        for a in range(3):
            b, c = ((1, 2), (2, 0), (0, 1))[a]
            value = 2 * beta * v[:, a] + 2j * alpha * (
                commutator(v[:, b], z[:, c]) + commutator(z[:, b], v[:, c]))
            value += 2 * mass * (delta_radius @ z[:, a] + z[:, a] @ delta_radius
                + radius @ v[:, a] + v[:, a] @ radius)
            for b in range(3):
                value += commutator(v[:, b], commutator(z[:, b], z[:, a]))
                value += commutator(z[:, b], commutator(v[:, b], z[:, a]))
                value += commutator(z[:, b], commutator(z[:, b], v[:, a]))
                value += parameters.gamma * (commutator(w[:, b], commutator(other[:, b], z[:, a]))
                    + commutator(other[:, b], commutator(w[:, b], z[:, a]))
                    + commutator(other[:, b], commutator(other[:, b], v[:, a])))
            output[:, sector, a] = parameters.n * value
    return hermitian_part(output)


def hold_tangent_response(positions, alphas, forces, receivers, *, member, numerical_view, pulse_steps):
    """Evaluator-only first variation along a saved HOLD, with both force kicks."""
    steps = len(positions) - 1
    if (steps not in (128, 256) or positions.shape != (steps + 1, 2, 3, 4, 4)
            or alphas.shape != (steps + 1, 2) or forces.shape != (4, 2, 3, 4, 4)
            or receivers.shape != (48, 2, 2, 3, 4, 4)
            or pulse_steps != steps // 8 or numerical_view.timestep * steps != Decimal('.128')):
        raise ValueError('HOLD tangent changes its saved branch, force map or physical observation clock')
    if not all(np.isfinite(value).all() for value in (positions, alphas, forces, receivers)):
        raise MechanismUnavailable('NONFINITE_SAVED_HOLD_OR_INSTRUMENT')
    q = np.zeros_like(forces)
    p = q.copy()
    samples, last_image = [], q.copy()
    dt = float(numerical_view.timestep)
    decay = np.exp(-float(numerical_view.friction_gamma) * dt)
    for tick in range(1, steps + 1):
        kick = .5 * dt * .01 * forces if tick <= pulse_steps else 0.
        last = SixMatrixParameters(2, float(member.mass_x), float(member.mass_y),
            float(member.cross_coupling_gamma), *map(float, alphas[tick]))
        # The preceding final Hessian image is exactly this first-kick image:
        # q and its saved-state parameters have not changed between steps.
        p = hermitian_part(p + kick - .5 * dt * last_image)
        q = hermitian_part(q + .5 * dt * p)
        p = hermitian_part(decay * p)
        q = hermitian_part(q + .5 * dt * p)
        if not np.isfinite(q).all() or not np.isfinite(p).all():
            raise MechanismUnavailable('NONFINITE_HOLD_TANGENT')
        last_image = hessian_action_batch(positions[tick], q, last)
        p = hermitian_part(p + kick - .5 * dt * last_image)
        samples.append(np.einsum('rpsjab,Apsjab->Ar', receivers.conj(), np.stack((q, p), axis=1)).real)
        if not np.isfinite(samples[-1]).all():
            raise MechanismUnavailable('NONFINITE_HOLD_TANGENT')
    return np.transpose(samples, (1, 0, 2))


def _decimal(value):
    return Decimal(repr(float(value)))


def _vector(values):
    return tuple(_decimal(value) for value in values)


def signed_cell(native, hold, full, factor, *, scale):
    """Retain signed task-unit vectors, squared norms and every pair cross term."""
    if (any(value.shape != (24,) or value.dtype != np.dtype('float64') for value in (native, hold, full, factor))
            or not np.isfinite(scale) or scale <= 0):
        raise ValueError('mechanism cell requires one original HS24 block and positive actuator scale')
    if not all(np.isfinite(value).all() for value in (native, hold, full, factor)):
        return {'status': 'UNAVAILABLE', 'reason': 'NONFINITE_NATIVE_OR_MECHANICAL_VECTOR'}
    terms = np.stack((native - hold, hold - full, full - factor)) / scale
    total = (native - factor) / scale
    residual = np.max(np.abs(np.sum(terms, axis=0) - total))
    squares = np.sum(terms * terms, axis=1)
    crosses = tuple(2 * np.dot(terms[left], terms[right]) for left, right in ((0, 1), (0, 2), (1, 2)))
    squared = np.dot(total, total)
    squared_residual = abs(squared - np.sum(squares) - sum(crosses))
    tolerance = float(MECHANISM_READOUT_RULE.identity_absolute_tolerance)
    return {'status': 'AVAILABLE' if residual <= tolerance and squared_residual <= tolerance else 'NUMERICALLY_UNEVALUABLE',
        'signed_task_vectors': tuple(_vector(row) for row in terms),
        'term_norms': _vector(np.sqrt(squares)), 'term_squared_norms': _vector(squares),
        'twice_signed_cross_terms_01_02_12': _vector(crosses),
        'total_error_norm': _decimal(np.linalg.norm(total)), 'total_squared_error': _decimal(squared),
        'actual_response_norm': _decimal(np.linalg.norm(native)),
        'actual_task_normalized_response_norm': _decimal(np.linalg.norm(native) / scale),
        'vector_identity_residual': _decimal(residual), 'squared_identity_residual': _decimal(squared_residual)}


def instrument_summary(frozen):
    """Original maps in the common native Hermitian frame, sufficient for arm contrasts."""
    if 'forces' not in frozen or 'receivers' not in frozen:
        return {'status': 'UNAVAILABLE'}
    from empirical_lawhood.adapters.simulators.six_matrix_response.shooting import hermitian_basis
    basis = hermitian_basis(4).conj()
    forces = np.einsum('kab,Asjab->Asjk', basis, frozen['forces']).real.reshape(4, 96)
    receivers = np.einsum('kab,rpsjab->rpsjk', basis, frozen['receivers']).real.reshape(48, 192)
    return {'status': 'AVAILABLE', 'rule': 'STATE_CONDITIONED_REBUILT_AT_EACH_PREPARED_HANDOFF',
        'force_maps_real_Hermitian': tuple(_vector(row) for row in forces),
        'receiver_maps_real_Hermitian': tuple(_vector(row) for row in receivers),
        'forces_sha256': sha256(frozen['forces'].tobytes()).hexdigest(),
        'receivers_sha256': sha256(frozen['receivers'].tobytes()).hexdigest()}


def compact_instrument(instrument):
    """Original arrays retain the maps; reports keep their pins and arm contrasts."""
    return {name: value for name, value in instrument.items()
        if name not in ('force_maps_real_Hermitian', 'receiver_maps_real_Hermitian')}


def instrument_change(baseline, selected):
    if baseline is None or selected is None or any(row.get('status') != 'AVAILABLE' for row in (baseline, selected)):
        return {'status': 'UNAVAILABLE'}
    force_before, force_after = (np.asarray(row['force_maps_real_Hermitian'], dtype=float) for row in (baseline, selected))
    before, after = (np.asarray(row['receiver_maps_real_Hermitian'], dtype=float) for row in (baseline, selected))
    if (before.shape != (48, 192) or after.shape != before.shape
            or force_before.shape != (4, 96) or force_after.shape != force_before.shape):
        raise ValueError('instrument contrast changes the complete common native Hermitian frame')
    return {'status': 'AVAILABLE', 'force_difference_norms_by_action': _vector(np.linalg.norm(force_after - force_before, axis=1)),
        'receiver_map_difference_frobenius': _decimal(np.linalg.norm(after - before)),
        'receiver_projector_difference_frobenius': _decimal(np.linalg.norm(after.T @ after - before.T @ before)),
        'identical_forces': baseline['forces_sha256'] == selected['forces_sha256'],
        'identical_receiver_map': baseline['receivers_sha256'] == selected['receivers_sha256']}


def same_bank_mechanism(protocol, causal, frozen, received, *, panel_ids, numerical_status, feature_disposition,
        observe_cost=None):
    """Post-reveal descriptive readout, with every selected panel/action/block.

    The API caller binds source records and receipt-authenticated archives and
    retains missing cases. Optional measured costs are separate operational
    observations, so reconstructing the scientific product is deterministic.
    """
    if (type(panel_ids) is not tuple or len(panel_ids) != 2 or panel_ids != tuple(sorted(set(panel_ids)))
            or protocol.horizon_steps != DENSE_RESPONSE_HORIZONS):
        raise ValueError('mechanism readout requires the unchanged complete dense two-panel task')
    start, cpu = perf_counter(), process_time()
    feature_start = perf_counter()
    features = causal_hessian_features(protocol, causal, frozen)
    feature_seconds = perf_counter() - feature_start
    results, comparator_rows = [], []
    coordinate = protocol.public_source.coordinate
    for view, multiplier in (('primary', 1), ('fine', 2)):
        numerical = coordinate.primary_view if multiplier == 1 else coordinate.fine_view
        design = SimpleNamespace(view=numerical, horizon_steps=tuple(tick * multiplier for tick in range(1, 129)))
        actions = tuple(SimpleNamespace(amplitude=action.amplitude, force_norm=action.force_norm,
            pulse_steps=action.pulse_steps * multiplier) for action in protocol.actions)
        krylov, construction = None, {'status': 'UNAVAILABLE', 'reason': 'MISSING_ORIGIN_INSTRUMENT'}
        if view + '_hessian' in frozen:
            try:
                system = origin_io_system(design, frozen[view + '_hessian'], frozen['forces'], frozen['receivers'], actions)
                basis, ranks = input_krylov_basis(system[0], system[1], frozen[view + '_hessian_spectrum'],
                    frozen[view + '_hessian_eigenvectors'], native_horizon=128 * multiplier)
                krylov = np.asarray(_linear_responses(design, basis, frozen[view + '_hessian'],
                    frozen['forces'], frozen['receivers'], actions))
                construction = {'status': 'AVAILABLE', **ranks}
            except MechanismUnavailable as error:
                construction = {'status': 'UNAVAILABLE', 'reason': str(error)}
        comparator_errors = []
        for panel in panel_ids:
            stems = tuple('branch.' + view + '.' + panel + '.' + action.action_id + '.' for action in protocol.actions)
            holds = tuple(stem + 'hold.positions' for stem in stems)
            tangent = None
            tangent_reason = 'MISSING_SAVED_NATIVE_BRANCH'
            if all(name in received for name in holds) and 'forces' in frozen:
                reference = stems[0] + 'hold.'
                ticks = received[reference + 'ticks']
                expected_ticks = np.arange(multiplier * protocol.public_source.policy.cutoff_tick,
                    multiplier * (protocol.public_source.policy.cutoff_tick + 128) + 1)
                if not np.array_equal(ticks, expected_ticks):
                    raise ValueError('mechanism readout substitutes the original physical future clock')
                for stem in stems:
                    if not np.array_equal(received[stem + 'hold.positions'], received[holds[0]], equal_nan=True):
                        raise ValueError('mechanism readout loses the shared HOLD within its noise panel')
                    for sign in ('minus', 'plus', 'hold'):
                        for key in ('ticks', 'alpha_tilde', 'innovations'):
                            if not np.array_equal(received[stem + sign + '.' + key], received[reference + key], equal_nan=True):
                                raise ValueError('mechanism readout changes shared panel noise, schedule or clocks')
                try:
                    tangent = hold_tangent_response(received[holds[0]], received[reference + 'alpha_tilde'],
                        frozen['forces'], frozen['receivers'], member=coordinate.member, numerical_view=numerical,
                        pulse_steps=16 * multiplier)[:, multiplier - 1::multiplier]
                except MechanismUnavailable as error:
                    tangent_reason = str(error)
            for action_index, (action, stem) in enumerate(zip(protocol.actions, stems, strict=True)):
                native = None
                if stem + 'plus.positions' in received and 'receivers' in frozen:
                    plus, minus = (np.stack((received[stem + sign + '.positions'], received[stem + sign + '.momenta']), axis=1)
                        for sign in ('plus', 'minus'))
                    if not np.array_equal(plus[0], minus[0], equal_nan=True):
                        raise ValueError('mechanism readout changes the identical signed branch initial state')
                    native = np.einsum('rpsjab,tpsjab->tr', frozen['receivers'].conj(), (plus - minus) / 2).real[multiplier::multiplier]
                for horizon in DENSE_RESPONSE_HORIZONS:
                    scales = nominal_actuator_scales(action, coordinate.primary_view.timestep, horizon)
                    error = None if native is None or krylov is None else max(float(np.linalg.norm(
                        native[horizon - 1, 24 * block:24 * (block + 1)] - krylov[action_index, horizon - 1, 24 * block:24 * (block + 1)]))
                            / float(scale) for block, scale in enumerate(scales))
                    comparator_errors.append((panel, action.action_id, horizon,
                        None if error is None or not np.isfinite(error) else _decimal(error)))
                    if horizon not in MECHANISM_READOUT_RULE.reporting_horizons:
                        continue
                    for block, scale in enumerate(scales):
                        section = slice(24 * block, 24 * (block + 1))
                        cell = {'status': 'UNAVAILABLE', 'reason': tangent_reason}
                        if native is not None and tangent is not None:
                            cell = signed_cell(native[horizon - 1, section], tangent[action_index, horizon - 1, section],
                                frozen[view + '_full_grid_full_coupled'][action_index, horizon - 1, section],
                                frozen[view + '_full_grid_factor'][action_index, horizon - 1, section], scale=float(scale))
                        results.append({'view': view.upper(), 'panel': panel, 'action': action.action_id,
                            'horizon_tick': horizon, 'block': ('q', 'p')[block], **cell})
        cumulative = tuple(None if any(value is None for _, _, tick, value in comparator_errors if tick <= horizon)
            else max(value for _, _, tick, value in comparator_errors if tick <= horizon) for horizon in DENSE_RESPONSE_HORIZONS)
        from .response_scoring import MatrixSampledResponseDuration
        duration = MatrixSampledResponseDuration(cumulative, Decimal('.01'), numerical_status == 'SATISFIED',
            tuple(value is not None for value in cumulative))
        comparator_rows.append({'view': view.upper(), 'construction': construction, 'cells': tuple(comparator_errors),
            'cumulative_error_curve': cumulative, 'sampled_duration': duration})
    from fractions import Fraction
    paired = tuple(zip(*(row['cumulative_error_curve'] for row in comparator_rows), strict=True))
    discrepancy = (None if any(value is None for pair in paired for value in pair)
        else max(abs(Fraction(left) - Fraction(right)) for left, right in paired))
    if discrepancy is None or discrepancy > Fraction(1, 10000):
        for row in comparator_rows:
            curve = row['cumulative_error_curve']
            row['sampled_duration'] = MatrixSampledResponseDuration(curve, Decimal('.01'), False,
                tuple(value is not None for value in curve))
    result = {'rule': MECHANISM_READOUT_RULE, 'causal_feature_rule': CAUSAL_HESSIAN_RULE,
        'status': 'POST_REVEAL_DESCRIPTIVE_SAME_BANK_NO_NEW_NATIVE_WORK',
        'numerical_status': numerical_status, 'factor_identification_admission': feature_disposition,
        'causal_features': features, 'instrument': instrument_summary(frozen),
        'signed_accounting': tuple(results), 'INPUT_KRYLOV48': tuple(comparator_rows),
        'comparator_paired_curve_discrepancy_exact_ratio': None if discrepancy is None else (discrepancy.numerator, discrepancy.denominator),
        'comparator_paired_numerically_usable': numerical_status == 'SATISFIED' and discrepancy is not None and discrepancy <= Fraction(1, 10000),
        'cost': {'native_calls': 0, 'fit_bundles': 0, 'causal_feature_views': 2, 'signed_cells': len(results),
            'scope': 'DETERMINISTIC_WORK_COUNTS_TIMINGS_IN_SEPARATE_OPERATION_OBSERVATIONS'}}
    if observe_cost is not None:
        observe_cost({'causal_Hessian_read_seconds': _decimal(feature_seconds),
            'total_read_seconds': _decimal(perf_counter() - start), 'total_cpu_seconds': _decimal(process_time() - cpu),
            'scope': 'READ_RECONSTRUCTION_COST_ORIGINAL_WORKFLOW_COST_REPORTED_SEPARATELY'})
    return result
