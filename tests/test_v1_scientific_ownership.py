# SPDX-License-Identifier: MPL-2.0
"""Independent signed-error controls and the scientific/application boundary."""
from copy import deepcopy
import subprocess
import sys
import threading
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.domains.matrix.matrix_factor_response.refresh_matched import (
    CELL_FIELDS, join_native_errors, representation_summary,
)
from empirical_lawhood.execution.local import parallel


def test_reusable_virtual_cell_battery_and_grid_forecasts_import_without_adapters():
    """Pure scientific reuse must not import HDF5, native solvers or adapters."""
    script = '''
import importlib.abc
import sys
class ForbidEffects(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith("empirical_lawhood.adapters") or fullname.split(".")[0] in {"h5py", "pybamm", "grid2op"}:
            raise AssertionError("pure scientific import entered effect owner: " + fullname)
sys.meta_path.insert(0, ForbidEffects())
from empirical_lawhood.domains.biology.virtual_cell.prediction import PredictionRoster, compile_absolute_prediction_means
from empirical_lawhood.domains.biology.virtual_cell.prediction_v2 import compile_shared_template_shift_v2_cells
from empirical_lawhood.domains.biology.virtual_cell.correction_records_v2 import SharedTemplateShiftV2Selection
from empirical_lawhood.domains.battery.battery_thermal_service.assessment import assess
from empirical_lawhood.domains.energy.grid2op.forecasting import Grid2OpForecastRule, build_grid2op_forecast_panel
assert len(Grid2OpForecastRule) == 6
assert SharedTemplateShiftV2Selection().VERSION == "2.0.0"
'''
    subprocess.run([sys.executable, "-c", script], check=True)


@pytest.mark.numerical(oracle="Two supplied residuals of one, divided by a floor of two, give a maximum normalized discrepancy of exactly one half")
def test_denominator_qualification_has_independent_normalized_error_oracle():
    from decimal import Decimal
    from empirical_lawhood.domains.fusion.denominator_response import _normalized_discrepancy
    assert _normalized_discrepancy(np.array([3., 1.]), np.array([2., 0.]), scale=Decimal(2)) == Decimal("0.5")


def test_denominator_qualification_preparation_defers_native_contact():
    script = '''
import importlib.abc
import sys
class ForbidNative(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".")[0] in {"gymtorax", "torax", "pybamm", "jax"}:
            raise AssertionError("scientific preparation entered a native runtime: " + fullname)
sys.meta_path.insert(0, ForbidNative())
from empirical_lawhood.domains.fusion.denominator_response import all_claim_bearing_cells, all_views, candidate_pairs
assert all_claim_bearing_cells()
assert all_views()
assert candidate_pairs()
'''
    subprocess.run([sys.executable, "-c", script], check=True)


def signed_fixture():
    """One 24-coordinate physical receiver with one nonzero coordinate.

    Full error is 4, reduced error is 3 and their difference is 1. This hand
    calculation fixes squared errors 16 and 9 and signed cross term 8.
    """
    cell = {field: field + ".case" for field in CELL_FIELDS}
    zero = [0.] * 24
    full, reduced, difference = (zero.copy() for _ in range(3))
    full[0], reduced[0], difference[0] = 4., 3., 1.
    matched = [
        {**cell, "comparison": name, "signed_frozen_error_low": zero.copy(),
         "signed_frozen_error_high": vector}
        for name, vector in (("FULL", full), ("INPUT_KRYLOV48", reduced))
    ]
    represented = [{**cell, "scope": "HIGH_MINUS_LOW", "regime": "FROZEN",
                    "signed_full_minus_reduced": difference}]
    return matched, represented


@pytest.mark.numerical(oracle="One-coordinate analytic control: full contrast 4, reduced contrast 3, squared errors 16/9 and twice alignment 8")
def test_signed_native_join_has_independent_analytic_control():
    matched, represented = signed_fixture()
    assert join_native_errors(matched, represented) == 0.
    result = represented[0]
    assert result["full_native_contrast_squared"] == 16.
    assert result["reduced_native_contrast_squared"] == 9.
    assert result["twice_full_error_representation_alignment"] == 8.
    assert result["signed_full_native_contrast_error"] == [4., *([0.] * 23)]
    assert result["signed_reduced_native_contrast_error"] == [3., *([0.] * 23)]


@pytest.mark.parametrize("defect", ("nan", "infinity", "short", "duplicate", "missing", "regime", "changed-sign"))
def test_native_join_refuses_invalid_values_and_incomplete_cell_census(defect):
    matched, represented = signed_fixture()
    if defect == "nan":
        matched[0]["signed_frozen_error_high"][0] = float("nan")
    elif defect == "infinity":
        represented[0]["signed_full_minus_reduced"][0] = float("inf")
    elif defect == "short":
        matched[1]["signed_frozen_error_low"] = [0.]
    elif defect == "duplicate":
        matched.append(deepcopy(matched[0]))
    elif defect == "missing":
        matched.pop()
    elif defect == "regime":
        represented[0]["regime"] = "unknown"
    else:
        represented[0]["signed_full_minus_reduced"][0] = -1.
    with pytest.raises(ValueError):
        join_native_errors(matched, represented)


