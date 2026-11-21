"""Native acquisition and external-format binding for the domain science."""

from __future__ import annotations
from decimal import Decimal
from hashlib import sha256
import math
import time
from typing import Any, Mapping
import numpy as np
from empirical_lawhood.science.evidence.evidence import OutcomeAccess
from empirical_lawhood.science.records.serialization import validate_sha256

from empirical_lawhood.domains.battery.reduced_coordinate_sufficiency import (
    BATTERY_REDUCED_OBSERVATION_CAPACITY_FLOOR_AH as _science_BATTERY_REDUCED_OBSERVATION_CAPACITY_FLOOR_AH,
    BATTERY_REDUCED_OBSERVATION_PARAMETER_SET as _science_BATTERY_REDUCED_OBSERVATION_PARAMETER_SET,
    BATTERY_REDUCED_OBSERVATION_ROUTE_ID as _science_BATTERY_REDUCED_OBSERVATION_ROUTE_ID,
    BATTERY_REDUCED_OBSERVATION_SOURCE_VERSION as _science_BATTERY_REDUCED_OBSERVATION_SOURCE_VERSION,
    BATTERY_REDUCED_OBSERVATION_TEMPERATURE_FLOOR_K as _science_BATTERY_REDUCED_OBSERVATION_TEMPERATURE_FLOOR_K,
    BATTERY_REDUCED_OBSERVATION_VOLTAGE_FLOOR_V as _science_BATTERY_REDUCED_OBSERVATION_VOLTAGE_FLOOR_V,
    BatteryReducedObservationDenominator as _science_BatteryReducedObservationDenominator,
    BatteryReducedObservationDesign as _science_BatteryReducedObservationDesign,
    BatteryReducedObservationDisposition as _science_BatteryReducedObservationDisposition,
    BatteryReducedObservationHistory as _science_BatteryReducedObservationHistory,
    BatteryReducedObservationPreparation as _science_BatteryReducedObservationPreparation,
    _future_clock,
    _hex_array,
    _lookup,
    _trace_error,
    canonical_sha256 as _science_canonical_sha256,
    decode_hex as _science_decode_hex,
    stable_json_bytes as _science_stable_json_bytes,
)

def _source_options(denominator: _science_BatteryReducedObservationDenominator) -> dict[str, str]:
    values = {
        "thermal": denominator.thermal.lower(),
        "cell geometry": "pouch",
    }
    if denominator.thermal == "ISOTHERMAL":
        values["calculate heat source for isothermal models"] = "true"
    return values


def _inputs(
    unit: _science_BatteryReducedObservationPreparation,
    current_delta_a: Decimal,
    ambient_delta_k: Decimal,
) -> dict[str, float]:
    return {
        "Current function [A]": float(current_delta_a),
        "Ambient temperature [K]": float(unit.initial_temperature_k + ambient_delta_k),
    }


def _runtime_objects(
    unit: _science_BatteryReducedObservationPreparation,
    denominator: _science_BatteryReducedObservationDenominator,
) -> tuple[Any, Any]:
    import pybamm  # type: ignore[import-untyped]

    if pybamm.__version__ != _science_BATTERY_REDUCED_OBSERVATION_SOURCE_VERSION:
        raise RuntimeError("installed PyBaMM differs from the frozen battery reduced observation source")
    model_class = pybamm.lithium_ion.SPMe if denominator.model == "SPME" else pybamm.lithium_ion.DFN
    model = model_class(options=_source_options(denominator))
    parameters = pybamm.ParameterValues(_science_BATTERY_REDUCED_OBSERVATION_PARAMETER_SET)
    parameters["Current function [A]"] = "[input]"
    parameters["Ambient temperature [K]"] = "[input]"
    parameters["Initial temperature [K]"] = float(unit.initial_temperature_k)
    if denominator.view.solver == "CASADI":
        solver = pybamm.CasadiSolver(
            mode="safe",
            rtol=float(denominator.view.rtol),
            atol=float(denominator.view.atol),
        )
    else:
        solver = pybamm.IDAKLUSolver(
            rtol=float(denominator.view.rtol),
            atol=float(denominator.view.atol),
        )
    points = denominator.view.spatial_points
    simulation = pybamm.Simulation(
        model,
        parameter_values=parameters,
        solver=solver,
        var_pts={
            "x_n": points,
            "x_s": points,
            "x_p": points,
            "r_n": points,
            "r_p": points,
        },
    )
    return pybamm, simulation


