# SPDX-License-Identifier: MPL-2.0
"""Singleton inquiry steps, exact portable products and distinct source-bound use."""
from hashlib import sha256

from empirical_lawhood.adapters.methods.rubisco_portfolio_inquiry import science as portfolio
from empirical_lawhood.kernel.authority import AuthorityAction, AuthorityPolicy, SourceAccessClass
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.recursive_requirements import (AssessmentDisposition, ConditionRole, ContributionRole,
    ScientificConditionScope, ScientificConnectionSpec, ScientificRequirementSpec)
from empirical_lawhood.kernel.scientific_contributions import ContributionManifest, ContributionProduct
from empirical_lawhood.kernel.status import LifecycleStatus, OperationalStatus
from empirical_lawhood.planning.campaigns import CampaignLane, CampaignNode, CampaignNodeKind, CampaignSpec, DecisionRight
from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft
from empirical_lawhood.runtime.recursive_inquiry import InquiryEvidenceBinding
from . import assessment
from .contracts import (NAMESPACE, QUESTION, CycleInstanceInput, CycleOperationConfig, CycleSupply,
                        CycleUseProduct, identity, design_from_source, scope)
from .operation_bindings import BUDGET, MAX_BYTES, MEDIA, PHASES, development_root, operation_registrations

CONDITION = 'Independently checked conditional gas-cycle procedure supplies an authentic macro-anchor query; actual enzyme microrates and target-assay admission remain unknown.'
FALSIFIER = 'Missing balance denominator, changed source/topology/assumptions, substituted macro anchors, omitted adverse scenarios, or unsupported biological admission.'


def instance_from_source(source, *, instance_id='instance.rubisco-cycle.finalists', candidate_ids=None, reference_ids=None):
    from .contracts import FINALIST_IDS, REFERENCE_IDS
    instance = CycleInstanceInput(instance_id, identity(source), FINALIST_IDS if candidate_ids is None else tuple(candidate_ids),
                                  REFERENCE_IDS if reference_ids is None else tuple(reference_ids))
    assessment.validate_instance(source, instance)
    return instance


def _operand(record):
    return record if isinstance(record, ObjectIdentity) else identity(record)


def _requirement_pair(node, parent, parent_product, design):
    requirement = ScientificRequirementSpec(f'requirement.{node}.conditional-model', node, ConditionRole.EVIDENTIAL,
        QUESTION, CONDITION, scope(design), node, FALSIFIER, (parent_product.role,))
    connection = ScientificConnectionSpec(f'connection.{node}.conditional-model', requirement.requirement_id, None, None,
        'supplier', node, f'claim.{node}', parent_product.role, FALSIFIER,
        ObjectIdentity.from_record(parent.contribution_id, parent), parent_product.product_id, f'external.{node}.supplier')
    return requirement, connection


def _draft(role, inputs, design, *, parent=None, successor=None, reuse_successor=None, draft_id):
    operands = tuple(sorted((_operand(record) for _, record in inputs), key=lambda row: row.object_id))
    config = CycleOperationConfig(f'config.{NAMESPACE}.{role}', role, design, operands, successor, reuse_successor)
    root = development_root(config, study_id=f'study.{draft_id}')
    policy = AuthorityPolicy(f'policy.{draft_id}', 'owner.local-researcher', 'operator.local-development',
        (root.study_id,), frozenset((root.world_kind,)),
        frozenset((AuthorityAction.REPOSITORY_IMPLEMENTATION, AuthorityAction.SIMULATION_EXECUTION)),
        frozenset((SourceAccessClass.NONE,)), ('gate.local-nonactuating-development',), frozenset(), BUDGET,
        OutcomeAccess.DEVELOPMENT_VISIBLE)
    root_id = f'design.{draft_id}'
    campaign = CampaignSpec(f'campaign.{draft_id}', QUESTION, (root.system.object_id,), (root.world_id,),
        tuple(row.claim_id for row in root.claims), BUDGET, ObjectIdentity.from_record(policy.policy_id, policy),
        (DecisionRight(f'decision-right.{draft_id}', AuthorityAction.SIMULATION_EXECUTION, 'owner.local-researcher', policy.policy_id, False),),
        (CampaignNode(root_id, CampaignNodeKind.EVIDENCE_SNAPSHOT, CampaignLane.EXPLORATORY,
                      ObjectIdentity.from_record(root.study_id, root), (), LifecycleStatus.ACTIVE),),
        (root_id,), (root_id,), (), LifecycleStatus.ACTIVE)
    registration = next(row for row in operation_registrations() if row.selection.capability_key == f'{NAMESPACE}.{role}')
    node = f'{NAMESPACE}.{role}'
    operation = RecursiveOperationSpec.from_config(node_id=node, selection=registration.selection, config_id=config.config_id,
        config=config, obligation_ids=(f'obligation.{node}.exact-conditional-scope',), resource_budget=BUDGET)
    external, links, requirements, connections = [], [], [], []
    for port, record in inputs:
        value = _operand(record)
        logical_id = value.object_id
        graph_role = ('OUTCOME' if role == 'reuse' else 'MODEL') if port == 'supplier' else 'SOURCE'
        pair = None
        if port == 'supplier' and parent is not None:
            wanted_role = ContributionRole.INSTANCE_PRODUCT if role == 'reuse' else ContributionRole.DESIGN_OPERAND
            products = tuple(row for row in parent.products if row.record == value and row.role is wanted_role)
            if len(products) != 1 or parent.scope != scope(design):
                raise ValueError('cycle later use changes exact parent product, original scope or role')
            logical_id = products[0].artifact.artifact_id
            pair = _requirement_pair(node, parent, products[0], design)
            requirements.append(pair[0]); connections.append(pair[1])
        input_id = f'external.{node}.{port}'
        external.append(RecursiveExternalInput(input_id, logical_id, value.object_schema, MEDIA, MAX_BYTES,
            OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY, value.object_fingerprint, graph_role))
        links.append(RecursiveInputLink(f'edge.{node}.{port}', node, port, external_input_id=input_id,
            scientific_role=graph_role, requirement_id=None if pair is None else pair[0].requirement_id,
            connection_id=None if pair is None else pair[1].connection_id))
    return RecursiveStudyDraft(draft_id, QUESTION, campaign, tuple(requirements), tuple(connections), (), (operation,),
        tuple(sorted(external, key=lambda row: row.input_id)), tuple(sorted(links, key=lambda row: row.edge_id)), (node,),
        development_study=root, contribution_parents=() if parent is None else (parent,))


