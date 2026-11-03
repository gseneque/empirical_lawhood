# SPDX-License-Identifier: MPL-2.0
"""Finite, evidenced robust inquiry ordering; no scheduler or scientific solver."""

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_inquiry import (
    InquiryAttempt,
    InquiryAttemptStatus,
    InquiryCost,
    InquiryState,
    InquirySuccessorIntent,
    _count,
    _ids,
    identity,
    summarize_cost,
    validate_inquiry_capability_id,
)
from empirical_lawhood.kernel.recursive_inquiry_policy import (
    CompletedInquiryWork,
    InquiryCriterionAssessment,
    InquiryAttemptWorkBinding,
    InquiryEvidenceNeed,
    InquiryObservation,
    InquiryPolicyAssumption,
    InquiryStopScope,
    InquiryTargetFrontier,
    RobustInquirySpecification,
    RobustInquiryDecision,
    RobustChoiceEvaluation,
    RobustChoiceStatus,
    ScientificInquiryWork,
    ScientificOutcomeKind,
    WorkBoundInquiryState,
    WorkBoundInquiryDecision,
)
from empirical_lawhood.kernel.recursive_requirements import (
    AssessmentDisposition,
    AssessmentPhase,
    ScientificConditionScope,
)
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord,
    require_sorted_unique_strings,
    validate_nonempty,
    validate_stable_id,
)
from .campaigns import CampaignSpec, DecisionRight
from .recursive_authoring import SupplierProposal, validate_selected_requirement_graph
from .recursive_inquiry import COST_FIELDS, InquiryAction, InquiryMenu, InquiryPolicy


class InquiryAlternativeKind(StrEnum):
    ACQUIRE = "ACQUIRE"
    REUSE = "REUSE"
    ADOPT = "ADOPT"
    INDEPENDENT_CHECK = "INDEPENDENT_CHECK"
    REFINE = "REFINE"
    PREREQUISITE = "PREREQUISITE"
    WAIT = "WAIT"
    CLOSE = "CLOSE"


class InquiryCriterionRole(StrEnum):
    TARGET_PROGRESS = "TARGET_PROGRESS"
    ENABLED_CAPABILITY = "ENABLED_CAPABILITY"
    DISCRIMINATION = "DISCRIMINATION"
    COST = "COST"


class InquiryOrdering(StrEnum):
    LEXICOGRAPHIC = "LEXICOGRAPHIC"
    PARTIAL = "PARTIAL"


class IncomparableResolution(StrEnum):
    HOLD = "HOLD"
    REQUIRE_HUMAN = "REQUIRE_HUMAN"


