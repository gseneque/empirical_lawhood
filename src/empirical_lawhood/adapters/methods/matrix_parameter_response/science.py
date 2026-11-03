"""Causal parameter origins and fully witnessed zero-fit BAOAB forecasts.

Only the copied causal archive and the public design reach the forecast.
Retained source tails and new innovations remain evaluator operands. All five
descriptions share one full native action/readout task and a zero fitting budget.
"""

from hashlib import sha256

import numpy as np

from empirical_lawhood.adapters.methods.matrix_factor_lifetime.science import eligible_origins
from empirical_lawhood.adapters.methods.matrix_parameter_factor.records import expected_members as factor_members, prefix
from empirical_lawhood.adapters.methods.matrix_parameter_history.records import expected_members as history_members
from empirical_lawhood.adapters.simulators.six_matrix_response.gradients import SixMatrixParameters
from empirical_lawhood.adapters.simulators.six_matrix_response.model import SixMatrixState, hermiticity_residual
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_derivatives import hessian_image
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history import initial_parameter_state
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_response import native_constant_response_branch, validate_future_view
from empirical_lawhood.adapters.simulators.six_matrix_response.shooting import hermitian_basis
from empirical_lawhood.infrastructure.matrix_array_io import encode_matrix_arrays
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity

from .records import (
    SIGNS, MatrixParameterNativeResponses, MatrixParameterResponseArrays,
    MatrixParameterResponseForecast, MatrixParameterResponseOrigin,
    MatrixParameterResponseOriginSelection, identity,
)

PREDICTORS = ('FACTOR', 'FULL_COUPLED', 'GENERIC_SLOW', 'NORM_RADIUS', 'SPECTRA')
ORIGIN_MEMBERS = frozenset((
    'positions', 'momenta', 'alpha_tilde', 'ticks', 'frame', 'forces', 'receivers',
    'generic_basis', 'force_coefficients', 'trace_coefficients', 'receiver_coefficients',
    'complement_raw', 'complement_normalized', 'complement_gram', 'complement_inverse_sqrt',
    'complement_eigenvalues', 'complement_eigenvectors',
))
FORECAST_MEMBERS = frozenset((
    'origin_hessian', 'hessian_eigenvalues', 'hessian_eigenvectors', 'hessian_order',
    'matrix_eigenvalues', 'matrix_eigenvectors', 'radial_directions', 'radial_norms',
    *(f'modes_{name.lower()}' for name in PREDICTORS), *(name.lower() for name in PREDICTORS),
))


def frame_axes(frame):
    frame = np.asarray(frame)
    if (frame.shape != (3, 4, 4) or frame.dtype.str != '<c16'
            or not np.isfinite(frame).all() or hermiticity_residual(frame) > 1e-12
            or not np.allclose(np.einsum('iab,jab->ij', frame.conj(), frame), np.eye(3), atol=1e-12, rtol=0)
            or not np.allclose(np.trace(frame, axis1=-2, axis2=-1), 0, atol=1e-12, rtol=0)):
        raise ValueError('parameter response frame is unidentified, nonorthonormal or contains trace')
    return np.concatenate((np.eye(4, dtype='<c16')[None] / 2, frame))


def native_position_coordinates(values):
    return np.einsum('kab,sjab->sjk', hermitian_basis(4).conj(), values).real.reshape(96)


def native_position_lift(values):
    return np.einsum('sjk,kab->sjab', np.asarray(values).reshape(2, 3, 16), hermitian_basis(4))


def _real(value, shape, name):
    value = np.asarray(value)
    if value.shape != shape or value.dtype.str != '<f8' or not np.isfinite(value).all():
        raise ValueError(f'parameter response {name} changes exact finite real geometry')
    return value


