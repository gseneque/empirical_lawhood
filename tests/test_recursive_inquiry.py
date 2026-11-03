# SPDX-License-Identifier: MPL-2.0
"""Independent arithmetic and adversarial joins for the bounded inquiry contract."""
from dataclasses import replace
from decimal import Decimal as D

import pytest

from empirical_lawhood.kernel.authority import AuthorityAction, ResourceBudget
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_inquiry import (
    AcquisitionEvent, InquiryAttempt, InquiryAttemptStatus, InquiryCharge, InquiryCost,
    InquiryCostAccount, InquiryCostCategory, InquiryEvidence, InquiryOutcomeChoice, InquirySpecification,
    InquiryState, identity, summarize_cost,
)
from empirical_lawhood.kernel.recursive_requirements import ContributionRole, ScientificConditionScope
from empirical_lawhood.kernel.status import LifecycleStatus
from empirical_lawhood.kernel.time import CausalPhase, InformationCutoff
from empirical_lawhood.planning.campaigns import (
    CampaignLane, CampaignNode, CampaignNodeKind, CampaignSpec, DecisionRight,
)
from empirical_lawhood.planning.recursive_inquiry import (
    InquiryAction, InquiryAlternative, InquiryMenu, InquiryPolicy, choose_inquiry,
    make_successor_intent, validate_inquiry_join, validate_inquiry_revision,
)


def obj(name):
    return ObjectIdentity(name, "empirical-lawhood/testing/operand", "1.0.0", "a" * 64)


def cost(cpu="0", wall="0", size="0"):
    return InquiryCost(*(None if v is None else D(v) for v in (cpu, wall, size)))


@pytest.fixture
def episode():
    cutoff = InformationCutoff("cutoff", "clock", CausalPhase.PRE_ACTION, D(0))
    scope = ScientificConditionScope("system", "world", "source", ("quantity",),
                                    ("SI",), "receiver", "clock", "exact endpoint",
                                    information_cutoff=cutoff, available_by=D(0))
    spec = InquirySpecification("spec", "Does local supply work?", ("usable", "invalid"),
                                obj("assessment"),
                                (InquiryOutcomeChoice("missing", ("hold", "stop")),
                                 InquiryOutcomeChoice("useful", ("act-a", "act-b", "stop"))),
                                scope, "bounded exposed analytical use")
    evidence = InquiryEvidence("stock", obj("source-product"), None, scope,
                               ContributionRole.RETAINED_ANALYSIS_INPUT, (), ("view-a", "view-b"),
                               source_contract=obj("source-contract"))
    state = InquiryState("state", identity(spec, "spec"), cutoff, (evidence,), (), (), (), 0, 0)
    sid, tid = identity(spec, "spec"), identity(state, "state")
    alternatives = tuple(InquiryAlternative(a, sid, tid, InquiryAction.ACT, ("useful",),
                                            ("stock",), D(2), cost("1", "2", "3"),
                                            obj("draft"), obj("config"), obj("origins"), "capability")
                         for a in ("act-a", "act-b")) + (
        InquiryAlternative("hold", sid, tid, InquiryAction.HOLD, ("missing",), (), D(1), cost()),
        InquiryAlternative("stop", sid, tid, InquiryAction.STOP, ("missing", "useful"), (), D(0), cost()))
    menu = InquiryMenu("menu", sid, tid, alternatives)
    policy = InquiryPolicy("policy", sid, cost("10", "20", "30"), 4, 2, 3)
    right = DecisionRight("right", AuthorityAction.READ_ONLY_EXPLORATION, "actor", "authority", True)
    node = CampaignNode("root", CampaignNodeKind.EVIDENCE_SNAPSHOT, CampaignLane.EXPLORATORY,
                        obj("initial"), (), LifecycleStatus.ACTIVE)
    campaign = CampaignSpec("campaign", "bounded inquiry", ("system",), ("world",), ("claim",),
                            ResourceBudget(1, 1024, 0, 120, 1024, 1024), obj("authority"),
                            (right,), (node,), ("root",), ("root",), (), LifecycleStatus.ACTIVE)
    return dict(specification=spec, state=state, menu=menu, policy=policy, campaign=campaign,
                right=right, actor_id="actor", outcome_id="useful", decision_id="decision")


