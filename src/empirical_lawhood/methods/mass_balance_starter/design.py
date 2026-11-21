# SPDX-License-Identifier: MPL-2.0
"""Derive the complete two-operation design from supplied exposed evidence."""

from empirical_lawhood.science.identity.authority import AuthorityAction, AuthorityPolicy, ResourceBudget, SourceAccessClass
from empirical_lawhood.science.evidence.evidence import ClaimSpec, EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import ConditionRole, ContributionRole, DevelopmentStudySpec, ScientificConditionScope, ScientificConnectionSpec, ScientificRequirementSpec
from empirical_lawhood.science.records.status import LifecycleStatus
from empirical_lawhood.science.models.worlds import WorldKind
from empirical_lawhood.design.campaigns import CampaignLane, CampaignNode, CampaignNodeKind, CampaignSpec, DecisionRight
from empirical_lawhood.design.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft
from empirical_lawhood.execution.capabilities import CapabilityPermission
from empirical_lawhood.execution.plans import ScientificStage

from empirical_lawhood.methods.mass_balance_starter.records import MAX_BYTES, NAMESPACE, MassOperationConfig, MassOutcome, MassOutcomes, MassPredictor, MassPredictors
from empirical_lawhood.methods.mass_balance_starter.science import prediction_config

BUDGET = ResourceBudget(1, 512 * 1024**2, 0, 60, 1024**2, MAX_BYTES)
ACCESS, VISIBILITY = OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY
PERMISSIONS = tuple(sorted((CapabilityPermission.READ_DEVELOPMENT, CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
                            CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS)))
QUESTION = "Does initial mass plus added mass agree with the supplied final mass within the selected tolerance?"
WORLD = "world." + NAMESPACE + ".exposed-analysis"


def stage(phase):
    return ScientificStage.TRANSFORM if phase == "predict" else ScientificStage.FALSIFY


def inputs_for(evidence):
    prefix = NAMESPACE + "." + evidence.fingerprint()
    return (
        MassPredictors(prefix + ".predictors", evidence.scope, evidence.identity,
                       tuple(MassPredictor(r.unit_id, r.initial_kg, r.added_kg) for r in evidence.observations)),
        MassOutcomes(prefix + ".outcomes", evidence.scope, evidence.identity,
                     tuple(MassOutcome(r.unit_id, r.final_kg) for r in evidence.observations)),
    )


def config_for(specification, evidence):
    predictors, outcomes = inputs_for(evidence)
    return MassOperationConfig("config." + NAMESPACE + "." + specification.fingerprint() + ".assess", "assess",
        specification.identity, specification.scope, specification.independent_unit_ids,
        predictors.identity, outcomes.identity, specification.tolerance_kg)


def scientific_root(config):
    study_id = "study." + NAMESPACE + "." + config.specification.object_fingerprint
    system = ObjectIdentity.from_record("system." + NAMESPACE + "." + config.scope.fingerprint(), config.scope)
    claim = ClaimSpec("claim." + study_id, WORLD, config.scope.population_id, QUESTION,
        "Supplied closed additive mass cases; missing final observations remain in the denominator.",
        "unit.independent-mass-case", None, EvidenceCeiling.NON_PROMOTABLE, ACCESS, VISIBILITY,
        "Exposed development evidence gives no fresh confirmation or qualification.",
        ("assumption.supplied-case-independence",))
    return DevelopmentStudySpec(study_id, QUESTION, system, WORLD, WorldKind.ANALYTIC_REFERENCE,
        config.independent_unit_ids, (), (claim,), tuple(sorted(
            (config.specification, config.predictors, config.outcomes), key=lambda p: p.object_id)))


def scientific_contract(config):
    root, parent = scientific_root(config), prediction_config(config)
    scope = ScientificConditionScope(root.system.object_id, WORLD, config.scope.source_id,
        ("final-mass",), ("kg",), config.scope.receiver_id, config.scope.clock_id,
        "Final mass after the declared addition in the supplied closed system.",
        source_config_sha256=config.predictors.object_fingerprint, population_id=config.scope.population_id)
    requirement = ScientificRequirementSpec("requirement." + config.node_id, config.node_id, ConditionRole.INFORMATIONAL,
        "Supply a prediction for every original independent unit to the observation-based falsifier.",
        "Exact original predictor identity, scientific scope, units and complete forecast census.",
        scope, config.node_id, "A missing unit or a substituted predictor, scope or unit invalidates the supply.",
        (ContributionRole.INSTANCE_PRODUCT,), background_assumption_ids=("assumption.supplied-case-independence",))
    connection = ScientificConnectionSpec("connection." + config.node_id, requirement.requirement_id,
        parent.node_id, "product", "forecast", config.node_id, root.claims[0].claim_id,
        ContributionRole.INSTANCE_PRODUCT, requirement.falsifier)
    return requirement, connection


def external_contracts(config):
    return tuple(sorted((RecursiveExternalInput("external." + p.object_id, p.object_id, p.object_schema,
        "application/json", MAX_BYTES, ACCESS, VISIBILITY, p.object_fingerprint, scientific_role=role)
        for p, role in ((config.predictors, "SOURCE"), (config.outcomes, "OUTCOME"))), key=lambda p: p.input_id))


def links_for(config):
    parent = prediction_config(config)
    requirement, connection = scientific_contract(config)
    return tuple(sorted((
        RecursiveInputLink("edge." + parent.node_id + ".predictors", parent.node_id, "predictors",
            external_input_id="external." + config.predictors.object_id, scientific_role="SOURCE"),
        RecursiveInputLink("edge." + config.node_id + ".outcomes", config.node_id, "outcomes",
            external_input_id="external." + config.outcomes.object_id, scientific_role="OUTCOME"),
        RecursiveInputLink("edge." + config.node_id + ".forecast", config.node_id, "forecast",
            parent.node_id, "product", scientific_role="HISTORY", requirement_id=requirement.requirement_id,
            connection_id=connection.connection_id),
    ), key=lambda p: p.edge_id))


def campaign_for(root):
    # This metadata describes an exposed analysis. It contains no grant or signature.
    prefix = root.study_id
    budget = ResourceBudget.aggregate((BUDGET, BUDGET))
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


def lower(specification, evidence):
    from empirical_lawhood.methods.mass_balance_starter.bindings import operation_declarations

    config = config_for(specification, evidence)
    selected = (config, prediction_config(config))
    declarations = {d.capability_key.rsplit(".", 1)[-1]: d for d in operation_declarations()}
    operations = tuple(RecursiveOperationSpec.from_config(node_id=c.node_id,
        selection=declarations[c.phase].registration().selection, config_id=c.config_id, config=c,
        obligation_ids=("obligation." + c.node_id,), resource_budget=BUDGET) for c in selected)
    root = scientific_root(config)
    requirement, connection = scientific_contract(config)
    draft = RecursiveStudyDraft(draft_id="draft." + specification.specification_id, question=QUESTION,
        campaign=campaign_for(root), requirements=(requirement,), connections=(connection,), suppliers=(),
        operations=operations, external_inputs=external_contracts(config), links=links_for(config),
        selected_operation_ids=tuple(c.node_id for c in selected), development_study=root)
    return draft, tuple(sorted(("external." + r.record_id, r) for r in inputs_for(evidence)))
