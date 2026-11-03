# SPDX-License-Identifier: MPL-2.0
"""Declarative single-operation drafts and actual receipt-bound contributions."""
from empirical_lawhood.kernel.authority import AuthorityAction, AuthorityPolicy, SourceAccessClass
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.recursive_requirements import ContributionRole
from empirical_lawhood.kernel.scientific_contributions import ContributionManifest, ContributionProduct
from empirical_lawhood.kernel.status import LifecycleStatus, OperationalStatus
from empirical_lawhood.planning.campaigns import CampaignLane, CampaignNode, CampaignNodeKind, CampaignSpec, DecisionRight
from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft
from empirical_lawhood.runtime.plans import ScientificInputRole
from . import science
from .operation_bindings import BUDGET, MAX_BYTES, MEDIA, NAMESPACE, InquiryOperationConfig, development_root, operation_registrations, record_identity, source_identity, supported_development_root
from .science import RubiscoAssessment, RubiscoSupply


def _draft(role, inputs, source, *, scientific_design, parent=None, draft_id):
    operands = tuple(sorted((record_identity(record) for _, record in inputs), key=lambda v: v.object_id))
    config = InquiryOperationConfig(f'config.{NAMESPACE}.{role}', role, source, operands, scientific_design)
    root = development_root(config, study_id=f'study.{draft_id}')
    policy = AuthorityPolicy(f'policy.{draft_id}', 'owner.local-researcher', 'operator.local-development',
        (root.study_id,), frozenset((root.world_kind,)),
        frozenset((AuthorityAction.REPOSITORY_IMPLEMENTATION, AuthorityAction.SIMULATION_EXECUTION)),
        frozenset((SourceAccessClass.NONE,)), ('gate.local-nonactuating-development',), frozenset(), BUDGET,
        OutcomeAccess.DEVELOPMENT_VISIBLE)
    root_id = f'design.{draft_id}'
    node = CampaignNode(root_id, CampaignNodeKind.EVIDENCE_SNAPSHOT, CampaignLane.EXPLORATORY,
        ObjectIdentity.from_record(root.study_id, root), (), LifecycleStatus.ACTIVE)
    campaign = CampaignSpec(f'campaign.{draft_id}', root.question, (root.system.object_id,), (root.world_id,),
        tuple(c.claim_id for c in root.claims), BUDGET, ObjectIdentity.from_record(policy.policy_id, policy),
        (DecisionRight(f'decision-right.{draft_id}', AuthorityAction.SIMULATION_EXECUTION,
                       'owner.local-researcher', policy.policy_id, False),), (node,), (root_id,), (root_id,), (), LifecycleStatus.ACTIVE)
    registration = next(r for r in operation_registrations() if r.selection.capability_key == f'{NAMESPACE}.{role}')
    node_id = f'{NAMESPACE}.{role}'
    operation = RecursiveOperationSpec.from_config(node_id=node_id, selection=registration.selection,
        config_id=config.config_id, config=config, obligation_ids=(f'obligation.{node_id}.exact-scope',), resource_budget=BUDGET)
    external, links = [], []
    for port, record in inputs:
        identity = record_identity(record)
        logical_id = identity.object_id
        scientific_role = ScientificInputRole.MODEL.value if port == 'supplier' else 'SOURCE'
        if port == 'supplier' and parent is not None:
            products = tuple(v for v in parent.products if v.record == identity and v.role is ContributionRole.DESIGN_OPERAND)
            if len(products) != 1 or parent.scope != record.scope:
                raise ValueError('later use changes exact parent product, scope or permitted role')
            logical_id = products[0].artifact.artifact_id
        input_id = f'external.{node_id}.{port}'
        external.append(RecursiveExternalInput(input_id, logical_id, record.SCHEMA, MEDIA, MAX_BYTES,
            OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY, record.fingerprint(), scientific_role))
        links.append(RecursiveInputLink(f'edge.{node_id}.{port}', node_id, port, external_input_id=input_id,
                                       scientific_role=scientific_role))
    return RecursiveStudyDraft(draft_id, root.question, campaign, (), (), (), (operation,),
        tuple(sorted(external, key=lambda v: v.input_id)), tuple(sorted(links, key=lambda v: v.edge_id)), (node_id,),
        development_study=root, contribution_parents=() if parent is None else (parent,))


def supply_draft(article, genbank, *, draft_id='draft.rubisco-inquiry.supply'):
    from empirical_lawhood.adapters.methods.rubisco_combinations.analysis import wilson_quartet_science
    from empirical_lawhood.adapters.methods.rubisco_combinations.source_binding import decode_source
    panel, parent = decode_source(article, genbank)
    selected = wilson_quartet_science(panel, parent)
    return _draft('supply', (('article', article), ('genbank', genbank)),
                  ObjectIdentity.from_record(selected.science_id, selected), scientific_design=selected, draft_id=draft_id)


