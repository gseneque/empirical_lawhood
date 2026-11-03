# SPDX-License-Identifier: MPL-2.0
"""Portable references to assessed products; manifests confer no authority."""

from dataclasses import dataclass
from typing import ClassVar

from .evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from .provenance import ObjectIdentity
from .references import ArtifactIdentity
from .recursive_requirements import ContributionRole, ScientificConditionScope, ScientificRequirementSpec
from .serialization import CanonicalRecord, require_sorted_unique_ids, validate_nonempty, validate_stable_id


@dataclass(frozen=True, slots=True)
class ContributionProduct(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/kernel/contribution-product"
    product_id: str
    record: ObjectIdentity
    artifact: ArtifactIdentity
    producing_receipt: ObjectIdentity
    role: ContributionRole
    evidence_ceiling: EvidenceCeiling
    outcome_access: OutcomeAccess
    visibility_ceiling: VisibilityCeiling

    def __post_init__(self) -> None:
        validate_stable_id(self.product_id, field_name="product_id")
        if self.record.object_schema != self.artifact.payload_schema or self.record.object_fingerprint != self.artifact.sha256:
            raise ValueError("contribution product changes its exact scientific bytes")
        if not isinstance(self.role, ContributionRole):
            raise ValueError("contribution role must be typed")
        if self.outcome_access in {OutcomeAccess.DEVELOPMENT_VISIBLE, OutcomeAccess.PRIVILEGED_TRUTH} and self.evidence_ceiling is not EvidenceCeiling.NON_PROMOTABLE:
            raise ValueError("exposed development or oracle evidence is non-promotable")
        if self.role is ContributionRole.QUALIFIED_EVIDENTIAL_PARENT and self.evidence_ceiling is EvidenceCeiling.NON_PROMOTABLE:
            raise ValueError("non-promotable evidence cannot be a qualified evidential parent")


@dataclass(frozen=True, slots=True)
class ContributionManifest(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/kernel/contribution-manifest"
    contribution_id: str
    scientific_question: str
    finding: str
    scope: ScientificConditionScope
    products: tuple[ContributionProduct, ...]
    assessments: tuple[ObjectIdentity, ...]
    remaining_requirements: tuple[ScientificRequirementSpec, ...]
    predecessors: tuple[ObjectIdentity, ...] = ()

    def __post_init__(self) -> None:
        validate_stable_id(self.contribution_id, field_name="contribution_id")
        validate_nonempty(self.scientific_question, field_name="scientific_question")
        validate_nonempty(self.finding, field_name="finding")
        require_sorted_unique_ids(self.products, attribute="product_id", field_name="products")
        require_sorted_unique_ids(self.assessments, attribute="object_id", field_name="assessments")
        require_sorted_unique_ids(self.remaining_requirements, attribute="requirement_id", field_name="remaining_requirements")
        require_sorted_unique_ids(self.predecessors, attribute="object_id", field_name="predecessors")
        if not self.products or not self.assessments:
            raise ValueError("contribution requires actual products and separate assessments")
