# SPDX-License-Identifier: MPL-2.0
"""Calibration-only response laws, sealed action choice and finite-menu audit.

The numerical algorithms accept scientific records, never paths, native engines,
worker contexts or storage. Independent preparation roots are the sampling unit;
actions, horizons and receivers remain paired nested observations.
"""
from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
import json
import math
from statistics import mean, stdev

from empirical_lawhood.science.joint_description import (
    Assessment, FittedReceiver, Forecast, ForecastRow, Model, decimal,
)


def description_cost(description, economics):
    """Authored cost conversion, not a measured universal economic law."""
    return float(description.state_dimension * economics.state_price / economics.reuse_count
        + description.interface_dimension * economics.interface_price
        + description.memory_dimension * description.memory_samples * economics.memory_price
        + (description.forecast_work_units + len(description.features) + 1) * economics.compute_price)


def _fit(description, receiver, predictor_rows, outcome_rows, penalty):
    import numpy as np
    if description.model == "fixed":
        return FittedReceiver(description.description_id, receiver, description.features,
            (Decimal(0), Decimal(1)), (Decimal(0),), (Decimal(1),), "fitted", "known-mechanistic-forecast")
    observations = {r.key: r for r in outcome_rows}
    selected = []
    for row in predictor_rows:
        outcome = observations[row.key]
        if row.receiver_id == receiver and outcome.status == "supported" and all(f in dict(row.features) for f in description.features):
            selected.append((row, outcome))
    roots = {r.unit_id for r, _ in selected}
    if len(roots) < 1 or not selected:
        return FittedReceiver(description.description_id, receiver, description.features, (), (), (), "unavailable", "no-supported-calibration-roots")
    x = np.array([[float(dict(r.features)[f]) for f in description.features] for r, _ in selected])
    y = np.array([float(o.outcome) for _, o in selected])
    # Equal total weight per independent root, even with incomplete action panels.
    counts = {u: sum(r.unit_id == u for r, _ in selected) for u in roots}
    weights = np.array([1 / counts[r.unit_id] for r, _ in selected])
    center = np.average(x, axis=0, weights=weights)
    scale = np.sqrt(np.average((x-center)**2, axis=0, weights=weights))
    scale[scale < 1e-12] = 1
    matrix = np.column_stack((np.ones(len(x)), (x-center)/scale))
    regularizer = np.diag([0.0, *([float(penalty)] * len(description.features))])
    if not all(np.isfinite(value).all() for value in (matrix, regularizer, y)):
        return FittedReceiver(description.description_id, receiver, description.features, (), (), (), "unavailable", "nonfinite-calibration-design")
    try:
        coefficients = np.linalg.solve(matrix.T @ (weights[:, None] * matrix) + regularizer, matrix.T @ (weights*y))
    except np.linalg.LinAlgError:
        return FittedReceiver(description.description_id, receiver, description.features, (), (), (), "unavailable", "singular-calibration-design")
    if not np.isfinite(coefficients).all():
        return FittedReceiver(description.description_id, receiver, description.features, (), (), (), "unavailable", "nonfinite-calibration-fit")
    return FittedReceiver(description.description_id, receiver, description.features,
        tuple(decimal(v) for v in coefficients.tolist()), tuple(decimal(v) for v in center.tolist()),
        tuple(decimal(v) for v in scale.tolist()), "fitted", "")


def _prediction(fit, row):
    features = dict(row.features)
    if fit.status != "fitted" or any(f not in features for f in fit.feature_names):
        return None
    value = float(fit.coefficients[0]) + sum(float(c)*(float(features[f])-float(center))/float(scale)
        for f, c, center, scale in zip(fit.feature_names, fit.coefficients[1:], fit.center, fit.scale, strict=True))
    return value if math.isfinite(value) else None


