# SPDX-License-Identifier: MPL-2.0
"""Retained six-question contributions below the unchanged conditional root."""

from hashlib import sha256

from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_inquiry_policy import ScientificInquiryWork
from empirical_lawhood.science.inquiry.recursive_requirements import ContributionRole
from empirical_lawhood.science.identity.references import ArtifactIdentity
from empirical_lawhood.science.inquiry.scientific_contributions import ContributionManifest, ContributionProduct
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.execution.recursive_inquiry import InquiryEvidenceBinding
from empirical_lawhood.execution.recursive_provider import RecursiveInquiryHooks
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_analysis_operation import ACTION_SCHEMA, capability_for, assessment_type, input_selections, external_id
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_analysis_translation import selected_config, selection_scope
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_assessment_records import require_response_assessment
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_design import response_scope


def endpoint_validator(draft, endpoint):
    if endpoint != response_scope(selected_config(draft).analysis.design):
        raise ValueError('response assessment changes its original local scientific scope')


def record_identity(record):
    require_response_assessment(record)
    return record.identity


def actual_products(draft, products):
    config = selected_config(draft)
    capability = capability_for(config)
    records = products['records'].get(capability, {})
    if not records:
        return ()
    if set(records) != {capability + '.assessment'}:
        raise ValueError('response assessment changes its complete canonical output census')
    assessment = records[capability + '.assessment']
    if (type(assessment) is not assessment_type(config) or assessment.design != config.analysis.design
            or assessment.assessor_source != config.assessor_source
            or assessment.assessment_id != capability + '.assessment.' + config.analysis.fingerprint()):
        raise ValueError('response assessment substitutes its original scientific design or assessor')
    receipt = products['receipts'].get(capability)
    if receipt is None or receipt.task_id != capability or receipt.operational_status is not OperationalStatus.SUCCEEDED:
        raise ValueError('response assessment lacks its original successful publication receipt')
    logicals = [r for r in receipt.output_logical_artifacts if r.payload_schema == assessment.SCHEMA
        and r.content_sha256 == assessment.fingerprint()]
    if len(logicals) != 1 or len(receipt.output_logical_artifacts) != 2:
        raise ValueError('response assessment loses its original assessment/action publication')
    arrays = [r for r in receipt.output_logical_artifacts if r.payload_schema == ACTION_SCHEMA]
    if len(arrays) != 1:
        raise ValueError('response assessment loses its complete original action array output')
    array = products['outputs'].get(arrays[0].logical_artifact_id)
    if (array is None or array.logical != arrays[0] or array.materialization not in receipt.output_materializations
            or array.materialization.physical_sha256 != array.logical.content_sha256):
        raise ValueError('response assessment changes its original complete action array custody')
    logical, = logicals
    artifact = products['outputs'].get(logical.logical_artifact_id)
    if (artifact is None or artifact.logical != logical or artifact.materialization not in receipt.output_materializations
            or artifact.materialization.size_bytes != assessment.canonical_size_bytes()
            or artifact.materialization.physical_sha256 != assessment.fingerprint()):
        raise ValueError('response assessment substitutes complete original output bytes')
    return ((capability, 'assessment', assessment, receipt, artifact),)


def describe_contributions(draft, authenticated_products):
    rows = actual_products(draft, authenticated_products)
    if not rows:
        return ()
    _, _, assessment, receipt, artifact = rows[0]
    config = selected_config(draft)
    capability = capability_for(config)
    product = ContributionProduct('product.' + capability + '.assessment', assessment.identity,
        ArtifactIdentity(artifact.logical.logical_artifact_id, 'original-six-question-assessment', assessment.SCHEMA,
            assessment.fingerprint(), 'application/json', artifact.materialization.size_bytes),
        ObjectIdentity.from_record(receipt.receipt_id, receipt), ContributionRole.RETAINED_ANALYSIS_INPUT,
        EvidenceCeiling.NON_PROMOTABLE, OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY)
    remaining = {r.requirement_id: r for p in config.analysis.parents for r in p.remaining_requirements}
    return (ContributionManifest('contribution.response-assessment.' + draft.fingerprint(), draft.question,
        'Independent original six-question assessment, including adverse or unavailable outcomes and the next supplier requirement. '
        'Complete action arrays remain in the original receipt-bound custody. No population, mean or kinetic admission follows.',
        response_scope(assessment.design), (product,), (assessment.identity,),
        tuple(remaining[k] for k in sorted(remaining)),
        tuple(ObjectIdentity.from_record(p.contribution_id, p) for p in config.analysis.parents)),)