def _step_prefix(
    unit: _science_BatteryReducedObservationPreparation,
    denominator: _science_BatteryReducedObservationDenominator,
    history: _science_BatteryReducedObservationHistory,
) -> tuple[Any, Any, Any]:
    pybamm, simulation = _runtime_objects(unit, denominator)
    initial = _inputs(unit, *history.values_at(0))
    simulation.build(initial_soc=float(unit.initial_soc), inputs=initial)
    solution = None
    for start, stop in zip((0, 150, 300), (150, 300, 450), strict=True):
        if start >= history.checkpoint_s:
            break
        duration = min(stop, history.checkpoint_s) - start
        values = _inputs(unit, *history.values_at(start))
        solution = simulation.step(
            duration,
            t_eval=np.asarray([0.0, float(duration)], dtype=np.float64),
            starting_solution=solution,
            inputs=values,
        )
    if solution is None or str(solution.termination) != "final time":
        raise RuntimeError("prefix did not reach the checkpoint")
    return pybamm, simulation, solution


def _scalar_series(solution: Any, variable: str, times: np.ndarray) -> np.ndarray:
    values = np.asarray(solution[variable](times), dtype=np.float64)
    return values.reshape(-1)


def _field_series(solution: Any, variable: str, times: np.ndarray) -> np.ndarray:
    values = np.asarray(solution[variable](times), dtype=np.float64)
    if values.ndim == 1:
        values = values.reshape(1, -1)
    return values.reshape(-1, times.size)


def _receiver_values(solution: Any, times: np.ndarray) -> dict[str, np.ndarray]:
    temperature = _field_series(solution, "Cell temperature [K]", times)
    return {
        "capacity_ah": _scalar_series(solution, "Discharge capacity [A.h]", times),
        "mean_temperature_k": _scalar_series(
            solution,
            "Volume-averaged cell temperature [K]",
            times,
        ),
        "maximum_temperature_k": np.max(temperature, axis=0),
        "terminal_voltage_v": _scalar_series(solution, "Terminal voltage [V]", times),
    }


def _checkpoint_coordinates(
    solution: Any,
    *,
    unit: _science_BatteryReducedObservationPreparation,
    checkpoint_s: int,
) -> dict[str, str]:
    times = np.asarray([float(checkpoint_s)], dtype=np.float64)
    receivers = _receiver_values(solution, times)
    electrolyte = _field_series(
        solution,
        "Electrolyte concentration [mol.m-3]",
        times,
    )
    stoichiometry = _field_series(
        solution,
        "Negative particle surface stoichiometry",
        times,
    )
    total_heating = _scalar_series(
        solution,
        "Volume-averaged total heating [W.m-3]",
        times,
    )
    capacity = float(receivers["capacity_ah"][0])
    values = {
        "soc-coordinate": float(unit.initial_soc) - capacity / 5.0,
        "cumulative-discharged-capacity-ah": capacity,
        "mean-temperature-k": float(receivers["mean_temperature_k"][0]),
        "terminal-voltage-v": float(receivers["terminal_voltage_v"][0]),
        "electrolyte-concentration-contrast": float(
            np.max(electrolyte[:, 0]) - np.min(electrolyte[:, 0])
        ),
        "negative-particle-surface-stoichiometry-contrast": float(
            np.max(stoichiometry[:, 0]) - np.min(stoichiometry[:, 0])
        ),
        "total-heating": float(total_heating[0]),
    }
    if not all(math.isfinite(value) for value in values.values()):
        raise RuntimeError("checkpoint coordinate is nonfinite")
    return {key: value.hex() for key, value in sorted(values.items())}


def _encode_trace(solution: Any, times: np.ndarray) -> dict[str, object]:
    receivers = _receiver_values(solution, times)
    return {
        "time_s_hex": _hex_array(times),
        **{f"{name}_hex": _hex_array(values) for name, values in sorted(receivers.items())},
        "termination": str(solution.termination),
    }


