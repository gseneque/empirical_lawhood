# SPDX-License-Identifier: MPL-2.0
"""Retain complete shared decision packets and their exact frozen Rubisco policy.

Structural joins here do not establish current access. The API always uses the
ordinary current-source inquiry reader before constructing these operands.
No historical-read escape or timestamp-only prospective claim is supplied.
"""

from dataclasses import dataclass
from decimal import localcontext
from typing import ClassVar

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_inquiry import InquirySuccessorIntent
from empirical_lawhood.science.inquiry.recursive_inquiry_policy import RobustInquirySpecification, WorkBoundInquiryDecision, WorkBoundInquiryState
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.design.campaigns import CampaignSpec, DecisionRight
from empirical_lawhood.design.recursive_inquiry import InquiryAction
from empirical_lawhood.design.recursive_inquiry_policy import RobustInquiryMenu, RobustInquiryPolicy, validate_robust_inquiry_join
from empirical_lawhood.execution.recursive_handoff import RecursiveImplementationBinding, RecursiveWaveMember
from empirical_lawhood.execution.recursive_inquiry import InquiryStateSources, WorkBoundInquiryDecisionPacket
from empirical_lawhood.domains.rubisco.rubisco_response.finite_policy import FiniteResponsePolicy, _cost_precision, finite_policy_specification, policy_requirements
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact


@dataclass(frozen=True, slots=True)
class RetainedPolicyDecision(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/retained-policy-decision"
    selection: FiniteResponsePolicy
    packet: WorkBoundInquiryDecisionPacket
    specification: RobustInquirySpecification
    state: WorkBoundInquiryState
    sources: InquiryStateSources
    menu: RobustInquiryMenu
    policy: RobustInquiryPolicy
    campaign: CampaignSpec
    right: DecisionRight
    decision: WorkBoundInquiryDecision
    implementation: RecursiveImplementationBinding
    intent: InquirySuccessorIntent | None = None

    def __post_init__(self):
        for value, kind in ((self.selection, FiniteResponsePolicy), (self.packet, WorkBoundInquiryDecisionPacket),
                (self.specification, RobustInquirySpecification), (self.state, WorkBoundInquiryState),
                (self.sources, InquiryStateSources), (self.menu, RobustInquiryMenu), (self.policy, RobustInquiryPolicy),
                (self.campaign, CampaignSpec), (self.right, DecisionRight), (self.decision, WorkBoundInquiryDecision),
                (self.implementation, RecursiveImplementationBinding)):
            exact(value, kind)
        if self.intent is not None:
            exact(self.intent, InquirySuccessorIntent)
        records = {"specification.json": self.specification, "state.json": self.state, "sources.json": self.sources,
            "menu.json": self.menu, "policy.json": self.policy, "campaign.json": self.campaign, "right.json": self.right,
            "decision.json": self.decision, "implementation.json": self.implementation}
        if self.intent is not None:
            records["intent.json"] = self.intent
        expected = tuple(RecursiveWaveMember(name,
            ObjectIdentity.from_record("inquiry-member." + name.removesuffix(".json"), record), len(record.canonical_bytes()))
            for name, record in sorted(records.items()))
        if self.packet.members != expected:
            raise ValueError("retained decision changes its original complete packet bytes")
        assumption_id = "assumption." + self.selection.policy_id + ".finite-order"
        if (len(self.policy.assumptions) != 1 or self.policy.assumptions[0].assumption_id != assumption_id
                or self.policy.assumptions[0].reason != self.selection.canonical_bytes().decode("utf-8").removesuffix("\n")):
            raise ValueError("retained decision changes the original frozen finite-policy selection")
        base = policy_requirements(self.selection)[1]
        expected_specification = finite_policy_specification(self.selection,
            distinguishing_assessment=self.specification.distinguishing_assessment,
            required_claims=self.specification.target.required_claims,
            supporting_connections=tuple(row for row in self.specification.connections if row not in base))
        if self.specification != expected_specification:
            raise ValueError("retained decision substitutes its Rubisco target or complete scientific prerequisites")
        checkpoints = self.selection.sequential.checkpoints
        index = len(self.state.previous_decisions)
        if index >= len(checkpoints) or checkpoints[index].information_cutoff != self.state.information_cutoff:
            raise ValueError("retained decision is outside the frozen ordered pre-action checkpoints")
        with localcontext() as context:
            context.prec = _cost_precision(self.state, self.selection, self.menu.alternatives)
            validate_robust_inquiry_join(decision=self.decision, specification=self.specification, state=self.state,
                menu=self.menu, policy=self.policy, campaign=self.campaign, right=self.right, intent=self.intent,
                validate_authority=False)
        selected = self.selected
        if (selected.action is InquiryAction.ACT) != (self.intent is not None):
            raise ValueError("retained decision drops its actual successor intent")
        if selected.alternative_id not in self.selection.alternative_ids or selected.action is InquiryAction.STOP:
            raise ValueError("finite Rubisco policy cannot invent an action or close the scientific target")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.decision.decision_id, self.decision)

    @property
    def selected(self):
        return next(row for row in self.menu.alternatives if row.alternative_id == self.decision.selected_alternative_id)

    @property
    def action(self):
        if self.selected.action is InquiryAction.HOLD:
            return "HOLD"
        return "REDUCED" if self.selected.alternative_id == "reduced" else "REFERENCE" if self.selected.alternative_id == "reference" else "REFINE"


def retained_policy_decision(selection, packet, records):
    """Compose the complete result of read_inquiry_decision; open no paths."""
    required = {"specification.json", "state.json", "sources.json", "menu.json", "policy.json", "campaign.json", "right.json",
        "decision.json", "implementation.json"}
    if set(records) not in (required, required | {"intent.json"}):
        raise ValueError("retained decision needs the exact shared packet member census")
    return RetainedPolicyDecision(selection, packet, *(records[name + ".json"] for name in
        ("specification", "state", "sources", "menu", "policy", "campaign", "right", "decision", "implementation")), records.get("intent.json"))
