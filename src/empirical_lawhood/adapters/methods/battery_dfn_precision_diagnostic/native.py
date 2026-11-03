# SPDX-License-Identifier: MPL-2.0
"""Selected diagnostic native entry, sharing the original full-state core."""

from functools import partial
from empirical_lawhood.adapters.methods.battery_thermal_inquiry.native import (
    acquire_with_numerics,
)
from .contracts import DiagnosticTrace, DiagnosticChargingAttempt


def acquire(config):
    config.__post_init__()
    return acquire_with_numerics(
        config,
        additional_source_members=config.source.additional_source_members,
        electrode_points=config.electrode_points,
        particle_points=config.particle_points,
        rtol=config.rtol,
        atol=config.atol,
        trace_factory=DiagnosticTrace,
        charging_attempt_factory=partial(
            DiagnosticChargingAttempt, configuration=config
        ),
    )
