# SPDX-License-Identifier: MPL-2.0
"""Withheld signed H64 response, fixed-basis updates and one Hermitian transfer query."""

from hashlib import sha256
import json
import math
from time import process_time

import numpy as np
from scipy.stats import beta

from empirical_lawhood.domains.matrix.classical_series import science as classical
from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02b_science import input_basis
from empirical_lawhood.domains.matrix.matrix_factor_response.origin_mechanics import discrete_baoab_maps
from empirical_lawhood.methods.model_free_response import incremental_receiver_certificate
from . import native
from .receiver_campaign import decimal_value
from .receiver_preparation import ARMS, service_origin

DEFAULTS = {
    "M3": {
        "signed_coordinates": ["nominal", "low-coupling", "high-coupling"],
        "signed_halfwidth": "0.001",
        "view_allowance": "0.0001",
        "absolute_block_allowance": "0.01",
        "selection_disagreement": "0.0005",
        "reconstruction_tolerance": "0.0000000001",
        "enrichment_directions": 4,
        "dense_seed_modulus": 8,
        "panels": [0, 1],
    },
    "M4": {
        "destination_ids": ["nominal", "temperature-1-125", "temperature-3-25", "high-coupling"],
        "signed_pair_allowance": "0.01",
        "probe_columns": 24,
        "local_columns": 48,
    },
}
METHODS = ("frozen", "fixed-refresh", "enriched-refresh")
CHECKS = np.arange(16, 65, 4)
ALL_CHECKS = np.arange(16, 65)


def validate(module, options, base):
    names = options["signed_coordinates" if module == "M3" else "destination_ids"]
    if type(names) is not list or not names or names[0] != "nominal" or len(set(names)) != len(names):
        raise ValueError("The source must be nominal and coordinates distinct")
    if module == "M3":
        for key in (
            "signed_halfwidth",
            "view_allowance",
            "absolute_block_allowance",
            "selection_disagreement",
            "reconstruction_tolerance",
        ):
            decimal_value(options[key], key)
        if (
            type(options["enrichment_directions"]) is not int
            or not 1 <= options["enrichment_directions"] <= 72
            or type(options["dense_seed_modulus"]) is not int
            or options["dense_seed_modulus"] < 1
            or len(options["panels"]) != 2
            or len(set(options["panels"])) != 2
            or any(type(p) is not int or p < 0 for p in options["panels"])
        ):
            raise ValueError(
                "M3 requires a causal enrichment, a prespecified dense subset and two coupled panels"
            )
    else:
        decimal_value(options["signed_pair_allowance"], "M4 paired allowance")
        if any(
            type(options[key]) is not int or not 1 <= options[key] <= 96
            for key in ("probe_columns", "local_columns")
        ):
            raise ValueError("M4 probe and local budgets count physical Hessian columns")


def case_ids(settings, module):
    selection = settings["receiver_study"]
    if module == "M4":
        return selection["M4"]["destination_ids"]
    physical = {row["id"] for row in settings["native"]["coordinates"]}
    destinations = [key for key in selection["M4"]["destination_ids"] if key in physical]
    return tuple(dict.fromkeys(selection["M3"]["signed_coordinates"] + destinations))


def _maps(matrix, basis, forces, dt, friction, amplitude):
    h = (matrix + matrix.T) / 2
    return discrete_baoab_maps(h, basis.T @ forces * amplitude, timestep=dt, decay=math.exp(-dt * friction))


def _mechanics(force, origin, state32, row, c, refinement, full, options, work, origin_models, arm, costs):
    member = native.coordinate(c, row).member
    old, new = native.action_at(service_origin(c, origin), member), native.action_at(state32, member)
    dt, friction, amp = float(c["timestep"]) / refinement, float(row["friction"]), float(c["amplitude"])

    def projected(basis, image):
        return basis, _maps(basis.T @ image, basis, force, dt, friction, amp)

    try:
        started = process_time()
        key = (arm, refinement)
        if key not in origin_models:
            basis, images, _ = input_basis(old, force, 24)
            origin_models[key] = {"frozen": projected(basis, images)}
        material = dict(origin_models[key])
        basis = material["frozen"][0]
        changed = new(basis)
        residual = changed - basis @ (basis.T @ changed)
        residual -= basis @ (basis.T @ residual)
        directions, magnitudes, _ = np.linalg.svd(residual, full_matrices=False)
        count = min(options["enrichment_directions"], int(np.sum(magnitudes > 1e-10 * max(1.0, magnitudes[0]))))
        extra = directions[:, :count]
        enriched = np.column_stack((basis, extra))
        expanded_images = np.column_stack((changed, new(extra))) if count else changed
        material["fixed-refresh"] = projected(basis, changed)
        material["enriched-refresh"] = projected(enriched, expanded_images)
        costs["candidate_operator_cpu_seconds"] += process_time() - started
        costs["candidate_hessian_columns"] += old.real_hessian_evaluations + new.real_hessian_evaluations
        if full:
            started = process_time()
            eye = np.eye(96)
            if "full-frozen" not in origin_models[key]:
                origin_models[key]["full-frozen"] = projected(eye, old(eye))
            material["full-frozen"] = origin_models[key]["full-frozen"]
            material["full-refresh"] = projected(eye, new(eye))
            costs["dense_operator_cpu_seconds"] += process_time() - started
        return material
    finally:
        work["native_hessian_actions"] += old.real_hessian_evaluations + new.real_hessian_evaluations


