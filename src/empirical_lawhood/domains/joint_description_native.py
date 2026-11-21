"""Declarative scientific assays for recorded and native preprint-inspired families.

Definitions describe new experiments. No original result, fitted coefficient or
historical case roster is an operand. Engine contact is injected by execution.
"""

from __future__ import annotations

from collections.abc import Mapping
from hashlib import sha256
import json
import math

import numpy as np


DEFAULT_CURRENT_TRACKING_TOLERANCE_A = 1e-6

PREPARATION_FIELDS = {
    "R13": ("baseline_hz", "history_hz", "resistance_mohm"),
    "R14": ("baseline_angle_rad", "history_angle_rad", "resonance_hz"),
    "R15": ("history_current_a", "initial_soc", "initial_temperature_k"),
    "R16": ("baseline_density_1e19_m3", "baseline_gas_rate", "history_receiver"),
    "R17": ("bootstrap_multiplier", "density_nbar", "inner_transport_scale", "temperature_scale"),
    "R18": ("history_current_a", "initial_soc", "initial_temperature_k"),
    "R19": ("history_current_a", "initial_soc", "initial_temperature_k"),
    "R22": ("core_temperature_ev", "density_1e19_m3", "heating_power_w", "history_temperature_ev"),
}

RECEIVERS = {
    "R13": ("firing_rate_hz",),
    "R14": ("displacement_rad",),
    "R15": ("terminal_voltage_v", "discharge_capacity_ah"),
    "R16": ("response_real", "response_imag"),
    "R17": ("fusion_gain",),
    "R18": ("terminal_voltage_v", "discharge_capacity_ah", "peak_temperature_k"),
    "R19": ("voltage_reduction_defect_v", "temperature_reduction_defect_k"),
    "R22": ("archive_temperature_change_ev", "simulator_temperature_change_ev"),
}

PRIMARY_STATE = {"R13": "resistance_mohm", "R14": "resonance_hz", "R15": "initial_soc",
                 "R16": "baseline_density_1e19_m3", "R17": "temperature_scale", "R18": "initial_soc",
                 "R19": "initial_soc", "R22": "core_temperature_ev"}


def feature_vector(family_id: str, preparation: Mapping[str, float], action: float, horizon: float):
    """Expose only preparation/history/action/horizon; outcomes stay in diagnostics."""
    fields = PREPARATION_FIELDS[family_id]
    values = {name: float(preparation[name]) for name in fields}
    # These are declared algebraic interface coordinates, not fitted features.
    first, last = next((name for name in fields if name.startswith("history_")), fields[0]), PRIMARY_STATE[family_id]
    values.update(action=float(action), horizon=float(horizon),
                  action_x_state=float(action * values[last]),
                  action_x_context=float(action * values[first]),
                  state_x_context=float(values[first] * values[last]))
    return tuple(sorted(values.items()))


def _descriptions(family_id):
    fields = PREPARATION_FIELDS[family_id]
    memory = int(any(name.startswith("history_") for name in fields))
    base = ["action", "horizon", PRIMARY_STATE[family_id]]
    additive = ["action", "horizon", *fields]
    descriptions = [
        {"id": "minimal", "features": base, "model": "ridge", "state_dimension": 1,
         "interface_dimension": 0, "memory_samples": 0, "memory_dimension": 0,
         "rationale": "Test whether one instantaneous state coordinate supports this action/receiver family."},
        {"id": "additive", "features": additive, "model": "ridge", "state_dimension": len(fields) - memory,
         "interface_dimension": 0, "memory_samples": memory, "memory_dimension": memory,
         "rationale": "Separate additive preparation and retained-history coordinates; no multiplicative interface."},
        {"id": "interface", "features": [*additive, "action_x_state", "action_x_context"], "model": "ridge",
         "state_dimension": len(fields) - memory, "interface_dimension": 2, "memory_samples": memory, "memory_dimension": memory,
         "rationale": "Pay for explicit action/state and action/history interface dependence."},
        {"id": "joint", "features": [*additive, "action_x_state", "action_x_context", "state_x_context"],
         "model": "ridge", "state_dimension": len(fields) - memory, "interface_dimension": 3,
         "memory_samples": memory, "memory_dimension": memory,
         "rationale": "Joint second-order description is an authored candidate, not an assertion of global minimality."},
    ]
    for description in descriptions:
        dimension = len(description["features"])
        products = sum("_x_" in name for name in description["features"])
        description.update(
            forecast_work_units=float(2 * dimension + products),
            forecast_work_unit="normalized-scalar-operation",
            forecast_work_basis=(f"Authored per-receiver inference estimate: {dimension} coordinate accesses, "
                                 f"{dimension} coordinate conversions, {products} explicit interface products; "
                                 "excludes final frozen predictor evaluation, shared raw/native acquisition and calibration fitting; "
                                 "not measured runtime."))
    return descriptions


