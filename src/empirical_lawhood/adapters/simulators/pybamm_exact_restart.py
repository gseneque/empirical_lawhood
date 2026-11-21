"""Native acquisition and external-format binding for the domain science."""

from __future__ import annotations
from decimal import Decimal
from hashlib import sha256
import time
from typing import Any, Mapping, Sequence
import numpy as np
import empirical_lawhood.domains.battery.electrothermal_hierarchy as battery_electrothermal
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import canonical_json_bytes, validate_stable_id

from empirical_lawhood.domains.battery.exact_restart import (
    BATTERY_EXACT_RESTART_QUALIFICATION_ROUTE_PREFERENCE as _science_BATTERY_EXACT_RESTART_QUALIFICATION_ROUTE_PREFERENCE,
    BATTERY_EXACT_RESTART_SOURCE_VERSION as _science_BATTERY_EXACT_RESTART_SOURCE_VERSION,
    BatteryExactRestartCapture as _science_BatteryExactRestartCapture,
    BatteryExactRestartCaptureDisposition as _science_BatteryExactRestartCaptureDisposition,
    BatteryExactRestartCheckpointCapsule as _science_BatteryExactRestartCheckpointCapsule,
    BatteryExactRestartExecutionBinding as _science_BatteryExactRestartExecutionBinding,
    BatteryExactRestartHistory as _science_BatteryExactRestartHistory,
    BatteryExactRestartInputLedger as _science_BatteryExactRestartInputLedger,
    BatteryExactRestartPreparation as _science_BatteryExactRestartPreparation,
    BatteryExactRestartReceiverTrace as _science_BatteryExactRestartReceiverTrace,
    BatteryExactRestartRoute as _science_BatteryExactRestartRoute,
    BatteryExactRestartRouteDisposition as _science_BatteryExactRestartRouteDisposition,
    BatteryExactRestartRouteResult as _science_BatteryExactRestartRouteResult,
    BatteryExactRestartSourceAudit as _science_BatteryExactRestartSourceAudit,
    BatteryExactRestartStageConfig as _science_BatteryExactRestartStageConfig,
    _RouteResultCommon,
    _capsule_inputs,
    _decimal,
    _hex_values,
    _lookup,
    _numeric_payload_sha256,
    _sample_clock,
    _trace_errors,
    decode_hex as _science_decode_hex,
)

def _source_options(denominator: battery_electrothermal.BatteryElectrothermalDenominator) -> dict[str, str]:
    values = {
        "thermal": {
            battery_electrothermal.BatteryElectrothermalThermal.ISOTHERMAL: "isothermal",
            battery_electrothermal.BatteryElectrothermalThermal.LUMPED: "lumped",
            battery_electrothermal.BatteryElectrothermalThermal.X_FULL: "x-full",
        }[denominator.thermal],
        "cell geometry": "pouch",
    }
    if denominator.thermal is battery_electrothermal.BatteryElectrothermalThermal.ISOTHERMAL:
        values["calculate heat source for isothermal models"] = "true"
    return values


def _inputs(
    unit: _science_BatteryExactRestartPreparation,
    current_delta_a: Decimal,
    ambient_delta_k: Decimal,
) -> dict[str, float]:
    return {
        "Current function [A]": float(current_delta_a),
        "Ambient temperature [K]": float(unit.initial_temperature_k + ambient_delta_k),
    }


