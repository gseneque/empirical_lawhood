# SPDX-License-Identifier: MPL-2.0
"""Selected origin-mechanical responses, frozen before scheduled pulse futures.

Only causal state and public physical/instrument operands enter. Production
retains all spectrum/eigenvector witnesses; cold reading uses those exact arrays
and independent derivatives, never a producer, RNG or eigensolve.
"""

from decimal import Decimal
from hashlib import sha256
from types import SimpleNamespace

import numpy as np

from empirical_lawhood.adapters.methods.matrix_factor_response.configured_secondary_readout import (
    E4_OBSERVATION_HORIZONS, E4_PRIMARY_TIMESTEP,
)
from empirical_lawhood.adapters.methods.matrix_factor_response.origin_mechanics import (
    IO48_FAILURES, IO48Unresolved, MatrixOriginResponseModel, balance_io48,
    factor_feedback_norms, model_predictors, pulse_responses,
)
from empirical_lawhood.adapters.methods.matrix_factor_response.science import _block_modes, _linear_responses, frame_axes, native_position_coordinates, native_position_lift, origin_io_system
from empirical_lawhood.adapters.methods.matrix_parameter_history.independent import potential_gradient
from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays, encode_matrix_arrays
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity

from .records import identity
from .response_records import ScheduledResponseArrays, ScheduledResponseForecast


