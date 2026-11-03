# SPDX-License-Identifier: MPL-2.0
"""Independent receiver reduction and the selected reusable model procedure."""

from bisect import bisect_right
from decimal import Decimal

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition

from .contracts import (
    BatteryInquiryAssessment,
    BatteryInquiryCostAllocation,
    BatteryInquiryInstance,
    BatteryInquiryNativeConfig,
    BatteryInquiryProcedure,
    BatteryInquiryReferenceCheck,
    BatteryInquirySource,
    BatteryInquirySupply,
    BatteryInquiryTraceCheck,
    CONTROL_RULE,
    DEVELOPMENT_TEMPERATURES,
    INTEGRAL_TOLERANCE,
    LATER_TEMPERATURES,
    MODEL_VIEWS,
    QUESTION as QUESTION,
    RECIPES,
    TIER_EVENT,
    TIER_TEMPERATURE,
    REQUIRED_EVENT_NAMES,
    TARGET_CHARGE,
    UNIT as UNIT,
    scope,
)

D = Decimal


def identity(record):
    key = next(
        getattr(record, name)
        for name in (
            "source_id",
            "product_id",
            "instance_id",
            "assessment_id",
            "trace_id",
            "check_id",
            "procedure_id",
            "config_id",
        )
        if hasattr(record, name)
    )
    return ObjectIdentity.from_record(key, record)


def validate_source(source):
    if type(source) is not BatteryInquirySource or source != BatteryInquirySource():
        raise ValueError(
            "thermal inquiry substitutes its frozen initial scientific stock"
        )


def source_scope(source_identity):
    source = BatteryInquirySource()
    if source_identity != identity(source):
        raise ValueError("thermal inquiry changes its exact selected source identity")
    return scope(source)


def _eligible(temperature):
    # Independent Decimal evaluator, not an evaluation of the native equation.
    return D("3.395") if temperature > D("298.15") else D("1.455")


def check_trace(trace):
    """Charge uses actual native current; CV is never a requested-current proxy."""
    reasons = []
    realized = capacity = discrepancy = completion = None
    envelope = controlled = False
    technical = trace.disposition == "TECHNICAL_FAILURE"
    if technical:
        reasons.append("native-technical-failure")
    if not trace.times_s:
        reasons.append("native-receivers-absent")
        technical = True
    else:
        realized = -sum(
            (
                (a + b) * (t1 - t0) / D(7200)
                for t0, t1, a, b in zip(
                    trace.times_s,
                    trace.times_s[1:],
                    trace.current_a,
                    trace.current_a[1:],
                )
            ),
            D(0),
        )
        capacity = -(trace.capacity_ah[-1] - trace.capacity_ah[0])
        discrepancy = abs(realized - capacity)
        if discrepancy > INTEGRAL_TOLERANCE:
            reasons.append("independent-current-capacity-disagreement")
            technical = True
        envelope = (
            all(D("2.5") - D("0.001") <= v <= D("4.201") for v in trace.voltage_v)
            and all(
                D("273.15") - D("0.01") <= t <= D("318.15") + D("0.01")
                for t in trace.mean_temperature_k
            )
            and all(
                -_eligible(t) - D("1e-6") <= i <= D("1e-6")
                for i, t in zip(trace.current_a, trace.mean_temperature_k, strict=True)
            )
        )
        if not envelope:
            reasons.append("sampled-source-envelope-violation")
        delivery = trace.delivery
        delivery_present = (
            delivery.requested_rule == CONTROL_RULE
            and delivery.accepted_voltage_v == D("4.2")
            and delivery.accepted_chamber_k == trace.config.chamber_temperature_k
            and delivery.applied_model_clock_s == trace.times_s[0]
            and delivery.applied_current_a == trace.current_a[0]
            and delivery.applied_voltage_v == trace.voltage_v[0]
            and delivery.applied_chamber_k == trace.ambient_temperature_k[0]
            and all(
                t == trace.config.chamber_temperature_k
                for t in trace.ambient_temperature_k
            )
            and all(
                (
                    delivery.accepted_control_expression,
                    delivery.applied_control_expression,
                    delivery.applied_current_expression,
                    delivery.applied_voltage_expression,
                    delivery.applied_chamber_expression,
                )
            )
            and len(trace.event_names) == len(trace.processed_event_expressions)
            and set(REQUIRED_EVENT_NAMES).issubset(trace.event_names)
            and all(trace.processed_event_expressions)
            and bool(trace.initializer_attempts)
            and trace.initializer_attempts[-1].disposition == "RETURNED"
        )
        epsilon = trace.config.localization_epsilon_k
        root_roundoff = epsilon / D("1000000")
        controlled = (
            delivery_present
            and bool(trace.charging_attempts)
            and all(
                abs(
                    min(
                        D("4.2") - v,
                        i + (D("1.455") if regime == "LOW" else D("3.395")),
                    )
                )
                <= D("0.001")
                and (
                    t > TIER_TEMPERATURE
                    if regime == "HIGH"
                    else t <= TIER_TEMPERATURE + epsilon + root_roundoff
                )
                for i, v, t, regime in zip(
                    trace.current_a,
                    trace.voltage_v,
                    trace.mean_temperature_k,
                    trace.temperature_regimes,
                    strict=True,
                )
            )
        )
        if not hybrid_custody_checked(trace):
            reasons.append("native-hybrid-state-root-or-subsolve-custody-unresolved")
            technical = True
        if not delivery_present:
            reasons.append("native-control-or-chamber-delivery-unresolved")
            technical = True
        elif not controlled:
            reasons.append("native-control-law-violated")
        if (
            trace.disposition != "TARGET_REACHED"
            or capacity < TARGET_CHARGE - INTEGRAL_TOLERANCE
            or realized < TARGET_CHARGE - INTEGRAL_TOLERANCE
        ):
            reasons.append("operational-soc80-target-not-delivered")
        else:
            completion = trace.times_s[-1]
    disposition = (
        AssessmentDisposition.UNEVALUABLE
        if technical
        else AssessmentDisposition.FALSIFIED
        if reasons
        else AssessmentDisposition.SATISFIED
    )
    return BatteryInquiryTraceCheck(
        f"check.{trace.trace_id}",
        identity(trace),
        disposition,
        realized,
        capacity,
        discrepancy,
        completion,
        tuple(sorted(set(reasons))),
        envelope,
        controlled,
    )


