# SPDX-License-Identifier: MPL-2.0
"""Independent SCI02-B equations, paired criteria and empirical fit checks."""
from decimal import Decimal

import numpy as np

from empirical_lawhood.domains.matrix.matrix_factor_response.refresh_read import affine_response_window
from empirical_lawhood.domains.matrix.matrix_factor_response.refresh_science import receiver_matrix
from empirical_lawhood.domains.matrix.matrix_factor_response.science import native_position_coordinates, native_position_lift
from empirical_lawhood.domains.matrix.matrix_parameter_history.independent import _ou_errors, potential_gradient
from empirical_lawhood.domains.matrix.matrix_scheduled_history.response_native import assess_scheduled_branch

from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02_read as old_read
from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02_science as old
from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02b_science import ACCOUNTS, PAIR, VIEWS


def action_check(design, positions, alpha, basis, actions):
    epsilon = float(design.assay.hessian_difference_step)
    literal = []
    for direction in basis.T:
        displacement = epsilon * native_position_lift(direction)
        literal.append(native_position_coordinates((potential_gradient(positions + displacement, design.coordinate.member, alpha)
            - potential_gradient(positions - displacement, design.coordinate.member, alpha)) / (2 * epsilon)))
    return old_read.close(actions, np.asarray(literal).T, 'SCI02-B literal derivative columns',
        tolerance=float(design.assay.hessian_reference_tolerance), scale=max(1., np.linalg.norm(actions)))


def model_checks(design, handoff, observation, model):
    """Literal gradients and independent affine maps, never the producer marcher."""
    force = np.stack([native_position_coordinates(v) * .01 for v in model['forces']], axis=1)
    receiver, scale = receiver_matrix(model['receivers']), np.repeat(old.actuator_scales(design), 24, axis=-1)
    residuals = []
    for view, mult in VIEWS:
        basis = model[view + '.basis']
        old_read.close(basis.T @ basis, np.eye(basis.shape[1]), 'SCI02-B orthogonal physical span')
        old_read.close(basis @ (basis.T @ force), force, 'SCI02-B retained physical inputs')
        actions = model[view + '.h0_actions']
        residuals.append(action_check(design, handoff[view + '_positions'][0], handoff[view + '_alpha_tilde'][0], basis, actions))
        h0 = (basis.T @ actions + actions.T @ basis) / 2
        old_read.close(model[view + '.h0_projected'], h0, 'SCI02-B projected origin operator')
        numerical = getattr(design.coordinate, view + '_view')
        phase = np.block([[basis, np.zeros_like(basis)], [np.zeros_like(basis), basis]])
        original = affine_response_window(h0, h0, np.eye(len(h0)), basis.T @ force,
            timestep=numerical.timestep, friction=numerical.friction_gamma,
            primary_horizon=64, pulse_ticks=16, refresh_tick=32)
        residuals.append(old_read.close(model[view + '.frozen'], original[:, mult::mult] @ phase.T @ receiver.T,
            'SCI02-B frozen affine response', scale=scale))
        for panel in (0, 1):
            stem = f'{view}.p{panel}'
            images = model[stem + '.h32_actions']
            residuals.append(action_check(design, observation[stem + '.positions'][0],
                observation[stem + '.alpha_tilde'][0], basis, images))
            h32 = (basis.T @ images + images.T @ basis) / 2
            old_read.close(model[stem + '.h32_projected'], h32, 'SCI02-B projected update')
            states = affine_response_window(h0, h32, np.eye(len(h0)), basis.T @ force,
                timestep=numerical.timestep, friction=numerical.friction_gamma,
                primary_horizon=64, pulse_ticks=16, refresh_tick=32)
            residuals.append(old_read.close(model[stem + '.updated'], states[:, mult::mult] @ phase.T @ receiver.T,
                'SCI02-B updated affine response', scale=scale))
            old_read.close(model[stem + '.own_state'], states[:, [0, 32 * mult, 64 * mult]], 'SCI02-B own affine state')
            old_read.same(model[stem + '.own_state'][:, :2], model[view + '.own_state'][:, :2], 'SCI02-B retained prefix state')
    return np.asarray(residuals, dtype='<f8')


