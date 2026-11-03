# SPDX-License-Identifier: MPL-2.0
"""Exposed software endpoint witnesses; these tests enter no native solver."""
from decimal import Decimal
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.battery_thermal_inquiry.native import differential_state_endpoints


class ExposedSegmentedSolution:
    def __init__(self, segments):
        self.all_ys = segments
        self.variables_returned = False

    @property
    def y(self):
        raise AssertionError("full dense trajectory must remain untouched")

    @property
    def first_state(self):
        raise AssertionError("cached boundary must not retain full sub-solutions")

    @property
    def last_state(self):
        raise AssertionError("cached boundary must not retain full sub-solutions")


@pytest.mark.parametrize("segments", [
    (np.array([[1.25, 2.5], [3.75, 4.5], [100, 200]]),),
    (np.array([[1.25, 2.5], [3.75, 4.5], [100, 200]]),
     np.array([[6.25, 7.5], [8.75, 9.5], [300, 400]])),
])
def test_exposed_exact_endpoint_columns_without_dense_trajectory(segments):
    expected_dense = np.hstack(segments)
    expected = tuple(tuple(Decimal(str(float(value))) for value in expected_dense[:2, column])
                     for column in (0, -1))
    assert differential_state_endpoints(ExposedSegmentedSolution(segments), 2) == expected


@pytest.mark.parametrize("boundary", [np.zeros((1, 1)), np.zeros((2, 0))])
def test_exposed_incomplete_boundary_refuses_full_state_witness(boundary):
    solution = SimpleNamespace(all_ys=(boundary, np.zeros((2, 1))), variables_returned=False)
    with pytest.raises(ValueError, match="complete differential-state column"):
        differential_state_endpoints(solution, 2)


def test_exposed_outputs_only_solution_cannot_supply_full_state_witness():
    solution = SimpleNamespace(all_ys=(np.zeros((2, 1)),), variables_returned=True)
    with pytest.raises(ValueError, match="actual full-state solution"):
        differential_state_endpoints(solution, 2)


def test_exposed_exact_state_row_count_keeps_all_differential_operands():
    segment = np.arange(12, dtype=np.float64).reshape(4, 3)
    start, end = differential_state_endpoints(ExposedSegmentedSolution((segment,)), 4)
    assert start == (Decimal("0.0"), Decimal("3.0"), Decimal("6.0"), Decimal("9.0"))
    assert end == (Decimal("2.0"), Decimal("5.0"), Decimal("8.0"), Decimal("11.0"))
