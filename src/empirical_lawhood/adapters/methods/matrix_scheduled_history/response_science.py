# SPDX-License-Identifier: MPL-2.0
"""Complete scheduled pulse arrays and independent finite-dt response scores.

The producer is called only after stock Native contact. The independent reader
uses the received full phase/noise arrays and literal derivatives; it never
draws noise, advances a producer, fits a predictor or computes a spectrum.
"""

from decimal import Decimal, localcontext
from types import SimpleNamespace

import numpy as np

from empirical_lawhood.adapters.methods.matrix_factor_response.records import PREDICTORS
from empirical_lawhood.adapters.methods.matrix_factor_response.origin_mechanics import MatrixOriginResponseModel, model_predictors
from empirical_lawhood.adapters.methods.matrix_factor_response.response_scoring import dense_response_measurements
from empirical_lawhood.adapters.methods.matrix_factor_response.response_scoring import response_error_norms
from empirical_lawhood.adapters.methods.matrix_parameter_response.paired_independent import verify_noise_pair
from empirical_lawhood.adapters.simulators.six_matrix_response.model import SixMatrixState
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history import split_parameter_innovations
from empirical_lawhood.adapters.simulators.six_matrix_response.simulation import hermitian_noise
from empirical_lawhood.kernel.provenance import ObjectIdentity

from .forecast import ScheduledForecastSeal
from .records import identity
from .response_native import assess_scheduled_branch, native_scheduled_branch
from .response_records import ScheduledE4DenseResponseCell, ScheduledE4DenseResponseScore, ScheduledResponseLossCell, ScheduledResponseScore, branch_census


def panel_innovations(source, history, panel, horizon):
    """Original checkpoint or explicit fresh future start, four exact purposes."""
    if (panel.independent_group_id != source.root.root.independent_group_id or horizon < 1
            or source.policy.cutoff_tick+horizon > source.coordinate.total_ticks
            or panel.role == 'COMMON_NOISE_PANEL' and panel.streams != source.root.streams):
        raise ValueError('scheduled future changes complete group/original common-stream scope')
    generators = {s.purpose: np.random.Generator(np.random.PCG64DXSM(s.effective_seed)) for s in panel.streams}
    if panel.role == 'COMMON_NOISE_PANEL':
        for saved in history.checkpoint.generators:
            generators[saved.purpose].bit_generator.state = saved.numpy_state()
    coarse, fine, bridge = [], [], []
    for tick in range(source.policy.cutoff_tick+1, source.policy.cutoff_tick+horizon+1):
        stage = 'preparation' if tick <= source.coordinate.ramp_ticks else 'autonomous'
        value = hermitian_noise(rng=generators[stage+'-coarse-driver'], q=2)
        pair = hermitian_noise(rng=generators[stage+'-fine-bridge'], q=2)
        coarse.append(value); bridge.append(pair)
        fine.extend(split_parameter_innovations(source.coordinate, value, pair))
    return {'primary': np.asarray(coarse, dtype='<c16'), 'fine': np.asarray(fine, dtype='<c16'),
        'bridge': np.asarray(bridge, dtype='<c16')}


