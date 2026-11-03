# SPDX-License-Identifier: MPL-2.0
"""Hand-calculated controls for dense finite-response and missingness rules."""

from dataclasses import replace
from decimal import Decimal, localcontext
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response import response_scoring as owner
from empirical_lawhood.kernel.decoding import decode_canonical_bytes


ACTION = SimpleNamespace(amplitude=Decimal('.01'), force_norm=Decimal(1), pulse_steps=16)
EPSILON = Decimal('.01')


def duration(values, *, usable=True):
    return owner.MatrixSampledResponseDuration(tuple(values), EPSILON, usable, tuple(value is not None for value in values))


def known_count(count):
    return duration([Decimal(0)] * count + [Decimal('.02')] * (29 - count))


@pytest.mark.parametrize('tick,position,momentum', (
    (1, '.000000005', '.00001'), (16, '.00000128', '.00016'),
    (32, '.00000384', '.00016'), (128, '.0000192', '.00016')))
def test_actuator_units_are_declared_not_response_relative(tick, position, momentum):
    actual = owner.nominal_actuator_scales(ACTION, Decimal('.001'), tick)
    assert actual == (Decimal(position), Decimal(momentum))
    # A 3-4-5 position error and one momentum component use L2 within each
    # block, then the maximum of blocks, never sqrt(48) or signal division.
    errors = [Decimal(0)] * 48
    errors[0], errors[1] = Decimal(position) * Decimal('.003'), Decimal(position) * Decimal('.004')
    errors[24] = Decimal(momentum) * Decimal('.01')
    q, p, loss = owner.response_error_norms(tuple(errors), action=ACTION,
        primary_timestep=Decimal('.001'), horizon_tick=tick)
    assert q == Decimal(position) * Decimal('.005')
    assert p == Decimal(momentum) * Decimal('.01') and loss == EPSILON
    with localcontext() as context:
        context.prec = 6
        assert owner.response_error_norms(tuple(errors), action=ACTION,
            primary_timestep=Decimal('.001'), horizon_tick=tick) == (q, p, loss)


def test_time_zero_is_undefined_and_fine_clock_has_identical_physical_units():
    with pytest.raises(ValueError, match='strictly positive'):
        owner.nominal_actuator_scales(ACTION, Decimal('.001'), 0)
    fine = SimpleNamespace(amplitude=ACTION.amplitude, force_norm=ACTION.force_norm, pulse_steps=32)
    for tick in range(1, 129):
        assert owner.nominal_actuator_scales(ACTION, Decimal('.001'), tick) == owner.nominal_actuator_scales(fine, Decimal('.0005'), 2 * tick)


def test_signed_hold_relative_even_and_zero_response_use_identical_contrast():
    receivers = np.zeros((48, 2, 2, 3, 4, 4), dtype='<c16')
    receivers[0, 0, 0, 0, 0, 0] = 1
    receivers[24, 1, 0, 0, 0, 0] = 1
    hold = np.zeros((2, 2, 2, 3, 4, 4), dtype='<c16')
    hold[:, :, 0, 0, 0, 0] = 10
    odd, even = np.zeros_like(hold), np.zeros_like(hold)
    odd[:, 0, 0, 0, 0, 0], odd[:, 1, 0, 0, 0, 0] = .002, -.004
    even[:, 0, 0, 0, 0, 0], even[:, 1, 0, 0, 0, 0] = .0001, .0003
    value = owner.response_contrasts(hold + odd + even, hold - odd + even, hold, receivers)
    np.testing.assert_allclose(value.odd[:, [0, 24]], [[.002, -.004]] * 2, rtol=1e-11)
    np.testing.assert_allclose(value.plus_from_hold[:, [0, 24]], [[.0021, -.0037]] * 2, rtol=1e-11)
    np.testing.assert_allclose(value.minus_from_hold[:, [0, 24]], [[-.0019, .0043]] * 2, rtol=1e-11)
    np.testing.assert_allclose(value.even_from_hold[:, [0, 24]], [[.0001, .0003]] * 2, rtol=1e-11)
    signed_zero_error = tuple(Decimal(str(float(v))) for v in -value.odd[0])
    assert owner.response_error_norms(signed_zero_error, action=ACTION,
        primary_timestep=Decimal('.001'), horizon_tick=128)[-1] > EPSILON
    quiet = owner.response_contrasts(hold, hold, hold, receivers)
    assert all(not np.any(getattr(quiet, name)) for name in ('odd', 'plus_from_hold', 'minus_from_hold', 'even_from_hold'))
    assert owner.response_error_norms((Decimal(0),) * 48, action=ACTION,
        primary_timestep=Decimal('.001'), horizon_tick=128)[-1] == 0


