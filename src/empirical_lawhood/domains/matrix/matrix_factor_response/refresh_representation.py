# SPDX-License-Identifier: MPL-2.0
"""Exact discrete variation-of-constants accounting on retained SCI01 states.

The basis and states are supplied by the closed calculation. No basis is built,
no observation is added and no native trajectory is acquired here.
"""

from math import fsum

import numpy as np

from empirical_lawhood.domains.matrix.matrix_factor_response.origin_mechanics import discrete_baoab_maps
from empirical_lawhood.domains.matrix.matrix_factor_response.refresh_science import lift_states, receiver_matrix


def phase_lift(basis):
    zero = np.zeros_like(basis)
    return np.block([[basis, zero], [zero, basis]])


def _step(states, hessian, dt, decay):
    """Independent unforced two-kick implementation for the reconstruction check."""
    n = len(hessian)
    q, p = states[:, :n].copy(), states[:, n:].copy()
    p -= dt / 2 * (q @ hessian.T)
    q += dt / 2 * p
    p *= decay
    q += dt / 2 * p
    p -= dt / 2 * (q @ hessian.T)
    return np.concatenate((q, p), axis=1)


def representation_terms(hessian, basis, full_checkpoint, reduced_checkpoint, *, timestep, friction, steps):
    """Return inherited and generated physical vectors, plus independent checks.

    Row batches implement I[j+1] = M I[j] and
    G[j+1] = M G[j] + (M L - L R) z[j], with G[0] = 0.
    R is composed AFTER projecting H, never L.T M L.
    """
    dt, decay = float(timestep), np.exp(-float(timestep * friction))
    reduced_hessian = basis.T @ hessian @ basis
    full_map, _ = discrete_baoab_maps(hessian, np.zeros((len(hessian), 1)), timestep=dt, decay=decay)
    reduced_map, _ = discrete_baoab_maps(reduced_hessian, np.zeros((basis.shape[1], 1)), timestep=dt, decay=decay)
    lift = phase_lift(basis)
    if (not isinstance(steps, int) or steps < 1 or steps > 256
            or full_checkpoint.ndim != 2 or reduced_checkpoint.ndim != 2
            or full_checkpoint.shape != (len(reduced_checkpoint), len(full_map))
            or reduced_checkpoint.shape[1] != len(reduced_map)
            or not np.isfinite(full_checkpoint).all() or not np.isfinite(reduced_checkpoint).all()
            or np.linalg.norm(basis.T @ basis - np.eye(basis.shape[1])) > 1e-10):
        raise ValueError('Representation accounting requires finite matched retained states and a fixed orthonormal basis')
    defect = full_map @ lift - lift @ reduced_map
    initial = full_checkpoint - reduced_checkpoint @ lift.T
    inherited, generated = initial.copy(), np.zeros_like(initial)
    reduced, full_direct, reduced_direct = reduced_checkpoint.copy(), full_checkpoint.copy(), reduced_checkpoint.copy()
    records, residuals = [], []
    for tick in range(steps + 1):
        direct = full_direct - reduced_direct @ lift.T
        residuals.append(float(np.max(np.abs(inherited + generated - direct))))
        records.append((inherited.copy(), generated.copy(), full_direct.copy(), reduced_direct.copy()))
        if tick < steps:
            inherited = inherited @ full_map.T
            generated = generated @ full_map.T + reduced @ defect.T
            reduced = reduced @ reduced_map.T
            full_direct = _step(full_direct, hessian, dt, decay)
            reduced_direct = _step(reduced_direct, reduced_hessian, dt, decay)
    if not all(np.isfinite(value).all() for record in records for value in record):
        raise ValueError('Nonfinite post-checkpoint representation accounting')
    return {'M': full_map, 'R': reduced_map, 'L': lift, 'defect': defect, 'd_checkpoint': initial,
            'records': records, 'maximum_direct_identity_residual': max(residuals),
            'projected_full_map_difference_norm': float(np.linalg.norm(lift.T @ full_map @ lift - reduced_map))}