def hybrid_custody_checked(trace):
    """Independent full-state/time/current checks of the event continuation."""
    rows = trace.charging_attempts
    retained_clocks = frozenset(trace.times_s)
    if (
        not rows
        or trace.backend_solve_calls != len(rows)
        or TIER_EVENT not in trace.event_names
    ):
        return False
    if len(trace.transitions) != sum(
        TIER_EVENT in row.termination for row in rows[:-1]
    ):
        return False
    refined = trace.config.model_view == "oregan-dfn-refined"
    rtol, atol = (D("1e-9"), D("1e-10")) if refined else (D("1e-7"), D("1e-8"))
    for index, row in enumerate(rows):
        if (
            row.disposition != "RETURNED"
            or not row.native_times_s
            or row.native_times_s[-1] <= row.requested_start_clock_s
        ):
            return False
        if index:
            before = rows[index - 1]
            if (
                row.requested_start_clock_s != before.native_times_s[-1]
                or row.requested_differential_state != before.end_differential_state
                or len(row.start_differential_state)
                != len(before.end_differential_state)
                or row.native_times_s[0] <= before.native_times_s[-1]
            ):
                return False
            if any(
                abs(a - b) > atol + rtol * max(abs(a), abs(b))
                for a, b in zip(
                    row.start_differential_state,
                    before.end_differential_state,
                    strict=True,
                )
            ):
                return False
            if (
                abs(row.start_receivers[3] - before.end_receivers[3])
                > INTEGRAL_TOLERANCE
            ):
                return False
        if row.start_receivers and row.end_receivers:
            for clock, receiver in (
                (row.native_times_s[0], row.start_receivers),
                (row.native_times_s[-1], row.end_receivers),
            ):
                pos = bisect_right(trace.times_s, clock) - 1
                if (
                    pos < 0
                    or trace.times_s[pos] != clock
                    or trace.temperature_regimes[pos] != row.regime
                ):
                    return False
                actual = (
                    trace.current_a[pos],
                    trace.voltage_v[pos],
                    trace.mean_temperature_k[pos],
                    trace.capacity_ah[pos],
                )
                if actual != receiver:
                    return False
            if any(clock not in retained_clocks for clock in row.native_times_s):
                return False
    for row in trace.transitions:
        expected = TIER_TEMPERATURE + trace.config.localization_epsilon_k / (
            D(1) if row.from_regime == "LOW" else D(2)
        )
        if (
            row.threshold_k != expected
            or abs(row.left_receivers[2] - expected)
            > trace.config.localization_epsilon_k / D("1000000")
            or row.right_clock_s is None
        ):
            return False
        if row.to_regime == "HIGH" and row.right_receivers[2] <= TIER_TEMPERATURE:
            return False
        if row.from_regime == "HIGH" and row.left_receivers[2] <= TIER_TEMPERATURE:
            return False
    return True


