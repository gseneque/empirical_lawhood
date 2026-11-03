# SPDX-License-Identifier: MPL-2.0
"""Shared finite odd-response metric and sampled-duration mathematics.

Native transition, source, view-pair and forecast-seal checks remain with the
calling assessor. Unknown measurements are neither successes nor observed
physical failures. No fitted account or acquisition is constructed here.
"""

from dataclasses import dataclass
from decimal import Decimal, localcontext
from typing import ClassVar

import numpy as np

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_decimal, validate_stable_id

from .origin_mechanics import MatrixOriginResponseModel, ORIGIN_RESPONSE_PREDICTORS


DENSE_RESPONSE_HORIZONS = tuple(range(16, 129, 4))
RESPONSE_PRIMARY_TIMESTEP = Decimal('0.001')
RESPONSE_FINE_TIMESTEP = Decimal('0.0005')
RESPONSE_HEADLINE_TOLERANCE = Decimal('0.01')
RESPONSE_SENSITIVITY_TOLERANCES = (Decimal('0.005'), Decimal('0.02'), Decimal('0.05'))
RESPONSE_CHALLENGERS = ('GENERIC_SLOW', 'IO48', 'SPECTRA')
RESPONSE_VIEWS = ('PRIMARY', 'FINE')
RESPONSE_CONTRASTS = ('EVEN_FROM_HOLD', 'MINUS_FROM_HOLD', 'ODD', 'PLUS_FROM_HOLD')


def nominal_actuator_scales(action, primary_timestep, horizon_tick):
    """Exact declared impulse/displacement, including partial-pulse times."""
    validate_decimal(primary_timestep, field_name='primary timestep', minimum=Decimal(0))
    if primary_timestep == 0 or type(horizon_tick) is not int or horizon_tick < 1:
        raise ValueError('normalised response requires a strictly positive physical time')
    if type(action.pulse_steps) is not int or action.pulse_steps < 1:
        raise ValueError('normalised response requires its declared pulse length')
    for name in ('amplitude', 'force_norm'):
        value = getattr(action, name)
        validate_decimal(value, field_name=name, minimum=Decimal(0))
        if value == 0:
            raise ValueError('normalised response requires a positive declared actuator')
    duration = primary_timestep * horizon_tick
    pulse = primary_timestep * min(action.pulse_steps, horizon_tick)
    impulse = action.amplitude * action.force_norm * pulse
    return impulse * (duration - pulse / 2), impulse


def response_error_norms(signed_errors, *, action, primary_timestep, horizon_tick):
    """Original 24-position/24-momentum Decimal arithmetic at precision 60."""
    if type(signed_errors) is not tuple or len(signed_errors) != 48:
        raise ValueError('response error requires the complete HS24 position/momentum chart')
    for value in signed_errors:
        validate_decimal(value, field_name='signed receiver error')
    with localcontext() as context:
        context.prec = 60
        position_scale, momentum_scale = nominal_actuator_scales(action, primary_timestep, horizon_tick)
        qnorm = sum(value * value for value in signed_errors[:24]).sqrt()
        pnorm = sum(value * value for value in signed_errors[24:]).sqrt()
        normalized = max(qnorm / position_scale, pnorm / momentum_scale)
    return qnorm, pnorm, normalized


@dataclass(frozen=True, slots=True)
class ResponseContrasts:
    """Receiver curves from received arrays, in original finite-response units."""

    odd: np.ndarray
    plus_from_hold: np.ndarray
    minus_from_hold: np.ndarray
    even_from_hold: np.ndarray


