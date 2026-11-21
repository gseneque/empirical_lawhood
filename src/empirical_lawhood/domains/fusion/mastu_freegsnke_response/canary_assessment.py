"""Reusable scientific contracts and calculations; native effects are owned by the adapter."""

from __future__ import annotations
import math
from typing import Any
import numpy as np


from typing import Final


SCHEMA: Final = 'empirical-lawhood/physical/mastu-freegsnke-response/canary-evaluation'


DT_S: Final = 0.0005


HORIZONS_S: Final = (0.005, 0.010, 0.015)


FRACTIONS: Final = (0.0625, 0.125, 0.25)


VIEWS: Final = (65, 129)


CURRENT_LIMITS_A: Final = {
    "px": (-5000.0, 5000.0),
    "d1": (-9000.0, 9000.0),
    "d2": (-9000.0, 9000.0),
    "d3": (-7000.0, 7000.0),
    "dp": (-7000.0, 7000.0),
    "d5": (-5000.0, 5000.0),
    "d6": (-4000.0, 4000.0),
    "d7": (-5000.0, 5000.0),
    "p4": (-10000.0, 0.0),
    "p5": (-10000.0, 0.0),
}



def action_roster(full_increment_v: float) -> tuple[tuple[str, float], ...]:
    if not math.isfinite(full_increment_v) or full_increment_v <= 0:
        raise ValueError("Admission voltage limit must be positive and finite")
    values = [("hold", 0.0)]
    for fraction in FRACTIONS:
        amplitude = full_increment_v * fraction
        values.extend(((f"minus-{fraction:g}", -amplitude), (f"plus-{fraction:g}", amplitude)))
    return tuple(values)

def select_preparation_slice(
    times_s: np.ndarray[Any, Any],
    baseline_valid: np.ndarray[Any, Any],
    refined_valid: np.ndarray[Any, Any],
) -> int:
    """Select the earliest source slice valid in both frozen numerical views."""

    if (
        times_s.ndim != 1
        or baseline_valid.shape != times_s.shape
        or refined_valid.shape != times_s.shape
    ):
        raise ValueError("static-validity rosters do not align")
    eligible = np.flatnonzero(
        np.asarray(baseline_valid, dtype=bool) & np.asarray(refined_valid, dtype=bool)
    )
    if not eligible.size:
        raise ValueError("no public preparation is valid in both numerical views")
    if np.any(np.diff(np.asarray(times_s, dtype=float)) <= 0):
        raise ValueError("public preparation times are not strictly increasing")
    return int(eligible[0])

def select_canary(
    episodes: list[dict[str, Any]], *, materiality_t: float = 0.0017
) -> dict[str, object]:
    """Apply the predeclared smallest-amplitude/earliest-horizon rule."""

    if not math.isfinite(materiality_t) or materiality_t <= 0:
        raise ValueError("materiality threshold must be positive and finite")
    by_key = {(int(row["view"]), str(row["word"])): row for row in episodes}
    for fraction in FRACTIONS:
        words = (f"minus-{fraction:g}", "hold", f"plus-{fraction:g}")
        if any((view, word) not in by_key for view in VIEWS for word in words):
            raise ValueError("canary episode roster is incomplete")
        if any(not bool(by_key[view, word]["valid"]) for view in VIEWS for word in words):
            continue
        for horizon in HORIZONS_S:
            key = format(horizon, ".3f")
            qualified = True
            contrasts: list[float] = []
            for view in VIEWS:
                minus = float(by_key[view, words[0]]["pickup_1_t"][key])
                hold = float(by_key[view, "hold"]["pickup_1_t"][key])
                plus = float(by_key[view, words[2]]["pickup_1_t"][key])
                initial = float(by_key[view, "hold"]["pickup_1_t"]["0.000"])
                contrast = min(plus - hold, hold - minus)
                hold_drift = abs(hold - initial)
                other = VIEWS[1] if view == VIEWS[0] else VIEWS[0]
                view_gap = abs(hold - float(by_key[other, "hold"]["pickup_1_t"][key]))
                qualified &= contrast > 0 and contrast > 2 * max(hold_drift, view_gap)
                contrasts.append(contrast)
            if qualified:
                minimum = min(contrasts)
                return {
                    "disposition": (
                        "SUPPORTED" if minimum >= materiality_t else "METHOD_MATERIALITY_INCOMPATIBLE"
                    ),
                    "selected_fraction": fraction,
                    "selected_horizon_s": horizon,
                    "minimum_signed_contrast_t": minimum,
                    "reason_codes": (
                        [] if minimum >= materiality_t else ["CONFIRMATORY_G1R_MATERIALITY_NOT_REACHED"]
                    ),
                }
    return {
        "disposition": "SHORT_HORIZON_SOURCE_UNEVALUABLE",
        "selected_fraction": None,
        "selected_horizon_s": None,
        "minimum_signed_contrast_t": None,
        "reason_codes": ["NO_VALID_SIGNED_VIEW_STABLE_SHORT_HORIZON"],
    }

