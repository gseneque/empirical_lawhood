# SPDX-License-Identifier: MPL-2.0
"""Direct finite-horizon competing-event accounting without hazard fitting."""
from collections import defaultdict
import math

import numpy as np

def assess_first_passage(records, *, horizon, target_event="target", alpha=0.05, time_grid=None):
    """Bound commitment, all-cause survival and restricted first-exit mean.

Records require root_id, status, observed_until, event_time and event. Status
is event, administrative_censor, failed or truncated. Every assigned path is
retained; the last two statuses carry unresolved mass after observed_until.
Weights must have been fixed independently of outcomes. Paths sharing a root
remain one independent group, including for uncertainty.
"""
    if not math.isfinite(horizon) or horizon <= 0 or not target_event:
        raise ValueError("a positive physical horizon and target-event identity are required")
    if not math.isfinite(alpha) or not 0 < alpha < 1:
        raise ValueError("alpha must lie in (0,1)")
    times = tuple(float(t) for t in time_grid) if time_grid is not None else tuple(horizon*j/16 for j in range(17))
    if not times or len(set(times)) != len(times) or any(not math.isfinite(t) or not 0 <= t <= horizon for t in times):
        raise ValueError("survival grid must be a finite frozen menu inside the horizon")
    times = sorted(times)
    records = list(records)
    if not records:
        raise ValueError("the complete assigned event roster is required")
    rows = []
    root_weight = defaultdict(float)
    for original in records:
        r = dict(original)
        root_id = r.get("root_id")
        if not isinstance(root_id, str) or not root_id:
            raise ValueError("every assigned path must retain its independent-root identity")
        status = r.get("status")
        if status not in {"event", "administrative_censor", "failed", "truncated"}:
            raise ValueError("unknown first-passage outcome disposition")
        observed = float(r.get("observed_until", -1))
        weight = float(r.get("weight", 1))
        recrossings = r.get("recrossings")
        if recrossings is not None and (type(recrossings) is not int or recrossings < 0):
            raise ValueError("observed recrossing counts must be nonnegative integers")
        if not math.isfinite(observed) or not 0 <= observed <= horizon:
            raise ValueError("observed physical time lies outside the declared horizon")
        if not math.isfinite(weight) or weight <= 0:
            raise ValueError("assigned weights must be finite and positive")
        if status == "event":
            time = r.get("event_time")
            if time is None or not math.isfinite(float(time)) or not 0 <= float(time) <= observed or not r.get("event"):
                raise ValueError("a completed event requires its observed time and identity")
            time = float(time)
            commitment = float(r["event"] == target_event)
            cl, cu, tl, tu = commitment, commitment, time, time
        else:
            if r.get("event_time") is not None or r.get("event") is not None:
                raise ValueError("nonevent outcomes cannot contain a completed event")
            if status == "administrative_censor" and observed != horizon:
                raise ValueError("administrative censoring requires observation through the full horizon")
            time = None
            cl, cu = 0., 0. if observed == horizon else 1.
            tl, tu = observed, horizon
        rows.append({**r, "weight": weight, "observed_until": observed, "event_time": time,
                     "commitment_bounds": (cl, cu), "restricted_time_bounds": (tl, tu)})
        root_weight[root_id] += weight
    total = sum(root_weight.values())
    effective_root_weight_sq = sum((w/total)**2 for w in root_weight.values())
    # Commitment, restricted mean, and all survival time endpoints form one
    # family; both lower/upper completion bounds are included in the union.
    family = 2*(2+len(times))
    band = min(1., math.sqrt(math.log(2*family/alpha)*effective_root_weight_sq/2))
    commit = [sum(r["weight"]*r["commitment_bounds"][j] for r in rows)/total for j in (0, 1)]
    restricted = [sum(r["weight"]*r["restricted_time_bounds"][j] for r in rows)/total for j in (0, 1)]
    survival = []
    for t in times:
        lower = upper = 0.
        for r in rows:
            if r["event_time"] is not None:
                lo = hi = float(r["event_time"] > t)
            elif (0 < r["observed_until"] and t <= r["observed_until"]) or (r["status"] == "administrative_censor" and t <= horizon):
                lo = hi = 1.
            else:
                lo, hi = 0., 1.
            lower += r["weight"]*lo/total
            upper += r["weight"]*hi/total
        survival.append({"time": t, "completion_bounds": [lower, upper],
                         "confidence_bounds": [max(0, lower-band), min(1, upper+band)]})
    unknown = sum(r["weight"] for r in rows if r["status"] in {"failed", "truncated"} and r["observed_until"] < horizon)/total
    return {
        "status": "UNRESOLVED" if unknown else "ESTIMATED",
        "target_event": target_event, "horizon": float(horizon),
        "assigned_paths": len(rows), "independent_roots": len(root_weight),
        "assigned_weight": total, "unresolved_weight_fraction": unknown,
        "outcome_census": {s: sum(r["status"] == s for r in rows) for s in ("event", "administrative_censor", "failed", "truncated")},
        "commitment_bounds": commit,
        "commitment_confidence_bounds": [max(0, commit[0]-band), min(1, commit[1]+band)],
        "restricted_mean_bounds": restricted,
        "restricted_mean_confidence_bounds": [max(0, restricted[0]-horizon*band), min(horizon, restricted[1]+horizon*band)],
        "survival": survival, "alpha": alpha, "root_hoeffding_halfwidth": band,
        "observed_recrossing_mean": (sum(r["weight"]*r["recrossings"] for r in rows)/total
                                      if all(r.get("recrossings") is not None for r in rows) else None),
        "recrossing_covered_weight_fraction": sum(r["weight"] for r in rows if r.get("recrossings") is not None)/total,
        "recrossing_scope": "descriptive observed paths only; missing future crossings remain unknown",
        "uncertainty_meaning": "simultaneous weighted independent-root Hoeffding; arbitrary dependence within roots",
        "scope": "finite-horizon commitment and restricted all-cause first-exit mean; no constant hazard or infinite-horizon rate",
        "entry_history_census": {str(h): sum(r.get("entry_history", "unspecified") == h for r in rows)
                                  for h in sorted({r.get("entry_history", "unspecified") for r in rows}, key=str)},
    }


