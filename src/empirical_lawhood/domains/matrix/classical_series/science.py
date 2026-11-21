# SPDX-License-Identifier: MPL-2.0
"""Native, inspectable classical-matrix experiment calculations.

These calculations use the existing six-Hermitian-matrix potential and BAOAB
implementation.  They own no files, workers, custody, or historical verdicts.
Every configuration is a new experiment.  Historical capstone/E-series results
are never imported as newly observed outcomes.  All alternatives use one fixed
physical receiver and force chart so endpoint/preparation contrasts are defined.
"""
from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
from hashlib import sha256
import json
import math
from time import perf_counter
from typing import Mapping

import numpy as np

from empirical_lawhood.domains.matrix.matrix_history_analysis import algebra
from empirical_lawhood.domains.matrix.matrix_factor_response.science import (
    native_position_coordinates, native_position_lift,
)
from empirical_lawhood.domains.matrix.matrix_factor_response.origin_mechanics import (
    discrete_baoab_maps, scaled_origin_system, balance_io48, MatrixIO48Construction, IO48Unresolved,
)
from empirical_lawhood.domains.matrix.six_matrix_response.contracts import (
    BetaCouplingRule, MatrixIntegratorKind, MatrixPrecision,
    SixMatrixResponseModelFamilyMember, SixMatrixResponseNumericalView,
)
from empirical_lawhood.domains.matrix.six_matrix_response.history_preparation import (
    FOUR_FAMILY_PREPARATION_IDS,
)
from empirical_lawhood.domains.matrix.six_matrix_response.parameter_history import (
    MatrixParameterCoordinate, INITIAL_RULE_ID, PREPARATION_RULE_ID,
    initial_parameter_state, advance_parameter_pair, split_parameter_innovations,
)
from empirical_lawhood.domains.matrix.six_matrix_response.parameter_derivatives import (
    hessian_image, parameters, scheduled_force_step,
)
from empirical_lawhood.domains.matrix.six_matrix_response.simulation import (
    BAOABGradientCache, hermitian_noise,
)

PHASES = ('capstone-forecast', 'capstone-preparation', 'e1', 'e2', 'e3',
          'e4', 'e5', 'e6', 'sci01', 'sci02', 'derivations')
FAMILIES = dict(zip(('joint-increasing', 'joint-decreasing', 'x-first', 'y-first'),
                    FOUR_FAMILY_PREPARATION_IDS, strict=True))
METHODS = ('FULL', 'FACTOR', 'GENERIC_SLOW', 'SPECTRA', 'NORM_RADIUS',
           'ZERO', 'IO48', 'INPUT_KRYLOV', 'JOINT_KRYLOV')
ACQUISITION_SCHEMA = 'classical-series-acquisition.v1'
ANALYSIS_SCHEMA = 'classical-series-analysis.v1'
CALIBRATION_SCHEMA = 'classical-series-calibration.v1'
DEFAULT_CONFIG = {
    'phases': list(PHASES),
    'timestep': '0.001',
    'target_x': '0.6666666666666666666666666667',
    'target_y': '7.333333333333333333333333334',
    'decreasing_start': '8', 'mass': '0.5',
    'ramp_ticks': 256, 'handoff_tick': 256, 'history_ticks': 1152,
    'horizon_ticks': 128, 'observation_stride': 16, 'pulse_ticks': 16,
    'refresh_tick': 32, 'actions': ['FACTOR', 'GENERIC', 'COMPLEMENT', 'TRACE'],
    'panels': 2, 'reduced_rank': 24, 'joint_rank': 48,
    'family': 'joint-decreasing',
    'coordinates': [{'id': 'nominal', 'temperature': '1', 'friction': '1', 'cross_coupling': '1'}],
    'preparation_arms': ['baseline'],
    'amplitude': '0.01', 'radius_limit': '1000000',
    'response_tolerance': '0.1', 'numerical_tolerance': '0.01',
    'calibration_alpha': '0.05', 'ridge_penalty': '0.000001',
    'preparation_minimum_gain': '0.1', 'strict_win_margin': '0.1',
    'factor_leakage_maximum': '0.05', 'factor_angle_degrees': '15',
    'persistence_ticks': 32, 'survival_ticks': 128, 'occurrence_deadline': None,
    'derivation_blocks': 3, 'resolvent_imaginary': '1',
    'capstone_support_radius':'3','capstone_task_threshold':'0','capstone_horizon_tick':None,
    'relation_training_coordinates':[], 'relation_response_method':'FACTOR',
    'relation_ridge_candidates':['0.000001','0.001','1'], 'relation_folds':4,
}


def normalise_config(config: Mapping[str, object]) -> dict:
    """Resolve scientific defaults once; preserve the authored decimal strings."""
    if not isinstance(config, Mapping):
        raise TypeError('Classical settings must be a mapping')
    unknown = set(config) - set(DEFAULT_CONFIG)
    if unknown:
        raise ValueError('Unknown classical scientific settings: ' + ', '.join(sorted(unknown)))
    c = deepcopy(DEFAULT_CONFIG)
    c.update(deepcopy(dict(config)))
    if c['occurrence_deadline'] is None:
        c['occurrence_deadline'] = c['history_ticks']-c['survival_ticks']
    if c['capstone_horizon_tick'] is None:
        c['capstone_horizon_tick'] = min(64,c['horizon_ticks'])
    if type(c['capstone_horizon_tick']) is not int or not 1<=c['capstone_horizon_tick']<=c['horizon_ticks']:
        raise ValueError('Capstone horizon must be an acquired positive tick')
    if not isinstance(c['capstone_task_threshold'],str) or not Decimal(c['capstone_task_threshold']).is_finite():
        raise ValueError('Capstone task threshold requires a finite exact decimal string')
    if type(c['occurrence_deadline']) is not int or not 0<=c['occurrence_deadline']<=c['history_ticks']-c['survival_ticks']:
        raise ValueError('Occurrence deadline must leave the complete declared survival follow-up')
    for key in ('timestep', 'target_x', 'target_y', 'decreasing_start', 'mass', 'amplitude',
                'radius_limit', 'response_tolerance', 'numerical_tolerance', 'calibration_alpha',
                'ridge_penalty', 'preparation_minimum_gain', 'strict_win_margin',
                'factor_leakage_maximum', 'factor_angle_degrees', 'resolvent_imaginary','capstone_support_radius'):
        value = c[key]
        if not isinstance(value, str):
            raise TypeError(f'{key} requires an exact decimal string')
        d = Decimal(value)
        if not d.is_finite() or d <= 0:
            raise ValueError(f'{key} must be finite and positive')
    for key in ('ramp_ticks', 'handoff_tick', 'history_ticks', 'horizon_ticks', 'observation_stride',
                'pulse_ticks', 'refresh_tick', 'panels', 'reduced_rank', 'joint_rank',
                'persistence_ticks', 'survival_ticks', 'derivation_blocks'):
        if type(c[key]) is not int or c[key] < 1:
            raise ValueError(f'{key} requires a positive integer')
    if (c['handoff_tick'] < c['ramp_ticks'] or c['history_ticks'] < c['handoff_tick']
            or not c['pulse_ticks'] <= c['refresh_tick'] < c['horizon_ticks']
            or c['reduced_rank'] > 96 or c['joint_rank'] > 96
            or c['joint_rank'] < c['reduced_rank'] or c['family'] not in FAMILIES
            or Decimal(c['calibration_alpha']) >= 1):
        raise ValueError('Classical clocks, rank, family, or calibration probability are inconsistent')
    if Decimal(c['preparation_minimum_gain'])>1:
        raise ValueError('Preparation net probability gain must be at most one')
    for key, allowed in (('phases', PHASES), ('actions', ('FACTOR', 'GENERIC', 'COMPLEMENT', 'TRACE')),
                         ('preparation_arms', ('baseline', 'joint-increasing', 'joint-decreasing', 'x-first', 'y-first'))):
        values = c[key]
        if not isinstance(values, (list, tuple)) or not values or len(set(values)) != len(values) or set(values) - set(allowed):
            raise ValueError(f'{key} needs a nonempty unique supported selection')
        c[key] = list(values)
    if 'baseline' not in c['preparation_arms']:
        raise ValueError('The unchanged baseline preparation must remain assigned')
    if not isinstance(c['coordinates'], (list, tuple)) or not c['coordinates']:
        raise ValueError('Declare at least one native coordinate')
    seen = set()
    for row in c['coordinates']:
        if not isinstance(row, dict) or set(row) != {'id', 'temperature', 'friction', 'cross_coupling'}:
            raise ValueError('Coordinate requires id, temperature, friction and cross_coupling')
        if not isinstance(row['id'], str) or not row['id'] or row['id'] in seen:
            raise ValueError('Coordinate identities must be unique nonempty strings')
        seen.add(row['id'])
        for key in ('temperature', 'friction', 'cross_coupling'):
            if not isinstance(row[key], str) or not Decimal(row[key]).is_finite() or Decimal(row[key]) <= 0:
                raise ValueError('Native coordinate values require positive exact decimals')
    c['coordinates'] = list(c['coordinates'])
    selected=c['relation_training_coordinates']
    if not isinstance(selected,list) or len(set(selected))!=len(selected) or set(selected)-seen:
        raise ValueError('Relation training coordinates must be unique authored coordinate IDs')
    if c['relation_response_method'] not in METHODS or type(c['relation_folds']) is not int or c['relation_folds']<2:
        raise ValueError('Relation target method or whole-root fold count invalid')
    candidates=c['relation_ridge_candidates']
    if not isinstance(candidates,list) or not candidates or len(set(candidates))!=len(candidates) or any(
        not isinstance(v,str) or not Decimal(v).is_finite() or Decimal(v)<=0 for v in candidates):
        raise ValueError('Relation ridge candidates require distinct positive exact decimal strings')
    return c


def _fingerprint(value) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def acquisition_config_fingerprint(config):
    """Analysis-phase selection is not a new native numerical acquisition."""
    c = normalise_config(config)
    return _fingerprint({key:value for key,value in c.items() if key!='phases'})


def _rng(seed: int, purpose: int, panel: int = 0):
    return np.random.Generator(np.random.PCG64DXSM(np.random.SeedSequence([seed, purpose, panel])))


