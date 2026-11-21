# SPDX-License-Identifier: MPL-2.0
"""Pure authoring of one complete member of a matched four-material plan."""

from empirical_lawhood.science.identity.authority import AuthorityAction, AuthorityPolicy, SourceAccessClass
from empirical_lawhood.science.evidence.evidence import ClaimSpec, EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import DevelopmentStudySpec
from empirical_lawhood.science.records.status import LifecycleStatus
from empirical_lawhood.science.models.worlds import WorldKind
from empirical_lawhood.design.campaigns import CampaignLane, CampaignNode, CampaignNodeKind, CampaignSpec, DecisionRight
from empirical_lawhood.design.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft
from empirical_lawhood.execution.plans import ScientificStage
from empirical_lawhood.domains.rubisco.rubisco_response.active_relaxation_operation import resource_budget, UNIT, capability_for, conditional_configuration, operands, operation_declaration, state_census_for


def development_root(config, *, study_id):
    conditional = conditional_configuration(config)
    views = tuple(sorted('view.active-relaxation.'+config.model_name+'.'+site+'.'+state+'.'+occupancy.lower()
        for site, state, occupancy in state_census_for(config)))
    population = ('One original assembly and four matched material views; only the prospectively selected site/state subset is measured. '
        'All other states remain unmeasured, with no inferred populations.') if conditional else (
        'One original assembly, four matched material views and eight nested sites; this operation retains all 96 starts for one material.')
    claim = ClaimSpec('claim.active-relaxation.original-endpoints', 'world.periodic-gp-active-relaxation',
        'population.one-source-assembly-matched-chemical-starts',
        'Which declared catalytic starting states retain their geometry and reach a stationary point of the selected full reference potential?',
        population,
        UNIT, None, EvidenceCeiling.NON_PROMOTABLE, OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY,
        'A stationary endpoint is neither an equilibrium population nor a physical rate, derivative validation or molecular-model admission.',
        ('assumption.selected-periodic-qmmm-reference-potential',), numerical_view_ids=views)
    return DevelopmentStudySpec(study_id, claim.proposition, config.plan.identity, claim.world_id, WorldKind.NUMERICAL_SIMULATOR,
        (UNIT,), views, (claim,), operands(config))


def input_selections(config):
    return tuple(sorted((('native-arrays', config.prototype.coordinates.identity, config.prototype.coordinates.canonical_size_bytes()),
        ('native-model', config.prototype.representation, config.representation_size_bytes),
        ('native-plan', config.plan.identity, config.plan.canonical_size_bytes()),
        ('native-preparation', config.preparation, config.preparation_size_bytes),
        ('native-prototype', config.prototype.identity, config.prototype.canonical_size_bytes()),
        ('native-provenance', config.provenance.identity, config.provenance.canonical_size_bytes()),
        *((f'native-seed.{i:03}', seed.identity, seed.canonical_size_bytes()) for i, seed in enumerate(config.seeds)),
        ('native-source', config.raw_sources, config.raw_source_size_bytes),
        *((('native-conditional-selection', config.selection.identity, config.selection.canonical_size_bytes()),)
            if conditional_configuration(config) else ())), key=lambda row:row[0]))


def native_external_inputs(config):
    return tuple(RecursiveExternalInput('external.active-relaxation.'+name, pin.object_id, pin.object_schema,
        'application/json', size, OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY,
        pin.object_fingerprint, 'SOURCE') for name, pin, size in input_selections(config))


def native_input_links(config):
    return tuple(RecursiveInputLink('edge.active-relaxation.'+name, capability_for(config), name,
        external_input_id='external.active-relaxation.'+name, scientific_role='SOURCE') for name, _, _ in input_selections(config))


def validate_root(config, context):
    capability = capability_for(config)
    if (type(context.root) is not DevelopmentStudySpec or context.root != development_root(config, study_id=context.root.study_id)
            or context.node_id != capability or context.stage is not ScientificStage.ACQUIRE
            or context.unit_ids != (UNIT,) or context.selected_unit_ids != (UNIT,) or not context.complete_unit_census
            or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or context.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY
            or len(context.config_inputs) != 1 or context.config_inputs[0].record is not config
            or context.config_inputs[0].node_id != capability or context.requirements or context.connections
            or context.external_inputs != native_external_inputs(config) or context.links != native_input_links(config)):
        raise ValueError('active relaxation graph changes its complete matched scientific scope')


def active_relaxation_draft(config, *, draft_id=None):
    conditional = conditional_configuration(config)
    capability = capability_for(config)
    draft_id = 'draft.active-relaxation.'+config.fingerprint() if draft_id is None else draft_id
    root = development_root(config, study_id='study.'+draft_id)
    policy = AuthorityPolicy('policy.'+draft_id, 'owner.local-researcher', 'operator.local-development', (root.study_id,),
        frozenset((root.world_kind,)), frozenset((AuthorityAction.REPOSITORY_IMPLEMENTATION, AuthorityAction.SIMULATION_EXECUTION)),
        frozenset((SourceAccessClass.NONE,)), ('gate.local-nonactuating-development',), frozenset(), resource_budget(config), OutcomeAccess.DEVELOPMENT_VISIBLE)
    node = CampaignNode('design.'+draft_id, CampaignNodeKind.EVIDENCE_SNAPSHOT, CampaignLane.EXPLORATORY,
        ObjectIdentity.from_record(root.study_id, root), (), LifecycleStatus.ACTIVE)
    campaign = CampaignSpec('campaign.'+draft_id, root.question, (root.system.object_id,), (root.world_id,),
        tuple(c.claim_id for c in root.claims), resource_budget(config), ObjectIdentity.from_record(policy.policy_id, policy),
        (DecisionRight('decision-right.'+draft_id, AuthorityAction.SIMULATION_EXECUTION, 'owner.local-researcher', policy.policy_id, False),),
        (node,), (node.node_id,), (node.node_id,), (), LifecycleStatus.ACTIVE)
    obligation = ('obligation.active-relaxation.complete-selected-conditional-census' if conditional
        else 'obligation.active-relaxation.complete-original-site-state-census')
    operation = RecursiveOperationSpec.from_config(node_id=capability,
        selection=operation_declaration(conditional=conditional, accelerated=config.ACCELERATED).registration().selection,
        config_id=config.config_id, config=config, obligation_ids=(obligation,),
        resource_budget=resource_budget(config), resource_lock_ids=('gp-periodic-force-native-worker',), maximum_attempts=1)
    return RecursiveStudyDraft(draft_id, root.question, campaign, (), (), (), (operation,),
        native_external_inputs(config), native_input_links(config), (capability,), development_study=root)
