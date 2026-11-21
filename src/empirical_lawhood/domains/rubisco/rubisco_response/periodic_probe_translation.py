# SPDX-License-Identifier: MPL-2.0
"""Pure graph derivation for one complete periodic force/cost observation."""

from empirical_lawhood.science.identity.authority import AuthorityAction, AuthorityPolicy, SourceAccessClass
from empirical_lawhood.science.evidence.evidence import ClaimSpec, EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import DevelopmentStudySpec
from empirical_lawhood.science.records.status import LifecycleStatus
from empirical_lawhood.science.models.worlds import WorldKind
from empirical_lawhood.design.campaigns import CampaignLane, CampaignNode, CampaignNodeKind, CampaignSpec, DecisionRight
from empirical_lawhood.design.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft
from empirical_lawhood.execution.plans import ScientificStage
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_operation import UNIT, capability_for, is_restart, operands, operation_declaration, resource_budget, selected_request
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_density_seed import DENSITY_SCHEMA


def development_root(config, *, study_id):
    capability_for(config)
    view = 'view.periodic-force.'+config.selection.fingerprint()
    claim = ClaimSpec('claim.periodic-force.original-return','world.periodic-gp-force',
        'population.one-source-assembly-one-complete-coupled-return',
        'What complete energy, physical-atom gradient and cost does the selected periodic Gp operator actually return?',
        'One selected complete assembly and focal site at one geometry; zero independent biological replicates.',
        UNIT,None,EvidenceCeiling.NON_PROMOTABLE,OutcomeAccess.DEVELOPMENT_VISIBLE,VisibilityCeiling.DEVELOPMENT_ONLY,
        'An authentic force return and measured cost do not establish derivatives, numerical convergence, chemical accuracy, rates or mutation response.',
        ('assumption.selected-periodic-qmmm-reference-potential',),numerical_view_ids=(view,))
    return DevelopmentStudySpec(study_id,claim.proposition,config.selection.identity,claim.world_id,WorldKind.NUMERICAL_SIMULATOR,
        (UNIT,),(view,),(claim,),operands(config))


def input_selections(config):
    records = (('native-arrays',config.selection.coordinates.identity,config.selection.coordinates.canonical_size_bytes()),
        ('native-model',config.selection.representation,config.representation_size_bytes),
        ('native-probe',config.selection.probe.identity,config.selection.probe.canonical_size_bytes()),
        ('native-provenance',config.provenance.identity,config.provenance.canonical_size_bytes()),
        ('native-request',selected_request(config).identity,selected_request(config).canonical_size_bytes()),
        ('native-source',config.raw_sources,config.raw_source_size_bytes))
    return tuple(sorted((*records, ('native-seed', config.seed.identity, config.seed.canonical_size_bytes()),
        ('native-density', config.seed.density_bytes, config.seed.arrays.size_bytes)))) if is_restart(config) else records


def native_external_inputs(config):
    return tuple(RecursiveExternalInput('external.periodic-force.'+name,pin.object_id,pin.object_schema,
        'application/octet-stream' if pin.object_schema == DENSITY_SCHEMA else 'application/json',
        size,OutcomeAccess.DEVELOPMENT_VISIBLE,VisibilityCeiling.DEVELOPMENT_ONLY,
        pin.object_fingerprint,'SOURCE') for name,pin,size in input_selections(config))


def native_input_links(config):
    return tuple(RecursiveInputLink('edge.periodic-force.'+name,capability_for(config),name,
        external_input_id='external.periodic-force.'+name,scientific_role='SOURCE') for name,_,_ in input_selections(config))


def validate_root(config,context):
    capability = capability_for(config)
    if (type(context.root) is not DevelopmentStudySpec
            or context.root != development_root(config,study_id=context.root.study_id)
            or context.node_id != capability or context.stage is not ScientificStage.ACQUIRE
            or context.unit_ids != (UNIT,) or context.selected_unit_ids != (UNIT,) or not context.complete_unit_census
            or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or context.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY
            or len(context.config_inputs) != 1 or context.config_inputs[0].record is not config
            or context.config_inputs[0].node_id != capability or context.requirements or context.connections
            or context.external_inputs != native_external_inputs(config) or context.links != native_input_links(config)):
        raise ValueError('periodic force graph substitutes its complete original scientific scope')


def periodic_probe_draft(config, *, draft_id=None):
    capability = capability_for(config)
    budget = resource_budget(config)
    draft_id = 'draft.periodic-force.'+config.fingerprint() if draft_id is None else draft_id
    root = development_root(config,study_id='study.'+draft_id)
    policy = AuthorityPolicy('policy.'+draft_id,'owner.local-researcher','operator.local-development',(root.study_id,),
        frozenset((root.world_kind,)),frozenset((AuthorityAction.REPOSITORY_IMPLEMENTATION,AuthorityAction.SIMULATION_EXECUTION)),
        frozenset((SourceAccessClass.NONE,)),('gate.local-nonactuating-development',),frozenset(),budget,OutcomeAccess.DEVELOPMENT_VISIBLE)
    node = CampaignNode('design.'+draft_id,CampaignNodeKind.EVIDENCE_SNAPSHOT,CampaignLane.EXPLORATORY,
        ObjectIdentity.from_record(root.study_id,root),(),LifecycleStatus.ACTIVE)
    campaign = CampaignSpec('campaign.'+draft_id,root.question,(root.system.object_id,),(root.world_id,),
        tuple(c.claim_id for c in root.claims),budget,ObjectIdentity.from_record(policy.policy_id,policy),
        (DecisionRight('decision-right.'+draft_id,AuthorityAction.SIMULATION_EXECUTION,'owner.local-researcher',policy.policy_id,False),),
        (node,),(node.node_id,),(node.node_id,),(),LifecycleStatus.ACTIVE)
    operation = RecursiveOperationSpec.from_config(node_id=capability,
        selection=operation_declaration(restart=is_restart(config), accelerated=config.ACCELERATED).registration().selection,
        config_id=config.config_id,config=config,obligation_ids=('obligation.periodic-force.complete-original-atom-census',),
        resource_budget=budget,resource_lock_ids=('gp-periodic-force-native-worker',),maximum_attempts=1)
    return RecursiveStudyDraft(draft_id,root.question,campaign,(),(),(),(operation,),
        native_external_inputs(config),native_input_links(config),(capability,),development_study=root)
