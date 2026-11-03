# SPDX-License-Identifier: MPL-2.0
"""Exposed source/math/actual-compiler conformance; no scientific operation or qualification."""
from dataclasses import replace
from decimal import Decimal

import pytest
from tests.rubisco_inquiry_source_fixtures import portfolio_source_operands

from empirical_lawhood.adapters.methods.rubisco_portfolio_inquiry import science, operation_bindings as owner, recursive_translation as drafts
from empirical_lawhood.adapters.methods.rubisco_portfolio_inquiry.source_manifest import INITIAL_CANDIDATE_IDS
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition
from empirical_lawhood.runtime.capabilities import CapabilityRegistry
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave


@pytest.fixture(scope='module')
def source():
    return science.source_audit_from_bytes(portfolio_source_operands(), candidate_ids=INITIAL_CANDIDATE_IDS)


@pytest.fixture(scope='module')
def supplier(source):
    # Software-only exposed original-data fixture arithmetic, not actual operation execution.
    return science.supply(source)


def test_complete_sources_recipes_and_endpoint_roles(source):
    rows = science.complete_candidate_roster(source)
    assert len(rows) == 32
    assert len(source.sources) == 34
    assert len(science.parent_anchors(source)) == 4
    unknown = next(v for v in rows if v.candidate_id == 'gp.i95m')
    assert unknown.turnover_s_inv is None and unknown.specificity_dimensionless is None
    assert len(unknown.ssu_sequence_views) == 2
    assert all(v.biological_admission == science.BIOLOGICAL_ADMISSION for v in rows)
    ps3 = next(v for v in rows if v.candidate_id == 'potato.ps3')
    assert 'FOUR_SITE' in ps3.pairing_and_processing
    assert ps3.turnover_s_inv == Decimal('3.5') and ps3.specificity_dimensionless == Decimal('87.3')
    assert source == decode_canonical_bytes(source.canonical_bytes(), science.SourceAudit, maximum_bytes=None)


def test_source_bytes_missing_endpoint_and_reference_refuse(source, supplier):
    with pytest.raises(ValueError, match='cutoff'):
        replace(source, cutoff='fresh-independent-20261012')
    with pytest.raises(ValueError, match='digest|length'):
        replace(source.sources[0], raw_base64='eA==')
    instance = science.authentic_candidate(supplier)
    for wrong in (replace(instance, conditional_only=False), replace(instance, references=(('g.sulfuraria', Decimal('5.46'), Decimal(166)),)), replace(instance, candidates=tuple(reversed(instance.candidates)))):
        with pytest.raises(ValueError, match='refuses'):
            science.assess(supplier, wrong)
    index = next(i for i, v in enumerate(instance.candidates) if v.candidate_id == 'gp.i95m')
    fabricated = replace(instance.candidates[index], turnover_s_inv=Decimal(8), specificity_dimensionless=Decimal(238))
    wrong = replace(instance, candidates=instance.candidates[:index] + (fabricated,) + instance.candidates[index + 1:])
    with pytest.raises(ValueError, match='refuses'):
        science.assess(supplier, wrong)


def test_joint_hull_does_not_join_incompatible_endpoint_maxima():
    D = Decimal
    points = ((D(2), D(-3)), (D(-3), D(2)))
    assert not science.joint_hull_covers(points, D(1), D(1))
    assert science.joint_hull_covers(((D(2), D(0)), (D(0), D(2))), D('0.9'), D('0.9'))
    assert science.joint_hull_covers((), D(-1), D(-1))
    assert not science.joint_hull_covers((), D(1), D(0))


def test_independent_full_denominator_no_nominee_and_single_endpoint_failures(supplier):
    result = science.assess(supplier, science.authentic_candidate(supplier))
    assert len(result.sentinels) == 4
    assert all(v.point_direction == 'POSITIVE/POSITIVE' for v in result.sentinels[:3])
    assert result.sentinels[3].point_direction == 'POSITIVE/NEGATIVE'
    assert 'FOUR_SITE' in result.sentinels[2].intervention
    assert len(supplier.effects) == 27
    assert len(result.candidate_views) == 64 and len(result.support_queries) == 8
    assert result.nominee is None and result.nomination == 'UNSUPPORTED'
    assert result.comparison == 'UNEVALUATED'
    assert all(v.point_joint_pass is not True for v in result.candidate_views)
    assert all(v.transported_all_background_envelope_support is AssessmentDisposition.FALSIFIED for v in result.support_queries)
    gp = tuple(v for v in result.support_queries if v.background == 'gp')
    assert all(v.within_background_single_effect_support is AssessmentDisposition.UNEVALUABLE for v in gp)
    fast = next(v for v in result.candidate_views if v.candidate_id == 'wilson2017-row17' and v.reference_view == 'radiometric')
    assert fast.turnover_ratio > 1 and fast.specificity_ratio < 1 and fast.point_joint_pass is False
    assert result == decode_canonical_bytes(result.canonical_bytes(), science.PortfolioAssessment, maximum_bytes=None)