def supply_draft(source, *, successor=None, reuse_successor=None, draft_id='draft.rubisco-cycle.supply'):
    return _draft('supply', (('source', source),), design_from_source(source), successor=successor,
                  reuse_successor=reuse_successor, draft_id=draft_id)


def use_draft(supplier, instance, *, macro_source=None, parent=None, successor=None, draft_id='draft.rubisco-cycle.use'):
    if type(supplier) is not CycleSupply:
        raise ValueError('cycle use requires an actual typed assessed model product')
    assessment.validate_supplier(supplier)
    if macro_source is not None:
        assessment.validate_instance(macro_source, instance)
    return _draft('use', (('supplier', supplier), ('macro-source', instance.macro_source), ('instance', instance)),
                  supplier.design, parent=parent, successor=successor, draft_id=draft_id)


def reuse_draft(previous, instance, *, macro_source=None, parent=None, successor=None, draft_id='draft.rubisco-cycle.reuse'):
    if type(previous) is not CycleUseProduct:
        raise ValueError('cycle reuse requires the actual previous instance assessment')
    assessment.validate_supplier(previous.model)
    previous.__post_init__()
    if instance.instance_id == previous.instance.instance_id or identity(instance) == identity(previous.instance):
        raise ValueError('cycle subsequent use requires a distinct declared instance query')
    if macro_source is not None:
        assessment.validate_instance(macro_source, instance)
    return _draft('reuse', (('supplier', previous), ('macro-source', instance.macro_source), ('instance', instance)),
                  previous.model.design, parent=parent, successor=successor, draft_id=draft_id)


def _config(draft):
    selected = tuple(row for row in draft.operations if row.node_id in draft.selected_operation_ids)
    if len(selected) != 1:
        raise ValueError('cycle inquiry requires its exact singleton selected operation')
    operation = selected[0]
    config = decode_canonical_bytes(operation.config_payload.encode(), CycleOperationConfig, maximum_bytes=None)
    registered = next(row for row in operation_registrations() if row.selection.capability_key == f'{NAMESPACE}.{config.operation}')
    if (operation.selection != registered.selection or operation.node_id != f'{NAMESPACE}.{config.operation}'
            or operation.config_id != config.config_id or draft.development_study != development_root(config, study_id=draft.development_study.study_id)):
        raise ValueError('cycle changes exact registration/config/root identity')
    return operation, config


