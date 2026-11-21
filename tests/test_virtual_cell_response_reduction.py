import math
import numpy as np
import pytest
from empirical_lawhood.domains.biology.virtual_cell.contracts import VirtualCellContractError
from empirical_lawhood.domains.biology.virtual_cell.response_reduction import ResponseMomentAccumulator, selected_control_rows


def accumulator():
    return ResponseMomentAccumulator.for_labels(np.array(['a', 'a', 'b']), np.array(['x', 'x', 'y']), 2, 'log1p-fixed-total', 4.)


@pytest.mark.numerical(oracle='Three two-gene cells: fixed-total4 transforms[1,3],[3,1],[2,2] to[ln2,ln4],[ln4,ln2],[ln3,ln3]; paired population variance(ln4-ln2)^2/4')
def test_dense_and_sparse_moments_match_closed_form():
    dense = accumulator()
    dense.add_dense(0, np.array([[1., 3.]]))
    dense.add_dense(1, np.array([[3., 1.], [2., 2.]]))
    sparse = accumulator()
    sparse.add_csr(0, np.array([0, 2, 4, 6]), np.array([0, 1, 0, 1, 0, 1]), np.array([1., 3., 3., 1., 2., 2.]))
    expected = np.array([[(math.log(2)+math.log(4))/2]*2, [math.log(3)]*2])
    variance = np.array([[(math.log(4)-math.log(2))**2/4]*2, [0., 0.]])
    for result in (dense, sparse):
        means, variances = result.finish()
        np.testing.assert_allclose(means, expected, rtol=0, atol=5e-16)
        np.testing.assert_allclose(variances, variance, rtol=0, atol=5e-16)
        assert result.counts.tolist() == [2, 1]


@pytest.mark.numerical(oracle='CSR repeated coordinate entries1+2 represent dense value3 before log1p normalization, never log2+log3')
def test_duplicate_csr_coordinates_match_the_mathematical_matrix():
    sparse = accumulator()
    sparse.add_csr(0, np.array([0, 3, 6, 8]), np.array([0, 1, 1, 0, 0, 1, 0, 1]), np.array([1., 1., 2., 1., 2., 1., 2., 2.]))
    dense = accumulator()
    dense.add_dense(0, np.array([[1., 3.], [3., 1.], [2., 2.]]))
    for a, b in zip(sparse.finish(), dense.finish(), strict=True):
        np.testing.assert_array_equal(a, b)


def test_complete_row_census_cannot_drop_repeat_or_reorder_cells():
    result = accumulator()
    with pytest.raises(VirtualCellContractError, match='incomplete'):
        result.finish()
    with pytest.raises(VirtualCellContractError, match='exactly once'):
        result.add_dense(1, np.ones((1, 2)))
    result.add_dense(0, np.ones((1, 2)))
    with pytest.raises(VirtualCellContractError, match='exactly once'):
        result.add_dense(0, np.ones((1, 2)))


def test_reservoir_covers_observed_batches_with_original_rows():
    targets=np.array(['control', 'treatment', 'control', 'control', 'control'])
    batches=np.array(['a', 'a', 'a', 'b', 'b'])
    selected=selected_control_rows(targets=targets,batches=batches,control_label='control',maximum_cells=2,seed=17)
    assert len(selected)==2 and set(batches[selected])=={'a','b'} and np.all(targets[selected]=='control')
    np.testing.assert_array_equal(selected, selected_control_rows(targets=targets,batches=batches,control_label='control',maximum_cells=2,seed=17))
    with pytest.raises(VirtualCellContractError, match='too small'):
        selected_control_rows(targets=targets,batches=batches,control_label='control',maximum_cells=1,seed=17)
