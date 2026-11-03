# SPDX-License-Identifier: MPL-2.0
"""Cold parameter-response controls, with no forecast or native producer calls.

The independent gradient differentiates literal ordered trace words.  Forecast
witnesses make all mode and instrument choices inspectable without invoking an
eigensolver.  Conditional readback checks the complete authenticated supplied
innovations; it does not claim to regenerate their bit-generator provenance.
"""

from decimal import Decimal
from hashlib import sha256

import numpy as np

from empirical_lawhood.adapters.methods.matrix_factor_response.records import (
    PREDICTORS, SIGNS, MatrixFactorResponseScore,
)
from empirical_lawhood.adapters.methods.matrix_factor_lifetime.records import FactorRootRole
from empirical_lawhood.adapters.methods.matrix_parameter_factor.records import (
    expected_members as factor_members, prefix,
)
from empirical_lawhood.adapters.methods.matrix_parameter_history.independent import (
    potential_gradient,
)
from empirical_lawhood.adapters.methods.matrix_parameter_history.records import expected_members as history_members
from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays, encode_matrix_arrays
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA

from .records import (
    MatrixParameterNativeResponses, MatrixParameterResponseAssessment,
    MatrixParameterResponseControl, MatrixParameterResponseForecast,
    MatrixParameterResponseOrigin, MatrixParameterResponseSource, identity,
)


def native_basis():
    """The literal 96 real Hermitian coordinate vectors, including trace."""
    matrices = []
    for row in range(4):
        value = np.zeros((4, 4), dtype='<c16')
        value[row, row] = 1
        matrices.append(value)
    for imaginary in (False, True):
        for row in range(4):
            for column in range(row + 1, 4):
                value = np.zeros((4, 4), dtype='<c16')
                value[row, column] = (1j if imaginary else 1) / np.sqrt(2)
                value[column, row] = value[row, column].conjugate()
                matrices.append(value)
    result = np.zeros((96, 2, 3, 4, 4), dtype='<c16')
    for index in range(6):
        result.reshape(96, 6, 4, 4)[16 * index:16 * (index + 1), index] = matrices
    return result


def _coordinates(value):
    return np.einsum('ksjab,sjab->k', native_basis().conj(), value).real


def _lift(value):
    return np.einsum('k,ksjab->sjab', value, native_basis())


def _decimal(value):
    if not np.isfinite(value):
        raise ValueError('parameter response control residual is not finite')
    return Decimal(repr(float(value)))


def _array(values, name, shape, dtype='<f8', *, nonfinite=False):
    value = np.asarray(values[name])
    if value.shape != shape or value.dtype != np.dtype(dtype) or not nonfinite and not np.isfinite(value).all():
        raise ValueError('parameter response drops or changes complete witness ' + name)
    return value


def _close(actual, expected, name, tolerance=1e-10):
    if not np.allclose(actual, expected, rtol=tolerance, atol=tolerance, equal_nan=False):
        raise ValueError('parameter response changes independently reconstructed ' + name)


def _axes(frame):
    frame = np.asarray(frame)
    if frame.shape != (3, 4, 4) or frame.dtype != np.dtype('<c16') or not np.isfinite(frame).all():
        raise ValueError('parameter response frame loses complete finite Hermitian geometry')
    _close(frame, frame.conj().swapaxes(-1, -2), 'Hermitian frame', 1e-12)
    _close(np.einsum('iab,jab->ij', frame.conj(), frame), np.eye(3), 'frame orthonormality', 1e-12)
    _close(np.trace(frame, axis1=-2, axis2=-1), np.zeros(3), 'traceless frame', 1e-12)
    return np.concatenate((np.eye(4, dtype='<c16')[None] / 2, frame))


def _block_modes(matrix_axes):
    columns = []
    for index, axes in enumerate(matrix_axes):
        for axis in axes:
            value = np.zeros((2, 3, 4, 4), dtype='<c16')
            value.reshape(6, 4, 4)[index] = axis
            columns.append(_coordinates(value))
    return np.asarray(columns).T


