"""Internal Brian2 worker run only by the installed CLI in a separate pinned env."""

from __future__ import annotations

import json
import platform
import sys
from decimal import Decimal
from pathlib import Path


def main() -> None:
    # Load only the execution-owned stdlib admission primitive, without importing the
    # main package or its NumPy pin into this separate native environment.
    sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "execution"))
    from native_time_grid import (
        BRIAN2_ESTIMATED_BYTES_PER_UPDATE,
        BRIAN2_MAX_ESTIMATED_HISTORY_BYTES,
        admit_native_time_grid,
    )

    sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "domains" / "biology" / "neuron_current_response"))
    from numerics import accept_current, summarize_post_step

    config = json.load(sys.stdin)
    admission = admit_native_time_grid(
        timestep=Decimal(config["timestep_ms"]),
        intervals=(Decimal(config["baseline_ms"]), Decimal(config["horizon_ms"])),
        label="Brian2",
        require_integral_intervals=True,
        sample_offset=0,
        estimated_bytes_per_sample=BRIAN2_ESTIMATED_BYTES_PER_UPDATE,
        maximum_estimated_bytes=BRIAN2_MAX_ESTIMATED_HISTORY_BYTES,
    )
    if type(config.get("sample_count")) is not int or config["sample_count"] != admission.sample_count:
        raise ValueError("Brian2 worker sample count differs from the admitted native grid")
    import brian2 as b
    import numpy as np

    if platform.python_version() != "3.11.14" or b.__version__ != "2.9.0" or np.__version__ != "1.26.4":
        raise RuntimeError("Brian2 native worker requires CPython 3.11.14, Brian2 2.9.0 and NumPy 1.26.4")
    dt = float(config["timestep_ms"])
    baseline = float(config["baseline_ms"])
    horizon = float(config["horizon_ms"])
    tau = float(config["membrane_tau_ms"])
    resistance = float(config["membrane_resistance_mohm"])
    rest = float(config["rest_mv"])
    reset = float(config["reset_mv"])
    threshold = float(config["threshold_mv"])
    requested = float(config["requested_step_pa"])
    maximum = float(config["maximum_accepted_pa"])
    results = []
    for arm, command in (("hold", 0.0), ("step", requested)):
        accepted = accept_current(command, maximum)
        b.start_scope()
        b.prefs.codegen.target = "numpy"
        b.defaultclock.dt = dt * b.ms
        values = np.zeros(admission.sample_count)
        values[admission.interval_updates[0]:] = accepted
        stimulus = b.TimedArray(values * b.pA, dt=dt * b.ms)
        group = b.NeuronGroup(
            1,
            "dv/dt = (v_rest-v + resistance*stimulus(t))/tau : volt",
            threshold="v >= v_threshold",
            reset="v = v_reset",
            method="euler",
            namespace={
                "v_rest": rest * b.mV,
                "v_reset": reset * b.mV,
                "v_threshold": threshold * b.mV,
                "resistance": resistance * b.Mohm,
                "tau": tau * b.ms,
                "stimulus": stimulus,
            },
        )
        group.v = rest * b.mV
        voltage = b.StateMonitor(group, "v", record=True, when="end")
        spikes = b.SpikeMonitor(group)
        b.run((baseline + horizon) * b.ms)
        times_ms = np.asarray(voltage.t / b.ms)
        spike_times = np.asarray(spikes.t / b.ms)
        mean_voltage, spike_count = summarize_post_step(times_ms, np.asarray(voltage.v[0] / b.mV), spike_times, baseline)
        realized = float(stimulus((baseline + dt) * b.ms) / b.pA)
        results.append({
            "arm": arm,
            "requested_pa": command,
            "accepted_pa": accepted,
            "applied_pa": accepted,
            "realized_pa": realized,
            "post_step_mean_mv": mean_voltage,
            "spike_count": spike_count,
            "receiver_horizon_ms": horizon,
        })
    print(json.dumps({"arms": results, "native_runtime": "cpython-3.11.14-brian2-2.9.0-numpy-1.26.4"}, sort_keys=True))


if __name__ == "__main__":
    main()