def _compile(draft):
    result = compile_recursive_wave(draft=draft, registrations=owner.operation_registrations(),
        registry=CapabilityRegistry('registry.exposed-portfolio-compile', owner.operation_manifests()),
        implementation_commit='1' * 40, output_codecs=owner.output_codecs())
    assert len(result.execution_plan.tasks) == 1
    return result


def test_actual_supply_and_portable_mixed_successor_compile(source, supplier):
    from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    from empirical_lawhood.kernel.references import ArtifactIdentity
    from empirical_lawhood.kernel.recursive_requirements import ContributionRole
    from empirical_lawhood.kernel.scientific_contributions import ContributionManifest, ContributionProduct
    # Software metadata fixture, never actual scientific custody or qualification.
    product = ContributionProduct('product.exposed-portfolio-compile.design-operand',
        ObjectIdentity.from_record(supplier.product_id, supplier),
        ArtifactIdentity('artifact.exposed-portfolio-compile.supplier', 'scientific-product', supplier.SCHEMA,
                         supplier.fingerprint(), 'application/json', len(supplier.canonical_bytes())),
        ObjectIdentity('receipt.exposed-portfolio-compile', 'empirical-lawhood/testing/exposed-compile-receipt', '1.0.0', 'a' * 64),
        ContributionRole.DESIGN_OPERAND, EvidenceCeiling.NON_PROMOTABLE,
        OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY)
    parent = ContributionManifest('contribution.exposed-portfolio-compile', science.QUESTION,
        'Software compile fixture; no actual scientific custody.', supplier.scope, (product,),
        (ObjectIdentity.from_record(supplier.check.check_id, supplier.check),), ())
    parent = decode_canonical_bytes(parent.canonical_bytes(), ContributionManifest, maximum_bytes=None)
    _compile(drafts.supply_draft(source))
    later = drafts.use_draft(supplier, parent=parent)
    result = _compile(later)
    assert len(result.selected_scientific_projection.contribution_parents) == 1
    assert next(v for v in later.external_inputs if v.input_id.endswith('.supplier')).scientific_role == 'MODEL'
    wrong = replace(later, external_inputs=tuple(replace(v, scientific_role='DESIGN_OPERAND') if v.input_id.endswith('.supplier') else v for v in later.external_inputs))
    with pytest.raises(ValueError):
        _compile(wrong)


def test_authenticated_looking_forged_consumer_outputs_refuse(supplier):
    from types import SimpleNamespace
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    from empirical_lawhood.kernel.status import OperationalStatus
    draft = drafts.use_draft(supplier)
    assessment = science.assess(supplier, science.authentic_candidate(supplier))
    selected = draft.operations[0]
    spec = SimpleNamespace(endpoint=assessment.scope, distinguishing_assessment=selected.config_identity)

    def products(record):
        # A software projection fixture simulates authenticated-looking metadata;
        # actual custody authentication remains owned by the API/receipt reader.
        logical = SimpleNamespace(payload_schema=record.SCHEMA, content_sha256=record.fingerprint())
        receipt = SimpleNamespace(operational_status=OperationalStatus.SUCCEEDED, output_logical_artifacts=(logical,))
        return {'records': {selected.node_id: {selected.node_id + '.product': record}}, 'receipts': {selected.node_id: receipt}}

    assert drafts.inquiry_outcome_projector(draft, spec, products(assessment)) == 'useful-supply'
    views = (replace(assessment.candidate_views[0], point_joint_pass=True), *assessment.candidate_views[1:])
    queries = (replace(assessment.support_queries[0], required_specificity_multiplier=Decimal('1.25')), *assessment.support_queries[1:])
    sentinels = (*assessment.sentinels[:3], replace(assessment.sentinels[3], point_direction='POSITIVE/POSITIVE'))
    for forged in (replace(assessment, candidate_views=views), replace(assessment, support_queries=queries),
                   replace(assessment, sentinels=sentinels), replace(assessment, supplier=ObjectIdentity('product.wrong-portfolio-supplier', supplier.SCHEMA, '1.0.0', 'a' * 64))):
        with pytest.raises(ValueError, match='differs|changes exact supplier'):
            drafts.inquiry_outcome_projector(draft, spec, products(forged))
