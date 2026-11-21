"""Fresh R03--R12 experiments, composed from reusable matrix science.

These are new declared trial populations. Historical result files, selected
paper events and campaign entry points are neither consulted nor wrapped. The
caller separates calibration and evaluation; the functions here never fit or
select on either tranche's outcomes. Every requested cell has an outcome row.
"""
from __future__ import annotations

from dataclasses import fields, replace
from hashlib import sha256
import json

import numpy as np
from scipy.linalg import expm

from empirical_lawhood.science.joint_description import TrialBatch, TrialRequest, TrialRow
from empirical_lawhood.domains.matrix.matrix_history_analysis.algebra import operator
from empirical_lawhood.domains.matrix.six_matrix_response.model import hermitian_part

from .instruments import (
    algebra_observation, causal_passive_transfer, describe_prefix,
    directional_passive_transfer, first_passage, geometry_admission,
    geometry_observation, radial_increment, response_receiver,
)
from .mechanisms import deterministic_forecast, radial_forecast
from .native import (
    CONSTITUTIONS, MatrixSettings, acquire_prefix, causal_tangent_forecast,
    force_direction, native_path, noise_tape, paired_refinement, realized_tangent,
)


_TITLES = {
    "R03": "Structural feasibility and joint-description scope",
    "R04": "Causally selected events and conditional commitment",
    "R05": "Approximate algebra persistence across decompositions",
    "R06": "Directional passive transfer and discarded interfaces",
    "R07": "Coupled tangent versus scalar finite-response descriptions",
    "R08": "Radial preparation increments and cross-sector information",
    "R09": "Absolute baseline, response increment and support",
    "R10": "Forecast-mediated composition with a fixed response mechanism",
    "R11": "Preparation-mediated composition with a fixed response mechanism",
    "R12": "Preparation and response numerical-sensitivity diagnosis",
}
_QUESTIONS = {
    "R03": "Which preparation and action scope admits a useful geometry description, and where does removing cross-sector information move its prediction error?",
    "R04": "Given a checkpoint selected only from its past, is a local, interface-augmented, remembered or joint description sufficient for conditional commitment?",
    "R05": "Does approximate algebra persist prospectively, and which joint, interface or memory information is needed when a scalar geometry summary is inadequate?",
    "R06": "When full passive response is decomposed into scalar directions, how much omitted operator coupling must be restored as interface information or memory?",
    "R07": "When does a full coupled origin Hessian predict signed finite response economically better than a local scalar curvature, and can interface information repair the reduction?",
    "R08": "Can a radial preparation-increment law remain useful after other-sector dynamics are removed, or is their influence paid as interface data, memory or error?",
    "R09": "Can an increment description meet absolute-state decisions without carrying its baseline and declared preparation support?",
    "R10": "Can a causally forecast handoff supply the joint description needed by an unchanged lower response mechanism, and what does its decomposition cost?",
    "R11": "Can a parent preparation supply conditions for an unchanged lower response mechanism, with interface and memory costs included?",
    "R12": "Are apparent description savings stable under physically paired native timestep refinement, including failed preparation and response outcomes?",
}
_BASE = ("context.action", "context.horizon", "context.preparation", "context.alpha-x", "context.alpha-y")
_LOCAL = tuple(f"local.{i:03d}" for i in range(96))
_INTERFACE = tuple(f"interface.{i:03d}" for i in range(8))
_MEMORY = tuple(f"memory.{i:03d}" for i in range(192))
_JOINT = tuple(f"joint.{i:03d}" for i in range(192))


def _description(identifier, features, *, model="ridge", state=0, interface=0, samples=0, memory=0, rationale,
                 work=0, work_basis="Copied declared coordinates; final linear evaluator is charged separately."):
    return {"id": identifier, "features": tuple(features), "model": model,
            "state_dimension": state, "interface_dimension": interface,
            "memory_samples": samples, "memory_dimension": memory, "rationale": rationale,
            "forecast_work_units": work, "forecast_work_unit": "normalized-scalar-operation",
            "forecast_work_basis": work_basis}


def _structural_descriptions():
    return (
        _description("local", (*_BASE, *_LOCAL), state=96, rationale="One sector's complete local phase coordinates; the other sector is unobserved.",
                     work=96 * 128, work_basis="Authored estimate:96 local HS projections times16 complex entries times8 real operations; excludes shared native prefix and calibration."),
        _description("local-interface", (*_BASE, *_LOCAL, *_INTERFACE), state=96, interface=8,
                     rationale="Restore explicit cross-commutator and coupled-curvature measurements.",
                     work=96 * 128 + 2 * 600 * 8 * 4**3 + 18 * 8 * 4**3,
                     work_basis="Authored conservative estimate:local HS projection plus two Hessian images (600 complex4x4 products each) and18 commutator products; not a benchmark."),
        _description("local-memory", (*_BASE, *_LOCAL, *_MEMORY), state=96, samples=2, memory=96,
                     rationale="Retain two declared past local phase samples without observing the other sector.",
                     work=3 * 96 * 128, work_basis="Authored estimate:three96-coordinate HS projections, present plus two past lags; excludes shared native prefix and fitting."),
        _description("joint", (*_BASE, *_JOINT), state=192,
                     rationale="Keep both sectors and momenta as one joint description with 192 real coordinates.",
                     work=192 * 128, work_basis="Authored estimate:192 HS projections times16 complex entries times8 real operations; excludes shared native prefix and calibration."),
    )


