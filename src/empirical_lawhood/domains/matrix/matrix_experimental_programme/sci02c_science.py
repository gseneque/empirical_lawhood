# SPDX-License-Identifier: MPL-2.0
"""Causal paired scalar descriptions and a fixed operator-history supplier."""
from dataclasses import replace
from decimal import Decimal
import time

import numpy as np

from empirical_lawhood.domains.matrix.matrix_factor_response.refresh_science import lift_states, receiver_matrix
from empirical_lawhood.domains.matrix.matrix_factor_response.science import native_position_coordinates

from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02_science as original
from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02b_science as previous
from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02_records import RECIPES
from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02b_development import subset
from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02c_records import Sci02CFrozenDescription, Sci02CCalibration

VIEWS, ACCOUNTS, PAIR = previous.VIEWS, previous.ACCOUNTS, previous.PAIR
ROUTES = ('BASIC', 'HISTORY')


def canonical_arrays(values): return {k: np.ascontiguousarray(v) for k, v in values.items()}
def exact(value): return Decimal(repr(float(value)))


def project_observations(baseline):
    """Project only H16/H32 states, excluding innovations and future responses."""
    arrays = {}
    for tick in (16, 32):
        for view, mult in VIEWS:
            for panel in (0, 1):
                for name in ('positions', 'momenta', 'alpha_tilde', 'ticks'):
                    source = baseline[f'branch.{view}.p{panel}.a0.hold.' + name]
                    if int(baseline[f'branch.{view}.p{panel}.a0.hold.ticks'][tick * mult]) != (256 + tick) * mult:
                        raise ValueError('SCI02-C observation changes its original causal clock')
                    arrays[f'h{tick}.{view}.p{panel}.' + name] = source[[tick * mult]].copy()
    return original.Computation(arrays)


def consumer_weights(design, instrument):
    factor, = (i for i, action in enumerate(design.assay.actions) if action.role == 'FACTOR')
    force = native_position_coordinates(instrument['forces'][factor])
    receiver = receiver_matrix(instrument['receivers'])[:, 96:]
    weights = receiver @ force
    if np.linalg.norm(receiver.T @ weights - force) > 1e-10 or abs(np.linalg.norm(force) - 1.) > 1e-10:
        raise ValueError('SCI02-C consumer direction is outside the original physical receiver')
    return factor, weights / original.actuator_scales(design)[factor, -1, 1]


def consumer_values(design, instrument, models, *, suffix='updated'):
    factor, weights = consumer_weights(design, instrument)
    endpoints = np.asarray([[[models[r][f'{v}.p{p}.' + suffix][factor, -1] @ weights
        for p in (0, 1)] for v, _ in VIEWS] for r in RECIPES], dtype='<f8')
    return endpoints, np.mean(endpoints[0] - endpoints[1], axis=-1)


def basic_models(design, instrument, handoffs, observations):
    if 'forces' not in instrument: return original.unavailable('SOURCE_INSTRUMENT_UNAVAILABLE')
    models, arrays, costs = {}, {}, {}
    consumer_weights(design, instrument)
    for recipe in RECIPES:
        origin = previous.origin_model(design, handoffs[recipe], instrument, 24)
        refreshed = previous.refresh_model(design, origin.arrays, subset(observations[recipe], 'h32.'))
        models[recipe] = canonical_arrays(refreshed.arrays)
        arrays.update({recipe.lower() + '.model.' + k: v for k, v in models[recipe].items()})
        costs.update({recipe + '.' + k: v for k, v in (*origin.measurements, *refreshed.measurements)})
    endpoints, q = consumer_values(design, instrument, models)
    frozen = {r: {f'{v}.p{p}.updated': models[r][v + '.frozen'] for v, _ in VIEWS for p in (0, 1)} for r in RECIPES}
    frozen_endpoints, frozen_q = consumer_values(design, instrument, frozen)
    arrays.update(frozen_endpoints=frozen_endpoints, frozen_q=frozen_q)
    arrays.update(features=previous.description({r: models[r] for r in PAIR}), endpoints=endpoints, model_q=q)
    return original.Computation(arrays, measurements=tuple(sorted(costs.items())))


def model_dict(arrays): return {r: subset(arrays, r.lower() + '.model.') for r in RECIPES}