def _runtime_objects(
    unit: _science_BatteryExactRestartPreparation,
    denominator: battery_electrothermal.BatteryElectrothermalDenominator,
) -> tuple[Any, Any]:
    import pybamm  # type: ignore[import-untyped]

    if pybamm.__version__ != _science_BATTERY_EXACT_RESTART_SOURCE_VERSION:
        raise RuntimeError("installed PyBaMM differs from the battery exact restart source")
    model_class = (
        pybamm.lithium_ion.SPMe
        if denominator.model is battery_electrothermal.BatteryElectrothermalModel.SPME
        else pybamm.lithium_ion.DFN
    )
    model = model_class(options=_source_options(denominator))
    parameters = pybamm.ParameterValues(battery_electrothermal.BATTERY_ELECTROTHERMAL_PARAMETER_SET)
    parameters["Current function [A]"] = "[input]"
    parameters["Ambient temperature [K]"] = "[input]"
    parameters["Initial temperature [K]"] = float(unit.initial_temperature_k)
    if denominator.view.solver is battery_electrothermal.BatteryElectrothermalSolver.CASADI:
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


def _state_layout_sha256(model: Any) -> str:
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


def _model_fingerprint_sha256(
    denominator: battery_electrothermal.BatteryElectrothermalDenominator,
    model: Any,
) -> str:
    return sha256(
        canonical_json_bytes(
            {
                "denominator": denominator.fingerprint(),
                "len_alg": int(model.len_alg),
                "len_rhs": int(model.len_rhs),
                "name": str(model.name),
                "state_layout_sha256": _state_layout_sha256(model),
            }
        )
    ).hexdigest()


def _configuration_fingerprints(
    *,
    unit: _science_BatteryExactRestartPreparation,
    denominator: battery_electrothermal.BatteryElectrothermalDenominator,
    history: _science_BatteryExactRestartHistory,
) -> tuple[str, str, str, str, str, str]:
    """Fingerprint the finite build/clock/receiver specifications.

    The installed source digest lives in the source audit.  These hashes bind
    the deterministic parameter overrides and numerical build chart that,
    together with that source digest, produce the evaluated model.
    """

    parameter = sha256(
        canonical_json_bytes(
            {
                "ambient_parameter": "[input]",
                "current_parameter": "[input]",
                "initial_temperature_k_hex": float(unit.initial_temperature_k).hex(),
                "parameter_set": denominator.parameter_set,
                "source_version": denominator.source_version,
            }
        )
    ).hexdigest()
    options = sha256(canonical_json_bytes(_source_options(denominator))).hexdigest()
    geometry_mesh = sha256(
        canonical_json_bytes(
            {
                "cell_geometry": denominator.cell_geometry,
                "spatial_points": denominator.view.spatial_points,
                "var_pts": ("r_n", "r_p", "x_n", "x_p", "x_s"),
            }
        )
    ).hexdigest()
    solver = sha256(
        canonical_json_bytes(
            {
                "atol": denominator.view.atol,
                "mode": (
                    "safe" if denominator.view.solver is battery_electrothermal.BatteryElectrothermalSolver.CASADI else "source-default"
                ),
                "rtol": denominator.view.rtol,
                "solver": denominator.view.solver.value,
            }
        )
    ).hexdigest()
    clock = sha256(
        canonical_json_bytes(_hex_values(_sample_clock(denominator, history)))
    ).hexdigest()
    receiver = sha256(
        canonical_json_bytes(
            (
                ("Discharge capacity [A.h]", "scalar"),
                ("Volume-averaged cell temperature [K]", "scalar"),
                ("Cell temperature [K]", "spatial-maximum"),
                ("Terminal voltage [V]", "scalar"),
            )
        )
    ).hexdigest()
    return parameter, options, geometry_mesh, solver, clock, receiver


def _input_ledger(values: Mapping[str, float]) -> tuple[_science_BatteryExactRestartInputLedger, ...]:
    return tuple(
        _science_BatteryExactRestartInputLedger(
            input_name=name,
            requested_hex=float(value).hex(),
            accepted_hex=float(value).hex(),
            applied_hex=float(value).hex(),
            realized_hex=float(value).hex(),
        )
        for name, value in sorted(values.items())
    )


