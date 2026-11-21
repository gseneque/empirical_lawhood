# SPDX-License-Identifier: MPL-2.0
"""Authored M0--M7 matrix acquisitions, independent readout and synthesis.

No TRAIN, FIT or CAL dependency is manufactured for a direct supplier. Native
acquisition and assessment remain separate, replayable public operations.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict
from hashlib import sha256
import json
import math
from time import perf_counter
import numpy as np

from empirical_lawhood.domains.matrix.classical_series import science as classical
from empirical_lawhood.domains.matrix.matrix_factor_response.origin_mechanics import discrete_baoab_maps
from . import native

MODULES = ('M0', 'M1', 'M2', 'M3', 'M4', 'M5', 'M6', 'M7')
DEFAULT_SETTINGS = {
    'native': {'history_ticks': 1280, 'handoff_tick': 1152,
        'coordinates': [{'id': 'nominal', 'temperature': '1', 'friction': '1', 'cross_coupling': '1'},
                        {'id': 'high-temperature', 'temperature': '2', 'friction': '1', 'cross_coupling': '1'}],
        'preparation_arms': ['baseline', 'joint-increasing', 'x-first', 'y-first'],
        'response_tolerance': '0.01', 'numerical_tolerance': '0.0001'},
    'formation': {'fixed_tick': 1152, 'trigger_deadline': 1152, 'trailing_ticks': 128,
        'observation_stride': 16, 'required_sectors': ['Y'], 'service_panels': 1,
        'probability_gain_margin': '0.1', 'continuous_loss_gain_margin': '0.0001',
        'minimum_signal': '0.000001', 'exposure_matched_recipes': [], 'exposure_match_amplitude': '0.1',
        'service_protocol': 'TERMINAL_COUPLING_AT_FIRST_SERVICE_FINAL_KICK',
        'work_convention': 'PARAMETER_JUMP_AFTER_SECOND_A_BEFORE_FINAL_B'},
    'memory': {'burnin_ticks': 4096, 'record_ticks': 16384, 'record_length_ladder': [16384, 65536, 131072],
        'observation_seed': 0,
        'stride': 1, 'lags': [1, 4, 16, 64, 256, 1024, 4096], 'history_orders': [1, 2],
        'observation_dimensions': [1, 2, 3], 'bin_edges': [[-10., 0., 10.], [-10., 0., 10.], [-100., 0., 100.]],
        'maximum_cells': 4096, 'minimum_support': 2, 'receiver_oscillation': '1', 'tolerance': '0.1',
        'binning_allowance': '0', 'tail_allowance': '0', 'checkpoint_ticks': [0, 8192, 16384],
        'reset_horizon_ticks': 128, 'protocol_age_ticks': [], 'optional_diagnostics': [],
        'segment_boundaries_samples': None, 'segment_transition_policy': 'within_segment'},
    'response': {'handoffs': ['fixed', 'triggered'], 'action_budgets': [24, 48],
        'equal_ranks': [24], 'methods': ['INPUT', 'JOINT', 'STRUCTURAL', 'STRUCTURAL_FORCE'],
        'resolvent_imaginary': '1', 'certificate_tolerance': '0.01',
        'refinements': [1, 2, 4], 'amplitude_scales': ['1', '0.5'],
        'refresh_schedules': [[], [32], [16, 32]], 'dense_oracle_seed_modulus': 8,
        'minimum_signal': '0.000001', 'port_controls': True, 'selection_tick': None},
    'transfer': {'source_coordinate_id': None, 'destination_coordinate_ids': [], 'probe_action_budget': None},
    'population': {'frame_size': 32, 'audit_size': 8, 'mode': 'reveal_all',
        'individual_halfwidth': '0.001', 'value_bounds': None, 'clip_bounds': None,
        'sampling_seed': 20261117, 'receiver_seed': 0, 'auxiliary_rank': 4,
        'auxiliary_failure_policy': 'ZERO_BEFORE_NATIVE_OUTCOMES'},
    'equilibrium': {'centers': ['-0.2', '-0.15', '-0.1', '-0.05', '0', '0.05', '0.1', '0.15', '0.2'],
        'receiver_seed': 0,
        'stiffness': '1', 'burnin_ticks': 4096, 'sample_ticks': 4096, 'reference_ticks': 16384,
        'stride': 4, 'importance_samples': 256, 'reference_precision': '8'},
    'events': {'horizon_ticks': 4096, 'replicas': 4, 'upper_target': '0.1', 'lower_target': '-0.1', 'receiver_seed': 0,
               'require_admitted_entry': True, 'history_pairs': None,
               'target_events': ['target', 'competing'], 'time_grid_ticks': None},
    'alpha': '0.05', 'evidence_scope': 'EXPOSED_DEVELOPMENT',
    'inference': {'module_alpha_weights': {module: '0.125' for module in MODULES}},
    'confirmation': None,
    'resources': {'memory_bytes': None, 'wall_time_seconds': None, 'output_bytes': None},
    'historical_operands': [], 'historical_comparison': 'NOT_CLAIMED_WITHOUT_AUTHENTICATED_OPERANDS',
}


def _positive(value, name, *, zero=False):
    if not isinstance(value, (str, int, float)) or isinstance(value, bool):
        raise TypeError(name + ' must be a finite scalar')
    result = float(value)
    if not math.isfinite(result) or result < 0 or (not zero and result == 0):
        raise ValueError(name + ' must be finite and ' + ('nonnegative' if zero else 'positive'))
    return result


def _integer(value, name, *, zero=False):
    if type(value) is not int or value < (0 if zero else 1):
        raise ValueError(name + ' requires an integer within its declared positive domain')


def normalise_settings(settings):
    if not isinstance(settings, dict) or set(settings) - set(DEFAULT_SETTINGS) - {'receiver_study'}:
        raise ValueError('Unknown model-free scientific settings')
    result = deepcopy(DEFAULT_SETTINGS)
    for key, value in settings.items():
        if key == 'receiver_study':
            continue
        if isinstance(result[key], dict):
            if not isinstance(value, dict):
                raise TypeError(key + ' settings must be an object')
            if key != 'native' and set(value) - set(result[key]):
                raise ValueError('Unknown ' + key + ' setting')
            result[key].update(deepcopy(value))
        else:
            result[key] = deepcopy(value)
    result['native'] = classical.normalise_config(result['native'])
    if not 0 < _positive(result['alpha'], 'alpha') < 1:
        raise ValueError('alpha must lie in (0,1)')
    if result['evidence_scope'] not in ('EXPOSED_DEVELOPMENT', 'FRESH_CONFIRMATION', 'EXPOSED_REANALYSIS'):
        raise ValueError('Explicit scientific exposure scope required')
    weights = result['inference']['module_alpha_weights']
    if not isinstance(weights, dict) or set(weights) != set(MODULES):
        raise ValueError('Allocate the complete M0-M7 inference family explicitly')
    if any(not 0 < _positive(v, 'module alpha weight') <= 1 for v in weights.values()) or math.fsum(float(v) for v in weights.values()) > 1 + 1e-15:
        raise ValueError('Positive module alpha weights must sum to at most one')
    if result['confirmation'] is not None:
        from .confirmation import ConfirmationSelection
        ConfirmationSelection.from_document(result['confirmation'])
    for key, value in result['resources'].items():
        if value is not None:
            _integer(value, 'resources.' + key)
    c, f, m, r, p, e, k = (result[name] for name in ('native', 'formation', 'memory', 'response', 'population', 'equilibrium', 'events'))
    if (f['service_protocol'] != 'TERMINAL_COUPLING_AT_FIRST_SERVICE_FINAL_KICK'
            or f['work_convention'] != 'PARAMETER_JUMP_AFTER_SECOND_A_BEFORE_FINAL_B'):
        raise ValueError('Select the implemented native split-step protocol and physical work convention')
    for key in ('fixed_tick', 'trigger_deadline', 'trailing_ticks', 'observation_stride', 'service_panels'):
        _integer(f[key], 'formation.' + key)
    if max(f['fixed_tick'], f['trigger_deadline']) > c['history_ticks'] or f['fixed_tick'] < c['ramp_ticks']:
        raise ValueError('Formation clocks must fit the declared native preparation')
    if f['trailing_ticks'] > f['trigger_deadline'] or f['trailing_ticks'] % f['observation_stride']:
        raise ValueError('Trailing persistence must fit deadline and observation clock')
    if not f['required_sectors'] or set(f['required_sectors']) - {'X', 'Y'}:
        raise ValueError('Declare actual factor sectors')
    if len(set(f['exposure_matched_recipes'])) != len(f['exposure_matched_recipes']) or set(f['exposure_matched_recipes']) - {'x-first-exposure-matched', 'y-first-exposure-matched'}:
        raise ValueError('Unknown or duplicated exposure-matched preparation')
    if not 0 < _positive(f['exposure_match_amplitude'], 'exposure matched amplitude') < 1 / (2 * math.pi):
        raise ValueError('Matched sinusoidal ramps must remain monotone')
    for key in ('probability_gain_margin', 'continuous_loss_gain_margin', 'minimum_signal'):
        _positive(f[key], 'formation.' + key)
    if float(f['probability_gain_margin']) > 1:
        raise ValueError('Probability gain has probability-difference units')
    for key in ('burnin_ticks', 'record_ticks', 'stride', 'maximum_cells', 'minimum_support', 'reset_horizon_ticks'):
        _integer(m[key], 'memory.' + key, zero=key == 'burnin_ticks')
    _integer(m['observation_seed'], 'memory.observation_seed', zero=True)
    _integer(e['receiver_seed'], 'equilibrium.receiver_seed', zero=True)
    _integer(k['receiver_seed'], 'events.receiver_seed', zero=True)
    ladder = m['record_length_ladder']
    if not isinstance(ladder, list) or sorted(set(ladder)) != ladder or m['record_ticks'] not in ladder:
        raise ValueError('Record length must be on the predeclared ordered acquisition ladder')
    for key in ('lags', 'history_orders', 'observation_dimensions'):
        if not m[key] or len(set(m[key])) != len(m[key]) or any(type(v) is not int or v < 1 for v in m[key]):
            raise ValueError('Invalid memory ' + key)
    if set(m['observation_dimensions']) - {1, 2, 3}:
        raise ValueError('Memory observation supports one to three declared coordinates')
    if max(m['lags']) * (1 + min(m['history_orders'])) >= m['record_ticks'] // m['stride'] + 1:
        raise ValueError('Smallest declared history has no complete anchor at maximum lag')
    if len(m['bin_edges']) != 3 or any(len(x) < 2 or any(not math.isfinite(float(v)) for v in x) or any(float(b) <= float(a) for a, b in zip(x, x[1:])) for x in m['bin_edges']):
        raise ValueError('Three finite ordered bin charts are required')
    for key in ('receiver_oscillation', 'tolerance', 'binning_allowance', 'tail_allowance'):
        _positive(m[key], 'memory.' + key, zero=key in ('binning_allowance', 'tail_allowance'))
    if m['record_ticks'] % m['stride'] or sorted(set(m['checkpoint_ticks'])) != m['checkpoint_ticks'] or any(type(v) is not int or not 0 <= v <= m['record_ticks'] or v % m['stride'] for v in m['checkpoint_ticks']):
        raise ValueError('Memory checkpoints outside selected record')
    if sorted(set(m['protocol_age_ticks'])) != m['protocol_age_ticks'] or any(type(v) is not int or not 0 <= v <= m['record_ticks'] or v % m['stride'] for v in m['protocol_age_ticks']):
        raise ValueError('Protocol-age memory anchors must lie on the declared observation clock')
    sample_count = m['record_ticks'] // m['stride'] + 1
    if m['segment_boundaries_samples'] is None:
        third, remainder = divmod(sample_count, 3)
        m['segment_boundaries_samples'] = [0, third + int(remainder > 0),
            2 * third + min(remainder, 2), sample_count]
    boundaries = m['segment_boundaries_samples']
    if (not isinstance(boundaries, list) or len(boundaries) < 3
            or any(type(v) is not int for v in boundaries)
            or boundaries != sorted(set(boundaries)) or boundaries[0] != 0 or boundaries[-1] != sample_count):
        raise ValueError('Memory segments must partition every observed sample exactly once')
    if m['segment_transition_policy'] != 'within_segment':
        raise ValueError('Segment diagnostics exclude boundary-spanning transitions explicitly')
    if len(set(m['optional_diagnostics'])) != len(m['optional_diagnostics']) or set(m['optional_diagnostics']) - {'compression', 'path_reversal'}:
        raise ValueError('Unknown optional model-free trajectory diagnostic')
    if not r['handoffs'] or set(r['handoffs']) - {'fixed', 'triggered'}:
        raise ValueError('Unknown response handoff')
    if not r['methods'] or set(r['methods']) - {'INPUT', 'JOINT', 'STRUCTURAL', 'STRUCTURAL_FORCE'}:
        raise ValueError('Unknown native response method')
    for key in ('action_budgets', 'equal_ranks'):
        if not r[key] or any(type(v) is not int or not 1 <= v <= 96 for v in r[key]):
            raise ValueError('Response budgets/ranks must fit 96 position dimensions')
    if 1 not in r['refinements'] or set(r['refinements']) - {1, 2, 4}:
        raise ValueError('Response refinement must include primary and supported OU nesting')
    if '1' not in r['amplitude_scales'] or any(not 0 < float(v) <= 1 for v in r['amplitude_scales']):
        raise ValueError('Response amplitudes must include original and bounded sensitivities')
    for schedule in r['refresh_schedules']:
        if sorted(set(schedule)) != schedule or any(type(v) is not int or not 0 < v < c['horizon_ticks'] for v in schedule):
            raise ValueError('Refresh schedules must be ordered physical response ticks')
    _integer(r['dense_oracle_seed_modulus'], 'dense oracle modulus')
    if type(r['port_controls']) is not bool:
        raise ValueError('Port controls selection must be explicit boolean')
    if r['selection_tick'] is None:
        r['selection_tick'] = min(32, c['horizon_ticks'] - 1)
    if type(r['selection_tick']) is not int or not 0 < r['selection_tick'] < c['horizon_ticks']:
        raise ValueError('Selector must leave a nonempty observed prefix and withheld suffix')
    for key in ('resolvent_imaginary', 'certificate_tolerance', 'minimum_signal'):
        _positive(r[key], 'response.' + key)
    transfer = result['transfer']
    coordinate_ids = [row['id'] for row in c['coordinates']]
    if transfer['source_coordinate_id'] is None:
        transfer['source_coordinate_id'] = coordinate_ids[0]
    if not transfer['destination_coordinate_ids']:
        transfer['destination_coordinate_ids'] = list(coordinate_ids)
    if transfer['source_coordinate_id'] not in coordinate_ids or set(transfer['destination_coordinate_ids']) - set(coordinate_ids) or len(set(transfer['destination_coordinate_ids'])) != len(transfer['destination_coordinate_ids']):
        raise ValueError('Transfer requires frozen source/destination native coordinates')
    if transfer['probe_action_budget'] is None:
        transfer['probe_action_budget'] = max(r['action_budgets'])
    _integer(transfer['probe_action_budget'], 'transfer.probe_action_budget')
    if transfer['probe_action_budget'] > 96:
        raise ValueError('Transfer probe budget exceeds physical position dimension')
    for key in ('frame_size', 'audit_size'):
        _integer(p[key], 'population.' + key)
    if not 2 <= p['audit_size'] <= p['frame_size'] or p['mode'] not in ('sparse', 'reveal_all'):
        raise ValueError('Finite frame requires 2..N audits and explicit acquisition mode')
    if p['auxiliary_failure_policy'] != 'ZERO_BEFORE_NATIVE_OUTCOMES':
        raise ValueError('The auxiliary failure fallback must be fixed before native outcomes')
    for name in ('sampling_seed', 'receiver_seed'):
        _integer(p[name], 'population.' + name, zero=True)
    _integer(p['auxiliary_rank'], 'population.auxiliary_rank')
    if p['auxiliary_rank'] > 96:
        raise ValueError('Auxiliary rank exceeds physical position dimension')
    if p['clip_bounds'] is not None:
        if len(p['clip_bounds']) != 2 or not all(math.isfinite(float(v)) for v in p['clip_bounds']) or not float(p['clip_bounds'][0]) < float(p['clip_bounds'][1]):
            raise ValueError('Clipped finite-frame receiver needs ordered bounds')
        p['value_bounds'] = deepcopy(p['clip_bounds'])
    elif p['value_bounds'] is not None:
        raise ValueError('Unbounded native momentum cannot claim a finite physical bound; select an explicit clipped receiver')
    _positive(p['individual_halfwidth'], 'individual halfwidth')
    centers = np.asarray(e['centers'], dtype=float)
    if centers.ndim != 1 or len(centers) < 5 or len(centers) % 2 != 1 or not np.isfinite(centers).all() or np.any(np.diff(centers) <= 0):
        raise ValueError('Equilibrium grid needs an odd nested ordered grid of at least five centers')
    for key in ('stiffness', 'reference_precision'):
        _positive(e[key], 'equilibrium.' + key)
    for key in ('burnin_ticks', 'sample_ticks', 'reference_ticks', 'stride', 'importance_samples'):
        _integer(e[key], 'equilibrium.' + key, zero=key == 'burnin_ticks')
    if e['reference_ticks'] < e['sample_ticks'] or e['sample_ticks'] // e['stride'] < 2 or e['reference_ticks'] % e['stride'] or e['sample_ticks'] % e['stride']:
        raise ValueError('Equilibrium reference and sample clocks inconsistent')
    for key in ('horizon_ticks', 'replicas'):
        _integer(k[key], 'events.' + key)
    if not all(math.isfinite(float(k[key])) for key in ('lower_target', 'upper_target')) or not float(k['lower_target']) < 0 < float(k['upper_target']):
        raise ValueError('Event targets must straddle the declared entry receiver')
    if type(k['require_admitted_entry']) is not bool:
        raise ValueError('Event entry admission selection must be explicit boolean')
    recipes = c['preparation_arms'] + f['exposure_matched_recipes']
    if k['history_pairs'] is None:
        k['history_pairs'] = [['baseline', recipe] for recipe in recipes if recipe != 'baseline'] if 'baseline' in recipes else []
    pairs = k['history_pairs']
    if (not isinstance(pairs, list) or any(not isinstance(pair, list) or len(pair) != 2
            or pair[0] == pair[1] or any(history not in recipes for history in pair) for pair in pairs)
            or len({tuple(pair) for pair in pairs}) != len(pairs)):
        raise ValueError('Event history pairs require unique ordered pairs of declared preparation recipes')
    if (not isinstance(k['target_events'], list) or not k['target_events']
            or len(set(k['target_events'])) != len(k['target_events'])
            or set(k['target_events']) - {'target', 'competing'}):
        raise ValueError('Select the native competing-event labels explicitly')
    if k['time_grid_ticks'] is None:
        k['time_grid_ticks'] = [k['horizon_ticks'] * j / 16 for j in range(17)]
    grid = k['time_grid_ticks']
    if (not isinstance(grid, list) or len(grid) < 2
            or any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in grid)
            or grid != sorted(set(grid)) or grid[0] != 0 or grid[-1] != k['horizon_ticks']):
        raise ValueError('Event grid must cover the full declared physical horizon in increasing ticks')
    json.dumps(result, allow_nan=False)
    if 'receiver_study' in settings:
        from .receiver_campaign import normalise_receiver_study
        result['receiver_study'] = normalise_receiver_study(settings['receiver_study'], result)
    return result


def settings_fingerprint(settings):
    return sha256(json.dumps(normalise_settings(settings), sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def _recipes(settings):
    return settings['native']['preparation_arms'] + settings['formation']['exposure_matched_recipes']


def _prerequisite(prerequisites, module, seed):
    value = (prerequisites or {}).get(module)
    if value is None:
        raise ValueError(module + ' native prerequisite is required; no hidden reacquisition')
    if value.get('module') != module or value.get('seed') != seed or value.get('schema') != 'matrix-model-free-acquisition.v1':
        raise ValueError('Prerequisite changes the assigned root or native module')
    return value


def _failure(case, error):
    partial = getattr(error, 'partial_accounting', None)
    return {**case, **({'partial_native_accounting': partial} if partial is not None else {}),
            'status': 'UNAVAILABLE', 'reason': type(error).__name__ + ': ' + str(error),
            'scientific_disposition': 'UNRESOLVED', 'attempted_work_retained': True}


def _certificate_readout(certificate):
    """Keep mechanics in the acquisition's bound array companion, not readers."""
    arrays = {'retained_basis', 'retained_basis_real', 'retained_basis_imag',
              'projected_operator', 'projected_operator_real', 'projected_operator_imag'}
    return {key: value for key, value in certificate.items() if key not in arrays}


