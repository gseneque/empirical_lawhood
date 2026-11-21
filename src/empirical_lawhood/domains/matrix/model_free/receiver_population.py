# SPDX-License-Identifier: MPL-2.0
"""Frozen individual suppliers and direct randomized audits of one signed H64 finite-frame mean."""

from hashlib import sha256
import json
import math
from decimal import Decimal
from time import process_time

import numpy as np

from empirical_lawhood.domains.matrix.classical_series import science as classical
from empirical_lawhood.domains.matrix.model_free import native
from empirical_lawhood.methods.model_free.finite_population import compare_finite_population_estimators
from .receiver_campaign import decimal_value
from .receiver_preparation import ARMS, service_origin

CASE = "nominal.ORIGINAL-minus-EARLY.FACTOR-momentum.H64"
DEFAULTS = {
    "M5": {
        "individual_halfwidth_actuator": "0.001",
        "numerical_allowance_actuator": "0.0001",
        "mean_rms_budget_actuator": "0.00025",
        "mean_halfwidth_actuator": "0.00025",
        "mean_error_risk": "0.05",
        "sparse_use": "ECONOMIC_DELIVERY",
        "sparse_supplier": "auxiliary",
        "panels": [5000, 5001],
    }
}


def validate(module, selection, base):
    for key in (
        "individual_halfwidth_actuator",
        "numerical_allowance_actuator",
        "mean_rms_budget_actuator",
        "mean_halfwidth_actuator",
    ):
        decimal_value(selection[key], key)
    if decimal_value(selection["mean_error_risk"], "mean error risk", maximum=Decimal(1)) >= 1:
        raise ValueError("M5 repeated-design error risk must be strictly below one")
    if selection["sparse_use"] not in ("ECONOMIC_DELIVERY", "DISJOINT_DEVELOPMENT_AUDIT"):
        raise ValueError("Declare the economic or developmental purpose of the disjoint sample")
    if selection["sparse_supplier"] not in ("auxiliary", "one_coefficient"):
        raise ValueError("The sparse signed estimator requires its preselected supplier")
    if (
        len(selection["panels"]) != 2
        or len(set(selection["panels"])) != 2
        or any(type(p) is not int or p < 0 for p in selection["panels"])
    ):
        raise ValueError("Select two distinct coupled M5 panels")
    if base["population"]["clip_bounds"] is not None or base["population"]["value_bounds"] is not None:
        raise ValueError("The signed H64 target is ordinary unbounded actuator-normalized momentum")


def case_ids(settings, module):
    return (CASE,)


def _predict(c, coordinate, origin, force, receiver, rank, work):
    from .science import _reduced_propagation

    action = native.action_at(origin, native.coordinate(c, coordinate).member)
    basis = force.copy()
    try:
        while basis.shape[1] < rank:
            image = action(basis[:, -1:])
            for _ in range(2):
                image -= basis @ (basis.T @ image)
            length = float(np.linalg.norm(image))
            if length <= 1e-12:
                break
            basis = np.column_stack((basis, image[:, 0] / length))
    finally:
        work["native_hessian_actions"] += action.real_hessian_evaluations
    ledger = {"native_hessian_actions": 0, "native_hessian_attempts": 0}
    try:
        model = _reduced_propagation(
            c, coordinate, origin, basis, force, receiver, {}, [], method="INPUT", work_ledger=ledger
        )
    finally:
        work["native_hessian_actions"] += ledger["native_hessian_actions"]
    return float(model["prediction"][0][-1][0])