def native_response(design, handoff, instrument, reference, *, baseline=None):
    """Every paired branch and both noise bridges; no trajectory generation."""
    result = {}
    for view, mult in VIEWS:
        for panel in (0, 1):
            stem = f'{view}.p{panel}'
            hold = {key: reference[f'branch.{stem}.a0.hold.' + key]
                for key in ('positions', 'momenta', 'alpha_tilde', 'ticks', 'innovations')}
            if baseline is not None:
                for key, value in hold.items():
                    count = 32 * mult + int(key != 'innovations')
                    old_read.same(value[:count], baseline[f'branch.{stem}.a0.hold.' + key], 'SCI02-B original paid HOLD prefix')
            native = []
            for index, direction in enumerate(instrument['forces']):
                for sign, amplitude in (('minus', -.01), ('plus', .01), ('hold', 0.)):
                    branch = hold if sign == 'hold' else {key: reference[f'branch.{stem}.a{index}.{sign}.' + key] for key in hold}
                    old_read.same(branch['innovations'], hold['innovations'], 'SCI02-B within-panel coupled noise')
                    control = assess_scheduled_branch(design.coordinate, branch, refinement=mult,
                        start_tick=256 * mult, initial_positions=handoff[view + '_positions'][0],
                        initial_momenta=handoff[view + '_momenta'][0], direction=direction, amplitude=amplitude,
                        pulse_steps=16 * mult, tolerance=design.assay.native_reference_tolerance, control_id='control.sci02b.response')
                    if control.disposition != 'SATISFIED':
                        raise ValueError('SCI02-B literal response equations failed')
                    result[f'{stem}.a{index}.{sign}.residual'] = np.asarray(control.measured_errors, dtype='<f8')
                plus, minus = f'branch.{stem}.a{index}.plus.', f'branch.{stem}.a{index}.minus.'
                dq = (reference[plus + 'positions'] - reference[minus + 'positions']) / 2
                dp = (reference[plus + 'momenta'] - reference[minus + 'momenta']) / 2
                native.append((np.einsum('rsjab,tsjab->tr', instrument['receivers'][:, 0].conj(), dq)
                    + np.einsum('rsjab,tsjab->tr', instrument['receivers'][:, 1].conj(), dp)).real[mult::mult])
            result[stem + '.native'] = np.asarray(native, dtype='<f8')
    for panel in (0, 1):
        for kind, errors in zip(('innovation', 'bath'), _ou_errors(design.coordinate.primary_view,
                reference[f'branch.primary.p{panel}.a0.hold.innovations'], reference[f'branch.fine.p{panel}.a0.hold.innovations'],
                reference[f'bridge.p{panel}']), strict=True):
            if max(errors) > float(design.assay.native_reference_tolerance):
                raise ValueError('SCI02-B reference changes the original noise bridge')
            result[f'p{panel}.bridge.{kind}.residual'] = np.asarray(errors, dtype='<f8')
    return result


def error_curves(errors):
    """One cumulative curve per numerical view, preserving all nested operands."""
    norms = np.asarray([[np.linalg.norm(errors[f'{v}.p{p}'], axis=-1) for p in (0, 1)] for v, _ in VIEWS])
    return np.maximum.accumulate(np.max(norms[:, :, :, 15:, :], axis=(1, 2, 4)), axis=1)


