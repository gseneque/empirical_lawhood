# SPDX-License-Identifier: MPL-2.0
"""Pure complete-array comparison controls; no fixture coordinates or RNG."""
import numpy as np
import pytest
from empirical_lawhood.api.matrix_native_acquisition_replay import _same_values


def test_nonuse_nan_in_complex_component_cannot_hide_changed_finite_component():
    expected = np.asarray([complex(float("nan"), 1)], dtype="<c16")
    changed = np.asarray([complex(float("nan"), 2)], dtype="<c16")
    with pytest.raises(PermissionError, match="received array values"):
        _same_values({"frame": changed}, {"frame": expected}, "causal")
    _same_values({"frame": expected.copy()}, {"frame": expected}, "causal")


@pytest.mark.parametrize("defect", ("member", "dtype", "shape", "finite"))
def test_complete_derived_arrays_refuse_thinning_and_changed_finite_values(defect):
    expected = {"observed": np.asarray([1, 2], dtype="<f8")}
    changed = dict(expected)
    if defect == "member":
        changed = {}
    elif defect == "dtype":
        changed["observed"] = expected["observed"].astype("<f4")
    elif defect == "shape":
        changed["observed"] = expected["observed"][:1]
    else:
        changed["observed"] = np.asarray([1, 3], dtype="<f8")
    with pytest.raises(PermissionError, match="native derived replay"):
        _same_values(changed, expected, "diagnostic")