def fit_response_laws(specification, calibration, *, record_id):
    """Leave-one-preparation-root-out selection; evaluation is not an operand."""
    if calibration.specification != specification.identity:
        raise ValueError("calibration belongs to another scientific specification")
    if {r.unit_id for r in calibration.predictors.rows} != set(specification.calibration_unit_ids):
        raise ValueError("calibration changed its complete independent-root cohort")
    policies = {r.receiver_id: r for r in specification.receivers}
    outcomes = {r.key: r for r in calibration.outcomes.rows}
    scores, fits = [], []
    for description in specification.descriptions:
        root_losses = []
        for root in specification.calibration_unit_ids:
            training_x = tuple(r for r in calibration.predictors.rows if r.unit_id != root)
            training_y = tuple(r for r in calibration.outcomes.rows if r.unit_id != root)
            fold = {receiver: _fit(description, receiver, training_x, training_y, specification.economics.ridge_penalty)
                for receiver in policies}
            losses, weights, predictions = [], [], {}
            for row in calibration.predictors.rows:
                if row.unit_id != root:
                    continue
                observed, policy = outcomes[row.key], policies[row.receiver_id]
                prediction = _prediction(fold[row.receiver_id], row)
                predictions[row.action, row.horizon, row.receiver_id] = prediction
                loss = float(specification.economics.missing_penalty)
                if prediction is not None and observed.status == "supported":
                    loss = ((prediction-float(observed.outcome))/float(policy.max_abs_error))**2
                losses.append(loss)
                weights.append(float(policy.weight))
            # The held-out calibration root is a complete simulated action
            # panel, but only its pre-response predictors choose an action.
            # Its outcomes score that frozen choice; evaluation is absent.
            controls = []
            for horizon in specification.horizons:
                menu = {}
                for action in specification.actions:
                    menu[action] = {receiver: predictions.get((action, horizon, receiver))
                                    for receiver in policies}
                selected = _choose_safe_action(menu, policies, specification.economics)
                if selected is None:
                    controls.append(float(specification.economics.missing_penalty))
                else:
                    values = {
                        receiver: (outcomes[root, selected, horizon, receiver].outcome
                                   if outcomes[root, selected, horizon, receiver].status == "supported" else None)
                        for receiver in policies
                    }
                    controls.append(_utility(values, policies, selected, specification.economics)[0])
            root_losses.append(_weighted_mean(losses, weights) + _finite_mean(controls))
        scores.append((description.description_id, decimal(mean(root_losses) + description_cost(description, specification.economics))))
        fits.extend(_fit(description, receiver, calibration.predictors.rows, calibration.outcomes.rows,
            specification.economics.ridge_penalty) for receiver in policies)
    selected = min(scores, key=lambda p: (p[1], p[0]))[0]
    return Model(record_id, specification.identity, calibration.identity,
        tuple(sorted(fits, key=lambda r: (r.description_id, r.receiver_id))), tuple(sorted(scores)), selected)


def _utility(values, policies, action, economics):
    if any(receiver not in values or values[receiver] is None for receiver in policies):
        return float(economics.missing_penalty), False
    result = float(economics.action_price) * abs(float(action))
    safe = True
    for receiver, policy in policies.items():
        value = float(values[receiver])
        result += float(policy.weight) * ((value-float(policy.target))/float(policy.scale))**2
        if ((policy.safety_lower is not None and value < float(policy.safety_lower))
                or (policy.safety_upper is not None and value > float(policy.safety_upper))):
            safe = False
    if not safe:
        result += float(economics.safety_penalty)
    if not math.isfinite(result):
        raise ValueError("authored utility overflowed its finite numerical accounting")
    return result, safe


def _choose_safe_action(menu, policies, economics):
    """A predicted guard failure is a no-entry decision, not a priced action."""
    candidates = []
    for action, values in menu.items():
        if any(values.get(receiver) is None for receiver in policies):
            continue
        loss, safe = _utility(values, policies, action, economics)
        if safe:
            candidates.append((loss, action))
    return min(candidates)[1] if candidates else None


def _finite_mean(values):
    if not values or any(not math.isfinite(value) for value in values):
        raise ValueError("root accounting requires a nonempty finite outcome census")
    value = mean(values)
    if not math.isfinite(value):
        raise ValueError("root mean overflowed finite numerical accounting")
    return value


def _weighted_mean(values, weights):
    """One normalized receiver-weighted loss per independent root.

    Receiver weights are not divided by the receiver count a second time.
    Scaling weights first also avoids overflow from an irrelevant common
    multiplicative choice of weight units.
    """
    if (not values or len(values) != len(weights)
            or any(not math.isfinite(value) for value in values)
            or any(not math.isfinite(weight) or weight <= 0 for weight in weights)):
        raise ValueError("weighted root accounting needs finite values and positive matching weights")
    largest = max(weights)
    denominator = math.fsum(weight / largest for weight in weights)
    result = math.fsum(value * (weight / largest) / denominator
                       for value, weight in zip(values, weights, strict=True))
    if not math.isfinite(result):
        raise ValueError("weighted root mean overflowed finite numerical accounting")
    return result


