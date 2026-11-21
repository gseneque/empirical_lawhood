# SPDX-License-Identifier: MPL-2.0
"""Fixed-basis, own-state continuation from one explicitly supplied observation.

The prediction boundary has no native response or subsequent HOLD trajectory.
Evaluation consumes those separately, after every prediction has been made.
"""

from dataclasses import dataclass
from decimal import Decimal
from time import perf_counter, process_time
from types import SimpleNamespace

import numpy as np

from empirical_lawhood.domains.matrix.six_matrix_response.shooting import hermitian_basis

from empirical_lawhood.domains.matrix.matrix_factor_response.mechanism_readout import MechanismUnavailable, hold_tangent_response, input_krylov_basis, signed_cell
from empirical_lawhood.domains.matrix.matrix_factor_response.refresh_records import REFRESH_METHODS, REFRESH_RULE
from empirical_lawhood.domains.matrix.matrix_factor_response.response_scoring import DENSE_RESPONSE_HORIZONS, nominal_actuator_scales
from empirical_lawhood.domains.matrix.matrix_factor_response.science import _block_modes, frame_axes, native_position_coordinates, origin_io_system


@dataclass(frozen=True, slots=True)
class RefreshObservation:
    """Only the permitted panel-specific position and parameters at physical .032."""
    view: str
    panel_id: str
    relative_native_tick: int
    position: np.ndarray
    alpha: np.ndarray

    def __post_init__(self):
        if (self.view not in ('primary', 'fine')
                or self.relative_native_tick != (32 if self.view == 'primary' else 64)
                or self.position.shape != (2, 3, 4, 4) or self.position.dtype != np.dtype('complex128')
                or self.alpha.shape != (2,) or self.alpha.dtype != np.dtype('float64')
                or not np.isfinite(self.position).all() or not np.isfinite(self.alpha).all()
                or not np.allclose(self.position, self.position.conj().swapaxes(-1, -2), atol=1e-12, rtol=0)):
            raise ValueError('SCI01 refresh requires the exact finite tick-32 Hermitian observation')


def continue_response(origin_operator, basis, force_inputs, *, timestep, friction, native_horizon,
                      refresh_operator=None):
    """Two-kick BAOAB, with no response reset or new projection at tick 32.

    Inputs contain the original physical force times its pulse amplitude.
    States include zero and every native tick, in the unchanged q/p basis.
    Small dimensions are supported for independent algebraic controls.
    """
    if type(native_horizon) is not int or timestep * native_horizon != Decimal('.128'):
        raise ValueError('SCI01 continuation changes its finite fixed span, force or physical clock')
    return continue_response_window(origin_operator, basis, force_inputs, timestep=timestep,
        friction=friction, primary_horizon=128, pulse_ticks=16, refresh_tick=32,
        refresh_operator=refresh_operator)


def continue_response_window(origin_operator, basis, force_inputs, *, timestep, friction,
                             primary_horizon, pulse_ticks, refresh_tick, refresh_operator=None):
    """Fixed-basis two-kick propagation on an explicitly selected physical window.

    No model state resets at the update. The original SCI01 wrapper retains its
    H128 contract; a successor must select its own window and information rule.
    """
    n = len(origin_operator)
    if (origin_operator.shape != (n, n) or not 1 <= n <= 96 or basis.ndim != 2 or basis.shape[0] != n
            or not 1 <= basis.shape[1] <= n or force_inputs.shape != (n, 4)
            or any(a.dtype != np.dtype('float64') or not np.isfinite(a).all()
                   for a in (origin_operator, basis, force_inputs))
            or not np.allclose(origin_operator, origin_operator.T, atol=1e-12, rtol=0)
            or np.linalg.norm(basis.T @ basis - np.eye(basis.shape[1])) > 1e-10
            or type(timestep) is not Decimal or timestep not in (Decimal('.001'), Decimal('.0005'))
            or type(friction) is not Decimal or not friction.is_finite() or friction < 0
            or any(type(v) is not int for v in (primary_horizon, pulse_ticks, refresh_tick))
            or not 1 <= pulse_ticks <= refresh_tick <= primary_horizon <= 128):
        raise ValueError('response continuation changes its finite fixed span, force or physical clock')
    if refresh_operator is not None and (refresh_operator.shape != (n, n)
            or refresh_operator.dtype != np.dtype('float64') or not np.isfinite(refresh_operator).all()
            or not np.allclose(refresh_operator, refresh_operator.T, atol=1e-12, rtol=0)):
        raise ValueError('SCI01 refresh changes its physical operator coordinates')
    h = float(timestep) / 2
    decay = np.exp(-float(friction * timestep))
    multiplier = 1 if timestep == Decimal('.001') else 2
    native_horizon = primary_horizon * multiplier
    operators = (basis.T @ origin_operator @ basis,
                 None if refresh_operator is None else basis.T @ refresh_operator @ basis)
    force = basis.T @ force_inputs
    q = np.zeros((basis.shape[1], 4))
    p = q.copy()
    states = [np.concatenate((q, p), axis=0).T.copy()]
    for tick in range(1, native_horizon + 1):
        operator = operators[1] if refresh_operator is not None and tick > refresh_tick * multiplier else operators[0]
        kick = h * force if tick <= pulse_ticks * multiplier else 0.
        p += kick - h * (operator @ q)
        q += h * p
        p *= decay
        q += h * p
        p += kick - h * (operator @ q)
        if not np.isfinite(q).all() or not np.isfinite(p).all():
            raise MechanismUnavailable('NONFINITE_SCI01_CONTINUATION')
        states.append(np.concatenate((q, p), axis=0).T.copy())
    return np.transpose(states, (1, 0, 2))


