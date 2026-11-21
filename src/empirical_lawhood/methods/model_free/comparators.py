# SPDX-License-Identifier: MPL-2.0
"""Opt-in comparators with explicit fitting and physical-inference limits.

None of these functions is a prerequisite of the direct M0--M7 suppliers.
Compression and observed reversal KL are descriptive diagnostics. The GLE
comparator fits a discrete linear prediction equation, not a unique physical
friction kernel. A nonlinear response identity needs its declared physical
initial-density and intervention premises.
"""
import math
import zlib

import numpy as np


def _symbols(sequence, alphabet_size):
    if type(alphabet_size) is not int or not 2 <= alphabet_size <= 2**32:
        raise ValueError("declare an alphabet of two through 2**32 uint32 symbols")
    x = np.asarray(sequence)
    if x.ndim != 1 or not len(x) or x.dtype.kind not in "iu" or np.any(x < 0) or np.any(x >= alphabet_size):
        raise ValueError("complete integer symbols in the declared alphabet are required")
    return x.astype("<u4")


def compression_diagnostic(sequence, *, alphabet_size, prefix_lengths, block_length=256,
                           shuffle_repetitions=16, seed=0):
    """Fixed-encoding compression compared with count-preserving shuffles.

Codec overhead, block boundaries, nonstationarity and observation conventions
remain part of this statistic; it is neither entropy nor a calibrated memory
test. Every prefix and block size must be selected before confirmation.
"""
    x = _symbols(sequence, alphabet_size)
    lengths = tuple(prefix_lengths)
    if not lengths or len(set(lengths)) != len(lengths) or any(type(n) is not int or not 1 <= n <= len(x) for n in lengths):
        raise ValueError("prefix lengths must be distinct positive integers within the record")
    if type(block_length) is not int or block_length < 1 or type(shuffle_repetitions) is not int or shuffle_repetitions < 1:
        raise ValueError("positive block length and shuffle repetitions are required")
    rng = np.random.default_rng(seed)
    def encoded_size(v):
        return sum(len(zlib.compress(v[start:start+block_length].tobytes(), level=9))
                   for start in range(0, len(v), block_length))
    rows = []
    for n in lengths:
        prefix = x[:n]
        actual = encoded_size(prefix)
        shuffled = [encoded_size(rng.permutation(prefix)) for _ in range(shuffle_repetitions)]
        rows.append({"prefix_length": n, "compressed_bytes": actual,
                     "bits_per_symbol_including_headers": 8*actual/n,
                     "shuffled_compressed_bytes": shuffled,
                     "shuffle_mean_minus_observed_bits_per_symbol": 8*(float(np.mean(shuffled))-actual)/n})
    return {"status": "DESCRIPTIVE", "codec": "zlib", "codec_version": zlib.ZLIB_RUNTIME_VERSION,
            "encoding": "little-endian uint32 symbols", "block_length": block_length, "prefixes": rows,
            "scope": "fixed observed encoding and prefix menu; no entropy, Markov or finite-sample confidence claim",
            "fit_required": False}


def fit_discrete_gle_comparator(training_roots, *, sample_interval, spring_constant,
                               history_order, mass=1.0, ridge=0.0):
    """Fit a declared Euler-discrete linear memory-force comparator.

The equation is m*dv/dt + k*q = -dt*sum_j Gamma[j]*v[t-j] + residual.
Orthogonality/FDT and exact discretization are not inferred from least squares.
Correlated residuals can bias interpretation of Gamma as physical friction.
"""
    if not isinstance(training_roots, dict) or not training_roots or any(not isinstance(k, str) or not k for k in training_roots):
        raise ValueError("explicit training-root identities are required")
    if type(history_order) is not int or history_order < 1:
        raise ValueError("declare a positive finite memory order")
    for value, allow_zero in ((sample_interval, False), (mass, False), (spring_constant, True), (ridge, True)):
        if not math.isfinite(value) or value < 0 or (not allow_zero and value == 0):
            raise ValueError("invalid timestep, mass, harmonic spring or regularization")
    features, outcomes, root_sizes = [], [], {}
    for identity, record in sorted(training_roots.items()):
        q, v = np.asarray(record["position"], dtype=float), np.asarray(record["velocity"], dtype=float)
        if q.ndim != 1 or q.shape != v.shape or len(q) <= history_order or not np.isfinite(q).all() or not np.isfinite(v).all():
            raise ValueError("complete aligned position/velocity records and sufficient history are required")
        root_sizes[identity] = len(q)-history_order
        for t in range(history_order-1, len(q)-1):
            features.append([sample_interval*v[t-j] for j in range(history_order)])
            outcomes.append(-(mass*(v[t+1]-v[t])/sample_interval+spring_constant*q[t]))
    x, y = np.asarray(features), np.asarray(outcomes)
    rank = int(np.linalg.matrix_rank(x))
    if rank < history_order:
        return {"status": "UNRESOLVED", "fit_required": True, "phase": "FIT",
                "reason": "training histories do not identify the declared linear coefficients",
                "training_root_ids": sorted(training_roots), "design_rank": rank, "history_order": history_order}
    if ridge:
        augmented_x = np.vstack((x, math.sqrt(ridge)*np.eye(history_order)))
        augmented_y = np.concatenate((y, np.zeros(history_order)))
    else:
        augmented_x, augmented_y = x, y
    coefficients = np.linalg.lstsq(augmented_x, augmented_y, rcond=None)[0]
    residual = y-x@coefficients
    return {"status": "FITTED", "phase": "FIT", "fit_required": True,
            "training_root_ids": sorted(training_roots), "training_root_rows": root_sizes,
            "history_order": history_order, "sample_interval": float(sample_interval),
            "spring_constant": float(spring_constant), "mass": float(mass), "ridge": float(ridge),
            "coefficients": coefficients.tolist(), "design_rank": rank,
            "training_residual_rms": float(np.sqrt(np.mean(residual**2))),
            "numerical_row_count": len(x), "independent_training_roots": len(training_roots),
            "physical_kernel_identified": False,
            "scope": "fitted discrete linear response comparator; no FDT, causal kernel, stability or coverage qualification"}


