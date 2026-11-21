# SPDX-License-Identifier: MPL-2.0
"""Complete independent-root reductions of retained classical-series readouts.

These are descriptive population summaries with explicitly conditional sampling
calculations. They do not retrospectively turn a development study into a
qualified confirmation or treat nested trajectories/cells as independent units.
"""
from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from fractions import Fraction
from functools import lru_cache
import math

from empirical_lawhood.methods.statistics.experimental_statistics import (
    binomial_probability_interval,
    binomial_upper_tail,
)


def _probability(value):
    if isinstance(value, bool):
        raise TypeError("interval alpha requires an explicit probability")
    alpha = Fraction(str(value)) if isinstance(value, (str, float)) else Fraction(value)
    if not 0 < alpha < 1:
        raise ValueError("interval alpha must lie strictly between zero and one")
    return alpha


def _ratio(value: Fraction):
    return {"numerator": value.numerator, "denominator": value.denominator,
            "value": float(value)}


@lru_cache(maxsize=4096)
def _interval_values(n, successes, alpha):
    interval = binomial_probability_interval(n, successes, tail_probability=alpha / 2)
    return float(interval.lower), float(interval.upper)


def _interval(n, successes, alpha):
    if n == 0:
        return None
    return list(_interval_values(n, successes, alpha))


def event_summary(events: Mapping[int, bool | None], *, alpha=Fraction(1, 20), null_probability=None):
    """Assigned-population CP envelope over every unresolved outcome completion."""
    a = _probability(alpha)
    if not events or any(type(seed) is not int or seed < 0 for seed in events):
        raise ValueError("events require a nonempty assigned independent-root census")
    if any(value is not None and type(value) is not bool for value in events.values()):
        raise TypeError("root events must be True, False or None")
    success = sorted(seed for seed, value in events.items() if value is True)
    failure = sorted(seed for seed, value in events.items() if value is False)
    unknown = sorted(seed for seed, value in events.items() if value is None)
    n, s, u = len(events), len(success), len(unknown)
    lower = _interval(n, s, a)[0]
    upper = _interval(n, s + u, a)[1]
    result = {"assigned_roots": n, "successes": s, "failures": len(failure), "unknown": u,
        "success_seeds": success, "failure_seeds": failure, "unknown_seeds": unknown,
        "assigned_success_fraction_lower": s / n, "assigned_success_fraction_upper": (s + u) / n,
        "population_interval_over_missing_completions": [lower, upper],
        "complete_case_interval": _interval(n - u, s, a),
        "interval_alpha": _ratio(a),
        "inference_scope": "MARGINAL_DESCRIPTIVE; INDEPENDENT_COMMON_BERNOULLI_ROOTS_REQUIRED; NOT_MULTIPLICITY_ADJUSTED"}
    if null_probability is not None:
        p0 = _probability(null_probability)
        result["null_probability"] = _ratio(p0)
        result["conservative_assigned_upper_tail"] = _ratio(binomial_upper_tail(n, s, p0))
        result["test_scope"] = "UNADJUSTED_CONDITIONAL_CALCULATION; UNKNOWN_ROOTS_ARE_OPERATIONAL_NONSUCCESS; NO_AUTOMATIC_QUALIFICATION"
    return result


def _conjunction(values):
    values = tuple(values)
    if any(value is False for value in values):
        return False
    if not values or any(value is None for value in values):
        return None
    return True


