# SPDX-License-Identifier: MPL-2.0
"""Compose the existing authoring graph and a source-checked dependent census."""

from dataclasses import replace
from decimal import Decimal

from empirical_lawhood.science.identity.authority import AuthorityAction, AuthorityPolicy, ResourceBudget, SourceAccessClass
from empirical_lawhood.science.evidence.evidence import ClaimSpec, EvidenceCeiling, VisibilityCeiling
from empirical_lawhood.science.experiments.experimental_design import IndependentUnit, UnitAllocation, UnitRoleAssignment
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import ConditionRole, ContributionRole, DevelopmentStudySpec, ScientificConditionScope, ScientificConnectionSpec, ScientificRequirementSpec
from empirical_lawhood.science.identity.references import NamedDecimal, QuantityBound
from empirical_lawhood.science.records.status import LifecycleStatus
from empirical_lawhood.science.models.time import CausalPhase, ClockCoordinate, CoordinateOrigin, InformationCutoff
from empirical_lawhood.science.models.worlds import WorldKind
from empirical_lawhood.design.campaigns import CampaignLane, CampaignNode, CampaignNodeKind, CampaignSpec, DecisionRight
from empirical_lawhood.design.inquiry_methods import AssignedInquiryOpportunity, DependentAssessmentContract, FixedOpportunityStopping, FrozenInquiryConsumer, InquiryAuthorContract, InquiryAuthoringMode, InquiryEvidenceRole, InquiryMethodEvidence, MissingOpportunityRule
from empirical_lawhood.design.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft
from empirical_lawhood.design.response_algebra import MultiplicityKind, MultiplicitySpec
from empirical_lawhood.execution.capabilities import CapabilityPermission
from empirical_lawhood.execution.plans import ScientificStage

from empirical_lawhood.methods.assigned_opportunity_assessment.records import ACCESS, MAX_BYTES, NAMESPACE, OpportunityAuthorInput, OpportunityConsumer, OpportunityOperationConfig, OpportunityOutcomes, method


BUDGET = ResourceBudget(1, 512 * 1024**2, 0, 60, 1024**2, MAX_BYTES)
VISIBILITY = VisibilityCeiling.DEVELOPMENT_ONLY
PERMISSIONS = tuple(sorted((CapabilityPermission.READ_DEVELOPMENT, CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
                            CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS)))
QUESTION = "Does the complete assigned finite opportunity mean reach the frozen threshold?"
WORLD = "world." + NAMESPACE + ".exposed"


def stage(phase):
    return ScientificStage.SYNTHESIZE if phase == "author" else ScientificStage.FALSIFY


def allocation_for(source):
    return UnitAllocation("allocation." + NAMESPACE + "." + source.fingerprint(), (source.identity,),
        (IndependentUnit(source.independent_unit_id, source.record_id, "family." + NAMESPACE,
                         source.numerical_view_ids, True),),
        (UnitRoleAssignment(source.independent_unit_id, "development"),))


def opportunities_for(source):
    return tuple(AssignedInquiryOpportunity(name, source.identity, source.independent_unit_id,
                 source.numerical_view_ids) for name in source.opportunity_ids)


def assessment_cutoff(source):
    return InformationCutoff("cutoff." + NAMESPACE + ".assessment", source.clock_id,
                             CausalPhase.POST_OUTCOME, Decimal(len(source.opportunity_ids) + 1))


def condition_scope(source):
    return ScientificConditionScope(source.record_id, WORLD, source.record_id, ("outcome",), ("1",),
        "receiver.finite-assigned-mean", source.clock_id,
        "Equal weight over every assigned opportunity in this original finite source roster.",
        source_config_sha256=source.fingerprint(), population_id="population." + source.record_id,
        information_cutoff=assessment_cutoff(source), valid_from=Decimal(1),
        valid_until=assessment_cutoff(source).coordinate)


def consumer_for(source):
    return OpportunityConsumer("consumer." + NAMESPACE + "." + source.fingerprint(), source.identity)


def frozen_consumer(source):
    bound = QuantityBound("rule." + NAMESPACE + ".threshold.v1", "threshold", "1", Decimal(0), Decimal(1))
    return FrozenInquiryConsumer(consumer_for(source).identity, ObjectIdentity.from_record(bound.bound_id, bound), (bound,))


def scientific_contract(source):
    requirement = ScientificRequirementSpec("requirement." + NAMESPACE + ".frozen-procedure", NAMESPACE + ".assess",
        ConditionRole.INFORMATIONAL, "Supply the original actor-authored finite-census predicate to its independent assessor.",
        "Exact consumer, allowed threshold, original dependence roots, complete assignments and evaluator-only evidence.",
        condition_scope(source), NAMESPACE + ".assess",
        "A changed consumer, causal cutoff, original root, assigned denominator or evidence role refuses the join.",
        (ContributionRole.DESIGN_OPERAND, ContributionRole.INSTANCE_PRODUCT),
        background_assumption_ids=("assumption.supplied-outcomes-in-unit-interval",))
    connection = ScientificConnectionSpec("connection." + NAMESPACE + ".frozen-procedure", requirement.requirement_id,
        NAMESPACE + ".author", "product", "procedure", NAMESPACE + ".assess", "claim." + NAMESPACE,
        ContributionRole.INSTANCE_PRODUCT, requirement.falsifier)
    return requirement, connection


