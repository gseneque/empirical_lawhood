# SPDX-License-Identifier: MPL-2.0
"""Disclosed numerical controls; no native, fresh or prospective evidence."""
from dataclasses import replace
from decimal import Decimal as D, localcontext
from hashlib import sha256
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history import e4_structural_prediction as science
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_records as original
from empirical_lawhood.adapters.methods.matrix_scheduled_history.forecast import FAMILY_MAP
from empirical_lawhood.adapters.methods.matrix_scheduled_history.full_factor_secondary_readout import OriginalFunctionalRows
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_selection import physical_grid_features
from empirical_lawhood.kernel.decoding import decode_canonical_bytes, decode_canonical_record
from empirical_lawhood.kernel.provenance import ObjectIdentity
from tests.test_matrix_selected_e4_fixtures import selected_e4_populations, selected_bridge, transfer  # noqa: F401
from tests.test_matrix_programme_scientific_design import build_scientific_design


def pin(name, schema):
    return ObjectIdentity(name, schema, '1.0.0', sha256(name.encode()).hexdigest())


def records(programme):
    groups = {group: index for index, group in enumerate(programme.group_ids)}
    with localcontext() as context:
        context.prec = 80
        result = []
        for case in programme.cases:
            signal = D(groups[case.independent_group_id] + 1) / 10
            values = tuple((name, signal) for name in science.STRUCTURAL_FEATURES)
            errors = tuple((D('.03') + signal / 10 + case.factor_values[0] / 100
                + D(view) / 1000 + D(horizon) / 10000).exp() - 1
                for view in range(2) for horizon in science.E4_OBSERVATION_HORIZONS)
            result.append(science.E4StructuralPredictionCase('prediction.' + case.root_id,
                pin('original.' + case.root_id, 'empirical-lawhood/testing/original-case'), case.source, case.root_id,
                case.independent_group_id, case.coordinate,
                pin('account.' + case.root_id, 'empirical-lawhood/testing/original-seal'),
                pin('feature.' + case.root_id, 'empirical-lawhood/testing/original-feature'), 'AVAILABLE', values,
                128, 16, 256, 'FINITE', errors, (True,) * science.ENDPOINTS))
        return tuple(result)


@pytest.fixture(scope='module')
def comparison(selected_e4_populations):  # noqa: F811
    f = selected_e4_populations
    choices = build_scientific_design().e4_revision
    groups = {}
    for case in f.development.cases:
        groups.setdefault(case.family_id, set()).add(case.independent_group_id)
    slots = tuple((family, ordinal, ordinal % 2) for family, values in sorted(groups.items())
        for ordinal, _ in enumerate(sorted(values)))
    choices = replace(choices, fold_slots=slots)
    selection = science.selected_structural_prediction('prediction.disclosed.selected')
    dev, cal = records(f.development), records(f.calibration)
    result = science.structural_prediction_comparison(selection, choices, f.development, dev,
        evaluation=(('CALIBRATION', f.calibration, cal),))
    return SimpleNamespace(populations=f, choices=choices, selection=selection, dev=dev, cal=cal, result=result)


def model(arm):
    return decode_canonical_record(arm['final_model'], science.E4StructuralPredictionModel)


def decimal(value):
    return D(value['decimal'])


def test_two_arm_fit_uses_same_whole_group_folds_and_independent_normal_equation_oracle(comparison):
    f = comparison
    physical, structural = f.result['arms']
    assert [arm['fit_calls'] for arm in (physical, structural)] == [5, 5]
    assert all(arm['endpoint_regressions_per_bundle'] == 58 for arm in (physical, structural))
    assert physical['fit_attempts'][:4] == structural['fit_attempts'][:4]
    assert physical['fit_attempts'][-1]['training_groups'] == structural['fit_attempts'][-1]['training_groups']
    assert set(f.result['complete_common_groups']) == set(f.populations.development.group_ids)
    for attempt in structural['fit_attempts'][:4]:
        assert not set(attempt['training_groups']).intersection(attempt['heldout_groups'])
        assert set(attempt['training_groups']) | set(attempt['heldout_groups']) == set(f.populations.development.group_ids)
    fitted = model(structural)
    cases = f.populations.development.cases
    by_root = {row.root_id: row for row in f.dev}
    x = np.asarray([[float(({**physical_grid_features(f.populations.development.factors, case.factor_values),
        **dict(by_root[case.root_id].feature_values)})[name]) for name in fitted.feature_names] for case in cases])
    y = np.asarray([np.log1p(float(by_root[case.root_id].cumulative_errors[0])) for case in cases])
    means, scales = x.mean(axis=0), x.std(axis=0)
    scales[scales == 0] = 1
    z = np.column_stack((np.ones(len(x)), (x-means)/scales))
    regularization = np.eye(z.shape[1]) * float(fitted.penalty)
    regularization[0, 0] = 0
    expected = np.linalg.solve(z.T @ z + regularization, z.T @ y)
    assert np.allclose([float(value) for value in fitted.parameters[0].coefficients], expected, rtol=1e-10, atol=1e-12)
    assert decimal(structural['evaluation'][1]['mean_group_mse']) < decimal(physical['evaluation'][1]['mean_group_mse'])
    assert fitted.training_groups == f.populations.development.group_ids
    assert decode_canonical_bytes(fitted.canonical_bytes(), type(fitted), maximum_bytes=None) == fitted


