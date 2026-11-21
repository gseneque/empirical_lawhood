# SPDX-License-Identifier: MPL-2.0
"""Pure public authoring for one selected complete gas-start minimization."""

from empirical_lawhood.science.identity.authority import AuthorityAction, AuthorityPolicy, SourceAccessClass
from empirical_lawhood.science.evidence.evidence import ClaimSpec, EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import DevelopmentStudySpec
from empirical_lawhood.science.records.status import LifecycleStatus
from empirical_lawhood.science.models.worlds import WorldKind
from empirical_lawhood.design.campaigns import CampaignLane, CampaignNode, CampaignNodeKind, CampaignSpec, DecisionRight
from empirical_lawhood.design.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft
from empirical_lawhood.execution.plans import ScientificStage
from empirical_lawhood.domains.rubisco.rubisco_response.gas_relaxation_operation import UNIT, capability_for, operands, operation_declaration, resource_budget


def development_root(config, *, study_id):
    views = ('view.gas-start.'+config.selection.fingerprint(),)
    claim = ClaimSpec('claim.gas-start.original-endpoint', 'world.periodic-gp-gas-start-relaxation',
        'population.one-source-assembly-selected-neutral-gas',
        'Does this source-bound neutral-gas starting point reach a stationary endpoint of the selected complete reference potential?',
        'One existing assembly/material/site/gas view; no additional biological unit, inferred state weight or replacement of the original starting-state census.',
        UNIT, None, EvidenceCeiling.NON_PROMOTABLE, OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY,
        'Numerical convergence and geometric observations do not admit a gas basin, electronic character, equilibrium population or physical rate.',
        ('assumption.selected-neutral-gas-electronic-hypothesis', 'assumption.selected-periodic-qmmm-reference-potential'), numerical_view_ids=views)
    return DevelopmentStudySpec(study_id, claim.proposition, config.selection.identity, claim.world_id,
        WorldKind.NUMERICAL_SIMULATOR, (UNIT,), views, (claim,), operands(config))


def input_selections(config):
    return (('native-arrays', config.selection.prototype.coordinates.identity, config.selection.prototype.coordinates.canonical_size_bytes()),
        ('native-model', config.selection.prototype.representation, config.representation_size_bytes),
        ('native-provenance', config.provenance.identity, config.provenance.canonical_size_bytes()),
        ('native-selection', config.selection.identity, config.selection.canonical_size_bytes()),
        ('native-source', config.raw_sources, config.raw_source_size_bytes))


def native_external_inputs(config):
    return tuple(RecursiveExternalInput('external.gas-relaxation.'+name, pin.object_id, pin.object_schema,
        'application/json', size, OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY,
        pin.object_fingerprint, 'SOURCE') for name, pin, size in input_selections(config))


def native_input_links(config):
    return tuple(RecursiveInputLink('edge.gas-relaxation.'+name, capability_for(config), name,
        external_input_id='external.gas-relaxation.'+name, scientific_role='SOURCE') for name, _, _ in input_selections(config))


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
        raise ValueError('gas relaxation graph changes its selected original scope or complete inputs')


def gas_relaxation_draft(config, *, draft_id=None):
    capability = capability_for(config)
    draft_id = 'draft.gas-relaxation.'+config.fingerprint() if draft_id is None else draft_id
    root = development_root(config, study_id='study.'+draft_id)
    policy = AuthorityPolicy('policy.'+draft_id, 'owner.local-researcher', 'operator.local-development', (root.study_id,),
        frozenset((root.world_kind,)), frozenset((AuthorityAction.REPOSITORY_IMPLEMENTATION, AuthorityAction.SIMULATION_EXECUTION)),
        frozenset((SourceAccessClass.NONE,)), ('gate.local-nonactuating-development',), frozenset(), resource_budget(config), OutcomeAccess.DEVELOPMENT_VISIBLE)
    node = CampaignNode('design.'+draft_id, CampaignNodeKind.EVIDENCE_SNAPSHOT, CampaignLane.EXPLORATORY,
        ObjectIdentity.from_record(root.study_id, root), (), LifecycleStatus.ACTIVE)
    campaign = CampaignSpec('campaign.'+draft_id, root.question, (root.system.object_id,), (root.world_id,),
        tuple(claim.claim_id for claim in root.claims), resource_budget(config), ObjectIdentity.from_record(policy.policy_id, policy),
        (DecisionRight('decision-right.'+draft_id, AuthorityAction.SIMULATION_EXECUTION, 'owner.local-researcher', policy.policy_id, False),),
        (node,), (node.node_id,), (node.node_id,), (), LifecycleStatus.ACTIVE)
    operation = RecursiveOperationSpec.from_config(node_id=capability,
        selection=operation_declaration(accelerated=config.ACCELERATED).registration().selection,
        config_id=config.config_id, config=config, obligation_ids=('obligation.gas-start.complete-original-attempt',),
        resource_budget=resource_budget(config), resource_lock_ids=('gp-periodic-force-native-worker',), maximum_attempts=1)
    return RecursiveStudyDraft(draft_id, root.question, campaign, (), (), (), (operation,),
        native_external_inputs(config), native_input_links(config), (capability,), development_study=root)
