"""Cortical action-option observables for a newly authored recorded cohort."""

from __future__ import annotations

import numpy as np


def firing_rate(spike_times_s, *, horizon_s: float) -> float:
    """Count the half-open receiver window [0,T); preserve empty spike trains."""
    spikes = np.asarray(spike_times_s, dtype=np.float64)
    if spikes.ndim != 1 or not np.isfinite(spikes).all():
        raise ValueError("spike times must be a finite vector")
    if not np.isfinite(horizon_s) or horizon_s <= 0:
        raise ValueError("cortical receiver horizon must be positive")
    if np.any(spikes < 0) or np.any(np.diff(spikes) <= 0):
        raise ValueError("spike times must be nonnegative and strictly increasing")
    if np.any(spikes > horizon_s):
        raise ValueError("spike train exceeds its declared receiver horizon")
    return float(np.count_nonzero(spikes < horizon_s) / horizon_s)
