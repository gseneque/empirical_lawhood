# SPDX-License-Identifier: MPL-2.0
"""Independent full-roster reductions, with references kept outside choice access."""
from hashlib import sha256
from decimal import Decimal

from empirical_lawhood.adapters.methods.battery_dfn_precision_diagnostic import science as diagnostic_science
from empirical_lawhood.adapters.methods.battery_dfn_precision_diagnostic.contracts import DiagnosticResult
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from .contracts import (
    NumericalSelection, NumericalPolicy, RefinedSource, NativeConfig, Trace, TraceCheck, Comparison,
    Qualification, Supply, Instance, ChoiceCommitment, Assessment, AssessedInstance,
    REDUCED, RECIPES, LATER_TEMPERATURES, identity,
)

D = Decimal


def validate_source_policy(source, policy, *, diagnostic, protocol_bytes):
    if type(source) is not RefinedSource or type(policy) is not NumericalPolicy:
        raise ValueError("refined source/policy must have their new exact types")
    source.__post_init__()
    policy.__post_init__()
    if (source.policy != identity(policy) or source.diagnostic != policy.diagnostic
            or source.protocol_sha256 != policy.protocol_sha256
            or sha256(protocol_bytes).hexdigest() != source.protocol_sha256):
        raise ValueError("refined source/policy/protocol identity differs")
    declared = decode_canonical_bytes(protocol_bytes, NumericalSelection, maximum_bytes=None)
    if declared != policy.selection:
        raise ValueError("actual protocol substitutes policy numerical/roster declarations")
    if type(diagnostic) is DiagnosticResult:
        diagnostic_science.validate_result(diagnostic)
        original = diagnostic.source.original
    else:
        from empirical_lawhood.adapters.methods.battery_diagnostic_obstruction import contracts as obstruction, science as obstruction_science
        if type(diagnostic) is not obstruction.ObstructionAssessment:
            raise ValueError("source requires the actual authenticated diagnostic result or authentic obstruction-history assessment")
        obstruction_science.validate_assessment(diagnostic)
        original = diagnostic.source.diagnostic_source.original
    if identity(diagnostic) != source.diagnostic or original != source.original:
        raise ValueError("source substitutes actual scientific result or adverse operational history")
    # Neither historical route grants complete new numerical qualification.


def native_config(source, policy, phase, temperature, recipe, view):
    return NativeConfig(f"config.battery-refined-inquiry.{phase}.{temperature}.{recipe}.{view}",
                        source, policy, phase, temperature, recipe, view)


def configurations(source, policy, phase="qualification"):
    preparations = policy.development_preparations if phase == "qualification" else tuple(
        (temperature, recipe) for p, temperature, recipes in policy.later_preparations if p == phase for recipe in recipes)
    if not preparations:
        raise ValueError("no selected scientific phase roster")
    return tuple(sorted((native_config(source, policy, phase, temperature, recipe, view.view_id)
        for temperature, recipe in preparations for view in policy.views), key=lambda config: config.config_id))


def check_trace(trace):
    if type(trace) is not Trace:
        raise ValueError("refined reduction requires its own authenticated trace type")
    trace.__post_init__()
    return diagnostic_science.check_trace(trace, check_factory=TraceCheck)


def compare_reference(left, right):
    if left.config.policy != right.config.policy:
        raise ValueError("reference changes exact numerical policy")
    return diagnostic_science.compare_reference(left, right, check_factory=TraceCheck, comparison_factory=Comparison)


def _rows(source, policy, phase, traces):
    expected = configurations(source, policy, phase)
    rows = {t.config.config_id: t for t in traces}
    if len(rows) != len(traces) or rows.keys() != {c.config_id for c in expected}:
        raise ValueError("complete phase forecast census omitted, duplicated or substituted")
    ordered = tuple(rows[c.config_id] for c in expected)
    for trace, config in zip(ordered, expected, strict=True):
        if type(trace) is not Trace or trace.config != config:
            raise ValueError("trace changes exact selected config/source/phase")
        trace.__post_init__()
    return ordered, {(t.config.initial_temperature_k, t.config.recipe, t.config.component_view): t for t in ordered}