def use_draft(supplier, instance=None, *, parent=None, draft_id='draft.rubisco-inquiry.use'):
    if type(supplier) is not RubiscoSupply:
        raise ValueError('later draft requires the actual typed scoped supplier')
    instance = science.authentic_candidate(supplier) if instance is None else instance
    return _draft('use', (('supplier', supplier), ('instance', instance)), source_identity(supplier), scientific_design=supplier.science, parent=parent, draft_id=draft_id)


def describe_contributions(draft, authenticated_products):
    entries = [(task, output, record) for task, records in authenticated_products['records'].items()
               for output, record in records.items() if type(record) is RubiscoSupply]
    if not entries:
        return ()
    if len(entries) != 1:
        raise ValueError('compact inquiry contribution has one actual supplier product')
    task, _, record = entries[0]
    selected = tuple(v for v in draft.operations if v.node_id in draft.selected_operation_ids)
    if len(selected) != 1 or selected[0].node_id != task:
        raise ValueError('contribution changes exact selected producing operation')
    config = decode_canonical_bytes(selected[0].config_payload.encode(), InquiryOperationConfig, maximum_bytes=MAX_BYTES)
    if config.operation != 'supply' or config.source != source_identity(record):
        raise ValueError('contribution substitutes source/config identity')
    receipt = authenticated_products['receipts'][task]
    if receipt.operational_status is not OperationalStatus.SUCCEEDED:
        raise ValueError('contribution requires its actual successful producing receipt')
    logicals = tuple(v for v in receipt.output_logical_artifacts if v.payload_schema == record.SCHEMA and v.content_sha256 == record.fingerprint())
    if len(logicals) != 1:
        raise ValueError('contribution supplier is not a unique actual receipt-bound output')
    logical = logicals[0]
    artifact = authenticated_products['outputs'][logical.logical_artifact_id]
    if artifact.logical.content_sha256 != record.fingerprint():
        raise ValueError('contribution supplier differs from authenticated artifact')
    identity = record_identity(record)
    product = ContributionProduct(f'product.{task}.design-operand', identity,
        ArtifactIdentity(logical.logical_artifact_id, 'scientific-product', record.SCHEMA, record.fingerprint(),
                         artifact.logical.media_type, artifact.materialization.size_bytes),
        ObjectIdentity.from_record(receipt.receipt_id, receipt), ContributionRole.DESIGN_OPERAND,
        EvidenceCeiling.NON_PROMOTABLE, artifact.logical.outcome_access, artifact.logical.visibility_ceiling)
    # The supplier is an assessed procedure product, never biological qualification.
    assessment = ObjectIdentity.from_record(record.evaluation.evaluation_id, record.evaluation)
    return (ContributionManifest(f'contribution.{draft.draft_id}', science.QUESTION,
        'Exact exposed scoped numerical procedure available for a separate instance assessment; qualification remains absent.',
        record.scope, (product,), (assessment,), (),
        tuple(ObjectIdentity.from_record(v.contribution_id, v) for v in draft.contribution_parents)),)


def next_wave_builder(draft, manifest, authenticated_products):
    if describe_contributions(draft, authenticated_products) != (manifest,):
        raise ValueError('successor substitutes its actual receipt-bound contribution')
    supplier = next(record for records in authenticated_products['records'].values() for record in records.values() if type(record) is RubiscoSupply)
    from .policy_binding import assessed_use_draft, contracts
    requirements, connection = contracts(supplier.scope)
    if draft.requirements == requirements and draft.connections == (connection,):
        return assessed_use_draft(supplier, parent=manifest)
    return use_draft(supplier, parent=manifest)