def response_contrasts(plus, minus, hold, receivers):
    """Keep the signed, HOLD-relative and even responses without rescaling.

    State arrays have axes time, phase, sector, matrix, row, column. The caller
    selects physically aligned post-step times from the retained native arrays.
    """
    expected = (2, 2, 3, 4, 4)
    if (not isinstance(receivers, np.ndarray) or receivers.dtype.str != '<c16'
            or receivers.shape != (48, *expected) or not np.isfinite(receivers).all()
            or any(not isinstance(value, np.ndarray) or value.dtype.str != '<c16'
                or value.ndim != 6 or value.shape[1:] != expected or not value.shape[0]
                or not np.isfinite(value).all() for value in (plus, minus, hold))
            or plus.shape != minus.shape or plus.shape != hold.shape):
        raise ValueError('response contrasts require complete finite matched native states and receivers')

    def project(values):
        return np.einsum('rpsjab,tpsjab->tr', receivers.conj(), values).real

    return ResponseContrasts(project((plus - minus) / 2), project(plus - hold),
        project(minus - hold), project((plus - hold + minus - hold) / 2))


def cumulative_response_errors(point_errors):
    """Unknown previous maxima stay unknown; they are never zero-filled."""
    maximum, unresolved, values = Decimal(0), False, []
    for value in point_errors:
        if value is None:
            unresolved = True
        else:
            validate_decimal(value, field_name='response error', minimum=Decimal(0))
            maximum = max(maximum, value)
        values.append(None if unresolved else maximum)
    return tuple(values)


def sampled_pass_count_bounds(values):
    """Feasible K over the exact 29 checks, including known later failures."""
    if (type(values) is not tuple or len(values) != 29
            or any(value is not None and type(value) is not bool for value in values)):
        raise ValueError('sampled pass count requires all 29 explicit pass/fail/unknown checks')
    lower = next((index for index, passed in enumerate(values) if passed is not True), 29)
    upper = next((index for index, passed in enumerate(values) if passed is False), 29)
    return lower, upper


@dataclass(frozen=True, slots=True)
class MatrixSampledResponseDuration(CanonicalRecord):
    """All 29 checks, observed error bounds and explicit menu completeness.

    With incomplete action/panel measurements, a known error is a lower bound
    on the maximum. It can prove failure but cannot prove a passing check.
    """

    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-response/sampled-duration'
    point_errors: tuple[Decimal | None, ...]
    tolerance: Decimal
    numerical_usable: bool
    point_complete: tuple[bool, ...]
    observation_horizons: tuple[int, ...] = DENSE_RESPONSE_HORIZONS

    def __post_init__(self):
        if (type(self.point_errors) is not tuple or len(self.point_errors) != 29
                or type(self.observation_horizons) is not tuple
                or any(type(tick) is not int for tick in self.observation_horizons)
                or self.observation_horizons != DENSE_RESPONSE_HORIZONS
                or type(self.numerical_usable) is not bool
                or type(self.point_complete) is not tuple or len(self.point_complete) != 29
                or any(type(value) is not bool for value in self.point_complete)
                or any(complete and value is None for value, complete in zip(self.point_errors, self.point_complete, strict=True))
                or type(self.tolerance) is not Decimal
                or self.tolerance not in (RESPONSE_HEADLINE_TOLERANCE, *RESPONSE_SENSITIVITY_TOLERANCES)):
            raise ValueError('sampled duration changes its complete grid, tolerance family or numerical disposition')
        for value in self.point_errors:
            if value is not None:
                validate_decimal(value, field_name='sampled response error', minimum=Decimal(0))

    @property
    def sampled_passes(self):
        return tuple(None if not self.numerical_usable or error is None else False if error > self.tolerance
            else True if complete else None
            for error, complete in zip(self.point_errors, self.point_complete, strict=True))

    @property
    def count_bounds(self):
        """Feasible initial-pass counts; later known failure still bounds K."""
        return sampled_pass_count_bounds(self.sampled_passes)

    @property
    def count(self):
        lower, upper = self.count_bounds
        return lower if lower == upper else None

    @property
    def complete_followup(self):
        return self.numerical_usable and all(self.point_complete)

    @property
    def right_censored(self):
        return self.complete_followup and self.count == 29

    @property
    def first_known_failure_tick(self):
        return next((tick for tick, passed in zip(self.observation_horizons, self.sampled_passes, strict=True)
            if passed is False), None)

    @property
    def first_unknown_tick(self):
        return next((tick for tick, passed in zip(self.observation_horizons, self.sampled_passes, strict=True)
            if passed is None), None)

    def adequate_through(self, horizon_tick):
        if type(horizon_tick) is not int or horizon_tick not in self.observation_horizons:
            raise ValueError('sampled adequacy requires an actual prespecified check')
        values = self.sampled_passes[:self.observation_horizons.index(horizon_tick) + 1]
        if any(value is False for value in values):
            return False
        return None if any(value is None for value in values) else True