def receiver_matrix(receivers):
    return np.einsum('kab,rpsjab->rpsjk', hermitian_basis(4).conj(), receivers).real.reshape(48, 192)


def phase_coordinates(states):
    """Raw physical q/p states to the existing common native Hermitian frame."""
    return np.einsum('kab,...psjab->...psjk', hermitian_basis(4).conj(), states).real.reshape(*states.shape[:-5], 192)


def lift_states(states, basis):
    dimension = basis.shape[1]
    return np.concatenate((states[..., :dimension] @ basis.T, states[..., dimension:] @ basis.T), axis=-1)


def _validate_assay(protocol, frozen, panel_ids):
    if (protocol.horizon_steps != DENSE_RESPONSE_HORIZONS or protocol.receiver_count != 48
            or len(protocol.actions) != 4 or tuple(sorted(a.role for a in protocol.actions))
                != ('COMPLEMENT', 'FACTOR', 'GENERIC', 'TRACE')
            or any(a.amplitude != Decimal('.01') or a.pulse_steps != 16 or a.force_norm != Decimal(1) for a in protocol.actions)
            or len(panel_ids) != 2 or panel_ids != tuple(sorted(set(panel_ids)))
            or frozen['forces'].shape != (4, 2, 3, 4, 4)
            or frozen['receivers'].shape != (48, 2, 2, 3, 4, 4)):
        raise ValueError('SCI01 changes the original complete force/receiver task')


def select_refresh_observations(protocol, received, *, panel_ids):
    """Validate clocks and shared branches before isolating the four observations."""
    observations = []
    cutoff = protocol.public_source.policy.cutoff_tick
    for view, mult in (('primary', 1), ('fine', 2)):
        count = 128 * mult
        expected_ticks = np.arange(mult * cutoff, mult * cutoff + count + 1)
        for panel in panel_ids:
            reference = f'branch.{view}.{panel}.{protocol.actions[0].action_id}.hold.'
            position, alpha = received[reference + 'positions'], received[reference + 'alpha_tilde']
            if position.shape != (count + 1, 2, 3, 4, 4) or alpha.shape != (count + 1, 2):
                raise ValueError('SCI01 loses a complete saved HOLD clock')
            if not np.array_equal(received[reference + 'ticks'], expected_ticks):
                raise ValueError('SCI01 substitutes its original absolute response clock')
            # This retained successor is restricted to the constant-parameter response suffix.
            if not np.array_equal(alpha, np.broadcast_to(alpha[0], alpha.shape)):
                raise ValueError('SCI01 does not replace a changing future parameter schedule')
            for action in protocol.actions:
                stem = f'branch.{view}.{panel}.{action.action_id}.'
                for phase in ('positions', 'momenta'):
                    if not np.array_equal(received[stem + 'hold.' + phase], received[reference + phase]):
                        raise ValueError('SCI01 substitutes a panel HOLD observation')
                    initial = received[reference + phase][0]
                    if any(not np.array_equal(received[stem + sign + '.' + phase][0], initial)
                           for sign in ('plus', 'minus')):
                        raise ValueError('SCI01 substitutes the common signed-branch origin')
                for sign in ('plus', 'minus', 'hold'):
                    for name in ('ticks', 'alpha_tilde', 'innovations'):
                        if not np.array_equal(received[stem + sign + '.' + name], received[reference + name]):
                            raise ValueError('SCI01 changes the original shared noise, parameters or clocks')
            observations.append(RefreshObservation(view, panel, 32 * mult,
                position[32 * mult].copy(), alpha[32 * mult].copy()))
    return tuple(observations)


