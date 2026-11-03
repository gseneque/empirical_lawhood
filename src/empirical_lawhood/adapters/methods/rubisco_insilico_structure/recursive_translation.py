# SPDX-License-Identifier: MPL-2.0
"""Two observed-structure operations consume one authentic nomination OUTCOME."""
from dataclasses import replace
from hashlib import sha256

from empirical_lawhood.adapters.methods.rubisco_nomination_preparation.contracts import NominationDossier
from empirical_lawhood.kernel.authority import AuthorityAction, AuthorityPolicy, SourceAccessClass
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import (
    AssessmentDisposition, ConditionRole, ContributionRole,
    ScientificConnectionSpec, ScientificRequirementSpec,
)
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.scientific_contributions import ContributionManifest, ContributionProduct
from empirical_lawhood.kernel.status import LifecycleStatus, OperationalStatus
from empirical_lawhood.planning.campaigns import (
    CampaignLane, CampaignNode, CampaignNodeKind, CampaignSpec, DecisionRight,
)
from empirical_lawhood.planning.recursive_authoring import (
    RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft,
)
from empirical_lawhood.runtime.recursive_inquiry import InquiryEvidenceBinding
from . import contracts as c, science
from .operation_bindings import (
    BUDGET, MEDIA, development_root, operation_outputs, operation_declarations,
)

ANALYZE = c.NAMESPACE + '.analyze'
ASSESS = c.NAMESPACE + '.assess'
CONDITION = 'Exact authentic Gp I95M nomination and original deposited structures support complete observed biological-assembly mapping, coordinate coverage and preparation uncertainty census; derived mutant geometry remains a separate pending comparison.'
FALSIFIER = 'A changed nomination, original coordinate or sequence digest, assembly operator, atom/residue denominator, processing view or role defeats correspondence. Missing coordinates and inhibited chemical states cannot be interpreted as a demonstrated mutant or catalytic result.'


def requirement_pair(nomination_scope, parent_identity, product_id):
    requirement = ScientificRequirementSpec('requirement.' + ANALYZE + '.nomination',
        ANALYZE, ConditionRole.EVIDENTIAL, c.QUESTION, CONDITION, nomination_scope,
        ASSESS, FALSIFIER, (ContributionRole.INSTANCE_PRODUCT,))
    connection = ScientificConnectionSpec('connection.' + ANALYZE + '.nomination',
        requirement.requirement_id, None, None, 'nomination', ASSESS,
        'claim.' + c.NAMESPACE + '.observed-mapping', ContributionRole.INSTANCE_PRODUCT,
        FALSIFIER, parent_identity, product_id, 'external.' + ANALYZE + '.nomination')
    return requirement, connection


def _validate_requirement(scope, requirement, connection):
    if connection.supplier_contribution is None or connection.supplier_product_id is None:
        raise ValueError('observed mapping requires the actual nomination contribution')
    if (requirement, connection) != requirement_pair(scope, connection.supplier_contribution,
                                                    connection.supplier_product_id):
        raise ValueError('observed mapping changes exact prior scope, condition, role or connection')


def validate_requirement_config(config, requirement, connection):
    config.__post_init__()
    _validate_requirement(config.nomination_scope, requirement, connection)


def validate_requirement_assessment(record, requirement, connection):
    if type(record) is not c.StructuralAssessment:
        raise ValueError('observed source assessment requires its actual canonical product')
    record.__post_init__()
    _validate_requirement(record.prior_nomination_scope, requirement, connection)


