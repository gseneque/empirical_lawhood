# SPDX-License-Identifier: MPL-2.0
"""Independent expected decisions for exposed target/prerequisite inquiry cases.

These deliberately exposed records are conformance examples. Source bytes are
bound to maintained domain selections; unsigned examples create no scientific
qualification, native authority or fresh experimental units.
"""

from dataclasses import fields, replace
from decimal import Decimal as D
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace as N

import pytest

from empirical_lawhood.kernel.authority import AuthorityAction, ResourceBudget
from empirical_lawhood.kernel.evidence import ClaimSpec
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_inquiry import (
    AcquisitionEvent, InquiryAttempt, InquiryAttemptStatus, InquiryCost,
    InquiryEvidence, InquiryState, identity,
)
from empirical_lawhood.kernel.recursive_inquiry_policy import (
    CompletedInquiryWork, InquiryClaimFinding, InquiryCriterionAssessment,
    InquiryEvidenceNeed, InquiryObservation, InquiryOutcomeMap, InquiryPolicyAssumption,
    InquiryQuestionKind, InquiryRequirementFinding, InquiryStopScope, InquiryTarget,
    InquiryTargetFrontier, RobustChoiceStatus, RobustInquirySpecification,
    ScientificInquiryWork, ScientificOutcomeKind,
    InquiryAttemptWorkBinding, WorkBoundInquiryState,
)
from empirical_lawhood.kernel.recursive_requirements import (
    AssessmentDisposition as A, AssessmentPhase, ConditionRole, ContributionRole,
    RequirementSupplyAssessment, ScientificConditionScope, ScientificConnectionSpec,
    ScientificRequirementSpec,
)
from empirical_lawhood.kernel.status import LifecycleStatus
from empirical_lawhood.kernel.time import CausalPhase, InformationCutoff
from empirical_lawhood.planning.campaigns import (
    CampaignLane, CampaignNode, CampaignNodeKind, CampaignSpec, DecisionRight,
)
from empirical_lawhood.planning.recursive_authoring import SupplierProposal
from empirical_lawhood.planning.recursive_inquiry import InquiryAction
from empirical_lawhood.planning.recursive_inquiry_policy import (
    IncomparableResolution, InquiryAlternativeKind, InquiryCriterionRole,
    InquiryCriterionRule, InquiryOrdering, RobustInquiryMenu, RobustInquiryPolicy,
    TargetDirectedAlternative, choose_robust_inquiry, evaluate_robust_inquiry,
    make_robust_successor_intent, validate_robust_inquiry_join,
    uncertain_contact_requires_recovery,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATHS = {
    "battery": "programmes/energy/battery-charging/records/battery-thermal-inquiry-selection.md",
    "rubisco": "programmes/biology/photosynthesis/records/rubisco-insilico-dynamics-selection.md",
    "matrix": "programmes/foundations/emergent-structure/records/matrix-programme.md",
}
DOMAIN_QUESTIONS = {
    "battery": (
        "Supply numerically warranted LGM50 charging knowledge for separate 20 C use and 30 C reuse",
        "All nine reference comparisons missed the unchanged 1 s, 1 mV and 0.01 K precision gates",
        "Independently vary localization, mesh and solver tolerance with fixed SOC, temperature and current preparations",
        "Full current-integral, event-clock, voltage, temperature and state disagreement census",
        "An independently admitted thermal supplier can support the later 20 C charging decision",
    ),
    "rubisco": (
        "Investigate one realized enzyme meeting both maize turnover and Gp specificity endpoints",
        "Authentic inhibited L8S8 source coordinates do not yet independently qualify full matched WT/I95M preparation",
        "Independently parse original 1BWV/3ZXW assembly operators, complete sequence maps and site neighborhoods",
        "All eight Gp linear I95/author I112 joins, full Te V98 donor context, missing atoms and M1/V1 views",
        "Admitted matched preparation can support the Te P415A WT/V98M and Gp WT/I95M dynamics discriminator",
    ),
    "matrix": (
        "Supply prospectively warranted native response and useful-lifetime knowledge from admitted matrix factors",
        "Scalar detector or recurrence success alone does not admit a parameter-consistent factor response instrument",
        "Independently assess factor admission and native finite-action response against the committed origin-only predictor",
        "Factor/frame source identity, complete root/branch census, native response error and independent falsifier",
        "An admitted source-bound response instrument enables prospective lifetime calibration",
    ),
}


def obj(name, schema="empirical-lawhood/testing/exposed-operand", content="exposed"):
    return ObjectIdentity(name, schema, "1.0.0", sha256(content.encode()).hexdigest())


def cost(cpu=None, wall=None, retained=None):
    return InquiryCost(*(None if value is None else D(value) for value in (cpu, wall, retained)))


def rebound(case, **changes):
    """Change a canonical owner then reconstruct exact state/menu dependent joins."""
    values = vars(case).copy()
    values.update(changes)
    sid = identity(values["specification"], values["specification"].specification_id)
    state = replace(values["state"], specification=sid)
    tid = identity(state, state.state_id)
    menu = values["menu"]
    menu = replace(menu, specification=sid, state=tid,
                   alternatives=tuple(replace(row, specification=sid, state=tid) for row in menu.alternatives),
                   observation=replace(menu.observation, specification=sid))
    policy = replace(values["policy"], specification=sid)
    return N(**dict(values, state=state, menu=menu, policy=policy))


def policy_case(domain="battery", *, outcome=ScientificOutcomeKind.UNEVALUABLE):
    original = (ROOT / SOURCE_PATHS[domain]).read_bytes()
    source = ObjectIdentity("source." + domain, "empirical-lawhood/testing/exposed-source", "1.0.0", sha256(original).hexdigest())
    cutoff = InformationCutoff("cutoff.exposed", "clock.exposed", CausalPhase.POST_OUTCOME, D(1))
    scope = ScientificConditionScope(
        "system." + domain, "world.exposed." + domain, source.object_id,
        ("target-response",), ("declared-native-unit",), "receiver." + domain,
        "clock.exposed", "Exact exposed domain selection; no new qualification",
        source_config_sha256=source.object_fingerprint, instance_id="instance." + domain,
        information_cutoff=cutoff, available_by=D(1),
    )
    target_purpose, retained_finding, next_question, observable, enabled_capability = DOMAIN_QUESTIONS[domain]
    condition = ScientificRequirementSpec(
        "condition", "use.target", ConditionRole.EVIDENTIAL,
        target_purpose,
        "Independent procedure, instance, admission and joined-use assessment",
        scope, "assess.condition", "The independent receiver refuses failed precision or preparation",
        (ContributionRole.RETAINED_ANALYSIS_INPUT,), ("instrument",),
    )
    instrument = ScientificRequirementSpec(
        "instrument", "supply.condition", ConditionRole.INFORMATIONAL,
        next_question,
        observable,
        scope, "assess.instrument", "Independent source/numerical check disagrees",
        (ContributionRole.RETAINED_ANALYSIS_INPUT,),
    )
    connection = ScientificConnectionSpec(
        "connection.condition", "condition", "supply.condition", "product.condition",
        "condition-input", "assess.condition", "claim.target",
        ContributionRole.RETAINED_ANALYSIS_INPUT, condition.falsifier,
    )
    iconnection = ScientificConnectionSpec(
        "connection.instrument", "instrument", "supply.instrument", "product.instrument",
        "instrument-input", "assess.instrument", "claim.instrument",
        ContributionRole.RETAINED_ANALYSIS_INPUT, instrument.falsifier,
    )
    claim = obj("claim.target", ClaimSpec.SCHEMA, domain + ": both declared target endpoints")
    target = InquiryTarget("target." + domain, target_purpose,
                           scope, ("condition",), (claim,), "Complete required claims in this same instance and receiver scope")
    outcomes = tuple(sorted((InquiryOutcomeMap(
        kind.value.lower(), kind, ("follow-parent", "hold", "investigate-prerequisite"),
        {
            ScientificOutcomeKind.POSITIVE: "Retain supplied components and assess actual later use",
            ScientificOutcomeKind.NEGATIVE: "Retain the negative and investigate the identified unsupported premise",
            ScientificOutcomeKind.UNEVALUABLE: "Retain uncertainty and acquire the independent numerical/structural discriminator",
            ScientificOutcomeKind.MISSING: "Find a supplier of the named missing prerequisite",
            ScientificOutcomeKind.OPERATIONAL_FAILURE: "Recover custody; failed execution supplies no scientific negative",
            ScientificOutcomeKind.UNCERTAIN_CONTACT: "Reconcile actual contact before any possible replay",
        }[kind], "An exact independently assessed contribution or an explicit remaining requirement",
    ) for kind in ScientificOutcomeKind), key=lambda row: row.outcome_id))
    spec = RobustInquirySpecification(
        "spec." + domain, "Which justified next inquiry enables the target condition?", (),
        obj("assessment.contract", content=domain + ": frozen independent assessment"), scope,
        "Exposed source-bound preparation and inference only", InquiryQuestionKind.SUPPLY,
        target, (condition, instrument), (connection, iconnection), "condition", outcomes,
        AuthorityAction.READ_ONLY_EXPLORATION,
    )
    sid = identity(spec, spec.specification_id)
    assessment = obj("assessment.actual", content=domain + ": exposed independently assessed retained uncertainty")
    source_evidence = InquiryEvidence("evidence.source", source, None, scope,
                                     ContributionRole.RETAINED_ANALYSIS_INPUT, (), (), source_contract=source)
    assessment_evidence = InquiryEvidence("evidence.assessment", assessment, None, scope,
                                         ContributionRole.RETAINED_ANALYSIS_INPUT, (), (), source_contract=source)
    attempts = ()
    events = ()
    if outcome in {ScientificOutcomeKind.OPERATIONAL_FAILURE, ScientificOutcomeKind.UNCERTAIN_CONTACT}:
        status = InquiryAttemptStatus.FAILED if outcome is ScientificOutcomeKind.OPERATIONAL_FAILURE else InquiryAttemptStatus.UNCERTAIN_CONTACT
        receipt = obj("receipt.operational")
        attempts = (InquiryAttempt("attempt.operational", obj("work.operational"), status, receipt, (), "Actual retained exposed interruption"),)
        events = (AcquisitionEvent("event.operational", "attempt.operational", receipt, cost()),)
    state = InquiryState("state." + domain, sid, cutoff, (assessment_evidence, source_evidence), attempts, (), events, 0, 0)
    tid = identity(state, state.state_id)
    observation = InquiryObservation(
        "observation." + domain, sid, outcome.value.lower(), outcome, spec.distinguishing_assessment,
        assessment if outcome in {ScientificOutcomeKind.POSITIVE, ScientificOutcomeKind.NEGATIVE, ScientificOutcomeKind.UNEVALUABLE} else None,
        ("evidence.assessment", "evidence.source") if outcome in {ScientificOutcomeKind.POSITIVE, ScientificOutcomeKind.NEGATIVE, ScientificOutcomeKind.UNEVALUABLE} else (),
        tuple(row.attempt_id for row in attempts), scope, cutoff,
        retained_finding,
    )
    frontier = InquiryTargetFrontier(
        "frontier." + domain, identity(target, target.target_id),
        (InquiryRequirementFinding(identity(condition, "condition"), None, ()),
         InquiryRequirementFinding(identity(instrument, "instrument"), None, ())),
        (InquiryClaimFinding(claim, scope, A.NOT_ATTEMPTED, None, (), "The overarching target has not been assessed"),), (),
    )
    rules = (
        InquiryCriterionRule("condition-resolution", InquiryCriterionRole.TARGET_PROGRESS, "requirements", True,
                             "Resolve a condition consequential for the next declared target use"),
        InquiryCriterionRule("enabled-uses", InquiryCriterionRole.ENABLED_CAPABILITY, "uses", True,
                             "Count the further source-bound capability whose requirement is addressed"),
        InquiryCriterionRule("discriminated-premises", InquiryCriterionRole.DISCRIMINATION, "premises", True,
                             "Distinguish the concrete numerical or source explanation responsible for uncertainty"),
        InquiryCriterionRule("cpu-cost", InquiryCriterionRole.COST, "s", False,
                             "Compare complete CPU expense when supported; otherwise retain unknown", "cpu_seconds"),
    )
    assumption = InquiryPolicyAssumption(
        "assumption.selected-design", "The chosen exposed discriminator can answer its declared premise",
        ("evidence.source",), "This is a conditional design premise, not a probability of scientific success",
    )
    policy = RobustInquiryPolicy("policy." + domain, sid, cost(), None, None, None,
                                 InquiryOrdering.LEXICOGRAPHIC, rules, (assumption,), IncomparableResolution.HOLD)
    def criteria():
        return tuple(sorted((InquiryCriterionAssessment(
            rule.criterion_id, None if rule.role is InquiryCriterionRole.COST else D(1),
            None if rule.role is InquiryCriterionRole.COST else D(1), rule.unit,
            ("evidence.source",), ("assumption.selected-design",), rule.justification,
        ) for rule in rules), key=lambda row: row.criterion_id))
    need = InquiryEvidenceNeed("evidence.source", source, scope, ContributionRole.RETAINED_ANALYSIS_INPUT)
    eligible = tuple(row.outcome_id for row in outcomes)
    parent = TargetDirectedAlternative(
        "follow-parent", sid, tid, InquiryAction.ACT, eligible, InquiryAlternativeKind.ACQUIRE,
        "condition", scope, "Use the parent supplier only after its independent prerequisite is admitted",
        "The selected target receiver response", (need,), ("instrument",), criteria(), cost(),
        "A warranted later target use", "Independent complete receiver assessment",
        "Supply the independently assessed missing instrument", work=ScientificInquiryWork(
            obj("method.parent"), (source,), scope, spec.distinguishing_assessment),
        successor_draft=obj("draft.parent"), successor_config=obj("config.parent"),
        input_origins=obj("origins.parent"), capability_id="capability.parent@1.0.0", planned_operation_count=2,
    )
    prerequisite = TargetDirectedAlternative(
        "investigate-prerequisite", sid, tid, InquiryAction.ACT, eligible, InquiryAlternativeKind.PREREQUISITE,
        "instrument", scope, next_question,
        observable, (need,), (), criteria(), cost(),
        enabled_capability,
        "Complete independent numerical/source assessment, including adverse outcomes",
        "An independent assessment establishes that this discriminator is unsupported",
        supplier=SupplierProposal("supplier.instrument", "instrument", ("supply.instrument",), (), True,
                                  "This source-bound supplier addresses the prerequisite that currently blocks parent use"),
        parent_requirement_id="condition", work=ScientificInquiryWork(
            obj("method.independent-source-check"), (source,), scope, spec.distinguishing_assessment),
        successor_draft=obj("draft.prerequisite"), successor_config=obj("config.prerequisite"),
        input_origins=obj("origins.prerequisite"), capability_id="capability.prerequisite@1.0.0", planned_operation_count=1,
    )
    hold = TargetDirectedAlternative(
        "hold", sid, tid, InquiryAction.HOLD, eligible, InquiryAlternativeKind.WAIT,
        "condition", scope, "Retain the unresolved target and obtain missing admission evidence",
        "Missing, unknown or incomparable evidence", (), ("instrument",), (), cost(),
        "The target remains available for a justified successor investigation",
        "An independently assessed supplier or explicit human resolution",
        "The missing scientific premise is supplied",)
    menu = RobustInquiryMenu("menu." + domain, sid, tid, (parent, hold, prerequisite), frontier, observation)
    auth = obj("authority", "empirical-lawhood/kernel/authority-policy")
    right = DecisionRight("right", AuthorityAction.READ_ONLY_EXPLORATION, "researcher", auth.object_id, True)
    node = CampaignNode("origin", CampaignNodeKind.EVIDENCE_SNAPSHOT, CampaignLane.EXPLORATORY,
                        source, (), LifecycleStatus.ACTIVE)
    campaign = CampaignSpec("campaign." + domain, target.purpose, (scope.system_id,), (scope.world_id,),
                            (claim.object_id,), ResourceBudget(1, 1024, 0, 1, 1, 1024), auth, (right,),
                            (node,), ("origin",), ("origin",), (source,), LifecycleStatus.ACTIVE)
    return N(specification=spec, state=state, menu=menu, policy=policy, campaign=campaign,
             right=right, actor_id="researcher", outcome_id=outcome.value.lower())


def choose(case, **kwargs):
    return choose_robust_inquiry(decision_id="decision", **vars(case), **kwargs)


@pytest.mark.parametrize("domain,scientific_reason", [
    ("battery", "Unresolved reference precision must be investigated before thermal-model admission"),
    ("rubisco", "Independent authentic structural preparation must precede controlled dynamics"),
    ("matrix", "An independently admitted factor/observation premise must precede dependent predictor use"),
])
def test_independent_domain_expected_prerequisite_decisions(domain, scientific_reason):
    case = policy_case(domain)
    decision = choose(case)
    assert decision.selected_alternative_id == "investigate-prerequisite", scientific_reason
    assert decision.unresolved_target_requirement_ids == ("condition", "instrument")
    assert decision.unresolved_target_claim_ids == ("claim.target",)
    assert decision.supplied_requirement_ids == ()
    parent = next(row for row in decision.evaluations if row.alternative_id == "follow-parent")
    assert "missing-prerequisite" in parent.reason_codes
    intent = make_robust_successor_intent(intent_id="intent", decision=decision,
                                        specification=case.specification, menu=case.menu)
    assert intent.decision.object_version == "2.0.0"
    validate_robust_inquiry_join(decision=decision, intent=intent, **{k: v for k, v in vars(case).items() if k not in {"actor_id", "outcome_id"}})


def complete_requirement(case, requirement_id):
    requirement = next(row for row in case.specification.requirements if row.requirement_id == requirement_id)
    connection = next(row for row in case.specification.connections if row.requirement_id == requirement_id)
    witness = case.state.stock[-1]
    assessments = tuple(sorted((RequirementSupplyAssessment(
        "assessment." + requirement_id + "." + phase.value.lower(), identity(requirement, requirement_id),
        identity(connection, connection.connection_id), phase, A.SATISFIED,
        case.specification.endpoint.instance_id, (witness.product,), (),
    ) for phase in AssessmentPhase), key=lambda row: row.assessment_id))
    stock = list(case.state.stock)
    stock.extend(InquiryEvidence(row.assessment_id, identity(row, row.assessment_id), None,
                                 requirement.scope, ContributionRole.RETAINED_ANALYSIS_INPUT,
                                 (), (), source_contract=witness.source_contract) for row in assessments)
    findings = tuple(InquiryRequirementFinding(identity(requirement, requirement_id), identity(connection, connection.connection_id), assessments)
                     if row.requirement.object_id == requirement_id else row for row in case.menu.frontier.requirement_findings)
    return rebound(case, state=replace(case.state, stock=tuple(sorted(stock, key=lambda row: row.evidence_id))),
                   menu=replace(case.menu, frontier=replace(case.menu.frontier, requirement_findings=findings)))


def test_assessed_prerequisite_changes_next_decision_and_preserves_target():
    case = complete_requirement(policy_case("battery"), "instrument")
    alternatives = tuple(replace(row, criteria=tuple(replace(c, lower=D(2), upper=D(2))
                                                   if c.criterion_id == "condition-resolution" else c for c in row.criteria))
                         if row.alternative_id == "follow-parent" else row for row in case.menu.alternatives)
    case = rebound(case, menu=replace(case.menu, alternatives=alternatives))
    decision = choose(case)
    assert decision.selected_alternative_id == "follow-parent"
    assert decision.supplied_requirement_ids == ("instrument",)
    assert decision.unresolved_target_requirement_ids == ("condition",)
    assert next(row for row in decision.evaluations if row.alternative_id == "investigate-prerequisite").status is RobustChoiceStatus.DOMINATED


def test_unknown_cost_and_overlapping_benefit_remain_incomparable():
    case = complete_requirement(policy_case("rubisco"), "instrument")
    decision = choose(case)
    assert decision.selected_alternative_id == "hold"
    assert all(row.status is RobustChoiceStatus.INCOMPARABLE for row in decision.evaluations if row.alternative_id != "hold")
    assert decision.remaining_cost.cpu_seconds is None
    policy = replace(case.policy, incomparable_resolution=IncomparableResolution.REQUIRE_HUMAN)
    case = rebound(case, policy=policy)
    with pytest.raises(ValueError, match="incomparable"):
        choose(case)
    with pytest.raises(ValueError, match="attributable reason"):
        choose(case, human_choice="follow-parent")
    decision = choose(case, human_choice="follow-parent", human_reason="Prioritize the declared controlled preparation because its receiver need is urgent")
    assert decision.human_directed
    assert decision.human_reason


@pytest.mark.parametrize("kind", [ScientificOutcomeKind.OPERATIONAL_FAILURE, ScientificOutcomeKind.UNCERTAIN_CONTACT])
def test_operational_failure_does_not_become_a_negative_scientific_assessment(kind):
    case = policy_case("rubisco", outcome=kind)
    altered = replace(case.menu.observation, kind=ScientificOutcomeKind.NEGATIVE,
                      outcome_id="negative", assessment=case.state.stock[0].product,
                      evidence_ids=("evidence.assessment",))
    case = rebound(case, outcome_id="negative", menu=replace(case.menu, observation=altered))
    with pytest.raises(ValueError, match="failed execution"):
        choose(case)


def test_finite_allowance_accounts_for_the_entire_proposed_wave():
    case = policy_case("battery")
    case = rebound(case, policy=replace(case.policy, max_operations=0))
    decision = choose(case)
    assert decision.selected_alternative_id == "hold"
    assert "finite-allowance-exhausted" in decision.evaluations[-1].reason_codes
    assert choose(rebound(case, policy=replace(case.policy, max_operations=None))).selected_alternative_id == "investigate-prerequisite"
    case = complete_requirement(rebound(case, policy=replace(case.policy, max_operations=1)), "instrument")
    evaluations = evaluate_robust_inquiry(case.specification, case.state, case.menu, case.policy, case.outcome_id)
    assert "finite-allowance-exhausted" in evaluations[0].reason_codes
    assert "finite-allowance-exhausted" not in evaluations[-1].reason_codes


@pytest.mark.parametrize("field,value", [("role", ContributionRole.INSTANCE_PRODUCT),
                                         ("scope", None), ("product", obj("wrong-source"))])
def test_source_scope_role_filter_precedes_any_ordering(field, value):
    case = policy_case("rubisco")
    chosen = case.menu.alternatives[-1]
    need = chosen.evidence_needs[0]
    if field == "scope":
        value = replace(need.scope, instance_id="other-material")
    chosen = replace(chosen, evidence_needs=(replace(need, **{field: value}),))
    case = rebound(case, menu=replace(case.menu, alternatives=(*case.menu.alternatives[:-1], chosen)))
    decision = choose(case)
    assert decision.selected_alternative_id == "hold"
    assert "source-scope-role-ineligible" in decision.evaluations[-1].reason_codes


def test_target_completion_requires_all_claims_and_all_four_scientific_supply_phases():
    case = complete_requirement(policy_case("rubisco", outcome=ScientificOutcomeKind.POSITIVE), "condition")
    closed = TargetDirectedAlternative(
        "close-target", case.menu.specification, case.menu.state, InquiryAction.STOP,
        tuple(row.outcome_id for row in case.specification.outcomes), InquiryAlternativeKind.CLOSE,
        "condition", case.specification.endpoint, "Assess simultaneous target completion", "Both endpoints in the same realized instance",
        (), (), (), cost(), "An assessed target contribution", "Any next benefit/transfer requirement",
        "Actual independently assessed paired endpoints change completion", stop_scope=InquiryStopScope.TARGET,
        local_question_answered=True,
    )
    outcomes = tuple(replace(row, alternative_ids=("close-target",)) for row in case.specification.outcomes)
    case = rebound(case, specification=replace(case.specification, outcomes=outcomes),
                   menu=replace(case.menu, alternatives=(closed,)))
    with pytest.raises(ValueError, match="no eligible decision"):
        choose(case)
    finding = case.menu.frontier.claim_findings[0]
    finding = replace(finding, disposition=A.SATISFIED, assessment=case.state.stock[0].product,
                      evidence_ids=(case.state.stock[0].evidence_id,), reason="Both required endpoints independently assessed at this exact scope")
    case = rebound(case, menu=replace(case.menu, frontier=replace(case.menu.frontier, claim_findings=(finding,))))
    # The target condition also requires the instrument. Assessing the parent
    # and its claim cannot silently credit that further prerequisite.
    with pytest.raises(ValueError, match="no eligible decision"):
        choose(case)
    case = complete_requirement(case, "instrument")
    assert choose(case).selected_alternative_id == "close-target"
    with pytest.raises(ValueError, match="actual instance"):
        choose(rebound(case, menu=replace(case.menu, frontier=replace(case.menu.frontier,
            claim_findings=(replace(finding, scope=replace(finding.scope, instance_id="other-enzyme")),)))))


def target_closure_case():
    case = complete_requirement(complete_requirement(
        policy_case("rubisco", outcome=ScientificOutcomeKind.POSITIVE), "condition"), "instrument")
    hold = case.menu.alternatives[1]
    eligible = tuple(row.outcome_id for row in case.specification.outcomes)
    close = TargetDirectedAlternative("close-target", case.menu.specification, case.menu.state,
        InquiryAction.STOP, eligible, InquiryAlternativeKind.CLOSE, "condition", case.specification.endpoint,
        "Assess the full target and its complete prerequisite closure", "Every declared endpoint and joined prerequisite",
        (), (), (), cost(), "Next assessed application", "The complete outcome denominator",
        "Any missing, adverse or independently unassessed prerequisite changes closure",
        stop_scope=InquiryStopScope.TARGET, local_question_answered=True)
    finding = replace(case.menu.frontier.claim_findings[0], disposition=A.SATISFIED,
        assessment=case.state.stock[0].product, evidence_ids=(case.state.stock[0].evidence_id,),
        reason="Exposed independent target claim witness at the original exact scope")
    return rebound(case, specification=replace(case.specification,
        outcomes=tuple(replace(row, alternative_ids=("close-target", "hold")) for row in case.specification.outcomes)),
        menu=replace(case.menu, alternatives=(close, hold),
            frontier=replace(case.menu.frontier, claim_findings=(finding,))))


@pytest.mark.parametrize("phase", tuple(AssessmentPhase))
@pytest.mark.parametrize("disposition", (None, A.FALSIFIED, A.REFUSED, A.UNSUPPORTED, A.UNEVALUABLE, A.NOT_ATTEMPTED))
def test_target_stop_refuses_every_missing_or_adverse_transitive_supply_phase(phase, disposition):
    case = target_closure_case()
    finding = case.menu.frontier.requirement_findings[-1]
    old = next(row for row in finding.assessments if row.phase is phase)
    new = None if disposition is None else replace(old, disposition=disposition,
        reason_codes=("exposed-prerequisite-not-satisfied",))
    assessments = tuple(new if row == old else row for row in finding.assessments if row != old or new is not None)
    stock = tuple(row for row in case.state.stock if row.product != identity(old, old.assessment_id))
    if new is not None:
        prior = next(row for row in case.state.stock if row.product == identity(old, old.assessment_id))
        stock = tuple(sorted((*stock, replace(prior, product=identity(new, new.assessment_id))), key=lambda row: row.evidence_id))
    case = rebound(case, state=replace(case.state, stock=stock), menu=replace(case.menu,
        frontier=replace(case.menu.frontier, requirement_findings=(case.menu.frontier.requirement_findings[0],
            replace(finding, assessments=assessments)))))
    decision = choose(case)
    assert decision.selected_alternative_id == "hold"
    assert decision.unresolved_target_requirement_ids == ("instrument",)
    assert "target-required-claims-or-joined-supply-unresolved" in decision.evaluations[0].reason_codes


def test_target_stop_requires_deep_prerequisites_and_every_required_claim():
    case = target_closure_case()
    condition, instrument = case.specification.requirements
    leaf = replace(instrument, requirement_id="measurement", consumer_operation_id="consume.measurement",
        assessment_operation_id="assess.measurement", further_requirement_ids=())
    instrument = replace(instrument, further_requirement_ids=("measurement",))
    connection = replace(case.specification.connections[-1], connection_id="connection.measurement",
        requirement_id="measurement", assessment_operation_id="assess.measurement", claim_id="claim.measurement")
    frontier = replace(case.menu.frontier, requirement_findings=(
        case.menu.frontier.requirement_findings[0],
        replace(case.menu.frontier.requirement_findings[-1], requirement=identity(instrument, "instrument"), assessments=()),
        InquiryRequirementFinding(identity(leaf, "measurement"), None, ())))
    old_assessments = {identity(row, row.assessment_id) for row in case.menu.frontier.requirement_findings[-1].assessments}
    case = rebound(case, specification=replace(case.specification, requirements=(condition, instrument, leaf),
        connections=(*case.specification.connections, connection)),
        state=replace(case.state, stock=tuple(row for row in case.state.stock if row.product not in old_assessments)),
        menu=replace(case.menu, frontier=frontier))
    case = complete_requirement(case, "instrument")
    assert case.specification.required_requirement_closure == ("condition", "instrument", "measurement")
    decision = choose(case)
    assert decision.selected_alternative_id == "hold" and decision.unresolved_target_requirement_ids == ("measurement",)
    case = complete_requirement(case, "measurement")
    assert choose(case).selected_alternative_id == "close-target"
    missing_claim = obj("claim.target.second", ClaimSpec.SCHEMA, "Second independently required target endpoint")
    target = replace(case.specification.target, required_claims=(*case.specification.target.required_claims, missing_claim))
    case = rebound(case, specification=replace(case.specification, target=target), menu=replace(case.menu,
        frontier=replace(case.menu.frontier, target=identity(target, target.target_id), claim_findings=(
            *case.menu.frontier.claim_findings,
            InquiryClaimFinding(missing_claim, target.scope, A.NOT_ATTEMPTED, None, (), "Second endpoint unentered")))))
    assert choose(case).selected_alternative_id == "hold"
    assert choose(case).unresolved_target_claim_ids == (missing_claim.object_id,)


@pytest.mark.parametrize("disposition", (A.FALSIFIED, A.REFUSED, A.UNEVALUABLE, A.UNSUPPORTED))
def test_adverse_target_claim_is_an_assessed_result_not_an_unattempted_label(disposition):
    finding = policy_case("rubisco").menu.frontier.claim_findings[0]
    with pytest.raises(ValueError, match="actual independent assessment"):
        replace(finding, disposition=disposition)


def test_scoped_menu_closure_retains_uncertain_target_and_next_supplier_question():
    case = policy_case("matrix")
    eligible = tuple(row.outcome_id for row in case.specification.outcomes)
    close = TargetDirectedAlternative("close-bounded-menu", case.menu.specification, case.menu.state,
        InquiryAction.STOP, eligible, InquiryAlternativeKind.CLOSE, "condition", case.specification.endpoint,
        "Does the assessed scalar result warrant another native response action in this exact frozen menu?",
        "Independent response-instrument admission remains absent for every selected action.", (), (), (), cost(),
        "A separately scoped instrument supplier question remains available.",
        "Independent parameter-consistent factor/action admission can reopen a new inquiry.",
        "An independently assessed instrument supplies the currently missing condition.",
        stop_scope=InquiryStopScope.BRANCH, local_question_answered=True)
    hold = replace(case.menu.alternatives[1], eligible_outcomes=eligible)
    case = rebound(case, specification=replace(case.specification,
        outcomes=tuple(replace(row, alternative_ids=(close.alternative_id, "hold")) for row in case.specification.outcomes)),
        menu=replace(case.menu, alternatives=(close, hold)))
    decision = choose(case)
    assert next(row.action for row in case.menu.alternatives
                if row.alternative_id == decision.selected_alternative_id) is InquiryAction.STOP
    assert decision.stop_scope is InquiryStopScope.BRANCH
    assert decision.unresolved_target_requirement_ids == ("condition", "instrument")
    assert decision.unresolved_target_claim_ids == ("claim.target",)
    assert "supplier question" in decision.next_enabled_capability
    assert case.menu.observation.kind is ScientificOutcomeKind.UNEVALUABLE


def test_frozen_outcome_census_routine_adoption_and_canonical_revision():
    case = policy_case("matrix")
    assert case.specification.explanations == ()
    assert case.specification.VERSION == "2.0.0"
    with pytest.raises(ValueError, match="outcome map"):
        replace(case.specification, outcomes=case.specification.outcomes[:-1])
    with pytest.raises(ValueError, match="invent competing"):
        replace(case.specification, explanations=("known method", "invented substitute"))
    with pytest.raises(ValueError, match="distinct explanations"):
        replace(case.specification, question_kind=InquiryQuestionKind.DISCRIMINATE)
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes

    assert decode_canonical_bytes(case.specification.canonical_bytes(), RobustInquirySpecification, maximum_bytes=None) == case.specification


def test_known_method_adoption_reuses_actual_completion_without_novelty_or_relabelled_acquisition():
    case = complete_requirement(policy_case("battery"), "instrument")
    original = case.menu.alternatives[-1]
    product = case.state.stock[-1].product
    receipt = obj("receipt.completed-known-method")
    attempt = InquiryAttempt("attempt.known-method", original.work.method, InquiryAttemptStatus.COMPLETED,
                             receipt, (product,), "Authenticated completion at its original exposed scope")
    event = AcquisitionEvent("event.known-method", attempt.attempt_id, receipt, cost("12", "15", "1024"))
    completion = CompletedInquiryWork("completion.known-method", original.work, attempt.attempt_id, receipt, (product,))
    adopt = replace(original, alternative_id="adopt-known-method", kind=InquiryAlternativeKind.ADOPT,
                    parent_requirement_id=None, reuse_completion=completion,
                    scientific_question="Use the established admitted numerical method and expose the next charging requirement")
    reacquire = replace(original, alternative_id="reacquire-fresh-label", kind=InquiryAlternativeKind.ACQUIRE,
                        parent_requirement_id=None, successor_draft=obj("fresh-label.draft"),
                        successor_config=obj("fresh-label.config"), input_origins=obj("fresh-label.origins"))
    hold = case.menu.alternatives[1]
    outcomes = tuple(replace(row, alternative_ids=(adopt.alternative_id, "hold", reacquire.alternative_id)) for row in case.specification.outcomes)
    case = rebound(case, specification=replace(case.specification, outcomes=outcomes),
                   state=replace(case.state, operational_census=(attempt,), cost_events=(event,)),
                   menu=replace(case.menu, alternatives=(adopt, hold, reacquire),
                                frontier=replace(case.menu.frontier, completed_work=(completion,))))
    decision = choose(case)
    assert decision.selected_alternative_id == "adopt-known-method"
    assert decision.unresolved_target_requirement_ids == ("condition",)
    assert "authenticated-completion-reuse-required" in decision.evaluations[-1].reason_codes
    assert "novelty" not in {row.criterion_id for row in case.policy.criterion_order}
    altered = replace(completion, receipt=obj("false-completion-receipt"))
    with pytest.raises(ValueError, match="receipt/product/attempt"):
        choose(rebound(case, menu=replace(case.menu, frontier=replace(case.menu.frontier, completed_work=(altered,)))))


def test_matrix_assessed_factor_negative_closes_only_its_branch_and_keeps_dependent_work_unentered():
    case = policy_case("matrix", outcome=ScientificOutcomeKind.NEGATIVE)
    close = TargetDirectedAlternative(
        "close-factor", case.menu.specification, case.menu.state, InquiryAction.STOP,
        ("negative",), InquiryAlternativeKind.CLOSE, "condition", case.specification.endpoint,
        "Retain the independently falsified factor-response hypothesis",
        "The frozen native-response loss and complete factor/root denominator", (), (), (), cost(),
        "A justified nonfactor question may subsequently be selected with new scientific bindings",
        "Any successor must freeze its own nonfactor instrument, permitted past and reserved roots",
        "Independent new evidence or a changed scientific object would justify a new inquiry",
        stop_scope=InquiryStopScope.BRANCH, local_question_answered=True,
    )
    hold = replace(case.menu.alternatives[1], eligible_outcomes=tuple(row.outcome_id for row in case.specification.outcomes if row.outcome_id != "negative"))
    outcomes = tuple(replace(row, alternative_ids=("close-factor",) if row.outcome_id == "negative" else ("hold",))
                     for row in case.specification.outcomes)
    case = rebound(case, specification=replace(case.specification, outcomes=outcomes),
                   menu=replace(case.menu, alternatives=(close, hold)))
    decision = choose(case)
    assert decision.selected_alternative_id == "close-factor"
    assert decision.stop_scope is InquiryStopScope.BRANCH
    assert decision.unresolved_target_claim_ids == ("claim.target",)
    assert decision.unentered_requirement_ids == ("condition", "instrument")
    assert case.menu.observation.kind is ScientificOutcomeKind.NEGATIVE
    with pytest.raises(ValueError, match="only a committed ACT"):
        make_robust_successor_intent(intent_id="false-intent", decision=decision,
                                    specification=case.specification, menu=case.menu)


@pytest.mark.parametrize("case_id,kind,reason,successor_question,expected", [
    ("native-utility", ScientificOutcomeKind.NEGATIVE,
     "The complete exposed native-response contrast fails its frozen utility requirement",
     "Which separately assessed nonfactor instrument predicts the native finite-action response?", InquiryAction.STOP),
    ("lifetime-variation", ScientificOutcomeKind.UNEVALUABLE,
     "The complete exposed population has insufficient useful-lifetime variation to distinguish the selected calibration",
     "Does a prospectively frozen population expose enough lifetime variation for the unchanged calibration?", InquiryAction.HOLD),
    ("preparation-headroom", ScientificOutcomeKind.UNEVALUABLE,
     "The complete exposed matched preparations leave no independently supported reliability headroom",
     "Which prospectively frozen population has useful preparation headroom under the unchanged lower package?", InquiryAction.HOLD),
    ("withheld-transfer", ScientificOutcomeKind.NEGATIVE,
     "The exposed frozen no-refit transfer assessment fails in its originally withheld regime",
     "What separately assessed domain boundary explains this withheld-regime transfer failure?", InquiryAction.STOP),
])
def test_matrix_boundaries_retain_assessed_outcome_and_freeze_an_unentered_successor(
        case_id, kind, reason, successor_question, expected):
    """Explicit exposed policy operands; no matrix study is acquired or qualified."""
    from empirical_lawhood.planning.recursive_inquiry_policy import validate_robust_inquiry_revision

    original = policy_case("matrix", outcome=kind)
    scope = original.specification.endpoint
    contract = obj("assessment.contract." + case_id,
                   content="Frozen exposed matrix assessment: " + reason)
    assessment = obj("assessment.actual." + case_id, content=reason)
    stock = tuple(replace(row, product=assessment) if row.evidence_id == "evidence.assessment" else row
                  for row in original.state.stock)
    retained = replace(original.menu.observation, assessment_contract=contract, assessment=assessment, reason=reason)
    hold = original.menu.alternatives[1]
    hold = replace(hold, scientific_question=successor_question, expected_next_evidence=successor_question,
                   evidence_that_changes_disposition="An independently assessed prospective design can distinguish this precise missing premise")
    alternatives = (hold,)
    if expected is InquiryAction.STOP:
        close = TargetDirectedAlternative(
            "close-scoped-" + case_id, original.menu.specification, original.menu.state,
            InquiryAction.STOP, (kind.value.lower(),), InquiryAlternativeKind.CLOSE,
            "condition", scope, reason, "Complete frozen exposed assessment denominator",
            (), (), (), cost(), "The overarching native response target remains open",
            successor_question, "An independently assessed successor answers a separately frozen question",
            stop_scope=InquiryStopScope.BRANCH, local_question_answered=True)
        alternatives = (close, hold)
    outcomes = tuple(replace(row, alternative_ids=tuple(sorted(alt.alternative_id for alt in alternatives
                                                               if row.outcome_id in alt.eligible_outcomes)))
                     for row in original.specification.outcomes)
    original = rebound(original, specification=replace(original.specification,
        distinguishing_assessment=contract, outcomes=outcomes),
        state=replace(original.state, stock=stock),
        menu=replace(original.menu, alternatives=alternatives, observation=retained))
    terminal = choose(original)
    assert next(row.action for row in original.menu.alternatives
                if row.alternative_id == terminal.selected_alternative_id) is expected
    assert original.menu.observation.kind is kind and original.menu.observation.scope == scope
    assert terminal.unresolved_target_claim_ids == ("claim.target",)
    assert terminal.unentered_requirement_ids == ("condition", "instrument")
    assert terminal.supplied_requirement_ids == ()
    if expected is InquiryAction.STOP:
        assert terminal.stop_scope is InquiryStopScope.BRANCH
    original = rebound(original, state=replace(original.state,
        previous_decisions=(identity(terminal, terminal.decision_id),)))
    hold = next(row for row in original.menu.alternatives if row.alternative_id == "hold")

    new_contract = obj("assessment.successor." + case_id, content=successor_question)
    new_scope = replace(scope, source_id="source.prospective." + case_id,
                        source_config_sha256=new_contract.object_fingerprint)
    requirements = tuple(replace(row, scope=new_scope) if row.requirement_id == "condition" else row
                         for row in original.specification.requirements)
    specification = replace(original.specification, specification_id="spec.successor." + case_id,
        question=successor_question, endpoint=new_scope, distinguishing_assessment=new_contract,
        requirements=requirements, question_kind=InquiryQuestionKind.ASSESS,
        outcomes=tuple(replace(row, alternative_ids=("hold",)) for row in original.specification.outcomes),
        predecessor_specification=identity(original.specification, original.specification.specification_id))
    state = replace(original.state, state_id="state.successor." + case_id,
                    revision_parent=identity(original.state, original.state.state_id))
    frontier = replace(original.menu.frontier, requirement_findings=tuple(
        replace(finding, requirement=identity(requirement, requirement.requirement_id))
        for finding, requirement in zip(original.menu.frontier.requirement_findings, requirements, strict=True)))
    observation = replace(retained, assessment_contract=new_contract, assessment=None, evidence_ids=(),
        kind=ScientificOutcomeKind.MISSING, outcome_id="missing", scope=new_scope,
        reason="The retained result remains in its original scope; this prospective successor is unentered")
    successor = rebound(original, specification=specification, state=state, outcome_id="missing",
        menu=replace(original.menu, alternatives=(replace(hold, scope=new_scope),),
                     observation=observation, frontier=frontier))
    validate_robust_inquiry_revision(previous_specification=original.specification,
        previous_state=original.state, specification=successor.specification, state=successor.state,
        policy=successor.policy)
    assert choose(successor).selected_alternative_id == "hold"
    assert successor.specification.target == original.specification.target
    assert successor.specification.distinguishing_assessment != original.specification.distinguishing_assessment
    assert successor.state.stock == original.state.stock
    assert successor.state.previous_decisions == original.state.previous_decisions
    assert successor.state.cost_events == original.state.cost_events
    assert successor.menu.observation.scope != original.menu.observation.scope


def test_exact_supported_ties_partial_order_and_human_direction_are_distinct():
    case = complete_requirement(policy_case("rubisco"), "instrument")
    alternatives = tuple(replace(row, expense_bound=cost("3"), criteria=tuple(
        replace(criterion, lower=D(3), upper=D(3)) if criterion.criterion_id == "cpu-cost" else criterion
        for criterion in row.criteria)) if row.action is InquiryAction.ACT else row
        for row in case.menu.alternatives)
    case = rebound(case, menu=replace(case.menu, alternatives=alternatives))
    assert choose(case).selected_alternative_id == "follow-parent"
    # Better target progress but worse expense is a genuine partial-order tradeoff.
    parent = replace(case.menu.alternatives[0], expense_bound=cost("10"), criteria=tuple(
        replace(row, lower=D(2), upper=D(2)) if row.criterion_id == "condition-resolution" else
        replace(row, lower=D(10), upper=D(10)) if row.criterion_id == "cpu-cost" else row
        for row in case.menu.alternatives[0].criteria))
    case = rebound(case, menu=replace(case.menu, alternatives=(parent, *case.menu.alternatives[1:])),
                   policy=replace(case.policy, ordering=InquiryOrdering.PARTIAL))
    assert choose(case).selected_alternative_id == "hold"
    decision = choose(case, human_choice="investigate-prerequisite", human_reason="The lower-cost independent scientific assessment resolves the current uncertainty first")
    assert decision.human_directed
    intent = make_robust_successor_intent(intent_id="intent.human", decision=decision,
                                        specification=case.specification, menu=case.menu)
    with pytest.raises(ValueError, match="intent scientific bindings"):
        validate_robust_inquiry_join(decision=replace(decision, human_reason="changed after commitment"),
                                    intent=intent,
                                    **{k: v for k, v in vars(case).items() if k not in {"actor_id", "outcome_id"}})


def test_cross_scope_reuse_requires_actual_independent_compatibility_and_retains_native_scopes():
    case = policy_case("rubisco")
    source = next(row for row in case.state.stock if row.evidence_id == "evidence.source")
    remote_scope = replace(source.scope, system_id="system.remote", world_id="world.exposed.remote", clock_id="clock.remote",
                           information_cutoff=replace(source.scope.information_cutoff, clock_id="clock.remote"))
    remote = replace(source, scope=remote_scope)
    case = rebound(case, state=replace(case.state, stock=(case.state.stock[0], remote)))
    chosen = case.menu.alternatives[-1]
    chosen = replace(chosen, evidence_needs=(replace(chosen.evidence_needs[0], scope=remote_scope),))
    case = rebound(case, menu=replace(case.menu, alternatives=(*case.menu.alternatives[:-1], chosen)))
    decision = choose(case)
    assert decision.selected_alternative_id == "hold"
    assert "independent-cross-scope-compatibility-required" in decision.evaluations[-1].reason_codes
    # A common target or method name does not supply that compatibility witness.
    assert case.state.stock[-1].scope.clock_id == "clock.remote"

    # An unrelated authenticated product is not an independent transfer assay.
    fake = replace(chosen.evidence_needs[0], compatibility_assessment=case.state.stock[0].product)
    chosen = replace(chosen, evidence_needs=(fake,))
    case = rebound(case, menu=replace(case.menu, alternatives=(*case.menu.alternatives[:-1], chosen)))
    assert "independent-cross-scope-compatibility-required" in choose(case).evaluations[-1].reason_codes

    # The exact ADMISSION phase names the remote operand and the receiving
    # requirement. It permits this conditional check without claiming joined use.
    requirement = case.specification.requirements[-1]
    connection = case.specification.connections[-1]
    assessment = RequirementSupplyAssessment("assessment.remote-admission",
        identity(requirement, requirement.requirement_id), identity(connection, connection.connection_id),
        AssessmentPhase.ADMISSION, A.SATISFIED, requirement.scope.instance_id, (remote.product,), ())
    witness = InquiryEvidence("evidence.remote-admission", identity(assessment, assessment.assessment_id), None,
        requirement.scope, ContributionRole.RETAINED_ANALYSIS_INPUT, (), (), source_contract=source.source_contract)
    finding = InquiryRequirementFinding(identity(requirement, requirement.requirement_id),
        identity(connection, connection.connection_id), (assessment,))
    chosen = replace(chosen, evidence_needs=(replace(fake, compatibility_assessment=witness.product),))
    case = rebound(case, state=replace(case.state, stock=tuple(sorted((*case.state.stock, witness), key=lambda row: row.evidence_id))),
        menu=replace(case.menu, alternatives=(*case.menu.alternatives[:-1], chosen),
            frontier=replace(case.menu.frontier, requirement_findings=(case.menu.frontier.requirement_findings[0], finding))))
    decision = choose(case)
    assert decision.selected_alternative_id == "investigate-prerequisite"
    assert decision.supplied_requirement_ids == ()  # admission is not joined use
    bad = replace(witness, scope=remote_scope)
    with pytest.raises(ValueError, match="exact scientific requirement scope"):
        choose(rebound(case, state=replace(case.state, stock=tuple(bad if row == witness else row for row in case.state.stock))))


def test_disconnected_side_inquiry_cannot_claim_target_progress():
    case = policy_case("matrix")
    unrelated = replace(case.specification.requirements[-1], requirement_id="side-inquiry",
        purpose="An unrelated matrix benchmark tournament", further_requirement_ids=())
    with pytest.raises(ValueError, match="disconnected"):
        replace(case.specification, requirements=tuple(sorted((*case.specification.requirements, unrelated),
            key=lambda row: row.requirement_id)))


def test_source_cutoff_and_all_claim_denominators_refuse_mutations():
    case = policy_case("battery")
    bad = replace(case.state.stock[-1], scope=replace(case.state.stock[-1].scope,
                  information_cutoff=replace(case.state.information_cutoff, coordinate=D(2))))
    with pytest.raises(ValueError, match="beyond the frozen"):
        choose(rebound(case, state=replace(case.state, stock=(case.state.stock[0], bad))))
    with pytest.raises(ValueError, match="claim denominator"):
        choose(rebound(case, menu=replace(case.menu, frontier=replace(case.menu.frontier, claim_findings=()))))
    with pytest.raises(ValueError, match="requirement denominator"):
        choose(rebound(case, menu=replace(case.menu, frontier=replace(case.menu.frontier,
                                                                    requirement_findings=case.menu.frontier.requirement_findings[:-1]))))
    # Retaining an assessment elsewhere in stock does not bind it to the
    # observation whose evidence list or receiver scope has been substituted.
    observation = replace(case.menu.observation, evidence_ids=("evidence.source",))
    with pytest.raises(ValueError, match="exact scoped evidence witness"):
        choose(rebound(case, menu=replace(case.menu, observation=observation)))
    evidence = case.state.stock[0]
    wrong = replace(evidence, scope=replace(evidence.scope, receiver_id="receiver.other-observable"))
    with pytest.raises(ValueError, match="exact scoped evidence witness"):
        choose(rebound(case, state=replace(case.state, stock=(wrong, *case.state.stock[1:]))))


def test_supplier_unavailable_disposition_is_retained_before_policy_ranking():
    case = policy_case("rubisco")
    chosen = case.menu.alternatives[-1]
    chosen = replace(chosen, supplier=replace(chosen.supplier, unavailable_reason_codes=("UNASSESSED_PREPARATION",)))
    case = rebound(case, menu=replace(case.menu, alternatives=(*case.menu.alternatives[:-1], chosen)))
    decision = choose(case)
    assert decision.selected_alternative_id == "hold"
    assert "supplier-unavailable-or-unselected" in decision.evaluations[-1].reason_codes


def test_scientific_redirection_preserves_target_exact_exposed_stock_and_terminal_history():
    from empirical_lawhood.planning.recursive_inquiry_policy import validate_robust_inquiry_revision

    old = policy_case("matrix")
    previous_decision = choose(old)
    old = rebound(old, state=replace(old.state, previous_decisions=(identity(previous_decision, "decision"),)))
    source = old.specification.endpoint
    new_scope = replace(source, source_id="source.changed-instrument", source_config_sha256="b" * 64)
    requirements = tuple(replace(row, scope=new_scope) if row.requirement_id == "condition" else row
                         for row in old.specification.requirements)
    spec = replace(old.specification, specification_id="spec.matrix-revised", endpoint=new_scope,
                   question="Freeze a separately scoped nonfactor instrument question after retaining the original factor result",
                   requirements=requirements, predecessor_specification=identity(old.specification, old.specification.specification_id))
    state = replace(old.state, state_id="state.matrix-revised", specification=identity(spec, spec.specification_id),
                    revision_parent=identity(old.state, old.state.state_id))
    policy = replace(old.policy, specification=identity(spec, spec.specification_id))
    validate_robust_inquiry_revision(previous_specification=old.specification, previous_state=old.state,
                                    specification=spec, state=state, policy=policy)
    assert state.stock == old.state.stock
    assert old.specification.endpoint != spec.endpoint
    with pytest.raises(ValueError, match="retained previous_decisions"):
        validate_robust_inquiry_revision(previous_specification=old.specification, previous_state=old.state,
                                        specification=spec, state=replace(state, previous_decisions=()), policy=policy)


def test_matrix_redirection_freezes_new_native_question_and_refuses_silent_factor_transfer():
    """Scalar discovery and native factor-response admission are distinct questions.

    These exposed immutable operands test redirection/admission, not completion
    of a matrix experiment or acquisition of another independent native root.
    """
    from empirical_lawhood.planning.recursive_inquiry_policy import validate_robust_inquiry_revision

    old = complete_requirement(policy_case("matrix", outcome=ScientificOutcomeKind.NEGATIVE), "instrument")
    terminal = choose(old, human_choice="hold", human_reason="Retain the scoped scalar negative and formulate an actual factor-response admission question")
    old = rebound(old, state=replace(old.state, previous_decisions=(identity(terminal, terminal.decision_id),)))
    original_scope = old.specification.endpoint
    new_scope = replace(original_scope, source_id="source.exposed-native-factor-response",
        source_config_sha256=sha256(b"frozen parameter-consistent factor/action admission contract").hexdigest())
    assessment_contract = obj("assessment.exposed-matrix-factor-action",
        content="Complete source/frame/model/parameter join; origin-only forecast; native branch response with separate oracle")
    requirements = tuple(replace(row, scope=new_scope) if row.requirement_id == "condition" else row
                         for row in old.specification.requirements)
    specification = replace(old.specification, specification_id="spec.matrix-native-admission",
        question="Does this parameter-consistent factor instrument support the committed native finite-action response?",
        question_kind=InquiryQuestionKind.DISCRIMINATE,
        explanations=("Scalar detector success does not assess the factor/action model join",
                      "The admitted factor/action model predicts the native response at its frozen conditions"),
        endpoint=new_scope, distinguishing_assessment=assessment_contract, requirements=requirements,
        outcomes=tuple(replace(row, alternative_ids=("follow-parent", "hold")) for row in old.specification.outcomes),
        predecessor_specification=identity(old.specification, old.specification.specification_id))
    state = replace(old.state, state_id="state.matrix-native-admission",
        specification=identity(specification, specification.specification_id),
        revision_parent=identity(old.state, old.state.state_id))
    parent, hold = old.menu.alternatives[:2]
    parent = replace(parent, scope=new_scope,
        scientific_question=specification.question, observable="Complete factor/action frame joins and all native branch response errors",
        work=replace(parent.work, method=obj("method.native-factor-action", content=assessment_contract.object_fingerprint),
            scope=new_scope, observation_contract=assessment_contract), successor_config=assessment_contract)
    hold = replace(hold, scope=new_scope, scientific_question="Require independently assessed compatibility before reusing the old instrument")
    frontier = replace(old.menu.frontier, requirement_findings=tuple(
        replace(row, requirement=identity(requirement, requirement.requirement_id)) if requirement.requirement_id == "condition" else row
        for row, requirement in zip(old.menu.frontier.requirement_findings, requirements, strict=True)))
    observation = replace(old.menu.observation, kind=ScientificOutcomeKind.MISSING, outcome_id="missing",
        assessment=None, evidence_ids=(), scope=new_scope, assessment_contract=assessment_contract,
        reason="The earlier scalar verdict remains historical; native factor/action assessment has not entered.")
    case = rebound(old, specification=specification, state=state, outcome_id="missing",
        menu=replace(old.menu, alternatives=(parent, hold), frontier=frontier, observation=observation))
    validate_robust_inquiry_revision(previous_specification=old.specification, previous_state=old.state,
        specification=case.specification, state=case.state, policy=case.policy)
    decision = choose(case)
    assert decision.selected_alternative_id == "hold"
    assert "independent-cross-scope-compatibility-required" in decision.evaluations[0].reason_codes
    assert decision.unresolved_target_claim_ids and case.specification.target == old.specification.target
    assert case.state.stock == old.state.stock and case.state.cost_events == old.state.cost_events
    assert case.state.previous_decisions == old.state.previous_decisions
    # Renaming the old scalar result cannot answer the newly frozen question.
    changed = replace(case.menu.observation, kind=ScientificOutcomeKind.POSITIVE, outcome_id="positive",
        assessment=old.menu.observation.assessment, evidence_ids=old.menu.observation.evidence_ids,
        assessment_contract=old.specification.distinguishing_assessment)
    with pytest.raises(ValueError, match="committed assessment"):
        choose(rebound(case, outcome_id="positive", menu=replace(case.menu, observation=changed)))


def test_uncertain_contact_requires_recovery_before_the_same_scientific_work():
    case = policy_case("rubisco", outcome=ScientificOutcomeKind.UNCERTAIN_CONTACT)
    original = case.state.operational_census[0]
    decision = choose(case)
    assert decision.selected_alternative_id == "hold"
    assert "uncertain-contact-recovery-required" in decision.evaluations[-1].reason_codes
    # A new draft/configuration label cannot settle the original contact state.
    alternative = replace(case.menu.alternatives[-1], successor_draft=obj("fresh-labelled-draft"),
                          successor_config=obj("fresh-labelled-config"))
    case = rebound(case, menu=replace(case.menu, alternatives=(*case.menu.alternatives[:-1], alternative)))
    assert choose(case).selected_alternative_id == "hold"
    assert case.state.operational_census[0] == original  # unknown legacy work is never relabelled


def test_battery_uncertain_contact_closes_no_scientific_branch_and_refuses_both_replay_choices():
    case = policy_case("battery", outcome=ScientificOutcomeKind.UNCERTAIN_CONTACT)
    # Exposed operational-contract operands; these are not newly discovered
    # counts for the historical OOM invocation whose completion remains unknown.
    decision = choose(case)
    assert decision.selected_alternative_id == "hold"
    assert decision.supplied_requirement_ids == () and decision.stop_scope is None
    assert decision.remaining_cost.cpu_seconds is None
    assert "uncertain-contact-recovery-required" in decision.evaluations[-1].reason_codes
    assert "missing-prerequisite" in decision.evaluations[0].reason_codes
    assert case.state.operational_census[0].status is InquiryAttemptStatus.UNCERTAIN_CONTACT


def work_bound_case(*, known=True):
    case = policy_case("rubisco", outcome=ScientificOutcomeKind.UNCERTAIN_CONTACT)
    attempt = case.state.operational_census[0]
    binding = InquiryAttemptWorkBinding(attempt.attempt_id, attempt.operation,
        case.menu.alternatives[-1].work if known else None,
        obj("wave.original", "empirical-lawhood/runtime/authored-recursive-wave"),
        obj("plan.original", "empirical-lawhood/runtime/development-execution-plan"),
        obj("task.original", "empirical-lawhood/runtime/execution-task"), attempt.receipt)
    state = WorkBoundInquiryState(**{field.name: getattr(case.state, field.name) for field in fields(InquiryState)},
        attempt_work_bindings=(binding,))
    return rebound(case, state=state)


@pytest.mark.parametrize("known", (False, True))
def test_shared_uncertain_work_rule_preserves_unknown_work_and_exact_operation_aliases(known):
    case = work_bound_case(known=known)
    attempt = case.state.operational_census[0]
    original = case.menu.alternatives[-1]
    distinct = replace(original.work, scientific_operands=(obj("different.actual.operand"),))
    assert uncertain_contact_requires_recovery(operational_census=case.state.operational_census,
        attempt_work_bindings=case.state.attempt_work_bindings,
        selected_work=distinct, successor_config=obj("different.configuration")) is (not known)
    assert uncertain_contact_requires_recovery(operational_census=case.state.operational_census,
        attempt_work_bindings=case.state.attempt_work_bindings,
        selected_work=distinct, successor_config=attempt.operation)
    assert uncertain_contact_requires_recovery(operational_census=case.state.operational_census,
        attempt_work_bindings=case.state.attempt_work_bindings,
        selected_work=replace(distinct, method=attempt.operation), successor_config=obj("renamed.configuration"))
    completed = replace(attempt, status=InquiryAttemptStatus.COMPLETED)
    assert not uncertain_contact_requires_recovery(operational_census=(completed,),
        attempt_work_bindings=case.state.attempt_work_bindings,
        selected_work=original.work, successor_config=attempt.operation)


@pytest.mark.parametrize("known", (False, True))
def test_explicit_attempt_work_custody_blocks_relabelled_uncertain_acquisition(known):
    case = work_bound_case(known=known)
    original = case.state.operational_census[0]
    alternative = replace(case.menu.alternatives[-1], successor_config=obj("config.renamed"),
        successor_draft=obj("draft.renamed"))
    case = rebound(case, menu=replace(case.menu, alternatives=(*case.menu.alternatives[:-1], alternative)))
    decision = choose(case)
    assert decision.VERSION == "3.0.0" and decision.selected_alternative_id == "hold"
    assert case.state.operational_census[0] == original
    assert "uncertain-contact-recovery-required" in decision.evaluations[-1].reason_codes


@pytest.mark.parametrize("part", ("denominator", "configuration", "witness", "wave"))
def test_work_binding_preserves_exact_attempt_denominator_and_custody_joins(part):
    case = work_bound_case()
    binding = case.state.attempt_work_bindings[0]
    with pytest.raises(ValueError, match="denominator|configuration/attempt witness|wave/plan/task"):
        if part == "denominator":
            replace(case.state, attempt_work_bindings=())
        else:
            changed = replace(binding, **({"authored_wave": None} if part == "wave" else {part: obj("substituted")}))
            replace(case.state, attempt_work_bindings=(changed,))


def test_original_closed_state_and_request_versions_remain_exactly_readable():
    from empirical_lawhood.api.recursive_inquiry import decode_inquiry_decision_request
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from empirical_lawhood.runtime.recursive_inquiry import InquiryStateSources, RobustInquiryDecisionRequest, WorkBoundInquiryDecisionRequest

    old = policy_case("rubisco")
    request = RobustInquiryDecisionRequest(old.specification, old.state, InquiryStateSources(()), old.menu, old.policy,
        old.campaign, old.right, old.actor_id)
    original = request.canonical_bytes()
    assert decode_inquiry_decision_request(original).canonical_bytes() == original
    assert decode_canonical_bytes(old.state.canonical_bytes(), InquiryState, maximum_bytes=None) == old.state
    current = work_bound_case()
    request3 = WorkBoundInquiryDecisionRequest(current.specification, current.state, InquiryStateSources(()),
        current.menu, current.policy, current.campaign, current.right, current.actor_id)
    assert decode_inquiry_decision_request(request3.canonical_bytes()) == request3
    with pytest.raises(ValueError):
        decode_canonical_bytes(request3.canonical_bytes(), RobustInquiryDecisionRequest, maximum_bytes=None)
    with pytest.raises(ValueError):
        decode_canonical_bytes(current.state.canonical_bytes(), InquiryState, maximum_bytes=None)


def test_archived_v2_frontier_bytes_are_history_and_never_current_policy_credit():
    case = policy_case("rubisco")
    current = choose(case)
    archived = replace(current, unresolved_target_requirement_ids=("condition",))
    original = archived.canonical_bytes()
    validate_robust_inquiry_join(decision=archived, specification=case.specification, state=case.state,
        menu=case.menu, policy=case.policy, campaign=case.campaign, right=case.right,
        validate_authority=False, historical=True)
    assert archived.canonical_bytes() == original
    with pytest.raises(ValueError, match="target/frontier/order/human"):
        validate_robust_inquiry_join(decision=archived, specification=case.specification, state=case.state,
            menu=case.menu, policy=case.policy, campaign=case.campaign, right=case.right)


def test_evidence_role_must_be_permitted_by_the_exact_requirement():
    case = policy_case("battery")
    instrument = replace(case.specification.requirements[-1], permitted_roles=(ContributionRole.DESIGN_OPERAND,))
    connection = replace(case.specification.connections[-1], evidence_role=ContributionRole.DESIGN_OPERAND)
    case = rebound(case, specification=replace(case.specification,
        requirements=(*case.specification.requirements[:-1], instrument),
        connections=(*case.specification.connections[:-1], connection)),
        menu=replace(case.menu, frontier=replace(case.menu.frontier,
            requirement_findings=(case.menu.frontier.requirement_findings[0],
                                  InquiryRequirementFinding(identity(instrument, instrument.requirement_id), None, ())))))
    decision = choose(case)
    assert decision.selected_alternative_id == "hold"
    assert "requirement-evidence-role-ineligible" in decision.evaluations[-1].reason_codes
