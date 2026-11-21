"""Neuron current acceptance and supplied-array receiver reduction.

This module has only a NumPy dependency and can be loaded directly by a pinned
Brian2 worker without importing the enclosing application package.
"""
import numpy as np


def accept_current(command, maximum):
    """Project the requested current onto the frozen nonnegative action chart."""
    return min(max(command, 0.0), maximum)


def summarize_post_step(times_ms, voltage_mv, spike_times_ms, baseline_ms):
    """Compute the declared post-step mean voltage and spike count."""
    post = np.asarray(voltage_mv)[np.asarray(times_ms) >= baseline_ms]
    return float(np.mean(post)), int(np.count_nonzero(np.asarray(spike_times_ms) >= baseline_ms))
