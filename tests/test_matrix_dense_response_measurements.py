# SPDX-License-Identifier: MPL-2.0
"""Independent mathematical controls; synthetic states confer no native authority."""

from dataclasses import replace
from decimal import Decimal as D
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response import response_scoring as score
from empirical_lawhood.adapters.methods.matrix_factor_response.origin_mechanics import (
    MatrixIO48Construction, MatrixOriginResponseModel, ORIGIN_RESPONSE_PREDICTORS,
)
from empirical_lawhood.adapters.methods.matrix_factor_response.records import ACTION_ROLES, MatrixFactorAction
from empirical_lawhood.adapters.simulators.six_matrix_response.shooting import hermitian_basis
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity


@pytest.fixture
def assay():
    model = MatrixOriginResponseModel('exposed.dense.model',
        ObjectIdentity('exposed.dense.implementation', 'empirical-lawhood/tests/inert-implementation', '1.0.0', 'a' * 64),
        MatrixIO48Construction('exposed.dense.io48'))
    protocol = SimpleNamespace(mechanical_model=model, horizon_steps=score.DENSE_RESPONSE_HORIZONS,
        actions=tuple(MatrixFactorAction('exposed.action.' + role.lower(), role, D('.01'), 16, D(1)) for role in ACTION_ROLES))
    panels = tuple(SimpleNamespace(panel_id='exposed.panel.' + str(index)) for index in range(2))
    axes = hermitian_basis(4)
    receivers = np.zeros((48, 2, 2, 3, 4, 4), dtype='<c16')
    for phase in range(2):
        for index in range(24):
            receivers[24 * phase + index, phase, index // 12, index // 4 % 3] = axes[index % 4]
    frozen = {view + '_full_grid_' + predictor.lower(): np.zeros((4, 128, 48), dtype='<f8')
        for view in ('primary', 'fine') for predictor in ORIGIN_RESPONSE_PREDICTORS}
    frozen['receivers'] = receivers
    native = {}
    for view, multiplier in (('primary', 1), ('fine', 2)):
        for panel in panels:
            for action in protocol.actions:
                for sign in ('plus', 'minus', 'hold'):
                    for phase in ('positions', 'momenta'):
                        native['branch.' + view + '.' + panel.panel_id + '.' + action.action_id + '.' + sign + '.' + phase] = np.zeros(
                            (128 * multiplier + 1, 2, 3, 4, 4), dtype='<c16')
    return protocol, panels, frozen, native


def impulse(assay, *, tick, magnitude, phase='positions', view='primary', panel=0, action=0, hold=0.):
    protocol, panels, frozen, native = assay
    receiver = frozen['receivers'][0 if phase == 'positions' else 24, 0 if phase == 'positions' else 1]
    multiplier = 1 if view == 'primary' else 2
    for sign, value in (('plus', magnitude + hold), ('minus', -magnitude + hold), ('hold', hold)):
        name = 'branch.' + view + '.' + panels[panel].panel_id + '.' + protocol.actions[action].action_id + '.' + sign + '.' + phase
        native[name][multiplier * tick] = receiver * value


def measure(assay, **kwargs):
    protocol, panels, frozen, native = assay
    return score.dense_response_measurements(protocol, panels, native, frozen,
        available=kwargs.get('available', True), numerical_usable=kwargs.get('numerical_usable', True))


def test_intercheck_excursion_does_not_redefine_the_sampled_duration(assay):
    impulse(assay, tick=17, magnitude=1e-4)
    cells, result = measure(assay)
    assert len(cells) == 3248 and len(result.curves) == 14 and len(result.amplitudes) == 64
    primary = next(row for row in result.curves if (row.view, row.predictor) == ('PRIMARY', 'FACTOR'))
    duration = primary.duration(numerical_usable=True)
    assert duration.count == 29 and duration.right_censored
    assert primary.point_errors[16] > D('.01') and primary.point_errors[15] == primary.point_errors[19] == 0
    assert result.factor_log_targets == (D(0),) * 58
    odd = next(row for row in result.amplitudes if row.key == ('PRIMARY', assay[1][0].panel_id, assay[0].actions[0].action_id, 'ODD'))
    assert odd.position_maxima[17] > 0 and odd.position_minima[17] == 0
    assert odd.position_norms[0] == 0 and odd.normalized_amplitudes[0] is None
    assert odd.normalized_amplitudes[17] == primary.point_errors[16]
    with pytest.raises(ValueError, match='3248'):
        result.validate_cells(cells[:-1])


def test_actual_error_uses_raw_odd_contrast_and_each_horizons_nominal_units(assay):
    impulse(assay, tick=16, magnitude=2e-6, hold=7e-5)
    impulse(assay, tick=16, magnitude=-3e-6, phase='momenta', hold=5e-5)
    cells, result = measure(assay)
    selected = next(row for row in cells if row.key == ('PRIMARY', assay[1][0].panel_id, assay[0].actions[0].action_id, 'ZERO_RESPONSE', 16))
    # Independent scalar HS contraction of actual retained PLUS/MINUS states.
    protocol, panels, frozen, native = assay
    stem = 'branch.primary.' + panels[0].panel_id + '.' + protocol.actions[0].action_id + '.'
    odd = np.stack(tuple((native[stem + 'plus.' + phase][16] - native[stem + 'minus.' + phase][16]) / 2
        for phase in ('positions', 'momenta')))
    actual = np.asarray([np.vdot(receiver, odd).real for receiver in frozen['receivers']])
    qnorm, pnorm = np.linalg.norm(actual[:24]), np.linalg.norm(actual[24:])
    expected = max(qnorm / (.01 * .016 * (.016 - .016 / 2)), pnorm / (.01 * .016))
    assert float(selected.normalized_error) == pytest.approx(expected, rel=1e-12)
    assert float(selected.position_error_norm) == pytest.approx(qnorm, rel=1e-12)
    assert float(selected.momentum_error_norm) == pytest.approx(pnorm, rel=1e-12)
    odd_curve = next(row for row in result.amplitudes if row.key == ('PRIMARY', panels[0].panel_id, protocol.actions[0].action_id, 'ODD'))
    plus = next(row for row in result.amplitudes if row.key == (*odd_curve.key[:3], 'PLUS_FROM_HOLD'))
    minus = next(row for row in result.amplitudes if row.key == (*odd_curve.key[:3], 'MINUS_FROM_HOLD'))
    even = next(row for row in result.amplitudes if row.key == (*odd_curve.key[:3], 'EVEN_FROM_HOLD'))
    assert plus.position_maxima[16] > 0 and minus.position_minima[16] < 0
    assert plus.momentum_minima[16] < 0 and minus.momentum_maxima[16] > 0
    assert float(even.position_norms[16]) < 1e-19 and float(even.momentum_norms[16]) < 1e-19
    assert odd_curve.complement_position_norms[16] < D('1e-19')
    assert decode_canonical_bytes(result.canonical_bytes(), score.MatrixDenseResponseDiagnostics, maximum_bytes=None) == result


def test_missing_action_does_not_pass_and_known_failure_still_bounds_K(assay):
    protocol, panels, frozen, native = assay
    frozen['primary_full_grid_factor'][1, 15, :] = np.nan
    impulse(assay, tick=20, magnitude=1e-3)
    _, result = measure(assay)
    curve = next(row for row in result.curves if (row.view, row.predictor) == ('PRIMARY', 'FACTOR'))
    assert curve.point_errors[15] == 0 and not curve.point_complete[15]
    duration = curve.duration(numerical_usable=True)
    assert duration.sampled_passes[0] is None and duration.sampled_passes[1] is False
    assert duration.count is None and duration.count_bounds == (0, 1)
    assert result.factor_log_targets[:29] == (None,) * 29
    assert result.factor_log_targets[29:] == (D(0),) * 29
    unusable = replace(result, numerical_usable=False)
    assert unusable.factor_log_targets == (None,) * 58
    assert curve.duration(numerical_usable=False).count_bounds == (0, 29)


def test_origin_defect_is_primary_only_and_never_uses_native_outcomes(assay):
    protocol, _, frozen, native = assay
    frozen['primary_full_grid_full_coupled'][0, 15, 0] = 1e-6
    baseline = score.origin_response_defect_feature(protocol, frozen)
    assert baseline > 0
    frozen['fine_full_grid_full_coupled'][0, 15, 0] = 1
    for value in native.values():
        value[:] = np.nan
    assert score.origin_response_defect_feature(protocol, frozen) == baseline
    frozen['primary_full_grid_factor'][1, 15, 0] = np.nan
    assert score.origin_response_defect_feature(protocol, frozen) is None


def test_unentered_complete_denominator_does_not_invent_zero_response_service(assay):
    protocol, panels, frozen, native = assay
    for name, value in frozen.items():
        if name != 'receivers':
            value[:] = np.nan
    cells, result = measure(assay, available=False, numerical_usable=False)
    assert len(cells) == 3248 and result.factor_log_targets == (None,) * 58
    assert all(row.normalized_error is None for row in cells)
    assert all(value is None for row in result.amplitudes for value in row.position_norms)
    assert all(row.duration(numerical_usable=False).count is None for row in result.curves)


def test_unknown_contact_projection_needs_no_arrays_and_retains_every_unobserved_cell(assay):
    protocol, panels, _, _ = assay
    cells, result = score.unobserved_dense_response_measurements(protocol, panels)
    assert len(cells) == 2 * 2 * 4 * 7 * 29
    assert result.factor_log_targets == (None,) * 58
    assert all(cell.normalized_error is None for cell in cells)
    assert all(curve.duration(numerical_usable=False).count_bounds == (0, 29) for curve in result.curves)
    assert all(value is None for curve in result.origin_curves for value in curve.point_errors)
    assert all(value is None for curve in result.amplitudes for value in curve.normalized_amplitudes)
    assert decode_canonical_bytes(result.canonical_bytes(), type(result), maximum_bytes=None) == result
