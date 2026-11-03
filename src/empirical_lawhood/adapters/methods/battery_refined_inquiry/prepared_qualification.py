# SPDX-License-Identifier: MPL-2.0
"""Compact fresh qualification requires each independently assessed preparation.

One PURE task reduces one trace; a comparison task needs only its two traces.
The final reducer consumes their compact products and never loads the full
54-trace population into memory. Historical qualification remains readable at
its original scientific scope.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.kernel.serialization import CanonicalRecord, require_sorted_unique_strings, validate_decimal, validate_stable_id
from . import contracts as c, science
from .preparation_contracts import InitialPreparationAssessment, identity
from .preparation_science import trace_identity
from .durable_roster import ExactConditionReuse, forecast_primitive

D = Decimal


@dataclass(frozen=True, slots=True)
class PreparedTraceSummary(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-preparation/trace-summary"
    summary_id: str
    configuration: c.NativeConfig
    trace: ObjectIdentity
    receiver_check: c.TraceCheck
    preparation: InitialPreparationAssessment
    cpu_seconds: Decimal
    wall_seconds: Decimal
    native_provider_attempts: int
    backend_solve_calls: int
    initializer_calls: int
    disposition: A
    reason_codes: tuple[str, ...]
    condition_reuse: ExactConditionReuse | None = None

    def __post_init__(self):
        validate_stable_id(self.summary_id)
        if type(self.configuration) is not c.NativeConfig or type(self.receiver_check) is not c.TraceCheck or type(self.preparation) is not InitialPreparationAssessment:
            raise ValueError("fresh summary substitutes its typed native/independent operands")
        if self.trace != self.receiver_check.trace or self.trace != self.preparation.trace:
            raise ValueError("fresh summary substitutes its actual assessed trace")
        if self.condition_reuse is None:
            if self.trace.object_id != "trace." + self.configuration.config_id:
                raise ValueError("fresh summary changes its exact original trace configuration")
        elif (type(self.condition_reuse) is not ExactConditionReuse
                or self.condition_reuse.requested_configuration != self.configuration
                or self.condition_reuse.original_trace != self.trace):
            raise ValueError("derived summary loses its explicit exact-condition reuse")
        for name in ("cpu_seconds", "wall_seconds"):
            validate_decimal(getattr(self, name), field_name=name)
            if getattr(self, name) < 0:
                raise ValueError("fresh summary has negative measured cost")
        if self.native_provider_attempts != (1 if self.condition_reuse is None else 0) or any(type(value) is not int or value < 0 for value in (self.backend_solve_calls, self.initializer_calls)):
            raise ValueError("fresh summary loses actual native-call accounting")
        if self.condition_reuse is not None and any((self.cpu_seconds, self.wall_seconds, self.backend_solve_calls, self.initializer_calls)):
            raise ValueError("derived summary double-counts original measured contact costs")
        expected = A.UNEVALUABLE if self.preparation.disposition is not A.SATISFIED else self.receiver_check.disposition
        nx, nr = self.configuration.numerical_view.electrode_points, self.configuration.numerical_view.particle_points
        expected_rhs = 3 + 3 * nx + 2 * (nx * nr if "dfn" in self.configuration.model_view else nr)
        if self.preparation.disposition is A.SATISFIED and (self.preparation.join is None or self.preparation.checked_state_components != expected_rhs):
            raise ValueError("satisfied preparation omits its complete joined differential-state denominator")
        if self.disposition is not expected:
            raise ValueError("fresh trace admission bypasses independent preparation")
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes")
        if self.disposition is not A.SATISFIED and not self.reason_codes:
            raise ValueError("fresh summary loses its negative/uncertain outcome")

    @property
    def completion_time_s(self):
        return self.receiver_check.completion_time_s if self.disposition is A.SATISFIED else None


@dataclass(frozen=True, slots=True)
class PreparedQualification(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-preparation/qualification"
    product_id: str
    source: c.RefinedSource
    policy: c.NumericalPolicy
    summaries: tuple[PreparedTraceSummary, ...]
    comparisons: tuple["PreparedComparisonSummary", ...]
    admitted_models: tuple[str, ...]
    selected_model: str | None
    model_reasons: tuple[tuple[str, tuple[str, ...]], ...]
    model_cpu_seconds: tuple[tuple[str, Decimal], ...]
    disposition: A
    reason_codes: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.product_id)
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes")
        if self.source.policy != c.identity(self.policy):
            raise ValueError("fresh qualification changes its exact source/policy")
        expected = science.configurations(self.source, self.policy)
        if tuple(s.configuration for s in self.summaries) != expected:
            raise ValueError("fresh qualification omits, reorders or substitutes its full forecast census")
        if (self.disposition is A.SATISFIED) != (self.selected_model is not None):
            raise ValueError("fresh qualification invents admitted-model status")
        if self.selected_model is not None and (any(s.preparation.disposition is not A.SATISFIED for s in self.summaries)
                or any(comparison.disposition is not A.SATISFIED for comparison in self.comparisons)):
            raise ValueError("fresh qualification bypasses preparation or independent precision")


def summarize_trace(trace, preparation):
    """Called by a receipt-bound independent PURE trace task, not the producer."""
    if type(trace) is not c.Trace or type(preparation) is not InitialPreparationAssessment or preparation.trace != trace_identity(trace):
        raise ValueError("fresh summary requires its exact trace/preparation join")
    receiver = science.check_trace(trace)
    disposition = A.UNEVALUABLE if preparation.disposition is not A.SATISFIED else receiver.disposition
    reasons = set(receiver.reason_codes)
    if preparation.disposition is not A.SATISFIED:
        reasons.update(preparation.reason_codes)
        reasons.add("independent-initial-preparation-unadmitted")
    return PreparedTraceSummary("summary.prepared." + trace.trace_id, trace.config, trace_identity(trace), receiver,
        preparation, trace.cpu_seconds, trace.wall_seconds, trace.native_provider_attempts, trace.backend_solve_calls,
        len(trace.initializer_attempts), disposition, tuple(sorted(reasons)))


@dataclass(frozen=True, slots=True)
class PreparedComparisonSummary(CanonicalRecord):
    """One selected pair, retaining the original actual two-trace assessment."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-preparation/comparison-summary"
    summary_id: str
    left_configuration: ObjectIdentity
    right_configuration: ObjectIdentity
    comparison: c.Comparison

    def __post_init__(self):
        validate_stable_id(self.summary_id)
        if (type(self.comparison) is not c.Comparison
                or any(value.object_schema != c.NativeConfig.SCHEMA for value in (self.left_configuration, self.right_configuration))):
            raise ValueError("selected comparison substitutes its typed original operands")

    @property
    def disposition(self):
        return self.comparison.disposition