def _instruments(design, frame, templates):
    if set(templates) != {'generic_basis', 'force_coefficients', 'trace_coefficients', 'receiver_coefficients'}:
        raise ValueError('parameter response instrument template census differs')
    axes = frame_axes(frame)
    generic = np.asarray(templates['generic_basis'])
    frame_axes(generic)
    coefficients = _real(templates['force_coefficients'], (2, 3, 3), 'force coefficients')
    trace = _real(templates['trace_coefficients'], (2, 3), 'trace coefficients')
    duals = _real(templates['receiver_coefficients'], (48, 2, 2, 3, 4), 'receiver coefficients')
    if (np.linalg.norm(coefficients) == 0 or np.linalg.norm(trace) == 0
            or not np.allclose(duals.reshape(48, 48) @ duals.reshape(48, 48).T,
                               np.eye(48), atol=1e-12, rtol=0)):
        raise ValueError('parameter response instruments lose their nonzero actions or complete dual chart')
    raw = generic - np.einsum('ic,cab->iab', np.einsum('cab,iab->ic', axes.conj(), generic).real, axes)
    gram = np.einsum('iab,jab->ij', raw.conj(), raw).real
    values, vectors = np.linalg.eigh(gram)
    if values[0] <= 1e-12:
        raise ValueError('parameter response comparison force loses its full complement span')
    inverse = (vectors / np.sqrt(values)) @ vectors.T
    complement = np.einsum('ij,jab->iab', inverse, raw)
    bases = {'FACTOR': frame, 'COMPLEMENT': complement, 'GENERIC': generic}
    forces = []
    for action in design.actions:
        force = trace[..., None, None] * axes[0] if action.role == 'TRACE' else np.einsum(
            'sjc,cab->sjab', coefficients, bases[action.role])
        length = np.linalg.norm(force)
        if not np.isfinite(length) or length <= 0:
            raise ValueError('parameter response action has no resolved physical force')
        forces.append(force * (float(action.force_norm) / length))
    return {
        'forces': np.asarray(forces, dtype='<c16'),
        'receivers': np.asarray(np.einsum('rpsjc,cab->rpsjab', duals, axes), dtype='<c16'),
        'generic_basis': np.asarray(generic, dtype='<c16').copy(),
        'force_coefficients': coefficients.copy(), 'trace_coefficients': trace.copy(),
        'receiver_coefficients': duals.copy(),
        'complement_raw': np.asarray(raw, dtype='<c16'),
        'complement_normalized': np.asarray(complement, dtype='<c16'),
        'complement_gram': np.asarray(gram, dtype='<f8'),
        'complement_inverse_sqrt': np.asarray(inverse, dtype='<f8'),
        'complement_eigenvalues': np.asarray(values, dtype='<f8'),
        'complement_eigenvectors': np.asarray(vectors, dtype='<f8'),
    }


def _history(design, arrays):
    coordinate = design.coordinate
    expected = history_members(coordinate)
    if set(arrays) != set(expected):
        raise ValueError('parameter response drops the original complete11 history members')
    initial = initial_parameter_state(coordinate)
    for name, (dtype, shape) in expected.items():
        value = arrays[name]
        if value.dtype.str != dtype or value.shape != shape or not np.isfinite(value).all():
            raise ValueError('parameter response history changes complete dtype/shape/finite population')
        if dtype == '<c16' and hermiticity_residual(value) > 1e-12:
            raise ValueError('parameter response historical state or innovations are non-Hermitian')
    for view, multiplier in (('primary', 1), ('fine', 2)):
        count = coordinate.total_ticks * multiplier + 1
        if not np.array_equal(arrays[view + '_ticks'], np.arange(count, dtype='<i8')):
            raise ValueError('parameter response history substitutes its original absolute native ticks')
        alpha = np.asarray([coordinate.couplings(t, refinement=multiplier) for t in range(count)], dtype='<f8')
        if not np.array_equal(arrays[view + '_alpha_tilde'], alpha):
            raise ValueError('parameter response history substitutes exact realized source couplings')
        if (not np.array_equal(arrays[view + '_positions'][0], initial.positions)
                or not np.array_equal(arrays[view + '_momenta'][0], initial.momenta)):
            raise ValueError('parameter response history changes its original family initial state')