def _propagate(material, receivers, refinement, pulse_ticks, costs):
    paths, snapshots, ranks, losses = {}, {}, {}, {}
    for name, (after, suffix) in material.items():
        started = process_time()
        before, prefix = material["full-frozen" if name.startswith("full") else "frozen"]
        lift_before, lift_after = classical._phase_lift(before), classical._phase_lift(after)
        state = np.zeros((2 * before.shape[1], prefix[1].shape[1]))
        outputs = []
        for step in range(64 * refinement):
            if step == 32 * refinement:
                physical = lift_before @ state
                state = lift_after.T @ physical
                losses[name] = float(np.linalg.norm(lift_after @ state - physical))
                snapshots[name] = state.copy()
            transition, forcing = prefix if step < 32 * refinement else suffix
            state = transition @ state
            if step < pulse_ticks * refinement:
                state += forcing
            if (step + 1) % refinement == 0 and (step + 1) // refinement >= 16:
                lift = lift_before if step < 32 * refinement else lift_after
                outputs.append((receivers @ lift @ state).T)
        paths[name] = np.asarray(outputs)
        ranks[name] = [before.shape[1], after.shape[1]]
        costs[
            "dense_propagation_cpu_seconds" if name.startswith("full") else "candidate_propagation_cpu_seconds"
        ] += process_time() - started
    defects = {}
    if "full-refresh" in material:
        full_map = material["full-refresh"][1][0]
        for name in ("fixed-refresh", "enriched-refresh"):
            basis, (reduced_map, _) = material[name]
            lift = classical._phase_lift(basis)
            reduced_state = snapshots[name]
            inherited = snapshots["full-refresh"] - lift @ reduced_state
            generated = np.zeros_like(inherited)
            defect = full_map @ lift - lift @ reduced_map
            for _ in range(32 * refinement):
                inherited = full_map @ inherited
                generated = full_map @ generated + defect @ reduced_state
                reduced_state = reduced_map @ reduced_state
            ih, gen = (receivers @ inherited).T, (receivers @ generated).T
            measured = paths["full-refresh"][-1] - paths[name][-1]
            defects[name] = {
                "inherited": ih.tolist(),
                "generated": gen.tolist(),
                "measured": measured.tolist(),
                "raw_closure_error": float(np.max(np.abs(ih + gen - measured))),
            }
    return {name: path.tolist() for name, path in paths.items()}, ranks, losses, defects


def _cert(action, b, c, tolerance, budget, basis=None):
    return incremental_receiver_certificate(
        action, b, c, 1j, tolerance=tolerance, max_actions=budget, seed_basis=basis
    )


def _portable(cert):
    return {
        key: cert[key]
        for key in ("status", "rank", "action_count", "residual_bound", "estimate_real", "estimate_imag")
    }


def _signed_direct(c, row, origins, instrument, seed, panels, work):
    force = np.asarray(instrument["forces"])[:, [instrument["force_roles"].index("FACTOR")]]
    receiver = np.concatenate((np.zeros(96), force[:, 0]))[None, :]
    values = {}
    for r in (1, 2):
        endpoints = []
        for arm in ARMS:
            origin = native.restore(origins[arm][str(r)])
            measured = []
            for panel in panels:
                trial = native.paired_response(
                    c,
                    row,
                    origin,
                    force,
                    receiver,
                    seed,
                    panel,
                    refinement=r,
                    origin_clock_multiplier=r,
                    synchronous_quench=True,
                    compute_tangent=False,
                )
                work["native_force_evaluations"] += trial["force_evaluations"]
                work["native_energy_evaluations"] += trial["protocol_handoff_work"]["potential_evaluations"]
                measured.append(trial["odd_response"][0][-1][0] / classical._scales(c)[-1, 1])
            endpoints.append(np.mean(measured))
        values[r] = float(endpoints[0] - endpoints[1])
    return values