def frozen_member_layout(protocol, disposition, *, members=None):
    """Bounded descriptor census; actual IO48 stages are re-proved from bytes.

    Adaptive balanced ranks are visible in retained shapes. This metadata check
    neither retries a failed solver nor claims that a shaped witness is valid.
    """
    result = {view + '_' + predictor.lower(): ('<f8', (4, len(protocol.horizon_steps), protocol.receiver_count))
        for view in ('primary', 'fine') for predictor in model_predictors(protocol.mechanical_model)}
    amended = type(protocol.mechanical_model) is MatrixOriginResponseModel
    if amended:
        result.update({view + '_full_grid_' + predictor.lower(): ('<f8', (4, 128, 48))
            for view in ('primary', 'fine') for predictor in model_predictors(protocol.mechanical_model)})
    if disposition in ('AVAILABLE', 'INSTRUMENT_UNRESOLVED'):
        result.update(complement_spectrum=('<f8', (3,)), complement_eigenvectors=('<f8', (3, 3)))
    if disposition == 'AVAILABLE':
        result.update(forces=('<c16', (4, 2, 3, 4, 4)), receivers=('<c16', (48, 2, 2, 3, 4, 4)))
        for view in ('primary', 'fine'):
            result.update({view + '_' + name: value for name, value in {
                'hessian': ('<f8', (96, 96)), 'hessian_spectrum': ('<f8', (96,)),
                'hessian_eigenvectors': ('<f8', (96, 96)), 'position_spectrum': ('<f8', (6, 4)),
                'position_eigenvectors': ('<c16', (6, 4, 4))}.items()})
    if not amended or disposition != 'AVAILABLE':
        return result
    if members is None:
        raise ValueError('amended forecast metadata requires its actual adaptive-rank descriptors')
    actual = {member.name: (member.dtype, member.shape) for member in members}
    if any(actual.get(name) != shape for name, shape in result.items()):
        raise ValueError('amended forecast metadata loses its complete predictions or origin instrument')
    gramian = {'gramian_c', 'gramian_o'}
    first_eigen = {'controllability_values', 'controllability_vectors'}
    eigen = first_eigen | {'observability_values', 'observability_vectors'}
    singular = {'hankel_values', 'hankel_left', 'hankel_right_t'}
    maps = {'lift', 'restrict', 'reduced_transition', 'reduced_inputs', 'reduced_outputs'}
    stages = (set(), gramian, gramian | first_eigen, gramian | eigen,
        gramian | eigen | singular, gramian | eigen | singular | maps)
    for view, multiplier in (('primary', 1), ('fine', 2)):
        fixed = {'io48_state_units': ('<f8', (192,)), 'io48_output_units': ('<f8', (48,)),
            'origin_cross_sector_norms': ('<f8', (2,)), 'io48_status': ('<i8', (1,)),
            'factor_escape_return': ('<f8', (2,)), 'factor_memory_curve': ('<f8', (128 * multiplier,))}
        for name, shape in fixed.items():
            if actual.get(view + '_' + name) != shape:
                raise ValueError('amended forecast metadata changes bounded IO48 diagnostics')
            result[view + '_' + name] = shape
        prefix = view + '_io48_witness_'
        witnesses = {name.removeprefix(prefix): value for name, value in actual.items() if name.startswith(prefix)}
        if set(witnesses) not in stages:
            raise ValueError('amended forecast metadata drops a complete IO48 solver stage')
        for name, (dtype, shape) in witnesses.items():
            if dtype != '<f8' or any(type(n) is not int or not 0 <= n <= 192 for n in shape):
                raise ValueError('amended forecast metadata expands the IO48 witness dimensions')
            expected = ((192, 192) if name in gramian or name.endswith('_vectors') else
                (192,) if name.endswith('_values') and not name.startswith('hankel') else None)
            if expected is not None and shape != expected:
                raise ValueError('amended forecast metadata changes a full Gramian or eigensystem')
        if singular <= set(witnesses):
            s = witnesses['hankel_values'][1]
            left, right = witnesses['hankel_left'][1], witnesses['hankel_right_t'][1]
            if len(s) != 1 or len(left) != 2 or len(right) != 2 or left[1] != s[0] or right[0] != s[0] or s[0] != min(left[0], right[1]):
                raise ValueError('amended forecast metadata changes its complete thin Hankel SVD')
        if maps <= set(witnesses):
            lift = witnesses['lift'][1]
            if len(lift) != 2 or lift[0] != 192 or lift[1] > 48:
                raise ValueError('amended forecast metadata exceeds the IO48 retained dimension cap')
            rank = lift[1]
            if any(witnesses[name][1] != shape for name, shape in {
                    'restrict': (rank, 192), 'reduced_transition': (rank, rank),
                    'reduced_inputs': (rank, 4), 'reduced_outputs': (48, rank)}.items()):
                raise ValueError('amended forecast metadata substitutes inconsistent reduced maps')
        result.update({prefix + name: value for name, value in witnesses.items()})
        optional = {view + '_io48_ranks': ('<i8', (4,)), view + '_io48_projection_condition_bound': ('<f8', (1,))}
        present = set(optional) & set(actual)
        if present and (present != set(optional) or not maps <= set(witnesses)
                or any(actual[name] != shape for name, shape in optional.items())):
            raise ValueError('amended forecast metadata invents incomplete successful rank diagnostics')
        if present:
            result.update(optional)
    if set(result) != set(actual):
        raise ValueError('amended forecast metadata adds unselected witness arrays')
    return result





def validate_e4_observation_horizons(protocol, horizons):
    """One physical grid for amended targets and the original dense readout."""
    coordinate = protocol.public_source.coordinate
    selected = E4_OBSERVATION_HORIZONS if type(protocol.mechanical_model) is MatrixOriginResponseModel else (16, 64, 128)
    if (type(horizons) is not tuple or horizons != E4_OBSERVATION_HORIZONS
            or protocol.horizon_steps != selected or protocol.receiver_count != 48
            or coordinate.primary_view.timestep != E4_PRIMARY_TIMESTEP
            or coordinate.fine_view.timestep != Decimal('0.0005')
            or protocol.public_source.policy.cutoff_tick + horizons[-1] > coordinate.total_ticks
            or any(action.pulse_steps != 16 for action in protocol.actions)):
        raise ValueError('E4 supplementary response changes its frozen grid, paired physical clock, pulse or follow-up')
    return horizons