def paired_duration_loss(predicted, observed):
    """Mean absolute K error across two views, divided by all 29 checks."""
    if (type(predicted) is not tuple or type(observed) is not tuple
            or len(predicted) != 2 or len(observed) != 2
            or any(type(row) is not MatrixSampledResponseDuration for row in (*predicted, *observed))
            or len({row.tolerance for row in (*predicted, *observed)}) != 1):
        raise ValueError('duration loss requires the same exact tolerance and both nested views')
    counts = tuple(row.count for row in (*predicted, *observed))
    if any(value is None for value in counts):
        return None
    with localcontext() as context:
        context.prec = 60
        return sum(Decimal(abs(a.count - b.count)) for a, b in zip(predicted, observed, strict=True)) / 58


def paired_adequacy(durations, horizon_tick):
    if type(durations) is not tuple or len(durations) != 2 or any(type(row) is not MatrixSampledResponseDuration for row in durations):
        raise ValueError('paired adequacy requires both complete sampled-view records')
    if durations[0].tolerance != durations[1].tolerance:
        raise ValueError('paired adequacy changes tolerance between views')
    values = tuple(row.adequate_through(horizon_tick) for row in durations)
    if False in values:
        return False
    return None if None in values else True


def joint_structural_advantage(factor, challengers, *, numerical_usable):
    """One strict E2 event against all three challengers in both views.

    Inputs are the cumulative losses through tick 128. ``None`` denotes an
    unresolved common comparison; the whole-roster operational test counts
    only ``True`` as success, while retaining nonuse separately from losses.
    """
    if (type(numerical_usable) is not bool or type(challengers) is not dict
            or set(challengers) != set(RESPONSE_CHALLENGERS)):
        raise ValueError('E2 structural event requires the exact three-challenger conjunction')
    rows = (factor, *(challengers[name] for name in RESPONSE_CHALLENGERS))
    if any(type(row) is not tuple or len(row) != 2 for row in rows):
        raise ValueError('E2 structural event requires both nested views for every comparator')
    for row in rows:
        for value in row:
            if value is not None:
                validate_decimal(value, field_name='cumulative response error', minimum=Decimal(0))
    if not numerical_usable or any(value is None for row in rows for value in row):
        return None
    with localcontext() as context:
        context.prec = 60
        if any(abs(primary - fine) > Decimal('0.0001') for primary, fine in rows):
            return None
        return all(challenger - candidate > Decimal('0.001')
            for row in rows[1:] for candidate, challenger in zip(factor, row, strict=True))


@dataclass(frozen=True, slots=True)
class MatrixDenseResponseCell(CanonicalRecord):
    """One compact scored check; original arrays retain all receiver vectors."""

    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-response/dense-response-cell'
    view: str
    panel_id: str
    action_id: str
    predictor: str
    horizon_tick: int
    position_error_norm: Decimal | None
    momentum_error_norm: Decimal | None
    normalized_error: Decimal | None

    def __post_init__(self):
        validate_stable_id(self.panel_id)
        validate_stable_id(self.action_id)
        values = (self.position_error_norm, self.momentum_error_norm, self.normalized_error)
        if (self.view not in RESPONSE_VIEWS or self.predictor not in ORIGIN_RESPONSE_PREDICTORS
                or type(self.horizon_tick) is not int or self.horizon_tick not in DENSE_RESPONSE_HORIZONS
                or any(value is None for value in values) != all(value is None for value in values)):
            raise ValueError('dense response cell changes its exact method/check or partial receiver norm')
        for value in values:
            if value is not None:
                validate_decimal(value, field_name='dense native error norm', minimum=Decimal(0))

    @property
    def key(self):
        return self.view, self.panel_id, self.action_id, self.predictor, self.horizon_tick


