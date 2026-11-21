# SPDX-License-Identifier: MPL-2.0
"""Analytic controls for retained accounting; fixtures supply no scientific evidence."""

from decimal import Decimal as D
from math import fsum
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.domains.matrix.matrix_factor_response.refresh_matched import census, compare_endpoint_errors, endpoint_accounting, matched_reversal_rows
from empirical_lawhood.domains.matrix.matrix_factor_response.refresh_representation import representation_terms, signed_term_accounting


def _v(*values):
    return np.pad(np.asarray(values, dtype=float), (0, 24 - len(values)))


def test_both_endpoints_improve_while_contrast_worsens_by_loss_of_alignment():
    result = compare_endpoint_errors(_v(2), _v(2), _v(1), _v(-1))
    assert result['both_endpoints_improve_contrast_worsens']
    assert result['delta_endpoint_energy'] == -6
    assert result['delta_twice_alignment'] == -10
    assert result['delta_contrast_squared'] == 4
    assert result['positive_deterioration_contributions'] == 'LOSS_OF_ALIGNMENT'
    assert result['alignment_change_residual'] == 0


@pytest.mark.parametrize('values,endpoint,contrast,contribution', (
    ((1, 1, .5, 2), 'MIXED', 'WORSENS', 'ENDPOINT_ENERGY_GROWTH'),
    ((1, 1, 2, -2), 'BOTH_WORSEN', 'WORSENS', 'BOTH'),
    ((1, -1, 2, 2), 'BOTH_WORSEN', 'IMPROVES', 'ENDPOINT_ENERGY_GROWTH'),
    ((2, -2, 1, -1), 'BOTH_IMPROVE', 'IMPROVES', 'NEITHER_POSITIVE'),
    ((0, 0, 0, 0), 'INCLUDES_TIE', 'ROUND_OFF_TIE', 'NEITHER_POSITIVE'),
))
def test_complete_contingency_and_overlapping_requested_events(values, endpoint, contrast, contribution):
    result = compare_endpoint_errors(*(_v(x) for x in values))
    assert result['endpoint_class'] == endpoint
    assert result['contrast_change'] == contrast
    assert result['positive_deterioration_contributions'] == contribution
    assert result['contrast_improves'] == (contrast == 'IMPROVES')
    assert result['both_endpoints_worsen'] == (endpoint == 'BOTH_WORSEN')


def test_sign_convention_preserves_squared_quantities_but_not_vectors():
    low, high = _v(3, -4), _v(-2, 1)
    assert endpoint_accounting(low, high) == endpoint_accounting(-low, -high)
    assert endpoint_accounting(low, high)['contrast_squared'] == 50
    with pytest.raises(ValueError, match='24 finite'):
        endpoint_accounting(_v(np.nan), high)


def test_near_equal_values_retain_strict_sign_and_roundoff_tie():
    result = compare_endpoint_errors(_v(1), _v(2), _v(np.nextafter(1., 2.)), _v(2))
    assert result['low_strict_change'] == 'WORSENS'
    assert result['low_change'] == 'ROUND_OFF_TIE'
    assert result['endpoint_class'] == 'INCLUDES_TIE'


def _pair_inputs():
    rows = []
    for method, low, high in (('FULL', 2, 2), ('FULL_REFRESH32', 1, -1),
                             ('INPUT_KRYLOV48', 2, 2), ('INPUT_KRYLOV48_REFRESH32', 1, -1)):
        rows.append({'group_id': 'group.0', 'low_case': 0, 'high_case': 1, 'nominal_receiver_case': 8,
            'action': 'TRACE', 'view': 'primary', 'panel_id': 'panel.0', 'horizon': 64, 'block': 'q',
            'common_receiver_sha256': 'a' * 64, 'force_sha256': 'b' * 64, 'temperature_friction': ['.5', '.5'],
            'signed_native_difference': _v(1).tolist(), 'native_endpoint_signal_low': 3., 'native_endpoint_signal_high': 4.,
            'signed_endpoint_error_low': _v(low).tolist(), 'signed_endpoint_error_high': _v(high).tolist(),
            'signed_difference_error': _v(high - low).tolist(), 'status': 'MATCHED', 'method': method})
    assessments = [SimpleNamespace(original_case=SimpleNamespace(case_index=i), methods=tuple(
        SimpleNamespace(method=r['method'], original_numerical_usable=True, paired_discrepancy=lambda h: D('.0002'),
                        adequate=lambda h: None) for r in rows)) for i in (0, 1)]
    return rows, assessments


