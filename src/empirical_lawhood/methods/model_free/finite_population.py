# SPDX-License-Identifier: MPL-2.0
"""Frozen-auxiliary probability sampling of a finite native frame."""
import math

import numpy as np


def finite_population_difference(auxiliary, sampled_indices, native_values, *,
                                 inclusion_probabilities=None,
                                 sampling_design="srs_without_replacement",
                                 value_bounds=None, acquisition_mode="sparse", alpha=0.05):
    """Horvitz--Thompson residual correction, conditional on a frozen frame.

For SRS the design variance estimate includes the finite-population correction.
Unequal-probability sampling reports no variance unless independent Bernoulli
inclusion is explicitly declared. Missing sampled returns are never removed.
Native values must follow sampled_indices, including None for failed returns.
"""
    a = np.asarray(auxiliary, dtype=float)
    if a.ndim != 1 or not len(a) or not np.all(np.isfinite(a)):
        raise ValueError("a complete finite frozen auxiliary frame is required")
    indices = tuple(sampled_indices)
    values = tuple(native_values)
    if len(indices) != len(values) or any(type(i) is not int for i in indices):
        raise ValueError("sample indices and native outcomes must be aligned")
    if len(set(indices)) != len(indices) or any(i < 0 or i >= len(a) for i in indices):
        raise ValueError("sample indices must be distinct members of the frozen frame")
    if sampling_design not in {"srs_without_replacement", "independent_bernoulli", "known_inclusion"}:
        raise ValueError("undeclared probability sampling design")
    if acquisition_mode not in {"sparse", "reveal_all"}:
        raise ValueError("declare actual sparse acquisition or a reveal-all benchmark")
    if not math.isfinite(alpha) or not 0 < alpha < 1:
        raise ValueError("alpha must lie in (0,1)")
    n, population = len(indices), len(a)
    if sampling_design == "srs_without_replacement" and n == 0:
        return {"status": "UNRESOLVED", "reason": "no probability-sampled native outcomes", "frame_size": population,
                "sample_size": 0, "estimate": None, "actual_native_calls_omitted": population if acquisition_mode == "sparse" else 0}
    if inclusion_probabilities is None:
        if sampling_design != "srs_without_replacement":
            raise ValueError("unequal probability designs require all frame inclusion probabilities")
        probabilities = np.full(population, n/population)
    else:
        probabilities = np.asarray(inclusion_probabilities, dtype=float)
        if probabilities.shape != a.shape or not np.all(np.isfinite(probabilities)) or np.any(probabilities <= 0) or np.any(probabilities > 1):
            raise ValueError("every frame unit needs a known positive inclusion probability <=1")
        if sampling_design == "srs_without_replacement" and not np.allclose(probabilities, n/population, rtol=0, atol=1e-14):
            raise ValueError("SRS inclusion probabilities must equal sample_size/frame_size")
    if value_bounds is not None:
        if len(value_bounds) != 2 or not all(math.isfinite(float(x)) for x in value_bounds) or value_bounds[1] < value_bounds[0]:
            raise ValueError("native value bounds must be finite and ordered")
        lower_value, upper_value = map(float, value_bounds)
    else:
        lower_value = upper_value = None
    residuals, weights, missing = [], [], []
    for i, value in zip(indices, values):
        if value is None:
            missing.append(i)
            continue
        value = float(value)
        if not math.isfinite(value):
            raise ValueError("failed native values must be represented explicitly by None")
        if value_bounds is not None and not lower_value <= value <= upper_value:
            raise ValueError("observed native value violates the declared physical bound")
        residuals.append(value-a[i])
        weights.append(1/probabilities[i])
    partial = float(a.mean()+np.dot(weights, residuals)/population)
    result = {
        "status": "ESTIMATED" if not missing else "UNRESOLVED",
        "estimate": partial if not missing else None,
        "frame_size": population, "sample_size": n, "completed_native_returns": n-len(missing),
        "missing_sampled_indices": missing, "sampled_indices": list(indices),
        "sampled_inclusion_probabilities": [float(probabilities[i]) for i in indices],
        "sampling_design": sampling_design, "acquisition_mode": acquisition_mode,
        "declared_frame_units_selected_for_acquisition": n if acquisition_mode == "sparse" else population,
        "actual_native_calls_omitted": population-n if acquisition_mode == "sparse" else 0,
        "counterfactual_calls_omitted": population-n,
        "design_unbiased_if_complete": True,
        "target": "fixed-frame native mean conditional on frozen auxiliaries and declared randomization",
        "variance_estimate": None, "standard_error": None,
        "work_count_scope": "frame-unit acquisition selection; measured native calls and partial failures belong to execution receipts",
    }
    if missing:
        result["reason"] = "sampled native failures retain their inclusion-weighted unresolved contribution"
        if value_bounds is not None:
            result["missing_return_estimator_bounds"] = [
                partial+sum((lower_value-a[i])/probabilities[i] for i in missing)/population,
                partial+sum((upper_value-a[i])/probabilities[i] for i in missing)/population,
            ]
        return result
    residuals = np.asarray(residuals, dtype=float)
    if sampling_design == "srs_without_replacement":
        if n == population:
            variance = 0.0
        elif n >= 2:
            variance = float((1-n/population)*np.var(residuals, ddof=1)/n)
        else:
            variance = None
    elif sampling_design == "independent_bernoulli":
        variance = float(sum((1-probabilities[i])/probabilities[i]**2 * residual**2
                             for i, residual in zip(indices, residuals))/population**2)
    else:
        variance = None
    result["variance_estimate"] = variance
    result["standard_error"] = None if variance is None else math.sqrt(variance)
    result["variance_meaning"] = "design variance estimate; not a confidence certificate or per-instance accuracy"
    if n == population and sampling_design == "srs_without_replacement":
        result["confidence_interval"] = [partial, partial]
        result["confidence_meaning"] = "complete finite-frame enumeration"
    elif value_bounds is not None and sampling_design == "srs_without_replacement":
        # Sampling without replacement is at least as concentrated as iid
        # sampling for Hoeffding's bounded finite-frame mean inequality.
        residual_range = (upper_value-float(a.min()))-(lower_value-float(a.max()))
        halfwidth = residual_range*math.sqrt(math.log(2/alpha)/(2*n))
        interval = [max(lower_value, partial-halfwidth), min(upper_value, partial+halfwidth)]
        result["confidence_interval"] = interval if interval[0] <= interval[1] else None
        if interval[0] > interval[1]:
            result["status"] = "UNRESOLVED"
            result["reason"] = "empty confidence set after intersecting the declared physical range"
        result["confidence_meaning"] = "conservative bounded SRS finite-frame Hoeffding interval"
        result["alpha"] = alpha
    return result


