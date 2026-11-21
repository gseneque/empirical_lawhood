# SPDX-License-Identifier: MPL-2.0
"""Root-valid bounded inference; within-root observations may be dependent."""
import math

import numpy as np


def _alpha(alpha):
    alpha = float(alpha)
    if not math.isfinite(alpha) or not 0 < alpha < 1:
        raise ValueError("alpha must lie strictly between zero and one")
    return alpha


def allocate_alpha(alpha, *, comparisons=1, look_index=0, looks=1):
    """Uniform finite-family spending, including every record-length look."""
    alpha = _alpha(alpha)
    if any(type(x) is not int for x in (comparisons, look_index, looks)):
        raise TypeError("family sizes and look index must be integers")
    if comparisons < 1 or looks < 1 or not 0 <= look_index < looks:
        raise ValueError("invalid prespecified comparison/look family")
    return alpha / (comparisons * looks)


def hoeffding_halfwidth(n, event_count, alpha=0.05):
    alpha = _alpha(alpha)
    if type(n) is not int or type(event_count) is not int or n < 1 or event_count < 1:
        raise ValueError("positive independent-root and event counts are required")
    return min(1.0, math.sqrt(math.log(2 * event_count / alpha) / (2 * n)))


def root_mean_bands(root_vectors, *, alpha=0.05, simplex=True):
    """Simultaneous intervals for equal-weight independent-root means.

No iid time-origin, mixing or stationarity assumption is made. Independent
roots and bounded coordinates are assumptions supplied by the caller.
"""
    x = np.asarray(root_vectors, dtype=float)
    if x.ndim != 2 or not x.shape[0] or not x.shape[1]:
        raise ValueError("provide an independent-root by event matrix")
    if not np.all(np.isfinite(x)) or np.any(x < 0) or np.any(x > 1):
        raise ValueError("root event frequencies must lie in [0,1]")
    if simplex and not np.allclose(x.sum(axis=1), 1, atol=1e-12, rtol=0):
        raise ValueError("joint laws must retain all event probability mass")
    halfwidth = hoeffding_halfwidth(len(x), x.shape[1], alpha)
    mean = x.mean(axis=0)
    lower, upper = np.maximum(0, mean-halfwidth), np.minimum(1, mean+halfwidth)
    if simplex:
        # Intersect coordinate bands with the unit simplex. Simultaneous
        # coverage is preserved; no independence of cells is assumed.
        old_lower, old_upper = lower.copy(), upper.copy()
        lower = np.maximum(old_lower, 1-(old_upper.sum()-old_upper))
        upper = np.minimum(old_upper, 1-(old_lower.sum()-old_lower))
    return {"mean": mean.tolist(), "lower": lower.tolist(), "upper": upper.tolist(),
            "halfwidth": halfwidth, "alpha": float(alpha), "independent_roots": len(x),
            "event_count": x.shape[1], "meaning": "simultaneous independent-root Hoeffding",
            "target": "mean of declared bounded root-level finite-record frequencies"}


def conditional_bands(lower, upper, *, denominator_bounds=None):
    """Enclose a normalized row only if its denominator is bounded positive."""
    lower, upper = np.asarray(lower, dtype=float), np.asarray(upper, dtype=float)
    if lower.ndim != 1 or lower.shape != upper.shape or not len(lower):
        raise ValueError("conditional numerator bands must be equal nonempty vectors")
    if not np.all(np.isfinite(lower)) or not np.all(np.isfinite(upper)) or np.any(lower < 0) or np.any(upper < lower):
        raise ValueError("invalid probability bands")
    denominator_lower, denominator_upper = float(lower.sum()), float(upper.sum())
    if denominator_bounds is not None:
        if (len(denominator_bounds) != 2 or not all(math.isfinite(v) for v in denominator_bounds)
                or denominator_bounds[0] < 0 or denominator_bounds[1] < denominator_bounds[0]):
            raise ValueError("invalid conditioning-probability interval")
        denominator_lower = max(denominator_lower, denominator_bounds[0])
        denominator_upper = min(denominator_upper, denominator_bounds[1])
        if denominator_upper < denominator_lower:
            raise ValueError("joint and marginal probability intervals are inconsistent")
    if denominator_lower <= 0:
        return None
    lo_den = lower + upper.sum() - upper
    hi_den = upper + lower.sum() - lower
    lo = np.maximum(lower/denominator_upper,
                    np.divide(lower, lo_den, out=np.zeros_like(lower), where=lo_den > 0))
    hi = np.minimum(upper/denominator_lower,
                    np.divide(upper, hi_den, out=np.zeros_like(upper), where=hi_den > 0))
    return np.clip(lo, 0, 1), np.clip(hi, 0, 1)


def zero_failure_upper(n, *, alpha=0.05):
    """One-sided exact binomial bound; n is independently admitted units."""
    alpha = _alpha(alpha)
    if type(n) is not int or n < 0:
        raise ValueError("admitted-unit count must be a nonnegative integer")
    return 1.0 if n == 0 else -math.expm1(math.log(alpha)/n)


def whole_root_bootstrap(root_values, *, alpha=0.05, repetitions=2000, seed=0):
    """Explicitly approximate percentile interval, resampling whole roots."""
    alpha = _alpha(alpha)
    x = np.asarray(root_values, dtype=float)
    if x.ndim not in (1, 2) or len(x) < 2 or not np.all(np.isfinite(x)):
        raise ValueError("at least two complete finite independent-root values are required")
    if type(repetitions) is not int or repetitions < 2:
        raise ValueError("at least two bootstrap repetitions are required")
    rng = np.random.default_rng(seed)
    estimates = np.asarray([x[rng.integers(0, len(x), len(x))].mean(axis=0) for _ in range(repetitions)])
    bounds = np.quantile(estimates, [alpha/2, 1-alpha/2], axis=0)
    return {"estimate": x.mean(axis=0).tolist(), "lower": bounds[0].tolist(),
            "upper": bounds[1].tolist(), "independent_roots": len(x), "alpha": alpha,
            "meaning": "approximate whole-root percentile bootstrap; no finite-sample coverage certificate"}
