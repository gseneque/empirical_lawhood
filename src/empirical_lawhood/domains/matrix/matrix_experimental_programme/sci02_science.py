# SPDX-License-Identifier: MPL-2.0
"""SCI02 composition of existing preparation, instrument and response kernels.

RNG entry is confined to acquire_preparation_interval/acquire_response_interval.
The native runner owns contact and custody. Shadow/model functions accept no
stream operands or future response arrays.
"""
from dataclasses import dataclass
from decimal import Decimal
from types import SimpleNamespace
import time

import numpy as np

from empirical_lawhood.domains.matrix.matrix_factor_lifetime.science import measure_sector
from empirical_lawhood.domains.matrix.matrix_factor_response.mechanism_readout import MechanismUnavailable, hold_tangent_window, input_krylov_basis
from empirical_lawhood.domains.matrix.matrix_factor_response.refresh_science import continue_response_window, lift_states, receiver_matrix
from empirical_lawhood.domains.matrix.matrix_factor_response.response_scoring import nominal_actuator_scales
from empirical_lawhood.domains.matrix.matrix_factor_response.science import _block_modes, frame_axes, native_position_coordinates, origin_io_system
from empirical_lawhood.domains.matrix.matrix_scheduled_history.response_forecast import InstrumentUnresolved, _hessian, instrument
from empirical_lawhood.domains.matrix.matrix_scheduled_history.response_native import native_scheduled_branch
from empirical_lawhood.domains.matrix.six_matrix_response.model import SixMatrixState
from empirical_lawhood.domains.matrix.six_matrix_response.parameter_history import initial_parameter_state, split_parameter_innovations
from empirical_lawhood.domains.matrix.six_matrix_response.parameter_history_segments import ParameterGeneratorState
from empirical_lawhood.domains.matrix.six_matrix_response.simulation import hermitian_noise

from empirical_lawhood.domains.matrix.matrix_experimental_programme.preparation_intervals import propagate_interval
from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02_records import METHODS, RECIPES, Sci02Design


@dataclass(frozen=True, slots=True)
class PreparationContext:
    design: Sci02Design
    recipe: object
    total_ticks: int = 256
    q: int = 2

    @property
    def member(self): return self.design.coordinate.member
    @property
    def primary_view(self): return self.design.coordinate.primary_view
    @property
    def fine_view(self): return self.design.coordinate.fine_view


@dataclass(frozen=True, slots=True)
class Computation:
    arrays: dict
    disposition: str = 'AVAILABLE'
    reasons: tuple[str, ...] = ()
    generators: tuple = ()
    measurements: tuple = ()


def measurements(values):
    return tuple((key, None if value is None else Decimal(repr(float(value)))) for key, value in sorted(values.items()))


def unavailable(reason):
    return Computation({'unavailable': np.array([1], dtype='<i8')}, 'UNAVAILABLE', (reason,))


def state_at(arrays, view, index=-1):
    return SixMatrixState(2, arrays[view + '_positions'][index], arrays[view + '_momenta'][index],
        int(arrays[view + '_ticks'][index]), *arrays[view + '_alpha_tilde'][index])


def project_state(arrays, *, tick):
    """Drop innovations and RNG state before a scientific prediction boundary."""
    out = {}
    for view, mult in (('primary', 1), ('fine', 2)):
        where = np.flatnonzero(arrays[view + '_ticks'] == mult * tick)
        if len(where) != 1:
            raise ValueError('SCI02 projection lacks its exact permitted absolute observation')
        for name in ('positions', 'momenta', 'alpha_tilde', 'ticks'):
            out[view + '_' + name] = arrays[view + '_' + name][where].copy()
    return Computation(out)


def validate_generators(streams, saved, count, panel):
    """Read-only cursor validation belongs before actual native contact."""
    current = {row.purpose: row for p, row in saved if p == panel}
    if len(current) != sum(p == panel for p, _ in saved) or count and set(current) != {row.purpose for row in streams}:
        raise ValueError('SCI02 continuation omits an actual consumed generator')
    if not count and saved:
        raise ValueError('SCI02 initial acquisition cannot consume a prior generator checkpoint')
    for stream in streams:
        state = current.get(stream.purpose)
        if count and (state is None or state.effective_seed != stream.effective_seed or state.completed_noise_matrices != count):
            raise ValueError('SCI02 continuation changes its exact original draw position')
    return current


