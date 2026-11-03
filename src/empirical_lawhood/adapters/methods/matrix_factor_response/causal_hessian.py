# SPDX-License-Identifier: MPL-2.0
"""Past-Hessian block/mixing features with the actual two-kick BAOAB timing.

Only past configurations, the handoff assay and the received origin instrument
enter this owner. No function accepts a future path, response or noise array.
The spectral split uses full current cluster subspaces, never matched modes.
"""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from typing import ClassVar

import numpy as np

from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_decimal

from .curve_contract import MECHANISM_FEATURES
from .response_scoring import DENSE_RESPONSE_HORIZONS, nominal_actuator_scales


@dataclass(frozen=True, slots=True)
class CausalHessianRule(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-experiment/causal-past-hessian-rule'
    window_primary_ticks: int = 32
    elapsed_time: Decimal = Decimal('.032')
    cluster_relative_gap: Decimal = Decimal('1e-10')
    witness_relative_tolerance: Decimal = Decimal('1e-10')
    hessian_owner: str = 'six-matrix-q2.parameter-native-derivatives.v1'
    parameter_rule: str = 'HANDOFF_ASSAY_PARAMETERS_AT_BOTH_PAST_ENDPOINTS'
    symmetrization: str = 'HALF_H_PLUS_TRANSPOSE_REAL_HERMITIAN_COORDINATES'
    cluster_rule: str = 'SIGNED_ASCENDING_ADJACENT_GAPS_LE_THRESHOLD_TRANSITIVE_FULL_PROJECTORS'
    kick_rule: str = 'FIRST_AT_J_DT_LAST_AT_J_PLUS_ONE_DT_INCLUDING_DRIVEN_LAST_KICK'
    aggregation: str = 'LOG1P_MAX_FOUR_ACTIONS_Q_P_ORIGINAL_29_HORIZONS'
    missing_rule: str = 'NO_WINDOW_SUBSTITUTION_PRIMARY_UNAVAILABLE_FINE_DIAGNOSTIC_ONLY'

    def __post_init__(self):
        if (type(self.window_primary_ticks) is not int or self.window_primary_ticks != 32
                or any(type(value) is not Decimal for value in (self.elapsed_time,
                    self.cluster_relative_gap, self.witness_relative_tolerance))
                or (self.elapsed_time, self.cluster_relative_gap, self.witness_relative_tolerance)
                    != (Decimal('.032'), Decimal('1e-10'), Decimal('1e-10'))
                or self.hessian_owner != 'six-matrix-q2.parameter-native-derivatives.v1'
                or self.parameter_rule != 'HANDOFF_ASSAY_PARAMETERS_AT_BOTH_PAST_ENDPOINTS'
                or self.symmetrization != 'HALF_H_PLUS_TRANSPOSE_REAL_HERMITIAN_COORDINATES'
                or self.cluster_rule != 'SIGNED_ASCENDING_ADJACENT_GAPS_LE_THRESHOLD_TRANSITIVE_FULL_PROJECTORS'
                or self.kick_rule != 'FIRST_AT_J_DT_LAST_AT_J_PLUS_ONE_DT_INCLUDING_DRIVEN_LAST_KICK'
                or self.aggregation != 'LOG1P_MAX_FOUR_ACTIONS_Q_P_ORIGINAL_29_HORIZONS'
                or self.missing_rule != 'NO_WINDOW_SUBSTITUTION_PRIMARY_UNAVAILABLE_FINE_DIAGNOSTIC_ONLY'):
            raise ValueError('causal Hessian features change their prospective source, clock, spectral or timing rule')


CAUSAL_HESSIAN_RULE = CausalHessianRule()


class HessianFeatureUnavailable(ValueError):
    """A declared numerical or past-observation prerequisite is unavailable."""


def _symmetric(value, name):
    value = np.asarray(value)
    if (value.dtype != np.dtype('float64') or value.ndim != 2 or value.shape[0] != value.shape[1]
            or not 1 <= len(value) <= 96 or not np.isfinite(value).all()
            or not np.allclose(value, value.T, rtol=0, atol=1e-12)):
        raise ValueError(name + ' requires a finite real symmetric position operator')
    return value


def current_eigenspace_split(hessian, difference, *, eigensystem=None):
    """Use a received signed eigensystem or construct it once; return full blocks."""
    hessian, difference = _symmetric(hessian, 'current Hessian'), _symmetric(difference, 'Hessian difference')
    if hessian.shape != difference.shape:
        raise ValueError('past Hessian difference changes the fixed Hermitian coordinates')
    try:
        values, vectors = np.linalg.eigh(hessian) if eigensystem is None else eigensystem
    except np.linalg.LinAlgError as error:
        raise HessianFeatureUnavailable('CURRENT_HESSIAN_EIGENSOLVE_FAILED') from error
    n = len(hessian)
    if (values.shape != (n,) or vectors.shape != (n, n) or values.dtype != np.dtype('float64')
            or vectors.dtype != np.dtype('float64') or not np.isfinite(values).all()
            or not np.isfinite(vectors).all() or np.any(np.diff(values) < 0)):
        raise ValueError('current Hessian split requires all signed sorted real eigenpairs')
    scale = max(1., float(np.max(np.abs(values))))
    tolerance = float(CAUSAL_HESSIAN_RULE.witness_relative_tolerance)
    if (np.linalg.norm(hessian @ vectors - vectors * values[None, :], ord=2) > tolerance * scale
            or np.linalg.norm(vectors.T @ vectors - np.eye(n), ord=2) > tolerance):
        raise ValueError('current Hessian split loses its complete spectral witness')
    boundaries = (0, *(int(index + 1) for index in np.flatnonzero(
        np.diff(values) > float(CAUSAL_HESSIAN_RULE.cluster_relative_gap) * scale)), n)
    clusters = tuple(zip(boundaries[:-1], boundaries[1:], strict=True))
    block = np.zeros_like(difference)
    for first, last in clusters:
        basis = vectors[:, first:last]
        block += basis @ (basis.T @ difference @ basis) @ basis.T
    block = (block + block.T) / 2
    return block, difference - block, clusters


def origin_trend_first_variation(hessian, difference, force_inputs, receiver_map, *,
        timestep, decay, pulse_steps, horizons):
    """Derivative at zero of H(s)=H0+eta*s*D, including the forced input map.

    The frozen response and its first variation are advanced through the same
    B-A-O-A-B stages. Force_inputs already includes the original amplitudes.
    """
    hessian, difference = _symmetric(hessian, 'current Hessian'), _symmetric(difference, 'Hessian trend')
    n = len(hessian)
    if (hessian.shape != difference.shape or force_inputs.ndim != 2 or force_inputs.shape[0] != n
            or not force_inputs.shape[1] or receiver_map.ndim != 2 or receiver_map.shape[1] != 2 * n
            or not np.isfinite(force_inputs).all() or not np.isfinite(receiver_map).all()
            or not np.isfinite(timestep) or timestep <= 0 or not np.isfinite(decay) or not 0 < decay <= 1
            or type(pulse_steps) is not int or pulse_steps < 1 or type(horizons) is not tuple or not horizons
            or horizons != tuple(sorted(set(horizons)))
            or any(type(tick) is not int or not 1 <= tick <= 256 for tick in horizons)):
        raise ValueError('causal trend changes its frozen origin instrument or physical BAOAB clock')
    q = np.zeros_like(force_inputs, dtype=np.float64)
    p, dq, dp = q.copy(), q.copy(), q.copy()
    half = timestep / 2
    outputs = []
    with np.errstate(over='ignore', invalid='ignore'):
        for tick in range(1, horizons[-1] + 1):
            kick = half * force_inputs if tick <= pulse_steps else 0.
            dp -= half * (hessian @ dq + ((tick - 1) * timestep) * (difference @ q))
            p += kick - half * (hessian @ q)
            dq += half * dp
            q += half * p
            dp *= decay
            p *= decay
            dq += half * dp
            q += half * p
            dp -= half * (hessian @ dq + (tick * timestep) * (difference @ q))
            p += kick - half * (hessian @ q)
            if tick in horizons:
                outputs.append((receiver_map @ np.concatenate((dq, dp))).T)
    result = np.transpose(np.asarray(outputs), (1, 0, 2))
    if not np.isfinite(result).all():
        raise HessianFeatureUnavailable('NONFINITE_ORIGIN_HESSIAN_TREND_RESPONSE')
    return result


@dataclass(frozen=True, slots=True)
class CausalHessianView(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-experiment/causal-past-hessian-view'
    view: str
    values: tuple[tuple[str, Decimal], ...]
    clusters: tuple[tuple[int, int], ...]
    reasons: tuple[str, ...]

    def __post_init__(self):
        if (self.view not in ('PRIMARY', 'FINE') or type(self.values) is not tuple or type(self.clusters) is not tuple
                or type(self.reasons) is not tuple or self.reasons != tuple(sorted(set(self.reasons)))):
            raise ValueError('causal Hessian view changes its numerical diagnostic census')
        if self.reasons:
            if self.values or self.clusters:
                raise ValueError('unavailable causal Hessian view invents finite predictors')
            return
        if (tuple(name for name, _ in self.values) != MECHANISM_FEATURES or not self.clusters
                or self.clusters[0][0] != 0 or self.clusters[-1][1] != 96
                or any(type(first) is not int or type(last) is not int or not 0 <= first < last <= 96
                    for first, last in self.clusters)
                or any(left[1] != right[0] for left, right in zip(self.clusters[:-1], self.clusters[1:], strict=True))):
            raise ValueError('causal Hessian view drops a descriptor or current eigenspace')
        for _, value in self.values:
            validate_decimal(value, field_name='causal Hessian trend feature', minimum=Decimal(0))


def causal_hessian_features(protocol, causal_arrays, frozen_arrays, *, include_fine=True):
    """The enclosing feature task authenticates these original received arrays."""
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_forecast import _hessian
    from empirical_lawhood.adapters.simulators.six_matrix_response.shooting import hermitian_basis
    from .science import native_position_coordinates

    public = protocol.public_source
    cutoff = public.policy.cutoff_tick
    if (type(include_fine) is not bool or protocol.horizon_steps != DENSE_RESPONSE_HORIZONS or protocol.receiver_count != 48
            or public.coordinate.primary_view.timestep != Decimal('.001')
            or public.coordinate.fine_view.timestep != Decimal('.0005')
            or len(protocol.actions) != 4 or any(action.pulse_steps != 16 or action.amplitude != Decimal('.01')
                for action in protocol.actions)):
        raise ValueError('causal Hessian features change their original paired-clock task')
    if any('innovation' in name or 'hold' in name.lower() or 'future' in name.lower() for name in causal_arrays):
        raise ValueError('causal Hessian features refuse future paths and noise')
    result = []
    for view, multiplier in ((('primary', 1), ('fine', 2)) if include_fine else (('primary', 1),)):
        ticks = causal_arrays[view + '_ticks']
        if (ticks.ndim != 1 or not len(ticks) or np.any(np.diff(ticks) <= 0)
                or ticks[-1] != multiplier * cutoff or np.any(ticks > multiplier * cutoff)):
            raise ValueError('causal Hessian features require exact past-only cutoff clocks')
        before = np.flatnonzero(ticks == multiplier * (cutoff - 32))
        if cutoff < 32 or len(before) != 1:
            result.append(CausalHessianView(view.upper(), (), (), ('MISSING_FIXED_032_PAST_OBSERVATION',)))
            continue
        if view + '_hessian' not in frozen_arrays:
            result.append(CausalHessianView(view.upper(), (), (), ('MISSING_ORIGIN_INSTRUMENT',)))
            continue
        past = causal_arrays[view + '_positions'][int(before[0])]
        alpha = causal_arrays[view + '_alpha_tilde'][-1]
        hessian = frozen_arrays[view + '_hessian']
        try:
            with np.errstate(over='ignore', invalid='ignore'):
                previous = _hessian(protocol, past, alpha)
                difference = (hessian - previous) / float(CAUSAL_HESSIAN_RULE.elapsed_time)
            if not np.isfinite(difference).all():
                raise HessianFeatureUnavailable('NONFINITE_PAST_HESSIAN_DIFFERENCE')
            block, mixing, clusters = current_eigenspace_split(hessian, difference,
                eigensystem=(frozen_arrays[view + '_hessian_spectrum'], frozen_arrays[view + '_hessian_eigenvectors']))
        except (HessianFeatureUnavailable, np.linalg.LinAlgError) as error:
            reason = str(error) if isinstance(error, HessianFeatureUnavailable) else 'CURRENT_HESSIAN_SPECTRAL_CHECK_FAILED'
            result.append(CausalHessianView(view.upper(), (), (), (reason,)))
            continue
        forces = np.stack([native_position_coordinates(force) * float(action.amplitude)
            for force, action in zip(frozen_arrays['forces'], protocol.actions, strict=True)], axis=1)
        receiver_map = np.einsum('kab,rpsjab->rpsjk', hermitian_basis(4).conj(),
            frozen_arrays['receivers']).real.reshape(48, 192)
        numerical = public.coordinate.primary_view if multiplier == 1 else public.coordinate.fine_view
        values = []
        try:
            for name, component in zip(MECHANISM_FEATURES, (block, mixing), strict=True):
                correction = origin_trend_first_variation(hessian, component, forces, receiver_map,
                    timestep=float(numerical.timestep), decay=np.exp(-float(numerical.friction_gamma * numerical.timestep)),
                    pulse_steps=16 * multiplier, horizons=tuple(tick * multiplier for tick in DENSE_RESPONSE_HORIZONS))
                maximum = 0.
                for action_index, action in enumerate(protocol.actions):
                    for horizon_index, horizon in enumerate(DENSE_RESPONSE_HORIZONS):
                        scales = nominal_actuator_scales(action, public.coordinate.primary_view.timestep, horizon)
                        maximum = max(maximum, *(float(np.linalg.norm(correction[action_index, horizon_index,
                            block_index * 24:(block_index + 1) * 24])) / float(scale)
                            for block_index, scale in enumerate(scales)))
                with localcontext() as context:
                    context.prec = 60
                    context.rounding = ROUND_HALF_EVEN
                    values.append((name, (Decimal(1) + Decimal(repr(maximum))).ln()))
        except HessianFeatureUnavailable as error:
            result.append(CausalHessianView(view.upper(), (), (), (str(error),)))
        else:
            result.append(CausalHessianView(view.upper(), tuple(values), clusters, ()))
    return tuple(result)