def _policy(units, target, scale, error, lower=None, upper=None):
    result = dict(units=units, target=target, scale=scale, max_abs_error=error, weight=1.0)
    if lower is not None:
        result["safety_lower"] = lower
    if upper is not None:
        result["safety_upper"] = upper
    return result


def presets():
    """Complete editable scientific defaults; numerical values are design choices."""
    definitions = (
        ("R13", "Cortical recorded action options", "Which preparation, history and current-action coordinates preserve useful firing-rate selection?",
         [-40.0, 40.0, 80.0], [0.5, 1.0], {}, {"firing_rate_hz": _policy("Hz", 10, 10, 2, 0, 100)}),
        ("R14", "Signed optical-mirror control", "How much state, history and action-sign information is required for useful mirror displacement predictions?",
         [-0.1, 0.0, 0.1], [0.1, 0.2], {}, {"displacement_rad": _policy("rad", 0.001, 0.001, 0.0002, -0.02, 0.02)}),
        ("R15", "Physical battery prediction", "Which joint description maintains voltage and capacity error promises across recorded cells?",
         [0.5, 1.0, 2.0], [60.0, 120.0], {"current_tracking_tolerance_a": DEFAULT_CURRENT_TRACKING_TOLERANCE_A}, {
             "terminal_voltage_v": _policy("V", 3.7, 0.5, 0.05, 2.5, 4.3),
             "discharge_capacity_ah": _policy("A.h", 0.05, 0.05, 0.005, 0)}),
        ("R16", "MAST-U modulation susceptibility", "Which state and interface coordinates preserve the complex divertor response across requested modulation frequencies?",
         [5.0, 10.0, 20.0], [1.0], {}, {
             "response_real": _policy("W.m^-2/(Pa.m^3.s^-1)", 0, 1, 0.2),
             "response_imag": _policy("W.m^-2/(Pa.m^3.s^-1)", 0, 1, 0.2)}),
        ("R17", "Fresh Gym-TORAX action efficacy", "How much coupled preparation information is needed to forecast and select effective heating actions in Gym-TORAX?",
         [-0.05, 0.0, 0.05], [2.0, 4.0], {
             "nbi_power_w": 30e6, "plasma_current_a": 12.5e6, "ecrh_power_w": 20e6,
             "nbi_location": 0.25, "nbi_width": 0.25, "ecrh_location": 0.35, "ecrh_width": 0.05,
             "temperature_scale_range": [0.99, 1.02], "density_nbar_range": [0.848, 0.852],
             "bootstrap_multiplier_range": [0.99, 1.005], "inner_transport_scale_range": [0.99, 1.01],
             "radial_cells": 25, "internal_timestep_s": 1.0, "corrector_steps": 10,
             "expected_versions": {"gymtorax": "1.1.1", "torax": "1.4.2", "jax": "0.10.2", "jaxlib": "0.10.2"}},
         {"fusion_gain": _policy("dimensionless", 10, 10, 1, 0)}),
        ("R18", "Fresh PyBaMM action efficacy", "Which preparation/history description supports useful current-action selection without violating voltage or temperature limits?",
         [0.5, 1.0, 2.0], [60.0, 120.0], {}, {
             "terminal_voltage_v": _policy("V", 3.7, 0.5, 0.05, 2.5, 4.3),
             "discharge_capacity_ah": _policy("A.h", 0.05, 0.05, 0.005, 0),
             "peak_temperature_k": _policy("K", 298.15, 10, 1, 273.15, 323.15)}),
        ("R19", "PyBaMM reduced-model continuation", "When does an SPMe continuation preserve the DFN voltage/temperature promise, and where do state/history omissions cause costly error?",
         [0.5, 1.0, 2.0], [60.0, 120.0], {}, {
             "voltage_reduction_defect_v": _policy("V", 0, 0.05, 0.02, 0, 0.05),
             "temperature_reduction_defect_k": _policy("K", 0, 1, 0.5, 0, 1)}),
        ("R22", "MAST archive and native TORAX bridge", "Which recorded-state information and declared transport assumptions preserve separate physical and simulated heating-response predictions?",
         [-0.1, 0.0, 0.1], [0.02, 0.04], {
             "radial_cells": 12, "internal_timestep_s": 0.002,
             "expected_versions": {"torax": "1.4.2", "jax": "0.10.2", "jaxlib": "0.10.2"}},
         {"archive_temperature_change_ev": _policy("eV", 10, 100, 20),
          "simulator_temperature_change_ev": _policy("eV", 10, 100, 20)}),
    )
    result = []
    for family, title, question, actions, horizons, parameters, policies in definitions:
        if family in {"R18", "R19"}:
            parameters = {"initial_soc_range": [0.35, 0.8], "initial_temperature_k_range": [293.15, 303.15],
                          "history_current_a_range": [0.0, 1.0], "history_duration_s": 30.0,
                          "parameter_set": "Chen2020", "spatial_points": 12,
                          "rtol": 1e-6, "atol": 1e-8, "sample_interval_s": 5.0,
                          "expected_versions": {"pybamm": "26.6.2.0"}}
        result.append({"family_id": family, "title": title, "question": question,
                       "receivers": list(RECEIVERS[family]), "receiver_policies": policies,
                       "parameters": parameters, "actions": actions, "horizons": horizons,
                       "calibration_units": 12, "evaluation_units": 6,
                       "descriptions": _descriptions(family),
                       "source_kind": "recorded-archive" if family in {"R13", "R14", "R15", "R16"} else
                                      "archive-and-native" if family == "R22" else "fresh-native-simulation"})
    return tuple(result)