def validate_requirement(record, requirement, connection):
    if type(record) is not CycleUseProduct:
        raise ValueError('cycle assessment projection needs the actual typed instance product')
    record.__post_init__()
    role = ContributionRole.DESIGN_OPERAND if record.supplier.object_schema == CycleSupply.SCHEMA else ContributionRole.INSTANCE_PRODUCT
    node = f'{NAMESPACE}.use' if role is ContributionRole.DESIGN_OPERAND else f'{NAMESPACE}.reuse'
    if (requirement.requirement_id != f'requirement.{node}.conditional-model' or requirement.consumer_operation_id != node
            or requirement.condition_role is not ConditionRole.EVIDENTIAL or requirement.purpose != QUESTION
            or requirement.condition != CONDITION or requirement.scope != record.scope or requirement.assessment_operation_id != node
            or requirement.falsifier != FALSIFIER or requirement.permitted_roles != (role,)
            or requirement.further_requirement_ids or requirement.background_assumption_ids or requirement.resource_commitment is not None
            or connection.connection_id != f'connection.{node}.conditional-model' or connection.requirement_id != requirement.requirement_id
            or connection.consumer_input_id != 'supplier' or connection.assessment_operation_id != node or connection.claim_id != f'claim.{node}'
            or connection.evidence_role is not role or connection.falsifier != FALSIFIER or connection.supplier_operation_id is not None
            or connection.external_input_id != f'external.{node}.supplier'):
        raise ValueError('cycle scientific requirement/connection changes its assessed condition or role')


def _actual_product(draft, products):
    operation, config = _config(draft)
    output_type = CycleSupply if config.operation == 'supply' else CycleUseProduct
    outputs = products['records'].get(operation.node_id, {})
    if not outputs:
        return operation, config, None
    if len(outputs) != 1 or set(outputs) != {operation.node_id + '.product'} or type(next(iter(outputs.values()))) is not output_type:
        raise ValueError('cycle actual product changes exact output census/type')
    record = next(iter(outputs.values()))
    receipt = products['receipts'][operation.node_id]
    logicals = tuple(row for row in receipt.output_logical_artifacts if row.payload_schema == record.SCHEMA and row.content_sha256 == record.fingerprint())
    if receipt.operational_status is not OperationalStatus.SUCCEEDED or len(logicals) != 1:
        raise ValueError('cycle product lacks its exact successful producing receipt')
    if type(record) is CycleSupply:
        assessment.validate_supplier(record)
        if record.design != config.design or config.operands != (record.design.source,):
            raise ValueError('cycle supply substitutes original mechanism source')
    else:
        record.__post_init__()
        assessment.validate_supplier(record.model)
        if (record.model.design != config.design or record.supplier not in config.operands
                or identity(record.instance) not in config.operands or record.instance.macro_source not in config.operands):
            raise ValueError('cycle actual use substitutes supplier, original macro source or instance')
    return operation, config, record


def describe_contributions(draft, authenticated_products):
    operation, config, record = _actual_product(draft, authenticated_products)
    if record is None:
        return ()
    receipt = authenticated_products['receipts'][operation.node_id]
    logical = next(row for row in receipt.output_logical_artifacts if row.content_sha256 == record.fingerprint() and row.payload_schema == record.SCHEMA)
    artifact = authenticated_products['outputs'][logical.logical_artifact_id]
    if artifact.logical != logical or artifact.logical.content_sha256 != record.fingerprint():
        raise ValueError('cycle contribution differs from authenticated producing artifact')
    role = ContributionRole.DESIGN_OPERAND if config.operation == 'supply' else ContributionRole.INSTANCE_PRODUCT
    product = ContributionProduct(f'product.{operation.node_id}.{role.value.lower()}', identity(record),
        ArtifactIdentity(logical.logical_artifact_id, 'scientific-product', record.SCHEMA, record.fingerprint(),
                         artifact.logical.media_type, artifact.materialization.size_bytes),
        ObjectIdentity.from_record(receipt.receipt_id, receipt), role, EvidenceCeiling.NON_PROMOTABLE,
        artifact.logical.outcome_access, artifact.logical.visibility_ceiling)
    check = record.check if type(record) is CycleSupply else record
    return (ContributionManifest(f'contribution.{draft.draft_id}', QUESTION,
        'Assessed conditional gas-cycle mathematics supports later source-bound queries; candidate microrates, matched assays and biological qualification remain unknown.',
        record.scope, (product,), (identity(check),), (),
        tuple(ObjectIdentity.from_record(row.contribution_id, row) for row in draft.contribution_parents)),)


def next_wave_builder(draft, manifest, authenticated_products):
    if describe_contributions(draft, authenticated_products) != (manifest,):
        raise ValueError('cycle successor changes actual receipt-bound contribution')
    _, config, record = _actual_product(draft, authenticated_products)
    if config.successor is None:
        return None
    return (use_draft(record, config.successor, parent=manifest, successor=config.reuse_successor) if config.operation == 'supply'
            else reuse_draft(record, config.successor, parent=manifest))


def inquiry_endpoint_validator(draft, endpoint):
    _, config = _config(draft)
    if endpoint != scope(config.design):
        raise ValueError('cycle inquiry changes original conditional model endpoint scope')