def forecast_and_choose(specification, model, predictors, *, record_id):
    """Frozen response laws see only predictors; action choices precede scoring."""
    if model.specification != specification.identity or predictors.specification != specification.identity:
        raise ValueError("forecast operands belong to another authored experiment")
    if {r.unit_id for r in predictors.rows} != set(specification.evaluation_unit_ids):
        raise ValueError("forecast changed its independent evaluation cohort")
    fits = {(r.description_id, r.receiver_id): r for r in model.fits}
    rows, selections = [], []
    values = {}
    for row in predictors.rows:
        for description in specification.descriptions:
            prediction = _prediction(fits[description.description_id, row.receiver_id], row)
            rows.append(ForecastRow(*row.key, description.description_id,
                None if prediction is None else decimal(prediction), "unavailable-predictor-or-fit" if prediction is None else ""))
            values[row.unit_id, row.horizon, description.description_id, row.action, row.receiver_id] = prediction
    policies = {r.receiver_id: r for r in specification.receivers}
    for unit in specification.evaluation_unit_ids:
        for horizon in specification.horizons:
            for description in specification.descriptions:
                menu = {}
                for action in specification.actions:
                    predicted = {r: values[unit, horizon, description.description_id, action, r] for r in policies}
                    menu[action] = predicted
                selections.append((unit, horizon, description.description_id,
                                   _choose_safe_action(menu, policies, specification.economics)))
    return Forecast(record_id, specification.identity, model.identity, predictors.identity,
        tuple(sorted(rows, key=lambda r: r.key)), tuple(sorted(selections)))


def _summary(values):
    average = None if not values else _finite_mean(values)
    error = None if len(values) < 2 else stdev(values)/math.sqrt(len(values))
    if error is not None and not math.isfinite(error):
        raise ValueError("root uncertainty overflowed finite numerical accounting")
    return {"independent_roots": len(values), "mean": average,
        "standard_error": error,
        "uncertainty": "standard error over independent roots; no asymptotic coverage guarantee"}