def acquire(settings, seed, module, prerequisites, sampling, assigned_modules):
    p, selection = settings["population"], settings["receiver_study"]["M5"]
    if (
        not sampling
        or type(sampling.get("audit_selected")) is not bool
        or not sampling.get("frame_id")
        or sampling["frame_size"] != p["frame_size"]
        or sampling["audit_size"] != p["audit_size"]
        or abs(float(sampling["inclusion_probability"]) - p["audit_size"] / p["frame_size"]) > 1e-14
    ):
        raise ValueError("M5 needs its assigned whole-root probability sample")
    c = {**settings["native"], "horizon_ticks": 64}
    pair = prerequisites["M1"]["response_preparation"]
    entry, instrument = pair["coordinates"]["nominal"], pair["instrument"]
    work = {
        "native_force_evaluations": 0,
        "native_hessian_actions": 0,
        "native_energy_evaluations": 0,
        "counts_are_lower_bounds": False,
    }
    case = {
        "case_id": CASE,
        "status": "COMPLETED",
        "auxiliary": 0.0,
        "one_coefficient": 0.0,
        "auxiliary_disposition": "FROZEN_ZERO",
        "sampling": sampling,
        "native_value": None,
        "numerical_difference": None,
        "force": None,
        "momentum_receiver": None,
        "native_selected": bool(sampling["audit_selected"] or p["mode"] == "reveal_all"),
        "preparation_cpu_seconds": pair.get("cpu_seconds"),
        "native_cpu_seconds": 0.0,
        "auxiliary_cpu_seconds": 0.0,
        "supplier_seconds": {"zero": 0.0, "one_coefficient": 0.0, "auxiliary": 0.0},
        "supplier_dispositions": {
            "zero": "FROZEN_ZERO",
            "one_coefficient": "FROZEN_ZERO",
            "auxiliary": "FROZEN_ZERO",
        },
        "native_calls_acquired": 0,
        "native_calls_attempted": 0,
    }
    actual = entry["status"] == instrument["status"] == "COMPLETED"
    case["frame_member_defined"] = actual
    if actual:
        force = np.asarray(instrument["forces"])[:, [instrument["force_roles"].index("FACTOR")]]
        receiver = np.concatenate((np.zeros(96), force[:, 0]))[None]
        case.update(force=force[:, 0].tolist(), momentum_receiver=receiver[0].tolist())
        scale = float(classical._scales(c)[-1, 1])
        before = process_time()
        origins = [service_origin(c, native.restore(entry["origins"][arm]["1"])) for arm in ARMS]
        for name, rank in (("one_coefficient", 1), ("auxiliary", p["auxiliary_rank"])):
            started = process_time()
            try:
                values = [
                    _predict(c, entry["coordinate"], origin, force, receiver, rank, work) / scale
                    for origin in origins
                ]
                case[name] = values[0] - values[1]
                case["supplier_dispositions"][name] = "FROZEN_ORIGIN_HESSIAN"
            except (FloatingPointError, OverflowError, np.linalg.LinAlgError) as error:
                case.setdefault("auxiliary_reasons", {})[name] = str(error)
                work["counts_are_lower_bounds"] = True
            finally:
                case["supplier_seconds"][name] = process_time() - started
        case["auxiliary_disposition"] = case["supplier_dispositions"]["auxiliary"]
        case["auxiliary_cpu_seconds"] = process_time() - before
    frozen = {
        name: case[name]
        for name in ("auxiliary", "one_coefficient", "force", "momentum_receiver", "supplier_dispositions")
    }
    case["frozen_sha256"] = sha256(json.dumps(frozen, sort_keys=True, allow_nan=False).encode()).hexdigest()
    if not actual:
        case.update(status="UNAVAILABLE", reason="SOURCE_PORT_OR_PAIRED_HANDOFF_UNAVAILABLE")
    elif case["native_selected"]:
        before = process_time()
        views = {}
        try:
            for refinement in (1, 2):
                arm_values = []
                for arm in ARMS:
                    panels = []
                    origin = native.restore(entry["origins"][arm][str(refinement)])
                    for panel in selection["panels"]:
                        case["native_calls_attempted"] += 1
                        response = native.paired_response(
                            c,
                            entry["coordinate"],
                            origin,
                            force,
                            receiver,
                            seed,
                            panel,
                            refinement=refinement,
                            origin_clock_multiplier=refinement,
                            synchronous_quench=True,
                            compute_tangent=False,
                        )
                        panels.append(float(response["odd_response"][0][-1][0]) / scale)
                        case["native_calls_acquired"] += 1
                        work["native_force_evaluations"] += response["force_evaluations"]
                        work["native_energy_evaluations"] += response["protocol_handoff_work"][
                            "potential_evaluations"
                        ]
                    arm_values.append(panels)
                views[str(refinement)] = arm_values
            primary, finer = (float(np.mean(np.subtract(*views[key]))) for key in ("1", "2"))
            case.update(
                native_value=primary, numerical_difference=abs(primary - finer), signed_arm_panel_values=views
            )
        except (FloatingPointError, OverflowError, np.linalg.LinAlgError) as error:
            case.update(status="UNAVAILABLE", reason=str(error), completed_views=views)
            for key in ("native_force_evaluations", "native_hessian_actions", "native_energy_evaluations"):
                work[key] += getattr(error, "partial_accounting", {}).get(key, 0)
            work["counts_are_lower_bounds"] = True
        case["native_cpu_seconds"] = process_time() - before
    return {"cases": [case], "work_accounting": work}