@dataclass(frozen=True, slots=True)
class MatrixResponseErrorCurve(CanonicalRecord):
    """Worst observed error at every aligned nonzero tick, with completeness."""

    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-response/full-grid-error-curve'
    view: str
    predictor: str
    point_errors: tuple[Decimal | None, ...]
    point_complete: tuple[bool, ...]

    def __post_init__(self):
        if (self.view not in RESPONSE_VIEWS
                or self.predictor not in (*ORIGIN_RESPONSE_PREDICTORS, 'FULL_MINUS_FACTOR')
                or type(self.point_errors) is not tuple or len(self.point_errors) != 128
                or type(self.point_complete) is not tuple or len(self.point_complete) != 128
                or any(type(value) is not bool for value in self.point_complete)
                or any(complete and error is None for error, complete in zip(self.point_errors, self.point_complete, strict=True))):
            raise ValueError('response diagnostic changes its complete aligned tick1..128 grid')
        for value in self.point_errors:
            if value is not None:
                validate_decimal(value, field_name='response diagnostic error', minimum=Decimal(0))

    def duration(self, *, numerical_usable, tolerance=RESPONSE_HEADLINE_TOLERANCE):
        return MatrixSampledResponseDuration(tuple(self.point_errors[t - 1] for t in DENSE_RESPONSE_HORIZONS),
            tolerance, numerical_usable, tuple(self.point_complete[t - 1] for t in DENSE_RESPONSE_HORIZONS))

    def cumulative_sampled_errors(self, *, numerical_usable):
        return cumulative_response_errors(tuple(self.point_errors[t - 1]
            if numerical_usable and self.point_complete[t - 1] else None for t in DENSE_RESPONSE_HORIZONS))


@dataclass(frozen=True, slots=True)
class MatrixResponseAmplitudeCurve(CanonicalRecord):
    """Raw signed extrema, block norms and complement at ticks zero through128.

    The original native states and frozen receiver map retain every signed
    component. These bounded scalar diagnostics do not replace those arrays.
    """

    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-response/native-amplitude-curve'
    view: str
    panel_id: str
    action_id: str
    contrast: str
    position_norms: tuple[Decimal | None, ...]
    momentum_norms: tuple[Decimal | None, ...]
    position_minima: tuple[Decimal | None, ...]
    position_maxima: tuple[Decimal | None, ...]
    momentum_minima: tuple[Decimal | None, ...]
    momentum_maxima: tuple[Decimal | None, ...]
    complement_position_norms: tuple[Decimal | None, ...]
    complement_momentum_norms: tuple[Decimal | None, ...]
    sector_x_position_norms: tuple[Decimal | None, ...]
    sector_y_position_norms: tuple[Decimal | None, ...]
    sector_x_momentum_norms: tuple[Decimal | None, ...]
    sector_y_momentum_norms: tuple[Decimal | None, ...]
    normalized_amplitudes: tuple[Decimal | None, ...]

    def __post_init__(self):
        validate_stable_id(self.panel_id)
        validate_stable_id(self.action_id)
        names = ('position_norms', 'momentum_norms', 'position_minima', 'position_maxima',
            'momentum_minima', 'momentum_maxima', 'complement_position_norms',
            'complement_momentum_norms', 'sector_x_position_norms', 'sector_y_position_norms',
            'sector_x_momentum_norms', 'sector_y_momentum_norms', 'normalized_amplitudes')
        if (self.view not in RESPONSE_VIEWS or self.contrast not in RESPONSE_CONTRASTS
                or any(type(getattr(self, name)) is not tuple or len(getattr(self, name)) != 129 for name in names)
                or self.normalized_amplitudes[0] is not None):
            raise ValueError('native amplitudes change raw tick-zero handling or the complete signed contrast grid')
        for name in names:
            for value in getattr(self, name):
                if value is not None:
                    validate_decimal(value, field_name='native response amplitude',
                        **({'minimum': Decimal(0)} if name.endswith('norms') or name == 'normalized_amplitudes' else {}))
        for index in range(129):
            raw = tuple(getattr(self, name)[index] for name in names[:-1])
            if (any(value is None for value in raw) != all(value is None for value in raw)
                    or index and (self.normalized_amplitudes[index] is None) != (raw[0] is None)
                    or raw[0] is not None and (raw[2] > raw[3] or raw[4] > raw[5])):
                raise ValueError('native amplitudes lose exact signed-range or complete-vector missingness')

    @property
    def key(self):
        return self.view, self.panel_id, self.action_id, self.contrast


