# SPDX-License-Identifier: MPL-2.0
"""Tiny exposed software controls, never a fit of actual scientific evidence."""

from dataclasses import replace
from decimal import Decimal as D, localcontext
from hashlib import sha256

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_factor_lifetime.records import FactorObservation
from empirical_lawhood.adapters.methods.matrix_factor_response.response_error_prediction import (
    ENDPOINTS, FEATURES, METHODS, ROOT_IDS, STRATA, SUBROLES, WARRANT,
    MatrixResponseErrorPredictionSpec, calibrate_error_model, development_roles,
    error_readout, fit_error_model, forecast_error, forecast_error_points, identity, origin_features,
    query_forecast_tolerance, rank_radius, readout_census, root_error_summaries,
)
from empirical_lawhood.adapters.methods.matrix_factor_response.response_frontier import MatrixResponseRootFrontier
from empirical_lawhood.adapters.methods.matrix_factor_response.response_population_statistics import MatrixResponseRootLossBounds
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from tests.test_matrix_response_population_statistics import spec as population_fixture


def obj(name, schema=None):
    return ObjectIdentity('software.error.' + name, schema or 'empirical-lawhood/tests/error-software-only',
                          '1.0.0', sha256(name.encode()).hexdigest())


def publication(record):
    # A checksum fixture is not a real guarded prior scientific publication.
    value = record if isinstance(record, ObjectIdentity) else identity(record)
    return ArtifactIdentity(value.object_id + '.exposed-fixture', 'exposed-software-only', value.object_schema,
                            value.object_fingerprint, 'application/json', 1)


@pytest.fixture(scope='module')
def spec():
    population = population_fixture.__wrapped__()
    roles = development_roles(population, record_id='software.error.roles')
    reservation = obj('physical-reserve')
    return MatrixResponseErrorPredictionSpec('software.error.spec', population, roles, publication(roles),
                                             reservation, publication(reservation))


def observation(tick, *, angle=D(1)):
    return FactorObservation(tick, 'AVAILABLE', True, True, True, None,
        D('.01'), D('.02'), D(2), angle, None, False, None)


def feature(spec, index, *, rotation=None, unavailable=False, future=()):
    selection = spec.population.selections[index]
    # No RNG/eigenspectrum/producer: four fixed matrices and their fixed signs.
    diagonal = np.diag([1., 2., -1., 3.]).astype('<c16')
    offdiag = np.asarray([[0, 1j, 0, 0], [-1j, 0, 1, 0], [0, 1, 0, 1j], [0, 0, -1j, 0]], dtype='<c16')
    base = np.stack((diagonal, offdiag, diagonal + offdiag))
    state = np.stack((np.stack((base, .7 * base)), np.stack((.2 * base, .3 * base)))) * (1 + index / 257)
    if rotation is not None:
        state = rotation @ state @ rotation.conj().T
    return origin_features(spec, selection, record_id='features.' + selection.root_id,
        evidence=(obj('authenticated-software-prefix'),), source=obj('source'), origin=obj('origin'),
        clock_id='software.error.clock', frame_sha256='a' * 64,
        context={'alpha-x': D('.666'), 'alpha-y': D('7.333'), 'bath-temperature': D(1),
                 'cross-gamma': D(1), 'friction': D(1), 'potential-m': D('.5')},
        state=state, spectrum=tuple(D(i) / 10 for i in range(15)),
        observations=(observation(0), observation(16), *future),
        unavailable_reason='exposed-required-input-absent' if unavailable else None)


def label(spec, index, predictor, horizon, *, missing=False, failure=False):
    selected = spec.population.selections[index]
    j = (16, 64, 128).index(horizon)
    nonuse = selected.disposition == 'NO_CAUSAL_ORIGIN'
    loss = D(index % 13 + j + 1) / 10
    disposition = ('NO_CAUSAL_ORIGIN' if nonuse else 'NATIVE_CROSSCHECK_FAILED' if failure
                   else 'UNKNOWN_CONTACT' if missing else 'CROSSCHECKED_FINITE')
    kind = 'KNOWN_NONUSE_INFINITY' if nonuse or failure else 'UNRESOLVED_INTERVAL' if missing else 'FINITE_POINT'
    return MatrixResponseRootLossBounds(f'labels.{selected.root_id}.{predictor.lower()}.h{horizon}',
        spec.population.identity, selected.root_id, selected.independent_group_id, selected.family_id,
        predictor, horizon, disposition, kind, None if nonuse or failure else D(0) if missing else loss,
        None if nonuse or failure or missing else loss,
        None if nonuse or missing else obj('frontier.' + selected.root_id, MatrixResponseRootFrontier.SCHEMA),
        (obj('exposed-label-custody'),), ('exposed-software-labelled-fixture',))


