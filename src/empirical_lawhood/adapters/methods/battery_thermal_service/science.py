# SPDX-License-Identifier: MPL-2.0
"""Source-owned acquisition and independent exposed service assessment."""

from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
import os
from pathlib import Path

from .contracts import (
    BatteryThermalAssessment, BatteryThermalTrace, EVENTS, GEOMETRY_SHA256,
    MODEL_MEMBERS, PARAMETER_SHA256, SOURCE_VERSION,
)


def _decimal(value):
    return Decimal(str(float(value)))


def acquire(config):
    """One selected solve. Failures retain a typed terminal, without retries."""
    os.environ["PYBAMM_DISABLE_TELEMETRY"] = "true"
    import numpy as np
    import pybamm

    implementation = sha256(Path(__file__).read_bytes()).hexdigest()
    accepted = applied = None
    accepted_clock = applied_clock = None
    events = ()
    processed_events = ()
    try:
        if pybamm.__version__ != SOURCE_VERSION:
            raise ValueError("installed PyBaMM source version differs")
        root = Path(pybamm.__file__).parent
        for member, expected in (
            ("input/parameters/lithium_ion/Chen2020.py", PARAMETER_SHA256),
            ("parameters/geometric_parameters.py", GEOMETRY_SHA256),
        ) + MODEL_MEMBERS:
            if sha256((root / member).read_bytes()).hexdigest() != expected:
                raise ValueError("installed PyBaMM source member differs")
        model = pybamm.lithium_ion.SPMe(options={
            "thermal": "lumped", "cell geometry": "arbitrary", "dimensionality": 0,
            "surface temperature": "ambient", "contact resistance": "false",
            "use lumped thermal capacity": "false", "operating mode": "current",
        })
        temperature = model.variables["Volume-averaged cell temperature [K]"]
        model.events.extend((
            pybamm.Event(EVENTS[2], 318.15 - temperature, pybamm.EventType.TERMINATION),
            pybamm.Event(EVENTS[3], temperature - 273.15, pybamm.EventType.TERMINATION),
        ))
        events = tuple(sorted(event.name for event in model.events if event.name in EVENTS))
        if events != EVENTS:
            raise ValueError("source-native protective event census differs")
        parameters = pybamm.ParameterValues("Chen2020")
        parameters.update({"Current function [A]": float(config.current_a),
                           "Initial temperature [K]": float(config.initial_temperature_k),
                           "Ambient temperature [K]": float(config.initial_temperature_k)})
        accepted = _decimal(parameters["Current function [A]"])
        # Parameter acceptance occurs at the new model's time origin before
        # solve, not at a copied controller request or receipt wall clock.
        accepted_clock = Decimal(0)
        tighter = config.view == "tighter"
        solver = pybamm.CasadiSolver(mode="safe", rtol=1e-7 if tighter else 1e-5,
                                    atol=1e-8 if tighter else 1e-6, dt_max=10)
        simulation = pybamm.Simulation(model, parameter_values=parameters, solver=solver,
                                      var_pts={name: 20 for name in ("x_n", "x_s", "x_p", "r_n", "r_p")})
        simulation.build(initial_soc=float(config.initial_soc))
        processed_events = tuple(str(next(event.expression for event in simulation.built_model.events if event.name == name)) for name in EVENTS)
        # The discretised current variable supplies application evidence, distinct
        # from the request and ParameterValues acceptance read above.
        # Variable processing can be delayed until this supported accessor read.
        applied_clock = _decimal(np.asarray(simulation.built_model.get_processed_variable("Time [s]").evaluate(t=0)).reshape(-1)[0])
        applied = _decimal(np.asarray(simulation.built_model.get_processed_variable("Current [A]").evaluate(t=float(applied_clock))).reshape(-1)[0])
        solution = simulation.solve(np.arange(0, 901, 1 if tighter else 10))
        clocks = np.asarray(solution.t, dtype=float).reshape(-1)
        columns = [tuple(_decimal(value) for value in np.asarray(solution[name](clocks), dtype=float).reshape(-1))
                   for name in ("Current [A]", "Terminal voltage [V]", "Discharge capacity [A.h]", "Volume-averaged cell temperature [K]")]
        complete = solution.termination == "final time" and clocks[-1] == 900
        return BatteryThermalTrace(config, config.source.fingerprint(), implementation,
                                   "COMPLETE" if complete else "SIMULATOR_TERMINATED",
                                   str(solution.termination), () if complete else ("native-termination",),
                                   config.current_a, accepted, applied,
                                   tuple(_decimal(value) for value in clocks), *columns, events, processed_events,
                                   accepted_model_clock_s=accepted_clock, applied_model_clock_s=applied_clock)
    except (ValueError, RuntimeError, KeyError, FileNotFoundError) as error:
        return BatteryThermalTrace(config, config.source.fingerprint(), implementation,
                                   "TECHNICAL_OBSERVATION_FAILURE", type(error).__name__,
                                   ("native-observation-failure",), config.current_a, accepted, applied,
                                   (), (), (), (), (), events, processed_events,
                                   accepted_model_clock_s=accepted_clock, applied_model_clock_s=applied_clock)