def reuse_summary(requested_configuration, observed_summary):
    """Preserve the original trace identity and measured cost once, explicitly."""
    from hashlib import sha256
    if type(observed_summary) is not PreparedTraceSummary or observed_summary.condition_reuse is not None:
        raise ValueError("conditional reuse requires its original actual compact summary")
    reuse = ExactConditionReuse("reuse." + requested_configuration.config_id, requested_configuration,
        observed_summary.configuration, observed_summary.trace, summary_identity(observed_summary),
        sha256(forecast_primitive(observed_summary.configuration)).hexdigest())
    return PreparedTraceSummary("summary.prepared." + requested_configuration.config_id, requested_configuration,
        observed_summary.trace, observed_summary.receiver_check, observed_summary.preparation, D(0), D(0), 0, 0, 0,
        observed_summary.disposition, observed_summary.reason_codes, reuse)


def comparison_summary(left_summary, right_summary, comparison):
    if (type(left_summary) is not PreparedTraceSummary or type(right_summary) is not PreparedTraceSummary
            or type(comparison) is not c.Comparison or comparison.left != left_summary.trace or comparison.right != right_summary.trace):
        raise ValueError("selected comparison loses its actual original trace joins")
    return PreparedComparisonSummary("comparison.prepared." + left_summary.configuration.config_id + "." + right_summary.configuration.component_view,
        c.identity(left_summary.configuration), c.identity(right_summary.configuration), comparison)


