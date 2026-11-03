# SPDX-License-Identifier: MPL-2.0
"""Disclosed numerical controls; these rows have no source or qualification."""
from dataclasses import replace
from decimal import Decimal as D

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response.configured_specification import matched_e3_estimators
from empirical_lawhood.adapters.methods.matrix_factor_response.matched_response_prediction import MATCHED_FEATURES, MATCHED_FEATURE_BLOCKS
from empirical_lawhood.adapters.methods.matrix_factor_response.matched_response_fitting import (
    MatchedTrainingRow, fit_matched_models, fit_ridge_bundle, predict_bundle,
)
from empirical_lawhood.kernel.decoding import decode_canonical_bytes


def rows64():
    return tuple(MatchedTrainingRow('test.root.%02d' % index, 'test.root.%02d' % index, 'test.family',
        tuple((name, D(index + 1) if ordinal % 3 == 0 else D(ordinal))
            for ordinal, name in enumerate(MATCHED_FEATURES)), (D('.02'),) * 58, ()) for index in range(64))


def fit(rows):
    groups = tuple(row.group_id for row in rows)
    return fit_matched_models(rows, assigned_groups=groups,
        folds=tuple((group, index % 2) for index, group in enumerate(groups)),
        method_features=tuple((method.method_key, tuple(sorted(name for block in method.feature_blocks
            for name in MATCHED_FEATURE_BLOCKS[block]))) for method in matched_e3_estimators()))


def test_common58_fits_are_fold_local_and_keep_exact_fit_budget_and_tie_rule():
    rows = rows64()
    models = {model.method_key: model for model in fit(rows)}
    for method in ('S0', 'B0', 'SHARED_BASE'):
        model = models[method]
        assert len(model.cross_validation) + 1 == 5
        assert len(model.fit_attempts) == 5 and all(attempt.disposition == 'FITTED' for attempt in model.fit_attempts)
        assert model.parameters.diagnostics.penalty == D(1)
        assert model.finite_counts == (64,) * 58
        assert all(count == 1 for _, _, count in model.parameters.diagnostics.row_groups)
        first = model.cross_validation[0]
        assert first.held_out_fold == 0
        assert first.diagnostics.fitting_groups == tuple(row.group_id for row in rows[1::2])
        expected = np.asarray([[float(dict(row.features)[name]) for name in model.feature_names] for row in rows[1::2]])
        np.testing.assert_allclose(np.asarray(first.diagnostics.means, dtype=float), expected.mean(axis=0))
        assert all(numerator == 0 and denominator == 58 for _, numerator, denominator in first.group_losses)
        assert decode_canonical_bytes(model.canonical_bytes(), type(model), maximum_bytes=2_000_000) == model
    assert len(models['S0'].feature_names) == len(models['B0'].feature_names) == 22
    # Changing a held-out value cannot alter this fit's scaler or coefficients.
    changed = replace(rows[0], features=tuple((name, value * 100) for name, value in rows[0].features))
    other = {model.method_key: model for model in fit((changed, *rows[1:]))}
    assert other['S0'].cross_validation[0].diagnostics == models['S0'].cross_validation[0].diagnostics


def test_one_missing_target_excludes_the_same_whole_roots_from_every_arm_without_redrawing_folds():
    rows = rows64()
    rows = tuple(replace(row, errors=(None, *row.errors[1:])) if index < 16 else row for index, row in enumerate(rows))
    models = fit(rows)
    assert all(model.complete_group_ids == tuple(row.group_id for row in rows[16:]) for model in models)
    assert all(len(model.exclusions) == 16 and not model.prerequisite_reasons for model in models)
    # The threshold is 48, with 24 in each original fold. A 47th fit does not run.
    failed = fit((*rows[:16], replace(rows[16], reasons=('NUMERICAL_FAILURE',)), *rows[17:]))
    for model in failed:
        assert model.parameters is None and not model.cross_validation
        assert 'INSUFFICIENT_COMMON_COMPLETE_GROUPS' in model.prerequisite_reasons
        assert 'INSUFFICIENT_COMMON_COMPLETE_FOLD_0' in model.prerequisite_reasons


def test_weighted_bundle_matches_an_independent_normal_equation_with_unpenalized_intercept():
    rows = tuple(MatchedTrainingRow('test.row.%d' % index, 'test.group.a' if index == 0 else 'test.group.b',
        'test.family', (('constant', D(7)), ('x', D(index))), (D(index) / 100 + D('.001'),) * 58, ()) for index in range(4))
    model = fit_ridge_bundle(rows, ('constant', 'x'), D(10))
    weights = np.array([1., 1/3, 1/3, 1/3])
    x = np.array([0., 1., 2., 3.])
    mean = np.average(x, weights=weights)
    scale = np.sqrt(np.average((x - mean)**2, weights=weights))
    design = np.column_stack((np.ones(4), np.zeros(4), (x - mean) / scale))
    y = np.log1p(np.array([.001, .011, .021, .031]))
    expected = np.linalg.solve(design.T @ (weights[:, None] * design) + np.diag([0., 10., 10.]), design.T @ (weights * y))
    np.testing.assert_allclose(float(model.intercepts[0]), expected[0], rtol=1e-13)
    np.testing.assert_allclose(np.array(model.coefficients, dtype=float)[:, 0], expected[1:], atol=1e-14)
    assert model.diagnostics.zero_variance_mask == (True, False)
    assert model.diagnostics.scales[0] == 1 and model.diagnostics.design_rank == 2
    assert float(model.diagnostics.effective_degrees_of_freedom) == pytest.approx(1 + 2/12)
    assert len(predict_bundle(model, rows[-1].features, ('constant', 'x'))) == 58


def test_unrepresentable_complete_training_values_keep_failure_without_retry_or_new_groups():
    rows = rows64()
    bad = replace(rows[0], features=tuple((name, D('1e400')) for name, _ in rows[0].features))
    models = fit((bad, *rows[1:]))
    for model in models:
        assert model.complete_group_ids == tuple(row.group_id for row in rows) and not model.exclusions
        if model.method_key == 'RAW_TRAIN_MEDIAN':
            assert not model.fit_attempts and model.raw_constants == (D('.02'),) * 58
            continue
        assert model.parameters is None and model.prerequisite_reasons == ('NUMERICALLY_UNEVALUABLE',)
        assert not model.cross_validation and len(model.fit_attempts) == 1
        assert model.fit_attempts[-1].held_out_fold == 0 and model.fit_attempts[-1].disposition == 'NUMERICALLY_UNEVALUABLE'
        assert model.fit_attempts[-1].diagnostics is not None  # fit succeeded; held-out evaluation could not
        assert decode_canonical_bytes(model.canonical_bytes(), type(model), maximum_bytes=None) == model


def test_failed_second_svd_retains_completed_fold_and_stops_that_account(monkeypatch):
    original, calls = np.linalg.svd, []
    def svd(*args, **kwargs):
        calls.append(None)
        if len(calls) == 2:
            raise np.linalg.LinAlgError('disclosed failed second fit')
        return original(*args, **kwargs)
    monkeypatch.setattr(np.linalg, 'svd', svd)
    models = {model.method_key: model for model in fit(rows64())}
    failed = models['B0']
    assert len(failed.cross_validation) == 1 and len(failed.fit_attempts) == 2
    assert failed.parameters is None and failed.fit_attempts[-1].diagnostics is None
    assert failed.prerequisite_reasons == ('NUMERICALLY_UNEVALUABLE',)
    assert models['S0'].parameters is not None and len(models['S0'].fit_attempts) == 5
    assert len(calls) == 12  # B0 stops after2; S0 and the shared control each use5.
