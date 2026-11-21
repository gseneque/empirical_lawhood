# SPDX-License-Identifier: MPL-2.0
"""One separately admitted derivative operation on original exposed evidence."""

from empirical_lawhood.methods.mass_balance_starter.design import ACCESS, BUDGET, PERMISSIONS as PERMISSIONS, VISIBILITY
from empirical_lawhood.science.identity.authority import AuthorityAction, AuthorityPolicy, SourceAccessClass
from empirical_lawhood.science.evidence.evidence import ClaimSpec, EvidenceCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import DevelopmentStudySpec
from empirical_lawhood.science.records.status import LifecycleStatus
from empirical_lawhood.science.models.worlds import WorldKind
from empirical_lawhood.design.campaigns import CampaignLane, CampaignNode, CampaignNodeKind, CampaignSpec, DecisionRight
from empirical_lawhood.design.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft

from empirical_lawhood.methods.mass_balance_revision.records import MAX_BYTES, ForecastUpgradeConfig

QUESTION = 'Does the explicitly converted gram representation preserve every original kg forecast and its retained evidence?'


def config_for(specification):
    return ForecastUpgradeConfig('config.mass-balance.upgrade.' + specification.fingerprint(), specification)


def root_for(config):
    specification = config.specification
    study_id = 'study.mass-balance.upgrade.' + specification.fingerprint()
    world = 'world.mass-balance.exposed-revision'
    claim = ClaimSpec('claim.' + study_id, world, specification.scope.population_id, QUESTION,
        'The complete retained exposed unit census; this operation introduces no new measurements.',
        'unit.original-mass-case', None, EvidenceCeiling.NON_PROMOTABLE, ACCESS, VISIBILITY,
        'A representation conversion preserves original adverse and missing findings without fresh qualification.',
        ('assumption.exact-si-mass-unit-conversion',))
    return DevelopmentStudySpec(study_id, QUESTION,
        ObjectIdentity.from_record('system.mass-balance.' + specification.scope.fingerprint(), specification.scope),
        world, WorldKind.ANALYTIC_REFERENCE, specification.independent_unit_ids, (), (claim,),
        tuple(sorted((specification.identity, specification.source), key=lambda value:value.object_id)))


def external_for(config):
    source = config.specification.source
    return RecursiveExternalInput('external.' + source.object_id, source.object_id, source.object_schema,
        'application/json', MAX_BYTES, ACCESS, VISIBILITY, source.object_fingerprint, scientific_role='HISTORY')


def link_for(config):
    return RecursiveInputLink('edge.' + config.node_id + '.original', config.node_id, 'original',
        external_input_id=external_for(config).input_id, scientific_role='HISTORY')


def campaign_for(root):
    prefix = root.study_id
    policy = AuthorityPolicy(prefix + '.policy', 'human.selected-operator', 'researcher.exposed-development',
        ('mass-balance.forecast-upgrade',), frozenset({WorldKind.ANALYTIC_REFERENCE}),
        frozenset({AuthorityAction.READ_ONLY_EXPLORATION}), frozenset({SourceAccessClass.NONE}),
        ('original-exposed-forecast-and-assessment',), frozenset(), BUDGET, ACCESS)
    node = CampaignNode(prefix + '.proposal', CampaignNodeKind.ANALYSIS_PROPOSAL, CampaignLane.EXPLORATORY,
        ObjectIdentity.from_record(root.study_id, root), (), LifecycleStatus.ACTIVE)
    return CampaignSpec(prefix + '.campaign', QUESTION, (root.system.object_id,), (root.world_id,),
        (root.claims[0].claim_id,), BUDGET, ObjectIdentity.from_record(policy.policy_id, policy),
        (DecisionRight(prefix + '.right', AuthorityAction.READ_ONLY_EXPLORATION, policy.delegate_id, policy.policy_id, True),),
        (node,), (node.node_id,), (node.node_id,), (), LifecycleStatus.ACTIVE)


def lower(specification, source):
    from empirical_lawhood.methods.mass_balance_revision.bindings import operation_declarations
    config = config_for(specification)
    declaration, = operation_declarations()
    operation = RecursiveOperationSpec.from_config(node_id=config.node_id,
        selection=declaration.registration().selection, config_id=config.config_id, config=config,
        obligation_ids=('obligation.' + config.node_id,), resource_budget=BUDGET)
    root = root_for(config)
    draft = RecursiveStudyDraft('draft.' + specification.record_id, QUESTION, campaign_for(root), (), (), (),
        (operation,), (external_for(config),), (link_for(config),), (config.node_id,), development_study=root)
    return draft, ((external_for(config).input_id, source),)