def _comparisons(policy, rows):
    preparations = sorted({(t, r) for t, r, _ in rows})
    return tuple(compare_reference(rows[t, r, left], rows[t, r, right])
                 for t, r in preparations for left, right in policy.comparison_pairs)


def best_recipes(checks):
    times = {recipe: c.completion_time_s for recipe, c in checks.items()
             if c.disposition is A.SATISFIED and c.completion_time_s is not None}
    if not times:
        return ()
    best = min(times.values())
    return tuple(sorted(r for r, time in times.items() if time <= best + D(2)))


def _model_admission(preparations, checks, model):
    reasons = set()
    for temperature, recipe in preparations:
        forecast, reference = checks[temperature, recipe, model], checks[temperature, recipe, "dfn-refined"]
        if A.UNEVALUABLE in (forecast.disposition, reference.disposition):
            reasons.add("forecast-or-reference-integrity-unresolved")
        if forecast.disposition is not reference.disposition:
            reasons.add("complete-roster-feasibility-disagrees")
        if forecast.disposition is A.SATISFIED and (
                forecast.completion_time_s is None or reference.completion_time_s is None
                or abs(forecast.completion_time_s - reference.completion_time_s) > reference.completion_time_s * D("0.01")):
            reasons.add("completion-forecast-exceeds-one-percent")
    for temperature in sorted({t for t, _ in preparations}):
        predicted = best_recipes({r: checks[temperature, r, model] for r in RECIPES})
        actual = best_recipes({r: checks[temperature, r, "dfn-refined"] for r in RECIPES})
        if not set(predicted).issubset(actual):
            reasons.add("fastest-choice-disagrees-outside-two-second-tie")
    return tuple(sorted(reasons))


def qualify(source, policy, traces):
    ordered, rows = _rows(source, policy, "qualification", traces)
    checks = tuple(check_trace(t) for t in ordered)
    checkrows = {(t.config.initial_temperature_k, t.config.recipe, t.config.component_view): c
                 for t, c in zip(ordered, checks, strict=True)}
    comparisons = _comparisons(policy, rows)
    reasons = tuple((m, _model_admission(policy.development_preparations, checkrows, m)) for m in REDUCED)
    admitted = tuple(m for m, why in reasons if not why)
    costs = tuple((m, sum((t.cpu_seconds for t in ordered if t.config.component_view == m), D(0)))
                  for m in (*REDUCED, "dfn-primary"))
    if any(c.disposition is not A.SATISFIED for c in comparisons):
        selected, disposition, why = None, A.UNEVALUABLE, ("complete-independent-reference-precision-unresolved",)
    else:
        selected = min(admitted, key=lambda m: (dict(costs)[m], m)) if admitted else "dfn-primary"
        disposition, why = A.SATISFIED, (() if admitted else ("reduced-models-refused-direct-dfn-fallback",))
    return Qualification("product.battery-refined-inquiry.qualification", identity(source), identity(policy), source.diagnostic,
        tuple(identity(t) for t in ordered), checks, comparisons, admitted, selected, reasons, costs, disposition, why)