def _response(settings, seed, source, assigned_modules, work):
    opt = settings["receiver_study"]["M3"]
    transfer = settings["receiver_study"]["M4"]
    c = {**settings["native"], "horizon_ticks": 64}
    instrument = source["instrument"]
    cases = []
    for key in case_ids(settings, "M3"):
        entry = source["coordinates"][key]
        row = entry["coordinate"]
        costs = dict.fromkeys(
            (
                "hold_cpu_seconds",
                "candidate_operator_cpu_seconds",
                "dense_operator_cpu_seconds",
                "candidate_propagation_cpu_seconds",
                "dense_propagation_cpu_seconds",
                "selection_cpu_seconds",
                "upstream_certificate_cpu_seconds",
                "scalar_native_cpu_seconds",
                "evaluation_cpu_seconds",
            ),
            0.0,
        )
        costs.update(
            preparation_cpu_seconds=entry["preparation_cpu_seconds"],
            candidate_hessian_columns=0,
            hold_force_evaluations=0,
        )
        case = {
            "case_id": key,
            "coordinate": row,
            "status": "UNAVAILABLE",
            "origins": entry["origins"],
            "forecasts": [],
            "native": [],
            "source_certificates": {},
            "costs": costs,
        }
        cases.append(case)
        if entry["status"] != "COMPLETED" or instrument["status"] != "COMPLETED":
            case["reason"] = "SOURCE_PORT_OR_PAIRED_HANDOFF_UNAVAILABLE"
            continue
        forces, receivers = np.asarray(instrument["forces"]), np.asarray(instrument["receivers"])
        roles = instrument["force_roles"]
        try:
            if key == "nominal" and "M4" in assigned_modules:
                started = process_time()
                for arm in ARMS:
                    checkpoint = native.restore(entry["origins"][arm]["1"])
                    action = native.action_at(checkpoint, native.coordinate(c, row).member)
                    try:
                        case["source_certificates"][arm] = _cert(
                            action,
                            forces[:, [roles.index("FACTOR")]],
                            forces[:, [roles.index("TRACE")]],
                            float(transfer["signed_pair_allowance"]) / 2,
                            transfer["local_columns"],
                        )
                        b = forces[:, [roles.index("FACTOR")]]
                        t = forces[:, [roles.index("TRACE")]]
                        case["source_certificates"][arm]["frozen_cross_coefficient"] = float(
                            (t.T @ action(b)).item()
                        )
                        case["source_certificates"][arm]["cross_coefficient_columns"] = 1
                    finally:
                        work["native_hessian_actions"] += action.real_hessian_evaluations
                costs["upstream_certificate_cpu_seconds"] = process_time() - started
            if key not in opt["signed_coordinates"]:
                case["status"] = "COMPLETED"
                continue
            dense = seed % opt["dense_seed_modulus"] == 0
            origin_models = {}
            for refinement in (1, 2):
                for panel in opt["panels"]:
                    for arm in ARMS:
                        origin = native.restore(entry["origins"][arm][str(refinement)])
                        started = process_time()
                        hold = native.paired_response(
                            {**c, "horizon_ticks": 32},
                            row,
                            origin,
                            forces[:, :0],
                            receivers,
                            seed,
                            panel,
                            checkpoints=(32,),
                            refinement=refinement,
                            origin_clock_multiplier=refinement,
                            synchronous_quench=True,
                            compute_tangent=False,
                        )
                        work["native_force_evaluations"] += hold["force_evaluations"]
                        work["native_energy_evaluations"] += hold["protocol_handoff_work"][
                            "potential_evaluations"
                        ]
                        costs["hold_force_evaluations"] += hold["force_evaluations"]
                        costs["hold_cpu_seconds"] += process_time() - started
                        checkpoint = hold["hold_checkpoints"]["32"]
                        material = _mechanics(
                            forces,
                            origin,
                            native.restore(checkpoint),
                            row,
                            c,
                            refinement,
                            dense,
                            opt,
                            work,
                            origin_models,
                            arm,
                            costs,
                        )
                        predictions, ranks, losses, defects = _propagate(
                            material, receivers, refinement, c["pulse_ticks"], costs
                        )
                        case["forecasts"].append(
                            {
                                "arm": arm,
                                "panel": panel,
                                "refinement": refinement,
                                "checkpoint_sha256": checkpoint["sha256"],
                                "predictions": predictions,
                                "ranks": ranks,
                                "projection_losses": losses,
                                "map_defects": defects,
                            }
                        )
            started = process_time()
            case["rule"] = _choose(case["forecasts"], instrument, opt, c)
            costs["selection_cpu_seconds"] = process_time() - started
            case["forecast_sha256"] = sha256(
                json.dumps(
                    [case["forecasts"], case["rule"]], sort_keys=True, separators=(",", ":"), allow_nan=False
                ).encode()
            ).hexdigest()
            started = process_time()
            initial_work = work["native_force_evaluations"]
            case["direct_signed_values"] = _signed_direct(
                c, row, entry["origins"], instrument, seed, opt["panels"], work
            )
            costs["scalar_native_cpu_seconds"] = process_time() - started
            costs["scalar_native_force_evaluations"] = work["native_force_evaluations"] - initial_work
            costs["policy_cpu_seconds"] = sum(
                costs[k]
                for k in (
                    "hold_cpu_seconds",
                    "candidate_operator_cpu_seconds",
                    "candidate_propagation_cpu_seconds",
                    "selection_cpu_seconds",
                )
            )
            costs["policy_including_preparation_and_fallback_cpu_seconds"] = (
                costs["preparation_cpu_seconds"]
                + costs["policy_cpu_seconds"]
                + (costs["scalar_native_cpu_seconds"] if case["rule"]["selected"] == "native-fallback" else 0.0)
            )
            costs["direct_including_preparation_cpu_seconds"] = (
                costs["preparation_cpu_seconds"] + costs["scalar_native_cpu_seconds"]
            )
            started = process_time()
            for refinement in (1, 2, 4):
                for panel in opt["panels"]:
                    for arm in ARMS:
                        origin = native.restore(entry["origins"][arm][str(refinement)])
                        trial = native.paired_response(
                            c,
                            row,
                            origin,
                            forces,
                            receivers,
                            seed,
                            panel,
                            checkpoints=(32,),
                            refinement=refinement,
                            origin_clock_multiplier=refinement,
                            synchronous_quench=True,
                        )
                        work["native_force_evaluations"] += trial["force_evaluations"]
                        work["native_energy_evaluations"] += trial["protocol_handoff_work"][
                            "potential_evaluations"
                        ]
                        work["native_hessian_actions"] += trial["tangent_hessian_actions"]
                        pre = [
                            r
                            for r in case["forecasts"]
                            if (r["arm"], r["panel"], r["refinement"]) == (arm, panel, refinement)
                        ]
                        if pre and pre[0]["checkpoint_sha256"] != trial["hold_checkpoints"]["32"]["sha256"]:
                            raise ValueError("Pre-cutoff HOLD observation changed on evaluator branch")
                        odd, tangent = (
                            np.asarray(trial[k])[:, ALL_CHECKS, :].transpose(1, 0, 2)
                            for k in ("odd_response", "native_tangent")
                        )
                        case["native"].append(
                            {
                                "arm": arm,
                                "panel": panel,
                                "refinement": refinement,
                                "response": odd.tolist(),
                                "tangent_error": _block_error(odd - tangent, c),
                                "protocol_work": trial["protocol_handoff_work"],
                            }
                        )
            costs["evaluation_cpu_seconds"] = process_time() - started
            case["status"] = "COMPLETED"
        except (FloatingPointError, OverflowError, np.linalg.LinAlgError) as error:
            case["reason"] = str(error)
            work["counts_are_lower_bounds"] = True
            for name in ("native_force_evaluations", "native_hessian_actions", "native_energy_evaluations"):
                work[name] += getattr(error, "partial_accounting", {}).get(name, 0)
    return {"cases": cases, "instrument": instrument}


def _error_curve(value, c, checks=CHECKS):
    value = value[checks - 16]
    scales = classical._scales(c)[checks - 1]
    return np.max(
        np.linalg.norm(value.reshape(len(checks), -1, 2, 24), axis=-1) / scales[:, None, :], axis=(1, 2)
    )


def _block_error(value, c):
    return float(max(_error_curve(value, c)))


def _scalar(endpoint, instrument, c):
    index = instrument["force_roles"].index("FACTOR")
    return float(
        np.asarray(endpoint)[index] @ np.asarray(instrument["momentum_weights"]) / classical._scales(c)[-1, 1]
    )