def _checkpoint_receiver(solution: Any, checkpoint_s: int) -> dict[str, str]:
    values = _receiver_values(
        solution,
        np.asarray([float(checkpoint_s)], dtype=np.float64),
    )
    return {key: float(value[0]).hex() for key, value in sorted(values.items())}


def _action_audit(
    solution: Any,
    *,
    unit: _science_BatteryReducedObservationPreparation,
    history: _science_BatteryReducedObservationHistory,
) -> tuple[list[dict[str, object]], bool]:
    rows = []
    for start, stop in zip(
        (0, 150, 300),
        (150, 300, 450),
        strict=True,
    ):
        if start >= history.checkpoint_s:
            break
        end = min(stop, history.checkpoint_s)
        current, ambient_delta = history.values_at(start)
        requested = {
            "current_delta_a": str(current),
            "ambient_delta_k": str(ambient_delta),
        }
        applied = _inputs(unit, current, ambient_delta)
        sample_s = float(start + (end - start) / 2)
        times = np.asarray([sample_s], dtype=np.float64)
        realized_current = float(_scalar_series(solution, "Current [A]", times)[0])
        realized_ambient = float(_scalar_series(solution, "Ambient temperature [K]", times)[0])
        valid = math.isclose(
            realized_current,
            float(current),
            rel_tol=0,
            abs_tol=1e-10,
        ) and math.isclose(
            realized_ambient,
            float(unit.initial_temperature_k + ambient_delta),
            rel_tol=0,
            abs_tol=1e-8,
        )
        rows.append(
            {
                "start_s": start,
                "end_s": end,
                "strict_interior_sample_s": sample_s,
                "requested": requested,
                "accepted": {name: float(value).hex() for name, value in sorted(applied.items())},
                "applied": {name: float(value).hex() for name, value in sorted(applied.items())},
                "realized": {
                    "current_a": realized_current.hex(),
                    "ambient_temperature_k": realized_ambient.hex(),
                },
                "realization_valid": valid,
            }
        )
    return rows, all(bool(row["realization_valid"]) for row in rows)


def _hold_realization(
    solution: Any,
    *,
    unit: _science_BatteryReducedObservationPreparation,
    clock: np.ndarray,
) -> tuple[dict[str, object], bool]:
    current = _scalar_series(solution, "Current [A]", clock)
    ambient = _scalar_series(solution, "Ambient temperature [K]", clock)
    valid = bool(
        np.allclose(current, 0.0, rtol=0, atol=1e-10)
        and np.allclose(
            ambient,
            float(unit.initial_temperature_k),
            rtol=0,
            atol=1e-8,
        )
    )
    return (
        {
            "requested": {
                "current_delta_a": "0",
                "ambient_delta_k": "0",
            },
            "accepted": {
                name: float(value).hex()
                for name, value in sorted(_inputs(unit, Decimal(0), Decimal(0)).items())
            },
            "applied": {
                name: float(value).hex()
                for name, value in sorted(_inputs(unit, Decimal(0), Decimal(0)).items())
            },
            "realized_current_a_hex": _hex_array(current),
            "realized_ambient_temperature_k_hex": _hex_array(ambient),
            "realization_valid": valid,
        },
        valid,
    )


def _starting_solution(
    pybamm: Any,
    *,
    checkpoint_s: int,
    state: np.ndarray,
    model: Any,
    inputs: Mapping[str, float],
) -> Any:
    return pybamm.Solution(
        [np.asarray([float(checkpoint_s)], dtype=np.float64)],
        [state.reshape(-1, 1)],
        [model],
        [{name: np.asarray([float(value)], dtype=np.float64) for name, value in inputs.items()}],
        termination="final time",
        check_solution=False,
    )


def _state_layout_sha256(model: Any) -> str:
    rows = []
    for variable, slices in sorted(
        model.y_slices.items(),
        key=lambda item: str(item[0]),
    ):
        rows.append((str(variable), tuple((value.start, value.stop) for value in slices)))
    return sha256(_science_stable_json_bytes(rows)).hexdigest()