def _finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def _preparation(rows, seeds, alpha):
    states = {}
    nominees = set()
    for seed in seeds:
        stage = rows.get(seed, {}).get("stages", {}).get("e5")
        if not stage or stage.get("status") != "PAIRED_CONFIRMATION":
            states[seed] = None
            continue
        nominee = stage.get("nominee")
        if not nominee:
            raise ValueError("paired preparation outcome lacks its frozen nominee")
        nominees.add(nominee)
        gain, harm = stage.get("gain"), stage.get("harm")
        if type(gain) is not bool or type(harm) is not bool or gain and harm:
            raise ValueError("preparation root has incompatible gain/harm states")
        states[seed] = "gain" if gain else "harm" if harm else "unchanged"
    if len(nominees) > 1:
        raise ValueError("a confirmation population cannot silently combine different nominees")
    gains = sum(value == "gain" for value in states.values())
    harms = sum(value == "harm" for value in states.values())
    unknown = sum(value is None for value in states.values())
    discordant = gains + harms
    tail = binomial_upper_tail(discordant, gains, Fraction(1, 2)) if discordant else Fraction(1)
    worst = binomial_upper_tail(discordant + unknown, gains, Fraction(1, 2)) if discordant + unknown else Fraction(1)
    n = len(seeds)
    return {"assigned_roots": n, "nominee": next(iter(nominees), None),
        "gains": gains, "harms": harms, "unchanged": n - gains - harms - unknown,
        "unknown_or_not_entered": unknown,
        "net_gain_fraction_completion_bounds": [(gains - harms - unknown) / n, (gains - harms + unknown) / n],
        "complete_pair_discordance_tail": _ratio(tail),
        "worst_completion_discordance_tail": _ratio(worst),
        "gain_population": event_summary({s: None if v is None else v == "gain" for s, v in states.items()}, alpha=alpha),
        "harm_population": event_summary({s: None if v is None else v == "harm" for s, v in states.items()}, alpha=alpha),
        "test_scope": "PAIRED_EXACT_CONDITIONAL_DISCORDANCE; INDEPENDENT_ROOT_PAIRS_AND_VALID_SIGN_NULL_REQUIRED; DESCRIPTIVE_UNADJUSTED",
        "qualification": "NOT_ESTABLISHED"}


