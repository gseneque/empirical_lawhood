# SPDX-License-Identifier: MPL-2.0
"""Selected native conditional forecasts; called only by the registered runner."""

from dataclasses import replace
from contextlib import contextmanager
from decimal import Decimal
from functools import wraps
from hashlib import sha256
import json
import os
from pathlib import Path
import resource
import time
import warnings

from .contracts import (
    BatteryInquiryDelivery,
    BatteryInquiryChargingAttempt,
    BatteryInquiryInitializerAttempt,
    BatteryInquiryTrace,
    BatteryInquiryTransition,
    CONTROL_RULE,
    MAX_MODEL_CLOCK,
    REQUIRED_EVENT_NAMES,
    SOURCE_MEMBERS,
    SOURCE_VERSION,
    TARGET_CHARGE,
    TARGET_EVENT as TARGET_EVENT,
    TIER_EVENT,
    TIER_TEMPERATURE,
)

D = Decimal
EVENT_NAMES = REQUIRED_EVENT_NAMES

ACTIVE_CURRENT_INPUT = "Inquiry active charging magnitude [A]"
TIER_THRESHOLD_INPUT = "Inquiry tier threshold [K]"
TIER_DIRECTION_INPUT = "Inquiry tier direction"


def hybrid_inputs(config, regime):
    epsilon = config.localization_epsilon_k
    return {
        ACTIVE_CURRENT_INPUT: D("1.455") if regime == "LOW" else D("3.395"),
        TIER_THRESHOLD_INPUT: TIER_TEMPERATURE
        + (epsilon if regime == "LOW" else epsilon / D(2)),
        TIER_DIRECTION_INPUT: D(-1) if regime == "LOW" else D(1),
    }


def project_hybrid_run(attempts, receiver_blocks, failure):
    """Project retained native blocks without inventing absent delivery."""
    flattened = []
    for block_clocks, values, regime in receiver_blocks:
        for index, clock in enumerate(block_clocks):
            if not flattened or clock > flattened[-1][0]:
                flattened.append(
                    (clock, tuple(values[column][index] for column in range(5)), regime)
                )
    clocks = tuple(row[0] for row in flattened)
    columns = tuple(tuple(row[1][column] for row in flattened) for column in range(5))
    regimes = tuple(row[2] for row in flattened)
    modes = tuple(
        "CV"
        if abs(v - D("4.2")) <= D("0.001")
        and abs(i) < (D("1.455") if regime == "LOW" else D("3.395")) - D("1e-6")
        else "CC"
        if abs(abs(i) - (D("1.455") if regime == "LOW" else D("3.395"))) <= D("1e-6")
        else "UNRESOLVED"
        for i, v, regime in zip(columns[0], columns[1], regimes, strict=True)
    )
    termination = (
        attempts[-1].termination if attempts else "native-no-charging-subsolve"
    )
    disposition = (
        "TARGET_REACHED" if TARGET_EVENT in termination else "SERVICE_TERMINATED"
    )
    error_type = error_message = None
    if failure is not None:
        disposition, (error_type, error_message) = "TECHNICAL_FAILURE", failure
    return (
        clocks,
        columns,
        modes,
        regimes,
        termination,
        disposition,
        error_type,
        error_message,
    )


