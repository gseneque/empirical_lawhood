# SPDX-License-Identifier: MPL-2.0
"""Matched SCI01 reversal census and between-endpoint signed accounting.

All comparisons share the physical receiver, force, panel, view and horizon.
These exposed descriptive cells do not create independent scientific units.
"""

from collections import Counter, defaultdict
from math import fsum, sqrt

import numpy as np


COMPARISONS = ('FULL', 'INPUT_KRYLOV48')
CELL_FIELDS = ('group_id', 'low_case', 'high_case', 'nominal_receiver_case',
               'action', 'view', 'panel_id', 'horizon', 'block')
JOIN_FIELDS = ('common_receiver_sha256', 'force_sha256', 'temperature_friction',
               'signed_native_difference', 'native_endpoint_signal_low', 'native_endpoint_signal_high')
EVENTS = ('both_endpoints_improve_contrast_worsens', 'one_improves_other_worsens',
          'both_endpoints_worsen', 'contrast_improves')


def _vector(value):
    array = np.asarray(value, dtype=float)
    if array.shape != (24,) or not np.isfinite(array).all():
        raise ValueError('Matched SCI01 requires all 24 finite signed receiver components')
    return array


def _square(vector):
    return fsum(float(x) ** 2 for x in vector)


def endpoint_accounting(low, high):
    """Compute S, A and D independently with accurate scalar summation."""
    low, high = _vector(low), _vector(high)
    low2, high2 = _square(low), _square(high)
    total = fsum((low2, high2))
    alignment = 2 * fsum(float(x) * float(y) for x, y in zip(high, low, strict=True))
    contrast = _square(high - low)
    residual = fsum((contrast, -total, alignment))
    # This is an arithmetic check, not an adequacy or scientific-effect cutoff.
    tolerance = 64 * np.finfo(float).eps * max(total, abs(alignment), contrast, np.finfo(float).tiny)
    if abs(residual) > tolerance:
        raise ValueError('Matched endpoint squared identity failed')
    return {'low_squared': low2, 'high_squared': high2,
            'endpoint_energy': total, 'twice_alignment': alignment,
            'contrast_squared': contrast, 'identity_residual': residual}


def _change(before, after, *, scale=None):
    difference = after - before
    scale = max(abs(before), abs(after)) if scale is None else scale
    bound = 64 * np.finfo(float).eps * max(scale, np.finfo(float).tiny)
    strict = 'IMPROVES' if difference < 0 else 'WORSENS' if difference > 0 else 'EQUAL'
    return difference, strict, 'ROUND_OFF_TIE' if abs(difference) <= bound else strict, bound


def compare_endpoint_errors(frozen_low, frozen_high, refreshed_low, refreshed_high):
    """Exactly the same two physical endpoints, before and after the paid refresh."""
    before = endpoint_accounting(frozen_low, frozen_high)
    after = endpoint_accounting(refreshed_low, refreshed_high)
    changes = {}
    for name, field in (('low', 'low_squared'), ('high', 'high_squared'), ('contrast', 'contrast_squared')):
        delta, strict, stable, bound = _change(before[field], after[field])
        changes.update({name + '_squared_change': delta, name + '_strict_change': strict,
                        name + '_change': stable, name + '_roundoff_bound': bound})
    low, high, contrast = (changes[name + '_change'] for name in ('low', 'high', 'contrast'))
    if low == high == 'IMPROVES':
        endpoint_class = 'BOTH_IMPROVE'
    elif {low, high} == {'IMPROVES', 'WORSENS'}:
        endpoint_class = 'MIXED'
    elif low == high == 'WORSENS':
        endpoint_class = 'BOTH_WORSEN'
    else:
        endpoint_class = 'INCLUDES_TIE'
    delta_s = after['endpoint_energy'] - before['endpoint_energy']
    delta_a = after['twice_alignment'] - before['twice_alignment']
    delta_d = changes['contrast_squared_change']
    residual = fsum((delta_d, -delta_s, delta_a))
    scale = max(before['endpoint_energy'], after['endpoint_energy'], np.finfo(float).tiny)
    if abs(residual) > 128 * np.finfo(float).eps * scale:
        raise ValueError('Matched change-of-alignment identity failed')
    growth = _change(0., delta_s, scale=scale)[2] == 'WORSENS'
    loss = _change(0., -delta_a, scale=scale)[2] == 'WORSENS'
    mechanism = ('BOTH' if growth and loss else 'ENDPOINT_ENERGY_GROWTH' if growth
                 else 'LOSS_OF_ALIGNMENT' if loss else 'NEITHER_POSITIVE')
    return {**{'frozen_' + k: v for k, v in before.items()},
            **{'refreshed_' + k: v for k, v in after.items()}, **changes,
            'endpoint_class': endpoint_class,
            'both_endpoints_improve_contrast_worsens': endpoint_class == 'BOTH_IMPROVE' and contrast == 'WORSENS',
            'one_improves_other_worsens': endpoint_class == 'MIXED',
            'both_endpoints_worsen': endpoint_class == 'BOTH_WORSEN',
            'contrast_improves': contrast == 'IMPROVES',
            'delta_endpoint_energy': delta_s, 'delta_twice_alignment': delta_a,
            'loss_of_alignment_contribution': -delta_a,
            'delta_contrast_squared': delta_d, 'alignment_change_residual': residual,
            'positive_deterioration_contributions': mechanism,
            'frozen_low_error': sqrt(before['low_squared']), 'frozen_high_error': sqrt(before['high_squared']),
            'refreshed_low_error': sqrt(after['low_squared']), 'refreshed_high_error': sqrt(after['high_squared']),
            'frozen_contrast_error': sqrt(before['contrast_squared']),
            'refreshed_contrast_error': sqrt(after['contrast_squared'])}


