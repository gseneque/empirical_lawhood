# SPDX-License-Identifier: MPL-2.0
"""Seedless numerical-entry controls over explicitly exposed literal operands.

No acquisition, issue, execution worker or scientific qualification occurs.
Historical wrappers retain identity/custody packaging; numerical entries consume
the same causal values and independently checked retained response witnesses.
"""

from dataclasses import replace
from decimal import Decimal as D
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history import forecast as feature
from empirical_lawhood.adapters.methods.matrix_scheduled_history import response_forecast as response
from tests.test_matrix_e3_causal_feature_extraction import _case as feature_fixture, _damaged
from tests import test_matrix_scheduled_response_forecast as response_fixture


@pytest.fixture(scope='module')
def feature_case(tmp_path_factory):
    return feature_fixture(tmp_path_factory.mktemp('seedless-feature-values'))


@pytest.fixture(scope='module')
def response_case(tmp_path_factory):
    return response_fixture.case.__wrapped__(tmp_path_factory)


def _feature_values(case, *, disposition=None, frame=None, traces=None, arrays=None, diagnostics=None,
                    window=32, cadence=16):
    public = feature.ScheduledPublicSource.from_source(case.source)
    return feature.causal_feature_values(public.coordinate, public.policy,
        prefix_disposition=case.prefix.disposition if disposition is None else disposition,
        prefix_frame_sha256=case.prefix.frame_sha256 if frame is None else frame,
        traces=case.witness.traces if traces is None else traces,
        causal_arrays=case.arrays if arrays is None else arrays,
        diagnostics=case.diagnostics if diagnostics is None else diagnostics,
        feature_window_ticks=window, feature_cadence_ticks=cadence)


def _feature_wrapped(case, *, witness=None, arrays=None, diagnostics=None):
    return feature.causal_feature(case.design, case.source, case.prefix,
        case.witness if witness is None else witness, case.arrays if arrays is None else arrays,
        case.diagnostics if diagnostics is None else diagnostics, feature_id='exposed.feature.values')


def _same_arrays(left, right):
    assert set(left) == set(right)
    for name in left:
        assert left[name].dtype == right[name].dtype, name
        assert left[name].shape == right[name].shape, name
        assert left[name].tobytes() == right[name].tobytes(), name


def test_feature_values_match_historical_wrapper_without_source_or_identity_access(feature_case, monkeypatch):
    case = feature_case
    wrapped = _feature_wrapped(case)
    public = feature.ScheduledPublicSource.from_source(case.source)

    def forbidden(*args, **kwargs):
        raise AssertionError('seedless feature accessed identity, model, native producer or spectrum solver')

    monkeypatch.setattr(feature, 'identity', forbidden)
    monkeypatch.setattr(feature.ScheduledForecastFeature, '__init__', forbidden)
    monkeypatch.setattr(np.linalg, 'eigh', forbidden)
    monkeypatch.setattr(np.random, 'Generator', forbidden)
    actual = feature.causal_feature_values(public.coordinate, public.policy,
        prefix_disposition=case.prefix.disposition, prefix_frame_sha256=case.prefix.frame_sha256,
        traces=case.witness.traces, causal_arrays=case.arrays, diagnostics=case.diagnostics,
        feature_window_ticks=32, feature_cadence_ticks=16)
    assert actual == (wrapped.disposition, wrapped.values)
    assert len(actual[1]) == 21
    values = dict(actual[1])
    assert values['alpha-x'] == D('2.0999999999999996')
    assert values['slow-y-mean'] == values['third-fourth-y-gap'] == D('.125')
    assert values['trailing-angle'] == 3


@pytest.mark.parametrize('damage', ('primary-clock', 'fine-clock', 'frame', 'couplings',
    'missing-array', 'spectrum-shape', 'nonfinite-spectrum', 'negative-feature',
    'missing-observation', 'missing-angle', 'ambiguous-observation', 'missing-primary-y'))
def test_feature_values_keep_original_array_and_diagnostic_refusals(feature_case, damage):
    witness, arrays, diagnostics = _damaged(feature_case, damage)
    disposition, values = _feature_values(feature_case, traces=witness.traces, arrays=arrays, diagnostics=diagnostics)
    wrapped = _feature_wrapped(feature_case, witness=witness, arrays=arrays, diagnostics=diagnostics)
    assert (disposition, values) == (wrapped.disposition, wrapped.values) == ('REFUSED', ())


@pytest.mark.parametrize('disposition,expected', (('NO_ORIGIN', 'NO_CAUSAL_ORIGIN'), ('UNEVALUABLE', 'UNAVAILABLE')))
def test_nonuse_feature_values_do_not_touch_arrays_or_traces(feature_case, disposition, expected):
    class NoRead:
        def __getitem__(self, name):
            raise AssertionError('nonuse feature accessed numerical operands')

        def __iter__(self):
            raise AssertionError('nonuse feature accessed traces')

    assert _feature_values(feature_case, disposition=disposition, arrays=NoRead(), diagnostics=NoRead(),
        traces=NoRead()) == (expected, ())


@pytest.mark.parametrize('window,cadence', ((True, 16), (32, False), (0, 16), (32, 0), (32.0, 16), (32, D(16))))
def test_direct_feature_values_require_positive_exact_integer_window_and_cadence(feature_case, window, cadence):
    with pytest.raises(ValueError, match='positive exact integer'):
        _feature_values(feature_case, window=window, cadence=cadence)