def inquiry_outcome_projector(draft, specification, products):
    """Project only the exact authenticated assessment; never accept a caller score."""
    inquiry_endpoint_validator(draft, specification.endpoint)
    selected = tuple(v for v in draft.operations if v.node_id in draft.selected_operation_ids)
    if len(selected) != 1 or specification.distinguishing_assessment != selected[0].config_identity:
        raise ValueError('inquiry specification changes exact selected assessment/configuration')
    config = decode_canonical_bytes(selected[0].config_payload.encode(), InquiryOperationConfig, maximum_bytes=MAX_BYTES)
    if not supported_development_root(config, draft.development_study):
        raise ValueError('inquiry assessment changes exact root/science identity')
    expected_type = RubiscoSupply if config.operation == 'supply' else RubiscoAssessment
    outputs = products['records'].get(selected[0].node_id, {})
    records = tuple(v for v in outputs.values() if type(v) is expected_type)
    if not records:
        if outputs:
            raise ValueError('inquiry changes typed assessment output')
        return 'unresolved'
    if len(records) != 1 or len(outputs) != 1:
        raise ValueError('inquiry assessment output census differs')
    record = records[0]
    receipt = products['receipts'][selected[0].node_id]
    if receipt.operational_status is not OperationalStatus.SUCCEEDED:
        raise ValueError('inquiry product lacks successful producing receipt')
    logicals = tuple(v for v in receipt.output_logical_artifacts
                     if v.payload_schema == record.SCHEMA and v.content_sha256 == record.fingerprint())
    if len(logicals) != 1:
        raise ValueError('inquiry assessment is not its exact producing receipt output')
    if config.operation == 'supply':
        if source_identity(record) != config.source or specification.endpoint != record.scope:
            raise ValueError('inquiry changes scientific source or endpoint scope')
        science.RubiscoSupply(record.product_id, record.science, record.panel, record.forecast, record.evaluation, record.scope, record.disposition)
    else:
        supplier_operands = tuple(value for value in config.operands if value.object_schema == RubiscoSupply.SCHEMA)
        if (len(supplier_operands) != 1 or record.supplier != supplier_operands[0]
                or record_identity(record.instance if hasattr(record, 'instance') else record.candidate) not in config.operands):
            raise ValueError('inquiry changes exact supplier or instance assembly')
        # The endpoint retains its original supplier scope, including unresolved biology.
        if specification.endpoint != record.scope or record.scope.source_config_sha256 != config.source.object_fingerprint:
            raise ValueError('inquiry changes endpoint source/config identity')
    from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition
    return ('useful-supply' if record.disposition is AssessmentDisposition.SATISFIED else
            'unresolved' if record.disposition is AssessmentDisposition.UNEVALUABLE else 'scoped-failure')