def predict_refresh_case(protocol, causal, frozen, observations, *, panel_ids, observe_cost=None):
    """Forecast with origin operands and checkpoint-only information.

    No realized response or later baseline is accepted by this function.
    Original FULL and FACTOR are reconstructed as controls, without a new fit.
    """
    from empirical_lawhood.domains.matrix.matrix_scheduled_history.response_forecast import _hessian
    _validate_assay(protocol, frozen, panel_ids)
    if tuple((o.view, o.panel_id) for o in observations) != tuple(
            (view, panel) for view in ('primary', 'fine') for panel in panel_ids):
        raise ValueError('SCI01 requires exactly one own-panel observation per numerical view')
    start, cpu = perf_counter(), process_time()
    output = {'forces': frozen['forces'], 'receivers': frozen['receivers']}
    force = np.stack([native_position_coordinates(f) * float(a.amplitude)
        for f, a in zip(frozen['forces'], protocol.actions, strict=True)], axis=1)
    receiver = receiver_matrix(frozen['receivers'])
    factor = _block_modes([frame_axes(causal['frame'])] * 6)
    constructions, timings = {}, {}
    for view, mult in (('primary', 1), ('fine', 2)):
        numerical = getattr(protocol.public_source.coordinate, view + '_view')
        design = SimpleNamespace(view=numerical, horizon_steps=tuple(range(1, 128 * mult + 1)))
        actions = tuple(SimpleNamespace(amplitude=a.amplitude, force_norm=a.force_norm, pulse_steps=16 * mult)
                        for a in protocol.actions)
        h0 = frozen[view + '_hessian']
        before = perf_counter()
        system = origin_io_system(design, h0, frozen['forces'], frozen['receivers'], actions)
        krylov, construction = input_krylov_basis(system[0], system[1], frozen[view + '_hessian_spectrum'],
            frozen[view + '_hessian_eigenvectors'], native_horizon=128 * mult)
        constructions[view] = construction
        timings[view + '.basis_seconds'] = perf_counter() - before
        output[view + '.h0'] = h0
        bases = {'FULL': np.eye(96), 'INPUT_KRYLOV48': krylov, 'FACTOR': factor}
        state_ticks = np.asarray((0, 32, 64, 128), dtype='<i8') * mult
        output[view + '.state_ticks'] = state_ticks
        frozen_prefixes = {}
        for method, basis in bases.items():
            output[view + '.basis.' + method.lower()] = basis
            before = perf_counter()
            states = continue_response(h0, basis, force, timestep=numerical.timestep,
                friction=numerical.friction_gamma, native_horizon=128 * mult)
            output[view + '.state.' + method.lower()] = states[:, state_ticks].copy()
            frozen_prefixes[method] = states[:, :32 * mult + 1].copy()
            prediction = lift_states(states[:, mult::mult], basis) @ receiver.T
            output[view + '.prediction.' + method.lower()] = prediction
            timings[view + '.propagation.' + method + '_seconds'] = perf_counter() - before
            original = {'FULL': 'full_coupled', 'FACTOR': 'factor'}.get(method)
            if original is not None and not np.allclose(prediction,
                    frozen[view + '_full_grid_' + original], atol=1e-14, rtol=1e-10):
                raise ValueError('SCI01 origin reconstruction differs from its original retained forecast')
        for pi, panel in enumerate(panel_ids):
            observation = next(o for o in observations if o.view == view and o.panel_id == panel)
            prefix = f'{view}.p{pi}'
            output[prefix + '.checkpoint.position'] = observation.position
            output[prefix + '.checkpoint.alpha'] = observation.alpha
            before = perf_counter()
            h32 = _hessian(protocol, observation.position, observation.alpha)
            timings[prefix + '.operator_seconds'] = perf_counter() - before
            output[prefix + '.h32'] = h32
            for method in ('FULL', 'INPUT_KRYLOV48'):
                before = perf_counter()
                states = continue_response(h0, bases[method], force, timestep=numerical.timestep,
                    friction=numerical.friction_gamma, native_horizon=128 * mult, refresh_operator=h32)
                name = method + '_REFRESH32'
                output[prefix + '.state.' + name.lower()] = states[:, state_ticks].copy()
                output[prefix + '.prediction.' + name.lower()] = lift_states(states[:, mult::mult], bases[method]) @ receiver.T
                timings[prefix + '.propagation.' + name + '_seconds'] = perf_counter() - before
                if not np.array_equal(states[:, :32 * mult + 1], frozen_prefixes[method]):
                    raise ValueError('SCI01 refresh changes already completed predictions')
    if observe_cost is not None:
        observe_cost({'phase': 'prediction', 'wall_seconds': perf_counter() - start,
            'cpu_seconds': process_time() - cpu, 'components': timings})
    return output, constructions