def _mechanism_descriptions(family, *, steps=32, parent_steps=8, memory_depth=2):
    if family == "R06":
        return (
            _description("scalar", ("forecast.local",), model="fixed", state=1,
                         rationale="Trace-average scalar generator discards all directional coupling.",
                         work=3 * 16 * 16 + 32, work_basis="Authored estimate:trace-centering and norms of three4x4 matrices plus one scalar exponential budget32; no measured runtime claim."),
            _description("joint-operator", ("forecast.joint",), model="fixed", state=120,
                         rationale="Full symmetric 15-dimensional origin generator retains directional interfaces.",
                         work=3 * 15 * (2 * 8 * 4**3 + 15 * 8 * 16) + 20 * 15**3,
                         work_basis="Authored estimate:full15-dimensional commutator Gram construction plus20 dense15-cubed exponential operations; not measured."),
            _description("operator-memory", ("forecast.memory",), model="fixed", state=120, samples=memory_depth, memory=120,
                         rationale="Two causal operator samples extrapolate drift; PSD clipping is declared.",
                         work=(memory_depth + 1) * (3 * 15 * (2 * 8 * 4**3 + 15 * 8 * 16)) + 40 * 15**3 + (memory_depth + 1) * 15**2 * 20,
                         work_basis="Authored estimate:three complete origin/past operators, quadratic drift fit, PSD spectral projection and matrix exponential; each dense decomposition budget20*15^3."),
        )
    # Explicit design assumptions, deliberately not timings. A complex4x4
    # product is budgeted as8*4^3 real scalar operations; gradient/Hessian
    # images have conservative300/600-product estimates. Reauthor these costs
    # whenever dt, horizon, memory depth or the implemented mechanism changes.
    gradient, hessian = 300 * 8 * 4**3, 600 * 8 * 4**3
    scalar = hessian + steps * 96 * 12
    joint = (2 * steps + 1) * hessian + steps * 96 * 12
    if family in ("R08", "R09"):
        scalar = 8 * gradient + 160 * steps
        joint = 2 * (steps + 1) * gradient + 16 * steps * 96
    elif family in ("R10", "R11", "R12"):
        scalar += 4 * gradient + 40 * parent_steps
        joint += (parent_steps + 1) * gradient + 8 * parent_steps * 96
    basis = ("Authored normalized real-operation estimate at q=2,max_horizon=0.064,dt=0.002,parent_steps=8:"
             "complex4x4 product8*4^3; gradient300 products; Hessian600 products; radial cubic coefficient construction4 gradients."
             " Reauthor if scope/numerics change; excludes shared native acquisition and calibration; not a benchmark.")
    return (
        _description("local-mechanism", ("forecast.local",), model="fixed", state=48 if family == "R07" else 96,
                     rationale="Local scalar/radial mechanism discards the hidden-sector dynamical interface.", work=scalar, work_basis=basis),
        _description("interface-mechanism", ("forecast.interface",), model="fixed", state=48 if family == "R07" else 96, interface=48,
                     rationale="Retain the hidden sector as a frozen interface rather than evolving the full joint state.", work=scalar, work_basis=basis),
        _description("memory-mechanism", ("forecast.memory",), model="fixed", state=48, samples=memory_depth, memory=48,
                     rationale="Supply a causal history-based velocity or upstream extrapolation to the same local mechanism.", work=scalar + (memory_depth + 1) * 48 * 20, work_basis=basis + " Causal local-position history polynomial fit adds (memory_depth+1)*48*20 operations."),
        _description("joint-mechanism", ("forecast.joint",), model="fixed", state=96 if family == "R07" else 192,
                     rationale="Compose the unchanged native constitutive or full coupled linearized mechanism on the joint state.", work=joint, work_basis=basis),
    )


def _receivers(family):
    return {
        "R03": ("x-gap", "y-gap", "joint-gap", "xy-angle", "x-admitted", "y-admitted", "joint-admitted"),
        "R04": ("commitment", "occupation"),
        "R05": ("associative-leakage", "lie-leakage", "band-ratio", "commutant-mixing", "algebra-survival"),
        "R06": tuple(f"direction.{i:02d}" for i in range(15)),
        "R07": ("signed-response", "transverse-response"),
        "R08": ("radial-increment",),
        "R09": ("absolute-position",),
        "R10": ("signed-response",),
        "R11": ("signed-response", "service"),
        "R12": ("signed-response", "service"),
    }[family]


def presets() -> tuple[dict, ...]:
    """Researcher-editable new designs, with no historical population assertion."""
    result = []
    for family, title in _TITLES.items():
        receivers = _receivers(family)
        parameters = {
            "dt": 0.002, "prefix_steps": 32, "history_stride": 4, "memory_depth": 2,
            "mass": 0.5, "cross_coupling": 1.0, "alpha_x": 1.0, "alpha_y": 2.0,
            "friction": 1.0, "temperature": 0.15, "position_jitter": 0.03,
            "momentum_jitter": 0.03, "preparations": tuple(CONSTITUTIONS),
            "direction": "x-radial", "observed_sector": 0,
            "maximum_band_ratio": 0.35, "maximum_associative_leakage": 0.15,
            "minimum_joint_angle_degrees": 60.0,
            "persistence_steps": 2, "shooting_replicates": 4, "kappa": 0.2,
            "handoff_steps": 8, "downstream_amplitude": 0.1,
            "service_threshold": 0.00001, "support_radius_limit": 100.0,
        }
        if family == "R04":
            parameters["preparations"] = ("product", "x-factor", "y-factor")
            parameters["observed_sector"] = 1
        if family == "R06":
            parameters["observed_sector"] = 1
        policies = {}
        for receiver in receivers:
            probability = receiver in ("commitment", "occupation", "algebra-survival", "service", "x-admitted", "y-admitted", "joint-admitted")
            if probability:
                policies[receiver] = {"units": "probability", "target": 1.0, "scale": 1.0,
                                      "max_abs_error": 0.2, "weight": 1.0}
            elif family == "R06":
                policies[receiver] = {"units": "passive-HS-coordinate", "target": 0.5,
                                      "scale": 1.0, "max_abs_error": 0.1, "weight": 1 / 15}
            elif family in ("R07", "R10", "R11", "R12"):
                policies[receiver] = {"units": "native-HS-displacement", "target": 0.0001,
                                      "scale": 0.0001, "max_abs_error": 0.00005, "weight": 1.0}
            elif family == "R08":
                policies[receiver] = {"units": "native-radius-squared", "target": 0.0,
                                      "scale": 0.01, "max_abs_error": 0.01, "weight": 1.0}
            else:
                policies[receiver] = {"units": "dimensionless" if family in ("R03", "R05") else "native-HS-position",
                                      "target": 0.0, "scale": 1.0, "max_abs_error": 0.1, "weight": 1 / len(receivers)}
        result.append({"family_id": family, "title": title, "question": _QUESTIONS[family],
            "receivers": receivers, "receiver_policies": policies, "parameters": parameters,
            "actions": (-0.1, 0.0, 0.1) if family != "R06" else (0.5, 1.0),
            "horizons": (0.032, 0.064), "calibration_units": 48, "evaluation_units": 32,
            "descriptions": _structural_descriptions() if family in ("R03", "R04", "R05") else _mechanism_descriptions(family)})
    return tuple(result)


