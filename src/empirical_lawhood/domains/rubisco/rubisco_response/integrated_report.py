# SPDX-License-Identifier: MPL-2.0
"""Additive integrated findings; original reference reports retain their contracts."""

from dataclasses import dataclass, replace
from typing import ClassVar

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_nonempty, validate_stable_id
from empirical_lawhood.execution.experiment_preparation import DependencyKind
from empirical_lawhood.domains.rubisco.rubisco_response.comparison_assessment import ResponseComparisonAssessment
from empirical_lawhood.domains.rubisco.rubisco_response.comparison_preparation import _native_dependencies
from empirical_lawhood.domains.rubisco.rubisco_response.finding_report import CombinedMilestoneAssessment
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_preparation import MolecularPreparationCensus
from empirical_lawhood.domains.rubisco.rubisco_response.reduction_target import ReductionTargetAssessment, assess_reduction_target


@dataclass(frozen=True, slots=True)
class NativeEntryRequirement(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/reported-native-entry-requirement"
    code: str
    kind: DependencyKind
    detail: str

    def __post_init__(self):
        validate_stable_id(self.code)
        if type(self.kind) is not DependencyKind:
            raise TypeError("native entry requirement needs its exact dependency kind")
        validate_nonempty(self.detail, field_name="detail")


def _entries(comparison, molecular, target):
    return tuple(NativeEntryRequirement(row.code, row.kind, row.detail)
        for row in _native_dependencies(comparison.design, molecular, target))


def _milestone(comparison):
    reference = comparison.arms[0].report
    prefix = "requirement." + comparison.design.design_id + "."
    extra = {
        "approximation-fidelity": (prefix + "actual-native-reference-and-parity",),
        "prospective-recognition-and-service": (prefix + "original-pre-reference-causal-custody",
            prefix + "prospective-complete-service", "requirement.rubisco.comparison.indicator-and-sequential-validity"),
        "computational-benefit": (prefix + "complete-comparative-measurements", "requirement.rubisco.comparison.justified-supplier"),
        "reusable-implementation": (prefix + "accepted-native-output-binding", "requirement.rubisco.comparison.installed-settled-source-acceptance"),
        "scientific-delivery": (prefix + "complete-scientific-result",),
    }
    components = []
    for row in reference.milestone.components:
        if row.component in extra:
            # The exposed comparison's failures and successes remain in the
            # complete operand. They do not qualify a native/prospective claim.
            row = replace(row, disposition=A.UNEVALUABLE,
                evidence=tuple(sorted({*row.evidence, comparison.identity}, key=lambda value: value.object_id)),
                remaining_requirement_ids=tuple(sorted({*row.remaining_requirement_ids, *extra[row.component]})))
        components.append(row)
    return CombinedMilestoneAssessment(reference.study.acceptance.identity, tuple(components), "OPEN")


def _remaining(comparison, target, molecular, milestone, entries):
    return tuple(sorted({*comparison.remaining_requirement_ids, *target.remaining_requirement_ids,
        *(() if molecular is None else molecular.unresolved_requirement_ids),
        *(key for row in milestone.components for key in row.remaining_requirement_ids),
        *("requirement." + row.code for row in entries)}))


@dataclass(frozen=True, slots=True)
class IntegratedResponseReport(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/integrated-report"
    report_id: str
    comparison: ResponseComparisonAssessment
    target_assessment: ReductionTargetAssessment
    molecular_preparation: MolecularPreparationCensus | None
    milestone: CombinedMilestoneAssessment
    native_entry_prerequisites: tuple[NativeEntryRequirement, ...]
    remaining_requirement_ids: tuple[str, ...]
    native_entry_status: str = "NOT_READY"
    evidence_scope: str = "EXPOSED_RETAINED_INTEGRATION_NOT_NATIVE_PROSPECTIVE_OR_BIOLOGICAL_QUALIFICATION"
    new_native_calls: int = 0

    def __post_init__(self):
        validate_stable_id(self.report_id)
        exact(self.comparison, ResponseComparisonAssessment)
        if self.reference is None:
            raise ValueError("integrated reference report requires the original reference finding; missing truth remains in comparison analysis")
        exact(self.target_assessment, ReductionTargetAssessment)
        if self.target_assessment.reference_report != self.reference:
            raise ValueError("integrated report substitutes another reference or reduction target")
        if self.molecular_preparation is not None:
            exact(self.molecular_preparation, MolecularPreparationCensus)
        entries = _entries(self.comparison, self.molecular_preparation, self.target_assessment)
        if type(self.native_entry_prerequisites) is not tuple:
            raise ValueError("integrated report needs its complete immutable entry requirement census")
        for row in self.native_entry_prerequisites:
            exact(row, NativeEntryRequirement)
        if self.native_entry_prerequisites != entries:
            raise ValueError("integrated report drops an actual native entry prerequisite")
        exact(self.milestone, CombinedMilestoneAssessment)
        if self.milestone != _milestone(self.comparison):
            raise ValueError("integrated report substitutes scientific milestone findings or promotes exposed comparison")
        if self.remaining_requirement_ids != _remaining(self.comparison, self.target_assessment,
                self.molecular_preparation, self.milestone, entries):
            raise ValueError("integrated report drops a remaining scientific requirement")
        if (self.native_entry_status != "NOT_READY" or type(self.new_native_calls) is not int or self.new_native_calls != 0
                or self.evidence_scope != "EXPOSED_RETAINED_INTEGRATION_NOT_NATIVE_PROSPECTIVE_OR_BIOLOGICAL_QUALIFICATION"):
            raise ValueError("integrated report cannot grant native entry or scientific qualification")

    @property
    def reference(self):
        return self.comparison.arms[0].report

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.report_id, self)


def build_integrated_report(comparison, *, report_id, molecular_preparation=None):
    exact(comparison, ResponseComparisonAssessment)
    reference = comparison.arms[0].report
    if reference is None:
        raise ValueError("integrated reference report requires the original reference finding; use comparison analysis for missing truth")
    target = assess_reduction_target(reference, assessment_id="target." + report_id)
    entries = _entries(comparison, molecular_preparation, target)
    milestone = _milestone(comparison)
    return IntegratedResponseReport(report_id, comparison, target, molecular_preparation, milestone, entries,
        _remaining(comparison, target, molecular_preparation, milestone, entries))
