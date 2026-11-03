# SPDX-License-Identifier: MPL-2.0
"""Same-origin finite-dt forecasts and explicitly coupled future innovations.

The paired design reaches the predictor without private source or stream
operands. The simulator receives the complete chosen innovation panel and
retains every state; bindings own contact, custody and recovery.
"""

import numpy as np

from empirical_lawhood.adapters.simulators.six_matrix_response.model import SixMatrixState, hermiticity_residual
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_ou_domain import validate_parameter_ou_domain
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_response import native_constant_response_branch
from empirical_lawhood.adapters.simulators.six_matrix_response.shooting import brownian_bridge_split

from . import science
from .paired_records import (
    VIEWS, MatrixParameterPairedDesign, MatrixParameterPairedForecast,
    MatrixParameterPairedNative, identity,
)
from .records import PREDICTORS, SIGNS

MEMBERS = ('positions', 'momenta', 'noise', 'alpha_tilde', 'ticks')


def _linear_response(design, view, modes, hessian, force, receivers, action):
    dt = float(design.view(view).timestep)
    decay = float(np.exp(-float(design.view(view).friction_gamma) * dt))
    reduced = modes.T @ hessian @ modes
    drive = modes.T @ science.native_position_coordinates(force) * float(action.amplitude)
    position = np.zeros(modes.shape[1])
    momentum = np.zeros_like(position)
    horizons = design.horizon_steps(view)
    pulse = action.pulse_steps * design.multiplier(view)
    result = []
    for tick in range(1, horizons[-1] + 1):
        kick = .5 * dt * drive if tick <= pulse else np.zeros_like(momentum)
        momentum += kick
        momentum -= .5 * dt * (reduced @ position)
        position += .5 * dt * momentum
        momentum *= decay
        position += .5 * dt * momentum
        momentum -= .5 * dt * (reduced @ position)
        momentum += kick
        if tick in horizons:
            response = np.stack((science.native_position_lift(modes @ position),
                                 science.native_position_lift(modes @ momentum)))
            result.append(np.einsum('rpsjab,psjab->r', receivers.conj(), response).real)
    return np.asarray(result, dtype='<f8')


def forecast_values(design, past, model):
    """Five zero-fit descriptions at both clocks, with common mode witnesses."""
    if type(design) is not MatrixParameterPairedDesign:
        raise ValueError('paired prediction requires an actual paired public design')
    science.validate_origin_arrays(design.common_origin, past)
    primary = design.primary
    if identity(model) != primary.model or model.predictors != PREDICTORS or model.fitting_budget != 0:
        raise ValueError('paired prediction substitutes the frozen zero-fit model')
    hessian = science.origin_hessian(primary, past)
    modes, unavailable, result = science.reduction_witnesses(primary, past, hessian)
    dispositions = tuple((name, 'UNRESOLVED', unavailable[name]) if name in unavailable
                         else (name, 'AVAILABLE', None) for name in PREDICTORS)
    nonfinite = []
    for view in VIEWS:
        for name in PREDICTORS:
            key = view.lower() + '_' + name.lower()
            if name in unavailable:
                result[key] = np.full((4, len(primary.horizon_steps), 48), np.nan, dtype='<f8')
                nonfinite.append(key)
            else:
                result[key] = np.asarray([_linear_response(design, view, modes[name], hessian,
                    force, past['receivers'], action) for force, action in
                    zip(past['forces'], primary.actions, strict=True)], dtype='<f8')
                if not np.isfinite(result[key]).all():
                    raise ValueError('paired linear forecast is numerically nonfinite')
    return result, dispositions, tuple(sorted(nonfinite))


def forecast(design, past, model, *, artifact_id):
    values, dispositions, nonfinite = forecast_values(design, past, model)
    raw, saved = science.array_product(values, producers=(identity(design), identity(design.common_origin), identity(model)),
        artifact_id=artifact_id, operand_id='arrays.paired-forecast.' + design.design_id,
        role='PAIRED_FORECAST', nonfinite=nonfinite)
    return raw, MatrixParameterPairedForecast('forecast.' + design.design_id, identity(design),
        identity(design.common_origin), identity(model), saved, dispositions)


def _matrix(rng):
    value = np.zeros((4, 4), dtype='<c16')
    value[np.diag_indices(4)] = rng.normal(size=4)
    real, imaginary = rng.normal(size=6), rng.normal(size=6)
    index = 0
    for row in range(4):
        for column in range(row + 1, 4):
            entry = (real[index] + 1j * imaginary[index]) / np.sqrt(2)
            value[row, column], value[column, row] = entry, entry.conjugate()
            index += 1
    return value