def _parameter_relations(rows, seeds, alpha, selected):
    """One assigned CONF root per event, with frame-wide CAL coverage kept intact."""
    expected_ids=tuple(x['id'] for x in selected['coordinates']) if selected is not None else ()
    training_ids=tuple(selected['relation_training_coordinates']) if selected is not None else ()
    enabled=bool(training_ids) and bool(set(selected['phases']) & {'e4','e6'}) if selected is not None else False
    stages={}; packages=set(); discovered_ids=set(); frames=set()
    root_census=[]
    for seed in seeds:
        stages_for_root=rows.get(seed,{}).get('stages',{})
        copies=[stages_for_root[phase]['parameter_relation'] for phase in ('e4','e6')
                if isinstance(stages_for_root.get(phase),Mapping) and 'parameter_relation' in stages_for_root[phase]]
        if len(copies)==2 and copies[0]!=copies[1]:
            raise ValueError('E4/E6 must reference the same frozen parameter-relation readout')
        stage=copies[0] if copies else None
        if stage is None:
            reason='MISSING_CONFIRMATION_READOUT' if seed not in rows else 'MISSING_PARAMETER_RELATION_FIELD'
            root_census.append({'seed':seed,'status':'UNAVAILABLE','reason':reason})
            continue
        if not isinstance(stage,Mapping):
            raise ValueError('parameter-relation readout must be a typed mapping')
        if stage.get('status')=='NOT_ENTERED':
            root_census.append({'seed':seed,'status':'NOT_ENTERED','reason':stage.get('reason')})
            continue
        enabled=True
        if stage.get('refits_on_confirmation')!=0:
            raise ValueError('parameter relation confirmation changed its frozen fitted package')
        if stage.get('coverage_transported_to_new_coordinates') is not False:
            raise ValueError('parameter relation cannot inherit calibration coverage at transfer coordinates')
        if not stage.get('package_sha256') or not isinstance(stage.get('training_coordinates'),list):
            root_census.append({'seed':seed,'status':'UNAVAILABLE','reason':'MISSING_FROZEN_RELATION_IDENTITY_OR_FRAME'})
            continue
        packages.add(stage['package_sha256'])
        frame=tuple(stage['training_coordinates'])
        if len(set(frame))!=len(frame):
            raise ValueError('relation training-coordinate frame is duplicated')
        frames.add(frame)
        coordinate_rows={}
        for coordinate in stage.get('coordinates',()):
            identity=coordinate.get('coordinate',{}).get('id')
            if not identity or identity in coordinate_rows:
                raise ValueError('parameter-relation coordinate identity is missing or duplicated')
            if expected_ids and identity not in expected_ids:
                raise ValueError('parameter-relation coordinate outside the authored frame')
            if coordinate.get('training_coordinate') is not (identity in frame):
                raise ValueError('parameter-relation training/transfer label changes its frozen frame')
            coordinate_rows[identity]=coordinate
            discovered_ids.add(identity)
        stages[seed]=coordinate_rows
        root_census.append({'seed':seed,'status':stage.get('status','UNAVAILABLE'),
                            'reason':stage.get('reason'),'available_coordinates':len(coordinate_rows)})
    if len(packages)>1 or len(frames)>1:
        raise ValueError('confirmation population combines different fitted relation packages or frames')
    observed_frame=next(iter(frames),())
    if training_ids and observed_frame and training_ids!=observed_frame:
        raise ValueError('relation calibration frame differs from authored training coordinates')
    training_ids=training_ids or observed_frame
    ids=expected_ids if enabled else ()
    if not ids and enabled:
        ids=tuple(sorted(discovered_ids | set(training_ids)))
    events=('admitted','delivered_service','false_admission','covered','actual_adequate')
    cells={}; unavailable=[]
    for identity in ids:
        for account in ('baseline','structure'):
            outcomes={event:{} for event in events}
            for seed in seeds:
                coordinate=stages.get(seed,{}).get(identity)
                model=coordinate.get('models',{}).get(account) if coordinate is not None else None
                if not isinstance(model,Mapping) or 'status' not in model or any(event not in model for event in events):
                    unavailable.append({'seed':seed,'coordinate':identity,'account':account,
                        'reason':'MISSING_RELATION_COORDINATE' if coordinate is None else 'MISSING_RELATION_ACCOUNT_OR_EVENT'})
                    for event in events:
                        outcomes[event][seed]=None
                    continue
                if identity not in training_ids and model.get('coverage_inherited') is True:
                    raise ValueError('a transfer prediction claims inherited calibration coverage')
                for event in events:
                    value=model[event]
                    if value is not None and type(value) is not bool:
                        raise ValueError('parameter-relation event must retain boolean or unknown state')
                    if model['status']=='UNAVAILABLE' or event=='false_admission' and model.get('unresolved_admitted_future'):
                        value=None
                    outcomes[event][seed]=value
            for event in events:
                cells[(identity,account,event)]=outcomes[event]
    training_table=[]; transfer_table=[]
    for (identity,account,event),outcomes in sorted(cells.items()):
        entry={'coordinate':identity,'account':account,'event':event,
               **event_summary(outcomes,alpha=alpha)}
        (training_table if identity in training_ids else transfer_table).append(entry)
    joint=[]
    for account in ('baseline','structure'):
        if not training_ids or not enabled:
            continue
        for event in ('covered','delivered_service','false_admission'):
            outcomes={}
            for seed in seeds:
                values=[cells.get((identity,account,event),{}).get(seed) for identity in training_ids]
                if event=='false_admission':
                    outcomes[seed]=True if any(v is True for v in values) else None if any(v is None for v in values) else False
                else:
                    outcomes[seed]=_conjunction(values)
            joint.append({'account':account,
                'event':{'covered':'all_training_coordinates_covered','delivered_service':'all_training_coordinates_delivered',
                         'false_admission':'any_training_coordinate_false_admission'}[event],
                **event_summary(outcomes,alpha=alpha)})
    return {'status':'CENSUS_COMPLETE_WITH_TYPED_MISSINGNESS' if enabled else 'NOT_ENTERED',
        'assigned_confirmation_roots':len(seeds),'available_relation_roots':len(stages),
        'package_sha256':next(iter(packages),None),'training_coordinates':list(training_ids),
        'training_frame':training_table,'transfer_coordinates':transfer_table,
        'simultaneous_training_frame':joint,'root_census':root_census,'unavailable_cells':unavailable,
        'refits_on_confirmation':0,'coverage_transported_to_new_coordinates':False,
        'training_coverage_scope':'FROZEN_CALIBRATION_ROOT_MAXIMUM_OVER_COMPLETE_DECLARED_TRAINING_COORDINATE_FRAME',
        'transfer_coverage_scope':'EMPIRICAL_ASSIGNED_ROOT_COVERAGE_ONLY; NO_INHERITED_CALIBRATION_GUARANTEE',
        'independent_unit':'ASSIGNED_CONFIRMATION_ROOT; COORDINATES_AND_ACCOUNTS_ARE_NESTED',
        'historical_reproduction':False}


