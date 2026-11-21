"""Battery receiver and reduced-description calculations for new trials."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from empirical_lawhood.methods.trace_observables import time_integral, truncate_at


@dataclass(frozen=True, slots=True)
class BatteryReceivers:
    terminal_voltage_v: float
    discharge_capacity_ah: float
    peak_temperature_k: float


def battery_receivers(time_s, current_a, voltage_v, temperature_k, *, horizon_s: float) -> BatteryReceivers:
    """Discharge-positive current; capacity is an integral, not a sample count."""
    _, voltage = truncate_at(time_s, voltage_v, horizon_s)
    _, temperature = truncate_at(time_s, temperature_k, horizon_s)
    if np.any(temperature <= 0):
        raise ValueError("battery temperature must be in positive kelvin")
    return BatteryReceivers(float(voltage[-1]), time_integral(time_s, current_a, horizon_s) / 3600,
                            float(np.max(temperature)))


def interval_exceedance(value: float, centre: float, radius: float) -> float:
    """Nonnegative error outside a previously frozen uncertainty interval."""
    if not all(np.isfinite(x) for x in (value, centre, radius)) or radius < 0:
        raise ValueError("uncertainty interval must have finite nonnegative radius")
    return max(0.0, abs(value - centre) - radius)


def continuation_defect(full, reduced, *, scales):
    """Dimensionless coordinatewise defect, retaining every receiver separately."""
    first, second, denominator = (np.asarray(x, dtype=np.float64) for x in (full, reduced, scales))
    if first.ndim != 1 or first.shape != second.shape or first.shape != denominator.shape:
        raise ValueError("continuation receivers and declared scales must match")
    if not all(np.isfinite(x).all() for x in (first, second, denominator)) or np.any(denominator <= 0):
        raise ValueError("continuation values must be finite and scales positive")
    return np.abs(first - second) / denominator
