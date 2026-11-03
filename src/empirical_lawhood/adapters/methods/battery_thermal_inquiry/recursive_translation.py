# SPDX-License-Identifier: MPL-2.0
"""Native procedure, distinct instance use and receipt-backed subsequent reuse."""
from hashlib import sha256
from decimal import Decimal

from empirical_lawhood.kernel.authority import AuthorityAction, AuthorityPolicy, SourceAccessClass
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition, ConditionRole, ContributionRole, ScientificConditionScope, ScientificConnectionSpec, ScientificRequirementSpec
from empirical_lawhood.kernel.scientific_contributions import ContributionManifest, ContributionProduct
from empirical_lawhood.kernel.status import LifecycleStatus, OperationalStatus
from empirical_lawhood.planning.campaigns import CampaignLane, CampaignNode, CampaignNodeKind, CampaignSpec, DecisionRight
from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft
from empirical_lawhood.runtime.recursive_inquiry import InquiryEvidenceBinding
from . import science
from .contracts import BatteryInquirySource, BatteryInquirySupply, QUESTION, scope
from .operation_bindings import (BUDGET, MAX_BYTES, MEDIA, NAMESPACE, PHASES, BatteryInquiryAssessedInstance, BatteryInquiryOperationConfig,
                                BatteryInquiryNativeCensus, development_root, operation_registrations, native_census)

CONDITION = 'Actual independently assessed temperature-dependent conservative hybrid model procedure supplies its distinct later preparation, complete finite-menu admission and joined native charging use under the declared localization bands.'
FALSIFIER = 'Changed source/protocol/preparation, missing native receiver or alternative census, unassessed model transfer, erroneous admission, or violated delivered charge/sample envelope.'


def _pair(node, source, parent, product):
    requirement = ScientificRequirementSpec(f'requirement.{node}.thermal-procedure', node, ConditionRole.EVIDENTIAL,
        QUESTION, CONDITION, scope(source), node, FALSIFIER, (product.role,))
    connection = ScientificConnectionSpec(f'connection.{node}.thermal-procedure', requirement.requirement_id, None, None,
        'supplier', node, f'claim.{node}', product.role, FALSIFIER, ObjectIdentity.from_record(parent.contribution_id, parent),
        product.product_id, f'external.{node}.supplier')
    return requirement, connection


def validate_requirement_config(config, requirement, connection):
    node = f'{NAMESPACE}.{config.operation}'
    role = ContributionRole.DESIGN_OPERAND if config.operation == 'use' else ContributionRole.INSTANCE_PRODUCT
    if (config.operation == 'supply' or requirement.requirement_id != f'requirement.{node}.thermal-procedure'
            or requirement.consumer_operation_id != node or requirement.condition_role is not ConditionRole.EVIDENTIAL
            or requirement.purpose != QUESTION or requirement.condition != CONDITION or requirement.scope != scope(config.source)
            or requirement.assessment_operation_id != node or requirement.falsifier != FALSIFIER or requirement.permitted_roles != (role,)
            or requirement.further_requirement_ids or requirement.background_assumption_ids or requirement.resource_commitment is not None
            or connection.connection_id != f'connection.{node}.thermal-procedure' or connection.requirement_id != requirement.requirement_id
            or connection.consumer_input_id != 'supplier' or connection.assessment_operation_id != node or connection.claim_id != f'claim.{node}'
            or connection.evidence_role is not role or connection.falsifier != FALSIFIER or connection.supplier_operation_id is not None
            or connection.external_input_id != f'external.{node}.supplier'):
        raise ValueError('thermal requirement/connection changes its actual scientific condition, original scope or role')


def validate_requirement_record(record, requirement, connection):
    if type(record) is not BatteryInquiryAssessedInstance:
        raise ValueError('thermal assessment projector needs actual assessed-instance product')
    record.__post_init__()
    phase = record.assessment.instance.phase
    operand = next((row for row in ('use', 'reuse') if row == phase), None)
    if operand is None:
        raise ValueError('thermal assessed instance changes exact later/reuse phase')
    # The record's original source and phase select the closed requirement
    # grammar; exact incoming product ownership is proved by common custody.
    config = type('ScientificConfig', (), {'operation': phase, 'source': record.source})()
    validate_requirement_config(config, requirement, connection)