def make_config(author_input, outcomes, *, missingness=MissingOpportunityRule.RETAIN_OUTCOME_BOUNDS):
    if type(author_input) is not OpportunityAuthorInput or type(outcomes) is not OpportunityOutcomes:
        raise TypeError("fixture authoring requires the original separate actor and evaluator records")
    author_input.__post_init__()
    outcomes.__post_init__()
    source = author_input.source
    if source != outcomes.source:
        raise ValueError("author and evaluator do not share the same original source roster")
    consumer = consumer_for(source)
    requirement, _ = scientific_contract(source)
    author = InquiryAuthorContract("author-contract." + NAMESPACE + "." + author_input.fingerprint(),
        InquiryAuthoringMode.INVESTIGATOR_RECIPE, method("author"), consumer.identity,
        NAMESPACE + ".finite-assigned-enclosure", (method("assess"),), 1,
        (ObjectIdentity.from_record(requirement.requirement_id, requirement),),
        (InquiryMethodEvidence(author_input.identity, InquiryEvidenceRole.ACTOR_INPUT, author_input.availability),),
        InformationCutoff("cutoff." + NAMESPACE + ".author", source.clock_id, CausalPhase.PRE_ACTION, Decimal(0)),
        ClockCoordinate(source.clock_id, Decimal(1), "tick", "source-start", CoordinateOrigin.ABSOLUTE),
        CausalPhase.ACTION_REQUESTED, frozen_consumer(source))
    assessment = DependentAssessmentContract("assessment-contract." + NAMESPACE + "." + outcomes.fingerprint(),
        method("assess"), consumer.identity, condition_scope(source),
        QuantityBound("bound." + NAMESPACE + ".outcome", "outcome", "1", Decimal(0), Decimal(1)),
        allocation_for(source), opportunities_for(source),
        (InquiryMethodEvidence(outcomes.identity, InquiryEvidenceRole.EVALUATOR_DIAGNOSTIC, outcomes.availability),),
        FixedOpportunityStopping("stopping." + NAMESPACE, source.opportunity_ids, assessment_cutoff(source)),
        MultiplicitySpec("multiplicity." + NAMESPACE, MultiplicityKind.NOT_APPLICABLE, (), None),
        missingness, frozen_consumer(source))
    return OpportunityOperationConfig("config." + NAMESPACE + ".assess", "assess", source, consumer, author,
        (NamedDecimal("threshold", author_input.requested_threshold, "1"),), assessment)


def author_config(config):
    return replace(config, config_id="config." + NAMESPACE + ".author", phase="author", assessment=None)


def validate_author_contract(config):
    source, author = config.source, config.author
    requirement, _ = scientific_contract(source)
    if (author.frozen_consumer != frozen_consumer(source)
            or author.cutoff != InformationCutoff("cutoff." + NAMESPACE + ".author", source.clock_id, CausalPhase.PRE_ACTION, Decimal(0))
            or author.activation != ClockCoordinate(source.clock_id, Decimal(1), "tick", "source-start", CoordinateOrigin.ABSOLUTE)
            or author.activation_phase is not CausalPhase.ACTION_REQUESTED
            or author.missing_conditions != (ObjectIdentity.from_record(requirement.requirement_id, requirement),)):
        raise ValueError("author changes its original hypothesis, cutoff, activation or permissible parameter rule")


def validate_assessment_contract(config):
    contract, source = config.assessment, config.source
    if (contract.method != method("assess") or contract.estimand != config.consumer.identity
            or contract.scope != condition_scope(source) or contract.allocation != allocation_for(source)
            or contract.opportunities != opportunities_for(source) or contract.frozen_consumer != frozen_consumer(source)
            or contract.outcome_bound != QuantityBound("bound." + NAMESPACE + ".outcome", "outcome", "1", Decimal(0), Decimal(1))
            or contract.stopping != FixedOpportunityStopping("stopping." + NAMESPACE, source.opportunity_ids, assessment_cutoff(source))
            or contract.multiplicity != MultiplicitySpec("multiplicity." + NAMESPACE, MultiplicityKind.NOT_APPLICABLE, (), None)
            or len(contract.inputs) != 1 or contract.inputs[0].role is not InquiryEvidenceRole.EVALUATOR_DIAGNOSTIC
            or (contract.inputs[0].record.object_schema, contract.inputs[0].record.object_version)
            != (OpportunityOutcomes.SCHEMA, OpportunityOutcomes.VERSION)):
        raise ValueError("assessor substitutes original dependence, estimand, stopping, evidence role or consumer")