class InstrumentUnresolved(ValueError):
    def __init__(self, reason, witnesses):
        super().__init__(reason)
        self.witnesses = witnesses


def array_product(protocol, arrays, *, role, artifact_id, producers, access, visibility, nonfinite=(), raw=None):
    encoded, members = encode_matrix_arrays(arrays, nonfinite_members=nonfinite)
    raw = encoded if raw is None else raw
    artifact = ArtifactIdentity(artifact_id, 'scheduled-response-'+role.lower(), MATRIX_ARRAY_SCHEMA,
        sha256(raw).hexdigest(), 'application/x-npz', len(raw))
    operand = ScheduledResponseArrays('arrays.'+artifact_id, role, protocol.public_source.source, artifact, members,
        tuple(sorted(producers, key=lambda o: o.object_id)), access, visibility)
    decode_matrix_arrays(raw, operand)
    return raw, operand


def instrument(protocol, frame, templates, *, witnesses=None):
    """Origin-fixed forces/receivers; all thresholds come from frozen protocol."""
    axes = frame_axes(frame)
    generic = templates['generic_basis']
    frame_axes(generic)
    complement = generic-np.einsum('ic,cab->iab', np.einsum('cab,iab->ic', axes.conj(), generic).real, axes)
    gram = np.einsum('iab,jab->ij', complement.conj(), complement).real
    if witnesses is None:
        values, vectors = np.linalg.eigh(gram)
    else:
        values, vectors = witnesses
        if (values.shape != (3,) or vectors.shape != (3, 3) or not np.isfinite(values).all() or not np.isfinite(vectors).all()
                or np.linalg.norm(gram@vectors-vectors*values[None]) > float(protocol.hessian_reference_tolerance)
                or np.linalg.norm(vectors.T@vectors-np.eye(3)) > float(protocol.hessian_reference_tolerance)
                or np.any(np.diff(values) < 0)):
            raise ValueError('scheduled fixed instrument changes retained complement eigenpair witnesses')
    if values[0] <= float(protocol.complement_gram_minimum):
        raise InstrumentUnresolved('scheduled declared complement instrument has unresolved span', (values, vectors))
    complement = np.einsum('ij,jab->iab', (vectors/np.sqrt(values))@vectors.T, complement)
    bases = {'FACTOR': frame, 'COMPLEMENT': complement, 'GENERIC': generic}
    forces = []
    for action in protocol.actions:
        force = templates['trace_coefficients'][..., None, None]*axes[0] if action.role == 'TRACE' else np.einsum('sjc,cab->sjab', templates['force_coefficients'], bases[action.role])
        length = np.linalg.norm(force)
        if not np.isfinite(length) or length == 0:
            raise InstrumentUnresolved('scheduled declared force has no resolved norm', (values, vectors))
        forces.append(force*float(action.force_norm)/length)
    receivers = np.einsum('rpsjc,cab->rpsjab', templates['receiver_coefficients'], axes)
    if not np.isfinite(receivers).all():
        raise ValueError('scheduled origin-fixed receiver is not finite')
    return np.asarray(forces, dtype='<c16'), np.asarray(receivers, dtype='<c16'), (values, vectors)


def _hessian(protocol, position, alpha):
    from empirical_lawhood.adapters.simulators.six_matrix_response.gradients import SixMatrixParameters
    from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_derivatives import hessian_image
    c = protocol.public_source.coordinate
    selected = SixMatrixParameters(2, float(c.member.mass_x), float(c.member.mass_y), float(c.member.cross_coupling_gamma),
        float(alpha[0]), float(alpha[1]))
    hessian = np.empty((96, 96), dtype='<f8')
    for j in range(96):
        hessian[:, j] = native_position_coordinates(hessian_image(position, native_position_lift(np.eye(96)[j]), selected))
    return (hessian+hessian.T)/2