def verify_instruments(design, past):
    """Reconstruct action roles and receiver duals, not just equal norms."""
    axes = _axes(past['frame'])
    generic = _array(past, 'generic_basis', (3, 4, 4), '<c16')
    _axes(generic)
    coefficients = _array(past, 'force_coefficients', (2, 3, 3))
    trace = _array(past, 'trace_coefficients', (2, 3))
    receiver_coefficients = _array(past, 'receiver_coefficients', (48, 2, 2, 3, 4))
    raw = generic - np.einsum('ic,cab->iab', np.einsum('cab,iab->ic', axes.conj(), generic).real, axes)
    gram = np.einsum('iab,jab->ij', raw.conj(), raw).real
    values = _array(past, 'complement_eigenvalues', (3,))
    vectors = _array(past, 'complement_eigenvectors', (3, 3))
    if values[0] <= 1e-12 or np.any(np.diff(values) < 0):
        raise ValueError('parameter response complement is unresolved or eigenvalues unordered')
    _close(vectors.T @ vectors, np.eye(3), 'complement eigenvector orthonormality', 1e-12)
    _close(gram @ vectors, vectors * values, 'complement eigenpairs', 1e-12)
    inverse = (vectors / np.sqrt(values)) @ vectors.T
    normalized = np.einsum('ij,jab->iab', inverse, raw)
    for name, expected in (('complement_raw', raw), ('complement_normalized', normalized),
                           ('complement_gram', gram), ('complement_inverse_sqrt', inverse)):
        _close(_array(past, name, expected.shape, expected.dtype.str), expected, name, 1e-12)
    _close(np.einsum('iab,jab->ij', normalized.conj(), normalized), np.eye(3), 'normalized complement', 1e-12)
    _close(np.einsum('iab,jab->ij', normalized.conj(), axes), np.zeros((3, 4)), 'complement chart exclusion', 1e-12)
    bases = {'FACTOR': axes[1:], 'COMPLEMENT': normalized, 'GENERIC': generic}
    forces = _array(past, 'forces', (4, 2, 3, 4, 4), '<c16')
    for index, action in enumerate(design.actions):
        expected = (trace[..., None, None] * axes[0] if action.role == 'TRACE'
                    else np.einsum('sjc,cab->sjab', coefficients, bases[action.role]))
        length = float(np.linalg.norm(expected))
        if length == 0 or not np.isfinite(length):
            raise ValueError('parameter response declared action has no physical direction')
        _close(forces[index], expected * float(action.force_norm) / length, action.role + ' force role', 1e-12)
    receivers = _array(past, 'receivers', (48, 2, 2, 3, 4, 4), '<c16')
    expected_receivers = np.einsum('rpsjc,cab->rpsjab', receiver_coefficients, axes)
    _close(receivers, expected_receivers, 'receiver chart duals', 1e-12)
    _close(np.einsum('rpsjab,tpsjab->rt', receivers.conj(), receivers), np.eye(48), 'receiver metric', 1e-12)
    _close(receivers[:24, 1], np.zeros_like(receivers[:24, 1]), 'position receiver phase', 1e-12)
    _close(receivers[24:, 0], np.zeros_like(receivers[24:, 0]), 'momentum receiver phase', 1e-12)
    return axes


def independent_hessian(position, design):
    """All96 columns from differences of independent trace-word gradients."""
    step = float(design.hessian_difference_step)
    if not np.isfinite(step) or step <= 0:
        raise ValueError('parameter Hessian requires its frozen positive difference step')
    alpha = np.asarray((float(design.alpha_x), float(design.alpha_y)))
    columns = []
    for direction in native_basis():
        image = (potential_gradient(position + step * direction, design.member, alpha)
                 - potential_gradient(position - step * direction, design.member, alpha)) / (2 * step)
        columns.append(_coordinates(image))
    result = np.asarray(columns).T
    return (result + result.T) / 2


def _linear_prediction(design, modes, hessian, force, receivers, action):
    """Literal zero-fit reduced unit-kinetic-mass BAOAB, with both kicks."""
    dt = float(design.view.timestep)
    decay = float(np.exp(-float(design.view.friction_gamma) * dt))
    reduced = modes.T @ hessian @ modes
    drive = modes.T @ _coordinates(force) * float(action.amplitude)
    x = np.zeros(modes.shape[1])
    p = np.zeros_like(x)
    output = []
    for tick in range(1, design.horizon_steps[-1] + 1):
        kick = dt / 2 * drive if tick <= action.pulse_steps else np.zeros_like(p)
        p = p + kick - dt / 2 * (reduced @ x)
        x = x + dt / 2 * p
        p = decay * p
        x = x + dt / 2 * p
        p = p - dt / 2 * (reduced @ x) + kick
        if tick in design.horizon_steps:
            native = np.stack((_lift(modes @ x), _lift(modes @ p)))
            output.append(np.einsum('rpsjab,psjab->r', receivers.conj(), native).real)
    return np.asarray(output, dtype='<f8')