def inputs(spec, *, role=None, rotation=None, missing=False, failure=False, unavailable=False):
    roots = ROOT_IDS if role is None else tuple(r[0] for r in spec.roles.rows if r[3] == role)
    indices = tuple(ROOT_IDS.index(r) for r in roots)
    features = tuple(feature(spec, i, rotation=rotation, unavailable=unavailable) for i in indices)
    labels = tuple(label(spec, i, m, h, missing=missing, failure=failure) for i in indices for m, h in ENDPOINTS)
    return features, labels


@pytest.fixture(scope='module')
def corpus(spec):
    return inputs(spec)


def select(spec, corpus, role):
    roots = {r[0] for r in spec.roles.rows if r[3] == role}
    return tuple(f for f in corpus[0] if f.root_id in roots), tuple(y for y in corpus[1] if y.root_id in roots)


@pytest.fixture(scope='module')
def model(spec, corpus):
    return fit_error_model(spec, *select(spec, corpus, 'TRAIN'), method='ALL_ORIGIN', record_id='software.error.model')


def test_all_roots_exposed_exact_roles_and_observed_quarantine(spec):
    assert len(spec.roles.rows) == 256
    assert all(r[3] == 'TRAIN' and r[4] for r in spec.roles.rows[:2])
    assert spec.roles.exposure == 'EXPOSED_DEVELOPMENT_NONPROMOTABLE'
    for family in STRATA:
        assert tuple(sum(r[2] == family and r[3] == role for r in spec.roles.rows) for role in SUBROLES) == (32, 16, 16)
    with pytest.raises(ValueError, match='census'):
        replace(spec.roles, rows=spec.roles.rows[:-1])
    rows = list(spec.roles.rows)
    train = next(i for i, r in enumerate(rows) if i > 1 and r[2] == STRATA[0] and r[3] == 'TRAIN')
    cal = next(i for i, r in enumerate(rows) if r[2] == STRATA[0] and r[3] == 'CALIBRATION_DESCRIPTIVE')
    rows[train] = (*rows[train][:3], 'CALIBRATION_DESCRIPTIVE', rows[train][4])
    rows[cal] = (*rows[cal][:3], 'TRAIN', rows[cal][4])
    changed = replace(spec.roles, rows=tuple(rows))
    with pytest.raises(ValueError, match='substitutes'):
        replace(spec, roles=changed, roles_publication=publication(changed))


def test_proposed_identity_without_exact_prior_publication_cannot_enter_fit_spec(spec):
    with pytest.raises(ValueError, match='publication'):
        replace(spec, future_regime_reservation=obj('renamed-reserve'))
    with pytest.raises(ValueError, match='publication'):
        replace(spec, roles_publication=replace(spec.roles_publication, sha256='b' * 64))
    with pytest.raises(ValueError, match='warrant'):
        replace(spec, sampling_warrant='SATISFIED')


def test_only_pre_cutoff_channels_and_future_changes_leave_features_identical(spec):
    ordinary = feature(spec, 0)
    # Full future measurements are changed severely, without changing prefix.
    adversarial = feature(spec, 0, future=(observation(32, angle=D(999)), observation(48, angle=D(888))))
    assert ordinary.canonical_bytes() == adversarial.canonical_bytes()
    assert tuple(k for k, _ in ordinary.values) == FEATURES
    selected = spec.population.selections[0]
    refused = origin_features(spec, selected, record_id='software.missing', evidence=(obj('prefix'),),
                              observations=(observation(16),), unavailable_reason='missing-prefix')
    assert refused.disposition == 'UNAVAILABLE' and not refused.values
    with pytest.raises(ValueError, match='cutoff'):
        from empirical_lawhood.adapters.methods.matrix_factor_response.response_error_prediction import _validate_feature
        _validate_feature(spec, replace(ordinary, cutoff=D('.032')))