def assess_descriptions(specification, model, forecast, outcomes, *, record_id):
    """All-use error/control/cost accounting with explicit conditional support."""
    if (model.specification != specification.identity or forecast.specification != specification.identity
            or outcomes.specification != specification.identity or forecast.model != model.identity):
        raise ValueError("assessment substituted the frozen model, specification or forecast")
    observed = {r.key: r for r in outcomes.rows}
    expected = {(u, a, h, r.receiver_id) for u in specification.evaluation_unit_ids
        for a in specification.actions for h in specification.horizons for r in specification.receivers}
    if set(observed) != expected or {r.key[:4] for r in forecast.rows} != expected:
        raise ValueError("evaluation omits or adds an assigned root/action/horizon/receiver")
    policies = {r.receiver_id: r for r in specification.receivers}
    selected = {(u,h,d): a for u,h,d,a in forecast.selected_actions}
    forecasts = {r.key: r for r in forecast.rows}
    results, root_economics = [], {}
    for description in specification.descriptions:
        did = description.description_id
        root_losses, root_controls, root_regrets, root_costs = [], [], [], []
        supported = failures = safety_failures = selected_supported = complete_menus = feasible_menus = 0
        receiver_errors = defaultdict(list)
        for unit in specification.evaluation_unit_ids:
            losses, weights, controls, regrets = [], [], [], []
            for key in sorted(k for k in expected if k[0] == unit):
                original, prediction, policy = observed[key], forecasts[(*key,did)].prediction, policies[key[3]]
                loss = float(specification.economics.missing_penalty)
                if original.status == "supported" and prediction is not None:
                    absolute = abs(float(prediction)-float(original.outcome))
                    receiver_errors[key[3]].append(absolute)
                    loss = (absolute/float(policy.max_abs_error))**2
                    supported += 1
                else:
                    failures += 1
                losses.append(loss)
                weights.append(float(policy.weight))
            for horizon in specification.horizons:
                action = selected[unit,horizon,did]
                menu = []
                for candidate in specification.actions:
                    values = {r: (observed[unit,candidate,horizon,r].outcome
                        if observed[unit,candidate,horizon,r].status == "supported" else None) for r in policies}
                    loss, safe = _utility(values, policies, candidate, specification.economics)
                    menu.append((candidate, loss, safe, all(v is not None for v in values.values())))
                actual = next((m for m in menu if m[0] == action), None)
                control = float(specification.economics.missing_penalty) if actual is None else actual[1]
                selected_supported += int(actual is not None and actual[3])
                safety_failures += int(actual is not None and actual[3] and not actual[2])
                controls.append(control)
                # Omitting an unavailable alternative can falsely shrink
                # oracle regret.  Only a complete finite menu identifies it.
                complete = all(m[3] for m in menu)
                complete_menus += int(complete)
                feasible = [m[1] for m in menu if m[3] and m[2]]
                feasible_menus += int(complete and bool(feasible))
                regrets.append(float(specification.economics.missing_penalty)
                    if actual is None or not actual[3] or not complete or not feasible
                    else max(0.0, control-min(feasible)))
            root_losses.append(_weighted_mean(losses, weights)); root_controls.append(_finite_mean(controls)); root_regrets.append(_finite_mean(regrets))
            root_costs.append(_weighted_mean(losses, weights)+_finite_mean(controls)+description_cost(description, specification.economics))
        coverage = supported/len(expected)
        control_coverage = selected_supported/(len(specification.evaluation_unit_ids)*len(specification.horizons))
        useful = (coverage >= float(specification.economics.minimum_coverage)
            and control_coverage >= float(specification.economics.minimum_coverage)
            and mean(root_losses) <= 1 and mean(root_regrets) <= float(specification.economics.maximum_control_regret)
            and safety_failures == 0)
        receiver_report = {r: {"units": p.units, "max_abs_error": str(p.max_abs_error),
            "supported_observations": len(receiver_errors[r]),
            "conditional_mean_absolute_error": mean(receiver_errors[r]) if receiver_errors[r] else None}
            for r,p in policies.items()}
        root_economics[did] = root_costs
        results.append({"description": did, "state_dimension": description.state_dimension,
            "interface_scalars_per_use": description.interface_dimension,
            "memory_scalar_samples": description.memory_dimension*description.memory_samples,
            "predictor_multiply_add_units": len(description.features)+1,
            "authored_forecast_construction_work_units": str(description.forecast_work_units),
            "forecast_work_unit": description.forecast_work_unit,
            "forecast_work_basis": description.forecast_work_basis,
            "forecast_computation_cost_scope": "authored construction estimate plus fixed-feature evaluator multiply-adds; shared native acquisition is separate",
            "authored_description_cost_per_use": description_cost(description,specification.economics),
            "supported": supported, "unavailable": failures, "assigned_observations": len(expected),
            "coverage": coverage, "control_coverage": control_coverage, "safety_failures": safety_failures,
            "complete_action_menus": complete_menus,
            "complete_menus_with_safe_alternative": feasible_menus,
            "assigned_action_menus": len(specification.evaluation_unit_ids)*len(specification.horizons),
            "oracle_regret_scope": "complete observed finite action menu with a safe alternative only; missing/infeasible menu receives authored missing penalty",
            "all_use_normalized_prediction_loss": _summary(root_losses), "control_loss": _summary(root_controls),
            "paired_action_panel_regret": _summary(root_regrets), "total_economic_loss": _summary(root_costs),
            "useful_under_authored_thresholds": useful, "receiver_errors": receiver_report})
    useful = [r for r in results if r["useful_under_authored_thresholds"]]
    minimum = min(useful, key=lambda r:(r["total_economic_loss"]["mean"],r["state_dimension"],r["description"])) if useful else None
    baseline = "joint" if "joint" in root_economics else specification.descriptions[0].description_id
    paired = {d: _summary([a-b for a,b in zip(values,root_economics[baseline],strict=True)])
        for d,values in root_economics.items()}
    # Pareto comparison reports the channels rather than hiding their exchange rate.
    def vector(r):
        return (r["state_dimension"],r["interface_scalars_per_use"],r["memory_scalar_samples"],
            float(r["authored_forecast_construction_work_units"])+r["predictor_multiply_add_units"],
            r["all_use_normalized_prediction_loss"]["mean"],r["control_loss"]["mean"])
    pareto = [r["description"] for r in results if not any(
        all(a<=b for a,b in zip(vector(q),vector(r),strict=True)) and any(a<b for a,b in zip(vector(q),vector(r),strict=True))
        for q in results if q is not r)]
    result = {"claim_scope":"FINITE_AUTHORED_MENU_AND_TASK_FAMILY", "family_id":specification.family_id,
        "question":specification.question, "scientific_scope":"held-out development action-panel audit; no universal irreducibility or physical prospective-control claim",
        "calibration_selected_description":model.selected_description,
        "evaluation_cost_minimum_exploratory":None if minimum is None else minimum["description"],
        "hypothesis_disposition":"NO_USEFUL_TESTED_DESCRIPTION" if not useful else "FINITE_MENU_CANDIDATES_IDENTIFIED_REQUIRES_NEW_CONFIRMATION",
        "nondominated_descriptions":pareto,
        "nondominated_vector_axes":("state_dimension", "interface_scalars_per_use", "memory_scalar_samples",
            "authored_forecast_construction_plus_evaluator_work", "all_use_normalized_prediction_loss", "control_loss"),
        "nondominated_forecast_work_unit":specification.descriptions[0].forecast_work_unit,
        "descriptions":results,
        "paired_economic_differences":{"reference_description":baseline,"contrasts":paired},
        "accounting_unit":specification.economics.accounting_unit,
        "shared_acquisition_work_units":sum(float(r.work_units) for r in outcomes.rows),
        "acquisition_cost_scope":"producer-declared work units; shared across description comparisons; measured runtime costs remain in native receipts",
        "economic_sensitivity_required":"Rerun assessment with separately authored prices/thresholds; this report is conditional on its exact economics.",
        "source_kind":outcomes.source_kind, "provenance":outcomes.provenance}
    return Assessment(record_id,specification.identity,model.identity,forecast.identity,outcomes.identity,
        json.dumps(result,allow_nan=False,sort_keys=True,separators=(",",":")))