def _campaign(root, draft_id):
    policy = AuthorityPolicy('policy.' + draft_id, 'owner.local-researcher', 'operator.local-development',
        (root.study_id,), frozenset((root.world_kind,)),
        frozenset((AuthorityAction.REPOSITORY_IMPLEMENTATION, AuthorityAction.SIMULATION_EXECUTION)),
        frozenset((SourceAccessClass.NONE,)), ('gate.local-nonactuating-development',),
        frozenset(), BUDGET, OutcomeAccess.DEVELOPMENT_VISIBLE)
    node = 'design.' + draft_id
    return CampaignSpec('campaign.' + draft_id, c.QUESTION, (root.system.object_id,),
        (root.world_id,), tuple(row.claim_id for row in root.claims), BUDGET,
        ObjectIdentity.from_record(policy.policy_id, policy),
        (DecisionRight('decision-right.' + draft_id, AuthorityAction.SIMULATION_EXECUTION,
                       'owner.local-researcher', policy.policy_id, False),),
        (CampaignNode(node, CampaignNodeKind.EVIDENCE_SNAPSHOT, CampaignLane.EXPLORATORY,
                      ObjectIdentity.from_record(root.study_id, root), (), LifecycleStatus.ACTIVE),),
        (node,), (node,), (), LifecycleStatus.ACTIVE)


def source_mapping_draft(source, dossier, *, parent,
                         draft_id='draft.rubisco-insilico-structure.observed-mapping'):
    science.validate_source(source, dossier)
    parent.__post_init__()
    matches = tuple(row for row in parent.products if row.record == c.identity(dossier)
                    and row.role is ContributionRole.INSTANCE_PRODUCT)
    if len(matches) != 1 or parent.scope != dossier.scope:
        raise ValueError('mapping parent substitutes the actual nomination OUTCOME or scope')
    product = matches[0]
    requirement, connection = requirement_pair(dossier.scope,
        ObjectIdentity.from_record(parent.contribution_id, parent), product.product_id)
    base = c.StructureOperationConfig('config.' + ANALYZE, 'analyze', source, dossier.scope,
        tuple(sorted((c.identity(source), c.identity(dossier)), key=lambda row: row.object_id)))
    registrations = {declaration.capability_key: declaration.registration() for declaration in operation_declarations()}
    operations, external, links = [], [], []
    for operation in ('analyze', 'assess'):
        node = c.NAMESPACE + '.' + operation
        config = replace(base, config_id='config.' + node, operation=operation)
        operations.append(RecursiveOperationSpec.from_config(node_id=node,
            selection=registrations[node].selection, config_id=config.config_id, config=config,
            obligation_ids=('obligation.' + node + '.exact-observed-source-census',), resource_budget=BUDGET))
        for name, record in (('source', source), ('nomination', dossier)):
            identity = c.identity(record)
            input_id = 'external.' + node + '.' + name
            role = 'OUTCOME' if name == 'nomination' else 'SOURCE'
            external.append(RecursiveExternalInput(input_id,
                product.artifact.artifact_id if name == 'nomination' else identity.object_id,
                identity.object_schema, MEDIA, None, OutcomeAccess.DEVELOPMENT_VISIBLE,
                VisibilityCeiling.DEVELOPMENT_ONLY, identity.object_fingerprint, role))
            connected = name == 'nomination' and node == ANALYZE
            links.append(RecursiveInputLink('edge.' + node + '.' + name, node, name,
                external_input_id=input_id, scientific_role=role,
                requirement_id=requirement.requirement_id if connected else None,
                connection_id=connection.connection_id if connected else None))
        if operation == 'assess':
            links.append(RecursiveInputLink('edge.' + node + '.inventory', node, 'inventory',
                producer_node_id=ANALYZE, producer_output_id='inventory', scientific_role='HISTORY'))
    root = development_root(base, study_id='study.' + draft_id)
    return RecursiveStudyDraft(draft_id, c.QUESTION, _campaign(root, draft_id), (requirement,),
        (connection,), (), tuple(sorted(operations, key=lambda row: row.node_id)),
        tuple(sorted(external, key=lambda row: row.input_id)), tuple(sorted(links, key=lambda row: row.edge_id)),
        (ANALYZE, ASSESS), development_study=root, contribution_parents=(parent,))