def make_origin_arrays(design, history_arrays, factor_arrays, templates, tick=None):
    """Copy every causal PRIMARY coordinate; original tails never reach forecast."""
    tick = design.origin_tick if tick is None else tick
    if tick != design.origin_tick or tick not in design.rule.lattice:
        raise ValueError('parameter response changes the frozen causal origin tick')
    validate_future_view(design.coordinate, design.view)
    _history(design, history_arrays)
    expected = factor_members(design.rule)
    if set(factor_arrays) != set(expected) or any(
            a.dtype.str != expected[n][0] or a.shape != expected[n][1] for n, a in factor_arrays.items()):
        raise ValueError('parameter response drops the original complete factor40 witness')
    for view in ('PRIMARY', 'FINE'):
        for sector in design.rule.sectors:
            if not np.array_equal(factor_arrays[prefix(view, sector) + 'ticks'],
                                  np.asarray(design.rule.lattice, dtype='<i8')):
                raise ValueError('parameter response factor clock substitutes the declared full lattice')
    base, index = prefix('PRIMARY', design.factor_sector), design.rule.lattice.index(tick)
    if not factor_arrays[base + 'available'][index] or not factor_arrays[base + 'identifiable'][index]:
        raise ValueError('parameter response origin has no available identified factor witness')
    frame = np.asarray(factor_arrays[base + 'aligned_factor'][index], dtype='<c16').copy()
    selected = np.asarray((float(design.alpha_x), float(design.alpha_y)), dtype='<f8')
    if (tick < design.coordinate.ramp_ticks
            or not np.array_equal(history_arrays['primary_alpha_tilde'][tick:],
                                  np.broadcast_to(selected, history_arrays['primary_alpha_tilde'][tick:].shape))
            or not np.array_equal(history_arrays['fine_alpha_tilde'][2*tick:],
                                  np.broadcast_to(selected, history_arrays['fine_alpha_tilde'][2*tick:].shape))):
        raise ValueError('parameter response origin is outside its exact constant autonomous region')
    arrays = {name: np.asarray(history_arrays['primary_' + name][:tick + 1]).copy()
              for name in ('positions', 'momenta', 'alpha_tilde', 'ticks')}
    arrays['frame'] = frame
    arrays.update(_instruments(design, frame, templates))
    validate_origin_values(design, arrays)
    return arrays


def validate_origin_values(design, arrays):
    """Causal-only array census and literal declared instrument-role joins."""
    if set(arrays) != ORIGIN_MEMBERS:
        raise ValueError('parameter response origin changes its complete causal array census')
    expected = (design.origin_tick + 1, 2, 3, 4, 4)
    for name in ('positions', 'momenta'):
        if (arrays[name].shape != expected or arrays[name].dtype.str != '<c16'
                or not np.isfinite(arrays[name]).all() or hermiticity_residual(arrays[name]) > 1e-12):
            raise ValueError('parameter response origin loses full192 causal phase coordinates')
    if (arrays['ticks'].dtype.str != '<i8'
            or not np.array_equal(arrays['ticks'], np.arange(design.origin_tick + 1, dtype='<i8'))
            or arrays['alpha_tilde'].dtype.str != '<f8' or arrays['alpha_tilde'].shape != (design.origin_tick + 1, 2)):
        raise ValueError('parameter response origin changes native clock or realized couplings')
    alpha = np.asarray([design.coordinate.couplings(t) for t in range(design.origin_tick + 1)], dtype='<f8')
    if (not np.array_equal(arrays['alpha_tilde'], alpha)
            or tuple(float(x).hex() for x in arrays['alpha_tilde'][-1]) !=
               (float(design.alpha_x).hex(), float(design.alpha_y).hex())):
        raise ValueError('parameter response origin substitutes retained versus normative coupling bits')
    frame_axes(arrays['frame'])
    templates = {name: arrays[name] for name in (
        'generic_basis', 'force_coefficients', 'trace_coefficients', 'receiver_coefficients')}
    expected_instruments = _instruments(design, arrays['frame'], templates)
    for name, value in expected_instruments.items():
        # Exact construction pins the declared labels, not merely force norms.
        if arrays[name].dtype != value.dtype or arrays[name].shape != value.shape or not np.allclose(
                arrays[name], value, atol=2e-12, rtol=2e-12):
            raise ValueError('parameter response origin substitutes action/receiver/complement witness')


def origin_hessian(design, arrays):
    """Analytic full96 derivative with selected M, beta, Gamma and observed alpha."""
    position = arrays['positions'][-1]
    selected = SixMatrixParameters(2, float(design.member.mass_x), float(design.member.mass_y),
        float(design.member.cross_coupling_gamma), float(design.alpha_x), float(design.alpha_y))
    basis = np.eye(96, dtype='<f8')
    hessian = np.column_stack([native_position_coordinates(hessian_image(
        position, native_position_lift(direction), selected)) for direction in basis])
    if not np.isfinite(hessian).all() or not np.allclose(hessian, hessian.T, atol=1e-10, rtol=1e-12):
        raise ValueError('parameter response full native Hessian is nonfinite or nonselfadjoint')
    return np.asarray((hessian + hessian.T) / 2, dtype='<f8')


