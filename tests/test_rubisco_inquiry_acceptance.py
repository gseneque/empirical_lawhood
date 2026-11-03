# SPDX-License-Identifier: MPL-2.0
"""Exposed arithmetic and adverse contracts, without native scientific execution."""
from dataclasses import replace
from decimal import Decimal
from math import exp, log

import pytest

from empirical_lawhood.adapters.methods.rubisco_combinations.source_binding import GENBANK_SOURCE_SHA256, WILSON_SOURCE_SHA256, TeParentGenbankInputV1, WilsonArticleInputV1
from empirical_lawhood.adapters.methods.rubisco_inquiry import science
from empirical_lawhood.adapters.methods.rubisco_inquiry.operation_bindings import operation_registrations
from empirical_lawhood.adapters.methods.rubisco_inquiry.recursive_translation import supply_draft, use_draft
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as Verdict

D = Decimal


@pytest.fixture(scope='module')
def operands():
    from tests.rubisco_nomination_fixture import source_operands
    retained = source_operands()
    return (WilsonArticleInputV1('input.wilson-inquiry.article', WILSON_SOURCE_SHA256,
                retained['macro/source.007--wilson2017-jbc.html'].decode()),
            TeParentGenbankInputV1('input.wilson-inquiry.genbank', GENBANK_SOURCE_SHA256,
                retained['macro/source.008--te-MG000148.gb'].decode()))


@pytest.fixture(scope='module')
def supplier(operands):
    return science.supply(*operands)


def test_frozen_quartet_independent_arithmetic_and_full_source(supplier):
    assert len(supplier.panel.rows) == 19
    forecast = supplier.forecast.additive_point
    for got, a, b, c in ((forecast.turnover_s_inv, 6.4, 8.8, 6.9),
                         (forecast.specificity_dimensionless, 50.5, 48.0, 52.6)):
        oracle = D(str(a)) * D(str(b)) / D(str(c))
        assert abs(got - oracle) / oracle < D('1e-12')
        assert abs(float(got) - exp(log(a) + log(b) - log(c))) / float(got) < 1e-12
    assert decode_canonical_bytes(supplier.canonical_bytes(), science.RubiscoSupply, maximum_bytes=4*1024**2) == supplier


def test_authentic_row22_is_noncompensating_negative(supplier):
    result = science.assess(supplier, science.authentic_candidate(supplier))
    assert result.disposition is Verdict.FALSIFIED
    assert result.turnover_ratio == D('8.1') / D('5.46') > 1
    assert result.specificity_ratio == D('45.5') / D(238) < 1
    assert result.unresolved


def test_conditional_compatible_numeric_and_missing_endpoints(supplier):
    candidate = replace(science.authentic_candidate(supplier), turnover_s_inv=D('5.46'), specificity_dimensionless=D(238))
    result = science.assess(supplier, candidate)
    assert result.disposition is Verdict.SATISFIED
    assert result.turnover_ratio == result.specificity_ratio == 1
    for field in ('turnover_s_inv', 'specificity_dimensionless'):
        missing = science.assess(supplier, replace(candidate, **{field: None}))
        assert missing.disposition is Verdict.UNEVALUABLE
        assert missing.turnover_ratio is missing.specificity_ratio is None


def test_wrong_assembly_reference_and_unconditional_refuse(supplier):
    candidate = science.authentic_candidate(supplier)
    wrong_recipe = next(c.protein_recipe for c in supplier.science.corners if c.role == 'PARENT')
    for changed in (replace(candidate, assembly=wrong_recipe), replace(candidate, specificity_reference='galdieria-sulfuraria'),
                    replace(candidate, turnover_reference='maize.coupled.3p70'), replace(candidate, conditional_scenario=False)):
        result = science.assess(supplier, changed)
        assert result.disposition is Verdict.REFUSED
        assert result.turnover_ratio is result.specificity_ratio is None


