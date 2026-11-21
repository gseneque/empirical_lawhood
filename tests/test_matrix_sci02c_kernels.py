# SPDX-License-Identifier: MPL-2.0
"""Independent scientific controls; no study roots or qualification evidence."""
from decimal import Decimal
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02b_science as previous
from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02b_read as previous_read
from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02c_science as science
from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02c_read as reader


def test_history_has_independent_affine_equations_and_exact_free_forcing_limit():
    force = np.array([[1., -.5, .2, 0.], [.1, .8, -.4, 1.]], dtype='<f8')
    zero = np.zeros((2, 2))
    for dt in (Decimal('.001'), Decimal('.0005')):
        result = science.history_window(zero, zero, zero, force, timestep=dt, friction=Decimal(0))
        # Exact free motion: momentum = F*.016; position = F*(.016**2/2 + .016*.048).
        np.testing.assert_allclose(result[:, -1, :2], force.T * (.016**2 / 2 + .016 * .048), atol=1e-16)
        np.testing.assert_allclose(result[:, -1, 2:], force.T * .016, atol=1e-15)
        operators = (np.diag([1., 3.]), np.array([[7., 2.], [2., 5.]]), np.diag([8., 2.]))
        actual = science.history_window(*operators, force, timestep=dt, friction=Decimal(1))
        expected = reader.affine_history(operators, force, timestep=dt, friction=Decimal(1))
        np.testing.assert_allclose(actual, expected, atol=1e-14)
        frozen = science.history_window(operators[0], operators[0], operators[2], force, timestep=dt, friction=Decimal(1))
        assert np.max(np.abs(actual[:, -1] - frozen[:, -1])) > 1e-6


def test_signed_fit_preserves_negative_corrections_and_training_only_scaling():
    features = np.asarray([[i, i*i, np.sin(i), 4.] for i in range(8)], dtype='<f8')
    target = -np.arange(1., 9.) / 100
    fitted = previous.fit_accounts(features, target)
    previous_read.check_fit(features, target, fitted)
    model = SimpleNamespace(numerical_arrays=lambda: {k: np.stack((v, v)) for k, v in fitted.items()})
    predictions = science.signed_predictions(model, 0, features[0], np.zeros(2))
    assert predictions[0, 0] == pytest.approx(np.median(target)) and np.all(predictions < 0)
    assert fitted['feature_scale'][3] == 1


def test_policy_cannot_use_audit_only_supplier_to_change_its_selected_route():
    study = SimpleNamespace(precision=Decimal('.001'), view_tolerance=Decimal('.0001'))
    radii = SimpleNamespace(radii=((Decimal('.002'),)*3, (Decimal('.0002'),)*3))
    model = SimpleNamespace(numerical_arrays=lambda: {'feature_mean': np.zeros((2, 4)), 'feature_scale': np.ones((2, 4)),
        'coefficients': np.zeros((2, 3, 4)), 'intercepts': np.zeros((2, 3))})
    config = SimpleNamespace(study=study, calibration=radii, model=model)
    basic = {'features': np.zeros(4), 'model_q': np.array([.01, .01])}
    request = science.request(config, basic).arrays
    assert request['request_history'][0] == 1 and request['admitted'][2] == 0
    history = {'features': np.zeros(4), 'model_q': np.array([.01, .01])}
    assert science.decide(config, request, history).arrays['selected_route'][0] == 1
    request['request_history'][0] = 0
    assert science.decide(config, request, history).arrays['selected_route'][0] == 2
    history['model_q'] = np.array([0., 0.])
    request['request_history'][0] = 1
    assert science.decide(config, request, history).arrays['selected_route'][0] == 2
