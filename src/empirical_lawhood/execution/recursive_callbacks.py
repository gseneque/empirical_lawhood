# SPDX-License-Identifier: MPL-2.0
"""Named scientific and inquiry callbacks at the existing compiler/API seams.

Scientific interpretation belongs to the registered owner. Canonical records,
closed units, original receipts and independent status axes keep their existing
contracts. A callback annotation supplies no scientific or access authority.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, TypeVar

if TYPE_CHECKING:
    from collections.abc import Mapping
    from contextlib import AbstractContextManager

    from empirical_lawhood.science.evidence.evidence import ClaimSpec
    from empirical_lawhood.science.identity.numerical_provenance import NumericalProducingProvenance
    from empirical_lawhood.science.identity.provenance import ObjectIdentity
    from empirical_lawhood.science.inquiry.recursive_claim_assessment import InquiryClaimAssessment
    from empirical_lawhood.science.inquiry.recursive_inquiry import InquirySpecification
    from empirical_lawhood.science.inquiry.recursive_inquiry_policy import RobustInquirySpecification, ScientificInquiryWork
    from empirical_lawhood.science.inquiry.recursive_requirements import RequirementSupplyAssessment, ScientificConditionScope, ScientificConnectionSpec, ScientificRequirementSpec
    from empirical_lawhood.science.inquiry.scientific_contributions import ContributionManifest, ContributionProduct
    from empirical_lawhood.science.records.serialization import CanonicalRecord
    from empirical_lawhood.design.recursive_authoring import RecursiveStudyDraft
    from empirical_lawhood.storage.contracts.artifacts import ArtifactLineageParent, ArtifactWriter
    from empirical_lawhood.execution.execution import ParentPreparedTaskRunner, TaskContext, TaskRunner
    from empirical_lawhood.execution.native_effects import NativeEffectContact
    from empirical_lawhood.execution.plans import ExecutionPlan
    from empirical_lawhood.execution.prepared_native_invocation import PreparedNativeWork
    from empirical_lawhood.execution.recursive_compiler import RecursiveConfigInput, RecursiveScientificRootContext, RecursiveScientificRootPreparationContext
    from empirical_lawhood.execution.recursive_inquiry import InquiryEvidenceBinding
    from empirical_lawhood.execution.recursive_provider import RecursiveInputSupplier
    from empirical_lawhood.execution.recursive_qualified_parents import QualifiedParentEvidence, RecursivePriorExecutionBinding


class RequirementAssessmentProjector(Protocol):
    def __call__(self, record: CanonicalRecord, requirement: ScientificRequirementSpec,
                 connection: ScientificConnectionSpec) -> tuple[RequirementSupplyAssessment, ...]: ...


class ScientificIdentityProjector(Protocol):
    """Sorted unique string identities; the owning field selects ID or SHA grammar."""

    def __call__(self, config: CanonicalRecord) -> tuple[str, ...]: ...


class ScientificRootValidator(Protocol):
    def __call__(self, config: CanonicalRecord, context: RecursiveScientificRootContext) -> None: ...


class ScientificClaimResolver(Protocol):
    def __call__(self, config: CanonicalRecord, context: RecursiveScientificRootContext,
                 requirement: ScientificRequirementSpec, connection: ScientificConnectionSpec) -> ClaimSpec: ...


PreparationT_co = TypeVar("PreparationT_co", covariant=True)


class ScientificRootPreparer(Protocol[PreparationT_co]):
    """One domain-owned non-None immutable object, scoped to one compilation."""

    def __call__(self, context: RecursiveScientificRootPreparationContext) -> PreparationT_co: ...


class QualifiedParentAssessor(Protocol):
    def __call__(self, *, requirement: ScientificRequirementSpec, connection: ScientificConnectionSpec,
                 contribution: ContributionManifest, product: ContributionProduct,
                 parent_evidence: QualifiedParentEvidence) -> None: ...


class PriorExecutionProjector(Protocol):
    def __call__(self, parent_evidence: QualifiedParentEvidence) -> tuple[RecursivePriorExecutionBinding, ...]: ...


class PriorExecutionScopeValidator(Protocol):
    def __call__(self, *, parent_evidence: QualifiedParentEvidence, binding: RecursivePriorExecutionBinding,
                 package: CanonicalRecord, execution_plan: ExecutionPlan) -> None: ...


class ContributionDescriber(Protocol):
    def __call__(self, draft: RecursiveStudyDraft, products: Mapping[str, object]) -> tuple[ContributionManifest, ...]: ...


class NextWaveBuilder(Protocol):
    def __call__(self, draft: RecursiveStudyDraft, contribution: ContributionManifest,
                 products: Mapping[str, object]) -> RecursiveStudyDraft | None: ...


class InquiryOutcomeProjector(Protocol):
    def __call__(self, draft: RecursiveStudyDraft, specification: InquirySpecification | RobustInquirySpecification,
                 products: Mapping[str, object]) -> str: ...


class InquiryEvidenceProjector(Protocol):
    def __call__(self, draft: RecursiveStudyDraft, payloads: Mapping[str, bytes],
                 products: Mapping[str, object] | None) -> tuple[InquiryEvidenceBinding, ...]: ...


class InquiryEndpointValidator(Protocol):
    def __call__(self, draft: RecursiveStudyDraft, endpoint: ScientificConditionScope) -> None: ...


class InquiryEndpointProjector(Protocol):
    """Return the exact original endpoint accepted by the matching validator."""

    def __call__(self, draft: RecursiveStudyDraft) -> ScientificConditionScope: ...


class InquirySelectionScope(Protocol):
    """Prepare immutable domain operands for one synchronous projection only."""

    def __call__(self, draft: RecursiveStudyDraft) -> AbstractContextManager[object]: ...


class InquiryRecordIdentity(Protocol):
    def __call__(self, record: CanonicalRecord) -> ObjectIdentity: ...


class InquiryWorkProjector(Protocol):
    def __call__(self, draft: RecursiveStudyDraft, task_id: str) -> ScientificInquiryWork: ...


class InquiryWorkBatchProjector(Protocol):
    """Validate one complete draft and return work for the exact selected tasks."""

    def __call__(self, draft: RecursiveStudyDraft,
                 task_ids: tuple[str, ...]) -> tuple[tuple[str, ScientificInquiryWork], ...]: ...


class InquiryClaimAssessmentProjector(Protocol):
    def __call__(self, draft: RecursiveStudyDraft, specification: RobustInquirySpecification,
                 products: Mapping[str, object]) -> tuple[InquiryClaimAssessment, ...]: ...


class NativeWorkPreparer(Protocol):
    def __call__(self, *, runner: TaskRunner, context: TaskContext,
                 expected_parent: NativeEffectContact) -> PreparedNativeWork: ...


class WorkerEnvironmentSelector(Protocol):
    def __call__(self, settings: Mapping[str, str]) -> Mapping[str, str]: ...


class RunnerPreparationFactory(Protocol):
    def __call__(self, supplier: RecursiveInputSupplier, runner: TaskRunner) -> ParentPreparedTaskRunner: ...


class ConfigInputParents(Protocol):
    def __call__(self, config: CanonicalRecord,
                 all_configs: tuple[tuple[str, CanonicalRecord], ...]) -> tuple[ArtifactLineageParent, ...]: ...


class PublicationValidator(Protocol):
    def __call__(self, writer: ArtifactWriter, configs: tuple[RecursiveConfigInput, ...]) -> None: ...


class NumericalProvenanceValidator(Protocol):
    def __call__(self, provenance: NumericalProducingProvenance) -> None: ...