def test_policy_tie_zero_novelty_and_human_choice(episode):
    decision = choose_inquiry(**episode)
    assert decision.selected_alternative_id == "act-a"
    assert decision.remaining_cost == cost("9", "18", "27")
    assert choose_inquiry(**episode, human_choice="act-b").human_directed
    assert choose_inquiry(**dict(episode, outcome_id="missing")).selected_alternative_id == "hold"
    with pytest.raises(ValueError, match="human choice"):
        choose_inquiry(**episode, human_choice="hold")
    with pytest.raises(ValueError, match="actor/right"):
        choose_inquiry(**dict(episode, actor_id="someone-else"))


@pytest.mark.parametrize("defect", ("system", "world", "policy", "reveal", "repository",
                                    "terminal", "superseded", "invalidated"))
def test_decision_provenance_rejects_unrelated_or_inactive_authority(episode, defect):
    campaign, right = episode["campaign"], episode["right"]
    if defect == "system":
        campaign = replace(campaign, system_ids=("unrelated-system",))
    elif defect == "world":
        campaign = replace(campaign, world_ids=("unrelated-world",))
    elif defect == "policy":
        right = replace(right, authority_policy_id="unrelated-policy")
    elif defect in ("reveal", "repository"):
        right = replace(right, action=(AuthorityAction.EVALUATOR_REVEAL if defect == "reveal"
                                       else AuthorityAction.REPOSITORY_IMPLEMENTATION))
    else:
        campaign = replace(campaign, lifecycle_status=LifecycleStatus[defect.upper()])
    campaign = replace(campaign, decision_rights=(right,))
    with pytest.raises(ValueError, match="campaign|decision action"):
        choose_inquiry(**dict(episode, campaign=campaign, right=right))


def test_invalid_historical_campaign_remains_readable_without_fresh_admission(episode):
    original = choose_inquiry(**episode)
    campaign = replace(episode["campaign"], system_ids=("unrelated-system",))
    historical = replace(original, campaign=identity(campaign, campaign.campaign_id))
    retained_bytes = historical.canonical_bytes()
    args = {key: value for key, value in episode.items()
            if key not in ("decision_id", "actor_id", "outcome_id")}
    args["campaign"] = campaign
    validate_inquiry_join(decision=historical, **args, historical=True)
    assert historical.canonical_bytes() == retained_bytes
    with pytest.raises(ValueError, match="system/world"):
        validate_inquiry_join(decision=historical, **args)


def test_physical_dedup_full_charge_repeat_and_nested_units(episode):
    receipt = obj("receipt-a")
    event = AcquisitionEvent("event-a", "attempt-a", receipt, cost("2", "3", "5"))
    repeat = AcquisitionEvent("event-b", "attempt-b", obj("receipt-b"), cost("7", "11", "13"))
    inquiry = identity(episode["specification"], "spec")
    charges = tuple(InquiryCharge(f"charge-{i}", identity(event, "event-a"), inquiry,
                                 arm, InquiryCostCategory.CONSTRUCTION, "later-1")
                    for i, arm in enumerate(("arm-a", "arm-b")))
    assert summarize_cost((event, event, repeat), charges) == cost("9", "14", "18")
    for charge in charges:
        account = InquiryCostAccount("account." + charge.arm_id, inquiry, charge.arm_id,
                                     "later-1", (charge.event,))
        assert summarize_cost((event, repeat), (charge,), arm_id=charge.arm_id,
                              account=account) == cost("2", "3", "5")
    assert episode["state"].stock[0].independent_unit_ids == ()
    assert len(episode["state"].stock[0].nested_view_ids) == 2
    assert summarize_cost((replace(event, cost=cost(None, "3", "5")), repeat)).cpu_seconds is None
    with pytest.raises(ValueError, match="collision"):
        summarize_cost((event, replace(event, cost=cost("4", "3", "5"))))
    with pytest.raises(ValueError, match="join"):
        summarize_cost((event,), (replace(charges[0], event=replace(charges[0].event, object_fingerprint="b" * 64)),))


def with_census(episode, expense):
    state = episode["state"]
    receipt = obj("receipt")
    attempt = InquiryAttempt("attempt", obj("operation"), InquiryAttemptStatus.FAILED, receipt, (), "failed")
    event = AcquisitionEvent("event", "attempt", receipt, expense)
    state = replace(state, operational_census=(attempt,), cost_events=(event,))
    menu = replace(episode["menu"], state=identity(state, "state"), alternatives=tuple(
        replace(a, state=identity(state, "state")) for a in episode["menu"].alternatives))
    return dict(episode, state=state, menu=menu)


