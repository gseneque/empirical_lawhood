# SPDX-License-Identifier: MPL-2.0
"""Independent explicit-numerics receiver and sensitivity reduction; no qualification."""

from bisect import bisect_right
from decimal import Decimal
import json
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition
from empirical_lawhood.adapters.methods.battery_thermal_inquiry import (
    science as inquiry,
)
from empirical_lawhood.adapters.methods.battery_thermal_inquiry.contracts import (
    CONTROL_RULE,
    INTEGRAL_TOLERANCE,
    TIER_EVENT,
    TIER_TEMPERATURE,
    REQUIRED_EVENT_NAMES,
    TARGET_CHARGE,
    BatteryInquirySupply,
)
from .contracts import (
    DiagnosticSource,
    DiagnosticNativeConfig,
    DiagnosticResult,
    DiagnosticTraceCheck,
    DiagnosticComparison,
    PREPARATIONS,
    NUMERICS,
)

D = Decimal
identity = inquiry.identity
_eligible = inquiry._eligible


def check_trace(trace, *, check_factory=DiagnosticTraceCheck):
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
        if (
            abs(trace.mean_temperature_k[0] - trace.config.initial_temperature_k)
            > D("0.01")
            or abs(trace.capacity_ah[0]) > INTEGRAL_TOLERANCE
        ):
            reasons.append("native-initial-preparation-unresolved")
            technical = True
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
    return check_factory(
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
    rtol, atol = trace.config.rtol, trace.config.atol
    for index, row in enumerate(rows):
        try:
            solver = json.loads(row.solver_configuration_json, parse_float=D)
            if (
                solver.get("type") != "IDAKLUSolver"
                or solver.get("rtol") != rtol
                or solver.get("atol") != atol
            ):
                return False
        except (ValueError, TypeError, AttributeError):
            return False
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


def compare_reference(primary, refined, *, check_factory=DiagnosticTraceCheck,
                      comparison_factory=DiagnosticComparison):
    """Independent common-clock comparison of the two authentic DFN views."""
    if any(
        getattr(primary.config, n) != getattr(refined.config, n)
        for n in ("source", "prior_supply", "phase", "initial_temperature_k", "recipe")
    ):
        raise ValueError("DFN reference comparison changes scientific preparations")
    a, b = (check_trace(primary, check_factory=check_factory),
            check_trace(refined, check_factory=check_factory))
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
    return comparison_factory(
        f"reference-check.{int(primary.config.initial_temperature_k - D('273.15'))}c.{primary.config.recipe}.{primary.config.component_view.lower()}.{refined.config.component_view.lower()}",
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


def validate_prior(source, prior):
    if type(source) is not DiagnosticSource or source != DiagnosticSource():
        raise ValueError("diagnostic replaces its selected source")
    if (
        type(prior) is not BatteryInquirySupply
        or prior.fingerprint() != source.prior_supply_sha256
    ):
        raise ValueError("diagnostic needs exact actual negative prior procedure")
    inquiry.validate_supply(prior)
    if (
        prior.source != source.original
        or prior.check.disposition is not AssessmentDisposition.UNEVALUABLE
        or prior.check.selected_model is not None
        or len(prior.check.reference_checks) != 9
        or any(
            x.disposition is not AssessmentDisposition.UNEVALUABLE
            for x in prior.check.reference_checks
        )
    ):
        raise ValueError("diagnostic disguises its unresolved reference context")


def configurations(source, prior_identity):
    return tuple(
        DiagnosticNativeConfig(
            f"config.battery-dfn-precision-diagnostic.{int(t - D('273.15'))}c.{recipe}.{view.lower()}",
            source,
            prior_identity,
            t,
            recipe,
            view,
            nx,
            nr,
            eps,
            rtol,
            atol,
        )
        for t, recipe in PREPARATIONS
        for view, nx, nr, eps, rtol, atol in NUMERICS
    )


def comparisons(traces):
    by = {
        (x.config.initial_temperature_k, x.config.recipe, x.config.component_view): x
        for x in traces
    }
    return tuple(
        compare_reference(by[t, recipe, a], by[t, recipe, b])
        for t, recipe in PREPARATIONS
        for a, b in (("A", "B"), ("B", "C"), ("B", "D"))
    )


def validate_result(result):
    if (
        result.product_id != "product.battery-dfn-precision-diagnostic"
        or result.qualification
    ):
        raise ValueError("diagnostic cannot confer qualification")
    result.source.__post_init__()
    expected = configurations(result.source, result.prior_supply)
    if tuple(x.config for x in result.traces) != expected:
        raise ValueError("diagnostic omits or reorders complete12 forecast roster")
    for trace in result.traces:
        trace.__post_init__()
    if result.checks != tuple(
        check_trace(x) for x in result.traces
    ) or result.comparisons != comparisons(result.traces):
        raise ValueError(
            "diagnostic changes independent receiver/sensitivity reduction"
        )
    disposition = (
        AssessmentDisposition.SATISFIED
        if all(
            x.disposition is not AssessmentDisposition.UNEVALUABLE
            for x in result.checks
        )
        and all(
            x.disposition is AssessmentDisposition.SATISFIED for x in result.comparisons
        )
        else AssessmentDisposition.UNEVALUABLE
    )
    if result.disposition is not disposition:
        raise ValueError("diagnostic invents resolved precision")


def run(source, prior):
    validate_prior(source, prior)
    return _run_validated_prior(source, identity(prior))


def _run_validated_prior(source, prior_identity):
    """Internal core after full actual-prior validation by run or its worker.

    Keeping only this exact immutable join allows the worker to release decoded
    historical traces before acquisition. It does not authenticate or validate
    a caller's historical product; the public entry point still requires it.
    """
    if type(source) is not DiagnosticSource or source != DiagnosticSource():
        raise ValueError("diagnostic replaces its selected source")
    expected = ObjectIdentity("product.battery-thermal-inquiry.supply", BatteryInquirySupply.SCHEMA,
                              BatteryInquirySupply.VERSION, source.prior_supply_sha256)
    if type(prior_identity) is not ObjectIdentity or prior_identity != expected:
        raise ValueError("diagnostic core changes its exact validated prior identity")
    from .native import acquire

    traces = tuple(
        acquire(config) for config in configurations(source, prior_identity)
    )
    checks = tuple(check_trace(x) for x in traces)
    pairs = comparisons(traces)
    disposition = (
        AssessmentDisposition.SATISFIED
        if all(x.disposition is not AssessmentDisposition.UNEVALUABLE for x in checks)
        and all(x.disposition is AssessmentDisposition.SATISFIED for x in pairs)
        else AssessmentDisposition.UNEVALUABLE
    )
    return DiagnosticResult(
        "product.battery-dfn-precision-diagnostic",
        source,
        prior_identity,
        traces,
        checks,
        pairs,
        disposition,
    )
