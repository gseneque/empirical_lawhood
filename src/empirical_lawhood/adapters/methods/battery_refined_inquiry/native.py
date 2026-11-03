# SPDX-License-Identifier: MPL-2.0
"""New typed numerical selections through the existing native full-state core."""
from functools import partial
from empirical_lawhood.adapters.methods.battery_thermal_inquiry.native import acquire_with_numerics
from empirical_lawhood.adapters.methods.battery_dfn_precision_diagnostic.contracts import ADDITIONAL_SOURCE_MEMBERS
from .contracts import NativeConfig, Trace, ChargingAttempt


def acquire(config):
    if type(config) is not NativeConfig:
        raise ValueError("refined acquisition requires its own exact typed config")
    config.__post_init__()
    settings = config.numerical_view
    return acquire_with_numerics(config, electrode_points=settings.electrode_points,
        particle_points=settings.particle_points, rtol=settings.rtol, atol=settings.atol,
        additional_source_members=ADDITIONAL_SOURCE_MEMBERS, trace_factory=Trace,
        charging_attempt_factory=partial(ChargingAttempt, configuration=config))
