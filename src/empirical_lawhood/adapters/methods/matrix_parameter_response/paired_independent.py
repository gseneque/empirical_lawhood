# SPDX-License-Identifier: MPL-2.0
"""Independent same-origin paired-future reproof without native producers.

Retained noise is authenticated and its weighted split is checked directly.
This cold route does not regenerate PCG64 or claim continuum enclosure.
"""

from decimal import Decimal
from hashlib import sha256

import numpy as np

from empirical_lawhood.adapters.methods.matrix_factor_response.independent_v2 import reference_branch_parameters
from empirical_lawhood.adapters.methods.matrix_factor_response.records import MatrixFactorResponseScore
from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays, encode_matrix_arrays
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA

from . import independent
from .paired_records import (
    DISPOSITION_WITHOUT_STANDARD, VIEWS, MatrixPairedControl, MatrixPairedFunctionalDiscrepancy,
    MatrixParameterPairedAssessment, MatrixParameterPairedDesign, MatrixParameterPairedForecast,
    MatrixParameterPairedNative, MatrixParameterPairedSource, identity,
)
from .records import PREDICTORS, SIGNS

MEMBERS = ('positions', 'momenta', 'noise', 'alpha_tilde', 'ticks')
WITNESSES = frozenset(('origin_hessian', 'hessian_eigenvalues', 'hessian_eigenvectors', 'hessian_order',
    'matrix_eigenvalues', 'matrix_eigenvectors', 'radial_directions', 'radial_norms',
    *('modes_' + name.lower() for name in PREDICTORS)))


def _decimal(value):
    value = float(value)
    if not np.isfinite(value):
        raise ValueError('paired scientific residual is nonfinite')
    return Decimal(str(value))


def _linear_prediction(design, view, modes, hessian, force, receivers, action):
    """Separate literal reduced BAOAB with both physical force kicks."""
    numerical = design.view(view)
    dt = float(numerical.timestep)
    damping = float(np.exp(-float(numerical.friction_gamma) * dt))
    stiffness = modes.T @ hessian @ modes
    drive = modes.T @ independent._coordinates(force) * float(action.amplitude)
    q, p = np.zeros(modes.shape[1]), np.zeros(modes.shape[1])
    horizons = design.horizon_steps(view)
    output = []
    for step in range(1, horizons[-1] + 1):
        applied = drive if step <= action.pulse_steps * design.multiplier(view) else np.zeros_like(drive)
        p = p + dt / 2 * applied - dt / 2 * (stiffness @ q)
        q = q + dt / 2 * p
        p = damping * p
        q = q + dt / 2 * p
        p = p - dt / 2 * (stiffness @ q) + dt / 2 * applied
        if step in horizons:
            response = np.stack((independent._lift(modes @ q), independent._lift(modes @ p)))
            output.append(np.einsum('rpsjab,psjab->r', receivers.conj(), response).real)
    return np.asarray(output, dtype='<f8')


def verify_forecast(design, past, predicted, commitment):
    """Reprove shared witnesses and each view's complete forecast without eigh."""
    if (type(design) is not MatrixParameterPairedDesign or type(commitment) is not MatrixParameterPairedForecast
            or commitment.design != identity(design) or commitment.origin != identity(design.common_origin)
            or commitment.model != design.primary.model
            or set(commitment.arrays.producers) != {identity(design), identity(design.common_origin), commitment.model}):
        raise ValueError('paired forecast changes its actual public design/origin/model producers')
    independent._validate_past(design.common_origin, past)
    expected = WITNESSES | {view.lower() + '_' + name.lower() for view in VIEWS for name in PREDICTORS}
    if set(predicted) != expected:
        raise ValueError('paired forecast drops shared witnesses or a complete numerical-view prediction')
    primary = {name: predicted[name] for name in WITNESSES}
    primary.update({name.lower(): predicted['primary_' + name.lower()] for name in PREDICTORS})
    error = independent.verify_forecast(design.common_origin, past, primary, commitment)
    for name, disposition, _ in commitment.dispositions:
        value = independent._array(predicted, 'fine_' + name.lower(),
            (4, len(design.primary.horizon_steps), 48), nonfinite=disposition == 'UNRESOLVED')
        if disposition == 'UNRESOLVED':
            if not np.isnan(value).all():
                raise ValueError('paired FINE unresolved description invents a finite prediction')
        else:
            rebuilt = np.asarray([_linear_prediction(design, 'FINE', predicted['modes_' + name.lower()],
                predicted['origin_hessian'], force, past['receivers'], action) for force, action in
                zip(past['forces'], design.primary.actions, strict=True)])
            independent._close(value, rebuilt, 'complete FINE discrete linear prediction',
                float(design.primary.forecast_reference_tolerance))
    return error


