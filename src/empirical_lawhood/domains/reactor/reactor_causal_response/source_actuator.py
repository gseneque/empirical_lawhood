"""Authenticate pinned external reactor source and bind its actuator statements."""
from hashlib import sha256
import json
from types import SimpleNamespace
import numpy as np
from empirical_lawhood.domains.reactor.reactor_prefix_response.reference_forecast import _native_actuator_projection
from empirical_lawhood.domains.reactor.reactor_prefix_response.contracts import PARAMS_SHA256, PLANT_SHA256
from empirical_lawhood.domains.reactor.reactor_causal_response.actuator import Actuator


def bind_native_actuator(plant: bytes, params: bytes) -> Actuator:
    """Bind the authenticated native actuator extraction to its scientific interface."""
    if sha256(plant).hexdigest() != PLANT_SHA256 or sha256(params).hexdigest() != PARAMS_SHA256:
        raise ValueError("actuator source pin differs")
    spec = json.loads(params)
    a, d, t = spec["actuators"], spec["dosing"], spec["timing"]
    return Actuator(
        projector=_native_actuator_projection(plant, {"np": np}),
        params=SimpleNamespace(
            dose_window_s=d["window_s"],
            dose_total_kg=d["total_mass_kg"],
            sample_dt_s=t["sample_dt_s"],
            **a,
        ),
    )