def prediction_for(arrays, view, panel_index, method):
    return arrays[(f'{view}.p{panel_index}' if method.endswith('_REFRESH32') else view) + '.prediction.' + method.lower()]


def evaluate_refresh_case(protocol, predictions, received, *, panel_ids, observe_cost=None):
    """Retain signed vectors and complete weak-channel accounting after prediction."""
    start, cpu = perf_counter(), process_time()
    output = dict(predictions)
    scales = np.asarray([[tuple(map(float, nominal_actuator_scales(action,
        protocol.public_source.coordinate.primary_view.timestep, tick)))
        for tick in range(1, 129)] for action in protocol.actions])
    output['scales'] = scales
    for view, mult in (('primary', 1), ('fine', 2)):
        numerical = getattr(protocol.public_source.coordinate, view + '_view')
        for pi, panel in enumerate(panel_ids):
            prefix = f'{view}.p{pi}'
            reference = f'branch.{view}.{panel}.{protocol.actions[0].action_id}.hold.'
            hold = hold_tangent_response(received[reference + 'positions'], received[reference + 'alpha_tilde'],
                predictions['forces'], predictions['receivers'], member=protocol.public_source.coordinate.member,
                numerical_view=numerical, pulse_steps=16 * mult)[:, mult - 1::mult]
            native, endpoints = [], []
            for action in protocol.actions:
                stem = f'branch.{view}.{panel}.{action.action_id}.'
                plus, minus = (np.stack([received[stem + sign + '.' + key] for key in ('positions', 'momenta')], axis=1)
                               for sign in ('plus', 'minus'))
                odd = (plus - minus) / 2
                native.append(np.einsum('rpsjab,tpsjab->tr', predictions['receivers'].conj(), odd).real[mult::mult])
                endpoints.append(phase_coordinates(odd[np.array((64, 128)) * mult]))
            native = np.asarray(native)
            output[prefix + '.native'] = native
            output[prefix + '.native.phase.endpoints'] = np.asarray(endpoints)
            output[prefix + '.hold'] = hold
            output[prefix + '.signal'] = np.linalg.norm(native.reshape(4, 128, 2, 24), axis=-1) / scales
            for method in REFRESH_METHODS:
                estimate = prediction_for(predictions, view, pi, method)
                error = (native - estimate).reshape(4, 128, 2, 24) / scales[..., None]
                output[prefix + '.error.' + method.lower()] = error
                output[prefix + '.error_norm.' + method.lower()] = np.linalg.norm(error, axis=-1)
            for method in ('FACTOR', 'INPUT_KRYLOV48', 'INPUT_KRYLOV48_REFRESH32'):
                full = prediction_for(predictions, view, pi, 'FULL_REFRESH32' if method.endswith('_REFRESH32') else 'FULL')
                estimate = prediction_for(predictions, view, pi, method)
                terms = np.stack((native - hold, hold - full, full - estimate)).reshape(3, 4, 128, 2, 24) / scales[None, ..., None]
                squares = np.sum(terms * terms, axis=-1)
                crosses = np.stack([2 * np.sum(terms[left] * terms[right], axis=-1) for left, right in ((0, 1), (0, 2), (1, 2))])
                output[prefix + '.signed.' + method.lower()] = terms
                output[prefix + '.squares.' + method.lower()] = squares
                output[prefix + '.cross.' + method.lower()] = crosses
                # Reuse the accepted signed accounting owner at both decision endpoints.
                for ai in range(4):
                    for tick in (64, 128):
                        for block in range(2):
                            sl = slice(block * 24, (block + 1) * 24)
                            cell = signed_cell(native[ai, tick - 1, sl], hold[ai, tick - 1, sl],
                                full[ai, tick - 1, sl], estimate[ai, tick - 1, sl], scale=scales[ai, tick - 1, block])
                            if cell['status'] != 'AVAILABLE':
                                raise MechanismUnavailable('SCI01_SIGNED_ACCOUNTING_IDENTITY_FAILED')
    if any(not np.isfinite(array).all() for array in output.values()):
        raise MechanismUnavailable('NONFINITE_SCI01_RETAINED_ARRAY')
    if observe_cost is not None:
        observe_cost({'phase': 'evaluation', 'wall_seconds': perf_counter() - start,
                      'cpu_seconds': process_time() - cpu})
    return output


