# SPDX-License-Identifier: MPL-2.0
"""Code-owned contribution edges for the local preparation/response consumer."""

from empirical_lawhood.science.identity.authority import AuthorityAction, AuthorityPolicy, SourceAccessClass
from empirical_lawhood.science.evidence.evidence import ClaimSpec, EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import DevelopmentStudySpec
from empirical_lawhood.science.records.status import LifecycleStatus
from empirical_lawhood.science.models.worlds import WorldKind
from empirical_lawhood.design.campaigns import CampaignLane, CampaignNode, CampaignNodeKind, CampaignSpec, DecisionRight
from empirical_lawhood.design.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft
from empirical_lawhood.execution.plans import ScientificStage
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_supply import CAPABILITY, CLAIM, UNIT, external_id, source_name, supply_graph
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_supply_operation import BUDGET, MAX_INPUT, PreparationSupplyConfig, operation_declaration


def graph_contracts(config):
    requirements, connections = supply_graph(config.selection)
    sources, links = [], []
    for record in config.selection.records:
        _, product = config.selection.product(record)
        name = source_name(record)
        connection, = (r for r in connections if r.consumer_input_id == name)
        sources.append(RecursiveExternalInput(external_id(record), product.artifact.artifact_id, record.SCHEMA,
            'application/json', record.canonical_size_bytes(), product.outcome_access, product.visibility_ceiling,
            record.fingerprint(), 'HISTORY'))
        links.append(RecursiveInputLink('edge.preparation-supply.' + name, CAPABILITY, name,
            external_input_id=external_id(record), scientific_role='HISTORY',
            requirement_id=connection.requirement_id, connection_id=connection.connection_id))
    return requirements, connections, tuple(sources), tuple(links)


def development_root(config, *, study_id):
    scope = config.selection.scope
    views = tuple(sorted('view.preparation-supply.' + model + '.' + position
        for model in ('m1-i95m', 'm1-wt') for position in ('initial', 'later')))
    claim = ClaimSpec(CLAIM, scope.world_id, scope.population_id,
        'Which original local preparation and response operands supply this exact finite investigation?',
        'Four nested positions in one matched construction; zero biological replicates. Original 4/32/384 denominator retained.',
        UNIT, None, EvidenceCeiling.NON_PROMOTABLE, OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY,
        'Adverse local findings can answer the question. Local supply admits no canonical population, rate or mutation forecast.',
        ('assumption.selected-periodic-qmmm-reference-potential',), numerical_view_ids=views)
    operands = tuple(sorted((config.selection.design.identity, *(r.identity for r in config.selection.records)), key=lambda p: p.object_id))
    return DevelopmentStudySpec(study_id, claim.proposition, config.selection.design.prefix.plan, scope.world_id,
        WorldKind.ANALYTIC_REFERENCE, (UNIT,), views, (claim,), operands)


def validate_root(config, context):
    requirements, connections, sources, links = graph_contracts(config)
    if (type(config) is not PreparationSupplyConfig or type(context.root) is not DevelopmentStudySpec
            or context.root != development_root(config, study_id=context.root.study_id)
            or context.node_id != CAPABILITY or context.stage is not ScientificStage.FALSIFY
            or len(context.config_inputs) != 1 or context.config_inputs[0].record != config
            or context.unit_ids != (UNIT,) or context.selected_unit_ids != (UNIT,) or context.complete_unit_census
            or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or context.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY
            or context.requirements != requirements or context.connections != connections
            or context.external_inputs != sources or context.links != links):
        raise ValueError('local supply changes its exact original scientific consumer graph')


def supply_draft(config, *, draft_id=None):
    draft_id = 'draft.preparation-supply.' + config.selection.fingerprint() if draft_id is None else draft_id
    root = development_root(config, study_id='study.' + draft_id)
    policy = AuthorityPolicy('policy.' + draft_id, 'owner.local-researcher', 'operator.local-development', (root.study_id,),
        frozenset((root.world_kind,)), frozenset((AuthorityAction.REPOSITORY_IMPLEMENTATION, AuthorityAction.SIMULATION_EXECUTION)),
        frozenset((SourceAccessClass.NONE,)), ('gate.local-nonactuating-development',), frozenset(), BUDGET, OutcomeAccess.DEVELOPMENT_VISIBLE)
    node = CampaignNode('design.' + draft_id, CampaignNodeKind.EVIDENCE_SNAPSHOT, CampaignLane.EXPLORATORY,
        ObjectIdentity.from_record(root.study_id, root), (), LifecycleStatus.ACTIVE)
    campaign = CampaignSpec('campaign.' + draft_id, root.question, (root.system.object_id,), (root.world_id,),
        (CLAIM,), BUDGET, ObjectIdentity.from_record(policy.policy_id, policy),
        (DecisionRight('decision-right.' + draft_id, AuthorityAction.SIMULATION_EXECUTION, 'owner.local-researcher', policy.policy_id, False),),
        (node,), (node.node_id,), (node.node_id,), (), LifecycleStatus.ACTIVE)
    operation = RecursiveOperationSpec.from_config(node_id=CAPABILITY, selection=operation_declaration().registration().selection,
        config_id=config.config_id, config=config, obligation_ids=('obligation.original-local-destination-supply',),
        resource_budget=BUDGET, maximum_attempts=1)
    requirements, connections, sources, links = graph_contracts(config)
    return RecursiveStudyDraft(draft_id, root.question, campaign, requirements, connections, (), (operation,), sources, links,
        (CAPABILITY,), development_study=root, contribution_parents=config.selection.parents)


def _selection_preparation():
    from empirical_lawhood.execution.recursive_inquiry_selection import InquirySelectionPreparation
    return InquirySelectionPreparation(_decode_selected_configs, (PreparationSupplyConfig,), (supply_draft,))


def selection_scope(draft):
    return _selection_preparation().scope(draft)


def selected_configs(draft):
    return _selection_preparation().read(draft)


def _decode_selected_configs(draft):
    from empirical_lawhood.science.records.decoded_record_store import decode_scoped_canonical_bytes
    if len(draft.operations) != 1 or draft.selected_operation_ids != (CAPABILITY,):
        raise ValueError('local supply changes its one selected original consumer')
    operation, = draft.operations
    if operation.config_identity.object_schema != PreparationSupplyConfig.SCHEMA:
        raise ValueError('local supply changes its registered configuration revision')
    config = decode_scoped_canonical_bytes(operation.config_payload.encode(), PreparationSupplyConfig, maximum_bytes=MAX_INPUT)
    if draft != supply_draft(config, draft_id=draft.draft_id):
        raise ValueError('local supply changes its code-derived original graph')
    return (config,)


def supply_input_origins(draft):
    from empirical_lawhood.design.recursive_input_origins import RecursiveInputOrigin, RecursiveInputOriginKind, RecursiveInputOrigins
    config, = selected_configs(draft)
    origins = []
    for record in config.selection.records:
        parent, product = config.selection.product(record)
        origins.append(RecursiveInputOrigin(external_id(record), RecursiveInputOriginKind.CONTRIBUTION,
            record.fingerprint(), product.role.value, ObjectIdentity.from_record(parent.contribution_id, parent),
            product.product_id, product.producing_receipt))
    result = RecursiveInputOrigins(tuple(origins))
    result.validate_draft(draft)
    return result