@pytest.mark.parametrize('boundary_angle', (D(1), D(70), None))
def test_trailing_window_excludes_preceding_interval_and_accepts_restart(spec, monkeypatch, boundary_angle):
    selected = replace(spec.population.selections[0], origin_tick=48, cutoff=D('.048'))
    population = replace(spec.population, selections=(selected, *spec.population.selections[1:]))
    roles = development_roles(population, record_id=spec.roles.record_id)
    revised = replace(spec, population=population, roles=roles, roles_publication=publication(roles))
    original = observation
    monkeypatch.setitem(globals(), 'observation', lambda tick, **kwargs:
        original(tick, angle=boundary_angle if tick == 16 else kwargs.get('angle', D(1))))
    value = feature(revised, 0, future=(original(32), original(48)))
    assert value.disposition == 'AVAILABLE' and dict(value.values)['trailing-angle'] == D(1)
    future = feature(revised, 0, future=(original(32), original(48), original(64, angle=D(999))))
    assert value.canonical_bytes() == future.canonical_bytes()
    missing = feature(revised, 0, future=(original(32, angle=None), original(48)))
    assert missing.disposition == 'REFUSED' and not missing.values


def test_missing_causal_angle_refuses_instead_of_imputing_zero(spec):
    selected = spec.population.selections[0]
    state = np.zeros((2, 2, 3, 4, 4), dtype='<c16')
    refused = origin_features(spec, selected, record_id='software.missing-angle',
        evidence=(obj('prefix'),), source=obj('source'), origin=obj('origin'),
        clock_id='software.clock', frame_sha256='a' * 64,
        context={'alpha-x': D(1), 'alpha-y': D(1), 'bath-temperature': D(1),
                 'cross-gamma': D(1), 'friction': D(1), 'potential-m': D('.5')},
        state=state, spectrum=tuple(D(i) for i in range(15)),
        observations=(observation(0, angle=None), observation(16, angle=None)))
    assert refused.disposition == 'REFUSED' and refused.values == ()


def test_family_and_feature_clock_values_join_actual_selection(spec, model):
    ordinary = feature(spec, 0)
    for key, value in (('cutoff', D('.999')), ('family-de-anneal', D(1))):
        changed = replace(ordinary, values=tuple((name, value if name == key else old)
                                                for name, old in ordinary.values))
        with pytest.raises(ValueError, match='actual cutoff|preparation family'):
            forecast_error(spec, model, changed, record_id='software.substitution')


@pytest.mark.parametrize('method', METHODS)
def test_actual_fixed_estimator_and_train_standardisation_covariant_on_conjugated_corpus(spec, corpus, method):
    original = fit_error_model(spec, *select(spec, corpus, 'TRAIN'), method=method, record_id='software.original')
    a = 1 / np.sqrt(2)
    rotation = np.asarray([[a, a, 0, 0], [-a, a, 0, 0], [0, 0, 1j, 0], [0, 0, 0, 1]], dtype='<c16')
    assert np.allclose(rotation @ rotation.conj().T, np.eye(4), rtol=0, atol=1e-15)
    conjugated = inputs(spec, role='TRAIN', rotation=rotation)
    transformed = fit_error_model(spec, *conjugated, method=method, record_id='software.transformed')
    np.testing.assert_allclose(tuple(map(float, original.means)), tuple(map(float, transformed.means)), rtol=0, atol=1e-12)
    np.testing.assert_allclose(tuple(map(float, original.scales)), tuple(map(float, transformed.scales)), rtol=0, atol=1e-12)
    np.testing.assert_allclose(np.asarray(original.coefficients, dtype=float), np.asarray(transformed.coefficients, dtype=float), rtol=0, atol=1e-11)
    point = forecast_error(spec, original, feature(spec, 3), record_id='software.point')
    conjugate = forecast_error(spec, transformed, feature(spec, 3, rotation=rotation), record_id='software.conjugate')
    np.testing.assert_allclose(np.asarray(point.log_error_points, dtype=float), np.asarray(conjugate.log_error_points, dtype=float), rtol=0, atol=1e-12)
    assert not any(v is not None for v in point.log_error_uppers)