@dataclass(frozen=True, slots=True)
class MatrixDenseResponseDiagnostics(CanonicalRecord):
    """Complete deterministic diagnostics for the amended response contract."""

    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-response/dense-response-diagnostics'
    mechanical_model: ObjectIdentity
    action_ids: tuple[str, ...]
    panel_ids: tuple[str, ...]
    numerical_usable: bool
    curves: tuple[MatrixResponseErrorCurve, ...]
    origin_curves: tuple[MatrixResponseErrorCurve, ...]
    amplitudes: tuple[MatrixResponseAmplitudeCurve, ...]

    def __post_init__(self):
        if (type(self.mechanical_model) is not ObjectIdentity or self.mechanical_model.object_schema != MatrixOriginResponseModel.SCHEMA
                or type(self.numerical_usable) is not bool
                or type(self.action_ids) is not tuple or len(self.action_ids) != 4 or self.action_ids != tuple(sorted(set(self.action_ids)))
                or type(self.panel_ids) is not tuple or len(self.panel_ids) != 2 or self.panel_ids != tuple(sorted(set(self.panel_ids)))
                or type(self.curves) is not tuple or any(type(row) is not MatrixResponseErrorCurve for row in self.curves)
                or tuple((row.view, row.predictor) for row in self.curves) != tuple(
                    (view, predictor) for view in RESPONSE_VIEWS for predictor in ORIGIN_RESPONSE_PREDICTORS)
                or type(self.origin_curves) is not tuple or any(type(row) is not MatrixResponseErrorCurve for row in self.origin_curves)
                or tuple((row.view, row.predictor) for row in self.origin_curves) != tuple((view, 'FULL_MINUS_FACTOR') for view in RESPONSE_VIEWS)
                or type(self.amplitudes) is not tuple or any(type(row) is not MatrixResponseAmplitudeCurve for row in self.amplitudes)
                or tuple(row.key for row in self.amplitudes) != tuple(sorted((v, p, a, c)
                    for v in RESPONSE_VIEWS for p in self.panel_ids for a in self.action_ids for c in RESPONSE_CONTRASTS))):
            raise ValueError('dense diagnostics thin the complete paired method/action/panel/contrast census')
        for value in (*self.action_ids, *self.panel_ids):
            validate_stable_id(value)
        self.mechanical_model.__post_init__()
        for row in (*self.curves, *self.origin_curves, *self.amplitudes):
            row.__post_init__()

    @property
    def factor_log_targets(self):
        with localcontext() as context:
            context.prec = 60
            return tuple(None if value is None else (Decimal(1) + value).ln()
                for row in self.curves if row.predictor == 'FACTOR'
                for value in row.cumulative_sampled_errors(numerical_usable=self.numerical_usable))

    def validate_cells(self, cells):
        expected = tuple(sorted((v, p, a, m, h) for v in RESPONSE_VIEWS
            for p in self.panel_ids for a in self.action_ids for m in ORIGIN_RESPONSE_PREDICTORS for h in DENSE_RESPONSE_HORIZONS))
        if type(cells) is not tuple or any(type(row) is not MatrixDenseResponseCell for row in cells) or tuple(row.key for row in cells) != expected:
            raise ValueError('dense response loses its complete3248 sampled cells')
        for row in cells:
            row.__post_init__()
        by_key = {(row.view, row.predictor, row.horizon_tick): [] for row in cells}
        for row in cells:
            by_key[row.view, row.predictor, row.horizon_tick].append(row.normalized_error)
        for curve in self.curves:
            for tick in DENSE_RESPONSE_HORIZONS:
                values = by_key[curve.view, curve.predictor, tick]
                known = tuple(value for value in values if value is not None)
                if ((max(known) if known else None) != curve.point_errors[tick - 1]
                        or (len(known) == 8) != curve.point_complete[tick - 1]):
                    raise ValueError('dense response curve differs from its complete native sampled cells')