def _draft(role, inputs, source, *, parent=None, draft_id):
    science.validate_source(source)
    config = BatteryInquiryOperationConfig(f'config.{NAMESPACE}.{role}', role, source,
        tuple(sorted((science.identity(record) for _, record in inputs), key=lambda row: row.object_id)))
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
        config=config, obligation_ids=(f'obligation.{node}.source-and-native-census',), resource_budget=BUDGET,
        resource_lock_ids=('battery-native-single-worker',))
    external, links, requirements, connections = [], [], [], []
    for port, record in inputs:
        value = science.identity(record)
        logical_id = value.object_id
        graph_role = ('OUTCOME' if role == 'reuse' else 'MODEL') if port == 'supplier' else 'SOURCE'
        pair = None
        if port == 'supplier' and parent is not None:
            wanted = ContributionRole.INSTANCE_PRODUCT if role == 'reuse' else ContributionRole.DESIGN_OPERAND
            products = tuple(row for row in parent.products if row.record == value and row.role is wanted)
            if len(products) != 1 or parent.scope != scope(source):
                raise ValueError('thermal next instance changes exact parent product, original scope or role')
            logical_id = products[0].artifact.artifact_id
            pair = _pair(node, source, parent, products[0])
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


def supply_draft(source=None, *, draft_id='draft.battery-thermal-inquiry.supply'):
    source = BatteryInquirySource() if source is None else source
    return _draft('supply', (('source', source),), source, draft_id=draft_id)


def use_draft(supplier, instance=None, *, parent=None, draft_id='draft.battery-thermal-inquiry.use'):
    if type(supplier) is not BatteryInquirySupply:
        raise ValueError('thermal use requires its actual typed source procedure')
    science.validate_supply(supplier)
    expected = science.compatible_instance(supplier, 'use')
    instance = expected if instance is None else instance
    if instance != expected:
        raise ValueError('thermal use changes exact actual supplier or later preparation')
    return _draft('use', (('instance', instance), ('supplier', supplier)), supplier.source, parent=parent, draft_id=draft_id)


def reuse_draft(previous, instance=None, *, parent=None, draft_id='draft.battery-thermal-inquiry.reuse'):
    if type(previous) is not BatteryInquiryAssessedInstance or previous.assessment.instance.phase != 'use':
        raise ValueError('thermal reuse requires the actual distinct prior use')
    previous.__post_init__()
    expected = science.compatible_instance(previous.supplier, 'reuse', prior_use=previous.assessment)
    instance = expected if instance is None else instance
    if instance != expected:
        raise ValueError('thermal reuse changes original supplier or subsequent preparation')
    return _draft('reuse', (('instance', instance), ('supplier', previous)), previous.source, parent=parent, draft_id=draft_id)


def _config(draft):
    selected = tuple(row for row in draft.operations if row.node_id in draft.selected_operation_ids)
    if len(selected) != 1:
        raise ValueError('thermal inquiry needs exactly one selected registered operation')
    operation = selected[0]
    config = decode_canonical_bytes(operation.config_payload.encode(), BatteryInquiryOperationConfig, maximum_bytes=None)
    registration = next(row for row in operation_registrations() if row.selection.capability_key == f'{NAMESPACE}.{config.operation}')
    if (operation.selection != registration.selection or operation.node_id != f'{NAMESPACE}.{config.operation}'
            or operation.config_id != config.config_id or draft.development_study != development_root(config, study_id=draft.development_study.study_id)):
        raise ValueError('thermal inquiry changes exact scientific source/configuration/root/registration')
    return operation, config