def _contrast(rows, instrument, c, name=None):
    grouped = {}
    for row in rows:
        if name is not None and name not in row["predictions"]:
            continue
        path = row["response"] if name is None else row["predictions"][name]
        grouped.setdefault((row["refinement"], row["arm"]), []).append(_scalar(path[-1], instrument, c))
    return {
        r: float(np.mean(grouped[r, "ORIGINAL"]) - np.mean(grouped[r, "EARLY"]))
        for r in (1, 2, 4)
        if (r, "ORIGINAL") in grouped and (r, "EARLY") in grouped
    }


def _choose(forecasts, instrument, options, c):
    values = {name: _contrast(forecasts, instrument, c, name) for name in METHODS}
    width, agree = float(options["signed_halfwidth"]), float(options["selection_disagreement"])
    chosen = None
    for name in METHODS:
        pred = values[name]
        if (
            min(abs(pred[1]), abs(pred[2])) > width
            and pred[1] * pred[2] > 0
            and abs(pred[1] - pred[2]) <= float(options["view_allowance"])
            and max(abs(pred[r] - values["enriched-refresh"][r]) for r in (1, 2)) <= agree
            and max(abs(values["fixed-refresh"][r] - values["enriched-refresh"][r]) for r in (1, 2)) <= agree
        ):
            chosen = name
            break
    return {
        "selected": chosen or "native-fallback",
        "forecasts": values,
        "decision_tick": 32,
        "interval": None if chosen is None else [values[chosen][1] - width, values[chosen][1] + width],
        "uses_observed_H32_and_all_candidate_construction": True,
        "calibration": "EMPIRICAL_CHALLENGE",
    }


def _transfer(settings, seed, source, work):
    opt = settings["receiver_study"]["M4"]
    index = {case["case_id"]: case for case in source["cases"]}
    original = index["nominal"]
    instrument = source["instrument"]
    cases = []
    for key in opt["destination_ids"]:
        supplied = index[key]
        case = {
            "case_id": key,
            "status": "UNAVAILABLE",
            "arms": {},
            "nominal_preparation_cpu_seconds": original["costs"]["preparation_cpu_seconds"],
            "destination_preparation_cpu_seconds": supplied["costs"]["preparation_cpu_seconds"],
            "upstream_certificate_cpu_seconds": original["costs"]["upstream_certificate_cpu_seconds"],
            "required_input": "ACTUAL_DESTINATION_HANDOFF",
        }
        cases.append(case)
        if (
            instrument["status"] != "COMPLETED"
            or set(supplied["origins"]) != set(ARMS)
            or len(original["source_certificates"]) != 2
        ):
            case["reason"] = "ASSIGNED_SOURCE_OR_DESTINATION_UNAVAILABLE"
            continue
        f = np.asarray(instrument["forces"])
        b = f[:, [instrument["force_roles"].index("FACTOR")]]
        output = f[:, [instrument["force_roles"].index("TRACE")]]
        try:
            for arm in ARMS:
                source_cert = original["source_certificates"][arm]
                canon = supplied["origins"][arm]["1"]
                origin = native.restore(canon)
                row = supplied["coordinate"]
                action = native.action_at(origin, native.coordinate(settings["native"], row).member)
                a = {
                    "operator_identity": canon == original["origins"][arm]["1"]
                    and row == original["coordinate"],
                    "inherited_columns": source_cert["action_count"],
                    "upstream_cross_columns": source_cert["cross_coefficient_columns"],
                }
                case["arms"][arm] = a
                tol = float(opt["signed_pair_allowance"]) / 2
                try:
                    a["reuse"] = (
                        _portable(source_cert)
                        if a["operator_identity"]
                        else {
                            "status": "UNRESOLVED",
                            "reason": "DESTINATION_OPERATOR_CHANGE",
                            "residual_bound": None,
                            "estimate_real": source_cert["estimate_real"],
                            "estimate_imag": source_cert["estimate_imag"],
                        }
                    )
                    a["reuse"]["incremental_columns"] = 0
                    a["reuse"]["cpu_seconds"] = 0.0
                    scalar = -float((output.T @ b).item())
                    a["frozen_cross"] = {
                        "estimate_real": -source_cert["frozen_cross_coefficient"],
                        "estimate_imag": scalar,
                        "incremental_columns": 0,
                        "cpu_seconds": 0.0,
                        "status": "SOURCE_COEFFICIENT_ONLY_NO_REMAINDER_BOUND",
                    }
                    started = process_time()
                    coefficient = float((output.T @ action(b)).item())
                    a["cross_coefficient"] = {
                        "estimate_real": -coefficient,
                        "estimate_imag": -float((output.T @ b)[0, 0]),
                        "incremental_columns": 1,
                        "cpu_seconds": process_time() - started,
                        "status": "UNBOUNDED_TRUNCATED_RESOLVENT_MOMENTS",
                    }
                    source_basis = np.asarray(source_cert["retained_basis"])
                    start = action.real_hessian_evaluations
                    started = process_time()
                    probe = _cert(
                        action, b, output, tol, opt["probe_columns"], source_basis[:, : opt["probe_columns"]]
                    )
                    a["probe"] = _portable(probe) | {
                        "incremental_columns": action.real_hessian_evaluations - start,
                        "cpu_seconds": process_time() - started,
                    }
                    for label, budget in (
                        ("local_same_budget", opt["probe_columns"]),
                        ("local", opt["local_columns"]),
                    ):
                        start = action.real_hessian_evaluations
                        started = process_time()
                        local = _cert(action, b, output, tol, budget)
                        a[label] = _portable(local) | {
                            "incremental_columns": action.real_hessian_evaluations - start,
                            "cpu_seconds": process_time() - started,
                        }
                    a["zero"] = {
                        "estimate_real": 0.0,
                        "estimate_imag": 0.0,
                        "incremental_columns": 0,
                        "cpu_seconds": 0.0,
                        "status": "BENCHMARK",
                    }
                    a["prespecified_dense_audit"] = (
                        seed % settings["receiver_study"]["M3"]["dense_seed_modulus"] == 0
                    )
                    a["requires_native_fallback"] = not any(
                        a[label]["status"] == "CERTIFIED" for label in ("reuse", "probe", "local")
                    )
                    if a["prespecified_dense_audit"] or a["requires_native_fallback"]:
                        started = process_time()
                        h = action(np.eye(96))
                        exact = (output.T @ np.linalg.solve(1j * np.eye(96) - h, b))[0, 0]
                        a["reference_real"], a["reference_imag"] = float(exact.real), float(exact.imag)
                        a["dense_fallback"] = {
                            "estimate_real": float(exact.real),
                            "estimate_imag": float(exact.imag),
                            "incremental_columns": 96,
                            "cpu_seconds": process_time() - started,
                            "status": "DENSE_NATIVE_RESOLVENT",
                        }
                        for label in (
                            "reuse",
                            "probe",
                            "local_same_budget",
                            "local",
                            "zero",
                            "frozen_cross",
                            "cross_coefficient",
                        ):
                            val = a[label]
                            prediction = complex(
                                float(np.asarray(val["estimate_real"]).item()),
                                float(np.asarray(val["estimate_imag"]).item()),
                            )
                            val["audit_error"] = abs(prediction - exact)
                    a["new_columns"] = action.real_hessian_evaluations
                finally:
                    work["native_hessian_actions"] += action.real_hessian_evaluations
            case["status"] = "COMPLETED"
        except (FloatingPointError, OverflowError, np.linalg.LinAlgError) as error:
            case["reason"] = str(error)
            work["counts_are_lower_bounds"] = True
    return {"cases": cases}


