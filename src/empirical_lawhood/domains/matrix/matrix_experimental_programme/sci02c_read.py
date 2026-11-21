# SPDX-License-Identifier: MPL-2.0
"""Independent physical equations, signed consumer readout and finite assessment."""
from math import comb

import numpy as np

from empirical_lawhood.domains.matrix.matrix_factor_response.refresh_science import receiver_matrix
from empirical_lawhood.domains.matrix.matrix_factor_response.science import native_position_coordinates

from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02_read as original_read
from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02_science as original
from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02b_read as previous
from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02c_science as science
from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02b_development import subset
from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02_records import RECIPES


def affine_history(operators, force, *, timestep, friction):
    """Independent composition of complete affine steps, including both kicks."""
    dt, decay = float(timestep), np.exp(-float(timestep * friction))
    mult = 1 if dt == .001 else 2
    half, drift = dt / 2, dt / 2 * (1 + decay)
    eye, maps = np.eye(len(force)), []
    for h in operators:
        a, b = eye - drift * half * h, drift * eye
        transition = np.block([[a, b], [-half * (decay * h + h @ a), decay * eye - half * h @ b]])
        dq = drift * half * force
        maps.append((transition, np.concatenate((dq, drift * force - half * h @ dq))))
    state = np.zeros((2 * len(force), 4))
    states = [state.T.copy()]
    for tick in range(1, 64 * mult + 1):
        m, drive = maps[0 if tick <= 16 * mult else 1 if tick <= 32 * mult else 2]
        state = m @ state + (drive if tick <= 16 * mult else 0.)
        states.append(state.T.copy())
    return np.transpose(states, (1, 0, 2))


def check_models(design, handoffs, observations, basic, history):
    if 'unavailable' in basic or 'unavailable' in history:
        raise ValueError('SCI02-C complete model check lacks its causal operands')
    models = science.model_dict(basic)
    residuals = []
    scale = np.repeat(original.actuator_scales(design), 24, axis=-1)
    for recipe in RECIPES:
        model = models[recipe]
        residuals.extend(previous.model_checks(design, handoffs[recipe], subset(observations[recipe], 'h32.'), model))
        extra = subset(history, recipe.lower() + '.model.')
        force = np.stack([native_position_coordinates(f) * .01 for f in model['forces']], axis=1)
        receiver = receiver_matrix(model['receivers'])
        for view, mult in science.VIEWS:
            basis = model[view + '.basis']
            phase = np.block([[basis, np.zeros_like(basis)], [np.zeros_like(basis), basis]])
            numerical = getattr(design.coordinate, view + '_view')
            for panel in (0, 1):
                stem = f'{view}.p{panel}'
                observed = subset(observations[recipe], 'h16.')
                images = extra[stem + '.h16_actions']
                residuals.append(previous.action_check(design, observed[stem + '.positions'][0],
                    observed[stem + '.alpha_tilde'][0], basis, images))
                h16 = (basis.T @ images + images.T @ basis) / 2
                original_read.close(extra[stem + '.h16_projected'], h16, 'SCI02-C H16 projected action')
                expected = affine_history((model[view + '.h0_projected'], h16, model[stem + '.h32_projected']),
                    basis.T @ force, timestep=numerical.timestep, friction=numerical.friction_gamma)
                residuals.append(original_read.close(extra[stem + '.updated'], expected[:, mult::mult] @ phase.T @ receiver.T,
                    'SCI02-C independent history affine response', scale=scale))
                original_read.close(extra[stem + '.history_state'], expected[:, [0, 16 * mult, 32 * mult, 64 * mult]],
                    'SCI02-C continuous own state at every operator change')
                original_read.close(extra[stem + '.history_state'][:, 0], model[view + '.own_state'][:, 0],
                    'SCI02-C identical original zero response')
    return np.asarray(residuals, dtype='<f8')


def assess_arm(config, arrays):
    """Verify native equations and original projection ports without new acquisition."""
    d, recipe = config.design, config.recipe
    if 'unavailable' in arrays['reference']:
        return original.unavailable('ORIGINAL_REFERENCE_UNAVAILABLE')
    joined = original_read.joined(arrays['prefix'], arrays['completion'])
    residuals = original_read.preparation_checks(d, recipe, joined)
    for name, value in original.project_state(joined, tick=256).arrays.items():
        original_read.same(arrays['handoff'][name], value, 'SCI02-C actual prepared handoff')
    for name, value in science.project_observations(arrays['baseline']).arrays.items():
        if name.startswith('h32.'):
            original_read.same(arrays['observation'][name], value, 'SCI02-C causal H32 HOLD observation')
    result = previous.native_response(d, arrays['handoff'], arrays['instrument'], arrays['reference'], baseline=arrays['baseline'])
    # The physical force projection must agree with the frozen receiver projection.
    factor, weights = science.consumer_weights(d, arrays['instrument'])
    scale = original.actuator_scales(d)[factor, -1, 1]
    force = arrays['instrument']['forces'][factor]
    for view, _ in science.VIEWS:
        for panel in (0, 1):
            stem = f'{view}.p{panel}'
            plus = arrays['reference'][f'branch.{stem}.a{factor}.plus.momenta'][-1]
            minus = arrays['reference'][f'branch.{stem}.a{factor}.minus.momenta'][-1]
            direct = np.real(np.vdot(force, (plus - minus) / 2)) / scale
            projected = result[stem + '.native'][factor, -1] @ weights
            original_read.close(np.asarray([projected]), np.asarray([direct]), 'SCI02-C literal signed force receiver')
    return original.Computation({**result, **residuals})