def native_responses(source, history, prefix_arrays, protocol, panels, frozen_arrays, *, on_step=None):
    """All24 action/sign/panel branches at each of two nested numerical views."""
    protocol.public_source.validate_source(source)
    if frozen_arrays['forces'].shape != (4, 2, 3, 4, 4):
        raise ValueError('scheduled pulse source lacks the actual fixed frozen force census')
    horizon = protocol.horizon_steps[-1]
    noises = {p.panel_id: panel_innovations(source, history, p, horizon) for p in panels}
    arrays = {}
    completed_steps = 0

    def completed_branch_step(_branch_counter):
        nonlocal completed_steps
        completed_steps += 1
        on_step(completed_steps)

    for panel in panels:
        for name, values in noises[panel.panel_id].items():
            arrays['noise.'+panel.panel_id+'.'+name] = values
    for branch, view, panel, action, sign in branch_census(protocol, panels):
        label, mult = view.lower(), 1 if view == 'PRIMARY' else 2
        state = SixMatrixState(2, prefix_arrays[label+'_positions'][-1], prefix_arrays[label+'_momenta'][-1],
            mult*source.policy.cutoff_tick, *source.coordinate.couplings(mult*source.policy.cutoff_tick, refinement=mult))
        index = protocol.actions.index(action)
        result = native_scheduled_branch(state, coordinate=source.coordinate, refinement=mult,
            direction=frozen_arrays['forces'][index], amplitude=0 if sign == 'HOLD' else float(action.amplitude)*(1 if sign == 'PLUS' else -1),
            pulse_steps=mult*action.pulse_steps, innovations=noises[panel.panel_id][label],
            **({"on_step": completed_branch_step} if on_step is not None else {}))
        arrays.update({'branch.'+branch+'.'+name: values for name, values in result.items()})
    return dict(sorted(arrays.items()))


def validate_frozen_response_arrays(protocol, arrays, *, disposition, observation_horizons=None):
    """Check the selected frozen instrument before native entry, without effects."""
    from .response_records import ScheduledResponseProtocol
    if type(protocol) is not ScheduledResponseProtocol:
        raise TypeError('scheduled response preflight requires its exact selected protocol')
    protocol.__post_init__()
    if observation_horizons is None:
        horizons = protocol.horizon_steps
    else:
        from .response_forecast import validate_e4_observation_horizons
        horizons = validate_e4_observation_horizons(protocol, observation_horizons)
    if disposition not in ('AVAILABLE', 'NO_ORIGIN', 'UNEVALUABLE', 'INSTRUMENT_UNRESOLVED'):
        raise ValueError('scheduled response preflight changes actual instrument disposition')
    for view in ('primary', 'fine'):
        for predictor in model_predictors(protocol.mechanical_model):
            value = arrays.get(view+'_'+predictor.lower())
            if (not isinstance(value, np.ndarray) or value.dtype.str != '<f8'
                    or value.shape != (4, len(horizons), protocol.receiver_count)
                    or np.isinf(value).any()):
                raise ValueError('scheduled response preflight loses its complete frozen prediction geometry')
            if disposition != 'AVAILABLE' and not np.isnan(value).all():
                raise ValueError('scheduled response nonuse invents available frozen predictions')
            if type(protocol.mechanical_model) is MatrixOriginResponseModel:
                full = arrays.get(view+'_full_grid_'+predictor.lower())
                if (not isinstance(full, np.ndarray) or full.dtype.str != '<f8' or full.shape != (4, 128, 48)
                        or np.isinf(full).any()
                        or not np.array_equal(value, full[:, tuple(t - 1 for t in horizons)], equal_nan=True)):
                    raise ValueError('amended response loses pre-future full-grid predictions or changes sampled values')
    if disposition != 'AVAILABLE':
        if 'forces' in arrays or 'receivers' in arrays:
            raise ValueError('scheduled response nonuse invents an available frozen instrument')
        return
    forces = arrays.get('forces')
    if (not isinstance(forces, np.ndarray) or forces.dtype.str != '<c16'
            or forces.shape != (4, 2, 3, 4, 4) or not np.isfinite(forces).all()
            or any(np.linalg.norm(direction-direction.conj().swapaxes(-1, -2)) > 1e-12
                for direction in forces)):
        raise ValueError('scheduled pulse source lacks the actual fixed frozen force census')
    # The receiver owner independently checks the complete declared HS chart.
    receivers = arrays.get('receivers')
    if not isinstance(receivers, np.ndarray):
        raise ValueError('scheduled response preflight lacks its complete frozen receiver census')
    receiver_metric(protocol, receivers)