def selected_receivers(request):
    """Validate the declared receiver census independently of acquisition."""
    if request.family_id not in RECEIVERS:
        raise ValueError("this producer does not own the requested family")
    receivers = request.parameters.get("receivers", RECEIVERS[request.family_id])
    if (not isinstance(receivers, (list, tuple)) or not receivers
            or any(not isinstance(receiver, str) for receiver in receivers)
            or len(set(receivers)) != len(receivers)
            or not set(receivers) <= set(RECEIVERS[request.family_id])):
        raise ValueError("selected receivers must be a nonempty unique subset of the family instrument")
    if request.family_id == "R22" and set(receivers) != set(RECEIVERS["R22"]):
        raise ValueError("R22 bridge requires both separate physical and native receivers")
    return tuple(receivers)


def resolve_parameters(request):
    selected_receivers(request)
    defaults = next(value["parameters"] for value in presets() if value["family_id"] == request.family_id)
    optional = {"recorded_power_tracking"} if request.family_id == "R22" else set()
    unknown = set(request.parameters) - set(defaults) - {"receivers"} - optional
    if unknown:
        raise ValueError(f"unknown family scientific parameters: {sorted(unknown)}")
    result = {**defaults, **{key: value for key, value in request.parameters.items() if key != "receivers"}}
    if "recorded_power_tracking" in result:
        tracking = result["recorded_power_tracking"]
        if (not isinstance(tracking, Mapping)
                or set(tracking) != {"max_fraction_error", "max_power_gap_s", "max_temperature_gap_s"}
                or any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)
                       for v in tracking.values())
                or tracking["max_fraction_error"] < 0 or min(tracking["max_power_gap_s"], tracking["max_temperature_gap_s"]) <= 0):
            raise ValueError("measured NBI requires a nonnegative tracking error and two positive clock-gap limits")
        commands = sorted(request.actions)
        tolerance = tracking["max_fraction_error"]
        if (any(0 < abs(command) <= tolerance for command in commands)
                or any(right - left <= 2 * tolerance for left, right in zip(commands, commands[1:]))):
            raise ValueError("measured NBI tracking bands must preserve sign and remain disjoint")
    if request.family_id == "R15":
        tolerance = result["current_tracking_tolerance_a"]
        if (isinstance(tolerance, bool) or not isinstance(tolerance, (int, float))
                or not math.isfinite(tolerance) or tolerance < 0):
            raise ValueError("battery current tracking tolerance must be finite and nonnegative in A")
        if tolerance > DEFAULT_CURRENT_TRACKING_TOLERANCE_A:
            commands = sorted(request.actions)
            if (any(0 < abs(command) <= tolerance for command in commands)
                    or any(right - left <= 2 * tolerance for left, right in zip(commands, commands[1:]))):
                raise ValueError("widened battery tracking bands must preserve command sign and remain disjoint")
    if request.family_id == "R17":
        power = result["nbi_power_w"]
        if isinstance(power, bool) or not isinstance(power, (int, float)) or not math.isfinite(power):
            raise ValueError("Gym-TORAX NBI preparation power must be finite")
        if any(not -0.5 <= action <= 0.5 or not 0 <= power * (1 + action) <= 33e6 for action in request.actions):
            raise ValueError("Gym-TORAX action menu leaves the native heating envelope")
        if any(horizon != int(horizon) or not 1 <= horizon <= 120 for horizon in request.horizons):
            raise ValueError("Gym-TORAX receiver horizons must be integer seconds in [1,120]")
    if request.family_id in {"R18", "R19"}:
        if any(not -10 <= action <= 10 for action in request.actions) or max(request.horizons) > 3600:
            raise ValueError("PyBaMM action/horizon menu exceeds its declared acquisition envelope")
    return result


