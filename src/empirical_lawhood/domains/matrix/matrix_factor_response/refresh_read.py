# SPDX-License-Identifier: MPL-2.0
"""Independent affine-map falsifier and method assessment for retained SCI01.

This reader never calls the continuation producer. It reconstructs the complete
discrete map, including its forced first/last kicks, from authenticated operands.
"""

from decimal import Decimal
from math import fsum, sqrt
from types import SimpleNamespace

import numpy as np

from empirical_lawhood.domains.matrix.six_matrix_response.gradients import SixMatrixParameters
from empirical_lawhood.domains.matrix.six_matrix_response.parameter_derivatives import hessian_image
from empirical_lawhood.domains.matrix.six_matrix_response.shooting import hermitian_basis

from empirical_lawhood.domains.matrix.matrix_factor_response.mechanism_readout import hold_tangent_response, input_krylov_basis
from empirical_lawhood.domains.matrix.matrix_factor_response.refresh_records import REFRESH_METHODS, REFRESH_RULE, MatrixRefreshCaseAssessment, MatrixRefreshMethodAssessment, refresh_array_names
from empirical_lawhood.domains.matrix.matrix_factor_response.response_scoring import DENSE_RESPONSE_HORIZONS, nominal_actuator_scales
from empirical_lawhood.domains.matrix.matrix_factor_response.science import _block_modes, frame_axes, native_position_coordinates, native_position_lift, origin_io_system


def affine_response(origin, refresh, basis, forces, *, timestep, friction):
    """Independently composed full-step equations; return all native-clock states."""
    return affine_response_window(origin, refresh, basis, forces, timestep=timestep,
        friction=friction, primary_horizon=128, pulse_ticks=16, refresh_tick=32)


def affine_response_window(origin, refresh, basis, forces, *, timestep, friction,
                           primary_horizon, pulse_ticks, refresh_tick):
    """Independent affine-map equations with an explicit successor clock."""
    if (type(timestep) is not Decimal or timestep not in (Decimal('.001'), Decimal('.0005'))
            or any(type(v) is not int for v in (primary_horizon, pulse_ticks, refresh_tick))
            or not 1 <= pulse_ticks <= refresh_tick <= primary_horizon <= 128):
        raise ValueError('independent response reader changes its declared clock')
    dt = float(timestep)
    mult = 1 if timestep == Decimal('.001') else 2
    count = primary_horizon * mult
    half = dt / 2
    decay = np.exp(-float(friction * timestep))
    drift = half * (1 + decay)
    identity = np.eye(basis.shape[1])
    force = basis.T @ forces
    maps = []
    for operator in (origin, refresh):
        reduced = basis.T @ operator @ basis
        qq, qp = identity - drift * half * reduced, drift * identity
        transition = np.block([[qq, qp], [-half * (decay * reduced + reduced @ qq),
                                          decay * identity - half * reduced @ qp]])
        bq = drift * half * force
        drive = np.concatenate((bq, drift * force - half * reduced @ bq), axis=0)
        maps.append((transition, drive))
    state = np.zeros((2 * len(identity), 4))
    states = [state.T.copy()]
    for tick in range(1, count + 1):
        transition, drive = maps[tick > refresh_tick * mult]
        state = transition @ state + (drive if tick <= pulse_ticks * mult else 0.)
        states.append(state.T.copy())
    return np.transpose(states, (1, 0, 2))


def _same(actual, expected, label):
    if actual.dtype != expected.dtype or actual.shape != expected.shape or not np.array_equal(actual, expected):
        raise ValueError('SCI01 independent reader changes original ' + label)


def _close(actual, expected, label, checks, *, scale=1.):
    if actual.shape != expected.shape or not np.isfinite(actual).all() or not np.isfinite(expected).all():
        raise ValueError('SCI01 independent reader loses finite complete ' + label)
    residual = float(np.max(np.abs((actual - expected) / scale)))
    checks[label] = max(checks.get(label, 0.), residual)
    if residual > float(REFRESH_RULE.reconstruction_tolerance):
        raise ValueError('SCI01 independent equation failed: ' + label)


def _phase_map(basis):
    zero = np.zeros_like(basis)
    return np.block([[basis, zero], [zero, basis]])


