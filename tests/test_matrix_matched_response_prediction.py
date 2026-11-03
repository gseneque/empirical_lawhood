# SPDX-License-Identifier: MPL-2.0
"""Exposed matched-curve arithmetic, with no acquired or qualified observations."""
from dataclasses import replace
from decimal import Decimal as D, localcontext
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response.configured_specification import (
    matched_e3_estimators, matched_e3_measurement,
)
from empirical_lawhood.adapters.methods.matrix_factor_response.matched_response_prediction import (
    MatchedResponseViewOutcome, matched_calibration_score, matched_duration_loss, postprocess_log_points,
    MATCHED_METHODS, matched_forecast_policy, matched_model_calibration, matched_primary_inference,
    matched_root_decision, admission_risk,
)
from empirical_lawhood.kernel.decoding import decode_canonical_bytes


def test_matched_contract_keeps_equal_feature_budgets_and_complete_paired_targets():
    measurement = matched_e3_measurement()
    assert measurement.endpoint_count == 29 and measurement.point_endpoint_count == 58
    selected = {method.method_key: method for method in matched_e3_estimators()}
    assert selected['S0'].feature_count == selected['B0'].feature_count == 22
    assert selected['SHARED_BASE'].feature_count == 18
    assert not selected['S0'].penalize_intercept and selected['S0'].ridge_lambda is None
    with pytest.raises(ValueError, match='unsupported acquisition geometry'):
        replace(measurement, horizons=(16, 64, 128))
    with pytest.raises(ValueError, match='matched estimator'):
        replace(selected['B0'], feature_blocks=selected['S0'].feature_blocks)
    assert decode_canonical_bytes(measurement.canonical_bytes(), type(measurement), maximum_bytes=100_000) == measurement


def test_public_matched_sampling_and_transport_use_factor_forecasts_without_diagnostic_endpoints():
    from pathlib import Path
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_adjudication import e3_sampling_endpoint_ids
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.e6_transport_science import _endpoint_order
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.scientific_design import MatrixProgrammeScientificDesign

    path = Path(__file__).resolve().parents[1] / 'programmes/foundations/emergent-structure/workflows/matrix-programme/scientific-design.example.json'
    design = decode_canonical_bytes(path.read_bytes(), MatrixProgrammeScientificDesign, maximum_bytes=None)
    expected = tuple(('FACTOR', tick) for tick in range(16, 129, 4))
    assert len(design.e3.measurement.descriptions) == 7
    assert design.e3.measurement.forecast_endpoints == _endpoint_order(design.e3.measurement) == expected
    assert e3_sampling_endpoint_ids(design.e3) == tuple(sorted(
        'output.factor.horizon-' + str(tick) for tick in range(16, 129, 4)))


def test_duration_loss_uses_both_initial_pass_counts_instead_of_point_error_size():
    with localcontext() as context:
        context.prec = 60
        failure = D('1.02').ln()
        points = (D(0),) * 10 + (failure,) * 19 + (D(0),) * 20 + (failure,) * 9
        actual = (D(0),) * 8 + (D('.03'),) * 21 + (D(0),) * 23 + (D('.03'),) * 6
        assert matched_duration_loss(points, actual) == D(5) / 58
    assert matched_duration_loss((None,) * 58, actual) is None


def test_duration_comparison_is_inclusive_in_log_domain_without_exponential_overflow():
    with localcontext() as context:
        context.prec = 60
        boundary = D('1.01').ln()
    assert matched_duration_loss((boundary,) * 58, (D('.01'),) * 58) == 0
    assert matched_duration_loss((D('1e10'),) * 58, (D('.02'),) * 58) == 0


def test_calibration_uses_the_postprocessed_point_and_missing_targets_are_infinite():
    with localcontext() as context:
        context.prec = 60
        top = D('1.1').ln()
        points = (D(-1), top, D(0)) + (top,) * 26 + (top,) * 29
        actual = (D(0), D('.1'), D('.15')) + (D('.1'),) * 26 + (D('.1'),) * 29
        expected = D('1.15').ln() - top
        assert postprocess_log_points(points)[:3] == (D(0), top, top)
        assert matched_calibration_score(points, actual) == expected
    assert matched_calibration_score(points, (None, *actual[1:])) is None
    assert matched_calibration_score((None, *points[1:]), actual) is None


def test_dense_view_cannot_drop_prior_unknown_or_recover_cumulative_error():
    outcome = MatchedResponseViewOutcome('primary', (D(1),) * 29, ('FINITE',) * 29)
    assert decode_canonical_bytes(outcome.canonical_bytes(), type(outcome), maximum_bytes=100_000) == outcome
    with pytest.raises(ValueError, match='preceding missingness'):
        replace(outcome, errors=(None, *outcome.errors[1:]), dispositions=('UNAVAILABLE', *outcome.dispositions[1:]))
    with pytest.raises(ValueError, match='cumulative error'):
        replace(outcome, errors=(D(2), *outcome.errors[1:]))