def _actual_product(draft, products):
    operation, config = _config(draft)
    outputs = products['records'].get(operation.node_id, {})
    if not outputs:
        return operation, config, None
    expected_type = BatteryInquirySupply if config.operation == 'supply' else BatteryInquiryAssessedInstance
    if (set(outputs) != {operation.node_id+'.product', operation.node_id+'.native-census'}
            or type(outputs[operation.node_id+'.product']) is not expected_type
            or type(outputs[operation.node_id+'.native-census']) is not BatteryInquiryNativeCensus):
        raise ValueError('thermal inquiry changes exact product/native census output denominator')
    record, census = outputs[operation.node_id+'.product'], outputs[operation.node_id+'.native-census']
    receipt = products['receipts'][operation.node_id]
    if receipt.operational_status is not OperationalStatus.SUCCEEDED or len(receipt.output_logical_artifacts) != 2:
        raise ValueError('thermal inquiry requires its exact complete successful publication receipt')
    for value in (record, census):
        if sum(row.payload_schema == value.SCHEMA and row.content_sha256 == value.fingerprint() for row in receipt.output_logical_artifacts) != 1:
            raise ValueError('thermal inquiry product/census differs from actual producing receipt')
    if type(record) is BatteryInquirySupply:
        science.validate_supply(record)
        if record.source != config.source or config.operands != (science.identity(record.source),):
            raise ValueError('thermal supply substitutes source/configured input')
    else:
        record.__post_init__()
        expected_schema = BatteryInquirySupply.SCHEMA if config.operation == 'use' else BatteryInquiryAssessedInstance.SCHEMA
        supplier_ids = tuple(row for row in config.operands if row.object_schema == expected_schema)
        if (record.source != config.source or record.assessment.instance.phase != config.operation
                or science.identity(record.assessment.instance) not in config.operands or len(supplier_ids) != 1
                or config.operation == 'use' and supplier_ids[0] != science.identity(record.supplier)):
            raise ValueError('thermal actual instance substitutes original source, supplier, phase or preparation')
        if config.operation == 'reuse':
            previous = BatteryInquiryAssessedInstance('product.battery-thermal-inquiry.use', record.supplier, record.prior_use)
            if supplier_ids[0] != science.identity(previous):
                raise ValueError('thermal reuse substitutes its exact configured actual prior use product')
    if census != native_census(record, config.operation):
        raise ValueError('thermal current native census substitutes/duplicates ancestor traces or measured expense')
    return operation, config, record


def describe_contributions(draft, authenticated_products):
    operation, config, record = _actual_product(draft, authenticated_products)
    if record is None:
        return ()
    receipt = authenticated_products['receipts'][operation.node_id]
    logical = next(row for row in receipt.output_logical_artifacts if row.payload_schema == record.SCHEMA and row.content_sha256 == record.fingerprint())
    artifact = authenticated_products['outputs'][logical.logical_artifact_id]
    if artifact.logical != logical:
        raise ValueError('thermal contribution differs from authenticated actual artifact')
    role = ContributionRole.DESIGN_OPERAND if config.operation == 'supply' else ContributionRole.INSTANCE_PRODUCT
    product = ContributionProduct(f'product.{operation.node_id}.{role.value.lower()}', science.identity(record),
        ArtifactIdentity(logical.logical_artifact_id, 'scientific-product', record.SCHEMA, record.fingerprint(),
                         artifact.logical.media_type, artifact.materialization.size_bytes),
        ObjectIdentity.from_record(receipt.receipt_id, receipt), role, EvidenceCeiling.NON_PROMOTABLE,
        artifact.logical.outcome_access, artifact.logical.visibility_ceiling)
    assessed = record.check if type(record) is BatteryInquirySupply else record.assessment
    return (ContributionManifest(f'contribution.{draft.draft_id}', QUESTION,
        'Actual conservative hybrid sampled numerical model-selection/instance evidence retained for a separate use; no exact pointwise ideal control, physical/continuous certificate or comparative superiority.',
        record.scope, (product,), (science.identity(assessed),), (),
        tuple(ObjectIdentity.from_record(row.contribution_id, row) for row in draft.contribution_parents)),)


def next_wave_builder(draft, manifest, authenticated_products):
    if describe_contributions(draft, authenticated_products) != (manifest,):
        raise ValueError('thermal successor changes actual receipt-backed parent contribution')
    _, config, record = _actual_product(draft, authenticated_products)
    if config.operation == 'supply':
        return use_draft(record, parent=manifest)
    if config.operation == 'use' and record.assessment.traces:
        return reuse_draft(record, parent=manifest)
    return None


def inquiry_endpoint_validator(draft, endpoint):
    _, config = _config(draft)
    if endpoint != scope(config.source):
        raise ValueError('thermal inquiry changes original declared numerical source scope')


def inquiry_outcome_projector(draft, specification, products):
    inquiry_endpoint_validator(draft, specification.endpoint)
    operation, _, record = _actual_product(draft, products)
    if specification.distinguishing_assessment != operation.config_identity:
        raise ValueError('thermal inquiry changes designated actual assessment/configuration')
    if record is None:
        return 'unresolved'
    return ('useful-supply' if record.disposition is AssessmentDisposition.SATISFIED else
            'unresolved' if record.disposition is AssessmentDisposition.UNEVALUABLE else 'scoped-failure')