def run_hybrid_segments(config, execute, attempts, transitions):
    """Continue one forecast only at an actual temperature root.

    ``execute`` records one real backend return/error and returns its opaque
    native solution. Pure mock callbacks test dispatch without importing native
    packages. There is no attempt/segment count or elapsed-time stop.
    """
    epsilon = config.localization_epsilon_k
    regime = (
        "HIGH" if config.initial_temperature_k >= TIER_TEMPERATURE + epsilon else "LOW"
    )
    start, previous = D(0), None
    pending = None
    while start < MAX_MODEL_CLOCK:
        row, previous = execute(len(attempts) + 1, regime, start, previous)
        attempts.append(row)
        if pending is not None:
            threshold, before = pending
            transitions.append(
                BatteryInquiryTransition(
                    len(transitions) + 1,
                    before.attempt_index,
                    row.attempt_index,
                    before.regime,
                    row.regime,
                    TIER_EVENT,
                    threshold,
                    before.native_times_s[-1],
                    before.end_receivers,
                    before.end_differential_state,
                    row.native_times_s[0] if row.start_receivers else None,
                    row.start_receivers,
                    row.start_differential_state if row.start_receivers else (),
                )
            )
            pending = None
        if row.disposition == "TECHNICAL_FAILURE":
            return row.error_type, row.error_message
        if not row.native_times_s or row.native_times_s[-1] <= start:
            return (
                "NativeNumericalNoProgress",
                "native charging subsolve returned without advancing its requested model clock",
            )
        if TIER_EVENT not in row.termination:
            return None
        root_temperature = row.end_receivers[2]
        threshold = hybrid_inputs(config, regime)[TIER_THRESHOLD_INPUT]
        # This is a numerical root-integrity test, not a physical accuracy
        # certificate. In particular HIGH is never admitted at exactly25C.
        if root_temperature <= TIER_TEMPERATURE or abs(
            root_temperature - threshold
        ) > epsilon / D("1000000"):
            return (
                "NativeTierRootUnresolved",
                "native temperature root is outside its predeclared one-sided localization/roundoff allowance",
            )
        pending = threshold, row
        start = row.native_times_s[-1]
        regime = "HIGH" if regime == "LOW" else "LOW"
    return None


def _decimal(value):
    return D(str(float(value)))


def differential_state_endpoints(solution, differential_state_count):
    """Read exact full-state boundary columns without concatenating the trajectory.

    Selected full-state PyBaMM first_state/last_state use these exact all_ys
    boundary slices. Read them directly so their cached sub-solution backrefs
    do not retain the full trajectory. No native clock/receiver is changed.
    """
    import numpy as np

    if type(differential_state_count) is not int or differential_state_count < 1:
        raise ValueError("differential-state count must be a positive integer")
    if solution.variables_returned or not solution.all_ys:
        raise ValueError("native endpoint requires the actual full-state solution")
    endpoints = []
    for boundary in (solution.all_ys[0][:, :1], solution.all_ys[-1][:, -1:]):
        state = np.asarray(boundary, dtype=float)
        if (
            state.ndim != 2
            or state.shape[1] != 1
            or state.shape[0] < differential_state_count
        ):
            raise ValueError(
                "native endpoint omits its complete differential-state column"
            )
        endpoints.append(
            tuple(_decimal(value) for value in state[:differential_state_count, 0])
        )
    return tuple(endpoints)