def case_representation(protocol, source, arrays):
    """Use both retained views and panels; frozen control and actual refresh share d_tau."""
    results, exports, checks = {}, {}, []
    for view, multiplier in (('primary', 1), ('fine', 2)):
        numerical = getattr(protocol.public_source.coordinate, view + '_view')
        basis = arrays[view + '.basis.input_krylov48']
        for pi in range(2):
            prefix = f'{view}.p{pi}'
            for regime in ('FROZEN', 'REFRESH32'):
                suffix = '_refresh32' if regime == 'REFRESH32' else ''
                stem = prefix if suffix else view
                full = arrays[stem + '.state.full' + suffix]
                reduced = arrays[stem + '.state.input_krylov48' + suffix]
                expected_ticks = np.asarray((0, 32, 64, 128)) * multiplier
                if not np.array_equal(arrays[view + '.state_ticks'], expected_ticks):
                    raise ValueError('Representation accounting changes the retained checkpoint clocks')
                for state, kind in ((full, 'full'), (reduced, 'input_krylov48')):
                    if not np.array_equal(state[:, 1], arrays[view + '.state.' + kind][:, 1]):
                        raise ValueError('Representation accounting resets the model checkpoint')
                operator = arrays[prefix + '.h32'] if suffix else arrays[view + '.h0']
                result = representation_terms(operator, basis, full[:, 1], reduced[:, 1],
                    timestep=numerical.timestep, friction=numerical.friction_gamma, steps=96 * multiplier)
                position_scale = float(arrays['scales'][0, 31, 0])
                maximum = result['maximum_direct_identity_residual'] / position_scale
                key = f'{prefix}.{regime.lower()}'
                for name in ('M', 'R', 'L', 'defect', 'd_checkpoint'):
                    exports[key + '.' + name.lower()] = result[name]
                for hi, horizon in enumerate((64, 128)):
                    inherited, generated, full_direct, reduced_direct = result['records'][(horizon - 32) * multiplier]
                    scale = np.repeat(arrays['scales'][:, horizon - 1], 96, axis=-1)
                    for actual, expected in ((full_direct, full[:, hi + 2]),
                            (lift_states(reduced_direct, basis), lift_states(reduced[:, hi + 2], basis))):
                        maximum = max(maximum, float(np.max(np.abs((actual - expected) / scale))))
                    direct = full[:, hi + 2] - lift_states(reduced[:, hi + 2], basis)
                    maximum = max(maximum, float(np.max(np.abs((inherited + generated - direct) / scale))))
                    results[(view, pi, regime, horizon)] = (inherited, generated, direct)
                    for name, value in zip(('inherited', 'generated', 'direct'), results[(view, pi, regime, horizon)], strict=True):
                        exports[f'{key}.h{horizon}.{name}'] = value
                if maximum > 1e-10:
                    raise ValueError('Retained post-checkpoint states fail independent representation reconstruction')
                checks.append({'case_index': source.case_index, 'view': view, 'panel_id': source.panel_ids[pi],
                    'regime': regime, 'maximum_normalized_residual': maximum,
                    'projected_full_map_difference_norm': result['projected_full_map_difference_norm']})
    return {'source': source, 'actions': tuple(a.role for a in protocol.actions),
            'terms': results, 'scales': arrays['scales'], 'receivers': arrays['receivers']}, exports, checks


def signed_term_accounting(inherited, generated, direct):
    """Signed receiver vectors and cross term; a norm alone loses cancellation."""
    total = inherited + generated
    i2, g2, d2 = (fsum(float(x) ** 2 for x in v) for v in (inherited, generated, direct))
    cross = 2 * fsum(float(x) * float(y) for x, y in zip(inherited, generated, strict=True))
    residual = float(np.max(np.abs(total - direct)))
    if residual > 1e-10 or abs(fsum((d2, -i2, -g2, -cross))) > 1e-10 * max(1., i2, g2, d2):
        raise ValueError('Common-receiver representation identity failed')
    return {'signed_inherited': inherited.tolist(), 'signed_generated': generated.tolist(),
            'signed_full_minus_reduced': direct.tolist(), 'inherited_squared': i2, 'generated_squared': g2,
            'twice_inherited_generated_alignment': cross, 'full_minus_reduced_squared': d2,
            'vector_identity_residual': residual, 'squared_identity_residual': fsum((d2, -i2, -g2, -cross))}


def paired_representation_rows(pair_rows, cases):
    """Apply one physical receiver, THEN take each signed high-minus-low contribution."""
    rows = []
    for matched in pair_rows:
        if matched['comparison'] != 'INPUT_KRYLOV48':
            continue
        low, high, nominal = (cases[matched[name]] for name in ('low_case', 'high_case', 'nominal_receiver_case'))
        receiver = receiver_matrix(nominal['receivers'])
        block = 0 if matched['block'] == 'q' else 1
        sl = slice(24 * block, 24 * (block + 1))
        for regime in ('FROZEN', 'REFRESH32'):
            projected = []
            for case in (low, high):
                ai = case['actions'].index(matched['action'])
                pi = case['source'].panel_ids.index(matched['panel_id'])
                key = (matched['view'], pi, regime, matched['horizon'])
                scale = case['scales'][ai, matched['horizon'] - 1, block]
                projected.append(tuple((term[ai] @ receiver.T)[sl] / scale for term in case['terms'][key]))
            common = {k: matched[k] for k in ('group_id', 'low_case', 'high_case', 'nominal_receiver_case',
                'temperature_friction', 'action', 'view', 'panel_id', 'horizon', 'block', 'common_receiver_sha256',
                'force_sha256', 'numerically_evaluable')}
            for scope, terms in (('LOW', projected[0]), ('HIGH', projected[1]),
                                 ('HIGH_MINUS_LOW', tuple(h - l for l, h in zip(*projected, strict=True)))):
                rows.append({**common, 'regime': regime, 'scope': scope, **signed_term_accounting(*terms)})
    return rows
