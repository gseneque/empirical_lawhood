# SPDX-License-Identifier: MPL-2.0
"""Independent exposed arithmetic controls, with no acquisition or qualification."""
from dataclasses import replace
from decimal import Decimal as D, localcontext
from fractions import Fraction
from math import comb

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response.curve_prediction import (
    MatchedCurveDecision, curve_loss, curve_decision, group_curve_loss,
)
from empirical_lawhood.adapters.methods.matrix_factor_response.curve_contract import MECHANISM_FEATURES
from empirical_lawhood.adapters.methods.matrix_factor_response.matched_response_prediction import (
    MATCHED_FEATURES, MATCHED_METHODS, SHARED_FEATURES, STRUCTURAL_FEATURES, DRIFT_FEATURES,
    matched_primary_inference,
)
from empirical_lawhood.adapters.methods.matrix_factor_response.matched_response_fitting import (
    MatchedCurveEstimatorModel, MatchedCurveCrossValidationFit, fit_matched_models,
    MatchedTrainingRow, predict_bundle,
)
from empirical_lawhood.kernel.decoding import decode_canonical_bytes


def test_root_rms_matches_independent_array_oracle_and_equal_paired_view_weights():
    raw = np.linspace(-.003, .02, 58)
    targets = np.concatenate((np.linspace(.001, .05, 29), np.linspace(.003, .07, 29)))
    clipped = np.concatenate([np.maximum.accumulate(np.maximum(raw[start:start + 29], 0)) for start in (0, 29)])
    expected = np.sqrt(np.mean((clipped - np.log1p(targets)) ** 2)) / np.log1p(.01)
    points, errors = tuple(map(lambda value: D(repr(float(value))), raw)), tuple(map(lambda value: D(repr(float(value))), targets))
    actual = curve_loss(points, errors)
    assert float(actual) == pytest.approx(expected, rel=2e-15)
    # Precision and rounding are source-owned, independent of the caller context.
    with localcontext() as context:
        context.prec = 9
        context.rounding = 'ROUND_DOWN'
        assert curve_loss(points, errors) == actual
    assert curve_loss(points, (None, *errors[1:])) is None
    with pytest.raises(ValueError):
        curve_loss(points, (D('-1'), *errors[1:]))
    with pytest.raises(ValueError):
        curve_loss(points[:-1], errors)
    # E4 averages root RMS, not squared errors pooled across nine coordinates.
    losses = (D(0),) * 8 + (D(9),)
    assert group_curve_loss(losses) == 1
    assert float(group_curve_loss(losses)) != np.sqrt(np.mean(np.square(np.asarray(losses, dtype=float))))


def decision(index=0, *, success=True, usable=True):
    losses = tuple((method, (D('.1') if method == 'B0' and success else D(0),)) for method in MATCHED_METHODS)
    return MatchedCurveDecision('exposed.root.%03d' % index, 'S0', 1, usable, success and usable,
        losses, tuple((method, 0) for method in MATCHED_METHODS), ('EXPOSED_ARITHMETIC',), ('exposed.root.%03d' % index,))


def test_inclusive_curve_margin_is_distinct_from_secondary_K_and_keeps_unknown_denominator():
    row = decision()
    assert row.success and row.improvement == Fraction(1, 10) and row.duration_success is False
    with pytest.raises(ValueError, match='margin'):
        replace(row, curve_losses=tuple((method, (D('.099999999999999999999999999999'),) if method == 'B0' else losses)
            for method, losses in row.curve_losses))
    missing = {method: (None,) * 58 if method == 'B0' else (D(0),) * 58 for method in MATCHED_METHODS}
    unknown = curve_decision('exposed.missing', (missing,), ((D(0),) * 58,), ())
    assert not unknown.usable and not unknown.success and unknown.improvement is None
    assert decode_canonical_bytes(row.canonical_bytes(), MatchedCurveDecision, maximum_bytes=None) == row
    for n, critical in ((80, 52), (32, 24), (64, 43)):
        # Direct exact binomial arithmetic, independent of the production tail.
        assert sum(Fraction(comb(n, k), 2 ** n) for k in range(critical, n + 1)) <= Fraction(1, 160)
        assert sum(Fraction(comb(n, k), 2 ** n) for k in range(critical - 1, n + 1)) > Fraction(1, 160)
        inference = matched_primary_inference(tuple(decision(i, success=i < critical) for i in range(n)))
        assert inference.criterion_met
        assert not matched_primary_inference(tuple(decision(i, success=i < critical - 1) for i in range(n))).criterion_met


