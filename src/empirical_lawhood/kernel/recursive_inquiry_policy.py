# SPDX-License-Identifier: MPL-2.0
"""Target-directed inquiry records, without planning or execution authority.

The version-two inquiry specification composes the existing scientific records.
An assessment is evidence for its declared scope; it is never inferred from a
policy value, a successful component, or an operational completion alone.
"""

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import ClassVar

from .authority import AuthorityAction
from .evidence import ClaimSpec
from .provenance import ObjectIdentity
from .recursive_inquiry import (
    InquiryCost, InquiryDecision, InquiryOutcomeChoice, InquirySpecification, InquiryState, _ids,
)
from .recursive_requirements import (
    AssessmentDisposition,
    AssessmentPhase,
    ContributionRole,
    RequirementSupplyAssessment,
    ScientificConditionScope,
    ScientificConnectionSpec,
    ScientificRequirementSpec,
)
from .serialization import (
    CanonicalRecord,
    require_sorted_unique_strings,
    validate_decimal,
    validate_nonempty,
    validate_stable_id,
)
from .time import InformationCutoff


class InquiryQuestionKind(StrEnum):
    DISCRIMINATE = "DISCRIMINATE"
    ADOPT = "ADOPT"
    SUPPLY = "SUPPLY"
    ASSESS = "ASSESS"
    REFINE = "REFINE"


class ScientificOutcomeKind(StrEnum):
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    UNEVALUABLE = "UNEVALUABLE"
    MISSING = "MISSING"
    OPERATIONAL_FAILURE = "OPERATIONAL_FAILURE"
    UNCERTAIN_CONTACT = "UNCERTAIN_CONTACT"


class InquiryStopScope(StrEnum):
    QUESTION = "QUESTION"
    BRANCH = "BRANCH"
    TARGET = "TARGET"