def test_representation_summary_retains_full_and_numerically_evaluable_denominators():
    rows = [
        {"scope": "HIGH_MINUS_LOW", "group": "g", "numerically_evaluable": allowed,
         "inherited_squared": 1., "generated_squared": 1.,
         "twice_inherited_generated_alignment": alignment,
         "full_minus_reduced_squared": 2. + alignment}
        for allowed, alignment in ((True, -2.), (False, 2.))
    ]
    summaries = representation_summary(rows, ("group",))
    assert [(r["retained_cells"], r["cells"]) for r in summaries] == [(2, 2), (2, 1)]
    assert summaries[0]["sum_full_minus_reduced_squared"] == 4.
    assert summaries[1]["sum_full_minus_reduced_squared"] == 0.
    assert summaries[0]["negative_cross_terms"] == 1
    assert summaries[0]["positive_cross_terms"] == 1


def test_ordered_subcalculations_respect_capacity_and_join_before_return(monkeypatch):
    monkeypatch.setattr(parallel, "observe_capacity", lambda: SimpleNamespace(cpu_cores=1))
    entered = []
    thread = threading.get_ident()
    def calculate(value):
        entered.append((value, threading.get_ident()))
        return value * value
    assert parallel.ordered_task_map(calculate, (3, 1, 2), maximum_workers=2,
        thread_name_prefix="test.ordered") == (9, 1, 4)
    assert entered == [(3, thread), (1, thread), (2, thread)]
    monkeypatch.setattr(parallel, "observe_capacity", lambda: SimpleNamespace(cpu_cores=8))
    assert parallel.ordered_task_map(np.negative, (3, 1, 2), maximum_workers=2,
        thread_name_prefix="test.ordered") == (-3, -1, -2)


def test_subcalculation_exception_propagates_without_replaying(monkeypatch):
    monkeypatch.setattr(parallel, "observe_capacity", lambda: SimpleNamespace(cpu_cores=1))
    calls = []
    def fail(value):
        calls.append(value)
        raise ArithmeticError("selected numerical refusal")
    with pytest.raises(ArithmeticError, match="selected numerical refusal"):
        parallel.ordered_task_map(fail, (1, 2), maximum_workers=2, thread_name_prefix="test.failure")
    assert calls == [1]


def test_extracted_science_is_independently_owned():
    from empirical_lawhood.domains.matrix.finite_response_law.current_preparation import derive_preparation_operands
    from empirical_lawhood.domains.matrix.matrix_preparation_analysis.report_validation import validate_report_semantics
    from empirical_lawhood.domains.matrix.matrix_scheduled_history.replay_validation import validate_derived_arrays
    for operation in (derive_preparation_operands, validate_report_semantics, validate_derived_arrays,
                      join_native_errors, representation_summary):
        assert operation.__module__.startswith("empirical_lawhood.domains.")


@pytest.mark.numerical(oracle="Exact medians of consecutive integer sequences 0..63, 64..127, 128..191 and 192..255 are 31.5, 95.5, 159.5 and 223.5")
def test_extracted_history_family_medians_have_an_independent_integer_oracle():
    from decimal import Decimal
    from empirical_lawhood.domains.matrix.matrix_history_analysis.reductions import family_medians
    roots = [SimpleNamespace(root_index=index, disposition="COMPLETE",
        metrics=(("value", Decimal(index)),)) for index in range(256)]
    observed = family_medians(roots)
    assert tuple(values[0][1] for _, values in observed) == tuple(
        Decimal(value) for value in ("31.5", "95.5", "159.5", "223.5"))


def test_extracted_family_reduction_preserves_missingness_and_complete_census():
    from decimal import Decimal
    from empirical_lawhood.domains.matrix.matrix_history_analysis.reductions import family_medians
    roots = [SimpleNamespace(root_index=index, disposition="COMPLETE",
        metrics=(("value", Decimal(index)),)) for index in range(256)]
    roots[7].disposition = "UNEVALUABLE"
    assert family_medians(roots)[0][1] == (("value", None),)
    assert family_medians(roots)[1][1] == (("value", Decimal("95.5")),)
    with pytest.raises(ValueError, match="complete ordered 256-root census"):
        family_medians(roots[:-1])
    with pytest.raises(ValueError, match="complete ordered 256-root census"):
        family_medians(tuple(reversed(roots)))
