# SPDX-License-Identifier: MPL-2.0
"""Receipt-bound contributions and exact target-claim projections for the root."""

from hashlib import sha256

from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_claim_assessment import InquiryClaimAssessment
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition as A, ContributionRole
from empirical_lawhood.science.identity.references import ArtifactIdentity
from empirical_lawhood.science.inquiry.scientific_contributions import ContributionManifest, ContributionProduct
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.execution.recursive_inquiry import InquiryEvidenceBinding
from empirical_lawhood.domains.rubisco.rubisco_response.initial_root import calculate_initial_root
from empirical_lawhood.domains.rubisco.rubisco_response.initial_root_records import InitialRootAnalysisInputs, InitialRootScopedAssessment, InitialRootScopedResult
from empirical_lawhood.domains.rubisco.rubisco_response.initial_root_requirements import ASSESS, CALCULATE, USE, analysis_arguments, initial_root_requirement_graph, initial_root_scope, nested_views, reconstruct_assessment
from empirical_lawhood.domains.rubisco.rubisco_response.initial_root_operation import MAX_INPUT_BYTES, MEDIA
from empirical_lawhood.domains.rubisco.rubisco_response.initial_root_translation import ANALYSIS_INPUT, initial_root_draft, selected_configs


def record_identity(record):
    if type(record) not in (InitialRootAnalysisInputs, InitialRootScopedResult, InitialRootScopedAssessment):
        raise TypeError('initial root inquiry cannot interpret an unrelated scientific record')
    return record.identity


def _actual_product(products, task, kind):
    outputs = products['records'].get(task, {})
    if not outputs:
        return None
    if len(outputs) != 1 or tuple(outputs) != (task + '.product',) or type(outputs[task + '.product']) is not kind:
        raise ValueError('initial root inquiry changes its exact complete scientific output')
    record = outputs[task + '.product']
    receipt = products['receipts'].get(task)
    if receipt is None or receipt.task_id != task or receipt.operational_status is not OperationalStatus.SUCCEEDED:
        raise ValueError('initial root inquiry product lacks its actual successful receipt')
    logicals = tuple(row for row in receipt.output_logical_artifacts
        if row.payload_schema == record.SCHEMA and row.content_sha256 == record.fingerprint())
    if len(logicals) != 1:
        raise ValueError('initial root inquiry loses the original receipt-to-product join')
    logical, = logicals
    artifact = products['outputs'].get(logical.logical_artifact_id)
    if (artifact is None or artifact.logical != logical or artifact.materialization not in receipt.output_materializations
            or artifact.materialization.size_bytes != len(record.canonical_bytes())
            or artifact.materialization.physical_sha256 != record.fingerprint() or artifact.materialization.compression != 'none'):
        raise ValueError('initial root inquiry changes its actual original output bytes')
    return record, receipt, artifact


def actual_assessment(draft, products):
    configs = selected_configs(draft)
    config = configs.get('use', configs.get('assess'))
    expected = calculate_initial_root(**analysis_arguments(config.analysis))
    scoped = InitialRootScopedResult(config.analysis.identity, initial_root_scope(config.analysis), expected)
    if config.parent is None:
        supplied = _actual_product(products, CALCULATE, InitialRootScopedResult)
        if supplied is not None and supplied[0] != scoped:
            raise ValueError('initial root product differs from its complete frozen-input reconstruction')
        assessment = _actual_product(products, ASSESS, InitialRootScopedAssessment)
        if assessment is not None and supplied is None:
            raise ValueError('initial root assessment omits its actual producing calculation')
    else:
        source = tuple(row for row in config.parent.products if row.record == scoped.identity)
        if len(source) != 1:
            raise ValueError('initial root reuse substitutes the original contribution result')
        supplied = None
        assessment = _actual_product(products, USE, InitialRootScopedAssessment)
    if assessment is not None:
        if assessment[0].analysis != scoped.analysis or assessment[0].scope != scoped.scope:
            raise ValueError('initial root changes the independently assessed exact recursive scope')
        reconstruct_assessment(config.analysis, expected, assessment[0].assessment)
    return config, expected, supplied, assessment


def _product(row, task):
    record, receipt, artifact = row
    return ContributionProduct('product.' + task, record.identity,
        ArtifactIdentity(artifact.logical.logical_artifact_id, 'conditional-root-analysis', record.SCHEMA,
            record.fingerprint(), MEDIA, artifact.materialization.size_bytes), ObjectIdentity.from_record(receipt.receipt_id, receipt),
        ContributionRole.RETAINED_ANALYSIS_INPUT, EvidenceCeiling.NON_PROMOTABLE,
        OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY)


def describe_contributions(draft, authenticated_products):
    config, result, supplied, assessed = actual_assessment(draft, authenticated_products)
    if assessed is None:
        return ()
    graph = initial_root_requirement_graph(config.analysis, result=result, parent=config.parent)
    products = ((_product(supplied, CALCULATE), _product(assessed, ASSESS)) if config.parent is None else
        (_product(assessed, USE),))
    remaining = tuple(row for row in graph.requirements if row.requirement_id in result.decision_requirement_ids)
    return (ContributionManifest('contribution.rubisco-initial-root.' + draft.fingerprint(), draft.question,
        'Conditional joint result ' + result.joint_outcome + '; original exposure, missing physical inputs and zero new native work retained.',
        initial_root_scope(config.analysis), tuple(sorted(products, key=lambda row: row.product_id)),
        (assessed[0].identity,), remaining,
        () if config.parent is None else (ObjectIdentity.from_record(config.parent.contribution_id, config.parent),)),)