def _rng(request, unit_id, purpose):
    digest = sha256(f"new-matrix-joint-description-v1\0{request.family_id}\0{request.seed}\0{request.split}\0{unit_id}\0{purpose}".encode()).digest()
    return np.random.Generator(np.random.PCG64DXSM(int.from_bytes(digest[:16], "big")))


def preparation_for_unit(request, unit_id, preparations):
    """Draw one preparation uniformly from a root's separately seeded stream.

    Assignment depends on the scientific root identity, never its position in
    an invocation. The runtime may partition roots into any number of subworks
    without changing their preparation or later predictor bytes.
    """
    index = int(_rng(request, unit_id, "preparation-assignment").integers(len(preparations)))
    return preparations[index]


def _steps(horizon, settings):
    result = int(round(float(horizon) / settings.dt))
    if result < 1 or abs(result * settings.dt - float(horizon)) > 1e-10 * max(1.0, abs(float(horizon))):
        raise ValueError("Matrix horizons must be positive integer multiples of the declared native dt")
    return result


def _description_operand(history, settings, direction, parameters):
    return describe_prefix(history, settings, direction=direction,
        observed_sector=int(parameters["observed_sector"]), memory_depth=int(parameters["memory_depth"]))


def _features(settings, preparation, action, horizon, description):
    result = dict(zip(_BASE, (action, horizon, float(tuple(CONSTITUTIONS).index(preparation)),
                            settings.alpha_x, settings.alpha_y), strict=True))
    for prefix, values in (("local", description.local), ("interface", description.interface),
                           ("memory", description.memory), ("joint", description.joint)):
        result.update((f"{prefix}.{i:03d}", float(value)) for i, value in enumerate(values))
    return result


def _row(request, unit, action, horizon, receiver, features, outcome, *, reason="", status="supported", diagnostics=(), work=0.0):
    values = tuple(sorted((name, float(value)) for name, value in features.items()))
    diagnostic_values = tuple(sorted((name, float(value)) for name, value in diagnostics))
    if not np.isfinite([value for _, value in values]).all():
        status, reason, outcome = "failed", "NONFINITE_CAUSAL_DESCRIPTION", None
        values = ()
    if outcome is not None and not np.isfinite(outcome):
        status, reason, outcome = "failed", "NONFINITE_RECEIVER", None
    return TrialRow(unit_id=unit, action=float(action), horizon=float(horizon), receiver_id=receiver,
        features=values, outcome=None if outcome is None else float(outcome), status=status, reason=reason,
        work_units=float(work), diagnostics=diagnostic_values)


def _all_failed(request, unit, receivers, reason, *, status="failed"):
    return [_row(request, unit, action, horizon, receiver, {}, None, status=status, reason=reason)
            for action in request.actions for horizon in request.horizons for receiver in receivers]


def _available_forecasts(tasks):
    """One lossy predictor may fail without erasing a measured native outcome."""
    available, reasons = {}, []
    for name, task in tasks.items():
        try:
            available[name] = task()
        except (FloatingPointError, OverflowError, np.linalg.LinAlgError) as exc:
            reasons.append(f"PREDICTOR_UNAVAILABLE:{name}:{type(exc).__name__}")
    return available, ";".join(reasons)


def _local_origin(origin, observed_sector, *, velocity_from=None, settings=None):
    positions, momenta = np.zeros_like(origin.positions), np.zeros_like(origin.momenta)
    positions[observed_sector] = origin.positions[observed_sector]
    momenta[observed_sector] = origin.momenta[observed_sector]
    if velocity_from is not None:
        elapsed = (origin.step_index - velocity_from.step_index) * settings.dt
        if elapsed <= 0:
            raise ValueError("Memory origin must strictly precede the forecasting cutoff")
        momenta[observed_sector] = (origin.positions[observed_sector] - velocity_from.positions[observed_sector]) / elapsed
    return replace(origin, positions=hermitian_part(positions), momenta=hermitian_part(momenta))


def _memory_origin(history, settings, depth, observed_sector=None):
    """Fit a causal degree-at-most-two local time polynomial to all declared lags."""
    times = -np.arange(depth + 1, dtype=float) * settings.history_stride * settings.dt
    design = np.column_stack([times**power for power in range(min(2, depth) + 1)])
    positions = np.asarray([history[-1 - lag * settings.history_stride].positions
                            if observed_sector is None else history[-1 - lag * settings.history_stride].positions[observed_sector]
                            for lag in range(depth + 1)])
    coefficients = np.linalg.lstsq(design, positions.reshape(depth + 1, -1), rcond=None)[0]
    momenta = np.zeros_like(history[-1].momenta)
    if observed_sector is None:
        momenta[:] = coefficients[1].reshape(2, 3, 4, 4)
    else:
        momenta[observed_sector] = coefficients[1].reshape(3, 4, 4)
    return replace(history[-1], momenta=hermitian_part(momenta))