def _interpolate(times, values, clock):
    if clock < times[0] or clock > times[-1]:
        raise ValueError("independent comparison exceeds retained receiver clock")
    pos = bisect_right(times, clock) - 1
    if pos == len(times) - 1 or times[pos] == clock:
        return values[pos]
    weight = (clock - times[pos]) / (times[pos + 1] - times[pos])
    return values[pos] + weight * (values[pos + 1] - values[pos])


def compare_reference(primary, refined):
    """Independent common-clock comparison of the two authentic DFN views."""
    if (
        primary.config.model_view != "oregan-dfn"
        or refined.config.model_view != "oregan-dfn-refined"
        or any(
            getattr(primary.config, n) != getattr(refined.config, n)
            for n in ("source", "phase", "initial_temperature_k", "recipe")
        )
    ):
        raise ValueError("DFN reference comparison changes scientific preparations")
    a, b = check_trace(primary), check_trace(refined)
    reasons = []
    td = vd = kd = None
    if AssessmentDisposition.UNEVALUABLE in (a.disposition, b.disposition):
        reasons.append("reference-native-integrity-unresolved")
    else:
        if a.disposition is not b.disposition:
            reasons.append("reference-feasibility-disagrees")
        if (
            primary.disposition == refined.disposition == "SERVICE_TERMINATED"
            and primary.termination != refined.termination
        ):
            reasons.append("reference-termination-event-disagrees")
        td = abs(primary.times_s[-1] - refined.times_s[-1])
        end = min(primary.times_s[-1], refined.times_s[-1])
        clocks = tuple(D(v) for v in range(int(end) + 1)) + (end,)
        vd = max(
            abs(
                _interpolate(primary.times_s, primary.voltage_v, t)
                - _interpolate(refined.times_s, refined.voltage_v, t)
            )
            for t in clocks
        )
        kd = max(
            abs(
                _interpolate(primary.times_s, primary.mean_temperature_k, t)
                - _interpolate(refined.times_s, refined.mean_temperature_k, t)
            )
            for t in clocks
        )
        if td > D(1):
            reasons.append("reference-terminal-clock-precision-unresolved")
        if vd > D("0.001"):
            reasons.append("reference-voltage-precision-unresolved")
        if kd > D("0.01"):
            reasons.append("reference-temperature-precision-unresolved")
    return BatteryInquiryReferenceCheck(
        f"reference-check.{primary.config.phase}.{int(primary.config.initial_temperature_k - D('273.15'))}c.{primary.config.recipe}",
        identity(primary),
        identity(refined),
        AssessmentDisposition.UNEVALUABLE
        if reasons
        else AssessmentDisposition.SATISFIED,
        td,
        vd,
        kd,
        tuple(sorted(reasons)),
    )


def best_recipes(rows):
    times = {
        trace.config.recipe: check_trace(trace).completion_time_s
        for trace in rows
        if check_trace(trace).disposition is AssessmentDisposition.SATISFIED
    }
    if not times:
        return ()
    best = min(times.values())
    return tuple(
        sorted(recipe for recipe, clock in times.items() if clock <= best + D(2))
    )


