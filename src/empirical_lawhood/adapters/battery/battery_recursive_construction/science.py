"""Native acquisition and external-format binding for the domain science."""

from decimal import localcontext
from hashlib import sha256
from importlib.metadata import distribution, version
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition as Disposition
from empirical_lawhood.science.records.serialization import canonical_json_bytes
from empirical_lawhood.domains.battery.battery_recursive_construction.contracts import BatteryCheckpoint, BatteryOperation, BatteryOperationConfig, BatterySourceContract, BatteryTrace

from empirical_lawhood.domains.battery.battery_recursive_construction.assessment import (
    CLOCKS as _science_CLOCKS,
    CONTEXT as _science_CONTEXT,
    D as _science_D,
    _empty_trace,
    _future,
    checkpoint_preflight as _science_checkpoint_preflight,
    identity as _science_identity,
    project_checkpoint as _science_project_checkpoint,
)

def source_preflight(source: BatterySourceContract):
    """Check installed source bytes without importing the solver or acquiring evidence."""
    for package, expected in (("pybamm", source.pybamm_version), ("casadi", source.casadi_version),
                              ("numpy", source.numpy_version), ("scipy", source.scipy_version)):
        if version(package) != expected:
            raise ValueError(f"battery frozen {package} version differs before contact")
    package = distribution("pybamm")
    for locator, expected in (
        ("pybamm/input/parameters/lithium_ion/Chen2020.py", source.parameter_sha256),
        ("pybamm/models/full_battery_models/lithium_ion/spme.py", source.model_sha256),
        ("pybamm/solvers/casadi_solver.py", source.solver_sha256),
    ):
        if sha256(package.locate_file(locator).read_bytes()).hexdigest() != expected:
            raise ValueError("battery installed source bytes differ before contact")


def _runtime(source, initial_soc, *, tighter=False):
    import pybamm

    model = pybamm.lithium_ion.SPMe(options={"thermal": "isothermal", "cell geometry": "pouch",
                                          "calculate heat source for isothermal models": "true"})
    parameters = pybamm.ParameterValues("Chen2020")
    if _science_D(str(parameters["Nominal cell capacity [A.h]"])) != _science_D(5):
        raise ValueError("installed nominal capacity differs from the frozen 5 Ah operand")
    parameters.update({"Current function [A]": "[input]", "Ambient temperature [K]": "[input]",
                       "Initial temperature [K]": 293.15})
    solver = pybamm.CasadiSolver(
        mode="safe", rtol=float(source.tighter_rtol if tighter else source.coarse_rtol),
        atol=float(source.tighter_atol if tighter else source.coarse_atol),
        extra_options_setup={"max_num_steps": source.integrator_max_steps},
        max_step_decrease_count=source.max_step_decreases, dt_max=600,
    )
    simulation = pybamm.Simulation(model, parameter_values=parameters, solver=solver,
                                  var_pts={name: source.mesh_points for name in ("x_n", "x_s", "x_p", "r_n", "r_p")})
    simulation.build(initial_soc=float(initial_soc), inputs=_inputs(_science_D(0)))
    return pybamm, simulation


def _layout(model):
    entries = tuple(sorted((variable.name, tuple((part.start, part.stop, part.step) for part in slices))
                           for variable, slices in model.y_slices.items()))
    return sha256(canonical_json_bytes(entries)).hexdigest()


def _model_id(model):
    return sha256(canonical_json_bytes((model.name, int(model.len_rhs), int(model.len_alg), _layout(model)))).hexdigest()


def _inputs(current):
    return {"Current function [A]": float(current), "Ambient temperature [K]": 293.15}


def _phase(simulation, start, stop, current, *, starting_solution=None):
    import numpy as np

    return simulation.step(float(stop - start), t_eval=np.arange(0, float(stop - start) + 1, 10),
                           inputs=_inputs(current), starting_solution=starting_solution)


def _prefix(simulation, history, on_phase=None):
    currents = (_science_D(1), _science_D(0)) if history == "early" else (_science_D(0), _science_D(1))
    for start, stop, current in zip((_science_D(0), _science_D(150)), (_science_D(150), _science_D(300)), currents, strict=True):
        if on_phase is not None:
            on_phase()
        _phase(simulation, start, stop, current)
    return simulation.solution


def _state(solution):
    import numpy as np

    value = solution.last_state.all_ys[0]
    if hasattr(value, "full"):
        value = value.full()
    values = np.asarray(value, dtype="<f8").reshape(-1)
    if not len(values) or len(values) > 4096 or not np.isfinite(values).all():
        raise ValueError("native checkpoint state violates the finite f8 census")
    return values


def _scalar(solution, variable, time):
    import numpy as np

    value = float(np.asarray(solution[variable](float(time))).reshape(-1)[0])
    if not np.isfinite(value):
        raise ValueError("native battery quantity is nonfinite")
    return _science_D(str(value))


def capture_checkpoint(config: BatteryOperationConfig):
    if config.operation is not BatteryOperation.CHECKPOINT:
        raise ValueError("checkpoint acquisition received another operation config")
    source_preflight(config.source)
    _, simulation = _runtime(config.source, config.initial_soc)
    solution = _prefix(simulation, config.history)
    if float(solution.t[-1]) < 300 - 1e-8:
        raise ValueError("native prefix terminated before the assigned checkpoint")
    return BatteryCheckpoint(
        f"{config.config_id}.checkpoint", config.source, config.unit_id, config.history, config.initial_soc,
        _science_D(300), _scalar(solution, "Discharge capacity [A.h]", 300),
        _scalar(solution, "Volume-averaged cell temperature [K]", 300),
        _science_D(0) if config.history == "early" else _science_D(1),
        (("Ambient temperature [K]", _science_D("293.15")), ("Current function [A]", _science_D(0) if config.history == "early" else _science_D(1))),
        _layout(simulation.built_model),
        _model_id(simulation.built_model), _state(solution).tobytes().hex(), 2,
    )