def _decimal_vector(values):
    return tuple(Decimal(str(float(value))) for value in values)


def _error_norms_or_unknown(values, action, tick):
    if not np.isfinite(values).all():
        return None, None, None
    return response_error_norms(_decimal_vector(values), action=action,
        primary_timestep=RESPONSE_PRIMARY_TIMESTEP, horizon_tick=tick)


def origin_response_discrepancy(protocol, frozen_arrays):
    """Causal FULL/FACTOR defect; receives only the sealed mechanical arrays."""
    if type(protocol.mechanical_model) is not MatrixOriginResponseModel or protocol.horizon_steps != DENSE_RESPONSE_HORIZONS:
        raise ValueError('origin response defect requires the complete amended assay')
    curves = []
    for view in RESPONSE_VIEWS:
        values, complete = [], []
        full, factor = (frozen_arrays[view.lower() + '_full_grid_' + name] for name in ('full_coupled', 'factor'))
        if any(value.dtype.str != '<f8' or value.shape != (4, 128, 48) for value in (full, factor)):
            raise ValueError('origin defect loses its full fixed action/receiver/physical clock')
        for index in range(128):
            losses = tuple(_error_norms_or_unknown(full[i, index] - factor[i, index], action, index + 1)[2]
                for i, action in enumerate(protocol.actions))
            known = tuple(value for value in losses if value is not None)
            values.append(max(known) if known else None)
            complete.append(len(known) == 4)
        curves.append(MatrixResponseErrorCurve(view, 'FULL_MINUS_FACTOR', tuple(values), tuple(complete)))
    return tuple(curves)


def origin_response_defect_feature(protocol, frozen_arrays):
    """PRIMARY log1p max over the exact29 checks; FINE remains diagnostic."""
    primary, _fine = origin_response_discrepancy(protocol, frozen_arrays)
    values = primary.cumulative_sampled_errors(numerical_usable=True)
    with localcontext() as context:
        context.prec = 60
        return None if values[-1] is None else (Decimal(1) + values[-1]).ln()


def validate_dense_score_units(protocol, score):
    """Recheck compact scalar units and their original complete dense binding."""
    if (type(score.dense) is not MatrixDenseResponseDiagnostics or score.dense.mechanical_model !=
            ObjectIdentity.from_record(protocol.mechanical_model.model_id, protocol.mechanical_model)):
        raise ValueError('dense response score changes its original mechanical model')
    score.dense.validate_cells(score.cells)
    actions = {action.action_id: action for action in protocol.actions}
    for value in score.cells:
        if value.normalized_error is not None:
            with localcontext() as context:
                context.prec = 60
                qscale, pscale = nominal_actuator_scales(actions[value.action_id],
                    protocol.public_source.coordinate.primary_view.timestep, value.horizon_tick)
                expected = max(value.position_error_norm / qscale, value.momentum_error_norm / pscale)
            if value.normalized_error != expected:
                raise ValueError('dense response score changes exact block norms or nominal actuator units')


