# SPDX-License-Identifier: MPL-2.0
"""Streaming lag laws and observational memory assessments.

CK agreement is compatibility at the tested resolution, never a Markov proof.
The independent observation for uncertainty is one complete root frequency
vector, regardless of its number of overlapping time origins.
"""
from collections import deque
import math

import numpy as np

from .uncertainty import allocate_alpha, conditional_bands, hoeffding_halfwidth, root_mean_bands


def memory_bound_feasibility(independent_roots, *, alphabet_size, history_order,
                             alpha=.05, comparison_groups=1, lag_count=1,
                             looks=1, max_cells=4096):
    """Necessary precision conditions for the actual finite-root memory bound.

The joint plus marginal family has k^(h+2)+k^(h+1)+k^2+k events. For all
k^(h+1) history/present denominators to have positive lower bounds, the common
Hoeffding halfwidth must be strictly below 1/k^(h+1), since the conditioning
probabilities sum to one. Failing this necessary condition makes the current
all-cell equivalence rule impossible even for exact Markov data. Passing it
does not establish support, a task-error bound, statistical power or adequacy.
"""
    for name, value, minimum in (("independent roots", independent_roots, 1),
            ("alphabet", alphabet_size, 2), ("history order", history_order, 1),
            ("comparison groups", comparison_groups, 1), ("lag count", lag_count, 1),
            ("looks", looks, 1), ("cell budget", max_cells, 1)):
        if type(value) is not int or value < minimum:
            raise ValueError(name + " must be an integer in its positive domain")
    per_lag_alpha = allocate_alpha(alpha, comparisons=comparison_groups*lag_count, looks=looks)
    common = {"independent_roots": independent_roots, "alphabet_size": alphabet_size,
        "history_order": history_order, "family_alpha": float(alpha),
        "comparison_groups": comparison_groups, "lag_count": lag_count,
        "record_length_looks": looks, "per_lag_alpha": per_lag_alpha,
        "power_established": False,
        "meaning": "necessary feasibility of the declared all-cell finite-root bound, not sufficient precision or a power guarantee"}
    if (history_order+2)*math.log(alphabet_size) > math.log(max_cells)+1e-12:
        return {**common, "status": "IMPOSSIBLE_UNDER_DECLARED_ALPHABET_BUDGET",
            "all_conditioning_lower_bounds_can_be_positive": False,
            "maximum_joint_cells": max_cells}
    joint_cells = alphabet_size**(history_order+2)
    conditioning_cells = alphabet_size**(history_order+1)
    events = joint_cells+conditioning_cells+alphabet_size**2+alphabet_size
    halfwidth = hoeffding_halfwidth(independent_roots, events, per_lag_alpha)
    threshold = 1/conditioning_cells
    necessary_n = math.floor(conditioning_cells**2 * math.log(2*events/per_lag_alpha)/2)+1
    possible = halfwidth < threshold
    return {**common, "status": "NECESSARY_CONDITION_PASSED" if possible else "IMPOSSIBLE_POSITIVE_CONDITIONING_BOUNDS",
        "joint_cells": joint_cells, "conditioning_cells": conditioning_cells,
        "joint_and_marginal_event_count": events, "root_probability_halfwidth": halfwidth,
        "largest_possible_minimum_conditioning_probability": threshold,
        "all_conditioning_lower_bounds_can_be_positive": possible,
        "necessary_independent_roots_for_positive_conditioning_bounds": necessary_n}