@pytest.mark.parametrize('first_failure', range(29))
def test_initial_consecutive_pass_count_and_equality_boundary(first_failure):
    values = [EPSILON] * 29
    values[first_failure] = Decimal('.0100000000000000000000000000000001')
    result = duration(values)
    assert result.count == first_failure and result.count_bounds == (first_failure, first_failure)
    assert result.first_known_failure_tick == 16 + 4 * first_failure
    assert result.first_unknown_tick is None and result.complete_followup and not result.right_censored
    assert result.adequate_through(128) is False
    if first_failure:
        assert result.adequate_through(16 + 4 * (first_failure - 1)) is True


def test_complete_only_censoring_and_unknown_eligibility_are_not_failures():
    complete = duration([EPSILON] * 29)
    assert complete.count == 29 and complete.count_bounds == (29, 29) and complete.right_censored
    unknown = duration([None] * 29)
    assert unknown.count is None and unknown.count_bounds == (0, 29)
    assert unknown.first_unknown_tick == 16 and unknown.first_known_failure_tick is None
    assert unknown.adequate_through(128) is None and not unknown.right_censored
    incomplete = duration([EPSILON] * 28 + [None])
    assert incomplete.count is None and incomplete.count_bounds == (28, 29)
    assert incomplete.adequate_through(124) is True and incomplete.adequate_through(128) is None
    assert not incomplete.complete_followup and not incomplete.right_censored
    unusable = duration([Decimal('.1')] * 29, usable=False)
    assert unusable.sampled_passes == (None,) * 29
    assert unusable.count_bounds == (0, 29) and unusable.first_known_failure_tick is None


def test_missing_before_and_after_known_failure_have_distinct_count_bounds():
    values = [Decimal(0)] * 29
    values[4], values[8] = None, Decimal('.02')
    ambiguous = duration(values)
    assert ambiguous.count is None and ambiguous.count_bounds == (4, 8)
    assert ambiguous.first_unknown_tick == 32 and ambiguous.first_known_failure_tick == 48
    assert ambiguous.adequate_through(32) is None and ambiguous.adequate_through(48) is False
    values[4], values[12] = Decimal(0), None
    known = duration(values)
    assert known.count == 8 and not known.complete_followup and not known.right_censored
    assert known.first_unknown_tick == 64


def test_incomplete_menu_can_prove_failure_but_not_a_pass_from_observed_lower_bound():
    value = replace(duration([EPSILON] * 29), point_complete=(False,) * 29)
    assert value.sampled_passes == (None,) * 29 and not value.right_censored
    failed = replace(value, point_errors=(Decimal('.02'),) + value.point_errors[1:])
    assert failed.count == 0 and failed.sampled_passes[0] is False
    assert failed.adequate_through(128) is False and not failed.complete_followup


def test_cumulative_unknowns_cannot_be_silently_dropped_or_interpolated():
    values = (Decimal('.003'), Decimal('.001'), None, Decimal('.02'))
    assert owner.cumulative_response_errors(values) == (Decimal('.003'), Decimal('.003'), None, None)
    with pytest.raises(ValueError, match='complete grid'):
        duration([Decimal(0)] * 3)


