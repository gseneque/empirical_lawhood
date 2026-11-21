# SPDX-License-Identifier: MPL-2.0
"""Independent mathematical falsifiers; no study roots or qualification."""
from copy import deepcopy

import numpy as np
import pytest

from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02b_read as reader
from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02b_science as science


def test_physical_arnoldi_retains_inputs_and_has_no_discrete_clock_operand():
    matrix = np.diag(np.linspace(1., 12., 96))
    inputs = np.sin(np.arange(384, dtype=float).reshape(96, 4) * .23)
    # Four independent inputs, with a sparse addition avoiding a rank-two sine bank.
    inputs[:4] += np.eye(4)
    called = []
    def action(values):
        called.append(values.shape[1])
        return matrix @ values
    basis, images, evidence = science.input_basis(action, inputs, 24)
    assert basis.shape == (96, 24) and sum(called) == 24
    np.testing.assert_allclose(basis.T @ basis, np.eye(24), atol=1e-12)
    np.testing.assert_allclose(images, matrix @ basis, atol=1e-12)
    np.testing.assert_allclose(basis @ (basis.T @ inputs), inputs, atol=1e-11)
    assert evidence['input_residual'] < 1e-10
    with pytest.raises(ValueError):
        science.input_basis(action, inputs, 48)


def test_exact_krylov_closure_keeps_actual_rank_without_spectral_filler():
    inputs = np.eye(96)[:, :4]
    basis, images, evidence = science.input_basis(lambda v: 3 * v, inputs, 32)
    assert basis.shape == (96, 4) and evidence['rank'] == evidence['hvp_columns'] == 4
    np.testing.assert_array_equal(images, 3 * basis)


def test_ridge_fit_has_independent_augmented_equation_falsifier():
    features = np.array([[i, i * i, np.sin(i), 1.] for i in range(8)], dtype='<f8')
    targets = np.log1p(np.arange(1., 9.))
    result = science.fit_accounts(features, targets)
    reader.check_fit(features, targets, result)
    assert result['feature_scale'][3] == 1
    bad = deepcopy(result)
    bad['coefficients'][2, 0] += .1
    with pytest.raises(ValueError, match='ridge'):
        reader.check_fit(features, targets, bad)
    assert np.isfinite(science.predict_accounts(result, features[0])).all()
    with pytest.raises(ValueError, match='eight'):
        science.fit_accounts(features[:7], targets[:7])


def test_signed_pair_error_and_view_gate_cannot_be_replaced_by_endpoint_means():
    from tests.test_matrix_sci02_workflow import fixture
    from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02_science import actuator_scales
    design = fixture()[0].design
    scales = actuator_scales(design)
    native, models = {}, {}
    for recipe, sign in (('ORIGINAL', 1), ('EARLY', -1)):
        native[recipe], models[recipe] = {}, {}
        for view, _ in science.VIEWS:
            for panel in (0, 1):
                stem = f'{view}.p{panel}'
                truth = np.zeros((4, 64, 48))
                truth[0, :, 24] = scales[0, :, 1]
                error = np.zeros_like(truth)
                error[:, :, 0] = sign * .006 * scales[:, :, 0]
                native[recipe][stem + '.native'] = truth
                models[recipe][stem + '.updated'] = truth - error
    assessed = dict(reader.assess_pair(design, native, models).measurements)
    assert float(assessed['primary.endpoint_error']) == pytest.approx(.006)
    assert float(assessed['primary.contrast_error']) == pytest.approx(.012)
    assert assessed['primary.joint_success'] == 0
    models['EARLY']['fine.p0.updated'][:, :, 0] += .0002 * scales[:, :, 0]
    assessed = dict(reader.assess_pair(design, native, models).measurements)
    assert float(assessed['primary.view_difference']) > .0001


def test_calibration_retains_unknown_and_simultaneous_account_maximum():
    assert reader.calibration_score(None, .8) is None
    assert float(reader.calibration_score(np.array([.1, .3, .7]), .8)) == pytest.approx(.7)
    assert reader.calibration_score(np.ones(3), .8) == 0