def assess_procedure(traces):
    rows = {
        (v.config.initial_temperature_k, v.config.recipe, v.config.model_view): v
        for v in traces
    }
    expected = {
        (t, r, m)
        for t in DEVELOPMENT_TEMPERATURES
        for r in RECIPES
        for m in MODEL_VIEWS
    }
    if len(traces) != len(expected) or set(rows) != expected:
        raise ValueError(
            "procedure assessment omits its complete development denominator"
        )
    references = tuple(
        compare_reference(rows[t, r, "oregan-dfn"], rows[t, r, "oregan-dfn-refined"])
        for t in DEVELOPMENT_TEMPERATURES
        for r in RECIPES
    )
    model_reasons = []
    for model in ("chen-spme", "oregan-spme"):
        reasons = set()
        for t in DEVELOPMENT_TEMPERATURES:
            for r in RECIPES:
                forecast, reference = (
                    check_trace(rows[t, r, model]),
                    check_trace(rows[t, r, "oregan-dfn-refined"]),
                )
                if forecast.disposition is AssessmentDisposition.UNEVALUABLE:
                    reasons.add("forecast-integrity-unresolved")
                if forecast.disposition is not reference.disposition:
                    reasons.add("finite-roster-feasibility-disagrees")
                if (
                    forecast.completion_time_s is not None
                    and reference.completion_time_s is not None
                    and abs(forecast.completion_time_s - reference.completion_time_s)
                    > reference.completion_time_s * D("0.01")
                ):
                    reasons.add("completion-forecast-exceeds-one-percent")
            predicted = best_recipes(tuple(rows[t, r, model] for r in RECIPES))
            actual = best_recipes(
                tuple(rows[t, r, "oregan-dfn-refined"] for r in RECIPES)
            )
            if predicted and (not actual or not set(predicted).issubset(actual)):
                reasons.add("unique-fastest-recipe-disagrees-outside-tie")
        model_reasons.append((model, tuple(sorted(reasons))))
    admitted = tuple(model for model, reasons in model_reasons if not reasons)
    costs = tuple(
        (
            model,
            sum((v.cpu_seconds for v in traces if v.config.model_view == model), D(0)),
        )
        for model in ("chen-spme", "oregan-dfn", "oregan-spme")
    )
    if any(v.disposition is not AssessmentDisposition.SATISFIED for v in references):
        selected, disposition, reasons = (
            None,
            AssessmentDisposition.UNEVALUABLE,
            ("independent-reference-precision-unresolved",),
        )
    else:
        selected = (
            min(admitted, key=lambda model: (dict(costs)[model], model))
            if admitted
            else "oregan-dfn"
        )
        disposition, reasons = (
            AssessmentDisposition.SATISFIED,
            () if admitted else ("reduced-models-refused-direct-dfn-fallback",),
        )
    return BatteryInquiryProcedure(
        "procedure.battery-thermal-inquiry.model-qualification",
        selected,
        admitted,
        references,
        tuple(model_reasons),
        costs,
        disposition,
        reasons,
    )


def native_config(source, phase, temperature, recipe, model):
    return BatteryInquiryNativeConfig(
        f"native.battery-thermal-inquiry.{phase}.{int(temperature - D('273.15'))}c.{recipe}.{model}",
        source,
        phase,
        temperature,
        recipe,
        model,
    )


def supply(source):
    validate_source(source)
    from .native import acquire

    traces = tuple(
        acquire(native_config(source, "supply", t, r, m))
        for t in DEVELOPMENT_TEMPERATURES
        for r in RECIPES
        for m in MODEL_VIEWS
    )
    checks = tuple(check_trace(trace) for trace in traces)
    procedure = assess_procedure(traces)
    return BatteryInquirySupply(
        "product.battery-thermal-inquiry.supply",
        source,
        traces,
        checks,
        procedure,
        scope(source),
        procedure.disposition,
    )


def compatible_instance(supplier, phase="use", *, prior_use=None):
    validate_source(supplier.source)
    if phase not in LATER_TEMPERATURES:
        raise ValueError(
            "thermal inquiry selects exactly one later and one subsequent reuse"
        )
    if phase == "reuse":
        if not isinstance(prior_use, BatteryInquiryAssessment):
            raise ValueError(
                "subsequent reuse requires its actual prior-use assessment"
            )
        if prior_use.instance.phase != "use" or not prior_use.traces:
            raise ValueError(
                "subsequent reuse requires a completed attempted later use"
            )
        validate_assessment(supplier, prior_use)
    elif prior_use is not None:
        raise ValueError("first later use cannot claim a previous use")
    return BatteryInquiryInstance(
        f"instance.battery-thermal-inquiry.{phase}",
        supplier.source,
        identity(supplier),
        phase,
        LATER_TEMPERATURES[phase],
        identity(prior_use) if prior_use is not None else None,
    )


def validate_supply(supplier):
    validate_source(supplier.source)
    if supplier.check != assess_procedure(
        supplier.traces
    ) or supplier.trace_checks != tuple(check_trace(t) for t in supplier.traces):
        raise ValueError(
            "supplier procedure or independent checks differ from exact retained native evidence"
        )