def test_paired_duration_loss_weights_views_and_all_29_checks():
    prediction, observed = (known_count(29), known_count(29)), (known_count(28), known_count(27))
    with localcontext() as context:
        context.prec = 60
        assert owner.paired_duration_loss(prediction, observed) == Decimal(3) / 58
        assert owner.paired_duration_loss(prediction, (known_count(28), known_count(28))) == Decimal(1) / 29
    assert owner.paired_duration_loss(prediction, (known_count(28), duration([None] * 29))) is None
    assert owner.paired_adequacy(prediction, 32) is True
    assert owner.paired_adequacy((known_count(29), known_count(4)), 32) is False
    assert owner.paired_adequacy((known_count(29), duration([None] * 29)), 32) is None
    assert owner.paired_adequacy((known_count(4), duration([None] * 29)), 32) is False
    with pytest.raises(ValueError, match='tolerance'):
        owner.paired_adequacy((known_count(29), replace(known_count(29), tolerance=Decimal('.02'))), 32)


def test_duration_record_has_a_stable_canonical_roundtrip():
    value = duration([Decimal('.01')] * 8 + [None] + [Decimal('.02')] * 20)
    assert decode_canonical_bytes(value.canonical_bytes(), owner.MatrixSampledResponseDuration, maximum_bytes=10000) == value


def test_structural_advantage_is_a_strict_three_way_conjunction_in_both_views():
    factor = (Decimal('.002'), Decimal('.0021'))
    challengers = {name: (Decimal('.004'), Decimal('.0041')) for name in owner.RESPONSE_CHALLENGERS}
    assert owner.joint_structural_advantage(factor, challengers, numerical_usable=True) is True
    for name in owner.RESPONSE_CHALLENGERS:
        changed = {**challengers, name: (Decimal('.003'), Decimal('.0031'))}
        assert owner.joint_structural_advantage(factor, changed, numerical_usable=True) is False  # Exact margin ties fail.
        changed = {**challengers, name: (Decimal('.004'), Decimal('.00410000001'))}
        assert owner.joint_structural_advantage(factor, changed, numerical_usable=True) is None
        changed = {**challengers, name: (Decimal('.004'), None)}
        assert owner.joint_structural_advantage(factor, changed, numerical_usable=True) is None
    assert owner.joint_structural_advantage(factor, challengers, numerical_usable=False) is None
    with pytest.raises(ValueError, match='three-challenger'):
        owner.joint_structural_advantage(factor, {key: val for key, val in challengers.items() if key != 'IO48'}, numerical_usable=True)


@pytest.mark.parametrize('case,expected', (('complete', (29, 29)), ('failure', (4, 4)),
    ('unknown-before-failure', (2, 4)), ('nonuse', (0, 29))))
def test_existing_e4_reader_reports_shared_k_and_preserves_nonuse(case, expected):
    from empirical_lawhood.adapters.methods.matrix_factor_response.retained_response_readout import adequacy_cell
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.full_factor_secondary_readout import _grid_lifetime

    values = [Decimal(0)] * 29
    if case in ('failure', 'unknown-before-failure'):
        values[4] = Decimal('.02')
    if case == 'unknown-before-failure':
        values[2] = None
    if case == 'nonuse':
        values = [None] * 29
    cells = tuple(adequacy_cell(horizon, error, normalized_tolerance=EPSILON,
        disposition='NO_ORIGIN' if case == 'nonuse' else 'FINITE', known_nonuse=case == 'nonuse')
        for horizon, error in zip(owner.DENSE_RESPONSE_HORIZONS, values, strict=True))
    result = _grid_lifetime(cells)
    assert (result['initial_sampled_pass_count_lower'], result['initial_sampled_pass_count_upper']) == expected
    assert result['initial_sampled_pass_count'] == (expected[0] if expected[0] == expected[1] else None)
    assert result['sampled_check_count'] == 29
    assert result['sampled_right_censored'] is (case == 'complete')
    assert result['sampled_followup_complete'] is (case in ('complete', 'failure'))