def receiver_metric(protocol, receivers):
    """The existing HS24 position/momentum metric, never receiver-count scaling."""
    if receivers.dtype.str != '<c16' or receivers.shape != (48, 2, 2, 3, 4, 4) or not np.isfinite(receivers).all():
        raise ValueError('scheduled error target requires all48 finite original receivers')
    gram = np.einsum('rpsjab,tpsjab->rt', receivers.conj(), receivers)
    errors = (np.linalg.norm(gram-np.eye(48)),
        np.sqrt(np.linalg.norm(receivers[:24, 1])**2+np.linalg.norm(receivers[24:, 0])**2),
        np.linalg.norm(receivers-receivers.conj().swapaxes(-1, -2)))
    if max(errors) > float(protocol.receiver_gram_tolerance):
        raise ValueError('scheduled response changes original HS24 metric/chart/phase support')
    return tuple(Decimal(str(float(v))) for v in errors)


def assess_responses(source, causal, history, prefix_arrays, error_seal, physical, frozen_arrays, protocol,
        panels, responses, response_arrays, *, score_id):
    """Literal transitions, exact bridge, all signed receiver errors and15 targets."""
    protocol.public_source.validate_source(source)
    if (type(error_seal) is not ScheduledForecastSeal or error_seal.source != identity(source)
            or error_seal.prefix != identity(causal) or physical.source != identity(source)
            or physical.causal_prefix != identity(causal) or responses.source != identity(source)
            or responses.physical_forecast != ObjectIdentity.from_record(physical.forecast_id, physical)
            or responses.error_forecast != identity(error_seal)
            or responses.protocol != ObjectIdentity.from_record(protocol.protocol_id, protocol)
            or physical.protocol != responses.protocol or responses.causal_prefix != identity(causal)
            or history.source != identity(source) or causal.history != identity(history)
            or error_seal.criterion != protocol.criterion
            or type(protocol.mechanical_model) is not MatrixOriginResponseModel and len(protocol.horizon_steps) != 3):
        raise ValueError('scheduled assessment substitutes original source/prefix/frozen menu/seals')
    return assess_paired_response_arrays(source, causal, history, prefix_arrays, physical, frozen_arrays,
        protocol, panels, responses, response_arrays, error_forecast=identity(error_seal), score_id=score_id)


