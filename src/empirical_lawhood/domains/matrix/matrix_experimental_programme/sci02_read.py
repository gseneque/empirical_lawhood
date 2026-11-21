# SPDX-License-Identifier: MPL-2.0
"""Cold SCI02 equations, complete signed readouts and whole-root reduction.

No RNG, preparation marcher or model-continuation producer is called here.
Native checks use literal trace-polynomial gradients; model checks compose the
independent affine map. A refused method remains an assigned comparison.
"""
from decimal import Decimal
from types import SimpleNamespace

import numpy as np

from empirical_lawhood.domains.matrix.matrix_factor_response.mechanism_readout import hold_tangent_window, input_krylov_basis
from empirical_lawhood.domains.matrix.matrix_factor_response.refresh_read import affine_response_window
from empirical_lawhood.domains.matrix.matrix_factor_response.refresh_science import receiver_matrix
from empirical_lawhood.domains.matrix.matrix_factor_response.science import _block_modes, frame_axes, native_position_coordinates, native_position_lift, origin_io_system
from empirical_lawhood.domains.matrix.matrix_factor_lifetime.science import measure_sector
from empirical_lawhood.domains.matrix.matrix_scheduled_history.response_forecast import instrument
from empirical_lawhood.domains.matrix.matrix_parameter_history.independent import _ou_errors, _trajectory_errors, potential_gradient
from empirical_lawhood.domains.matrix.matrix_scheduled_history.response_native import assess_scheduled_branch
from empirical_lawhood.domains.matrix.six_matrix_response.parameter_history import initial_parameter_state

from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02_records import METHODS, RECIPES
from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02_science import Computation, actuator_scales, measurements, prediction


def same(left, right, label):
    if left.dtype != right.dtype or left.shape != right.shape or not np.array_equal(left, right):
        raise ValueError('SCI02 reader substitutes ' + label)


def close(left, right, label, *, tolerance=1e-10, scale=1.):
    if left.shape != right.shape or not np.isfinite(left).all() or not np.isfinite(right).all():
        raise ValueError('SCI02 reader loses complete finite ' + label)
    error = float(np.max(np.abs((left - right) / scale)))
    if error > tolerance:
        raise ValueError(f'SCI02 independent {label} residual {error} exceeds {tolerance}')
    return error


def joined(first, second):
    if set(first) != set(second):
        raise ValueError('SCI02 continuation changes the retained member census')
    result = {}
    for key, value in first.items():
        continuous = not ('innovations' in key or key.startswith('bridge.'))
        if continuous:
            same(value[-1], second[key][0], 'interval endpoint ' + key)
        result[key] = np.concatenate((value, second[key][int(continuous):]))
    return result