def _modes(protocol, position, frame, hessian, *, retained=None):
    """Produce or reprove the same full96 reduction witnesses."""
    tol = float(protocol.hessian_reference_tolerance)
    arrays, unavailable = {}, {}
    spectra_modes, radius_modes = [], []
    for j, matrix in enumerate(position.reshape(6, 4, 4)):
        if retained is None:
            values, vectors = np.linalg.eigh(matrix)
        else:
            values, vectors = retained['position_spectrum'][j], retained['position_eigenvectors'][j]
            if (values.shape != (4,) or vectors.shape != (4, 4) or not np.isfinite(values).all() or not np.isfinite(vectors).all()
                    or np.linalg.norm(matrix@vectors-vectors*values[None]) > tol
                    or np.linalg.norm(vectors.conj().T@vectors-np.eye(4)) > tol or np.any(np.diff(values) < 0)):
                raise ValueError('scheduled predictor changes retained native-matrix eigenpairs')
        arrays.setdefault('position_spectrum', []).append(values)
        arrays.setdefault('position_eigenvectors', []).append(vectors)
        if np.min(np.diff(values)) <= float(protocol.spectral_gap_minimum):
            unavailable['SPECTRA'] = 'ORIGIN_NATIVE_MATRIX_SPECTRUM_DEGENERATE'
        spectra_modes.append(np.asarray([np.outer(v, v.conj()) for v in vectors.T]))
        traceless = matrix-np.trace(matrix)*np.eye(4)/4
        length = np.linalg.norm(traceless)
        if length <= float(protocol.radial_norm_minimum):
            unavailable['NORM_RADIUS'] = 'ORIGIN_RADIAL_DIRECTION_UNRESOLVED'
        else:
            radius_modes.append(np.stack((np.eye(4)/2, traceless/length)))
    if retained is None:
        values, vectors = np.linalg.eigh(hessian)
    else:
        values, vectors = retained['hessian_spectrum'], retained['hessian_eigenvectors']
        if (values.shape != (96,) or vectors.shape != (96, 96) or not np.isfinite(values).all() or not np.isfinite(vectors).all()
                or np.linalg.norm(hessian@vectors-vectors*values[None]) > tol
                or np.linalg.norm(vectors.T@vectors-np.eye(96)) > tol or np.any(np.diff(values) < 0)):
            raise ValueError('scheduled predictor changes complete retained Hessian eigenpairs')
    order = np.argsort(np.abs(values), kind='stable')
    modes = {'FACTOR': _block_modes([frame_axes(frame)]*6), 'FULL_COUPLED': np.eye(96, dtype='<f8')}
    if abs(values[order[24]])-abs(values[order[23]]) <= float(protocol.generic_gap_minimum):
        unavailable['GENERIC_SLOW'] = 'ORIGIN_NATIVE_SLOW_MODE_CUTOFF_DEGENERATE'
    else:
        modes['GENERIC_SLOW'] = vectors[:, order[:24]]
    if 'SPECTRA' not in unavailable:
        modes['SPECTRA'] = _block_modes(spectra_modes)
    if 'NORM_RADIUS' not in unavailable:
        modes['NORM_RADIUS'] = _block_modes(radius_modes)
    arrays = {n: np.asarray(a) for n, a in arrays.items()}
    arrays['hessian_spectrum'], arrays['hessian_eigenvectors'] = values, vectors
    return modes, unavailable, arrays