def _generators(streams, saved, count, panel):
    current = validate_generators(streams, saved, count, panel)
    values = {}
    for stream in streams:
        generator = np.random.Generator(np.random.PCG64DXSM(stream.effective_seed))
        if count:
            state = current.get(stream.purpose)
            if state is None or state.effective_seed != stream.effective_seed or state.completed_noise_matrices != count:
                raise ValueError('SCI02 continuation changes its exact original draw position')
            generator.bit_generator.state = state.numpy_state()
        elif saved:
            raise ValueError('SCI02 initial acquisition cannot consume a prior generator checkpoint')
        values[stream.purpose] = generator
    return values


def _save_generators(streams, generators, count, panel):
    rows = []
    for stream in streams:
        value = generators[stream.purpose].bit_generator.state
        rows.append((panel, ParameterGeneratorState(stream.purpose, stream.effective_seed,
            value['state']['state'], value['state']['inc'], value['has_uint32'], value['uinteger'], count)))
    return tuple(rows)


def _noise_pair(generators, phase, count):
    return tuple(np.asarray([hermitian_noise(rng=generators[phase + '-' + suffix], q=2)
        for _ in range(count)], dtype='<c16') for suffix in ('coarse-driver', 'fine-bridge'))


def acquire_preparation_interval(design, recipe, streams, *, prefix=None, saved=(), on_step=None):
    """Actual RNG/native entry only after the ordinary runner's BEGIN."""
    start, stop = (0, 64) if prefix is None else (64, 256)
    selected = tuple(s for s in streams if s.purpose.startswith('preparation'))
    if len(selected) != 2 or recipe not in RECIPES or start == 0 and recipe != 'ORIGINAL':
        raise ValueError('SCI02 preparation changes its common-prefix stream or arm selection')
    generators = _generators(selected, saved, start, 0)
    coarse, bridge = _noise_pair(generators, 'preparation', stop - start)
    if prefix is None:
        primary = fine = initial_parameter_state(design.coordinate)
    else:
        primary, fine = (state_at(prefix, view) for view in ('primary', 'fine'))
    source = PreparationContext(design, design.recipe(recipe))
    arrays = propagate_interval(source, primary, fine, end_tick=stop,
        coarse_innovations=coarse, bridge_innovations=bridge, on_step=on_step)
    return Computation(arrays, generators=_save_generators(selected, generators, stop, 0),
        measurements=measurements({'native.integration_steps': 3 * (stop - start),
            'native.gradient_evaluations': 3 * (stop - start) + 2, 'rng.hermitian_matrices': 2 * (stop - start)}))


def _chart(position, rule):
    measured = measure_sector(position[1], rule)
    admitted = bool(measured.identifiable and measured.associative_leakage <= rule.associative_leakage_maximum
        and measured.lie_leakage <= rule.lie_leakage_maximum
        and measured.factor_fit_angle_degrees <= rule.factor_fit_angle_maximum_degrees)
    return measured.factor, admitted, measured


def fixed_instrument(design, past, templates):
    if set(past) != {v + '_' + n for v in ('primary', 'fine') for n in ('positions', 'momenta', 'ticks', 'alpha_tilde')}:
        raise ValueError('SCI02 instrument receives only the permitted source observation')
    if int(past['primary_ticks'][0]) != 64 or int(past['fine_ticks'][0]) != 128:
        raise ValueError('SCI02 physical task must be fixed at absolute source tick64')
    try:
        frame, admitted, measured = _chart(past['primary_positions'][0], design.factor_rule)
    except (ArithmeticError, np.linalg.LinAlgError):
        return unavailable('SOURCE_CHART_NUMERICAL_FAILURE')
    if frame is None: return unavailable('SOURCE_CHART_UNAVAILABLE')
    try:
        forces, receivers, witness = instrument(design.assay, frame, templates)
    except InstrumentUnresolved:
        return unavailable('SOURCE_INSTRUMENT_UNRESOLVED')
    receiver = receiver_matrix(receivers)
    gram = receiver @ receiver.T
    if np.linalg.norm(gram - np.eye(48)) > float(design.assay.receiver_gram_tolerance):
        raise ValueError('SCI02 inherited receiver does not preserve its orthonormal physical metric')
    return Computation({'forces': forces, 'receivers': receivers, 'source_frame': frame,
        'source_spectrum': measured.spectrum, 'source_low': measured.basis,
        'complement_spectrum': witness[0], 'complement_vectors': witness[1],
        'source_factor_admitted': np.array([int(admitted)], dtype='<i8')})