def test_curve_cross_validation_replays_root_losses_and_preserves_fold_local_five_fit_budget():
    features = tuple(sorted((*MATCHED_FEATURES, *MECHANISM_FEATURES)))
    rows = tuple(MatchedTrainingRow('exposed.root.%02d' % i, 'exposed.root.%02d' % i, 'exposed.family',
        tuple((name, D(i + 1) if j % 3 == 0 else D(j)) for j, name in enumerate(features)),
        tuple(D('.001') + D(i * i + h) / 100000 for h in range(58)), ()) for i in range(64))
    groups = tuple(row.group_id for row in rows)
    base = (*SHARED_FEATURES, *MECHANISM_FEATURES)
    selected = (('B0', tuple(sorted((*base, *DRIFT_FEATURES)))), ('RAW_TRAIN_MEDIAN', ()),
        ('S0', tuple(sorted((*base, *STRUCTURAL_FEATURES)))), ('SHARED_BASE', tuple(sorted(base))))
    models = fit_matched_models(rows, assigned_groups=groups, folds=tuple((group, i % 2) for i, group in enumerate(groups)),
        method_features=selected, curve_primary=True)
    for model in models:
        assert type(model) is MatchedCurveEstimatorModel
        assert decode_canonical_bytes(model.canonical_bytes(), MatchedCurveEstimatorModel, maximum_bytes=None) == model
        if model.method_key == 'RAW_TRAIN_MEDIAN':
            assert not model.fit_attempts
            continue
        assert len(model.fit_attempts) == 5
        assert len(model.feature_names) == (20 if model.method_key == 'SHARED_BASE' else 24)
        for fit in model.cross_validation:
            assert type(fit) is MatchedCurveCrossValidationFit
            assert len(fit.diagnostics.fitting_groups) == 32
            assert tuple(group for group, _ in fit.coordinate_losses) == groups[fit.held_out_fold::2]
            assert all(count == 1 for _, _, count in fit.diagnostics.row_groups)
        losses = {penalty: sum(Fraction(n, d) for fit in model.cross_validation if fit.diagnostics.penalty == penalty
            for _, n, d in fit.group_losses) / 64 for penalty in (D(1), D(10))}
        assert model.parameters.diagnostics.penalty == min(losses, key=lambda penalty: (losses[penalty], penalty))
        # Out-of-fold loss is a whole-root RMS of the actually postprocessed curve.
        from empirical_lawhood.adapters.methods.matrix_factor_response.matched_response_fitting import fit_ridge_bundle
        fit = model.cross_validation[0]
        original = fit_ridge_bundle(rows[1::2], model.feature_names, D(1))
        for row, (_, coordinate_losses) in zip(rows[::2], fit.coordinate_losses, strict=True):
            assert coordinate_losses == (curve_loss(predict_bundle(original, row.features, model.feature_names), row.errors),)


def test_median_K_headroom_uses_only_fitting_labels_and_lower_even_integer():
    from empirical_lawhood.adapters.methods.matrix_factor_response.curve_duration import duration_diagnostic
    def row(index, k):
        return MatchedTrainingRow('exposed.median.%02d' % index, 'exposed.median.%02d' % index, 'exposed.family', (),
            ((D('.001'),) * k + (D('.02'),) * (29 - k)) * 2, ())
    fitting = tuple(row(index, k) for index, k in enumerate((10, 11, 11, 12)))
    held = (row(4, 5), row(5, 29))
    diagnostic = duration_diagnostic(fitting, held, fitting_points={}, held_out_points={})
    assert diagnostic.median_counts == (11, 11)
    changed = duration_diagnostic(fitting, (row(4, 0), row(5, 0)), fitting_points={}, held_out_points={})
    assert changed.median_counts == diagnostic.median_counts
    assert duration_diagnostic(fitting[:2], (), fitting_points={}, held_out_points={}).median_counts == (10, 10)
    report = diagnostic.headroom(tuple(row.group_id for row in fitting), held_out=False, median=True)
    assert report['one_check_opportunities'] == 2 and report['assigned_groups'] == report['observed_groups'] == 4
    with pytest.raises(ValueError, match='held-out'):
        duration_diagnostic(fitting, fitting[:1], fitting_points={}, held_out_points={})


def test_later_median_K_keeps_unavailable_roots_and_complete_nine_coordinate_weights():
    from types import SimpleNamespace
    from empirical_lawhood.adapters.methods.matrix_factor_response.curve_duration import evaluation_median_K
    model = SimpleNamespace(duration_diagnostic=SimpleNamespace(median_counts=(11, 11)))
    def targets(k):
        return ((D('.001'),) * k + (D('.02'),) * (29 - k)) * 2
    report = evaluation_median_K(model, ('group.a', 'group.b'), tuple(
        ('coordinate.%02d' % i, 'group.a', targets(10 if i < 8 else 2), True) for i in range(9)), coordinate_count=9)
    assert report['assigned_groups'] == 2 and report['unknown_groups'] == 1
    assert report['paired_K_losses'] == (('group.a', (17, 261)), ('group.b', None))
    assert report['one_check_oracle_opportunities'] == 1
    with pytest.raises(ValueError, match='coordinate'):
        evaluation_median_K(model, ('group.a',), (('row.a', 'group.a', targets(11), True),
            ('row.b', 'group.a', targets(11), True)))


def test_curve_loss_retains_unrepresentable_numerics_as_unknown():
    assert curve_loss((D('1e999999'),) * 58, (D(0),) * 58) is None
    # A log prediction can remain usable even when its exp is unrepresentable.
    assert curve_loss((D('1e7'),) * 58, (D(0),) * 58).is_finite()
    menu = {method: (D('1e999999'),) * 58 for method in MATCHED_METHODS}
    row = curve_decision('exposed.overflow', (menu,), ((D(0),) * 58,), ())
    assert not row.usable and row.duration_success is False and row.duration_improvement_count == 0
    invalid = curve_decision('exposed.invalid-target', (menu,), ((D(0),) * 58,), ('NUMERICAL_FAILURE',))
    assert invalid.duration_success is None