def verify_refresh_case(protocol, causal, frozen, received, arrays, original_case):
    """Authenticate every retained trajectory and signed component against its inputs."""
    if original_case.original_availability != 'FINITE':
        raise ValueError('SCI01 numerical reader cannot manufacture a missing origin')
    if tuple(sorted(arrays)) != refresh_array_names():
        raise ValueError('SCI01 changes its complete retained array census')
    checks = {}
    _same(arrays['forces'], frozen['forces'], 'physical force')
    _same(arrays['receivers'], frozen['receivers'], 'physical receiver')
    h_basis = hermitian_basis(4)
    receiver = np.einsum('kab,rpsjab->rpsjk', h_basis.conj(), frozen['receivers']).real.reshape(48, 192)
    force = np.stack([native_position_coordinates(f) * float(action.amplitude)
        for f, action in zip(frozen['forces'], protocol.actions, strict=True)], axis=1)
    scales = np.asarray([[tuple(map(float, nominal_actuator_scales(action,
        protocol.public_source.coordinate.primary_view.timestep, tick))) for tick in range(1, 129)]
        for action in protocol.actions])
    _same(arrays['scales'], scales, 'original actuator scales')
    member = protocol.public_source.coordinate.member
    factor = _block_modes([frame_axes(causal['frame'])] * 6)
    for view, mult in (('primary', 1), ('fine', 2)):
        numerical = getattr(protocol.public_source.coordinate, view + '_view')
        h0 = frozen[view + '_hessian']
        _same(arrays[view + '.h0'], h0, 'origin operator')
        ticks = np.asarray((0, 32, 64, 128), dtype='<i8') * mult
        _same(arrays[view + '.state_ticks'], ticks, 'saved model clocks')
        design = SimpleNamespace(view=numerical, horizon_steps=tuple(range(1, 128 * mult + 1)))
        actions = tuple(SimpleNamespace(amplitude=a.amplitude, force_norm=a.force_norm, pulse_steps=16 * mult)
                        for a in protocol.actions)
        system = origin_io_system(design, h0, frozen['forces'], frozen['receivers'], actions)
        krylov, _ = input_krylov_basis(system[0], system[1], frozen[view + '_hessian_spectrum'],
            frozen[view + '_hessian_eigenvectors'], native_horizon=128 * mult)
        bases = {'FULL': np.eye(96), 'INPUT_KRYLOV48': krylov, 'FACTOR': factor}
        forecast = {}
        # A fixed origin H is the independent frozen control, without a special continuation path.
        for method, basis in bases.items():
            _same(arrays[view + '.basis.' + method.lower()], basis, 'fixed ' + method + ' basis')
            states = affine_response(h0, h0, basis, force, timestep=numerical.timestep, friction=numerical.friction_gamma)
            _close(arrays[view + '.state.' + method.lower()], states[:, ticks], 'own_state.' + method, checks,
                scale=float(nominal_actuator_scales(protocol.actions[0], numerical.timestep, 16 * mult)[0]))
            expected = states[:, mult::mult] @ _phase_map(basis).T @ receiver.T
            _close(arrays[view + '.prediction.' + method.lower()], expected, 'origin_forecast.' + method,
                checks, scale=np.repeat(scales, 24, axis=-1))
            original = {'FULL': 'full_coupled', 'FACTOR': 'factor'}.get(method)
            if original:
                _close(expected, frozen[view + '_full_grid_' + original], 'original_forecast.' + method,
                    checks, scale=np.repeat(scales, 24, axis=-1))
            forecast[method] = expected
        for pi, panel in enumerate(original_case.panel_ids):
            prefix = f'{view}.p{pi}'
            reference = f'branch.{view}.{panel}.{protocol.actions[0].action_id}.hold.'
            positions = received[reference + 'positions']
            alphas = received[reference + 'alpha_tilde']
            clock = np.arange(mult * protocol.public_source.policy.cutoff_tick,
                mult * protocol.public_source.policy.cutoff_tick + 128 * mult + 1, dtype='<i8')
            _same(received[reference + 'ticks'], clock, 'absolute response clock')
            _same(alphas, np.broadcast_to(alphas[0], alphas.shape), 'fixed response parameters')
            _same(arrays[prefix + '.checkpoint.position'], positions[32 * mult], 'own-panel checkpoint')
            _same(arrays[prefix + '.checkpoint.alpha'], alphas[32 * mult], 'checkpoint parameters')
            par = SixMatrixParameters(2, float(member.mass_x), float(member.mass_y),
                float(member.cross_coupling_gamma), *map(float, alphas[32 * mult]))
            # The source-owned HVP acts on each physical coordinate. No later state enters this operator.
            columns = np.stack([native_position_coordinates(hessian_image(positions[32 * mult],
                native_position_lift(direction), par)) for direction in np.eye(96)], axis=1)
            h32 = (columns + columns.T) / 2
            _close(arrays[prefix + '.h32'], h32, 'source_checkpoint_operator', checks, scale=max(1., np.linalg.norm(h32)))
            for method in ('FULL', 'INPUT_KRYLOV48'):
                basis = bases[method]
                states = affine_response(h0, h32, basis, force, timestep=numerical.timestep, friction=numerical.friction_gamma)
                name = method + '_REFRESH32'
                _close(arrays[prefix + '.state.' + name.lower()], states[:, ticks], 'own_state.' + name, checks,
                    scale=float(nominal_actuator_scales(protocol.actions[0], numerical.timestep, 16 * mult)[0]))
                _same(arrays[prefix + '.state.' + name.lower()][:, :2], arrays[view + '.state.' + method.lower()][:, :2],
                    'completed checkpoint state without reset')
                forecast[name] = states[:, mult::mult] @ _phase_map(basis).T @ receiver.T
                _close(arrays[prefix + '.prediction.' + name.lower()], forecast[name], 'continued_forecast.' + name,
                    checks, scale=np.repeat(scales, 24, axis=-1))
            native, endpoints = [], []
            for action in protocol.actions:
                stem = f'branch.{view}.{panel}.{action.action_id}.'
                for name in ('positions', 'momenta'):
                    _same(received[stem + 'hold.' + name], received[reference + name], 'shared HOLD ' + name)
                    for sign in ('plus', 'minus'):
                        _same(received[stem + sign + '.' + name][0], received[reference + name][0], 'signed origin ' + name)
                for sign in ('plus', 'minus', 'hold'):
                    for name in ('ticks', 'alpha_tilde', 'innovations'):
                        _same(received[stem + sign + '.' + name], received[reference + name], 'panel ' + name)
                q = (received[stem + 'plus.positions'] - received[stem + 'minus.positions']) / 2
                p = (received[stem + 'plus.momenta'] - received[stem + 'minus.momenta']) / 2
                # Evaluate q and p independently before their fixed receiver sum.
                native.append((np.einsum('rsjab,tsjab->tr', frozen['receivers'][:, 0].conj(), q)
                    + np.einsum('rsjab,tsjab->tr', frozen['receivers'][:, 1].conj(), p)).real[mult::mult])
                endpoints.append(np.concatenate([np.einsum('kab,tsjab->tsjk', h_basis.conj(), phase).real.reshape(2, 96)
                    for phase in (q[np.array((64, 128)) * mult], p[np.array((64, 128)) * mult])], axis=1))
            native = np.asarray(native)
            _close(arrays[prefix + '.native'], native, 'native_receiver', checks, scale=np.repeat(scales, 24, axis=-1))
            _same(arrays[prefix + '.native.phase.endpoints'], np.asarray(endpoints), 'raw native endpoints')
            hold = hold_tangent_response(positions, alphas, frozen['forces'], frozen['receivers'],
                member=member, numerical_view=numerical, pulse_steps=16 * mult)[:, mult - 1::mult]
            _same(arrays[prefix + '.hold'], hold, 'accepted evaluator-only HOLD tangent')
            _close(arrays[prefix + '.signal'], np.linalg.norm(native.reshape(4, 128, 2, 24), axis=-1) / scales,
                'native_signal', checks)
            for method in REFRESH_METHODS:
                error = (native - forecast[method]).reshape(4, 128, 2, 24) / scales[..., None]
                _close(arrays[prefix + '.error.' + method.lower()], error, 'signed_error.' + method, checks)
                # Independent accurate scalar sums, rather than the producer's vectorized norm.
                norms = np.asarray([sqrt(fsum(float(x) ** 2 for x in vector))
                    for vector in error.reshape(-1, 24)]).reshape(4, 128, 2)
                _close(arrays[prefix + '.error_norm.' + method.lower()], norms, 'error_norm.' + method, checks)
                if method not in ('FACTOR', 'INPUT_KRYLOV48', 'INPUT_KRYLOV48_REFRESH32'):
                    continue
                full = forecast['FULL_REFRESH32' if method.endswith('_REFRESH32') else 'FULL']
                terms = np.stack((native - hold, hold - full, full - forecast[method])).reshape(3, 4, 128, 2, 24) / scales[None, ..., None]
                _close(arrays[prefix + '.signed.' + method.lower()], terms, 'signed_terms.' + method, checks)
                squares = np.einsum('katbr,katbr->katb', terms, terms)
                crosses = np.asarray([2 * np.einsum('atbr,atbr->atb', terms[i], terms[j]) for i, j in ((0, 1), (0, 2), (1, 2))])
                _close(arrays[prefix + '.squares.' + method.lower()], squares, 'squares.' + method, checks)
                _close(arrays[prefix + '.cross.' + method.lower()], crosses, 'cross.' + method, checks)
                _close(np.sum(terms, axis=0), error, 'vector_identity.' + method, checks)
                _close(np.sum(squares + crosses, axis=0), norms ** 2, 'squared_identity.' + method, checks)
    return checks


def assess_refresh_case(original_case, arrays):
    """Recalculate the independent decision from complete signed response errors."""
    methods = []
    for method in REFRESH_METHODS:
        curves = []
        for view in ('primary', 'fine'):
            maximum, curve = Decimal(0), []
            for tick in DENSE_RESPONSE_HORIZONS:
                for pi in range(2):
                    for ai in range(4):
                        for block in range(2):
                            vector = arrays[f'{view}.p{pi}.error.{method.lower()}'][ai, tick - 1, block]
                            norm = Decimal(repr(sqrt(fsum(float(x) ** 2 for x in vector))))
                            maximum = max(maximum, norm)
                curve.append(maximum)
            curves.append(tuple(curve))
        methods.append(MatrixRefreshMethodAssessment(method, *curves, original_case.numerical_usable))
    return MatrixRefreshCaseAssessment(original_case, tuple(methods))