def _tangent_predictions(origin, memory_origin, settings, direction, steps, observed_sector, amplitude):
    local = _local_origin(origin, observed_sector)
    memory = _local_origin(memory_origin, observed_sector)
    # A local history supplies a causal extrapolated position before freezing its Hessian.
    memory = replace(memory, positions=hermitian_part(memory.positions + steps * settings.dt * memory.momenta / 2))
    return _available_forecasts({
        "local": lambda: amplitude * causal_tangent_forecast(local, settings, direction=direction, steps=steps, scalar_curvature=True),
        "interface": lambda: amplitude * causal_tangent_forecast(origin, settings, direction=direction, steps=steps, scalar_curvature=True),
        "memory": lambda: amplitude * causal_tangent_forecast(memory, settings, direction=direction, steps=steps, scalar_curvature=True),
        "joint": lambda: amplitude * causal_tangent_forecast(origin, settings, direction=direction, steps=steps),
    })


def _structural_rows(request, unit, history, settings, parameters, preparation, direction, receivers, *, predictors_only=False):
    family, observed = request.family_id, int(parameters["observed_sector"])
    criteria = {"sector_index": observed, "maximum_band_ratio": float(parameters["maximum_band_ratio"]),
                "maximum_associative_leakage": float(parameters["maximum_associative_leakage"])}
    if family == "R04":
        # Every eligibility decision precedes its shooting futures. Earliest admissible
        # checkpoint is a stopping-time rule, never an argmax over future outcomes.
        minimum = int(parameters["memory_depth"]) * settings.history_stride
        matches = [i for i in range(max(1, minimum), len(history)) if geometry_admission(history[i], **criteria)[0]]
        if not matches:
            return _all_failed(request, unit, receivers, "CONDITIONAL_NONENTRY_NO_PAST_ADMITTED_EVENT", status="unsupported")
        history = history[:matches[0] + 1]
        direction = force_direction(history[-1], str(parameters["direction"]))
    origin = history[-1]
    if family == "R05":
        try:
            origin_algebra = algebra_observation(origin, observed)
        except FloatingPointError:
            return _all_failed(request, unit, receivers, "CONDITIONAL_NONENTRY_NO_IDENTIFIABLE_ORIGIN_ALGEBRA", status="unsupported")
        if max(origin_algebra[:2]) > float(parameters["maximum_associative_leakage"]):
            return _all_failed(request, unit, receivers, "CONDITIONAL_NONENTRY_ORIGIN_ALGEBRA_NOT_ADMITTED", status="unsupported")
    description = _description_operand(history, settings, direction, parameters)
    if predictors_only:
        return [_row(request, unit, action, horizon, receiver,
                _features(settings, preparation, action, horizon, description), None,
                status="unsupported", reason="not-yet-acquired")
                for action in request.actions for horizon in request.horizons for receiver in receivers]
    maximum = max(_steps(h, settings) for h in request.horizons)
    tape = noise_tape(_rng(request, unit, "future"), maximum)
    rows = []
    for action in request.actions:
        coupling = (float(action), 0.0) if family == "R03" else (0.0, 0.0)
        amplitude = 0.0 if family == "R03" else float(action)
        path = native_path(origin, settings, tape, direction=direction, amplitude=amplitude, coupling_delta=coupling)
        shot_paths = [path]
        if family == "R04":
            shot_paths += [native_path(origin, settings, noise_tape(_rng(request, unit, f"shooting.{i}"), maximum),
                         direction=direction, amplitude=amplitude)
                         for i in range(1, int(parameters["shooting_replicates"]))]
        for horizon in request.horizons:
            steps = _steps(horizon, settings)
            features = _features(settings, preparation, action, horizon, description)
            if family == "R03":
                values = dict(zip(_receivers(family)[:4], geometry_observation(path[steps]), strict=True))
                admitted = [geometry_admission(path[steps], sector_index=i,
                    maximum_band_ratio=float(parameters["maximum_band_ratio"]),
                    maximum_associative_leakage=float(parameters["maximum_associative_leakage"]))[0] for i in (0, 1)]
                values.update({"x-admitted": float(admitted[0]), "y-admitted": float(admitted[1]),
                    "joint-admitted": float(all(admitted) and 90 * values["xy-angle"] >= float(parameters["minimum_joint_angle_degrees"]))})
            elif family == "R04":
                values = dict(zip(_receivers(family), np.mean([first_passage(p[:steps + 1], **criteria,
                    persistence_steps=min(int(parameters["persistence_steps"]), steps)) for p in shot_paths], axis=0), strict=True))
            else:
                values = {"algebra-survival": 0.0}
                try:
                    observed_values = algebra_observation(path[steps], observed)
                    values.update(zip(_receivers(family)[:-1], observed_values, strict=True))
                    values["algebra-survival"] = float(max(observed_values[:2]) <= float(parameters["maximum_associative_leakage"]))
                except FloatingPointError:
                    pass
            for receiver in receivers:
                unavailable = receiver not in values
                rows.append(_row(request, unit, action, horizon, receiver, features, values.get(receiver),
                    status="unsupported" if unavailable else "supported",
                    reason="SLOW_SECTOR_NOT_IDENTIFIABLE" if unavailable else "",
                    diagnostics=(("origin-step", float(origin.step_index)), ("conditional-futures", float(len(shot_paths)))),
                    work=len(shot_paths) * steps))
    return rows


