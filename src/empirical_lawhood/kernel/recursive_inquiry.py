# SPDX-License-Identifier: MPL-2.0
"""Bounded inquiry evidence and measured costs; no execution or qualification authority."""
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import ClassVar

from .evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from .provenance import ObjectIdentity
from .recursive_requirements import ContributionRole, ScientificConditionScope
from .serialization import (CanonicalRecord, require_sorted_unique_ids,
                            require_sorted_unique_strings, validate_decimal,
                            validate_nonempty, validate_stable_id)
from .time import InformationCutoff


def identity(record: CanonicalRecord, object_id: str) -> ObjectIdentity:
    return ObjectIdentity.from_record(object_id, record)


def validate_inquiry_capability_id(value: str) -> None:
    """Accept exact key@version selections and retain historical stable keys."""
    from .serialization import validate_semantic_version

    validate_nonempty(value, field_name="capability_id")
    key, separator, version = value.partition("@")
    validate_stable_id(key, field_name="capability key")
    if separator:
        validate_semantic_version(version)


def _ids(values: tuple, attribute: str, field: str) -> None:
    require_sorted_unique_ids(values, attribute=attribute, field_name=field)


def _count(value: int, field: str) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(f"{field} requires a nonnegative integer")


@dataclass(frozen=True, slots=True)
class InquiryCost(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/kernel/inquiry-cost"
    cpu_seconds: Decimal | None
    wall_seconds: Decimal | None
    retained_bytes: Decimal | None

    def __post_init__(self) -> None:
        for field in ("cpu_seconds", "wall_seconds", "retained_bytes"):
            value = getattr(self, field)
            if value is not None:
                validate_decimal(value, field_name=field, minimum=Decimal(0))


@dataclass(frozen=True, slots=True)
class AcquisitionEvent(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/kernel/inquiry-acquisition-event"
    event_id: str
    attempt_id: str
    receipt: ObjectIdentity
    cost: InquiryCost

    def __post_init__(self) -> None:
        validate_stable_id(self.event_id)
        validate_stable_id(self.attempt_id)


class InquiryCostCategory(StrEnum):
    CONSTRUCTION = "CONSTRUCTION"
    FAILED_INVESTIGATION = "FAILED_INVESTIGATION"
    COMPATIBILITY = "COMPATIBILITY"
    QUALIFICATION = "QUALIFICATION"
    LATER_SUPPLY_USE = "LATER_SUPPLY_USE"
    REVALIDATION = "REVALIDATION"
    RESEARCHER_ASSISTANCE = "RESEARCHER_ASSISTANCE"


@dataclass(frozen=True, slots=True)
class InquiryCharge(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/kernel/inquiry-charge"
    charge_id: str
    event: ObjectIdentity
    inquiry: ObjectIdentity
    arm_id: str
    category: InquiryCostCategory
    sequence_id: str

    def __post_init__(self) -> None:
        for value in (self.charge_id, self.arm_id, self.sequence_id):
            validate_stable_id(value)
        if not isinstance(self.category, InquiryCostCategory):
            raise ValueError("cost category must be typed")
        if self.event.object_schema != AcquisitionEvent.SCHEMA:
            raise ValueError("charge requires acquisition event identity")



@dataclass(frozen=True, slots=True)
class InquiryCostAccount(CanonicalRecord):
    """Frozen full-charge opportunities for one inquiry arm and later-use sequence."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/kernel/inquiry-cost-account"
    account_id: str
    inquiry: ObjectIdentity
    arm_id: str
    sequence_id: str
    events: tuple[ObjectIdentity, ...]

    def __post_init__(self) -> None:
        for value in (self.account_id, self.arm_id, self.sequence_id):
            validate_stable_id(value)
        if self.inquiry.object_schema != InquirySpecification.SCHEMA:
            raise ValueError("account requires exact inquiry specification")
        _ids(self.events, "object_id", "events")
        if any(event.object_schema != AcquisitionEvent.SCHEMA for event in self.events):
            raise ValueError("account events must be acquisition event identities")


def summarize_cost(events: tuple[AcquisitionEvent, ...],
                   charges: tuple[InquiryCharge, ...] = (), *,
                   arm_id: str | None = None,
                   account: InquiryCostAccount | None = None) -> InquiryCost:
    """Physical events once, or frozen full charges per selected policy arm."""
    if arm_id is not None and (account is None or account.arm_id != arm_id):
        raise ValueError("arm cost projection requires exact frozen account")
    if account is not None and arm_id is None:
        raise ValueError("account projection requires its selected arm")
    unique: dict[str, AcquisitionEvent] = {}
    for event in events:
        if event.event_id in unique and unique[event.event_id] != event:
            raise ValueError("event identity collision")
        unique[event.event_id] = event
    attempt_events: dict[str, str] = {}
    for event in unique.values():
        if event.attempt_id in attempt_events:
            raise ValueError("one physical attempt has multiple acquisition event identities")
        attempt_events[event.attempt_id] = event.event_id
    charge_ids: set[str] = set()
    opportunities: set[tuple[ObjectIdentity, ObjectIdentity, str]] = set()
    charged: list[AcquisitionEvent] = []
    for charge in charges:
        if charge.charge_id in charge_ids:
            raise ValueError("duplicate charge")
        charge_ids.add(charge.charge_id)
        event = unique.get(charge.event.object_id)
        if event is None or charge.event != identity(event, event.event_id):
            raise ValueError("charge event join differs")
        opportunity = (charge.event, charge.inquiry, charge.arm_id)
        if opportunity in opportunities:
            raise ValueError("duplicate full-charge opportunity")
        opportunities.add(opportunity)
        if account is not None:
            if (charge.inquiry != account.inquiry or charge.arm_id != account.arm_id
                    or charge.sequence_id != account.sequence_id
                    or charge.event not in account.events):
                raise ValueError("charge account inquiry/arm/sequence/event join differs")
            charged.append(event)
    if account is not None and {identity(e, e.event_id) for e in charged} != set(account.events):
        raise ValueError("full-charge account event census incomplete")
    selected = list(unique.values()) if arm_id is None else charged
    totals = []
    for field in ("cpu_seconds", "wall_seconds", "retained_bytes"):
        values = [getattr(event.cost, field) for event in selected]
        totals.append(None if any(value is None for value in values)
                      else sum(values, Decimal(0)))
    return InquiryCost(*totals)


@dataclass(frozen=True, slots=True)
class InquiryOutcomeChoice(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/kernel/inquiry-outcome-choice"
    outcome_id: str
    alternative_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        validate_stable_id(self.outcome_id)
        require_sorted_unique_strings(self.alternative_ids, field_name="alternative_ids", allow_empty=False)


@dataclass(frozen=True, slots=True)
class InquirySpecification(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/kernel/inquiry-specification"
    specification_id: str
    question: str
    explanations: tuple[str, ...]
    distinguishing_assessment: ObjectIdentity
    outcome_choices: tuple[InquiryOutcomeChoice, ...]
    endpoint: ScientificConditionScope
    receiver_risk: str
    predecessor_specification: ObjectIdentity | None = None

    def __post_init__(self) -> None:
        validate_stable_id(self.specification_id)
        for field in ("question", "receiver_risk"):
            validate_nonempty(getattr(self, field), field_name=field)
        if len(self.explanations) < 2 or len(set(self.explanations)) != len(self.explanations):
            raise ValueError("inquiry requires distinct competing explanations")
        for explanation in self.explanations:
            validate_nonempty(explanation, field_name="explanations")
        _ids(self.outcome_choices, "outcome_id", "outcome_choices")
        if not self.outcome_choices:
            raise ValueError("inquiry requires an outcome-to-choice map")


@dataclass(frozen=True, slots=True)
class InquiryEvidence(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/kernel/inquiry-evidence"
    evidence_id: str
    product: ObjectIdentity
    producing_receipt: ObjectIdentity | None
    scope: ScientificConditionScope
    role: ContributionRole
    independent_unit_ids: tuple[str, ...]
    nested_view_ids: tuple[str, ...]
    source_contract: ObjectIdentity | None = None
    evidence_ceiling: EvidenceCeiling = EvidenceCeiling.NON_PROMOTABLE
    outcome_access: OutcomeAccess = OutcomeAccess.DEVELOPMENT_VISIBLE
    visibility_ceiling: VisibilityCeiling = VisibilityCeiling.DEVELOPMENT_ONLY

    def __post_init__(self) -> None:
        validate_stable_id(self.evidence_id)
        if (self.producing_receipt is None) == (self.source_contract is None):
            raise ValueError("evidence needs exactly one receipt or source contract origin")
        if (self.evidence_ceiling is not EvidenceCeiling.NON_PROMOTABLE
                or self.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                or self.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
            raise ValueError("selected inquiry stock is exposed non-promotable development evidence")
        if self.role is ContributionRole.QUALIFIED_EVIDENTIAL_PARENT:
            raise ValueError("exposed development evidence cannot be a qualified evidential parent")
        if not isinstance(self.role, ContributionRole):
            raise ValueError("evidence role must be typed")
        for field in ("independent_unit_ids", "nested_view_ids"):
            require_sorted_unique_strings(getattr(self, field), field_name=field)


class InquiryAttemptStatus(StrEnum):
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    UNCERTAIN_CONTACT = "UNCERTAIN_CONTACT"
    NONATTEMPT = "NONATTEMPT"


@dataclass(frozen=True, slots=True)
class InquiryAttempt(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/kernel/inquiry-attempt"
    attempt_id: str
    operation: ObjectIdentity
    status: InquiryAttemptStatus
    receipt: ObjectIdentity | None
    products: tuple[ObjectIdentity, ...]
    reason: str

    def __post_init__(self) -> None:
        validate_stable_id(self.attempt_id)
        validate_nonempty(self.reason, field_name="reason")
        if not isinstance(self.status, InquiryAttemptStatus):
            raise ValueError("attempt status must be typed")
        _ids(self.products, "object_id", "products")
        if self.receipt is None:
            raise ValueError("every operational attempt requires authentic receipt or recovery-event witness")
        if self.status is not InquiryAttemptStatus.COMPLETED and self.products:
            raise ValueError("failed/blocked work cannot invent products")


@dataclass(frozen=True, slots=True)
class InquiryState(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/kernel/inquiry-state"
    state_id: str
    specification: ObjectIdentity
    information_cutoff: InformationCutoff
    stock: tuple[InquiryEvidence, ...]
    operational_census: tuple[InquiryAttempt, ...]
    previous_decisions: tuple[ObjectIdentity, ...]
    cost_events: tuple[AcquisitionEvent, ...]
    wave_count: int
    depth_count: int
    revision_parent: ObjectIdentity | None = None

    def __post_init__(self) -> None:
        validate_stable_id(self.state_id)
        if self.specification.object_schema != InquirySpecification.SCHEMA:
            raise ValueError("state requires inquiry specification")
        for field, attribute in (("stock", "evidence_id"), ("operational_census", "attempt_id"),
                                 ("previous_decisions", "object_id"), ("cost_events", "event_id")):
            _ids(getattr(self, field), attribute, field)
        for field in ("wave_count", "depth_count"):
            _count(getattr(self, field), field)
        attempts = {attempt.attempt_id: attempt for attempt in self.operational_census}
        event_attempt_ids = [event.attempt_id for event in self.cost_events]
        if len(set(event_attempt_ids)) != len(event_attempt_ids) or set(event_attempt_ids) != set(attempts):
            raise ValueError("complete cost census requires exactly one event per operational attempt")
        for event in self.cost_events:
            attempt = attempts.get(event.attempt_id)
            if attempt is None or attempt.receipt != event.receipt:
                raise ValueError("cost event requires exact census attempt/receipt")


@dataclass(frozen=True, slots=True)
class InquiryChoiceEvaluation(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/kernel/inquiry-choice-evaluation"
    alternative_id: str
    eligible: bool
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        validate_stable_id(self.alternative_id)
        if type(self.eligible) is not bool:
            raise ValueError("eligible must be boolean")
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes")
        if self.eligible == bool(self.reason_codes):
            raise ValueError("eligibility requires consistent reasons")


@dataclass(frozen=True, slots=True)
class InquiryDecision(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/kernel/inquiry-decision"
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
    evaluations: tuple[InquiryChoiceEvaluation, ...]
    remaining_cost: InquiryCost

    def __post_init__(self) -> None:
        for value in (self.decision_id, self.selected_alternative_id, self.actor_id, self.outcome_id):
            validate_stable_id(value)
        if type(self.human_directed) is not bool:
            raise ValueError("human_directed must be boolean")
        _ids(self.evaluations, "alternative_id", "evaluations")


@dataclass(frozen=True, slots=True)
class InquirySuccessorIntent(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/kernel/inquiry-successor-intent"
    intent_id: str
    decision: ObjectIdentity
    specification: ObjectIdentity
    state: ObjectIdentity
    menu: ObjectIdentity
    policy: ObjectIdentity
    alternative_id: str
    draft: ObjectIdentity
    configuration: ObjectIdentity
    input_origins: ObjectIdentity
    endpoint: ScientificConditionScope
    capability_id: str

    def __post_init__(self) -> None:
        for value in (self.intent_id, self.alternative_id):
            validate_stable_id(value)
        validate_inquiry_capability_id(self.capability_id)

