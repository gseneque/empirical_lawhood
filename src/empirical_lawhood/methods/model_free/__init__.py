# SPDX-License-Identifier: MPL-2.0
"""Reusable diagnostics and design-based estimators without fitted dynamics.

These numerical functions confer neither a physical clock nor a stationary
ensemble. Domain contracts must qualify those premises and independent roots.
"""

from .events import assess_first_passage, assess_paired_first_passage
from .finite_population import compare_finite_population_estimators, finite_population_difference
from .memory import assess_root_memory, assess_root_segments, memory_bound_feasibility, memory_diagnostics, root_lag_counts, root_segment_counts
from .observation import ObservationContract, discretize
from .uncertainty import allocate_alpha, hoeffding_halfwidth, root_mean_bands

__all__ = [
    "ObservationContract", "allocate_alpha", "assess_first_passage", "assess_paired_first_passage",
    "assess_root_memory", "assess_root_segments", "compare_finite_population_estimators", "discretize", "finite_population_difference",
    "hoeffding_halfwidth", "memory_bound_feasibility", "memory_diagnostics", "root_lag_counts", "root_segment_counts",
    "root_mean_bands",
]