def next_wave_builder(draft, manifest, authenticated_products):
    if describe_contributions(draft, authenticated_products) != (manifest,):
        raise ValueError('initial root successor changes the actual receipt-bound contribution')
    config, result, _, assessment = actual_assessment(draft, authenticated_products)
    if config.parent is not None or assessment is None or assessment[0].numerical_disposition is not A.SATISFIED or result.joint_outcome != 'SUPPORTED':
        return None
    return initial_root_draft(config.analysis, parent=manifest)


def endpoint_validator(draft, endpoint):
    config = next(iter(selected_configs(draft).values()))
    if endpoint != initial_root_scope(config.analysis):
        raise ValueError('initial root inquiry changes its exact original source, receiver or conditional scope')


def outcome_projector(draft, specification, products):
    endpoint_validator(draft, specification.endpoint)
    config, result, _, assessed = actual_assessment(draft, products)
    operation = next(row for row in draft.operations if row.node_id == (ASSESS if config.parent is None else USE))
    if specification.distinguishing_assessment != operation.config_identity:
        raise ValueError('initial root inquiry substitutes its actual independent assessor')
    if assessed is None:
        return 'unresolved'
    if assessed[0].numerical_disposition is not A.SATISFIED:
        return 'numerical-failure'
    return {'SUPPORTED': 'supported', 'CONTRADICTED': 'contradicted', 'UNRESOLVED': 'unresolved'}[result.joint_outcome]


def claim_assessment_projector(draft, specification, products):
    """Recompute the exact conditional claim; computational success is separate."""
    endpoint_validator(draft, specification.endpoint)
    target = getattr(specification, 'target', None)
    claims = tuple(row for row in draft.development_study.claims
        if target is not None and ObjectIdentity.from_record(row.claim_id, row) in target.required_claims)
    if not claims:
        return ()
    config, result, _, assessed = actual_assessment(draft, products)
    if assessed is None:
        return ()
    assessment, receipt, _ = assessed
    operation = next(row for row in draft.operations if row.node_id == (ASSESS if config.parent is None else USE))
    if specification.distinguishing_assessment != operation.config_identity or target.scope != initial_root_scope(config.analysis):
        raise ValueError('initial root target claim changes its selected independent assessment or scope')
    disposition = A.UNEVALUABLE if assessment.numerical_disposition is not A.SATISFIED else {
        'SUPPORTED': A.SATISFIED, 'CONTRADICTED': A.FALSIFIED, 'UNRESOLVED': A.UNEVALUABLE}[result.joint_outcome]
    return tuple(InquiryClaimAssessment(claim, operation.config_identity, assessment.identity,
        ObjectIdentity.from_record(receipt.receipt_id, receipt), initial_root_scope(config.analysis), disposition,
        (assessment.identity,), (), nested_views(config.analysis), EvidenceCeiling.NON_PROMOTABLE,
        OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY) for claim in claims)


def evidence_projector(draft, payloads, products=None):
    configs = selected_configs(draft)
    config = next(iter(configs.values()))
    kinds = {kind.SCHEMA: kind for kind in (InitialRootAnalysisInputs, InitialRootScopedResult, InitialRootScopedAssessment)}
    bindings = []
    scope = initial_root_scope(config.analysis)
    for external in draft.external_inputs:
        path = 'external-' + sha256(external.input_id.encode()).hexdigest()[:24] + '.json'
        record = decode_canonical_bytes(payloads[path], kinds[external.payload_schema], maximum_bytes=MAX_INPUT_BYTES)
        if record.fingerprint() != external.expected_content_sha256:
            raise ValueError('initial root evidence substitutes its frozen exact input bytes')
        if external.input_id == ANALYSIS_INPUT:
            if record != config.analysis or external.scientific_role != 'SOURCE':
                raise ValueError('initial root evidence changes its complete source/consumer analysis')
        elif config.parent is None or not any(row.record == record.identity for row in config.parent.products):
            raise ValueError('initial root evidence changes an original retained contribution input')
        bindings.append(InquiryEvidenceBinding(external.input_id, record.fingerprint(), scope,
            ContributionRole.RETAINED_ANALYSIS_INPUT, (), nested_views(config.analysis)))
    if products is not None:
        actual_assessment(draft, products)
        for task, records in products['records'].items():
            if task not in draft.selected_operation_ids:
                raise ValueError('initial root evidence adds an unrelated operation product')
            for output, record in records.items():
                if type(record) not in (InitialRootScopedResult, InitialRootScopedAssessment) or output != task + '.product':
                    raise ValueError('initial root evidence changes its complete typed product roster')
                bindings.append(InquiryEvidenceBinding(output, record.fingerprint(), scope,
                    ContributionRole.INSTANCE_PRODUCT, (), nested_views(config.analysis)))
    return tuple(sorted(bindings, key=lambda row: row.binding_id))