def assess_discrete_gle_comparator(model, *, root_id, position, velocity):
    """Assess the frozen fitted equation on an identifier-disjoint root."""
    if model.get("status") != "FITTED" or not root_id or root_id in model["training_root_ids"]:
        raise ValueError("a frozen fitted comparator and distinct assessment-root identity are required")
    q, v = np.asarray(position, dtype=float), np.asarray(velocity, dtype=float)
    order = model["history_order"]
    if q.ndim != 1 or q.shape != v.shape or len(q) <= order or not np.isfinite(q).all() or not np.isfinite(v).all():
        raise ValueError("complete aligned held-root state history is required")
    dt, mass, spring = model["sample_interval"], model["mass"], model["spring_constant"]
    gamma = np.asarray(model["coefficients"])
    predictions = np.array([v[t]-dt/mass*(spring*q[t]+dt*np.dot(gamma, [v[t-j] for j in range(order)]))
                            for t in range(order-1, len(v)-1)])
    observed = v[order:]
    return {"status": "ASSESSED", "root_id": root_id, "prediction": predictions.tolist(),
            "signed_error": (predictions-observed).tolist(), "mean_square_error": float(np.mean((predictions-observed)**2)),
            "independent_roots": 1, "calibration_performed": False,
            "scope": "identifier-disjoint exposed assessment; identifiers alone supply no freshness authority"}


def path_reversal_diagnostic(roots, *, alphabet_size, reversal_map, order,
                             sample_interval, clock="physical", maximum_cells=4096,
                             stationarity_qualified=False, reversal_qualified=False,
                             memory_order_qualified=False):
    """Observed finite-word KL under a declared involutive physical reversal.

Even fully supported observed KL is not automatically an entropy-production
bound. Missing reverse support is unresolved, never repaired with pseudocounts.
"""
    if clock != "physical" or not math.isfinite(sample_interval) or sample_interval <= 0:
        raise ValueError("physical reversal requires a qualified physical sampling clock")
    if not isinstance(roots, dict) or not roots or any(not key for key in roots):
        raise ValueError("declared independent roots are required")
    if type(order) is not int or order < 1 or type(maximum_cells) is not int or maximum_cells < 1:
        raise ValueError("positive finite word order and cell budget are required")
    if type(alphabet_size) is not int or alphabet_size < 2:
        raise ValueError("declare the physical observed-state alphabet")
    reversal = tuple(reversal_map)
    if len(reversal) != alphabet_size or set(reversal) != set(range(alphabet_size)) or any(reversal[reversal[i]] != i for i in range(alphabet_size)):
        raise ValueError("physical time reversal must be an explicit involution on observed states")
    if (order+1)*math.log(alphabet_size) > math.log(maximum_cells)+1e-12:
        return {"status": "UNRESOLVED", "reason": "declared reversal word exceeds cell budget", "order": order}
    size = alphabet_size**(order+1)
    laws = []
    for sequence in roots.values():
        x = _symbols(sequence, alphabet_size)
        if len(x) <= order:
            return {"status": "UNRESOLVED", "reason": "an assigned root has no complete word", "order": order}
        count = np.zeros(size)
        for start in range(len(x)-order):
            index = 0
            for value in x[start:start+order+1]:
                index = index*alphabet_size+int(value)
            count[index] += 1
        laws.append(count/count.sum())
    p = np.mean(laws, axis=0)
    reversed_indices = []
    for index in range(size):
        digits = []
        for _ in range(order+1):
            digits.append(index % alphabet_size)
            index //= alphabet_size
        mapped = 0
        for digit in digits:
            mapped = mapped*alphabet_size+reversal[digit]
        reversed_indices.append(mapped)
    reverse = p[reversed_indices]
    supported = p > 0
    missing = np.flatnonzero(supported & (reverse == 0)).tolist()
    kl = None if missing else float(np.sum(p[supported]*np.log(p[supported]/reverse[supported])))
    premises = {"stationarity": bool(stationarity_qualified), "physical_reversal": bool(reversal_qualified),
                "memory_order": bool(memory_order_qualified)}
    return {"status": "UNRESOLVED" if missing or not all(premises.values()) else "DESCRIPTIVE",
            "observed_path_kl": kl, "missing_reverse_words": missing, "order": order,
            "word_duration": order*sample_interval, "root_count": len(roots),
            "reversal_map": list(reversal), "premises": premises,
            "entropy_production_claim": False, "coverage_claim": False,
            "scope": "observed equal-root finite-word law; no thermodynamic rate or memory-order saturation inferred"}