def _branches(source):
    return tuple(sorted((view, f'{view.lower()}.{stream.panel_id}.{action.action_id}.{sign.lower()}',
        stream, action, sign) for view in VIEWS for stream in source.root.streams
        for action in source.design.primary.actions for sign in SIGNS))


def verify_noise_pair(design, coarse, fine, bridge):
    """Independently prove the conditioned OU split at all native matrices."""
    steps = design.primary.horizon_steps[-1]
    for name, value, count in (('coarse', coarse, steps), ('fine', fine, 2 * steps), ('bridge', bridge, steps)):
        value = np.asarray(value)
        if (value.shape != (count, 2, 3, 4, 4) or value.dtype.str != '<c16' or not np.isfinite(value).all()
                or np.linalg.norm(value - value.conj().swapaxes(-1, -2)) > 1e-12):
            raise ValueError('paired noise changes complete finite Hermitian ' + name + ' innovations')
    primary, fine_view = design.primary.view, design.fine_view
    coarse_dt, fine_dt = float(primary.timestep), float(fine_view.timestep)
    gamma, bath = float(primary.friction_gamma), float(primary.bath_temperature)
    half = float(np.exp(-gamma * fine_dt))
    decay = float(np.exp(-gamma * coarse_dt))
    if (fine_dt * 2 != coarse_dt or not 0 < half < 1 or not 0 <= decay < 1
            or half != float(np.exp(-gamma * coarse_dt / 2))):
        raise ValueError('paired OU coupling has unsupported physical numerical clocks')
    denominator = np.sqrt(1 + half * half)
    first = (half * coarse + bridge) / denominator
    second = (coarse - half * bridge) / denominator
    if not np.array_equal(fine[::2], first) or not np.array_equal(fine[1::2], second):
        raise ValueError('paired innovations change the exact retained weighted OU bridge')
    # This proves the recombined OU innovation with its actual bath scales;
    # the tiny allowance concerns binary64 multiplication, not dt adequacy.
    fine_scale = np.sqrt(bath * (1 - half * half))
    primary_scale = np.sqrt(bath * (1 - decay * decay))
    rebuilt = fine_scale * (half * fine[::2] + fine[1::2])
    expected = primary_scale * coarse
    error = float(np.max(np.abs(rebuilt - expected)))
    # Independent native OU coefficients each round their variance. Retain
    # their measured mismatch instead of pretending the binary64 scales obey
    # the real-number identity exactly, especially at very small friction.
    coefficient_rounding = abs(fine_scale * denominator - primary_scale) * float(np.max(np.abs(coarse)))
    arithmetic_tolerance = coefficient_rounding + 64 * np.finfo(float).eps * max(1., float(np.max(np.abs(expected))))
    if error > arithmetic_tolerance:
        raise ValueError('paired fine OU recombination changes actual coarse bath contribution')
    return error