def root_lag_counts(sequence, lags, *, alphabet_size, history_order=1,
                    max_cells=4096, root_id="", record_scope="finite_record_root_average",
                    anchor_indices=None):
    """Count (older history, present, future) with bounded rolling storage.

For lag L, future is at t, present at t-L, and the older-history word is
at t-(h+1)L,...,t-2L. Missing symbol -1 invalidates the whole anchor while
retaining its denominator. Chunk boundaries are immaterial: pass one iterable.
"""
    lags = tuple(lags)
    if not lags or any(type(k) is not int or k < 1 for k in lags) or len(set(lags)) != len(lags):
        raise ValueError("lags must be distinct positive integer sample offsets")
    if type(alphabet_size) is not int or alphabet_size < 2:
        raise ValueError("alphabet must contain at least two symbols")
    if type(history_order) is not int or history_order < 1:
        raise ValueError("older-history order must be positive")
    if type(max_cells) is not int or max_cells < 1:
        raise ValueError("a positive joint-cell budget is required")
    if record_scope not in {"finite_record_root_average", "stationary", "protocol_age"}:
        raise ValueError("unknown root probability law")
    anchors = None if anchor_indices is None else tuple(anchor_indices)
    if anchors is not None and (not anchors or len(set(anchors)) != len(anchors)
            or any(type(t) is not int or t < 0 for t in anchors)):
        raise ValueError("anchor sample indices must be distinct nonnegative integers")
    if record_scope == "protocol_age" and (anchors is None or len(anchors) != 1):
        raise ValueError("protocol-age law requires one explicit frozen future-anchor age")
    selected = None if anchors is None else frozenset(anchors)
    # Bound exponentiation as well as allocation for malformed large orders.
    if (history_order + 2) * math.log(alphabet_size) > math.log(max_cells) + 1e-12:
        return {"status": "UNRESOLVED", "reason": "declared history alphabet exceeds joint-cell budget",
                "root_id": str(root_id), "record_scope": record_scope,
                "alphabet_size": alphabet_size, "history_order": history_order,
                "max_cells": max_cells, "lags": {}}
    k = alphabet_size
    shape = (k**history_order, k, k)
    arrays = {lag: np.zeros(shape, dtype=np.int64) for lag in lags}
    attempted = {lag: 0 for lag in lags}
    missing = {lag: 0 for lag in lags}
    buffer = deque(maxlen=(history_order+1)*max(lags)+1)
    length = 0
    for raw in sequence:
        if isinstance(raw, (bool, np.bool_)) or not isinstance(raw, (int, np.integer)):
            raise TypeError("symbols must be integer alphabet codes or -1")
        symbol = int(raw)
        if symbol < -1 or symbol >= k:
            raise ValueError("symbol outside declared alphabet")
        buffer.append(symbol)
        length += 1
        if selected is not None and length-1 not in selected:
            continue
        for lag in lags:
            if len(buffer) <= (history_order+1)*lag:
                continue
            attempted[lag] += 1
            digits = [buffer[-1-i*lag] for i in range(history_order+1, -1, -1)]
            if -1 in digits:
                missing[lag] += 1
                continue
            history = 0
            for digit in digits[:-2]:
                history = history*k + digit
            arrays[lag][history, digits[-2], digits[-1]] += 1
    return {
        "status": "COUNTED", "root_id": str(root_id), "record_scope": record_scope,
        "alphabet_size": k, "history_order": history_order, "record_length": length,
        "anchor_indices": None if anchors is None else list(anchors),
        "joint_cells_per_lag": math.prod(shape),
        "maximum_retained_samples": buffer.maxlen,
        "lags": {str(lag): {"joint_counts": arrays[lag].tolist(),
                    "attempted_anchors": attempted[lag],
                    "observed_anchors": int(arrays[lag].sum()),
                    "missing_anchors": missing[lag]} for lag in lags},
    }


