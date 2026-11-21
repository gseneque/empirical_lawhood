# SPDX-License-Identifier: MPL-2.0
"""Code-owned root graphs on the unchanged recursive compiler and authoring path."""

from empirical_lawhood.methods.compact_inquiry_policy import compact_scientific_work
from empirical_lawhood.science.identity.authority import AuthorityAction, AuthorityPolicy, SourceAccessClass
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import ContributionRole
from empirical_lawhood.science.records.status import LifecycleStatus
from empirical_lawhood.design.campaigns import CampaignLane, CampaignNode, CampaignNodeKind, CampaignSpec, DecisionRight
from empirical_lawhood.design.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft
from empirical_lawhood.design.recursive_input_origins import RecursiveInputOrigin, RecursiveInputOriginKind, RecursiveInputOrigins, contribution_graph_role
from empirical_lawhood.domains.rubisco.rubisco_response.initial_root_records import InitialRootAnalysisInputs, InitialRootScopedAssessment, InitialRootScopedResult
from empirical_lawhood.domains.rubisco.rubisco_response.initial_root_requirements import ASSESS, CALCULATE, USE, initial_root_requirement_graph, initial_root_scope
from empirical_lawhood.domains.rubisco.rubisco_response.initial_root_operation import BUDGET, MAX_INPUT_BYTES, MEDIA, PHASES, InitialRootOperationConfig, development_root, operation_declarations
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact

ANALYSIS_INPUT = 'external.rubisco-response.initial-root-analysis'


def graph_contracts(config):
    graph = initial_root_requirement_graph(config.analysis, parent=config.parent)
    external = [RecursiveExternalInput(ANALYSIS_INPUT, config.analysis.identity.object_id,
        config.analysis.SCHEMA, MEDIA, MAX_INPUT_BYTES, OutcomeAccess.DEVELOPMENT_VISIBLE,
        VisibilityCeiling.DEVELOPMENT_ONLY, config.analysis.fingerprint(), 'SOURCE')]
    phases = (USE,) if config.parent is not None else (CALCULATE, ASSESS)
    links = [RecursiveInputLink('edge.' + phase + '.analysis', phase, 'analysis', external_input_id=ANALYSIS_INPUT,
        scientific_role='SOURCE') for phase in phases]
    connection, = graph.connections
    if config.parent is None:
        links.append(RecursiveInputLink('edge.' + ASSESS + '.result', ASSESS, 'result', CALCULATE, 'product',
            scientific_role='HISTORY', requirement_id=graph.numerical_requirement_id, connection_id=connection.connection_id))
    else:
        for name, kind in (('original-assessment', InitialRootScopedAssessment), ('result', InitialRootScopedResult)):
            product, = tuple(row for row in config.parent.products if row.record.object_schema == kind.SCHEMA)
            key = 'external.' + USE + '.' + name
            role = contribution_graph_role(product.role)
            external.append(RecursiveExternalInput(key, product.artifact.artifact_id, kind.SCHEMA, MEDIA,
                product.artifact.size_bytes, product.outcome_access, product.visibility_ceiling, product.record.object_fingerprint, role))
            links.append(RecursiveInputLink('edge.' + USE + '.' + name, USE, name, external_input_id=key,
                scientific_role=role, requirement_id=graph.numerical_requirement_id if name == 'result' else None,
                connection_id=connection.connection_id if name == 'result' else None))
    return graph.requirements, graph.connections, tuple(sorted(external, key=lambda row: row.input_id)), tuple(sorted(links, key=lambda row: row.edge_id))


