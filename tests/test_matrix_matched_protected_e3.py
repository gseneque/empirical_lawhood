# SPDX-License-Identifier: MPL-2.0
"""Protected matched calculations over disclosed arithmetic native-schema rows.

These are exposed software operands and opaque physical pins. The fixture's
publication custody proves bytes only, never native acquisition or qualification.
"""
from dataclasses import replace
from decimal import Decimal as D
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response import configured_protected_methods as science
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_specification import (
    ConfiguredE3Assessment, ConfiguredE3Protocol, matched_e3_estimators, matched_e3_measurement,
)
from empirical_lawhood.adapters.methods.matrix_factor_response import matched_response_prediction as matched
from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_records import NativeTrainingPhysicalForecast
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_response_records import ConfiguredProtectedE3PhysicalForecast
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_adjudication import conditional_reasons
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_inputs import project_protected_e3_allocation
from empirical_lawhood.adapters.methods.matrix_primary_family import AMENDED_PRIMARY_FAMILY
from empirical_lawhood.adapters.methods.matrix_scheduled_history import response_records
from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex
from empirical_lawhood.api.configured_e3_incomplete_read import _denominator_math
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from tests.test_matrix_e3_original_publications import build_original_case
from tests.test_matrix_configured_protected_statistical import case as configured_case
from tests.test_matrix_configured_protected_e3 import actual_join, causal
from tests.test_matrix_e3_protected_methods import reference


@pytest.fixture(scope='module')
def original_case(tmp_path_factory):
    return build_original_case(tmp_path_factory, selected64=True)


def feature_values(row, *, curve_primary=False):
    return tuple(sorted((*row.values, ('d_lin', D('.001')),
        *((name, D('-1')) for name in matched.DRIFT_FEATURES),
        *((name, D('.001')) for name in ('d_hessian_block', 'd_hessian_mix') if curve_primary))))


def outcome(forecast, missing=False):
    views = tuple(matched.MatchedResponseViewOutcome(view, (None if missing else D('.03'),) * 29,
        ('UNKNOWN_CONTACT' if missing else 'FINITE',) * 29) for view in ('fine', 'primary'))
    unit = forecast.feature.unit_id
    return science.ConfiguredProtectedE3PairedOutcome('matched.outcome.' + unit, forecast.feature,
        science.identity(forecast), reference('matched.score.' + unit, response_records.ScheduledResponseScore),
        'b' * 64, reference('matched.protocol.' + unit, response_records.ScheduledResponseProtocol),
        tuple(reference('matched.panel.' + name + '.' + unit, response_records.ScheduledResponsePanel) for name in ('common', 'independent')),
        views, 'UNEVALUABLE' if missing else 'SATISFIED')


