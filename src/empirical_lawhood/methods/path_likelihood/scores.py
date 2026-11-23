# SPDX-License-Identifier: MPL-2.0
"""Likelihood scores with physical laws, observation and clock supplied by callers."""

import numpy as np
from scipy.special import logsumexp
from scipy.stats import t


def gaussian_log_density(value, mean, variance):
    """Elementwise independent Gaussian density, including normalization."""
    variance = np.asarray(variance)
    if np.any(variance <= 0) or not np.isfinite(variance).all():
        raise ValueError("Gaussian density requires finite positive variance")
    return -0.5 * (np.log(2 * np.pi * variance) + np.square(value - mean) / variance)


def gaussian_joint_log_density(samples, mean, covariance):
    """Independent covariance-factorization oracle, one joint vector per row."""
    samples = np.asarray(samples)
    chol = np.linalg.cholesky(covariance)
    from scipy.linalg import solve_triangular

    centered = solve_triangular(chol, (samples - mean).T, lower=True)
    return (
        -0.5 * (np.sum(centered**2, axis=0) + len(mean) * np.log(2 * np.pi))
        - np.log(np.diag(chol)).sum()
    )


def mean_interval(values, alpha=0.05):
    values = np.asarray(values, dtype=float)
    if values.ndim != 1 or len(values) < 2 or not np.isfinite(values).all():
        raise ValueError(
            "interval requires at least two finite independent-unit measurements"
        )
    center = float(values.mean())
    error = float(
        t.isf(alpha / 2, len(values) - 1) * values.std(ddof=1) / np.sqrt(len(values))
    )
    return {
        "mean": center,
        "lower": center - error,
        "upper": center + error,
        "n": len(values),
    }


def bounded_path_kl(forward, reversed_reference, *, bound, alpha):
    """Held-out DV bound with simultaneous, distribution-free one-sided limits."""
    f, r = map(np.asarray, (forward, reversed_reference))
    if (
        not 0 < alpha < 1
        or not 0 < bound <= 20
        or min(len(f), len(r)) < 2
        or any(
            x.ndim != 1 or not np.isfinite(x).all() or np.max(np.abs(x)) > bound
            for x in (f, r)
        )
    ):
        raise ValueError("invalid fixed critic or independent path census")

    def upper_radius(width, n):
        return width * np.sqrt(np.log(2 / alpha) / (2 * n))

    mean = f.mean()
    moment = np.exp(r).mean()
    lower_mean = max(-bound, mean - upper_radius(2 * bound, len(f)))
    upper_moment = min(np.exp(bound), moment + upper_radius(2 * np.sinh(bound), len(r)))
    return {
        "estimate": float(mean - (logsumexp(r) - np.log(len(r)))),
        "lower": float(lower_mean - np.log(upper_moment)),
        "alpha": alpha,
        "forward_n": len(f),
        "reverse_n": len(r),
        "critic_bound": bound,
    }
