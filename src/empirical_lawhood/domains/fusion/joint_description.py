"""Fusion receiver projections and explicit archive-to-simulator mapping."""

from __future__ import annotations

import numpy as np

from empirical_lawhood.methods.trace_observables import harmonic_response, truncate_at


def divertor_modulation(time_s, gas_rate, receiver, *, frequency_hz: float, horizon_s: float):
    """Requested-frequency susceptibility; samples are nested within a shot."""
    return harmonic_response(time_s, gas_rate, receiver,
                             frequency_hz=frequency_hz, horizon_s=horizon_s)


def temperature_change(time_s, receiver_ev, *, horizon_s: float, maximum_sample_gap_s: float | None = None) -> float:
    """Signed core-temperature change in eV on an explicitly supported clock."""
    _, values = truncate_at(time_s, receiver_ev, horizon_s, maximum_sample_gap_s=maximum_sample_gap_s)
    if np.any(values <= 0):
        raise ValueError("fusion core temperature must be positive in eV")
    return float(values[-1] - values[0])


def heating_tracking_error(time_s, power_w, *, baseline_w: float, action: float, horizon_s: float,
                          maximum_sample_gap_s: float) -> float:
    """Largest departure from the selected fractional heating change on its recorded clock."""
    if not np.isfinite(baseline_w) or baseline_w <= 0 or not np.isfinite(action):
        raise ValueError("measured heating requires a positive baseline and a finite action")
    _, powers = truncate_at(time_s, power_w, horizon_s, maximum_sample_gap_s=maximum_sample_gap_s)
    if np.any(powers < 0):
        raise ValueError("recorded coupled power must be nonnegative")
    return float(np.max(np.abs((powers - baseline_w) - action * baseline_w)) / baseline_w)