def assess(config, trace):
    """Integrate the realized current; never infer delivery from a request."""
    if config.operation != "assess":
        raise ValueError("thermal assessment requires its separately selected operation")
    if trace.config != replace(config, operation="acquire"):
        # Config identities belong to their operation, so compare the scientific
        # fields separately when the authored nodes use distinct labels.
        expected = replace(config, operation="acquire", config_id=trace.config.config_id)
        if trace.config != expected:
            raise ValueError("thermal assessment substitutes its producing scientific operands")
    reasons = []
    realized = capacity = discrepancy = None
    envelope = guarded = False
    if not trace.times_s:
        reasons.append("native-receivers-absent")
    else:
        realized = -sum(((a + b) * (t1 - t0) / Decimal(7200)
                         for t0, t1, a, b in zip(trace.times_s, trace.times_s[1:], trace.current_a, trace.current_a[1:])), Decimal(0))
        capacity = -(trace.discharge_capacity_ah[-1] - trace.discharge_capacity_ah[0])
        discrepancy = abs(realized - capacity)
        # This is a declared numerical receiver agreement, not physical uncertainty.
        if discrepancy > Decimal("1e-8"):
            reasons.append("current-capacity-disagreement")
        if realized < Decimal("0.36375"):
            reasons.append("useful-charge-not-delivered")
        envelope = (all(Decimal("2.5") <= v <= Decimal("4.2") for v in trace.voltage_v)
                    and all(Decimal("273.15") <= t <= Decimal("318.15") for t in trace.volume_mean_temperature_k)
                    and all(abs(i) <= Decimal("1.455") for i in trace.current_a))
        if not envelope:
            reasons.append("sampled-service-envelope-violation")
        if trace.accepted_current_a != config.current_a or trace.applied_current_a != config.current_a or any(i != config.current_a for i in trace.current_a):
            reasons.append("native-current-delivery-differs")
        guarded = (trace.event_names == EVENTS and len(trace.processed_event_expressions) == len(EVENTS)
                   and all(trace.processed_event_expressions) and trace.disposition == "COMPLETE")
    if trace.disposition != "COMPLETE":
        reasons.append("full-service-horizon-not-realized")
    if reasons:
        disposition = "UNEVALUABLE" if not trace.times_s else "SERVICE_FAIL"
    else:
        disposition = "UNEVALUABLE"
        reasons.append("whole-time-certificate-absent")
    return BatteryThermalAssessment(config.fingerprint(), trace.fingerprint(), disposition,
                                    tuple(sorted(reasons)), realized, capacity, discrepancy, envelope, guarded)