@dataclass(frozen=True, slots=True)
class InquiryCriterionRule(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/planning/inquiry-criterion-rule"
    criterion_id: str
    role: InquiryCriterionRole
    unit: str
    maximize: bool
    justification: str
    cost_field: str | None = None

    def __post_init__(self):
        validate_stable_id(self.criterion_id)
        if not isinstance(self.role, InquiryCriterionRole) or type(self.maximize) is not bool:
            raise ValueError("criterion role and ordering direction must be typed")
        for field in ("unit", "justification"):
            validate_nonempty(getattr(self, field), field_name=field)
        if self.cost_field is not None and (
            self.cost_field not in COST_FIELDS
            or self.role is not InquiryCriterionRole.COST
            or self.maximize
        ):
            raise ValueError("physical expense criterion must minimize its exact cost field")


@dataclass(frozen=True, slots=True)
class TargetDirectedAlternative(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/planning/inquiry-alternative"
    VERSION: ClassVar[str] = "2.0.0"
    alternative_id: str
    specification: ObjectIdentity
    state: ObjectIdentity
    action: InquiryAction
    eligible_outcomes: tuple[str, ...]
    kind: InquiryAlternativeKind
    requirement_id: str
    scope: ScientificConditionScope
    scientific_question: str
    observable: str
    evidence_needs: tuple[InquiryEvidenceNeed, ...]
    prerequisite_requirement_ids: tuple[str, ...]
    criteria: tuple[InquiryCriterionAssessment, ...]
    expense_bound: InquiryCost
    next_enabled_capability: str
    expected_next_evidence: str
    evidence_that_changes_disposition: str
    supplier: SupplierProposal | None = None
    parent_requirement_id: str | None = None
    work: ScientificInquiryWork | None = None
    reuse_completion: CompletedInquiryWork | None = None
    successor_draft: ObjectIdentity | None = None
    successor_config: ObjectIdentity | None = None
    input_origins: ObjectIdentity | None = None
    capability_id: str | None = None
    stop_scope: InquiryStopScope | None = None
    local_question_answered: bool = False
    planned_operation_count: int = 0

    def __post_init__(self):
        for field in ("alternative_id", "requirement_id"):
            validate_stable_id(getattr(self, field))
        if not isinstance(self.action, InquiryAction) or not isinstance(self.kind, InquiryAlternativeKind):
            raise ValueError("alternative action/scientific purpose must be typed")
        if type(self.local_question_answered) is not bool:
            raise ValueError("local completion must be explicit")
        _count(self.planned_operation_count, "planned_operation_count")
        for field in (
            "scientific_question", "observable", "next_enabled_capability",
            "expected_next_evidence", "evidence_that_changes_disposition",
        ):
            validate_nonempty(getattr(self, field), field_name=field)
        for field in ("eligible_outcomes", "prerequisite_requirement_ids"):
            require_sorted_unique_strings(getattr(self, field), field_name=field)
        _ids(self.evidence_needs, "evidence_id", "evidence_needs")
        _ids(self.criteria, "criterion_id", "criteria")
        bindings = (
            self.successor_draft, self.successor_config, self.input_origins, self.capability_id,
        )
        if self.action is InquiryAction.ACT:
            if any(value is None for value in bindings) or self.work is None or self.planned_operation_count == 0:
                raise ValueError("ACT needs exact successor bindings and scientific work identity")
            validate_inquiry_capability_id(self.capability_id)
            if self.kind in {InquiryAlternativeKind.WAIT, InquiryAlternativeKind.CLOSE}:
                raise ValueError("ACT cannot be waiting or scoped closure")
        elif any(value is not None for value in bindings) or self.work is not None or self.planned_operation_count:
            raise ValueError("HOLD/STOP has no executable successor")
        if self.action is InquiryAction.HOLD and self.kind is not InquiryAlternativeKind.WAIT:
            raise ValueError("HOLD must retain an explicit missing/uncertain question")
        if self.action is InquiryAction.STOP:
            if self.kind is not InquiryAlternativeKind.CLOSE or not isinstance(self.stop_scope, InquiryStopScope):
                raise ValueError("STOP needs an explicit question/branch/target scope")
        elif self.stop_scope is not None:
            raise ValueError("only STOP closes a declared scope")
        if self.kind is InquiryAlternativeKind.PREREQUISITE:
            if self.parent_requirement_id is None or self.parent_requirement_id == self.requirement_id:
                raise ValueError("recursive investigation must preserve its distinct parent requirement")
        elif self.parent_requirement_id is not None:
            raise ValueError("parent requirement belongs to a prerequisite investigation")
        if self.kind in {InquiryAlternativeKind.REUSE, InquiryAlternativeKind.ADOPT}:
            if self.reuse_completion is None:
                raise ValueError("adoption/reuse needs authenticated completed work")
        elif self.reuse_completion is not None:
            raise ValueError("a completed-work witness belongs to actual adoption/reuse")

    @property
    def required_evidence_ids(self):
        return tuple(row.evidence_id for row in self.evidence_needs)


@dataclass(frozen=True, slots=True)
class RobustInquiryMenu(CanonicalRecord):
    SCHEMA: ClassVar[str] = InquiryMenu.SCHEMA
    VERSION: ClassVar[str] = "2.0.0"
    menu_id: str
    specification: ObjectIdentity
    state: ObjectIdentity
    alternatives: tuple[TargetDirectedAlternative, ...]
    frontier: InquiryTargetFrontier
    observation: InquiryObservation

    def __post_init__(self):
        validate_stable_id(self.menu_id)
        _ids(self.alternatives, "alternative_id", "alternatives")
        if not self.alternatives:
            raise ValueError("inquiry menu must be finite and nonempty")
        for row in self.alternatives:
            row.__post_init__()
            if row.specification != self.specification or row.state != self.state:
                raise ValueError("alternative menu join differs")


@dataclass(frozen=True, slots=True)
class RobustInquiryPolicy(CanonicalRecord):
    SCHEMA: ClassVar[str] = InquiryPolicy.SCHEMA
    VERSION: ClassVar[str] = "2.0.0"
    policy_id: str
    specification: ObjectIdentity
    max_cost: InquiryCost
    max_operations: int | None
    max_waves: int | None
    max_depth: int | None
    ordering: InquiryOrdering
    criterion_order: tuple[InquiryCriterionRule, ...]
    assumptions: tuple[InquiryPolicyAssumption, ...]
    incomparable_resolution: IncomparableResolution

    def __post_init__(self):
        validate_stable_id(self.policy_id)
        for field in ("max_operations", "max_waves", "max_depth"):
            value = getattr(self, field)
            if value is not None:
                _count(value, field)
        if not isinstance(self.ordering, InquiryOrdering) or not isinstance(
            self.incomparable_resolution, IncomparableResolution
        ):
            raise ValueError("ordering and unresolved-choice treatment must be explicit")
        if len({row.criterion_id for row in self.criterion_order}) != len(self.criterion_order):
            raise ValueError("criterion priority repeats an ordering rule")
        if {row.role for row in self.criterion_order} != set(InquiryCriterionRole):
            raise ValueError("policy must assess target, enabled capability, discrimination and cost")
        for row in self.criterion_order:
            row.__post_init__()
        _ids(self.assumptions, "assumption_id", "assumptions")


def _validate_records(specification: RobustInquirySpecification, state: InquiryState,
                      menu: RobustInquiryMenu, policy: RobustInquiryPolicy, outcome_id: str):
    for row in (specification, state, menu, policy, menu.frontier, menu.observation):
        row.__post_init__()
    sid = identity(specification, specification.specification_id)
    tid = identity(state, state.state_id)
    if state.specification != sid or menu.specification != sid or policy.specification != sid or menu.state != tid:
        raise ValueError("robust inquiry specification/state/menu/policy join differs")
    target = specification.target
    if menu.frontier.target != identity(target, target.target_id):
        raise ValueError("frontier changes the overarching scientific target")
    alternatives = {row.alternative_id: row for row in menu.alternatives}
    mapped = {(row.outcome_id, aid) for row in specification.outcomes for aid in row.alternative_ids}
    declared = {(oid, row.alternative_id) for row in menu.alternatives for oid in row.eligible_outcomes}
    if mapped != declared or any(aid not in alternatives for _, aid in mapped):
        raise ValueError("alternatives differ from the frozen complete outcome map")
    outcome = next((row for row in specification.outcomes if row.outcome_id == outcome_id), None)
    observation = menu.observation
    if outcome is None or (
        observation.specification != sid or observation.outcome_id != outcome_id
        or observation.kind is not outcome.kind
        or observation.assessment_contract != specification.distinguishing_assessment
        or observation.scope != specification.endpoint
        or observation.information_cutoff != state.information_cutoff
    ):
        raise ValueError("observation changes committed assessment/outcome/scope/cutoff")
    stock = {row.evidence_id: row for row in state.stock}
    products = {row.product for row in state.stock}
    if not set(observation.evidence_ids) <= stock.keys() or (
        observation.assessment is not None and observation.assessment not in products
    ):
        raise ValueError("observation lacks its authenticated stock assessment/evidence")
    if observation.assessment is not None and not any(
        stock[key].product == observation.assessment and stock[key].scope == observation.scope
        for key in observation.evidence_ids
    ):
        raise ValueError("observation assessment lacks its exact scoped evidence witness")
    attempts = {row.attempt_id: row for row in state.operational_census}
    if not set(observation.attempt_ids) <= attempts.keys():
        raise ValueError("observation substitutes retained operational attempts")
    statuses = {attempts[key].status for key in observation.attempt_ids}
    if observation.kind is ScientificOutcomeKind.UNCERTAIN_CONTACT:
        if statuses != {InquiryAttemptStatus.UNCERTAIN_CONTACT}:
            raise ValueError("uncertain contact cannot become completed or scientific work")
    elif observation.kind is ScientificOutcomeKind.OPERATIONAL_FAILURE:
        if not statuses or not statuses <= {InquiryAttemptStatus.FAILED, InquiryAttemptStatus.BLOCKED}:
            raise ValueError("operational failure requires its actual failed/blocked census")
    elif statuses and statuses != {InquiryAttemptStatus.COMPLETED}:
        raise ValueError("failed execution cannot become a scientific outcome")
    for evidence in state.stock:
        scope = evidence.scope
        cutoff = state.information_cutoff
        exposed = scope.information_cutoff
        if exposed is not None and exposed.clock_id != scope.clock_id:
            raise ValueError("stock cutoff changes its original scientific clock")
        if exposed is not None and exposed.clock_id == cutoff.clock_id and (
            exposed.coordinate is not None and (cutoff.coordinate is None or exposed.coordinate > cutoff.coordinate)
            or exposed.coordinate == cutoff.coordinate and (
                not exposed.phase.precedes_or_equals(cutoff.phase)
                or exposed.includes_coordinate and not cutoff.includes_coordinate
            )
        ):
            raise ValueError("stock lies beyond the frozen inquiry cutoff")
        if scope.available_by is not None and scope.clock_id == cutoff.clock_id and (
            cutoff.coordinate is None
            or scope.available_by > cutoff.coordinate
            or scope.available_by == cutoff.coordinate and not cutoff.includes_coordinate
        ):
            raise ValueError("stock is unavailable at the declared cutoff")
        for bound, lower in ((scope.valid_from, True), (scope.valid_until, False)):
            if bound is not None and scope.clock_id == cutoff.clock_id and (
                cutoff.coordinate is None
                or lower and cutoff.coordinate < bound or not lower and cutoff.coordinate > bound
            ):
                raise ValueError("stock is outside exact scientific validity")
    suppliers = tuple(row.supplier for row in menu.alternatives if row.supplier is not None)
    validate_selected_requirement_graph(requirements=specification.requirements, suppliers=suppliers)
    requirements = {row.requirement_id: row for row in specification.requirements}
    connections = {identity(row, row.connection_id): row for row in specification.connections}
    findings = {row.requirement.object_id: row for row in menu.frontier.requirement_findings}
    if findings.keys() != requirements.keys():
        raise ValueError("frontier drops target or prerequisite requirement denominator")
    supplied = set()
    for key, finding in findings.items():
        finding.__post_init__()
        if finding.requirement != identity(requirements[key], key):
            raise ValueError("frontier substitutes a requirement revision")
        if finding.connection is not None and (
            finding.connection not in connections or connections[finding.connection].requirement_id != key
        ):
            raise ValueError("frontier substitutes its actual assessed connection")
        for assessment in finding.assessments:
            assessment_identity = identity(assessment, assessment.assessment_id)
            if assessment_identity not in products or not set(assessment.evidence) <= products:
                raise ValueError("frontier supply finding lacks actual authenticated assessment/evidence")
            if not any(row.product == assessment_identity and row.scope == requirements[key].scope
                       for row in stock.values()):
                raise ValueError("frontier assessment changes its exact scientific requirement scope")
        if finding.supplied:
            supplied.add(key)
    claims = {row.claim.object_id: row for row in menu.frontier.claim_findings}
    if {row.claim for row in claims.values()} != set(target.required_claims):
        raise ValueError("frontier drops required target claim denominator")
    satisfied_claims = set()
    for finding in claims.values():
        finding.__post_init__()
        if finding.scope != target.scope:
            raise ValueError("target claim changes its actual instance/receiver/scientific scope")
        if not set(finding.evidence_ids) <= stock.keys() or (
            finding.assessment is not None and finding.assessment not in products
        ):
            raise ValueError("target claim lacks actual assessment stock")
        if finding.assessment is not None and not any(
            stock[key].product == finding.assessment and stock[key].scope == finding.scope
            for key in finding.evidence_ids
        ):
            raise ValueError("target claim assessment lacks its exact scoped evidence witness")
        if finding.disposition is AssessmentDisposition.SATISFIED:
            if any(stock[key].scope != finding.scope for key in finding.evidence_ids):
                raise ValueError("target success cannot combine incompatible endpoint scopes")
            satisfied_claims.add(finding.claim.object_id)
    completions = {row.completion_id: row for row in menu.frontier.completed_work}
    work_bindings = ({row.attempt_id: row for row in state.attempt_work_bindings}
                     if isinstance(state, WorkBoundInquiryState) else {})
    for completion in completions.values():
        completion.__post_init__()
        attempt = attempts.get(completion.attempt_id)
        if attempt is None or attempt.status is not InquiryAttemptStatus.COMPLETED or (
            attempt.receipt != completion.receipt or not set(completion.products) <= set(attempt.products)
            or not set(completion.products) <= products
        ):
            raise ValueError("completed work lacks its actual receipt/product/attempt joins")
        binding = work_bindings.get(completion.attempt_id)
        if binding is not None and binding.work != completion.work:
            raise ValueError("completed work changes its authenticated scientific work identity")
        if isinstance(state, WorkBoundInquiryState) and completion.products != attempt.products:
            raise ValueError("current completion changes its complete authenticated product denominator")
    assumptions = {row.assumption_id: row for row in policy.assumptions}
    if any(not set(row.evidence_ids) <= stock.keys() for row in assumptions.values()):
        raise ValueError("ordering assumption substitutes its supporting evidence")
    rules = {row.criterion_id: row for row in policy.criterion_order}
    for alternative in menu.alternatives:
        requirement = requirements.get(alternative.requirement_id)
        if requirement is None or alternative.scope != requirement.scope:
            raise ValueError("alternative changes exact target/prerequisite scientific scope")
        if not set(alternative.prerequisite_requirement_ids) <= requirements.keys():
            raise ValueError("alternative invents an unregistered scientific prerequisite")
        if alternative.supplier is not None and (
            alternative.supplier.requirement_id != alternative.requirement_id
            or alternative.supplier.prerequisite_requirement_ids != alternative.prerequisite_requirement_ids
        ):
            raise ValueError("alternative changes the supplier/prerequisite contract")
        if alternative.parent_requirement_id is not None and (
            alternative.parent_requirement_id not in requirements
            or alternative.requirement_id not in requirements[alternative.parent_requirement_id].further_requirement_ids
        ):
            raise ValueError("recursive supplier question loses its parent dependency")
        if alternative.action is InquiryAction.ACT:
            if alternative.work.scope != alternative.scope:
                raise ValueError("work changes the chosen scientific endpoint")
            if {row.criterion_id for row in alternative.criteria} != rules.keys():
                raise ValueError("ACT omits the complete policy criterion denominator")
        for criterion in alternative.criteria:
            rule = rules.get(criterion.criterion_id)
            if rule is None or criterion.unit != rule.unit or (
                not set(criterion.evidence_ids) <= stock.keys()
                or not set(criterion.assumption_ids) <= assumptions.keys()
            ):
                raise ValueError("ordering criterion changes units/evidence/declared assumptions")
            if rule.cost_field is not None and criterion.upper != getattr(alternative.expense_bound, rule.cost_field):
                raise ValueError("expense ordering cannot replace unknown/full resource accounting")
    return stock, supplied, satisfied_claims, completions


def _comparison(left, right, policy):
    """1 means robustly better, -1 worse, 0 exact tie, None incomparable."""
    a = {row.criterion_id: row for row in left.criteria}
    b = {row.criterion_id: row for row in right.criteria}
    signs = []
    for rule in policy.criterion_order:
        x, y = a[rule.criterion_id], b[rule.criterion_id]
        if x.lower is None or y.lower is None:
            result = None
        elif x.lower == x.upper == y.lower == y.upper:
            result = 0
        elif x.lower > y.upper:
            result = 1 if rule.maximize else -1
        elif x.upper < y.lower:
            result = -1 if rule.maximize else 1
        else:
            result = None
        if policy.ordering is InquiryOrdering.LEXICOGRAPHIC:
            if result != 0:
                return result
        signs.append(result)
    if policy.ordering is InquiryOrdering.LEXICOGRAPHIC:
        return 0
    if any(row is None for row in signs):
        return None
    if all(row >= 0 for row in signs) and any(row > 0 for row in signs):
        return 1
    if all(row <= 0 for row in signs) and any(row < 0 for row in signs):
        return -1
    return 0 if all(row == 0 for row in signs) else None


def uncertain_contact_requires_recovery(*, operational_census: tuple[InquiryAttempt, ...],
        attempt_work_bindings: tuple[InquiryAttemptWorkBinding, ...],
        selected_work: ScientificInquiryWork, successor_config: ObjectIdentity) -> bool:
    """Apply the existing no-replay rule to authenticated actual attempt records.

    Unknown historical work remains conservative. Callers authenticate custody
    and the census/binding joins before using this predicate; it grants nothing.
    """
    bindings = {row.attempt_id: row for row in attempt_work_bindings}
    return any(attempt.status is InquiryAttemptStatus.UNCERTAIN_CONTACT and (
        attempt.attempt_id not in bindings or bindings[attempt.attempt_id].work is None
        or bindings[attempt.attempt_id].work == selected_work
        or attempt.operation in {selected_work.method, successor_config}
    ) for attempt in operational_census)


def evaluate_robust_inquiry(specification, state, menu, policy, outcome_id):
    stock, supplied, claims, completions = _validate_records(specification, state, menu, policy, outcome_id)
    target_complete = set(specification.required_requirement_closure) <= supplied and {
        row.object_id for row in specification.target.required_claims
    } <= claims
    spent = summarize_cost(state.cost_events)
    reasons = {}
    requirements = {row.requirement_id: row for row in specification.requirements}
    for alternative in menu.alternatives:
        why = []
        if outcome_id not in alternative.eligible_outcomes:
            why.append("outcome-ineligible")
        if alternative.action is InquiryAction.ACT and not set(alternative.prerequisite_requirement_ids) <= supplied:
            why.append("missing-prerequisite")
        for need in alternative.evidence_needs:
            actual = stock.get(need.evidence_id)
            if actual is None:
                why.append("missing-evidence")
            elif actual.product != need.product or actual.scope != need.scope or actual.role is not need.role:
                why.append("source-scope-role-ineligible")
            if need.role not in requirements[alternative.requirement_id].permitted_roles:
                why.append("requirement-evidence-role-ineligible")
            if need.scope != alternative.scope:
                finding = next(row for row in menu.frontier.requirement_findings
                               if row.requirement.object_id == alternative.requirement_id)
                compatible = any(
                    identity(assessment, assessment.assessment_id) == need.compatibility_assessment
                    and assessment.phase is AssessmentPhase.ADMISSION
                    and assessment.disposition is AssessmentDisposition.SATISFIED
                    and need.product in assessment.evidence
                    for assessment in finding.assessments
                )
                if not compatible:
                    why.append("independent-cross-scope-compatibility-required")
        if alternative.action is InquiryAction.ACT:
            bindings = ({row.attempt_id: row for row in state.attempt_work_bindings}
                        if isinstance(state, WorkBoundInquiryState) else {})
            if uncertain_contact_requires_recovery(operational_census=state.operational_census,
                    attempt_work_bindings=(state.attempt_work_bindings
                        if isinstance(state, WorkBoundInquiryState) else ()),
                    selected_work=alternative.work, successor_config=alternative.successor_config):
                why.append("uncertain-contact-recovery-required")
            if alternative.supplier is not None and (
                not alternative.supplier.selected or alternative.supplier.unavailable_reason_codes
            ):
                why.append("supplier-unavailable-or-unselected")
            already_completed = any(attempt.status is InquiryAttemptStatus.COMPLETED and (
                (attempt.attempt_id in bindings and bindings[attempt.attempt_id].work == alternative.work)
                or attempt.operation in {alternative.work.method, alternative.successor_config}
            ) for attempt in state.operational_census) if isinstance(state, WorkBoundInquiryState) else (
                alternative.kind is InquiryAlternativeKind.ACQUIRE and any(
                    row.work == alternative.work for row in completions.values()))
            if already_completed and alternative.reuse_completion is None:
                why.append("authenticated-completion-reuse-required")
            if alternative.reuse_completion is not None and (
                completions.get(alternative.reuse_completion.completion_id) != alternative.reuse_completion
                or alternative.reuse_completion.work != alternative.work
            ):
                why.append("completion-reuse-join-ineligible")
            read_only_reuse = isinstance(state, WorkBoundInquiryState) and alternative.reuse_completion is not None
            counts = (
                (len(state.operational_census) + (0 if read_only_reuse else alternative.planned_operation_count), policy.max_operations),
                (state.wave_count + (0 if read_only_reuse else 1), policy.max_waves),
                (state.depth_count + (0 if read_only_reuse else 1), policy.max_depth),
            )
            if any(bound is not None and count > bound for count, bound in counts):
                why.append("finite-allowance-exhausted")
            for field in COST_FIELDS:
                old, new, bound = getattr(spent, field), getattr(alternative.expense_bound, field), getattr(policy.max_cost, field)
                if bound is not None:
                    if old is None or new is None:
                        why.append("unknown-required-expense")
                    elif old + new > bound:
                        why.append("resource-allowance-exhausted")
        elif alternative.action is InquiryAction.STOP:
            if alternative.stop_scope is InquiryStopScope.TARGET and not target_complete:
                why.append("target-required-claims-or-joined-supply-unresolved")
            elif alternative.stop_scope is not InquiryStopScope.TARGET and not alternative.local_question_answered:
                why.append("local-question-closure-unassessed")
            if menu.observation.kind in {ScientificOutcomeKind.MISSING, ScientificOutcomeKind.OPERATIONAL_FAILURE, ScientificOutcomeKind.UNCERTAIN_CONTACT}:
                why.append("operational-or-missing-result-does-not-answer-science")
        reasons[alternative.alternative_id] = tuple(sorted(set(why)))
    acts = [row for row in menu.alternatives if row.action is InquiryAction.ACT and not reasons[row.alternative_id]]
    evaluations = []
    for alternative in menu.alternatives:
        aid = alternative.alternative_id
        dominators, incomparable = [], []
        if not reasons[aid] and alternative.action is InquiryAction.ACT:
            for other in acts:
                if other.alternative_id == aid:
                    continue
                comparison = _comparison(alternative, other, policy)
                if comparison == -1:
                    dominators.append(other.alternative_id)
                elif comparison is None:
                    incomparable.append(other.alternative_id)
        status = (
            RobustChoiceStatus.INELIGIBLE if reasons[aid] else
            RobustChoiceStatus.DOMINATED if dominators else
            RobustChoiceStatus.INCOMPARABLE if incomparable else
            RobustChoiceStatus.MAXIMAL if alternative.action is InquiryAction.ACT else
            RobustChoiceStatus.AVAILABLE
        )
        evaluations.append(RobustChoiceEvaluation(
            aid, not reasons[aid], reasons[aid], status, tuple(sorted(dominators)),
            tuple(sorted(incomparable)), alternative.evidence_that_changes_disposition,
        ))
    return tuple(evaluations)


def _choose_robust_inquiry(*, decision_id, specification, state, menu, policy,
                         campaign: CampaignSpec, right: DecisionRight, actor_id, outcome_id, human_choice=None,
                         human_reason=None, validate_authority=True):
    if validate_authority:
        from .recursive_inquiry import validate_inquiry_authority

        validate_inquiry_authority(
            specification=specification, campaign=campaign, right=right,
            actor_id=actor_id, required_action=specification.required_decision_action,
        )
    evaluations = evaluate_robust_inquiry(specification, state, menu, policy, outcome_id)
    eligible = {row.alternative_id for row in evaluations if row.eligible}
    alternatives = {row.alternative_id: row for row in menu.alternatives}
    if human_choice is not None:
        if human_choice not in eligible or human_reason is None:
            raise ValueError("human redirection requires an eligible frozen choice and attributable reason")
        validate_nonempty(human_reason, field_name="human_reason")
        selected = alternatives[human_choice]
        reason = "Human-directed eligible alternative; automatic policy credit is not claimed."
    else:
        if human_reason is not None:
            raise ValueError("human reason cannot be attributed to an automatic decision")
        maximal = [row for row in evaluations if row.eligible and not row.dominated_by
                   and alternatives[row.alternative_id].action is InquiryAction.ACT]
        incomparable = any(
            other.alternative_id in row.incomparable_with
            for row in maximal for other in maximal if other != row
        )
        if maximal and not incomparable:
            selected = alternatives[min(row.alternative_id for row in maximal)]
            reason = "Robust evidenced ordering; exact supported ties use the frozen lexical identifier order."
        else:
            if maximal and policy.incomparable_resolution is IncomparableResolution.REQUIRE_HUMAN:
                raise ValueError("incomparable supported alternatives require explicit human direction")
            holds = [row for row in menu.alternatives if row.alternative_id in eligible and row.action is InquiryAction.HOLD]
            stops = [row for row in menu.alternatives if row.alternative_id in eligible and row.action is InquiryAction.STOP]
            if maximal and not holds:
                raise ValueError("incomparable alternatives need an explicit frozen HOLD")
            # An assessed local closure is itself a meaningful declared result.
            # Incomparability still requires HOLD; otherwise close the eligible
            # answered branch/target before an available generic wait choice.
            fallback = holds if maximal else stops if stops else holds
            if not fallback:
                raise ValueError("no eligible decision; retain a prerequisite/revision HOLD in the frozen menu")
            selected = min(fallback, key=lambda row: row.alternative_id)
            reason = (
                "Supported alternatives are incomparable; unknown bounds remain unknown." if maximal else
                "No eligible supported action; retain the declared missing prerequisite or scoped local closure."
            )
    if validate_authority:
        validate_inquiry_authority(
            specification=specification, campaign=campaign, right=right,
            actor_id=actor_id, required_action=specification.required_decision_action,
            additional_scopes=(selected.scope,),
        )
    supplied = tuple(sorted(row.requirement.object_id for row in menu.frontier.requirement_findings if row.supplied))
    unresolved_requirements = tuple(sorted(set(specification.required_requirement_closure) - set(supplied)))
    satisfied = {row.claim.object_id for row in menu.frontier.claim_findings if row.disposition is AssessmentDisposition.SATISFIED}
    unresolved_claims = tuple(sorted({row.object_id for row in specification.target.required_claims} - satisfied))
    spent = summarize_cost(state.cost_events)
    remaining = InquiryCost(*(
        None if getattr(policy.max_cost, field) is None or getattr(spent, field) is None
        or getattr(selected.expense_bound, field) is None else
        max(Decimal(0), getattr(policy.max_cost, field) - getattr(spent, field) - getattr(selected.expense_bound, field))
        for field in COST_FIELDS
    ))
    decision_type = WorkBoundInquiryDecision if isinstance(state, WorkBoundInquiryState) else RobustInquiryDecision
    return decision_type(
        decision_id, identity(specification, specification.specification_id), identity(state, state.state_id),
        identity(menu, menu.menu_id), identity(policy, policy.policy_id), selected.alternative_id,
        actor_id, identity(right, right.decision_right_id), identity(campaign, campaign.campaign_id),
        human_choice is not None, outcome_id, evaluations, remaining,
        identity(specification.target, specification.target.target_id), identity(menu.frontier, menu.frontier.frontier_id),
        supplied, unresolved_requirements, unresolved_claims, selected.next_enabled_capability,
        selected.expected_next_evidence, reason, human_reason, selected.stop_scope,
        tuple(row.requirement.object_id for row in menu.frontier.requirement_findings if not row.assessments),
    )


def choose_robust_inquiry(*, decision_id, specification, state, menu, policy,
                         campaign, right, actor_id, outcome_id, human_choice=None,
                         human_reason=None):
    """New decisions always enforce applicable current campaign/right authority."""
    return _choose_robust_inquiry(
        decision_id=decision_id, specification=specification, state=state, menu=menu,
        policy=policy, campaign=campaign, right=right, actor_id=actor_id,
        outcome_id=outcome_id, human_choice=human_choice, human_reason=human_reason,
        validate_authority=True,
    )


def make_robust_successor_intent(*, intent_id, decision, specification, menu):
    if decision.specification != identity(specification, specification.specification_id) or (
        decision.menu != identity(menu, menu.menu_id) or decision.state != menu.state
        or decision.frontier != identity(menu.frontier, menu.frontier.frontier_id)
    ):
        raise ValueError("successor changes its exact target/frontier/menu decision")
    selected = next((row for row in menu.alternatives if row.alternative_id == decision.selected_alternative_id), None)
    if selected is None or selected.action is not InquiryAction.ACT:
        raise ValueError("only a committed ACT has a successor intent")
    return InquirySuccessorIntent(
        intent_id, identity(decision, decision.decision_id), decision.specification, decision.state,
        decision.menu, decision.policy, selected.alternative_id, selected.successor_draft,
        selected.successor_config, selected.input_origins, selected.scope, selected.capability_id,
    )


def validate_robust_inquiry_join(*, decision, specification, state, menu, policy,
                               campaign, right, intent=None, validate_authority=True, historical=False):
    """Pure archived replay is explicitly selected; fresh admission checks authority."""
    if historical and type(decision) is RobustInquiryDecision and type(state) is InquiryState:
        # This authenticates the closed original record joins and its retained
        # evaluations. It does not rerank old work under a new policy or grant
        # admission from a historical eligibility/target-completion statement.
        _validate_records(specification, state, menu, policy, decision.outcome_id)
        expected = (identity(specification, specification.specification_id), identity(state, state.state_id),
                    identity(menu, menu.menu_id), identity(policy, policy.policy_id),
                    identity(campaign, campaign.campaign_id), identity(right, right.decision_right_id),
                    identity(specification.target, specification.target.target_id),
                    identity(menu.frontier, menu.frontier.frontier_id))
        if (decision.specification, decision.state, decision.menu, decision.policy, decision.campaign,
                decision.decision_right, decision.target, decision.frontier) != expected:
            raise ValueError("historical robust decision changes its original record joins")
        selected = next((row for row in menu.alternatives if row.alternative_id == decision.selected_alternative_id), None)
        evaluations = {row.alternative_id: row for row in decision.evaluations}
        if (evaluations.keys() != {row.alternative_id for row in menu.alternatives}
                or selected is None or not evaluations[selected.alternative_id].eligible
                or decision.outcome_id not in selected.eligible_outcomes or decision.stop_scope != selected.stop_scope):
            raise ValueError("historical robust decision changes its original selected evaluation")
        if intent is not None and intent != make_robust_successor_intent(
            intent_id=intent.intent_id, decision=decision, specification=specification, menu=menu,
        ):
            raise ValueError("historical robust successor intent changes original scientific bindings")
        return
    expected = _choose_robust_inquiry(
        decision_id=decision.decision_id, specification=specification, state=state, menu=menu,
        policy=policy, campaign=campaign, right=right, actor_id=decision.actor_id,
        outcome_id=decision.outcome_id,
        human_choice=decision.selected_alternative_id if decision.human_directed else None,
        human_reason=decision.human_reason, validate_authority=validate_authority,
    )
    if expected != decision:
        raise ValueError("robust decision target/frontier/order/human join differs")
    if intent is not None and intent != make_robust_successor_intent(
        intent_id=intent.intent_id, decision=decision, specification=specification, menu=menu,
    ):
        raise ValueError("robust successor intent scientific bindings differ")


def validate_robust_inquiry_revision(*, previous_specification, previous_state,
                                    specification, state, policy):
    """Redirect a scientific question while preserving its target and exposed history."""
    if specification.predecessor_specification != identity(previous_specification, previous_specification.specification_id):
        raise ValueError("revision needs the exact frozen predecessor inquiry and outcome map")
    if state.revision_parent != identity(previous_state, previous_state.state_id):
        raise ValueError("revision needs the exact retained predecessor state")
    if specification.target != previous_specification.target:
        raise ValueError("scientific redirection cannot replace or complete the overarching target")
    sid = identity(specification, specification.specification_id)
    if state.specification != sid or policy.specification != sid:
        raise ValueError("revision specification/state/policy join differs")
    if specification.specification_id == previous_specification.specification_id or state.state_id == previous_state.state_id:
        raise ValueError("changed scientific question needs its own explicit canonical revision")
    for field, attribute in (
        ("stock", "evidence_id"), ("cost_events", "event_id"),
        ("operational_census", "attempt_id"), ("previous_decisions", "object_id"),
    ):
        retained = {getattr(row, attribute): row for row in getattr(state, field)}
        if any(retained.get(getattr(row, attribute)) != row for row in getattr(previous_state, field)):
            raise ValueError(f"scientific redirection altered retained {field}")
    if isinstance(previous_state, WorkBoundInquiryState):
        if not isinstance(state, WorkBoundInquiryState):
            raise ValueError("scientific redirection drops authenticated work bindings")
        retained = {row.attempt_id: row for row in state.attempt_work_bindings}
        if any(retained.get(row.attempt_id) != row for row in previous_state.attempt_work_bindings):
            raise ValueError("scientific redirection altered retained work bindings")
    old, new = previous_state.information_cutoff, state.information_cutoff
    if old.clock_id == new.clock_id and (
        old.coordinate is not None and (new.coordinate is None or new.coordinate < old.coordinate)
        or old.coordinate == new.coordinate and (
            not old.phase.precedes_or_equals(new.phase) or old.includes_coordinate and not new.includes_coordinate
        )
    ):
        raise ValueError("scientific revision resets source exposure cutoff")
    if state.wave_count < previous_state.wave_count or state.depth_count < previous_state.depth_count:
        raise ValueError("scientific revision resets operational counts")