def actuator_scales(design):
    return np.asarray([[tuple(map(float, nominal_actuator_scales(action, Decimal('.001'), tick)))
        for tick in range(1, 65)] for action in design.assay.actions], dtype='<f8')


def origin_models(design, handoff, fixed):
    """Build every handoff model; no future observations or streams enter."""
    if int(handoff['primary_ticks'][0]) != 256 or int(handoff['fine_ticks'][0]) != 512:
        raise ValueError('SCI02 models require their actual handoff observation')
    coordinate = design.coordinate
    forces, receivers = fixed['forces'], fixed['receivers']
    force = np.stack([native_position_coordinates(f) * float(a.amplitude)
        for f, a in zip(forces, design.assay.actions, strict=True)], axis=1)
    receiver = receiver_matrix(receivers)
    try:
        frame, admitted, _ = _chart(handoff['primary_positions'][0], design.factor_rule)
    except (ArithmeticError, np.linalg.LinAlgError):
        frame, admitted = None, False
    out = {'forces': forces.copy(), 'receivers': receivers.copy(),
        'factor_admitted': np.array([int(admitted)], dtype='<i8')}
    if frame is not None: out['handoff_frame'] = frame
    protocol = SimpleNamespace(public_source=SimpleNamespace(coordinate=coordinate))
    reasons, costs = [], {}
    for view, mult in (('primary', 1), ('fine', 2)):
        numerical = getattr(coordinate, view + '_view')
        begun = time.process_time()
        try:
            h0 = _hessian(protocol, handoff[view + '_positions'][0], handoff[view + '_alpha_tilde'][0])
            costs[view + '.origin.hessian_cpu_seconds'] = time.process_time() - begun
            begun = time.process_time()
            values, vectors = np.linalg.eigh(h0)
        except (ArithmeticError, np.linalg.LinAlgError):
            reasons.append(view.upper() + '_ORIGIN_NUMERICAL_FAILURE')
            continue
        costs[view + '.origin.eigensystem_cpu_seconds'] = time.process_time() - begun
        # Basis construction and whitening retain the original physical H128.
        definition = SimpleNamespace(view=numerical, horizon_steps=tuple(range(1, 128 * mult + 1)))
        actions = tuple(SimpleNamespace(amplitude=a.amplitude, force_norm=a.force_norm, pulse_steps=16 * mult)
            for a in design.assay.actions)
        system = origin_io_system(definition, h0, forces, receivers, actions)
        bases = {'FULL': np.eye(96)}
        begun = time.process_time()
        try:
            krylov, _ = input_krylov_basis(system[0], system[1], values, vectors, native_horizon=128 * mult)
            bases['INPUT_KRYLOV48'] = krylov
        except MechanismUnavailable as exc:
            reasons.append(view.upper() + '_' + str(exc))
        costs[view + '.origin.krylov_cpu_seconds'] = time.process_time() - begun
        if frame is not None: bases['FACTOR'] = _block_modes([frame_axes(frame)] * 6)
        out.update({view + '.h0': h0, view + '.eigenvalues': values, view + '.eigenvectors': vectors})
        for method, basis in bases.items():
            begun = time.process_time()
            states = continue_response_window(h0, basis, force, timestep=numerical.timestep,
                friction=numerical.friction_gamma, primary_horizon=64, pulse_ticks=16, refresh_tick=32)
            out[view + '.basis.' + method.lower()] = basis
            out[view + '.state.' + method.lower()] = states[:, np.array((0, 32, 64)) * mult].copy()
            out[view + '.prediction.' + method.lower()] = lift_states(states[:, mult::mult], basis) @ receiver.T
            costs[view + '.origin.' + method.lower() + '_cpu_seconds'] = time.process_time() - begun
    return Computation(out, 'PARTIAL' if reasons else 'AVAILABLE', tuple(sorted(reasons)), measurements=measurements({'model.hessian_hvp_columns': 192, 'model.hessians': 2,
        'model.eigensystems': 2, 'model.krylov_bases': 2,
        'model.propagation_steps_four_actions': 192 * (3 if frame is not None else 2), **costs}))