def verify_forecast(origin, past, predicted, commitment):
    """Reprove every eigenpair, cutoff, mode and sealed prediction without eigh."""
    design = origin.design
    axes = verify_instruments(design, past)
    hessian = _array(predicted, 'origin_hessian', (96, 96))
    reference = independent_hessian(past['positions'][-1], design)
    error = float(np.linalg.norm(hessian - reference) / max(1., np.linalg.norm(reference)))
    if error > float(design.hessian_reference_tolerance):
        raise ValueError('parameter response full96 Hessian fails independent trace-gradient differences')
    _close(hessian, hessian.T, 'Hessian symmetry', 1e-12)
    values = _array(predicted, 'hessian_eigenvalues', (96,))
    vectors = _array(predicted, 'hessian_eigenvectors', (96, 96))
    order = _array(predicted, 'hessian_order', (96,), '<i8')
    if np.any(np.diff(values) < 0) or not np.array_equal(order, np.argsort(np.abs(values), kind='stable')):
        raise ValueError('parameter response changes complete Hessian order or slow-mode cutoff')
    _close(vectors.T @ vectors, np.eye(96), 'Hessian eigenvector basis')
    _close(hessian @ vectors, vectors * values, 'all96 Hessian eigenpairs')
    matrix_values = _array(predicted, 'matrix_eigenvalues', (6, 4))
    matrix_vectors = _array(predicted, 'matrix_eigenvectors', (6, 4, 4), '<c16')
    norms = _array(predicted, 'radial_norms', (6,))
    directions = _array(predicted, 'radial_directions', (6, 4, 4), '<c16')
    radial, spectra = [], []
    unavailable = {}
    for index, matrix in enumerate(past['positions'][-1].reshape(6, 4, 4)):
        traceless = matrix - np.trace(matrix) * np.eye(4) / 4
        length = float(np.linalg.norm(traceless))
        _close(norms[index], length, 'radial norm', 1e-12)
        expected = np.zeros((4, 4), dtype='<c16') if length <= 1e-12 else traceless / length
        _close(directions[index], expected, 'radial direction', 1e-12)
        if length <= 1e-12:
            unavailable['NORM_RADIUS'] = 'ORIGIN_RADIAL_DIRECTION_UNRESOLVED'
        radial.append(np.stack((np.eye(4) / 2, expected)))
        eigenvalues, eigenvectors = matrix_values[index], matrix_vectors[index]
        if np.any(np.diff(eigenvalues) < 0):
            raise ValueError('parameter response native matrix eigenvalues are unordered')
        _close(eigenvectors.conj().T @ eigenvectors, np.eye(4), 'native matrix eigenvector basis')
        _close(matrix @ eigenvectors, eigenvectors * eigenvalues, 'all native matrix eigenpairs')
        if np.min(np.diff(eigenvalues)) <= float(design.spectral_gap_minimum):
            unavailable['SPECTRA'] = 'ORIGIN_NATIVE_MATRIX_SPECTRUM_DEGENERATE'
        spectra.append(np.asarray([np.outer(v, v.conj()) for v in eigenvectors.T]))
    if abs(values[order[24]]) - abs(values[order[23]]) <= float(design.generic_gap_minimum):
        unavailable['GENERIC_SLOW'] = 'ORIGIN_NATIVE_SLOW_MODE_CUTOFF_DEGENERATE'
    expected_modes = {'FACTOR': _block_modes([axes] * 6), 'FULL_COUPLED': np.eye(96),
                      'NORM_RADIUS': _block_modes(radial), 'SPECTRA': _block_modes(spectra),
                      'GENERIC_SLOW': vectors[:, order[:24]]}
    expected_members = {'origin_hessian', 'hessian_eigenvalues', 'hessian_eigenvectors', 'hessian_order',
                        'matrix_eigenvalues', 'matrix_eigenvectors', 'radial_norms', 'radial_directions'}
    expected_members |= {n.lower() for n in PREDICTORS} | {'modes_' + n.lower() for n in PREDICTORS}
    if set(predicted) != expected_members or tuple(commitment.dispositions) != tuple(
            (name, 'UNRESOLVED', unavailable[name]) if name in unavailable else (name, 'AVAILABLE', None)
            for name in PREDICTORS):
        raise ValueError('parameter response drops full forecast witness or unavailable comparator reason')
    for name in PREDICTORS:
        expected = np.empty((96, 0)) if name in unavailable else expected_modes[name]
        modes = _array(predicted, 'modes_' + name.lower(), expected.shape)
        _close(modes, expected, name + ' complete mode roles')
        prediction = _array(predicted, name.lower(), (4, len(design.horizon_steps), 48), nonfinite=name in unavailable)
        if name in unavailable:
            if not np.isnan(prediction).all():
                raise ValueError('parameter unresolved comparator has a fabricated prediction')
        else:
            _close(modes.T @ modes, np.eye(modes.shape[1]), name + ' mode isometry')
            expected_prediction = np.asarray([
                _linear_prediction(design, modes, hessian, force, past['receivers'], action)
                for force, action in zip(past['forces'], design.actions, strict=True)])
            _close(prediction, expected_prediction, name + ' literal discrete BAOAB prediction',
                   float(design.forecast_reference_tolerance))
    return error


