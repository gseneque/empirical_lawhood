# SPDX-License-Identifier: MPL-2.0
"""Complete case/group summaries and physically matched finite-change diagnostics."""

from collections import Counter
from decimal import Decimal
from hashlib import sha256
from itertools import product

import numpy as np

from empirical_lawhood.domains.matrix.matrix_factor_response.refresh_records import REFRESH_METHODS
from empirical_lawhood.domains.matrix.matrix_factor_response.refresh_science import lift_states, receiver_matrix
from empirical_lawhood.domains.matrix.matrix_factor_response.response_scoring import DENSE_RESPONSE_HORIZONS


def channel_endpoints(protocol, source, arrays):
    """Keep weak signals, signed accounting and cancellation beside each endpoint."""
    rows = []
    for view, pi, ai, horizon, block in product(('primary', 'fine'), range(2), range(4), (64, 128), range(2)):
        prefix = f'{view}.p{pi}'
        signal = float(arrays[prefix + '.signal'][ai, horizon - 1, block])
        for method in REFRESH_METHODS:
            error = float(arrays[prefix + '.error_norm.' + method.lower()][ai, horizon - 1, block])
            row = {'case_index': source.case_index, 'group_id': source.group_id,
                'coordinate': source.temperature_friction_coupling, 'view': view,
                'panel_id': source.panel_ids[pi], 'action': protocol.actions[ai].role,
                'horizon': horizon, 'block': ('q', 'p')[block], 'method': method,
                'native_signal': signal, 'error': error,
                'error_over_signal_diagnostic': None if signal == 0 else error / signal,
                'relative_adequacy': 'UNSELECTED_NO_RATIO_THRESHOLD'}
            if method in ('FACTOR', 'INPUT_KRYLOV48', 'INPUT_KRYLOV48_REFRESH32'):
                squares = arrays[prefix + '.squares.' + method.lower()][:, ai, horizon - 1, block]
                cross = arrays[prefix + '.cross.' + method.lower()][:, ai, horizon - 1, block]
                row.update(term_squared_norms=squares.tolist(), signed_cross_terms=cross.tolist(),
                    cancellation_fraction=None if sum(squares) == 0 else float(-sum(cross) / sum(squares)))
            rows.append(row)
    return rows


def finite_pair_operands(protocol, source, arrays):
    """Retain raw physical endpoints, never reproject an incompatible scored response."""
    phases = {}
    for view, pi in product(('primary', 'fine'), range(2)):
        prefix = f'{view}.p{pi}'
        phases[(view, pi, 'NATIVE')] = arrays[prefix + '.native.phase.endpoints'].copy()
        for method in REFRESH_METHODS:
            stem = prefix if method.endswith('_REFRESH32') else view
            basis_name = method.removesuffix('_REFRESH32')
            phases[(view, pi, method)] = lift_states(arrays[stem + '.state.' + method.lower()][:, 2:],
                arrays[view + '.basis.' + basis_name.lower()])
    return {'source': source, 'actions': tuple(a.role for a in protocol.actions),
        'forces': arrays['forces'].copy(), 'receivers': arrays['receivers'].copy(),
        'scales': arrays['scales'][:, np.asarray((63, 127))].copy(), 'phases': phases}


def paired_endpoint_rows(low, high, nominal):
    """Exact force joins plus a preselected nominal receiver; missing joins stay missing."""
    source = low['source']
    common = {'group_id': source.group_id, 'low_case': source.case_index,
        'high_case': high['source'].case_index, 'nominal_receiver_case': nominal['source'].case_index,
        'temperature_friction': source.temperature_friction_coupling[:2]}
    if source.panel_ids != high['source'].panel_ids or source.panel_ids != nominal['source'].panel_ids:
        return [{**common, 'status': 'INCOMPATIBLE_PANEL_IDENTITIES'}]
    receiver = receiver_matrix(nominal['receivers'])
    common['common_receiver_sha256'] = sha256(nominal['receivers'].tobytes()).hexdigest()
    rows = []
    for action in ('TRACE', 'GENERIC'):
        indices = tuple(value['actions'].index(action) for value in (low, high, nominal))
        li, hi, _ = indices
        if not (np.array_equal(low['forces'][li], high['forces'][hi])
                and np.array_equal(low['scales'][li], high['scales'][hi])):
            rows.append({**common, 'action': action, 'status': 'INCOMPATIBLE_PHYSICAL_FORCE_OR_SCALE'})
            continue
        force_hash = sha256(low['forces'][li].tobytes()).hexdigest()
        for view, pi, ei, method, block in product(('primary', 'fine'), range(2), range(2), REFRESH_METHODS, range(2)):
            sl = slice(block * 24, (block + 1) * 24)
            scale = low['scales'][li, ei, block]
            nl, nh = (value['phases'][(view, pi, 'NATIVE')][ai, ei] @ receiver.T
                      for value, ai in ((low, li), (high, hi)))
            ml, mh = (value['phases'][(view, pi, method)][ai, ei] @ receiver.T
                      for value, ai in ((low, li), (high, hi)))
            el, eh = (nl - ml)[sl] / scale, (nh - mh)[sl] / scale
            delta = eh - el
            nd = (nh - nl)[sl] / scale
            rows.append({**common, 'action': action, 'force_sha256': force_hash, 'status': 'MATCHED',
                'view': view, 'panel_id': source.panel_ids[pi], 'horizon': (64, 128)[ei],
                'block': ('q', 'p')[block], 'method': method,
                'signed_endpoint_error_low': el.tolist(), 'signed_endpoint_error_high': eh.tolist(),
                'signed_difference_error': delta.tolist(), 'signed_native_difference': nd.tolist(),
                'endpoint_error_low': float(np.linalg.norm(el)), 'endpoint_error_high': float(np.linalg.norm(eh)),
                'difference_error': float(np.linalg.norm(delta)), 'native_difference_signal': float(np.linalg.norm(nd)),
                'native_endpoint_signal_low': float(np.linalg.norm(nl[sl]) / scale),
                'native_endpoint_signal_high': float(np.linalg.norm(nh[sl]) / scale),
                'endpoint_cross_term': float(-2 * np.dot(el, eh))})
    return rows