def _validate_receipt(source, commitment, event, stream, arrays):
    definition = event.definition
    expected_sources = {identity(source), identity(source.design), identity(source.design.common_origin), identity(commitment)}
    key = sha256((definition.parent_contact.task_id + ':' + definition.subwork_id).encode()).hexdigest()
    task_id = 'native-subwork.' + key
    attempt_id = definition.parent_contact.run_id + '.' + task_id + '.attempt-001'
    if (definition.subwork_id != event.branch_id or not expected_sources <= set(definition.sources)
            or definition.code_sources_sha256 != source.provenance.code_sources_sha256
            or definition.dependency_lock_sha256 != source.provenance.dependency_lock_sha256
            or definition.streams != (source.root.stream_identity(stream),)
            or not set(definition.input_materialization_ids) <= set(event.receipt.input_materialization_ids)
            or event.receipt.run_id != definition.parent_contact.run_id or event.receipt.task_id != task_id
            or event.receipt.attempt_id != attempt_id or event.receipt.receipt_id != 'receipt.' + attempt_id
            or event.receipt.implementation_commit != definition.parent_contact.implementation_commit
            or len(event.receipt.output_logical_artifacts) != 2 or len(event.receipt.output_materializations) != 2):
        raise ValueError('paired Native changes actual source/design/commitment/code/stream/parent receipt joins')
    raw, _ = encode_matrix_arrays(arrays)
    logicals = {o.payload_schema: o for o in event.receipt.output_logical_artifacts}
    materials = {m.logical_artifact_id: m for m in event.receipt.output_materializations}
    if set(logicals) != {MATRIX_ARRAY_SCHEMA, event.completion.SCHEMA}:
        raise ValueError('paired child loses actual arrays/completion publications')
    logical = logicals[MATRIX_ARRAY_SCHEMA]
    material = materials[logical.logical_artifact_id]
    if (logical.logical_artifact_id != task_id + '.output.arrays' or logical.content_sha256 != sha256(raw).hexdigest()
            or material.physical_sha256 != sha256(raw).hexdigest() or material.size_bytes != len(raw)
            or material.compression != 'none'):
        raise ValueError('paired aggregate substitutes receipt-bound full child state or innovations')
    logical = logicals[event.completion.SCHEMA]
    material = materials[logical.logical_artifact_id]
    raw = event.completion.canonical_bytes()
    if (logical.logical_artifact_id != task_id + '.completion' or logical.content_sha256 != sha256(raw).hexdigest()
            or material.physical_sha256 != sha256(raw).hexdigest() or material.size_bytes != len(raw)
            or material.compression != 'none'):
        raise ValueError('paired child changes actual completion publication bytes')


def _numerical_disposition(design, discrepancies, native_pass):
    standard = design.numerical_standard
    if standard is None:
        return None, DISPOSITION_WITHOUT_STANDARD
    if standard.consumer != design.primary.receiver:
        raise ValueError('paired numerical standard substitutes the frozen functional endpoint consumer')
    if not native_pass:
        return identity(standard), 'UNASSESSED_FAILED_NATIVE_REFERENCE'
    if (any(max(row.receiver_absolute_errors) > standard.receiver_absolute_tolerance
            or row.relative_curve_error is not None and row.relative_curve_error > standard.relative_curve_tolerance
            for row in discrepancies)):
        return identity(standard), 'VIOLATED_FROZEN_EMPIRICAL_STANDARD'
    if any(row.weak_response for row in discrepancies):
        return identity(standard), 'UNRESOLVED_WEAK_FUNCTIONAL_DENOMINATOR'
    return identity(standard), 'COMPATIBLE_WITH_FROZEN_EMPIRICAL_STANDARD'