def compare_finite_population_estimators(auxiliary, sampled_indices, native_values, *,
                                        full_native_values=None, value_bounds=None,
                                        acquisition_mode="sparse", alpha=0.05):
    """Compare frozen-auxiliary and direct SRS means on the identical audit.

    This calculation does not choose a sample or fit an auxiliary. Full-frame
    outcomes are permitted only for a reveal-all benchmark. Their exact design
    variances describe hypothetical repeated SRS audits of that fixed frame;
    they are not observed savings or an accuracy guarantee for another frame.
    """
    if not math.isfinite(alpha) or not 0 < alpha < 1:
        raise ValueError("alpha must lie in (0,1)")
    a = np.asarray(auxiliary, dtype=float)
    indices, values = tuple(sampled_indices), tuple(native_values)
    options = dict(value_bounds=value_bounds, acquisition_mode=acquisition_mode,
                   alpha=alpha / 2)
    corrected = finite_population_difference(a, indices, values, **options)
    direct = finite_population_difference(np.zeros_like(a), indices, values, **options)
    n, population = len(indices), len(a)
    result = {
        "status": "ESTIMATED" if corrected["status"] == direct["status"] == "ESTIMATED" else "UNRESOLVED",
        "residual_correction": corrected, "direct_sampling": direct,
        "same_frozen_frame_and_sample": True,
        "baseline": "DIRECT_SRS_SAMPLE_MEAN_EQUIVALENT_TO_ANY_FROZEN_CONSTANT_AUXILIARY",
        "paired_estimator_covariance_estimate": None,
        "paired_estimator_difference_variance_estimate": None,
        "variance_ratio_corrected_over_direct": None,
        "alpha": alpha, "alpha_allocation": "equal allocation across the two bounded-mean intervals",
        "full_frame_benchmark": None,
    }
    if n and all(value is not None for value in values):
        y = np.asarray(values, dtype=float)
        residuals = y - a[list(indices)]
        if n == population:
            covariance, difference_variance = 0., 0.
        elif n >= 2:
            factor = (1 - n / population) / n
            covariance = float(factor * np.cov(residuals, y, ddof=1)[0, 1])
            difference_variance = float(factor * np.var(a[list(indices)], ddof=1))
        else:
            covariance = difference_variance = None
        result["paired_estimator_covariance_estimate"] = covariance
        result["paired_estimator_difference_variance_estimate"] = difference_variance
        direct_variance = direct.get("variance_estimate")
        if direct_variance is not None and direct_variance > 0:
            result["variance_ratio_corrected_over_direct"] = corrected["variance_estimate"] / direct_variance
    if full_native_values is not None:
        if acquisition_mode != "reveal_all":
            raise ValueError("full-frame native outcomes belong only to a reveal-all benchmark")
        full = tuple(full_native_values)
        if len(full) != population:
            raise ValueError("reveal-all outcomes must cover the complete frozen frame")
        missing = [i for i, value in enumerate(full) if value is None]
        for index, value in zip(indices, values, strict=True):
            if full[index] != value:
                raise ValueError("audit and reveal-all outcomes disagree for the same frame member")
        if any(value is not None and not math.isfinite(float(value)) for value in full):
            raise ValueError("failed reveal-all outcomes must be explicit None values")
        benchmark = {"status": "UNRESOLVED" if missing else "ENUMERATED",
                     "missing_frame_indices": missing, "full_frame_mean": None,
                     "actual_native_calls_omitted": 0,
                     "counterfactual_calls_omitted": population - n,
                     "scope": "exact repeated-SRS design moments conditional on this revealed frame"}
        if not missing:
            full = np.asarray(full, dtype=float)
            if value_bounds is not None and (np.any(full < value_bounds[0]) or np.any(full > value_bounds[1])):
                raise ValueError("reveal-all outcome violates the declared physical bound")
            benchmark["full_frame_mean"] = float(full.mean())
            if n:
                factor = (1 - n / population) / n
                residual = full - a
                # A singleton frame can only be a census and has zero variance.
                cov = np.zeros((2, 2)) if population == 1 else factor * np.cov(residual, full, ddof=1)
                benchmark.update(corrected_design_variance=float(cov[0, 0]),
                                 direct_design_variance=float(cov[1, 1]),
                                 paired_design_covariance=float(cov[0, 1]),
                                 corrected_error=float(corrected["estimate"] - full.mean()),
                                 direct_error=float(direct["estimate"] - full.mean()),
                                 variance_ratio_corrected_over_direct=(float(cov[0, 0] / cov[1, 1]) if cov[1, 1] > 0 else None))
        result["full_frame_benchmark"] = benchmark
    return result