def reduce_root(config, arrays):
    if any('unavailable' in arrays[key] for key in ('basic', 'history', 'decision', *(r + '.assess' for r in RECIPES))):
        return original.unavailable('COMPLETE_ORIGINAL_ROOT_UNAVAILABLE')
    basic, history = arrays['basic'], arrays['history']
    basic_models = science.model_dict(basic)
    models = (basic_models, science.combined_models(basic, history))
    native = {r: arrays[r + '.assess'] for r in RECIPES}
    endpoints, target = science.consumer_values(config.design, basic_models['ORIGINAL'], native, suffix='native')
    retained = {'native_q': target, 'native_endpoints': endpoints, 'frozen_q': basic['frozen_q'],
        'model_q': np.stack((basic['model_q'], history['model_q'])), **arrays['decision']}
    measured = {}
    for route, m in zip(science.ROUTES, models, strict=True):
        assessed = previous.assess_pair(config.design, native, m)
        retained.update({route.lower() + '.diagnostic.' + key: value for key, value in assessed.arrays.items()})
        measured.update({route + '.' + k: v for k, v in assessed.measurements})
    frozen = {r: {f'{v}.p{p}.updated': basic_models[r][v + '.frozen'] for v, _ in science.VIEWS for p in (0, 1)} for r in RECIPES}
    frozen_assessed = previous.assess_pair(config.design, native, frozen)
    measured.update({'FROZEN.' + k: v for k, v in frozen_assessed.measurements})
    selected = int(retained['selected_route'][0])
    numerical = abs(target[0] - target[1]) <= float(config.study.view_tolerance)
    delivered = selected < 2
    error = None if not delivered else abs(target[0] - retained['predictions'][selected, 2, 0])
    wrong_sign = delivered and target[0] * retained['predictions'][selected, 2, 0] <= 0
    valid = delivered and numerical and error <= float(config.study.precision) and not wrong_sign
    measured.update({'consumer.native_view_difference': science.exact(abs(target[0] - target[1])),
        'consumer.numerically_usable': science.exact(numerical), 'policy.delivered': science.exact(delivered),
        'policy.valid_delivery': science.exact(valid), 'policy.false_or_unusable_delivery': science.exact(delivered and not valid),
        'policy.selected_route': science.exact(selected), 'policy.purchased_history': science.exact(retained['request_history'][0]),
        'policy.absolute_error': None if error is None else science.exact(error)})
    return original.Computation(retained, measurements=tuple(sorted(measured.items())))


def confirm(config, parents, arrays):
    rows = sorted(parents.values(), key=lambda p: p.config.root.ordinal)
    forecasts, targets, methods, selected, purchases, usable, widths = [], [], [], [], [], [], []
    availability = []
    for p in rows:
        available = p.disposition == 'AVAILABLE'
        availability.append(int(available))
        values = arrays[p.config.node_id]
        forecasts.append(values['predictions'] if available else np.zeros((2, 3, 2)))
        targets.append(values['native_q'] if available else np.zeros(2))
        methods.append(values['model_q'] if available else np.zeros((2, 2)))
        selected.append(int(values['selected_route'][0]) if available else 2)
        purchases.append(int(values['request_history'][0]) if available else 0)
        usable.append(int(available and dict(p.measurements)['consumer.numerically_usable'] == 1))
        widths.append(values['widths'] if available else np.full((2, 3), -1.))
    forecasts, targets, methods, widths = map(np.asarray, (forecasts, targets, methods, widths))
    available = np.asarray(availability, dtype=bool)
    errors = forecasts - targets[:, None, None, :]
    wins = int(np.sum(available & (np.abs(errors[:, 0, 1, 0]) - np.abs(errors[:, 0, 2, 0]) >= float(config.study.forecast_win_margin))))
    delivered = sum(dict(p.measurements).get('policy.delivered', 0) for p in rows)
    false = sum(dict(p.measurements).get('policy.false_or_unusable_delivery', 0) for p in rows)
    measurements = {'assigned_roots': 32, 'available_roots': int(available.sum()), 'forecast.structure_wins': wins,
        'forecast.sign_test_p': sum(comb(32, k) for k in range(wins, 33)) / 2**32,
        'forecast.criterion_met': int(wins >= 22), 'delivery.count': delivered, 'delivery.false_or_unusable': false,
        'delivery.criterion_met': int(delivered >= 24 and false == 0 and available.all())}
    audit = np.asarray(config.study.audit_ordinals, dtype='<i8')
    output = {'predictions': forecasts, 'native_q': targets, 'model_q': methods, 'errors': errors,
        'selected_route': np.asarray(selected, dtype='<i8'), 'purchased_history': np.asarray(purchases, dtype='<i8'),
        'available': np.asarray(availability, dtype='<i8'), 'numerically_usable': np.asarray(usable, dtype='<i8'),
        'widths': widths, 'audit_ordinals': audit}
    if available.all():
        predictor, truth = forecasts[:, 0, 2, 0], targets[:, 0]
        residual = truth - predictor
        corrected = np.mean(predictor) + np.mean(residual[audit])
        se = np.sqrt((1 - 8 / 32) * np.var(residual[audit], ddof=1) / 8)
        output['aggregate'] = np.asarray([np.mean(truth), np.mean(predictor), np.mean(truth[audit]), corrected, se], dtype='<f8')
        measurements['aggregate.absolute_corrected_error'] = abs(corrected - np.mean(truth))
    return original.Computation(output, measurements=original.measurements(measurements))