@pytest.fixture(scope='module', params=(False, True), ids=('retained-K', 'prospective-curve'))
def matched_e3_products(original_case, request):
    from empirical_lawhood.adapters.methods.matrix_factor_response.curve_contract import CURVE_IMPROVEMENT_RULE
    curve_primary = request.param
    previous = configured_case.__wrapped__(original_case)
    assessment = ConfiguredE3Assessment(improvement_margin=None, minimum_usable_units=0,
        null_success_numerator=1, null_success_denominator=2, alpha_numerator=1, alpha_denominator=160,
        comparison_ids=AMENDED_PRIMARY_FAMILY, improvement_rule='MATCHED_MEAN_K_LOSS_REDUCTION_AT_LEAST_ONE_OF_29',
        duration_margin_numerator=1, duration_margin_denominator=29)
    if curve_primary:
        assessment = replace(assessment, improvement_rule=CURVE_IMPROVEMENT_RULE, improvement_margin=D('.1'))
    specification = replace(previous.inputs.specification, specification_id='test.matched.protected-e3',
        protocol=ConfiguredE3Protocol('test.matched.protocol', matched_e3_measurement(), 'ORIGIN_ONLY_WHOLE_ROOT_MATCHED58'),
        methods=matched_e3_estimators(curve_primary=curve_primary), assessment=assessment, calibration_alpha=D('.05'),
        calibration_scope='MAX_POSITIVE_LOG1P_RESIDUAL_PAIRED58_FACTOR_OUTPUTS_PER_WHOLE_UNIT')
    inputs = replace(previous.inputs, specification=specification)
    allocation = project_protected_e3_allocation(inputs)
    features = []
    for row in previous.train_features.rows:
        pin = reference('matched.physical.' + row.unit_id, NativeTrainingPhysicalForecast)
        features.append(replace(row, physical_forecast=pin, fine_response_defect=D('.002'), values=feature_values(row, curve_primary=curve_primary),
            evidence=tuple(sorted((*row.evidence, pin), key=lambda value: value.object_id))))
    feature_bank = replace(previous.train_features, rows=tuple(features))
    outcome_bank = replace(previous.train_outcomes, rows=tuple(replace(row,
        views=tuple(matched.MatchedResponseViewOutcome(view, (D('.02'),) * 29, ('FINITE',) * 29)
            for view in ('fine', 'primary')), numerical_disposition='SATISFIED') for row in previous.train_outcomes.rows))
    case = SimpleNamespace(**{**vars(previous), 'inputs': inputs, 'allocation': allocation,
        'train_features': feature_bank, 'train_outcomes': outcome_bank})
    joined, banks = actual_join(case, inputs, allocation)
    models = science.fit_protected_e3_models(inputs, joined, *banks, record_id='test.matched.models')
    assert all(model.finite_counts == (64,) * 58 for model in models.models)
    assert tuple(model.method_key for model in models.models) == matched.MATCHED_METHODS
    frozen = science.freeze_protected_e3(specification, allocation, models, record_id='test.matched.model-freeze')
    index = ScheduledSourceIndex.from_shared(reservation=original_case.inputs.reservation,
        specification=original_case.inputs.native_specification, provenances=(original_case.provenance,))

    def forecast(unit, role, freeze, calibration=None):
        _, feature = causal(original_case, unit, source_index=index)
        pin = reference('matched.physical.' + unit, ConfiguredProtectedE3PhysicalForecast)
        feature = replace(feature, physical_forecast=pin, fine_response_defect=D('.002'), values=feature_values(feature, curve_primary=curve_primary),
            evidence=tuple(sorted((*feature.evidence, pin), key=lambda value: value.object_id)))
        return science.forecast_protected_e3(specification, allocation, models, freeze, feature,
            role=role, record_id='test.matched.forecast.' + unit, calibration=calibration)

    cal_fs = tuple(forecast(unit, 'calibration', frozen) for unit in allocation.unit_ids('calibration'))
    cal_ys = tuple(outcome(row, missing=ordinal < 3) for ordinal, row in enumerate(cal_fs))
    calibration = science.calibrate_protected_e3(specification, allocation, models, frozen, cal_fs, cal_ys,
        record_id='test.matched.calibration')
    assert tuple(row.method_key for row in calibration.model_calibrations) == ('B0', 'S0')
    assert all(row.rank == 62 and row.radius is None for row in calibration.model_calibrations)
    assert all(policy.bound_kind == 'UNCALIBRATED' for row in cal_fs for policy in row.policies)
    sealed = science.freeze_protected_e3(specification, allocation, models, record_id='test.matched.calibration-freeze',
        model_freeze=frozen, calibration=calibration)
    return SimpleNamespace(specification=specification, inputs=inputs, allocation=allocation, joined=joined, models=models,
        frozen=frozen, calibration=calibration, sealed=sealed, forecast=forecast, cal_fs=cal_fs, cal_ys=cal_ys, index=index)