def history_window(h0, h16, h32, force, *, timestep, friction):
    """Three fixed operators in one continuous two-kick response state."""
    if (len(h0) > 24 or any(h.shape != h0.shape or not np.isfinite(h).all()
            or not np.allclose(h, h.T, atol=1e-12, rtol=0) for h in (h0, h16, h32))
            or force.shape != (len(h0), 4) or timestep not in (Decimal('.001'), Decimal('.0005'))):
        raise ValueError('SCI02-C history changes its fixed physical span or clock')
    mult = 1 if timestep == Decimal('.001') else 2
    half, decay = float(timestep) / 2, np.exp(-float(friction * timestep))
    q, p = np.zeros_like(force), np.zeros_like(force)
    states = [np.concatenate((q, p)).T.copy()]
    for tick in range(1, 64 * mult + 1):
        operator = h0 if tick <= 16 * mult else h16 if tick <= 32 * mult else h32
        kick = half * force if tick <= 16 * mult else 0.
        p += kick - half * (operator @ q)
        q += half * p
        p *= decay
        q += half * p
        p += kick - half * (operator @ q)
        states.append(np.concatenate((q, p)).T.copy())
    result = np.transpose(states, (1, 0, 2))
    if not np.isfinite(result).all(): raise ValueError('SCI02-C nonfinite history response')
    return result


def history_models(design, basic, observations):
    if 'unavailable' in basic: return original.unavailable('BASIC_DESCRIPTION_UNAVAILABLE')
    models, arrays, costs = model_dict(basic), {}, {}
    drifts, omitted = [], []
    for recipe in RECIPES:
        model = models[recipe]
        inputs = np.stack([native_position_coordinates(v) * .01 for v in model['forces']], axis=1)
        receiver = receiver_matrix(model['receivers'])
        for view, mult in VIEWS:
            numerical = getattr(design.coordinate, view + '_view')
            basis, h0 = model[view + '.basis'], model[view + '.h0_projected']
            for panel in (0, 1):
                started = time.process_time()
                stem = f'{view}.p{panel}'
                observation = subset(observations[recipe], 'h16.')
                if observation[stem + '.ticks'].tolist() != [272 * mult]:
                    raise ValueError('SCI02-C history supplier changes its H16 clock')
                images = previous.operator_action(design, observation[stem + '.positions'][0],
                    observation[stem + '.alpha_tilde'][0], basis)
                h16 = (basis.T @ images + images.T @ basis) / 2
                states = history_window(h0, h16, model[stem + '.h32_projected'], basis.T @ inputs,
                    timestep=numerical.timestep, friction=numerical.friction_gamma)
                extra = {stem + '.h16_actions': images, stem + '.h16_projected': h16,
                    stem + '.history_state': states[:, [0, 16 * mult, 32 * mult, 64 * mult]],
                    stem + '.updated': lift_states(states[:, mult::mult], basis) @ receiver.T}
                extra = canonical_arrays(extra)
                model.update(extra)
                arrays.update({recipe.lower() + '.model.' + k: v for k, v in extra.items()})
                costs[recipe + '.' + stem + '.supplier_cpu_seconds'] = time.process_time() - started
                costs[recipe + '.' + stem + '.hvp_columns'] = basis.shape[1]
                if recipe in PAIR and view == 'primary':
                    old = model[view + '.h0_actions']
                    for value in (images, model[stem + '.h32_actions']):
                        drifts.append(np.linalg.norm(value - old) / max(1., np.linalg.norm(old)))
                        omitted.append(np.linalg.norm(value - basis @ (basis.T @ value)) / max(1., np.linalg.norm(value)))
    endpoints, q = consumer_values(design, models['ORIGINAL'], models)
    arrays.update(features=np.asarray((*basic['features'][:2], *np.log1p((max(drifts), max(omitted)))), dtype='<f8'),
        endpoints=endpoints, model_q=q)
    return original.Computation(arrays, measurements=original.measurements(costs))


def combined_models(basic, history):
    models = model_dict(basic)
    for recipe in RECIPES: models[recipe].update(subset(history, recipe.lower() + '.model.'))
    return models


def signed_predictions(model, route, features, model_q):
    fitted = model.numerical_arrays()
    centered = (features - fitted['feature_mean'][route]) / fitted['feature_scale'][route]
    correction = fitted['intercepts'][route] + fitted['coefficients'][route] @ centered
    return model_q[None, :] + correction[:, None]


def admission(study, calibration, predictions, route):
    radii = (None,) * 3 if calibration is None else calibration.radii[route]
    view_difference = np.abs(predictions[:, 0] - predictions[:, 1])
    widths = np.array([-1. if r is None else float(r) + v for r, v in zip(radii, view_difference, strict=True)], dtype='<f8')
    admitted = np.asarray([(r is not None and w <= float(study.precision)
        and v <= float(study.view_tolerance) and abs(p) > w)
        for r, w, v, p in zip(radii, widths, view_difference, predictions[:, 0], strict=True)], dtype='<i8')
    return admitted, widths


def request(config, basic):
    if 'unavailable' in basic: return original.unavailable('BASIC_DESCRIPTION_UNAVAILABLE')
    predictions = signed_predictions(config.model, 0, basic['features'], basic['model_q'])
    admitted, widths = admission(config.study, config.calibration, predictions, 0)
    radius = None if config.calibration is None else config.calibration.radii[1][2]
    requested = config.calibration is not None and not admitted[2] and radius is not None and radius <= config.study.precision
    return original.Computation({'predictions': predictions, 'admitted': admitted, 'widths': widths,
        'request_history': np.asarray([int(requested)], dtype='<i8')})


