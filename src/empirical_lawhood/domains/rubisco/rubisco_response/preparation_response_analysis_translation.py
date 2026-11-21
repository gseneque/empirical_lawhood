# SPDX-License-Identifier: MPL-2.0
"""Code-derived non-native assessment draft and exact inherited input origins."""

from empirical_lawhood.science.identity.authority import AuthorityAction, AuthorityPolicy, SourceAccessClass
from empirical_lawhood.science.evidence.evidence import ClaimSpec, EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import DevelopmentStudySpec
from empirical_lawhood.science.records.status import LifecycleStatus
from empirical_lawhood.science.models.worlds import WorldKind
from empirical_lawhood.design.campaigns import CampaignLane, CampaignNode, CampaignNodeKind, CampaignSpec, DecisionRight
from empirical_lawhood.design.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft
from empirical_lawhood.execution.plans import ScientificStage
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_analysis_operation import BUDGET, MAX_CONFIG, UNIT, capability_for, config_types, external_id, input_selections, operation_declaration
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_design import response_scope


def graph_inputs(config):
    rows, links = [], []
    for name, pin, media, size, artifact, record in input_selections(config):
        key = external_id(config, name)
        role = 'SOURCE' if record is None else 'HISTORY'
        rows.append(RecursiveExternalInput(key, artifact, pin.object_schema, media, size,
            OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY, pin.object_fingerprint, role))
        links.append(RecursiveInputLink('edge.' + name, capability_for(config), name, external_input_id=key, scientific_role=role))
    return tuple(rows), tuple(links)


def development_root(config, *, study_id):
    scope = response_scope(config.analysis.design)
    views = tuple(sorted('view.response-assessment.' + model + '.' + position
        for model in ('m1-i95m', 'm1-wt') for position in ('initial', 'later')))
    claim = ClaimSpec('claim.preparation-response.six-questions', scope.world_id, scope.population_id,
        'Does the allowed preparation improve the same signed formation response, and which limitation remains consequential?',
        'One matched construction; four nested positions and zero independent biological replicates. '
        'The original four-material, 32-site, 384-start denominator remains unresolved.', UNIT, None,
        EvidenceCeiling.NON_PROMOTABLE, OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY,
        'Empirical numerical consistency and local response do not establish a rigorous force bound, equilibrium mean or kinetic contrast.',
        ('assumption.selected-periodic-qmmm-reference-potential',), numerical_view_ids=views)
    operands = tuple(sorted({config.analysis.identity, *(r[1] for r in input_selections(config))}, key=lambda p: p.object_id))
    return DevelopmentStudySpec(study_id, claim.proposition, config.analysis.design.identity, scope.world_id,
        WorldKind.ANALYTIC_REFERENCE, (UNIT,), views, (claim,), operands)


def validate_root(config, context):
    external, links = graph_inputs(config)
    if (type(config) not in config_types() or type(context.root) is not DevelopmentStudySpec
            or context.root != development_root(config, study_id=context.root.study_id)
            or context.node_id != capability_for(config) or context.stage is not ScientificStage.FALSIFY
            or len(context.config_inputs) != 1 or context.config_inputs[0].record != config
            or context.unit_ids != (UNIT,) or context.selected_unit_ids != (UNIT,) or context.complete_unit_census
            or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or context.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY
            or context.external_inputs != external or context.links != links or context.requirements or context.connections):
        raise ValueError('response assessment changes its exact original scientific graph')


def response_analysis_draft(config, *, draft_id=None):
    draft_id = 'draft.response-assessment.' + config.analysis.fingerprint() if draft_id is None else draft_id
    root = development_root(config, study_id='study.' + draft_id)
    policy = AuthorityPolicy('policy.' + draft_id, 'owner.local-researcher', 'operator.local-development', (root.study_id,),
        frozenset((root.world_kind,)), frozenset((AuthorityAction.REPOSITORY_IMPLEMENTATION, AuthorityAction.SIMULATION_EXECUTION)),
        frozenset((SourceAccessClass.NONE,)), ('gate.local-nonactuating-development',), frozenset(), BUDGET, OutcomeAccess.DEVELOPMENT_VISIBLE)
    node = CampaignNode('design.' + draft_id, CampaignNodeKind.EVIDENCE_SNAPSHOT, CampaignLane.EXPLORATORY,
        ObjectIdentity.from_record(root.study_id, root), (), LifecycleStatus.ACTIVE)
    campaign = CampaignSpec('campaign.' + draft_id, root.question, (root.system.object_id,), (root.world_id,),
        tuple(c.claim_id for c in root.claims), BUDGET, ObjectIdentity.from_record(policy.policy_id, policy),
        (DecisionRight('decision-right.' + draft_id, AuthorityAction.SIMULATION_EXECUTION, 'owner.local-researcher', policy.policy_id, False),),
        (node,), (node.node_id,), (node.node_id,), (), LifecycleStatus.ACTIVE)
    selection = operation_declaration(environmental=config.ENVIRONMENTAL).registration().selection
    operation = RecursiveOperationSpec.from_config(node_id=capability_for(config), selection=selection, config_id=config.config_id,
        config=config, obligation_ids=('obligation.original-six-question-assessment',), resource_budget=BUDGET, maximum_attempts=1)
    external, links = graph_inputs(config)
    return RecursiveStudyDraft(draft_id, root.question, campaign, (), (), (), (operation,), external, links,
        (capability_for(config),), development_study=root, contribution_parents=config.analysis.parents)


def _selection_preparation():
    from empirical_lawhood.execution.recursive_inquiry_selection import InquirySelectionPreparation
    return InquirySelectionPreparation(_decode_selected_configs, config_types(),
        (response_analysis_draft,))


def selection_scope(draft):
    return _selection_preparation().scope(draft)


def _decode_selected_configs(draft):
    from empirical_lawhood.science.records.decoded_record_store import decode_scoped_canonical_bytes
    if len(draft.operations) != 1 or draft.selected_operation_ids != (draft.operations[0].node_id,):
        raise ValueError('response assessment changes its one original non-native operation')
    operation, = draft.operations
    kind = next((kind for kind in config_types() if kind.SCHEMA == operation.config_identity.object_schema), None)
    if kind is None:
        raise ValueError('response assessment changes its selected configuration revision')
    config = decode_scoped_canonical_bytes(operation.config_payload.encode(), kind, maximum_bytes=MAX_CONFIG)
    if operation.node_id != capability_for(config) or draft != response_analysis_draft(config, draft_id=draft.draft_id):
        raise ValueError('response assessment changes its complete code-derived draft')
    return (config,)


def selected_config(draft):
    config, = selected_configs(draft)
    return config


def selected_configs(draft):
    return _selection_preparation().read(draft)


def analysis_input_origins(draft):
    from empirical_lawhood.design.recursive_input_origins import RecursiveInputOrigin, RecursiveInputOriginKind, RecursiveInputOrigins
    config = selected_config(draft)
    rows = []
    for name, pin, _, _, _, record in input_selections(config):
        key = external_id(config, name)
        if record is None:
            rows.append(RecursiveInputOrigin(key, RecursiveInputOriginKind.SOURCE, pin.object_fingerprint, 'SOURCE'))
        else:
            parent, product = config.analysis.product(record)
            rows.append(RecursiveInputOrigin(key, RecursiveInputOriginKind.CONTRIBUTION, pin.object_fingerprint, product.role.value,
                ObjectIdentity.from_record(parent.contribution_id, parent), product.product_id, product.producing_receipt))
    origins = RecursiveInputOrigins(tuple(rows))
    origins.validate_draft(draft)
    return origins
