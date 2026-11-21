# SPDX-License-Identifier: MPL-2.0
"""Frozen, paired SSU-to-kinetics comparison across LSU backgrounds."""

from decimal import Decimal, localcontext

# Counts are for the side chain; backbone C/N/O are excluded.
_SIDE_C = dict(
    zip(
        "ACDEFGHIKLMNPQRSTVWY",
        (1, 1, 2, 3, 7, 0, 4, 4, 4, 4, 3, 2, 3, 3, 4, 1, 2, 3, 9, 7),
        strict=True,
    )
)
_SIDE_NO = dict(
    zip(
        "ACDEFGHIKLMNPQRSTVWY",
        (0, 0, 2, 2, 0, 0, 2, 0, 1, 0, 0, 2, 0, 2, 3, 1, 1, 0, 1, 1),
        strict=True,
    )
)
NAMES = (
    "side_chain_C_over_4",
    "side_chain_NO_over_3",
    "sulfur",
    "charge",
    "beta_branched",
)
ENDPOINTS = ("turnover", "specificity")


def descriptor(aa):
    if aa == "-":
        return (0.0,) * 5
    return (
        _SIDE_C[aa] / 4,
        _SIDE_NO[aa] / 3,
        float(aa in "CM"),
        float((aa in "KR") - (aa in "DE")),
        float(aa in "ITV"),
    )


def edits(parent, variant):
    """Map changed sequence positions using the pinned Levenshtein tie policy."""
    from rapidfuzz.distance import Levenshtein

    result = []
    for tag, i, j in Levenshtein.editops(parent, variant):
        old, new = (
            (parent[i] if tag != "insert" else "-"),
            (variant[j] if tag != "delete" else "-"),
        )
        result.append((None if tag == "insert" else i + 1, old, new))
    return result


def aligned_weights(parent, template, weights):
    from rapidfuzz.distance import Levenshtein

    result = {}
    for tag, a, b, c, d in Levenshtein.opcodes(parent, template):
        if tag in ("equal", "replace"):
            for i, j in zip(range(a, b), range(c, d)):
                if j + 1 in weights:
                    result[i + 1] = weights[j + 1]
    return result


def site_vector(parent, variant, weights):
    changes = []
    vector = [0.0] * 10
    for position, old, new in edits(parent, variant):
        weight = weights.get(position, 0.0)
        changes.append(
            {
                "position": position,
                "from": old,
                "to": new,
                "weight": weight,
                "mapped": position in weights,
            }
        )
        for k, (before, after) in enumerate(
            zip(descriptor(old), descriptor(new), strict=True)
        ):
            delta = after - before
            vector[k] += delta
            vector[5 + k] += weight * delta
    return vector, changes


def log_ratio(numerator, denominator):
    with localcontext() as ctx:
        ctx.prec = 50
        nums = [Decimal(x) for x in (numerator, denominator)]
        if not all(v.is_finite() and v > 0 for v in nums):
            raise ValueError("Paired kinetic means must be positive and finite")
        return (nums[0] / nums[1]).ln()


def fit_predict(training, tests):
    """Equal-weight, through-origin ridge; labels may occur only on training rows."""
    import numpy as np

    if not training or not tests or any("responses" in row for row in tests):
        raise ValueError("Separate training labels and label-free query rows")
    ids = [row["id"] for row in training + tests]
    if len(set(ids)) != len(ids):
        raise ValueError("Repeated case identity")
    backgrounds = {row["background"] for row in training}
    if backgrounds & {row["background"] for row in tests}:
        raise ValueError("A training LSU background entered the external queries")
    x = np.asarray([row["features"] for row in training], dtype=float)
    y = np.asarray(
        [
            [float(log_ratio(*r["responses"][label])) for label in ENDPOINTS]
            for r in training
        ]
    )
    xt = np.asarray([row["features"] for row in tests], dtype=float)
    if (
        x.shape != (len(training), 10)
        or xt.shape != (len(tests), 10)
        or not all(np.isfinite(a).all() for a in (x, y, xt))
    ):
        raise ValueError("Invalid SSU feature vectors or native responses")
    result = {row["id"]: {"zero": [0.0, 0.0]} for row in tests}
    coefficients = {}
    for name, width in (("sequence", 5), ("interface", 10)):
        design = x[:, :width]
        coef = np.linalg.solve(design.T @ design + np.eye(width), design.T @ y)
        coefficients[name] = coef.tolist()
        for row, pred in zip(tests, xt[:, :width] @ coef, strict=True):
            result[row["id"]][name] = pred.tolist()
    return coefficients, result


def score_forecasts(frozen, observations, margins):
    """Retain assigned missing and secondary outcomes and score only like quantities."""
    if set(observations) != set(frozen):
        raise ValueError(
            "The assigned external census differs from the frozen predictions"
        )
    result = {}
    for key, obs in observations.items():
        row = {}
        for method, predict in frozen[key].items():
            values = {}
            for ep, i in (("turnover", 0), ("specificity", 1), ("mass_activity", 0)):
                measure = obs.get(ep)
                if measure is None:
                    values[ep] = None
                    continue
                actual = float(log_ratio(measure["mutant"], measure["parent"]))
                signed = predict[i] - actual
                values[ep] = {
                    "native": measure,
                    "observed_log_ratio": actual,
                    "forecast_log_ratio": predict[i],
                    "signed_error": signed,
                    "absolute_error": abs(signed),
                    "within_donor_margin": abs(signed) <= margins[i],
                    "direction_matches": ((predict[i] > 0) - (predict[i] < 0))
                    == ((actual > 0) - (actual < 0)),
                }
            row[method] = values
        result[key] = {
            "methods": row,
            "reported_mass_activity": obs.get("mass_activity"),
            "role": obs["role"],
        }
    return result


def classify_joint_bounds(views):
    """Apply the scientific thresholds to qualified simultaneous log-ratio bounds."""
    if set(views) != {"M1", "V1"}:
        raise ValueError("Both processing views are required")
    status = {}
    for view, intervals in views.items():
        if intervals is None:
            status[view] = "UNRESOLVED"
            continue
        if set(intervals) != set(ENDPOINTS):
            raise ValueError("A qualified view must specify both endpoints")
        from math import isfinite

        for bounds in intervals.values():
            if bounds is None:
                continue
            low, high = bounds
            if not (isfinite(low) and isfinite(high) and low <= high):
                raise ValueError("Invalid simultaneous log-ratio bounds")
        t, s = intervals["turnover"], intervals["specificity"]
        if (t is not None and t[1] <= 0) or (s is not None and s[1] < 0):
            status[view] = "ADVERSE"
        elif t is not None and s is not None and t[0] > 0 and s[0] >= 0:
            status[view] = "SUPPORTED"
        else:
            status[view] = "UNRESOLVED"
    joint = (
        "ADVERSE"
        if "ADVERSE" in status.values()
        else ("SUPPORTED" if set(status.values()) == {"SUPPORTED"} else "UNRESOLVED")
    )
    return {"processing": status, "joint": joint}