def outcome_projector(draft, specification, products):
    config = selected_config(draft)
    endpoint_validator(draft, specification.endpoint)
    if specification.distinguishing_assessment != config.identity:
        raise ValueError('response inquiry changes its original non-native assessor')
    rows = actual_products(draft, products)
    if not rows:
        return 'unresolved'
    assessment = rows[0][2]
    return 'supported' if all(q.assessable_comparisons == q.assigned_comparisons
        for q in assessment.questions) else 'unresolved'


def evidence_projector(draft, payloads, products=None):
    config = selected_config(draft)
    scope = response_scope(config.analysis.design)
    views = draft.development_study.numerical_view_ids
    bindings = []
    for name, pin, media, _, _, record in input_selections(config):
        key = external_id(config, name)
        suffix = '.json' if media == 'application/json' else '.gz' if media == 'application/gzip' else '.bin'
        raw = payloads['external-' + sha256(key.encode()).hexdigest()[:24] + suffix]
        if sha256(raw).hexdigest() != pin.object_fingerprint:
            raise ValueError('response assessment substitutes original direct input bytes')
        parent = None if record is None else config.analysis.product(record)[0]
        bindings.append(InquiryEvidenceBinding(key, pin.object_fingerprint, scope if parent is None else parent.scope,
            ContributionRole.DESIGN_OPERAND if parent is None else ContributionRole.RETAINED_ANALYSIS_INPUT,
            (), views if parent is None else ()))
    if products is not None:
        for task, name, record, receipt, _ in actual_products(draft, products):
            bindings.append(InquiryEvidenceBinding(task + '.' + name, record.fingerprint(), scope,
                ContributionRole.INSTANCE_PRODUCT, (), views))
            arrays, = [r for r in receipt.output_logical_artifacts if r.payload_schema == ACTION_SCHEMA]
            bindings.append(InquiryEvidenceBinding(task + '.actions', arrays.content_sha256, scope,
                ContributionRole.INSTANCE_PRODUCT, (), views))
    return tuple(sorted(bindings, key=lambda row: row.binding_id))


def scientific_work(draft, operation_id):
    from empirical_lawhood.methods.compact_inquiry_policy import CompactScientificMethod
    config = selected_config(draft)
    capability = capability_for(config)
    if operation_id != capability:
        raise ValueError('response assessment work changes its original operation')
    operation, = draft.operations
    scope = response_scope(config.analysis.design)
    operands = tuple(sorted({config.analysis.identity, *(r[1] for r in input_selections(config))}, key=lambda p: p.object_id))
    method = CompactScientificMethod('rubisco-response-assessment', 'assess', operation.selection.capability_key,
        operation.selection.capability_version, operation.selection.implementation_sha256,
        config.analysis.identity, config.analysis.design.identity, operands, scope,
        assessment_type(config).SCHEMA, assessment_type(config).VERSION)
    return ScientificInquiryWork(ObjectIdentity.from_record('method.rubisco.response-assessment', method), operands, scope,
        ObjectIdentity.from_record('observation.rubisco.response-assessment', method))


def inquiry_hooks():
    return RecursiveInquiryHooks(contribution_describer=describe_contributions, inquiry_endpoint_validator=endpoint_validator,
        inquiry_evidence_projector=evidence_projector, inquiry_outcome_projector=outcome_projector,
        inquiry_record_identity=record_identity, inquiry_work_projector=scientific_work,
        inquiry_selection_scope=selection_scope)
