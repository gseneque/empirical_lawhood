"""Native contact for new joint-description trials, entered by typed execution.

There is no synthetic fallback, historical campaign invocation or implicit retry.
Importing/constructing this adapter does not import a native engine. The execution
runner owns native-effect custody and CPU/GPU worker selection.
"""

from __future__ import annotations

import copy
from decimal import Decimal
from importlib.metadata import PackageNotFoundError, version
import math
from collections.abc import Mapping

import numpy as np

from empirical_lawhood.domains.joint_description_native import RECEIVERS, feature_vector, preparation_rng, resolve_parameters, sample_preparation, selected_receivers
from empirical_lawhood.domains.battery.joint_description import battery_receivers, continuation_defect
from empirical_lawhood.domains.fusion.joint_description import temperature_change


class NativePrerequisiteError(RuntimeError):
    """An authored engine/device/input prerequisite is absent before execution."""


class NativePartialEpisodeError(RuntimeError):
    """A late native failure retains completed earlier horizons without retry."""

    def __init__(self, reason, outcomes, work_units=0.0):
        super().__init__(reason)
        self.outcomes = outcomes
        self.work_units = work_units


def _number(parameters, name, default, *, lower=None, upper=None):
    value = parameters.get(name, default)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"native parameter {name} must be finite")
    result = float(value)
    if lower is not None and result < lower or upper is not None and result > upper:
        raise ValueError(f"native parameter {name} is outside its admitted bounds")
    return result


def _integer(parameters, name, default, *, lower, upper):
    value = parameters.get(name, default)
    if type(value) is not int or not lower <= value <= upper:
        raise ValueError(f"native parameter {name} must be an integer in [{lower},{upper}]")
    return value


def _versions(parameters, required):
    expected = parameters.get("expected_versions")
    if not isinstance(expected, Mapping) or set(expected) != set(required):
        raise ValueError("native version denominator must name every required engine")
    observed = []
    for package in sorted(required):
        try:
            actual = version(package)
        except PackageNotFoundError as error:
            raise NativePrerequisiteError(f"required native dependency is absent: {package}=={expected[package]}") from error
        if actual != expected[package]:
            raise NativePrerequisiteError(f"native version differs: {package} expected {expected[package]}, observed {actual}")
        observed.append(f"{package}=={actual}")
    return tuple(observed)


def _jax_device(device):
    if device not in {"cpu", "gpu"}:
        raise ValueError("native JAX device must be cpu or gpu")
    if device == "gpu":
        from empirical_lawhood.execution.remote.worker_profiles import JAX_TORAX_WORKER
        try:
            installed = {name: version(name) for name, _ in JAX_TORAX_WORKER.required_versions}
        except PackageNotFoundError as error:
            raise NativePrerequisiteError("selected GPU workload requires the pinned JAX CUDA12 native library closure") from error
        JAX_TORAX_WORKER.validate_versions(installed)
    import jax
    jax.config.update("jax_platforms", "cuda" if device == "gpu" else "cpu")
    jax.config.update("jax_enable_x64", True)
    if jax.default_backend() != device or not jax.config.read("jax_enable_x64"):
        raise NativePrerequisiteError("native JAX backend/float64 does not match the authored device")
    if device == "gpu" and len(jax.devices("gpu")) != 1:
        raise NativePrerequisiteError("selected JAX GPU operation requires exactly one visible admitted device")


def _rows_for(request, unit_id, preparation, action, outcomes, *, status="supported", reason="", diagnostics=(), work_units=0.0):
    from empirical_lawhood.science.joint_description import TrialRow
    receivers = selected_receivers(request)
    return tuple(TrialRow(unit_id=unit_id, action=action, horizon=horizon, receiver_id=receiver,
                          features=feature_vector(request.family_id, preparation, action, horizon),
                          outcome=outcomes.get(horizon, {}).get(receiver),
                          status="supported" if receiver in outcomes.get(horizon, {}) else status,
                          reason="" if receiver in outcomes.get(horizon, {}) else reason,
                          work_units=work_units / (len(request.horizons) * len(receivers)),
                          diagnostics=tuple(sorted(diagnostics)))
                 for horizon in request.horizons for receiver in receivers)


def _native_failure(error):
    return f"NATIVE_EPISODE_FAILED:{type(error).__name__}:{str(error)[:500]}"


def _sample_clock(horizon, interval):
    if not 0 < interval <= horizon or horizon > 3600:
        raise ValueError("native battery clock must have 0 < interval <= horizon <= 3600 s")
    size = math.ceil(horizon / interval)
    if size > 10000:
        raise ValueError("native battery clock exceeds 10000 output intervals")
    return np.linspace(0, horizon, size + 1, dtype=np.float64)