def preparation_checks(design, recipe, arrays, *, start=0, source=None, zero=False):
    """Every full192 transition, both clocks and every conditioned bridge."""
    out, tolerance = {}, float(design.assay.native_reference_tolerance)
    for view, mult in (('primary', 1), ('fine', 2)):
        ticks = np.arange(start * mult, 256 * mult + 1, dtype='<i8')
        same(arrays[view + '_ticks'], ticks, 'preparation clock')
        alpha = np.asarray(design.recipe(recipe).half_tick_couplings[2 * start::2 // mult], dtype='<f8')
        same(arrays[view + '_alpha_tilde'], alpha, 'selected half-tick schedule')
        state = initial_parameter_state(design.coordinate) if source is None else None
        for name in ('positions', 'momenta'):
            same(arrays[view + '_' + name][0], getattr(state, name) if source is None else source[view + '_' + name][0],
                'permitted preparation start ' + name)
        noise = arrays[view + '_innovations']
        if zero: same(noise, np.zeros_like(noise), 'sealed zero innovation hypothesis')
        errors = np.asarray(_trajectory_errors(arrays[view + '_positions'], arrays[view + '_momenta'], noise,
            design.coordinate.member, getattr(design.coordinate, view + '_view'), alpha, alpha[1:]), dtype='<f8')
        out[view + '.preparation.residual'] = errors
        if np.max(errors) > tolerance: raise ValueError('SCI02 literal preparation equations failed')
    for key, errors in zip(('innovation', 'bath'), _ou_errors(design.coordinate.primary_view,
            arrays['primary_innovations'], arrays['fine_innovations'], arrays['bridge_innovations']), strict=True):
        out['preparation.ou.' + key] = np.asarray(errors, dtype='<f8')
        if max(errors) > tolerance: raise ValueError('SCI02 original preparation OU bridge failed')
    return out


def hessian_check(design, hessian, positions, alpha):
    eps = float(design.assay.hessian_difference_step)
    columns = []
    for direction in np.eye(96):
        displacement = eps * native_position_lift(direction)
        columns.append(native_position_coordinates((potential_gradient(positions + displacement, design.coordinate.member, alpha)
            - potential_gradient(positions - displacement, design.coordinate.member, alpha)) / (2 * eps)))
    literal = np.stack(columns, axis=1)
    return close(hessian, literal, 'literal gradient Hessian', tolerance=float(design.assay.hessian_reference_tolerance),
        scale=max(1., np.linalg.norm(literal)))


def chart_check(design, position, retained, key):
    measured = measure_sector(position[1], design.factor_rule)
    if measured.factor is None:
        if key in retained: raise ValueError('SCI02 retained chart is unavailable at its actual observation')
    elif key not in retained:
        raise ValueError('SCI02 omits its available original chart')
    else:
        same(retained[key], measured.factor, 'original observed factor chart')
    return measured


def instrument_checks(design, source, sealed, templates):
    """Check the source chart and inherited physical instrument from original bytes."""
    if 'forces' not in sealed: return
    measured = chart_check(design, source['primary_positions'][0], sealed, 'source_frame')
    forces, receivers, witness = instrument(design.assay, measured.factor, templates)
    for key, expected in (('forces', forces), ('receivers', receivers), ('source_spectrum', measured.spectrum),
            ('source_low', measured.basis), ('complement_spectrum', witness[0]), ('complement_vectors', witness[1])):
        same(sealed[key], expected, 'fixed source64 instrument ' + key)


def model_checks(design, models, handoff, observations, *, shadow_recipe=None):
    """Reconstruct the unchanged basis and forced map, retaining original H128 construction."""
    forces, receivers = models['forces'], models['receivers']
    force = np.stack([native_position_coordinates(f) * float(a.amplitude)
        for f, a in zip(forces, design.assay.actions, strict=True)], axis=1)
    receiver, scales = receiver_matrix(receivers), actuator_scales(design)
    chart_check(design, handoff['primary_positions'][0], models,
        'handoff_frame' if shadow_recipe is None else shadow_recipe.lower() + '.handoff_frame')
    residuals = []
    for view, mult in (('primary', 1), ('fine', 2)):
        numerical = getattr(design.coordinate, view + '_view')
        prefix = view if shadow_recipe is None else f'{shadow_recipe.lower()}.{view}'
        if prefix + '.h0' not in models: continue
        h0 = models[prefix + '.h0']
        residuals.append(hessian_check(design, h0, handoff[view + '_positions'][0], handoff[view + '_alpha_tilde'][0]))
        spectrum, vectors = models[prefix + '.eigenvalues'], models[prefix + '.eigenvectors']
        close(h0 @ vectors, vectors * spectrum, 'retained eigenpairs', scale=max(1., np.linalg.norm(h0)))
        close(vectors.T @ vectors, np.eye(96), 'eigenvector orthogonality')
        definition = SimpleNamespace(view=numerical, horizon_steps=tuple(range(1, 128 * mult + 1)))
        actions = tuple(SimpleNamespace(amplitude=a.amplitude, force_norm=a.force_norm, pulse_steps=16 * mult)
            for a in design.assay.actions)
        system = origin_io_system(definition, h0, forces, receivers, actions)
        bases = {'FULL': np.eye(96)}
        if prefix + '.basis.input_krylov48' in models:
            basis, _ = input_krylov_basis(system[0], system[1], spectrum, vectors, native_horizon=128 * mult)
            same(models[prefix + '.basis.input_krylov48'], basis, 'inherited Krylov basis')
            bases['INPUT_KRYLOV48'] = basis
        frame_key = 'handoff_frame' if shadow_recipe is None else shadow_recipe.lower() + '.handoff_frame'
        if frame_key in models:
            factor = _block_modes([frame_axes(models[frame_key])] * 6)
            same(models[prefix + '.basis.factor'], factor, 'handoff factor chart')
            bases['FACTOR'] = factor
        for panel in ((0, 1) if shadow_recipe is None else (0,)):
            h32key = f'{view}.p{panel}.h32' if shadow_recipe is None else prefix + '.h32'
            h32 = models.get(h32key)
            if h32 is not None:
                residuals.append(hessian_check(design, h32, observations[f'{view}.p{panel}.positions'][0],
                    observations[f'{view}.p{panel}.alpha_tilde'][0]))
            for method in METHODS:
                base = method.removesuffix('_REFRESH32')
                estimate = prediction(models, view, panel, method) if shadow_recipe is None else models.get(prefix + '.prediction.' + method.lower())
                if estimate is None: continue
                if base not in bases or method.endswith('_REFRESH32') and h32 is None:
                    raise ValueError('SCI02 forecast lacks its original basis or permitted observation')
                basis = bases[base]
                states = affine_response_window(h0, h32 if method.endswith('_REFRESH32') else h0, basis, force,
                    timestep=numerical.timestep, friction=numerical.friction_gamma, primary_horizon=64, pulse_ticks=16, refresh_tick=32)
                phase = np.block([[basis, np.zeros_like(basis)], [np.zeros_like(basis), basis]])
                expected = states[:, mult::mult] @ phase.T @ receiver.T
                residuals.append(close(estimate, expected, 'forced affine map ' + method, scale=np.repeat(scales, 24, axis=-1)))
                if shadow_recipe is None:
                    state_key = f'{view}.p{panel}' if method.endswith('_REFRESH32') else view
                    close(models[state_key + '.state.' + method.lower()], states[:, np.array((0, 32, 64)) * mult], 'own accumulated model state',
                        scale=float(scales[0, 15, 0]))
    return np.asarray(residuals, dtype='<f8')


def shadow_checks(design, source, sealed):
    out = {}
    if 'forces' not in sealed: return {'unavailable': np.array([1], dtype='<i8')}
    for recipe in RECIPES:
        recipe_key = recipe.lower()
        if f'{recipe_key}.primary.h0' not in sealed: continue
        path, handoff, observations = {}, {}, {}
        for view, mult in (('primary', 1), ('fine', 2)):
            for name in ('positions', 'momenta', 'alpha_tilde', 'ticks'):
                path[view + '_' + name] = sealed[f'{recipe_key}.{view}.shadow-preparation.' + name]
                handoff[view + '_' + name] = path[view + '_' + name][-1:]
                observations[f'{view}.p0.' + name] = sealed[f'{recipe_key}.{view}.shadow-hold.' + name][32 * mult:32 * mult + 1]
            path[view + '_innovations'] = np.zeros((192 * mult, 2, 3, 4, 4), dtype='<c16')
            hold = {name: sealed[f'{recipe_key}.{view}.shadow-hold.' + name] for name in ('positions', 'momenta', 'alpha_tilde', 'ticks')}
            hold['innovations'] = np.zeros((64 * mult, 2, 3, 4, 4), dtype='<c16')
            control = assess_scheduled_branch(design.coordinate, hold, refinement=mult,
                start_tick=256 * mult, initial_positions=handoff[view + '_positions'][0], initial_momenta=handoff[view + '_momenta'][0],
                direction=sealed['forces'][0], amplitude=0., pulse_steps=16 * mult,
                tolerance=design.assay.native_reference_tolerance, control_id='control.sci02.shadow')
            if control.disposition != 'SATISFIED': raise ValueError('SCI02 shadow literal HOLD equations failed')
            out[f'{recipe_key}.{view}.hold.residual'] = np.asarray(control.measured_errors, dtype='<f8')
            tangent = hold_tangent_window(hold['positions'], hold['alpha_tilde'], sealed['forces'], sealed['receivers'],
                member=design.coordinate.member, numerical_view=getattr(design.coordinate, view + '_view'),
                primary_horizon=64, pulse_ticks=16)[:, mult - 1::mult]
            same(sealed[f'{recipe_key}.{view}.tangent'], tangent, 'point hypothesis tangent')
            scales = actuator_scales(design)
            close(sealed[f'{recipe_key}.{view}.signal'], np.linalg.norm(tangent.reshape(4, 64, 2, 24), axis=-1) / scales, 'shadow signal')
            for method in METHODS:
                estimate = sealed.get(f'{recipe_key}.{view}.prediction.' + method.lower())
                if estimate is None: continue
                error = (tangent - estimate).reshape(4, 64, 2, 24) / scales[..., None]
                close(sealed[f'{recipe_key}.{view}.error.' + method.lower()], error, 'sealed target error')
                full = sealed[f'{recipe_key}.{view}.prediction.' + ('full_refresh32' if method.endswith('_REFRESH32') else 'full')]
                signed = np.stack((tangent - full, full - estimate)).reshape(2, 4, 64, 2, 24) / scales[None, ..., None]
                close(sealed[f'{recipe_key}.{view}.signed.' + method.lower()], signed, 'sealed signed decomposition')
        path['bridge_innovations'] = np.zeros((192, 2, 3, 4, 4), dtype='<c16')
        out.update({recipe_key + '.' + k: v for k, v in preparation_checks(design, recipe, path, start=64, source=source, zero=True).items()})
        out[recipe_key + '.model.residual'] = model_checks(design, sealed, handoff, observations, shadow_recipe=recipe)
    return out


def assess_arm(design, recipe, prefix, completion, handoff, sealed, origin, observations, models, first, second):
    """Complete native controls and five model errors on all 49 aligned ticks."""
    preparation = joined(prefix, completion)
    out = preparation_checks(design, recipe, preparation)
    scores = {'assigned': 1.}
    if 'forces' not in sealed or not first or not second or 'unavailable' in first or 'unavailable' in second:
        return Computation(out, 'UNAVAILABLE', ('SOURCE_OR_NATIVE_RESPONSE_UNAVAILABLE',), measurements=measurements(scores))
    response = joined(first, second)
    same(models['forces'], sealed['forces'], 'fixed physical forces')
    same(models['receivers'], sealed['receivers'], 'fixed physical receivers')
    for key, value in origin.items():
        same(models[key], value, 'original model member ' + key)
    out['model.residual'] = model_checks(design, models, handoff, observations)
    scales = actuator_scales(design)
    out['scales'] = scales
    for view, mult in (('primary', 1), ('fine', 2)):
        for panel in (0, 1):
            stem = f'{view}.p{panel}'
            hold = {name: response[f'branch.{stem}.a0.hold.' + name]
                for name in ('positions', 'momenta', 'alpha_tilde', 'ticks', 'innovations')}
            native = []
            for action, force in enumerate(sealed['forces']):
                a = f'branch.{stem}.a{action}.'
                for sign, coefficient in (('hold', 0), ('minus', -1), ('plus', 1)):
                    branch = {name: response[a + sign + '.' + name] for name in hold}
                    same(branch['innovations'], hold['innovations'], 'within-panel common noise')
                    if sign == 'hold':
                        for name in hold: same(branch[name], hold[name], 'common HOLD')
                    control = assess_scheduled_branch(design.coordinate, branch, refinement=mult,
                        start_tick=256 * mult, initial_positions=handoff[view + '_positions'][0], initial_momenta=handoff[view + '_momenta'][0],
                        direction=force, amplitude=coefficient * .01, pulse_steps=16 * mult,
                        tolerance=design.assay.native_reference_tolerance, control_id='control.sci02.response')
                    if control.disposition != 'SATISFIED': raise ValueError('SCI02 literal response equations failed')
                    out[f'{stem}.a{action}.{sign}.residual'] = np.asarray(control.measured_errors, dtype='<f8')
                q = (response[a + 'plus.positions'] - response[a + 'minus.positions']) / 2
                p = (response[a + 'plus.momenta'] - response[a + 'minus.momenta']) / 2
                native.append((np.einsum('rsjab,tsjab->tr', sealed['receivers'][:, 0].conj(), q)
                    + np.einsum('rsjab,tsjab->tr', sealed['receivers'][:, 1].conj(), p)).real[mult::mult])
            native = np.asarray(native, dtype='<f8')
            tangent = hold_tangent_window(hold['positions'], hold['alpha_tilde'], sealed['forces'], sealed['receivers'],
                member=design.coordinate.member, numerical_view=getattr(design.coordinate, view + '_view'),
                primary_horizon=64, pulse_ticks=16)[:, mult - 1::mult]
            out[stem + '.native'], out[stem + '.hold'] = native, tangent
            out[stem + '.signal'] = np.linalg.norm(native.reshape(4, 64, 2, 24), axis=-1) / scales
            for method in METHODS:
                estimate = prediction(models, view, panel, method)
                if estimate is None: continue
                error = (native - estimate).reshape(4, 64, 2, 24) / scales[..., None]
                full = prediction(models, view, panel, 'FULL_REFRESH32' if method.endswith('_REFRESH32') else 'FULL')
                terms = np.stack((native - tangent, tangent - full, full - estimate)).reshape(3, 4, 64, 2, 24) / scales[None, ..., None]
                out[stem + '.error.' + method.lower()] = error
                out[stem + '.signed.' + method.lower()] = terms
                squares = np.sum(terms * terms, axis=-1)
                cross = np.asarray([2 * np.sum(terms[i] * terms[j], axis=-1) for i, j in ((0, 1), (0, 2), (1, 2))])
                out[stem + '.squares.' + method.lower()], out[stem + '.cross.' + method.lower()] = squares, cross
                close(np.sum(terms, axis=0), error, 'signed error identity')
                close(np.sum(squares + cross, axis=0), np.sum(error * error, axis=-1), 'squared error identity')
                shadow = sealed.get(f'{recipe.lower()}.{view}.error.' + method.lower())
                if shadow is not None: out[stem + '.forecast_difference.' + method.lower()] = error - shadow
    for panel in (0, 1):
        for key, errors in zip(('innovation', 'bath'), _ou_errors(design.coordinate.primary_view,
                response[f'branch.primary.p{panel}.a0.hold.innovations'], response[f'branch.fine.p{panel}.a0.hold.innovations'],
                response[f'bridge.p{panel}']), strict=True):
            out[f'p{panel}.response.ou.' + key] = np.asarray(errors, dtype='<f8')
            if max(errors) > float(design.assay.native_reference_tolerance): raise ValueError('SCI02 response bridge failed')
    factor_action, = (i for i, action in enumerate(design.assay.actions) if action.role == 'FACTOR')
    signal = min(out[f'{v}.p{p}.signal'][factor_action, -1, 1] for v in ('primary', 'fine') for p in (0, 1))
    scores.update({'signal.factor_momentum64': signal, 'signal.adequate': float(signal >= .10), 'equations.accepted': 1.,
        'factor.admitted': float(models.get('factor_admitted', np.array([0]))[0])})
    for method in METHODS:
        available = all(f'{v}.p{p}.error.' + method.lower() in out for v in ('primary', 'fine') for p in (0, 1))
        scores[method + '.available'] = float(available)
        if not available: continue
        norms = np.asarray([[np.linalg.norm(out[f'{v}.p{p}.error.' + method.lower()], axis=-1)
            for p in (0, 1)] for v in ('primary', 'fine')])
        curves = np.maximum.accumulate(np.max(norms[:, :, :, 15:, :], axis=(1, 2, 4)), axis=1)
        out[method.lower() + '.joint_error_curves'] = curves
        view_delta = float(np.max(np.abs(curves[0] - curves[1])))
        error = float(np.max(curves))
        scores.update({method + '.error': error, method + '.view_difference': view_delta,
            method + '.joint_success': float(error <= .01 and view_delta <= .0001 and signal >= .10)})
        forecasts = [sealed.get(f'{recipe.lower()}.{v}.error.' + method.lower()) for v in ('primary', 'fine')]
        if all(x is not None for x in forecasts):
            predicted_error = max(float(np.max(np.linalg.norm(x[:, 15:], axis=-1))) for x in forecasts)
            predicted_signal = min(float(sealed[f'{recipe.lower()}.{v}.signal'][factor_action, -1, 1]) for v in ('primary', 'fine'))
            predicted_curves = [np.maximum.accumulate(np.max(np.linalg.norm(x[:, 15:], axis=-1), axis=(0, 2))) for x in forecasts]
            predicted_view = float(np.max(np.abs(predicted_curves[0] - predicted_curves[1])))
            scores.update({method + '.forecast_error': predicted_error, method + '.forecast_signal': predicted_signal,
                method + '.forecast_view_difference': predicted_view,
                method + '.forecast_admit': float(predicted_error <= .01 and predicted_view <= .0001 and predicted_signal >= .10),
                method + '.forecast_absolute_miss': abs(predicted_error - error)})
    return Computation(out, measurements=measurements(scores))


def reduce_root(products, assessments):
    if tuple(p.config.recipe for p in products) != RECIPES or len({p.config.root.identity for p in products}) != 1:
        raise ValueError('SCI02 reducer changes its complete original whole-root denominator')
    if set(assessments) != set(RECIPES):
        raise ValueError('SCI02 finite-pair assessment changes its original recipe census')
    values, arrays = {}, {'assigned_arms': np.arange(3, dtype='<i8')}
    for product in products:
        if product.config.phase != 'assess': raise ValueError('SCI02 reducer requires independent arm assessments')
        values.update({product.config.recipe + '.' + k: v for k, v in product.measurements})
        values[product.config.recipe + '.evaluable'] = Decimal(product.disposition == 'AVAILABLE')
    for left, right in (('ORIGINAL', 'EARLY'), ('ORIGINAL', 'DELAYED'), ('EARLY', 'DELAYED')):
        label = left + '_MINUS_' + right
        for method in METHODS:
            pairs = []
            for view in ('primary', 'fine'):
                for panel in (0, 1):
                    key = f'{view}.p{panel}.error.' + method.lower()
                    if key not in assessments[left] or key not in assessments[right]: continue
                    a, b = assessments[left][key], assessments[right][key]
                    delta = a - b
                    # Both endpoint errors remain visible beside their compatible contrast.
                    arrays[f'{label.lower()}.{key}'] = np.stack((a, b, delta))
                    pairs.append(float(np.max(np.linalg.norm(delta[:, 15:], axis=-1))))
            values['pair.' + label + '.' + method + '.available'] = Decimal(len(pairs) == 4)
            values['pair.' + label + '.' + method + '.contrast_error'] = Decimal(repr(max(pairs))) if len(pairs) == 4 else None
    return Computation(arrays, measurements=tuple(sorted(values.items())))