def acquire(settings, seed, module, prerequisites, sampling, assigned_modules):
    work = {
        "native_force_evaluations": 0,
        "native_energy_evaluations": 0,
        "native_hessian_actions": 0,
        "counts_are_lower_bounds": False,
    }
    data = (
        _response(settings, seed, prerequisites["M1"]["response_preparation"], assigned_modules, work)
        if module == "M3"
        else _transfer(settings, seed, prerequisites["M3"], work)
    )
    return {**data, "work_accounting": work}


def analyse(settings, module, payload):
    if module == "M4":
        rows = []
        for row in payload["cases"]:
            result = dict(row)
            if row["status"] == "COMPLETED":
                result["signed_pair"] = {}
                for name in (
                    "reuse",
                    "probe",
                    "local_same_budget",
                    "local",
                    "zero",
                    "frozen_cross",
                    "cross_coefficient",
                ):
                    arms = [row["arms"][arm][name] for arm in ARMS]
                    bounds = [a.get("residual_bound") for a in arms]
                    bound = sum(bounds) if None not in bounds else None
                    predicted = [
                        complex(
                            float(np.asarray(a["estimate_real"]).item()),
                            float(np.asarray(a["estimate_imag"]).item()),
                        )
                        for a in arms
                    ]
                    exact = None
                    if all("reference_real" in row["arms"][arm] for arm in ARMS):
                        exact = complex(
                            row["arms"]["ORIGINAL"]["reference_real"] - row["arms"]["EARLY"]["reference_real"],
                            row["arms"]["ORIGINAL"]["reference_imag"] - row["arms"]["EARLY"]["reference_imag"],
                        )
                    inherited = (
                        sum(row["arms"][arm]["inherited_columns"] for arm in ARMS)
                        if name in ("reuse", "probe")
                        else (
                            sum(row["arms"][arm]["upstream_cross_columns"] for arm in ARMS)
                            if name == "frozen_cross"
                            else 0
                        )
                    )
                    increment = sum(a["incremental_columns"] for a in arms)
                    result["signed_pair"][name] = {
                        "bound": bound,
                        "certified": bound is not None
                        and bound <= float(settings["receiver_study"]["M4"]["signed_pair_allowance"]),
                        "incremental_columns": increment,
                        "standalone_columns": increment + inherited,
                        "upstream_columns": inherited,
                        "cpu_seconds": sum(a["cpu_seconds"] for a in arms),
                        "estimate_real": (predicted[0] - predicted[1]).real,
                        "estimate_imag": (predicted[0] - predicted[1]).imag,
                        "native_pair_error": None
                        if exact is None
                        else abs(predicted[0] - predicted[1] - exact),
                    }
                chosen = {}
                total_columns = 0
                for arm in ARMS:
                    arm_case = row["arms"][arm]
                    for supplier in ("reuse", "probe", "local", "dense_fallback"):
                        candidate = arm_case.get(supplier)
                        if candidate is None:
                            continue
                        total_columns += candidate["incremental_columns"]
                        if candidate["status"] in ("CERTIFIED", "DENSE_NATIVE_RESOLVENT"):
                            chosen[arm] = supplier
                            break
                result["delivered_pair"] = {
                    "suppliers": chosen,
                    "incremental_columns_including_refused_probes": total_columns,
                    "status": "AVAILABLE" if len(chosen) == 2 else "UNAVAILABLE",
                }
            rows.append(result)
        return {"cases": rows}
    c = {**settings["native"], "horizon_ticks": 64}
    opt = settings["receiver_study"]["M3"]
    instrument = payload["instrument"]
    rows = []
    for case in payload["cases"]:
        row = {k: case[k] for k in ("case_id", "status", "coordinate", "costs")}
        rows.append(row)
        if case["status"] != "COMPLETED" or not case["native"]:
            row["reason"] = case.get("reason", "TRANSFER_QUERY_ONLY")
            if "rule" in case:
                row.update(
                    rule=case["rule"],
                    delivery_correct=None,
                    wrong_sign=None,
                    delivery_disposition="NATIVE_BRANCH_UNAVAILABLE",
                    completed_native_comparisons=len(case["native"]),
                )
            continue
        actual = _contrast(case["native"], instrument, c)
        direct = {int(r): v for r, v in case["direct_signed_values"].items()}
        direct_closure = max(abs(direct[r] - actual[r]) for r in (1, 2))
        if direct_closure > float(opt["reconstruction_tolerance"]):
            raise ValueError("Scalar native fallback and independently projected four-action audit disagree")
        refs = {(v["arm"], v["panel"], v["refinement"]): np.asarray(v["response"]) for v in case["native"]}
        norm = classical._scales(c)[-1]
        methods = {}
        endpoints = {}
        signed = {}
        factor = instrument["force_roles"].index("FACTOR")
        signal = min(
            float(np.linalg.norm(v[-1, factor, 24:]) / norm[1]) for k, v in refs.items() if k[2] in (1, 2)
        )
        for name in case["forecasts"][0]["predictions"]:
            vals = _contrast(case["forecasts"], instrument, c, name)
            worst = 0.0
            endpoint = {}
            curves = {}
            for forecast in case["forecasts"]:
                key = forecast["arm"], forecast["panel"], forecast["refinement"]
                pred = np.asarray(forecast["predictions"][name])
                error = pred - refs[key]
                curves[key] = [_error_curve(error, c, checks) for checks in (CHECKS, ALL_CHECKS)]
                worst = max(worst, _block_error(error, c))
                endpoint[key] = error[-1] / np.repeat(norm, 24)[None, :]
            pairs = []
            for panel in opt["panels"]:
                for refinement in (1, 2):
                    a, b = (endpoint[arm, panel, refinement].reshape(4, 2, 24) for arm in ARMS)
                    pairs.append(
                        {
                            "panel": panel,
                            "refinement": refinement,
                            "a_squared": (a * a).sum(axis=-1).tolist(),
                            "b_squared": (b * b).sum(axis=-1).tolist(),
                            "cross_term": (-2 * a * b).sum(axis=-1).tolist(),
                            "contrast_squared": ((a - b) ** 2).sum(axis=-1).tolist(),
                        }
                    )
            signed[name] = pairs
            endpoints[name] = [
                {"arm": k[0], "panel": k[1], "refinement": k[2], "normalized_error": e.tolist()}
                for k, e in endpoint.items()
            ]
            metrics = []
            for j in (0, 1):
                arm_curves = {}
                for arm in ARMS:
                    cumulative = [
                        np.maximum.accumulate(np.max([curves[arm, p, r][j] for p in opt["panels"]], axis=0))
                        for r in (1, 2)
                    ]
                    arm_curves[arm] = {
                        "maximum_error": float(np.max(cumulative)),
                        "maximum_view_curve_disagreement": float(np.max(np.abs(cumulative[0] - cumulative[1]))),
                    }
                metrics.append(arm_curves)
            methods[name] = {
                "predicted_signed_contrast": vals,
                "primary_signed_error": vals[1] - actual[1],
                "refined_signed_error": vals[2] - actual[2],
                "maximum_scheduled_block_error": worst,
                "scheduled_error_curves_by_arm": metrics[0],
                "sci02_all49_error_curves_by_arm": metrics[1],
                "measured_ranks": sorted({tuple(f["ranks"][name]) for f in case["forecasts"]}),
            }
        value = case["rule"]["selected"]
        num = {
            f"{a}/{b}": max(
                _block_error(refs[arm, panel, a] - refs[arm, panel, b], c)
                for arm in ARMS
                for panel in opt["panels"]
            )
            for a, b in ((1, 2), (2, 4))
        }
        for metrics in methods.values():
            metrics["absolute_adequacy"] = (
                metrics["maximum_scheduled_block_error"] <= float(opt["absolute_block_allowance"])
                and all(
                    a["maximum_view_curve_disagreement"] <= float(opt["view_allowance"])
                    for a in metrics["scheduled_error_curves_by_arm"].values()
                )
                and signal >= 0.10
            )
            metrics["absolute_adequacy_all49"] = (
                all(
                    a["maximum_error"] <= float(opt["absolute_block_allowance"])
                    and a["maximum_view_curve_disagreement"] <= float(opt["view_allowance"])
                    for a in metrics["sci02_all49_error_curves_by_arm"].values()
                )
                and signal >= 0.10
            )
        checked = None
        wrong_sign = None
        delivery_disposition = "NATIVE_FALLBACK"
        if value != "native-fallback":
            lo, hi = case["rule"]["interval"]
            if abs(actual[1] - actual[2]) > float(opt["view_allowance"]):
                delivery_disposition = "NATIVE_VIEWS_DISAGREE"
            else:
                checked = lo <= actual[1] <= hi and lo <= actual[2] <= hi
                wrong_sign = bool(
                    (lo > 0 and max(actual[1], actual[2]) <= 0) or (hi < 0 and min(actual[1], actual[2]) >= 0)
                )
                delivery_disposition = "INTERVAL_CONTAINS_BOTH_VIEWS" if checked else "INTERVAL_MISS"
        defects = []
        for forecast in case["forecasts"]:
            for name, acc in forecast["map_defects"].items():
                closure = (
                    np.asarray(acc["inherited"]) + np.asarray(acc["generated"]) - np.asarray(acc["measured"])
                ) / np.repeat(norm, 24)
                defects.append(
                    {
                        "arm": forecast["arm"],
                        "panel": forecast["panel"],
                        "refinement": forecast["refinement"],
                        "model": name,
                        "maximum_normalized_closure": float(np.max(abs(closure))),
                        "normalized_vectors": {
                            term: (np.asarray(acc[term]) / np.repeat(norm, 24)).tolist()
                            for term in ("inherited", "generated", "measured")
                        },
                        "inherited_normalized_norm": float(
                            np.linalg.norm(np.asarray(acc["inherited"]) / np.repeat(norm, 24))
                        ),
                        "generated_normalized_norm": float(
                            np.linalg.norm(np.asarray(acc["generated"]) / np.repeat(norm, 24))
                        ),
                    }
                )
        fallback = (
            abs(direct[1] - direct[2]) <= float(opt["view_allowance"])
            and min(abs(direct[1]), abs(direct[2])) > float(opt["signed_halfwidth"])
            and direct[1] * direct[2] > 0
        )
        row.update(
            native_signed_contrast=actual,
            methods=methods,
            signed_errors=signed,
            normalized_endpoints=endpoints,
            direct_fallback_signed_decision_resolved=bool(fallback),
            direct_reconstruction_error=direct_closure,
            minimum_FACTOR_H64_momentum_signal=signal,
            numerical_discrepancies=num,
            rule=case["rule"],
            delivery_correct=checked,
            delivery_disposition=delivery_disposition,
            wrong_sign=wrong_sign,
            independent_defects=defects,
            maximum_tangent_error=max(v["tangent_error"] for v in case["native"]),
            maximum_projection_loss=max(v for f in case["forecasts"] for v in f["projection_losses"].values()),
            native_signed_numerical_discrepancy=abs(actual[1] - actual[2]),
        )
    return {
        "cases": rows,
        "force_roles": instrument.get("force_roles", []),
        "source_factor_admitted": instrument.get("source_factor_admitted"),
    }


