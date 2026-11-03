"""Origin-fixed factor observation/action/receiver chart for native q=2 states.

The retained order is position then momentum, X then Y, components 0..2, and
(I4/2, factor 0, factor 1, factor 2). These are 48 real HS coordinates out of
the full 192 native coordinates. The complement remains a full native operand.
This pure chart neither advances a native branch nor fits a response predictor.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal
from hashlib import sha256
from typing import ClassVar

import numpy as np

from empirical_lawhood.adapters.methods.matrix_factor_lifetime.records import FactorEventSpec, FactorRootRole, FactorTrace
from empirical_lawhood.adapters.methods.matrix_factor_lifetime.science import eligible_origins
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_decimal, validate_sha256, validate_stable_id

from .model import SixMatrixState, hermiticity_residual
from .shooting import hermitian_basis

PHASE_ORDER = ('POSITION', 'MOMENTUM')
SECTOR_ORDER = ('X', 'Y')
COMPONENT_ORDER = (0, 1, 2)
COORDINATE_ORDER = ('TRACE_I4_OVER_2', 'FACTOR_0', 'FACTOR_1', 'FACTOR_2')
RETAINED_SHAPE = (2, 2, 3, 4)
NATIVE_SHAPE = (2, 2, 3, 4, 4)


def _hermitian(value, shape):
    value = np.asarray(value)
    if (value.shape != shape or value.dtype != np.dtype('complex128')
            or not np.isfinite(value).all() or hermiticity_residual(value) > 1e-12):
        raise ValueError('factor bridge requires complete finite complex128 Hermitian operands')
    return value


def _real(value, shape):
    value = np.asarray(value)
    if value.shape != shape or value.dtype != np.dtype('float64') or not np.isfinite(value).all():
        raise ValueError('factor bridge requires complete finite float64 coordinates')
    return value


def _frozen(value):
    return np.frombuffer(np.ascontiguousarray(value).tobytes(), dtype=value.dtype).reshape(value.shape)


def factor_frame_sha256(frame):
    """Exact little-endian original frame bytes, with no normalization or refit."""
    frame = _hermitian(frame, (3, 4, 4))
    return sha256(np.ascontiguousarray(frame, dtype='<c16').tobytes()).hexdigest()


@dataclass(frozen=True, slots=True)
class FactorBridgeChart(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/simulators/six-matrix-response/factor-bridge-chart'
    chart_id: str
    root: FactorRootRole
    rule: ObjectIdentity
    frame_arrays: ArtifactIdentity
    clock: ObjectIdentity
    view: str
    observed_sector: str
    origin_tick: int
    origin_native_step: int
    cutoff: Decimal
    frame_sha256: str
    native_dimension: int = 192
    retained_dimension: int = 48
    phase_order: tuple[str, ...] = PHASE_ORDER
    sector_order: tuple[str, ...] = SECTOR_ORDER
    component_order: tuple[int, ...] = COMPONENT_ORDER
    coordinate_order: tuple[str, ...] = COORDINATE_ORDER
    normalization: str = 'REAL_HILBERT_SCHMIDT_ORTHONORMAL_TRACE_I4_OVER_2'
    frame_policy: str = 'ORIGIN_FIXED_NO_FUTURE_ALIGNMENT'
    retained_memory: str = 'ORIGIN_ONLY'

    def __post_init__(self):
        validate_stable_id(self.chart_id)
        self.root.__post_init__()
        self.rule.__post_init__()
        self.frame_arrays.__post_init__()
        self.clock.__post_init__()
        validate_sha256(self.frame_sha256)
        validate_decimal(self.cutoff, field_name='cutoff', minimum=Decimal(0))
        if (self.rule.object_schema != FactorEventSpec.SCHEMA or self.view not in ('PRIMARY', 'FINE')
                or self.observed_sector not in SECTOR_ORDER
                or type(self.origin_tick) is not int or self.origin_tick < 0
                or type(self.origin_native_step) is not int or self.origin_native_step < 0
                or (self.native_dimension, self.retained_dimension) != (192, 48)
                or (self.phase_order, self.sector_order, self.coordinate_order) != (PHASE_ORDER, SECTOR_ORDER, COORDINATE_ORDER)
                or self.component_order != COMPONENT_ORDER
                or self.normalization != 'REAL_HILBERT_SCHMIDT_ORTHONORMAL_TRACE_I4_OVER_2'
                or self.frame_policy != 'ORIGIN_FIXED_NO_FUTURE_ALIGNMENT'
                or self.retained_memory != 'ORIGIN_ONLY'):
            raise ValueError('factor bridge changes its source/frame/clock or complete chart convention')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.chart_id, self)


@dataclass(frozen=True, slots=True)
class FactorBridge:
    chart: FactorBridgeChart
    factor_frame: np.ndarray

    def __post_init__(self):
        self.chart.__post_init__()
        frame = _hermitian(self.factor_frame, (3, 4, 4))
        gram = np.einsum('iab,jab->ij', frame.conj(), frame)
        if (not np.allclose(gram, np.eye(3), atol=1e-12, rtol=0)
                or np.max(np.abs(np.trace(frame, axis1=-2, axis2=-1))) > 1e-12
                or factor_frame_sha256(frame) != self.chart.frame_sha256):
            raise ValueError('factor bridge frame is substituted, nonorthonormal or contains trace')
        object.__setattr__(self, 'factor_frame', _frozen(np.asarray(frame, dtype='<c16')))

    @property
    def axes(self):
        return _frozen(np.concatenate((np.eye(4, dtype='<c16')[None] / 2, self.factor_frame)))


def select_factor_bridge(*, chart_id, spec, trace, origin_tick, cutoff, clock,
                         origin_native_step, frame, expected_frame_sha256):
    """Join A's actual causal eligibility and selected aligned-frame artifact.

    The retained adapter must authenticate the frame bytes and clock/native-step
    mapping against the original source/view before calling this pure selector.
    Numerical frame selection uses the declared causal origin. The full A
    diagnostic artifact remains a custody reference; the forecasting process
    receives only this frozen chart/frame, without diagnostic bytes or labels.
    """
    if type(spec) is not FactorEventSpec or type(trace) is not FactorTrace:
        raise ValueError('factor bridge requires the declared A rule and complete retained trace')
    spec.__post_init__()
    trace.__post_init__()
    if (origin_tick not in eligible_origins(trace, spec) or trace.diagnostics is None
            or cutoff != spec.primary_dt * origin_tick or trace.rule != spec.identity):
        raise ValueError('unadmitted/unidentified factor or changed causal cutoff refuses bridge')
    observation = next(row for row in trace.observations if row.tick == origin_tick)
    if (observation.status != 'AVAILABLE' or observation.identifiable is not True
            or observation.raw_admitted is not True or observation.causal_admitted is not True
            or observation.alignment_ambiguous):
        raise ValueError('factor bridge requires an identified unambiguous admitted origin')
    chart = FactorBridgeChart(chart_id, trace.root, spec.identity, trace.diagnostics, clock,
        trace.view, trace.sector, origin_tick, origin_native_step, cutoff, expected_frame_sha256)
    return FactorBridge(chart, frame)


def _selected(bridge, chart):
    if type(bridge) is not FactorBridge or chart != bridge.chart.identity:
        raise ValueError('factor bridge substitutes its sealed source/frame/cutoff chart')


def _phase(state):
    if (type(state) is not SixMatrixState or state.q != 2 or not state.finite
            or type(state.step_index) is not int):
        raise ValueError('factor bridge requires a complete finite native q=2 state')
    return np.stack((state.positions, state.momenta))


def observe(bridge, state, *, chart):
    _selected(bridge, chart)
    phase = _phase(state)
    if state.step_index < bridge.chart.origin_native_step:
        raise ValueError('factor bridge observation precedes its selected origin')
    return _frozen(np.einsum('cab,psjab->psjc', bridge.axes.conj(), phase).real)


def lift(bridge, coordinates, *, chart):
    _selected(bridge, chart)
    coordinates = _real(coordinates, RETAINED_SHAPE)
    return _frozen(np.einsum('psjc,cab->psjab', coordinates, bridge.axes))


def native_coordinates(state):
    """All192 coordinates: phase, X/Y, component, historical16-axis HS basis."""
    return _frozen(np.einsum('kab,psjab->psjk', hermitian_basis(4).conj(), _phase(state)).real.reshape(192))


def decompose(bridge, state, *, chart):
    coordinates = observe(bridge, state, chart=chart)
    retained = lift(bridge, coordinates, chart=chart)
    return coordinates, retained, _frozen(_phase(state) - retained)


def factor_force(bridge, coefficients, *, chart, kind):
    """Lift a declared force on both sectors; trace control stays distinct."""
    _selected(bridge, chart)
    coefficients = _real(coefficients, (2, 3, 4))
    if (kind not in ('FACTOR', 'TRACE')
            or kind == 'FACTOR' and np.any(coefficients[..., 0] != 0)
            or kind == 'TRACE' and np.any(coefficients[..., 1:] != 0)):
        raise ValueError('factor and trace force roles must remain separate')
    return _frozen(np.einsum('sjc,cab->sjab', coefficients, bridge.axes))


def norm_matched_complement_force(bridge, candidate, *, chart, norm):
    _selected(bridge, chart)
    candidate = _hermitian(candidate, (2, 3, 4, 4))
    if not np.isfinite(norm) or norm <= 0:
        raise ValueError('complement force requires explicit positive finite matched norm')
    projected = np.einsum('sjc,cab->sjab',
        np.einsum('cab,sjab->sjc', bridge.axes.conj(), candidate).real, bridge.axes)
    complement = candidate - projected
    length = float(np.linalg.norm(complement))
    if length <= 32 * np.finfo(float).eps * float(np.linalg.norm(candidate)):
        raise ValueError('candidate has no resolved orthogonal-complement force')
    return _frozen(complement * (norm / length))


def momentum_kick(bridge, state, direction, *, chart, duration, amplitude):
    """Pure full-state force kick; a coupled two-kick native branch is separate."""
    _selected(bridge, chart)
    _phase(state)
    if state.step_index < bridge.chart.origin_native_step:
        raise ValueError('factor bridge force precedes its selected origin')
    direction = _hermitian(direction, (2, 3, 4, 4))
    if not np.isfinite(duration) or duration < 0 or not np.isfinite(amplitude):
        raise ValueError('factor force duration/amplitude must be finite and explicit')
    return replace(state, momenta=state.momenta + duration * amplitude * direction)


def readout(bridge, state, receiver, *, chart):
    """Same origin-fixed native dual target for every future predictor."""
    receiver = _real(receiver, RETAINED_SHAPE)
    return float(np.vdot(receiver, observe(bridge, state, chart=chart)).real)