def _block_modes(axes_by_matrix):
    columns = []
    for index, axes in enumerate(axes_by_matrix):
        for axis in axes:
            native = np.zeros((2, 3, 4, 4), dtype='<c16')
            native.reshape(6, 4, 4)[index] = axis
            columns.append(native_position_coordinates(native))
    return np.asarray(columns, dtype='<f8').T


def reduction_witnesses(design, arrays, hessian):
    modes = {'FACTOR': _block_modes([frame_axes(arrays['frame'])] * 6), 'FULL_COUPLED': np.eye(96)}
    unavailable, radial, spectra = {}, [], []
    lengths, directions, matrix_values, matrix_vectors = [], [], [], []
    for matrix in arrays['positions'][-1].reshape(6, 4, 4):
        traceless = matrix - np.trace(matrix) * np.eye(4) / 4
        length = float(np.linalg.norm(traceless))
        lengths.append(length)
        direction = np.zeros((4, 4), dtype='<c16') if length <= 1e-12 else traceless / length
        directions.append(direction)
        if length <= 1e-12:
            unavailable['NORM_RADIUS'] = 'ORIGIN_RADIAL_DIRECTION_UNRESOLVED'
        radial.append(np.stack((np.eye(4) / 2, direction)))
        values, vectors = np.linalg.eigh(matrix)
        matrix_values.append(values)
        matrix_vectors.append(vectors)
        if np.min(np.diff(values)) <= float(design.spectral_gap_minimum):
            unavailable['SPECTRA'] = 'ORIGIN_NATIVE_MATRIX_SPECTRUM_DEGENERATE'
        spectra.append(np.asarray([np.outer(v, v.conj()) for v in vectors.T]))
    if 'NORM_RADIUS' not in unavailable:
        modes['NORM_RADIUS'] = _block_modes(radial)
    if 'SPECTRA' not in unavailable:
        modes['SPECTRA'] = _block_modes(spectra)
    values, vectors = np.linalg.eigh(hessian)
    order = np.argsort(np.abs(values), kind='stable')
    if abs(values[order[24]]) - abs(values[order[23]]) <= float(design.generic_gap_minimum):
        unavailable['GENERIC_SLOW'] = 'ORIGIN_NATIVE_SLOW_MODE_CUTOFF_DEGENERATE'
    else:
        modes['GENERIC_SLOW'] = vectors[:, order[:24]]
    witness = {
        'origin_hessian': np.asarray(hessian, dtype='<f8'),
        'hessian_eigenvalues': np.asarray(values, dtype='<f8'),
        'hessian_eigenvectors': np.asarray(vectors, dtype='<f8'),
        'hessian_order': np.asarray(order, dtype='<i8'),
        'matrix_eigenvalues': np.asarray(matrix_values, dtype='<f8'),
        'matrix_eigenvectors': np.asarray(matrix_vectors, dtype='<c16'),
        'radial_directions': np.asarray(directions, dtype='<c16'),
        'radial_norms': np.asarray(lengths, dtype='<f8'),
    }
    for name in PREDICTORS:
        witness['modes_' + name.lower()] = np.asarray(modes.get(name, np.empty((96, 0))), dtype='<f8')
    return modes, unavailable, witness


def _linear_response(design, modes, hessian, force, receivers, action):
    """Native-order discrete origin-linearized odd response with both kicks."""
    dt = float(design.view.timestep)
    # Match the simulator's separate binary64 conversions, not Decimal gamma*dt.
    decay = float(np.exp(-float(design.view.friction_gamma) * dt))
    reduced_hessian = modes.T @ hessian @ modes
    reduced_force = modes.T @ native_position_coordinates(force) * float(action.amplitude)
    position = np.zeros(modes.shape[1])
    momentum = np.zeros_like(position)
    output = []
    for tick in range(1, design.horizon_steps[-1] + 1):
        kick = .5 * dt * reduced_force if tick <= action.pulse_steps else np.zeros_like(momentum)
        momentum += kick
        momentum -= .5 * dt * (reduced_hessian @ position)
        position += .5 * dt * momentum
        momentum *= decay
        position += .5 * dt * momentum
        momentum -= .5 * dt * (reduced_hessian @ position)
        momentum += kick
        if tick in design.horizon_steps:
            native = np.stack((native_position_lift(modes @ position), native_position_lift(modes @ momentum)))
            output.append(np.einsum('rpsjab,psjab->r', receivers.conj(), native).real)
    return np.asarray(output, dtype='<f8')


