"""Native acquisition and external-format binding for the domain science."""

from __future__ import annotations
from decimal import Decimal
from hashlib import sha256
import math
import time
from typing import Any, Mapping, Sequence
import numpy as np
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import canonical_json_bytes, validate_stable_id

from empirical_lawhood.domains.battery.electrothermal_hierarchy import (
    BATTERY_ELECTROTHERMAL_BOUNDARIES_S as _science_BATTERY_ELECTROTHERMAL_BOUNDARIES_S,
    BATTERY_ELECTROTHERMAL_HORIZON_S as _science_BATTERY_ELECTROTHERMAL_HORIZON_S,
    BATTERY_ELECTROTHERMAL_PARAMETER_SET as _science_BATTERY_ELECTROTHERMAL_PARAMETER_SET,
    BATTERY_ELECTROTHERMAL_SOURCE_VERSION as _science_BATTERY_ELECTROTHERMAL_SOURCE_VERSION,
    BatteryElectrothermalActionWord as _science_BatteryElectrothermalActionWord,
    BatteryElectrothermalCapturedEpisode as _science_BatteryElectrothermalCapturedEpisode,
    BatteryElectrothermalCheckpointState as _science_BatteryElectrothermalCheckpointState,
    BatteryElectrothermalDenominator as _science_BatteryElectrothermalDenominator,
    BatteryElectrothermalDiagnosticSeries as _science_BatteryElectrothermalDiagnosticSeries,
    BatteryElectrothermalEpisodeDisposition as _science_BatteryElectrothermalEpisodeDisposition,
    BatteryElectrothermalModel as _science_BatteryElectrothermalModel,
    BatteryElectrothermalPreparation as _science_BatteryElectrothermalPreparation,
    BatteryElectrothermalRestartResult as _science_BatteryElectrothermalRestartResult,
    BatteryElectrothermalSolver as _science_BatteryElectrothermalSolver,
    BatteryElectrothermalStageConfig as _science_BatteryElectrothermalStageConfig,
    BatteryElectrothermalThermal as _science_BatteryElectrothermalThermal,
    _decimal,
    _sample_clock,
    action_ledger as _science_action_ledger,
    checkpoint_state as _science_checkpoint_state,
)

def _source_options(denominator: _science_BatteryElectrothermalDenominator) -> dict[str, str]:
    values = {
        "thermal": {
            _science_BatteryElectrothermalThermal.ISOTHERMAL: "isothermal",
            _science_BatteryElectrothermalThermal.LUMPED: "lumped",
            _science_BatteryElectrothermalThermal.X_FULL: "x-full",
        }[denominator.thermal],
        "cell geometry": "pouch",
    }
    if denominator.thermal is _science_BatteryElectrothermalThermal.ISOTHERMAL:
        values["calculate heat source for isothermal models"] = "true"
    return values


def _inputs(
    unit: _science_BatteryElectrothermalPreparation,
    current_delta_a: Decimal,
    ambient_delta_k: Decimal,
) -> dict[str, float]:
    return {
        "Current function [A]": float(current_delta_a),
        "Ambient temperature [K]": float(unit.initial_temperature_k + ambient_delta_k),
    }


def _runtime_objects(
    unit: _science_BatteryElectrothermalPreparation,
    denominator: _science_BatteryElectrothermalDenominator,
) -> tuple[Any, Any]:
    import pybamm  # type: ignore[import-untyped]

    if pybamm.__version__ != _science_BATTERY_ELECTROTHERMAL_SOURCE_VERSION:
        raise RuntimeError("installed PyBaMM differs from the battery electrothermal source")
    model_class = (
        pybamm.lithium_ion.SPMe if denominator.model is _science_BatteryElectrothermalModel.SPME else pybamm.lithium_ion.DFN
    )
    model = model_class(options=_source_options(denominator))
    parameters = pybamm.ParameterValues(_science_BATTERY_ELECTROTHERMAL_PARAMETER_SET)
    parameters["Current function [A]"] = "[input]"
    parameters["Ambient temperature [K]"] = "[input]"
    parameters["Initial temperature [K]"] = float(unit.initial_temperature_k)
    if denominator.view.solver is _science_BatteryElectrothermalSolver.CASADI:
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