def _finite_pairs(decision, operands):
    available = {value['source'].case_index: value for value in operands}
    groups = sorted({case.original_case.group_id for case in decision.cases})
    rows = []
    for group in groups:
        cases = [row.original_case for row in decision.cases if row.original_case.group_id == group]
        nominal = next(row for row in cases if row.temperature_friction_coupling == (Decimal(1),) * 3)
        for low in (row for row in cases if row.temperature_friction_coupling[2] == Decimal('.5')):
            high = next(row for row in cases if row.temperature_friction_coupling == (
                *low.temperature_friction_coupling[:2], Decimal(2)))
            if any(row.case_index not in available for row in (low, high, nominal)):
                rows.append({'group_id': group, 'low_case': low.case_index, 'high_case': high.case_index,
                    'nominal_receiver_case': nominal.case_index, 'status': 'UNAVAILABLE_ORIGINAL_OR_CONSTRUCTION',
                    'original_availability': tuple(row.original_availability for row in (low, high, nominal))})
                continue
            rows.extend(paired_endpoint_rows(*(available[row.case_index] for row in (low, high, nominal))))
    return rows


def summarize_refresh(decision, channels, operands):
    """Equal group summaries are descriptive; coordinates and panels add no replication."""
    cases, summaries = [], []
    for row in decision.cases:
        cases.append({'case_index': row.original_case.case_index, 'group_id': row.original_case.group_id,
            'coordinate': row.original_case.temperature_friction_coupling, 'decision': row.decision,
            'construction_failure': row.construction_failure,
            'methods': {method.method: {'H' + str(h): {
                'error': str(max(method.primary_curve[DENSE_RESPONSE_HORIZONS.index(h)],
                                 method.fine_curve[DENSE_RESPONSE_HORIZONS.index(h)])),
                'paired_discrepancy': str(method.paired_discrepancy(h)), 'adequate': method.adequate(h)}
                for h in (32, 64, 128)} for method in row.methods}})
    for regime, coupling in (('all', None), ('low_coupling', Decimal('.5')),
                            ('high_coupling', Decimal(2)), ('center', Decimal(1))):
        selected = [r for r in decision.cases if r.methods and (
            coupling is None or r.original_case.temperature_friction_coupling[2] == coupling)]
        for method, horizon in product(REFRESH_METHODS, (64, 128)):
            group_rows = []
            for group in sorted({r.original_case.group_id for r in selected}):
                values = [next(m for m in r.methods if m.method == method) for r in selected if r.original_case.group_id == group]
                index = DENSE_RESPONSE_HORIZONS.index(horizon)
                errors = [max(v.primary_curve[index], v.fine_curve[index]) for v in values]
                group_rows.append({'group_id': group, 'case_count': len(values),
                    'mean_error': sum(errors) / len(errors), 'maximum_error': max(errors),
                    'adequate': sum(v.adequate(horizon) is True for v in values),
                    'inadequate': sum(v.adequate(horizon) is False for v in values),
                    'unevaluable': sum(v.adequate(horizon) is None for v in values)})
            summaries.append({'regime': regime, 'method': method, 'horizon': horizon, 'groups': group_rows,
                'independent_groups': len(group_rows), 'nested_cases': len(selected),
                'equal_group_mean_error': None if not group_rows else sum(g['mean_error'] for g in group_rows) / len(group_rows),
                'maximum_error': None if not group_rows else max(g['maximum_error'] for g in group_rows)})
    finite_pairs = _finite_pairs(decision, operands)
    return {'decision': decision.identity, 'assigned_cases': 144, 'original_usable_cases': 36,
        'NO_ORIGIN': 108, 'assigned_groups': 16, 'usable_independent_groups': 4,
        'decision_counts': decision.decision_counts, 'cases': cases, 'method_summaries': summaries,
        'channel_endpoint_count': len(channels), 'finite_pair_row_statuses': dict(Counter(r['status'] for r in finite_pairs)),
        'finite_pair_assigned_pairs': 64, 'finite_pair_original_usable_pairs': 16,
        'scientific_role': 'EXPOSED_DEVELOPMENT_NO_MOLECULAR_ADMISSION',
        'weak_channel_adequacy': 'NO_CONSUMER_SPECIFIC_TOLERANCE_SELECTED',
        'independence': 'FOUR_GROUPS_COORDINATES_PANELS_ACTIONS_VIEWS_AND_TIMES_ARE_NESTED',
        'new_native_acquisition': 0, 'new_statistical_fits': 0}, finite_pairs
