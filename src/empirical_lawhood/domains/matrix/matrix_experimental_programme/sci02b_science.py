# SPDX-License-Identifier: MPL-2.0
"""SCI02-B response descriptions using the existing coupled derivative owner.

Predictive functions receive physical observations and immutable model arrays.
They receive neither random-stream material nor pulse-response observations.
"""
from dataclasses import replace
from decimal import Decimal
import time

import numpy as np

from empirical_lawhood.domains.matrix.matrix_factor_response.mechanism_readout import hessian_action_batch
from empirical_lawhood.domains.matrix.matrix_factor_response.refresh_science import continue_response_window, lift_states, receiver_matrix
from empirical_lawhood.domains.matrix.matrix_factor_response.science import native_position_coordinates, native_position_lift
from empirical_lawhood.domains.matrix.six_matrix_response.gradients import SixMatrixParameters
from empirical_lawhood.domains.matrix.six_matrix_response.parameter_history import split_parameter_innovations
from empirical_lawhood.domains.matrix.matrix_scheduled_history.response_native import native_scheduled_branch

from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02_science as old

ACCOUNTS = ('CONSTANT', 'BASE', 'STRUCTURE')
VIEWS = (('primary', 1), ('fine', 2))
PAIR = ('ORIGINAL', 'EARLY')


def operator_action(design, position, alpha, columns):
    """Actual bounded HVP columns; no dense Hessian or eigensystem is acquired."""
    if columns.ndim != 2 or columns.shape[0] != 96 or not 1 <= columns.shape[1] <= 96:
        raise ValueError('SCI02-B derivative requires physical position columns')
    member = design.coordinate.member
    parameters = SixMatrixParameters(2, float(member.mass_x), float(member.mass_y),
        float(member.cross_coupling_gamma), float(alpha[0]), float(alpha[1]))
    result = []
    for start in range(0, columns.shape[1], 4):
        lifted = np.asarray([native_position_lift(v) for v in columns[:, start:start + 4].T], dtype='<c16')
        result.extend(native_position_coordinates(v) for v in hessian_action_batch(position, lifted, parameters))
    return np.asarray(result, dtype='<f8').T


def input_basis(action, inputs, maximum_dimension):
    """Finite block Arnoldi with deterministic twice-reorthogonalized columns."""
    if maximum_dimension not in (24, 32) or inputs.shape != (96, 4) or not np.isfinite(inputs).all():
        raise ValueError('SCI02-B basis changes its finite candidate menu or four physical inputs')
    columns, images, rejected = [], [], 0

    def append(value):
        nonlocal rejected
        original = float(np.linalg.norm(value))
        residual = value.copy()
        if columns:
            basis = np.stack(columns, axis=1)
            for _ in range(2):
                residual -= basis @ (basis.T @ residual)
        size = float(np.linalg.norm(residual))
        if size <= 1e-10 * original or original == 0:
            rejected += 1
            return
        residual /= size
        if residual[np.argmax(np.abs(residual))] < 0:
            residual *= -1
        columns.append(residual)

    for column in inputs.T:
        append(column)
    if not columns:
        raise ValueError('SCI02-B has no retained input direction')
    cursor = 0
    while cursor < len(columns):
        stop = min(cursor + 4, len(columns))
        block = np.stack(columns[cursor:stop], axis=1)
        transformed = action(block)
        if transformed.shape != block.shape or not np.isfinite(transformed).all():
            raise ValueError('SCI02-B source operator loses a finite action column')
        images.extend(transformed.T.copy())
        cursor = stop
        if len(columns) < maximum_dimension:
            for column in transformed.T:
                if len(columns) == maximum_dimension:
                    break
                append(column)
    basis, actions = np.stack(columns, axis=1), np.stack(images, axis=1)
    residual = float(np.linalg.norm(basis.T @ basis - np.eye(len(columns))))
    if residual > 1e-10:
        raise ValueError('SCI02-B input basis fails orthogonality')
    return basis, actions, {'rank': len(columns), 'hvp_columns': len(images),
        'rejected_columns': rejected, 'orthogonality_residual': residual,
        'basis_condition_number': float(np.linalg.cond(basis)),
        'input_residual': float(np.linalg.norm(inputs - basis @ (basis.T @ inputs)))}