def qualify_summaries(source, policy, summaries, comparisons):
    """Complete compact denominator; separate preparation/precision/selection."""
    expected = science.configurations(source, policy)
    if len(summaries) != len(expected) or any(type(s) is not PreparedTraceSummary for s in summaries):
        raise ValueError("fresh qualification requires all compact forecast summaries")
    by_config = {s.configuration.config_id: s for s in summaries}
    if len(by_config) != len(summaries) or set(by_config) != {native.config_id for native in expected}:
        raise ValueError("fresh qualification omits, duplicates or substitutes forecast summaries")
    ordered = tuple(by_config[native.config_id] for native in expected)
    if tuple(s.configuration for s in ordered) != expected:
        raise ValueError("fresh summary changes an immutable selected native operand")
    rows = {(s.configuration.initial_temperature_k, s.configuration.recipe, s.configuration.component_view): s for s in ordered}
    pairs = tuple((c.identity(rows[t, r, left].configuration), c.identity(rows[t, r, right].configuration))
        for t, r in policy.development_preparations for left, right in policy.comparison_pairs)
    # Historical receiver-only fixtures can enter this compact engineering
    # reducer; each assessment is explicitly bound to its selected config pair.
    if all(type(cmp) is c.Comparison for cmp in comparisons):
        original = {(summary.trace, summary.configuration.config_id): summary for summary in ordered}
        comparisons = tuple(comparison_summary(original[cmp.left, cmp.left.object_id.removeprefix("trace.")],
            original[cmp.right, cmp.right.object_id.removeprefix("trace.")], cmp) for cmp in comparisons)
    if len(comparisons) != len(pairs) or any(type(cmp) is not PreparedComparisonSummary for cmp in comparisons):
        raise ValueError("fresh qualification omits complete independent precision comparisons")
    actual_pairs = {(cmp.left_configuration, cmp.right_configuration): cmp for cmp in comparisons}
    if len(actual_pairs) != len(comparisons) or set(actual_pairs) != set(pairs):
        raise ValueError("fresh qualification changes its exact two-trace comparison roster")
    ordered_comparisons = tuple(actual_pairs[pair] for pair in pairs)
    by_identity = {c.identity(summary.configuration): summary for summary in ordered}
    for cmp in ordered_comparisons:
        if (cmp.comparison.left != by_identity[cmp.left_configuration].trace
                or cmp.comparison.right != by_identity[cmp.right_configuration].trace):
            raise ValueError("selected comparison substitutes original trace assessment")
    for summary in ordered:
        if summary.condition_reuse is not None:
            original_summary = by_identity.get(c.identity(summary.condition_reuse.observed_configuration))
            if original_summary is None or summary != reuse_summary(summary.configuration, original_summary):
                raise ValueError("conditional reuse differs from its authenticated complete original summary")
    reasons_by_model = tuple((model, science._model_admission(policy.development_preparations, rows, model)) for model in c.REDUCED)
    admitted = tuple(model for model, reasons in reasons_by_model if not reasons)
    costs = tuple((model, sum((s.cpu_seconds for s in ordered if s.configuration.component_view == model), D(0)))
        for model in (*c.REDUCED, "dfn-primary"))
    reasons = set()
    if any(s.preparation.disposition is not A.SATISFIED for s in ordered):
        reasons.add("complete-independent-initial-preparation-unresolved")
    if any(comparison.disposition is not A.SATISFIED for comparison in ordered_comparisons):
        reasons.add("complete-independent-reference-precision-unresolved")
    selected = None if reasons else min(admitted, key=lambda model: (dict(costs)[model], model)) if admitted else "dfn-primary"
    if not reasons and not admitted:
        reasons.add("reduced-models-refused-direct-dfn-fallback")
    return PreparedQualification("product.battery-preparation.qualification", source, policy, ordered,
        ordered_comparisons, admitted, selected, reasons_by_model, costs, A.UNEVALUABLE if selected is None else A.SATISFIED,
        tuple(sorted(reasons)))


def require_current_qualification(qualification):
    """Every fresh later-use route must pass the independently reconstructed join."""
    if type(qualification) is not PreparedQualification:
        raise ValueError("current qualification requires its additive preparation-aware schema")
    if qualification != qualify_summaries(qualification.source, qualification.policy, qualification.summaries, qualification.comparisons):
        raise ValueError("current qualification differs from its complete independent compact reduction")
    if qualification.disposition is not A.SATISFIED:
        raise ValueError("current qualification has no admitted model")
    return qualification


def summary_identity(summary):
    return identity(summary, summary.summary_id)
