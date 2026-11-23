# SPDX-License-Identifier: MPL-2.0
"""Physical acquisitions for the model-free matrix programme.

The unit-mass six-Hermitian-matrix generator is the existing native generator.
This module owns no files, clocks other than the declared physical clock, or
execution authority. Random streams are separated by root and scientific use.
"""
from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import json
import math
import numpy as np

from empirical_lawhood.domains.matrix.classical_series import science as classical
from empirical_lawhood.domains.matrix.six_matrix_response.gradients import analytic_gradient_terms, optimized_action_terms
from empirical_lawhood.domains.matrix.six_matrix_response.model import SixMatrixState, hermitian_part, ideal_state
from empirical_lawhood.domains.matrix.six_matrix_response.parameter_derivatives import parameters, hessian_image, scheduled_force_step, tangent_step
from empirical_lawhood.domains.matrix.six_matrix_response.parameter_history import initial_parameter_state, split_parameter_innovations
from empirical_lawhood.domains.matrix.six_matrix_response.preparation_differential import NativeStateDifferential
from empirical_lawhood.domains.matrix.six_matrix_response.simulation import BAOABGradientCache, hermitian_noise
from empirical_lawhood.domains.matrix.matrix_factor_response.science import native_position_coordinates, native_position_lift
from empirical_lawhood.methods.protocol_work import ProtocolWorkAccount

WORK_CONVENTION = 'PARAMETER_JUMP_AFTER_SECOND_A_BEFORE_FINAL_B'


def protocol_work_account():
    return ProtocolWorkAccount('native-potential-energy', WORK_CONVENTION)


def _potential(position, selected):
    return optimized_action_terms(position, selected).total


class NativeResponseFailure(FloatingPointError):
    """A failed future with its actual completed computational/work prefix."""
    def __init__(self, error, partial_accounting):
        super().__init__(type(error).__name__ + ': ' + str(error))
        self.partial_accounting = partial_accounting


def rng(seed, purpose, index=0):
    return np.random.Generator(np.random.PCG64DXSM(np.random.SeedSequence([seed, purpose, index])))