def assess_paired_first_passage(records, *, histories, assignments, horizon,
                               target_event="target", alpha=0.05, time_grid=None):
    """Second-minus-first history contrasts on a frozen paired path roster.

    ``assignments`` contains unique (root_id, replica, weight) records shared by
    both histories. Weights are assigned before outcomes. Omitted observations
    become wholly unknown paths, including missing/nonadmitted entries. Each
    root contributes one weighted paired outcome; replicas remain dependent.
    The two histories must use the same physical receiver, horizon and future
    randomization policy, as established by the domain's frozen declaration.
    """
    histories = tuple(histories)
    if len(histories) != 2 or len(set(histories)) != 2 or any(not isinstance(h, str) or not h for h in histories):
        raise ValueError("a contrast requires two distinct declared histories")
    if not math.isfinite(alpha) or not 0 < alpha < 1:
        raise ValueError("alpha must lie in (0,1)")
    roster, root_weights = {}, defaultdict(float)
    for row in assignments:
        root, replica, weight = row.get("root_id"), row.get("replica"), float(row.get("weight", 1))
        if not isinstance(root, str) or not root or type(replica) is not int or replica < 0:
            raise ValueError("each assigned path requires a root and nonnegative replica identity")
        if not math.isfinite(weight) or weight <= 0 or (root, replica) in roster:
            raise ValueError("assigned paired paths require unique identities and positive fixed weights")
        roster[(root, replica)] = weight
        root_weights[root] += weight
    if not roster:
        raise ValueError("a complete assigned paired path roster is required")
    indexed = {}
    for original in records:
        row = dict(original)
        key = (row.get("root_id"), row.get("replica"))
        history = row.get("entry_history")
        if key not in roster or history not in histories or (*key, history) in indexed:
            raise ValueError("paired observations contain an unknown or duplicate assigned path/history")
        if float(row.get("weight", 1)) != roster[key]:
            raise ValueError("paired observations changed an assigned path weight")
        indexed[(*key, history)] = row
    grouped = {(root, history): [] for root in root_weights for history in histories}
    missing = []
    for (root, replica), weight in roster.items():
        for history in histories:
            row = indexed.get((root, replica, history))
            if row is None:
                missing.append({"root_id": root, "replica": replica, "entry_history": history})
                row = dict(root_id=root, replica=replica, entry_history=history, weight=weight,
                           status="failed", observed_until=0., event_time=None, event=None,
                           reason="ASSIGNED_PAIRED_PATH_UNAVAILABLE")
            grouped[(root, history)].append(row)
    # Reuse the same exact event, censoring and failure semantics as marginals.
    root_assessments = {(root, history): assess_first_passage(rows, horizon=horizon,
        target_event=target_event, alpha=alpha, time_grid=time_grid)
        for (root, history), rows in grouped.items()}
    root_ids = sorted(root_weights)
    reference = root_assessments[(root_ids[0], histories[0])]
    times = [row["time"] for row in reference["survival"]]
    total_weight = sum(root_weights.values())
    weights = np.array([root_weights[root] / total_weight for root in root_ids])
    # Two completion endpoints for commitment, restricted mean and each time.
    family = 2 * (2 + len(times))
    unit_band = min(2., math.sqrt(2 * math.log(2 * family / alpha) * float(weights @ weights)))
    root_rows = []
    for root in root_ids:
        first, second = (root_assessments[(root, h)] for h in histories)
        root_rows.append({"root_id": root, "assigned_weight": root_weights[root],
            "first_commitment_bounds": first["commitment_bounds"],
            "second_commitment_bounds": second["commitment_bounds"],
            "first_restricted_mean_bounds": first["restricted_mean_bounds"],
            "second_restricted_mean_bounds": second["restricted_mean_bounds"],
            "first_survival_bounds": [r["completion_bounds"] for r in first["survival"]],
            "second_survival_bounds": [r["completion_bounds"] for r in second["survival"]]})

    def contrast(first, second, scale):
        first, second = np.asarray(first, dtype=float), np.asarray(second, dtype=float)
        paired = np.column_stack((second[:, 0] - first[:, 1], second[:, 1] - first[:, 0]))
        interval = weights @ paired
        observed = bool(np.all(first[:, 0] == first[:, 1]) and np.all(second[:, 0] == second[:, 1]))
        same_weights = bool(np.all(weights == weights[0]))
        covariance = variance = None
        if observed and same_weights and len(weights) >= 2:
            covariance = float(np.cov(first[:, 0], second[:, 0], ddof=1)[0, 1])
            variance = float(np.var(paired[:, 0], ddof=1) / len(weights))
        return {"status": "ESTIMATED" if observed else "UNRESOLVED",
            "completion_bounds": interval.tolist(),
            "confidence_bounds": [max(-scale, float(interval[0]) - scale * unit_band),
                                  min(scale, float(interval[1]) + scale * unit_band)],
            "root_contrast_bounds": paired.tolist(),
            "sample_root_cross_covariance": covariance,
            "sample_paired_mean_variance": variance,
            "sample_moment_scope": "descriptive complete equal-weight root pairs; uncertainty uses the bounded root inequality"}

    commitment = contrast([r["first_commitment_bounds"] for r in root_rows],
                          [r["second_commitment_bounds"] for r in root_rows], 1.)
    restricted = contrast([r["first_restricted_mean_bounds"] for r in root_rows],
                          [r["second_restricted_mean_bounds"] for r in root_rows], float(horizon))
    survival = [{"time": time, **contrast([r["first_survival_bounds"][j] for r in root_rows],
                  [r["second_survival_bounds"][j] for r in root_rows], 1.)} for j, time in enumerate(times)]
    return {"status": "UNRESOLVED" if any(r["status"] == "UNRESOLVED" for r in [commitment, restricted, *survival]) else "ESTIMATED",
        "contrast": "SECOND_MINUS_FIRST_HISTORY", "histories": list(histories),
        "target_event": target_event, "horizon": float(horizon),
        "estimand": "assigned-population paired history contrast; nonentry remains unresolved mass",
        "independent_roots": len(root_ids), "assigned_paired_paths": len(roster),
        "assigned_weight": total_weight, "missing_path_histories": missing,
        "root_pairs": root_rows, "commitment": commitment, "restricted_mean": restricted,
        "survival": survival, "alpha": alpha, "unit_root_hoeffding_halfwidth": unit_band,
        "uncertainty_meaning": "simultaneous weighted independent-root Hoeffding over both completion endpoints and the frozen time menu; arbitrary dependence within root and across histories"}