def forecast_values(design, arrays, model):
    validate_origin_values(design, arrays)
    if (ObjectIdentity.from_record(model.model_id, model) != design.model
            or model.predictors != PREDICTORS or model.fitting_budget != 0):
        raise ValueError('parameter response forecast substitutes the frozen zero-fit model')
    hessian = origin_hessian(design, arrays)
    modes, unavailable, forecast = reduction_witnesses(design, arrays, hessian)
    dispositions = []
    for name in PREDICTORS:
        if name in unavailable:
            forecast[name.lower()] = np.full((4, len(design.horizon_steps), 48), np.nan, dtype='<f8')
            dispositions.append((name, 'UNRESOLVED', unavailable[name]))
        else:
            forecast[name.lower()] = np.asarray([_linear_response(design, modes[name], hessian, force,
                arrays['receivers'], action) for force, action in zip(arrays['forces'], design.actions, strict=True)], dtype='<f8')
            if not np.isfinite(forecast[name.lower()]).all():
                raise ValueError('parameter response prediction is numerically nonfinite')
            dispositions.append((name, 'AVAILABLE', None))
    return forecast, tuple(dispositions), tuple(sorted(n.lower() for n in unavailable))


def array_product(arrays, *, producers, artifact_id, operand_id, role='ORIGIN', nonfinite=()):
    """Publish the new member contract without aliasing an old scientific type."""
    raw, members = encode_matrix_arrays(arrays, nonfinite_members=nonfinite)
    artifact = ArtifactIdentity(artifact_id, 'parameter-response-' + role.lower(), MATRIX_ARRAY_SCHEMA,
        sha256(raw).hexdigest(), 'application/x-npz', len(raw))
    saved = MatrixParameterResponseArrays(operand_id, artifact, members,
        tuple(sorted(set(producers), key=lambda p: p.object_id)))
    return raw, saved


def origin_record(source, history_arrays, factor_arrays, templates, factor_product, *, artifact_id):
    """An authenticated source caller supplies the actual history/factor joins."""
    d, public = source.design, source.causal
    if (identity(factor_product) != public.factor_product
            or factor_product.source != public.factor_source
            or factor_product.root_id != source.root.root_id
            or factor_product.independent_group_id != source.root.independent_group_id
            or factor_product.source_state != 'COMPLETED' or factor_product.history_numerical_pass is not True):
        raise ValueError('parameter response origin substitutes the authenticated factor product')
    traces = tuple(t for t in factor_product.traces if (t.view, t.sector) == ('PRIMARY', d.factor_sector))
    if len(traces) != 1 or traces[0].rule != d.rule.identity:
        raise ValueError('parameter response origin loses its unique actual PRIMARY sector trace')
    candidates = tuple(t for t in eligible_origins(traces[0], d.rule)
        if t >= d.coordinate.ramp_ticks and (d.ramp_boundary == 'AT_RAMP_END' or t > d.coordinate.ramp_ticks))
    if not candidates or candidates[0] != d.origin_tick:
        raise ValueError('parameter response changes its first causally eligible constant-region origin')
    arrays = make_origin_arrays(d, history_arrays, factor_arrays, templates)
    frame_sha = sha256(np.ascontiguousarray(arrays['frame'], dtype='<c16').tobytes()).hexdigest()
    selection = MatrixParameterResponseOriginSelection('selection.' + public.source_id, identity(public),
        source.root.root_id, source.root.independent_group_id,
        ObjectIdentity.from_record(d.coordinate.coordinate_id, d.coordinate), 'COMPLETED', 'SELECTED',
        d.origin_tick, d.cutoff, frame_sha, ('first-causal-primary-constant-region-origin',))
    raw, saved = array_product(arrays, producers=(identity(public), identity(d)), artifact_id=artifact_id,
        operand_id='arrays.origin.' + public.source_id)
    origin = MatrixParameterResponseOrigin('origin.' + public.source_id, identity(public), d,
        source.root.root_id, source.root.independent_group_id, source.root.clock_id, saved, frame_sha, selection)
    return raw, origin


def validate_origin_arrays(origin, arrays):
    validate_origin_values(origin.design, arrays)
    if (sha256(np.ascontiguousarray(arrays['frame'], dtype='<c16').tobytes()).hexdigest() != origin.frame_sha256
            or origin.arrays.producers != tuple(sorted((origin.source, identity(origin.design)), key=lambda p: p.object_id))):
        raise ValueError('parameter response origin substitutes its public source/frame producers')


