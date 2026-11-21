# SPDX-License-Identifier: MPL-2.0
"""SCI02-C scoped findings and local stops for the generic recursive inquiry."""
from dataclasses import dataclass
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_claim_assessment import InquiryClaimAssessment
from empirical_lawhood.science.inquiry.recursive_inquiry_policy import ScientificInquiryWork
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition, ContributionRole, ScientificConditionScope
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.execution.recursive_inquiry import InquiryEvidenceBinding

from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02c_records import Sci02CConfig, Sci02CDesign, Sci02CProduct


@dataclass(frozen=True, slots=True)
class WorkMethod(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-sci02c/work-method'
    phase: str
    study: Sci02CDesign
    implementation_sha256: str


def wave(draft):
    from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02c_bindings as binding
    operations = tuple(op for op in draft.operations if op.node_id in draft.selected_operation_ids)
    configs = tuple(decode_canonical_bytes(op.config_payload.encode(), Sci02CConfig, maximum_bytes=binding.MAX_RECORD) for op in operations)
    pooled = tuple(c for c in configs if c.phase in ('fit', 'calibrate', 'confirm'))
    if (len(pooled) != 1 or tuple(sorted(configs, key=lambda c: c.node_id)) != binding.selected_for(pooled[0])
            or any(op.node_id != c.node_id or op.config_identity != c.identity
                or op.selection.capability_key != 'matrix-sci02c.' + c.phase for op, c in zip(operations, configs, strict=True))
            or draft.development_study != binding.development_root(configs, draft.development_study.study_id)):
        raise ValueError('SCI02-C inquiry changes its complete original scientific population')
    return {c.node_id: c for c in configs}


def scope(config):
    from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02c_bindings import WORLD
    return ScientificConditionScope(config.study.original_selection.object_id, WORLD, config.design.coordinate.coordinate_id,
        ('signed-paired-force-projected-response', 'required-consumer-precision'), ('actuator-units', 'actuator-units'),
        'receiver.primary-y-source64.hs48', config.design.coordinate.clock_id,
        'Original minus EARLY; source64 FACTOR-force momentum projection; causal HOLD16/32; H64 panel mean; original whole-root population.',
        source_config_sha256=config.study.fingerprint(), population_id='population.matrix-sci02c.original-reservation')


def inquiry_endpoint_validator(draft, endpoint):
    if endpoint != scope(next(iter(wave(draft).values()))):
        raise ValueError('SCI02-C inquiry cannot convert Matrix development into a molecular supply')


def inquiry_work_projector(draft, task_id):
    config = wave(draft)[task_id]
    operation, = (op for op in draft.operations if op.node_id == task_id)
    method = WorkMethod(config.phase, config.study, operation.selection.implementation_sha256)
    identity = ObjectIdentity.from_record('method.matrix-sci02c.' + config.phase, method)
    return ScientificInquiryWork(identity, tuple(sorted((config.study.identity, *config.retained_cases,
        *(r.identity for r in config.roots)), key=lambda p: p.object_id)), scope(config),
        ObjectIdentity.from_record('observation.matrix-sci02c.' + config.phase, method))


def product(products, config):
    values = tuple(products['records'].get(config.node_id, {}).values())
    if not values: return None
    if len(values) != 1 or type(values[0]) is not Sci02CProduct or values[0].config != config:
        raise ValueError('SCI02-C inquiry changes its original assessed product')
    result, = values
    receipt = products['receipts'].get(config.node_id)
    if (receipt is None or receipt.operational_status is not OperationalStatus.SUCCEEDED
            or sum(p.payload_schema == result.SCHEMA and p.content_sha256 == result.fingerprint()
                for p in receipt.output_logical_artifacts) != 1):
        raise ValueError('SCI02-C inquiry lacks its actual successful producing receipt')
    return result


def assessed(draft, products):
    configs = wave(draft)
    rows = tuple(product(products, c) for c in configs.values())
    if any(p is None for p in rows): return ()
    pooled, = (p for p in rows if p.config.phase in ('fit', 'calibrate', 'confirm'))
    from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02c_bindings as binding
    expected = tuple(sorted((products['records'][c.node_id][next(iter(products['records'][c.node_id]))].identity
        for c in binding.parents_for(pooled.config).values()), key=lambda p: p.object_id))
    if pooled.predecessors != expected:
        raise ValueError('SCI02-C inquiry loses original complete tranche custody')
    return rows


def inquiry_outcome_projector(draft, specification, products):
    inquiry_endpoint_validator(draft, specification.endpoint)
    return 'useful-supply' if assessed(draft, products) else 'unresolved'


def inquiry_claim_assessment_projector(draft, specification, products):
    claims = tuple(c for c in draft.development_study.claims
        if ObjectIdentity.from_record(c.claim_id, c) in specification.target.required_claims)
    if not claims: return ()
    inquiry_endpoint_validator(draft, specification.target.scope)
    rows = assessed(draft, products)
    if not rows: return ()
    fitted, = (p for p in rows if p.config.phase in ('fit', 'calibrate', 'confirm'))
    receipt = products['receipts'][fitted.config.node_id]
    disposition = AssessmentDisposition.UNEVALUABLE
    # Development may supply a local scientific stop; it never establishes
    # prospective economical reuse or the foreign molecular parent target.
    return tuple(InquiryClaimAssessment(c, fitted.config.identity, fitted.identity,
        ObjectIdentity.from_record(receipt.receipt_id, receipt), scope(fitted.config), disposition,
        tuple(sorted((p.identity for p in rows), key=lambda p: p.object_id)),
        tuple(sorted(r.group_id for r in fitted.config.roots)), draft.development_study.numerical_view_ids,
        c.evidence_ceiling, c.outcome_access, c.visibility_ceiling) for c in claims)


def inquiry_evidence_projector(draft, payloads, products=None):
    configs = wave(draft)
    first = next(iter(configs.values()))
    views = draft.development_study.numerical_view_ids
    rows = []
    for external in draft.external_inputs:
        suffix = '.npz' if external.media_type == 'application/x-npz' else '.json'
        name = 'external-' + sha256(external.input_id.encode()).hexdigest()[:24] + suffix
        if sha256(payloads[name]).hexdigest() != external.expected_content_sha256:
            raise ValueError('SCI02-C inquiry substitutes exact original retained operands')
        units = tuple(sorted({r.group_id for c in configs.values() for r in c.roots
            if external.logical_artifact_id.endswith(r.fingerprint())}))
        rows.append(InquiryEvidenceBinding(external.input_id, external.expected_content_sha256, scope(first),
            ContributionRole.RETAINED_ANALYSIS_INPUT, units, views))
    if products is not None:
        if set(products['records']) - set(configs): raise ValueError('SCI02-C inquiry adds a foreign operation')
        for task_id, outputs in products['records'].items():
            record = product(products, configs[task_id])
            for output_id in outputs:
                rows.append(InquiryEvidenceBinding(output_id, record.fingerprint(), scope(record.config),
                    ContributionRole.RETAINED_ANALYSIS_INPUT, tuple(sorted(r.group_id for r in record.config.roots)), views))
    return tuple(sorted(rows, key=lambda r: r.binding_id))