def initial_root_draft(analysis, *, parent=None, draft_id=None):
    exact(analysis, InitialRootAnalysisInputs)
    phases = ('use',) if parent is not None else ('calculate', 'assess')
    draft_id = draft_id or 'draft.rubisco-initial-root.' + analysis.fingerprint() + ('.reuse' if parent is not None else '')
    base = InitialRootOperationConfig('config.rubisco-response.initial-root-' + phases[0], phases[0], analysis, parent)
    root = development_root(base, study_id='study.' + draft_id)
    policy = AuthorityPolicy('policy.' + draft_id, 'owner.local-researcher', 'operator.local-development',
        (root.study_id,), frozenset((root.world_kind,)),
        frozenset((AuthorityAction.REPOSITORY_IMPLEMENTATION, AuthorityAction.SIMULATION_EXECUTION)),
        frozenset((SourceAccessClass.NONE,)), ('gate.local-nonactuating-development',), frozenset(), BUDGET,
        OutcomeAccess.DEVELOPMENT_VISIBLE)
    node_id = 'design.' + draft_id
    node = CampaignNode(node_id, CampaignNodeKind.EVIDENCE_SNAPSHOT, CampaignLane.EXPLORATORY,
        ObjectIdentity.from_record(root.study_id, root), (), LifecycleStatus.ACTIVE)
    campaign = CampaignSpec('campaign.' + draft_id, root.question, (root.system.object_id,), (root.world_id,),
        tuple(row.claim_id for row in root.claims), BUDGET, ObjectIdentity.from_record(policy.policy_id, policy),
        (DecisionRight('decision-right.' + draft_id, AuthorityAction.SIMULATION_EXECUTION,
            'owner.local-researcher', policy.policy_id, False),), (node,), (node_id,), (node_id,), (), LifecycleStatus.ACTIVE)
    registrations = {row.capability_key: row.registration() for row in operation_declarations()}
    operations = []
    for phase in phases:
        key = next(row[1] for row in PHASES if row[0] == phase)
        config = InitialRootOperationConfig('config.' + key, phase, analysis, parent)
        operations.append(RecursiveOperationSpec.from_config(node_id=key, selection=registrations[key].selection,
            config_id=config.config_id, config=config, obligation_ids=('obligation.' + key + '.complete-scientific-scope',),
            resource_budget=BUDGET))
    requirements, connections, external, links = graph_contracts(base)
    graph = initial_root_requirement_graph(analysis, parent=parent)
    operations = tuple(sorted(operations, key=lambda row: row.node_id))
    return RecursiveStudyDraft(draft_id, root.question, campaign, requirements, connections, graph.suppliers,
        operations, external, links, tuple(row.node_id for row in operations), development_study=root,
        contribution_parents=() if parent is None else (parent,))


def selected_configs(draft):
    selected = tuple(row for row in draft.operations if row.node_id in draft.selected_operation_ids)
    if not selected:
        raise ValueError('initial root needs its selected calculation/assessment or retained-use operation')
    configs = {}
    registrations = {row.capability_key: row.registration() for row in operation_declarations()}
    for operation in selected:
        config = decode_canonical_bytes(operation.config_payload.encode(), InitialRootOperationConfig, maximum_bytes=MAX_INPUT_BYTES)
        if (operation.node_id not in registrations or operation.selection != registrations[operation.node_id].selection
                or operation.config_identity != ObjectIdentity.from_record(config.config_id, config)
                or operation.node_id != 'rubisco-response.initial-root-' + config.operation or operation.resource_budget != BUDGET):
            raise ValueError('initial root changes its selected code, source configuration, phase or resources')
        configs[config.operation] = config
    first = next(iter(configs.values()))
    if (any(row.analysis != first.analysis or row.parent != first.parent for row in configs.values())
            or draft != initial_root_draft(first.analysis, parent=first.parent, draft_id=draft.draft_id)):
        raise ValueError('initial root changes its full source/consumer selection, requirements or original contribution')
    return configs


def initial_root_origins(draft):
    config = next(iter(selected_configs(draft).values()))
    rows = []
    for external in draft.external_inputs:
        if external.input_id == ANALYSIS_INPUT:
            rows.append(RecursiveInputOrigin(external.input_id, RecursiveInputOriginKind.SOURCE,
                external.expected_content_sha256, external.scientific_role))
        else:
            products = tuple(row for row in config.parent.products if row.artifact.artifact_id == external.logical_artifact_id)
            if len(products) != 1 or products[0].role is not ContributionRole.RETAINED_ANALYSIS_INPUT:
                raise ValueError('initial root reuse changes original product role or ownership')
            product, = products
            rows.append(RecursiveInputOrigin(external.input_id, RecursiveInputOriginKind.CONTRIBUTION,
                product.record.object_fingerprint, product.role.value,
                ObjectIdentity.from_record(config.parent.contribution_id, config.parent), product.product_id, product.producing_receipt))
    origins = RecursiveInputOrigins(tuple(sorted(rows, key=lambda row: row.input_id)))
    origins.validate_draft(draft)
    return origins


def scientific_work(draft, operation_id):
    configs = selected_configs(draft)
    operation = next((row for row in draft.operations if row.node_id == operation_id), None)
    if operation is None:
        raise ValueError('initial root work changes its selected operation')
    config = configs[operation_id.removeprefix('rubisco-response.initial-root-')]
    # This config explicitly exposes the complete source and operand semantics
    # expected by the existing compact-work owner. Labels/paths grant no novelty.
    return compact_scientific_work(namespace='rubisco-initial-root', operation=operation, config=config,
        scope=initial_root_scope(config.analysis), output_type=InitialRootScopedResult if config.operation == 'calculate' else InitialRootScopedAssessment,
        scientific_design=config.analysis.request.identity)