def forecast(protocol, causal, causal_arrays, templates, *, artifact_id, retained=None, raw=None):
    """Same fixed PRIMARY frame, distinct retained view states, fixed model menu."""
    public, c = protocol.public_source, protocol.public_source.coordinate
    if (causal.source != public.source or causal.root != public.root or causal.cutoff_tick != public.policy.cutoff_tick
            or causal.policy != identity(public.policy) or causal.frame_sha256 is not None
                and sha256(causal_arrays['frame'].tobytes()).hexdigest() != causal.frame_sha256):
        raise ValueError('scheduled physical forecast changes original public source/cutoff/frame')
    # The preceding projection already independently authenticated every prefix
    # state. This producer checks its exact terminal clocks and realized alphas.
    for view, mult in (('primary', 1), ('fine', 2)):
        if (causal_arrays[view+'_ticks'][-1] != mult*causal.cutoff_tick
                or not np.array_equal(causal_arrays[view+'_alpha_tilde'][-1], np.asarray(c.couplings(mult*causal.cutoff_tick, refinement=mult), dtype='<f8'))):
            raise ValueError('scheduled predictor substitutes actual cutoff schedule or paired clock')
    arrays, disposition, dispositions = forecast_response_arrays(protocol, causal_arrays, templates,
        disposition=causal.disposition, retained=retained)
    nonfinite = tuple(n for n, a in arrays.items() if not np.isfinite(a).all())
    raw, operand = array_product(protocol, arrays, role='FORECAST', artifact_id=artifact_id,
        producers=(public.source, identity(causal), ObjectIdentity.from_record(protocol.protocol_id, protocol)),
        access=OutcomeAccess.OUTCOME_BLIND, visibility=VisibilityCeiling.PROSPECTIVE, nonfinite=nonfinite, raw=raw)
    value = ScheduledResponseForecast('response-forecast.'+public.root.root_id, public.source, identity(causal),
        ObjectIdentity.from_record(protocol.protocol_id, protocol), ObjectIdentity.from_record(protocol.mechanical_model.model_id, protocol.mechanical_model),
        causal.frame_sha256, operand, disposition, tuple(dispositions))
    return raw, value


def _io48_forecast(model, numerical, hessian, forces, receivers, actions, factor_modes, retained):
    """Original reduced maps plus bounded projector feedback diagnostics."""
    transition, inputs, outputs, state_units, output_units = origin_io_system(
        numerical, hessian, forces, receivers, actions)
    arrays = {'io48_state_units': state_units, 'io48_output_units': output_units}
    sector_x = np.r_[0:48, 96:144]
    sector_y = np.r_[48:96, 144:192]
    arrays['origin_cross_sector_norms'] = np.asarray((np.linalg.norm(transition[np.ix_(sector_x, sector_y)]),
        np.linalg.norm(transition[np.ix_(sector_y, sector_x)])), dtype='<f8')
    declared_failure, witnesses = None, None
    if retained is not None:
        status = retained.get('io48_status')
        if (not isinstance(status, np.ndarray) or status.dtype.str != '<i8' or status.shape != (1,)
                or not 0 <= status[0] <= len(IO48_FAILURES)):
            raise ValueError('IO48 loses its original complete success/nonuse status')
        declared_failure = None if status[0] == 0 else IO48_FAILURES[int(status[0]) - 1]
        witnesses = {name.removeprefix('io48_witness_'): value for name, value in retained.items()
            if name.startswith('io48_witness_')}
    try:
        reduction = balance_io48(transition, inputs, outputs, numerical.horizon_steps[-1], model.io48,
            retained=witnesses, declared_failure=None if declared_failure == 'NONFINITE_ORIGIN_PULSE_RESPONSE' else declared_failure)
        arrays.update({'io48_witness_' + name: value for name, value in reduction.witnesses.items()})
        arrays['io48_ranks'] = np.asarray((reduction.reachable_rank, reduction.observable_rank,
            reduction.balanced_rank, reduction.effective_rank), dtype='<i8')
        arrays['io48_projection_condition_bound'] = np.asarray([reduction.projection_condition_bound], dtype='<f8')
        predicted = pulse_responses(reduction.transition, reduction.inputs, reduction.outputs,
            pulse_steps=tuple(action.pulse_steps for action in actions),
            horizons=numerical.horizon_steps, output_units=output_units)
        if declared_failure is not None:
            raise ValueError('IO48 original pulse nonuse is contradicted by retained reduced maps')
        reason = None
    except IO48Unresolved as error:
        if retained is not None and error.reason != declared_failure:
            raise ValueError('IO48 replay changes the original nonuse stage') from error
        arrays.update({'io48_witness_' + name: value for name, value in error.witnesses.items()})
        predicted = np.full((len(actions), len(numerical.horizon_steps), len(output_units)), np.nan, dtype='<f8')
        reason = error.reason
    arrays['io48_status'] = np.asarray([0 if reason is None else IO48_FAILURES.index(reason) + 1], dtype='<i8')
    zero = np.zeros_like(factor_modes)
    factor_phase = np.block([[factor_modes, zero], [zero, factor_modes]])
    try:
        escape, returning, memory = factor_feedback_norms(transition, factor_phase, numerical.horizon_steps[-1])
        arrays['factor_escape_return'] = np.asarray((escape, returning), dtype='<f8')
        arrays['factor_memory_curve'] = memory
    except IO48Unresolved:
        arrays['factor_escape_return'] = np.full(2, np.nan, dtype='<f8')
        arrays['factor_memory_curve'] = np.full(numerical.horizon_steps[-1], np.nan, dtype='<f8')
    return predicted, reason, arrays