def validate_specification(specification):
    """Check authored feature channels and native menu bounds without engine contact."""
    from empirical_lawhood.science.joint_description import TrialRequest

    family = specification.family_id
    if family not in PREPARATION_FIELDS:
        raise ValueError("Native/recorded feature owner received another scientific family")
    parameters = json.loads(specification.parameters_json)
    receivers = tuple(receiver.receiver_id for receiver in specification.receivers)
    if "receivers" in parameters:
        declared = parameters["receivers"]
        if not isinstance(declared, (list, tuple)) or tuple(declared) != receivers:
            raise ValueError("Receiver policy selection conflicts with the reserved receiver declaration")
    parameters["receivers"] = receivers
    request = TrialRequest(family, specification.seed, specification.calibration_unit_ids,
        "calibration", tuple(float(value) for value in specification.actions),
        tuple(float(value) for value in specification.horizons), parameters)
    resolve_parameters(request)
    fields = set(PREPARATION_FIELDS[family])
    history = {name for name in fields if name.startswith("history_")}
    products = {"action_x_state", "action_x_context", "state_x_context"}
    available = fields | products | {"action", "horizon"}
    for description in specification.descriptions:
        selected = set(description.features)
        if not selected <= available or description.model != "ridge":
            raise ValueError("Recorded/native feature descriptions require declared causal coordinates and calibration-only ridge")
        memory_dimension = len(selected & history)
        expected = (len(selected & (fields - history)), len(selected & products),
                    memory_dimension, int(memory_dimension > 0))
        observed = (description.state_dimension, description.interface_dimension,
                    description.memory_dimension, description.memory_samples)
        if observed != expected:
            raise ValueError(f"Recorded/native information dimensions differ for {description.description_id}: expected {expected}")
        minimum_work = 2 * len(selected) + len(selected & products)
        if (description.forecast_work_unit != "normalized-scalar-operation"
                or description.forecast_work_units < minimum_work):
            raise ValueError("Recorded/native construction work must cover its explicit coordinate and cross-product estimate")