def project_checkpoint(design, responses):
    out = {}
    for view, mult in (('primary', 1), ('fine', 2)):
        for panel in (0, 1):
            stem = f'branch.{view}.p{panel}.a0.hold.'
            if int(responses[stem + 'ticks'][-1]) != 288 * mult:
                raise ValueError('SCI02 checkpoint changes its exact relative tick32 cutoff')
            for name in ('positions', 'momenta', 'alpha_tilde', 'ticks'):
                out[f'{view}.p{panel}.' + name] = responses[stem + name][-1:].copy()
    return Computation(out)


def refresh_models(design, origin, observations):
    """Use only the isolated actual tick32 observation and the original basis."""
    out = dict(origin)
    force = np.stack([native_position_coordinates(f) * float(a.amplitude)
        for f, a in zip(origin['forces'], design.assay.actions, strict=True)], axis=1)
    receiver = receiver_matrix(origin['receivers'])
    protocol = SimpleNamespace(public_source=SimpleNamespace(coordinate=design.coordinate))
    costs, reasons = {}, []
    expected = {f'{v}.p{p}.' + n for v in ('primary', 'fine') for p in (0, 1)
        for n in ('positions', 'momenta', 'alpha_tilde', 'ticks')}
    if set(observations) != expected:
        raise ValueError('SCI02 refresh receives information outside its tick32 observation')
    for view, mult in (('primary', 1), ('fine', 2)):
        numerical = getattr(design.coordinate, view + '_view')
        if view + '.h0' not in origin:
            reasons.append(view.upper() + '_ORIGIN_UNAVAILABLE')
            continue
        for panel in (0, 1):
            stem = f'{view}.p{panel}'
            if observations[stem + '.ticks'].tolist() != [288 * mult]:
                raise ValueError('SCI02 refresh changes its permitted physical observation clock')
            begun = time.process_time()
            try:
                h32 = _hessian(protocol, observations[stem + '.positions'][0], observations[stem + '.alpha_tilde'][0])
            except (ArithmeticError, np.linalg.LinAlgError):
                reasons.append(view.upper() + f'_P{panel}_UPDATE_NUMERICAL_FAILURE')
                continue
            costs[stem + '.refresh.hessian_cpu_seconds'] = time.process_time() - begun
            out[stem + '.h32'] = h32
            for method in ('FULL', 'INPUT_KRYLOV48'):
                if view + '.basis.' + method.lower() not in origin:
                    continue
                basis = origin[view + '.basis.' + method.lower()]
                begun = time.process_time()
                states = continue_response_window(origin[view + '.h0'], basis, force,
                    timestep=numerical.timestep, friction=numerical.friction_gamma,
                    primary_horizon=64, pulse_ticks=16, refresh_tick=32, refresh_operator=h32)
                if not np.array_equal(states[:, 32 * mult], origin[view + '.state.' + method.lower()][:, 1]):
                    raise ValueError('SCI02 refresh resets its own accumulated model state')
                out[stem + '.state.' + method.lower() + '_refresh32'] = states[:, np.array((0, 32, 64)) * mult].copy()
                out[stem + '.prediction.' + method.lower() + '_refresh32'] = lift_states(states[:, mult::mult], basis) @ receiver.T
                costs[stem + '.refresh.' + method.lower() + '_cpu_seconds'] = time.process_time() - begun
    return Computation(out, 'PARTIAL' if reasons else 'AVAILABLE', tuple(sorted(reasons)), measurements=measurements({'refresh.hessian_hvp_columns': 384,
        'refresh.observations': 4, 'refresh.propagation_steps_four_actions': 768, **costs}))


def prediction(arrays, view, panel, method):
    prefix = f'{view}.p{panel}' if method.endswith('_REFRESH32') else view
    return arrays.get(prefix + '.prediction.' + method.lower())


