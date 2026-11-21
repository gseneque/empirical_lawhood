# SPDX-License-Identifier: MPL-2.0
"""Scoped SCI02 meanings for the existing outer inquiry service.

A complete experiment supplies findings for requirement revision. It does not
establish the broad preparation/predictability/policy question, or satisfy the
separate molecular shortcut target merely by completing its assigned work.
"""
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

from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02_records import METHODS, RECIPES, Sci02Config, Sci02Design, Sci02Product


@dataclass(frozen=True, slots=True)
class Sci02WorkMethod(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-sci02/work-method'
    phase: str
    recipe: str
    design: Sci02Design
    implementation_sha256: str


def _wave(draft):
    from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02_bindings as binding
    operations = tuple(op for op in draft.operations if op.node_id in draft.selected_operation_ids)
    configs = tuple(decode_canonical_bytes(op.config_payload.encode(), Sci02Config,
        maximum_bytes=binding.MAX_RECORD) for op in operations)
    if not configs or any(op.node_id != c.node_id or op.config_identity != c.identity
            or op.selection.capability_key != 'matrix-sci02.' + c.phase for op, c in zip(operations, configs, strict=True)):
        raise ValueError('SCI02 inquiry substitutes original operation semantics')
    first = configs[0]
    roots = {c.root for c in configs}
    expected = tuple(sorted((c for root in roots for c in binding.configs(first.design, root, first.provenance)), key=lambda c: c.node_id))
    if (tuple(sorted(configs, key=lambda c: c.node_id)) != expected
            or draft.development_study != binding.development_root(configs, draft.development_study.study_id)
            or draft.external_inputs != binding.external_contracts(configs)
            or draft.links != tuple(sorted((link for c in configs for link in binding.input_links(c)), key=lambda v: v.edge_id))):
        raise ValueError('SCI02 inquiry changes its original complete scientific census')
    return {c.node_id: c for c in configs}


def scope(config):
    from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02_bindings import WORLD
    return ScientificConditionScope(config.root.selection.object_id, WORLD, config.design.coordinate.coordinate_id,
        ('actuator-normalized-response-error', 'factor-momentum-signal'), ('dimensionless', 'dimensionless'),
        'receiver.primary-y-source64.hs48', config.design.coordinate.clock_id,
        'Fixed source64 physical instrument; matched preparation arms; actual handoff and one permitted HOLD32 query; H16-H64.',
        source_config_sha256=config.design.fingerprint(), population_id='population.matrix-sci02.selected')


def inquiry_endpoint_validator(draft, endpoint):
    first = next(iter(_wave(draft).values()))
    if endpoint != scope(first):
        raise ValueError('SCI02 inquiry cannot replace its Matrix scope with a molecular or qualified target')


def inquiry_work_projector(draft, task_id):
    config = _wave(draft)[task_id]
    operation, = (op for op in draft.operations if op.node_id == task_id)
    method = Sci02WorkMethod(config.phase, config.recipe, config.design, operation.selection.implementation_sha256)
    identity = ObjectIdentity.from_record('method.matrix-sci02.' + config.phase + '.' + config.recipe.lower(), method)
    return ScientificInquiryWork(identity, tuple(sorted((config.design.identity, config.root.identity), key=lambda v: v.object_id)),
        scope(config), ObjectIdentity.from_record('observation.matrix-sci02.' + config.phase, method))


def _product(products, config):
    outputs = products['records'].get(config.node_id, {})
    if not outputs: return None
    records = tuple(outputs.values())
    if len(records) != 1 or type(records[0]) is not Sci02Product or records[0].config != config:
        raise ValueError('SCI02 inquiry changes its exact producing output')
    product, = records
    receipt = products['receipts'].get(config.node_id)
    if (receipt is None or receipt.operational_status is not OperationalStatus.SUCCEEDED
            or sum(v.payload_schema == product.SCHEMA and v.content_sha256 == product.fingerprint()
                for v in receipt.output_logical_artifacts) != 1):
        raise ValueError('SCI02 inquiry lacks the original successful producing receipt')
    return product


def _assessed(draft, products):
    configs = _wave(draft)
    reductions = []
    from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02_bindings import config_for
    for config in sorted(configs.values(), key=lambda c: c.root.ordinal):
        if config.phase != 'reduce': continue
        reduction = _product(products, config)
        if reduction is None: return ()
        values, predecessors = {}, []
        for recipe in RECIPES:
            assessed = _product(products, config_for(config, recipe + '.assess'))
            if assessed is None: return ()
            predecessors.append(assessed.identity)
            measured = dict(assessed.measurements)
            if measured.get('assigned') != 1:
                raise ValueError('SCI02 inquiry changes the original assigned arm denominator')
            for method in METHODS:
                if measured.get(method + '.available') != 1: continue
                passed = (measured[method + '.error'] <= config.design.error_tolerance
                    and measured[method + '.view_difference'] <= config.design.view_tolerance
                    and measured['signal.factor_momentum64'] >= config.design.signal_minimum)
                if measured[method + '.joint_success'] != int(passed):
                    raise ValueError('SCI02 inquiry changes the independently measured acceptance criteria')
            values.update({recipe + '.' + k: v for k, v in assessed.measurements})
            values[recipe + '.evaluable'] = int(assessed.disposition == 'AVAILABLE')
        if reduction.predecessors != tuple(sorted(predecessors, key=lambda p: p.object_id)):
            raise ValueError('SCI02 inquiry substitutes an original assessment parent')
        actual = dict(reduction.measurements)
        if any(actual.get(k) != v for k, v in values.items()):
            raise ValueError('SCI02 inquiry changes complete original assessment findings')
        reductions.append(reduction)
    return tuple(reductions)


def inquiry_outcome_projector(draft, specification, products):
    inquiry_endpoint_validator(draft, specification.endpoint)
    # Useful supply is the scoped evidence for the next decision, including
    # negative results. It is not a successful approximation or target claim.
    return 'useful-supply' if _assessed(draft, products) else 'unresolved'


def inquiry_claim_assessment_projector(draft, specification, products):
    claims = tuple(c for c in draft.development_study.claims
        if ObjectIdentity.from_record(c.claim_id, c) in specification.target.required_claims)
    if not claims: return ()
    inquiry_endpoint_validator(draft, specification.target.scope)
    assessed = _assessed(draft, products)
    if not assessed: return ()
    first = assessed[0]
    receipt = products['receipts'][first.config.node_id]
    # The broad three-part scientific question is not a predeclared Boolean
    # superiority test. DEV completion cannot convert it into target success.
    # Foreign molecular claims receive no projection at all.
    evidence = tuple(sorted((p.identity for p in assessed), key=lambda p: p.object_id))
    return tuple(InquiryClaimAssessment(c, first.config.identity, first.identity,
        ObjectIdentity.from_record(receipt.receipt_id, receipt), scope(first.config), AssessmentDisposition.UNEVALUABLE,
        evidence, tuple(sorted(p.config.root.group_id for p in assessed)), draft.development_study.numerical_view_ids,
        c.evidence_ceiling, c.outcome_access, c.visibility_ceiling) for c in claims)


def inquiry_evidence_projector(draft, payloads, products=None):
    configs = _wave(draft)
    first = next(iter(configs.values()))
    views = draft.development_study.numerical_view_ids
    rows = []
    for external in draft.external_inputs:
        suffix = '.npz' if external.media_type == 'application/x-npz' else '.json'
        filename = 'external-' + sha256(external.input_id.encode()).hexdigest()[:24] + suffix
        if sha256(payloads[filename]).hexdigest() != external.expected_content_sha256:
            raise ValueError('SCI02 inquiry substitutes its original input bytes')
        units = tuple(sorted({c.root.group_id for c in configs.values() if external.logical_artifact_id == c.root.record_id
            or any(external.logical_artifact_id == p.object_id for _, pins in c.root.streams for p in pins)}))
        rows.append(InquiryEvidenceBinding(external.input_id, external.expected_content_sha256, scope(first),
            ContributionRole.RETAINED_ANALYSIS_INPUT, units, views))
    if products is not None:
        if set(products['records']) - set(configs): raise ValueError('SCI02 inquiry adds a foreign producing operation')
        for task_id, outputs in products['records'].items():
            product = _product(products, configs[task_id])
            for output_id in outputs:
                rows.append(InquiryEvidenceBinding(output_id, product.fingerprint(), scope(product.config),
                    ContributionRole.RETAINED_ANALYSIS_INPUT, (product.config.root.group_id,), views))
    return tuple(sorted(rows, key=lambda r: r.binding_id))