def test_native_schema_protected_matched_fit_freeze_calibrate_confirm_and_full_unknown_read(original_case, matched_e3_products, monkeypatch):
    f = matched_e3_products
    specification, allocation, joined, models = f.specification, f.allocation, f.joined, f.models
    frozen, calibration, sealed, forecast, cal_fs, cal_ys = f.frozen, f.calibration, f.sealed, f.forecast, f.cal_fs, f.cal_ys
    index = f.index
    fs = tuple(forecast(unit, 'evaluation', sealed, calibration) for unit in allocation.unit_ids('evaluation'))
    ys = tuple(outcome(row, missing=ordinal == 0) for ordinal, row in enumerate(fs))
    result = science.assess_protected_e3(specification, allocation, sealed, fs, ys, record_id='test.matched.assessment')
    assert result.amended_inference.events[0] is None and not result.criterion_met
    assert len(result.decisions) == len(allocation.unit_ids('evaluation'))
    assert all(policy.bound_kind == 'INFINITE' and not any(policy.admissions) for row in fs for policy in row.policies)
    assert conditional_reasons(specification, allocation, result)
    assert all(row['upper95_worst_case_failure_probability'] is None for row in matched.matched_admission_risk(fs, ys))
    from empirical_lawhood.adapters.methods.matrix_factor_response.curve_prediction import curve_loss_summary
    summary = curve_loss_summary if specification.is_curve_primary else matched.matched_loss_summary
    assert summary(result.decisions)['unknown_groups' if specification.is_curve_primary else 'unknown_units'] == 1
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.configured_selected_package import ConfiguredMatrixSelectedFrozenPackage
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.configured_selected_public import ConfiguredMatrixSelectedPublicPackage
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_package import predict_selected_points
    package = ConfiguredMatrixSelectedFrozenPackage('test.matched.export', specification, allocation, joined, models,
        frozen, calibration, sealed, tuple(sorted((*allocation.unit_ids('calibration'), *allocation.unit_ids('evaluation')))))
    public = ConfiguredMatrixSelectedPublicPackage.from_package(package)
    assert len(package.endpoint_order) == 58
    assert public.predict(values=fs[0].feature.values, disposition='AVAILABLE') == fs[0].log_points
    assert predict_selected_points(package, values=fs[0].feature.values) == fs[0].log_points
    for record in (models, frozen, calibration, sealed, fs[0], ys[0], result, package, public):
        assert decode_canonical_bytes(record.canonical_bytes(), type(record), maximum_bytes=None) == record
    rows = {row.feature.unit_id: {'forecast': row, 'outcome': value, 'state': 'RECEIVED'}
        for row, value in zip((*cal_fs, *fs), (*cal_ys, *ys), strict=True)}
    # The incomplete reader preserves both complete rank denominators even if
    # an authenticated contact has no forecast/outcome product at all.
    rows[cal_fs[0].feature.unit_id] = {'state': 'UNKNOWN_CONTACT'}
    rows[fs[0].feature.unit_id] = {'state': 'UNKNOWN_CONTACT'}
    read = _denominator_math(specification, allocation, rows, {science.identity(frozen): frozen, science.identity(sealed): sealed})
    assert read['assessment']['amended_inference'] == result.amended_inference
    assert all(row.rank == 62 and row.radius is None for row in read['calibration']['separate_model_calibrations'])
    with pytest.raises(ValueError, match='complete assigned whole roots'):
        science.calibrate_protected_e3(specification, allocation, models, frozen, cal_fs[:-1], cal_ys[:-1], record_id='test.matched.thinned')

    # Exercise the post-authentication UNKNOWN projection with disclosed
    # operands. The mocked guard supplies no real access or contact authority.
    from empirical_lawhood.adapters.methods.matrix_factor_response import configured_protected_unknown_response as unknown
    from empirical_lawhood.adapters.methods.matrix_factor_response.origin_mechanics import MatrixOriginResponseModel, MatrixIO48Construction
    from empirical_lawhood.adapters.methods.matrix_factor_response.response_scoring import DENSE_RESPONSE_HORIZONS
    from empirical_lawhood.adapters.methods.matrix_factor_response.protected_secondary_readout import _checked_pair
    error = fs[0]
    source, _ = causal(original_case, error.feature.unit_id, source_index=index)
    from empirical_lawhood.adapters.methods.matrix_factor_response.records import MatrixFactorAction, ACTION_ROLES
    protocol = SimpleNamespace(public_source=error.feature.public_source, criterion=specification.identity,
        mechanical_model=MatrixOriginResponseModel('test.matched.unknown-model', response_records.physical_forecast_implementation(),
            MatrixIO48Construction('test.matched.unknown-io48')), horizon_steps=DENSE_RESPONSE_HORIZONS,
        actions=tuple(MatrixFactorAction('test.matched.unknown.' + role.lower(), role, D('.01'), 16, D(1)) for role in ACTION_ROLES))
    panels = tuple(SimpleNamespace(panel_id='test.matched.unknown.panel.' + str(i)) for i in range(2))
    values = dict(specification=specification, allocation=allocation, source=source, protocol=protocol, panels=panels,
        causal=SimpleNamespace(record_id=error.feature.prefix.object_id), physical=SimpleNamespace(), error=error)
    availability = SimpleNamespace(identity=reference('test.matched.unknown-contact', unknown.ConfiguredProtectedE3UnknownResponseAvailability),
        disposition='UNEVALUABLE')
    with monkeypatch.context() as controls:
        controls.setattr(unknown, '_validated_operands', lambda *_: (SimpleNamespace(source=source), values))
        controls.setattr(unknown, 'identity', lambda record: error.feature.prefix if record is values['causal'] else science.identity(record))
        original_object = unknown._object
        pins = {id(values['physical']): error.feature.physical_forecast,
            id(protocol): reference('test.matched.unknown.protocol', response_records.ScheduledResponseProtocol),
            **{id(panel): science.ObjectIdentity(panel.panel_id, response_records.ScheduledResponsePanel.SCHEMA,
                response_records.ScheduledResponsePanel.VERSION, 'b' * 64) for panel in panels}}
        controls.setattr(unknown, '_object', lambda record: pins[id(record)] if id(record) in pins else original_object(record))
        score, observed = unknown.score_unknown_response(availability, object(),
            score_id='test.matched.unknown-score', outcome_id='test.matched.unknown-outcome')
    assert len(score.cells) == 3248 and score.cumulative_log_errors == (None,) * 58
    assert all(view.errors == (None,) * 29 and view.dispositions == ('UNKNOWN_CONTACT',) * 29 for view in observed.views)
    _checked_pair(specification, allocation, 'evaluation', observed, error, score)
    assert decode_canonical_bytes(observed.canonical_bytes(), type(observed), maximum_bytes=None) == observed