def forecast(origin, arrays, model, *, artifact_id):
    validate_origin_arrays(origin, arrays)
    values, dispositions, nonfinite = forecast_values(origin.design, arrays, model)
    raw, saved = array_product(values, producers=(identity(origin), identity(model)), artifact_id=artifact_id,
        operand_id='arrays.forecast.' + origin.origin_id, role='FORECAST', nonfinite=nonfinite)
    return raw, MatrixParameterResponseForecast('forecast.' + origin.origin_id, identity(origin), identity(model),
        origin.design.cutoff, saved, dispositions)


def branch_census(source):
    return tuple(sorted((f'{s.panel_id}.{a.action_id}.{sign.lower()}', s, a, sign)
        for s in source.root.streams for a in source.design.actions for sign in SIGNS))


def native_branch(source, origin, past, forecast_record, branch, innovations):
    """Numerical child only; bindings own actual guards, receipts and streams."""
    validate_origin_arrays(origin, past)
    if (origin.source != identity(source.causal) or origin.design != source.design
            or forecast_record.origin != identity(origin) or forecast_record.model != source.design.model
            or forecast_record.cutoff != source.design.cutoff or branch not in branch_census(source)):
        raise ValueError('parameter native response changes committed source/origin/forecast/branch census')
    _, _, action, sign = branch
    d = source.design
    if len(innovations) != d.horizon_steps[-1]:
        raise ValueError('parameter native response drops its declared complete innovation horizon')
    state = SixMatrixState(2, past['positions'][-1], past['momenta'][-1], d.origin_tick,
        float(d.alpha_x), float(d.alpha_y))
    amplitude = float(action.amplitude) * {'HOLD': 0, 'MINUS': -1, 'PLUS': 1}[sign]
    return native_constant_response_branch(state, member=d.member, numerical_view=d.view,
        direction=past['forces'][d.actions.index(action)], amplitude=amplitude,
        pulse_steps=action.pulse_steps, innovations=innovations,
        alpha_tilde_x=float(d.alpha_x), alpha_tilde_y=float(d.alpha_y))


def responses(source, origin, forecast_record, branches, events, *, artifact_id):
    expected = tuple(b[0] for b in branch_census(source))
    if (tuple(sorted(branches)) != expected or tuple(e.branch_id for e in events) != expected
            or origin.source != identity(source.causal) or forecast_record.origin != identity(origin)):
        raise ValueError('parameter response publication drops an actual panel/action/sign/event')
    count = source.design.horizon_steps[-1]
    selected = np.asarray((float(source.design.alpha_x), float(source.design.alpha_y)), dtype='<f8')
    for values in branches.values():
        if set(values) != {'positions', 'momenta', 'noise', 'alpha_tilde', 'ticks'}:
            raise ValueError('parameter response native publication drops full state/noise/coupling/clock')
        for name in ('positions', 'momenta', 'noise'):
            value = values[name]
            length = count if name == 'noise' else count + 1
            if (value.dtype.str != '<c16' or value.shape != (length, 2, 3, 4, 4)
                    or not np.isfinite(value).all() or hermiticity_residual(value) > 1e-12):
                raise ValueError('parameter response native publication changes complete finite Hermitian state')
        if (values['alpha_tilde'].dtype.str != '<f8'
                or not np.array_equal(values['alpha_tilde'], np.broadcast_to(selected, (count + 1, 2)))
                or values['ticks'].dtype.str != '<i8'
                or not np.array_equal(values['ticks'], np.arange(source.design.origin_tick,
                    source.design.origin_tick + count + 1, dtype='<i8'))
                or not np.array_equal(values['positions'][0], branches[expected[0]]['positions'][0])
                or not np.array_equal(values['momenta'][0], branches[expected[0]]['momenta'][0])):
            raise ValueError('parameter response native publication changes constant realization/shared initial clock')
    arrays = {f'{branch}.{name}': value for branch, values in branches.items() for name, value in values.items()}
    raw, saved = array_product(arrays, producers=(identity(source), identity(origin), identity(forecast_record)),
        artifact_id=artifact_id, operand_id='arrays.responses.' + source.source_id, role='NATIVE_RESPONSES')
    return raw, MatrixParameterNativeResponses('responses.' + source.source_id, identity(source), identity(origin),
        identity(forecast_record), expected, saved, tuple(events))