def scientific_root(config):
    source = config.source
    claim = ClaimSpec("claim." + NAMESPACE, WORLD, "population." + source.record_id,
        "The original assigned finite opportunity mean is at least " + str(config.parameters[0].value) + ".",
        "Only the complete original assigned finite census, conditional on the declared outcome bounds.",
        source.independent_unit_id, None, EvidenceCeiling.NON_PROMOTABLE, ACCESS, VISIBILITY,
        "Exposed software evidence; no population confidence, physical independence or scientific qualification.",
        ("assumption.supplied-outcomes-in-unit-interval",), numerical_view_ids=source.numerical_view_ids)
    operands = (source.identity, config.consumer.identity, config.author.identity, config.assessment.identity)
    return DevelopmentStudySpec("study." + NAMESPACE + "." + config.fingerprint(), QUESTION, source.identity, WORLD,
        WorldKind.ANALYTIC_REFERENCE, (source.independent_unit_id,), source.numerical_view_ids, (claim,),
        tuple(sorted(operands, key=lambda p: p.object_id)))


def external_contracts(config):
    return tuple(sorted((RecursiveExternalInput("external." + value.record.object_id, value.record.object_id,
        value.record.object_schema, "application/json", MAX_BYTES, ACCESS, VISIBILITY,
        value.record.object_fingerprint, scientific_role=role)
        for value, role in ((config.author.inputs[0], "SOURCE"), (config.assessment.inputs[0], "OUTCOME"))), key=lambda v: v.input_id))


def links_for(config):
    requirement, connection = scientific_contract(config.source)
    return tuple(sorted((
        RecursiveInputLink("edge." + NAMESPACE + ".actor", NAMESPACE + ".author", "actor",
            external_input_id="external." + config.author.inputs[0].record.object_id, scientific_role="SOURCE"),
        RecursiveInputLink("edge." + NAMESPACE + ".outcomes", NAMESPACE + ".assess", "outcomes",
            external_input_id="external." + config.assessment.inputs[0].record.object_id, scientific_role="OUTCOME"),
        RecursiveInputLink("edge." + NAMESPACE + ".procedure", NAMESPACE + ".assess", "procedure",
            NAMESPACE + ".author", "product", scientific_role="HISTORY", requirement_id=requirement.requirement_id,
            connection_id=connection.connection_id),
    ), key=lambda p: p.edge_id))


def campaign_for(root):
    prefix, budget = root.study_id, ResourceBudget.aggregate((BUDGET, BUDGET))
    policy = AuthorityPolicy(prefix + ".policy", "human.selected-operator", "researcher.exposed-development",
        (NAMESPACE + ".development",), frozenset({WorldKind.ANALYTIC_REFERENCE}),
        frozenset({AuthorityAction.READ_ONLY_EXPLORATION}), frozenset({SourceAccessClass.NONE}),
        ("supplied-exposed-evidence",), frozenset(), budget, ACCESS)
    node = CampaignNode(prefix + ".proposal", CampaignNodeKind.ANALYSIS_PROPOSAL, CampaignLane.EXPLORATORY,
        ObjectIdentity.from_record(root.study_id, root), (), LifecycleStatus.ACTIVE)
    return CampaignSpec(prefix + ".campaign", QUESTION, (root.system.object_id,), (WORLD,), (root.claims[0].claim_id,),
        budget, ObjectIdentity.from_record(policy.policy_id, policy),
        (DecisionRight(prefix + ".right", AuthorityAction.READ_ONLY_EXPLORATION, policy.delegate_id, policy.policy_id, True),),
        (node,), (node.node_id,), (node.node_id,), (), LifecycleStatus.ACTIVE)


def lower(author_input, outcomes, *, missingness=MissingOpportunityRule.RETAIN_OUTCOME_BOUNDS):
    from empirical_lawhood.methods.assigned_opportunity_assessment.bindings import operation_declarations

    config = make_config(author_input, outcomes, missingness=missingness)
    selected = (config, author_config(config))
    declarations = {d.capability_key: d for d in operation_declarations()}
    operations = tuple(RecursiveOperationSpec.from_config(node_id=c.node_id,
        selection=declarations[NAMESPACE + "." + c.phase].registration().selection,
        config_id=c.config_id, config=c, obligation_ids=("obligation." + c.node_id,), resource_budget=BUDGET)
        for c in selected)
    root = scientific_root(config)
    requirement, connection = scientific_contract(config.source)
    draft = RecursiveStudyDraft("draft." + NAMESPACE + "." + config.fingerprint(), QUESTION, campaign_for(root),
        (requirement,), (connection,), (), operations, external_contracts(config), links_for(config),
        tuple(c.node_id for c in selected), development_study=root)
    return draft, tuple(sorted(("external." + r.record_id, r) for r in (author_input, outcomes)))