def forecast_response_arrays(protocol, causal_arrays, templates, *, disposition, retained=None, observation_horizons=None,
        origin_witnesses=None, no_origin_reason='NO_ADMITTED_OR_RESOLVED_ORIGIN_FIXED_INSTRUMENT'):
    """Original two-view mechanical predictions and complete cold witnesses.

    The caller owns public source/frame/root/policy/cutoff and realized-clock
    authentication. This numerical entry creates no historical record or grant.
    """
    c = protocol.public_source.coordinate
    predictors = model_predictors(protocol.mechanical_model)
    amended = type(protocol.mechanical_model) is MatrixOriginResponseModel
    # Explicit supplementary calls require a distinct frozen E4 artifact/target
    # identity from their caller. Never publish these arrays as the E3 product.
    horizons = (protocol.horizon_steps if observation_horizons is None
        else validate_e4_observation_horizons(protocol, observation_horizons))
    if retained is not None and origin_witnesses is not None:
        raise ValueError('select full cold arrays or original origin witnesses, not both')
    witnesses = retained if retained is not None else origin_witnesses
    arrays, dispositions = {}, []
    if disposition == 'AVAILABLE':
        try:
            forces, receivers, comp = instrument(protocol, causal_arrays['frame'], templates,
                witnesses=None if witnesses is None else (witnesses['complement_spectrum'], witnesses['complement_eigenvectors']))
        except InstrumentUnresolved as error:
            arrays['complement_spectrum'], arrays['complement_eigenvectors'] = error.witnesses
            disposition = 'INSTRUMENT_UNRESOLVED'
    if disposition != 'AVAILABLE':
        for view in ('primary', 'fine'):
            for name in predictors:
                arrays[view+'_'+name.lower()] = np.full((4, len(horizons), protocol.receiver_count), np.nan, dtype='<f8')
                if amended:
                    arrays[view+'_full_grid_'+name.lower()] = np.full((4, 128, protocol.receiver_count), np.nan, dtype='<f8')
                dispositions.append((view.upper(), name, 'UNRESOLVED', no_origin_reason))
    else:
        arrays['forces'], arrays['receivers'] = forces, receivers
        arrays['complement_spectrum'], arrays['complement_eigenvectors'] = comp
        for view, multiplier in (('primary', 1), ('fine', 2)):
            position = causal_arrays[view+'_positions'][-1]
            alpha = causal_arrays[view+'_alpha_tilde'][-1]
            if witnesses is None:
                hessian = _hessian(protocol, position, alpha)
            else:
                hessian = witnesses[view+'_hessian']
                if hessian.dtype.str != '<f8' or hessian.shape != (96, 96) or not np.isfinite(hessian).all():
                    raise ValueError('scheduled forecast loses complete finite full96 origin Hessian')
                epsilon = float(protocol.hessian_difference_step)
                reference = np.empty((96, 96), dtype='<f8')
                for j in range(96):
                    direction = native_position_lift(np.eye(96)[j])
                    reference[:, j] = native_position_coordinates((potential_gradient(position+epsilon*direction, c.member, alpha)
                        -potential_gradient(position-epsilon*direction, c.member, alpha))/(2*epsilon))
                reference = (reference+reference.T)/2
                if np.linalg.norm(reference-hessian)/max(1., np.linalg.norm(reference)) > float(protocol.hessian_reference_tolerance):
                    raise ValueError('scheduled forecast Hessian fails independent literal potential derivative')
            modes, unavailable, diagnostic = _modes(protocol, position, causal_arrays['frame'], hessian,
                retained=None if witnesses is None else {n.removeprefix(view+'_'): a for n, a in witnesses.items() if n.startswith(view+'_')})
            arrays[view+'_hessian'] = hessian
            arrays.update({view+'_'+n: a for n, a in diagnostic.items()})
            calculation_horizons = tuple(range(1, 129)) if amended else horizons
            d = SimpleNamespace(view=c.primary_view if multiplier == 1 else c.fine_view,
                horizon_steps=tuple(multiplier*h for h in calculation_horizons))
            actions = tuple(SimpleNamespace(amplitude=a.amplitude, force_norm=a.force_norm,
                pulse_steps=multiplier*a.pulse_steps) for a in protocol.actions)
            if amended:
                io, reason, io_arrays = _io48_forecast(protocol.mechanical_model, d, hessian, forces,
                    receivers, actions, modes['FACTOR'], None if witnesses is None else {
                        n.removeprefix(view+'_'): a for n, a in witnesses.items() if n.startswith(view+'_')})
                arrays.update({view+'_'+n: a for n, a in io_arrays.items()})
                if reason is not None:
                    unavailable['IO48'] = reason
            for name in predictors:
                if name in unavailable:
                    value = np.full((4, len(calculation_horizons), protocol.receiver_count), np.nan, dtype='<f8')
                    dispositions.append((view.upper(), name, 'UNRESOLVED', unavailable[name]))
                else:
                    if name == 'IO48':
                        value = io
                    elif name == 'ZERO_RESPONSE':
                        value = np.zeros((4, len(calculation_horizons), protocol.receiver_count), dtype='<f8')
                    else:
                        value = np.asarray(_linear_responses(d, modes[name], hessian, forces, receivers, actions), dtype='<f8')
                    dispositions.append((view.upper(), name, 'AVAILABLE', None))
                if amended:
                    arrays[view+'_full_grid_'+name.lower()] = value
                    value = value[:, tuple(h - 1 for h in horizons), :].copy()
                arrays[view+'_'+name.lower()] = value
    if retained is not None:
        if set(arrays) != set(retained) or any(not np.array_equal(v, retained[n], equal_nan=True) for n, v in arrays.items()):
            raise ValueError('scheduled cold forecast substitutes actual frozen forces/receivers/predictions/witnesses')
    return arrays, disposition, tuple(dispositions)