def _response_arrays(coordinate, starts, forces, noise, *, start, stop, on_step=None):
    """Supplied-noise acquisition shared by actual entry and zero shadows."""
    arrays, done, costs = {}, 0, {'hold': 0., 'minus': 0., 'plus': 0.}
    for panel in (0, 1):
        coarse, bridge = noise[panel]
        fine = np.concatenate([split_parameter_innovations(coordinate, c, b)
            for c, b in zip(coarse, bridge, strict=True)])
        arrays[f'bridge.p{panel}'] = bridge.copy()
        for view, mult, values in (('primary', 1, coarse), ('fine', 2, fine)):
            for action, force in enumerate(forces):
                for sign, coefficient in (('hold', 0), ('minus', -1), ('plus', 1)):
                    stem = f'branch.{view}.p{panel}.a{action}.{sign}.'
                    if start == 0:
                        state = state_at(starts, view)
                    else:
                        state = SixMatrixState(2, starts[stem + 'positions'][-1], starts[stem + 'momenta'][-1],
                            int(starts[stem + 'ticks'][-1]), *starts[stem + 'alpha_tilde'][-1])
                    begun = time.process_time()
                    row = native_scheduled_branch(state, coordinate=coordinate, refinement=mult,
                        direction=force, amplitude=coefficient * .01 if start == 0 else 0., pulse_steps=16 * mult,
                        innovations=values, on_step=None)
                    # HOLD is identical across actions; action0 is the actually
                    # required causal observation for this panel and view.
                    if sign != 'hold' or action == 0:
                        costs[sign] += time.process_time() - begun
                    arrays.update({stem + name: value for name, value in row.items()})
                    done += (stop - start) * mult
                    if on_step is not None: on_step(done)
    return arrays, {'native.' + k + '_cpu_seconds': v for k, v in costs.items()}


def acquire_response_interval(design, starts, fixed, streams, *, start, saved=(), on_step=None):
    """One complete causal response half with original paired stream cursors."""
    if start not in (0, 32): raise ValueError('SCI02 response interval is not an admitted half')
    noise, states = {}, []
    for panel in (0, 1):
        selected = tuple(s for p, s in streams if p == panel and s.purpose.startswith('autonomous'))
        if len(selected) != 2: raise ValueError('SCI02 response loses a panel driver or bridge')
        generators = _generators(selected, saved, start, panel)
        noise[panel] = _noise_pair(generators, 'autonomous', 32)
        states.extend(_save_generators(selected, generators, start + 32, panel))
    arrays, costs = _response_arrays(design.coordinate, starts, fixed['forces'], noise, start=start, stop=start + 32, on_step=on_step)
    return Computation(arrays, generators=tuple(states), measurements=measurements({
        'native.integration_steps': 2304, 'native.gradient_evaluations': 2352,
        'rng.hermitian_matrices': 128, 'native.nested_branches': 48, **costs}))