def _state_layout_sha256(solution: Any) -> str:
    model = solution.all_models[-1]
    layout = tuple(
        sorted(
            (
                str(variable),
                tuple(
                    (
                        int(item.start or 0),
                        int(item.stop or 0),
                        int(item.step or 1),
                    )
                    for item in (slices if isinstance(slices, list) else [slices])
                ),
            )
            for variable, slices in model.y_slices.items()
        )
    )
    return sha256(canonical_json_bytes(layout)).hexdigest()


def _step_schedule(
    *,
    unit: _science_BatteryElectrothermalPreparation,
    denominator: _science_BatteryElectrothermalDenominator,
    word: _science_BatteryElectrothermalActionWord,
    stop_s: int = _science_BATTERY_ELECTROTHERMAL_HORIZON_S,
) -> tuple[Any, Any, Mapping[int, Any], Decimal]:
    build_started = time.monotonic()
    pybamm, simulation = _runtime_objects(unit, denominator)
    current, ambient = word.values_at(0)
    simulation.build(
        initial_soc=float(unit.initial_soc),
        inputs=_inputs(unit, current, ambient),
    )
    source_build_seconds = _decimal(time.monotonic() - build_started)
    checkpoints: dict[int, Any] = {}
    interval = float(denominator.view.nominal_output_interval_s)
    for start, stop in zip(
        _science_BATTERY_ELECTROTHERMAL_BOUNDARIES_S[:-1],
        _science_BATTERY_ELECTROTHERMAL_BOUNDARIES_S[1:],
        strict=True,
    ):
        if start >= stop_s:
            break
        segment_stop = min(stop, stop_s)
        current, ambient = word.values_at(start)
        duration = segment_stop - start
        relative = np.arange(0.0, duration + interval, interval, dtype=np.float64)
        relative[-1] = float(duration)
        simulation.step(
            duration,
            t_eval=np.unique(relative),
            inputs=_inputs(unit, current, ambient),
        )
        if segment_stop in {300, 450}:
            checkpoints[segment_stop] = simulation.solution.last_state
        if segment_stop == stop_s:
            break
    return pybamm, simulation, checkpoints, source_build_seconds


def _variable(solution: Any, name: str, times: np.ndarray) -> np.ndarray:
    values = np.asarray(solution[name](times), dtype=np.float64)
    if not np.all(np.isfinite(values)):
        raise RuntimeError(f"battery electrothermal source variable {name!r} is nonfinite")
    return values


def _scalar_series(solution: Any, name: str, times: np.ndarray) -> np.ndarray:
    values = _variable(solution, name, times).reshape(-1)
    if values.size != times.size:
        raise RuntimeError(f"battery electrothermal source variable {name!r} is not scalar by clock")
    return values


def _field_by_time(solution: Any, name: str, times: np.ndarray) -> np.ndarray:
    values = _variable(solution, name, times)
    if values.ndim == 1:
        if values.size != times.size:
            raise RuntimeError(f"battery electrothermal source field {name!r} has an invalid shape")
        return values.reshape(1, -1)
    if values.shape[-1] == times.size:
        return values.reshape(-1, times.size)
    if values.shape[0] == times.size:
        return np.moveaxis(values, 0, -1).reshape(-1, times.size)
    raise RuntimeError(f"battery electrothermal source field {name!r} lacks a clock axis")


def _diagnostic(
    diagnostic_id: str,
    unit: str,
    reduction: str,
    values: np.ndarray,
) -> _science_BatteryElectrothermalDiagnosticSeries:
    return _science_BatteryElectrothermalDiagnosticSeries(
        diagnostic_id=diagnostic_id,
        native_unit=unit,
        reduction=reduction,
        values=tuple(_decimal(float(item)) for item in values),
    )