def test_calibration_targets_cannot_change_standardization_selection_or_final_dev_fit(comparison):
    f = comparison
    changed = tuple(replace(row, cumulative_errors=tuple(value + 100 for value in row.cumulative_errors)) for row in f.cal)
    result = science.structural_prediction_comparison(f.selection, f.choices, f.populations.development, f.dev,
        evaluation=(('CALIBRATION', f.populations.calibration, changed),))
    for before, after in zip(f.result['arms'], result['arms'], strict=True):
        assert before['final_model'] == after['final_model']
        assert before['candidates'] == after['candidates']
        assert before['evaluation'][1]['mean_group_mse'] != after['evaluation'][1]['mean_group_mse']
        assert after['evaluation'][1]['scope'] == 'HELD_OUT_DESCRIPTIVE_REPLAY'
        assert after['evaluation'][1]['new_before_outcome_prediction_seal'] is False


def test_missing_coordinate_excludes_entire_common_group_and_retains_assigned_denominator(comparison):
    f = comparison
    missing = replace(f.dev[0], feature_disposition='UNAVAILABLE', feature_values=())
    rows = (missing, *f.dev[1:])
    result = science.structural_prediction_comparison(f.selection, f.choices, f.populations.development, rows)
    assert result['assigned_groups'] == len(f.populations.development.group_ids)
    assert len(result['complete_common_groups']) == result['assigned_groups'] - 1
    assert result['excluded_groups'] == [{'group_id': missing.group_id, 'incomplete_roots': [missing.root_id]}]
    for arm in result['arms']:
        assert missing.group_id not in model(arm).training_groups
        assert len(arm['evaluation'][0]['predictions']) == len(f.dev)
        assert arm['evaluation'][0]['population_inference'] == 'NOT_ESTABLISHED_FROM_COMPLETE_CASES'
    with pytest.raises(ValueError, match='denominator'):
        science.structural_prediction_comparison(f.selection, f.choices, f.populations.development, rows[1:])


def test_empty_whole_fold_and_unusable_response_never_become_finite_target_or_censor(comparison):
    f = comparison
    folds = science.bind_group_fold_slots(f.populations.development, f.choices.fold_slots, 2)
    absent = {fold.unit_id for fold in folds if fold.fold == 0}
    rows = tuple(replace(row, response_disposition='NATIVE_CROSSCHECK_FAILED')
        if row.group_id in absent else row for row in f.dev)
    result = science.structural_prediction_comparison(f.selection, f.choices, f.populations.development, rows)
    assert len(result['excluded_groups']) == len(absent)
    assert all(arm['status'] == 'NOT_ESTABLISHED' and arm['fit_calls'] == 0 for arm in result['arms'])
    assert all(arm['final_model'] is None and arm['evaluation'] == [] for arm in result['arms'])


def test_exact_selection_and_sampled_tau_meaning():
    selection = science.selected_structural_prediction('prediction.disclosed.roundtrip')
    assert decode_canonical_bytes(selection.canonical_bytes(), type(selection), maximum_bytes=None) == selection
    for changes in ({'penalties': (D(1), D(100))}, {'fold_count': 3}, {'structural_features': ('new-feature',)},
                    {'maximum_fit_calls_per_arm': 6}, {'target': 'EXACT_CENSORED_TAU'}):
        with pytest.raises(ValueError):
            replace(selection, **changes)
    with localcontext() as context:
        context.prec = 80
        boundary = (1 + D('.01')).ln()
        result = science._tau((boundary,) * 29 + (boundary, boundary + D('.001')) + (boundary + D('.001'),) * 27)
    assert result[0]['first_predicted_strict_exceedance'] is None
    assert result[0]['classification'] == 'MODEL_PREDICTED_NO_EXCEEDANCE_WITHIN_GRID'
    assert result[1]['first_predicted_strict_exceedance'] == 20
    assert result[1]['last_predicted_pass'] == 16
    assert all(row['observed_event_or_continuous_time_bound'] is False for row in result)