def reference_branch(design, past, force, amplitude, pulse_steps, noise):
    """Literal trace-gradient BAOAB over every retained clock, conditioned on noise."""
    x, p = past['positions'][-1].copy(), past['momenta'][-1].copy()
    positions, momenta = [x.copy()], [p.copy()]
    dt = float(design.view.timestep)
    decay = float(np.exp(-float(design.view.friction_gamma) * dt))
    scale = float(np.sqrt(float(design.view.bath_temperature) * (1 - decay**2)))
    alpha = np.asarray((float(design.alpha_x), float(design.alpha_y)))

    def hermitian(value):
        return (value + value.conj().swapaxes(-1, -2)) / 2

    for index, innovation in enumerate(noise):
        kick = dt / 2 * amplitude * force if index < pulse_steps else np.zeros_like(force)
        p = hermitian(p + kick)
        p = hermitian(p - dt / 2 * potential_gradient(x, design.member, alpha))
        x = hermitian(x + dt / 2 * p)
        p = hermitian(decay * p + scale * innovation)
        x = hermitian(x + dt / 2 * p)
        p = hermitian(p - dt / 2 * potential_gradient(x, design.member, alpha))
        p = hermitian(p + kick)
        positions.append(x.copy())
        momenta.append(p.copy())
    return {'positions': np.asarray(positions, dtype='<c16'), 'momenta': np.asarray(momenta, dtype='<c16')}


def noise_panel(stream, steps):
    """Optional independent selected-stream regeneration; excluded in cold mode."""
    rng = np.random.Generator(np.random.PCG64(stream.seed))
    values = np.zeros((steps, 2, 3, 4, 4), dtype='<c16')
    for tick in values:
        for sector in tick:
            for matrix in sector:
                matrix[np.diag_indices(4)] = rng.normal(size=4)
                real, imaginary = rng.normal(size=6), rng.normal(size=6)
                index = 0
                for row in range(4):
                    for column in range(row + 1, 4):
                        value = (real[index] + 1j * imaginary[index]) / np.sqrt(2)
                        matrix[row, column], matrix[column, row] = value, value.conjugate()
                        index += 1
    return values


def _validate_past(origin, past):
    design = origin.design
    expected = {'positions', 'momenta', 'alpha_tilde', 'ticks', 'frame', 'forces', 'receivers',
                'generic_basis', 'force_coefficients', 'trace_coefficients', 'receiver_coefficients',
                'complement_raw', 'complement_normalized', 'complement_gram', 'complement_inverse_sqrt',
                'complement_eigenvalues', 'complement_eigenvectors'}
    if set(past) != expected:
        raise ValueError('parameter independent reader loses full causal-only origin census')
    shape = (design.origin_tick + 1, 2, 3, 4, 4)
    for name in ('positions', 'momenta'):
        value = _array(past, name, shape, '<c16')
        _close(value, value.conj().swapaxes(-1, -2), 'full causal Hermitian ' + name, 1e-12)
    ticks = _array(past, 'ticks', (design.origin_tick + 1,), '<i8')
    alpha = _array(past, 'alpha_tilde', (design.origin_tick + 1, 2))
    expected_alpha = np.asarray([design.coordinate.couplings(t) for t in range(design.origin_tick + 1)])
    if (not np.array_equal(ticks, np.arange(design.origin_tick + 1))
            or not np.array_equal(alpha, expected_alpha)
            or tuple(float(x).hex() for x in alpha[-1]) != design.actual_alpha_hex
            or sha256(np.ascontiguousarray(past['frame'], dtype='<c16').tobytes()).hexdigest() != origin.frame_sha256):
        raise ValueError('parameter independent reader substitutes original clock, actual coupling or frame bytes')


