"""Reusable supplied-array scientific records and calculations."""
import numpy as np
from empirical_lawhood.domains.matrix.matrix_preparation.projection import PROJECTION_SHAPES
from empirical_lawhood.domains.matrix.matrix_preparation.numerical_semantics import native_view_errors
from empirical_lawhood.domains.matrix.matrix_preparation_analysis.tangent_records import TangentPreparationConfig


def tangent_analysis(config: TangentPreparationConfig, arrays):
    """Full 128-root accounting and 6,400 nested mechanism comparisons.

    Paired native-view agreement retains all 128 roots. The mechanism subset
    is pre-outcome ranked: 16 roots per context. Coupled and scalar tangent
    comparisons remain diagnostics, never use-time forecasts.
    """
    for name, shape in PROJECTION_SHAPES.items():
        if name not in arrays or arrays[name].shape != (128, 2, *shape) or arrays[name].dtype != np.float64:
            raise ValueError("Tangent analysis changes the complete native projection axes")
    for name, shape in (("prefix_complete", (128, 2)), ("mechanism_complete", (128, 2)), ("native_complete", (128,))):
        if name not in arrays or arrays[name].shape != shape or arrays[name].dtype != np.bool_:
            raise ValueError("Tangent analysis lacks complete native disposition census")
    selected = np.asarray([root.numerical_semantics for root in config.roots], dtype=np.bool_)
    complete = arrays["native_complete"] & arrays["prefix_complete"].all(axis=1)
    mechanism_complete = complete & arrays["mechanism_complete"].all(axis=1)
    for name in ("amplitude_chi", "amplitude_even", "amplitude_position_error", "amplitude_momentum_error", "coupled_tangent", "scalar_tangent", "secant_receiver", "secant_position_error", "secant_momentum_error", "secant_position_norm", "secant_momentum_norm"):
        mechanism_complete &= np.isfinite(arrays[name]).reshape(128, -1).all(axis=1)
    response = arrays["response"].transpose(0, 2, 1, 3, 4, 5)
    absolute, odd = native_view_errors(response)
    numerical_complete = np.isfinite(absolute).reshape(128, -1).all(axis=1) & np.isfinite(odd).reshape(128, -1).all(axis=1)
    absolute_pass = np.max(absolute.reshape(128, -1), axis=1) <= 1 / 128
    odd_pass = np.max(odd.reshape(128, -1), axis=1) <= 1 / 256
    native_view_pass = complete & numerical_complete & absolute_pass & odd_pass
    secant_position = arrays["secant_position_error"] / (1e-8 + 1e-5 * arrays["secant_position_norm"])
    secant_momentum = arrays["secant_momentum_error"] / (1e-8 + 1e-5 * arrays["secant_momentum_norm"])
    secant_pass = (np.max(secant_position.reshape(128, -1), axis=1) <= 1) & (np.max(secant_momentum.reshape(128, -1), axis=1) <= 1)
    tangent = arrays["coupled_tangent"][:, :, :, None]
    scalar = arrays["scalar_tangent"][:, :, :, None]
    coupled_error = arrays["amplitude_chi"] - tangent
    scalar_error = arrays["amplitude_chi"] - scalar
    full_pass = selected & mechanism_complete & native_view_pass & secant_pass
    out = {"numerical_subset": selected, "native_complete": complete, "mechanism_complete": mechanism_complete,
           "absolute_view_error": absolute, "odd_view_error": odd, "absolute_pass": absolute_pass,
           "odd_pass": odd_pass, "native_view_pass": native_view_pass, "secant_position_ratio": secant_position,
           "secant_momentum_ratio": secant_momentum, "secant_pass": secant_pass,
           "numerical_pass": full_pass, "coupled_amplitude_error": coupled_error,
           "scalar_amplitude_error": scalar_error,
           "amplitude_even": arrays["amplitude_even"],
           "scalar_coupled_receiver_difference": arrays["scalar_tangent"] - arrays["coupled_tangent"],
           "finite_action_secant_tangent_difference": arrays["secant_receiver"] - arrays["coupled_tangent"],
           "development_role": np.asarray([("fit", "interval", "screen").index(root.development_role) for root in config.roots], dtype=np.int64)}
    metrics = {"independent_source_roots": 128, "independent_view_roots": 128, "independent_mechanism_roots": 32,
               "nested_mechanism_comparisons": 6400, "complete_source_roots": int(complete.sum()),
               "complete_mechanism_roots": int(np.sum(selected & mechanism_complete)),
               "native_view_passing_roots": int(native_view_pass.sum()),
               "numerical_passing_roots": int(full_pass.sum()),
               "absolute_view_failing_roots": int(np.sum(~complete | ~numerical_complete | ~absolute_pass)),
               "odd_view_failing_roots": int(np.sum(~complete | ~numerical_complete | ~odd_pass)),
               "secant_failing_roots": int(np.sum(selected & (~mechanism_complete | ~secant_pass)))}
    cohort = np.asarray([config.summary_context == "all" or root.context == config.summary_context for root in config.roots])
    usable = selected & mechanism_complete & cohort
    metrics["coupled_tangent_mse"] = float(np.mean(coupled_error[usable] ** 2)) if usable.any() else None
    metrics["scalar_tangent_mse"] = float(np.mean(scalar_error[usable] ** 2)) if usable.any() else None
    metrics["scalar_minus_coupled_mse"] = None if not usable.any() else metrics["scalar_tangent_mse"] - metrics["coupled_tangent_mse"]
    incomplete = tuple(root.root_id for index, root in enumerate(config.roots) if not complete[index] or not numerical_complete[index] or (selected[index] and not mechanism_complete[index]))
    return out, metrics, incomplete