def matched_reversal_rows(pair_rows, assessments):
    """Join the retained complete cell census; refuse duplicates and changed instruments."""
    methods_by_cell, unavailable = defaultdict(dict), []
    by_case = {row.original_case.case_index: row for row in assessments}
    for row in pair_rows:
        if row['status'] != 'MATCHED':
            unavailable.append(dict(row))
            continue
        key = tuple(row[field] for field in CELL_FIELDS)
        if row['method'] in methods_by_cell[key]:
            raise ValueError('Duplicate matched SCI01 method cell')
        methods_by_cell[key][row['method']] = row
    results = []
    for key, methods in sorted(methods_by_cell.items()):
        for method in COMPARISONS:
            refreshed = method + '_REFRESH32'
            if method not in methods or refreshed not in methods:
                raise ValueError('Matched SCI01 drops a frozen/refreshed comparison')
            before, after = methods[method], methods[refreshed]
            if any(before[field] != after[field] for field in JOIN_FIELDS):
                raise ValueError('Matched SCI01 substitutes its common physical instrument or native response')
            vectors = [row[field] for row in (before, after)
                       for field in ('signed_endpoint_error_low', 'signed_endpoint_error_high')]
            for row in (before, after):
                if not np.array_equal(_vector(row['signed_endpoint_error_high']) - _vector(row['signed_endpoint_error_low']),
                                      _vector(row['signed_difference_error'])):
                    raise ValueError('Matched SCI01 loses the signed high-minus-low error')
            # Original SCI01 stores native-minus-model; the paper declares the opposite.
            vectors = [(-_vector(vector)).tolist() for vector in vectors]
            gates = []
            for case in (before['low_case'], before['high_case']):
                assessment = by_case[case]
                for name in (method, refreshed):
                    original = next(m for m in assessment.methods if m.method == name)
                    gates.append({'case_index': case, 'method': name,
                                  'original_numerical_usable': original.original_numerical_usable,
                                  'paired_discrepancy': str(original.paired_discrepancy(before['horizon'])),
                                  'numerically_evaluable': original.adequate(before['horizon']) is not None})
            results.append({**dict(zip(CELL_FIELDS, key, strict=True)),
                **{field: before[field] for field in JOIN_FIELDS},
                'status': 'MATCHED', 'comparison': method, 'frozen_method': method, 'refreshed_method': refreshed,
                'numerically_evaluable': all(g['numerically_evaluable'] for g in gates), 'original_numerical_gates': gates,
                'signed_frozen_error_low': vectors[0], 'signed_frozen_error_high': vectors[1],
                'signed_refreshed_error_low': vectors[2], 'signed_refreshed_error_high': vectors[3],
                **compare_endpoint_errors(*vectors)})
    return results, unavailable