def _coordinate(c, row, family):
    member = SixMatrixResponseModelFamilyMember('classical-series.member.' + row['id'],
        Decimal(c['mass']), Decimal(c['mass']), Decimal(row['cross_coupling']),
        BetaCouplingRule.PUBLISHED_DETERMINISTIC)
    def view(multiplier):
        return SixMatrixResponseNumericalView(
            'classical-series.' + ('primary' if multiplier == 1 else 'fine'),
            MatrixIntegratorKind.BAOAB_UNDERDAMPED_LANGEVIN,
            Decimal(c['timestep']) / multiplier, 'dimensionless-langevin-time',
            Decimal(row['friction']), Decimal(row['temperature']), MatrixPrecision.COMPLEX128,
            'numpy.pcg64dxsm', '1.0.0', 'classical-series.root-purpose-seedsequence.v1', 1)
    ticks = tuple(sorted({0, c['history_ticks'], c['handoff_tick'],
                          *range(0, c['history_ticks'] + 1, c['observation_stride'])}))
    return MatrixParameterCoordinate('classical-series.coordinate.' + row['id'], 2, member,
        view(1), view(2), 'classical-series.physical-clock', FAMILIES[family],
        Decimal(c['target_x']), Decimal(c['target_y']), Decimal(c['decreasing_start']),
        c['ramp_ticks'], c['history_ticks'] - c['ramp_ticks'], ticks,
        INITIAL_RULE_ID, PREPARATION_RULE_ID)


def _native_guard(state, c):
    if not state.finite or np.linalg.norm(state.positions) > float(c['radius_limit']):
        raise FloatingPointError('NATIVE_NONFINITE_OR_DECLARED_RADIUS_LIMIT')


def _block_modes(axes):
    columns = []
    for matrix_index in range(6):
        for axis in axes:
            value = np.zeros((6, 4, 4), dtype='<c16')
            value[matrix_index] = axis
            columns.append(native_position_coordinates(value.reshape(2, 3, 4, 4)))
    return np.asarray(columns, dtype='<f8').T


def _instrument(c, seed):
    """A fixed physical chart shared by every endpoint and preparation arm.

    The reference Pauli factor is the explicit right product factor, not one
    chosen after viewing a trajectory.  This is a deliberate new matched-task
    adaptation of the original origin-dependent instrument.
    """
    axes = np.concatenate((np.eye(4, dtype='<c16')[None] / 2, algebra.RIGHT))
    u = _block_modes(axes)
    z = np.zeros_like(u.T)
    receivers = np.block([[u.T, z], [z, u.T]])
    rng = _rng(seed, 30)
    generic = rng.normal(size=96)
    factor = u[:, np.arange(24)%4 != 0] @ rng.normal(size=18)
    trace = u[:, ::4] @ rng.normal(size=6)
    complement = generic - u @ (u.T @ generic)
    selected = {'GENERIC': generic, 'FACTOR': factor, 'TRACE': trace, 'COMPLEMENT': complement}
    forces = np.column_stack([selected[name] / np.linalg.norm(selected[name]) for name in c['actions']])
    return np.asarray(forces, dtype='<f8'), np.asarray(receivers, dtype='<f8')


def _factor_measure(position, c):
    result = {}
    for sector, name in enumerate(('X', 'Y')):
        value = algebra.sector(position[sector])
        metrics = value['metrics']
        identified = value['identifiable']
        admitted = None if not identified else bool(
            metrics['associative_leakage'] <= float(c['factor_leakage_maximum'])
            and metrics['lie_leakage'] <= float(c['factor_leakage_maximum'])
            and metrics['factor_angle_degrees'] <= float(c['factor_angle_degrees']))
        result[name] = {'identified': identified, 'raw_admitted': admitted,
            'spectrum': value['spectrum'].tolist(), 'low': value['low'].tolist(),
            'associative_leakage': metrics.get('associative_leakage'),
            'lie_leakage': metrics.get('lie_leakage'),
            'factor_fit_angle_degrees': metrics.get('factor_angle_degrees')}
    return result


def _history(c, row, family, coarse, bridge):
    coordinate = _coordinate(c, row, family)
    primary = fine = initial_parameter_state(coordinate)
    caches = (BAOABGradientCache(), BAOABGradientCache())
    observed = []
    origin = None
    wanted = set(coordinate.observation_ticks)
    for tick in range(c['history_ticks'] + 1):
        if tick in wanted:
            observed.append({'tick': tick, 'primary': _factor_measure(primary.positions, c),
                             'fine': _factor_measure(fine.positions, c)})
        if tick == c['handoff_tick']:
            origin = (primary, fine)
        if tick < c['history_ticks']:
            primary, _, fine = advance_parameter_pair(primary, fine, coordinate=coordinate,
                coarse_step=tick+1, coarse_noise=coarse[tick], bridge_noise=bridge[tick],
                primary_cache=caches[0], fine_cache=caches[1])
            _native_guard(primary, c)
            _native_guard(fine, c)
    return coordinate, origin, observed


def _hessian(state, member):
    selected = parameters(state, member)
    columns = [native_position_coordinates(hessian_image(state.positions,
        native_position_lift(np.eye(96)[index]), selected)) for index in range(96)]
    h = np.asarray(columns, dtype='<f8').T
    residual = float(np.linalg.norm(h - h.T))
    if residual > 1e-8 * max(1., float(np.linalg.norm(h))):
        raise FloatingPointError('NATIVE_HESSIAN_SYMMETRY_FAILED')
    return (h + h.T) / 2


def _orthogonal_prefix(h, seeds, rank):
    """Double-reorthogonalized block prefix with an explicit selected rank.

    Seed columns are reduced by SVD only for algebraic dependence.  Rank caps
    and discarded seed norm are retained; they are never hidden certification.
    """
    basis = np.empty((len(h), 0))
    block = np.array(seeds, dtype=float,copy=True)
    while basis.shape[1] < rank and block.shape[1]:
        for _ in range(2):
            block -= basis @ (basis.T @ block)
        u, s, _ = np.linalg.svd(block, full_matrices=False)
        if not len(s) or s[0] <= 1e-13:
            break
        count = min(rank-basis.shape[1], int(np.sum(s > 1e-12*s[0])))
        if not count:
            break
        fresh = u[:, :count]
        basis = np.column_stack((basis, fresh))
        block = h @ fresh
    return basis, float(np.linalg.norm(seeds - basis @ (basis.T @ seeds)))


def _bases(c, state, h, forces, receivers):
    values, vectors = np.linalg.eigh(h)
    selected = {'GENERIC_SLOW': vectors[:, np.argsort(np.abs(values), kind='stable')[:c['reduced_rank']]]}
    unavailable = {}
    raw = algebra.sector(state.positions[1])
    if raw['identifiable'] and raw['metrics']['associative_leakage'] <= float(c['factor_leakage_maximum']) and raw['metrics']['lie_leakage'] <= float(c['factor_leakage_maximum']) and raw['metrics']['factor_angle_degrees'] <= float(c['factor_angle_degrees']):
        axes = np.concatenate((np.eye(4, dtype='<c16')[None]/2, raw['factor']))
        selected['FACTOR'] = _block_modes(axes)
    else:
        unavailable['FACTOR'] = 'Y_FACTOR_UNIDENTIFIABLE_OR_UNADMITTED_AT_ASSIGNED_HANDOFF'
    spectral, radial = [], []
    for matrix in state.positions.reshape(6, 4, 4):
        eig, vec = np.linalg.eigh(matrix)
        spectral.append(np.asarray([np.outer(v, v.conj()) for v in vec.T]))
        centered = matrix - np.trace(matrix)*np.eye(4)/4
        length = np.linalg.norm(centered)
        radial.append(None if length <= 1e-12 else np.stack((np.eye(4)/2, centered/length)))
        if np.min(np.diff(eig)) <= 1e-10:
            unavailable['SPECTRA'] = 'NATIVE_MATRIX_SPECTRAL_CHART_DEGENERATE'
    def assemble(per_matrix):
        columns = []
        for i, axes in enumerate(per_matrix):
            for axis in axes:
                q = np.zeros((6,4,4), dtype='<c16'); q[i] = axis
                columns.append(native_position_coordinates(q.reshape(2,3,4,4)))
        return np.asarray(columns).T
    if 'SPECTRA' not in unavailable:
        selected['SPECTRA'] = assemble(spectral)
    if all(value is not None for value in radial):
        selected['NORM_RADIUS'] = assemble(radial)
    else:
        unavailable['NORM_RADIUS'] = 'NATIVE_RADIAL_CHART_UNRESOLVED'
    selected['INPUT_KRYLOV'], input_loss = _orthogonal_prefix(h, forces, c['reduced_rank'])
    seeds = np.column_stack((forces, receivers[:24, :96].T))
    selected['JOINT_KRYLOV'], joint_loss = _orthogonal_prefix(h, seeds, c['joint_rank'])
    return selected, unavailable, {'input_seed_discarded_norm': input_loss,
        'joint_seed_discarded_norm': joint_loss, 'joint_position_rank': selected['JOINT_KRYLOV'].shape[1],
        'input_position_rank': selected['INPUT_KRYLOV'].shape[1]}


