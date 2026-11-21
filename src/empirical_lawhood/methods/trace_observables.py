"""Clock-aware observables for independently acquired action/receiver traces.

These functions neither acquire data nor choose a scientific denominator.  The
caller must author the clock, horizon, frequency and receiver before evaluation.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def clocked_values(time_s, values, *, horizon_s: float | None = None):
    """Validate finite scalar samples; never silently extrapolate a horizon."""
    clock = np.asarray(time_s, dtype=np.float64)
    signal = np.asarray(values, dtype=np.float64)
    if clock.ndim != 1 or signal.shape != clock.shape or clock.size < 2:
        raise ValueError("a scalar trace needs at least two matched clock samples")
    if not np.isfinite(clock).all() or not np.isfinite(signal).all():
        raise ValueError("a trace contains nonfinite values")
    if clock[0] != 0 or np.any(np.diff(clock) <= 0):
        raise ValueError("relative trace clock must begin at zero and strictly increase")
    if horizon_s is not None and (
        not np.isfinite(horizon_s) or horizon_s <= 0 or clock[-1] < horizon_s
    ):
        raise ValueError("trace does not cover the declared positive horizon")
    return clock, signal


def truncate_at(time_s, values, horizon_s: float, *, maximum_sample_gap_s: float | None = None):
    """Retain a declared horizon using linear interpolation at its endpoint."""
    clock, signal = clocked_values(time_s, values, horizon_s=horizon_s)
    if maximum_sample_gap_s is not None:
        if not np.isfinite(maximum_sample_gap_s) or maximum_sample_gap_s <= 0:
            raise ValueError("maximum sample gap must be positive and finite")
        end = np.searchsorted(clock, horizon_s, side="left")
        if np.any(np.diff(clock[:end + 1]) > maximum_sample_gap_s):
            raise ValueError("a source sample gap exceeds the declared limit")
    keep = clock < horizon_s
    return (
        np.concatenate((clock[keep], [horizon_s])),
        np.concatenate((signal[keep], [np.interp(horizon_s, clock, signal)])),
    )


def time_integral(time_s, values, horizon_s: float) -> float:
    clock, signal = truncate_at(time_s, values, horizon_s)
    return float(np.trapezoid(signal, clock))


@dataclass(frozen=True, slots=True)
class HarmonicResponse:
    """Response/action phasor with a declared cos-minus-i-sin convention."""

    real: float
    imag: float
    input_amplitude: float
    residual_rms: float
    condition_number: float

    @property
    def magnitude(self) -> float:
        return float(np.hypot(self.real, self.imag))


def harmonic_response(time_s, action, receiver, *, frequency_hz: float, horizon_s: float,
                      minimum_cycles: float = 2.0, maximum_condition: float = 1e8) -> HarmonicResponse:
    """Fit a DC + sinusoid on the actual clock, without FFT-bin substitution.

    A frequency/horizon supporting fewer than the authored minimum cycles, an
    unexcited action, or a rank-deficient observation is explicitly unevaluable.
    Both amplitudes use exactly the same clock and least-squares design.
    """
    if not np.isfinite(frequency_hz) or frequency_hz <= 0:
        raise ValueError("frequency must be positive and finite")
    if not np.isfinite(minimum_cycles) or minimum_cycles <= 0:
        raise ValueError("minimum cycles must be positive and finite")
    if not np.isfinite(maximum_condition) or maximum_condition < 1:
        raise ValueError("maximum condition must be finite and at least one")
    clock, stimulus = truncate_at(time_s, action, horizon_s)
    response_clock, response = truncate_at(time_s, receiver, horizon_s)
    if not np.array_equal(clock, response_clock):
        raise ValueError("action and receiver clocks differ")
    if frequency_hz * horizon_s < minimum_cycles or clock.size < 6:
        raise ValueError("insufficient clock support for the requested frequency")
    if np.max(np.diff(clock)) >= 0.5 / frequency_hz:
        raise ValueError("clock cannot resolve the requested modulation frequency")
    phase = 2 * np.pi * frequency_hz * clock
    design = np.column_stack((np.ones(clock.size), np.cos(phase), np.sin(phase)))
    condition = float(np.linalg.cond(design))
    if not np.isfinite(condition) or condition > maximum_condition:
        raise ValueError("harmonic fit is ill-conditioned")
    coefficients, _, rank, _ = np.linalg.lstsq(design, np.column_stack((stimulus, response)), rcond=None)
    if rank != 3:
        raise ValueError("harmonic fit lacks full rank")
    phasors = coefficients[1] - 1j * coefficients[2]
    amplitude = float(abs(phasors[0]))
    threshold = 64 * np.finfo(np.float64).eps * max(1.0, float(np.max(np.abs(stimulus))))
    if amplitude <= threshold:
        raise ValueError("requested action has no resolvable modulation")
    transfer = phasors[1] / phasors[0]
    residual = float(np.sqrt(np.mean((response - design @ coefficients[:, 1]) ** 2)))
    return HarmonicResponse(float(transfer.real), float(transfer.imag), amplitude, residual, condition)