@pytest.mark.parametrize("expense", [cost(None, "1", "1"), cost("10", "20", "30")])
def test_unknown_and_overbudget_block_act_keep_stop(episode, expense):
    altered = with_census(episode, expense)
    decision = choose_inquiry(**altered)
    assert decision.selected_alternative_id == "stop"
    assert not decision.evaluations[0].eligible
    if expense.cpu_seconds is None:
        assert decision.remaining_cost.cpu_seconds is None


def test_unrestricted_policy_retains_unknown_costs_and_allows_act(episode):
    altered = with_census(episode, cost(None, None, None))
    state = replace(altered["state"], wave_count=40, depth_count=40)
    menu = replace(altered["menu"], state=identity(state, "state"), alternatives=tuple(
        replace(a, state=identity(state, "state"), expense_bound=cost(None, None, None))
        for a in altered["menu"].alternatives))
    policy = replace(altered["policy"], max_cost=cost(None, None, None),
                     max_operations=None, max_waves=None, max_depth=None)
    original = state.canonical_bytes()
    decision = choose_inquiry(**dict(altered, state=state, menu=menu, policy=policy))
    assert decision.selected_alternative_id == "act-a"
    assert decision.remaining_cost == cost(None, None, None)
    assert state.canonical_bytes() == original
    assert summarize_cost(state.cost_events) == cost(None, None, None)


def test_partially_unrestricted_policy_checks_only_selected_allowances(episode):
    altered = with_census(episode, cost(None, "1", "1"))
    policy = replace(altered["policy"], max_cost=cost(None, "3", "4"))
    decision = choose_inquiry(**dict(altered, policy=policy))
    assert decision.selected_alternative_id == "act-a"
    assert decision.remaining_cost == cost(None, "0", "0")
    over = replace(policy, max_cost=cost(None, "2", "4"))
    assert choose_inquiry(**dict(altered, policy=over)).selected_alternative_id == "stop"
    # A finite operation ceiling still applies independently of unrestricted cost.
    finite_operations = replace(policy, max_operations=1)
    assert choose_inquiry(**dict(altered, policy=finite_operations)).selected_alternative_id == "stop"


def test_policy_roundtrips_finite_and_unrestricted_records(episode):
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    finite = episode["policy"]
    for policy in (finite, replace(finite, max_cost=cost(None, None, None),
                                  max_operations=None, max_waves=None, max_depth=None)):
        raw = policy.canonical_bytes()
        decoded = decode_canonical_bytes(raw, InquiryPolicy, maximum_bytes=len(raw))
        assert decoded == policy
        assert decoded.canonical_bytes() == raw


@pytest.mark.parametrize("part", ["specification", "state", "menu", "policy", "right", "endpoint", "draft", "configuration", "input_origins", "intent"])
def test_mutations_refuse_join_before_effect(episode, part):
    decision = choose_inquiry(**episode)
    intent = make_successor_intent(intent_id="intent", decision=decision,
                                   specification=episode["specification"], menu=episode["menu"])
    args = {k: v for k, v in episode.items() if k not in {"actor_id", "outcome_id", "decision_id"}}
    if part == "specification":
        args[part] = replace(args[part], question="A substituted question?")
    elif part == "state":
        args[part] = replace(args[part], wave_count=1)
    elif part == "menu":
        args[part] = replace(args[part], menu_id="other-menu")
    elif part == "policy":
        args[part] = replace(args[part], max_depth=4)
    elif part == "right":
        args[part] = replace(args[part], delegated=False)
    elif part == "endpoint":
        intent = replace(intent, endpoint=replace(intent.endpoint, receiver_id="other-receiver"))
    elif part == "intent":
        intent = replace(intent, capability_id="other-capability")
    else:
        intent = replace(intent, **{part: obj("other")})
    with pytest.raises(ValueError):
        validate_inquiry_join(decision=decision, intent=intent, **args)