def inquiry_evidence_projector(draft, payloads, products=None):
    """Retain original source meaning independently of any requested endpoint."""
    from hashlib import sha256
    from empirical_lawhood.kernel.recursive_requirements import ScientificConditionScope
    from empirical_lawhood.runtime.recursive_inquiry import InquiryEvidenceBinding
    from .operation_bindings import PHASES
    from .science import RubiscoCandidate
    selected = tuple(op for op in draft.operations if op.node_id in draft.selected_operation_ids)
    if len(selected) != 1:
        raise ValueError('Rubisco evidence needs its exact single operation')
    operation = selected[0]
    config = decode_canonical_bytes(operation.config_payload.encode(), InquiryOperationConfig, maximum_bytes=MAX_BYTES)
    if (not supported_development_root(config, draft.development_study)
            or operation.node_id != f'{NAMESPACE}.{config.operation}'):
        raise ValueError('Rubisco evidence changes frozen root or source role')
    inputs = dict(next(row[1] for row in PHASES if row[0] == config.operation))
    incoming = tuple(link for link in draft.links if link.consumer_node_id == operation.node_id)
    if (len(incoming) != len(inputs) or {link.consumer_input_id for link in incoming} != set(inputs)
            or any(link.external_input_id is None for link in incoming)):
        raise ValueError('Rubisco evidence source role census differs')
    external_by_id = {external.input_id: external for external in draft.external_inputs}
    bindings, records = [], []
    for link in incoming:
        external = external_by_id[link.external_input_id]
        filename = 'external-' + sha256(external.input_id.encode()).hexdigest()[:24] + '.json'
        record = decode_canonical_bytes(payloads[filename], inputs[link.consumer_input_id], maximum_bytes=MAX_BYTES)
        if external.expected_content_sha256 != record.fingerprint():
            raise ValueError('Rubisco evidence source bytes differ from exact configured operand')
        records.append(record_identity(record))
        if link.consumer_input_id == 'article':
            from empirical_lawhood.adapters.methods.rubisco_combinations.source_binding import WILSON_SOURCE_SHA256
            if record.source_sha256 != WILSON_SOURCE_SHA256 or external.scientific_role != 'SOURCE':
                raise ValueError('Rubisco article evidence source or original role differs')
            scope = ScientificConditionScope('system.wilson2017.native-article', 'world.wilson2017.exposed-table',
                'source.wilson2017.article', ('specificity', 'turnover'), ('dimensionless', 's^-1'),
                'receiver.wilson2017.reported-assays', 'clock.wilson2017.exposed-table',
                'Original nineteen-row Wilson article panel and assay context; no scoped transfer warrant or invented independent biological n.',
                source_config_sha256=record.source_sha256)
            role, views = ContributionRole.RETAINED_ANALYSIS_INPUT, ('view.wilson2017.nineteen-native-rows',)
        elif link.consumer_input_id == 'genbank':
            from empirical_lawhood.adapters.methods.rubisco_combinations.source_binding import GENBANK_SOURCE_SHA256
            if record.source_sha256 != GENBANK_SOURCE_SHA256 or external.scientific_role != 'SOURCE':
                raise ValueError('Rubisco GenBank evidence source or original role differs')
            scope = ScientificConditionScope('system.te.deposited-parent', 'world.te.exposed-sequence',
                'source.te.mg000148.1', ('lsu-sequence', 'ssu-sequence'), ('residue', 'residue'),
                'receiver.deposited-cds-translations', 'clock.deposited-record-version',
                'MG000148.1 deposited ATN39932.1/ATN39933.1 nucleotide/CDS parent; sequence evidence supplies no kinetic measurement.',
                source_config_sha256=record.source_sha256)
            role, views = ContributionRole.RETAINED_ANALYSIS_INPUT, ('view.te.deposited-lsu-ssu',)
        elif link.consumer_input_id == 'supplier':
            if source_identity(record) != config.source or external.scientific_role != ScientificInputRole.MODEL.value:
                raise ValueError('Rubisco supplier evidence changes original source or contribution role')
            scope, role = record.scope, ContributionRole.DESIGN_OPERAND
            views = draft.development_study.numerical_view_ids
        else:
            if type(record) is not RubiscoCandidate or external.scientific_role != 'SOURCE':
                raise ValueError('Rubisco instance evidence changes exact original operand role')
            scope = ScientificConditionScope('system.rubisco.conditional-candidate', 'world.rubisco.conditional-input',
                record.candidate_id, ('specificity', 'turnover'), ('dimensionless', 's^-1'),
                'receiver.conditional-endpoint-arithmetic', 'clock.exposed-conditional-input',
                'Exact supplied candidate assembly and disclosed conditional endpoint operands; unavailable endpoints remain missing; paired biological assay admission unresolved.',
                source_config_sha256=record.fingerprint(), instance_id=record.candidate_id)
            role, views = ContributionRole.RETAINED_ANALYSIS_INPUT, ('view.rubisco.conditional-endpoint-input',)
        bindings.append(InquiryEvidenceBinding(external.input_id, record.fingerprint(), scope, role, (), tuple(sorted(views))))
    if tuple(sorted(records, key=lambda value: value.object_id)) != config.operands:
        raise ValueError('Rubisco evidence changes exact configured original source identities')
    if products is not None:
        outputs = products['records'].get(operation.node_id, {})
        expected_type = RubiscoSupply if config.operation == 'supply' else RubiscoAssessment
        if len(outputs) > 1 or any(type(record) is not expected_type for record in outputs.values()):
            raise ValueError('Rubisco evidence product census or essential scoped metadata differs')
        for output_id, record in outputs.items():
            if output_id != operation.node_id + '.product':
                raise ValueError('Rubisco evidence changes original output identity')
            if record.scope != science.scope(config.scientific_design):
                raise ValueError('Rubisco product changes its declared original scope')
            role = ContributionRole.DESIGN_OPERAND if type(record) is RubiscoSupply else ContributionRole.INSTANCE_PRODUCT
            bindings.append(InquiryEvidenceBinding(output_id, record.fingerprint(), record.scope, role, (),
                                                  draft.development_study.numerical_view_ids))
    return tuple(sorted(bindings, key=lambda value: value.binding_id))


def inquiry_endpoint_validator(draft, endpoint):
    """Validate history scope without selecting that wave as the current assessment."""
    selected = tuple(operation for operation in draft.operations if operation.node_id in draft.selected_operation_ids)
    if len(selected) != 1:
        raise ValueError('inquiry endpoint needs its exact single registered operation')
    operation = selected[0]
    config = decode_canonical_bytes(operation.config_payload.encode(), InquiryOperationConfig, maximum_bytes=MAX_BYTES)
    from .operation_bindings import operation_registrations
    registrations = tuple(registration for registration in operation_registrations()
                          if registration.selection == operation.selection)
    if (len(registrations) != 1 or operation.config_id != config.config_id
            or operation.node_id != f'{NAMESPACE}.{config.operation}'
            or operation.selection.capability_key != f'{NAMESPACE}.{config.operation}'
            or not supported_development_root(config, draft.development_study)):
        raise ValueError('inquiry endpoint changes exact selected configuration or scientific root')
    if endpoint != science.scope(config.scientific_design):
        raise ValueError('inquiry changes frozen original design endpoint scope')
    return None