def _passive_rows(request, unit, history, settings, parameters, preparation, direction, receivers, *, predictors_only=False):
    origin = history[-1]
    description = _description_operand(history, settings, direction, parameters)
    observed, kappa = int(parameters["observed_sector"]), float(parameters["kappa"])
    maximum = max(_steps(h, settings) for h in request.horizons)
    path = None if predictors_only else native_path(origin, settings, noise_tape(_rng(request, unit, "future"), maximum))
    current = operator(origin.positions[observed])
    elapsed = settings.history_stride * settings.dt
    depth = int(parameters["memory_depth"])
    times = -np.arange(depth + 1, dtype=float) * elapsed
    design = np.column_stack([times**power for power in range(min(2, depth) + 1)])
    operators = np.asarray([operator(history[-1 - lag * settings.history_stride].positions[observed]) for lag in range(depth + 1)])
    derivative = np.linalg.lstsq(design, operators.reshape(depth + 1, -1), rcond=None)[0][1].reshape(15, 15)
    rows = []
    for horizon in request.horizons:
        steps = _steps(horizon, settings)
        actual = None if path is None else directional_passive_transfer(path[:steps + 1], settings, observed_sector=observed, kappa=kappa)
        joint = causal_passive_transfer(origin, observed_sector=observed, kappa=kappa, horizon=horizon, radius_only=False)
        local = causal_passive_transfer(origin, observed_sector=observed, kappa=kappa, horizon=horizon, radius_only=True)
        extrapolated = current + derivative * float(horizon) / 2
        rates, vectors = np.linalg.eigh(extrapolated)
        memory = expm(-kappa * float(horizon) * ((vectors * np.maximum(rates, 0)) @ vectors.T))
        for action in request.actions:
            base = _features(settings, preparation, action, horizon, description)
            for receiver in receivers:
                index = int(receiver.split(".")[1])
                features = {**base, "forecast.local": action * local[index, index],
                            "forecast.joint": action * joint[index, index], "forecast.memory": action * memory[index, index]}
                diagnostic = () if actual is None else (("directional-leakage", float(np.sum(actual[:, index]**2) - actual[index, index]**2)),
                    ("operator-worst-error", float(np.linalg.norm(joint - actual, 2))))
                rows.append(_row(request, unit, action, horizon, receiver, features,
                    None if actual is None else action * actual[index, index],
                    status="unsupported" if predictors_only else "supported", reason="not-yet-acquired" if predictors_only else "",
                    diagnostics=diagnostic, work=0 if predictors_only else steps * 15**3))
    return rows


def _response_rows(request, unit, history, settings, parameters, preparation, direction, receivers, *, predictors_only=False):
    origin = history[-1]
    description = _description_operand(history, settings, direction, parameters)
    observed, family = int(parameters["observed_sector"]), request.family_id
    memory_origin = _memory_origin(history, settings, int(parameters["memory_depth"]), observed)
    maximum = max(_steps(h, settings) for h in request.horizons)
    tape = None if predictors_only else noise_tape(_rng(request, unit, "future"), maximum)
    baseline = None if predictors_only else native_path(origin, settings, tape)
    transverse = force_direction(origin, "y-coordinate" if observed == 0 else "x-coordinate")
    rows = []
    for action in request.actions:
        coupling = (float(action), 0.0) if family == "R08" else (0.0, 0.0)
        amplitude = 0.0 if family == "R08" else float(action)
        path = None if predictors_only else native_path(origin, settings, tape, direction=direction, amplitude=amplitude, coupling_delta=coupling)
        if family in ("R08", "R09"):
            forecasts, forecast_reason = _available_forecasts({
                "joint": lambda: deterministic_forecast(origin, settings, steps=maximum, direction=direction, amplitude=amplitude, coupling_delta=coupling),
                "local": lambda: radial_forecast(origin, settings, steps=maximum, direction=direction, observed_sector=observed, amplitude=amplitude, coupling_delta=coupling),
                "interface": lambda: radial_forecast(origin, settings, steps=maximum, direction=direction, observed_sector=observed, amplitude=amplitude, coupling_delta=coupling, retain_interface=True),
                "memory": lambda: radial_forecast(memory_origin, settings, steps=maximum, direction=direction, observed_sector=observed, amplitude=amplitude, coupling_delta=coupling),
            })
            reference_tasks = {"joint": lambda: deterministic_forecast(origin, settings, steps=maximum, direction=direction)}
            for kind in ("local", "interface", "memory"):
                reference_tasks[kind] = lambda kind=kind: radial_forecast(memory_origin if kind == "memory" else origin, settings, steps=maximum, direction=direction, observed_sector=observed,
                    retain_interface=kind == "interface")
            reference, reference_reason = _available_forecasts(reference_tasks)
            forecast_reason = ";".join(filter(None, (forecast_reason, reference_reason)))
        for horizon in request.horizons:
            steps = _steps(horizon, settings)
            base = _features(settings, preparation, action, horizon, description)
            if family == "R07":
                predictions, forecast_reason = _tangent_predictions(origin, memory_origin, settings, direction, steps, observed, float(action))
                diagnostic, diagnostic_reason = None, ""
                if not predictors_only:
                    available, diagnostic_reason = _available_forecasts({"realized-tangent-diagnostic":
                        lambda: action * realized_tangent(baseline[:steps + 1], settings, direction=direction, pulse_steps=steps)})
                    diagnostic = available.get("realized-tangent-diagnostic")
                for receiver in receivers:
                    axis = direction if receiver == "signed-response" else transverse
                    features = {**base, **{f"forecast.{name}": float(np.vdot(axis, value).real) for name, value in predictions.items()}}
                    outcome = None if predictors_only else float(np.vdot(axis, path[steps].positions - baseline[steps].positions).real)
                    rows.append(_row(request, unit, action, horizon, receiver, features, outcome,
                        status="unsupported" if predictors_only else "supported",
                        reason="not-yet-acquired" if predictors_only else ";".join(filter(None, (forecast_reason, diagnostic_reason))),
                        diagnostics=() if diagnostic is None else (("realized-tangent-oracle", float(np.vdot(axis, diagnostic).real)),),
                        work=0 if predictors_only else steps * 6))
            elif family == "R08":
                predicted = {name: radial_increment(ref[steps], forecasts[name][steps], observed) for name, ref in reference.items() if name in forecasts}
                features = {**base, **{f"forecast.{name}": value for name, value in predicted.items()}}
                rows.append(_row(request, unit, action, horizon, "radial-increment", features,
                    None if predictors_only else radial_increment(baseline[steps], path[steps], observed),
                    status="unsupported" if predictors_only else "supported", reason="not-yet-acquired" if predictors_only else forecast_reason,
                    work=0 if predictors_only else steps * 10))
            else:
                supported = float(np.linalg.norm(origin.positions)) <= float(parameters["support_radius_limit"])
                predicted = {name: response_receiver(origin, value[steps], direction, "absolute-position") for name, value in forecasts.items()}
                # Deliberately omit the baseline in the reduced increment-only description.
                if "local" in predicted:
                    if "local" in reference:
                        predicted["local"] -= response_receiver(origin, reference["local"][steps], direction, "absolute-position")
                    else:
                        predicted.pop("local")
                features = {**base, **{f"forecast.{name}": value for name, value in predicted.items()}}
                rows.append(_row(request, unit, action, horizon, "absolute-position", features,
                    response_receiver(origin, path[steps], direction, "absolute-position") if supported and not predictors_only else None,
                    status="supported" if supported and not predictors_only else "unsupported",
                    reason="not-yet-acquired" if predictors_only else forecast_reason if supported else "PREPARATION_OUTSIDE_DECLARED_RADIUS_SUPPORT",
                    diagnostics=() if predictors_only else (("absolute-baseline", response_receiver(origin, baseline[steps], direction, "absolute-position")),),
                    work=0 if predictors_only else steps * 10))
    return rows