def assess_paired_response_arrays(source, causal, history, prefix_arrays, physical, frozen_arrays, protocol,
        panels, responses, response_arrays, *, error_forecast: ObjectIdentity, score_id):
    """Original complete received-array arithmetic after caller-owned seal guards.

    The forecast reference joins these exact received arrays. It supplies no
    forecast qualification, source eligibility, chronology or authority. The
    caller validates its actual scientific forecast and original protocol.
    """
    if type(error_forecast) is not ObjectIdentity:
        raise TypeError('scheduled assessment requires its exact forecast identity')
    error_forecast.__post_init__()
    protocol.public_source.validate_source(source)
    if (physical.source != identity(source) or physical.causal_prefix != identity(causal)
            or responses.source != identity(source)
            or responses.physical_forecast != ObjectIdentity.from_record(physical.forecast_id, physical)
            or responses.error_forecast != error_forecast
            or responses.protocol != ObjectIdentity.from_record(protocol.protocol_id, protocol)
            or physical.protocol != responses.protocol or responses.causal_prefix != identity(causal)
            or history.source != identity(source) or causal.history != identity(history)
            or physical.mechanical_model != ObjectIdentity.from_record(protocol.mechanical_model.model_id, protocol.mechanical_model)
            or type(protocol.mechanical_model) is not MatrixOriginResponseModel and len(protocol.horizon_steps) != 3):
        raise ValueError('scheduled assessment substitutes original source/prefix/frozen menu/seals')
    census = branch_census(protocol, panels)
    if responses.branch_ids != tuple(row[0] for row in census):
        raise ValueError('scheduled assessment thins complete48 nested branch denominator')
    controls, cells, reasons = [], [], []
    available = responses.disposition == 'COMPLETED' and physical.disposition == 'AVAILABLE'
    if available:
        receiver_metric(protocol, frozen_arrays['receivers'])
        expected = {'noise.'+p.panel_id+'.'+n for p in panels for n in ('primary', 'fine', 'bridge')}
        expected.update('branch.'+b+'.'+n for b, *_ in census for n in ('positions', 'momenta', 'innovations', 'ticks', 'alpha_tilde'))
        if set(response_arrays) != expected:
            raise ValueError('scheduled response drops/extends original complete branch/noise/clock members')
        paired = SimpleNamespace(primary=SimpleNamespace(horizon_steps=protocol.horizon_steps, view=source.coordinate.primary_view),
            fine_view=source.coordinate.fine_view)
        for panel in panels:
            noise = {n: response_arrays['noise.'+panel.panel_id+'.'+n] for n in ('primary', 'fine', 'bridge')}
            verify_noise_pair(paired, noise['primary'], noise['fine'], noise['bridge'])
        for branch, view, panel, action, sign in census:
            label, mult = view.lower(), 1 if view == 'PRIMARY' else 2
            values = {n: response_arrays['branch.'+branch+'.'+n] for n in ('positions', 'momenta', 'innovations', 'ticks', 'alpha_tilde')}
            if not np.array_equal(values['innovations'], response_arrays['noise.'+panel.panel_id+'.'+label]):
                raise ValueError('scheduled response replaces common innovations across actions/signs')
            control = assess_scheduled_branch(source.coordinate, values, refinement=mult,
                initial_positions=prefix_arrays[label+'_positions'][-1], initial_momenta=prefix_arrays[label+'_momenta'][-1],
                start_tick=mult*source.policy.cutoff_tick, direction=frozen_arrays['forces'][protocol.actions.index(action)],
                amplitude=0 if sign == 'HOLD' else float(action.amplitude)*(1 if sign == 'PLUS' else -1),
                pulse_steps=mult*action.pulse_steps, tolerance=protocol.native_reference_tolerance,
                control_id='control.scheduled.'+source.root_id+'.'+branch)
            controls.append(control)
        if any(c.disposition != 'SATISFIED' for c in controls):
            reasons.append('literal-full192-native-transition-violated')
    else:
        reasons.append(responses.disposition.lower())
        if set(response_arrays) != {'unentered_branches'} or not np.array_equal(response_arrays['unentered_branches'], np.arange(48, dtype='<i8')):
            raise ValueError('scheduled nonuse response invents received native branch arrays')
    passed = available and len(controls) == 48 and all(c.disposition == 'SATISFIED' for c in controls)
    dense = None
    if type(protocol.mechanical_model) is MatrixOriginResponseModel:
        cells, dense = dense_response_measurements(protocol, panels, response_arrays, frozen_arrays,
            available=available, numerical_usable=passed)
        cumulative = dense.factor_log_targets
    else:
        cells = _response_loss_cells(source, protocol, panels, response_arrays, frozen_arrays,
            horizons=protocol.horizon_steps, available=available)
        cumulative = []
        for predictor in PREDICTORS:
            for horizon in protocol.horizon_steps:
                values = [c.normalized_error for c in cells if c.view == 'PRIMARY' and c.predictor == predictor and c.horizon_tick <= horizon]
                with localcontext() as ctx:
                    ctx.prec = 50
                    cumulative.append(None if not passed or any(v is None for v in values) else (Decimal(1)+max(values)).ln())
    disposition = ('FINITE' if all(v is not None for v in cumulative) else 'PARTIAL') if passed else (
        'NATIVE_CROSSCHECK_FAILED' if available else 'NO_ORIGIN' if responses.disposition == 'NO_ORIGIN' else
        'INSTRUMENT_UNRESOLVED' if responses.disposition == 'INSTRUMENT_UNRESOLVED' else 'UNEVALUABLE')
    return ScheduledResponseScore(score_id, identity(source), identity(causal), error_forecast,
        ObjectIdentity.from_record(physical.forecast_id, physical), ObjectIdentity.from_record(responses.response_id, responses),
        source.root_id, source.root.root.independent_group_id, source.root.root.role.value, protocol.criterion,
        tuple(controls), passed, disposition, tuple(cells), tuple(cumulative), tuple(sorted(set(reasons))), dense)