def preparation_rng(request, unit_id):
    payload = f"{request.family_id}\0{request.seed}\0{request.split}\0{unit_id}".encode()
    return np.random.default_rng(int.from_bytes(sha256(payload).digest()[:8], "big"))


def sample_preparation(request, unit_id, parameters):
    """Fresh authored simulator preparation, independent of any action outcome."""
    rng = preparation_rng(request, unit_id)
    values = {}
    for name in PREPARATION_FIELDS[request.family_id]:
        bounds = parameters.get(name + "_range")
        if not isinstance(bounds, (list, tuple)) or len(bounds) != 2:
            raise ValueError(f"native preparation range missing: {name}")
        lower, upper = bounds
        if not all(isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) for x in bounds) or lower > upper:
            raise ValueError(f"native preparation range invalid: {name}")
        values[name] = float(rng.uniform(lower, upper))
    if "initial_soc" in values and not 0 < values["initial_soc"] < 1:
        raise ValueError("native battery initial SOC must lie in (0,1)")
    if any(values[name] <= 0 for name in values if name != "history_current_a"):
        raise ValueError("native preparation coordinates must be positive")
    return values


def prepare_predictors(request, *, native_port=None):
    """Prepare a complete outcome-free table before the forecast is frozen.

    Physical files are already exposed archives: only their explicit pre-action
    declarations enter this table. No receiver reducer or native engine is called.
    The execution graph must reject any later feature substitution.
    """
    del native_port
    from empirical_lawhood.science.joint_description import TrialBatch, TrialRow
    parameters = resolve_parameters(request)
    receivers = selected_receivers(request)
    archive = request.family_id in {"R13", "R14", "R15", "R16", "R22"}
    if archive:
        from empirical_lawhood.adapters.physical.joint_description import cohort_from_request
        cohort = cohort_from_request(request)
        preparations = {unit_id: cohort.selected_unit(unit_id, request.split)["preparation"]
                        for unit_id in request.unit_ids}
        provenance = (f"source:{cohort.source_id}", f"sha256:{cohort.content_sha256}", "recorded-archive-pre-action-coordinates")
        source_kind = "archive-and-native" if request.family_id == "R22" else "recorded-archive"
    else:
        if request.input_path is not None or request.input_json is not None:
            raise ValueError("fresh native simulator preparations do not consume an archive")
        preparations = {unit_id: sample_preparation(request, unit_id, parameters) for unit_id in request.unit_ids}
        provenance = ("fresh-authored-preparations", "no-native-contact", "no-outcome-derived-features")
        source_kind = "fresh-native-simulation"
    rows = tuple(TrialRow(unit_id=unit_id, action=action, horizon=horizon, receiver_id=receiver,
                          features=feature_vector(request.family_id, preparations[unit_id], action, horizon),
                          outcome=None, status="unsupported", reason="not-yet-acquired")
                 for unit_id in request.unit_ids for action in request.actions for horizon in request.horizons
                 for receiver in receivers)
    return TrialBatch(request.family_id, request.split, rows, source_kind, provenance)


def produce(request, *, native_port=None):
    if request.family_id in {"R13", "R14", "R15", "R16"}:
        from empirical_lawhood.adapters.physical.joint_description import produce_archive
        return produce_archive(request)
    if request.family_id not in {"R17", "R18", "R19", "R22"}:
        raise ValueError("this producer does not own the requested family")
    if native_port is None:
        raise ValueError("native experiment requires the typed execution runner's native port")
    return native_port.acquire(request)
