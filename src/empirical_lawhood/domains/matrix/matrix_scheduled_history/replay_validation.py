# SPDX-License-Identifier: MPL-2.0
"""Pure validation of original scheduled-history numerical transformations.

This owner receives decoded arrays and records. Authentication, access lifetimes
and publication remain application/storage responsibilities.
"""
from dataclasses import replace
import numpy as np


def same_values(actual, expected, label):
    """Exact finite values and nonuse locations, preserving original archive bytes."""
    if set(actual) != set(expected):
        raise PermissionError("native derived replay changes complete " + label + " array members")
    for name, value in expected.items():
        received = actual[name]
        if received.dtype.str != value.dtype.str or received.shape != value.shape:
            raise PermissionError("native derived replay changes " + label + " array dtype/shape")
        # Complex nonuse is checked per real/imaginary component; a NaN in one
        # component cannot hide a changed finite value in the other component.
        equal = (np.array_equal(received.real, value.real, equal_nan=True)
            and np.array_equal(received.imag, value.imag, equal_nan=True)) if value.dtype.kind == "c" else np.array_equal(received, value, equal_nan=True)
        if not equal:
            raise PermissionError("native derived replay changes " + label + " received array values")



def validate_derived_arrays(*, source, protocol, records, prefix, diagnostic, causal_arrays, frozen, templates):
    """Reconstruct original measurement/frame/cutoff/physical transforms only.

    The caller separately authenticates native prefix custody and its actual
    numerical assessment. This pure seam grants no receipt or source authority.
    No archive is regenerated and no physical trajectory is acquired.
    """
    from empirical_lawhood.domains.matrix.matrix_scheduled_history import science, response_forecast
    witness, frames, causal, physical, numerical = (records[key] for key in ("witness", "frames", "causal", "physical", "numerical"))
    expected_diagnostic, traces = science.measure_prefix_values(source, prefix)
    same_values(diagnostic, expected_diagnostic, "prefix diagnostic")
    if witness.traces != traces:
        raise PermissionError("native derived replay changes original complete measured traces")
    controls = science.check_prefix_frame_values(source, traces, prefix, diagnostic)
    if frames != replace(frames, controls=controls,
            numerical_pass=all(value.disposition in ("SATISFIED", "NOT_APPLICABLE") for value in controls)):
        raise PermissionError("native derived replay changes original independent frame controls")
    values, frame_sha, disposition, reason = science.causal_cutoff_values(source, traces,
        numerical.numerical_pass, frames.numerical_pass, prefix, diagnostic)
    same_values(causal_arrays, values, "causal cutoff")
    if causal != replace(causal, frame_sha256=frame_sha, disposition=disposition, reason=reason):
        raise PermissionError("native derived replay changes actual causal cutoff/origin/nonuse")
    # Existing cold forecast owner checks retained complete eigensystems and
    # literal Hessian derivatives before reconstructing all mechanical views.
    predicted, disposition, dispositions = response_forecast.forecast_response_arrays(protocol, causal_arrays, templates,
        disposition=causal.disposition, retained=frozen)
    same_values(frozen, predicted, "physical forecast")
    if (physical.disposition, physical.dispositions) != (disposition, dispositions):
        raise PermissionError("native derived replay changes actual physical availability/nonuse")