def assess(source, commitment, native, past, predicted, actual, *, original_inputs):
    """All 48 full-state controls and all paired functional/forecast outcomes."""
    if (type(source) is not MatrixParameterPairedSource or type(native) is not MatrixParameterPairedNative
            or native.source != identity(source) or native.design != identity(source.design)
            or native.origin != identity(source.design.common_origin) or native.forecast != identity(commitment)
            or source.root.root_id != source.design.common_origin.root_id
            or source.root.independent_group_id != source.design.common_origin.independent_group_id
            or source.root.clock_id != source.design.common_origin.clock_id
            or set(native.arrays.producers) != {identity(source), identity(source.design),
                identity(source.design.common_origin), identity(commitment)}):
        raise ValueError('paired assessment changes actual typed source/origin/group/clock/native producers')
    if type(original_inputs) is not tuple or len(original_inputs) != 8:
        raise ValueError('paired original reproof requires authentic original source and seven upstream operands')
    original, *operands = original_inputs
    source.validate_original(original, source.design.common_origin)
    independent.validate_original_origin(original, source.design.common_origin, past, *operands)
    verify_forecast(source.design, past, predicted, commitment)
    design, primary = source.design, source.design.primary
    census = _branches(source)
    expected = tuple(sorted(b[1] for b in census))
    expected_members = {f'{branch}.{name}' for branch in expected for name in MEMBERS}
    expected_members |= {stream.panel_id + '.bridge' for stream in source.root.streams}
    if native.branch_ids != expected or set(actual) != expected_members:
        raise ValueError('paired assessment drops a view/branch/full-state member or retained bridge')
    events = {event.branch_id: event for event in native.events}
    if len({event.definition.parent_contact for event in native.events}) != 1:
        raise ValueError('paired native branches change their common parent contact')
    controls, states = [], {}
    constant = np.asarray((float(primary.alpha_x), float(primary.alpha_y)), dtype='<f8')
    references = {}
    for view, branch, panel, action, sign in census:
        count = design.horizon_steps(view)[-1]
        values = {name: actual[f'{branch}.{name}'] for name in MEMBERS}
        # Bridge is a sixth physical child member. Its exact byte join proves
        # that the aggregate bridge came from every actual native contact.
        values['bridge'] = actual[panel.panel_id + '.bridge']
        for name in ('positions', 'momenta'):
            value = independent._array(values, name, (count + 1, 2, 3, 4, 4), '<c16')
            independent._close(value, value.conj().swapaxes(-1, -2), 'paired Hermitian full-state ' + name, 1e-12)
            if not np.array_equal(value[0], past[name][-1]):
                raise ValueError('paired native changes exact shared PRIMARY origin state')
        noise = independent._array(values, 'noise', (count, 2, 3, 4, 4), '<c16')
        alpha = independent._array(values, 'alpha_tilde', (count + 1, 2))
        ticks = independent._array(values, 'ticks', (count + 1,), '<i8')
        start = design.native_origin_tick(view)
        if (not np.array_equal(alpha, np.broadcast_to(constant, alpha.shape))
                or not np.array_equal(ticks, np.arange(start, start + count + 1))):
            raise ValueError('paired native changes exact coupling or absolute numerical-view scalar clock')
        hold_key = f'{view.lower()}.{panel.panel_id}.{primary.actions[0].action_id}.hold.noise'
        if not np.array_equal(noise, actual[hold_key]):
            raise ValueError('paired action/sign branches change their shared panel innovations')
        _validate_receipt(source, commitment, events[branch], panel, values)
        amplitude = float(action.amplitude) * {'PLUS': 1, 'MINUS': -1, 'HOLD': 0}[sign]
        cache_key = (view, panel.panel_id) if sign == 'HOLD' else (view, branch)
        if cache_key not in references:
            references[cache_key] = reference_branch_parameters(member=primary.member,
                alpha_tilde=(primary.alpha_x, primary.alpha_y), view=design.view(view),
                positions=past['positions'][-1], momenta=past['momenta'][-1],
                force=past['forces'][primary.actions.index(action)], amplitude=amplitude,
                pulse_steps=action.pulse_steps * design.multiplier(view), noise=noise)
        reference = references[cache_key]
        error = float(np.linalg.norm(np.stack(tuple(values[name] - reference[name] for name in ('positions', 'momenta')))))
        decimal_error = _decimal(error)
        controls.append(MatrixPairedControl('control.' + branch, branch, view, decimal_error,
            primary.native_reference_tolerance, 'SATISFIED' if decimal_error <= primary.native_reference_tolerance else 'VIOLATED', count))
        states[view, panel.panel_id, action.action_id, sign] = values
    for panel in source.root.streams:
        hold = primary.actions[0].action_id
        verify_noise_pair(design, states['PRIMARY', panel.panel_id, hold, 'HOLD']['noise'],
            states['FINE', panel.panel_id, hold, 'HOLD']['noise'], actual[panel.panel_id + '.bridge'])
    scores, discrepancies = [], []
    axes = independent._axes(past['frame'])
    dispositions = {name: state for name, state, _ in commitment.dispositions}
    for panel in source.root.streams:
        for ai, action in enumerate(primary.actions):
            for hi, horizon in enumerate(primary.horizon_steps):
                curves = {}
                for view in VIEWS:
                    index = design.multiplier(view) * horizon
                    plus, minus = (states[view, panel.panel_id, action.action_id, sign] for sign in ('PLUS', 'MINUS'))
                    odd = np.stack(tuple((plus[name][index] - minus[name][index]) / 2 for name in ('positions', 'momenta')))
                    truth = np.einsum('rpsjab,psjab->r', past['receivers'].conj(), odd).real
                    curves[view] = truth
                    retained = np.einsum('psjc,cab->psjab', np.einsum('cab,psjab->psjc', axes.conj(), odd).real, axes)
                    leakage = _decimal(np.linalg.norm(odd - retained))
                    for ri, measured in enumerate(truth):
                        weak = bool(abs(measured) <= float(primary.weak_response_minimum))
                        for name in PREDICTORS:
                            unresolved = dispositions[name] == 'UNRESOLVED'
                            prediction = None if unresolved else predicted[view.lower() + '_' + name.lower()][ai, hi, ri]
                            error = None if unresolved else abs(prediction - measured)
                            score = MatrixFactorResponseScore(panel.panel_id, panel.role, action.action_id,
                                horizon, ri, name, None if unresolved else _decimal(prediction), _decimal(measured),
                                None if unresolved else _decimal(error), None if unresolved else _decimal(prediction - measured),
                                None if unresolved or weak else _decimal(error / abs(measured)), weak, leakage, dispositions[name])
                            scores.append((view, score))
                difference = curves['PRIMARY'] - curves['FINE']
                denominator = float(np.linalg.norm(curves['FINE']))
                weak = bool(denominator <= float(primary.weak_response_minimum))
                discrepancies.append(MatrixPairedFunctionalDiscrepancy(panel.panel_id, action.action_id,
                    primary.view.timestep * horizon, tuple(_decimal(abs(value)) for value in difference),
                    None if weak else _decimal(np.linalg.norm(difference) / denominator), weak))
    native_pass = all(control.disposition == 'SATISFIED' for control in controls)
    standard, disposition = _numerical_disposition(design, discrepancies, native_pass)
    return MatrixParameterPairedAssessment(assessment_id='assessment.' + source.source_id,
        source=identity(source), native=identity(native), forecast=identity(commitment),
        controls=tuple(controls), functional_discrepancies=tuple(discrepancies), scores=tuple(scores),
        native_reference_pass=native_pass, numerical_standard=standard, numerical_disposition=disposition,
        requested_horizons=len(primary.horizon_steps))


def read_retained(source_raw, forecast_raw, native_raw, assessment_raw, fetch, *, original_inputs):
    """Receipt callers authenticate records; this reader rechecks all arrays."""
    source, commitment, native, retained = tuple(decode_canonical_bytes(raw, kind, maximum_bytes=None)
        for raw, kind in zip((source_raw, forecast_raw, native_raw, assessment_raw),
            (MatrixParameterPairedSource, MatrixParameterPairedForecast, MatrixParameterPairedNative,
             MatrixParameterPairedAssessment), strict=True))
    origin = source.design.common_origin
    past, predicted, actual = tuple(decode_matrix_arrays(fetch(record.arrays.array_artifact), record.arrays)
        for record in (origin, commitment, native))
    rebuilt = assess(source, commitment, native, past, predicted, actual, original_inputs=original_inputs)
    if rebuilt != retained:
        raise ValueError('paired retained assessment differs from independent cold reproof')
    return rebuilt