def validate_qualification_projection(source, policy, qualification):
    configs = configurations(source, policy)
    expected_ids = tuple("trace." + c.config_id for c in configs)
    if tuple(t.object_id for t in qualification.traces) != expected_ids or any(t.object_schema != Trace.SCHEMA for t in qualification.traces):
        raise ValueError("qualification projection omits its complete development trace census")
    by_id = {t.object_id: t for t in qualification.traces}
    expected_pairs = tuple((by_id["trace." + native_config(source, policy, "qualification", t, r, left).config_id],
                            by_id["trace." + native_config(source, policy, "qualification", t, r, right).config_id])
        for t, r in policy.development_preparations for left, right in policy.comparison_pairs)
    if tuple((c.left, c.right) for c in qualification.comparisons) != expected_pairs:
        raise ValueError("qualification projection omits band/mesh/combined preparation comparisons")
    checks = {(c.initial_temperature_k, c.recipe, c.component_view): check for c, check in zip(configs, qualification.checks, strict=True)}
    model_reasons = tuple((m, _model_admission(policy.development_preparations, checks, m)) for m in REDUCED)
    admitted = tuple(m for m, reasons in model_reasons if not reasons)
    if model_reasons != qualification.model_reasons or admitted != qualification.admitted_models:
        raise ValueError("qualification invents reduced-model feasibility/error/choice admission")
    if tuple(m for m, _ in qualification.model_cpu_seconds) != (*REDUCED, "dfn-primary"):
        raise ValueError("qualification omits actual model CPU selection census")
    for _, expense in qualification.model_cpu_seconds:
        if expense < 0 or not isinstance(expense, D) or not expense.is_finite():
            raise ValueError("qualification selection expense invalid")
    selected = None if any(c.disposition is not A.SATISFIED for c in qualification.comparisons) else (
        min(admitted, key=lambda m: (dict(qualification.model_cpu_seconds)[m], m)) if admitted else "dfn-primary")
    if qualification.selected_model != selected:
        raise ValueError("qualification invents cheapest admitted or precision-gated fallback selection")


def validate_qualification(source, policy, qualification, traces):
    if qualification != qualify(source, policy, traces):
        raise ValueError("qualification differs from complete independent actual trace reduction")


def construct_supply(source, policy, qualification, traces):
    validate_qualification(source, policy, qualification, traces)
    return Supply("product.battery-refined-inquiry.supply", source, policy, qualification)


def compatible_instance(supplier, phase="use", *, prior_use=None):
    if type(supplier) is not Supply or supplier.disposition is not A.SATISFIED:
        raise ValueError("instance requires an actually admitted refined supplier")
    if phase == "reuse":
        if type(prior_use) is not AssessedInstance or prior_use.assessment.instance.phase != "use" or prior_use.supplier != supplier or not prior_use.assessment.traces:
            raise ValueError("reuse requires actual entered20C use of the original supplier")
    elif phase != "use" or prior_use is not None:
        raise ValueError("instance changes original four-phase lineage")
    return Instance("instance.battery-refined-inquiry." + phase, identity(supplier.source), identity(supplier.policy),
        identity(supplier), phase, LATER_TEMPERATURES[phase], identity(prior_use) if prior_use is not None else None)


def commit_choice(supplier, instance, forecasts):
    model = supplier.qualification.selected_model
    if model is None:
        raise ValueError("unadmitted supplier cannot choose a later action")
    expected = tuple(native_config(supplier.source, supplier.policy, instance.phase, instance.initial_temperature_k, r, model) for r in RECIPES)
    rows = {t.config: t for t in forecasts}
    if len(rows) != len(forecasts) or rows.keys() != set(expected):
        raise ValueError("choice requires exactly all three admitted-model forecasts before reference reveal")
    ordered = tuple(rows[c] for c in expected)
    checks = tuple(check_trace(t) for t in ordered)
    ties = best_recipes(dict(zip(RECIPES, checks, strict=True)))
    return ChoiceCommitment("choice.battery-refined-inquiry." + instance.phase, identity(supplier), identity(instance),
        tuple(identity(t) for t in ordered), checks, ties[0] if ties else None, ties)


