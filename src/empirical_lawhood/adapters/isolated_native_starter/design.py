# SPDX-License-Identifier: MPL-2.0
"""Derive the complete exposed development design through existing contracts."""

from empirical_lawhood.science.identity.authority import AuthorityAction, AuthorityPolicy, ResourceBudget, SourceAccessClass
from empirical_lawhood.science.evidence.evidence import ClaimSpec, EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import DevelopmentStudySpec
from empirical_lawhood.science.records.status import LifecycleStatus
from empirical_lawhood.science.models.worlds import WorldKind
from empirical_lawhood.design.campaigns import CampaignLane, CampaignNode, CampaignNodeKind, CampaignSpec, DecisionRight
from empirical_lawhood.design.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft
from empirical_lawhood.execution.capabilities import CapabilityPermission

from empirical_lawhood.adapters.isolated_native_starter.records import MAX_SOURCE_BYTES, NAMESPACE, UNIT, SquareConfig

# Wall reservation bounds this disclosed developer calculation only. It is not
# a measured CPU quantity or a policy for any unrelated native route.
BUDGET = ResourceBudget(1, 1024**3, 0, 120, MAX_SOURCE_BYTES, 512 * 1024)
ACCESS, VISIBILITY = OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY
PERMISSIONS = tuple(sorted((CapabilityPermission.READ_DEVELOPMENT, CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
                            CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS)))
QUESTION = "Does the selected NumPy sum of integer squares equal the independent finite-sum formula?"
WORLD = "world." + NAMESPACE + ".exposed-software"


def config_for(specification):
    return SquareConfig("config." + NAMESPACE + "." + specification.fingerprint(), specification)


def root_for(config):
    spec = config.specification
    study = "study." + NAMESPACE + "." + spec.fingerprint()
    claim = ClaimSpec("claim." + study, WORLD, "population.exposed-integer-sequence", QUESTION,
        "One exposed finite sequence; the exercise establishes software behavior only.",
        "unit.dimensionless-integer", None, EvidenceCeiling.NON_PROMOTABLE, ACCESS, VISIBILITY,
        "No physical observation, fresh confirmation or scientific qualification.",
        ("assumption.exact-bounded-integer-arithmetic",))
    return DevelopmentStudySpec(study, QUESTION, spec.operand, WORLD, WorldKind.ANALYTIC_REFERENCE,
        (UNIT,), (), (claim,), tuple(sorted((spec.identity, spec.operand, spec.provenance), key=lambda r: r.object_id)))


def input_contracts(config):
    spec = config.specification
    return tuple(sorted((RecursiveExternalInput("external." + r.object_id, r.object_id, r.object_schema,
        "application/json", MAX_SOURCE_BYTES, ACCESS, VISIBILITY, r.object_fingerprint, scientific_role="SOURCE")
        for r in (spec.operand, spec.provenance)), key=lambda r: r.input_id))


def links_for(config):
    return tuple(sorted((RecursiveInputLink("edge." + config.node_id + "." + port,
        config.node_id, port, external_input_id="external." + identity.object_id, scientific_role="SOURCE")
        for port, identity in (("operand", config.specification.operand), ("provenance", config.specification.provenance))),
        key=lambda r: r.edge_id))


def campaign_for(root):
    policy = AuthorityPolicy(root.study_id + ".policy", "human.selected-operator", "researcher.exposed-development",
        (NAMESPACE + ".development",), frozenset({WorldKind.ANALYTIC_REFERENCE}),
        frozenset({AuthorityAction.READ_ONLY_EXPLORATION}), frozenset({SourceAccessClass.NONE}),
        ("supplied-exposed-integers",), frozenset(), BUDGET, ACCESS)
    node = CampaignNode(root.study_id + ".proposal", CampaignNodeKind.ANALYSIS_PROPOSAL, CampaignLane.EXPLORATORY,
        ObjectIdentity.from_record(root.study_id, root), (), LifecycleStatus.ACTIVE)
    return CampaignSpec(root.study_id + ".campaign", QUESTION, (root.system.object_id,), (WORLD,), (root.claims[0].claim_id,),
        BUDGET, ObjectIdentity.from_record(policy.policy_id, policy),
        (DecisionRight(root.study_id + ".right", AuthorityAction.READ_ONLY_EXPLORATION, policy.delegate_id, policy.policy_id, True),),
        (node,), (node.node_id,), (node.node_id,), (), LifecycleStatus.ACTIVE)


def lower(specification, operand, provenance):
    from empirical_lawhood.adapters.isolated_native_starter.bindings import operation_declaration

    config = config_for(specification)
    declaration = operation_declaration()
    operation = RecursiveOperationSpec.from_config(node_id=config.node_id,
        selection=declaration.registration().selection, config_id=config.config_id, config=config,
        obligation_ids=("obligation." + config.node_id,), resource_budget=BUDGET)
    root = root_for(config)
    draft = RecursiveStudyDraft(draft_id="draft." + specification.specification_id, question=QUESTION,
        campaign=campaign_for(root), requirements=(), connections=(), suppliers=(), operations=(operation,),
        external_inputs=input_contracts(config), links=links_for(config), selected_operation_ids=(config.node_id,),
        development_study=root)
    return draft, tuple(sorted(("external." + value.identity.object_id, value) for value in (operand, provenance)))