def validate_original_origin(source, origin, past, parameter, supply, factor_source,
                             factor_product, factor_assessment, history_arrays, factor_arrays):
    """Prove original-prefix/frame supply from authenticated original operands.

    The caller must decode the two original raw publications against their
    original manifests, and authenticate the supplied ordinary/native receipts.
    No structural or history producer is rerun by this independent join.
    """
    source.validate_operands(parameter, supply, factor_source, factor_product, factor_assessment)
    _validate_past(origin, past)
    coordinate, design = source.design.coordinate, source.design
    expected = history_members(coordinate)
    if set(history_arrays) != set(expected):
        raise ValueError('parameter origin copy proof drops original full11 history members')
    for name, (dtype, shape) in expected.items():
        value = _array(history_arrays, name, shape, dtype)
        if dtype == '<c16':
            _close(value, value.conj().swapaxes(-1, -2), 'original Hermitian ' + name, 1e-12)
    initial_fp = sha256(np.ascontiguousarray(history_arrays['primary_positions'][0], dtype='<c16').tobytes()
                        + np.ascontiguousarray(history_arrays['primary_momenta'][0], dtype='<c16').tobytes()).hexdigest()
    if dict(source.allocation.initial_state_sha256s)[source.root.root_id] != initial_fp:
        raise ValueError('parameter matched group is not bound to the authenticated original initial state')
    for view, multiplier in (('primary', 1), ('fine', 2)):
        count = coordinate.total_ticks * multiplier + 1
        if (not np.array_equal(history_arrays[view + '_ticks'], np.arange(count))
                or not np.array_equal(history_arrays[view + '_alpha_tilde'], np.asarray(
                    [coordinate.couplings(t, refinement=multiplier) for t in range(count)]))):
            raise ValueError('parameter origin copy proof substitutes original complete clock or schedule')
    for name in ('positions', 'momenta', 'alpha_tilde', 'ticks'):
        if not np.array_equal(past[name], history_arrays['primary_' + name][:design.origin_tick + 1]):
            raise ValueError('parameter response origin is not the exact complete causal PRIMARY prefix')
    expected_factor = factor_members(design.rule)
    if set(factor_arrays) != set(expected_factor) or any(
            np.asarray(factor_arrays[name]).shape != shape or np.asarray(factor_arrays[name]).dtype.str != dtype
            for name, (dtype, shape) in expected_factor.items()):
        raise ValueError('parameter origin copy proof loses original full factor member denominator')
    expected_root = FactorRootRole(source.root.root_id, source.root.independent_group_id, coordinate.family_id,
        source.causal.history_source, supply.product.arrays.array_artifact, supply.product_artifact)
    if (tuple((t.view, t.sector) for t in factor_product.traces) !=
            tuple((v, s) for v in ('PRIMARY', 'FINE') for s in design.rule.sectors)
            or any(t.root != expected_root or t.rule != design.rule.identity
                   or t.diagnostics != factor_product.arrays.array_artifact
                   or t.diagnostic_members != factor_product.arrays.members for t in factor_product.traces)):
        raise ValueError('parameter origin copy proof substitutes original trace/root/source/member joins')
    for view in ('PRIMARY', 'FINE'):
        for sector in design.rule.sectors:
            if not np.array_equal(factor_arrays[prefix(view, sector) + 'ticks'], np.asarray(design.rule.lattice)):
                raise ValueError('parameter origin copy proof substitutes original factor clocks')
    trace = next(t for t in factor_product.traces if (t.view, t.sector) == ('PRIMARY', design.factor_sector))
    candidates = tuple(o.tick for o in trace.observations
        if o.tick >= design.rule.risk_start_tick and o.tick >= coordinate.ramp_ticks
        and (design.ramp_boundary != 'STRICTLY_AFTER_RAMP' or o.tick > coordinate.ramp_ticks)
        and o.status == 'AVAILABLE' and o.identifiable is True and o.raw_admitted is True
        and o.causal_admitted is True and not o.alignment_ambiguous)
    if not candidates or candidates[0] != design.origin_tick:
        raise ValueError('parameter origin is not first causal eligible selected PRIMARY constant-region cutoff')
    base, index = prefix('PRIMARY', design.factor_sector), design.rule.lattice.index(design.origin_tick)
    if (not factor_arrays[base + 'available'][index] or not factor_arrays[base + 'identifiable'][index]
            or not np.array_equal(past['frame'], factor_arrays[base + 'aligned_factor'][index])):
        raise ValueError('parameter response frame is not the exact independently assessed selected original row')
    constant = np.asarray((float(design.alpha_x), float(design.alpha_y)))
    for view, start in (('primary', design.origin_tick), ('fine', 2 * design.origin_tick)):
        suffix = history_arrays[view + '_alpha_tilde'][start:]
        if not np.array_equal(suffix, np.broadcast_to(constant, suffix.shape)):
            raise ValueError('parameter response original suffix does not supply its claimed constant realization')