def test_source_substitution_and_separate_drafts(operands, supplier):
    first, second = supply_draft(*operands), use_draft(supplier)
    assert len(first.operations) == len(second.operations) == 1
    assert first.operations[0].selection != second.operations[0].selection
    assert all(not r.native_effect for r in operation_registrations())
    with pytest.raises(ValueError):
        replace(operands[0], raw_html_utf8=operands[0].raw_html_utf8 + ' ')


def test_registered_outcome_projection_refuses_endpoint_and_config_substitution(operands, supplier):
    from types import SimpleNamespace as N
    from empirical_lawhood.adapters.methods.rubisco_inquiry.recursive_translation import inquiry_outcome_projector
    from empirical_lawhood.kernel.status import OperationalStatus
    draft = supply_draft(*operands)
    node = draft.operations[0].node_id
    specification = N(distinguishing_assessment=draft.operations[0].config_identity, endpoint=supplier.scope)
    logical = N(payload_schema=supplier.SCHEMA, content_sha256=supplier.fingerprint())
    products = {'records': {node: {'product': supplier}}, 'receipts': {node: N(
        operational_status=OperationalStatus.SUCCEEDED, output_logical_artifacts=(logical,))}}
    assert inquiry_outcome_projector(draft, specification, products) == 'useful-supply'
    with pytest.raises(ValueError, match='endpoint'):
        inquiry_outcome_projector(draft, N(distinguishing_assessment=specification.distinguishing_assessment,
            endpoint=replace(supplier.scope, receiver_id='wrong.receiver')), products)
    with pytest.raises(ValueError, match='configuration'):
        inquiry_outcome_projector(draft, N(distinguishing_assessment=draft.development_study.system, endpoint=supplier.scope), products)
    assert inquiry_outcome_projector(draft, specification, {'records': {}, 'receipts': {}}) == 'unresolved'


def test_strict_assessment_codec_rejects_ratio_or_uncertainty_substitution(supplier):
    result = science.assess(supplier, science.authentic_candidate(supplier))
    with pytest.raises(ValueError, match='ratios'):
        replace(result, specificity_ratio=D(2))
    with pytest.raises(ValueError, match='uncertainties'):
        replace(result, unresolved=())


def _evidence_payloads(draft, records):
    from hashlib import sha256
    by_digest = {record.fingerprint(): record for record in records}
    return {'external-' + sha256(external.input_id.encode()).hexdigest()[:24] + '.json':
            by_digest[external.expected_content_sha256].canonical_bytes() for external in draft.external_inputs}


def test_original_article_sequence_scope_role_not_requested_endpoint(operands, supplier):
    from empirical_lawhood.adapters.methods.rubisco_inquiry.recursive_translation import inquiry_evidence_projector
    from empirical_lawhood.kernel.recursive_requirements import ContributionRole
    draft = supply_draft(*operands)
    records = {row.binding_id: row for row in inquiry_evidence_projector(draft, _evidence_payloads(draft, operands))}
    article = records['external.rubisco-inquiry.supply.article']
    sequence = records['external.rubisco-inquiry.supply.genbank']
    assert article.scope != sequence.scope != supplier.scope
    assert article.role is sequence.role is ContributionRole.RETAINED_ANALYSIS_INPUT
    assert article.scope.quantity_ids == ('specificity', 'turnover')
    assert sequence.scope.quantity_ids == ('lsu-sequence', 'ssu-sequence')
    assert all(not row.independent_unit_ids for row in records.values())