def root_segment_counts(sequence, boundaries, *, lags, alphabet_size, root_id,
                        sample_interval=1., max_cells=4096):
    """One-pass occupancy and within-segment two-time transition census.

Boundaries are sample indices, with the final boundary exclusive. A lag pair
is retained only when both endpoints belong to the same segment. All globally
available pairs excluded by a boundary have their own census. Missing endpoint
symbols retain the attempted denominator; no trajectory is concatenated with
another root. Transition missingness concerns endpoints, not intermediate times.
"""
    edges, lags = tuple(boundaries), tuple(lags)
    if len(edges) < 3 or any(type(v) is not int for v in edges) or edges[0] != 0 or any(b <= a for a, b in zip(edges, edges[1:])):
        raise ValueError("segment boundaries must partition the complete record into nonempty segments")
    if not lags or len(set(lags)) != len(lags) or any(type(v) is not int or v < 1 for v in lags):
        raise ValueError("segment lags must be distinct positive sample offsets")
    if type(alphabet_size) is not int or alphabet_size < 2 or type(max_cells) is not int or max_cells < 1:
        raise ValueError("a finite alphabet and cell budget are required")
    if not math.isfinite(sample_interval) or sample_interval <= 0 or not str(root_id):
        raise ValueError("positive physical interval and independent-root identity required")
    common = {"root_id": str(root_id), "boundaries_samples": list(edges),
        "alphabet_size": alphabet_size, "sample_interval": float(sample_interval),
        "transition_policy": "within_segment", "boundary_convention": "left_closed_right_open",
        "scope": "equal-root finite-record occupancy and transition frequencies; no stationarity qualification"}
    if alphabet_size**2 > max_cells:
        return {**common, "status": "UNRESOLVED", "reason": "transition alphabet exceeds joint-cell budget", "segments": []}
    segments = []
    for index, (start, stop) in enumerate(zip(edges, edges[1:])):
        segments.append({"segment": index, "start_sample": start, "stop_sample_exclusive": stop,
            "first_sample_time": start*sample_interval, "last_sample_time": (stop-1)*sample_interval,
            "sample_count": stop-start, "observed_samples": 0, "missing_samples": 0,
            "occupancy_counts": np.zeros(alphabet_size, dtype=np.int64),
            "transitions": {str(lag): {"joint_counts": np.zeros((alphabet_size, alphabet_size), dtype=np.int64),
                "attempted_pairs": 0, "observed_pairs": 0, "missing_pairs": 0,
                "boundary_crossing_pairs_excluded": 0} for lag in lags}})
    buffer, segment_index, length = deque(maxlen=max(lags)+1), 0, 0
    for index, raw in enumerate(sequence):
        if index >= edges[-1]:
            raise ValueError("record exceeds its frozen segment boundaries")
        if isinstance(raw, (bool, np.bool_)) or not isinstance(raw, (int, np.integer)):
            raise TypeError("symbols must be integer alphabet codes or -1")
        symbol = int(raw)
        if not -1 <= symbol < alphabet_size:
            raise ValueError("symbol outside declared alphabet")
        while index >= edges[segment_index+1]:
            segment_index += 1
        segment = segments[segment_index]
        if symbol < 0:
            segment["missing_samples"] += 1
        else:
            segment["observed_samples"] += 1
            segment["occupancy_counts"][symbol] += 1
        buffer.append(symbol)
        length += 1
        for lag in lags:
            if index < lag:
                continue
            row = segment["transitions"][str(lag)]
            if index-lag < segment["start_sample"]:
                row["boundary_crossing_pairs_excluded"] += 1
                continue
            row["attempted_pairs"] += 1
            older = buffer[-1-lag]
            if symbol < 0 or older < 0:
                row["missing_pairs"] += 1
            else:
                row["joint_counts"][older, symbol] += 1
                row["observed_pairs"] += 1
    if length != edges[-1]:
        raise ValueError("record is shorter than its frozen segment boundaries")
    for segment in segments:
        segment["occupancy_counts"] = segment["occupancy_counts"].tolist()
        for row in segment["transitions"].values():
            counts = row["joint_counts"]
            support = counts.sum(axis=1)
            row["conditional_transition_probabilities"] = [
                (counts[i]/support[i]).tolist() if support[i] else None for i in range(alphabet_size)]
            row["origin_support"] = support.tolist()
            row["joint_counts"] = counts.tolist()
    return {**common, "status": "COUNTED", "record_length": length,
            "maximum_retained_samples": buffer.maxlen, "segments": segments}


