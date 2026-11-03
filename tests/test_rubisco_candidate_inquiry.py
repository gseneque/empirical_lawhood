# SPDX-License-Identifier: MPL-2.0
"""Exposed software/source checks; no scientific execution or new biology."""
from dataclasses import replace
from decimal import Decimal

import pytest
from tests.rubisco_candidate_programme_fixture import programme_report
from tests.rubisco_inquiry_source_fixtures import candidate_source_operands
from empirical_lawhood.kernel.decoding import decode_canonical_bytes, decode_canonical_record
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition
from empirical_lawhood.adapters.methods.rubisco_candidate_inquiry import science
from empirical_lawhood.adapters.methods.rubisco_candidate_inquiry.operation_bindings import (
    BUDGET, MAX_BYTES, operation_registrations, InquiryOperationConfig,
)
from empirical_lawhood.adapters.methods.rubisco_candidate_inquiry.recursive_translation import supply_draft, use_draft


@pytest.fixture(scope='module')
def source():
    return science.source_audit_from_bytes(candidate_source_operands())


@pytest.fixture(scope='module')
def supplied(source):
    return science.supply(source)


def test_exact_sources_and_conditional_thresholds(source, supplied):
    assert len(source.sources) == 22
    assert len(supplied.panel.rows) == 19
    assert len(supplied.protein_recipes) == 9
    assert len(supplied.points) == 18
    thresholds = supplied.thresholds
    assert abs(thresholds[0].alpha_k_required - Decimal('3.8385204209')) < Decimal('1e-10')
    assert abs(thresholds[1].alpha_k_required - Decimal('2.6216598674')) < Decimal('1e-10')
    assert all(value.alpha_s_required == 0 for value in thresholds)
    assert decode_canonical_bytes(supplied.canonical_bytes(), science.CandidateSupply, maximum_bytes=None) == supplied


def test_independent_consumer_and_useful_decision(supplied):
    result = science.assess(supplied, science.authentic_candidate(supplied))
    assert result.disposition is AssessmentDisposition.SATISFIED
    assert len(result.frontier) == 36
    at3 = [v for v in result.frontier if v.alpha_k == 3 and v.alpha_s == 0]
    assert [v.joint_conditional_pass for v in at3] == [False, True]
    assert abs(at3[0].turnover_s_inv - Decimal('4.1758368873')) < Decimal('1e-10')
    assert all(v.joint_conditional_pass for v in result.frontier if v.alpha_k == 4 and v.alpha_s >= 0)
    assert not any(v.joint_conditional_pass for v in result.frontier if v.alpha_k == 1)
    assert not any(v.joint_conditional_pass for v in result.frontier if v.alpha_s < 0)
    assert result.nominee is None and result.comparison == 'UNEVALUATED'
    assert all(v.disposition is AssessmentDisposition.UNEVALUABLE for v in result.candidate_verdicts if v.candidate_id == 'gp.i95m')
    assert all(v.biological_admission == 'UNEVALUABLE_MATCHED_ASSAY_PREPARATION' for v in result.candidate_verdicts)
    # Actual positive local turnover still fails specificity: no endpoint compensation.
    donor = [v for v in result.candidate_verdicts if v.candidate_id == 'te.p415a-v98m']
    assert all(v.turnover_ratio > 1 and v.specificity_ratio < 1 and v.disposition is AssessmentDisposition.FALSIFIED for v in donor)