def checkpoint(state):
    result = {'positions': native_position_coordinates(state.positions).tolist(),
              'momenta': native_position_coordinates(state.momenta).tolist(),
              'positions_real': state.positions.real.tolist(), 'positions_imag': state.positions.imag.tolist(),
              'momenta_real': state.momenta.real.tolist(), 'momenta_imag': state.momenta.imag.tolist(),
              'step_index': int(state.step_index), 'alpha_x': state.alpha_tilde_x,
              'alpha_y': state.alpha_tilde_y, 'q': 2}
    result['sha256'] = sha256(json.dumps(result, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return result


def restore(value):
    copy = {key: val for key, val in value.items() if key != 'sha256'}
    if sha256(json.dumps(copy, sort_keys=True, separators=(',', ':')).encode()).hexdigest() != value['sha256']:
        raise ValueError('Native checkpoint digest mismatch')
    if value['q'] != 2 or type(value['step_index']) is not int:
        raise ValueError('Checkpoint changes native geometry or physical clock')
    state = SixMatrixState(2, np.asarray(value['positions_real']) + 1j * np.asarray(value['positions_imag']),
                          np.asarray(value['momenta_real']) + 1j * np.asarray(value['momenta_imag']), value['step_index'],
                          value['alpha_x'], value['alpha_y'])
    if (not state.finite or not np.array_equal(native_position_coordinates(state.positions), value['positions'])
            or not np.array_equal(native_position_coordinates(state.momenta), value['momenta'])):
        raise ValueError('Checkpoint physical state and coordinate views disagree')
    return state


def physical_chart(c, seed):
    return classical._instrument(c, seed)


def coordinate(c, row, family='joint-increasing'):
    return classical._coordinate(c, row, family)


def guard(state, c):
    classical._native_guard(state, c)


def step(state, coord, noise, *, force=None, amplitude=0., numerical=None, cache=None, couplings=None, protocol_work=None):
    view = coord.primary_view if numerical is None else numerical
    target = (float(coord.target_x), float(coord.target_y)) if couplings is None else couplings
    force = np.zeros((2, 3, 4, 4), dtype='<c16') if force is None else force
    advanced = scheduled_force_step(state, direction=force, amplitude=amplitude,
        member=coord.member, numerical_view=view, next_alpha_tilde_x=target[0],
        next_alpha_tilde_y=target[1], standardized_noise=noise, gradient_cache=cache)
    if protocol_work is not None and (state.alpha_tilde_x, state.alpha_tilde_y) != tuple(target):
        # The actual BAOAB map uses the previous force for its first B kick.
        # It changes parameters at the new position after A-O-A, before the
        # final B kick. This is not a jump at the incoming configuration.
        protocol_work.record_jump(_potential, advanced.positions,
            parameters(state, coord.member), parameters(advanced, coord.member))
    return advanced


def target_state(c, row):
    coord = coordinate(c, row)
    return coord, ideal_state(q=2, alpha_tilde_x=float(c['target_x']),
                             alpha_tilde_y=float(c['target_y']), constitution='11')


def formation(c, row, recipe, seed, policy, *, yoked_tick=None, reviewed=False,
              retain_incoming_state=False):
    """Observe a causal persistence landmark and a common fixed-time landmark.

    Persistence is explicitly on the declared observation grid; no assertion
    about unobserved sub-stride survival is made. All recipes use the same noise.
    """
    matched = recipe.endswith('-exposure-matched')
    family = 'joint-increasing' if matched else ('joint-decreasing' if recipe == 'baseline' else recipe)
    coord = coordinate(c, row, family)
    state = initial_parameter_state(coord)
    stream = rng(seed, 110)
    cache = BAOABGradientCache()
    end = max(policy['fixed_tick'], policy['trigger_deadline'])
    observations, saved, exposure = [], {}, np.zeros(2)
    work = protocol_work_account()
    streak_start, first, previous, reentries = None, None, False, 0
    completed_ticks, failure = 0, None
    incoming_state = None
    try:
        for tick in range(end + 1):
            if tick % policy['observation_stride'] == 0 or tick in (end, policy['fixed_tick'], yoked_tick):
                measured = classical._factor_measure(state.positions, c)
                admitted = all(measured[k]['raw_admitted'] is True for k in policy['required_sectors'])
                if admitted:
                    earlier_admission = first is not None
                    if first is None:
                        first = tick
                    if not previous:
                        streak_start = tick
                        reentries += int(earlier_admission if reviewed else bool(observations))
                else:
                    streak_start = None
                observations.append({'tick': tick, 'present': admitted, 'factors': measured})
                if (admitted and streak_start is not None and tick - streak_start >= policy['trailing_ticks']
                        and tick <= policy['trigger_deadline'] and 'triggered' not in saved):
                    saved['triggered'] = {'tick': tick, 'state': checkpoint(state), 'present': True,
                                          'protocol_work_prefix': work.summary(),
                                          'trailing_start': streak_start}
                previous = admitted
                if tick == yoked_tick:
                    saved['yoked'] = {'tick': tick, 'state': checkpoint(state), 'present': admitted,
                                      'protocol_work_prefix': work.summary()}
            if tick == policy['fixed_tick']:
                measured = classical._factor_measure(state.positions, c)
                saved['fixed'] = {'tick': tick, 'state': checkpoint(state), 'protocol_work_prefix': work.summary(),
                                 'present': all(measured[k]['raw_admitted'] is True for k in policy['required_sectors'])}
            if reviewed:
                for handoff in saved.values():
                    if handoff['tick'] == tick:
                        handoff['preparation_force_calls'] = cache.completed_evaluations
                        handoff['coupling_exposure_prefix'] = exposure.tolist()
                        handoff['identifiable'] = all(measured[k]['raw_admitted'] is not None for k in policy['required_sectors'])
                        if retain_incoming_state:
                            handoff['incoming_state'] = None if incoming_state is None else checkpoint(incoming_state)
            if tick < end:
                if matched:
                    fraction = min(tick + 1, c['ramp_ticks']) / c['ramp_ticks']
                    deviation = float(policy['exposure_match_amplitude']) * math.sin(2 * math.pi * fraction)
                    sign = 1 if recipe.startswith('x-first') else -1
                    target = (float(c['target_x']) * (fraction + sign * deviation),
                              float(c['target_y']) * (fraction - sign * deviation))
                else:
                    target = coord.couplings(min(tick + 1, coord.total_ticks))
                exposure += np.asarray(target) * float(c['timestep'])
                if retain_incoming_state:
                    incoming_state = state
                state = step(state, coord, hermitian_noise(rng=stream, q=2), cache=cache, couplings=target, protocol_work=work)
                completed_ticks += 1
                guard(state, c)
    except (FloatingPointError, np.linalg.LinAlgError, OverflowError) as error:
        failure = type(error).__name__ + ': ' + str(error)
    for label in ('fixed', 'triggered'):
        if label not in saved:
            saved[label] = {'tick': None, 'state': None, 'present': False,
                'status': 'UNAVAILABLE' if failure else 'NOT_ENTERED',
                'reason': 'PREPARATION_FAILED' if failure else 'NO_TRAILING_ADMISSION_BEFORE_DEADLINE'}
    return {'recipe': recipe, 'coordinate': row, 'checkpoints': saved,
            'observations': observations, 'first_observed_admission': first,
            'initial_presence': observations[0]['present'] if observations else None,
            'origin_scope': 'OBSERVED_LANDMARK_NOT_PHYSICAL_FIRST_ORIGIN',
            'loss_observations': sum(not x['present'] for x in observations), 'reentries': reentries,
            'coupling_exposure': exposure.tolist(),
            'preparation_force_evaluations': cache.completed_evaluations,
            'preparation_force_evaluations_attempted': cache.evaluation_attempts,
            'preparation_completed_ticks': completed_ticks,
            'protocol_work': work.summary(complete=failure is None),
            'service_protocol': 'TERMINAL_COUPLING_AT_PHYSICAL_HANDOFF' if reviewed else policy['service_protocol'],
            'schedule_scope': 'EQUAL_INTEGRATED_SECTOR_EXPOSURE_EARLY_RAMP_ORDER' if matched else 'ORIGINAL_FOUR_FAMILY_SCHEDULE',
            'waiting_ticks': saved['triggered']['tick'] if saved['triggered']['tick'] is not None else policy['trigger_deadline'],
            'status': 'COMPLETED' if failure is None else 'UNAVAILABLE', 'failure': failure}


def action_at(state, member):
    selected = parameters(state, member)
    def action(columns):
        values = np.asarray(columns)
        one = values.ndim == 1
        if one:
            values = values[:, None]
        def measured_image(vector):
            action.real_hessian_attempts += 1
            image = native_position_coordinates(hessian_image(state.positions, native_position_lift(vector), selected))
            action.real_hessian_evaluations += 1
            return image
        real = np.column_stack([measured_image(v.real) for v in values.T])
        if np.iscomplexobj(values) and np.any(values.imag):
            imag = np.column_stack([measured_image(v.imag) for v in values.T])
            result = real + 1j * imag
        else:
            result = real
        return result[:, 0] if one else result
    action.real_hessian_evaluations = 0
    action.real_hessian_attempts = 0
    return action


def structural_seed(state):
    raw = classical.algebra.sector(state.positions[1])
    if not raw['identifiable']:
        return None
    axes = np.concatenate((np.eye(4, dtype='<c16')[None] / 2, raw['factor']))
    return classical._block_modes(axes)


def conjugation_chart(unitary):
    """Real orthogonal coordinates for simultaneous physical conjugation."""
    columns = []
    for vector in np.eye(96):
        matrix = native_position_lift(vector)
        columns.append(native_position_coordinates(unitary @ matrix @ unitary.conj().T))
    return np.column_stack(columns)


def port_controls(c, row, state, forces, receivers, seed, *, budget, tolerance, imaginary):
    from empirical_lawhood.methods.model_free_response import incremental_receiver_certificate
    from empirical_lawhood.domains.matrix.six_matrix_response.model import conjugate_state
    coord = coordinate(c, row)
    action = action_at(state, coord.member)
    transformed_action = None
    try:
        receiver = receivers[:24, :96].T
        structure = structural_seed(state)
        common_seed = np.column_stack((forces, receiver))
        u, singular, _ = np.linalg.svd(common_seed, full_matrices=False)
        q = u[:, :int(np.sum(singular > 1e-12 * singular[0]))]
        held = rng(seed, 131).normal(size=96)
        for _ in range(2):
            held -= q @ (q.T @ held)
        held /= np.linalg.norm(held)
        held_cert = incremental_receiver_certificate(action, held[:, None], receiver, complex(0, imaginary),
            tolerance=tolerance, max_actions=budget, seed_basis=common_seed)
        swap = np.eye(4)[[0, 2, 1, 3]]
        swapped = conjugation_chart(swap) @ forces
        swap_seed = forces if structure is None else structure
        swap_cert = incremental_receiver_certificate(action, swapped, receiver, complex(0, imaginary),
            tolerance=tolerance, max_actions=budget, seed_basis=swap_seed)
        random = rng(seed, 132)
        unitary, _ = np.linalg.qr(random.normal(size=(4, 4)) + 1j * random.normal(size=(4, 4)))
        orthogonal = conjugation_chart(unitary)
        changed = conjugate_state(state, unitary)
        transformed_action = action_at(changed, coord.member)
        original_image = action(forces)
        changed_image = transformed_action(orthogonal @ forces)
        gauge_residual = float(np.linalg.norm(changed_image - orthogonal @ original_image))
        return {'held_out': {'certificate': held_cert, 'initial_seed_defect': float(np.linalg.norm(held - q @ (q.T @ held))),
                            'declared_input': held.tolist(), 'scope': 'NEW_PHYSICAL_INPUT_NOT_IN_INITIAL_SEED'},
                'swapped_port': {'certificate': swap_cert, 'scope': 'SWAPPED_PHYSICAL_FORCE_FIXED_ORIGINAL_RECEIVER'},
                'gauge': {'native_action_covariance_residual': gauge_residual,
                    'coordinate_orthogonality_error': float(np.linalg.norm(orthogonal.T @ orthogonal - np.eye(96))),
                    'scope': 'SIMULTANEOUS_STATE_OPERATOR_INPUT_RECEIVER_CONJUGATION'},
                'native_real_hessian_evaluations': action.real_hessian_evaluations + transformed_action.real_hessian_evaluations}
    except (FloatingPointError, np.linalg.LinAlgError, OverflowError) as error:
        raise NativeResponseFailure(error, {
            'native_hessian_actions': action.real_hessian_evaluations + (0 if transformed_action is None else transformed_action.real_hessian_evaluations),
            'native_hessian_actions_attempted': action.real_hessian_attempts + (0 if transformed_action is None else transformed_action.real_hessian_attempts),
            'counts_are_lower_bounds': True,
        }) from error


def paired_response(c, row, origin, forces, receivers, seed, panel, *, refinement=1,
                    amplitude_scale=1., checkpoints=(), collect_survival=False, required_sectors=('Y',),
                    origin_clock_multiplier=1, synchronous_quench=False, forced_survival=False, compute_tangent=True):
    """Fresh common-noise +/-/HOLD futures, plus exact native tangent.

    Refinements 1/2/4 condition OU innovations, retaining identical physical
    pulse times. Tangents are evaluator-only realized-path objects.
    """
    if refinement not in (1, 2, 4):
        raise ValueError('Native response refinement must be 1, 2 or 4')
    coord = coordinate(c, row)
    view = replace(coord.primary_view, timestep=coord.primary_view.timestep / refinement)
    if (origin_clock_multiplier not in (1, 2, 4) or origin.step_index * refinement % origin_clock_multiplier):
        raise ValueError('Handoff and native refinement must share an exact physical clock')
    start = replace(origin, step_index=origin.step_index * refinement // origin_clock_multiplier)
    count = forces.shape[1]
    states = [start for _ in range(2 * count + 1)]
    caches = [BAOABGradientCache() for _ in states]
    work_accounts = [protocol_work_account() for _ in states]
    if synchronous_quench:
        terminal = replace(start, alpha_tilde_x=float(coord.target_x), alpha_tilde_y=float(coord.target_y))
        if (start.alpha_tilde_x, start.alpha_tilde_y) != (terminal.alpha_tilde_x, terminal.alpha_tilde_y):
            for work in work_accounts:
                work.record_jump(_potential, start.positions, parameters(start, coord.member), parameters(terminal, coord.member))
        states = [terminal for _ in states]
    directions = [native_position_lift(forces[:, index]) for index in range(count)]
    zero = np.zeros((2, 3, 4, 4), dtype='<c16')
    tangents = [NativeStateDifferential(zero, zero) for _ in range(count)]
    horizon = c['horizon_ticks']
    odd = np.zeros((count, horizon + 1, receivers.shape[0]))
    even = np.zeros_like(odd)
    tangent = np.zeros_like(odd)
    hold_states, survival, signed_phases = {}, [], {}
    coarse, bridge, quarter = rng(seed, 120, panel), rng(seed, 121, panel), rng(seed, 122, panel)
    tangent_actions_completed = 0
    try:
        for tick in range(horizon):
            noise = hermitian_noise(rng=coarse, q=2)
            aux = hermitian_noise(rng=bridge, q=2)
            halves = split_parameter_innovations(coord, noise, aux)
            if refinement == 1:
                noises = (noise,)
            elif refinement == 2:
                noises = halves
            else:
                from empirical_lawhood.domains.matrix.six_matrix_response.shooting import brownian_bridge_split
                decay = math.exp(-float(row['friction']) * float(c['timestep']) / 4)
                noises = tuple(v for half in halves for v in brownian_bridge_split(coarse_noise=half,
                    bridge_noise=hermitian_noise(rng=quarter, q=2), half_decay=decay))
            amplitude = float(c['amplitude']) * amplitude_scale if tick < c['pulse_ticks'] else 0.
            for innovation in noises:
                old_hold = states[-1]
                for index, state in enumerate(states):
                    action_index = min(index // 2, count - 1)
                    a = amplitude * (1 if index % 2 == 0 else -1) if index < 2 * count else 0.
                    states[index] = step(state, coord, innovation, numerical=view,
                        force=directions[action_index] if count else zero, amplitude=a, cache=caches[index],
                        protocol_work=work_accounts[index])
                    guard(states[index], c)
                for index, delta in enumerate(tangents if compute_tangent else ()):
                    tangents[index] = tangent_step(old_hold, states[-1], delta, direction=directions[index],
                        force_derivative=amplitude, member=coord.member, numerical_view=view)
                    tangent_actions_completed += 2
            hold_phase = np.concatenate((native_position_coordinates(states[-1].positions), native_position_coordinates(states[-1].momenta)))
            phase_chords = []
            for index in range(count):
                phases = [np.concatenate((native_position_coordinates(s.positions), native_position_coordinates(s.momenta)))
                          for s in states[2 * index:2 * index + 2]]
                odd[index, tick + 1] = receivers @ ((phases[0] - phases[1]) / 2)
                phase_chords.append((phases[0] - phases[1]) / 2)
                even[index, tick + 1] = receivers @ ((phases[0] + phases[1]) / 2 - hold_phase)
                delta = tangents[index]
                tangent[index, tick + 1] = receivers @ np.concatenate((native_position_coordinates(delta.positions), native_position_coordinates(delta.momenta)))
            if tick + 1 in checkpoints:
                hold_states[str(tick + 1)] = checkpoint(states[-1])
            if tick + 1 in checkpoints or tick + 1 == horizon:
                signed_phases[str(tick + 1)] = np.asarray(phase_chords).tolist()
            if collect_survival and ((tick + 1) % c['observation_stride'] == 0 or tick + 1 == horizon):
                measured = classical._factor_measure(states[-1].positions, c)
                survival.append({'tick': tick + 1, 'present': all(measured[k]['raw_admitted'] is True for k in required_sectors)})
                if forced_survival:
                    survival[-1]['branches'] = [
                        [observed[k]['raw_admitted'] for k in required_sectors]
                        for observed in (classical._factor_measure(state.positions, c) for state in states)]
    except (FloatingPointError, np.linalg.LinAlgError, OverflowError) as error:
        raise NativeResponseFailure(error, {
            'native_force_evaluations': sum(cache.completed_evaluations for cache in caches),
            'native_force_evaluations_attempted': sum(cache.evaluation_attempts for cache in caches),
            'native_hessian_actions': tangent_actions_completed,
            'native_energy_evaluations': sum(work.potential_evaluations_completed for work in work_accounts),
            'protocol_handoff_work': [work.summary(complete=False) for work in work_accounts],
            'counts_are_lower_bounds': True,
        }) from error
    return {'odd_response': odd.tolist(), 'even_response': even.tolist(),
            'native_tangent': tangent.tolist() if compute_tangent else None,
            'hold_checkpoints': hold_states, 'signed_phase_checkpoints': signed_phases, 'survival': survival,
            'force_evaluations': sum(cache.completed_evaluations for cache in caches),
            'protocol_handoff_work': {'per_path': [work.summary() for work in work_accounts],
                'path_order': ['action.' + str(i) + '.' + sign for i in range(count) for sign in ('plus', 'minus')] + ['hold'],
                'service_protocol': ('TERMINAL_COUPLING_AT_PHYSICAL_HANDOFF' if synchronous_quench
                                     else 'TERMINAL_COUPLING_AT_FIRST_SERVICE_FINAL_KICK'),
                'physical_scope': 'SEPARATE_SERVICE_PATHS; DO_NOT_SUM_AS_ONE_PHYSICAL_TRAJECTORY',
                'potential_evaluations': sum(work.potential_evaluations_completed for work in work_accounts)},
            'tangent_hessian_actions': tangent_actions_completed,
            'refinement': refinement, 'amplitude_scale': amplitude_scale,
            'scope': 'PAIRED_NATIVE_FINITE_CHORD_AND_REALIZED_PATH_TANGENT',
            'future_noise_rule': 'ROOT_PANEL_OU_WEIGHTED_NESTING', 'physical_horizon': horizon * float(c['timestep'])}


def memory_record(c, row, seed, config):
    coord, state = target_state(c, row)
    stream = rng(seed, 200)
    cache = BAOABGradientCache()
    caches = [cache]
    forces, _ = physical_chart(c, config['observation_seed'])
    observation = forces[:, 0]
    data, energies, saved, reset_results = [], [], [], []
    total = config['burnin_ticks'] + config['record_ticks']
    observed_forces = observed_attempts = energy_count = energy_attempts = completed_ticks = 0
    stage, pending_observation = 'OBSERVATION_RECORD', None

    def prefix():
        return {'coordinate': row, 'observables': data, 'energies': energies, 'checkpoints': saved,
            'momentum_reset_controls': reset_results, 'physical_timestep': float(c['timestep']) * config['stride'],
            'scope': 'CONSTANT_CONTROL_FINITE_AGE_ROOT_POPULATION', 'stationarity_established': False,
            'observation': {'q': 'fixed physical force coordinate', 'velocity': 'unit kinetic mass',
                'force': 'negative native complete conservative gradient projection',
                'direction': observation.tolist(), 'chart_seed': config['observation_seed']},
            'completed_scientific_prefix': {'completed_record_ticks': completed_ticks,
                'requested_record_ticks': total, 'complete_observations': len(data),
                'completed_reset_controls': sum(value['status'] == 'COMPLETED' for value in reset_results),
                'requested_reset_controls': len(config['checkpoint_ticks']), 'stage': stage},
            'incomplete_observation': pending_observation}

    def accounting():
        return {'native_force_evaluations': sum(value.completed_evaluations for value in caches) + observed_forces,
            'native_force_attempts': sum(value.evaluation_attempts for value in caches) + observed_attempts,
            'native_energy_evaluations': energy_count, 'native_energy_attempts': energy_attempts}

    try:
        for tick in range(total + 1):
            if tick >= config['burnin_ticks'] and (tick - config['burnin_ticks']) % config['stride'] == 0:
                q = native_position_coordinates(state.positions)
                p = native_position_coordinates(state.momenta)
                observed_attempts += 1
                g = analytic_gradient_terms(state.positions, parameters(state, coord.member)).total
                observed_forces += 1
                measured = [float(observation @ q), float(observation @ p), -float(observation @ native_position_coordinates(g))]
                if not np.all(np.isfinite(measured)):
                    raise FloatingPointError('Nonfinite native memory observation')
                pending_observation = {'age_tick': tick, 'observables': measured, 'energy_available': False}
                energy_attempts += 1
                energy = float(optimized_action_terms(state.positions, parameters(state, coord.member)).total + .5 * (p @ p))
                energy_count += 1
                if not math.isfinite(energy):
                    raise FloatingPointError('Nonfinite native memory energy')
                data.append(measured)
                energies.append(energy)
                pending_observation = None
                if tick - config['burnin_ticks'] in config['checkpoint_ticks']:
                    saved.append({'age_tick': tick, 'state': checkpoint(state)})
            if tick < total:
                state = step(state, coord, hermitian_noise(rng=stream, q=2), cache=cache)
                guard(state, c)
                completed_ticks = tick + 1
        # Each intervention branch owns its exact force cache; the same future
        # noise and physical map are retained. In-flight caches retain costs.
        stage = 'MOMENTUM_RESET_CONTROLS'
        for saved_index, saved_row in enumerate(saved):
            original = restore(saved_row['state'])
            reset = replace(original, momenta=math.sqrt(float(row['temperature'])) * hermitian_noise(rng=rng(seed, 202, saved_index), q=2))
            pair = [original, reset, restore(saved_row['state'])]
            branch_caches = [BAOABGradientCache() for _ in pair]
            caches.extend(branch_caches)
            future = rng(seed, 203, saved_index)
            samples = [[], [], []]
            reset_record = {'age_tick': saved_row['age_tick'], 'original': samples[0], 'momentum_reset': samples[1],
                'full_state_clone': samples[2], 'completed_ticks_by_path': [0, 0, 0],
                'status': 'PARTIAL', 'full_state_clone_max_abs_difference': None,
                'scope': 'PHYSICAL_MOMENTUM_INTERVENTION_AND_IDENTICAL_FULL_STATE_MARKOV_NULL'}
            reset_results.append(reset_record)
            for tick in range(config['reset_horizon_ticks'] + 1):
                for index, current in enumerate(pair):
                    samples[index].append(float(observation @ native_position_coordinates(current.positions)))
                if tick < config['reset_horizon_ticks']:
                    noise = hermitian_noise(rng=future, q=2)
                    for index, current in enumerate(pair):
                        pair[index] = step(current, coord, noise, cache=branch_caches[index])
                        guard(pair[index], c)
                        reset_record['completed_ticks_by_path'][index] = tick + 1
            reset_record.update(status='COMPLETED',
                full_state_clone_max_abs_difference=float(np.max(np.abs(np.asarray(samples[0]) - samples[2]))))
    except (FloatingPointError, np.linalg.LinAlgError, OverflowError) as error:
        failure = NativeResponseFailure(error, {**accounting(), 'counts_are_lower_bounds': True})
        failure.partial_record = prefix()
        raise failure from error
    stage = 'COMPLETED'
    return {**prefix(), **accounting(), 'status': 'COMPLETED'}


def restrained_step(state, coord, noise, direction, center, stiffness, numerical=None, *, accounting=None):
    """BAOAB for the actual native potential plus k/2*(a.q-s)^2.

    The native kinetic convention is unit mass. No Gaussian reference force is
    substituted for the physical gradient.
    """
    view = coord.primary_view if numerical is None else numerical
    dt, gamma, temperature = float(view.timestep), float(view.friction_gamma), float(view.bath_temperature)
    selected = parameters(state, coord.member)
    a = native_position_lift(direction)
    def gradient(position):
        q = native_position_coordinates(position)
        if accounting is not None:
            accounting['native_force_evaluations_attempted'] += 1
        result = analytic_gradient_terms(position, selected).total
        if accounting is not None:
            accounting['native_force_evaluations'] += 1
        return result + stiffness * (float(direction @ q) - center) * a
    momentum = hermitian_part(state.momenta - .5 * dt * gradient(state.positions))
    position = hermitian_part(state.positions + .5 * dt * momentum)
    decay = math.exp(-gamma * dt)
    momentum = hermitian_part(decay * momentum + math.sqrt(temperature * (1 - decay * decay)) * noise)
    position = hermitian_part(position + .5 * dt * momentum)
    momentum = hermitian_part(momentum - .5 * dt * gradient(position))
    return replace(state, positions=position, momenta=momentum, step_index=state.step_index + 1)


def equilibrium_record(c, row, seed, config):
    coord, initial = target_state(c, row)
    force, _ = physical_chart(c, config['receiver_seed'])
    direction = force[:, 0]
    k, beta = float(config['stiffness']), 1 / float(row['temperature'])
    reference_precision = float(config['reference_precision'])
    records, importance, native_energies = [], [], []
    proposals = None
    current = None
    accounting = {'native_force_evaluations': 0, 'native_force_evaluations_attempted': 0,
        'native_energy_evaluations': 0, 'native_energy_evaluations_attempted': 0, 'native_hessian_actions': 0}
    stage = 'RESTRAINED_NATIVE_ENSEMBLES'
    try:
        for center_index, center in enumerate(config['centers']):
            center = float(center)
            state = initial
            stream = rng(seed, 300, center_index)
            samples, short, long, controlled, gradients = [], [], [], [], []
            current = {'center': center, 'samples': samples, 'sample_ticks': [], 'completed_ticks': 0,
                'status': 'PARTIAL'}
            force_start = accounting['native_force_evaluations']
            total = config['burnin_ticks'] + config['reference_ticks']
            for tick in range(total + 1):
                if tick >= config['burnin_ticks'] and (tick - config['burnin_ticks']) % config['stride'] == 0:
                    q = native_position_coordinates(state.positions)
                    value = float(direction @ q)
                    accounting['native_force_evaluations_attempted'] += 1
                    native_gradient = analytic_gradient_terms(state.positions, parameters(state, coord.member)).total
                    accounting['native_force_evaluations'] += 1
                    complete_gradient = native_position_coordinates(native_gradient)
                    complete_gradient += k * (value - center) * direction
                    score_control = value - float(direction @ complete_gradient) / reference_precision
                    measured = [value, -k * (value - center), score_control]
                    if not np.all(np.isfinite(measured)):
                        raise FloatingPointError('Nonfinite restrained native observation')
                    samples.append(measured)
                    current['sample_ticks'].append(tick)
                    long.append(value)
                    if tick - config['burnin_ticks'] <= config['sample_ticks']:
                        short.append(value)
                        controlled.append(score_control)
                        gradients.append(float(direction @ complete_gradient))
                if tick < total:
                    state = restrained_step(state, coord, hermitian_noise(rng=stream, q=2), direction, center, k,
                        accounting=accounting)
                    guard(state, c)
                    current['completed_ticks'] = tick + 1
            records.append({'center': center, 'samples': samples, 'mean': float(np.mean(short)),
                            'variance': float(np.var(short, ddof=1)), 'controlled_mean': float(np.mean(controlled)),
                            'gradient_mean': float(np.mean(gradients)), 'reference_mean': float(np.mean(long)),
                            'native_force_evaluations': accounting['native_force_evaluations'] - force_start,
                            'sample_count': len(short), 'reference_count': len(long), 'status': 'COMPLETED'})
            current = None
        # Full-dimensional Gaussian importance control preserves the native
        # residual. Retained marginal alone cannot absorb a transverse residual.
        stage = 'FULL_NATIVE_RESIDUAL_IMPORTANCE'
        from scipy.special import logsumexp
        from empirical_lawhood.methods.retained_gaussian_response import reduce_dense_reference
        q0 = native_position_coordinates(initial.positions)
        precision = reference_precision * np.eye(96)
        retained = reduce_dense_reference(precision, q0, direction[:, None], beta=beta)
        proposals = rng(seed, 305).normal(size=(config['importance_samples'], 96)) / math.sqrt(beta * reference_precision) + q0
        for q in proposals:
            accounting['native_energy_evaluations_attempted'] += 1
            value = float(optimized_action_terms(native_position_lift(q), parameters(initial, coord.member)).total)
            accounting['native_energy_evaluations'] += 1
            if not math.isfinite(value):
                raise FloatingPointError('Nonfinite native importance energy')
            native_energies.append(value)
        base = .5 * reference_precision * np.sum((proposals - q0) ** 2, axis=1)
        residual = np.asarray(native_energies) - base
        projected = proposals @ direction
        for center in config['centers']:
            weights = -beta * (residual + .5 * k * (projected - float(center)) ** 2)
            normalizer = float(logsumexp(weights))
            if not np.all(np.isfinite(weights)) or not math.isfinite(normalizer):
                raise FloatingPointError('Nonfinite native importance log weights')
            normalized = np.exp(weights - normalizer)
            importance.append({'center': float(center), 'mean': float(normalized @ projected),
                'log_normalization_ratio': normalizer - math.log(len(weights)),
                'effective_sample_size': float(1 / (normalized @ normalized)),
                'maximum_normalized_weight': float(np.max(normalized)),
                'scope': 'FULL_NATIVE_RESIDUAL_MONTE_CARLO_IMPORTANCE_ESTIMATE_NO_GLOBAL_ENCLOSURE'})
    except (FloatingPointError, np.linalg.LinAlgError, OverflowError) as error:
        failure = NativeResponseFailure(error, {**accounting, 'counts_are_lower_bounds': True})
        failure.partial_record = {'center_records': records, 'incomplete_center_record': current,
            'importance': importance, 'completed_importance_native_samples': [] if proposals is None else
                [{'position': q.tolist(), 'native_energy': value} for q, value in zip(proposals, native_energies)],
            'failed_stage': stage, 'canonical_preparation_qualified': False,
            'finite_step_measure_bias_bound': None, 'native_prefix_scope': 'INCOMPLETE_ASSIGNED_ROOT_NOT_AN_ESTIMATE'}
        raise failure from error
    return {'coordinate': row, 'center_records': records, 'importance': importance,
        'retained_compliance': retained.reference.compliance.tolist(),
        'reference_log_partition': float(48 * math.log(2 * math.pi / (beta * reference_precision))),
        'reference_precision': reference_precision, 'receiver_direction': direction.tolist(),
        'residual_scope': 'ALL_96_COORDINATES_AT_EVERY_IMPORTANCE_SAMPLE',
        'measure': 'exp[-beta*(native_potential+k/2*(a.q-s)^2)] dq dp',
        'canonical_preparation_qualified': False, 'finite_step_measure_bias_bound': None,
        'status': 'COMPLETED', 'scientific_disposition': 'FINITE_PREPARATION_ESTIMATE_CANONICAL_CLAIM_UNRESOLVED',
        **accounting, 'reference_shared_path': True}


def first_passage(c, row, seed, config, origin=None, history='declared-native-preparation'):
    coord, default = target_state(c, row)
    initial = default if origin is None else origin
    force, _ = physical_chart(c, config['receiver_seed'])
    direction = force[:, 0]
    # The target chart is fixed by the declared ideal target material, never
    # re-centered separately on each observed preparation outcome.
    reference = float(direction @ native_position_coordinates(default.positions))
    events = []
    for replica in range(config['replicas']):
        state, stream, cache = initial, rng(seed, 400, replica), BAOABGradientCache()
        work = protocol_work_account()
        event, event_time, crossings = None, None, 0
        previous_side = 0
        observed_until = 0.
        status = 'administrative_censor'
        try:
            for tick in range(config['horizon_ticks'] + 1):
                displacement = float(direction @ native_position_coordinates(state.positions)) - reference
                side = 1 if displacement >= float(config['upper_target']) else (-1 if displacement <= float(config['lower_target']) else 0)
                crossings += int(side != previous_side and side != 0)
                previous_side = side
                observed_until = tick * float(c['timestep'])
                if side and event is None:
                    event = 'target' if side == 1 else 'competing'
                    event_time = observed_until
                    status = 'event'
                if tick < config['horizon_ticks']:
                    state = step(state, coord, hermitian_noise(rng=stream, q=2), cache=cache, protocol_work=work)
                    guard(state, c)
        except (FloatingPointError, np.linalg.LinAlgError, OverflowError) as error:
            if event is None:
                status = 'failed'
            failure = str(error)
        else:
            failure = None
        events.append({'root_id': str(seed), 'replica': replica, 'status': status, 'event': event,
            'event_time': event_time, 'observed_until': observed_until, 'entry_history': history,
            'weight': 1 / config['replicas'], 'recrossings': max(0, crossings - 1),
            'recrossing_definition': 'TARGET_SET_ENTRIES_AFTER_FIRST_NOT_DIVIDING_SURFACE_CROSSINGS',
            'target_reference': reference, 'lower_target': reference + float(config['lower_target']),
            'upper_target': reference + float(config['upper_target']),
            'failure': failure, 'native_force_evaluations': cache.completed_evaluations,
            'native_force_evaluations_attempted': cache.evaluation_attempts,
            'protocol_handoff_work': work.summary(complete=failure is None),
            'native_energy_evaluations': work.potential_evaluations_completed})
    return events