def test_original_sealed_feature_join_refuses_substituted_cutoff_or_account(selected_bridge):  # noqa: F811
    from tests.test_matrix_selected_point import feature
    f = selected_bridge
    case = f.programme.cases[0]
    source = f.bank.source(case.root_id, index=f.bank.source_index())
    prefix = pin('prefix.prediction.disclosed', original.SelectedE3E4CausalPrefix.SCHEMA)
    values = feature(f.selected, f.selected.sources[0][1]).values
    observed = original.SelectedE3E4Feature('feature.prediction.disclosed', case.source, prefix,
        case.root_id, case.independent_group_id, FAMILY_MAP[source.coordinate.family_id],
        source.coordinate.clock_id, source.coordinate.physical_time(source.policy.cutoff_tick), 'b' * 64, 'AVAILABLE', values)
    account = original.SelectedE3E4AccountSeal('account.prediction.disclosed', f.bank.forecast_design.identity,
        case.source, prefix, observed, f.selected.package.identity,
        original.identity(f.selected.package.calibration),
        f.bank.forecast_design.package.predict(values=values, disposition='AVAILABLE'))
    original_case = replace(original.SelectedE3E4CaseResult.unentered(case), forecast=account.identity,
        original_log_points=account.log_points)
    count = 2 * 5 * 29
    row = OriginalFunctionalRows(ObjectIdentity.from_record(case.root_id, original_case), case.source,
        case.root_id, case.independent_group_id, case.coordinate, source.policy.cutoff_tick, None, prefix,
        'UNAVAILABLE', (None,) * count, account.log_points,
        observation_horizons=science.E4_OBSERVATION_HORIZONS, cumulative_complete=(False,) * count)
    result = science.prediction_case(f.bank, original_case, row, account)
    assert dict(result.feature_values) == {name: dict(values)[name] for name in science.STRUCTURAL_FEATURES}
    assert result.causal_account == account.identity and not result.complete
    assert result.feature_window_ticks == f.bank.forecast_design.package.specification.measurement.feature_window_ticks
    with pytest.raises(PermissionError, match='actual original account'):
        science.prediction_case(f.bank, original_case, row, None)
    moved = replace(account, feature=replace(observed, cutoff=observed.cutoff + D('.001')))
    moved_case = replace(original_case, forecast=moved.identity)
    moved_row = replace(row, original_case=ObjectIdentity.from_record(case.root_id, moved_case))
    with pytest.raises(PermissionError, match='cutoff or seal'):
        science.prediction_case(f.bank, moved_case, moved_row, moved)


def test_whole_programme_report_requires_complete_authenticated_comparison_operands():
    from empirical_lawhood.api.matrix_programme_structural_prediction import programme_structural_prediction
    design = SimpleNamespace(e4_structure=SimpleNamespace(prediction=science.selected_structural_prediction('prediction.disclosed.missing')))
    assert programme_structural_prediction(SimpleNamespace(observations={}, design=design))['status'] == 'DEPENDENCIES_REQUIRED'
    context = SimpleNamespace(design=design, observations={'e4.development': SimpleNamespace(report={
        'structure': {'scientific_completion': 'COMPLETE_ORIGINAL_FULL_FACTOR_CENSUS'}})})
    with pytest.raises(PermissionError, match='causal prediction cases'):
        programme_structural_prediction(context)


@pytest.mark.parametrize('when', ('before-fit', 'during-fit'))
def test_report_keeps_current_access_through_comparison(comparison, monkeypatch, when):
    from contextlib import nullcontext
    from empirical_lawhood.api import matrix_programme_structural_prediction as report_owner, matrix_programme_products
    f = comparison
    programme = f.populations.development
    structure = {'scientific_completion': 'COMPLETE_ORIGINAL_FULL_FACTOR_CENSUS',
        'original_programme': programme.to_document(), 'prediction_cases': tuple(row.to_document() for row in f.dev),
        'assigned_groups': len(programme.group_ids), 'assigned_cases': len(programme.cases)}
    writer = object()
    context = SimpleNamespace(observations={'e4.development': SimpleNamespace(report={'structure': structure})},
        writer=SimpleNamespace(read_context=lambda: nullcontext(writer)),
        plan=SimpleNamespace(specification=SimpleNamespace(operations=SimpleNamespace(
            metadata_budget=SimpleNamespace(source_scan_bytes=64 * 1024**2)))),
        design=SimpleNamespace(e4_structure=SimpleNamespace(prediction=f.selection), e4_revision=f.choices))
    revoked = when == 'before-fit'
    fitted = False
    def grants(actual, authority_writer):
        assert actual is context and authority_writer is writer
        def current():
            if revoked:
                raise PermissionError('disclosed grant revocation during report')
        current()
        return current
    def fit(*args, **kwargs):
        nonlocal revoked, fitted
        assert not revoked
        fitted, revoked = True, True
        return f.result
    monkeypatch.setattr(matrix_programme_products, '_current_grants', grants)
    monkeypatch.setattr(report_owner, 'structural_prediction_comparison', fit)
    with pytest.raises(PermissionError, match='revocation'):
        report_owner.programme_structural_prediction(context)
    assert fitted == (when == 'during-fit')