def census(rows, fields):
    """Full descriptive counts and gate-qualified subsets, never independent cell trials."""
    groups = defaultdict(list)
    for row in rows:
        groups[tuple(row[f] for f in fields)].append(row)
    summaries = []
    for key, group in sorted(groups.items()):
        for population in ('ALL_RETAINED', 'ORIGINAL_NUMERICAL_GATES_PASS'):
            selected = [r for r in group if population == 'ALL_RETAINED' or r['numerically_evaluable']]
            worsened = [r for r in selected if r['contrast_change'] == 'WORSENS']
            summaries.append({**dict(zip(fields, key, strict=True)), 'population': population,
                'retained_cells': len(group), 'cells': len(selected),
                'numerically_unevaluable_cells': sum(not r['numerically_evaluable'] for r in group),
                'independent_groups': len({r['group_id'] for r in selected}),
                **{event: sum(r[event] for r in selected) for event in EVENTS},
                'endpoint_classes': dict(Counter(r['endpoint_class'] for r in selected)),
                'contrast_classes': dict(Counter(r['contrast_change'] for r in selected)),
                'joint_classes': dict(Counter(r['endpoint_class'] + ':' + r['contrast_change'] for r in selected)),
                'worsened_contrast_contributions': dict(Counter(r['positive_deterioration_contributions'] for r in worsened)),
                'sum_delta_endpoint_energy': fsum(r['delta_endpoint_energy'] for r in selected),
                'sum_delta_twice_alignment': fsum(r['delta_twice_alignment'] for r in selected),
                'sum_delta_contrast_squared': fsum(r['delta_contrast_squared'] for r in selected),
                'sum_loss_of_alignment_contribution': fsum(r['loss_of_alignment_contribution'] for r in selected)})
    return summaries


def representation_summary(rows, fields):
    grouped = defaultdict(list)
    for row in rows:
        if row['scope'] == 'HIGH_MINUS_LOW':
            grouped[tuple(row[key] for key in fields)].append(row)
    results = []
    for key, group in sorted(grouped.items()):
        for population in ('ALL_RETAINED', 'ORIGINAL_NUMERICAL_GATES_PASS'):
            selected = [r for r in group if population == 'ALL_RETAINED' or r['numerically_evaluable']]
            results.append({**dict(zip(fields, key, strict=True)), 'population': population,
                'retained_cells': len(group), 'cells': len(selected),
                'negative_cross_terms': sum(r['twice_inherited_generated_alignment'] < 0 for r in selected),
                'positive_cross_terms': sum(r['twice_inherited_generated_alignment'] > 0 for r in selected),
                **{'sum_' + field: fsum(r[field] for r in selected) for field in ('inherited_squared', 'generated_squared',
                    'twice_inherited_generated_alignment', 'full_minus_reduced_squared')}})
    return results



def join_native_errors(matched, representation):
    """Verify e_reduced,delta = e_full,delta - (d_H - d_L), retaining all signs."""
    indexed = {}
    for row in matched:
        key = (tuple(row[field] for field in CELL_FIELDS), row['comparison'])
        if key in indexed:
            raise ValueError('Duplicate native matched contrast cell')
        if row['comparison'] not in COMPARISONS:
            raise ValueError('Native matched contrast has an undeclared comparison')
        indexed[key] = row
    maximum = 0.
    for row in representation:
        if row['scope'] != 'HIGH_MINUS_LOW':
            continue
        key = tuple(row[k] for k in CELL_FIELDS)
        if any((key, method) not in indexed for method in COMPARISONS):
            raise ValueError('Native matched contrast omits its complete full/reduced pair')
        if row['regime'] not in ('FROZEN', 'REFRESH32'):
            raise ValueError('Native matched contrast changes its declared regime')
        full, reduced = (indexed[(key, method)] for method in COMPARISONS)
        prefix = 'signed_refreshed_error_' if row['regime'] == 'REFRESH32' else 'signed_frozen_error_'
        ef, er = (_vector(r[prefix + 'high']) - _vector(r[prefix + 'low']) for r in (full, reduced))
        d = _vector(row['signed_full_minus_reduced'])
        residual = float(np.max(np.abs(er - (ef - d))))
        if residual > 1e-10:
            raise ValueError('Representation terms do not join the native matched contrast')
        row.update(signed_full_native_contrast_error=ef.tolist(), signed_reduced_native_contrast_error=er.tolist(),
            full_native_contrast_squared=float(np.dot(ef, ef)), reduced_native_contrast_squared=float(np.dot(er, er)),
            native_join_residual=residual,
            twice_full_error_representation_alignment=float(2 * np.dot(ef, d)))
        maximum = max(maximum, residual)
    return maximum