def _validate_native_receipt(source, origin, commitment, event, stream, arrays):
    """Bind supplied innovations/states to the actual completed child publication.

    The caller's receipt store authenticates the receipt. This exact byte join
    does not itself make an arbitrary caller-constructed receipt genuine.
    """
    definition = event.definition
    expected_sources = {identity(source), identity(origin), identity(commitment)}
    key = sha256((definition.parent_contact.task_id + ':' + definition.subwork_id).encode()).hexdigest()
    task_id = 'native-subwork.' + key
    attempt_id = definition.parent_contact.run_id + '.' + task_id + '.attempt-001'
    if (not expected_sources <= set(definition.sources)
            or definition.code_sources_sha256 != source.provenance.code_sources_sha256
            or definition.dependency_lock_sha256 != source.provenance.dependency_lock_sha256
            or definition.streams != (source.root.stream_identity(stream),)
            or not set(definition.input_materialization_ids) <= set(event.receipt.input_materialization_ids)
            or event.receipt.run_id != definition.parent_contact.run_id or event.receipt.task_id != task_id
            or event.receipt.attempt_id != attempt_id or event.receipt.receipt_id != 'receipt.' + attempt_id
            or event.receipt.implementation_commit != definition.parent_contact.implementation_commit
            or len(event.receipt.output_logical_artifacts) != 2
            or len(event.receipt.output_materializations) != 2):
        raise ValueError('parameter native readback changes exact source/seal/code/lock/stream receipt joins')
    raw, _ = encode_matrix_arrays(arrays)
    digest = sha256(raw).hexdigest()
    logicals = {o.payload_schema: o for o in event.receipt.output_logical_artifacts}
    materials = {m.logical_artifact_id: m for m in event.receipt.output_materializations}
    if set(logicals) != {MATRIX_ARRAY_SCHEMA, event.completion.SCHEMA}:
        raise ValueError('parameter native receipt omits exact array/completion publication')
    logical = logicals[MATRIX_ARRAY_SCHEMA]
    material = materials[logical.logical_artifact_id]
    if (logical.content_sha256 != digest or material.physical_sha256 != digest
            or logical.logical_artifact_id != task_id + '.output.arrays'
            or material.size_bytes != len(raw) or material.compression != 'none'):
        raise ValueError('parameter native aggregate changes authenticated child state or panel innovations')
    completion = logicals[event.completion.SCHEMA]
    material = materials[completion.logical_artifact_id]
    raw = event.completion.canonical_bytes()
    if (completion.logical_artifact_id != task_id + '.completion'
            or completion.content_sha256 != sha256(raw).hexdigest()
            or material.physical_sha256 != sha256(raw).hexdigest()
            or material.size_bytes != len(raw) or material.compression != 'none'):
        raise ValueError('parameter native receipt changes exact retained completion bytes')