def _paired_segment_contrast(first, second, *, alpha, root_ids, missing):
    """Paired bounded-root difference; missing pairs are never dropped."""
    if missing:
        return {"status": "UNRESOLVED", "reason": "incomplete or unsupported assigned-root pair",
                "independent_roots": len(root_ids), "unresolved_root_ids": missing}
    a, b = np.asarray(first, dtype=float), np.asarray(second, dtype=float)
    differences = b-a
    bands = root_mean_bands((differences+1)/2, alpha=alpha, simplex=False)
    n = len(root_ids)
    variance = np.var(differences, axis=0, ddof=1)/n if n > 1 else None
    covariance = np.sum((a-a.mean(axis=0))*(b-b.mean(axis=0)), axis=0)/(n-1) if n > 1 else None
    return {"status": "ASSESSED", "mean_difference": (2*np.asarray(bands["mean"])-1).tolist(),
        "lower": (2*np.asarray(bands["lower"])-1).tolist(),
        "upper": (2*np.asarray(bands["upper"])-1).tolist(),
        "halfwidth": 2*bands["halfwidth"], "alpha": alpha, "independent_roots": n,
        "root_differences": differences.tolist(), "root_ids": root_ids,
        "estimated_mean_variance": None if variance is None else variance.tolist(),
        "paired_segment_covariance_per_coordinate": None if covariance is None else covariance.tolist(),
        "variance_meaning": "descriptive paired-root sample variance divided by root count; paired segment covariance retained per event coordinate",
        "meaning": "simultaneous independent-root Hoeffding; second segment minus first; finite-record target only"}


