# SPDX-License-Identifier: MPL-2.0
"""Conditional intensity-weighted means and independent bounds on compression loss."""

import numpy as np


def moments(codes, weights, outcomes):
    """First and second weighted outcome moments by finite observed cell and mark."""
    cells, inv = np.unique(codes, return_inverse=True)

    def totals(x):
        return np.stack(
            [np.bincount(inv, weights=v, minlength=len(cells)) for v in x.T], axis=1
        )

    return (
        cells,
        totals(weights),
        totals(weights * outcomes),
        totals(weights * outcomes**2),
    )


def projection(codes, weights, outcomes, pooling):
    cells, mass, total, _ = moments(codes, weights, outcomes)
    global_mass = mass.sum(axis=0)
    baseline = np.divide(
        total.sum(axis=0),
        global_mass,
        out=np.zeros(mass.shape[1]),
        where=global_mass > 0,
    )
    denominator = mass + pooling
    means = np.divide(
        total + pooling * baseline,
        denominator,
        out=np.broadcast_to(baseline, mass.shape).copy(),
        where=denominator > 0,
    )
    return {
        "cells": cells.tolist(),
        "mean": means.tolist(),
        "fallback": baseline.tolist(),
    }


def apply_projection(codes, table):
    keys = np.asarray(table["cells"])
    index = np.minimum(np.searchsorted(keys, codes), len(keys) - 1)
    match = keys[index] == codes
    return np.where(
        match[..., None], np.asarray(table["mean"])[index], table["fallback"]
    ), match


def empirical_residual(codes, weights, outcomes):
    _, mass, total, second = moments(codes, weights, outcomes)
    explained = np.divide(total**2, mass, out=np.zeros_like(total), where=mass > 0)
    return float((second - explained).sum() / len(codes))


def paired_lower_contributions(codes, intensity, consequence, *, maximum_rate):
    """Independent matched-cell pairs give a lower bound on ideal within-cell risk.

    Each cell's true weighted variance is multiplied by its unconditional
    activity divided by the mark's upper intensity bound, always at most one.
    This lower bound needs no fitted cell means and remains valid for sparse bins.
    """
    n = len(codes) // 2
    even, odd = slice(0, 2 * n, 2), slice(1, 2 * n, 2)
    same = codes[even] == codes[odd]
    return (
        same[..., None]
        * intensity[even]
        * intensity[odd]
        * (consequence[even] - consequence[odd]) ** 2
        / (2 * maximum_rate)
    )