def inquiry_outcome_projector(draft, specification, products):
    inquiry_endpoint_validator(draft, specification.endpoint)
    operation, _, record = _actual_product(draft, products)
    if specification.distinguishing_assessment != operation.config_identity:
        raise ValueError('cycle inquiry substitutes designated actual assessment configuration')
    if record is None:
        return 'unresolved'
    return 'useful-supply' if record.disposition is AssessmentDisposition.SATISFIED else 'scoped-failure'


def inquiry_evidence_projector(draft, payloads, products=None):
    operation, config = _config(draft)
    phase = next(row for row in PHASES if row[0] == config.operation)
    codecs = dict(phase[1])
    links = tuple(row for row in draft.links if row.consumer_node_id == operation.node_id)
    if len(links) != len(codecs) or {row.consumer_input_id for row in links} != set(codecs):
        raise ValueError('cycle evidence changes complete original operand census')
    external = {row.input_id: row for row in draft.external_inputs}
    bindings, inputs = [], {}
    for link in links:
        selected = external[link.external_input_id]
        record = decode_canonical_bytes(payloads['external-' + sha256(selected.input_id.encode()).hexdigest()[:24] + '.json'],
                                        codecs[link.consumer_input_id], maximum_bytes=None)
        if selected.expected_content_sha256 != record.fingerprint():
            raise ValueError('cycle evidence changes original operand bytes')
        inputs[link.consumer_input_id] = record
        if link.consumer_input_id == 'source':
            if design_from_source(record) != config.design or selected.scientific_role != 'SOURCE':
                raise ValueError('cycle evidence changes original mechanism source role')
            original = ScientificConditionScope('system.rubisco-cycle.mechanism-sources', 'world.rubisco-cycle.exposed-inputs', record.input_id,
                ('original-source-bytes',), ('byte',), 'receiver.original-mechanism-audit', 'clock.' + record.cutoff,
                'Exact published mechanism source bytes, not biological microrate measurements.', source_config_sha256=record.fingerprint())
            role = ContributionRole.RETAINED_ANALYSIS_INPUT
        elif link.consumer_input_id == 'macro-source':
            if selected.scientific_role != 'SOURCE':
                raise ValueError('cycle evidence changes original macro source role')
            original, role = portfolio.original_source_scope(record), ContributionRole.RETAINED_ANALYSIS_INPUT
        elif link.consumer_input_id == 'supplier':
            wanted = 'MODEL' if config.operation == 'use' else 'OUTCOME'
            model = record if type(record) is CycleSupply else record.model
            assessment.validate_supplier(model)
            if model.design != config.design or selected.scientific_role != wanted:
                raise ValueError('cycle evidence changes original supplier role/scope')
            original = record.scope
            role = ContributionRole.DESIGN_OPERAND if type(record) is CycleSupply else ContributionRole.INSTANCE_PRODUCT
        else:
            if selected.scientific_role != 'SOURCE':
                raise ValueError('cycle evidence changes original conditional query role')
            original = ScientificConditionScope('system.rubisco-cycle.hypothetical-query', 'world.rubisco-cycle.exposed-inputs', record.instance_id,
                ('latent-dimensionless-coordinates',), ('dimensionless',), 'receiver.declared-conditional-query', 'clock.exposed-conditional-query',
                'Complete declared hypothetical u/v and release sensitivity census with source-bound candidate/reference selections, not observed microscopic parameters.',
                source_config_sha256=record.fingerprint(), instance_id=record.instance_id)
            role = ContributionRole.RETAINED_ANALYSIS_INPUT
        bindings.append(InquiryEvidenceBinding(selected.input_id, record.fingerprint(), original, role, (), draft.development_study.numerical_view_ids))
    if tuple(sorted((identity(row) for row in inputs.values()), key=lambda row: row.object_id)) != config.operands:
        raise ValueError('cycle evidence substitutes configured original operands')
    if config.operation != 'supply':
        assessment.validate_instance(inputs['macro-source'], inputs['instance'])
    if products is not None:
        _, _, actual = _actual_product(draft, products)
        if actual is not None:
            expected = (assessment.supply(inputs['source']) if config.operation == 'supply'
                        else assessment.assess_use(inputs['supplier'], inputs['macro-source'], inputs['instance']))
            if actual != expected:
                raise ValueError('cycle actual product differs from source-bound independent assessment')
            role = ContributionRole.DESIGN_OPERAND if type(actual) is CycleSupply else ContributionRole.INSTANCE_PRODUCT
            bindings.append(InquiryEvidenceBinding(operation.node_id + '.product', actual.fingerprint(), actual.scope, role, (),
                                                  draft.development_study.numerical_view_ids))
    return tuple(sorted(bindings, key=lambda row: row.binding_id))