def test_join_preserves_unavailable_and_numerically_failed_cells_and_converts_signs():
    rows, assessments = _pair_inputs()
    missing = {'status': 'UNAVAILABLE_ORIGINAL_OR_CONSTRUCTION', 'low_case': 9, 'high_case': 10}
    matched, unavailable = matched_reversal_rows([*rows, missing], assessments)
    assert unavailable == [missing]
    assert len(matched) == 2 and all(not r['numerically_evaluable'] for r in matched)
    assert matched[0]['signed_frozen_error_low'] == _v(-2).tolist()
    counted = census(matched, ('horizon',))
    assert counted[0]['cells'] == 2 and counted[1]['cells'] == 0
    assert counted[1]['retained_cells'] == counted[1]['numerically_unevaluable_cells'] == 2


@pytest.mark.parametrize('mutation', ('receiver', 'force', 'native', 'missing', 'duplicate', 'difference'))
def test_changed_or_incomplete_physical_cell_is_refused(mutation):
    rows, assessments = _pair_inputs()
    if mutation in ('receiver', 'force'):
        rows[1]['common_receiver_sha256' if mutation == 'receiver' else 'force_sha256'] = 'c' * 64
    elif mutation == 'native':
        rows[1]['signed_native_difference'] = _v(2).tolist()
    elif mutation == 'difference':
        rows[1]['signed_difference_error'] = _v(3).tolist()
    elif mutation == 'missing':
        rows.pop()
    else:
        rows.append(rows[0])
    with pytest.raises(ValueError, match='[Mm]atched|Duplicate'):
        matched_reversal_rows(rows, assessments)


@pytest.mark.parametrize('dt', (D('.001'), D('.0005')))
@pytest.mark.parametrize('friction', (D(0), D(2)))
def test_variation_of_constants_matches_explicit_sum_and_saved_state(dt, friction):
    h = np.array([[2., .7, -.3], [.7, 7., 1.], [-.3, 1., 4.]])
    basis = np.eye(3)[:, :2]
    full = np.array([[.1, -.2, .05, .03, .2, -.1]])
    reduced = np.array([[.08, -.19, .04, .18]])
    result = representation_terms(h, basis, full, reduced, timestep=dt, friction=friction, steps=17)
    m, r, lift, defect = (result[key] for key in ('M', 'R', 'L', 'defect'))
    inherited = np.linalg.matrix_power(m, 17) @ (full[0] - lift @ reduced[0])
    generated = np.zeros(6)
    for k in range(17):
        generated += np.linalg.matrix_power(m, 16 - k) @ defect @ np.linalg.matrix_power(r, k) @ reduced[0]
    i, g, f, z = result['records'][-1]
    np.testing.assert_allclose(i[0], inherited, rtol=1e-13, atol=1e-16)
    np.testing.assert_allclose(g[0], generated, rtol=1e-13, atol=1e-16)
    np.testing.assert_allclose(i + g, f - z @ lift.T, rtol=1e-13, atol=1e-16)
    # The projected composed map includes a feedback term absent from actual reduced BAOAB.
    assert result['projected_full_map_difference_norm'] > 0
    assert not np.array_equal(r, lift.T @ m @ lift)


def test_zero_checkpoint_error_does_not_remove_new_representation_error():
    h = np.array([[2., 3.], [3., 4.]])
    basis = np.eye(2)[:, :1]
    reduced = np.array([[1., .1]])
    result = representation_terms(h, basis, np.array([[1., 0., .1, 0.]]), reduced,
                                  timestep=D('.001'), friction=D(1), steps=20)
    inherited, generated, _, _ = result['records'][-1]
    np.testing.assert_array_equal(inherited, np.zeros_like(inherited))
    assert np.linalg.norm(generated) > 0


def test_invariant_representation_has_only_propagated_checkpoint_error():
    result = representation_terms(np.diag([2., 4.]), np.eye(2)[:, :1], np.array([[1., 2., .1, .2]]),
        np.array([[.8, .05]]), timestep=D('.001'), friction=D(1), steps=20)
    inherited, generated, full, reduced = result['records'][-1]
    np.testing.assert_array_equal(generated, np.zeros_like(generated))
    np.testing.assert_allclose(inherited, full - reduced @ result['L'].T, atol=1e-14)


def test_signed_receiver_accounting_retains_cancellation():
    i, g = _v(2, 1), _v(-1, -1)
    row = signed_term_accounting(i, g, i + g)
    assert row['twice_inherited_generated_alignment'] == -6
    assert row['full_minus_reduced_squared'] == fsum((row['inherited_squared'], row['generated_squared'], -6)) == 1
    with pytest.raises(ValueError, match='identity failed'):
        signed_term_accounting(i, g, _v(2))
