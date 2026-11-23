# SPDX-License-Identifier: MPL-2.0
"""Sensitivity of the early consequence residual to time quadrature on original histories."""

import numpy as np
from empirical_lawhood.methods.marked_process.consequences import (
    empirical_residual,
    paired_lower_contributions,
)
from empirical_lawhood.methods.path_likelihood.scores import mean_interval
from .experiment import OBSERVERS
from .physics import compressions, consequences, parameters, receivers, replay, system


def marked_diagnostics(options, batches):
    args = parameters(options)
    basis, _, propagator, _, initial = system(*args)
    sizes = [options["nodes"] * k for k in (1, 2, 4)]
    grids = [receivers(args, s) for s in sizes]
    offsets = np.r_[0, np.cumsum(sizes)]
    rows = [[] for _ in grids]
    replay_error, event_free_error, empty, n = 0.0, 0.0, 0, 0
    for batch in batches:
        for i in range(len(batch["evaluable_root"])):
            count = int(batch["count"][i])
            t = batch["times"][i, :count]
            marks = batch["marks"][i, :count]
            if not count:
                empty += 1
            for g, (clock, observable) in enumerate(grids):
                states = batch["native"][i, offsets[g] : offsets[g + 1]]
                weights, values = consequences(states, observable, basis, args[-1])
                reconstructed = replay(t, marks, clock, basis, propagator, initial)
                _, independent = consequences(
                    reconstructed, observable, basis, args[-1]
                )
                error = float(np.max(abs(independent - values)))
                replay_error = max(replay_error, error)
                if not count:
                    event_free_error = max(event_free_error, error)
                codes = compressions(t, marks, clock, basis.l_sites)
                rows[g].append((weights, values[:, :, 0], codes))
            n += 1
    norm = args[-1] * args[1]
    grids_out = []
    for size, samples in zip(sizes, rows, strict=True):
        w, y, c = map(np.stack, zip(*samples, strict=True))
        observed = {}
        for j, name in enumerate(OBSERVERS):
            code = c[:, :, j]
            ideal = (
                np.mean(
                    [
                        empirical_residual(code[:, k], w[:, k], y[:, k])
                        for k in range(size)
                    ]
                )
                / norm
            )
            pairs = (
                paired_lower_contributions(code, w, y, maximum_rate=args[-1])
                .sum(axis=2)
                .mean(axis=1)
                / norm
            )
            observed[name] = {
                "ideal_plugin_squared": float(ideal),
                "independent_pair_lower": mean_interval(
                    pairs, alpha=0.05 / (2 * len(OBSERVERS))
                ),
                "per_node_occupied_cells": [len(np.unique(col)) for col in code.T],
            }
        grids_out.append({"nodes": size, "observers": observed})
    return {
        "grids": grids_out,
        "replayed_consequence_max_error": replay_error,
        "event_free_replay_max_error": event_free_error,
        "event_free_histories": empty,
        "evaluable": n,
        "loss_normalization": norm,
        "diagnostic_scope": "ADDITIONAL_READ_OF_ORIGINALS",
    }