def _composed_rows(request, unit, history, settings, parameters, preparation, direction, receivers, *, predictors_only=False):
    family, origin = request.family_id, history[-1]
    description = _description_operand(history, settings, direction, parameters)
    observed, parent_steps = int(parameters["observed_sector"]), int(parameters["handoff_steps"])
    memory_origin = _memory_origin(history, settings, int(parameters["memory_depth"]), observed)
    maximum = max(_steps(h, settings) for h in request.horizons)
    parent_tape = None if predictors_only else noise_tape(_rng(request, unit, "parent-preparation"), parent_steps)
    future_tape = None if predictors_only else noise_tape(_rng(request, unit, "lower-response"), maximum)
    refine = family == "R12" and not predictors_only
    if refine:
        parent_bridge = noise_tape(_rng(request, unit, "parent-refinement"), parent_steps)
        lower_bridge = noise_tape(_rng(request, unit, "lower-refinement"), maximum)
    rows = []
    for action in request.actions:
        coupling = (0.0, 0.0) if family == "R10" else (float(action), 0.0)
        # Parent instruments are chosen from the forecasting cutoff. The fixed
        # lower map never gets a fitted relation or a future response operand.
        predicted_handoffs, handoff_reason = _available_forecasts({
            "joint": lambda: deterministic_forecast(origin, settings, steps=parent_steps, direction=direction, coupling_delta=coupling)[-1],
            "interface": lambda: radial_forecast(origin, settings, steps=parent_steps, direction=direction, observed_sector=observed, coupling_delta=coupling, retain_interface=True)[-1],
            "local": lambda: radial_forecast(origin, settings, steps=parent_steps, direction=direction, observed_sector=observed, coupling_delta=coupling)[-1],
            "memory": lambda: radial_forecast(memory_origin, settings, steps=parent_steps, direction=direction, observed_sector=observed, coupling_delta=coupling)[-1],
        })
        amplitude = float(action) if family == "R10" else float(parameters["downstream_amplitude"])
        baseline, path, fine, fine_baseline = None, None, None, None
        if refine:
            preparation_pair = paired_refinement(origin, settings, parent_tape, parent_bridge, coupling_delta=coupling)
            handoff, fine_handoff = (trajectory[-1] for trajectory in preparation_pair)
            path, fine = paired_refinement(handoff, settings, future_tape, lower_bridge,
                                           fine_initial=fine_handoff, direction=direction, amplitude=amplitude)
            baseline, fine_baseline = paired_refinement(handoff, settings, future_tape, lower_bridge,
                                                        fine_initial=fine_handoff)
        elif not predictors_only:
            handoff = native_path(origin, settings, parent_tape, coupling_delta=coupling)[-1]
            baseline = native_path(handoff, settings, future_tape)
            path = native_path(handoff, settings, future_tape, direction=direction, amplitude=amplitude)
        for horizon in request.horizons:
            steps = _steps(horizon, settings)
            base = _features(settings, preparation, action, horizon, description)
            predictions, prediction_reason = _available_forecasts({name: lambda name=name, state=state: amplitude * float(np.vdot(direction, causal_tangent_forecast(state,
                settings, direction=direction, steps=steps, scalar_curvature=name != "joint")).real)
                for name, state in predicted_handoffs.items()})
            primary = None if predictors_only else float(np.vdot(direction, path[steps].positions - baseline[steps].positions).real)
            actual = primary if fine is None else float(np.vdot(direction, fine[steps].positions - fine_baseline[steps].positions).real)
            threshold = float(parameters["service_threshold"])
            diagnostics = () if predictors_only else (("primary-response", primary), ("paired-refinement-discrepancy", abs(actual - primary)),
                           ("actual-handoff-radius", float(np.linalg.norm(handoff.positions))),
                           ("lower-mechanism-unchanged", 1.0))
            if refine:
                diagnostics += (("refined-handoff-radius", float(np.linalg.norm(fine_handoff.positions))),
                                ("paired-handoff-position-discrepancy", float(np.linalg.norm(fine_handoff.positions - handoff.positions))),
                                ("primary-service", float(primary >= threshold)),
                                ("refined-service", float(actual >= threshold)))
            for receiver in receivers:
                features = {**base, **{f"forecast.{name}": value if receiver == "signed-response" else float(value >= threshold)
                                      for name, value in predictions.items()}}
                value = None if predictors_only else actual if receiver == "signed-response" else float(actual >= threshold)
                rows.append(_row(request, unit, action, horizon, receiver, features, value,
                    status="unsupported" if predictors_only else "supported",
                    reason="not-yet-acquired" if predictors_only else ";".join(filter(None, (handoff_reason, prediction_reason))),
                    diagnostics=diagnostics, work=0 if predictors_only else parent_steps * 5 + steps * (6 if family == "R12" else 4)))
    return rows


_PRODUCERS = {"R03": _structural_rows, "R04": _structural_rows, "R05": _structural_rows,
              "R06": _passive_rows, "R07": _response_rows, "R08": _response_rows,
              "R09": _response_rows, "R10": _composed_rows, "R11": _composed_rows, "R12": _composed_rows}