def check_fit(config, parents, values, product, arrays):
    rows = sorted(parents.values(), key=lambda p: p.config.root.ordinal)
    if any(p.disposition != 'AVAILABLE' for p in rows):
        if product.frozen_description is not None or product.disposition != 'UNAVAILABLE':
            raise ValueError('SCI02-C fitted an incomplete original development population')
        return
    model = product.frozen_description
    if model is None or model.diagnosis_products != tuple(p.identity for p in rows):
        raise ValueError('SCI02-C fit omits original training custody')
    features = np.stack([values[p.config.node_id]['features'] for p in rows])
    targets = np.stack([values[p.config.node_id]['native_q'][0] - values[p.config.node_id]['model_q'][:, 0] for p in rows])
    fitted = model.numerical_arrays()
    for route in range(2):
        previous.check_fit(features[:, route], targets[:, route], {k: v[route] for k, v in fitted.items()})
    for name, expected in {**fitted, 'training_features': features, 'training_targets': targets}.items():
        original_read.close(arrays[name], expected, 'SCI02-C frozen training-only signed fit')


def check_diagnosis(config, retained, values, product, arrays):
    if product.disposition != 'AVAILABLE':
        if 'instrument.forces' in values: raise ValueError('SCI02-C unsupported training unavailability')
        return
    handoffs = {r: subset(values, r.lower() + '.handoff.') for r in RECIPES}
    observations = {r: subset(values, r.lower() + '.observation.') for r in RECIPES}
    basic, history = subset(arrays, 'basic.'), subset(arrays, 'history.')
    check_models(config.design, handoffs, observations, basic, history)
    instrument = subset(values, 'instrument.')
    native = {r: subset(values, r.lower() + '.assess.') for r in RECIPES}
    endpoints, q = science.consumer_values(config.design, instrument, native, suffix='native')
    original_read.same(arrays['native_q'], q, 'SCI02-C signed original training target')
    original_read.same(arrays['native_endpoints'], endpoints, 'SCI02-C complete original panel targets')
    check_descriptions(config.design, basic, history)
    original_read.same(arrays['features'], np.stack((basic['features'], history['features'])), 'SCI02-C training features')
    original_read.same(arrays['model_q'], np.stack((basic['model_q'], history['model_q'])), 'SCI02-C training model values')


def check_descriptions(design, basic, history):
    models = science.model_dict(basic)
    handoff_norms = np.mean([[np.linalg.norm(models[r]['primary.handoff_' + n][0]) for n in ('positions', 'momenta')]
        for r in science.PAIR], axis=0)
    for route, output in enumerate((basic, history)):
        selected = models if not route else science.combined_models(basic, history)
        drift, omitted = [], []
        for recipe in science.PAIR:
            model = selected[recipe]
            basis, origin = model['primary.basis'], model['primary.h0_actions']
            for panel in (0, 1):
                for tick in ((32,) if not route else (16, 32)):
                    action = model[f'primary.p{panel}.h{tick}_actions']
                    drift.append(np.linalg.norm(action - origin) / max(1., np.linalg.norm(origin)))
                    omitted.append(np.linalg.norm(action - basis @ (basis.T @ action)) / max(1., np.linalg.norm(action)))
        expected = np.log1p(np.asarray((*handoff_norms, max(drift), max(omitted)), dtype='<f8'))
        original_read.same(output['features'], expected, 'SCI02-C declared causal description')
        endpoints, q = science.consumer_values(design, models['ORIGINAL'], selected)
        original_read.same(output['model_q'], q, 'SCI02-C original model projection')
        original_read.same(output['endpoints'], endpoints, 'SCI02-C original model panels')
