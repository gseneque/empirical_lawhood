# SPDX-License-Identifier: MPL-2.0
"""Finite inquiry choice, immutable successor bindings and structural admission."""
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import ClassVar

from empirical_lawhood.kernel.authority import AuthorityAction
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.status import LifecycleStatus
from empirical_lawhood.kernel.recursive_inquiry import (
    InquiryCost, InquirySpecification, InquiryState, InquiryChoiceEvaluation, InquiryDecision,
    InquirySuccessorIntent, _count, _ids, identity, summarize_cost, validate_inquiry_capability_id,
)
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord, require_sorted_unique_strings, validate_decimal,
    validate_stable_id,
)
from .campaigns import CampaignSpec, DecisionRight


class InquiryAction(StrEnum):
    ACT = "ACT"
    HOLD = "HOLD"
    STOP = "STOP"


@dataclass(frozen=True, slots=True)
class InquiryAlternative(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/planning/inquiry-alternative"
    alternative_id: str
    specification: ObjectIdentity
    state: ObjectIdentity
    action: InquiryAction
    eligible_outcomes: tuple[str, ...]
    required_evidence_ids: tuple[str, ...]
    declared_value: Decimal
    expense_bound: InquiryCost
    successor_draft: ObjectIdentity | None = None
    successor_config: ObjectIdentity | None = None
    input_origins: ObjectIdentity | None = None
    capability_id: str | None = None

    def __post_init__(self) -> None:
        validate_stable_id(self.alternative_id)
        if not isinstance(self.action, InquiryAction):
            raise ValueError("inquiry action must be typed")
        validate_decimal(self.declared_value, field_name="declared_value")
        for field in ("eligible_outcomes", "required_evidence_ids"):
            require_sorted_unique_strings(getattr(self, field), field_name=field)
        bindings = (self.successor_draft, self.successor_config, self.input_origins, self.capability_id)
        if self.action is InquiryAction.ACT:
            if any(value is None for value in bindings):
                raise ValueError("ACT requires exact draft/config/input origins/capability")
            validate_inquiry_capability_id(self.capability_id)
        elif any(value is not None for value in bindings):
            raise ValueError("HOLD/STOP has no successor")


@dataclass(frozen=True, slots=True)
class InquiryMenu(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/planning/inquiry-menu"
    menu_id: str
    specification: ObjectIdentity
    state: ObjectIdentity
    alternatives: tuple[InquiryAlternative, ...]

    def __post_init__(self) -> None:
        validate_stable_id(self.menu_id)
        _ids(self.alternatives, "alternative_id", "alternatives")
        if not self.alternatives:
            raise ValueError("inquiry menu must be finite and nonempty")
        for alternative in self.alternatives:
            if alternative.specification != self.specification or alternative.state != self.state:
                raise ValueError("alternative menu join differs")


@dataclass(frozen=True, slots=True)
class InquiryPolicy(CanonicalRecord):
    """Optional operator allowances; ``None`` declares no ceiling for that field.

    ``max_cost`` is a ceiling in this policy, not a measurement. Unknown actual
    or forecast costs remain unknown and matter only when that cost is bounded.
    Existing finite policies retain their exact canonical representation.
    """
    SCHEMA: ClassVar[str] = "empirical-lawhood/planning/inquiry-policy"
    policy_id: str
    specification: ObjectIdentity
    max_cost: InquiryCost
    max_operations: int | None
    max_waves: int | None
    max_depth: int | None

    def __post_init__(self) -> None:
        validate_stable_id(self.policy_id)
        for field in ("max_operations", "max_waves", "max_depth"):
            value = getattr(self, field)
            if value is not None:
                _count(value, field)


COST_FIELDS = ("cpu_seconds", "wall_seconds", "retained_bytes")


def validate_inquiry_authority(*, specification, campaign: CampaignSpec,
                               right: DecisionRight, actor_id: str,
                               required_action: AuthorityAction | None = None,
                               additional_scopes=()) -> None:
    """Check decision provenance without granting native execution authority.

    The campaign and right are immutable operands of the inquiry decision.
    Execution, issue and reveal still pass through their existing owners.
    """
    if campaign.lifecycle_status is not LifecycleStatus.ACTIVE:
        raise ValueError("inquiry decision requires an ACTIVE campaign")
    for scope in (specification.endpoint, *additional_scopes):
        if scope.system_id not in campaign.system_ids or scope.world_id not in campaign.world_ids:
            raise ValueError("inquiry endpoint is outside campaign system/world scope")
    if right not in campaign.decision_rights or right.decision_maker_id != actor_id:
        raise ValueError("actor/right is not the campaign decision maker")
    if right.authority_policy_id != campaign.authority_policy.object_id:
        raise ValueError("inquiry decision right changes campaign authority policy")
    actions = {AuthorityAction.READ_ONLY_EXPLORATION, AuthorityAction.SIMULATION_EXECUTION,
               AuthorityAction.REFERENCE_WORLD_EXECUTION}
    if right.action not in actions or (required_action is not None and right.action is not required_action):
        raise ValueError("inquiry decision right does not authorize the required decision action")



def _validate_inputs(specification: InquirySpecification, state: InquiryState,
                     menu: InquiryMenu, policy: InquiryPolicy) -> None:
    spec = identity(specification, specification.specification_id)
    current = identity(state, state.state_id)
    if (state.specification != spec or menu.specification != spec or policy.specification != spec
            or menu.state != current):
        raise ValueError("inquiry specification/state/menu/policy join differs")
    alternatives = {a.alternative_id: a for a in menu.alternatives}
    for outcome in specification.outcome_choices:
        if not set(outcome.alternative_ids) <= alternatives.keys():
            raise ValueError("outcome map references absent alternative")
        if any(outcome.outcome_id not in alternatives[a].eligible_outcomes
               for a in outcome.alternative_ids):
            raise ValueError("outcome map differs from alternative eligibility")
    mapped = {(o.outcome_id, a) for o in specification.outcome_choices for a in o.alternative_ids}
    if any((o, a.alternative_id) not in mapped for a in menu.alternatives for o in a.eligible_outcomes):
        raise ValueError("alternative outcome absent from frozen map")
    for evidence in state.stock:
        scope = evidence.scope
        if scope.information_cutoff is not None and scope.information_cutoff != state.information_cutoff:
            raise ValueError("stock cutoff differs from state")
        for field, lower in (("valid_from", True), ("valid_until", False)):
            bound = getattr(scope, field)
            if bound is not None:
                point = state.information_cutoff.coordinate
                if (scope.clock_id != state.information_cutoff.clock_id or point is None
                        or (lower and point < bound) or (not lower and point > bound)):
                    raise ValueError("stock outside validity at cutoff")
        if scope.available_by is not None:
            cutoff = state.information_cutoff
            if (scope.clock_id != cutoff.clock_id or cutoff.coordinate is None
                    or scope.available_by > cutoff.coordinate
                    or (scope.available_by == cutoff.coordinate and not cutoff.includes_coordinate)):
                raise ValueError("stock unavailable at cutoff")


def evaluate_inquiry(specification: InquirySpecification, state: InquiryState,
                     menu: InquiryMenu, policy: InquiryPolicy,
                     outcome_id: str) -> tuple[InquiryChoiceEvaluation, ...]:
    _validate_inputs(specification, state, menu, policy)
    if outcome_id not in {o.outcome_id for o in specification.outcome_choices}:
        raise ValueError("outcome absent from frozen inquiry map")
    stock = {e.evidence_id for e in state.stock}
    spent = summarize_cost(state.cost_events)
    evaluations = []
    for alternative in menu.alternatives:
        reasons = []
        if outcome_id not in alternative.eligible_outcomes:
            reasons.append("outcome-ineligible")
        if not set(alternative.required_evidence_ids) <= stock:
            reasons.append("missing-evidence")
        if alternative.action is InquiryAction.ACT:
            counts = ((len(state.operational_census), policy.max_operations),
                      (state.wave_count, policy.max_waves), (state.depth_count, policy.max_depth))
            if any(bound is not None and count >= bound for count, bound in counts):
                reasons.append("finite-allowance-exhausted")
            for field in COST_FIELDS:
                old, new, bound = getattr(spent, field), getattr(alternative.expense_bound, field), getattr(policy.max_cost, field)
                if bound is None:
                    continue
                if old is None or new is None:
                    reasons.append("unknown-required-expense")
                elif old + new > bound:
                    reasons.append("resource-allowance-exhausted")
        evaluations.append(InquiryChoiceEvaluation(alternative.alternative_id, not reasons, tuple(sorted(set(reasons)))))
    return tuple(evaluations)


def _choose_inquiry(*, decision_id: str, specification: InquirySpecification,
                   state: InquiryState, menu: InquiryMenu, policy: InquiryPolicy,
                   campaign: CampaignSpec, right: DecisionRight, actor_id: str,
                   outcome_id: str, human_choice: str | None = None,
                   historical: bool = False) -> InquiryDecision:
    if historical:
        # Preserve the original v1 arithmetic for authenticated archive reading.
        # Fresh decisions and successor admission never select this path.
        if right not in campaign.decision_rights or right.decision_maker_id != actor_id:
            raise ValueError("actor/right is not the campaign decision maker")
    else:
        validate_inquiry_authority(specification=specification, campaign=campaign,
                                   right=right, actor_id=actor_id)
    evaluations = evaluate_inquiry(specification, state, menu, policy, outcome_id)
    eligible = {e.alternative_id for e in evaluations if e.eligible}
    candidates = [a for a in menu.alternatives if a.alternative_id in eligible]
    if not candidates:
        raise ValueError("no eligible choice; frozen menu needs a HOLD/STOP")
    if human_choice is None:
        selected = sorted(candidates, key=lambda a: (-a.declared_value, a.alternative_id))[0]
    else:
        if human_choice not in eligible:
            raise ValueError("human choice is outside eligible frozen menu")
        selected = next(a for a in candidates if a.alternative_id == human_choice)
    spent = summarize_cost(state.cost_events)
    remaining = InquiryCost(*(None if getattr(policy.max_cost, f) is None or getattr(spent, f) is None or getattr(selected.expense_bound, f) is None
                              else max(Decimal(0), getattr(policy.max_cost, f) - getattr(spent, f) - getattr(selected.expense_bound, f))
                              for f in COST_FIELDS))
    return InquiryDecision(decision_id, identity(specification, specification.specification_id),
                           identity(state, state.state_id), identity(menu, menu.menu_id),
                           identity(policy, policy.policy_id), selected.alternative_id, actor_id,
                           identity(right, right.decision_right_id), identity(campaign, campaign.campaign_id),
                           human_choice is not None, outcome_id, evaluations, remaining)


def choose_inquiry(*, decision_id: str, specification: InquirySpecification,
                   state: InquiryState, menu: InquiryMenu, policy: InquiryPolicy,
                   campaign: CampaignSpec, right: DecisionRight, actor_id: str,
                   outcome_id: str, human_choice: str | None = None) -> InquiryDecision:
    return _choose_inquiry(decision_id=decision_id, specification=specification, state=state,
        menu=menu, policy=policy, campaign=campaign, right=right, actor_id=actor_id,
        outcome_id=outcome_id, human_choice=human_choice)


def validate_inquiry_join(*, decision: InquiryDecision, specification: InquirySpecification,
                          state: InquiryState, menu: InquiryMenu, policy: InquiryPolicy,
                          campaign: CampaignSpec, right: DecisionRight,
                          intent: InquirySuccessorIntent | None = None,
                          historical: bool = False) -> None:
    expected = _choose_inquiry(decision_id=decision.decision_id, specification=specification,
                              state=state, menu=menu, policy=policy, campaign=campaign, right=right,
                              actor_id=decision.actor_id, outcome_id=decision.outcome_id,
                              human_choice=decision.selected_alternative_id if decision.human_directed else None,
                              historical=historical)
    if expected != decision:
        raise ValueError("decision join differs")
    if intent is not None:
        if intent != make_successor_intent(intent_id=intent.intent_id, decision=decision,
                                          specification=specification, menu=menu):
            raise ValueError("successor intent join differs")


def make_successor_intent(*, intent_id: str, decision: InquiryDecision,
                          specification: InquirySpecification, menu: InquiryMenu) -> InquirySuccessorIntent:
    if (decision.specification != identity(specification, specification.specification_id)
            or decision.menu != identity(menu, menu.menu_id) or decision.state != menu.state):
        raise ValueError("successor specification/menu/state join differs")
    selected = next((a for a in menu.alternatives if a.alternative_id == decision.selected_alternative_id), None)
    if selected is None or selected.action is not InquiryAction.ACT:
        raise ValueError("only ACT has a successor intent")
    return InquirySuccessorIntent(intent_id, identity(decision, decision.decision_id),
                                  decision.specification, decision.state, decision.menu, decision.policy,
                                  selected.alternative_id, selected.successor_draft, selected.successor_config,
                                  selected.input_origins, specification.endpoint, selected.capability_id)


def validate_inquiry_revision(*, previous_specification: InquirySpecification,
                              previous_state: InquiryState, specification: InquirySpecification,
                              state: InquiryState, policy: InquiryPolicy) -> None:
    """Revision preserves exposed stock, cost events, decisions and every terminal."""
    if specification.predecessor_specification != identity(previous_specification, previous_specification.specification_id):
        raise ValueError("revision requires exact predecessor specification")
    if state.revision_parent != identity(previous_state, previous_state.state_id):
        raise ValueError("revision requires exact predecessor state")
    if state.specification != identity(specification, specification.specification_id) or policy.specification != state.specification:
        raise ValueError("revision specification/state/policy join differs")
    if (specification.specification_id == previous_specification.specification_id
            or state.state_id == previous_state.state_id):
        raise ValueError("revision requires fresh explicit identities")
    for field, attribute in (("stock", "evidence_id"), ("cost_events", "event_id"),
                             ("operational_census", "attempt_id"), ("previous_decisions", "object_id")):
        retained = {getattr(v, attribute): v for v in getattr(state, field)}
        if any(retained.get(getattr(v, attribute)) != v for v in getattr(previous_state, field)):
            raise ValueError(f"revision lost or altered {field}")
    old_scope, new_scope = previous_specification.endpoint, specification.endpoint
    if (old_scope.system_id, old_scope.world_id, old_scope.source_id) != (new_scope.system_id, new_scope.world_id, new_scope.source_id):
        raise ValueError("revision cannot open another source/system/world scope")
    old_cutoff, new_cutoff = previous_state.information_cutoff, state.information_cutoff
    if (old_cutoff.clock_id != new_cutoff.clock_id
            or old_cutoff.coordinate is not None and (new_cutoff.coordinate is None or new_cutoff.coordinate < old_cutoff.coordinate)):
        raise ValueError("revision cannot reset exposure cutoff")
    if old_cutoff.coordinate == new_cutoff.coordinate and (
            not old_cutoff.phase.precedes_or_equals(new_cutoff.phase)
            or old_cutoff.includes_coordinate and not new_cutoff.includes_coordinate):
        raise ValueError("revision cannot reset exposure cutoff phase or inclusion")
    if state.wave_count < previous_state.wave_count or state.depth_count < previous_state.depth_count:
        raise ValueError("revision reset finite counts")