def origin_model(design, handoff, instrument, dimension):
    """One selected response construction at the actual handoff, before responses."""
    expected = {v + '_' + n for v, _ in VIEWS for n in ('positions', 'momenta', 'ticks', 'alpha_tilde')}
    if set(handoff) != expected or any(handoff[v + '_ticks'].tolist() != [256 * m] for v, m in VIEWS):
        raise ValueError('SCI02-B origin changes its exact physical observation cutoff')
    if 'forces' not in instrument:
        return old.unavailable('SOURCE_INSTRUMENT_UNAVAILABLE')
    forces, receivers = instrument['forces'], instrument['receivers']
    inputs = np.stack([native_position_coordinates(v) * .01 for v in forces], axis=1)
    receiver = receiver_matrix(receivers)
    arrays = {'forces': forces.copy(), 'receivers': receivers.copy()}
    costs = {}
    for view, mult in VIEWS:
        started = time.process_time()
        action = lambda v: operator_action(design, handoff[view + '_positions'][0], handoff[view + '_alpha_tilde'][0], v)
        basis, actions, witnesses = input_basis(action, inputs, dimension)
        projected = basis.T @ actions
        projected = (projected + projected.T) / 2
        numerical = getattr(design.coordinate, view + '_view')
        states = continue_response_window(projected, np.eye(len(projected)), basis.T @ inputs,
            timestep=numerical.timestep, friction=numerical.friction_gamma,
            primary_horizon=64, pulse_ticks=16, refresh_tick=32)
        arrays.update({view + '.basis': basis, view + '.h0_actions': actions,
            view + '.h0_projected': projected, view + '.own_state': states[:, [0, 32 * mult, 64 * mult]],
            view + '.frozen': lift_states(states[:, mult::mult], basis) @ receiver.T,
            view + '.handoff_positions': handoff[view + '_positions'],
            view + '.handoff_momenta': handoff[view + '_momenta']})
        costs.update({view + '.' + key: value for key, value in witnesses.items()})
        costs[view + '.construction_cpu_seconds'] = time.process_time() - started
    left, right = (arrays[v + '.basis'] for v, _ in VIEWS)
    costs['view_projector_distance'] = float(np.linalg.norm(left @ left.T - right @ right.T))
    return old.Computation(arrays, measurements=old.measurements(costs))


def refresh_model(design, origin, observation):
    expected = {f'{v}.p{p}.' + n for v, _ in VIEWS for p in (0, 1)
        for n in ('positions', 'momenta', 'alpha_tilde', 'ticks')}
    if set(observation) != expected:
        raise ValueError('SCI02-B update receives information outside its HOLD32 observation')
    if 'forces' not in origin:
        return old.unavailable('ORIGIN_UNAVAILABLE')
    arrays, costs = dict(origin), {}
    inputs = np.stack([native_position_coordinates(v) * .01 for v in origin['forces']], axis=1)
    receiver = receiver_matrix(origin['receivers'])
    for view, mult in VIEWS:
        numerical = getattr(design.coordinate, view + '_view')
        basis, h0 = origin[view + '.basis'], origin[view + '.h0_projected']
        for panel in (0, 1):
            stem = f'{view}.p{panel}'
            if observation[stem + '.ticks'].tolist() != [288 * mult]:
                raise ValueError('SCI02-B update changes its exact permitted physical clock')
            started = time.process_time()
            actions = operator_action(design, observation[stem + '.positions'][0],
                observation[stem + '.alpha_tilde'][0], basis)
            h32 = basis.T @ actions
            h32 = (h32 + h32.T) / 2
            states = continue_response_window(h0, np.eye(len(h0)), basis.T @ inputs,
                timestep=numerical.timestep, friction=numerical.friction_gamma,
                primary_horizon=64, pulse_ticks=16, refresh_tick=32, refresh_operator=h32)
            if not np.array_equal(states[:, 32 * mult], origin[view + '.own_state'][:, 1]):
                raise ValueError('SCI02-B update resets its own response state')
            arrays.update({stem + '.h32_actions': actions, stem + '.h32_projected': h32,
                stem + '.own_state': states[:, [0, 32 * mult, 64 * mult]],
                stem + '.updated': lift_states(states[:, mult::mult], basis) @ receiver.T})
            costs[stem + '.update_cpu_seconds'] = time.process_time() - started
            costs[stem + '.hvp_columns'] = basis.shape[1]
    return old.Computation(arrays, measurements=old.measurements(costs))


