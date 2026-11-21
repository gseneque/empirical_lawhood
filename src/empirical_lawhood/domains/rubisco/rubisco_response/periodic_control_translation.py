# SPDX-License-Identifier: MPL-2.0
"""Complete prospective periodic controls through ordinary shared task nodes."""
from dataclasses import dataclass
from types import MappingProxyType

from empirical_lawhood.science.identity.authority import AuthorityAction, AuthorityPolicy, SourceAccessClass
from empirical_lawhood.science.evidence.evidence import ClaimSpec, EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import DevelopmentStudySpec
from empirical_lawhood.science.records.status import LifecycleStatus
from empirical_lawhood.science.models.worlds import WorldKind
from empirical_lawhood.design.campaigns import CampaignLane, CampaignNode, CampaignNodeKind, CampaignSpec, DecisionRight
from empirical_lawhood.design.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft
from empirical_lawhood.execution.plans import ScientificStage
from empirical_lawhood.execution.recursive_compiler import RecursiveScientificRootPreparationContext
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_control_operation import UNIT, capability_for, node_id, operands, operation_declaration, selected_request, resource_budget


def validate_configs(configs):
    if type(configs) is not tuple or not configs:
        raise ValueError('periodic controls require their complete original configuration tuple')
    for config in configs:
        capability_for(config)
    base = configs[0]
    if (tuple(c.point.ordinal for c in configs) != tuple(range(base.protocol.point_count))
            or any(c.original != base.original or c.protocol != base.protocol for c in configs)):
        raise ValueError('periodic controls omit or substitute a complete original prospective point')
    return base


def development_root(configs, *, study_id):
    base = validate_configs(configs)
    views = tuple(sorted('view.'+c.point.point_id for c in configs))
    claim = ClaimSpec('claim.periodic-controls.original-numerics', 'world.periodic-gp-numerical-controls',
        'population.one-source-assembly-prospective-numerical-views',
        'Do the complete selected periodic forces agree with independent energy differences, and how do declared refinements change the return?',
        'One complete original assembly; all numerical points are nested views, with zero independent biological replicates.',
        UNIT, None, EvidenceCeiling.NON_PROMOTABLE, OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY,
        'Selected numerical controls do not establish untested derivative components, chemical accuracy, ensemble convergence, rates or mutation response.',
        ('assumption.selected-periodic-qmmm-reference-potential',), numerical_view_ids=views)
    if base.FORCE_ACTIONS:
        claim = ClaimSpec('claim.periodic-force-actions.local-response', 'world.periodic-gp-force-actions',
            'population.one-source-assembly-prospective-numerical-views',
            'How do complete Cartesian force-difference actions and their receiver projections change across the selected displacement sizes?',
            'One complete original assembly; all displacement points are nested views, with zero independent biological replicates.',
            UNIT, None, EvidenceCeiling.NON_PROMOTABLE, OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY,
            'Two-scale action comparisons supply no rigorous derivative bound, positive inverse, ensemble, rate or mutation-response admission.',
            ('assumption.selected-periodic-qmmm-reference-potential',), numerical_view_ids=views)
    sources = tuple(sorted({pin for config in configs for pin in operands(config)}, key=lambda r:r.object_id))
    return DevelopmentStudySpec(study_id, claim.proposition, base.protocol.identity, claim.world_id,
        WorldKind.NUMERICAL_SIMULATOR, (UNIT,), views, (claim,), sources)


def input_selections(config):
    original = config.original
    return (('native-arrays', original.selection.coordinates.identity, original.selection.coordinates.canonical_size_bytes()),
        ('native-model', original.selection.representation, original.representation_size_bytes),
        ('native-protocol', config.protocol.identity, config.protocol.canonical_size_bytes()),
        ('native-prototype', original.selection.identity, original.selection.canonical_size_bytes()),
        ('native-provenance', original.provenance.identity, original.provenance.canonical_size_bytes()),
        ('native-point', config.point.identity, config.point.canonical_size_bytes()),
        ('native-request', selected_request(config).identity, selected_request(config).canonical_size_bytes()),
        ('native-source', original.raw_sources, original.raw_source_size_bytes))


def external_id(config, name):
    suffix = '.'+f'{config.point.ordinal:08d}' if name in {'native-point', 'native-request'} else ''
    return 'external.periodic-controls.'+name+suffix


def native_external_inputs(configs):
    validate_configs(configs)
    rows = {}
    for config in configs:
        for name, pin, size in input_selections(config):
            key = external_id(config, name)
            row = RecursiveExternalInput(key, pin.object_id, pin.object_schema, 'application/json', size,
                OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY, pin.object_fingerprint, 'SOURCE')
            if key in rows and rows[key] != row:
                raise ValueError('periodic controls substitute a shared complete input')
            rows[key] = row
    return tuple(rows[key] for key in sorted(rows))