def _response_loss_cells(source, protocol, panels, response_arrays, frozen_arrays, *, horizons, available, dense=False):
    """One unchanged HS24/nominal-actuator arithmetic owner for sampled cells."""
    cells = []
    for view, mult in (('PRIMARY', 1), ('FINE', 2)):
        for panel in panels:
            for action_index, action in enumerate(protocol.actions):
                truths = {}
                for predictor in PREDICTORS:
                    for horizon_index, horizon in enumerate(horizons):
                        truth = signed = absolute = relative = normalized = qnorm = pnorm = None
                        if available:
                            if horizon not in truths:
                                stem = view.lower()+'.'+panel.panel_id+'.'+action.action_id
                                odd = np.stack(tuple((response_arrays['branch.'+stem+'.plus.'+phase][mult*horizon]
                                    -response_arrays['branch.'+stem+'.minus.'+phase][mult*horizon])/2 for phase in ('positions', 'momenta')))
                                actual = np.einsum('rpsjab,psjab->r', frozen_arrays['receivers'].conj(), odd).real
                                truth = tuple(Decimal(str(float(v))) for v in actual)
                                truths[horizon] = actual, truth
                            else:
                                actual, truth = truths[horizon]
                            predicted = frozen_arrays[view.lower()+'_'+predictor.lower()][action_index, horizon_index]
                            if np.isfinite(predicted).all():
                                signed = tuple(Decimal(str(float(v))) for v in predicted-actual)
                                absolute = tuple(abs(v) for v in signed)
                                relative = tuple(None if abs(t) <= protocol.weak_response_minimum else e/abs(t)
                                    for t, e in zip(truth, absolute, strict=True))
                                qnorm, pnorm, normalized = response_error_norms(signed, action=action,
                                    primary_timestep=source.coordinate.primary_view.timestep, horizon_tick=horizon)
                        if dense:
                            cells.append(ScheduledE4DenseResponseCell(view, panel.panel_id, action.action_id,
                                predictor, horizon, qnorm, pnorm, normalized))
                        else:
                            cells.append(ScheduledResponseLossCell(view, panel.panel_id, action.action_id, predictor, horizon,
                                truth, signed, absolute, relative, normalized))
    cells.sort(key=lambda c: c.key)
    return cells