def _step_prefix(
    *,
    unit: _science_BatteryExactRestartPreparation,
    denominator: battery_electrothermal.BatteryElectrothermalDenominator,
    history: _science_BatteryExactRestartHistory,
) -> tuple[Any, Any, Any, Decimal]:
    started = time.monotonic()
    pybamm, simulation = _runtime_objects(unit, denominator)
    current, ambient = history.word.values_at(0)
    simulation.build(
        initial_soc=float(unit.initial_soc),
        inputs=_inputs(unit, current, ambient),
    )
    build_seconds = _decimal(time.monotonic() - started)
    interval = float(denominator.view.nominal_output_interval_s)
    prefix = None
    for start, stop in zip(battery_electrothermal.BATTERY_ELECTROTHERMAL_BOUNDARIES_S[:-1], battery_electrothermal.BATTERY_ELECTROTHERMAL_BOUNDARIES_S[1:], strict=True):
        if start >= history.checkpoint_s:
            break
        segment_stop = min(stop, history.checkpoint_s)
        current, ambient = history.word.values_at(start)
        duration = segment_stop - start
        relative = np.arange(0.0, duration + interval, interval, dtype=np.float64)
        relative[-1] = float(duration)
        simulation.step(
            duration,
            t_eval=np.unique(relative),
            inputs=_inputs(unit, current, ambient),
        )
        if segment_stop == history.checkpoint_s:
            prefix = simulation.solution.last_state
            break
    if prefix is None:
        raise RuntimeError("battery exact restart prefix did not reach its checkpoint")
    return pybamm, simulation, prefix, build_seconds


def _variable(solution: Any, name: str, times: np.ndarray) -> np.ndarray:
    values = np.asarray(solution[name](times), dtype=np.float64)
    if not np.all(np.isfinite(values)):
        raise RuntimeError(f"battery exact restart source variable {name!r} is nonfinite")
    return values


def _scalar_series(solution: Any, name: str, times: np.ndarray) -> np.ndarray:
    values = _variable(solution, name, times).reshape(-1)
    if values.size != times.size:
        raise RuntimeError(f"battery exact restart source variable {name!r} is not scalar by clock")
    return values


def _field_by_time(solution: Any, name: str, times: np.ndarray) -> np.ndarray:
    values = _variable(solution, name, times)
    if values.ndim == 1:
        if values.size != times.size:
            raise RuntimeError(f"battery exact restart source field {name!r} has invalid shape")
        return values.reshape(1, -1)
    if values.shape[-1] == times.size:
        return values.reshape(-1, times.size)
    if values.shape[0] == times.size:
        return np.moveaxis(values, 0, -1).reshape(-1, times.size)
    raise RuntimeError(f"battery exact restart source field {name!r} lacks a clock axis")


def _trace(solution: Any, clock: np.ndarray) -> _science_BatteryExactRestartReceiverTrace:
    return _science_BatteryExactRestartReceiverTrace(
        time_hex=_hex_values(clock),
        capacity_hex=_hex_values(_scalar_series(solution, "Discharge capacity [A.h]", clock)),
        mean_temperature_hex=_hex_values(
            _scalar_series(solution, "Volume-averaged cell temperature [K]", clock)
        ),
        maximum_temperature_hex=_hex_values(
            np.max(_field_by_time(solution, "Cell temperature [K]", clock), axis=0)
        ),
        terminal_voltage_hex=_hex_values(_scalar_series(solution, "Terminal voltage [V]", clock)),
        termination=str(solution.termination),
        complete=str(solution.termination) == "final time",
    )


