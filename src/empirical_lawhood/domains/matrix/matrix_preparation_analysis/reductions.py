# SPDX-License-Identifier: MPL-2.0
"""Current preparation population rules and reductions over authenticated operands.

Callers own custody. These operations consume arrays and scientific records without
filesystem access, publication, discovery or native acquisitions.
"""

from decimal import Decimal
import numpy as np
from empirical_lawhood.domains.matrix.matrix_preparation_analysis.records import PreparationAnalysisMetric
from empirical_lawhood.domains.matrix.matrix_preparation_analysis.transient import transient_analysis, validate_operands, baseline_support_analysis as evaluate


def analysis_metrics(values):
    return tuple(PreparationAnalysisMetric(name, None if value is None or not np.isfinite(value) else Decimal(str(float(value))))
                 for name, value in sorted(values.items()))



def transient_response_evaluation(config, native_arrays, arrays, allocation, lower):
    """Keep all 24 independent roots and the frozen all/q2/cir1 summary selection."""
    for name in ("x", "z", "y", "features"):
        if name not in native_arrays or name not in arrays or not np.array_equal(native_arrays[name], arrays[name], equal_nan=True):
            raise ValueError("Transient bridge changes authenticated current native operands")
    if ("requested_ticks" not in native_arrays or not np.array_equal(native_arrays["requested_ticks"], np.tile(np.arange(0, 401, 16), (24, 1)) + 4096)
            or tuple(root.cohort for root in allocation.roots) != ("q2",) * 8 + ("cir1",) * 16):
        raise ValueError("Transient analysis changes source clocks or complete cohort order")
    incomplete_indices = set(validate_operands(arrays, lower))
    for name in ("parent_complete", "response_observed"):
        value = native_arrays.get(name)
        expected = (24, 9, 2) if name == "parent_complete" else (24, 9, 4, 8, 2, 2)
        if not isinstance(value, np.ndarray) or value.shape != expected or value.dtype != np.bool_:
            raise ValueError("Transient analysis lacks the complete native observation census")
        incomplete_indices.update(np.flatnonzero(~value.reshape(24, -1).all(axis=1)).tolist())
    incomplete = tuple(allocation.roots[index].root_id for index in sorted(incomplete_indices))
    if incomplete:
        out = {"missing_roots": np.asarray([index in incomplete_indices for index in range(24)], dtype=np.bool_)}
        metrics = {"independent_roots": 24, "complete_roots": 24 - len(incomplete), "outer_fits": 0, "inner_fits": 0}
    else:
        out = transient_analysis(arrays, lower)
        out["missing_roots"] = np.zeros(24, dtype=np.bool_)
        selection = slice(None) if config.summary_population == "all" else slice(0, 8) if config.summary_population == "q2" else slice(8, 24)
        metrics = {"independent_roots": 24, "complete_roots": 24, "outer_fits": 32, "new_outer_fits": 28, "reused_outer_fits": 4, "inner_fits": 24}
        for name, value in out.items():
            if name.endswith("mse_by_root"):
                metrics[name + ".summary"] = float(np.mean(value[selection]))
        for key in ("radial.all", "nonrestoring.all"):
            metrics[key + ".exploratory_covered_roots"] = int(out[key + ".exploratory_response_covered"].sum())
            metrics[key + ".enclosed_support_cells"] = int(out[key + ".enclosed_support"].sum())
    return out, metrics, incomplete


def baseline_response_evaluation(config, parent, allocation, arrays, lower):
    """Assess saved forecasts without fitting or native replay."""
    if parent.disposition == "UNEVALUABLE":
        out = {"missing_roots": np.asarray([root.root_id in parent.incomplete_roots for root in allocation.roots], dtype=np.bool_)}
        metrics = {"support.total_cells": 216, "independent_roots": 24, "complete_roots": 24 - len(parent.incomplete_roots)}
    else:
        out, metrics = evaluate(arrays, lower, model=config.model)
        metrics.update(independent_roots=24, complete_roots=24)
    return out, metrics


def tangent_source_arrays(config, projected):
    """Project the complete fixed source census, retaining every incomplete root."""
    arrays = {name: np.stack([row[name] for row in projected]) for name in projected[0]}
    incomplete = tuple(root.root_id for index, root in enumerate(config.roots)
        if not arrays["native_complete"][index] or not arrays["prefix_complete"][index].all())
    metrics = {"independent_source_roots": 128, "complete_source_roots": 128 - len(incomplete),
        "independent_mechanism_roots": 32}
    return arrays, incomplete, metrics