def _numerical_protocol(protocol):
    # Only original physical/numerical fields. No source identity, root, policy,
    # protocol ID, criterion, fitted error model, arrays manifest or historical record type.
    names = ('actions', 'horizon_steps', 'receiver_count', 'hessian_difference_step', 'generic_gap_minimum',
        'spectral_gap_minimum', 'radial_norm_minimum', 'complement_gram_minimum', 'hessian_reference_tolerance',
        'mechanical_model')
    return SimpleNamespace(**{name: getattr(protocol, name) for name in names},
        public_source=SimpleNamespace(coordinate=protocol.public_source.coordinate))


def test_response_values_match_every_retained_byte_without_historical_packaging(response_case, monkeypatch):
    case = response_case
    protocol = _numerical_protocol(case.protocol)
    response_fixture.block_cold(monkeypatch)

    def forbidden(*args, **kwargs):
        raise AssertionError('response numerical entry accessed record identity or historical packaging')

    monkeypatch.setattr(response, 'identity', forbidden)
    monkeypatch.setattr(response, 'array_product', forbidden)
    monkeypatch.setattr(response.ScheduledResponseForecast, '__init__', forbidden)
    arrays, disposition, dispositions = response.forecast_response_arrays(protocol, case.arrays, case.templates,
        disposition=case.causal.disposition, retained=case.retained)
    _same_arrays(arrays, case.retained)
    assert (disposition, dispositions) == (case.result.disposition, case.result.dispositions)
    assert tuple((view, method) for view, method, _, _ in dispositions) == tuple(
        (view, method) for view in ('PRIMARY', 'FINE') for method in ('FACTOR', 'FULL_COUPLED', 'GENERIC_SLOW', 'NORM_RADIUS', 'SPECTRA'))


@pytest.mark.parametrize('disposition', ('NO_ORIGIN', 'UNEVALUABLE'))
def test_response_nonuse_retains_both_views_and_all_five_methods(response_case, monkeypatch, disposition):
    case = response_case
    arrays = {name: value.copy() for name, value in case.arrays.items()}
    arrays['frame'][:] = np.nan
    causal = response_fixture.causal_record(case.source, arrays, disposition=disposition)
    response_fixture.block_cold(monkeypatch)
    raw, wrapped = response.forecast(case.protocol, causal, arrays, case.templates, artifact_id='exposed.values.nonuse')
    values, overall, dispositions = response.forecast_response_arrays(_numerical_protocol(case.protocol), arrays,
        case.templates, disposition=disposition)
    assert overall == wrapped.disposition == disposition and dispositions == wrapped.dispositions
    assert len(values) == 10 and all(np.isnan(value).all() for value in values.values())
    retained = response.decode_matrix_arrays(raw, wrapped.arrays)
    _same_arrays(values, retained)
    cold, cold_overall, cold_dispositions = response.forecast_response_arrays(_numerical_protocol(case.protocol),
        arrays, case.templates, disposition=disposition, retained=retained)
    _same_arrays(cold, retained)
    assert (cold_overall, cold_dispositions) == (overall, dispositions)


@pytest.mark.parametrize('condition', ('instrument', 'spectral'))
def test_response_unresolved_and_partial_methods_keep_all_original_witnesses(response_case, monkeypatch, condition):
    case = response_case
    protocol = replace(case.protocol, **({'complement_gram_minimum': D(2)} if condition == 'instrument'
        else {'spectral_gap_minimum': D(100)}))
    raw, wrapped = response.forecast(protocol, case.causal, case.arrays, case.templates,
        artifact_id='exposed.values.' + condition)
    retained = response.decode_matrix_arrays(raw, wrapped.arrays)
    response_fixture.block_cold(monkeypatch)
    values, disposition, dispositions = response.forecast_response_arrays(_numerical_protocol(protocol),
        case.arrays, case.templates, disposition=case.causal.disposition, retained=retained)
    _same_arrays(values, retained)
    assert (disposition, dispositions) == (wrapped.disposition, wrapped.dispositions)
    assert {'complement_spectrum', 'complement_eigenvectors'} <= set(values)
    if condition == 'instrument':
        assert disposition == 'INSTRUMENT_UNRESOLVED'
        assert len(values) == 12 and all(status == 'UNRESOLVED' for _, _, status, _ in dispositions)
    else:
        assert disposition == 'AVAILABLE'
        assert all(status == 'UNRESOLVED' for _, method, status, _ in dispositions if method == 'SPECTRA')
        assert all(status == 'AVAILABLE' for _, method, status, _ in dispositions if method == 'FULL_COUPLED')


@pytest.mark.parametrize('damage', ('forces', 'receivers', 'prediction', 'hessian-eigenpair', 'omitted-witness', 'extra-array'))
def test_response_values_reject_substituted_complete_cold_arrays(response_case, monkeypatch, damage):
    case = response_case
    retained = {name: value.copy() for name, value in case.retained.items()}
    if damage == 'omitted-witness':
        del retained['fine_hessian_eigenvectors']
    elif damage == 'extra-array':
        retained['extra'] = np.zeros(1, dtype='<f8')
    else:
        retained[{'forces': 'forces', 'receivers': 'receivers', 'prediction': 'primary_full_coupled',
            'hessian-eigenpair': 'primary_hessian_eigenvectors'}[damage]].flat[0] += .1
    response_fixture.block_cold(monkeypatch)
    with pytest.raises((ValueError, KeyError)):
        response.forecast_response_arrays(_numerical_protocol(case.protocol), case.arrays, case.templates,
            disposition=case.causal.disposition, retained=retained)