def test_retained_typed_assessment_preserves_complete_frontier_and_unknown_biology():
    """Read the exact exposed product without restoring its historical launcher."""
    report = programme_report()
    use = report['waves']['programme-use']
    documents = [value for products in use['report']['terminal_products'].values()
                 for value in products.values() if value['schema'] == science.CandidateAssessment.SCHEMA]
    assert len(documents) == 1
    assessment = decode_canonical_record(documents[0], science.CandidateAssessment)
    assert decode_canonical_bytes(assessment.canonical_bytes(), science.CandidateAssessment, maximum_bytes=None) == assessment
    assert assessment.fingerprint() == use['product_identities']['rubisco-candidate-inquiry.use']['rubisco-candidate-inquiry.use.product']['sha256']
    assert assessment.disposition is AssessmentDisposition.SATISFIED
    references = {'historical-radiometric-conditional', 'historical-coupled-conditional'}
    assert len(assessment.frontier) == 36
    assert {(row.reference_view, row.alpha_k, row.alpha_s) for row in assessment.frontier} == {
        (reference, Decimal(alpha_k), Decimal(alpha_s))
        for reference in references for alpha_k in ('0', '0.5', '1', '2', '3', '4')
        for alpha_s in ('-1', '0', '1')}
    assert len(assessment.independently_checked_thresholds) == 2
    assert {row.reference_view for row in assessment.independently_checked_thresholds} == references
    at_three = tuple(row for row in assessment.frontier if row.alpha_k == 3 and row.alpha_s == 0)
    assert {row.reference_view: row.joint_conditional_pass for row in at_three} == {
        'historical-radiometric-conditional': False, 'historical-coupled-conditional': True}
    assert all(set(row.to_document()) == {'schema', 'value', 'version'} for row in at_three)
    assert len(assessment.candidate_verdicts) == 12
    assert {(row.candidate_id, row.ssu_view, row.reference_view) for row in assessment.candidate_verdicts} == {
        (candidate, view, reference)
        for candidate, view in (('gp.wt', 'm1'), ('gp.wt', 'v1'), ('gp.i95m', 'm1'),
                                ('gp.i95m', 'v1'), ('te.p415a', 'native'), ('te.p415a-v98m', 'native'))
        for reference in references}
    actual_mutant = tuple(row for row in assessment.candidate_verdicts if row.candidate_id == 'gp.i95m')
    assert len(actual_mutant) == 4
    assert all(row.disposition is AssessmentDisposition.UNEVALUABLE
               and row.turnover_ratio is None and row.specificity_ratio is None for row in actual_mutant)
    assert all(row.disposition is AssessmentDisposition.FALSIFIED
               for row in assessment.candidate_verdicts if row.candidate_id != 'gp.i95m')
    assert all(row.biological_admission == 'UNEVALUABLE_MATCHED_ASSAY_PREPARATION' for row in assessment.candidate_verdicts)
    assert assessment.nominee is None and assessment.comparison == 'UNEVALUATED'
    assert assessment.unresolved == ('ACTUAL_GP_I95M_ENDPOINTS_UNKNOWN', 'GP_PREPARATION_UNRESOLVED',
                                      'MATCHED_ASSAY_PREPARATION_UNRESOLVED', 'GTG_INITIATION_M1_V1_UNRESOLVED')
    assert assessment.candidate_decision == ('RETAIN_EXPLORATORY_I95M_REQUIRE_MATCHED_CANDIDATE_BACKGROUND_KINETICS_'
                                           'REJECT_UNIT_TRANSFER_NOMINATION_AND_ASSAY_SUBSTITUTION')


def test_wrong_sources_cutoff_and_recipe(source):
    with pytest.raises(ValueError, match='source bytes'):
        replace(source.sources[0], raw_utf8=source.sources[0].raw_utf8 + ' ')
    with pytest.raises(ValueError, match='cutoff'):
        replace(source, cutoff='fresh-2026-10-11')
    with pytest.raises(ValueError, match='recipe'):
        replace(science.ProteinRecipe(*science.RECIPES[3]), sequence_ascii='F98M')


def test_exact_wrong_assembly_reference_and_missing_controls(supplied):
    instance = science.authentic_candidate(supplied)
    assert science.assess(supplied, replace(instance, references=('substituted-coupled-for-radiometric',))).disposition is AssessmentDisposition.REFUSED
    changed = (replace(instance.candidates[0], assembly='mixed L8S8'), *instance.candidates[1:])
    assert science.assess(supplied, replace(instance, candidates=changed)).disposition is AssessmentDisposition.REFUSED
    changed = (*instance.candidates[:-1], replace(instance.candidates[-1], specificity_dimensionless=None))
    result = science.assess(supplied, replace(instance, candidates=changed))
    assert all(v.disposition is AssessmentDisposition.UNEVALUABLE and v.specificity_ratio is None for v in result.candidate_verdicts if v.candidate_id == 'te.p415a-v98m')
    changed = (*instance.candidates[:-1], replace(instance.candidates[-1], turnover_s_inv=None))
    result = science.assess(supplied, replace(instance, candidates=changed))
    assert all(v.disposition is AssessmentDisposition.UNEVALUABLE and v.turnover_ratio is None for v in result.candidate_verdicts if v.candidate_id == 'te.p415a-v98m')
    changed = tuple(replace(v, turnover_s_inv=Decimal(10)) if v.candidate_id == 'gp.i95m' else v for v in instance.candidates)
    assert science.assess(supplied, replace(instance, candidates=changed)).disposition is AssessmentDisposition.REFUSED


def test_two_distinct_registered_pure_drafts(source, supplied):
    draft1, draft2 = supply_draft(source), use_draft(supplied)
    assert draft1.selected_operation_ids == ('rubisco-candidate-inquiry.supply',)
    assert draft2.selected_operation_ids == ('rubisco-candidate-inquiry.use',)
    assert BUDGET.cpu_cores == 1 and MAX_BYTES is None
    assert len(operation_registrations()) == 2
    assert all(not op.native_effect and all(port.maximum_size_bytes is None for port in op.input_ports) for op in operation_registrations())
    assert decode_canonical_bytes(draft1.operations[0].config_payload.encode(), InquiryOperationConfig, maximum_bytes=None).scientific_design == source


def _payloads(draft, records):
    from hashlib import sha256
    by_digest = {record.fingerprint(): record for record in records}
    return {'external-' + sha256(v.input_id.encode()).hexdigest()[:24] + '.json': by_digest[v.expected_content_sha256].canonical_bytes() for v in draft.external_inputs}