def test_evidence_projector_retains_product_scope_and_refuses_missing_metadata(operands, supplier):
    from empirical_lawhood.adapters.methods.rubisco_inquiry.recursive_translation import inquiry_evidence_projector
    from empirical_lawhood.kernel.recursive_requirements import ContributionRole
    draft = supply_draft(*operands)
    payloads = _evidence_payloads(draft, operands)
    rows = inquiry_evidence_projector(draft, payloads, {'records': {'rubisco-inquiry.supply': {'rubisco-inquiry.supply.product': supplier}}})
    product = next(row for row in rows if row.binding_id == 'rubisco-inquiry.supply.product')
    assert product.scope == supplier.scope and product.role is ContributionRole.DESIGN_OPERAND
    with pytest.raises(ValueError, match='metadata'):
        inquiry_evidence_projector(draft, payloads, {'records': {'rubisco-inquiry.supply': {'rubisco-inquiry.supply.product': supplier.forecast}}})
    first, second = operands
    changed = dict(payloads)
    from hashlib import sha256
    external = next(row for row in draft.external_inputs if row.input_id.endswith('.article'))
    changed['external-' + sha256(external.input_id.encode()).hexdigest()[:24] + '.json'] = replace(first, input_id='input.changed-id').canonical_bytes()
    with pytest.raises(ValueError, match='bytes'):
        inquiry_evidence_projector(draft, changed)


def test_api_evidence_helper_refuses_parent_scope_relabel(supplier, monkeypatch):
    from empirical_lawhood.api.recursive_inquiry_evidence import project_wave_evidence_bindings
    from empirical_lawhood.adapters.methods.rubisco_inquiry.executable_binding import EXECUTABLE_BINDING_FACTORIES
    # Isolate this API meaning test from the coordinator-owned generated aggregate.
    monkeypatch.setattr('empirical_lawhood.api.recursive_inquiry_evidence.operation_factories', lambda: EXECUTABLE_BINDING_FACTORIES)
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    from empirical_lawhood.kernel.recursive_requirements import ContributionRole
    from empirical_lawhood.kernel.references import ArtifactIdentity
    from empirical_lawhood.kernel.scientific_contributions import ContributionManifest, ContributionProduct
    from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
    # Pure metadata conformance: this manifest is never admitted to real custody.
    product = ContributionProduct('product.software-test.supplier', ObjectIdentity.from_record(supplier.product_id, supplier),
        ArtifactIdentity('artifact.software-test.supplier', 'scientific-product', supplier.SCHEMA, supplier.fingerprint(), 'application/json', len(supplier.canonical_bytes())),
        ObjectIdentity('receipt.software-test', 'empirical-lawhood/testing/receipt', '1.0.0', 'a'*64),
        ContributionRole.DESIGN_OPERAND, EvidenceCeiling.NON_PROMOTABLE, OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY)
    parent = ContributionManifest('contribution.software-test', science.QUESTION, 'Exposed metadata conformance only', supplier.scope, (product,),
        (ObjectIdentity.from_record(supplier.evaluation.evaluation_id, supplier.evaluation),), ())
    candidate = science.authentic_candidate(supplier)
    draft = use_draft(supplier, candidate, parent=parent)
    bindings = project_wave_evidence_bindings(draft=draft, payloads=_evidence_payloads(draft, (supplier, candidate)))
    original = bindings['external.rubisco-inquiry.use.supplier']
    assert original.scope == parent.scope and original.role is product.role
    bad_parent = replace(parent, scope=replace(parent.scope, receiver_id='wrong.requested-receiver'))
    changed = replace(draft, contribution_parents=(bad_parent,))
    with pytest.raises(ValueError, match='original contribution scope'):
        project_wave_evidence_bindings(draft=changed, payloads=_evidence_payloads(draft, (supplier, candidate)))


def test_use_outcome_refuses_instance_as_supplier_identity(supplier):
    from types import SimpleNamespace as N
    from empirical_lawhood.adapters.methods.rubisco_inquiry.recursive_translation import inquiry_outcome_projector
    from empirical_lawhood.adapters.methods.rubisco_inquiry.operation_bindings import record_identity
    from empirical_lawhood.kernel.status import OperationalStatus
    candidate = science.authentic_candidate(supplier)
    draft = use_draft(supplier, candidate)
    result = replace(science.assess(supplier, candidate), supplier=record_identity(candidate))
    node = draft.operations[0].node_id
    spec = N(distinguishing_assessment=draft.operations[0].config_identity, endpoint=supplier.scope)
    logical = N(payload_schema=result.SCHEMA, content_sha256=result.fingerprint())
    products = {'records': {node: {'product': result}}, 'receipts': {node: N(
        operational_status=OperationalStatus.SUCCEEDED, output_logical_artifacts=(logical,))}}
    with pytest.raises(ValueError, match='exact supplier'):
        inquiry_outcome_projector(draft, spec, products)