def _pybamm_episode(preparation, action, horizons, parameters, *, model_name):
    """One fresh model, one history prefix and one continuation; no restart shim."""
    import pybamm
    horizon = max(horizons)
    interval = _number(parameters, "sample_interval_s", 5, lower=1e-6)
    clock = _sample_clock(horizon, interval)
    prefix = _number(parameters, "history_duration_s", 30, lower=0, upper=3600)
    points = _integer(parameters, "spatial_points", 12, lower=4, upper=100)
    rtol = _number(parameters, "rtol", 1e-6, lower=1e-12, upper=1e-2)
    atol = _number(parameters, "atol", 1e-8, lower=1e-14, upper=1e-2)
    parameter_set = parameters["parameter_set"]
    if not isinstance(parameter_set, str) or not parameter_set:
        raise ValueError("native PyBaMM parameter-set identity must be explicit")
    model_class = {"SPMe": pybamm.lithium_ion.SPMe, "DFN": pybamm.lithium_ion.DFN}[model_name]
    model = model_class(options={"thermal": "lumped", "cell geometry": "pouch"})
    parameter_values = pybamm.ParameterValues(parameter_set)
    parameter_values["Current function [A]"] = "[input]"
    parameter_values["Initial temperature [K]"] = preparation["initial_temperature_k"]
    parameter_values["Ambient temperature [K]"] = preparation["initial_temperature_k"]
    simulation = pybamm.Simulation(model, parameter_values=parameter_values,
                                  solver=pybamm.CasadiSolver(mode="safe", rtol=rtol, atol=atol),
                                  var_pts={key: points for key in ("x_n", "x_s", "x_p", "r_n", "r_p")})
    simulation.build(initial_soc=preparation["initial_soc"], inputs={"Current function [A]": preparation["history_current_a"]})
    if prefix > 0:
        simulation.step(prefix, t_eval=_sample_clock(prefix, min(interval, prefix)),
                        inputs={"Current function [A]": preparation["history_current_a"]})
        if simulation.solution.termination != "final time":
            raise RuntimeError("native battery history terminated before the authored cutoff")
    simulation.step(horizon, t_eval=clock, inputs={"Current function [A]": action})
    solution = simulation.solution
    if solution.termination != "final time":
        raise RuntimeError(f"native battery continuation terminated: {solution.termination}")
    actual_clock = prefix + clock
    voltage = np.asarray(solution["Terminal voltage [V]"](actual_clock), dtype=np.float64).reshape(-1)
    temperature = np.asarray(solution["Volume-averaged cell temperature [K]"](actual_clock), dtype=np.float64).reshape(-1)
    capacity = np.asarray(solution["Discharge capacity [A.h]"](actual_clock), dtype=np.float64).reshape(-1)
    realized = np.asarray(solution["Current [A]"](actual_clock[1:]), dtype=np.float64).reshape(-1)
    if not np.allclose(realized, action, rtol=0, atol=1e-8):
        raise RuntimeError("native PyBaMM realized current differs from the requested constant action")
    if not all(values.shape == clock.shape and np.isfinite(values).all() for values in (voltage, temperature, capacity)):
        raise RuntimeError("native battery retained receiver clock/finite-value check failed")
    results = {}
    for cut in horizons:
        receiver = battery_receivers(clock, np.full(clock.shape, action), voltage, temperature, horizon_s=cut)
        native_capacity = float(np.interp(cut, clock, capacity) - capacity[0])
        if abs(native_capacity - receiver.discharge_capacity_ah) > max(1e-6, 10 * atol):
            raise RuntimeError("native discharge capacity violates the independently integrated current action")
        results[cut] = {"terminal_voltage_v": receiver.terminal_voltage_v,
                        "discharge_capacity_ah": native_capacity,
                        "peak_temperature_k": receiver.peak_temperature_k}
    return results, points * len(clock)