def _coupling_comparison(root, options):
    endpoints = {case["case_id"]: case for case in root["cases"]}
    contrasts = {}
    for label, before, after in (
        ("reduced", "frozen", "fixed-refresh"),
        ("full", "full-frozen", "full-refresh"),
    ):
        rows = [endpoints.get(key, {}) for key in ("high-coupling", "low-coupling")]
        if not all(before in row.get("methods", {}) and after in row["methods"] for row in rows):
            contrasts[label] = {"status": "UNAVAILABLE", "assigned_nested_cells": 16}
            continue
        eligible = all(
            row["methods"][name]["scheduled_error_curves_by_arm"]["ORIGINAL"]["maximum_view_curve_disagreement"]
            <= float(options["view_allowance"])
            for row in rows
            for name in (before, after)
        )
        counts = dict.fromkeys(
            (
                "evaluated",
                "both_endpoints_improve_contrast_worsens",
                "contrast_worsens",
                "contrast_improves",
                "tied",
            ),
            0,
        )
        cells = []
        for panel in options["panels"]:
            for refinement in (1, 2):
                vectors = []
                paired_defects = []
                for row in rows:
                    if label == "reduced":
                        matches = [
                            d
                            for d in row["independent_defects"]
                            if (d["arm"], d["panel"], d["refinement"], d["model"])
                            == ("ORIGINAL", panel, refinement, after)
                        ]
                        if matches:
                            paired_defects.append(matches[0]["normalized_vectors"])
                    for name in (before, after):
                        observation = next(
                            endpoint
                            for endpoint in row["normalized_endpoints"][name]
                            if (endpoint["arm"], endpoint["panel"], endpoint["refinement"])
                            == ("ORIGINAL", panel, refinement)
                        )
                        vectors.append(np.asarray(observation["normalized_error"]))
                for role in ("TRACE", "GENERIC"):
                    i = root["force_roles"].index(role)
                    for block, sl in (("position", slice(0, 24)), ("momentum", slice(24, 48))):
                        h0, h1, l0, l1 = (v[i, sl] for v in vectors)
                        previous, new = float(np.linalg.norm(h0 - l0)), float(np.linalg.norm(h1 - l1))
                        delta_sum = float(h1 @ h1 + l1 @ l1 - h0 @ h0 - l0 @ l0)
                        delta_alignment = float(2 * (h1 @ l1 - h0 @ l0))
                        counts["evaluated"] += 1
                        counts["both_endpoints_improve_contrast_worsens"] += int(
                            np.linalg.norm(h1) < np.linalg.norm(h0)
                            and np.linalg.norm(l1) < np.linalg.norm(l0)
                            and new > previous
                        )
                        counts["contrast_worsens"] += int(new > previous)
                        counts["contrast_improves"] += int(new < previous)
                        counts["tied"] += int(new == previous)
                        cells.append(
                            {
                                "panel": panel,
                                "view": refinement,
                                "action": role,
                                "block": block,
                                "frozen_error": previous,
                                "refreshed_error": new,
                                "delta_squared_endpoints": delta_sum,
                                "delta_alignment": delta_alignment,
                                "signed_identity_residual": abs(
                                    new**2 - previous**2 - (delta_sum - delta_alignment)
                                ),
                            }
                        )
                        if len(paired_defects) == 2:
                            h, l = paired_defects
                            inherited, generated, measured = (
                                np.asarray(h[t])[i, sl] - np.asarray(l[t])[i, sl]
                                for t in ("inherited", "generated", "measured")
                            )
                            cells[-1]["full_minus_reduced_contrast"] = {
                                "inherited_norm": float(np.linalg.norm(inherited)),
                                "generated_norm": float(np.linalg.norm(generated)),
                                "measured_norm": float(np.linalg.norm(measured)),
                                "closure_norm": float(np.linalg.norm(inherited + generated - measured)),
                            }
        contrasts[label] = {
            "status": "COMPLETED",
            "assigned_nested_cells": 16,
            "numerically_evaluable": eligible,
            "evaluable_cells": len(cells) if eligible else 0,
            "all_available": counts,
            "signed_cells": cells,
        }
    return {"seed": root["seed"], "status": contrasts["reduced"]["status"], "models": contrasts}