def _configuration(request):
    if request.family_id not in _PRODUCERS:
        raise ValueError("This matrix producer owns exactly R03--R12")
    preset = next(p for p in presets() if p["family_id"] == request.family_id)
    parameters = {**preset["parameters"], **dict(request.parameters)}
    allowed = set(preset["parameters"]) | {field.name for field in fields(MatrixSettings)} | {"receivers"}
    unknown = set(parameters) - allowed
    if unknown:
        raise ValueError(f"Unknown matrix scientific parameters: {sorted(unknown)}")
    settings = MatrixSettings(**{field.name: parameters[field.name] for field in fields(MatrixSettings) if field.name in parameters})
    receivers = tuple(parameters.get("receivers", preset["receivers"]))
    if not receivers or len(set(receivers)) != len(receivers) or not set(receivers) <= set(preset["receivers"]):
        raise ValueError("Matrix receivers must be a unique nonempty subset of the declared family instrument")
    preparations = tuple(parameters["preparations"])
    if not preparations or len(set(preparations)) != len(preparations) or not set(preparations) <= set(CONSTITUTIONS):
        raise ValueError("Matrix preparation family contains an undeclared native constitution")
    for field in ("memory_depth", "persistence_steps", "shooting_replicates", "handoff_steps"):
        if type(parameters[field]) is not int or parameters[field] < 1:
            raise ValueError(f"Matrix {field} must be a positive declared integer")
    if int(parameters["memory_depth"]) * settings.history_stride > settings.prefix_steps:
        raise ValueError("Declared causal history depth exceeds the prepared prefix")
    if type(parameters["observed_sector"]) is not int or parameters["observed_sector"] not in (0, 1):
        raise ValueError("Matrix observed_sector must be zero or one")
    for name, lower, upper in (("maximum_band_ratio", 0, 1), ("maximum_associative_leakage", 0, 1),
                                ("minimum_joint_angle_degrees", 0, 90)):
        value = parameters[name]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not np.isfinite(value) or not lower <= value <= upper:
            raise ValueError(f"Matrix {name} lies outside its declared finite scientific range")
    for name in ("kappa", "support_radius_limit"):
        if isinstance(parameters[name], bool) or not isinstance(parameters[name], (int, float)) or not np.isfinite(parameters[name]) or parameters[name] <= 0:
            raise ValueError(f"Matrix {name} must be finite and positive")
    if not np.isfinite((parameters["downstream_amplitude"], parameters["service_threshold"])).all():
        raise ValueError("Matrix downstream service declarations must be finite")
    directions = {"x-radial", "y-radial", "x-trace", "y-trace", "x-coordinate", "y-coordinate", "joint-radial"}
    if parameters["direction"] not in directions:
        raise ValueError("Matrix direction is outside the declared native force charts")
    if request.family_id in ("R08", "R09", "R10", "R11", "R12"):
        selected = "x" if parameters["observed_sector"] == 0 else "y"
        if not parameters["direction"].startswith((selected + "-", "joint-")):
            raise ValueError("Radial mechanism chart must contain the observed sector's force direction")
    if not request.actions or not request.horizons or not np.isfinite((*request.actions, *request.horizons)).all():
        raise ValueError("Matrix trial actions/horizons need finite nonempty declared rosters")
    for horizon in request.horizons:
        _steps(horizon, settings)
    if request.family_id in ("R03", "R08", "R11", "R12") and settings.alpha_x + min(request.actions) < 0:
        raise ValueError("Preparation actions leave the declared nonnegative coupling domain")
    return settings, parameters, receivers, preparations