@dataclass(frozen=True, slots=True)
class InquiryTarget(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/kernel/inquiry-target"
    target_id: str
    purpose: str
    scope: ScientificConditionScope
    required_requirement_ids: tuple[str, ...]
    required_claims: tuple[ObjectIdentity, ...]
    success_condition: str

    def __post_init__(self):
        validate_stable_id(self.target_id)
        validate_nonempty(self.purpose, field_name="purpose")
        validate_nonempty(self.success_condition, field_name="success_condition")
        self.scope.__post_init__()
        require_sorted_unique_strings(
            self.required_requirement_ids,
            field_name="required_requirement_ids",
            allow_empty=False,
        )
        _ids(self.required_claims, "object_id", "required_claims")
        if not self.required_claims or any(
            claim.object_schema != ClaimSpec.SCHEMA for claim in self.required_claims
        ):
            raise ValueError("target needs its complete required scientific claim census")


@dataclass(frozen=True, slots=True)
class InquiryOutcomeMap(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/kernel/inquiry-outcome-map"
    outcome_id: str
    kind: ScientificOutcomeKind
    alternative_ids: tuple[str, ...]
    consequence: str
    expected_next_evidence: str

    def __post_init__(self):
        validate_stable_id(self.outcome_id)
        if not isinstance(self.kind, ScientificOutcomeKind):
            raise ValueError("scientific and operational outcomes must be typed")
        require_sorted_unique_strings(
            self.alternative_ids, field_name="alternative_ids", allow_empty=False
        )
        for field in ("consequence", "expected_next_evidence"):
            validate_nonempty(getattr(self, field), field_name=field)


@dataclass(frozen=True, slots=True)
class RobustInquirySpecification(CanonicalRecord):
    SCHEMA: ClassVar[str] = InquirySpecification.SCHEMA
    VERSION: ClassVar[str] = "2.0.0"
    specification_id: str
    question: str
    explanations: tuple[str, ...]
    distinguishing_assessment: ObjectIdentity
    endpoint: ScientificConditionScope
    receiver_risk: str
    question_kind: InquiryQuestionKind
    target: InquiryTarget
    requirements: tuple[ScientificRequirementSpec, ...]
    connections: tuple[ScientificConnectionSpec, ...]
    question_requirement_id: str
    outcomes: tuple[InquiryOutcomeMap, ...]
    required_decision_action: AuthorityAction
    predecessor_specification: ObjectIdentity | None = None

    def __post_init__(self):
        validate_stable_id(self.specification_id)
        validate_stable_id(self.question_requirement_id)
        for field in ("question", "receiver_risk"):
            validate_nonempty(getattr(self, field), field_name=field)
        if not isinstance(self.question_kind, InquiryQuestionKind):
            raise ValueError("question semantics must be typed")
        if not isinstance(self.required_decision_action, AuthorityAction):
            raise ValueError("required decision action must be typed")
        if self.question_kind is InquiryQuestionKind.DISCRIMINATE:
            if len(self.explanations) < 2 or len(set(self.explanations)) != len(
                self.explanations
            ):
                raise ValueError("discrimination needs actual distinct explanations")
        elif self.explanations:
            raise ValueError("routine supply/use cannot invent competing explanations")
        for value in self.explanations:
            validate_nonempty(value, field_name="explanations")
        self.target.__post_init__()
        self.endpoint.__post_init__()
        for values, attribute, field in (
            (self.requirements, "requirement_id", "requirements"),
            (self.connections, "connection_id", "connections"),
            (self.outcomes, "outcome_id", "outcomes"),
        ):
            _ids(values, attribute, field)
            for value in values:
                value.__post_init__()
        requirements = {row.requirement_id: row for row in self.requirements}
        if not set((*self.target.required_requirement_ids, self.question_requirement_id)) <= requirements.keys():
            raise ValueError("inquiry omits a target/question scientific requirement")
        if any(row.scope is None for row in self.requirements):
            raise ValueError("every inquiry requirement needs its exact scientific scope")
        if requirements[self.question_requirement_id].scope != self.endpoint:
            raise ValueError("question endpoint differs from its exact requirement")
        reachable = set(self.target.required_requirement_ids)
        pending = list(reachable)
        while pending:
            requirement = requirements[pending.pop()]
            for prerequisite in requirement.further_requirement_ids:
                if prerequisite not in requirements:
                    raise ValueError("target prerequisite has no declared scientific requirement")
                if prerequisite not in reachable:
                    reachable.add(prerequisite)
                    pending.append(prerequisite)
        if requirements.keys() != reachable:
            raise ValueError("inquiry requirement is disconnected from the declared target frontier")
        if {row.kind for row in self.outcomes} != set(ScientificOutcomeKind):
            raise ValueError("frozen outcome map omits adverse/missing/operational cases")
        for connection in self.connections:
            requirement = requirements.get(connection.requirement_id)
            if requirement is None or connection.evidence_role not in requirement.permitted_roles:
                raise ValueError("connection changes its scientific requirement/evidence role")
            if requirement.assessment_operation_id != connection.assessment_operation_id:
                raise ValueError("connection changes the independent assessment operation")

    @property
    def outcome_choices(self):
        """The historical map interface, without rewriting version-one records."""
        return tuple(
            InquiryOutcomeChoice(row.outcome_id, row.alternative_ids)
            for row in self.outcomes
        )

    @property
    def required_requirement_closure(self):
        """Exact transitive scientific prerequisites of the declared target."""
        requirements = {row.requirement_id: row for row in self.requirements}
        reachable = set(self.target.required_requirement_ids)
        pending = list(reachable)
        while pending:
            for key in requirements[pending.pop()].further_requirement_ids:
                if key not in reachable:
                    reachable.add(key)
                    pending.append(key)
        return tuple(sorted(reachable))


@dataclass(frozen=True, slots=True)
class InquiryObservation(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/kernel/inquiry-observation"
    observation_id: str
    specification: ObjectIdentity
    outcome_id: str
    kind: ScientificOutcomeKind
    assessment_contract: ObjectIdentity
    assessment: ObjectIdentity | None
    evidence_ids: tuple[str, ...]
    attempt_ids: tuple[str, ...]
    scope: ScientificConditionScope
    information_cutoff: InformationCutoff
    reason: str

    def __post_init__(self):
        for field in ("observation_id", "outcome_id"):
            validate_stable_id(getattr(self, field))
        validate_nonempty(self.reason, field_name="reason")
        for field in ("evidence_ids", "attempt_ids"):
            require_sorted_unique_strings(getattr(self, field), field_name=field)
        if not isinstance(self.kind, ScientificOutcomeKind):
            raise ValueError("observation kind must be typed")
        scientific = self.kind in {
            ScientificOutcomeKind.POSITIVE,
            ScientificOutcomeKind.NEGATIVE,
            ScientificOutcomeKind.UNEVALUABLE,
        }
        if scientific and (self.assessment is None or not self.evidence_ids):
            raise ValueError("scientific outcome needs an actual assessed evidence witness")
        if not scientific and self.assessment is not None:
            raise ValueError("missing/operational work cannot manufacture scientific assessment")
        if self.kind in {
            ScientificOutcomeKind.OPERATIONAL_FAILURE,
            ScientificOutcomeKind.UNCERTAIN_CONTACT,
        } and not self.attempt_ids:
            raise ValueError("operational outcome needs retained actual attempt witnesses")


@dataclass(frozen=True, slots=True)
class InquiryRequirementFinding(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/kernel/inquiry-requirement-finding"
    requirement: ObjectIdentity
    connection: ObjectIdentity | None
    assessments: tuple[RequirementSupplyAssessment, ...]

    def __post_init__(self):
        if self.requirement.object_schema != ScientificRequirementSpec.SCHEMA:
            raise ValueError("finding requires an exact scientific requirement")
        _ids(self.assessments, "assessment_id", "assessments")
        if self.assessments and self.connection is None:
            raise ValueError("supply finding requires the actual assessed connection")
        if len({row.phase for row in self.assessments}) != len(self.assessments):
            raise ValueError("finding duplicates a scientific supply phase")
        if len({row.instance_id for row in self.assessments}) > 1:
            raise ValueError("supply phases cannot join different actual instances")
        for row in self.assessments:
            row.__post_init__()
            if row.requirement != self.requirement or row.connection != self.connection:
                raise ValueError("finding substitutes an assessed requirement/connection")

    @property
    def supplied(self):
        return {row.phase for row in self.assessments} == set(AssessmentPhase) and all(
            row.disposition is AssessmentDisposition.SATISFIED for row in self.assessments
        )


@dataclass(frozen=True, slots=True)
class InquiryClaimFinding(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/kernel/inquiry-claim-finding"
    claim: ObjectIdentity
    scope: ScientificConditionScope
    disposition: AssessmentDisposition
    assessment: ObjectIdentity | None
    evidence_ids: tuple[str, ...]
    reason: str

    def __post_init__(self):
        if self.claim.object_schema != ClaimSpec.SCHEMA:
            raise ValueError("claim finding needs its exact scientific claim")
        if not isinstance(self.disposition, AssessmentDisposition):
            raise ValueError("claim disposition must be typed")
        require_sorted_unique_strings(self.evidence_ids, field_name="evidence_ids")
        validate_nonempty(self.reason, field_name="reason")
        if self.disposition is not AssessmentDisposition.NOT_ATTEMPTED and (
            self.assessment is None or not self.evidence_ids
        ):
            raise ValueError("assessed target claim needs actual independent assessment")


@dataclass(frozen=True, slots=True)
class ScientificInquiryWork(CanonicalRecord):
    """Scientific identity excludes invocation/seed labels and operational paths."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/kernel/scientific-inquiry-work"
    method: ObjectIdentity
    scientific_operands: tuple[ObjectIdentity, ...]
    scope: ScientificConditionScope
    observation_contract: ObjectIdentity

    def __post_init__(self):
        _ids(self.scientific_operands, "object_id", "scientific_operands")
        if not self.scientific_operands:
            raise ValueError("work needs its complete source-bound scientific operands")


@dataclass(frozen=True, slots=True)
class InquiryAttemptWorkBinding(CanonicalRecord):
    """Actual configuration and custody witnesses for one scientific work identity.

    Missing domain semantics stay unknown. They cannot authorize a differently
    labelled replay of an uncertain attempt.
    """
    SCHEMA: ClassVar[str] = "empirical-lawhood/kernel/inquiry-attempt-work-binding"
    attempt_id: str
    configuration: ObjectIdentity
    work: ScientificInquiryWork | None
    authored_wave: ObjectIdentity | None
    execution_plan: ObjectIdentity | None
    execution_task: ObjectIdentity | None
    witness: ObjectIdentity

    def __post_init__(self):
        validate_stable_id(self.attempt_id)
        for record, schema in ((self.authored_wave, "empirical-lawhood/runtime/authored-recursive-wave"),
                               (self.execution_plan, "empirical-lawhood/runtime/development-execution-plan"),
                               (self.execution_task, "empirical-lawhood/runtime/execution-task")):
            if record is not None and record.object_schema != schema:
                raise ValueError("scientific work binding substitutes its custody witness type")
        if self.work is not None:
            self.work.__post_init__()
            if any(record is None for record in (self.authored_wave, self.execution_plan, self.execution_task)):
                raise ValueError("known scientific work requires its actual wave/plan/task witnesses")


@dataclass(frozen=True, slots=True, kw_only=True)
class WorkBoundInquiryState(InquiryState):
    """Additive current state; historical version-one state bytes are unchanged."""
    VERSION: ClassVar[str] = "2.0.0"
    attempt_work_bindings: tuple[InquiryAttemptWorkBinding, ...]

    def __post_init__(self):
        InquiryState.__post_init__(self)
        _ids(self.attempt_work_bindings, "attempt_id", "attempt_work_bindings")
        attempts = {row.attempt_id: row for row in self.operational_census}
        if {row.attempt_id for row in self.attempt_work_bindings} != attempts.keys():
            raise ValueError("scientific work binding omits the complete attempt denominator")
        for binding in self.attempt_work_bindings:
            binding.__post_init__()
            attempt = attempts[binding.attempt_id]
            if binding.configuration != attempt.operation or binding.witness != attempt.receipt:
                raise ValueError("scientific work binding changes actual configuration/attempt witness")


@dataclass(frozen=True, slots=True)
class CompletedInquiryWork(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/kernel/completed-inquiry-work"
    completion_id: str
    work: ScientificInquiryWork
    attempt_id: str
    receipt: ObjectIdentity
    products: tuple[ObjectIdentity, ...]

    def __post_init__(self):
        validate_stable_id(self.completion_id)
        validate_stable_id(self.attempt_id)
        _ids(self.products, "object_id", "products")
        if not self.products:
            raise ValueError("completion needs authenticated actual products")


@dataclass(frozen=True, slots=True)
class InquiryTargetFrontier(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/kernel/inquiry-target-frontier"
    frontier_id: str
    target: ObjectIdentity
    requirement_findings: tuple[InquiryRequirementFinding, ...]
    claim_findings: tuple[InquiryClaimFinding, ...]
    completed_work: tuple[CompletedInquiryWork, ...]

    def __post_init__(self):
        validate_stable_id(self.frontier_id)
        if self.target.object_schema != InquiryTarget.SCHEMA:
            raise ValueError("frontier requires the immutable overarching target")
        if tuple(row.requirement.object_id for row in self.requirement_findings) != tuple(
            sorted({row.requirement.object_id for row in self.requirement_findings})
        ):
            raise ValueError("frontier requirement census repeats or reorders identities")
        if tuple(row.claim.object_id for row in self.claim_findings) != tuple(
            sorted({row.claim.object_id for row in self.claim_findings})
        ):
            raise ValueError("frontier claim census repeats or reorders identities")
        _ids(self.completed_work, "completion_id", "completed_work")


@dataclass(frozen=True, slots=True)
class InquiryEvidenceNeed(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/kernel/inquiry-evidence-need"
    evidence_id: str
    product: ObjectIdentity
    scope: ScientificConditionScope
    role: ContributionRole
    compatibility_assessment: ObjectIdentity | None = None

    def __post_init__(self):
        validate_stable_id(self.evidence_id)
        if not isinstance(self.role, ContributionRole):
            raise ValueError("scientific evidence role must be typed")


@dataclass(frozen=True, slots=True)
class InquiryCriterionAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/kernel/inquiry-criterion-assessment"
    criterion_id: str
    lower: Decimal | None
    upper: Decimal | None
    unit: str
    evidence_ids: tuple[str, ...]
    assumption_ids: tuple[str, ...]
    rationale: str

    def __post_init__(self):
        validate_stable_id(self.criterion_id)
        for field in ("unit", "rationale"):
            validate_nonempty(getattr(self, field), field_name=field)
        for field in ("evidence_ids", "assumption_ids"):
            require_sorted_unique_strings(getattr(self, field), field_name=field)
        if (self.lower is None) != (self.upper is None):
            raise ValueError("unknown criterion requires both bounds unknown")
        if self.lower is not None:
            validate_decimal(self.lower, field_name="lower")
            validate_decimal(self.upper, field_name="upper")
            if self.lower > self.upper:
                raise ValueError("criterion interval is reversed")
            if not self.evidence_ids and not self.assumption_ids:
                raise ValueError("known interval needs evidence or declared assumptions")


@dataclass(frozen=True, slots=True)
class InquiryPolicyAssumption(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/kernel/inquiry-policy-assumption"
    assumption_id: str
    proposition: str
    evidence_ids: tuple[str, ...]
    reason: str

    def __post_init__(self):
        validate_stable_id(self.assumption_id)
        for field in ("proposition", "reason"):
            validate_nonempty(getattr(self, field), field_name=field)
        require_sorted_unique_strings(self.evidence_ids, field_name="evidence_ids")


class RobustChoiceStatus(StrEnum):
    INELIGIBLE = "INELIGIBLE"
    DOMINATED = "DOMINATED"
    MAXIMAL = "MAXIMAL"
    INCOMPARABLE = "INCOMPARABLE"
    AVAILABLE = "AVAILABLE"


@dataclass(frozen=True, slots=True)
class RobustChoiceEvaluation(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/kernel/inquiry-choice-evaluation"
    VERSION: ClassVar[str] = "2.0.0"
    alternative_id: str
    eligible: bool
    reason_codes: tuple[str, ...]
    status: RobustChoiceStatus
    dominated_by: tuple[str, ...]
    incomparable_with: tuple[str, ...]
    evidence_that_changes_disposition: str

    def __post_init__(self):
        validate_stable_id(self.alternative_id)
        if type(self.eligible) is not bool or not isinstance(self.status, RobustChoiceStatus):
            raise ValueError("choice disposition must be typed")
        for field in ("reason_codes", "dominated_by", "incomparable_with"):
            require_sorted_unique_strings(getattr(self, field), field_name=field)
        if self.eligible != (self.status is not RobustChoiceStatus.INELIGIBLE):
            raise ValueError("choice eligibility and disposition differ")
        validate_nonempty(self.evidence_that_changes_disposition, field_name="evidence_that_changes_disposition")


@dataclass(frozen=True, slots=True)
class RobustInquiryDecision(CanonicalRecord):
    SCHEMA: ClassVar[str] = InquiryDecision.SCHEMA
    VERSION: ClassVar[str] = "2.0.0"
    decision_id: str
    specification: ObjectIdentity
    state: ObjectIdentity
    menu: ObjectIdentity
    policy: ObjectIdentity
    selected_alternative_id: str
    actor_id: str
    decision_right: ObjectIdentity
    campaign: ObjectIdentity
    human_directed: bool
    outcome_id: str
    evaluations: tuple[RobustChoiceEvaluation, ...]
    remaining_cost: InquiryCost
    target: ObjectIdentity
    frontier: ObjectIdentity
    supplied_requirement_ids: tuple[str, ...]
    unresolved_target_requirement_ids: tuple[str, ...]
    unresolved_target_claim_ids: tuple[str, ...]
    next_enabled_capability: str
    expected_next_evidence: str
    reason: str
    human_reason: str | None = None
    stop_scope: InquiryStopScope | None = None
    unentered_requirement_ids: tuple[str, ...] = ()

    def __post_init__(self):
        for field in ("decision_id", "selected_alternative_id", "actor_id", "outcome_id"):
            validate_stable_id(getattr(self, field))
        if type(self.human_directed) is not bool:
            raise ValueError("human direction must be attributable")
        if self.human_directed != (self.human_reason is not None):
            raise ValueError("human choice requires its actual reason")
        for field in ("reason", "next_enabled_capability", "expected_next_evidence"):
            validate_nonempty(getattr(self, field), field_name=field)
        if self.human_reason is not None:
            validate_nonempty(self.human_reason, field_name="human_reason")
        for field in (
            "supplied_requirement_ids", "unresolved_target_requirement_ids", "unresolved_target_claim_ids",
            "unentered_requirement_ids",
        ):
            require_sorted_unique_strings(getattr(self, field), field_name=field)
        if self.stop_scope is not None and not isinstance(self.stop_scope, InquiryStopScope):
            raise ValueError("terminal scope must remain explicit")
        _ids(self.evaluations, "alternative_id", "evaluations")


@dataclass(frozen=True, slots=True)
class WorkBoundInquiryDecision(RobustInquiryDecision):
    """Current work-bound policy decision; original version-two bytes remain closed."""
    VERSION: ClassVar[str] = "3.0.0"