def _configs(draft):
    draft.__post_init__()
    if tuple(row.node_id for row in draft.operations) != (ANALYZE, ASSESS) or draft.selected_operation_ids != (ANALYZE, ASSESS):
        raise ValueError('observed mapping changes the exact two-operation census')
    registrations = {declaration.capability_key: declaration.registration() for declaration in operation_declarations()}
    values = {}
    for row in draft.operations:
        config = decode_canonical_bytes(row.config_payload.encode(), c.StructureOperationConfig, maximum_bytes=None)
        if row.config_id != config.config_id or row.node_id != c.NAMESPACE + '.' + config.operation or row.selection != registrations[row.node_id].selection:
            raise ValueError('observed mapping changes installed operation/config identities')
        values[row.node_id] = config
    base = values[ANALYZE]
    if (replace(base, operation='assess', config_id='config.' + ASSESS) != values[ASSESS]
            or draft.development_study != development_root(base, study_id=draft.development_study.study_id)
            or len(draft.requirements) != 1 or len(draft.connections) != 1):
        raise ValueError('observed mapping changes source, actual outcome scope or common root')
    validate_requirement_config(base, draft.requirements[0], draft.connections[0])
    return values, base


def _actual_outputs(draft, products):
    configs, config = _configs(draft)
    retained = {}
    for node, selected in configs.items():
        records = products['records'].get(node, {})
        if not records:
            retained[node] = None
            continue
        roster = operation_outputs(selected.operation)
        if set(records) != {node + '.' + name for name, _ in roster}:
            raise ValueError('observed mapping changes actual output denominator')
        receipt = products['receipts'][node]
        if receipt.operational_status is not OperationalStatus.SUCCEEDED:
            raise ValueError('observed mapping output lacks an actual successful receipt')
        for name, codec in roster:
            record = records[node + '.' + name]
            if type(record) is not codec:
                raise ValueError('observed mapping substitutes an actual output type')
            record.__post_init__()
            matches = tuple(row for row in receipt.output_logical_artifacts
                if row.payload_schema == record.SCHEMA and row.content_sha256 == record.fingerprint())
            if len(matches) != 1 or products['outputs'][matches[0].logical_artifact_id].logical != matches[0]:
                raise ValueError('observed mapping changes actual output materialization')
        retained[node] = records
    if retained[ASSESS] is not None:
        if retained[ANALYZE] is None:
            raise ValueError('assessed mapping omits the actual inventory')
        inventory = retained[ANALYZE][ANALYZE + '.inventory']
        coordinates = retained[ANALYZE][ANALYZE + '.coordinates']
        assessment = retained[ASSESS][ASSESS + '.assessment']
        if (inventory.source != c.identity(config.source) or inventory.nomination != config.source.nomination
                or coordinates.inventory != c.identity(inventory) or assessment.source != c.identity(config.source)
                or assessment.inventory != c.identity(inventory) or assessment.nomination != config.source.nomination
                or assessment.prior_nomination_scope != config.nomination_scope):
            raise ValueError('assessed mapping substitutes its source, inventory, coordinates or parent')
        validate_requirement_assessment(assessment, draft.requirements[0], draft.connections[0])
    return config, retained


def inquiry_endpoint_validator(draft, endpoint):
    _, config = _configs(draft)
    if endpoint != c.scope(config.source):
        raise ValueError('observed mapping inquiry changes its exact source/mapping scope')


def inquiry_outcome_projector(draft, specification, products):
    inquiry_endpoint_validator(draft, specification.endpoint)
    config, retained = _actual_outputs(draft, products)
    if specification.distinguishing_assessment != draft.operations[0].config_identity:
        raise ValueError('observed mapping inquiry changes its committed graph designation')
    if retained[ASSESS] is None:
        return 'unresolved'
    result = retained[ASSESS][ASSESS + '.assessment']
    return 'useful-supply' if result.source_disposition is AssessmentDisposition.SATISFIED else 'unresolved'


