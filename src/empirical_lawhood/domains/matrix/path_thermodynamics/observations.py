# SPDX-License-Identifier: MPL-2.0
"""Time orientation precedes every observation, including causal filtering."""

import numpy as np
from empirical_lawhood.methods.path_likelihood.critics import (
    apply_linear_critic,
    fit_linear_critic,
)
from empirical_lawhood.methods.path_likelihood.scores import bounded_path_kl


def path_features(paths):
    """Same position-only features on either ensemble at identical clock times."""
    ticks = paths.shape[1] - 1
    marked = paths[:, np.linspace(0, ticks, 5, dtype=int)]
    mean = paths.mean(axis=1)
    return np.concatenate(
        (marked.reshape(len(paths), -1), mean, (paths[:, -1] - paths[:, 0]) * mean),
        axis=1,
    )


def window_labels(series, threshold, *, trailing):
    from numpy.lib.stride_tricks import sliding_window_view

    # Both label orders can use three true samples on each side of this clock.
    if series.shape[1] < 8:
        return np.empty((len(series), 0), dtype=bool)
    values = (
        sliding_window_view(series, 4, axis=1).mean(axis=-1)[:, :-3]
        if trailing
        else series[:, 3:-3]
    )
    return values >= threshold


def label_features(labels):
    values = labels.astype(float)
    n = values.shape[1]
    chunks = [v.mean(axis=1) for v in np.array_split(values, min(4, n), axis=1)]
    switches = (
        np.abs(np.diff(values, axis=1)).mean(axis=1) if n > 1 else np.zeros(len(values))
    )
    return np.column_stack((*chunks, values[:, 0], values[:, -1], switches))


def history_contexts(values):
    from numpy.lib.stride_tricks import sliding_window_view

    census = {}
    for depth in (1, 2, 4, 8):
        counts = np.zeros((2**depth, 2), dtype=np.int64)
        if values.shape[1] > depth:
            words = sliding_window_view(values, depth + 1, axis=1)
            indices = words[:, :, :-1] @ (2 ** np.arange(depth - 1, -1, -1))
            np.add.at(counts, (indices.ravel(), words[:, :, -1].astype(int).ravel()), 1)
        census[str(depth)] = {
            "next_zero_and_one": counts.tolist(),
            "no_history": len(values) * min(depth, values.shape[1]),
        }
    return census


def observe(options, forward, reverse_native, decision):
    reverse = reverse_native[:, ::-1]
    primary = "endpoints-1"
    bound = float(options["critic_bound"])
    threshold = (
        float(
            np.median(
                np.concatenate((forward[:, :, 0].ravel(), reverse[:, :, 0].ravel()))
            )
        )
        if decision is None
        else decision["threshold"]
    )
    rules, rows, labels = {}, {}, {}

    def score(name, a, b):
        if decision is None:
            rules[name] = fit_linear_critic(a, b, bound=bound)
        else:
            rules[name] = decision["critics"][name]
        fs, rs = (apply_linear_critic(x, rules[name]) for x in (a, b))
        # Two numerical views test the primary. Eight secondary records on
        # each clock share a separate simultaneous error budget.
        rows[name] = bounded_path_kl(
            fs, rs, bound=bound, alpha=0.025 if name == primary else 0.05 / 16
        )
        rows[name]["score_ranges"] = [
            [float(v.min()), float(v.max())] for v in (fs, rs)
        ]

    for stride in (1, 4, 16):
        a, b = forward[:, ::stride], reverse[:, ::stride]
        score("endpoints-" + str(stride), path_features(a), path_features(b))
        for trailing in (False, True):
            tag = ("trailing" if trailing else "instant") + "-" + str(stride)
            la, lb = (
                window_labels(v[:, :, 0], threshold, trailing=trailing) for v in (a, b)
            )
            if la.shape[1] == 0:
                labels[tag] = {
                    "status": "INSUFFICIENT_PADDING",
                    "observed_ticks": a.shape[1],
                }
                continue
            wrong = window_labels(
                reverse_native[:, ::stride, 0], threshold, trailing=trailing
            )[:, ::-1]
            labels[tag] = {
                "forward": history_contexts(la),
                "reverse": history_contexts(lb),
                "wrong_order_disagreements": int(np.count_nonzero(wrong != lb)),
                "scored": int(lb.size),
                "padding_each_end": 3,
            }
            score(tag, label_features(la), label_features(lb))
    return {"threshold": threshold, "critics": rules}, rows, labels
