# SPDX-License-Identifier: MPL-2.0
"""Original local-admission receipts and scientific work for shared inquiry."""

from hashlib import sha256

from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_inquiry_policy import ScientificInquiryWork
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition as A, ContributionRole
from empirical_lawhood.science.identity.references import ArtifactIdentity
from empirical_lawhood.science.inquiry.scientific_contributions import ContributionManifest, ContributionProduct
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.execution.recursive_inquiry import InquiryEvidenceBinding
from empirical_lawhood.execution.recursive_provider import RecursiveInquiryHooks
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_supply import CAPABILITY, PreparationSupplyResult, assess_supply, external_id
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_supply_translation import selected_configs, selection_scope


def endpoint_validator(draft, endpoint):
    config, = selected_configs(draft)
    if endpoint != config.selection.scope:
        raise ValueError('local admission changes its exact original destination scope')


def record_identity(record):
    if type(record) is not PreparationSupplyResult:
        raise TypeError('local admission requires its original independently assessed result')
    return record.identity


def actual_products(draft, products):
    config, = selected_configs(draft)
    records = products['records'].get(CAPABILITY, {})
    if not records:
        return ()
    if set(records) != {CAPABILITY + '.assessment'}:
        raise ValueError('local admission changes its original assessment census')
    record = records[CAPABILITY + '.assessment']
    if type(record) is not PreparationSupplyResult or record != assess_supply(config.selection):
        raise ValueError('local admission disagrees with its original destination reconstruction')
    receipt = products['receipts'].get(CAPABILITY)
    if (receipt is None or receipt.task_id != CAPABILITY or receipt.operational_status is not OperationalStatus.SUCCEEDED
            or len(receipt.output_logical_artifacts) != 1):
        raise ValueError('local admission lacks its original complete successful publication')
    logical, = receipt.output_logical_artifacts
    artifact = products['outputs'].get(logical.logical_artifact_id)
    if (logical.payload_schema != record.SCHEMA or logical.content_sha256 != record.fingerprint()
            or artifact is None or artifact.logical != logical or artifact.materialization not in receipt.output_materializations
            or artifact.materialization.physical_sha256 != record.fingerprint()
            or artifact.materialization.size_bytes != record.canonical_size_bytes()):
        raise ValueError('local admission substitutes its complete original receipt-bound bytes')
    return ((CAPABILITY, 'assessment', record, receipt, artifact),)


def describe_contributions(draft, authenticated_products):
    rows = actual_products(draft, authenticated_products)
    if not rows:
        return ()
    _, _, result, receipt, artifact = rows[0]
    product = ContributionProduct('product.' + CAPABILITY + '.assessment', result.identity,
        ArtifactIdentity(artifact.logical.logical_artifact_id, 'original-local-destination-assessment', result.SCHEMA,
            result.fingerprint(), 'application/json', artifact.materialization.size_bytes),
        ObjectIdentity.from_record(receipt.receipt_id, receipt), ContributionRole.RETAINED_ANALYSIS_INPUT,
        EvidenceCeiling.NON_PROMOTABLE, OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY)
    remaining = {r.requirement_id: r for parent in result.selection.parents for r in parent.remaining_requirements}
    return (ContributionManifest('contribution.preparation-supply.' + draft.fingerprint(), draft.question,
        'Original local destination supply and outcome-dependent next requirement. A complete adverse finding is not favorable physics. '
        'Wider physical, population and kinetic requirements remain open.', result.selection.scope, (product,), (result.identity,),
        tuple(remaining[key] for key in sorted(remaining)),
        tuple(ObjectIdentity.from_record(p.contribution_id, p) for p in result.selection.parents)),)


def outcome_projector(draft, specification, products):
    endpoint_validator(draft, specification.endpoint)
    config, = selected_configs(draft)
    if specification.distinguishing_assessment != config.identity:
        raise ValueError('local admission changes its actual assessment contract')
    rows = actual_products(draft, products)
    if not rows:
        return 'unresolved'
    result = rows[0][2]
    dispositions = [a for _, a in result.checkpoint_dispositions]
    if result.response_disposition is not None:
        dispositions.append(result.response_disposition)
    return 'supported' if all(a is A.SATISFIED for a in dispositions) else 'contradicted' if A.FALSIFIED in dispositions else 'unresolved'


def evidence_projector(draft, payloads, products=None):
    config, = selected_configs(draft)
    rows = []
    for record in config.selection.records:
        key = external_id(record)
        if payloads['external-' + sha256(key.encode()).hexdigest()[:24] + '.json'] != record.canonical_bytes():
            raise ValueError('local admission substitutes actual contribution input bytes')
        parent, product = config.selection.product(record)
        rows.append(InquiryEvidenceBinding(key, record.fingerprint(), parent.scope, product.role, (), ()))
    if products is not None:
        for task, name, record, _, _ in actual_products(draft, products):
            rows.append(InquiryEvidenceBinding(task + '.' + name, record.fingerprint(), config.selection.scope,
                ContributionRole.INSTANCE_PRODUCT, (), draft.development_study.numerical_view_ids))
    return tuple(sorted(rows, key=lambda r: r.binding_id))


def scientific_work(draft, operation_id):
    from empirical_lawhood.methods.compact_inquiry_policy import CompactScientificMethod
    config, = selected_configs(draft)
    if operation_id != CAPABILITY:
        raise ValueError('local admission changes its selected scientific work')
    operation, = draft.operations
    operands = tuple(sorted((config.selection.design.identity, *(r.identity for r in config.selection.records)), key=lambda p: p.object_id))
    method = CompactScientificMethod('rubisco-preparation-supply', 'admit', operation.selection.capability_key,
        operation.selection.capability_version, operation.selection.implementation_sha256,
        config.selection.identity, config.selection.design.identity, operands, config.selection.scope,
        PreparationSupplyResult.SCHEMA, PreparationSupplyResult.VERSION)
    return ScientificInquiryWork(ObjectIdentity.from_record('method.rubisco.preparation-supply', method), operands,
        config.selection.scope, ObjectIdentity.from_record('observation.rubisco.preparation-supply', method))


def inquiry_hooks():
    return RecursiveInquiryHooks(contribution_describer=describe_contributions, inquiry_endpoint_validator=endpoint_validator,
        inquiry_evidence_projector=evidence_projector, inquiry_outcome_projector=outcome_projector,
        inquiry_record_identity=record_identity, inquiry_work_projector=scientific_work,
        inquiry_selection_scope=selection_scope)
