# SPDX-License-Identifier: MPL-2.0
"""Scientific requirements and assessed connections, separate from execution authority."""

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import ClassVar

from .authority import ResourceBudget
from .evidence import ClaimSpec, EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from .provenance import ObjectIdentity
from .serialization import (
    CanonicalRecord, require_sorted_unique_ids, require_sorted_unique_strings,
    validate_decimal, validate_nonempty, validate_sha256, validate_stable_id,
)
from .time import InformationCutoff
from .worlds import WorldKind


class ConditionRole(StrEnum):
    PHYSICAL = "PHYSICAL"
    INFORMATIONAL = "INFORMATIONAL"
    EVIDENTIAL = "EVIDENTIAL"
    TASK = "TASK"


class ContributionRole(StrEnum):
    DESIGN_OPERAND = "DESIGN_OPERAND"
    QUALIFIED_EVIDENTIAL_PARENT = "QUALIFIED_EVIDENTIAL_PARENT"
    RETAINED_ANALYSIS_INPUT = "RETAINED_ANALYSIS_INPUT"
    INSTANCE_PRODUCT = "INSTANCE_PRODUCT"


@dataclass(frozen=True, slots=True)
class ScientificConditionScope(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/kernel/scientific-condition-scope"
    system_id: str
    world_id: str
    source_id: str
    quantity_ids: tuple[str, ...]
    native_units: tuple[str, ...]
    receiver_id: str
    clock_id: str
    coordinate_meaning: str
    source_config_sha256: str | None = None
    instance_id: str | None = None
    population_id: str | None = None
    information_cutoff: InformationCutoff | None = None
    available_by: Decimal | None = None
    valid_from: Decimal | None = None
    valid_until: Decimal | None = None
    uncertainty_contract: ObjectIdentity | None = None

    def __post_init__(self) -> None:
        for name in ("system_id", "world_id", "source_id", "receiver_id", "clock_id"):
            validate_stable_id(getattr(self, name), field_name=name)
        require_sorted_unique_strings(self.quantity_ids, field_name="quantity_ids", allow_empty=False)
        if len(self.native_units) != len(self.quantity_ids):
            raise ValueError("each scoped quantity requires its exact native unit")
        for unit in self.native_units:
            validate_nonempty(unit, field_name="native_units")
        validate_nonempty(self.coordinate_meaning, field_name="coordinate_meaning")
        for name in ("instance_id", "population_id"):
            if getattr(self, name) is not None:
                validate_stable_id(getattr(self, name), field_name=name)
        if self.source_config_sha256 is not None:
            validate_sha256(self.source_config_sha256)
        for name in ("available_by", "valid_from", "valid_until"):
            if getattr(self, name) is not None:
                validate_decimal(getattr(self, name), field_name=name)
        if self.valid_from is not None and self.valid_until is not None and self.valid_from > self.valid_until:
            raise ValueError("condition validity interval is reversed")


@dataclass(frozen=True, slots=True)
class ScientificRequirementSpec(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/kernel/scientific-requirement-spec"
    requirement_id: str
    consumer_operation_id: str
    condition_role: ConditionRole
    purpose: str
    condition: str
    scope: ScientificConditionScope | None
    assessment_operation_id: str | None
    falsifier: str
    permitted_roles: tuple[ContributionRole, ...]
    further_requirement_ids: tuple[str, ...] = ()
    background_assumption_ids: tuple[str, ...] = ()
    resource_commitment: ResourceBudget | None = None

    def __post_init__(self) -> None:
        validate_stable_id(self.requirement_id, field_name="requirement_id")
        validate_stable_id(self.consumer_operation_id, field_name="consumer_operation_id")
        if not isinstance(self.condition_role, ConditionRole):
            raise ValueError("condition role must use its closed scientific grammar")
        for name in ("purpose", "condition", "falsifier"):
            validate_nonempty(getattr(self, name), field_name=name)
        if self.assessment_operation_id is not None:
            validate_stable_id(self.assessment_operation_id, field_name="assessment_operation_id")
        require_sorted_unique_strings(self.permitted_roles, field_name="permitted_roles", allow_empty=False)
        if any(not isinstance(role, ContributionRole) for role in self.permitted_roles):
            raise ValueError("requirement parent roles are not typed")
        for name in ("further_requirement_ids", "background_assumption_ids"):
            require_sorted_unique_strings(getattr(self, name), field_name=name)
        if self.requirement_id in self.further_requirement_ids:
            raise ValueError("requirement cannot require itself")


@dataclass(frozen=True, slots=True)
class ScientificConnectionSpec(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/kernel/scientific-connection-spec"
    connection_id: str
    requirement_id: str
    supplier_operation_id: str | None
    supplier_output_id: str | None
    consumer_input_id: str
    assessment_operation_id: str
    claim_id: str
    evidence_role: ContributionRole
    falsifier: str
    supplier_contribution: ObjectIdentity | None = None
    supplier_product_id: str | None = None
    external_input_id: str | None = None

    def __post_init__(self) -> None:
        for name in ("connection_id", "requirement_id", "consumer_input_id", "assessment_operation_id", "claim_id"):
            validate_stable_id(getattr(self, name), field_name=name)
        internal = self.supplier_operation_id is not None or self.supplier_output_id is not None
        external = self.supplier_contribution is not None or self.supplier_product_id is not None or self.external_input_id is not None
        if internal == external:
            raise ValueError("assessed connection requires exactly one internal or contribution supplier")
        if internal:
            if self.supplier_operation_id is None or self.supplier_output_id is None:
                raise ValueError("internal supplier requires its complete operation and output")
            validate_stable_id(self.supplier_operation_id, field_name="supplier_operation_id")
            validate_stable_id(self.supplier_output_id, field_name="supplier_output_id")
        else:
            if self.supplier_contribution is None or self.supplier_product_id is None or self.external_input_id is None:
                raise ValueError("external supplier requires its exact contribution, product and input")
            if self.supplier_contribution.object_schema != "empirical-lawhood/kernel/contribution-manifest":
                raise ValueError("external supplier requires a contribution manifest")
            validate_stable_id(self.supplier_product_id, field_name="supplier_product_id")
            validate_stable_id(self.external_input_id, field_name="external_input_id")
        if not isinstance(self.evidence_role, ContributionRole):
            raise ValueError("connection evidence role must be typed")
        validate_nonempty(self.falsifier, field_name="falsifier")


class AssessmentPhase(StrEnum):
    PROCEDURE = "PROCEDURE"
    INSTANCE = "INSTANCE"
    ADMISSION = "ADMISSION"
    JOINED = "JOINED"


class AssessmentDisposition(StrEnum):
    SATISFIED = "SATISFIED"
    FALSIFIED = "FALSIFIED"
    REFUSED = "REFUSED"
    UNEVALUABLE = "UNEVALUABLE"
    UNSUPPORTED = "UNSUPPORTED"
    NOT_ATTEMPTED = "NOT_ATTEMPTED"


@dataclass(frozen=True, slots=True)
class RequirementSupplyAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/kernel/requirement-supply-assessment"
    assessment_id: str
    requirement: ObjectIdentity
    connection: ObjectIdentity
    phase: AssessmentPhase
    disposition: AssessmentDisposition
    instance_id: str
    evidence: tuple[ObjectIdentity, ...]
    reason_codes: tuple[str, ...]
    evidence_ceiling: EvidenceCeiling = EvidenceCeiling.NON_PROMOTABLE
    outcome_access: OutcomeAccess = OutcomeAccess.DEVELOPMENT_VISIBLE
    visibility_ceiling: VisibilityCeiling = VisibilityCeiling.DEVELOPMENT_ONLY

    def __post_init__(self) -> None:
        validate_stable_id(self.assessment_id, field_name="assessment_id")
        validate_stable_id(self.instance_id, field_name="instance_id")
        if self.requirement.object_schema != ScientificRequirementSpec.SCHEMA or self.connection.object_schema != ScientificConnectionSpec.SCHEMA:
            raise ValueError("assessment requires exact requirement and connection identities")
        if not isinstance(self.phase, AssessmentPhase) or not isinstance(self.disposition, AssessmentDisposition):
            raise ValueError("assessment phase and disposition must be typed")
        require_sorted_unique_ids(self.evidence, attribute="object_id", field_name="evidence")
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes")
        if self.disposition is AssessmentDisposition.SATISFIED and not self.evidence:
            raise ValueError("satisfied supply assessment requires actual evidence")
        if self.disposition is not AssessmentDisposition.SATISFIED and not self.reason_codes:
            raise ValueError("negative or unevaluable assessment requires reasons")
        if self.outcome_access is OutcomeAccess.DEVELOPMENT_VISIBLE and self.evidence_ceiling is not EvidenceCeiling.NON_PROMOTABLE:
            raise ValueError("development assessments cannot grant qualification")


@dataclass(frozen=True, slots=True)
class DevelopmentStudySpec(CanonicalRecord):
    """An exposed scientific design, without prospective issue or execution authority."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/kernel/development-study-spec"
    study_id: str
    question: str
    system: ObjectIdentity
    world_id: str
    world_kind: WorldKind
    assigned_unit_ids: tuple[str, ...]
    numerical_view_ids: tuple[str, ...]
    claims: tuple[ClaimSpec, ...]
    scientific_operands: tuple[ObjectIdentity, ...]
    evidence_ceiling: EvidenceCeiling = EvidenceCeiling.NON_PROMOTABLE

    def __post_init__(self) -> None:
        validate_stable_id(self.study_id, field_name="study_id")
        validate_stable_id(self.world_id, field_name="world_id")
        validate_nonempty(self.question, field_name="question")
        if self.world_kind not in {WorldKind.ANALYTIC_REFERENCE, WorldKind.NUMERICAL_SIMULATOR}:
            raise ValueError("development studies cannot select physical or protected execution")
        require_sorted_unique_strings(self.assigned_unit_ids, field_name="assigned_unit_ids", allow_empty=False)
        require_sorted_unique_strings(self.numerical_view_ids, field_name="numerical_view_ids")
        require_sorted_unique_ids(self.claims, attribute="claim_id", field_name="claims")
        if not self.claims or self.evidence_ceiling is not EvidenceCeiling.NON_PROMOTABLE:
            raise ValueError("development study needs non-promotable scientific claims")
        for claim in self.claims:
            if (claim.world_id != self.world_id or claim.evidence_ceiling is not EvidenceCeiling.NON_PROMOTABLE
                    or claim.requested_rung is not None or claim.outcome_access not in {OutcomeAccess.DEVELOPMENT_VISIBLE, OutcomeAccess.EVALUATION_REVEALED}
                    or claim.visibility_ceiling not in {VisibilityCeiling.DEVELOPMENT_ONLY, VisibilityCeiling.OUTCOME_VISIBLE}):
                raise ValueError("development claim changes its exposed evidence boundary")
        require_sorted_unique_ids(self.scientific_operands, attribute="object_id", field_name="scientific_operands")

    @property
    def access_pair(self) -> tuple[OutcomeAccess, VisibilityCeiling]:
        """One exposed execution role, without issue or reveal authority."""
        pairs = {(claim.outcome_access, claim.visibility_ceiling) for claim in self.claims}
        allowed = {(OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY),
                   (OutcomeAccess.EVALUATION_REVEALED, VisibilityCeiling.OUTCOME_VISIBLE)}
        if len(pairs) != 1 or not pairs.issubset(allowed):
            raise ValueError("development execution requires one exact exposed claim access pair")
        return next(iter(pairs))