def detached_terminal_solution(solution):
    """Own the complete terminal state without owning its native trajectory.

    Matches selected PyBaMM ``Solution.last_state`` state/sensitivity slicing,
    copying every array without its cached boundary/sub-solution backrefs.
    Share only the processed model identity required by BaseSolver.step.
    Call after all native knots, receivers and endpoint metadata are retained.
    This is continuation custody, never an additional solve.
    """
    from copy import deepcopy
    import numpy as np
    import pybamm

    if not isinstance(solution, pybamm.Solution) or solution.variables_returned:
        raise ValueError("detached continuation requires a full native Solution")
    if not solution.all_ts or not solution.all_ys or not solution.all_models:
        raise ValueError("detached continuation lacks actual terminal state")
    model = solution.all_models[-1]
    n_states = model.len_rhs_and_alg
    states = np.array(solution.all_ys[-1][:, -1:], copy=True)
    clocks = np.array(solution.all_ts[-1][-1:], copy=True)
    if states.ndim != 2 or states.shape != (n_states, 1) or clocks.shape != (1,):
        raise ValueError(
            "detached continuation changes complete RHS/algebraic dimensions"
        )
    derivatives = None
    if solution.all_yps is not None:
        derivatives = np.array(solution.all_yps[-1][:, -1:], copy=True)
        if derivatives.shape != states.shape:
            raise ValueError("detached continuation changes full native derivative")
    sensitivities = {}
    for name, blocks in solution._all_sensitivities.items():
        values = np.array(blocks[-1][-n_states:, :], copy=True)
        if values.ndim != 2 or values.shape[0] != n_states:
            raise ValueError(
                "detached continuation changes complete terminal sensitivities"
            )
        sensitivities[name] = values
    terminal = pybamm.Solution(
        clocks,
        states,
        model,
        deepcopy(solution.all_inputs[-1]),
        t_event=deepcopy(solution.t_event),
        y_event=deepcopy(solution.y_event),
        termination=solution.termination,
        all_sensitivities=sensitivities,
        all_yps=derivatives,
        options=deepcopy(solution.user_options),
    )
    terminal.closest_event_idx = deepcopy(solution.closest_event_idx)
    terminal.initial_start_time = deepcopy(solution.initial_start_time)
    for name in ("solve_time", "integration_time", "set_up_time"):
        setattr(terminal, name, getattr(solution, name))
    return terminal


def guarded_magnitude(temperature_k):
    """The independent evaluator uses the exact source boundary, including25C."""
    return D("3.395") if temperature_k > D("298.15") else D("1.455")