def test_revision_preserves_failures_unknowns_and_exposure(episode):
    prior = with_census(episode, cost(None, "1", "1"))
    old_spec, old_state = prior["specification"], prior["state"]
    spec = replace(old_spec, specification_id="revision", predecessor_specification=identity(old_spec, "spec"))
    state = replace(old_state, state_id="revision-state", specification=identity(spec, "revision"),
                    revision_parent=identity(old_state, "state"))
    policy = replace(prior["policy"], specification=state.specification)
    args = dict(previous_specification=old_spec, previous_state=old_state,
                specification=spec, state=state, policy=policy)
    validate_inquiry_revision(**args)
    with pytest.raises(ValueError, match="lost"):
        validate_inquiry_revision(**dict(args, state=replace(state, operational_census=(), cost_events=())))
    for cutoff in (replace(state.information_cutoff, phase=CausalPhase.PREPARATION),
                   replace(state.information_cutoff, includes_coordinate=False)):
        with pytest.raises(ValueError, match="cutoff"):
            validate_inquiry_revision(**dict(args, state=replace(state, information_cutoff=cutoff)))


def test_cutoff_missing_stock_and_finite_boundaries(episode):
    with pytest.raises(ValueError, match="cutoff"):
        state = replace(episode["state"], information_cutoff=replace(episode["state"].information_cutoff, coordinate=D(-1)))
        menu = replace(episode["menu"], state=identity(state, "state"), alternatives=tuple(
            replace(a, state=identity(state, "state")) for a in episode["menu"].alternatives))
        choose_inquiry(**dict(episode, state=state, menu=menu))
    policy = replace(episode["policy"], max_waves=0)
    assert choose_inquiry(**dict(episode, policy=policy)).selected_alternative_id == "stop"
    with pytest.raises(ValueError):
        replace(policy, max_waves=True)
    assert replace(policy, max_cost=cost(None, "2", "3")).max_cost.cpu_seconds is None


@pytest.mark.parametrize("status", list(InquiryAttemptStatus))
def test_every_attempt_requires_cost_event_and_authentic_witness(episode, status):
    witness = obj("recovery-event")
    attempt = InquiryAttempt("attempt", obj("operation"), status, witness, (), "retained work")
    event = AcquisitionEvent("event", "attempt", witness, cost(None, None, None))
    state = replace(episode["state"], operational_census=(attempt,), cost_events=(event,))
    assert summarize_cost(state.cost_events).cpu_seconds is None
    with pytest.raises(ValueError, match="complete cost census"):
        replace(state, cost_events=())
    with pytest.raises(ValueError, match="witness"):
        replace(attempt, receipt=None)
    second_attempt = replace(attempt, attempt_id="attempt-b")
    second_event = replace(event, event_id="event-b", attempt_id="attempt-b")
    state = replace(state, operational_census=(attempt, second_attempt), cost_events=(event, second_event))
    with pytest.raises(ValueError, match="complete cost census"):
        replace(state, cost_events=(second_event,))


def test_qualified_parent_refuses_exposed_stock(episode):
    with pytest.raises(ValueError, match="qualified evidential parent"):
        replace(episode["state"].stock[0], role=ContributionRole.QUALIFIED_EVIDENTIAL_PARENT)


def test_full_charge_semantic_duplication_and_foreign_account(episode):
    event = AcquisitionEvent("event", "attempt", obj("receipt"), cost("2", "3", "5"))
    inquiry = identity(episode["specification"], "spec")
    charge = InquiryCharge("charge", identity(event, "event"), inquiry, "arm",
                           InquiryCostCategory.CONSTRUCTION, "later-1")
    account = InquiryCostAccount("account", inquiry, "arm", "later-1", (charge.event,))
    for altered in (replace(charge, charge_id="renamed"),
                    replace(charge, charge_id="renamed", category=InquiryCostCategory.COMPATIBILITY),
                    replace(charge, charge_id="renamed", sequence_id="later-2")):
        with pytest.raises(ValueError, match="duplicate full-charge"):
            summarize_cost((event,), (charge, altered))
    for altered in (replace(charge, inquiry=replace(inquiry, object_fingerprint="b" * 64)),
                    replace(charge, sequence_id="later-2"), replace(charge, arm_id="other")):
        with pytest.raises(ValueError, match="account"):
            summarize_cost((event,), (altered,), arm_id="arm", account=account)
    with pytest.raises(ValueError, match="frozen account"):
        summarize_cost((event,), (charge,), arm_id="arm")
    with pytest.raises(ValueError, match="incomplete"):
        summarize_cost((event,), (), arm_id="arm", account=account)