def refresh_case_summary(arrays, *, numerical_usable):
    """Complete origin-cumulative decisions, with separate all-tick diagnostics."""
    checks = np.asarray(DENSE_RESPONSE_HORIZONS) - 1
    methods = {}
    for method in REFRESH_METHODS:
        curves = []
        all_ticks = []
        for view in ('primary', 'fine'):
            norms = np.stack([arrays[f'{view}.p{pi}.error_norm.{method.lower()}'] for pi in range(2)])
            point = norms.max(axis=(0, 1, 3))
            curves.append(np.maximum.accumulate(point[checks]))
            all_ticks.append(np.maximum.accumulate(point))
        row = {'primary_curve': curves[0].tolist(), 'fine_curve': curves[1].tolist()}
        for horizon in (32, 64, 128):
            index = DENSE_RESPONSE_HORIZONS.index(horizon)
            values = tuple(float(curve[index]) for curve in curves)
            discrepancy = float(np.max(np.abs(curves[0][:index + 1] - curves[1][:index + 1])))
            paired = numerical_usable and discrepancy <= float(REFRESH_RULE.paired_view_tolerance)
            row['H' + str(horizon)] = {'errors': values,
                'paired_view_discrepancy': discrepancy, 'numerically_usable': paired,
                'adequate': None if not paired else max(values) <= float(REFRESH_RULE.actuator_error_tolerance),
                'all_tick_errors': tuple(float(curve[horizon - 1]) for curve in all_ticks)}
        methods[method] = row
    f, k, rf, rk = (methods[name]['H64']['adequate'] for name in (
        'FULL', 'INPUT_KRYLOV48', 'FULL_REFRESH32', 'INPUT_KRYLOV48_REFRESH32'))
    decision = ('FROZEN_RESPONSE' if f and k else
        'NUMERICALLY_UNEVALUABLE' if any(value is None for value in (rf, rk)) else 'ONE_REFRESH' if rf and rk else
        'INADEQUATE_RETENTION' if rf else 'CANCELLATION_REQUIRES_ASSESSMENT' if rk else 'REFERENCE_CALCULATION')
    return {'status': 'CALCULATED_RETAINED_DEVELOPMENT_PENDING_INDEPENDENT_READ', 'methods': methods, 'H64_method_decision': decision,
        'weak_channel_adequacy': 'NO_SEPARATE_SIGNAL_RELATIVE_TOLERANCE_SELECTED',
        'new_native_acquisition': 0, 'new_statistical_fits': 0}


def refresh_work_counts():
    """Counts per usable case, separating paid information from study reuse."""
    return {
        'study': {'origin_operators_reused': 2, 'origin_eigensystems_reused': 2, 'input_krylov_bases': 2,
            'checkpoint_observations_consumed': 4, 'refresh_operators_constructed': 4,
            'source_hessian_vector_products_for_refresh': 4 * 96,
            'model_native_steps_four_actions_each': (128 + 256) * 7,
            'model_hessian_action_columns': (128 + 256) * 7 * 4 * 2,
            'revealed_hold_tangent_steps_four_actions_each': 2 * (128 + 256),
            'revealed_hold_source_hessian_action_columns': 2 * (128 + 256) * 4 * 2,
            'new_native_acquisition': 0, 'new_statistical_fits': 0},
        'prospective_one_primary_panel': {
            'shared_origin_observation_required': 1, 'origin_operator_work': '96_SOURCE_HVP_IF_NOT_ALREADY_AVAILABLE',
            'INPUT_KRYLOV48_basis_required': 1, 'refresh_observation_required': 1,
            'refresh_operator_work_as_implemented': '96_SOURCE_HVP_SHARED_BY_FULL_AND_REDUCED_CONTROLS',
            'baseline_prefix_if_not_legitimately_available': {'native_steps': 32, 'gradient_calls': 'MUST_BE_CHARGED_BY_NATIVE_OWNER'},
            'refresh_changes_prediction_steps': (33, 128), 'extra_refreshes_at_H128': 0,
            'native_reference_cost': 'ORIGINAL_COST_WHERE_MEASURED_OTHERWISE_UNKNOWN',
            'finite_reuse_cost_rule': 'SETUP_PLUS_N_TIMES_PROPAGATION_OBSERVATION_PREFIX_UPDATE_AND_REQUIRED_FALLBACK',
            'cost_saving_claim': 'NONE_FROM_MATRIX_OPERATION_COUNTS_ALONE'},
    }