def _formation(settings, seed):
    c, policy = settings['native'], settings['formation']
    forces, receivers = native.physical_chart(c, seed)
    cases = []
    for row in c['coordinates']:
        for recipe in _recipes(settings):
            base = {'coordinate': row, 'recipe': recipe}
            case = base
            try:
                case = native.formation(c, row, recipe, seed, policy)
                if case['status'] != 'COMPLETED':
                    cases.append(case)
                    continue
                for label, handoff in case['checkpoints'].items():
                    if handoff['state'] is None:
                        continue
                    service = []
                    handoff['service'] = service
                    for panel in range(policy['service_panels']):
                        response = native.paired_response(c, row, native.restore(handoff['state']), forces[:, :1], receivers,
                            seed, panel, collect_survival=True, required_sectors=policy['required_sectors'])
                        odd = np.asarray(response['odd_response'])
                        even = np.asarray(response['even_response'])
                        service.append({'panel': panel, 'signed_endpoint': odd[:, -1].tolist(),
                            'signal': float(np.linalg.norm(odd[:, -1, 24:])),
                            'signal_units': 'PHYSICAL_MOMENTUM_BLOCK_L2',
                            'maximum_even_normalized': classical._score(even, classical._scales(c))[0]['maximum'],
                            'survival': response['survival'], 'force_evaluations': response['force_evaluations'],
                            'tangent_hessian_actions': response['tangent_hessian_actions'],
                            'protocol_handoff_work': response['protocol_handoff_work']})
                cases.append(case)
            except (FloatingPointError, np.linalg.LinAlgError, OverflowError) as error:
                cases.append(_failure(case, error))
    return {'cases': cases, 'forces': forces.tolist(), 'receivers': receivers.tolist(),
            'same_physical_chart_across_recipes': True,
            'assigned_case_count': len(c['coordinates']) * len(_recipes(settings))}


def _memory(settings, seed):
    cases = []
    for row in settings['native']['coordinates']:
        try:
            cases.append(native.memory_record(settings['native'], row, seed, settings['memory']))
        except (FloatingPointError, np.linalg.LinAlgError, OverflowError) as error:
            cases.append(_failure({'coordinate': row, **getattr(error, 'partial_record', {})}, error))
    return {'cases': cases, 'assigned_case_count': len(cases)}


def _reduced_propagation(c, row, origin, basis, forces, receivers, hold_checkpoints, schedule, method='JOINT', native_phase_checkpoints=None, work_ledger=None):
    """Fixed or rebuilt Galerkin dynamics with explicit acquired-action costs."""
    basis = np.asarray(basis, dtype=float)
    phase_basis = classical._phase_lift(basis)
    state = np.zeros((2 * basis.shape[1], forces.shape[1]))
    actions = 0
    rank_roster, outputs, inherited = [], [], {}
    def acquired_image(at, selected):
        nonlocal actions
        action = native.action_at(at, native.coordinate(c, row).member)
        try:
            return action(selected)
        finally:
            actions += action.real_hessian_evaluations
            if work_ledger is not None:
                work_ledger['native_hessian_actions'] += action.real_hessian_evaluations
                work_ledger['native_hessian_attempts'] += getattr(action, 'real_hessian_attempts', action.real_hessian_evaluations)

    def maps(at, selected):
        image = acquired_image(at, selected)
        h = (selected.T @ image + image.T @ selected) / 2
        return discrete_baoab_maps(h, selected.T @ forces * float(c['amplitude']),
            timestep=float(c['timestep']), decay=math.exp(-float(row['friction']) * float(c['timestep'])))
    transition, injection = maps(origin, basis)
    for tick in range(c['horizon_ticks'] + 1):
        outputs.append((receivers @ phase_basis @ state).T)
        if tick in schedule:
            current = native.restore(hold_checkpoints[str(tick)])
            # Rebuild from the same seed channels after operator change. Full
            # spans remain FULL; projected state is carried in physical space.
            if basis.shape[1] < 96:
                old = phase_basis @ state
                old_phase_basis = phase_basis
                image = acquired_image(current, basis)
                structure = native.structural_seed(current)
                selected = {'INPUT': forces, 'JOINT': np.column_stack((forces, receivers[:24, :96].T)),
                    'STRUCTURAL': structure, 'STRUCTURAL_FORCE': None if structure is None else np.column_stack((structure, forces))}[method]
                if selected is None:
                    return {'prediction': None, 'hessian_actions': actions, 'status': 'UNRESOLVED',
                        'reason': 'REFRESH_STRUCTURAL_CHART_UNIDENTIFIABLE', 'schedule_ticks': schedule,
                        'position_rank_by_tick': rank_roster, 'forecast_scope': 'RETROSPECTIVE_REFRESH'}
                joined = np.column_stack((selected, image))
                u, singular, _ = np.linalg.svd(joined, full_matrices=False)
                basis = u[:, :min(basis.shape[1], int(np.sum(singular > 1e-12 * singular[0])))]
                phase_basis = classical._phase_lift(basis)
                state = phase_basis.T @ old
                inherited = {key: phase_basis.T @ old_phase_basis @ value for key, value in inherited.items()}
            transition, injection = maps(current, basis)
        if native_phase_checkpoints is not None and str(tick) in native_phase_checkpoints and tick < c['horizon_ticks']:
            original = np.asarray(native_phase_checkpoints[str(tick)]).T
            inherited[str(tick)] = phase_basis.T @ (phase_basis @ state - original)
        rank_roster.append(int(basis.shape[1]))
        if tick < c['horizon_ticks']:
            state = transition @ state + (injection if tick < c['pulse_ticks'] else 0.)
            inherited = {key: transition @ value for key, value in inherited.items()}
    decomposition = {}
    if inherited:
        from empirical_lawhood.methods.model_free_response import signed_propagation_account
        final_native = receivers @ np.asarray(native_phase_checkpoints[str(c['horizon_ticks'])]).T
        error = outputs[-1] - final_native.T
        normalizers = np.repeat(classical._scales(c)[-1], 24)
        for key, value in inherited.items():
            first = (receivers @ phase_basis @ value).T
            generated = error - first
            decomposition[key] = {'inherited_physical_vector': first.tolist(),
                'generated_physical_vector': generated.tolist(),
                'normalized_account': signed_propagation_account(first / normalizers, generated / normalizers),
                'scope': 'EXACT_ERROR_IDENTITY_FOR_THE_SELECTED_REDUCED_LINEAR_PROPAGATOR'}
    return {'prediction': np.stack(outputs, axis=1).tolist(), 'hessian_actions': actions,
            'schedule_ticks': schedule, 'position_rank_by_tick': rank_roster,
            'signed_propagation': decomposition,
            'forecast_scope': 'RETROSPECTIVE_WHEN_REFRESH_USES_ACQUIRED_FUTURE_HOLD', 'status': 'COMPLETED'}