def assess_root_segments(root_counts, *, alpha=.05):
    """Paired occupancy and transition changes for the complete root roster.

The target is the mean paired change in finite-record root frequencies.
Row-conditional transition changes use each root's own origin denominator;
every assigned root must support that row. Root and segment lengths remain
explicit. Stable diagnostics do not establish stationarity or mixing.
"""
    roots = list(root_counts)
    if not roots:
        raise ValueError("complete assigned-root segment roster required")
    identities = [root.get("root_id", "") for root in roots]
    if any(not identity for identity in identities) or len(set(identities)) != len(identities):
        raise ValueError("one distinct independent-root identity is required")
    missing = [identity for identity, root in zip(identities, roots) if root.get("status") != "COUNTED"]
    if missing:
        return {"status": "UNRESOLVED", "independent_roots": len(roots),
                "unresolved_root_ids": missing, "reason": "assigned segment record unavailable"}
    common_keys = ("boundaries_samples", "alphabet_size", "sample_interval", "transition_policy")
    if any(any(root[key] != roots[0][key] for key in common_keys) for root in roots):
        raise ValueError("root segment, alphabet and clock declarations must match")
    segments, k = len(roots[0]["segments"]), roots[0]["alphabet_size"]
    lags = tuple(roots[0]["segments"][0]["transitions"])
    if any(len(root["segments"]) != segments or any(set(row["transitions"]) != set(lags) for row in root["segments"]) for root in roots):
        raise ValueError("root segment and transition census must match")
    edges = roots[0]["boundaries_samples"]
    if len(edges) != segments+1 or edges[0] != 0 or any(type(edge) is not int for edge in edges) or any(b <= a for a, b in zip(edges, edges[1:])):
        raise ValueError("invalid complete segment partition")
    for root in roots:
        if root["record_length"] != edges[-1]:
            raise ValueError("segment record length differs from its complete partition")
        for index, segment in enumerate(root["segments"]):
            start, stop = edges[index:index+2]
            n = stop-start
            occupancy = np.asarray(segment["occupancy_counts"])
            if (segment["segment"] != index or segment["start_sample"] != start or segment["stop_sample_exclusive"] != stop
                    or segment["sample_count"] != n or occupancy.shape != (k,) or occupancy.dtype.kind not in "iu"
                    or np.any(occupancy < 0) or segment["observed_samples"] != int(occupancy.sum())
                    or segment["missing_samples"] < 0 or int(occupancy.sum())+segment["missing_samples"] != n):
                raise ValueError("segment occupancy does not conserve its complete sample denominator")
            for lag, row in segment["transitions"].items():
                offset, counts = int(lag), np.asarray(row["joint_counts"])
                excluded = max(0, min(stop, start+offset)-max(start, offset))
                if (offset < 1 or counts.shape != (k, k) or counts.dtype.kind not in "iu" or np.any(counts < 0)
                        or row["attempted_pairs"] != max(0, n-offset) or row["missing_pairs"] < 0
                        or row["observed_pairs"] != int(counts.sum())
                        or int(counts.sum())+row["missing_pairs"] != row["attempted_pairs"]
                        or row["boundary_crossing_pairs_excluded"] != excluded
                        or row["origin_support"] != counts.sum(axis=1).tolist()):
                    raise ValueError("segment transitions do not conserve their complete within-segment denominator")
                expected = [(counts[i]/counts[i].sum()).tolist() if counts[i].sum() else None for i in range(k)]
                if row["conditional_transition_probabilities"] != expected:
                    raise ValueError("conditional transition probabilities differ from their measured support")
    comparisons = segments*(segments-1)//2
    families = comparisons*(1+len(lags)*(1+k))
    per_family_alpha = allocate_alpha(alpha, comparisons=families)
    outputs = []
    for first in range(segments):
        for second in range(first+1, segments):
            pairs = [(root["segments"][first], root["segments"][second]) for root in roots]
            unavailable = [identity for identity, pair in zip(identities, pairs) if any(row["missing_samples"] for row in pair)]
            occupancy = _paired_segment_contrast(
                [np.asarray(a["occupancy_counts"])/a["sample_count"] for a, _ in pairs],
                [np.asarray(b["occupancy_counts"])/b["sample_count"] for _, b in pairs],
                alpha=per_family_alpha, root_ids=identities, missing=unavailable)
            transitions = {}
            for lag in lags:
                rows = [(a["transitions"][lag], b["transitions"][lag]) for a, b in pairs]
                unavailable = [identity for identity, pair in zip(identities, rows)
                    if any(row["attempted_pairs"] == 0 or row["missing_pairs"] for row in pair)]
                joint = _paired_segment_contrast(
                    [(np.asarray(a["joint_counts"])/max(1, a["attempted_pairs"])).reshape(-1) for a, _ in rows],
                    [(np.asarray(b["joint_counts"])/max(1, b["attempted_pairs"])).reshape(-1) for _, b in rows],
                    alpha=per_family_alpha, root_ids=identities, missing=unavailable)
                conditional = []
                for origin in range(k):
                    no_support = [identity for identity, pair in zip(identities, rows)
                        if any(not row["origin_support"][origin] or row["missing_pairs"] for row in pair)]
                    contrast = _paired_segment_contrast(
                        [a["conditional_transition_probabilities"][origin] or [0.]*k for a, _ in rows],
                        [b["conditional_transition_probabilities"][origin] or [0.]*k for _, b in rows],
                        alpha=per_family_alpha, root_ids=identities, missing=no_support)
                    conditional.append({"origin": origin, **contrast})
                transitions[lag] = {"joint_frequency": joint, "row_conditional": conditional}
            outputs.append({"first_segment": first, "second_segment": second,
                            "occupancy": occupancy, "transitions": transitions})
    return {"status": "ASSESSED", "independent_roots": len(roots), "root_ids": identities,
        **{key: roots[0][key] for key in common_keys}, "alpha": alpha,
        "comparison_families": families, "comparisons": outputs, "stationarity_established": False,
        "scope": "paired changes of finite-record occupancy, transition-joint and supported row-conditional frequencies"}


