# SPDX-License-Identifier: MPL-2.0
"""Fit a bounded directional score once, then apply it unchanged to either law."""

import numpy as np


def fit_linear_critic(forward, reference, *, bound):
    pooled = np.vstack((forward, reference))
    center = pooled.mean(axis=0)
    scale = pooled.std(axis=0)
    scale[scale < 1e-10] = 1.0
    z = (pooled - center) / scale
    labels = np.repeat([1.0, -1.0], [len(forward), len(reference)])
    weight = np.linalg.solve(z.T @ z + len(z) * 0.1 * np.eye(z.shape[1]), z.T @ labels)
    return {
        "center": center.tolist(),
        "scale": scale.tolist(),
        "weight": weight.tolist(),
        "bound": bound,
    }


def apply_linear_critic(rows, decision):
    return decision["bound"] * np.tanh(
        2
        * ((rows - np.asarray(decision["center"])) / decision["scale"])
        @ np.asarray(decision["weight"])
    )