def test_training_only_and_thinned_foreign_role_labels_refuse_before_solver(spec, corpus, monkeypatch):
    from empirical_lawhood.adapters.methods.matrix_factor_response import response_error_prediction as owner
    def forbidden(*args, **kwargs):
        raise AssertionError('solver entered before scientific role/label admission')
    monkeypatch.setattr(owner.np.linalg, 'solve', forbidden)
    training = select(spec, corpus, 'TRAIN')
    calibration = select(spec, corpus, 'CALIBRATION_DESCRIPTIVE')
    for fs, ys in ((corpus[0], training[1]), (training[0], calibration[1]), (training[0], training[1][:-1])):
        with pytest.raises(ValueError, match='roles|endpoints'):
            fit_error_model(spec, fs, ys, method='ALL_ORIGIN', record_id='software.invalid')


def test_context_comparator_is_literal_family_mean_with_empty_family_refusal(spec, corpus, monkeypatch):
    from empirical_lawhood.adapters.methods.matrix_factor_response import response_error_prediction as owner
    def forbidden(*args, **kwargs):
        raise AssertionError('literal family mean must not call the ridge solver')
    monkeypatch.setattr(owner.np.linalg, 'solve', forbidden)
    fs, ys = select(spec, corpus, 'TRAIN')
    context = fit_error_model(spec, fs, ys, method='CONTEXT', record_id='software.family-mean')
    for family in STRATA:
        root_feature = next(f for f in fs if f.stratum_id == family and f.disposition == 'AVAILABLE')
        prediction = forecast_error(spec, context, root_feature, record_id='software.context-point')
        finite = tuple(y for y in ys if y.stratum_id == family and y.bound_kind == 'FINITE_POINT'
                       and (y.predictor, y.horizon_step) == ENDPOINTS[0])
        expected = sum((D(1) + y.lower_loss).ln() for y in finite) / len(finite)
        assert abs(prediction.raw_log_error_points[0] - expected) < D('1e-14')
    changed = tuple(replace(y, disposition='UNKNOWN_CONTACT', bound_kind='UNRESOLVED_INTERVAL',
                            lower_loss=D(0), upper_loss=None, frontier=None)
                    if y.stratum_id == STRATA[1] else y for y in ys)
    incomplete = fit_error_model(spec, fs, changed, method='CONTEXT', record_id='software.empty-family')
    prediction = forecast_error(spec, incomplete, next(f for f in fs if f.stratum_id == STRATA[1]),
                                record_id='software.empty-family-point')
    assert prediction.disposition == 'NO_FINITE_MODEL'
    assert all(p is None for p in prediction.log_error_points)


def test_ridge_lambda_one_and_unpenalised_intercept_against_two_group_solution(spec, corpus):
    fs, ys = select(spec, corpus, 'TRAIN')
    changed_features = []
    for f in fs:
        if f.root_id in ROOT_IDS[:2]:
            x = D(0) if f.root_id == ROOT_IDS[0] else D(2)
            values = tuple((name, x if name == 'position-x-norm' else D(0)
                           if name.endswith('-norm') else value) for name, value in f.values)
            changed_features.append(replace(f, values=values))
        elif f.disposition == 'AVAILABLE':
            changed_features.append(replace(f, disposition='UNAVAILABLE', values=()))
        else:
            changed_features.append(f)
    changed_labels = tuple(replace(y, lower_loss=(D(2 if y.root_id == ROOT_IDS[0] else 4)
                            + D((16, 64, 128).index(y.horizon_step))).exp() - 1,
                            upper_loss=(D(2 if y.root_id == ROOT_IDS[0] else 4)
                            + D((16, 64, 128).index(y.horizon_step))).exp() - 1)
                           if y.root_id in ROOT_IDS[:2] else y for y in ys)
    fitted = fit_error_model(spec, tuple(changed_features), changed_labels,
                             method='NORM_RADIUS', record_id='software.ridge-golden')
    j = fitted.feature_names.index('position-x-norm')
    # Standardised x=(-1,+1), y=(2,4): intercept3 and slope2/(2+lambda).
    assert fitted.means[j] == fitted.scales[j] == 1
    assert abs(fitted.coefficients[0][0] - D(3)) < D('1e-14')
    assert abs(fitted.coefficients[0][j + 1] - D(2) / 3) < D('1e-14')
    assert fitted.endpoint_finite_group_counts == (2,) * 15
    assert all(abs(v) < D('1e-14') for k, v in enumerate(fitted.coefficients[0]) if k not in (0, j + 1))