def synthesise(settings, module, roots, alpha):
    if module == "M4":
        rows = []
        for destination in case_ids(settings, module):
            cases = [next(c for c in root["cases"] if c["case_id"] == destination) for root in roots]
            for label in (
                "reuse",
                "probe",
                "local_same_budget",
                "local",
                "zero",
                "frozen_cross",
                "cross_coefficient",
            ):
                measured = [c["signed_pair"][label] for c in cases if c["status"] == "COMPLETED"]
                rows.append(
                    {
                        "destination": destination,
                        "mode": label,
                        "assigned": len(roots),
                        "measured": len(measured),
                        "certified_pairs": sum(v["certified"] for v in measured),
                        "incremental_columns": sum(v["incremental_columns"] for v in measured),
                        "standalone_columns": sum(v["standalone_columns"] for v in measured),
                        "native_comparisons": sum(v["native_pair_error"] is not None for v in measured),
                        "within_width_when_audited": sum(
                            v["native_pair_error"] is not None
                            and v["native_pair_error"]
                            <= float(settings["receiver_study"]["M4"]["signed_pair_allowance"])
                            for v in measured
                        ),
                    }
                )
            rows.append(
                {
                    "destination": destination,
                    "mode": "prospective-cascade",
                    "assigned": len(roots),
                    "measured": sum(c["status"] == "COMPLETED" for c in cases),
                    "delivered_pairs": sum(
                        c.get("delivered_pair", {}).get("status") == "AVAILABLE" for c in cases
                    ),
                    "pairs_requiring_native": sum(
                        "dense_fallback" in c.get("delivered_pair", {}).get("suppliers", {}).values()
                        for c in cases
                    ),
                    "incremental_columns": sum(
                        c["delivered_pair"]["incremental_columns_including_refused_probes"]
                        for c in cases
                        if c["status"] == "COMPLETED"
                    ),
                }
            )
        return {
            "decision": "SCOPED_RESOLVENT_CERTIFICATES"
            if any(r.get("certified_pairs", 0) for r in rows)
            else "UNRESOLVED",
            "paired_transfer": rows,
            "query": "TRACE^T (i I - H)^-1 FACTOR, ORIGINAL minus EARLY",
            "finite_time_response_bound": None,
        }
    options = settings["receiver_study"]["M3"]
    summaries = []
    for key in options["signed_coordinates"]:
        cases = [next(c for c in root["cases"] if c["case_id"] == key) for root in roots]
        available = [case for case in cases if case.get("methods")]
        assigned_policies = [case for case in cases if "rule" in case]
        selected = [case for case in assigned_policies if case["rule"]["selected"] != "native-fallback"]
        wrong = sum(c["delivery_correct"] is False for c in selected)
        unevaluable = sum(c["delivery_correct"] is None for c in selected)
        conservative_errors = wrong + unevaluable
        confidence_alpha = alpha / len(options["signed_coordinates"])
        rows = []
        for name in (*METHODS, "full-frozen", "full-refresh"):
            values = [case["methods"][name] for case in available if name in case["methods"]]
            if values:
                rows.append(
                    {
                        "method": name,
                        "evaluable": len(values),
                        "absolute_adequate": sum(c["absolute_adequacy"] for c in values),
                        "absolute_adequate_all49": sum(c["absolute_adequacy_all49"] for c in values),
                        "mean_absolute_signed_error": float(
                            np.mean([abs(c["primary_signed_error"]) for c in values])
                        ),
                        "within_scalar_width": sum(
                            abs(c["primary_signed_error"]) <= float(options["signed_halfwidth"]) for c in values
                        ),
                    }
                )
        summaries.append(
            {
                "coordinate": key,
                "assigned": len(roots),
                "evaluable": len(available),
                "accepted": len(selected),
                "wrong_deliveries": wrong,
                "wrong_sign": sum(c["wrong_sign"] is True for c in selected),
                "accepted_but_numerically_unresolved": unevaluable,
                "fallback_or_unavailable": len(roots) - len(selected),
                "methods": rows,
                "conditional_wrong_risk_upper_bound": (
                    None
                    if not selected
                    else 1.0
                    if conservative_errors == len(selected)
                    else float(
                        beta.ppf(
                            1 - confidence_alpha, conservative_errors + 1, len(selected) - conservative_errors
                        )
                    )
                ),
                "assigned_decision_alpha": confidence_alpha,
                "fallback_selected": len(assigned_policies) - len(selected),
                "precutoff_unavailable": len(cases) - len(assigned_policies),
                "fallback_signed_decisions": sum(
                    c["rule"]["selected"] == "native-fallback" and c["direct_fallback_signed_decision_resolved"]
                    for c in available
                ),
                "priced_complete_comparisons": len(available),
                "policy_cpu_seconds_including_preparation_and_fallback": sum(
                    c["costs"]["policy_including_preparation_and_fallback_cpu_seconds"] for c in available
                ),
                "direct_cpu_seconds_including_preparation": sum(
                    c["costs"]["direct_including_preparation_cpu_seconds"] for c in available
                ),
                "greatest_defect_reconstruction_error": max(
                    (
                        d["maximum_normalized_closure"]
                        for case in available
                        for d in case["independent_defects"]
                    ),
                    default=None,
                ),
                "coarse_numerical_pass": sum(
                    c["numerical_discrepancies"]["1/2"] <= float(options["view_allowance"]) for c in available
                ),
                "finer_numerical_pass": sum(
                    c["numerical_discrepancies"]["2/4"] <= float(options["view_allowance"]) for c in available
                ),
            }
        )
    primary = summaries[0]
    contrast = [_coupling_comparison(root, options) for root in roots]
    return {
        "decision": "NO_REDUCED_DELIVERIES"
        if not primary["accepted"]
        else "ADVERSE_DELIVERY"
        if primary["wrong_deliveries"]
        else "NUMERICAL_DELIVERY_UNRESOLVED"
        if primary["accepted_but_numerically_unresolved"]
        else "BOUNDED_OBSERVED_DELIVERIES",
        "primary_signed_receiver": "nominal ORIGINAL minus EARLY H64 FACTOR odd momentum in actuator units",
        "source_factor_admission": {
            "assigned": len(roots),
            "present": sum(root["source_factor_admitted"] is True for root in roots),
            "unavailable": sum(root["source_factor_admitted"] is None for root in roots),
        },
        "response_by_coordinate": summaries,
        "secondary_coupling_contrast": contrast,
        "claim": "INDEPENDENT_ROOTS_ONLY; NESTED_PORTS_PANELS_AND_VIEWS; NO_POPULATION_RELIABILITY_QUALIFICATION",
    }