def test_separate_model_calibration_keeps_exact64_rank_and_vacuous_bounds():
    scores = tuple(('test.root.%02d' % index, D(index) / 1000, ('FINITE_WHOLE_UNIT_MAX58',)) for index in range(64))
    fitted = matched_model_calibration('S0', scores)
    assert fitted.rank == 62 and fitted.radius == D('.061')
    two = tuple((unit, None, ('UNKNOWN_CONTACT',)) if index < 2 else (unit, value, reasons)
        for index, (unit, value, reasons) in enumerate(scores))
    assert matched_model_calibration('B0', two).radius == D('.063')
    three = tuple((unit, None, ('UNKNOWN_CONTACT',)) if index < 3 else (unit, value, reasons)
        for index, (unit, value, reasons) in enumerate(scores))
    assert matched_model_calibration('B0', three).radius is None
    cal_policy = matched_forecast_policy('S0', (D(0),) * 58, None, calibrated=False)
    infinite = matched_forecast_policy('S0', (D(0),) * 58, None, calibrated=True)
    missing = matched_forecast_policy('B0', (None,) * 58, D(0), calibrated=True)
    assert cal_policy.bound_kind == 'UNCALIBRATED' and cal_policy.admissions == (None,) * 29
    assert infinite.bound_kind == 'INFINITE' and infinite.admissions == (False,) * 29
    assert missing.bound_kind == 'UNAVAILABLE' and missing.admissions == (None,) * 29
    assert matched_forecast_policy('B0', (D(0),) * 58, D(0), calibrated=True).admissions == (True,) * 29


def test_one_of29_win_uses_exact_integer_margin_and80_assigned_roots():
    views = {view: MatchedResponseViewOutcome(view, (D(0),) * 29, ('FINITE',) * 29) for view in ('primary', 'fine')}
    outcome = SimpleNamespace(view=views.__getitem__)
    with localcontext() as context:
        context.prec = 60
        fail = D('1.02').ln()
    points = {method: (D(0),) * 58 for method in MATCHED_METHODS}
    points['B0'] = (D(0),) * 28 + (fail,) + (D(0),) * 28 + (fail,)
    success = matched_root_decision('test.root.00', points, outcome, ())
    assert success.success and success.improvement_count == 2
    points['B0'] = (D(0),) * 57 + (fail,)
    assert not matched_root_decision('test.root.00', points, outcome, ()).success
    # Unknown roots are retained as operational nonsuccess and true-event unknown.
    decisions = tuple(replace(success, unit_id='test.root.%02d' % index) if index < 52 else
        matched_root_decision('test.root.%02d' % index, {method: (None,) * 58 for method in MATCHED_METHODS}, outcome,
            ('UNKNOWN_CONTACT',)) for index in range(80))
    inference = matched_primary_inference(decisions)
    assert len(inference.unit_ids) == 80 and inference.critical_successes == 52
    assert inference.events == (True,) * 52 + (None,) * 28
    assert inference.tail_numerator * 160 <= inference.tail_denominator


def test_admission_risk_retains_unknown_outcomes_and_zero_coverage_is_undefined():
    from scipy.stats import beta
    units = tuple('test.root.%02d' % index for index in range(8))
    result = admission_risk(units, (True,) * 4 + (False,) * 3 + (None,),
        (True, False, None, True, False, False, False, False))
    assert result['known_admitted_failure_unit_ids'] == units[1:2]
    assert result['unknown_admitted_outcome_unit_ids'] == units[2:3]
    assert result['coverage_numerator'] == 4 and result['coverage_denominator'] == 8
    assert (result['assigned_units'], result['admitted_units'], result['assessed_admitted_units'],
        result['unresolved_admitted_units'], result['observed_admitted_failures']) == (8, 4, 3, 1, 1)
    assert float(result['upper95_worst_case_failure_probability']) == pytest.approx(beta.ppf(.95, 3, 2), abs=1e-12)
    result = admission_risk(units, (False,) * 8, (False,) * 8)
    assert result['upper95_worst_case_failure_probability'] is None
    assert result['bound_kind'] == 'UNDEFINED_NO_ADMISSIONS'


def test_unrepresentable_upper_curve_keeps_log_domain_duration_loss_and_refuses_admission():
    from empirical_lawhood.adapters.methods.matrix_factor_response.matched_response_prediction import matched_duration_error_count
    points = (D('1e10'),) * 58
    policy = matched_forecast_policy('SR', points, D(0), calibrated=True)
    assert policy.bound_kind == 'UNAVAILABLE' and policy.admissions == (None,) * 29
    assert matched_duration_error_count(points, (D(0),) * 58) == 58
