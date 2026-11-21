import numpy as np
import pytest
from empirical_lawhood.methods.electronic_structure.diis import checked_diis_weights, accumulate_diis_block


@pytest.mark.numerical(oracle='Closed-form two-vector constrained minimum: variance1/4 gives weights4/5,1/5 and multiplier-4/5')
def test_diis_weights_against_closed_form_quadratic():
    matrix = np.array([[0., 1., 1.], [1., 1., 0.], [1., 0., 4.]])
    weights, diagnostics = checked_diis_weights(matrix)
    np.testing.assert_allclose(weights, [-.8, .8, .2], rtol=0, atol=2e-15)
    assert diagnostics['eigenpair_residual'] <= diagnostics['eigenpair_residual_limit']
    assert diagnostics['orthogonality_residual'] <= diagnostics['orthogonality_limit']
    output = np.zeros(3)
    accumulate_diis_block(output, np.array([1., 3., 5.]), weights[1])
    accumulate_diis_block(output, np.array([6., 8., 10.]), weights[2])
    np.testing.assert_allclose(output, [2., 4., 6.], rtol=0, atol=2e-15)


@pytest.mark.numerical(oracle='Identical two-vector Gram rows: Moore-Penrose solution has multiplier-1 and symmetric weights1/2,1/2')
def test_dependent_diis_weights_preserve_original_threshold():
    matrix = np.array([[0., 1., 1.], [1., 1., 1.], [1., 1., 1.]])
    weights, diagnostics = checked_diis_weights(matrix)
    np.testing.assert_allclose(weights, [-1., .5, .5], rtol=0, atol=2e-14)
    assert diagnostics['original_dependence_threshold'] == 1e-14


@pytest.mark.parametrize('matrix', [np.array([[0., np.nan], [np.nan, 1.]]), np.array([[1., 2.], [3., 4.]]), np.ones((2, 3)), np.eye(2, dtype=int)])
def test_standalone_diis_rejects_invalid_matrix(matrix):
    with pytest.raises(ValueError, match='finite Hermitian matrix'):
        checked_diis_weights(matrix)