def test_registered_source_meaning_and_distinct_use_evidence(source, supplied, monkeypatch):
    from empirical_lawhood.api import recursive_inquiry_evidence as api
    from empirical_lawhood.adapters.methods.rubisco_candidate_inquiry.executable_binding import EXECUTABLE_BINDING_FACTORIES
    monkeypatch.setattr(api, 'operation_factories', lambda: EXECUTABLE_BINDING_FACTORIES)
    draft = supply_draft(source)
    binding = api.project_wave_evidence_bindings(draft=draft, payloads=_payloads(draft, (source,)))
    assert len(binding) == 1
    row = next(iter(binding.values()))
    assert row.scope != supplied.scope and row.independent_unit_ids == ()
    assert row.scope.quantity_ids == ('original-source-bytes',)
    instance = science.authentic_candidate(supplied)
    later = use_draft(supplied, instance)
    bindings = api.project_wave_evidence_bindings(draft=later, payloads=_payloads(later, (supplied, instance)))
    assert len(bindings) == 2
    assert bindings['external.rubisco-candidate-inquiry.use.supplier'].scope == supplied.scope


def test_endpoint_and_authenticated_product_projection(source, supplied):
    from types import SimpleNamespace as N
    from empirical_lawhood.kernel.status import OperationalStatus
    from empirical_lawhood.adapters.methods.rubisco_candidate_inquiry.recursive_translation import inquiry_outcome_projector, inquiry_endpoint_validator
    for draft, record in ((supply_draft(source), supplied), (use_draft(supplied), science.assess(supplied, science.authentic_candidate(supplied)))):
        node = draft.operations[0].node_id
        spec = N(distinguishing_assessment=draft.operations[0].config_identity, endpoint=supplied.scope)
        logical = N(payload_schema=record.SCHEMA, content_sha256=record.fingerprint())
        products = {'records': {node: {node + '.product': record}}, 'receipts': {node: N(operational_status=OperationalStatus.SUCCEEDED, output_logical_artifacts=(logical,))}}
        assert inquiry_outcome_projector(draft, spec, products) == 'useful-supply'
        with pytest.raises(ValueError, match='endpoint'):
            inquiry_endpoint_validator(draft, replace(supplied.scope, receiver_id='wrong.reference.receiver'))
        assert inquiry_outcome_projector(draft, spec, {'records': {}}) == 'unresolved'
    result = science.assess(supplied, science.authentic_candidate(supplied))
    with pytest.raises(ValueError, match='ratios'):
        replace(result.frontier[0], turnover_ratio=Decimal(2))
    with pytest.raises(ValueError, match='nomination'):
        replace(result, nominee='gp.i95m')


def test_frontier_preserves_adverse_and_distinct_hypotheses(supplied):
    result = science.assess(supplied, science.authentic_candidate(supplied))
    no_gain_specificity_loss = next(v for v in result.frontier if v.alpha_k == 0 and v.alpha_s == -1)
    assert 'gp.i95m.m1' not in no_gain_specificity_loss.conditional_nondominated_candidate_views
    assert 'gp.wt.m1' in no_gain_specificity_loss.conditional_nondominated_candidate_views
    assert len({v.candidate_id for v in result.candidate_verdicts}) == 4
    assert {v.ssu_view for v in result.candidate_verdicts if v.candidate_id == 'gp.i95m'} == {'m1', 'v1'}


def test_full_registered_source_and_portable_parent_successor_compilation(source, supplied):
    from tests.test_inquiry_successor_compilation import compile_complete_draft, portable_parent
    from empirical_lawhood.adapters.methods.rubisco_candidate_inquiry import operation_bindings as owner
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    from empirical_lawhood.planning.recursive_input_origins import RecursiveInputOrigin, RecursiveInputOriginKind, RecursiveInputOrigins
    from empirical_lawhood.runtime.plans import ScientificInputRole
    first = supply_draft(source)
    compile_complete_draft(first, owner)
    parent = portable_parent(supplied)
    later = use_draft(supplied, parent=parent)
    product = parent.products[0]
    origins = RecursiveInputOrigins(tuple(sorted((
        RecursiveInputOrigin(value.input_id, RecursiveInputOriginKind.CONTRIBUTION,
            value.expected_content_sha256, product.role.value, ObjectIdentity.from_record(parent.contribution_id, parent),
            product.product_id, product.producing_receipt) if value.input_id.endswith('.supplier') else
        RecursiveInputOrigin(value.input_id, RecursiveInputOriginKind.SOURCE, value.expected_content_sha256, value.scientific_role)
        for value in later.external_inputs), key=lambda value: value.input_id)))
    origins.validate_draft(later)
    assert next(value for value in later.external_inputs if value.input_id.endswith('.supplier')).scientific_role == ScientificInputRole.MODEL.value
    compile_complete_draft(later, owner)
    wrong = replace(later, external_inputs=tuple(replace(value, scientific_role='OUTCOME') if value.input_id.endswith('.supplier') else value for value in later.external_inputs))
    with pytest.raises(ValueError, match='digest or role'):
        origins.validate_draft(wrong)
    with pytest.raises(ValueError, match='exact external-input contract'):
        compile_complete_draft(wrong, owner)