def description(models):
    """Four pre-outcome features; only PRIMARY supplies empirical predictors."""
    if set(models) != set(PAIR):
        raise ValueError('SCI02-B description changes its selected finite contrast')
    values, drifts, residuals = [], [], []
    for recipe in PAIR:
        arrays = models[recipe]
        values.append([np.linalg.norm(arrays['primary.handoff_' + name][0]) for name in ('positions', 'momenta')])
        basis, h0 = arrays['primary.basis'], arrays['primary.h0_actions']
        for panel in (0, 1):
            h32 = arrays[f'primary.p{panel}.h32_actions']
            drifts.append(np.linalg.norm(h32 - h0) / max(1., np.linalg.norm(h0)))
            residuals.append(np.linalg.norm(h32 - basis @ (basis.T @ h32)) / max(1., np.linalg.norm(h32)))
    return np.log1p(np.asarray((*np.mean(values, axis=0), max(drifts), max(residuals)), dtype='<f8'))


def fit_accounts(features, log_risk):
    """One fixed ridge fit per account; no hyperparameter or feature search."""
    if features.shape != (8, 4) or log_risk.shape != (8,) or not np.isfinite(features).all() or not np.isfinite(log_risk).all():
        raise ValueError('SCI02-B fit requires all eight original independent development roots')
    mean, scale = np.mean(features, axis=0), np.std(features, axis=0)
    scale[scale == 0] = 1.
    centered = (features - mean) / scale
    intercept = float(np.mean(log_risk))
    coefficients = np.zeros((3, 4), dtype='<f8')
    intercepts = np.array([float(np.median(log_risk)), intercept, intercept], dtype='<f8')
    for row, width in ((1, 2), (2, 4)):
        u, s, vt = np.linalg.svd(centered[:, :width], full_matrices=False)
        coefficients[row, :width] = vt.T @ ((s / (s * s + 1.)) * (u.T @ (log_risk - intercept)))
    return {'feature_mean': mean, 'feature_scale': scale, 'coefficients': coefficients, 'intercepts': intercepts}


def predict_accounts(fitted, features):
    result = fitted['intercepts'] + fitted['coefficients'] @ ((features - fitted['feature_mean']) / fitted['feature_scale'])
    return np.maximum(result, 0.)


def calibrated_admission(design, models, points, radius):
    if radius is None:
        return np.zeros(3, dtype='<i8'), np.full(3, -1., dtype='<f8')
    upper = np.expm1(points + radius)
    factor, = (i for i, action in enumerate(design.assay.actions) if action.role == 'FACTOR')
    scales = old.actuator_scales(design)
    signal = min(np.linalg.norm(models[r][f'{v}.p{p}.updated'][factor, -1, 24:]) / scales[factor, -1, 1]
        for r in PAIR for v, _ in VIEWS for p in (0, 1))
    admitted = np.asarray((upper <= 1.) & (signal - .01 * upper >= .10), dtype='<i8')
    return admitted, upper


def acquire_baseline(design, handoff, instrument, streams, *, on_step=None):
    """Acquire HOLD only to relative tick32, keeping exact original cursors."""
    arrays, saved, work = {}, [], 0
    started = time.process_time()
    for panel in (0, 1):
        selected = tuple(s for p, s in streams if p == panel and s.purpose.startswith('autonomous'))
        generators = old._generators(selected, (), 0, panel)
        coarse, bridge = old._noise_pair(generators, 'autonomous', 32)
        fine = np.concatenate([split_parameter_innovations(design.coordinate, c, b)
            for c, b in zip(coarse, bridge, strict=True)])
        arrays[f'bridge.p{panel}'] = bridge
        for view, mult, noise in (('primary', 1, coarse), ('fine', 2, fine)):
            result = native_scheduled_branch(old.state_at(handoff, view), coordinate=design.coordinate,
                refinement=mult, direction=instrument['forces'][0], amplitude=0., pulse_steps=16 * mult, innovations=noise)
            arrays.update({f'branch.{view}.p{panel}.a0.hold.' + key: value for key, value in result.items()})
            work += 32 * mult
            if on_step is not None:
                on_step(work)
        saved.extend(old._save_generators(selected, generators, 32, panel))
    return old.Computation(arrays, generators=tuple(saved), measurements=old.measurements({
        'native.hold_cpu_seconds': time.process_time() - started, 'native.integration_steps': 192,
        'native.gradient_evaluations': 196, 'rng.hermitian_matrices': 128}))


