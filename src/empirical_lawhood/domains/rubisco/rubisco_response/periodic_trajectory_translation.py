# SPDX-License-Identifier: MPL-2.0
"""Pure shared authoring for one original diagnostic reference trajectory."""

from empirical_lawhood.science.identity.authority import AuthorityAction, AuthorityPolicy, SourceAccessClass
from empirical_lawhood.science.evidence.evidence import ClaimSpec, EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import DevelopmentStudySpec
from empirical_lawhood.science.records.status import LifecycleStatus
from empirical_lawhood.science.models.worlds import WorldKind
from empirical_lawhood.design.campaigns import CampaignLane, CampaignNode, CampaignNodeKind, CampaignSpec, DecisionRight
from empirical_lawhood.design.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft
from empirical_lawhood.execution.plans import ScientificStage
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_trajectory_operation import UNIT, capability_for, resource_budget, operands, operation_declaration


def development_root(config, *, study_id):
    capability_for(config)
    view = 'view.reference-trajectory.'+config.selection.fingerprint()
    claim = ClaimSpec('claim.reference-trajectory.original-trace', 'world.periodic-gp-reference-trajectory',
        'population.one-source-assembly-original-phase-space',
        'Does the original complete reference trajectory satisfy its selected trace criteria over the physical observation horizon?',
        'One complete assembly and supplied initial phase-space point; zero independent biological replicates.',
        UNIT, None, EvidenceCeiling.NON_PROMOTABLE, OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY,
        'Trace criteria do not establish force accuracy, integration-step convergence, a qualified starting ensemble, physical rates or mutation response.',
        ('assumption.selected-periodic-qmmm-reference-potential',), numerical_view_ids=(view,))
    return DevelopmentStudySpec(study_id, claim.proposition, config.selection.identity, claim.world_id,
        WorldKind.NUMERICAL_SIMULATOR, (UNIT,), (view,), (claim,), operands(config))


def input_selections(config):
    original = config.original
    return (('native-arrays', config.selection.arrays.identity, config.selection.arrays.canonical_size_bytes(), 'application/json'),
        ('native-model', original.selection.representation, original.representation_size_bytes, 'application/json'),
        ('native-phase', config.selection.phase_bytes, config.selection.arrays.size_bytes, 'application/octet-stream'),
        ('native-prototype', original.selection.identity, original.selection.canonical_size_bytes(), 'application/json'),
        ('native-provenance', original.provenance.identity, original.provenance.canonical_size_bytes(), 'application/json'),
        ('native-selection', config.selection.identity, config.selection.canonical_size_bytes(), 'application/json'),
        ('native-source', original.raw_sources, original.raw_source_size_bytes, 'application/json'))


def native_external_inputs(config):
    return tuple(RecursiveExternalInput('external.reference-trajectory.'+name, pin.object_id, pin.object_schema,
        media, size, OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY, pin.object_fingerprint, 'SOURCE')
        for name, pin, size, media in input_selections(config))


def native_input_links(config):
    return tuple(RecursiveInputLink('edge.reference-trajectory.'+name, capability_for(config), name,
        external_input_id='external.reference-trajectory.'+name, scientific_role='SOURCE')
        for name, _, _, _ in input_selections(config))


def validate_root(config, context):
    if (type(context.root) is not DevelopmentStudySpec
            or context.root != development_root(config, study_id=context.root.study_id)
            or context.node_id != capability_for(config) or context.stage is not ScientificStage.ACQUIRE
            or context.unit_ids != (UNIT,) or context.selected_unit_ids != (UNIT,) or not context.complete_unit_census
            or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or context.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY
            or len(context.config_inputs) != 1 or context.config_inputs[0].record is not config
            or context.config_inputs[0].node_id != capability_for(config) or context.requirements or context.connections
            or context.external_inputs != native_external_inputs(config) or context.links != native_input_links(config)):
        raise ValueError('reference trajectory graph substitutes its complete original scientific scope')


def reference_trajectory_draft(config, *, draft_id=None):
    capability_for(config)
    draft_id = 'draft.reference-trajectory.'+config.fingerprint() if draft_id is None else draft_id
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
    operation = RecursiveOperationSpec.from_config(node_id=capability_for(config), selection=operation_declaration(accelerated=config.ACCELERATED).registration().selection,
        config_id=config.config_id, config=config, obligation_ids=('obligation.reference-trajectory.complete-original-phase-space',),
        resource_budget=resource_budget(config), resource_lock_ids=('gp-periodic-force-native-worker',), maximum_attempts=1)
    return RecursiveStudyDraft(draft_id, root.question, campaign, (), (), (), (operation,),
        native_external_inputs(config), native_input_links(config), (capability_for(config),), development_study=root)