def assess(source, origin, commitment, native, past, predicted, actual, *, original_inputs, regenerate_noise=False):
    """Assess every retained branch and score; conditional noise is explicit."""
    if (type(source) is not MatrixParameterResponseSource or type(origin) is not MatrixParameterResponseOrigin
            or type(commitment) is not MatrixParameterResponseForecast or type(native) is not MatrixParameterNativeResponses
            or type(regenerate_noise) is not bool or origin.source != identity(source.causal)
            or origin.design != source.design or origin.root_id != source.root.root_id
            or origin.independent_group_id != source.root.independent_group_id
            or origin.clock_id != source.root.clock_id or commitment.origin != identity(origin)
            or commitment.model != source.design.model or commitment.cutoff != source.design.cutoff
            or native.source != identity(source) or native.origin != identity(origin)
            or native.forecast != identity(commitment)):
        raise ValueError('parameter response assessment substitutes typed source/origin/commitment/clock')
    expected_producers = ((identity(source.causal), identity(source.design)),
                          (identity(origin), commitment.model),
                          (identity(source), identity(origin), identity(commitment)))
    for record, producers in zip((origin, commitment, native), expected_producers, strict=True):
        if set(record.arrays.producers) != set(producers):
            raise ValueError('parameter response array custody changes exact scientific producers')
    if type(original_inputs) is not tuple or len(original_inputs) != 7:
        raise ValueError('parameter assessment requires authenticated original history/factor operands')
    validate_original_origin(source, origin, past, *original_inputs)
    hessian_error = verify_forecast(origin, past, predicted, commitment)
    design = source.design
    panels = source.root.streams
    expected_branches = tuple(sorted(f'{p.panel_id}.{a.action_id}.{sign.lower()}'
                                    for p in panels for a in design.actions for sign in SIGNS))
    members = ('positions', 'momenta', 'noise', 'alpha_tilde', 'ticks')
    if (native.branch_ids != expected_branches
            or set(actual) != {f'{b}.{name}' for b in expected_branches for name in members}):
        raise ValueError('parameter response independent reader loses full24 branch/member denominator')
    controls = [MatrixParameterResponseControl('control.origin-hessian', identity(source), None,
                _decimal(hessian_error), design.hessian_reference_tolerance,
                'FULL96_INDEPENDENT_TRACE_WORD_GRADIENT_DIFFERENCES', 'SATISFIED', 96, 96)]
    # Every literal forecast and action witness was rechecked above. Its value is
    # the measured max residual of that reproof, rather than a producer verdict.
    forecast_errors = []
    available_count = 0
    for name, state, _ in commitment.dispositions:
        if state == 'AVAILABLE':
            available_count += 1
            modes = predicted['modes_' + name.lower()]
            for index, action in enumerate(design.actions):
                rebuilt = _linear_prediction(design, modes, predicted['origin_hessian'],
                    past['forces'][index], past['receivers'], action)
                forecast_errors.append(float(np.max(np.abs(predicted[name.lower()][index] - rebuilt))))
    residual = max(forecast_errors, default=0.)
    controls.append(MatrixParameterResponseControl('control.forecast-reconstruction', identity(source), None,
        _decimal(residual), design.forecast_reference_tolerance, 'AVAILABLE_MODE_WITNESSED_DISCRETE_BAOAB_RETAINED_UNRESOLVED',
        'SATISFIED' if residual <= float(design.forecast_reference_tolerance) else 'VIOLATED',
        len(design.horizon_steps) * 4 * available_count, 48))
    axes = _axes(past['frame'])
    dispositions = {name: state for name, state, _ in commitment.dispositions}
    events = {event.branch_id: event for event in native.events}
    scores = []
    steps = design.horizon_steps[-1]
    constant = np.asarray((float(design.alpha_x), float(design.alpha_y)), dtype='<f8')
    for panel in panels:
        retained_noise = _array(actual, f'{panel.panel_id}.{design.actions[0].action_id}.hold.noise',
                                (steps, 2, 3, 4, 4), '<c16')
        _close(retained_noise, retained_noise.conj().swapaxes(-1, -2), 'Hermitian supplied innovations', 1e-12)
        if regenerate_noise and not np.array_equal(retained_noise, noise_panel(panel, steps)):
            raise ValueError('parameter response changes independently regenerated selected PCG64 panel')
        for index, action in enumerate(design.actions):
            states = {}
            for sign in SIGNS:
                branch = f'{panel.panel_id}.{action.action_id}.{sign.lower()}'
                values = {name: actual[f'{branch}.{name}'] for name in members}
                for name in ('positions', 'momenta'):
                    value = _array(values, name, (steps + 1, 2, 3, 4, 4), '<c16')
                    _close(value, value.conj().swapaxes(-1, -2), 'Hermitian full native ' + name, 1e-12)
                    if not np.array_equal(value[0], past[name][-1]):
                        raise ValueError('parameter native branch changes exact retained origin handoff')
                noise = _array(values, 'noise', (steps, 2, 3, 4, 4), '<c16')
                alpha = _array(values, 'alpha_tilde', (steps + 1, 2))
                ticks = _array(values, 'ticks', (steps + 1,), '<i8')
                if (not np.array_equal(noise, retained_noise)
                        or not np.array_equal(alpha, np.broadcast_to(constant, alpha.shape))
                        or not np.array_equal(ticks, np.arange(design.origin_tick, design.origin_tick + steps + 1))):
                    raise ValueError('parameter native branch changes common panel, frozen couplings or absolute clocks')
                _validate_native_receipt(source, origin, commitment, events[branch], panel, values)
                amplitude = float(action.amplitude) * {'PLUS': 1, 'MINUS': -1, 'HOLD': 0}[sign]
                reference = reference_branch(design, past, past['forces'][index], amplitude,
                                             action.pulse_steps, retained_noise)
                error = float(np.linalg.norm(np.stack(tuple(values[name] - reference[name]
                                                           for name in ('positions', 'momenta')))))
                controls.append(MatrixParameterResponseControl('control.' + branch, identity(source), branch,
                    _decimal(error), design.native_reference_tolerance,
                    'FULL192_INDEPENDENT_TRACE_WORD_BAOAB_BOTH_KICKS_ALL_CLOCKS',
                    'SATISFIED' if error <= float(design.native_reference_tolerance) else 'VIOLATED', steps, 192))
                states[sign] = values
            for hi, horizon in enumerate(design.horizon_steps):
                odd = np.stack(tuple((states['PLUS'][n][horizon] - states['MINUS'][n][horizon]) / 2
                                     for n in ('positions', 'momenta')))
                truth = np.einsum('rpsjab,psjab->r', past['receivers'].conj(), odd).real
                retained = np.einsum('psjc,cab->psjab', np.einsum('cab,psjab->psjc', axes.conj(), odd).real, axes)
                leakage = _decimal(np.linalg.norm(odd - retained))
                for ri, measured in enumerate(truth):
                    weak = bool(abs(measured) <= float(design.weak_response_minimum))
                    for name in PREDICTORS:
                        unresolved = dispositions[name] == 'UNRESOLVED'
                        prediction = None if unresolved else predicted[name.lower()][index, hi, ri]
                        error = None if unresolved else abs(prediction - measured)
                        scores.append(MatrixFactorResponseScore(panel.panel_id, panel.role, action.action_id,
                            horizon, ri, name, None if unresolved else _decimal(prediction), _decimal(measured),
                            None if unresolved else _decimal(error), None if unresolved else _decimal(prediction - measured),
                            None if unresolved or weak else _decimal(error / abs(measured)),
                            weak, leakage, dispositions[name]))
    return MatrixParameterResponseAssessment('assessment.' + source.source_id, identity(source), identity(origin),
        identity(commitment), identity(native), tuple(scores), tuple(controls),
        all(c.disposition == 'SATISFIED' for c in controls), noise_scope=(
            'REGENERATED_SELECTED_PCG64_STREAMS' if regenerate_noise else 'CONDITIONAL_AUTHENTICATED_PANEL_NOISE'))