def _admission_limit(inductance: np.ndarray[Any, Any], resistance: np.ndarray[Any, Any], labels: tuple[str, ...], baseline: np.ndarray[Any, Any]) -> float:
    from scipy.linalg import expm

    inductance = np.asarray(inductance, dtype=float)
    resistance = np.asarray(resistance, dtype=float)
    dynamics = np.linalg.solve(inductance, np.diag(resistance))
    forcing = np.linalg.solve(inductance, np.eye(12))
    p4 = labels.index("p4")
    maximum = np.zeros(12, dtype=float)
    for clock in np.linspace(0.0, HORIZONS_S[-1], 61):
        kernel = np.linalg.solve(dynamics, np.eye(12) - expm(-dynamics * clock)) @ forcing
        maximum = np.maximum(maximum, np.abs(kernel[:, p4]))
    candidates = []
    for index, label in enumerate(labels):
        if label not in CURRENT_LIMITS_A or maximum[index] == 0:
            continue
        lower, upper = CURRENT_LIMITS_A[label]
        headroom = min(upper - baseline[index], baseline[index] - lower)
        if headroom <= 0:
            raise ValueError(f"{label} lacks symmetric current headroom")
        candidates.append(0.05 * headroom / maximum[index])
    value = math.floor(min(candidates) * 1_000_000) / 1_000_000
    if value <= 0:
        raise ValueError("derived admission voltage limit is not positive")
    return float(value)

def _currents_valid(
    labels: tuple[str, ...],
    minimum: np.ndarray[Any, Any],
    maximum: np.ndarray[Any, Any],
) -> bool:
    return all(
        minimum[labels.index(label)] >= lower and maximum[labels.index(label)] <= upper
        for label, (lower, upper) in CURRENT_LIMITS_A.items()
    )




def voltage_vector(baseline: np.ndarray[Any, Any], resistance: np.ndarray[Any, Any], labels: tuple[str, ...], increment_v: float) -> tuple[np.ndarray[Any, Any], str]:
    """Form the exact constant active-coil voltage vector and its byte identity."""
    import hashlib

    voltage = baseline * resistance
    voltage[labels.index("p4")] += increment_v
    vector_sha = hashlib.sha256(np.asarray(voltage, dtype="<f8").tobytes()).hexdigest()
    return voltage, vector_sha


def current_extrema(minimum: np.ndarray[Any, Any], maximum: np.ndarray[Any, Any], currents: np.ndarray[Any, Any]) -> tuple[np.ndarray[Any, Any], np.ndarray[Any, Any]]:
    """Retain the complete active-coil envelope across observed native steps."""
    return np.minimum(minimum, currents), np.maximum(maximum, currents)


def assemble_canary_episode(
    *, active_labels: tuple[str, ...], extrema_min: np.ndarray[Any, Any], extrema_max: np.ndarray[Any, Any],
    validity: bool, domain_departed: bool, snapshots: dict[str, float], completed_steps: int,
    view: int, word: str, increment_v: float, vector_sha: str, max_relative_change: float,
    runtime_s: float,
) -> dict[str, object]:
    """Assemble the complete signed-response canary census from observed operands."""
    current_valid = _currents_valid(active_labels, extrema_min, extrema_max)
    valid = bool(
        validity
        and not domain_departed
        and current_valid
        and set(snapshots) == {"0.000", "0.005", "0.010", "0.015"}
    )
    return {
        "episode_id": f"canary.view-{view}.{word}",
        "view": view,
        "word": word,
        "requested_increment_v": increment_v,
        "accepted_increment_v": increment_v,
        "applied_vector_sha256": vector_sha,
        "realized_vector_sha256": vector_sha if completed_steps else None,
        "applied_clocks_s": [format(step * DT_S, ".4f") for step in range(completed_steps)],
        "pickup_1_t": snapshots,
        "valid": valid,
        "domain_departed": domain_departed,
        "current_limits_passed": bool(current_valid),
        "maximum_nk_relative_change": max_relative_change,
        "runtime_s": runtime_s,
    }