def forecast_e4_dense(protocol, causal, causal_arrays, templates, *, target, secondary,
        original_physical, original_forecast_raw, artifact_id, forecast_id, retained=None, raw=None):
    """Seal prediction-only dense arrays in the existing mechanical task.

    The original archive owns all origin witnesses. Cold reading reuses those
    exact witnesses and replays only the deterministic mechanical arithmetic.
    """
    from .response_records import ScheduledE4DenseMechanicalForecast, _e4_original_forecast
    from .response_science import validate_frozen_response_arrays
    original_pin = _e4_original_forecast(original_physical)
    secondary.validate_target(target)
    target.validate_protocol(protocol)
    public, coordinate = protocol.public_source, protocol.public_source.coordinate
    if (original_physical.source != public.source or original_physical.causal_prefix != identity(causal)
            or original_physical.protocol != ObjectIdentity.from_record(protocol.protocol_id, protocol)
            or original_physical.mechanical_model != ObjectIdentity.from_record(protocol.mechanical_model.model_id, protocol.mechanical_model)
            or causal.source != public.source or causal.root != public.root
            or causal.policy != identity(public.policy) or causal.cutoff_tick != public.policy.cutoff_tick
            or causal.frame_sha256 != original_physical.frame_sha256
            or causal.frame_sha256 is not None and sha256(causal_arrays['frame'].tobytes()).hexdigest() != causal.frame_sha256):
        raise ValueError('dense E4 changes its actual original causal cutoff/frame/physical seal')
    for view, multiplier in (('primary', 1), ('fine', 2)):
        if (causal_arrays[view + '_ticks'][-1] != multiplier * causal.cutoff_tick
                or not np.array_equal(causal_arrays[view + '_alpha_tilde'][-1], np.asarray(
                    coordinate.couplings(multiplier * causal.cutoff_tick, refinement=multiplier), dtype='<f8'))):
            raise ValueError('dense E4 changes its actual PRIMARY/FINE cutoff clock or schedule')
    original = decode_matrix_arrays(original_forecast_raw, original_physical.arrays)
    validate_frozen_response_arrays(protocol, original, disposition=original_physical.disposition)
    names = {view + '_' + predictor.lower() for view in ('primary', 'fine') for predictor in model_predictors(protocol.mechanical_model)}
    if retained is not None and set(retained) != names:
        raise ValueError('dense E4 archive must contain the complete paired prediction array census')
    if protocol.horizon_steps == target.observation_horizons:
        # The amended original already seals every dense endpoint. This output
        # is an exact projection, with no second mechanical computation.
        arrays, disposition, dispositions = original, original_physical.disposition, original_physical.dispositions
        if retained is not None and any(retained[name].dtype != original[name].dtype
                or retained[name].shape != original[name].shape or retained[name].tobytes() != original[name].tobytes()
                for name in names):
            raise ValueError('matched E4 projection changes original sealed dense predictions')
    else:
        full_retained = None if retained is None else {**original, **retained}
        arrays, disposition, dispositions = forecast_response_arrays(protocol, causal_arrays, templates,
            disposition=causal.disposition, retained=full_retained,
            observation_horizons=target.observation_horizons,
            origin_witnesses=original if full_retained is None else None)
    indices = tuple(target.observation_horizons.index(horizon) for horizon in protocol.horizon_steps)
    if (disposition, dispositions) != (original_physical.disposition, original_physical.dispositions):
        raise ValueError('dense E4 changes original instrument availability')
    for name in original:
        selected = arrays[name][:, indices, :] if name in names else arrays[name]
        if selected.dtype != original[name].dtype or selected.shape != original[name].shape or selected.tobytes() != original[name].tobytes():
            raise ValueError('dense E4 changes original3sample values or original origin witnesses')
    predictions = {name: arrays[name] for name in sorted(names)}
    nonfinite = tuple(name for name, value in predictions.items() if not np.isfinite(value).all())
    encoded, operand = array_product(protocol, predictions, role='FORECAST', artifact_id=artifact_id,
        producers=(public.source, identity(causal), original_pin, target.identity, secondary.identity),
        access=original_physical.arrays.outcome_access, visibility=original_physical.arrays.visibility_ceiling,
        nonfinite=nonfinite, raw=raw)
    result = ScheduledE4DenseMechanicalForecast(forecast_id, public.source, identity(causal),
        ObjectIdentity.from_record(protocol.protocol_id, protocol), original_pin, target.identity, secondary.identity,
        public.policy.cutoff_tick, operand, disposition, dispositions)
    result.validate_original(protocol, target, secondary, original_physical)
    return encoded, result