def assess_instance(supplier, instance, traces, choice, persisted_choice, *, prior_use=None):
    if instance != compatible_instance(supplier, instance.phase, prior_use=prior_use):
        raise ValueError("assessment changes original supplier/actual prior-use lineage")
    ordered, rows = _rows(supplier.source, supplier.policy, instance.phase, traces)
    forecasts = tuple(rows[instance.initial_temperature_k, r, supplier.qualification.selected_model] for r in RECIPES)
    if choice != commit_choice(supplier, instance, forecasts) or persisted_choice != identity(choice):
        raise ValueError("assessment substitutes the actual before-reveal forecast choice")
    checks = tuple(check_trace(t) for t in ordered)
    checkrows = {(t.config.initial_temperature_k, t.config.recipe, t.config.component_view): c for t, c in zip(ordered, checks, strict=True)}
    comparisons = _comparisons(supplier.policy, rows)
    reference = {r: checkrows[instance.initial_temperature_k, r, "dfn-refined"] for r in RECIPES}
    best = best_recipes(reference)
    if any(c.disposition is not A.SATISFIED for c in comparisons):
        inst = admission = joined = overall = A.UNEVALUABLE
        reasons = ("independent-recipient-reference-precision-unresolved",)
    else:
        inst = A.SATISFIED
        why = _model_admission(tuple((instance.initial_temperature_k, r) for r in RECIPES), checkrows, supplier.qualification.selected_model)
        admission = A.UNEVALUABLE if "forecast-or-reference-integrity-unresolved" in why else A.FALSIFIED if why or choice.selected_recipe is not None and choice.selected_recipe not in best else A.SATISFIED
        joined = reference[choice.selected_recipe].disposition if choice.selected_recipe is not None else A.REFUSED
        overall = A.SATISFIED if admission is joined is A.SATISFIED else A.UNEVALUABLE if admission is A.UNEVALUABLE else A.FALSIFIED if admission is A.FALSIFIED or joined is A.FALSIFIED else A.REFUSED
        reasons = tuple(sorted(set(why) | ({"no-feasible-delivery-selected"} if choice.selected_recipe is None else set())))
    return Assessment("product.battery-refined-inquiry." + instance.phase, identity(supplier), instance, choice, persisted_choice,
        tuple(identity(t) for t in ordered), checks, comparisons, best, inst, admission, joined, overall, reasons,
        sum(t.native_provider_attempts for t in ordered), sum(t.backend_solve_calls for t in ordered),
        sum((t.cpu_seconds for t in ordered), D(0)), sum((t.wall_seconds for t in ordered), D(0)))


def validate_assessment(supplier, assessment, traces, *, prior_use=None):
    expected = assess_instance(supplier, assessment.instance, traces, assessment.choice, assessment.persisted_choice, prior_use=prior_use)
    if expected != assessment:
        raise ValueError("assessment differs from independent full-roster instance reduction")


def run_qualification(source, policy, *, acquire):
    traces = tuple(acquire(config) for config in configurations(source, policy))
    return qualify(source, policy, traces), traces


def run_instance(supplier, instance, *, acquire, persist_choice, prior_use=None):
    """Convenience service; graph owners may instead bind forecast/choice/reference tasks."""
    if instance != compatible_instance(supplier, instance.phase, prior_use=prior_use):
        raise ValueError("instance requires actual compatible lineage before any acquisition")
    cache = {}
    for recipe in RECIPES:
        config = native_config(supplier.source, supplier.policy, instance.phase, instance.initial_temperature_k, recipe, supplier.qualification.selected_model)
        cache[config.config_id] = acquire(config)
    choice = commit_choice(supplier, instance, tuple(cache.values()))
    witness = persist_choice(choice)
    if witness != identity(choice):
        raise ValueError("choice was not retained before reference acquisition")
    for config in configurations(supplier.source, supplier.policy, instance.phase):
        if config.config_id not in cache:
            cache[config.config_id] = acquire(config)
    traces = tuple(cache[c.config_id] for c in configurations(supplier.source, supplier.policy, instance.phase))
    assessment = assess_instance(supplier, instance, traces, choice, witness, prior_use=prior_use)
    return AssessedInstance("product.battery-refined-inquiry.assessed-" + instance.phase, supplier, assessment,
                            prior_use.assessment if prior_use is not None else None), traces