def native_input_links(configs):
    return tuple(sorted((RecursiveInputLink('edge.'+node_id(config)+'.'+name, node_id(config), name,
        external_input_id=external_id(config, name), scientific_role='SOURCE')
        for config in configs for name, _, _ in input_selections(config)), key=lambda r:r.edge_id))


@dataclass(frozen=True, slots=True, eq=False)
class ControlPreparation:
    batch: RecursiveScientificRootPreparationContext
    configs: object


def prepare_root(batch):
    if type(batch) is not RecursiveScientificRootPreparationContext or type(batch.root) is not DevelopmentStudySpec:
        raise ValueError('periodic controls require their original development root')
    configs = tuple(row.record for row in batch.config_inputs)
    validate_configs(configs)
    if (tuple(row.node_id for row in batch.config_inputs) != tuple(node_id(c) for c in configs)
            or batch.root != development_root(configs, study_id=batch.root.study_id)
            or batch.external_inputs != native_external_inputs(configs) or batch.links != native_input_links(configs)
            or batch.requirements or batch.connections
            or any(units != (UNIT,) for units in batch.selected_unit_ids_by_selection.values())):
        raise ValueError('periodic controls change their complete original graph or scientific census')
    return ControlPreparation(batch, MappingProxyType({node_id(c):c for c in configs}))


def validate_root(config, context):
    selected = context.scientific_preparation
    if type(selected) is not ControlPreparation:
        raise ValueError('periodic controls require the complete prepared graph')
    if (selected.configs.get(context.node_id) is not config or context.root is not selected.batch.root
            or context.config_inputs is not selected.batch.config_inputs or context.links is not selected.batch.links
            or context.external_inputs is not selected.batch.external_inputs
            or context.requirements is not selected.batch.requirements or context.connections is not selected.batch.connections
            or context.node_id != node_id(config) or context.stage is not ScientificStage.ACQUIRE
            or context.unit_ids != (UNIT,) or context.selected_unit_ids != (UNIT,) or not context.complete_unit_census
            or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or context.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
        raise ValueError('periodic numerical point changes its prepared original task scope')


def periodic_controls_draft(configs, *, draft_id=None):
    base = validate_configs(configs)
    draft_id = 'draft.periodic-controls.'+base.protocol.fingerprint() if draft_id is None else draft_id
    root = development_root(configs, study_id='study.'+draft_id)
    budget = resource_budget(base)
    policy = AuthorityPolicy('policy.'+draft_id, 'owner.local-researcher', 'operator.local-development', (root.study_id,),
        frozenset((root.world_kind,)), frozenset((AuthorityAction.REPOSITORY_IMPLEMENTATION, AuthorityAction.SIMULATION_EXECUTION)),
        frozenset((SourceAccessClass.NONE,)), ('gate.local-nonactuating-development',), frozenset(), budget, OutcomeAccess.DEVELOPMENT_VISIBLE)
    node = CampaignNode('design.'+draft_id, CampaignNodeKind.EVIDENCE_SNAPSHOT, CampaignLane.EXPLORATORY,
        ObjectIdentity.from_record(root.study_id, root), (), LifecycleStatus.ACTIVE)
    campaign = CampaignSpec('campaign.'+draft_id, root.question, (root.system.object_id,), (root.world_id,),
        tuple(c.claim_id for c in root.claims), budget, ObjectIdentity.from_record(policy.policy_id, policy),
        (DecisionRight('decision-right.'+draft_id, AuthorityAction.SIMULATION_EXECUTION, 'owner.local-researcher', policy.policy_id, False),),
        (node,), (node.node_id,), (node.node_id,), (), LifecycleStatus.ACTIVE)
    operation_selection = operation_declaration(accelerated=base.ACCELERATED, force_actions=base.FORCE_ACTIONS).registration().selection
    operations = tuple(RecursiveOperationSpec.from_config(node_id=node_id(c), selection=operation_selection,
        config_id=c.config_id, config=c, obligation_ids=('obligation.'+node_id(c)+'.complete-original-point',),
        resource_budget=resource_budget(c), resource_lock_ids=('gp-periodic-force-native-worker',), maximum_attempts=1) for c in configs)
    return RecursiveStudyDraft(draft_id, root.question, campaign, (), (), (), operations,
        native_external_inputs(configs), native_input_links(configs), tuple(node_id(c) for c in configs), development_study=root)