def _amplitude_curve(view, panel_id, action, contrast, native, receivers):
    projected = np.einsum('rpsjab,tpsjab->tr', receivers.conj(), native).real
    complement = native - np.einsum('tr,rpsjab->tpsjab', projected, receivers)
    columns = [[] for _ in range(13)]
    for tick, values in enumerate(projected):
        if np.isfinite(native[tick]).all() and np.isfinite(values).all() and np.isfinite(complement[tick]).all():
            row = _decimal_vector(values)
            with localcontext() as context:
                context.prec = 60
                qnorm, pnorm = (sum(value * value for value in block).sqrt() for block in (row[:24], row[24:]))
            raw = (qnorm, pnorm, min(row[:24]), max(row[:24]), min(row[24:]), max(row[24:]),
                Decimal(str(float(np.linalg.norm(complement[tick, 0])))), Decimal(str(float(np.linalg.norm(complement[tick, 1])))))
            raw = (*raw, *(Decimal(str(float(np.linalg.norm(native[tick, phase, sector]))))
                for phase in range(2) for sector in range(2)))
            normalized = None if tick == 0 else response_error_norms(row, action=action,
                primary_timestep=RESPONSE_PRIMARY_TIMESTEP, horizon_tick=tick)[2]
            sample = (*raw, normalized)
        else:
            sample = (None,) * 13
        for column, value in zip(columns, sample, strict=True):
            column.append(value)
    return MatrixResponseAmplitudeCurve(view, panel_id, action.action_id, contrast,
        *(tuple(column) for column in columns)), projected


def unobserved_dense_response_measurements(protocol, panels):
    """Keep every unknown-contact cell without reading or claiming observations.

    Origin discrepancies also remain unobserved in this metadata-only record.
    The separately retained physical forecast and its causal feature are intact.
    """
    if (type(protocol.mechanical_model) is not MatrixOriginResponseModel
            or protocol.horizon_steps != DENSE_RESPONSE_HORIZONS
            or len(panels) != 2 or len(protocol.actions) != 4):
        raise ValueError('unobserved dense response changes the original complete assay')
    actions = tuple(action.action_id for action in protocol.actions)
    panel_ids = tuple(panel.panel_id for panel in panels)
    cells = tuple(sorted((MatrixDenseResponseCell(view, panel, action, predictor, tick, None, None, None)
        for view in RESPONSE_VIEWS for panel in panel_ids for action in actions
        for predictor in ORIGIN_RESPONSE_PREDICTORS for tick in DENSE_RESPONSE_HORIZONS), key=lambda row: row.key))
    def curve(view, predictor):
        return MatrixResponseErrorCurve(view, predictor, (None,) * 128, (False,) * 128)
    diagnostics = MatrixDenseResponseDiagnostics(
        ObjectIdentity.from_record(protocol.mechanical_model.model_id, protocol.mechanical_model),
        actions, panel_ids, False,
        tuple(curve(view, predictor) for view in RESPONSE_VIEWS for predictor in ORIGIN_RESPONSE_PREDICTORS),
        tuple(curve(view, 'FULL_MINUS_FACTOR') for view in RESPONSE_VIEWS),
        tuple(sorted((MatrixResponseAmplitudeCurve(view, panel, action, contrast,
            *((None,) * 129 for _ in range(13))) for view in RESPONSE_VIEWS for panel in panel_ids
            for action in actions for contrast in RESPONSE_CONTRASTS), key=lambda row: row.key)))
    diagnostics.validate_cells(cells)
    return cells, diagnostics