def _response(settings, seed, prerequisites):
    from empirical_lawhood.methods.model_free_response import incremental_receiver_certificate
    prepared = _prerequisite(prerequisites, 'M1', seed)
    c, options = settings['native'], settings['response']
    forces, receivers = np.asarray(prepared['forces']), np.asarray(prepared['receivers'])
    cases = []
    refresh = sorted({tick for schedule in options['refresh_schedules'] for tick in schedule})
    for prepared_case in prepared['cases']:
        for label in options['handoffs']:
            base = {'coordinate': prepared_case['coordinate'], 'recipe': prepared_case['recipe'], 'handoff': label}
            handoff = prepared_case.get('checkpoints', {}).get(label)
            if prepared_case['status'] != 'COMPLETED' or handoff is None or handoff['state'] is None:
                cases.append({**base, 'status': 'NOT_ENTERED', 'reason': 'REQUIRED_PHYSICAL_HANDOFF_UNAVAILABLE'})
                continue
            action, controls, error_record = None, None, None
            certificates, futures, models = [], [], []
            model_work = {'native_hessian_actions': 0, 'native_hessian_attempts': 0}
            stage = 'ORIGIN_RESTORATION'
            try:
                origin = native.restore(handoff['state'])
                row = prepared_case['coordinate']
                coord = native.coordinate(c, row)
                action = native.action_at(origin, coord.member)
                structure = native.structural_seed(origin)
                seeds = {'INPUT': forces, 'JOINT': np.column_stack((forces, receivers[:24, :96].T)),
                         'STRUCTURAL': structure,
                         'STRUCTURAL_FORCE': None if structure is None else np.column_stack((structure, forces))}
                stage = 'ORIGIN_CERTIFICATES'
                for method in options['methods']:
                    for budget in options['action_budgets']:
                        if seeds[method] is None:
                            certificates.append({'method': method, 'budget': budget, 'status': 'UNRESOLVED', 'reason': 'STRUCTURAL_CHART_UNIDENTIFIABLE'})
                            continue
                        cert = incremental_receiver_certificate(action, forces, receivers[:24, :96].T,
                            complex(0., float(options['resolvent_imaginary'])), tolerance=float(options['certificate_tolerance']),
                            max_actions=budget, seed_basis=seeds[method])
                        certificates.append({'method': method, 'budget': budget, **cert})
                stage = 'PORT_CONTROLS'
                controls = native.port_controls(c, row, origin, forces, receivers, seed,
                    budget=max(options['action_budgets']), tolerance=float(options['certificate_tolerance']),
                    imaginary=float(options['resolvent_imaginary'])) if options['port_controls'] else None
                stage = 'NATIVE_FUTURES'
                for refinement in options['refinements']:
                    for scale in options['amplitude_scales']:
                        futures.append(native.paired_response(c, row, origin, forces, receivers, seed, 0,
                            refinement=refinement, amplitude_scale=float(scale), checkpoints=refresh,
                            collect_survival=True, required_sectors=settings['formation']['required_sectors']))
                primary = next(x for x in futures if x['refinement'] == 1 and x['amplitude_scale'] == 1.)
                for method in options['methods']:
                    selected = seeds[method]
                    if selected is None:
                        continue
                    u, s, _ = np.linalg.svd(selected, full_matrices=False)
                    for rank in options['equal_ranks']:
                        stage = 'MODEL_SEED_EXPANSION'
                        basis = u[:, :min(rank, int(np.sum(s > s[0] * 1e-12)))]
                        # Expand the exact seed prefix by native actions; all
                        # newly acquired images are charged to this comparison.
                        expansion = 0
                        while basis.shape[1] < rank:
                            image = action(basis)
                            expansion += basis.shape[1]
                            for _ in range(2):
                                image -= basis @ (basis.T @ image)
                            u2, s2, _ = np.linalg.svd(image, full_matrices=False)
                            available = int(np.sum(s2 > 1e-12 * max(1., s2[0])))
                            if not available:
                                break
                            basis = np.column_stack((basis, u2[:, :min(rank - basis.shape[1], available)]))
                        for schedule in options['refresh_schedules']:
                            stage = 'REDUCED_MODELS'
                            model = _reduced_propagation(c, row, origin, basis, forces, receivers, primary['hold_checkpoints'], schedule,
                                method=method, native_phase_checkpoints=primary['signed_phase_checkpoints'], work_ledger=model_work)
                            models.append({'method': method, 'requested_rank': rank,
                                'shared_seed_expansion_actions': expansion, 'shared_seed_expansion_id': method + '.rank.' + str(rank), **model})
                if seed % options['dense_oracle_seed_modulus'] == 0:
                    for schedule in options['refresh_schedules']:
                        stage = 'DENSE_ORACLE'
                        model = _reduced_propagation(c, row, origin, np.eye(96), forces, receivers, primary['hold_checkpoints'], schedule,
                            native_phase_checkpoints=primary['signed_phase_checkpoints'], work_ledger=model_work)
                        models.append({'method': 'FULL_ORACLE', 'requested_rank': 96,
                            'shared_seed_expansion_actions': 0, 'shared_seed_expansion_id': 'FULL_ORACLE', **model})
            except (FloatingPointError, np.linalg.LinAlgError, OverflowError) as error:
                error_record = _failure({}, error)
            record = {**base, 'status': 'COMPLETED', 'origin': handoff['state'], 'handoff_present': handoff['present'],
                'certificates': certificates, 'futures': futures, 'linear_models': models, 'port_controls': controls,
                'actual_hessian_actions': (0 if action is None else action.real_hessian_evaluations)
                    + model_work['native_hessian_actions']
                    + (0 if controls is None else controls['native_real_hessian_evaluations'])
                    + sum(future['tangent_hessian_actions'] for future in futures),
                'actual_force_evaluations': sum(future['force_evaluations'] for future in futures),
                'origin_action_attempts': 0 if action is None else getattr(action, 'real_hessian_attempts', action.real_hessian_evaluations),
                'model_action_attempts': model_work['native_hessian_attempts'],
                'completed_scientific_prefix': {'certificates': len(certificates), 'native_futures': len(futures),
                    'linear_models': len(models), 'failure_stage': stage if error_record else None},
                'hessian_accounting': 'DISJOINT_CERTIFICATE_SEED_EXPANSION_MODEL_REFRESH_PORT_CONTROL_AND_TANGENT_WORK',
                'information_cutoff': 'ORIGIN_CERTIFICATES_BEFORE_FUTURE_NOISE',
                'native_response_scope': 'FINITE_CHORD_WITH_SEPARATE_NUMERICAL_AND_NONLINEAR_DIAGNOSTICS'}
            if error_record:
                record.update(error_record)
            cases.append(record)
    return {'cases': cases, 'forces': forces.tolist(), 'receivers': receivers.tolist(),
            'assigned_case_count': len(prepared['cases']) * len(options['handoffs'])}


def _composition(settings, seed, prerequisites):
    source = _prerequisite(prerequisites, 'M3', seed)
    c = settings['native']
    forces, receivers = np.asarray(source['forces']), np.asarray(source['receivers'])[:24, :96]
    z = complex(0., float(settings['response']['resolvent_imaginary']))
    cases = []
    for case in source['cases']:
        if case['coordinate']['id'] not in settings['transfer']['destination_coordinate_ids']:
            continue
        row = {key: case[key] for key in ('coordinate', 'recipe', 'handoff', 'status')}
        if case['status'] == 'COMPLETED':
            nominal = next((candidate for candidate in source['cases']
                if candidate['status'] == 'COMPLETED' and candidate['recipe'] == case['recipe']
                and candidate['handoff'] == case['handoff']
                and candidate['coordinate']['id'] == settings['transfer']['source_coordinate_id']), None)
            probes = []
            identity = nominal is not None and nominal['coordinate'] == case['coordinate'] and nominal['origin'] == case['origin']
            zero_reuse = {'status': 'UNRESOLVED', 'reason': 'DESTINATION_OPERATOR_REMAINDER_NOT_SUPPLIED',
                'new_native_column_actions': 0, 'operator_identity_verified': False}
            if identity:
                inherited = [_certificate_readout(value) for value in nominal['certificates']]
                certified = bool(inherited) and all(value['status'] == 'CERTIFIED' for value in inherited)
                zero_reuse = {'status': 'CERTIFIED' if certified else 'UNRESOLVED',
                    'reason': 'EXACT_SAME_OPERATOR_INPUT_AND_RECEIVER_CERTIFICATE_REUSE',
                    'operator_identity_verified': True, 'checkpoint_sha256': case['origin']['sha256'],
                    'source_coordinate': nominal['coordinate']['id'], 'destination_coordinate': case['coordinate']['id'],
                    'new_native_column_actions': 0, 'suppliers': inherited,
                    'inherited_action_count': sum(value.get('action_count', 0) for value in inherited),
                    'target_scope': 'HERMITIAN_RESOLVENT',
                    'premises': ['identical native configuration and full saved state',
                        'identical acquired physical input and receiver', 'original certificate premises and allowances retained']}
            probe_action = None
            probe_error = None
            try:
                if nominal is not None:
                    state = native.restore(case['origin'])
                    probe_action = native.action_at(state, native.coordinate(c, case['coordinate']).member)
                    for supplier in nominal['certificates']:
                        basis_value = supplier.get('retained_basis')
                        operator_value = supplier.get('projected_operator')
                        if basis_value is None or operator_value is None:
                            continue
                        basis, operator = np.asarray(basis_value), np.asarray(operator_value)
                        if not basis.size:
                            continue
                        retained = min(basis.shape[1], settings['transfer']['probe_action_budget'])
                        basis, operator = basis[:, :retained], operator[:retained, :retained]
                        solution = np.linalg.solve(z * np.eye(len(operator)) - operator, basis.T @ forces)
                        image = probe_action(basis)
                        residual = forces - (z * basis - image) @ solution
                        bound = float(np.linalg.norm(receivers, 2) * np.linalg.norm(residual, 2) / abs(z.imag))
                        estimate = receivers @ basis @ solution
                        probes.append({'method': supplier['method'], 'source_coordinate': nominal['coordinate']['id'],
                            'destination_coordinate': case['coordinate']['id'], 'native_column_actions': basis.shape[1],
                            'source_action_budget': supplier['budget'], 'source_action_count': supplier['action_count'],
                            'source_rank': supplier['rank'], 'retained_probe_rank': retained,
                            'estimate_real': estimate.real.tolist(), 'estimate_imag': estimate.imag.tolist(),
                            'destination_receiver_bound': bound, 'target_scope': 'HERMITIAN_RESOLVENT',
                            'status': 'CERTIFIED' if bound <= float(settings['response']['certificate_tolerance']) else 'UNRESOLVED',
                            'premises': ['declared Hermitian native Hessian', 'floating-point action numerical allowance remains separate'],
                            'actual_destination_probe': True, 'native_finite_response_certified': False,
                            'destination_operator_error_bound': 0.,
                            'numerical_scope': 'binary64 mathematical residual estimate; no interval or native finite-response certificate'})
            except (FloatingPointError, np.linalg.LinAlgError, OverflowError) as error:
                probe_error = _failure({}, error)
            row.update(measured_checkpoint=case['origin'],
                direct_suppliers=[_certificate_readout(value) for value in case['certificates']],
                transfer_modes={'zero_new_action_reuse': zero_reuse,
                    'residual_probe_reuse': {'status': ('PARTIAL' if probes else 'UNRESOLVED') if probe_error else ('AVAILABLE' if probes else 'UNRESOLVED'),
                        'scope': 'SCOPED_NATIVE_RESOLVENT_CERTIFICATE', 'suppliers': probes},
                    'new_local_actions': {'status': 'AVAILABLE', 'scope': 'ALGORITHM_PORTABILITY', 'same_frozen_policy': True,
                        'suppliers': [_certificate_readout(value) for value in case['certificates']], 'work_already_acquired_in': 'M3',
                        'inherited_action_count': sum(v.get('action_count', 0) for v in case['certificates'])}},
                acquired_information='ACTUAL_CHECKPOINT_NOT_FORECAST_U',
                historical_U_F='UNAVAILABLE_UNLESS_ORIGINAL_AUTHENTICATED_OPERANDS_ENTERED',
                new_native_actions=0 if probe_action is None else probe_action.real_hessian_evaluations,
                native_action_attempts=0 if probe_action is None else getattr(probe_action, 'real_hessian_attempts', probe_action.real_hessian_evaluations),
                completed_destination_probes=len(probes))
            if probe_error:
                row.update(probe_error)
        cases.append(row)
    return {'cases': cases, 'assigned_case_count': len(cases),
            'new_native_actions': sum(case.get('new_native_actions', 0) for case in cases),
            'reuse_scope': 'SOURCE_REUSE_DESTINATION_PROBES_AND_NEW_LOCAL_PURCHASE_SEPARATED', 'learned_benchmark_status': 'NOT_ENTERED'}