def noise_panel(source, stream):
    """One selected PCG64 stream; coarse then bridge for every native matrix.

    The bridge is returned and retained. A cold independent reader can prove
    every fine innovation's coupling without opening any generator.
    """
    design = source.design
    if stream not in source.root.streams:
        raise ValueError('paired sampler receives an undeclared actual panel stream')
    validate_parameter_ou_domain(design.primary.coordinate)
    count = design.primary.horizon_steps[-1]
    half = float(np.exp(-float(design.primary.view.friction_gamma) * float(design.primary.view.timestep) / 2))
    rng = np.random.Generator(np.random.PCG64(stream.seed))
    coarse = np.zeros((count, 2, 3, 4, 4), dtype='<c16')
    bridge = np.zeros_like(coarse)
    fine = np.zeros((2 * count, 2, 3, 4, 4), dtype='<c16')
    for tick in range(count):
        for sector in range(2):
            for matrix in range(3):
                coarse[tick, sector, matrix] = _matrix(rng)
                bridge[tick, sector, matrix] = _matrix(rng)
        fine[2 * tick], fine[2 * tick + 1] = brownian_bridge_split(
            coarse_noise=coarse[tick], bridge_noise=bridge[tick], half_decay=half)
    return {'PRIMARY': coarse, 'FINE': fine, 'BRIDGE': bridge}


def noise_panels(source):
    """Pure fixture convenience; each Native child uses its one declared panel."""
    return {stream.panel_id: noise_panel(source, stream) for stream in source.root.streams}


def branch_census(source):
    """Every view, panel, force and sign retains its distinct child identity."""
    return tuple(sorted((view, f'{view.lower()}.{stream.panel_id}.{action.action_id}.{sign.lower()}',
        stream, action, sign) for view in VIEWS for stream in source.root.streams
        for action in source.design.primary.actions for sign in SIGNS))


def native_branch(source, past, branch, noises):
    design = source.design
    science.validate_origin_arrays(design.common_origin, past)
    if branch not in branch_census(source):
        raise ValueError('paired native branch substitutes the complete actual view/panel/action/sign census')
    view, _, _, action, sign = branch
    if type(noises) is not dict or set(noises) != {'PRIMARY', 'FINE', 'BRIDGE'}:
        raise ValueError('paired native requires its actual retained coarse/fine/bridge panel')
    for name, count in (('PRIMARY', design.primary.horizon_steps[-1]),
                        ('FINE', design.horizon_steps('FINE')[-1]),
                        ('BRIDGE', design.primary.horizon_steps[-1])):
        value = np.asarray(noises[name])
        if (value.dtype.str != '<c16' or value.shape != (count, 2, 3, 4, 4)
                or not np.isfinite(value).all() or hermiticity_residual(value) > 1e-12):
            raise ValueError('paired native drops finite Hermitian complete ' + name + ' panel')
    innovations = np.asarray(noises[view])
    if len(innovations) != design.horizon_steps(view)[-1]:
        raise ValueError('paired native branch drops complete selected numerical-view horizon')
    primary = design.primary
    state = SixMatrixState(2, past['positions'][-1], past['momenta'][-1], design.native_origin_tick(view),
        float(primary.alpha_x), float(primary.alpha_y))
    result = native_constant_response_branch(state, member=primary.member, numerical_view=design.view(view),
        direction=past['forces'][primary.actions.index(action)],
        amplitude=float(action.amplitude) * {'HOLD': 0, 'MINUS': -1, 'PLUS': 1}[sign],
        pulse_steps=action.pulse_steps * design.multiplier(view), innovations=innovations,
        alpha_tilde_x=float(primary.alpha_x), alpha_tilde_y=float(primary.alpha_y))
    result['bridge'] = np.asarray(noises['BRIDGE'], dtype='<c16').copy()
    return result


def responses(source, commitment, branches, events, panels, *, artifact_id):
    expected = tuple(sorted(b[1] for b in branch_census(source)))
    if (tuple(sorted(branches)) != expected or tuple(e.branch_id for e in events) != expected
            or commitment.design != identity(source.design)
            or commitment.origin != identity(source.design.common_origin)):
        raise ValueError('paired native publication drops actual branch/event or committed public design')
    values = {f'{branch}.{name}': arrays[name] for branch, arrays in sorted(branches.items())
              for name in MEMBERS}
    if any(set(a) != {*MEMBERS, 'bridge'} for a in branches.values()) or set(panels) != {s.panel_id for s in source.root.streams}:
        raise ValueError('paired native publication drops native members or an innovation panel')
    for view, branch, stream, _, _ in branch_census(source):
        if (not np.array_equal(branches[branch]['bridge'], panels[stream.panel_id]['BRIDGE'])
                or not np.array_equal(branches[branch]['noise'], panels[stream.panel_id][view])):
            raise ValueError('paired native publication substitutes actual child bridge or panel noise')
    for panel_id, panel in sorted(panels.items()):
        values[panel_id + '.bridge'] = panel['BRIDGE']
    raw, saved = science.array_product(values,
        producers=(identity(source), identity(source.design), identity(source.design.common_origin), identity(commitment)),
        artifact_id=artifact_id, operand_id='arrays.paired-responses.' + source.source_id, role='PAIRED_NATIVE')
    return raw, MatrixParameterPairedNative('responses.' + source.source_id, identity(source), identity(source.design),
        identity(source.design.common_origin), identity(commitment), expected, saved, events)
