# SPDX-License-Identifier: MPL-2.0
"""Original response contributions and exact ordinary inquiry work identities."""

from hashlib import sha256

from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_inquiry_policy import ScientificInquiryWork
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition, ContributionRole
from empirical_lawhood.science.identity.references import ArtifactIdentity
from empirical_lawhood.science.inquiry.scientific_contributions import ContributionManifest, ContributionProduct
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.execution.recursive_inquiry import InquiryEvidenceBinding
from empirical_lawhood.execution.recursive_provider import RecursiveInquiryHooks
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_operation import PeriodicProbeResult
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_design import response_scope
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_operation import node_id
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_read import PreparationResponsePointReadout
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_translation import contribution_parents, selected_configs, selection_scope


def endpoint_projector(draft):
    return response_scope(selected_configs(draft)[0].protocol)


def endpoint_validator(draft, endpoint):
    if endpoint != endpoint_projector(draft):
        raise ValueError('response inquiry changes the original local receiver, construction or uncertainty scope')


def record_identity(record):
    if type(record) is PeriodicProbeResult:
        return ObjectIdentity.from_record(record.result_id, record)
    if type(record) is PreparationResponsePointReadout:
        return record.identity
    raise TypeError('response inquiry requires its original force result or independent point readout')


def actual_products(draft, products):
    rows = []
    configs = selected_configs(draft)
    for config in configs:
        task = node_id(config)
        records = products['records'].get(task, {})
        if not records:
            continue
        if set(records) != {task + '.product', task + '.assessment'}:
            raise ValueError('response inquiry omits an original result or independent point assessment')
        result, assessed = records[task + '.product'], records[task + '.assessment']
        if (type(result) is not PeriodicProbeResult or type(assessed) is not PreparationResponsePointReadout
                or result.returned.selection != config.point.identity or assessed.configuration != config.identity
                or assessed.point != config.point or assessed.original.original_result != result):
            raise ValueError('response inquiry substitutes its original selected molecular return')
        receipt = products['receipts'].get(task)
        if receipt is None or receipt.task_id != task or receipt.operational_status is not OperationalStatus.SUCCEEDED:
            raise ValueError('response scientific output lacks its completed publishing receipt')
        for name, record in (('product', result), ('assessment', assessed)):
            logicals = [r for r in receipt.output_logical_artifacts
                if r.payload_schema == record.SCHEMA and r.content_sha256 == record.fingerprint()]
            if len(logicals) != 1:
                raise ValueError('response output lacks a unique original receipt binding')
            logical, = logicals
            artifact = products['outputs'].get(logical.logical_artifact_id)
            if (artifact is None or artifact.logical != logical or artifact.materialization not in receipt.output_materializations
                    or artifact.materialization.size_bytes != record.canonical_size_bytes()
                    or artifact.materialization.physical_sha256 != record.fingerprint()):
                raise ValueError('response inquiry substitutes complete original output bytes')
            rows.append((task, name, record, receipt, artifact))
    return tuple(rows)


def describe_contributions(draft, authenticated_products):
    configs = selected_configs(draft)
    rows = actual_products(draft, authenticated_products)
    if len(rows) != 2 * len(configs):
        return ()
    products, assessments = [], []
    for task, name, record, receipt, artifact in rows:
        products.append(ContributionProduct('product.' + task + '.' + name, record_identity(record),
            ArtifactIdentity(artifact.logical.logical_artifact_id, 'original-response-' + name, record.SCHEMA,
                record.fingerprint(), 'application/json', artifact.materialization.size_bytes),
            ObjectIdentity.from_record(receipt.receipt_id, receipt), ContributionRole.RETAINED_ANALYSIS_INPUT,
            EvidenceCeiling.NON_PROMOTABLE, OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY))
        if name == 'assessment':
            assessments.append(record.identity)
    parent = configs[0].preparation_parent
    return (ContributionManifest('contribution.preparation-response.' + draft.fingerprint(), draft.question,
        'Complete original selected stage including failed returns; independent six-question reconstruction remains scoped '
        'to one matched construction, with unavailable force enclosure, population and kinetic contrasts.',
        response_scope(configs[0].protocol), tuple(sorted(products, key=lambda p: p.product_id)),
        tuple(sorted(assessments, key=lambda p: p.object_id)), () if parent is None else parent.remaining_requirements,
        tuple(ObjectIdentity.from_record(p.contribution_id, p) for p in contribution_parents(configs[0]))),)