def acquire_reference(design, handoff, instrument, baseline, streams, saved, *, on_step=None, observe_cost=None):
    """Reuse paid prefix noise; acquire paired reference only after prediction."""
    arrays, cursors, work, costs = {}, [], 0, {'plus': 0., 'minus': 0., 'hold_suffix': 0.}
    for panel in (0, 1):
        selected = tuple(s for p, s in streams if p == panel and s.purpose.startswith('autonomous'))
        generators = old._generators(selected, saved, 32, panel)
        new_coarse, new_bridge = old._noise_pair(generators, 'autonomous', 32)
        coarse = np.concatenate((baseline[f'branch.primary.p{panel}.a0.hold.innovations'], new_coarse))
        bridge = np.concatenate((baseline[f'bridge.p{panel}'], new_bridge))
        fine = np.concatenate([split_parameter_innovations(design.coordinate, c, b)
            for c, b in zip(coarse, bridge, strict=True)])
        arrays[f'bridge.p{panel}'] = bridge
        for view, mult, noise in (('primary', 1, coarse), ('fine', 2, fine)):
            for index, direction in enumerate(instrument['forces']):
                for sign, amplitude in (('minus', -.01), ('plus', .01)):
                    started = time.process_time()
                    branch = native_scheduled_branch(old.state_at(handoff, view), coordinate=design.coordinate,
                        refinement=mult, direction=direction, amplitude=amplitude, pulse_steps=16 * mult, innovations=noise)
                    elapsed = time.process_time() - started
                    costs[sign] += elapsed
                    if observe_cost is not None:
                        observe_cost(f'reference.{view}.p{panel}.a{index}.{sign}', elapsed)
                    arrays.update({f'branch.{view}.p{panel}.a{index}.{sign}.' + key: value for key, value in branch.items()})
                    work += 64 * mult
                    if on_step is not None:
                        on_step(work)
            stem = f'branch.{view}.p{panel}.a0.hold.'
            from empirical_lawhood.domains.matrix.six_matrix_response.model import SixMatrixState
            state = SixMatrixState(2, baseline[stem + 'positions'][-1], baseline[stem + 'momenta'][-1],
                int(baseline[stem + 'ticks'][-1]), *baseline[stem + 'alpha_tilde'][-1])
            started = time.process_time()
            suffix = native_scheduled_branch(state, coordinate=design.coordinate, refinement=mult,
                direction=instrument['forces'][0], amplitude=0., pulse_steps=16 * mult, innovations=noise[32 * mult:])
            elapsed = time.process_time() - started
            costs['hold_suffix'] += elapsed
            if observe_cost is not None:
                observe_cost(f'reference.{view}.p{panel}.hold_suffix', elapsed)
            for key, value in suffix.items():
                offset = 0 if key == 'innovations' else 1
                arrays[stem + key] = np.concatenate((baseline[stem + key], value[offset:]))
            work += 32 * mult
            if on_step is not None:
                on_step(work)
        cursors.extend(old._save_generators(selected, generators, 64, panel))
    return old.Computation(arrays, generators=tuple(cursors), measurements=old.measurements({
        'native.' + key + '_cpu_seconds': value for key, value in costs.items()} | {
        'native.integration_steps': 3264, 'native.gradient_evaluations': 3300, 'rng.hermitian_matrices': 128}))


def with_cost(result, cpu, wall):
    return replace(result, measurements=tuple(sorted((*result.measurements,
        ('runtime.science_cpu_seconds', Decimal(str(time.process_time() - cpu))),
        ('runtime.science_wall_seconds', Decimal(str(time.monotonic() - wall)))))))