def acquire_episode(
    *,
    config: _science_BatteryElectrothermalStageConfig,
    unit_id: str,
    denominator_id: str,
    word_id: str,
    episode_suffix: str,
) -> _science_BatteryElectrothermalCapturedEpisode:
    """Acquire one complete word while preserving valid partial outcomes."""

    validate_stable_id(episode_suffix, field_name="episode_suffix")
    unit = next(item for item in config.units if item.unit_id == unit_id)
    denominator = next(
        item for item in config.denominators if item.denominator_id == denominator_id
    )
    word = next(item for item in config.words if item.word_id == word_id)
    started = time.monotonic()
    disposition = _science_BatteryElectrothermalEpisodeDisposition.COMPLETE
    reasons: set[str] = set()
    termination = "not-started"
    times = np.asarray([], dtype=np.float64)
    arrays: dict[str, np.ndarray] = {}
    diagnostics: list[_science_BatteryElectrothermalDiagnosticSeries] = []
    absent_diagnostics: set[str] = set()
    temperature_field = np.asarray([], dtype=np.float64)
    temperature_shape: tuple[int, int] | None = None
    checkpoint_records: tuple[_science_BatteryElectrothermalCheckpointState, ...] = ()
    state_length = 0
    source_build_seconds = Decimal(0)
    try:
        _, simulation, checkpoints, source_build_seconds = _step_schedule(
            unit=unit,
            denominator=denominator,
            word=word,
        )
        solution = simulation.solution
        termination = str(solution.termination)
        times = _sample_clock(denominator.view.nominal_output_interval_s)
        arrays["capacity"] = _scalar_series(
            solution,
            "Discharge capacity [A.h]",
            times,
        )
        arrays["temperature"] = _scalar_series(
            solution,
            "Volume-averaged cell temperature [K]",
            times,
        )
        arrays["voltage"] = _scalar_series(solution, "Terminal voltage [V]", times)
        source_current = _scalar_series(solution, "Current [A]", times)
        source_ambient = _scalar_series(solution, "Ambient temperature [K]", times)
        arrays["current"] = source_current
        arrays["ambient"] = source_ambient

        cell_temperature = _field_by_time(solution, "Cell temperature [K]", times)
        arrays["maximum_temperature"] = np.max(cell_temperature, axis=0)
        if denominator.thermal is _science_BatteryElectrothermalThermal.X_FULL:
            temperature_field = cell_temperature
            temperature_shape = (
                int(cell_temperature.shape[0]),
                int(cell_temperature.shape[1]),
            )

        scalar_diagnostics = (
            (
                "diagnostic.total-heating",
                "Volume-averaged total heating [W.m-3]",
                "W.m-3",
            ),
            (
                "diagnostic.ohmic-heating",
                "Volume-averaged Ohmic heating [W.m-3]",
                "W.m-3",
            ),
            (
                "diagnostic.irreversible-heating",
                "Volume-averaged irreversible electrochemical heating [W.m-3]",
                "W.m-3",
            ),
            (
                "diagnostic.reversible-heating",
                "Volume-averaged reversible heating [W.m-3]",
                "W.m-3",
            ),
            (
                "diagnostic.negative-reaction-overpotential",
                "X-averaged negative electrode reaction overpotential [V]",
                "V",
            ),
            (
                "diagnostic.positive-reaction-overpotential",
                "X-averaged positive electrode reaction overpotential [V]",
                "V",
            ),
        )
        for diagnostic_id, variable_name, native_unit in scalar_diagnostics:
            try:
                values = _scalar_series(solution, variable_name, times)
            except (KeyError, RuntimeError, ValueError):
                absent_diagnostics.add(diagnostic_id)
                continue
            diagnostics.append(
                _diagnostic(
                    diagnostic_id,
                    native_unit,
                    "source-volume-or-x-average",
                    values,
                )
            )
        field_diagnostics = (
            (
                "electrolyte-concentration",
                "Electrolyte concentration [mol.m-3]",
                "mol.m-3",
            ),
            (
                "negative-particle-surface-stoichiometry",
                "Negative particle surface stoichiometry",
                "1",
            ),
            (
                "positive-particle-surface-stoichiometry",
                "Positive particle surface stoichiometry",
                "1",
            ),
        )
        for token, variable_name, native_unit in field_diagnostics:
            try:
                values = _field_by_time(solution, variable_name, times)
            except (KeyError, RuntimeError, ValueError):
                absent_diagnostics.update(
                    (
                        f"diagnostic.{token}-minimum",
                        f"diagnostic.{token}-maximum",
                        f"diagnostic.{token}-contrast",
                    )
                )
                continue
            diagnostics.extend(
                (
                    _diagnostic(
                        f"diagnostic.{token}-minimum",
                        native_unit,
                        "spatial-minimum",
                        np.min(values, axis=0),
                    ),
                    _diagnostic(
                        f"diagnostic.{token}-maximum",
                        native_unit,
                        "spatial-maximum",
                        np.max(values, axis=0),
                    ),
                    _diagnostic(
                        f"diagnostic.{token}-contrast",
                        native_unit,
                        "spatial-maximum-minus-minimum",
                        np.max(values, axis=0) - np.min(values, axis=0),
                    ),
                )
            )

        checkpoint_values: list[_science_BatteryElectrothermalCheckpointState] = []
        for clock in (300, 450):
            checkpoint = checkpoints[clock]
            values = np.asarray(checkpoint.y, dtype=np.float64).reshape(-1)
            if not np.all(np.isfinite(values)):
                raise RuntimeError("battery electrothermal checkpoint state is nonfinite")
            layout_sha256 = _state_layout_sha256(checkpoint)
            checkpoint_values.append(
                _science_BatteryElectrothermalCheckpointState(
                    clock_s=clock,
                    state_y=tuple(_decimal(float(item)) for item in values),
                    state_layout_sha256=layout_sha256,
                )
            )
        checkpoint_records = tuple(checkpoint_values)
        state_length = len(checkpoint_records[0].state_y)
        if any(len(item.state_y) != state_length for item in checkpoint_records):
            raise RuntimeError("battery electrothermal state vector length changes by checkpoint")

        # Boundary samples can belong to the preceding source segment. Exact
        # realization is checked at strict segment-interior output clocks.
        for start, stop in zip(
            _science_BATTERY_ELECTROTHERMAL_BOUNDARIES_S[:-1],
            _science_BATTERY_ELECTROTHERMAL_BOUNDARIES_S[1:],
            strict=True,
        ):
            interior = (times > start) & (times < stop)
            if not np.any(interior):
                continue
            expected_current, expected_ambient = word.values_at(start)
            if not np.allclose(
                source_current[interior],
                float(expected_current),
                rtol=0,
                atol=1e-10,
            ) or not np.allclose(
                source_ambient[interior],
                float(unit.initial_temperature_k + expected_ambient),
                rtol=0,
                atol=1e-8,
            ):
                disposition = _science_BatteryElectrothermalEpisodeDisposition.DELIVERY_INVALID
                reasons.add("SOURCE_INPUT_REALIZATION_MISMATCH")
        if termination != "final time" or not math.isclose(
            float(times[-1]),
            _science_BATTERY_ELECTROTHERMAL_HORIZON_S,
            abs_tol=1e-8,
        ):
            disposition = _science_BatteryElectrothermalEpisodeDisposition.SIMULATOR_TERMINATED
            reasons.add("SIMULATOR_TERMINATED_BEFORE_HORIZON")
    except Exception as error:
        if times.size:
            disposition = _science_BatteryElectrothermalEpisodeDisposition.SCIENTIFIC_PARTIAL
        else:
            disposition = _science_BatteryElectrothermalEpisodeDisposition.TECHNICAL_OBSERVATION_FAILURE
        reasons.add(f"PYBAMM_{type(error).__name__.upper()}")
        termination = f"error:{type(error).__name__}"

    def encode(name: str) -> tuple[Decimal, ...]:
        return tuple(_decimal(float(item)) for item in arrays.get(name, ()))

    token = (
        f"{unit_id.removeprefix('unit.battery-electrothermal.')}."
        f"{denominator_id.removeprefix('denominator.pybamm.')}."
        f"{word_id.removeprefix('word.battery-electrothermal.')}.{episode_suffix}"
    )
    return _science_BatteryElectrothermalCapturedEpisode(
        episode_id=f"episode.battery-electrothermal.{token}",
        config=ObjectIdentity.from_record(config.config_id, config),
        unit=ObjectIdentity.from_record(unit.unit_id, unit),
        denominator=ObjectIdentity.from_record(
            denominator.denominator_id,
            denominator,
        ),
        word=ObjectIdentity.from_record(word.word_id, word),
        time_s=tuple(_decimal(float(item)) for item in times),
        discharge_capacity_ah=encode("capacity"),
        mean_temperature_k=encode("temperature"),
        maximum_temperature_k=encode("maximum_temperature"),
        terminal_voltage_v=encode("voltage"),
        source_current_a=encode("current"),
        source_ambient_temperature_k=encode("ambient"),
        diagnostics=tuple(sorted(diagnostics, key=lambda item: item.diagnostic_id)),
        absent_diagnostic_ids=tuple(sorted(absent_diagnostics)),
        temperature_field_shape=temperature_shape,
        temperature_field_k=tuple(_decimal(float(item)) for item in temperature_field.reshape(-1)),
        checkpoint_states=checkpoint_records,
        action_rows=_science_action_ledger(word),
        state_vector_length=state_length,
        termination=termination,
        disposition=disposition,
        reason_codes=tuple(sorted(reasons)),
        source_build_seconds=source_build_seconds,
        runtime_seconds=_decimal(time.monotonic() - started),
        outcome_access=config.outcome_access,
    )