def validate_specification(specification):
    """Validate declared information/cost channels without entering a native step."""
    parameters = json.loads(specification.parameters_json)
    authored_receivers = tuple(policy.receiver_id for policy in specification.receivers)
    if "receivers" in parameters and tuple(sorted(parameters["receivers"])) != authored_receivers:
        raise ValueError("Matrix parameter receivers conflict with the scientific receiver menu")
    request = TrialRequest(specification.family_id, specification.seed, specification.calibration_unit_ids,
        "calibration", tuple(float(a) for a in specification.actions), tuple(float(h) for h in specification.horizons),
        {**parameters, "receivers": authored_receivers})
    settings, parameters, _, _ = _configuration(request)
    depth, observed = int(parameters["memory_depth"]), int(parameters["observed_sector"])
    memory_names = {f"memory.{i:03d}" for i in range(96 * depth)}
    raw_names = set((*_BASE, *_LOCAL, *_INTERFACE, *_JOINT)) | memory_names
    mechanisms = {} if specification.family_id in ("R03", "R04", "R05") else {
        row["features"][0]: row for row in _mechanism_descriptions(specification.family_id,
            steps=max(_steps(h, settings) for h in request.horizons),
            parent_steps=int(parameters["handoff_steps"]), memory_depth=depth)}
    for description in specification.descriptions:
        selected = set(description.features)
        if not selected <= raw_names | set(mechanisms):
            raise ValueError("Matrix description names a feature absent from its causal instrument")
        forecast = selected & set(mechanisms)
        if forecast:
            if len(selected) != 1:
                raise ValueError("A built-in matrix mechanism is one sealed forecast; declare combined mechanisms as a new supplied-operand method")
            expected = mechanisms[next(iter(forecast))]
            dimensions = (expected["state_dimension"], expected["interface_dimension"],
                          expected["memory_dimension"], expected["memory_samples"])
            minimum_work = expected["forecast_work_units"]
        else:
            phase_coordinates = set()
            for name in selected:
                if name.startswith("joint."):
                    phase_coordinates.add(int(name.split(".")[1]))
                elif name.startswith("local."):
                    index = int(name.split(".")[1])
                    phase_coordinates.add((index // 48) * 96 + observed * 48 + index % 48)
            interfaces = selected & set(_INTERFACE)
            lag_widths = {}
            for name in selected & memory_names:
                lag = int(name.split(".")[1]) // 96
                lag_widths[lag] = lag_widths.get(lag, 0) + 1
            if len(set(lag_widths.values())) > 1:
                raise ValueError("Matrix memory uses one common coordinate width per retained lag")
            width = next(iter(lag_widths.values()), 0)
            dimensions = (len(phase_coordinates), len(interfaces), width, len(lag_widths))
            minimum_work = 128 * (len(phase_coordinates) + width * len(lag_widths))
            if interfaces:
                minimum_work += 2 * 600 * 8 * 4**3 + 18 * 8 * 4**3
        supplied = (description.state_dimension, description.interface_dimension,
                    description.memory_dimension, description.memory_samples)
        if supplied != dimensions:
            raise ValueError(f"Matrix retained information dimensions differ for {description.description_id}: expected {dimensions}")
        if description.forecast_work_unit != "normalized-scalar-operation" or description.forecast_work_units < minimum_work:
            raise ValueError("Matrix forecast construction budget is below its declared kernel-operation estimate; reauthor work when changing horizon/dt/history")


def _shared_work(request, settings, parameters, unit_rows, *, predictors_only):
    """Scheduled source intervals, allocated once rather than per receiver.

    This is an explicit acquisition budget, not measured execution time. The
    evaluation budget includes both causal-prefix passes in the six-phase
    workflow. Native receipts retain actual elapsed work and failure timing.
    """
    prefix = settings.prefix_steps * (2 if request.split == "evaluation" and not predictors_only else 1)
    if predictors_only or all("CONDITIONAL_NONENTRY" in row.reason for row in unit_rows):
        return prefix
    steps, actions, family = max(_steps(h, settings) for h in request.horizons), len(request.actions), request.family_id
    if family in ("R03", "R05"):
        return prefix + actions * steps
    if family == "R04":
        return prefix + actions * int(parameters["shooting_replicates"]) * steps
    if family == "R06":
        return prefix + steps
    if family in ("R07", "R08", "R09"):
        return prefix + (1 + actions) * steps
    preparation_and_response = int(parameters["handoff_steps"]) + 2 * steps
    return prefix + actions * preparation_and_response * (3 if family == "R12" else 1)


def _generate(request: TrialRequest, *, predictors_only: bool) -> TrialBatch:
    if request.device != "cpu":
        raise ValueError("q=2 six-matrix native instrument is CPU numerical science; no GPU execution is implemented")
    if request.input_path is not None or request.input_json is not None:
        raise ValueError("Fresh matrix experiments do not accept historical archive/result inputs")
    settings, parameters, receivers, preparations = _configuration(request)
    rows = []
    for unit in request.unit_ids:
        preparation = preparation_for_unit(request, unit, preparations)
        start = len(rows)
        history, direction = None, None
        try:
            history = acquire_prefix(settings, preparation, _rng(request, unit, "prefix"))
            direction = force_direction(history[-1], str(parameters["direction"]))
            with np.errstate(over="raise", invalid="raise", divide="raise"):
                rows.extend(_PRODUCERS[request.family_id](request, unit, history, settings, parameters, preparation, direction, receivers,
                    predictors_only=predictors_only))
        except (FloatingPointError, OverflowError, np.linalg.LinAlgError) as exc:
            reason = f"NATIVE_OR_MECHANISM_FAILURE:{type(exc).__name__}:{exc}"
            retained = None
            if not predictors_only and history is not None and direction is not None:
                try:
                    with np.errstate(over="raise", invalid="raise", divide="raise"):
                        retained = _PRODUCERS[request.family_id](request, unit, history, settings, parameters,
                            preparation, direction, receivers, predictors_only=True)
                except (FloatingPointError, OverflowError, np.linalg.LinAlgError):
                    pass
            rows.extend(_all_failed(request, unit, receivers, reason) if retained is None else
                        [replace(row, outcome=None, status="failed", reason=reason, diagnostics=()) for row in retained])
        work = _shared_work(request, settings, parameters, rows[start:], predictors_only=predictors_only)
        rows[start:] = [replace(row, work_units=float(work) if offset == 0 else 0.0)
                        for offset, row in enumerate(rows[start:])]
    expected = len(request.unit_ids) * len(request.actions) * len(request.horizons) * len(receivers)
    if len(rows) != expected:
        raise RuntimeError("Matrix producer lost a declared independent-unit/action/horizon/receiver cell")
    return TrialBatch(family_id=request.family_id, split=request.split, rows=tuple(rows),
        source_kind="fresh-six-matrix-q2-baoab-native-simulation",
        provenance=("new-experiment:no-original-paper-results", "native:full-two-sector-q2-complex128",
                    "randomness:family/split/independent-unit/purpose-pcg64dxsm",
                    "preparations:uniform-independent-root-assignment;invariant-under-worker-partitioning",
                    "causal-features:prefix-only-and-issued-forecasts", "diagnostics:evaluator-only",
                    "execution:prefix-replayed-deterministically-at-outcome-phase;future-acquired-once",
                    "coupling-actions:linear-ramp-reaching-target-at-longest-declared-horizon",
                    "independent-unit:root;directions/actions/horizons/shooting-futures:nested",
                    *(("R12:paired-primary-and-half-step-preparation-and-response;common-predecision-prefix",)
                      if request.family_id == "R12" else ()),
                    "work-units:scheduled-native-baoab-interval-budget;first-cell-per-root-carries-shared-budget",
                    "work-scope:includes-both-evaluation-prefix-passes;excludes-forecast-construction-charged-per-description;not-measured-runtime"))


def prepare_predictors(request: TrialRequest, *, native_port=None) -> TrialBatch:
    """Issue causal descriptions before any actual native response is acquired.

    Only the fresh past prefix is integrated. Deterministic mechanistic
    forecasts may be computed, but no realized future innovations, downstream
    handoff, response branches, passive target operators or outcome diagnostics
    are created. Rows carry unavailable outcomes solely for predictor transport.
    """
    return _generate(request, predictors_only=True)


def produce(request: TrialRequest, *, native_port=None) -> TrialBatch:
    """Acquire the new native census after the caller seals forecasts/choices.

    The past prefix is deterministically regenerated and must match the earlier
    predictor artifact in the shared runtime. It is additional prefix work,
    never a replay or re-exposure of actual response outcomes.
    """
    return _generate(request, predictors_only=False)
