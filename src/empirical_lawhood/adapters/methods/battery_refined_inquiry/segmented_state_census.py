# SPDX-License-Identifier: MPL-2.0
"""Compact complete full-state controls, without inventing later-use admission.

The original paired assessment remains primary custody. This projection retains
its identity, complete counts and all uncovered spans while discarding no native
data. A complete census joins the 108 selected uses to the 96 distinct controls;
equal-condition uses retain their actual original configuration and trace.
Native options, boundary/event/suffix qualification and admission remain separate
scientific operands. This owner neither changes an old assessment nor runs a model.
"""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.kernel.serialization import CanonicalRecord, require_sorted_unique_strings, validate_stable_id
from . import segmented_fidelity_stream as stream
from . import segmented_fidelity as local
from . import segmented_contracts as contracts
from . import segmented_evidence as evidence
from . import segmented_qualification as qualification


def _identity(record, field):
    return ObjectIdentity.from_record(getattr(record, field), record)


@dataclass(frozen=True, slots=True)
class FullStateConclusion(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/full-state-conclusion"
    conclusion_id: str
    original_assessment: ObjectIdentity
    control: ObjectIdentity
    configurations: tuple[ObjectIdentity, ObjectIdentity]
    traces: tuple[ObjectIdentity, ObjectIdentity]
    evidence: tuple[ObjectIdentity, ObjectIdentity]
    declared_segment_counts: tuple[int, int]
    retained_native_knots: tuple[int, int]
    actual_terminal_clocks: tuple[tuple[int, int] | None, tuple[int, int] | None]
    transition_counts: tuple[int, int]
    original_interval_count: int
    original_interval_dispositions: tuple[tuple[str, int], ...]
    comparison_counts: tuple[int, int, int, int]
    coverage_issues: tuple[stream.StreamCoverageIssue, ...]
    disposition: A
    reason_codes: tuple[str, ...]
    scope: str = "EXACT_COMPACT_ORIGINAL_STREAM_CONCLUSION;NOT_A_LATER_USE_SUPPLIER"
    whole_time_certified: bool = False
    physical_qualification: bool = False
    fresh_physical_units: int = 0

    def __post_init__(self):
        validate_stable_id(self.conclusion_id)
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes")
        if (type(self.original_assessment) is not ObjectIdentity
                or self.original_assessment.object_schema != stream.FullStateStreamAssessment.SCHEMA
                or type(self.control) is not ObjectIdentity or self.control.object_schema != local.FullStateControlProtocol.SCHEMA
                or any(type(rows) is not tuple or len(rows) != 2 or any(type(row) is not ObjectIdentity for row in rows)
                       for rows in (self.configurations, self.traces, self.evidence))
                or any(type(rows) is not tuple or len(rows) != 2 or any(type(n) is not int or n < 0 for n in rows)
                       for rows in (self.declared_segment_counts, self.retained_native_knots, self.transition_counts))
                or type(self.comparison_counts) is not tuple or len(self.comparison_counts) != 4
                or any(type(n) is not int or n < 0 for n in self.comparison_counts)
                or type(self.original_interval_count) is not int or self.original_interval_count < 0
                or tuple(name for name, _ in self.original_interval_dispositions) != tuple(sorted(row.value for row in A))
                or any(type(n) is not int or n < 0 for _, n in self.original_interval_dispositions)
                or sum(n for _, n in self.original_interval_dispositions) != self.original_interval_count
                or any(type(row) is not stream.StreamCoverageIssue for row in self.coverage_issues)
                or type(self.disposition) is not A
                or self.disposition is not A.SATISFIED and not self.reason_codes
                or self.scope != "EXACT_COMPACT_ORIGINAL_STREAM_CONCLUSION;NOT_A_LATER_USE_SUPPLIER"
                or type(self.whole_time_certified) is not bool or self.whole_time_certified
                or type(self.physical_qualification) is not bool or self.physical_qualification
                or type(self.fresh_physical_units) is not int or self.fresh_physical_units != 0):
            raise ValueError("compact state conclusion changes original census or scientific scope")
        for values, schema in ((self.configurations, contracts.SegmentedNativeConfig.SCHEMA),
                (self.traces, contracts.SegmentedTrace.SCHEMA), (self.evidence, evidence.SegmentedNativeEvidence.SCHEMA)):
            if any(row.object_schema != schema for row in values):
                raise ValueError("compact state conclusion substitutes scientific operand roles")
        if type(self.actual_terminal_clocks) is not tuple or len(self.actual_terminal_clocks) != 2:
            raise ValueError("compact state conclusion loses actual terminal clocks")
        for clock in self.actual_terminal_clocks:
            if clock is not None:
                stream._require_fraction(clock)
        for issue in self.coverage_issues:
            issue.__post_init__()
        if self.disposition is A.SATISFIED and (self.reason_codes or self.coverage_issues
                or any(self.transition_counts) or not self.original_interval_count
                or any(n for name, n in self.original_interval_dispositions if name != A.SATISFIED.value)
                or self.actual_terminal_clocks[0] is None or self.actual_terminal_clocks[0] != self.actual_terminal_clocks[1]):
            raise ValueError("compact state conclusion clears an unresolved original outcome")


def compact_stream_assessment(assessment):
    """Project one complete authenticated input; ordinary receipts bind originals."""
    if type(assessment) is not stream.FullStateStreamAssessment:
        raise ValueError("compact state conclusion requires the complete original typed assessment")
    assessment.__post_init__()
    return FullStateConclusion("conclusion." + assessment.assessment_id,
        _identity(assessment, "assessment_id"), assessment.control,
        (assessment.left_configuration, assessment.right_configuration),
        (assessment.left_trace, assessment.right_trace), (assessment.left_evidence, assessment.right_evidence),
        assessment.declared_segment_counts, assessment.original_retained_native_knots,
        assessment.actual_terminal_clocks, assessment.declared_transition_counts, len(assessment.intervals),
        tuple((name, sum(row.disposition.value == name for row in assessment.intervals)) for name in sorted(row.value for row in A)),
        (assessment.interval_queries_including_repeated_boundaries, assessment.compared_rhs_components,
            assessment.compared_algebraic_components, assessment.compared_derivative_components),
        assessment.coverage_issues, assessment.disposition, assessment.reason_codes)


@dataclass(frozen=True, slots=True)
class FullStateSelectedUse(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/full-state-selected-use"
    requested_configurations: tuple[ObjectIdentity, ObjectIdentity]
    actual_configurations: tuple[ObjectIdentity, ObjectIdentity]
    original_conclusion: ObjectIdentity
    equal_condition_derivations: tuple[ObjectIdentity, ...]
    fresh_physical_units: int = 0

    def __post_init__(self):
        if (any(type(rows) is not tuple or len(rows) != 2 or any(type(row) is not ObjectIdentity for row in rows)
                for rows in (self.requested_configurations, self.actual_configurations))
                or any(row.object_schema != contracts.SegmentedNativeConfig.SCHEMA
                       for row in (*self.requested_configurations, *self.actual_configurations))
                or type(self.original_conclusion) is not ObjectIdentity
                or self.original_conclusion.object_schema != FullStateConclusion.SCHEMA
                or type(self.equal_condition_derivations) is not tuple
                or len(self.equal_condition_derivations) != (0 if self.requested_configurations == self.actual_configurations else 2)
                or any(type(row) is not ObjectIdentity or row.object_schema != qualification.SegmentedConditionReuse.SCHEMA
                       for row in self.equal_condition_derivations)
                or type(self.fresh_physical_units) is not int or self.fresh_physical_units != 0):
            raise ValueError("full-state selected use invents configuration, source or fresh evidence")


@dataclass(frozen=True, slots=True)
class CompleteFullStateCensus(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/complete-full-state-census"
    census_id: str
    receiver_fidelity: ObjectIdentity
    conclusions: tuple[FullStateConclusion, ...]
    selected_uses: tuple[FullStateSelectedUse, ...]
    disposition: A
    reason_codes: tuple[str, ...]
    scope: str = "COMPLETE108_SELECTED96_DISTINCT12_DERIVED_STATE_CENSUS;NUMERICAL_RECIPE_AND_COVERAGE_ADMISSION_SEPARATE"
    selected_model: None = None
    whole_time_certified: bool = False
    physical_qualification: bool = False
    fresh_physical_units: int = 0

    def __post_init__(self):
        validate_stable_id(self.census_id)
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes")
        if (type(self.receiver_fidelity) is not ObjectIdentity
                or self.receiver_fidelity.object_schema != qualification.SegmentedFidelityQualification.SCHEMA
                or len(self.conclusions) != 96 or any(type(row) is not FullStateConclusion for row in self.conclusions)
                or len(self.selected_uses) != 108 or any(type(row) is not FullStateSelectedUse for row in self.selected_uses)
                or len({row.original_assessment for row in self.conclusions}) != 96
                or len({row.requested_configurations for row in self.selected_uses}) != 108
                or sum(bool(row.equal_condition_derivations) for row in self.selected_uses) != 12
                or type(self.disposition) is not A or self.disposition is not A.SATISFIED and not self.reason_codes
                or self.scope != "COMPLETE108_SELECTED96_DISTINCT12_DERIVED_STATE_CENSUS;NUMERICAL_RECIPE_AND_COVERAGE_ADMISSION_SEPARATE"
                or self.selected_model is not None or type(self.whole_time_certified) is not bool or self.whole_time_certified
                or type(self.physical_qualification) is not bool or self.physical_qualification
                or type(self.fresh_physical_units) is not int or self.fresh_physical_units != 0):
            raise ValueError("complete state census omits outcomes or creates later-use admission")
        stock = {_identity(row, "conclusion_id"): row for row in self.conclusions}
        if any(row.original_conclusion not in stock or stock[row.original_conclusion].configurations != row.actual_configurations
               for row in self.selected_uses):
            raise ValueError("complete state census substitutes an actual paired conclusion")
        for row in (*self.conclusions, *self.selected_uses):
            row.__post_init__()
        expected_reasons = tuple(sorted({code for row in self.conclusions for code in row.reason_codes}))
        expected_disposition = A.FALSIFIED if any(row.disposition is A.FALSIFIED for row in self.conclusions) else A.UNEVALUABLE if expected_reasons else A.SATISFIED
        if (set(stock) != {row.original_conclusion for row in self.selected_uses}
                or len({row.control for row in self.conclusions}) != 1
                or self.reason_codes != expected_reasons or self.disposition is not expected_disposition):
            raise ValueError("complete state census hides an original control or adverse outcome")
        if self.disposition is A.SATISFIED and (self.reason_codes or any(row.disposition is not A.SATISFIED for row in self.conclusions)):
            raise ValueError("complete state census promotes a negative or unevaluable original")


def join_complete_full_state(receiver_fidelity, conclusions):
    """Join exact full roster identities, with explicit original equal-condition uses."""
    if (type(receiver_fidelity) is not qualification.SegmentedFidelityQualification
            or receiver_fidelity != qualification.qualify_fidelity(receiver_fidelity.method_qualifications, receiver_fidelity.fidelity_comparisons)):
        raise ValueError("complete state census needs the exact recomputed full receiver denominator")
    rows = tuple(conclusions)
    if len(rows) != 96 or any(type(row) is not FullStateConclusion for row in rows):
        raise ValueError("complete state census needs all ninety-six distinct original paired controls")
    stock = {row.configurations: row for row in rows}
    if len(stock) != 96 or len({row.control for row in rows}) != 1:
        raise ValueError("complete state census duplicates an original paired control")
    products, uses = receiver_fidelity.method_qualifications, []
    for left_product, right_product in zip(products, products[1:]):
        for left, right in zip(left_product.summaries, right_product.summaries, strict=True):
            actual = tuple(row.configuration if row.condition_reuse is None else row.condition_reuse.observed_configuration for row in (left, right))
            key = tuple(_identity(row, "config_id") for row in actual)
            conclusion = stock.get(key)
            if conclusion is None or conclusion.traces != (left.trace, right.trace):
                raise ValueError("complete state census omits selected actual source/trace operands")
            conclusion.__post_init__()
            uses.append(FullStateSelectedUse(tuple(_identity(row.configuration, "config_id") for row in (left, right)), key,
                _identity(conclusion, "conclusion_id"), tuple(_identity(row.condition_reuse, "reuse_id") for row in (left, right) if row.condition_reuse is not None)))
    if set(stock) != {row.actual_configurations for row in uses}:
        raise ValueError("complete state census adds an unselected actual control")
    reasons = {code for row in rows for code in row.reason_codes}
    disposition = A.FALSIFIED if any(row.disposition is A.FALSIFIED for row in rows) else A.UNEVALUABLE if reasons else A.SATISFIED
    ordered = tuple(stock[key] for key in sorted(stock, key=lambda values: tuple(row.object_id for row in values)))
    return CompleteFullStateCensus("census." + receiver_fidelity.product_id, _identity(receiver_fidelity, "product_id"),
        ordered, tuple(uses), disposition, tuple(sorted(reasons)))