def test_zero_variance_mask_is_frozen_and_raw_clipping_is_retained(spec, model, corpus):
    ordinary = corpus[0][0]
    constant_index = model.feature_names.index('alpha-x')
    assert model.zero_variance_mask[constant_index] is True
    assert model.scales[constant_index] == 1
    changed = replace(ordinary, values=tuple((k, D(12345) if k == 'alpha-x' else v)
                                             for k, v in ordinary.values))
    a = forecast_error(spec, model, ordinary, record_id='software.a')
    b = forecast_error(spec, model, changed, record_id='software.b')
    assert a.raw_log_error_points == b.raw_log_error_points
    rows = tuple((D(v), *(D(0) for _ in model.feature_names)) for v in (-2, 1, .5)) * 5
    altered = replace(model, coefficients=rows)
    clipped = forecast_error(spec, altered, ordinary, record_id='software.clipped')
    assert clipped.raw_log_error_points == (D(-2), D(1), D('.5')) * 5
    assert clipped.log_error_points == (D(0), D(1), D(1)) * 5
    converted = forecast_error_points(clipped)
    assert converted[0] == 0 and abs(converted[1] - (D(1).exp() - 1)) < D('1e-26')
    with pytest.raises(ValueError, match='raw-to-cumulative'):
        replace(clipped, raw_log_error_points=(D(3), *clipped.raw_log_error_points[1:]))


def test_original_unit_conversion_explicitly_refuses_numeric_overflow(spec, model, corpus):
    rows = ((D('1e20'), *(D(0) for _ in model.feature_names)),) * 15
    large = forecast_error(spec, replace(model, coefficients=rows), corpus[0][0], record_id='software.large')
    with pytest.raises(ValueError, match='unrepresentable'):
        forecast_error_points(large)


def test_model_role_criterion_reservation_and_feature_group_substitutions_refuse(spec, model):
    f = feature(spec, 0)
    for altered in (replace(model, roles=obj('foreign-roles')), replace(model, reservation=obj('foreign-reserve')),
                    replace(model, spec=obj('foreign-criterion', spec.SCHEMA))):
        with pytest.raises(ValueError, match='join'):
            forecast_error(spec, altered, f, record_id='software.invalid')
    with pytest.raises(ValueError, match='group'):
        forecast_error(spec, model, replace(f, independent_group_id='software.other-group'), record_id='software.invalid')


def test_rank_boundary_preserves_infinity_at_low_decimal_precision(spec, corpus, model):
    fs, ys = select(spec, corpus, 'CALIBRATION_DESCRIPTIVE')
    calibration = calibrate_error_model(spec, model, fs, ys, record_id='software.error.exact-rank')
    below = D('0.0588235294117647058823529411764705882352941176470588235294117647058823529411764605882352941')
    above = D('0.0588235294117647058823529411764705882352941176470588235294117647058823529411764805882352941')
    for precision in (3, 28, 100):
        with localcontext() as context:
            context.prec = precision
            assert rank_radius(calibration, STRATA[1], below) == (16, 17, None)
            n, k, radius = rank_radius(calibration, STRATA[1], above)
            assert (n, k) == (16, 16) and radius is not None


def test_default_alpha_none_and_family_rank_formula_missing_infinity(spec, corpus, model):
    fs, ys = select(spec, corpus, 'CALIBRATION_DESCRIPTIVE')
    calibration = calibrate_error_model(spec, model, fs, ys, record_id='software.error.calibration')
    assert calibration.alpha is None and calibration.sampling_warrant == WARRANT
    # All16 de-anneal roots are selected in this exposed fixture, but are not
    # independently qualified science. These are only software rank queries.
    n, k, radius = rank_radius(calibration, STRATA[1], D('.1'))
    assert (n, k) == (16, 16) and radius is not None
    assert rank_radius(calibration, STRATA[1], D('.01')) == (16, 17, None)
    assert any(s[2] is None for s in calibration.scores)
    point = forecast_error(spec, model, feature(spec, 64), record_id='software.no-level', calibration=calibration)
    assert all(u is None for u in point.log_error_uppers)
    software_query = replace(calibration, alpha=D('.1'))
    bounded = forecast_error(spec, model, feature(spec, 64), record_id='software.query-only', calibration=software_query)
    assert all(u is not None for u in bounded.log_error_uppers)
    assert bounded.sampling_warrant == WARRANT
    with pytest.raises(ValueError, match='warrant'):
        replace(calibration, sampling_warrant='SATISFIED')