def assess_pair(design, native, models):
    """Three complete recipe contrasts with the declared ORIGINAL/EARLY target."""
    scales = old.actuator_scales(design)
    arrays, measured, endpoint = {}, {}, {}
    factor, = (i for i, action in enumerate(design.assay.actions) if action.role == 'FACTOR')
    for recipe in native:
        endpoint[recipe] = {}
        for view, _ in VIEWS:
            for panel in (0, 1):
                stem = f'{view}.p{panel}'
                observed, estimate = native[recipe][stem + '.native'], models[recipe][stem + '.updated']
                error = (observed - estimate).reshape(4, 64, 2, 24) / scales[..., None]
                endpoint[recipe][stem] = error
                arrays[recipe.lower() + '.' + stem + '.error'] = error
                arrays[recipe.lower() + '.' + stem + '.native'] = observed
        curves = error_curves(endpoint[recipe])
        signal = min(np.linalg.norm(native[recipe][f'{v}.p{p}.native'][factor, -1, 24:]) / scales[factor, -1, 1]
            for v, _ in VIEWS for p in (0, 1))
        arrays[recipe.lower() + '.error_curves'] = curves
        measured.update({recipe + '.error': float(curves.max()), recipe + '.view_difference': float(np.abs(curves[0] - curves[1]).max()),
            recipe + '.signal': signal})
    for left, right in (('ORIGINAL', 'EARLY'), ('ORIGINAL', 'DELAYED'), ('EARLY', 'DELAYED')):
        if left not in endpoint or right not in endpoint:
            continue
        label = left + '_MINUS_' + right
        delta = {stem: endpoint[left][stem] - endpoint[right][stem] for stem in endpoint[left]}
        curves = error_curves(delta)
        for stem, value in delta.items():
            arrays[label.lower() + '.' + stem + '.error'] = value
        arrays[label.lower() + '.error_curves'] = curves
        measured.update({label + '.error': float(curves.max()), label + '.view_difference': float(np.abs(curves[0] - curves[1]).max())})
    error = max(measured[r + '.error'] for r in PAIR)
    contrast = measured['ORIGINAL_MINUS_EARLY.error']
    discrepancy = max(measured[r + '.view_difference'] for r in (*PAIR, 'ORIGINAL_MINUS_EARLY'))
    signal = min(measured[r + '.signal'] for r in PAIR)
    risk = max(error / .01, contrast / .01, discrepancy / .0001)
    measured.update({'primary.risk': risk, 'primary.log_risk': float(np.log1p(risk)),
        'primary.endpoint_error': error, 'primary.contrast_error': contrast,
        'primary.view_difference': discrepancy, 'primary.signal': signal,
        'primary.joint_success': int(risk <= 1. and signal >= .10), 'assigned': 1})
    return old.Computation(arrays, measurements=old.measurements(measured))


def check_fit(features, targets, fitted):
    """Independent augmented least squares, rather than the producer thin SVD."""
    mean, scale = np.mean(features, axis=0), np.std(features, axis=0)
    scale[scale == 0] = 1.
    old_read.close(fitted['feature_mean'], mean, 'SCI02-B training-only means')
    old_read.close(fitted['feature_scale'], scale, 'SCI02-B training-only scales')
    target = targets - np.mean(targets)
    expected = np.zeros((3, 4))
    for row, width in ((1, 2), (2, 4)):
        x = (features[:, :width] - mean[:width]) / scale[:width]
        expected[row, :width] = np.linalg.lstsq(np.vstack((x, np.eye(width))),
            np.concatenate((target, np.zeros(width))), rcond=None)[0]
    old_read.close(fitted['coefficients'], expected, 'SCI02-B independent ridge fit')
    old_read.close(fitted['intercepts'], np.array([np.median(targets), np.mean(targets), np.mean(targets)]), 'SCI02-B original intercepts')


def calibration_score(points, target):
    if points is None or target is None:
        return None
    if points.shape != (len(ACCOUNTS),) or not np.isfinite(points).all() or not np.isfinite(target):
        raise ValueError('SCI02-B calibration requires finite original account predictions')
    return Decimal(repr(float(max(0., np.max(target - points)))))