def _shadow_forecasts(design, past, templates, *, recipes, fixed):
    """Three deterministic point hypotheses, with no future stream operand."""
    if fixed.disposition != 'AVAILABLE': return fixed
    out = dict(fixed.arrays)
    scales = actuator_scales(design)
    zero = np.zeros((192, 2, 3, 4, 4), dtype='<c16')
    for recipe in recipes:
        recipe_key = recipe.lower()
        source = PreparationContext(design, design.recipe(recipe))
        path = propagate_interval(source, state_at(past, 'primary'), state_at(past, 'fine'), end_tick=256,
            coarse_innovations=zero, bridge_innovations=zero)
        handoff = project_state(path, tick=256).arrays
        origin = origin_models(design, handoff, fixed.arrays).arrays
        observations, holds = {}, {}
        for view, mult in (('primary', 1), ('fine', 2)):
            hold = native_scheduled_branch(state_at(handoff, view), coordinate=design.coordinate, refinement=mult,
                direction=fixed.arrays['forces'][0], amplitude=0., pulse_steps=16 * mult,
                innovations=np.zeros((64 * mult, 2, 3, 4, 4), dtype='<c16'))
            holds[view] = hold
            for panel in (0, 1):
                for name in ('positions', 'momenta', 'alpha_tilde', 'ticks'):
                    observations[f'{view}.p{panel}.' + name] = hold[name][32 * mult:32 * mult + 1].copy()
        modeled = refresh_models(design, origin, observations).arrays
        if any(prediction(modeled, view, 0, 'FULL_REFRESH32') is None for view in ('primary', 'fine')):
            raise MechanismUnavailable('SHADOW_ORIGIN_OR_UPDATE_UNAVAILABLE')
        if 'handoff_frame' in origin:
            out[recipe_key + '.handoff_frame'] = origin['handoff_frame']
        out[recipe_key + '.factor_admitted'] = origin['factor_admitted']
        for view, mult in (('primary', 1), ('fine', 2)):
            hold = holds[view]
            for name in ('positions', 'momenta', 'alpha_tilde', 'ticks'):
                out[f'{recipe_key}.{view}.shadow-preparation.{name}'] = path[view + '_' + name]
                out[f'{recipe_key}.{view}.shadow-hold.{name}'] = hold[name]
            for name in ('h0', 'eigenvalues', 'eigenvectors', 'basis.input_krylov48'):
                if view + '.' + name in origin:
                    out[f'{recipe_key}.{view}.' + name] = origin[view + '.' + name]
            if view + '.basis.factor' in origin:
                out[f'{recipe_key}.{view}.basis.factor'] = origin[view + '.basis.factor']
            out[f'{recipe_key}.{view}.h32'] = modeled[f'{view}.p0.h32']
            tangent = hold_tangent_window(hold['positions'], hold['alpha_tilde'], fixed.arrays['forces'], fixed.arrays['receivers'],
                member=design.coordinate.member, numerical_view=getattr(design.coordinate, view + '_view'),
                primary_horizon=64, pulse_ticks=16)[:, mult - 1::mult]
            out[f'{recipe_key}.{view}.tangent'] = tangent
            out[f'{recipe_key}.{view}.signal'] = np.linalg.norm(tangent.reshape(4, 64, 2, 24), axis=-1) / scales
            for method in METHODS:
                estimate = prediction(modeled, view, 0, method)
                if estimate is None: continue
                out[f'{recipe_key}.{view}.prediction.{method.lower()}'] = estimate
                out[f'{recipe_key}.{view}.error.{method.lower()}'] = (tangent - estimate).reshape(4, 64, 2, 24) / scales[..., None]
                full = prediction(modeled, view, 0, 'FULL_REFRESH32' if method.endswith('_REFRESH32') else 'FULL')
                out[f'{recipe_key}.{view}.signed.{method.lower()}'] = np.stack((tangent - full, full - estimate)).reshape(2, 4, 64, 2, 24) / scales[None, ..., None]
    return Computation(out, measurements=measurements({'shadow.preparation_steps': 576 * len(recipes),
        'shadow.hold_steps': 192 * len(recipes), 'shadow.hessian_hvp_columns': 576 * len(recipes), 'shadow.krylov_bases': 2 * len(recipes),
        'shadow.tangent_steps_four_actions': 192 * len(recipes), 'shadow.tangent_hvp_columns': 768 * len(recipes),
        'shadow.model_steps_four_actions': 1344 * len(recipes),
        'shadow.point_hypothesis_not_stochastic_bound': 1}))


def shadow_forecasts(design, past, templates):
    """Keep each unavailable point hypothesis without dropping actual arms."""
    fixed = fixed_instrument(design, past, templates)
    if fixed.disposition != 'AVAILABLE': return fixed
    arrays, costs, reasons = dict(fixed.arrays), {}, []
    for recipe in RECIPES:
        try:
            result = _shadow_forecasts(design, past, templates, recipes=(recipe,), fixed=fixed)
            arrays.update(result.arrays)
            for key, value in result.measurements:
                costs[key] = costs.get(key, Decimal(0)) + value
        except (ArithmeticError, np.linalg.LinAlgError, MechanismUnavailable) as exc:
            arrays[recipe.lower() + '.unavailable'] = np.array([1], dtype='<i8')
            reasons.append(recipe + '_SHADOW_' + type(exc).__name__.upper())
    costs['shadow.point_hypothesis_not_stochastic_bound'] = Decimal(1)
    costs['shadow.failed_recipes'] = Decimal(len(reasons))
    return Computation(arrays, 'PARTIAL' if reasons else 'AVAILABLE', tuple(sorted(reasons)), measurements=tuple(sorted(costs.items())))