def test_calibration_full_roster_missing_unknown_and_native_failures_unbounded(spec, model):
    for missing, failure in ((True, False), (False, True)):
        fs, ys = inputs(spec, role='CALIBRATION_DESCRIPTIVE', missing=missing, failure=failure)
        calibration = calibrate_error_model(spec, model, fs, ys, record_id='software.unbounded')
        assert len(calibration.root_ids) == len(calibration.scores) == 64
        assert all(s[2] is None for s in calibration.scores)
        assert rank_radius(calibration, STRATA[1], D('.5'))[2] is None
    fs, ys = inputs(spec, role='CALIBRATION_DESCRIPTIVE')
    with pytest.raises(ValueError, match='roles'):
        calibrate_error_model(spec, model, fs[:-1], ys, record_id='software.thinned')


def test_calibration_model_group_and_stratum_rebinding_refuse(spec, model, corpus):
    calibration = calibrate_error_model(spec, model, *select(spec, corpus, 'CALIBRATION_DESCRIPTIVE'), record_id='software.cal')
    for altered in (replace(calibration, model=obj('foreign-model', model.SCHEMA)),
                    replace(calibration, reservation=obj('foreign-reserve')),
                    replace(calibration, scores=((calibration.scores[0][0], STRATA[3], *calibration.scores[0][2:]), *calibration.scores[1:]))):
        with pytest.raises(ValueError, match='substitutes'):
            forecast_error(spec, model, feature(spec, 0), record_id='software.invalid', calibration=altered)


def test_all_missing_all_refusal_retains3840_complete_denominator_and_no_use(spec):
    fs, ys = inputs(spec, missing=True, unavailable=True)
    training = select(spec, (fs, ys), 'TRAIN')
    empty_model = fit_error_model(spec, *training, method='ALL_ORIGIN', record_id='software.empty-model')
    assert all(c is None for c in empty_model.coefficients)
    assert set(empty_model.endpoint_finite_group_counts) == {0}
    calibration = calibrate_error_model(spec, empty_model, *select(spec, (fs, ys), 'CALIBRATION_DESCRIPTIVE'), record_id='software.empty-cal')
    assert all(s[2] is None for s in calibration.scores)
    predictions = tuple(forecast_error(spec, empty_model, f, record_id='prediction.' + f.root_id,
                                      calibration=calibration) for f in fs)
    result = error_readout(spec, empty_model, predictions, ys, record_id='software.empty-readout')
    census = readout_census(result)
    assert census['requested_roots'] == 256 and census['requested_endpoints'] == 3840
    assert dict(census['label_dispositions']) == {'NO_CAUSAL_ORIGIN': 70 * 15, 'UNKNOWN_CONTACT': 186 * 15}
    assert census['finite_accuracy_endpoints'] == census['finite_bound_endpoints'] == census['admitted_use_endpoints'] == 0
    assert census['complete_accuracy_roots'] == census['partial_accuracy_roots'] == census['complete_bound_roots'] == 0
    assert len(root_error_summaries(result)) == 256
    assert all(row[3] is None and row[4] is None for row in root_error_summaries(result))
    assert result.qualification == 'NOT_ESTABLISHED'
    with pytest.raises(ValueError, match='denominator'):
        replace(result, cells=result.cells[:-1])
    with pytest.raises(ValueError, match='qualification'):
        replace(result, qualification='SATISFIED')


def test_partial_forecasts_missing_result_no_origin_cannot_fake_full_accuracy(spec, model, corpus):
    prediction = forecast_error(spec, model, corpus[0][0], record_id='software.one-root')
    result = error_readout(spec, model, (prediction,), corpus[1], record_id='software.partial-readout')
    census = readout_census(result)
    assert census['finite_accuracy_endpoints'] == 15
    assert census['complete_accuracy_roots'] == 1 and census['partial_accuracy_roots'] == 0
    assert census['accuracy_roots_by_subrole'] == (('TRAIN', 1, 128),
            ('CALIBRATION_DESCRIPTIVE', 0, 64), ('EVALUATION_DESCRIPTIVE', 0, 64))
    assert dict(census['forecast_dispositions'])['FORECAST_MISSING'] == 255 * 15
    assert census['finite_bound_endpoints'] == census['admitted_use_endpoints'] == 0
    # This requests a frontier, not a nomination or imputed useful lifetime.
    query = query_forecast_tolerance(prediction, D('1000000'))
    assert all(p and not u for _, _, p, u in query)
    with pytest.raises(ValueError):
        query_forecast_tolerance(prediction, D('Infinity'))
    no_origin = next(f for f in corpus[0] if f.disposition == 'NO_CAUSAL_ORIGIN')
    refused = forecast_error(spec, model, no_origin, record_id='software.no-origin')
    assert refused.disposition == 'NO_CAUSAL_ORIGIN' and all(x is None for x in refused.log_error_points)