def outcome_projector(draft, specification, products):
    configs = selected_configs(draft)
    endpoint_validator(draft, specification.endpoint)
    if specification.distinguishing_assessment not in {c.identity for c in configs}:
        raise ValueError('response inquiry substitutes its selected original point assessor')
    rows = actual_products(draft, products)
    if len(rows) != 2 * len(configs):
        return 'unresolved'
    reports = [record for _, name, record, _, _ in rows if name == 'assessment']
    if any(r.numerical_findings or r.original.original_result.returned.error is not None
           or r.original.geometry_quality.disposition != 'SCREEN_PASSED'
           or r.original.numerical_integrity is None
           or r.original.numerical_integrity.disposition is not AssessmentDisposition.SATISFIED for r in reports):
        return 'unresolved'
    return 'supported'  # Complete point supply; the six-question reader owns response conclusions.


def evidence_projector(draft, payloads, products=None):
    configs = selected_configs(draft)
    scope = response_scope(configs[0].protocol)
    views = draft.development_study.numerical_view_ids
    bindings = []
    for external in draft.external_inputs:
        suffix = '.bin' if external.media_type == 'application/octet-stream' else '.json'
        path = 'external-' + sha256(external.input_id.encode()).hexdigest()[:24] + suffix
        if sha256(payloads[path]).hexdigest() != external.expected_content_sha256:
            raise ValueError('response inquiry substitutes exact original direct input bytes')
        historical = external.scientific_role == 'HISTORY'
        parent = next((p for p in contribution_parents(configs[0]) if any(
            r.artifact.artifact_id == external.logical_artifact_id for r in p.products)), None) if historical else None
        bindings.append(InquiryEvidenceBinding(external.input_id, external.expected_content_sha256,
            parent.scope if historical else scope,
            ContributionRole.RETAINED_ANALYSIS_INPUT if historical else ContributionRole.DESIGN_OPERAND, (),
            () if historical else views))
    if products is not None:
        for task, name, record, _, _ in actual_products(draft, products):
            bindings.append(InquiryEvidenceBinding(task + '.' + name, record.fingerprint(), scope,
                ContributionRole.INSTANCE_PRODUCT, (), views))
    return tuple(sorted(bindings, key=lambda row: row.binding_id))


def scientific_work(draft, operation_id):
    configs = selected_configs(draft)
    config = next((c for c in configs if node_id(c) == operation_id), None)
    if config is None:
        raise ValueError('response work is outside the complete originally selected stage')
    return _scientific_work(draft, operation_id, config)


def scientific_work_batch(draft, operation_ids):
    configs = {node_id(config): config for config in selected_configs(draft)}
    if (type(operation_ids) is not tuple or operation_ids != tuple(sorted(set(operation_ids)))
            or not set(operation_ids).issubset(configs)):
        raise ValueError('response work batch changes its originally selected task census')
    return tuple((operation_id, _scientific_work(draft, operation_id, configs[operation_id]))
        for operation_id in operation_ids)


def _scientific_work(draft, operation_id, config):
    from empirical_lawhood.methods.compact_inquiry_policy import CompactScientificMethod
    operation = next(row for row in draft.operations if row.node_id == operation_id)
    operands = tuple(sorted({config.original.selection.identity, config.original.raw_sources,
        config.protocol.identity, config.center.center_bytes, config.frame.identity, config.point.identity}, key=lambda p: p.object_id))
    scope = response_scope(config.protocol)
    method = CompactScientificMethod('rubisco-preparation-response', 'acquire', operation.selection.capability_key,
        operation.selection.capability_version, operation.selection.implementation_sha256,
        config.original.selection.identity, config.protocol.identity, operands, scope,
        PreparationResponsePointReadout.SCHEMA, PreparationResponsePointReadout.VERSION)
    return ScientificInquiryWork(ObjectIdentity.from_record('method.rubisco.preparation-response', method), operands, scope,
        ObjectIdentity.from_record('observation.rubisco.preparation-response', method))


def inquiry_hooks():
    return RecursiveInquiryHooks(contribution_describer=describe_contributions, inquiry_endpoint_validator=endpoint_validator,
        inquiry_evidence_projector=evidence_projector, inquiry_outcome_projector=outcome_projector,
        inquiry_record_identity=record_identity, inquiry_work_projector=scientific_work,
        inquiry_work_batch_projector=scientific_work_batch, inquiry_endpoint_projector=endpoint_projector,
        inquiry_selection_scope=selection_scope)