def _response_acquisition(c, coordinate, origins, forces, receivers, coarse, bridge):
    """Acquire both signed branches and a common HOLD with paired nested views."""
    n = c['horizon_ticks']; actions = len(c['actions'])
    directions = [native_position_lift(forces[:, i]) for i in range(actions)]
    signed = [[origins[view] for _ in range(2*actions+1)] for view in range(2)]
    caches = [[BAOABGradientCache() for _ in group] for group in signed]
    native = [np.zeros((actions, n+1, 48)), np.zeros((actions, n+1, 48))]
    refresh = None
    gradient_evaluations = 0
    for tick in range(n):
        halves = split_parameter_innovations(coordinate, coarse[tick], bridge[tick])
        for view, noises in enumerate(((coarse[tick],), halves)):
            numerical = coordinate.primary_view if view == 0 else coordinate.fine_view
            for noise in noises:
                for index in range(2*actions+1):
                    a = min(index//2, actions-1)
                    amplitude = (float(c['amplitude']) * (1 if index%2 == 0 else -1)
                                 if index < 2*actions and tick < c['pulse_ticks'] else 0.)
                    signed[view][index] = scheduled_force_step(signed[view][index],
                        direction=directions[a], amplitude=amplitude, member=coordinate.member,
                        numerical_view=numerical, next_alpha_tilde_x=float(c['target_x']),
                        next_alpha_tilde_y=float(c['target_y']), standardized_noise=noise,
                        gradient_cache=caches[view][index])
                    _native_guard(signed[view][index], c)
                    gradient_evaluations += 1  # Cache reuses the preceding endpoint gradient.
            for a in range(actions):
                plus, minus = signed[view][2*a:2*a+2]
                chord = np.concatenate((native_position_coordinates((plus.positions-minus.positions)/2),
                                        native_position_coordinates((plus.momenta-minus.momenta)/2)))
                native[view][a, tick+1] = receivers @ chord
        if tick+1 == c['refresh_tick']:
            refresh = [_hessian(group[-1], coordinate.member) for group in signed]
    return native, refresh, gradient_evaluations + 2*(2*actions+1)


def acquire_native_root(config: Mapping[str, object], seed: int, *, calibration: dict|None=None) -> dict:
    """One assigned independent root; all coordinates, arms and panels are nested.

    Purpose-separated PCG64DXSM streams are fixed by seed before any acquisition.
    Prefix-dependent mechanical operands are built before future noise is read.
    A caller may pass the result to arbitrarily many retained analyses without
    repeating native work.  Unavailable cases stay in the complete assignment.
    """
    c = normalise_config(config)
    if type(seed) is not int or seed < 0:
        raise ValueError('Root seed must be a nonnegative integer')
    _validate_freeze(c,calibration,seed)
    from .capstones import capstone_preparation_commitment,capstone_response_commitment
    began = perf_counter()
    forces,receivers = _instrument(c,seed)
    capstone_package=None if calibration is None else calibration.get('capstones')
    planned={}
    for arm in c['preparation_arms']:
        family=c['family'] if arm=='baseline' else arm
        for row in c['coordinates']:
            initial=initial_parameter_state(_coordinate(c,row,family))
            descriptor=receivers[:24,:96]@native_position_coordinates(initial.positions)
            planned[(arm,row['id'])]={'preparation_initial_descriptor':descriptor.tolist(),
                'capstone_preparation_commitment':capstone_preparation_commitment(c,seed,row,arm,descriptor,forces,capstone_package)}
    coarse_rng, bridge_rng = _rng(seed, 10), _rng(seed, 11)
    coarse = np.asarray([hermitian_noise(rng=coarse_rng, q=2) for _ in range(c['history_ticks'])])
    bridge = np.asarray([hermitian_noise(rng=bridge_rng, q=2) for _ in range(c['history_ticks'])])
    cases = []
    for arm in c['preparation_arms']:
        family = c['family'] if arm == 'baseline' else arm
        for row in c['coordinates']:
            case = {'coordinate': deepcopy(row), 'arm': arm, 'family': family, 'status': 'UNAVAILABLE',**planned[(arm,row['id'])]}
            start = perf_counter()
            try:
                coordinate, origins, observed = _history(c, row, family, coarse, bridge)
                hessians = [_hessian(state, coordinate.member) for state in origins]
                basis_info = [_bases(c, state, h, forces, receivers) for state, h in zip(origins, hessians, strict=True)]
                origin_operands = {'origin_hessians': [h.tolist() for h in hessians],
                    'origin_states': [np.concatenate((native_position_coordinates(state.positions),
                        native_position_coordinates(state.momenta))).tolist() for state in origins],
                    'bases': [{name: value.tolist() for name, value in entry[0].items()} for entry in basis_info],
                    'unavailable_methods': [entry[1] for entry in basis_info],
                    'basis_witnesses': [entry[2] for entry in basis_info],
                    'io48': [_io_origin(c,row,h,forces,receivers,view) for view,h in enumerate(hessians)]}
                case.update(origin_operands)
                case['causal_prefix_sha256'] = _fingerprint(origin_operands)
                case['factor_observations'] = observed
                case['pre_response_commitment'] = _precommit(c,seed,case,calibration)
                descriptors=(receivers[:24,:96]@np.asarray(case['origin_states'])[:,:96].T).T
                case['capstone_response_commitment']=capstone_response_commitment(c,seed,row,arm,descriptors,forces,capstone_package)
                case['panels'] = []
                native_calls = 3*c['history_ticks'] + 2
                for panel in range(c['panels']):
                    rng, brng = _rng(seed, 20, panel), _rng(seed, 21, panel)
                    future = np.asarray([hermitian_noise(rng=rng, q=2) for _ in range(c['horizon_ticks'])])
                    bridges = np.asarray([hermitian_noise(rng=brng, q=2) for _ in range(c['horizon_ticks'])])
                    native, refresh, count = _response_acquisition(c, coordinate, origins, forces, receivers, future, bridges)
                    native_calls += count
                    case['panels'].append({'panel': panel,
                        'native_response': [x.tolist() for x in native],
                        'refresh_hessians': [x.tolist() for x in refresh]})
                case.update(status='COMPLETED', native_force_evaluations=native_calls,
                            hessian_column_actions=96*2*(1+c['panels']))
            except (FloatingPointError, np.linalg.LinAlgError) as exc:
                case.update(status='UNAVAILABLE', reason=type(exc).__name__ + ': ' + str(exc))
            case['native_seconds'] = perf_counter()-start
            cases.append(case)
    result = {'schema': ACQUISITION_SCHEMA, 'seed': seed, 'config': c,
        'config_sha256': acquisition_config_fingerprint(c), 'freeze_sha256':None if calibration is None else calibration['freeze_sha256'], 'status': 'COMPLETED' if all(x['status']=='COMPLETED' for x in cases) else 'PARTIAL',
        'independent_units': 1, 'assigned_cases': len(c['coordinates'])*len(c['preparation_arms']),
        'cases': cases, 'forces': forces.tolist(), 'receivers': receivers.tolist(),
        'native_seconds': perf_counter()-began,
        'causal_policy': 'ORIGIN_OPERANDS_BEFORE_FUTURE; REFRESH_FROM_HOLD_AT_CHECKPOINT',
        'evidence_scope': 'NEW_AUTHORED_CLASSICAL_MATRIX_EXPERIMENT_NOT_HISTORICAL_REPLICATION'}
    incomplete = sum(case['status']!='COMPLETED' for case in cases)
    result['work_accounting'] = {
        'reported_force_evaluations':sum(case.get('native_force_evaluations',0) for case in cases),
        'reported_hessian_column_actions':sum(case.get('hessian_column_actions',0) for case in cases),
        'unavailable_case_counts':incomplete,
        'counts_are_lower_bounds':bool(incomplete),
        'cost_status':'PARTIAL_FAILED_ATTEMPTS_REQUIRE_RECEIPTS' if incomplete else 'COMPLETE_NATIVE_CALL_CENSUS',
        'all_attempted_case_wall_seconds_included':True,
        'timing_scope':'ACQUISITION_WALL_TIME_INCLUDES_PREPARATION_FACTOR_HESSIAN_REDUCTION_AND_FUTURE_WORK',
    }
    json.dumps(result, allow_nan=False)
    return result


def _scales(c):
    t = np.arange(1, c['horizon_ticks']+1)*float(c['timestep'])
    pulse = np.minimum(t, c['pulse_ticks']*float(c['timestep']))
    amplitude = float(c['amplitude'])
    return np.column_stack((amplitude*pulse*(t-pulse/2), amplitude*pulse))


def _phase_lift(basis):
    z = np.zeros_like(basis)
    return np.block([[basis, z], [z, basis]])


def _linear(c, coordinate, h, basis, forces, receiver, refresh_h, view):
    dt = float(c['timestep'])/(view+1)
    decay = np.exp(-float(coordinate['friction'])*dt)
    reduced = basis.T@h@basis
    reduced = (reduced+reduced.T)/2
    transition, b = discrete_baoab_maps(reduced, basis.T@forces*float(c['amplitude']),
                                      timestep=dt, decay=decay)
    fresh_h = basis.T@refresh_h@basis
    fresh_h = (fresh_h+fresh_h.T)/2
    refreshed, _ = discrete_baoab_maps(fresh_h, basis.T@forces*float(c['amplitude']),
                                     timestep=dt, decay=decay)
    lift = _phase_lift(basis)
    output = receiver@lift
    state = np.zeros((2*basis.shape[1], forces.shape[1]))
    repaired = state.copy()
    values, updated, states = [], [], []
    multiplier = view+1
    for tick in range(c['horizon_ticks']*multiplier+1):
        if tick%multiplier == 0:
            values.append((output@state).T)
            updated.append((output@repaired).T)
            states.append(state.copy())
        if tick < c['horizon_ticks']*multiplier:
            force = b if tick < c['pulse_ticks']*multiplier else 0.
            state = transition@state+force
            repaired = (transition if tick < c['refresh_tick']*multiplier else refreshed)@repaired+force
    return (np.stack(values, axis=1), np.stack(updated, axis=1), states,
            transition, refreshed, lift)


def _score(error, scales):
    # The 24 components in a block are nested receiver coordinates.
    normal = error[:, 1:]/np.repeat(scales, 24, axis=1)[None, :, :]
    blocks = np.sqrt(np.sum(normal.reshape(len(normal), len(scales), 2, 24)**2, axis=-1))
    return {'maximum': float(blocks.max()), 'curve_rms': float(np.sqrt(np.mean(normal**2))),
            'endpoint': float(np.sqrt(np.mean(normal[:, -1]**2)))}, normal


def _features(case):
    h = np.asarray(case['origin_hessians'][0])
    at = next(x for x in case['factor_observations'] if x['tick'] == case['handoff_tick'])
    factor = at['primary']['Y']
    row = case['coordinate']
    baseline = [1., math.log1p(float(np.linalg.norm(h, 2))), math.log(float(row['temperature'])),
                math.log(float(row['friction'])), math.log(float(row['cross_coupling']))]
    spectrum = factor['spectrum']
    if factor['associative_leakage'] is None or factor['lie_leakage'] is None:
        return {'baseline':baseline,'structure':None}
    extra = [float(factor['associative_leakage']), float(factor['lie_leakage']),
             float(spectrum[3]-spectrum[2])/max(abs(spectrum[-1]), 1e-30)]
    return {'baseline': baseline, 'structure': baseline+extra}


def _analyse_case(c, case, forces, receivers, *, selected_methods=METHODS):
    scales = _scales(c)
    result = {'coordinate': case['coordinate'], 'arm': case['arm'], 'status': case['status']}
    if case['status'] != 'COMPLETED':
        result['reason'] = case.get('reason', 'ORIGINAL_NATIVE_UNAVAILABLE')
        return result, {}
    case = dict(case, handoff_tick=c['handoff_tick'])
    result['features'] = _features(case)
    native_views = [np.asarray(panel['native_response']) for panel in case['panels']]
    discrepancy = max(_score(panel[0]-panel[1], scales)[0]['maximum'] for panel in native_views)
    result['paired_view_discrepancy'] = discrepancy
    result['numerical_policy_pass'] = bool(discrepancy <= float(c['numerical_tolerance']))
    result['numerical_policy_scope'] = 'DECLARED_TWO_VIEW_DISCREPANCY_NOT_A_CONTINUUM_ERROR_BOUND'
    result['method_scores'] = {name: [] for name in METHODS}
    result['method_nonuse'] = deepcopy(case['unavailable_methods'])
    cache = {}
    for view in range(2):
        h = np.asarray(case['origin_hessians'][view])
        bases = {name: np.asarray(value) for name, value in case['bases'][view].items()}
        bases['FULL'] = np.eye(96)
        for panel in case['panels']:
            pi = panel['panel']
            native = np.asarray(panel['native_response'][view])
            refresh = np.asarray(panel['refresh_hessians'][view])
            for name in selected_methods:
                if name == 'ZERO':
                    frozen = updated = np.zeros_like(native)
                    states = [np.empty((0, len(c['actions']))) for _ in range(c['horizon_ticks']+1)]
                    full = None
                elif name == 'IO48':
                    io = case['io48'][view]
                    if io['status'] != 'COMPLETED':
                        result['method_nonuse'][view]['IO48'] = io['reason']
                        continue
                    full = _io_linear(c,case['coordinate'],io,forces,receivers,refresh,view)
                    frozen,updated,states = full[:3]
                elif name not in bases:
                    continue
                else:
                    full = _linear(c, case['coordinate'], h, bases[name], forces, receivers, refresh, view)
                    frozen, updated, states = full[:3]
                frozen_score, error = _score(frozen-native, scales)
                refresh_score, refresh_error = _score(updated-native, scales)
                result['method_scores'][name].append({'view': ('PRIMARY','FINE')[view], 'panel': pi,
                    'frozen': frozen_score, 'refresh': refresh_score,
                    'frozen_adequate': frozen_score['maximum'] <= float(c['response_tolerance']),
                    'refresh_adequate': refresh_score['maximum'] <= float(c['response_tolerance'])})
                cache[(view, pi, name)] = {'native': native, 'frozen': frozen, 'refresh': updated,
                    'error': error, 'refresh_error': refresh_error, 'states': states, 'linear': full,
                    'basis': bases.get(name), 'refresh_hessian': refresh}
    return result, cache


def _occurrence(c, case):
    traces = []
    if case['status'] != 'COMPLETED':
        return {'status': 'UNAVAILABLE', 'assigned_traces': 4, 'traces': []}
    for view in ('primary', 'fine'):
        for sector in ('X', 'Y'):
            rows, previous = [], None
            for sample in case['factor_observations']:
                obs = sample[view][sector]
                adjacent = None if previous is None or not obs['identified'] else algebra.principal_angle(
                    np.asarray(previous['low']), np.asarray(obs['low']))
                moving = None if obs['raw_admitted'] is None else bool(obs['raw_admitted'] and
                    (adjacent is None or adjacent <= float(c['factor_angle_degrees'])))
                rows.append({'tick': sample['tick'], 'moving': moving, 'low': obs['low'],
                             'adjacent_angle': adjacent, 'raw': obs['raw_admitted']})
                previous = obs if obs['identified'] else None
            causal = []
            for index, row in enumerate(rows):
                begin = row['tick']-c['persistence_ticks']
                trailing = [x for x in rows[:index+1] if x['tick'] >= begin]
                if row['tick'] == 0 and row['raw'] is True:
                    causal.append(index)
                elif trailing and trailing[0]['tick'] == begin and all(x['moving'] is True for x in trailing):
                    causal.append(index)
            causal = [index for index in causal if rows[index]['tick'] <= c['occurrence_deadline']]
            origin = causal[0] if causal else None
            unknown_before = origin is not None and any(x['moving'] is None for x in rows[:origin])
            survival = None
            if origin is not None and not unknown_before:
                start = rows[origin]
                follow = [x for x in rows[origin:] if x['tick'] <= start['tick']+c['survival_ticks']]
                flags = [None if x['moving'] is None else x['moving'] and algebra.principal_angle(
                    np.asarray(start['low']), np.asarray(x['low'])) <= 30. for x in follow]
                if False in flags:
                    survival = False
                elif follow[-1]['tick'] == start['tick']+c['survival_ticks'] and all(x is True for x in flags):
                    survival = True
            traces.append({'view': view.upper(), 'sector': sector,
                'occurrence': True if causal else (None if any(x['moving'] is None and x['tick'] <= c['occurrence_deadline'] for x in rows) else False),
                'occurrence_deadline':c['occurrence_deadline'],
                'first_observed_admission_tick': None if origin is None else rows[origin]['tick'],
                'first_origin_established': origin is not None and not unknown_before,
                'joint_survival': survival, 'unknown_samples': sum(x['moving'] is None for x in rows),
                'sample_count': len(rows)})
    return {'status': 'OBSERVED', 'assigned_traces': 4, 'traces': traces}


def _paired_contrasts(c, acquired, analysed, caches):
    from empirical_lawhood.methods.joint_response import signed_contrast_account, propagation_accounting
    rows = []
    horizon_indices = sorted({c['horizon_ticks'], min(c['horizon_ticks'], max(c['refresh_tick']+1, 64))})
    for lo_index, low in enumerate(acquired['cases']):
        for hi_index, high in enumerate(acquired['cases']):
            lc, hc = low['coordinate'], high['coordinate']
            if (low['arm'] != high['arm'] or lc['temperature'] != hc['temperature']
                    or lc['friction'] != hc['friction']
                    or Decimal(lc['cross_coupling']) >= Decimal(hc['cross_coupling'])):
                continue
            for view in range(2):
                for panel in range(c['panels']):
                    for method in ('FULL','INPUT_KRYLOV','JOINT_KRYLOV','FACTOR'):
                        key=(view,panel,method)
                        left,right=caches[lo_index].get(key),caches[hi_index].get(key)
                        integrals={}
                        if left is not None and right is not None:
                            before_curve=(right['frozen']-right['native'])-(left['frozen']-left['native'])
                            after_curve=(right['refresh']-right['native'])-(left['refresh']-left['native'])
                            dt=float(c['timestep'])
                            for horizon in horizon_indices:
                                normalization=np.trapezoid(np.vstack((np.zeros(2),_scales(c)[:horizon])),dx=dt,axis=0)
                                integrals[horizon]=tuple(np.trapezoid(curve[:,:horizon+1],dx=dt,axis=1)/np.repeat(normalization,24) for curve in (before_curve,after_curve))
                        for horizon in horizon_indices:
                            for action,action_name in enumerate(c['actions']):
                                for bi,block in enumerate(('POSITION','MOMENTUM')):
                                    cell={'arm':low['arm'],'low':lc['id'],'high':hc['id'],
                                        'view':('PRIMARY','FINE')[view],'panel':panel,'method':method,
                                        'horizon':horizon,'action':action_name,'block':block}
                                    if left is None or right is None:
                                        rows.append({**cell,'status':'UNEVALUABLE',
                                            'reason':'ASSIGNED_NATIVE_ENDPOINT_OR_METHOD_UNAVAILABLE'})
                                        continue
                                    sl=slice(24*bi,24*(bi+1))
                                    e_l,e_h=left['error'][action,horizon-1,sl],right['error'][action,horizon-1,sl]
                                    r_l,r_h=left['refresh_error'][action,horizon-1,sl],right['refresh_error'][action,horizon-1,sl]
                                    before,after=signed_contrast_account(e_l,e_h),signed_contrast_account(r_l,r_h)
                                    integral_before,integral_after=(value[action,sl] for value in integrals[horizon])
                                    rows.append({**cell,
                                        'status':'EVALUABLE' if analysed[lo_index]['numerical_policy_pass'] and analysed[hi_index]['numerical_policy_pass'] else 'NUMERICAL_UNRESOLVED',
                                        'endpoint_energy_before':before.endpoint_energy,'endpoint_energy_after':after.endpoint_energy,
                                        'alignment_before':before.signed_alignment,'alignment_after':after.signed_alignment,
                                        'contrast_energy_before':before.contrast_energy,'contrast_energy_after':after.contrast_energy,
                                        'both_endpoints_improve':bool(after.low_energy<before.low_energy and after.high_energy<before.high_energy),
                                        'contrast_worsens':bool(after.contrast_energy>before.contrast_energy),
                                        'integrated_contrast_error_before':float(np.linalg.norm(integral_before)),
                                        'integrated_contrast_error_after':float(np.linalg.norm(integral_after)),
                                        'integrated_target_rule':'TRAPEZOID_OF_SIGNED_PHYSICAL_RESPONSE_NORMALIZED_BY_INTEGRATED_ACTUATOR_SCALE;SECONDARY',
                                        'identity_residual':max(before.identity_residual,after.identity_residual),
                                        'low_signed_error_before':e_l.tolist(),'high_signed_error_before':e_h.tolist(),
                                        'low_signed_error_after':r_l.tolist(),'high_signed_error_after':r_h.tolist(),
                                        'signed_integrated_contrast_error_before':integral_before.tolist(),
                                        'signed_integrated_contrast_error_after':integral_after.tolist()})
    accounting = []
    for i, case in enumerate(acquired['cases']):
        if case['status'] != 'COMPLETED':
            continue
        for key, reduced in caches[i].items():
            view, panel, method = key
            if method not in ('INPUT_KRYLOV','JOINT_KRYLOV','FACTOR'):
                continue
            full = caches[i][(view,panel,'FULL')]
            checkpoint = c['refresh_tick']
            for horizon in horizon_indices:
                result = propagation_accounting(full['linear'][4], reduced['linear'][4], reduced['linear'][5],
                    full['states'][checkpoint], reduced['states'][checkpoint],
                    (horizon-checkpoint)*(view+1))
                scale = np.repeat(_scales(c)[horizon-1],24)
                receiver = np.asarray(acquired['receivers'])
                accounting.append({'coordinate':case['coordinate']['id'], 'arm':case['arm'],
                    'view':('PRIMARY','FINE')[view], 'panel':panel,'method':method,'horizon':horizon,
                    'inherited_receiver_norm':float(np.linalg.norm((receiver@result.inherited)/scale[:,None])),
                    'generated_receiver_norm':float(np.linalg.norm((receiver@result.generated)/scale[:,None])),
                    'inherited_receiver_vectors':((receiver@result.inherited)/scale[:,None]).tolist(),
                    'generated_receiver_vectors':((receiver@result.generated)/scale[:,None]).tolist(),
                    'signed_cross_term':2*float(np.vdot((receiver@result.inherited)/scale[:,None],(receiver@result.generated)/scale[:,None]).real),
                    'reconstruction_error':float(result.reconstruction_error),
                    'projected_map_difference_norm':float(np.linalg.norm(reduced['linear'][5].T@full['linear'][4]@reduced['linear'][5]-reduced['linear'][4]))})
    return rows, accounting


def validate_acquisition(config, acquired):
    c = normalise_config(config)
    if (not isinstance(acquired, dict) or acquired.get('schema') != ACQUISITION_SCHEMA
            or acquired.get('config_sha256') != acquisition_config_fingerprint(c)
            or acquisition_config_fingerprint(acquired.get('config',{})) != acquisition_config_fingerprint(c)
            or acquired.get('independent_units') != 1):
        raise ValueError('Original acquisition does not match its complete authored scientific settings')
    expected = {(arm,row['id']) for arm in c['preparation_arms'] for row in c['coordinates']}
    actual = [(row['arm'],row['coordinate']['id']) for row in acquired['cases']]
    if len(actual) != len(expected) or set(actual) != expected or acquired['assigned_cases'] != len(expected):
        raise ValueError('Acquisition loses or duplicates an assigned nested case')
    expected_forces,expected_receivers=_instrument(c,acquired['seed'])
    if not np.array_equal(np.asarray(acquired['forces']),expected_forces) or not np.array_equal(np.asarray(acquired['receivers']),expected_receivers):
        raise ValueError('Retained physical force/receiver instrument was substituted')
    coordinates={row['id']:row for row in c['coordinates']}
    for case in acquired['cases']:
        if case['coordinate']!=coordinates[case['coordinate']['id']] or case['family']!=(c['family'] if case['arm']=='baseline' else case['arm']):
            raise ValueError('Native case changes its coordinate or preparation family')
        if case['status'] not in ('COMPLETED','UNAVAILABLE'):
            raise ValueError('Unknown native case status')
        if case['status'] != 'COMPLETED':
            continue
        operands = {key:case[key] for key in ('origin_hessians','origin_states','bases','unavailable_methods','basis_witnesses','io48')}
        if _fingerprint(operands) != case['causal_prefix_sha256']:
            raise ValueError('Retained causal prefix changed')
        commitment = case.get('pre_response_commitment')
        if not isinstance(commitment,dict) or _fingerprint({k:v for k,v in commitment.items() if k!='commitment_sha256'})!=commitment.get('commitment_sha256') or commitment.get('causal_prefix_sha256')!=case['causal_prefix_sha256']:
            raise ValueError('Root before-response commitment is absent or changed')
        if len(case['panels']) != c['panels'] or [p['panel'] for p in case['panels']] != list(range(c['panels'])):
            raise ValueError('Native panel census changed')
        for panel in case['panels']:
            values = np.asarray(panel['native_response'])
            if values.shape != (2,len(c['actions']),c['horizon_ticks']+1,48) or not np.isfinite(values).all():
                raise ValueError('Native response has incomplete or nonfinite receiver/time/view operands')
    return c


def _base_analysis(c, acquired, *, selected_methods=METHODS):
    validate_acquisition(c, acquired)
    forces, receivers = np.asarray(acquired['forces']),np.asarray(acquired['receivers'])
    if forces.shape != (96,len(c['actions'])) or receivers.shape != (48,192):
        raise ValueError('Native instrument geometry changed')
    analysed, caches = [], []
    for case in acquired['cases']:
        result, cache = _analyse_case(c,case,forces,receivers,selected_methods=selected_methods)
        analysed.append(result); caches.append(cache)
    return analysed,caches


def _root_loss(analysed, method='INPUT_KRYLOV', arm='baseline', coordinate_ids=None):
    rows = [case for case in analysed if case['arm']==arm and
            (coordinate_ids is None or case['coordinate']['id'] in coordinate_ids)]
    if not rows or any(case['status']!='COMPLETED' or not case['numerical_policy_pass'] or not case['method_scores'][method] for case in rows):
        return None
    return max(score['frozen']['maximum'] for case in rows for score in case['method_scores'][method])


def _root_features(analysed, kind, arm='baseline', coordinate_ids=None):
    rows = [case for case in analysed if case['arm']==arm and case['status']=='COMPLETED'
            and (coordinate_ids is None or case['coordinate']['id'] in coordinate_ids)]
    return None if not rows or any(case['features'][kind] is None for case in rows) else np.mean([case['features'][kind] for case in rows],axis=0)


def calibrate_native_roots(config: Mapping[str,object], acquisitions: Mapping[str,dict]) -> dict:
    """Freeze TRAIN fits, CAL residual quantiles, and a TRAIN-only E5 nominee.

    Missing roots count in both original denominator and calibration quantile.
    A missing CAL response has infinite residual, encoded as a vacuous radius.
    The held CONF roots and E6 outcomes cannot enter this operation.
    """
    raw = dict(config)
    train_seeds = tuple(raw.pop('training_seeds', ()))
    cal_seeds = tuple(raw.pop('calibration_seeds', ()))
    c = normalise_config(raw)
    if (not train_seeds or not cal_seeds or len(set(train_seeds))!=len(train_seeds)
            or len(set(cal_seeds))!=len(cal_seeds) or set(train_seeds)&set(cal_seeds)
            or any(type(x) is not int or x<0 for x in (*train_seeds,*cal_seeds))):
        raise ValueError('Training and calibration require distinct complete assigned root rosters')
    by_seed = {}
    summaries_by_seed = {}
    prep_losses = {}
    for value in acquisitions.values():
        if value['seed'] in by_seed or value['seed'] not in set(train_seeds)|set(cal_seeds):
            raise ValueError('Calibrator has duplicate or unassigned roots')
        summary = summarise_native_root(c,value) if value.get('schema')==ACQUISITION_SCHEMA else value
        if summary.get('schema')!='classical-series-summary.v1' or summary.get('config_sha256')!=acquisition_config_fingerprint(c):
            raise ValueError('Calibrator requires an original compatible native summary')
        summaries_by_seed[value['seed']] = summary
        by_seed[value['seed']] = summary['case_summaries']
        prep_losses[value['seed']] = summary['preparation_contrast_losses']
    # Fit the nominal coordinate only. Transfer coordinates remain held out of
    # fitting and calibration even when their native controls are acquired.
    nominal_ids = [row['id'] for row in c['coordinates'] if Decimal(row['temperature'])==1
                   and Decimal(row['friction'])==1 and Decimal(row['cross_coupling'])==1]
    selected_ids = nominal_ids
    models = {}
    for kind in ('baseline','structure'):
        xs,ys = [],[]
        for seed in train_seeds:
            rows = by_seed.get(seed,[])
            y = _root_loss(rows,coordinate_ids=selected_ids)
            x = _root_features(rows,kind,coordinate_ids=selected_ids)
            if y is not None and x is not None:
                xs.append(x); ys.append(math.log1p(y))
        if not xs:
            models[kind] = {'status':'FIT_UNAVAILABLE','radius':None,'training_usable':0}
            continue
        x,y = np.asarray(xs),np.asarray(ys)
        scale = np.maximum(np.sqrt(np.mean(x*x,axis=0)),1.)
        x = x/scale
        ridge = float(c['ridge_penalty'])*np.eye(x.shape[1]); ridge[0,0]=0.
        coefficient = np.linalg.solve(x.T@x+ridge,x.T@y)
        residuals = []
        for seed in cal_seeds:
            rows = by_seed.get(seed,[])
            target = _root_loss(rows,coordinate_ids=selected_ids)
            feature = _root_features(rows,kind,coordinate_ids=selected_ids)
            residuals.append(math.inf if target is None or feature is None else
                abs(math.log1p(target)-float(feature/scale@coefficient)))
        order = math.ceil((len(cal_seeds)+1)*(1-float(c['calibration_alpha'])))
        radius = math.inf if order>len(residuals) else sorted(residuals)[order-1]
        models[kind] = {'status':'FROZEN','coefficients':coefficient.tolist(),'feature_scale':scale.tolist(),
            'radius':None if not math.isfinite(radius) else radius,'vacuous':not math.isfinite(radius),
            'training_usable':len(ys),'calibration_assigned':len(cal_seeds),
            'calibration_usable':sum(math.isfinite(v) for v in residuals),'order_statistic':order,
            'target':'log1p(maximum_normalized_INPUT_KRYLOV_error)','coordinate_ids':selected_ids}
    arm_scores = {}
    for arm in c['preparation_arms']:
        scores = [prep_losses.get(seed,{}).get(arm) for seed in train_seeds]
        arm_scores[arm] = None if any(v is None for v in scores) else float(np.mean(scores))
    baseline = arm_scores['baseline']
    # The authored minimum gain is a NET ADEQUACY PROBABILITY, not loss units.
    # Missing assigned roots remain undelivered in the development denominator.
    delivery_rates={arm:float(np.mean([prep_losses.get(seed,{}).get(arm) is not None
        and prep_losses[seed][arm]<=float(c['response_tolerance']) for seed in train_seeds]))
        for arm in c['preparation_arms']}
    available=[arm for arm in c['preparation_arms'] if arm!='baseline'
        and arm_scores[arm] is not None and baseline is not None
        and delivery_rates[arm]-delivery_rates['baseline']>=float(c['preparation_minimum_gain'])
        and arm_scores[arm]<=baseline]
    nominee=min(available,key=lambda arm:(-delivery_rates[arm],arm_scores[arm],arm)) if available else None
    result = {'schema':CALIBRATION_SCHEMA,'config_sha256':acquisition_config_fingerprint(c),'training_seeds':list(train_seeds),
        'calibration_seeds':list(cal_seeds),'models':models,'nominee':nominee,'training_arm_losses':arm_scores,
        'training_arm_delivery_rates':delivery_rates,
        'preparation_probability_headroom':1.-delivery_rates['baseline'],
        'preparation_minimum_gain_units':'NET_ADEQUACY_PROBABILITY',
        'preparation_target':'JOINT_RECEIVER_HIGH_MINUS_LOW_REFRESHED_CONTRAST_MAX_ERROR',
        'preparation_status':'NOMINATED' if nominee is not None else 'NONDISCRIMINATING_OR_UNAVAILABLE',
        'evidence_scope':'NEW_FROZEN_CALIBRATION_NO_HISTORICAL_E4_QUALIFICATION',
        'coverage_premises':'Independent exchangeable complete-root scores in the declared nominal population; transfer has no inherited guarantee'}
    result['parameter_relation']=_fit_parameter_relation(c,by_seed,train_seeds,cal_seeds)
    from .capstones import freeze_capstones
    result['capstones']=freeze_capstones(c,summaries_by_seed,train_seeds,cal_seeds) if len(nominal_ids)==1 else None
    result['capstone_status']='FROZEN_PACKAGE' if result['capstones'] is not None else 'NOT_ENTERED_NO_UNIQUE_NOMINAL_COORDINATE'
    result['freeze_sha256'] = _fingerprint(result)
    return result


def _preparation_contrast_loss(c, acquired, caches, arm):
    values = []
    for i, low in enumerate(acquired['cases']):
        if low['arm'] != arm:
            continue
        for j, high in enumerate(acquired['cases']):
            lc,hc = low['coordinate'],high['coordinate']
            if (high['arm']!=arm or lc['temperature']!=hc['temperature'] or lc['friction']!=hc['friction']
                    or Decimal(lc['cross_coupling'])>=Decimal(hc['cross_coupling'])):
                continue
            if low['status']!='COMPLETED' or high['status']!='COMPLETED':
                return None
            for case in (low,high):
                if any(_score(np.asarray(panel['native_response'][0])-np.asarray(panel['native_response'][1]),_scales(c))[0]['maximum']>float(c['numerical_tolerance']) for panel in case['panels']):
                    return None
            for view in range(2):
                for panel in range(c['panels']):
                    key = (view,panel,'JOINT_KRYLOV')
                    if key not in caches[i] or key not in caches[j]:
                        return None
                    delta = caches[j][key]['refresh_error']-caches[i][key]['refresh_error']
                    values.append(float(np.sqrt(np.sum(delta.reshape(len(c['actions']),c['horizon_ticks'],2,24)**2,axis=-1)).max()))
    return max(values) if values else None


def _derivation_readout(c, acquired):
    """Apply the operator identities to native Hessians; use an explicit canonical
    Gaussian control for the thermodynamic identity, never the nonequilibrium
    matrix history as a canonical sampling assumption.
    """
    from scipy.linalg import null_space
    from empirical_lawhood.methods.joint_response import (
        acquire_block_krylov, galerkin_response, finite_update_response,
        finite_auxiliary_self_energy, finite_grid_mean_bridge, finite_grid_from_means,
    )
    from empirical_lawhood.methods.retained_gaussian_response import HarmonicBath
    complete = [case for case in acquired['cases'] if case['status']=='COMPLETED']
    if not complete:
        return {'status':'UNAVAILABLE','reason':'NO_NATIVE_HESSIAN'}
    case = complete[0]
    h = np.asarray(case['origin_hessians'][0])
    b = np.asarray(acquired['forces'])
    cp = np.asarray(acquired['receivers'])[:24,:96].T
    ports = np.column_stack((b,cp))
    prefix = acquire_block_krylov(h,ports,blocks=c['derivation_blocks'])
    z = complex(0.,float(c['resolvent_imaginary']))
    answer = galerkin_response(prefix,cp,z,inputs=b)
    inverse = np.linalg.solve(z*np.eye(96)-h,np.eye(96))
    exact = cp.T@inverse@b
    actual_error = float(np.linalg.norm(exact-answer.estimate,2))
    q = prefix.basis
    complement = null_space(q.conj().T)
    if complement.shape[1]:
        sigma = finite_auxiliary_self_energy(complement.conj().T@h@complement,q.conj().T@h@complement,z)
    else:
        sigma = np.zeros((q.shape[1],q.shape[1]),dtype=complex)
    head = np.linalg.solve(z*np.eye(q.shape[1])-q.conj().T@h@q-sigma,q.conj().T@b)
    schur = cp.T@q@head
    changed = np.asarray(case['panels'][0]['refresh_hessians'][0])
    delta = (changed-h+changed.T-h.T)/2
    eig,u = np.linalg.eigh(delta)
    updated = finite_update_response(exact,cp.T@inverse@u,u.T@inverse@u,u.T@inverse@b,np.diag(eig))
    native_updated = cp.T@np.linalg.solve(z*np.eye(96)-changed,b)
    # Scalar restrained Gaussians: native U_i(x)=a_i(x-m_i)^2/2,
    # same beta and finite restraint k(x-s)^2/2; integrals are analytic.
    beta,k=1.3,2.
    aw,am,mw,mm=3.,5.,-.2,.4
    grid=np.asarray([-.7,-.1,.35,.9]); weights=np.asarray([.3,-.1,.5,.7])
    muw=lambda s:(aw*mw+k*s)/(aw+k)
    mum=lambda s:(am*mm+k*s)/(am+k)
    variance=1/(beta*(am+k))-1/(beta*(aw+k))
    bridge=finite_grid_mean_bridge(grid,weights,mum(grid[0])-muw(grid[0]),lambda s:variance,
                                  beta=beta,stiffness=k,energy_scale=1000.)
    direct=finite_grid_from_means(grid,weights,mum(grid),muw(grid),stiffness=k,energy_scale=1000.)
    # Same static Schur complement, different exact memory. Retain a fully
    # declared analytical control; no positive native K is manufactured.
    bath1=HarmonicBath(np.asarray([[2.]]),np.asarray([[1.]]),np.asarray([[1.]]))
    bath2=HarmonicBath(np.asarray([[2.]]),np.asarray([[2.]]),np.asarray([[4.]]))
    return {'status':'COMPUTED','native_operator':'REAL_SYMMETRIC_PHYSICAL_HESSIAN_NOT_BAOAB_MAP',
        'minimum_native_hessian_eigenvalue':float(np.linalg.eigvalsh(h)[0]),
        'prefix_rank':int(q.shape[1]),'prefix_operator_actions':prefix.action_count,
        'dense_hessian_operator_actions_already_charged':96,
        'resolvent_error':actual_error,'resolvent_residual_bound':float(answer.bound),
        'resolvent_enclosure_contains_oracle':actual_error<=float(answer.bound)+1e-10,
        'finite_tail_dense_oracle_error':float(np.linalg.norm(schur-exact)),
        'finite_operator_update_rank':int(np.linalg.matrix_rank(delta)),
        'finite_operator_update_width':int(delta.shape[1]),
        'finite_operator_update_singular_values':np.linalg.svd(delta,compute_uv=False).tolist(),
        'finite_operator_update_rank_tolerance':float(np.linalg.norm(delta,2)*max(delta.shape)*np.finfo(float).eps),
        'finite_operator_update_error':float(np.linalg.norm(updated-native_updated)),
        'finite_update_locality_claim':False,'tail_scope':'EXACT_ACQUIRED_DENSE_COMPLEMENT_CONTROL; NO_CHEAP_TAIL_CLAIM',
        'canonical_mean_bridge':{'direct':direct,'from_anchor_and_variance':bridge.value,
            'absolute_error':abs(direct-bridge.value),'anchor_term':bridge.anchor_term,
            'variance_term':bridge.variance_term,'canonical_native_matrix_claim':False,
            'scope':'ANALYTIC_GAUSSIAN_CONFORMANCE_CONTROL_WITH_SIGNED_NONUNIFORM_WEIGHTS'},
        'static_dynamic_separation':{'scope':'EXACT_HARMONIC_CONTROL',
            'static_equal':bool(np.array_equal(bath1.effective_stiffness,bath2.effective_stiffness)),'memory_at_one_first':float(bath1.memory(1.)[0,0]),
            'memory_at_one_second':float(bath2.memory(1.)[0,0])},
        'retained_gaussian_elimination':_retained_gaussian_controls(h,cp,q),
        'actual_native_work_avoided':0}


def _frozen_forecast(c, acquired, analysed, calibration):
    if calibration is None:
        return {'status':'NOT_ESTABLISHED','reason':'NO_SEPARATE_FROZEN_TRAIN_CAL_SUPPLIER'}
    _validate_freeze(c,calibration,acquired['seed'])
    if acquired.get('freeze_sha256')!=calibration['freeze_sha256']:
        raise ValueError('CONF acquisition did not consume this original freeze before native futures')
    for case in acquired['cases']:
        if case['status']=='COMPLETED' and case.get('pre_response_commitment')!=_precommit(c,acquired['seed'],case,calibration):
            raise ValueError('Original before-response root forecast commitment differs')
    rows=[]
    for coordinate in c['coordinates']:
        ids=[coordinate['id']]
        target=_root_loss(analysed,coordinate_ids=ids)
        case=next(row for row in acquired['cases'] if row['arm']=='baseline' and row['coordinate']['id']==coordinate['id'])
        item={'coordinate':coordinate,'target':target,'models':{},
              'pre_response_commitment_sha256':case.get('pre_response_commitment',{}).get('commitment_sha256')}
        forecasts=case.get('pre_response_commitment',{}).get('forecasts',{})
        for kind in calibration['models']:
            fixed=forecasts.get(kind,{'status':'UNAVAILABLE','admitted':False,'upper':None,'point':None})
            upper,point=fixed['upper'],fixed['point']
            admitted=fixed['admitted']
            complete=all(row['status']=='COMPLETED' and row['numerical_policy_pass']
                for row in analysed if row['arm']=='baseline' and row['coordinate']['id'] in ids)
            adequate=target is not None and complete and target<=float(c['response_tolerance'])
            item['models'][kind]={**fixed,
                'covered':None if target is None or upper is None else target<=upper,
                'actual_adequate':bool(adequate),'delivered_service':bool(admitted and adequate),
                'false_admission':bool(admitted and target is not None and complete and not adequate),
                'unresolved_admitted_future':bool(admitted and (target is None or not complete)),
                'point_absolute_error':None if target is None or point is None else abs(point-target)}
        rows.append(item)
    return {'status':'FROZEN_RULE_EVALUATED','freeze_sha256':calibration['freeze_sha256'],'coordinates':rows,
        'independent_units':1,'all_assigned_coordinates_retained':True,
        'scope':'CAUSAL_ERROR_FORECAST_AND_ADMISSION_ADAPTATION; NO_ORIGINAL_CAPSTONE_REPLICATION'}


def analyse_native_root(config: Mapping[str,object], acquired: dict, *, calibration: dict|None=None) -> dict:
    """Reanalyse retained original numerical operands without native contact.

    Stage names are historical question anchors, not inherited qualifications.
    They remain explicit when their selected prerequisites were not supplied.
    """
    c=normalise_config(config)
    began=perf_counter()
    stage_set=set(c['phases'])
    mechanics=bool(stage_set & {'e2','e3','e4','e5','e6','sci01','sci02'})
    if mechanics:
        methods=(METHODS if 'e2' in stage_set else
            ('FULL','INPUT_KRYLOV','JOINT_KRYLOV','FACTOR') if stage_set & {'e4','sci01','sci02'} else
            ('INPUT_KRYLOV','JOINT_KRYLOV') if 'e5' in stage_set else ('INPUT_KRYLOV',))
        if c['relation_training_coordinates']:
            methods=tuple(dict.fromkeys((*methods,c['relation_response_method'])))
        analysed,caches=_base_analysis(c,acquired,selected_methods=methods)
    else:
        validate_acquisition(c,acquired)
        analysed,caches=[],[]
    stages={}
    if 'e1' in stage_set:
        stages['e1']={'status':'DESCRIPTIVE_COMPLETE_CENSUS','independent_units':1,
            'cases':[{'coordinate':case['coordinate']['id'],'arm':case['arm'],**_occurrence(c,case)}
                     for case in acquired['cases']],
            'historical_reproduction':False,
            'scope':'SAME_ALGEBRA_ADMISSION; DECLARED_NEW_POPULATION_AND_CLOCK'}
    if 'e2' in stage_set:
        stages['e2']={'status':'MECHANICAL_RESPONSE_COMPARISON','independent_units':1,'cases':analysed,
            'method_menu':list(METHODS),'instrument':'FIXED_REFERENCE_FACTOR_PHYSICAL_CHART',
            'historical_reproduction':False,'io48_status':'ORIGIN_FINITE_HORIZON_BALANCED_PHASE_CONTROL_WITH_RETAINED_NONUSE'}
    if stage_set & {'e4','sci01','sci02'}:
        contrasts,accounting=_paired_contrasts(c,acquired,analysed,caches)
        if 'e4' in stage_set:
            stages['e4']={'status':'OBSERVED' if contrasts else 'NOT_ESTABLISHED','independent_units':1,
                'assigned_nested_cells':len(contrasts),'cells':contrasts,
                'reason':None if contrasts else 'NO_ASSIGNED_MATCHED_CROSS_COUPLING_ENDPOINTS',
                'historical_e4_qualification':'UNCHANGED_NOT_ESTABLISHED'}
        if 'sci01' in stage_set:
            evaluable=[x for x in contrasts if x['status']=='EVALUABLE']
            stages['sci01']={'status':'DESCRIPTIVE_MATCHED_ACCOUNTING','independent_units':1,
                'assigned_cells':len(contrasts),'evaluable_cells':len(evaluable),
                'endpoint_improvement_contrast_reversals':sum(x['both_endpoints_improve'] and x['contrast_worsens'] for x in evaluable),
                'census':[{'method':name,'evaluable':sum(x['method']==name for x in evaluable),
                    'reversals':sum(x['method']==name and x['both_endpoints_improve'] and x['contrast_worsens'] for x in evaluable)}
                    for name in ('FULL','INPUT_KRYLOV','JOINT_KRYLOV','FACTOR')],
                'inherited_generated':accounting,
                'historical_197_of_240_is_not_a_pass_target':True}
        if 'sci02' in stage_set:
            stages['sci02']={'status':'FROZEN_VERSUS_CAUSAL_REFRESH_CONTROL','independent_units':1,
                'causal_cutoff_tick':c['refresh_tick'],'native_force_calls_avoided':0,
                'native_force_evaluations':sum(x.get('native_force_evaluations',0) for x in acquired['cases']),
                'hessian_column_actions':sum(x.get('hessian_column_actions',0) for x in acquired['cases']),
                'counts_are_lower_bounds':bool(any(x['status']!='COMPLETED' for x in acquired['cases'])),
                'cost_status':'PARTIAL_FAILED_ATTEMPTS_REQUIRE_RECEIPTS' if any(x['status']!='COMPLETED' for x in acquired['cases']) else 'COMPLETE_NATIVE_CALL_CENSUS',
                'scope':'CAUSAL_OPERATOR_REPAIR_AND_REPRESENTATION_ACCOUNTING; DENSE_REFERENCE_ACQUIRED',
                'measured_saving_claim':False}
    if stage_set & {'e3','e6'}:
        forecast=_frozen_forecast(c,acquired,analysed,calibration)
        for phase in stage_set & {'e3'}:
            stages[phase]=deepcopy(forecast)
        if 'e6' in stage_set:
            selected=[row for row in forecast.get('coordinates',[]) if Decimal(row['coordinate']['temperature']) in (Decimal('1.125'),Decimal('3.25')) and Decimal(row['coordinate']['friction'])==1 and Decimal(row['coordinate']['cross_coupling'])==1]
            both_regimes=sorted(Decimal(row['coordinate']['temperature']) for row in selected)==[Decimal('1.125'),Decimal('3.25')]
            stages['e6']={'status':'EMPIRICAL_FROZEN_TRANSFER' if both_regimes else 'NOT_ESTABLISHED',
                'independent_units':1,'coordinates':selected,
                'reason':None if both_regimes else 'REQUIRES_BOTH_T1.125_AND_T3.25_AND_FROZEN_CALIBRATION',
                'coverage_guarantee_transported':False,'recalibration_performed':False,
                'freeze_sha256':None if calibration is None else calibration['freeze_sha256']}
    if stage_set & {'e4','e6'} and c['relation_training_coordinates']:
        relation=_parameter_relation_readout(c,acquired,analysed,calibration)
        for phase in stage_set & {'e4','e6'}:
            stages[phase]['parameter_relation']=relation
            stages[phase]['global_relation_distinct_from_signed_contrasts']=True
        if 'e4' in stage_set and relation['status']=='FROZEN_RELATION_EVALUATED':
            stages['e4']['contrast_status']=stages['e4']['status']
            stages['e4']['status']='FROZEN_PARAMETER_RELATION_EVALUATED'
    if 'e5' in stage_set:
        losses={arm:_preparation_contrast_loss(c,acquired,caches,arm) for arm in c['preparation_arms']}
        nominee=None if calibration is None else calibration.get('nominee')
        available=nominee is not None and losses.get(nominee) is not None and losses['baseline'] is not None
        if calibration is not None:
            _frozen_forecast(c,acquired,analysed,calibration)  # One original freeze/role validation.
        outcome={'status':'PAIRED_CONFIRMATION' if available else 'NOT_ENTERED','independent_units':1,
            'nominee':nominee,'joint_contrast_losses':losses,
            'target':'JOINT_RECEIVER_HIGH_MINUS_LOW_REFRESHED_CONTRAST_MAX_ERROR',
            'gain':bool(available and losses[nominee]<=float(c['response_tolerance'])<losses['baseline']),
            'harm':bool(available and losses['baseline']<=float(c['response_tolerance'])<losses[nominee]),
            'gain_units':'NET_ADEQUACY_PROBABILITY',
            'continuous_loss_improvement':None if not available else losses['baseline']-losses[nominee],
            'reason':None if available else 'NO_TRAIN_ONLY_JOINT_TARGET_NOMINEE_OR_COMPLETE_CONFIRMATION',
            'historical_reproduction':False,'historical_e5_nonentry_unchanged':True,
            'all_preparation_costs_and_unsuccessful_arms_retained':True}
        for phase in stage_set & {'e5'}:
            stages[phase]=deepcopy(outcome)
    if stage_set & {'capstone-forecast','capstone-preparation'}:
        from .capstones import assess_capstones
        capstones=assess_capstones(c,acquired,None if calibration is None else calibration.get('capstones'))
        if 'capstone-forecast' in stage_set:
            stages['capstone-forecast']=capstones['forecast']
        if 'capstone-preparation' in stage_set:
            stages['capstone-preparation']=capstones['preparation']
    if 'derivations' in stage_set:
        stages['derivations']=_derivation_readout(c,acquired)
    result={'schema':ANALYSIS_SCHEMA,'seed':acquired['seed'],'config_sha256':acquisition_config_fingerprint(c),
        'status':'COMPLETE_READOUT','stages':stages,'census':{'independent_units':1,
            'assigned_cases':acquired['assigned_cases'],'native_completed':sum(x['status']=='COMPLETED' for x in acquired['cases']),
            'native_unavailable':sum(x['status']!='COMPLETED' for x in acquired['cases']),
            'numerical_policy_pass':sum(x.get('numerical_policy_pass',False) for x in analysed)},
        'native_seconds':acquired['native_seconds'],'analysis_seconds':perf_counter()-began,
        'evidence_scope':'NEW_MATRIX_EXPERIMENT_READOUT; NESTED_CELLS_NOT_INDEPENDENT_UNITS',
        'actual_native_work_avoided':0}
    json.dumps(result,allow_nan=False)
    return result


def _io_origin(c, coordinate, h, forces, receivers, view):
    steps=c['horizon_ticks']*(view+1)
    if steps>256:
        return {'status':'UNAVAILABLE','reason':'IO48_HORIZON_OUTSIDE_DECLARED_256_STEP_SCOPE',
            'requested_steps':steps,'supported_maximum_steps':256,'witnesses':{}}
    dt=float(c['timestep'])/(view+1)
    scales=_scales(c)[-1]
    m,b,out,state_units,output_units=scaled_origin_system(h,forces*float(c['amplitude']),receivers,
        timestep=dt,decay=np.exp(-float(coordinate['friction'])*dt),
        position_scale=float(scales[0]),momentum_scale=float(scales[1]))
    try:
        reduced=balance_io48(m,b,out,c['horizon_ticks']*(view+1),MatrixIO48Construction('classical-series.io48'))
    except IO48Unresolved as exc:
        return {'status':'UNAVAILABLE','reason':exc.reason,
            'witnesses':{key:array.tolist() for key,array in exc.witnesses.items()}}
    return {'status':'COMPLETED','witnesses':{key:array.tolist() for key,array in reduced.witnesses.items()},
        'state_units':state_units.tolist(),'output_units':output_units.tolist(),
        'phase_rank':int(reduced.transition.shape[0])}


def _io_linear(c, coordinate, retained, forces, receiver, refresh_h, view):
    arrays={key:np.asarray(value) for key,value in retained['witnesses'].items()}
    m,b,out=arrays['reduced_transition'],arrays['reduced_inputs'],arrays['reduced_outputs']
    multiplier=view+1
    dt=float(c['timestep'])/multiplier
    scales=_scales(c)[-1]
    refreshed,_,_,_,_=scaled_origin_system(refresh_h,forces*float(c['amplitude']),receiver,
        timestep=dt,decay=np.exp(-float(coordinate['friction'])*dt),
        position_scale=float(scales[0]),momentum_scale=float(scales[1]))
    r=arrays['restrict']@refreshed@arrays['lift']
    out=np.asarray(retained['output_units'])[:,None]*out
    state=np.zeros((len(m),len(c['actions']))); repaired=state.copy()
    values=[]; updated=[]; states=[]
    for tick in range(c['horizon_ticks']*multiplier+1):
        if tick%multiplier==0:
            values.append((out@state).T); updated.append((out@repaired).T); states.append(state.copy())
        if tick<c['horizon_ticks']*multiplier:
            force=b if tick<c['pulse_ticks']*multiplier else 0.
            state=m@state+force
            repaired=(m if tick<c['refresh_tick']*multiplier else r)@repaired+force
    lift=np.asarray(retained['state_units'])[:,None]*arrays['lift']
    return np.stack(values,axis=1),np.stack(updated,axis=1),states,m,r,lift


def _validate_freeze(c, calibration, seed):
    if calibration is None:
        return
    if (calibration.get('schema')!=CALIBRATION_SCHEMA
            or calibration.get('config_sha256')!=acquisition_config_fingerprint(c)
            or _fingerprint({k:v for k,v in calibration.items() if k!='freeze_sha256'})!=calibration.get('freeze_sha256')
            or seed in set(calibration['training_seeds'])|set(calibration['calibration_seeds'])):
        raise ValueError('Frozen forecast changes calibration, scientific settings, or TRAIN/CAL/CONF separation')


def _predict_feature(feature, model):
    if model['status']!='FROZEN' or feature is None:
        return {'status':'UNAVAILABLE','point':None,'upper':None,'admitted':False}
    value=float(np.asarray(feature)/np.asarray(model['feature_scale'])@np.asarray(model['coefficients']))
    point=None if value>700 else math.expm1(max(0.,value))
    upper_log=None if model['radius'] is None else value+model['radius']
    upper=None if upper_log is None or upper_log>700 else math.expm1(max(0.,upper_log))
    return {'status':'VACUOUS' if upper is None else 'FINITE','point':point,'upper':upper}


def _precommit(c, seed, case, calibration):
    features=_features(dict(case,handoff_tick=c['handoff_tick']))
    forecasts={} if calibration is None else {
        kind:_predict_feature(features[kind],model) for kind,model in calibration['models'].items()}
    for item in forecasts.values():
        item['admitted']=bool(item['upper'] is not None and item['upper']<=float(c['response_tolerance']))
    value={'schema':'classical-series-root-forecast-commitment.v1', 'seed':seed,
        'coordinate':case['coordinate'],'arm':case['arm'],
        'config_sha256':acquisition_config_fingerprint(c),'causal_prefix_sha256':case['causal_prefix_sha256'],
        'freeze_sha256':None if calibration is None else calibration['freeze_sha256'],
        'features':features,'forecasts':forecasts,'selected_preparation':None if calibration is None else calibration['nominee'],
        'cutoff_tick':c['handoff_tick'],
        'commitment_policy':'COMPUTED_AND_HASHED_BEFORE_ANY_ASSAY_FUTURE_RNG_READ_OR_NATIVE_ADVANCE',
        'mechanical_rule':'ORIGIN_FIXED_MODELS; CAUSAL_HOLD_REFRESH_AT_DECLARED_CHECKPOINT'}
    if calibration is not None and calibration.get('parameter_relation') is not None:
        from empirical_lawhood.methods.parameter_relations import predict_parameter_relations
        row=case['coordinate']
        value['parameter_relation_forecasts']=predict_parameter_relations(calibration['parameter_relation'],
            root_id=seed,coordinate_id=row['id'],
            parameters=[math.log(float(row[k])) for k in ('temperature','friction','cross_coupling')],
            features=features,tolerance=float(c['response_tolerance']))
        value['parameter_relation_package_sha256']=calibration['parameter_relation'].get('package_sha256')
    value['commitment_sha256']=_fingerprint(value)
    return value


def summarise_native_root(config: Mapping[str,object], acquired: dict) -> dict:
    """Compact retained statistics for one original TRAIN/CAL root.

    The execution layer binds this operation to the acquisition's exact artifact.
    No multi-root native histories or arrays need be retained by the fit worker.
    """
    c=normalise_config(config)
    methods=('INPUT_KRYLOV','JOINT_KRYLOV')
    if c['relation_training_coordinates']:
        methods=tuple(dict.fromkeys((*methods,c['relation_response_method'])))
    analysed,caches=_base_analysis(c,acquired,selected_methods=methods)
    from .capstones import capstone_case_summary
    return {'schema':'classical-series-summary.v1','seed':acquired['seed'],
        'config_sha256':acquisition_config_fingerprint(c),'case_summaries':analysed,
        'preparation_contrast_losses':{arm:_preparation_contrast_loss(c,acquired,caches,arm)
                                     for arm in c['preparation_arms']},
        'acquisition_causal_prefixes':[case.get('causal_prefix_sha256') for case in acquired['cases']],
        'capstone_cases':[capstone_case_summary(c,acquired['seed'],case,acquired['receivers'],acquired['forces']) for case in acquired['cases']],
        'assigned_cases':acquired['assigned_cases'],'independent_units':1,
        'native_seconds':acquired['native_seconds']}


def _retained_gaussian_controls(h, ports, basis):
    from empirical_lawhood.methods import retained_gaussian_response as method
    k=np.asarray([[2.,-1.],[-1.,2.]])
    reference=method.reduce_dense_reference(k,[0.,0.],np.eye(2),beta=1.)
    quartic=[]
    for order in (64,96):
        quadrature=method.gaussian_quadrature(reference.reference,order=order,maximum_points=order**2)
        wt=method.RetainedSamples(quadrature,np.zeros(len(quadrature.points)),quadrature.points[:,0])
        mutant=method.RetainedSamples(quadrature,quadrature.points[:,1]**4,quadrature.points[:,0])
        pair=method.paired_response(method.restrained_series(wt,[0.,.5,1.],1.),
                                    method.restrained_series(mutant,[0.,.5,1.],1.))
        quartic.append({'order':order,'endpoint':pair.endpoint,'finite_grid':pair.finite_grid})
    physical=np.asarray([[4.,-1.,0.,0.],[-1.,3.,-1.,0.],[0.,-1.,3.,-1.],[0.,0.,-1.,2.]])
    s=np.eye(4)[:,:2]
    reduced=method.reduce_dense_reference(physical,np.zeros(4),s,beta=1.)
    schur_expected=np.asarray([[13.,5.],[5.,20.]])/47
    energy=lambda x:float(.5*x@physical@x+x[0]**4+np.sin(x[1]))
    physical_point=np.asarray([.2,-.4,.7,.1])
    transverse_residual=reduced.residual(physical_point,energy,lambda x:physical@x)
    minimum=float(np.linalg.eigvalsh(h)[0])
    native={'status':'NOT_APPLICABLE','minimum_eigenvalue':minimum,
            'reason':'NATIVE_HESSIAN_NOT_POSITIVE_DEFINITE; NO_SHIFT_OR_EIGENVALUE_CLIPPING'}
    if minimum>0:
        real_basis=np.asarray(np.real_if_close(basis),dtype=float)
        bound=method.galerkin_compliance(ports,real_basis,lambda x:h@x,lower_eigenvalue_bound=minimum/2)
        exact=ports.T@np.linalg.solve(h,ports)
        low_margin=float(np.linalg.eigvalsh((exact-bound.lower+exact.T-bound.lower.T)/2)[0])
        high_margin=float(np.linalg.eigvalsh((bound.upper-exact+bound.upper.T-exact.T)/2)[0])
        native={'status':'CONDITIONAL_FLOAT64_ENCLOSURE_CONTROL','minimum_eigenvalue':minimum,
            'selected_lower_eigenvalue_bound':minimum/2,'lower_enclosure_minimum_margin':low_margin,
            'upper_enclosure_minimum_margin':high_margin,
            'roundoff_tolerance':1e-10,'native_global_quadratic_potential_claim':False,
            'scope':'ACTUAL_SPD_SNAPSHOT_OPERATOR_ONLY; NONLINEAR_NATIVE_REMAINDER_NOT_BOUNDED'}
    return {'status':'COMPUTED','quartic_same_origin_hessian':True,
        'quartic_controls':quartic,'quartic_endpoint_expected':.0195967797645805,
        'quartic_finite_grid_expected':.0196015100174638,
        'quadrature_refinement_endpoint_change':abs(quartic[1]['endpoint']-quartic[0]['endpoint']),
        'actual_hidden_coordinate_elimination':{'retained_dimension':2,'physical_dimension':4,
            'compliance_schur_error':float(np.linalg.norm(reduced.reference.compliance-schur_expected)),
            'finite_nonlinear_lift_residual':float(transverse_residual),
            'scope':'DECLARED_EXACT_CLASS_QUADRATIC_ENVIRONMENT_PLUS_FINITE_RETAINED_NONLINEARITY'},
        'native_snapshot_compliance':native,
        'native_matrix_equilibrium_or_free_energy_claim':False}


def _fit_parameter_relation(c, by_seed, train_seeds, cal_seeds):
    """Optional global relation uses the existing explicit fitted lifecycle."""
    if not c['relation_training_coordinates']:
        return None
    from empirical_lawhood.methods.parameter_relations import fit_parameter_relations
    rows=[]
    for seed in (*train_seeds,*cal_seeds):
        for case in by_seed.get(seed,[]):
            if case['arm']!='baseline' or case['coordinate']['id'] not in c['relation_training_coordinates']:
                continue
            row=case['coordinate']
            target=_root_loss([case],method=c['relation_response_method'])
            rows.append({'root_id':seed,'coordinate_id':row['id'],
                'parameters':[math.log(float(row[k])) for k in ('temperature','friction','cross_coupling')],
                'features':case.get('features',{'baseline':None,'structure':None}),'target':target})
    result=fit_parameter_relations(rows,training_roots=train_seeds,calibration_roots=cal_seeds,
        coordinate_ids=c['relation_training_coordinates'],
        ridge_candidates=[float(v) for v in c['relation_ridge_candidates']],
        folds=c['relation_folds'],alpha=float(c['calibration_alpha']))
    result['receiver_loss_method']=c['relation_response_method']
    result['historical_reproduction']=False
    result['scope']='NEW_IDENTIFIABLE_PARAMETER_RELATION_WITH_MATCHED_BR_SR_GROUPED_SELECTION'
    result.pop('package_sha256',None)
    result['package_sha256']=_fingerprint(result)
    return result


def _parameter_relation_readout(c, acquired, analysed, calibration):
    if calibration is None or calibration.get('parameter_relation') is None:
        return {'status':'NOT_ENTERED','reason':'NO_FROZEN_GLOBAL_PARAMETER_RELATION'}
    _validate_freeze(c,calibration,acquired['seed'])
    package=calibration['parameter_relation']
    output=[]
    for coordinate in c['coordinates']:
        case=next(row for row in acquired['cases'] if row['arm']=='baseline' and row['coordinate']['id']==coordinate['id'])
        if case['status']=='COMPLETED' and case.get('pre_response_commitment')!=_precommit(c,acquired['seed'],case,calibration):
            raise ValueError('Relation forecast did not preserve its before-future commitment')
        forecasts=case.get('pre_response_commitment',{}).get('parameter_relation_forecasts',{})
        target=_root_loss(analysed,method=c['relation_response_method'],coordinate_ids=[coordinate['id']])
        models={}
        for kind in ('baseline','structure'):
            prediction=forecasts.get(kind,{'status':'UNRESOLVED','point':None,'upper':None,'admitted':False})
            upper=prediction['upper']
            models[kind]={**prediction,
                'covered':None if target is None or upper is None else target<=upper,
                'actual_adequate':None if target is None else target<=float(c['response_tolerance']),
                'false_admission':None if target is None else bool(prediction['admitted'] and target>float(c['response_tolerance'])),
                'delivered_service':bool(prediction['admitted'] and target is not None and target<=float(c['response_tolerance'])),
                'unresolved_admitted_future':bool(prediction['admitted'] and target is None)}
        output.append({'coordinate':coordinate,'target':target,'models':models,
                       'training_coordinate':coordinate['id'] in package['training_coordinates']})
    return {'status':'FROZEN_RELATION_EVALUATED' if package['status']=='FROZEN' else 'FIT_UNAVAILABLE',
        'reason':package.get('reason'),'package_sha256':package['package_sha256'],
        'coordinates':output,'receiver_loss_method':c['relation_response_method'],
        'training_coordinates':package['training_coordinates'],'refits_on_confirmation':0,
        'coverage_transported_to_new_coordinates':False,'historical_reproduction':False,
        'selection_scope':package['selection_scope']}