def _recipient_assessment(supplier, instance, traces, selected_recipe, cache_hits):
    rows = {(v.config.recipe, v.config.model_view): v for v in traces}
    references = (
        tuple(
            compare_reference(rows[r, "oregan-dfn"], rows[r, "oregan-dfn-refined"])
            for r in RECIPES
        )
        if rows
        else ()
    )
    best = (
        best_recipes(tuple(rows[r, "oregan-dfn-refined"] for r in RECIPES))
        if rows
        else ()
    )
    direct = best_recipes(tuple(rows[r, "oregan-dfn"] for r in RECIPES)) if rows else ()
    chen = best_recipes(tuple(rows[r, "chen-spme"] for r in RECIPES)) if rows else ()
    reasons = []
    if not rows:
        inst = admission = joined = overall = AssessmentDisposition.REFUSED
        reasons.append("supplier-procedure-not-admitted")
    elif any(v.disposition is not AssessmentDisposition.SATISFIED for v in references):
        inst = admission = joined = overall = AssessmentDisposition.UNEVALUABLE
        reasons.append("independent-recipient-reference-unresolved")
    else:
        inst = AssessmentDisposition.SATISFIED
        forecasts = {
            r: check_trace(rows[r, supplier.check.selected_model]) for r in RECIPES
        }
        actuals = {r: check_trace(rows[r, "oregan-dfn-refined"]) for r in RECIPES}
        complete_roster_agrees = all(
            forecasts[r].disposition is actuals[r].disposition
            and (
                forecasts[r].completion_time_s is None
                or actuals[r].completion_time_s is not None
                and abs(forecasts[r].completion_time_s - actuals[r].completion_time_s)
                <= actuals[r].completion_time_s * D("0.01")
            )
            for r in RECIPES
        )
        forecast_unresolved = any(
            v.disposition is AssessmentDisposition.UNEVALUABLE
            for v in forecasts.values()
        )
        if forecast_unresolved:
            admission = overall = AssessmentDisposition.UNEVALUABLE
            joined = (
                check_trace(rows[selected_recipe, "oregan-dfn-refined"]).disposition
                if selected_recipe is not None
                else AssessmentDisposition.UNEVALUABLE
            )
            reasons.append("supplied-model-native-forecast-unresolved")
        elif selected_recipe is None:
            joined = AssessmentDisposition.REFUSED
            admission = (
                AssessmentDisposition.SATISFIED
                if complete_roster_agrees
                else AssessmentDisposition.FALSIFIED
            )
            overall = (
                AssessmentDisposition.REFUSED
                if complete_roster_agrees
                else AssessmentDisposition.FALSIFIED
            )
            reasons.append("supplied-procedure-selects-no-delivery")
            if not complete_roster_agrees:
                reasons.append("supplied-model-admission-choice-or-time-falsified")
        else:
            forecast = forecasts[selected_recipe]
            actual = check_trace(rows[selected_recipe, "oregan-dfn-refined"])
            agrees = (
                complete_roster_agrees
                and forecast.disposition is actual.disposition
                and forecast.completion_time_s is not None
                and actual.completion_time_s is not None
                and abs(forecast.completion_time_s - actual.completion_time_s)
                <= actual.completion_time_s * D("0.01")
                and selected_recipe in best
            )
            admission = (
                AssessmentDisposition.SATISFIED
                if agrees
                else AssessmentDisposition.FALSIFIED
            )
            joined = actual.disposition
            overall = (
                AssessmentDisposition.SATISFIED
                if admission is joined is AssessmentDisposition.SATISFIED
                else AssessmentDisposition.FALSIFIED
            )
            if not agrees:
                reasons.append("supplied-model-admission-choice-or-time-falsified")
            if joined is not AssessmentDisposition.SATISFIED:
                reasons.append("joined-native-delivery-not-satisfied")
    return BatteryInquiryAssessment(
        f"assessment.battery-thermal-inquiry.{instance.phase}",
        identity(supplier),
        supplier.scope,
        instance,
        traces,
        tuple(check_trace(v) for v in traces),
        references,
        selected_recipe,
        best,
        direct[0] if direct else None,
        chen[0] if chen else None,
        inst,
        admission,
        joined,
        overall,
        tuple(sorted(reasons)),
        sum(v.native_provider_attempts for v in traces),
        sum(v.backend_solve_calls for v in traces),
        tuple(sorted(cache_hits)),
    )