def test_partial_root_accuracy_keeps_missing_target_and_all_role_denominators(spec, model, corpus):
    fs, ys = select(spec, corpus, 'TRAIN')
    changed = tuple(replace(y, disposition='UNKNOWN_CONTACT', bound_kind='UNRESOLVED_INTERVAL',
                            upper_loss=None)
                    if (y.predictor, y.horizon_step) == ENDPOINTS[2]
                    and y.bound_kind == 'FINITE_POINT' else y for y in ys)
    partial_model = fit_error_model(spec, fs, changed, method='ALL_ORIGIN', record_id='software.partial-model')
    forecast = forecast_error(spec, partial_model, corpus[0][0], record_id='software.partial-target')
    result = error_readout(spec, partial_model, (forecast,), corpus[1], record_id='software.partial-target-readout')
    summary = root_error_summaries(result)[0]
    assert summary[2] == 14 and summary[3] is not None and summary[4] is None
    census = readout_census(result)
    assert census['complete_accuracy_roots'] == 0 and census['partial_accuracy_roots'] == 1
    assert census['requested_roots'] == 256 and census['requested_endpoints'] == 3840


def test_omitted_target_mask_cannot_be_thinned_or_relabelled(spec, model):
    assert model.endpoint_omissions
    with pytest.raises(ValueError, match='omitted-root'):
        replace(model, endpoint_omissions=model.endpoint_omissions[:-1])
    with pytest.raises(ValueError, match='omitted-root'):
        replace(model, endpoint_omissions=((*model.endpoint_omissions[0][:3], 'SATISFIED'),
                                           *model.endpoint_omissions[1:]))


def test_label_frontier_and_cumulative_substitution_refuses(spec, model, corpus):
    fs, ys = select(spec, corpus, 'TRAIN')
    changed = replace(ys[1], lower_loss=D(0), upper_loss=D(0))
    with pytest.raises(ValueError, match='decreases'):
        fit_error_model(spec, fs, (ys[0], changed, *ys[2:]), method='CONTEXT', record_id='software.bad')
    foreign = replace(ys[0], frontier=obj('different-frontier', MatrixResponseRootFrontier.SCHEMA))
    with pytest.raises(ValueError, match='mixes'):
        fit_error_model(spec, fs, (foreign, *ys[1:]), method='CONTEXT', record_id='software.bad')
    forecast = forecast_error(spec, model, corpus[0][0], record_id='software.forecast')
    with pytest.raises(ValueError, match='reverses'):
        replace(forecast, log_error_points=(D(999), *forecast.log_error_points[1:]))


def test_future_outcome_changes_leave_small_forecast_identical(spec, model, corpus):
    original = forecast_error(spec, model, corpus[0][0], record_id='software.same-seal')
    changed = replace(corpus[1][0], lower_loss=D(100000), upper_loss=D(100000))
    assert changed != corpus[1][0]  # The later evaluator's data really changed.
    assert original.canonical_bytes() == forecast_error(spec, model, corpus[0][0], record_id='software.same-seal').canonical_bytes()
    assert len(model.training_root_ids) == 128
    assert all(r in {row[0] for row in spec.roles.rows if row[3] == 'TRAIN'} for r in model.training_root_ids)


def test_canonical_descriptive_records_round_trip(spec, model, corpus):
    calibration = calibrate_error_model(spec, model, *select(spec, corpus, 'CALIBRATION_DESCRIPTIVE'), record_id='software.cal')
    forecast = forecast_error(spec, model, corpus[0][0], record_id='software.forecast', calibration=calibration)
    result = error_readout(spec, model, (forecast,), corpus[1], record_id='software.readout')
    for record in (spec.roles, spec, corpus[0][0], model, calibration, forecast, result):
        assert decode_canonical_bytes(record.canonical_bytes(), type(record), maximum_bytes=None) == record
