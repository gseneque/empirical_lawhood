# SPDX-License-Identifier: MPL-2.0
"""Scientific metric roles, complete denominators and missingness semantics.

Validation consumes retained records and arrays without I/O or recomputation.
"""
import numpy as np
from .records import TransientAnalysisConfig


TRANSIENT_INPUT_ROLES = (
    "native-arrays", "native-manifest", "bridge-arrays", "bridge-manifest", "bridge-input", "bridge-spec",
    "original-f-operand", "original-payload", "original-manifest", "original-commit", "original-calibration", "original-qualification",
)


def metric_names(kind, *, incomplete):
    if kind == "TANGENT_SOURCE":
        return {"independent_source_roots", "complete_source_roots", "independent_mechanism_roots"}
    if kind == "TANGENT_ANALYSIS":
        return set(("independent_source_roots", "independent_view_roots", "independent_mechanism_roots",
                    "nested_mechanism_comparisons", "complete_source_roots", "complete_mechanism_roots",
                    "native_view_passing_roots", "numerical_passing_roots", "absolute_view_failing_roots",
                    "odd_view_failing_roots", "secant_failing_roots", "coupled_tangent_mse", "scalar_tangent_mse",
                    "scalar_minus_coupled_mse"))
    if kind == "BASELINE_SUPPORT":
        if incomplete:
            return {"support.total_cells", "independent_roots", "complete_roots"}
        return {"independent_roots", "complete_roots", "support.total_cells", "support.failure_roots",
                "support.true_supported", "support.true_unsupported", "support.false_supported", "support.false_unsupported",
                "feature.baseline_mse", "feature.transient_mse", "feature.cross_term", "feature.total_mse",
                "response.lower_mse", "response.baseline_mse", "response.transient_mse", "response.total_mse",
                "response.cross_lower_baseline", "response.cross_lower_transient", "response.cross_baseline_transient"}
    if incomplete:
        return {"independent_roots", "complete_roots", "outer_fits", "inner_fits"}
    prefixes = tuple(model + "." + regime for model in ("radial", "nonrestoring")
                     for regime in ("all", "early_time", "duration_transfer", "recovery_transfer"))
    names = {"independent_roots", "complete_roots", "outer_fits", "new_outer_fits", "reused_outer_fits", "inner_fits"}
    names.update(prefix + "." + part + "_mse_by_root.summary"
                 for prefix in ("actual_handoff_f", "current_u2", "predicted_hold_only", *prefixes)
                 for part in ("feature", "response"))
    names.update(prefix + "." + part + "_mse_by_root.summary" for prefix in prefixes
                 for part in ("measured_hold_diagnostic.response", "increment", "transfer", "trajectory", "late"))
    names.update(model + ".all." + role for model in ("radial", "nonrestoring")
                 for role in ("exploratory_covered_roots", "enclosed_support_cells"))
    return names


def validate_report_semantics(report, *, config, arrays, inputs):
    kind = inputs.analysis_kind
    values = {metric.name: metric.value for metric in report.metrics}
    if set(values) != metric_names(kind, incomplete=bool(report.incomplete_roots)):
        raise ValueError("Preparation report changes its closed metric roles")
    if any(value is not None and value < 0 and ("cross" not in name and name != "scalar_minus_coupled_mse")
           for name, value in values.items()):
        raise ValueError("Preparation report has an impossible nonnegative diagnostic/count")
    def count(name, expected):
        if values.get(name) != expected:
            raise ValueError("Preparation report count differs from its retained observation census")
    def boolean(name, shape):
        value = arrays.get(name)
        if not isinstance(value, np.ndarray) or value.dtype != np.bool_ or value.shape != shape:
            raise ValueError("Preparation report lacks its exact retained missingness census")
        return value
    if kind.startswith("TANGENT"):
        from empirical_lawhood.domains.matrix.matrix_preparation_analysis.tangent_records import TangentPreparationConfig
        if (type(config) is not TangentPreparationConfig or report.provenance.dependency_lock_sha256 != config.dependency_lock_sha256
                or report.provenance.code_sources_sha256 != config.code_sources_sha256):
            raise ValueError("Tangent report changes its selected configuration/lock")
        shard_names = tuple(root.root_id + suffix for root in config.roots
                            for suffix in (".prefix.canonical.json", ".prefix.h5", ".native.canonical.json", ".native.h5"))
        expected_roles = shard_names if kind == "TANGENT_SOURCE" else ("source-report", "source-arrays", "source-manifest", *shard_names)
        if inputs.roles != expected_roles or tuple(value.artifact_id for value in inputs.artifacts[-512:]) != shard_names:
            raise ValueError("Tangent report changes its full source input role census")
        complete = boolean("native_complete", (128,))
        if kind == "TANGENT_SOURCE":
            complete = complete & boolean("prefix_complete", (128, 2)).all(axis=1)
            incomplete = ~complete
        else:
            selected = boolean("numerical_subset", (128,))
            if not np.array_equal(selected, [root.numerical_semantics for root in config.roots]):
                raise ValueError("Tangent report changes its pre-outcome numerical subset")
            mechanism = boolean("mechanism_complete", (128,))
            numerical_complete = np.isfinite(arrays["absolute_view_error"]).reshape(128, -1).all(axis=1) & np.isfinite(arrays["odd_view_error"]).reshape(128, -1).all(axis=1)
            incomplete = ~complete | ~numerical_complete | (selected & ~mechanism)
            count("independent_view_roots", 128)
            count("nested_mechanism_comparisons", 6400)
            count("complete_mechanism_roots", int(np.sum(selected & mechanism)))
            count("native_view_passing_roots", int(boolean("native_view_pass", (128,)).sum()))
            count("numerical_passing_roots", int(boolean("numerical_pass", (128,)).sum()))
        count("independent_source_roots", 128)
        count("independent_mechanism_roots", 32)
        count("complete_source_roots", int(complete.sum()))
    else:
        expected_kind = "TRANSIENT_ANALYSIS" if type(config) is TransientAnalysisConfig else "BASELINE_SUPPORT"
        expected_roles = TRANSIENT_INPUT_ROLES if kind == "TRANSIENT_ANALYSIS" else ("transient-report", "transient-arrays", "transient-manifest", *("parent." + role for role in TRANSIENT_INPUT_ROLES))
        if kind != expected_kind or inputs.roles != expected_roles:
            raise ValueError("Preparation report changes its closed scientific input roles")
        incomplete = boolean("missing_roots", (24,))
        count("independent_roots", 24)
        count("complete_roots", 24 - int(incomplete.sum()))
        if kind == "TRANSIENT_ANALYSIS":
            count("outer_fits", 0 if incomplete.any() else 32)
            count("inner_fits", 0 if incomplete.any() else 24)
        else:
            count("support.total_cells", 216)
            if not incomplete.any():
                actual, predicted = boolean("actual_support", (24, 9)), boolean("predicted_support", (24, 9))
                count("support.true_supported", int(np.sum(actual & predicted)))
                count("support.true_unsupported", int(np.sum(~actual & ~predicted)))
                count("support.false_supported", int(np.sum(~actual & predicted)))
                count("support.false_unsupported", int(np.sum(actual & ~predicted)))
                count("support.failure_roots", int(np.any(~actual, axis=1).sum()))
    expected_missing = tuple(sorted(root for root, missing in zip(report.root_ids, incomplete, strict=True) if missing))
    if report.incomplete_roots != expected_missing or (report.disposition == "COMPLETE") != (not incomplete.any()):
        raise ValueError("Preparation report disposition differs from its retained array missingness")