def _fabricated_solution(
    pybamm: Any,
    template_state: Any,
    state_y: Sequence[Decimal],
    checkpoint_s: int,
) -> Any:
    values = np.asarray([float(item) for item in state_y], dtype=np.float64).reshape(-1, 1)
    return pybamm.Solution(
        [np.asarray([float(checkpoint_s)], dtype=np.float64)],
        [values],
        [template_state.all_models[-1]],
        [template_state.all_inputs[-1]],
        termination="final time",
        check_solution=False,
    )


def acquire_restart_result(
    *,
    config: _science_BatteryElectrothermalStageConfig,
    evaluation_episode: _science_BatteryElectrothermalCapturedEpisode,
    donor_episode: _science_BatteryElectrothermalCapturedEpisode,
    checkpoint_s: int,
    continuation_end_s: int,
    restart_suffix: str,
) -> _science_BatteryElectrothermalRestartResult:
    """Run actual, exact serialized-state, and reduced donor continuations."""

    validate_stable_id(restart_suffix, field_name="restart_suffix")
    started = time.monotonic()
    if (
        evaluation_episode.denominator.object_id != donor_episode.denominator.object_id
        or evaluation_episode.disposition is not _science_BatteryElectrothermalEpisodeDisposition.COMPLETE
        or donor_episode.disposition is not _science_BatteryElectrothermalEpisodeDisposition.COMPLETE
        or checkpoint_s not in {300, 450}
        or continuation_end_s - checkpoint_s != 300
    ):
        raise ValueError("battery electrothermal restart operands are incompatible")
    unit = next(item for item in config.units if item.unit_id == evaluation_episode.unit.object_id)
    denominator = next(
        item
        for item in config.denominators
        if item.denominator_id == evaluation_episode.denominator.object_id
    )
    word = next(item for item in config.words if item.word_id == evaluation_episode.word.object_id)
    exact_state = _science_checkpoint_state(evaluation_episode, checkpoint_s)
    donor_state = _science_checkpoint_state(donor_episode, checkpoint_s)
    if exact_state.state_layout_sha256 != donor_state.state_layout_sha256:
        raise ValueError("battery electrothermal donor state layout differs within a denominator")
    reasons: set[str] = set()
    exact_complete = reduced_complete = False
    clock = _sample_clock(
        denominator.view.nominal_output_interval_s,
        start=checkpoint_s,
        stop=continuation_end_s,
    )
    relative = clock - checkpoint_s
    values: dict[str, np.ndarray] = {}
    exact_errors: dict[str, Decimal | None] = {
        "capacity": None,
        "temperature": None,
        "maximum_temperature": None,
        "voltage": None,
    }
    reduced_errors = dict(exact_errors)
    reduced_operational_error = None
    try:
        pybamm, actual_simulation, checkpoints, _ = _step_schedule(
            unit=unit,
            denominator=denominator,
            word=word,
            stop_s=checkpoint_s,
        )
        prefix = checkpoints[checkpoint_s]
        actual_solution = actual_simulation.step(
            continuation_end_s - checkpoint_s,
            t_eval=relative,
            starting_solution=prefix,
            inputs=_inputs(unit, Decimal(0), Decimal(0)),
        )
        values["actual_capacity"] = _scalar_series(
            actual_solution,
            "Discharge capacity [A.h]",
            clock,
        )
        values["actual_temperature"] = _scalar_series(
            actual_solution,
            "Volume-averaged cell temperature [K]",
            clock,
        )
        values["actual_voltage"] = _scalar_series(
            actual_solution,
            "Terminal voltage [V]",
            clock,
        )
        values["actual_maximum_temperature"] = np.max(
            _field_by_time(actual_solution, "Cell temperature [K]", clock),
            axis=0,
        )

        _, exact_simulation = _runtime_objects(unit, denominator)
        exact_simulation.build(
            initial_soc=float(unit.initial_soc),
            inputs=_inputs(unit, Decimal(0), Decimal(0)),
        )
        exact_start = _fabricated_solution(
            pybamm,
            prefix,
            exact_state.state_y,
            checkpoint_s,
        )
        exact_solution = exact_simulation.step(
            continuation_end_s - checkpoint_s,
            t_eval=relative,
            starting_solution=exact_start,
            inputs=_inputs(unit, Decimal(0), Decimal(0)),
        )
        values["exact_capacity"] = _scalar_series(
            exact_solution,
            "Discharge capacity [A.h]",
            clock,
        )
        values["exact_temperature"] = _scalar_series(
            exact_solution,
            "Volume-averaged cell temperature [K]",
            clock,
        )
        values["exact_voltage"] = _scalar_series(
            exact_solution,
            "Terminal voltage [V]",
            clock,
        )
        values["exact_maximum_temperature"] = np.max(
            _field_by_time(exact_solution, "Cell temperature [K]", clock),
            axis=0,
        )
        exact_complete = str(exact_solution.termination) == "final time"

        _, reduced_simulation = _runtime_objects(unit, denominator)
        reduced_simulation.build(
            initial_soc=float(unit.initial_soc),
            inputs=_inputs(unit, Decimal(0), Decimal(0)),
        )
        reduced_start = _fabricated_solution(
            pybamm,
            prefix,
            donor_state.state_y,
            checkpoint_s,
        )
        reduced_solution = reduced_simulation.step(
            continuation_end_s - checkpoint_s,
            t_eval=relative,
            starting_solution=reduced_start,
            inputs=_inputs(unit, Decimal(0), Decimal(0)),
        )
        values["reduced_capacity"] = _scalar_series(
            reduced_solution,
            "Discharge capacity [A.h]",
            clock,
        )
        values["reduced_temperature"] = _scalar_series(
            reduced_solution,
            "Volume-averaged cell temperature [K]",
            clock,
        )
        values["reduced_voltage"] = _scalar_series(
            reduced_solution,
            "Terminal voltage [V]",
            clock,
        )
        values["reduced_maximum_temperature"] = np.max(
            _field_by_time(reduced_solution, "Cell temperature [K]", clock),
            axis=0,
        )
        reduced_complete = str(reduced_solution.termination) == "final time"

        for coordinate in (
            "capacity",
            "temperature",
            "maximum_temperature",
            "voltage",
        ):
            exact_errors[coordinate] = _decimal(
                float(
                    np.max(np.abs(values[f"exact_{coordinate}"] - values[f"actual_{coordinate}"]))
                )
            )
            reduced_errors[coordinate] = _decimal(
                float(
                    np.max(np.abs(values[f"reduced_{coordinate}"] - values[f"actual_{coordinate}"]))
                )
            )
        assert reduced_errors["capacity"] is not None
        assert reduced_errors["temperature"] is not None
        assert reduced_errors["voltage"] is not None
        reduced_operational_error = max(
            reduced_errors["capacity"] / Decimal("0.001"),
            reduced_errors["temperature"] / Decimal("0.005"),
            reduced_errors["voltage"] / Decimal("0.005"),
        )
    except Exception as error:
        reasons.add(f"RESTART_{type(error).__name__.upper()}")
    if not exact_complete:
        reasons.add("EXACT_RESTART_INCOMPLETE")
    if not reduced_complete:
        reasons.add("REDUCED_RESTART_INCOMPLETE")

    def encode(name: str) -> tuple[Decimal, ...]:
        return tuple(_decimal(float(item)) for item in values.get(name, ()))

    token = (
        f"{evaluation_episode.unit.object_id.removeprefix('unit.battery-electrothermal.')}."
        f"{denominator.denominator_id.removeprefix('denominator.pybamm.')}."
        f"{word.word_id.removeprefix('word.battery-electrothermal.')}.{checkpoint_s}.{restart_suffix}"
    )
    return _science_BatteryElectrothermalRestartResult(
        restart_id=f"restart.battery-electrothermal.{token}",
        config=ObjectIdentity.from_record(config.config_id, config),
        unit_id=unit.unit_id,
        denominator_id=denominator.denominator_id,
        history_word_id=word.word_id,
        checkpoint_s=checkpoint_s,
        continuation_end_s=continuation_end_s,
        donor_unit_id=donor_episode.unit.object_id,
        donor_word_id=donor_episode.word.object_id,
        time_s=tuple(_decimal(float(item)) for item in clock),
        actual_capacity_ah=encode("actual_capacity"),
        exact_capacity_ah=encode("exact_capacity"),
        reduced_capacity_ah=encode("reduced_capacity"),
        actual_temperature_k=encode("actual_temperature"),
        exact_temperature_k=encode("exact_temperature"),
        reduced_temperature_k=encode("reduced_temperature"),
        actual_maximum_temperature_k=encode("actual_maximum_temperature"),
        exact_maximum_temperature_k=encode("exact_maximum_temperature"),
        reduced_maximum_temperature_k=encode("reduced_maximum_temperature"),
        actual_voltage_v=encode("actual_voltage"),
        exact_voltage_v=encode("exact_voltage"),
        reduced_voltage_v=encode("reduced_voltage"),
        exact_capacity_error_ah=exact_errors["capacity"],
        exact_temperature_error_k=exact_errors["temperature"],
        exact_maximum_temperature_error_k=exact_errors["maximum_temperature"],
        exact_voltage_error_v=exact_errors["voltage"],
        reduced_capacity_error_ah=reduced_errors["capacity"],
        reduced_temperature_error_k=reduced_errors["temperature"],
        reduced_maximum_temperature_error_k=reduced_errors["maximum_temperature"],
        reduced_voltage_error_v=reduced_errors["voltage"],
        reduced_operational_error=reduced_operational_error,
        exact_restart_complete=exact_complete,
        reduced_restart_complete=reduced_complete,
        reason_codes=tuple(sorted(reasons)),
        runtime_seconds=_decimal(time.monotonic() - started),
        outcome_access=config.outcome_access,
    )
