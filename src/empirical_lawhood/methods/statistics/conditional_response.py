# SPDX-License-Identifier: MPL-2.0
"""Scores for paired conditional-mean forecasts and joint trajectory ensembles."""

import numpy as np
from scipy.spatial.distance import pdist


def independent_product(first, second):
    a, b = np.asarray(first), np.asarray(second)
    if a.shape != b.shape or not a.size:
        raise ValueError("independent panels must have identical nonempty axes")
    return a * b


def paired_mean_loss(prediction, panel_a, panel_b):
    return independent_product(prediction - panel_a, prediction - panel_b)


def root_interval(values, *, alpha=0.05, seed=280131, draws=20000):
    """Percentile interval, resampling independent roots with all their nested measurements."""
    x = np.asarray(values, dtype=float)
    if x.ndim != 1 or len(x) < 2 or not np.isfinite(x).all():
        raise ValueError("interval requires at least two finite independent roots")
    rng = np.random.default_rng(seed)
    sample = np.empty(draws)
    for start in range(0, draws, 128):
        size = min(128, draws - start)
        sample[start : start + size] = x[
            rng.integers(len(x), size=(size, len(x)))
        ].mean(axis=1)
    lo, hi = np.quantile(sample, [alpha / 2, 1 - alpha / 2])
    return dict(mean=float(x.mean()), lower=float(lo), upper=float(hi), n=len(x))


def fair_energy(draws, truth):
    """Fair ensemble energy score averaged over independent reference vectors."""
    x, y = np.asarray(draws), np.atleast_2d(truth)
    if x.ndim != 2 or len(x) < 2 or x.shape[1] != y.shape[1]:
        raise ValueError(
            "trajectory draws require a common vector space and independent samples"
        )
    return float(np.linalg.norm(x[:, None] - y, axis=-1).mean() - pdist(x).mean() / 2)


def ridge_fit(x, y, penalty):
    """One standardised linear fit and intercept for each response coordinate."""
    from empirical_lawhood.methods.causal_access_tournament import (
        FeatureMap,
        fit_standardized_ridge,
    )

    y = np.asarray(y).reshape(len(x), -1)
    fits = [
        fit_standardized_ridge(
            x, column, feature_map=FeatureMap.LINEAR, ridge_alpha=penalty
        )
        for column in y.T
    ]
    return dict(
        center=list(fits[0].center),
        scale=list(fits[0].scale),
        coefficients=[list(f.coefficients) for f in fits],
        intercept=[f.intercept for f in fits],
        penalty=penalty,
    )


def ridge_predict(x, fit):
    z = (np.asarray(x) - fit["center"]) / fit["scale"]
    return z @ np.asarray(fit["coefficients"]).T + fit["intercept"]