@contextmanager
def observe_initial_solver_calls(base_solver, attempts):
    """Meter each SOH backend solve without changing its native fallback policy.

    The selected worker has one numerical thread. The observer covers initial
    state preparation only and restores the original method on every exit.
    CompositeSolver dispatches its actual subsolver calls through this boundary;
    its dispatcher is not counted again as another numerical solve.
    """
    original = base_solver.solve

    @wraps(original)
    def observed(solver, model, *args, **kwargs):
        start_wall, start_cpu = time.perf_counter(), time.process_time()
        expressions = {
            name: sorted(
                (str(variable), str(expression))
                for variable, expression in getattr(model, name).items()
            )
            for name in ("algebraic", "initial_conditions")
        }
        model_sha = sha256(
            json.dumps(expressions, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        config_json = json.dumps(
            solver.to_config(), sort_keys=True, separators=(",", ":"), allow_nan=False
        )
        error_type = error_message = None
        disposition = "RETURNED"
        try:
            return original(solver, model, *args, **kwargs)
        except Exception as error:
            disposition = "TECHNICAL_FAILURE"
            error_type, error_message = type(error).__name__, str(error)
            raise
        finally:
            attempts.append(
                BatteryInquiryInitializerAttempt(
                    len(attempts) + 1,
                    type(solver).__name__,
                    solver.name,
                    config_json,
                    model.name,
                    model_sha,
                    disposition,
                    error_type,
                    error_message,
                    _decimal(time.process_time() - start_cpu),
                    _decimal(time.perf_counter() - start_wall),
                )
            )

    base_solver.solve = observed
    try:
        yield
    finally:
        base_solver.solve = original


def acquire(config):
    """Original1.1 entry: preserve its exact mesh/tolerances and record types."""
    refined = config.model_view == "oregan-dfn-refined"
    return acquire_with_numerics(
        config,
        electrode_points=60 if refined else 30,
        particle_points=80 if refined else 40,
        rtol=D("1e-9") if refined else D("1e-7"),
        atol=D("1e-10") if refined else D("1e-8"),
        trace_factory=BatteryInquiryTrace,
        charging_attempt_factory=BatteryInquiryChargingAttempt,
    )


def acquire_with_numerics(
    config,
    *,
    electrode_points,
    particle_points,
    rtol,
    atol,
    trace_factory,
    charging_attempt_factory,
    additional_source_members=(),
):
    """Retain one source-bound native attempt, its receivers and actual costs."""
    start_wall, start_cpu = time.perf_counter(), time.process_time()
    implementation = sha256(Path(__file__).read_bytes()).hexdigest()
    delivery = BatteryInquiryDelivery(
        CONTROL_RULE,
        D("4.2"),
        None,
        config.chamber_temperature_k,
        None,
        D(0),
        None,
        "",
        "",
        "",
        "",
        "",
        None,
        None,
        None,
    )
    clocks = columns = modes = ()
    event_names = processed_events = ()
    termination, disposition, error_type, error_message = (
        "native-not-built",
        "TECHNICAL_FAILURE",
        None,
        None,
    )
    charging_attempts, transitions, temperature_regimes = [], [], ()
    initializer_attempts = []
    # Native imports, model construction and solve are deliberately runtime-only.
    os.environ["PYBAMM_DISABLE_TELEMETRY"] = "true"
    try:
        import numpy as np
        import pybamm

        if pybamm.__version__ != SOURCE_VERSION:
            raise ValueError("installed PyBaMM source version differs")
        root = Path(pybamm.__file__).parent
        for member, expected in (*SOURCE_MEMBERS, *additional_source_members):
            if sha256((root / member).read_bytes()).hexdigest() != expected:
                raise ValueError(
                    f"installed native scientific source differs: {member}"
                )
        if (
            pybamm.settings.min_max_mode != "exact"
            or pybamm.settings.heaviside_smoothing != "exact"
        ):
            raise ValueError(
                "native exact complementarity/temperature-tier semantics differ"
            )

        def control(variables):
            eligible = pybamm.InputParameter(ACTIVE_CURRENT_INPUT)
            voltage_slack = (
                pybamm.Scalar(4.2) - variables["Voltage [V]"]
            ) / pybamm.Scalar(1)
            current_slack = (variables["Current [A]"] + eligible) / pybamm.Scalar(1)
            return pybamm.minimum(voltage_slack, current_slack)

        options = {
            "thermal": "lumped",
            "cell geometry": "arbitrary",
            "dimensionality": 0,
            "surface temperature": "ambient",
            "contact resistance": "false",
            "use lumped thermal capacity": "false",
            "operating mode": control,
        }
        constructor = (
            pybamm.lithium_ion.DFN
            if "dfn" in config.model_view
            else pybamm.lithium_ion.SPMe
        )
        model = constructor(options=options)
        temperature = model.variables["Volume-averaged cell temperature [K]"]
        voltage = model.variables["Voltage [V]"]
        current = model.variables["Current [A]"]
        capacity = model.variables["Discharge capacity [A.h]"]
        # The nominal complementarity target stays4.2V. Its native CV branch
        # needs a separately declared numerical protective event, rather than
        # the standard CC-only terminating event at the regulation voltage.
        model.events = [
            event for event in model.events if event.name != "Maximum voltage [V]"
        ]
        for name, expression in (
            (TARGET_EVENT, pybamm.Scalar(float(TARGET_CHARGE)) + capacity),
            (EVENT_NAMES[1], pybamm.Scalar(318.15) - temperature),
            (EVENT_NAMES[2], temperature - pybamm.Scalar(273.15)),
            (EVENT_NAMES[3], pybamm.Scalar(4.201) - voltage),
            (EVENT_NAMES[4], -current - pybamm.Scalar(0.05)),
        ):
            model.events.append(
                pybamm.Event(name, expression, pybamm.EventType.TERMINATION)
            )
        model.events.append(
            pybamm.Event(
                TIER_EVENT,
                pybamm.InputParameter(TIER_DIRECTION_INPUT)
                * (temperature - pybamm.InputParameter(TIER_THRESHOLD_INPUT)),
                pybamm.EventType.TERMINATION,
            )
        )
        event_names = tuple(
            sorted(
                event.name
                for event in model.events
                if event.event_type is pybamm.EventType.TERMINATION
            )
        )
        parameter_set = "Chen2020" if config.model_view == "chen-spme" else "ORegan2022"
        parameters = pybamm.ParameterValues(parameter_set)
        parameters.update(
            {
                "Upper voltage cut-off [V]": 4.2,
                "Lower voltage cut-off [V]": 2.5,
                "Open-circuit voltage at 100% SOC [V]": 4.2,
                "Open-circuit voltage at 0% SOC [V]": 2.5,
                "Initial temperature [K]": float(config.initial_temperature_k),
                "Ambient temperature [K]": float(config.chamber_temperature_k),
            }
        )
        delivery = replace(
            delivery,
            accepted_voltage_v=_decimal(parameters["Upper voltage cut-off [V]"]),
            accepted_chamber_k=_decimal(parameters["Ambient temperature [K]"]),
            accepted_control_expression=str(control(model.variables)),
        )
        solver = pybamm.IDAKLUSolver(
            rtol=float(rtol),
            atol=float(atol),
            on_failure="warn",
            options={
                "max_num_steps": -1,
                "dt_max": 0.0,
                "num_steps_no_progress": 0,
                "num_threads": 1,
                "num_solvers": 1,
            },
        )
        mesh = dict(model.default_submesh_types)
        for particle in ("negative particle", "positive particle"):
            mesh[particle] = pybamm.MeshGenerator(
                pybamm.Exponential1DSubMesh, {"side": "right"}
            )
        points = {
            name: particle_points if name.startswith("r_") else electrode_points
            for name in ("x_n", "x_s", "x_p", "r_n", "r_p")
        }
        simulation = pybamm.Simulation(
            model,
            parameter_values=parameters,
            solver=solver,
            submesh_types=mesh,
            var_pts=points,
        )
        initial_regime = (
            "HIGH"
            if config.initial_temperature_k
            >= TIER_TEMPERATURE + config.localization_epsilon_k
            else "LOW"
        )
        with observe_initial_solver_calls(pybamm.BaseSolver, initializer_attempts):
            simulation.build(
                initial_soc=0.30,
                inputs={
                    name: float(value)
                    for name, value in hybrid_inputs(config, initial_regime).items()
                },
            )
        built = simulation.built_model
        processed_events = tuple(
            str(next(event.expression for event in built.events if event.name == name))
            for name in event_names
        )
        delivery = replace(
            delivery,
            applied_control_expression=str(
                next(
                    expression
                    for variable, expression in built.algebraic.items()
                    if variable.name == "Current variable [A]"
                )
            ),
            applied_current_expression=str(built.get_processed_variable("Current [A]")),
            applied_voltage_expression=str(built.get_processed_variable("Voltage [V]")),
            applied_chamber_expression=str(
                built.get_processed_variable("Ambient temperature [K]")
            ),
        )
        model_sha = sha256(
            json.dumps(
                {
                    name: sorted(
                        (str(variable), str(expression))
                        for variable, expression in getattr(built, name).items()
                    )
                    for name in ("rhs", "algebraic")
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ).hexdigest()
        solver_json = json.dumps(
            solver.to_config(), sort_keys=True, separators=(",", ":"), allow_nan=False
        )
        receiver_blocks = []
        names = (
            "Current [A]",
            "Voltage [V]",
            "Discharge capacity [A.h]",
            "Volume-averaged cell temperature [K]",
            "Ambient temperature [K]",
        )

        def execute(index, regime, requested_start, previous):
            wall, cpu = time.perf_counter(), time.process_time()
            inputs = hybrid_inputs(config, regime)
            requested_state = (
                charging_attempts[-1].end_differential_state
                if charging_attempts
                else ()
            )
            raw_clocks = start_state = end_state = first = last = ()
            failure_type = failure_message = None
            actual_return, end_reason, solution = (
                "RETURNED",
                "native-not-returned",
                None,
            )
            try:
                with warnings.catch_warnings(record=True) as observed_warnings:
                    solution = solver.step(
                        previous,
                        built,
                        float(MAX_MODEL_CLOCK - requested_start),
                        inputs={name: float(value) for name, value in inputs.items()},
                        save=False,
                    )
                raw = np.asarray(solution.t, dtype=float).reshape(-1)
                raw_clocks = tuple(_decimal(value) for value in raw)
                start_state, end_state = differential_state_endpoints(
                    solution, built.len_rhs
                )
                observed = np.unique(
                    np.concatenate((raw, np.arange(np.ceil(raw[0]), raw[-1], 1)))
                )
                observed_clocks = tuple(_decimal(value) for value in observed)
                values = tuple(
                    tuple(
                        _decimal(value)
                        for value in np.asarray(
                            solution[name](observed), dtype=float
                        ).reshape(-1)
                    )
                    for name in names
                )
                first = (values[0][0], values[1][0], values[3][0], values[2][0])
                last = (values[0][-1], values[1][-1], values[3][-1], values[2][-1])
                receiver_blocks.append((observed_clocks, values, regime))
                end_reason = str(solution.termination)
                if end_reason == "failure":
                    actual_return, failure_type = (
                        "TECHNICAL_FAILURE",
                        "NativeSolverFailure",
                    )
                    failure_message = "; ".join(
                        str(w.message) for w in observed_warnings
                    )
                else:
                    # Every receiver, native knot, differential endpoint and
                    # event metadata is extracted above. Carry only a complete
                    # independently owned terminal column into the next solve.
                    solution = detached_terminal_solution(solution)
            except Exception as error:
                actual_return, failure_type, failure_message = (
                    "TECHNICAL_FAILURE",
                    type(error).__name__,
                    str(error),
                )
                end_reason = failure_type
            return charging_attempt_factory(
                index,
                regime,
                config.localization_epsilon_k,
                requested_start,
                solver_json,
                model_sha,
                delivery.applied_control_expression,
                tuple(sorted(inputs.items())),
                requested_state,
                actual_return,
                end_reason,
                failure_type,
                failure_message,
                _decimal(time.process_time() - cpu),
                _decimal(time.perf_counter() - wall),
                raw_clocks,
                start_state,
                end_state,
                first,
                last,
            ), solution

        failure = run_hybrid_segments(config, execute, charging_attempts, transitions)
        (
            clocks,
            columns,
            modes,
            temperature_regimes,
            termination,
            disposition,
            error_type,
            error_message,
        ) = project_hybrid_run(charging_attempts, receiver_blocks, failure)
        if clocks:
            delivery = replace(
                delivery,
                applied_model_clock_s=clocks[0],
                applied_current_a=columns[0][0],
                applied_voltage_v=columns[1][0],
                applied_chamber_k=columns[4][0],
            )

    except (
        Exception
    ) as error:  # Complete technical attempts stay typed; no automatic retry.
        error_type, error_message = type(error).__name__, str(error)
        termination, disposition = error_type, "TECHNICAL_FAILURE"
        if not columns:
            clocks, modes = (), ()
    if not columns:
        columns = ((), (), (), (), ())
    if not processed_events:
        # Preserve the known requested event census even when construction
        # failed before native expression processing; empty expressions do not
        # grant application or protective-event evidence.
        processed_events = tuple("" for _ in event_names)
    return trace_factory(
        f"trace.{config.config_id}",
        config,
        implementation,
        disposition,
        termination,
        error_type,
        error_message,
        delivery,
        clocks,
        *columns,
        modes,
        event_names,
        processed_events,
        1,
        len(charging_attempts),
        _decimal(time.perf_counter() - start_wall),
        _decimal(time.process_time() - start_cpu),
        int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * 1024,
        tuple(initializer_attempts),
        charging_attempts=tuple(charging_attempts),
        transitions=tuple(transitions),
        temperature_regimes=temperature_regimes,
    )