def test_api_meaning_helper_source_scope_and_complete_census(operands, supplier, monkeypatch):
    from empirical_lawhood.api import recursive_inquiry_evidence as api
    from empirical_lawhood.adapters.methods.rubisco_inquiry.executable_binding import EXECUTABLE_BINDING_FACTORIES
    from empirical_lawhood.adapters.methods.rubisco_inquiry.recursive_translation import inquiry_evidence_projector
    monkeypatch.setattr(api, 'operation_factories', lambda: EXECUTABLE_BINDING_FACTORIES)
    draft = supply_draft(*operands)
    payloads = _evidence_payloads(draft, operands)
    bindings = api.project_wave_evidence_bindings(draft=draft, payloads=payloads)
    assert len(bindings) == 2
    assert len({row.scope for row in bindings.values()}) == 2
    assert all(not row.independent_unit_ids for row in bindings.values())
    from types import SimpleNamespace as N
    factory = EXECUTABLE_BINDING_FACTORIES[0]
    def omitted(*args):
        return inquiry_evidence_projector(*args)[:1]
    monkeypatch.setattr(api, 'operation_factories', lambda: (N(registration=factory.registration, inquiry_evidence_projector=omitted),))
    with pytest.raises(ValueError, match='exact selected source bytes'):
        api.project_wave_evidence_bindings(draft=draft, payloads=payloads)
    def extra(*args):
        rows = inquiry_evidence_projector(*args)
        return tuple(sorted((*rows, replace(rows[0], binding_id='extra.unselected-input')), key=lambda row: row.binding_id))
    monkeypatch.setattr(api, 'operation_factories', lambda: (N(registration=factory.registration, inquiry_evidence_projector=extra),))
    with pytest.raises(ValueError, match='complete original'):
        api.project_wave_evidence_bindings(draft=draft, payloads=payloads)


def test_source_only_design_endpoint_validation_precedes_missing_product(operands, supplier):
    from types import SimpleNamespace as N
    from empirical_lawhood.adapters.methods.rubisco_inquiry.recursive_translation import inquiry_outcome_projector
    draft = supply_draft(*operands)
    original = N(distinguishing_assessment=draft.operations[0].config_identity, endpoint=supplier.scope)
    assert inquiry_outcome_projector(draft, original, {'records': {}}) == 'unresolved'
    wrong = N(distinguishing_assessment=original.distinguishing_assessment,
              endpoint=replace(supplier.scope, receiver_id='wrong.requested-endpoint'))
    with pytest.raises(ValueError, match='original design endpoint'):
        inquiry_outcome_projector(draft, wrong, {'records': {}})


def test_static_history_endpoint_validates_supply_and_use_without_current_assessment(operands, supplier):
    from empirical_lawhood.adapters.methods.rubisco_inquiry.recursive_translation import inquiry_endpoint_validator
    first, later = supply_draft(*operands), use_draft(supplier)
    assert first.operations[0].config_identity != later.operations[0].config_identity
    assert inquiry_endpoint_validator(first, supplier.scope) is None
    assert inquiry_endpoint_validator(later, supplier.scope) is None
    wrong_scope = replace(supplier.scope, receiver_id='wrong.history-receiver')
    for draft in (first, later):
        with pytest.raises(ValueError, match='original design endpoint'):
            inquiry_endpoint_validator(draft, wrong_scope)
    changed = replace(later, operations=(replace(later.operations[0], selection=first.operations[0].selection),))
    with pytest.raises(ValueError, match='selected configuration'):
        inquiry_endpoint_validator(changed, supplier.scope)