def _joint(values):
    p = np.asarray(values, dtype=float)
    if p.ndim != 3 or any(n < 1 for n in p.shape) or p.shape[1] != p.shape[2]:
        raise ValueError("expected older-history by present by future joint law")
    if not np.all(np.isfinite(p)) or np.any(p < 0) or p.sum() <= 0:
        raise ValueError("joint law must have finite nonnegative nonzero mass")
    return p/p.sum()


def _kl(p, q):
    mask = p > 0
    if np.any(q[mask] <= 0):
        return None  # JSON-safe infinity, with an explicit flag at the caller.
    return max(0.0, float(np.sum(p[mask]*np.log(p[mask]/q[mask]))))


def memory_diagnostics(joint_counts):
    """Descriptive plug-in discrepancies, with no uncertainty qualification.

All marginals come from the same anchor law. A stationary CK interpretation
requires the domain's separate stationarity contract.
"""
    p = _joint(joint_counts)
    phz, pzy = p.sum(axis=2), p.sum(axis=0)
    pz = pzy.sum(axis=1)
    q = np.divide(pzy, pz[:, None], out=np.zeros_like(pzy), where=pz[:, None] > 0)
    conditional = np.divide(p, phz[:, :, None], out=np.zeros_like(p), where=phz[:, :, None] > 0)
    tv = .5*np.abs(conditional-q[None, :, :]).sum(axis=2)
    supported = phz > 0
    markov_joint = phz[:, :, None]*q[None, :, :]
    cmi = _kl(p, markov_joint)
    result = {
        "status": "DESCRIPTIVE", "conditional_mutual_information": cmi,
        "history_tv": [[float(tv[h, z]) if supported[h, z] else None for z in range(p.shape[1])]
                       for h in range(p.shape[0])],
        "weighted_history_tv": float(np.sum(phz*tv)),
        "maximum_supported_history_tv": float(np.max(tv[supported])),
        "supported_history_cells": supported.tolist(),
        "meaning": "plug-in observed-law discrepancy; no confidence bound or Markov certification",
    }
    if p.shape[0] != p.shape[1]:
        result["ck"] = {"status": "NOT_APPLICABLE", "reason": "CK comparison requires a single older observation"}
        return result
    pa = phz.sum(axis=1)
    direct = np.divide(p.sum(axis=1), pa[:, None], out=np.zeros_like(p.sum(axis=1)), where=pa[:, None] > 0)
    first = np.divide(phz, pa[:, None], out=np.zeros_like(phz), where=pa[:, None] > 0)
    reconstructed = first@q
    row_tv = .5*np.abs(direct-reconstructed).sum(axis=1)
    kl = [_kl(direct[i], reconstructed[i]) if pa[i] > 0 else None for i in range(len(pa))]
    infinite = any(kl[i] is None for i in range(len(pa)) if pa[i] > 0)
    js = []
    for a, b in zip(direct, reconstructed):
        mid = (a+b)/2
        js.append(.5*(_kl(a, mid) or 0)+.5*(_kl(b, mid) or 0))
    result["ck"] = {
        "status": "DESCRIPTIVE", "direct": direct.tolist(), "composed": reconstructed.tolist(),
        "residual": (direct-reconstructed).tolist(),
        "row_tv": [float(row_tv[i]) if pa[i] > 0 else None for i in range(len(pa))],
        "weighted_tv": float(pa@row_tv), "maximum_supported_row_tv": float(row_tv[pa > 0].max()),
        "row_kl": kl, "weighted_kl": None if infinite else sum(float(pa[i])*kl[i] for i in range(len(pa)) if pa[i] > 0),
        "infinite_kl": infinite, "weighted_js": float(pa@np.asarray(js)),
        "scope": "three-time anchor law; stationary semigroup interpretation requires a qualified stationary record",
    }
    return result