def _population(settings, seed, prerequisites, sampling):
    """Freeze local auxiliaries and audit entire paired roots selected by design."""
    source = _prerequisite(prerequisites, 'M1', seed)
    c, p = settings['native'], settings['population']
    required = {'audit_selected', 'inclusion_probability', 'frame_id', 'frame_size', 'audit_size'}
    if not isinstance(sampling, dict) or set(sampling) != required:
        raise ValueError('M5 requires the authored whole-root probability-sampling assignment')
    if (type(sampling['audit_selected']) is not bool or not sampling['frame_id']
            or sampling['frame_size'] != p['frame_size'] or sampling['audit_size'] != p['audit_size']
            or abs(float(sampling['inclusion_probability']) - p['audit_size'] / p['frame_size']) > 1e-14):
        raise ValueError('M5 changes its frozen finite-frame SRS design')
    forces, receivers = native.physical_chart(c, p['receiver_seed'])
    component = 24
    frozen = []
    # Complete all auxiliaries before the selected native outcomes are touched.
    for case in source['cases']:
        row = {'coordinate': case['coordinate'], 'recipe': case['recipe'],
               'auxiliary': 0., 'auxiliary_hessian_actions': 0, 'origin': None,
               'auxiliary_status': 'NO_PHYSICAL_PREPARATION',
               'auxiliary_failure_policy': p['auxiliary_failure_policy']}
        handoff = case.get('checkpoints', {}).get('fixed')
        if case['status'] == 'COMPLETED' and handoff is not None and handoff['state'] is not None:
            origin = native.restore(handoff['state'])
            row['origin'] = handoff['state']
            work = 0
            try:
                action = native.action_at(origin, native.coordinate(c, case['coordinate']).member)
                basis = forces[:, :1].copy()
                while basis.shape[1] < p['auxiliary_rank']:
                    image = action(basis)
                    work += basis.shape[1]
                    for _ in range(2):
                        image -= basis @ (basis.T @ image)
                    u, values, _ = np.linalg.svd(image, full_matrices=False)
                    available = int(np.sum(values > 1e-12 * max(1., values[0])))
                    if not available:
                        break
                    basis = np.column_stack((basis, u[:, :min(available, p['auxiliary_rank'] - basis.shape[1])]))
                model = _reduced_propagation(c, case['coordinate'], origin, basis, forces[:, :1], receivers, {}, [], method='INPUT')
                auxiliary = float(np.asarray(model['prediction'])[0, -1, component])
                work += model['hessian_actions']
                if not math.isfinite(auxiliary):
                    raise FloatingPointError('nonfinite frozen physical auxiliary')
                row.update(auxiliary=auxiliary, auxiliary_hessian_actions=work,
                           auxiliary_status='PHYSICAL_AUXILIARY')
            except (FloatingPointError, np.linalg.LinAlgError, OverflowError) as error:
                # Any finite frozen auxiliary remains design-unbiased. Select
                # this fallback before contact; native outcomes never refit it.
                row.update(auxiliary=0., auxiliary_hessian_actions=work,
                    auxiliary_status='NUMERICAL_FAILURE_FROZEN_ZERO', auxiliary_failure=str(error),
                    attempted_work_count_is_lower_bound=True)
        frozen.append(row)
    freeze = sha256(json.dumps(frozen, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    cases = []
    selected = sampling['audit_selected'] or p['mode'] == 'reveal_all'
    for row in frozen:
        case = {key: value for key, value in row.items() if key != 'origin'}
        case.update(status='COMPLETED', native_value=None, native_calls_acquired=0,
                    native_calls_attempted=0, native_force_evaluations=0,
                    native_energy_evaluations=0, protocol_handoff_work={},
                    tangent_hessian_actions=0, auxiliary_frozen_sha256=freeze,
                    frame_member_defined=row['origin'] is not None)
        if row['origin'] is None:
            case.update(status='UNAVAILABLE', reason='FINITE_FRAME_PREPARATION_UNAVAILABLE')
        if selected:
            if row['origin'] is None:
                case.update(status='UNAVAILABLE', reason='SELECTED_ROOT_PREPARATION_UNAVAILABLE')
            else:
                try:
                    views = {}
                    for refinement in (1, 2):
                        case['native_calls_attempted'] += 1
                        view = native.paired_response(c, row['coordinate'], native.restore(row['origin']),
                            forces[:, :1], receivers, seed, 5000, refinement=refinement)
                        case['native_calls_acquired'] += 1
                        case['native_force_evaluations'] += view['force_evaluations']
                        case['tangent_hessian_actions'] += view['tangent_hessian_actions']
                        if 'protocol_handoff_work' in view:
                            case['protocol_handoff_work'][str(refinement)] = view['protocol_handoff_work']
                            case['native_energy_evaluations'] += view['protocol_handoff_work']['potential_evaluations']
                        views[refinement] = view
                    coarse, fine = views[1], views[2]
                    actual = float(np.asarray(fine['odd_response'])[0, -1, component])
                    primary = float(np.asarray(coarse['odd_response'])[0, -1, component])
                    if p['clip_bounds'] is not None:
                        actual = float(np.clip(actual, *[float(v) for v in p['clip_bounds']]))
                    case.update(native_value=actual,
                        numerical_view_difference=abs(primary - float(np.asarray(fine['odd_response'])[0, -1, component])),
                        individual_error=abs(actual - row['auxiliary']),
                        individual_within_requested_halfwidth=abs(actual - row['auxiliary']) <= float(p['individual_halfwidth']))
                except (FloatingPointError, np.linalg.LinAlgError, OverflowError) as error:
                    case.update(status='UNAVAILABLE', reason=str(error),
                                attempted_work_count_is_lower_bound=True)
                    if getattr(error, 'partial_accounting', None) is not None:
                        case['partial_native_accounting'] = error.partial_accounting
        cases.append(case)
    return {'cases': cases, 'assigned_case_count': len(source['cases']), 'sampling': sampling,
        'auxiliary_freeze_sha256': freeze, 'frame_unit': 'WHOLE_PAIRED_INDEPENDENT_ROOT',
        'native_future_panel': 5000, 'native_frame_target': 'SIGNED_FINE_VIEW_ENDPOINT_MOMENTUM',
        'receiver_direction': forces[:, 0].tolist(), 'native_audit_root_acquired': selected,
        'native_audit_root_omitted': not selected, 'native_clipped_target': p['clip_bounds'],
        'no_individual_calibration_claim': True}


def _equilibrium(settings, seed):
    cases = []
    for row in settings['native']['coordinates']:
        try:
            cases.append(native.equilibrium_record(settings['native'], row, seed, settings['equilibrium']))
        except (FloatingPointError, np.linalg.LinAlgError, OverflowError) as error:
            cases.append(_failure({'coordinate': row, **getattr(error, 'partial_record', {})}, error))
    return {'cases': cases, 'assigned_case_count': len(cases)}


def _events(settings, seed, prerequisites):
    prepared = (prerequisites or {}).get('M1')
    cases = []
    if prepared is not None:
        prepared = _prerequisite(prerequisites, 'M1', seed)
        selected = [(x['coordinate'], x['recipe'], x.get('checkpoints', {}).get('fixed')) for x in prepared['cases']]
    else:
        selected = [(row, 'declared-native-preparation', None) for row in settings['native']['coordinates']]
    for row, history, checkpoint in selected:
        if prepared is not None and (checkpoint is None or checkpoint.get('state') is None
                or settings['events']['require_admitted_entry'] and not checkpoint.get('present', False)):
            cases.append({'coordinate': row, 'entry_history': history, 'status': 'UNAVAILABLE',
                          'reason': 'ASSIGNED_PREPARATION_ENTRY_UNAVAILABLE_OR_NOT_ADMITTED'})
            continue
        try:
            events = native.first_passage(settings['native'], row, seed, settings['events'],
                origin=None if checkpoint is None else native.restore(checkpoint['state']), history=history)
            cases.append({'coordinate': row, 'entry_history': history, 'status': 'COMPLETED', 'events': events})
        except (FloatingPointError, np.linalg.LinAlgError, OverflowError) as error:
            cases.append(_failure({'coordinate': row, 'entry_history': history}, error))
    return {'cases': cases, 'assigned_case_count': len(selected),
            'entry_source': 'M1' if prepared is not None else 'DECLARED_TARGET_PREPARATION'}


def _validate_acquisition_census(settings, payload):
    module = payload['module']
    coords = [row['id'] for row in settings['native']['coordinates']]
    recipes = _recipes(settings)
    if module == 'M0':
        if payload['cases'] or payload['assigned_case_count'] != 1:
            raise ValueError('Control acquisition changes the assigned independent root')
        return
    if module in ('M1', 'M5'):
        expected = {(coordinate, recipe) for coordinate in coords for recipe in recipes}
        actual = [(case['coordinate']['id'], case['recipe']) for case in payload['cases']]
    elif module in ('M3', 'M4'):
        if module == 'M4':
            coords = settings['transfer']['destination_coordinate_ids']
        expected = {(coordinate, recipe, handoff) for coordinate in coords for recipe in recipes for handoff in settings['response']['handoffs']}
        actual = [(case['coordinate']['id'], case['recipe'], case['handoff']) for case in payload['cases']]
    elif module == 'M7':
        histories = recipes if payload['entry_source'] == 'M1' else ['declared-native-preparation']
        expected = {(coordinate, history) for coordinate in coords for history in histories}
        actual = [(case['coordinate']['id'], case['entry_history']) for case in payload['cases']]
        replicas = settings['events']['replicas']
        for case in payload['cases']:
            if case['status'] != 'COMPLETED':
                continue
            events = case.get('events', [])
            if (len(events) != replicas or {event.get('replica') for event in events} != set(range(replicas))
                    or any(type(event.get('replica')) is not int or event.get('root_id') != str(payload['seed'])
                        or event.get('entry_history') != case['entry_history']
                        or event.get('weight') != 1 / replicas for event in events)):
                raise ValueError('Native event acquisition changes its assigned paired replica/root/weight census')
            timestep = float(settings['native']['timestep'])
            horizon = settings['events']['horizon_ticks'] * timestep
            tolerance = 64 * np.finfo(float).eps * max(horizon, timestep)
            for event in events:
                for field in ('event_time', 'observed_until'):
                    value = event.get(field)
                    if field == 'event_time' and value is None:
                        continue
                    if (isinstance(value, bool) or not isinstance(value, (int, float))
                            or not math.isfinite(value) or not 0 <= value <= horizon
                            or abs(value - round(value / timestep) * timestep) > tolerance):
                        raise ValueError('Native first-passage times must lie on the declared native tick grid')
    else:
        expected = set(coords)
        actual = [case['coordinate']['id'] for case in payload['cases']]
    if len(actual) != len(set(actual)) or set(actual) != expected or payload['assigned_case_count'] != len(expected):
        raise ValueError('Native acquisition loses or duplicates an assigned scientific case')


def acquire_root(settings, seed, module, *, prerequisite_payloads=None, sampling=None, assigned_modules=None):
    settings = normalise_settings(settings)
    if module not in MODULES or type(seed) is not int or seed < 0:
        raise ValueError('Unknown module or invalid independent root')
    for value in (prerequisite_payloads or {}).values():
        if value.get('settings_sha256') != settings_fingerprint(settings):
            raise ValueError('Prerequisite changes the frozen scientific settings')
    if 'receiver_study' in settings:
        from .receiver_campaign import acquire
        return acquire(settings, seed, module, prerequisite_payloads or {}, sampling, assigned_modules)
    began = perf_counter()
    if module == 'M0':
        from empirical_lawhood.methods.model_free.controls import control_suite
        from empirical_lawhood.methods.model_free_response import harmonic_bath_trajectories
        from empirical_lawhood.methods.retained_gaussian_response import HarmonicBath
        baths = []
        for coupling, hidden in ((1., 1.), (2., 4.)):
            bath = HarmonicBath(np.array([[2.]]), np.array([[coupling]]), np.array([[hidden]]))
            for preparation in ('canonical', 'conditional'):
                values = harmonic_bath_trajectories(bath, beta=1., times=np.linspace(0., 4., 33), samples=32,
                    seed=seed, preparation=preparation,
                    **({'retained_position': [1.], 'retained_velocity': [0.]} if preparation == 'conditional' else {}))
                baths.append({'coupling': coupling, 'hidden_stiffness': hidden,
                    **{key: val.tolist() if isinstance(val, np.ndarray) else val for key, val in values.items()}})
        payload = {'controls': control_suite(seed=seed), 'cases': [], 'assigned_case_count': 1,
            'harmonic_bath_controls': baths,
            'historical_operands': settings['historical_operands'],
            'historical_status': 'UNAVAILABLE' if not settings['historical_operands'] else 'DECLARED_REFERENCES_REQUIRE_AUTHENTICATION',
            'unit_checks': {'probability_gain': 'PROBABILITY_DIFFERENCE', 'loss_gain': 'NORMALIZED_CONTINUOUS_LOSS'},
            'no_empty_admission_shortcut': True}
    elif module == 'M1':
        payload = _formation(settings, seed)
    elif module == 'M2':
        payload = _memory(settings, seed)
    elif module == 'M3':
        payload = _response(settings, seed, prerequisite_payloads)
    elif module == 'M4':
        payload = _composition(settings, seed, prerequisite_payloads)
    elif module == 'M5':
        payload = _population(settings, seed, prerequisite_payloads, sampling)
    elif module == 'M6':
        payload = _equilibrium(settings, seed)
    else:
        payload = _events(settings, seed, prerequisite_payloads)
    result = {'schema': 'matrix-model-free-acquisition.v1', 'module': module, 'seed': seed,
        'settings_sha256': settings_fingerprint(settings), 'independent_units': 1,
        'evidence_scope': settings['evidence_scope'], 'acquisition_seconds': perf_counter() - began,
        'prerequisites': {key: {'seed': val['seed'], 'module': val['module'], 'settings_sha256': val['settings_sha256']}
                          for key, val in (prerequisite_payloads or {}).items()}, **payload}
    result['status'] = 'COMPLETED' if all(x['status'] == 'COMPLETED' for x in result['cases']) else 'PARTIAL'
    force_count, hessian_count, energy_count = 0, 0, 0
    for case in result['cases']:
        if module == 'M1':
            force_count += case.get('preparation_force_evaluations', 0)
            energy_count += case.get('protocol_work', {}).get('potential_evaluations_completed', 0)
            for handoff in case.get('checkpoints', {}).values():
                for panel in handoff.get('service', []):
                    force_count += panel['force_evaluations']
                    hessian_count += panel['tangent_hessian_actions']
                    energy_count += panel.get('protocol_handoff_work', {}).get('potential_evaluations', 0)
        elif module == 'M3':
            force_count += case.get('actual_force_evaluations', 0)
            hessian_count += case.get('actual_hessian_actions', 0)
            energy_count += sum(future.get('protocol_handoff_work', {}).get('potential_evaluations', 0) for future in case.get('futures', []))
        elif module == 'M7':
            force_count += sum(row['native_force_evaluations'] for row in case.get('events', []))
            energy_count += sum(row.get('native_energy_evaluations', 0) for row in case.get('events', []))
        else:
            force_count += case.get('native_force_evaluations', 0)
            hessian_count += case.get('auxiliary_hessian_actions', 0) + case.get('tangent_hessian_actions', 0)
            energy_count += case.get('native_energy_evaluations', 0)
        partial = case.get('partial_native_accounting', {})
        force_count += partial.get('native_force_evaluations', 0)
        hessian_count += partial.get('native_hessian_actions', 0)
        energy_count += partial.get('native_energy_evaluations', 0)
    if module == 'M4':
        hessian_count += result['new_native_actions']
    result['work_accounting'] = {'native_force_evaluations': force_count, 'native_hessian_actions': hessian_count,
        'native_energy_evaluations': energy_count, 'counts_are_lower_bounds': any(case['status'] == 'UNAVAILABLE'
            or case.get('attempted_work_count_is_lower_bound', False)
            or any(event['status'] in ('failed', 'truncated') or event.get('failure') is not None
                for event in case.get('events', [])) for case in result['cases']),
        'wall_seconds': result['acquisition_seconds'],
        'scope': 'THIS_OPERATION_ONLY; SHARED_PREREQUISITE_WORK_CHARGED_AT_ITS_ORIGINAL_ACQUISITION; PUBLICATION_AND_READING_IN_EXECUTION_RECEIPTS'}
    _validate_acquisition_census(settings, result)
    json.dumps(result, allow_nan=False)
    return result


def _analyse_memory(settings, acquired):
    from empirical_lawhood.methods.model_free.observation import ObservationContract, discretize
    from empirical_lawhood.methods.model_free.memory import root_lag_counts, memory_diagnostics, root_segment_counts
    options, cases = settings['memory'], []
    for case in acquired['cases']:
        if case['status'] != 'COMPLETED':
            raw_fields = {'observables', 'energies', 'checkpoints', 'momentum_reset_controls', 'incomplete_observation'}
            cases.append({**{key: value for key, value in case.items() if key not in raw_fields},
                'partial_native_record': {'observations': len(case.get('observables', [])),
                    'energies': len(case.get('energies', [])), 'checkpoints': len(case.get('checkpoints', [])),
                    'reset_controls': len(case.get('momentum_reset_controls', [])),
                    'completed_reset_controls': sum(row.get('status') == 'COMPLETED'
                        for row in case.get('momentum_reset_controls', [])),
                    'incomplete_observation_present': case.get('incomplete_observation') is not None,
                    'raw_prefix_owner': 'IMMUTABLE_ORIGINAL_ACQUISITION; NOT_REPLAYED_OR_RECOUNTED_HERE'}})
            continue
        values, energies = np.asarray(case['observables']), np.asarray(case['energies'])
        observations, segment_observations = [], []
        for dimension in options['observation_dimensions']:
            contract = ObservationContract('q-velocity-force-' + str(dimension), ('q', 'velocity', 'force')[:dimension],
                ('matrix-position', 'matrix-position/time', 'matrix-force')[:dimension],
                tuple(tuple(float(v) for v in x) for x in options['bin_edges'][:dimension]),
                case['physical_timestep'], 'constant-controls-finite-age', parity=(1, -1, 1)[:dimension])
            symbols = discretize(values[:, :dimension], contract)
            segment_counts = root_segment_counts(symbols['symbols'], options['segment_boundaries_samples'],
                lags=options['lags'], alphabet_size=symbols['alphabet_size'], root_id=str(acquired['seed']),
                sample_interval=case['physical_timestep'], max_cells=options['maximum_cells'])
            for segment in segment_counts['segments']:
                segment_symbols = discretize(values[segment['start_sample']:segment['stop_sample_exclusive'], :dimension], contract)
                segment['nonfinite_samples'] = segment_symbols['nonfinite_rows']
                segment['out_of_range_samples'] = segment_symbols['out_of_range_rows']
                segment['absolute_first_sample_time'] = (options['burnin_ticks'] * float(settings['native']['timestep'])
                    + segment['first_sample_time'])
            segment_observations.append({'observation_id': contract.observation_id,
                'contract': asdict(contract), 'counts': segment_counts})
            for order in options['history_orders']:
                counts = root_lag_counts(symbols['symbols'], options['lags'], alphabet_size=symbols['alphabet_size'],
                    history_order=order, max_cells=options['maximum_cells'], root_id=str(acquired['seed']))
                diagnostics = {lag: memory_diagnostics(row['joint_counts']) for lag, row in counts['lags'].items() if row['observed_anchors']}
                observations.append({'observation_id': contract.observation_id, 'history_order': order,
                    'contract': asdict(contract), 'counts': counts, 'diagnostics': diagnostics,
                    'missing_rows': symbols['missing_rows'], 'nonfinite_rows': symbols['nonfinite_rows'],
                    'out_of_range_rows': symbols['out_of_range_rows']})
                for age in options['protocol_age_ticks']:
                    age_counts = root_lag_counts(symbols['symbols'], options['lags'], alphabet_size=symbols['alphabet_size'],
                        history_order=order, max_cells=options['maximum_cells'], root_id=str(acquired['seed']),
                        record_scope='protocol_age', anchor_indices=(age // options['stride'],))
                    observations.append({'observation_id': contract.observation_id + '-age-' + str(age),
                        'history_order': order, 'contract': {**asdict(contract), 'target_law': 'protocol_age',
                            'absolute_age_tick': options['burnin_ticks'] + age}, 'counts': age_counts,
                        'diagnostics': {lag: memory_diagnostics(row['joint_counts']) for lag, row in age_counts['lags'].items() if row['observed_anchors']},
                        'missing_rows': symbols['missing_rows']})
        optional = {}
        if options['optional_diagnostics']:
            from empirical_lawhood.methods.model_free.comparators import compression_diagnostic, path_reversal_diagnostic
            contract = ObservationContract('q', ('q',), ('matrix-position',),
                (tuple(float(x) for x in options['bin_edges'][0]),), case['physical_timestep'], 'constant-controls-finite-age')
            mapped = discretize(values[:, :1], contract)
            if mapped['missing_rows']:
                optional = {name: {'status': 'UNRESOLVED', 'reason': 'DECLARED_DIAGNOSTIC_OBSERVATION_HAS_MISSING_OR_TAIL_ROWS'} for name in options['optional_diagnostics']}
            else:
                if 'compression' in options['optional_diagnostics']:
                    optional['compression'] = compression_diagnostic(mapped['symbols'], alphabet_size=mapped['alphabet_size'],
                        prefix_lengths=[len(mapped['symbols'])], seed=acquired['seed'])
                if 'path_reversal' in options['optional_diagnostics']:
                    optional['path_reversal'] = path_reversal_diagnostic({str(acquired['seed']): mapped['symbols']},
                        alphabet_size=mapped['alphabet_size'], reversal_map=list(range(mapped['alphabet_size'])),
                        order=1, sample_interval=case['physical_timestep'], maximum_cells=options['maximum_cells'])
        segments = [slice(start, stop) for start, stop in zip(options['segment_boundaries_samples'], options['segment_boundaries_samples'][1:])]
        cases.append({'coordinate': case['coordinate'], 'status': 'COMPLETED', 'observations': observations,
            'stationarity': {'established': False, 'scope': case['scope'],
                'segment_observable_means': [values[s].mean(axis=0).tolist() for s in segments],
                'segment_energy_means': [float(energies[s].mean()) for s in segments],
                'segment_observations': segment_observations,
                'segment_boundaries_samples': options['segment_boundaries_samples'],
                'transition_policy': options['segment_transition_policy'],
                'interpretation': 'DRIFT_DIAGNOSTICS_DO_NOT_PROVE_MIXING'},
            'momentum_reset_controls': case['momentum_reset_controls'],
            'optional_diagnostics': optional, 'physical_observation': case['observation'],
            'native_force_evaluations': case['native_force_evaluations']})
    return cases


def _analyse_response(settings, acquired):
    cases = []
    from empirical_lawhood.methods.model_free_response import signed_error_account, select_causal_response
    tolerance = float(settings['native']['response_tolerance'])
    numerical_tolerance = float(settings['native']['numerical_tolerance'])
    scales = classical._scales(settings['native'])
    def score(values):
        return classical._score(np.asarray(values), scales)[0]['maximum']
    for case in acquired['cases']:
        if case['status'] != 'COMPLETED':
            # Complete prefix arrays stay in the authenticated acquisition.
            # A failed later phase must not duplicate them in population readout
            # or turn the prefix into a complete response comparison.
            compact = {key: value for key, value in case.items()
                if key not in ('futures', 'linear_models', 'origin', 'certificates', 'port_controls')}
            compact['certificates'] = [_certificate_readout(value) for value in case.get('certificates', [])]
            compact['completed_native_futures'] = [{key: future[key] for key in
                ('refinement', 'amplitude_scale', 'force_evaluations', 'tangent_hessian_actions', 'scope', 'physical_horizon')}
                for future in case.get('futures', [])]
            compact['completed_model_prefix'] = [{key: value for key, value in model.items() if key != 'prediction'}
                for model in case.get('linear_models', [])]
            compact['native_prefix_owner'] = 'EXACT_BOUND_ACQUISITION; INCOMPLETE_RESPONSE_REMAINS_UNAVAILABLE'
            cases.append(compact)
            continue
        primary = next(v for v in case['futures'] if v['refinement'] == 1 and v['amplitude_scale'] == 1.)
        target = np.asarray(primary['odd_response'])
        fine = next((v for v in case['futures'] if v['refinement'] == 2 and v['amplitude_scale'] == 1.), None)
        finest = next((v for v in case['futures'] if v['refinement'] == 4 and v['amplitude_scale'] == 1.), None)
        numeric = None if fine is None else score(target - np.asarray(fine['odd_response']))
        fine_numeric = None if finest is None or fine is None else score(np.asarray(fine['odd_response']) - np.asarray(finest['odd_response']))
        scale = next((v for v in case['futures'] if v['refinement'] == 1 and v['amplitude_scale'] != 1.), None)
        nonlinearity = None if scale is None else score(target - np.asarray(scale['odd_response']) / scale['amplitude_scale'])
        tangent_error = score(target - np.asarray(primary['native_tangent']))
        models = []
        for model in case['linear_models']:
            if model.get('status') == 'UNRESOLVED':
                models.append(model)
                continue
            prediction = np.asarray(model['prediction'])
            error = prediction - target
            maximum = score(error)
            signal = float(np.linalg.norm(target[:, -1, 24:]))
            models.append({**{key: value for key, value in model.items() if key != 'prediction'},
                'predicted_endpoint': prediction[:, -1].tolist(),
                'signed_endpoint_error': error[:, -1].tolist(), 'maximum_receiver_error': maximum,
                'signed_checkpoint_errors': {str(tick): error[:, tick].tolist() for tick in sorted({t for schedule in settings['response']['refresh_schedules'] for t in schedule})},
                'complete_signed_error_recipe': {'source': 'EXACT_BOUND_ACQUISITION', 'operation': 'prediction_minus_native_odd_response',
                    'method': model['method'], 'rank': model['requested_rank'], 'schedule': model['schedule_ticks'],
                    'native_refinement': 1, 'native_amplitude_scale': 1},
                'error_units': 'MAXIMUM_POSITION_OR_MOMENTUM_BLOCK_L2_NORMALIZED_BY_DECLARED_FREE_IMPULSE_SCALE',
                'physical_endpoint_position_error': float(np.linalg.norm(error[:, -1, :24])),
                'physical_endpoint_momentum_error': float(np.linalg.norm(error[:, -1, 24:])),
                'signal': signal, 'adequate': maximum <= tolerance and signal >= float(settings['response']['minimum_signal'])
                    and numeric is not None and numeric <= numerical_tolerance,
                'error_budget': {'numerical_view_difference': numeric, 'finer_difference': fine_numeric,
                    'finite_amplitude_difference': nonlinearity, 'native_tangent_difference': tangent_error,
                    'complete_deterministic_bound': None},
                'signed_endpoint_contrast': signed_error_account(target[0, -1], prediction[0, -1],
                    target[-1, -1], prediction[-1, -1])})
        selectors = []
        cutoff = settings['response']['selection_tick']
        normalizers = np.repeat(scales, 24, axis=1)
        for method in settings['response']['methods']:
            for rank in settings['response']['equal_ranks']:
                candidates = {','.join(str(tick) for tick in model['schedule_ticks']) or 'origin-only': np.asarray(model['prediction'])
                    for model in case['linear_models'] if model['method'] == method and model['requested_rank'] == rank
                    and model.get('status') != 'UNRESOLVED' and max(model['schedule_ticks'], default=0) <= cutoff}
                if not candidates:
                    continue
                selected = select_causal_response(target, candidates, cutoff_tick=cutoff,
                    target_tick=settings['native']['horizon_ticks'], normalizers=normalizers, block_width=24,
                    minimum_signal=float(settings['response']['minimum_signal']))
                suffix_scores = {}
                for name, prediction in candidates.items():
                    error = (prediction[:, cutoff + 1:] - target[:, cutoff + 1:]) / normalizers[cutoff:]
                    suffix_scores[name] = float(np.max(np.linalg.norm(error.reshape(-1, 24), axis=-1)))
                selectors.append({'method': method, 'rank': rank, **selected,
                    'withheld_suffix_scores': suffix_scores,
                    'selected_suffix_score': None if selected['selected'] is None else suffix_scores[selected['selected']],
                    'prefix_acquisition_already_charged': True, 'future_operator_data_in_candidate_after_cutoff': False})
        control = deepcopy(case['port_controls'])
        if control is not None:
            for key in ('held_out', 'swapped_port'):
                control[key]['certificate'] = _certificate_readout(control[key]['certificate'])
        cases.append({key: value for key, value in case.items() if key not in ('futures', 'linear_models', 'origin', 'certificates', 'port_controls')} | {
            'certificates': [_certificate_readout(value) for value in case['certificates']], 'port_controls': control,
            'models': models, 'selectors': selectors, 'numerical_difference': numeric, 'finer_numerical_difference': fine_numeric,
            'native_endpoint': target[:, -1].tolist(),
            'nonlinear_chord_difference': nonlinearity, 'native_tangent_difference': tangent_error,
            'survival': primary['survival'], 'maximum_even_normalized_response': score(primary['even_response']),
            'native_force_evaluations': sum(v['force_evaluations'] for v in case['futures']),
            'native_tangent_hessian_actions': sum(v['tangent_hessian_actions'] for v in case['futures'])})
    return cases


def analyse_root(settings, payload, *, retained_settings=None):
    settings = normalise_settings(settings)
    acquisition_settings = settings if retained_settings is None else normalise_settings(retained_settings)
    changed = False
    if retained_settings is not None:
        from .retained_analysis import validate_reanalysis_settings
        changed = validate_reanalysis_settings(acquisition_settings, settings, (payload.get('module'),))
    if payload.get('schema') != 'matrix-model-free-acquisition.v1' or payload.get('settings_sha256') != settings_fingerprint(acquisition_settings):
        raise ValueError('Analysis changes original scientific acquisition')
    module = payload['module']
    if 'receiver_study' in settings:
        from .receiver_campaign import analyse
        return analyse(settings, payload, acquisition_settings, changed, retained_settings is not None)
    _validate_acquisition_census(acquisition_settings, payload)
    if module == 'M2':
        cases = _analyse_memory(settings, payload)
    elif module == 'M3':
        cases = _analyse_response(settings, payload)
    elif module == 'M1':
        cases = []
        for case in payload['cases']:
            if case['status'] != 'COMPLETED':
                cases.append(case)
                continue
            handoffs = {}
            for key, handoff in case['checkpoints'].items():
                service = handoff.get('service', [])
                survives = bool(service) and all(all(row['present'] for row in panel['survival']) for panel in service)
                signal = min((p['signal'] for p in service), default=0.)
                handoffs[key] = {'tick': handoff['tick'], 'present': handoff['present'], 'survives': survives,
                    'signal': signal, 'service_available': handoff['present'] and survives and signal >= float(settings['formation']['minimum_signal']),
                    'accuracy_assessment_owner': 'M3_MATCHED_NATIVE_RESPONSE',
                    'service_force_evaluations': sum(p['force_evaluations'] for p in service),
                    'preparation_protocol_work_prefix': handoff.get('protocol_work_prefix'),
                    'service_protocol_work_by_panel': [p.get('protocol_handoff_work') for p in service]}
            cases.append({key: value for key, value in case.items() if key not in ('checkpoints', 'observations')} | {'handoffs': handoffs})
    elif module == 'M6':
        cases = []
        for case in payload['cases']:
            if case['status'] != 'COMPLETED':
                raw_fields = {'center_records', 'incomplete_center_record', 'importance', 'completed_importance_native_samples'}
                current = case.get('incomplete_center_record') or {}
                cases.append({**{key: value for key, value in case.items() if key not in raw_fields},
                    'partial_native_record': {'completed_centers': len(case.get('center_records', [])),
                        'incomplete_center_samples': len(current.get('samples', [])),
                        'incomplete_center_completed_ticks': current.get('completed_ticks'),
                        'completed_importance_native_samples': len(case.get('completed_importance_native_samples', [])),
                        'completed_importance_centers': len(case.get('importance', [])),
                        'raw_prefix_owner': 'IMMUTABLE_ORIGINAL_ACQUISITION; NOT_REPLAYED_OR_RECOUNTED_HERE'}})
                continue
            center_records = []
            for record in case['center_records']:
                samples = np.asarray(record['samples'])
                half = len(samples) // 2
                center_records.append({key: value for key, value in record.items() if key != 'samples'} | {
                    'short_second_moment': float(np.mean(samples[:record['sample_count'], 0] ** 2)),
                    'temporal_sample_variance_scope': 'DDOF1_FINITE_RECORD; AUTOCORRELATION_BIAS_NOT_CORRECTED',
                    'instantaneous_covariance': np.cov(samples.T, ddof=1).tolist(),
                    'lag_one_covariance': ((samples[:-1] - samples[:-1].mean(axis=0)).T @ (samples[1:] - samples[1:].mean(axis=0)) / max(1, len(samples) - 2)).tolist(),
                    'early_late_mean_difference': float(samples[half:, 0].mean() - samples[:half, 0].mean())})
            cases.append({key: value for key, value in case.items() if key != 'center_records'} | {'center_records': center_records})
    else:
        cases = payload['cases']
    result = {'schema': 'matrix-model-free-analysis.v1', 'module': module, 'seed': payload['seed'],
        'settings_sha256': settings_fingerprint(settings), 'independent_units': 1, 'cases': cases,
        'retained_acquisition_settings_sha256': payload['settings_sha256'],
        'analysis_settings_changed': changed,
        'assessment_exposure': 'EXPOSED_REANALYSIS' if retained_settings is not None else 'AS_AUTHORED',
        'assigned_case_count': payload['assigned_case_count'], 'status': payload['status'],
        'acquisition_seconds': payload['acquisition_seconds'], 'evidence_scope': payload['evidence_scope'],
        'work_accounting': payload['work_accounting'],
        'scientific_claim': 'SCOPED_ESTIMATES_AND_UNRESOLVED_PREMISES_NOT_AUTOMATIC_QUALIFICATION'}
    if module == 'M5':
        for key in ('sampling', 'frame_unit', 'native_audit_root_acquired', 'native_audit_root_omitted', 'native_clipped_target'):
            result[key] = payload[key]
    if module == 'M7':
        result['entry_source'] = payload['entry_source']
    if module == 'M0':
        result['controls'] = payload['controls']
        result['harmonic_bath_controls'] = payload['harmonic_bath_controls']
        result['historical_status'] = payload['historical_status']
    json.dumps(result, allow_nan=False)
    return result


def synthesise_roots(settings, readouts):
    settings = normalise_settings(settings)
    if not readouts:
        raise ValueError('Population synthesis requires assigned root results')
    if len({(x['module'], x['seed']) for x in readouts}) != len(readouts):
        raise ValueError('Duplicate independent root/module readout')
    fingerprint = settings_fingerprint(settings)
    if any(x.get('schema') != 'matrix-model-free-analysis.v1' or x['settings_sha256'] != fingerprint for x in readouts):
        raise ValueError('Population analysis changes frozen settings or readout type')
    by_module = {module: [x for x in readouts if x['module'] == module] for module in MODULES}
    results = {}
    original_settings = settings
    for module, roots in by_module.items():
        if not roots:
            continue
        # Each module spends only its frozen share of the programme-wide
        # family. Within-module tests and record-length looks subdivide it.
        module_alpha = float(original_settings['alpha']) * float(original_settings['inference']['module_alpha_weights'][module])
        settings = {**original_settings, 'alpha': str(module_alpha)}
        outcome = {'assigned_roots': len(roots), 'root_seeds': [x['seed'] for x in roots],
            'completed_roots': sum(x['status'] == 'COMPLETED' for x in roots),
            'assigned_cases': sum(x['assigned_case_count'] for x in roots),
            'unavailable_cases': sum(y['status'] != 'COMPLETED' for x in roots for y in x['cases']),
            'acquisition_seconds': sum(x['acquisition_seconds'] for x in roots),
            'inference_allocation': {'programme_alpha': float(original_settings['alpha']),
                'module_weight': float(original_settings['inference']['module_alpha_weights'][module]),
                'module_alpha': module_alpha,
                'meaning': 'UNION_BOUND_ACROSS_DECLARED_MODULES; APPROXIMATE_INTERVALS_RETAIN_THEIR_OWN_LIMITS'}}
        outcome['work_accounting'] = {key: sum(root['work_accounting'][key] for root in roots)
            for key in ('native_force_evaluations', 'native_hessian_actions', 'native_energy_evaluations', 'wall_seconds')}
        outcome['work_accounting']['counts_are_lower_bounds'] = any(root['work_accounting']['counts_are_lower_bounds'] for root in roots)
        if 'receiver_study' in settings:
            from .receiver_campaign import synthesise
            outcome.update(synthesise(original_settings, module, roots, module_alpha))
            results[module] = outcome
            continue
        if module == 'M2':
            from empirical_lawhood.methods.model_free.memory import assess_root_memory, assess_root_segments
            options = settings['memory']
            groups = {(coordinate['id'], 'q-velocity-force-' + str(dimension) + suffix, order): []
                for coordinate in settings['native']['coordinates'] for dimension in options['observation_dimensions']
                for order in options['history_orders'] for suffix in ['', *['-age-' + str(age) for age in options['protocol_age_ticks']]]}
            for root in roots:
                found = {}
                for case in root['cases']:
                    if case['status'] != 'COMPLETED':
                        continue
                    for obs in case['observations']:
                        key = (case['coordinate']['id'], obs['observation_id'], obs['history_order'])
                        found[key] = obs['counts']
                for key in groups:
                    groups[key].append(found.get(key, {'root_id': str(root['seed']), 'status': 'UNRESOLVED',
                        'reason': 'ASSIGNED_NATIVE_OBSERVATION_UNAVAILABLE'}))
            outcome['memory'] = [{'coordinate': key[0], 'observation': key[1], 'history_order': key[2],
                'physical_sample_interval': float(settings['native']['timestep']) * options['stride'],
                'physical_lag_times': {str(lag): lag * float(settings['native']['timestep']) * options['stride'] for lag in options['lags']},
                'assessment': assess_root_memory(values, alpha=.5 * float(settings['alpha']) / max(1, len(groups)),
                    minimum_support=options['minimum_support'], receiver_oscillation=float(options['receiver_oscillation']),
                    tolerance=float(options['tolerance']), binning_allowance=float(options['binning_allowance']),
                    tail_allowance=float(options['tail_allowance']),
                    look_index=options['record_length_ladder'].index(options['record_ticks']), looks=len(options['record_length_ladder']))}
                for key, values in groups.items()]
            segment_groups = {(coordinate['id'], 'q-velocity-force-' + str(dimension)): []
                for coordinate in settings['native']['coordinates'] for dimension in options['observation_dimensions']}
            for root in roots:
                found = {(case['coordinate']['id'], observation['observation_id']): observation['counts']
                    for case in root['cases'] if case['status'] == 'COMPLETED'
                    for observation in case['stationarity']['segment_observations']}
                for key in segment_groups:
                    segment_groups[key].append(found.get(key, {'root_id': str(root['seed']), 'status': 'UNRESOLVED',
                        'reason': 'ASSIGNED_NATIVE_OBSERVATION_UNAVAILABLE'}))
            outcome['segment_drift'] = [{'coordinate': key[0], 'observation': key[1],
                'assessment': assess_root_segments(values,
                    alpha=.5 * float(settings['alpha']) / max(1, len(segment_groups)) / len(options['record_length_ladder']))}
                for key, values in segment_groups.items()]
            outcome['memory_error_allocation'] = {'history_fraction': .5, 'segment_fraction': .5,
                'record_length_looks': len(options['record_length_ladder']),
                'look_index': options['record_length_ladder'].index(options['record_ticks']),
                'scope': 'fixed complete history and segment menus share the module error allowance'}
            post_hoc = any(root.get('analysis_settings_changed', False) for root in roots)
            outcome['analysis_menu_scope'] = 'EXPOSED_POST_HOC' if post_hoc else 'AS_AUTHORED_FIXED_MENU'
            if post_hoc:
                # A new menu selected after seeing these retained observations
                # has no simultaneous guarantee over that adaptive selection.
                # Preserve useful fixed-menu arithmetic without promoting its
                # equivalence/detection labels into scientific qualification.
                for row in [*outcome['memory'], *outcome['segment_drift']]:
                    fixed = row['assessment']
                    row['assessment'] = {'status': 'EXPLORATORY_POST_HOC',
                        'independent_roots': len(roots),
                        'selection_adjusted_coverage': False,
                        'task_equivalence_qualified': False,
                        'distributional_detection_qualified': False,
                        'fixed_menu_calculation': fixed,
                        'interpretation': 'Bands and labels are calculations for this selected menu only; post-hoc selection is unadjusted and needs a frozen fresh-root confirmation.'}
        elif module == 'M1':
            rows = []
            for coordinate in settings['native']['coordinates']:
                for handoff in ('fixed', 'triggered'):
                    for recipe in _recipes(settings):
                        differences, indicators = [], []
                        for root in roots:
                            selected = [c for c in root['cases'] if c['coordinate']['id'] == coordinate['id']]
                            def delivery(arm):
                                case = next((c for c in selected if c['recipe'] == arm), None)
                                return int(case is not None and case['status'] == 'COMPLETED' and case['handoffs'][handoff]['service_available'])
                            indicators.append(delivery(recipe))
                            differences.append(delivery(recipe) - delivery('baseline'))
                        n = len(roots)
                        comparisons = len(settings['native']['coordinates']) * 2 * len(_recipes(settings))
                        allowance = math.sqrt(2 * math.log(2 * comparisons / float(settings['alpha'])) / n)
                        rows.append({'coordinate': coordinate['id'], 'handoff': handoff, 'recipe': recipe,
                            'assigned_service_availability_fraction': float(np.mean(indicators)), 'net_availability_probability_gain': float(np.mean(differences)),
                            'gain_interval': [max(-1., float(np.mean(differences)) - allowance), min(1., float(np.mean(differences)) + allowance)],
                            'margin': float(settings['formation']['probability_gain_margin']),
                            'scope': 'SIMULTANEOUS_PAIRED_ROOT_ASSIGNED_POLICY_AVAILABILITY_NOT_RESPONSE_ACCURACY'})
            outcome['preparation'] = rows
            outcome['physical_work'] = [{'root_seed': root['seed'], 'coordinate': case['coordinate']['id'],
                'recipe': case['recipe'], 'status': case['status'],
                'preparation': case.get('protocol_work'), 'coupling_exposure': case.get('coupling_exposure'),
                'handoffs': {name: {'preparation_prefix': value.get('preparation_protocol_work_prefix'),
                    'service_by_panel': value.get('service_protocol_work_by_panel', [])}
                    for name, value in case.get('handoffs', {}).items()},
                'failed_service_prefix': case.get('partial_native_accounting', {}).get('protocol_handoff_work'),
                'scope': 'SIGNED_PARAMETER_WORK_PER_PHYSICAL_PATH; EXPOSURE_AND_COMPUTATIONAL_COST_ARE_SEPARATE'}
                for root in roots for case in root['cases']]
        elif module == 'M3':
            from empirical_lawhood.methods.model_free_response import signed_error_account
            paired, preparation = [], []
            comparison_family = (len(settings['native']['coordinates']) * len(settings['response']['handoffs'])
                * len(_recipes(settings)) * len(settings['response']['methods']) * len(settings['response']['equal_ranks']))
            probability_halfwidth = math.sqrt(2 * math.log(2 * comparison_family / float(settings['alpha'])) / len(roots))
            for coordinate in settings['native']['coordinates']:
                for handoff in settings['response']['handoffs']:
                    for recipe in _recipes(settings):
                        for method in settings['response']['methods']:
                            for rank in settings['response']['equal_ranks']:
                                gains, losses = [], []
                                for root in roots:
                                    selected = [case for case in root['cases'] if case['coordinate']['id'] == coordinate['id'] and case['handoff'] == handoff]
                                    baseline = next((case for case in selected if case['recipe'] == 'baseline' and case['status'] == 'COMPLETED'), None)
                                    changed = next((case for case in selected if case['recipe'] == recipe and case['status'] == 'COMPLETED'), None)
                                    def model(case):
                                        return None if case is None else next((x for x in case['models'] if x['method'] == method
                                            and x['requested_rank'] == rank and not x['schedule_ticks'] and x.get('status') != 'UNRESOLVED'), None)
                                    first, last = model(baseline), model(changed)
                                    def delivered(case, estimate):
                                        return int(case is not None and estimate is not None and case['handoff_present']
                                            and estimate['adequate'] and all(x['present'] for x in case['survival']))
                                    gains.append(delivered(changed, last) - delivered(baseline, first))
                                    if first is not None and last is not None:
                                        losses.append(first['maximum_receiver_error'] - last['maximum_receiver_error'])
                                        paired.append({'seed': root['seed'], 'coordinate': coordinate['id'], 'handoff': handoff,
                                            'recipe': recipe, 'method': method, 'rank': rank,
                                            'signed_error': signed_error_account(baseline['native_endpoint'], first['predicted_endpoint'],
                                                changed['native_endpoint'], last['predicted_endpoint'])})
                                preparation.append({'coordinate': coordinate['id'], 'handoff': handoff, 'recipe': recipe,
                                    'method': method, 'rank': rank, 'assigned_roots': len(roots),
                                    'net_adequacy_probability_gain': float(np.mean(gains)),
                                    'gain_interval': [max(-1., float(np.mean(gains)) - probability_halfwidth),
                                        min(1., float(np.mean(gains)) + probability_halfwidth)],
                                    'gain_uncertainty': {'method': 'SIMULTANEOUS_PAIRED_ROOT_HOEFFDING',
                                        'paired_difference_range': [-1, 1], 'assigned_roots': len(roots),
                                        'family_size': comparison_family, 'family_alpha': float(settings['alpha']),
                                        'scope': 'ASSIGNED_POLICY_DELIVERY; NONENTRY_AND_UNAVAILABLE_RESPONSE_COUNT_AS_NO_DELIVERY'},
                                    'continuous_loss_gain_complete_pairs': None if not losses else float(np.mean(losses)),
                                    'complete_loss_pairs': len(losses), 'missing_loss_pairs': len(roots) - len(losses),
                                    'probability_margin': float(settings['formation']['probability_gain_margin']),
                                    'loss_margin': float(settings['formation']['continuous_loss_gain_margin']),
                                    'baseline_and_no_entry_permitted': True})
            outcome['preparation_service'] = preparation
            outcome['signed_preparation_contrasts'] = paired
            selector_groups = {(coordinate['id'], recipe, handoff, method, rank): []
                for coordinate in settings['native']['coordinates'] for recipe in _recipes(settings)
                for handoff in settings['response']['handoffs'] for method in settings['response']['methods']
                for rank in settings['response']['equal_ranks']}
            for root in roots:
                for case in root['cases']:
                    if case['status'] != 'COMPLETED':
                        continue
                    for selector in case['selectors']:
                        key = (case['coordinate']['id'], case['recipe'], case['handoff'], selector['method'], selector['rank'])
                        selector_groups[key].append(selector)
            outcome['selector_comparisons'] = []
            for key, selectors in selector_groups.items():
                complete = [row for row in selectors if row['selected_suffix_score'] is not None]
                schedules = sorted(set.intersection(*(set(row['withheld_suffix_scores']) for row in complete))) if complete else []
                fixed = {schedule: float(np.mean([row['withheld_suffix_scores'][schedule] for row in complete])) for schedule in schedules}
                selected_mean = None if not complete else float(np.mean([row['selected_suffix_score'] for row in complete]))
                outcome['selector_comparisons'].append({'coordinate': key[0], 'recipe': key[1], 'handoff': key[2],
                    'method': key[3], 'rank': key[4], 'assigned_roots': len(roots), 'evaluable_roots': len(complete),
                    'missing_roots': len(roots) - len(complete),
                    'status': 'ESTIMATED' if len(complete) == len(roots) else 'UNRESOLVED',
                    'mean_selected_suffix_error': selected_mean, 'mean_fixed_schedule_suffix_errors': fixed,
                    'best_fixed_exposed_mean': None if not fixed else min(fixed.values()),
                    'selected_beats_every_fixed_mean': len(complete) == len(roots) and bool(fixed) and selected_mean < min(fixed.values()),
                    'comparison_scope': 'OBSERVED_PREFIX_POLICY_VS_FIXED_SCHEDULES_ON_WITHHELD_SUFFIX; BEST_FIXED_IS_EXPOSED_ORACLE'})
        elif module == 'M6':
            from empirical_lawhood.methods.model_free_response import equilibrium_grid_estimate, equilibrium_importance_endpoint, equilibrium_variance_transport
            from empirical_lawhood.methods.retained_gaussian_response import trapezoid_weights
            groups = {coordinate['id']: {} for coordinate in settings['native']['coordinates']}
            for root in roots:
                for case in root['cases']:
                    if case['status'] == 'COMPLETED':
                        groups[case['coordinate']['id']][root['seed']] = case
            centers = [float(x) for x in settings['equilibrium']['centers']]
            stiffness = float(settings['equilibrium']['stiffness'])
            # Five marginal suppliers per coordinate and three paired
            # suppliers per coordinate contrast. These intervals remain
            # explicitly approximate; allocation does not repair their bias.
            family = 5 * len(groups) + 3 * max(0, len(groups) - 1)
            alpha = float(settings['alpha']) / family
            weights = trapezoid_weights(centers)
            outcome['family_allocation'] = {'families': family, 'alpha_per_family': alpha,
                'scope': 'all marginal grid/control/importance and paired direct/importance/moment-transport intervals; approximation premises remain explicit'}
            output_rows = []
            for key, cases in groups.items():
                absent = [r['seed'] for r in roots if r['seed'] not in cases]
                if absent:
                    output_rows.append({'coordinate': key, 'status': 'UNRESOLVED', 'missing_roots': absent,
                        'reason': 'ASSIGNED_ENSEMBLE_UNAVAILABLE_NO_COMPLETE_CASE_SUBSTITUTION'})
                    continue
                means = np.asarray([[x['mean'] for x in cases[root['seed']]['center_records']] for root in roots])
                controlled = np.asarray([[x['controlled_mean'] for x in cases[root['seed']]['center_records']] for root in roots])
                long = np.asarray([[x['reference_mean'] for x in cases[root['seed']]['center_records']] for root in roots])
                force = stiffness * (np.asarray(centers) - means)
                ref_force = stiffness * (np.asarray(centers) - long)
                controlled_force = stiffness * (np.asarray(centers) - controlled)
                importance_logs = np.asarray([[x['log_normalization_ratio'] for x in cases[root['seed']]['importance']] for root in roots])
                importance_means = np.asarray([[x['mean'] for x in cases[root['seed']]['importance']] for root in roots])
                inverse_temperature = 1 / float(cases[roots[0]['seed']]['coordinate']['temperature'])
                importance = equilibrium_importance_endpoint(importance_logs, centers, inverse_temperature, alpha=alpha)
                importance_grid = stiffness * (np.asarray(centers) - importance_means) @ weights
                importance.update(minimum_effective_sample_size=min(x['effective_sample_size'] for case in cases.values() for x in case['importance']),
                    maximum_normalized_weight=max(x['maximum_normalized_weight'] for case in cases.values() for x in case['importance']),
                    own_finite_grid_values=importance_grid.tolist(),
                    endpoint_minus_own_grid=(np.asarray(importance['root_targets']) - importance_grid).tolist(),
                    endpoint_grid_scope='CONSISTENCY_DIAGNOSTIC; NEITHER_INTERPOLATION_ERROR_NOR_OVERLAP_BOUND')
                estimator_targets = np.column_stack((force @ weights, force[:, ::2] @ trapezoid_weights(centers[::2]), ref_force @ weights,
                    controlled_force @ weights, importance['root_targets']))
                output_rows.append({'coordinate': key, 'status': 'ESTIMATED',
                    'finite_grid': equilibrium_grid_estimate(force, centers, alpha=alpha),
                    'coarse_grid': equilibrium_grid_estimate(force[:, ::2], centers[::2], alpha=alpha),
                    'longer_shared_path_reference': equilibrium_grid_estimate(ref_force, centers, alpha=alpha),
                    'fixed_control': equilibrium_grid_estimate(controlled_force, centers, alpha=alpha),
                    'native_residual_importance': importance,
                    'complete_estimator_mean_covariance': None if len(roots) < 2 else (np.cov(estimator_targets, rowvar=False, ddof=1) / len(roots)).tolist(),
                    'estimator_covariance_order': ['finite_grid', 'coarse_grid', 'longer_shared_path_reference', 'fixed_control', 'native_residual_importance_endpoint'],
                    'integrand': 'k*(center-native_receiver_mean)',
                    'canonical_disposition': 'UNRESOLVED_PREPARATION_AND_FINITE_STEP_MEASURE_BIAS'})
            outcome['equilibrium'] = output_rows
            if len(groups) >= 2 and all(len(cases) == len(roots) for cases in groups.values()):
                from empirical_lawhood.methods.joint_response.thermodynamics import finite_grid_mean_bridge
                ids = list(groups)
                paired = []
                for key in ids[1:]:
                    values = np.asarray([[[-stiffness * item['mean'] for item in groups[arm][root['seed']]['center_records']]
                        for arm in (ids[0], key)] for root in roots])
                    means = np.asarray([[[item['mean'] for item in groups[arm][root['seed']]['center_records']]
                        for arm in (ids[0], key)] for root in roots])
                    second_moments = np.asarray([[[item['short_second_moment'] for item in groups[arm][root['seed']]['center_records']]
                        for arm in (ids[0], key)] for root in roots])
                    inverse_temperatures = [1 / float(groups[arm][roots[0]['seed']]['coordinate']['temperature']) for arm in (ids[0], key)]
                    importance_logs = np.asarray([[[item['log_normalization_ratio'] for item in groups[arm][root['seed']]['importance']]
                        for arm in (ids[0], key)] for root in roots])
                    bridges = []
                    for root in roots:
                        first, last = groups[ids[0]][root['seed']], groups[key][root['seed']]
                        anchor = last['center_records'][0]['mean'] - first['center_records'][0]['mean']
                        # Different temperature coordinates retain their own
                        # inverse temperatures inside the variance contrast.
                        variance = np.asarray([item['variance'] / float(last['coordinate']['temperature']) for item in last['center_records']])
                        variance -= np.asarray([item['variance'] / float(first['coordinate']['temperature']) for item in first['center_records']])
                        bridge = finite_grid_mean_bridge(centers, trapezoid_weights(centers), anchor,
                            lambda s: float(np.interp(s, centers, variance)), beta=1., stiffness=stiffness)
                        bridges.append({'seed': root['seed'], **asdict(bridge)})
                    paired.append({'coordinates': [ids[0], key], 'signed_paired_finite_grid': equilibrium_grid_estimate(values, centers,
                        alpha=alpha),
                        'signed_paired_importance_endpoint': equilibrium_importance_endpoint(importance_logs, centers, inverse_temperatures, alpha=alpha),
                        'independent_root_variance_transport': equilibrium_variance_transport(means, second_moments,
                            centers, inverse_temperatures, stiffness=stiffness, alpha=alpha),
                        'anchored_variance_transport': {'root_estimates': bridges,
                            'mean': float(np.mean([bridge['value'] for bridge in bridges])),
                            'variance_of_mean': None if len(bridges) < 2 else float(np.var([bridge['value'] for bridge in bridges], ddof=1) / len(bridges)),
                            'scope': 'NATIVE_ANCHOR_AND_VARIANCE_WITH_PIECEWISE_LINEAR_CENTER_INTERPOLATION',
                            'variance_operand': 'WITHIN_RECORD_DDOF1_SAMPLE_VARIANCE_PLUGIN',
                            'finite_record_correlation_bias_bound': None,
                            'continuous_variance_interpolation_error_bound': None,
                            'canonical_measure_qualification': 'UNRESOLVED'},
                        'interpretation': 'SECOND_MINUS_FIRST_COORDINATE_FREE_ENERGY_CHANGE_CONTRAST'})
                outcome['paired_equilibrium'] = paired
        elif module == 'M5':
            from empirical_lawhood.methods.model_free.finite_population import compare_finite_population_estimators
            frames = {root['sampling']['frame_id'] for root in roots}
            if len(frames) != 1:
                raise ValueError('Population synthesis mixes different frozen frames')
            p = settings['population']
            if len(roots) != p['frame_size']:
                outcome['finite_population'] = {'status': 'UNRESOLVED',
                    'reason': 'COMPLETE_AUTHORED_ROOT_FRAME_REQUIRED', 'expected_roots': p['frame_size']}
            else:
                ordered = sorted(roots, key=lambda root: root['seed'])
                selected = [index for index, root in enumerate(ordered) if root['sampling']['audit_selected']]
                if len(selected) != p['audit_size']:
                    raise ValueError('Population census changes the authored SRS audit size')
                rows, contrasts = [], []
                recipes = _recipes(settings)
                contrast_count = len(recipes) - 1 if 'baseline' in recipes else 0
                alpha = float(settings['alpha']) / (len(settings['native']['coordinates']) * (len(recipes) + contrast_count))
                for coordinate in settings['native']['coordinates']:
                    def find(root, recipe):
                        return next(case for case in root['cases'] if case['coordinate']['id'] == coordinate['id'] and case['recipe'] == recipe)
                    for recipe in _recipes(settings):
                        cases = [find(root, recipe) for root in ordered]
                        aux = [case['auxiliary'] for case in cases]
                        values = [cases[index]['native_value'] for index in selected]
                        bounds = None if p['clip_bounds'] is None else tuple(float(v) for v in p['clip_bounds'])
                        comparison = compare_finite_population_estimators(aux, selected, values, value_bounds=bounds,
                            full_native_values=[case['native_value'] for case in cases] if p['mode'] == 'reveal_all' else None,
                            acquisition_mode=p['mode'], alpha=alpha)
                        assessment = comparison['residual_correction']
                        if any(not case['frame_member_defined'] for case in cases):
                            comparison['status'] = 'UNRESOLVED'
                            for estimate in (assessment, comparison['direct_sampling']):
                                estimate.update(status='UNRESOLVED', estimate=None,
                                    confidence_interval=None, variance_estimate=None, standard_error=None,
                                    design_unbiased_if_complete=False,
                                    reason='COMPLETE_FINITE_FRAME_PHYSICAL_PREPARATION_REQUIRED',
                                    missing_preparation_roots=[root['seed'] for root, case in zip(ordered, cases, strict=True) if not case['frame_member_defined']])
                        rows.append({'coordinate': coordinate['id'], 'recipe': recipe, 'assessment': assessment,
                            'estimator_comparison': comparison,
                            'auxiliary_native_hessian_actions': sum(case['auxiliary_hessian_actions'] for case in cases),
                            'native_force_evaluations': sum(case['native_force_evaluations'] for case in cases),
                            'native_future_calls_attempted': sum(case['native_calls_attempted'] for case in cases),
                            'native_future_calls_acquired': sum(case['native_calls_acquired'] for case in cases),
                            'actual_native_root_audits_omitted': sum(root['native_audit_root_omitted'] for root in roots),
                            'individual_evaluable_audits': sum(case['native_value'] is not None for case in cases),
                            'individual_within_requested_halfwidth': sum(case.get('individual_within_requested_halfwidth', False) for case in cases),
                            'full_frame_mean': None if any(case['native_value'] is None for case in cases) else float(np.mean([case['native_value'] for case in cases])),
                            'individual_target_halfwidth': float(p['individual_halfwidth'])})
                        if recipe != 'baseline' and 'baseline' in recipes:
                            baseline = [find(root, 'baseline') for root in ordered]
                            differences = [None if cases[index]['native_value'] is None or baseline[index]['native_value'] is None
                                else cases[index]['native_value'] - baseline[index]['native_value'] for index in selected]
                            contrast_bounds = None if bounds is None else (bounds[0] - bounds[1], bounds[1] - bounds[0])
                            full_differences = [None if case['native_value'] is None or base['native_value'] is None
                                else case['native_value'] - base['native_value'] for case, base in zip(cases, baseline, strict=True)]
                            contrast_comparison = compare_finite_population_estimators([a - b['auxiliary'] for a, b in zip(aux, baseline, strict=True)],
                                    selected, differences, value_bounds=contrast_bounds, acquisition_mode=p['mode'],
                                    full_native_values=full_differences if p['mode'] == 'reveal_all' else None,
                                    alpha=alpha)
                            contrast = contrast_comparison['residual_correction']
                            if any(not case['frame_member_defined'] for case in [*cases, *baseline]):
                                contrast_comparison['status'] = 'UNRESOLVED'
                                for estimate in (contrast, contrast_comparison['direct_sampling']):
                                    estimate.update(status='UNRESOLVED', estimate=None,
                                        confidence_interval=None, variance_estimate=None, standard_error=None,
                                        design_unbiased_if_complete=False,
                                        reason='COMPLETE_PAIRED_FINITE_FRAME_PREPARATION_REQUIRED')
                            contrasts.append({'coordinate': coordinate['id'], 'recipe': recipe, 'assessment': contrast,
                                              'estimator_comparison': contrast_comparison})
                outcome['finite_population'] = rows
                outcome['paired_finite_population_contrasts'] = contrasts
                outcome['frame_id'] = next(iter(frames))
                outcome['unit'] = 'WHOLE_PAIRED_INDEPENDENT_ROOT'
                outcome['acquisition_mode'] = p['mode']
                outcome['stage_interpretation'] = ('REVEAL_ALL_BENCHMARK_COUNTERFACTUAL_SAVINGS_ONLY'
                    if p['mode'] == 'reveal_all' else 'SPARSE_DEPLOYMENT_ACTUAL_OMITTED_ROOT_AUDITS')
        elif module == 'M7':
            from empirical_lawhood.methods.model_free.events import assess_first_passage, assess_paired_first_passage
            # The entry-history roster is frozen by the selected dependency.
            if len({root['entry_source'] for root in roots}) != 1:
                raise ValueError('First-passage roots mix different entry ensemble contracts')
            histories = _recipes(settings) if roots[0]['entry_source'] == 'M1' else ['declared-native-preparation']
            options = settings['events']
            pairs = options['history_pairs'] if roots[0]['entry_source'] == 'M1' else []
            horizon = options['horizon_ticks'] * float(settings['native']['timestep'])
            time_grid = [tick * float(settings['native']['timestep']) for tick in options['time_grid_ticks']]
            assignments = [{'root_id': str(root['seed']), 'replica': replica, 'weight': 1 / options['replicas']}
                for root in roots for replica in range(options['replicas'])]
            groups = {(coordinate['id'], history): [] for coordinate in settings['native']['coordinates'] for history in histories}
            for root in roots:
                found = {}
                for case in root['cases']:
                    if case['status'] == 'COMPLETED':
                        found[(case['coordinate']['id'], case['entry_history'])] = case['events']
                for key in groups:
                    groups[key].extend(found.get(key, [{'root_id': str(root['seed']), 'replica': replica, 'status': 'failed',
                        'event_time': None, 'observed_until': 0., 'event': None, 'weight': 1 / options['replicas'],
                        'entry_history': key[1], 'reason': 'ASSIGNED_NATIVE_ENTRY_UNAVAILABLE'} for replica in range(options['replicas'])]))
            families = len(options['target_events']) * (len(groups) + len(settings['native']['coordinates']) * len(pairs))
            alpha = float(settings['alpha']) / families
            outcome['first_passage'] = [{'coordinate': key[0], 'entry_history': key[1], 'target_event': target,
                'assessment': assess_first_passage(events, horizon=horizon, target_event=target,
                    time_grid=time_grid, alpha=alpha)} for key, events in groups.items() for target in options['target_events']]
            outcome['paired_history_contrasts'] = [{'coordinate': coordinate['id'], 'histories': pair, 'target_event': target,
                'assessment': assess_paired_first_passage([*groups[(coordinate['id'], pair[0])], *groups[(coordinate['id'], pair[1])]],
                    histories=pair, assignments=assignments, horizon=horizon, target_event=target,
                    time_grid=time_grid, alpha=alpha)} for coordinate in settings['native']['coordinates']
                for pair in pairs for target in options['target_events']]
            outcome['family_allocation'] = {'families': families, 'alpha_per_family': alpha,
                'scope': 'all declared coordinate/history/event marginals and paired contrasts; each contains its frozen time menu'}
            outcome['future_coupling'] = 'SAME_ROOT_AND_REPLICA_NOISE_STREAM_ACROSS_HISTORIES'
            outcome['event_time_scope'] = 'FIRST_TARGET_SET_ENTRY_OBSERVED_ON_NATIVE_TICK_GRID'
            outcome['physical_observation_timestep'] = float(settings['native']['timestep'])
            outcome['continuous_first_passage_qualified'] = False
        results[module] = outcome
    output = {'schema': 'matrix-model-free-synthesis.v1', 'settings_sha256': fingerprint,
        'modules': results, 'independent_unit': 'ASSIGNED_ROOT_WITH_NESTED_CASES',
        'supplier_classes': ['direct_measurement', 'exact_identity', 'deterministic_certificate', 'statistical_estimator'],
        'learned_training_dependencies': [], 'rubisco_scope': {'immediate': 'M50_Q1_Q6_NATIVE_ACTION_AND_PREPARATION_METHODS',
            'physical_time_required_for_memory': True, 'molecular_qualification': False}}
    json.dumps(output, allow_nan=False)
    return output