def assess(supplier, instance, *, prior_use=None):
    validate_supply(supplier)
    if instance != compatible_instance(supplier, instance.phase, prior_use=prior_use):
        raise ValueError(
            "recipient substitutes its exact supplier instance or preparation"
        )
    if supplier.check.disposition is not AssessmentDisposition.SATISFIED:
        return _recipient_assessment(supplier, instance, (), None, ())
    from .native import acquire

    cache = {}
    hits = []

    def get(recipe, model, role):
        key = (recipe, model)
        if key in cache:
            hits.append((role, cache[key].trace_id))
        else:
            cache[key] = acquire(
                native_config(
                    supplier.source,
                    instance.phase,
                    instance.initial_temperature_k,
                    recipe,
                    model,
                )
            )
        return cache[key]

    forecasts = tuple(
        get(r, supplier.check.selected_model, "supplied-forecast." + r) for r in RECIPES
    )
    predicted = best_recipes(forecasts)
    # The recipient's action is frozen from its actual supplied-model forecasts
    # before any reference view reveals the outcome or alternative choice.
    selected_recipe = predicted[0] if predicted else None
    for model in MODEL_VIEWS:
        for recipe in RECIPES:
            get(recipe, model, f"full-roster.{model}.{recipe}")
    traces = tuple(cache[r, m] for r in RECIPES for m in MODEL_VIEWS)
    return _recipient_assessment(supplier, instance, traces, selected_recipe, hits)


def validate_assessment(supplier, assessment, *, prior_use=None):
    validate_supply(supplier)
    if assessment.instance != compatible_instance(
        supplier, assessment.instance.phase, prior_use=prior_use
    ):
        raise ValueError("assessment changes its actual source-bound recipient")
    expected = {(r, m) for r in RECIPES for m in MODEL_VIEWS}
    if assessment.traces and (
        len(assessment.traces) != len(expected)
        or {(v.config.recipe, v.config.model_view) for v in assessment.traces}
        != expected
    ):
        raise ValueError("recipient assessment omits its finite native roster")
    if any(
        v.config.source != supplier.source
        or v.config.phase != assessment.instance.phase
        or v.config.initial_temperature_k != assessment.instance.initial_temperature_k
        for v in assessment.traces
    ):
        raise ValueError("recipient assessment changes original native scopes")
    selected = best_recipes(
        tuple(
            v
            for v in assessment.traces
            if v.config.model_view == supplier.check.selected_model
        )
    )
    expected_record = _recipient_assessment(
        supplier,
        assessment.instance,
        assessment.traces,
        selected[0] if selected else None,
        assessment.cache_hits,
    )
    if assessment != expected_record:
        raise ValueError(
            "recipient assessment substitutes independently derived scientific outcomes"
        )


def cost_allocations(supplier, assessments):
    """Allocate shared actual forecasts; no replay or fictitious second trial."""
    validate_supply(supplier)
    if len({a.instance.phase for a in assessments}) != len(assessments):
        raise ValueError("cost comparison duplicates a recipient phase")
    previous = next((a for a in assessments if a.instance.phase == "use"), None)
    for assessment in assessments:
        validate_assessment(
            supplier,
            assessment,
            prior_use=previous if assessment.instance.phase == "reuse" else None,
        )
    actual = (
        *supplier.traces,
        *(trace for assessment in assessments for trace in assessment.traces),
    )
    if len({t.trace_id for t in actual}) != len(actual):
        raise ValueError("cost comparison relabels or duplicates a native trace")
    allocations = []
    for arm in (
        "el-full-procedure",
        "matched-conventional-full-procedure",
        "direct-dfn",
    ):
        charged = tuple(
            t
            for t in actual
            if arm != "direct-dfn"
            or t.config.model_view in {"oregan-dfn", "oregan-dfn-refined"}
        )
        allocations.append(
            BatteryInquiryCostAllocation(
                f"cost-allocation.battery-thermal-inquiry.{arm}",
                arm,
                tuple(identity(t) for t in charged),
                sum(t.native_provider_attempts for t in charged),
                sum(t.backend_solve_calls for t in charged),
                sum((t.cpu_seconds for t in charged), D(0)),
                sum((t.wall_seconds for t in charged), D(0)),
                initializer_solver_attempts=sum(
                    len(t.initializer_attempts) for t in charged
                ),
            )
        )
    return tuple(allocations)