def nonlinear_response_diagnostic(unperturbed, perturbed, log_density_ratios, *,
                                  root_ids, alpha=0.05, observable_bounds=None,
                                  log_weight_upper=None, density_identity_qualified=False,
                                  intervention_qualified=False):
    """Challenge an initial-density reweighting identity without self-normalizing.

Inputs have one row per independent root and arbitrary nested columns. The
physical question is E[A(Y)_perturbed] = E[A(Y)_baseline * p_shift(X0)/p(X0)].
The density ratio must be supplied by an exact/qualified physical reference;
estimating it introduces its own fitting and uncertainty obligations.
"""
    if not math.isfinite(alpha) or not 0 < alpha < 1:
        raise ValueError("alpha must lie in (0,1)")
    baseline, changed, logw = (np.asarray(x, dtype=float) for x in (unperturbed, perturbed, log_density_ratios))
    if baseline.ndim == 1:
        baseline, changed, logw = baseline[:, None], changed[:, None], logw[:, None]
    if baseline.ndim != 2 or changed.shape != baseline.shape or logw.shape != baseline.shape or not baseline.size:
        raise ValueError("aligned independent-root by nested-path observations are required")
    if len(root_ids) != len(baseline) or len(set(root_ids)) != len(root_ids) or any(not r for r in root_ids):
        raise ValueError("each independent root must have one distinct identity")
    if not all(np.isfinite(v).all() for v in (baseline, changed, logw)):
        raise ValueError("failed or incomplete observations cannot enter a finite response identity")
    if np.max(logw) > 700:
        return {"status": "UNRESOLVED", "reason": "weight overflow / heavy-tail acquisition boundary", "independent_roots": len(baseline)}
    weights = np.exp(logw)
    differences = (changed-baseline*weights).mean(axis=1)
    if not np.isfinite(differences).all():
        return {"status": "UNRESOLVED", "reason": "unbounded numerical weighted response", "independent_roots": len(baseline)}
    maximum = float(weights.max())
    scaled = np.exp(logw-float(logw.max()))
    result = {"status": "DESCRIPTIVE", "signed_difference": float(differences.mean()),
              "root_differences": differences.tolist(), "independent_roots": len(baseline),
              "maximum_weight": maximum, "mean_weight": float(weights.mean()),
              "descriptive_weight_ess": float(scaled.sum()**2/np.sum(scaled**2)),
              "self_normalized": False, "finite_sample_certificate": False,
              "scope": "qualified initial-density intervention identity; not an unconditional Markov test"}
    if observable_bounds is None or log_weight_upper is None:
        result["reason"] = "no declared bounded-weight/observable premise; sample variance is not a finite-variance proof"
        return result
    if len(observable_bounds) != 2 or not all(math.isfinite(v) for v in observable_bounds) or observable_bounds[1] < observable_bounds[0]:
        raise ValueError("finite ordered observable bounds are required")
    low, high = map(float, observable_bounds)
    if not math.isfinite(log_weight_upper) or not 0 <= log_weight_upper <= 700 or np.max(logw) > log_weight_upper:
        raise ValueError("observed density ratio violates declared finite bound")
    if np.any(baseline < low) or np.any(baseline > high) or np.any(changed < low) or np.any(changed > high):
        raise ValueError("observed receiver violates declared boundedness")
    bound = math.exp(log_weight_upper)
    width = (high-low)+max(0., high*bound)-min(0., low*bound)
    if not math.isfinite(width):
        result.update(status="UNRESOLVED", reason="weighted receiver bound exceeds numerical range")
        return result
    halfwidth = width*math.sqrt(math.log(2/alpha)/(2*len(baseline)))
    interval = [result["signed_difference"]-halfwidth, result["signed_difference"]+halfwidth]
    result.update(confidence_interval=interval, alpha=alpha,
                  uncertainty_meaning="independent-root bounded Hoeffding; nested paths do not increase root count")
    if density_identity_qualified and intervention_qualified:
        result["finite_sample_certificate"] = True
        result["status"] = "DISCREPANCY_DETECTED" if interval[0] > 0 or interval[1] < 0 else "UNRESOLVED"
    else:
        result["status"] = "UNRESOLVED"
        result["reason"] = "physical density/intervention premises unqualified"
    return result
