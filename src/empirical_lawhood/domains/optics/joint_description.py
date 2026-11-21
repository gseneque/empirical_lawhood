"""Signed optical response observables independent of file formats."""

from __future__ import annotations

from empirical_lawhood.methods.trace_observables import truncate_at


def signed_displacement(time_s, position_rad, *, horizon_s: float) -> float:
    """Endpoint displacement in radians; no absolute-value loss of action sign."""
    _, values = truncate_at(time_s, position_rad, horizon_s)
    return float(values[-1] - values[0])