def _starting(pybamm, checkpoint, state, model):
    # Reuse the installed repository's known restart primitive. The source input
    # applies at the checkpoint; later step inputs supply the declared future.
    from empirical_lawhood.adapters.simulators.pybamm_exact_restart import _starting_solution
    # PyBaMM stacks Solution input dict values; its solver uses alphabetical
    # names. The canonical ledger preserves this required order explicitly.
    return _starting_solution(pybamm, checkpoint_s=300, state=state, model=model,
                              inputs=dict(checkpoint.source_input_ledger))


def continue_checkpoint(config, checkpoint, admission=None):
    if config.operation not in {BatteryOperation.REFERENCE, BatteryOperation.FULL, BatteryOperation.SOC, BatteryOperation.TIGHTER}:
        raise ValueError("native continuation received another registered config")
    _science_checkpoint_preflight(config, checkpoint)
    if config.wave == "B":
        if admission is None or admission.consumer_id != "C1" or admission.supply.disposition is not Disposition.SATISFIED:
            return _empty_trace(config, checkpoint, ("C1_ADMISSION_NOT_SATISFIED",))
        if admission.checkpoint_summary.object_fingerprint != _science_project_checkpoint(checkpoint).fingerprint():
            raise ValueError("admission is bound to another checkpoint before native contact")
        if config.contribution_sha256 != admission.contribution_sha256:
            raise ValueError("continuation changed its committed contribution before native contact")
    elif admission is not None:
        raise ValueError("Wave A cannot receive a later admission")
    source_preflight(config.source)
    tighter = config.operation is BatteryOperation.TIGHTER
    route = config.operation.value
    pybamm, simulation = _runtime(config.source, config.initial_soc, tighter=tighter)
    if _layout(simulation.built_model) != checkpoint.state_layout_sha256 or _model_id(simulation.built_model) != checkpoint.model_sha256:
        raise ValueError("checkpoint layout or model differs before integration")
    phase_calls = 0
    exact = False
    try:
        import numpy as np

        if route == "REFERENCE":
            def entered_prefix_phase():
                nonlocal phase_calls
                phase_calls += 1
            solution = _prefix(simulation, config.history, entered_prefix_phase)
            exact = _state(solution).tobytes().hex() == checkpoint.state_hex
            starting = None
        else:
            if route == "SOC":
                with localcontext(_science_CONTEXT):
                    soc = checkpoint.initial_soc - checkpoint.capacity_Ah / _science_D(5)
                pybamm, simulation = _runtime(config.source, soc)
                state = np.asarray(simulation.built_model.concatenated_initial_conditions.evaluate(inputs=_inputs(checkpoint.source_current_A)), dtype="<f8").reshape(-1)
                capacity_slices = [slices for variable, slices in simulation.built_model.y_slices.items() if variable.name == "Discharge capacity [A.h]"]
                if len(capacity_slices) != 1 or len(capacity_slices[0]) != 1:
                    raise ValueError("SOC capacity state has no unique native bookkeeping coordinate")
                state[capacity_slices[0][0]] = float(checkpoint.capacity_Ah)
            else:
                state = np.frombuffer(bytes.fromhex(checkpoint.state_hex), dtype="<f8").copy()
                exact = state.tobytes().hex() == checkpoint.state_hex
            starting = _starting(pybamm, checkpoint, state, simulation.built_model)
        for start, stop, current in _future(config.future_word):
            phase_calls += 1
            solution = _phase(simulation, start, stop, current, starting_solution=starting)
            starting = None
            if float(solution.t[-1]) < float(stop) - 1e-8:
                return _trace(config, checkpoint, solution, exact, False, ("NATIVE_EARLY_TERMINATION",), phase_calls)
        return _trace(config, checkpoint, solution, exact, True, (), phase_calls)
    except (pybamm.SolverError, RuntimeError, ValueError) as error:
        # Preserve finite data actually returned before a scientific native stop.
        reason = (f"NATIVE_{type(error).__name__.upper()}",)
        solution = simulation.solution
        if solution is not None and hasattr(solution, "t") and len(solution.t) and float(solution.t[-1]) >= 300:
            return _trace(config, checkpoint, solution, exact, False, reason, phase_calls)
        return _empty_trace(config, checkpoint, reason, phase_calls)


def _trace(config, checkpoint, solution, exact, completed, reasons, calls):
    last = _science_D(str(float(solution.t[-1])))
    retained = []
    for clock in (t for t in _science_CLOCKS if t <= last + _science_D("0.00000001")):
        try:
            values = tuple(_scalar(solution, variable, clock) for variable in
                           ("Terminal voltage [V]", "Discharge capacity [A.h]", "Volume-averaged cell temperature [K]"))
        except ValueError:
            completed = False
            reasons = tuple(sorted(set((*reasons, "NATIVE_INVALID_QUANTITY"))))
            break
        retained.append((clock, values))
    clocks = tuple(t for t, _ in retained)
    channels = tuple(tuple(values[index] for _, values in retained) for index in range(3))
    return BatteryTrace(f"{config.config_id}.trace", _science_identity(checkpoint), checkpoint.unit_id, checkpoint.history,
                        config.future_word, config.operation.value, "tighter" if config.operation is BatteryOperation.TIGHTER else "coarse",
                        clocks, *channels, exact, completed, reasons, calls, config.source)