def verify_denominator_builds(
    *,
    unit: _science_BatteryExactRestartPreparation,
    denominators: Sequence[battery_electrothermal.BatteryElectrothermalDenominator],
) -> tuple[str, ...]:
    """Build every supplied denominator and verify required source operands."""

    built = []
    required = {
        "Discharge capacity [A.h]",
        "Volume-averaged cell temperature [K]",
        "Cell temperature [K]",
        "Terminal voltage [V]",
    }
    for denominator in denominators:
        _, simulation = _runtime_objects(unit, denominator)
        simulation.build(
            initial_soc=float(unit.initial_soc),
            inputs=_inputs(unit, Decimal(0), Decimal(0)),
        )
        model = simulation.built_model
        if (
            not required.issubset(model.variables)
            or int(model.len_rhs) + int(model.len_alg) <= 0
            or not _state_layout_sha256(model)
        ):
            raise RuntimeError(f"battery exact restart source build is incomplete: {denominator.denominator_id}")
        built.append(denominator.denominator_id)
    return tuple(sorted(built))


def capture_reference(
    *,
    config: _science_BatteryExactRestartStageConfig,
    unit_id: str,
    denominator_id: str,
    history_id: str,
    source_audit: _science_BatteryExactRestartSourceAudit,
    execution_binding: _science_BatteryExactRestartExecutionBinding,
) -> _science_BatteryExactRestartCapture:
    """Capture a lossless checkpoint and native same-object hold continuation."""

    started = time.monotonic()
    build_seconds = Decimal(0)
    unit, denominator, history = _lookup(
        config,
        unit_id=unit_id,
        denominator_id=denominator_id,
        history_id=history_id,
    )
    token = (
        f"{unit.unit_id.removeprefix('unit.battery-exact-restart.')}."
        f"{denominator.denominator_id.removeprefix('denominator.pybamm.')}."
        f"{history.history_id.removeprefix('history.battery-exact-restart.')}"
    )
    capture_id = f"capture.battery-exact-restart.{token}"
    config_identity = ObjectIdentity.from_record(config.config_id, config)
    if (
        execution_binding.config != config_identity
        or execution_binding.source_audit
        != ObjectIdentity.from_record(source_audit.audit_id, source_audit)
        or execution_binding.outcome_access is not config.outcome_access
    ):
        raise ValueError("battery exact restart capture execution binding differs from the config")
    try:
        _, simulation, prefix, build_seconds = _step_prefix(
            unit=unit,
            denominator=denominator,
            history=history,
        )
        model = prefix.all_models[-1]
        state = np.asarray(prefix.all_ys[0], dtype=np.float64).reshape(-1)
        derivative = (
            np.asarray(prefix.all_yps[0], dtype=np.float64).reshape(-1)
            if prefix.all_yps is not None
            else np.asarray([], dtype=np.float64)
        )
        inputs = tuple(
            sorted(
                (
                    str(name),
                    float(np.asarray(value, dtype=np.float64).reshape(-1)[0]).hex(),
                )
                for name, value in prefix.all_inputs[-1].items()
            )
        )
        state_hex = _hex_values(state)
        derivative_hex = _hex_values(derivative)
        layout = _state_layout_sha256(model)
        (
            parameter_fingerprint,
            options_fingerprint,
            geometry_mesh_fingerprint,
            solver_fingerprint,
            clock_fingerprint,
            receiver_fingerprint,
        ) = _configuration_fingerprints(
            unit=unit,
            denominator=denominator,
            history=history,
        )
        checkpoint_values = {name: float.fromhex(value) for name, value in inputs}
        continuation_values = _inputs(unit, Decimal(0), Decimal(0))
        capsule = _science_BatteryExactRestartCheckpointCapsule(
            capsule_id=f"capsule.battery-exact-restart.{token}",
            execution_binding=execution_binding,
            source_audit=ObjectIdentity.from_record(
                source_audit.audit_id,
                source_audit,
            ),
            unit=ObjectIdentity.from_record(unit.unit_id, unit),
            denominator=ObjectIdentity.from_record(
                denominator.denominator_id,
                denominator,
            ),
            history=ObjectIdentity.from_record(history.history_id, history),
            checkpoint_s=history.checkpoint_s,
            source_version=_science_BATTERY_EXACT_RESTART_SOURCE_VERSION,
            distribution_record_sha256=source_audit.distribution_record_sha256,
            python_version=source_audit.python_version,
            platform_identity=source_audit.platform_identity,
            numpy_version=source_audit.numpy_version,
            casadi_version=source_audit.casadi_version,
            parameter_set=denominator.parameter_set,
            evaluated_parameter_fingerprint_sha256=parameter_fingerprint,
            model_fingerprint_sha256=_model_fingerprint_sha256(denominator, model),
            model_options_fingerprint_sha256=options_fingerprint,
            geometry_mesh_discretization_fingerprint_sha256=(geometry_mesh_fingerprint),
            solver_fingerprint_sha256=solver_fingerprint,
            state_layout_sha256=layout,
            observation_clock_fingerprint_sha256=clock_fingerprint,
            receiver_schema_fingerprint_sha256=receiver_fingerprint,
            state_vector_length=len(state_hex),
            differential_state_length=int(model.len_rhs),
            algebraic_state_length=int(model.len_alg),
            state_hex=state_hex,
            derivative_hex=derivative_hex,
            source_input_hex=inputs,
            checkpoint_input_ledger=_input_ledger(checkpoint_values),
            continuation_input_ledger=_input_ledger(continuation_values),
            continuation_time_origin_s=history.checkpoint_s,
            continuation_end_s=history.continuation_end_s,
            prefix_termination=str(prefix.termination),
            prefix_valid=bool(
                str(prefix.termination) == "final time"
                and np.all(np.isfinite(state))
                and (not derivative.size or np.all(np.isfinite(derivative)))
            ),
            route_compatible_ids=_science_BATTERY_EXACT_RESTART_QUALIFICATION_ROUTE_PREFERENCE,
            numeric_payload_sha256=_numeric_payload_sha256(
                state_hex,
                derivative_hex,
                inputs,
            ),
            bit_exact_roundtrip=tuple(_hex_values(_science_decode_hex(state_hex))) == state_hex,
            outcome_access=config.outcome_access,
        )
        clock = _sample_clock(denominator, history)
        relative = clock - history.checkpoint_s
        native_solution = simulation.step(
            history.continuation_end_s - history.checkpoint_s,
            t_eval=relative,
            starting_solution=prefix,
            inputs=_inputs(unit, Decimal(0), Decimal(0)),
        )
        native_trace = _trace(native_solution, clock)
        if not native_trace.complete:
            raise RuntimeError(f"native termination: {native_trace.termination}")
        return _science_BatteryExactRestartCapture(
            capture_id=capture_id,
            config=config_identity,
            unit_id=unit_id,
            denominator_id=denominator_id,
            history_id=history_id,
            capsule=capsule,
            native_trace=native_trace,
            disposition=_science_BatteryExactRestartCaptureDisposition.COMPLETE,
            reason_codes=(),
            source_build_seconds=build_seconds,
            runtime_seconds=_decimal(time.monotonic() - started),
            outcome_access=config.outcome_access,
        )
    except Exception as error:
        return _science_BatteryExactRestartCapture(
            capture_id=capture_id,
            config=config_identity,
            unit_id=unit_id,
            denominator_id=denominator_id,
            history_id=history_id,
            capsule=None,
            native_trace=None,
            disposition=_science_BatteryExactRestartCaptureDisposition.SOURCE_DENOMINATOR_FAILURE,
            reason_codes=(f"CAPTURE_{type(error).__name__.upper()}",),
            source_build_seconds=build_seconds,
            runtime_seconds=_decimal(time.monotonic() - started),
            outcome_access=config.outcome_access,
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


def _preconsistent_state(
    *,
    unit: _science_BatteryExactRestartPreparation,
    denominator: battery_electrothermal.BatteryElectrothermalDenominator,
    checkpoint_s: int,
    raw_state: np.ndarray,
) -> tuple[np.ndarray, Decimal, Decimal | None, Decimal | None]:
    _, audit_simulation = _runtime_objects(unit, denominator)
    hold_inputs = _inputs(unit, Decimal(0), Decimal(0))
    audit_simulation.build(
        initial_soc=float(unit.initial_soc),
        inputs=hold_inputs,
    )
    model = audit_simulation.built_model
    solver = audit_simulation.solver
    if int(model.len_alg) == 0:
        return raw_state.copy(), Decimal(0), Decimal(0), Decimal(0)
    solver.set_up(model, hold_inputs)
    model.y0_list = [raw_state.reshape(-1, 1)]
    time_value = float(np.nextafter(float(checkpoint_s), np.inf))

    def residual(values: np.ndarray) -> Decimal | None:
        try:
            evaluated = np.asarray(
                model.algebraic_eval(time_value, values, hold_inputs),
                dtype=np.float64,
            )
            if evaluated.size == 0:
                return Decimal(0)
            return _decimal(float(np.max(np.abs(evaluated))))
        except Exception:
            return None

    pre_residual = residual(raw_state)
    consistent = np.asarray(
        solver.calculate_consistent_state(model, time_value, [hold_inputs])[0],
        dtype=np.float64,
    ).reshape(-1)
    post_residual = residual(consistent)
    correction = _decimal(float(np.max(np.abs(consistent - raw_state))))
    return consistent, correction, pre_residual, post_residual


def acquire_route_result(
    *,
    config: _science_BatteryExactRestartStageConfig,
    capture: _science_BatteryExactRestartCapture,
    route: _science_BatteryExactRestartRoute,
    source_audit: _science_BatteryExactRestartSourceAudit,
    execution_binding: _science_BatteryExactRestartExecutionBinding,
    fresh_process_isolation: bool,
    result_suffix: str = "primary",
) -> _science_BatteryExactRestartRouteResult:
    """Reconstruct one persisted checkpoint through one predeclared route."""

    if route is _science_BatteryExactRestartRoute.NATIVE_SAME_OBJECT:
        raise ValueError("Native continuation is acquired only by capture_reference")
    if route not in config.routes:
        raise ValueError("battery exact restart route leaves the issued config")
    validate_stable_id(result_suffix, field_name="result_suffix")
    started = time.monotonic()
    common: _RouteResultCommon = {
        "result_id": (
            f"route-result.battery-exact-restart."
            f"{capture.capture_id.removeprefix('capture.battery-exact-restart.')}."
            f"{route.name.lower()}.{result_suffix}"
        ),
        "config": ObjectIdentity.from_record(config.config_id, config),
        "capture": ObjectIdentity.from_record(capture.capture_id, capture),
        "unit_id": capture.unit_id,
        "denominator_id": capture.denominator_id,
        "history_id": capture.history_id,
        "route": route,
        "outcome_access": config.outcome_access,
    }
    if (
        capture.disposition is not _science_BatteryExactRestartCaptureDisposition.COMPLETE
        or capture.capsule is None
        or capture.native_trace is None
    ):
        return _science_BatteryExactRestartRouteResult(
            **common,
            trace=None,
            capacity_error_ah=None,
            mean_temperature_error_k=None,
            maximum_temperature_error_k=None,
            terminal_voltage_error_v=None,
            first_sample_max_normalized_error=None,
            preconsistent_correction_max_abs=None,
            pre_algebraic_residual_max_abs=None,
            post_algebraic_residual_max_abs=None,
            capsule_bit_exact=False,
            fresh_process_isolation=fresh_process_isolation,
            receiver_closed=False,
            disposition=_science_BatteryExactRestartRouteDisposition.SOURCE_ROUTE_FAILURE,
            reason_codes=("CAPTURE_NOT_COMPLETE",),
            runtime_seconds=_decimal(time.monotonic() - started),
        )
    capsule = capture.capsule
    unit, denominator, history = _lookup(
        config,
        unit_id=capture.unit_id,
        denominator_id=capture.denominator_id,
        history_id=capture.history_id,
    )
    if (
        capture.config != ObjectIdentity.from_record(config.config_id, config)
        or capsule.execution_binding != execution_binding
        or execution_binding.config != ObjectIdentity.from_record(config.config_id, config)
        or capsule.source_audit != ObjectIdentity.from_record(source_audit.audit_id, source_audit)
        or capsule.distribution_record_sha256 != source_audit.distribution_record_sha256
        or capsule.python_version != source_audit.python_version
        or capsule.platform_identity != source_audit.platform_identity
        or capsule.numpy_version != source_audit.numpy_version
        or capsule.casadi_version != source_audit.casadi_version
        or capsule.denominator.object_id != denominator.denominator_id
        or capsule.unit.object_id != unit.unit_id
        or capsule.history.object_id != history.history_id
    ):
        return _science_BatteryExactRestartRouteResult(
            **common,
            trace=None,
            capacity_error_ah=None,
            mean_temperature_error_k=None,
            maximum_temperature_error_k=None,
            terminal_voltage_error_v=None,
            first_sample_max_normalized_error=None,
            preconsistent_correction_max_abs=None,
            pre_algebraic_residual_max_abs=None,
            post_algebraic_residual_max_abs=None,
            capsule_bit_exact=False,
            fresh_process_isolation=fresh_process_isolation,
            receiver_closed=False,
            disposition=_science_BatteryExactRestartRouteDisposition.UNEVALUABLE_IDENTITY,
            reason_codes=("CAPSULE_IDENTITY_MISMATCH",),
            runtime_seconds=_decimal(time.monotonic() - started),
        )
    correction = pre_residual = post_residual = None
    try:
        raw_state = _science_decode_hex(capsule.state_hex)
        bit_exact = _hex_values(raw_state) == capsule.state_hex
        if (
            not bit_exact
            or _numeric_payload_sha256(
                capsule.state_hex,
                capsule.derivative_hex,
                capsule.source_input_hex,
            )
            != capsule.numeric_payload_sha256
        ):
            raise ValueError("capsule round trip changed")
        pybamm, target_simulation = _runtime_objects(unit, denominator)
        hold_inputs = _inputs(unit, Decimal(0), Decimal(0))
        target_simulation.build(
            initial_soc=float(unit.initial_soc),
            inputs=hold_inputs,
        )
        target_model = target_simulation.built_model
        (
            parameter_fingerprint,
            options_fingerprint,
            geometry_mesh_fingerprint,
            solver_fingerprint,
            clock_fingerprint,
            receiver_fingerprint,
        ) = _configuration_fingerprints(
            unit=unit,
            denominator=denominator,
            history=history,
        )
        if (
            capsule.model_fingerprint_sha256 != _model_fingerprint_sha256(denominator, target_model)
            or capsule.state_layout_sha256 != _state_layout_sha256(target_model)
            or capsule.evaluated_parameter_fingerprint_sha256 != parameter_fingerprint
            or capsule.model_options_fingerprint_sha256 != options_fingerprint
            or capsule.geometry_mesh_discretization_fingerprint_sha256 != geometry_mesh_fingerprint
            or capsule.solver_fingerprint_sha256 != solver_fingerprint
            or capsule.observation_clock_fingerprint_sha256 != clock_fingerprint
            or capsule.receiver_schema_fingerprint_sha256 != receiver_fingerprint
            or capsule.checkpoint_input_ledger != _input_ledger(_capsule_inputs(capsule))
            or capsule.continuation_input_ledger != _input_ledger(hold_inputs)
        ):
            raise ValueError("capsule rebuild identity changed")
        state = raw_state
        start_model = target_model
        start_inputs: Mapping[str, float] = _capsule_inputs(capsule)
        if route in {
            _science_BatteryExactRestartRoute.DECIMAL15_LIVE_PREFIX_MAP,
            _science_BatteryExactRestartRoute.LOSSLESS_LIVE_PREFIX_MAP,
        }:
            _, _, prefix, _ = _step_prefix(
                unit=unit,
                denominator=denominator,
                history=history,
            )
            start_model = prefix.all_models[-1]
            start_inputs = {
                name: float(np.asarray(value, dtype=np.float64).reshape(-1)[0])
                for name, value in prefix.all_inputs[-1].items()
            }
            if route is _science_BatteryExactRestartRoute.DECIMAL15_LIVE_PREFIX_MAP:
                state = np.asarray(
                    [float(f"{item:.15g}") for item in raw_state],
                    dtype=np.float64,
                )
        elif route is _science_BatteryExactRestartRoute.LOSSLESS_PUBLIC_MAP:
            _, source_simulation = _runtime_objects(unit, denominator)
            source_simulation.build(
                initial_soc=float(unit.initial_soc),
                inputs=_capsule_inputs(capsule),
            )
            start_model = source_simulation.built_model
        elif route is _science_BatteryExactRestartRoute.LOSSLESS_PRECONSISTENT:
            state, correction, pre_residual, post_residual = _preconsistent_state(
                unit=unit,
                denominator=denominator,
                checkpoint_s=history.checkpoint_s,
                raw_state=raw_state,
            )
        elif route is not _science_BatteryExactRestartRoute.LOSSLESS_TARGET_DIRECT:
            raise ValueError("unsupported battery exact restart route")
        start = _starting_solution(
            pybamm,
            checkpoint_s=history.checkpoint_s,
            state=state,
            model=start_model,
            inputs=start_inputs,
        )
        clock = _sample_clock(denominator, history)
        solution = target_simulation.step(
            history.continuation_end_s - history.checkpoint_s,
            t_eval=clock - history.checkpoint_s,
            starting_solution=start,
            inputs=hold_inputs,
        )
        trace = _trace(solution, clock)
        if not trace.complete:
            raise RuntimeError(f"route termination: {trace.termination}")
        errors, first_error, closed = _trace_errors(
            trace,
            capture.native_trace,
            config.tolerance,
        )
        return _science_BatteryExactRestartRouteResult(
            **common,
            trace=trace,
            capacity_error_ah=errors[0],
            mean_temperature_error_k=errors[1],
            maximum_temperature_error_k=errors[2],
            terminal_voltage_error_v=errors[3],
            first_sample_max_normalized_error=first_error,
            preconsistent_correction_max_abs=correction,
            pre_algebraic_residual_max_abs=pre_residual,
            post_algebraic_residual_max_abs=post_residual,
            capsule_bit_exact=bit_exact,
            fresh_process_isolation=fresh_process_isolation,
            receiver_closed=closed,
            disposition=(
                _science_BatteryExactRestartRouteDisposition.COMPLETE if closed else _science_BatteryExactRestartRouteDisposition.RECEIVER_OPPOSED
            ),
            reason_codes=(),
            runtime_seconds=_decimal(time.monotonic() - started),
        )
    except Exception as error:
        return _science_BatteryExactRestartRouteResult(
            **common,
            trace=None,
            capacity_error_ah=None,
            mean_temperature_error_k=None,
            maximum_temperature_error_k=None,
            terminal_voltage_error_v=None,
            first_sample_max_normalized_error=None,
            preconsistent_correction_max_abs=correction,
            pre_algebraic_residual_max_abs=pre_residual,
            post_algebraic_residual_max_abs=post_residual,
            capsule_bit_exact=False,
            fresh_process_isolation=fresh_process_isolation,
            receiver_closed=False,
            disposition=_science_BatteryExactRestartRouteDisposition.SOURCE_ROUTE_FAILURE,
            reason_codes=(f"ROUTE_{type(error).__name__.upper()}",),
            runtime_seconds=_decimal(time.monotonic() - started),
        )