def _acquire_battery(request, parameters):
    from empirical_lawhood.science.joint_description import TrialBatch
    if request.device != "cpu":
        raise NativePrerequisiteError("PyBaMM/CasADi workload declares CPU execution; GPU is not a supported relabeling")
    versions = _versions(parameters, {"pybamm"})
    rows = []
    for unit_id in request.unit_ids:
        preparation = sample_preparation(request, unit_id, parameters)
        for action in request.actions:
            if not -10 <= action <= 10:
                raise ValueError("authored PyBaMM action exceeds the [-10,10] A acquisition envelope")
            try:
                if request.family_id == "R18":
                    outcomes, work = _pybamm_episode(preparation, action, request.horizons, parameters, model_name="SPMe")
                else:
                    full, work_full = _pybamm_episode(preparation, action, request.horizons, parameters, model_name="DFN")
                    reduced, work_reduced = _pybamm_episode(preparation, action, request.horizons, parameters, model_name="SPMe")
                    outcomes = {}
                    for horizon in request.horizons:
                        defect = continuation_defect(
                            [full[horizon]["terminal_voltage_v"], full[horizon]["peak_temperature_k"]],
                            [reduced[horizon]["terminal_voltage_v"], reduced[horizon]["peak_temperature_k"]], scales=[1, 1])
                        outcomes[horizon] = dict(zip(RECEIVERS["R19"], map(float, defect), strict=True))
                    work = work_full + work_reduced
                rows.extend(_rows_for(request, unit_id, preparation, action, outcomes, work_units=work))
            except (RuntimeError, ValueError, ArithmeticError) as error:
                rows.extend(_rows_for(request, unit_id, preparation, action, {}, status="failed", reason=_native_failure(error)))
    scope = "spme-lumped-current-continuation" if request.family_id == "R18" else "dfn-vs-spme-lumped-continuations-not-exact-state-restarts"
    return TrialBatch(request.family_id, request.split, tuple(rows), "fresh-native-simulation",
                      (*versions, "device:cpu", f"parameter-set:{parameters['parameter_set']}", scope,
                       "potential-action-panel-for-simulator-audit-only", "no-physical-cell-control-claim"))


def _scale_radial(source, scale):
    result = copy.deepcopy(source)
    if not isinstance(result, Mapping):
        raise ValueError("Gym-TORAX configured temperature profile is not a radial mapping")
    for values in result.values():
        if not isinstance(values, dict):
            raise ValueError("Gym-TORAX profile time slice is not a mapping")
        for radius in values:
            if float(radius) < 1:
                values[radius] = float(values[radius]) * scale
    return result