def aggregate_readouts(readouts, *, assigned_seeds, alpha=Fraction(1, 20), win_margin=Decimal("0.1"), scientific_settings=None):
    """Reduce every assigned CONF root, retaining absent readouts as unknown.

    ``readouts`` may be a sequence or mapping of the original domain analysis
    payloads. Transport/custody authentication belongs to the calling public
    reader. Forecast comparisons use one whole-root result per coordinate; all
    views, actions, panels and receiver components remain nested.
    """
    seeds = tuple(assigned_seeds)
    if (not seeds or any(type(s) is not int or s < 0 for s in seeds)
            or len(set(seeds)) != len(seeds)):
        raise ValueError("the exact unique nonempty confirmation-root roster is required")
    seeds = tuple(sorted(seeds))
    a = _probability(alpha)
    margin = float(win_margin)
    if not math.isfinite(margin) or margin < 0:
        raise ValueError("forecast win margin must be finite and nonnegative")
    rows = {}
    for row in readouts.values() if isinstance(readouts, Mapping) else readouts:
        if not isinstance(row, Mapping) or row.get("schema") != "classical-series-analysis.v1":
            raise ValueError("aggregate consumes exact classical-series analysis payloads")
        seed = row.get("seed")
        if type(seed) is not int or seed not in seeds or seed in rows:
            raise ValueError("analysis root is duplicated or outside the assigned confirmation roster")
        if row.get("census", {}).get("independent_units") != 1:
            raise ValueError("each analysis contributes exactly one independent root")
        rows[seed] = row

    occurrence, adequacy, forecasts, capstones, preparation_connections = {}, {}, {}, {}, {}
    selected=None
    if scientific_settings is not None:
        from .science import METHODS, normalise_config
        from .capstones import _settings as capstone_settings
        selected = normalise_config(scientific_settings)
        phases = set(selected["phases"])
        for coordinate in selected["coordinates"]:
            identity = coordinate["id"]
            for arm in selected["preparation_arms"]:
                if "e1" in phases:
                    for view in ("PRIMARY", "FINE"):
                        for sector in ("X", "Y"):
                            for event in ("occurrence", "joint_survival"):
                                occurrence[(identity, arm, view, sector, event)] = {}
                if "e2" in phases:
                    for method in METHODS:
                        for policy in ("frozen", "refresh"):
                            adequacy[(identity, arm, method, policy)] = {}
                for connection in phases & {"capstone-forecast", "capstone-preparation"}:
                    for task in capstone_settings(selected)["tasks"]:
                        for event in ("admitted", "delivered_service", "false_admission", "covered"):
                            capstones[(connection, identity, arm, task["task_id"], event)] = {}
                    capstones[(connection, identity, arm, "ALL_ASSIGNED_TASKS", "delivered_service")] = {}
            transfer = (Decimal(coordinate["temperature"]) in (Decimal("1.125"), Decimal("3.25"))
                and Decimal(coordinate["friction"]) == 1 and Decimal(coordinate["cross_coupling"]) == 1)
            if "e3" in phases or "e6" in phases and transfer:
                for account in ("baseline", "structure"):
                    for event in ("admitted", "delivered_service", "false_admission", "covered"):
                        forecasts[(identity, account, event)] = {}
                forecasts[(identity, "structure-v-baseline", "margin_win")] = {}
    sci01 = []
    method_control = []
    for seed, row in sorted(rows.items()):
        stages = row["stages"]
        for case in stages.get("e1", {}).get("cases", ()):
            for view in ("PRIMARY", "FINE"):
                for sector in ("X", "Y"):
                    for event in ("occurrence", "joint_survival"):
                        occurrence.setdefault((case["coordinate"], case["arm"], view, sector, event), {})
            for trace in case.get("traces", ()):
                for event in ("occurrence", "joint_survival"):
                    key = (case["coordinate"], case["arm"], trace["view"], trace["sector"], event)
                    value = trace[event]
                    if value is not None and type(value) is not bool:
                        raise ValueError("structural event has no boolean or unknown state")
                    occurrence.setdefault(key, {})[seed] = value
        for case in stages.get("e2", {}).get("cases", ()):
            for method in stages["e2"].get("method_menu", ()):
                for policy in ("frozen", "refresh"):
                    adequacy.setdefault((case["coordinate"]["id"], case["arm"], method, policy), {})
            for method, scores in case.get("method_scores", {}).items():
                for policy in ("frozen", "refresh"):
                    key = (case["coordinate"]["id"], case["arm"], method, policy)
                    value = None
                    if case["status"] == "COMPLETED" and case.get("numerical_policy_pass") is True:
                        value = _conjunction(score.get(policy + "_adequate") for score in scores)
                    adequacy.setdefault(key, {})[seed] = value
        forecast = stages.get("e3") or stages.get("e6") or {}
        for coordinate in forecast.get("coordinates", ()):
            identity = coordinate["coordinate"]["id"]
            for account, model in coordinate.get("models", {}).items():
                for event in ("admitted", "delivered_service", "false_admission", "covered"):
                    key = (identity, account, event)
                    value = model.get(event)
                    if model.get("status") == "UNAVAILABLE" or event == "false_admission" and model.get("unresolved_admitted_future"):
                        value = None
                    if value is not None and type(value) is not bool:
                        raise ValueError("forecast event has no boolean or unknown state")
                    forecasts.setdefault(key, {})[seed] = value
            base = coordinate.get("models", {}).get("baseline", {}).get("point_absolute_error")
            structural = coordinate.get("models", {}).get("structure", {}).get("point_absolute_error")
            win = None if not _finite(base) or not _finite(structural) else base - structural >= margin
            forecasts.setdefault((identity, "structure-v-baseline", "margin_win"), {})[seed] = win
        for connection in ("capstone-forecast", "capstone-preparation"):
            stage = stages.get(connection, {})
            if stage and stage.get("coefficient_refits_on_confirmation") != 0:
                raise ValueError("capstone confirmation changed its frozen downstream predictor")
            for case in stage.get("cases", ()):
                identity, arm = case["coordinate"]["id"], case["arm"]
                tasks = case["tasks"]
                for task in tasks:
                    for event in ("admitted", "delivered_service", "false_admission", "covered"):
                        value = task[event]
                        if value is not None and type(value) is not bool:
                            raise ValueError("capstone task outcome must retain boolean or unknown status")
                        key = (connection, identity, arm, task["task_id"], event)
                        capstones.setdefault(key, {})[seed] = value
                key = (connection, identity, arm, "ALL_ASSIGNED_TASKS", "delivered_service")
                capstones.setdefault(key, {})[seed] = _conjunction(t["delivered_service"] for t in tasks)
            for pair in stage.get("comparisons", ()):
                if pair.get("same_complete_package") is not True:
                    raise ValueError("preparation connection changed the downstream package")
                for event in ("gain", "harm"):
                    value = pair[event] if pair["complete_pair"] else None
                    if value is not None and type(value) is not bool:
                        raise ValueError("preparation connection has no boolean or unknown outcome")
                    key = (pair["coordinate"]["id"], pair["nominee"] or "NOT_NOMINATED", event)
                    preparation_connections.setdefault(key, {})[seed] = value
        if "sci01" in stages:
            stage = stages["sci01"]
            sci01.append({"seed": seed, "assigned_nested_cells": stage.get("assigned_cells", 0),
                "evaluable_nested_cells": stage.get("evaluable_cells", 0),
                "reversal_nested_cells": stage.get("endpoint_improvement_contrast_reversals", 0),
                "method_census": stage.get("census", [])})
        if "derivations" in stages:
            stage = stages["derivations"]
            method_control.append({"seed":seed, "status":stage["status"],
                "resolvent_enclosure_contains_oracle":stage.get("resolvent_enclosure_contains_oracle"),
                "resolvent_error":stage.get("resolvent_error"),
                "resolvent_residual_bound":stage.get("resolvent_residual_bound"),
                "finite_tail_dense_oracle_error":stage.get("finite_tail_dense_oracle_error"),
                "finite_operator_update_error":stage.get("finite_operator_update_error")})

    def summarize(cells, names):
        table = []
        for key, outcomes in sorted(cells.items()):
            row = dict(zip(names, key, strict=True))
            row.update(event_summary({seed:outcomes.get(seed) for seed in seeds}, alpha=a,
                null_probability=Fraction(1,2) if key[-1] == "margin_win" else None))
            table.append(row)
        return table

    native_times = [row.get("native_seconds") for row in rows.values()]
    analysis_times = [row.get("analysis_seconds") for row in rows.values()]
    return {"schema":"classical-series-population-readout.v1", "assigned_confirmation_roots":len(seeds),
        "assigned_seeds":list(seeds), "readout_available_roots":len(rows),
        "missing_readout_seeds":[s for s in seeds if s not in rows],
        "cell_census_source":("AUTHORED_SETTINGS_AND_ORIGINAL_READOUTS" if scientific_settings is not None
            else "ORIGINAL_READOUT_CASE_ROSTERS" if rows else "UNAVAILABLE_NO_AUTHORED_SETTINGS_OR_READOUT_ROSTERS"),
        "qualification":"NOT_ESTABLISHED", "historical_decisions_changed":False,
        "structural_events":summarize(occurrence, ("coordinate","arm","view","sector","event")),
        "mechanical_adequacy":summarize(adequacy, ("coordinate","arm","method","policy")),
        "forecast_and_transfer":summarize(forecasts, ("coordinate","account","event")),
        "parameter_relations":_parameter_relations(rows,seeds,a,selected),
        "capstone_connections":summarize(capstones, ("connection","coordinate","arm","task","event")),
        "capstone_preparation_gains":summarize(preparation_connections, ("coordinate","nominee","event")),
        "forecast_win_margin":margin,
        "paired_preparation":_preparation(rows,seeds,a),
        "signed_error_accounting":{"independent_roots":len(seeds),"root_rows":sci01,
            "assigned_nested_cells":sum(r["assigned_nested_cells"] for r in sci01),
            "evaluable_nested_cells":sum(r["evaluable_nested_cells"] for r in sci01),
            "reversal_nested_cells":sum(r["reversal_nested_cells"] for r in sci01),
            "nested_cell_inferential_sample_size":False},
        "derivation_controls":{"independent_roots":len(seeds),"root_rows":method_control,
            "scope":"NUMERICAL_METHOD_CONTROLS_ON_RETAINED_OPERANDS; NO_MOLECULAR_ADMISSION"},
        "timing":{"available_confirmation_native_seconds":sum(v for v in native_times if _finite(v)),
            "available_confirmation_analysis_seconds":sum(v for v in analysis_times if _finite(v)),
            "missing_native_timing_roots":len(seeds)-sum(_finite(v) for v in native_times),
            "missing_analysis_timing_roots":len(seeds)-sum(_finite(v) for v in analysis_times),
            "scope":"DISJOINT_CONF_ROOT_COMPONENTS_ONLY; TRAINING_CALIBRATION_FRAMEWORK_AND_FAILED_ATTEMPTS_REMAIN_SEPARATE",
            "complete_programme_cost":None},
        "actual_native_work_avoided":0 if rows else None,
        "inference_policy":"DESCRIPTIVE_MARGINAL_ROOT_SUMMARIES; NO_INHERITED_HISTORICAL_ALPHA_ALLOCATION_OR_MULTIPLICITY_CLAIM"}