def inquiry_evidence_projector(draft, payloads, products=None):
    operation, config = _config(draft)
    phase = next(row for row in PHASES if row[0] == config.operation)
    codecs = dict(phase[1])
    links = tuple(row for row in draft.links if row.consumer_node_id == operation.node_id)
    if len(links) != len(codecs) or {row.consumer_input_id for row in links} != set(codecs):
        raise ValueError('thermal evidence changes complete selected external source census')
    external = {row.input_id: row for row in draft.external_inputs}
    bindings, inputs = [], {}
    for link in links:
        selected = external[link.external_input_id]
        record = decode_canonical_bytes(payloads['external-' + sha256(selected.input_id.encode()).hexdigest()[:24] + '.json'],
                                        codecs[link.consumer_input_id], maximum_bytes=None)
        if selected.expected_content_sha256 != record.fingerprint():
            raise ValueError('thermal evidence substitutes original operand bytes')
        inputs[link.consumer_input_id] = record
        if link.consumer_input_id == 'source':
            science.validate_source(record)
            if record != config.source or selected.scientific_role != 'SOURCE':
                raise ValueError('thermal evidence changes initial source scope/role')
            original, role = science.source_scope(science.identity(record)), ContributionRole.RETAINED_ANALYSIS_INPUT
        elif link.consumer_input_id == 'supplier':
            supplier = record if type(record) is BatteryInquirySupply else record.supplier
            if type(record) is BatteryInquiryAssessedInstance:
                record.__post_init__()
                if record.assessment.instance.phase != 'use':
                    raise ValueError('thermal subsequent evidence needs actual distinct prior use')
            science.validate_supply(supplier)
            if supplier.source != config.source or selected.scientific_role != ('OUTCOME' if config.operation == 'reuse' else 'MODEL'):
                raise ValueError('thermal evidence changes original supplier source/role')
            original, role = record.scope, ContributionRole.DESIGN_OPERAND if type(record) is BatteryInquirySupply else ContributionRole.INSTANCE_PRODUCT
        else:
            if record.source != config.source or record.phase != config.operation or selected.scientific_role != 'SOURCE':
                raise ValueError('thermal evidence changes original declared instance preparation/role')
            original = ScientificConditionScope('system.battery-thermal-inquiry.instance-selection', 'world.battery-thermal-inquiry.exposed-inputs',
                record.instance_id, ('initial-temperature',), ('K',), 'receiver.declared-native-preparation', 'clock.native-model-start',
                'Exact original source-bound later preparation selection; no realized native receiver or new physical unit.',
                source_config_sha256=record.fingerprint(), instance_id=record.instance_id, available_by=Decimal(0))
            role = ContributionRole.RETAINED_ANALYSIS_INPUT
        bindings.append(InquiryEvidenceBinding(selected.input_id, record.fingerprint(), original, role, (), draft.development_study.numerical_view_ids))
    if tuple(sorted((science.identity(row) for row in inputs.values()), key=lambda row: row.object_id)) != config.operands:
        raise ValueError('thermal evidence changes original configured operands')
    if config.operation != 'supply':
        supplier = inputs['supplier'] if config.operation == 'use' else inputs['supplier'].supplier
        previous = inputs['supplier'].assessment if config.operation == 'reuse' else None
        expected_instance = (science.compatible_instance(supplier, config.operation, prior_use=previous) if previous is not None
                             else science.compatible_instance(supplier, config.operation))
        if inputs['instance'] != expected_instance:
            raise ValueError('thermal evidence changes exact source-bound later instance')
    if products is not None:
        _, _, actual = _actual_product(draft, products)
        if actual is not None:
            if config.operation != 'supply':
                if actual.supplier != supplier:
                    raise ValueError('thermal actual assessment changes exact authenticated parent source')
                if config.operation == 'reuse':
                    if actual.prior_use != inputs['supplier'].assessment:
                        raise ValueError('thermal reuse substitutes exact authenticated actual prior use')
                    science.validate_assessment(supplier, actual.assessment, prior_use=actual.prior_use)
                else:
                    science.validate_assessment(supplier, actual.assessment)
            role = ContributionRole.DESIGN_OPERAND if type(actual) is BatteryInquirySupply else ContributionRole.INSTANCE_PRODUCT
            bindings.append(InquiryEvidenceBinding(operation.node_id+'.product', actual.fingerprint(), actual.scope, role, (), draft.development_study.numerical_view_ids))
            census = products['records'][operation.node_id][operation.node_id+'.native-census']
            bindings.append(InquiryEvidenceBinding(operation.node_id+'.native-census', census.fingerprint(), scope(config.source),
                ContributionRole.RETAINED_ANALYSIS_INPUT, (), draft.development_study.numerical_view_ids))
    return tuple(sorted(bindings, key=lambda row: row.binding_id))
