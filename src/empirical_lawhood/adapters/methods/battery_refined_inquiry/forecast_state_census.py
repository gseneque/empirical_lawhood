# SPDX-License-Identifier: MPL-2.0
"""Complete compact fixed-budget state census; no supplier admission.

Actual full-state products and native assignments have distinct identities.
Equal-condition uses remain explicit derivations, never new observations.
Event, regime, uncovered suffix and real-clock uncertainty remain retained.
"""
from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.kernel.serialization import CanonicalRecord, require_sorted_unique_strings, validate_stable_id
from . import forecast_state_control as state, forecast_step_control as step
from . import segmented_contracts as contracts, segmented_evidence as evidence
from . import segmented_fidelity_stream as stream, segmented_qualification as qualification


@dataclass(frozen=True, slots=True)
class ForecastStateConclusion(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/fixed-budget-state-conclusion"
    conclusion_id: str
    original_assessment: ObjectIdentity
    control: ObjectIdentity
    actual_assignment_evidence: tuple[ObjectIdentity, ObjectIdentity]
    configurations: tuple[ObjectIdentity, ObjectIdentity]
    traces: tuple[ObjectIdentity, ObjectIdentity]
    evidence: tuple[ObjectIdentity, ObjectIdentity]
    declared_segment_counts: tuple[int, int]
    retained_native_knots: tuple[int, int]
    actual_terminal_clocks: tuple[tuple[int, int] | None, tuple[int, int] | None]
    transition_counts: tuple[int, int]
    interval_count: int
    interval_dispositions: tuple[tuple[str, int], ...]
    comparison_counts: tuple[int, int, int, int]
    coverage_issues: tuple[stream.StreamCoverageIssue, ...]
    disposition: A
    reason_codes: tuple[str, ...]
    scope: str = "COMPLETE_FIXED_BUDGET_STATE_AND_ACTUAL_ASSIGNMENTS;COVERAGE_AND_ADMISSION_SEPARATE"

    def __post_init__(self):
        validate_stable_id(self.conclusion_id)
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes")
        if (type(self.original_assessment) is not ObjectIdentity or self.original_assessment.object_schema != state.ForecastStateStream.SCHEMA
                or type(self.control) is not ObjectIdentity or self.control.object_schema != state.ForecastStateControl.SCHEMA
                or any(type(rows) is not tuple or len(rows) != 2 or any(type(row) is not ObjectIdentity or row.object_schema != schema for row in rows)
                    for rows, schema in ((self.actual_assignment_evidence, step.ForecastStepEvidence.SCHEMA),
                        (self.configurations, contracts.SegmentedNativeConfig.SCHEMA), (self.traces, contracts.SegmentedTrace.SCHEMA),
                        (self.evidence, evidence.SegmentedNativeEvidence.SCHEMA)))
                or any(type(rows) is not tuple or len(rows) != 2 or any(type(row) is not int or row < 0 for row in rows)
                    for rows in (self.declared_segment_counts, self.retained_native_knots, self.transition_counts))
                or type(self.interval_count) is not int or self.interval_count < 0
                or type(self.interval_dispositions) is not tuple
                or tuple(name for name, _ in self.interval_dispositions) != tuple(sorted(row.value for row in A))
                or any(type(n) is not int or n < 0 for _, n in self.interval_dispositions)
                or sum(n for _, n in self.interval_dispositions) != self.interval_count
                or type(self.comparison_counts) is not tuple or len(self.comparison_counts) != 4
                or any(type(n) is not int or n < 0 for n in self.comparison_counts)
                or type(self.coverage_issues) is not tuple or any(type(row) is not stream.StreamCoverageIssue for row in self.coverage_issues)
                or type(self.disposition) is not A or self.disposition is not A.SATISFIED and not self.reason_codes
                or self.scope != "COMPLETE_FIXED_BUDGET_STATE_AND_ACTUAL_ASSIGNMENTS;COVERAGE_AND_ADMISSION_SEPARATE"
                or type(self.actual_terminal_clocks) is not tuple or len(self.actual_terminal_clocks) != 2):
            raise ValueError("fixed-budget state conclusion loses complete scientific identities, counts or uncertainty")
        for row in self.coverage_issues:
            row.__post_init__()
        for clock in self.actual_terminal_clocks:
            if clock is not None:
                stream._require_fraction(clock)
        if self.disposition is A.SATISFIED and (self.reason_codes or self.coverage_issues or any(self.transition_counts)
                or not self.interval_count or any(n for name, n in self.interval_dispositions if name != A.SATISFIED.value)
                or self.actual_terminal_clocks[0] is None or self.actual_terminal_clocks[0] != self.actual_terminal_clocks[1]):
            raise ValueError("fixed-budget state conclusion promotes unresolved original coverage")


def compact_assessment(original):
    if type(original) is not state.ForecastStateStream:
        raise ValueError("fixed-budget conclusion needs its complete original typed scientific assessment")
    original.__post_init__()
    return ForecastStateConclusion("conclusion." + original.assessment_id,
        step.identity(original, "assessment_id"), original.control, original.actual_assignment_evidence,
        (original.left_configuration, original.right_configuration), (original.left_trace, original.right_trace),
        (original.left_evidence, original.right_evidence), original.declared_segment_counts,
        original.original_retained_native_knots, original.actual_terminal_clocks, original.declared_transition_counts,
        len(original.intervals), tuple((name, sum(row.disposition.value == name for row in original.intervals)) for name in sorted(row.value for row in A)),
        (original.interval_queries_including_repeated_boundaries, original.compared_rhs_components,
            original.compared_algebraic_components, original.compared_derivative_components),
        original.coverage_issues, original.disposition, original.reason_codes)


@dataclass(frozen=True, slots=True)
class ForecastStateSelectedUse(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/fixed-budget-state-selected-use"
    requested_configurations: tuple[ObjectIdentity, ObjectIdentity]
    actual_configurations: tuple[ObjectIdentity, ObjectIdentity]
    conclusion: ObjectIdentity
    equal_condition_derivations: tuple[ObjectIdentity, ...]

    def __post_init__(self):
        if (any(type(rows) is not tuple or len(rows) != 2 or any(type(row) is not ObjectIdentity or row.object_schema != contracts.SegmentedNativeConfig.SCHEMA for row in rows)
                for rows in (self.requested_configurations, self.actual_configurations))
                or type(self.conclusion) is not ObjectIdentity or self.conclusion.object_schema != ForecastStateConclusion.SCHEMA
                or type(self.equal_condition_derivations) is not tuple
                or len(self.equal_condition_derivations) != (0 if self.requested_configurations == self.actual_configurations else 2)
                or any(type(row) is not ObjectIdentity or row.object_schema != qualification.SegmentedConditionReuse.SCHEMA for row in self.equal_condition_derivations)):
            raise ValueError("fixed-budget state selected use substitutes actual source or equal-condition derivation")


@dataclass(frozen=True, slots=True)
class ForecastStateCensus(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/fixed-budget-state-census"
    census_id: str
    receiver_fidelity: ObjectIdentity
    conclusions: tuple[ForecastStateConclusion, ...]
    selected_uses: tuple[ForecastStateSelectedUse, ...]
    disposition: A
    reason_codes: tuple[str, ...]
    scope: str = "FULL108_USES96_DISTINCT12_EQUAL;NO_MODEL_ADMISSION_OR_FRESH_PHYSICAL_UNITS"

    def __post_init__(self):
        validate_stable_id(self.census_id)
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes")
        if (type(self.receiver_fidelity) is not ObjectIdentity or self.receiver_fidelity.object_schema != qualification.SegmentedFidelityQualification.SCHEMA
                or type(self.conclusions) is not tuple or len(self.conclusions) != 96 or any(type(row) is not ForecastStateConclusion for row in self.conclusions)
                or type(self.selected_uses) is not tuple or len(self.selected_uses) != 108 or any(type(row) is not ForecastStateSelectedUse for row in self.selected_uses)
                or len({row.original_assessment for row in self.conclusions}) != 96
                or len({row.configurations for row in self.conclusions}) != 96
                or len({row.requested_configurations for row in self.selected_uses}) != 108
                or sum(bool(row.equal_condition_derivations) for row in self.selected_uses) != 12
                or len({row.control for row in self.conclusions}) != 1
                or self.scope != "FULL108_USES96_DISTINCT12_EQUAL;NO_MODEL_ADMISSION_OR_FRESH_PHYSICAL_UNITS"):
            raise ValueError("fixed-budget state census omits complete original denominators or scientific controls")
        for row in (*self.conclusions, *self.selected_uses):
            row.__post_init__()
        stock = {step.identity(row, "conclusion_id"): row for row in self.conclusions}
        if (set(stock) != {row.conclusion for row in self.selected_uses}
                or any(stock[row.conclusion].configurations != row.actual_configurations for row in self.selected_uses)):
            raise ValueError("fixed-budget state census changes an original actual paired control")
        reasons = tuple(sorted({code for row in self.conclusions for code in row.reason_codes}))
        disposition = A.FALSIFIED if any(row.disposition is A.FALSIFIED for row in self.conclusions) else A.UNEVALUABLE if reasons else A.SATISFIED
        if self.reason_codes != reasons or self.disposition is not disposition or self.disposition is A.SATISFIED and any(row.disposition is not A.SATISFIED for row in self.conclusions):
            raise ValueError("fixed-budget state census hides an adverse or uncertain original outcome")


def join_complete_state(receiver, conclusions):
    """Recompute receiver denominator; join all actual/equal-condition identities."""
    if (type(receiver) is not qualification.SegmentedFidelityQualification
            or receiver != qualification.qualify_fidelity(receiver.method_qualifications, receiver.fidelity_comparisons)):
        raise ValueError("fixed-budget state census needs the exact full independently recomputed receiver denominator")
    rows = tuple(conclusions)
    if len(rows) != 96 or any(type(row) is not ForecastStateConclusion for row in rows):
        raise ValueError("fixed-budget state census needs all ninety-six distinct completed original controls")
    stock = {row.configurations: row for row in rows}
    if len(stock) != 96:
        raise ValueError("fixed-budget state census duplicates an original control")
    uses = []
    for a, b in zip(receiver.method_qualifications, receiver.method_qualifications[1:]):
        for left, right in zip(a.summaries, b.summaries, strict=True):
            actual = tuple(row.configuration if row.condition_reuse is None else row.condition_reuse.observed_configuration for row in (left, right))
            key = tuple(step.identity(row, "config_id") for row in actual)
            conclusion = stock.get(key)
            if conclusion is None or conclusion.traces != (left.trace, right.trace):
                raise ValueError("fixed-budget state census omits actual selected trace/source operands")
            uses.append(ForecastStateSelectedUse(tuple(step.identity(row.configuration, "config_id") for row in (left, right)),
                key, step.identity(conclusion, "conclusion_id"), tuple(step.identity(row.condition_reuse, "reuse_id") for row in (left, right) if row.condition_reuse is not None)))
    reasons = tuple(sorted({code for row in rows for code in row.reason_codes}))
    disposition = A.FALSIFIED if any(row.disposition is A.FALSIFIED for row in rows) else A.UNEVALUABLE if reasons else A.SATISFIED
    return ForecastStateCensus("census.fixed-budget." + receiver.product_id, step.identity(receiver, "product_id"),
        tuple(stock[key] for key in sorted(stock, key=lambda values: tuple(row.object_id for row in values))), tuple(uses), disposition, reasons)