def acquire_cell(
    *,
    design: _science_BatteryReducedObservationDesign,
    unit_id: str,
    denominator_id: str,
    history_id: str,
    source_identity_sha256: str,
    implementation_sha256: str,
    outcome_access: OutcomeAccess,
) -> tuple[dict[str, object], dict[str, object]]:
    """Acquire one native capture and independent direct restart continuation.

    Outcome visibility is a bound record property; callers enforce the
    development/evaluation authority and storage boundary.
    """

    validate_sha256(source_identity_sha256, field_name="source_identity_sha256")
    validate_sha256(implementation_sha256, field_name="implementation_sha256")
    unit, denominator, history = _lookup(
        design,
        unit_id,
        denominator_id,
        history_id,
    )
    return acquire_preparation(
        unit=unit,
        denominator=denominator,
        history=history,
        source_identity_sha256=source_identity_sha256,
        implementation_sha256=implementation_sha256,
        outcome_access=outcome_access,
    )


def acquire_preparation(
    *,
    unit: _science_BatteryReducedObservationPreparation,
    denominator: _science_BatteryReducedObservationDenominator,
    history: _science_BatteryReducedObservationHistory,
    source_identity_sha256: str,
    implementation_sha256: str,
    outcome_access: OutcomeAccess,
) -> tuple[dict[str, object], dict[str, object]]:
    """Acquire a fresh typed preparation without the historical design roster."""

    validate_sha256(source_identity_sha256, field_name="source_identity_sha256")
    validate_sha256(implementation_sha256, field_name="implementation_sha256")
    if (
        not isinstance(unit, _science_BatteryReducedObservationPreparation)
        or not isinstance(denominator, _science_BatteryReducedObservationDenominator)
        or not isinstance(history, _science_BatteryReducedObservationHistory)
    ):
        raise TypeError("battery reduced observation preparation, denominator or history has another type")
    if not isinstance(outcome_access, OutcomeAccess):
        raise TypeError("battery reduced observation outcome-access stage has another type")
    started = time.monotonic()
    key = {
        "unit_id": unit.unit_id,
        "denominator_id": denominator.denominator_id,
        "history_id": history.history_id,
    }
    try:
        pybamm, source_simulation, prefix = _step_prefix(unit, denominator, history)
        state = np.asarray(prefix.last_state.y, dtype=np.float64).reshape(-1)
        if not np.all(np.isfinite(state)):
            raise RuntimeError("checkpoint state is nonfinite")
        source_inputs = {
            name: float(np.asarray(value, dtype=np.float64).reshape(-1)[0])
            for name, value in prefix.last_state.all_inputs[-1].items()
        }
        state_hex = _hex_array(state)
        state_sha256 = sha256(
            _science_stable_json_bytes(
                {
                    "state_hex": state_hex,
                    "source_inputs": {
                        name: float(value).hex() for name, value in sorted(source_inputs.items())
                    },
                }
            )
        ).hexdigest()
        checkpoint = _checkpoint_receiver(prefix, history.checkpoint_s)
        coordinates = _checkpoint_coordinates(
            prefix,
            unit=unit,
            checkpoint_s=history.checkpoint_s,
        )
        prefix_action_rows, prefix_action_valid = _action_audit(
            prefix,
            unit=unit,
            history=history,
        )
        if not prefix_action_valid:
            raise RuntimeError("prefix action realization differs")
        clock = _future_clock(denominator, history)
        relative = clock - history.checkpoint_s
        hold = _inputs(unit, Decimal(0), Decimal(0))
        native_solution = source_simulation.step(
            history.end_s - history.checkpoint_s,
            t_eval=np.concatenate((np.asarray([0.0], dtype=np.float64), relative)),
            starting_solution=prefix,
            inputs=hold,
        )
        available_clock = clock[clock <= float(np.max(native_solution.t)) + 1e-8]
        if available_clock.size == 0:
            raise RuntimeError("native continuation terminated before first future clock")
        native_trace = _encode_trace(native_solution, available_clock)
        native_complete = bool(
            str(native_solution.termination) == "final time"
            and math.isclose(
                float(np.max(native_solution.t)),
                float(history.end_s),
                rel_tol=0,
                abs_tol=1e-8,
            )
        )
        hold_realization, hold_valid = _hold_realization(
            native_solution,
            unit=unit,
            clock=available_clock,
        )
        if not hold_valid:
            raise RuntimeError("native hold realization differs")
        capture: dict[str, object] = {
            "schema": 'empirical-lawhood/simulators/battery-reduced-observation-prediction/native-state-capture',
            "version": "1.0.0",
            "value": {
                **key,
                "stage": unit.stage.value,
                "stratum_id": unit.stratum_id,
                "initial_soc": str(unit.initial_soc),
                "initial_temperature_k": str(unit.initial_temperature_k),
                "checkpoint_s": history.checkpoint_s,
                "end_s": history.end_s,
                "source_identity_sha256": source_identity_sha256,
                "implementation_sha256": implementation_sha256,
                "state_hex": state_hex,
                "state_payload_sha256": state_sha256,
                "state_layout_sha256": _state_layout_sha256(source_simulation.built_model),
                "source_inputs_hex": {
                    name: float(value).hex() for name, value in sorted(source_inputs.items())
                },
                "checkpoint_receiver_hex": checkpoint,
                "checkpoint_coordinates_hex": coordinates,
                "prefix_action_rows": prefix_action_rows,
                "continuation_hold_realization": hold_realization,
                "native_trace": native_trace,
                "disposition": (
                    _science_BatteryReducedObservationDisposition.COMPLETE.value
                    if native_complete
                    else _science_BatteryReducedObservationDisposition.TERMINATED.value
                ),
                "reason_codes": (
                    [] if native_complete else ["SOURCE_TERMINATED_BEFORE_FROZEN_HORIZON"]
                ),
                "outcome_access": outcome_access.value,
                "runtime_seconds": time.monotonic() - started,
            },
        }
        if not native_complete:
            return (
                capture,
                {
                    "schema": 'empirical-lawhood/simulators/battery-reduced-observation-prediction/exact-state-continuation-result',
                    "version": "1.0.0",
                    "value": {
                        **key,
                        "route_id": _science_BATTERY_REDUCED_OBSERVATION_ROUTE_ID,
                        "capture_sha256": _science_canonical_sha256(capture),
                        "disposition": _science_BatteryReducedObservationDisposition.TERMINATED.value,
                        "reason_codes": ["SOURCE_TERMINATION_PRECLUDES_DIRECT_RESTART_SENTINEL"],
                        "outcome_access": outcome_access.value,
                        "runtime_seconds": 0.0,
                    },
                },
            )
    except Exception as error:
        message = str(error).lower()
        if any(token in message for token in ("terminated", "termination", "event")):
            failure_disposition = _science_BatteryReducedObservationDisposition.TERMINATED
        elif isinstance(error, KeyError):
            failure_disposition = _science_BatteryReducedObservationDisposition.RECEIVER_INVALID
        else:
            failure_disposition = _science_BatteryReducedObservationDisposition.SOURCE_FAILURE
        failure: dict[str, object] = {
            "schema": 'empirical-lawhood/simulators/battery-reduced-observation-prediction/native-state-capture',
            "version": "1.0.0",
            "value": {
                **key,
                "stage": unit.stage.value,
                "stratum_id": unit.stratum_id,
                "source_identity_sha256": source_identity_sha256,
                "implementation_sha256": implementation_sha256,
                "disposition": failure_disposition.value,
                "reason_codes": [f"PYBAMM_{type(error).__name__.upper()}"],
                "error_summary": str(error)[:500],
                "outcome_access": outcome_access.value,
                "runtime_seconds": time.monotonic() - started,
            },
        }
        r3_skipped: dict[str, object] = {
            "schema": 'empirical-lawhood/simulators/battery-reduced-observation-prediction/exact-state-continuation-result',
            "version": "1.0.0",
            "value": {
                **key,
                "route_id": _science_BATTERY_REDUCED_OBSERVATION_ROUTE_ID,
                "disposition": _science_BatteryReducedObservationDisposition.DIRECT_RESTART_FAILURE.value,
                "reason_codes": ["CAPTURE_NOT_COMPLETE"],
                "outcome_access": outcome_access.value,
                "runtime_seconds": 0.0,
            },
        }
        return failure, r3_skipped

    r3_started = time.monotonic()
    try:
        capture_value = capture["value"]
        assert isinstance(capture_value, dict)
        state = _science_decode_hex(capture_value["state_hex"])
        if _hex_array(state) != capture_value["state_hex"]:
            raise ValueError("direct restart state round trip changed")
        pybamm, target_simulation = _runtime_objects(unit, denominator)
        hold = _inputs(unit, Decimal(0), Decimal(0))
        target_simulation.build(initial_soc=float(unit.initial_soc), inputs=hold)
        target_model = target_simulation.built_model
        if _state_layout_sha256(target_model) != capture_value["state_layout_sha256"]:
            raise ValueError("direct restart target state layout differs")
        source_inputs = {
            name: float.fromhex(value) for name, value in capture_value["source_inputs_hex"].items()
        }
        start = _starting_solution(
            pybamm,
            checkpoint_s=history.checkpoint_s,
            state=state,
            model=target_model,
            inputs=source_inputs,
        )
        clock = _future_clock(denominator, history)
        solution = target_simulation.step(
            history.end_s - history.checkpoint_s,
            t_eval=np.concatenate(
                (
                    np.asarray([0.0], dtype=np.float64),
                    clock - history.checkpoint_s,
                )
            ),
            starting_solution=start,
            inputs=hold,
        )
        trace = _encode_trace(solution, clock)
        if trace["termination"] != "final time":
            raise RuntimeError("direct restart continuation terminated")
        route_hold_realization, route_hold_valid = _hold_realization(
            solution,
            unit=unit,
            clock=clock,
        )
        if not route_hold_valid:
            raise RuntimeError("direct restart hold realization differs")
        native_trace = capture_value["native_trace"]
        errors = _trace_error(trace, native_trace)
        floors = {
            "capacity_ah": float(_science_BATTERY_REDUCED_OBSERVATION_CAPACITY_FLOOR_AH),
            "mean_temperature_k": float(_science_BATTERY_REDUCED_OBSERVATION_TEMPERATURE_FLOOR_K),
            "maximum_temperature_k": float(_science_BATTERY_REDUCED_OBSERVATION_TEMPERATURE_FLOOR_K),
            "terminal_voltage_v": float(_science_BATTERY_REDUCED_OBSERVATION_VOLTAGE_FLOOR_V),
        }
        closed = all(errors[name] <= floors[name] for name in floors)
        result: dict[str, object] = {
            "schema": 'empirical-lawhood/simulators/battery-reduced-observation-prediction/exact-state-continuation-result',
            "version": "1.0.0",
            "value": {
                **key,
                "route_id": _science_BATTERY_REDUCED_OBSERVATION_ROUTE_ID,
                "capture_sha256": _science_canonical_sha256(capture),
                "trace": trace,
                "continuation_hold_realization": route_hold_realization,
                "maximum_receiver_errors": errors,
                "receiver_closed": closed,
                "state_bit_exact": True,
                "disposition": _science_BatteryReducedObservationDisposition.COMPLETE.value,
                "reason_codes": [] if closed else ["DIRECT_RESTART_RECEIVER_FLOOR_EXCEEDED"],
                "outcome_access": outcome_access.value,
                "runtime_seconds": time.monotonic() - r3_started,
            },
        }
    except Exception as error:
        result = {
            "schema": 'empirical-lawhood/simulators/battery-reduced-observation-prediction/exact-state-continuation-result',
            "version": "1.0.0",
            "value": {
                **key,
                "route_id": _science_BATTERY_REDUCED_OBSERVATION_ROUTE_ID,
                "capture_sha256": _science_canonical_sha256(capture),
                "disposition": _science_BatteryReducedObservationDisposition.DIRECT_RESTART_FAILURE.value,
                "reason_codes": [f"DIRECT_RESTART_{type(error).__name__.upper()}"],
                "error_summary": str(error)[:500],
                "outcome_access": outcome_access.value,
                "runtime_seconds": time.monotonic() - r3_started,
            },
        }
    return capture, result