def score_e4_dense(source, protocol, panels, *, target, secondary, original_score, original_physical,
        dense_physical, responses, original_forecast_raw, dense_forecast_raw, response_raw, score_id):
    """Pure production/read reproof from exact original and supplementary archives.

    Caller retains current access, original native validation and receipt joins.
    This performs no acquisition, noise generation, native entry or fitting.
    """
    from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays
    from .response_records import ScheduledE4DenseMechanicalForecast, _e4_original_forecast
    from .selected_e3_e4_records import SelectedE3E4MechanicalForecast, SelectedE3E4Responses
    from .selected_e4_native_records import SelectedE4ProtectedResponses
    _e4_original_forecast(original_physical)
    response_kind = SelectedE3E4Responses if type(original_physical) is SelectedE3E4MechanicalForecast else SelectedE4ProtectedResponses
    if type(original_score) is not ScheduledResponseScore or type(dense_physical) is not ScheduledE4DenseMechanicalForecast or type(responses) is not response_kind:
        raise TypeError('dense E4 score requires exact actual original/dense/response record owners')
    original_score.__post_init__()
    responses.__post_init__()
    dense_physical.validate_original(protocol, target, secondary, original_physical)
    protocol.public_source.validate_source(source)
    response_pin = ObjectIdentity.from_record(responses.response_id, responses)
    if (original_score.source != identity(source) or original_score.causal_prefix != original_physical.causal_prefix
            or original_score.criterion != protocol.criterion
            or original_score.physical_forecast != ObjectIdentity.from_record(original_physical.forecast_id, original_physical)
            or original_score.responses != response_pin or responses.physical_forecast != original_score.physical_forecast
            or responses.source != original_score.source or responses.causal_prefix != original_score.causal_prefix
            or responses.error_forecast != original_score.error_forecast
            or responses.protocol != ObjectIdentity.from_record(protocol.protocol_id, protocol)
            or responses.branch_ids != tuple(row[0] for row in branch_census(protocol, panels))):
        raise ValueError('dense E4 score substitutes exact original score/source/cutoff/native response census')
    original = decode_matrix_arrays(original_forecast_raw, original_physical.arrays)
    predictions = decode_matrix_arrays(dense_forecast_raw, dense_physical.arrays)
    received = decode_matrix_arrays(response_raw, responses.arrays)
    expected = {'noise.' + panel.panel_id + '.' + name for panel in panels for name in ('primary', 'fine', 'bridge')}
    expected.update('branch.' + branch + '.' + name for branch, *_ in branch_census(protocol, panels)
        for name in ('positions', 'momenta', 'innovations', 'ticks', 'alpha_tilde'))
    available = responses.disposition == 'COMPLETED' and original_physical.disposition == 'AVAILABLE'
    if available != (original_score.disposition in ('FINITE', 'PARTIAL', 'NATIVE_CROSSCHECK_FAILED')):
        raise ValueError('dense E4 score substitutes original received/native nonuse disposition')
    if available:
        if set(received) != expected:
            raise ValueError('dense E4 score changes the complete actual response archive census')
    elif (set(received) != {'unentered_branches'}
            or not np.array_equal(received['unentered_branches'], np.arange(48, dtype='<i8'))):
        raise ValueError('dense E4 nonuse invents received branch arrays')
    frozen = {**original, **predictions}
    indices = tuple(target.observation_horizons.index(horizon) for horizon in protocol.horizon_steps)
    for name, value in predictions.items():
        sampled = value[:, indices, :]
        if sampled.dtype != original[name].dtype or sampled.shape != original[name].shape or sampled.tobytes() != original[name].tobytes():
            raise ValueError('dense E4 score changes original3sample mechanical prediction values')
    validate_frozen_response_arrays(protocol, original, disposition=original_physical.disposition)
    validate_frozen_response_arrays(protocol, frozen, disposition=dense_physical.disposition,
        observation_horizons=target.observation_horizons)
    if original_score.dense is not None:
        from empirical_lawhood.adapters.methods.matrix_factor_response.response_scoring import dense_response_measurements
        cells, dense = dense_response_measurements(protocol, panels, received, original,
            available=available, numerical_usable=original_score.numerical_pass)
        if cells != original_score.cells or dense != original_score.dense:
            raise ValueError('matched E4 score projection changes independently replayed original dense measurements')
    else:
        cells = tuple(_response_loss_cells(source, protocol, panels, received, frozen,
            horizons=target.observation_horizons, available=available, dense=True))
    result = ScheduledE4DenseResponseScore(score_id, ObjectIdentity.from_record(original_score.score_id, original_score),
        dense_physical.identity, dense_physical.arrays.array_artifact, response_pin, responses.arrays.array_artifact,
        target.identity, secondary.identity, identity(source), original_score.causal_prefix,
        ObjectIdentity.from_record(protocol.protocol_id, protocol), protocol.public_source.policy.cutoff_tick,
        original_score.root_id, original_score.independent_group_id, original_score.role, original_score.numerical_pass,
        original_score.disposition, original_score.reason_codes, cells)
    result.validate_original(protocol, panels, target, secondary, original_score)
    return result