def _gym_episode(preparation, action, horizons, parameters, seed):
    """One actual IterHybridEnv; exact source action delivery is audited."""
    from gymtorax.envs.iter_hybrid_env import CONFIG, IterHybridEnv
    horizon = max(horizons)
    if any(h <= 0 or h != int(h) for h in horizons) or horizon > 120:
        raise ValueError("Gym-TORAX observation horizons must be integer seconds in [1,120]")
    dt = _number(parameters, "internal_timestep_s", 1, lower=0.05, upper=1)
    ratio = int(round(1 / dt))
    if abs(ratio * dt - 1) > 1e-12:
        raise ValueError("Gym-TORAX internal step must divide its one-second action clock")
    cells = _integer(parameters, "radial_cells", 25, lower=4, upper=256)
    config = copy.deepcopy(CONFIG)
    config["numerics"]["t_final"] = horizon
    config["numerics"]["fixed_dt"] = dt
    config["geometry"]["n_rho"] = cells
    config["solver"]["n_corrector_steps"] = _integer(parameters, "corrector_steps", 10, lower=0, upper=50)
    for field in ("T_i", "T_e"):
        config["profile_conditions"][field] = _scale_radial(config["profile_conditions"][field], preparation["temperature_scale"])
    config["profile_conditions"]["nbar"] = preparation["density_nbar"]
    config["neoclassical"]["bootstrap_current"]["bootstrap_multiplier"] = preparation["bootstrap_multiplier"]
    for field in ("D_e_inner", "chi_i_inner", "chi_e_inner"):
        config["transport"][field] = float(config["transport"][field]) * preparation["inner_transport_scale"]

    class Environment(IterHybridEnv):
        def _get_torax_config(self):
            return {"config": config, "discretization": "fixed", "ratio_a_sim": ratio}

        def _compute_reward(self, state, next_state, action):
            return 0.0

    nbi = _number(parameters, "nbi_power_w", 30e6, lower=0, upper=33e6) * (1 + action)
    if not 0 <= nbi <= 33e6 or not -0.5 <= action <= 0.5:
        raise ValueError("Gym-TORAX heating fraction leaves the native [0,33 MW] action envelope")
    plasma_current = _number(parameters, "plasma_current_a", 12.5e6, lower=1e5, upper=15e6)
    config["profile_conditions"]["Ip"] = plasma_current
    native_action = {"Ip": np.array([plasma_current]),
                     "NBI": np.array([nbi,
                         _number(parameters, "nbi_location", 0.25, lower=0, upper=1),
                         _number(parameters, "nbi_width", 0.25, lower=0.01, upper=1)]),
                     "ECRH": np.array([_number(parameters, "ecrh_power_w", 20e6, lower=0, upper=20e6),
                         _number(parameters, "ecrh_location", 0.35, lower=0, upper=1),
                         _number(parameters, "ecrh_width", 0.05, lower=0.01, upper=1)])}
    environment = Environment(render_mode=None, store_history=False, log_level="warning")
    outcomes = {}
    try:
        environment.reset(seed=seed)
        if abs(float(environment.current_time)) > 1e-8:
            raise RuntimeError("Gym-TORAX reset did not produce the declared action-zero clock")
        for clock in range(1, int(horizon) + 1):
            step = environment.step(native_action)
            if not isinstance(step, tuple) or len(step) != 5:
                raise RuntimeError("Gym-TORAX step does not implement the inspected five-field Gymnasium contract")
            _, _, terminated, truncated, info = step
            if abs(float(environment.current_time) - clock) > 1e-8:
                raise RuntimeError("Gym-TORAX action/receiver clock differs")
            getter = getattr(getattr(getattr(environment, "torax_app", None), "config", None), "get_current_action_values", None)
            applied = info.get("applied_action") if isinstance(info, Mapping) else None
            if applied is None and callable(getter):
                applied = getter()
            if not isinstance(applied, Mapping) or any(
                name not in applied or np.asarray(applied[name]).shape != value.shape
                or not np.allclose(np.asarray(applied[name], dtype=float), value, rtol=1e-8, atol=1e-8)
                for name, value in native_action.items()
            ):
                raise RuntimeError("Gym-TORAX applied action missing or clipped; no effect credited to a different action")
            state = environment.state
            if not isinstance(state, Mapping) or not isinstance(state.get("scalars"), Mapping):
                raise RuntimeError("Gym-TORAX native scalar state is absent")
            scalars = state["scalars"]
            numerics = state.get("numerics")
            if not isinstance(numerics, Mapping):
                from empirical_lawhood.adapters.simulators.gym_torax_native.runtime import _native_numerics
                numerics = _native_numerics(environment)
            solver_error = np.asarray(numerics.get("solver_error_state", []), dtype=np.float64)
            if solver_error.size != 1 or not np.isfinite(solver_error).all() or float(solver_error.reshape(-1)[0]) != 0:
                raise RuntimeError("Gym-TORAX solver status is absent or nonzero")
            if clock in horizons:
                value = np.asarray(scalars["Q_fusion"], dtype=np.float64)
                if value.size != 1 or not np.isfinite(value).all():
                    raise RuntimeError("Gym-TORAX fusion-gain receiver is not a finite scalar")
                outcomes[float(clock)] = {"fusion_gain": float(value.reshape(-1)[0])}
            if (terminated or truncated) and clock < horizon:
                raise RuntimeError("Gym-TORAX native episode ended before its declared horizon")
        return outcomes, cells * int(horizon) * ratio
    except (RuntimeError, ValueError, KeyError, ArithmeticError) as error:
        if outcomes:
            raise NativePartialEpisodeError(str(error), outcomes, cells * max(outcomes) * ratio) from error
        raise
    finally:
        environment.close()


def _acquire_gym(request, parameters):
    from empirical_lawhood.science.joint_description import TrialBatch
    versions = _versions(parameters, {"gymtorax", "torax", "jax", "jaxlib"})
    _jax_device(request.device)
    rows = []
    for unit_id in request.unit_ids:
        preparation = sample_preparation(request, unit_id, parameters)
        seed = int(preparation_rng(request, unit_id).integers(0, 2**31 - 1))
        for action in request.actions:
            try:
                outcomes, work = _gym_episode(preparation, action, request.horizons, parameters, seed)
                rows.extend(_rows_for(request, unit_id, preparation, action, outcomes, work_units=work))
            except (RuntimeError, ValueError, KeyError, ArithmeticError) as error:
                partial = error.outcomes if isinstance(error, NativePartialEpisodeError) else {}
                work = error.work_units if isinstance(error, NativePartialEpisodeError) else 0
                rows.extend(_rows_for(request, unit_id, preparation, action, partial, status="failed", reason=_native_failure(error), work_units=work))
    return TrialBatch(request.family_id, request.split, tuple(rows), "fresh-native-simulation",
                      (*versions, f"device:{request.device}", "float64", "Gym-TORAX-IterHybridEnv",
                       "fresh-preparations-same-seed-potential-action-panel", "no-physical-plasma-control-claim"))


