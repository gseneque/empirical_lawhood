# SPDX-License-Identifier: MPL-2.0
"""Compact full-census qualification of the changed battery method.

Reference precision and segment convergence are different assessments. Neither
favourable mathematical roots nor exposed runtime fixtures admit later use.
Every record below holds identities/compact assessments, never native arrays.
"""

from bisect import bisect_right
from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.kernel.serialization import CanonicalRecord, require_sorted_unique_strings, validate_decimal, validate_stable_id
from . import contracts as c
from . import durable_roster as dr
from . import science as historical_science
from . import segmented_contracts as sc
from . import segmented_roster as sr
from . import segmented_science as ss

D = Decimal


def identity(record, name):
    return ObjectIdentity.from_record(getattr(record, name), record)


@dataclass(frozen=True, slots=True)
class SegmentedConditionReuse(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/equal-condition-reuse"
    reuse_id: str
    requested_configuration: sc.SegmentedNativeConfig
    observed_configuration: sc.SegmentedNativeConfig
    original_summary: ObjectIdentity
    original_trace: ObjectIdentity
    derivation: str = "DERIVED_FROM_IDENTICAL_PHYSICS_PREPARATION_AND_SEGMENT_METHOD;ORIGINAL_TRACE_UNCHANGED"
    native_contacts: int = 0
    fresh_physical_units: int = 0

    def __post_init__(self):
        validate_stable_id(self.reuse_id)
        if (type(self.requested_configuration) is not sc.SegmentedNativeConfig or type(self.observed_configuration) is not sc.SegmentedNativeConfig
                or dr.forecast_primitive(self.requested_configuration.native) != dr.forecast_primitive(self.observed_configuration.native)
                or self.requested_configuration.preparation != self.observed_configuration.preparation
                or self.requested_configuration.preparation_assessment != self.observed_configuration.preparation_assessment
                or self.requested_configuration.method != self.observed_configuration.method
                or self.original_summary.object_schema != SegmentedTraceSummary.SCHEMA or self.original_trace.object_schema != sc.SegmentedTrace.SCHEMA
                or self.derivation != "DERIVED_FROM_IDENTICAL_PHYSICS_PREPARATION_AND_SEGMENT_METHOD;ORIGINAL_TRACE_UNCHANGED"
                or self.native_contacts != 0 or self.fresh_physical_units != 0):
            raise ValueError("segmented equal-condition use substitutes physical operands or fresh native evidence")


@dataclass(frozen=True, slots=True)
class SegmentedTraceSummary(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/trace-summary"
    summary_id: str
    configuration: sc.SegmentedNativeConfig
    trace: ObjectIdentity
    preparation: ss.DerivedPreparationAssessment | ss.UnavailableDerivedPreparationAssessment
    receiver_check: sc.SegmentedTraceCheck
    segment_assessments: tuple[ss.SegmentAssessment, ...]
    cpu_seconds: Decimal
    wall_seconds: Decimal
    native_contacts: int
    charging_segment_calls: int
    process_peak_rss_bytes: int
    disposition: A
    reason_codes: tuple[str, ...]
    condition_reuse: SegmentedConditionReuse | None = None

    def __post_init__(self):
        validate_stable_id(self.summary_id)
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes")
        if (type(self.configuration) is not sc.SegmentedNativeConfig or self.trace.object_schema != sc.SegmentedTrace.SCHEMA
                or type(self.preparation) not in (ss.DerivedPreparationAssessment, ss.UnavailableDerivedPreparationAssessment) or type(self.receiver_check) is not sc.SegmentedTraceCheck
                or self.receiver_check.trace != self.trace or type(self.disposition) is not A
                or any(type(row) is not ss.SegmentAssessment for row in self.segment_assessments)):
            raise ValueError("segmented summary substitutes its exact independent preparation/trace/segment checks")
        for name in ("cpu_seconds", "wall_seconds"):
            validate_decimal(getattr(self, name), field_name=name)
            if getattr(self, name) < 0:
                raise ValueError("segmented compact cost cannot be negative")
        if any(type(value) is not int or value < 0 for value in (self.native_contacts, self.charging_segment_calls, self.process_peak_rss_bytes)):
            raise ValueError("segmented summary changes actual native/resource accounting")
        if self.condition_reuse is None:
            if (self.native_contacts != 1 or self.charging_segment_calls != len(self.segment_assessments)
                    or self.preparation.configuration != identity(self.configuration, "config_id")):
                raise ValueError("segmented original summary loses actual preparation/contact/segment census")
        elif (type(self.condition_reuse) is not SegmentedConditionReuse or self.condition_reuse.requested_configuration != self.configuration
                or self.condition_reuse.original_trace != self.trace or self.cpu_seconds != 0 or self.wall_seconds != 0
                or self.native_contacts != 0 or self.charging_segment_calls != 0 or self.process_peak_rss_bytes != 0):
            raise ValueError("segmented condition reuse relabels trace bytes or counts native cost twice")
        if self.disposition is not A.SATISFIED and not self.reason_codes:
            raise ValueError("negative/missing compact summary requires reasons")
        if self.disposition is A.SATISFIED and (self.preparation.disposition is not A.SATISFIED
                or any(row.disposition is not A.SATISFIED for row in self.segment_assessments) or self.receiver_check.disposition is not A.SATISFIED):
            raise ValueError("segmented summary bypasses independent preparation or native assessment")

    @property
    def completion_time_s(self):
        return self.receiver_check.completion_time_s


def summarize_trace(trace, preparation, segment_assessments):
    receiver = ss.check_receivers(trace, preparation, segment_assessments)
    reasons = set(receiver.reason_codes)
    integrity = preparation.disposition is A.SATISFIED and all(row.disposition is A.SATISFIED for row in segment_assessments)
    if not integrity:
        reasons.add("independent-native-preparation-or-segment-integrity-unadmitted")
    return SegmentedTraceSummary("summary." + trace.trace_id, trace.config, identity(trace, "trace_id"), preparation, receiver,
        tuple(segment_assessments), trace.cpu_seconds, trace.wall_seconds, trace.native_provider_attempts, trace.backend_solve_calls,
        trace.process_peak_rss_bytes, receiver.disposition if integrity else A.UNEVALUABLE, tuple(sorted(reasons)))


def reuse_summary(requested_config, original):
    if type(original) is not SegmentedTraceSummary or original.condition_reuse is not None:
        raise ValueError("segmented condition use requires original authenticated summary")
    reuse = SegmentedConditionReuse("reuse." + requested_config.config_id, requested_config, original.configuration,
        identity(original, "summary_id"), original.trace)
    return SegmentedTraceSummary("summary." + requested_config.config_id, requested_config, original.trace,
        original.preparation, original.receiver_check, original.segment_assessments, D(0), D(0), 0, 0, 0,
        original.disposition, original.reason_codes, reuse)


@dataclass(frozen=True, slots=True)
class SegmentedComparison(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/comparison"
    comparison_id: str
    left_configuration: ObjectIdentity
    right_configuration: ObjectIdentity
    left_trace: ObjectIdentity
    right_trace: ObjectIdentity
    comparison_kind: str
    disposition: A
    terminal_time_difference_s: Decimal | None
    maximum_voltage_difference_v: Decimal | None
    maximum_temperature_difference_k: Decimal | None
    reason_codes: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.comparison_id)
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes")
        if (any(row.object_schema != sc.SegmentedNativeConfig.SCHEMA for row in (self.left_configuration, self.right_configuration))
                or any(row.object_schema != sc.SegmentedTrace.SCHEMA for row in (self.left_trace, self.right_trace))
                or self.comparison_kind not in {"REFERENCE_PRECISION", "SEGMENT_FIDELITY"} or type(self.disposition) is not A):
            raise ValueError("segmented comparison substitutes selected preparation or assessment scope")
        for value in (self.terminal_time_difference_s, self.maximum_voltage_difference_v, self.maximum_temperature_difference_k):
            if value is not None:
                validate_decimal(value, field_name="comparison")
                if value < 0:
                    raise ValueError("segmented comparison has negative discrepancy")
        if (self.disposition is A.SATISFIED) != (not self.reason_codes):
            raise ValueError("segmented comparison bypasses unchanged precision gates")


def _interpolate(times, values, clock):
    if not times or clock < times[0] or clock > times[-1]:
        raise ValueError("segmented comparison exceeds retained actual receiver clocks")
    index = bisect_right(times, clock) - 1
    if index == len(times) - 1 or times[index] == clock:
        return values[index]
    weight = (clock - times[index]) / (times[index + 1] - times[index])
    return values[index] + weight * (values[index + 1] - values[index])


def compare_traces(left, right, left_summary, right_summary, *, comparison_kind="REFERENCE_PRECISION"):
    """A separate full receiver falsifier; no producer re-execution."""
    if any(type(row) is not sc.SegmentedTrace for row in (left, right)) or any(type(row) is not SegmentedTraceSummary for row in (left_summary, right_summary)):
        raise ValueError("segmented comparison requires actual traces and independent summaries")
    for trace, summary in ((left, left_summary), (right, right_summary)):
        if (summary.trace != identity(trace, "trace_id") or dr.forecast_primitive(summary.configuration.native) != dr.forecast_primitive(trace.config.native)
                or summary.configuration.method != trace.config.method or summary.configuration.preparation != trace.config.preparation):
            raise ValueError("segmented pair substitutes actual original trace/selected condition")
    a, b = left_summary.configuration, right_summary.configuration
    if any(getattr(a.native, name) != getattr(b.native, name) for name in ("source", "policy", "phase", "initial_temperature_k", "recipe")):
        raise ValueError("segmented pair changes its exact selected physical preparation")
    if comparison_kind == "REFERENCE_PRECISION":
        if a.method != b.method:
            raise ValueError("reference precision silently mixes different segmentation methods")
    elif comparison_kind == "SEGMENT_FIDELITY":
        if a.native != b.native or a.preparation != b.preparation or a.preparation_assessment != b.preparation_assessment or (
                a.method.maximum_segment_horizon_s, b.method.maximum_segment_horizon_s) not in {(D(60), D(30)), (D(30), D(15))}:
            raise ValueError("segment fidelity must isolate successive half/quarter horizons")
    else:
        raise ValueError("segmented comparison changes its declared scientific kind")
    reasons = set()
    td = vd = kd = None
    if any(summary.preparation.disposition is not A.SATISFIED or any(check.disposition is not A.SATISFIED for check in summary.segment_assessments)
            or summary.disposition is A.UNEVALUABLE for summary in (left_summary, right_summary)):
        reasons.add("reference-native-integrity-unresolved")
    elif not left.times_s or not right.times_s:
        reasons.add("reference-native-receivers-absent")
    else:
        if left_summary.disposition is not right_summary.disposition:
            reasons.add("reference-feasibility-disagrees")
        if left.disposition == right.disposition == "SERVICE_TERMINATED" and left.termination != right.termination:
            reasons.add("reference-termination-event-disagrees")
        td = abs(left.times_s[-1] - right.times_s[-1])
        end = min(left.times_s[-1], right.times_s[-1])
        clocks = tuple(D(value) for value in range(int(end) + 1)) + (end,)
        vd = max(abs(_interpolate(left.times_s, left.voltage_v, clock) - _interpolate(right.times_s, right.voltage_v, clock)) for clock in clocks)
        kd = max(abs(_interpolate(left.times_s, left.mean_temperature_k, clock) - _interpolate(right.times_s, right.mean_temperature_k, clock)) for clock in clocks)
        if td > D(1):
            reasons.add("reference-terminal-clock-precision-unresolved")
        if vd > D(".001"):
            reasons.add("reference-voltage-precision-unresolved")
        if kd > D(".01"):
            reasons.add("reference-temperature-precision-unresolved")
    return SegmentedComparison("comparison." + comparison_kind.lower() + "." + a.config_id + "." + b.config_id,
        identity(a, "config_id"), identity(b, "config_id"), left_summary.trace, right_summary.trace, comparison_kind,
        A.UNEVALUABLE if reasons else A.SATISFIED, td, vd, kd, tuple(sorted(reasons)))


@dataclass(frozen=True, slots=True)
class SegmentedQualification(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/qualification"
    product_id: str
    roster: sr.SegmentedQualificationRoster
    summaries: tuple[SegmentedTraceSummary, ...]
    comparisons: tuple[SegmentedComparison, ...]
    admitted_models: tuple[str, ...]
    selected_model: str | None
    model_reasons: tuple[tuple[str, tuple[str, ...]], ...]
    model_cpu_seconds: tuple[tuple[str, Decimal], ...]
    disposition: A
    reason_codes: tuple[str, ...]
    segment_fidelity: str = "UNASSESSED;NOT_A_LATER_USE_SUPPLIER"

    def __post_init__(self):
        validate_stable_id(self.product_id)
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes")
        if (type(self.roster) is not sr.SegmentedQualificationRoster or len(self.summaries) != 54 or len(self.comparisons) != 36
                or tuple(row.configuration for row in self.summaries) != self.roster.configurations
                or tuple((row.left_configuration.object_id, row.right_configuration.object_id) for row in self.comparisons) != self.roster.comparison_config_pairs
                or self.segment_fidelity != "UNASSESSED;NOT_A_LATER_USE_SUPPLIER" or self.selected_model is not None
                or self.disposition is not A.UNEVALUABLE):
            raise ValueError("single-method qualification cannot omit the complete census or bypass segment fidelity")


def qualify_summaries(roster, summaries, comparisons):
    """Retain all54/36 results, with later use blocked pending separate fidelity."""
    roster.__post_init__()
    by_config = {summary.configuration.config_id: summary for summary in summaries}
    if (len(summaries) != 54 or len(by_config) != 54 or set(by_config) != {config.config_id for config in roster.configurations}
            or any(type(summary) is not SegmentedTraceSummary for summary in summaries)):
        raise ValueError("segmented qualification omits its complete selected forecast denominator")
    ordered = tuple(by_config[config.config_id] for config in roster.configurations)
    if tuple(summary.configuration for summary in ordered) != roster.configurations:
        raise ValueError("segmented qualification substitutes immutable selected operands")
    pairs = {(comparison.left_configuration.object_id, comparison.right_configuration.object_id): comparison for comparison in comparisons}
    if (len(comparisons) != 36 or len(pairs) != 36 or set(pairs) != set(roster.comparison_config_pairs)
            or any(type(comparison) is not SegmentedComparison or comparison.comparison_kind != "REFERENCE_PRECISION" for comparison in comparisons)):
        raise ValueError("segmented qualification omits its complete independent comparison denominator")
    ordered_comparisons = tuple(pairs[pair] for pair in roster.comparison_config_pairs)
    for summary in ordered:
        if summary.condition_reuse is not None:
            original = by_config.get(summary.condition_reuse.observed_configuration.config_id)
            if original is None or summary != reuse_summary(summary.configuration, original):
                raise ValueError("segmented alias differs from authenticated original summary")
    for comparison in ordered_comparisons:
        if (comparison.left_configuration != identity(by_config[comparison.left_configuration.object_id].configuration, "config_id")
                or comparison.right_configuration != identity(by_config[comparison.right_configuration.object_id].configuration, "config_id")
                or comparison.left_trace != by_config[comparison.left_configuration.object_id].trace
                or comparison.right_trace != by_config[comparison.right_configuration.object_id].trace):
            raise ValueError("segmented comparison substitutes original source/trace identities")
    checks = {(summary.configuration.native.initial_temperature_k, summary.configuration.native.recipe, summary.configuration.native.component_view): summary for summary in ordered}
    policy = roster.configurations[0].native.policy
    model_reasons = tuple((model, historical_science._model_admission(policy.development_preparations, checks, model)) for model in c.REDUCED)
    admitted = tuple(model for model, reasons in model_reasons if not reasons)
    costs = tuple((model, sum((summary.cpu_seconds for summary in ordered if summary.configuration.native.component_view == model), D(0)))
        for model in (*c.REDUCED, "dfn-primary"))
    reasons = {"independent-segment-convergence-controls-unassessed"}
    if any(summary.preparation.disposition is not A.SATISFIED or any(check.disposition is not A.SATISFIED for check in summary.segment_assessments) for summary in ordered):
        reasons.add("complete-independent-native-preparation-or-segment-integrity-unresolved")
    if any(comparison.disposition is not A.SATISFIED for comparison in ordered_comparisons):
        reasons.add("complete-independent-reference-precision-unresolved")
    return SegmentedQualification("product.segmented." + str(roster.method.maximum_segment_horizon_s), roster, ordered, ordered_comparisons,
        admitted, None, model_reasons, costs, A.UNEVALUABLE, tuple(sorted(reasons)))


@dataclass(frozen=True, slots=True)
class SegmentedFidelityQualification(CanonicalRecord):
    """All selected outcomes plus isolated half/quarter continuation controls."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/fidelity-qualification"
    product_id: str
    method_qualifications: tuple[SegmentedQualification, ...]
    fidelity_comparisons: tuple[SegmentedComparison, ...]
    admitted_models: tuple[str, ...]
    selected_model: str | None
    model_reasons: tuple[tuple[str, tuple[str, ...]], ...]
    disposition: A
    reason_codes: tuple[str, ...]
    selected_forecast_slots: int = 162
    distinct_forecast_effects: int = 144
    derived_equal_condition_uses: int = 18
    selected_reference_comparisons: int = 108
    selected_fidelity_comparisons: int = 108
    fresh_physical_units: int = 0
    whole_time_certified: bool = False
    physical_qualification: bool = False
    historical_completion: str = "NOT_ASSESSED;OLD_UNKNOWN_RETAINED"
    full_state_fidelity: str = "UNASSESSED;RECEIVER_PRECISION_DOES_NOT_ADMIT_FULL_STATE_CONVERGENCE"

    def __post_init__(self):
        validate_stable_id(self.product_id)
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes")
        if (len(self.method_qualifications) != 3 or any(type(row) is not SegmentedQualification for row in self.method_qualifications)
                or tuple(row.roster.method.maximum_segment_horizon_s for row in self.method_qualifications) != (D(60), D(30), D(15))
                or len(self.fidelity_comparisons) != 108 or any(type(row) is not SegmentedComparison or row.comparison_kind != "SEGMENT_FIDELITY" for row in self.fidelity_comparisons)
                or (self.selected_forecast_slots, self.distinct_forecast_effects, self.derived_equal_condition_uses,
                    self.selected_reference_comparisons, self.selected_fidelity_comparisons) != (162, 144, 18, 108, 108)
                or self.fresh_physical_units != 0 or self.whole_time_certified or self.physical_qualification
                or self.historical_completion != "NOT_ASSESSED;OLD_UNKNOWN_RETAINED"
                or self.full_state_fidelity != "UNASSESSED;RECEIVER_PRECISION_DOES_NOT_ADMIT_FULL_STATE_CONVERGENCE"
                or type(self.disposition) is not A or (self.disposition is A.SATISFIED) != (self.selected_model is not None)
                or self.selected_model is not None or self.disposition is not A.UNEVALUABLE
                or self.selected_model is not None and self.selected_model not in (*c.REDUCED, "dfn-primary")
                or self.selected_model in c.REDUCED and self.selected_model not in self.admitted_models
                or self.disposition is not A.SATISFIED and not self.reason_codes):
            raise ValueError("fidelity qualification omits full selected controls or invents later-use admission")


def qualify_fidelity(method_qualifications, fidelity_comparisons):
    """Recompute complete method products, then join all isolated controls.

    Authentic ordinary input receipts remain the caller's boundary. This pure
    reduction neither grants execution authority nor certifies continuous time.
    A completed negative forecast is permitted; unresolved integrity or numerical
    precision keeps the later-use frontier unentered.
    """
    products = tuple(method_qualifications)
    if (len(products) != 3 or any(type(row) is not SegmentedQualification for row in products)
            or tuple(row.roster.method.maximum_segment_horizon_s for row in products) != (D(60), D(30), D(15))):
        raise ValueError("fidelity supplier requires complete sixty/half/quarter method products")
    original = products[0].roster.original_selection
    history = products[0].roster.uncertain_work
    for product in products:
        if (product.roster.original_selection != original or product.roster.uncertain_work != history
                or product != qualify_summaries(product.roster, product.summaries, product.comparisons)):
            raise ValueError("fidelity supplier substitutes a complete independently recomputed method product")
    pairs = tuple((left.configuration.config_id, right.configuration.config_id)
        for a, b in zip(products, products[1:]) for left, right in zip(a.summaries, b.summaries, strict=True))
    comparisons = {(row.left_configuration.object_id, row.right_configuration.object_id): row for row in fidelity_comparisons}
    if (len(fidelity_comparisons) != 108 or len(comparisons) != 108 or set(comparisons) != set(pairs)
            or any(type(row) is not SegmentedComparison or row.comparison_kind != "SEGMENT_FIDELITY" for row in fidelity_comparisons)):
        raise ValueError("fidelity supplier omits complete one-hundred-eight selected comparisons")
    ordered = tuple(comparisons[pair] for pair in pairs)
    summaries = {row.configuration.config_id: row for product in products for row in product.summaries}
    for comparison in ordered:
        left, right = summaries[comparison.left_configuration.object_id], summaries[comparison.right_configuration.object_id]
        if (comparison.left_configuration != identity(left.configuration, "config_id") or comparison.right_configuration != identity(right.configuration, "config_id")
                or comparison.left_trace != left.trace or comparison.right_trace != right.trace
                or left.configuration.native != right.configuration.native
                or left.configuration.preparation != right.configuration.preparation
                or left.configuration.preparation_assessment != right.configuration.preparation_assessment):
            raise ValueError("fidelity supplier changes its isolated native/root/trace operands")
    why = {"complete-independent-full-state-convergence-unassessed"}
    if any(row.disposition is not A.SATISFIED for product in products for row in product.comparisons):
        why.add("complete-independent-reference-precision-unresolved")
    if any(row.disposition is not A.SATISFIED for row in ordered):
        why.add("complete-independent-segment-convergence-unresolved")
    if any(summary.preparation.disposition is not A.SATISFIED or any(row.disposition is not A.SATISFIED for row in summary.segment_assessments)
            or summary.disposition is A.UNEVALUABLE for product in products for summary in product.summaries):
        why.add("complete-independent-native-preparation-or-segment-integrity-unresolved")
    model_reasons = tuple((model, tuple(sorted({reason for product in products for name, reasons in product.model_reasons if name == model for reason in reasons})))
        for model in c.REDUCED)
    admitted = tuple(model for model, reasons in model_reasons if not reasons)
    selected = None if why else min(admitted, key=lambda model: (dict(products[0].model_cpu_seconds)[model], model)) if admitted else "dfn-primary"
    if selected == "dfn-primary":
        why.add("reduced-models-refused-direct-dfn-fallback")
    return SegmentedFidelityQualification("product.segmented.complete-fidelity", products, ordered, admitted, selected, model_reasons,
        A.SATISFIED if selected is not None else A.UNEVALUABLE, tuple(sorted(why)))


def require_fidelity_supplier(product):
    if type(product) is not SegmentedFidelityQualification or product != qualify_fidelity(product.method_qualifications, product.fidelity_comparisons):
        raise ValueError("later use requires exact complete independently recomputed fidelity supplier")
    if product.disposition is not A.SATISFIED:
        raise ValueError("later use remains unentered while complete independent fidelity is unresolved")
    return product