def dense_response_measurements(protocol, panels, native_arrays, frozen_arrays, *, available, numerical_usable):
    """Shared scalar scores and signed diagnostics from the complete native data.

    Caller-owned source, pre-future seals and independent transition controls
    establish the meaning of these received arrays. This function neither
    acquires a native case nor authorizes access to one.
    """
    if (type(protocol.mechanical_model) is not MatrixOriginResponseModel or protocol.horizon_steps != DENSE_RESPONSE_HORIZONS
            or type(available) is not bool or type(numerical_usable) is not bool or numerical_usable and not available
            or len(panels) != 2 or len(protocol.actions) != 4):
        raise ValueError('dense response requires the original complete amended assay and explicit numerical use')
    cells, amplitudes, errors = [], [], {}
    for view, multiplier in (('PRIMARY', 1), ('FINE', 2)):
        for panel in panels:
            for action_index, action in enumerate(protocol.actions):
                odd = np.full((129, 48), np.nan, dtype='<f8')
                if available:
                    stem = 'branch.' + view.lower() + '.' + panel.panel_id + '.' + action.action_id + '.'
                    states = {sign: np.stack(tuple(native_arrays[stem + sign + '.' + phase][::multiplier]
                        for phase in ('positions', 'momenta')), axis=1) for sign in ('plus', 'minus', 'hold')}
                    if any(value.shape != (129, 2, 2, 3, 4, 4) or value.dtype.str != '<c16' for value in states.values()):
                        raise ValueError('dense diagnostics lose complete aligned native tick0..128 states')
                    plus, minus, hold = (states[name] for name in ('plus', 'minus', 'hold'))
                    contrasts = {'ODD': (plus - minus) / 2, 'PLUS_FROM_HOLD': plus - hold,
                        'MINUS_FROM_HOLD': minus - hold, 'EVEN_FROM_HOLD': (plus - hold + minus - hold) / 2}
                    for name in RESPONSE_CONTRASTS:
                        amplitude, projected = _amplitude_curve(view, panel.panel_id, action, name,
                            contrasts[name], frozen_arrays['receivers'])
                        amplitudes.append(amplitude)
                        if name == 'ODD':
                            odd = projected
                else:
                    for name in RESPONSE_CONTRASTS:
                        amplitudes.append(MatrixResponseAmplitudeCurve(view, panel.panel_id, action.action_id, name,
                            *((None,) * 129 for _ in range(13))))
                for predictor in ORIGIN_RESPONSE_PREDICTORS:
                    predicted = frozen_arrays[view.lower() + '_full_grid_' + predictor.lower()]
                    if predicted.dtype.str != '<f8' or predicted.shape != (4, 128, 48):
                        raise ValueError('dense diagnostics lose pre-future complete aligned model predictions')
                    for tick in range(1, 129):
                        qnorm, pnorm, error = (_error_norms_or_unknown(predicted[action_index, tick - 1] - odd[tick], action, tick)
                            if available else (None, None, None))
                        errors.setdefault((view, predictor, tick), []).append(error)
                        if tick in DENSE_RESPONSE_HORIZONS:
                            cells.append(MatrixDenseResponseCell(view, panel.panel_id, action.action_id,
                                predictor, tick, qnorm, pnorm, error))
    curves = []
    for view in RESPONSE_VIEWS:
        for predictor in ORIGIN_RESPONSE_PREDICTORS:
            known = [tuple(value for value in errors[view, predictor, tick] if value is not None) for tick in range(1, 129)]
            curves.append(MatrixResponseErrorCurve(view, predictor,
                tuple(max(values) if values else None for values in known), tuple(len(values) == 8 for values in known)))
    result = MatrixDenseResponseDiagnostics(ObjectIdentity.from_record(protocol.mechanical_model.model_id, protocol.mechanical_model),
        tuple(action.action_id for action in protocol.actions), tuple(panel.panel_id for panel in panels), numerical_usable,
        tuple(curves), origin_response_discrepancy(protocol, frozen_arrays), tuple(sorted(amplitudes, key=lambda row: row.key)))
    selected = tuple(sorted(cells, key=lambda row: row.key))
    result.validate_cells(selected)
    return selected, result