def decide(config, request_arrays, history):
    if 'unavailable' in request_arrays or 'unavailable' in history:
        return original.unavailable('CAUSAL_DESCRIPTION_UNAVAILABLE')
    predictions = signed_predictions(config.model, 1, history['features'], history['model_q'])
    admitted, widths = admission(config.study, config.calibration, predictions, 1)
    purchased = int(request_arrays['request_history'][0])
    # Audit-only supplier results cannot alter a decision whose policy did not request them.
    selected = 0 if request_arrays['admitted'][2] else 1 if purchased and admitted[2] else 2
    return original.Computation({'predictions': np.stack((request_arrays['predictions'], predictions)),
        'admitted': np.stack((request_arrays['admitted'], admitted)), 'widths': np.stack((request_arrays['widths'], widths)),
        'request_history': np.asarray([purchased], dtype='<i8'), 'selected_route': np.asarray([selected], dtype='<i8')})


def diagnose(config, retained, values):
    if retained.root != config.root or retained.design != config.design:
        raise ValueError('SCI02-C training substitutes its original physical root')
    instrument = subset(values, 'instrument.')
    handoffs = {r: subset(values, r.lower() + '.handoff.') for r in RECIPES}
    observations = {r: subset(values, r.lower() + '.observation.') for r in RECIPES}
    basic = basic_models(config.design, instrument, handoffs, observations)
    if basic.disposition == 'UNAVAILABLE': return basic
    history = history_models(config.design, basic.arrays, observations)
    native = {r: subset(values, r.lower() + '.assess.') for r in RECIPES}
    endpoints, target = consumer_values(config.design, instrument, native, suffix='native')
    arrays = {'basic.' + k: v for k, v in basic.arrays.items()}
    arrays.update({'history.' + k: v for k, v in history.arrays.items()})
    arrays.update(features=np.stack((basic.arrays['features'], history.arrays['features'])),
        model_q=np.stack((basic.arrays['model_q'], history.arrays['model_q'])), native_q=target, native_endpoints=endpoints)
    costs = tuple(sorted((*basic.measurements, *(('history.' + k, v) for k, v in history.measurements))))
    return original.Computation(arrays, measurements=costs)


def fit(config, parents, arrays):
    selected = sorted(parents.values(), key=lambda p: p.config.root.ordinal)
    if len(selected) != 8 or any(p.disposition != 'AVAILABLE' for p in selected):
        return original.unavailable('COMPLETE_TRAINING_DESCRIPTIONS_UNAVAILABLE'), None
    features = np.stack([arrays[p.config.node_id]['features'] for p in selected])
    targets = np.stack([arrays[p.config.node_id]['native_q'][0] - arrays[p.config.node_id]['model_q'][:, 0] for p in selected])
    fits = [previous.fit_accounts(features[:, r], targets[:, r]) for r in range(2)]
    fitted = {key: np.stack([f[key] for f in fits]) for key in fits[0]}
    nested = lambda a: tuple(nested(v) for v in a) if np.ndim(a) else exact(a)
    model = Sci02CFrozenDescription('description.' + config.study.fingerprint(), config.study.identity, config.roots,
        tuple(p.identity for p in selected), *(nested(fitted[k]) for k in ('feature_mean', 'feature_scale', 'coefficients', 'intercepts')))
    return original.Computation({**fitted, 'training_features': features, 'training_targets': targets}), model


def calibrate(config, parents, arrays):
    rows = sorted(parents.values(), key=lambda p: p.config.root.ordinal)
    scores = []
    for p in rows:
        values = arrays[p.config.node_id]
        score = None if p.disposition != 'AVAILABLE' else np.max(np.abs(values['predictions'] - values['native_q'][None, None, :]), axis=-1)
        scores.append(tuple(tuple(None if score is None else exact(score[r, a]) for a in range(3)) for r in range(2)))
    scores = tuple(scores)
    radii = tuple(tuple(None if any(s[r][a] is None for s in scores) else max(s[r][a] for s in scores) for a in range(3)) for r in range(2))
    record = Sci02CCalibration('calibration.' + config.study.fingerprint(), config.study.identity, config.model.identity,
        config.roots, tuple(p.identity for p in rows), scores, radii)
    values = np.asarray([[[-1. if v is None else float(v) for v in route] for route in s] for s in scores], dtype='<f8')
    return original.Computation({'scores': values, 'radii': np.asarray([[-1. if v is None else float(v) for v in r] for r in radii], dtype='<f8')}), record


def with_cost(result, cpu, wall):
    return replace(result, arrays=canonical_arrays(result.arrays), measurements=tuple(sorted((*result.measurements,
        ('runtime.science_cpu_seconds', exact(time.process_time() - cpu)),
        ('runtime.science_wall_seconds', exact(time.monotonic() - wall))))))