def assess_root_memory(root_counts, *, alpha=0.05, minimum_support=2,
                       receiver_oscillation=1.0, tolerance=0.1,
                       binning_allowance=0.0, tail_allowance=0.0,
                       look_index=0, looks=1, minimum_tv_effect=0.0):
    """Simultaneous history/receiver bounds from independent root laws.

No time-origin iid assumption is used. Missing anchors or absent roots leave
the relevant requested target unresolved rather than selecting complete cases.
"""
    roots = list(root_counts)
    if not roots:
        raise ValueError("the complete assigned-root roster is required")
    if type(minimum_support) is not int or minimum_support < 1:
        raise ValueError("minimum support counts independent roots")
    for value in (receiver_oscillation, tolerance, binning_allowance, tail_allowance, minimum_tv_effect):
        if not math.isfinite(value) or value < 0:
            raise ValueError("receiver allowances must be finite and nonnegative")
    identities = [r.get("root_id", "") for r in roots]
    if any(not r for r in identities) or len(set(identities)) != len(identities):
        raise ValueError("each independently assigned root needs one distinct identity")
    if any(r.get("status") != "COUNTED" for r in roots):
        return {"status": "UNRESOLVED", "reason": "an assigned root could not count the declared alphabet", "independent_roots": len(roots), "lags": {}}
    keys = ("record_scope", "alphabet_size", "history_order", "anchor_indices")
    if any(any(r[key] != roots[0][key] for key in keys) or set(r["lags"]) != set(roots[0]["lags"]) for r in roots):
        raise ValueError("root observation/history/lag laws must match")
    result = {"status": "ASSESSED", "independent_roots": len(roots),
              "record_scope": roots[0]["record_scope"], "alpha": alpha,
              "look_index": look_index, "looks": looks, "lags": {},
              "scope": "observational task equivalence only; no intervention or unrestricted Markov claim"}
    per_lag_alpha = allocate_alpha(alpha, comparisons=len(roots[0]["lags"]), look_index=look_index, looks=looks)
    for lag in sorted(roots[0]["lags"], key=int):
        entries = [r["lags"][lag] for r in roots]
        totals = [e["attempted_anchors"] for e in entries]
        if any(t < 1 or e["missing_anchors"] != 0 for t, e in zip(totals, entries)):
            result["lags"][lag] = {"status": "UNRESOLVED", "reason": "empty or incomplete assigned-root anchor law",
                "attempted_anchors": totals, "missing_anchors": [e["missing_anchors"] for e in entries]}
            continue
        arrays = [np.asarray(e["joint_counts"], dtype=float) for e in entries]
        for a, t, e in zip(arrays, totals, entries):
            if np.any(a < 0) or not np.all(np.isfinite(a)) or a.sum() != t or e["observed_anchors"] != t:
                raise ValueError("root joint counts do not conserve the complete anchor denominator")
        shape = arrays[0].shape
        if any(a.shape != shape for a in arrays):
            raise ValueError("root joint alphabet shapes differ")
        laws = np.asarray([a/t for a, t in zip(arrays, totals)])
        # Direct marginal events yield useful denominator bounds even when
        # every rare joint-cell lower bound is zero. They join the SAME union
        # family; no free marginal estimates or iid time origins are assumed.
        joint_size = math.prod(shape)
        hz_shape, zy_shape = shape[:2], shape[1:]
        hz_size, zy_size = math.prod(hz_shape), math.prod(zy_shape)
        events = np.concatenate((laws.reshape(len(roots), -1),
            laws.sum(axis=3).reshape(len(roots), -1),
            laws.sum(axis=1).reshape(len(roots), -1),
            laws.sum(axis=(1, 3))), axis=1)
        bands = root_mean_bands(events, alpha=per_lag_alpha, simplex=False)
        mean = np.asarray(bands["mean"][:joint_size]).reshape(shape)
        lo = np.asarray(bands["lower"][:joint_size]).reshape(shape)
        hi = np.asarray(bands["upper"][:joint_size]).reshape(shape)
        hz_lo = np.asarray(bands["lower"][joint_size:joint_size+hz_size]).reshape(hz_shape)
        hz_hi = np.asarray(bands["upper"][joint_size:joint_size+hz_size]).reshape(hz_shape)
        zy_start = joint_size+hz_size
        zy_lo = np.asarray(bands["lower"][zy_start:zy_start+zy_size]).reshape(zy_shape)
        zy_hi = np.asarray(bands["upper"][zy_start:zy_start+zy_size]).reshape(zy_shape)
        z_lo, z_hi = np.asarray(bands["lower"][zy_start+zy_size:]), np.asarray(bands["upper"][zy_start+zy_size:])
        cells = []
        for h in range(shape[0]):
            for z in range(shape[1]):
                support = int(sum(a[h, z].sum() > 0 for a in arrays))
                row = {"history": h, "present": z, "support_roots": support,
                       "conditioning_probability_lower": float(max(lo[h, z].sum(), hz_lo[h, z]))}
                first = conditional_bands(lo[h, z], hi[h, z], denominator_bounds=(hz_lo[h, z], hz_hi[h, z]))
                second = conditional_bands(zy_lo[z], zy_hi[z], denominator_bounds=(z_lo[z], z_hi[z]))
                if support < minimum_support or first is None or second is None:
                    row.update(status="UNRESOLVED", reason="conditioning event lacks root support or a positive denominator bound")
                else:
                    a, b = first
                    c, d = second
                    tv_lo = float(.5*np.maximum(0, np.maximum(a-d, c-b)).sum())
                    tv_hi = min(1., float(.5*np.maximum(np.abs(a-d), np.abs(b-c)).sum()))
                    allowance = binning_allowance+tail_allowance
                    task_hi = receiver_oscillation*tv_hi+allowance
                    # A lower TV does not imply an effect for an arbitrary f;
                    # it witnesses distributional dependence only.
                    row.update(tv_lower=tv_lo, tv_upper=tv_hi, receiver_error_upper=task_hi,
                               distributional_dependence_detected=tv_lo > minimum_tv_effect,
                               task_equivalent=task_hi <= tolerance,
                               status="EQUIVALENT" if task_hi <= tolerance else "DETECTED" if tv_lo > minimum_tv_effect else "UNRESOLVED",
                               meaning="simultaneous finite-root bound")
                cells.append(row)
        result["lags"][lag] = {
            "status": "EQUIVALENT" if cells and all(c["status"] == "EQUIVALENT" for c in cells) else
                      "DETECTED" if any(c["status"] == "DETECTED" for c in cells) else "UNRESOLVED",
            "distributional_dependence_detected": any(c.get("distributional_dependence_detected", False) for c in cells),
            "task_equivalent": bool(cells) and all(c.get("task_equivalent", False) for c in cells),
            "cells": cells, "point": memory_diagnostics(mean),
            "root_band_halfwidth": bands["halfwidth"], "alpha": per_lag_alpha,
            "joint_and_marginal_event_count": bands["event_count"],
            "attempted_anchors": totals,
        }
    lag_order = sorted(result["lags"], key=int)
    result["duration"] = {
        "detected_lags": [int(lag) for lag in lag_order if result["lags"][lag].get("distributional_dependence_detected", False)],
        "equivalent_lags": [int(lag) for lag in lag_order if result["lags"][lag].get("task_equivalent", False)],
        "unresolved_lags": [int(lag) for lag in lag_order if result["lags"][lag]["status"] == "UNRESOLVED"],
        "extent": "RIGHT_CENSORED" if lag_order and result["lags"][lag_order[-1]].get("distributional_dependence_detected", False) else "UNRESOLVED",
        "meaning": "tested lag menu only; distributional memory and task equivalence may coexist; no fitted cutoff or inference from nonsignificance",
    }
    return result