def inquiry_evidence_projector(draft, payloads, products=None):
    configs, config = _configs(draft)
    external = {row.input_id: row for row in draft.external_inputs}
    bindings, actual = [], {}
    for node in configs:
        for name, codec in (('source', c.StructuralSource), ('nomination', NominationDossier)):
            input_id = 'external.' + node + '.' + name
            item = external[input_id]
            record = decode_canonical_bytes(payloads['external-' + sha256(input_id.encode()).hexdigest()[:24] + '.json'], codec, maximum_bytes=None)
            expected = c.identity(config.source) if name == 'source' else config.source.nomination
            role = 'SOURCE' if name == 'source' else 'OUTCOME'
            if (c.identity(record) != expected or record.fingerprint() != item.expected_content_sha256
                    or item.scientific_role != role or (name in actual and record != actual[name])):
                raise ValueError('observed mapping evidence changes actual source/outcome bytes or role')
            actual[name] = record
            bindings.append(InquiryEvidenceBinding(input_id, record.fingerprint(),
                c.scope(config.source) if name == 'source' else record.scope,
                ContributionRole.RETAINED_ANALYSIS_INPUT if name == 'source' else ContributionRole.INSTANCE_PRODUCT,
                (), draft.development_study.numerical_view_ids))
    science.validate_source(actual['source'], actual['nomination'])
    if products is not None:
        _, retained = _actual_outputs(draft, products)
        if retained[ANALYZE] is not None:
            inventory = retained[ANALYZE][ANALYZE + '.inventory']
            from .independent_assessment import validate_observed_inventory, validate_coordinate_export

            reconstructed_inventory, _, _, _ = validate_observed_inventory(actual['source'], actual['nomination'], inventory)
            # Canonical inventory bytes preserve Decimal values, not source token
            # exponents. Reconstruct export spelling from the original source;
            # the independent parser supplies every atom, without producer
            # replay. The existing export formatter supplies only its exact
            # historical text layout; independently check columns/metadata too.
            if retained[ANALYZE][ANALYZE + '.coordinates'] != science.assembly_coordinates(actual['source'], reconstructed_inventory):
                raise ValueError('actual coordinate export changes independently reconstructed assembly')
            validate_coordinate_export(actual['source'], reconstructed_inventory, retained[ANALYZE][ANALYZE + '.coordinates'])
            if retained[ASSESS] is not None and retained[ASSESS][ASSESS + '.assessment'] != science.assess(actual['source'], actual['nomination'], inventory):
                raise ValueError('actual structural assessment fails independent reconstruction')
        for records in retained.values():
            for output_id, record in ({} if records is None else records).items():
                bindings.append(InquiryEvidenceBinding(output_id, record.fingerprint(), c.scope(config.source),
                    ContributionRole.RETAINED_ANALYSIS_INPUT, (), draft.development_study.numerical_view_ids))
    return tuple(sorted(bindings, key=lambda row: row.binding_id))


def describe_contributions(draft, products):
    config, retained = _actual_outputs(draft, products)
    if retained[ASSESS] is None:
        return ()
    exported = []
    for node, records in retained.items():
        receipt = products['receipts'][node]
        for output_id, record in records.items():
            logical = next(row for row in receipt.output_logical_artifacts
                if row.payload_schema == record.SCHEMA and row.content_sha256 == record.fingerprint())
            artifact = products['outputs'][logical.logical_artifact_id]
            exported.append(ContributionProduct('product.' + output_id, c.identity(record),
                ArtifactIdentity(logical.logical_artifact_id, 'scientific-product', record.SCHEMA,
                    record.fingerprint(), MEDIA, artifact.materialization.size_bytes),
                ObjectIdentity.from_record(receipt.receipt_id, receipt), ContributionRole.RETAINED_ANALYSIS_INPUT,
                EvidenceCeiling.NON_PROMOTABLE, logical.outcome_access, logical.visibility_ceiling))
    return (ContributionManifest('contribution.' + draft.draft_id, c.QUESTION,
        'Observed source-mapping substep: complete authentic biological assemblies, residue/atom denominators and source-bound coordinates. Mutant comparison remains pending and kinetics unmeasured.',
        c.scope(config.source), tuple(sorted(exported, key=lambda row: row.product_id)),
        tuple(sorted((c.identity(record) for records in retained.values() for record in records.values()),
                     key=lambda row: row.object_id)), (),
        tuple(ObjectIdentity.from_record(parent.contribution_id, parent) for parent in draft.contribution_parents)),)


def next_wave_builder(draft, manifest, products):
    if describe_contributions(draft, products) != (manifest,):
        raise ValueError('observed mapping successor changes actual source-bound products')
    return None