def read_retained(source_raw, origin_raw, forecast_raw, native_raw, assessment_raw, fetch, *, original_records):
    """Authenticate complete retained arrays and reproduce conditional assessment."""
    types = (MatrixParameterResponseSource, MatrixParameterResponseOrigin, MatrixParameterResponseForecast,
             MatrixParameterNativeResponses, MatrixParameterResponseAssessment)
    records = tuple(decode_canonical_bytes(raw, kind, maximum_bytes=None)
                    for raw, kind in zip((source_raw, origin_raw, forecast_raw, native_raw, assessment_raw), types, strict=True))
    source, origin, commitment, native, retained = records
    if retained.noise_scope != 'CONDITIONAL_AUTHENTICATED_PANEL_NOISE':
        raise ValueError('cold RNG-blocked reader cannot reproduce a claimed regenerated-stream assessment')
    values = tuple(decode_matrix_arrays(fetch(r.arrays.array_artifact), r.arrays) for r in (origin, commitment, native))
    if type(original_records) is not tuple or len(original_records) != 5:
        raise ValueError('parameter cold reader requires authenticated original five typed supplier records')
    _, supply, _, factor_product, _ = original_records
    originals = (decode_matrix_arrays(fetch(source.history_arrays), supply.product.arrays),
                 decode_matrix_arrays(fetch(source.factor_arrays), factor_product.arrays))
    if assess(source, origin, commitment, native, *values, original_inputs=(*original_records, *originals)) != retained:
        raise ValueError('parameter cold readback changes independently assessed retained source/products')
    return retained