def analyse(settings, module, payload):
    options = settings["receiver_study"]["M5"]
    case = dict(payload["cases"][0])
    actual = case["native_value"]
    case["individual_checks"] = {}
    for name, prediction in (
        ("zero", 0.0),
        ("one_coefficient", case["one_coefficient"]),
        ("auxiliary", case["auxiliary"]),
    ):
        width = float(options["individual_halfwidth_actuator"])
        case["individual_checks"][name] = {
            "prediction": prediction,
            "individual_absolute_error": None if actual is None else abs(actual - prediction),
            "point_within_width": None if actual is None else abs(actual - prediction) <= width,
            "candidate_interval_excludes_zero": abs(prediction) > width,
            "within_numerical_allowance": None
            if actual is None
            else case["numerical_difference"] <= float(options["numerical_allowance_actuator"]),
            "prospective_calibrated_interval": False,
        }
    return {"cases": [case]}


def synthesise(settings, module, roots, alpha):
    options, p = settings["receiver_study"]["M5"], settings["population"]
    ordered_roots = sorted(roots, key=lambda r: r["seed"])
    cases = [root["cases"][0] for root in ordered_roots]
    n_total, n = len(cases), p["audit_size"]
    selected = [i for i, case in enumerate(cases) if case["sampling"]["audit_selected"]]
    if (
        len(selected) != n
        or n_total != p["frame_size"]
        or len({case["sampling"]["frame_id"] for case in cases}) != 1
    ):
        raise ValueError("M5 signed estimator needs the complete randomized paired frame")
    actual = [case["native_value"] for case in cases]
    undefined = [
        r["seed"] for r, case in zip(ordered_roots, cases, strict=True) if not case["frame_member_defined"]
    ]
    full = actual if p["mode"] == "reveal_all" else None
    target = float(options["mean_rms_budget_actuator"])
    halfwidth = float(options["mean_halfwidth_actuator"])
    risk = float(options["mean_error_risk"])
    comparisons = {}
    for key in ("auxiliary", "one_coefficient", "zero"):
        aux = [0.0 if key == "zero" else case[key] for case in cases]
        comparison = compare_finite_population_estimators(
            aux,
            selected,
            [actual[i] for i in selected],
            full_native_values=full,
            acquisition_mode=p["mode"],
            alpha=alpha / 3,
        )
        if undefined:
            comparison.update(status="UNRESOLVED", reason="ASSIGNED_PHYSICAL_FRAME_MEMBER_UNDEFINED")
            for label in ("residual_correction", "direct_sampling"):
                comparison[label].update(
                    status="UNRESOLVED",
                    estimate=None,
                    standard_error=None,
                    variance_estimate=None,
                    confidence_interval=None,
                    design_unbiased_if_complete=False,
                    reason="ASSIGNED_PHYSICAL_FRAME_MEMBER_UNDEFINED",
                )
        exact = comparison.get("full_frame_benchmark")
        if exact and exact["status"] == "ENUMERATED":
            variance = float(np.var(np.subtract(actual, aux), ddof=1)) if n_total > 1 else 0.0
            required = next(
                size for size in range(1, n_total + 1) if (1 - size / n_total) * variance / size <= target**2
            )
            exact.update(
                smallest_audit_for_mean_rms_budget=required,
                meets_mean_rms_budget=math.sqrt(exact["corrected_design_variance"]) <= target,
                smallest_audit_for_mean_halfwidth_at_risk=next(
                    size
                    for size in range(1, n_total + 1)
                    if (1 - size / n_total) * variance / size <= risk * halfwidth**2
                ),
                meets_mean_halfwidth_at_risk=exact["corrected_design_variance"] <= risk * halfwidth**2,
                chebyshev_halfwidth_at_risk=math.sqrt(exact["corrected_design_variance"] / risk),
            )
        comparisons[key] = comparison
    checks = {
        name: {
            "evaluated": sum(y["native_value"] is not None for y in cases),
            "point_within_width": sum(
                y["individual_checks"][name]["point_within_width"] is True for y in cases
            ),
            "sign_decisive_and_correct_on_both_views": int(
                sum(
                    y["native_value"] is not None
                    and y["individual_checks"][name]["candidate_interval_excludes_zero"]
                    and y["individual_checks"][name]["point_within_width"]
                    and y["individual_checks"][name]["within_numerical_allowance"]
                    and abs(
                        y["individual_checks"][name]["prediction"]
                        - np.mean(np.subtract(*y["signed_arm_panel_values"]["2"]))
                    )
                    <= float(options["individual_halfwidth_actuator"])
                    for y in cases
                )
            ),
            "zero_substitutions_due_to_supplier_failure": sum(
                y["supplier_dispositions"][name] == "FROZEN_ZERO" for y in cases
            )
            if name != "zero"
            else 0,
        }
        for name in comparisons
    }
    prep = [case["preparation_cpu_seconds"] for case in cases]
    acquired = [c for c in cases if c["native_value"] is not None]
    native_cost = sum(row["native_cpu_seconds"] for row in acquired) / len(acquired) if acquired else None
    auxiliary_cost = sum(row["auxiliary_cpu_seconds"] for row in cases)
    costs = {
        "actual_all_frame_preparation_cpu_seconds": None if None in prep else sum(prep),
        "actual_all_comparator_auxiliary_cpu_seconds": auxiliary_cost,
        "actual_native_cpu_seconds": sum(row["native_cpu_seconds"] for row in cases),
        "actual_native_audited_roots": len(acquired),
        "assigned_native_omissions": n_total - sum(row["native_selected"] for row in cases),
    }
    exact = comparisons["auxiliary"]["full_frame_benchmark"]
    economics = "UNRESOLVED"
    preferred = None
    supported = {"one_coefficient": False, "auxiliary": False}
    numerical_failures = sum(
        y["native_value"] is not None and not y["individual_checks"]["auxiliary"]["within_numerical_allowance"]
        for y in cases
    )
    if exact and exact["status"] == "ENUMERATED" and native_cost is not None and None not in prep:
        mean_prep = sum(prep) / n_total
        routes = {}
        for name, comparison in comparisons.items():
            benchmark = comparison["full_frame_benchmark"]
            size = benchmark["smallest_audit_for_mean_halfwidth_at_risk"]
            overhead = sum(c["supplier_seconds"][name] for c in cases)

            def priced(sample_size):
                return (
                    sample_size * (mean_prep + native_cost)
                    if name == "zero"
                    else sum(prep) + overhead + sample_size * native_cost
                )

            routes[name] = {
                "required_audit_roots": size,
                "expected_cpu_seconds": priced(size),
                "configured_n_cpu_seconds": priced(n),
                "configured_n_all_comparators_cpu_seconds": sum(prep) + auxiliary_cost + n * native_cost,
                "all_auxiliary_cpu_seconds": overhead,
            }
        preferred = min(
            ("zero", "one_coefficient", "auxiliary"), key=lambda label: routes[label]["expected_cpu_seconds"]
        )
        supported = {
            k: numerical_failures == 0
            and comparisons[k]["full_frame_benchmark"]["meets_mean_halfwidth_at_risk"]
            and routes[k]["configured_n_all_comparators_cpu_seconds"] < routes["zero"]["expected_cpu_seconds"]
            for k in ("one_coefficient", "auxiliary")
        }
        costs.update(
            equal_precision_routes=routes,
            modeled_direct_cpu_seconds=routes["zero"]["expected_cpu_seconds"],
            marginal_cost_scope="EXPECTED_SRS_CPU_ON_ENUMERATED_FRAME; ALL_PREPARATIONS_AND_SELECTED_NATIVE_FUTURES",
        )
        economics = "MODELED_SAVING" if preferred != "zero" else "RETAIN_DIRECT"
    selected_supplier = options["sparse_supplier"]
    estimate = comparisons[selected_supplier]["residual_correction"]
    return {
        "acquisition_mode": p["mode"],
        "frame_size": n_total,
        "audit_size": n,
        "signed_receiver": CASE,
        "units": "actuator-normalized-momentum",
        "finite_frame_comparisons": comparisons,
        "individual_checks": checks,
        "mean_rms_budget_actuator": target,
        "mean_halfwidth_actuator": halfwidth,
        "mean_error_risk": risk,
        "sparse_use": options["sparse_use"],
        "primary_supplier": selected_supplier,
        "costs": costs,
        "preferred_supplier": preferred,
        "economically_supported_suppliers": supported,
        "economically_supported_sparse_delivery": any(supported.values()),
        "assigned_root_seeds": [r["seed"] for r in ordered_roots],
        "sampled_root_seeds": [ordered_roots[i]["seed"] for i in selected],
        "undefined_frame_member_seeds": undefined,
        "decision": economics,
        "finite_frame_mean": estimate["estimate"],
        "mean_standard_error": estimate["standard_error"],
        "distribution_free_precision": (
            "CHEBYSHEV_USING_EXACT_VARIANCE_ON_THIS_ENUMERATED_FRAME"
            if exact and exact["status"] == "ENUMERATED"
            else "UNRESOLVED_UNBOUNDED_MOMENTUM"
        ),
        "sampled_numerical_failures": sum(
            actual[i] is not None
            and not cases[i]["individual_checks"]["auxiliary"]["within_numerical_allowance"]
            for i in selected
        ),
        "all_observed_numerical_failures": numerical_failures,
        "missing_sampled_root_seeds": [ordered_roots[i]["seed"] for i in selected if actual[i] is None],
    }
