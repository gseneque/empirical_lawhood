# SPDX-License-Identifier: MPL-2.0
"""Derive the two-gas construction graph without entering a native library."""

from empirical_lawhood.science.identity.authority import AuthorityAction, AuthorityPolicy, SourceAccessClass
from empirical_lawhood.science.evidence.evidence import ClaimSpec, EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import DevelopmentStudySpec
from empirical_lawhood.science.records.status import LifecycleStatus
from empirical_lawhood.science.models.worlds import WorldKind
from empirical_lawhood.design.campaigns import CampaignLane, CampaignNode, CampaignNodeKind, CampaignSpec, DecisionRight
from empirical_lawhood.design.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft
from empirical_lawhood.execution.plans import ScientificStage
from empirical_lawhood.domains.rubisco.rubisco_response.gas_parameter_operation import BUDGET, CAPABILITY, UNIT, GasParameterConfig, operands, operation_declaration
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact


def development_root(config, *, study_id):
    exact(config, GasParameterConfig)
    view = 'view.complete-host-and-two-source-gases'
    claim = ClaimSpec('claim.gas-parameter-assignment', 'world.gp-gas-parameters',
        'population.one-source-assembly-two-nested-gas-alternatives',
        'Do both gas parameter extensions preserve every original host parameter and add only the selected source stock?',
        'One original complete host; two nested gas alternatives; zero independent biological units.',
        UNIT, None, EvidenceCeiling.NON_PROMOTABLE, OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY,
        'Parameter correspondence establishes no coordinate geometry, reactive chemistry, ensemble or rate.',
        ('assumption.source-selected-gas-stock-lorentz-berthelot-cross-terms',), numerical_view_ids=(view,))
    return DevelopmentStudySpec(study_id, claim.proposition, config.source, claim.world_id, WorldKind.NUMERICAL_SIMULATOR,
        (UNIT,), (view,), (claim,), operands(config))


def native_external_inputs(config):
    rows = (('native-provenance', config.provenance.identity, config.provenance.canonical_size_bytes()),
        ('native-source', config.source, config.source_size_bytes))
    return tuple(RecursiveExternalInput('external.gas-parameters.'+name, pin.object_id, pin.object_schema,
        'application/json', size, OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY,
        pin.object_fingerprint, 'SOURCE') for name, pin, size in rows)


def native_input_links(config):
    return tuple(RecursiveInputLink('edge.gas-parameters.'+name, CAPABILITY, name,
        external_input_id='external.gas-parameters.'+name, scientific_role='SOURCE')
        for name in ('native-provenance', 'native-source'))


def validate_root(config, context):
    if (type(context.root) is not DevelopmentStudySpec
            or context.root != development_root(config, study_id=context.root.study_id)
            or context.node_id != CAPABILITY or context.stage is not ScientificStage.ACQUIRE
            or context.unit_ids != (UNIT,) or context.selected_unit_ids != (UNIT,) or not context.complete_unit_census
            or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or context.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY
            or len(context.config_inputs) != 1 or context.config_inputs[0].record is not config
            or context.config_inputs[0].node_id != CAPABILITY or context.requirements or context.connections
            or context.external_inputs != native_external_inputs(config) or context.links != native_input_links(config)):
        raise ValueError('gas parameter construction substitutes its complete original scientific scope')


def gas_parameter_draft(config, *, draft_id=None):
    exact(config, GasParameterConfig)
    draft_id = 'draft.gas-parameters.'+config.fingerprint() if draft_id is None else draft_id
    root = development_root(config, study_id='study.'+draft_id)
    policy = AuthorityPolicy('policy.'+draft_id, 'owner.local-researcher', 'operator.local-development', (root.study_id,),
        frozenset((root.world_kind,)), frozenset((AuthorityAction.REPOSITORY_IMPLEMENTATION, AuthorityAction.SIMULATION_EXECUTION)),
        frozenset((SourceAccessClass.NONE,)), ('gate.local-nonactuating-development',), frozenset(), BUDGET,
        OutcomeAccess.DEVELOPMENT_VISIBLE)
    node = CampaignNode('design.'+draft_id, CampaignNodeKind.EVIDENCE_SNAPSHOT, CampaignLane.EXPLORATORY,
        ObjectIdentity.from_record(root.study_id, root), (), LifecycleStatus.ACTIVE)
    campaign = CampaignSpec('campaign.'+draft_id, root.question, (root.system.object_id,), (root.world_id,),
        tuple(claim.claim_id for claim in root.claims), BUDGET, ObjectIdentity.from_record(policy.policy_id, policy),
        (DecisionRight('decision-right.'+draft_id, AuthorityAction.SIMULATION_EXECUTION, 'owner.local-researcher', policy.policy_id, False),),
        (node,), (node.node_id,), (node.node_id,), (), LifecycleStatus.ACTIVE)
    operation = RecursiveOperationSpec.from_config(node_id=CAPABILITY, selection=operation_declaration().registration().selection,
        config_id=config.config_id, config=config, obligation_ids=('obligation.gas-parameters.complete-host-and-two-gases',),
        resource_budget=BUDGET, resource_lock_ids=('gp-gas-parameter-native-worker',), maximum_attempts=1)
    return RecursiveStudyDraft(draft_id, root.question, campaign, (), (), (), (operation,), native_external_inputs(config),
        native_input_links(config), (CAPABILITY,), development_study=root)
