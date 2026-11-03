# SPDX-License-Identifier: MPL-2.0
"""Exact custody witnesses for a retained inquiry decision."""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_inquiry import InquirySpecification, InquiryState
from empirical_lawhood.kernel.recursive_inquiry_policy import RobustInquirySpecification, WorkBoundInquiryState
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord, require_sorted_unique_ids, require_sorted_unique_strings,
    validate_relative_locator, validate_stable_id,
)
from .recursive_handoff import RecursiveWaveMember
from empirical_lawhood.planning.campaigns import CampaignSpec, DecisionRight
from empirical_lawhood.planning.recursive_inquiry import InquiryMenu, InquiryPolicy
from empirical_lawhood.planning.recursive_inquiry_policy import RobustInquiryMenu, RobustInquiryPolicy


@dataclass(frozen=True, slots=True)
class InquiryWaveSource(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/runtime/inquiry-wave-source"
    relative_path: str
    packet: ObjectIdentity
    include_products: bool

    def __post_init__(self):
        validate_relative_locator(self.relative_path)
        if type(self.include_products) is not bool:
            raise ValueError("inquiry wave source needs explicit product access")


@dataclass(frozen=True, slots=True)
class InquiryStateSources(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/runtime/inquiry-state-sources"
    waves: tuple[InquiryWaveSource, ...]
    measured_event_paths: tuple[str, ...] = ()
    previous_decision_paths: tuple[str, ...] = ()

    def __post_init__(self):
        require_sorted_unique_ids(self.waves, attribute="relative_path", field_name="waves")
        for name in ("measured_event_paths", "previous_decision_paths"):
            paths = getattr(self, name)
            require_sorted_unique_strings(paths, field_name=name)
            for path in paths:
                validate_relative_locator(path)


@dataclass(frozen=True, slots=True)
class InquiryDecisionPacket(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/runtime/inquiry-decision-packet"
    packet_id: str
    members: tuple[RecursiveWaveMember, ...]

    def __post_init__(self):
        validate_stable_id(self.packet_id)
        require_sorted_unique_ids(self.members, attribute="filename", field_name="members")
        names = {member.filename for member in self.members}
        required = {"specification.json", "state.json", "sources.json", "menu.json",
                    "policy.json", "campaign.json", "right.json", "decision.json", "implementation.json"}
        if not required <= names or names - required - {"intent.json"}:
            raise ValueError("inquiry decision packet changes its exact member census")


@dataclass(frozen=True, slots=True)
class InquirySuccessorAdmission(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/runtime/inquiry-successor-admission"
    decision_relative_path: str
    decision_packet: ObjectIdentity
    intent: ObjectIdentity
    authored_wave: ObjectIdentity

    def __post_init__(self):
        validate_relative_locator(self.decision_relative_path)


@dataclass(frozen=True, slots=True)
class InquiryDecisionRequest(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/runtime/inquiry-decision-request"
    specification: InquirySpecification
    state: InquiryState
    sources: InquiryStateSources
    menu: InquiryMenu
    policy: InquiryPolicy
    campaign: CampaignSpec
    right: DecisionRight
    actor_id: str
    human_choice: str | None = None

    def __post_init__(self):
        validate_stable_id(self.actor_id)
        if self.human_choice is not None:
            validate_stable_id(self.human_choice)


@dataclass(frozen=True, slots=True)
class RobustInquiryDecisionPacket(InquiryDecisionPacket):
    """Same closed custody census, with version-two inquiry policy members."""
    VERSION: ClassVar[str] = "2.0.0"


@dataclass(frozen=True, slots=True)
class WorkBoundInquiryDecisionPacket(InquiryDecisionPacket):
    """Current robust policy members with explicit version-two state custody."""
    VERSION: ClassVar[str] = "3.0.0"


@dataclass(frozen=True, slots=True)
class RobustInquiryDecisionRequest(CanonicalRecord):
    SCHEMA: ClassVar[str] = InquiryDecisionRequest.SCHEMA
    VERSION: ClassVar[str] = "2.0.0"
    specification: RobustInquirySpecification
    state: InquiryState
    sources: InquiryStateSources
    menu: RobustInquiryMenu
    policy: RobustInquiryPolicy
    campaign: CampaignSpec
    right: DecisionRight
    actor_id: str
    human_choice: str | None = None
    human_reason: str | None = None

    def __post_init__(self):
        from empirical_lawhood.kernel.serialization import validate_nonempty
        validate_stable_id(self.actor_id)
        if (self.human_choice is None) != (self.human_reason is None):
            raise ValueError("human direction requires its choice and reason")
        if self.human_choice is not None:
            validate_stable_id(self.human_choice)
            validate_nonempty(self.human_reason, field_name="human_reason")


@dataclass(frozen=True, slots=True)
class WorkBoundInquiryDecisionRequest(RobustInquiryDecisionRequest):
    """Explicit successor envelope; version-two request bytes retain their type."""
    VERSION: ClassVar[str] = "3.0.0"
    state: WorkBoundInquiryState


from empirical_lawhood.kernel.recursive_requirements import ContributionRole, ScientificConditionScope


@dataclass(frozen=True, slots=True)
class InquiryEvidenceBinding(CanonicalRecord):
    """Code-owned scientific meaning; receipt and origin authentication stay in API."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/runtime/inquiry-evidence-binding'
    binding_id: str
    content_sha256: str
    scope: ScientificConditionScope
    role: ContributionRole
    independent_unit_ids: tuple[str, ...]
    nested_view_ids: tuple[str, ...]

    def __post_init__(self):
        from empirical_lawhood.kernel.serialization import validate_sha256
        validate_stable_id(self.binding_id)
        validate_sha256(self.content_sha256)
        if type(self.scope) is not ScientificConditionScope or not isinstance(self.role, ContributionRole):
            raise ValueError('inquiry evidence meaning requires exact typed scientific scope and role')
        require_sorted_unique_strings(self.independent_unit_ids, field_name='independent_unit_ids')
        require_sorted_unique_strings(self.nested_view_ids, field_name='nested_view_ids')