def _acquire_bridge(request, parameters):
    from empirical_lawhood.science.joint_description import TrialBatch, TrialRow
    from empirical_lawhood.adapters.physical.joint_description import archive_rows, cohort_from_request, mapped_torax_preparation
    from empirical_lawhood.domains.fusion.torax_native.contracts import NativeToraxAction, NativeToraxActionStage, NativeToraxView, NativeToraxEpisodeDisposition
    from empirical_lawhood.science.response.action_contracts import ActionDeliveryStage
    from empirical_lawhood.adapters.simulators.torax_native.runtime import execute_native_torax
    cohort = cohort_from_request(request)
    physical = archive_rows(request, cohort, parameters)
    # Parse every mapped preparation before touching a native engine.
    mapped = {unit_id: mapped_torax_preparation(unit_id, cohort.units[unit_id]) for unit_id in request.unit_ids}
    versions = _versions(parameters, {"torax", "jax", "jaxlib"})
    _jax_device(request.device)
    horizon = max(request.horizons)
    view = NativeToraxView(view_id="view.joint-description.bridge", radial_cells=_integer(parameters, "radial_cells", 12, lower=4, upper=256),
                           timestep_s=Decimal(str(_number(parameters, "internal_timestep_s", 0.002, lower=1e-6))),
                           horizon_s=Decimal(str(horizon)), solver_id="linear-theta-fully-implicit", linear_solver_id="thomas",
                           precision="float64", closure_id="closure.joint-description.authored-constant-transport")
    rows = list(physical)
    for unit_id in request.unit_ids:
        raw = cohort.units[unit_id]
        preparation = raw["preparation"]
        for index, fraction in enumerate(request.actions):
            power = preparation["heating_power_w"] * (1 + fraction)
            if power < 0:
                raise ValueError("bridge heating fraction creates a negative native power")
            action = NativeToraxAction(action_id=f"action.joint-description.bridge.{index}", action_label=f"option-{index}",
                                        stages=tuple(NativeToraxActionStage(stage, Decimal(str(power)), Decimal(0)) for stage in ActionDeliveryStage),
                                        duration_s=view.horizon_s, source_model_id="generic-ion-electron-gaussian-proxy")
            values, status, reason, work = {}, "supported", "", 0
            try:
                trajectory, episode = execute_native_torax(mapped[unit_id], action, view)
                if episode.disposition is not NativeToraxEpisodeDisposition.COMPLETE:
                    raise RuntimeError(";".join(episode.reason_codes))
                for cut in request.horizons:
                    values[cut] = temperature_change(trajectory.time_s, trajectory.core_electron_temperature_ev, horizon_s=cut)
                work = len(trajectory.time_s) * view.radial_cells
            except (RuntimeError, ValueError, ArithmeticError) as error:
                status, reason = "failed", _native_failure(error)
            for cut in request.horizons:
                rows.append(TrialRow(unit_id=unit_id, action=fraction, horizon=cut, receiver_id="simulator_temperature_change_ev",
                                     features=feature_vector("R22", preparation, fraction, cut), outcome=values.get(cut), status=status,
                                     reason=reason, work_units=work / len(request.horizons),
                                     diagnostics=(("requested_power_w", float(power)),)))
    return TrialBatch("R22", request.split, tuple(rows), "archive-and-native",
                      (f"physical-source:{cohort.source_id}", f"physical-sha256:{cohort.content_sha256}",
                       "physical-exposure:recorded-archive", *versions, f"device:{request.device}",
                       "native-source:direct-TORAX-gaussian-heat-proxy", "mapping-assumptions-authored-per-unit",
                       "separate-physical-and-simulator-receivers", "no-unqualified-physical-transport-claim"))


class NativeJointDescriptionPort:
    """Concrete adapter for the runner's one entered native request.

    Construct only inside the typed native worker. Reuse of returned evidence,
    interruption recovery, and permissions remain the runner's responsibility.
    """

    def acquire(self, request):
        if request.family_id in {"R17", "R18", "R19"} and (request.input_json is not None or request.input_path is not None):
            raise ValueError("fresh native simulator preparations do not consume an archive")
        parameters = resolve_parameters(request)
        if request.family_id in {"R18", "R19"}:
            return _acquire_battery(request, parameters)
        if request.family_id == "R17":
            return _acquire_gym(request, parameters)
        if request.family_id == "R22":
            return _acquire_bridge(request, parameters)
        raise ValueError("native adapter does not own this family")
